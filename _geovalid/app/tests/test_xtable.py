"""Phase 2 cross-table rules (v2 brief F8, XTB-01…07) on a small hand-built project with one case of each, and its
negative twin."""
import pandas as pd
import pytest

from geovalid_pro.engine import ProjectSpec, load_inputs, load_params, run


def _write(d, name, rows, cols):
    pd.DataFrame(rows, columns=cols).to_csv(d / f"{name}.csv", index=False)


def _project(d, bad=True):
    _write(d, "collar", [("XH-1", 1000, 2000, 500, 60), ("XH-2", 1100, 2000, 500, 60), ("XH-3", 1200, 2000, 500, 60)],
           ["HoleID", "East", "North", "RL", "Depth"])
    _write(d, "survey", [(h, 0, 0, -90) for h in ("XH-1", "XH-2", "XH-3")], ["HoleID", "Depth", "Azimuth", "Dip"])
    lith = [("XH-1", 0, 10, "ALLUV"), ("XH-1", 10, 30, "AND"), ("XH-1", 30, 50, "QMP"), ("XH-1", 50, 60, "AND"),
            ("XH-2", 0, 20, "AND"), ("XH-2", 20, 30, "DYKE"), ("XH-2", 30, 60, "AND"),
            ("XH-3", 0, 25, "AND"), ("XH-3", 25, 27, "FAULT"), ("XH-3", 27, 60, "AND")]
    if not bad:
        lith[6] = ("XH-2", 30, 60, "AND")
    _write(d, "lithology", lith, ["HoleID", "From", "To", "Lith"])
    wth = [("XH-1", 0, 15, "OXIDE"), ("XH-1", 15, 25, "MIXED"), ("XH-1", 25, 60, "PRIMARY"),
           ("XH-2", 0, 15, "OXIDE"), ("XH-2", 15, 35, "PRIMARY"), ("XH-2", 35, 40, "OXIDE" if bad else "PRIMARY"), ("XH-2", 40, 60, "PRIMARY"),
           ("XH-3", 0, 10, "OXIDE"), ("XH-3", 10, 22, "PRIMARY"), ("XH-3", 22, 30, "OXIDE" if bad else "PRIMARY"), ("XH-3", 30, 60, "PRIMARY")]
    _write(d, "weathering", wth, ["HoleID", "From", "To", "Weathering"])
    assay = []
    for h in ("XH-1", "XH-2", "XH-3"):
        for k in range(30):
            fr, to = 2.0 * k, 2.0 * k + 2
            cu = 0.05
            if h == "XH-1" and 30 <= fr < 50:
                cu = 0.8
            if h == "XH-2" and 20 <= fr < 30 and bad:
                cu = 1.2                                   # high grade in the barren dyke: 5 consecutive samples
            assay.append((h, fr, to, f"S{h[-1]}{k:03d}", cu))
    if bad:
        assay = [r for r in assay if not (r[0] == "XH-1" and 40 <= r[1] < 50)]   # 10 m of the QMP zone not assayed
    _write(d, "assay", assay, ["HoleID", "From", "To", "SampleID", "Cu_pct"])
    geo = [(h, 2.0 * k, 2.0 * k + 2, 2.0, 1.9, 1.5) for h in ("XH-1", "XH-2", "XH-3") for k in range(30)]
    if bad:
        geo[3] = ("XH-1", 6.0, 8.0, 3.0, 2.6, 1.0)      # run 3 m recorded over a 2 m interval; 2.6 m recovered
    _write(d, "geotech", geo, ["HoleID", "From", "To", "RunLength", "RecM", "RQDm"])
    den = [(h, 5.0 * k + 1, 5.0 * k + 1.2, 2.70) for h in ("XH-1", "XH-2", "XH-3") for k in range(12)]
    if bad:
        den[7] = ("XH-1", 36.0, 36.2, 3.30)              # QMP sample above the QMP range 2.5–2.8
    _write(d, "density", den, ["HoleID", "From", "To", "SG"])


