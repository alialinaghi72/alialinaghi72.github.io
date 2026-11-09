"""3-D helpers for the spatial checks (v2 brief F11): segment–segment distance, compositing and composite positions.

Compositing is used only as the pre-step of the drill-type bias and twin comparisons (brief §12 allows nothing more).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def seg_seg_distance(p0, p1, q0, q1):
    """Minimum distance between segments [p0, p1] and [q0, q1] (arrays (n, 3)), vectorised. Returns (d, s, t), with s and
    t the parameters (0…1) of the closest points on each segment (Ericson, Real-Time Collision Detection §5.1.9)."""
    p0, p1, q0, q1 = (np.atleast_2d(np.asarray(a, float)) for a in (p0, p1, q0, q1))
    d1, d2, r = p1 - p0, q1 - q0, p0 - q0
    a = np.einsum("ij,ij->i", d1, d1)
    e = np.einsum("ij,ij->i", d2, d2)
    f = np.einsum("ij,ij->i", d2, r)
    c = np.einsum("ij,ij->i", d1, r)
    b = np.einsum("ij,ij->i", d1, d2)
    eps = 1e-12
    denom = a * e - b * b
    s = np.where(denom > eps, np.clip((b * f - c * e) / np.where(denom > eps, denom, 1), 0, 1), 0.0)
    s = np.where(a <= eps, 0.0, s)
    t = np.where(e > eps, (b * s + f) / np.where(e > eps, e, 1), 0.0)
    # clamp t and recompute s where needed
    t_lo, t_hi = t < 0, t > 1
    t = np.clip(t, 0, 1)
    s = np.where(t_lo & (a > eps), np.clip(-c / np.where(a > eps, a, 1), 0, 1), s)
    s = np.where(t_hi & (a > eps), np.clip((b - c) / np.where(a > eps, a, 1), 0, 1), s)
    cp = p0 + d1 * s[:, None]
    cq = q0 + d2 * t[:, None]
    return np.linalg.norm(cp - cq, axis=1), s, t


def composite_hole(fr: np.ndarray, to: np.ndarray, vals: np.ndarray, length: float, min_cover: float = 0.5) -> pd.DataFrame:
    """Length-weighted downhole composites of fixed length from the first sampled depth. A composite needs at least
    `min_cover` of its length sampled (per value column; NaN where not)."""
    fr, to = np.asarray(fr, float), np.asarray(to, float)
    vals = np.asarray(vals, float).reshape(len(fr), -1)
    if len(fr) == 0:
        return pd.DataFrame()
    start = np.floor(fr.min() / length) * length
    edges = np.arange(start, to.max() + length, length)
    rows = []
    for c0, c1 in zip(edges[:-1], edges[1:]):
        ov = np.clip(np.minimum(to, c1) - np.maximum(fr, c0), 0, None)
        if not (ov > 0).any():
            continue
        out = []
        for j in range(vals.shape[1]):
            ok = (ov > 0) & np.isfinite(vals[:, j])
            w = ov[ok].sum()
            out.append(float((ov[ok] * vals[ok, j]).sum() / w) if w >= min_cover * length else np.nan)
        rows.append([c0, c1, *out])
    return pd.DataFrame(rows, columns=["from_m", "to_m", *range(vals.shape[1])])


def composites(ctx, length: float, analytes: list[str]) -> pd.DataFrame:
    """Composites of every hole for the given analytes (routine samples, value with BDL at ½ DL), with the composite
    mid-point position from the desurveyed trace and the collar's drilling method."""
    from ..rules.interval import QC_TYPES
    from .desurvey import position_at
    parts = []
    for t in ctx.by_kind("assay"):
        df = t.df
        ok = df["hole_id"].notna() & (df["to_m"] > df["from_m"])
        if "qc_class" in df:
            ok &= ~df["qc_class"].isin(QC_TYPES)
        cols = {}
        for a in t.analytes:
            if a.analyte in analytes and not a.partial and a.analyte not in cols:
                cols[a.analyte] = a.parsed["value_policy"].astype(float)
        if not cols:
            continue
        d = pd.DataFrame({"hole_id": df["hole_id"], "from_m": df["from_m"], "to_m": df["to_m"], **cols})[ok]
        parts.append(d)
    if not parts:
        return pd.DataFrame()
    s = pd.concat(parts, ignore_index=True)
    names = [a for a in analytes if a in s]
    meth = ctx.collar_u["drill_method"] if ctx.has("collar") and "drill_method" in ctx.collar_u else pd.Series(dtype=object)
    out = []
    for h, g in s.groupby("hole_id", sort=False):
        c = composite_hole(g["from_m"].to_numpy(), g["to_m"].to_numpy(), g[names].to_numpy(float), length)
        if c.empty:
            continue
        c.columns = ["from_m", "to_m", *names]
        c.insert(0, "hole_id", h)
        mid = (c["from_m"] + c["to_m"]).to_numpy() / 2
        tr = ctx.traces.get(h)
        xyz = position_at(tr, mid) if tr is not None else np.full((len(c), 3), np.nan)
        c["x"], c["y"], c["z"] = xyz[:, 0], xyz[:, 1], xyz[:, 2]
        c["mid_m"] = mid
        c["method"] = meth.get(h) if h in meth.index else None
        out.append(c)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def greedy_pairs(a_xyz: np.ndarray, b_xyz: np.ndarray, max_dist: float) -> list[tuple[int, int, float]]:
    """One-to-one nearest pairs between two point sets within max_dist, closest first."""
    from scipy.spatial import cKDTree
    if len(a_xyz) == 0 or len(b_xyz) == 0:
        return []
    tree = cKDTree(b_xyz)
    cand = []
    for i, lst in enumerate(tree.query_ball_point(a_xyz, max_dist)):
        for j in lst:
            cand.append((float(np.linalg.norm(a_xyz[i] - b_xyz[j])), i, j))
    cand.sort()
    used_a, used_b, out = set(), set(), []
    for d, i, j in cand:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        out.append((i, j, d))
    return out


def paired_stats(a: np.ndarray, b: np.ndarray) -> dict:
    """Paired comparison of two value series: n, means, mean ratio, mean and median relative difference (b − a)/mean,
    Wilcoxon signed-rank on the log ratio (positive pairs), and the quantile pairs for a QQ plot."""
    from scipy.stats import wilcoxon
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    out = {"n": int(len(a))}
    if len(a) == 0:
        return out
    m = (a + b) / 2
    rel = np.where(m > 0, (b - a) / np.where(m > 0, m, 1), 0.0)
    out.update({"mean_a": float(a.mean()), "mean_b": float(b.mean()), "mean_ratio": float(b.mean() / a.mean()) if a.mean() > 0 else None,
                "mean_rel_diff": float(rel.mean()), "median_rel_diff": float(np.median(rel)), "mean_diff": float((b - a).mean())})
    pos = (a > 0) & (b > 0)
    if pos.sum() >= 6 and np.any(np.log(b[pos] / a[pos]) != 0):
        out["wilcoxon_p"] = float(wilcoxon(np.log(b[pos] / a[pos])).pvalue)
    q = np.linspace(0, 1, min(len(a), 50))
    out["qq"] = (np.quantile(a, q).tolist(), np.quantile(b, q).tolist())
    return out
