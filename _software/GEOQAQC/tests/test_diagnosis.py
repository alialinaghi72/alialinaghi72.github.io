import inspect

import pytest

from geoqaqc.core import R_BAD, R_EXC, R_GOOD, R_POOR, R_VBAD
from geoqaqc.diagnosis import (SEVERITIES, STAGES, diagnose,
                               severity_from_rating)
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_SETTINGS, RuleBook)
from geoqaqc.report import texts_fa
from test_demo_detection import demo


@pytest.fixture(scope="module")
def dx():
    p, R = demo()
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    return p, R, diagnose(p, R, C, dict(DEFAULT_SETTINGS), RuleBook())


def codes(d, el):
    return {(f.code, f.stage) for f in d.by_element(el)}


def test_demo_verdicts(dx):
    _, _, d = dx
    assert d.verdict("Cu_pct")[0] == "RESTRICTED"
    assert d.verdict("Au_ppm")[0] == "RESTRICTED"
    assert d.verdict("Ag_ppm")[0] == "REMEDIATE"
    assert d.verdict("Mo_ppm")[0] == "SUITABLE"


def test_demo_stage_attribution(dx):
    _, _, d = dx
    cu = codes(d, "Cu_pct")
    assert ("CRM_DRIFT", "ACCURACY") in cu
    assert ("BLK_CARRY", "CONTAMINATION") in cu
    assert ("BLK_PREP", "PREPARATION") in cu
    assert ("UMP_BIAS", "INTERLAB") in cu
    assert ("BUDGET_DOMINANT", "SAMPLING") in codes(d, "Au_ppm")
    ag = [f for f in d.by_element("Ag_ppm") if f.code == "CRM_SYSTEMATIC"]
    assert ag and "تناسبی" in ag[0].evidence_fa
    proj = {(f.code, f.subject) for f in d.findings if not f.element}
    assert ("DATA_SWAP", "") in {(c, "") for c, _ in proj}
    assert any(c == "INS_RATE" and s == "COARSE DUP" for c, s in proj)


def test_umpire_cross_check_names_the_primary_lab_for_ag(dx):
    _, _, d = dx
    f = [x for x in d.by_element("Ag_ppm") if x.code == "UMP_BIAS"][0]
    assert "آزمایشگاه اصلی" in f.cause_fa


def test_matrix_and_actions(dx):
    p, _, d = dx
    m = d.matrix()
    assert list(m) == p.elements
    assert all(set(row) == set(STAGES) for row in m.values())
    assert m["Ag_ppm"]["ACCURACY"] == "CRITICAL"
    acts = d.actions()
    order = [SEVERITIES.index(a.severity) for a in acts]
    assert order == sorted(order)


def test_severity_mapping_editable():
    rb = RuleBook()
    assert severity_from_rating(R_BAD, rb) == "MATERIAL"
    rb.set("sev_BAD", "CRITICAL")
    assert severity_from_rating(R_BAD, rb) == "CRITICAL"
    rb.set("sev_POOR", "NONE")
    assert severity_from_rating(R_POOR, rb) is None
    assert severity_from_rating(R_VBAD, rb) == "CRITICAL"


def test_no_finding_on_good():
    rb = RuleBook()
    assert severity_from_rating(R_GOOD, rb) is None
    assert severity_from_rating(R_EXC, rb) is None


def test_every_finding_is_complete(dx):
    _, _, d = dx
    for f in d.findings:
        assert f.stage in STAGES and f.severity in SEVERITIES
        assert f.title_fa and f.evidence_fa and f.cause_fa and f.actions_fa
        assert f.title_en
        for txt in [f.title_fa, f.evidence_fa, f.cause_fa] + f.actions_fa:
            assert "{" not in txt and "}" not in txt, (f.code, txt)
            assert "None" not in txt, (f.code, txt)


def test_texts_have_no_placeholders():
    fns = [getattr(texts_fa, n) for n in dir(texts_fa) if n.startswith("f_")]
    assert len(fns) >= 20
    for fn in fns:
        kw = {}
        for name, par in inspect.signature(fn).parameters.items():
            kw[name] = par.default if par.default is not inspect._empty else 1.5
        out = fn(**kw)
        assert len(out) == 4
        for txt in out[:3] + tuple(out[3]):
            assert txt and "{" not in txt and "}" not in txt, (fn.__name__, txt)


def test_crms_without_any_certificate_restrict_the_verdict():
    # CRMs inserted but no certificate for the element: accuracy is unknown,
    # which is never "suitable" (no CRMs at all already gives RESTRICTED)
    from conftest import make_project
    from geoqaqc.analysis import run_analysis
    from geoqaqc.protocol import DEFAULT_FORMULAS, FormulaBook
    import random
    rng = random.Random(3)
    rows = []
    for i in range(400):
        v = rng.lognormvariate(-1.2, 0.6)
        rows.append({"SAMPLE_ID": f"S{i}", "Cu_pct": f"{v:.4f}"})
        if i % 20 == 0:                  # the laboratory reads 15 % high
            rows.append({"SAMPLE_ID": f"C{i}", "SAMPLE_TYPE": "CRM", "CRM_ID": "CRM-A",
                         "Cu_pct": f"{0.5 * 1.15 * (1 + rng.gauss(0, 0.02)):.4f}"})
        if i % 20 == 10:
            rows.append({"SAMPLE_ID": f"BL{i}", "SAMPLE_TYPE": "BLANK", "Cu_pct": "<0.001"})
        if i % 20 == 5:
            for t, cv in (("FIELD DUP", 0.08), ("COARSE DUP", 0.04), ("PULP DUP", 0.02)):
                rows.append({"SAMPLE_ID": f"{t[0]}D{i}", "SAMPLE_TYPE": t,
                             "PARENT_ID": f"S{i}",
                             "Cu_pct": f"{v * (1 + rng.gauss(0, cv)):.4f}"})
    p, S = make_project(rows, None, ("Cu_pct",))
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    rb = RuleBook()
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S, rb, log=lambda m: None)
    d = diagnose(p, R, C, S, rb)
    f = [x for x in d.by_element("Cu_pct") if x.code == "CRM_NOCERT"]
    assert f and f[0].severity == "MATERIAL"
    assert d.verdict("Cu_pct")[0] != "SUITABLE"
