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
 "geology": ("تحلیل عیار بر پایهٔ واحدهای توصیفی", "Grade versus logged geology"),
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
 "contents": ("فهرست مطالب", "Contents"), "samples": ("نمونهٔ اصلی", "Original samples"), "rules_run": ("قاعدهٔ اجراشده", "Rules run"),
 "disclaimer": ("این نرم‌افزار ابزار پشتیبان تصمیم است. پذیرش نهایی داده‌ها برای گزارش‌دهی عمومی (JORC، NI 43-101) بر عهدهٔ شخص صلاحیت‌دار (Competent / Qualified Person) است. هیچ داده‌ای به‌طور خودکار تغییر داده نشده است؛ همهٔ اصلاحات پیشنهادی نیازمند بازبینی و ثبت دلیل هستند.",
                "This software is a decision-support tool. Final acceptance of data for public reporting (JORC, NI 43-101) remains with the Competent / Qualified Person. No data were changed automatically; every proposed correction requires review and a recorded reason."),
 "v01": ("نسخهٔ {ver}: اجرای {run} قاعده از فهرست مصوب؛ قواعد دیگر در فازهای بعدی (به سند ۰۵ مراجعه شود). شاخص اطمینان داده در فاز ۴ اضافه می‌شود.",
         "Version {ver} runs {run} rules of the approved catalogue; the rest follow in later phases (see document 05). The data confidence index arrives in Phase 4."),
 "stats": ("آمار توصیفی (نمونه‌های اصلی؛ زیر حد تشخیص = نصف حد)", "Descriptive statistics (original samples; BDL = ½ DL)"),
 "geo_intro": ("هر نمونهٔ اصلی رده‌ای را می‌گیرد که در نقطهٔ میانی آن در جداول سنگ‌شناسی، دگرسانی، هوازدگی و سایر ستون‌های توصیفی ثبت شده است. شدت ارتباط با η² (نسبت همبستگی روی لگاریتم عیار؛ سهم واریانس توضیح‌داده‌شده) و آزمون ناپارامتری کروسکال–والیس سنجیده می‌شود. η² بالای ۰٫۳ کنترل قوی، ۰٫۱ تا ۰٫۳ متوسط و کمتر از ۰٫۱ ضعیف است. ارتباط آماری الزاماً رابطهٔ علّی نیست.",
               "Each original sample takes the category logged at its mid-point in the lithology, alteration, weathering and other coded logging columns. Association is measured by η² (correlation ratio of log grade: the share of variance explained) and the non-parametric Kruskal–Wallis test. η² above 0.3 is a strong control, 0.1–0.3 moderate, below 0.1 weak. Association is not causation."),
}


def t(key, lang):
    fa, en = S[key]
    return fa if lang == "fa" else en


