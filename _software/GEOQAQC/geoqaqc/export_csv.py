# -*- coding: utf-8 -*-
"""CSV exports: the 1.1 files, the 2.0 additions, and the protocol file that
records every formula, criterion, setting and rule a run used -- with a
'Changed' flag wherever the value differs from the standard protocol."""

from __future__ import annotations

import csv
import os

from .core import R_VBAD, RATING_ORDER, fmt_num
from .protocol import DEFAULT_CRITERIA, DEFAULT_FORMULAS, DEFAULT_SETTINGS, RULES

def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def export_results(project, F, C, S, RB, diagnosis, folder, base, log=print):
    R = project.results
    if not R:
        raise ValueError("Run the analysis first.")
    stamp = (base or "qaqc").strip()
    written = []

    def out(name, rows, fields):
        if not rows:
            return
        p = os.path.join(folder, f"{stamp}_{name}.csv")
        write_csv(p, rows, fields)
        written.append(p)

    # ---- scorecard ----
    score = [{"Section": "OVERALL", "Subject": "all methods", "Element": "",
              "n": len(project.samples), "Statistic": "weighted score",
              "Value": f"{R['score']:.1f}" if R["score"] is not None else "",
              "Criterion": "", "Rating": R["overall"]}]
    for (code, el), rec in sorted(R["crm"].items()):
        score.append({"Section": "CRM", "Subject": code, "Element": el,
                      "n": rec["n"], "Statistic": "mean bias %",
                      "Value": f"{rec['bias']:.3f}" if rec.get("bias") is not None else "",
                      "Criterion": C["crm_bias"]["label"], "Rating": rec["rating"]})
    for (bt, el), rec in sorted(R["blank"].items()):
        score.append({"Section": "BLANK", "Subject": bt, "Element": el,
                      "n": rec["n"], "Statistic": "failure rate %",
                      "Value": f"{rec['fail_pct']:.2f}",
                      "Criterion": C["blank_fail"]["label"], "Rating": rec["rating"]})
    for (dt, el), rec in sorted(R["dup"].items()):
        score.append({"Section": dt, "Subject": "duplicates", "Element": el,
                      "n": rec["n"],
                      "Statistic": f"P{rec['hard_pct_used']:g} HARD %",
                      "Value": f"{rec['hard_p90']:.2f}" if rec.get("hard_p90") is not None else "",
                      "Criterion": "90th percentile HARD", "Rating": rec["rating"]})
    for (dt, el), rec in sorted(R["th"].items()):
        score.append({"Section": "PRECISION", "Subject": dt, "Element": el,
                      "n": len(rec["bins"]) * rec["group"],
                      "Statistic": f"TH precision % at {fmt_num(rec['c_ref'])}",
                      "Value": f"{rec['precision_at_ref']:.2f}"
                      if rec.get("precision_at_ref") is not None else "",
                      "Criterion": C["th_precision"]["label"], "Rating": rec["rating"]})
    for el, rec in sorted(R.get("umpire", {}).items()):
        score.append({"Section": "CHECK / UMPIRE",
                      "Subject": rec.get("lab") or "umpire lab", "Element": el,
                      "n": rec["n"], "Statistic": "grade-weighted bias %",
                      "Value": f"{rec['wbias']:.3f}"
                      if rec.get("wbias") is not None else "",
                      "Criterion": C["ump_wbias"]["label"], "Rating": rec["rating"]})
    for r in R["insertion"]["rows"]:
        if r.get("info_only"):
            continue
        score.append({"Section": "INSERTION", "Subject": r["type"], "Element": "",
                      "n": r["n"], "Statistic": "insertion rate %",
                      "Value": f"{(r['pct'] or 0):.2f}",
                      "Criterion": C["insert_rate"]["label"], "Rating": r["rating"]})
    out("scorecard", score, ["Section", "Subject", "Element", "n", "Statistic",
                             "Value", "Criterion", "Rating"])

    # ---- CRM detail ----
    crm_rows = []
    for (code, el), rec in sorted(R["crm"].items()):
        for p in rec["points"]:
            crm_rows.append({
                "CRM": code, "Element": el, "Sample ID": p["sample"],
                "Batch": p["batch"], "Date": p["date"], "Sequence": p["order"],
                "Measured": p["value"], "Certified": rec.get("cert"),
                "SD": rec.get("eff_sd"),
                "Bias %": None if p["bias"] is None else round(p["bias"], 4),
                "Z-score": None if p["z"] is None else round(p["z"], 4),
                "Status": ("FAIL" if p["z"] is not None and abs(p["z"]) > S["k_fail"]
                           else "WARN" if p["z"] is not None
                           and abs(p["z"]) > S["k_warn"] else "OK"),
                "Row": p["row"]})
    out("crm_results", crm_rows,
        ["CRM", "Element", "Sample ID", "Batch", "Date", "Sequence", "Measured",
         "Certified", "SD", "Bias %", "Z-score", "Status", "Row"])

    rule_rows = []
    for (code, el), rec in sorted(R["crm"].items()):
        for r in rec["rules"]:
            rule_rows.append({"CRM": code, "Element": el, "Rule": r["rule"],
                              "Severity": r["sev"], "Sample ID": r["sample"],
                              "Z-score": round(r["z"], 4) if r["z"] is not None else "",
                              "Description": r["desc"]})
    out("crm_rule_violations", rule_rows,
        ["CRM", "Element", "Rule", "Severity", "Sample ID", "Z-score", "Description"])

    # ---- blanks ----
    bl = []
    for (bt, el), rec in sorted(R["blank"].items()):
        for p in rec["points"]:
            bl.append({"Blank type": bt, "Element": el, "Sample ID": p["sample"],
                       "Batch": p["batch"],
                       "Sequence": p["order"], "Value": p["value"],
                       "DL": rec["dl"], "x DL": round(p["ratio"], 3)
                       if p["ratio"] is not None else "",
                       "Limit": rec["limit"],
                       "Preceding Sample": p["prev_sample"],
                       "Preceding Value": p["prev_value"],
                       "Carry-over %": round(p["carry_pct"], 3)
                       if p["carry_pct"] is not None else "",
                       "Status": "FAIL" if p["fail"] else "OK", "Row": p["row"]})
    out("blank_results", bl,
        ["Blank type", "Element", "Sample ID", "Batch", "Sequence", "Value", "DL", "x DL",
         "Limit", "Preceding Sample", "Preceding Value", "Carry-over %",
         "Status", "Row"])

    # ---- duplicates ----
    dp = []
    for (dt, el), rec in sorted(R["dup"].items()):
        for r in rec["rows"]:
            dp.append({"Type": dt, "Element": el, "Original": r["orig"],
                       "Duplicate": r["dup"], "Batch": r["batch"],
                       "Value 1": r["a"], "Value 2": r["b"],
                       "Mean": round(r["mean"], 6) if r["mean"] is not None else "",
                       "Abs Diff": round(r["diff"], 6) if r["diff"] is not None else "",
                       "RD %": round(r["rd"], 4) if r["rd"] is not None else "",
                       "ARD %": round(r["ard"], 4) if r["ard"] is not None else "",
                       "HARD %": round(r["hard"], 4) if r["hard"] is not None else "",
                       "HRD %": round(r["hrd"], 4) if r["hrd"] is not None else "",
                       "CV %": round(r["cv"], 4) if r["cv"] is not None else "",
                       "Precision 95 %": round(r["prec95"], 4)
                       if r.get("prec95") is not None else ""})
    out("duplicate_pairs", dp,
        ["Type", "Element", "Original", "Duplicate", "Batch", "Value 1", "Value 2",
         "Mean", "Abs Diff", "RD %", "ARD %", "HARD %", "HRD %", "CV %",
         "Precision 95 %"])

    ds = []
    for (dt, el), rec in sorted(R["dup"].items()):
        ds.append({"Type": dt, "Element": el, "n pairs": rec["n"],
                   "Mean HARD %": round(rec["hard_mean"], 3),
                   "Median HARD %": round(rec["hard_median"], 3),
                   f"P{rec['hard_pct_used']:g} HARD %": round(rec["hard_p90"], 3),
                   "Mean RD %": round(rec["rd_mean"], 3),
                   "Mean CV %": round(rec["cv_mean"], 3),
                   "Pooled RP %": round(rec["pooled_rp"], 3)
                   if rec.get("pooled_rp") is not None else "",
                   "r": round(rec["r"], 5) if rec.get("r") is not None else "",
                   "RMA slope": round(rec["rma_b"], 5)
                   if rec.get("rma_b") is not None else "",
                   "% within 10 %": round(rec["within"][10], 1),
                   "% within 20 %": round(rec["within"][20], 1),
                   "Rating": rec["rating"]})
    if ds:
        out("duplicate_summary", ds, list(ds[0].keys()))

    # ---- Thompson-Howarth ----
    th = []
    for (dt, el), rec in sorted(R["th"].items()):
        for b in rec["bins"]:
            th.append({"Type": dt, "Element": el, "Bin size": rec["group"],
                       "Mean concentration": round(b["conc"], 6),
                       "Mean abs difference": round(b["dbar"], 6)})
        th.append({"Type": dt, "Element": el, "Bin size": "FIT",
                   "Mean concentration": f"intercept {rec['a_int']:.6g}",
                   "Mean abs difference": f"slope {rec['b_slope']:.6g}  "
                                          f"precision@{fmt_num(rec['c_ref'])} "
                                          f"= {rec['precision_at_ref']:.2f}%  "
                                          f"PDL = {fmt_num(rec['pdl'])}"})
    out("thompson_howarth", th,
        ["Type", "Element", "Bin size", "Mean concentration", "Mean abs difference"])

    um = []
    for el, rec in sorted(R.get("umpire", {}).items()):
        for r in rec["rows"]:
            um.append({"Element": el, "Umpire Lab": rec.get("lab", ""),
                       "Sample ID": r["sample"], "Primary": r["primary"],
                       "Umpire": r["umpire"],
                       "Difference": round(r["diff"], 6),
                       "Bias %": round(r["bias"], 4) if r["bias"] is not None else "",
                       "Ratio": round(r["ratio"], 6) if r["ratio"] is not None else "",
                       "HARD %": round(r["hard"], 4) if r["hard"] is not None else ""})
    out("umpire_pairs", um,
        ["Element", "Umpire Lab", "Sample ID", "Primary", "Umpire", "Difference",
         "Bias %", "Ratio", "HARD %"])

    us = []
    for el, rec in sorted(R.get("umpire", {}).items()):
        tt, wx = rec.get("ttest"), rec.get("wilcoxon")
        row = {"Element": el, "Umpire Lab": rec.get("lab", ""), "n pairs": rec["n"],
               "Sum primary": round(rec["sum_primary"], 4),
               "Sum umpire": round(rec["sum_umpire"], 4),
               "Grade-weighted bias %": round(rec["wbias"], 4)
               if rec.get("wbias") is not None else "",
               "Mean pair bias %": round(rec["pbias"], 4)
               if rec.get("pbias") is not None else "",
               "Median ratio": round(rec["median_ratio"], 5)
               if rec.get("median_ratio") is not None else "",
               f"P{rec['hard_pct_used']:g} HARD %": round(rec["hard_p90"], 3)
               if rec.get("hard_p90") is not None else "",
               "r": round(rec["r"], 5) if rec.get("r") is not None else "",
               "RMA slope": round(rec["rma_b"], 5)
               if rec.get("rma_b") is not None else "",
               "Worst quartile bias %": round(rec["worst_quartile"], 3)
               if rec.get("worst_quartile") is not None else "",
               "Paired t p": round(tt["p"], 5) if tt and tt.get("p") is not None else "",
               "Wilcoxon p": round(wx["p"], 5) if wx and wx.get("p") is not None else "",
               "Rating": rec["rating"]}
        for q in rec["quartiles"]:
            row[f"Q{q['q']} bias %"] = (round(q["bias"], 3)
                                        if q["bias"] is not None else "")
        us.append(row)
    if us:
        out("umpire_summary", us, list(us[0].keys()))

    _export_v2(project, R, F, C, S, RB, diagnosis, out)

    # ---- protocol: every formula, criterion, setting and rule actually used ----
    proto = []
    for k, d in F.defs.items():
        proto.append({"Kind": "FORMULA", "Group": d["group"], "Key": k,
                      "Label": d["label"], "Definition": d["expr"],
                      "Variables": d["vars"], "Note": d["note"],
                      "Changed": _flag(k in DEFAULT_FORMULAS
                                       and d["expr"] != DEFAULT_FORMULAS[k]["expr"])})
    for k, d in C.items():
        proto.append({"Kind": "CRITERION", "Group": d["group"], "Key": k,
                      "Label": d["label"],
                      "Definition": " | ".join(
                          f"{n} {'<=' if d['dir'] == 'low' else '>='} {c:g}"
                          for n, c in zip(RATING_ORDER[:5], d["cuts"]))
                      + f" | {R_VBAD} otherwise",
                      "Variables": d["unit"], "Note": d["note"],
                      "Changed": _flag(k in DEFAULT_CRITERIA and [float(x) for x in d["cuts"]]
                                       != [float(x) for x in DEFAULT_CRITERIA[k]["cuts"]])})
    for k, v in S.items():
        proto.append({"Kind": "SETTING", "Group": "SETTINGS", "Key": k,
                      "Label": k, "Definition": str(v), "Variables": "", "Note": "",
                      "Changed": _flag(k in DEFAULT_SETTINGS and v != DEFAULT_SETTINGS[k])})
    changed = set(RB.changed())
    for k, d in RULES.items():
        proto.append({"Kind": "RULE", "Group": d["group"], "Key": k,
                      "Label": d["label"], "Definition": RB.describe(k),
                      "Variables": d["kind"], "Note": d["note"],
                      "Changed": _flag(k in changed)})
    out("protocol", proto,
        ["Kind", "Group", "Key", "Label", "Definition", "Changed", "Variables", "Note"])

    for p in written:
        log(f"  wrote {os.path.basename(p)}")
    return written


