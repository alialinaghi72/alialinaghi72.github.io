# -*- coding: utf-8 -*-
"""Build the consultant report (a document.Document) from one analysis run.

Order (spec 8): cover, document control, contents, executive summary,
introduction, data validation, QC programme, one chapter per element, action
plan, conclusion, appendices. Every section is built inside its own guard: a
failure in one section becomes a visible notice in that section, the reason
goes to the log, and the rest of the report is still produced."""

from __future__ import annotations

import math
import os
import traceback

from ..core import (BLANK_TYPES, DUP_TYPES, R_NA, RATING_ORDER, T_NORMAL, T_PDUP,
                    fa_digits, fa_num)
from ..diagnosis import SEVERITIES, STAGES
from ..figures import figure_catalog
from ..elements import METHOD_LABEL, criteria_for
from ..exclusions import REASONS_FA, provisional
from ..model import usable
from ..protocol import DEFAULT_CRITERIA, DEFAULT_SETTINGS, RULES
from . import texts_fa as T
from .document import (Bullets, Callout, Cell, Cover, DocControl, Document,
                       FigureBlock, FindingCard, Heading, PageBreak, Para,
                       ReportMeta, Signature, Table, TOC, VerdictGrid)

MAX_DETAIL = 8
MAX_ROWS = 400

_SEV_TONE = {"CRITICAL": "critical", "MATERIAL": "material", "MINOR": "minor"}
_VERDICT_TONE = {"SUITABLE": "ok", "RESTRICTED": "warn", "REMEDIATE": "critical"}
_RATING_TONE = {"EXCELLENT": "ok", "VERY GOOD": "ok", "GOOD": "ok", "POOR": "warn",
                "BAD": "material", "VERY BAD": "critical", "NO DATA": "muted"}
_BATCH_TONE = {"PASS": "ok", "WARN": "warn", "FAIL": "critical", "NONE": "muted"}
_BATCH_FA = {"PASS": "قبول", "WARN": "هشدار", "FAIL": "رد", "NONE": "بدون کنترل"}


def _n(v, d=None):
    return fa_num(v, d)


def _p(v, d=1):
    return T.pct(v, d)


def _rating(r):
    return Cell(T.RATING_FA.get(r, r), _RATING_TONE.get(r, "muted"))


def _ltr(s):
    return Cell(str(s), ltr=True)


def _el(el):
    return f"{T.el_fa(el)} ({el})"


class _Ctx:
    def __init__(self, project, R, d, meta, F, C, S, RB, log):
        self.project, self.R, self.d, self.meta = project, R, d, meta
        self.F, self.C, self.S, self.RB, self.log = F, C, S, RB, log
        self.cat = figure_catalog(project, R, d, S, C, RB)
        self.fig_n = 0
        self.tab_n = 0
        self.sec_n = 0

    def section(self, doc, text, anchor):
        self.sec_n += 1
        num = fa_digits(str(self.sec_n))
        doc.add(Heading(1, text, anchor, num))
        self.sub_n = 0
        return num

    def sub(self, doc, text):
        self.sub_n += 1
        doc.add(Heading(2, text, "", f"{fa_digits(str(self.sec_n))}-"
                                       f"{fa_digits(str(self.sub_n))}"))

    def figure(self, doc, fid, caption):
        make = self.cat.get(fid)
        if make is None:
            return False
        self.fig_n += 1
        doc.add(FigureBlock(make(), caption, fa_digits(str(self.fig_n))))
        return True

    def table(self, doc, header, rows, caption="", widths=None, compact=False):
        self.tab_n += 1
        doc.add(Table(header, rows, caption, widths, fa_digits(str(self.tab_n)), compact))


def _guard(ctx, doc, title, fn):
    try:
        fn(ctx, doc)
    except Exception as ex:                    # noqa: BLE001 -- isolate any section
        ctx.log(f"report section '{title}' failed: {ex}\n{traceback.format_exc()}")
        doc.add(Callout("critical", f"{T.SECTION_ERROR}: {title}",
                        "جزئیات خطا در گزارش اجرای نرم‌افزار ثبت شده است."))


def detail_elements(project, meta):
    chosen = [e for e in (meta.detail_elements or []) if e in project.elements]
    if chosen:
        return chosen
    return list(project.elements[:MAX_DETAIL])


# ===========================================================================
def build_report(project, R, diagnosis, meta, F, C, S, RB, log=print):
    meta = meta if isinstance(meta, ReportMeta) else ReportMeta.from_dict(meta)
    if not meta.standard and RB is not None:
        meta.standard = RB.el.preset            # R19: the standard the limits came from
    ctx = _Ctx(project, R, diagnosis, meta, F, C, S, RB, log)
    doc = Document(meta)
    _guard(ctx, doc, "جلد", _cover)
    doc.add(DocControl(meta), TOC(), PageBreak())
    _guard(ctx, doc, T.H["summary"], _summary)
    _guard(ctx, doc, T.H["intro"], _intro)
    _guard(ctx, doc, T.H["cleaning"], _cleaning)
    _guard(ctx, doc, T.H["programme"], _programme)
    detail = detail_elements(project, meta)
    for el in detail:
        _guard(ctx, doc, _el(el), lambda c, d_, el=el: _element(c, d_, el))
    if len(detail) < len(project.elements):
        _guard(ctx, doc, T.H["others"], lambda c, d_: _others(c, d_, detail))
    _guard(ctx, doc, T.H["exclusions"], _exclusions)
    _guard(ctx, doc, T.H["actions"], _actions)
    _guard(ctx, doc, T.H["conclusion"], _conclusion)
    doc.add(PageBreak())
    _guard(ctx, doc, T.H["app_methods"], _app_methods)
    _guard(ctx, doc, T.H["app_criteria"], _app_criteria)
    if meta.include_cleaning_log:
        _guard(ctx, doc, T.H["app_cleaning"], _app_cleaning)
    if meta.include_failed:
        _guard(ctx, doc, T.H["app_failed"], _app_failed)
    if meta.include_protocol:
        _guard(ctx, doc, T.H["app_protocol"], _app_protocol)
    return doc


