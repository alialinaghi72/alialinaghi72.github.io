from conftest import make_project
from geoqaqc.analysis import run_analysis
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS, FormulaBook,
                              RuleBook)

ELS4 = ("Cu_pct", "Au_ppm", "Ag_ppm", "Mo_ppm")


def _rows(elements, bad_factor=4.0):
    """12 parent/field-duplicate pairs agreeing within ~3 %, one pair (P12)
    whose duplicate reads bad_factor x the parent in every element, plus
    samples at the detection limit."""
    rows = []
    for i in range(13):
        base = {e: 0.5 + 0.1 * i for e in elements}
        rows.append({"SAMPLE_ID": f"P{i}", "SAMPLE_TYPE": "SAMPLE",
                     **{e: f"{v:.4f}" for e, v in base.items()}})
        f = bad_factor if i == 12 else (1.03 if i % 2 else 0.97)
        rows.append({"SAMPLE_ID": f"P{i}-FD", "SAMPLE_TYPE": "FIELD DUP",
                     "PARENT_ID": f"P{i}",
                     **{e: f"{v * f:.4f}" for e, v in base.items()}})
    rows += [{"SAMPLE_ID": f"L{i}", "SAMPLE_TYPE": "SAMPLE",
              **{e: "<0.01" for e in elements}} for i in range(3)]
    return rows


def _run(rows, elements):
    p, S = make_project(rows, None, elements)
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS),
                     {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}, S,
                     RuleBook(), log=lambda m: None)
    return p, R


def test_C16_mispair_multi():
    p, R = _run(_rows(ELS4), ELS4)
    assert ("P12", "P12-FD") in p.excluded_pairs
    acts = [a for a in p.clean_log.actions if a.rule == "C16"]
    assert [(a.sample, a.action) for a in acts] == [("P12-FD", "excluded")]
    assert R["dup"][("FIELD DUP", "Cu_pct")]["n"] == 12


def test_C16_single_element_flag_only():
    p, R = _run(_rows(("Cu_pct",)), ("Cu_pct",))
    assert p.excluded_pairs == set()
    acts = [a for a in p.clean_log.actions if a.rule == "C16"]
    assert [(a.sample, a.action) for a in acts] == [("P12-FD", "flagged")]
    assert R["dup"][("FIELD DUP", "Cu_pct")]["n"] == 13


def test_C16_scattered_pair_is_not_a_mispair():
    # a pair 1.5x apart (HARD 20 %) is poor precision, never a data error
    p, R = _run(_rows(ELS4, bad_factor=1.5), ELS4)
    assert p.excluded_pairs == set()
    assert not [a for a in p.clean_log.actions if a.rule == "C16"]


def test_C17_orphans_logged():
    rows = _rows(("Cu_pct",))
    rows.append({"SAMPLE_ID": "LOST-FD", "SAMPLE_TYPE": "FIELD DUP",
                 "PARENT_ID": "NOPE", "Cu_pct": "0.5"})
    p, _ = _run(rows, ("Cu_pct",))
    acts = [a for a in p.clean_log.actions if a.rule == "C17"]
    assert [a.sample for a in acts] == ["LOST-FD"]
