# -*- coding: utf-8 -*-
"""Write a document.Document as one self-contained, print-ready HTML file:
right-to-left, Vazirmatn embedded, vector charts inline, A4 page rules with
running header and Persian page numbers. Edge or Chrome turns it into the
PDF (pdf.py); any browser shows it."""

from __future__ import annotations

import base64
import html
import os
import re
import sys

from .. import APP_NAME, APP_VER
from ..core import fa_digits, fa_num, jalali_str
from ..render import to_svg
from . import texts_fa as T
from .document import (Bullets, Callout, Cell, Cover, DocControl, FigureBlock,
                       FindingCard, Heading, PageBreak, Para, Signature, Table, TOC,
                       VerdictGrid, split_runs)


def asset_path(name):
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = os.path.join(base, "geoqaqc", "assets", name)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", name)


def _font_face():
    try:
        with open(asset_path("Vazirmatn.woff2"), "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        src = f"url(data:font/woff2;base64,{b64}) format('woff2')"
    except OSError:
        src = "local('Vazirmatn')"
    return ("@font-face{font-family:'Vazirmatn';font-weight:100 900;"
            f"font-style:normal;font-display:block;src:{src};}}")


def t(text):
    """Escaped inline text; Latin runs isolated, **bold** honoured."""
    out = []
    for seg, latin, bold in split_runs(text):
        s = html.escape(seg, quote=False)
        if latin:
            s = f'<span class="lat" dir="ltr">{s}</span>'
        if bold:
            s = f"<strong>{s}</strong>"
        out.append(s)
    return "".join(out)


def _css_str(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


CSS = """
:root{--ink:#16202b;--ink2:#4b5563;--muted:#8a94a3;--line:#e3e7ed;--zebra:#f7f9fb;
--navy:#0f2742;--navy2:#1d3d63;--gold:#c8902f;--gold2:#e7c27d;
--ok:#0b8a0b;--okbg:#e5f4e5;--warn:#9a6a00;--warnbg:#fff3d1;--mat:#b5532c;--matbg:#fde7dd;
--crit:#b42424;--critbg:#fbe1e1;--info:#1d5fa8;--infobg:#e6f0fa;--mutedbg:#eef0f3}
*{box-sizing:border-box}
html{background:#e9ecef}
body{font-family:'Vazirmatn',Tahoma,'Segoe UI',sans-serif;color:var(--ink);font-size:10pt;
line-height:1.95;margin:0;text-align:justify;-webkit-print-color-adjust:exact;
print-color-adjust:exact}
.lat{unicode-bidi:isolate;font-family:'Segoe UI','Inter','Vazirmatn',sans-serif}
.page{background:#fff;width:210mm;margin:12mm auto;padding:18mm 16mm 20mm;
box-shadow:0 2px 18px rgba(0,0,0,.12)}
@page{size:A4;margin:20mm 16mm 18mm 16mm;
 @top-right{content:var(--hdr-r);font:8pt 'Vazirmatn';color:#8a94a3}
 @top-left{content:var(--hdr-l);font:8pt 'Vazirmatn';color:#8a94a3}
 @bottom-center{content:"صفحهٔ " counter(page,persian);font:8pt 'Vazirmatn';color:#8a94a3}}
@page cover{margin:0;@top-right{content:none}@top-left{content:none}@bottom-center{content:none}}
@media print{html{background:#fff}.page{width:auto;margin:0;padding:0;box-shadow:none}
.cover{page:cover}}
h1{font-size:17pt;color:var(--navy);margin:18pt 0 10pt;padding:4pt 0 8pt;
border-bottom:1.6pt solid var(--gold);break-after:avoid;line-height:1.5}
h1.newpage{break-before:page;margin-top:0}
h1 .num{display:inline-block;min-width:24pt;height:24pt;line-height:24pt;margin-left:9pt;
border-radius:6pt;background:var(--navy);color:#fff;text-align:center;font-size:12pt}
h2{font-size:12.5pt;color:var(--navy2);margin:16pt 0 6pt;break-after:avoid}
h2 .num{color:var(--gold);margin-left:6pt;font-weight:700}
h3{font-size:10.5pt;color:var(--ink);margin:12pt 0 3pt;break-after:avoid}
p{margin:0 0 7pt}
p.lead{font-size:11pt;color:var(--ink)}
p.note{font-size:8.6pt;color:var(--ink2)}
ul,ol{margin:2pt 0 8pt;padding-right:18pt}
li{margin:1.5pt 0}
.cover{height:297mm;position:relative;padding:0;overflow:hidden;break-after:page;
display:flex;flex-direction:column}
.cover .band{background:linear-gradient(160deg,var(--navy) 0%,#163a63 70%,#1d4a7a 100%);
color:#fff;padding:26mm 20mm 18mm;flex:0 0 auto;position:relative}
.cover .band:after{content:"";position:absolute;right:0;left:0;bottom:-3pt;height:3pt;
background:linear-gradient(90deg,var(--gold2),var(--gold))}
.cover .logo{position:absolute;top:14mm;left:20mm;max-height:22mm;max-width:50mm}
.cover .brand{font-size:8.5pt;letter-spacing:.5pt;color:var(--gold2);margin-bottom:22mm}
.cover .kicker{font-size:11pt;color:var(--gold2);margin-bottom:4pt}
.cover .title{font-size:25pt;font-weight:800;line-height:1.5;margin:0 0 6pt}
.cover .subtitle{font-size:11.5pt;color:#c9d6e6;margin:0}
.cover .body{padding:14mm 20mm 0;flex:1 1 auto}
.metagrid{display:grid;grid-template-columns:1fr 1fr;gap:6pt 18pt;margin-bottom:12mm}
.metagrid div{border-bottom:.6pt solid var(--line);padding:3pt 0}
.metagrid b{display:block;font-size:7.8pt;color:var(--muted);font-weight:500}
.metagrid span.v{font-size:10.5pt;font-weight:600}
.scoreline{display:flex;gap:14pt;align-items:stretch;margin-bottom:9mm}
.badge{border-radius:10pt;padding:9pt 14pt;color:#fff;min-width:55mm}
.badge b{display:block;font-size:8pt;font-weight:500;opacity:.85}
.badge span{font-size:17pt;font-weight:800}
.badge span.st{display:block;font-size:13pt;line-height:1.6;margin:2pt 0 3pt}
.stats{display:flex;gap:8pt;flex:1}
.stat{flex:1;border:.6pt solid var(--line);border-radius:9pt;padding:7pt 10pt;text-align:center}
.stat span{display:block;font-size:15pt;font-weight:800;color:var(--navy)}
.stat b{font-size:8pt;color:var(--muted);font-weight:500}
.chips{display:flex;flex-wrap:wrap;gap:6pt}
.vchip{border-radius:20pt;padding:3pt 11pt;font-size:9pt;font-weight:600}
.cover .foot{padding:0 20mm 12mm;font-size:8pt;color:var(--muted);display:flex;
justify-content:space-between}
.tone-ok{background:var(--okbg);color:var(--ok)}
.tone-warn{background:var(--warnbg);color:var(--warn)}
.tone-minor{background:var(--warnbg);color:var(--warn)}
.tone-material{background:var(--matbg);color:var(--mat)}
.tone-critical{background:var(--critbg);color:var(--crit)}
.tone-fail{background:var(--critbg);color:var(--crit)}
.tone-muted{background:var(--mutedbg);color:var(--ink2)}
.bg-ok{background:var(--ok)}.bg-warn{background:#c98b00}.bg-material{background:var(--mat)}
.bg-critical{background:var(--crit)}.bg-muted{background:#6b7280}
table{width:100%;border-collapse:collapse;margin:4pt 0 3pt;font-size:8.8pt;line-height:1.6;
break-inside:auto}
thead{display:table-header-group}
tr{break-inside:avoid}
th{background:#eef2f7;color:var(--navy2);font-weight:700;text-align:right;
padding:4pt 6pt;border-bottom:1pt solid #cfd7e2}
td{padding:3.2pt 6pt;border-bottom:.5pt solid var(--line);vertical-align:top;text-align:right}
tbody tr:nth-child(even) td{background:var(--zebra)}
td.ltr{direction:ltr;text-align:left;font-family:'Segoe UI','Inter',sans-serif;font-size:8.2pt}
table.compact{font-size:7.9pt}table.compact td{padding:2.2pt 5pt}
td .tone{display:inline-block;border-radius:10pt;padding:0 8pt;font-weight:600;font-size:8pt}
.cap{font-size:8.2pt;color:var(--ink2);margin:0 0 11pt}
.cap b{color:var(--navy2)}
figure{margin:8pt 0 12pt;break-inside:avoid}
figure svg{width:100%;height:auto;display:block;border:.6pt solid var(--line);border-radius:6pt}
figcaption{font-size:8.2pt;color:var(--ink2);margin-top:4pt}
figcaption b{color:var(--navy2)}
.callout{border-right:3.5pt solid;border-radius:6pt;padding:7pt 11pt;margin:8pt 0 11pt;
break-inside:avoid}
.callout .ct{font-weight:800;margin-bottom:2pt}
.callout.info{border-color:var(--info);background:var(--infobg)}
.callout.ok{border-color:var(--ok);background:var(--okbg)}
.callout.warn{border-color:#c98b00;background:var(--warnbg)}
.callout.critical{border-color:var(--crit);background:var(--critbg)}
.card{border:.7pt solid var(--line);border-radius:9pt;margin:8pt 0 10pt;break-inside:avoid;
overflow:hidden}
.card .hd{display:flex;gap:6pt;align-items:center;padding:6pt 10pt;background:#f7f9fb;
border-bottom:.6pt solid var(--line);flex-wrap:wrap}
.card .hd .ttl{font-weight:800;font-size:10pt;flex:1 1 100%;color:var(--ink)}
.pill{border-radius:20pt;padding:0 9pt;font-size:7.8pt;font-weight:700;color:#fff}
.tag{border-radius:20pt;padding:0 9pt;font-size:7.8pt;background:#e8edf4;color:var(--navy2)}
.card .bd{padding:6pt 11pt 4pt}
.card .lbl{font-weight:700;color:var(--navy2)}
.card ol{margin-top:0}
.vgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(38mm,1fr));gap:7pt;
margin:6pt 0 12pt}
.vcard{border:.7pt solid var(--line);border-radius:10pt;padding:8pt 10pt;break-inside:avoid;
text-align:start}
.vcard .nm{font-size:13pt;font-weight:800;color:var(--navy)}
.vcard .cd{font-size:7.8pt;color:var(--muted)}
.vcard .vc{display:block;border-radius:6pt;padding:2pt 7pt;margin:5pt 0;font-weight:700;
font-size:8.4pt}
.vcard .ct{font-size:7.8pt;color:var(--ink2)}
.toc{columns:1;margin:0;padding:0;list-style:none}
.toc li{margin:2pt 0}.toc a{color:var(--ink);text-decoration:none}
.toc .l1{font-weight:700;margin-top:6pt}.toc .l2{padding-right:16pt;color:var(--ink2);
font-size:9pt}
.toc .n{display:inline-block;min-width:22pt;color:var(--gold);font-weight:800}
.sig{display:grid;grid-template-columns:repeat(3,1fr);gap:10pt;margin-top:16pt;
break-inside:avoid}
.sig div{border:.7pt solid var(--line);border-radius:8pt;padding:8pt 10pt;min-height:30mm}
.sig b{display:block;color:var(--navy2);font-size:8.5pt}
.sig span{display:block;font-size:9.5pt;margin-top:2pt}
.sig .line{margin-top:14mm;border-top:.6pt dashed var(--muted);font-size:7.5pt;
color:var(--muted);padding-top:2pt}
.doccontrol{margin-top:4pt}
"""

_TONE_BG = {"CRITICAL": "critical", "MATERIAL": "material", "MINOR": "warn"}
_VERDICT_TONE = {"SUITABLE": "ok", "RESTRICTED": "warn", "REMEDIATE": "critical"}
_RATING_BG = {"EXCELLENT": "ok", "VERY GOOD": "ok", "GOOD": "ok", "POOR": "warn",
              "BAD": "material", "VERY BAD": "critical", "NO DATA": "muted"}


class _W:
    def __init__(self, doc):
        self.doc = doc
        self.out = []
        self.h1 = 0
        self.headings = []      # (level, number, text, id)
        self._ids()

    def _ids(self):
        n1 = n2 = 0
        for b in self.doc.blocks:
            if isinstance(b, Heading) and b.level in (1, 2):
                if b.level == 1:
                    n1 += 1
                    n2 = 0
                    b.anchor = b.anchor or f"s{n1}"
                else:
                    n2 += 1
                    b.anchor = b.anchor or f"s{n1}-{n2}"
                self.headings.append((b.level, b.number, b.text, b.anchor))

    def w(self, s):
        self.out.append(s)


def _cell(c):
    if isinstance(c, Cell):
        cls = ' class="ltr" dir="ltr"' if c.ltr else ""
        body = html.escape(c.text) if c.ltr else t(c.text)
        if c.tone:
            body = f'<span class="tone tone-{c.tone}">{body}</span>'
        return f"<td{cls}>{body}</td>"
    return f"<td>{t(c)}</td>"


def _svg(fig):
    s = to_svg(fig, "light")
    # drop the fixed size: the chart scales to the column width
    s = re.sub(r'(<svg[^>]*?)\s(width|height)="[^"]*"', r"\1", s, count=1)
    s = re.sub(r'(<svg[^>]*?)\s(width|height)="[^"]*"', r"\1", s, count=1)
    return s


def _logo(path):
    if not path or not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "svg": "svg+xml",
            "gif": "gif"}.get(ext)
    if not mime:
        return ""
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f'<img class="logo" src="data:image/{mime};base64,{b64}" alt="">'


def _cover(w, b):
    m = b.meta
    d = m.the_date()
    # the cover leads with the WORST verdict: a weighted average of ratings can
    # read "very good" while one element is unusable, which would mislead
    order = ["REMEDIATE", "RESTRICTED", "SUITABLE"]
    worst = min((c for _, _, c in b.verdicts), key=order.index, default="SUITABLE")
    tone = _VERDICT_TONE[worst]
    n_worst = sum(1 for _, _, c in b.verdicts if c == worst)
    status = (T.VERDICT_FA[worst] if worst == "SUITABLE"
              else f"{T.VERDICT_FA[worst]} برای {fa_num(n_worst, 0)} عنصر")
    rows = [("کارفرما", m.client), ("مشاور", m.consultant), ("شمارهٔ گزارش", m.report_no),
            ("ویرایش", fa_digits(m.revision)), ("تاریخ", f"{jalali_str(d)} — {d.isoformat()}"),
            ("محل", m.location)]
    grid = "".join(f"<div><b>{t(k)}</b><span class=\"v\">{t(v)}</span></div>"
                   for k, v in rows if v)
    chips = "".join(
        f'<span class="vchip tone-{_VERDICT_TONE[c]}">{t(name)}: {t(T.VERDICT_FA[c])}</span>'
        for el, name, c in b.verdicts)
    stats = "".join(f'<div class="stat"><span>{t(v)}</span><b>{t(k)}</b></div>'
                    for k, v in b.stats)
    avg = T.RATING_FA.get(b.rating, b.rating) + (
        f" ({fa_num(b.score, 0)} از ۱۰۰)" if b.score is not None else "")
    w.w(f"""<section class="page cover"><div class="band">{_logo(m.logo_path)}
<div class="brand"><span class="lat" dir="ltr">{APP_NAME} {APP_VER}</span></div>
<div class="kicker">{t(m.project or "")}</div>
<div class="title">{t(T.REPORT_TITLE)}</div>
<p class="subtitle">{t(T.REPORT_SUBTITLE)}</p></div>
<div class="body"><div class="metagrid">{grid}</div>
<div class="scoreline"><div class="badge bg-{tone}"><b>وضعیت کلی</b>
<span class="st">{t(status)}</span><b>میانگین وزنی رتبه‌ها: {t(avg)}</b></div>
<div class="stats">{stats}</div></div>
<h3>حکم کفایت داده به تفکیک عنصر</h3><div class="chips">{chips}</div></div>
<div class="foot"><span>{t(m.author)}{(' — ' + t(m.author_title)) if m.author else ''}</span>
<span>تهیه‌شده با نرم‌افزار <span class="lat" dir="ltr">{APP_NAME} {APP_VER}</span></span></div>
</section><section class="page">""")


def _doccontrol(w, b):
    m = b.meta
    d = m.the_date()
    rows = [("عنوان", T.REPORT_TITLE), ("پروژه", m.project), ("شمارهٔ گزارش", m.report_no),
            ("ویرایش", fa_digits(m.revision)), ("تاریخ", jalali_str(d))]
    body = "".join(f"<tr><th>{t(k)}</th><td>{t(v or '—')}</td></tr>" for k, v in rows)
    people = [("تهیه‌کننده", m.author, m.author_title), ("بازبین", m.reviewer, ""),
              ("تأییدکننده", m.approver, "")]
    pb = "".join(f"<tr><td>{t(r)}</td><td>{t(n or '—')}</td><td>{t(ti or '')}</td>"
                 f"<td></td></tr>" for r, n, ti in people)
    w.w(f"""<h2 style="margin-top:0">{t(T.H['control'])}</h2>
<table class="doccontrol"><tbody>{body}</tbody></table>
<table><thead><tr><th>نقش</th><th>نام</th><th>سمت</th><th>امضا</th></tr></thead>
<tbody>{pb}</tbody></table>""")


def _toc(w):
    items = []
    for level, num, text, anchor in w.headings:
        n = f'<span class="n">{t(num)}</span>' if num else ""
        items.append(f'<li class="l{level}"><a href="#{anchor}">{n}{t(text)}</a></li>')
    w.w(f'<h2>{t(T.H["toc"])}</h2><ul class="toc">{"".join(items)}</ul>')


def _card(f):
    sev_bg = {"CRITICAL": "critical", "MATERIAL": "material", "MINOR": "warn"}[f.severity]
    acts = "".join(f"<li>{t(a)}</li>" for a in f.actions_fa)
    return (f'<div class="card"><div class="hd"><span class="ttl">{t(f.title_fa)}</span>'
            f'<span class="pill bg-{sev_bg}">{t(T.SEVERITY_FA[f.severity])}</span>'
            f'<span class="tag">{t(T.STAGE_FA[f.stage])}</span>'
            f'<span class="tag">مسئول: {t(T.OWNER_FA.get(f.owner, f.owner))}</span>'
            f'<span class="tag">{t(T.TIMING_FA.get(f.timing, f.timing))}</span></div>'
            f'<div class="bd"><p><span class="lbl">شواهد: </span>{t(f.evidence_fa)}</p>'
            f'<p><span class="lbl">علت محتمل: </span>{t(f.cause_fa)}</p>'
            f'<p class="lbl" style="margin:0">راهکار:</p><ol>{acts}</ol></div></div>')


def _vgrid(items):
    cards = []
    for name, el, code, counts in items:
        c = (f"بحرانی {fa_num(counts['CRITICAL'], 0)} · مهم {fa_num(counts['MATERIAL'], 0)}"
             f" · جزئی {fa_num(counts['MINOR'], 0)}")
        cards.append(f'<div class="vcard"><div class="nm">{t(name)}</div>'
                     f'<div class="cd"><span class="lat" dir="ltr">{html.escape(el)}</span></div>'
                     f'<span class="vc tone-{_VERDICT_TONE[code]}">{t(T.VERDICT_FA[code])}</span>'
                     f'<div class="ct">{t(c)}</div></div>')
    return f'<div class="vgrid">{"".join(cards)}</div>'


def _signature(m):
    people = [("تهیه‌کننده", m.author, m.author_title), ("بازبین", m.reviewer, ""),
              ("تأییدکننده", m.approver, "")]
    boxes = "".join(f'<div><b>{t(r)}</b><span>{t(n or "")}</span>'
                    f'<span style="color:#8a94a3;font-size:8pt">{t(ti or "")}</span>'
                    f'<div class="line">امضا و تاریخ</div></div>' for r, n, ti in people)
    return f'<div class="sig">{boxes}</div>'


def render_body(doc):
    w = _W(doc)
    for b in doc.blocks:
        if isinstance(b, Cover):
            _cover(w, b)
        elif isinstance(b, DocControl):
            _doccontrol(w, b)
        elif isinstance(b, TOC):
            _toc(w)
        elif isinstance(b, Heading):
            num = f'<span class="num">{t(b.number)}</span>' if b.number else ""
            lvl = min(max(b.level, 1), 3)
            a = b.anchor or ""
            cls = (' class="newpage"' if lvl == 1 and (a in ("summary", "actions")
                                                        or a.startswith(("el-", "app-")))
                   else "")
            w.w(f'<h{lvl} id="{html.escape(a)}"{cls}>{num}{t(b.text)}</h{lvl}>')
        elif isinstance(b, Para):
            w.w(f'<p class="{b.style}">{t(b.text)}</p>')
        elif isinstance(b, Bullets):
            tag = "ol" if b.ordered else "ul"
            w.w(f"<{tag}>" + "".join(f"<li>{t(i)}</li>" for i in b.items) + f"</{tag}>")
        elif isinstance(b, Table):
            cols = ""
            if b.widths:
                tot = float(sum(b.widths))
                cols = "<colgroup>" + "".join(f'<col style="width:{100 * x / tot:.1f}%">'
                                              for x in b.widths) + "</colgroup>"
            head = "".join(f"<th>{t(h)}</th>" for h in b.header)
            body = "".join("<tr>" + "".join(_cell(c) for c in r) + "</tr>" for r in b.rows)
            cls = ' class="compact"' if b.compact else ""
            w.w(f"<table{cls}>{cols}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            if b.caption:
                w.w(f'<p class="cap"><b>جدول {t(b.number)}.</b> {t(b.caption)}</p>')
        elif isinstance(b, FigureBlock):
            w.w(f"<figure>{_svg(b.fig)}<figcaption><b>شکل {t(b.number)}.</b> "
                f"{t(b.caption)}</figcaption></figure>")
        elif isinstance(b, Callout):
            w.w(f'<div class="callout {b.kind}"><div class="ct">{t(b.title)}</div>'
                f"<div>{t(b.text)}</div></div>")
        elif isinstance(b, FindingCard):
            w.w(_card(b.finding))
        elif isinstance(b, VerdictGrid):
            w.w(_vgrid(b.items))
        elif isinstance(b, Signature):
            w.w(_signature(b.meta))
        elif isinstance(b, PageBreak):
            w.w('<div style="break-after:page"></div>')
    return "\n".join(w.out)


def write_html(doc, path):
    m = doc.meta
    hdr_r = f"{m.project} · {T.REPORT_TITLE}" if m.project else T.REPORT_TITLE
    hdr_l = m.report_no or ""
    body = render_body(doc)
    title = html.escape(f"{m.project} — {T.REPORT_TITLE}" if m.project else T.REPORT_TITLE)
    page = f"""<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="generator" content="{APP_NAME} {APP_VER}">
<style>{_font_face()}
:root{{--hdr-r:{_css_str(hdr_r)};--hdr-l:{_css_str(hdr_l)}}}
{CSS}</style></head>
<body>
{body}
</section></body></html>"""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path
