"""WGS84 geographic ↔ UTM (any zone, both hemispheres), Krüger series to sixth order in n (Karney 2011, "Transverse
Mercator with an accuracy of a few nanometres"): sub-millimetre inside a zone and well beyond its edges.

Only WGS84 is supported. A declared datum other than WGS84 is reported by the callers; no datum shift is applied.
"""
from __future__ import annotations

import math
import re

import numpy as np

A_WGS84 = 6378137.0
F_WGS84 = 1 / 298.257223563
K0 = 0.9996
E0 = 500000.0
N0_SOUTH = 10000000.0

_n = F_WGS84 / (2 - F_WGS84)
_e = math.sqrt(F_WGS84 * (2 - F_WGS84))
_A = A_WGS84 / (1 + _n) * (1 + _n ** 2 / 4 + _n ** 4 / 64 + _n ** 6 / 256)
n = _n
_ALPHA = [
    n / 2 - 2 * n ** 2 / 3 + 5 * n ** 3 / 16 + 41 * n ** 4 / 180 - 127 * n ** 5 / 288 + 7891 * n ** 6 / 37800,
    13 * n ** 2 / 48 - 3 * n ** 3 / 5 + 557 * n ** 4 / 1440 + 281 * n ** 5 / 630 - 1983433 * n ** 6 / 1935360,
    61 * n ** 3 / 240 - 103 * n ** 4 / 140 + 15061 * n ** 5 / 26880 + 167603 * n ** 6 / 181440,
    49561 * n ** 4 / 161280 - 179 * n ** 5 / 168 + 6601661 * n ** 6 / 7257600,
    34729 * n ** 5 / 80640 - 3418889 * n ** 6 / 1995840,
    212378941 * n ** 6 / 319334400,
]
_BETA = [
    n / 2 - 2 * n ** 2 / 3 + 37 * n ** 3 / 96 - n ** 4 / 360 - 81 * n ** 5 / 512 + 96199 * n ** 6 / 604800,
    n ** 2 / 48 + n ** 3 / 15 - 437 * n ** 4 / 1440 + 46 * n ** 5 / 105 - 1118711 * n ** 6 / 3870720,
    17 * n ** 3 / 480 - 37 * n ** 4 / 840 - 209 * n ** 5 / 4480 + 5569 * n ** 6 / 90720,
    4397 * n ** 4 / 161280 - 11 * n ** 5 / 504 - 830251 * n ** 6 / 7257600,
    4583 * n ** 5 / 161280 - 108847 * n ** 6 / 3991680,
    20648693 * n ** 6 / 638668800,
]
del n


def utm_zone(lon, lat=None) -> np.ndarray:
    """Standard UTM zone of a longitude, with the Norway (32V) and Svalbard (31X–37X) exceptions when lat is given."""
    lon = np.asarray(lon, float)
    z = np.floor((((lon + 180) % 360) - 180 + 180) / 6).astype(int) + 1
    z = np.clip(z, 1, 60)
    if lat is not None:
        lat = np.asarray(lat, float)
        z = np.where((lat >= 56) & (lat < 64) & (lon >= 3) & (lon < 12), 32, z)
        for lo, hi, zz in ((0, 9, 31), (9, 21, 33), (21, 33, 35), (33, 42, 37)):
            z = np.where((lat >= 72) & (lat < 84) & (lon >= lo) & (lon < hi), zz, z)
    return z


def central_meridian(zone) -> np.ndarray:
    return (np.asarray(zone, float) - 1) * 6 - 180 + 3


def _tau_prime(tau):
    sig = np.sinh(_e * np.arctanh(_e * tau / np.sqrt(1 + tau * tau)))
    return tau * np.sqrt(1 + sig * sig) - sig * np.sqrt(1 + tau * tau)


def wgs84_to_utm(lat, lon, zone=None, south=None):
    """(lat, lon) in degrees → (easting, northing, zone, south). `zone` / `south` force a zone or hemisphere
    (scalars or arrays); otherwise they follow from each point."""
    lat = np.atleast_1d(np.asarray(lat, float))
    lon = np.atleast_1d(np.asarray(lon, float))
    z = utm_zone(lon, lat) if zone is None else np.broadcast_to(np.asarray(zone, int), lat.shape)
    s = (lat < 0) if south is None else np.broadcast_to(np.asarray(south, bool), lat.shape)
    lam = np.radians(((lon - central_meridian(z) + 180) % 360) - 180)
    phi = np.radians(lat)
    tau = np.tan(phi)
    taup = _tau_prime(tau)
    xip = np.arctan2(taup, np.cos(lam))
    etap = np.arcsinh(np.sin(lam) / np.sqrt(taup * taup + np.cos(lam) ** 2))
    xi, eta = xip.copy(), etap.copy()
    for j, a in enumerate(_ALPHA, start=1):
        xi += a * np.sin(2 * j * xip) * np.cosh(2 * j * etap)
        eta += a * np.cos(2 * j * xip) * np.sinh(2 * j * etap)
    E = E0 + K0 * _A * eta
    N = K0 * _A * xi + np.where(s, N0_SOUTH, 0.0)
    return E, N, np.asarray(z), np.asarray(s)


