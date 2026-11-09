"""Phase 2 R2: topography in every supported format, coordinates, licence boundaries and the topography rules.

A planar surface z = 1000 + 0.02·(x − X0) − 0.01·(y − Y0) is written in each format and read back: bilinear grids,
barycentric meshes and local Delaunay on points / contours are all exact on a plane, so every reader must return it
within 1e-6 m.
"""
import struct
import zipfile

import numpy as np
import pandas as pd
import pytest

from geovalid_pro.engine import ProjectSpec, load_inputs, load_params, run
from geovalid_pro.io.boundary import read_boundary
from geovalid_pro.io.geo import describe_wkt, utm_to_wgs84, wgs84_to_utm
from geovalid_pro.io.tiff import write_tiff
from geovalid_pro.io.topo import read_surface

X0, Y0, NX, NY, DX = 500000.0, 3900000.0, 41, 31, 25.0


def plane(x, y):
    return 1000 + 0.02 * (np.asarray(x) - X0) - 0.01 * (np.asarray(y) - Y0)


def lattice():
    xs = X0 + DX * np.arange(NX)
    ys = Y0 + DX * np.arange(NY)
    return xs, ys, plane(*np.meshgrid(xs, ys))          # row 0 = south


QX = X0 + np.array([37.3, 400.0, 812.6, 950.1, 123.4])
QY = Y0 + np.array([41.9, 300.0, 650.2, 222.2, 701.0])


# ---- writers --------------------------------------------------------------------------------------------------------
def w_asc(d):
    xs, ys, z = lattice()
    f = d / "s.asc"
    with open(f, "w") as o:
        o.write(f"ncols {NX}\nnrows {NY}\nxllcorner {X0 - DX / 2}\nyllcorner {Y0 - DX / 2}\ncellsize {DX}\nNODATA_value -9999\n")
        np.savetxt(o, z[::-1], fmt="%.6f")
    return f


def w_dsaa(d):
    xs, ys, z = lattice()
    f = d / "s.grd"
    with open(f, "w") as o:
        o.write(f"DSAA\n{NX} {NY}\n{xs[0]} {xs[-1]}\n{ys[0]} {ys[-1]}\n{z.min()} {z.max()}\n")
        np.savetxt(o, z, fmt="%.6f")
    return f


def w_dsbb(d):
    xs, ys, z = lattice()
    f = d / "s6.grd"
    f.write_bytes(b"DSBB" + struct.pack("<2h6d", NX, NY, xs[0], xs[-1], ys[0], ys[-1], z.min(), z.max()) + z.astype("<f4").tobytes())
    return f


def w_dsrb(d):
    xs, ys, z = lattice()
    f = d / "s7.grd"
    grid = struct.pack("<2i8d", NY, NX, xs[0], ys[0], DX, DX, z.min(), z.max(), 0.0, 1.70141e38)
    f.write_bytes(b"DSRB" + struct.pack("<2i", 4, 2) + b"GRID" + struct.pack("<i", len(grid)) + grid
                  + b"DATA" + struct.pack("<i", z.size * 8) + z.astype("<f8").tobytes())
    return f


def w_bil(d, layout):
    xs, ys, z = lattice()
    f = d / f"s.{layout}"
    a = z[::-1].astype(">f4")
    if layout == "bil":
        data = np.stack([a, a + 1], axis=1)
    elif layout == "bip":
        data = np.stack([a, a + 1], axis=2)
    else:
        data = np.stack([a, a + 1], axis=0)
    f.write_bytes(data.astype(">f4").tobytes())
    (d / f"s.hdr").write_text(f"nrows {NY}\nncols {NX}\nnbands 2\nnbits 32\npixeltype float\nbyteorder M\nlayout {layout}\n"
                              f"ulxmap {xs[0]}\nulymap {ys[-1]}\nxdim {DX}\nydim {DX}\n")
    return f