# ---- cover and summary -----------------------------------------------------------
def _live(project):
    return [s for s in project.samples if not s.dropped]


def _cover(ctx, doc):
    p, d = ctx.project, ctx.d
    live = _live(p)
    n_ctrl = sum(1 for s in live if s.stype != T_NORMAL)
    batches = {s.batch for s in live if s.batch}
    verdicts = [(el, T.el_fa(el), d.verdict(el)[0]) for el in p.elements]
    decisions = [(el, T.el_fa(el), d.decision(el)[0]) for el in p.elements]
    stats = [("نمونه", _n(len(live), 0)), ("عنصر", _n(len(p.elements), 0)),
             ("بچ", _n(len(batches), 0) if batches else "—"),
             ("نمونهٔ کنترلی", _n(n_ctrl, 0))]
    doc.add(Cover(ctx.meta, decisions, verdicts, stats))


def _summary(ctx, doc):
    p, R, d = ctx.project, ctx.R, ctx.d
    ctx.section(doc, T.H["summary"], "summary")
    live = _live(p)
    n_ctrl = sum(1 for s in live if s.stype != T_NORMAL)
    batches = {s.batch for s in live if s.batch}
    codes = [d.verdict(el)[0] for el in p.elements]
    lead = (f"این گزارش {_n(len(live), 0)} نمونه"
            + (f" در {_n(len(batches), 0)} بچ آزمایشگاهی" if batches else "")
            + f" را برای {_n(len(p.elements), 0)} عنصر ({'، '.join(T.el_fa(e) for e in p.elements)}) "
            f"ارزیابی کرده است؛ {_n(n_ctrl, 0)} نمونه ({_p(100.0 * n_ctrl / max(1, len(live)))}) "
            f"نمونهٔ کنترلی بوده‌اند. از نظر کفایت تجمعی، داده‌های "
            f"{_n(codes.count('SUITABLE'), 0)} عنصر قابل استفاده، "
            f"{_n(codes.count('RESTRICTED'), 0)} عنصر قابل استفاده با محدودیت و "
            f"{_n(codes.count('REMEDIATE'), 0)} عنصر نیازمند اصلاح پیش از استفاده‌اند.")
    doc.add(Para(lead, "lead"))
    # (1) batch decision from the spec rules, apart from (2) cumulative adequacy
    ctx.sub(doc, T.DECISION_TITLE)
    if not (p.assay and p.assay.mapping.get("batch")):
        doc.add(Callout("warn", "ستون بچ", T.NO_BATCH_COLUMN))
    rows = []
    for el in p.elements:
        code, reasons, ranges = d.decision(el)
        why = "؛ ".join(T.DECISION_REASON_FA.get(r, r.replace(
            "CRM failure", "ردشدگی نمونهٔ استاندارد")) for r in reasons) or "—"
        rows.append([_el(el), Cell(T.BATCH_DECISION_FA[code], T.BATCH_DECISION_TONE[code]),
                     why, T.ranges_text(ranges) or "—"])
    ctx.table(doc, ["عنصر", "تصمیم", "دلیل", "بازهٔ آنالیز مجدد"], rows,
              "تصمیم پذیرش بچ به تفکیک عنصر (قواعد مشخصهٔ فنی)", widths=[12, 16, 34, 38])
    border, bm = d.batch_matrix()
    if len(border) > 1:
        ctx.sub(doc, T.BATCH_MATRIX_TITLE)
        doc.add(Para(T.BATCH_MATRIX_INTRO))
        mrows = []
        for bt in border:
            row = [_ltr(bt)]
            for el in p.elements:
                code, ra = bm[bt].get(el, ("NOT_ASSESSABLE", []))
                n = sum(r["n_samples"] for r in ra)
                txt = T.BATCH_DECISION_FA[code] + (f" ({_n(n, 0)} نمونه)" if n else "")
                row.append(Cell(txt, T.BATCH_DECISION_TONE[code]))
            mrows.append(row)
        ctx.table(doc, ["بچ"] + [_el(el) for el in p.elements], mrows,
                  "ماتریس پذیرش بچ × عنصر (قواعد مشخصهٔ فنی)؛ عدد داخل پرانتز تعداد نمونه‌های "
                  "بازهٔ آنالیز مجدد است")
    ctx.sub(doc, T.ADEQUACY_TITLE)
    doc.add(VerdictGrid([(T.el_fa(el), el, d.verdict(el)[0], d.counts(el))
                         for el in p.elements]))
    ctx.figure(doc, "source_matrix", "منشأ خطا: شدیدترین یافته در هر مرحلهٔ زنجیرهٔ نمونه، "
                                     "به تفکیک عنصر")
    serious = [f for f in d.actions() if f.severity in ("CRITICAL", "MATERIAL")]
    if serious:
        ctx.sub(doc, "یافته‌های بحرانی و مهم")
        doc.add(Bullets([f"**{T.SEVERITY_FA[f.severity]}** — "
                         f"{f.title_fa} ({T.STAGE_FA[f.stage]})" for f in serious]))
    now = [f for f in d.actions() if f.timing == "IMMEDIATE"][:8]
    if now:
        ctx.sub(doc, "اقدامات فوری")
        doc.add(Bullets([f"{f.actions_fa[0]} ({T.el_fa(f.element) if f.element else 'کل پروژه'})"
                         for f in now], ordered=True))
    if R.get("budget"):
        ctx.figure(doc, "budget", "بودجهٔ خطا: سهم نمونه‌برداری، آماده‌سازی و آنالیز از "
                                  "واریانس کل")
    doc.add(Callout("info", "تذکر", T.DISCLAIMER))


