import csv
import json
import os

import pytest

from conftest import DATA
from geoqaqc import session
from geoqaqc.diagnosis import diagnose
from geoqaqc.export_csv import export_results
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, FormulaBook, RuleBook)
from test_demo_detection import demo


def _read(path):
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def run():
    p, R = demo()
    F = FormulaBook(DEFAULT_FORMULAS)
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S = dict(DEFAULT_SETTINGS)
    rb = RuleBook()
    return p, R, F, C, S, rb, diagnose(p, R, C, S, rb)


def test_export_files(run, tmp_path):
    p, R, F, C, S, rb, d = run
    files = export_results(p, F, C, S, rb, d, str(tmp_path), "demo", log=lambda m: None)
    names = {os.path.basename(f) for f in files}
    for n in ("scorecard", "crm_results", "crm_rule_violations", "blank_results",
              "duplicate_pairs", "duplicate_summary", "thompson_howarth",
              "umpire_pairs", "umpire_summary", "protocol", "cleaning_log",
              "findings", "error_budget", "batch_status", "reassay_ranges",
              "accuracy_curve", "crm_drift"):
        assert f"demo_{n}.csv" in names, n
    findings = _read(tmp_path / "demo_findings.csv")
    assert findings and {"Element", "Stage", "Severity", "Finding", "Evidence",
                         "Cause", "Actions", "Owner", "Timing"} <= set(findings[0])
    blanks = _read(tmp_path / "demo_blank_results.csv")
    assert {"COARSE BLANK", "PULP BLANK"} <= {r["Blank type"] for r in blanks}
    clean = _read(tmp_path / "demo_cleaning_log.csv")
    assert any(r["Rule"] == "C13" for r in clean)


def test_protocol_changed_flag(run, tmp_path):
    p, R, F, C, S, _, d = run
    rb = RuleBook()
    rb.set("drift_p", 0.01)
    C2 = {k: dict(v) for k, v in C.items()}
    C2["crm_bias"]["cuts"] = [1.0, 2.0, 4.0, 6.0, 9.0]
    export_results(p, F, C2, S, rb, d, str(tmp_path), "x", log=lambda m: None)
    rows = {r["Key"]: r for r in _read(tmp_path / "x_protocol.csv")}
    assert rows["drift_p"]["Kind"] == "RULE"
    assert rows["drift_p"]["Changed"] == "yes"
    assert rows["swap_frac"]["Changed"] == ""
    assert rows["crm_bias"]["Changed"] == "yes"


def test_session_roundtrip(run, tmp_path):
    p, R, F, C, S, _, d = run
    rb = RuleBook()
    rb.set("swap_single_z", 8.0)
    F2 = FormulaBook(DEFAULT_FORMULAS)
    F2.set_expr("dup_hard", "abs(a - b) / (a + b) * 100.0")
    C2 = {k: dict(v) for k, v in C.items()}
    C2["blank_fail"]["cuts"] = [0.5, 1.0, 2.0, 5.0, 10.0]
    S2 = dict(S)
    S2["k_dl"] = 10.0
    meta = {"project": "Demo project", "client": "Client Co.",
            "detail_elements": ["Cu_pct"]}
    path = str(tmp_path / "s.qaproj")
    session.save(path, p, F2, C2, S2, rb, meta)
    st = session.load(path)
    assert st["version"] == "2.0"
    out = session.restore(st, log=lambda m: None)
    assert out["RB"]["swap_single_z"] == 8.0
    assert out["F"].expr("dup_hard") == "abs(a - b) / (a + b) * 100.0"
    assert out["C"]["blank_fail"]["cuts"] == [0.5, 1.0, 2.0, 5.0, 10.0]
    assert out["S"]["k_dl"] == 10.0
    assert out["meta"]["client"] == "Client Co."
    pr = out["project"]
    assert pr.assay.mapping == p.assay.mapping
    assert pr.crm is not None and pr.umpire is not None
    assert out["missing"] == []


def test_load_v11_session(tmp_path):
    state = {"version": "1.1", "settings": {"k_dl": 7.0},
             "formulas": {"crm_bias": "(meas - cert) / cert * 100"},
             "criteria": {"crm_bias": [2, 3, 5, 7, 10]},
             "assay": {"kind": "assay", "name": "ASSAY",
                       "path": os.path.join(DATA, "assay.csv"),
                       "mapping": {"sampleid": "SAMPLE_ID", "type": "SAMPLE_TYPE"},
                       "value_cols": [["Cu_pct", "numeric"]], "type_map": {},
                       "dl": {}},
             "crm": None, "pairs": None,
             "umpire": {"kind": "umpire", "name": "U", "path": "/no/such/file.csv",
                        "mapping": {"sampleid": "SAMPLE_ID"}, "value_cols": [],
                        "type_map": {}, "dl": {}}}
    path = tmp_path / "old.qaproj"
    path.write_text(json.dumps(state), encoding="utf-8")
    out = session.restore(session.load(str(path)), log=lambda m: None)
    assert out["S"]["k_dl"] == 7.0
    assert out["RB"].changed() == []
    assert out["project"].assay.value_cols == [("Cu_pct", "numeric")]
    assert out["project"].umpire is None
    assert out["missing"] == ["/no/such/file.csv"]
