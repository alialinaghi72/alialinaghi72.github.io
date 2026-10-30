import pytest

from conftest import CERTS, crm_rows, make_project
from geoqaqc.cleaning import clean_values, norm_code, parse_value
from geoqaqc.core import fnum
from geoqaqc.protocol import RULES, RuleBook


def run(rows, certs=CERTS, elements=("Cu_pct", "Au_ppm"), rb=None):
    p, S = make_project(rows, certs, elements)
    rb = rb or RuleBook()
    log = clean_values(p, S, rb, log=lambda m: None)
    return p, log


def by_id(p, sid):
    return [s for s in p.samples if s.sid == sid]


def rules_of(log, sample=None):
    return [a.rule for a in log.actions if sample is None or a.sample == sample]


# ---- C04-C07: value parsing -------------------------------------------------
def test_C04_lab_code():
    p, log = run([{"SAMPLE_ID": "S1", "Cu_pct": "IS", "Au_ppm": "0.1"}])
    assert p.samples[0].vals["Cu_pct"] is None
    assert rules_of(log, "S1") == ["C04"]


def test_C05_sentinel():
    p, log = run([{"SAMPLE_ID": "S1", "Cu_pct": "-999", "Au_ppm": "0.1"}])
    assert p.samples[0].vals["Cu_pct"] is None
    assert "C05" in rules_of(log, "S1")


def test_C06_negative_is_below_dl():
    p, _ = run([{"SAMPLE_ID": "S1", "Cu_pct": "-0.01", "Au_ppm": "0.1"}])
    s = p.samples[0]
    assert (s.vals["Cu_pct"], s.flags["Cu_pct"]) == (pytest.approx(0.01), "<")


def test_C07_zero_is_below_dl():
    p, _ = run([{"SAMPLE_ID": "S1", "Cu_pct": "0", "Au_ppm": "0.1"}])
    assert p.samples[0].flags["Cu_pct"] == "<"


def test_parse_value_direct():
    rb = RuleBook()
    assert parse_value("LNR", rb) == (None, "", "C04")
    assert parse_value("0.25", rb) == (0.25, "", None)
    assert parse_value("<0.01", rb) == (0.01, "<", None)


def test_C08_over_range_on_crm():
    rows = crm_rows("OREAS-501b", 0.283, 0.312)
    rows[2]["Cu_pct"] = ">10000"
    p, log = run(rows)
    s = by_id(p, "OREAS-501b-2")[0]
    assert s.excl["Cu_pct"].startswith("C08")
    assert "Au_ppm" not in s.excl


# ---- C02, C03: rows and IDs --------------------------------------------------
def test_C02_exact_duplicate_row():
    row = {"SAMPLE_ID": "S1", "Cu_pct": "0.2", "Au_ppm": "0.1", "SEQ": 1}
    p, log = run([row, dict(row)])
    assert [s.dropped for s in p.samples] == [False, True]
    assert rules_of(log) == ["C02"]


def test_C03_reassay_keep_first():
    p, log = run([{"SAMPLE_ID": "S1", "Cu_pct": "0.2", "Au_ppm": "0.1"},
                  {"SAMPLE_ID": "S1", "Cu_pct": "0.3", "Au_ppm": "0.1"}])
    assert [s.dropped for s in p.samples] == [False, True]
    assert rules_of(log) == ["C03"]


def test_C03_exclude_all():
    rb = RuleBook()
    rb.set("dup_id_policy", "exclude all")
    p, _ = run([{"SAMPLE_ID": "S1", "Cu_pct": "0.2", "Au_ppm": "0.1"},
                {"SAMPLE_ID": "S1", "Cu_pct": "0.3", "Au_ppm": "0.1"}], rb=rb)
    assert [s.dropped for s in p.samples] == [True, True]


# ---- C09-C12: certificates and units ----------------------------------------
def test_norm_code():
    assert norm_code(" OREAS 501b ") == norm_code("oreas-501B") == "OREAS501B"
    assert norm_code("CDN.ME/1") == "CDNME1"


def test_C09_loose_crm_code():
    rows = crm_rows("oreas-501B", 0.283, 0.312)
    certs = [("OREAS 501b", "Cu_pct", 0.283, 0.009, "%")]
    p, log = run(rows, certs)
    assert ("OREAS501B", "Cu_pct") in p.certs
    assert p.crm_labels["OREAS501B"] == "OREAS 501b"
    assert "C09" in rules_of(log)