# ---- introduction ------------------------------------------------------------------
def _intro(ctx, doc):
    p = ctx.project
    ctx.section(doc, T.H["intro"], "intro")
    for para in T.INTRO:
        doc.add(Para(para))
    rows = []
    for label, t in (("نتایج آنالیز", p.assay), ("گواهی شاهدها", p.crm),
                     ("جفت‌های تکراری", p.pairs), ("آزمایشگاه دوم", p.umpire)):
        if t is not None:
            rows.append([label, _ltr(os.path.basename(t.path)), _n(len(t.rows), 0),
                         _n(len(t.header), 0)])
    ctx.sub(doc, "داده‌های دریافتی")
    ctx.table(doc, ["جدول", "فایل", "سطر", "ستون"], rows, "فایل‌های ورودی")
    live = _live(p)
    counts = {}
    for s in live:
        counts[s.stype] = counts.get(s.stype, 0) + 1
    ctx.table(doc, ["نوع نمونه", "تعداد", "سهم"],
              [[T.TYPE_FA.get(t, t), _n(n, 0), _p(100.0 * n / max(1, len(live)))]
               for t, n in sorted(counts.items(), key=lambda x: -x[1])],
              "ترکیب نمونه‌ها پس از پاک‌سازی")
    from ..model import detection_limit
    ctx.table(doc, ["عنصر", "ستون", "حد تشخیص", "نمونهٔ عادی دارای نتیجه"],
              [[T.el_fa(el), _ltr(el), _n(detection_limit(p, el, ctx.S)),
                _n(sum(1 for s in live if s.stype == T_NORMAL
                       and s.vals.get(el) is not None), 0)] for el in p.elements],
              "عناصر ارزیابی‌شده")
    labs = sorted({s.lab for s in live if s.lab})
    ump = {r.get("lab") for r in ctx.R.get("umpire", {}).values() if r.get("lab")}
    if labs or ump:
        doc.add(Para("آزمایشگاه اصلی: " + (" ، ".join(labs) or "—")
                     + (f" — آزمایشگاه دوم: {' ، '.join(sorted(ump))}" if ump else "")))


# ---- cleaning --------------------------------------------------------------------
def _cleaning(ctx, doc):
    p = ctx.project
    ctx.section(doc, T.H["cleaning"], "cleaning")
    doc.add(Para(T.CLEANING_INTRO))
    L = p.clean_log
    if L is None or not L.actions:
        doc.add(Para("هیچ خطای داده‌ای شناسایی نشد."))
    else:
        from ..cleaning import RULE_TITLES
        rows = []
        for code, n in L.counts().items():
            acts = [a.action for a in L.actions if a.rule == code]
            main = max(set(acts), key=acts.count)
            rows.append([_ltr(code), RULE_TITLES.get(code, ("", code))[1], _n(n, 0),
                         T.ACTION_FA.get(main, main)])
        ctx.table(doc, ["کد", "قاعده", "تعداد", "اقدام"], rows,
                  "خلاصهٔ اقدامات پاک‌سازی (فهرست کامل در پیوست ج)")
    data = [f for f in ctx.d.project_findings() if f.stage == "DATA"]
    for f in data:
        doc.add(FindingCard(f))


# ---- programme -------------------------------------------------------------------
def _programme(ctx, doc):
    R = ctx.R
    ctx.section(doc, T.H["programme"], "programme")
    doc.add(Para(T.PROGRAMME_INTRO))
    ins = R.get("insertion")
    if ins:
        rows = [[T.TYPE_FA.get(r["type"], r["type"]), _n(r["n"], 0), _p(r["pct"], 2),
                 (f"یک در {_n(r['every'], 0)}" if r.get("every") else "—"),
                 (_p(r["target"], 1) if r.get("target") else "۵٪ (قرارداد)"),
                 Cell("برای اطلاع", "muted") if r.get("info_only") else _rating(r["rating"])]
                for r in ins["rows"]]
        ctx.table(doc, ["کلاس کنترلی", "تعداد", "نرخ درج", "تناوب", "هدف", "رتبه"], rows,
                  f"نرخ درج نمونه‌های کنترلی از {_n(ins['n_total'], 0)} نمونه")
        ctx.figure(doc, "insertion", "نرخ درج هر کلاس کنترلی در برابر هدف آن کلاس")
    if R.get("batches"):
        ctx.figure(doc, "batches", "پذیرش بچ‌ها: وضعیت شاهدها و شاهدهای خالی در هر بچ")
    for f in [f for f in ctx.d.project_findings() if f.stage == "PROGRAMME"]:
        doc.add(FindingCard(f))


# ---- element chapter ---------------------------------------------------------------
def _element(ctx, doc, el):
    d = ctx.d
    ctx.section(doc, f"عنصر {T.el_fa(el)}", f"el-{el}")
    code, text = d.verdict(el)
    doc.add(Callout({"SUITABLE": "ok", "RESTRICTED": "warn",
                     "REMEDIATE": "critical"}[code], T.VERDICT_FA[code], text))
    _el_accuracy(ctx, doc, el)
    _el_contamination(ctx, doc, el)
    _el_precision(ctx, doc, el)
    _el_th(ctx, doc, el)
    _el_budget(ctx, doc, el)
    _el_interlab(ctx, doc, el)
    _el_batches(ctx, doc, el)
    ctx.sub(doc, T.H["findings"])
    fs = sorted(d.by_element(el), key=lambda f: (SEVERITIES.index(f.severity),
                                                 STAGES.index(f.stage)))
    if not fs:
        doc.add(Para(T.MISSING["findings"]))
    for f in fs:
        doc.add(FindingCard(f))


