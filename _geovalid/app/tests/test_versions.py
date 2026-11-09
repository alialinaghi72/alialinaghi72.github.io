"""Phase 2 F6: version comparison (three-stage interval diff, change classes, metal deltas, per-hole hash skipping),
accepted snapshots and VER-009. The baseline is the clean synthetic database; the current version carries one change
of each class."""
import glob
import shutil

import pandas as pd
import pytest

from geovalid_pro import synth, versions
from geovalid_pro.engine import ProjectSpec, load_inputs, run


def _inputs(folder):
    return [i for i in load_inputs(sorted(glob.glob(f"{folder}/*.csv"))) if i.kind != "ignore"]


def _edit(cur):
    c = pd.read_csv(cur / "collar.csv", dtype=str)
    s = pd.read_csv(cur / "survey.csv", dtype=str)
    a = pd.read_csv(cur / "assay.csv", dtype=str, keep_default_na=False)
    lith = pd.read_csv(cur / "lithology.csv", dtype=str, encoding="utf-8-sig")
    # hole deleted (GV-064 from every table) and hole added (copy of GV-063 as GV-099)
    for f in ("collar", "survey", "assay", "alteration", "weathering", "geotech", "density"):
        df = pd.read_csv(cur / f"{f}.csv", dtype=str, keep_default_na=False)
        df = df[df.iloc[:, 0] != "GV-064"]
        add = df[df.iloc[:, 0] == "GV-063"].copy()
        add.iloc[:, 0] = "GV-099"
        if f == "assay":
            add["SampleID"] = "N" + add["SampleID"]
        df = pd.concat([df, add])
        df.to_csv(cur / f"{f}.csv", index=False)
    lith = lith[lith.iloc[:, 0] != "GV-064"]
    add = lith[lith.iloc[:, 0] == "GV-063"].copy()
    add.iloc[:, 0] = "GV-099"
    lith = pd.concat([lith, add])
    c = pd.read_csv(cur / "collar.csv", dtype=str)
    c.loc[c["HoleID"] == "GV-002", "East"] = f"{float(c.loc[c['HoleID'] == 'GV-002', 'East'].iloc[0]) + 5:.3f}"
    c.to_csv(cur / "collar.csv", index=False)
    s = pd.read_csv(cur / "survey.csv", dtype=str)
    i = s.index[s["HoleID"] == "GV-003"][2]
    s.loc[i, "Dip"] = f"{float(s.loc[i, 'Dip']) + 3:.2f}"
    s.to_csv(cur / "survey.csv", index=False)
    a = pd.read_csv(cur / "assay.csv", dtype=str, keep_default_na=False)
    r = a.index[(a["HoleID"] == "GV-004") & (a["SampleType"] == "ORIGINAL")][40]
    a.loc[r, "Cu_pct"] = "1.2345"                                         # re-assayed
    r2 = a.index[(a["HoleID"] == "GV-005") & (a["SampleType"] == "ORIGINAL")][30]
    fr, to = float(a.at[r2, "From"]), float(a.at[r2, "To"])
    half = a.loc[[r2]].copy()
    a.loc[r2, "To"] = f"{(fr + to) / 2:.2f}"
    half["From"] = f"{(fr + to) / 2:.2f}"
    half["SampleID"] = half["SampleID"] + "B"
    a = pd.concat([a, half])                                              # re-segmented: one interval split in two
    r3 = a.index[(a["HoleID"] == "GV-006") & (a["SampleType"] == "ORIGINAL")][10]
    a = a.drop(index=r3)                                                  # interval removed
    a.to_csv(cur / "assay.csv", index=False)
    j = lith.index[lith.iloc[:, 0] == "GV-007"][2]
    lith.iloc[lith.index.get_loc(j), 3] = "DIO" if lith.loc[j].iloc[3] != "DIO" else "AND"
    lith.to_csv(cur / "lithology.csv", index=False, encoding="utf-8-sig")


@pytest.fixture(scope="module")
def vcase(tmp_path_factory):
    base = tmp_path_factory.mktemp("base")
    synth.generate(str(base), inject=False)
    cur = tmp_path_factory.mktemp("cur")
    for f in base.glob("*"):
        shutil.copy(f, cur / f.name)
    _edit(cur)
    res = run(ProjectSpec(_inputs(cur), project_name="v", baseline_inputs=_inputs(base)))
    return base, cur, res


