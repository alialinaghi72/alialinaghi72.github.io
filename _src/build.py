#!/usr/bin/env python3
"""سازندهٔ سایت. همهٔ صفحه‌ها را از روی محتوای _src می‌سازد.

اجرا:  python3 _src/build.py      (نیاز: pip install segno)
خروجی: index.html، en/index.html، services/*/index.html، en/services/*/index.html، sitemap.xml
"""
import json, os, re, sys, html
from datetime import date

SRC = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SRC)
sys.path.insert(0, SRC)
from icons import ICONS
import visual, topics_fa, topics_en

SITE = 'https://alialinaghi72.github.io'
PHONE, PHONE_TXT, EMAIL = '+989135133397', '+98 913 513 3397', 'alialinaghi72@gmail.com'
LINKEDIN, WA = 'https://www.linkedin.com/in/alialinaghi72', 'https://wa.me/989135133397'
TODAY = date.today().isoformat()
def _ver(rel):
    import hashlib
    return hashlib.sha1(open(os.path.join(ROOT, rel), 'rb').read()).hexdigest()[:8]
CSS_V, JS_V = _ver('assets/site.css'), _ver('assets/site.js')

L = {
 'fa': dict(dir='rtl', locale='fa_IR', alt_locale='en_US', name='علی علینقی', home='/', svc='/services/',
   skip='رفتن به محتوا', menu='منو', mainnav='منوی اصلی', other='English', other_lang='en',
   nav=[('#services','خدمات'),('#workflow','روش کار'),('#areas','حوزه‌ها'),('#projects','پروژه‌ها'),('#contact','تماس')],
   foot_tag='مشاورهٔ اکتشاف معدن، مدل‌سازی سه‌بعدی زمین‌شناسی و تخمین ذخیره', areas='حوزه‌های تخصصی', pages='صفحه‌ها',
   contact='تماس', top='بازگشت به بالا ↑', crumb_home='خانه', crumb_svc='خدمات', toc='در این صفحه', related='موضوعات مرتبط',
   faq='پرسش‌ها', cta_h='پروژه‌ای در دست دارید؟', cta_p='برای بررسی محدوده، بازبینی گزارش یا شروع تخمین ذخیره پیام بدهید. معمولاً ظرف یک روز کاری پاسخ می‌دهم.',
   cta_wa='گفت‌وگو در واتس‌اپ', cta_mail='ارسال ایمیل', more='بیشتر بخوانید', year='۲۰۲۶', home_label='صفحهٔ اصلی',
   vcard_label='کد QR — ذخیرهٔ مخاطب علی علینقی'),
 'en': dict(dir='ltr', locale='en_US', alt_locale='fa_IR', name='Ali Alinaghi', home='/en/', svc='/en/services/',
   skip='Skip to content', menu='Menu', mainnav='Main', other='فارسی', other_lang='fa',
   nav=[('#services','Services'),('#workflow','Approach'),('#areas','Expertise'),('#projects','Projects'),('#contact','Contact')],
   foot_tag='Mineral exploration, 3D geological modelling and resource estimation consulting', areas='Areas of expertise', pages='Pages',
   contact='Contact', top='Back to top ↑', crumb_home='Home', crumb_svc='Services', toc='On this page', related='Related topics',
   faq='Questions', cta_h='Have a project in mind?', cta_p='Send a message about assessing an area, reviewing a report or starting a resource estimate. I usually reply within one working day.',
   cta_wa='Chat on WhatsApp', cta_mail='Send an email', more='Read more', year='2026', home_label='home',
   vcard_label='QR code — save Ali Alinaghi as a contact'),
}
TOPICS = {'fa': topics_fa.TOPICS, 'en': topics_en.TOPICS}
CARD = {
 'fa': {'resource-estimation':'زمین‌آمار، کریجینگ و شبیه‌سازی، مدل بلوکی و رده‌بندی منابع.',
        '3d-geological-modelling':'مدل لیتولوژی، دگرسانی، ساختار و پهنهٔ کانی‌سازی در Leapfrog و Surpac.',
        'mineral-exploration':'از شناسایی و پی‌جویی تا اکتشاف تفصیلی و هدف‌گیری حفاری.',
        'exploration-geophysics':'تفسیر مغناطیس‌سنجی، IP، مقاومت ویژه و گرانی‌سنجی.',
        'exploration-geochemistry':'نمونه‌برداری، جداسازی آنومالی و عناصر ردیاب.',
        'remote-sensing':'نقشه‌برداری دگرسانی با ASTER، Sentinel-2 و Landsat.',
        'project-management':'برنامه‌ریزی مرحله‌ای، بودجه، مدیریت حفاری و کنترل کیفیت.',
        'commodities':'طلا، مس، مولیبدن، آهن، سرب و روی، تالک و زغال‌سنگ.'},
 'en': {'resource-estimation':'Geostatistics, kriging and simulation, block models and resource classification.',
        '3d-geological-modelling':'Lithology, alteration, structure and mineralised domains in Leapfrog and Surpac.',
        'mineral-exploration':'From reconnaissance and prospecting to detailed exploration and drill targeting.',
        'exploration-geophysics':'Interpretation of magnetics, IP, resistivity and gravity.',
        'exploration-geochemistry':'Sampling design, anomaly separation and pathfinder elements.',
        'remote-sensing':'Alteration mapping with ASTER, Sentinel-2 and Landsat.',
        'project-management':'Staged planning, budgets, drilling management and QA/QC.',
        'commodities':'Gold, copper, molybdenum, iron, lead–zinc, talc and coal.'},
}
BY_SLUG = {lang: {t['slug']: t for t in TOPICS[lang]} for lang in L}

