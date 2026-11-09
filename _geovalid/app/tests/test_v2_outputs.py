"""v2 brief §5.5, §5.6, §8, F10: fingerprints, fixes, evidence pack, issues JSON, JSON profiles, generated catalogue."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from geovalid_pro.core import fixes
from geovalid_pro.core.fingerprint import dataset_hash, hole_hashes
from geovalid_pro.engine import default_params, load_params, save_profile
from geovalid_pro.io.writers import write_outputs
from test_v2_rules import base, run_db


def test_per_hole_hashes_ignore_order_and_format_but_see_values(tmp_path):
    t = base()
    h1 = hole_hashes(run_db(tmp_path, t).ctx)
    t2 = base()
    t2["assay"] = t2["assay"].sample(frac=1, random_state=3)                      # row order
    t2["assay"]["Cu_pct"] = t2["assay"]["Cu_pct"].astype(float).map(lambda v: f"{v:.4f}0")   # trailing zero
    h2 = hole_hashes(run_db(tmp_path, t2).ctx)
    assert dataset_hash(h1) == dataset_hash(h2)
    t3 = base()
    t3["assay"].loc[250, "Cu_pct"] = "9.9999"                                   # one value in DH-03
    h3 = hole_hashes(run_db(tmp_path, t3).ctx).set_index("hole_id")["hash"]
    h1i = h1.set_index("hole_id")["hash"]
    assert (h3 != h1i).tolist() == [False, False, True]


def test_fix_classes_write_copies_and_log_never_sources(tmp_path):
    t = base()
    t["assay"].loc[t["assay"]["HoleID"] == "DH-02", "HoleID"] = "dh02"
    t["survey"].loc[2, "Azimuth"] = 370.0
    src = tmp_path / "in"
    src.mkdir()
    res = run_db(src, t)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in src.glob("*.csv")}
    cand = fixes.candidates(res)
    assert {"ID_MAP", "AZ_WRAP"} <= set(cand["fix_class"])
    idm = fixes.suggested_id_map(res)
    assert list(idm["raw_id"]) == ["dh02"] and list(idm["target_id"]) == ["DH-02"]
    out = fixes.apply_fixes(res, ["AZ_WRAP"], str(tmp_path / "fx1"), idm, user="qp")      # ID map not approved
    log = pd.read_csv(out["fix_log"])
    assert set(log["fix_class"]) == {"AZ_WRAP"} and log["new"].astype(str).tolist() == ["10"]
    idm["approved"] = True
    out = fixes.apply_fixes(res, ["ID_MAP"], str(tmp_path / "fx2"), idm, user="qp")
    log = pd.read_csv(out["fix_log"])
    assert len(log) == 100 and set(log["user"]) == {"qp"} and set(log["new"]) == {"DH-02"}
    fixed = pd.read_csv(tmp_path / "fx2" / "assay_corrected.csv")
    assert (fixed["HoleID"] == "dh02").sum() == 0
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in src.glob("*.csv")}
    assert before == after


def test_outputs_issues_json_and_evidence_pack(tmp_path):
    t = base()
    t["collar"].loc[0, "DrillType"] = "XQ"
    res = run_db(tmp_path, t)
    files = write_outputs(res, str(tmp_path / "out"), "both")
    doc = json.loads(files["issues_json"].read_text(encoding="utf-8"))
    assert doc["schema"] == "geovalid-issues/1.0" and doc["count"] == len(res.issues) and doc["dataset_hash"]
    pack = json.loads(files["evidence_json"].read_text(encoding="utf-8"))
    assert pack["schema"] == "geovalid-evidence/1.0"
    assert {c["tag"] for c in pack["clauses"]} == {"JORC-T1-S1-Verification", "JORC-T1-S1-Location", "JORC-T1-S3-DBIntegrity",
                                                   "NI43101-F1-Item12", "SK1300-601b96-iii-B-9", "CIM2019-4.2", "CIM2019-4.5", "CIM2019-6.2"}
    assert pack["qp_sections"] == {"procedures_applied": "", "limitations": "", "opinion_on_adequacy": ""}
    assert pack["dataset"]["dataset_hash"] == res.ctx.stats["dataset_hash"] and len(pack["dataset"]["files"]) == 4
    html = files["evidence_en"].read_text(encoding="utf-8")
    assert "Opinion on adequacy" in html and "does not express an opinion" in html
    assert (files["folder"] / "hole_hashes.csv").exists()
    rep = files["report_en"].read_text(encoding="utf-8")
    assert "Status by hole" in rep and "Dataset fingerprints" in rep and "PASS/FAIL" in rep


def test_json_profile_round_trip(tmp_path):
    p = default_params()
    p["severity_overrides"]["COL-014"] = "ERROR"
    p["disabled_rules"] = ["SUR-007"]
    p["code_dictionaries"] = {"lith_code": ["AND", "DIO"]}
    path = tmp_path / "profile.json"
    h = save_profile(p, str(path))
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["profile_format"] == "geovalid-profile/1" and doc["profile_hash"] == h
    q = load_params(str(path))
    assert q["severity_overrides"]["COL-014"] == "ERROR" and q["disabled_rules"] == ["SUR-007"]
    assert q["code_dictionaries"] == {"lith_code": ["AND", "DIO"]}


def test_code_dictionary_file_and_cli(tmp_path):
    t = base()
    t["lithology"].loc[2, "Lith"] = "ANDX"
    for k, df in t.items():
        df.to_csv(tmp_path / f"{k}.csv", index=False)
    pd.DataFrame({"field": ["lithology", "lithology"], "code": ["AND", "DIO"]}).to_csv(tmp_path / "codes.csv", index=False)
    app = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, "-m", "geovalid_pro", "run", "--files", *[str(tmp_path / f"{k}.csv") for k in t],
                        "--codes", str(tmp_path / "codes.csv"), "--out", str(tmp_path / "o"), "--lang", "en"],
                       cwd=app, capture_output=True, text=True, timeout=600)
    iss = pd.read_csv(next((tmp_path / "o").glob("*/issues.csv")))
    assert (iss["rule_id"] == "INT-015").sum() == 1, r.stderr[-2000:]


def test_rule_catalogue_is_generated_from_the_registry(tmp_path):
    app = Path(__file__).resolve().parents[1]
    out = tmp_path / "RULE_CATALOGUE.md"
    subprocess.run([sys.executable, "tools/gen_rule_catalogue.py", str(out)], cwd=app, check=True, timeout=300)
    text = out.read_text(encoding="utf-8")
    from geovalid_pro.engine import IMPORT_RULES
    from geovalid_pro.rules import REGISTRY
    for rid in IMPORT_RULES + [r.id for r in REGISTRY]:
        assert f"| {rid} |" in text
    assert "SRV-09" in text and "VAL-06" in text
