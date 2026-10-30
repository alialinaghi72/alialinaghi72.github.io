"""Figures for the report (ivory theme, PNG) and the desktop app (obsidian theme, embedded canvas).

Every chart function returns a matplotlib Figure (or None when the data are insufficient); `png()` turns it into
an embeddable data URI. Figures are built with the object API (no pyplot state), so they are safe in worker threads.
Labels follow `lang` ("fa" text is shaped for right-to-left display).
"""
from __future__ import annotations

import base64
import io
import threading
from contextlib import contextmanager

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from . import theme as T  # noqa: E402

_LOCK = threading.RLock()
MAX_POINTS = 6000

FAMILY = {"COL": ("دهانه", "Collars"), "SUR": ("انحراف‌سنجی", "Survey"), "INT": ("بازه‌ها", "Intervals"),
          "ASY": ("عیار", "Assays"), "QAQ": ("کنترل کیفیت", "QA/QC"), "LIT": ("سنگ‌شناسی", "Lithology"),
          "GEO": ("ژئوتکنیک", "Geotech"), "DEN": ("چگالی", "Density"), "IMP": ("ورود داده", "Import"),
          "CRS": ("میان‌جدولی", "Cross-table"), "SPA": ("مکانی", "Spatial")}
SEV_FA = {"CRITICAL": "بحرانی", "ERROR": "خطا", "WARNING": "هشدار", "INFO": "اطلاعات"}


# ------------------------------------------------------------------ helpers
@contextmanager
def styled(theme=T.IVORY):
    with _LOCK:
        T.register_fonts()
        with matplotlib.rc_context(T.rc(theme)):
            yield


def png(fig, dpi: int = 150) -> str | None:
    if fig is None:
        return None
    if isinstance(fig, str):
        return fig
    buf = io.BytesIO()
    with _LOCK:
        fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _L(en: str, fa: str, lang: str) -> str:
    return T.label(fa, en, lang)


def _s(x) -> str:
    """Any label that may hold Persian (codes, column names from Persian headers)."""
    return T.fa(str(x))


def _new(w, h, theme, nrows=1, ncols=1, **kw):
    fig = Figure(figsize=(w, h), layout="constrained", facecolor=theme.bg)
    fig.get_layout_engine().set(w_pad=0.08, h_pad=0.08)
    axes = fig.subplots(nrows, ncols, squeeze=False, **kw)
    for ax in axes.flat:
        ax.set_facecolor(theme.panel)
    return fig, axes


def _head(ax, title, subtitle=None, lang="en", theme=T.IVORY):
    loc = "right" if lang == "fa" else "left"
    ax.set_title(title, loc=loc, pad=18 if subtitle else 8, color=theme.ink, fontweight="semibold")
    if subtitle:
        ax.text(1 if lang == "fa" else 0, 1.015, subtitle, transform=ax.transAxes, ha=loc, va="bottom",
                fontsize=7.8, color=theme.muted)


def _equal(ax, lang="en"):
    ax.set_aspect("equal", adjustable="datalim")
    ax.ticklabel_format(useOffset=False, style="plain")
    ax.set_xlabel(_L("Easting (m)", "شرقی (متر)", lang))
    ax.set_ylabel(_L("Northing (m)", "شمالی (متر)", lang))
    ax.tick_params(axis="both", labelsize=7)


def _map_furniture(ax, theme):
    """North arrow and a round-number scale bar."""
    ax.annotate("N", xy=(0.965, 0.95), xytext=(0.965, 0.84), xycoords="axes fraction", ha="center", va="center",
                fontsize=9, fontweight="bold", color=theme.ink,
                arrowprops=dict(arrowstyle="-|>", color=theme.accent, lw=1.4))
    x0, x1 = ax.get_xlim()
    span = (x1 - x0) / 5
    if span <= 0:
        return
    mag = 10 ** np.floor(np.log10(span))
    L = max(v * mag for v in (1, 2, 5) if v * mag <= span)
    y0, y1 = ax.get_ylim()
    xs, ys = x0 + 0.04 * (x1 - x0), y0 + 0.05 * (y1 - y0)
    ax.plot([xs, xs + L], [ys, ys], color=theme.ink, lw=2.2, solid_capstyle="butt", zorder=6)
    ax.plot([xs, xs + L / 2], [ys, ys], color=theme.bg, lw=1.0, solid_capstyle="butt", zorder=7)
    ax.text(xs + L / 2, ys + 0.015 * (y1 - y0), f"{L:,.0f} m", ha="center", va="bottom", fontsize=7, color=theme.ink, zorder=7)


def _logfmt(ax, axis="y", dense=True):
    """Readable log-axis labels (0.01, 0.1, 1, 10 …) with 2 and 5 minor ticks labelled when the span is short."""
    a = ax.yaxis if axis == "y" else ax.xaxis
    lo, hi = (ax.get_ylim() if axis == "y" else ax.get_xlim())
    decades = np.log10(max(hi, 1e-12)) - np.log10(max(lo, 1e-12))
    subs = (1.0, 2.0, 5.0) if dense and decades < 2.5 else (1.0,)
    a.set_major_locator(matplotlib.ticker.LogLocator(base=10, subs=subs))
    a.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: _fmt(v)))
    a.set_minor_formatter(matplotlib.ticker.NullFormatter())


def _on(rgba) -> str:
    """Text colour readable on a cell of colour `rgba` (relative luminance)."""
    r, g, b = mcolors.to_rgb(rgba)
    return "#14181D" if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.55 else "#F4F1EA"


def _seqmap(theme) -> str:
    return "gv_seq_dark" if theme.dark else "gv_seq"


def _pfmt(p: float) -> str:
    return "< 1e-300" if p <= 0 else f"= {p:.1e}" if p < 1e-3 else f"= {p:.3f}"


def _fmt(v: float) -> str:
    if not np.isfinite(v):
        return "–"
    a = abs(v)
    return f"{v:,.0f}" if a >= 100 else f"{v:.3g}"


def _log_ok(v) -> pd.Series:
    v = pd.Series(v, dtype=float).dropna()
    return v[(v > 0) & np.isfinite(v)]


def _sev_legend(ax, lang, theme, counts=None, loc="best", ncol=1, anchor=None):
    h = []
    for s in ("CRITICAL", "ERROR", "WARNING", "INFO"):
        lab = SEV_FA[s] if lang == "fa" else s.title()
        if counts is not None:
            lab += f" ({counts.get(s, 0)})"
        h.append(Patch(color=T.SEVERITY[s], label=T.fa(lab, lang)))
    ax.legend(handles=h, loc=loc, fontsize=7.5, ncol=ncol, bbox_to_anchor=anchor)