def ico(name): return ICONS[name]
def esc(s): return html.escape(s, quote=True)
def page_url(lang, slug=None):
    base = L[lang]['home']
    return SITE + (base if slug is None else L[lang]['svc'] + slug + '/')

def head(lang, title, desc, slug=None, ld=None):
    l = L[lang]; url = page_url(lang, slug)
    fa_url, en_url = page_url('fa', slug), page_url('en', slug)
    ld_tag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>' if ld else ''
    verify = '<meta name="google-site-verification" content="yGlYYZduh8Y1SDMxFbUH2CFhwXWF_r1zAWW8D1_FwbQ">\n' if lang == 'fa' and slug is None else ''
    return f'''<!DOCTYPE html>
<html lang="{lang}" dir="{l["dir"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{verify}<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{l["name"]}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#0B0E10">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="fa" href="{fa_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fa_url}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
<link rel="icon" href="/icon-512.png" type="image/png" sizes="512x512">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="{"profile" if slug is None else "article"}">
<meta property="og:site_name" content="{l["name"]}">
<meta property="og:locale" content="{l["locale"]}">
<meta property="og:locale:alternate" content="{l["alt_locale"]}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE}/og.png">
<link rel="preload" href="/fonts/Vazirmatn.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css?v={CSS_V}">
<script>document.documentElement.classList.add('js')</script>
{ld_tag}
</head>
<body>
<a class="skip" href="#main">{l["skip"]}</a>
'''

def header(lang, slug=None, is_home=False):
    l = L[lang]; other = L[l['other_lang']]
    prefix = '' if is_home else l['home']
    links = ''.join(f'<a href="{prefix}{h}">{t}</a>' for h, t in l['nav'])
    other_href = other['home'] if slug is None else other['svc'] + slug + '/'
    return f'''<header class="site-header">
  <div class="wrap bar">
    <a class="mark" href="{"#top" if is_home else l["home"]}" aria-label="{l["name"]} — {l["home_label"]}">
      <span class="mono">A.A</span>
      <span>{l["name"]}</span>
    </a>
    <nav aria-label="{l["mainnav"]}">
      <div class="links" id="nav-links">{links}</div>
      <a class="lang" href="{other_href}" hreflang="{l["other_lang"]}" lang="{l["other_lang"]}">{l["other"]}</a>
      <button class="menu-btn" id="menu-btn" type="button" aria-label="{l["menu"]}" aria-controls="nav-links" aria-expanded="false"><span></span></button>
    </nav>
  </div>
</header>
'''