def certificate_rows(project):
    """R1: the certificate row used for every CRM x column."""
    out = []
    for (key, col), c in sorted(project.certs.items()):
        out.append({"crm": c.get("label") or project.crm_labels.get(key, key),
                    "column": col, "element": c.get("cert_element", ""),
                    "method": c.get("method", ""), "cert": c["cert"], "sd": c.get("sd"),
                    "unit": c.get("unit", ""), "cert_unit": c.get("cert_unit", ""),
                    "row": c.get("cert_row")})
    return out


def _el_accuracy(ctx, doc, el):
    R = ctx.R
    ctx.sub(doc, T.H["accuracy"])
    recs = [(lab, r) for (lab, e), r in sorted(R.get("crm", {}).items()) if e == el]
    if not [r for _, r in recs if r.get("cert") is not None]:
        doc.add(Para(T.MISSING["crm"]))
        return
    doc.add(Para(T.SECTION_INTRO["accuracy"]))
    rows = []
    for lab, r in recs:
        if r.get("status") == "NOT_CERTIFIED":
            rows.append([_ltr(lab), _n(r["n"], 0), "—", _n(r.get("obs_mean")), "—", "—",
                         "—", "—", Cell(T.NOT_CERTIFIED, "muted")])
            continue
        if r.get("status") == "MONITORING":
            rating = Cell(T.MONITORING_ONLY.format(k=T.lim(ctx.RB["crm_min_kdl"], "")), "muted")
        elif r["n"] < ctx.RB["bias_min_n"]:
            rating = Cell(T.INSUFFICIENT_BIAS.format(n=fa_digits(str(ctx.RB["bias_min_n"]))),
                          "muted")
        else:
            rating = _rating(r["rating"])
        rows.append([_ltr(lab), _n(r["n"], 0), _n(r.get("cert")), _n(r.get("obs_mean")),
                     _p(r.get("bias"), 2), _p(r.get("fail_pct"), 1),
                     _p(r.get("rsd_pct"), 2),
                     (_n(r["rsd_ratio"], 2) if r.get("rsd_ratio") is not None else "—"),
                     rating])
    ctx.table(doc, ["نمونه استاندارد", "تعداد", "مقدار گواهی", "میانگین", "بایاس",
                    "بیرون از حد عمل", "انحراف معیار نسبی", "نسبت به گواهی", "رتبه"], rows,
              f"نتایج نمونه‌های استاندارد برای {_el(el)}")
    if ctx.RB["rsd_by_ratio"]:
        doc.add(Para(T.RSD_RATIO_NOTE.format(
            k=T.lim(ctx.RB["rsd_ratio"], ""))))
    used = [c for c in certificate_rows(ctx.project) if c["column"] == el]
    if used:
        ctx.table(doc, ["نمونه استاندارد", "ردیف گواهی", "عنصر در گواهی", "روش", "مقدار",
                        "انحراف معیار", "واحد"],
                  [[_ltr(c["crm"]), _n(c["row"], 0) if c["row"] else "—", _ltr(c["element"]),
                    _ltr(METHOD_LABEL.get(c["method"], c["method"]) or "—"), _n(c["cert"]),
                    _n(c["sd"]), _ltr(c["unit"])] for c in used],
                  f"ردیف‌های گواهی به‌کاررفته برای {_el(el)}")
    dr = R.get("drift", {}).get(el)
    if dr and dr.get("insufficient"):
        doc.add(Para(T.DRIFT_INSUFFICIENT.format(n=fa_digits(str(dr["n"])),
                                                 m=fa_digits(str(ctx.RB["drift_min_pooled"])))))
    elif dr:
        ctx.figure(doc, f"drift/{el}", f"بایاس همهٔ شاهدهای {T.el_fa(el)} به ترتیب آنالیز و "
                                       f"روند برازش‌شده")
    ctx.figure(doc, f"accuracy/{el}", f"منحنی صحت {T.el_fa(el)}: میانگین اندازه‌گیری‌شده در "
                                      f"برابر مقدار گواهی")
    for lab, r in recs:
        if r.get("cert") is not None:
            ctx.figure(doc, f"crm/{lab}/{el}/control",
                       f"نمودار کنترلی شاهد {lab} برای {T.el_fa(el)}")
    fails = [f for f in ctx.d.by_element(el) if f.code in ("CRM_FAIL", "CRM_CLUSTER")]
    if fails:
        worst = max((r for _, r in recs if r.get("fail_pct") is not None),
                    key=lambda r: r["fail_pct"], default=None)
        if worst:
            ctx.figure(doc, f"crm/{worst['crm']}/{el}/batch",
                       f"بایاس شاهد {worst['crm']} در هر بچ")
    cov = R.get("coverage", {}).get(el)
    if cov and cov.get("certs"):
        def _yes(flag):
            return Cell("ندارد", "fail") if flag else Cell("دارد", "ok")
        rows = [["صدک ۱۰ تا ۹۰", f"{_n(cov['pcts'].get(10.0))} تا {_n(cov['p90'])}",
                 _yes(cov["none_above_p90"] or cov["none_below_p10"])],
                ["صدک ۲۵ تا ۹۰ (دامنهٔ اقتصادی)", f"{_n(cov['p25'])} تا {_n(cov['p90'])}",
                 _yes(cov["gap_p25_p90"])]]
        if cov.get("cutoff"):
            rows.append([f"عیار حد ±{T.lim(cov['band_pct'])}", _n(cov["cutoff"]),
                         _yes(cov["no_cutoff_crm"])])
        else:
            rows.append(["عیار حد", "تعریف نشده", Cell("ارزیابی نشد", "muted")])
        if cov.get("upper") is not None:
            rows.append(["زیر حد بالای روش", _n(cov["upper"]),
                         Cell(f"{_n(len(cov['above_upper']), 0)} بالاتر از حد", "fail")
                         if cov["above_upper"] else Cell("همه زیر حد", "ok")])
        ctx.table(doc, ["بازه", f"عیار ({_ltr(cov.get('unit') or '—')})",
                        "نمونه استاندارد در بازه"], rows,
                  f"پوشش عیاری نمونه‌های استاندارد {_el(el)}")
    ctx.figure(doc, f"coverage/{el}",
               f"پوشش دامنهٔ عیار {T.el_fa(el)} با نمونه‌های استاندارد")


