# -*- coding: utf-8 -*-
"""Chart descriptions, independent of any drawing library.

A builder turns one analysis record into a Figure -- a list of layers in
data units plus colour TOKENS ('s1', 'crit', 'GOOD', ...). render.py draws
the same Figure in the dark app theme or the light print theme, so a chart
looks the same in the program, in the HTML report and in Word.

Colour roles follow one rule each: categorical slots s1-s3 identify series;
the status set (good / warn / serious / crit) is reserved for pass, warning
and failure and always comes with a legend entry or a label; reference
lines (certified value, 1:1) are ink, never a series colour.
"""

from __future__ import annotations

from .core import RATING_ORDER, R_NA, T_CDUP, T_FDUP, T_PDUP, fmt_num, mean
from .protocol import DEFAULT_CRITERIA, rate

SEP = " · "
_DUP_CRIT = {T_FDUP: "fdup_hard90", T_CDUP: "cdup_hard90", T_PDUP: "pdup_hard90"}
_DUP_SHORT = {T_FDUP: "Field duplicates", T_CDUP: "Coarse duplicates",
              T_PDUP: "Pulp duplicates"}
_BLANK_SHORT = {"BLANK": "Blanks", "COARSE BLANK": "Coarse blanks",
                "PULP BLANK": "Pulp blanks"}


class Figure:
    """Renderer-neutral chart description."""

    def __init__(self, title="", subtitle="", xlabel="", ylabel="", kind="xy"):
        self.title = title
        self.subtitle = subtitle
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.kind = kind
        self.xlog = False
        self.ylog = False
        self.layers = []
        self.notes = []
        self.xr = None
        self.yr = None
        self.xticks = None
        self.matrix_data = None
        self.size = None            # preferred (w, h) in inches for the report
        self.legend_loc = "best"    # or "outside" (a column right of the plot)
        self.inside_text = False    # bar labels inside stacked segments

    # -- layers ------------------------------------------------------------
    def points(self, xs, ys, color="s1", size=3.4, label=None, marker="o", ids=None):
        self.layers.append({"kind": "points", "xs": list(xs), "ys": list(ys),
                            "color": color, "size": size, "label": label,
                            "marker": marker, "ids": list(ids) if ids else None})

    def line(self, xs, ys, color="s1", width=2.0, dash=None, label=None):
        self.layers.append({"kind": "line", "xs": list(xs), "ys": list(ys),
                            "color": color, "width": width, "dash": dash,
                            "label": label})

    def hline(self, y, color="ref", width=1.0, dash=None, label=None, text=None):
        if y is None:
            return
        self.layers.append({"kind": "hline", "y": y, "color": color, "width": width,
                            "dash": dash, "label": label, "text": text})

    def vline(self, x, color="ref", width=1.0, dash=None, label=None, text=None):
        if x is None:
            return
        self.layers.append({"kind": "vline", "x": x, "color": color, "width": width,
                            "dash": dash, "label": label, "text": text})

    def band(self, y0, y1, color="okband", label=None):
        if y0 is None or y1 is None:
            return
        self.layers.append({"kind": "band", "y0": y0, "y1": y1, "color": color,
                            "label": label})

    def bars(self, xs, hs, colors="s1", width=0.6, bottom=None, label=None,
             texts=None):
        n = len(xs)
        cols = colors if isinstance(colors, (list, tuple)) else [colors] * n
        self.layers.append({"kind": "bars", "xs": list(xs), "hs": list(hs),
                            "colors": list(cols), "width": width,
                            "bottom": list(bottom) if bottom else None,
                            "label": label, "texts": list(texts) if texts else None})

    def text(self, x, y, s, color="fg2", ha="left", va="center", size=7.2,
             weight="normal", offset=(0, 0)):
        self.layers.append({"kind": "text", "x": x, "y": y, "s": s, "color": color,
                            "ha": ha, "va": va, "size": size, "weight": weight,
                            "offset": offset})

    def note(self, text, color="muted"):
        if text:
            self.notes.append((text, color))

    def set_range(self, xr=None, yr=None):
        if xr is not None:
            self.xr = xr
        if yr is not None:
            self.yr = yr

    def set_xticks(self, pos, labels, rotation=0):
        self.xticks = (list(pos), list(labels), rotation)

    @classmethod
    def matrix(cls, title, rows, cols, levels, texts=None, subtitle="",
               row_labels=None, col_labels=None, legend=None):
        """levels[i][j]: a colour token per cell (rating, severity or batch
        status); texts[i][j]: the label printed in the cell."""
        f = cls(title, subtitle, kind="matrix")
        f.matrix_data = {"rows": list(rows), "cols": list(cols),
                         "levels": levels, "texts": texts,
                         "row_labels": row_labels or list(rows),
                         "col_labels": col_labels or list(cols),
                         "legend": legend or []}
        f.size = (7.2, 0.95 + 0.36 * len(rows))
        return f


def _pos(vals):
    return [v for v in vals if v is not None and v > 0]


def _robust_y(f, ys, floor):
    """Symmetric y-range from the 2nd-98th percentile, so one pair at the
    detection limit does not flatten everything else; clipped points are
    counted in a note."""
    v = sorted(abs(y) for y in ys if y is not None)
    if len(v) < 10:
        return
    lim = max(floor, v[int(0.98 * (len(v) - 1))] * 1.15)
    out = sum(1 for y in ys if y is not None and abs(y) > lim)
    if out:
        f.set_range(yr=(-lim, lim))
        f.note(f"{out} point(s) beyond +/-{lim:.0f} % are outside the plot "
               f"(listed in the table)")


_TYPE_LABEL = {"CRM": "CRM", "BLANK": "Blank", "FIELD DUP": "Field dup",
               "COARSE DUP": "Coarse dup", "PULP DUP": "Pulp dup"}


