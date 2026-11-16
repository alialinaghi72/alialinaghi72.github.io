"""International good-practice defaults by element type, and the buttons
that set them on the Protocol pages."""

import os

import pytest

from geoqaqc.core import T_CDUP, T_FDUP, T_PDUP
from geoqaqc.elements import criteria_for
from geoqaqc.presets import (ELEMENT_TYPES, apply_element_defaults, element_type,
                             element_type_defaults)
from geoqaqc.protocol import DEFAULT_CRITERIA, RuleBook


def test_types():
    assert element_type("Au_ppb") == "precious" and element_type("Cu_PPm") == "base"
    assert element_type("Fe_pct") == "bulk" and element_type("Mo_ppm") == "minor"
    assert element_type("Zz") == "base"
    for d in ELEMENT_TYPES.values():                 # field >= coarse >= pulp
        h = d["hard90"]
        assert h[T_FDUP] >= h[T_CDUP] >= h[T_PDUP]


def test_defaults_follow_the_element():
    rb = RuleBook()
    rb.el.set("Cu_PPm", "qc_dl", 5.0)
    rb.el.set("Cu_PPm", "cutoff", 2000.0)
    apply_element_defaults(rb, ["Au_ppb", "Cu_PPm", "Fe_pct"])
    au = criteria_for(DEFAULT_CRITERIA, rb, "Au_ppb")
    cu = criteria_for(DEFAULT_CRITERIA, rb, "Cu_PPm")
    fe = criteria_for(DEFAULT_CRITERIA, rb, "Fe_pct")
    assert au["pdup_hard90"]["cuts"][2] == 10 and cu["pdup_hard90"]["cuts"][2] == 5
    assert fe["fdup_hard90"]["cuts"][2] == 5
    for c in (au, cu, fe):
        for k in ("fdup_hard90", "cdup_hard90", "pdup_hard90", "crm_bias"):
            assert c[k]["cuts"] == sorted(c[k]["cuts"])
    assert rb.el.profile("Au")["outlier_preselect"] == "keep"
    assert rb.el.profile("Cu")["cv_avg_limit"][T_PDUP] == 5
    # what belongs to the laboratory and the deposit is kept
    assert rb.el.profile("Cu")["qc_dl"] == 5.0 and rb.el.profile("Cu")["cutoff"] == 2000.0
    # criteria only: the profile is not touched
    rb2 = RuleBook()
    apply_element_defaults(rb2, ["Au_ppb"], what="criteria")
    assert rb2.el.profile("Au")["blank_fail"] is None
    assert rb2.el.profile("Au")["criteria"]["pdup_hard90"][2] == 10
    assert element_type_defaults("Au")[0]["blank_fail"] == 10


@pytest.mark.skipif(not os.environ.get("DISPLAY") and os.name != "nt", reason="no display")
def test_buttons_on_the_protocol_pages():
    pytest.importorskip("tkinter")
    from conftest import DATA
    from geoqaqc.protocol import DEFAULT_SETTINGS
    from geoqaqc.ui.app import App
    a = App()
    a.withdraw()
    try:
        a.load_files(os.path.join(DATA, "demo_assay.csv"),
                     os.path.join(DATA, "demo_crm_certificates.csv"))
        a.update()
        done = a.intl_elements("Au_ppm")
        assert list(done) == ["Au_ppm"]
        assert a.RB.el.profile("Au")["criteria"]["cdup_hard90"][2] == 20
        assert "criteria" not in a.RB.el.overrides.get("Cu", {})
        a.intl_el.set(a._ALL_COLUMNS)
        assert len(a.intl_elements()) == len(a.project.assay.value_cols)
        a.crit_scope.set("Cu")
        a.RB.el.overrides["Cu"].pop("criteria")
        a.intl_criteria()
        assert a.RB.el.profile("Cu")["criteria"]["pdup_hard90"][2] == 5
        a._svars["min_pairs"].set("3")
        a.apply_settings()
        a.reset_settings()
        assert a.S["min_pairs"] == DEFAULT_SETTINGS["min_pairs"]
        assert a._svars["min_pairs"].get() == str(DEFAULT_SETTINGS["min_pairs"])
    finally:
        a.destroy()
