"""Section 5 regression checks on a synthetic batch shaped like NLR Batch 16
(tests/batch16.py), plus R24. test_p0_batch16_real.py runs the same checks on
the real BATH16.csv when it is in tests/data."""

import pytest

import batch16 as B
from conftest import make_project
from geoqaqc.analysis import run_analysis
from geoqaqc.diagnosis import diagnose
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, FormulaBook, RuleBook)


def _rb():
    rb = RuleBook()
    rb.el.set_method("Au_ppb", "FA")          # Batch 16 gold: fire assay
    rb.el.set_method("Cu_PPm", "TOTAL")       # four-acid total copper
    return rb


@pytest.fixture(scope="module")
def b16():
    p, S = make_project(B.rows(), B.CERTS, B.ELS)
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    rb = _rb()
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S, rb, log=lambda m: None)
    return p, R, diagnose(p, R, C, S, rb), C, S, rb


def test_1_g913_gold_against_fire_assay(b16):
    p, R, d, *_ = b16
    rec = R["crm"][("G913-4", "Au_ppb")]
    assert rec["cert"] == pytest.approx(1370) and rec["sd"] == pytest.approx(40)
    assert rec["method"] == "FA"
    assert rec["points"][-1]["z"] < -3
    assert rec["bias"] == pytest.approx(-5.75, abs=0.5)
    assert rec["n"] < 10                                   # insufficient for a rating
    assert not [f for f in d.by_element("Au_ppb") if f.code in ("CRM_BIAS", "CRM_SYSTEMATIC")]
    code, reasons, ranges = d.decision("Au_ppb")
    assert code == "REJECTED"
    r = [x for x in ranges if x["control"] == "CRM" and "G913-4" in x["crm"]][0]
    assert r["bracket_from"] == "STD-G913-3" and r["bracket_to"] == "(end of batch)"


def test_2_g913_copper_not_certified(b16):
    p, R, d, *_ = b16
    rec = R["crm"][("G913-4", "Cu_PPm")]
    assert rec["status"] == "NOT_CERTIFIED" and rec["ratings"] == {}


def test_3_gbm922_step_and_2_2s(b16):
    p, R, d, *_ = b16
    rec = R["crm"][("GBM922-12", "Cu_PPm")]
    assert rec["cert"] == pytest.approx(13975)
    rules = {r["rule"] for r in rec["rules"]}
    assert "2-2s" in rules
    assert rec["shift"] and rec["shift"]["after"] == 3
    assert not [f for f in d.by_element("Cu_PPm") if f.code == "CRM_DRIFT"]
    assert R["drift"]["Cu_PPm"].get("insufficient")
    f = [x for x in d.by_element("Cu_PPm") if x.code == "CRM_FAIL"][0]
    assert f.severity == "CRITICAL" and "2-2s" in f.evidence_fa
    shift = [x for x in d.by_element("Cu_PPm") if x.code == "CRM_SHIFT"]
    assert shift and "پله‌ای" in shift[0].evidence_fa
    ranges = [x for x in d.decision("Cu_PPm")[2] if x["control"] == "CRM"]
    assert ranges[0]["bracket_from"] == "(start of batch)"
    assert ranges[0]["bracket_to"] == "STD-GBM-3"            # the 4th GBM922-12
    assert ranges[0]["from_sample"] == "NLR-0000"


def test_4_oreas906_total_copper_and_monitoring_molybdenum():
    els = ("Cu_PPm", "Au_ppb", "Mo_ppm")
    p, S = make_project(B.oreas906_rows(), B.CERTS, els)
    rb = _rb()
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS),
                     {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}, S, rb,
                     log=lambda m: None)
    assert R["crm"][("OREAS906", "Cu_PPm")]["cert"] == pytest.approx(3100)   # 0.310 %
    mo = R["crm"][("OREAS906", "Mo_ppm")]
    assert mo["status"] == "MONITORING" and mo["ratings"] == {} and mo["rules"] == []


def test_5_over_limit_listed(b16):
    p, R, d, *_ = b16
    f = [x for x in d.findings if x.code == "OVER_LIMIT" and x.element == "Cu_PPm"][0]
    assert "NLR-0060" in f.evidence_fa and "NLR-0140" in f.evidence_fa
    assert f.severity == "MATERIAL"


def test_6_spreadsheet_errors(b16):
    p, *_ = b16
    rules = [a.rule for a in p.clean_log.actions if a.element == "Au_ppb"]
    assert rules.count("C19") == 5 and "C04" not in rules


def test_7_mispairs_both_variants_and_budget(b16):
    p, R, d, *_ = b16
    cand = [r for r in R["exclusions"] if r["element"] == "Cu_PPm" and r["trigger"] != "low-grade"]
    assert len([r for r in cand if r["dtype"] == "COARSE DUP"]) == 7
    assert len([r for r in cand if r["dtype"] == "PULP DUP"]) >= 2
    a, b = R["dup_all"][("COARSE DUP", "Cu_PPm")], R["dup"][("COARSE DUP", "Cu_PPm")]
    assert b["hard_p90"] < a["hard_p90"]
    assert R["budget"]["Cu_PPm"]["estimable"] is False          # 8 field pairs < 30


def test_8_thompson_howarth_both_variants(b16):
    p, R, d, *_ = b16
    a, b = R["th_all"].get(("PULP DUP", "Cu_PPm")), R["th"].get(("PULP DUP", "Cu_PPm"))
    assert a and b
    assert b["precision_at_ref"] < a["precision_at_ref"]


def test_9_limits_print_as_entered(tmp_path, b16):
    from geoqaqc.report.builder import build_report
    from geoqaqc.report.document import ReportMeta
    from geoqaqc.report.html_writer import write_html
    p, R, d, C, S, rb = b16
    C = {k: dict(v) for k, v in C.items()}
    C["pdup_hard90"]["cuts"] = [2.5, 4.0, 7.5, 10.0, 15.0]
    doc = build_report(p, R, d, ReportMeta(project="B16"), FormulaBook(DEFAULT_FORMULAS),
                       C, dict(DEFAULT_SETTINGS), rb, log=lambda m: None)
    h = open(write_html(doc, str(tmp_path / "r.html")), encoding="utf-8").read()
    assert "7.5%" in h                    # R23: Latin digits in tables
    assert "8%" not in h.split("7.5%")[0][-6:]


def test_r24_review_window_content(b16):
    p, R, d, *_ = b16
    pend = [r for r in R["exclusions"] if r.get("pending")]
    cu = [r for r in pend if r["element"] == "Cu_PPm"]
    assert len([r for r in cu if r["dtype"] == "COARSE DUP"]) == 7
    assert len([r for r in cu if r["dtype"] == "PULP DUP"]) >= 2
    au = [r for r in pend if r["element"] == "Au_ppb"]
    assert au and all(r["decision"] == "keep" for r in au)


def test_drift_never_critical_on_five_points(b16):
    p, R, d, *_ = b16
    assert not [f for f in d.findings if f.code == "CRM_DRIFT" and f.severity == "CRITICAL"]