def _run(d, bad):
    _project(d, bad)
    params = load_params(None)
    params["mineralised_codes"] = {"lith_code": ["QMP"]}
    params["barren_codes"] = {"lith_code": ["DYKE", "ALLUV"]}
    params["density_ranges"] = {"lith_code": {"QMP": [2.5, 2.8], "AND": [2.55, 2.85]}}
    params["analysis_cutoffs"] = {"Cu": [0.2, "%"]}
    params["severity_overrides"] = {}                    # emitted severities, before the brief-default overrides
    ins = [i for i in load_inputs(sorted(str(p) for p in d.glob("*.csv"))) if i.kind != "ignore"]
    kinds = {i.kind for i in ins}
    assert {"collar", "lithology", "weathering", "assay", "geotech", "density"} <= kinds, kinds
    return run(ProjectSpec(ins, project_name="xtb", params=params))


@pytest.fixture(scope="module")
def xbad(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("xbad"), True)


@pytest.fixture(scope="module")
def xgood(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("xgood"), False)


def _iss(res, rule):
    return res.issues[res.issues["rule_id"] == rule]


def test_xtb01_mineralised_zone_without_assay(xbad, xgood):
    i = _iss(xbad, "ASY-008")
    assert len(i) == 1 and i["severity"].iloc[0] == "WARNING" and i["hole_id"].iloc[0] == "XH-1"
    assert "10.0 of 20.0 m have no assay" in i["message_en"].iloc[0] and i["rule_alias"].iloc[0] == "XTB-01"
    assert _iss(xgood, "ASY-008").empty


def test_xtb02_recovered_length_beyond_interval(xbad, xgood):
    i = _iss(xbad, "GEO-001")
    assert i["message_en"].str.contains("Recovered length 2.6 m exceeds the interval length 2 m").any()
    assert _iss(xgood, "GEO-001").empty


def test_xtb04_density_outside_lithology_range(xbad, xgood):
    i = _iss(xbad, "DEN-001")
    hit = i[i["message_en"].str.contains("set for QMP")]
    assert len(hit) == 1 and hit["severity"].iloc[0] == "ERROR"
    assert _iss(xgood, "DEN-001").empty


def test_xtb05_coverage_mismatch(xbad, xgood):
    i = _iss(xbad, "INT-011")
    assert len(i) == 1 and i["hole_id"].iloc[0] == "XH-1" and "assay 83 %" in i["message_en"].iloc[0]
    cov = xbad.ctx.stats["coverage"]
    assert cov.loc["XH-1", "assay"] == pytest.approx(50 / 60) and cov.loc["XH-2", "lithology"] == 1.0
    assert _iss(xgood, "INT-011").empty


def test_xtb06_weathering_inversion_and_fault_control(xbad, xgood):
    i = _iss(xbad, "WTH-001").set_index("hole_id")
    assert i.loc["XH-2", "severity"] == "WARNING" and "OXIDE at 35–40 m below PRIMARY from 15 m" in i.loc["XH-2", "message_en"]
    assert i.loc["XH-3", "severity"] == "INFO" and "fault" in i.loc["XH-3", "message_en"]
    assert _iss(xgood, "WTH-001").empty


def test_xtb07_high_grade_in_barren_unit(xbad, xgood):
    i = _iss(xbad, "CRS-001")
    w = i[i["severity"] == "WARNING"]
    assert len(w) == 1 and w["hole_id"].iloc[0] == "XH-2" and "5 consecutive samples 20–30 m logged barren (DYKE)" in w["message_en"].iloc[0]
    assert _iss(xgood, "CRS-001").empty


def test_rules_not_applicable_without_codes(tmp_path):
    _project(tmp_path, True)
    ins = [i for i in load_inputs(sorted(str(p) for p in tmp_path.glob("*.csv"))) if i.kind != "ignore"]
    res = run(ProjectSpec(ins, project_name="xtb"))
    m = res.matrix.set_index("rule_id")
    assert m.loc["ASY-008", "status"] == "NOT_APPLICABLE" and m.loc["CRS-001", "status"] == "NOT_APPLICABLE"
    assert m.loc["WTH-001", "status"] == "RUN"
    assert (_iss(res, "WTH-001")["severity"] == "INFO").all()          # brief default (profile override)