def test_change_classes(vcase):
    _, _, res = vcase
    v = res.ctx.stats["version"]
    s = v["summary"]
    assert s["holes"]["added"] == 1 and s["holes"]["deleted"] == 1
    assert s["holes"]["changed"] == 6 and s["holes"]["unchanged"] == s["holes"]["common"] - 6
    ch = v["changes"]
    by = lambda cls: ch[ch["change_class"] == cls]
    assert set(by("hole added")["hole_id"]) == {"GV-099"} and set(by("hole deleted")["hole_id"]) == {"GV-064"}
    mv = by("collar moved")
    assert list(mv["hole_id"]) == ["GV-002"] and abs(mv["delta"].iloc[0] - 5.0) < 1e-6
    sv = by("survey changed")
    assert list(sv["hole_id"]) == ["GV-003"] and sv["delta"].iloc[0] > 0.5
    ra = by("re-assayed")
    assert (ra["hole_id"] == "GV-004").all() and ra["new"].iloc[0] == "1.2345" and ra["field"].iloc[0] == "Cu"
    rs = by("re-segmented")
    assert list(rs["hole_id"]) == ["GV-005"] and "1 interval(s) → 2 interval(s)" in rs["detail"].iloc[0]
    rm = by("interval removed")
    assert list(rm["hole_id"]) == ["GV-006"]
    cc = by("code changed")
    assert list(cc["hole_id"]) == ["GV-007"] and cc["field"].iloc[0] == "lith_code"
    assert by("interval added").empty


def test_metal_deltas_and_reconciliation(vcase):
    _, _, res = vcase
    m = res.ctx.stats["version"]["metal"].set_index(["analyte", "scope"])
    cu_all, cu_common = m.loc[("Cu", "all holes")], m.loc[("Cu", "common holes")]
    assert cu_all["delta_metal"] != 0 and cu_common["delta_metal"] != 0
    hm = res.ctx.stats["version"]["metal_by_hole"]
    cu = hm[hm["analyte"] == "Cu"].set_index("hole_id")
    assert {"GV-004", "GV-006", "GV-064", "GV-099"} <= set(cu.index)
    assert "GV-005" not in cu.index or abs(cu.loc["GV-005", "delta_metal"]) < 1e-9      # a split keeps the metal


def test_ver_rules(vcase):
    _, _, res = vcase
    i = res.issues
    v1 = i[i["rule_id"] == "VER-001"]
    assert (v1.loc[v1["severity"] == "WARNING", "hole_id"] == "GV-064").all() and (v1["severity"] == "WARNING").sum() == 1
    assert i[(i["rule_id"] == "VER-002") & (i["hole_id"] == "GV-002")].shape[0] == 1
    assert i[(i["rule_id"] == "VER-003") & (i["hole_id"] == "GV-003")].shape[0] == 1
    v4 = i[i["rule_id"] == "VER-004"]
    assert v4["message_en"].str.contains("re-segmented").any() and v4["message_en"].str.contains("interval removed").any()
    v5 = i[i["rule_id"] == "VER-005"]
    assert v5["message_en"].str.contains("lith_code: 1 codes changed").any()
    assert not res.errors


def test_identical_versions_are_all_unchanged(vcase):
    base, _, _ = vcase
    res = run(ProjectSpec(_inputs(base), project_name="same", baseline_inputs=_inputs(base)))
    s = res.ctx.stats["version"]["summary"]
    assert s["holes"]["changed"] == 0 and s["holes"]["unchanged"] == s["holes"]["current"] and not s["change_classes"]


def test_common_shift_is_a_datum_change(tmp_path):
    base, cur = tmp_path / "b", tmp_path / "c"
    synth.generate(str(base), inject=False)
    shutil.copytree(base, cur)
    c = pd.read_csv(cur / "collar.csv", dtype=str)
    c["North"] = (c["North"].astype(float) + 210.0).map(lambda v: f"{v:.3f}")
    c.to_csv(cur / "collar.csv", index=False)
    res = run(ProjectSpec(_inputs(cur), project_name="shift", baseline_inputs=_inputs(base)))
    w = res.issues[(res.issues["rule_id"] == "VER-002") & (res.issues["severity"] == "WARNING")]
    assert len(w) == 1 and "dy +210.00" in w["message_en"].iloc[0]


def test_snapshot_and_locked_holes(vcase, tmp_path):
    base, _, res_cur = vcase
    res_base = run(ProjectSpec(_inputs(base), project_name="b"))
    m = versions.accept(res_base, str(tmp_path / "snap" / "accepted.json"), "A. Reviewer", "resource 2026", lock=["GV-002", "GV-010", "GV-064"])
    assert m["format"] == versions.SNAPSHOT_FORMAT and len(m["locked_holes"]) == 3
    res = run(ProjectSpec(res_cur.spec.inputs, project_name="v", snapshot_path=str(tmp_path / "snap")))
    v9 = res.issues[res.issues["rule_id"] == "VER-009"]
    crit = v9[v9["severity"] == "CRITICAL"]
    assert set(crit["hole_id"]) == {"GV-002", "GV-064"} and (crit["rule_alias"] == "VER-01").all()
    assert v9["message_en"].str.contains("unlocked holes changed").any()
    same = run(ProjectSpec(_inputs(base), project_name="b", snapshot_path=str(tmp_path / "snap" / "accepted.json")))
    assert same.issues[same.issues["rule_id"] == "VER-009"].empty
