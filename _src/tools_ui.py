# رابط کاربری ابزارها؛ منطق محاسبه در assets/tools.js
import json, math, random, html
from charts import S1, S2, legend

def esc(s): return html.escape(str(s), quote=True)
def J(o): return esc(json.dumps(o, ensure_ascii=False, separators=(',', ':')))

def field(label, name, unit='', value='', extra='', cls=''):
    u = f'<span class="u">{unit}</span>' if unit and not unit.startswith('<') else unit
    return (f'<label class="{cls}"><span class="lb">{label}</span><span class="in-unit"><input name="{name}" type="number" inputmode="decimal" step="any" '
            f'value="{value}" {extra}>{u}</span></label>')

def chart_shell(cap, capd, leg, table_label):
    return (f'<figure class="chart tool-chart" data-hover="" tabindex="0"><figcaption><b>{esc(cap)}</b><span>{esc(capd)}</span></figcaption>{leg}'
            f'<div class="chart-box"></div><details class="tbl"><summary>{esc(table_label)}</summary><div class="tbl-scroll"><table></table></div></details></figure>')

PRESETS = {
 'cu': dict(unit='pct', price=9000, pu='t', sell=1000, rec=88, pay=96.5, mine=2.5, proc=12, ga=2),
 'au': dict(unit='gpt', price=2000, pu='oz', sell=5, rec=90, pay=99.5, mine=3, proc=18, ga=4),
 'ag': dict(unit='gpt', price=25, pu='oz', sell=0.5, rec=80, pay=95, mine=3, proc=15, ga=3),
 'zn': dict(unit='pct', price=2600, pu='t', sell=450, rec=85, pay=85, mine=3, proc=18, ga=4),
 'pb': dict(unit='pct', price=2100, pu='t', sell=350, rec=85, pay=95, mine=3, proc=18, ga=4),
 'mo': dict(unit='pct', price=20, pu='lb', sell=2, rec=80, pay=98, mine=2.5, proc=12, ga=2),
}
METALS = {'fa': [('cu', 'مس'), ('au', 'طلا'), ('ag', 'نقره'), ('zn', 'روی'), ('pb', 'سرب'), ('mo', 'مولیبدن')],
          'en': [('cu', 'Copper'), ('au', 'Gold'), ('ag', 'Silver'), ('zn', 'Zinc'), ('pb', 'Lead'), ('mo', 'Molybdenum')]}
PU = '<select name="pu" aria-label="unit"><option value="t">$/t</option><option value="lb">$/lb</option><option value="oz">$/oz</option></select>'

def cutoff(lang):
    fa = lang == 'fa'; p = PRESETS['cu']
    opts = ''.join(f'<option value="{k}">{n}</option>' for k, n in METALS[lang])
    form = (f'<form class="tool-form" autocomplete="off" onsubmit="return false">'
            f'<fieldset><legend>{"فلز و قیمت" if fa else "Metal and price"}</legend>'
            f'<label class="full"><span class="lb">{"ماده معدنی" if fa else "Commodity"}</span><select name="metal">{opts}</select></label>'
            + field('قیمت' if fa else 'Price', 'price', PU, p['price'], 'min="0"')
            + field('هزینهٔ فروش (TC/RC، حمل)' if fa else 'Selling cost (TC/RC, freight)', 'sell', '<span class="u" data-pu>$/t</span>', p['sell'], 'min="0"')
            + f'</fieldset><fieldset><legend>{"بازیابی و پرداخت" if fa else "Recovery and payability"}</legend>'
            + field('بازیابی متالورژیکی' if fa else 'Metallurgical recovery', 'rec', '%', p['rec'], 'min="0" max="100"')
            + field('درصد قابل پرداخت' if fa else 'Payable', 'pay', '%', p['pay'], 'min="0" max="100"')
            + f'</fieldset><fieldset><legend>{"هزینه‌ها (دلار بر تن کانسنگ)" if fa else "Costs ($ per tonne of ore)"}</legend>'
            + field('استخراج' if fa else 'Mining', 'mine', '$/t', p['mine'], 'min="0"')
            + field('فرآوری' if fa else 'Processing', 'proc', '$/t', p['proc'], 'min="0"')
            + field('عمومی و اداری' if fa else 'G&amp;A', 'ga', '$/t', p['ga'], 'min="0"', 'full')
            + f'</fieldset><p class="tool-note">{"مقادیر پیش‌فرض نمایشی‌اند؛ اعداد پروژهٔ خود را وارد کنید." if fa else "Default values are illustrative; enter your own project numbers."}</p></form>')
    out = (f'<div class="tool-out" aria-live="polite"><div class="kpis">'
           f'<div class="kpi main"><span>{"عیار حد سربه‌سر" if fa else "Break-even cut-off"}</span><b data-o="be">—</b><small>{"شامل هزینهٔ استخراج" if fa else "includes mining cost"}</small></div>'
           f'<div class="kpi"><span>{"عیار حد حاشیه‌ای" if fa else "Marginal cut-off"}</span><b data-o="mg">—</b><small>{"بدون هزینهٔ استخراج" if fa else "excludes mining cost"}</small></div>'
           f'<div class="kpi"><span>{"درآمد خالص هر واحد عیار" if fa else "Net value per grade unit"}</span><b data-o="nv">—</b><small data-o="nvu"></small></div></div>'
           + chart_shell('حساسیت عیار حد به قیمت' if fa else 'Cut-off grade sensitivity to price',
                         'قیمت از ۶۰ تا ۱۴۰ درصد مقدار واردشده' if fa else 'Price from 60% to 140% of the value entered',
                         legend([('عیار حد سربه‌سر' if fa else 'Break-even', S1, 'line'), ('عیار حد حاشیه‌ای' if fa else 'Marginal', S2, 'line')]),
                         'نمایش داده‌های نمودار' if fa else 'Show chart data') + '</div>')
    return f'<div class="tool" data-tool="cog" data-presets="{J(PRESETS)}"><div class="tool-grid">{form}{out}</div></div>'

