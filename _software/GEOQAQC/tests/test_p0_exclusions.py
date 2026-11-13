"""P0 R5, R14, R24: mispair candidates and the exclusion review."""

import random

import pytest

from conftest import make_project
from geoqaqc import exclusions as X
from geoqaqc.analysis import run_analysis
from geoqaqc.diagnosis import diagnose
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, FormulaBook, RuleBook)

ELS = ("Cu_PPm", "Au_ppb")


def batch(n=40, mix=7, seed=4):
    """Coarse and pulp pairs of Cu and Au, with `mix` coarse pairs whose Cu
    differs 5-57x (mix-ups) and one pulp pair 8x apart; Au varies widely
    (nugget). Below-DL values give a known DL (Cu 1 ppm, Au 5 ppb)."""
    rng = random.Random(seed)
    rows = [{"SAMPLE_ID": "LOW", "Cu_PPm": "<1", "Au_ppb": "<5"}]
    for i in range(n):
        cu = rng.uniform(300, 6000)
        au = rng.uniform(60, 900)
        rows.append({"SAMPLE_ID": f"S{i}", "Cu_PPm": f"{cu:.0f}", "Au_ppb": f"{au:.0f}"})
        f = (5 + 52 * i / max(1, mix - 1)) if i < mix else rng.uniform(0.9, 1.1)
        rows.append({"SAMPLE_ID": f"C{i}", "SAMPLE_TYPE": "COARSE DUP", "PARENT_ID": f"S{i}",
                     "Cu_PPm": f"{cu * f:.0f}",
                     "Au_ppb": f"{au * (4.0 if i == 20 else rng.uniform(0.8, 1.2)):.0f}"})
        g = 8.0 if i == 30 else rng.uniform(0.97, 1.03)
        rows.append({"SAMPLE_ID": f"P{i}", "SAMPLE_TYPE": "PULP DUP", "PARENT_ID": f"S{i}",
                     "Cu_PPm": f"{cu * g:.0f}", "Au_ppb": f"{au * rng.uniform(0.9, 1.1):.0f}"})
    return rows


def run(rows=None, rb=None, project=None):
    p, S = make_project(rows or batch(), None, ELS)
    if project is not None:
        p.pair_decisions = project.pair_decisions
    rb = rb or RuleBook()
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S, rb, log=lambda m: None)
    return p, R, diagnose(p, R, C, S, rb)


def _rows(R, el, dtype, trigger=None):
    return [r for r in R["exclusions"] if r["element"] == el and r["dtype"] == dtype
            and (trigger is None or r["trigger"] == trigger)]


def test_cu_mixups_become_candidates_and_au_never_votes_alone():
    p, R, _ = run()
    cu = [r for r in _rows(R, "Cu_PPm", "COARSE DUP") if r["trigger"] != "low-grade"]
    assert {r["orig"] for r in cu} == {f"S{i}" for i in range(7)}
    assert len([r for r in _rows(R, "Cu_PPm", "PULP DUP") if r["trigger"] != "low-grade"]) >= 1
    # the Au 4x coarse pair is an outlier for Au (HARD 60 % < 67 %: not even that)
    assert not [r for r in _rows(R, "Au_ppb", "COARSE DUP") if r["orig"] == "S20"]
    # a Cu mix-up makes the pair a C16 candidate; Au rows of it are pre-set to keep
    au = [r for r in R["exclusions"] if r["element"] == "Au_ppb" and r["trigger"] != "low-grade"]
    assert au and all(r["decision"] == "keep" and r["pending"] for r in au)


def test_both_variants_and_the_verdict_uses_the_reviewed_one():
    p, R, d = run()
    a, b = R["dup_all"][("COARSE DUP", "Cu_PPm")], R["dup"][("COARSE DUP", "Cu_PPm")]
    assert a["n"] == b["n"] + 7
    assert b["hard_p90"] < a["hard_p90"]
    assert R["th_all"].get(("PULP DUP", "Cu_PPm")) is not None
    assert X.provisional(R["exclusions"])           # pre-set exclusions: unverified


def test_decisions_are_saved_and_reapplied():
    p, R, _ = run()
    cu = [r for r in _rows(R, "Cu_PPm", "COARSE DUP") if r["trigger"] != "low-grade"]
    for r in cu:
        X.record(p, r, "exclude", X.REASONS[0])
    keep = cu[0]
    X.record(p, keep, "keep")
    p2, R2, _ = run(project=p)
    rows = {r["key"]: r for r in R2["exclusions"]}
    assert rows[keep["key"]]["decision"] == "keep" and rows[keep["key"]]["source"] == "user"
    assert R2["dup"][("COARSE DUP", "Cu_PPm")]["n"] == R2["dup_all"][("COARSE DUP", "Cu_PPm")]["n"] - 6
    assert not [r for r in X.provisional(R2["exclusions"]) if r["element"] == "Cu_PPm"
                and r["dtype"] == "COARSE DUP"]