def _el_contamination(ctx, doc, el):
    R = ctx.R
    ctx.sub(doc, T.H["contamination"])
    recs = [(bt, R["blank"][(bt, el)]) for bt in BLANK_TYPES if (bt, el) in R.get("blank", {})]
    if not recs:
        have = any(s.stype in BLANK_TYPES and usable(s, el) for s in ctx.project.samples)
        doc.add(Para(T.MISSING["blank_nodl" if have else "blank"]))
        return
    doc.add(Para(T.SECTION_INTRO["contamination"]))
    rows = [[T.TYPE_FA[bt], _n(r["n"], 0), _n(r["limit"]), _n(r["n_fail"], 0),
             _p(r["fail_pct"], 1), _n(r["max_ratio"], 1), _rating(r["rating"])]
            for bt, r in recs]
    ctx.table(doc, ["نوع", "تعداد", "حد آلودگی", "ردشده", "نرخ ردشدگی",
                    "بدترین (برابر حد تشخیص)", "رتبه"], rows,
              f"نتایج شاهدهای خالی برای {_el(el)}")
    for bt, r in recs:
        ctx.figure(doc, f"blank/{bt}/{el}", f"نمودار کنترلی {T.TYPE_FA[bt]} برای {T.el_fa(el)}")
        if r["n_fail"]:
            ctx.figure(doc, f"blankprev/{bt}/{el}",
                       f"{T.TYPE_FA[bt]} در برابر نمونهٔ قبلی: آزمون انتقال آلودگی")


_DUP_CRIT = {"FIELD DUP": "fdup_hard90", "COARSE DUP": "cdup_hard90",
             "PULP DUP": "pdup_hard90"}


def _el_precision(ctx, doc, el):
    R = ctx.R
    ctx.sub(doc, T.H["precision"])
    recs = [(dt, R["dup"][(dt, el)]) for dt in DUP_TYPES if (dt, el) in R.get("dup", {})]
    if not recs:
        doc.add(Para(T.MISSING["dup"]))
        return
    doc.add(Para(T.SECTION_INTRO["precision"]))
    first = recs[0][1]
    note = T.near_dl_note(first.get("min_kdl"), first.get("kdl_dl"),
                          [(T.TYPE_FA[dt], r.get("n_below_kdl", 0)) for dt, r in recs],
                          method_kept=True, unknown=first.get("kdl_dl") is None)
    if note:
        doc.add(Para(note))
    rows = []
    for dt, r in recs:
        crit = criteria_for(ctx.C, ctx.RB, el)[_DUP_CRIT[dt]]
        rows.append([T.TYPE_FA[dt], _n(r["n"], 0), _p(r["hard_p90"], 1),
                     T.lim(crit["cuts"][2]), _p(100.0 - r["maxmin"]["fail_pct"], 0),
                     _p(r["rd_mean"], 2), _rating(r["ratings"].get(_DUP_CRIT[dt], R_NA))])
    ctx.table(doc, ["کلاس", "جفت", "صدک نودم HARD", "مرز پذیرش", "جفت‌های درون مرز",
                    "میانگین اختلاف نسبی", "رتبه"], rows, f"دقت نمونه‌های تکراری {_el(el)}")
    flagged = {f.subject for f in ctx.d.by_element(el) if f.code == "DUP_PRECISION"}
    for dt, r in recs:
        ctx.figure(doc, f"dup/{dt}/{el}/rank", f"منحنی رتبه‌ای HARD — {T.TYPE_FA[dt]} {T.el_fa(el)}")
        if dt in flagged:
            ctx.figure(doc, f"dup/{dt}/{el}/maxmin",
                       f"نمودار بیشینه-کمینه — {T.TYPE_FA[dt]} {T.el_fa(el)}")
    worst = max(recs, key=lambda x: x[1]["hard_p90"] or 0)
    if worst[0] in flagged:
        ctx.figure(doc, f"dup/{worst[0]}/{el}/quartile",
                   f"دقت در هر چارک عیار — {T.TYPE_FA[worst[0]]} {T.el_fa(el)}")


def _el_th(ctx, doc, el):
    th = ctx.R.get("th", {}).get((T_PDUP, el))
    ctx.sub(doc, T.H["th"])
    if not th:
        doc.add(Para(T.MISSING["th"]))
        return
    ctx.table(doc, ["غلظت مرجع", "دقت در سطح اطمینان ۹۵٪", "حد تشخیص عملی", "رتبه"],
              [[_n(th["c_ref"]), _p(th["precision_at_ref"], 1),
                _n(th["pdl"]) if th.get("pdl") else "—",
                _rating(th["ratings"].get("th_precision", R_NA))]],
              f"دقت آنالیز {_el(el)} از تکراری‌های پالپ")
    ctx.figure(doc, f"th/{T_PDUP}/{el}/curve", f"منحنی دقت آنالیز {T.el_fa(el)}")


def _el_budget(ctx, doc, el):
    b = ctx.R.get("budget", {}).get(el)
    ctx.sub(doc, T.H["budget"])
    if not b:
        doc.add(Para(T.MISSING["budget"]))
        return
    if not b.get("estimable"):
        doc.add(Para(T.BUDGET_NOT_ESTIMABLE.format(
            n=fa_digits(str(ctx.RB["budget_min_pairs"])))))
        return
    doc.add(Para(T.SECTION_INTRO["budget"]))
    rows = [[T.BUDGET_STAGE_FA.get(k, k), _p(v, 1) if v is not None else "قابل برآورد نیست"]
            for k, v in b["pct"].items()]
    ctx.table(doc, ["مرحله", "سهم از واریانس کل"], rows,
              f"بودجهٔ خطای {_el(el)} (ضریب تغییرات کل {_p(b['total_cv_pct'], 1)})")
    if b.get("unmeasured"):
        doc.add(Para("تکراری صحرایی وجود ندارد؛ خطای نمونه‌برداری در این بودجه سنجیده "
                     "نشده است.", "note"))


