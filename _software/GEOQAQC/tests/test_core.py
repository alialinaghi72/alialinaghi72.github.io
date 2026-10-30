import datetime as dt

import pytest

from geoqaqc import core
from geoqaqc.core import (T_BLANK, T_CBLANK, T_PBLANK, T_PDUP, classify_type,
                          cusum, element_family, element_symbol, element_unit,
                          fa_num, fnum, gregorian_to_jalali, jalali_str,
                          linreg_stats, spearman, unit_factor)


def test_fnum_decimal_comma():
    assert fnum("0,123") == pytest.approx(0.123)
    assert fnum("1,234.5") == pytest.approx(1234.5)
    assert fnum("1,234,567") == pytest.approx(1234567)
    assert fnum("<0,01") == pytest.approx(0.01)


def test_fnum_persian_digits():
    assert fnum("۰٫۱۲۳") == pytest.approx(0.123)
    assert fnum("٠٫٥") == pytest.approx(0.5)
    assert fnum("۱٬۲۳۴") == pytest.approx(1234)


def test_fnum_v11_behaviour_kept():
    assert fnum("<0.01") == pytest.approx(0.01)
    assert fnum(">10000") == pytest.approx(10000)
    assert fnum("") is None
    assert fnum("n/a") is None
    assert fnum("abc") is None


def test_classify_blank_subtypes():
    for code in ("CBLK", "coarse blank", "Blank-Coarse"):
        assert classify_type(code) == T_CBLANK, code
    for code in ("PBLK", "pulp blank"):
        assert classify_type(code) == T_PBLANK, code
    assert classify_type("BLK") == T_BLANK
    assert classify_type("PULP DUP") == T_PDUP


def test_linreg_stats_known():
    xs = list(range(1, 11))
    noise = [0.1, -0.1] * 5
    ys = [2 * x + 1 + e for x, e in zip(xs, noise)]
    st = linreg_stats(xs, ys)
    assert st["b"] == pytest.approx(2.0, abs=0.02)
    assert st["p"] < 1e-6
    assert st["n"] == 10


def test_linreg_stats_degenerate():
    assert linreg_stats([1, 1, 1], [1, 2, 3]) is None
    assert linreg_stats([1], [1]) is None


def test_spearman_monotone():
    st = spearman([1, 2, 3, 4, 5, 6], [2, 4, 8, 16, 32, 64])
    assert st["rho"] == pytest.approx(1.0)


def test_cusum_signals():
    zs = [0.0] * 5 + [1.5] * 10
    out = cusum(zs, 0.5, 5.0)
    # +1.0 per step from index 5: the sum first exceeds h = 5 at index 10
    assert out["signals"][0] == 10
    assert len(out["hi"]) == len(zs) == len(out["lo"])


def test_jalali():
    assert gregorian_to_jalali(2026, 10, 30) == (1405, 8, 8)
    assert gregorian_to_jalali(2024, 3, 20) == (1403, 1, 1)
    assert jalali_str(dt.date(2026, 10, 30)) == "۱۴۰۵/۰۸/۰۸"


def test_fa_num():
    assert fa_num(12.345, 2) == "۱۲٫۳۵"
    # a negative number is wrapped in a left-to-right embedding so the minus
    # stays in front of the digits inside Persian text
    assert fa_num(-3, 0) == "\u202a−۳\u202c"
    assert fa_num(-1.34, 2, suffix="٪") == "\u202a−۱٫۳۴٪\u202c"
    assert fa_num(1.5, 1, suffix="٪") == "۱٫۵٪"
    assert fa_num(None) == "—"


def test_element_helpers():
    assert (element_symbol("Cu_pct"), element_unit("Cu_pct")) == ("Cu", "%")
    assert (element_symbol("AU_PPM"), element_unit("AU_PPM")) == ("Au", "ppm")
    assert (element_symbol("Au_ppb"), element_unit("Au_ppb")) == ("Au", "ppb")
    assert (element_symbol("Ag_gt"), element_unit("Ag_gt")) == ("Ag", "g/t")
    assert element_unit("Cu") == ""
    assert unit_factor("%", "ppm") == 10000
    assert unit_factor("ppb", "ppm") == pytest.approx(0.001)
    assert unit_factor("g/t", "ppm") == 1
    assert unit_factor("%", "kg") is None
    assert element_family("Au_ppm") == "precious"
    assert element_family("Mo_ppm") == "base"
    assert element_family("Fe2O3_pct") == "other"


def test_sample_types_order():
    st = core.SAMPLE_TYPES
    assert st.index(T_CBLANK) == st.index(T_BLANK) + 1
    assert st.index(T_PBLANK) == st.index(T_BLANK) + 2
    assert core.BLANK_TYPES == [T_BLANK, T_CBLANK, T_PBLANK]
