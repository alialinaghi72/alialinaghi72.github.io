# اطلس کانسارها: نقشهٔ ایران، صفحهٔ فهرست و صفحهٔ هر کانسار.
# مرز کشورها: Natural Earth (دامنهٔ عمومی) از بستهٔ world-atlas، ساده‌شده در data/iran_outline.json
import json, math, os, html
from charts import S1, S2, SURF, INK, INK2, MUTED, txt

HERE = os.path.dirname(os.path.abspath(__file__))
OUTLINE = json.load(open(os.path.join(HERE, 'data', 'iran_outline.json')))
LON0, LON1, LAT0, LAT1 = 42.6, 64.6, 24.0, 40.6
COSL = math.cos(math.radians(32.3))
W = 640; K = W / ((LON1 - LON0) * COSL); H = round((LAT1 - LAT0) * K)
def P(lon, lat): return ((lon - LON0) * COSL * K, (LAT1 - lat) * K)
def esc(s): return html.escape(str(s), quote=True)

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
            f'<p class="lede">{(f"زمین‌شناسی، تیپ و موقعیت {n} کانسار مهم مس، آهن، سرب و روی و طلای ایران؛ با منابع علمی و نکات کارشناسی دربارهٔ اکتشاف و تخمین ذخیرهٔ هرکدام.") if fa else (f"Geology, deposit type and location of {n} major copper, iron, lead–zinc and gold deposits in Iran, with scientific references and expert notes on exploring and estimating each one.")}</p>'
            f'<div class="section-cta"><a class="btn solid" href="{hub_path}">{"ورود به اطلس" if fa else "Open the atlas"}</a></div></div>'
            f'<a class="map-wrap mini-map rv" href="{hub_path}" aria-label="{"اطلس کانسارها" if fa else "Deposit atlas"}">{map_svg(lang, deps, hub_path, labels=False, mini=True)}</a>'
            f'</div></div></section>')

def facts_table(lang, d):
    c = d[lang]
    rows = ''.join(f'<tr><th>{esc(k)}</th><td>{v}</td></tr>' for k, v in c['facts'])
    return f'<div class="tbl-scroll"><table class="dtable facts">{rows}</table></div>'

def coord_txt(lang, d):
    if d.get('lat') is None: return 'منتشر نشده' if lang == 'fa' else 'not published'
    s = f'{d["lat"]:.3f}° N، {d["lon"]:.3f}° E' if lang == 'fa' else f'{d["lat"]:.3f}° N, {d["lon"]:.3f}° E'
    return s