def _el_interlab(ctx, doc, el):
    u = ctx.R.get("umpire", {}).get(el)
    ctx.sub(doc, T.H["interlab"])
    if not u:
        doc.add(Para(T.MISSING["umpire"]))
        return
    doc.add(Para(T.SECTION_INTRO["interlab"]))
    note = T.near_dl_note(u.get("min_kdl"), u.get("kdl_dl"), [("", u.get("n_below_kdl", 0))],
                          unknown=u.get("kdl_dl") is None)
    if note:
        doc.add(Para(note))
    tt = u.get("ttest") or {}
    ctx.table(doc, ["جفت", "بایاس وزنی", "میانگین بایاس جفت‌ها", "مقدار احتمال آزمون t",
                    "بدترین چارک عیار", "رتبه"],
              [[_n(u["n"], 0), _p(u["wbias"], 2), _p(u["pbias"], 2),
                T.p_text(tt.get("p")), _p(u.get("worst_quartile"), 2),
                _rating(u["rating"])]],
              f"مقایسهٔ آزمایشگاه اصلی و آزمایشگاه دوم برای {_el(el)}")
    ctx.figure(doc, f"umpire/{el}/bias", f"بایاس بین‌آزمایشگاهی {T.el_fa(el)} در برابر عیار")
    ctx.figure(doc, f"umpire/{el}/quartile", f"بایاس بین‌آزمایشگاهی {T.el_fa(el)} در هر چارک عیار")


def _el_batches(ctx, doc, el):
    b = ctx.R.get("batches", {}).get(el)
    ctx.sub(doc, T.H["batches"])
    if not b or not b["rows"] or all(r["crm_status"] == "NONE" for r in b["rows"]):
        doc.add(Para(T.MISSING["batches"]))
        return
    doc.add(Para(T.SECTION_INTRO["batches"]))
    nb = len(b["rows"])
    doc.add(Para(f"از {_n(nb, 0)} بچ، {_n(b['n_fail'], 0)} بچ رد و {_n(b['n_warn'], 0)} بچ "
                 f"در وضعیت هشدار است."))
    ra = b["reassay"]
    if ra:
        rows = [[_ltr(r["batch"]), _ltr(r["crm"]), _ltr(r["failed_sample"]), _ltr(r["rule"]),
                 _ltr(r["from_sample"]), _ltr(r["to_sample"]), _n(r["n_samples"], 0)]
                for r in ra[:60]]
        ctx.table(doc, ["بچ", "شاهد", "نمونهٔ شاهد ردشده", "قاعده", "از نمونه", "تا نمونه",
                        "تعداد نمونه"], rows,
                  f"بازه‌های آنالیز مجدد {_el(el)}"
                  + (f" ({_n(len(ra), 0)} بازه؛ فهرست کامل در خروجی CSV)" if len(ra) > 60 else ""),
                  compact=True)


def _others(ctx, doc, detail):
    ctx.section(doc, T.H["others"], "others")
    rows = []
    for el in ctx.project.elements:
        if el in detail:
            continue
        code, _ = ctx.d.verdict(el)
        c = ctx.d.counts(el)
        worst = sorted(ctx.d.by_element(el), key=lambda f: SEVERITIES.index(f.severity))
        rows.append([_el(el), Cell(T.VERDICT_FA[code], _VERDICT_TONE[code]),
                     _n(c["CRITICAL"], 0), _n(c["MATERIAL"], 0), _n(c["MINOR"], 0),
                     worst[0].title_fa if worst else "—"])
    ctx.table(doc, ["عنصر", "حکم", "بحرانی", "مهم", "جزئی", "مهم‌ترین مسئله"], rows,
              "عناصری که فصل جداگانه ندارند")


# ---- actions and conclusion -------------------------------------------------------
def _cv_avg(rec):
    """CV_avg: root mean square of the pair CVs (Stanley & Lawie 2007), %."""
    v = rec.get("cv2_mean") if rec else None
    return math.sqrt(v) * 100.0 if v is not None and v >= 0 else None


def _within(rec, C, dt):
    if not rec:
        return None
    good = C[_DUP_CRIT[dt]]["cuts"][2]
    hh = [r["hard"] for r in rec["rows"] if r["hard"] is not None]
    return 100.0 * sum(1 for h in hh if h <= good) / len(hh) if hh else None


