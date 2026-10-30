"""Cross-table rules on grade versus logged geology (03 §2 CRS family): candidate domains and contact behaviour."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..analysis import categorical as C
from .base import rule


def _mad(x: np.ndarray) -> float:
    return 1.4826 * float(np.median(np.abs(x - np.median(x))))


def _holm(p: list[float]) -> list[float]:
    order = np.argsort(p)
    m, adj, run = len(p), [0.0] * len(p), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * p[i]))
        adj[i] = run
    return adj


@rule("CRS-004", ("assay", "logging"))
def crs_004(ctx):
    from scipy.stats import kruskal, mannwhitneyu
    p = ctx.p("CRS-004")
    smp, units, fields = C.sample_table(ctx)
    if smp.empty:
        return
    keys = C.key_analytes(units, ctx.params)
    assoc = C.association(smp, fields, list(units), p["min_n"])
    ctx.stats["categorical"]["association"] = assoc
    domains = []
    for f, (en, fa, group) in fields.items():
        if group != "logging":
            continue
        for a in keys:
            d = smp[[f, a]].dropna()
            d = d[d[a] > 0]
            counts = d[f].value_counts()
            d = d[d[f].isin(counts[counts >= p["min_n"]].index)]
            if d[f].nunique() < 2:
                continue
            g = {k: np.log10(v.to_numpy(float)) for k, v in d.groupby(f)[a]}
            order = sorted(g, key=lambda k: -np.median(g[k]))
            H, kw_p = kruskal(*g.values())
            pairs = list(zip(order[:-1], order[1:]))
            raw = [mannwhitneyu(g[x], g[y]).pvalue for x, y in pairs]
            adj = _holm(raw)
            merged = []
            for (x, y), pv in zip(pairs, adj):
                pooled = np.sqrt((_mad(g[x]) ** 2 + _mad(g[y]) ** 2) / 2)
                effect = abs(np.median(g[x]) - np.median(g[y])) / pooled if pooled > 0 else 0.0
                if pv >= p["alpha"] or effect < p["effect_min"]:
                    merged.append((x, y))
                    ctx.add("CRS-004", "INFO", f, f"{en}: {x} and {y} have similar {a} grades (median {10 ** np.median(g[x]):.3g} vs {10 ** np.median(g[y]):.3g} {units[a]}; effect {effect:.2f} pooled MAD, Holm p = {pv:.2g}): merge candidates for estimation domains.",
                            f"{fa}: {x} و {y} عیار {a} مشابهی دارند (میانه {10 ** np.median(g[x]):.3g} در برابر {10 ** np.median(g[y]):.3g} {units[a]}؛ اندازهٔ اثر {effect:.2f}، p هولم = {pv:.2g}): نامزد ادغام در دامنه‌های تخمین.",
                            field=a, value=f"{x}|{y}")
            cvs = {k: float((10 ** g[k]).std() / (10 ** g[k]).mean()) for k in order}
            high = {k: v for k, v in cvs.items() if v > p["cv_mixed"]}
            if high and a == keys[0]:
                txt = ", ".join(f"{k} {v:.1f}" for k, v in high.items())
                ctx.add("CRS-004", "INFO", f, f"{en}: {a} CV > {p['cv_mixed']:g} in {txt}: probably mixed grade populations; split these units (e.g. by alteration or weathering) or review top-cuts before estimation.",
                        f"{fa}: ضریب تغییرات {a} بیش از {p['cv_mixed']:g} در {txt}: احتمالاً جامعه‌های عیاری مختلط؛ پیش از تخمین این واحدها را (مثلاً با دگرسانی یا هوازدگی) تفکیک یا سقف عیار را بررسی کنید.",
                        field=a, value=", ".join(high))
            row = assoc[(assoc["field"] == f) & (assoc["analyte"] == a)]
            eta2 = float(row["eta2"].iloc[0]) if len(row) else np.nan
            if np.isfinite(eta2) and eta2 < p["eta2_weak"]:
                ctx.add("CRS-004", "INFO", f, f"{en} explains only {eta2:.1%} of the variance of log {a} (η²): it does not separate grade populations and is a weak domaining criterion.",
                        f"{fa} تنها {eta2:.1%} از واریانس لگاریتم {a} را توضیح می‌دهد (η²): جامعه‌های عیاری را تفکیک نمی‌کند و معیار ضعیفی برای دامنه‌بندی است.",
                        field=a, value=f"eta2={eta2:.3f}")
            groups, cur = [], [order[0]]
            for x, y in pairs:
                if (x, y) in merged:
                    cur.append(y)
                else:
                    groups.append(cur)
                    cur = [y]
            groups.append(cur)
            domains.append({"field": f, "analyte": a, "eta2": eta2, "kw_p": float(kw_p),
                            "suggested_domains": " | ".join(" + ".join(gr) for gr in groups)})
    ctx.stats["categorical"]["domains"] = pd.DataFrame(domains)


def _fit_contact(prof: pd.DataFrame, max_w: float):
    """AIC of a step and a linear-ramp model of log grade against signed distance; return (width, aic_step, aic_ramp)."""
    x, y, w = prof["bin"].to_numpy(float), np.log10(prof["geomean"].to_numpy(float)), prof["n"].to_numpy(float)
    n = len(x)
    if n < 6:
        return None

    def sse(pred):
        return float((w * (y - pred) ** 2).sum() / w.mean())

    a, b = np.average(y[x < 0], weights=w[x < 0]), np.average(y[x > 0], weights=w[x > 0])
    s_step = sse(np.where(x < 0, a, b))
    best = (np.inf, 0.0)
    for width in np.linspace(abs(x[1] - x[0]), max_w, 25):
        t = np.clip((x + width / 2) / width, 0, 1)
        X = np.column_stack([1 - t, t])
        coef, *_ = np.linalg.lstsq(X * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)
        s = sse(X @ coef)
        if s < best[0]:
            best = (s, width)
    aic = lambda s, k: n * np.log(max(s, 1e-12) / n) + 2 * k
    return best[1], aic(s_step, 2), aic(best[0], 3)


@rule("CRS-005", ("assay", "logging"))
def crs_005(ctx):
    p = ctx.p("CRS-005")
    smp, units, fields = C.sample_table(ctx)
    if smp.empty:
        return
    assoc = ctx.stats["categorical"].get("association")
    keys = C.primary_analytes(assoc, units, ctx.params, 1) if assoc is not None else C.key_analytes(units, ctx.params, 1)
    comp = float(smp["length_m"].median())
    step = max(comp, 1.0)
    out = []
    for f, (en, fa, group) in fields.items():
        if group != "logging":
            continue
        for a in keys:
            med = smp.groupby(f)[a].median().dropna().sort_values(ascending=False)
            counts = smp[f].value_counts()
            for unit in [u for u in med.index if counts.get(u, 0) >= 50][:2]:
                prof = C.contact_profile(smp, f, unit, a, p["max_dist_m"], step)
                if prof.empty or (prof["bin"] < 0).sum() < 3 or (prof["bin"] > 0).sum() < 3:
                    continue
                fit = _fit_contact(prof, 2 * p["max_dist_m"])
                if fit is None:
                    continue
                width, aic_s, aic_r = fit
                soft = aic_r + 2 < aic_s and width >= 2 * comp
                out.append({"field": f, "unit": unit, "analyte": a, "width_m": round(width, 1) if soft else 0.0,
                            "aic_step": aic_s, "aic_ramp": aic_r, "boundary": "soft" if soft else "hard", "profile": prof})
                if soft:
                    ctx.add("CRS-005", "INFO", f, f"{en} {unit}: {a} changes gradually across the contact (transition ≈ {width:.0f} m, ramp AIC {aic_r:.1f} vs step {aic_s:.1f}): soft boundary — share samples across the contact in estimation.",
                            f"{fa} {unit}: عیار {a} در همبری به‌تدریج تغییر می‌کند (پهنای گذار ≈ {width:.0f} متر): مرز نرم — در تخمین، نمونه‌ها در دو سوی همبری مشترک استفاده شوند.",
                            field=a, value=f"{unit}: soft {width:.0f} m")
                else:
                    ctx.add("CRS-005", "INFO", f, f"{en} {unit}: {a} steps sharply at the contact (step AIC {aic_s:.1f} vs ramp {aic_r:.1f}): hard boundary — estimate the unit separately.",
                            f"{fa} {unit}: عیار {a} در همبری به‌طور ناگهانی تغییر می‌کند: مرز سخت — واحد جداگانه تخمین زده شود.",
                            field=a, value=f"{unit}: hard")
    ctx.stats["categorical"]["contacts"] = out
