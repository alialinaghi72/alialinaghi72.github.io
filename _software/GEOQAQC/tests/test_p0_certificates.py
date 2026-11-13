"""P0 R1-R4: method-aware certificates, uncertified CRMs, over-limit values and
spreadsheet errors."""

import pytest

from conftest import make_project
from geoqaqc.analysis import run_analysis
from geoqaqc.cleaning import CertificateConflict, clean_values, parse_value
from geoqaqc.diagnosis import diagnose
from geoqaqc.elements import parse_cert_element
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS, FormulaBook,
                              RuleBook)

ELS = ("Cu_PPm", "Au_ppb")
# the structure of the project's certificate file: alternative-method rows
# (Au_AR, CuSol) sit beside the primary ones
CERTS = [("G913-4", "Au", 1.37, 0.04, "ppm"),
         ("G913-4", "Au_AR", 1.35, 0.08, "ppm"),
         ("GBM922-12", "Cu", 1.3975, 0.0556, "%"),
         ("GBM922-12", "CuSol", 1.12, 0.05, "%"),
         ("OREAS906", "Cu", 0.310, 0.008, "%"),
         ("OREAS906", "CuSol", 0.259, 0.009, "%"),
         ("OREAS906", "Mo", 4.05, 0.3, "ppm")]


def run(rows, certs=CERTS, els=ELS, rb=None):
    p, S = make_project(rows, certs, els)
    rb = rb or RuleBook()
    clean_values(p, S, rb, log=lambda m: None)
    return p


def analyse(rows, certs=CERTS, els=ELS, rb=None):
    p, S = make_project(rows, certs, els)
    rb = rb or RuleBook()
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS), C, S, rb, log=lambda m: None)
    return p, R, diagnose(p, R, C, S, rb)


def _crm(code, n, **vals):
    return [dict({"SAMPLE_ID": f"{code}-{i}", "SAMPLE_TYPE": "CRM", "CRM_ID": code},
                 **{k: v[i] if isinstance(v, list) else v for k, v in vals.items()})
            for i in range(n)]


# ---- R1 ---------------------------------------------------------------------
def test_parse_cert_element():
    assert parse_cert_element("Au") == ("Au", "FA")
    assert parse_cert_element("Au_AR") == ("Au", "AR")
    assert parse_cert_element("CuSol") == ("Cu", "SOL")
    assert parse_cert_element("Cu_Sol") == ("Cu", "SOL")
    assert parse_cert_element("Cu") == ("Cu", "TOTAL")
    assert parse_cert_element("Au", "Aqua regia") == ("Au", "AR")


def test_fire_assay_row_chosen_over_aqua_regia():
    p = run(_crm("G913-4", 3, Au_ppb="1370"))
    c = p.certs[("G9134", "Au_ppb")]
    assert c["cert"] == pytest.approx(1370) and c["sd"] == pytest.approx(40)
    assert c["method"] == "FA" and c["cert_element"] == "Au"


def test_total_copper_never_takes_the_soluble_row():
    p = run(_crm("OREAS906", 3, Cu_PPm="3100"))
    assert p.certs[("OREAS906", "Cu_PPm")]["cert"] == pytest.approx(3100)  # 0.310 %
    p = run(_crm("GBM922-12", 3, Cu_PPm="13975"))
    assert p.certs[("GBM92212", "Cu_PPm")]["cert"] == pytest.approx(13975)


def test_column_method_set_to_aqua_regia_takes_the_ar_row():
    rb = RuleBook()
    rb.el.set_method("Au_ppb", "AR")
    p = run(_crm("G913-4", 3, Au_ppb="1350"), rb=rb)
    assert p.certs[("G9134", "Au_ppb")]["cert"] == pytest.approx(1350)