def _limits(C, key):
    return (C or DEFAULT_CRITERIA)[key]["cuts"]


# ===========================================================================
#  CRM
# ===========================================================================
def fig_crm_control(rec, S):
    f = Figure(f"CRM control chart{SEP}{rec['crm']}{SEP}{rec['element']}",
               "Each result in analytical order against the certified value",
               "insertion sequence",
               f"measured {rec['element']}" + (f" ({rec['unit']})" if rec.get("unit") else ""))
    pts = rec["points"]
    xs = list(range(1, len(pts) + 1))
    ys = [p["value"] for p in pts]
    ids = [p["sample"] for p in pts]
    cert, sd = rec.get("cert"), rec.get("eff_sd")
    kw, kf = S["k_warn"], S["k_fail"]
    if cert is not None and sd:
        f.band(cert - kw * sd, cert + kw * sd, "okband")
        f.hline(cert, "fg", 1.4, None, "certified", f"certified {fmt_num(cert)}")
        f.hline(cert + kw * sd, "warn", 1.0, "dash", None, f"+{kw:g} SD")
        f.hline(cert - kw * sd, "warn", 1.0, "dash", None, f"-{kw:g} SD")
        f.hline(cert + kf * sd, "crit", 1.0, "dash", None, f"+{kf:g} SD")
        f.hline(cert - kf * sd, "crit", 1.0, "dash", None, f"-{kf:g} SD")
        lo = min(ys + [cert - (kf + 0.8) * sd])
        hi = max(ys + [cert + (kf + 0.8) * sd])
        f.set_range(yr=(lo, hi))
    f.line(xs, ys, "muted", 1.0)
    groups = {"ok": ([], [], []), "warn": ([], [], []), "crit": ([], [], [])}
    for x, p in zip(xs, pts):
        z = p["z"]
        g = ("crit" if z is not None and abs(z) > kf else
             "warn" if z is not None and abs(z) > kw else "ok")
        groups[g][0].append(x)
        groups[g][1].append(p["value"])
        groups[g][2].append(p["sample"])
    f.points(groups["ok"][0], groups["ok"][1], "s1", label="within limits",
             ids=groups["ok"][2])
    if groups["warn"][0]:
        f.points(groups["warn"][0], groups["warn"][1], "warn", 4.0,
                 f"beyond {kw:g} SD", ids=groups["warn"][2])
    if groups["crit"][0]:
        f.points(groups["crit"][0], groups["crit"][1], "crit", 4.4,
                 f"beyond {kf:g} SD", "s", ids=groups["crit"][2])
    if rec.get("bias") is not None:
        f.note(f"n = {rec['n']}   mean bias {rec['bias']:+.2f} %   observed RSD "
               f"{rec['rsd_pct']:.2f} %   SD source: {rec.get('sd_source', '-')}")
    del ids
    return f


def fig_crm_bias(rec, S, C=None):
    cuts = _limits(C, "crm_bias")
    f = Figure(f"CRM bias{SEP}{rec['crm']}{SEP}{rec['element']}",
               "Relative deviation of every result from the certified value",
               "insertion sequence", "bias %")
    pts = rec["points"]
    xs = list(range(1, len(pts) + 1))
    ys = [p["bias"] for p in pts]
    good, bad = cuts[2], cuts[4]
    f.band(-good, good, "okband")
    f.hline(0, "fg", 1.2)
    for v, col in ((good, "warn"), (-good, "warn"), (bad, "crit"), (-bad, "crit")):
        f.hline(v, col, 1.0, "dash", None, f"{v:+g} %")
    if rec.get("bias") is not None:
        f.hline(rec["bias"], "s2", 1.8, None, "mean bias", f"mean {rec['bias']:+.2f} %")
    f.line(xs, ys, "muted", 1.0)
    f.points(xs, ys, "s1", label="result", ids=[p["sample"] for p in pts])
    return f


def fig_crm_zhist(rec, S):
    f = Figure(f"Z-score distribution{SEP}{rec['crm']}{SEP}{rec['element']}",
               "Standard deviations from the certified value",
               "z-score", "count")
    zs = [p["z"] for p in rec["points"] if p["z"] is not None]
    if not zs:
        f.note("no z-scores: the certificate carries no standard deviation")
        return f
    lo, hi = min(-4.0, min(zs)), max(4.0, max(zs))
    nb = 16
    step = (hi - lo) / nb
    counts = [0] * nb
    for z in zs:
        counts[min(nb - 1, max(0, int((z - lo) / step)))] += 1
    xs = [lo + (i + 0.5) * step for i in range(nb)]
    cols = ["s1" if abs(x) <= S["k_warn"] else "warn" if abs(x) <= S["k_fail"]
            else "crit" for x in xs]
    f.bars(xs, counts, cols, width=step * 0.92)
    for k, col in ((S["k_warn"], "warn"), (S["k_fail"], "crit")):
        f.vline(k, col, 1.0, "dash")
        f.vline(-k, col, 1.0, "dash")
    f.set_range(xr=(lo, hi), yr=(0, max(counts) * 1.18 or 1))
    f.note(f"n = {len(zs)}   beyond {S['k_warn']:g} SD: {rec['warn_pct']:.1f} %   "
           f"beyond {S['k_fail']:g} SD: {rec['fail_pct']:.1f} %")
    return f


