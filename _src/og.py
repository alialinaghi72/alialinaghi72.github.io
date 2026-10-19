#!/usr/bin/env python3
"""تصویرهای اشتراک‌گذاری (۱۲۰۰×۶۳۰) برای هر صفحه. فقط تصویرهای تازه یا تغییرکرده دوباره ساخته می‌شوند.

اجرا (پس از build.py):  python3 _src/og.py   سپس دوباره  python3 _src/build.py
نیاز: playwright با Chromium
"""
import hashlib, html, json, os, sys, tempfile
SRC = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SRC)
sys.path.insert(0, SRC)
import visual

MAN = os.path.join(SRC, 'og_manifest.json'); HASHES = os.path.join(SRC, 'og_hashes.json')
OUT = os.path.join(ROOT, 'og')
FONT = 'file://' + os.path.join(ROOT, 'fonts', 'Vazirmatn.woff2')
CHROME = os.environ.get('CHROME', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')

def page_html(e):
    fa = e['lang'] == 'fa'
    title = e['title'].split(' | ')[0]
    name, site = ('علی علینقی', 'alialinaghi72.github.io') if fa else ('Ali Alinaghi', 'alialinaghi72.github.io')
    role = 'اکتشاف معدن · مدل‌سازی سه‌بعدی · تخمین ذخیره' if fa else 'Mineral exploration · 3D modelling · Resource estimation'
    size = 64 if len(title) < 34 else 56 if len(title) < 52 else 48
    return f'''<!doctype html><html lang="{e["lang"]}" dir="{"rtl" if fa else "ltr"}"><head><meta charset="utf-8"><style>
@font-face{{font-family:V;src:url("{FONT}") format("woff2");font-weight:100 900}}
*{{box-sizing:border-box;margin:0}}
body{{width:1200px;height:630px;overflow:hidden;background:#0B0E10;color:#E9E5DF;font-family:V,sans-serif;position:relative}}
.g{{position:absolute;inset:0;background:radial-gradient(700px 420px at {"85%" if not fa else "15%"} 20%,rgba(192,122,69,.18),transparent 70%),
  linear-gradient(#1A2226 1px,transparent 1px) 0 0/48px 48px,linear-gradient(90deg,#1A2226 1px,transparent 1px) 0 0/48px 48px;opacity:.9}}
.f{{position:absolute;inset:28px;border:1px solid #222C31}}
.c{{position:absolute;top:84px;{"right" if fa else "left"}:84px;width:700px}}
.lab{{display:inline-flex;align-items:center;gap:12px;color:#E2A96B;font-size:26px;font-weight:500;margin-bottom:26px}}
.lab:before{{content:"";width:46px;height:2px;background:#C07A45}}
h1{{font-size:{size}px;font-weight:700;line-height:1.3;letter-spacing:-.01em}}
.ft{{position:absolute;bottom:72px;{"right" if fa else "left"}:84px;display:flex;align-items:center;gap:18px}}
.mono{{width:58px;height:58px;border:2px solid #C07A45;color:#E2A96B;display:grid;place-items:center;font-size:20px;font-weight:600;direction:ltr}}
.ft b{{display:block;font-size:28px;font-weight:600}}
.ft span{{display:block;font-size:20px;color:#98A2A6;margin-top:2px}}
.url{{position:absolute;bottom:42px;{"left" if fa else "right"}:84px;font-size:20px;color:#C07A45;direction:ltr}}
.art{{position:absolute;{"left" if fa else "right"}:50px;top:110px;width:380px;opacity:.95}}
.art svg{{width:100%;height:auto}}
.bm-grid line{{stroke:#2A363C;stroke-width:.6}} .bm-dh line{{stroke:#5E9C8B;stroke-width:1.1;stroke-dasharray:3 2.5}} .bm-dh circle{{fill:#5E9C8B}}
</style></head><body><div class="g"></div><div class="f"></div>
<div class="art">{visual.hero_svg()}</div>
<div class="c"><div class="lab">{html.escape(e["label"])}</div><h1>{html.escape(title)}</h1></div>
<div class="ft"><div class="mono">A.A</div><div><b>{name}</b><span>{role}</span></div></div>
<div class="url">{site}</div></body></html>'''

def main():
    from playwright.sync_api import sync_playwright
    man = json.load(open(MAN, encoding='utf-8'))
    old = json.load(open(HASHES)) if os.path.exists(HASHES) else {}
    os.makedirs(OUT, exist_ok=True)
    todo = []
    for e in man:
        h = hashlib.sha1(json.dumps(e, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
        if old.get(e['file']) != h or not os.path.exists(os.path.join(OUT, e['file'])): todo.append((e, h))
    print('og images to render:', len(todo))
    if not todo: return
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None)
        pg = b.new_page(viewport={'width': 1200, 'height': 630})
        for e, h in todo:
            f = os.path.join(tmp, 'og.html'); open(f, 'w', encoding='utf-8').write(page_html(e))
            pg.goto('file://' + f); pg.wait_for_timeout(120)
            pg.screenshot(path=os.path.join(OUT, e['file']), type='jpeg', quality=84)
            old[e['file']] = h
        b.close()
    keep = {e['file'] for e in man}
    for fn in os.listdir(OUT):
        if fn not in keep: os.remove(os.path.join(OUT, fn))
    json.dump({k: v for k, v in old.items() if k in keep}, open(HASHES, 'w'), indent=0)

if __name__ == '__main__':
    main()