# ------------------------------------------------------------------ overview
def severity_donut(issues: pd.DataFrame, lang="en", theme=T.IVORY):
    if issues is None or issues.empty:
        return None
    with styled(theme):
        counts = issues["severity"].value_counts()
        sev = [s for s in ("CRITICAL", "ERROR", "WARNING", "INFO") if counts.get(s, 0)]
        fig, ax = _new(3.6, 3.4, theme)
        ax = ax[0, 0]
        ax.grid(False)
        vals = [counts[s] for s in sev]
        ax.pie(vals, colors=[T.SEVERITY[s] for s in sev], startangle=90, counterclock=False,
               wedgeprops=dict(width=0.32, edgecolor=theme.bg, linewidth=2))
        ax.text(0, 0.08, f"{int(sum(vals)):,}", ha="center", va="center", fontsize=20, fontweight="bold", color=theme.ink)
        ax.text(0, -0.2, _L("issues", "مسئله", lang), ha="center", va="center", fontsize=8.5, color=theme.muted)
        _sev_legend(ax, lang, theme, counts.to_dict(), loc="upper center", ncol=2, anchor=(0.5, 0.0))
        _head(ax, _L("Issues by severity", "مسائل بر پایهٔ شدت", lang), lang=lang, theme=theme)
        return fig


def family_bar(issues: pd.DataFrame, lang="en", theme=T.IVORY):
    if issues is None or issues.empty:
        return None
    with styled(theme):
        t = issues.assign(family=issues["rule_id"].str[:3]).groupby(["family", "severity"]).size().unstack(fill_value=0)
        t = t.reindex(columns=["CRITICAL", "ERROR", "WARNING", "INFO"], fill_value=0)
        t = t.loc[t.sum(axis=1).sort_values().index]
        fig, ax = _new(6.6, 0.36 * len(t) + 1.5, theme)
        ax = ax[0, 0]
        labels = [T.fa(FAMILY.get(f, (f, f))[0], lang) + f"  {f}" if lang == "fa" else f"{FAMILY.get(f, (f, f))[1]}  ·  {f}" for f in t.index]
        left = np.zeros(len(t))
        for sev in t.columns:
            ax.barh(labels, t[sev], left=left, color=T.SEVERITY[sev], height=0.62, edgecolor=theme.bg, linewidth=0.8)
            left += t[sev].to_numpy()
        for y, v in enumerate(left):
            ax.text(v, y, f"  {int(v):,}", va="center", fontsize=7.5, color=theme.muted)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, left.max() * 1.12)
        ax.set_xlabel(_L("Issues", "تعداد مسائل", lang))
        _sev_legend(ax, lang, theme, loc="lower right")
        _head(ax, _L("Issues by rule family and severity", "مسائل بر پایهٔ خانوادهٔ قاعده و شدت", lang),
              _L(f"{len(issues):,} issues in {len(t)} families", f"{len(issues):,} مسئله در {len(t)} خانواده", lang), lang, theme)
        return fig


# ------------------------------------------------------------------ collars & surveys
def collar_map(ctx, worst: pd.Series, lang="en", theme=T.IVORY):
    c, excluded = ctx.spatial_collars()
    if c.empty:
        return None
    with styled(theme):
        fig, ax = _new(7.4, 6.0, theme)
        ax = ax[0, 0]
        if ctx.licence is not None:
            ax.fill(ctx.licence[:, 0], ctx.licence[:, 1], facecolor=theme.accent, alpha=0.06, edgecolor=theme.accent, lw=1.2, ls="--")
        for h, tr in list(ctx.traces.items())[:3000]:
            if h in c.index:
                ax.plot(tr["x"], tr["y"], color=theme.axis, lw=0.7, alpha=0.8, zorder=1, solid_capstyle="round")
        w = worst.reindex(c.index)
        counts = {}
        for sev in [None, "INFO", "WARNING", "ERROR", "CRITICAL"]:
            sub = c[w.isna()] if sev is None else c[w.eq(sev)]
            counts[sev] = len(sub)
            if len(sub):
                ax.scatter(sub["x"], sub["y"], s=30 if sev in ("ERROR", "CRITICAL") else 22, color=T.SEVERITY[sev],
                           edgecolor=theme.bg, lw=0.7, zorder=3 + (sev is not None))
        _equal(ax, lang)
        _map_furniture(ax, theme)
        h = [Line2D([], [], marker="o", ls="", color=T.SEVERITY[s], markeredgecolor=theme.bg, markersize=6,
                    label=T.fa(f"{(SEV_FA.get(s, 'بدون مسئله') if lang == 'fa' else (s.title() if s else 'No issue'))} ({counts[s]})", lang))
             for s in ("CRITICAL", "ERROR", "WARNING", "INFO", None) if counts.get(s)]
        if ctx.licence is not None:
            h.append(Line2D([], [], color=theme.accent, ls="--", label=_L("Licence", "محدودهٔ پروانه", lang)))
        ax.legend(handles=h, loc="upper left", fontsize=7.5, frameon=True, facecolor=theme.panel, edgecolor=theme.grid, framealpha=0.9)
        note = _L(f"{len(excluded)} collars with location errors not shown", f"{len(excluded)} دهانه با خطای موقعیت نمایش داده نشده", lang) if excluded else None
        _head(ax, _L(f"Collars by worst issue severity (n = {len(c)})", f"دهانه‌ها بر پایهٔ شدیدترین مسئله (n = {len(c)})", lang), note, lang, theme)
        return fig


def hist(values, title, xlabel, log=False, bins=40, color=None, vline=None, lang="en", theme=T.IVORY):
    v = pd.Series(values, dtype=float).dropna()
    v = v[np.isfinite(v)]
    if log:
        v = v[v > 0]
    if len(v) < 3:
        return None
    with styled(theme):
        color = color or T.CAT[0]
        fig, ax = _new(5.6, 3.4, theme)
        ax = ax[0, 0]
        b = np.logspace(np.log10(v.min()), np.log10(v.max()) + 1e-9, bins) if log else bins
        ax.hist(v, bins=b, color=color, alpha=0.88, edgecolor=theme.bg, lw=0.5)
        if log:
            ax.set_xscale("log")
        if vline is not None:
            for k, x in enumerate(np.atleast_1d(vline)):
                ax.axvline(x, color=T.SEVERITY["WARNING" if abs(x) == min(np.abs(np.atleast_1d(vline))) else "CRITICAL"], lw=1, ls="--")
        med = float(v.median())
        ax.axvline(med, color=theme.accent, lw=1.4)
        ax.text(med, ax.get_ylim()[1] * 0.97, f" P50 {_fmt(med)}", color=theme.accent, fontsize=7.5, va="top")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(_L("Count", "تعداد", lang))
        ax.grid(axis="x", visible=False)
        _head(ax, title, f"n = {len(v):,} · mean {_fmt(v.mean())} · P95 {_fmt(v.quantile(.95))}", lang, theme)
        return fig


