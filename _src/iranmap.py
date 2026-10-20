# اطلس کانسارها: نقشهٔ ایران، صفحهٔ فهرست و صفحهٔ هر کانسار.
# مرز کشورها: Natural Earth (دامنهٔ عمومی) از بستهٔ world-atlas، ساده‌شده در data/iran_outline.json
import csv, io, json, math, os, html, re
from charts import S1, S2, SURF, GRID, AXIS, INK, INK2, MUTED, txt, num, nice_ticks, _dec, legend, figure
import deposit_notes

HERE = os.path.dirname(os.path.abspath(__file__))
OUTLINE = json.load(open(os.path.join(HERE, 'data', 'iran_outline.json')))
LON0, LON1, LAT0, LAT1 = 42.6, 64.6, 24.0, 40.6
COSL = math.cos(math.radians(32.3))
W = 640; K = W / ((LON1 - LON0) * COSL); H = round((LAT1 - LAT0) * K)
def P(lon, lat): return ((lon - LON0) * COSL * K, (LAT1 - lat) * K)
def esc(s): return html.escape(str(s), quote=True)
FA_D = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

COMM = {  # نماد شکل‌محور تا هویت فقط به رنگ وابسته نباشد
 'cu': {'fa': 'مس', 'en': 'Copper', 'shape': 'circle'},
 'fe': {'fa': 'آهن', 'en': 'Iron', 'shape': 'square'},
 'znpb': {'fa': 'سرب و روی', 'en': 'Lead–zinc', 'shape': 'triangle'},
 'au': {'fa': 'طلا', 'en': 'Gold', 'shape': 'diamond'},
}
def marker(shape, x, y, r=6, fill=S1, cls=''):
    st = f'fill="{fill}" stroke="{SURF}" stroke-width="2" class="mk {cls}"'
    if shape == 'circle': return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" {st}/>'
    if shape == 'square': return f'<rect x="{x - r + .5:.1f}" y="{y - r + .5:.1f}" width="{2 * r - 1}" height="{2 * r - 1}" rx="1.5" {st}/>'
    if shape == 'triangle': return f'<path d="M{x:.1f},{y - r - 1:.1f} L{x + r + 1:.1f},{y + r - .5:.1f} L{x - r - 1:.1f},{y + r - .5:.1f} Z" {st}/>'
    return f'<path d="M{x:.1f},{y - r - 1.5:.1f} L{x + r + 1.5:.1f},{y:.1f} L{x:.1f},{y + r + 1.5:.1f} L{x - r - 1.5:.1f},{y:.1f} Z" {st}/>'
def legend_key(shape, color=S1):
    return f'<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">{marker(shape, 8, 8, 5, color)}</svg>'

def _paths():
    out = []
    for code, rings in OUTLINE.items():
        d = ''.join('M' + ' L'.join(f'{P(lon, lat)[0]:.1f},{P(lon, lat)[1]:.1f}' for lon, lat in r) + 'Z' for r in rings)
        out.append((code, d))
    return out
PATHS = _paths()

SEAS = {'fa': [('دریای خزر', 51.2, 39.4), ('خلیج فارس', 51.6, 27.0), ('دریای عمان', 58.6, 24.55)],
        'en': [('Caspian Sea', 51.2, 39.4), ('Persian Gulf', 51.6, 27.0), ('Gulf of Oman', 58.6, 24.55)]}

