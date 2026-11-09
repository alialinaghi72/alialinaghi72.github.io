"""Phase 2 R1: laboratory / QA-QC file (GEOQAQC format), CRM certificates, reconciliation REC-01…07.

Synthetic files (geovalid_pro.synth_lab) carry one discrepancy of each class; the clean twin carries none. The owner's
GEOQAQC sample files are not in the public repository: the reference-count test runs only where they exist locally.
"""
from pathlib import Path

import pandas as pd
import pytest

from geovalid_pro import audit, synth_lab
from geovalid_pro.engine import ProjectSpec, load_inputs, load_params, run
from geovalid_pro.io.lab import convert, counts_by_type, read_crm_certificates, read_lab_file, read_umpire_file

REF = Path(__file__).resolve().parents[2] / "reference" / "qaqc_samples"


def _run(g, **kw):
    ins = [i for i in load_inputs([g["db"]]) if i.kind != "ignore"]
    return run(ProjectSpec(ins, lab_path=g["lab"], umpire_path=g["umpire"], crm_path=g["crm"], project_name="lab", **kw))


@pytest.fixture(scope="module")
def lab_case(tmp_path_factory):
    g = synth_lab.generate(str(tmp_path_factory.mktemp("lab")), inject=True)
    return g, _run(g)


@pytest.fixture(scope="module")
def lab_clean(tmp_path_factory):
    g = synth_lab.generate(str(tmp_path_factory.mktemp("labc")), inject=False)
    return g, _run(g)


def _iss(res, rule, alias=None):
    i = res.issues[res.issues["rule_id"] == rule]
    return i if alias is None else i[i["rule_alias"] == alias]


# ---- readers ------------------------------------------------------------------------------------------------------
def test_reader_classes_codes_and_units(lab_case):
    g, _ = lab_case
    c = read_lab_file(g["lab"])
    n = counts_by_type(c)
    assert n["ORIGINAL"] == 302 and n["CRM"] == 15 and n["BLANK"] == 8 and n["COARSE_BLANK"] == 7
    assert n["FIELD_DUP"] == 6 and n["PULP_DUP"] == 6
    au = next(a for a in c.analytes if a.analyte == "Au")
    assert au.unit == "ppb" and au.unit_declared
    assert int(au.parsed["not_analysed"].sum()) == 1                     # IS
    ag = next(a for a in c.analytes if a.analyte == "Ag")
    assert int(ag.parsed["not_analysed"].sum()) == 1                     # LNR
    assert (ag.parsed["flag"] == "BDL").sum() > 0 and ag.parsed.loc[ag.parsed["flag"] == "BDL", "dl"].eq(0.2).all()
    u = read_umpire_file(g["umpire"])
    assert len(u.df) == 40 and (u.df["qc_class"] == "UMPIRE").all()
    crm = read_crm_certificates(g["crm"])
    assert set(crm["crm_id"]) == {"LBCRM 1", "LBCRM-2", "LBCRM-3"}
    assert crm.loc[(crm["crm_id"] == "LBCRM-2") & (crm["analyte"] == "Au"), "unit"].iloc[0] == "ppb"
    assert convert(312, "ppb", "ppm") == pytest.approx(0.312) and convert(1.0, "%", "ppm") == pytest.approx(10000)


def test_unknown_sample_type_kept_and_reported(tmp_path):
    g = synth_lab.generate(str(tmp_path), inject=False)
    df = pd.read_csv(g["lab"], dtype=str, keep_default_na=False)
    df.loc[df.index[df["SAMPLE_TYPE"] == "PD"][:2], "SAMPLE_TYPE"] = "REP"
    df.to_csv(g["lab"], index=False)
    c = read_lab_file(g["lab"])
    assert (c.df["qc_class"] == "UNKNOWN").sum() == 2
    res = _run(g)
    w = _iss(res, "CRS-008", "REC-06")
    assert any("REP × 2" in m for m in w["message_en"])
    c2 = read_lab_file(g["lab"], {"lab_sample_types": {"rep": "PULP_DUP"}})
    assert (c2.df["qc_class"] == "UNKNOWN").sum() == 0