def dz_map(ctx, lang="en", theme=T.IVORY):
    dz = ctx.stats.get("dz")
    if dz is None or dz.dropna().empty:
        return None
    with styled(theme):
        c = ctx.collar_u.loc[dz.dropna().index]
        lim = max(1.0, float(np.nanpercentile(np.abs(dz.dropna()), 95)))
        fig, ax = _new(6.4, 5.2, theme)
        ax = ax[0, 0]
        sc = ax.scatter(c["x"], c["y"], c=dz.loc[c.index], cmap=theme.div, vmin=-lim, vmax=lim, s=34, edgecolor=theme.axis, lw=0.4)
        cb = fig.colorbar(sc, ax=ax, shrink=0.85, pad=0.01)
        cb.set_label(_L("ΔZ = collar − topography (m)", "اختلاف ارتفاع دهانه و توپوگرافی (متر)", lang))
        cb.outline.set_visible(False)
        _equal(ax, lang)
        _map_furniture(ax, theme)
        _head(ax, _L("Collar elevation minus topography", "اختلاف ارتفاع دهانه با توپوگرافی", lang),
              _L("blue: collar below the DEM · red: above", "آبی: پایین‌تر از توپوگرافی · قرمز: بالاتر", lang), lang, theme)
        return fig


def method_bar(cm: pd.DataFrame, lang="en", theme=T.IVORY):
    if cm is None or cm.empty:
        return None
    with styled(theme):
        counts = cm["inferred_method"].value_counts().sort_values()
        fig, ax = _new(5.4, 0.42 * len(counts) + 1.3, theme)
        ax = ax[0, 0]
        ax.barh(counts.index, counts.values, color=[T.METHOD.get(k, theme.axis) for k in counts.index], height=0.6)
        for y, v in enumerate(counts.values):
            ax.text(v, y, f"  {v} ({v / counts.sum():.0%})", va="center", fontsize=7.5, color=theme.muted)
        ax.set_xlim(0, counts.max() * 1.25)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel(_L("Collars", "تعداد دهانه", lang))
        _head(ax, _L("Inferred collar survey method", "روش استنتاجی برداشت مختصات دهانه", lang), lang=lang, theme=theme)
        return fig


# ------------------------------------------------------------------ assays
def logprob(series_by_name: dict, units: dict | None = None, lang="en", theme=T.IVORY):
    from scipy.stats import norm
    items = [(k, _log_ok(v)) for k, v in series_by_name.items()]
    items = [(k, v) for k, v in items if len(v) >= 20]
    if not items:
        return None
    with styled(theme):
        n = len(items)
        cols = min(3, n)
        rows = int(np.ceil(n / cols))
        fig, axes = _new(3.5 * cols, 3.0 * rows, theme, rows, cols)
        ticks = [0.001, 0.01, 0.1, 0.5, 0.9, 0.99, 0.999]
        for k, (ax, (name, v)) in enumerate(zip(axes.flat, items)):
            s = np.sort(v.to_numpy())
            if len(s) > MAX_POINTS:
                s = s[np.linspace(0, len(s) - 1, MAX_POINTS).astype(int)]
            q = norm.ppf((np.arange(1, len(s) + 1) - 0.5) / len(s))
            ax.scatter(s, q, s=5, color=T.CAT[k % len(T.CAT)], alpha=0.8, lw=0)
            ax.set_xscale("log")
            _logfmt(ax, "x")
            ax.set_yticks(norm.ppf(ticks))
            ax.set_yticklabels([f"{t * 100:g}" for t in ticks])
            ax.set_ylim(norm.ppf(0.0005), norm.ppf(0.9995))
            unit = (units or {}).get(name, "")
            ax.set_xlabel(f"{name} {unit}".strip())
            ax.set_ylabel(_L("Cumulative %", "درصد تجمعی", lang))
            ax.grid(True, which="both", alpha=0.6)
            _head(ax, name, f"n = {len(v):,}", lang, theme)
        for ax in list(axes.flat)[n:]:
            ax.set_visible(False)
        fig.suptitle(_L("Log-probability plots — slope breaks mark separate grade populations",
                        "نمودارهای احتمال لگاریتمی — تغییر شیب نشانهٔ جامعه‌های عیاری جداگانه است", lang),
                     fontsize=9, color=theme.muted, x=0.99 if lang == "fa" else 0.01, ha="right" if lang == "fa" else "left")
        return fig


def corr_heatmap(frame: pd.DataFrame, lang="en", theme=T.IVORY):
    if frame.shape[1] < 3:
        return None
    lg = np.log10(frame.where(frame > 0))
    cm = lg.corr(method="spearman", min_periods=30)
    if cm.isna().all().all():
        return None
    with styled(theme):
        k = cm.shape[0]
        fig, ax = _new(0.5 * k + 2.6, 0.5 * k + 1.8, theme)
        ax = ax[0, 0]
        m = cm.to_numpy().copy()
        m[np.triu_indices(k, 0)] = np.nan
        im = ax.imshow(m, cmap=theme.div, vmin=-1, vmax=1)
        ax.set_xticks(range(k))
        ax.set_xticklabels(cm.columns, rotation=90)
        ax.set_yticks(range(k))
        ax.set_yticklabels(cm.index)
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        if k <= 16:
            for i in range(k):
                for j in range(i + 1):
                    v = cm.iat[i, j]
                    if np.isfinite(v) and i != j:
                        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5, color=_on(im.cmap(im.norm(v))))
        cb = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
        cb.set_label(_L("Spearman ρ (log values)", "ضریب اسپیرمن (مقادیر لگاریتمی)", lang))
        cb.outline.set_visible(False)
        _head(ax, _L("Inter-element correlation", "همبستگی بین عناصر", lang), _L("original samples only", "فقط نمونه‌های اصلی", lang), lang, theme)
        return fig


def scatter_pair(smp: pd.DataFrame, a: str, b: str, field: str | None, units: dict, lang="en", theme=T.IVORY):
    cols = [a, b] + ([field] if field else [])
    d = smp[cols].dropna(subset=[a, b])
    d = d[(d[a] > 0) & (d[b] > 0)]
    if len(d) < 20:
        return None
    from scipy.stats import spearmanr
    with styled(theme):
        rho = spearmanr(d[a], d[b]).statistic
        fig, ax = _new(5.6, 4.4, theme)
        ax = ax[0, 0]
        if len(d) > MAX_POINTS:
            d = d.sample(MAX_POINTS, random_state=1)
        if field:
            order = list(d[field].value_counts().index[:9])
            colours = T.cat_colours(category_order_simple(d, field)[:12])
            for cat in order[::-1]:
                g = d[d[field] == cat]
                ax.scatter(g[a], g[b], s=7, alpha=0.55, lw=0, color=colours.get(cat, theme.axis), label=_s(f"{cat} ({len(g)})"))
            ax.legend(fontsize=7, markerscale=2, loc="upper left", title=_s(field), title_fontsize=7.5)
        else:
            ax.hexbin(d[a], d[b], xscale="log", yscale="log", gridsize=45, mincnt=1, cmap=_seqmap(theme), bins="log")
        ax.set_xscale("log")
        ax.set_yscale("log")
        _logfmt(ax, "x")
        _logfmt(ax, "y")
        ax.set_xlabel(f"{a} {units.get(a, '')}")
        ax.set_ylabel(f"{b} {units.get(b, '')}")
        ax.grid(True, which="major")
        _head(ax, _L(f"{b} against {a}", f"{b} در برابر {a}", lang), f"Spearman ρ = {rho:.2f} · n = {len(d):,}", lang, theme)
        return fig


