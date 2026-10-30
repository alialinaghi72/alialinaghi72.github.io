"""Synthetic drillhole database with an error injector and ground-truth manifest (04 §3.2–3.3).

generate(folder, inject=True) writes collar/survey/assay/lithology/alteration/weathering/geotech/density CSVs, a DEM (.asc),
a licence polygon, a CRM table and manifest.csv (rule_id, table, hole_id, description).
With inject=False the clean twin is produced: deterministic rules must raise no ERROR/CRITICAL on it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

X0, Y0 = 512000.0, 3285000.0     # UTM zone 40N, central Iran
CRMS = {"GV-CRM1": {"Cu": (0.55, 0.02), "Au": (0.80, 0.04)}, "GV-CRM2": {"Cu": (1.20, 0.04), "Au": (2.10, 0.08)}}
LITHS = ["AND", "DIO", "QMP", "BXH", "TUF"]
COLOURS = ["grey", "green", "pink", "dark grey", "buff", "red-brown"]
# Porphyry model: grade multipliers by host unit, alteration zone and weathering profile (Sillitoe 2010 style zoning)
LITH_F = {"QMP": 2.2, "BXH": 2.6, "DIO": 1.0, "AND": 0.55, "TUF": 0.35, "ALLUV": 0.05}
ALT_F = {"POTASSIC": 1.6, "PHYLLIC": 1.2, "ARGILLIC": 0.6, "PROPYLITIC": 0.4}
WTH_F = {"OXIDE": 0.5, "MIXED": 1.3, "PRIMARY": 1.0}
SG_LITH = {"QMP": 2.62, "BXH": 2.68, "DIO": 2.78, "AND": 2.72, "TUF": 2.45, "ALLUV": 2.0}
CENTRE = (250.0, 250.0)       # stock centre, metres from the grid origin
SAMPLE_TABLES = ("collar", "survey", "assay", "lithology", "alteration", "weathering", "geotech", "density")


def dem_z(x, y):
    return 1500 + 80 * np.sin((x - X0) / 400) + 60 * np.cos((y - Y0) / 300) + 0.02 * (x - X0)


def _pos(hx, hy, depth):
    """Horizontal offset and vertical depth of a point `depth` m down a −60°/045° hole."""
    h = 0.5 * depth / np.sqrt(2)
    return hx + h, hy + h, 0.866 * depth


def _at(intervals, depth):
    for fr, to, *v in intervals:
        if fr <= depth < to:
            return v
    return intervals[-1][2:]


def _pick(rng, probs: dict, prev):
    keys = [k for k in probs if k != prev]
    w = np.array([probs[k] for k in keys], float)
    return keys[int(rng.choice(len(keys), p=w / w.sum()))]


def generate(folder: str, inject: bool = True, seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    manifest = []

    # ---------------- collars ----------------
    rows = []
    k = 0
    for j in range(8):
        for i in range(8):
            k += 1
            h = f"GV-{k:03d}"
            gx, gy = X0 + 100 + i * 50, Y0 + 100 + j * 50
            camp = "A-2019-RTK" if k <= 24 else ("B-2021-GPS" if k <= 44 else "C-2023-DGPS")
            if camp.startswith("A"):
                x, y = round(gx + rng.normal(0, 1.5), 3), round(gy + rng.normal(0, 1.5), 3)
                z = round(float(dem_z(x, y) + rng.normal(0, 0.1)), 3)
            elif camp.startswith("B"):
                x, y = float(round(gx + rng.normal(0, 3))), float(round(gy + rng.normal(0, 3)))
                z = float(round(dem_z(x, y) + rng.normal(0, 4)))
            else:
                x, y = round(gx + rng.normal(0, 1.5), 2), round(gy + rng.normal(0, 1.5), 2)
                z = round(float(dem_z(x, y) + rng.normal(0, 0.25)), 2)
            eoh = round(float(rng.uniform(150, 300)), 1)
            start = pd.Timestamp("2019-04-01") + pd.Timedelta(days=int(k * 9 + (0 if camp[0] == "A" else 600 if camp[0] == "B" else 1300)))
            rows.append({"HoleID": h, "East": x, "North": y, "RL": z, "MaxDepth": eoh, "Azimuth": 45.0, "Dip": -60.0,
                         "Campaign": camp, "StartDate": start.date().isoformat(),
                         "EndDate": (start + pd.Timedelta(days=int(eoh // 40 + 2))).date().isoformat(), "Rig": f"RIG-{1 + k % 3}",
                         "DrillType": "DD"})
    collar = pd.DataFrame(rows)

    # ---------------- surveys ----------------
    srows = []
    for r in collar.itertuples():
        d, az, dip = 0.0, 45.0 + rng.normal(0, 0.5), -60.0 + rng.normal(0, 0.3)
        while d + 30 <= r.MaxDepth:
            d += 30
            az += rng.normal(0.5, 0.15)
            dip += rng.normal(0.3, 0.1)
            srows.append({"HoleID": r.HoleID, "Depth": d, "Azimuth": round(az, 2), "Dip": round(dip, 2), "Instrument": "Gyro"})
    survey = pd.DataFrame(srows)

    # ---------------- logging: lithology (Persian headers), alteration, weathering ----------------
    lrows, arows_alt, wrows, logs = [], [], [], {}
    for r in collar.itertuples():
        hx, hy = r.East - X0, r.North - Y0
        cover = round(float(rng.uniform(3, 8)), 1)
        lith_iv = [(0.0, cover, "ALLUV")]
        lrows.append({"شماره گمانه": r.HoleID, "از": 0.0, "تا": cover, "سنگ‌شناسی": "ALLUV", "رنگ": "buff"})
        d, prev = cover, None
        while d < r.MaxDepth:
            L = round(float(rng.uniform(5, 40)), 1)
            to = min(round(d + L, 1), r.MaxDepth)
            px, py, pz = _pos(hx, hy, (d + to) / 2)
            rad = np.hypot(px - CENTRE[0], py - CENTRE[1])
            if rad < 110 and pz > 35:
                probs = {"QMP": .55, "BXH": .25, "DIO": .15, "AND": .05, "TUF": .0}
            elif rad < 200:
                probs = {"DIO": .40, "BXH": .12, "QMP": .13, "AND": .25, "TUF": .10}
            else:
                probs = {"AND": .45, "TUF": .30, "DIO": .20, "QMP": .03, "BXH": .02}
            if pz < 40:
                probs["TUF"] += .25
                probs["AND"] += .15
            code = _pick(rng, probs, prev)
            prev = code
            lith_iv.append((d, to, code))
            lrows.append({"شماره گمانه": r.HoleID, "از": d, "تا": to, "سنگ‌شناسی": code, "رنگ": rng.choice(COLOURS)})
            d = to
        alt_iv, d = [], 0.0
        while d < r.MaxDepth:
            to = min(round(d + float(rng.uniform(6, 30)), 1), r.MaxDepth)
            px, py, pz = _pos(hx, hy, (d + to) / 2)
            d3 = np.sqrt((px - CENTRE[0]) ** 2 + (py - CENTRE[1]) ** 2 + 0.6 * (pz - 170) ** 2) + rng.normal(0, 25)
            if d3 < 115:
                alt, inten = "POTASSIC", "STRONG" if d3 < 70 else "MODERATE"
            elif d3 < 195:
                alt, inten = "PHYLLIC", "STRONG" if d3 < 150 else "MODERATE"
            elif pz < 70 and np.hypot(px - CENTRE[0], py - CENTRE[1]) < 280:
                alt, inten = "ARGILLIC", "MODERATE"
            else:
                alt, inten = "PROPYLITIC", "WEAK" if d3 > 260 else "MODERATE"
            if alt_iv and alt_iv[-1][2:] == [alt, inten]:
                alt_iv[-1][1] = to
            else:
                alt_iv.append([d, to, alt, inten])
            d = to
        for fr, to, alt, inten in alt_iv:
            arows_alt.append({"HoleID": r.HoleID, "From": round(fr, 1), "To": round(to, 1), "AltType": alt, "Intensity": inten})
        ox = round(cover + float(rng.uniform(10, 35)), 1)
        mx = round(ox + float(rng.uniform(5, 20)), 1)
        wth_iv = [(0.0, min(ox, r.MaxDepth), "OXIDE"), (min(ox, r.MaxDepth), min(mx, r.MaxDepth), "MIXED"), (min(mx, r.MaxDepth), r.MaxDepth, "PRIMARY")]
        wth_iv = [w for w in wth_iv if w[1] > w[0]]
        for fr, to, w in wth_iv:
            wrows.append({"HoleID": r.HoleID, "From": fr, "To": to, "Oxidation": w})
        logs[r.HoleID] = (lith_iv, [tuple(a) for a in alt_iv], wth_iv)
    lith = pd.DataFrame(lrows)
    alteration = pd.DataFrame(arows_alt)
    weathering = pd.DataFrame(wrows)

    # ---------------- assays with QC ----------------
    arows, n_orig, sample_no = [], 0, 100000
    qc_seq = []
    for r in collar.itertuples():
        depth = 0.0
        L = 2.0 if r.Campaign[0] == "B" else 1.0
        hx, hy = r.East - X0, r.North - Y0
        while depth + L <= r.MaxDepth:
            mid = depth + L / 2
            px, py, _ = _pos(hx, hy, mid)
            trend = np.exp(-((px - CENTRE[0]) ** 2 + (py - CENTRE[1]) ** 2) / 2 / 170 ** 2) * np.exp(-((mid - 140) / 110) ** 2)
            lith_iv, alt_iv, wth_iv = logs[r.HoleID]
            lc, (ac, _), (wc,) = _at(lith_iv, mid)[0], _at(alt_iv, mid), _at(wth_iv, mid)
            f = LITH_F[lc] * ALT_F[ac] * WTH_F[wc]
            cu = float(np.clip((0.02 + 0.55 * trend) * f * rng.lognormal(0, 0.4), 0.002, 6))
            au = float(cu * rng.lognormal(0.2, 0.5) * 0.8 * (1.5 if lc == "BXH" else 1.0))
            mo = float(15 + 260 * trend * (2.0 if ac == "POTASSIC" else 1.0) * (1.4 if lc == "QMP" else 1.0) * rng.lognormal(0, 0.6))
            s = float((cu * rng.uniform(0.6, 1.6) + rng.uniform(0.3, 1.5)) * (0.5 if wc == "OXIDE" else 1.0))
            fe = float(rng.uniform(2.5, 6.5))
            sample_no += 1
            arows.append({"HoleID": r.HoleID, "From": round(depth, 2), "To": round(depth + L, 2), "SampleID": f"S{sample_no}",
                          "SampleType": "ORIGINAL", "ParentID": "", "StdID": "", "Batch": f"B{sample_no // 200:03d}",
                          "Cu_pct": f"{cu:.4f}", "Au_ppm": (f"{au:.3f}" if au >= 0.005 else "<0.005"),
                          "Mo_ppm": (f"{mo:.1f}" if mo >= 2 else "<2"), "S_pct": f"{s:.3f}", "Fe_pct": f"{fe:.2f}"})
            n_orig += 1
            last = arows[-1]
            def qc(kind, **kw):
                nonlocal sample_no
                sample_no += 1
                row = {"HoleID": "", "From": "", "To": "", "SampleID": f"S{sample_no}", "SampleType": kind, "ParentID": "", "StdID": "",
                       "Batch": last["Batch"], "Cu_pct": "", "Au_ppm": "", "Mo_ppm": "", "S_pct": "", "Fe_pct": ""}
                row.update(kw)
                arows.append(row)
                return row
            if n_orig % 19 == 0:
                cid = "GV-CRM1" if (n_orig // 19) % 2 else "GV-CRM2"
                cu_c, cu_s = CRMS[cid]["Cu"]
                au_c, au_s = CRMS[cid]["Au"]
                z1, z2 = np.clip(rng.normal(0, 0.8, 2), -2.4, 2.4)
                qc_seq.append(qc("CRM", StdID=cid, Cu_pct=f"{cu_c + z1 * cu_s:.4f}", Au_ppm=f"{au_c + z2 * au_s:.3f}",
                                 Mo_ppm="<2", S_pct="0.020", Fe_pct="1.00"))
            if n_orig % 30 == 0:
                qc_seq.append(qc("BLANK", Cu_pct="0.0020", Au_ppm="<0.005", Mo_ppm="<2", S_pct="0.010", Fe_pct="0.30"))
            for kind, every, sd in (("FIELD_DUP", 25, 0.07), ("COARSE_DUP", 40, 0.04), ("PULP_DUP", 40, 0.015)):
                if n_orig % every == 0:
                    f = lambda v, sd=sd: v if v.startswith("<") else f"{float(v) * (1 + rng.normal(0, sd)):.4f}"
                    qc(kind, HoleID=last["HoleID"], From=last["From"], To=last["To"], ParentID=last["SampleID"],
                       Cu_pct=f(last["Cu_pct"]), Au_ppm=f(last["Au_ppm"]), Mo_ppm=f(last["Mo_ppm"]), S_pct=f(last["S_pct"]),
                       Fe_pct=f(last["Fe_pct"]))
            depth += L
    assay = pd.DataFrame(arows)

    # ---------------- geotech ----------------
    grows = []
    for r in collar.itertuples():
        d = 0.0
        while d < r.MaxDepth:
            to = min(d + 3.0, r.MaxDepth)
            run = to - d
            run = round(run, 2)
            rec = round(run * float(rng.uniform(0.86, 1.0)), 2)
            rqd = round(rec * float(rng.uniform(0.3, 0.95)), 2)
            grows.append({"HoleID": r.HoleID, "From": round(d, 2), "To": round(to, 2), "Run_m": run, "Rec_m": rec,
                          "RQD_m": rqd, "Recovery": round(100 * rec / run, 1), "RQD": round(100 * rqd / run, 1)})
            d = to
    geo = pd.DataFrame(grows)

    # ---------------- density ----------------
    drows = []
    for r in collar.itertuples():
        for dd in np.arange(10, r.MaxDepth - 0.2, 10.0):
            lith_iv, _, wth_iv = logs[r.HoleID]
            sg = SG_LITH[_at(lith_iv, dd + 0.1)[0]] - (0.25 if _at(wth_iv, dd + 0.1)[0] == "OXIDE" else 0) + rng.normal(0, 0.06)
            drows.append({"HoleID": r.HoleID, "From": round(dd, 1), "To": round(dd + 0.2, 1), "SG": round(float(sg), 3)})
    dens = pd.DataFrame(drows)

    # ---------------- error injection ----------------
    def m(rule, table, hole, desc):
        manifest.append({"rule_id": rule, "table": table, "hole_id": hole, "description": desc})

    if inject:
        i5 = collar.index[collar["HoleID"] == "GV-005"][0]
        dup = collar.loc[i5].copy()
        dup["East"] += 10
        collar = pd.concat([collar, dup.to_frame().T], ignore_index=True)
        m("COL-001", "collar", "GV-005", "duplicate HoleID with conflicting coordinates")
        collar.loc[collar["HoleID"] == "GV-007", "RL"] = ""
        m("COL-002", "collar", "GV-007", "missing Z")
        r9 = collar["HoleID"] == "GV-009"
        collar.loc[r9, ["East", "North"]] = collar.loc[r9, ["North", "East"]].to_numpy()
        m("COL-006", "collar", "GV-009", "X and Y swapped")
        t12 = collar[collar["HoleID"] == "GV-012"].iloc[0].copy()
        t12["HoleID"], t12["East"], t12["Azimuth"] = "GV-012T", t12["East"] + 0.5, 225.0
        collar = pd.concat([collar, t12.to_frame().T], ignore_index=True)
        survey = pd.concat([survey, pd.DataFrame([{"HoleID": "GV-012T", "Depth": 30.0 * q, "Azimuth": 225.0, "Dip": -70.0, "Instrument": "Gyro"}
                                                  for q in range(1, 5)])], ignore_index=True)
        m("COL-004", "collar", "GV-012", "twin collar 0.5 m away (GV-012T)")
        collar.loc[collar["HoleID"] == "GV-014", "MaxDepth"] = collar.loc[collar["HoleID"] == "GV-014", "MaxDepth"].astype(float) - 20
        m("COL-007", "collar", "GV-014", "EOH 20 m shorter than the data")
        collar.loc[collar["HoleID"] == "GV-021", "HoleID"] = "GV021"
        m("SUR-001", "survey", "GV-021", "collar ID written 'GV021': survey rows orphaned (join error)")
        m("INT-006", "assay", "GV-021", "collar ID written 'GV021': assay rows orphaned (join error)")
        c30 = collar[collar["HoleID"] == "GV-030"].iloc[0].copy()
        c30["HoleID"], c30["East"] = "GV-30", c30["East"] + 25
        collar = pd.concat([collar, c30.to_frame().T], ignore_index=True)
        m("COL-003", "collar", "GV-030", "near-duplicate HoleID 'GV-30'")
        ix = survey.index[(survey["HoleID"] == "GV-025") & (survey["Depth"] == 60)][0]
        bad = survey.loc[ix].copy()
        bad["Azimuth"] += 12
        survey = pd.concat([survey, bad.to_frame().T], ignore_index=True)
        m("SUR-002", "survey", "GV-025", "duplicate station at 60 m with different azimuth")
        survey.loc[(survey["HoleID"] == "GV-026") & (survey["Depth"] == 90), "Dip"] = -95.0
        m("SUR-003", "survey", "GV-026", "dip −95°")
        survey.loc[(survey["HoleID"] == "GV-027") & (survey["Depth"] == 60), "Azimuth"] = 365.0
        m("SUR-004", "survey", "GV-027", "azimuth 365°")
        survey.loc[(survey["HoleID"] == "GV-028") & (survey["Depth"] == 120), "Dip"] = 58.0
        m("SUR-005", "survey", "GV-028", "positive dip within a negative-dip hole")
        e29 = float(collar.loc[collar["HoleID"] == "GV-029", "MaxDepth"].iloc[0])
        survey = pd.concat([survey, pd.DataFrame([{"HoleID": "GV-029", "Depth": e29 + 15, "Azimuth": 50.0, "Dip": -58.0, "Instrument": "Gyro"}])], ignore_index=True)
        m("SUR-006", "survey", "GV-029", "station 15 m below EOH")
        ix = survey.index[(survey["HoleID"] == "GV-031") & (survey["Depth"] == 90)][0]
        survey.loc[ix, "Azimuth"] = float(survey.loc[ix, "Azimuth"]) + 40
        m("SUR-013", "survey", "GV-031", "single-station azimuth spike +40°")
        survey = pd.concat([survey, pd.DataFrame([{"HoleID": "GV-999", "Depth": 30.0, "Azimuth": 45.0, "Dip": -60.0, "Instrument": "Gyro"}])], ignore_index=True)
        m("SUR-001", "survey", "GV-999", "survey for a hole without collar")
        orig = assay["SampleType"] == "ORIGINAL"
        ia = assay.index[orig & (assay["HoleID"] == "GV-032")][10]
        assay.loc[ia, ["From", "To"]] = [assay.loc[ia, "To"], assay.loc[ia, "From"]]
        m("INT-001", "assay", "GV-032", "From > To")
        il = lith.index[lith["شماره گمانه"] == "GV-033"][2]
        lith.loc[il, "تا"] = float(lith.loc[il, "تا"]) + 3
        m("INT-002", "lithology", "GV-033", "overlap of 3 m")
        ia = assay.index[orig & (assay["HoleID"] == "GV-034")][5]
        assay = pd.concat([assay, assay.loc[[ia]]], ignore_index=True)
        m("INT-003", "assay", "GV-034", "duplicated sample row")
        il = lith.index[lith["شماره گمانه"] == "GV-035"][3]
        lith.loc[il, "از"] = float(lith.loc[il, "از"]) + 4
        m("INT-004", "lithology", "GV-035", "internal gap of 4 m")
        last = assay[orig & (assay["HoleID"] == "GV-036")].iloc[-1].copy()
        last["From"], last["To"], last["SampleID"] = float(last["To"]) + 5, float(last["To"]) + 6, "S999001"
        assay = pd.concat([assay, last.to_frame().T], ignore_index=True)
        m("INT-005", "assay", "GV-036", "sample beyond EOH")
        m("COL-007", "collar", "GV-036", "EOH shallower than the injected sample")
        o = assay[orig & (assay["HoleID"] == "GV-040")].iloc[0].copy()
        o["HoleID"], o["SampleID"] = "GV-998", "S999002"
        assay = pd.concat([assay, o.to_frame().T], ignore_index=True)
        m("INT-006", "assay", "GV-998", "assay for a hole without collar")
        orig = assay["SampleType"] == "ORIGINAL"
        assay.loc[assay.index[orig & (assay["HoleID"] == "GV-037")][7], "Cu_pct"] = "150"
        m("ASY-003", "assay", "GV-037", "Cu = 150 %")
        holes_ppb = [f"GV-{q:03d}" for q in (50, 51, 52, 53, 54, 55)]
        mask = orig & assay["HoleID"].isin(holes_ppb) & ~assay["Au_ppm"].str.startswith("<")
        assay.loc[mask, "Au_ppm"] = (assay.loc[mask, "Au_ppm"].astype(float) * 1000).round(0).astype(int).astype(str)
        m("ASY-004", "assay", None, "Au of six holes reported in ppb in the ppm column")
        assay.loc[assay.index[orig & (assay["HoleID"] == "GV-038")][9], "Cu_pct"] = ">10"
        m("ASY-005", "assay", "GV-038", "Cu over range without re-assay")
        i39 = assay.index[orig & (assay["HoleID"] == "GV-039")][50]
        assay.loc[i39, ["Cu_pct", "S_pct"]] = ["2.5000", "0.200"]
        m("ASY-006", "assay", "GV-039", "Cu 2.5 % with S 0.2 %")
        assay.loc[assay.index[orig & (assay["HoleID"] == "GV-041")][3], "Cu_pct"] = "NS"
        m("ASY-002", "assay", None, "text code NS")
        icrm = assay.index[assay["StdID"] == "GV-CRM1"][3]
        assay.loc[icrm, "Cu_pct"] = "0.7000"
        m("QAQ-002", "assay", None, "CRM GV-CRM1 Cu fails (+7.5 SD)")
        ib = assay.index[assay["SampleType"] == "BLANK"][4]
        assay.loc[ib, "Au_ppm"] = "0.200"
        m("QAQ-003", "assay", None, "blank Au = 40 × DL")
        src = assay.index[orig & (assay["HoleID"] == "GV-049")][40:46]
        dst = assay.index[orig & (assay["HoleID"] == "GV-047")][60:66]
        for c in ("Cu_pct", "Au_ppm", "Mo_ppm", "S_pct", "Fe_pct", "Batch"):
            assay.loc[dst, c] = assay.loc[src, c].to_numpy()
        m("INT-009", "assay", "GV-047", "six sample rows copied from GV-049")
        for q, il in enumerate(lith.index[(lith["سنگ‌شناسی"] == "AND")][:3]):
            lith.loc[il, "سنگ‌شناسی"] = "and" if q < 2 else "ANDE"
        m("LIT-001", "lithology", None, "code variants 'and' and 'ANDE'")
        r40 = lith[lith["شماره گمانه"] == "GV-040"].iloc[4]
        lith.loc[r40.name, "سنگ‌شناسی"] = "ALLUV"
        m("LIT-003", "lithology", "GV-040", "cover unit logged below bedrock")
        geo.loc[geo.index[geo["HoleID"] == "GV-041"][5], ["Rec_m", "Recovery"]] = [3.6, 120.0]
        m("GEO-001", "geotech", "GV-041", "core recovery 120 %")
        g42 = geo.index[geo["HoleID"] == "GV-042"][6]
        geo.loc[g42, ["RQD_m", "RQD"]] = [float(geo.loc[g42, "Rec_m"]) + 0.5, round(100 * (float(geo.loc[g42, "Rec_m"]) + 0.5) / 3, 1)]
        m("GEO-002", "geotech", "GV-042", "RQD greater than recovery")
        dens.loc[dens.index[dens["HoleID"] == "GV-043"][2], "SG"] = 9.5
        m("DEN-001", "density", "GV-043", "density 9.5 g/cm³")
        collar.loc[collar["HoleID"] == "GV-044", "RL"] = collar.loc[collar["HoleID"] == "GV-044", "RL"].astype(float) + 12
        m("COL-011", "collar", "GV-044", "surveyed collar 12 m above topography")
        cm = collar["Campaign"] == "C-2023-DGPS"
        collar.loc[cm, "RL"] = (collar.loc[cm, "RL"].astype(float) + 3.0).round(2)
        m("COL-012", "collar", None, "campaign C has a +3 m vertical datum offset")

    # ---------------- write ----------------
    collar.to_csv(out / "collar.csv", index=False)
    survey.to_csv(out / "survey.csv", index=False)
    assay.to_csv(out / "assay.csv", index=False)
    lith.to_csv(out / "lithology.csv", index=False, encoding="utf-8-sig")
    alteration.to_csv(out / "alteration.csv", index=False)
    weathering.to_csv(out / "weathering.csv", index=False)
    geo.to_csv(out / "geotech.csv", index=False)
    dens.to_csv(out / "density.csv", index=False)
    xs, ys = np.arange(X0 - 200, X0 + 800, 10.0), np.arange(Y0 - 200, Y0 + 800, 10.0)
    gx, gy = np.meshgrid(xs, ys[::-1])
    with open(out / "dem.asc", "w") as f:
        f.write(f"ncols {len(xs)}\nnrows {len(ys)}\nxllcenter {xs[0]}\nyllcenter {ys[0]}\ncellsize 10\nNODATA_value -9999\n")
        np.savetxt(f, dem_z(gx, gy), fmt="%.2f")
    pd.DataFrame({"x": [X0, X0 + 600, X0 + 600, X0], "y": [Y0, Y0, Y0 + 600, Y0 + 600]}).to_csv(out / "licence.csv", index=False)
    pd.DataFrame([{"crm_id": c, "analyte": a, "certified": v[0], "sd": v[1]} for c, d in CRMS.items() for a, v in d.items()]).to_csv(out / "crm_standards.csv", index=False)
    pd.DataFrame(manifest, columns=["rule_id", "table", "hole_id", "description"]).to_csv(out / "manifest.csv", index=False)
    (out / "README.txt").write_text(
        "GEOVALID PRO synthetic test database (porphyry Cu-Au-Mo style, UTM 40N).\n"
        + ("Errors were injected deliberately; see manifest.csv.\n" if inject else "Clean twin: no injected errors.\n")
        + "Campaigns: A = RTK, B = handheld GPS, C = DGPS. lithology.csv uses Persian headers.\n"
        + "Grade follows a porphyry model: host unit (QMP, BXH > DIO > AND, TUF), alteration (potassic > phyllic > argillic, propylitic)\n"
        + "and weathering (leached oxide, supergene-enriched mixed zone, primary).\n", encoding="utf-8")
    return {"folder": str(out), "manifest": pd.DataFrame(manifest)}