def test_actions_per_element_and_class():
    rb = RuleBook()
    rb.el.set("Cu", "outlier_action", "keep")
    p, R, _ = run(rb=rb)
    assert R["dup"][("COARSE DUP", "Cu_PPm")]["n"] == R["dup_all"][("COARSE DUP", "Cu_PPm")]["n"]
    rb = RuleBook()
    rb.el.set("Cu", "outlier_action", "exclude")
    p, R, _ = run(rb=rb)
    r = [x for x in _rows(R, "Cu_PPm", "COARSE DUP") if x["trigger"] != "low-grade"][0]
    assert r["decision"] == "exclude" and r["source"] == "rule" and not r["pending"]


def test_low_grade_per_class_minimum_and_counts():
    rb = RuleBook()
    rb.el.set("Cu", "low_kdl", {"PULP DUP": 1000.0})        # 1000 x 1 ppm
    p, R, _ = run(rb=rb)
    rec = R["dup"][("PULP DUP", "Cu_PPm")]
    assert rec["n_below_kdl"] > 0 and rec["min_kdl"] == 1000.0 and rec["kdl_dl"] == 1.0
    assert R["dup"][("COARSE DUP", "Cu_PPm")]["n_below_kdl"] == 0
    s = R["exclusion_summary"][("PULP DUP", "Cu_PPm")]
    assert s["low"] == rec["n_below_kdl"]


def test_qc_reference_dl_drives_the_low_grade_cut():
    rb = RuleBook()
    rb.el.set("Cu", "qc_dl", 100.0)
    rb.el.set("Cu", "qc_dl_unit", "ppm")
    p, R, _ = run(rb=rb)
    assert R["dup"][("PULP DUP", "Cu_PPm")]["kdl_dl"] == 100.0
    assert all(r["mean"] >= 1000 for r in R["dup"][("PULP DUP", "Cu_PPm")]["rows"])


def test_mispair_finding_and_provisional_note():
    p, R, d = run()
    f = [x for x in d.findings if x.code == "DATA_MISPAIR"]
    assert f and f[0].root == "DATA" and f[0].stage == "DATA"
    dp = [x for x in d.findings if x.code == "DUP_PRECISION" and x.element == "Cu_PPm"]
    assert all("تأیید" in x.evidence_fa for x in dp)


def test_session_keeps_decisions_and_profiles(tmp_path):
    from geoqaqc import session
    p, R, _ = run()
    r = [x for x in _rows(R, "Cu_PPm", "COARSE DUP") if x["trigger"] != "low-grade"][0]
    X.record(p, r, "exclude", X.REASONS[2])
    rb = RuleBook()
    rb.el.set("Au", "outlier_hard", {"PULP DUP": 40.0})
    rb.el.set_method("Au_ppb", "FA")
    st = session.state(p, FormulaBook(DEFAULT_FORMULAS),
                       {k: dict(v) for k, v in DEFAULT_CRITERIA.items()},
                       dict(DEFAULT_SETTINGS), rb)
    assert st["pair_decisions"][r["key"]]["reason"] == X.REASONS[2]
    rb2 = RuleBook(st["rules"])
    assert rb2.el.profile("Au_ppb")["outlier_hard"]["PULP DUP"] == 40.0
    assert rb2.el.method("Au_ppb") == "FA"


def test_exports_decisions_csv(tmp_path):
    from geoqaqc.export_csv import export_results
    p, R, d = run()
    files = export_results(p, FormulaBook(DEFAULT_FORMULAS),
                           {k: dict(v) for k, v in DEFAULT_CRITERIA.items()},
                           dict(DEFAULT_SETTINGS), RuleBook(), d, str(tmp_path), "b",
                           log=lambda m: None)
    names = {f.split("/")[-1] for f in files}
    assert "b_exclusion_review.csv" in names and "b_mispair_candidates.csv" in names


def test_report_section_documents_exclusions(tmp_path):
    from geoqaqc.report.builder import build_report
    from geoqaqc.report.document import ReportMeta
    from geoqaqc.report.html_writer import write_html
    p, R, d = run()
    doc = build_report(p, R, d, ReportMeta(project="t"), FormulaBook(DEFAULT_FORMULAS),
                       {k: dict(v) for k, v in DEFAULT_CRITERIA.items()},
                       dict(DEFAULT_SETTINGS), RuleBook(), log=lambda m: None)
    h = open(write_html(doc, str(tmp_path / "r.html")), encoding="utf-8").read()
    assert "داده‌های کنارگذاشته از محاسبات دقت" in h
    assert "حکم موقت" in h and "JORC" in h
    assert "همهٔ جفت‌ها / پس از بازبینی" in h
    assert ">C1<" in h or "C1" in h
    assert "خطای داخلی" not in h                     # no section failed to build
