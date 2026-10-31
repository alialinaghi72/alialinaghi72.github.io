# -*- coding: utf-8 -*-
"""Constants, number parsing and statistics shared by every GEOQAQC module.

Nothing in here knows about tkinter, matplotlib or the report: the analysis
can run headless, which is what the tests and the report builder rely on.
"""

from __future__ import annotations

import datetime as _dt
import math
import re

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
T_CBLANK = "COARSE BLANK"
T_PBLANK = "PULP BLANK"
T_FDUP = "FIELD DUP"
T_CDUP = "COARSE DUP"
T_PDUP = "PULP DUP"
T_UMP = "CHECK / UMPIRE"
SAMPLE_TYPES = [T_NORMAL, T_CRM, T_BLANK, T_CBLANK, T_PBLANK, T_FDUP, T_CDUP,
                T_PDUP, T_UMP]
BLANK_TYPES = [T_BLANK, T_CBLANK, T_PBLANK]
DUP_TYPES = [T_FDUP, T_CDUP, T_PDUP]

# common codes seen in real laboratory submission files
TYPE_HINTS = {
    T_CRM: ["crm", "std", "standard", "stnd", "ref", "reference", "oreas", "geostats",
            "cdn", "amis", "rocklabs", "shaw", "control"],
    T_CBLANK: ["cblk", "c_blk", "c-blk", "cblank", "coarse blank", "coarse_blank",
               "blank coarse", "blank-coarse", "blank_coarse", "crushed blank",
               "prep blank", "preparation blank"],
    T_PBLANK: ["pblk", "p_blk", "p-blk", "pblank", "pulp blank", "pulp_blank",
               "blank pulp", "blank-pulp", "blank_pulp", "analytical blank",
               "method blank", "reagent blank"],
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

# order in which hints are tried: the specific blank kinds before the generic
# one, so "pulp blank" is not taken for a pulp duplicate or a plain blank
_CLASSIFY_ORDER = (T_UMP, T_CBLANK, T_PBLANK, T_PDUP, T_CDUP, T_FDUP, T_BLANK,
                   T_CRM)


# ===========================================================================
#  Number parsing
# ===========================================================================
NULL_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "nd", "n.d."}

# Persian and Arabic-Indic digits, Arabic decimal and thousands separators
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫٬", "01234567890123456789.,")
_THOUSANDS = re.compile(r"^-?[1-9]\d{0,2}(,\d{3})+(\.\d+)?$")
_DECIMAL_COMMA = re.compile(r"^-?\d*,\d+$")


def to_latin_digits(s):
    return str(s).translate(_DIGITS)


def fnum(v, decimal_comma=False):
    """Permissive float parse. Handles '<0.01' and '>10000' detection-limit
    notation by returning the numeric part; use dl_flag() to know which.

    A comma is a thousands separator only in the form 1,234 or 1,234,567.5;
    any other single comma between digits is a decimal comma (0,123), which
    is how semicolon-delimited exports from many locales write numbers.
    With decimal_comma=True (a table already known to use that convention)
    every comma is the decimal mark and dots are thousands separators."""
    if v is None:
        return None
    s = to_latin_digits(v).strip()
    if s.lower() in NULL_TOKENS:
        return None
    if s and s[0] in "<>":
        s = s[1:].strip()
    if decimal_comma:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        if _THOUSANDS.match(s):
            s = s.replace(",", "")
        elif _DECIMAL_COMMA.match(s):
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
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


def classify_type(raw):
    """Map an arbitrary sample-type code to one of SAMPLE_TYPES. Best guess."""
    s = str(raw or "").strip().lower()
    if not s:
        return T_NORMAL
    for t in _CLASSIFY_ORDER + (T_NORMAL,):
        for hint in TYPE_HINTS[t]:
            if s == hint:
                return t
    for t in _CLASSIFY_ORDER:
        for hint in TYPE_HINTS[t]:
            if hint in s:
                return t
    return T_NORMAL