def category_order_simple(d: pd.DataFrame, field: str) -> list:
    return list(d[field].value_counts().index)


# ------------------------------------------------------------------ QA/QC
def crm_chart(s: pd.DataFrame, lang="en", theme=T.IVORY):
    if s is None or s.empty:
        return None
    with styled(theme):
        fig, ax = _new(7.4, 3.4, theme)
        ax = ax[0, 0]
        ax.axhspan(-2, 2, color=T.CAT[0], alpha=0.07, lw=0)
        for y, c in ((3, T.SEVERITY["CRITICAL"]), (-3, T.SEVERITY["CRITICAL"]), (2, T.SEVERITY["WARNING"]), (-2, T.SEVERITY["WARNING"])):
            ax.axhline(y, color=c, lw=0.9, ls="--")
        ax.axhline(0, color=theme.axis, lw=0.8)
        for k, (key, g) in enumerate(s.groupby(["crm", "analyte"])):
            z = g["z"].to_numpy()
            ax.plot(range(len(g)), z, marker="o", ms=3.2, lw=0.9, color=T.CAT[k % len(T.CAT)], label=f"{key[0]} · {key[1]}", alpha=0.9)
            bad = np.abs(z) > 3
            if bad.any():
                ax.scatter(np.arange(len(g))[bad], z[bad], s=60, facecolor="none", edgecolor=T.SEVERITY["CRITICAL"], lw=1.4, zorder=5)
        ax.set_xlabel(_L("Insertion sequence", "ترتیب درج", lang))
        ax.set_ylabel("z = (value − certified) / SD")
        ax.legend(fontsize=7, ncol=4, loc="upper left")
        ax.set_ylim(min(-4, ax.get_ylim()[0]), max(4, ax.get_ylim()[1]))
        _head(ax, _L("CRM control chart", "نمودار کنترل مواد مرجع (CRM)", lang),
              _L("Shewhart limits ±2 SD (warning) and ±3 SD (failure); failures circled", "حدود شوهارت: ±۲ (هشدار) و ±۳ انحراف معیار (مردودی)", lang), lang, theme)
        return fig


def blank_chart(items, lang="en", theme=T.IVORY):
    if not items:
        return None
    with styled(theme):
        fig, ax = _new(7.4, 3.2, theme)
        ax = ax[0, 0]
        ax.axhspan(0.1, 5, color=T.CAT[0], alpha=0.06, lw=0)
        for k, (an, dl, v) in enumerate(items):
            if isinstance(v, pd.Series):
                v = pd.DataFrame({"flag": "VAL", "value": v})
            v = v[v["flag"].isin(["VAL", "BDL"])]
            if v.empty:
                continue
            r = np.where(v["flag"] == "VAL", v["value"] / dl, 0.5)
            col = T.CAT[k % len(T.CAT)]
            x = np.arange(len(r))
            ax.plot(x, r, lw=0.7, color=col, alpha=0.5)
            val = (v["flag"] == "VAL").to_numpy()
            ax.scatter(x[val], r[val], s=14, color=col, label=f"{an} (DL {dl:g})", zorder=3)
            ax.scatter(x[~val], r[~val], s=14, facecolor="none", edgecolor=col, lw=0.9, zorder=3)
        ax.scatter([], [], s=14, facecolor="none", edgecolor=theme.muted, label=_L("below DL (plotted at ½ DL)", "کمتر از حد تشخیص (در ½ حد)", lang))
        ax.axhline(5, color=T.SEVERITY["WARNING"], ls="--", lw=0.9)
        ax.axhline(10, color=T.SEVERITY["CRITICAL"], ls="--", lw=0.9)
        ax.set_yscale("log")
        _logfmt(ax, "y")
        ax.set_xlabel(_L("Blank sequence", "ترتیب بلانک", lang))
        ax.set_ylabel(_L("Value / detection limit", "مقدار / حد تشخیص", lang))
        ax.legend(fontsize=7, ncol=6)
        _head(ax, _L("Blank results", "نتایج نمونه‌های شاهد (بلانک)", lang), _L("warning 5 × DL · failure 10 × DL", "هشدار ۵ برابر و مردودی ۱۰ برابر حد تشخیص", lang), lang, theme)
        return fig


def hard_chart(pairs: dict, lang="en", theme=T.IVORY, analytes: list | None = None):
    if not pairs:
        return None
    with styled(theme):
        fig, ax = _new(6.2, 3.6, theme)
        ax = ax[0, 0]
        items = list(pairs.items())
        if len(items) > 8:
            keep = list(dict.fromkeys(an for (_, _, an), _ in items))[:2] if not analytes else analytes
            items = [it for it in items if it[0][2] in keep][:9]
        for k, ((tab, kind, an), arr) in enumerate(items):
            hard = np.sort(100 * np.abs(arr[:, 0] - arr[:, 1]) / (arr[:, 0] + arr[:, 1]))
            ax.plot(100 * np.arange(1, len(hard) + 1) / len(hard), hard, lw=1.6, color=T.CAT[k % len(T.CAT)], label=f"{kind} {an} (n {len(hard)})")
        ax.axvline(90, color=theme.muted, ls=":", lw=0.9)
        ax.set_xlabel(_L("Percentile of pairs", "صدک جفت‌ها", lang))
        ax.set_ylabel("HARD (%)")
        ax.set_ylim(0, min(100, ax.get_ylim()[1]))
        ax.legend(fontsize=7, ncol=1 if len(items) <= 5 else 2)
        _head(ax, _L("Ranked HARD plot of duplicate pairs", "نمودار رتبه‌ای HARD نمونه‌های تکراری", lang),
              _L("half absolute relative difference; read the curve at the 90th percentile", "نیمِ اختلاف نسبی مطلق؛ مقدار در صدک ۹۰ خوانده شود", lang), lang, theme)
        return fig


def recovery_grade(rec: pd.Series, val: pd.Series, analyte: str, lang="en", theme=T.IVORY):
    ok = rec.notna() & val.notna() & (val > 0)
    if ok.sum() < 30:
        return None
    with styled(theme):
        r, v = rec[ok].clip(0, 110), val[ok]
        fig, ax = _new(5.6, 3.6, theme)
        ax = ax[0, 0]
        ax.scatter(r, v, s=5, alpha=0.25, color=T.CAT[0], lw=0)
        bins = pd.qcut(r, 10, duplicates="drop")
        med = v.groupby(bins, observed=True).median()
        xs = r.groupby(bins, observed=True).median()
        ax.plot(xs.values, med.values, color=theme.accent, lw=2, marker="o", ms=4, label=_L("median per recovery decile", "میانه در هر دهک بازیافت", lang))
        ax.set_yscale("log")
        _logfmt(ax, "y")
        ax.set_xlabel(_L("Core recovery (%)", "بازیافت مغزه (درصد)", lang))
        ax.set_ylabel(analyte)
        ax.legend(fontsize=7.5)
        _head(ax, _L("Core recovery vs grade", "بازیافت مغزه در برابر عیار", lang),
              _L("a slope in the median line signals recovery-related sampling bias", "شیب خط میانه نشانهٔ اریبی نمونه‌برداری ناشی از بازیافت است", lang), lang, theme)
        return fig


