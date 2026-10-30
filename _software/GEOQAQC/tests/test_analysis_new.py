import math
import random

import pytest

from conftest import CERTS, crm_rows, make_project
from geoqaqc.analysis import run_analysis
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS, FormulaBook,
                              RuleBook)

CU_CERTS = [c for c in CERTS if c[1] == "Cu_pct"]


def analyse(rows, certs=CERTS, elements=("Cu_pct", "Au_ppm"), rb=None):
    p, S = make_project(rows, certs, elements)
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS),
                     {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}, S,
                     rb or RuleBook(), log=lambda m: None)
    return p, R


# ---- CRM drift, CUSUM, batch bias -------------------------------------------
def _drift_rows(bias_end, noise):
    rng = random.Random(7)
    rows = []
    for i in range(40):
        b = bias_end * i / 39.0 + rng.uniform(-noise, noise)
        rows.append({"SAMPLE_ID": f"C{i}", "SAMPLE_TYPE": "CRM",
                     "CRM_ID": "OREAS-501b", "BATCH": f"B{i // 10}",
                     "Cu_pct": f"{0.283 * (1 + b / 100):.5f}"})
    return rows


def test_drift_detected():
    _, R = analyse(_drift_rows(-6.0, 0.3), CU_CERTS, ("Cu_pct",))
    rec = R["crm"][("OREAS-501b", "Cu_pct")]
    assert rec["drift"]["sig"] is True
    assert rec["drift"]["total"] == pytest.approx(-6.0, abs=0.5)
    assert rec["cusum"]["signals"]                       # sustained low bias
    assert [b["batch"] for b in rec["batch_bias"]] == ["B0", "B1", "B2", "B3"]
    assert rec["batch_bias"][3]["bias"] < rec["batch_bias"][0]["bias"]


def test_no_drift_noise():
    _, R = analyse(_drift_rows(0.0, 2.0), CU_CERTS, ("Cu_pct",))
    assert R["crm"][("OREAS-501b", "Cu_pct")]["drift"]["sig"] is False


def test_rsd_ratio():
    _, R = analyse(_drift_rows(0.0, 2.0), CU_CERTS, ("Cu_pct",))
    rec = R["crm"][("OREAS-501b", "Cu_pct")]
    cert_rsd = 0.009 / 0.283 * 100
    assert rec["rsd_ratio"] == pytest.approx(rec["rsd_pct"] / cert_rsd)


# ---- accuracy curve and coverage ----------------------------------------------
def test_accuracy_curve_proportional():
    rows = (crm_rows("OREAS-501b", 0.283 * 1.1, 0.312, start=0)
            + crm_rows("OREAS-504b", 1.052 * 1.1, 0.905, start=10)
            + crm_rows("CDN-ME-1", 0.505 * 1.1, 1.48, start=20))
    _, R = analyse(rows)
    acc = R["accuracy"]["Cu_pct"]
    assert acc["n_crm"] == 3
    assert acc["prop_bias_pct"] == pytest.approx(10.0, abs=0.5)
    assert acc["const_bias"] == pytest.approx(0.0, abs=0.005)
    assert acc["p_slope"] is not None and acc["p_slope"] < 0.05
    au = R["accuracy"]["Au_ppm"]
    assert au["prop_bias_pct"] == pytest.approx(0.0, abs=0.5)


def test_coverage():
    rows = crm_rows("OREAS-501b", 0.283, 0.312)
    rows += [{"SAMPLE_ID": f"N{i}", "Cu_pct": f"{0.5 + i * 0.1:.2f}",
              "Au_ppm": "0.5"} for i in range(20)]
    _, R = analyse(rows, CU_CERTS, ("Cu_pct", "Au_ppm"))
    cov = R["coverage"]["Cu_pct"]
    assert set(cov["pcts"]) == {10.0, 50.0, 90.0}
    # only CRMs that were actually inserted count towards coverage
    assert cov["certs"] == [("OREAS-501b", pytest.approx(0.283))]
    assert cov["none_above_p90"] is True                 # P90 = 2.31 % Cu
    # 101 quantiles (P0..P100) of the routine grades for the coverage chart
    q = cov["quantiles"]
    assert len(q) == 101 and q[0][0] == 0 and q[-1] == (100, pytest.approx(2.4))


