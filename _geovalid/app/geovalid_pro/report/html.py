"""Self-contained HTML technical report (fa / en). Offline: font and figures are embedded."""
from __future__ import annotations

import base64
import html
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd

from .. import __version__
from ..core.issues import SEV_RANK
from . import charts

S = {
 "title": ("گزارش اعتبارسنجی پایگاه داده گمانه‌های اکتشافی", "Exploration Drillhole Database Validation Report"),
 "exec": ("خلاصهٔ مدیریتی", "Executive summary"), "inventory": ("فهرست پایگاه داده", "Database inventory"),
 "collar": ("دهانهٔ گمانه‌ها", "Collars"), "survey": ("انحراف‌سنجی درون‌چاهی", "Downhole survey"),
 "intervals": ("جداول بازه‌ای", "Interval tables"), "assay": ("نتایج آنالیز", "Assays"), "qaqc": ("کنترل کیفیت (QA/QC)", "QA/QC"),
 "logging": ("سنگ‌شناسی، ژئوتکنیک و چگالی", "Lithology, geotechnical and density"),
 "rules": ("خلاصهٔ مسائل بر پایهٔ قاعده", "Issues by rule"), "matrix": ("ماتریس اجرای قواعد", "Rule execution matrix"),
 "issues": ("فهرست مسائل", "Issue list"), "appendix": ("پیوست: پارامترها و یادداشت‌ها", "Appendix: parameters and notes"),
 "critical": ("بحرانی", "Critical"), "error": ("خطا", "Error"), "warning": ("هشدار", "Warning"), "info": ("اطلاعات", "Info"),
 "project": ("پروژه", "Project"), "date": ("تاریخ اجرا", "Run date"), "software": ("نرم‌افزار", "Software"),
 "inputs": ("فایل‌های ورودی", "Input files"), "table": ("جدول", "Table"), "kind": ("نوع", "Type"), "rows": ("ردیف", "Rows"),
 "holes": ("گمانه", "Holes"), "metres": ("متراژ", "Metres"), "analytes": ("عنصر", "Analytes"), "file": ("فایل", "File"),
 "rule": ("قاعده", "Rule"), "title_col": ("عنوان", "Title"), "total": ("جمع", "Total"), "status": ("وضعیت", "Status"),
 "note": ("یادداشت", "Note"), "severity": ("شدت", "Severity"), "hole": ("گمانه", "Hole"), "from": ("از", "From"),
 "to": ("تا", "To"), "message": ("شرح", "Message"), "fix": ("پیشنهاد اصلاح", "Suggested fix"), "row": ("ردیف فایل", "File row"),
 "search": ("جستجو در مسائل…", "Search issues…"), "top": ("مهم‌ترین یافته‌ها", "Key findings"),
 "disclaimer": ("این نرم‌افزار ابزار پشتیبان تصمیم است. پذیرش نهایی داده‌ها برای گزارش‌دهی عمومی (JORC، NI 43-101) بر عهدهٔ شخص صلاحیت‌دار (Competent / Qualified Person) است. هیچ داده‌ای به‌طور خودکار تغییر داده نشده است؛ همهٔ اصلاحات پیشنهادی نیازمند بازبینی و ثبت دلیل هستند.",
                "This software is a decision-support tool. Final acceptance of data for public reporting (JORC, NI 43-101) remains with the Competent / Qualified Person. No data were changed automatically; every proposed correction requires review and a recorded reason."),
 "v01": ("نسخهٔ ۰٫۱: اجرای {run} قاعده از فهرست مصوب؛ قواعد دیگر در فازهای بعدی (به سند ۰۵ مراجعه شود). شاخص اطمینان داده در فاز ۴ اضافه می‌شود.",
         "Version 0.1 runs {run} rules of the approved catalogue; the rest follow in later phases (see document 05). The data confidence index arrives in Phase 4."),
 "stats": ("آمار توصیفی (نمونه‌های اصلی؛ زیر حد تشخیص = نصف حد)", "Descriptive statistics (original samples; BDL = ½ DL)"),
}


def t(key, lang):
    fa, en = S[key]
    return fa if lang == "fa" else en


def esc(x) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return ""
    if isinstance(x, float):
        return f"{x:,.4g}" if abs(x) < 1e6 else f"{x:,.0f}"
    return html.escape(str(x))


