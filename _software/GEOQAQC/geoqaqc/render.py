# -*- coding: utf-8 -*-
"""Draw a figures.Figure with matplotlib (object API only -- no pyplot, so it
runs headless and inside Tk alike).

Two themes, one design: 'dark' for the application (the GEOVALID navy) and
'light' for print. Series slots s1-s3 and the status set were checked with the
dataviz palette validator against both surfaces (all-pairs CVD and normal
vision pass; aqua sits below 3:1 on white, so it is never the only carrier of
meaning and always has a legend entry or a label).
"""

from __future__ import annotations

import io
import itertools
import math
import re

import matplotlib
from matplotlib import font_manager
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure as MplFigure
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator, MaxNLocator, NullFormatter
from matplotlib.patches import FancyBboxPatch, Patch
from matplotlib.transforms import blended_transform_factory

_STATUS = {"good": "#0ca30c", "warn": "#fab219", "serious": "#ec835a",
           "crit": "#d03b3b"}


def _theme(bg, panel, fg, fg2, muted, grid, spine, s1, s2, s3, none_cell, good_cell):
    t = {"bg": bg, "panel": panel, "fg": fg, "fg2": fg2, "muted": muted,
         "grid": grid, "spine": spine, "ref": fg2, "s1": s1, "s2": s2, "s3": s3,
         "none": none_cell, "goodcell": good_cell}
    t.update(_STATUS)
    t.update({"okband": (_STATUS["good"], 0.08), "warnband": (_STATUS["warn"], 0.10),
              "critband": (_STATUS["crit"], 0.08)})
    rating = {"EXCELLENT": "good", "VERY GOOD": "good", "GOOD": "good",
              "POOR": "warn", "BAD": "serious", "VERY BAD": "crit", "NO DATA": "none"}
    sev = {"CRITICAL": "crit", "MATERIAL": "serious", "MINOR": "warn",
           "NONE_SEV": "none"}
    batch = {"PASS": "good", "WARN": "warn", "FAIL": "crit", "NONE": "none"}
    for table in (rating, sev, batch):
        for k, v in table.items():
            t[k] = t[v]
    return t


THEMES = {
    "light": _theme("#ffffff", "#ffffff", "#0b0b0b", "#52514e", "#898781",
                    "#e7e6e1", "#c3c2b7", "#2a78d6", "#eb6834", "#1baf7a", "#eeede8",
                    "#d4ecd4"),
    "dark": _theme("#161c24", "#161c24", "#dce4ee", "#aab6c4", "#7d8a9b",
                   "#232d3a", "#33404f", "#3987e5", "#d95926", "#199e70", "#232d3a",
                   "#1e4a2c"),
}

_DASH = {None: "-", "dash": (0, (4, 3)), "dot": (0, (1, 2.5))}
_FONTS = ["Segoe UI", "Inter", "Helvetica Neue", "Arial", "Liberation Sans",
          "DejaVu Sans"]


def _pick_font():
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in _FONTS:
        if name in have:
            return name
    return "DejaVu Sans"


FONT = _pick_font()
matplotlib.rcParams.update({
    "font.family": [FONT, "DejaVu Sans"],
    "svg.fonttype": "path",          # identical glyphs in the browser, PDF and Word
    "axes.unicode_minus": True,
    "savefig.dpi": 200,
})


def _c(th, token):
    v = th.get(token, token)
    return v[0] if isinstance(v, tuple) else v


def _alpha(th, token, default=1.0):
    v = th.get(token)
    return v[1] if isinstance(v, tuple) else default


def _luminance(hexcol):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _ink_on(th, fill):
    """White on a dark fill, near-black on a light one (warning, empty cells)."""
    return "#0b0b0b" if _luminance(fill) > 0.42 else "#ffffff"


