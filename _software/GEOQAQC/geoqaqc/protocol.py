# -*- coding: utf-8 -*-
"""The QA/QC protocol: editable formulas, rating criteria, settings and rules.

Formulas, criteria and settings are unchanged from GEOQAQC 1.1 apart from the
additions marked 2.0. RULES is new: every threshold used by the cleaning,
diagnosis and batch-acceptance logic.
"""

from __future__ import annotations

import ast
import math

from .core import R_NA, R_VBAD, RATING_ORDER, RATING_SCORE

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
    "dup_cv2": {
        "group": "DUPLICATE", "label": "Pair relative variance (CV squared)",
        "expr": "(a - b) ** 2 / (2 * ((a + b) / 2) ** 2)", "vars": "a, b",
        "note": "2.0. Squared pair CV as a fraction. Averaged per duplicate "
                "class it gives the variance of that stage of the sample "
                "chain, from which the error budget is built."},
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

    "maxmin_fail": {
        "group": "DUPLICATE", "label": "Max-Min failure rate %", "unit": "%",
        "cuts": [5, 10, 15, 20, 30], "dir": "low",
        "note": "2.0. Share of pairs outside the acceptance line of the "
                "Max-Min plot, the line being the GOOD boundary of the HARD "
                "criterion of the class. Up to 10% failing is the usual pass "
                "mark, matching the 90th-percentile convention."},

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
    "carry_kdl": 10.0,          # 2.0: 'high grade' predecessor, multiples of DL
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
#  Editable rules -- every cleaning, diagnosis and batch threshold
# ===========================================================================
# Nothing in cleaning.py, analysis.py or diagnosis.py is a literal threshold:
# each one is looked up here, so it can be changed in the Rules tab, saved in
# the session and written to the protocol file next to the results it made.
SEVERITY_CHOICES = ["NONE", "MINOR", "MATERIAL", "CRITICAL"]
STAGE_CHOICES = ["SAMPLING", "PREPARATION", "ACCURACY", "PRECISION",
                 "CONTAMINATION", "INTERLAB", "DATA", "PROGRAMME"]
CRM_RULE_CHOICES = ["1-3s", "2-2s", "R-4s", "4-1s", "10x", "2s"]

_CLEAN_RULES = [
    ("C01", "Rows without a sample ID",
     "A row with no sample ID cannot be paired, sequenced or reported. It is "
     "set aside and listed."),
    ("C02", "Exact duplicate rows",
     "The same row pasted twice inflates every count. Extra copies are dropped."),
    ("C03", "Duplicate sample IDs (re-assays)",
     "Two different results under one ID are usually a re-assay appended to "
     "the file. One is kept according to the policy below."),
    ("C04", "Text codes from the laboratory",
     "IS, NSS, LNR and similar codes mean 'no result'. They become missing "
     "values instead of being dropped silently by the number parser."),
    ("C05", "Sentinel numbers",
     "-999 and similar are placeholders for 'no result', not concentrations."),
    ("C06", "Negative values as below detection",
     "Many laboratories report <0.01 as -0.01. Read as below detection."),
    ("C07", "Zero as below detection",
     "A true zero concentration does not exist; a reported 0 is below detection."),
    ("C08", "Over-range values (>)",
     "'>10000' is a censored value, not a result. It is excluded from CRM "
     "statistics and from duplicate pairs."),
    ("C09", "Match CRM codes loosely",
     "'OREAS 501b', 'OREAS-501B' and 'oreas_501b' are the same material. "
     "Matching ignores case, spaces, dashes, dots and slashes."),
    ("C10", "Match certificate elements and convert units",
     "Cu on the certificate matches Cu_pct in the assay file, and a ppb "
     "certificate is converted to a ppm column."),
    ("C11", "Detect a unit mismatch of a whole column",
     "If every CRM reads about 1000x or 10000x its certificate, the units "
     "differ. The certificate is rescaled and the mismatch is reported."),
    ("C12", "Detect a single decimal or unit slip",
     "One CRM at 10x, 100x or 1000x its certificate while the others agree is "
     "a transcription slip, not an analytical failure."),
    ("C13", "Detect swapped CRMs",
     "A result that fails its own certificate but agrees with another CRM's "
     "certificate is a labelling error, not a laboratory failure."),
    ("C14", "Detect a blank inserted as a CRM",
     "A 'CRM' whose every element sits at blank level is a missing or "
     "mislabelled standard."),
    ("C15", "Detect a CRM inserted as a blank",
     "A 'blank' that matches a CRM certificate is a swap, not contamination."),
    ("C16", "Detect mispaired duplicates",
     "In multi-element data, a pair that disagrees grossly in most elements "
     "comes from two different samples. In single-element data this cannot be "
     "told from a nugget effect, so the pair is only flagged."),
    ("C17", "Report duplicates without a parent",
     "A duplicate whose parent ID is missing or wrong drops out of the "
     "precision statistics; it is listed so the database can be fixed."),
    ("C18", "Report sequence problems",
     "Missing or repeated sequence numbers change the order of control charts; "
     "they are listed."),
]

