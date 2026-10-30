#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEOQAQC  --  Analytical Quality Control Suite
=============================================
QA/QC of geochemical analytical data from ANY sampling medium: drillhole
intervals, trenches, channels, soils, rock chips, stream sediments.

Design note
-----------
The key of this application is the SAMPLE ID, not a hole/from/to triple.
CRMs and blanks have no spatial position at all, and a trench sample is not
a drillhole interval. Location (hole, from, to / trench, station) is therefore
an OPTIONAL ATTRIBUTE of a sample, never its identity. That single decision
is what lets one tool cover drillholes, trenches and surface sampling.

Methods implemented (international standard practice)
-----------------------------------------------------
CRM / standards      Shewhart control chart, bias %, z-score, Westgard-style
                     failure rules (1-3s, 2-2s, 4-1s, 10x run), failure and
                     warning rates, per-batch bias drift
Blanks               contamination threshold as a multiple of the detection
                     limit, carry-over test against the preceding sample,
                     failure rate
Duplicates           RD%, ARD%, HARD%, HRD%, pair CV%, relative precision at
                     95%, rank-HARD plot, correlation and reduced major axis
                     regression, scatter with 1:1 line and precision envelope,
                     mean-vs-difference (Bland-Altman) plot
Precision            Thompson & Howarth (1978) binned precision regression,
                     precision curve and practical detection limit
Insertion            control sample insertion rates against the 5% convention

Every computed quantity is an EDITABLE EXPRESSION. Nothing is hard-coded in
the analysis path: open the Formulas tab and change any expression, or open
the Criteria tab and change any rating threshold. Both are saved with the
session, so a project can carry its own agreed QA/QC protocol.

Ratings                VERY BAD - BAD - POOR - GOOD - VERY GOOD - EXCELLENT
Every rating comes from an explicit, visible, editable threshold band.

Requirements : Python 3.9+ only. No third-party packages.
Run          : double-click RUN_GEOQAQC.bat, or  python GEOQAQC.py
Build .exe   : see BUILD_EXE.bat
"""

from __future__ import annotations

import ast
import csv
import datetime as _dt
import json
import math
import os
import sys

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "GEOQAQC"
APP_SUB = "Analytical Quality Control Suite"
APP_VER = "1.1"

# ---------------------------------------------------------------------------
# Palette -- identical to GEOVALID so the two tools look like one family
# ---------------------------------------------------------------------------
BG0 = "#0f1419"
BG1 = "#161c24"
BG2 = "#1e2733"
BG3 = "#2a3644"
FG = "#dce4ee"
FG_DIM = "#8593a5"
ACCENT = "#d99a3e"
ACCENT_D = "#a8752c"
C_OK = "#4fae7f"
C_WARN = "#e0b342"
C_ERR = "#e0605c"
C_INFO = "#5a9fd4"
C_PLOT = "#7cc0f0"
C_PLOT2 = "#c99ae0"

MONO = ("Consolas", 9)
MONO_B = ("Consolas", 9, "bold")
UI = ("Segoe UI", 9)
UI_B = ("Segoe UI", 9, "bold")
UI_H = ("Segoe UI Semibold", 11)
UI_TITLE = ("Segoe UI", 17)

STRATA = ["#8a6a45", "#6d7f8c", "#a8853f", "#5c6b5a", "#7a5a55"]

# ---------------------------------------------------------------------------
# Rating scale
# ---------------------------------------------------------------------------
R_EXC = "EXCELLENT"
R_VG = "VERY GOOD"
R_GOOD = "GOOD"
R_POOR = "POOR"
R_BAD = "BAD"
R_VBAD = "VERY BAD"
R_NA = "NO DATA"

RATING_ORDER = [R_EXC, R_VG, R_GOOD, R_POOR, R_BAD, R_VBAD]
RATING_COLOR = {R_EXC: "#3fbf8f", R_VG: "#4fae7f", R_GOOD: "#9ec46a",
                R_POOR: C_WARN, R_BAD: "#e08a4a", R_VBAD: C_ERR, R_NA: FG_DIM}
RATING_SCORE = {R_EXC: 100.0, R_VG: 85.0, R_GOOD: 70.0, R_POOR: 50.0,
                R_BAD: 30.0, R_VBAD: 10.0}

# grouping dimensions offered on every precision tab
GROUP_NONE = "None (all data)"
GROUP_HOLE = "Hole / trench"
GROUP_BATCH = "Batch"
GROUP_DRILL = "Drill type"
GROUP_LAB = "Laboratory"
GROUP_KEYS = {GROUP_NONE: None, GROUP_HOLE: "hole", GROUP_BATCH: "batch",
              GROUP_DRILL: "drilltype", GROUP_LAB: "lab"}
GROUP_CHOICES = [GROUP_NONE, GROUP_HOLE, GROUP_BATCH, GROUP_DRILL, GROUP_LAB]

SEV_ERROR = "ERROR"
SEV_WARN = "WARNING"

# sample classes
T_NORMAL = "NORMAL"
T_CRM = "CRM"
T_BLANK = "BLANK"
T_FDUP = "FIELD DUP"
T_CDUP = "COARSE DUP"
T_PDUP = "PULP DUP"
T_UMP = "CHECK / UMPIRE"
SAMPLE_TYPES = [T_NORMAL, T_CRM, T_BLANK, T_FDUP, T_CDUP, T_PDUP, T_UMP]
DUP_TYPES = [T_FDUP, T_CDUP, T_PDUP]

# common codes seen in real laboratory submission files
TYPE_HINTS = {
    T_CRM: ["crm", "std", "standard", "stnd", "ref", "reference", "oreas", "geostats",
            "cdn", "amis", "rocklabs", "shaw", "control"],
    T_BLANK: ["blank", "blk", "bl", "barren", "silica", "quartz"],
    T_FDUP: ["fd", "f_dup", "f-dup", "fdup", "field dup", "field duplicate",
             "field", "twin", "quarter core", "1/4 core", "second split", "dup"],
    T_CDUP: ["cd", "c_dup", "c-dup", "cdup", "coarse dup", "coarse duplicate",
             "crush", "crushed", "reject", "coarse reject"],
    T_PDUP: ["pd", "p_dup", "p-dup", "pdup", "pulp dup", "pulp duplicate", "pulp",
             "lab dup", "lab duplicate", "repeat"],
    T_UMP: ["umpire", "check", "check assay", "umpire assay", "referee",
            "second lab", "external", "ext", "um", "chk", "inter-lab",
            "interlab", "round robin"],
    T_NORMAL: ["normal", "sample", "routine", "primary", "original", "ore", "core"],
}


# ===========================================================================
#  Generic helpers
# ===========================================================================
NULL_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "nd", "n.d."}


def fnum(v):
    """Permissive float parse. Handles '<0.01' and '>10000' detection-limit
    notation by returning the numeric part; use dl_flag() to know which."""
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if s.lower() in NULL_TOKENS:
        return None
    if s and s[0] in "<>":
        s = s[1:].strip()
    try:
        return float(s)
    except ValueError:
        return None


def dl_flag(v):
    """'<' below detection, '>' over range, '' normal."""
    if v is None:
        return ""
    s = str(v).strip()
    # NOTE: `s[:1] in "<>"` is True for an empty string, because "" is a
    # substring of everything. That made every blank cell raise IndexError.
    return s[0] if s and s[0] in "<>" else ""


def is_blank(v):
    return v is None or str(v).strip().lower() in NULL_TOKENS


def sniff_and_read(path, max_rows=None):
    """Read a delimited text file. Returns (header, rows, delimiter)."""
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        sample = fh.read(64 * 1024)
        fh.seek(0)
        delim = ","
        try:
            delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except Exception:
            counts = {d: sample.count(d) for d in ",;\t|"}
            delim = max(counts, key=counts.get) if max(counts.values()) else ","
        rdr = csv.reader(fh, delimiter=delim)
        try:
            header = next(rdr)
        except StopIteration:
            return [], [], delim
        header = [h.strip().lstrip("\ufeff") for h in header]
        seen, clean = {}, []
        for i, h in enumerate(header):
            h = h if h else f"COLUMN_{i + 1}"
            if h in seen:
                seen[h] += 1
                h = f"{h}_{seen[h]}"
            else:
                seen[h] = 0
            clean.append(h)
        rows = []
        n = len(clean)
        for r in rdr:
            if not any(str(x).strip() for x in r):
                continue
            if len(r) < n:
                r = list(r) + [""] * (n - len(r))
            elif len(r) > n:
                r = list(r[:n])
            rows.append(r)
            if max_rows and len(rows) >= max_rows:
                break
        return clean, rows, delim


ROLE_HINTS = {
    "sampleid": ["sampleid", "sample_id", "sample id", "sample", "sampno", "sample_no",
                 "sampleno", "id", "labid", "lab_id", "sample_number", "samp"],
    "type": ["sampletype", "sample_type", "sample type", "type", "qc", "qctype",
             "qc_type", "class", "category", "sampclass"],
    "crmid": ["crmid", "crm_id", "crm", "standard", "std", "stdid", "std_id",
              "controlid", "reference", "refmat"],
    "parent": ["parent", "parentid", "parent_id", "original", "originalid",
               "orig_id", "origid", "source", "duplicateof", "twin_of", "master"],
    "batch": ["batch", "batchid", "batch_id", "job", "jobno", "job_no", "submission",
              "shipment", "dispatch", "workorder", "certificate", "report"],
    "lab": ["lab", "laboratory", "labname", "lab_name", "assayer", "provider"],
    "drilltype": ["drilltype", "drill_type", "drill type", "holetype", "hole_type",
                  "method", "drilling", "drill", "rig", "type_of_drilling",
                  "sampletype2", "media", "medium", "sample_medium"],
    "date": ["date", "assaydate", "assay_date", "reportdate", "analysisdate",
             "date_received", "datereported"],
    "order": ["order", "seq", "sequence", "position", "index", "runorder", "no", "row"],
    "element": ["element", "analyte", "el", "elem", "variable", "det"],
    "certified": ["certified", "cert", "certvalue", "cert_value", "expected", "value",
                  "mean", "recommended", "best_value"],
    "sd": ["sd", "stdev", "std_dev", "stddev", "sigma", "s", "1sd", "onesd",
           "standard_deviation", "uncertainty"],
    "unit": ["unit", "units", "uom"],
    "method": ["method", "technique", "digest", "analysismethod", "assay_method"],
    "dl": ["dl", "detectionlimit", "detection_limit", "lod", "mdl", "ldl"],
    # optional location roles
    "holeid": ["holeid", "hole_id", "hole", "bhid", "dhid", "drillhole", "trench",
               "trenchid", "site", "station", "line"],
    "from": ["from", "depth_from", "from_m", "fromdepth", "top", "start"],
    "to": ["to", "depth_to", "to_m", "todepth", "bottom", "base", "end"],
    "dupid": ["dupid", "dup_id", "duplicate", "duplicateid", "duplicate_id",
              "pair", "checkid", "check_id", "repeat_id"],
    "umplab": ["umpirelab", "umpire_lab", "checklab", "check_lab", "lab2",
               "second_lab", "external_lab", "referee"],
}


def guess_role(header, role, taken=()):
    hints = ROLE_HINTS.get(role, [])
    low = {h: h.strip().lower().replace(" ", "_") for h in header}
    for hint in hints:
        for h in header:
            if h in taken:
                continue
            if low[h] == hint:
                return h
    for hint in hints:
        for h in header:
            if h in taken:
                continue
            if hint in low[h]:
                return h
    return ""


def looks_numeric(values, thresh=0.6):
    vals = [v for v in values if not is_blank(v)]
    if not vals:
        return False
    ok = sum(1 for v in vals if fnum(v) is not None)
    return ok / len(vals) >= thresh


def classify_type(raw):
    """Map an arbitrary sample-type code to one of SAMPLE_TYPES. Best guess."""
    s = str(raw or "").strip().lower()
    if not s:
        return T_NORMAL
    for t in (T_UMP, T_PDUP, T_CDUP, T_FDUP, T_BLANK, T_CRM, T_NORMAL):
        for hint in TYPE_HINTS[t]:
            if s == hint:
                return t
    for t in (T_UMP, T_PDUP, T_CDUP, T_FDUP, T_BLANK, T_CRM):
        for hint in TYPE_HINTS[t]:
            if hint in s:
                return t
    return T_NORMAL


def pctile(sorted_vals, p):
    """Linear-interpolated percentile of an already sorted list."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def stdev(vals, ddof=1):
    vals = [v for v in vals if v is not None]
    if len(vals) <= ddof:
        return None
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - ddof))


def linreg(xs, ys):
    """Ordinary least squares. Returns (intercept, slope, r)."""
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pts)
    if n < 2:
        return None, None, None
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    if sxx == 0:
        return None, None, None
    b = sxy / sxx
    a = my - b * mx
    r = sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else None
    return a, b, r


# --- significance tests (no third-party statistics library) -----------------
def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 3.0e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betainc(a, b, x):
    """Regularised incomplete beta function."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lb = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
          + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(lb)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_two_tail_p(t, df):
    """Two-tailed p-value of Student's t."""
    if df <= 0:
        return None
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def norm_two_tail_p(z):
    return math.erfc(abs(z) / math.sqrt(2.0))


def paired_t(diffs):
    """Paired t-test on a list of differences. Returns (t, df, p, mean, sem)."""
    d = [x for x in diffs if x is not None]
    n = len(d)
    if n < 2:
        return None
    m = sum(d) / n
    sd = stdev(d)
    if not sd:
        return None
    sem = sd / math.sqrt(n)
    if sem == 0:
        return None
    t = m / sem
    return {"t": t, "df": n - 1, "p": t_two_tail_p(t, n - 1),
            "mean": m, "sem": sem, "n": n}


def wilcoxon(diffs):
    """Wilcoxon signed-rank test, normal approximation with tie correction."""
    d = [x for x in diffs if x is not None and x != 0]
    n = len(d)
    if n < 6:
        return None
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    ties = []
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        if j > i:
            ties.append(j - i + 1)
        i = j + 1
    wp = sum(r for r, x in zip(ranks, d) if x > 0)
    mu = n * (n + 1) / 4.0
    var = n * (n + 1) * (2 * n + 1) / 24.0
    var -= sum(t ** 3 - t for t in ties) / 48.0
    if var <= 0:
        return None
    z = (wp - mu) / math.sqrt(var)
    return {"W": wp, "z": z, "p": norm_two_tail_p(z), "n": n}


def rma(xs, ys):
    """Reduced major axis regression -- the correct fit when BOTH axes carry
    error, which is always the case for a duplicate pair. Returns (a, b)."""
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pts)
    if n < 2:
        return None, None
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sx = math.sqrt(sum((p[0] - mx) ** 2 for p in pts) / (n - 1))
    sy = math.sqrt(sum((p[1] - my) ** 2 for p in pts) / (n - 1))
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    if sx == 0 or sy == 0:
        return None, None
    b = (sy / sx) * (1 if sxy >= 0 else -1)
    return my - b * mx, b


# ===========================================================================
#  Editable formula engine
# ===========================================================================
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd,
    ast.Call, ast.IfExp, ast.Compare, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Eq, ast.NotEq, ast.BoolOp, ast.And, ast.Or, ast.Tuple,
)

_FUNCS = {
    "abs": abs, "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "exp": math.exp, "min": min, "max": max, "round": round,
    "floor": math.floor, "ceil": math.ceil, "pow": pow,
    "pi": math.pi, "e": math.e,
}


class FormulaError(Exception):
    pass


