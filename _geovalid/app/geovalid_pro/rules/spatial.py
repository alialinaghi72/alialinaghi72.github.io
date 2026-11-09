"""Spatial checks (v2 brief F11, category H): twin holes and drilling-method bias. SPA-02 hole clash is SUR-016.

  CRS-006  SPA-03  twin candidates: collars closer than `twin_collar_m` with traces within `twin_angle_deg`
           SPA-04  twin comparison: composites matched by downhole depth or by elevation, per element mean difference,
                   relative difference, Wilcoxon signed-rank and QQ data; intercept thickness above the cut-off
  CRS-002  SPA-05  drilling-method bias: composites of different methods paired one-to-one within `pair_dist_m`,
                   mean ratio, relative difference, Wilcoxon signed-rank and QQ data

The statistics are computed here (no GEOQAQC code is used). Compositing is only the pre-step (brief §12).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import rule


def _key_analytes(ctx, n: int = 4) -> list[str]:
    keys = list(ctx.params.get("key_analytes") or [])
    present = []
    for t in ctx.by_kind("assay"):
        for a in t.analytes:
            if not a.partial and a.analyte not in present:
                present.append(a.analyte)
    out = [a for a in keys if a in present] or present
    return out[:n]


def _direction(tr: pd.DataFrame, depth: float) -> np.ndarray | None:
    from ..analysis.desurvey import position_at
    if tr is None or len(tr) < 1:
        return None
    d = min(depth, float(tr["depth_m"].iloc[-1]))
    if d <= 0:
        return None
    p = position_at(tr, [0.0, d])
    v = p[1] - p[0]
    n = np.linalg.norm(v)
    return v / n if n > 0 else None


def twin_pairs(ctx) -> list[dict]:
    """Twin candidates: collars within `twin_collar_m` (3-D) and within `twin_rel_spacing` × the median collar spacing
    (twins are anomalously close for the drill pattern), whose traces point the same way (angle between the
    collar-to-depth vectors over `twin_depth_m` within `twin_angle_deg`)."""
    from scipy.spatial import cKDTree
    p = ctx.p("CRS-006")
    c = ctx.collar_u
    c = c[np.isfinite(c["x"]) & np.isfinite(c["y"])]
    if len(c) < 2:
        return []
    xyz = np.column_stack([c["x"], c["y"], c["z"].fillna(0)]).astype(float)
    tree = cKDTree(xyz)
    # twins are close *relative to the drill spacing*: in a 8 m grade-control grid every neighbour is within 10 m
    nn = tree.query(xyz, k=2)[0][:, 1]
    spacing = float(np.median(nn[np.isfinite(nn) & (nn > 0)])) if (nn > 0).any() else np.inf
    lim = min(float(p.get("twin_collar_m", 10.0)), float(p.get("twin_rel_spacing", 0.5)) * spacing)
    ctx.stats["twin_limit_m"] = lim
    out = []
    for i, j in sorted(tree.query_pairs(lim)):
        a, b = c.index[i], c.index[j]
        va, vb = _direction(ctx.traces.get(a), p.get("twin_depth_m", 100.0)), _direction(ctx.traces.get(b), p.get("twin_depth_m", 100.0))
        if va is None or vb is None:
            continue
        ang = float(np.degrees(np.arccos(np.clip(va @ vb, -1, 1))))
        if ang <= float(p.get("twin_angle_deg", 10.0)):
            out.append({"a": a, "b": b, "collar_dist_m": float(np.linalg.norm(xyz[i] - xyz[j])), "angle_deg": ang,
                        "method_a": c.at[a, "drill_method"] if "drill_method" in c else None,
                        "method_b": c.at[b, "drill_method"] if "drill_method" in c else None})
    return out


@rule("CRS-006", ("collar", "traces"))
def crs_006(ctx):
    """SPA-03 / SPA-04. Twin candidates → INFO each. For each pair with assays: composites (`comp_len_m`) matched by
    downhole depth (`match_by` depth) or by elevation (`match_by` elevation, bins of `comp_len_m`); per key analyte the
    paired statistics. |median relative difference| ≥ `thr_warn_frac` with Wilcoxon p < 0.01 and ≥ `min_pairs` pairs →
    WARNING; intercept thickness above the cut-off differing by more than `thick_tol_frac` → WARNING; otherwise INFO
    with the numbers. The profile maps WARNING to INFO by default (brief: Info)."""
    from ..analysis import categorical as C
    from ..analysis.spatial3d import composites, paired_stats
    p = ctx.p("CRS-006")
    pairs = twin_pairs(ctx)
    ctx.stats["twin_pairs"] = pairs
    if not pairs:
        return
    tname = ctx.collar.name
    for tp in pairs:
        ctx.add("CRS-006", "INFO", tname, f"Twin candidate: {tp['a']} and {tp['b']} (collars {tp['collar_dist_m']:.1f} m apart, traces within {tp['angle_deg']:.1f}°)"
                + (f", drilled by {tp['method_a']} / {tp['method_b']}" if tp.get("method_a") or tp.get("method_b") else "") + ".",
                f"گمانه‌های دوقلوی احتمالی: {tp['a']} و {tp['b']} (فاصلهٔ دهانه {tp['collar_dist_m']:.1f} متر، زاویهٔ مسیر {tp['angle_deg']:.1f} درجه).",
                hole_id=tp["a"], field="twin", value=tp["b"], alias="SPA-03")
    an = _key_analytes(ctx)
    if not an or not ctx.by_kind("assay"):
        return
    L = float(p.get("comp_len_m", 2.0))
    comp = composites(ctx, L, an)
    if comp.empty:
        return
    smp, units, _ = C.sample_table(ctx)
    cuts = {a: C.cutoff_for(smp, a, units.get(a), ctx.params) for a in an} if not smp.empty else {}
    results = {}
    by = {h: g for h, g in comp.groupby("hole_id")}
    for tp in pairs:
        ga, gb = by.get(tp["a"]), by.get(tp["b"])
        if ga is None or gb is None:
            continue
        if p.get("match_by", "depth") == "elevation":
            ka, kb = np.floor(ga["z"] / L).astype("Int64"), np.floor(gb["z"] / L).astype("Int64")
        else:
            ka, kb = np.round(ga["from_m"] / L).astype("Int64"), np.round(gb["from_m"] / L).astype("Int64")
        m = pd.merge(ga.assign(_k=ka.to_numpy()), gb.assign(_k=kb.to_numpy()), on="_k", suffixes=("_a", "_b")).dropna(subset=["_k"])
        if m.empty:
            continue
        for a in an:
            st = paired_stats(m[f"{a}_a"], m[f"{a}_b"])
            results[(tp["a"], tp["b"], a)] = st
            if st.get("n", 0) < int(p.get("min_pairs", 10)):
                ctx.add("CRS-006", "INFO", tname, f"Twins {tp['a']} / {tp['b']}, {a}: only {st.get('n', 0)} matched composites; not compared.",
                        f"دوقلوهای {tp['a']} و {tp['b']}، {a}: تنها {st.get('n', 0)} کامپوزیت هم‌تراز؛ مقایسه نشد.", hole_id=tp["a"], field=a,
                        value=st.get("n", 0), alias="SPA-04")
                continue
            pv = st.get("wilcoxon_p")
            big = abs(st["median_rel_diff"]) >= float(p.get("thr_warn_frac", 0.10)) and pv is not None and pv < 0.01
            txt = (f"Twins {tp['a']} / {tp['b']}, {a}: {st['n']} matched composites ({p.get('match_by', 'depth')}), mean {st['mean_a']:.3g} vs {st['mean_b']:.3g} "
                   f"{units.get(a, '')}, median relative difference {100 * st['median_rel_diff']:+.1f} %" + (f", Wilcoxon p = {pv:.2g}" if pv is not None else "") + ".")
            ctx.add("CRS-006", "WARNING" if big else "INFO", tname, txt,
                    f"دوقلوهای {tp['a']} و {tp['b']}، {a}: {st['n']} کامپوزیت هم‌تراز، اختلاف نسبی میانه {100 * st['median_rel_diff']:+.1f} درصد.",
                    hole_id=tp["a"], field=a, value=round(100 * st["median_rel_diff"], 2), alias="SPA-04")
            cut = cuts.get(a)
            if cut:
                ta = float(((m[f"{a}_a"] >= cut)).sum() * L)
                tb = float(((m[f"{a}_b"] >= cut)).sum() * L)
                if max(ta, tb) >= 3 * L and abs(ta - tb) >= 2 * L and abs(ta - tb) / max(ta, tb) > float(p.get("thick_tol_frac", 0.30)):
                    ctx.add("CRS-006", "WARNING", tname, f"Twins {tp['a']} / {tp['b']}: metres above the {a} cut-off {cut:g} differ ({ta:.0f} m vs {tb:.0f} m over the matched length).",
                            f"دوقلوهای {tp['a']} و {tp['b']}: ضخامت بالای عیار حد {a} متفاوت است ({ta:.0f} و {tb:.0f} متر).",
                            hole_id=tp["a"], field=a, value=f"{ta:.0f}/{tb:.0f} m", alias="SPA-04")
    ctx.stats["twin_results"] = results


@rule("CRS-002", ("assay", "traces", "drill_methods"))
def crs_002(ctx):
    """SPA-05. Composites (`comp_len_m`) of holes drilled by different methods (collar drilling method), paired one to
    one within `pair_dist_m` (3-D, closest first). For each method pair and key analyte: n, means, mean ratio, median
    relative difference, Wilcoxon signed-rank on the log ratio and QQ data. |median relative difference| ≥
    `thr_warn_frac` with p < 0.01 and ≥ `min_pairs` pairs → WARNING; otherwise INFO with the numbers; too few pairs →
    INFO recommending twin holes. The profile maps WARNING to INFO by default (brief: Info)."""
    from ..analysis.spatial3d import composites, greedy_pairs, paired_stats
    p = ctx.p("CRS-002")
    c = ctx.collar_u if ctx.has("collar") else pd.DataFrame()
    if c.empty or "drill_method" not in c or c["drill_method"].dropna().nunique() < 2:
        return
    an = _key_analytes(ctx)
    comp = composites(ctx, float(p.get("comp_len_m", 2.0)), an)
    if comp.empty:
        return
    comp = comp[comp["method"].notna() & np.isfinite(comp["x"])]
    meth = comp["method"].astype(str).str.strip().str.upper()
    groups = sorted(meth.unique())
    results = {}
    tname = ctx.by_kind("assay")[0].name
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            A, B = groups[i], groups[j]
            ca, cb = comp[meth == A], comp[meth == B]
            pr = greedy_pairs(ca[["x", "y", "z"]].to_numpy(float), cb[["x", "y", "z"]].to_numpy(float), float(p.get("pair_dist_m", 10.0)))
            if len(pr) < int(p.get("min_pairs", 30)):
                ctx.add("CRS-002", "INFO", tname, f"{A} vs {B}: {len(pr)} composite pairs within {p.get('pair_dist_m', 10)} m (fewer than {p.get('min_pairs', 30)}): drilling-method bias not testable; twin holes would answer it.",
                        f"{A} در برابر {B}: تنها {len(pr)} جفت کامپوزیت در فاصلهٔ {p.get('pair_dist_m', 10)} متر؛ اریبی روش حفاری قابل آزمون نیست.",
                        field="drill_method", value=len(pr), alias="SPA-05")
                continue
            ia = np.array([q[0] for q in pr])
            ib = np.array([q[1] for q in pr])
            for a in an:
                st = paired_stats(ca[a].to_numpy(float)[ia], cb[a].to_numpy(float)[ib])
                st["pair_dist_median_m"] = float(np.median([q[2] for q in pr]))
                results[(A, B, a)] = st
                if st.get("n", 0) < int(p.get("min_pairs", 30)):
                    continue
                pv = st.get("wilcoxon_p")
                big = abs(st["median_rel_diff"]) >= float(p.get("thr_warn_frac", 0.10)) and pv is not None and pv < 0.01
                ratio = st.get("mean_ratio")
                ctx.add("CRS-002", "WARNING" if big else "INFO", tname,
                        f"{a}, {B} vs {A}: {st['n']} composite pairs (median separation {st['pair_dist_median_m']:.1f} m), mean ratio {ratio:.3f}, "
                        f"median relative difference {100 * st['median_rel_diff']:+.1f} %" + (f", Wilcoxon p = {pv:.2g}" if pv is not None else "") + ".",
                        f"{a}، {B} در برابر {A}: {st['n']} جفت کامپوزیت، نسبت میانگین {ratio:.3f}، اختلاف نسبی میانه {100 * st['median_rel_diff']:+.1f} درصد.",
                        field=a, value=round(100 * st["median_rel_diff"], 2), expected=f"{A}/{B}", alias="SPA-05")
    ctx.stats["drill_bias"] = results
