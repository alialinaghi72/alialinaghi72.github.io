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


# ===========================================================================
#  International good-practice defaults by element type
# ===========================================================================
# There is no single international standard for QA/QC acceptance limits: the
# JORC Code, NI 43-101 and CIM guidance ask for a documented programme with
# justified limits. The values below are the limits most often quoted in
# practice and are a starting point to review against the project
# specification:
#   * duplicates -- the AMEC rule (Long 1998; Simon 2004): 90 % of pairs
#     within 30 % relative difference for field (twin) samples, 20 % for
#     coarse rejects, 10 % for pulps, i.e. HARD 15 / 10 / 5 %; relaxed for
#     precious metals with a nugget effect and tightened for bulk commodities;
#   * CV_avg -- "acceptable" levels of Abzalov (2008) by commodity;
#   * blanks -- failure above 5 x DL (10 x DL for gold by fire assay);
#   * umpire -- mean difference within 5 % (10 % gold, 2 % bulk commodities).
INTERNATIONAL = "International good practice (by element type)"

ELEMENT_TYPES = {
    "precious": {
        "label": "Precious metals (Au, PGE, Ag)",
        "symbols": ("Au", "Pt", "Pd", "Rh", "Ir", "Os", "Ru", "Ag"),
        "hard90": {T_FDUP: 30.0, T_CDUP: 20.0, T_PDUP: 10.0},
        "cv": {T_FDUP: 30.0, T_CDUP: 20.0, T_PDUP: 10.0},
        "th": 20.0, "umpire": 10.0, "crm_bias": 5.0,
        "blank": (5.0, 10.0),
        "outlier_hard": {T_FDUP: 67.0, T_CDUP: 67.0, T_PDUP: 67.0},
        "outlier_preselect": "keep", "single_vote": False},
    "base": {
        "label": "Base metals (Cu, Pb, Zn, Ni, Co, Sn)",
        "symbols": ("Cu", "Pb", "Zn", "Ni", "Co", "Sn", "Sb", "As", "Bi", "Cd"),
        "hard90": {T_FDUP: 15.0, T_CDUP: 10.0, T_PDUP: 5.0},
        "cv": {T_FDUP: 15.0, T_CDUP: 10.0, T_PDUP: 5.0},
        "th": 10.0, "umpire": 5.0, "crm_bias": 5.0,
        "blank": (3.0, 5.0),
        "outlier_hard": {T_FDUP: 67.0, T_CDUP: 50.0, T_PDUP: 50.0},
        "outlier_preselect": "exclude", "single_vote": True},
    "minor": {
        "label": "Minor and by-product metals (Mo, W, U, Re, Li, REE)",
        "symbols": ("Mo", "W", "U", "Re", "Li", "Nb", "Ta", "La", "Ce", "Nd", "Y", "V"),
        "hard90": {T_FDUP: 20.0, T_CDUP: 15.0, T_PDUP: 7.5},
        "cv": {T_FDUP: 20.0, T_CDUP: 15.0, T_PDUP: 10.0},
        "th": 15.0, "umpire": 5.0, "crm_bias": 5.0,
        "blank": (3.0, 5.0),
        "outlier_hard": {T_FDUP: 67.0, T_CDUP: 50.0, T_PDUP: 50.0},
        "outlier_preselect": "exclude", "single_vote": True},
    "bulk": {
        "label": "Bulk commodities (Fe, Al, Si, Mn, Cr, Ti, P, S)",
        "symbols": ("Fe", "Al", "Si", "Mn", "Cr", "Ti", "P", "S", "Ca", "Mg", "K", "Na"),
        "hard90": {T_FDUP: 5.0, T_CDUP: 3.0, T_PDUP: 1.5},
        "cv": {T_FDUP: 5.0, T_CDUP: 3.0, T_PDUP: 1.5},
        "th": 5.0, "umpire": 2.0, "crm_bias": 2.0,
        "blank": (3.0, 5.0),
        "outlier_hard": {T_FDUP: 50.0, T_CDUP: 30.0, T_PDUP: 20.0},
        "outlier_preselect": "exclude", "single_vote": True},
}
_TYPE_OF = {s: t for t, d in ELEMENT_TYPES.items() for s in d["symbols"]}


def element_type(element):
    """'Au_ppb' -> 'precious'; an element not listed is treated as a base metal."""
    from .core import element_symbol
    return _TYPE_OF.get(element_symbol(element), "base")


def _five(good):
    """Five rating boundaries around an acceptance limit (GOOD)."""
    return [round(good * k, 4) for k in (0.5, 0.75, 1.0, 1.5, 2.0)]


def element_type_defaults(element):
    """(profile values, criteria) of the element's type."""
    d = ELEMENT_TYPES[element_type(element)]
    h = d["hard90"]
    crit = {"fdup_hard90": _five(h[T_FDUP]), "cdup_hard90": _five(h[T_CDUP]),
            "pdup_hard90": _five(h[T_PDUP]), "th_precision": _five(d["th"]),
            "ump_wbias": _five(d["umpire"]), "ump_pbias": _five(d["umpire"]),
            "crm_bias": _five(d["crm_bias"])}
    lo = round(1.0 - d["umpire"] / 100.0, 3)
    prof = {"low_kdl": {T_FDUP: None, T_CDUP: None, T_PDUP: None}, "low_action": "exclude",
            "outlier_hard": dict(d["outlier_hard"]), "outlier_action": "ask",
            "outlier_preselect": d["outlier_preselect"], "single_vote": d["single_vote"],
            "blank_warn": d["blank"][0], "blank_warn_unit": "x DL",
            "blank_fail": d["blank"][1], "blank_fail_unit": "x DL",
            "high_grade": None, "high_grade_unit": "",
            "cv_avg_limit": dict(d["cv"]),
            "umpire_limit": {"mean_diff": d["umpire"], "rma": (lo, round(2.0 - lo, 3))},
            "criteria": crit}
    return prof, crit


def apply_element_defaults(RB, elements, what="all"):
    """Set the international good-practice defaults of each element's type.
    what: 'all' (profile and criteria), 'criteria' or 'profile'. The values
    that belong to the laboratory and the deposit -- analytical method, QC
    detection limit, upper limit, cut-off grade -- are left as they are.
    Returns {element: type label}."""
    from .core import element_symbol
    done = {}
    for el in elements:
        sym = element_symbol(el)
        prof, crit = element_type_defaults(el)
        cur = RB.el.overrides.setdefault(sym, {})
        if what in ("all", "profile"):
            for k, v in prof.items():
                if k == "criteria":
                    continue
                cur[k] = dict(v) if isinstance(v, dict) else v
        if what in ("all", "criteria"):
            cur["criteria"] = {k: list(v) for k, v in crit.items()}
        done[el] = ELEMENT_TYPES[element_type(el)]["label"]
    if done and not RB.el.preset:
        RB.el.preset = INTERNATIONAL
    return done