def table(df: pd.DataFrame, cols=None, headers=None, max_rows=None, cls="") -> str:
    if df is None or df.empty:
        return ""
    cols = cols or list(df.columns)
    headers = headers or cols
    d = df[cols].head(max_rows) if max_rows else df[cols]
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for _, r in d.iterrows():
        tds = []
        for c in cols:
            v = r[c]
            if c == "severity":
                tds.append(f'<td><span class="sev {esc(v).lower()}">{esc(v)}</span></td>')
            else:
                tds.append(f"<td>{esc(v)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def fig(src, caption) -> str:
    if not src:
        return ""
    return f'<figure><img src="{src}" alt=""><figcaption>{esc(caption)}</figcaption></figure>'


def _font_b64() -> str:
    data = resources.files("geovalid_pro.resources").joinpath("Vazirmatn.woff2").read_bytes()
    return base64.b64encode(data).decode()


CSS = """
@font-face{font-family:Vazirmatn;src:url(data:font/woff2;base64,__FONT__) format('woff2');font-weight:100 900}
:root{--ink:#1F2A30;--muted:#5F6B71;--line:#DDE2E5;--bg:#FFFFFF;--soft:#F4F6F7;--acc:#8A5A2B;
--c:#B2182B;--e:#E66101;--w:#C98F00;--i:#3A7FC0}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Vazirmatn,'Segoe UI',Tahoma,sans-serif;font-size:14px;line-height:1.75}
.wrap{max-width:1100px;margin:0 auto;padding:28px 20px 60px}
header{border-bottom:3px solid var(--acc);padding-bottom:14px;margin-bottom:20px}
h1{font-size:24px;margin:0 0 6px}h2{font-size:19px;margin:34px 0 10px;padding-bottom:4px;border-bottom:1px solid var(--line);color:var(--acc)}
h3{font-size:15px;margin:20px 0 8px}.meta{color:var(--muted);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}
.card{border:1px solid var(--line);border-radius:8px;padding:10px 14px;background:var(--soft)}
.card b{display:block;font-size:24px}.card.c b{color:var(--c)}.card.e b{color:var(--e)}.card.w b{color:var(--w)}.card.i b{color:var(--i)}
.tw{overflow-x:auto;margin:8px 0 16px}table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:start;vertical-align:top}
th{background:var(--soft);font-weight:600;position:sticky;top:0}tbody tr:nth-child(even){background:#FAFBFB}
.sev{display:inline-block;padding:0 6px;border-radius:4px;color:#fff;font-size:11px;font-weight:600}
.sev.critical{background:var(--c)}.sev.error{background:var(--e)}.sev.warning{background:var(--w)}.sev.info{background:var(--i)}
figure{margin:14px 0;text-align:center}figure img{max-width:100%;border:1px solid var(--line);border-radius:6px}
figcaption{font-size:12.5px;color:var(--muted);margin-top:4px}
.note{background:#FFF8EC;border-inline-start:4px solid var(--acc);padding:10px 14px;border-radius:4px;margin:12px 0}
ul.find li{margin:4px 0}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
input.q{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:6px;font:inherit;margin:6px 0}
details summary{cursor:pointer;font-weight:600;margin:8px 0}
.ltr{direction:ltr;unicode-bidi:embed}
@media (max-width:760px){.cards{grid-template-columns:1fr 1fr}.grid2{grid-template-columns:1fr}}
@media print{.q{display:none}h2{break-after:avoid}figure{break-inside:avoid}}
"""

JS = """
function gvFilter(inp){var q=inp.value.toLowerCase();document.querySelectorAll('#issues tbody tr').forEach(function(r){
r.style.display=r.textContent.toLowerCase().indexOf(q)>=0?'':'none';});}
"""


def _worst_by_hole(issues: pd.DataFrame) -> pd.Series:
    if issues.empty:
        return pd.Series(dtype=object)
    i = issues[issues["hole_id"].notna()].copy()
    i["r"] = i["severity"].map(SEV_RANK)
    return i.sort_values("r").groupby("hole_id")["severity"].first()


def _narrative(res, lang, counts, inv) -> list[str]:
    ctx, fa = res.ctx, lang == "fa"
    out = []
    nh = len(ctx.collar_u) if ctx.has("collar") else 0
    m = float(ctx.collar_u["eoh_m"].sum()) if nh and "eoh_m" in ctx.collar_u else 0
    out.append(f"پایگاه داده شامل {nh} گمانه با مجموع حدود {m:,.0f} متر حفاری در {len(inv)} جدول است." if fa else
               f"The database holds {nh} holes, about {m:,.0f} m drilled, in {len(inv)} tables.")
    c, e = counts.get("CRITICAL", 0), counts.get("ERROR", 0)
    if c:
        out.append(f"{c} مسئلهٔ بحرانی یافت شد؛ تا رفع یا مستندسازی آن‌ها داده‌ها برای مدل‌سازی قابل استفاده نیستند." if fa else
                   f"{c} critical issues were found; the data cannot be used for modelling until they are fixed or documented.")
    if e:
        out.append(f"{e} خطا موقعیت، طول، عیار یا هویت داده‌ها را تغییر می‌دهد و پیش از تخمین منابع باید اصلاح شود." if fa else
                   f"{e} errors change the position, length, grade or identity of data and must be corrected before resource estimation.")
    cm = ctx.stats.get("collar_method")
    if cm is not None and len(cm):
        weak = cm["inferred_method"].isin(["HANDHELD_GPS", "PLANNED", "DIGITISED"]).sum()
        if weak:
            out.append(f"مختصات {weak} دهانه ({weak / len(cm):.0%}) احتمالاً با GPS دستی، از طراحی یا از نقشه به دست آمده است؛ برداشت مجدد با DGPS/RTK پیش از تخمین منابع توصیه می‌شود (JORC جدول ۱، موقعیت نقاط داده)." if fa else
                       f"{weak} collars ({weak / len(cm):.0%}) were probably located by handheld GPS, from the design or from a map; re-survey with DGPS/RTK before resource estimation (JORC Table 1, location of data points).")
    dz = ctx.stats.get("dz")
    if dz is not None and dz.notna().sum():
        d = dz.dropna()
        out.append(f"اختلاف ارتفاع دهانه با توپوگرافی: میانه {d.median():+.2f} متر، انحراف معیار مقاوم {1.4826 * (d - d.median()).abs().median():.2f} متر (n = {len(d)})." if fa else
                   f"Collar minus topography: median {d.median():+.2f} m, robust SD {1.4826 * (d - d.median()).abs().median():.2f} m (n = {len(d)}).")
    ex = ctx.stats.get("spatial_excluded") or []
    if ex:
        out.append(f"{len(ex)} دهانه با خطای موقعیت ({', '.join(map(str, ex[:6]))}) از آمار فاصله‌داری و نقشه‌ها کنار گذاشته شد." if fa else
                   f"{len(ex)} collars with location errors ({', '.join(map(str, ex[:6]))}) were excluded from spacing statistics and maps.")
    ce = ctx.stats.get("clark_evans", {})
    if "R" in ce:
        kind = ("خوشه‌ای" if ce["R"] < 0.8 else "منظم" if ce["R"] > 1.2 else "تصادفی") if fa else ("clustered" if ce["R"] < 0.8 else "regular" if ce["R"] > 1.2 else "random")
        out.append(f"آرایش دهانه‌ها {kind} است (شاخص کلارک–ایوانز R = {ce['R']:.2f}؛ میانگین فاصلهٔ نزدیک‌ترین همسایه {ce['mean_nn']:.0f} متر)." if fa else
                   f"Collar pattern is {kind} (Clark–Evans R = {ce['R']:.2f}; mean nearest-neighbour distance {ce['mean_nn']:.0f} m).")
    if not ctx.has("qaqc") and ctx.has("assay"):
        out.append("هیچ دادهٔ کنترل کیفیتی شناسایی نشد؛ این یک کمبود بحرانی برای گزارش‌دهی عمومی است (JORC جدول ۱، کیفیت داده‌های آنالیز)." if fa else
                   "No QA/QC data were identified: a critical gap for public reporting (JORC Table 1, quality of assay data).")
    return out


def build_report(res, lang, sm, inv, ast) -> str:
    fa = lang == "fa"
    ctx, iss = res.ctx, res.issues
    counts = iss["severity"].value_counts().to_dict() if not iss.empty else {}
    n_run = int((res.matrix["status"] == "RUN").sum())
    worst = _worst_by_hole(iss)
    parts = []
    head = f"""<header><h1>{t('title', lang)}</h1>
<div class="meta">{t('project', lang)}: <b>{esc(res.spec.project_name)}</b> · {t('date', lang)}: <span class="ltr">{esc(res.started.replace('T', ' '))}</span> ·
{t('software', lang)}: <span class="ltr">GEOVALID PRO {__version__}</span> · run <span class="ltr">{esc(res.run_id[:8])}</span></div></header>"""
    parts.append(head)
    cards = "".join(f'<div class="card {k[0].lower()}"><span>{t(k.lower(), lang)}</span><b>{counts.get(k, 0)}</b></div>'
                    for k in ("CRITICAL", "ERROR", "WARNING", "INFO"))
    find = "".join(f"<li>{esc(s)}</li>" for s in _narrative(res, lang, counts, inv))
    top = sm["by_rule"].head(10).reset_index() if not sm["by_rule"].empty else pd.DataFrame()
    title_col = "title_fa" if fa else "title_en"
    parts.append(f"<h2>1. {t('exec', lang)}</h2><div class='cards'>{cards}</div><h3>{t('top', lang)}</h3><ul class='find'>{find}</ul>")
    if not top.empty:
        parts.append(table(top, ["rule_id", title_col, "CRITICAL", "ERROR", "WARNING", "INFO", "total"],
                           [t("rule", lang), t("title_col", lang), "C", "E", "W", "I", t("total", lang)]))
    parts.append(f"<div class='note'>{esc(t('v01', lang).format(run=n_run))}</div>")
    parts.append(fig(charts.family_bar(iss), "مسائل بر پایهٔ خانوادهٔ قاعده و شدت" if fa else "Issues by rule family and severity"))
    # inventory
    parts.append(f"<h2>2. {t('inventory', lang)}</h2>")
    parts.append(table(inv, ["table", "kind", "source", "rows", "holes", "metres", "analytes"],
                       [t("table", lang), t("kind", lang), t("file", lang), t("rows", lang), t("holes", lang), t("metres", lang), t("analytes", lang)]))
    files = pd.DataFrame([{"file": Path(i.raw.source).name, "sheet": i.raw.sheet or "", "kind": i.kind, "sha256": i.raw.sha256[:16] + "…"}
                          for i in res.spec.inputs])
    parts.append(f"<details><summary>{t('inputs', lang)}</summary>{table(files)}</details>")
    # collar
    if ctx.has("collar"):
        parts.append(f"<h2>3. {t('collar', lang)}</h2>")
        parts.append(fig(charts.collar_map(ctx, worst), "موقعیت دهانه‌ها بر پایهٔ شدیدترین مسئله و مسیر گمانه‌ها" if fa else "Collars coloured by worst issue, with desurveyed traces"))
        nn = ctx.stats.get("nn")
        ce = ctx.stats.get("clark_evans", {})
        g = []
        if nn is not None:
            g.append(fig(charts.hist(nn["nn1_m"], "Nearest-neighbour distance", "Distance (m)"),
                         "توزیع فاصلهٔ نزدیک‌ترین همسایه" if fa else "Nearest-neighbour distance distribution"))
        cm = ctx.stats.get("collar_method")
        if cm is not None:
            g.append(fig(charts.method_bar(cm), "روش استنتاجی برداشت مختصات دهانه (نسخهٔ پیش‌نمایش)" if fa else "Inferred collar survey method (preview)"))
        parts.append(f"<div class='grid2'>{''.join(g)}</div>")
        if ce.get("R"):
            parts.append(table(pd.DataFrame([{"n": ce["n"], "Clark–Evans R": round(ce["R"], 3), "mean NN (m)": round(ce["mean_nn"], 1),
                                              "expected NN (m)": round(ce["expected_nn"], 1), "holes / km²": round(ce["density_per_km2"], 2)}])))
        if "dz" in ctx.stats:
            d = ctx.stats["dz"]
            g2 = [fig(charts.hist(d, "ΔZ collar − topography", "ΔZ (m)", vline=[-2, 2, -5, 5]),
                      "توزیع اختلاف ارتفاع دهانه و توپوگرافی (خطوط: ±۲ و ±۵ متر)" if fa else "ΔZ distribution (lines: ±2 and ±5 m)"),
                  fig(charts.dz_map(ctx), "نقشهٔ ΔZ" if fa else "ΔZ map")]
            parts.append(f"<div class='grid2'>{''.join(g2)}</div>")
        if cm is not None:
            weak = cm[cm["inferred_method"] != "SURVEYED"]
            parts.append(f"<details><summary>{'شواهد روش برداشت مختصات' if fa else 'Collar method evidence'} ({len(cm)})</summary>"
                         f"{table(cm, ['hole_id', 'inferred_method', 'confidence_pct', 'declared_method', 'evidence'], max_rows=1000)}</details>")
    # survey
    if ctx.has("traces"):
        parts.append(f"<h2>4. {t('survey', lang)}</h2>")
        dls = pd.concat([tr["dogleg_deg"] * 30 / tr["depth_m"].diff() for tr in ctx.traces.values()])
        parts.append(fig(charts.hist(dls[np.isfinite(dls)], "Dogleg severity per segment", "°/30 m", vline=[3, 6]),
                         "توزیع شدت خمیدگی (خطوط: آستانهٔ هشدار ۳ و خطای ۶ درجه بر ۳۰ متر)" if fa else "Dogleg severity (lines: warning 3 and error 6 °/30 m)"))
        parts.append(f"<p>{'قرارداد شیب' if fa else 'Dip convention'}: <span class='ltr'>{esc(ctx.dip_convention)}</span></p>")
    # intervals
    if ctx.interval_tables:
        parts.append(f"<h2>5. {t('intervals', lang)}</h2>")
        if not sm["by_table"].empty:
            parts.append(table(sm["by_table"].reset_index(), None, [t("table", lang), "C", "E", "W", "I"]))
        for tb in ctx.by_kind("assay")[:2]:
            L = (tb.df["to_m"] - tb.df["from_m"])
            parts.append(fig(charts.hist(L[(L > 0) & (L < 20)], f"Sample length – {tb.name}", "Length (m)"),
                             ("توزیع طول نمونه‌ها: " if fa else "Sample length distribution: ") + tb.name))
        cc = ctx.stats.get("contact_crossing", {})
        for name, (n, tot) in cc.items():
            parts.append(f"<p>{name}: {n} / {tot} {'نمونه از همبری سنگ‌شناسی عبور می‌کنند' if fa else 'samples cross a lithology contact'} ({100 * n / max(tot, 1):.1f}%).</p>")
    # assays
    if ast is not None and not ast.empty:
        parts.append(f"<h2>6. {t('assay', lang)}</h2><h3>{t('stats', lang)}</h3>")
        parts.append(table(ast, ["table", "column", "unit", "unit_source", "n", "pct_bdl", "min", "median", "mean", "mean_lw", "p95", "max", "cv"],
                           ["table", "column", "unit", "unit src", "n", "% BDL", "min", "P50", "mean", "mean (LW)", "P95", "max", "CV"]))
        keys = ctx.params.get("key_analytes", [])
        series, frame = {}, {}
        from ..rules.interval import QC_TYPES
        for tb in ctx.tables:
            orig = ~tb.df["qc_class"].isin(QC_TYPES) if "qc_class" in tb.df else pd.Series(True, index=tb.df.index)
            for a in tb.analytes:
                if not a.partial:
                    v = a.parsed["value_policy"].where(orig)
                    frame.setdefault(a.analyte, v)
                    if a.analyte in keys and len(series) < 6:
                        series.setdefault(a.analyte, v)
        parts.append(fig(charts.logprob(series), "نمودار احتمال لگاریتمی عناصر کلیدی" if fa else "Log-probability plots of key analytes"))
        fr = pd.DataFrame(frame)
        if fr.shape[1] > 15:
            fr = fr[fr.count().sort_values(ascending=False).index[:15]]
        parts.append(fig(charts.corr_heatmap(fr), "همبستگی اسپیرمن بین عناصر (لگاریتمی)" if fa else "Spearman correlation between analytes (log values)"))
    # qaqc
    if ctx.has("assay"):
        parts.append(f"<h2>7. {t('qaqc', lang)}</h2>")
        rates = ctx.stats.get("qaqc_rates", {})
        if rates:
            rows = [{"table": k, "originals": n, **{kk: round(v, 2) for kk, v in r.items()}} for k, (n, r) in rates.items()]
            parts.append(table(pd.DataFrame(rows)))
        else:
            parts.append(f"<div class='note'>{'دادهٔ کنترل کیفیت شناسایی نشد (QAQ-001: بحرانی).' if fa else 'No QA/QC data identified (QAQ-001: CRITICAL).'}</div>")
        for name, s in ctx.stats.get("crm_results", {}).items():
            parts.append(fig(charts.crm_chart(s), "نمودار کنترل مواد مرجع" if fa else "CRM control chart"))
        for name, items in ctx.stats.get("blank_results", {}).items():
            parts.append(fig(charts.blank_chart(items), "نتایج بلانک‌ها" if fa else "Blank results"))
        parts.append(fig(charts.hard_chart(ctx.stats.get("dup_pairs", {})), "نمودار رتبه‌ای HARD نمونه‌های تکراری" if fa else "Ranked HARD plot"))
    # logging
    inv_l = ctx.stats.get("lith_inventory", {})
    if inv_l or ctx.by_kind("geotech") or ctx.by_kind("density"):
        parts.append(f"<h2>8. {t('logging', lang)}</h2>")
        for name, df in inv_l.items():
            parts.append(f"<h3>{esc(name)}</h3>" + table(df.reset_index().rename(columns={"index": "code", "lith_code": "code"}).round(1), max_rows=60))
        for name, (an, rec, val) in ctx.stats.get("recovery_grade", {}).items():
            parts.append(fig(charts.recovery_grade(rec, val, an), "بازیافت مغزه در برابر عیار" if fa else "Core recovery vs grade"))
    # rules
    parts.append(f"<h2>9. {t('rules', lang)}</h2>")
    if not sm["by_rule"].empty:
        parts.append(table(sm["by_rule"].reset_index(), ["rule_id", title_col, "CRITICAL", "ERROR", "WARNING", "INFO", "total"],
                           [t("rule", lang), t("title_col", lang), "C", "E", "W", "I", t("total", lang)]))
    parts.append(f"<details><summary>{t('matrix', lang)} ({len(res.matrix)})</summary>"
                 f"{table(res.matrix, ['rule_id', title_col, 'status', 'n_issues', 'note'], [t('rule', lang), t('title_col', lang), t('status', lang), 'n', t('note', lang)])}</details>")
    # issues
    msg = "message_fa" if fa else "message_en"
    parts.append(f"<h2>10. {t('issues', lang)}</h2><input class='q' placeholder='{t('search', lang)}' oninput='gvFilter(this)'>")
    parts.append(table(iss, ["issue_id", "severity", "rule_id", "table", "hole_id", "from_m", "to_m", "src_row", msg, "suggested_fix"],
                       ["#", t("severity", lang), t("rule", lang), t("table", lang), t("hole", lang), t("from", lang), t("to", lang),
                        t("row", lang), t("message", lang), t("fix", lang)], max_rows=3000, cls="issues").replace("<table", "<table id='issues'", 1))
    if len(iss) > 3000:
        parts.append(f"<p>{'فهرست کامل در فایل issue_log.xlsx است.' if fa else 'The full list is in issue_log.xlsx.'}</p>")
    # appendix
    parts.append(f"<h2>11. {t('appendix', lang)}</h2><div class='note'>{esc(t('disclaimer', lang))}</div>")
    if res.errors:
        parts.append("<h3>Run messages</h3><pre class='ltr'>" + esc("\n".join(res.errors[:40])) + "</pre>")
    prm = pd.DataFrame([{"rule": k, "parameters": ", ".join(f"{a}={b}" for a, b in v.items())}
                        for k, v in ctx.params.get("rules", {}).items()])
    parts.append(f"<details><summary>{'پارامترهای به‌کاررفته' if fa else 'Parameters used'}</summary>{table(prm)}</details>")
    css = CSS.replace("__FONT__", _font_b64())
    return (f"<!doctype html><html lang='{lang}' dir='{'rtl' if fa else 'ltr'}'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>GEOVALID PRO – {esc(res.spec.project_name)}</title>"
            f"<style>{css}</style><script>{JS}</script></head><body><div class='wrap'>{''.join(parts)}</div></body></html>")
