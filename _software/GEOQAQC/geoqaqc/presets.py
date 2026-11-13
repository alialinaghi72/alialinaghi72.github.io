# -*- coding: utf-8 -*-
"""Project QA/QC standards loaded with one click (R19).

NLR-QAQC-SPC-001 Rev. 0 -- the North Lar (NLR) porphyry-skarn Cu-Au(-Mo)
QA/QC specification, section 4: analytical methods and QC reference DLs,
CRM rules, absolute blank limits, duplicate and umpire limits per element
and class, and the global analysis parameters."""

from __future__ import annotations

from .core import T_CDUP, T_FDUP, T_PDUP

NLR = "NLR-QAQC-SPC-001 Rev. 0"

# 4.1 methods, QC reference DL, upper limit; 4.3 blanks; R13 high grade
_ELEMENTS = {
    "Au": {"method": "FA", "qc_dl": 0.005, "qc_dl_unit": "ppm",
           "upper": 10.0, "upper_unit": "ppm",
           "blank_warn": 0.025, "blank_warn_unit": "ppm",
           "blank_fail": 0.050, "blank_fail_unit": "ppm",
           "high_grade": 0.5, "high_grade_unit": "g/t"},
    "Cu": {"method": "TOTAL", "qc_dl": 5.0, "qc_dl_unit": "ppm",
           "upper": 1.0, "upper_unit": "%",
           "blank_warn": 25.0, "blank_warn_unit": "ppm",
           "blank_fail": 50.0, "blank_fail_unit": "ppm",
           "high_grade": 0.5, "high_grade_unit": "%"},
    "Mo": {"method": "TOTAL", "qc_dl": 1.0, "qc_dl_unit": "ppm",
           "upper": 1.0, "upper_unit": "%",
           "blank_warn": 5.0, "blank_warn_unit": "ppm",
           "blank_fail": 10.0, "blank_fail_unit": "ppm",
           "high_grade": 500.0, "high_grade_unit": "ppm"},
}

# 4.4 / 4.5 rating boundaries (EXCELLENT / VERY GOOD / GOOD / POOR / BAD);
# the GOOD boundary is the acceptance limit
_CRITERIA = {
    "Cu": {"fdup_hard90": [10, 15, 20, 30, 40], "cdup_hard90": [5, 7.5, 10, 15, 20],
           "pdup_hard90": [2.5, 4, 5, 7.5, 10], "ump_hard90": [5, 7.5, 10, 15, 20],
           "th_precision": [5, 10, 15, 20, 30], "ump_wbias": [2, 3, 5, 7, 10],
           "ump_pbias": [2, 3, 5, 7, 10]},
    "Au": {"fdup_hard90": [15, 20, 30, 40, 50], "cdup_hard90": [10, 15, 20, 30, 40],
           "pdup_hard90": [7.5, 10, 15, 20, 30], "ump_hard90": [5, 10, 15, 20, 30],
           "th_precision": [10, 20, 30, 40, 50], "ump_wbias": [3, 5, 10, 15, 20],
           "ump_pbias": [3, 5, 10, 15, 20]},
    "Mo": {"fdup_hard90": [12.5, 20, 25, 35, 50], "cdup_hard90": [5, 10, 15, 20, 25],
           "pdup_hard90": [5, 7.5, 10, 15, 20], "ump_hard90": [5, 10, 15, 20, 30],
           "th_precision": [5, 10, 15, 20, 30], "ump_wbias": [2, 3, 5, 7, 10],
           "ump_pbias": [2, 3, 5, 7, 10]},
}

# 4.4 CV_avg limits (%), kept with the profile for the compliance table
_CV = {"Cu": {T_FDUP: 16, T_CDUP: 8, T_PDUP: 4, "UMPIRE": 8},
       "Mo": {T_FDUP: 20, T_CDUP: 12, T_PDUP: 8, "UMPIRE": 12},
       "Au": {T_FDUP: 24, T_CDUP: 16, T_PDUP: 12, "UMPIRE": 12}}
# 4.5 umpire acceptance
_UMPIRE = {"Cu": {"mean_diff": 5, "rma": (0.95, 1.05)},
           "Mo": {"mean_diff": 5, "rma": (0.95, 1.05)},
           "Au": {"mean_diff": 10, "rma": (0.90, 1.10)}}

# 4.2 CRM rules and 4.6 global parameters
_RULES = {"batch_fail_rules": ["1-3s", "2-2s"], "batch_warn_rules": ["2s"],
          "batch_blank_fail": True, "crm_min_kdl": 10.0, "bias_min_n": 10,
          "bias_cond": 5.0, "bias_fail": 10.0, "drift_min_crm": 10,
          "drift_min_pooled": 15, "drift_p": 0.01, "drift_total": 3.0,
          "budget_min_pairs": 30, "dup_min_kdl": 10.0}
_SETTINGS = {"k_warn": 2.0, "k_fail": 3.0, "run_len": 10, "min_crm": 10,
             "min_pairs": 20, "drop_below_dl": True}
_GLOBAL_CRITERIA = {"maxmin_fail": [3, 5, 10, 15, 20], "crm_bias": [2, 3, 5, 7.5, 10]}

PRESETS = {NLR: (_ELEMENTS, _CRITERIA, _RULES, _SETTINGS, _GLOBAL_CRITERIA)}


def apply_preset(name, RB, C, S):
    """Load a preset into the rule book (with its element profiles), the
    criteria and the settings, in place. The preset's name is kept in the
    session and printed in the report."""
    els, crits, rules, settings, gcrit = PRESETS[name]
    for sym, prof in els.items():
        for k, v in prof.items():
            if k == "method":
                continue
            RB.el.set(sym, k, v)
        RB.el.set(sym, "criteria", {k: [float(x) for x in v]
                                    for k, v in crits.get(sym, {}).items()})
        RB.el.set(sym, "cv_avg_limit", dict(_CV.get(sym, {})))
        RB.el.set(sym, "umpire_limit", dict(_UMPIRE.get(sym, {})))
        RB.el.primary[sym] = prof["method"]
    for k, v in rules.items():
        RB.set(k, v)
    S.update(settings)
    for k, cuts in gcrit.items():
        C[k]["cuts"] = [float(x) for x in cuts]
    RB.el.preset = name
    return name
