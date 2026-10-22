"""Import normalisation (02 §6): Persian digits and letters, invisible characters, numbers, dates.

Raw text is never altered in the source; these functions build the canonical values beside it.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

_DIGITS = str.maketrans({**{chr(0x06F0 + i): str(i) for i in range(10)},   # Persian ۰–۹
                         **{chr(0x0660 + i): str(i) for i in range(10)},   # Arabic-Indic ٠–٩
                         "٫": ".", "٬": "", "،": ",",       # ٫ decimal, ٬ thousands, ، comma
                         "ي": "ی", "ك": "ک",           # ي → ی, ك → ک
                         " ": " ", "​": "", "‎": "", "‏": "", "﻿": "",
                         "‪": "", "‫": "", "‬": "", "−": "-"})


def clean_text(s: pd.Series) -> pd.Series:
    """N02–N04: fold digits and letters, drop invisible characters, trim."""
    out = s.astype("string").str.translate(_DIGITS).str.strip()
    return out.where(out.notna() & (out != ""), pd.NA)


def header_key(name: str) -> str:
    """Matching key for column headers: lower case, Persian folded, separators removed."""
    t = str(name).translate(_DIGITS).replace("‌", "").lower()
    return re.sub(r"[\s_\-\.\(\)\[\]/\\:#%]+", "", t)


def hole_key(hole_id) -> str | None:
    """02 N12: case-fold, strip separators and leading zeros of numeric runs."""
    if hole_id is None or (isinstance(hole_id, float) and np.isnan(hole_id)) or hole_id is pd.NA:
        return None
    t = re.sub(r"[\s_\-\./]+", "", str(hole_id).translate(_DIGITS).upper())
    return re.sub(r"(?<!\d)0+(?=\d)", "", t)


_NUM_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_THOUS_RE = re.compile(r"^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$")
_DECCOMMA_RE = re.compile(r"^[+-]?\d+,\d+$")


def parse_numbers(raw: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series, str]:
    """Return (value, decimals, bad_mask, note). N05: decimal comma or thousands separators per column."""
    txt = clean_text(raw)
    present = txt.notna()
    t = txt.fillna("")
    note = ""
    has_comma = t.str.contains(",", regex=False) & present
    if has_comma.any():
        dec = t[has_comma].str.match(_DECCOMMA_RE)
        no_dot = not t[present].str.contains(".", regex=False).any()
        if no_dot and dec.mean() >= 0.95:
            t = t.str.replace(",", ".", regex=False)
            note = "decimal comma"
        else:
            th = t.str.match(_THOUS_RE)
            t = t.where(~th, t.str.replace(",", "", regex=False))
            if th.any():
                note = "thousands separators removed"
    ok = t.str.match(_NUM_RE) & present
    val = pd.to_numeric(t.where(ok), errors="coerce").astype("float64")
    # significant decimals: trailing zeros are export artefacts ("512100.0" from Excel/pandas is whole metres)
    sig = t.where(ok).str.replace(r"(\.\d*?)0+$", r"\1", regex=True)
    decimals = sig.str.extract(r"\.(\d*)")[0].str.len().fillna(0)
    decimals = decimals.where(ok).astype("float64")
    bad = present & ~ok
    return val, decimals, bad, note


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> tuple[int, int, int]:
    """Solar Hijri → Gregorian (arithmetic algorithm, valid 1300–1499 AP)."""
    jy += 1595
    days = -355668 + 365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4 + jd
    days += (jm - 1) * 31 if jm < 7 else (jm - 7) * 30 + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0
    months = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 12 and gd > months[gm]:
        gd -= months[gm]
        gm += 1
    return gy, gm + 1, gd


def parse_dates(raw: pd.Series) -> tuple[pd.Series, int]:
    """N08: ISO, D/M/Y text, Excel serials and Jalali dates. Returns (dates, n_jalali)."""
    txt = clean_text(raw)
    out = pd.Series(pd.NaT, index=raw.index, dtype="datetime64[ns]")
    n_jal = 0
    for i, v in txt.dropna().items():
        s = str(v)
        m = re.match(r"^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", s)
        try:
            if m:
                y, mo, d = map(int, m.groups())
                if 1300 <= y <= 1499:
                    y, mo, d = jalali_to_gregorian(y, mo, d)
                    n_jal += 1
                out[i] = pd.Timestamp(y, mo, d)
                continue
            if re.match(r"^\d{5}(\.\d+)?$", s) and 25569 <= float(s) <= 73051:
                out[i] = pd.Timestamp("1899-12-30") + pd.to_timedelta(float(s), unit="D")
                continue
            m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})$", s)
            if m:
                d, mo, y = map(int, m.groups())
                if mo > 12 and d <= 12:
                    d, mo = mo, d
                out[i] = pd.Timestamp(y, mo, d)
                continue
            out[i] = pd.Timestamp(s)
        except (ValueError, OverflowError):
            pass
    return out, n_jal