def test_C10_unit_conversion():
    rows = crm_rows("OREAS-501b", 0.283, 0.312)
    certs = [("OREAS-501b", "Au", 312, 18, "ppb"),
             ("OREAS-501b", "Cu", 0.283, 0.009, "%")]
    p, log = run(rows, certs)
    c = p.certs[("OREAS501B", "Au_ppm")]
    assert c["cert"] == pytest.approx(0.312)
    assert c["sd"] == pytest.approx(0.018)
    assert p.certs[("OREAS501B", "Cu_pct")]["cert"] == pytest.approx(0.283)
    assert [(a.element, a.action) for a in log.actions if a.rule == "C10"] == [
        ("Au_ppm", "converted"), ("Cu_pct", "corrected")]


def test_C10_off_requires_exact_names():
    rb = RuleBook()
    rb.set("clean_C10", False)
    rows = crm_rows("OREAS-501b", 0.283, 0.312)
    p, _ = run(rows, [("OREAS-501b", "Au", 312, 18, "ppb")], rb=rb)
    assert ("OREAS501B", "Au_ppm") not in p.certs


def test_C11_column_unit_mismatch():
    rows = [{"SAMPLE_ID": f"C{i}", "SAMPLE_TYPE": "CRM", "CRM_ID": "OREAS-501b",
             "Cu": f"{2830 * (1 + (i % 3 - 1) * 0.01):.1f}"} for i in range(6)]
    p, log = run(rows, [("OREAS-501b", "Cu", 0.283, 0.009, "")], elements=("Cu",))
    c = p.certs[("OREAS501B", "Cu")]
    assert c["cert"] == pytest.approx(2830)
    assert c["sd"] == pytest.approx(90)
    assert [a.action for a in log.actions if a.rule == "C11"] == ["converted"]


def test_C12_single_decimal_slip():
    rows = crm_rows("OREAS-501b", 0.283, 0.312)
    rows[3]["Cu_pct"] = f"{0.283 * 1000.2:.3f}"
    p, log = run(rows)
    bad = [s.sid for s in p.samples if "Cu_pct" in s.excl]
    assert bad == ["OREAS-501b-3"]
    assert p.samples[3].excl["Cu_pct"].startswith("C12")
    assert rules_of(log, "OREAS-501b-3") == ["C12"]


# ---- C13-C15: swaps -----------------------------------------------------------
def _three_crms():
    return (crm_rows("OREAS-501b", 0.283, 0.312, start=0)
            + crm_rows("OREAS-504b", 1.052, 0.905, start=10)
            + crm_rows("CDN-ME-1", 0.505, 1.48, start=20))


def test_C13_swap_multi_element():
    rows = _three_crms()
    rows.append({"SAMPLE_ID": "X1", "SAMPLE_TYPE": "CRM", "CRM_ID": "OREAS-504b",
                 "Cu_pct": "0.285", "Au_ppm": "0.309"})
    p, log = run(rows)
    s = by_id(p, "X1")[0]
    assert s.excl_all.startswith("C13")
    assert s.swap_to == "OREAS501B"
    assert rules_of(log, "X1") == ["C13"]


def test_C13_single_element_swap_and_genuine_failure():
    rows = [r for r in _three_crms()]
    for r in rows:
        r.pop("Au_ppm")
    rows.append({"SAMPLE_ID": "SWAP", "SAMPLE_TYPE": "CRM", "CRM_ID": "OREAS-504b",
                 "Cu_pct": "0.290"})
    rows.append({"SAMPLE_ID": "FAIL", "SAMPLE_TYPE": "CRM", "CRM_ID": "OREAS-504b",
                 "Cu_pct": "0.940"})
    certs = [c for c in CERTS if c[1] == "Cu_pct"]
    p, log = run(rows, certs, elements=("Cu_pct",))
    assert by_id(p, "SWAP")[0].excl_all.startswith("C13")
    fail = by_id(p, "FAIL")[0]
    assert fail.excl_all == "" and fail.excl == {}       # genuine failure kept
    assert rules_of(log, "FAIL") == []


