"""Vector readers shared by topography and licence boundaries: DXF (ASCII), ESRI Shapefile (+ .dbf, .prj),
KML / KMZ, GeoJSON, Surpac string (.str) and DTM (.dtm).

Each reader returns plain geometry (numpy arrays), never interpreted: points (N, 3), polylines [(N, 3), closed flag],
triangles (V (N, 3), T (M, 3)) and polygon rings, with the coordinate system as found (geographic for KML; whatever
the file holds otherwise) and notes for the report.
"""
from __future__ import annotations

import re
import struct
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Geometry:
    points: list = field(default_factory=list)        # (x, y, z)
    lines: list = field(default_factory=list)         # (array (N, 3), closed: bool, z_known: bool)
    vertices: list = field(default_factory=list)      # mesh vertices (x, y, z)
    triangles: list = field(default_factory=list)     # (i, j, k) into vertices
    polygons: list = field(default_factory=list)      # list of rings (array (N, 2)) per polygon (outer first, then holes)
    crs: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


# ---- DXF -----------------------------------------------------------------------------------------------------------
def read_dxf(path: str) -> Geometry:
    """ASCII DXF: POINT, LINE, 3DFACE, LWPOLYLINE (elevation 38), POLYLINE (2D with elevation, 3D, polyface mesh)."""
    with open(path, "rb") as f:
        head = f.read(22)
    if head.startswith(b"AutoCAD Binary DXF"):
        raise ValueError("binary DXF is not supported: save the drawing as ASCII DXF")
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    pairs = [(lines[i].strip(), lines[i + 1].rstrip("\r")) for i in range(0, len(lines) - 1, 2)]
    g = Geometry()
    in_ent, k, n = False, 0, len(pairs)
    while k < n:
        c, v = pairs[k]
        if c == "2" and v.strip() == "ENTITIES":
            in_ent = True
        elif c == "0" and v.strip() == "ENDSEC":
            in_ent = False
        if not (in_ent and c == "0"):
            k += 1
            continue
        etype = v.strip()
        j = k + 1
        grp = []
        while j < n and pairs[j][0] != "0":
            grp.append(pairs[j])
            j += 1
        if etype == "POINT":
            d = _codes(grp)
            g.points.append((d.get("10", 0), d.get("20", 0), d.get("30", 0)))
        elif etype == "LINE":
            d = _codes(grp)
            g.lines.append((np.array([[d.get("10", 0), d.get("20", 0), d.get("30", 0)], [d.get("11", 0), d.get("21", 0), d.get("31", 0)]]), False, True))
        elif etype == "3DFACE":
            d = _codes(grp)
            p = [(d.get(f"1{i}", 0), d.get(f"2{i}", 0), d.get(f"3{i}", 0)) for i in range(4)]
            base = len(g.vertices)
            g.vertices.extend(p[:3])
            g.triangles.append((base, base + 1, base + 2))
            if p[3] != p[2]:
                g.vertices.append(p[3])
                g.triangles.append((base, base + 2, base + 3))
        elif etype == "LWPOLYLINE":
            elev, flags, xs, ys = 0.0, 0, [], []
            has_z = False
            for cc, vv in grp:
                if cc == "38":
                    elev, has_z = float(vv), True
                elif cc == "70":
                    flags = int(vv)
                elif cc == "10":
                    xs.append(float(vv))
                elif cc == "20":
                    ys.append(float(vv))
            if len(xs) >= 2:
                g.lines.append((np.column_stack([xs, ys[:len(xs)], np.full(len(xs), elev)]), bool(flags & 1), has_z))
        elif etype == "POLYLINE":
            d = _codes(grp)
            flags = int(d.get("70", 0))
            elev = d.get("30", 0.0)
            verts, faces = [], []
            j2 = j
            while j2 < n and pairs[j2][1].strip() == "VERTEX" and pairs[j2][0] == "0":
                vg = []
                j3 = j2 + 1
                while j3 < n and pairs[j3][0] != "0":
                    vg.append(pairs[j3])
                    j3 += 1
                vd = _codes(vg)
                vf = int(vd.get("70", 0))
                if flags & 64 and vf & 128 and not vf & 64:
                    idx = [abs(int(vd.get(f"7{i}", 0))) for i in range(1, 5)]
                    idx = [q - 1 for q in idx if q]
                    faces.append(idx)
                else:
                    verts.append((vd.get("10", 0), vd.get("20", 0), vd.get("30", elev) if flags & (8 | 16 | 64) else elev))
                j2 = j3
            j = j2
            if flags & 64:
                base = len(g.vertices)
                g.vertices.extend(verts)
                for fc in faces:
                    for t in range(1, len(fc) - 1):
                        g.triangles.append((base + fc[0], base + fc[t], base + fc[t + 1]))
            elif len(verts) >= 2:
                g.lines.append((np.array(verts, float), bool(flags & 1), bool(flags & 8) or "30" in d))
        k = j
    return g