def converter(lang):
    fa = lang == 'fa'
    gu = '<select name="gu" aria-label="unit"><option value="pct">%</option><option value="ppm">ppm</option><option value="gpt">g/t</option><option value="ppb">ppb</option><option value="ozst">oz/st</option></select>'
    form = (f'<form class="tool-form" autocomplete="off" onsubmit="return false">'
            f'<fieldset><legend>{"تناژ" if fa else "Tonnage"}</legend>'
            + field('حجم' if fa else 'Volume', 'vol', 'm³', 1000000, 'min="0"')
            + field('چگالی توده‌ای' if fa else 'Bulk density', 'dens', 't/m³', 2.7, 'min="0"')
            + field('یا تناژ مستقیم (اختیاری)' if fa else 'Or tonnage directly (optional)', 'ton', 't', '', 'min="0"', 'full')
            + f'</fieldset><fieldset><legend>{"عیار" if fa else "Grade"}</legend>'
            + field('عیار' if fa else 'Grade', 'grade', gu, 0.5, 'min="0"', 'full')
            + f'</fieldset><fieldset><legend>{"ارزش برجا (اختیاری)" if fa else "In-situ value (optional)"}</legend>'
            + field('قیمت فلز' if fa else 'Metal price', 'price', PU, '', 'min="0"', 'full')
            + '</fieldset></form>')
    out = (f'<div class="tool-out" aria-live="polite"><div class="kpis">'
           f'<div class="kpi main"><span>{"تناژ" if fa else "Tonnage"}</span><b data-o="t">—</b></div>'
           f'<div class="kpi main"><span>{"فلز محتوا" if fa else "Contained metal"}</span><b data-o="m">—</b><small data-o="m2"></small></div>'
           f'<div class="kpi"><span>{"ارزش برجا" if fa else "In-situ value"}</span><b data-o="v">—</b><small>{"ارزش برجا ارزش اقتصادی نیست" if fa else "in-situ value is not economic value"}</small></div></div>'
           f'<div class="tbl-scroll"><table class="dtable conv"><thead><tr><th>{"واحد" if fa else "Unit"}</th><th>{"عیار معادل" if fa else "Equivalent grade"}</th></tr></thead><tbody data-o="tbl"></tbody></table></div>'
           f'<p class="tool-note">{"فلز محتوا مقدار برجاست و بازیابی استخراج و فرآوری در آن لحاظ نشده است." if fa else "Contained metal is in situ and excludes mining and processing recovery."}</p></div>')
    return f'<div class="tool" data-tool="conv"><div class="tool-grid">{form}{out}</div></div>'

def _model(kind, h, c0, c1, a):
    if h <= 0: return 0.0
    if kind == 'sph': return c0 + c1 * (1.5 * h / a - .5 * (h / a) ** 3) if h < a else c0 + c1
    if kind == 'exp': return c0 + c1 * (1 - math.exp(-3 * h / a))
    return c0 + c1 * (1 - math.exp(-3 * h * h / (a * a)))

