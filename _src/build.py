#!/usr/bin/env python3
"""سازندهٔ سایت. همهٔ صفحه‌ها را از روی محتوای _src می‌سازد.

اجرا:   python3 _src/build.py          (نیاز: pip install segno)
تصاویر اشتراک‌گذاری:  python3 _src/og.py   (نیاز: playwright؛ فقط برای صفحه‌های تازه یا تغییرکرده)
"""
import json, os, re, sys, html, hashlib
from datetime import date
from urllib.parse import quote

SRC = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SRC)
sys.path.insert(0, SRC)
from icons import ICONS
import visual, charts, config, topics_fa, topics_en, articles_fa, articles_en, glossary, tools_content, tools_ui
try:
    import deposits, iranmap
except ImportError:
    deposits = iranmap = None

SITE = 'https://alialinaghi72.github.io'
PHONE, PHONE_TXT, EMAIL = '+989135133397', '+98 913 513 3397', 'alialinaghi72@gmail.com'
LINKEDIN, WA_NUM = 'https://www.linkedin.com/in/alialinaghi72', '989135133397'
WA = 'https://wa.me/' + WA_NUM
TODAY = date.today().isoformat()

def _ver(rel): return hashlib.sha1(open(os.path.join(ROOT, rel), 'rb').read()).hexdigest()[:8]
V = {f: _ver(f'assets/{f}') for f in ('site.css', 'site.js', 'charts.js', 'tools.js', 'atlas.js') if os.path.exists(os.path.join(ROOT, 'assets', f))}

L = {
 'fa': dict(dir='rtl', locale='fa_IR', alt_locale='en_US', name='علی علینقی', home='/', other='English', other_lang='en',
   skip='رفتن به محتوا', menu='منو', mainnav='منوی اصلی', home_label='صفحهٔ اصلی',
   n_svc='خدمات', n_art='مقالات', n_atlas='اطلس کانسارها', n_tools='ابزارها', n_gloss='واژه‌نامه', n_contact='تماس',
   foot_tag='مشاورهٔ اکتشاف معدن، مدل‌سازی سه‌بعدی زمین‌شناسی و تخمین ذخیره', areas='حوزه‌های تخصصی', content='محتوا',
   contact='تماس', top='بازگشت به بالا ↑', crumb_home='خانه', crumb_svc='خدمات', toc='در این صفحه', related='موضوعات مرتبط',
   faq='پرسش‌ها', cta_h='پروژه‌ای در دست دارید؟', cta_p='برای بررسی محدوده، بازبینی گزارش یا شروع تخمین ذخیره پیام بدهید. معمولاً ظرف یک روز کاری پاسخ می‌دهم.',
   cta_wa='گفت‌وگو در واتس‌اپ', cta_mail='ارسال ایمیل', more='بیشتر بخوانید', year='۲۰۲۶', rss='خوراک RSS',
   vcard_label='کد QR — ذخیرهٔ مخاطب علی علینقی', by='نوشتهٔ', updated='به‌روزرسانی', minutes='دقیقه مطالعه',
   takeaways='خلاصه', refs='منابع', rel_art='مطالب مرتبط', rel_tools='ابزارهای مرتبط', rel_svc='خدمات مرتبط',
   share='اشتراک‌گذاری', copy='کپی پیوند', copied='پیوند کپی شد', fb_q='این مطلب برایتان مفید بود؟', fb_yes='بله', fb_no='نه چندان',
   fb_thanks='سپاس از بازخورد شما.', fb_more='پیشنهاد یا پرسشی دارید؟ برایم بنویسید',
   author_bio='کارشناس ارشد اکتشاف معدن با بیش از ده سال تجربه در اکتشاف، مدل‌سازی سه‌بعدی و تخمین ذخیرهٔ طلا، مس، مولیبدن، آهن و سرب و روی در ایران، ارمنستان، ونزوئلا و مراکش.',
   about_author='دربارهٔ نویسنده', all_art='همهٔ مقاله‌ها', all_tools='همهٔ ابزارها', open_tool='باز کردن ابزار',
   art_hub_t='مقالات و راهنماهای اکتشاف و تخمین ذخیره | علی علینقی', art_hub_h='مقالات و راهنماها',
   art_hub_d='راهنماهای کاربردی به زبان فارسی دربارهٔ تخمین ذخیره، زمین‌آمار، کریجینگ، واریوگرام، عیار حد، کد JORC، کنترل کیفیت و مراحل اکتشاف معدن.',
   art_hub_l='راهنماهای فنی و کاربردی برای زمین‌شناسان، مهندسان معدن، مدیران پروژه و سرمایه‌گذاران؛ نوشته‌شده از دل کار واقعی تخمین ذخیره و اکتشاف.',
   tools_hub_t='ابزارهای آنلاین معدن: ماشین‌حساب عیار حد، تبدیل واحد و واریوگرام | علی علینقی', tools_hub_h='ابزارهای آنلاین',
   tools_hub_d='ابزارهای رایگان و آنلاین برای زمین‌شناسان و مهندسان معدن: محاسبهٔ عیار حد، محاسبهٔ تناژ و فلز محتوا، تبدیل واحدهای عیار و آزمایشگاه تعاملی واریوگرام.',
   tools_hub_l='ماشین‌حساب‌های سریع برای کارهای روزمرهٔ اکتشاف و تخمین ذخیره. همه در مرورگر شما اجرا می‌شوند و داده‌ای ارسال نمی‌شود.',
   gloss_t='واژه‌نامهٔ اکتشاف و تخمین ذخیره (فارسی–انگلیسی) | علی علینقی', gloss_h='واژه‌نامهٔ اکتشاف و تخمین ذخیره',
   gloss_d='تعریف کوتاه و دقیق اصطلاحات اکتشاف معدن، زمین‌آمار، تخمین ذخیره، کنترل کیفیت و گزارش‌دهی JORC به فارسی و انگلیسی.',
   gloss_l='معادل انگلیسی و تعریف کوتاه اصطلاحاتی که در گزارش‌های اکتشاف و تخمین ذخیره بیشتر به کار می‌روند.',
   gloss_search='جست‌وجوی اصطلاح…', gloss_none='اصطلاحی پیدا نشد.', see='بیشتر', terms='اصطلاح',
   nf_t='صفحه پیدا نشد', nf_p='نشانی‌ای که دنبالش بودید وجود ندارد یا جابه‌جا شده است.',
   illustrative='نمودارها و اعداد این صفحه نمایشی‌اند، مگر آنکه منبع داشته باشند.'),
 'en': dict(dir='ltr', locale='en_US', alt_locale='fa_IR', name='Ali Alinaghi', home='/en/', other='فارسی', other_lang='fa',
   skip='Skip to content', menu='Menu', mainnav='Main', home_label='home',
   n_svc='Services', n_art='Articles', n_atlas='Deposit atlas', n_tools='Tools', n_gloss='Glossary', n_contact='Contact',
   foot_tag='Mineral exploration, 3D geological modelling and resource estimation consulting', areas='Areas of expertise', content='Content',
   contact='Contact', top='Back to top ↑', crumb_home='Home', crumb_svc='Services', toc='On this page', related='Related topics',
   faq='Questions', cta_h='Have a project in mind?', cta_p='Send a message about assessing an area, reviewing a report or starting a resource estimate. I usually reply within one working day.',
   cta_wa='Chat on WhatsApp', cta_mail='Send an email', more='Read more', year='2026', rss='RSS feed',
   vcard_label='QR code — save Ali Alinaghi as a contact', by='By', updated='Updated', minutes='min read',
   takeaways='Key takeaways', refs='References', rel_art='Related articles', rel_tools='Related tools', rel_svc='Related services',
   share='Share', copy='Copy link', copied='Link copied', fb_q='Was this article useful?', fb_yes='Yes', fb_no='Not really',
   fb_thanks='Thank you for the feedback.', fb_more='Have a suggestion or a question? Write to me',
   author_bio='MSc mineral exploration geologist with more than ten years in exploration, 3D modelling and resource estimation of gold, copper, molybdenum, iron and lead–zinc in Iran, Armenia, Venezuela and Morocco.',
   about_author='About the author', all_art='All articles', all_tools='All tools', open_tool='Open the tool',
   art_hub_t='Mineral Exploration and Resource Estimation Articles | Ali Alinaghi', art_hub_h='Articles and guides',
   art_hub_d='Practical guides on resource estimation, geostatistics, kriging, variograms, cut-off grade, the JORC Code, QA/QC and the stages of mineral exploration.',
   art_hub_l='Technical, practical guides for geologists, mining engineers, project managers and investors — written from real resource-estimation and exploration work.',
   tools_hub_t='Free Mining Tools: Cut-off Grade Calculator, Unit Converter, Variogram | Ali Alinaghi', tools_hub_h='Online tools',
   tools_hub_d='Free online tools for geologists and mining engineers: cut-off grade calculator, tonnage and contained-metal calculator, grade unit converter and an interactive variogram lab.',
   tools_hub_l='Quick calculators for everyday exploration and resource-estimation work. Everything runs in your browser; nothing is sent anywhere.',
   gloss_t='Mineral Exploration and Resource Estimation Glossary (English–Persian) | Ali Alinaghi', gloss_h='Exploration and resource estimation glossary',
   gloss_d='Short, precise definitions of mineral exploration, geostatistics, resource estimation, QA/QC and JORC reporting terms, in English and Persian.',
   gloss_l='Persian equivalents and short definitions of the terms used most in exploration and resource-estimation reports.',
   gloss_search='Search terms…', gloss_none='No matching term.', see='More', terms='terms',
   nf_t='Page not found', nf_p='The address you were looking for does not exist or has moved.',
   illustrative='Charts and figures on this page are illustrative unless a source is given.'),
}
SEG = {'svc': 'services', 'art': 'articles', 'atlas': 'atlas', 'gloss': 'glossary', 'tools': 'tools'}

