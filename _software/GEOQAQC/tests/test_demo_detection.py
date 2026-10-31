"""Every defect planted in the demonstration dataset must be found, and the
control element (Mo) must come out clean."""

import os

import pytest

from conftest import DATA
from geoqaqc.analysis import run_analysis
from geoqaqc.core import R_EXC, R_GOOD, R_NA, R_VG
from geoqaqc.loader import load_project
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, FormulaBook, RuleBook)


def demo():
    p = load_project(os.path.join(DATA, "demo_assay.csv"),
                     os.path.join(DATA, "demo_crm_certificates.csv"),
                     os.path.join(DATA, "demo_umpire.csv"))
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS),
                     {k: dict(v) for k, v in DEFAULT_CRITERIA.items()},
                     dict(DEFAULT_SETTINGS), RuleBook(), log=lambda m: None)
    return p, R


@pytest.fixture(scope="module")
def pr():
    return demo()


def test_mapping_guessed(pr):
    p, _ = pr
    assert p.elements == ["Cu_pct", "Au_ppm", "Ag_ppm", "Mo_ppm"]
    assert p.assay.mapping["order"] == "SEQ"


def test_cleaning_counts(pr):
    p, _ = pr
    c = p.clean_log.counts()
    assert c["C03"] == 2
    assert c["C04"] == 5
    assert c["C05"] == 2
    assert c["C06"] == 5
    for rule in ("C09", "C12", "C13", "C14", "C15", "C16", "C17"):
        assert c[rule] == 1, rule


def test_swap_identified(pr):
    p, _ = pr
    swapped = [s for s in p.samples if s.excl_all.startswith("C13")]
    assert len(swapped) == 1 and swapped[0].swap_to == "DEMO501"


def test_au_certificate_converted_from_ppb(pr):
    p, _ = pr
    assert p.certs[("DEMO501", "Au_ppm")]["cert"] == pytest.approx(0.312)


def test_cu_drift(pr):
    _, R = pr
    assert R["drift"]["Cu_pct"]["sig"] is True
    assert R["drift"]["Cu_pct"]["total"] < -3


def test_no_false_drift(pr):
    _, R = pr
    for el in ("Au_ppm", "Ag_ppm", "Mo_ppm"):
        assert R["drift"][el]["sig"] is False, el


def test_coarse_blank_carry_over(pr):
    _, R = pr
    cb = R["blank"][("COARSE BLANK", "Cu_pct")]
    assert cb["fail_pct"] >= 10
    assert cb["fail_after_high_pct"] > cb["fail_other_pct"]
    assert R["blank"][("PULP BLANK", "Cu_pct")]["fail_pct"] == 0


def test_au_nugget_budget(pr):
    _, R = pr
    assert R["budget"]["Au_ppm"]["dominant"] == "sampling"
    assert R["dup"][("FIELD DUP", "Au_ppm")]["hard_p90"] > 40


def test_ag_proportional_bias(pr):
    _, R = pr
    assert R["accuracy"]["Ag_ppm"]["prop_bias_pct"] == pytest.approx(11, abs=2)


def test_umpire(pr):
    _, R = pr
    assert R["umpire"]["Cu_pct"]["wbias"] == pytest.approx(-6, abs=1.5)
    assert R["umpire"]["Au_ppm"]["ttest"]["p"] > 0.05


def test_coarse_dup_insertion_low(pr):
    _, R = pr
    row = [r for r in R["insertion"]["rows"] if r["type"] == "COARSE DUP"][0]
    assert 2.0 <= row["pct"] < 3.0


def test_mo_clean(pr):
    _, R = pr
    ok = {R_EXC, R_VG, R_GOOD, R_NA}
    for section in ("crm", "blank", "dup"):
        for key, rec in R[section].items():
            if key[1] == "Mo_ppm":
                assert rec["rating"] in ok, (section, key, rec["rating"])


@pytest.mark.parametrize("seed", [1, 7])
def test_clean_elements_hold_across_seeds(seed, tmp_path):
    # the clean-element assertions must not depend on the demo's chosen seed
    import sys
    sys.path.insert(0, DATA)
    from make_demo import make_demo
    from geoqaqc.diagnosis import diagnose
    make_demo(str(tmp_path), seed=seed)
    p = load_project(*(str(tmp_path / f) for f in (
        "demo_assay.csv", "demo_crm_certificates.csv", "demo_umpire.csv")))
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S, rb = dict(DEFAULT_SETTINGS), RuleBook()
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S, rb, log=lambda m: None)
    assert R["drift"]["Cu_pct"]["sig"] is True
    for el in ("Au_ppm", "Ag_ppm", "Mo_ppm"):
        assert R["drift"][el]["sig"] is False, el
    assert diagnose(p, R, C, S, rb).verdict("Mo_ppm")[0] == "SUITABLE"
