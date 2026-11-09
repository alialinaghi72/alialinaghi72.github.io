"""v2 brief §10.1: every new or changed rule has a positive test (error detected) and a negative test (clean data passes).

Each test builds a small database (3 holes, 0–100 m), changes one thing, runs the full engine and looks at one rule.
"""
import copy

import numpy as np
import pandas as pd

from geovalid_pro.engine import ProjectSpec, default_params, load_inputs, run

X0, Y0 = 500_000.0, 3_500_000.0


def base(n_holes=3):
    collar = pd.DataFrame({"HoleID": [f"DH-{i:02d}" for i in range(1, n_holes + 1)],
                           "East": [X0 + 100 * i for i in range(n_holes)], "North": [Y0 + 50 * i for i in range(n_holes)],
                           "RL": [1500.0 + i for i in range(n_holes)], "MaxDepth": [100.0] * n_holes,
                           "Azimuth": [45.0] * n_holes, "Dip": [-60.0] * n_holes, "DrillType": ["DD"] * n_holes})
    sv = []
    for h in collar["HoleID"]:
        for k, d in enumerate((0, 30, 60, 90)):
            sv.append({"HoleID": h, "Depth": float(d), "Azimuth": 45.0 + 0.3 * k, "Dip": -60.0 + 0.2 * k, "Instrument": "Gyro"})
    survey = pd.DataFrame(sv)
    rng = np.random.default_rng(1)
    rows, num = [], 1000
    for h in collar["HoleID"]:
        for d in range(100):
            num += 1
            rows.append({"HoleID": h, "From": float(d), "To": float(d + 1), "SampleID": f"S{num}",
                         "Cu_pct": f"{rng.uniform(0.1, 1.0):.4f}", "Au_ppm": f"{rng.uniform(0.05, 0.9):.3f}",
                         "Fe_pct": f"{rng.uniform(2, 6):.2f}"})
    assay = pd.DataFrame(rows)
    lith = pd.DataFrame([{"HoleID": h, "From": f, "To": t, "Lith": c} for h in collar["HoleID"]
                         for f, t, c in ((0.0, 40.0, "AND"), (40.0, 100.0, "DIO"))])
    return {"collar": collar, "survey": survey, "assay": assay, "lithology": lith}


def run_db(tmp_path, tables, params=None):
    paths = []
    for name, df in tables.items():
        p = tmp_path / f"{name}.csv"
        df.to_csv(p, index=False)
        paths.append(str(p))
    ins = [i for i in load_inputs(paths) if i.kind != "ignore"]
    return run(ProjectSpec(ins, params=params or default_params()))


def issues(res, rule):
    return res.issues[res.issues["rule_id"] == rule]


def status(res, rule):
    return res.matrix.set_index("rule_id").at[rule, "status"]


# ------------------------------------------------------------------ the clean base database
def test_clean_base_has_no_new_rule_findings(tmp_path):
    res = run_db(tmp_path, base())
    new = ["SUR-013", "SUR-014", "SUR-015", "SUR-023", "SUR-027", "COL-002", "COL-003", "COL-014", "IMP-006", "IMP-012",
           "INT-001", "INT-002", "INT-012", "INT-007", "SMP-001", "SMP-002", "ASY-003", "ASY-010", "ASY-019", "ASY-028", "ASY-029", "ASY-030"]
    found = res.issues[res.issues["rule_id"].isin(new) & (res.issues["severity"] != "INFO")]
    found = found[~((found["rule_id"] == "SUR-014"))]           # north reference undeclared: tested separately
    assert found.empty, found[["rule_id", "hole_id", "message_en"]].to_string()
    assert (res.matrix["status"] != "FAILED").all()


# ------------------------------------------------------------------ survey QA pack (F1)
def test_sur_007_missing_zero_station(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "SUR-007").empty
    t["survey"] = t["survey"][t["survey"]["Depth"] > 0]
    i = issues(run_db(tmp_path, t), "SUR-007")
    assert len(i) == 3 and set(i["severity"]) == {"WARNING"} and "collar orientation" in i["message_en"].iloc[0]


def test_sur_009_straight_line_assumption(tmp_path):
    t = base()
    t["collar"].loc[0, "MaxDepth"] = 150.0
    t["survey"] = t["survey"][t["survey"]["HoleID"] != "DH-01"]
    i = issues(run_db(tmp_path, t), "SUR-009")
    assert (i["hole_id"] == "DH-01").any() and "straight-line" in i["message_en"].iloc[0]
    t2 = base()
    t2["survey"] = t2["survey"][t2["survey"]["HoleID"] != "DH-01"]           # 100 m: not above the 100 m threshold
    assert issues(run_db(tmp_path, t2), "SUR-009").empty