def fig_crm_cusum(rec, S, RB=None):
    f = Figure(f"CUSUM{SEP}{rec['crm']}{SEP}{rec['element']}",
               "Cumulative sum of z-scores: a sustained shift climbs out of the band",
               "insertion sequence", "cumulative z")
    cs = rec.get("cusum")
    if not cs:
        f.note("no z-scores: the certificate carries no standard deviation")
        return f
    xs = list(range(1, len(cs["hi"]) + 1))
    h = RB["cusum_h"] if RB is not None else 5.0
    f.band(-h, h, "okband")
    f.hline(h, "crit", 1.0, "dash", None, f"+h = {h:g}")
    f.hline(-h, "crit", 1.0, "dash", None, f"-h = {h:g}")
    f.hline(0, "fg", 1.0)
    f.line(xs, cs["hi"], "s1", 2.0, label="upper sum")
    f.line(xs, cs["lo"], "s2", 2.0, label="lower sum")
    if cs["signals"]:
        sx = [i + 1 for i in cs["signals"]]
        sy = [cs["hi"][i] if abs(cs["hi"][i]) >= abs(cs["lo"][i]) else cs["lo"][i]
              for i in cs["signals"]]
        f.points(sx, sy, "crit", 4.4, "signal", "s",
                 ids=[rec["points"][i]["sample"] for i in cs["signals"]])
    f.note(f"{len(cs['signals'])} signal(s)" if cs["signals"] else "no signal")
    return f


def fig_crm_batch(rec, S, C=None):
    good = _limits(C, "crm_bias")[2]
    f = Figure(f"CRM bias by batch{SEP}{rec['crm']}{SEP}{rec['element']}",
               "Mean bias of the results in each laboratory batch", "", "mean bias %")
    bb = [b for b in rec.get("batch_bias", []) if b["bias"] is not None]
    if not bb:
        f.note("no batch information")
        return f
    xs = list(range(1, len(bb) + 1))
    hs = [b["bias"] for b in bb]
    cols = ["crit" if (b["zmax"] or 0) > S["k_fail"] else "s1" for b in bb]
    f.band(-good, good, "okband")
    f.hline(0, "fg", 1.0)
    f.bars(xs, hs, cols, 0.6, label=None)
    f.set_xticks(xs, [b["batch"] for b in bb], 45 if len(bb) > 6 else 0)
    if any(c == "crit" for c in cols):
        f.points([], [], "crit", label=f"batch with a result beyond {S['k_fail']:g} SD")
        f.points([], [], "s1", label="other batches")
    return f


def fig_crm_drift(dr, el, S, C=None):
    good = _limits(C, "crm_bias")[2]
    f = Figure(f"Laboratory drift{SEP}{el}",
               "Bias of every CRM in analytical order, less that CRM's own mean "
               "bias, with the common trend",
               "rank in analytical sequence", "bias less the CRM's mean bias, %")
    f.band(-good, good, "okband")
    f.hline(0, "fg", 1.0)
    labels = []
    for _, _, lab in dr["series"]:
        if lab not in labels:
            labels.append(lab)
    for i, lab in enumerate(labels[:3]):
        pts = [(k, b) for k, (_, b, lb) in enumerate(dr["series"]) if lb == lab]
        f.points([k for k, _ in pts], [b for _, b in pts], f"s{i + 1}", 3.2, lab)
    if len(labels) > 3:
        pts = [(k, b) for k, (_, b, lb) in enumerate(dr["series"]) if lb in labels[3:]]
        f.points([k for k, _ in pts], [b for _, b in pts], "muted", 3.0, "other CRMs")
    n = dr["n"]
    f.line([0, n - 1], [dr["a"], dr["a"] + dr["slope"] * (n - 1)], "fg", 2.0,
           label="trend")
    f.note(f"change over the series {dr['total']:+.2f} %   p = {dr['p']:.4f}   "
           f"{'significant' if dr['sig'] else 'not significant'}", "crit" if dr["sig"] else "muted")
    return f


def fig_accuracy_curve(acc, el):
    f = Figure(f"Accuracy curve{SEP}{el}",
               "Mean measured value of each CRM against its certified value",
               "certified value", "mean measured value")
    pts = acc["points"]
    xs, ys = [p["cert"] for p in pts], [p["mean"] for p in pts]
    lo, hi = min(xs + ys), max(xs + ys)
    pad = (hi - lo) * 0.08 or hi * 0.1
    f.line([lo - pad, hi + pad], [lo - pad, hi + pad], "fg", 1.2, None, "1:1")
    if acc.get("b") is not None:
        f.line([lo - pad, hi + pad], [acc["a"] + acc["b"] * (lo - pad),
                                      acc["a"] + acc["b"] * (hi + pad)],
               "s2", 2.0, label="fitted line")
    f.points(xs, ys, "s1", 4.2, "CRM", ids=[p["crm"] for p in pts])
    for p in pts:
        f.text(p["cert"], p["mean"], p["crm"], "fg2", "left", "top", 6.8,
               offset=(6, -5))
    if acc.get("prop_bias_pct") is not None:
        f.note(f"slope {acc['b']:.4f} (proportional bias {acc['prop_bias_pct']:+.2f} %)"
               f"   intercept {fmt_num(acc['a'])}   {acc['n_crm']} CRMs")
    return f


def fig_coverage(cov, el):
    f = Figure(f"Grade coverage of the CRMs{SEP}{el}",
               "Cumulative distribution of routine grades and the certified values",
               el, "cumulative % of routine samples")
    q = [(p, v) for p, v in cov["quantiles"] if v is not None and v > 0]
    f.xlog = True
    if q:
        f.line([v for _, v in q], [p for p, _ in q], "s1", 2.0, label="routine samples")
    for lab, c in cov["certs"]:
        f.vline(c, "s2", 1.4, None, None, lab)
    if cov["certs"]:
        f.line([], [], "s2", 1.4, label="certified value of a CRM")
    for pct_ in sorted(cov["pcts"]):
        f.hline(pct_, "muted", 0.8, "dot", None, f"P{pct_:g}")
    f.set_range(yr=(0, 100))
    return f


