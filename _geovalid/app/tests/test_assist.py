"""Phase 3 F12: optional anomaly assist (off by default): code-mapping suggestions (IMP-021) and the robust
compositional anomaly score (ASY-031)."""
import numpy as np
import pandas as pd
import pytest

from geovalid_pro.engine import ProjectSpec, load_inputs, load_params, run
from geovalid_pro.rules.assist import code_suggestions, mcd


def test_code_suggestions_are_explainable():
    s = code_suggestions("Quartz Monzonite Porphyry", ["QMP", "AND", "DIO"])
    assert s[0][0] == "QMP" and s[0][2] == "initials"
    s = code_suggestions("andesite", ["AND", "ANDESITE", "DIO"])
    assert s[0][0] == "ANDESITE" and s[0][1] == pytest.approx(1.0)
    s = code_suggestions("DIOR", ["AND", "DIO"])
    assert s[0][0] == "DIO" and s[0][2] in ("prefix", "characters")


def test_mcd_resists_outliers():
    rng = np.random.default_rng(1)
    X = rng.normal(0, 1, (400, 3))
    X[:40] += 12
    mu, S = mcd(X)
    assert np.all(np.abs(mu) < 0.3) and np.all(np.diag(S) < 1.6)


def _project(d, n=300, outliers=(17, 123)):
    rng = np.random.default_rng(3)
    holes = [f"A{i:02d}" for i in range(6)]
    pd.DataFrame({"HoleID": holes, "East": 1000 + 50.0 * np.arange(6), "North": 2000.0, "RL": 500.0, "Depth": 60.0}).to_csv(d / "collar.csv", index=False)
    rows = []
    for k in range(n):
        h = holes[k % 6]
        f = float((k // 6) * 1.0)
        cu = np.exp(rng.normal(-1.5, 0.4))
        fe = cu * 8 * np.exp(rng.normal(0, 0.1))
        s = cu * 1.1 * np.exp(rng.normal(0, 0.1))
        zn = np.exp(rng.normal(-3, 0.2)) * 100
        mo = np.exp(rng.normal(3, 0.2))
        if k in outliers:                                       # copper-rich but sulphur-poor and zinc-rich: unusual mix
            s, zn = s / 20, zn * 30
        rows.append((h, f, f + 1, round(cu, 4), round(fe, 3), round(s, 4), round(zn, 2), round(mo, 2)))
    pd.DataFrame(rows, columns=["HoleID", "From", "To", "Cu_pct", "Fe_pct", "S_pct", "Zn_ppm", "Mo_ppm"]).to_csv(d / "assay.csv", index=False)
    pd.DataFrame({"HoleID": holes * 2, "From": [0.0] * 6 + [30.0] * 6, "To": [30.0] * 6 + [60.0] * 6,
                  "Lith": ["Quartz Monzonite Porphyry"] * 3 + ["AND"] * 3 + ["andesite"] * 3 + ["DIO"] * 3}).to_csv(d / "lithology.csv", index=False)


def _run(d, enabled):
    params = load_params(None)
    params["anomaly_assist"]["enabled"] = enabled
    params["code_dictionaries"] = {"lith_code": ["QMP", "AND", "DIO", "ANDESITE"]}
    ins = [i for i in load_inputs(sorted(str(p) for p in d.glob("*.csv"))) if i.kind != "ignore"]
    return run(ProjectSpec(ins, project_name="assist", params=params))


def test_off_by_default(tmp_path):
    _project(tmp_path)
    res = _run(tmp_path, False)
    m = res.matrix.set_index("rule_id")
    assert m.loc["IMP-021", "status"] == "NOT_APPLICABLE" and m.loc["ASY-031", "status"] == "NOT_APPLICABLE"
    assert load_params(None)["anomaly_assist"]["enabled"] is False


def test_assist_on(tmp_path):
    _project(tmp_path)
    res = _run(tmp_path, True)
    i = res.issues
    imp = i[i["rule_id"] == "IMP-021"]
    assert (imp["severity"] == "INFO").all()
    assert imp.loc[imp["value"] == "Quartz Monzonite Porphyry", "expected"].iloc[0] == "QMP"
    asy = i[(i["rule_id"] == "ASY-031") & i["src_row"].notna()]
    assert (asy["severity"] == "INFO").all()
    rows = set(asy["src_row"].astype(int))
    assert {17 + 2, 123 + 2} <= rows and len(rows) <= 8
    msg = asy.loc[asy["src_row"] == 19, "message_en"].iloc[0]
    assert "S low" in msg and "Zn high" in msg
