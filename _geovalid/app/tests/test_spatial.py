"""Phase 3 F11: hole clash (SPA-02, exact segment distance), twin candidates and comparison (SPA-03/04) and
drilling-method bias (SPA-05) on a small built project with one case of each and a negative twin."""
import numpy as np
import pandas as pd
import pytest

from geovalid_pro.analysis.spatial3d import composite_hole, paired_stats, seg_seg_distance
from geovalid_pro.engine import ProjectSpec, load_inputs, load_params, run


def grade(x, y, z):
    return 0.3 + 0.2 * np.sin(x / 40.0) + 0.15 * np.cos(y / 35.0) + 0.002 * (1000 - z)


def build(d, bias=1.15, twin_factor=1.5, clash=True):
    rng = np.random.default_rng(4)
    rows, surv, ass = [], [], []
    k = 0
    for i in range(8):                      # RC and DD holes on alternating rows, 6 m apart: composites can pair
        for j in range(8):
            h = f"P{k:03d}"
            k += 1
            x, y = 1000 + 12.0 * j + (6.0 if i % 2 else 0.0), 2000 + 6.0 * i
            m = "RC" if i % 2 else "DD"
            rows.append((h, x, y, 1000.0, 60.0, m))
            surv.append((h, 0.0, 0.0, -90.0))
            for f in np.arange(0, 60, 1.0):
                g = grade(x, y, 1000 - f - 0.5) * (bias if m == "RC" else 1.0) * np.exp(rng.normal(0, 0.05))
                ass.append((h, f, f + 1, f"{h}-{int(f)}", round(g, 4)))
    # twins: T1 (DD) and T2 (DD) 3 m apart, parallel; T2 reports 1.5 x the grade
    for h, x, fac in (("T1", 1300.0, 1.0), ("T2", 1303.0, twin_factor)):
        rows.append((h, x, 2300.0, 1000.0, 60.0, "DD"))
        surv.append((h, 0.0, 0.0, -90.0))
        for f in np.arange(0, 60, 1.0):
            ass.append((h, f, f + 1, f"{h}-{int(f)}", round(grade(1300, 2300, 1000 - f) * fac * np.exp(rng.normal(0, 0.03)), 4)))
    # clash: C1 vertical; C2 inclined, crossing C1's trace within 0.5 m at about 40 m depth. C3 passes 3 m away (negative)
    rows += [("C1", 1600.0, 2600.0, 1000.0, 80.0, "DD"), ("C2", 1640.4, 2600.0, 1000.0, 90.0, "DD"), ("C3", 1640.0, 2700.0, 1000.0, 90.0, "DD")]
    surv += [("C1", 0.0, 0.0, -90.0), ("C2", 0.0, 270.0 if clash else 90.0, -45.0), ("C3", 0.0, 270.0, -45.0)]
    rows.append(("C4", 1600.0, 2703.0, 1000.0, 80.0, "DD"))
    surv.append(("C4", 0.0, 0.0, -90.0))
    pd.DataFrame(rows, columns=["HoleID", "East", "North", "RL", "Depth", "DrillType"]).to_csv(d / "collar.csv", index=False)
    pd.DataFrame(surv, columns=["HoleID", "Depth", "Azimuth", "Dip"]).to_csv(d / "survey.csv", index=False)
    pd.DataFrame(ass, columns=["HoleID", "From", "To", "SampleID", "Cu_pct"]).to_csv(d / "assay.csv", index=False)


def _run(d, overrides=None, **kw):
    params = load_params(None)
    params["analysis_cutoffs"] = {"Cu": [0.5, "%"]}
    if overrides is not None:
        params["severity_overrides"] = overrides
    ins = [i for i in load_inputs(sorted(str(p) for p in d.glob("*.csv"))) if i.kind != "ignore"]
    return run(ProjectSpec(ins, project_name="spa", params=params))


@pytest.fixture(scope="module")
def spa(tmp_path_factory):
    d = tmp_path_factory.mktemp("spa")
    build(d)
    return _run(d, overrides={})