# ===========================================================================
def draw_figure(fig, mfig, theme="light"):
    """Draw fig into the matplotlib figure mfig. Returns {artist: ids} for the
    point layers that carry sample IDs (the app uses it for hover tooltips)."""
    th = THEMES[theme]
    mfig.clear()
    mfig.set_facecolor(th["bg"])
    w, h = mfig.get_size_inches()
    if fig.kind == "matrix":
        _draw_matrix(fig, mfig, th, w, h)
        return {}

    top = 0.50 + (0.20 if fig.subtitle else 0.0)
    two_line = fig.xticks and (fig.xticks[2] or any("\n" in str(x) for x in fig.xticks[1]))
    bottom = 0.50 + (0.28 if two_line else 0.0) + 0.16 * len(fig.notes)
    left, right = 0.80, (1.45 if fig.legend_loc == "outside" else 0.32)
    ax = mfig.add_axes([left / w, bottom / h, max(0.1, 1 - (left + right) / w),
                        max(0.1, 1 - (top + bottom) / h)])
    _title(fig, mfig, th, left, w, h)
    _notes(fig, mfig, th, left, w, h)
    ax.set_facecolor(th["panel"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(th["spine"])
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=th["muted"], labelsize=7.2, length=3, width=0.6)
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_color(th["fg2"])
    ax.grid(True, color=th["grid"], linewidth=0.6)
    ax.set_axisbelow(True)
    if fig.xlog:
        ax.set_xscale("log")
    if fig.ylog:
        ax.set_yscale("log")
    ax.set_xlabel(fig.xlabel, color=th["fg2"], fontsize=7.8, labelpad=4)
    ax.set_ylabel(fig.ylabel, color=th["fg2"], fontsize=7.8, labelpad=4)

    def keep(x, y):
        if x is None or y is None:
            return False
        if fig.xlog and x <= 0:
            return False
        if fig.ylog and y <= 0:
            return False
        return True

    hover, handles = {}, []
    xform_h = blended_transform_factory(ax.transAxes, ax.transData)
    xform_v = blended_transform_factory(ax.transData, ax.transAxes)
    has_data = False
    for L in fig.layers:
        k = L["kind"]
        if k == "band":
            ax.axhspan(L["y0"], L["y1"], color=_c(th, L["color"]),
                       alpha=_alpha(th, L["color"], 0.1), lw=0, zorder=0.5)
            if L["label"]:
                handles.append((Patch(color=_c(th, L["color"]),
                                      alpha=_alpha(th, L["color"], 0.1) * 3), L["label"]))
        elif k == "hline":
            if fig.ylog and L["y"] <= 0:
                continue
            ax.axhline(L["y"], color=_c(th, L["color"]), lw=L["width"],
                       ls=_DASH[L["dash"]], zorder=2.2)
            if L["text"]:
                ax.text(0.995, L["y"], L["text"], transform=xform_h, ha="right",
                        va="bottom", fontsize=6.4, color=th["fg2"], zorder=4,
                        bbox=dict(boxstyle="square,pad=0.15", fc=th["panel"],
                                  ec="none", alpha=0.85))
            if L["label"]:
                handles.append((Line2D([], [], color=_c(th, L["color"]), lw=L["width"],
                                       ls=_DASH[L["dash"]]), L["label"]))
        elif k == "vline":
            if fig.xlog and L["x"] <= 0:
                continue
            ax.axvline(L["x"], color=_c(th, L["color"]), lw=L["width"],
                       ls=_DASH[L["dash"]], zorder=1.5)
            if L["text"]:
                ax.text(L["x"], 0.985, f" {L['text']}", transform=xform_v, ha="left",
                        va="top", rotation=90, fontsize=6.2, color=th["fg2"], zorder=4)
        elif k == "line":
            pts = [(x, y) for x, y in zip(L["xs"], L["ys"]) if keep(x, y)]
            if pts:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], color=_c(th, L["color"]),
                        lw=L["width"], ls=_DASH[L["dash"]], solid_capstyle="round",
                        solid_joinstyle="round", zorder=2)
                has_data = True
            if L["label"]:
                handles.append((Line2D([], [], color=_c(th, L["color"]), lw=L["width"],
                                       ls=_DASH[L["dash"]]), L["label"]))
        elif k == "points":
            rows = [(x, y, i) for x, y, i in zip(L["xs"], L["ys"],
                                                 L["ids"] or itertools.repeat(None))
                    if keep(x, y)]
            marker = {"o": "o", "s": "s", "+": "P"}.get(L["marker"], "o")
            if rows:
                art = ax.scatter([r[0] for r in rows], [r[1] for r in rows],
                                 s=(2 * L["size"]) ** 2, c=_c(th, L["color"]),
                                 marker=marker, edgecolors=th["panel"], linewidths=1.0,
                                 zorder=3)
                if L["ids"]:
                    hover[art] = [r[2] for r in rows]
                has_data = True
            if L["label"]:
                handles.append((Line2D([], [], color=_c(th, L["color"]), marker=marker,
                                       ls="none", markersize=L["size"] * 1.9,
                                       markeredgecolor=th["panel"]), L["label"]))
        elif k == "bars":
            bottom_v = L["bottom"] or [0.0] * len(L["xs"])
            cols = [_c(th, c) for c in L["colors"]]
            ax.bar(L["xs"], L["hs"], L["width"], bottom=bottom_v, color=cols,
                   edgecolor=th["panel"], linewidth=1.4, zorder=2)
            has_data = has_data or bool(L["xs"])
            if L["texts"]:
                inside = getattr(fig, "inside_text", False)
                for x, hh, b, t, col in zip(L["xs"], L["hs"], bottom_v, L["texts"], cols):
                    if not t:
                        continue
                    if inside:
                        ax.text(x, b + hh / 2.0, t, ha="center", va="center",
                                fontsize=6.8, color=_ink_on(th, col), zorder=4)
                    else:
                        ax.text(x, b + hh, t, ha="center",
                                va="bottom" if hh >= 0 else "top", fontsize=6.8,
                                color=th["fg2"], zorder=4)
            if L["label"]:
                handles.append((Patch(color=cols[0] if cols else th["s1"]), L["label"]))
        elif k == "text":
            if keep(L["x"], L["y"]):
                ax.annotate(L["s"], (L["x"], L["y"]), xytext=L.get("offset", (0, 0)),
                            textcoords="offset points", ha=L["ha"], va=L["va"],
                            fontsize=L["size"], color=_c(th, L["color"]),
                            fontweight=L["weight"], zorder=4)
    _ranges(fig, ax)
    _tick_style(fig, ax)
    if fig.xticks:
        pos, labels, rot = fig.xticks
        ax.set_xticks(pos)
        ax.set_xticklabels(labels, rotation=rot, ha="right" if rot else "center",
                           fontsize=6.8, color=th["fg2"])
        ax.grid(False, axis="x")
    if len(handles) >= 2:
        where = ({"loc": "upper left", "bbox_to_anchor": (1.02, 1.0)}
                 if fig.legend_loc == "outside" else {"loc": fig.legend_loc})
        leg = ax.legend([h_ for h_, _ in handles], [l_ for _, l_ in handles],
                        fontsize=6.6, frameon=True, facecolor=th["panel"],
                        edgecolor="none", framealpha=0.88, borderpad=0.5,
                        handlelength=1.6, **where)
        for t in leg.get_texts():
            t.set_color(th["fg2"])
    if not has_data and fig.notes:
        ax.text(0.5, 0.5, fig.notes[0][0], transform=ax.transAxes, ha="center",
                va="center", fontsize=8, color=th["muted"])
    return hover


