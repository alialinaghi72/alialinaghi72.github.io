"""Section 5 checks on the real NLR Batch 16 file. Put BATH16.csv and the
original certificate file crm.csv in tests/data; without them these tests
are skipped. Column methods: Au_ppb = fire assay, Cu_PPm = total."""

import os

import pytest

from conftest import TEST_DATA

ASSAY = os.path.join(TEST_DATA, "BATH16.csv")
CERT = os.path.join(TEST_DATA, "crm.csv")
pytestmark = pytest.mark.skipif(not (os.path.exists(ASSAY) and os.path.exists(CERT)),
                                reason="BATH16.csv / crm.csv not in tests/data")


@pytest.fixture(scope="module")
def real():
    from geoqaqc.analysis import run_analysis
    from geoqaqc.cleaning import norm_code
    from geoqaqc.diagnosis import diagnose
    from geoqaqc.loader import load_project
    from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                                  DEFAULT_SETTINGS, FormulaBook, RuleBook)
    p = load_project(ASSAY, CERT)
    rb = RuleBook()
    cu = next(c for c, _ in p.assay.value_cols if c.lower().startswith("cu"))
    au = next(c for c, _ in p.assay.value_cols if c.lower().startswith("au"))
    rb.el.set_method(au, "FA")
    rb.el.set_method(cu, "TOTAL")
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S = dict(DEFAULT_SETTINGS)
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S, rb, log=lambda m: None)
    d = diagnose(p, R, C, S, rb)
    lab = {norm_code(v): v for v in p.crm_labels.values()}
    return p, R, d, cu, au, lab


def _rec(R, lab, code, el):
    from geoqaqc.cleaning import norm_code
    name = lab.get(norm_code(code), code)
    return R["crm"].get((name, el))


def test_g913_gold_fire_assay(real):
    p, R, d, cu, au, lab = real
    rec = _rec(R, lab, "G913-4", au)
    f = 1000.0 if "ppb" in au.lower() else 1.0
    assert rec["cert"] == pytest.approx(1.37 * f) and rec["sd"] == pytest.approx(0.04 * f)
    assert rec["points"][-1]["z"] < -3
    assert rec["n"] < 10
    assert d.decision(au)[0] == "REJECTED"


def test_g913_copper_not_certified(real):
    p, R, d, cu, au, lab = real
    assert _rec(R, lab, "G913-4", cu)["status"] == "NOT_CERTIFIED"


def test_gbm922_step_shift_no_drift(real):
    p, R, d, cu, au, lab = real
    rec = _rec(R, lab, "GBM922-12", cu)
    assert "2-2s" in {r["rule"] for r in rec["rules"]}
    assert rec["shift"] and rec["shift"]["after"] == 3
    assert not [f for f in d.by_element(cu) if f.code == "CRM_DRIFT"]


def test_over_limit_and_spreadsheet_errors(real):
    p, R, d, cu, au, lab = real
    ol = [s for s in p.samples if s.flags.get(cu) == ">"]
    assert len(ol) == 2
    assert [x for x in d.findings if x.code == "OVER_LIMIT" and x.element == cu]
    assert sum(1 for a in p.clean_log.actions if a.rule == "C19" and a.element == au) == 5


def test_mispairs_review_and_budget(real):
    p, R, d, cu, au, lab = real
    cand = [r for r in R["exclusions"] if r["element"] == cu and r["trigger"] != "low-grade"]
    assert len([r for r in cand if r["dtype"] == "COARSE DUP"]) >= 7
    assert len([r for r in cand if r["dtype"] == "PULP DUP"]) >= 2
    a, b = R["dup_all"][("COARSE DUP", cu)], R["dup"][("COARSE DUP", cu)]
    assert b["hard_p90"] < a["hard_p90"]
    assert R["budget"][cu]["estimable"] is False
    assert all(r["decision"] == "keep" for r in R["exclusions"]
               if r["element"] == au and r["trigger"] != "low-grade" and r.get("pending"))
