#!/usr/bin/env python3
"""Generate the GEOQAQC 2.0 demonstration dataset.

A synthetic porphyry Cu-Au-Mo-Ag drilling programme: 12 holes, 12 laboratory
batches, about 1460 rows. The CRM codes (DEMO-501, DEMO-504, DEMO-ME1) and
their certificates are invented for this demonstration; they are NOT the
published values of any commercial reference material.

Every result is built as  true grade x sampling error x preparation error x
analytical error x laboratory bias,  so field, coarse and pulp duplicates
carry exactly the stages of the sample chain they are meant to test.

Defects planted on purpose, each of which GEOQAQC must find:

  Cu  laboratory drift: bias falls from 0 to -6 % over batches 7-12
  Cu  coarse blanks after high-grade samples in batches 5-6 read 20-60 x DL
      (crusher carry-over); pulp blanks stay clean
  Cu  the umpire laboratory reads 6 % lower than the primary
  Au  nugget effect: field-duplicate CV ~39 %, coarse ~13 %, pulp ~4 %
  Ag  +11 % proportional calibration bias on everything
  Mo  clean -- the control element
  data  one CRM labelled DEMO-504 that is really DEMO-501; one CRM with Cu
        typed in ppm (x 10000); one CRM slot holding a blank; one coarse
        blank that is really DEMO-ME1; one field duplicate taken from the
        wrong sample; two re-assays under existing IDs; IS / LNR codes,
        -999 sentinels and negative below-detection values; one duplicate
        with a mistyped parent ID; certificate written 'DEMO 501' and Au
        certified in ppb
  QC design  coarse duplicates at about 2.5 %

The default seed is one for which the random noise adds no spurious finding
(a chance p < 0.05 drift appears in roughly one seed in six), so the demo
shows the planted defects and nothing else.

    python sample_data/make_demo.py
"""

import csv
import math
import os
import random

ELS = ["Cu_pct", "Au_ppm", "Ag_ppm", "Mo_ppm"]
DL = {"Cu_pct": 0.001, "Au_ppm": 0.005, "Ag_ppm": 0.2, "Mo_ppm": 1.0}
DEC = {"Cu_pct": 4, "Au_ppm": 3, "Ag_ppm": 2, "Mo_ppm": 1}
# relative standard deviation of each stage: sampling, preparation, analysis
SIG = {"Cu_pct": (0.06, 0.03, 0.015), "Au_ppm": (0.37, 0.14, 0.043),
       "Ag_ppm": (0.08, 0.04, 0.03), "Mo_ppm": (0.07, 0.03, 0.02)}
CERTS = {
    "DEMO-501": {"Cu_pct": (0.283, 0.009), "Au_ppm": (0.312, 0.018),
                 "Ag_ppm": (0.90, 0.07), "Mo_ppm": (90.0, 4.0)},
    "DEMO-504": {"Cu_pct": (1.052, 0.028), "Au_ppm": (0.905, 0.041),
                 "Ag_ppm": (3.10, 0.15), "Mo_ppm": (300.0, 12.0)},
    "DEMO-ME1": {"Cu_pct": (0.505, 0.015), "Au_ppm": (1.480, 0.062),
                 "Ag_ppm": (1.80, 0.10), "Mo_ppm": (25.0, 1.5)},
}
UMPIRE = {"Cu_pct": (0.94, 0.02), "Au_ppm": (1.0, 0.08),
          "Ag_ppm": (1 / 1.11, 0.04), "Mo_ppm": (1.0, 0.03)}
N_BATCH, PER_BATCH = 12, 100
COLS = ["SAMPLE_ID", "SAMPLE_TYPE", "CRM_ID", "PARENT_ID", "BATCH", "SEQ",
        "HOLE_ID", "FROM", "TO", "DRILL_TYPE", "LAB", "DATE"] + ELS


def lab_factor(el, b):
    if el == "Cu_pct" and b >= 6:
        return 1.0 - 0.06 * (b - 5) / 6.0
    if el == "Ag_ppm":
        return 1.11
    return 1.0


def fmt(el, v):
    if v is None:
        return ""
    if v < DL[el]:
        return f"<{DL[el]:g}"
    return f"{v:.{DEC[el]}f}"