# ------------------------------------------------------------------ grade vs logged geology
def grade_by_category(smp: pd.DataFrame, field: str, analyte: str, unit: str, field_label: str | None = None,
                      cutoff: float | None = None, assoc_row: dict | None = None, lang="en", theme=T.IVORY, min_n: int = 5):
    d = smp[[field, analyte, "length_m"]].dropna()
    d = d[d[analyte] > 0]
    if d.empty or d[field].nunique() < 2:
        return None
    counts = d[field].value_counts()
    d = d[d[field].isin(counts[counts >= min_n].index)]
    if d[field].nunique() < 2:
        return None
    with styled(theme):
        med = d.groupby(field)[analyte].median().sort_values(ascending=True)
        cats = list(med.index)
        colours = T.cat_colours(category_order_simple(d, field))
        fig, ax = _new(7.2, 0.5 * len(cats) + 1.7, theme)
        ax = ax[0, 0]
        data = [np.log10(d.loc[d[field] == c, analyte].to_numpy(float)) for c in cats]
        bp = ax.boxplot(data, orientation="horizontal", widths=0.58, patch_artist=True, showfliers=False, whis=(5, 95),
                        medianprops=dict(color=theme.ink, lw=1.8), whiskerprops=dict(color=theme.muted, lw=0.9),
                        capprops=dict(color=theme.muted, lw=0.9))
        rng = np.random.default_rng(3)
        for k, (c, box) in enumerate(zip(cats, bp["boxes"])):
            col = colours[c]
            box.set(facecolor=mcolors.to_rgba(col, 0.38), edgecolor=col, lw=1.2)
            x = data[k]
            if len(x) > 500:
                x = rng.choice(x, 500, replace=False)
            ax.scatter(x, k + 1 + rng.uniform(-0.2, 0.2, len(x)), s=3.5, color=col, alpha=0.35, lw=0, zorder=2)
            g = d[d[field] == c]
            lw = float((g[analyte] * g["length_m"]).sum() / g["length_m"].sum())
            ax.scatter([np.log10(lw)], [k + 1], marker="D", s=26, color=theme.accent, edgecolor=theme.bg, lw=0.8, zorder=4)
        ax.set_yticks(range(1, len(cats) + 1))
        ax.set_yticklabels([_s(c) for c in cats])
        lo, hi = np.floor(min(np.percentile(x, 1) for x in data)), np.ceil(max(np.percentile(x, 99.5) for x in data))
        ax.set_xlim(lo - 0.05, hi + 0.05)
        xt = np.arange(lo, hi + 1)
        ax.set_xticks(xt)
        ax.set_xticklabels([_fmt(10 ** v) for v in xt])
        ax.grid(axis="y", visible=False)
        if cutoff:
            ax.axvline(np.log10(cutoff), color=T.SEVERITY["ERROR"], lw=1, ls="--")
        trans = ax.get_yaxis_transform()
        for k, c in enumerate(cats):
            ax.text(1.005, k + 1, f"P50 {_fmt(med[c])}  ·  n {counts[c]:,}", transform=trans, va="center", fontsize=7, color=theme.muted)
        ax.set_xlabel(f"{analyte} ({unit}, log scale)" if lang != "fa" else T.fa(f"عیار {analyte} ({unit}، مقیاس لگاریتمی)", lang))
        sub = None
        if assoc_row:
            sub = (f"η² = {assoc_row['eta2']:.2f} ({assoc_row['eta2']:.0%} of log-grade variance explained) · Kruskal–Wallis p {_pfmt(assoc_row['kw_p'])}"
                   if lang != "fa" else T.fa(f"η² = {assoc_row['eta2']:.2f} — {assoc_row['eta2']:.0%} واریانس لگاریتم عیار توسط این واحدها توضیح داده می‌شود", lang))
        label = field_label or field
        _head(ax, _s(f"{analyte} grade by {label}" if lang != "fa" else f"عیار {analyte} به تفکیک {label}"), sub, lang, theme)
        handles = [Line2D([], [], marker="D", ls="", color=theme.accent, label=_L("length-weighted mean", "میانگین وزنی طولی", lang)),
                   Line2D([], [], color=theme.ink, lw=1.8, label=_L("median · box P25–P75 · whiskers P5–P95", "میانه · جعبه P25–P75 · خطوط P5–P95", lang))]
        if cutoff:
            handles.append(Line2D([], [], color=T.SEVERITY["ERROR"], ls="--", lw=1, label=_L(f"cut-off {_fmt(cutoff)} {unit}", f"عیار حد {_fmt(cutoff)} {unit}", lang)))
        ax.legend(handles=handles, loc="lower right", fontsize=7, frameon=True, facecolor=theme.panel, edgecolor=theme.grid)
        return fig


def association_heatmap(assoc: pd.DataFrame, labels: dict | None = None, lang="en", theme=T.IVORY):
    if assoc is None or assoc.empty:
        return None
    with styled(theme):
        pv = assoc.pivot_table(index="field", columns="analyte", values="eta2")
        pp = assoc.pivot_table(index="field", columns="analyte", values="kw_p")
        pv = pv.loc[pv.max(axis=1).sort_values(ascending=False).index]
        pp = pp.loc[pv.index, pv.columns]
        r, c = pv.shape
        fig, ax = _new(0.62 * c + 3.6, 0.48 * r + 1.9, theme)
        ax = ax[0, 0]
        im = ax.imshow(pv.to_numpy(), cmap=_seqmap(theme), vmin=0, vmax=max(0.3, float(np.nanmax(pv.to_numpy()))), aspect="auto")
        ax.set_xticks(range(c))
        ax.set_xticklabels(pv.columns)
        ax.set_yticks(range(r))
        ax.set_yticklabels([_s((labels or {}).get(f, f)) for f in pv.index])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        for i in range(r):
            for j in range(c):
                v, p = pv.iat[i, j], pp.iat[i, j]
                if np.isfinite(v):
                    star = "***" if p < 1e-3 else "**" if p < 1e-2 else "*" if p < 0.05 else ""
                    ax.text(j, i, f"{v:.2f}{star}", ha="center", va="center", fontsize=7, color=_on(im.cmap(im.norm(v))))
        cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cb.set_label(_L("η² (share of log-grade variance explained)", "η² (سهم واریانس لگاریتم عیار)", lang))
        cb.outline.set_visible(False)
        _head(ax, _L("Which logged attributes control grade?", "کدام ویژگی‌های توصیفی عیار را کنترل می‌کنند؟", lang),
              _L("correlation ratio η² of log grade by category · Kruskal–Wallis * p<0.05 ** p<0.01 *** p<0.001",
                 "نسبت همبستگی η² لگاریتم عیار به تفکیک رده · آزمون کروسکال–والیس", lang), lang, theme)
        return fig


