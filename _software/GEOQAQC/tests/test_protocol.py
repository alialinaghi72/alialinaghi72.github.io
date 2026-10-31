import pytest

from geoqaqc.core import R_BAD, R_EXC, R_GOOD, R_NA, R_VBAD
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, RULES, FormulaBook, RuleBook,
                              rate)


def test_rulebook_validation():
    rb = RuleBook()
    with pytest.raises(ValueError):
        rb.set("swap_frac", 2.0)
    with pytest.raises(ValueError):
        rb.set("sev_POOR", "TERRIBLE")
    with pytest.raises(KeyError):
        rb.get("no_such_rule")


def test_rulebook_changed_and_roundtrip():
    rb = RuleBook()
    assert rb.changed() == []
    rb.set("drift_p", 0.01)
    assert rb.changed() == ["drift_p"]
    assert rb["drift_p"] == 0.01
    rb2 = RuleBook()
    rb2.from_state(rb.to_state())
    assert rb2["drift_p"] == 0.01
    rb2.from_state({"unknown_key": 1})       # ignored
    rb2.reset()
    assert rb2.changed() == []


def test_rulebook_lists_and_bools():
    rb = RuleBook()
    rb.set("lab_codes", "IS, NSS ,LNR")
    assert rb["lab_codes"] == ["IS", "NSS", "LNR"]
    rb.set("sentinels", "-999, 9999")
    assert rb["sentinels"] == [-999.0, 9999.0]
    rb.set("clean_C13", "false")
    assert rb["clean_C13"] is False


def test_rules_complete():
    for i in range(1, 19):
        assert RULES[f"clean_C{i:02d}"]["default"] is True
    assert RULES["dup_id_policy"]["default"] == "keep first"
    assert RULES["swap_frac"]["default"] == 0.667
    assert RULES["sev_VERY BAD"]["default"] == "CRITICAL"
    assert RULES["verdict_stages"]["default"] == ["ACCURACY", "CONTAMINATION",
                                                  "INTERLAB"]
    groups = [g for g, _ in RuleBook().groups()]
    assert groups[0] == "CLEANING"
    assert "SEVERITY" in groups


def test_new_formula_and_criterion():
    F = FormulaBook(DEFAULT_FORMULAS)
    assert F.calc("dup_cv2", a=1.0, b=3.0) == pytest.approx(4 / (2 * 4))
    assert DEFAULT_CRITERIA["maxmin_fail"]["cuts"] == [5, 10, 15, 20, 30]
    assert DEFAULT_SETTINGS["carry_kdl"] == 10.0


def test_rate_unchanged():
    low = DEFAULT_CRITERIA["crm_bias"]
    assert rate(1.0, low) == R_EXC
    assert rate(5.0, low) == R_GOOD
    assert rate(9.0, low) == R_BAD
    assert rate(50.0, low) == R_VBAD
    assert rate(None, low) == R_NA
    high = DEFAULT_CRITERIA["insert_rate"]
    assert rate(6.0, high) == R_EXC
    assert rate(0.5, high) == R_VBAD