def _flag(b):
    return "yes" if b else ""


def _r(v, n=4):
    return "" if v is None else round(v, n)


def _export_v2(project, R, F, C, S, RB, diagnosis, out):
    """The files added in 2.0."""
    L = project.clean_log
    if L is not None:
        out("cleaning_log", L.rows(),
            ["Rule", "Sample", "Element", "Original", "Action", "Reason", "Severity"])
    if diagnosis is not None:
        rows = [{"Element": f.element or "(project)", "Stage": f.stage,
                 "Severity": f.severity, "Code": f.code, "Subject": f.subject,
                 "Finding": f.title_fa, "Finding (EN)": f.title_en,
                 "Evidence": f.evidence_fa, "Cause": f.cause_fa,
                 "Actions": " | ".join(f.actions_fa), "Owner": f.owner,
                 "Timing": f.timing} for f in diagnosis.actions()]
        out("findings", rows, ["Element", "Stage", "Severity", "Code", "Subject",
                               "Finding", "Finding (EN)", "Evidence", "Cause",
                               "Actions", "Owner", "Timing"])
        vr = [{"Element": el, "Verdict": diagnosis.verdict(el)[0],
               "Text": diagnosis.verdict(el)[1]} for el in project.elements]
        out("verdicts", vr, ["Element", "Verdict", "Text"])
    eb = []
    for el, b in R.get("budget", {}).items():
        row = {"Element": el, "Total CV %": _r(b.get("total_cv_pct"), 2),
               "Dominant stage": b.get("dominant") or "",
               "Merged": b.get("merged") or "", "Notes": " | ".join(b.get("notes", []))}
        for k in ("field", "coarse", "pulp"):
            row[f"CV2 {k}"] = _r(b["cv2"].get(k), 6)
        for k, v in b.get("pct", {}).items():
            row[f"% {k}"] = _r(v, 2)
        eb.append(row)
    if eb:
        keys = []
        for r in eb:
            for k in r:
                if k not in keys:
                    keys.append(k)
        out("error_budget", eb, keys)
    bs, ra = [], []
    for el, b in R.get("batches", {}).items():
        for r in b["rows"]:
            bs.append({"Element": el, "Batch": r["batch"], "Samples": r["n"],
                       "CRM": r["crm_status"], "Blank": r["blank_status"],
                       "Status": r["status"], "Reasons": " | ".join(r["reasons"])})
        for r in b["reassay"]:
            ra.append({"Element": el, "CRM": r["crm"], "Failed CRM sample": r["failed_sample"],
                       "Rule": r["rule"], "Batch": r["batch"], "From sample": r["from_sample"],
                       "To sample": r["to_sample"], "Samples to re-assay": r["n_samples"]})
    out("batch_status", bs, ["Element", "Batch", "Samples", "CRM", "Blank", "Status",
                             "Reasons"])
    out("reassay_ranges", ra, ["Element", "CRM", "Failed CRM sample", "Rule", "Batch",
                               "From sample", "To sample", "Samples to re-assay"])
    ac = []
    for el, a in R.get("accuracy", {}).items():
        for p in a["points"]:
            ac.append({"Element": el, "CRM": p["crm"], "Certified": p["cert"],
                       "Mean measured": _r(p["mean"], 6), "n": p["n"],
                       "Bias %": _r(p["bias"], 3), "Slope": _r(a.get("b"), 5),
                       "Intercept": _r(a.get("a"), 6),
                       "Proportional bias %": _r(a.get("prop_bias_pct"), 3),
                       "p (slope = 1)": _r(a.get("p_slope"), 5)})
    out("accuracy_curve", ac, ["Element", "CRM", "Certified", "Mean measured", "n",
                               "Bias %", "Slope", "Intercept", "Proportional bias %",
                               "p (slope = 1)"])
    dr = [{"Element": el, "n": d["n"], "CRMs": d["n_crm"], "Slope % per result": _r(d["slope"], 5),
           "Change over series %": _r(d["total"], 3), "p": _r(d["p"], 5),
           "Significant": _flag(d["sig"])} for el, d in R.get("drift", {}).items()]
    out("crm_drift", dr, ["Element", "n", "CRMs", "Slope % per result",
                          "Change over series %", "p", "Significant"])