# ===========================================================================
#  Blanks
# ===========================================================================
def fig_blank(rec, S):
    bt = _BLANK_SHORT.get(rec.get("btype", "BLANK"), "Blanks")
    f = Figure(f"{bt} control chart{SEP}{rec['element']}",
               f"Detection limit {fmt_num(rec['dl'])}; failure above "
               f"{S['k_dl']:g} x DL = {fmt_num(rec['limit'])}",
               "insertion sequence", f"{rec['element']}")
    pts = rec["points"]
    xs = list(range(1, len(pts) + 1))
    f.hline(rec["dl"], "muted", 1.0, "dot", None, "DL")
    f.hline(rec["limit"], "crit", 1.2, "dash", None, f"limit {fmt_num(rec['limit'])}")
    f.line(xs, [p["value"] for p in pts], "muted", 1.0)
    ok = [(x, p) for x, p in zip(xs, pts) if not p["fail"]]
    bad = [(x, p) for x, p in zip(xs, pts) if p["fail"]]
    f.points([x for x, _ in ok], [p["value"] for _, p in ok], "s1", label="pass",
             ids=[p["sample"] for _, p in ok])
    if bad:
        f.points([x for x, _ in bad], [p["value"] for _, p in bad], "crit", 4.4,
                 "fail", "s", ids=[p["sample"] for _, p in bad])
    f.note(f"n = {rec['n']}   failures {rec['n_fail']} ({rec['fail_pct']:.1f} %)   "
           f"worst {rec['max_ratio']:.1f} x DL")
    return f


def fig_blank_prev(rec, S):
    bt = _BLANK_SHORT.get(rec.get("btype", "BLANK"), "Blanks")
    f = Figure(f"{bt} against the preceding sample{SEP}{rec['element']}",
               "A rising cloud on the right is carry-over from rich samples",
               "preceding sample", "blank result")
    f.xlog = True
    pts = [p for p in rec["points"] if p["prev_value"] and p["prev_value"] > 0]
    ok = [p for p in pts if not p["fail"]]
    bad = [p for p in pts if p["fail"]]
    f.hline(rec["limit"], "crit", 1.2, "dash", None, "contamination limit")
    if rec.get("high_grade_cut"):
        f.vline(rec["high_grade_cut"], "muted", 1.0, "dot", None, "high grade")
    f.points([p["prev_value"] for p in ok], [p["value"] for p in ok], "s1", label="pass",
             ids=[p["sample"] for p in ok])
    if bad:
        f.points([p["prev_value"] for p in bad], [p["value"] for p in bad], "crit", 4.4,
                 "fail", "s", ids=[p["sample"] for p in bad])
    if rec.get("rho") is not None:
        f.note(f"Spearman rho {rec['rho']:.2f}   failure rate after high grade "
               f"{(rec.get('fail_after_high_pct') or 0):.0f} %, otherwise "
               f"{(rec.get('fail_other_pct') or 0):.0f} %")
    return f


# ===========================================================================
#  Duplicates
# ===========================================================================
def _dup_title(name, rec):
    return f"{name}{SEP}{_DUP_SHORT.get(rec.get('type'), rec.get('type', ''))}{SEP}{rec['element']}"


def fig_dup_scatter(rec, S):
    f = Figure(_dup_title("Original vs duplicate", rec),
               "Every pair against the 1:1 line", "original", "duplicate")
    f.xlog = f.ylog = bool(S["log_axis"])
    xs = [r["a"] for r in rec["rows"]]
    ys = [r["b"] for r in rec["rows"]]
    lo, hi = min(_pos(xs + ys) or [1e-3]), max(_pos(xs + ys) or [1.0])
    f.line([lo, hi], [lo, hi], "fg", 1.2, None, "1:1")
    for env, col in ((10, "good"), (20, "warn")):
        k = 1 + env / 100.0
        f.line([lo, hi], [lo * k, hi * k], col, 1.0, "dash", f"±{env} %")
        f.line([lo, hi], [lo / k, hi / k], col, 1.0, "dash")
    if rec.get("rma_b") is not None:
        a, b = rec["rma_a"], rec["rma_b"]
        f.line([lo, hi], [a + b * lo, a + b * hi], "s2", 2.0, label="RMA fit")
    f.points(xs, ys, "s1", label="pairs", ids=[r["dup"] for r in rec["rows"]])
    bits = [f"n = {rec['n']}"]
    if rec.get("r") is not None:
        bits.append(f"r = {rec['r']:.4f}")
    if rec.get("rma_b") is not None:
        bits.append(f"RMA slope = {rec['rma_b']:.4f}")
    f.note("   ".join(bits))
    return f


def fig_dup_rank_hard(rec, S, C=None):
    f = Figure(_dup_title("Ranked HARD", rec),
               "Half absolute relative difference of every pair, ranked",
               "cumulative % of pairs", "HARD %")
    hards = sorted(r["hard"] for r in rec["rows"] if r["hard"] is not None)
    n = len(hards)
    xs = [100.0 * (i + 0.5) / n for i in range(n)]
    p, v = rec["hard_pct_used"], rec["hard_p90"]
    crit = _limits(C, _DUP_CRIT.get(rec.get("type"), "fdup_hard90"))
    f.hline(crit[2], "warn", 1.0, "dash", None, f"acceptance {crit[2]:g} %")
    f.vline(p, "muted", 1.0, "dot")
    f.hline(v, "s2", 1.4, None, f"P{p:g} = {v:.1f} %", None)
    f.line(xs, hards, "s1", 2.0, label="HARD")
    f.set_range(xr=(0, 100))
    note = f"n = {n}   P{p:g} HARD = {v:.2f} %   median {rec['hard_median']:.2f} %"
    if rec.get("pooled_rp") is not None:
        note += f"   pooled relative precision {rec['pooled_rp']:.2f} %"
    f.note(note)
    return f


