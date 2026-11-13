# -*- coding: utf-8 -*-
"""Compliance against the project QA/QC specification (R22).

One row per control and criterion: the spec limit, the observed value, the
number of results, and PASS / CONDITIONAL / FAIL -- or INSUFFICIENT when n
is below the minimum, which draws no conclusion. It replaces a weighted
overall score, which hides which control failed.
"""

from __future__ import annotations

import math

from .core import DUP_TYPES, T_UMP
from .elements import criteria_for

PASS, COND, FAIL, INSUFF = "PASS", "CONDITIONAL", "FAIL", "INSUFFICIENT"

_DUP_CRIT = {"FIELD DUP": "fdup_hard90", "COARSE DUP": "cdup_hard90",
             "PULP DUP": "pdup_hard90"}


def _cv_avg(rec):
    v = rec.get("cv2_mean") if rec else None
    return math.sqrt(v) * 100.0 if v is not None and v >= 0 else None


def compliance(project, R, C, S, RB):
    """[{element, control, criterion, limit, observed, unit, n, result}]."""
    rows = []

    def add(el, control, criterion, limit, observed, n, result, unit="%"):
        rows.append({"element": el, "control": control, "criterion": criterion,
                     "limit": limit, "observed": observed, "unit": unit, "n": n,
                     "result": result})

    for el in project.elements:
        Ce = criteria_for(C, RB, el)
        # ---- CRMs: Westgard per batch, cumulative bias ----
        pts = (R.get("batches", {}).get(el) or {}).get("crm_points", [])
        fail_rules = set(RB["batch_fail_rules"])
        by_crm = {}
        for x in pts:
            by_crm.setdefault(x[2], []).append(x)
        for (lab, e), rec in sorted(R.get("crm", {}).items()):
            if e != el or rec.get("status") != "EVALUATED":
                continue
            px = by_crm.get(lab, [])
            nf = sum(1 for x in px if x[3] & fail_rules)
            add(el, lab, "rules", "/".join(sorted(fail_rules)), nf, rec["n"],
                FAIL if nf else PASS, unit="")
            b = rec.get("bias")
            if rec["n"] < RB["bias_min_n"] or b is None:
                res = INSUFF
            elif abs(b) > RB["bias_fail"]:
                res = FAIL
            elif abs(b) > RB["bias_cond"]:
                res = COND
            else:
                res = PASS
            add(el, lab, "bias", RB["bias_cond"], b, rec["n"], res)
        # ---- blanks ----
        for (bt, e), rec in sorted(R.get("blank", {}).items()):
            if e != el:
                continue
            vals = [p["value"] for p in rec.get("points", []) if p.get("value") is not None]
            add(el, bt, "blank", rec.get("limit"), max(vals) if vals else None, rec["n"],
                FAIL if rec.get("n_fail") else PASS, unit="")
        # ---- duplicates: HARD90 and CV_avg against the element's limits ----
        cvlim = RB.el.profile(el).get("cv_avg_limit") or {}
        for dt in DUP_TYPES:
            rec = R.get("dup", {}).get((dt, el))
            if not rec:
                continue
            n = rec["n"]
            enough = n >= S["min_pairs"]
            good = Ce[_DUP_CRIT[dt]]["cuts"][2]
            h = rec.get("hard_p90")
            add(el, dt, "hard90", good, h, n,
                INSUFF if not enough or h is None else PASS if h <= good else FAIL)
            lim = cvlim.get(dt)
            cv = _cv_avg(rec)
            if lim is not None:
                add(el, dt, "cv_avg", lim, cv, n,
                    INSUFF if not enough or cv is None else PASS if cv <= lim else FAIL)
        # ---- umpire ----
        u = R.get("umpire", {}).get(el)
        if u:
            ul = RB.el.profile(el).get("umpire_limit") or {}
            lim = ul.get("mean_diff", Ce["ump_wbias"]["cuts"][2])
            wb = u.get("wbias")
            add(el, T_UMP, "umpire", lim, wb, u["n"],
                INSUFF if u["n"] < S["min_pairs"] or wb is None else
                PASS if abs(wb) <= lim else FAIL)
    # ---- insertion against the class targets ----
    ins = R.get("insertion") or {}
    for r in ins.get("rows", []):
        if r.get("info_only") or not r.get("target"):
            continue
        add("", r["type"], "insertion", r["target"], r.get("pct"), r["n"],
            PASS if (r.get("pct") or 0) >= r["target"] else FAIL)
    return rows