def make_demo(out_dir, seed=2036):
    rng = random.Random(seed)
    ln = rng.gauss

    def err(el, stage):
        return math.exp(ln(0, SIG[el][stage]))

    rows, umpire = [], []
    seq = [0]

    def add(**kw):
        seq[0] += 1
        r = {c: "" for c in COLS}
        r.update(kw)
        r["SEQ"] = seq[0]
        rows.append(r)
        return r

    routine = []                       # (row, true, splitA, pulpA, batch)
    n_std = n_blk = 0
    crm_cycle = ["DEMO-501", "DEMO-ME1", "DEMO-504"]
    for b in range(N_BATCH):
        batch = f"JOB-25{b + 1:02d}"
        hole = f"BH-{b + 1:02d}"
        drill = "DD" if b < 8 else "RC"
        date = f"2025-{(b // 2) + 3:02d}-{(b % 2) * 14 + 5:02d}"
        base = dict(BATCH=batch, HOLE_ID=hole, DRILL_TYPE=drill, LAB="LAB-1",
                    DATE=date)
        # true grades down the hole, with a leached cap at the top
        trues = []
        for i in range(PER_BATCH):
            cu = math.exp(ln(math.log(0.35), 0.75))
            if i < 8:
                cu *= 0.05
            au = 0.55 * cu ** 1.1 * math.exp(ln(0, 0.5))
            ag = 2.2 * cu * math.exp(ln(0, 0.35))
            mo = math.exp(ln(math.log(80), 0.85)) * (0.1 if i < 8 else 1.0)
            trues.append({"Cu_pct": cu, "Au_ppm": au, "Ag_ppm": ag, "Mo_ppm": mo})
        # in batches 5 and 6 the coarse blanks follow the three richest samples
        if b in (4, 5):
            rich = sorted(range(PER_BATCH), key=lambda i: -trues[i]["Cu_pct"])[:3]
            cblank_after = set(rich)
        else:
            cblank_after = {5, 38, 71}
        for i, tg in enumerate(trues):
            sid = f"GQ{b * PER_BATCH + i + 1:05d}"
            split_a = {e: tg[e] * err(e, 0) for e in ELS}
            pulp_a = {e: split_a[e] * err(e, 1) for e in ELS}
            val = {e: pulp_a[e] * err(e, 2) * lab_factor(e, b) for e in ELS}
            r = add(SAMPLE_ID=sid, SAMPLE_TYPE="SAMPLE", FROM=f"{2 * i:.1f}",
                    TO=f"{2 * i + 2:.1f}", **base,
                    **{e: fmt(e, val[e]) for e in ELS})
            routine.append((r, tg, split_a, pulp_a, b, val))
            if i % 10 == 4:                                   # umpire pulp
                urow = {"SAMPLE_ID": sid, "LAB": "LAB-2 (umpire)", "BATCH": batch}
                for e in ELS:
                    f, s = UMPIRE[e]
                    urow[e] = fmt(e, pulp_a[e] * math.exp(ln(0, s))
                                  * lab_factor(e, b) * f)
                umpire.append(urow)
            if i % 20 == 7:                                   # field duplicate
                dv = {e: tg[e] * err(e, 0) * err(e, 1) * err(e, 2)
                      * lab_factor(e, b) for e in ELS}
                add(SAMPLE_ID=f"{sid}-FD", SAMPLE_TYPE="FD", PARENT_ID=sid, **base,
                    **{e: fmt(e, dv[e]) for e in ELS})
            if i % 33 == 20:                                  # coarse duplicate
                dv = {e: split_a[e] * err(e, 1) * err(e, 2) * lab_factor(e, b)
                      for e in ELS}
                add(SAMPLE_ID=f"{sid}-CD", SAMPLE_TYPE="CD", PARENT_ID=sid, **base,
                    **{e: fmt(e, dv[e]) for e in ELS})
            if i % 25 == 12:                                  # pulp duplicate
                dv = {e: pulp_a[e] * err(e, 2) * lab_factor(e, b) for e in ELS}
                add(SAMPLE_ID=f"{sid}-PD", SAMPLE_TYPE="PD", PARENT_ID=sid, **base,
                    **{e: fmt(e, dv[e]) for e in ELS})
            if i in cblank_after:                             # coarse blank
                n_blk += 1
                bv = {e: DL[e] * rng.uniform(0.3, 1.6) for e in ELS}
                if b in (4, 5):
                    bv["Cu_pct"] = max(val["Cu_pct"] * rng.uniform(0.012, 0.025),
                                       0.02)
                add(SAMPLE_ID=f"GQ-BLK-{n_blk:04d}", SAMPLE_TYPE="CBLK", **base,
                    **{e: fmt(e, bv[e]) for e in ELS})
            if i % 50 == 30:                                  # pulp blank
                n_blk += 1
                bv = {e: DL[e] * rng.uniform(0.3, 1.4) for e in ELS}
                add(SAMPLE_ID=f"GQ-BLK-{n_blk:04d}", SAMPLE_TYPE="PBLK", **base,
                    **{e: fmt(e, bv[e]) for e in ELS})
            if i % 20 == 15:                                  # CRM
                code = crm_cycle[n_std % 3]
                n_std += 1
                cv = {e: CERTS[code][e][0] * math.exp(ln(0, CERTS[code][e][1]
                                                         / CERTS[code][e][0]))
                      * lab_factor(e, b) for e in ELS}
                add(SAMPLE_ID=f"GQ-STD-{n_std:04d}", SAMPLE_TYPE="STD",
                    CRM_ID=code, **base, **{e: fmt(e, cv[e]) for e in ELS})

    _plant_defects(rows, routine, rng)
    _write(out_dir, rows, umpire)
    return out_dir