def _iss(res, rule):
    return res.issues[res.issues["rule_id"] == rule]


def test_segment_distance_geometry():
    d, s, t = seg_seg_distance([[0, 0, 0]], [[10, 0, 0]], [[5, -5, 3]], [[5, 5, 3]])
    assert d[0] == pytest.approx(3.0) and s[0] == pytest.approx(0.5) and t[0] == pytest.approx(0.5)
    d, *_ = seg_seg_distance([[0, 0, 0]], [[10, 0, 0]], [[12, 0, 1]], [[20, 0, 1]])
    assert d[0] == pytest.approx(np.sqrt(5))


def test_compositing_is_length_weighted():
    c = composite_hole(np.array([0, 1, 3]), np.array([1, 3, 4]), np.array([1.0, 2.0, 4.0]), 2.0)
    assert c.iloc[0, 2] == pytest.approx((1 * 1 + 1 * 2) / 2) and c.iloc[1, 2] == pytest.approx((1 * 2 + 1 * 4) / 2)


def test_clash_exact_distance(spa):
    i = _iss(spa, "SUR-016")
    clash = i[i["rule_alias"] == "SPA-02"]
    assert len(clash) == 1 and set(clash["hole_id"]) <= {"C1", "C2"} and "C3" not in " ".join(clash["message_en"])
    dist = float(clash["message_en"].str.extract(r"within ([\d.]+) m")[0].iloc[0])
    assert dist < 1.0


def test_twin_candidates_and_comparison(spa):
    i = _iss(spa, "CRS-006")
    cand = i[i["rule_alias"] == "SPA-03"]
    assert any(("T1" in m and "T2" in m) for m in cand["message_en"])
    assert not any("C3" in m and "C4" in m for m in cand["message_en"])      # 3 m apart but not parallel
    comp = i[(i["rule_alias"] == "SPA-04") & (i["severity"] == "WARNING")]
    assert comp["message_en"].str.contains("Twins T1 / T2, Cu").any()
    st = spa.ctx.stats["twin_results"][("T1", "T2", "Cu")]
    assert st["n"] >= 25 and st["mean_ratio"] == pytest.approx(1.5, rel=0.05) and len(st["qq"][0]) > 5


def test_drill_type_bias(spa):
    i = _iss(spa, "CRS-002")
    w = i[i["severity"] == "WARNING"]
    assert len(w) == 1 and "RC vs DD" in w["message_en"].iloc[0]
    st = spa.ctx.stats["drill_bias"][("DD", "RC", "Cu")]
    assert st["mean_ratio"] == pytest.approx(1.15, abs=0.04) and st["wilcoxon_p"] < 1e-6


def test_brief_default_severity_is_info(tmp_path):
    build(tmp_path)
    res = _run(tmp_path)
    for r in ("CRS-002", "CRS-006"):
        assert set(_iss(res, r)["severity"]) == {"INFO"}, r


def test_negative_twin_no_bias(tmp_path):
    build(tmp_path, bias=1.0, twin_factor=1.0, clash=False)
    res = _run(tmp_path, overrides={})
    assert _iss(res, "CRS-002").query("severity == 'WARNING'").empty
    assert _iss(res, "CRS-006").query("severity == 'WARNING'").empty
    assert _iss(res, "SUR-016").query("rule_alias == 'SPA-02'").empty


def test_bias_not_applicable_with_one_method(tmp_path):
    build(tmp_path)
    c = pd.read_csv(tmp_path / "collar.csv")
    c["DrillType"] = "DD"
    c.to_csv(tmp_path / "collar.csv", index=False)
    res = _run(tmp_path)
    assert res.matrix.set_index("rule_id").loc["CRS-002", "status"] == "NOT_APPLICABLE"


def test_paired_stats_identity():
    a = np.linspace(1, 2, 40)
    st = paired_stats(a, a * 1.0)
    assert st["mean_ratio"] == pytest.approx(1.0) and st["median_rel_diff"] == pytest.approx(0.0)
