"""Desurvey engine (02 §4.22): minimum curvature (default), balanced tangential, tangential.

Dip is negative downward; inclination from vertical I = 90° + dip.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _unit(az_deg: np.ndarray, dip_deg: np.ndarray) -> np.ndarray:
    inc = np.radians(90.0 + dip_deg)
    az = np.radians(az_deg)
    return np.column_stack([np.sin(inc) * np.sin(az), np.sin(inc) * np.cos(az), -np.cos(inc)])  # E, N, Z(up)


def dogleg_deg(az1, dip1, az2, dip2) -> np.ndarray:
    t1, t2 = _unit(np.atleast_1d(az1), np.atleast_1d(dip1)), _unit(np.atleast_1d(az2), np.atleast_1d(dip2))
    return np.degrees(np.arccos(np.clip((t1 * t2).sum(axis=1), -1.0, 1.0)))


def stations_for_hole(depth, az, dip, eoh, collar_az=None, collar_dip=None) -> pd.DataFrame:
    """Accepted stations plus a collar station (depth 0) and an EOH station."""
    d = np.asarray(depth, float)
    a = np.asarray(az, float)
    p = np.asarray(dip, float)
    ok = np.isfinite(d) & np.isfinite(p)
    d, a, p = d[ok], a[ok], p[ok]
    a = np.where(np.isfinite(a), a, np.nan)
    if len(d) == 0:
        ca = collar_az if collar_az is not None and np.isfinite(collar_az) else 0.0
        cd = collar_dip if collar_dip is not None and np.isfinite(collar_dip) else -90.0
        d, a, p = np.array([0.0]), np.array([ca]), np.array([cd])
    order = np.argsort(d, kind="stable")
    d, a, p = d[order], a[order], p[order]
    a = pd.Series(a).ffill().bfill().fillna(0.0).to_numpy() % 360.0
    if d[0] > 0:
        ca = collar_az if collar_az is not None and np.isfinite(collar_az) else a[0]
        cd = collar_dip if collar_dip is not None and np.isfinite(collar_dip) else p[0]
        d, a, p = np.r_[0.0, d], np.r_[ca, a], np.r_[cd, p]
    if eoh is not None and np.isfinite(eoh) and eoh > d[-1]:
        d, a, p = np.r_[d, eoh], np.r_[a, a[-1]], np.r_[p, p[-1]]
    _, idx = np.unique(d, return_index=True)
    return pd.DataFrame({"depth_m": d[idx], "azimuth": a[idx], "dip": p[idx]})


def desurvey(st: pd.DataFrame, x0: float, y0: float, z0: float, method: str = "MIN_CURV") -> pd.DataFrame:
    d = st["depth_m"].to_numpy(float)
    t = _unit(st["azimuth"].to_numpy(float), st["dip"].to_numpy(float))
    pos = np.zeros((len(d), 3))
    pos[0] = (x0, y0, z0)
    if len(d) > 1:
        dmd = np.diff(d)
        t1, t2 = t[:-1], t[1:]
        if method == "TAN":
            step = t2 * dmd[:, None]
        else:
            beta = np.arccos(np.clip((t1 * t2).sum(axis=1), -1.0, 1.0))
            rf = np.ones_like(beta)
            if method == "MIN_CURV":
                nz = beta > 1e-9
                rf[nz] = 2.0 / beta[nz] * np.tan(beta[nz] / 2.0)
            step = (t1 + t2) * (dmd / 2.0 * rf)[:, None]
        pos[1:] = pos[0] + np.cumsum(step, axis=0)
    out = st.copy()
    out["x"], out["y"], out["z"] = pos[:, 0], pos[:, 1], pos[:, 2]
    dl = np.r_[np.nan, dogleg_deg(st["azimuth"].to_numpy()[:-1], st["dip"].to_numpy()[:-1],
                                  st["azimuth"].to_numpy()[1:], st["dip"].to_numpy()[1:])] if len(d) > 1 else np.array([np.nan])
    out["dogleg_deg"] = dl
    return out


def position_at(trace: pd.DataFrame, depths) -> np.ndarray:
    d = np.asarray(depths, float)
    td = trace["depth_m"].to_numpy(float)
    return np.column_stack([np.interp(d, td, trace[c].to_numpy(float)) for c in ("x", "y", "z")])


def resample(trace: pd.DataFrame, step: float = 1.0) -> np.ndarray:
    end = float(trace["depth_m"].iloc[-1])
    if end <= 0:
        return position_at(trace, [0.0])
    return position_at(trace, np.arange(0.0, end + 1e-9, step))