RULES = {}
for _code, _label, _note in _CLEAN_RULES:
    RULES[f"clean_{_code}"] = {"group": "CLEANING", "label": f"{_code}  {_label}",
                               "kind": "bool", "default": True, "note": _note}


def _r(key, group, label, kind, default, note, lo=None, hi=None, choices=None):
    d = {"group": group, "label": label, "kind": kind, "default": default,
         "note": note}
    if lo is not None:
        d["min"] = lo
    if hi is not None:
        d["max"] = hi
    if choices is not None:
        d["choices"] = choices
    RULES[key] = d


# ---- cleaning parameters ----
_r("dup_id_policy", "CLEANING", "C03 policy for duplicate IDs", "choice",
   "keep first", "Which result stands when one ID appears twice. 'keep first' "
   "treats later rows as re-assays.",
   choices=["keep first", "keep last", "exclude all"])
_r("lab_codes", "CLEANING", "C04 laboratory 'no result' codes", "list",
   ["IS", "NSS", "LNR", "NR", "NS", "INS", "ISS", "NSR", "NP", "N.A.", "NA",
    "N/A", "ND", "N.D.", "X", "NAN", "NULL", "NONE", "-", "--"],
   "Case-insensitive. IS/NSS/INS = insufficient sample, LNR = listed not "
   "received, NR/NS = not received, NP = not prepared, ND = not determined.")
_r("sentinels", "CLEANING", "C05 sentinel values", "list",
   [-999.0, -9999.0, -99.0, -99.9, -999.9, 9999.0, 99999.0],
   "Numbers that databases use as placeholders for 'no value'.")
_r("unit_col_tol", "CLEANING", "C11 tolerance on the column ratio (%)", "float",
   25.0, "The median measured/certified ratio must lie within this much of "
   "1000, 10000, 1/1000 or 1/10000 to be called a unit mismatch.", 1, 60)
_r("unit_single_tol", "CLEANING", "C12 tolerance on a single ratio (%)",
   "float", 10.0, "A single result must lie within this much of 10, 100 or "
   "1000 times (or a tenth, hundredth, thousandth of) its certificate.", 1, 40)
_r("swap_frac", "CLEANING", "C13/C15 share of elements that must agree",
   "float", 0.667, "Share of the certified elements in which the result must "
   "fail its own CRM and agree with the other one. Two thirds keeps a single "
   "bad element from being called a swap.", 0.34, 1.0)
_r("swap_single_z", "CLEANING", "C13 single-element threshold (SD)", "float",
   6.0, "With only one certified element there is no cross-check, so the "
   "result must sit this many SD from its own CRM before a swap is called.",
   3.0, 50.0)
_r("swap_alt_z", "CLEANING", "C13/C15 agreement with the other CRM (SD)",
   "float", 2.0, "Distance from the other CRM's certificate, in its SD, within "
   "which the result is said to agree with it.", 0.5, 5.0)
_r("crm_blank_kdl", "CLEANING", "C14 blank level (x DL)", "float", 5.0,
   "A CRM result below this multiple of the detection limit in every element "
   "is treated as a blank.", 1.0, 50.0)
_r("mispair_hard", "CLEANING", "C16 HARD of a mispaired element (%)", "float",
   50.0, "HARD above 50% means one value is more than three times the other.",
   20.0, 99.0)
