"""GeoTIFF reader (v2 brief R2), standard library + numpy.

Classic TIFF and BigTIFF; stripped and tiled layouts; chunky or planar samples (band 1 is read); compression none,
Deflate (8 and 32946), LZW (5, own decoder) and PackBits (32773); horizontal predictor (2) and floating-point
predictor (3); 8/16/32/64-bit integers and 32/64-bit floats. Geo-referencing from ModelPixelScale + ModelTiepoint or
ModelTransformation (general affine, rotation allowed), RasterType (pixel is area / point), EPSG from the GeoKeys and
nodata from GDAL_NODATA (42113). JPEG and other compressions are refused with a clear message.

Windowed reading: only the strips or tiles holding the requested pixels are read and decoded (small LRU cache), so a
20 000 × 20 000 float32 DEM never loads fully.
"""
from __future__ import annotations

import struct
import zlib
from collections import OrderedDict

import numpy as np

_TYPES = {1: ("B", 1), 2: ("s", 1), 3: ("H", 2), 4: ("I", 4), 5: ("II", 8), 6: ("b", 1), 7: ("B", 1), 8: ("h", 2),
          9: ("i", 4), 10: ("ii", 8), 11: ("f", 4), 12: ("d", 8), 13: ("I", 4), 16: ("Q", 8), 17: ("q", 8), 18: ("Q", 8)}
COMPRESSION = {1: "none", 2: "CCITT RLE", 3: "CCITT G3", 4: "CCITT G4", 5: "LZW", 6: "JPEG (old)", 7: "JPEG", 8: "Deflate",
               32773: "PackBits", 32946: "Deflate", 34887: "LERC", 34925: "LZMA", 50000: "ZSTD", 50001: "WebP"}


def lzw_decode(data: bytes, expected: int | None = None) -> bytes:
    """TIFF LZW (MSB-first codes, 9–12 bits, ClearCode 256, EOI 257, early code-width change)."""
    out = bytearray()
    table = [bytes([i]) for i in range(256)] + [b"", b""]
    width, buf, nbits, pos, prev = 9, 0, 0, 0, None
    n = len(data)
    while True:
        while nbits < width:
            if pos >= n:
                return bytes(out)
            buf = (buf << 8) | data[pos]
            pos += 1
            nbits += 8
        code = (buf >> (nbits - width)) & ((1 << width) - 1)
        nbits -= width
        if code == 257:
            break
        if code == 256:
            table = table[:258]
            width, prev = 9, None
            continue
        if prev is None:
            entry = table[code]
            out += entry
            prev = entry
            continue
        if code < len(table):
            entry = table[code]
            table.append(prev + entry[:1])
        elif code == len(table):
            entry = prev + prev[:1]
            table.append(entry)
        else:
            raise ValueError("corrupt LZW stream")
        out += entry
        prev = entry
        nt = len(table)
        if nt >= 511 and width == 9 or nt >= 1023 and width == 10 or nt >= 2047 and width == 11:
            width += 1
        if expected is not None and len(out) >= expected:
            break
    return bytes(out)


def packbits_decode(data: bytes) -> bytes:
    out = bytearray()
    i, n = 0, len(data)
    while i < n:
        h = data[i]
        i += 1
        if h < 128:
            out += data[i:i + h + 1]
            i += h + 1
        elif h > 128:
            if i < n:
                out += bytes([data[i]]) * (257 - h)
            i += 1
    return bytes(out)