def footer(lang, is_home=False):
    l = L[lang]; other = L[l['other_lang']]; prefix = '' if is_home else l['home']
    areas = ''.join(f'<a href="{l["svc"]}{t["slug"]}/">{t["short"]}</a>' for t in TOPICS[lang])
    pages = ''.join(f'<a href="{prefix}{h}">{t}</a>' for h, t in l['nav'])
    return f'''<footer><div class="wrap">
  <div class="foot">
    <div class="brand"><b>{l["name"]}</b><span>{l["foot_tag"]}</span></div>
    <nav class="fcol" aria-label="{l["areas"]}"><h4>{l["areas"]}</h4>{areas}</nav>
    <nav class="fcol" aria-label="{l["pages"]}"><h4>{l["pages"]}</h4>{pages}<a href="{other["home"]}" hreflang="{l["other_lang"]}" lang="{l["other_lang"]}">{l["other"]}</a></nav>
    <div class="fcol"><h4>{l["contact"]}</h4><a href="tel:{PHONE}" dir="ltr">{PHONE_TXT}</a><a href="mailto:{EMAIL}">{EMAIL}</a><a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a></div>
  </div>
  <div class="foot-bottom">
    <span>© <span id="year">{l["year"]}</span> {l["name"]}</span>
    <a class="to-top" href="#top">{l["top"]}</a>
  </div>
</div></footer>

<script src="/assets/site.js?v={JS_V}" defer></script>
</body>
</html>
'''

def person_ld(lang):
    fa = lang == 'fa'
    return {
      "@type": "Person", "@id": SITE + "/#person",
      "name": "علی علینقی" if fa else "Ali Alinaghi",
      "alternateName": ["Ali Alinaghi", "علي علينقي"] if fa else ["علی علینقی"],
      "jobTitle": "کارشناس ارشد اکتشاف معدن" if fa else "MSc Mineral Exploration — resource modelling and estimation specialist",
      "url": SITE + L[lang]['home'], "image": SITE + "/og.png", "email": "mailto:" + EMAIL, "telephone": PHONE,
      "sameAs": [LINKEDIN],
      "knowsAbout": (["اکتشاف معدن", "تخمین ذخیره", "مدل‌سازی سه‌بعدی زمین‌شناسی", "مدل بلوکی", "زمین‌آمار", "کریجینگ", "ژئوفیزیک اکتشافی", "ژئوشیمی اکتشافی", "دورسنجی", "سنجش از دور", "مدیریت پروژه اکتشافی", "زمین‌شناسی اقتصادی", "طلا", "مس", "مولیبدن", "آهن", "سرب و روی", "تالک", "زغال‌سنگ", "JORC", "NI 43-101"] if fa else
                     ["Mineral exploration", "Resource estimation", "3D geological modelling", "Block modelling", "Geostatistics", "Kriging", "Exploration geophysics", "Exploration geochemistry", "Remote sensing", "Exploration project management", "Economic geology", "Gold", "Copper", "Molybdenum", "Iron ore", "Lead–zinc", "Talc", "Coal", "JORC", "NI 43-101"]),
      "knowsLanguage": ["fa", "en"], "address": {"@type": "PostalAddress", "addressCountry": "IR"}}