# ---- REC-01 … REC-06 ----------------------------------------------------------------------------------------------
def test_rec01_both_directions_with_case_suggestion(lab_case):
    g, res = lab_case
    i = _iss(res, "SMP-004", "REC-01")
    vals = set(i["value"])
    assert {"LB00030", "LB00031", "LB00020", "lb00020"} <= vals and len(i) == 4
    assert i.loc[i["value"] == "lb00020", "message_en"].str.contains("Closest laboratory ID: LB00020").all()
    assert not i["message_en"].str.contains("Closest database ID: LB0", regex=False).loc[i["value"] == "LB00030"].any()


def test_rec02_rec03_rec04_classes(lab_case):
    g, res = lab_case
    inj = g["injected"]
    a = _iss(res, "ASY-020")
    msg = " ".join(a["message_en"])
    assert inj["value_mismatch"] in msg and "0.9999" in msg
    assert a.loc[a["rule_alias"] == "REC-03", "message_en"].str.contains(f"{inj['scale_x1000']} Cu_pct.*×10\\^3", regex=True).any()
    coding = a[a["rule_alias"] == "REC-04"]
    assert set(inj["bdl_coding"]) <= set(coding["message_en"].str.extract(r"^(LB\d+)")[0]) and (coding["severity"] == "WARNING").all()
    assert a["message_en"].str.contains(f"{inj['rounded']} Cu_pct: the database holds the laboratory value rounded").any()
    assert a["message_en"].str.contains("6 consecutive database values (LB00201 … LB00206)", regex=False).any()
    assert a.loc[a["message_en"].str.contains("converting the declared laboratory unit"), "severity"].eq("INFO").all()
    rate = res.ctx.stats["lab_reconciliation"]["error_rate"]
    assert rate["compared"] > 800 and rate["mismatched"] >= 9 and rate["upper95_pct"] > rate["rate_pct"]


def test_rec05_reassays_listed_and_umpire_in_db(lab_case):
    g, res = lab_case
    a = _iss(res, "ASY-009", "REC-05")
    info = a[a["severity"] == "INFO"]
    assert set(info["value"]) == set(g["reassayed"])
    assert info["message_en"].str.contains("does not choose").all()
    assert info["message_en"].str.contains(r"Cu_pct = [\d.]+ \(= laboratory row \d+\)", regex=True).all()
    err = a[a["severity"] == "ERROR"]
    assert len(err) == 1 and err["message_en"].str.contains(g["injected"]["umpire_in_db"]).all()


def test_rec06_qc_sample_in_database(lab_case):
    g, res = lab_case
    c = _iss(res, "CRS-008", "REC-06")
    crit = c[c["severity"] == "CRITICAL"]
    assert len(crit) == 1 and crit["message_en"].str.contains(g["injected"]["crm_in_db"]).all()


def test_clean_twin_reconciles(lab_clean):
    _, res = lab_clean
    for r in ("SMP-004", "CRS-008"):
        assert _iss(res, r).empty, r
    a = _iss(res, "ASY-020")
    assert set(a["severity"]) <= {"INFO"}
    assert res.ctx.stats["lab_reconciliation"]["error_rate"]["mismatched"] == 0
    assert not res.errors


# ---- QA/QC on the laboratory file ---------------------------------------------------------------------------------
def test_crm_identity_conversion_mislabel_and_blank_swap(lab_case):
    g, res = lab_case
    q8 = _iss(res, "QAQ-008")
    assert len(q8) == 1 and q8["message_en"].str.contains("'LBCRM 1' differs only in separators").all()
    q2 = _iss(res, "QAQ-002")
    assert q2.loc[q2["severity"] == "INFO", "message_en"].str.contains("converted from the declared ppb").sum() == 0   # lab Au is ppb too
    q6 = _iss(res, "QAQ-006")
    assert q6["message_en"].str.contains(f"{g['mislabel']}: fails its declared CRM LBCRM-2 but matches LBCRM 1", regex=False).any()
    assert q6["message_en"].str.contains(f"{g['blank_swap']}: declared CRM LBCRM-3 but every element is at blank level", regex=False).any()
    assert q2["message_en"].str.contains("Reported below detection").any()


def test_crm_alias_resolves_and_converts(tmp_path):
    g = synth_lab.generate(str(tmp_path), inject=False)
    params = load_params(None)
    params["crm_id_aliases"] = {"LBCRM-1": "LBCRM 1"}
    res = _run(g, params=params)
    assert _iss(res, "QAQ-008").empty
    db = pd.read_csv(g["lab"], dtype=str)
    db["Au_ppm"] = [v if not v[0].isdigit() else f"{float(v) / 1000:.3f}" for v in db.pop("Au_ppb")]
    db.to_csv(g["lab"], index=False)
    res2 = _run(g, params=params)
    conv = _iss(res2, "QAQ-002")
    assert conv.loc[conv["severity"] == "INFO", "message_en"].str.contains("converted from the declared ppb to the column unit ppm").sum() == 3