def test_sur_012_near_vertical_suppression_reported(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "SUR-012").empty
    t["survey"].loc[t["survey"]["HoleID"] == "DH-02", "Dip"] = -89.0
    t["survey"].loc[(t["survey"]["HoleID"] == "DH-02") & (t["survey"]["Depth"] == 60), "Azimuth"] = 200.0
    t["collar"].loc[1, "Dip"] = -89.0
    i = issues(run_db(tmp_path, t), "SUR-012")
    assert list(i["severity"]) == ["INFO"] and "suppressed" in i["message_en"].iloc[0]


def test_sur_013_neighbour_inconsistent_station(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "SUR-013").empty
    t["survey"].loc[(t["survey"]["HoleID"] == "DH-03") & (t["survey"]["Depth"] == 30), "Azimuth"] = 70.0
    i = issues(run_db(tmp_path, t), "SUR-013")
    assert list(i["hole_id"]) == ["DH-03"] and i["severity"].iloc[0] == "ERROR" and i["from_m"].iloc[0] == 30


def test_sur_014_north_reference(tmp_path):
    t = base()
    i = issues(run_db(tmp_path, t), "SUR-014")
    assert len(i) == 1 and i["severity"].iloc[0] == "WARNING"                  # undeclared
    p = default_params()
    p["north_reference"] = "TRUE"
    p["rules"]["SUR-014"]["declination_deg"] = 4.0
    t["survey"]["AzMag"] = t["survey"]["Azimuth"] - 4.0
    assert issues(run_db(tmp_path, t, copy.deepcopy(p)), "SUR-014").empty   # consistent correction
    t["survey"].loc[t["survey"]["HoleID"] == "DH-02", "AzMag"] = t["survey"]["Azimuth"] - 1.0
    i = issues(run_db(tmp_path, t, copy.deepcopy(p)), "SUR-014")
    assert list(i["hole_id"]) == ["DH-02"] and i["severity"].iloc[0] == "ERROR"


def test_sur_015_desurvey_sensitivity(tmp_path):
    t = base()
    i = issues(run_db(tmp_path, t), "SUR-015")
    assert set(i["severity"]) == {"INFO"}                                         # summary only
    t["collar"].loc[0, "MaxDepth"] = 400.0
    s = t["survey"]
    s.loc[(s["HoleID"] == "DH-01") & (s["Depth"] == 90), ["Azimuth", "Dip"]] = [120.0, -30.0]
    s.loc[len(s)] = {"HoleID": "DH-01", "Depth": 400.0, "Azimuth": 125.0, "Dip": -28.0, "Instrument": "Gyro"}
    t["assay"] = t["assay"]
    i = issues(run_db(tmp_path, t), "SUR-015")
    assert (i[i["severity"] == "WARNING"]["hole_id"] == "DH-01").any()


def test_sur_023_collar_vs_first_station(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "SUR-023").empty
    t["collar"].loc[2, "Dip"] = -75.0
    i = issues(run_db(tmp_path, t), "SUR-023")
    assert list(i["hole_id"]) == ["DH-03"] and i["severity"].iloc[0] == "ERROR"


def test_sur_027_magnetic_interference(tmp_path):
    t = base()
    s = t["survey"]
    s.loc[(s["HoleID"] == "DH-01") & (s["Depth"] == 60), "Azimuth"] = 55.0
    s.loc[(s["HoleID"] == "DH-01") & (s["Depth"] == 60), "Dip"] = -59.8
    assert issues(run_db(tmp_path, t), "SUR-027").empty                      # gyro: not magnetic
    t["survey"]["Instrument"] = "Reflex EZ-Shot"
    i = issues(run_db(tmp_path, t), "SUR-027")
    assert (i["hole_id"] == "DH-01").all() and len(i) >= 1


# ------------------------------------------------------------------ identifiers, collars, schema (F3, F4)
def test_col_002_dummy_coordinates(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "COL-002").empty
    t["collar"].loc[1, "RL"] = -999
    i = issues(run_db(tmp_path, t), "COL-002")
    assert list(i["hole_id"]) == ["DH-02"] and i["severity"].iloc[0] == "CRITICAL"


def test_col_003_hole_id_groups_across_tables(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "COL-003").empty
    t["assay"].loc[t["assay"]["HoleID"] == "DH-02", "HoleID"] = "dh02"
    res = run_db(tmp_path, t)
    i = issues(res, "COL-003")
    assert len(i) == 1 and i["severity"].iloc[0] == "ERROR" and i["hole_id"].iloc[0] == "DH-02" and i["fix_class"].iloc[0] == "ID_MAP"
    o = issues(res, "INT-006")
    assert "DH-02" in o["suggested_fix"].iloc[0]                             # SCH-04b closest collar suggestion


def test_col_014_drill_type_codes(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "COL-014").empty
    t["collar"].loc[0, "DrillType"] = "XQ"
    i = issues(run_db(tmp_path, t), "COL-014")
    assert len(i) == 1 and "XQ" in i["message_en"].iloc[0]