def two_way_heatmap(med: pd.DataFrame, cnt: pd.DataFrame, row_label: str, col_label: str, analyte: str, unit: str, lang="en", theme=T.IVORY):
    if med is None or med.empty or med.notna().sum().sum() < 2:
        return None
    with styled(theme):
        r, c = med.shape
        fig, ax = _new(0.95 * c + 3.2, 0.5 * r + 1.9, theme)
        ax = ax[0, 0]
        vals = med.to_numpy(float)
        pos = vals[np.isfinite(vals) & (vals > 0)]
        norm = mcolors.LogNorm(vmin=pos.min(), vmax=pos.max()) if len(pos) and pos.max() > pos.min() else None
        im = ax.imshow(np.where(np.isfinite(vals) & (vals > 0), vals, np.nan), cmap="gv_grade", norm=norm, aspect="auto")
        ax.set_xticks(range(c))
        ax.set_xticklabels([_s(x) for x in med.columns], rotation=30, ha="right")
        ax.set_yticks(range(r))
        ax.set_yticklabels([_s(x) for x in med.index])
        ax.set_xlabel(_s(col_label))
        ax.set_ylabel(_s(row_label))
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        for i in range(r):
            for j in range(c):
                v = vals[i, j]
                n = cnt.iat[i, j] if cnt is not None else np.nan
                if np.isfinite(v) and v > 0:
                    tc = _on(im.cmap(im.norm(v)))
                    ax.text(j, i - 0.1, _fmt(v), ha="center", va="center", fontsize=7.5, fontweight="semibold", color=tc)
                    if np.isfinite(n):
                        ax.text(j, i + 0.24, f"n {int(n)}", ha="center", va="center", fontsize=5.8, color=tc, alpha=0.8)
                else:
                    ax.text(j, i, "·", ha="center", va="center", color=theme.muted)
        cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cb.set_label(_L(f"median {analyte} ({unit})", f"میانهٔ {analyte} ({unit})", lang))
        cb.outline.set_visible(False)
        _head(ax, _s(f"Median {analyte}: {row_label} × {col_label}" if lang != "fa" else f"میانهٔ {analyte}: {row_label} × {col_label}"),
              _L("cells with fewer than 5 samples are blank", "خانه‌های با کمتر از ۵ نمونه خالی‌اند", lang), lang, theme)
        return fig


def contact_plot(contacts: list, units: dict, lang="en", theme=T.IVORY, labels: dict | None = None):
    items = [c for c in (contacts or []) if c.get("profile") is not None and not c["profile"].empty]
    if not items:
        return None
    with styled(theme):
        n = len(items)
        cols = min(3, n)
        rows = int(np.ceil(n / cols))
        fig, axes = _new(3.6 * cols, 3.0 * rows, theme, rows, cols)
        for ax, c in zip(axes.flat, items):
            p = c["profile"]
            soft = c["boundary"] == "soft"
            col = T.CAT[0] if soft else T.CAT[1]
            ax.axvspan(0, p["bin"].max() + 1, color=col, alpha=0.06, lw=0)
            ax.axvline(0, color=theme.muted, lw=1)
            ax.plot(p["bin"], p["geomean"], color=col, lw=2, marker="o", ms=3.5, label=_L("geometric mean", "میانگین هندسی", lang))
            ax.plot(p["bin"], p["median"], color=theme.muted, lw=1, ls="--", label=_L("median", "میانه", lang))
            ax.set_yscale("log")
            _logfmt(ax, "y")
            if soft and c.get("width_m"):
                ax.axvspan(-c["width_m"] / 2, c["width_m"] / 2, color=theme.accent, alpha=0.12, lw=0)
            ax.set_xlabel(_L("distance to contact (m) · inside →", "فاصله تا همبری (متر) · درون واحد ←", lang))
            ax.set_ylabel(f"{c['analyte']} {units.get(c['analyte'], '')}")
            flabel = (labels or {}).get(c["field"], c["field"])
            if lang == "fa":
                sub = T.fa(f"{flabel} · مرز {'نرم' if soft else 'سخت'}" + (f" ≈ {c['width_m']:.0f} متر" if soft else ""), lang)
            else:
                sub = f"{flabel} · " + (f"soft boundary ≈ {c['width_m']:.0f} m" if soft else "hard boundary")
            _head(ax, _s(c["unit"]), sub, lang, theme)
        axes.flat[0].legend(fontsize=7, loc="lower right")
        for ax in list(axes.flat)[n:]:
            ax.set_visible(False)
        fig.suptitle(_L("Contact analysis: grade against distance to the unit boundary", "تحلیل همبری: عیار در برابر فاصله تا مرز واحد", lang),
                     fontsize=9, color=theme.muted, x=0.99 if lang == "fa" else 0.01, ha="right" if lang == "fa" else "left")
        return fig


def swath_plots(smp: pd.DataFrame, analyte: str, unit: str, lang="en", theme=T.IVORY):
    from ..analysis.categorical import swath
    axes_def = [("x", _L("Easting (m)", "شرقی (متر)", lang)), ("y", _L("Northing (m)", "شمالی (متر)", lang)), ("z", _L("Elevation (m)", "ارتفاع (متر)", lang))]
    sw = [(a, lab, swath(smp, analyte, a)) for a, lab in axes_def]
    sw = [s for s in sw if not s[2].empty]
    if not sw:
        return None
    with styled(theme):
        fig, axes = _new(10.5, 3.2, theme, 1, len(sw))
        for k, (ax, (a, lab, s)) in enumerate(zip(axes.flat, sw)):
            ax2 = ax.twinx()
            ax2.bar(s["centre"], s["n"], width=(s["centre"].diff().median() or 1) * 0.85, color=theme.grid, alpha=0.9, zorder=0)
            ax2.set_ylim(0, s["n"].max() * 3)
            ax2.set_yticks([])
            ax2.spines[:].set_visible(False)
            ax2.grid(False)
            ax.set_zorder(ax2.get_zorder() + 1)
            ax.patch.set_visible(False)
            ax.plot(s["centre"], s["mean_lw"], color=T.CAT[k], lw=2, marker="o", ms=3.5, label=_L("length-weighted mean", "میانگین وزنی طولی", lang))
            ax.plot(s["centre"], s["median"], color=theme.muted, lw=1, ls="--", label=_L("median", "میانه", lang))
            ax.set_xlabel(lab)
            ax.set_ylabel(f"{analyte} ({unit})")
            ax.ticklabel_format(axis="x", useOffset=False, style="plain")
            ax.tick_params(axis="x", labelsize=7)
            _head(ax, lab, _L("bars: samples per slice", "ستون‌ها: تعداد نمونه در هر برش", lang), lang, theme)
        axes.flat[0].legend(fontsize=7, loc="upper left")
        fig.suptitle(_L(f"Swath plots — {analyte} trends along the three axes", f"نمودارهای نواری (Swath) — روند {analyte} در سه جهت", lang),
                     fontsize=9, color=theme.muted, x=0.99 if lang == "fa" else 0.01, ha="right" if lang == "fa" else "left")
        return fig