def w_flt(d):
    xs, ys, z = lattice()
    f = d / "f.flt"
    f.write_bytes(z[::-1].astype("<f4").tobytes())
    (d / "f.hdr").write_text(f"ncols {NX}\nnrows {NY}\nxllcorner {X0 - DX / 2}\nyllcorner {Y0 - DX / 2}\ncellsize {DX}\nNODATA_value -9999\nbyteorder LSBFIRST\n")
    return f


def w_tif(d, **kw):
    xs, ys, z = lattice()
    f = d / f"s_{kw.get('compression', 1)}_{kw.get('tile')}.tif"
    write_tiff(str(f), z[::-1].astype(np.float64), affine_ul=(X0 - DX / 2, ys[-1] + DX / 2, DX, DX), epsg=32639, nodata=-9999, **kw)
    return f


def w_xyz_grid(d):
    xs, ys, z = lattice()
    X, Y = np.meshgrid(xs, ys)
    f = d / "g.xyz"
    np.savetxt(f, np.column_stack([X.ravel(), Y.ravel(), z.ravel()]), fmt="%.6f")
    return f


def scattered():
    rng = np.random.default_rng(3)
    x = X0 + rng.uniform(-50, 1050, 900)
    y = Y0 + rng.uniform(-50, 800, 900)
    return np.column_stack([x, y, plane(x, y)])


def w_points_csv(d):
    p = scattered()
    f = d / "pts.csv"
    pd.DataFrame(p, columns=["Easting", "Northing", "Elevation"]).to_csv(f, index=False)
    return f


def contours():
    """Contour lines of the plane (straight lines of constant z), every 2 m."""
    out = []
    for z in np.arange(985, 1022, 2.0):
        # 0.02 (x - X0) - 0.01 (y - Y0) = z - 1000  →  x = X0 + (z - 1000 + 0.01 (y - Y0)) / 0.02
        yy = Y0 + np.linspace(-60, 820, 12)
        xx = X0 + (z - 1000 + 0.01 * (yy - Y0)) / 0.02
        out.append(np.column_stack([xx, yy, np.full(len(yy), z)]))
    return out


def tri_mesh():
    xs, ys, z = lattice()
    X, Y = np.meshgrid(xs, ys)
    V = np.column_stack([X.ravel(), Y.ravel(), z.ravel()])
    T = []
    for r in range(NY - 1):
        for c in range(NX - 1):
            a, b, cc, dd = r * NX + c, r * NX + c + 1, (r + 1) * NX + c, (r + 1) * NX + c + 1
            T += [(a, b, dd), (a, dd, cc)]
    return V, np.array(T)


def w_dxf(d, what):
    f = d / f"{what}.dxf"
    L = ["0", "SECTION", "2", "ENTITIES"]
    if what == "points":
        for x, y, z in scattered():
            L += ["0", "POINT", "8", "TOPO", "10", f"{x}", "20", f"{y}", "30", f"{z}"]
    elif what == "3dface":
        V, T = tri_mesh()
        for t in T:
            p = V[t]
            L += ["0", "3DFACE", "8", "T"] + [s for i in range(4) for s in (f"1{i}", f"{p[min(i, 2), 0]}", f"2{i}", f"{p[min(i, 2), 1]}", f"3{i}", f"{p[min(i, 2), 2]}")]
    elif what == "polyface":
        V, T = tri_mesh()
        L += ["0", "POLYLINE", "8", "T", "66", "1", "70", "64", "71", str(len(V)), "72", str(len(T))]
        for x, y, z in V:
            L += ["0", "VERTEX", "8", "T", "10", f"{x}", "20", f"{y}", "30", f"{z}", "70", "192"]
        for t in T:
            L += ["0", "VERTEX", "8", "T", "10", "0", "20", "0", "30", "0", "70", "128", "71", str(t[0] + 1), "72", str(t[1] + 1), "73", str(t[2] + 1)]
        L += ["0", "SEQEND"]
    elif what == "lwpoly":
        for c in contours():
            L += ["0", "LWPOLYLINE", "8", "CONT", "90", str(len(c)), "70", "0", "38", f"{c[0, 2]}"]
            for x, y, _ in c:
                L += ["10", f"{x}", "20", f"{y}"]
    elif what == "poly3d":
        for c in contours():
            L += ["0", "POLYLINE", "8", "CONT", "66", "1", "70", "8"]
            for x, y, z in c:
                L += ["0", "VERTEX", "8", "CONT", "10", f"{x}", "20", f"{y}", "30", f"{z}", "70", "32"]
            L += ["0", "SEQEND"]
    L += ["0", "ENDSEC", "0", "EOF"]
    f.write_text("\n".join(L) + "\n")
    return f


