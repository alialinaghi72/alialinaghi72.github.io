import numpy as np
import pandas as pd

from geovalid_pro.analysis.assay import parse_assay
from geovalid_pro.analysis.desurvey import desurvey, stations_for_hole
from geovalid_pro.core.normalise import hole_key, jalali_to_gregorian, parse_numbers
from geovalid_pro.io.mapping import parse_analyte_header


def test_persian_digits_and_decimal_separator():
    v, d, bad, _ = parse_numbers(pd.Series(["۱۲۳٫۴۵", "512100.0", "x"]))
    assert v[0] == 123.45 and d[0] == 2 and d[1] == 0 and bad[2]


def test_jalali():
    assert jalali_to_gregorian(1403, 1, 1) == (2024, 3, 20)
    assert jalali_to_gregorian(1399, 10, 11) == (2020, 12, 31)


def test_hole_key():
    assert hole_key("bh-001") == hole_key("BH 1") == "BH1"


def test_assay_codes():
    p = parse_assay(pd.Series(["<0.01", ">10", "NS", "-0.01", "-999", "1.5", ""]))
    assert list(p["flag"]) == ["BDL", "ODL", "TXT", "BDL", "SNT", "VAL", "NA"]
    assert p["value_policy"][0] == 0.005


def test_headers():
    a = parse_analyte_header("Fe2O3_pct")
    assert a.analyte == "Fe2O3" and a.unit == "%"
    assert parse_analyte_header("CuAS_pct").partial
    assert parse_analyte_header("Sample") is None and parse_analyte_header("CR") is None


def test_min_curvature_vertical_and_arc():
    st = stations_for_hole([0, 100], [0, 0], [-90, -90], 100)
    tr = desurvey(st, 0, 0, 0)
    assert np.isclose(tr["z"].iloc[-1], -100)
    # quarter circle from vertical to horizontal over an arc length of 100 m: radius 200/π
    st = stations_for_hole([0, 100], [90, 90], [-90, 0], 100)
    tr = desurvey(st, 0, 0, 0)
    r = 200 / np.pi
    assert np.isclose(tr["x"].iloc[-1], r, atol=1e-6) and np.isclose(tr["z"].iloc[-1], -r, atol=1e-6)