TOPICS = {'fa': topics_fa.TOPICS, 'en': topics_en.TOPICS}
ARTS = {'fa': articles_fa.ARTICLES, 'en': articles_en.ARTICLES}
DEPS = deposits.DEPOSITS if deposits else []
BY = {lang: {'svc': {t['slug']: t for t in TOPICS[lang]}, 'art': {a['slug']: a for a in ARTS[lang]},
             'tools': {t['slug']: dict(t[lang], slug=t['slug'], icon=t['icon']) for t in tools_content.TOOLS}} for lang in L}
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

SVC_LINKS = {
 'resource-estimation': {'art': ['kriging', 'variogram', 'resources-vs-reserves'], 'tools': ['cut-off-grade', 'variogram-lab']},
 '3d-geological-modelling': {'art': ['kriging', 'variogram'], 'tools': ['grade-converter']},
 'mineral-exploration': {'art': ['exploration-stages-iran', 'qaqc']},
 'exploration-geophysics': {'art': ['exploration-stages-iran']},
 'exploration-geochemistry': {'art': ['exploration-stages-iran', 'qaqc']},
 'remote-sensing': {'art': ['exploration-stages-iran']},
 'project-management': {'art': ['exploration-stages-iran', 'qaqc', 'resources-vs-reserves'], 'tools': ['cut-off-grade']},
 'commodities': {'art': ['cut-off-grade', 'resources-vs-reserves'], 'tools': ['cut-off-grade', 'grade-converter']},
}

def ico(name): return ICONS[name]
def esc(s): return html.escape(str(s), quote=True)
def path(lang, kind='home', slug=None):
    base = L[lang]['home']
    if kind == 'home': return base
    return base + SEG[kind] + '/' + (slug + '/' if slug else '')
def url(lang, kind='home', slug=None): return SITE + path(lang, kind, slug)
FA_D = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
def fanum(s, lang): return str(s).translate(FA_D) if lang == 'fa' else str(s)