def w_surpac(d):
    V, T = tri_mesh()
    s = ["topo, 01-Jan-26,  ,", "0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000"]
    s += [f"1, {y:.6f}, {x:.6f}, {z:.6f}," for x, y, z in V]
    s += ["0, 0.000, 0.000, 0.000,", "0, 0.000, 0.000, 0.000, END"]
    (d / "topo.str").write_text("\n".join(s) + "\n")
    t = ["topo.str,  01-Jan-26,  ,", "0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000", "OBJECT, 1,", "TRISOLATION, 1, neighbours=no,validated=true,closed=no"]
    t += [f"{i + 1}, {a + 1}, {b + 1}, {c + 1}, 0, 0, 0," for i, (a, b, c) in enumerate(T)]
    t += ["END"]
    (d / "topo.dtm").write_text("\n".join(t) + "\n")
    return d / "topo.dtm"


def w_obj(d):
    V, T = tri_mesh()
    f = d / "s.obj"
    f.write_text("\n".join([f"v {x} {y} {z}" for x, y, z in V] + [f"f {a + 1} {b + 1} {c + 1}" for a, b, c in T]) + "\n")
    return f


def w_stl(d, binary):
    V, T = tri_mesh()
    f = d / f"s_{'b' if binary else 'a'}.stl"
    if binary:
        rec = np.zeros(len(T), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
        rec["v"] = (V[T] - [X0, Y0, 0]).astype("<f4")             # float32: stored relative to the origin
        f.write_bytes(b"\0" * 80 + struct.pack("<I", len(T)) + rec.tobytes())
    else:
        lines = ["solid topo"]
        for t in T:
            lines += ["facet normal 0 0 1", "outer loop"] + [f"vertex {x} {y} {z}" for x, y, z in V[t]] + ["endloop", "endfacet"]
        f.write_text("\n".join(lines + ["endsolid topo"]) + "\n")
    return f


def w_ply(d, binary):
    V, T = tri_mesh()
    f = d / f"s_{'b' if binary else 'a'}.ply"
    head = f"ply\nformat {'binary_little_endian' if binary else 'ascii'} 1.0\nelement vertex {len(V)}\nproperty double x\nproperty double y\nproperty double z\n" \
           f"element face {len(T)}\nproperty list uchar int vertex_indices\nend_header\n"
    if binary:
        body = V.astype("<f8").tobytes() + b"".join(struct.pack("<B3i", 3, *t) for t in T)
        f.write_bytes(head.encode() + body)
    else:
        f.write_text(head + "\n".join(f"{x} {y} {z}" for x, y, z in V) + "\n" + "\n".join(f"3 {a} {b} {c}" for a, b, c in T) + "\n")
    return f


def _shp(path, shapes, stype):
    recs = b""
    for i, s in enumerate(shapes):
        recs += struct.pack(">2i", i + 1, len(s) // 2) + s
    hdr = struct.pack(">7i", 9994, 0, 0, 0, 0, 0, (100 + len(recs)) // 2) + struct.pack("<2i", 1000, stype) + struct.pack("<8d", *([0.0] * 8))
    path.write_bytes(hdr + recs)


def w_shp(d, kind):
    f = d / f"{kind}.shp"
    if kind == "pointz":
        _shp(f, [struct.pack("<i4d", 11, x, y, z, 0.0) for x, y, z in scattered()], 11)
    elif kind == "polylinez":
        out = []
        for c in contours():
            n = len(c)
            s = struct.pack("<i4d2i", 13, c[:, 0].min(), c[:, 1].min(), c[:, 0].max(), c[:, 1].max(), 1, n) + struct.pack("<i", 0)
            s += c[:, :2].astype("<f8").tobytes() + struct.pack("<2d", c[:, 2].min(), c[:, 2].max()) + c[:, 2].astype("<f8").tobytes()
            out.append(s)
        _shp(f, out, 13)
    return f


def geo_plane(lon, lat):
    return 800 + 50 * (np.asarray(lon) - 51.0) - 30 * (np.asarray(lat) - 35.0)


def w_hgt(d):
    n = 1201
    lon = 51 + np.arange(n) / (n - 1)
    lat = 36 - np.arange(n) / (n - 1)
    LON, LAT = np.meshgrid(lon, lat)
    f = d / "N35E051.hgt"
    f.write_bytes(np.round(geo_plane(LON, LAT)).astype(">i2").tobytes())
    return f


def w_kml(d, kmz=False):
    rng = np.random.default_rng(5)
    lon, lat = 51.2 + rng.uniform(0, 0.05, 300), 35.3 + rng.uniform(0, 0.05, 300)
    pm = "".join(f"<Placemark><Point><altitudeMode>absolute</altitudeMode><coordinates>{a},{b},{geo_plane(a, b)}</coordinates></Point></Placemark>"
                 for a, b in zip(lon, lat))
    doc = f'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>{pm}</Document></kml>'
    if kmz:
        f = d / "t.kmz"
        with zipfile.ZipFile(f, "w") as z:
            z.writestr("doc.kml", doc)
        return f
    f = d / "t.kml"
    f.write_text(doc)
    return f


PROJECTED = {
    "asc": w_asc, "dsaa": w_dsaa, "dsbb": w_dsbb, "dsrb": w_dsrb, "bil": lambda d: w_bil(d, "bil"), "bip": lambda d: w_bil(d, "bip"),
    "bsq": lambda d: w_bil(d, "bsq"), "flt": w_flt, "tif": lambda d: w_tif(d), "tif_lzw_tiled": lambda d: w_tif(d, compression=5, tile=16),
    "tif_deflate_pred3": lambda d: w_tif(d, compression=8, predictor=3, rows_per_strip=7), "tif_packbits": lambda d: w_tif(d, compression=32773),
    "xyz_grid": w_xyz_grid, "csv_points": w_points_csv, "dxf_points": lambda d: w_dxf(d, "points"), "dxf_3dface": lambda d: w_dxf(d, "3dface"),
    "dxf_polyface": lambda d: w_dxf(d, "polyface"), "dxf_lwpolyline": lambda d: w_dxf(d, "lwpoly"), "dxf_polyline3d": lambda d: w_dxf(d, "poly3d"),
    "surpac": w_surpac, "obj": w_obj, "stl_ascii": lambda d: w_stl(d, False), "ply_ascii": lambda d: w_ply(d, False),
    "ply_binary": lambda d: w_ply(d, True), "shp_pointz": lambda d: w_shp(d, "pointz"), "shp_polylinez": lambda d: w_shp(d, "polylinez"),
}


@pytest.mark.parametrize("name", list(PROJECTED))
def test_planar_surface_every_format(name, tmp_path):
    f = PROJECTED[name](tmp_path)
    s = read_surface(str(f))
    z = s.sample(QX, QY)
    assert np.all(np.isfinite(z)), (name, z)
    assert np.max(np.abs(z - plane(QX, QY))) < 1e-6, (name, z - plane(QX, QY))
    assert s.info["format"] and s.extent is not None


def test_binary_stl_float32(tmp_path):
    s = read_surface(str(w_stl(tmp_path, True)))
    z = s.sample(QX - X0, QY - Y0)
    assert np.max(np.abs(z - plane(QX, QY))) < 1e-3          # float32 storage


def test_geographic_surfaces_bridge_to_utm(tmp_path):
    E, N, _, _ = wgs84_to_utm(np.array([35.31, 35.33]), np.array([51.21, 51.24]), zone=39, south=False)
    params = load_params(None)
    params["crs"] = {"utm_zone": 39, "hemisphere": "N"}
    from geovalid_pro.io.topo import align
    for f, tol in ((w_hgt(tmp_path), 0.6), (w_kml(tmp_path), 1e-6), (w_kml(tmp_path, kmz=True), 1e-6)):
        s, notes = align(read_surface(str(f)), params, E, N)
        lat, lon = utm_to_wgs84(E, N, 39, False)
        z = s.sample(E, N)
        assert np.max(np.abs(z - geo_plane(lon, lat))) < tol, (f.name, z, geo_plane(lon, lat))
        assert any("UTM zone 39N (declared)" in n for n in notes)
    hgt = read_surface(str(w_hgt(tmp_path)))
    assert any("EGM96" in n for n in hgt.info["notes"])


def test_point_cloud_refuses_far_points(tmp_path):
    s = read_surface(str(w_points_csv(tmp_path)))
    z = s.sample(np.array([X0 + 500, X0 + 5000]), np.array([Y0 + 400, Y0 + 400]))
    assert np.isfinite(z[0]) and np.isnan(z[1])
    assert s.support(np.array([X0 + 5000]), np.array([Y0 + 400]))[0] > s.max_dist


def test_unsupported_formats_say_so(tmp_path):
    (tmp_path / "pit.00t").write_bytes(b"\x00" * 64)
    with pytest.raises(ValueError, match="no public specification"):
        read_surface(str(tmp_path / "pit.00t"))
    f = tmp_path / "j.tif"
    write_tiff(str(f), np.zeros((4, 4), np.float32), affine_ul=(0, 0, 1, 1))
    b = bytearray(f.read_bytes())
    i = b.find(struct.pack("<HHI", 259, 3, 1))
    b[i + 8:i + 10] = struct.pack("<H", 7)
    f.write_bytes(bytes(b))
    with pytest.raises(ValueError, match="JPEG is not supported"):
        read_surface(str(f))


def test_utm_round_trip_millimetre():
    rng = np.random.default_rng(11)
    lat, lon = rng.uniform(-79.9, 83.9, 5000), rng.uniform(-180, 180, 5000)
    E, N, z, s = wgs84_to_utm(lat, lon)
    la, lo = utm_to_wgs84(E, N, z, s)
    E2, N2, _, _ = wgs84_to_utm(la, lo, zone=z, south=s)
    assert np.max(np.hypot(E2 - E, N2 - N)) < 1e-3
    e, n, zz, ss = wgs84_to_utm(0.0, 6.0, zone=31)          # zone edge on the equator: 833 978.557 m
    assert abs(e[0] - 833978.557) < 0.001 and abs(n[0]) < 1e-6
    d = describe_wkt('PROJCS["WGS 84 / UTM zone 39N",GEOGCS["WGS 84",DATUM["WGS_1984"]],PROJECTION["Transverse_Mercator"],AUTHORITY["EPSG","32639"]]')
    assert d["zone"] == 39 and d["south"] is False and d["datum"] == "WGS84"


# ---- licence boundaries -------------------------------------------------------------------------------------------
OUTER = np.array([[0, 0], [1000, 0], [1000, 1000], [0, 1000]], float) + [X0, Y0]
HOLE = np.array([[400, 400], [600, 400], [600, 600], [400, 600]], float) + [X0, Y0]
PART2 = np.array([[2000, 0], [2500, 0], [2500, 500], [2000, 500]], float) + [X0, Y0]
BX = X0 + np.array([100, 500, 2200, 1500, 999])
BY = Y0 + np.array([100, 500, 200, 500, 500])
EXPECT = np.array([True, False, True, False, True])       # in, in hole, second part, outside, inside near edge


def _rings_geojson(f):
    import json
    f.write_text(json.dumps({"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::32639"}},
                             "features": [{"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": [
                                 [OUTER.tolist() + [OUTER[0].tolist()], HOLE.tolist() + [HOLE[0].tolist()]], [PART2.tolist() + [PART2[0].tolist()]]]}}]}))