def _exclusions(ctx, doc):
    """R24: what was left out of the precision statistics, and why."""
    R = ctx.R
    ctx.section(doc, T.H["exclusions"], "exclusions")
    for t in T.EXCLUSION_INTRO:
        doc.add(Para(t))
    rev = R.get("exclusions") or []
    summ = R.get("exclusion_summary") or {}
    prov = provisional(rev)
    if prov:
        doc.add(Callout("warn", "حکم موقت",
                        T.EXCLUSION_PROVISIONAL.format(n=fa_digits(str(len(prov))))))
    if not summ:
        doc.add(Para(T.EXCLUSION_NONE))
        return
    rows = []
    for (dt, el), v in sorted(summ.items(), key=lambda x: (x[0][1], DUP_TYPES.index(x[0][0]))):
        rows.append([_el(el), T.TYPE_FA[dt], _n(v["total"], 0), _n(v["low"], 0),
                     _n(v["out_excl"], 0), _n(v["out_kept"], 0)])
    ctx.table(doc, ["عنصر", "کلاس", "کل جفت‌ها", "کنارگذاشته (کم‌عیار)",
                    "کنارگذاشته (پرت)", "پرتِ نگه‌داشته"], rows,
              "خلاصهٔ جفت‌های کنارگذاشته به تفکیک عنصر و کلاس")
    outl = [r for r in rev if r["trigger"] != "low-grade"]
    if outl:
        ctx.table(doc, ["عنصر", "کلاس", "نمونهٔ اصلی", "تکراری", "مقدار اصلی", "مقدار تکراری",
                        "HARD", "علت", "تصمیم", "دلیل"],
                  [[_el(r["element"]), T.TYPE_FA[r["dtype"]], _ltr(r["orig"]), _ltr(r["dup"]),
                    _n(r["a"]), _n(r["b"]), _p(r["hard"], 0), T.TRIGGER_FA[r["trigger"]],
                    Cell(T.DECISION_FA[r["decision"]] + (" (پیش‌فرض)" if r.get("pending") else ""),
                         "warn" if r.get("pending") else ""),
                    REASONS_FA.get(r.get("reason"), r.get("reason") or "—")]
                   for r in outl],
                  "همهٔ جفت‌های پرت، کنارگذاشته یا نگه‌داشته", compact=True)
    side = []
    for (dt, el), b in sorted(R.get("dup", {}).items(), key=lambda x: (x[0][1], x[0][0])):
        a = R.get("dup_all", {}).get((dt, el))
        tha = R.get("th_all", {}).get((dt, el))
        thb = R.get("th", {}).get((dt, el))
        side.append([_el(el), T.TYPE_FA[dt],
                     f"{_n(a['n'], 0) if a else '—'} / {_n(b['n'], 0)}",
                     f"{_p(a['hard_p90'], 1) if a else '—'} / {_p(b['hard_p90'], 1)}",
                     f"{_p(_within(a, criteria_for(ctx.C, ctx.RB, el), dt), 0)} / "
                     f"{_p(_within(b, criteria_for(ctx.C, ctx.RB, el), dt), 0)}",
                     f"{_p(_cv_avg(a), 1)} / {_p(_cv_avg(b), 1)}",
                     f"{_p(a['rd_mean'], 2) if a else '—'} / {_p(b['rd_mean'], 2)}",
                     f"{_n(a['rma_b']) if a else '—'} / {_n(b['rma_b'])}",
                     f"{_p(tha['precision_at_ref'], 0) if tha else '—'} / "
                     f"{_p(thb['precision_at_ref'], 0) if thb else '—'}"])
    if side:
        doc.add(Para(T.EXCLUSION_VARIANT))
        ctx.table(doc, ["عنصر", "کلاس", "تعداد", "صدک نودم HARD", "درون مرز",
                        "CV_avg", "میانگین اختلاف نسبی", "شیب RMA", "دقت تامپسون-هوارث"],
                  side, "آمار دقت: همهٔ جفت‌ها / پس از بازبینی", compact=True)


def _actions(ctx, doc):
    ctx.section(doc, T.H["actions"], "actions")
    doc.add(Para(T.ACTIONS_INTRO))
    rows = []
    for i, f in enumerate(ctx.d.actions(), start=1):
        rows.append([_n(i, 0), T.el_fa(f.element) if f.element else "کل پروژه", f.title_fa,
                     T.ROOT_FA.get(f.root, ""),
                     Cell(T.SEVERITY_FA[f.severity], _SEV_TONE[f.severity]),
                     f.actions_fa[0], T.OWNER_FA.get(f.owner, f.owner),
                     T.TIMING_FA.get(f.timing, f.timing)])
    if rows:
        ctx.table(doc, ["ردیف", "عنصر", "مسئله", "منشأ ریشه‌ای", "شدت", "اقدام", "مسئول",
                        "زمان"],
                  rows, "برنامهٔ اقدام یکپارچه", widths=[4, 8, 22, 10, 7, 33, 9, 7],
                  compact=True)
    else:
        doc.add(Para("هیچ اقدامی لازم نیست."))


def _conclusion(ctx, doc):
    ctx.section(doc, T.H["conclusion"], "conclusion")
    for el in ctx.project.elements:
        code, text = ctx.d.verdict(el)
        doc.add(Para(f"**{T.el_fa(el)} — {T.VERDICT_FA[code]}.** {text}"))
    doc.add(Callout("info", "تذکر", T.DISCLAIMER))
    doc.add(Signature(ctx.meta))


# ---- appendices ------------------------------------------------------------------
def _app_methods(ctx, doc):
    doc.add(Heading(1, T.H["app_methods"], "app-methods", ""))
    for title, text in T.METHODS:
        doc.add(Heading(3, title))
        doc.add(Para(text))
    rows = [[_ltr(d["group"]), _ltr(d["label"]), _ltr(d["expr"])]
            for d in ctx.F.defs.values()]
    ctx.table(doc, ["گروه", "کمیت", "تعریف"], rows, "فرمول‌های به‌کاررفته در این اجرا",
              compact=True)
    doc.add(Heading(3, "منابع"))
    doc.add(Bullets([r for r in T.REFERENCES]))


def _limit_text(v, unit):
    if v is None:
        return "—"
    return f"{T.lim(v, '')} {unit}".strip() if unit != "x DL" else f"{T.lim(v, '')} × حد تشخیص"