def test_imp_006_missing_value_ambiguity(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "IMP-006").empty
    t["collar"]["MaxDepth"] = t["collar"]["MaxDepth"].astype(object)
    t["collar"].loc[0, "MaxDepth"] = ""
    t["collar"].loc[1, "MaxDepth"] = -999
    i = issues(run_db(tmp_path, t), "IMP-006")
    assert len(i) == 1 and i["severity"].iloc[0] == "WARNING" and i["field"].iloc[0] == "eoh_m"


def test_imp_012_crs_plausibility(tmp_path):
    t = base(6)
    i = issues(run_db(tmp_path, t), "IMP-012")
    assert list(i["severity"]) == ["INFO"]                                    # undeclared CRS, described
    t["collar"].loc[[4, 5], "East"] = t["collar"].loc[[4, 5], "East"] + 300_000
    i = issues(run_db(tmp_path, t), "IMP-012")
    assert (i["severity"] == "ERROR").sum() == 1
    p = default_params()
    p["crs"] = {"epsg": 32640}
    t = base(4)
    t["collar"].loc[0, "East"] = 950_000.0
    i = issues(run_db(tmp_path, t, p), "IMP-012")
    assert list(i[i["severity"] == "ERROR"]["hole_id"]) == ["DH-01"]


# ------------------------------------------------------------------ intervals and samples (F4)
def test_int_001_severities(tmp_path):
    t = base()
    a = t["assay"]
    a.loc[5, ["From", "To"]] = [6.0, 5.0]
    a.loc[205, "To"] = a.loc[205, "From"]
    i = issues(run_db(tmp_path, t), "INT-001")
    assert set(zip(i["hole_id"], i["severity"])) == {("DH-01", "CRITICAL"), ("DH-03", "ERROR")}


def test_int_002_overlap_and_int_012_precision_artefact(tmp_path):
    t = base()
    res = run_db(tmp_path, t)
    assert issues(res, "INT-002").empty and issues(res, "INT-012").empty
    l = t["lithology"]
    l.loc[1, "From"] = 39.9995                       # 0.5 mm overlap: precision artefact
    l.loc[3, "From"] = 35.0                          # 5 m overlap: real
    res = run_db(tmp_path, t)
    a, b = issues(res, "INT-012"), issues(res, "INT-002")
    assert list(a["hole_id"]) == ["DH-01"] and a["severity"].iloc[0] == "WARNING"
    assert list(b["hole_id"]) == ["DH-02"] and b["severity"].iloc[0] == "CRITICAL"


def test_int_007_sample_length_by_drill_type(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "INT-007").empty
    a = t["assay"]
    a = a[~((a["HoleID"] == "DH-01") & (a["From"].between(11, 17)))].copy()
    a.loc[(a["HoleID"] == "DH-01") & (a["From"] == 10), "To"] = 18.0
    t["assay"] = a
    i = issues(run_db(tmp_path, t), "INT-007")
    assert len(i[i["severity"] == "WARNING"]) == 1


def test_smp_001_duplicate_sample_id(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "SMP-001").empty
    t["assay"].loc[150, "SampleID"] = t["assay"].loc[10, "SampleID"]
    i = issues(run_db(tmp_path, t), "SMP-001")
    assert len(i) == 1 and i["severity"].iloc[0] == "CRITICAL"


def test_smp_002_numbering(tmp_path):
    t = base()
    t["assay"]["SampleType"] = "ORIGINAL"
    qc = pd.DataFrame([{"HoleID": "", "From": "", "To": "", "SampleID": "S1301", "SampleType": "CRM",
                        "Cu_pct": "0.5", "Au_ppm": "0.8", "Fe_pct": "1.0"}])
    a = t["assay"]
    a.loc[a.index >= 50, "SampleID"] = [f"S{int(s[1:]) + 1}" for s in a.loc[a.index >= 50, "SampleID"]]   # 1051 used by QC
    qc.loc[0, "SampleID"] = "S1051"
    t["assay"] = pd.concat([a.iloc[:50], qc, a.iloc[50:]], ignore_index=True)
    assert issues(run_db(tmp_path, t), "SMP-002").empty                       # the QC insert fills the number
    t["assay"] = t["assay"][t["assay"]["SampleID"] != "S1051"]
    i = issues(run_db(tmp_path, t), "SMP-002")
    assert len(i) == 1 and "S1051" in i["message_en"].iloc[0]
    t2 = base()
    a = t2["assay"]
    a.loc[[20, 21], "SampleID"] = a.loc[[21, 20], "SampleID"].to_numpy()
    i = issues(run_db(tmp_path, t2), "SMP-002")
    assert list(i["hole_id"]) == ["DH-01"] and "out of downhole order" in i["message_en"].iloc[0]


