"""P1 R10-R13, R19: per-element limits, QC reference DL, absolute blank
limits, absolute high-grade threshold, and the NLR preset."""

import random

import pytest

from conftest import make_project
from geoqaqc.analysis import run_analysis
from geoqaqc.diagnosis import diagnose
from geoqaqc.elements import criteria_for
from geoqaqc.presets import NLR, apply_preset
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, FormulaBook, RuleBook)

ELS = ("Cu_PPm", "Au_ppb")


def books(preset=True):
    rb = RuleBook()
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S = dict(DEFAULT_SETTINGS)
    if preset:
        apply_preset(NLR, rb, C, S)
    return rb, C, S


def run(rows, rb, C, S, els=ELS):
    p, S0 = make_project(rows, None, els)
    S0.update(S)
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S0, rb, log=lambda m: None)
    return p, R, diagnose(p, R, C, S0, rb)


def test_preset_loads_section_4():
    rb, C, S = books()
    assert rb.el.preset == NLR
    assert rb.el.method("Au_ppb") == "FA" and rb.el.method("Cu_PPm") == "TOTAL"
    assert rb.el.qc_dl("Cu_PPm", "ppm") == 5.0
    assert rb.el.qc_dl("Au_ppb", "ppb") == pytest.approx(5.0)
    assert rb.el.upper("Cu_PPm", "ppm") == pytest.approx(10000)
    assert rb.el.blank_limits("Au_ppb", "ppb", 5.0) == (pytest.approx(25), pytest.approx(50))
    assert rb.el.blank_limits("Cu_PPm", "ppm", 5.0) == (25.0, 50.0)
    assert rb.el.high_grade("Cu_PPm", "ppm") == pytest.approx(5000)
    cu, au, mo = (criteria_for(C, rb, e) for e in ("Cu_PPm", "Au_ppb", "Mo_ppm"))
    assert [cu["pdup_hard90"]["cuts"][2], au["pdup_hard90"]["cuts"][2],
            mo["pdup_hard90"]["cuts"][2]] == [5, 15, 10]
    assert cu["fdup_hard90"]["cuts"][2] == 20 and au["cdup_hard90"]["cuts"][2] == 20
    assert criteria_for(C, rb, "Ag_ppm")["pdup_hard90"]["cuts"] == \
        DEFAULT_CRITERIA["pdup_hard90"]["cuts"]          # other elements: defaults
    assert S["min_pairs"] == 20 and rb["drift_p"] == 0.01 and rb["bias_min_n"] == 10
    assert C["maxmin_fail"]["cuts"] == [3, 5, 10, 15, 20]


def _pulp_pairs(rel=0.07, n=30):
    rng = random.Random(1)
    rows = [{"SAMPLE_ID": "L", "Cu_PPm": "<1", "Au_ppb": "<1"}]
    for i in range(n):
        cu, au = rng.uniform(500, 5000), rng.uniform(200, 2000)
        s = 1 if i % 2 else -1
        rows.append({"SAMPLE_ID": f"S{i}", "Cu_PPm": f"{cu:.1f}", "Au_ppb": f"{au:.1f}"})
        rows.append({"SAMPLE_ID": f"P{i}", "SAMPLE_TYPE": "PULP DUP", "PARENT_ID": f"S{i}",
                     "Cu_PPm": f"{cu * (1 + s * rel):.1f}", "Au_ppb": f"{au * (1 + s * rel):.1f}"})
    return rows


def test_same_precision_judged_against_each_elements_limit():
    # HARD ~3.4 % on every pair: within Au's pulp limit (15 %), and with the
    # preset Cu limit at 5 % also within, but beyond Cu's EXCELLENT bound
    rb, C, S = books()
    p, R, d = run(_pulp_pairs(0.07), rb, C, S)
    cu, au = R["dup"][("PULP DUP", "Cu_PPm")], R["dup"][("PULP DUP", "Au_ppb")]
    assert cu["hard_p90"] == pytest.approx(au["hard_p90"], rel=0.01)
    assert cu["ratings"]["pdup_hard90"] != au["ratings"]["pdup_hard90"]
    # max-min acceptance line follows the element's GOOD boundary
    assert cu["maxmin"]["limit_hard"] == 5 and au["maxmin"]["limit_hard"] == 15


def test_absolute_blank_warning_and_failure():
    rb, C, S = books()
    base = [{"SAMPLE_ID": f"S{i}", "Cu_PPm": f"{300 + i}", "Au_ppb": "20"} for i in range(30)]
    base += [{"SAMPLE_ID": "L", "Cu_PPm": "<1", "Au_ppb": "<5"}]
    crm = [{"SAMPLE_ID": f"C{i}", "SAMPLE_TYPE": "CRM", "CRM_ID": "X", "Cu_PPm": "3000",
            "Au_ppb": "500"} for i in range(3)]
    certs = [("X", "Cu", 0.30, 0.01, "%"), ("X", "Au", 0.5, 0.02, "ppm")]

    def blanks(cu):
        return [{"SAMPLE_ID": f"B{i}", "SAMPLE_TYPE": "PULP BLANK",
                 "Cu_PPm": cu if i == 0 else "<1", "Au_ppb": "<5"} for i in range(12)]
    for cu, want, state in (("30", "CONDITIONAL", "warn"), ("60", "REJECTED", "fail")):
        p, S0 = make_project(base + crm + blanks(cu), certs, ELS)
        S0.update(S)
        R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S0, rb, log=lambda m: None)
        d = diagnose(p, R, C, S0, rb)
        rec = R["blank"][("PULP BLANK", "Cu_PPm")]
        assert rec["limit"] == 50.0 and rec["warn_limit"] == 25.0
        assert d.decision("Cu_PPm")[0] == want, state


def test_qc_reference_dl_drives_cuts():
    rb, C, S = books()
    p, R, d = run(_pulp_pairs(0.02), rb, C, S)
    rec = R["dup"][("PULP DUP", "Cu_PPm")]
    assert rec["kdl_dl"] == 5.0                                  # not the 1 ppm lab DL
    th = R["th"].get(("PULP DUP", "Cu_PPm"))
    if th:
        assert th["c_requested"] == pytest.approx(5.0 * S["th_at_dl"])


def test_preset_and_element_criteria_survive_the_session():
    from geoqaqc import session
    from geoqaqc.model import Project
    rb, C, S = books()
    rb.el.set("Cu", "criteria", {"pdup_hard90": [1, 2, 4, 6, 8]})
    st = session.state(Project(), FormulaBook(DEFAULT_FORMULAS), C, S, rb)
    rb2 = RuleBook(st["rules"])
    assert rb2.el.preset == NLR
    assert criteria_for(C, rb2, "Cu_PPm")["pdup_hard90"]["cuts"][2] == 4
    assert rb2.el.method("Au_ppb") == "FA"


def test_report_prints_preset_and_each_elements_limits(tmp_path):
    from geoqaqc.report.builder import build_report
    from geoqaqc.report.document import ReportMeta
    from geoqaqc.report.html_writer import write_html
    rb, C, S = books()
    p, R, d = run(_pulp_pairs(0.07), rb, C, S)
    doc = build_report(p, R, d, ReportMeta(project="t"), FormulaBook(DEFAULT_FORMULAS), C,
                       dict(DEFAULT_SETTINGS, **S), rb, log=lambda m: None)
    h = open(write_html(doc, str(tmp_path / "r.html")), encoding="utf-8").read()
    assert NLR in h
    assert "حدهای پذیرش به‌کاررفته برای هر عنصر" in h
    assert "خطای داخلی" not in h