def _app_criteria(ctx, doc):
    doc.add(Heading(1, T.H["app_criteria"], "app-criteria", ""))
    preset = ctx.RB.el.preset
    doc.add(Para(T.PRESET_USED.format(name=preset) if preset else T.PRESET_NONE))
    # R10: the acceptance limits actually used, per element
    rows = []
    EB = ctx.RB.el
    for el in ctx.project.elements:
        pr = EB.profile(el)
        Ce = criteria_for(ctx.C, ctx.RB, el)
        good = [T.lim(Ce[k]["cuts"][2]) for k in ("fdup_hard90", "cdup_hard90", "pdup_hard90",
                                                  "th_precision", "ump_hard90")]
        rows.append([_el(el), _ltr(METHOD_LABEL.get(EB.method(el), EB.method(el))),
                     _limit_text(pr["qc_dl"], pr["qc_dl_unit"]),
                     _limit_text(pr["upper"], pr["upper_unit"]),
                     _limit_text(pr["blank_warn"], pr["blank_warn_unit"]),
                     _limit_text(pr["blank_fail"], pr["blank_fail_unit"])] + good)
    if rows:
        ctx.table(doc, ["عنصر", "روش", "حد تشخیص مرجع", "حد بالا", "هشدار شاهد",
                        "ردشدگی شاهد", "HARD صحرایی", "HARD درشت", "HARD پالپ",
                        "تامپسون-هوارث", "HARD داور"], rows,
                  "حدهای پذیرش به‌کاررفته برای هر عنصر (مرز «خوب» هر معیار)", compact=True)
    rows = []
    for k, d in ctx.C.items():
        changed = k in DEFAULT_CRITERIA and [float(x) for x in d["cuts"]] != [
            float(x) for x in DEFAULT_CRITERIA[k]["cuts"]]
        rows.append([_ltr(d["label"]), _ltr(d["unit"] or "-")]
                    + [T.lim(c, "") for c in d["cuts"]]
                    + [Cell("تغییریافته", "warn") if changed else ""])
    ctx.table(doc, ["معیار", "واحد"] + [T.RATING_FA[r] for r in RATING_ORDER[:5]]
              + ["وضعیت"], rows,
              "مرزهای رتبه‌بندی پیش‌فرض (عنصرهایی که مرز خود را ندارند)؛ مقدار بدتر از "
              "آخرین مرز «خیلی بد» است", compact=True)
    # the per-method ratings, for diagnosis only: no composite number (R22)
    doc.add(Para(T.DIAGNOSTIC_GRID))
    ctx.figure(doc, "scores", "رتبهٔ هر روش برای هر عنصر (تشخیصی؛ بدون عدد ترکیبی)")


def _app_cleaning(ctx, doc):
    doc.add(Heading(1, T.H["app_cleaning"], "app-cleaning", ""))
    L = ctx.project.clean_log
    if L is None or not L.actions:
        doc.add(Para("هیچ اقدام پاک‌سازی ثبت نشد."))
        return
    acts = L.actions[:MAX_ROWS]
    rows = [[_ltr(a.rule), _ltr(a.sample), _ltr(a.element or "-"), _ltr(a.original or "-"),
             T.ACTION_FA.get(a.action, a.action), _ltr(a.reason)] for a in acts]
    ctx.table(doc, ["قاعده", "نمونه", "عنصر", "مقدار اصلی", "اقدام", "شرح"], rows,
              "دفتر پاک‌سازی"
              + (f" (نخستین {_n(MAX_ROWS, 0)} سطر از {_n(len(L.actions), 0)}؛ "
                 f"فهرست کامل در خروجی CSV)" if len(L.actions) > MAX_ROWS else ""),
              widths=[6, 12, 9, 10, 12, 51], compact=True)


def _app_failed(ctx, doc):
    doc.add(Heading(1, T.H["app_failed"], "app-failed", ""))
    R, S = ctx.R, ctx.S
    rows = []
    for (lab, el), r in sorted(R.get("crm", {}).items()):
        for p in r.get("failures", []):
            rows.append([_ltr(lab), _ltr(el), _ltr(p["sample"]), _ltr(p["batch"] or "-"),
                         _n(p["value"]), _n(r.get("cert")), _n(p["z"], 2)])
    if rows:
        ctx.table(doc, ["شاهد", "عنصر", "نمونه", "بچ", "مقدار", "گواهی", "امتیاز Z"],
                  rows[:MAX_ROWS], f"نتایج شاهد بیرون از {_n(S['k_fail'], 0)} انحراف معیار",
                  compact=True)
    rows = []
    for (bt, el), r in sorted(R.get("blank", {}).items()):
        for p in r["points"]:
            if p["fail"]:
                rows.append([T.TYPE_FA[bt], _ltr(el), _ltr(p["sample"]),
                             _ltr(p["batch"] or "-"), _n(p["value"]), _n(p["ratio"], 1),
                             _ltr(p["prev_sample"] or "-"), _n(p["prev_value"])])
    if rows:
        ctx.table(doc, ["نوع", "عنصر", "نمونه", "بچ", "مقدار", "برابر حد تشخیص",
                        "نمونهٔ قبلی", "مقدار نمونهٔ قبلی"], rows[:MAX_ROWS],
                  "شاهدهای خالی ردشده", compact=True)
    if not any(r.get("failures") for r in R.get("crm", {}).values()) and not rows:
        doc.add(Para("هیچ نمونهٔ کنترلی ردشده‌ای وجود ندارد."))


def _app_protocol(ctx, doc):
    doc.add(Heading(1, T.H["app_protocol"], "app-protocol", ""))
    S, RB = ctx.S, ctx.RB
    rows = [[_ltr(k), _ltr(str(v)),
             Cell("تغییریافته", "warn") if k in DEFAULT_SETTINGS and v != DEFAULT_SETTINGS[k]
             else ""] for k, v in S.items()]
    ctx.table(doc, ["تنظیم", "مقدار", "وضعیت"], rows, "تنظیمات تحلیل", compact=True)
    changed = set(RB.changed())
    rows = [[_ltr(d["group"]), _ltr(d["label"]), _ltr(RB.describe(k)),
             Cell("تغییریافته", "warn") if k in changed else ""]
            for k, d in RULES.items()]
    ctx.table(doc, ["گروه", "قاعده", "مقدار", "وضعیت"], rows,
              "قواعد پاک‌سازی، تشخیص و پذیرش بچ", widths=[10, 52, 28, 10], compact=True)