def map_svg(lang, deps, base_path, highlight=None, labels=True, mini=False):
    """نقشه با نشانهٔ کانسارها؛ هر نشانه پیوند به صفحهٔ کانسار است و راهنمای هاور دارد."""
    fa = lang == 'fa'
    g = [f'<defs><clipPath id="mclip{"m" if mini else ""}"><rect width="{W}" height="{H}"/></clipPath></defs>',
         f'<rect width="{W}" height="{H}" fill="#0C1114"/>', f'<g clip-path="url(#mclip{"m" if mini else ""})">']
    for code, d in PATHS:
        if code != 'IRN': g.append(f'<path d="{d}" fill="#12181B" stroke="#1F282C" stroke-width=".8"/>')
    g.append(f'<path d="{dict(PATHS)["IRN"]}" fill="#18201F" stroke="#5E4632" stroke-width="1.2" stroke-linejoin="round"/>')
    g.append('</g>')
    if not mini:
        for name, lon, lat in SEAS[lang]:
            x, y = P(lon, lat); g.append(txt(x, y, name, lang, 'middle', 11, '#4F6066', ' font-style="italic"'))
    tx, ty = P(51.389, 35.689)
    g.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="3.2" fill="none" stroke="{INK2}" stroke-width="1.4"/>')
    g.append(txt(tx + 7, ty + 4, 'تهران' if fa else 'Tehran', lang, 'start', 11, INK2))
    placed = []
    marks = []
    for d in deps:
        if d.get('lat') is None: continue
        x, y = P(d['lon'], d['lat']); c = d[lang]; cm = COMM[d['commodity']]
        on = highlight is None or highlight == d['slug']
        fill = S1 if on else '#4A565B'
        tip = f'{c["name"]} · {cm[lang]} · {c["type_short"]}'
        href = f'{base_path}{d["slug"]}/'
        marks.append(f'<a href="{href}" class="dep" data-c="{d["commodity"]}" data-tip="{esc(tip)}" aria-label="{esc(tip)}">'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="transparent"/>{marker(cm["shape"], x, y, 7 if highlight == d["slug"] else 6, fill)}</a>')
        if labels and on:
            name = c['name']; w = len(name) * (6.2 if fa else 6.4) + 6
            for side in (1, -1):
                lx = x + side * 11; box = (lx if side > 0 else lx - w, y - 8, w, 14)
                if all(box[0] + box[2] < b[0] or b[0] + b[2] < box[0] or box[1] + box[3] < b[1] or b[1] + b[3] < box[1] for b in placed) and 4 < box[0] and box[0] + box[2] < W - 4:
                    placed.append(box)
                    marks.append(txt(lx, y + 4, name, lang, 'start' if side > 0 else 'end', 11.5, INK, f' class="dep-l" data-c="{d["commodity"]}" pointer-events="none"'))
                    break
    g += marks
    return f'<svg class="iran-map" viewBox="0 0 {W} {H}" role="img" aria-label="{"نقشهٔ موقعیت کانسارها در ایران" if fa else "Map of deposit locations in Iran"}" direction="ltr">{"".join(g)}</svg>'

def legend_html(lang, deps):
    used = [k for k in COMM if any(d['commodity'] == k for d in deps)]
    return '<div class="chart-legend map-legend">' + ''.join(f'<span>{legend_key(COMM[k]["shape"])}{COMM[k][lang]}</span>' for k in used) + '</div>'

def filters_html(lang, deps):
    used = [k for k in COMM if any(d['commodity'] == k for d in deps)]
    allb = 'همه' if lang == 'fa' else 'All'
    return ('<div class="map-filter" role="group" aria-label="filter"><button type="button" class="on" data-f="all">' + allb + '</button>'
            + ''.join(f'<button type="button" data-f="{k}">{legend_key(COMM[k]["shape"])}{COMM[k][lang]}</button>' for k in used) + '</div>')

def teaser(lang, deps, hub_path):
    fa = lang == 'fa'
    n = len(deps)
    return (f'<section id="atlas" class="atlas-teaser"><div class="wrap"><div class="grid2 at-grid">'
            f'<div class="rv"><div class="eyebrow" data-n="0">{"اطلس" if fa else "Atlas"}</div>'
            f'<h2>{"اطلس کانسارهای ایران" if fa else "Atlas of Iranian ore deposits"}</h2>'
            f'<p class="lede">{(f"زمین‌شناسی، تیپ و موقعیت {str(n).translate(FA_D)} کانسار مهم مس، آهن، سرب و روی و طلای ایران؛ با منابع علمی و نکات کارشناسی دربارهٔ اکتشاف و تخمین ذخیرهٔ هرکدام.") if fa else (f"Geology, deposit type and location of {n} major copper, iron, lead–zinc and gold deposits in Iran, with scientific references and expert notes on exploring and estimating each one.")}</p>'
            f'<div class="section-cta"><a class="btn solid" href="{hub_path}">{"ورود به اطلس" if fa else "Open the atlas"}</a></div></div>'
            f'<a class="map-wrap mini-map rv" href="{hub_path}" aria-label="{"اطلس کانسارها" if fa else "Deposit atlas"}">{map_svg(lang, deps, hub_path, labels=False, mini=True)}</a>'
            f'</div></div></section>')

# ---------- ارجاع‌های شماره‌دار ----------
_C1 = re.compile(r'\[\[([\w-]+)\]\]')
_CG = re.compile(r'\s*\[\[[\w-]+\]\](?:\s*\[\[[\w-]+\]\])*')

def cite_all(parts, lang, src):
    """[[کلید]] ← بالانویس شماره‌دار به ترتیب نخستین ارجاع؛ فهرست منابع به همان ترتیب."""
    order = []
    for p in parts:
        for k in _C1.findall(p):
            if k not in order: order.append(k)
    n = {k: i for i, k in enumerate(order, 1)}
    def lab(i): return str(i).translate(FA_D) if lang == 'fa' else str(i)
    def rep(m):
        keys = _C1.findall(m.group(0))
        return '<sup class="cite">' + ''.join(f'<a href="#r{n[k]}">[{lab(n[k])}]</a>' for k in keys) + '</sup>'
    return [_CG.sub(rep, p) for p in parts], [src[k] for k in order]

# ---------- مشخصات و ارقام منتشرشده ----------
FL = {
 'aka': ('نام‌های دیگر', 'Other names'),
 'loc': ('استان و شهرستان', 'Province and county'),
 'coord': ('موقعیت تقریبی', 'Approximate location'),
 'comm': ('ماده معدنی', 'Commodities'),
 'type': ('تیپ کانسار', 'Deposit type'),
 'belt': ('پهنهٔ ساختاری', 'Tectonic setting'),
 'host': ('سنگ میزبان', 'Host rocks'),
 'age': ('سن', 'Age'),
 'op': ('بهره‌بردار و وضعیت', 'Operator and status'),
}
CONF = {'H': ('بالا', 'High', 'h'), 'MH': ('متوسط تا بالا', 'Medium–high', 'h'), 'M': ('متوسط', 'Medium', 'm'),
        'ML': ('کم تا متوسط', 'Low–medium', 'l'), 'L': ('کم', 'Low', 'l')}
METAL = {'cu': ('pct', 'مس', 'copper', 'Cu'), 'zn': ('pct', 'روی', 'zinc', 'Zn'), 'au': ('gpt', 'طلا', 'gold', 'Au'), 'fe': (None, 'آهن', 'iron', 'Fe')}
LOWC = '#59666C'   # میلهٔ کم‌اطمینان: خنثی، همراه با برچسب در راهنما

def coord_txt(lang, d):
    if d.get('lat') is None: return 'منتشر نشده' if lang == 'fa' else 'not published'
    return f'{d["lat"]:.3f}° N, {d["lon"]:.3f}° E'

def coord_cell(lang, d):
    fa = lang == 'fa'
    if d.get('lat') is None:
        head = 'منتشر نشده' if fa else 'Not published'
    else:
        head = (f'<span dir="ltr">{coord_txt(lang, d)}</span> — {esc(d["coord_src"])}[[{d["coord_cite"]}]] · '
                f'{"اطمینان" if fa else "confidence"}: {CONF[d["coord_conf"]][0 if fa else 1]}')
    note = d[lang].get('coord_note', '')
    return head + (f'<span class="fnote">{note}</span>' if note else '')

def facts_table(lang, d):
    i = 0 if lang == 'fa' else 1; rows = []
    for k, v in d[lang]['facts']:
        rows.append((FL[k][i], v))
        if k == 'loc': rows.append((FL['coord'][i], coord_cell(lang, d)))
    return '<div class="tbl-scroll"><table class="dtable facts">' + ''.join(f'<tr><th>{esc(k)}</th><td>{v}</td></tr>' for k, v in rows) + '</table></div>'

def contained(d, r):
    """فلز محتوا به تن: میلیون تن × درصد × ۱۰⁴، یا میلیون تن × گرم در تن؛ رقم اعلام‌شده همان‌گونه که هست."""
    kind = METAL[d['metal']][0]
    if r.get('direct') is not None: return float(r['direct'])
    if not r.get('calc') or not kind: return None
    return sum(t * g * (1e4 if kind == 'pct' else 1) for t, g in r['calc'])

def metal_unit(d):
    kind = METAL[d['metal']][0]
    if kind == 'gpt': return 't'
    vals = [v for v in (contained(d, r) for r in d['res']) if v is not None]
    return 'Mt' if vals and max(vals) >= 1e6 else 'kt'

UNIT = {'Mt': (1e6, 1, 'میلیون تن', 'Mt'), 'kt': (1e3, 0, 'هزار تن', 'kt'), 't': (1, 0, 'تن', 't')}
def fmt_metal(lang, d, v, unit):
    sc, dec, ufa, uen = UNIT[unit]; x = v / sc
    if unit == 't' and x < 10: dec = 1
    m = METAL[d['metal']]
    return f'≈ {num(x, lang, dec)} {ufa} {m[1]}' if lang == 'fa' else f'≈ {num(x, lang, dec)} {uen} {m[3]}'

def res_chart(lang, d, unit):
    fa = lang == 'fa'; m = METAL[d['metal']]
    rows = [(r, contained(d, r)) for r in d['res'] if r.get('chart', True) and contained(d, r) is not None]
    if len(rows) < 2: return ''
    sc, dec = UNIT[unit][0], UNIT[unit][1]
    vals = [v / sc for _, v in rows]; vmax = max(vals)
    if unit == 't' and vmax < 10: dec = 1
    step = nice_ticks(0, vmax)[1]; top = math.ceil(vmax / step - 1e-9) * step or step
    ticks = [round(i * step, 10) for i in range(int(round(top / step)) + 1)]
    w, ml, mr, mt, rh, mb = 420, 4, 50, 2, 46, 50
    h = mt + rh * len(rows) + mb; x1 = w - mr
    X = lambda v: ml + v / top * (x1 - ml)
    y1 = mt + rh * len(rows); td = _dec(step)
    g = [f'<g stroke="{GRID}" stroke-width="1">'] + [f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{mt + 18}" y2="{y1}"/>' for t in ticks] + ['</g>']
    g += [f'<text x="{X(t):.1f}" y="{y1 + 18}" text-anchor="middle" fill="{MUTED}" font-size="12">{num(t, lang, td)}</text>' for t in ticks]
    ax = (f'{m[1]} محتوا ({UNIT[unit][2]})' if fa else f'Contained {m[2]} ({UNIT[unit][3]})')
    g.append(txt((ml + x1) / 2, h - 8, ax, lang, 'middle', 12.5))
    low = False
    for i, ((r, _), v) in enumerate(zip(rows, vals)):
        y0 = mt + i * rh; lo = CONF[r['conf']][2] == 'l'; low |= lo
        lab = (r['lab'] or ('', ''))[0 if fa else 1]
        g.append(txt(ml, y0 + 14, lab, lang, 'start', 13, INK2))
        g.append(f'<rect x="{ml}" y="{y0 + 21}" width="{max(X(v) - ml, 1.5):.1f}" height="15" rx="2" fill="{LOWC if lo else S1}"/>')
        g.append(f'<text x="{X(v) + 6:.1f}" y="{y0 + 33}" fill="{INK}" font-size="13">{num(v, lang, dec)}</text>')
    g.append(f'<line x1="{ml}" x2="{ml}" y1="{mt + 18}" y2="{y1}" stroke="{AXIS}" stroke-width="1"/>')
    items = [('اطمینان متوسط یا بالا' if fa else 'Medium or high confidence', S1, 'square')]
    if low: items.append(('اطمینان کم' if fa else 'Low confidence', LOWC, 'square'))
    cap = 'فلز محتوای هر رقم منتشرشده' if fa else 'Contained metal implied by each published figure'
    capd = ('هر میله فلز محتوای یک رقم را نشان می‌دهد؛ ارقام مبنا و دامنهٔ متفاوت دارند. داده‌های نمودار همان جدول بالاست.' if fa else
            'Each bar shows the contained metal implied by one figure; the figures differ in basis and scope. The table above holds the chart’s data.')
    return figure(''.join(g), cap, esc(capd), legend(items), '', None, w, h).replace('<figure class="chart"', '<figure class="chart res-chart"', 1)

def res_html(lang, d):
    fa = lang == 'fa'
    if not d['res']: return ''
    has_m = METAL[d['metal']][0] is not None
    unit = metal_unit(d) if has_m else None
    head = (['رقم منتشرشده', 'مبنا و منبع'] + (['فلز محتوا (محاسبهٔ نویسنده)'] if has_m else []) + ['اطمینان']) if fa else \
           (['Figure as published', 'Basis and source'] + (['Contained metal (author’s arithmetic)'] if has_m else []) + ['Confidence'])
    rows = []
    for r in d['res']:
        cells = [r['fa'] if fa else r['en'], (r['bfa'] if fa else r['ben']) + ''.join(f'[[{k}]]' for k in r['src'])]
        if has_m:
            v = contained(d, r)
            cells.append('—' if v is None else fmt_metal(lang, d, v, unit) + (f' <small>({r["dn"][0 if fa else 1]})</small>' if r.get('direct') is not None else ''))
        cf = CONF[r['conf']]
        cells.append(f'<span class="conf conf-{cf[2]}">{cf[0 if fa else 1]}</span>')
        rows.append('<tr>' + ''.join(f'<td data-th="{esc(hd)}">{c}</td>' for hd, c in zip(head, cells)) + '</tr>')
    note = ('هیچ‌یک از ارقام زیر مبنای کدهای گزارش‌دهی بین‌المللی مانند JORC یا NI 43-101 را ذکر نمی‌کند و تاریخ و عیار حد بیشترشان روشن نیست؛ بنابراین فقط «همان‌گونه که منتشر شده‌اند» و با منبع آمده‌اند.'
            + (' ستون فلز محتوا حاصل‌ضرب تناژ در عیار و محاسبهٔ نویسنده است؛ ارقام مبنا و دامنهٔ متفاوت دارند و قابل جمع نیستند.' if has_m else '')) if fa else \
           ('None of the figures below states a basis under an international reporting code such as JORC or NI 43-101, and most give no date or cut-off grade, so they are shown only “as published”, each with its source.'
            + (' The contained-metal column is tonnage multiplied by grade — the author’s arithmetic; the figures differ in basis and scope and must not be added together.' if has_m else ''))
    table = ('<div class="tbl-scroll"><table class="dtable res"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head)
             + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')
    return f'<p class="res-note">{note}</p>{table}' + (res_chart(lang, d, unit) if has_m else '')

# ---------- صفحه‌ها ----------
def build_hub(b, lang, deps):
    l = b.L[lang]; fa = lang == 'fa'; u = b.url(lang, 'atlas'); hub = b.path(lang, 'atlas')
    import deposits as D
    trail = [(l['crumb_home'], l['home']), (l['n_atlas'], hub)]
    title = 'اطلس کانسارهای ایران: مس، آهن، طلا و سرب و روی | علی علینقی' if fa else 'Atlas of Iranian Ore Deposits: Copper, Iron, Gold, Lead–Zinc | Ali Alinaghi'
    desc = ('زمین‌شناسی و موقعیت ۱۷ کانسار مهم ایران، از جمله سرچشمه، سونگون، میدوک، گل‌گهر، چادرملو، سنگان، مهدی‌آباد، انگوران و زرشوران؛ با منبع هر رقم، سطح اطمینان و تحلیل فلز محتوا.' if fa else
            'Geology and location of 17 major Iranian ore deposits — Sarcheshmeh, Sungun, Miduk, Gol-e-Gohar, Chadormalu, Sangan, Mehdiabad, Angouran, Zarshuran and more — with a source and confidence level for every figure and a contained-metal check.')
    lede = ('نقشه و معرفی کانسارهای مهم مس پورفیری، آهن، سرب و روی و طلای ایران. اطلاعات هر کانسار از مقاله‌ها و منابع منتشرشده گردآوری شده، منبع هر عدد ذکر شده و نکات کارشناسی جداگانه مشخص شده‌اند.' if fa else
            'A map and profiles of Iran’s major porphyry copper, iron, lead–zinc and gold deposits. Each profile is compiled from published papers and sources, every number is cited, and expert notes are marked separately.')
    cards = ''.join(f'<a class="area dep-card" data-c="{d["commodity"]}" href="{hub}{d["slug"]}/" style="--i:{i}"><span class="ico">{legend_key(COMM[d["commodity"]]["shape"])}</span>'
                    f'<span class="meta">{COMM[d["commodity"]][lang]} · {esc(d[lang]["province"])}</span><b>{esc(d[lang]["name"])}</b><span>{esc(d[lang]["type_short"])}</span>'
                    f'<i class="go">{l["more"]} {b.ico("arrow")}</i></a>' for i, d in enumerate(deps, 1))
    rows = ''.join(f'<tr><td><a href="{hub}{d["slug"]}/">{esc(d[lang]["name"])}</a></td><td>{COMM[d["commodity"]][lang]}</td><td>{esc(d[lang]["type_short"])}</td>'
                   f'<td>{esc(d[lang]["province"])}</td><td dir="ltr">{coord_txt(lang, d)}</td></tr>' for d in deps)
    head = ['کانسار', 'ماده', 'تیپ', 'استان', 'مختصات تقریبی'] if fa else ['Deposit', 'Commodity', 'Type', 'Province', 'Approx. coordinates']
    n_xy = sum(1 for d in deps if d.get('lat') is not None)
    dl = (f'<a class="btn dl" href="{b.path("fa", "atlas")}iran-deposits.csv" download>{b.ico("download")}'
          f'{f"دانلود مختصات {b.fanum(n_xy, lang)} کانسار (CSV)" if fa else f"Download coordinates of {n_xy} deposits (CSV)"}</a>')
    table = (f'<details class="tbl"><summary>{"نمایش جدول کانسارها" if fa else "Show the deposit table"}</summary><div class="tbl-scroll"><table><thead><tr>'
             + ''.join(f'<th>{h}</th>' for h in head) + f'</tr></thead><tbody>{rows}</tbody></table></div><p class="dl-row">{dl}</p></details>')
    note = ('موقعیت‌ها تقریبی‌اند و منبع هرکدام در صفحهٔ کانسار آمده است؛ مهدی‌آباد و موته تا تأیید موقعیت روی نقشه نیامده‌اند. ارقام ذخیره فقط با منبع و سال آمده‌اند.' if fa else
            'Locations are approximate, with each source given on the deposit page; Mehdiabad and Muteh are not mapped until their locations are verified. Resource figures appear only with their source and year.')
    secs, refs = list(D.HUB[lang]), []
    parts, refs = cite_all([s for _, s in secs], lang, D.SRC)
    secs = [(h, p) for (h, _), p in zip(secs, parts)]
    main = (b.page_hero(trail, 'map', 'اطلس کانسارهای ایران' if fa else 'Atlas of Iranian ore deposits', lede)
            + f'<section class="atlas"><div class="wrap">{filters_html(lang, deps)}'
            f'<figure class="chart map-fig rv"><figcaption><b>{"موقعیت کانسارها" if fa else "Deposit locations"}</b><span>{note}</span></figcaption>{legend_html(lang, deps)}'
            f'<div class="map-wrap">{map_svg(lang, deps, hub)}</div>{table}</figure>'
            f'<div class="areas hub-grid dep-grid rv">{cards}</div></div></section>'
            + b.doc_body(lang, secs, (), refs=refs, tail=b.share_html(lang, u, 'اطلس کانسارهای ایران' if fa else 'Atlas of Iranian ore deposits')
                         + b.feedback_html(lang, 'atlas', 'اطلس کانسارهای ایران' if fa else 'Atlas of Iranian ore deposits'))
            + b.cta_band(lang))
    ld = b.ld_graph(b.person_ld(lang),
         {"@type": "CollectionPage", "@id": u, "name": 'اطلس کانسارهای ایران' if fa else 'Atlas of Iranian ore deposits', "description": desc, "inLanguage": lang,
          "author": {"@id": b.SITE + "/#person"}, "isPartOf": {"@id": b.SITE + "/#website"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i, "url": b.url(lang, 'atlas', d['slug']), "name": d[lang]['name']} for i, d in enumerate(deps, 1)]}},
         b.crumbs_ld(lang, trail))
    return b.page(lang, 'atlas', None, title, desc, ld, main, 'website', l['n_atlas'], scripts=('charts.js', 'atlas.js'))

def build_deposit(b, lang, d, deps):
    l = b.L[lang]; fa = lang == 'fa'; c = d[lang]; u = b.url(lang, 'atlas', d['slug']); hub = b.path(lang, 'atlas')
    import deposits as D
    trail = [(l['crumb_home'], l['home']), (l['n_atlas'], hub), (c['name'], b.path(lang, 'atlas', d['slug']))]
    cm = COMM[d['commodity']]
    tag = f'<span class="tag">{legend_key(cm["shape"])}{cm[lang]} · {esc(c["type_short"])}</span>'
    meta = (f'<div class="art-meta"><span class="av" aria-hidden="true">A.A</span><span>{l["by"]} <a href="{l["home"]}">{l["name"]}</a></span>'
            f'<span>{l["updated"]}: <time datetime="{d["updated"]}">{b.fdate(d["updated"], lang)}</time></span></div>')
    mapfig = (f'<figure class="chart map-fig mini rv"><div class="map-wrap">{map_svg(lang, deps, hub, highlight=d["slug"], labels=False)}</div>'
              f'<figcaption><span>{"موقعیت تقریبی" if fa else "Approximate location"}: <span dir="ltr">{coord_txt(lang, d)}</span> — {esc(d["coord_src"])}</span></figcaption></figure>'
              if d.get('lat') is not None else '')
    lead = f'<section class="prose-sec rv" id="facts"><h2>{"مشخصات" if fa else "Key facts"}</h2>{facts_table(lang, d)}{mapfig}</section>'
    res = res_html(lang, d)
    secs = [(h, s.replace('{{res}}', res)) for h, s in c['sections']]
    expert = list(c['expert']) + [deposit_notes.NOTES[d['ntype']][lang]]
    parts, refs = cite_all([lead] + [s for _, s in secs] + [s for _, s in expert], lang, D.SRC)
    lead, k = parts[0], 1 + len(secs)
    secs = [(h, p) for (h, _), p in zip(secs, parts[1:k])]
    expert = [(h, p) for (h, _), p in zip(expert, parts[k:])]
    xk = 'یادداشت کارشناسی — تحلیل نویسنده، نه دادهٔ منتشرشده' if fa else 'Expert note — the author’s analysis, not published data'
    mid = ''.join(f'<section class="prose-sec expert rv" id="x{n}"><h2>{h}</h2><p class="xk">{xk}</p>{s}</section>' for n, (h, s) in enumerate(expert, 1))
    tail = b.share_html(lang, u, c['h1']) + b.feedback_html(lang, 'dep-' + d['slug'], c['h1']) + b.author_html(lang)
    body = b.doc_body(lang, secs, (), lead=lead, tail=tail, refs=refs, mid=mid)
    body = body.replace(f'<h4>{l["toc"]}</h4>', f'<h4>{l["toc"]}</h4><a href="#facts">{"مشخصات" if fa else "Key facts"}</a>', 1)
    body = body.replace('<a href="#refs">', ''.join(f'<a href="#x{n}">{h}</a>' for n, (h, _) in enumerate(expert, 1)) + '<a href="#refs">', 1)
    rel_deps = [x for s in d['related'] for x in deps if x['slug'] == s]
    relc = ''.join(f'<a class="area dep-card" href="{hub}{x["slug"]}/" style="--i:{i}"><span class="ico">{legend_key(COMM[x["commodity"]]["shape"])}</span>'
                   f'<span class="meta">{COMM[x["commodity"]][lang]} · {esc(x[lang]["province"])}</span><b>{esc(x[lang]["name"])}</b><span>{esc(x[lang]["type_short"])}</span>'
                   f'<i class="go">{l["more"]} {b.ico("arrow")}</i></a>' for i, x in enumerate(rel_deps, 1))
    related = (f'<section class="related"><div class="wrap"><h2 class="rv">{"کانسارهای مرتبط" if fa else "Related deposits"}</h2><div class="areas rel rv">{relc}</div></div></section>' if relc else '') \
              + b.related_html(lang, d.get('links', {}))
    main = b.page_hero(trail, None, c['h1'], c['lede'], meta, tag=tag) + body + related + b.cta_band(lang)
    place = {"@type": "Place", "name": c['name'], "address": {"@type": "PostalAddress", "addressRegion": c['province'], "addressCountry": "IR"}}
    if d.get('lat') is not None: place["geo"] = {"@type": "GeoCoordinates", "latitude": d['lat'], "longitude": d['lon']}
    dois = sorted(set(re.findall(r'https://doi\.org/[^"]+', ' '.join(refs))))
    ld = b.ld_graph(b.person_ld(lang),
         {"@type": "TechArticle", "@id": u + "#article", "headline": c['h1'], "description": c['desc'], "inLanguage": lang,
          "datePublished": d['published'], "dateModified": d['updated'], "author": {"@id": b.SITE + "/#person"}, "publisher": {"@id": b.SITE + "/#person"},
          "mainEntityOfPage": u, "image": b.SITE + f'/og/{lang}-atlas-{d["slug"]}.jpg', "about": place, "isPartOf": {"@id": b.SITE + "/#website"},
          "keywords": ', '.join([c['name'], c['type_short'], cm[lang], c['province']]), **({"citation": dois} if dois else {})},
         b.crumbs_ld(lang, trail))
    return b.page(lang, 'atlas', d['slug'], c['title'], c['desc'], ld, main, og_label=l['n_atlas'], scripts=('charts.js',))

def csv_text(b, deps):
    """مختصات کانسارهای تأییدشده؛ مهدی‌آباد و موته عمداً حذف شده‌اند."""
    out = io.StringIO(); w = csv.writer(out, lineterminator='\n')
    w.writerow(['slug', 'name_en', 'name_fa', 'commodity', 'deposit_type', 'province', 'latitude', 'longitude',
                'coordinate_source', 'coordinate_confidence', 'page_fa', 'page_en'])
    for d in deps:
        if d.get('lat') is None: continue
        w.writerow([d['slug'], d['en']['name'], d['fa']['name'], COMM[d['commodity']]['en'], d['en']['type_short'], d['en']['province'],
                    f'{d["lat"]:.5f}', f'{d["lon"]:.5f}', d['coord_src'], CONF[d['coord_conf']][1],
                    b.url('fa', 'atlas', d['slug']), b.url('en', 'atlas', d['slug'])])
    return '﻿' + out.getvalue()