def _codes(grp) -> dict:
    d = {}
    for c, v in grp:
        try:
            d[c] = float(v)
        except ValueError:
            d[c] = v
    return d


# ---- Shapefile -----------------------------------------------------------------------------------------------------
SHP_TYPES = {0: "Null", 1: "Point", 3: "PolyLine", 5: "Polygon", 8: "MultiPoint", 11: "PointZ", 13: "PolyLineZ", 15: "PolygonZ",
             18: "MultiPointZ", 21: "PointM", 23: "PolyLineM", 25: "PolygonM", 28: "MultiPointM", 31: "MultiPatch"}


def read_dbf(path: str) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        return []
    b = p.read_bytes()
    nrec, hlen, rlen = struct.unpack("<IHH", b[4:12])
    fields, pos = [], 32
    while pos < hlen - 1 and b[pos] != 0x0D:
        name = b[pos:pos + 11].split(b"\x00")[0].decode("latin-1").strip()
        typ, ln = chr(b[pos + 11]), b[pos + 16]
        fields.append((name, typ, ln))
        pos += 32
    out = []
    for r in range(nrec):
        off = hlen + r * rlen + 1
        rec, o = {}, off
        for name, typ, ln in fields:
            raw = b[o:o + ln].decode("latin-1", errors="replace").strip()
            o += ln
            if typ in "NFB":
                try:
                    rec[name] = float(raw) if raw else None
                except ValueError:
                    rec[name] = None
            else:
                rec[name] = raw
        out.append(rec)
    return out


def read_shp(path: str) -> Geometry:
    """Points, multipoints, polylines and polygons (2D, Z and M). Z values come from the Z block; 2D lines and points
    take their elevation from a .dbf field named like ELEV, ELEVATION, Z, CONTOUR, HEIGHT or ALT when present."""
    p = Path(path)
    b = p.read_bytes()
    if struct.unpack(">I", b[:4])[0] != 9994:
        raise ValueError("not an ESRI shapefile (.shp)")
    g = Geometry()
    prj = p.with_suffix(".prj")
    if prj.is_file():
        from .geo import describe_wkt
        g.crs = describe_wkt(prj.read_text(errors="replace"))
    dbf = read_dbf(str(p.with_suffix(".dbf")))
    zfield = None
    if dbf:
        for k in dbf[0]:
            if re.fullmatch(r"(ELEV|ELEVATION|Z|CONTOUR|HEIGHT|ALT|ALTITUDE|RL|ELEV_M|Z_M|CONT)", k.upper()):
                zfield = k
                break
    pos, rec = 100, 0
    while pos + 8 <= len(b):
        _, clen = struct.unpack(">II", b[pos:pos + 8])
        c = b[pos + 8: pos + 8 + 2 * clen]
        pos += 8 + 2 * clen
        attr = dbf[rec] if rec < len(dbf) else {}
        rec += 1
        if len(c) < 4:
            continue
        st = struct.unpack("<i", c[:4])[0]
        zattr = attr.get(zfield) if zfield else None
        if st in (1, 11, 21):
            x, y = struct.unpack("<2d", c[4:20])
            z = struct.unpack("<d", c[20:28])[0] if st == 11 else (zattr if zattr is not None else np.nan)
            g.points.append((x, y, z))
        elif st in (8, 18, 28):
            npt = struct.unpack("<i", c[36:40])[0]
            xy = np.frombuffer(c[40:40 + 16 * npt], "<f8").reshape(-1, 2)
            if st == 18:
                zo = 40 + 16 * npt + 16
                z = np.frombuffer(c[zo:zo + 8 * npt], "<f8")
            else:
                z = np.full(npt, zattr if zattr is not None else np.nan)
            g.points.extend(map(tuple, np.column_stack([xy, z])))
        elif st in (3, 5, 13, 15, 23, 25):
            nparts, npt = struct.unpack("<2i", c[36:44])
            parts = list(struct.unpack(f"<{nparts}i", c[44:44 + 4 * nparts])) + [npt]
            xo = 44 + 4 * nparts
            xy = np.frombuffer(c[xo:xo + 16 * npt], "<f8").reshape(-1, 2)
            if st in (13, 15):
                zo = xo + 16 * npt + 16
                z = np.frombuffer(c[zo:zo + 8 * npt], "<f8")
                zk = True
            else:
                z = np.full(npt, zattr if zattr is not None else np.nan)
                zk = zattr is not None
            rings = [xy[parts[i]:parts[i + 1]] for i in range(nparts)]
            if st in (5, 15, 25):
                g.polygons.append(rings)
            for i in range(nparts):
                seg = np.column_stack([xy[parts[i]:parts[i + 1]], z[parts[i]:parts[i + 1]]])
                g.lines.append((seg, st in (5, 15, 25), zk))
        elif st == 31:
            g.notes.append("MultiPatch shapes are skipped")
    return g