def _plain(v, _pos=None):
    if v <= 0:
        return ""
    s = f"{v:.6f}".rstrip("0").rstrip(".") if v < 1 else f"{v:,.0f}" if v >= 1000 else f"{v:g}"
    return s


def _tick_style(fig, ax):
    """Plain numbers on log axes (0.01, 0.1, 1 rather than 10^-2) and whole
    numbers on sequence axes."""
    for log, axis, lim in ((fig.xlog, ax.xaxis, ax.get_xlim()),
                           (fig.ylog, ax.yaxis, ax.get_ylim())):
        if log:
            lo, hi = sorted(lim)
            decades = math.log10(hi / lo) if lo > 0 and hi > 0 else 3
            # a range shorter than ~1.5 decades has at most one power of ten
            # in it, so label 1-2-5 (or every step) inside each decade
            subs = ((1.0,) if decades >= 1.5 else (1.0, 2.0, 5.0) if decades >= 0.6
                    else tuple(float(i) for i in range(1, 10)))
            axis.set_major_locator(LogLocator(base=10.0, subs=subs, numticks=12))
            axis.set_major_formatter(FuncFormatter(_plain))
            axis.set_minor_formatter(NullFormatter())
    if not fig.xlog and not fig.xticks:
        xs = [x for L in fig.layers if L["kind"] in ("points", "line")
              for x in L["xs"] if x is not None]
        if xs and all(float(x).is_integer() for x in xs):
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))


def _title(fig, mfig, th, left, w, h):
    mfig.text(left / w, 1 - 0.24 / h, fig.title, ha="left", va="baseline",
              fontsize=10, fontweight="bold", color=th["fg"])
    if fig.subtitle:
        mfig.text(left / w, 1 - 0.45 / h, fig.subtitle, ha="left", va="baseline",
                  fontsize=7.4, color=th["fg2"])


def _notes(fig, mfig, th, left, w, h):
    n = len(fig.notes)
    for i, (text, color) in enumerate(fig.notes):
        mfig.text(left / w, (0.12 + 0.16 * (n - 1 - i)) / h, text, ha="left",
                  va="baseline", fontsize=6.8, color=_c(th, color))