# ===========================================================================
#  Statistics (unchanged from 1.1)
# ===========================================================================
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


# --- added in 2.0 ------------------------------------------------------------
def linreg_stats(xs, ys):
    """OLS with the standard error and two-tailed p-value of the slope.
    Returns {a, b, r, se_b, t, p, n} or None when no slope can be fitted."""
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pts)
    if n < 3:
        return None
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    if sxx == 0:
        return None
    b = sxy / sxx
    a = my - b * mx
    r = sxy / math.sqrt(sxx * syy) if syy > 0 else None
    sse = sum((y - (a + b * x)) ** 2 for x, y in pts)
    df = n - 2
    se_b = math.sqrt(sse / df / sxx) if sse > 0 else 0.0
    if se_b == 0:
        t, p = (math.inf if b else 0.0), (0.0 if b else 1.0)
    else:
        t = b / se_b
        p = t_two_tail_p(t, df)
    return {"a": a, "b": b, "r": r, "se_b": se_b, "t": t, "p": p, "n": n}


def common_slope(groups):
    """One slope shared by several series, each with its own intercept
    (analysis of covariance): x and y are centred within each group, so the
    level of one group never reads as a trend across groups.
    groups: iterable of (xs, ys). Returns {b, se_b, t, p, n, k, mx} or None."""
    sxx = sxy = 0.0
    cen, n, k, sx = [], 0, 0, 0.0
    for xs, ys in groups:
        pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
        if not pts:
            continue
        gx = sum(p[0] for p in pts) / len(pts)
        gy = sum(p[1] for p in pts) / len(pts)
        for x, y in pts:
            cen.append((x - gx, y - gy))
            sx += x
        n += len(pts)
        k += 1
    df = n - k - 1
    if df < 1:
        return None
    sxx = sum(dx * dx for dx, _ in cen)
    sxy = sum(dx * dy for dx, dy in cen)
    if sxx == 0:
        return None
    b = sxy / sxx
    sse = sum((dy - b * dx) ** 2 for dx, dy in cen)
    se_b = math.sqrt(sse / df / sxx) if sse > 0 else 0.0
    if se_b == 0:
        t, p = (math.inf if b else 0.0), (0.0 if b else 1.0)
    else:
        t = b / se_b
        p = t_two_tail_p(t, df)
    return {"b": b, "se_b": se_b, "t": t, "p": p, "n": n, "k": k, "mx": sx / n}


def _ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(xs, ys):
    """Spearman rank correlation with a t-approximation p-value."""
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pts)
    if n < 4:
        return None
    rx = _ranks([p[0] for p in pts])
    ry = _ranks([p[1] for p in pts])
    _, _, rho = linreg(rx, ry)
    if rho is None:
        return None
    if abs(rho) >= 1.0:
        p = 0.0
    else:
        t = rho * math.sqrt((n - 2) / (1.0 - rho * rho))
        p = t_two_tail_p(t, n - 2)
    return {"rho": rho, "p": p, "n": n}


def cusum(zs, k, h):
    """Tabular CUSUM on standardised results (Page, 1954).
    hi_i = max(0, hi_{i-1} + z_i - k); lo_i = min(0, lo_{i-1} + z_i + k).
    A signal is raised at every index where |hi| or |lo| first exceeds h after
    being reset; both sums restart from zero after a signal."""
    hi, lo, sig = [], [], []
    sh = sl = 0.0
    for i, z in enumerate(zs):
        if z is None:
            hi.append(sh)
            lo.append(sl)
            continue
        sh = max(0.0, sh + z - k)
        sl = min(0.0, sl + z + k)
        hi.append(sh)
        lo.append(sl)
        if sh > h or sl < -h:
            sig.append(i)
            sh = sl = 0.0
    return {"hi": hi, "lo": lo, "signals": sig}


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