def gt_map(hg: pd.DataFrame, analyte: str, unit: str, cutoff: float | None, licence=None, lang="en", theme=T.IVORY):
    if hg is None or hg.empty:
        return None
    with styled(theme):
        fig, ax = _new(7.0, 5.8, theme)
        ax = ax[0, 0]
        if licence is not None:
            ax.fill(licence[:, 0], licence[:, 1], facecolor=theme.accent, alpha=0.05, edgecolor=theme.accent, lw=1, ls="--")
        gt = hg["gt"].clip(lower=0)
        size = 18 + 520 * (gt / gt.max()) if gt.max() > 0 else 30
        vals = hg["mean_lw"].clip(lower=hg["mean_lw"][hg["mean_lw"] > 0].min() if (hg["mean_lw"] > 0).any() else 1e-6)
        norm = mcolors.LogNorm(vmin=vals.min(), vmax=vals.max()) if vals.max() > vals.min() > 0 else None
        sc = ax.scatter(hg["x"], hg["y"], s=size, c=vals, cmap="gv_grade", norm=norm, edgecolor=theme.bg, lw=0.8, alpha=0.92, zorder=3)
        for _, r in hg.nlargest(5, "gt").iterrows():
            ax.annotate(str(r["hole_id"]), (r["x"], r["y"]), xytext=(6, 6), textcoords="offset points", fontsize=7, color=theme.ink, zorder=5)
        cb = fig.colorbar(sc, ax=ax, shrink=0.8, pad=0.01)
        cb.set_label(_L(f"hole mean {analyte} ({unit}, length-weighted)", f"میانگین وزنی {analyte} گمانه ({unit})", lang))
        cb.outline.set_visible(False)
        _equal(ax, lang)
        _map_furniture(ax, theme)
        cut = f"{_fmt(cutoff)} {unit}" if cutoff else "—"
        _head(ax, _L(f"Grade × thickness by hole — {analyte}", f"عیار × ضخامت در هر گمانه — {analyte}", lang),
              _L(f"bubble size: Σ grade·metres above cut-off {cut}", f"اندازهٔ دایره: مجموع عیار×متر بالای عیار حد {cut}", lang), lang, theme)
        return fig


def grade_length_curve(smp: pd.DataFrame, analyte: str, unit: str, lang="en", theme=T.IVORY):
    from ..analysis.categorical import grade_length
    g = grade_length(smp, analyte)
    if g.empty:
        return None
    with styled(theme):
        fig, ax = _new(6.2, 3.8, theme)
        ax = ax[0, 0]
        ax.plot(g["cutoff"], g["metres"], color=T.CAT[0], lw=2.2, label=_L("metres above cut-off", "متراژ بالای عیار حد", lang))
        ax.fill_between(g["cutoff"], g["metres"], color=T.CAT[0], alpha=0.08)
        ax.set_xscale("log")
        _logfmt(ax, "x")
        ax.set_xlabel(_L(f"cut-off {analyte} ({unit})", f"عیار حد {analyte} ({unit})", lang))
        ax.set_ylabel(_L("sampled metres above cut-off", "متراژ نمونه‌ها بالای عیار حد", lang), color=T.CAT[0])
        ax2 = ax.twinx()
        ax2.plot(g["cutoff"], g["grade"], color=T.CAT[1], lw=2.2, label=_L("mean grade above cut-off", "عیار میانگین بالای عیار حد", lang))
        ax2.set_ylabel(_L(f"mean grade above cut-off ({unit})", f"عیار میانگین بالای حد ({unit})", lang), color=T.CAT[1])
        ax2.grid(False)
        ax2.spines["right"].set_visible(True)
        ax2.spines["right"].set_color(theme.axis)
        ax2.tick_params(colors=theme.muted)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc="center left", fontsize=7.5)
        _head(ax, _L(f"Grade–length curve — {analyte}", f"منحنی عیار–متراژ — {analyte}", lang),
              _L("analogue of a grade–tonnage curve on sample lengths (not declustered, no density)", "مشابه منحنی عیار–تناژ بر پایهٔ طول نمونه‌ها (بدون وزن‌دهی مکانی و چگالی)", lang), lang, theme)
        return fig


def composition_depth(smp: pd.DataFrame, field: str, field_label: str | None = None, lang="en", theme=T.IVORY):
    from ..analysis.categorical import depth_proportions
    p = depth_proportions(smp, field)
    if p.empty or p.shape[1] < 2 or len(p) < 3:
        return None
    with styled(theme):
        colours = T.cat_colours(list(p.sum().sort_values(ascending=False).index))
        fig, ax = _new(4.6, 5.4, theme)
        ax = ax[0, 0]
        left = np.zeros(len(p))
        y = p.index.to_numpy(float)
        for c in p.sum().sort_values(ascending=False).index:
            ax.fill_betweenx(y, left, left + p[c].to_numpy(), color=colours[c], alpha=0.9, lw=0, label=_s(c), step="mid")
            left += p[c].to_numpy()
        ax.set_ylim(y.max() + (y[1] - y[0]) / 2, 0)
        ax.set_xlim(0, 1)
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.set_ylabel(_L("downhole depth (m)", "عمق درون‌چاهی (متر)", lang))
        ax.set_xlabel(_L("share of logged metres", "سهم متراژ لاگ‌شده", lang))
        ax.grid(False)
        ax.legend(fontsize=7, loc="lower left", bbox_to_anchor=(1.0, 0.0), frameon=False)
        label = field_label or field
        _head(ax, _s(f"{label} with depth" if lang != "fa" else f"{label} با عمق"), lang=lang, theme=theme)
        return fig


