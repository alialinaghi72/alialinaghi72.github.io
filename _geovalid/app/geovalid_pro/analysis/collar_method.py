"""Collar survey-method inference (brief §3.2; 01 §6.10), v0.1 weights of evidence.

Every contribution is recorded as evidence text, so the class can be reviewed and overridden.
Classes: SURVEYED (RTK / DGPS / total station), HANDHELD_GPS, PLANNED, DIGITISED, UNKNOWN.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

CLASSES = ["SURVEYED", "HANDHELD_GPS", "PLANNED", "DIGITISED"]
DECLARED = {"rtk": "SURVEYED", "dgps": "SURVEYED", "gps-rtk": "SURVEYED", "total station": "SURVEYED", "ts": "SURVEYED",
            "surveyed": "SURVEYED", "survey": "SURVEYED", "دوربین": "SURVEYED", "توتال": "SURVEYED",
            "gps": "HANDHELD_GPS", "handheld": "HANDHELD_GPS", "hgps": "HANDHELD_GPS", "gpsدستی": "HANDHELD_GPS",
            "planned": "PLANNED", "design": "PLANNED", "plan": "PLANNED", "طراحی": "PLANNED",
            "map": "DIGITISED", "digitised": "DIGITISED", "digitized": "DIGITISED", "نقشه": "DIGITISED"}
DESIGN_DIPS = {-90, -85, -80, -75, -70, -65, -60, -55, -50, -45}


def _terminal_digit_flag(vals: pd.Series) -> bool:
    """χ² test of the last integer digit against uniform: excess of 0 and 5 suggests rounding."""
    v = vals.dropna()
    if len(v) < 20:
        return False
    digits = (np.floor(np.abs(v.to_numpy())) % 10).astype(int)
    obs = np.bincount(digits, minlength=10)
    exp = len(digits) / 10.0
    chi2 = ((obs - exp) ** 2 / exp).sum()
    return chi2 > 27.88 and (obs[0] + obs[5]) > 2 * 2 * exp     # p < 0.001 (9 dof) and 0/5 excess


def infer(collar: pd.DataFrame, dz: pd.Series | None, steps=(100, 50, 25)) -> pd.DataFrame:
    rows = []
    camp = collar["campaign"] if "campaign" in collar and collar["campaign"].notna().any() else pd.Series("ALL", index=collar.index)
    camp = camp.fillna("—")
    camp_round = {}
    camp_dz_sd = {}
    for k, idx in camp.groupby(camp).groups.items():
        sub = collar.loc[idx]
        camp_round[k] = _terminal_digit_flag(sub["x"]) and _terminal_digit_flag(sub["y"])
        if dz is not None:
            d = dz.loc[idx].dropna()
            if len(d) >= 5:
                camp_dz_sd[k] = 1.4826 * float(np.median(np.abs(d - d.median())))
    for i, r in collar.iterrows():
        sc = dict.fromkeys(CLASSES, 0.0)
        ev = []
        # the most precise coordinate sets the precision: stripped trailing zeros can only lower it
        dec = np.nanmax([float(r.get(k, np.nan)) for k in ("x_dec", "y_dec", "z_dec")])
        if np.isfinite(dec):
            if dec >= 2:
                sc["SURVEYED"] += 2.5
                ev.append(f"coordinates to {int(dec)} decimals (+2.5 surveyed)")
            elif dec == 1:
                sc["SURVEYED"] += 0.5
                sc["HANDHELD_GPS"] += 0.5
                ev.append("coordinates to 1 decimal (+0.5 surveyed, +0.5 handheld)")
            else:
                sc["HANDHELD_GPS"] += 2.0
                ev.append("whole-metre coordinates (+2 handheld)")
        x, y = r.get("x", np.nan), r.get("y", np.nan)
        on_grid = False
        if np.isfinite(x) and np.isfinite(y):
            for s in steps:
                if x % s == 0 and y % s == 0:
                    w = 3.0 if s >= 50 else 1.5
                    sc["PLANNED"] += w
                    ev.append(f"X and Y exact multiples of {s} m (+{w:g} planned)")
                    on_grid = True
                    break
            if dec == 0 and x % 5 == 0 and y % 5 == 0 and not (x % 25 == 0 and y % 25 == 0):
                sc["DIGITISED"] += 1.0
                ev.append("X and Y rounded to 5 m (+1 digitised)")
        az, dip, eoh = r.get("azimuth", np.nan), r.get("dip", np.nan), r.get("eoh_m", np.nan)
        # collar az/dip are usually design values, so they count only together with grid-snapped coordinates
        if on_grid and np.isfinite(dip) and dip in DESIGN_DIPS and (not np.isfinite(az) or az % 45 == 0):
            sc["PLANNED"] += 1.0
            ev.append("design-like orientation on a grid node (+1 planned)")
        if on_grid and np.isfinite(eoh) and eoh > 0 and eoh % 10 == 0:
            sc["PLANNED"] += 0.5
            ev.append("EOH a multiple of 10 m (+0.5 planned)")
        k = camp.loc[i]
        if camp_round.get(k):
            sc["HANDHELD_GPS"] += 1.0
            ev.append(f"campaign {k}: last digits rounded to 0/5 (χ², +1 handheld)")
        if dz is not None and np.isfinite(dz.get(i, np.nan)):
            d = dz.loc[i]
            if abs(d) < 0.05:
                sc["DIGITISED"] += 2.5
                ev.append(f"ΔZ = {d:+.2f} m: Z taken from the DEM (+2.5 digitised/derived)")
            sd = camp_dz_sd.get(k)
            if sd is not None:
                if sd < 1.0:
                    sc["SURVEYED"] += 1.5
                    ev.append(f"campaign ΔZ robust SD {sd:.2f} m (+1.5 surveyed)")
                elif sd > 5.0:
                    sc["HANDHELD_GPS"] += 2.0
                    ev.append(f"campaign ΔZ robust SD {sd:.1f} m (+2 handheld)")
        best = max(sc, key=sc.get)
        if sc[best] < 2.0:
            cls, conf = "UNKNOWN", 0.0
        else:
            ex = {c: math.exp(v) for c, v in sc.items()}
            cls, conf = best, 100.0 * ex[best] / sum(ex.values())
        declared = None
        raw_dm = r.get("collar_survey_method")
        dm = "" if raw_dm is None or pd.isna(raw_dm) else str(raw_dm).strip().lower()
        if dm:
            declared = next((v for kk, v in DECLARED.items() if kk in dm.replace(" ", "")), None)
        rows.append({"hole_id": r["hole_id"], "inferred_method": cls, "confidence_pct": round(conf, 1),
                     "declared_method": declared, "agrees": None if declared is None else declared == cls,
                     "evidence": "; ".join(ev), "campaign": k})
    return pd.DataFrame(rows, index=collar.index)