def test_two_rows_of_one_method_stop_with_a_clear_message():
    certs = [("G913-4", "Au", 1.37, 0.04, "ppm"), ("G913-4", "Au", 1.36, 0.05, "ppm")]
    with pytest.raises(CertificateConflict) as ex:
        run(_crm("G913-4", 3, Au_ppb="1370"), certs)
    msg = str(ex.value)
    assert "G913-4" in msg and "Au_ppb" in msg and "row 2" in msg and "row 3" in msg


def test_method_column_wins_over_the_name():
    certs = [("G913-4", "Au", 1.35, 0.08, "ppm", "AR"),
             ("G913-4", "Au", 1.37, 0.04, "ppm", "Fire assay")]
    p = run(_crm("G913-4", 3, Au_ppb="1370"), certs)
    assert p.certs[("G9134", "Au_ppb")]["cert"] == pytest.approx(1370)


def test_certificate_rows_used_are_reported():
    from geoqaqc.report.builder import certificate_rows
    p, R, _ = analyse(_crm("G913-4", 6, Au_ppb="1370", Cu_PPm="50"))
    rows = certificate_rows(p)
    assert ("G913-4", "Au_ppb", "Au", "FA") in [(r["crm"], r["column"], r["element"],
                                                 r["method"]) for r in rows]


# ---- R2 ---------------------------------------------------------------------
def test_crm_without_certified_value_is_not_evaluated():
    rows = _crm("G913-4", 6, Au_ppb="1370", Cu_PPm=["40", "60", "35", "90", "20", "70"])
    p, R, d = analyse(rows)
    rec = R["crm"][("G913-4", "Cu_PPm")]
    assert rec["status"] == "NOT_CERTIFIED" and rec["ratings"] == {}
    assert rec["rating"] == "NO DATA"
    assert not [f for f in d.findings if f.subject == "G913-4" and f.element == "Cu_PPm"]


# ---- R3 ---------------------------------------------------------------------
def test_over_limit_with_units_is_parsed_and_converted():
    rb = RuleBook()
    assert parse_value(">5%", rb, unit="ppm") == (50000.0, ">", None)
    assert parse_value("> 5 %", rb, unit="ppm") == (50000.0, ">", None)
    assert parse_value(">10000 ppm", rb, unit="ppm") == (10000.0, ">", None)
    assert parse_value(">10", rb, unit="ppm") == (10.0, ">", None)


def test_over_limit_samples_listed_for_ore_grade_reassay():
    rows = [{"SAMPLE_ID": f"S{i}", "Cu_PPm": f"{100 + 50 * i}", "Au_ppb": "20"}
            for i in range(30)]
    rows[4]["Cu_PPm"] = ">5%"
    rows[9]["Cu_PPm"] = "> 5 %"
    p, R, d = analyse(rows)
    s4 = [s for s in p.samples if s.sid == "S4"][0]
    assert s4.vals["Cu_PPm"] == pytest.approx(50000) and s4.flags["Cu_PPm"] == ">"
    f = [x for x in d.findings if x.code == "OVER_LIMIT" and x.element == "Cu_PPm"]
    assert f and f[0].severity == "MATERIAL"
    assert "S4" in f[0].evidence_fa and "S9" in f[0].evidence_fa
    assert not [a for a in p.clean_log.actions if a.rule == "C04"]


# ---- R4 ---------------------------------------------------------------------
def test_spreadsheet_errors_are_c19_not_lab_codes():
    rows = [{"SAMPLE_ID": f"S{i}", "Cu_PPm": "200", "Au_ppb": "#N/A" if i < 5 else "30"}
            for i in range(20)]
    rows[6]["Au_ppb"] = "#VALUE!"
    p, R, d = analyse(rows)
    rules = [a.rule for a in p.clean_log.actions if a.element == "Au_ppb"]
    assert rules.count("C19") == 6 and "C04" not in rules
    f = [x for x in d.findings if x.code == "DATA_SPREADSHEET"]
    assert f and f[0].stage == "DATA" and f[0].severity == "MATERIAL"