# ---- KML / KMZ -----------------------------------------------------------------------------------------------------
def read_kml(path: str) -> Geometry:
    """Placemark Point / LineString / LinearRing / Polygon (outer and inner boundaries), MultiGeometry. Coordinates are
    lon,lat[,alt] (WGS 84). Altitudes are used only when present and the altitude mode is not clampToGround."""
    import xml.etree.ElementTree as ET
    p = Path(path)
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".kml")]
            if not names:
                raise ValueError("KMZ archive without a .kml document")
            data = z.read("doc.kml" if "doc.kml" in names else names[0])
    else:
        data = p.read_bytes()
    root = ET.fromstring(data)
    g = Geometry(crs={"kind": "geographic", "datum": "WGS84"})

    def tag(e):
        return e.tag.rsplit("}", 1)[-1]

    def coords(e):
        txt = next((c.text for c in e.iter() if tag(c) == "coordinates"), "") or ""
        pts = []
        for tok in txt.split():
            v = tok.split(",")
            if len(v) >= 2:
                pts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 and v[2] else np.nan))
        return np.array(pts, float).reshape(-1, 3)

    def clamped(e):
        m = next((c.text for c in e.iter() if tag(c) == "altitudeMode"), None)
        return m is None or m.strip() == "clampToGround"

    for e in root.iter():
        t = tag(e)
        if t == "Point":
            c = coords(e)
            if len(c):
                z = c[0, 2] if not clamped(e) or (np.isfinite(c[0, 2]) and c[0, 2] != 0) else np.nan
                g.points.append((c[0, 0], c[0, 1], z))
        elif t in ("LineString", "LinearRing"):
            parent_poly = False
            c = coords(e)
            if len(c) >= 2:
                zk = np.isfinite(c[:, 2]).any() and not (np.nan_to_num(c[:, 2]) == 0).all()
                g.lines.append((c, t == "LinearRing", bool(zk)))
            _ = parent_poly
        elif t == "Polygon":
            rings = []
            for b in e:
                if tag(b) in ("outerBoundaryIs", "innerBoundaryIs"):
                    c = coords(b)
                    if len(c) >= 3:
                        rings.append((tag(b) == "outerBoundaryIs", c[:, :2]))
            rings.sort(key=lambda r: not r[0])
            if rings:
                g.polygons.append([r[1] for r in rings])
    return g