# ---- duplicates: error budget, max-min, quartiles, split ---------------------
def _dup_rows(cv, dtype, prefix, n=10, bias=0.0):
    d = cv / math.sqrt(2)       # pair CV^2 = 2 d^2 for a = m(1+d), b = m(1-d)
    rows = []
    for i in range(n):
        m = 0.5 + 0.05 * i
        s = 1 if i % 2 else -1
        rows.append({"SAMPLE_ID": f"{prefix}{i}", "SAMPLE_TYPE": "SAMPLE",
                     "Cu_pct": f"{m * (1 + s * d):.6f}"})
        rows.append({"SAMPLE_ID": f"{prefix}{i}-D", "SAMPLE_TYPE": dtype,
                     "PARENT_ID": f"{prefix}{i}",
                     "Cu_pct": f"{m * (1 - s * d) * (1 + bias):.6f}"})
    return rows


def _dl():
    return [{"SAMPLE_ID": f"L{i}", "Cu_pct": "<0.001"} for i in range(3)]


def test_error_budget():
    rows = (_dup_rows(0.30, "FIELD DUP", "F") + _dup_rows(0.15, "COARSE DUP", "C")
            + _dup_rows(0.05, "PULP DUP", "P") + _dl())
    _, R = analyse(rows, None, ("Cu_pct",))
    b = R["budget"]["Cu_pct"]
    assert b["cv2"]["field"] == pytest.approx(0.09, rel=0.01)
    assert b["pct"]["sampling"] == pytest.approx(75.0, abs=3)
    assert b["pct"]["preparation"] == pytest.approx(22.2, abs=3)
    assert b["dominant"] == "sampling"
    assert b["merged"] is None
    assert b["total_cv_pct"] == pytest.approx(30.0, abs=1)


def test_error_budget_missing_coarse():
    rows = _dup_rows(0.30, "FIELD DUP", "F") + _dup_rows(0.05, "PULP DUP", "P") + _dl()
    _, R = analyse(rows, None, ("Cu_pct",))
    b = R["budget"]["Cu_pct"]
    assert b["merged"] == "sampling+preparation"
    assert set(b["pct"]) == {"sampling+preparation", "analytical"}
    assert b["dominant"] == "sampling+preparation"


def test_maxmin_and_quartiles():
    _, R = analyse(_dup_rows(0.30, "FIELD DUP", "F") + _dl(), None, ("Cu_pct",))
    rec = R["dup"][("FIELD DUP", "Cu_pct")]
    assert rec["maxmin"]["limit_hard"] == 20
    assert rec["maxmin"]["ratio_line"] == pytest.approx(1.5)
    assert rec["maxmin"]["fail_pct"] == pytest.approx(100.0)   # HARD 21.2 % > 20
    assert len(rec["quartiles"]) == 4
    assert sum(q["n"] for q in rec["quartiles"]) == rec["n"]


def test_splitting_bias():
    rows = _dup_rows(0.05, "FIELD DUP", "F", n=12, bias=-0.12) + _dl()
    _, R = analyse(rows, None, ("Cu_pct",))
    sp = R["dup"][("FIELD DUP", "Cu_pct")]["split"]
    assert sp["sig"] is True
    rows = _dup_rows(0.05, "FIELD DUP", "F", n=12) + _dl()
    _, R = analyse(rows, None, ("Cu_pct",))
    assert R["dup"][("FIELD DUP", "Cu_pct")]["split"]["sig"] is False


# ---- batches and re-assay ranges ------------------------------------------------
def _batch_rows():
    rows = []
    for seq in range(1, 61):
        batch = f"B{(seq - 1) // 20 + 1}"
        if seq in (10, 30, 50):
            v = 0.283 + (4 * 0.009 if seq == 30 else 0.001)
            rows.append({"SAMPLE_ID": f"STD{seq}", "SAMPLE_TYPE": "CRM",
                         "CRM_ID": "OREAS-501b", "BATCH": batch, "SEQ": seq,
                         "Cu_pct": f"{v:.4f}"})
        else:
            rows.append({"SAMPLE_ID": f"S{seq:02d}", "SAMPLE_TYPE": "SAMPLE",
                         "BATCH": batch, "SEQ": seq, "Cu_pct": "0.4"})
    return rows


