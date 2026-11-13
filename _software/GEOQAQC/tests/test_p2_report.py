"""P2: R21 assessment mode, R22 report structure, R23 terminology."""

import re

import pytest

import batch16 as B
from conftest import make_project
from geoqaqc.analysis import run_analysis
from geoqaqc.diagnosis import diagnose
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, FormulaBook, RuleBook)
from geoqaqc.report import texts_fa as T
from geoqaqc.report.builder import build_report
from geoqaqc.report.document import ReportMeta
from geoqaqc.report.html_writer import write_html


def _run(mode="concurrent"):
    p, _ = make_project(B.rows(), B.CERTS, B.ELS)
    rb = RuleBook()
    rb.el.set_method("Au_ppb", "FA")
    rb.el.set_method("Cu_PPm", "TOTAL")
    rb.set("assessment_mode", mode)
    F = FormulaBook(DEFAULT_FORMULAS)
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S = dict(DEFAULT_SETTINGS)
    R = run_analysis(p, F, C, S, rb, log=lambda m: None)
    return p, R, diagnose(p, R, C, S, rb), F, C, S, rb


@pytest.fixture(scope="module")
def conc():
    return _run()


@pytest.fixture(scope="module")
def retro():
    return _run("retrospective")


def _html(run, tmp_path, meta=None):
    p, R, d, F, C, S, rb = run
    meta = meta or ReportMeta(project="North Lar (NLR)")
    doc = build_report(p, R, d, meta, F, C, S, rb, log=lambda m: None)
    return open(write_html(doc, str(tmp_path / "r.html")), encoding="utf-8").read(), meta


# ---- R23 ------------------------------------------------------------------------
def test_terminology_matches_the_spec(conc, tmp_path):
    assert T.TYPE_FA["CRM"] == "نمونه استاندارد"
    assert T.TYPE_FA["BLANK"] == "شاهد"
    assert T.TYPE_FA["COARSE BLANK"] == "شاهد درشت" and T.TYPE_FA["PULP BLANK"] == "شاهد پالپ"
    assert T.TYPE_FA["COARSE DUP"] == "تکراری درشت"
    assert T.TYPE_FA["CHECK / UMPIRE"] == "آزمایشگاه داور"
    h, _ = _html(conc, tmp_path)
    for old in ("شاهد خالی", "تکراری خردایش", "آزمایشگاه دوم", "نمونهٔ استاندارد"):
        assert old not in h, old
    assert "نمونه استاندارد" in h


def test_latin_digits_in_tables_persian_in_prose(conc, tmp_path):
    h, _ = _html(conc, tmp_path)
    part = h.split(T.COMPLIANCE_INTRO)[1].split("</table>")[0]
    cells = re.findall(r"<td[^>]*>(.*?)</td>", part)
    assert cells and not any(re.search(r"[۰-۹]", c) for c in cells)
    assert any(re.search(r"[0-9]", c) for c in cells)
    paras = re.findall(r"<p>(.*?)</p>", h)
    assert any(re.search(r"[۰-۹]", x) for x in paras)


# ---- R21 ------------------------------------------------------------------------
def test_retrospective_actions_and_impact(conc, retro, tmp_path):
    dc, dr = conc[2], retro[2]
    ins_c = [f for f in dc.findings if f.code in ("INS_RATE", "INS_MISSING", "CRM_GAP")]
    ins_r = [f for f in dr.findings if f.code in ("INS_RATE", "INS_MISSING", "CRM_GAP")]
    assert ins_c and len(ins_c) == len(ins_r)
    for a, b in zip(ins_c, ins_r):
        assert a.actions_fa != b.actions_fa
    assert all(f.impact_fa for f in dr.findings if f.severity == "CRITICAL")
    assert dr.mode == "retrospective" and dc.mode == "concurrent"
    h, _ = _html(retro, tmp_path)
    assert T.RETRO_NOTE[:30] in h and "اثر بر طبقه‌بندی منابع" in h


# ---- R22 ------------------------------------------------------------------------
def test_metadata_from_data(conc, tmp_path):
    h, meta = _html(conc, tmp_path)
    assert meta.report_no == "NLR-QAQC-RPT-B16 Rev. 0"
    assert meta.batches == "B16"
    assert meta.author_title == "کارشناس ارشد اکتشاف معدن"
    assert "NLR-QAQC-RPT-B16" in h and "حالت ارزیابی" in h


def test_compliance_table_and_insufficient_data(conc, tmp_path):
    from geoqaqc.compliance import compliance
    p, R, d, F, C, S, rb = conc
    rows = compliance(p, R, C, S, rb)
    by = {(r["element"], r["control"], r["criterion"]): r for r in rows}
    g = by[("Au_ppb", "G913-4", "bias")]
    assert g["n"] < rb["bias_min_n"] and g["result"] == "INSUFFICIENT"
    assert by[("Au_ppb", "G913-4", "rules")]["result"] == "FAIL"
    small = [r for r in rows if r["criterion"] in ("hard90", "cv_avg", "umpire")
             and r["n"] < S["min_pairs"]]
    assert all(r["result"] == "INSUFFICIENT" for r in small)
    S2 = dict(S, min_pairs=1000)
    assert all(r["result"] == "INSUFFICIENT" for r in compliance(p, R, C, S2, rb)
               if r["criterion"] == "hard90")
    h, _ = _html(conc, tmp_path)
    assert T.COMPLIANCE_TITLE in h and T.INSUFFICIENT_DATA in h
    assert "امتیاز کلی" not in h.split(T.COMPLIANCE_INTRO)[0][-500:]


def test_at_most_five_key_findings(conc, tmp_path):
    h, _ = _html(conc, tmp_path)
    part = h.split(T.KEY_FINDINGS_TITLE)[-1].split("</ol>")[0]
    assert 1 <= part.count("<li>") <= 5


def test_precision_table_has_cv_avg(conc, tmp_path):
    h, _ = _html(conc, tmp_path)
    assert "CV_avg" in h and "Stanley" in h