def _dl_rows():
    return [{"SAMPLE_ID": f"N{i}", "Cu_pct": "<0.001", "Au_ppm": "<0.002"}
            for i in range(3)]


def test_C14_blank_inserted_as_crm():
    rows = _three_crms() + _dl_rows()
    rows.append({"SAMPLE_ID": "LOW", "SAMPLE_TYPE": "CRM", "CRM_ID": "OREAS-504b",
                 "Cu_pct": "0.0005", "Au_ppm": "0.001"})
    p, log = run(rows)
    assert by_id(p, "LOW")[0].excl_all.startswith("C14")


def test_C15_crm_inserted_as_blank():
    rows = _three_crms() + _dl_rows()
    rows.append({"SAMPLE_ID": "BSWAP", "SAMPLE_TYPE": "BLANK",
                 "Cu_pct": "0.506", "Au_ppm": "1.47"})
    rows.append({"SAMPLE_ID": "BDIRTY", "SAMPLE_TYPE": "BLANK",
                 "Cu_pct": "0.020", "Au_ppm": "0.040"})
    p, log = run(rows)
    assert by_id(p, "BSWAP")[0].excl_all.startswith("C15")
    assert by_id(p, "BDIRTY")[0].excl_all == ""          # contamination is kept


# ---- switches -------------------------------------------------------------------
def test_switch_off_keeps_v11_parse():
    rb = RuleBook()
    for k in RULES:
        if k.startswith("clean_"):
            rb.set(k, False)
    raw = ["IS", "-999", "-0.01", "0", "<0.01", "0.25"]
    rows = [{"SAMPLE_ID": f"S{i}", "Cu_pct": v, "Au_ppm": "0.1"}
            for i, v in enumerate(raw)]
    p, log = run(rows, rb=rb)
    assert [s.vals["Cu_pct"] for s in p.samples] == [fnum(v) for v in raw]
    assert log.actions == []


def test_log_api():
    p, log = run([{"SAMPLE_ID": "S1", "Cu_pct": "IS", "Au_ppm": "-999"},
                  {"SAMPLE_ID": "S1", "Cu_pct": "0.3", "Au_ppm": "0.1"}])
    assert log.counts() == {"C03": 1, "C04": 1, "C05": 1}
    assert log.excluded_samples() == {"S1"}
    assert {a.rule for a in log.for_element("Cu_pct")} == {"C04"}
    row = log.rows()[0]
    assert set(row) == {"Rule", "Sample", "Element", "Original", "Action",
                        "Reason", "Severity"}
    assert p.clean_log is log


def test_C12_percent_typed_as_ppm():
    # x 10000 is the commonest slip of all: a % column filled in ppm
    rows = crm_rows("OREAS-501b", 0.283, 0.312)
    rows[2]["Cu_pct"] = f"{0.2831 * 10000:.0f}"
    p, log = run(rows)
    assert p.samples[2].excl["Cu_pct"].startswith("C12")


def test_C13_swap_found_despite_laboratory_bias():
    # this laboratory reads every Au 12 % high: a swapped CRM carries the same
    # bias, so it must be compared with what the lab reports for the other CRM,
    # not only with that CRM's certificate
    rows = []
    for code, cu, au in (("OREAS-501b", 0.283, 0.312), ("OREAS-504b", 1.052, 0.905),
                         ("CDN-ME-1", 0.505, 1.48)):
        for i in range(8):
            d = ((i * 7) % 5 - 2) * 0.006
            rows.append({"SAMPLE_ID": f"{code}-{i}", "SAMPLE_TYPE": "CRM",
                         "CRM_ID": code, "Cu_pct": f"{cu * (1 + d):.4f}",
                         "Au_ppm": f"{au * 1.12 * (1 + d):.4f}"})
    rows.append({"SAMPLE_ID": "X1", "SAMPLE_TYPE": "CRM", "CRM_ID": "OREAS-504b",
                 "Cu_pct": "0.2850", "Au_ppm": f"{0.312 * 1.12 * 1.01:.4f}"})
    p, log = run(rows)
    assert by_id(p, "X1")[0].excl_all.startswith("C13")
    # the biased but correctly labelled results are not swaps
    assert rules_of(log).count("C13") == 1
