"""Synthetic laboratory files in the GEOQAQC format (QAQC_FORMAT.md), for tests and the program's demonstration.

`generate(folder, inject=True)` writes:
  lab_qaqc.csv          laboratory / QA-QC file: routine samples with CRM, blank, coarse blank and duplicate inserts,
                        `<x` codes, IS / LNR codes and two re-assayed samples
  umpire.csv            check-laboratory results for 40 routine samples (+1 % bias)
  crm_certificates.csv  three CRMs; Au certified in ppb while the files report Au in ppb (lab) and ppm (database)
  assay_db.csv          the database assay table built from the laboratory file; with `inject`, the discrepancies
                        listed in the returned dict (one of each reconciliation class)
No real data is used.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

CRMS = {"LBCRM-1": {"Cu": (0.283, 0.009, "%"), "Au": (312, 18, "ppb"), "Ag": (0.9, 0.07, "ppm")},
        "LBCRM-2": {"Cu": (1.052, 0.028, "%"), "Au": (905, 41, "ppb"), "Ag": (3.1, 0.15, "ppm")},
        "LBCRM-3": {"Cu": (0.505, 0.015, "%"), "Au": (1480, 62, "ppb"), "Ag": (1.8, 0.1, "ppm")}}


def _fmt(v: float, dl: float, nd: int) -> str:
    return f"<{dl:g}" if v < dl else f"{v:.{nd}f}"


def generate(folder: str, inject: bool = True, seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    rows, n, seq = [], 0, 0
    holes = [f"LH{h:02d}" for h in range(1, 7)]
    routine = []
    for h in holes:
        for k in range(50):
            n += 1
            cu = float(np.exp(rng.normal(-2.0, 0.9)))
            au = cu * float(np.exp(rng.normal(6.4, 0.5)))          # ppb
            ag = cu * float(np.exp(rng.normal(1.0, 0.6)))
            routine.append({"SAMPLE_ID": f"LB{n:05d}", "HOLE_ID": h, "FROM": 2.0 * k, "TO": 2.0 * k + 2, "cu": cu, "au": au, "ag": ag})
    crm_ids = list(CRMS)
    for i, r in enumerate(routine):
        seq += 1
        rows.append({"SAMPLE_ID": r["SAMPLE_ID"], "SAMPLE_TYPE": "SAMPLE", "CRM_ID": "", "PARENT_ID": "", "BATCH": f"JOB-{1 + i // 100:02d}",
                     "SEQ": seq, "HOLE_ID": r["HOLE_ID"], "FROM": r["FROM"], "TO": r["TO"], "LAB": "LAB-A",
                     "Cu_pct": _fmt(r["cu"], 0.001, 4), "Au_ppb": _fmt(r["au"], 5, 0), "Ag_ppm": _fmt(r["ag"], 0.2, 2)})
        b = rows[-1]["BATCH"]
        if i % 20 == 9:                                            # CRM
            c = crm_ids[(i // 20) % 3]
            cert = CRMS[c]
            seq += 1
            rows.append({"SAMPLE_ID": f"{r['SAMPLE_ID']}-S", "SAMPLE_TYPE": "STD", "CRM_ID": c, "PARENT_ID": "", "BATCH": b, "SEQ": seq,
                         "HOLE_ID": r["HOLE_ID"], "FROM": "", "TO": "", "LAB": "LAB-A",
                         "Cu_pct": f"{cert['Cu'][0] + rng.normal(0, cert['Cu'][1]):.4f}", "Au_ppb": f"{cert['Au'][0] + rng.normal(0, cert['Au'][1]):.0f}",
                         "Ag_ppm": f"{cert['Ag'][0] + rng.normal(0, cert['Ag'][1]):.2f}"})
        if i % 20 == 14:                                           # blank, alternating pulp / coarse
            seq += 1
            rows.append({"SAMPLE_ID": f"{r['SAMPLE_ID']}-B", "SAMPLE_TYPE": "BLANK" if i % 40 == 14 else "CBLK", "CRM_ID": "", "PARENT_ID": "",
                         "BATCH": b, "SEQ": seq, "HOLE_ID": r["HOLE_ID"], "FROM": "", "TO": "", "LAB": "LAB-A",
                         "Cu_pct": "<0.001", "Au_ppb": "<5", "Ag_ppm": "<0.2"})
        if i % 25 == 5:                                            # field / pulp duplicate of this sample
            t = "FD" if i % 50 == 5 else "PD"
            f = float(np.exp(rng.normal(0, 0.12 if t == "FD" else 0.04)))
            seq += 1
            rows.append({"SAMPLE_ID": f"{r['SAMPLE_ID']}-{t}", "SAMPLE_TYPE": t, "CRM_ID": "", "PARENT_ID": r["SAMPLE_ID"], "BATCH": b, "SEQ": seq,
                         "HOLE_ID": r["HOLE_ID"], "FROM": "", "TO": "", "LAB": "LAB-A",
                         "Cu_pct": _fmt(r["cu"] * f, 0.001, 4), "Au_ppb": _fmt(r["au"] * f, 5, 0), "Ag_ppm": _fmt(r["ag"] * f, 0.2, 2)})
    lab = pd.DataFrame(rows)
    lab["DATE"] = "2026-03-01"
    lab.loc[lab["SAMPLE_ID"] == "LB00011", "Au_ppb"] = "IS"
    lab.loc[lab["SAMPLE_ID"] == "LB00012", "Ag_ppm"] = "LNR"
    # two re-assays at the end of the file (same SAMPLE_ID, later batch)
    re = lab[lab["SAMPLE_ID"].isin(["LB00041", "LB00042"])].copy()
    re["BATCH"], re["SEQ"] = "JOB-RE", lab["SEQ"].max() + np.arange(1, 3)
    re["Cu_pct"] = [f"{float(v) * 1.04:.4f}" for v in re["Cu_pct"]]
    lab = pd.concat([lab, re], ignore_index=True)
    # one mislabelled CRM (an LBCRM-1 result recorded as LBCRM-2) and one CRM/blank swap
    std = lab.index[lab["SAMPLE_TYPE"] == "STD"]
    c1 = CRMS["LBCRM-1"]
    lab.loc[std[1], ["CRM_ID", "Cu_pct", "Au_ppb", "Ag_ppm"]] = ["LBCRM-2", f"{c1['Cu'][0]:.4f}", f"{c1['Au'][0]:.0f}", f"{c1['Ag'][0]:.2f}"]
    lab.loc[std[2], ["CRM_ID", "Cu_pct", "Au_ppb", "Ag_ppm"]] = ["LBCRM-3", "<0.001", "<5", "<0.2"]
    # one duplicate whose PARENT_ID is mistyped (letter O for zero): it cannot be paired (QAQ-010)
    fd = lab.index[lab["SAMPLE_TYPE"] == "FD"][1]
    lab.loc[fd, "PARENT_ID"] = lab.loc[fd, "PARENT_ID"].replace("0", "O", 1)
    lab = lab[["SAMPLE_ID", "SAMPLE_TYPE", "CRM_ID", "PARENT_ID", "BATCH", "SEQ", "HOLE_ID", "FROM", "TO", "LAB", "DATE", "Cu_pct", "Au_ppb", "Ag_ppm"]]
    lab.to_csv(out / "lab_qaqc.csv", index=False)
    # certificates: LBCRM-1 written with a space, as certificates often are (QAQ-008 must not match it silently)
    cert = [{"CRM_ID": "LBCRM 1" if c == "LBCRM-1" else c, "ELEMENT": el, "CERTIFIED": v[0], "SD": v[1], "UNIT": v[2]}
            for c, d in CRMS.items() for el, v in d.items()]
    pd.DataFrame(cert).to_csv(out / "crm_certificates.csv", index=False)
    # umpire: 40 routine samples, +1 % bias, Au in ppm
    rr = [r for r in routine if r["cu"] > 0.05][:40]
    ump = pd.DataFrame({"SAMPLE_ID": [r["SAMPLE_ID"] for r in rr], "LAB": "LAB-B (umpire)", "BATCH": "UMP-01",
                        "Cu_pct": [f"{float(lab.loc[lab['SAMPLE_ID'] == r['SAMPLE_ID'], 'Cu_pct'].iloc[0].lstrip('<')) * 1.01 * float(np.exp(rng.normal(0, 0.02))):.4f}" for r in rr]})
    ump.to_csv(out / "umpire.csv", index=False)
    # database assay table: routine samples, Au stored in ppm
    first = lab[lab["SAMPLE_TYPE"] == "SAMPLE"].drop_duplicates("SAMPLE_ID")
    db = pd.DataFrame({"HOLE_ID": first["HOLE_ID"], "FROM": first["FROM"], "TO": first["TO"], "SAMPLE_ID": first["SAMPLE_ID"],
                       "Cu_pct": first["Cu_pct"], "Au_ppm": [v if v in ("IS",) else ("<0.005" if v.startswith("<") else f"{float(v) / 1000:.3f}") for v in first["Au_ppb"]],
                       "Ag_ppm": first["Ag_ppm"]}).reset_index(drop=True)
    injected = {}
    if inject:
        db = db[~db["SAMPLE_ID"].isin(["LB00030", "LB00031"])].reset_index(drop=True)
        injected["missing_in_db"] = ["LB00030", "LB00031"]
        db.loc[db["SAMPLE_ID"] == "LB00020", "SAMPLE_ID"] = "lb00020"
        injected["case_variant"] = ("lb00020", "LB00020")
        db.loc[db["SAMPLE_ID"] == "LB00050", "Cu_pct"] = "0.9999"
        injected["value_mismatch"] = "LB00050"
        v = db.loc[db["SAMPLE_ID"] == "LB00060", "Cu_pct"].iloc[0]
        db.loc[db["SAMPLE_ID"] == "LB00060", "Cu_pct"] = f"{float(v) * 1000:.1f}"
        injected["scale_x1000"] = "LB00060"
        bdl = db.index[db["Ag_ppm"].str.startswith("<")][:2]
        injected["bdl_coding"] = db.loc[bdl, "SAMPLE_ID"].tolist()
        db.loc[bdl, "Ag_ppm"] = "0.1"
        big = db.index[db["Cu_pct"].str.match(r"^\d+\.\d{4}$") & (pd.to_numeric(db["Cu_pct"], errors="coerce") > 0.1) & (db["SAMPLE_ID"].str.upper() > "LB00100") & (db["SAMPLE_ID"].str.upper() < "LB00200")][0]
        db.loc[big, "Cu_pct"] = f"{float(db.loc[big, 'Cu_pct']):.2f}"
        injected["rounded"] = db.loc[big, "SAMPLE_ID"]
        idx = db.index[(db["SAMPLE_ID"] >= "LB00201") & (db["SAMPLE_ID"] <= "LB00207")]
        ag = db.loc[idx, "Ag_ppm"].tolist()
        db.loc[idx, "Cu_pct"] = db.loc[idx, "Cu_pct"].tolist()[1:] + [db.loc[idx, "Cu_pct"].iloc[0]]
        db.loc[idx, "Ag_ppm"] = ag
        injected["offset_run"] = ("LB00201", 6)
        crm_row = lab[lab["SAMPLE_TYPE"] == "STD"].iloc[5]
        db = pd.concat([db, pd.DataFrame([{"HOLE_ID": "LH06", "FROM": 100.0, "TO": 102.0, "SAMPLE_ID": crm_row["SAMPLE_ID"], "Cu_pct": crm_row["Cu_pct"],
                                           "Au_ppm": f"{float(crm_row['Au_ppb']) / 1000:.3f}", "Ag_ppm": crm_row["Ag_ppm"]}])], ignore_index=True)
        injected["crm_in_db"] = crm_row["SAMPLE_ID"]
        u0 = ump.iloc[0]
        db.loc[db["SAMPLE_ID"] == u0["SAMPLE_ID"], "Cu_pct"] = u0["Cu_pct"]
        injected["umpire_in_db"] = u0["SAMPLE_ID"]
    db.to_csv(out / "assay_db.csv", index=False)
    return {"lab": str(out / "lab_qaqc.csv"), "umpire": str(out / "umpire.csv"), "crm": str(out / "crm_certificates.csv"),
            "db": str(out / "assay_db.csv"), "injected": injected,
            "reassayed": ["LB00041", "LB00042"], "mislabel": lab.loc[std[1], "SAMPLE_ID"], "blank_swap": lab.loc[std[2], "SAMPLE_ID"],
            "orphan_duplicate": lab.loc[fd, "SAMPLE_ID"]}


CODES = {"ORIGINAL": "SAMPLE", "CRM": "STD", "BLANK": "BLANK", "FIELD_DUP": "FD", "COARSE_DUP": "CD", "PULP_DUP": "PD"}


def from_database(folder: str, out: str | None = None, seed: int = 11) -> dict:
    """GEOQAQC laboratory and umpire files for the program's synthetic database (`synth.generate`), so the sample
    project shows a working reconciliation: the laboratory file is the database's assay table in GEOQAQC form, with a
    few laboratory-side differences (two samples the database lacks, three results the database transcribed wrongly,
    one re-assay) and an umpire subset with a small bias."""
    rng = np.random.default_rng(seed)
    src = Path(folder) / "assay.csv"
    a = pd.read_csv(src, dtype=str, keep_default_na=False)
    o = Path(out or Path(folder) / "lab")
    o.mkdir(parents=True, exist_ok=True)
    lab = pd.DataFrame({"SAMPLE_ID": a["SampleID"], "SAMPLE_TYPE": a["SampleType"].map(CODES).fillna(a["SampleType"]),
                        "CRM_ID": a["StdID"], "PARENT_ID": a["ParentID"], "BATCH": a["Batch"], "SEQ": np.arange(1, len(a) + 1),
                        "HOLE_ID": a["HoleID"], "FROM": a["From"], "TO": a["To"], "LAB": "LAB-1"})
    elems = [c for c in a.columns if "_" in c and c.split("_")[0] in ("Cu", "Au", "Mo", "S", "Fe", "Ag", "Zn", "Pb")]
    for c in elems:
        lab[c] = a[c]
    routine = lab.index[lab["SAMPLE_TYPE"] == "SAMPLE"]
    changed = []
    for i in rng.choice(routine[200:], 3, replace=False):           # the database holds a mistyped value for these
        v = lab.at[i, "Cu_pct"]
        try:
            lab.at[i, "Cu_pct"] = f"{float(v) * 1.37:.4f}"
            changed.append(lab.at[i, "SAMPLE_ID"])
        except ValueError:
            pass
    extra = lab.loc[routine[:2]].copy()                              # results the database never received
    extra["SAMPLE_ID"] = ["S900001", "S900002"]
    re = lab.loc[routine[50:51]].copy()                              # one re-assay in a later batch
    re["BATCH"], re["SEQ"] = "B999", len(lab) + 3
    re["Cu_pct"] = [f"{float(x) * 1.05:.4f}" if x.replace('.', '', 1).isdigit() else x for x in re["Cu_pct"]]
    lab = pd.concat([lab, extra, re], ignore_index=True)
    lab.to_csv(o / "lab_qaqc.csv", index=False)
    pick = rng.choice(routine, 60, replace=False)
    ump = pd.DataFrame({"SAMPLE_ID": lab.loc[pick, "SAMPLE_ID"], "LAB": "LAB-2 (umpire)", "BATCH": "U-01"})
    for c in ("Cu_pct", "Au_ppm"):
        if c in lab:
            v = pd.to_numeric(lab.loc[pick, c], errors="coerce")
            ump[c] = [f"{x * 1.02 * float(np.exp(rng.normal(0, 0.03))):.4f}" if pd.notna(x) and x > 0 else lab.at[i, c] for x, i in zip(v, pick)]
    ump.to_csv(o / "umpire.csv", index=False)
    return {"lab": str(o / "lab_qaqc.csv"), "umpire": str(o / "umpire.csv"), "changed": changed}
