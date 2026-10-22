"""Report figures (matplotlib, Agg). Labels in English for v0.1; captions are bilingual in the HTML."""
from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SEV_COLOR = {"CRITICAL": "#B2182B", "ERROR": "#E66101", "WARNING": "#E6AB02", "INFO": "#4D9DE0", None: "#A0A8AC"}
PAL = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#E3E6E8", "grid.linewidth": 0.6, "axes.edgecolor": "#6B7478", "figure.dpi": 110,
                     "savefig.dpi": 150, "axes.titleweight": "bold", "axes.titlesize": 10})


def _png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _equal(ax):
    ax.set_aspect("equal", adjustable="datalim")
    ax.ticklabel_format(useOffset=False, style="plain")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")


def collar_map(ctx, worst: pd.Series) -> str | None:
    c, excluded = ctx.spatial_collars()
    if c.empty:
        return None
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    if ctx.licence is not None:
        ax.plot(ctx.licence[:, 0], ctx.licence[:, 1], color="#333", lw=1.2, ls="--", label="Licence")
    for h, tr in list(ctx.traces.items())[:3000]:
        if h in c.index:
            ax.plot(tr["x"], tr["y"], color="#9AA4A8", lw=0.6, zorder=1)
    for sev in ["INFO", None, "WARNING", "ERROR", "CRITICAL"]:
        sub = c[worst.reindex(c.index).where(worst.reindex(c.index).notna(), None).eq(sev)] if sev else c[worst.reindex(c.index).isna()]
        if len(sub):
            ax.scatter(sub["x"], sub["y"], s=18, color=SEV_COLOR[sev], edgecolor="white", lw=0.4, zorder=3,
                       label=f"{sev or 'no issue'} ({len(sub)})")
    _equal(ax)
    note = f"; {len(excluded)} collars with location errors not shown" if excluded else ""
    ax.set_title(f"Collars by worst issue severity (n = {len(c)}{note})")
    ax.legend(loc="best", fontsize=7, frameon=True)
    return _png(fig)


def hist(values, title, xlabel, log=False, bins=40, color=PAL[0], vline=None) -> str | None:
    v = pd.Series(values).dropna()
    v = v[np.isfinite(v)]
    if log:
        v = v[v > 0]
    if len(v) < 3:
        return None
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    if log:
        b = np.logspace(np.log10(v.min()), np.log10(v.max()) + 1e-9, bins)
        ax.hist(v, bins=b, color=color, edgecolor="white", lw=0.4)
        ax.set_xscale("log")
    else:
        ax.hist(v, bins=bins, color=color, edgecolor="white", lw=0.4)
    if vline is not None:
        for x in np.atleast_1d(vline):
            ax.axvline(x, color="#B2182B", lw=1, ls="--")
    ax.set_title(f"{title} (n = {len(v)})")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    return _png(fig)


def dz_map(ctx) -> str | None:
    dz = ctx.stats.get("dz")
    if dz is None or dz.dropna().empty:
        return None
    c = ctx.collar_u.loc[dz.dropna().index]
    lim = max(1.0, float(np.nanpercentile(np.abs(dz.dropna()), 95)))
    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    sc = ax.scatter(c["x"], c["y"], c=dz.loc[c.index], cmap="RdBu_r", vmin=-lim, vmax=lim, s=22, edgecolor="#555", lw=0.3)
    fig.colorbar(sc, ax=ax, label="ΔZ = Z collar − Z topo (m)")
    _equal(ax)
    ax.set_title("Collar elevation minus topography")
    return _png(fig)


def method_bar(cm: pd.DataFrame) -> str | None:
    if cm is None or cm.empty:
        return None
    counts = cm["inferred_method"].value_counts()
    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    cols = {"SURVEYED": "#009E73", "HANDHELD_GPS": "#E69F00", "PLANNED": "#D55E00", "DIGITISED": "#CC79A7", "UNKNOWN": "#A0A8AC"}
    ax.barh(counts.index, counts.values, color=[cols.get(k, "#888") for k in counts.index])
    ax.set_xlabel("Collars")
    ax.set_title("Inferred collar survey method")
    ax.invert_yaxis()
    return _png(fig)


def logprob(series_by_name: dict) -> str | None:
    from scipy.stats import norm
    items = [(k, pd.Series(v).dropna()) for k, v in series_by_name.items()]
    items = [(k, v[v > 0]) for k, v in items if (pd.Series(v) > 0).sum() >= 20]
    if not items:
        return None
    n = len(items)
    cols = min(3, n)
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.3 * cols, 2.9 * rows), squeeze=False)
    for ax, (k, v) in zip(axes.flat, items):
        s = np.sort(v.to_numpy())
        q = norm.ppf((np.arange(1, len(s) + 1) - 0.5) / len(s))
        ax.scatter(s, q, s=4, color=PAL[0])
        ax.set_xscale("log")
        ticks = [0.01, 0.1, 0.5, 0.9, 0.99]
        ax.set_yticks(norm.ppf(ticks))
        ax.set_yticklabels([f"{t * 100:g}" for t in ticks])
        ax.set_title(f"{k} (n = {len(s)})")
        ax.set_ylabel("Cumulative %")
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    fig.suptitle("Log-probability plots (population breaks appear as slope changes)", fontsize=9)
    fig.tight_layout()
    return _png(fig)