# ---- GeoJSON -------------------------------------------------------------------------------------------------------
def read_geojson(path: str) -> Geometry:
    import json
    d = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    g = Geometry()
    crs = (d.get("crs") or {}).get("properties", {}).get("name", "") if isinstance(d, dict) else ""
    m = re.search(r"EPSG:+(\d+)", str(crs))
    if m:
        from .geo import describe_epsg
        g.crs = describe_epsg(int(m.group(1)))

    def geom(o):
        if not isinstance(o, dict):
            return
        t = o.get("type")
        if t == "FeatureCollection":
            for f in o.get("features", []):
                geom(f)
        elif t == "Feature":
            geom(o.get("geometry"))
        elif t == "GeometryCollection":
            for x in o.get("geometries", []):
                geom(x)
        elif t == "Polygon":
            g.polygons.append([np.asarray(r, float)[:, :2] for r in o["coordinates"]])
        elif t == "MultiPolygon":
            for poly in o["coordinates"]:
                g.polygons.append([np.asarray(r, float)[:, :2] for r in poly])
        elif t == "Point":
            c = list(o["coordinates"]) + [np.nan]
            g.points.append((c[0], c[1], c[2]))
        elif t == "MultiPoint":
            for c in o["coordinates"]:
                c = list(c) + [np.nan]
                g.points.append((c[0], c[1], c[2]))
        elif t in ("LineString", "MultiLineString"):
            for ln in ([o["coordinates"]] if t == "LineString" else o["coordinates"]):
                a = np.asarray(ln, float)
                z = a[:, 2] if a.shape[1] > 2 else np.full(len(a), np.nan)
                g.lines.append((np.column_stack([a[:, :2], z]), False, a.shape[1] > 2))
    geom(d)
    if not g.crs:
        xs = [p[0][0][0] for p in g.polygons] + [p[0] for p in g.points]
        ys = [p[0][0][1] for p in g.polygons] + [p[1] for p in g.points]
        from .geo import looks_geographic
        g.crs = {"kind": "geographic", "datum": "WGS84"} if xs and looks_geographic(xs, ys) else {"kind": "as file"}
    return g


# ---- Surpac --------------------------------------------------------------------------------------------------------
def read_surpac(path: str) -> Geometry:
    """Surpac string file: records `string, Y, X, Z, …` (northing before easting), strings ended by a 0 record.
    With a .dtm of the same name, its triangles (`id, p1, p2, p3, …`, 1-based point numbers in .str order) form a TIN."""
    p = Path(path)
    s_path = p if p.suffix.lower() == ".str" else p.with_suffix(".str")
    d_path = p if p.suffix.lower() == ".dtm" else p.with_suffix(".dtm")
    if not s_path.is_file():
        raise ValueError(f"Surpac string file {s_path.name} not found (a .dtm needs its .str)")
    rows = s_path.read_text(encoding="latin-1", errors="replace").splitlines()
    g = Geometry()
    pts, cur, cur_sn = [], [], None
    for ln in rows[2:]:
        t = [x.strip() for x in ln.split(",")]
        if len(t) < 4:
            continue
        try:
            sn, y, x, z = int(float(t[0])), float(t[1]), float(t[2]), float(t[3])
        except ValueError:
            continue
        if sn == 0:
            if len(cur) >= 2:
                g.lines.append((np.array(cur), np.allclose(cur[0], cur[-1]), True))
            elif len(cur) == 1:
                g.points.append(tuple(cur[0]))
            cur, cur_sn = [], None
            continue
        if cur_sn is not None and sn != cur_sn and cur:
            g.lines.append((np.array(cur), False, True))
            cur = []
        cur_sn = sn
        cur.append((x, y, z))
        pts.append((x, y, z))
    if cur:
        g.lines.append((np.array(cur), False, True))
    if d_path.is_file():
        tris = []
        started = False
        for ln in d_path.read_text(encoding="latin-1", errors="replace").splitlines():
            u = ln.strip().upper()
            if u.startswith("TRISOLATION"):
                started = True
                continue
            if not started or u.startswith(("OBJECT", "END")):
                continue
            t = [x.strip() for x in ln.split(",")]
            try:
                tris.append((int(t[1]) - 1, int(t[2]) - 1, int(t[3]) - 1))
            except (ValueError, IndexError):
                continue
        if tris:
            g.vertices = pts
            g.triangles = [t for t in tris if max(t) < len(pts) and min(t) >= 0]
            g.lines, g.points = [], []
            g.notes.append("Surpac DTM: point numbers taken in .str order")
    return g


# ---- mesh formats --------------------------------------------------------------------------------------------------
def read_obj(path: str) -> Geometry:
    g = Geometry()
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        t = ln.split()
        if not t:
            continue
        if t[0] == "v" and len(t) >= 4:
            g.vertices.append((float(t[1]), float(t[2]), float(t[3])))
        elif t[0] == "f" and len(t) >= 4:
            n = len(g.vertices)
            idx = [int(x.split("/")[0]) for x in t[1:]]
            idx = [i - 1 if i > 0 else n + i for i in idx]
            for k in range(1, len(idx) - 1):
                g.triangles.append((idx[0], idx[k], idx[k + 1]))
    return g