_r("mispair_kdl", "CLEANING", "C16 minimum grade (x DL)", "float", 5.0,
   "Only elements where both values exceed this multiple of the DL vote; near "
   "the DL large relative differences are normal.", 1.0, 100.0)
_r("mispair_min_el", "CLEANING", "C16 minimum voting elements", "int", 2,
   "With fewer voting elements the pair is flagged, never excluded.", 2, 20)
_r("mispair_frac", "CLEANING", "C16 share of elements that must disagree",
   "float", 0.667, "Share of the voting elements that must exceed the HARD "
   "threshold.", 0.34, 1.0)

# ---- CRM diagnosis ----
_r("drift_p", "CRM", "Drift: significance level", "float", 0.05,
   "p-value of the regression of bias on sequence below which a trend is "
   "considered real.", 0.001, 0.2)
_r("drift_total", "CRM", "Drift: minimum change over the series (%)", "float",
   3.0, "A statistically real trend smaller than this is not material.", 0.5,
   20.0)
_r("sys_bias", "CRM", "Systematic bias: minimum |bias| per CRM (%)", "float",
   2.5, "Bias of the same sign in several CRMs, each at least this large, is a "
   "laboratory-wide bias rather than a problem with one material.", 0.5, 20.0)
_r("sys_min_crm", "CRM", "Systematic bias: minimum number of CRMs", "int", 2,
   "How many CRMs must share the sign.", 2, 10)
_r("rsd_ratio", "CRM", "Observed / certified RSD ratio", "float", 1.5,
   "The laboratory repeats a CRM less well than the round robin that "
   "certified it when the ratio exceeds this.", 1.0, 5.0)
_r("cluster_frac", "CRM", "Failure clustering: share of failures", "float", 0.5,
   "Share of all CRM failures that falls in the worst batches.", 0.2, 1.0)
_r("cluster_batches", "CRM", "Failure clustering: share of batches (%)",
   "float", 20.0, "If the failures above sit in at most this share of the "
   "batches, the problem is batch-specific.", 5.0, 60.0)
_r("cusum_k", "CRM", "CUSUM reference value k (SD)", "float", 0.5,
   "Half the shift to detect; 0.5 SD detects a 1 SD shift quickly.", 0.1, 2.0)
_r("cusum_h", "CRM", "CUSUM decision interval h (SD)", "float", 5.0,
   "Standard choice with k = 0.5.", 1.0, 20.0)
_r("coverage_pcts", "CRM", "Grade percentiles the CRMs should cover", "list",
   [10.0, 50.0, 90.0], "CRMs should bracket the low, median and high grade "
   "of the routine samples.")

# ---- blanks ----
_r("carry_frac", "BLANK", "Carry-over: share of failures after high grade",
   "float", 0.5, "If at least this share of blank failures follows a "
   "high-grade sample, carry-over is the cause.", 0.2, 1.0)
_r("blank_median_kdl", "BLANK", "Contaminated blank material (median x DL)",
   "float", 2.0, "A blank material whose median sits above this, without any "
   "link to the preceding sample, is itself not barren.", 1.0, 20.0)

# ---- duplicates ----
_r("split_p", "DUPLICATE", "Splitting bias: significance level", "float", 0.05,
   "p-value of the paired t-test on ln(original/duplicate).", 0.001, 0.2)
_r("budget_dominant", "DUPLICATE", "Error budget: dominant stage share (%)",
   "float", 50.0, "A stage carrying more than this share of the total "
   "variance is named as the main source of error.", 30.0, 90.0)

# ---- batches ----
_r("batch_fail_rules", "BATCH", "CRM rules that fail a batch", "list",
   ["1-3s", "2-2s"], "Westgard rules whose violation fails the batch and "
   "triggers a re-assay range. Allowed: " + ", ".join(CRM_RULE_CHOICES))
_r("batch_warn_rules", "BATCH", "CRM rules that put a batch on warning",
   "list", ["2s"], "'2s' is a single result beyond the warning limit.")
_r("batch_blank_fail", "BATCH", "A failed blank fails its batch", "bool", True,
   "When off, a failed blank only puts the batch on warning.")