# ------------------------------------------------------------------ values (F5)
def test_asy_002_bdl_coding_inventory(tmp_path):
    t = base()
    t["assay"].loc[[3, 4], "Au_ppm"] = "<0.01"
    assert issues(run_db(tmp_path, t), "ASY-002").query("severity == 'WARNING'").empty
    t["assay"].loc[[5], "Au_ppm"] = "-0.01"
    i = issues(run_db(tmp_path, t), "ASY-002").query("severity == 'WARNING'")
    assert len(i) == 1 and "2 ways" in i["message_en"].iloc[0]


def test_asy_003_element_sum(tmp_path):
    t = base()
    t["assay"].loc[7, ["Cu_pct", "Fe_pct"]] = ["60.0", "55.0"]
    i = issues(run_db(tmp_path, t), "ASY-003")
    assert (i["field"] == "element sum").sum() == 1 and i["severity"].iloc[0] == "CRITICAL"


def test_asy_010_detection_limits(tmp_path):
    t = base()
    t["assay"].loc[[1, 2], "Au_ppm"] = "<0.01"
    assert issues(run_db(tmp_path, t), "ASY-010").empty
    t["assay"].loc[[3], "Au_ppm"] = "<0.005"
    assert len(issues(run_db(tmp_path, t), "ASY-010")) == 1


def test_asy_019_mixed_labs(tmp_path):
    t = base()
    t["assay"]["Lab"] = "ALS"
    assert issues(run_db(tmp_path, t), "ASY-019").empty
    t["assay"].loc[:30, "Lab"] = "SGS"
    i = issues(run_db(tmp_path, t), "ASY-019")
    assert len(i) == 1 and "ALS" in i["message_en"].iloc[0] and "SGS" in i["message_en"].iloc[0]


def test_asy_028_stoichiometric_cap(tmp_path):
    t = base()
    t["assay"]["Zn_pct"] = "1.0"
    t["assay"].loc[9, "Zn_pct"] = "60"
    assert issues(run_db(tmp_path, t), "ASY-028").empty
    t["assay"].loc[9, "Zn_pct"] = "70"
    i = issues(run_db(tmp_path, t), "ASY-028")
    assert len(i) == 1 and i["severity"].iloc[0] == "ERROR"


def test_asy_029_downhole_spike(tmp_path):
    t = base()
    assert issues(run_db(tmp_path, t), "ASY-029").empty
    t["assay"].loc[50, "Cu_pct"] = "25.0"
    i = issues(run_db(tmp_path, t), "ASY-029")
    assert list(i["from_m"]) == [50.0] and i["severity"].iloc[0] == "INFO"


def test_asy_030_repeated_values(tmp_path):
    t = base()
    t["assay"].loc[60:63, "Cu_pct"] = "0.5000"
    assert issues(run_db(tmp_path, t), "ASY-030").empty                      # 4 in a row: below the run length
    t["assay"].loc[60:65, "Cu_pct"] = "0.5000"
    i = issues(run_db(tmp_path, t), "ASY-030")
    assert len(i) == 1 and i["value"].iloc[0] == "6"


def test_int_015_code_dictionary(tmp_path):
    t = base()
    res = run_db(tmp_path, t)
    assert status(res, "INT-015") == "NOT_APPLICABLE"
    p = default_params()
    p["code_dictionaries"] = {"lith_code": ["AND", "DIO"]}
    assert issues(run_db(tmp_path, t, copy.deepcopy(p)), "INT-015").empty
    t["lithology"].loc[2, "Lith"] = "ANDX"
    i = issues(run_db(tmp_path, t, copy.deepcopy(p)), "INT-015")
    assert len(i) == 1 and i["value"].iloc[0] == "ANDX" and i["severity"].iloc[0] == "ERROR"


# ------------------------------------------------------------------ registry and profile (§5.2, §5.3)
def test_severity_override_and_disabled_rule(tmp_path):
    t = base()
    t["collar"].loc[0, "DrillType"] = "XQ"
    p = default_params()
    p["severity_overrides"]["COL-014"] = "ERROR"
    p["disabled_rules"] = ["SUR-007"]
    res = run_db(tmp_path, t, p)
    i = issues(res, "COL-014")
    assert list(i["severity"]) == ["ERROR"] and list(i["severity_default"]) == ["WARNING"]
    assert status(res, "SUR-007") == "DISABLED"


def test_issue_fields_v2(tmp_path):
    t = base()
    t["collar"].loc[0, "DrillType"] = "XQ"
    res = run_db(tmp_path, t)
    r = issues(res, "COL-014").iloc[0]
    assert r["category"] == "B" and r["rule_alias"] == "COL-08" and r["source_file"] == "collar.csv" and r["src_row"] == 2
    assert "NI43101-F1-Item12" in r["standards_refs"]