def home_ld(lang):
    fa = lang == 'fa'
    faq = re.findall(r'<summary>(.*?)</summary>\s*<p>(.*?)</p>', open(f'{SRC}/home_{lang}.html', encoding='utf-8').read(), re.S)
    return {"@context": "https://schema.org", "@graph": [
      person_ld(lang),
      {"@type": "ProfessionalService", "@id": SITE + "/#service",
       "name": "مشاورهٔ اکتشاف معدن و تخمین ذخیره — علی علینقی" if fa else "Ali Alinaghi — mineral exploration and resource estimation consulting",
       "founder": {"@id": SITE + "/#person"}, "url": SITE + L[lang]['home'], "image": SITE + "/og.png",
       "telephone": PHONE, "email": "mailto:" + EMAIL, "priceRange": "$$",
       "areaServed": [{"@type": "Country", "name": n} for n in ["Iran", "Armenia", "Morocco", "Venezuela"]],
       "address": {"@type": "PostalAddress", "addressCountry": "IR"},
       "hasOfferCatalog": {"@type": "OfferCatalog", "name": "خدمات" if fa else "Services", "itemListElement": [
          {"@type": "Offer", "itemOffered": {"@type": "Service", "name": t['h1'], "url": page_url(lang, t['slug'])}} for t in TOPICS[lang]]}},
      {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/",
       "name": "علی علینقی — اکتشاف معدن و تخمین ذخیره" if fa else "Ali Alinaghi — mineral exploration and resource estimation",
       "inLanguage": ["fa-IR", "en"], "publisher": {"@id": SITE + "/#person"}},
      {"@type": "FAQPage", "@id": SITE + L[lang]['home'] + "#faq", "mainEntity": [
          {"@type": "Question", "name": q.strip(), "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a).strip()}} for q, a in faq]},
    ]}

def topic_ld(lang, t):
    l = L[lang]; url = page_url(lang, t['slug'])
    g = [person_ld(lang),
         {"@type": "Service", "@id": url + "#service", "name": t['h1'], "serviceType": t['h1'], "description": t['desc'], "url": url,
          "provider": {"@id": SITE + "/#person"}, "areaServed": ["Iran", "Armenia", "Morocco", "Venezuela"], "inLanguage": lang},
         {"@type": "BreadcrumbList", "itemListElement": [
           {"@type": "ListItem", "position": 1, "name": l['crumb_home'], "item": SITE + l['home']},
           {"@type": "ListItem", "position": 2, "name": l['crumb_svc'], "item": SITE + l['home'] + '#areas'},
           {"@type": "ListItem", "position": 3, "name": t['h1'], "item": url}]}]
    if t['faq']:
        g.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t['faq']]})
    return {"@context": "https://schema.org", "@graph": g}

def topics_grid(lang):
    l = L[lang]; cards = []
    for n, t in enumerate(TOPICS[lang], 1):
        cards.append(f'<a class="area" href="{l["svc"]}{t["slug"]}/" style="--i:{n}"><span class="ico">{ico(t["icon"])}</span>'
                     f'<b>{t["h1"]}</b><span>{CARD[lang][t["slug"]]}</span>'
                     f'<i class="go">{l["more"]} {ico("arrow")}</i></a>')
    return '<div class="areas rv">' + ''.join(cards) + '</div>'

def fill(h, lang):
    vcard = f"BEGIN:VCARD\r\nVERSION:3.0\r\nN:Alinaghi;Ali;;;\r\nFN:Ali Alinaghi\r\nTEL;TYPE=CELL:{PHONE}\r\nEMAIL:{EMAIL}\r\nURL:{SITE}/\r\nEND:VCARD\r\n"
    rep = {'{{BM}}': visual.hero_svg(), '{{STORY}}': visual.story_svg(), '{{VARIO}}': visual.variogram_svg(), '{{SWATH}}': visual.swath_svg(),
           '{{QR}}': visual.qr_svg(vcard, L[lang]['vcard_label']), '{{AREAS}}': topics_grid(lang), '{{SVC}}': L[lang]['svc']}
    for k, v in rep.items(): h = h.replace(k, v)
    h = re.sub(r'\{\{ico:(\w+)\}\}', lambda m: ico(m.group(1)), h)
    left = re.findall(r'\{\{.*?\}\}', h)
    assert not left, left
    return h

def build_home(lang):
    body = open(f'{SRC}/home_{lang}.html', encoding='utf-8').read()
    meta = re.search(r'<!--\s*title:(.*?)\n\s*desc:(.*?)-->', body, re.S)
    title, desc = meta.group(1).strip(), meta.group(2).strip()
    body = body[meta.end():]
    return head(lang, title, desc, None, home_ld(lang)) + header(lang, None, True) + fill(body, lang) + footer(lang, True)