def vlab_sets():
    out = []
    for sid, fa_n, en_n, kind, c0, c1, a, step, n, seed, start in (
            ('au', 'طلای رگه‌ای — اثر قطعه‌ای بالا', 'Vein gold — high nugget', 'sph', .55, .45, 28, 5, 20, 4, dict(model='sph', c0=.2, c1=.6, a=60)),
            ('cu', 'مس پورفیری — پیوستگی خوب', 'Porphyry copper — good continuity', 'sph', .15, .85, 180, 20, 20, 9, dict(model='sph', c0=.4, c1=.4, a=100)),
            ('fe', 'آهن — پیوستگی بسیار زیاد', 'Iron — very high continuity', 'exp', .05, .95, 320, 25, 18, 12, dict(model='sph', c0=.3, c1=.5, a=120))):
        random.seed(seed); lags = [step * (i + 1) for i in range(n)]
        pairs = [int(40 + 260 * math.sin(math.pi * (i + 1) / (n + 3))) for i in range(n)]
        gam = [round(max(0.0, _model(kind, h, c0, c1, a) + random.gauss(0, .045) * (90 / pr) ** .5), 4) for h, pr in zip(lags, pairs)]
        out.append(dict(id=sid, fa=fa_n, en=en_n, lags=lags, gam=gam, pairs=pairs, start=start))
    return out

def vlab(lang):
    fa = lang == 'fa'; sets = vlab_sets()
    opts = ''.join(f'<option value="{s["id"]}">{esc(s[lang])}</option>' for s in sets)
    def rng(label, name, mn, mx, st, unit=''):
        return (f'<label class="full range"><span class="lb">{label} <output data-o="{name}"></output>{unit}</span>'
                f'<input type="range" name="{name}" min="{mn}" max="{mx}" step="{st}"></label>')
    form = (f'<form class="tool-form" autocomplete="off" onsubmit="return false">'
            f'<fieldset><legend>{"داده" if fa else "Data"}</legend><label class="full"><span class="lb">{"مجموعه‌داده" if fa else "Dataset"}</span><select name="set">{opts}</select></label></fieldset>'
            f'<fieldset><legend>{"مدل" if fa else "Model"}</legend>'
            f'<label class="full"><span class="lb">{"نوع مدل" if fa else "Model type"}</span><select name="model"><option value="sph">{"کروی" if fa else "Spherical"}</option>'
            f'<option value="exp">{"نمایی" if fa else "Exponential"}</option><option value="gau">{"گاوسی" if fa else "Gaussian"}</option></select></label>'
            + rng('اثر قطعه‌ای C₀' if fa else 'Nugget C₀', 'c0', 0, 1.2, .01)
            + rng('سقف جزئی C₁' if fa else 'Partial sill C₁', 'c1', 0, 1.5, .01)
            + rng('دامنه a' if fa else 'Range a', 'a', 5, 500, 1, ' ' + ('متر' if fa else 'm'))
            + f'<div class="btns"><button type="button" class="btn solid" data-act="fit">{"برازش خودکار" if fa else "Auto-fit"}</button>'
            f'<button type="button" class="btn" data-act="reset">{"بازنشانی" if fa else "Reset"}</button></div></fieldset></form>')
    out = (f'<div class="tool-out" aria-live="polite"><div class="kpis">'
           f'<div class="kpi main"><span>{"خطای برازش" if fa else "Fit error"}</span><b data-o="err">—</b><small>{"وزن‌دهی‌شده با تعداد جفت" if fa else "weighted by pairs"}</small></div>'
           f'<div class="kpi"><span>{"نسبت اثر قطعه‌ای به سقف" if fa else "Nugget-to-sill ratio"}</span><b data-o="ratio">—</b><small data-o="cls"></small></div>'
           f'<div class="kpi"><span>{"سقف کل" if fa else "Total sill"}</span><b data-o="sill">—</b></div></div>'
           + chart_shell('واریوگرام تجربی و مدل' if fa else 'Experimental variogram and model', '', legend([('واریوگرام تجربی' if fa else 'Experimental', S2, 'dot'), ('مدل' if fa else 'Model', S1, 'line')]),
                         'نمایش داده‌های نمودار' if fa else 'Show chart data')
           + '<p class="tool-note" data-o="interp"></p></div>')
    return f'<div class="tool" data-tool="vlab" data-sets="{J(sets)}"><div class="tool-grid">{form}{out}</div></div>'

UI = {'cut-off-grade': cutoff, 'grade-converter': converter, 'variogram-lab': vlab}