def read_stl(path: str) -> Geometry:
    b = Path(path).read_bytes()
    g = Geometry()
    if len(b) >= 84:
        n = struct.unpack("<I", b[80:84])[0]
        if 84 + 50 * n == len(b):
            rec = np.frombuffer(b[84:], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n)
            v = rec["v"].reshape(-1, 3).astype(float)
            g.vertices = v.tolist()
            g.triangles = np.arange(len(v)).reshape(-1, 3).tolist()
            return g
    txt = b.decode("utf-8", errors="replace")
    if not txt.lstrip().lower().startswith("solid"):
        raise ValueError("not an STL file")
    v = [tuple(map(float, m)) for m in re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", txt)]
    g.vertices = v
    g.triangles = np.arange(len(v) - len(v) % 3).reshape(-1, 3).tolist()
    return g


def read_ply(path: str) -> Geometry:
    b = Path(path).read_bytes()
    end = b.find(b"end_header")
    if not b.startswith(b"ply") or end < 0:
        raise ValueError("not a PLY file")
    header = b[:end].decode("latin-1").splitlines()
    body = b[b.index(b"\n", end) + 1:]
    fmt = next(h.split()[1] for h in header if h.startswith("format"))
    elems, cur = [], None
    for h in header:
        t = h.split()
        if t[:1] == ["element"]:
            cur = [t[1], int(t[2]), []]
            elems.append(cur)
        elif t[:1] == ["property"] and cur is not None:
            cur[2].append(t[1:])
    tmap = {"char": "i1", "uchar": "u1", "short": "i2", "ushort": "u2", "int": "i4", "uint": "u4", "float": "f4", "double": "f8",
            "int8": "i1", "uint8": "u1", "int16": "i2", "uint16": "u2", "int32": "i4", "uint32": "u4", "float32": "f4", "float64": "f8"}
    g = Geometry()
    if fmt == "ascii":
        toks = body.decode("latin-1").split()
        pos = 0
        for name, cnt, props in elems:
            for _ in range(cnt):
                rec = {}
                for pr in props:
                    if pr[0] == "list":
                        k = int(float(toks[pos]))
                        rec[pr[-1]] = [int(float(x)) for x in toks[pos + 1:pos + 1 + k]]
                        pos += 1 + k
                    else:
                        rec[pr[-1]] = float(toks[pos])
                        pos += 1
                _ply_add(g, name, rec)
        return g
    bo = "<" if fmt == "binary_little_endian" else ">"
    pos = 0
    for name, cnt, props in elems:
        if all(pr[0] != "list" for pr in props):
            dt = np.dtype([(pr[-1], bo + tmap[pr[0]]) for pr in props])
            arr = np.frombuffer(body[pos:pos + dt.itemsize * cnt], dt, count=cnt)
            pos += dt.itemsize * cnt
            if name == "vertex":
                g.vertices = np.column_stack([arr["x"], arr["y"], arr["z"]]).astype(float).tolist()
            continue
        for _ in range(cnt):
            rec = {}
            for pr in props:
                if pr[0] == "list":
                    ct, it = np.dtype(bo + tmap[pr[1]]), np.dtype(bo + tmap[pr[2]])
                    k = int(np.frombuffer(body[pos:pos + ct.itemsize], ct)[0])
                    pos += ct.itemsize
                    rec[pr[-1]] = np.frombuffer(body[pos:pos + it.itemsize * k], it).astype(int).tolist()
                    pos += it.itemsize * k
                else:
                    t = np.dtype(bo + tmap[pr[0]])
                    rec[pr[-1]] = float(np.frombuffer(body[pos:pos + t.itemsize], t)[0])
                    pos += t.itemsize
            _ply_add(g, name, rec)
    return g


def _ply_add(g: Geometry, name: str, rec: dict) -> None:
    if name == "vertex":
        g.vertices.append((rec["x"], rec["y"], rec["z"]))
    elif name == "face":
        idx = rec.get("vertex_indices", rec.get("vertex_index", []))
        for k in range(1, len(idx) - 1):
            g.triangles.append((idx[0], idx[k], idx[k + 1]))