# ---- severity and verdict ----
_r("sev_POOR", "SEVERITY", "Severity of a POOR rating", "choice", "MINOR",
   "Findings take their severity from the rating of their criterion.",
   choices=SEVERITY_CHOICES)
_r("sev_BAD", "SEVERITY", "Severity of a BAD rating", "choice", "MATERIAL",
   "", choices=SEVERITY_CHOICES)
_r("sev_VERY BAD", "SEVERITY", "Severity of a VERY BAD rating", "choice",
   "CRITICAL", "", choices=SEVERITY_CHOICES)
_r("verdict_stages", "SEVERITY", "Stages where a critical finding blocks use",
   "list", ["ACCURACY", "CONTAMINATION", "INTERLAB"],
   "A critical finding in one of these stages makes the verdict 'usable after "
   "remediation'. Allowed: " + ", ".join(STAGE_CHOICES))

RULE_GROUPS = ["CLEANING", "CRM", "BLANK", "DUPLICATE", "BATCH", "SEVERITY"]


def _as_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"'{v}' is not true/false")


class RuleBook:
    """Current values of RULES, validated on every change."""

    def __init__(self, state=None):
        self.values = {k: self._copy(d["default"]) for k, d in RULES.items()}
        if state:
            self.from_state(state)

    @staticmethod
    def _copy(v):
        return list(v) if isinstance(v, list) else v

    def get(self, key):
        if key not in RULES:
            raise KeyError(key)
        return self.values[key]

    __getitem__ = get

    def coerce(self, key, value):
        """Parse and validate a value for key; raises ValueError."""
        d = RULES[key]
        kind = d["kind"]
        if kind == "bool":
            return _as_bool(value)
        if kind in ("float", "int"):
            try:
                v = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"{d['label']}: '{value}' is not a number")
            if kind == "int":
                if v != int(v):
                    raise ValueError(f"{d['label']}: must be a whole number")
                v = int(v)
            if "min" in d and v < d["min"] or "max" in d and v > d["max"]:
                raise ValueError(f"{d['label']}: must lie between "
                                 f"{d.get('min')} and {d.get('max')}")
            return v
        if kind == "choice":
            if value not in d["choices"]:
                raise ValueError(f"{d['label']}: choose one of "
                                 + ", ".join(d["choices"]))
            return value
        if kind == "list":
            items = value
            if isinstance(value, str):
                items = [x.strip() for x in value.split(",") if x.strip()]
            items = list(items)
            if isinstance(d["default"], list) and d["default"] and \
                    isinstance(d["default"][0], float):
                try:
                    return [float(x) for x in items]
                except ValueError:
                    raise ValueError(f"{d['label']}: every item must be a number")
            items = [str(x).strip() for x in items]
            allowed = (CRM_RULE_CHOICES if key in ("batch_fail_rules",
                                                   "batch_warn_rules")
                       else STAGE_CHOICES if key == "verdict_stages" else None)
            if allowed:
                bad = [x for x in items if x not in allowed]
                if bad:
                    raise ValueError(f"{d['label']}: unknown item(s) "
                                     + ", ".join(bad))
            return items
        raise ValueError(f"unknown kind {kind}")

    def set(self, key, value):
        if key not in RULES:
            raise KeyError(key)
        self.values[key] = self.coerce(key, value)

    def reset(self):
        self.values = {k: self._copy(d["default"]) for k, d in RULES.items()}

    def to_state(self):
        return {k: self._copy(v) for k, v in self.values.items()}

    def from_state(self, state):
        for k, v in (state or {}).items():
            if k in RULES:
                try:
                    self.set(k, v)
                except ValueError:
                    pass

    def changed(self):
        return [k for k in RULES if self.values[k] != RULES[k]["default"]]

    def groups(self):
        return [(g, [k for k, d in RULES.items() if d["group"] == g])
                for g in RULE_GROUPS]

    def describe(self, key):
        v = self.values[key]
        return ", ".join(f"{x:g}" if isinstance(x, float) else str(x)
                         for x in v) if isinstance(v, list) else (
            f"{v:g}" if isinstance(v, float) else str(v))
