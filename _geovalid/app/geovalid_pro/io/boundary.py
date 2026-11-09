"""Licence boundary (v2 brief F9, COL-005): KML / KMZ, Shapefile polygons (.prj read for information), GeoJSON, DXF
closed polylines and CSV / TXT / XLSX vertex lists (optionally with a part or ring column). Multipart polygons and
holes are handled with the even–odd ray-casting rule over all rings."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import vector as V


class Boundary:
    def __init__(self, polygons: list[list[np.ndarray]], source: str, fmt: str, crs: dict | None = None, notes=None):
        self.polygons = [[_close(np.asarray(r, float)[:, :2]) for r in poly if len(r) >= 3] for poly in polygons]
        self.polygons = [p for p in self.polygons if p]
        if not self.polygons:
            raise ValueError("licence boundary without a polygon of at least 3 vertices")
        self.source, self.fmt, self.crs, self.notes = source, fmt, crs or {}, list(notes or [])

    @property
    def rings(self) -> list[np.ndarray]:
        return [r for p in self.polygons for r in p]

    @property
    def extent(self):
        a = np.vstack(self.rings)
        return float(a[:, 0].min()), float(a[:, 1].min()), float(a[:, 0].max()), float(a[:, 1].max())

    def contains(self, x, y) -> np.ndarray:
        """Even–odd rule over every ring: holes and separate parts come out right."""
        x, y = np.asarray(x, float), np.asarray(y, float)
        inside = np.zeros(x.shape, bool)
        for r in self.rings:
            inside ^= _pip(x, y, r)
        return inside

    def distance(self, x, y) -> np.ndarray:
        x, y = np.asarray(x, float)[:, None], np.asarray(y, float)[:, None]
        best = np.full(x.shape[0], np.inf)
        for r in self.rings:
            ax, ay, bx, by = r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]
            dx, dy = bx - ax, by - ay
            t = np.clip(((x - ax) * dx + (y - ay) * dy) / np.maximum(dx * dx + dy * dy, 1e-12), 0, 1)
            best = np.minimum(best, np.sqrt((x - (ax + t * dx)) ** 2 + (y - (ay + t * dy)) ** 2).min(axis=1))
        return best

    def info(self) -> dict:
        return {"format": self.fmt, "polygons": len(self.polygons), "rings": len(self.rings),
                "vertices": int(sum(len(r) - 1 for r in self.rings)), "extent": self.extent, "crs": self.crs, "notes": self.notes}


def _close(r: np.ndarray) -> np.ndarray:
    return r if np.allclose(r[0], r[-1]) else np.vstack([r, r[:1]])


def _pip(x, y, ring) -> np.ndarray:
    """Ray casting (crossing number) for one ring, vectorised over points."""
    xs, ys = ring[:-1, 0], ring[:-1, 1]
    xe, ye = ring[1:, 0], ring[1:, 1]
    px, py = x[..., None], y[..., None]
    cond = (ys > py) != (ye > py)
    with np.errstate(divide="ignore", invalid="ignore"):
        xc = xs + (py - ys) * (xe - xs) / (ye - ys)
    return (cond & (px < xc)).sum(axis=-1) % 2 == 1


def _vertex_table(path: str) -> list[list[np.ndarray]]:
    from ..core.normalise import header_key, parse_numbers
    from .mapping import SYN, _score
    from .readers import read_file
    p = Path(path)
    if p.suffix.lower() in (".csv", ".xlsx", ".xls"):
        df = read_file(path)[0].df
        keys = {c: header_key(c) for c in df.columns}
        cx = max(df.columns, key=lambda c: _score(keys[c], SYN["x"]))
        cy = max(df.columns, key=lambda c: _score(keys[c], SYN["y"]))
        if cx == cy or _score(keys[cx], SYN["x"]) == 0 or _score(keys[cy], SYN["y"]) == 0:
            num = [c for c in df.columns if parse_numbers(df[c])[0].notna().mean() > 0.9]
            cx, cy = (num + list(df.columns))[:2]
        part = next((c for c, k in keys.items() if k in ("part", "ring", "polygon", "poly", "id", "partid", "ringid", "shape", "block")), None)
        xy = np.column_stack([parse_numbers(df[cx])[0], parse_numbers(df[cy])[0]])
        groups = df[part].astype(str).to_numpy() if part else np.zeros(len(df), dtype=object)
        polys = []
        for g in dict.fromkeys(groups):
            r = xy[groups == g]
            r = r[np.isfinite(r).all(axis=1)]
            if len(r) >= 3:
                polys.append([r])
        return polys
    rows = []
    polys = []
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        t = ln.replace(",", " ").replace(";", " ").split()
        try:
            rows.append((float(t[0]), float(t[1])))
        except (ValueError, IndexError):
            if len(rows) >= 3:              # a blank or text line separates parts
                polys.append([np.array(rows)])
            rows = []
    if len(rows) >= 3:
        polys.append([np.array(rows)])
    return polys


def read_boundary(path: str, fmt: str | None = None) -> Boundary:
    p = Path(path)
    f = (fmt or p.suffix.lower().lstrip(".")).lower()
    if f in ("kml", "kmz"):
        g = V.read_kml(path)
        polys = g.polygons or [[ln[0][:, :2]] for ln in g.lines if ln[1]]
        return Boundary(polys, path, f.upper(), g.crs, g.notes)
    if f == "shp":
        g = V.read_shp(path)
        polys = g.polygons or [[ln[0][:, :2]] for ln in g.lines if ln[1] or np.allclose(ln[0][0, :2], ln[0][-1, :2])]
        notes = list(g.notes) + ([] if g.crs else ["no .prj file: coordinates taken as the project's"])
        return Boundary(polys, path, "Shapefile", g.crs, notes)
    if f in ("geojson", "json"):
        g = V.read_geojson(path)
        return Boundary(g.polygons, path, "GeoJSON", g.crs, g.notes)
    if f == "dxf":
        g = V.read_dxf(path)
        polys = [[ln[0][:, :2]] for ln in g.lines if ln[1] or (len(ln[0]) > 3 and np.allclose(ln[0][0, :2], ln[0][-1, :2]))]
        if not polys:
            raise ValueError("DXF has no closed polyline for the licence boundary")
        return Boundary(polys, path, "DXF", {}, g.notes)
    return Boundary(_vertex_table(path), path, "vertex list", {}, [])


def align_boundary(b: Boundary, params: dict, collar_x, collar_y) -> tuple[Boundary, list[str]]:
    """Geographic boundaries (KML, lon/lat GeoJSON) are converted to the collars' UTM zone (declared, or inferred from the
    boundary location and reported)."""
    from .geo import looks_geographic, project_crs, utm_zone, wgs84_to_utm
    notes = []
    if b.crs.get("datum") not in (None, "WGS84", "unknown"):
        notes.append(f"boundary datum {b.crs['datum']}: no datum shift is applied (WGS 84 only)")
    x0, y0, x1, y1 = b.extent
    geo = b.crs.get("kind") == "geographic" or looks_geographic([x0, x1], [y0, y1])
    if not geo or looks_geographic(collar_x, collar_y):
        return b, notes
    pc = project_crs(params)
    if pc.get("kind") == "utm":
        zone, south, how = pc["zone"], pc["south"], "declared"
    else:
        zone, south, how = int(utm_zone((x0 + x1) / 2, (y0 + y1) / 2)), (y0 + y1) / 2 < 0, "inferred from the boundary location (declare crs.utm_zone to confirm)"
    polys = []
    for poly in b.polygons:
        rings = []
        for r in poly:
            E, N, _, _ = wgs84_to_utm(r[:, 1], r[:, 0], zone=zone, south=south)
            rings.append(np.column_stack([E, N]))
        polys.append(rings)
    note = f"geographic boundary converted to UTM zone {zone}{'S' if south else 'N'} ({how})"
    out = Boundary(polys, b.source, b.fmt, {"kind": "utm", "zone": zone, "south": south, "datum": "WGS84"}, b.notes + [note])
    return out, notes + [note]