def esc(x) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return ""
    if isinstance(x, (float, np.floating)):
        x = float(x)
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
            elif isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool):
                tds.append(f"<td class='num'>{esc(v)}</td>")
            else:
                tds.append(f"<td>{esc(v)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def fig(src, caption, wide=False) -> str:
    src = charts.png(src)
    if not src:
        return ""
    return f'<figure class="{"wide" if wide else ""}"><img src="{src}" alt=""><figcaption>{esc(caption)}</figcaption></figure>'


def _font_b64() -> str:
    data = resources.files("geovalid_pro.resources").joinpath("Vazirmatn.woff2").read_bytes()
    return base64.b64encode(data).decode()


CSS = """
@font-face{font-family:Vazirmatn;src:url(data:font/woff2;base64,__FONT__) format('woff2');font-weight:100 900}
:root{--ink:#1E2A32;--muted:#5F6B76;--line:#E3E7EA;--bg:#F7F5F0;--paper:#FFFFFF;--soft:#FBFAF7;--gold:#B07D3A;--gold2:#D4A85A;
--night:#141A21;--night2:#1C2530;--teal:#0F7173;--c:#9B2226;--e:#CA6702;--w:#EE9B00;--i:#0A9396;--r:14px}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Vazirmatn,'Segoe UI',Tahoma,sans-serif;font-size:14px;line-height:1.8}
.hero{background:radial-gradient(1200px 400px at 85% -10%,rgba(212,168,90,.22),transparent 60%),linear-gradient(135deg,var(--night),var(--night2));
color:#ECE6DA;padding:34px 0 30px;border-bottom:3px solid var(--gold)}
.hero .in{max-width:1360px;margin:0 auto;padding:0 28px}
.brand{display:flex;align-items:center;gap:10px;letter-spacing:.24em;font-size:11.5px;color:var(--gold2);font-weight:700;text-transform:uppercase}
.brand i{display:inline-block;width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,var(--gold2),var(--gold));
box-shadow:0 0 0 1px rgba(255,255,255,.12) inset}
.hero h1{font-size:28px;line-height:1.35;margin:12px 0 10px;font-weight:800;color:#FBF7EF}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.chip{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:999px;padding:3px 12px;font-size:12.5px;color:#D9D3C7}
.chip b{color:#FBF7EF;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(8,1fr);gap:10px;margin-top:22px}
.kpi{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.10);border-radius:12px;padding:10px 14px}
.kpi span{display:block;font-size:11.5px;color:#AEB6BF}.kpi b{display:block;font-size:24px;font-weight:800;color:#FBF7EF;line-height:1.3}
.kpi.c{border-top:3px solid var(--c)}.kpi.e{border-top:3px solid var(--e)}.kpi.w{border-top:3px solid var(--w)}.kpi.i{border-top:3px solid var(--i)}
.kpi.g{border-top:3px solid var(--gold2)}
.layout{max-width:1360px;margin:0 auto;padding:26px 28px 70px;display:grid;grid-template-columns:220px 1fr;gap:26px}
nav.toc{position:sticky;top:18px;align-self:start;background:var(--paper);border:1px solid var(--line);border-radius:var(--r);padding:16px 14px;
box-shadow:0 1px 2px rgba(20,26,33,.04)}
nav.toc h4{margin:0 0 8px;font-size:12px;letter-spacing:.12em;color:var(--gold);text-transform:uppercase}
nav.toc a{display:flex;gap:8px;color:var(--ink);text-decoration:none;font-size:13px;padding:4px 6px;border-radius:7px}
nav.toc a:hover{background:var(--soft);color:var(--gold)}nav.toc a span{color:var(--gold);font-weight:700;min-width:18px}
main{min-width:0}
section{background:var(--paper);border:1px solid var(--line);border-radius:var(--r);padding:22px 26px;margin-bottom:22px;
box-shadow:0 1px 2px rgba(20,26,33,.04),0 8px 24px -18px rgba(20,26,33,.18)}
h2{display:flex;align-items:baseline;gap:12px;font-size:20px;margin:0 0 14px;padding-bottom:10px;border-bottom:1px solid var(--line)}
h2 .n{font-size:13px;color:#fff;background:linear-gradient(135deg,var(--gold2),var(--gold));border-radius:8px;padding:1px 9px;font-weight:700}
h3{font-size:15px;margin:22px 0 8px;color:var(--ink)}h3::before{content:"";display:inline-block;width:8px;height:8px;border-radius:2px;
background:var(--gold2);margin-inline-end:8px;vertical-align:middle}
.lead{color:var(--muted);font-size:13.5px;margin:-4px 0 12px}
.tw{overflow-x:auto;margin:10px 0 16px;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border-bottom:1px solid var(--line);padding:6px 10px;text-align:start;vertical-align:top}
th{background:var(--soft);font-weight:700;font-size:11.5px;color:var(--muted);letter-spacing:.02em;position:sticky;top:0}
td.num{font-variant-numeric:tabular-nums;direction:ltr;text-align:end}
tbody tr:hover{background:#FBF6EC}tbody tr:last-child td{border-bottom:none}
.sev{display:inline-block;padding:0 8px;border-radius:999px;color:#fff;font-size:11px;font-weight:700}
.sev.critical{background:var(--c)}.sev.error{background:var(--e)}.sev.warning{background:var(--w)}.sev.info{background:var(--i)}
figure{margin:12px 0;background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:10px;text-align:center}
figure img{max-width:100%;height:auto;border-radius:6px}
figcaption{font-size:12.5px;color:var(--muted);margin-top:6px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}.grid2>figure{margin:0}
.note{background:linear-gradient(90deg,#FFF7E8,#FFFDF8);border-inline-start:4px solid var(--gold2);padding:10px 16px;border-radius:10px;margin:12px 0;color:#4A3F2E}
.find{list-style:none;padding:0;margin:8px 0}.find li{position:relative;padding:6px 26px 6px 0;margin:2px 0;border-bottom:1px dashed var(--line)}
html[dir=ltr] .find li{padding:6px 0 6px 26px}
.find li::before{content:"";position:absolute;inset-inline-start:4px;top:15px;width:9px;height:9px;border-radius:50%;background:var(--gold2)}
input.q{width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:10px;font:inherit;margin:6px 0;background:var(--soft)}
details{margin:10px 0}details summary{cursor:pointer;font-weight:700;color:var(--teal);margin:6px 0}
.ltr{direction:ltr;unicode-bidi:embed}
footer{max-width:1360px;margin:0 auto;padding:0 28px 40px;color:var(--muted);font-size:12px}
@media (max-width:1000px){.layout{grid-template-columns:1fr}nav.toc{position:static}.kpis{grid-template-columns:repeat(4,1fr)}}
@media (max-width:700px){.kpis{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}section{padding:16px}
.hero h1{font-size:22px}}
@media print{body{background:#fff}.q,nav.toc{display:none}.layout{display:block;padding:0}section{box-shadow:none;break-inside:avoid-page}
figure{break-inside:avoid}.hero{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
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
        out.append(f"{len(ex)} دهانه با خطای موقعیت ({', '.join(map(str, ex[:6]))}) از آمار فاصله‌داری، نقشه‌ها و تحلیل‌های مکانی عیار کنار گذاشته شد." if fa else
                   f"{len(ex)} collars with location errors ({', '.join(map(str, ex[:6]))}) were excluded from spacing statistics, maps and spatial grade analyses.")
    ce = ctx.stats.get("clark_evans", {})
    if "R" in ce:
        kind = ("خوشه‌ای" if ce["R"] < 0.8 else "منظم" if ce["R"] > 1.2 else "تصادفی") if fa else ("clustered" if ce["R"] < 0.8 else "regular" if ce["R"] > 1.2 else "random")
        out.append(f"آرایش دهانه‌ها {kind} است (شاخص کلارک–ایوانز R = {ce['R']:.2f}؛ میانگین فاصلهٔ نزدیک‌ترین همسایه {ce['mean_nn']:.0f} متر)." if fa else
                   f"Collar pattern is {kind} (Clark–Evans R = {ce['R']:.2f}; mean nearest-neighbour distance {ce['mean_nn']:.0f} m).")
    if not ctx.has("qaqc") and ctx.has("assay"):
        out.append("هیچ دادهٔ کنترل کیفیتی شناسایی نشد؛ این یک کمبود بحرانی برای گزارش‌دهی عمومی است (JORC جدول ۱، کیفیت داده‌های آنالیز)." if fa else
                   "No QA/QC data were identified: a critical gap for public reporting (JORC Table 1, quality of assay data).")
    geo = ctx.stats.get("categorical", {})
    assoc = geo.get("association")
    if isinstance(assoc, pd.DataFrame) and not assoc.empty:
        top = assoc.sort_values("eta2", ascending=False).iloc[0]
        f = geo["fields"].get(top["field"], (top["field"], top["field"], ""))
        out.append(f"قوی‌ترین کنترل زمین‌شناختی بر عیار: {f[1]} برای {top['analyte']} (η² = {top['eta2']:.2f}؛ بیشترین میانه در {top['top_category']}). بخش «{t('geology', 'fa')}» را ببینید." if fa else
                   f"Strongest geological control on grade: {f[0]} for {top['analyte']} (η² = {top['eta2']:.2f}; highest median in {top['top_category']}). See “{t('geology', 'en')}”.")
    return out


def _geology_section(res, lang, num) -> str:
    """Grade versus logged geology: association, box plots, two-way medians, domains, contacts, spatial trends."""
    from ..analysis import categorical as C
    ctx, fa = res.ctx, lang == "fa"
    smp, units, fields = C.sample_table(ctx)
    if smp.empty or not fields:
        return ""
    cat = ctx.stats["categorical"]
    assoc = cat.get("association")
    if assoc is None:
        assoc = cat["association"] = C.association(smp, fields, list(units))
    if assoc.empty:
        return ""
    labels = {f: (v[1] if fa else v[0]) for f, v in fields.items()}
    prim = C.primary_analytes(assoc, units, ctx.params, 2)
    a = prim[0]
    unit = units[a]
    cut = C.cutoff_for(smp, a, unit, ctx.params)
    P = [f"<section id='s{num}'><h2><span class='n'>{num}</span>{t('geology', lang)}</h2><p class='lead'>{esc(t('geo_intro', lang))}</p>"]
    P.append(f"<h3>{'کدام ویژگی‌ها عیار را کنترل می‌کنند؟' if fa else 'Which logged attributes control grade?'}</h3>")
    P.append(fig(charts.association_heatmap(assoc, labels, lang), "ماتریس η²: سهم واریانس لگاریتم عیار که هر ویژگی توصیفی توضیح می‌دهد" if fa else
                 "η² matrix: share of log-grade variance explained by each logged attribute", wide=True))
    lines = C.narrative(assoc, fields, units, a, lang)
    if lines:
        P.append("<ul class='find'>" + "".join(f"<li>{esc(x)}</li>" for x in lines[:6]) + "</ul>")
    at = assoc.assign(field=assoc["field"].map(labels)).sort_values("eta2", ascending=False)
    P.append(f"<details><summary>{'جدول کامل ارتباط' if fa else 'Full association table'} ({len(at)})</summary>" +
             table(at.round(4), ["field", "analyte", "n", "groups", "eta2", "kw_p", "epsilon2", "top_category", "top_median", "low_category", "low_median"],
                   ["field", "analyte", "n", "k", "η²", "KW p", "ε²", "top", "P50 top", "low", "P50 low"]) + "</details>")
    # box plots per logged field
    logging = [f for f, v in fields.items() if v[2] == "logging"]
    strong = set(assoc[(assoc["analyte"] == a) & (assoc["eta2"] >= 0.05)]["field"])
    others = [f for f, v in fields.items() if v[2] != "logging" and f in strong]
    P.append(f"<h3>{f'توزیع عیار {a} در هر واحد' if fa else f'{a} grade distribution by unit'}</h3>")
    figs = []
    for f in logging + others[:2]:
        row = assoc[(assoc["field"] == f) & (assoc["analyte"] == a)]
        rd = row.iloc[0].to_dict() if len(row) else None
        figs.append(fig(charts.grade_by_category(smp, f, a, unit, labels[f], cut, rd, lang),
                        (f"عیار {a} به تفکیک {labels[f]} — مقیاس لگاریتمی؛ لوزی: میانگین وزنی طولی؛ خط‌چین: عیار حد" if fa else
                         f"{a} by {labels[f]} — log scale; diamond: length-weighted mean; dashed: cut-off")))
    P.append("".join(figs))
    stats = []
    for f in logging:
        st = C.category_stats(smp, f, a, cut)
        if not st.empty:
            stats.append(f"<h4>{esc(labels[f])}</h4>" + table(st.round(4), ["category", "n", "metres", "mean_lw", "median", "p10", "p90", "max", "cv", "pct_above_cutoff"],
                                                               ["category", "n", "m", "mean (LW)", "P50", "P10", "P90", "max", "CV", f"% ≥ {cut:.3g}"]))
    if stats:
        P.append(f"<details><summary>{'آمار عیار در هر واحد' if fa else 'Grade statistics by unit'} ({a}, {unit})</summary>{''.join(stats)}</details>")
    # two-way and field association
    g2 = []
    if len(logging) >= 2:
        med, cnt = C.two_way(smp, logging[0], logging[1], a)
        g2.append(fig(charts.two_way_heatmap(med, cnt, labels[logging[0]], labels[logging[1]], a, unit, lang),
                      f"میانهٔ {a} در ترکیب {labels[logging[0]]} و {labels[logging[1]]}" if fa else f"Median {a} for each {labels[logging[0]]} × {labels[logging[1]]} combination"))
    g2.append(fig(charts.field_association(smp, fields, lang),
                  "V کرامر بین ویژگی‌های توصیفی؛ مقادیر بالا یعنی دو ویژگی هم‌پوشان‌اند و اثرشان از هم جدا نمی‌شود" if fa else
                  "Cramér's V between logged attributes; high values mean two attributes overlap and their effects cannot be separated"))
    if any(g2):
        P.append(f"<h3>{'ترکیب واحدها' if fa else 'Unit combinations'}</h3><div class='grid2'>{''.join(g2)}</div>")
    # domains and contacts
    dom = cat.get("domains")
    if isinstance(dom, pd.DataFrame) and not dom.empty:
        P.append(f"<h3>{'پیشنهاد دامنه‌های تخمین (CRS-004)' if fa else 'Candidate estimation domains (CRS-004)'}</h3>")
        P.append(f"<p class='lead'>{'رده‌های مجاور (به ترتیب میانه) که عیارشان از نظر آماری یا عملی تفاوتی ندارد با + ادغام شده‌اند؛ | مرز دامنه‌هاست.' if fa else 'Adjacent categories (by median) whose grades do not differ statistically or practically are joined with +; | separates domains.'}</p>")
        d = dom.assign(field=dom["field"].map(labels))
        P.append(table(d.round(3), ["field", "analyte", "eta2", "suggested_domains"], ["field", "analyte", "η²", "suggested domains"]))
    contacts = cat.get("contacts") or []
    if contacts:
        P.append(f"<h3>{'تحلیل همبری: مرز سخت یا نرم (CRS-005)' if fa else 'Contact analysis: hard or soft boundaries (CRS-005)'}</h3>")
        P.append(fig(charts.contact_plot(contacts, units, lang, labels=labels),
                     "عیار در برابر فاصله تا مرز واحد؛ پرش ناگهانی = مرز سخت (تخمین جداگانه)، تغییر تدریجی = مرز نرم (اشتراک نمونه‌ها)" if fa else
                     "Grade against distance to the unit boundary; a step = hard boundary (estimate separately), a ramp = soft boundary (share samples)", wide=True))
    # spatial
    P.append(f"<h3>{'روندهای مکانی عیار' if fa else 'Spatial grade trends'}</h3>")
    P.append(fig(charts.swath_plots(smp, a, unit, lang), "نمودارهای نواری در جهت شرقی، شمالی و ارتفاع" if fa else "Swath plots along easting, northing and elevation", wide=True))
    g3 = [fig(charts.gt_map(C.hole_grades(smp, ctx, a, cut), a, unit, cut, ctx.licence, lang),
              "عیار × ضخامت در هر گمانه بالای عیار حد" if fa else "Grade × thickness per hole above the cut-off"),
          fig(charts.grade_length_curve(smp, a, unit, lang), "منحنی عیار–متراژ (پیش‌نمایش منحنی عیار–تناژ)" if fa else "Grade–length curve (preview of a grade–tonnage curve)")]
    P.append(f"<div class='grid2'>{''.join(g3)}</div>")
    # depth, physical properties, strip log
    g4 = []
    for f in logging[:2]:
        g4.append(fig(charts.composition_depth(smp, f, labels[f], lang), f"سهم هر رده از {labels[f]} با عمق" if fa else f"Share of each {labels[f]} class with depth"))
    phys = C.physical_table(ctx)
    if not phys.empty and logging:
        for var in ("Density g/cm³", "RQD %"):
            g4.append(fig(charts.physical_by_category(phys, logging[0], var, labels[logging[0]], lang),
                          (f"{'چگالی' if var.startswith('D') else 'RQD'} به تفکیک {labels[logging[0]]}" if fa else f"{var} by {labels[logging[0]]}")))
    if any(g4):
        P.append(f"<h3>{'عمق و ویژگی‌های فیزیکی' if fa else 'Depth and physical properties'}</h3><div class='grid2'>{''.join(g4)}</div>")
    hg = C.hole_grades(smp, ctx, a, cut)
    if not hg.empty:
        best = hg.sort_values("gt", ascending=False)["hole_id"].iloc[0]
        P.append(fig(charts.strip_log(smp, best, prim + [x for x in units if x not in prim][:1], fields, units, lang),
                     f"لاگ ستونی گمانهٔ {best} (بیشترین عیار×ضخامت): زمین‌شناسی ثبت‌شده در کنار عیار" if fa else
                     f"Strip log of {best} (largest grade × thickness): logged geology beside grade", wide=True))
    P.append("</section>")
    return "".join(P)


def build_report(res, lang, sm, inv, ast) -> str:
    fa = lang == "fa"
    ctx, iss = res.ctx, res.issues
    counts = iss["severity"].value_counts().to_dict() if not iss.empty else {}
    n_run = int((res.matrix["status"] == "RUN").sum())
    worst = _worst_by_hole(iss)
    sections = []        # (anchor number, title)
    body = []

    def sec(key, content, num):
        sections.append((num, t(key, lang)))
        body.append(f"<section id='s{num}'><h2><span class='n'>{num}</span>{t(key, lang)}</h2>{content}</section>")

    from ..rules.interval import QC_TYPES
    n_orig = 0
    for tb in ctx.by_kind("assay"):
        n_orig += int((~tb.df["qc_class"].isin(QC_TYPES)).sum()) if "qc_class" in tb.df else len(tb.df)
    nh = len(ctx.collar_u) if ctx.has("collar") else 0
    metres = float(ctx.collar_u["eoh_m"].sum()) if nh and "eoh_m" in ctx.collar_u else 0
    kpi = "".join(f'<div class="kpi {k[0].lower()}"><span>{t(k.lower(), lang)}</span><b>{counts.get(k, 0):,}</b></div>' for k in ("CRITICAL", "ERROR", "WARNING", "INFO"))
    kpi += "".join(f'<div class="kpi g"><span>{lab}</span><b>{val}</b></div>' for lab, val in
                   ((t("holes", lang), f"{nh:,}"), (t("metres", lang), f"{metres:,.0f}"), (t("samples", lang), f"{n_orig:,}"), (t("rules_run", lang), f"{n_run}")))
    hero = f"""<header class="hero"><div class="in"><div class="brand"><i></i>GEOVALID PRO</div><h1>{t('title', lang)}</h1>
<div class="chips"><span class="chip">{t('project', lang)}: <b>{esc(res.spec.project_name)}</b></span>
<span class="chip">{t('date', lang)}: <b class="ltr">{esc(res.started.replace('T', ' '))}</b></span>
<span class="chip">{t('software', lang)}: <b class="ltr">GEOVALID PRO {__version__}</b></span><span class="chip">run <b class="ltr">{esc(res.run_id[:8])}</b></span></div>
<div class="kpis">{kpi}</div></div></header>"""
    # 1 executive
    find = "".join(f"<li>{esc(s)}</li>" for s in _narrative(res, lang, counts, inv))
    top = sm["by_rule"].head(10).reset_index() if not sm["by_rule"].empty else pd.DataFrame()
    title_col = "title_fa" if fa else "title_en"
    c1 = f"<h3>{t('top', lang)}</h3><ul class='find'>{find}</ul>"
    c1 += f"<div class='grid2'>{fig(charts.severity_donut(iss, lang), 'توزیع مسائل بر پایهٔ شدت' if fa else 'Issues by severity')}" \
          f"{fig(charts.family_bar(iss, lang), 'مسائل بر پایهٔ خانوادهٔ قاعده و شدت' if fa else 'Issues by rule family and severity')}</div>"
    if not top.empty:
        c1 += table(top, ["rule_id", title_col, "CRITICAL", "ERROR", "WARNING", "INFO", "total"],
                    [t("rule", lang), t("title_col", lang), "C", "E", "W", "I", t("total", lang)])
    c1 += f"<div class='note'>{esc(t('v01', lang).format(run=n_run, ver=__version__))}</div>"
    sec("exec", c1, 1)
    # 2 inventory
    files = pd.DataFrame([{"file": Path(i.raw.source).name, "sheet": i.raw.sheet or "", "kind": i.kind, "sha256": i.raw.sha256[:16] + "…"}
                          for i in res.spec.inputs])
    sec("inventory", table(inv, ["table", "kind", "source", "rows", "holes", "metres", "analytes"],
                           [t("table", lang), t("kind", lang), t("file", lang), t("rows", lang), t("holes", lang), t("metres", lang), t("analytes", lang)])
        + f"<details><summary>{t('inputs', lang)}</summary>{table(files)}</details>", 2)
    num = 3
    # collars
    if ctx.has("collar"):
        c = [fig(charts.collar_map(ctx, worst, lang), "موقعیت دهانه‌ها بر پایهٔ شدیدترین مسئله و مسیر گمانه‌ها" if fa else "Collars coloured by worst issue, with desurveyed traces", wide=True)]
        nn = ctx.stats.get("nn")
        ce = ctx.stats.get("clark_evans", {})
        g = []
        if nn is not None:
            g.append(fig(charts.hist(nn["nn1_m"], "فاصلهٔ نزدیک‌ترین همسایه" if fa else "Nearest-neighbour distance", "متر" if fa else "Distance (m)", lang=lang),
                         "توزیع فاصلهٔ نزدیک‌ترین همسایه" if fa else "Nearest-neighbour distance distribution"))
        cm = ctx.stats.get("collar_method")
        if cm is not None:
            g.append(fig(charts.method_bar(cm, lang), "روش استنتاجی برداشت مختصات دهانه (نسخهٔ پیش‌نمایش)" if fa else "Inferred collar survey method (preview)"))
        c.append(f"<div class='grid2'>{''.join(g)}</div>")
        if ce.get("R"):
            c.append(table(pd.DataFrame([{"n": ce["n"], "Clark–Evans R": round(ce["R"], 3), "mean NN (m)": round(ce["mean_nn"], 1),
                                          "expected NN (m)": round(ce["expected_nn"], 1), "holes / km²": round(ce["density_per_km2"], 2)}])))
        if "dz" in ctx.stats:
            d = ctx.stats["dz"]
            g2 = [fig(charts.hist(d, "اختلاف ارتفاع دهانه و توپوگرافی" if fa else "ΔZ collar − topography", "ΔZ (m)", vline=[-2, 2, -5, 5], lang=lang),
                      "توزیع اختلاف ارتفاع دهانه و توپوگرافی (خطوط: ±۲ و ±۵ متر)" if fa else "ΔZ distribution (lines: ±2 and ±5 m)"),
                  fig(charts.dz_map(ctx, lang), "نقشهٔ ΔZ" if fa else "ΔZ map")]
            c.append(f"<div class='grid2'>{''.join(g2)}</div>")
        if cm is not None:
            c.append(f"<details><summary>{'شواهد روش برداشت مختصات' if fa else 'Collar method evidence'} ({len(cm)})</summary>"
                     f"{table(cm, ['hole_id', 'inferred_method', 'confidence_pct', 'declared_method', 'evidence'], max_rows=1000)}</details>")
        sec("collar", "".join(c), num)
        num += 1
    # survey
    if ctx.has("traces"):
        dls = pd.concat([tr["dogleg_deg"] * 30 / tr["depth_m"].diff() for tr in ctx.traces.values()])
        c = fig(charts.hist(dls[np.isfinite(dls)], "شدت خمیدگی در هر بخش" if fa else "Dogleg severity per segment", "°/30 m", vline=[3, 6], lang=lang),
                "توزیع شدت خمیدگی (خطوط: آستانهٔ هشدار ۳ و خطای ۶ درجه بر ۳۰ متر)" if fa else "Dogleg severity (lines: warning 3 and error 6 °/30 m)")
        c += f"<p>{'قرارداد شیب' if fa else 'Dip convention'}: <span class='ltr'>{esc(ctx.dip_convention)}</span></p>"
        sec("survey", c, num)
        num += 1
    # intervals
    if ctx.interval_tables:
        c = []
        if not sm["by_table"].empty:
            c.append(table(sm["by_table"].reset_index(), None, [t("table", lang), "C", "E", "W", "I"]))
        g = []
        for tb in ctx.by_kind("assay")[:2]:
            L = (tb.df["to_m"] - tb.df["from_m"])
            g.append(fig(charts.hist(L[(L > 0) & (L < 20)], ("طول نمونه – " if fa else "Sample length – ") + tb.name, "متر" if fa else "Length (m)", lang=lang),
                         ("توزیع طول نمونه‌ها: " if fa else "Sample length distribution: ") + tb.name))
        c.append(f"<div class='grid2'>{''.join(g)}</div>")
        for name, (n, tot) in ctx.stats.get("contact_crossing", {}).items():
            c.append(f"<p>{name}: {n} / {tot} {'نمونه از همبری سنگ‌شناسی عبور می‌کنند' if fa else 'samples cross a lithology contact'} ({100 * n / max(tot, 1):.1f}%).</p>")
        sec("intervals", "".join(c), num)
        num += 1
    # assays
    if ast is not None and not ast.empty:
        c = [f"<h3>{t('stats', lang)}</h3>",
             table(ast, ["table", "column", "unit", "unit_source", "n", "pct_bdl", "min", "median", "mean", "mean_lw", "p95", "max", "cv"],
                   ["table", "column", "unit", "unit src", "n", "% BDL", "min", "P50", "mean", "mean (LW)", "P95", "max", "CV"])]
        keys = ctx.params.get("key_analytes", [])
        series, frame, units = {}, {}, {}
        for tb in ctx.tables:
            orig = ~tb.df["qc_class"].isin(QC_TYPES) if "qc_class" in tb.df else pd.Series(True, index=tb.df.index)
            for a in tb.analytes:
                if not a.partial:
                    v = a.parsed["value_policy"].where(orig)
                    frame.setdefault(a.analyte, v)
                    units.setdefault(a.analyte, a.unit)
                    if a.analyte in keys and len(series) < 6:
                        series.setdefault(a.analyte, v)
        c.append(fig(charts.logprob(series, units, lang), "نمودار احتمال لگاریتمی عناصر کلیدی" if fa else "Log-probability plots of key analytes", wide=True))
        fr = pd.DataFrame(frame)
        if fr.shape[1] > 15:
            fr = fr[fr.count().sort_values(ascending=False).index[:15]]
        g = [fig(charts.corr_heatmap(fr, lang), "همبستگی اسپیرمن بین عناصر (لگاریتمی)" if fa else "Spearman correlation between analytes (log values)")]
        cat = ctx.stats.get("categorical", {})
        if cat.get("fields") and isinstance(cat.get("association"), pd.DataFrame):
            from ..analysis import categorical as C
            pr = C.primary_analytes(cat["association"], cat["units"], ctx.params, 2)
            lg = [f for f, v in cat["fields"].items() if v[2] == "logging"]
            if len(pr) == 2:
                g.append(fig(charts.scatter_pair(cat["samples"], pr[0], pr[1], lg[0] if lg else None, cat["units"], lang),
                             f"{pr[1]} در برابر {pr[0]} به تفکیک واحد" if fa else f"{pr[1]} against {pr[0]} by unit"))
        c.append(f"<div class='grid2'>{''.join(g)}</div>")
        sec("assay", "".join(c), num)
        num += 1
    # grade vs geology
    geo = _geology_section(res, lang, num)
    if geo:
        sections.append((num, t("geology", lang)))
        body.append(geo)
        num += 1
    # qaqc
    if ctx.has("assay"):
        c = []
        rates = ctx.stats.get("qaqc_rates", {})
        if rates:
            rows = [{"table": k, "originals": n, **{kk: round(v, 2) for kk, v in r.items()}} for k, (n, r) in rates.items()]
            c.append(table(pd.DataFrame(rows)))
        else:
            c.append(f"<div class='note'>{'دادهٔ کنترل کیفیت شناسایی نشد (QAQ-001: بحرانی).' if fa else 'No QA/QC data identified (QAQ-001: CRITICAL).'}</div>")
        for name, s in ctx.stats.get("crm_results", {}).items():
            c.append(fig(charts.crm_chart(s, lang), "نمودار کنترل مواد مرجع" if fa else "CRM control chart", wide=True))
        g = []
        for name, items in ctx.stats.get("blank_results", {}).items():
            g.append(fig(charts.blank_chart(items, lang), "نتایج بلانک‌ها" if fa else "Blank results"))
        pairs = ctx.stats.get("dup_pairs", {})
        keys = [k for k in ctx.params.get("key_analytes", []) if any(p[2] == k for p in pairs)][:2]
        g.append(fig(charts.hard_chart(pairs, lang, analytes=keys or None),
                     "نمودار رتبه‌ای HARD نمونه‌های تکراری" if fa else "Ranked HARD plot"))
        c.append(f"<div class='grid2'>{''.join(g)}</div>")
        sec("qaqc", "".join(c), num)
        num += 1
    # logging
    inv_l = ctx.stats.get("lith_inventory", {})
    if inv_l or ctx.by_kind("geotech") or ctx.by_kind("density"):
        c = []
        for name, df in inv_l.items():
            c.append(f"<h3>{esc(name)}</h3>" + table(df.reset_index().rename(columns={"index": "code", "lith_code": "code"}).round(1), max_rows=60))
        for name, (an, rec, val) in ctx.stats.get("recovery_grade", {}).items():
            c.append(fig(charts.recovery_grade(rec, val, an, lang), "بازیافت مغزه در برابر عیار" if fa else "Core recovery vs grade"))
        sec("logging", "".join(c), num)
        num += 1
    # rules
    c = ""
    if not sm["by_rule"].empty:
        c += table(sm["by_rule"].reset_index(), ["rule_id", title_col, "CRITICAL", "ERROR", "WARNING", "INFO", "total"],
                   [t("rule", lang), t("title_col", lang), "C", "E", "W", "I", t("total", lang)])
    c += (f"<details><summary>{t('matrix', lang)} ({len(res.matrix)})</summary>"
          f"{table(res.matrix, ['rule_id', title_col, 'status', 'n_issues', 'note'], [t('rule', lang), t('title_col', lang), t('status', lang), 'n', t('note', lang)])}</details>")
    sec("rules", c, num)
    num += 1
    # issues
    msg = "message_fa" if fa else "message_en"
    c = f"<input class='q' placeholder='{t('search', lang)}' oninput='gvFilter(this)'>"
    c += table(iss, ["issue_id", "severity", "rule_id", "table", "hole_id", "from_m", "to_m", "src_row", msg, "suggested_fix"],
               ["#", t("severity", lang), t("rule", lang), t("table", lang), t("hole", lang), t("from", lang), t("to", lang),
                t("row", lang), t("message", lang), t("fix", lang)], max_rows=3000, cls="issues").replace("<table", "<table id='issues'", 1)
    if len(iss) > 3000:
        c += f"<p>{'فهرست کامل در فایل issue_log.xlsx است.' if fa else 'The full list is in issue_log.xlsx.'}</p>"
    sec("issues", c, num)
    num += 1
    # appendix
    c = f"<div class='note'>{esc(t('disclaimer', lang))}</div>"
    if res.errors:
        c += "<h3>Run messages</h3><pre class='ltr'>" + esc("\n".join(res.errors[:40])) + "</pre>"
    prm = pd.DataFrame([{"rule": k, "parameters": ", ".join(f"{a}={b}" for a, b in v.items())}
                        for k, v in ctx.params.get("rules", {}).items()])
    c += f"<details><summary>{'پارامترهای به‌کاررفته' if fa else 'Parameters used'}</summary>{table(prm)}</details>"
    sec("appendix", c, num)
    toc = "".join(f"<a href='#s{n}'><span>{n}</span>{esc(ti)}</a>" for n, ti in sorted(sections))
    css = CSS.replace("__FONT__", _font_b64())
    foot = f"<footer>GEOVALID PRO {__version__} · {esc(res.run_id)} · {'تهیه‌شده به‌صورت خودکار؛ نیازمند بازبینی شخص صلاحیت‌دار' if fa else 'Generated automatically; requires review by a Competent Person'}</footer>"
    return (f"<!doctype html><html lang='{lang}' dir='{'rtl' if fa else 'ltr'}'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>GEOVALID PRO – {esc(res.spec.project_name)}</title>"
            f"<style>{css}</style><script>{JS}</script></head><body>{hero}<div class='layout'><nav class='toc'><h4>{t('contents', lang)}</h4>{toc}</nav>"
            f"<main>{''.join(body)}</main></div>{foot}</body></html>")