# ---------- تاریخ (شمسی برای فارسی) ----------
def g2j(gy, gm, gd):
    gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + gdm[gm - 1]
    jy = -1595 + 33 * (days // 12053); days %= 12053
    jy += 4 * (days // 1461); days %= 1461
    if days > 365: jy += (days - 1) // 365; days = (days - 1) % 365
    if days < 186: return jy, 1 + days // 31, 1 + days % 31
    return jy, 7 + (days - 186) // 30, 1 + (days - 186) % 30
JM = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
GM = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
def fdate(iso, lang):
    y, m, d = map(int, iso.split('-'))
    if lang == 'fa':
        jy, jm, jd = g2j(y, m, d); return fanum(f'{jd} {JM[jm - 1]} {jy}', 'fa')
    return f'{d} {GM[m - 1]} {y}'

def words(h): return len(re.sub(r'<[^>]+>', ' ', h).split())
def read_min(a, lang):
    n = words(' '.join(b for _, b in a['sections'])) + words(' '.join(a.get('takeaways', [])))
    return max(2, round(n / (190 if lang == 'fa' else 220)))

# ---------- تصاویر اشتراک‌گذاری ----------
OG = []
def og_image(lang, kind, slug, title, label):
    name = f'{lang}-{kind}-{slug or "index"}.jpg'
    OG.append({'file': name, 'lang': lang, 'title': title, 'label': label})
    return f'/og/{name}' if os.path.exists(os.path.join(ROOT, 'og', name)) else '/og.png'

def analytics():
    out = ''
    if config.GOATCOUNTER_CODE:
        out += f'<script data-goatcounter="https://{config.GOATCOUNTER_CODE}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>\n'
    if config.GA4_ID:
        out += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={config.GA4_ID}"></script>\n'
                f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{config.GA4_ID}');</script>\n")
    return out

def head(lang, kind, slug, title, desc, ld=None, og_type='article', og_label='', extra=''):
    l = L[lang]; u = url(lang, kind, slug)
    img = SITE + og_image(lang, kind, slug, title, og_label)
    ld_tag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>' if ld else ''
    verify = '<meta name="google-site-verification" content="yGlYYZduh8Y1SDMxFbUH2CFhwXWF_r1zAWW8D1_FwbQ">\n' if lang == 'fa' and kind == 'home' else ''
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
<link rel="canonical" href="{u}">
<link rel="alternate" hreflang="fa" href="{url("fa", kind, slug)}">
<link rel="alternate" hreflang="en" href="{url("en", kind, slug)}">
<link rel="alternate" hreflang="x-default" href="{url("fa", kind, slug)}">
<link rel="alternate" type="application/rss+xml" title="{esc(l["name"] + " — " + l["n_art"])}" href="{l["home"]}feed.xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
<link rel="icon" href="/icon-512.png" type="image/png" sizes="512x512">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{l["name"]}">
<meta property="og:locale" content="{l["locale"]}">
<meta property="og:locale:alternate" content="{l["alt_locale"]}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{u}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{img}">
<link rel="preload" href="/fonts/Vazirmatn.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css?v={V["site.css"]}">
<script>document.documentElement.classList.add('js')</script>
{analytics()}{extra}{ld_tag}
</head>
<body>
<a class="skip" href="#main">{l["skip"]}</a>
'''

def header(lang, kind='home', slug=None):
    l = L[lang]; other = l['other_lang']; is_home = kind == 'home'
    items = [('services', l['n_svc'], '#services' if is_home else l['home'] + '#services'),
             ('art', l['n_art'], path(lang, 'art'))]
    if DEPS: items.append(('atlas', l['n_atlas'], path(lang, 'atlas')))
    items += [('tools', l['n_tools'], path(lang, 'tools')), ('contact', l['n_contact'], '#contact' if is_home else l['home'] + '#contact')]
    links = ''.join(f'<a href="{h}"{" aria-current=" + chr(34) + "page" + chr(34) if k == kind else ""}>{t}</a>' for k, t, h in items)
    return f'''<header class="site-header">
  <div class="wrap bar">
    <a class="mark" href="{"#top" if is_home else l["home"]}" aria-label="{l["name"]} — {l["home_label"]}">
      <span class="mono">A.A</span>
      <span>{l["name"]}</span>
    </a>
    <nav aria-label="{l["mainnav"]}">
      <div class="links" id="nav-links">{links}</div>
      <a class="lang" href="{path(other, "home" if kind == "nf" else kind, slug)}" hreflang="{other}" lang="{other}">{l["other"]}</a>
      <button class="menu-btn" id="menu-btn" type="button" aria-label="{l["menu"]}" aria-controls="nav-links" aria-expanded="false"><span></span></button>
    </nav>
  </div>
</header>
'''

def footer(lang, kind='home', scripts=(), slug=None):
    l = L[lang]; other = l['other_lang']
    areas = ''.join(f'<a href="{path(lang, "svc", t["slug"])}">{t["short"]}</a>' for t in TOPICS[lang])
    content = [(path(lang, 'art'), l['n_art'])] + ([(path(lang, 'atlas'), l['n_atlas'])] if DEPS else []) + \
              [(path(lang, 'tools'), l['n_tools']), (path(lang, 'gloss'), l['n_gloss']), (l['home'] + 'feed.xml', l['rss'])]
    content_html = ''.join(f'<a href="{h}">{t}</a>' for h, t in content)
    js = ''.join(f'<script src="/assets/{s}?v={V[s]}" defer></script>\n' for s in ('site.js',) + tuple(scripts))
    return f'''<footer><div class="wrap">
  <div class="foot">
    <div class="brand"><b>{l["name"]}</b><span>{l["foot_tag"]}</span>
      <div class="social"><a href="{LINKEDIN}" target="_blank" rel="noopener" aria-label="LinkedIn">{ico("in")}</a><a href="{WA}" target="_blank" rel="noopener" aria-label="WhatsApp">{ico("wa")}</a><a href="mailto:{EMAIL}" aria-label="Email">{ico("mail")}</a><a href="{l["home"]}feed.xml" aria-label="RSS">{ico("rss")}</a></div></div>
    <nav class="fcol" aria-label="{l["areas"]}"><h4>{l["areas"]}</h4>{areas}</nav>
    <nav class="fcol" aria-label="{l["content"]}"><h4>{l["content"]}</h4>{content_html}<a href="{path(other, kind, slug) if kind != "nf" else path(other)}" hreflang="{other}" lang="{other}">{l["other"]}</a></nav>
    <div class="fcol"><h4>{l["contact"]}</h4><a href="tel:{PHONE}" dir="ltr">{PHONE_TXT}</a><a href="mailto:{EMAIL}">{EMAIL}</a><a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a></div>
  </div>
  <div class="foot-bottom">
    <span>© <span id="year">{l["year"]}</span> {l["name"]}</span>
    <a class="to-top" href="#top">{l["top"]}</a>
  </div>
</div></footer>
{js}</body>
</html>
'''

# ---------- داده‌های ساختاریافته ----------
def person_ld(lang):
    fa = lang == 'fa'
    return {
      "@type": "Person", "@id": SITE + "/#person",
      "name": "علی علینقی" if fa else "Ali Alinaghi",
      "alternateName": ["Ali Alinaghi", "علي علينقي"] if fa else ["علی علینقی"],
      "jobTitle": "کارشناس ارشد اکتشاف معدن" if fa else "MSc Mineral Exploration — resource modelling and estimation specialist",
      "description": L[lang]['author_bio'],
      "url": SITE + L[lang]['home'], "image": SITE + "/og.png", "email": "mailto:" + EMAIL, "telephone": PHONE,
      "sameAs": [LINKEDIN],
      "knowsAbout": (["اکتشاف معدن", "تخمین ذخیره", "مدل‌سازی سه‌بعدی زمین‌شناسی", "مدل بلوکی", "زمین‌آمار", "کریجینگ", "واریوگرام", "عیار حد", "ژئوفیزیک اکتشافی", "ژئوشیمی اکتشافی", "دورسنجی", "سنجش از دور", "مدیریت پروژه اکتشافی", "زمین‌شناسی اقتصادی", "طلا", "مس", "مولیبدن", "آهن", "سرب و روی", "تالک", "زغال‌سنگ", "JORC", "NI 43-101"] if fa else
                     ["Mineral exploration", "Resource estimation", "3D geological modelling", "Block modelling", "Geostatistics", "Kriging", "Variography", "Cut-off grade", "Exploration geophysics", "Exploration geochemistry", "Remote sensing", "Exploration project management", "Economic geology", "Gold", "Copper", "Molybdenum", "Iron ore", "Lead–zinc", "Talc", "Coal", "JORC", "NI 43-101"]),
      "knowsLanguage": ["fa", "en"], "address": {"@type": "PostalAddress", "addressCountry": "IR"}}

def crumbs_ld(lang, trail):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i, "name": n, "item": SITE + h} for i, (n, h) in enumerate(trail, 1)]}

def ld_graph(*nodes): return {"@context": "https://schema.org", "@graph": [n for n in nodes if n]}

def home_ld(lang):
    fa = lang == 'fa'
    faq = re.findall(r'<summary>(.*?)</summary>\s*<p>(.*?)</p>', open(f'{SRC}/home_{lang}.html', encoding='utf-8').read(), re.S)
    return ld_graph(
      person_ld(lang),
      {"@type": "ProfilePage", "@id": url(lang) + "#profile", "url": url(lang), "inLanguage": lang, "mainEntity": {"@id": SITE + "/#person"},
       "dateModified": TODAY, "isPartOf": {"@id": SITE + "/#website"}},
      {"@type": "ProfessionalService", "@id": SITE + "/#service",
       "name": "مشاورهٔ اکتشاف معدن و تخمین ذخیره — علی علینقی" if fa else "Ali Alinaghi — mineral exploration and resource estimation consulting",
       "founder": {"@id": SITE + "/#person"}, "url": url(lang), "image": SITE + "/og.png",
       "telephone": PHONE, "email": "mailto:" + EMAIL, "priceRange": "$$",
       "areaServed": [{"@type": "Country", "name": n} for n in ["Iran", "Armenia", "Morocco", "Venezuela"]],
       "address": {"@type": "PostalAddress", "addressCountry": "IR"},
       "hasOfferCatalog": {"@type": "OfferCatalog", "name": "خدمات" if fa else "Services", "itemListElement": [
          {"@type": "Offer", "itemOffered": {"@type": "Service", "name": t['h1'], "url": url(lang, 'svc', t['slug'])}} for t in TOPICS[lang]]}},
      {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/",
       "name": "علی علینقی — اکتشاف معدن و تخمین ذخیره" if fa else "Ali Alinaghi — mineral exploration and resource estimation",
       "inLanguage": ["fa-IR", "en"], "publisher": {"@id": SITE + "/#person"}},
      {"@type": "FAQPage", "@id": url(lang) + "#faq", "mainEntity": [
          {"@type": "Question", "name": q.strip(), "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a).strip()}} for q, a in faq]})

# ---------- اجزای مشترک ----------
def crumbs_html(trail):
    parts = [f'<a href="{h}">{esc(n)}</a>' for n, h in trail[:-1]] + [f'<span aria-current="page">{esc(trail[-1][0])}</span>']
    return '<nav class="crumbs" aria-label="breadcrumb">' + '<span>/</span>'.join(parts) + '</nav>'

def share_html(lang, u, title):
    l = L[lang]; eu, et = quote(u, safe=''), quote(title, safe='')
    return (f'<div class="share"><span>{l["share"]}</span>'
            f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={eu}" target="_blank" rel="noopener" aria-label="LinkedIn">{ico("in")}</a>'
            f'<a href="https://wa.me/?text={et}%20{eu}" target="_blank" rel="noopener" aria-label="WhatsApp">{ico("wa")}</a>'
            f'<a href="https://t.me/share/url?url={eu}&amp;text={et}" target="_blank" rel="noopener" aria-label="Telegram">{ico("tg")}</a>'
            f'<a href="https://twitter.com/intent/tweet?url={eu}&amp;text={et}" target="_blank" rel="noopener" aria-label="X">{ico("x")}</a>'
            f'<button type="button" class="copy" data-url="{esc(u)}" data-done="{esc(l["copied"])}">{ico("link")}<span>{l["copy"]}</span></button></div>')

def feedback_html(lang, page_id, title):
    l = L[lang]; msg = quote(('دربارهٔ «' + title + '»: ') if lang == 'fa' else ('About "' + title + '": '), safe='')
    return (f'<div class="fb" data-page="{esc(page_id)}"><span class="fb-q">{l["fb_q"]}</span>'
            f'<button type="button" data-v="yes">{ico("thumb")}{l["fb_yes"]}</button><button type="button" data-v="no" class="no">{ico("thumb")}{l["fb_no"]}</button>'
            f'<p class="fb-done" hidden>{l["fb_thanks"]} <a href="{WA}?text={msg}" target="_blank" rel="noopener">{l["fb_more"]}</a></p></div>')

def author_html(lang):
    l = L[lang]
    return (f'<aside class="author"><div class="av" aria-hidden="true">A.A</div><div><span class="ab-k">{l["about_author"]}</span><b>{l["name"]}</b><p>{l["author_bio"]}</p>'
            f'<div class="ab-links"><a href="{l["home"]}">{l["home_label"]}</a><a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a><a href="{l["home"]}#contact">{l["contact"]}</a></div></div></aside>')

def cta_band(lang):
    l = L[lang]
    return (f'<section class="cta-band"><div class="wrap rv"><h2>{l["cta_h"]}</h2><p>{l["cta_p"]}</p>'
            f'<div class="actions"><a class="btn solid" href="{WA}" target="_blank" rel="noopener">{ico("wa")}{l["cta_wa"]}</a><a class="btn" href="mailto:{EMAIL}">{ico("mail")}{l["cta_mail"]}</a></div></div></section>')

def card(href, icon, title, text, more, meta='', i=0, cls=''):
    m = f'<span class="meta">{meta}</span>' if meta else ''
    return (f'<a class="area {cls}" href="{href}" style="--i:{i}"><span class="ico">{ico(icon)}</span>{m}<b>{esc(title)}</b><span>{esc(text)}</span>'
            f'<i class="go">{more} {ico("arrow")}</i></a>')

def art_card(lang, a, i=0):
    meta = f'{esc(a["cat"])} · {fanum(read_min(a, lang), lang)} {L[lang]["minutes"]}'
    return card(path(lang, 'art', a['slug']), a['icon'], a['h1'], a['card'], L[lang]['more'], meta, i, 'art-card')

def tool_card(lang, t, i=0):
    return card(path(lang, 'tools', t['slug']), t['icon'], t['h1'], t['card'], L[lang]['open_tool'], '', i)

def related_html(lang, rel):
    l = L[lang]; out = []
    if rel.get('art'): out.append(('rel_art', [art_card(lang, BY[lang]['art'][s], i) for i, s in enumerate(rel['art'], 1)]))
    if rel.get('tools'): out.append(('rel_tools', [tool_card(lang, BY[lang]['tools'][s], i) for i, s in enumerate(rel['tools'], 1)]))
    if rel.get('svc'): out.append(('rel_svc', [card(path(lang, 'svc', s), BY[lang]['svc'][s]['icon'], BY[lang]['svc'][s]['h1'], CARD[lang][s], l['more'], '', i)
                                               for i, s in enumerate(rel['svc'], 1)]))
    if not out: return ''
    blocks = ''.join(f'<h2 class="rv">{l[k]}</h2><div class="areas rel rv">{"".join(c)}</div>' for k, c in out)
    return f'<section class="related"><div class="wrap">{blocks}</div></section>'

def expand(h, lang):
    h = re.sub(r'\{\{fig:(\w+)\}\}', lambda m: charts.FIGS[m.group(1)](lang), h)
    h = re.sub(r'\{\{ico:(\w+)\}\}', lambda m: ico(m.group(1)), h)
    return h

def doc_body(lang, sections, faq=(), lead='', tail='', refs=(), takeaways=(), mid=''):
    l = L[lang]
    toc = (f'<a href="#takeaways">{l["takeaways"]}</a>' if takeaways else '') + ''.join(f'<a href="#s{n}">{h}</a>' for n, (h, _) in enumerate(sections, 1))
    if faq: toc += f'<a href="#q">{l["faq"]}</a>'
    if refs: toc += f'<a href="#refs">{l["refs"]}</a>'
    tk = (f'<section class="takeaways rv" id="takeaways"><h2>{l["takeaways"]}</h2><ul>' + ''.join(f'<li>{t}</li>' for t in takeaways) + '</ul></section>') if takeaways else ''
    secs = ''.join(f'<section class="prose-sec rv" id="s{n}"><h2>{h}</h2>{expand(b, lang)}</section>' for n, (h, b) in enumerate(sections, 1))
    fq = ''
    if faq:
        fq = f'<section class="prose-sec rv" id="q"><h2>{l["faq"]}</h2><div class="faq">' + ''.join(
            f'<details{" open" if i == 0 else ""}><summary>{q}</summary><p>{a}</p></details>' for i, (q, a) in enumerate(faq)) + '</div></section>'
    rf = (f'<section class="prose-sec refs rv" id="refs"><h2>{l["refs"]}</h2><ol>' + ''.join(f'<li id="r{n}">{r}</li>' for n, r in enumerate(refs, 1)) + '</ol></section>') if refs else ''
    return (f'<div class="wrap doc"><aside class="toc" aria-label="{l["toc"]}"><div><h4>{l["toc"]}</h4>{toc}</div></aside>'
            f'<article class="prose">{lead}{tk}{secs}{mid}{fq}{rf}{tail}</article></div>')

def page_hero(trail, icon, h1, lede, meta='', actions='', tag=''):
    return (f'<section class="page-hero" id="top"><div class="wrap">{crumbs_html(trail)}'
            f'{"<div class=" + chr(34) + "page-ico" + chr(34) + ">" + ico(icon) + "</div>" if icon else ""}{tag}<h1 class="vt-title">{h1}</h1>'
            f'<p class="lede-lg">{lede}</p>{meta}{actions}</div></section>')

def contact_actions(lang):
    l = L[lang]
    return (f'<div class="actions"><a class="btn solid" href="{WA}" target="_blank" rel="noopener">{ico("wa")}{l["cta_wa"]}</a>'
            f'<a class="btn" href="mailto:{EMAIL}">{ico("mail")}{l["cta_mail"]}</a></div>')

def page(lang, kind, slug, title, desc, ld, main, og_type='article', og_label='', scripts=(), extra=''):
    return head(lang, kind, slug, title, desc, ld, og_type, og_label, extra) + header(lang, kind, slug) + f'<main id="main">\n{main}\n</main>\n' + footer(lang, kind, scripts, slug)

# ---------- صفحهٔ اصلی ----------
def latest_html(lang, n=3):
    arts = sorted(ARTS[lang], key=lambda a: a['published'], reverse=True)[:n]
    return '<div class="areas latest rv">' + ''.join(art_card(lang, a, i) for i, a in enumerate(arts, 1)) + '</div>'

def topics_grid(lang):
    return '<div class="areas rv">' + ''.join(card(path(lang, 'svc', t['slug']), t['icon'], t['h1'], CARD[lang][t['slug']], L[lang]['more'], '', n)
                                            for n, t in enumerate(TOPICS[lang], 1)) + '</div>'

def fill(h, lang):
    vcard = f"BEGIN:VCARD\r\nVERSION:3.0\r\nN:Alinaghi;Ali;;;\r\nFN:Ali Alinaghi\r\nTEL;TYPE=CELL:{PHONE}\r\nEMAIL:{EMAIL}\r\nURL:{SITE}/\r\nEND:VCARD\r\n"
    rep = {'{{BM}}': visual.hero_svg(), '{{STORY}}': visual.story_svg(), '{{VARIO}}': visual.variogram_svg(), '{{SWATH}}': visual.swath_svg(),
           '{{QR}}': visual.qr_svg(vcard, L[lang]['vcard_label']), '{{AREAS}}': topics_grid(lang), '{{SVC}}': path(lang, 'svc'),
           '{{LATEST}}': latest_html(lang), '{{ARTS}}': path(lang, 'art'), '{{TOOLS}}': path(lang, 'tools'), '{{GLOSS}}': path(lang, 'gloss'),
           '{{TOOLCARDS}}': '<div class="areas rel rv">' + ''.join(tool_card(lang, dict(t[lang], slug=t['slug'], icon=t['icon']), i)
                                                                 for i, t in enumerate(tools_content.TOOLS, 1)) + '</div>',
           '{{ATLAS}}': atlas_teaser(lang)}
    for k, v in rep.items(): h = h.replace(k, v)
    h = re.sub(r'\{\{ico:(\w+)\}\}', lambda m: ico(m.group(1)), h)
    left = re.findall(r'\{\{.*?\}\}', h)
    assert not left, left
    n = [0]
    def ren(m):
        n[0] += 1; return f'data-n="{fanum(f"{n[0]:02d}", lang)}"'
    return re.sub(r'data-n="[^"]*"', ren, h)

def build_home(lang):
    body = open(f'{SRC}/home_{lang}.html', encoding='utf-8').read()
    meta = re.search(r'<!--\s*title:(.*?)\n\s*desc:(.*?)-->', body, re.S)
    title, desc = meta.group(1).strip(), meta.group(2).strip()
    body = body[meta.end():]
    return head(lang, 'home', None, title, desc, home_ld(lang), 'profile', L[lang]['foot_tag']) + header(lang) + fill(body, lang) + footer(lang, 'home', ('charts.js',))

# ---------- صفحه‌های خدمات ----------
def build_topic(lang, t):
    l = L[lang]; u = url(lang, 'svc', t['slug'])
    trail = [(l['crumb_home'], l['home']), (l['crumb_svc'], l['home'] + '#areas'), (t['short'], path(lang, 'svc', t['slug']))]
    ld = ld_graph(person_ld(lang),
         {"@type": "Service", "@id": u + "#service", "name": t['h1'], "serviceType": t['h1'], "description": t['desc'], "url": u,
          "provider": {"@id": SITE + "/#person"}, "areaServed": ["Iran", "Armenia", "Morocco", "Venezuela"], "inLanguage": lang},
         crumbs_ld(lang, trail),
         {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t['faq']]} if t['faq'] else None)
    rel = dict(SVC_LINKS.get(t['slug'], {}), svc=t['related'])
    main = page_hero(trail, t['icon'], t['h1'], t['lede'], actions=contact_actions(lang)) + doc_body(lang, t['sections'], t['faq'], tail=share_html(lang, u, t['h1'])) \
           + related_html(lang, rel) + cta_band(lang)
    return page(lang, 'svc', t['slug'], t['title'], t['desc'], ld, main, og_label=l['crumb_svc'])

# ---------- مقاله‌ها ----------
def build_article(lang, a):
    l = L[lang]; u = url(lang, 'art', a['slug'])
    trail = [(l['crumb_home'], l['home']), (l['n_art'], path(lang, 'art')), (a['short'], path(lang, 'art', a['slug']))]
    img = SITE + f'/og/{lang}-art-{a["slug"]}.jpg'
    ld = ld_graph(person_ld(lang),
         {"@type": "TechArticle", "@id": u + "#article", "headline": a['h1'], "description": a['desc'], "inLanguage": lang,
          "datePublished": a['published'], "dateModified": a['updated'], "author": {"@id": SITE + "/#person"}, "publisher": {"@id": SITE + "/#person"},
          "mainEntityOfPage": u, "image": img, "articleSection": a['cat'], "keywords": a['keywords'], "wordCount": words(' '.join(b for _, b in a['sections'])),
          "isPartOf": {"@id": SITE + "/#website"}},
         crumbs_ld(lang, trail))
    meta = (f'<div class="art-meta"><span class="av" aria-hidden="true">A.A</span><span>{l["by"]} <a href="{l["home"]}">{l["name"]}</a></span>'
            f'<span><time datetime="{a["published"]}">{fdate(a["published"], lang)}</time></span>'
            + (f'<span>{l["updated"]}: <time datetime="{a["updated"]}">{fdate(a["updated"], lang)}</time></span>' if a['updated'] != a['published'] else '')
            + f'<span>{ico("clock")}{fanum(read_min(a, lang), lang)} {l["minutes"]}</span></div>')
    tag = f'<span class="tag">{esc(a["cat"])}</span>'
    tail = share_html(lang, u, a['h1']) + feedback_html(lang, 'art-' + a['slug'], a['h1']) + author_html(lang)
    main = page_hero(trail, None, a['h1'], a['lede'], meta, tag=tag) + doc_body(lang, a['sections'], a['faq'], tail=tail, refs=a.get('refs', ()), takeaways=a['takeaways']) \
           + related_html(lang, a['related']) + cta_band(lang)
    return page(lang, 'art', a['slug'], a['title'], a['desc'], ld, main, og_label=a['cat'], scripts=('charts.js',))

def build_art_hub(lang):
    l = L[lang]; u = url(lang, 'art')
    trail = [(l['crumb_home'], l['home']), (l['n_art'], path(lang, 'art'))]
    arts = sorted(ARTS[lang], key=lambda a: a['published'], reverse=True)
    ld = ld_graph(person_ld(lang), {"@type": "CollectionPage", "@id": u, "name": l['art_hub_h'], "description": l['art_hub_d'], "inLanguage": lang,
                  "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i, "url": url(lang, 'art', a['slug']), "name": a['h1']}
                                                                       for i, a in enumerate(arts, 1)]}}, crumbs_ld(lang, trail))
    main = page_hero(trail, 'book', l['art_hub_h'], l['art_hub_l']) + \
           f'<section class="hub"><div class="wrap"><div class="areas hub-grid rv">{"".join(art_card(lang, a, i) for i, a in enumerate(arts, 1))}</div>' \
           f'<p class="hub-more rv"><a class="btn" href="{path(lang, "gloss")}">{ico("abc")}{l["n_gloss"]}</a><a class="btn" href="{l["home"]}feed.xml">{ico("rss")}{l["rss"]}</a></p></div></section>' + cta_band(lang)
    return page(lang, 'art', None, l['art_hub_t'], l['art_hub_d'], ld, main, 'website', l['n_art'])

# ---------- ابزارها ----------
def build_tools_hub(lang):
    l = L[lang]; u = url(lang, 'tools')
    trail = [(l['crumb_home'], l['home']), (l['n_tools'], path(lang, 'tools'))]
    tl = [dict(t[lang], slug=t['slug'], icon=t['icon']) for t in tools_content.TOOLS]
    ld = ld_graph(person_ld(lang), {"@type": "CollectionPage", "@id": u, "name": l['tools_hub_h'], "description": l['tools_hub_d'], "inLanguage": lang,
                  "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i, "url": url(lang, 'tools', t['slug']), "name": t['h1']}
                                                                       for i, t in enumerate(tl, 1)]}}, crumbs_ld(lang, trail))
    main = page_hero(trail, 'calc', l['tools_hub_h'], l['tools_hub_l']) + \
           f'<section class="hub"><div class="wrap"><div class="areas rel hub-grid rv">{"".join(tool_card(lang, t, i) for i, t in enumerate(tl, 1))}</div></div></section>' + cta_band(lang)
    return page(lang, 'tools', None, l['tools_hub_t'], l['tools_hub_d'], ld, main, 'website', l['n_tools'])

def build_tool(lang, t):
    l = L[lang]; c = t[lang]; u = url(lang, 'tools', t['slug'])
    trail = [(l['crumb_home'], l['home']), (l['n_tools'], path(lang, 'tools')), (c['short'], path(lang, 'tools', t['slug']))]
    ld = ld_graph(person_ld(lang),
         {"@type": "WebApplication", "@id": u + "#app", "name": c['h1'], "description": c['desc'], "url": u, "inLanguage": lang,
          "applicationCategory": "EducationalApplication", "operatingSystem": "Any", "browserRequirements": "Requires JavaScript",
          "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "author": {"@id": SITE + "/#person"}},
         crumbs_ld(lang, trail))
    ui = tools_ui.UI[t['slug']](lang)
    tail = share_html(lang, u, c['h1']) + feedback_html(lang, 'tool-' + t['slug'], c['h1']) + author_html(lang)
    main = page_hero(trail, t['icon'], c['h1'], c['lede']) + f'<section class="tool-sec"><div class="wrap">{ui}</div></section>' + \
           doc_body(lang, c['sections'], c['faq'], tail=tail) + related_html(lang, c['related']) + cta_band(lang)
    return page(lang, 'tools', t['slug'], c['title'], c['desc'], ld, main, og_label=l['n_tools'], scripts=('charts.js', 'tools.js'))

# ---------- واژه‌نامه ----------
def build_glossary(lang):
    l = L[lang]; u = url(lang, 'gloss'); fa = lang == 'fa'
    trail = [(l['crumb_home'], l['home']), (l['n_gloss'], path(lang, 'gloss'))]
    terms = sorted(glossary.TERMS, key=lambda t: glossary.sort_key(t, lang))
    groups = {}
    for t in terms: groups.setdefault(glossary.initial(t, lang), []).append(t)
    idx = ''.join(f'<a href="#g-{i}">{esc(k)}</a>' for i, k in enumerate(groups))
    body = []
    for i, (k, ts) in enumerate(groups.items()):
        items = []
        for t in ts:
            name, other, d = (t['fa'], t['en'], t['dfa']) if fa else (t['en'], t['fa'], t['den'])
            link = f' <a class="see" href="{path(lang, *t["link"])}">{l["see"]} →</a>' if t.get('link') else ''
            items.append(f'<div class="term" id="{t["id"]}" data-s="{esc((t["fa"] + " " + t["en"]).lower())}"><dt><b>{esc(name)}</b>'
                         f'<span lang="{"en" if fa else "fa"}" dir="{"ltr" if fa else "rtl"}">{esc(other)}</span></dt><dd>{d}{link}</dd></div>')
        body.append(f'<section class="g-group" id="g-{i}"><h2>{esc(k)}</h2><dl>{"".join(items)}</dl></section>')
    ld = ld_graph(person_ld(lang),
         {"@type": "DefinedTermSet", "@id": u + "#terms", "name": l['gloss_h'], "description": l['gloss_d'], "inLanguage": lang, "url": u,
          "hasDefinedTerm": [{"@type": "DefinedTerm", "@id": u + "#" + t['id'], "name": t['fa'] if fa else t['en'],
                              "alternateName": t['en'] if fa else t['fa'], "description": re.sub('<[^>]+>', '', t['dfa'] if fa else t['den']),
                              "inDefinedTermSet": u + "#terms"} for t in terms]},
         crumbs_ld(lang, trail))
    count = f'<p class="g-count">{fanum(len(terms), lang)} {l["terms"]}</p>'
    main = page_hero(trail, 'abc', l['gloss_h'], l['gloss_l'], count) + \
           (f'<section class="gloss"><div class="wrap"><div class="g-tools rv"><label class="g-search">{ico("search")}<input type="search" id="g-q" placeholder="{l["gloss_search"]}" '
            f'aria-label="{l["gloss_search"]}"></label><nav class="g-idx" aria-label="index">{idx}</nav></div><p class="g-none" hidden>{l["gloss_none"]}</p>'
            f'{"".join(body)}{share_html(lang, u, l["gloss_h"])}</div></section>') + cta_band(lang)
    return page(lang, 'gloss', None, l['gloss_t'], l['gloss_d'], ld, main, 'website', l['n_gloss'])

# ---------- اطلس کانسارها ----------
def atlas_teaser(lang):
    if not DEPS: return ''
    return iranmap.teaser(lang, DEPS, path(lang, 'atlas'))

def build_atlas(lang):
    return iranmap.build_hub(sys.modules[__name__], lang, DEPS)

def build_deposit(lang, d):
    return iranmap.build_deposit(sys.modules[__name__], lang, d, DEPS)

# ---------- ۴۰۴ ----------
def build_404():
    lang = 'fa'; l = L[lang]; e = L['en']
    main = (f'<section class="page-hero nf" id="top"><div class="wrap"><p class="nf-code">404</p><h1>{l["nf_t"]}</h1><p class="lede-lg">{l["nf_p"]}</p>'
            f'<div class="actions"><a class="btn solid" href="/">{l["home_label"]}</a><a class="btn" href="{path("fa", "art")}">{l["n_art"]}</a><a class="btn" href="{path("fa", "tools")}">{l["n_tools"]}</a></div>'
            f'<div class="nf-en" lang="en" dir="ltr"><h2>{e["nf_t"]}</h2><p>{e["nf_p"]}</p><a href="/en/">Go to the English home page →</a></div></div></section>')
    h = head(lang, 'home', None, f'{l["nf_t"]} | {l["name"]}', l['nf_p']).replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">', '<meta name="robots" content="noindex">')
    OG.pop()
    return h + header(lang, 'nf') + f'<main id="main">{main}</main>' + footer(lang, 'nf')

# ---------- خوراک و نقشهٔ سایت ----------
def rss(lang):
    l = L[lang]; items = sorted(ARTS[lang], key=lambda a: a['published'], reverse=True)
    def rfc(iso):
        y, m, d = map(int, iso.split('-')); return date(y, m, d).strftime('%a, %d %b %Y 08:00:00 +0330')
    it = ''.join(f'<item><title>{esc(a["h1"])}</title><link>{url(lang, "art", a["slug"])}</link><guid>{url(lang, "art", a["slug"])}</guid>'
                 f'<pubDate>{rfc(a["published"])}</pubDate><description>{esc(a["desc"])}</description></item>' for a in items)
    for d in DEPS:
        c = d[lang]
        it += (f'<item><title>{esc(c["h1"])}</title><link>{url(lang, "atlas", d["slug"])}</link><guid>{url(lang, "atlas", d["slug"])}</guid>'
               f'<pubDate>{rfc(d["published"])}</pubDate><description>{esc(c["desc"])}</description></item>')
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
            f'<title>{esc(l["name"] + " — " + l["n_art"])}</title><link>{url(lang)}</link><description>{esc(l["art_hub_d"])}</description>'
            f'<language>{lang}</language><atom:link href="{SITE}{l["home"]}feed.xml" rel="self" type="application/rss+xml"/>{it}</channel></rss>\n')

PAGES = []   # (kind, slug)
# lastmod هر صفحه فقط وقتی تغییر می‌کند که محتوای <main> آن تغییر کند (گوگل lastmod نادرست را نادیده می‌گیرد)
LASTMOD_F = os.path.join(SRC, 'lastmod.json')
LASTMOD = json.load(open(LASTMOD_F)) if os.path.exists(LASTMOD_F) else {}
def touch(rel, s):
    m = re.search(r'<main[^>]*>(.*)</main>', s, re.S)
    h = hashlib.sha1(re.sub(r'\?v=[0-9a-f]{8}', '', m.group(1) if m else s).encode()).hexdigest()[:12]
    if LASTMOD.get(rel, [None])[0] != h: LASTMOD[rel] = [h, TODAY]
def sitemap():
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for kind, slug in PAGES:
        for lang in ('fa', 'en'):
            lastmod = LASTMOD.get(out_path(lang, kind, slug), [None, TODAY])[1]
            out.append(f'  <url>\n    <loc>{url(lang, kind, slug)}</loc>')
            for al in ('fa', 'en'): out.append(f'    <xhtml:link rel="alternate" hreflang="{al}" href="{url(al, kind, slug)}"/>')
            out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{url("fa", kind, slug)}"/>')
            out.append(f'    <lastmod>{lastmod}</lastmod>\n  </url>')
    out.append('</urlset>\n'); return '\n'.join(out)

def write(rel, s):
    p = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(p) or ROOT, exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s); print('wrote', rel, len(s))
    if rel.endswith('.html'): touch(rel, s)

def out_path(lang, kind, slug=None): return path(lang, kind, slug).lstrip('/') + 'index.html'

if __name__ == '__main__':
    for lang in ('fa', 'en'):
        write(out_path(lang, 'home'), build_home(lang))
        for t in TOPICS[lang]: write(out_path(lang, 'svc', t['slug']), build_topic(lang, t))
        for a in ARTS[lang]: write(out_path(lang, 'art', a['slug']), build_article(lang, a))
        write(out_path(lang, 'art'), build_art_hub(lang))
        write(out_path(lang, 'tools'), build_tools_hub(lang))
        for t in tools_content.TOOLS: write(out_path(lang, 'tools', t['slug']), build_tool(lang, t))
        write(out_path(lang, 'gloss'), build_glossary(lang))
        if DEPS:
            write(out_path(lang, 'atlas'), build_atlas(lang))
            for d in DEPS: write(out_path(lang, 'atlas', d['slug']), build_deposit(lang, d))
        write(('' if lang == 'fa' else 'en/') + 'feed.xml', rss(lang))
    write('404.html', build_404())
    if DEPS: write('atlas/iran-deposits.csv', iranmap.csv_text(sys.modules[__name__], DEPS))
    PAGES += [('home', None)] + [('svc', t['slug']) for t in TOPICS['fa']] + [('art', None)] + [('art', a['slug']) for a in ARTS['fa']] + \
             [('tools', None)] + [('tools', t['slug']) for t in tools_content.TOOLS] + [('gloss', None)]
    if DEPS: PAGES += [('atlas', None)] + [('atlas', d['slug']) for d in DEPS]
    write('sitemap.xml', sitemap())
    json.dump(OG, open(os.path.join(SRC, 'og_manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    open(LASTMOD_F, 'w', encoding='utf-8').write('{\n' + ',\n'.join(f'{json.dumps(k)}: {json.dumps(v)}' for k, v in sorted(LASTMOD.items())) + '\n}\n')
    print('pages:', len(PAGES) * 2, 'og images listed:', len(OG))
