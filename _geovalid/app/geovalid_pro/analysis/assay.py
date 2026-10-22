"""Assay value classification (02 §4.9.1–4.9.2) and unit inference (brief §6.1)."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from ..core.normalise import clean_text
from ..io.mapping import OXIDES

SENTINELS = (-99.0, -999.0, -9999.0, -99999.0)
TEXT_CODES = {"NS": "not sampled", "N/S": "not sampled", "NSS": "not sampled", "IS": "insufficient sample",
              "INS": "insufficient sample", "LNR": "listed not received", "NR": "not received", "NA": "not analysed",
              "N/A": "not analysed", "X": "not analysed", "-": "not analysed", "LOST": "lost", "NSR": "not received",
              "ND": "not detected", "BDL": "below detection", "TR": "trace", "?": "unknown"}
TO_PPM = {"ppm": 1.0, "g/t": 1.0, "ppb": 1e-3, "%": 1e4, "oz/t": 34.2857}
PRECIOUS = {"Au", "Ag", "Pt", "Pd", "Rh"}
PCT_ELEMENTS = {"Fe", "Mn", "Al", "Ca", "Mg", "Na", "K", "S", "Ti", "Si", "P", "C"}
BASE_METALS = {"Cu", "Pb", "Zn", "Ni"}

_LT = re.compile(r"^<\s*=?\s*([0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)$")
_GT = re.compile(r"^>\s*=?\s*([0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)$")
_NUM = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def parse_assay(raw: pd.Series) -> pd.DataFrame:
    """Columns: value (numeric as reported, NaN unless VAL/ODL), flag, dl, code, value_policy (BDL → ½DL)."""
    t = clean_text(raw)
    s = t.fillna("").str.replace(",", ".", regex=False).str.replace(" ", "", regex=False)
    flag = pd.Series("NA", index=raw.index, dtype=object)
    value = pd.Series(np.nan, index=raw.index)
    dl = pd.Series(np.nan, index=raw.index)
    lt = s.str.extract(_LT)[0]
    gt = s.str.extract(_GT)[0]
    is_num = s.str.match(_NUM)
    num = pd.to_numeric(s.where(is_num), errors="coerce")
    m_lt, m_gt = lt.notna(), gt.notna()
    flag[m_lt] = "BDL"
    dl[m_lt] = pd.to_numeric(lt[m_lt])
    flag[m_gt] = "ODL"
    value[m_gt] = pd.to_numeric(gt[m_gt])
    flag[is_num] = "VAL"
    value[is_num] = num[is_num]
    neg = is_num & (num < 0)
    if neg.any():
        snt = neg & num.isin(SENTINELS)
        flag[snt] = "SNT"
        value[snt] = np.nan
        rest = neg & ~snt
        mags = np.unique(np.round(-num[rest], 9))
        if 0 < len(mags) <= 3 and (mags <= 10).all():
            flag[rest] = "BDL"
            dl[rest] = -num[rest]
            value[rest] = np.nan
    txt = (s != "") & ~is_num & ~m_lt & ~m_gt
    flag[txt] = "TXT"
    code = t.where(txt)
    policy = value.where(flag.isin(["VAL", "ODL"]))
    policy = policy.where(~(flag == "BDL"), dl / 2.0)
    return pd.DataFrame({"value": value, "flag": flag, "dl": dl, "code": code, "value_policy": policy})


def infer_unit(analyte: str, parsed: pd.DataFrame) -> tuple[str, str]:
    """Return (unit, evidence) for a column without a declared unit."""
    v = parsed.loc[parsed["flag"] == "VAL", "value"]
    v = v[v > 0]
    if analyte in OXIDES:
        return "%", "oxide or LOI: reported in wt %"
    if len(v) == 0:
        return "ppm", "no positive values; ppm assumed"
    p50, p99 = float(v.median()), float(v.quantile(0.99))
    if analyte in PRECIOUS:
        if p50 >= 50 and p99 > 1000:
            return "ppb", f"median {p50:.3g}, P99 {p99:.3g}: magnitude typical of ppb"
        return "g/t", f"median {p50:.3g}, P99 {p99:.3g}: magnitude typical of g/t"
    if analyte in PCT_ELEMENTS and p99 <= 100:
        return "%", f"P99 {p99:.3g} ≤ 100: major element in %"
    if analyte in BASE_METALS and p99 <= 30:
        return "%", f"P99 {p99:.3g} ≤ 30: base metal in %"
    return "ppm", f"P99 {p99:.3g}: magnitude typical of ppm"