def utm_to_wgs84(E, N, zone, south=False):
    """(easting, northing) in a UTM zone → (lat, lon) in degrees."""
    E = np.atleast_1d(np.asarray(E, float))
    N = np.atleast_1d(np.asarray(N, float))
    s = np.broadcast_to(np.asarray(south, bool), E.shape)
    xi = (N - np.where(s, N0_SOUTH, 0.0)) / (K0 * _A)
    eta = (E - E0) / (K0 * _A)
    xip, etap = xi.copy(), eta.copy()
    for j, b in enumerate(_BETA, start=1):
        xip -= b * np.sin(2 * j * xi) * np.cosh(2 * j * eta)
        etap -= b * np.cos(2 * j * xi) * np.sinh(2 * j * eta)
    taup = np.sin(xip) / np.sqrt(np.sinh(etap) ** 2 + np.cos(xip) ** 2)
    lam = np.arctan2(np.sinh(etap), np.cos(xip))
    tau = taup.copy()
    e2m = 1 - _e * _e
    for _ in range(8):                                  # Newton on τ' (τ) = τ'; converges in 2–3 steps
        tp = _tau_prime(tau)
        dtau = (taup - tp) / np.sqrt(1 + tp * tp) * (1 + e2m * tau * tau) / (e2m * np.sqrt(1 + tau * tau))
        tau = tau + dtau
        if np.nanmax(np.abs(dtau)) < 1e-14:
            break
    lat = np.degrees(np.arctan(tau))
    lon = np.degrees(lam) + central_meridian(zone)
    lon = ((lon + 180) % 360) - 180
    return lat, lon


# ---- CRS descriptions ---------------------------------------------------------------------------------------------
def epsg_utm(epsg) -> tuple[int, bool] | None:
    """(zone, south) for WGS 84 / UTM EPSG codes 326zz and 327zz."""
    try:
        e = int(epsg)
    except (TypeError, ValueError):
        return None
    if 32601 <= e <= 32660:
        return e - 32600, False
    if 32701 <= e <= 32760:
        return e - 32700, True
    return None


def describe_epsg(epsg) -> dict:
    """What GEOVALID knows about an EPSG code: geographic WGS 84, WGS 84 / UTM, or another datum (no shift applied)."""
    try:
        e = int(epsg)
    except (TypeError, ValueError):
        return {"epsg": None, "kind": "unknown"}
    if e == 4326:
        return {"epsg": e, "kind": "geographic", "datum": "WGS84"}
    u = epsg_utm(e)
    if u:
        return {"epsg": e, "kind": "utm", "zone": u[0], "south": u[1], "datum": "WGS84"}
    if 23028 <= e <= 23038:
        return {"epsg": e, "kind": "utm", "zone": e - 23000, "south": False, "datum": "ED50"}
    if e in (4230, 4258, 4269, 4267, 4283):
        return {"epsg": e, "kind": "geographic", "datum": {4230: "ED50", 4258: "ETRS89", 4269: "NAD83", 4267: "NAD27", 4283: "GDA94"}[e]}
    return {"epsg": e, "kind": "projected", "datum": "unknown"}


def describe_wkt(wkt: str) -> dict:
    """Datum, projection and UTM zone read from a .prj / WKT string (for the report; no transformation)."""
    if not wkt:
        return {}
    w = wkt.upper()
    out = {"wkt": wkt.strip()[:400]}
    m = re.search(r'AUTHORITY\["EPSG",\s*"?(\d+)"?\]\s*\]\s*$', w) or re.search(r'ID\["EPSG",\s*(\d+)\]\s*\]\s*$', w)
    if m:
        out.update(describe_epsg(int(m.group(1))))
    out["datum"] = out.get("datum") or ("WGS84" if "WGS" in w and "84" in w else "ED50" if "ED50" in w or "EUROPEAN_DATUM_1950" in w else "unknown")
    out["kind"] = "geographic" if w.startswith("GEOGCS") or w.startswith("GEOGCRS") else ("utm" if "UTM" in w or "TRANSVERSE_MERCATOR" in w else out.get("kind", "projected"))
    z = re.search(r"UTM[ _]ZONE[ _](\d{1,2})\s*([NS])?", w)
    if z:
        out["zone"] = int(z.group(1))
        out["south"] = (z.group(2) == "S") if z.group(2) else bool(re.search(r"FALSE_NORTHING\"?,\s*10000000", w))
    if "FOOT" in w or "FEET" in w:
        out["units"] = "feet"
    return out


def looks_geographic(x, y) -> bool:
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    return bool(ok.any()) and bool((np.abs(x[ok]) <= 180).all() and (np.abs(y[ok]) <= 90).all())


def project_crs(params: dict) -> dict:
    """The project's declared horizontal CRS from the profile (`crs: {epsg, utm_zone, hemisphere}`)."""
    c = params.get("crs") or {}
    if c.get("epsg"):
        d = describe_epsg(c["epsg"])
        if d.get("kind") == "utm":
            return d
    if c.get("utm_zone"):
        return {"kind": "utm", "zone": int(c["utm_zone"]), "south": str(c.get("hemisphere") or "N").upper().startswith("S"),
                "datum": "WGS84", "epsg": None}
    return {"kind": "unknown"}
