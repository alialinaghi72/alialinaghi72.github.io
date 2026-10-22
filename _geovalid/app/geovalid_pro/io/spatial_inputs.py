"""DEM (ESRI ASCII grid .asc, XYZ point files → TIN) and licence polygon (vertex list) readers."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .readers import read_file
from .mapping import SYN, _score
from ..core.normalise import header_key, parse_numbers


class Dem:
    def __init__(self, kind: str, source: str, sampler, resolution: float | None, n_points: int, extent):
        self.kind, self.source, self._sampler = kind, source, sampler
        self.resolution, self.n_points, self.extent = resolution, n_points, extent

    def sample(self, x, y) -> np.ndarray:
        return self._sampler(np.asarray(x, float), np.asarray(y, float))


def _read_asc(path: str) -> Dem:
    header, n = {}, 0
    with open(path, encoding="ascii", errors="replace") as f:
        for _ in range(6):
            pos = f.tell()
            line = f.readline().split()
            if len(line) == 2 and line[0].lower() in ("ncols", "nrows", "xllcorner", "yllcorner", "xllcenter",
                                                      "yllcenter", "cellsize", "nodata_value"):
                header[line[0].lower()] = float(line[1])
                n += 1
            else:
                f.seek(pos)
                break
        data = np.loadtxt(f, dtype=float)
    nc, nr, cs = int(header["ncols"]), int(header["nrows"]), header["cellsize"]
    data = data.reshape(nr, nc)
    nod = header.get("nodata_value", -9999.0)
    data[data == nod] = np.nan
    x0 = header["xllcenter"] if "xllcenter" in header else header["xllcorner"] + cs / 2
    y0 = header["yllcenter"] if "yllcenter" in header else header["yllcorner"] + cs / 2
    grid = data[::-1]          # row 0 = southernmost

    def sampler(x, y):
        fx, fy = (x - x0) / cs, (y - y0) / cs
        i0, j0 = np.floor(fy).astype(int), np.floor(fx).astype(int)
        out = np.full(len(x), np.nan)
        ok = (i0 >= 0) & (j0 >= 0) & (i0 < nr - 1) & (j0 < nc - 1)
        i, j, ty, tx = i0[ok], j0[ok], fy[ok] - i0[ok], fx[ok] - j0[ok]
        z = (grid[i, j] * (1 - tx) * (1 - ty) + grid[i, j + 1] * tx * (1 - ty)
             + grid[i + 1, j] * (1 - tx) * ty + grid[i + 1, j + 1] * tx * ty)
        out[ok] = z
        return out

    ext = (x0, y0, x0 + (nc - 1) * cs, y0 + (nr - 1) * cs)
    return Dem("ESRI ASCII grid", path, sampler, cs, int(np.isfinite(data).sum()), ext)


def _xyz_columns(df: pd.DataFrame) -> tuple[str, str, str]:
    keys = {c: header_key(c) for c in df.columns}
    pick = []
    for f in ("x", "y", "z"):
        best = max(df.columns, key=lambda c: _score(keys[c], SYN[f]))
        pick.append(best if _score(keys[best], SYN[f]) > 0 else None)
    if None in pick or len(set(pick)) < 3:
        cols = list(df.columns)[:3]
        if len(cols) < 3:
            raise ValueError("XYZ file needs three columns (x, y, z)")
        return tuple(cols)
    return tuple(pick)


def _read_xyz(path: str) -> Dem:
    from scipy.interpolate import LinearNDInterpolator
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace").splitlines()
    first = text[0].replace(",", " ").split() if text else []
    if first and all(_is_float(t) for t in first[:3]):
        arr = np.loadtxt([ln.replace(",", " ") for ln in text if ln.strip()], dtype=float)[:, :3]
    else:
        df = read_file(path)[0].df
        cx, cy, cz = _xyz_columns(df)
        arr = np.column_stack([parse_numbers(df[c])[0].to_numpy() for c in (cx, cy, cz)])
    arr = arr[np.isfinite(arr).all(axis=1)]
    interp = LinearNDInterpolator(arr[:, :2], arr[:, 2])
    nn = np.median(np.sqrt(np.diff(np.sort(arr[:, 0])) ** 2)) if len(arr) > 3 else None
    ext = (arr[:, 0].min(), arr[:, 1].min(), arr[:, 0].max(), arr[:, 1].max())
    return Dem("XYZ points (Delaunay TIN)", path, lambda x, y: interp(x, y), nn, len(arr), ext)


def _is_float(t: str) -> bool:
    try:
        float(t)
        return True
    except ValueError:
        return False


def read_dem(path: str) -> Dem:
    ext = Path(path).suffix.lower()
    if ext == ".asc":
        return _read_asc(path)
    if ext in (".xyz", ".csv", ".txt", ".xlsx", ".xls", ".pts"):
        return _read_xyz(path)
    raise ValueError(f"DEM format {ext} not supported in v0.1 (use .asc grid or .xyz/.csv points)")


def read_polygon(path: str) -> np.ndarray:
    """Licence polygon: a vertex list (x y or x,y per line, optional header); closed automatically."""
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls", ".csv"):
        df = read_file(path)[0].df
        cols = [c for c in df.columns if _score(header_key(c), SYN["x"]) > 0 or _score(header_key(c), SYN["y"]) > 0]
        cx, cy = (cols[:2] if len(cols) >= 2 else list(df.columns)[:2])
        xy = np.column_stack([parse_numbers(df[cx])[0], parse_numbers(df[cy])[0]])
    else:
        rows = []
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            t = ln.replace(",", " ").replace(";", " ").split()
            if len(t) >= 2 and _is_float(t[0]) and _is_float(t[1]):
                rows.append((float(t[0]), float(t[1])))
        xy = np.array(rows, float)
    xy = xy[np.isfinite(xy).all(axis=1)]
    if len(xy) < 3:
        raise ValueError("licence polygon needs at least 3 vertices")
    if not np.allclose(xy[0], xy[-1]):
        xy = np.vstack([xy, xy[0]])
    return xy
