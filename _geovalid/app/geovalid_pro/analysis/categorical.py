"""Grade versus descriptive logging (brief §9, §11): which logged units, alterations or weathering classes carry grade.

Every original assay sample receives the category logged at its mid-point in each logging table, plus hole-level
attributes (campaign, drilling method). Association between a category field and grade is measured on log10 grade:
  η²  (correlation ratio) = SS_between / SS_total — share of log-grade variance explained by the categories;
  Kruskal–Wallis H, p and ε² = H / (n − 1) — rank-based, robust to outliers;
  Cramér's V between two category fields.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..rules.interval import QC_TYPES

MAX_LEVELS = 40          # coded columns with more distinct values are treated as free text
MIN_GROUP_N = 10         # categories with fewer samples are left out of tests (still counted)

_FIELD_NAMES = {"lith_code": ("Lithology", "سنگ‌شناسی"), "alt_type": ("Alteration", "دگرسانی"),
                "weathering": ("Weathering", "هوازدگی/اکسیداسیون")}


def _assign(samples: pd.DataFrame, table: pd.DataFrame, col: str) -> pd.Series:
    """Category of `table[col]` at each sample mid-point (interval containing the mid-point, per hole)."""
    out = pd.Series(pd.NA, index=samples.index, dtype="object")
    t = table[table["hole_id"].notna() & table["from_m"].notna() & table["to_m"].notna() & table[col].notna()]
    t = t.sort_values(["hole_id", "from_m"])
    groups = {h: g for h, g in t.groupby("hole_id", sort=False)}
    for h, idx in samples.groupby("hole_id").groups.items():
        g = groups.get(h)
        if g is None:
            continue
        mids = samples.loc[idx, "mid_m"].to_numpy(float)
        fr, to = g["from_m"].to_numpy(float), g["to_m"].to_numpy(float)
        k = np.searchsorted(fr, mids, side="right") - 1
        ok = (k >= 0) & (mids < to[np.clip(k, 0, None)])
        vals = g[col].astype(str).to_numpy()
        res = np.full(len(mids), None, dtype=object)
        res[ok] = vals[k[ok]]
        out.loc[idx] = res
    return out


def sample_table(ctx) -> tuple[pd.DataFrame, dict, dict]:
    """Return (samples, analyte units, category fields {column: (label_en, label_fa, group)}).

    group is "logging" (lithology, alteration, weathering codes: candidate estimation domains), "attribute" (other
    coded logging columns such as colour or intensity) or "collar" (campaign, drilling method)."""
    if "categorical" in ctx.stats:
        c = ctx.stats["categorical"]
        return c["samples"], c["units"], c["fields"]
    rows, units = [], {}
    for t in ctx.by_kind("assay"):
        df = t.df
        orig = ~df["qc_class"].isin(QC_TYPES) if "qc_class" in df else pd.Series(True, index=df.index)
        ok = orig & df["hole_id"].notna() & df["from_m"].notna() & df["to_m"].notna() & (df["to_m"] > df["from_m"])
        s = pd.DataFrame({"hole_id": df.loc[ok, "hole_id"], "from_m": df.loc[ok, "from_m"], "to_m": df.loc[ok, "to_m"]})
        for a in t.analytes:
            if a.partial or a.analyte in s:
                continue
            s[a.analyte] = a.parsed.loc[ok, "value_policy"].astype(float)
            units[a.analyte] = a.unit
        rows.append(s)
    if not rows:
        ctx.stats["categorical"] = {"samples": pd.DataFrame(), "units": {}, "fields": {}, "sources": []}
        return pd.DataFrame(), {}, {}
    smp = pd.concat(rows, ignore_index=True)
    smp["length_m"] = smp["to_m"] - smp["from_m"]
    smp["mid_m"] = (smp["from_m"] + smp["to_m"]) / 2
    from .desurvey import position_at
    xyz = np.full((len(smp), 3), np.nan)
    good = set(ctx.spatial_collars()[0].index) if ctx.has("collar") else set()
    no_z = {r["hole_id"] for r in ctx.log.rows if r["rule_id"] == "COL-002"}
    for h, idx in smp.groupby("hole_id").indices.items():
        tr = ctx.traces.get(h)
        if tr is not None and h in good:     # collars with location errors would distort swaths and maps
            xyz[idx] = position_at(tr, smp["mid_m"].to_numpy()[idx])
            if h in no_z:
                xyz[idx, 2] = np.nan
    smp["x"], smp["y"], smp["z"] = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    fields, sources = {}, []
    for t in ctx.tables:
        if not t.is_interval or t.kind in ("assay", "density"):
            continue
        cols = [c for c in ("lith_code", "alt_type", "weathering") if c in t.df and t.df[c].notna().any()]
        for c in cols:
            name = _FIELD_NAMES[c][0]
            if name in smp:
                name = f"{name} ({t.name})"
            smp[name] = _assign(smp, t.df, c)
            fields[name] = (name, _FIELD_NAMES[c][1], "logging")
            sources.append((name, t.df, c))
        for c in t.attrs:
            v = t.df[c].dropna()
            nun = v.nunique()
            numeric = pd.to_numeric(v, errors="coerce").notna().mean() > 0.8 if len(v) else True
            if 2 <= nun <= MAX_LEVELS and not numeric:
                name = f"{t.name}: {c.split(':', 1)[1]}"
                smp[name] = _assign(smp, t.df, c)
                fields[name] = (name, name, "attribute")
                sources.append((name, t.df, c))
    if ctx.collar is not None:
        cu = ctx.collar_u
        for col, en, fa_ in (("campaign", "Campaign", "فاز حفاری"), ("drill_method", "Drill method", "روش حفاری")):
            if col in cu and cu[col].notna().any() and cu[col].nunique() >= 2:
                smp[en] = smp["hole_id"].map(cu[col]).astype("object")
                fields[en] = (en, fa_, "collar")
    ctx.stats["categorical"] = {"samples": smp, "units": units, "fields": fields, "sources": sources}
    return smp, units, fields


def attach(ctx, df: pd.DataFrame) -> pd.DataFrame:
    """Add the logged categories (at each interval mid-point) to any table with hole_id/from_m/to_m."""
    sample_table(ctx)
    out = df.copy()
    out["mid_m"] = (out["from_m"] + out["to_m"]) / 2
    for name, src, col in ctx.stats["categorical"].get("sources", []):
        out[name] = _assign(out, src, col)
    return out


def physical_table(ctx) -> pd.DataFrame:
    """Core recovery, RQD and density with logged categories attached (long format: variable, value)."""
    from ..rules.logging_rules import _cr_rqd
    parts = []
    for t in ctx.by_kind("geotech"):
        df, cr, rqd, cr_c, rqd_c = _cr_rqd(t)
        base = df[["hole_id", "from_m", "to_m"]]
        for var, v in (("CR %", cr_c.where(cr_c.notna(), cr)), ("RQD %", rqd_c.where(rqd_c.notna(), rqd))):
            if v.notna().any():
                parts.append(base.assign(variable=var, value=v.clip(0, 100)))
    for t in ctx.by_kind("density"):
        df = t.df
        if "from_m" in df and "to_m" in df and "density" in df:
            v = pd.to_numeric(df["density"], errors="coerce")
            parts.append(df[["hole_id", "from_m", "to_m"]].assign(variable="Density g/cm³", value=v.where((v > 1) & (v < 6.5))))
    if not parts:
        return pd.DataFrame()
    d = pd.concat(parts, ignore_index=True).dropna(subset=["hole_id", "from_m", "to_m", "value"])
    return attach(ctx, d)


def grade_length(smp: pd.DataFrame, analyte: str, n: int = 40) -> pd.DataFrame:
    """Metres and length-weighted grade above a range of cut-offs (grade–tonnage analogue on sample length)."""
    d = smp[[analyte, "length_m"]].dropna()
    d = d[d[analyte] > 0]
    if len(d) < 30:
        return pd.DataFrame()
    cuts = np.logspace(np.log10(d[analyte].quantile(0.05)), np.log10(d[analyte].quantile(0.995)), n)
    v, w = d[analyte].to_numpy(), d["length_m"].to_numpy()
    rows = []
    for c in cuts:
        m = v >= c
        rows.append({"cutoff": c, "metres": float(w[m].sum()), "grade": float((v[m] * w[m]).sum() / w[m].sum()) if m.any() else np.nan,
                     "metal": float((v[m] * w[m]).sum())})
    out = pd.DataFrame(rows)
    out["metal_pct"] = 100 * out["metal"] / float((v * w).sum())
    return out


def category_order(smp: pd.DataFrame, field: str) -> list:
    """Categories by logged metres (descending): the order used for stable colours."""
    d = smp[[field, "length_m"]].dropna()
    return list(d.groupby(field)["length_m"].sum().sort_values(ascending=False).index)


def _log(v: pd.Series) -> pd.Series:
    v = v[(v > 0) & np.isfinite(v)]
    return np.log10(v)


def association(smp: pd.DataFrame, fields, analytes, min_n: int = MIN_GROUP_N) -> pd.DataFrame:
    from scipy.stats import kruskal
    out = []
    for f in fields:
        for a in analytes:
            d = smp[[f, a]].dropna()
            d = d[d[a] > 0]
            counts = d[f].value_counts()
            keep = counts[counts >= min_n].index
            d = d[d[f].isin(keep)]
            if d[f].nunique() < 2 or len(d) < 3 * min_n:
                continue
            y = np.log10(d[a].to_numpy(float))
            gm = d.assign(y=y).groupby(f)["y"]
            ss_b = float((gm.count() * (gm.mean() - y.mean()) ** 2).sum())
            ss_t = float(((y - y.mean()) ** 2).sum())
            eta2 = ss_b / ss_t if ss_t > 0 else np.nan
            H, p = kruskal(*[g.to_numpy() for _, g in gm])
            med = d.groupby(f)[a].median().sort_values(ascending=False)
            out.append({"field": f, "analyte": a, "n": len(d), "groups": int(d[f].nunique()), "eta2": eta2,
                        "kw_H": float(H), "kw_p": float(p), "epsilon2": float(H / (len(d) - 1)),
                        "top_category": med.index[0], "top_median": float(med.iloc[0]),
                        "low_category": med.index[-1], "low_median": float(med.iloc[-1])})
    return pd.DataFrame(out)


def category_stats(smp: pd.DataFrame, field: str, analyte: str, cutoff: float | None = None) -> pd.DataFrame:
    d = smp[[field, analyte, "length_m"]].dropna()
    rows = []
    for c, g in d.groupby(field):
        v, w = g[analyte], g["length_m"].clip(lower=0)
        row = {"category": c, "n": len(g), "metres": round(float(w.sum()), 1),
               "mean_lw": float((v * w).sum() / w.sum()) if w.sum() > 0 else np.nan, "median": float(v.median()),
               "p10": float(v.quantile(.1)), "p90": float(v.quantile(.9)), "max": float(v.max()),
               "cv": float(v.std() / v.mean()) if v.mean() > 0 else np.nan}
        if cutoff is not None:
            row["pct_above_cutoff"] = round(100 * float((v >= cutoff).mean()), 1)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("median", ascending=False).reset_index(drop=True)


def cramers_v(smp: pd.DataFrame, a: str, b: str) -> float:
    from scipy.stats import chi2_contingency
    tab = pd.crosstab(smp[a], smp[b])
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return np.nan
    chi2 = chi2_contingency(tab, correction=False)[0]
    n = tab.to_numpy().sum()
    return float(np.sqrt(chi2 / (n * (min(tab.shape) - 1))))


def two_way(smp: pd.DataFrame, a: str, b: str, analyte: str, min_n: int = 5):
    d = smp[[a, b, analyte]].dropna()
    med = d.pivot_table(index=a, columns=b, values=analyte, aggfunc="median")
    cnt = d.pivot_table(index=a, columns=b, values=analyte, aggfunc="count")
    med = med.where(cnt >= min_n)
    order_r = med.median(axis=1).sort_values(ascending=False).index
    order_c = med.median(axis=0).sort_values(ascending=False).index
    return med.loc[order_r, order_c], cnt.loc[order_r, order_c]


def contact_profile(smp: pd.DataFrame, field: str, unit: str, analyte: str, max_dist: float = 30.0, step: float = 2.0):
    """Mean grade against signed distance to the nearest boundary of `unit` (positive inside the unit)."""
    rows = []
    for h, g in smp.groupby("hole_id"):
        g = g.sort_values("mid_m")
        inside = (g[field] == unit).to_numpy()
        if not inside.any() or inside.all():
            continue
        mids = g["mid_m"].to_numpy(float)
        change = np.where(inside[1:] != inside[:-1])[0]
        bounds = (mids[change] + mids[change + 1]) / 2
        d = np.min(np.abs(mids[:, None] - bounds[None, :]), axis=1)
        signed = np.where(inside, d, -d)
        rows.append(pd.DataFrame({"dist": signed, "v": g[analyte].to_numpy(float)}))
    if not rows:
        return pd.DataFrame()
    d = pd.concat(rows)
    d = d[(d["dist"].abs() <= max_dist) & (d["v"] > 0)]
    if d.empty:
        return pd.DataFrame()
    d["bin"] = (np.floor(d["dist"] / step) + 0.5) * step
    agg = d.groupby("bin")["v"].agg(["mean", "median", "count", lambda x: np.exp(np.log(x).mean())])
    agg.columns = ["mean", "median", "n", "geomean"]
    return agg.reset_index()


def swath(smp: pd.DataFrame, analyte: str, axis: str, n_bins: int = 18) -> pd.DataFrame:
    d = smp[[axis, analyte, "length_m"]].dropna()
    if len(d) < 20:
        return pd.DataFrame()
    edges = np.linspace(d[axis].min(), d[axis].max(), n_bins + 1)
    d["bin"] = pd.cut(d[axis], edges, include_lowest=True)
    g = d.groupby("bin", observed=True)
    out = pd.DataFrame({"centre": [iv.mid for iv in g.groups.keys()],
                        "mean_lw": g.apply(lambda x: (x[analyte] * x["length_m"]).sum() / x["length_m"].sum(), include_groups=False).to_numpy(),
                        "median": g[analyte].median().to_numpy(), "n": g.size().to_numpy()})
    return out


def depth_proportions(smp: pd.DataFrame, field: str, step: float = 20.0, top: int = 8) -> pd.DataFrame:
    d = smp[[field, "mid_m", "length_m"]].dropna()
    if d.empty:
        return pd.DataFrame()
    keep = d.groupby(field)["length_m"].sum().sort_values(ascending=False).index[:top]
    d[field] = d[field].where(d[field].isin(keep), "other")
    d["bin"] = (np.floor(d["mid_m"] / step) + 0.5) * step
    p = d.pivot_table(index="bin", columns=field, values="length_m", aggfunc="sum").fillna(0)
    return p.div(p.sum(axis=1), axis=0)


def hole_grades(smp: pd.DataFrame, ctx, analyte: str, cutoff: float | None) -> pd.DataFrame:
    rows = []
    cu = ctx.spatial_collars()[0]
    for h, g in smp[["hole_id", analyte, "length_m"]].dropna().groupby("hole_id"):
        if h not in cu.index:
            continue
        w = g["length_m"].clip(lower=0)
        above = g[g[analyte] >= cutoff] if cutoff is not None else g
        rows.append({"hole_id": h, "x": cu.at[h, "x"], "y": cu.at[h, "y"],
                     "mean_lw": float((g[analyte] * w).sum() / w.sum()) if w.sum() > 0 else np.nan,
                     "max": float(g[analyte].max()),
                     "gt": float((above[analyte] * above["length_m"]).sum()),
                     "metres_above": float(above["length_m"].sum())})
    return pd.DataFrame(rows)


def key_analytes(units: dict, params: dict, n: int = 3) -> list[str]:
    keys = [a for a in params.get("key_analytes", []) if a in units]
    return keys[:n] if keys else list(units)[:n]


def default_cutoff(smp: pd.DataFrame, analyte: str) -> float | None:
    v = smp[analyte].dropna()
    v = v[v > 0]
    return float(v.quantile(0.75)) if len(v) else None


def cutoff_for(smp: pd.DataFrame, analyte: str, unit: str, params: dict) -> float | None:
    """Profile cut-off converted to the column unit; P75 of the data when the profile has none."""
    from .assay import TO_PPM
    c = (params.get("analysis_cutoffs") or {}).get(analyte)
    if c:
        value, cu = float(c[0]), str(c[1])
        if cu == unit:
            return value
        if cu in TO_PPM and unit in TO_PPM:
            return value * TO_PPM[cu] / TO_PPM[unit]
    return default_cutoff(smp, analyte)


def primary_analytes(assoc: pd.DataFrame, units: dict, params: dict, n: int = 2) -> list[str]:
    """Key analytes ordered by how strongly logged geology controls them (largest η²)."""
    keys = [a for a in params.get("key_analytes", []) if a in units] or list(units)
    if assoc is None or assoc.empty:
        return keys[:n]
    best = assoc[assoc["analyte"].isin(keys)].groupby("analyte")["eta2"].max().sort_values(ascending=False)
    order = list(best.index) + [k for k in keys if k not in best.index]
    return order[:n]


def narrative(assoc: pd.DataFrame, fields: dict, units: dict, analyte: str, lang: str) -> list[str]:
    """Plain-language findings on grade versus logged attributes, strongest first."""
    out = []
    if assoc is None or assoc.empty:
        return out
    a = assoc[assoc["analyte"] == analyte].sort_values("eta2", ascending=False)
    fa = lang == "fa"
    u = units.get(analyte, "")
    for r in a.itertuples():
        en_f, fa_f, group = fields.get(r.field, (r.field, r.field, "attribute"))
        ratio = r.top_median / r.low_median if r.low_median > 0 else np.nan
        strength = ("قوی" if r.eta2 >= 0.3 else "متوسط" if r.eta2 >= 0.1 else "ضعیف") if fa else \
                   ("strong" if r.eta2 >= 0.3 else "moderate" if r.eta2 >= 0.1 else "weak")
        if r.eta2 < 0.02:
            continue
        if fa:
            s = (f"{fa_f}: کنترل {strength} بر عیار {analyte} (η² = {r.eta2:.2f}، یعنی {r.eta2:.0%} از واریانس لگاریتم عیار)؛ "
                 f"بیشترین میانه در {r.top_category} ({r.top_median:.3g} {u}) و کمترین در {r.low_category} ({r.low_median:.3g} {u})"
                 + (f"، حدود {ratio:,.0f} برابر." if np.isfinite(ratio) and ratio >= 2 else "."))
            if group == "collar":
                s += " این ارتباط احتمالاً از تفاوت مکان حفاری فازها ناشی است، نه علت‌ومعلولی؛ با آزمون‌های جفت‌شدهٔ مکانی (CRS-007) بررسی شود."
        else:
            s = (f"{en_f}: {strength} control on {analyte} (η² = {r.eta2:.2f}, i.e. {r.eta2:.0%} of log-grade variance); "
                 f"highest median in {r.top_category} ({r.top_median:.3g} {u}), lowest in {r.low_category} ({r.low_median:.3g} {u})"
                 + (f", about {ratio:,.0f}×." if np.isfinite(ratio) and ratio >= 2 else "."))
            if group == "collar":
                s += " This is probably because the campaigns drilled different parts of the deposit, not a cause; check with spatially paired tests (CRS-007)."
        out.append(s)
    return out