def _ranges(fig, ax):
    def fix(r, log, cur):
        lo, hi = r
        if log:
            if hi is None or hi <= 0:
                return None
            if lo is None or lo <= 0:
                lo = min(cur[0], hi / 10.0) if cur[0] > 0 else hi / 1000.0
        return lo, hi
    if fig.xr:
        r = fix(fig.xr, fig.xlog, ax.get_xlim())
        if r:
            ax.set_xlim(*r)
    if fig.yr:
        r = fix(fig.yr, fig.ylog, ax.get_ylim())
        if r and r[0] != r[1]:
            ax.set_ylim(*r)


_GOOD_LEVELS = {"EXCELLENT", "VERY GOOD", "GOOD", "PASS"}


def _cell(th, level):
    """Matrix cell fill: passing cells are a quiet tint so that warnings and
    failures stand out; everything else takes its status colour."""
    if level in _GOOD_LEVELS:
        return th["goodcell"]
    return _c(th, level) if level in th else th["none"]


def _draw_matrix(fig, mfig, th, w, h):
    m = fig.matrix_data
    nr, nc = len(m["rows"]), len(m["cols"])
    top = 0.50 + (0.20 if fig.subtitle else 0.0) + 0.36
    bottom = 0.42
    left, right = 0.95, 0.2
    ax = mfig.add_axes([left / w, bottom / h, 1 - (left + right) / w,
                        max(0.05, 1 - (top + bottom) / h)])
    _title(fig, mfig, th, left, w, h)
    ax.set_xlim(0, max(nc, 1))
    ax.set_ylim(max(nr, 1), 0)
    ax.axis("off")
    gap = 0.045
    for i in range(nr):
        ax.text(-0.12, i + 0.5, m["row_labels"][i], ha="right", va="center",
                fontsize=7.4, color=th["fg"], fontweight="bold")
        for j in range(nc):
            lvl = m["levels"][i][j]
            fill = _cell(th, lvl)
            ax.add_patch(FancyBboxPatch((j + gap, i + gap), 1 - 2 * gap, 1 - 2 * gap,
                                        boxstyle="round,pad=0,rounding_size=0.10",
                                        facecolor=fill, edgecolor="none",
                                        mutation_aspect=1.0))
            txt = (m["texts"][i][j] if m["texts"] else "") or ""
            if txt:
                ax.text(j + 0.5, i + 0.52, txt, ha="center", va="center",
                        fontsize=6.6 if nc > 10 else 7, color=_ink_on(th, fill))
    for j in range(nc):
        ax.text(j + 0.5, -0.12, m["col_labels"][j], ha="center", va="bottom",
                fontsize=6.4 if nc > 10 else 6.9, color=th["fg2"],
                rotation=60 if nc > 10 else 0)
    if m.get("legend"):
        hs = [Patch(color=_cell(th, k)) for k, _ in m["legend"]]
        leg = mfig.legend(hs, [lab for _, lab in m["legend"]], loc="lower left",
                          bbox_to_anchor=(left / w, 0.02), ncol=len(hs), fontsize=6.8,
                          frameon=False, handlelength=1.2, columnspacing=1.4)
        for t in leg.get_texts():
            t.set_color(th["fg2"])


# ===========================================================================
_ID = re.compile(r'id="([^"]+)"')
_SEQ = itertools.count(1)


def _prefix_ids(svg):
    """Inline SVGs in one HTML page share one id namespace; prefix every id so
    the glyph and clip-path definitions of one chart never resolve to another."""
    p = f"g{next(_SEQ)}-"
    ids = set(_ID.findall(svg))
    if not ids:
        return svg
    svg = _ID.sub(lambda m: f'id="{p}{m.group(1)}"', svg)
    svg = re.sub(r'(xlink:href|href)="#([^"]+)"',
                 lambda m: f'{m.group(1)}="#{p}{m.group(2)}"' if m.group(2) in ids
                 else m.group(0), svg)
    svg = re.sub(r"url\(#([^)]+)\)",
                 lambda m: f"url(#{p}{m.group(1)})" if m.group(1) in ids else m.group(0),
                 svg)
    return svg


def _mfig(fig, size):
    mf = MplFigure(figsize=size or fig.size or (7.2, 3.6))
    FigureCanvasAgg(mf)
    return mf


def to_svg(fig, theme="light", size=None):
    mf = _mfig(fig, size)
    draw_figure(fig, mf, theme)
    buf = io.StringIO()
    mf.savefig(buf, format="svg", facecolor=THEMES[theme]["bg"])
    s = buf.getvalue()
    return _prefix_ids(s[s.index("<svg"):])


def to_png(fig, theme="light", size=None, dpi=200):
    mf = _mfig(fig, size)
    draw_figure(fig, mf, theme)
    buf = io.BytesIO()
    mf.savefig(buf, format="png", dpi=dpi, facecolor=THEMES[theme]["bg"])
    return buf.getvalue()