def compile_formula(expr):
    """Parse and validate an expression. Raises FormulaError on anything unsafe."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as ex:
        raise FormulaError(f"syntax error: {ex.msg}")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise FormulaError(f"'{type(node).__name__}' is not allowed in a formula")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
                raise FormulaError("only abs, sqrt, log, log10, exp, min, max, "
                                   "round, floor, ceil and pow may be called")
    return compile(tree, "<formula>", "eval")


def eval_formula(code, variables):
    env = dict(_FUNCS)
    env.update(variables)
    try:
        return eval(code, {"__builtins__": {}}, env)     # noqa: S307 - validated above
    except ZeroDivisionError:
        return None
    except (ValueError, OverflowError):
        return None
    except NameError as ex:
        raise FormulaError(str(ex))


class FormulaBook:
    """All editable expressions, with their variables and documentation."""

    def __init__(self, defs):
        self.defs = {k: dict(v) for k, v in defs.items()}
        self._cache = {}

    def expr(self, key):
        return self.defs[key]["expr"]

    def set_expr(self, key, expr):
        compile_formula(expr)                 # validate before accepting
        self.defs[key]["expr"] = expr
        self._cache.pop(key, None)

    def code(self, key):
        if key not in self._cache:
            self._cache[key] = compile_formula(self.defs[key]["expr"])
        return self._cache[key]

    def calc(self, key, **variables):
        try:
            return eval_formula(self.code(key), variables)
        except FormulaError:
            return None

    def to_state(self):
        return {k: v["expr"] for k, v in self.defs.items()}

    def from_state(self, state):
        for k, expr in (state or {}).items():
            if k in self.defs:
                try:
                    self.set_expr(k, expr)
                except FormulaError:
                    pass


# --- the standard formula set ----------------------------------------------
# group, label, expression, variables, reference / note
DEFAULT_FORMULAS = {
    # ---- CRM ----
    "crm_bias": {
        "group": "CRM", "label": "Bias %", "expr": "(meas - cert) / cert * 100",
        "vars": "meas = measured value, cert = certified value",
        "note": "Signed relative deviation of a single CRM result from its "
                "certified value. The primary accuracy statistic."},
    "crm_recovery": {
        "group": "CRM", "label": "Recovery %", "expr": "meas / cert * 100",
        "vars": "meas, cert",
        "note": "Same information expressed as recovery; 100% is perfect."},
    "crm_z": {
        "group": "CRM", "label": "Z-score", "expr": "(meas - cert) / sd",
        "vars": "meas, cert, sd = certified 1 standard deviation",
        "note": "Deviation in units of the certified standard deviation. "
                "The control-chart limits are drawn at z = +/-2 and +/-3."},
    "crm_ucl": {
        "group": "CRM", "label": "Upper control limit", "expr": "cert + k * sd",
        "vars": "cert, sd, k = number of standard deviations",
        "note": "Shewhart upper limit. k = 2 warning, k = 3 action."},
    "crm_lcl": {
        "group": "CRM", "label": "Lower control limit", "expr": "cert - k * sd",
        "vars": "cert, sd, k", "note": "Shewhart lower limit."},
    "crm_pooled_sd_pct": {
        "group": "CRM", "label": "Observed RSD %", "expr": "obs_sd / obs_mean * 100",
        "vars": "obs_sd = standard deviation of the measured results, "
                "obs_mean = mean of the measured results",
        "note": "Observed relative standard deviation of the laboratory for this "
                "CRM. Compare against the certified SD to judge whether the lab "
                "is performing within the tolerance the CRM was certified to."},

    # ---- Blanks ----
    "blank_limit": {
        "group": "BLANK", "label": "Contamination limit", "expr": "k_dl * dl",
        "vars": "dl = detection limit, k_dl = multiplier",
        "note": "A blank is failed above this value. The usual convention is "
                "5 x DL for a strict protocol and 10 x DL for a tolerant one."},
    "blank_ratio": {
        "group": "BLANK", "label": "Blank / DL", "expr": "meas / dl",
        "vars": "meas, dl",
        "note": "Blank result expressed in detection-limit units."},
    "blank_carry": {
        "group": "BLANK", "label": "Carry-over %", "expr": "meas / prev * 100",
        "vars": "meas = blank result, prev = result of the preceding sample",
        "note": "Contamination of a blank expressed as a percentage of the "
                "sample that ran immediately before it. A high value with a "
                "high-grade predecessor is direct evidence of carry-over."},

    # ---- Duplicates ----
    "dup_mean": {
        "group": "DUPLICATE", "label": "Pair mean", "expr": "(a + b) / 2",
        "vars": "a = original result, b = duplicate result",
        "note": "Best estimate of the true value of the pair; the x-axis of "
                "every precision plot."},
    "dup_diff": {
        "group": "DUPLICATE", "label": "Absolute difference", "expr": "abs(a - b)",
        "vars": "a, b", "note": "Used by the Thompson-Howarth regression."},
    "dup_rd": {
        "group": "DUPLICATE", "label": "RD %  (relative difference)",
        "expr": "(a - b) / ((a + b) / 2) * 100", "vars": "a, b",
        "note": "Signed relative difference. Its mean over many pairs detects "
                "systematic bias between original and duplicate."},
    "dup_ard": {
        "group": "DUPLICATE", "label": "ARD %  (absolute relative difference)",
        "expr": "abs(a - b) / ((a + b) / 2) * 100", "vars": "a, b",
        "note": "Unsigned relative difference; the plain measure of scatter."},
    "dup_hard": {
        "group": "DUPLICATE", "label": "HARD %  (half absolute relative difference)",
        "expr": "abs(a - b) / (a + b) * 100", "vars": "a, b",
        "note": "Exactly ARD/2. The industry standard precision statistic, "
                "because acceptance is normally quoted as the 90th percentile "
                "of HARD. Reported by almost every QP report."},
    "dup_hrd": {
        "group": "DUPLICATE", "label": "HRD %  (half relative difference, signed)",
        "expr": "(a - b) / (a + b) * 100", "vars": "a, b",
        "note": "Signed form of HARD. Plot against pair mean to see whether "
                "the scatter is symmetric or one-sided."},
    "dup_cv": {
        "group": "DUPLICATE", "label": "Pair CV %",
        "expr": "abs(a - b) / (sqrt(2) * ((a + b) / 2)) * 100", "vars": "a, b",
        "note": "Coefficient of variation of a duplicate pair. For two "
                "measurements the standard deviation estimate is |a-b|/sqrt(2), "
                "so CV = ARD / sqrt(2)."},
    "dup_precision95": {
        "group": "DUPLICATE", "label": "Relative precision at 95 %",
        "expr": "2 * cv", "vars": "cv = pair CV %",
        "note": "Two standard deviations, i.e. the interval that should contain "
                "95% of repeat determinations."},
    "dup_pooled_rel_var": {
        "group": "DUPLICATE", "label": "Pooled relative variance term",
        "expr": "((a - b) / (a + b)) ** 2", "vars": "a, b",
        "note": "Summed over all pairs and used for the pooled relative "
                "precision:  RP% = 2 * sqrt( 2 * sum(term) / n ) * 100."},
    "dup_pooled_rp": {
        "group": "DUPLICATE", "label": "Pooled relative precision %",
        "expr": "2 * sqrt(2 * s_terms / n) * 100",
        "vars": "s_terms = sum of the pooled relative variance terms, "
                "n = number of pairs",
        "note": "A single precision number for the whole population of pairs, "
                "independent of grade. Widely reported alongside rank-HARD."},

    # ---- Thompson & Howarth ----
    "th_sigma": {
        "group": "THOMPSON-HOWARTH", "label": "Sigma from mean |difference|",
        "expr": "0.8862 * dbar", "vars": "dbar = mean absolute difference of a bin",
        "note": "For a normal distribution E|d| = sigma_d * sqrt(2/pi) and "
                "sigma_d = sigma * sqrt(2), giving sigma = 0.8862 * E|d|."},
    "th_precision": {
        "group": "THOMPSON-HOWARTH", "label": "Precision % at concentration c",
        "expr": "177.2 * (a_int + b_slope * c) / c",
        "vars": "a_int = regression intercept, b_slope = regression slope, "
                "c = concentration",
        "note": "Precision at 95% confidence from the fitted mean-|difference| "
                "regression. 177.2 = 2 * 0.8862 * 100."},
    "th_pdl": {
        "group": "THOMPSON-HOWARTH", "label": "Practical detection limit",
        "expr": "3 * 0.8862 * a_int", "vars": "a_int = regression intercept",
        "note": "Three sigma at zero concentration -- the concentration below "
                "which the method cannot separate a result from nothing."},

    # ---- Check / umpire assays ----
    "ump_bias": {
        "group": "CHECK / UMPIRE", "label": "Pair relative bias %",
        "expr": "(u - pr) / ((u + pr) / 2) * 100",
        "vars": "pr = primary laboratory result, u = umpire laboratory result",
        "note": "Signed relative difference between the two laboratories for one "
                "sample. Averaged over all pairs it is the unweighted bias -- "
                "every sample counts the same, so low-grade samples dominate it."},
    "ump_weighted_bias": {
        "group": "CHECK / UMPIRE", "label": "Grade-weighted bias %",
        "expr": "(sum_u - sum_pr) / sum_pr * 100",
        "vars": "sum_pr = sum of the primary results, sum_u = sum of the umpire "
                "results",
        "note": "The ratio of the two totals. THIS is the statistic that matters "
                "for a resource: it weights every sample by its grade, so it "
                "answers 'would the contained metal change if the umpire lab "
                "were right'. Always report it beside the unweighted bias."},
    "ump_ratio": {
        "group": "CHECK / UMPIRE", "label": "Umpire / primary ratio",
        "expr": "u / pr", "vars": "pr, u",
        "note": "Ratio for one pair. Its median is a robust alternative to the "
                "mean bias when a few pairs are wild."},
    "ump_hard": {
        "group": "CHECK / UMPIRE", "label": "Inter-laboratory HARD %",
        "expr": "abs(u - pr) / (u + pr) * 100", "vars": "pr, u",
        "note": "Scatter between the two laboratories. Secondary here: a check "
                "programme is run to detect BIAS, and scatter can be large while "
                "bias is nil, or tiny while bias is severe."},

    # ---- Insertion ----
    "insert_rate": {
        "group": "INSERTION", "label": "Insertion rate %",
        "expr": "n_control / n_total * 100",
        "vars": "n_control = number of control samples of this class, "
                "n_total = total number of samples submitted",
        "note": "The long-standing convention is 5% of each control class, "
                "i.e. one in twenty, giving roughly 15-20% total QA/QC load."},
    "insert_interval": {
        "group": "INSERTION", "label": "One control in every N samples",
        "expr": "n_total / n_control", "vars": "n_control, n_total",
        "note": "The same figure expressed the way a sampler works in practice."},
}


# ===========================================================================
#  Editable acceptance criteria
# ===========================================================================
# cuts are the five boundaries producing the six classes.
# direction 'low'  -> smaller is better (bias, failure rate, HARD ...)
# direction 'high' -> larger is better (correlation, insertion rate ...)
DEFAULT_CRITERIA = {
    "crm_bias": {
        "group": "CRM", "label": "Mean absolute bias %", "unit": "%",
        "cuts": [2.0, 3.0, 5.0, 7.0, 10.0], "dir": "low",
        "note": "Accuracy of the laboratory against the certified value. "
                "Most QP reports treat a mean bias beyond 5% as requiring "
                "investigation and beyond 10% as grounds for re-assay."},
    "crm_fail": {
        "group": "CRM", "label": "Failure rate beyond 3 SD %", "unit": "%",
        "cuts": [1.0, 2.0, 5.0, 10.0, 20.0], "dir": "low",
        "note": "For a controlled process only about 0.3% of results should "
                "fall beyond 3 SD. A rate above 5% means the batch is out of "
                "control and the affected batches should be re-assayed."},
    "crm_warn": {
        "group": "CRM", "label": "Warning rate beyond 2 SD %", "unit": "%",
        "cuts": [5.0, 8.0, 12.0, 20.0, 30.0], "dir": "low",
        "note": "About 5% of results are expected beyond 2 SD by chance alone, "
                "so this criterion is deliberately more tolerant than the 3 SD "
                "one."},
    "crm_rsd": {
        "group": "CRM", "label": "Observed RSD %", "unit": "%",
        "cuts": [2.0, 3.0, 5.0, 8.0, 12.0], "dir": "low",
        "note": "Repeatability of the laboratory on a homogeneous material. "
                "Should be comparable with the certified standard deviation."},

    "blank_fail": {
        "group": "BLANK", "label": "Blank failure rate %", "unit": "%",
        "cuts": [1.0, 2.0, 5.0, 10.0, 20.0], "dir": "low",
        "note": "Proportion of blanks above the contamination limit. "
                "Occasional single failures are tolerable; a rate above 5% "
                "indicates systematic contamination in preparation."},
    "blank_max": {
        "group": "BLANK", "label": "Maximum blank / DL", "unit": "x DL",
        "cuts": [2.0, 3.0, 5.0, 10.0, 20.0], "dir": "low",
        "note": "Worst single blank expressed in detection-limit units. "
                "Catches the case of a low failure rate hiding one gross event."},

    "fdup_hard90": {
        "group": "FIELD DUP", "label": "90th percentile HARD %", "unit": "%",
        "cuts": [10.0, 15.0, 20.0, 30.0, 40.0], "dir": "low",
        "note": "Field duplicates carry the full sampling variance, so the "
                "accepted tolerance is the widest of the three. The common "
                "industry pass mark is 90% of pairs within 20-30% HARD."},
    "cdup_hard90": {
        "group": "COARSE DUP", "label": "90th percentile HARD %", "unit": "%",
        "cuts": [5.0, 10.0, 15.0, 20.0, 25.0], "dir": "low",
        "note": "Coarse (crushed reject) duplicates test the sub-sampling of "
                "the crushed material. The usual pass mark is 90% within "
                "10-20% HARD."},
    "pdup_hard90": {
        "group": "PULP DUP", "label": "90th percentile HARD %", "unit": "%",
        "cuts": [3.0, 5.0, 7.5, 10.0, 15.0], "dir": "low",
        "note": "Pulp duplicates isolate analytical precision alone, so the "
                "tolerance is the tightest. The usual pass mark is 90% within "
                "5-10% HARD."},
    "dup_bias": {
        "group": "DUPLICATE", "label": "Mean RD % (original vs duplicate)", "unit": "%",
        "cuts": [1.0, 2.0, 5.0, 8.0, 12.0], "dir": "low",
        "note": "The mean SIGNED relative difference should be near zero. A "
                "persistent sign means the duplicate is systematically richer "
                "or poorer, which points at the splitting stage, not precision."},
    "dup_r": {
        "group": "DUPLICATE", "label": "Correlation coefficient", "unit": "",
        "cuts": [0.99, 0.98, 0.95, 0.90, 0.80], "dir": "high",
        "note": "Correlation between original and duplicate. Weak on its own "
                "because it is dominated by grade range, so it is reported "
                "beside HARD rather than instead of it."},
    "dup_rma_slope": {
        "group": "DUPLICATE", "label": "|RMA slope - 1|", "unit": "",
        "cuts": [0.02, 0.05, 0.10, 0.15, 0.25], "dir": "low",
        "note": "Reduced major axis slope should be 1. A departure means a "
                "proportional bias that grows with grade."},

    "th_precision": {
        "group": "PRECISION", "label": "Thompson-Howarth precision % at 10 x DL",
        "unit": "%", "cuts": [5.0, 10.0, 15.0, 20.0, 30.0], "dir": "low",
        "note": "Precision at 95% confidence read from the fitted curve at ten "
                "times the detection limit, which is the lowest concentration "
                "at which most projects need reliable numbers."},

    "ump_wbias": {
        "group": "CHECK / UMPIRE", "label": "Absolute grade-weighted bias %",
        "unit": "%", "cuts": [2.0, 3.0, 5.0, 7.0, 10.0], "dir": "low",
        "note": "Difference between the two laboratories on a metal-weighted "
                "basis. Beyond about 5% the choice of laboratory would visibly "
                "move the resource, and the cause must be found before the "
                "primary data can be used for estimation."},
    "ump_pbias": {
        "group": "CHECK / UMPIRE", "label": "Absolute mean pair bias %",
        "unit": "%", "cuts": [2.0, 3.0, 5.0, 8.0, 12.0], "dir": "low",
        "note": "Unweighted mean of the per-pair relative bias. A large gap "
                "between this and the grade-weighted figure means the bias is "
                "grade-dependent."},
    "ump_hard90": {
        "group": "CHECK / UMPIRE", "label": "90th percentile inter-lab HARD %",
        "unit": "%", "cuts": [5.0, 10.0, 15.0, 20.0, 30.0], "dir": "low",
        "note": "Scatter between laboratories. Expected to be wider than pulp "
                "duplicates within one laboratory, because two different "
                "methods and instruments are involved."},
    "ump_grade_range": {
        "group": "CHECK / UMPIRE", "label": "Worst grade-quartile bias %",
        "unit": "%", "cuts": [3.0, 5.0, 8.0, 12.0, 18.0], "dir": "low",
        "note": "Largest absolute bias among the four grade quartiles. A bias "
                "that appears only at high grade is far more damaging to a "
                "resource than the same average bias spread evenly, and an "
                "overall mean hides it completely."},

    "insert_rate": {
        "group": "INSERTION", "label": "Insertion rate %", "unit": "%",
        "cuts": [5.0, 4.0, 3.0, 2.0, 1.0], "dir": "high",
        "note": "The 5% per control class convention, i.e. one in twenty. "
                "Below 2% the control population is too small to support any "
                "statistical statement about the data."},
}

DEFAULT_SETTINGS = {
    "k_warn": 2.0,              # control-chart warning limit, in SD
    "k_fail": 3.0,              # control-chart action limit, in SD
    "k_dl": 5.0,                # blank contamination limit, multiples of DL
    "hard_pct": 90.0,           # percentile used for the rank-HARD criterion
    "th_group": 11,             # pairs per Thompson-Howarth bin
    "th_at_dl": 10.0,           # report TH precision at this multiple of DL
    "min_pairs": 8,             # below this a duplicate set is not rated
    "min_crm": 5,               # below this a CRM set is not rated
    "run_len": 10,              # consecutive same-side results = bias run
    "drop_below_dl": True,      # exclude pairs where either value is below DL
    "dl_substitute": 0.5,       # if kept, replace <DL by this fraction of DL
    "log_axis": True,           # duplicate scatter on log-log axes
}


# ===========================================================================
#  Rating engine
# ===========================================================================
def rate(value, crit):
    """Map a measured value onto the six-class scale using an editable band."""
    if value is None:
        return R_NA
    cuts = crit["cuts"]
    if crit["dir"] == "low":
        for cut, name in zip(cuts, RATING_ORDER[:5]):
            if value <= cut:
                return name
        return R_VBAD
    for cut, name in zip(cuts, RATING_ORDER[:5]):
        if value >= cut:
            return name
    return R_VBAD


def combine_ratings(ratings, weights=None):
    """Weighted mean of rating scores -> a single overall rating."""
    items = [r for r in ratings if r and r != R_NA]
    if not items:
        return R_NA, None
    if weights is None:
        weights = [1.0] * len(items)
    weights = weights[:len(items)] + [1.0] * max(0, len(items) - len(weights))
    total = sum(weights)
    score = sum(RATING_SCORE[r] * w for r, w in zip(items, weights)) / total
    for name in RATING_ORDER:
        if score >= RATING_SCORE[name] - 7.5:
            return name, score
    return R_VBAD, score


# ===========================================================================
#  Data model
# ===========================================================================
class DataTable:
    """One imported table."""

    def __init__(self, kind, name, path, header, rows, delim=","):
        self.kind = kind            # 'assay' | 'crm' | 'pairs'
        self.name = name
        self.path = path
        self.header = header
        self.rows = rows
        self.delim = delim
        self.mapping = {}
        self.value_cols = []        # assay only: [(element, 'numeric')]
        self.type_map = {}          # assay only: raw code -> SAMPLE_TYPES
        self.dl = {}                # element -> detection limit

    def idx(self, role):
        col = self.mapping.get(role)
        if not col or col not in self.header:
            return None
        return self.header.index(col)

    def get(self, row, role):
        i = self.idx(role)
        return row[i] if i is not None and i < len(row) else None

    def col(self, row, name):
        if name not in self.header:
            return None
        i = self.header.index(name)
        return row[i] if i < len(row) else None

    def col_values(self, colname):
        if colname not in self.header:
            return []
        i = self.header.index(colname)
        return [r[i] if i < len(r) else "" for r in self.rows]

    def to_state(self):
        return {"kind": self.kind, "name": self.name, "path": self.path,
                "mapping": self.mapping, "value_cols": self.value_cols,
                "type_map": self.type_map, "dl": self.dl}


class Sample:
    __slots__ = ("sid", "stype", "raw_type", "crmid", "parent", "batch", "lab",
                 "date", "order", "vals", "flags", "row_n", "loc",
                 "hole", "drilltype")

    def __init__(self, sid, row_n):
        self.sid = sid
        self.row_n = row_n
        self.stype = T_NORMAL
        self.raw_type = ""
        self.crmid = ""
        self.parent = ""
        self.batch = ""
        self.lab = ""
        self.date = ""
        self.order = None
        self.vals = {}              # element -> float or None
        self.flags = {}             # element -> '<' / '>' / ''
        self.loc = ""
        self.hole = ""              # hole / trench / station -- optional
        self.drilltype = ""         # DD / RC / AC / channel ... -- optional

    def group(self, key):
        """Value of a grouping dimension, '' when the column was not mapped."""
        return getattr(self, key, "") if key else ""


class Project:
    def __init__(self):
        self.assay = None
        self.crm = None             # certificate table
        self.pairs = None           # explicit duplicate pair table
        self.umpire = None          # second-laboratory results
        self.samples = []
        self.elements = []
        self.certs = {}             # (crmid, element) -> {'cert':, 'sd':, 'unit':}
        self.results = {}           # analysis output
        self.analysed_at = None
        self.orphan_dups = []       # duplicates whose parent could not be found

    def tables(self):
        return [t for t in (self.assay, self.crm, self.pairs, self.umpire) if t]

    def clear_results(self):
        self.results = {}
        self.analysed_at = None


# ===========================================================================
#  Build the sample population from the imported tables
# ===========================================================================
def build_samples(project, S, log=print):
    t = project.assay
    if t is None:
        raise ValueError("An assay table must be imported before analysing.")

    elements = [c for c, k in t.value_cols if k == "numeric"]
    if not elements:
        raise ValueError("No element column has been flagged as numeric.")

    samples = []
    for n, r in enumerate(t.rows, start=2):
        sid = str(t.get(r, "sampleid") or "").strip()
        if not sid:
            continue
        s = Sample(sid, n)
        raw = t.get(r, "type")
        s.raw_type = str(raw or "").strip()
        s.stype = t.type_map.get(s.raw_type) or classify_type(s.raw_type)
        s.crmid = str(t.get(r, "crmid") or "").strip()
        s.parent = str(t.get(r, "parent") or "").strip()
        s.batch = str(t.get(r, "batch") or "").strip()
        s.lab = str(t.get(r, "lab") or "").strip()
        s.date = str(t.get(r, "date") or "").strip()
        s.order = fnum(t.get(r, "order"))
        hid = str(t.get(r, "holeid") or "").strip()
        fr, to = t.get(r, "from"), t.get(r, "to")
        s.hole = hid
        s.drilltype = str(t.get(r, "drilltype") or "").strip()
        if hid:
            s.loc = f"{hid} {fr or ''}-{to or ''}".strip()
        # a CRM whose code lives in the type column rather than its own column
        if s.stype == T_CRM and not s.crmid and s.raw_type:
            s.crmid = s.raw_type
        for e in elements:
            raw_v = t.col(r, e)
            s.vals[e] = fnum(raw_v)
            s.flags[e] = dl_flag(raw_v)
        samples.append(s)

    # sequence: explicit order column, else file order
    if all(s.order is None for s in samples):
        for i, s in enumerate(samples, start=1):
            s.order = float(i)

    project.samples = samples
    project.elements = elements

    # certificates
    certs = {}
    ct = project.crm
    if ct is not None:
        for r in ct.rows:
            cid = str(ct.get(r, "crmid") or "").strip()
            el = str(ct.get(r, "element") or "").strip()
            cv = fnum(ct.get(r, "certified"))
            sd = fnum(ct.get(r, "sd"))
            if not cid or not el or cv is None:
                continue
            certs[(cid.upper(), el.upper())] = {
                "cert": cv, "sd": sd,
                "unit": str(ct.get(r, "unit") or "").strip(),
                "method": str(ct.get(r, "method") or "").strip()}
    project.certs = certs

    counts = {}
    for s in samples:
        counts[s.stype] = counts.get(s.stype, 0) + 1
    log(f"{len(samples)} samples, {len(elements)} element(s). "
        + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if certs:
        log(f"{len(certs)} certificate entries for "
            f"{len({k[0] for k in certs})} CRM code(s).")
    return samples


def detection_limit(project, element, S):
    """Detection limit for an element: the declared value if the user gave one,
    otherwise inferred from the smallest '<' value, otherwise the smallest
    positive result in the dataset."""
    t = project.assay
    if t is not None and t.dl.get(element) is not None:
        return t.dl[element]
    below = [s.vals[element] for s in project.samples
             if s.flags.get(element) == "<" and s.vals.get(element) is not None]
    if below:
        return max(below)
    pos = [s.vals[element] for s in project.samples
           if s.vals.get(element) is not None and s.vals[element] > 0]
    return min(pos) if pos else None


# ===========================================================================
#  CRM analysis
# ===========================================================================
def analyse_crm(project, F, C, S, log=print):
    """Per (CRM code, element): control-chart series, statistics, rating."""
    out = {}
    crm_samples = [s for s in project.samples if s.stype == T_CRM]
    if not crm_samples:
        return out

    codes = sorted({s.crmid.upper() for s in crm_samples if s.crmid})
    if not codes:
        log("  ! CRM samples found but no CRM code column was mapped.")
        return out

    for code in codes:
        subset = [s for s in crm_samples if s.crmid.upper() == code]
        subset.sort(key=lambda s: (s.order if s.order is not None else 0))
        for el in project.elements:
            cert = project.certs.get((code, el.upper()))
            series = [(s, s.vals.get(el)) for s in subset if s.vals.get(el) is not None]
            if not series:
                continue
            meas = [v for _, v in series]
            obs_mean = mean(meas)
            obs_sd = stdev(meas)
            key = (code, el)

            rec = {"crm": code, "element": el, "n": len(series),
                   "obs_mean": obs_mean, "obs_sd": obs_sd,
                   "cert": None, "sd": None, "unit": "",
                   "points": [], "failures": [], "rules": [],
                   "bias": None, "fail_pct": None, "warn_pct": None,
                   "rsd_pct": None, "ratings": {}, "rating": R_NA, "score": None}

            if cert is None:
                rec["note"] = ("No certificate found for this CRM/element pair. "
                               "Import a certificate table to enable accuracy "
                               "statistics; only repeatability is reported.")
                rec["rsd_pct"] = F.calc("crm_pooled_sd_pct",
                                        obs_sd=obs_sd or 0.0, obs_mean=obs_mean or 1.0)
                rec["ratings"]["crm_rsd"] = rate(rec["rsd_pct"], C["crm_rsd"])
                rec["rating"], rec["score"] = combine_ratings(
                    [rec["ratings"]["crm_rsd"]])
                out[key] = rec
                continue

            cv, sd = cert["cert"], cert["sd"]
            rec["cert"], rec["sd"], rec["unit"] = cv, sd, cert.get("unit", "")

            # if the certificate carries no SD, fall back on the observed spread
            eff_sd = sd if sd else obs_sd
            rec["eff_sd"] = eff_sd
            rec["sd_source"] = "certified" if sd else "observed"

            biases, zs = [], []
            for s, v in series:
                bias = F.calc("crm_bias", meas=v, cert=cv)
                z = F.calc("crm_z", meas=v, cert=cv, sd=eff_sd) if eff_sd else None
                biases.append(bias)
                zs.append(z)
                rec["points"].append({
                    "sample": s.sid, "order": s.order, "batch": s.batch,
                    "date": s.date, "value": v, "bias": bias, "z": z,
                    "row": s.row_n})

            rec["bias"] = mean([b for b in biases if b is not None])
            rec["abs_bias"] = abs(rec["bias"]) if rec["bias"] is not None else None
            rec["rsd_pct"] = F.calc("crm_pooled_sd_pct",
                                    obs_sd=obs_sd or 0.0, obs_mean=obs_mean or 1.0)
            zz = [z for z in zs if z is not None]
            if zz:
                rec["fail_pct"] = 100.0 * sum(1 for z in zz
                                              if abs(z) > S["k_fail"]) / len(zz)
                rec["warn_pct"] = 100.0 * sum(1 for z in zz
                                              if abs(z) > S["k_warn"]) / len(zz)

            # ---- Westgard-style rule violations ----
            rules = []
            for i, z in enumerate(zs):
                if z is None:
                    continue
                p = rec["points"][i]
                if abs(z) > S["k_fail"]:
                    rules.append({"rule": "1-3s", "sample": p["sample"],
                                  "z": z, "sev": SEV_ERROR,
                                  "desc": f"single result beyond {S['k_fail']:g} SD"})
                if i >= 1 and zs[i - 1] is not None:
                    if (z > S["k_warn"] and zs[i - 1] > S["k_warn"]) or \
                       (z < -S["k_warn"] and zs[i - 1] < -S["k_warn"]):
                        rules.append({"rule": "2-2s", "sample": p["sample"], "z": z,
                                      "sev": SEV_ERROR,
                                      "desc": "two consecutive results beyond "
                                              f"{S['k_warn']:g} SD on the same side"})
                if i >= 3 and all(zs[j] is not None for j in range(i - 3, i + 1)):
                    w = zs[i - 3:i + 1]
                    if all(x > 1 for x in w) or all(x < -1 for x in w):
                        rules.append({"rule": "4-1s", "sample": p["sample"], "z": z,
                                      "sev": SEV_WARN,
                                      "desc": "four consecutive results beyond "
                                              "1 SD on the same side"})
                if i >= 1 and zs[i - 1] is not None and abs(z - zs[i - 1]) > 4:
                    rules.append({"rule": "R-4s", "sample": p["sample"], "z": z,
                                  "sev": SEV_WARN,
                                  "desc": "range between two consecutive results "
                                          "exceeds 4 SD"})
            n_run = int(S["run_len"])
            side = 0
            run = 0
            for i, z in enumerate(zs):
                if z is None:
                    side, run = 0, 0
                    continue
                s_now = 1 if z > 0 else -1
                run = run + 1 if s_now == side else 1
                side = s_now
                if run == n_run:
                    rules.append({"rule": f"{n_run}x", "sample": rec["points"][i]["sample"],
                                  "z": z, "sev": SEV_WARN,
                                  "desc": f"{n_run} consecutive results on the same "
                                          "side of the certified value -- a bias, "
                                          "not random scatter"})
            rec["rules"] = rules
            rec["failures"] = [p for p, z in zip(rec["points"], zs)
                               if z is not None and abs(z) > S["k_fail"]]

            if len(series) >= S["min_crm"]:
                rec["ratings"]["crm_bias"] = rate(rec["abs_bias"], C["crm_bias"])
                rec["ratings"]["crm_fail"] = rate(rec["fail_pct"], C["crm_fail"])
                rec["ratings"]["crm_warn"] = rate(rec["warn_pct"], C["crm_warn"])
                rec["ratings"]["crm_rsd"] = rate(rec["rsd_pct"], C["crm_rsd"])
                rec["rating"], rec["score"] = combine_ratings(
                    [rec["ratings"]["crm_bias"], rec["ratings"]["crm_fail"],
                     rec["ratings"]["crm_warn"], rec["ratings"]["crm_rsd"]],
                    [3.0, 3.0, 1.0, 1.5])
            else:
                rec["note"] = (f"Only {len(series)} results. Below the minimum of "
                               f"{S['min_crm']} the statistics are not stable "
                               f"enough to carry a rating.")
            out[key] = rec
    return out


# ===========================================================================
#  Blank analysis
# ===========================================================================
def analyse_blank(project, F, C, S, log=print):
    out = {}
    blanks = [s for s in project.samples if s.stype == T_BLANK]
    if not blanks:
        return out
    order_index = {id(s): i for i, s in enumerate(project.samples)}

    for el in project.elements:
        dl = detection_limit(project, el, S)
        if dl is None or dl <= 0:
            continue
        limit = F.calc("blank_limit", dl=dl, k_dl=S["k_dl"])
        pts, fails = [], 0
        for s in blanks:
            v = s.vals.get(el)
            if v is None:
                continue
            ratio = F.calc("blank_ratio", meas=v, dl=dl)
            i = order_index[id(s)]
            prev = project.samples[i - 1] if i > 0 else None
            prev_v = prev.vals.get(el) if prev else None
            carry = (F.calc("blank_carry", meas=v, prev=prev_v)
                     if prev_v not in (None, 0) else None)
            bad = limit is not None and v > limit
            if bad:
                fails += 1
            pts.append({"sample": s.sid, "order": s.order, "batch": s.batch,
                        "value": v, "ratio": ratio, "limit": limit,
                        "prev_sample": prev.sid if prev else "",
                        "prev_value": prev_v, "carry_pct": carry,
                        "fail": bad, "row": s.row_n})
        if not pts:
            continue
        vals = [p["value"] for p in pts]
        rec = {"element": el, "n": len(pts), "dl": dl, "limit": limit,
               "points": pts, "n_fail": fails,
               "fail_pct": 100.0 * fails / len(pts),
               "max": max(vals), "mean": mean(vals),
               "max_ratio": max(p["ratio"] for p in pts if p["ratio"] is not None),
               "ratings": {}, "rating": R_NA, "score": None}
        rec["ratings"]["blank_fail"] = rate(rec["fail_pct"], C["blank_fail"])
        rec["ratings"]["blank_max"] = rate(rec["max_ratio"], C["blank_max"])
        rec["rating"], rec["score"] = combine_ratings(
            [rec["ratings"]["blank_fail"], rec["ratings"]["blank_max"]], [3.0, 1.0])
        # carry-over evidence
        rec["carry"] = [p for p in pts
                        if p["fail"] and p["carry_pct"] is not None
                        and p["prev_value"] is not None
                        and p["prev_value"] > 10 * dl]
        out[el] = rec
    return out


# ===========================================================================
#  Duplicate pairing and precision
# ===========================================================================
def build_pairs(project, S, log=print):
    """Return {dup_type: [(orig_sample, dup_sample), ...]}."""
    by_id = {}
    for s in project.samples:
        by_id.setdefault(s.sid.strip().upper(), s)
    pairs = {t: [] for t in DUP_TYPES}
    used = set()

    # 1) explicit pair table
    pt = project.pairs
    if pt is not None:
        for r in pt.rows:
            o = str(pt.get(r, "sampleid") or "").strip().upper()
            d = str(pt.get(r, "dupid") or "").strip().upper()
            if not o or not d:
                continue
            so, sd_ = by_id.get(o), by_id.get(d)
            if not so or not sd_:
                continue
            raw = str(pt.get(r, "type") or "").strip()
            t = pt.type_map.get(raw) or classify_type(raw)
            if t not in DUP_TYPES:
                t = sd_.stype if sd_.stype in DUP_TYPES else T_FDUP
            pairs[t].append((so, sd_))
            used.add((o, d))

    # 2) parent-id column on the duplicate record
    for s in project.samples:
        if s.stype not in DUP_TYPES or not s.parent:
            continue
        o = s.parent.strip().upper()
        key = (o, s.sid.strip().upper())
        if key in used:
            continue
        so = by_id.get(o)
        if so:
            pairs[s.stype].append((so, s))
            used.add(key)

    # Duplicates whose declared parent is not in the table are silently lost
    # otherwise, and a wrong PARENT_ID column is a common spreadsheet error.
    orphans = []
    for smp in project.samples:
        if smp.stype not in DUP_TYPES:
            continue
        if not smp.parent:
            orphans.append((smp.sid, smp.stype, "no parent sample ID recorded"))
        elif smp.parent.strip().upper() not in by_id:
            orphans.append((smp.sid, smp.stype,
                            f"parent '{smp.parent}' is not in the table"))
    project.orphan_dups = orphans

    for t in DUP_TYPES:
        if pairs[t]:
            log(f"  {t}: {len(pairs[t])} pair(s)")
    if orphans:
        n_dup = sum(1 for x in project.samples if x.stype in DUP_TYPES)
        log(f"  ! {len(orphans)} of {n_dup} duplicate row(s) could NOT be paired "
            f"({100.0 * len(orphans) / max(1, n_dup):.0f} %). "
            f"Check the parent-sample column -- see the Log tab for the list.")
        for sid, t, why in orphans[:25]:
            log(f"      {t}  {sid}: {why}")
        if len(orphans) > 25:
            log(f"      ... and {len(orphans) - 25} more")
    return pairs


def analyse_duplicates(project, F, C, S, pairs, log=print):
    out = {}
    crit_key = {T_FDUP: "fdup_hard90", T_CDUP: "cdup_hard90", T_PDUP: "pdup_hard90"}

    for dtype in DUP_TYPES:
        plist = pairs.get(dtype) or []
        if not plist:
            continue
        for el in project.elements:
            dl = detection_limit(project, el, S)
            rows = []
            for so, sd_ in plist:
                a, b = so.vals.get(el), sd_.vals.get(el)
                if a is None or b is None:
                    continue
                below = (so.flags.get(el) == "<" or sd_.flags.get(el) == "<"
                         or (dl and (a < dl or b < dl)))
                if below and S["drop_below_dl"]:
                    continue
                if below and dl:
                    a = dl * S["dl_substitute"] if a < dl else a
                    b = dl * S["dl_substitute"] if b < dl else b
                if a + b <= 0:
                    continue
                m = F.calc("dup_mean", a=a, b=b)
                rows.append({
                    "orig": so.sid, "dup": sd_.sid, "batch": sd_.batch,
                    "hole": so.hole or sd_.hole,
                    "drilltype": so.drilltype or sd_.drilltype,
                    "lab": so.lab or sd_.lab,
                    "a": a, "b": b, "mean": m,
                    "diff": F.calc("dup_diff", a=a, b=b),
                    "rd": F.calc("dup_rd", a=a, b=b),
                    "ard": F.calc("dup_ard", a=a, b=b),
                    "hard": F.calc("dup_hard", a=a, b=b),
                    "hrd": F.calc("dup_hrd", a=a, b=b),
                    "cv": F.calc("dup_cv", a=a, b=b),
                    "term": F.calc("dup_pooled_rel_var", a=a, b=b),
                })
            if not rows:
                continue
            for r in rows:
                r["prec95"] = F.calc("dup_precision95", cv=r["cv"] or 0.0)

            hards = sorted(r["hard"] for r in rows if r["hard"] is not None)
            terms = [r["term"] for r in rows if r["term"] is not None]
            a_int, b_slope, r_corr = linreg([r["a"] for r in rows],
                                            [r["b"] for r in rows])
            rma_a, rma_b = rma([r["a"] for r in rows], [r["b"] for r in rows])

            rec = {"type": dtype, "element": el, "n": len(rows), "rows": rows,
                   "dl": dl,
                   "hard_mean": mean(hards),
                   "hard_median": pctile(hards, 50),
                   "hard_p90": pctile(hards, S["hard_pct"]),
                   "hard_pct_used": S["hard_pct"],
                   "rd_mean": mean([r["rd"] for r in rows]),
                   "ard_mean": mean([r["ard"] for r in rows]),
                   "cv_mean": mean([r["cv"] for r in rows]),
                   "pooled_rp": (F.calc("dup_pooled_rp",
                                        s_terms=sum(terms), n=len(terms))
                                 if terms else None),
                   "r": r_corr, "ols_a": a_int, "ols_b": b_slope,
                   "rma_a": rma_a, "rma_b": rma_b,
                   "ratings": {}, "rating": R_NA, "score": None}

            rec["within"] = {}
            for lim in (5, 10, 15, 20, 30):
                rec["within"][lim] = 100.0 * sum(1 for h in hards if h <= lim) / len(hards)

            if len(rows) >= S["min_pairs"]:
                rec["ratings"][crit_key[dtype]] = rate(rec["hard_p90"],
                                                       C[crit_key[dtype]])
                rec["ratings"]["dup_bias"] = rate(
                    abs(rec["rd_mean"]) if rec["rd_mean"] is not None else None,
                    C["dup_bias"])
                rec["ratings"]["dup_r"] = rate(rec["r"], C["dup_r"])
                rec["ratings"]["dup_rma_slope"] = rate(
                    abs(rma_b - 1.0) if rma_b is not None else None,
                    C["dup_rma_slope"])
                rec["rating"], rec["score"] = combine_ratings(
                    [rec["ratings"][crit_key[dtype]], rec["ratings"]["dup_bias"],
                     rec["ratings"]["dup_r"], rec["ratings"]["dup_rma_slope"]],
                    [4.0, 2.0, 1.0, 1.5])
            else:
                rec["note"] = (f"Only {len(rows)} usable pairs. Below the minimum "
                               f"of {S['min_pairs']} a percentile is meaningless, "
                               f"so no rating is given.")
            out[(dtype, el)] = rec
    return out


# ===========================================================================
#  Grouping -- the same precision statistics computed per hole, batch,
#  drill type or laboratory. This is what turns "the duplicates are poor"
#  into "the duplicates are poor in BH103 and nowhere else".
# ===========================================================================
def dup_stats(rows, F, C, S, crit_key):
    """Recompute the duplicate summary for an arbitrary subset of pairs."""
    rows = [r for r in rows if r.get("hard") is not None]
    if not rows:
        return None
    hards = sorted(r["hard"] for r in rows)
    terms = [r["term"] for r in rows if r.get("term") is not None]
    a_int, b_slope, r_corr = linreg([r["a"] for r in rows], [r["b"] for r in rows])
    rma_a, rma_b = rma([r["a"] for r in rows], [r["b"] for r in rows])
    st = {"n": len(rows),
          "hard_mean": mean(hards),
          "hard_median": pctile(hards, 50),
          "hard_p90": pctile(hards, S["hard_pct"]),
          "hard_pct_used": S["hard_pct"],
          "rd_mean": mean([r["rd"] for r in rows]),
          "ard_mean": mean([r["ard"] for r in rows]),
          "cv_mean": mean([r["cv"] for r in rows]),
          "pooled_rp": (F.calc("dup_pooled_rp", s_terms=sum(terms), n=len(terms))
                        if terms else None),
          "r": r_corr, "rma_a": rma_a, "rma_b": rma_b,
          "within": {}}
    for lim in (5, 10, 15, 20, 30):
        st["within"][lim] = 100.0 * sum(1 for h in hards if h <= lim) / len(hards)
    if len(rows) >= S["min_pairs"]:
        st["rating"] = rate(st["hard_p90"], C[crit_key])
    else:
        st["rating"] = R_NA
        st["note"] = (f"only {len(rows)} pairs -- below the minimum of "
                      f"{S['min_pairs']}, so no rating")
    return st


def group_values(rows, key):
    """Distinct values of a grouping dimension, blanks folded into one bucket."""
    seen = []
    for r in rows:
        v = (r.get(key) or "").strip() or "(not recorded)"
        if v not in seen:
            seen.append(v)
    return sorted(seen)


def group_rows(rows, key, value):
    if not key or value is None:
        return list(rows)
    out = []
    for r in rows:
        v = (r.get(key) or "").strip() or "(not recorded)"
        if v == value:
            out.append(r)
    return out


def group_breakdown(rec, key, F, C, S, crit_key):
    """[{group, n, hard_p90, rd_mean, r, rating}] for every value of a
    grouping dimension, worst first so the problem group is at the top."""
    rows = rec["rows"]
    out = []
    for g in group_values(rows, key):
        st = dup_stats(group_rows(rows, key, g), F, C, S, crit_key)
        if st:
            st["group"] = g
            out.append(st)
    out.sort(key=lambda d: (-(d["hard_p90"] or 0)))
    return out


# ===========================================================================
#  Thompson & Howarth precision regression
# ===========================================================================
MIN_TH_BINS = 3
MIN_TH_GROUP = 5


def _th_bins(rows, g):
    out = []
    for i in range(0, len(rows) - g + 1, g):
        chunk = rows[i:i + g]
        if len(chunk) < g:
            break
        out.append({"n": len(chunk),
                    "conc": mean([c["mean"] for c in chunk]),
                    "dbar": mean([c["diff"] for c in chunk])})
    return out


def analyse_th(project, F, C, S, dups, log=print):
    """Thompson & Howarth binned precision regression.

    The 1978 paper bins 11 pairs at a time, but that is a convention, not a
    requirement: the regression needs at least three bins to mean anything.
    When the requested bin size cannot deliver three bins, the bin size is
    reduced (never below MIN_TH_GROUP) and the size actually used is reported
    on the chart. If even that fails, the reason is recorded instead of the
    method silently producing nothing."""
    out = {}
    skipped = []
    g_req = max(MIN_TH_GROUP, int(S["th_group"]))
    for (dtype, el), rec in dups.items():
        rows = [r for r in rec["rows"] if r["mean"] is not None and r["mean"] > 0]
        g = g_req
        bins = _th_bins(rows, g)
        while len(bins) < MIN_TH_BINS and g > MIN_TH_GROUP:
            g -= 1
            bins = _th_bins(rows, g)
        if len(bins) < MIN_TH_BINS:
            need = MIN_TH_BINS * MIN_TH_GROUP
            skipped.append((dtype, el,
                            f"{len(rows)} usable pairs. The regression needs at "
                            f"least {MIN_TH_BINS} bins, so at least {need} pairs "
                            f"even at the smallest bin size of {MIN_TH_GROUP}. "
                            f"Insert more duplicates of this class, or lower the "
                            f"bin size in Settings if you accept coarser bins."))
            continue
        rows.sort(key=lambda r: r["mean"])
        bins = _th_bins(rows, g)
        cs = [bb["conc"] for bb in bins]
        ds = [bb["dbar"] for bb in bins]
        a_int, b_slope, r_corr = linreg(cs, ds)
        if a_int is None:
            skipped.append((dtype, el, "the binned points are collinear in x; "
                                       "no regression can be fitted."))
            continue

        # The intercept is the mean absolute difference at zero concentration,
        # so it cannot be negative. An unconstrained fit on few bins spanning a
        # wide grade range routinely returns a negative one, which then yields a
        # negative precision and a negative detection limit. When that happens
        # the model is refitted through the origin, which is the constrained
        # form of the same model rather than a cosmetic clamp.
        constrained = False
        if a_int < 0:
            sxx = sum(c * c for c in cs)
            if sxx <= 0:
                skipped.append((dtype, el, "all binned concentrations are zero."))
                continue
            b_slope = sum(c * d for c, d in zip(cs, ds)) / sxx
            a_int = 0.0
            constrained = True

        if b_slope <= 0:
            skipped.append((dtype, el,
                            "the fitted slope is not positive, so absolute "
                            "difference does not grow with grade. With this few "
                            "bins that is noise rather than a real result; treat "
                            "the rank-HARD statistics as the precision measure "
                            "for this set."))
            continue

        dl = rec.get("dl")
        # never read the curve below the lowest bin -- that is extrapolation
        # into the region the regression knows nothing about
        c_lo, c_hi = min(cs), max(cs)
        c_req = (dl * S["th_at_dl"]) if dl else bins[len(bins) // 2]["conc"]
        c_ref = min(max(c_req, c_lo), c_hi)
        clamped = abs(c_ref - c_req) > 1e-12
        prec = F.calc("th_precision", a_int=a_int, b_slope=b_slope, c=c_ref)
        rr = {"type": dtype, "element": el, "bins": bins, "group": g,
              "a_int": a_int, "b_slope": b_slope, "r": r_corr,
              "c_ref": c_ref, "c_requested": c_req, "clamped": clamped,
              "constrained": constrained, "dl": dl,
              "c_lo": c_lo, "c_hi": c_hi,
              "precision_at_ref": prec,
              "sigma_at_ref": F.calc("th_sigma",
                                     dbar=a_int + b_slope * c_ref),
              "pdl": (F.calc("th_pdl", a_int=a_int) if a_int > 0 else None),
              "curve": [], "ratings": {}, "rating": R_NA, "score": None}
        lo, hi = c_lo, c_hi
        for i in range(60):
            c = lo + (hi - lo) * i / 59.0
            if c <= 0:
                continue
            p = F.calc("th_precision", a_int=a_int, b_slope=b_slope, c=c)
            if p is not None:
                rr["curve"].append((c, p))
        rr["ratings"]["th_precision"] = rate(
            abs(prec) if prec is not None else None, C["th_precision"])
        rr["rating"], rr["score"] = combine_ratings([rr["ratings"]["th_precision"]])
        rr["group_requested"] = g_req
        out[(dtype, el)] = rr
    out["_skipped"] = skipped
    return out


# ===========================================================================
#  Check / umpire assays
# ===========================================================================
#  A duplicate measures PRECISION: the same laboratory, the same method, twice.
#  A check (umpire) assay measures ACCURACY BETWEEN LABORATORIES: the same
#  pulp, two different laboratories. The statistics are therefore different.
#  HARD is not the headline number here -- the grade-weighted bias is, because
#  that is the figure that moves contained metal.
# ===========================================================================
def _match_element(name, elements):
    """Match an umpire column to a primary element, allowing lab suffixes."""
    n = name.strip().lower()
    for e in elements:
        if n == e.strip().lower():
            return e
    for e in elements:
        el = e.strip().lower()
        if n.startswith(el) or el.startswith(n):
            return e
    for e in elements:
        el = e.strip().lower()
        base = el.split("_")[0]
        if base and n.startswith(base):
            return e
    return None


def build_umpire(project, S, log=print):
    """Return {element: [(sample_id, primary, umpire)]} plus the umpire lab name."""
    by_id = {}
    for smp in project.samples:
        by_id.setdefault(smp.sid.strip().upper(), smp)
    pairs = {}
    lab = ""

    # (a) a separate results file from the second laboratory
    ut = project.umpire
    if ut is not None:
        cols = [c for c, k in ut.value_cols if k == "numeric"] or [
            c for c in ut.header if c not in ut.mapping.values()]
        colmap = {}
        for c in cols:
            e = _match_element(c, project.elements)
            if e:
                colmap[c] = e
        if not colmap:
            log("  ! no umpire column could be matched to a primary element.")
        for r in ut.rows:
            sid = str(ut.get(r, "sampleid") or "").strip()
            if not sid:
                continue
            prim = by_id.get(sid.upper())
            if prim is None:
                continue
            if not lab:
                lab = str(ut.get(r, "lab") or "").strip()
            for c, e in colmap.items():
                a = prim.vals.get(e)
                b = fnum(ut.col(r, c))
                if a is None or b is None:
                    continue
                pairs.setdefault(e, []).append(
                    (sid, a, b, prim.hole, prim.batch, prim.drilltype, prim.lab))

    # (b) umpire rows inside the main table, keyed by parent sample
    for smp in project.samples:
        if smp.stype != T_UMP or not smp.parent:
            continue
        prim = by_id.get(smp.parent.strip().upper())
        if prim is None:
            continue
        if not lab:
            lab = smp.lab
        for e in project.elements:
            a, b = prim.vals.get(e), smp.vals.get(e)
            if a is None or b is None:
                continue
            pairs.setdefault(e, []).append(
                (smp.sid, a, b, prim.hole, prim.batch, prim.drilltype, prim.lab))

    for e, lst in pairs.items():
        log(f"  CHECK / UMPIRE {e}: {len(lst)} pair(s)")
    return pairs, lab


def analyse_umpire(project, F, C, S, log=print):
    out = {}
    pairs, lab = build_umpire(project, S, log=log)
    for el, lst in pairs.items():
        dl = detection_limit(project, el, S)
        rows = []
        for item in lst:
            sid, a, b = item[0], item[1], item[2]
            hole, batch, drilltype, plab = (list(item[3:]) + ["", "", "", ""])[:4]
            if a is None or b is None or a + b <= 0:
                continue
            if dl and S["drop_below_dl"] and (a < dl or b < dl):
                continue
            rows.append({
                "sample": sid, "primary": a, "umpire": b,
                "hole": hole, "batch": batch, "drilltype": drilltype, "lab": plab,
                "a": a, "b": b,
                "mean": (a + b) / 2.0, "diff": b - a,
                "bias": F.calc("ump_bias", pr=a, u=b),
                "ratio": F.calc("ump_ratio", pr=a, u=b),
                "hard": F.calc("ump_hard", pr=a, u=b)})
        if len(rows) < 3:
            continue

        sp = sum(r["primary"] for r in rows)
        su = sum(r["umpire"] for r in rows)
        wbias = F.calc("ump_weighted_bias", sum_pr=sp, sum_u=su)
        biases = [r["bias"] for r in rows if r["bias"] is not None]
        ratios = sorted(r["ratio"] for r in rows if r["ratio"] is not None)
        hards = sorted(r["hard"] for r in rows if r["hard"] is not None)
        diffs = [r["diff"] for r in rows]

        _, ols_b, r_corr = linreg([r["primary"] for r in rows],
                                  [r["umpire"] for r in rows])
        rma_a, rma_b = rma([r["primary"] for r in rows],
                           [r["umpire"] for r in rows])

        # bias by grade quartile -- an average hides a high-grade-only bias
        srt = sorted(rows, key=lambda r: r["primary"])
        q = max(1, len(srt) // 4)
        quart = []
        for i in range(4):
            chunk = srt[i * q:(i + 1) * q] if i < 3 else srt[3 * q:]
            if not chunk:
                continue
            cp = sum(c["primary"] for c in chunk)
            cu = sum(c["umpire"] for c in chunk)
            quart.append({
                "q": i + 1, "n": len(chunk),
                "lo": chunk[0]["primary"], "hi": chunk[-1]["primary"],
                "bias": F.calc("ump_weighted_bias", sum_pr=cp, sum_u=cu)})
        worst_q = max((abs(x["bias"]) for x in quart if x["bias"] is not None),
                      default=None)

        rec = {"element": el, "n": len(rows), "rows": rows, "lab": lab, "dl": dl,
               "sum_primary": sp, "sum_umpire": su,
               "mean_primary": sp / len(rows), "mean_umpire": su / len(rows),
               "wbias": wbias, "pbias": mean(biases),
               "median_ratio": pctile(ratios, 50),
               "hard_p90": pctile(hards, S["hard_pct"]),
               "hard_median": pctile(hards, 50),
               "hard_pct_used": S["hard_pct"],
               "r": r_corr, "ols_b": ols_b, "rma_a": rma_a, "rma_b": rma_b,
               "quartiles": quart, "worst_quartile": worst_q,
               "ttest": paired_t(diffs), "wilcoxon": wilcoxon(diffs),
               "ratings": {}, "rating": R_NA, "score": None}

        if len(rows) >= S["min_pairs"]:
            rec["ratings"]["ump_wbias"] = rate(
                abs(wbias) if wbias is not None else None, C["ump_wbias"])
            rec["ratings"]["ump_pbias"] = rate(
                abs(rec["pbias"]) if rec["pbias"] is not None else None,
                C["ump_pbias"])
            rec["ratings"]["ump_hard90"] = rate(rec["hard_p90"], C["ump_hard90"])
            rec["ratings"]["ump_grade_range"] = rate(worst_q, C["ump_grade_range"])
            rec["rating"], rec["score"] = combine_ratings(
                [rec["ratings"]["ump_wbias"], rec["ratings"]["ump_pbias"],
                 rec["ratings"]["ump_hard90"], rec["ratings"]["ump_grade_range"]],
                [4.0, 2.0, 1.5, 3.0])
        else:
            rec["note"] = (f"Only {len(rows)} usable pairs. Below the minimum of "
                           f"{S['min_pairs']} an inter-laboratory bias cannot be "
                           f"separated from chance, so no rating is given.")
        out[el] = rec
    return out


# ===========================================================================
#  Insertion rates
# ===========================================================================
def analyse_insertion(project, F, C, S, pairs, log=print):
    n_total = len(project.samples)
    counts = {t: 0 for t in SAMPLE_TYPES}
    for s in project.samples:
        counts[s.stype] = counts.get(s.stype, 0) + 1
    out = {"n_total": n_total, "rows": [], "rating": R_NA, "score": None}
    ratings = []
    for t in (T_CRM, T_BLANK, T_FDUP, T_CDUP, T_PDUP):
        n = counts.get(t, 0)
        pct = F.calc("insert_rate", n_control=n, n_total=n_total) if n_total else None
        every = (F.calc("insert_interval", n_control=n, n_total=n_total)
                 if n else None)
        r = rate(pct, C["insert_rate"]) if n_total else R_NA
        # a control class that is simply absent is a finding in itself
        if n == 0:
            r = R_VBAD
        out["rows"].append({"type": t, "n": n, "pct": pct, "every": every,
                            "rating": r})
        ratings.append(r)
    out["counts"] = counts
    out["rating"], out["score"] = combine_ratings(ratings)
    return out


# ===========================================================================
#  Driver
# ===========================================================================
def run_analysis(project, F, C, S, log=print):
    log("Building the sample population ...")
    build_samples(project, S, log=log)
    log("Pairing duplicates ...")
    pairs = build_pairs(project, S, log=log)
    log("Analysing CRMs ...")
    crm = analyse_crm(project, F, C, S, log=log)
    log("Analysing blanks ...")
    blank = analyse_blank(project, F, C, S, log=log)
    log("Analysing duplicates ...")
    dup = analyse_duplicates(project, F, C, S, pairs, log=log)
    log("Fitting Thompson-Howarth precision ...")
    th = analyse_th(project, F, C, S, dup, log=log)
    th_skipped = th.pop("_skipped", [])
    for dt, el, why in th_skipped:
        log(f"  Thompson-Howarth not fitted for {dt} / {el}: {why}")
    log("Analysing check / umpire assays ...")
    ump = analyse_umpire(project, F, C, S, log=log)
    log("Checking insertion rates ...")
    ins = analyse_insertion(project, F, C, S, pairs, log=log)

    ratings, weights = [], []
    for rec in crm.values():
        if rec["rating"] != R_NA:
            ratings.append(rec["rating"])
            weights.append(3.0)
    for rec in blank.values():
        if rec["rating"] != R_NA:
            ratings.append(rec["rating"])
            weights.append(1.5)
    for rec in dup.values():
        if rec["rating"] != R_NA:
            ratings.append(rec["rating"])
            weights.append(2.5)
    for rec in ump.values():
        if rec["rating"] != R_NA:
            ratings.append(rec["rating"])
            weights.append(3.0)
    if ins["rating"] != R_NA:
        ratings.append(ins["rating"])
        weights.append(1.0)
    overall, score = combine_ratings(ratings, weights)

    project.results = {"crm": crm, "blank": blank, "dup": dup, "th": th,
                       "umpire": ump, "th_skipped": th_skipped,
                       "insertion": ins, "pairs": pairs,
                       "overall": overall, "score": score}
    project.analysed_at = _dt.datetime.now()
    log(f"Analysis complete. Overall QA/QC rating: {overall}"
        + (f"  (score {score:.1f}/100)" if score is not None else ""))
    return project.results


# ===========================================================================
#  Chart engine -- pure tkinter Canvas, no third-party plotting library
# ===========================================================================
def nice_ticks(lo, hi, target=6):
    """Human-friendly linear tick positions covering [lo, hi]."""
    if lo == hi:
        lo, hi = lo - 0.5, hi + 0.5
    span = hi - lo
    raw = span / max(1, target)
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if raw / mag <= m:
            step = m * mag
            break
    else:
        step = 10 * mag
    start = math.floor(lo / step) * step
    ticks, v = [], start
    while v <= hi + step * 0.5:
        if v >= lo - step * 1e-9:
            ticks.append(round(v, 12))
        v += step
    return ticks


def log_ticks(lo, hi):
    if lo <= 0:
        lo = hi / 1e4 if hi > 0 else 1e-3
    out = []
    d0 = math.floor(math.log10(lo))
    d1 = math.ceil(math.log10(hi))
    decades = d1 - d0
    for d in range(int(d0), int(d1) + 1):
        for m in ((1,) if decades > 4 else (1, 2, 5)):
            v = m * 10 ** d
            if lo <= v <= hi:
                out.append(v)
    return out or [lo, hi]


def fmt_num(v):
    if v is None:
        return ""
    a = abs(v)
    if a == 0:
        return "0"
    if a >= 1e5 or a < 1e-3:
        return f"{v:.1e}"
    if a >= 100:
        return f"{v:,.0f}"
    if a >= 10:
        return f"{v:.1f}"
    if a >= 1:
        return f"{v:.2f}"
    return f"{v:.4g}"


class Chart(tk.Canvas):
    """A small self-contained plotting canvas: linear or log axes, points,
    lines, shaded bands, envelopes, labels, legend and PostScript export."""

    PAD_L, PAD_R, PAD_T, PAD_B = 78, 26, 42, 56

    def __init__(self, master, **kw):
        super().__init__(master, bg=BG1, highlightthickness=0, bd=0, **kw)
        self.title = ""
        self.xlabel = ""
        self.ylabel = ""
        self.xlog = False
        self.ylog = False
        self._layers = []
        self._legend = []
        self._xr = None
        self._yr = None
        self._notes = []
        self.bind("<Configure>", lambda e: self.redraw())

    # -- building ----------------------------------------------------------
    def clear(self):
        self._layers = []
        self._legend = []
        self._notes = []
        self._xr = self._yr = None
        self.title = self.xlabel = self.ylabel = ""
        self.xlog = self.ylog = False

    def points(self, xs, ys, color=C_PLOT, size=3, label=None, shape="o",
               outline=None):
        self._layers.append(("pts", xs, ys, color, size, shape, outline))
        if label:
            self._legend.append((label, color, "pts"))

    def line(self, xs, ys, color=ACCENT, width=2, dash=None, label=None):
        self._layers.append(("line", xs, ys, color, width, dash, None))
        if label:
            self._legend.append((label, color, "line"))

    def hline(self, y, color=FG_DIM, width=1, dash=None, label=None, text=None):
        self._layers.append(("hline", y, None, color, width, dash, text))
        if label:
            self._legend.append((label, color, "line"))

    def band(self, y0, y1, color="#243040", label=None):
        self._layers.append(("band", y0, y1, color, 0, None, None))
        if label:
            self._legend.append((label, color, "band"))

    def note(self, text, color=FG_DIM):
        self._notes.append((text, color))

    def set_range(self, xr=None, yr=None):
        self._xr, self._yr = xr, yr

    # -- coordinate transforms --------------------------------------------
    def _bounds(self):
        xs, ys = [], []
        for L in self._layers:
            kind = L[0]
            if kind in ("pts", "line"):
                xs += [v for v in L[1] if v is not None]
                ys += [v for v in L[2] if v is not None]
            elif kind == "hline":
                ys.append(L[1])
            elif kind == "band":
                ys += [L[1], L[2]]
        if self._xr:
            xs = list(self._xr)
        if self._yr:
            ys = list(self._yr)
        if not xs:
            xs = [0, 1]
        if not ys:
            ys = [0, 1]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        if self.xlog:
            pos = [v for v in xs if v > 0]
            x0 = min(pos) if pos else 1e-3
            x1 = max(pos) if pos else 1.0
            x0, x1 = x0 / 1.6, x1 * 1.6
        else:
            m = (x1 - x0) * 0.05 or 0.5
            x0, x1 = x0 - m, x1 + m
        if self.ylog:
            pos = [v for v in ys if v > 0]
            y0 = min(pos) if pos else 1e-3
            y1 = max(pos) if pos else 1.0
            y0, y1 = y0 / 1.6, y1 * 1.6
        else:
            m = (y1 - y0) * 0.08 or 0.5
            y0, y1 = y0 - m, y1 + m
        return x0, x1, y0, y1

    def _mk(self, x0, x1, y0, y1, w, h):
        L, R, T, B = self.PAD_L, self.PAD_R, self.PAD_T, self.PAD_B
        pw, ph = max(10, w - L - R), max(10, h - T - B)

        def fx(v):
            if v is None:
                return None
            if self.xlog:
                if v <= 0:
                    return None
                t = (math.log10(v) - math.log10(x0)) / (math.log10(x1) - math.log10(x0))
            else:
                t = (v - x0) / (x1 - x0) if x1 != x0 else 0.5
            return L + t * pw

        def fy(v):
            if v is None:
                return None
            if self.ylog:
                if v <= 0:
                    return None
                t = (math.log10(v) - math.log10(y0)) / (math.log10(y1) - math.log10(y0))
            else:
                t = (v - y0) / (y1 - y0) if y1 != y0 else 0.5
            return T + ph - t * ph
        return fx, fy, L, T, pw, ph

    # -- drawing -----------------------------------------------------------
    def redraw(self):
        self.delete("all")
        w = self.winfo_width() or 600
        h = self.winfo_height() or 400
        if w < 120 or h < 100:
            return
        x0, x1, y0, y1 = self._bounds()
        # reserve room under the plot for the x label plus any notes
        self.PAD_B = 56 + 15 * len(self._notes)
        fx, fy, L, T, pw, ph = self._mk(x0, x1, y0, y1, w, h)

        self.create_rectangle(L, T, L + pw, T + ph, fill=BG2, outline=BG3)

        xt = log_ticks(x0, x1) if self.xlog else nice_ticks(x0, x1)
        yt = log_ticks(y0, y1) if self.ylog else nice_ticks(y0, y1)
        for v in xt:
            px = fx(v)
            if px is None or not (L - 1 <= px <= L + pw + 1):
                continue
            self.create_line(px, T, px, T + ph, fill="#222d3a")
            self.create_line(px, T + ph, px, T + ph + 4, fill=BG3)
            self.create_text(px, T + ph + 14, text=fmt_num(v), fill=FG_DIM, font=MONO)
        for v in yt:
            py = fy(v)
            if py is None or not (T - 1 <= py <= T + ph + 1):
                continue
            self.create_line(L, py, L + pw, py, fill="#222d3a")
            self.create_line(L - 4, py, L, py, fill=BG3)
            self.create_text(L - 8, py, text=fmt_num(v), fill=FG_DIM, font=MONO,
                             anchor="e")

        # bands first so points sit on top
        for L_ in self._layers:
            if L_[0] != "band":
                continue
            a, b = fy(L_[1]), fy(L_[2])
            if a is None or b is None:
                continue
            self.create_rectangle(L, min(a, b), L + pw, max(a, b),
                                  fill=L_[3], outline="")

        for L_ in self._layers:
            kind = L_[0]
            if kind == "hline":
                py = fy(L_[1])
                if py is None or not (T <= py <= T + ph):
                    continue
                self.create_line(L, py, L + pw, py, fill=L_[3], width=L_[4],
                                 dash=L_[5] or ())
                if L_[6]:
                    self.create_text(L + 5, py - 8, text=L_[6], fill=L_[3],
                                     font=MONO, anchor="w")
            elif kind == "line":
                pts = []
                for xv, yv in zip(L_[1], L_[2]):
                    px, py = fx(xv), fy(yv)
                    if px is None or py is None:
                        continue
                    pts += [px, py]
                if len(pts) >= 4:
                    self.create_line(*pts, fill=L_[3], width=L_[4],
                                     dash=L_[5] or (), smooth=False)
            elif kind == "pts":
                col, sz, shape, outl = L_[3], L_[4], L_[5], L_[6]
                for xv, yv in zip(L_[1], L_[2]):
                    px, py = fx(xv), fy(yv)
                    if px is None or py is None:
                        continue
                    if not (L - 2 <= px <= L + pw + 2 and T - 2 <= py <= T + ph + 2):
                        continue
                    if shape == "s":
                        self.create_rectangle(px - sz, py - sz, px + sz, py + sz,
                                              fill=col, outline=outl or col)
                    elif shape == "+":
                        self.create_line(px - sz, py, px + sz, py, fill=col)
                        self.create_line(px, py - sz, px, py + sz, fill=col)
                    else:
                        self.create_oval(px - sz, py - sz, px + sz, py + sz,
                                         fill=col, outline=outl or col)

        if self.title:
            self.create_text(L, 16, text=self.title, fill=FG, font=UI_H, anchor="w")
        if self.xlabel:
            self.create_text(L + pw / 2, T + ph + 30, text=self.xlabel,
                             fill=FG_DIM, font=UI)
        if self.ylabel:
            self.create_text(14, T + ph / 2, text=self.ylabel, fill=FG_DIM,
                             font=UI, angle=90)

        if self._legend:
            lw = 8 + 10 + max(len(x[0]) for x in self._legend) * 6.6
            lh = 8 + 15 * len(self._legend)
            lx = L + pw - lw - 8
            self.create_rectangle(lx, T + 4, lx + lw, T + 4 + lh,
                                  fill=BG1, outline=BG3)
            ly = T + 16
            for label, color, kind in self._legend:
                self.create_rectangle(lx + 8, ly - 4, lx + 16, ly + 4,
                                      fill=color, outline="")
                self.create_text(lx + 22, ly, text=label, fill=FG_DIM, font=MONO,
                                 anchor="w")
                ly += 15

        ny = T + ph + 48
        for text, color in self._notes:
            self.create_text(L, ny, text=text, fill=color, font=MONO, anchor="w")
            ny += 14

    def export_ps(self, path):
        self.update_idletasks()
        self.postscript(file=path, colormode="color",
                        width=self.winfo_width(), height=self.winfo_height())
        return path


# ===========================================================================
#  Chart builders -- one per method
# ===========================================================================
def chart_crm_control(ch, rec, S):
    """Shewhart control chart: sequence vs measured value."""
    ch.clear()
    ch.title = f"CRM control chart -- {rec['crm']}  /  {rec['element']}"
    ch.xlabel = "insertion sequence"
    ch.ylabel = f"measured value {('(' + rec['unit'] + ')') if rec.get('unit') else ''}"
    pts = rec["points"]
    xs = list(range(1, len(pts) + 1))
    ys = [p["value"] for p in pts]
    cert, sd = rec.get("cert"), rec.get("eff_sd")
    if cert is not None and sd:
        kw, kf = S["k_warn"], S["k_fail"]
        ch.band(cert - kw * sd, cert + kw * sd, "#1c2a24")
        ch.hline(cert, ACCENT, 2, None, "certified", f"certified {fmt_num(cert)}")
        for k, col in ((kw, C_WARN), (kf, C_ERR)):
            ch.hline(cert + k * sd, col, 1, (4, 3), None, f"+{k:g} SD")
            ch.hline(cert - k * sd, col, 1, (4, 3), None, f"-{k:g} SD")
        ch.set_range(yr=(min(ys + [cert - (kf + 0.7) * sd]),
                         max(ys + [cert + (kf + 0.7) * sd])))
    ok_x = [x for x, p in zip(xs, pts)
            if p["z"] is None or abs(p["z"]) <= S["k_warn"]]
    ok_y = [p["value"] for p in pts if p["z"] is None or abs(p["z"]) <= S["k_warn"]]
    wn_x = [x for x, p in zip(xs, pts)
            if p["z"] is not None and S["k_warn"] < abs(p["z"]) <= S["k_fail"]]
    wn_y = [p["value"] for p in pts
            if p["z"] is not None and S["k_warn"] < abs(p["z"]) <= S["k_fail"]]
    bd_x = [x for x, p in zip(xs, pts) if p["z"] is not None and abs(p["z"]) > S["k_fail"]]
    bd_y = [p["value"] for p in pts if p["z"] is not None and abs(p["z"]) > S["k_fail"]]
    ch.line(xs, ys, "#3d5064", 1)
    ch.points(ok_x, ok_y, C_PLOT, 3, "within limits")
    if wn_x:
        ch.points(wn_x, wn_y, C_WARN, 4, f"beyond {S['k_warn']:g} SD")
    if bd_x:
        ch.points(bd_x, bd_y, C_ERR, 5, f"beyond {S['k_fail']:g} SD", "s")
    if rec.get("bias") is not None:
        ch.note(f"mean bias {rec['bias']:+.2f} %    observed RSD "
                f"{rec['rsd_pct']:.2f} %    n = {rec['n']}    "
                f"SD source: {rec.get('sd_source', '-')}")
    ch.redraw()


def chart_crm_bias(ch, rec, S):
    """Bias of every CRM result in sequence, with the acceptance band."""
    ch.clear()
    ch.title = f"CRM bias -- {rec['crm']}  /  {rec['element']}"
    ch.xlabel = "insertion sequence"
    ch.ylabel = "bias %"
    pts = rec["points"]
    xs = list(range(1, len(pts) + 1))
    ys = [p["bias"] for p in pts]
    ch.band(-5, 5, "#1c2a24")
    ch.hline(0, ACCENT, 2, None, None, "certified")
    for v in (-10, -5, 5, 10):
        ch.hline(v, C_WARN if abs(v) == 5 else C_ERR, 1, (4, 3), None, f"{v:+g} %")
    if rec.get("bias") is not None:
        ch.hline(rec["bias"], C_INFO, 2, (6, 3), "mean bias",
                 f"mean {rec['bias']:+.2f} %")
    ch.line(xs, ys, "#3d5064", 1)
    ch.points(xs, ys, C_PLOT, 3, "bias")
    ch.redraw()


def chart_crm_zhist(ch, rec, S):
    """Distribution of z-scores against the expected normal shape."""
    ch.clear()
    ch.title = f"Z-score distribution -- {rec['crm']}  /  {rec['element']}"
    ch.xlabel = "z-score (standard deviations from certified)"
    ch.ylabel = "count"
    zs = [p["z"] for p in rec["points"] if p["z"] is not None]
    if not zs:
        ch.note("no z-scores: the certificate carries no standard deviation")
        ch.redraw()
        return
    lo, hi = min(-4.0, min(zs)), max(4.0, max(zs))
    nb = 16
    step = (hi - lo) / nb
    counts = [0] * nb
    for z in zs:
        i = min(nb - 1, max(0, int((z - lo) / step)))
        counts[i] += 1
    for i, c in enumerate(counts):
        if not c:
            continue
        x0 = lo + i * step
        x1 = x0 + step
        ch.line([x0, x0, x1, x1], [0, c, c, 0],
                C_PLOT if abs((x0 + x1) / 2) <= S["k_warn"] else
                (C_WARN if abs((x0 + x1) / 2) <= S["k_fail"] else C_ERR), 2)
    for k, col in ((S["k_warn"], C_WARN), (S["k_fail"], C_ERR)):
        for sgn in (-1, 1):
            ch.line([sgn * k, sgn * k], [0, max(counts)], col, 1, (4, 3))
    ch.set_range(xr=(lo, hi), yr=(0, max(counts) * 1.15))
    ch.note(f"n = {len(zs)}   beyond {S['k_warn']:g} SD: {rec['warn_pct']:.1f} %"
            f"   beyond {S['k_fail']:g} SD: {rec['fail_pct']:.1f} %")
    ch.redraw()


def chart_blank(ch, rec, S):
    ch.clear()
    ch.title = f"Blank control chart -- {rec['element']}"
    ch.xlabel = "insertion sequence"
    ch.ylabel = f"value (DL = {fmt_num(rec['dl'])})"
    pts = rec["points"]
    xs = list(range(1, len(pts) + 1))
    ys = [p["value"] for p in pts]
    ch.hline(rec["dl"], C_INFO, 1, (4, 3), "detection limit", "DL")
    ch.hline(rec["limit"], C_ERR, 2, None, "contamination limit",
             f"{S['k_dl']:g} x DL = {fmt_num(rec['limit'])}")
    ok_x = [x for x, p in zip(xs, pts) if not p["fail"]]
    ok_y = [p["value"] for p in pts if not p["fail"]]
    bd_x = [x for x, p in zip(xs, pts) if p["fail"]]
    bd_y = [p["value"] for p in pts if p["fail"]]
    ch.line(xs, ys, "#3d5064", 1)
    ch.points(ok_x, ok_y, C_OK, 3, "pass")
    if bd_x:
        ch.points(bd_x, bd_y, C_ERR, 5, "fail", "s")
    ch.note(f"n = {rec['n']}   failures {rec['n_fail']} ({rec['fail_pct']:.1f} %)"
            f"   worst {fmt_num(rec['max'])} = {rec['max_ratio']:.1f} x DL")
    if rec.get("carry"):
        ch.note(f"{len(rec['carry'])} failure(s) directly follow a high-grade "
                f"sample -- carry-over is the likely cause", C_WARN)
    ch.redraw()


def chart_dup_scatter(ch, rec, S):
    ch.clear()
    ch.title = (f"Original vs duplicate -- {rec['type']}  /  {rec['element']}")
    ch.xlabel = "original"
    ch.ylabel = "duplicate"
    ch.xlog = ch.ylog = bool(S["log_axis"])
    xs = [r["a"] for r in rec["rows"]]
    ys = [r["b"] for r in rec["rows"]]
    lo = min(min(xs), min(ys))
    hi = max(max(xs), max(ys))
    ch.line([lo, hi], [lo, hi], ACCENT, 2, None, "1:1")
    for env, col in ((10, C_OK), (20, C_WARN)):
        f = 1 + env / 100.0
        ch.line([lo, hi], [lo * f, hi * f], col, 1, (4, 3),
                f"+/-{env} %" if env == 10 else None)
        ch.line([lo, hi], [lo / f, hi / f], col, 1, (4, 3))
    if rec.get("rma_b") is not None:
        a, b = rec["rma_a"], rec["rma_b"]
        ch.line([lo, hi], [a + b * lo, a + b * hi], C_PLOT2, 2, (7, 3), "RMA fit")
    ch.points(xs, ys, C_PLOT, 3, "pairs")
    bits = [f"n = {rec['n']}"]
    if rec.get("r") is not None:
        bits.append(f"r = {rec['r']:.4f}")
    if rec.get("rma_b") is not None:
        bits.append(f"RMA slope = {rec['rma_b']:.4f}")
    ch.note("   ".join(bits))
    ch.redraw()


def chart_dup_rank_hard(ch, rec, S):
    """The rank-HARD plot -- the plot acceptance is normally quoted from."""
    ch.clear()
    ch.title = f"Rank-HARD -- {rec['type']}  /  {rec['element']}"
    ch.xlabel = "cumulative percentile of pairs"
    ch.ylabel = "HARD %"
    hards = sorted(r["hard"] for r in rec["rows"] if r["hard"] is not None)
    n = len(hards)
    xs = [100.0 * (i + 0.5) / n for i in range(n)]
    ch.line(xs, hards, C_PLOT, 2, None, "HARD")
    ch.points(xs, hards, C_PLOT, 2)
    p = rec["hard_pct_used"]
    v = rec["hard_p90"]
    ch.line([p, p], [0, max(hards)], C_INFO, 1, (4, 3))
    ch.hline(v, C_INFO, 1, (4, 3), None, f"P{p:g} = {v:.2f} %")
    for lim, col in ((10, C_OK), (20, C_WARN), (30, C_ERR)):
        ch.hline(lim, col, 1, (2, 4), None, f"{lim} %")
    ch.set_range(xr=(0, 100))
    note = (f"n = {n}   P{p:g} HARD = {v:.2f} %   "
            f"median {rec['hard_median']:.2f} %")
    if rec.get("pooled_rp") is not None:
        note += f"   pooled relative precision {rec['pooled_rp']:.2f} %"
    ch.note(note)
    ch.redraw()


def chart_dup_mean_hrd(ch, rec, S):
    """Bland-Altman style: signed relative difference against pair mean.
    Shows whether scatter depends on grade and whether it is one-sided."""
    ch.clear()
    ch.title = f"Relative difference vs grade -- {rec['type']}  /  {rec['element']}"
    ch.xlabel = "pair mean"
    ch.ylabel = "HRD %  (signed)"
    ch.xlog = bool(S["log_axis"])
    xs = [r["mean"] for r in rec["rows"]]
    ys = [r["hrd"] for r in rec["rows"]]
    ch.hline(0, ACCENT, 2)
    for v, col in ((10, C_OK), (-10, C_OK), (20, C_WARN), (-20, C_WARN)):
        ch.hline(v, col, 1, (4, 3), None, f"{v:+g} %")
    m = mean(ys)
    if m is not None:
        ch.hline(m, C_INFO, 2, (6, 3), "mean HRD", f"mean {m:+.2f} %")
    if rec.get("dl"):
        ch.line([rec["dl"], rec["dl"]], [min(ys), max(ys)], C_PLOT2, 1, (2, 4))
    ch.points(xs, ys, C_PLOT, 3, "pairs")
    ch.note(f"mean signed HRD {m:+.2f} %   a persistent sign means a splitting "
            f"bias, not poor precision" if m is not None else "")
    ch.redraw()


def chart_dup_hist(ch, rec, S):
    ch.clear()
    ch.title = f"HARD distribution -- {rec['type']}  /  {rec['element']}"
    ch.xlabel = "HARD %"
    ch.ylabel = "count"
    hards = [r["hard"] for r in rec["rows"] if r["hard"] is not None]
    hi = max(hards + [1.0])
    nb = 20
    step = hi / nb
    counts = [0] * nb
    for h in hards:
        counts[min(nb - 1, int(h / step))] += 1
    for i, c in enumerate(counts):
        if not c:
            continue
        x0, x1 = i * step, (i + 1) * step
        mid = (x0 + x1) / 2
        col = C_OK if mid <= 10 else (C_WARN if mid <= 20 else C_ERR)
        ch.line([x0, x0, x1, x1], [0, c, c, 0], col, 2)
    ch.set_range(xr=(0, hi), yr=(0, max(counts) * 1.15))
    ch.note("   ".join(f"<={k}%: {v:.0f}%" for k, v in rec["within"].items()))
    ch.redraw()


def chart_th(ch, rec, S):
    ch.clear()
    ch.title = (f"Thompson-Howarth precision -- {rec['type']}  /  {rec['element']}")
    ch.xlabel = "mean concentration of bin"
    ch.ylabel = "mean absolute difference"
    xs = [b["conc"] for b in rec["bins"]]
    ys = [b["dbar"] for b in rec["bins"]]
    lbl = f"bins of {rec['group']} pairs"
    if rec.get("group_requested") and rec["group_requested"] != rec["group"]:
        lbl += f" (reduced from {rec['group_requested']})"
    ch.points(xs, ys, C_PLOT, 4, lbl, "s")
    lo, hi = min(xs), max(xs)
    ch.line([lo, hi], [rec["a_int"] + rec["b_slope"] * lo,
                       rec["a_int"] + rec["b_slope"] * hi], ACCENT, 2, None,
            "fitted line")
    ch.note(f"mean|d| = {fmt_num(rec['a_int'])} + {rec['b_slope']:.4f} x c"
            f"    r = {rec['r']:.4f}" if rec.get("r") is not None else "")
    note = (f"precision at {fmt_num(rec['c_ref'])} = "
            f"{rec['precision_at_ref']:.1f} %")
    note += (f"    practical detection limit {fmt_num(rec['pdl'])}"
             if rec.get("pdl") else "    practical detection limit not resolvable")
    ch.note(note)
    if rec.get("constrained"):
        ch.note("intercept was negative, so the model was refitted through the "
                "origin", C_WARN)
    if rec.get("clamped"):
        ch.note(f"requested {fmt_num(rec['c_requested'])} is outside the binned "
                f"range {fmt_num(rec['c_lo'])} - {fmt_num(rec['c_hi'])}; "
                f"read at {fmt_num(rec['c_ref'])} instead", C_WARN)
    ch.redraw()


def chart_th_curve(ch, rec, S):
    ch.clear()
    ch.title = f"Precision curve -- {rec['type']}  /  {rec['element']}"
    ch.xlabel = "concentration"
    ch.ylabel = "precision % at 95 % confidence"
    ch.xlog = True
    xs = [c for c, _ in rec["curve"]]
    ys = [p for _, p in rec["curve"]]
    ch.line(xs, ys, ACCENT, 2, None, "precision")
    for lim, col in ((10, C_OK), (20, C_WARN), (30, C_ERR)):
        ch.hline(lim, col, 1, (4, 3), None, f"{lim} %")
    if rec.get("dl"):
        ch.line([rec["dl"], rec["dl"]], [0, max(ys)], C_PLOT2, 1, (2, 4))
    ch.set_range(yr=(0, min(120.0, max(ys) * 1.1)))
    ch.note(f"reference concentration {fmt_num(rec['c_ref'])} "
            f"-> {rec['precision_at_ref']:.1f} %")
    ch.redraw()


def chart_ump_qq(ch, rec, S):
    """Quantile-quantile plot -- the standard umpire plot. Both series are
    sorted independently, so a mis-paired sample cannot distort it; it shows
    whether the two laboratories report the same DISTRIBUTION of grades."""
    ch.clear()
    ch.title = f"Q-Q plot, primary vs umpire -- {rec['element']}"
    ch.xlabel = "primary laboratory, sorted"
    ch.ylabel = "umpire laboratory, sorted"
    ch.xlog = ch.ylog = bool(S["log_axis"])
    xs = sorted(r["primary"] for r in rec["rows"])
    ys = sorted(r["umpire"] for r in rec["rows"])
    lo, hi = min(xs[0], ys[0]), max(xs[-1], ys[-1])
    ch.line([lo, hi], [lo, hi], ACCENT, 2, None, "1:1")
    ch.points(xs, ys, C_PLOT2, 3, "quantile pairs")
    ch.note("A curve lying wholly above or below the 1:1 line is a distribution "
            "bias; a curve that crosses it is a grade-dependent bias.")
    ch.redraw()


def chart_ump_scatter(ch, rec, S):
    ch.clear()
    ch.title = f"Primary vs umpire -- {rec['element']}"
    ch.xlabel = "primary laboratory"
    ch.ylabel = "umpire laboratory"
    ch.xlog = ch.ylog = bool(S["log_axis"])
    xs = [r["primary"] for r in rec["rows"]]
    ys = [r["umpire"] for r in rec["rows"]]
    lo, hi = min(min(xs), min(ys)), max(max(xs), max(ys))
    ch.line([lo, hi], [lo, hi], ACCENT, 2, None, "1:1")
    for env, col in ((10, C_OK), (20, C_WARN)):
        f = 1 + env / 100.0
        ch.line([lo, hi], [lo * f, hi * f], col, 1, (4, 3),
                f"+/-{env} %" if env == 10 else None)
        ch.line([lo, hi], [lo / f, hi / f], col, 1, (4, 3))
    if rec.get("rma_b") is not None:
        a, b = rec["rma_a"], rec["rma_b"]
        ch.line([lo, hi], [a + b * lo, a + b * hi], C_PLOT2, 2, (7, 3), "RMA fit")
    ch.points(xs, ys, C_PLOT, 3, "pairs")
    bits = [f"n = {rec['n']}"]
    if rec.get("r") is not None:
        bits.append(f"r = {rec['r']:.4f}")
    if rec.get("rma_b") is not None:
        bits.append(f"RMA slope = {rec['rma_b']:.4f}")
    ch.note("   ".join(bits))
    ch.redraw()


def chart_ump_bias_grade(ch, rec, S):
    ch.clear()
    ch.title = f"Relative bias vs grade -- {rec['element']}"
    ch.xlabel = "primary laboratory result"
    ch.ylabel = "umpire - primary, relative %"
    ch.xlog = bool(S["log_axis"])
    xs = [r["primary"] for r in rec["rows"]]
    ys = [r["bias"] for r in rec["rows"]]
    ch.hline(0, ACCENT, 2, None, None, "no bias")
    for v, col in ((10, C_OK), (-10, C_OK), (20, C_WARN), (-20, C_WARN)):
        ch.hline(v, col, 1, (4, 3), None, f"{v:+g} %")
    if rec.get("wbias") is not None:
        ch.hline(rec["wbias"], C_INFO, 2, (6, 3), "grade-weighted bias",
                 f"weighted {rec['wbias']:+.2f} %")
    ch.points(xs, ys, C_PLOT, 3, "pairs")
    ch.note("A tilt across this plot means the bias depends on grade, which no "
            "single average bias figure can express.")
    ch.redraw()


def chart_ump_quartile(ch, rec, S):
    ch.clear()
    ch.title = f"Grade-weighted bias by grade quartile -- {rec['element']}"
    ch.xlabel = "grade quartile of the primary result"
    ch.ylabel = "grade-weighted bias %"
    ch.hline(0, ACCENT, 2)
    for v, col in ((5, C_OK), (-5, C_OK), (10, C_WARN), (-10, C_WARN)):
        ch.hline(v, col, 1, (4, 3), None, f"{v:+g} %")
    vals = []
    for q in rec["quartiles"]:
        if q["bias"] is None:
            continue
        x, v = q["q"], q["bias"]
        vals.append(v)
        col = C_OK if abs(v) <= 5 else (C_WARN if abs(v) <= 10 else C_ERR)
        ch.line([x - 0.3, x - 0.3, x + 0.3, x + 0.3], [0, v, v, 0], col, 2)
    if not vals:
        ch.redraw()
        return
    ch.set_range(xr=(0.4, 4.6),
                 yr=(min(vals + [-6.0]) * 1.25, max(vals + [6.0]) * 1.25))
    ch.note("   ".join(
        f"Q{q['q']} ({fmt_num(q['lo'])}-{fmt_num(q['hi'])}, n={q['n']}): "
        f"{q['bias']:+.2f} %" for q in rec["quartiles"] if q["bias"] is not None))
    ch.redraw()


def chart_ump_ratio(ch, rec, S):
    ch.clear()
    ch.title = f"Umpire / primary ratio, ranked -- {rec['element']}"
    ch.xlabel = "cumulative percentile of pairs"
    ch.ylabel = "umpire / primary"
    ratios = sorted(r["ratio"] for r in rec["rows"] if r["ratio"] is not None)
    n = len(ratios)
    xs = [100.0 * (i + 0.5) / n for i in range(n)]
    ch.hline(1.0, ACCENT, 2, None, None, "1.00")
    for v, col in ((1.1, C_OK), (0.9, C_OK), (1.2, C_WARN), (0.8, C_WARN)):
        ch.hline(v, col, 1, (4, 3), None, f"{v:.2f}")
    ch.line(xs, ratios, C_PLOT, 2, None, "ratio")
    ch.points(xs, ratios, C_PLOT, 2)
    ch.hline(rec["median_ratio"], C_INFO, 2, (6, 3), "median",
             f"median {rec['median_ratio']:.4f}")
    ch.set_range(xr=(0, 100))
    ch.note(f"n = {n}   median ratio {rec['median_ratio']:.4f}   "
            f"grade-weighted ratio {rec['sum_umpire'] / rec['sum_primary']:.4f}")
    ch.redraw()



def chart_group_summary(ch, breakdown, label, S, crit=None):
    """Bar chart of P90 HARD per group, coloured by rating. The chart that
    answers 'where is the problem', rather than 'is there a problem'."""
    ch.clear()
    ch.title = f"Precision by {label}"
    ch.xlabel = ""
    ch.ylabel = f"P{S['hard_pct']:g} HARD %"
    if not breakdown:
        ch.note("no groups to compare")
        ch.redraw()
        return
    vals = [g["hard_p90"] or 0.0 for g in breakdown]
    if crit:
        for cut, name in zip(crit["cuts"][:3], RATING_ORDER[:3]):
            ch.hline(cut, RATING_COLOR[name], 1, (4, 3), None, f"{name} <= {cut:g}")
    for i, g in enumerate(breakdown):
        x = i + 1
        v = g["hard_p90"] or 0.0
        col = RATING_COLOR.get(g.get("rating"), FG_DIM)
        ch.line([x - 0.32, x - 0.32, x + 0.32, x + 0.32], [0, v, v, 0], col, 2)
    ch.set_range(xr=(0.3, len(breakdown) + 0.7), yr=(0, max(vals) * 1.2 or 1))
    shown = breakdown[:8]
    ch.note("worst first:  " + "   ".join(
        f"{g['group']} {g['hard_p90']:.1f}% (n={g['n']})" for g in shown))
    if len(breakdown) > len(shown):
        ch.note(f"... and {len(breakdown) - len(shown)} more group(s); "
                f"see the table below")
    ch.redraw()


def chart_dup_qq(ch, rec, S):
    """Quantile-quantile plot of the two populations. A scatter tests whether
    each PAIR agrees; a Q-Q plot tests whether the two DISTRIBUTIONS agree,
    which is the question that matters when one side is a different lab."""
    ch.clear()
    ch.title = f"Q-Q plot -- {rec.get('type', 'duplicates')}  /  {rec['element']}"
    ch.xlabel = "original -- sorted quantiles"
    ch.ylabel = "duplicate -- sorted quantiles"
    ch.xlog = ch.ylog = bool(S["log_axis"])
    xs = sorted(r["a"] for r in rec["rows"])
    ys = sorted(r["b"] for r in rec["rows"])
    if not xs:
        ch.note("no pairs")
        ch.redraw()
        return
    lo = min(xs[0], ys[0])
    hi = max(xs[-1], ys[-1])
    ch.line([lo, hi], [lo, hi], ACCENT, 2, None, "1:1")
    ch.points(xs, ys, C_PLOT2, 3, "quantiles")
    a_int, b_slope, r_corr = linreg(xs, ys)
    if b_slope is not None:
        ch.line([lo, hi], [a_int + b_slope * lo, a_int + b_slope * hi],
                C_INFO, 2, (7, 3), "fit")
        ch.note(f"quantile fit slope {b_slope:.4f}   intercept "
                f"{fmt_num(a_int)}   r = {r_corr:.4f}")
    ch.note("points above the 1:1 line mean the duplicate population is "
            "systematically richer, not just noisier")
    ch.redraw()


def chart_insertion(ch, ins, S):
    ch.clear()
    ch.title = "Control sample insertion rates"
    ch.xlabel = ""
    ch.ylabel = "insertion rate %"
    rows = ins["rows"]
    ch.hline(5, C_OK, 2, None, "5 % convention", "5 % convention")
    for i, r in enumerate(rows):
        x = i + 1
        v = r["pct"] or 0.0
        col = RATING_COLOR.get(r["rating"], FG_DIM)
        ch.line([x - 0.28, x - 0.28, x + 0.28, x + 0.28], [0, v, v, 0], col, 2)
    ch.set_range(xr=(0.3, len(rows) + 0.7),
                 yr=(0, max([r["pct"] or 0 for r in rows] + [6.5]) * 1.15))
    ch.note("   ".join(f"{r['type']}: {r['n']} ({(r['pct'] or 0):.1f} %)"
                       for r in rows))
    ch.redraw()


# ===========================================================================
#  Export
# ===========================================================================
def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def export_results(project, F, C, S, folder, base, log=print):
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
    for el, rec in sorted(R["blank"].items()):
        score.append({"Section": "BLANK", "Subject": "blanks", "Element": el,
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
    for el, rec in sorted(R["blank"].items()):
        for p in rec["points"]:
            bl.append({"Element": el, "Sample ID": p["sample"], "Batch": p["batch"],
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
        ["Element", "Sample ID", "Batch", "Sequence", "Value", "DL", "x DL",
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

    # ---- protocol: the formulas and criteria actually used ----
    proto = []
    for k, d in F.defs.items():
        proto.append({"Kind": "FORMULA", "Group": d["group"], "Key": k,
                      "Label": d["label"], "Definition": d["expr"],
                      "Variables": d["vars"], "Note": d["note"]})
    for k, d in C.items():
        proto.append({"Kind": "CRITERION", "Group": d["group"], "Key": k,
                      "Label": d["label"],
                      "Definition": " | ".join(
                          f"{n} {'<=' if d['dir'] == 'low' else '>='} {c:g}"
                          for n, c in zip(RATING_ORDER[:5], d["cuts"]))
                      + f" | {R_VBAD} otherwise",
                      "Variables": d["unit"], "Note": d["note"]})
    for k, v in S.items():
        proto.append({"Kind": "SETTING", "Group": "SETTINGS", "Key": k,
                      "Label": k, "Definition": str(v), "Variables": "", "Note": ""})
    out("protocol", proto,
        ["Kind", "Group", "Key", "Label", "Definition", "Variables", "Note"])

    for p in written:
        log(f"  wrote {os.path.basename(p)}")
    return written


# ===========================================================================
#  Theme
# ===========================================================================
def apply_theme(root):
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    root.configure(bg=BG0)
    st.configure(".", background=BG1, foreground=FG, font=UI,
                 fieldbackground=BG2, bordercolor=BG3, focuscolor=ACCENT)
    st.configure("TFrame", background=BG1)
    st.configure("Dark.TFrame", background=BG0)
    st.configure("Panel.TFrame", background=BG1)
    st.configure("Head.TFrame", background=BG2)
    st.configure("TLabel", background=BG1, foreground=FG)
    st.configure("Dim.TLabel", background=BG1, foreground=FG_DIM)
    st.configure("Head.TLabel", background=BG2, foreground=ACCENT, font=UI_H)
    st.configure("Sec.TLabel", background=BG1, foreground=ACCENT, font=UI_B)
    st.configure("Mono.TLabel", background=BG1, foreground=FG, font=MONO)
    st.configure("TButton", background=BG3, foreground=FG, borderwidth=0,
                 focusthickness=0, padding=(12, 6))
    st.map("TButton", background=[("active", "#35455a"), ("disabled", BG2)],
           foreground=[("disabled", FG_DIM)])
    st.configure("Accent.TButton", background=ACCENT_D, foreground="#12161c",
                 font=UI_B, padding=(14, 7))
    st.map("Accent.TButton", background=[("active", ACCENT), ("disabled", BG3)],
           foreground=[("disabled", FG_DIM)])
    st.configure("Step.TButton", background=BG2, foreground=FG, padding=(10, 9),
                 anchor="w")
    st.map("Step.TButton", background=[("active", BG3)])
    st.configure("TEntry", fieldbackground=BG2, foreground=FG, insertcolor=ACCENT,
                 bordercolor=BG3, lightcolor=BG3, darkcolor=BG3)
    st.configure("TCombobox", fieldbackground=BG2, background=BG3, foreground=FG,
                 arrowcolor=ACCENT, bordercolor=BG3)
    st.map("TCombobox", fieldbackground=[("readonly", BG2)],
           foreground=[("readonly", FG)])
    st.configure("TCheckbutton", background=BG1, foreground=FG)
    st.map("TCheckbutton", background=[("active", BG1)])
    st.configure("TNotebook", background=BG0, borderwidth=0, tabmargins=(2, 4, 2, 0))
    st.configure("TNotebook.Tab", background=BG1, foreground=FG_DIM,
                 padding=(7, 7), borderwidth=0, font=UI)
    st.map("TNotebook.Tab", background=[("selected", BG2)],
           foreground=[("selected", ACCENT)], font=[("selected", UI_B)])
    st.configure("Treeview", background=BG2, fieldbackground=BG2, foreground=FG,
                 rowheight=21, borderwidth=0, font=MONO)
    st.configure("Treeview.Heading", background=BG3, foreground=ACCENT,
                 font=UI_B, relief="flat", padding=(6, 5))
    st.map("Treeview.Heading", background=[("active", "#35455a")])
    st.map("Treeview", background=[("selected", "#3c5a78")],
           foreground=[("selected", "#ffffff")])
    st.configure("TSeparator", background=BG3)
    st.configure("Vertical.TScrollbar", background=BG3, troughcolor=BG1,
                 arrowcolor=FG_DIM, bordercolor=BG1)
    st.configure("Horizontal.TScrollbar", background=BG3, troughcolor=BG1,
                 arrowcolor=FG_DIM, bordercolor=BG1)
    st.configure("TLabelframe", background=BG1, foreground=ACCENT, bordercolor=BG3)
    st.configure("TLabelframe.Label", background=BG1, foreground=ACCENT, font=UI_B)
    return st


def draw_logo(canvas, w=44, h=44):
    """Control chart mark: a centre line with points scattering around it."""
    canvas.delete("all")
    canvas.configure(bg=BG0, highlightthickness=0)
    x0, x1 = 5, w - 5
    mid = h / 2
    canvas.create_line(x0, mid - (h * 0.26), x1, mid - (h * 0.26),
                       fill=C_ERR, width=1, dash=(2, 2))
    canvas.create_line(x0, mid + (h * 0.26), x1, mid + (h * 0.26),
                       fill=C_ERR, width=1, dash=(2, 2))
    canvas.create_line(x0, mid, x1, mid, fill=ACCENT, width=2)
    pts = [0.10, -0.14, 0.05, 0.19, -0.08, 0.30, -0.05]
    n = len(pts)
    for i, dy in enumerate(pts):
        px = x0 + (x1 - x0) * i / (n - 1)
        py = mid + dy * h
        col = C_ERR if abs(dy) > 0.26 else (C_WARN if abs(dy) > 0.17 else C_PLOT)
        canvas.create_oval(px - 2.2, py - 2.2, px + 2.2, py + 2.2,
                           fill=col, outline="")


# ===========================================================================
#  Import dialogs
# ===========================================================================
class MappingDialog(tk.Toplevel):
    """Column mapping, sample-type classification and element flagging."""

    ROLES = {
        "assay": [("sampleid", "Sample ID", True), ("type", "Sample Type", False),
                  ("crmid", "CRM code", False), ("parent", "Parent / original ID", False),
                  ("batch", "Batch / job", False), ("lab", "Laboratory", False),
                  ("date", "Date", False), ("order", "Sequence", False),
                  ("holeid", "Hole / trench (optional)", False),
                  ("drilltype", "Drill type (optional)", False),
                  ("from", "From (optional)", False), ("to", "To (optional)", False)],
        "crm": [("crmid", "CRM code", True), ("element", "Element", True),
                ("certified", "Certified value", True),
                ("sd", "Standard deviation", False), ("unit", "Unit", False),
                ("method", "Method", False)],
        "pairs": [("sampleid", "Original sample ID", True),
                  ("dupid", "Duplicate sample ID", True),
                  ("type", "Duplicate type", False)],
        "umpire": [("sampleid", "Sample ID", True), ("lab", "Umpire laboratory",
                                                     False),
                   ("batch", "Batch / job", False), ("date", "Date", False)],
    }
    TITLES = {"assay": "ASSAY / RESULTS TABLE",
              "crm": "CRM CERTIFICATE TABLE",
              "pairs": "DUPLICATE PAIR TABLE",
              "umpire": "CHECK / UMPIRE ASSAY TABLE  (second laboratory)"}

    def __init__(self, master, kind, path, header, rows, delim, suggested=""):
        super().__init__(master)
        self.title(f"{APP_NAME} -- map {kind} columns")
        self.configure(bg=BG1)
        self.transient(master)
        self.grab_set()
        self.kind, self.path, self.header = kind, path, header
        self.rows, self.delim = rows, delim
        self.result = None
        self._role_vars = {}
        self._el_vars = {}
        self._dl_vars = {}
        self._type_vars = {}

        top = ttk.Frame(self, style="Head.TFrame", padding=(14, 10))
        top.pack(fill="x")
        ttk.Label(top, text=self.TITLES[kind], style="Head.TLabel").pack(anchor="w")
        ttk.Label(self, text=f"{os.path.basename(path)}   --   {len(rows)} rows, "
                             f"{len(header)} columns",
                  style="Dim.TLabel").pack(anchor="w", padx=14, pady=(6, 2))

        body = ttk.Frame(self, style="Panel.TFrame", padding=(14, 8))
        body.pack(fill="both", expand=True)

        nf = ttk.Frame(body, style="Panel.TFrame")
        nf.pack(fill="x", pady=(0, 8))
        ttk.Label(nf, text="Table name", style="Sec.TLabel").pack(side="left")
        self.name_var = tk.StringVar(
            value=suggested or os.path.splitext(os.path.basename(path))[0].upper())
        ttk.Entry(nf, textvariable=self.name_var, width=26).pack(side="left", padx=8)

        box = ttk.Labelframe(body, text="  Column mapping  ", padding=10)
        box.pack(fill="x")
        taken = []
        for i, (role, label, req) in enumerate(self.ROLES[kind]):
            g = guess_role(header, role, taken)
            if g:
                taken.append(g)
            v = tk.StringVar(value=g)
            self._role_vars[role] = v
            ttk.Label(box, text=label + (" *" if req else ""),
                      style="Sec.TLabel" if req else "TLabel").grid(
                row=i % 6, column=(i // 6) * 2, sticky="w", pady=3, padx=(0, 8))
            ttk.Combobox(box, textvariable=v, values=[""] + list(header),
                         state="readonly", width=26).grid(
                row=i % 6, column=(i // 6) * 2 + 1, sticky="w", padx=(0, 20))

        if kind == "assay":
            self._build_types(body)
            self._build_elements(body)
        elif kind == "umpire":
            ttk.Label(body, text="Element columns are matched to the primary "
                                 "table by name; a laboratory suffix such as "
                                 "Cu_pct_UM is matched to Cu_pct automatically.",
                      style="Dim.TLabel").pack(anchor="w", pady=(8, 0))
            self._build_elements(body)

        bar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 12))
        bar.pack(fill="x")
        ttk.Label(bar, text="* required", style="Dim.TLabel").pack(side="left")
        ttk.Button(bar, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bar, text="Import", style="Accent.TButton",
                   command=self._ok).pack(side="right")

        self.update_idletasks()
        self.minsize(940, 480)
        self.wait_window(self)

    # -- sample type classification ---------------------------------------
    def _build_types(self, parent):
        box = ttk.Labelframe(parent, text="  Sample types  ", padding=10)
        box.pack(fill="x", pady=8)
        self._type_box = box
        ttk.Label(box, text="Tell GEOQAQC what each code in the sample-type column "
                            "means. The guesses below come from the usual industry "
                            "abbreviations -- correct anything that is wrong.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 6))
        self._type_holder = ttk.Frame(box, style="Panel.TFrame")
        self._type_holder.pack(fill="x")
        self._role_vars["type"].trace_add("write", lambda *_: self._refresh_types())
        self._refresh_types()

    def _refresh_types(self):
        for w in self._type_holder.winfo_children():
            w.destroy()
        self._type_vars = {}
        col = self._role_vars["type"].get()
        if not col or col not in self.header:
            ttk.Label(self._type_holder,
                      text="No sample-type column mapped. Every row will be treated "
                           "as a normal sample unless a CRM code or parent ID "
                           "identifies it.", style="Dim.TLabel").pack(anchor="w")
            return
        i = self.header.index(col)
        codes = []
        for r in self.rows:
            v = str(r[i]).strip() if i < len(r) else ""
            if v and v not in codes:
                codes.append(v)
            if len(codes) > 40:
                break
        counts = {}
        for r in self.rows:
            v = str(r[i]).strip() if i < len(r) else ""
            counts[v] = counts.get(v, 0) + 1
        for n, code in enumerate(sorted(codes)):
            row = ttk.Frame(self._type_holder, style="Panel.TFrame")
            row.grid(row=n % 8, column=(n // 8) * 2, sticky="w", pady=1, padx=(0, 16))
            ttk.Label(row, text=f"{code[:22]:<22} ({counts.get(code, 0)})",
                      style="Mono.TLabel").pack(side="left")
            v = tk.StringVar(value=classify_type(code))
            self._type_vars[code] = v
            ttk.Combobox(row, textvariable=v, values=SAMPLE_TYPES,
                         state="readonly", width=13).pack(side="left", padx=6)

    # -- element flagging --------------------------------------------------
    def _build_elements(self, parent):
        box = ttk.Labelframe(parent, text="  Element columns  ", padding=10)
        box.pack(fill="both", expand=True, pady=(0, 4))
        ttk.Label(box, text="Tick every column that holds an analytical result. "
                            "A detection limit is optional: leave it blank and "
                            "GEOQAQC infers it from the smallest '<' value.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 6))
        bb = ttk.Frame(box, style="Panel.TFrame")
        bb.pack(fill="x", pady=(0, 6))
        ttk.Button(bb, text="Select all numeric", width=18,
                   command=lambda: self._set_all(True)).pack(side="left", padx=2)
        ttk.Button(bb, text="Clear all", width=12,
                   command=lambda: self._set_all(False)).pack(side="left", padx=2)

        canvas = tk.Canvas(box, bg=BG1, highlightthickness=0, height=170)
        sb = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        holder = ttk.Frame(canvas, style="Panel.TFrame")
        holder.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=holder, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        mapped = {v.get() for v in self._role_vars.values() if v.get()}
        n = 0
        for c in self.header:
            if c in mapped:
                continue
            vals = self.col_values(c)
            num = looks_numeric(vals)
            row = ttk.Frame(holder, style="Panel.TFrame")
            row.grid(row=n % 12, column=n // 12, sticky="w", padx=(0, 22), pady=1)
            bv = tk.BooleanVar(value=num)
            self._el_vars[c] = bv
            ttk.Checkbutton(row, text=f"{c[:18]:<18}", variable=bv).pack(side="left")
            dv = tk.StringVar(value="")
            self._dl_vars[c] = dv
            ttk.Label(row, text="DL", style="Dim.TLabel").pack(side="left", padx=(4, 2))
            ttk.Entry(row, textvariable=dv, width=8).pack(side="left")
            n += 1

    def col_values(self, colname):
        if colname not in self.header:
            return []
        i = self.header.index(colname)
        return [r[i] if i < len(r) else "" for r in self.rows]

    def _set_all(self, val):
        for c, v in self._el_vars.items():
            v.set(val and looks_numeric(self.col_values(c)))

    def _ok(self):
        mapping = {}
        for role, label, req in self.ROLES[self.kind]:
            col = self._role_vars[role].get().strip()
            if req and not col:
                messagebox.showwarning(APP_NAME, f"'{label}' must be mapped.",
                                       parent=self)
                return
            if col:
                mapping[role] = col
        t = DataTable(self.kind, self.name_var.get().strip() or self.kind.upper(),
                      self.path, self.header, self.rows, self.delim)
        t.mapping = mapping
        if self.kind == "umpire":
            t.value_cols = [(c, "numeric") for c, v in self._el_vars.items()
                            if v.get()]
            if not t.value_cols:
                messagebox.showwarning(APP_NAME, "Tick at least one element "
                                                 "column.", parent=self)
                return
        if self.kind == "assay":
            t.value_cols = [(c, "numeric") for c, v in self._el_vars.items() if v.get()]
            if not t.value_cols:
                messagebox.showwarning(APP_NAME, "Tick at least one element column.",
                                       parent=self)
                return
            t.type_map = {k: v.get() for k, v in self._type_vars.items()}
            for c, v in self._dl_vars.items():
                d = fnum(v.get())
                if d is not None:
                    t.dl[c] = d
        self.result = t
        self.destroy()


class ExportDialog(tk.Toplevel):
    def __init__(self, master, default_base="qaqc"):
        super().__init__(master)
        self.title(f"{APP_NAME} -- export")
        self.configure(bg=BG1)
        self.transient(master)
        self.grab_set()
        self.result = None
        ttk.Label(self, text="  EXPORT QA/QC RESULTS", style="Head.TLabel").pack(
            fill="x", pady=(10, 8))
        f = ttk.Frame(self, style="Panel.TFrame", padding=(14, 6))
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Folder", style="Sec.TLabel").grid(row=0, column=0, sticky="w")
        self.folder = tk.StringVar(value=os.path.expanduser("~"))
        ttk.Entry(f, textvariable=self.folder, width=52).grid(row=0, column=1, padx=8)
        ttk.Button(f, text="Browse", command=self._browse).grid(row=0, column=2)
        ttk.Label(f, text="File prefix", style="Sec.TLabel").grid(
            row=1, column=0, sticky="w", pady=8)
        self.base = tk.StringVar(value=default_base)
        ttk.Entry(f, textvariable=self.base, width=52).grid(row=1, column=1, padx=8)
        ttk.Label(f, text="The protocol file records every formula, threshold and "
                          "setting used for this run, so the export is reproducible.",
                  style="Dim.TLabel", wraplength=520, justify="left").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))
        bar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 12))
        bar.pack(fill="x")
        ttk.Button(bar, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bar, text="Export", style="Accent.TButton",
                   command=self._ok).pack(side="right")
        self.update_idletasks()
        self.wait_window(self)

    def _browse(self):
        p = filedialog.askdirectory(parent=self)
        if p:
            self.folder.set(p)

    def _ok(self):
        if not os.path.isdir(self.folder.get()):
            messagebox.showwarning(APP_NAME, "Choose a valid folder.", parent=self)
            return
        self.result = (self.folder.get(), self.base.get())
        self.destroy()


# ===========================================================================
#  Main window
# ===========================================================================
class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VER}  --  {APP_SUB}")
        self.geometry("1460x900")
        self.minsize(1160, 720)
        self.configure(bg=BG0)
        try:
            self.state("zoomed")
        except tk.TclError:
            pass
        apply_theme(self)

        self.project = Project()
        self.F = FormulaBook(DEFAULT_FORMULAS)
        self.C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
        self.settings = dict(DEFAULT_SETTINGS)
        self._svars = {}
        self._fvars = {}
        self._cvars = {}

        self._build_header()
        self._build_body()
        self._build_status()
        self.log(f"{APP_NAME} {APP_VER} ready.")
        self.log("Step 1 -- import the assay / results table to begin.")
        self._sync()

    # ---------------- layout ------------------------------------------------
    def _build_header(self):
        hd = tk.Frame(self, bg=BG0, height=68)
        hd.pack(fill="x", side="top")
        hd.pack_propagate(False)
        cv = tk.Canvas(hd, width=46, height=46, bg=BG0, highlightthickness=0)
        cv.pack(side="left", padx=(16, 12), pady=11)
        draw_logo(cv, 46, 46)
        tl = tk.Frame(hd, bg=BG0)
        tl.pack(side="left", pady=12)
        tk.Label(tl, text=APP_NAME, bg=BG0, fg=FG, font=UI_TITLE,
                 anchor="w").pack(anchor="w", pady=(0, 1))
        tk.Label(tl, text=APP_SUB.upper(), bg=BG0, fg=ACCENT, anchor="w",
                 font=("Segoe UI", 7, "bold")).pack(anchor="w")

        self.badge = tk.Label(hd, text="  NOT ANALYSED  ", bg=BG2, fg=FG_DIM,
                              font=("Segoe UI", 11, "bold"), padx=10, pady=6)
        self.badge.pack(side="left", padx=26)

        rb = tk.Frame(hd, bg=BG0)
        rb.pack(side="right", padx=14)
        ttk.Button(rb, text="Load session", command=self.load_session,
                   width=13).pack(side="left", padx=3)
        ttk.Button(rb, text="Save session", command=self.save_session,
                   width=13).pack(side="left", padx=3)
        ttk.Button(rb, text="Export results", command=self.do_export,
                   width=14).pack(side="left", padx=3)
        self.btn_run = ttk.Button(rb, text="RUN QA/QC", style="Accent.TButton",
                                  command=self.do_analyse)
        self.btn_run.pack(side="left", padx=(10, 0))
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

    def _build_body(self):
        pw = tk.PanedWindow(self, orient="horizontal", bg=BG0, sashwidth=4,
                            bd=0, sashrelief="flat")
        pw.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(pw, style="Panel.TFrame", padding=0)
        pw.add(left, minsize=300, width=330)

        tk.Label(left, text="  DATA", bg=BG2, fg=ACCENT, font=UI_B,
                 anchor="w", pady=7).pack(fill="x")
        sf = ttk.Frame(left, style="Panel.TFrame", padding=(10, 10))
        sf.pack(fill="x")
        self.step_btns = {}
        for key, num, txt in [("assay", "1", "Import Assay / Results"),
                              ("crm", "2", "Import CRM Certificates"),
                              ("pairs", "3", "Import Duplicate Pairs"),
                              ("umpire", "4", "Import Check / Umpire Assays")]:
            b = ttk.Button(sf, text=f"   {num}.  {txt}", style="Step.TButton",
                           command=lambda k=key: self.do_import(k))
            b.pack(fill="x", pady=2)
            self.step_btns[key] = b
        ttk.Label(sf, text="Only the assay table is required. Certificates enable\n"
                           "CRM accuracy; a pair table is only needed when the\n"
                           "duplicates carry no parent-sample column. Umpire\n"
                           "results can come as a second-laboratory file here, or\n"
                           "as rows typed CHECK / UMPIRE in the assay table.",
                  style="Dim.TLabel", justify="left").pack(anchor="w", pady=(6, 0))

        ttk.Separator(left).pack(fill="x", pady=4)
        tk.Label(left, text="  PROJECT", bg=BG2, fg=ACCENT, font=UI_B,
                 anchor="w", pady=7).pack(fill="x")
        tf = ttk.Frame(left, style="Panel.TFrame")
        tf.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree = ttk.Treeview(tf, columns=("info",), show="tree headings",
                                 height=16, selectmode="browse")
        self.tree.heading("#0", text="Object")
        self.tree.heading("info", text="Count / Status")
        self.tree.column("#0", width=180, anchor="w")
        self.tree.column("info", width=110, anchor="e")
        tsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tsb.pack(side="right", fill="y")
        self.tree.tag_configure("root", foreground=ACCENT, font=UI_B)
        self.tree.tag_configure("empty", foreground=FG_DIM)
        self.tree.tag_configure("ok", foreground=FG)

        bf = ttk.Frame(left, style="Panel.TFrame", padding=(6, 0, 6, 8))
        bf.pack(fill="x")
        ttk.Button(bf, text="Remove selected",
                   command=self.remove_selected).pack(fill="x")

        right = ttk.Frame(pw, style="Dark.TFrame")
        pw.add(right, minsize=680)
        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True)

        self._tab_scorecard()
        self._tab_crm()
        self._tab_blank()
        self._tab_dup()
        self._tab_precision()
        self._tab_umpire()
        self._tab_insertion()
        self._tab_formulas()
        self._tab_criteria()
        self._tab_settings()
        self._tab_log()

    # -------- generic pieces ------------------------------------------------
    def _chart_pane(self, parent):
        holder = ttk.Frame(parent, style="Panel.TFrame")
        holder.pack(fill="both", expand=True)
        ch = Chart(holder)
        ch.pack(fill="both", expand=True, padx=4, pady=4)
        return ch

    def _grid(self, parent, cols, widths, height=None):
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=True)
        kw = {"height": height} if height else {}
        tv = ttk.Treeview(holder, columns=cols, show="headings", **kw)
        for c, w in zip(cols, widths):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor="w")
        vs = ttk.Scrollbar(holder, orient="vertical", command=tv.yview)
        hs = ttk.Scrollbar(holder, orient="horizontal", command=tv.xview)
        tv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tv.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        for r, c in RATING_COLOR.items():
            tv.tag_configure(r, foreground=c)
        tv.tag_configure("FAIL", foreground=C_ERR)
        tv.tag_configure("WARN", foreground=C_WARN)
        tv.tag_configure("OK", foreground=C_OK)
        tv.tag_configure("ERROR", foreground=C_ERR)
        tv.tag_configure("WARNING", foreground=C_WARN)
        return tv

    # -------- scorecard -----------------------------------------------------
    def _tab_scorecard(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=10)
        self.nb.add(f, text=" Scorecard ")
        self.sc_hdr = tk.Label(f, text="Import data and press RUN QA/QC.",
                               bg=BG1, fg=FG_DIM, font=MONO, anchor="w",
                               justify="left")
        self.sc_hdr.pack(fill="x", pady=(0, 8))
        self.sctree = self._grid(
            f, ("Section", "Subject", "Element", "n", "Statistic", "Value",
                "Criterion", "Rating"),
            (110, 120, 80, 60, 190, 90, 210, 110))

    # -------- CRM -----------------------------------------------------------
    def _tab_crm(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=8)
        self.nb.add(f, text=" Standards ")
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="CRM / element", style="Sec.TLabel").pack(side="left")
        self.crm_sel = tk.StringVar()
        self.crm_cb = ttk.Combobox(bar, textvariable=self.crm_sel, state="readonly",
                                   width=34)
        self.crm_cb.pack(side="left", padx=8)
        self.crm_cb.bind("<<ComboboxSelected>>", lambda e: self.render_crm())
        ttk.Label(bar, text="Chart", style="Sec.TLabel").pack(side="left", padx=(14, 0))
        self.crm_chart = tk.StringVar(value="Control chart")
        cb = ttk.Combobox(bar, textvariable=self.crm_chart, state="readonly", width=24,
                          values=["Control chart", "Bias sequence", "Z-score distribution"])
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self.render_crm())
        ttk.Button(bar, text="Save chart", command=lambda: self.save_chart(self.crm_ch)
                   ).pack(side="right")
        self.crm_lbl = tk.Label(f, text="", bg=BG1, fg=FG_DIM, font=MONO,
                                anchor="w", justify="left")
        self.crm_lbl.pack(fill="x", pady=(0, 4))
        pane = tk.PanedWindow(f, orient="vertical", bg=BG1, sashwidth=4, bd=0)
        pane.pack(fill="both", expand=True)
        top = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(top, minsize=260, height=400)
        self.crm_ch = self._chart_pane(top)
        bot = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(bot, minsize=110)
        self.crmtree = self._grid(
            bot, ("Sample ID", "Batch", "Sequence", "Measured", "Certified",
                  "Bias %", "Z-score", "Status", "Rule violations"),
            (140, 100, 80, 100, 100, 90, 90, 70, 320))

    # -------- blanks --------------------------------------------------------
    def _tab_blank(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=8)
        self.nb.add(f, text=" Blanks ")
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Element", style="Sec.TLabel").pack(side="left")
        self.bl_sel = tk.StringVar()
        self.bl_cb = ttk.Combobox(bar, textvariable=self.bl_sel, state="readonly",
                                  width=20)
        self.bl_cb.pack(side="left", padx=8)
        self.bl_cb.bind("<<ComboboxSelected>>", lambda e: self.render_blank())
        ttk.Button(bar, text="Save chart", command=lambda: self.save_chart(self.bl_ch)
                   ).pack(side="right")
        self.bl_lbl = tk.Label(f, text="", bg=BG1, fg=FG_DIM, font=MONO,
                               anchor="w", justify="left")
        self.bl_lbl.pack(fill="x", pady=(0, 4))
        pane = tk.PanedWindow(f, orient="vertical", bg=BG1, sashwidth=4, bd=0)
        pane.pack(fill="both", expand=True)
        top = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(top, minsize=240, height=380)
        self.bl_ch = self._chart_pane(top)
        bot = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(bot, minsize=110)
        self.bltree = self._grid(
            bot, ("Sample ID", "Batch", "Sequence", "Value", "x DL",
                  "Preceding Sample", "Preceding Value", "Carry-over %", "Status"),
            (140, 100, 80, 100, 80, 150, 120, 110, 70))

    # -------- duplicates ----------------------------------------------------
    def _tab_dup(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=8)
        self.nb.add(f, text=" Duplicates ")
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Set", style="Sec.TLabel").pack(side="left")
        self.dup_sel = tk.StringVar()
        self.dup_cb = ttk.Combobox(bar, textvariable=self.dup_sel, state="readonly",
                                   width=32)
        self.dup_cb.pack(side="left", padx=8)
        self.dup_cb.bind("<<ComboboxSelected>>",
                         lambda e: self._dup_groups_changed())
        ttk.Label(bar, text="Method", style="Sec.TLabel").pack(side="left", padx=(14, 0))
        self.dup_chart = tk.StringVar(value="Rank-HARD")
        cb = ttk.Combobox(bar, textvariable=self.dup_chart, state="readonly", width=32,
                          values=["Rank-HARD", "Original vs duplicate scatter",
                                  "Q-Q plot", "Relative difference vs grade",
                                  "HARD distribution", "Compare groups (bar)"])
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self.render_dup())
        ttk.Button(bar, text="Save chart", command=lambda: self.save_chart(self.dup_ch)
                   ).pack(side="right")

        bar2 = ttk.Frame(f)
        bar2.pack(fill="x", pady=(0, 6))
        ttk.Label(bar2, text="Group by", style="Sec.TLabel").pack(side="left")
        self.dup_groupby = tk.StringVar(value=GROUP_NONE)
        gb = ttk.Combobox(bar2, textvariable=self.dup_groupby, state="readonly",
                          width=18, values=GROUP_CHOICES)
        gb.pack(side="left", padx=8)
        gb.bind("<<ComboboxSelected>>", lambda e: self._dup_groups_changed())
        ttk.Label(bar2, text="Show", style="Sec.TLabel").pack(side="left", padx=(14, 0))
        self.dup_group = tk.StringVar(value="All groups")
        self.dup_group_cb = ttk.Combobox(bar2, textvariable=self.dup_group,
                                         state="readonly", width=26,
                                         values=["All groups"])
        self.dup_group_cb.pack(side="left", padx=8)
        self.dup_group_cb.bind("<<ComboboxSelected>>", lambda e: self.render_dup())
        ttk.Label(bar2, text="Charts and statistics recompute for the selected "
                            "group, so a bad hole or batch stops hiding inside "
                            "the project average.",
                  style="Dim.TLabel").pack(side="left", padx=12)
        self.dup_lbl = tk.Label(f, text="", bg=BG1, fg=FG_DIM, font=MONO,
                                anchor="w", justify="left")
        self.dup_lbl.pack(fill="x", pady=(0, 4))
        pane = tk.PanedWindow(f, orient="vertical", bg=BG1, sashwidth=4, bd=0)
        pane.pack(fill="both", expand=True)
        top = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(top, minsize=240, height=380)
        self.dup_ch = self._chart_pane(top)
        bot = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(bot, minsize=110)
        self.duptree = self._grid(
            bot, ("Original", "Duplicate", "Group", "Value 1", "Value 2", "Mean",
                  "RD %", "ARD %", "HARD %", "HRD %", "CV %", "Precision 95 %"),
            (130, 130, 110, 90, 90, 90, 80, 80, 80, 80, 80, 110))
        self.dupgrouptree = self._grid(
            bot, ("Group", "n pairs", "P90 HARD %", "Median HARD %", "Mean RD %",
                  "Pooled RP %", "r", "Rating"),
            (170, 80, 110, 120, 100, 110, 90, 110))
        self.dupgrouptree.master.pack_forget()

    # -------- precision -----------------------------------------------------
    def _tab_precision(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=8)
        self.nb.add(f, text=" Thompson-Howarth ")
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Set", style="Sec.TLabel").pack(side="left")
        self.th_sel = tk.StringVar()
        self.th_cb = ttk.Combobox(bar, textvariable=self.th_sel, state="readonly",
                                  width=32)
        self.th_cb.pack(side="left", padx=8)
        self.th_cb.bind("<<ComboboxSelected>>", lambda e: self.render_th())
        ttk.Label(bar, text="Chart", style="Sec.TLabel").pack(side="left", padx=(14, 0))
        self.th_chart = tk.StringVar(value="Precision curve")
        cb = ttk.Combobox(bar, textvariable=self.th_chart, state="readonly", width=28,
                          values=["Precision curve", "Binned regression"])
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self.render_th())
        ttk.Button(bar, text="Save chart", command=lambda: self.save_chart(self.th_ch)
                   ).pack(side="right")
        self.th_lbl = tk.Label(f, text="", bg=BG1, fg=FG_DIM, font=MONO,
                               anchor="w", justify="left")
        self.th_lbl.pack(fill="x", pady=(0, 4))
        pane = tk.PanedWindow(f, orient="vertical", bg=BG1, sashwidth=4, bd=0)
        pane.pack(fill="both", expand=True)
        top = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(top, minsize=240, height=400)
        self.th_ch = self._chart_pane(top)
        bot = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(bot, minsize=100)
        self.thtree = self._grid(
            bot, ("Bin", "n", "Mean concentration", "Mean abs difference"),
            (80, 70, 190, 190))

    # -------- insertion -----------------------------------------------------
    def _tab_umpire(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=8)
        self.nb.add(f, text=" Check / Umpire ")
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Element", style="Sec.TLabel").pack(side="left")
        self.ump_sel = tk.StringVar()
        self.ump_cb = ttk.Combobox(bar, textvariable=self.ump_sel, state="readonly",
                                   width=20)
        self.ump_cb.pack(side="left", padx=8)
        self.ump_cb.bind("<<ComboboxSelected>>",
                         lambda e: self._ump_groups_changed())
        ttk.Label(bar, text="Chart", style="Sec.TLabel").pack(side="left", padx=(14, 0))
        self.ump_chart = tk.StringVar(value="Q-Q plot")
        cb = ttk.Combobox(bar, textvariable=self.ump_chart, state="readonly", width=30,
                          values=["Q-Q plot", "Primary vs umpire scatter",
                                  "Relative bias vs grade",
                                  "Bias by grade quartile", "Ranked ratio"])
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self.render_umpire())
        ttk.Button(bar, text="Save chart",
                   command=lambda: self.save_chart(self.ump_ch)).pack(side="right")

        bar2 = ttk.Frame(f)
        bar2.pack(fill="x", pady=(0, 6))
        ttk.Label(bar2, text="Group by", style="Sec.TLabel").pack(side="left")
        self.ump_groupby = tk.StringVar(value=GROUP_NONE)
        gb = ttk.Combobox(bar2, textvariable=self.ump_groupby, state="readonly",
                          width=18, values=GROUP_CHOICES)
        gb.pack(side="left", padx=8)
        gb.bind("<<ComboboxSelected>>", lambda e: self._ump_groups_changed())
        ttk.Label(bar2, text="Show", style="Sec.TLabel").pack(side="left", padx=(14, 0))
        self.ump_group = tk.StringVar(value="All groups")
        self.ump_group_cb = ttk.Combobox(bar2, textvariable=self.ump_group,
                                         state="readonly", width=26,
                                         values=["All groups"])
        self.ump_group_cb.pack(side="left", padx=8)
        self.ump_group_cb.bind("<<ComboboxSelected>>",
                               lambda e: self.render_umpire())
        ttk.Label(bar2, text="An inter-laboratory bias is often confined to one "
                            "hole, one batch or one drilling method. Group the "
                            "pairs to find out which.",
                  style="Dim.TLabel").pack(side="left", padx=12)

        self.ump_lbl = tk.Label(f, text="", bg=BG1, fg=FG_DIM, font=MONO,
                                anchor="w", justify="left")
        self.ump_lbl.pack(fill="x", pady=(0, 4))
        pane = tk.PanedWindow(f, orient="vertical", bg=BG1, sashwidth=4, bd=0)
        pane.pack(fill="both", expand=True)
        top = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(top, minsize=240, height=380)
        self.ump_ch = self._chart_pane(top)
        bot = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(bot, minsize=110)
        self.umptree = self._grid(
            bot, ("Sample ID", "Group", "Primary", "Umpire", "Difference",
                  "Bias %", "Ratio", "HARD %"),
            (200, 120, 110, 110, 110, 100, 100, 100))

    def _tab_insertion(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=8)
        self.nb.add(f, text=" Insertion ")
        ttk.Label(f, text="Control sample insertion rates against the 5 % per class "
                          "convention (one in twenty). Below 2 % the control "
                          "population is too small to support a statistical "
                          "statement about the data.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 6))
        pane = tk.PanedWindow(f, orient="vertical", bg=BG1, sashwidth=4, bd=0)
        pane.pack(fill="both", expand=True)
        top = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(top, minsize=220, height=360)
        self.ins_ch = self._chart_pane(top)
        bot = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(bot, minsize=110)
        self.instree = self._grid(
            bot, ("Sample type", "Count", "Insertion rate %", "One in every",
                  "Rating"), (170, 100, 150, 140, 130))

    # -------- formulas ------------------------------------------------------
    def _tab_formulas(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=10)
        self.nb.add(f, text=" Formulas ")
        ttk.Label(f, text="Every quantity GEOQAQC computes is defined here. Edit any "
                          "expression and press Apply; the analysis then uses your "
                          "definition. Expressions are saved with the session, so a "
                          "project can carry its own agreed protocol.",
                  style="Dim.TLabel", justify="left").pack(anchor="w", pady=(0, 8))
        bb = ttk.Frame(f, style="Panel.TFrame")
        bb.pack(fill="x", pady=(0, 6))
        ttk.Button(bb, text="Apply formulas", style="Accent.TButton",
                   command=self.apply_formulas).pack(side="left")
        ttk.Button(bb, text="Restore defaults",
                   command=self.reset_formulas).pack(side="left", padx=6)
        ttk.Label(bb, text="allowed: + - * / ** ( )  abs sqrt log log10 exp min max "
                           "round floor ceil pow",
                  style="Dim.TLabel").pack(side="left", padx=14)

        canvas = tk.Canvas(f, bg=BG1, highlightthickness=0)
        sb = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        holder = ttk.Frame(canvas, style="Panel.TFrame")
        holder.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=holder, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        group = None
        for key, d in self.F.defs.items():
            if d["group"] != group:
                group = d["group"]
                tk.Label(holder, text=f"  {group}", bg=BG2, fg=ACCENT, font=UI_B,
                         anchor="w", pady=5, width=150).pack(fill="x", pady=(10, 4))
            row = ttk.Frame(holder, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=d["label"], style="Sec.TLabel", width=38,
                      anchor="w").pack(side="left")
            v = tk.StringVar(value=d["expr"])
            self._fvars[key] = v
            ttk.Entry(row, textvariable=v, width=52).pack(side="left", padx=6)
            ttk.Label(holder, text=f"      {d['vars']}", style="Dim.TLabel",
                      justify="left").pack(anchor="w")
            ttk.Label(holder, text=f"      {d['note']}", style="Dim.TLabel",
                      wraplength=980, justify="left").pack(anchor="w", pady=(0, 4))

    # -------- criteria ------------------------------------------------------
    def _tab_criteria(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=10)
        self.nb.add(f, text=" Criteria ")
        ttk.Label(f, text="The rating bands. Five boundaries produce the six classes. "
                          "Defaults follow common international reporting practice; "
                          "replace them with your own protocol where you have one.",
                  style="Dim.TLabel", justify="left").pack(anchor="w", pady=(0, 6))
        bb = ttk.Frame(f, style="Panel.TFrame")
        bb.pack(fill="x", pady=(0, 6))
        ttk.Button(bb, text="Apply criteria", style="Accent.TButton",
                   command=self.apply_criteria).pack(side="left")
        ttk.Button(bb, text="Restore defaults",
                   command=self.reset_criteria).pack(side="left", padx=6)

        hdr = ttk.Frame(f, style="Panel.TFrame")
        hdr.pack(fill="x", pady=(6, 2))
        ttk.Label(hdr, text="criterion", style="Sec.TLabel", width=42,
                  anchor="w").pack(side="left")
        for name in RATING_ORDER[:5]:
            tk.Label(hdr, text=name, bg=BG1, fg=RATING_COLOR[name], font=MONO,
                     width=11).pack(side="left", padx=2)
        tk.Label(hdr, text=R_VBAD, bg=BG1, fg=RATING_COLOR[R_VBAD],
                 font=MONO).pack(side="left", padx=8)

        canvas = tk.Canvas(f, bg=BG1, highlightthickness=0)
        sb = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        holder = ttk.Frame(canvas, style="Panel.TFrame")
        holder.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=holder, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        group = None
        for key, d in self.C.items():
            if d["group"] != group:
                group = d["group"]
                tk.Label(holder, text=f"  {group}", bg=BG2, fg=ACCENT, font=UI_B,
                         anchor="w", pady=5, width=150).pack(fill="x", pady=(10, 4))
            row = ttk.Frame(holder, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            arrow = "lower is better" if d["dir"] == "low" else "higher is better"
            ttk.Label(row, text=f"{d['label']} [{d['unit']}]", style="Sec.TLabel",
                      width=42, anchor="w").pack(side="left")
            vs = []
            for c in d["cuts"]:
                v = tk.StringVar(value=f"{c:g}")
                vs.append(v)
                ttk.Entry(row, textvariable=v, width=10).pack(side="left", padx=2)
            self._cvars[key] = vs
            ttk.Label(row, text=arrow, style="Dim.TLabel").pack(side="left", padx=10)
            ttk.Label(holder, text=f"      {d['note']}", style="Dim.TLabel",
                      wraplength=980, justify="left").pack(anchor="w", pady=(0, 4))

    # -------- settings ------------------------------------------------------
    def _tab_settings(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=14)
        self.nb.add(f, text=" Settings ")
        spec = [
            ("Control chart warning limit (SD)", "k_warn",
             "Shewhart warning limit. 2 SD is the international convention."),
            ("Control chart action limit (SD)", "k_fail",
             "Shewhart action limit. A result beyond 3 SD fails the batch."),
            ("Blank contamination limit (x DL)", "k_dl",
             "5 x DL is the strict convention, 10 x DL the tolerant one."),
            ("HARD percentile for acceptance", "hard_pct",
             "Acceptance is normally quoted as the 90th percentile of HARD."),
            ("Thompson-Howarth bin size", "th_group",
             "Pairs per bin. Thompson & Howarth (1978) used 11."),
            ("Report TH precision at (x DL)", "th_at_dl",
             "Concentration at which the precision curve is read and rated."),
            ("Minimum duplicate pairs to rate", "min_pairs",
             "Below this a percentile carries no meaning, so no rating is given."),
            ("Minimum CRM results to rate", "min_crm",
             "Below this the bias and failure statistics are unstable."),
            ("Consecutive same-side run", "run_len",
             "Length of a one-sided run that is reported as a bias, not scatter."),
            ("Below-DL substitution factor", "dl_substitute",
             "If below-DL pairs are kept, replace them by this fraction of the DL."),
        ]
        box = ttk.Labelframe(f, text="  Analysis parameters  ", padding=12)
        box.pack(fill="x")
        for i, (lbl, key, hint) in enumerate(spec):
            v = tk.StringVar(value=str(self.settings[key]))
            self._svars[key] = v
            ttk.Label(box, text=lbl, style="Sec.TLabel").grid(
                row=i, column=0, sticky="w", pady=3)
            ttk.Entry(box, textvariable=v, width=12).grid(
                row=i, column=1, sticky="w", padx=12)
            ttk.Label(box, text=hint, style="Dim.TLabel").grid(
                row=i, column=2, sticky="w")
        box.columnconfigure(2, weight=1)

        box2 = ttk.Labelframe(f, text="  Options  ", padding=12)
        box2.pack(fill="x", pady=12)
        for key, lbl in [
            ("drop_below_dl", "Exclude duplicate pairs where either value is below "
                              "the detection limit  (recommended)"),
            ("log_axis", "Use logarithmic axes on duplicate scatter plots  "
                         "(recommended for grade data)")]:
            v = tk.BooleanVar(value=self.settings[key])
            self._svars[key] = v
            ttk.Checkbutton(box2, text=lbl, variable=v).pack(anchor="w", pady=2)

        ttk.Button(f, text="Apply settings", style="Accent.TButton",
                   command=self.apply_settings).pack(anchor="w")
        ttk.Label(f, text="Changing a setting does not re-run the analysis. "
                          "Apply, then press RUN QA/QC.",
                  style="Dim.TLabel").pack(anchor="w", pady=6)

    def _tab_log(self):
        f = ttk.Frame(self.nb, style="Panel.TFrame", padding=10)
        self.nb.add(f, text=" Log ")
        self.txt = tk.Text(f, bg=BG2, fg=FG, insertbackground=ACCENT, font=MONO,
                           bd=0, wrap="none", padx=10, pady=8)
        sb = ttk.Scrollbar(f, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set, state="disabled")
        self.txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _build_status(self):
        s = tk.Frame(self, bg=BG2, height=26)
        s.pack(fill="x", side="bottom")
        s.pack_propagate(False)
        self.status = tk.Label(s, text="Ready", bg=BG2, fg=FG_DIM, font=MONO,
                               anchor="w")
        self.status.pack(side="left", padx=12)
        tk.Label(s, text=f"{APP_NAME} {APP_VER}", bg=BG2, fg=FG_DIM,
                 font=MONO).pack(side="right", padx=12)

    # ---------------- helpers ----------------------------------------------
    def log(self, msg):
        ts = _dt.datetime.now().strftime("%H:%M:%S")
        self.txt.configure(state="normal")
        self.txt.insert("end", f"[{ts}] {msg}\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")
        self.status.configure(text=str(msg)[:160])
        self.update_idletasks()

    def _sync(self):
        self.tree.delete(*self.tree.get_children())
        root = self.tree.insert("", "end", text="QA/QC Project", values=("",),
                                open=True, tags=("root",))
        p = self.project
        for label, t in (("Assay / results", p.assay), ("CRM certificates", p.crm),
                         ("Duplicate pairs", p.pairs),
                         ("Check / umpire", p.umpire)):
            if t:
                self.tree.insert(root, "end", text=label,
                                 values=(f"{len(t.rows)} rows",), tags=("ok",))
            else:
                self.tree.insert(root, "end", text=label, values=("not loaded",),
                                 tags=("empty",))
        if p.samples:
            n = self.tree.insert(root, "end", text="Samples",
                                 values=(f"{len(p.samples)}",), open=True,
                                 tags=("ok",))
            counts = {}
            for s in p.samples:
                counts[s.stype] = counts.get(s.stype, 0) + 1
            for t in SAMPLE_TYPES:
                if counts.get(t):
                    self.tree.insert(n, "end", text=f"  {t}",
                                     values=(str(counts[t]),), tags=("ok",))
            self.tree.insert(root, "end", text="Elements",
                             values=(f"{len(p.elements)}",), tags=("ok",))
        self.btn_run.configure(state=("normal" if p.assay else "disabled"))
        self.step_btns["assay"].configure(
            text=f"   1.  Assay / Results   [{len(p.assay.rows)} rows]"
            if p.assay else "   1.  Import Assay / Results")
        self.step_btns["crm"].configure(
            text=f"   2.  CRM Certificates   [{len(p.crm.rows)} rows]"
            if p.crm else "   2.  Import CRM Certificates")
        self.step_btns["pairs"].configure(
            text=f"   3.  Duplicate Pairs   [{len(p.pairs.rows)} rows]"
            if p.pairs else "   3.  Import Duplicate Pairs")
        self.step_btns["umpire"].configure(
            text=f"   4.  Check / Umpire   [{len(p.umpire.rows)} rows]"
            if p.umpire else "   4.  Import Check / Umpire Assays")

    def set_badge(self, rating, score=None):
        self.badge.configure(
            text=f"  {rating}  " + (f"({score:.0f}/100)  " if score is not None else ""),
            fg="#12161c" if rating != R_NA else FG_DIM,
            bg=RATING_COLOR.get(rating, BG2))

    # ---------------- import ------------------------------------------------
    def do_import(self, kind):
        p = filedialog.askopenfilename(
            parent=self, title=f"Select the {kind} file",
            filetypes=[("Delimited text", "*.csv *.txt *.tsv"), ("All files", "*.*")])
        if not p:
            return
        try:
            h, r, d = sniff_and_read(p)
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Could not read the file:\n{ex}", parent=self)
            return
        if not h or not r:
            messagebox.showwarning(APP_NAME, "The file has no readable rows.",
                                   parent=self)
            return
        dlg = MappingDialog(self, kind, p, h, r, d)
        if not dlg.result:
            return
        t = dlg.result
        setattr(self.project, kind, t)
        self.project.clear_results()
        self.log(f"Imported {kind}: {t.name} -- {len(t.rows)} rows, "
                 f"{len(t.header)} columns.")
        if kind == "assay":
            self.log(f"  {len(t.value_cols)} element column(s): "
                     + ", ".join(c for c, _ in t.value_cols[:12])
                     + (" ..." if len(t.value_cols) > 12 else ""))
        self._sync()

    def remove_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        label = self.tree.item(sel[0], "text").strip()
        for name, attr in (("Assay / results", "assay"), ("CRM certificates", "crm"),
                           ("Duplicate pairs", "pairs"),
                           ("Check / umpire", "umpire")):
            if label == name and getattr(self.project, attr):
                setattr(self.project, attr, None)
                self.project.clear_results()
                self.log(f"Removed {name}.")
                self._sync()
                return

    # ---------------- settings / formulas / criteria ------------------------
    def apply_settings(self):
        try:
            for k, v in self._svars.items():
                if isinstance(v, tk.BooleanVar):
                    self.settings[k] = v.get()
                else:
                    self.settings[k] = float(v.get())
        except ValueError:
            messagebox.showerror(APP_NAME, "All parameters must be numeric.",
                                 parent=self)
            return
        self.settings["th_group"] = int(self.settings["th_group"])
        self.settings["run_len"] = int(self.settings["run_len"])
        self.settings["min_pairs"] = int(self.settings["min_pairs"])
        self.settings["min_crm"] = int(self.settings["min_crm"])
        self.log("Settings applied.")
        messagebox.showinfo(APP_NAME, "Settings applied. Press RUN QA/QC to "
                                      "re-analyse.", parent=self)

    def apply_formulas(self):
        bad = []
        for key, v in self._fvars.items():
            expr = v.get().strip()
            if expr == self.F.expr(key):
                continue
            try:
                self.F.set_expr(key, expr)
                self.log(f"formula '{self.F.defs[key]['label']}' = {expr}")
            except FormulaError as ex:
                bad.append(f"{self.F.defs[key]['label']}: {ex}")
                v.set(self.F.expr(key))
        if bad:
            messagebox.showerror(APP_NAME, "These formulas were rejected and "
                                           "reverted:\n\n" + "\n".join(bad),
                                 parent=self)
            return
        messagebox.showinfo(APP_NAME, "Formulas applied. Press RUN QA/QC to "
                                      "re-analyse.", parent=self)

    def reset_formulas(self):
        if not messagebox.askyesno(APP_NAME, "Restore every formula to its default?",
                                   parent=self):
            return
        self.F = FormulaBook(DEFAULT_FORMULAS)
        for key, v in self._fvars.items():
            v.set(self.F.expr(key))
        self.log("Formulas restored to defaults.")

    def apply_criteria(self):
        try:
            for key, vs in self._cvars.items():
                cuts = [float(v.get()) for v in vs]
                d = self.C[key]
                ordered = (cuts == sorted(cuts) if d["dir"] == "low"
                           else cuts == sorted(cuts, reverse=True))
                if not ordered:
                    raise ValueError(
                        f"'{d['label']}' -- the five boundaries must run "
                        + ("from tightest to loosest (increasing)."
                           if d["dir"] == "low"
                           else "from best to worst (decreasing)."))
                d["cuts"] = cuts
        except ValueError as ex:
            messagebox.showerror(APP_NAME, str(ex), parent=self)
            return
        self.log("Acceptance criteria applied.")
        messagebox.showinfo(APP_NAME, "Criteria applied. Press RUN QA/QC to "
                                      "re-rate.", parent=self)

    def reset_criteria(self):
        if not messagebox.askyesno(APP_NAME, "Restore every criterion to its "
                                             "default?", parent=self):
            return
        self.C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
        for key, vs in self._cvars.items():
            for v, c in zip(vs, self.C[key]["cuts"]):
                v.set(f"{c:g}")
        self.log("Criteria restored to defaults.")

    # ---------------- run ---------------------------------------------------
    def do_analyse(self):
        if not self.project.assay:
            messagebox.showinfo(APP_NAME, "Import the assay table first.", parent=self)
            return
        self.log("=" * 60)
        try:
            run_analysis(self.project, self.F, self.C, self.settings, log=self.log)
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Analysis failed:\n{ex}", parent=self)
            self.log(f"FAILED: {ex}")
            return
        self.render_all()
        self.nb.select(0)
        self._sync()

    # ---------------- rendering --------------------------------------------
    def render_all(self):
        R = self.project.results
        if not R:
            return
        self.set_badge(R["overall"], R["score"])
        self.render_scorecard()

        keys = [f"{c}  /  {e}" for (c, e) in sorted(R["crm"])]
        self.crm_cb.configure(values=keys)
        if keys and self.crm_sel.get() not in keys:
            self.crm_sel.set(keys[0])
        self.render_crm()

        els = sorted(R["blank"])
        self.bl_cb.configure(values=els)
        if els and self.bl_sel.get() not in els:
            self.bl_sel.set(els[0])
        self.render_blank()

        dkeys = [f"{t}  /  {e}" for (t, e) in sorted(R["dup"])]
        self.dup_cb.configure(values=dkeys)
        if dkeys and self.dup_sel.get() not in dkeys:
            self.dup_sel.set(dkeys[0])
        self._dup_groups_changed()

        tkeys = [f"{t}  /  {e}" for (t, e) in sorted(R["th"])]
        self.th_cb.configure(values=tkeys)
        if tkeys and self.th_sel.get() not in tkeys:
            self.th_sel.set(tkeys[0])
        self.render_th()

        uels = sorted(R.get("umpire", {}))
        self.ump_cb.configure(values=uels)
        if uels and self.ump_sel.get() not in uels:
            self.ump_sel.set(uels[0])
        self._ump_groups_changed()

        self.render_insertion()

    def render_scorecard(self):
        R = self.project.results
        tv = self.sctree
        tv.delete(*tv.get_children())

        def add(sec, subj, el, n, stat, val, crit, rating):
            tv.insert("", "end", tags=(rating,), values=(
                sec, subj, el, n, stat,
                "" if val is None else (f"{val:.3f}" if isinstance(val, float) else val),
                crit, rating))

        for (code, el), rec in sorted(R["crm"].items()):
            add("CRM", code, el, rec["n"], "mean bias %", rec.get("bias"),
                self.C["crm_bias"]["label"], rec["ratings"].get("crm_bias", R_NA))
            if rec.get("fail_pct") is not None:
                add("CRM", code, el, rec["n"],
                    f"failure rate beyond {self.settings['k_fail']:g} SD %",
                    rec["fail_pct"], self.C["crm_fail"]["label"],
                    rec["ratings"].get("crm_fail", R_NA))
            add("CRM", code, el, rec["n"], "observed RSD %", rec.get("rsd_pct"),
                self.C["crm_rsd"]["label"], rec["ratings"].get("crm_rsd", R_NA))
        for el, rec in sorted(R["blank"].items()):
            add("BLANK", "blanks", el, rec["n"], "failure rate %", rec["fail_pct"],
                self.C["blank_fail"]["label"], rec["ratings"].get("blank_fail", R_NA))
            add("BLANK", "blanks", el, rec["n"], "worst blank / DL", rec["max_ratio"],
                self.C["blank_max"]["label"], rec["ratings"].get("blank_max", R_NA))
        ck = {T_FDUP: "fdup_hard90", T_CDUP: "cdup_hard90", T_PDUP: "pdup_hard90"}
        for (dt, el), rec in sorted(R["dup"].items()):
            add(dt, "duplicates", el, rec["n"],
                f"P{rec['hard_pct_used']:g} HARD %", rec.get("hard_p90"),
                self.C[ck[dt]]["label"], rec["ratings"].get(ck[dt], R_NA))
            add(dt, "duplicates", el, rec["n"], "mean RD % (bias)", rec.get("rd_mean"),
                self.C["dup_bias"]["label"], rec["ratings"].get("dup_bias", R_NA))
        for (dt, el), rec in sorted(R["th"].items()):
            add("PRECISION", dt, el, len(rec["bins"]) * rec["group"],
                f"TH precision % at {fmt_num(rec['c_ref'])}",
                rec.get("precision_at_ref"), self.C["th_precision"]["label"],
                rec["ratings"].get("th_precision", R_NA))
        for el, rec in sorted(R.get("umpire", {}).items()):
            add("CHECK / UMPIRE", rec.get("lab") or "umpire lab", el, rec["n"],
                "grade-weighted bias %", rec.get("wbias"),
                self.C["ump_wbias"]["label"], rec["ratings"].get("ump_wbias", R_NA))
            add("CHECK / UMPIRE", rec.get("lab") or "umpire lab", el, rec["n"],
                "worst grade-quartile bias %", rec.get("worst_quartile"),
                self.C["ump_grade_range"]["label"],
                rec["ratings"].get("ump_grade_range", R_NA))
            add("CHECK / UMPIRE", rec.get("lab") or "umpire lab", el, rec["n"],
                f"P{rec['hard_pct_used']:g} inter-lab HARD %", rec.get("hard_p90"),
                self.C["ump_hard90"]["label"],
                rec["ratings"].get("ump_hard90", R_NA))
        for r in R["insertion"]["rows"]:
            add("INSERTION", r["type"], "", r["n"], "insertion rate %", r["pct"],
                self.C["insert_rate"]["label"], r["rating"])

        n_rules = sum(len(rec["rules"]) for rec in R["crm"].values())
        n_fail = sum(rec["n_fail"] for rec in R["blank"].values())
        self.sc_hdr.configure(
            text=(f"OVERALL RATING   {R['overall']}"
                  + (f"   (weighted score {R['score']:.1f} / 100)"
                     if R["score"] is not None else "")
                  + f"\n{len(self.project.samples)} samples   "
                    f"{len(self.project.elements)} element(s)   "
                    f"{len(R['crm'])} CRM/element set(s)   "
                    f"{len(R['dup'])} duplicate set(s)   "
                    f"{n_rules} control-rule violation(s)   "
                    f"{n_fail} failed blank(s)\n"
                    f"analysed {self.project.analysed_at:%Y-%m-%d %H:%M}"),
            fg=RATING_COLOR.get(R["overall"], FG))

    def render_crm(self):
        R = self.project.results
        if not R or not self.crm_sel.get():
            return
        code, el = [s.strip() for s in self.crm_sel.get().split("/")]
        rec = R["crm"].get((code, el))
        if not rec:
            return
        mode = self.crm_chart.get()
        if mode.startswith("Bias"):
            chart_crm_bias(self.crm_ch, rec, self.settings)
        elif mode.startswith("Z-score"):
            chart_crm_zhist(self.crm_ch, rec, self.settings)
        else:
            chart_crm_control(self.crm_ch, rec, self.settings)

        bits = [f"RATING {rec['rating']}", f"n = {rec['n']}"]
        if rec.get("cert") is not None:
            bits.append(f"certified {fmt_num(rec['cert'])}"
                        + (f" +/- {fmt_num(rec['sd'])}" if rec.get("sd") else ""))
        if rec.get("bias") is not None:
            bits.append(f"mean bias {rec['bias']:+.2f} %")
        if rec.get("fail_pct") is not None:
            bits.append(f"beyond {self.settings['k_fail']:g} SD "
                        f"{rec['fail_pct']:.1f} %")
        if rec.get("rsd_pct") is not None:
            bits.append(f"observed RSD {rec['rsd_pct']:.2f} %")
        txt = "     ".join(bits)
        if rec.get("note"):
            txt += "\n" + rec["note"]
        self.crm_lbl.configure(text=txt, fg=RATING_COLOR.get(rec["rating"], FG_DIM))

        by_sample = {}
        for r in rec["rules"]:
            by_sample.setdefault(r["sample"], []).append(f"{r['rule']} {r['desc']}")
        tv = self.crmtree
        tv.delete(*tv.get_children())
        for p in rec["points"]:
            z = p["z"]
            st = ("FAIL" if z is not None and abs(z) > self.settings["k_fail"]
                  else "WARN" if z is not None and abs(z) > self.settings["k_warn"]
                  else "OK")
            tv.insert("", "end", tags=(st,), values=(
                p["sample"], p["batch"], fmt_num(p["order"]), fmt_num(p["value"]),
                fmt_num(rec.get("cert")),
                "" if p["bias"] is None else f"{p['bias']:+.2f}",
                "" if z is None else f"{z:+.2f}", st,
                " | ".join(by_sample.get(p["sample"], []))[:200]))

    def render_blank(self):
        R = self.project.results
        if not R or not self.bl_sel.get():
            return
        rec = R["blank"].get(self.bl_sel.get())
        if not rec:
            return
        chart_blank(self.bl_ch, rec, self.settings)
        self.bl_lbl.configure(
            text=(f"RATING {rec['rating']}     n = {rec['n']}     "
                  f"DL = {fmt_num(rec['dl'])}     limit = "
                  f"{fmt_num(rec['limit'])} ({self.settings['k_dl']:g} x DL)     "
                  f"failures {rec['n_fail']} ({rec['fail_pct']:.1f} %)     "
                  f"worst {rec['max_ratio']:.1f} x DL"),
            fg=RATING_COLOR.get(rec["rating"], FG_DIM))
        tv = self.bltree
        tv.delete(*tv.get_children())
        for p in rec["points"]:
            tv.insert("", "end", tags=("FAIL" if p["fail"] else "OK",), values=(
                p["sample"], p["batch"], fmt_num(p["order"]), fmt_num(p["value"]),
                "" if p["ratio"] is None else f"{p['ratio']:.2f}",
                p["prev_sample"], fmt_num(p["prev_value"]),
                "" if p["carry_pct"] is None else f"{p['carry_pct']:.3f}",
                "FAIL" if p["fail"] else "OK"))

    CRIT_BY_DUP = {T_FDUP: "fdup_hard90", T_CDUP: "cdup_hard90",
                   T_PDUP: "pdup_hard90"}

    def _dup_context(self):
        """(record, group key, group value, filtered rows) for the current
        selection, or None."""
        R = self.project.results
        if not R or not self.dup_sel.get():
            return None
        parts = [x.strip() for x in self.dup_sel.get().rsplit("/", 1)]
        if len(parts) != 2:
            return None
        rec = R["dup"].get((parts[0], parts[1]))
        if not rec:
            return None
        key = GROUP_KEYS.get(self.dup_groupby.get())
        val = self.dup_group.get()
        if not key or val in ("", "All groups"):
            return rec, key, None, rec["rows"]
        return rec, key, val, group_rows(rec["rows"], key, val)

    def _dup_groups_changed(self):
        ctx = self._dup_context()
        key = GROUP_KEYS.get(self.dup_groupby.get())
        vals = ["All groups"]
        if ctx and key:
            vals += group_values(ctx[0]["rows"], key)
        self.dup_group_cb.configure(values=vals)
        if self.dup_group.get() not in vals:
            self.dup_group.set("All groups")
        self.render_dup()

    def render_dup(self):
        ctx = self._dup_context()
        if not ctx:
            return
        rec, key, val, rows = ctx
        dt = rec["type"]
        crit_key = self.CRIT_BY_DUP[dt]
        mode = self.dup_chart.get()

        # a filtered view is a different population, so every statistic and
        # every chart must be recomputed from the subset, not merely masked
        view = dict(rec)
        view["rows"] = rows
        st = dup_stats(rows, self.F, self.C, self.settings, crit_key)
        if st:
            view.update(st)
        view["type"] = dt

        show_groups = mode.startswith("Compare groups") and key
        if show_groups:
            bd = group_breakdown(rec, key, self.F, self.C, self.settings, crit_key)
            chart_group_summary(self.dup_ch, bd, self.dup_groupby.get(),
                                self.settings, self.C[crit_key])
            self.duptree.master.pack_forget()
            self.dupgrouptree.master.pack(fill="both", expand=True)
            gv = self.dupgrouptree
            gv.delete(*gv.get_children())
            for g in bd:
                gv.insert("", "end", tags=(g.get("rating", R_NA),), values=(
                    g["group"], g["n"],
                    "" if g["hard_p90"] is None else f"{g['hard_p90']:.2f}",
                    "" if g["hard_median"] is None else f"{g['hard_median']:.2f}",
                    "" if g["rd_mean"] is None else f"{g['rd_mean']:+.2f}",
                    "" if g["pooled_rp"] is None else f"{g['pooled_rp']:.2f}",
                    "" if g["r"] is None else f"{g['r']:.4f}",
                    g.get("rating", R_NA)))
            worst = bd[0] if bd else None
            self.dup_lbl.configure(
                text=(f"{len(bd)} group(s) by {self.dup_groupby.get().lower()}."
                      + (f"   Worst: {worst['group']} with P{self.settings['hard_pct']:g} "
                         f"HARD {worst['hard_p90']:.2f} % over {worst['n']} pair(s)."
                         if worst else "")
                      + "   Groups with fewer than "
                        f"{self.settings['min_pairs']} pairs are listed but not rated."),
                fg=RATING_COLOR.get(worst.get("rating"), FG_DIM) if worst else FG_DIM)
            return

        self.dupgrouptree.master.pack_forget()
        self.duptree.master.pack(fill="both", expand=True)

        if not rows:
            self.dup_ch.clear()
            self.dup_ch.note("no pairs in this group")
            self.dup_ch.redraw()
            self.duptree.delete(*self.duptree.get_children())
            self.dup_lbl.configure(text="No pairs in the selected group.", fg=FG_DIM)
            return

        if mode.startswith("Original"):
            chart_dup_scatter(self.dup_ch, view, self.settings)
        elif mode.startswith("Q-Q"):
            chart_dup_qq(self.dup_ch, view, self.settings)
        elif mode.startswith("Relative"):
            chart_dup_mean_hrd(self.dup_ch, view, self.settings)
        elif mode.startswith("HARD dist"):
            chart_dup_hist(self.dup_ch, view, self.settings)
        else:
            chart_dup_rank_hard(self.dup_ch, view, self.settings)

        bits = [f"RATING {view['rating']}", f"n = {view['n']} pairs"]
        if val:
            bits.insert(1, f"{self.dup_groupby.get()} = {val}")
        bits += [f"P{view['hard_pct_used']:g} HARD {view['hard_p90']:.2f} %",
                 f"median HARD {view['hard_median']:.2f} %",
                 f"mean RD {view['rd_mean']:+.2f} %"]
        if view.get("pooled_rp") is not None:
            bits.append(f"pooled RP {view['pooled_rp']:.2f} %")
        if view.get("r") is not None:
            bits.append(f"r = {view['r']:.4f}")
        if view.get("rma_b") is not None:
            bits.append(f"RMA slope {view['rma_b']:.4f}")
        txt = "     ".join(bits)
        if view.get("note"):
            txt += "\n" + view["note"]
        self.dup_lbl.configure(text=txt, fg=RATING_COLOR.get(view["rating"], FG_DIM))

        tv = self.duptree
        tv.delete(*tv.get_children())
        for r in rows:
            h = r["hard"]
            tag = "OK" if h is not None and h <= 10 else (
                "WARN" if h is not None and h <= 20 else "FAIL")
            gval = ""
            if key:
                gval = (r.get(key) or "").strip() or "(not recorded)"
            elif r.get("hole"):
                gval = r["hole"]
            tv.insert("", "end", tags=(tag,), values=(
                r["orig"], r["dup"], gval, fmt_num(r["a"]), fmt_num(r["b"]),
                fmt_num(r["mean"]),
                "" if r["rd"] is None else f"{r['rd']:+.2f}",
                "" if r["ard"] is None else f"{r['ard']:.2f}",
                "" if h is None else f"{h:.2f}",
                "" if r["hrd"] is None else f"{r['hrd']:+.2f}",
                "" if r["cv"] is None else f"{r['cv']:.2f}",
                "" if r.get("prec95") is None else f"{r['prec95']:.2f}"))

    def render_th(self):
        R = self.project.results
        if not R or not self.th_sel.get():
            self.th_ch.clear()
            self.th_ch.redraw()
            self.thtree.delete(*self.thtree.get_children())
            why = R.get("th_skipped") if R else None
            if why:
                self.th_lbl.configure(
                    text="Thompson-Howarth could not be fitted to any duplicate "
                         "set:\n" + "\n".join(f"  {d} / {e}: {w}" for d, e, w in why),
                    fg=C_WARN)
            else:
                self.th_lbl.configure(
                    text="No duplicate pairs available for a precision regression.",
                    fg=FG_DIM)
            return
        dt, el = [s.strip() for s in self.th_sel.get().split("/")]
        rec = R["th"].get((dt, el))
        if not rec:
            return
        _ = rec
        if self.th_chart.get().startswith("Binned"):
            chart_th(self.th_ch, rec, self.settings)
        else:
            chart_th_curve(self.th_ch, rec, self.settings)
        txt = (f"RATING {rec['rating']}     bins of {rec['group']} pairs     "
               f"mean|d| = {fmt_num(rec['a_int'])} + {rec['b_slope']:.5f} x c     "
               f"precision at {fmt_num(rec['c_ref'])} = "
               f"{rec['precision_at_ref']:.2f} %")
        txt += (f"     practical detection limit {fmt_num(rec['pdl'])}"
                if rec.get("pdl") else "     practical detection limit not resolvable")
        if rec.get("constrained"):
            txt += ("\nThe unconstrained intercept was negative, which is "
                    "physically impossible, so the model was refitted through "
                    "the origin.")
        if rec.get("clamped"):
            txt += (f"\nThe requested reference concentration "
                    f"{fmt_num(rec['c_requested'])} lies outside the binned range "
                    f"{fmt_num(rec['c_lo'])} - {fmt_num(rec['c_hi'])}. The curve "
                    f"was read at {fmt_num(rec['c_ref'])} instead; reading below "
                    f"the data would be extrapolation.")
        self.th_lbl.configure(text=txt, fg=RATING_COLOR.get(rec["rating"], FG_DIM))
        tv = self.thtree
        tv.delete(*tv.get_children())
        for i, b in enumerate(rec["bins"], start=1):
            tv.insert("", "end", values=(i, b["n"], fmt_num(b["conc"]),
                                         fmt_num(b["dbar"])))

    def _ump_groups_changed(self):
        R = self.project.results
        rec = R.get("umpire", {}).get(self.ump_sel.get()) if R else None
        key = GROUP_KEYS.get(self.ump_groupby.get())
        vals = ["All groups"]
        if rec and key:
            vals += group_values(rec["rows"], key)
        self.ump_group_cb.configure(values=vals)
        if self.ump_group.get() not in vals:
            self.ump_group.set("All groups")
        self.render_umpire()

    def render_umpire(self):
        R = self.project.results
        if not R:
            return
        rec = R.get("umpire", {}).get(self.ump_sel.get())
        if not rec:
            self.ump_ch.clear()
            self.ump_ch.redraw()
            self.umptree.delete(*self.umptree.get_children())
            self.ump_lbl.configure(
                text="No check / umpire pairs found.\n"
                     "Either import a second-laboratory results file with button 4, "
                     "or mark rows in the assay table as CHECK / UMPIRE and give "
                     "each one the parent sample ID it re-assays.",
                fg=FG_DIM)
            return
        # a group filter makes a different population, so re-derive the view
        key = GROUP_KEYS.get(self.ump_groupby.get())
        gval = self.ump_group.get()
        filtered = rec["rows"]
        if key and gval not in ("", "All groups"):
            filtered = group_rows(rec["rows"], key, gval)
        if not filtered:
            self.ump_ch.clear()
            self.ump_ch.note("no pairs in this group")
            self.ump_ch.redraw()
            self.umptree.delete(*self.umptree.get_children())
            self.ump_lbl.configure(text="No pairs in the selected group.", fg=FG_DIM)
            return
        rec = dict(rec)
        if len(filtered) != len(rec["rows"]):
            sp = sum(r["primary"] for r in filtered)
            su = sum(r["umpire"] for r in filtered)
            hh = sorted(r["hard"] for r in filtered if r["hard"] is not None)
            rec["rows"] = filtered
            rec["n"] = len(filtered)
            rec["sum_primary"], rec["sum_umpire"] = sp, su
            rec["wbias"] = self.F.calc("ump_weighted_bias", sum_pr=sp, sum_u=su)
            rec["pbias"] = mean([r["bias"] for r in filtered
                                 if r["bias"] is not None])
            rec["hard_p90"] = pctile(hh, self.settings["hard_pct"])
            rec["hard_median"] = pctile(hh, 50)
            _, ols_b, r_corr = linreg([r["primary"] for r in filtered],
                                      [r["umpire"] for r in filtered])
            rec["r"], rec["ols_b"] = r_corr, ols_b
            rec["rma_a"], rec["rma_b"] = rma([r["primary"] for r in filtered],
                                             [r["umpire"] for r in filtered])
            # statistics that are not meaningful on a filtered subset
            for k in ("ttest", "wilcoxon", "quartiles", "worst_quartile"):
                rec[k] = None
            rec["rating"] = R_NA
            rec["filtered"] = f"{self.ump_groupby.get()} = {gval}"

        mode = self.ump_chart.get()
        if mode.startswith("Primary"):
            chart_ump_scatter(self.ump_ch, rec, self.settings)
        elif mode.startswith("Relative"):
            chart_ump_bias_grade(self.ump_ch, rec, self.settings)
        elif mode.startswith("Bias by"):
            chart_ump_quartile(self.ump_ch, rec, self.settings)
        elif mode.startswith("Ranked"):
            chart_ump_ratio(self.ump_ch, rec, self.settings)
        else:
            chart_ump_qq(self.ump_ch, rec, self.settings)

        bits = [f"RATING {rec['rating']}", f"n = {rec['n']} pairs"]
        if rec.get("filtered"):
            bits.insert(1, rec["filtered"])
        if rec.get("lab"):
            bits.append(f"umpire lab {rec['lab']}")
        if rec.get("wbias") is not None:
            bits.append(f"grade-weighted bias {rec['wbias']:+.2f} %")
        if rec.get("pbias") is not None:
            bits.append(f"mean pair bias {rec['pbias']:+.2f} %")
        bits.append(f"P{rec['hard_pct_used']:g} HARD {rec['hard_p90']:.2f} %")
        if rec.get("r") is not None:
            bits.append(f"r = {rec['r']:.4f}")
        if rec.get("worst_quartile") is not None:
            bits.append(f"worst quartile {rec['worst_quartile']:.2f} %")
        txt = "     ".join(bits)

        tt, wx = rec.get("ttest"), rec.get("wilcoxon")
        if tt and tt.get("p") is not None:
            verdict = ("a real bias, not chance" if tt["p"] < 0.05
                       else "not distinguishable from chance")
            txt += (f"\npaired t = {tt['t']:+.3f} on {tt['df']} df, p = "
                    f"{tt['p']:.4f}  ->  {verdict}")
            if wx and wx.get("p") is not None:
                txt += f"     Wilcoxon p = {wx['p']:.4f}"
            txt += ("\nSignificance is reported but never rated: with enough pairs "
                    "a trivial bias becomes significant, and with few pairs a "
                    "serious one does not. The rating uses the SIZE of the bias.")
        if rec.get("note"):
            txt += "\n" + rec["note"]
        self.ump_lbl.configure(text=txt, fg=RATING_COLOR.get(rec["rating"], FG_DIM))

        tv = self.umptree
        tv.delete(*tv.get_children())
        for r in rec["rows"]:
            b = r["bias"]
            tag = ("OK" if b is not None and abs(b) <= 10
                   else "WARN" if b is not None and abs(b) <= 20 else "FAIL")
            tv.insert("", "end", tags=(tag,), values=(
                r["sample"],
                ((r.get(key) or "").strip() or "(not recorded)") if key
                else (r.get("hole") or ""),
                fmt_num(r["primary"]), fmt_num(r["umpire"]),
                fmt_num(r["diff"]),
                "" if b is None else f"{b:+.2f}",
                "" if r["ratio"] is None else f"{r['ratio']:.4f}",
                "" if r["hard"] is None else f"{r['hard']:.2f}"))

    def render_insertion(self):
        R = self.project.results
        ins = R["insertion"]
        chart_insertion(self.ins_ch, ins, self.settings)
        tv = self.instree
        tv.delete(*tv.get_children())
        for r in ins["rows"]:
            tv.insert("", "end", tags=(r["rating"],), values=(
                r["type"], r["n"],
                "" if r["pct"] is None else f"{r['pct']:.2f}",
                "" if r["every"] is None else f"1 in {r['every']:.0f}",
                r["rating"]))

    # ---------------- output ------------------------------------------------
    def save_chart(self, chart):
        p = filedialog.asksaveasfilename(
            parent=self, defaultextension=".ps",
            filetypes=[("PostScript (vector)", "*.ps"), ("All files", "*.*")],
            title="Save the chart")
        if not p:
            return
        try:
            chart.export_ps(p)
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Could not save the chart:\n{ex}",
                                 parent=self)
            return
        self.log(f"Chart written to {os.path.basename(p)}")
        messagebox.showinfo(APP_NAME, "Chart saved as vector PostScript.\n\n"
                                      "It opens in Illustrator, Inkscape, CorelDRAW "
                                      "and most publishing tools, and can be placed "
                                      "straight into a report.", parent=self)

    def do_export(self):
        if not self.project.results:
            messagebox.showinfo(APP_NAME, "Run the analysis first.", parent=self)
            return
        base = "qaqc"
        if self.project.assay:
            base = os.path.splitext(os.path.basename(self.project.assay.path))[0]
        dlg = ExportDialog(self, default_base=base)
        if not dlg.result:
            return
        folder, b = dlg.result
        self.log(f"Exporting to {folder} ...")
        try:
            files = export_results(self.project, self.F, self.C, self.settings,
                                   folder, b, log=self.log)
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Export failed:\n{ex}", parent=self)
            return
        self.log(f"Exported {len(files)} file(s).")
        if messagebox.askyesno(APP_NAME, f"{len(files)} file(s) written to:\n{folder}"
                                         f"\n\nOpen the folder now?", parent=self):
            try:
                os.startfile(folder)          # Windows
            except AttributeError:
                pass

    # ---------------- session ------------------------------------------------
    def save_session(self):
        if not self.project.assay:
            messagebox.showinfo(APP_NAME, "Nothing to save yet.", parent=self)
            return
        p = filedialog.asksaveasfilename(parent=self, defaultextension=".qaproj",
                                         filetypes=[("GEOQAQC session", "*.qaproj")])
        if not p:
            return
        state = {"version": APP_VER, "settings": self.settings,
                 "formulas": self.F.to_state(),
                 "criteria": {k: v["cuts"] for k, v in self.C.items()},
                 "assay": self.project.assay.to_state(),
                 "crm": self.project.crm.to_state() if self.project.crm else None,
                 "pairs": self.project.pairs.to_state() if self.project.pairs else None,
                 "umpire": (self.project.umpire.to_state()
                            if self.project.umpire else None)}
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        self.log(f"Session saved to {os.path.basename(p)}")

    def load_session(self):
        p = filedialog.askopenfilename(parent=self,
                                       filetypes=[("GEOQAQC session", "*.qaproj"),
                                                  ("All files", "*.*")])
        if not p:
            return
        try:
            with open(p, encoding="utf-8") as fh:
                state = json.load(fh)
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Could not read the session:\n{ex}",
                                 parent=self)
            return

        def rebuild(s):
            if not s:
                return None
            if not os.path.exists(s["path"]):
                self.log(f"  ! missing file: {s['path']}")
                return None
            h, r, d = sniff_and_read(s["path"])
            t = DataTable(s["kind"], s["name"], s["path"], h, r, d)
            t.mapping = s["mapping"]
            t.value_cols = [tuple(x) for x in s.get("value_cols", [])]
            t.type_map = s.get("type_map", {})
            t.dl = {k: float(v) for k, v in (s.get("dl") or {}).items()}
            return t

        self.project = Project()
        self.settings.update(state.get("settings", {}))
        for k, v in self._svars.items():
            if k in self.settings:
                v.set(self.settings[k])
        self.F.from_state(state.get("formulas"))
        for key, v in self._fvars.items():
            v.set(self.F.expr(key))
        for key, cuts in (state.get("criteria") or {}).items():
            if key in self.C:
                self.C[key]["cuts"] = [float(c) for c in cuts]
                for v, c in zip(self._cvars.get(key, []), self.C[key]["cuts"]):
                    v.set(f"{c:g}")
        self.project.assay = rebuild(state.get("assay"))
        self.project.crm = rebuild(state.get("crm"))
        self.project.pairs = rebuild(state.get("pairs"))
        self.project.umpire = rebuild(state.get("umpire"))
        self.set_badge(R_NA)
        self.log(f"Session loaded from {os.path.basename(p)}")
        self._sync()


def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)     # crisp text on Windows HiDPI
    except Exception:
        pass
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
