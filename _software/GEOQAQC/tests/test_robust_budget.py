"""Robust error budget: beside the mean-of-squares budget, one from the HARD
percentile; a warning when a few outlier pairs make the two disagree."""

import random

from geoqaqc.analysis import analyse_error_budget
from geoqaqc.protocol import DEFAULT_SETTINGS, RuleBook


def _rec(dt, cvs):
    hards = sorted(100.0 * c / 2 ** 0.5 for c in cvs)          # HARD % of each pair
    k = int(round(0.9 * (len(hards) - 1)))
    return {"type": dt, "n": len(cvs), "cv2_mean": sum(c * c for c in cvs) / len(cvs),
            "hard_p90": hards[k], "hard_pct_used": 90.0}


def _dup(pulp_extra=()):
    rnd = random.Random(7)
    def cvs(sd, n=200):
        # pair CV of two results with relative sd: |a-b|/mean/sqrt(2)... drawn directly
        return [abs(rnd.gauss(0, sd)) for _ in range(n)]
    return {("FIELD DUP", "Cu"): _rec("FIELD DUP", cvs(0.20)),
            ("COARSE DUP", "Cu"): _rec("COARSE DUP", cvs(0.15)),
            ("PULP DUP", "Cu"): _rec("PULP DUP", cvs(0.03) + list(pulp_extra))}


def test_clean_data_two_budgets_agree():
    b = analyse_error_budget(_dup(), dict(DEFAULT_SETTINGS), RuleBook())["Cu"]
    assert b["estimable"] and b["robust"]["estimable"]
    assert not b["disagree"] and b["preferred"] == "classical"
    assert b["dominant"] == b["robust"]["dominant"]
    assert b["max_diff"] < 25


def test_outlier_pairs_trigger_the_warning():
    # six wild pulp pairs (mix-ups) out of 206 carry the classical budget to
    # the analytical stage; the percentile hardly moves
    b = analyse_error_budget(_dup(pulp_extra=[1.2] * 6), dict(DEFAULT_SETTINGS), RuleBook())["Cu"]
    r = b["robust"]
    assert r["estimable"] and r["dominant"] != "analytical"
    assert b["disagree"] and b["preferred"] == "robust"
    if b["estimable"]:
        assert b["pct"]["analytical"] > r["pct"]["analytical"] + 25


def test_demo_report_shows_both(tmp_path):
    from geoqaqc.diagnosis import diagnose
    from geoqaqc.protocol import DEFAULT_CRITERIA, DEFAULT_FORMULAS, FormulaBook
    from geoqaqc.report.builder import build_report
    from geoqaqc.report.document import ReportMeta
    from geoqaqc.report.html_writer import write_html
    from geoqaqc.report import texts_fa as T
    from test_demo_detection import demo
    p, R = demo()
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S, rb = dict(DEFAULT_SETTINGS), RuleBook()
    d = diagnose(p, R, C, S, rb)
    errs = []
    doc = build_report(p, R, d, ReportMeta(project="D"), FormulaBook(DEFAULT_FORMULAS), C, S, rb,
                       log=errs.append)
    h = open(write_html(doc, str(tmp_path / "r.html")), encoding="utf-8").read()
    assert not [e for e in errs if "failed" in e]
    assert T.BUDGET_TWO_WAYS[:25] in h
    for el, b in R["budget"].items():
        assert "robust" in b and "disagree" in b