class Tiff:
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            head = f.read(16)
        if head[:2] == b"II":
            self.bo = "<"
        elif head[:2] == b"MM":
            self.bo = ">"
        else:
            raise ValueError("not a TIFF file")
        ver = struct.unpack(self.bo + "H", head[2:4])[0]
        if ver == 42:
            self.big = False
            ifd = struct.unpack(self.bo + "I", head[4:8])[0]
        elif ver == 43:
            self.big = True
            ifd = struct.unpack(self.bo + "Q", head[8:16])[0]
        else:
            raise ValueError(f"unknown TIFF version {ver}")
        self.tags = self._read_ifd(ifd)
        t = self.tags
        self.width, self.height = int(t[256][0]), int(t[257][0])
        bps = t.get(258, (1,))
        self.bits = int(bps[0])
        if any(int(b) != self.bits for b in bps):
            raise ValueError("TIFF with different bit depths per sample is not supported")
        self.spp = int(t.get(277, (1,))[0])
        self.planar = int(t.get(284, (1,))[0])
        self.compression = int(t.get(259, (1,))[0])
        self.predictor = int(t.get(317, (1,))[0])
        fmt = int(t.get(339, (1,))[0])
        if self.compression not in (1, 5, 8, 32773, 32946):
            name = COMPRESSION.get(self.compression, f"code {self.compression}")
            raise ValueError(f"TIFF compression {name} is not supported (supported: none, Deflate, LZW, PackBits)")
        kind = {1: "u", 2: "i", 3: "f"}.get(fmt)
        if kind is None or self.bits not in (8, 16, 32, 64) or (kind == "f" and self.bits not in (32, 64)):
            raise ValueError(f"TIFF sample format {fmt} with {self.bits} bits is not supported")
        self.dtype = np.dtype(f"{self.bo}{kind}{self.bits // 8}")
        if 322 in t:
            self.tiled = True
            self.bw, self.bh = int(t[322][0]), int(t[323][0])
            self.offsets, self.counts = list(t[324]), list(t[325])
            self.across = -(-self.width // self.bw)
            self.down = -(-self.height // self.bh)
        else:
            self.tiled = False
            self.bw = self.width
            self.bh = int(t.get(278, (self.height,))[0])
            self.bh = min(self.bh, self.height) if self.bh > 0 else self.height
            self.offsets, self.counts = list(t[273]), list(t.get(279, ()))
            self.across, self.down = 1, -(-self.height // self.bh)
        self._cache: OrderedDict = OrderedDict()
        self.nodata = None
        if 42113 in t:
            try:
                self.nodata = float(str(t[42113]).strip().strip("\x00"))
            except ValueError:
                pass
        self.geokeys = self._geokeys()
        self.affine = self._affine()

    # ---- IFD ------------------------------------------------------------------------------------------------------
    def _read_ifd(self, off: int) -> dict:
        tags = {}
        with open(self.path, "rb") as f:
            f.seek(off)
            if self.big:
                n = struct.unpack(self.bo + "Q", f.read(8))[0]
                esz, inl = 20, 8
            else:
                n = struct.unpack(self.bo + "H", f.read(2))[0]
                esz, inl = 12, 4
            raw = f.read(n * esz)
            for k in range(n):
                e = raw[k * esz:(k + 1) * esz]
                tag, typ = struct.unpack(self.bo + "HH", e[:4])
                cnt = struct.unpack(self.bo + ("Q" if self.big else "I"), e[4:4 + (8 if self.big else 4)])[0]
                val = e[4 + (8 if self.big else 4):]
                if typ not in _TYPES:
                    continue
                code, size = _TYPES[typ]
                nbytes = size * cnt
                if nbytes <= inl:
                    data = val[:nbytes]
                else:
                    ptr = struct.unpack(self.bo + ("Q" if self.big else "I"), val[:inl])[0]
                    here = f.tell()
                    f.seek(ptr)
                    data = f.read(nbytes)
                    f.seek(here)
                if typ == 2:
                    tags[tag] = data.decode("latin-1")
                elif typ in (5, 10):
                    v = struct.unpack(self.bo + code[0] * (2 * cnt), data)
                    tags[tag] = tuple(v[i] / v[i + 1] if v[i + 1] else 0.0 for i in range(0, len(v), 2))
                else:
                    tags[tag] = struct.unpack(self.bo + code * cnt, data)
        return tags

    def _geokeys(self) -> dict:
        t = self.tags
        if 34735 not in t:
            return {}
        k = t[34735]
        dbl = t.get(34736, ())
        asc = t.get(34737, "")
        out = {}
        for i in range(int(k[3])):
            kid, loc, cnt, val = k[4 + 4 * i: 8 + 4 * i]
            if loc == 0:
                out[kid] = val
            elif loc == 34736:
                out[kid] = dbl[val:val + cnt] if cnt > 1 else (dbl[val] if val < len(dbl) else None)
            elif loc == 34737:
                out[kid] = asc[val:val + cnt].rstrip("|\x00")
        return out

    def _affine(self):
        """Pixel centre (col, row) → (x, y): x = a·col + b·row + c, y = d·col + e·row + f."""
        t, g = self.tags, self.geokeys
        point = g.get(1025) == 2                        # RasterPixelIsPoint
        h = 0.0 if point else 0.5
        if 34264 in t:
            m = t[34264]
            a, b, d, e = m[0], m[1], m[4], m[5]
            c, f = m[3] + (a + b) * h, m[7] + (d + e) * h
            return (a, b, c, d, e, f)
        if 33550 in t and 33922 in t:
            sx, sy = t[33550][0], t[33550][1]
            i, j, _, x, y, _ = t[33922][:6]
            return (sx, 0.0, x + (h - i) * sx, 0.0, -sy, y - (h - j) * sy)
        return None

    def crs(self) -> dict:
        from .geo import describe_epsg
        g = self.geokeys
        out = {}
        if g.get(3072) and g[3072] not in (0, 32767):
            out = describe_epsg(g[3072])
        elif g.get(2048) and g[2048] not in (0, 32767):
            out = describe_epsg(g[2048])
        elif g.get(1024) == 2:
            out = {"kind": "geographic", "datum": "unknown"}
        if g.get(3076) in (9002, 9003):
            out["units"] = "feet"
        if g.get(1026) or g.get(3073):
            out["citation"] = str(g.get(1026) or g.get(3073))[:120]
        return out

    # ---- data ------------------------------------------------------------------------------------------------------
    def _block(self, k: int) -> np.ndarray:
        if k in self._cache:
            self._cache.move_to_end(k)
            return self._cache[k]
        rows = self.bh if self.tiled else min(self.bh, self.height - k * self.bh)
        spp = 1 if self.planar == 2 else self.spp
        cols = self.bw
        nbytes = rows * cols * spp * self.dtype.itemsize
        with open(self.path, "rb") as f:
            f.seek(self.offsets[k])
            raw = f.read(self.counts[k] if self.counts else nbytes * 2)
        if self.compression in (8, 32946):
            raw = zlib.decompress(raw)
        elif self.compression == 5:
            raw = lzw_decode(raw, nbytes)
        elif self.compression == 32773:
            raw = packbits_decode(raw)
        raw = raw[:nbytes]
        if len(raw) < nbytes:
            raw = raw + b"\x00" * (nbytes - len(raw))
        if self.predictor == 3:
            if self.dtype.kind != "f":
                raise ValueError("floating-point predictor on integer TIFF data")
            b = np.frombuffer(raw, np.uint8).reshape(rows, cols * spp * self.dtype.itemsize)
            b = np.cumsum(b.reshape(rows, -1, spp), axis=1, dtype=np.uint8).reshape(rows, -1)
            planes = b.reshape(rows, self.dtype.itemsize, cols * spp)
            le = np.ascontiguousarray(planes.transpose(0, 2, 1)[:, :, ::-1])
            arr = le.view(f"<f{self.dtype.itemsize}").reshape(rows, cols, spp)
        else:
            arr = np.frombuffer(raw, self.dtype).reshape(rows, cols, spp)
            if self.predictor == 2:
                if self.dtype.kind == "f":
                    raise ValueError("horizontal predictor on floating-point TIFF data is not supported")
                arr = np.cumsum(arr.astype(self.dtype.newbyteorder("=")), axis=1, dtype=self.dtype.newbyteorder("="))
        band = np.array(arr[:, :, 0], dtype=float)
        if self.nodata is not None:
            band[band == self.nodata] = np.nan
        self._cache[k] = band
        if len(self._cache) > 64:
            self._cache.popitem(last=False)
        return band

    def pixels(self, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
        """Values at integer (row, col) pairs, NaN outside the image or on nodata. Only the blocks needed are decoded."""
        rows, cols = np.asarray(rows, int), np.asarray(cols, int)
        out = np.full(rows.shape, np.nan)
        ok = (rows >= 0) & (cols >= 0) & (rows < self.height) & (cols < self.width)
        r, c = rows[ok], cols[ok]
        k = (r // self.bh) * self.across + (c // self.bw) if self.tiled else r // self.bh
        vals = np.empty(len(r))
        for kk in np.unique(k):
            m = k == kk
            blk = self._block(int(kk))
            vals[m] = blk[r[m] - (r[m] // self.bh) * self.bh, c[m] % self.bw if self.tiled else c[m]]
        out[ok] = vals
        return out

    def read_all(self) -> np.ndarray:
        rr, cc = np.mgrid[0:self.height, 0:self.width]
        return self.pixels(rr.ravel(), cc.ravel()).reshape(self.height, self.width)


def write_tiff(path: str, arr: np.ndarray, *, affine_ul: tuple[float, float, float, float] | None = None, epsg: int | None = None,
               nodata: float | None = None, compression: int = 1, predictor: int = 1, tile: int | None = None,
               rows_per_strip: int | None = None, big_endian: bool = False) -> None:
    """Minimal GeoTIFF writer for tests: one band, strips or tiles, compression none / Deflate / PackBits (raw runs) /
    LZW (as literal codes), predictors 2 and 3. `affine_ul` = (x_ul_corner, y_ul_corner, sx, sy)."""
    bo = ">" if big_endian else "<"
    a = np.asarray(arr)
    h, w = a.shape
    dt = a.dtype.newbyteorder(bo)
    a = a.astype(dt)
    bw, bh = (tile, tile) if tile else (w, rows_per_strip or h)
    blocks = []
    across, down = (-(-w // bw), -(-h // bh))
    for br in range(down):
        for bc in range(across if tile else 1):
            blk = a[br * bh:(br + 1) * bh, bc * bw:(bc + 1) * bw] if tile else a[br * bh:(br + 1) * bh]
            if tile and blk.shape != (bh, bw):
                pad = np.zeros((bh, bw), dt)
                pad[:blk.shape[0], :blk.shape[1]] = blk
                blk = pad
            rows = blk.shape[0]
            if predictor == 2:
                d = blk.astype(blk.dtype.newbyteorder("=")).copy()
                d[:, 1:] = np.diff(d, axis=1)
                raw = d.astype(dt).tobytes()
            elif predictor == 3:
                le = blk.astype(blk.dtype.newbyteorder("<"))
                b = np.frombuffer(le.tobytes(), np.uint8).reshape(rows, -1, dt.itemsize)[:, :, ::-1]
                planes = np.ascontiguousarray(b.transpose(0, 2, 1)).reshape(rows, -1)
                dd = planes.astype(np.int16)
                dd[:, 1:] = np.diff(planes.astype(np.int16), axis=1)
                raw = (dd % 256).astype(np.uint8).tobytes()
            else:
                raw = blk.tobytes()
            if compression == 8:
                raw = zlib.compress(raw)
            elif compression == 32773:
                out = bytearray()
                for i in range(0, len(raw), 128):
                    chunk = raw[i:i + 128]
                    out.append(len(chunk) - 1)
                    out += chunk
                raw = bytes(out)
            elif compression == 5:
                raw = _lzw_encode(raw)
            blocks.append(raw)
    tags = {256: (4, [w]), 257: (4, [h]), 258: (3, [dt.itemsize * 8]), 259: (3, [compression]), 262: (3, [1]),
            277: (3, [1]), 284: (3, [1]), 339: (3, [{"u": 1, "i": 2, "f": 3}[dt.kind]])}
    if predictor > 1:
        tags[317] = (3, [predictor])
    if affine_ul:
        x0, y0, sx, sy = affine_ul
        tags[33550] = (12, [sx, sy, 0.0])
        tags[33922] = (12, [0.0, 0.0, 0.0, x0, y0, 0.0])
    if epsg:
        geo = [1, 1, 0, 3, 1024, 0, 1, 1 if epsg != 4326 else 2, 1025, 0, 1, 1, 3072 if epsg != 4326 else 2048, 0, 1, epsg]
        tags[34735] = (3, geo)
    if nodata is not None:
        tags[42113] = (2, f"{nodata:g}\x00")
    data_off = 8
    offsets, pos = [], data_off
    for b in blocks:
        offsets.append(pos)
        pos += len(b)
    if tile:
        tags[322], tags[323] = (3, [bw]), (3, [bh])
        tags[324], tags[325] = (4, offsets), (4, [len(b) for b in blocks])
    else:
        tags[278] = (4, [bh])
        tags[273], tags[279] = (4, offsets), (4, [len(b) for b in blocks])
    ifd_off = pos + (pos % 2)
    fmt = {2: "s", 3: "H", 4: "I", 12: "d"}
    size = {2: 1, 3: 2, 4: 4, 12: 8}
    entries, extra = [], bytearray()
    extra_off = ifd_off + 2 + 12 * len(tags) + 4
    for tag in sorted(tags):
        typ, vals = tags[tag]
        if typ == 2:
            data = vals.encode("latin-1")
            cnt = len(data)
        else:
            data = struct.pack(bo + fmt[typ] * len(vals), *vals)
            cnt = len(vals)
        if len(data) <= 4:
            entries.append(struct.pack(bo + "HHI", tag, typ, cnt) + data.ljust(4, b"\x00"))
        else:
            entries.append(struct.pack(bo + "HHII", tag, typ, cnt, extra_off + len(extra)))
            extra += data
            if len(extra) % 2:
                extra += b"\x00"
    with open(path, "wb") as f:
        f.write((b"II" if bo == "<" else b"MM") + struct.pack(bo + "HI", 42, ifd_off))
        for b in blocks:
            f.write(b)
        if pos % 2:
            f.write(b"\x00")
        f.write(struct.pack(bo + "H", len(tags)))
        for e in entries:
            f.write(e)
        f.write(struct.pack(bo + "I", 0))
        f.write(bytes(extra))


def _lzw_encode(data: bytes) -> bytes:
    """Real LZW encoder (TIFF flavour) so the decoder is tested on genuine code-width changes."""
    out, buf, nbits = bytearray(), 0, 0
    width = 9

    def emit(code):
        nonlocal buf, nbits
        buf = (buf << width) | code
        nbits += width
        while nbits >= 8:
            out.append((buf >> (nbits - 8)) & 0xFF)
            nbits -= 8

    table = {bytes([i]): i for i in range(256)}
    nxt = 258
    emit(256)
    w = b""
    for ch in data:
        wc = w + bytes([ch])
        if wc in table:
            w = wc
            continue
        emit(table[w])
        table[wc] = nxt
        nxt += 1
        if nxt + 1 >= 4094:                  # leave room: clear before 12-bit overflow
            emit(256)
            table = {bytes([i]): i for i in range(256)}
            nxt, width = 258, 9
        elif nxt in (512, 1024, 2048):          # the decoder, one entry behind, switches at 511 / 1023 / 2047
            width += 1
        w = bytes([ch])
    if w:
        emit(table[w])
        if nxt + 1 in (512, 1024, 2048):        # the decoder adds one more entry on the last code before EOI
            width += 1
    emit(257)
    if nbits:
        out.append((buf << (8 - nbits)) & 0xFF)
    return bytes(out)