def _rings_shp(f):
    rings = [OUTER[::-1], HOLE, PART2[::-1]]
    rings = [np.vstack([r, r[:1]]) for r in rings]
    pts = np.vstack(rings)
    parts = np.cumsum([0] + [len(r) for r in rings[:-1]])
    s = struct.pack("<i4d2i", 5, pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max(), len(rings), len(pts))
    s += struct.pack(f"<{len(rings)}i", *parts) + pts.astype("<f8").tobytes()
    _shp(f, [s], 5)
    f.with_suffix(".prj").write_text('PROJCS["WGS_1984_UTM_Zone_39N",GEOGCS["GCS_WGS_1984"]]')


def _rings_dxf(f):
    L = ["0", "SECTION", "2", "ENTITIES"]
    for r in (OUTER, HOLE, PART2):
        L += ["0", "LWPOLYLINE", "8", "LIC", "90", str(len(r)), "70", "1"]
        for x, y in r:
            L += ["10", f"{x}", "20", f"{y}"]
    f.write_text("\n".join(L + ["0", "ENDSEC", "0", "EOF"]) + "\n")


def _rings_csv(f):
    rows = [(k, x, y) for k, r in enumerate((OUTER, HOLE, PART2)) for x, y in r]
    pd.DataFrame(rows, columns=["Ring", "Easting", "Northing"]).to_csv(f, index=False)