# ===========================================================================
#  Persian text helpers
# ===========================================================================
_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_digits(s):
    """Latin digits -> Persian digits; '.' between digits -> Persian decimal."""
    s = re.sub(r"(?<=\d)\.(?=\d)", "٫", str(s))
    return s.translate(_FA)


def fa_num(v, decimals=None, suffix=""):
    """Number for Persian prose: Persian digits, '٫' decimal, a true minus.
    A negative number (with its suffix, e.g. '٪') is wrapped in a left-to-right
    embedding: in right-to-left text the bare minus would otherwise drift to
    the far end of the number and read as a trailing sign."""
    if v is None:
        return "—"
    if decimals is None:
        txt = fmt_num(v)
    else:
        txt = f"{v:,.{decimals}f}".replace(",", "٬")
    if txt.startswith("-"):
        if txt.strip("-0.,٬") == "":
            return fa_digits(txt[1:]) + suffix
        return "\u202a" + "−" + fa_digits(txt[1:]) + suffix + "\u202c"
    return fa_digits(txt) + suffix


def gregorian_to_jalali(gy, gm, gd):
    """Gregorian -> Solar Hijri (the algorithm used by jdf.scr.ir)."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100
            + (gy2 + 399) // 400 + gd + g_d_m[gm - 1])
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def jalali_str(date=None):
    d = date or _dt.date.today()
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return fa_digits(f"{jy}/{jm:02d}/{jd:02d}")


# ===========================================================================
#  Element names and units
# ===========================================================================
_SYMBOLS = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si",
    "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co",
    "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I",
    "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au",
    "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th", "Pa", "U"}
_SYM_UPPER = {s.upper(): s for s in _SYMBOLS}

PRECIOUS = {"Au", "Ag", "Pt", "Pd", "Rh", "Ir", "Os", "Ru"}
BASE = {"Cu", "Pb", "Zn", "Ni", "Co", "Mo", "Sn", "Sb", "W", "Bi", "Cd", "As"}

# suffix token -> canonical unit
_UNIT_TOKENS = {"pct": "%", "perc": "%", "percent": "%", "%": "%", "wt%": "%",
                "ppm": "ppm", "ppb": "ppb", "gt": "g/t", "g/t": "g/t",
                "gpt": "g/t", "g_t": "g/t", "gpt.": "g/t"}
# value of one unit expressed in ppm
_IN_PPM = {"%": 10000.0, "ppm": 1.0, "g/t": 1.0, "ppb": 0.001}


def element_symbol(name):
    """Chemical symbol at the start of a column name: 'Cu_pct' -> 'Cu',
    'AU_PPM' -> 'Au', 'Au-FA' -> 'Au', 'CaO_pct' -> 'Ca'. A name that does not
    start with a symbol is returned stripped."""
    s = str(name or "").strip()
    two, one = s[:2].upper(), s[:1].upper()
    if len(s) >= 2 and s[1].isalpha() and two in _SYM_UPPER:
        return _SYM_UPPER[two]
    if one in _SYM_UPPER:
        return _SYM_UPPER[one]
    return s


def element_unit(name):
    """Unit encoded in a column name, '' when the name carries none."""
    s = str(name or "").strip().lower()
    parts = re.split(r"[_\-\s\(\)\[\]]+", s)
    for p in reversed(parts[1:]):
        if p in _UNIT_TOKENS:
            return _UNIT_TOKENS[p]
    if s.endswith("%"):
        return "%"
    return ""


def canonical_unit(u):
    return _UNIT_TOKENS.get(str(u or "").strip().lower(), "")


def unit_factor(src, dst):
    """Multiplier converting a value in unit src into unit dst, or None."""
    a, b = canonical_unit(src), canonical_unit(dst)
    if not a or not b:
        return None
    f = _IN_PPM[a] / _IN_PPM[b]
    return int(f) if f == int(f) else f


def element_family(name):
    sym = element_symbol(name)
    if sym in PRECIOUS:
        return "precious"
    if sym in BASE:
        return "base"
    return "other"
