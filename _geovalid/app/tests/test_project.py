"""Phase 3 F10: profiles carrying column mappings and the ID-merge table, project files, headless mode, log file and
exit codes."""
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from geovalid_pro import cli, synth
from geovalid_pro.engine import load_inputs, load_params, save_profile
from geovalid_pro.project_file import (PROJECT_FORMAT, apply_profile_mappings, build_spec, load_project, save_project,
                                       store_mappings)


@pytest.fixture(scope="module")
def sample(tmp_path_factory):
    d = tmp_path_factory.mktemp("proj")
    synth.generate(str(d), inject=True)
    return d


def _renamed_collar(d: Path) -> Path:
    """A collar table whose headers the automatic mapping cannot resolve (to test stored mappings)."""
    c = pd.read_csv(d / "collar.csv", dtype=str)
    c = c.rename(columns={"HoleID": "BHNAME", "East": "COORD_A", "North": "COORD_B", "RL": "ELEV_Q"})
    f = d / "odd" / "collar.csv"
    f.parent.mkdir(exist_ok=True)
    c.to_csv(f, index=False)
    return f


def test_profile_keeps_mappings_and_id_merge(sample, tmp_path):
    f = _renamed_collar(sample)
    t = load_inputs([str(f)])[0]
    t.kind = "collar"
    from geovalid_pro.io.mapping import propose_mapping
    t.mapping = propose_mapping(t.raw.df, "collar")
    t.mapping.fields.update({"hole_id": "BHNAME", "x": "COORD_A", "y": "COORD_B", "z": "ELEV_Q"})
    params = load_params(None)
    store_mappings([t], params)
    params["id_merge"] = [{"raw_id": "gv-001", "target_id": "GV-001", "approved": True}]
    p = tmp_path / "prof.json"
    save_profile(params, str(p))
    doc = json.loads(p.read_text(encoding="utf-8"))
    assert doc["profile_format"] == "geovalid-profile/1" and doc["column_mappings"]["collar"]["fields"]["x"] == "COORD_A"
    again = load_inputs([str(f)])[0]
    msgs = apply_profile_mappings([again], load_params(str(p)))
    assert again.kind == "collar" and again.mapping.fields["hole_id"] == "BHNAME" and msgs
    assert load_params(str(p))["id_merge"][0]["target_id"] == "GV-001"


def test_project_round_trip_relative_paths(sample, tmp_path):
    proj = tmp_path / "work"
    shutil.copytree(sample, proj / "data")
    ins = [i for i in load_inputs(sorted(str(p) for p in (proj / "data").glob("*.csv"))) if i.kind != "ignore"]
    ins[0].enabled = False
    params = load_params(None)
    params["rules"]["COL-011"]["warn_m"] = 3.5
    save_project(str(proj / "p.json"), ins, {"dem": str(proj / "data" / "dem.asc")}, params, "Demo", str(proj / "out"), "en")
    raw = json.loads((proj / "p.json").read_text(encoding="utf-8"))
    assert raw["format"] == PROJECT_FORMAT and raw["inputs"][0]["path"].startswith("data/") and raw["optional"]["dem"] == "data/dem.asc"
    moved = tmp_path / "moved"
    shutil.move(str(proj), str(moved))                     # a project folder can be moved
    doc = load_project(str(moved / "p.json"))
    spec, out, lang, msgs = build_spec(doc)
    assert not msgs and lang == "en" and out == str((moved / "out").resolve())
    assert len(spec.inputs) == len(ins) - 1 and spec.params["rules"]["COL-011"]["warn_m"] == 3.5
    assert spec.dem_path == str((moved / "data" / "dem.asc").resolve())


def test_missing_columns_are_reported_not_guessed(sample, tmp_path):
    f = _renamed_collar(sample)
    t = load_inputs([str(f)])[0]
    t.kind = "collar"
    from geovalid_pro.io.mapping import propose_mapping
    t.mapping = propose_mapping(t.raw.df, "collar")
    t.mapping.fields.update({"hole_id": "BHNAME", "x": "COORD_A", "y": "COORD_B", "z": "ELEV_Q"})
    save_project(str(tmp_path / "p.json"), [t], {}, load_params(None), "x")
    c = pd.read_csv(f, dtype=str).rename(columns={"COORD_A": "EASTING_NEW"})
    c.to_csv(f, index=False)
    doc = load_project(str(tmp_path / "p.json"))
    spec, *_rest, msgs = build_spec(doc)
    assert any("x→COORD_A" in m for m in msgs) and spec.inputs[0].mapping.fields["x"] is None


def test_headless_cli_project_exit_code_and_log(sample, tmp_path):
    ins = [i for i in load_inputs(sorted(str(p) for p in sample.glob("*.csv"))) if i.kind != "ignore"]
    save_project(str(tmp_path / "p.json"), ins, {"dem": str(sample / "dem.asc")}, load_params(None), "Headless", str(tmp_path / "out"), "en")
    code = cli.main(["--cli", "--project", str(tmp_path / "p.json")])
    assert code == 2                                      # the sample has CRITICAL issues
    runs = list((tmp_path / "out").glob("GEOVALID_*"))
    assert len(runs) == 1
    log = (runs[0] / "geovalid_run.log").read_text(encoding="utf-8")
    assert "exit code 2" in log and "project:" in log and "Headless" in log


def test_headless_clean_data_exit_zero_or_one(tmp_path):
    d = tmp_path / "clean"
    synth.generate(str(d), inject=False)
    code = cli.main(["run", "--files", *sorted(str(p) for p in d.glob("*.csv")), "--out", str(tmp_path / "o"), "--lang", "en",
                     "--save-project", str(tmp_path / "saved.json")])
    assert code in (0, 1) and (tmp_path / "saved.json").is_file()
    assert json.loads((tmp_path / "saved.json").read_text(encoding="utf-8"))["format"] == PROJECT_FORMAT


def test_headless_apply_fixes_from_profile_id_map(sample, tmp_path):
    params = load_params(None)
    params["id_merge"] = [{"raw_id": "GV-999", "target_id": "GV-001", "approved": True}]
    prof = tmp_path / "p.json"
    save_profile(params, str(prof))
    code = cli.main(["run", "--files", *sorted(str(p) for p in sample.glob("*.csv")), "--profile", str(prof), "--out", str(tmp_path / "o"),
                     "--lang", "en", "--apply-fixes", "ID_MAP", "--reviewer", "QP"])
    assert code == 2
    run = next((tmp_path / "o").glob("GEOVALID_*"))
    log = pd.read_csv(run / "corrected" / "fix_log.csv")
    assert (log["fix_class"] == "ID_MAP").any() and (log["user"] == "QP").all()
