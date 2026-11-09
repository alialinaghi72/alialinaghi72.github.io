"""Topography surfaces (v2 brief R2): many formats, auto-detected by extension and magic bytes (manual override with
`fmt`), evaluated only where needed.

Grids (bilinear):     ESRI ASCII (.asc), Surfer DSAA / DSBB / DSRB (.grd), ESRI BIL / BIP / BSQ / FLT (+ .hdr),
                      GeoTIFF (.tif, windowed), SRTM (.hgt), regular XYZ grids.
Points and contours:  XYZ / CSV / TXT point clouds, DXF POINT and contour (LW)POLYLINE / LINE, Shapefile PointZ /
                      PolylineZ (or 2D with an elevation field), KML / KMZ with altitudes, Surpac strings without a DTM.
                      A local Delaunay triangulation of the nearest points (scipy) is built per query point; beyond
                      `max_dist` from the data the result is "not supported here" (NaN), never a guess.
Meshes (TIN):         DXF 3DFACE and polyface POLYLINE, Surpac .str + .dtm, OBJ, STL (ASCII / binary), PLY (ASCII /
                      binary). A grid index finds the triangle under each point; barycentric interpolation; where
                      several triangles overlap, the highest (topographic) surface is used.
Each surface reports what it read (`info`): format, extent, resolution or point / triangle count, nodata, CRS, notes.
Proprietary formats without a public specification (Vulcan .00t, Datamine .dm) are refused with that reason.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

import numpy as np

from . import vector as V


class Surface:
    """sample(x, y) → z (NaN where the surface does not support the point). `support(x, y)` → distance to the nearest
    data (0 for grids and meshes inside their extent)."""
    kind = "surface"

    def __init__(self, source: str, fmt: str, info: dict):
        self.source, self.fmt, self.info = source, fmt, info
        self.crs = info.get("crs") or {}
        ext = info.get("extent")
        self.extent = tuple(ext) if ext else None
        self.resolution = info.get("resolution")
        self.n_points = info.get("n_points") or info.get("n_cells") or info.get("n_triangles") or 0

    def sample(self, x, y) -> np.ndarray:  # pragma: no cover - abstract
        raise NotImplementedError

    def support(self, x, y) -> np.ndarray:
        z = self.sample(x, y)
        return np.where(np.isfinite(z), 0.0, np.inf)


# ---- grids ---------------------------------------------------------------------------------------------------------
class Grid(Surface):
    kind = "grid"

    def __init__(self, source, fmt, nrows, ncols, affine, getter, nodata=None, crs=None, notes=None):
        self.nr, self.nc, self.affine, self._get = nrows, ncols, affine, getter
        a, b, c, d, e, f = affine
        det = a * e - b * d
        if det == 0:
            raise ValueError("degenerate grid geo-reference")
        self._inv = (e / det, -b / det, -d / det, a / det)
        corners = np.array([[0, 0], [ncols - 1, 0], [0, nrows - 1], [ncols - 1, nrows - 1]], float)
        xs = a * corners[:, 0] + b * corners[:, 1] + c
        ys = d * corners[:, 0] + e * corners[:, 1] + f
        info = {"format": fmt, "rows": nrows, "cols": ncols, "resolution": float(np.hypot(a, d)), "n_cells": nrows * ncols,
                "extent": (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())), "nodata": nodata,
                "crs": crs or {}, "notes": list(notes or [])}
        super().__init__(source, fmt, info)

    def to_pixel(self, x, y):
        a, b, c, d, e, f = self.affine
        i0, i1, i2, i3 = self._inv
        dx, dy = np.asarray(x, float) - c, np.asarray(y, float) - f
        return i0 * dx + i1 * dy, i2 * dx + i3 * dy           # col, row (fractional, pixel centres at integers)

    def sample(self, x, y) -> np.ndarray:
        col, row = self.to_pixel(x, y)
        c0, r0 = np.floor(col).astype(int), np.floor(row).astype(int)
        tx, ty = col - c0, row - r0
        out = np.full(np.shape(col), np.nan)
        ok = np.isfinite(col) & np.isfinite(row) & (c0 >= 0) & (r0 >= 0) & (c0 < self.nc - 1) & (r0 < self.nr - 1)
        if ok.any():
            c, r = c0[ok], r0[ok]
            rr = np.concatenate([r, r, r + 1, r + 1])
            cc = np.concatenate([c, c + 1, c, c + 1])
            v = self._get(rr, cc).reshape(4, -1)
            t, u = tx[ok], ty[ok]
            out[ok] = v[0] * (1 - t) * (1 - u) + v[1] * t * (1 - u) + v[2] * (1 - t) * u + v[3] * t * u
        return out


def _array_getter(arr: np.ndarray, nodata=None):
    def get(r, c):
        v = np.asarray(arr[r, c], dtype=float)
        if nodata is not None:
            v = np.where(v == nodata, np.nan, v)
        return v
    return get


def read_asc(path: str) -> Grid:
    header = {}
    with open(path, encoding="ascii", errors="replace") as f:
        while True:
            pos = f.tell()
            t = f.readline().split()
            if len(t) == 2 and re.fullmatch(r"[a-zA-Z_]+", t[0]):
                header[t[0].lower()] = float(t[1])
            else:
                f.seek(pos)
                break
        data = np.loadtxt(f, dtype=np.float32, ndmin=2)
    nc, nr = int(header["ncols"]), int(header["nrows"])
    data = data.reshape(nr, nc)
    cs = header.get("cellsize") or header.get("dx")
    csy = header.get("dy", cs)
    if "xllcenter" in header:
        x0, yb = header["xllcenter"], header["yllcenter"]
    else:
        x0, yb = header["xllcorner"] + cs / 2, header["yllcorner"] + csy / 2
    nod = header.get("nodata_value")
    return Grid(path, "ESRI ASCII grid", nr, nc, (cs, 0.0, x0, 0.0, -csy, yb + (nr - 1) * csy), _array_getter(data, nod), nod)


SURFER_BLANK = 1.70141e38


def read_surfer(path: str) -> Grid:
    with open(path, "rb") as f:
        tag = f.read(4)
    if tag == b"DSAA":
        tok = Path(path).read_text(encoding="ascii", errors="replace").split()
        nx, ny = int(tok[1]), int(tok[2])
        xlo, xhi, ylo, yhi = map(float, tok[3:7])
        vals = np.array(tok[9:9 + nx * ny], dtype=np.float64).reshape(ny, nx)
        fmt = "Surfer ASCII grid (DSAA)"
    elif tag == b"DSBB":
        b = Path(path).read_bytes()
        nx, ny = struct.unpack("<2h", b[4:8])
        xlo, xhi, ylo, yhi, _, _ = struct.unpack("<6d", b[8:56])
        vals = np.memmap(path, "<f4", "r", 56, (ny, nx))
        fmt = "Surfer 6 binary grid (DSBB)"
    elif tag == b"DSRB":
        b = open(path, "rb").read(200)
        pos = 4 + 4 + struct.unpack("<i", b[4:8])[0]
        if b[pos:pos + 4] != b"GRID":
            raise ValueError("Surfer 7 grid: GRID section not found where expected")
        ny, nx = struct.unpack("<2i", b[pos + 8:pos + 16])
        xll, yll, dx, dy, _, _, rot, blank = struct.unpack("<8d", b[pos + 16:pos + 80])
        if rot:
            raise ValueError("rotated Surfer 7 grids are not supported")
        dpos = pos + 8 + struct.unpack("<i", b[pos + 4:pos + 8])[0]
        if b[dpos:dpos + 4] != b"DATA":
            raise ValueError("Surfer 7 grid: DATA section not found")
        vals = np.memmap(path, "<f8", "r", dpos + 8, (ny, nx))
        xlo, ylo, xhi, yhi = xll, yll, xll + dx * (nx - 1), yll + dy * (ny - 1)
        fmt = "Surfer 7 grid (DSRB)"
        nod = blank
        return Grid(path, fmt, ny, nx, (dx, 0.0, xll, 0.0, dy, yll), _blank_getter(vals, nod), nod)
    else:
        raise ValueError("not a Surfer grid (DSAA / DSBB / DSRB)")
    dx, dy = (xhi - xlo) / (nx - 1), (yhi - ylo) / (ny - 1)
    return Grid(path, fmt, ny, nx, (dx, 0.0, xlo, 0.0, dy, ylo), _blank_getter(vals, SURFER_BLANK), SURFER_BLANK)


def _blank_getter(arr, blank):
    def get(r, c):
        v = np.asarray(arr[r, c], dtype=float)
        return np.where(v >= blank * 0.999, np.nan, v)
    return get


def _hdr(path: Path) -> dict:
    for cand in (path.with_suffix(".hdr"), path.with_suffix(".HDR"), Path(str(path) + ".hdr")):
        if cand.is_file():
            out = {}
            for ln in cand.read_text(errors="replace").splitlines():
                t = ln.split()
                if len(t) >= 2:
                    out[t[0].lower()] = t[1]
            return out
    raise ValueError(f"{path.name}: the .hdr header file is missing")


def read_bil(path: str) -> Grid:
    """ESRI BIL / BIP / BSQ (ulxmap/ulymap/xdim/ydim) and float grids .flt (xllcorner/cellsize), band 1."""
    p = Path(path)
    h = _hdr(p)
    nr, nc = int(h["nrows"]), int(h["ncols"])
    if p.suffix.lower() == ".flt" or "cellsize" in h:
        bo = ">" if h.get("byteorder", "LSBFIRST").upper().startswith("MSB") else "<"
        cs = float(h["cellsize"])
        x0 = float(h["xllcenter"]) if "xllcenter" in h else float(h["xllcorner"]) + cs / 2
        yb = float(h["yllcenter"]) if "yllcenter" in h else float(h["yllcorner"]) + cs / 2
        arr = np.memmap(p, bo + "f4", "r", 0, (nr, nc))
        nod = float(h.get("nodata_value", h.get("nodata", -9999)))
        return Grid(path, "ESRI float grid (.flt)", nr, nc, (cs, 0.0, x0, 0.0, -cs, yb + (nr - 1) * cs), _array_getter(arr, nod), nod)
    nbits = int(h.get("nbits", 8))
    nb = int(h.get("nbands", 1))
    layout = h.get("layout", p.suffix.lower().lstrip(".")).lower()
    bo = ">" if h.get("byteorder", "I").upper() in ("M", "MOTOROLA", "MSBFIRST") else "<"
    pt = h.get("pixeltype", "signedint" if nbits in (16, 32) else "unsignedint").lower()
    kind = "f" if pt.startswith("float") else ("u" if pt.startswith("unsigned") else "i")
    dt = np.dtype(f"{bo}{kind}{nbits // 8}")
    skip = int(h.get("skipbytes", 0))
    if layout == "bsq" or nb == 1:
        arr = np.memmap(p, dt, "r", skip, (nr, nc))
    elif layout == "bil":
        arr = np.memmap(p, dt, "r", skip, (nr, nb, nc))[:, 0, :]
    elif layout == "bip":
        arr = np.memmap(p, dt, "r", skip, (nr, nc, nb))[:, :, 0]
    else:
        raise ValueError(f"unknown band layout {layout}")
    xd, yd = float(h.get("xdim", 1)), float(h.get("ydim", 1))
    x0, y0 = float(h.get("ulxmap", 0)), float(h.get("ulymap", nr * yd))
    nod = float(h["nodata"]) if "nodata" in h else None
    return Grid(path, f"ESRI {layout.upper()} grid", nr, nc, (xd, 0.0, x0, 0.0, -yd, y0), _array_getter(arr, nod), nod)


def read_hgt(path: str) -> Grid:
    p = Path(path)
    m = re.match(r"([NS])(\d{2})([EW])(\d{3})", p.stem.upper())
    if not m:
        raise ValueError("SRTM .hgt file name must be like N34E045.hgt (it carries the tile position)")
    lat0 = int(m.group(2)) * (1 if m.group(1) == "N" else -1)
    lon0 = int(m.group(4)) * (1 if m.group(3) == "E" else -1)
    n = int(round(np.sqrt(p.stat().st_size / 2)))
    if n * n * 2 != p.stat().st_size:
        raise ValueError("SRTM .hgt size is not a square 1201² or 3601² grid of int16")
    arr = np.memmap(p, ">i2", "r", 0, (n, n))
    step = 1.0 / (n - 1)
    notes = ["SRTM heights are referenced to the EGM96 geoid (orthometric), not the ellipsoid",
             "30 m-class global DEM: not resource-grade topography"]
    return Grid(path, f"SRTM .hgt ({'1' if n == 3601 else '3'} arc-second)", n, n, (step, 0.0, lon0, 0.0, -step, lat0 + 1),
                _array_getter(arr, -32768), -32768, {"kind": "geographic", "datum": "WGS84"}, notes)


def read_geotiff(path: str) -> Grid:
    from .tiff import Tiff
    t = Tiff(path)
    if t.affine is None:
        raise ValueError("TIFF without geo-referencing (no ModelPixelScale/ModelTiepoint or ModelTransformation)")
    notes = [f"compression {t.compression}, {'tiled' if t.tiled else 'stripped'}, {t.dtype}, predictor {t.predictor}"]
    if t.big:
        notes.append("BigTIFF")
    return Grid(path, "GeoTIFF", t.height, t.width, t.affine, t.pixels, t.nodata, t.crs(), notes)


# ---- points, contours and meshes -----------------------------------------------------------------------------------
class PointCloud(Surface):
    kind = "points"

    def __init__(self, source, fmt, pts: np.ndarray, max_dist: float | None = None, contour: bool = False, crs=None, notes=None, k: int = 24):
        from scipy.spatial import cKDTree
        pts = np.asarray(pts, float)
        pts = pts[np.isfinite(pts).all(axis=1)]
        if len(pts) < 3:
            raise ValueError("fewer than three points with an elevation")
        _, uniq = np.unique(np.round(pts[:, :2], 6), axis=0, return_index=True)
        pts = pts[np.sort(uniq)]
        self.pts, self.tree, self.k = pts, cKDTree(pts[:, :2]), min(k, len(pts))
        if max_dist is None:
            max_dist = self._auto_dist(contour)
        self.max_dist = float(max_dist)
        info = {"format": fmt, "n_points": int(len(pts)), "extent": (float(pts[:, 0].min()), float(pts[:, 1].min()), float(pts[:, 0].max()), float(pts[:, 1].max())),
                "max_dist_m": round(self.max_dist, 3), "resolution": None, "crs": crs or {}, "notes": list(notes or [])}
        super().__init__(source, fmt, info)

    def _auto_dist(self, contour: bool) -> float:
        rng = np.random.default_rng(0)
        idx = rng.choice(len(self.pts), size=min(2000, len(self.pts)), replace=False)
        d, j = self.tree.query(self.pts[idx, :2], k=min(16, len(self.pts)))
        if not contour:
            return float(max(5 * np.median(d[:, 1]), 1e-9))
        # contours: distance to the nearest point of a different elevation (across contour lines)
        z = self.pts[:, 2]
        out = []
        for row, jj, dd in zip(idx, j, d):
            o = np.nonzero(np.abs(z[jj] - z[row]) > 1e-9)[0]
            if len(o):
                out.append(dd[o[0]])
        if not out:
            return float(5 * np.median(d[:, 1]))
        return float(2 * np.percentile(out, 90))

    def support(self, x, y) -> np.ndarray:
        d, _ = self.tree.query(np.column_stack([np.asarray(x, float), np.asarray(y, float)]), k=1)
        return d

    def sample(self, x, y) -> np.ndarray:
        """Local Delaunay interpolation. Query points are processed in small spatial clusters (cell ≈ 4 × max_dist):
        each cluster triangulates only the union of its points' nearest data points, so the triangulation stays
        local (never the full area) while trace points along a hole share one triangulation."""
        from scipy.spatial import Delaunay, QhullError
        q = np.column_stack([np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(y, float))])
        out = np.full(len(q), np.nan)
        ok = np.isfinite(q).all(axis=1)
        if not ok.any():
            return out
        idx = np.nonzero(ok)[0]
        d, j = self.tree.query(q[idx], k=self.k)
        d, j = d.reshape(len(idx), -1), j.reshape(len(idx), -1)
        near = d[:, 0] <= self.max_dist
        exact = near & (d[:, 0] < 1e-9)
        out[idx[exact]] = self.pts[j[exact, 0], 2]
        todo = near & ~exact
        if not todo.any():
            return out
        cell = 4 * self.max_dist
        key = np.floor(q[idx[todo]] / cell).astype(np.int64)
        groups = {}
        for n, kk in zip(np.nonzero(todo)[0], map(tuple, key)):
            groups.setdefault(kk, []).append(n)
        for members in groups.values():
            members = np.array(members)
            sel = np.unique(j[members].ravel())
            local = self.pts[sel]
            try:
                tri = Delaunay(local[:, :2])
            except QhullError:
                continue
            qq = q[idx[members]]
            simp = tri.find_simplex(qq)
            good = simp >= 0
            if not good.any():
                continue
            T = tri.transform[simp[good]]
            b = np.einsum("nij,nj->ni", T[:, :2], qq[good] - T[:, 2])
            bc = np.column_stack([b, 1 - b.sum(axis=1)])
            verts = tri.simplices[simp[good]]
            z = (bc * local[verts, 2]).sum(axis=1)
            # no long edges bridging data gaps: every vertex of the triangle within 2 × max_dist of the query point
            far = np.hypot(local[verts, 0] - qq[good][:, :1], local[verts, 1] - qq[good][:, 1:2]).max(axis=1) > 2 * self.max_dist
            z[far] = np.nan
            out[idx[members[good]]] = z
        return out


class Tin(Surface):
    kind = "tin"

    def __init__(self, source, fmt, verts, tris, crs=None, notes=None):
        V_ = np.asarray(verts, float).reshape(-1, 3)
        T_ = np.asarray(tris, int).reshape(-1, 3)
        T_ = T_[(T_ >= 0).all(axis=1) & (T_ < len(V_)).all(axis=1)]
        if len(T_) == 0:
            raise ValueError("mesh without triangles")
        self.V, self.T = V_, T_
        P = V_[T_][:, :, :2]
        lo, hi = P.min(axis=1), P.max(axis=1)
        ext = (float(lo[:, 0].min()), float(lo[:, 1].min()), float(hi[:, 0].max()), float(hi[:, 1].max()))
        size = np.median(np.maximum(hi - lo, 1e-9).max(axis=1))
        self.cell = float(max(size, (ext[2] - ext[0] + ext[3] - ext[1]) / 2 / max(np.sqrt(len(T_)), 1), 1e-6))
        self.x0, self.y0 = ext[0], ext[1]
        i0 = np.floor((lo - [self.x0, self.y0]) / self.cell).astype(int)
        i1 = np.floor((hi - [self.x0, self.y0]) / self.cell).astype(int)
        idx = {}
        for t in range(len(T_)):
            for ix in range(i0[t, 0], i1[t, 0] + 1):
                for iy in range(i0[t, 1], i1[t, 1] + 1):
                    idx.setdefault((ix, iy), []).append(t)
        self.index = {k: np.array(v) for k, v in idx.items()}
        info = {"format": fmt, "n_triangles": int(len(T_)), "n_points": int(len(V_)), "extent": ext, "resolution": float(size),
                "crs": crs or {}, "notes": list(notes or [])}
        super().__init__(source, fmt, info)

    def sample(self, x, y) -> np.ndarray:
        x, y = np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(y, float))
        out = np.full(len(x), np.nan)
        for n in range(len(x)):
            if not (np.isfinite(x[n]) and np.isfinite(y[n])):
                continue
            key = (int(np.floor((x[n] - self.x0) / self.cell)), int(np.floor((y[n] - self.y0) / self.cell)))
            cand = self.index.get(key)
            if cand is None:
                continue
            P = self.V[self.T[cand]]
            a, b, c = P[:, 0], P[:, 1], P[:, 2]
            v0, v1 = b[:, :2] - a[:, :2], c[:, :2] - a[:, :2]
            v2 = np.array([x[n], y[n]]) - a[:, :2]
            den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
            with np.errstate(divide="ignore", invalid="ignore"):
                l1 = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
                l2 = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
            l0 = 1 - l1 - l2
            e = -1e-9
            inside = (den != 0) & (l0 >= e) & (l1 >= e) & (l2 >= e)
            if inside.any():
                z = l0 * a[:, 2] + l1 * b[:, 2] + l2 * c[:, 2]
                out[n] = float(z[inside].max())
        return out


def _densify(lines, step: float) -> np.ndarray:
    pts = []
    for arr, _, _ in lines:
        arr = np.asarray(arr, float)
        for a, b in zip(arr[:-1], arr[1:]):
            L = float(np.hypot(*(b[:2] - a[:2])))
            k = max(1, int(np.ceil(L / step)))
            t = np.linspace(0, 1, k, endpoint=False)[:, None]
            pts.append(a + t * (b - a))
        pts.append(arr[-1:])
    return np.vstack(pts) if pts else np.zeros((0, 3))


def _from_geometry(path: str, fmt: str, g: V.Geometry, max_dist=None) -> Surface:
    if g.triangles:
        return Tin(path, fmt + " mesh", g.vertices, g.triangles, g.crs, g.notes)
    lines = [ln for ln in g.lines if ln[2] and np.isfinite(ln[0][:, 2]).all()]
    pts = [p for p in g.points if np.isfinite(p[2])]
    if lines:
        seg = np.concatenate([np.hypot(*np.diff(ln[0][:, :2], axis=0).T) for ln in lines if len(ln[0]) > 1] or [np.array([1.0])])
        step = float(np.median(seg[seg > 0])) if (seg > 0).any() else 1.0
        P = _densify(lines, step)
        if pts:
            P = np.vstack([P, np.array(pts)])
        return PointCloud(path, fmt + " contours", P, max_dist, contour=True, crs=g.crs, notes=g.notes)
    if pts:
        return PointCloud(path, fmt + " points", np.array(pts), max_dist, crs=g.crs, notes=g.notes)
    raise ValueError(f"{Path(path).name}: no elevation data found (points, contours with elevation or triangles)")


def read_xyz(path: str, max_dist=None) -> Surface:
    """XYZ text or spreadsheet (any delimiter, optional header). A regular lattice becomes a grid; anything else a point cloud."""
    from ..core.normalise import header_key, parse_numbers
    from .mapping import SYN, _score
    from .readers import read_file
    p = Path(path)
    arr = None
    if p.suffix.lower() in (".xyz", ".txt", ".pts", ".dat", ".csv"):
        rows = []
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            t = re.split(r"[,\s;]+", ln.strip())
            if len(t) >= 3:
                try:
                    rows.append((float(t[0]), float(t[1]), float(t[2])))
                except ValueError:
                    continue
        if len(rows) >= 3:
            arr = np.array(rows)
    if arr is None:
        df = read_file(path)[0].df
        keys = {c: header_key(c) for c in df.columns}
        cols = []
        for f in ("x", "y", "z"):
            best = max(df.columns, key=lambda c: _score(keys[c], SYN[f]))
            cols.append(best if _score(keys[best], SYN[f]) > 0 else None)
        if None in cols or len(set(cols)) < 3:
            cols = list(df.columns)[:3]
        arr = np.column_stack([parse_numbers(df[c])[0].to_numpy(float) for c in cols])
    arr = arr[np.isfinite(arr).all(axis=1)]
    ux, uy = np.unique(arr[:, 0]), np.unique(arr[:, 1])
    if len(ux) > 2 and len(uy) > 2 and len(ux) * len(uy) == len(arr):
        dx, dy = np.diff(ux), np.diff(uy)
        if np.ptp(dx) < 1e-6 * max(dx.mean(), 1e-12) and np.ptp(dy) < 1e-6 * max(dy.mean(), 1e-12):
            ix = np.round((arr[:, 0] - ux[0]) / dx.mean()).astype(int)
            iy = np.round((arr[:, 1] - uy[0]) / dy.mean()).astype(int)
            g = np.full((len(uy), len(ux)), np.nan)
            g[iy, ix] = arr[:, 2]
            return Grid(path, "regular XYZ grid", len(uy), len(ux), (dx.mean(), 0.0, ux[0], 0.0, dy.mean(), uy[0]), _array_getter(g))
    return PointCloud(path, "XYZ points", arr, max_dist)


# ---- detection -----------------------------------------------------------------------------------------------------
FORMATS = {
    "asc": read_asc, "grd": read_surfer, "surfer": read_surfer, "bil": read_bil, "bip": read_bil, "bsq": read_bil, "flt": read_bil,
    "tif": read_geotiff, "tiff": read_geotiff, "geotiff": read_geotiff, "hgt": read_hgt, "xyz": read_xyz,
}
VECTOR = {"dxf": V.read_dxf, "shp": V.read_shp, "kml": V.read_kml, "kmz": V.read_kml, "str": V.read_surpac, "dtm": V.read_surpac,
          "obj": V.read_obj, "stl": V.read_stl, "ply": V.read_ply, "geojson": V.read_geojson, "json": V.read_geojson}
NAMES = {"dxf": "DXF", "shp": "Shapefile", "kml": "KML", "kmz": "KMZ", "str": "Surpac", "dtm": "Surpac", "obj": "OBJ", "stl": "STL",
         "ply": "PLY", "geojson": "GeoJSON", "json": "GeoJSON"}
UNSUPPORTED = {"00t": "Vulcan .00t triangulations have no public specification", "dm": "Datamine .dm files have no public specification",
               "ecw": "ECW is a proprietary compressed raster", "sid": "MrSID is a proprietary compressed raster",
               "jp2": "JPEG 2000 rasters are not supported"}


def detect(path: str) -> str:
    p = Path(path)
    ext = p.suffix.lower().lstrip(".")
    with open(p, "rb") as f:
        head = f.read(64)
    if head[:4] in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
        return "tif"
    if head[:4] in (b"DSAA", b"DSBB", b"DSRB"):
        return "grd"
    if head[:3] == b"ply":
        return "ply"
    if head[:4] == b"\x00\x00\x27\x0a":
        return "shp"
    if head[:2] == b"PK" and ext in ("kmz", "zip"):
        return "kmz"
    txt = head.decode("latin-1", errors="replace").lower()
    if "<kml" in txt or (txt.lstrip().startswith("<?xml") and ext in ("kml", "xml")):
        return "kml"
    if ext in UNSUPPORTED:
        return ext
    if ext in ("csv", "txt", "pts", "dat", "xlsx", "xls"):
        return "xyz"
    if txt.strip().startswith("0") and "section" in txt and ext != "str":
        return "dxf"
    return ext


def read_surface(path: str, fmt: str | None = None, max_dist: float | None = None) -> Surface:
    """Read any supported topography. `fmt` overrides detection (asc, grd, bil, flt, tif, hgt, xyz, dxf, shp, kml, kmz,
    str, obj, stl, ply, geojson). Unsupported variants raise a clear message, never a silent wrong result."""
    f = (fmt or detect(path)).lower()
    if f in UNSUPPORTED:
        raise ValueError(f"{Path(path).name}: {UNSUPPORTED[f]}; export the surface as GeoTIFF, ASCII grid, DXF or XYZ")
    if f in FORMATS:
        return FORMATS[f](path) if f != "xyz" else read_xyz(path, max_dist)
    if f in VECTOR:
        return _from_geometry(path, NAMES[f], VECTOR[f](path), max_dist)
    raise ValueError(f"{Path(path).name}: topography format '{f}' is not supported")


# ---- coordinate bridge ---------------------------------------------------------------------------------------------
class GeographicBridge(Surface):
    """A geographic (lon/lat) surface queried with UTM coordinates: each point is converted to WGS 84 first."""

    def __init__(self, inner: Surface, zone: int, south: bool, note: str):
        self.inner, self.zone, self.south = inner, zone, south
        info = dict(inner.info)
        from .geo import wgs84_to_utm
        if inner.extent:
            x0, y0, x1, y1 = inner.extent
            E, N, _, _ = wgs84_to_utm(np.array([y0, y0, y1, y1]), np.array([x0, x1, x0, x1]), zone=zone, south=south)
            info["extent_geographic"] = inner.extent
            info["extent"] = (float(E.min()), float(N.min()), float(E.max()), float(N.max()))
        info["notes"] = list(info.get("notes", [])) + [note]
        super().__init__(inner.source, inner.fmt, info)
        self.kind = inner.kind

    def _ll(self, x, y):
        from .geo import utm_to_wgs84
        lat, lon = utm_to_wgs84(x, y, self.zone, self.south)
        return lon, lat

    def sample(self, x, y):
        lon, lat = self._ll(x, y)
        return self.inner.sample(lon, lat)

    def support(self, x, y):
        lon, lat = self._ll(x, y)
        s = self.inner.support(lon, lat)
        return np.where(np.isfinite(s) & (s > 0), s * 111320.0, s)      # degrees → approximate metres


def align(surface: Surface, params: dict, collar_x, collar_y) -> tuple[Surface, list[str]]:
    """Put a surface in the collars' coordinate system. Geographic surfaces (SRTM, KML, lon/lat files) queried with UTM
    collars go through WGS 84 → UTM, in the declared zone or, failing that, the zone of the surface itself (reported).
    Non-WGS 84 datums are reported; no datum shift is applied."""
    from .geo import looks_geographic, project_crs, utm_zone
    notes = []
    crs = surface.crs or {}
    if crs.get("datum") not in (None, "WGS84", "unknown"):
        notes.append(f"topography datum {crs['datum']} declared: no datum shift is applied (WGS 84 only)")
    geographic = crs.get("kind") == "geographic" or (surface.extent is not None and looks_geographic(surface.extent[0::2], surface.extent[1::2]))
    if not geographic or looks_geographic(collar_x, collar_y):
        pc = project_crs(params)
        if crs.get("kind") == "utm" and pc.get("kind") == "utm" and (crs.get("zone"), crs.get("south")) != (pc.get("zone"), pc.get("south")):
            notes.append(f"topography is UTM zone {crs.get('zone')}{'S' if crs.get('south') else 'N'} but the project declares zone {pc['zone']}{'S' if pc['south'] else 'N'}")
        return surface, notes
    pc = project_crs(params)
    if pc.get("kind") == "utm":
        zone, south, how = pc["zone"], pc["south"], "declared"
    else:
        x0, y0, x1, y1 = surface.extent
        zone, south, how = int(utm_zone((x0 + x1) / 2, (y0 + y1) / 2)), (y0 + y1) / 2 < 0, "inferred from the topography location (declare crs.utm_zone to confirm)"
    note = f"geographic topography converted to UTM zone {zone}{'S' if south else 'N'} ({how})"
    notes.append(note)
    return GeographicBridge(surface, zone, south, note), notes
