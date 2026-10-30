import re

import pytest

from conftest import make_project
from geoqaqc.analysis import run_analysis
from geoqaqc.diagnosis import diagnose
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, FormulaBook, RuleBook)
from geoqaqc.report import builder, texts_fa
from geoqaqc.report.builder import build_report
from geoqaqc.report.document import ReportMeta, split_runs
from geoqaqc.report.html_writer import write_html
from test_demo_detection import demo

META = ReportMeta(project="پروژهٔ مس پورفیری نمونه", client="شرکت کارفرما",
                  consultant="مشاور نمونه", author="علی علینقی", report_no="QC-1405-01",
                  date="2026-10-30")


def _run(p, R):
    F = FormulaBook(DEFAULT_FORMULAS)
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S = dict(DEFAULT_SETTINGS)
    rb = RuleBook()
    d = diagnose(p, R, C, S, rb)
    return build_report(p, R, d, META, F, C, S, rb, log=lambda m: None)


@pytest.fixture(scope="module")
def demo_html(tmp_path_factory):
    p, R = demo()
    path = tmp_path_factory.mktemp("rep") / "report.html"
    write_html(_run(p, R), str(path))
    return path.read_text(encoding="utf-8")


def test_html_demo(demo_html):
    h = demo_html
    assert 'dir="rtl"' in h and 'lang="fa"' in h
    assert "@font-face" in h and "Vazirmatn" in h
    assert h.count("<svg") >= 30
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    for name in ("مس", "طلا", "نقره", "مولیبدن"):
        assert any(name in x for x in h1), name
    assert texts_fa.VERDICT_FA["REMEDIATE"] in h
    assert "QC-1405-01" in h
    assert "۱۴۰۵/۰۸/۰۸" in h                      # Jalali date on the cover
    assert "@page" in h


def test_html_has_no_unescaped_markup_in_text(demo_html):
    # the cleaning log quotes raw cells such as '<0.01' and '>10000'
    assert "<0.0" not in re.sub(r"<(script|style)[\s\S]*?</\1>", "", demo_html)


def test_html_minimal_dataset(tmp_path):
    rows = [{"SAMPLE_ID": f"S{i}", "Cu_pct": f"{0.1 + i * 0.01:.3f}"} for i in range(20)]
    rows += [{"SAMPLE_ID": f"B{i}", "SAMPLE_TYPE": "BLANK", "Cu_pct": "<0.001"}
             for i in range(6)]
    p, S = make_project(rows, None, ("Cu_pct",))
    p.assay.mapping.pop("batch")
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS),
                     {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}, S, RuleBook(),
                     log=lambda m: None)
    path = tmp_path / "min.html"
    write_html(_run(p, R), str(path))
    h = path.read_text(encoding="utf-8")
    assert texts_fa.MISSING["crm"] in h
    assert texts_fa.MISSING["dup"] in h
    assert texts_fa.MISSING["umpire"] in h
    assert texts_fa.SECTION_ERROR not in h


def test_section_failure_isolated(tmp_path, monkeypatch):
    def boom(ctx, doc):
        raise RuntimeError("synthetic failure")
    monkeypatch.setattr(builder, "_programme", boom)
    p, R = demo()
    path = tmp_path / "r.html"
    write_html(_run(p, R), str(path))
    h = path.read_text(encoding="utf-8")
    assert texts_fa.SECTION_ERROR in h
    assert texts_fa.H["actions"] in h            # later sections still built


def test_split_runs_keeps_parentheses_outside_latin():
    runs = split_runs("نتایج مس (Cu_pct) و طلا")
    assert ("Cu_pct", True, False) in runs


def test_cover_shows_worst_verdict(demo_html):
    cover = demo_html.split('class="page cover"', 1)[1].split("</section>", 1)[0]
    assert "وضعیت کلی" in cover
    assert texts_fa.VERDICT_FA["REMEDIATE"] in cover.split("حکم کفایت")[0]


def test_split_runs():
    runs = split_runs("صدک P90 HARD برابر **۱۲٪** است")
    assert ("P90 HARD", True, False) in runs
    assert ("۱۲٪", False, True) in runs
    assert "".join(r[0] for r in runs) == "صدک P90 HARD برابر ۱۲٪ است"