def fig_dup_mean_hrd(rec, S):
    f = Figure(_dup_title("Relative difference vs grade", rec),
               "Signed half relative difference against the pair mean",
               "pair mean", "HRD % (signed)")
    f.xlog = bool(S["log_axis"])
    xs = [r["mean"] for r in rec["rows"]]
    ys = [r["hrd"] for r in rec["rows"]]
    f.hline(0, "fg", 1.2)
    for v, col in ((10, "good"), (-10, "good"), (20, "warn"), (-20, "warn")):
        f.hline(v, col, 1.0, "dash", None, f"{v:+g} %")
    m = mean(ys)
    if m is not None:
        f.hline(m, "s2", 1.8, None, "mean HRD", f"mean {m:+.2f} %")
    f.points(xs, ys, "s1", label="pairs", ids=[r["dup"] for r in rec["rows"]])
    _robust_y(f, ys, 25.0)
    return f


def fig_dup_hist(rec, S):
    f = Figure(_dup_title("HARD distribution", rec), "", "HARD %", "count")
    hards = [r["hard"] for r in rec["rows"] if r["hard"] is not None]
    hi = max(hards + [1.0])
    nb = 20
    step = hi / nb
    counts = [0] * nb
    for h in hards:
        counts[min(nb - 1, int(h / step))] += 1
    xs = [(i + 0.5) * step for i in range(nb)]
    cols = ["s1" if x <= 10 else "warn" if x <= 20 else "crit" for x in xs]
    f.bars(xs, counts, cols, step * 0.92)
    f.set_range(xr=(0, hi), yr=(0, max(counts) * 1.18 or 1))
    f.note("   ".join(f"<= {k} %: {v:.0f} % of pairs" for k, v in rec["within"].items()))
    return f


def fig_dup_qq(rec, S):
    f = Figure(_dup_title("Q-Q plot", rec),
               "Sorted originals against sorted duplicates: do the two populations agree",
               "original, sorted", "duplicate, sorted")
    f.xlog = f.ylog = bool(S["log_axis"])
    xs = sorted(r["a"] for r in rec["rows"])
    ys = sorted(r["b"] for r in rec["rows"])
    if not xs:
        f.note("no pairs")
        return f
    lo, hi = min(_pos(xs + ys) or [1e-3]), max(_pos(xs + ys) or [1.0])
    f.line([lo, hi], [lo, hi], "fg", 1.2, None, "1:1")
    f.points(xs, ys, "s1", label="quantiles")
    return f


def fig_dup_maxmin(rec, S):
    mm = rec["maxmin"]
    f = Figure(_dup_title("Max-Min plot", rec),
               f"Larger against smaller value of each pair; acceptance line at "
               f"HARD {mm['limit_hard']:g} %",
               "smaller value of the pair", "larger value of the pair")
    f.xlog = f.ylog = True
    rows = [r for r in rec["rows"] if r["a"] > 0 and r["b"] > 0]
    mins = [min(r["a"], r["b"]) for r in rows]
    maxs = [max(r["a"], r["b"]) for r in rows]
    if not rows:
        f.note("no pairs above zero")
        return f
    lo, hi = min(mins), max(maxs)
    f.line([lo, hi], [lo, hi], "fg", 1.2, None, "1:1")
    if mm["ratio_line"]:
        f.line([lo, hi], [lo * mm["ratio_line"], hi * mm["ratio_line"]], "crit", 1.2,
               "dash", "acceptance line")
    ok = [(a, b, r["dup"]) for a, b, r in zip(mins, maxs, rows)
          if r["hard"] is None or r["hard"] <= mm["limit_hard"]]
    bad = [(a, b, r["dup"]) for a, b, r in zip(mins, maxs, rows)
           if r["hard"] is not None and r["hard"] > mm["limit_hard"]]
    f.points([x[0] for x in ok], [x[1] for x in ok], "s1", label="accepted",
             ids=[x[2] for x in ok])
    if bad:
        f.points([x[0] for x in bad], [x[1] for x in bad], "crit", 3.8, "beyond the line",
                 ids=[x[2] for x in bad])
    f.note(f"{mm['fail_pct']:.1f} % of {len(rows)} pairs beyond the acceptance line")
    return f


def fig_dup_quartile(rec, S, C=None):
    crit = (C or DEFAULT_CRITERIA)[_DUP_CRIT.get(rec.get("type"), "fdup_hard90")]
    f = Figure(_dup_title("Precision by grade quartile", rec),
               f"P{S['hard_pct']:g} HARD of the pairs in each quarter of the grade range",
               "", f"P{S['hard_pct']:g} HARD %")
    qs = [q for q in rec.get("quartiles", []) if q["hard_p90"] is not None]
    if not qs:
        f.note("too few pairs")
        return f
    xs = [q["q"] for q in qs]
    hs = [q["hard_p90"] for q in qs]
    cols = [rate(h, crit) for h in hs]
    f.hline(crit["cuts"][2], "warn", 1.0, "dash", None, f"acceptance {crit['cuts'][2]:g} %")
    f.bars(xs, hs, cols, 0.55, texts=[f"{h:.1f} %" for h in hs])
    f.set_xticks(xs, [f"Q{q['q']}\n{fmt_num(q['lo'])}-{fmt_num(q['hi'])}" for q in qs])
    f.set_range(yr=(0, max(hs + [crit["cuts"][2]]) * 1.25))
    return f


def fig_group_summary(breakdown, label, S, crit=None):
    f = Figure(f"Precision by {label.lower()}", "Worst group first", "",
               f"P{S['hard_pct']:g} HARD %")
    if not breakdown:
        f.note("no groups to compare")
        return f
    xs = list(range(1, len(breakdown) + 1))
    hs = [g["hard_p90"] or 0.0 for g in breakdown]
    cols = [g.get("rating", R_NA) for g in breakdown]
    if crit:
        f.hline(crit["cuts"][2], "warn", 1.0, "dash", None, f"acceptance {crit['cuts'][2]:g} %")
    f.bars(xs, hs, cols, 0.6)
    f.set_xticks(xs, [f"{g['group']}\n(n={g['n']})" for g in breakdown],
                 45 if len(breakdown) > 6 else 0)
    return f