def _find(rows, **kw):
    return [r for r in rows if all(r[k] == v for k, v in kw.items())]


def _plant_defects(rows, routine, rng):
    stds = [r for r in rows if r["SAMPLE_TYPE"] == "STD"]
    # C13: a DEMO-501 result labelled DEMO-504 (batch 3)
    s = [r for r in stds if r["CRM_ID"] == "DEMO-501" and r["BATCH"] == "JOB-2503"][0]
    s["CRM_ID"] = "DEMO-504"
    # C12: Cu typed in ppm on one CRM (batch 4)
    s = [r for r in stds if r["BATCH"] == "JOB-2504"][1]
    s["Cu_pct"] = f"{float(s['Cu_pct']) * 10000:.0f}"
    # C14: a blank in a CRM slot (batch 8)
    s = [r for r in stds if r["BATCH"] == "JOB-2508"][2]
    for e in ELS:
        s[e] = fmt(e, DL[e] * rng.uniform(0.5, 1.5))
    # C15: DEMO-ME1 inserted as a coarse blank (batch 9)
    s = _find(rows, SAMPLE_TYPE="CBLK", BATCH="JOB-2509")[1]
    for e in ELS:
        c, sd = CERTS["DEMO-ME1"][e]
        s[e] = fmt(e, c + rng.uniform(-sd, sd))
    # C16: a field duplicate that is really another, five times richer sample
    fds = _find(rows, SAMPLE_TYPE="FD", BATCH="JOB-2510")
    by_id = {r["SAMPLE_ID"]: r for r in rows}
    for fd in fds:
        parent = by_id[fd["PARENT_ID"]]
        if all(not parent[e].startswith("<") and float(parent[e]) > 10 * DL[e]
               for e in ("Cu_pct", "Au_ppm", "Mo_ppm")):
            for e in ELS:
                v = parent[e].lstrip("<")
                fd[e] = fmt(e, float(v) * 5.0 * rng.uniform(0.95, 1.05))
            break
    # C17: a duplicate with a mistyped parent (batch 11)
    fd = _find(rows, SAMPLE_TYPE="FD", BATCH="JOB-2511")[0]
    fd["PARENT_ID"] = fd["PARENT_ID"].replace("GQ", "GO")
    # C04 / C05 / C06: text codes, sentinels, negative values (batch 2)
    norm = [r for r in rows if r["SAMPLE_TYPE"] == "SAMPLE" and r["BATCH"] == "JOB-2502"]
    for r, code in zip(norm[10:13], ["IS", "IS", "IS"]):
        r["Au_ppm"] = code
    for r in norm[20:22]:
        r["Ag_ppm"] = "LNR"
    for r in norm[30:32]:
        r["Mo_ppm"] = "-999"
    for r in norm[0:5]:
        r["Cu_pct"] = "-0.001"
    # C03: two re-assays appended under existing IDs
    for r in norm[40:42]:
        re_ = dict(r)
        re_["Cu_pct"] = f"{float(r['Cu_pct'].lstrip('<')) * 1.04:.4f}"
        re_["SEQ"] = len(rows) + 1
        rows.append(re_)


def _write(out_dir, rows, umpire):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "demo_assay.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(out_dir, "demo_umpire.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["SAMPLE_ID", "LAB", "BATCH"] + ELS)
        w.writeheader()
        w.writerows(umpire)
    with open(os.path.join(out_dir, "demo_crm_certificates.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["CRM_ID", "ELEMENT", "CERTIFIED", "SD", "UNIT"])
        for code, els in CERTS.items():
            label = "DEMO 501" if code == "DEMO-501" else code
            for e, (c, sd) in els.items():
                sym = e.split("_")[0]
                if e == "Au_ppm":
                    w.writerow([label, sym, f"{c * 1000:g}", f"{sd * 1000:g}", "ppb"])
                else:
                    unit = {"Cu_pct": "%", "Ag_ppm": "ppm", "Mo_ppm": "ppm"}[e]
                    w.writerow([label, sym, f"{c:g}", f"{sd:g}", unit])


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    make_demo(here)
    print("demo_assay.csv, demo_crm_certificates.csv, demo_umpire.csv written to", here)