def test_reassay_range():
    _, R = analyse(_batch_rows(), CU_CERTS, ("Cu_pct",))
    ra = R["batches"]["Cu_pct"]["reassay"]
    assert len(ra) == 1
    r = ra[0]
    assert (r["failed_sample"], r["from_sample"], r["to_sample"]) == (
        "STD30", "S11", "S49")
    assert r["n_samples"] == 38
    assert r["batch"] == "B2" and "1-3s" in r["rule"]


def test_batch_status():
    _, R = analyse(_batch_rows(), CU_CERTS, ("Cu_pct",))
    st = {b["batch"]: b["status"] for b in R["batches"]["Cu_pct"]["rows"]}
    assert st == {"B1": "PASS", "B2": "FAIL", "B3": "PASS"}
    rb = RuleBook()
    rb.set("batch_fail_rules", [])
    _, R = analyse(_batch_rows(), CU_CERTS, ("Cu_pct",), rb=rb)
    st = {b["batch"]: b["status"] for b in R["batches"]["Cu_pct"]["rows"]}
    assert st["B2"] == "WARN"
    assert R["batches"]["Cu_pct"]["reassay"] == []


# ---- blanks: carry-over -------------------------------------------------------
def test_carry_over_split():
    rows = _dl()
    for i in range(10):
        hi = i < 4
        rows.append({"SAMPLE_ID": f"N{i}", "Cu_pct": "5.0" if hi else "0.005"})
        rows.append({"SAMPLE_ID": f"BL{i}", "SAMPLE_TYPE": "COARSE BLANK",
                     "Cu_pct": "0.05" if hi else "0.001"})
    _, R = analyse(rows, None, ("Cu_pct",))
    rec = R["blank"][("COARSE BLANK", "Cu_pct")]
    assert rec["fail_after_high_pct"] == pytest.approx(100.0)
    assert rec["fail_other_pct"] == pytest.approx(0.0)
    assert rec["rho"] > 0.5
    assert rec["btype"] == "COARSE BLANK"


def test_pooled_drift_per_element():
    # three CRMs interleaved, each falling 0 -> -6 % with noise of ~1 SD:
    # each CRM alone is weak evidence, the pooled series is not
    rng = random.Random(3)
    rows = []
    certs = {"OREAS-501b": (0.283, 0.009), "OREAS-504b": (1.052, 0.028),
             "CDN-ME-1": (0.505, 0.015)}
    for i in range(60):
        code = list(certs)[i % 3]
        c, sd = certs[code]
        b = -6.0 * i / 59.0
        v = c * (1 + b / 100) + rng.gauss(0, sd)
        rows.append({"SAMPLE_ID": f"C{i}", "SAMPLE_TYPE": "CRM", "CRM_ID": code,
                     "Cu_pct": f"{v:.5f}"})
    _, R = analyse(rows, CU_CERTS, ("Cu_pct",))
    d = R["drift"]["Cu_pct"]
    assert d["n"] == 60
    assert d["sig"] is True
    # SE of the total is ~1.3 % here (60 points, noise 1 SD ~ 3 %)
    assert d["total"] == pytest.approx(-6.0, abs=3.0)


def test_carry_over_relative_grade():
    # every predecessor is far above 10 x DL; only the richest ones carry over
    rows = _dl()
    for i in range(12):
        hi = i < 3
        rows.append({"SAMPLE_ID": f"N{i}", "Cu_pct": "3.5" if hi else f"{0.2 + i * 0.01:.2f}"})
        rows.append({"SAMPLE_ID": f"BL{i}", "SAMPLE_TYPE": "COARSE BLANK",
                     "Cu_pct": "0.05" if hi else "0.001"})
    _, R = analyse(rows, None, ("Cu_pct",))
    rec = R["blank"][("COARSE BLANK", "Cu_pct")]
    assert rec["fail_after_high_pct"] == pytest.approx(100.0)
    assert rec["fail_other_pct"] == pytest.approx(0.0)