# ===========================================================================
#  Thompson-Howarth
# ===========================================================================
def fig_th(rec, S):
    f = Figure(_dup_title("Thompson-Howarth regression", {"type": rec["type"],
                                                           "element": rec["element"]}),
               f"Mean absolute difference of bins of {rec['group']} pairs",
               "mean concentration of the bin", "mean absolute difference")
    xs = [b["conc"] for b in rec["bins"]]
    ys = [b["dbar"] for b in rec["bins"]]
    lo, hi = min(xs), max(xs)
    f.line([lo, hi], [rec["a_int"] + rec["b_slope"] * lo, rec["a_int"] + rec["b_slope"] * hi],
           "s2", 2.0, label="fitted line")
    f.points(xs, ys, "s1", 4.0, "bins", "s")
    f.note(f"mean|d| = {fmt_num(rec['a_int'])} + {rec['b_slope']:.4f} x c")
    if rec.get("constrained"):
        f.note("negative intercept: refitted through the origin", "warn")
    return f


def fig_th_curve(rec, S):
    f = Figure(_dup_title("Precision curve", {"type": rec["type"], "element": rec["element"]}),
               "Precision at 95 % confidence against concentration",
               "concentration", "precision %")
    f.xlog = True
    xs = [c for c, _ in rec["curve"]]
    ys = [p for _, p in rec["curve"]]
    for lim, col in ((10, "good"), (20, "warn"), (30, "crit")):
        f.hline(lim, col, 1.0, "dash", None, f"{lim} %")
    # the DL is shown only when it is near the fitted range, otherwise it would
    # squeeze the curve into a corner of the plot
    if rec.get("dl") and rec["dl"] >= rec["c_lo"] / 20.0:
        f.vline(rec["dl"], "muted", 1.0, "dot", None, "DL")
    f.line(xs, ys, "s1", 2.0, label="precision")
    f.points([rec["c_ref"]], [rec["precision_at_ref"]], "s2", 4.2,
             f"{rec['precision_at_ref']:.1f} % at {fmt_num(rec['c_ref'])}")
    f.set_range(yr=(0, min(120.0, max(ys + [35.0]) * 1.1)))
    return f


# ===========================================================================
#  Check / umpire
# ===========================================================================
def fig_ump_qq(rec, S):
    f = Figure(f"Q-Q plot, primary vs umpire{SEP}{rec['element']}",
               "Do the two laboratories report the same distribution of grades",
               "primary laboratory, sorted", "umpire laboratory, sorted")
    f.xlog = f.ylog = bool(S["log_axis"])
    xs = sorted(r["primary"] for r in rec["rows"])
    ys = sorted(r["umpire"] for r in rec["rows"])
    lo, hi = min(_pos(xs + ys) or [1e-3]), max(_pos(xs + ys) or [1.0])
    f.line([lo, hi], [lo, hi], "fg", 1.2, None, "1:1")
    f.points(xs, ys, "s1", label="quantile pairs")
    return f


def fig_ump_scatter(rec, S):
    f = Figure(f"Primary vs umpire{SEP}{rec['element']}", "", "primary laboratory",
               "umpire laboratory")
    f.xlog = f.ylog = bool(S["log_axis"])
    xs = [r["primary"] for r in rec["rows"]]
    ys = [r["umpire"] for r in rec["rows"]]
    lo, hi = min(_pos(xs + ys) or [1e-3]), max(_pos(xs + ys) or [1.0])
    f.line([lo, hi], [lo, hi], "fg", 1.2, None, "1:1")
    for env, col in ((10, "good"), (20, "warn")):
        k = 1 + env / 100.0
        f.line([lo, hi], [lo * k, hi * k], col, 1.0, "dash", f"±{env} %")
        f.line([lo, hi], [lo / k, hi / k], col, 1.0, "dash")
    if rec.get("rma_b") is not None:
        a, b = rec["rma_a"], rec["rma_b"]
        f.line([lo, hi], [a + b * lo, a + b * hi], "s2", 2.0, label="RMA fit")
    f.points(xs, ys, "s1", label="pairs", ids=[r["sample"] for r in rec["rows"]])
    return f


def fig_ump_bias_grade(rec, S):
    f = Figure(f"Inter-laboratory bias vs grade{SEP}{rec['element']}",
               "Relative difference of every pair against the primary result",
               "primary laboratory result", "umpire - primary, relative %")
    f.xlog = bool(S["log_axis"])
    xs = [r["primary"] for r in rec["rows"]]
    ys = [r["bias"] for r in rec["rows"]]
    f.hline(0, "fg", 1.2)
    for v, col in ((10, "good"), (-10, "good"), (20, "warn"), (-20, "warn")):
        f.hline(v, col, 1.0, "dash", None, f"{v:+g} %")
    if rec.get("wbias") is not None:
        f.hline(rec["wbias"], "s2", 1.8, None, "grade-weighted bias",
                f"weighted {rec['wbias']:+.2f} %")
    f.points(xs, ys, "s1", label="pairs", ids=[r["sample"] for r in rec["rows"]])
    _robust_y(f, ys, 25.0)
    return f