def _rings_kml(f):
    def ll(r):
        lat, lon = utm_to_wgs84(r[:, 0], r[:, 1], 39, False)
        return " ".join(f"{a},{b},0" for a, b in zip(lon, lat)) + f" {lon[0]},{lat[0]},0"
    poly = lambda o, h=None: (f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{ll(o)}</coordinates></LinearRing></outerBoundaryIs>"
                              + (f"<innerBoundaryIs><LinearRing><coordinates>{ll(h)}</coordinates></LinearRing></innerBoundaryIs>" if h is not None else "") + "</Polygon>")
    f.write_text(f'<kml xmlns="http://www.opengis.net/kml/2.2"><Placemark><MultiGeometry>{poly(OUTER, HOLE)}{poly(PART2)}</MultiGeometry></Placemark></kml>')


@pytest.mark.parametrize("ext,writer", [("geojson", _rings_geojson), ("shp", _rings_shp), ("dxf", _rings_dxf), ("csv", _rings_csv), ("kml", _rings_kml)])
def test_boundary_formats_multipart_and_holes(ext, writer, tmp_path):
    from geovalid_pro.io.boundary import align_boundary
    f = tmp_path / f"lic.{ext}"
    writer(f)
    b = read_boundary(str(f))
    params = load_params(None)
    params["crs"] = {"utm_zone": 39, "hemisphere": "N"}
    b, _ = align_boundary(b, params, BX, BY)
    assert (b.contains(BX, BY) == EXPECT).all(), (ext, b.contains(BX, BY))
    assert abs(b.distance(BX[-1:], BY[-1:])[0] - 1.0) < 0.01