def test_duplicate_parent_link_and_umpire_bias(lab_case):
    g, res = lab_case
    q10 = _iss(res, "QAQ-010")
    assert len(q10) == 1 and q10["message_en"].str.contains(g["orphan_duplicate"]).all()
    q7 = _iss(res, "QAQ-007")
    assert len(q7) == 1 and q7["severity"].iloc[0] == "INFO" and "40 pairs" in q7["message_en"].iloc[0]
    assert "Cu" in res.ctx.stats["umpire_pairs"]


def test_qc_aware_sequence_uses_lab_file(lab_case):
    _, res = lab_case
    assert _iss(res, "SMP-002").empty         # database numbers LB00030/31 removed, but they are issued in the lab file


# ---- REC-07 random audit ------------------------------------------------------------------------------------------
def test_random_audit_reproducible_and_import(lab_case, tmp_path):
    g, res = lab_case
    params = dict(load_params(None))
    s1, m1 = audit.select(res.ctx, params)
    s2, m2 = audit.select(res.ctx, params)
    assert m1["selection_hash"] == m2["selection_hash"] and m1["selected"] == min(m1["population"], 100)
    assert s1["sample_id"].tolist() == s2["sample_id"].tolist()
    p3 = dict(params, random_audit={"pct": 5, "min_n": 100, "seed": 1})
    assert audit.select(res.ctx, p3)[1]["selection_hash"] != m1["selection_hash"]
    # row order of the input does not change the selection
    db = pd.read_csv(g["db"], dtype=str).iloc[::-1]
    alt = tmp_path / "assay_db.csv"
    db.to_csv(alt, index=False)
    res_rev = _run(dict(g, db=str(alt)))
    assert set(audit.select(res_rev.ctx, params)[0]["sample_id"]) == set(s1["sample_id"])
    out = audit.export(res.ctx, params, str(tmp_path / "checklist.xlsx"))
    assert Path(out["path"]).is_file()
    df = pd.read_excel(out["path"], dtype=str)
    assert {"audit_id", "verified (Y/N)", "selection_hash", "db Cu_pct", "lab Cu_pct"} <= set(df.columns)
    df["verified (Y/N)"] = "Y"
    df.loc[[0, 1], "verified (Y/N)"] = "N"
    df.loc[2, "verified (Y/N)"] = ""
    df.to_excel(tmp_path / "filled.xlsx", index=False)
    r = _run(g, audit_path=str(tmp_path / "filled.xlsx"))
    ra = r.ctx.stats["random_audit"]
    assert ra["selection_matches"] and ra["checked"] == len(df) - 1 and ra["discrepancies"] == 2
    assert len(ra["discrepancy_rows"]) == 2 and ra["upper95_pct"] > ra["rate_pct"] > 0
    assert _run(g).ctx.stats["random_audit"]["status"].startswith("selection ready")


# ---- the owner's GEOQAQC sample files (local only) ----------------------------------------------------------------
@pytest.mark.skipif(not (REF / "demo_assay.csv").is_file(), reason="GEOQAQC sample files are kept out of the public repository")
def test_reference_counts():
    d = counts_by_type(read_lab_file(str(REF / "demo_assay.csv")))
    assert d == {"ORIGINAL": 1202, "FIELD_DUP": 60, "CRM": 60, "PULP_DUP": 48, "COARSE_BLANK": 36, "COARSE_DUP": 36, "PULP_BLANK": 24}
    a = counts_by_type(read_lab_file(str(REF / "assay.csv")))
    assert a == {"ORIGINAL": 320, "FIELD_DUP": 32, "CRM": 32, "BLANK": 32, "COARSE_DUP": 16, "PULP_DUP": 16}
    assert len(read_umpire_file(str(REF / "umpire_lab2.csv")).df) == 80
    demo = read_lab_file(str(REF / "demo_assay.csv"))
    na = {a.analyte: int(a.parsed["not_analysed"].sum()) for a in demo.analytes}
    assert na["Au"] == 3 and na["Ag"] == 2
    assert demo.df["sample_id"].duplicated().sum() == 2