def fig_ump_quartile(rec, S, C=None):
    crit = (C or DEFAULT_CRITERIA)["ump_grade_range"]
    f = Figure(f"Inter-laboratory bias by grade quartile{SEP}{rec['element']}",
               "Grade-weighted bias in each quarter of the primary grade range",
               "", "grade-weighted bias %")
    qs = [q for q in (rec.get("quartiles") or []) if q["bias"] is not None]
    if not qs:
        f.note("not available for a filtered subset")
        return f
    xs = [q["q"] for q in qs]
    hs = [q["bias"] for q in qs]
    f.hline(0, "fg", 1.0)
    g = crit["cuts"][2]
    f.band(-g, g, "okband")
    f.bars(xs, hs, [rate(abs(h), crit) for h in hs], 0.55,
           texts=[f"{h:+.1f} %" for h in hs])
    f.set_xticks(xs, [f"Q{q['q']}\n{fmt_num(q['lo'])}-{fmt_num(q['hi'])}" for q in qs])
    m = max(abs(h) for h in hs + [g])
    f.set_range(yr=(-m * 1.35, m * 1.35))
    return f


def fig_ump_ratio(rec, S):
    f = Figure(f"Umpire / primary ratio, ranked{SEP}{rec['element']}", "",
               "cumulative % of pairs", "umpire / primary")
    ratios = sorted(r["ratio"] for r in rec["rows"] if r["ratio"] is not None)
    n = len(ratios)
    xs = [100.0 * (i + 0.5) / n for i in range(n)]
    f.hline(1.0, "fg", 1.2)
    for v, col in ((1.1, "good"), (0.9, "good"), (1.2, "warn"), (0.8, "warn")):
        f.hline(v, col, 1.0, "dash", None, f"{v:.2f}")
    f.hline(rec["median_ratio"], "s2", 1.8, None, "median",
            f"median {rec['median_ratio']:.3f}")
    f.line(xs, ratios, "s1", 2.0, label="ratio")
    f.set_range(xr=(0, 100))
    return f


# ===========================================================================
#  Programme-wide
# ===========================================================================
def fig_insertion(ins, S):
    f = Figure("Control sample insertion rates",
               "Share of all submitted samples, against the 5 % convention", "",
               "insertion rate %")
    rows = [r for r in ins["rows"] if not r.get("info_only")]
    xs = list(range(1, len(rows) + 1))
    hs = [r["pct"] or 0.0 for r in rows]
    f.hline(5, "good", 1.2, "dash", None, "5 % convention")
    f.bars(xs, hs, [r["rating"] for r in rows], 0.55, texts=[f"{h:.1f} %" for h in hs])
    f.set_xticks(xs, [_TYPE_LABEL.get(r["type"], r["type"]) for r in rows])
    f.set_range(yr=(0, max(hs + [6.5]) * 1.25))
    return f


_STAGE_SHORT = {"sampling": "Sampling", "preparation": "Preparation",
                "analytical": "Analysis", "sampling+preparation": "Sampling + prep.",
                "preparation+analytical": "Prep. + analysis"}


def fig_error_budget(budget, elements):
    f = Figure("Error budget by stage of the sample chain",
               "Share of the total relative variance carried by each stage", "",
               "% of total variance")
    els = [el for el in elements if budget.get(el) and budget[el]["pct"]]
    if not els:
        f.note("needs at least two duplicate classes with enough pairs")
        return f
    order = ["sampling", "sampling+preparation", "preparation",
             "preparation+analytical", "analytical"]
    color = {"sampling": "s1", "sampling+preparation": "s1", "preparation": "s2",
             "preparation+analytical": "s2", "analytical": "s3"}
    xs = list(range(1, len(els) + 1))
    base = [0.0] * len(els)
    for st in order:
        hs = [(budget[el]["pct"].get(st) or 0.0) for el in els]
        if not any(hs):
            continue
        f.bars(xs, hs, color[st], 0.5, bottom=list(base), label=_STAGE_SHORT[st],
               texts=[f"{h:.0f} %" if h >= 8 else "" for h in hs])
        base = [b + h for b, h in zip(base, hs)]
    f.set_xticks(xs, [f"{el}\nCV {budget[el]['total_cv_pct']:.0f} %" for el in els])
    f.set_range(yr=(0, 104))
    f.legend_loc = "outside"
    f.inside_text = True
    return f


def fig_batch_matrix(batches, elements):
    els = [el for el in elements if el in batches]
    names = []
    for el in els:
        for r in batches[el]["rows"]:
            if r["batch"] not in names:
                names.append(r["batch"])
    levels, texts = [], []
    for el in els:
        st = {r["batch"]: r["status"] for r in batches[el]["rows"]}
        levels.append([st.get(b, "NONE") for b in names])
        texts.append([{"PASS": "", "WARN": "W", "FAIL": "F", "NONE": "-"}[st.get(b, "NONE")]
                      for b in names])
    f = Figure.matrix("Batch acceptance", els, names, levels, texts,
                      "Each laboratory batch by element: CRM and blank controls",
                      legend=[("PASS", "pass"), ("WARN", "warning"), ("FAIL", "fail"),
                              ("NONE", "no control")])
    f.size = (7.2, 1.15 + 0.36 * len(els))
    return f


def fig_source_matrix(diagnosis):
    from .diagnosis import STAGES
    m = diagnosis.matrix()
    rows = list(m)
    levels = [[m[el][st] or "NONE_SEV" for st in STAGES] for el in rows]
    short = {"CRITICAL": "Critical", "MATERIAL": "Material", "MINOR": "Minor",
             None: ""}
    texts = [[short[m[el][st]] for st in STAGES] for el in rows]
    short = {"SAMPLING": "Sampling", "PREPARATION": "Preparation",
             "ACCURACY": "Accuracy", "PRECISION": "Precision",
             "CONTAMINATION": "Contam-\nination", "INTERLAB": "Inter-lab",
             "DATA": "Data", "PROGRAMME": "QC design"}
    f = Figure.matrix("Where the error comes from", rows, STAGES, levels, texts,
                      "Worst finding in each stage of the sample chain, by element",
                      col_labels=[short[s] for s in STAGES],
                      legend=[("CRITICAL", "critical"), ("MATERIAL", "material"),
                              ("MINOR", "minor"), ("NONE_SEV", "no finding")])
    f.size = (7.2, 1.35 + 0.38 * len(rows))
    return f


