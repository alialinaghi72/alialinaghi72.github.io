"""P1 R15, R16, R18: insertion targets, CRM repeatability against the
certificate, CRM grade coverage (P25-P90, cut-off, method upper limit)."""

import os

import pytest

from conftest import TEST_DATA


def _demo(rb_setup=None):
    from geoqaqc.analysis import run_analysis
    from geoqaqc.diagnosis import diagnose
    from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                                  DEFAULT_SETTINGS, FormulaBook, RuleBook)
    from conftest import DATA
    from geoqaqc.loader import load_project
    p = load_project(os.path.join(DATA, "demo_assay.csv"),
                     os.path.join(DATA, "demo_crm_certificates.csv"),
                     os.path.join(DATA, "demo_umpire.csv"))
    rb = RuleBook()
    if rb_setup:
        rb_setup(rb, p)
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S = dict(DEFAULT_SETTINGS)
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S, rb, log=lambda m: None)
    return p, R, diagnose(p, R, C, S, rb), rb


def test_rsd_rated_on_ratio_to_certificate():
    from geoqaqc.protocol import rate
    from geoqaqc.protocol import DEFAULT_CRITERIA
    p, R, d, rb = _demo()
    rated = [r for r in R["crm"].values() if r.get("rsd_basis")]
    assert rated
    for r in rated:
        if r["rsd_basis"] == "ratio":
            assert r["ratings"]["crm_rsd"] == rate(r["rsd_ratio"],
                                                   DEFAULT_CRITERIA["crm_rsd_ratio"])
    # off: the 2.0 absolute rating
    p, R2, d, rb = _demo(lambda rb, p: rb.set("rsd_by_ratio", False))
    assert all(r["rsd_basis"] == "absolute"
               for r in R2["crm"].values() if r.get("rsd_basis"))


def test_coverage_cutoff_and_upper_limit():
    def setup(rb, p):
        rb.el.set("Cu_pct", "cutoff", 1e9)           # far from every CRM
        rb.el.set("Cu_pct", "upper", 1e-9)           # below every CRM
    p, R, d, rb = _demo(setup)
    el = next(e for e in p.elements if e.lower().startswith("cu"))
    cov = R["coverage"][el]
    assert cov["no_cutoff_crm"] and len(cov["above_upper"]) == len(cov["certs"])
    codes = {f.code for f in d.by_element(el)}
    assert {"CRM_CUTOFF", "CRM_ABOVE_UPPER"} <= codes
    f = next(f for f in d.by_element(el) if f.code == "CRM_CUTOFF")
    assert f.severity == "MATERIAL" and f.root == "PROGRAMME"


def test_coverage_gap_p25_p90_flag():
    p, R, d, rb = _demo()
    for el, cov in R["coverage"].items():
        cv = [c for _, c in cov["certs"]]
        assert cov["gap_p25_p90"] == (bool(cv) and not any(cov["p25"] <= c <= cov["p90"]
                                                            for c in cv))
        assert ("CRM_GAP" in {f.code for f in d.by_element(el)}) == cov["gap_p25_p90"]


ASSAY = os.path.join(TEST_DATA, "BATH16.csv")
CERT = os.path.join(TEST_DATA, "crm.csv")


@pytest.mark.skipif(not (os.path.exists(ASSAY) and os.path.exists(CERT)),
                    reason="BATH16.csv / crm.csv not in tests/data")
def test_batch16_gbm922_above_icp_upper_limit():
    """GBM922-12 at 1.40 % Cu is above the 1 % upper limit of the routine ICP."""
    from geoqaqc.analysis import run_analysis
    from geoqaqc.diagnosis import diagnose
    from geoqaqc.loader import load_project
    from geoqaqc.presets import NLR, apply_preset
    from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                                  DEFAULT_SETTINGS, FormulaBook, RuleBook)
    p = load_project(ASSAY, CERT)
    rb = RuleBook()
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S = dict(DEFAULT_SETTINGS)
    apply_preset(NLR, rb, C, S)
    cu = next(c for c, _ in p.assay.value_cols if c.lower().startswith("cu"))
    au = next(c for c, _ in p.assay.value_cols if c.lower().startswith("au"))
    rb.el.set_method(au, "FA")
    rb.el.set_method(cu, "TOTAL")
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S, rb, log=lambda m: None)
    d = diagnose(p, R, C, S, rb)
    cov = R["coverage"][cu]
    assert any("922" in lab for lab, _ in cov["above_upper"])
    assert "CRM_ABOVE_UPPER" in {f.code for f in d.by_element(cu)}
