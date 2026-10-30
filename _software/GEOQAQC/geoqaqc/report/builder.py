# -*- coding: utf-8 -*-
"""Build the consultant report (a document.Document) from one analysis run.

Order (spec 8): cover, document control, contents, executive summary,
introduction, data validation, QC programme, one chapter per element, action
plan, conclusion, appendices. Every section is built inside its own guard: a
failure in one section becomes a visible notice in that section, the reason
goes to the log, and the rest of the report is still produced."""

from __future__ import annotations

import os
import traceback

from ..core import (BLANK_TYPES, DUP_TYPES, R_NA, RATING_ORDER, T_NORMAL, T_PDUP,
                    fa_digits, fa_num)
from ..diagnosis import SEVERITIES, STAGES
from ..figures import figure_catalog
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
    p, R, d = ctx.project, ctx.R, ctx.d
    live = _live(p)
    n_ctrl = sum(1 for s in live if s.stype != T_NORMAL)
    batches = {s.batch for s in live if s.batch}
    verdicts = [(el, T.el_fa(el), d.verdict(el)[0]) for el in p.elements]
    stats = [("نمونه", _n(len(live), 0)), ("عنصر", _n(len(p.elements), 0)),
             ("بچ", _n(len(batches), 0) if batches else "—"),
             ("نمونهٔ کنترلی", _n(n_ctrl, 0))]
    doc.add(Cover(ctx.meta, R.get("overall", R_NA), R.get("score"), verdicts, stats))


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
            f"نمونهٔ کنترلی بوده‌اند. رتبهٔ کلی کنترل کیفیت **{T.RATING_FA.get(R.get('overall'), '—')}** "
            f"است. داده‌های {_n(codes.count('SUITABLE'), 0)} عنصر قابل استفاده، "
            f"{_n(codes.count('RESTRICTED'), 0)} عنصر قابل استفاده با محدودیت و "
            f"{_n(codes.count('REMEDIATE'), 0)} عنصر نیازمند اصلاح پیش از استفاده‌اند.")
    doc.add(Para(lead, "lead"))
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
                 Cell("برای اطلاع", "muted") if r.get("info_only") else _rating(r["rating"])]
                for r in ins["rows"]]
        ctx.table(doc, ["کلاس کنترلی", "تعداد", "نرخ درج", "تناوب", "رتبه"], rows,
                  f"نرخ درج نمونه‌های کنترلی از {_n(ins['n_total'], 0)} نمونه")
        ctx.figure(doc, "insertion", "نرخ درج هر کلاس کنترلی در برابر قرارداد پنج درصد")
    ctx.figure(doc, "scores", "کارنامهٔ کنترل کیفیت: رتبهٔ هر روش برای هر عنصر")
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
        rows.append([_ltr(lab), _n(r["n"], 0), _n(r.get("cert")), _n(r.get("obs_mean")),
                     _p(r.get("bias"), 2), _p(r.get("fail_pct"), 1),
                     _p(r.get("rsd_pct"), 2), _rating(r["rating"])])
    ctx.table(doc, ["شاهد", "تعداد", "مقدار گواهی", "میانگین", "بایاس", "بیرون از حد عمل",
                    "انحراف معیار نسبی", "رتبه"], rows, f"نتایج شاهدها برای {_el(el)}")
    dr = R.get("drift", {}).get(el)
    if dr:
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
    ctx.figure(doc, f"coverage/{el}", f"پوشش دامنهٔ عیار {T.el_fa(el)} با شاهدها")


def _el_contamination(ctx, doc, el):
    R = ctx.R
    ctx.sub(doc, T.H["contamination"])
    recs = [(bt, R["blank"][(bt, el)]) for bt in BLANK_TYPES if (bt, el) in R.get("blank", {})]
    if not recs:
        doc.add(Para(T.MISSING["blank"]))
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
    rows = []
    for dt, r in recs:
        crit = ctx.C[_DUP_CRIT[dt]]
        rows.append([T.TYPE_FA[dt], _n(r["n"], 0), _p(r["hard_p90"], 1),
                     _p(crit["cuts"][2], 0), _p(100.0 - r["maxmin"]["fail_pct"], 0),
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
    if not b or not b.get("pct"):
        doc.add(Para(T.MISSING["budget"]))
        return
    doc.add(Para(T.SECTION_INTRO["budget"]))
    rows = [[T.BUDGET_STAGE_FA.get(k, k), _p(v, 1)] for k, v in b["pct"].items()
            if v is not None]
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
def _actions(ctx, doc):
    ctx.section(doc, T.H["actions"], "actions")
    doc.add(Para(T.ACTIONS_INTRO))
    rows = []
    for i, f in enumerate(ctx.d.actions(), start=1):
        rows.append([_n(i, 0), T.el_fa(f.element) if f.element else "کل پروژه", f.title_fa,
                     T.STAGE_FA[f.stage], Cell(T.SEVERITY_FA[f.severity], _SEV_TONE[f.severity]),
                     f.actions_fa[0], T.OWNER_FA.get(f.owner, f.owner),
                     T.TIMING_FA.get(f.timing, f.timing)])
    if rows:
        ctx.table(doc, ["ردیف", "عنصر", "مسئله", "مرحله", "شدت", "اقدام", "مسئول", "زمان"],
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


def _app_criteria(ctx, doc):
    doc.add(Heading(1, T.H["app_criteria"], "app-criteria", ""))
    rows = []
    for k, d in ctx.C.items():
        changed = k in DEFAULT_CRITERIA and [float(x) for x in d["cuts"]] != [
            float(x) for x in DEFAULT_CRITERIA[k]["cuts"]]
        rows.append([_ltr(d["label"]), _ltr(d["unit"] or "-")]
                    + [_n(c) for c in d["cuts"]]
                    + [Cell("تغییریافته", "warn") if changed else ""])
    ctx.table(doc, ["معیار", "واحد"] + [T.RATING_FA[r] for r in RATING_ORDER[:5]]
              + ["وضعیت"], rows,
              "مرزهای رتبه‌بندی؛ مقدار بدتر از آخرین مرز «خیلی بد» است", compact=True)


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