_SCORE_ABBR = {"EXCELLENT": "EXC", "VERY GOOD": "V.GOOD", "GOOD": "GOOD",
               "POOR": "POOR", "BAD": "BAD", "VERY BAD": "V.BAD", "NO DATA": "-"}


def fig_element_scores(results, diagnosis, elements):
    cols = ["CRM", "Coarse blank", "Pulp blank", "Blank", "Field dup",
            "Coarse dup", "Pulp dup", "Umpire"]
    keys = [("crm", None), ("blank", "COARSE BLANK"), ("blank", "PULP BLANK"),
            ("blank", "BLANK"), ("dup", T_FDUP), ("dup", T_CDUP), ("dup", T_PDUP),
            ("umpire", None)]
    R = results
    present = []
    for (sec, sub), name in zip(keys, cols):
        if sec == "crm" and R.get("crm"):
            present.append((sec, sub, name))
        elif sec == "umpire" and R.get("umpire"):
            present.append((sec, sub, name))
        elif sec in ("blank", "dup") and any(k[0] == sub for k in R.get(sec, {})):
            present.append((sec, sub, name))
    levels, texts = [], []
    for el in elements:
        lv, tx = [], []
        for sec, sub, _ in present:
            if sec == "crm":
                rs = [r["rating"] for (lab, e), r in R["crm"].items()
                      if e == el and r["rating"] in RATING_ORDER]
                rt = max(rs, key=RATING_ORDER.index) if rs else R_NA
            elif sec == "umpire":
                rt = R["umpire"].get(el, {}).get("rating", R_NA)
            else:
                rt = R[sec].get((sub, el), {}).get("rating", R_NA)
            lv.append(rt)
            tx.append(_SCORE_ABBR.get(rt, rt))
        levels.append(lv)
        texts.append(tx)
    f = Figure.matrix("QA/QC scorecard", elements, [p[2] for p in present], levels,
                      texts, "Rating of each control method by element (worst CRM shown)",
                      legend=[("EXCELLENT", "excellent - good"), ("POOR", "poor"),
                              ("BAD", "bad"), ("VERY BAD", "very bad"),
                              ("NO DATA", "no rating")])
    return f


# ===========================================================================
#  Catalogue: every figure of a run, by id
# ===========================================================================
def figure_catalog(project, R, diagnosis, S, C, RB=None):
    """{figure id: zero-argument callable returning the Figure}. Ids follow
    the references the diagnosis attaches to its findings."""
    cat = {}

    def put(fid, fn, *args):
        cat[fid] = lambda fn=fn, args=args: fn(*args)

    for (lab, el), rec in sorted(R.get("crm", {}).items()):
        base = f"crm/{lab}/{el}"
        put(f"{base}/control", fig_crm_control, rec, S)
        if rec.get("cert") is None:
            continue
        put(f"{base}/bias", fig_crm_bias, rec, S, C)
        put(f"{base}/z", fig_crm_zhist, rec, S)
        put(f"{base}/cusum", fig_crm_cusum, rec, S, RB)
        put(f"{base}/batch", fig_crm_batch, rec, S, C)
    for el, dr in R.get("drift", {}).items():
        put(f"drift/{el}", fig_crm_drift, dr, el, S, C)
    for el, acc in R.get("accuracy", {}).items():
        if acc["n_crm"] >= 2:
            put(f"accuracy/{el}", fig_accuracy_curve, acc, el)
    for el, cov in R.get("coverage", {}).items():
        put(f"coverage/{el}", fig_coverage, cov, el)
    for (bt, el), rec in sorted(R.get("blank", {}).items()):
        put(f"blank/{bt}/{el}", fig_blank, rec, S)
        put(f"blankprev/{bt}/{el}", fig_blank_prev, rec, S)
    for (dt, el), rec in sorted(R.get("dup", {}).items()):
        base = f"dup/{dt}/{el}"
        put(f"{base}/rank", fig_dup_rank_hard, rec, S, C)
        put(f"{base}/scatter", fig_dup_scatter, rec, S)
        put(f"{base}/maxmin", fig_dup_maxmin, rec, S)
        put(f"{base}/quartile", fig_dup_quartile, rec, S, C)
        put(f"{base}/qq", fig_dup_qq, rec, S)
        put(f"{base}/hrd", fig_dup_mean_hrd, rec, S)
        put(f"{base}/hist", fig_dup_hist, rec, S)
    for (dt, el), rec in sorted(R.get("th", {}).items()):
        put(f"th/{dt}/{el}/curve", fig_th_curve, rec, S)
        put(f"th/{dt}/{el}/bins", fig_th, rec, S)
    for el, rec in sorted(R.get("umpire", {}).items()):
        put(f"umpire/{el}/qq", fig_ump_qq, rec, S)
        put(f"umpire/{el}/scatter", fig_ump_scatter, rec, S)
        put(f"umpire/{el}/bias", fig_ump_bias_grade, rec, S)
        put(f"umpire/{el}/quartile", fig_ump_quartile, rec, S, C)
        put(f"umpire/{el}/ratio", fig_ump_ratio, rec, S)
    if R.get("insertion"):
        put("insertion", fig_insertion, R["insertion"], S)
    if R.get("budget"):
        put("budget", fig_error_budget, R["budget"], project.elements)
    if R.get("batches"):
        put("batches", fig_batch_matrix, R["batches"], project.elements)
    if diagnosis is not None:
        put("source_matrix", fig_source_matrix, diagnosis)
        put("scores", fig_element_scores, R, diagnosis, project.elements)
    return cat
