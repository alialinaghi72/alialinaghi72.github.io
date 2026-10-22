"""End-to-end gates (04 §3.4): 100 % recall on injected errors; no ERROR/CRITICAL on the clean twin."""
import glob

import pandas as pd
import pytest

from geovalid_pro import synth
from geovalid_pro.engine import ProjectSpec, load_inputs, run
from geovalid_pro.io.writers import write_outputs

# Findings the clean twin contains by design (campaign B is a handheld-GPS campaign).
DESIGNED = {("COL-010", "ERROR")}


def _run(folder):
    ins = [i for i in load_inputs(sorted(glob.glob(f"{folder}/*.csv"))) if i.kind != "ignore"]
    return run(ProjectSpec(ins, dem_path=f"{folder}/dem.asc", licence_path=f"{folder}/licence.csv",
                           crm_path=f"{folder}/crm_standards.csv", project_name="test"))


@pytest.fixture(scope="module")
def injected(tmp_path_factory):
    d = tmp_path_factory.mktemp("err")
    synth.generate(str(d), inject=True)
    return d, _run(str(d))


@pytest.fixture(scope="module")
def clean(tmp_path_factory):
    d = tmp_path_factory.mktemp("clean")
    synth.generate(str(d), inject=False)
    return d, _run(str(d))


def test_every_injected_error_is_detected(injected):
    folder, res = injected
    man = pd.read_csv(folder / "manifest.csv")
    missed = []
    for _, m in man.iterrows():
        sub = res.issues[res.issues["rule_id"] == m["rule_id"]]
        if isinstance(m["hole_id"], str):
            sub = sub[sub["hole_id"] == m["hole_id"]]
        if sub.empty:
            missed.append((m["rule_id"], m["hole_id"], m["description"]))
    assert not missed, missed


def test_no_rule_fails(injected, clean):
    for _, res in (injected, clean):
        assert (res.matrix["status"] != "FAILED").all(), res.matrix[res.matrix["status"] == "FAILED"]
        assert not res.errors


def test_clean_twin_has_no_errors(clean):
    _, res = clean
    bad = res.issues[res.issues["severity"].isin(["ERROR", "CRITICAL"])]
    unexpected = [(r, s) for r, s in zip(bad["rule_id"], bad["severity"]) if (r, s) not in DESIGNED]
    assert not unexpected, bad[["rule_id", "hole_id", "message_en"]].to_string()


def test_fingerprints_stable(clean):
    folder, res = clean
    again = _run(str(folder))
    assert set(res.issues["fingerprint"]) == set(again.issues["fingerprint"])


def test_outputs_written(injected, tmp_path):
    _, res = injected
    files = write_outputs(res, str(tmp_path), "both")
    for k in ("issue_log_xlsx", "issues_csv", "report_fa", "report_en"):
        assert files[k].exists() and files[k].stat().st_size > 1000
    flagged = list((files["folder"] / "flagged_tables").glob("*.csv"))
    assert len(flagged) >= 6
    col = pd.read_csv([f for f in flagged if f.name.startswith("collar")][0])
    assert {"QC_FLAG", "QC_COMMENT"} <= set(col.columns)
    assert (col["QC_FLAG"] == "C").any()
    html = files["report_fa"].read_text(encoding="utf-8")
    assert 'dir=\'rtl\'' in html and "گزارش اعتبارسنجی" in html


def test_sources_never_modified(tmp_path):
    synth.generate(str(tmp_path), inject=True)
    import hashlib
    before = {p: hashlib.sha256(open(p, "rb").read()).hexdigest() for p in glob.glob(f"{tmp_path}/*.csv")}
    res = _run(str(tmp_path))
    write_outputs(res, str(tmp_path / "out"), "en")
    after = {p: hashlib.sha256(open(p, "rb").read()).hexdigest() for p in before}
    assert before == after