def corr_heatmap(frame: pd.DataFrame) -> str | None:
    if frame.shape[1] < 3:
        return None
    lg = np.log10(frame.where(frame > 0))
    cm = lg.corr(method="spearman", min_periods=30)
    if cm.isna().all().all():
        return None
    k = cm.shape[0]
    fig, ax = plt.subplots(figsize=(0.45 * k + 2.2, 0.45 * k + 1.6))
    im = ax.imshow(cm.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(k))
    ax.set_xticklabels(cm.columns, rotation=90)
    ax.set_yticks(range(k))
    ax.set_yticklabels(cm.index)
    ax.grid(False)
    for i in range(k):
        for j in range(k):
            v = cm.iat[i, j]
            if np.isfinite(v) and k <= 16:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6, color="white" if abs(v) > 0.6 else "#222")
    fig.colorbar(im, ax=ax, label="Spearman ρ (log values)", shrink=0.8)
    ax.set_title("Inter-element correlation")
    return _png(fig)


def crm_chart(s: pd.DataFrame) -> str | None:
    if s is None or s.empty:
        return None
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    for k, (key, g) in enumerate(s.groupby(["crm", "analyte"])):
        ax.plot(range(len(g)), g["z"].to_numpy(), marker="o", ms=3, lw=0.8, color=PAL[k % len(PAL)], label=f"{key[0]} {key[1]}")
    for y, c in ((3, "#B2182B"), (-3, "#B2182B"), (2, "#E6AB02"), (-2, "#E6AB02")):
        ax.axhline(y, color=c, lw=0.9, ls="--")
    ax.set_xlabel("Insertion sequence")
    ax.set_ylabel("z = (value − certified) / SD")
    ax.set_title("CRM control chart (Shewhart ±2/±3 SD)")
    ax.legend(fontsize=6, ncol=3)
    return _png(fig)


def blank_chart(items) -> str | None:
    if not items:
        return None
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    for k, (an, dl, vals) in enumerate(items):
        if len(vals):
            ax.plot(range(len(vals)), (vals / dl).to_numpy(), marker="o", ms=3, lw=0.8, color=PAL[k % len(PAL)], label=an)
    ax.axhline(5, color="#E6AB02", ls="--", lw=0.9)
    ax.axhline(10, color="#B2182B", ls="--", lw=0.9)
    ax.set_yscale("log")
    ax.set_xlabel("Blank sequence")
    ax.set_ylabel("Value / detection limit")
    ax.set_title("Blank results (warning 5 × DL, failure 10 × DL)")
    ax.legend(fontsize=7)
    return _png(fig)


def hard_chart(pairs: dict) -> str | None:
    if not pairs:
        return None
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    for k, ((tab, kind, an), arr) in enumerate(pairs.items()):
        hard = np.sort(100 * np.abs(arr[:, 0] - arr[:, 1]) / (arr[:, 0] + arr[:, 1]))
        ax.plot(100 * np.arange(1, len(hard) + 1) / len(hard), hard, lw=1.2, color=PAL[k % len(PAL)], label=f"{kind} {an} (n {len(hard)})")
    ax.axvline(90, color="#555", ls=":", lw=0.9)
    ax.set_xlabel("Percentile of pairs")
    ax.set_ylabel("HARD (%)")
    ax.set_title("Ranked HARD plot of duplicate pairs")
    ax.legend(fontsize=7)
    return _png(fig)


def family_bar(issues: pd.DataFrame) -> str | None:
    if issues.empty:
        return None
    t = issues.assign(family=issues["rule_id"].str[:3]).groupby(["family", "severity"]).size().unstack(fill_value=0)
    t = t.reindex(columns=["CRITICAL", "ERROR", "WARNING", "INFO"], fill_value=0)
    fig, ax = plt.subplots(figsize=(6.4, 0.32 * len(t) + 1.2))
    left = np.zeros(len(t))
    for sev in t.columns:
        ax.barh(t.index, t[sev], left=left, color=SEV_COLOR[sev], label=sev)
        left += t[sev].to_numpy()
    ax.invert_yaxis()
    ax.set_xlabel("Issues")
    ax.set_title("Issues by rule family and severity")
    ax.legend(fontsize=7, ncol=4, loc="lower right")
    return _png(fig)


def recovery_grade(rec: pd.Series, val: pd.Series, analyte: str) -> str | None:
    ok = rec.notna() & val.notna() & (val > 0)
    if ok.sum() < 30:
        return None
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    ax.scatter(rec[ok], val[ok], s=5, alpha=0.4, color=PAL[0])
    ax.set_yscale("log")
    ax.set_xlabel("Core recovery (%)")
    ax.set_ylabel(analyte)
    ax.set_title("Core recovery vs grade")
    return _png(fig)
