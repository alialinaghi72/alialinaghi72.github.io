"""Outputs: issue log (XLSX + CSV), flagged copies of every input table, traces, run metadata, profile used."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .. import __version__
from ..core.issues import SEV_LETTER, SEV_RANK


def summaries(res) -> dict[str, pd.DataFrame]:
    iss = res.issues
    out = {}
    if iss.empty:
        empty = pd.DataFrame(columns=["count"])
        return {"by_rule": empty, "by_table": empty, "by_hole": empty, "by_severity": empty}
    sev_order = ["CRITICAL", "ERROR", "WARNING", "INFO"]
    out["by_severity"] = iss["severity"].value_counts().reindex(sev_order, fill_value=0).rename("count").to_frame()
    br = iss.groupby(["rule_id", "severity"]).size().unstack(fill_value=0).reindex(columns=sev_order, fill_value=0)
    br["total"] = br.sum(axis=1)
    m = res.matrix.set_index("rule_id")
    br.insert(0, "title_en", m["title_en"].reindex(br.index))
    br.insert(1, "title_fa", m["title_fa"].reindex(br.index))
    out["by_rule"] = br.sort_values(sev_order, ascending=False)
    bt = iss.groupby(["table", "severity"]).size().unstack(fill_value=0).reindex(columns=sev_order, fill_value=0)
    out["by_table"] = bt
    bh = iss[iss["hole_id"].notna()].groupby(["hole_id", "severity"]).size().unstack(fill_value=0).reindex(columns=sev_order, fill_value=0)
    bh["total"] = bh.sum(axis=1)
    out["by_hole"] = bh.sort_values(sev_order, ascending=False)
    return out


def inventory(res) -> pd.DataFrame:
    ctx = res.ctx
    rows = []
    for t in ([ctx.collar] if ctx.collar else []) + ([ctx.survey] if ctx.survey else []) + ctx.tables:
        df = t.df
        metres = float((df["to_m"] - df["from_m"]).clip(lower=0).sum()) if "to_m" in df and "from_m" in df else np.nan
        rows.append({"table": t.name, "kind": t.kind, "source": Path(t.source).name, "rows": len(df),
                     "holes": int(df["hole_id"].nunique()) if "hole_id" in df else 0,
                     "metres": round(metres, 1) if np.isfinite(metres) else None, "analytes": len(t.analytes)})
    return pd.DataFrame(rows)


def assay_stats(res) -> pd.DataFrame:
    from ..rules.interval import QC_TYPES
    rows = []
    for t in res.ctx.tables:
        m = ~t.df["qc_class"].isin(QC_TYPES) if "qc_class" in t.df else pd.Series(True, index=t.df.index)
        L = (t.df["to_m"] - t.df["from_m"]) if "to_m" in t.df else pd.Series(1.0, index=t.df.index)
        for a in t.analytes:
            p = a.parsed[m]
            v = p["value_policy"].dropna()
            rep = p["flag"].isin(["VAL", "BDL", "ODL"]).sum()
            if len(v) == 0:
                continue
            w = L.reindex(v.index).clip(lower=0).fillna(0)
            wmean = float((v * w).sum() / w.sum()) if w.sum() > 0 else np.nan
            rows.append({"table": t.name, "column": a.column, "analyte": a.analyte, "unit": a.unit,
                         "unit_source": "declared" if a.unit_declared else "inferred", "n": int(rep),
                         "n_missing": int((p["flag"] == "NA").sum()), "n_bdl": int((p["flag"] == "BDL").sum()),
                         "pct_bdl": round(100 * (p["flag"] == "BDL").sum() / max(rep, 1), 1),
                         "min": v.min(), "p25": v.quantile(.25), "median": v.median(), "mean": v.mean(), "mean_lw": wmean,
                         "p75": v.quantile(.75), "p95": v.quantile(.95), "p99": v.quantile(.99), "max": v.max(),
                         "sd": v.std(), "cv": v.std() / v.mean() if v.mean() > 0 else np.nan,
                         "geomean": float(np.exp(np.log(v[v > 0]).mean())) if (v > 0).any() else np.nan,
                         "skew": v.skew(), "kurtosis": v.kurt()})
    return pd.DataFrame(rows)


def flagged_table(res, inp) -> pd.DataFrame:
    df = inp.raw.df.copy()
    iss = res.issues
    iss = iss[iss["table"].fillna("").str.split("+").apply(lambda xs: inp.name in xs)]
    flag = pd.Series("", index=df.index, dtype=object)
    rank = pd.Series(9, index=df.index)
    comment = pd.Series("", index=df.index, dtype=object)
    hole_col = inp.mapping.fields.get("hole_id")
    for _, r in iss.iterrows():
        if pd.notna(r["src_row"]):
            idx = [int(r["src_row"]) - 2]
        elif pd.notna(r["hole_id"]) and hole_col:
            idx = df.index[df[hole_col].astype("string").str.strip() == str(r["hole_id"])].tolist()
        else:
            continue
        sr = SEV_RANK[r["severity"]]
        for i in idx:
            if i not in df.index:
                continue
            if sr < rank[i]:
                rank[i], flag[i] = sr, SEV_LETTER[r["severity"]]
            if r["rule_id"] not in comment[i]:
                comment[i] = (comment[i] + "; " if comment[i] else "") + r["rule_id"]
    df["QC_FLAG"], df["QC_COMMENT"] = flag, comment
    return df


def write_outputs(res, out_dir: str, lang: str = "fa", progress=None) -> dict:
    from ..report.html import build_report
    progress = progress or (lambda pct, msg: None)
    out = Path(out_dir)
    stamp = res.started.replace(":", "").replace("-", "")[:15]
    run_dir = out / f"GEOVALID_{stamp}"
    (run_dir / "flagged_tables").mkdir(parents=True, exist_ok=True)
    files = {}
    iss = res.issues
    sm = summaries(res)
    inv = inventory(res)
    ast = assay_stats(res)
    res.ctx.stats["inventory"], res.ctx.stats["assay_stats"] = inv, ast
    iss.to_csv(run_dir / "issues.csv", index=False, encoding="utf-8-sig")
    files["issues_csv"] = run_dir / "issues.csv"
    xlsx = run_dir / "issue_log.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
        iss.to_excel(xw, sheet_name="Issues", index=False)
        sm["by_rule"].to_excel(xw, sheet_name="By_rule")
        sm["by_table"].to_excel(xw, sheet_name="By_table")
        sm["by_hole"].to_excel(xw, sheet_name="By_hole")
        res.matrix.to_excel(xw, sheet_name="Rule_matrix", index=False)
        inv.to_excel(xw, sheet_name="Inventory", index=False)
        if not ast.empty:
            ast.to_excel(xw, sheet_name="Assay_stats", index=False)
        cm = res.ctx.stats.get("collar_method")
        if cm is not None:
            cm.to_excel(xw, sheet_name="Collar_method", index=False)
        if "dz" in res.ctx.stats:
            pd.DataFrame({"hole_id": res.ctx.collar_u.index, "z": res.ctx.collar_u["z"].to_numpy(),
                          "z_topo": res.ctx.stats["z_topo"].to_numpy(), "dz": res.ctx.stats["dz"].to_numpy()}).to_excel(xw, sheet_name="Collar_vs_DEM", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for col in ws.columns:
                width = min(60, max(10, max(len(str(c.value or "")) for c in col[:200]) + 2))
                ws.column_dimensions[col[0].column_letter].width = width
    files["issue_log_xlsx"] = xlsx
    progress(97, "writing flagged tables")
    for inp in res.spec.inputs:
        if inp.enabled and inp.kind != "ignore":
            safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in inp.name)
            flagged_table(res, inp).to_csv(run_dir / "flagged_tables" / f"{safe}_QC.csv", index=False, encoding="utf-8-sig")
    if res.ctx.traces:
        tr = pd.concat([t.assign(hole_id=h) for h, t in res.ctx.traces.items()], ignore_index=True)
        tr[["hole_id", "depth_m", "x", "y", "z", "azimuth", "dip", "dogleg_deg"]].round(3).to_csv(run_dir / "desurveyed_traces.csv", index=False, encoding="utf-8-sig")
    (run_dir / "profile_used.yaml").write_text(yaml.safe_dump(res.ctx.params, allow_unicode=True, sort_keys=False), encoding="utf-8")
    meta = {"software": "GEOVALID PRO", "version": __version__, "run_id": res.run_id, "started": res.started, "finished": res.finished,
            "inputs": [{"name": i.name, "file": i.raw.source, "sheet": i.raw.sheet, "sha256": i.raw.sha256, "kind": i.kind,
                        "enabled": i.enabled, "encoding": i.raw.encoding, "mapping": i.mapping.fields,
                        "analytes": [{"column": a.column, "analyte": a.analyte, "unit": a.unit} for a in i.mapping.analytes]}
                       for i in res.spec.inputs],
            "spatial": {k: {"file": v, "sha256": sha} for k, v, sha in
                        [(k, v, _sha(v)) for k, v in (("dem", res.spec.dem_path), ("licence", res.spec.licence_path), ("crm", res.spec.crm_path)) if v]},
            "dip_convention": res.ctx.dip_convention, "issue_counts": res.issues["severity"].value_counts().to_dict() if not res.issues.empty else {},
            "errors": res.errors}
    (run_dir / "run_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    progress(98, "writing report")
    for lg in ([lang] if lang in ("fa", "en") else ["fa", "en"]):
        path = run_dir / f"report_{lg}.html"
        path.write_text(build_report(res, lg, sm, inv, ast), encoding="utf-8")
        files[f"report_{lg}"] = path
    files["folder"] = run_dir
    res.outputs = files
    return files


def _sha(path):
    from .readers import sha256_of
    try:
        return sha256_of(path)
    except OSError:
        return None