# ---- rules on a small project -------------------------------------------------------------------------------------
def _collars(d, z_shift=0.0, xy_swap=False, feet=False, n=30):
    rng = np.random.default_rng(2)
    x, y = X0 + rng.uniform(50, 950, n), Y0 + rng.uniform(50, 700, n)
    z = plane(x, y) + z_shift + rng.normal(0, 0.3, n)
    if feet:
        z = z * 3.28084
    if xy_swap:
        x, y = y, x
    df = pd.DataFrame({"HoleID": [f"T{i:03d}" for i in range(n)], "East": x, "North": y, "RL": z, "Depth": 100.0,
                       "HoleType": ["UG" if i < 2 else "DD" for i in range(n)]})
    df.loc[5, "RL"] += 8.0                                   # one collar 8 m above the ground
    df.to_csv(d / "collar.csv", index=False)
    pd.DataFrame({"HoleID": df["HoleID"], "Depth": 0.0, "Azimuth": 0.0, "Dip": -90.0}).to_csv(d / "survey.csv", index=False)


def _run(d, topo, **params_kw):
    params = load_params(None)
    params.update(params_kw)
    ins = [i for i in load_inputs([str(d / "collar.csv"), str(d / "survey.csv")]) if i.kind != "ignore"]
    return run(ProjectSpec(ins, dem_path=str(topo), project_name="topo", params=params))