def build_hub(b, lang, deps):
    l = b.L[lang]; fa = lang == 'fa'; u = b.url(lang, 'atlas'); hub = b.path(lang, 'atlas')
    trail = [(l['crumb_home'], l['home']), (l['n_atlas'], hub)]
    title = 'اطلس کانسارهای ایران: مس، آهن، طلا و سرب و روی | علی علینقی' if fa else 'Atlas of Iranian Ore Deposits: Copper, Iron, Gold, Lead–Zinc | Ali Alinaghi'
    desc = ('معرفی زمین‌شناسی و موقعیت کانسارهای مهم ایران از جمله سرچشمه، سونگون، میدوک، گل‌گهر، چادرملو، سنگان، مهدی‌آباد، انگوران و زرشوران، با منابع علمی و نکات اکتشاف و تخمین ذخیره.' if fa else
            'Geology and location of Iran\'s major ore deposits — Sarcheshmeh, Sungun, Miduk, Gol-e-Gohar, Chadormalu, Sangan, Mehdiabad, Angouran, Zarshuran and more — with scientific references and exploration and estimation notes.')
    lede = ('نقشه و معرفی کانسارهای مهم مس پورفیری، آهن، سرب و روی و طلای ایران. اطلاعات هر کانسار از مقاله‌ها و منابع منتشرشده گردآوری شده و منبع هر مورد ذکر شده است؛ نکات کارشناسی جداگانه مشخص شده‌اند.' if fa else
            'A map and profiles of Iran\'s major porphyry copper, iron, lead–zinc and gold deposits. Each profile is compiled from published papers and sources, with every fact cited; expert notes are marked separately.')
    cards = ''.join(f'<a class="area dep-card" data-c="{d["commodity"]}" href="{hub}{d["slug"]}/" style="--i:{i}"><span class="ico">{legend_key(COMM[d["commodity"]]["shape"])}</span>'
                    f'<span class="meta">{COMM[d["commodity"]][lang]} · {esc(d[lang]["province"])}</span><b>{esc(d[lang]["name"])}</b><span>{esc(d[lang]["type_short"])}</span>'
                    f'<i class="go">{l["more"]} {b.ico("arrow")}</i></a>' for i, d in enumerate(deps, 1))
    rows = ''.join(f'<tr><td><a href="{hub}{d["slug"]}/">{esc(d[lang]["name"])}</a></td><td>{COMM[d["commodity"]][lang]}</td><td>{esc(d[lang]["type_short"])}</td>'
                   f'<td>{esc(d[lang]["province"])}</td><td dir="ltr">{coord_txt(lang, d)}</td></tr>' for d in deps)
    head = ['کانسار', 'ماده', 'تیپ', 'استان', 'مختصات تقریبی'] if fa else ['Deposit', 'Commodity', 'Type', 'Province', 'Approx. coordinates']
    table = (f'<details class="tbl"><summary>{"نمایش جدول کانسارها" if fa else "Show the deposit table"}</summary><div class="tbl-scroll"><table><thead><tr>'
             + ''.join(f'<th>{h}</th>' for h in head) + f'</tr></thead><tbody>{rows}</tbody></table></div></details>')
    note = ('موقعیت‌ها تقریبی‌اند و از منابع منتشرشده (عمدتاً Mindat و مقاله‌های علمی) گرفته شده‌اند. ارقام ذخیره در منابع مختلف متفاوت‌اند و فقط با ذکر منبع و سال آمده‌اند.' if fa else
            'Locations are approximate and taken from published sources (mainly Mindat and scientific papers). Resource figures differ between sources and are given only with their source and year.')
    main = (b.page_hero(trail, 'map', 'اطلس کانسارهای ایران' if fa else 'Atlas of Iranian ore deposits', lede)
            + f'<section class="atlas"><div class="wrap">{filters_html(lang, deps)}'
            f'<figure class="chart map-fig rv"><figcaption><b>{"موقعیت کانسارها" if fa else "Deposit locations"}</b><span>{note}</span></figcaption>{legend_html(lang, deps)}'
            f'<div class="map-wrap">{map_svg(lang, deps, hub)}</div>{table}</figure>'
            f'<div class="areas hub-grid dep-grid rv">{cards}</div>{b.share_html(lang, u, "اطلس کانسارهای ایران" if fa else "Atlas of Iranian ore deposits")}</div></section>'
            + b.cta_band(lang))
    ld = b.ld_graph(b.person_ld(lang),
         {"@type": "CollectionPage", "@id": u, "name": 'اطلس کانسارهای ایران' if fa else 'Atlas of Iranian ore deposits', "description": desc, "inLanguage": lang,
          "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i, "url": b.url(lang, 'atlas', d['slug']), "name": d[lang]['name']} for i, d in enumerate(deps, 1)]}},
         b.crumbs_ld(lang, trail))
    return b.page(lang, 'atlas', None, title, desc, ld, main, 'website', l['n_atlas'], scripts=('charts.js', 'atlas.js'))

def build_deposit(b, lang, d, deps):
    l = b.L[lang]; fa = lang == 'fa'; c = d[lang]; u = b.url(lang, 'atlas', d['slug']); hub = b.path(lang, 'atlas')
    trail = [(l['crumb_home'], l['home']), (l['n_atlas'], hub), (c['name'], b.path(lang, 'atlas', d['slug']))]
    cm = COMM[d['commodity']]
    tag = f'<span class="tag">{legend_key(cm["shape"])}{cm[lang]} · {esc(c["type_short"])}</span>'
    meta = (f'<div class="art-meta"><span class="av" aria-hidden="true">A.A</span><span>{l["by"]} <a href="{l["home"]}">{l["name"]}</a></span>'
            f'<span>{l["updated"]}: <time datetime="{d["updated"]}">{b.fdate(d["updated"], lang)}</time></span></div>')
    lead = (f'<section class="prose-sec rv" id="facts"><h2>{"مشخصات" if fa else "Key facts"}</h2>{facts_table(lang, d)}'
            f'<figure class="chart map-fig mini rv"><div class="map-wrap">{map_svg(lang, deps, hub, highlight=d["slug"], labels=False)}</div>'
            f'<figcaption><span>{"موقعیت تقریبی" if fa else "Approximate location"}: <span dir="ltr">{coord_txt(lang, d)}</span> — {esc(d["coord_src"])}</span></figcaption></figure></section>')
    expert = ''.join(f'<section class="prose-sec expert rv" id="x{n}"><h2>{h}</h2><p class="xk">{"یادداشت کارشناسی — تحلیل نویسنده، نه دادهٔ منتشرشده" if fa else "Expert note — the author’s analysis, not published data"}</p>{body}</section>'
                     for n, (h, body) in enumerate(c['expert'], 1))
    secs = c['sections']
    tail = expert + b.share_html(lang, u, c['h1']) + b.feedback_html(lang, 'dep-' + d['slug'], c['h1']) + b.author_html(lang)
    body = b.doc_body(lang, secs, (), lead=lead, tail=tail, refs=d['refs'])
    body = body.replace(f'<h4>{l["toc"]}</h4>', f'<h4>{l["toc"]}</h4><a href="#facts">{"مشخصات" if fa else "Key facts"}</a>', 1)
    body = body.replace('<a href="#refs">', ''.join(f'<a href="#x{n}">{h}</a>' for n, (h, _) in enumerate(c['expert'], 1)) + '<a href="#refs">', 1)
    rel_deps = [x for x in deps if x['slug'] in d['related']]
    relc = ''.join(f'<a class="area dep-card" href="{hub}{x["slug"]}/" style="--i:{i}"><span class="ico">{legend_key(COMM[x["commodity"]]["shape"])}</span>'
                   f'<span class="meta">{COMM[x["commodity"]][lang]} · {esc(x[lang]["province"])}</span><b>{esc(x[lang]["name"])}</b><span>{esc(x[lang]["type_short"])}</span>'
                   f'<i class="go">{l["more"]} {b.ico("arrow")}</i></a>' for i, x in enumerate(rel_deps, 1))
    related = (f'<section class="related"><div class="wrap"><h2 class="rv">{"کانسارهای مرتبط" if fa else "Related deposits"}</h2><div class="areas rel rv">{relc}</div></div></section>' if relc else '') \
              + b.related_html(lang, d.get('links', {}))
    main = b.page_hero(trail, None, c['h1'], c['lede'], meta, tag=tag) + body + related + b.cta_band(lang)
    place = {"@type": "Place", "name": c['name'], "address": {"@type": "PostalAddress", "addressRegion": c['province'], "addressCountry": "IR"}}
    if d.get('lat') is not None: place["geo"] = {"@type": "GeoCoordinates", "latitude": d['lat'], "longitude": d['lon']}
    ld = b.ld_graph(b.person_ld(lang),
         {"@type": "TechArticle", "@id": u + "#article", "headline": c['h1'], "description": c['desc'], "inLanguage": lang,
          "datePublished": d['published'], "dateModified": d['updated'], "author": {"@id": b.SITE + "/#person"}, "publisher": {"@id": b.SITE + "/#person"},
          "mainEntityOfPage": u, "image": b.SITE + f'/og/{lang}-atlas-{d["slug"]}.jpg', "about": place, "isPartOf": {"@id": b.SITE + "/#website"}},
         b.crumbs_ld(lang, trail))
    return b.page(lang, 'atlas', d['slug'], c['title'], c['desc'], ld, main, og_label=l['n_atlas'], scripts=('charts.js',))