def build_topic(lang, t):
    l = L[lang]
    toc = ''.join(f'<a href="#s{n}">{h}</a>' for n, (h, _) in enumerate(t['sections'], 1))
    if t['faq']: toc += f'<a href="#q">{l["faq"]}</a>'
    secs = ''.join(f'<section class="prose-sec rv" id="s{n}"><h2>{h}</h2>{b}</section>' for n, (h, b) in enumerate(t['sections'], 1))
    faq = ''
    if t['faq']:
        faq = f'<section class="prose-sec rv" id="q"><h2>{l["faq"]}</h2><div class="faq">' + ''.join(
            f'<details{" open" if i == 0 else ""}><summary>{q}</summary><p>{a}</p></details>' for i, (q, a) in enumerate(t['faq'])) + '</div></section>'
    rel = ''.join(f'<a class="area" href="{l["svc"]}{s}/"><span class="ico">{ico(BY_SLUG[lang][s]["icon"])}</span><b>{BY_SLUG[lang][s]["h1"]}</b>'
                  f'<i class="go">{l["more"]} {ico("arrow")}</i></a>' for s in t['related'])
    main = f'''<main id="main">
<section class="page-hero" id="top"><div class="wrap">
  <nav class="crumbs" aria-label="breadcrumb"><a href="{l["home"]}">{l["crumb_home"]}</a><span>/</span><a href="{l["home"]}#areas">{l["crumb_svc"]}</a><span>/</span><span aria-current="page">{t["short"]}</span></nav>
  <div class="page-ico">{ico(t["icon"])}</div>
  <h1 class="vt-title">{t["h1"]}</h1>
  <p class="lede-lg">{t["lede"]}</p>
  <div class="actions"><a class="btn solid" href="{WA}" target="_blank" rel="noopener">{ico("wa")}{l["cta_wa"]}</a><a class="btn" href="mailto:{EMAIL}">{ico("mail")}{l["cta_mail"]}</a></div>
</div></section>
<div class="wrap doc">
  <aside class="toc" aria-label="{l["toc"]}"><div><h4>{l["toc"]}</h4>{toc}</div></aside>
  <article class="prose">{secs}{faq}</article>
</div>
<section class="related"><div class="wrap"><h2 class="rv">{l["related"]}</h2><div class="areas rel rv">{rel}</div></div></section>
<section class="cta-band"><div class="wrap rv"><h2>{l["cta_h"]}</h2><p>{l["cta_p"]}</p>
  <div class="actions"><a class="btn solid" href="{WA}" target="_blank" rel="noopener">{ico("wa")}{l["cta_wa"]}</a><a class="btn" href="mailto:{EMAIL}">{ico("mail")}{l["cta_mail"]}</a></div></div></section>
</main>
'''
    return head(lang, t['title'], t['desc'], t['slug'], topic_ld(lang, t)) + header(lang, t['slug']) + main + footer(lang)

def write(rel, s):
    p = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s); print('wrote', rel, len(s))

def sitemap():
    urls = [None] + [t['slug'] for t in TOPICS['fa']]
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for slug in urls:
        for lang in ('fa', 'en'):
            out.append(f'  <url>\n    <loc>{page_url(lang, slug)}</loc>')
            for al in ('fa', 'en'): out.append(f'    <xhtml:link rel="alternate" hreflang="{al}" href="{page_url(al, slug)}"/>')
            out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{page_url("fa", slug)}"/>')
            out.append(f'    <lastmod>{TODAY}</lastmod>\n    <priority>{"1.0" if slug is None else "0.8"}</priority>\n  </url>')
    out.append('</urlset>\n'); return '\n'.join(out)

if __name__ == '__main__':
    write('index.html', build_home('fa')); write('en/index.html', build_home('en'))
    for lang in ('fa', 'en'):
        for t in TOPICS[lang]:
            write(L[lang]['svc'].strip('/') + '/' + t['slug'] + '/index.html', build_topic(lang, t))
    write('sitemap.xml', sitemap())