def _iss(res, rule):
    return res.issues[res.issues["rule_id"] == rule]


def test_dz_rule_with_exemption(tmp_path):
    _collars(tmp_path)
    res = _run(tmp_path, w_tif(tmp_path), topo_exempt={"field": "HoleType", "values": ["UG"]})
    c11 = _iss(res, "COL-011")
    assert set(c11.loc[c11["severity"] == "ERROR", "hole_id"]) == {"T005"}
    assert c11["message_en"].str.contains("2 collars exempt").any()
    assert _iss(res, "COL-025").query("severity != 'INFO'").empty and _iss(res, "COL-012").empty


def test_vertical_datum_offset(tmp_path):
    _collars(tmp_path, z_shift=4.0)
    res = _run(tmp_path, w_asc(tmp_path))
    c12 = _iss(res, "COL-012")
    assert len(c12) == 1 and c12["severity"].iloc[0] == "ERROR" and c12["rule_alias"].iloc[0] == "COL-06b"


@pytest.mark.parametrize("case,expect", [("swap", "swapped"), ("feet", "feet"), ("false_easting", "false easting")])
def test_sanity_blocks_gross_errors(case, expect, tmp_path):
    _collars(tmp_path, xy_swap=case == "swap", feet=case == "feet")
    if case == "false_easting":
        c = pd.read_csv(tmp_path / "collar.csv")
        c["East"] -= 500000
        c.to_csv(tmp_path / "collar.csv", index=False)
    res = _run(tmp_path, w_asc(tmp_path))
    c25 = _iss(res, "COL-025")
    err = c25[c25["severity"] == "ERROR"]
    assert len(err) == 1 and expect in err["message_en"].iloc[0], c25["message_en"].tolist()
    assert _iss(res, "COL-011").empty and _iss(res, "COL-012").empty


def test_collars_outside_topography_not_checked(tmp_path):
    _collars(tmp_path)
    c = pd.read_csv(tmp_path / "collar.csv")
    c.loc[[7, 8], "East"] += 3000
    c.to_csv(tmp_path / "collar.csv", index=False)
    res = _run(tmp_path, w_asc(tmp_path))
    w = _iss(res, "COL-025").query("severity == 'WARNING'")
    assert len(w) == 1 and "2 collars lie outside" in w["message_en"].iloc[0] and "T007" in w["message_en"].iloc[0]


def test_dated_topographies(tmp_path):
    _collars(tmp_path)
    c = pd.read_csv(tmp_path / "collar.csv")
    c["StartDate"] = ["2020-05-01"] * 15 + ["2024-05-01"] * 15
    c.to_csv(tmp_path / "collar.csv", index=False)
    xs, ys, z = lattice()
    now = tmp_path / "now.asc"                               # the pit lowered the ground 10 m after 2022
    with open(now, "w") as o:
        o.write(f"ncols {NX}\nnrows {NY}\nxllcorner {X0 - DX / 2}\nyllcorner {Y0 - DX / 2}\ncellsize {DX}\nNODATA_value -9999\n")
        np.savetxt(o, z[::-1] - 10, fmt="%.6f")
    pre = w_asc(tmp_path)
    res = _run(tmp_path, pre, topographies=[{"path": str(now), "date": "2022-01-01", "label": "current"}])
    src = res.ctx.stats["z_topo_source"]
    assert (src.iloc[:15] == "primary").all() and (src.iloc[15:] == "current").all()
    bad = set(_iss(res, "COL-011").query("severity != 'INFO'")["hole_id"])
    assert set(c["HoleID"].iloc[15:]) <= bad and not (set(c["HoleID"].iloc[:15]) - {"T005"}) & bad