def physical_by_category(phys: pd.DataFrame, field: str, variable: str, field_label: str | None = None, lang="en", theme=T.IVORY, min_n: int = 5):
    if phys is None or phys.empty or field not in phys:
        return None
    d = phys[(phys["variable"] == variable)][[field, "value"]].dropna()
    counts = d[field].value_counts()
    d = d[d[field].isin(counts[counts >= min_n].index)]
    if d[field].nunique() < 2:
        return None
    with styled(theme):
        med = d.groupby(field)["value"].median().sort_values()
        cats = list(med.index)
        colours = T.cat_colours(category_order_simple(d, field))
        fig, ax = _new(5.8, 0.46 * len(cats) + 1.6, theme)
        ax = ax[0, 0]
        data = [d.loc[d[field] == c, "value"].to_numpy(float) for c in cats]
        parts = ax.violinplot(data, orientation="horizontal", showextrema=False, widths=0.8)
        for c, body in zip(cats, parts["bodies"]):
            body.set_facecolor(colours[c])
            body.set_edgecolor(colours[c])
            body.set_alpha(0.45)
        ax.boxplot(data, orientation="horizontal", widths=0.18, showfliers=False, patch_artist=True,
                   boxprops=dict(facecolor=theme.panel, edgecolor=theme.ink, lw=0.8), medianprops=dict(color=theme.accent, lw=2),
                   whiskerprops=dict(color=theme.ink, lw=0.8), capprops=dict(color=theme.ink, lw=0.8))
        ax.set_yticks(range(1, len(cats) + 1))
        ax.set_yticklabels([_s(x) for x in cats])
        ax.grid(axis="y", visible=False)
        trans = ax.get_yaxis_transform()
        for k, c in enumerate(cats):
            ax.text(1.005, k + 1, f"P50 {med[c]:.3g} · n {counts[c]}", transform=trans, va="center", fontsize=7, color=theme.muted)
        names = {"CR %": ("Core recovery (%)", "بازیافت مغزه (درصد)"), "RQD %": ("RQD (%)", "RQD (درصد)"),
                 "Density g/cm³": ("Density (g/cm³)", "چگالی (گرم بر سانتی‌متر مکعب)")}
        en, fa_ = names.get(variable, (variable, variable))
        ax.set_xlabel(_L(en, fa_, lang))
        label = field_label or field
        _head(ax, _s(f"{en} by {label}" if lang != "fa" else f"{fa_} به تفکیک {label}"), lang=lang, theme=theme)
        return fig


def field_association(smp: pd.DataFrame, fields: dict, lang="en", theme=T.IVORY):
    from ..analysis.categorical import cramers_v
    names = [f for f in fields if smp[f].notna().sum() > 30]
    if len(names) < 2:
        return None
    with styled(theme):
        k = len(names)
        m = np.full((k, k), np.nan)
        for i in range(k):
            for j in range(i):
                m[i, j] = cramers_v(smp, names[i], names[j])
        fig, ax = _new(0.7 * k + 3.2, 0.6 * k + 1.6, theme)
        ax = ax[0, 0]
        im = ax.imshow(m, cmap=_seqmap(theme), vmin=0, vmax=1)
        lab = [_s(fields[f][1] if lang == "fa" else fields[f][0]) for f in names]
        ax.set_xticks(range(k))
        ax.set_xticklabels(lab, rotation=35, ha="right")
        ax.set_yticks(range(k))
        ax.set_yticklabels(lab)
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        for i in range(k):
            for j in range(i):
                if np.isfinite(m[i, j]):
                    ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center", fontsize=7.5, color=_on(im.cmap(im.norm(m[i, j]))))
        cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cb.set_label("Cramér's V")
        cb.outline.set_visible(False)
        _head(ax, _L("How strongly do the logged attributes coincide?", "میزان هم‌رخدادی ویژگی‌های توصیفی", lang),
              _L("Cramér's V: 0 independent · 1 one attribute predicts the other", "V کرامر: ۰ مستقل · ۱ یکی دیگری را کاملاً پیش‌بینی می‌کند", lang), lang, theme)
        return fig


def strip_log(smp: pd.DataFrame, hole: str, analytes: list[str], fields: dict, units: dict, lang="en", theme=T.IVORY):
    d = smp[smp["hole_id"] == hole].sort_values("from_m")
    if d.empty:
        return None
    flist = [f for f, v in fields.items() if v[2] == "logging" and d[f].notna().any()]
    flist = (flist + [f for f, v in fields.items() if v[2] == "attribute" and d[f].notna().any()])[:4]
    analytes = [a for a in analytes if a in d and d[a].notna().any()][:3]
    if not analytes:
        return None
    with styled(theme):
        ncol = len(flist) + len(analytes)
        ratios = [0.85] * len(flist) + [1.6] * len(analytes)
        fig = Figure(figsize=(1.15 * len(flist) + 2.2 * len(analytes) + 0.8, 7.2), layout="constrained", facecolor=theme.bg)
        fig.get_layout_engine().set(rect=(0, 0.15, 1, 0.85), w_pad=0.04)    # bottom band keeps the category legends
        axes = fig.subplots(1, ncol, sharey=True, gridspec_kw={"width_ratios": ratios})
        axes = np.atleast_1d(axes)
        top, bottom = float(d["from_m"].min()), float(d["to_m"].max())
        for ax, f in zip(axes, flist):
            ax.set_facecolor(theme.panel)
            colours = T.cat_colours(category_order_simple(smp, f))
            for r in d[["from_m", "to_m", f]].itertuples(index=False):
                if pd.notna(r[2]):
                    ax.add_patch(matplotlib.patches.Rectangle((0, r[0]), 1, r[1] - r[0], color=colours.get(r[2], theme.axis), lw=0))
            ax.set_xlim(0, 1)
            ax.set_xticks([])
            ax.grid(False)
            import textwrap
            ttl = str(fields[f][1] if lang == "fa" else fields[f][0]).replace("/", "/ ")
            ax.set_title(_s("\n".join(textwrap.wrap(ttl, 12))), fontsize=7.5, loc="center")
            present = [c for c in colours if c in set(d[f].dropna())]
            leg = ax.legend(handles=[Patch(color=colours[c], label=_s(c)) for c in present], fontsize=6, loc="upper center",
                            bbox_to_anchor=(0.5, -0.01), ncol=1, frameon=False, handlelength=1, borderaxespad=0)
            leg.set_in_layout(False)
        for k, (ax, a) in enumerate(zip(axes[len(flist):], analytes)):
            ax.set_facecolor(theme.panel)
            v = d[a].where(d[a] > 0)
            y = np.repeat(np.c_[d["from_m"], d["to_m"]], 1, axis=0).ravel()
            x = np.repeat(v.to_numpy(), 2)
            ax.fill_betweenx(y, np.nanmin(v) * 0.8 if v.notna().any() else 1e-3, x, color=T.CAT[k], alpha=0.25, lw=0)
            ax.plot(x, y, color=T.CAT[k], lw=1.1)
            ax.set_xscale("log")
            _logfmt(ax, "x", dense=False)
            ax.tick_params(axis="x", labelsize=7)
            ax.set_title(f"{a}\n({units.get(a, '')})", fontsize=8, loc="center")
            ax.grid(True, which="major", axis="x")
        axes[0].set_ylim(bottom, top)
        axes[0].set_ylabel(_L("downhole depth (m)", "عمق درون‌چاهی (متر)", lang))
        fig.suptitle(_L(f"Hole {hole} — logged geology and grade", f"گمانهٔ {hole} — زمین‌شناسی ثبت‌شده و عیار", lang),
                     fontsize=10, fontweight="semibold", color=theme.ink, x=0.99 if lang == "fa" else 0.01, ha="right" if lang == "fa" else "left")
        return fig
