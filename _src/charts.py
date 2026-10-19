# نمودارهای مقاله‌ها (SVG درون‌خطی + جدول داده + لایهٔ هاور)
# رنگ‌ها با validate_palette.js روی سطح تیرهٔ #111619 بررسی شده‌اند: S1 و S2 هر شش آزمون را می‌گذرانند.
import html, json, math, random, re

SURF, GRID, AXIS, MUTED, INK, INK2 = '#111619', '#222C31', '#3A464C', '#8A9599', '#E9E5DF', '#98A2A6'
S1, S2 = '#C07A45', '#34A38C'          # سری ۱ (مسی) و سری ۲ (پتینه)
WARN, CRIT = '#fab219', '#d03b3b'      # فقط برای وضعیت (هشدار / خطا)، همیشه با نماد و برچسب

FA_DIGITS = str.maketrans('0123456789.-', '۰۱۲۳۴۵۶۷۸۹٫−')

def num(v, lang, dec=0, pct=False):
    s = f'{v:,.{dec}f}' if abs(v) >= 1000 else f'{v:.{dec}f}'
    if lang == 'fa':
        s = s.replace(',', '٬').translate(FA_DIGITS)
    return s + ('٪' if pct and lang == 'fa' else '%' if pct else '')

def esc(s): return html.escape(str(s), quote=True)

PERSIAN = re.compile('[\u0600-\u06FF]')
def txt(x, y, s, lang, anchor='start', size=12, fill=INK2, extra=''):
    """متن SVG؛ برای برچسب‌های فارسی جهت راست‌به‌چپ و جابه‌جایی start/end تا جای دیداری ثابت بماند."""
    d = ''
    if lang == 'fa' and PERSIAN.search(str(s)):
        d = ' direction="rtl"'; anchor = {'start': 'end', 'end': 'start'}.get(anchor, anchor)
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{fill}" font-size="{size}"{d}{extra}>{esc(s)}</text>'

def nice_ticks(lo, hi, n=5):
    span = hi - lo; raw = span / n; mag = 10 ** math.floor(math.log10(raw)); step = mag
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag: step = m * mag; break
    t0 = math.ceil(lo / step - 1e-9) * step
    out = []; v = t0
    while v <= hi + 1e-9: out.append(round(v, 10)); v += step
    return out, step

def _dec(step):
    d = max(0, -math.floor(math.log10(step) + 1e-9))
    return d if abs(step * 10 ** d - round(step * 10 ** d)) < 1e-9 else d + 1

class Plot:
    def __init__(s, w, h, xlim, ylim, ml=58, mr=18, mt=18, mb=48):
        s.w, s.h, s.xlim, s.ylim = w, h, xlim, ylim
        s.x0, s.x1, s.y0, s.y1 = ml, w - mr, mt, h - mb
    def X(s, v): return s.x0 + (v - s.xlim[0]) / (s.xlim[1] - s.xlim[0]) * (s.x1 - s.x0)
    def Y(s, v): return s.y1 - (v - s.ylim[0]) / (s.ylim[1] - s.ylim[0]) * (s.y1 - s.y0)

def axes(p, lang, xlabel, ylabel, xt=None, yt=None, xfmt=None, yfmt=None):
    xt = xt or nice_ticks(*p.xlim); yt = yt or nice_ticks(*p.ylim)
    xd, yd = _dec(xt[1]), _dec(yt[1])
    xfmt = xfmt or (lambda v: num(v, lang, xd)); yfmt = yfmt or (lambda v: num(v, lang, yd))
    g = [f'<g class="grid" stroke="{GRID}" stroke-width="1">']
    g += [f'<line x1="{p.x0}" x2="{p.x1}" y1="{p.Y(v):.1f}" y2="{p.Y(v):.1f}"/>' for v in yt[0] if p.ylim[0] <= v <= p.ylim[1]]
    g.append('</g>')
    g.append(f'<line x1="{p.x0}" x2="{p.x1}" y1="{p.y1}" y2="{p.y1}" stroke="{AXIS}" stroke-width="1"/>')
    g.append(f'<g class="ticks" fill="{MUTED}" font-size="11">')
    g += [f'<text x="{p.X(v):.1f}" y="{p.y1 + 17}" text-anchor="middle">{xfmt(v)}</text>' for v in xt[0] if p.xlim[0] <= v <= p.xlim[1]]
    g += [f'<text x="{p.x0 - 8}" y="{p.Y(v) + 4:.1f}" text-anchor="end">{yfmt(v)}</text>' for v in yt[0] if p.ylim[0] <= v <= p.ylim[1]]
    g.append('</g>')
    g.append(txt((p.x0 + p.x1) / 2, p.h - 8, xlabel, lang, 'middle'))
    g.append(txt(0, 0, ylabel, lang, 'middle', extra=f' transform="translate(14 {(p.y0 + p.y1) / 2:.1f}) rotate(-90)"'))
    return ''.join(g)

def legend(items):
    """items: (label, color, kind) kind = line | dot | dash | status-x | status-!"""
    out = ['<div class="chart-legend">']
    for label, color, kind in items:
        if kind == 'line': key = f'<svg width="22" height="10" aria-hidden="true"><line x1="1" x2="21" y1="5" y2="5" stroke="{color}" stroke-width="2" stroke-linecap="round"/></svg>'
        elif kind == 'dash': key = f'<svg width="22" height="10" aria-hidden="true"><line x1="1" x2="21" y1="5" y2="5" stroke="{color}" stroke-width="1.5" stroke-dasharray="4 3"/></svg>'
        elif kind == 'dot': key = f'<svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="4.5" fill="{color}"/></svg>'
        elif kind == 'hollow': key = f'<svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="4.5" fill="none" stroke="{color}" stroke-width="1.5"/></svg>'
        elif kind == 'square': key = f'<svg width="14" height="14" aria-hidden="true"><rect x="2" y="2" width="10" height="10" rx="2" fill="{color}"/></svg>'
        else: key = f'<span class="st" style="--c:{color}">{"✕" if kind == "status-x" else "!"}</span>'
        out.append(f'<span>{key}{esc(label)}</span>')
    out.append('</div>'); return ''.join(out)

def table(head, rows, summary):
    th = ''.join(f'<th>{esc(h)}</th>' for h in head)
    tr = ''.join('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>' for r in rows)
    return f'<details class="tbl"><summary>{esc(summary)}</summary><div class="tbl-scroll"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></details>'

def hover_data(p, xs_px, xlabels, series):
    """series: [{'name','color','vals':[formatted]}] — JS picks the nearest x and lists every series."""
    return esc(json.dumps({'top': p.y0, 'bottom': p.y1, 'px': [round(x, 1) for x in xs_px], 'xl': xlabels,
                           'series': series}, ensure_ascii=False, separators=(',', ':')))

def figure(inner_svg, caption_t, caption_d, legend_html, table_html, hover=None, w=640, h=340, label=''):
    hv = f' data-hover="{hover}" tabindex="0"' if hover else ''
    return (f'<figure class="chart"{hv}><figcaption><b>{esc(caption_t)}</b><span>{caption_d}</span></figcaption>{legend_html}'
            f'<div class="chart-box"><svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label or caption_t)}" direction="ltr">{inner_svg}</svg></div>'
            f'{table_html}</figure>')

T = {
 'fa': dict(table='نمایش داده‌های نمودار', lag='فاصله (h، متر)', gamma='واریوگرام γ(h)', exp='واریوگرام تجربی', model='مدل کروی برازش‌شده',
            nugget='اثر قطعه‌ای', sill='سقف', range='دامنه', pairs='تعداد زوج', m='متر'),
 'en': dict(table='Show chart data', lag='Lag distance (h, m)', gamma='Variogram γ(h)', exp='Experimental variogram', model='Fitted spherical model',
            nugget='nugget', sill='sill', range='range', pairs='pairs', m='m'),
}

def sph(h, c0, c1, a):
    if h <= 0: return 0.0
    return c0 + c1 * (1.5 * h / a - 0.5 * (h / a) ** 3) if h < a else c0 + c1

# ---------- ۱) واریوگرام تجربی و مدل ----------
def fig_variogram(lang):
    t = T[lang]; c0, c1, a = .15, .85, 80
    random.seed(21)
    lags = list(range(10, 151, 10))
    pairs = [int(60 + 140 * math.sin(math.pi * h / 170)) for h in lags]
    expv = [sph(h, c0, c1, a) + random.gauss(0, .045) * (90 / pairs[i]) ** .5 for i, h in enumerate(lags)]
    p = Plot(640, 340, (0, 160), (0, 1.25))
    curve = ' '.join(f'{p.X(h):.1f},{p.Y(sph(h, c0, c1, a) if h > 0 else c0):.1f}' for h in [0.0001] + list(range(1, 161)))
    svg = [axes(p, lang, t['lag'], t['gamma'])]
    # خطوط مرجع سقف و دامنه
    svg.append(f'<g stroke="{MUTED}" stroke-width="1" stroke-dasharray="3 4" opacity=".7"><line x1="{p.x0}" x2="{p.x1}" y1="{p.Y(c0 + c1):.1f}" y2="{p.Y(c0 + c1):.1f}"/>'
               f'<line x1="{p.X(a):.1f}" x2="{p.X(a):.1f}" y1="{p.Y(c0 + c1):.1f}" y2="{p.y1}"/></g>')
    svg.append(f'<polyline points="{curve}" fill="none" stroke="{S1}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    svg.append(''.join(f'<circle cx="{p.X(h):.1f}" cy="{p.Y(v):.1f}" r="4.5" fill="{S2}" stroke="{SURF}" stroke-width="2"/>' for h, v in zip(lags, expv)))
    svg.append(txt(p.x1 - 4, p.Y(c0 + c1) - 8, f'{t["sill"]} = {num(c0 + c1, lang, 2)}', lang, 'end'))
    svg.append(txt(p.X(a) + 6, p.y1 - 10, f'{t["range"]} a = {num(a, lang)} {t["m"]}', lang))
    svg.append(txt(p.x0 + 10, p.Y(c0) + 18, f'{t["nugget"]} C₀ = {num(c0, lang, 2)}', lang))
    hv = hover_data(p, [p.X(h) for h in lags], [f'h = {num(h, lang)} {t["m"]}' for h in lags], [
        {'name': t['exp'], 'color': S2, 'vals': [num(v, lang, 3) for v in expv]},
        {'name': t['model'], 'color': S1, 'vals': [num(sph(h, c0, c1, a), lang, 3) for h in lags]}])
    leg = legend([(t['exp'], S2, 'dot'), (t['model'], S1, 'line')])
    tbl = table([t['lag'], t['exp'], t['model'], t['pairs']],
                [[num(h, lang), num(v, lang, 3), num(sph(h, c0, c1, a), lang, 3), num(n, lang)] for h, v, n in zip(lags, expv, pairs)], t['table'])
    cap = ('واریوگرام تجربی و مدل کروی' if lang == 'fa' else 'Experimental variogram and spherical model')
    capd = ('داده‌های نمایشی؛ اثر قطعه‌ای ۰٫۱۵، سقف ۱٫۰۰ و دامنهٔ ۸۰ متر. نقاط با زوج‌های کمتر پراکندگی بیشتری دارند.' if lang == 'fa'
            else 'Illustrative data: nugget 0.15, sill 1.00, range 80 m. Lags with fewer pairs scatter more.')
    return figure(''.join(svg), cap, capd, leg, tbl, hv)

# ---------- ۲) وزن‌های کریجینگ معمولی در برابر عکس فاصله ----------
def _solve(A, b):
    n = len(b); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1): M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]

# یک نمونهٔ تنها در شرق، خوشهٔ سه‌تایی در غرب در همان فاصله، و یک نمونه درست پشت نمونهٔ شمالی (اثر سایه)
KR_SAMPLES = [(45, 0), (-45, 0), (-49, 7), (-49, -7), (0, 25), (0, 55), (0, -40)]

def kriging_weights(c0=.1, c1=.9, a=80, pts=KR_SAMPLES):
    g = lambda p, q: sph(math.dist(p, q), c0, c1, a)
    n = len(pts)
    A = [[g(pts[i], pts[j]) for j in range(n)] + [1] for i in range(n)] + [[1] * n + [0]]
    b = [g(pts[i], (0, 0)) for i in range(n)] + [1]
    sol = _solve(A, b); lam, mu = sol[:n], sol[n]
    kv = sum(l * bi for l, bi in zip(lam, b[:n])) + mu
    inv = [1 / math.dist(p, (0, 0)) ** 2 for p in pts]; idw = [v / sum(inv) for v in inv]
    return lam, idw, kv

def fig_kriging_weights(lang):
    fa = lang == 'fa'; lam, idw, kv = kriging_weights()
    p = Plot(560, 440, (-90, 90), (-70, 80), ml=46, mr=18, mt=18, mb=44)
    # نسبت ابعاد مساوی: ۱۸۰ متر افقی و ۱۵۰ متر عمودی
    xt, yt = ([-80, -40, 0, 40, 80], 40), ([-40, 0, 40], 40)
    svg = [axes(p, lang, 'شرقی (متر)' if fa else 'Easting (m)', 'شمالی (متر)' if fa else 'Northing (m)', xt=xt, yt=yt)]
    r = (p.X(80) - p.X(0)); ry = (p.Y(0) - p.Y(80))
    svg.append(f'<ellipse cx="{p.X(0):.1f}" cy="{p.Y(0):.1f}" rx="{r:.1f}" ry="{ry:.1f}" fill="none" stroke="{MUTED}" stroke-width="1" stroke-dasharray="3 4" opacity=".6"/>')
    svg.append(txt(p.X(0) + r * .70, p.Y(0) - ry * .76, 'دامنهٔ واریوگرام' if fa else 'variogram range', lang, size=11))
    for i, ((x, y), w, wi) in enumerate(zip(KR_SAMPLES, lam, idw), 1):
        rad = 4 + 26 * math.sqrt(abs(w))
        tip = (f'نمونهٔ {num(i, lang)} · فاصله {num(math.dist((x, y), (0, 0)), lang)} متر · وزن کریجینگ {num(w * 100, lang, 1, True)} · وزن عکس فاصله {num(wi * 100, lang, 1, True)}' if fa else
               f'Sample {i} · {math.dist((x, y), (0, 0)):.0f} m · kriging weight {w * 100:.1f}% · inverse-distance weight {wi * 100:.1f}%')
        fill = f'fill="{S2}" fill-opacity=".85"' if w >= 0 else f'fill="none" stroke="{S2}" stroke-width="1.5"'
        svg.append(f'<g class="tip-t" data-tip="{esc(tip)}" tabindex="0"><circle cx="{p.X(x):.1f}" cy="{p.Y(y):.1f}" r="{max(rad, 12):.1f}" fill="transparent"/>'
                   f'<circle cx="{p.X(x):.1f}" cy="{p.Y(y):.1f}" r="{rad:.1f}" {fill} stroke-width="2"/>'
                   + (f'<text x="{p.X(x) - rad - 6:.1f}" y="{p.Y(y) + 4:.1f}" text-anchor="end" fill="{INK}" font-size="11.5">{num(w * 100, lang, 0, True)}</text></g>' if x < -30 else
                      f'<text x="{p.X(x):.1f}" y="{p.Y(y) - rad - 5:.1f}" text-anchor="middle" fill="{INK}" font-size="11.5">{num(w * 100, lang, 0, True)}</text></g>'))
    s = 7; svg.append(f'<rect x="{p.X(0) - s:.1f}" y="{p.Y(0) - s:.1f}" width="{2 * s}" height="{2 * s}" rx="2" fill="{S1}" stroke="{SURF}" stroke-width="2"/>')
    svg.append(txt(p.X(0), p.Y(0) + 24, 'نقطهٔ تخمین' if fa else 'estimated point', lang, 'middle', 11))
    leg = legend([('نقطهٔ تخمین' if fa else 'Estimated point', S1, 'square'), ('نمونه (اندازه ∝ وزن)' if fa else 'Sample (size ∝ weight)', S2, 'dot'),
                  ('وزن منفی' if fa else 'Negative weight', S2, 'hollow')])
    tbl = table(['نمونه' if fa else 'Sample', 'فاصله (متر)' if fa else 'Distance (m)', 'وزن کریجینگ' if fa else 'Kriging weight', 'وزن عکس فاصلهٔ توان ۲' if fa else 'IDW² weight'],
                [[num(i, lang), num(math.dist(pt, (0, 0)), lang), num(w * 100, lang, 1, True), num(wi * 100, lang, 1, True)]
                 for i, (pt, w, wi) in enumerate(zip(KR_SAMPLES, lam, idw), 1)], T[lang]['table'])
    cap = 'وزن‌های کریجینگ معمولی' if fa else 'Ordinary kriging weights'
    cl, single, icl, isg, scr = sum(lam[1:4]) * 100, lam[0] * 100, sum(idw[1:4]) * 100, idw[0] * 100, lam[5] * 100
    capd = (f'هفت نمونه با مدل کروی (اثر قطعه‌ای ۰٫۱، سقف ۱، دامنهٔ ۸۰ متر). سه نمونهٔ خوشه‌ای غرب روی هم {num(cl, lang, 0, True)} وزن می‌گیرند، تقریباً برابر تک‌نمونهٔ شرق در همان فاصله ({num(single, lang, 0, True)})؛ '
            f'روش عکس فاصله به خوشه {num(icl, lang, 0, True)} و به تک‌نمونه {num(isg, lang, 0, True)} وزن می‌دهد. نمونهٔ پشت نمونهٔ شمالی «سایه» می‌خورد و وزنش {num(scr, lang, 0, True)} است. واریانس کریجینگ: {num(kv, lang, 3)}.' if fa else
            f'Seven samples, spherical model (nugget 0.1, sill 1, range 80 m). The three clustered samples to the west receive {cl:.0f}% together — about the same as the single sample to the east at the same distance ({single:.0f}%); '
            f'inverse distance would give the cluster {icl:.0f}% and the single sample {isg:.0f}%. The sample behind the northern one is screened and gets {scr:.0f}%. Kriging variance: {kv:.3f}.')
    return figure(''.join(svg), cap, capd, leg, tbl, None, 560, 440)

# ---------- ۳) منحنی عیار‑تناژ (دو نمودار کوچک، بدون محور دوگانه) ----------
def _phi(x): return .5 * (1 + math.erf(x / math.sqrt(2)))

def grade_tonnage(T0=800, m=.45, s=.6, cuts=None):
    mu = math.log(m) - s * s / 2; cuts = cuts or [round(.05 * i, 2) for i in range(0, 25)]
    out = []
    for z in cuts:
        if z <= 0: out.append((z, T0, m)); continue
        P = 1 - _phi((math.log(z) - mu) / s)
        mg = m * _phi((mu + s * s - math.log(z)) / s) / P if P > 1e-9 else float('nan')
        out.append((z, T0 * P, mg))
    return out

def fig_grade_tonnage(lang):
    fa = lang == 'fa'; d = grade_tonnage(); cuts = [r[0] for r in d]
    xl = 'عیار حد (٪ مس)' if fa else 'Cut-off grade (% Cu)'
    figs = []
    for key, idx, ylab, ylim, dec, title in (
            ('t', 1, 'تناژ بالای عیار حد (میلیون تن)' if fa else 'Tonnage above cut-off (Mt)', (0, 850), 0, 'تناژ بالای عیار حد' if fa else 'Tonnage above cut-off'),
            ('g', 2, 'عیار میانگین (٪ مس)' if fa else 'Average grade (% Cu)', (0, 1.6), 2, 'عیار میانگین بالای عیار حد' if fa else 'Average grade above cut-off')):
        p = Plot(640, 260, (0, 1.2), ylim, mb=44)
        vals = [r[idx] for r in d]
        pts = ' '.join(f'{p.X(z):.1f},{p.Y(v):.1f}' for z, v in zip(cuts, vals))
        svg = axes(p, lang, xl, ylab) + f'<path d="M{p.X(0):.1f},{p.y1} L{pts.replace(" ", " L")} L{p.X(cuts[-1]):.1f},{p.y1} Z" fill="{S1}" fill-opacity=".1"/>' \
              f'<polyline points="{pts}" fill="none" stroke="{S1}" stroke-width="2" stroke-linejoin="round"/>'
        z0 = .3; v0 = [r for r in d if abs(r[0] - z0) < 1e-6][0][idx]
        svg += f'<circle cx="{p.X(z0):.1f}" cy="{p.Y(v0):.1f}" r="4.5" fill="{S1}" stroke="{SURF}" stroke-width="2"/>'
        svg += f'<text x="{p.X(z0) + 9:.1f}" y="{p.Y(v0) - 9:.1f}" fill="{INK}" font-size="12">{num(v0, lang, dec)}{"" if key == "t" else ("٪" if fa else "%")}</text>'
        hv = hover_data(p, [p.X(z) for z in cuts], [f'{"عیار حد" if fa else "cut-off"} {num(z, lang, 2)}{"٪" if fa else "%"}' for z in cuts],
                        [{'name': title, 'color': S1, 'vals': [num(v, lang, dec) for v in vals]}])
        figs.append(figure(svg, title, '', '', '', hv, 640, 260))
    tbl = table([xl, 'تناژ (میلیون تن)' if fa else 'Tonnage (Mt)', 'عیار میانگین (٪)' if fa else 'Average grade (%)', 'فلز محتوا (هزار تن)' if fa else 'Contained metal (kt)'],
                [[num(z, lang, 2), num(t, lang, 0), num(g, lang, 2), num(t * g * 10, lang, 0)] for z, t, g in d], T[lang]['table'])
    cap = ('منحنی عیار‑تناژ یک کانسار فرضی' if fa else 'Grade–tonnage curves for a hypothetical deposit')
    capd = ('توزیع لاگ‌نرمال با ۸۰۰ میلیون تن و عیار میانگین ۰٫۴۵٪ مس (داده‌های نمایشی). دو نمودار جدا به‌جای یک نمودار با دو محور عمودی، تا مقیاس‌ها رابطهٔ کاذب نسازند. نقطهٔ نشان‌داده‌شده: عیار حد ۰٫۳٪.' if fa else
            'Lognormal distribution, 800 Mt at 0.45% Cu (illustrative). Two separate charts rather than one dual-axis chart, so the scales cannot invent a relationship. Marked point: 0.3% cut-off.')
    return f'<div class="chart-group"><p class="cg-cap"><b>{esc(cap)}</b><span>{esc(capd)}</span></p>{"".join(figs)}{tbl}</div>'

# ---------- ۴) نمودار کنترل نمونهٔ استاندارد (CRM) ----------
def fig_control_chart(lang):
    fa = lang == 'fa'; cv, sd = 1.25, .04
    random.seed(8); vals = [round(cv + random.gauss(0, .028), 3) for _ in range(40)]
    vals[16] = 1.402; vals[27], vals[28] = 1.338, 1.344
    n = list(range(1, 41))
    p = Plot(640, 320, (0, 41), (1.08, 1.44), mb=46)
    svg = [axes(p, lang, 'ترتیب درج در دسته‌های آزمایشگاه' if fa else 'Insertion sequence in laboratory batches', 'طلا (گرم در تن)' if fa else 'Au (g/t)',
                xt=([1, 10, 20, 30, 40], 10), yt=([1.1, 1.2, 1.3, 1.4], .1))]
    for k, col, dash in ((0, INK2, ''), (2, WARN, '4 3'), (-2, WARN, '4 3'), (3, CRIT, '4 3'), (-3, CRIT, '4 3')):
        y = p.Y(cv + k * sd)
        svg.append(f'<line x1="{p.x0}" x2="{p.x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="1" {"stroke-dasharray=" + chr(34) + dash + chr(34) if dash else ""} opacity=".85"/>')
        lab = ('مقدار تأییدشده' if fa else 'certified') if k == 0 else f'{"+" if k > 0 else "−"}{abs(k)}SD'
        svg.append(txt(p.x1 - 4, y - 5, lab, lang, 'end', 11))
    svg.append(f'<polyline points="{" ".join(f"{p.X(i):.1f},{p.Y(v):.1f}" for i, v in zip(n, vals))}" fill="none" stroke="{S2}" stroke-width="1" opacity=".45"/>')
    for i, v in zip(n, vals):
        dev = (v - cv) / sd
        if abs(dev) > 3:
            svg.append(f'<circle cx="{p.X(i):.1f}" cy="{p.Y(v):.1f}" r="7" fill="{CRIT}" stroke="{SURF}" stroke-width="2"/><text x="{p.X(i):.1f}" y="{p.Y(v) + 4:.1f}" text-anchor="middle" fill="#fff" font-size="9" font-weight="700">✕</text>')
            svg.append(txt(p.X(i) + 11, p.Y(v) + 4, 'خطا: بیش از ۳ انحراف معیار' if fa else 'failure: outside ±3SD', lang, size=11.5, fill=INK))
        elif abs(dev) > 2:
            svg.append(f'<circle cx="{p.X(i):.1f}" cy="{p.Y(v):.1f}" r="7" fill="{WARN}" stroke="{SURF}" stroke-width="2"/><text x="{p.X(i):.1f}" y="{p.Y(v) + 3.5:.1f}" text-anchor="middle" fill="#111" font-size="9" font-weight="700">!</text>')
        else:
            svg.append(f'<circle cx="{p.X(i):.1f}" cy="{p.Y(v):.1f}" r="4.5" fill="{S2}" stroke="{SURF}" stroke-width="2"/>')
    svg.append(txt(p.X(28.5), p.Y(1.338) - 14, 'دو هشدار پیاپی ← خطا' if fa else 'two warnings in a row → failure', lang, 'middle', 11.5, INK))
    def state(v):
        d = abs(v - cv) / sd
        return ('خطا' if fa else 'failure') if d > 3 else ('هشدار' if fa else 'warning') if d > 2 else ('قابل قبول' if fa else 'pass')
    hv = hover_data(p, [p.X(i) for i in n], [f'{"نمونهٔ" if fa else "sample"} {num(i, lang)}' for i in n],
                    [{'name': ('طلا (g/t) · ' if fa else 'Au (g/t) · '), 'color': S2, 'vals': [f'{num(v, lang, 3)} · {state(v)}' for v in vals]}])
    leg = legend([('نتیجهٔ نمونهٔ استاندارد' if fa else 'CRM result', S2, 'dot'), ('هشدار: بین ۲ و ۳ انحراف معیار' if fa else 'warning: 2–3 SD', WARN, 'status-!'),
                  ('خطا: بیش از ۳ انحراف معیار' if fa else 'failure: beyond ±3 SD', CRIT, 'status-x')])
    tbl = table(['نمونه' if fa else 'Sample', 'طلا (g/t)' if fa else 'Au (g/t)', 'انحراف (SD)' if fa else 'Deviation (SD)', 'وضعیت' if fa else 'Status'],
                [[num(i, lang), num(v, lang, 3), num((v - cv) / sd, lang, 1), state(v)] for i, v in zip(n, vals)], T[lang]['table'])
    cap = 'نمودار کنترل یک نمونهٔ استاندارد طلا' if fa else 'Control chart for a gold CRM'
    capd = ('مقدار تأییدشده ۱٫۲۵ گرم در تن و انحراف معیار ۰٫۰۴ (داده‌های نمایشی).' if fa else 'Certified value 1.25 g/t, standard deviation 0.04 (illustrative data).')
    return figure(''.join(svg), cap, capd, leg, tbl, hv, 640, 320)

# ---------- ۵) نمودار رده‌بندی منابع و ذخایر (الگوی JORC) ----------
def fig_jorc(lang):
    fa = lang == 'fa'
    W, H = 640, 400
    L = dict(er='نتایج اکتشاف' if fa else 'Exploration Results', mr='منابع معدنی' if fa else 'Mineral Resources', orr='ذخایر کانسنگ' if fa else 'Ore Reserves',
             inf='استنباطی' if fa else 'Inferred', ind='نشان‌داده‌شده' if fa else 'Indicated', mea='اندازه‌گیری‌شده' if fa else 'Measured',
             pro='احتمالی' if fa else 'Probable', prv='قطعی (اثبات‌شده)' if fa else 'Proved',
             conf='افزایش دانش و اطمینان زمین‌شناسی' if fa else 'Increasing geological knowledge and confidence',
             mod='اعمال عوامل تعدیل‌کننده: استخراج، فرآوری، متالورژی، زیرساخت، اقتصاد، بازار، حقوقی، زیست‌محیطی، اجتماعی و حاکمیتی' if fa else
                 'Applying the Modifying Factors: mining, processing, metallurgical, infrastructure, economic, marketing, legal, environmental, social, governmental')
    def box(x, y, w, h, text, tone):
        fills = {'a': ('#1A2226', AXIS), 'b': ('#2A2017', S1), 'c': ('#13261F', S2)}
        f, s = fills[tone]
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{f}" stroke="{s}" stroke-width="1.2"/>'
                + txt(x + w / 2, y + h / 2 + 5, text, lang, 'middle', 14, INK))
    lx, rx, bw, bh = 120, 420, 180, 52
    rows = [150, 222, 294]
    svg = [f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{INK2}"/></marker></defs>']
    svg.append(box(lx, 40, bw, bh, L['er'], 'a'))
    svg.append(txt(lx + bw / 2, rows[0] - 14, L['mr'], lang, 'middle', 13, S1, ' font-weight="600"'))
    svg.append(txt(rx + bw / 2, rows[1] - 14, L['orr'], lang, 'middle', 13, S2, ' font-weight="600"'))
    for y, t in zip(rows, (L['inf'], L['ind'], L['mea'])): svg.append(box(lx, y, bw, bh, t, 'b'))
    svg.append(box(rx, rows[1], bw, bh, L['pro'], 'c')); svg.append(box(rx, rows[2], bw, bh, L['prv'], 'c'))
    a = f'stroke="{INK2}" stroke-width="1.4" marker-end="url(#ar)" fill="none"'
    svg.append(f'<line x1="{lx + bw + 4}" y1="{rows[1] + bh / 2}" x2="{rx - 6}" y2="{rows[1] + bh / 2}" {a}/>')
    svg.append(f'<line x1="{lx + bw + 4}" y1="{rows[2] + bh / 2}" x2="{rx - 6}" y2="{rows[2] + bh / 2}" {a}/>')
    svg.append(f'<line x1="{lx + bw + 4}" y1="{rows[2] + 10}" x2="{rx - 6}" y2="{rows[1] + bh - 10}" {a} stroke-dasharray="4 3"/>')
    svg.append(f'<line x1="{lx + bw / 2}" y1="{40 + bh + 4}" x2="{lx + bw / 2}" y2="{rows[0] - 26}" {a}/>')
    svg.append(f'<line x1="70" y1="60" x2="70" y2="{rows[2] + bh}" {a}/>')
    svg.append(txt(0, 0, L['conf'], lang, 'middle', 12, INK2, f' transform="translate(56 {(60 + rows[2] + bh) / 2}) rotate(-90)"'))
    svg.append(f'<foreignObject x="{lx}" y="{H - 44}" width="{rx + bw - lx}" height="40"><div xmlns="http://www.w3.org/1999/xhtml" class="fo-note">{esc(L["mod"])} →</div></foreignObject>')
    cap = 'رابطهٔ نتایج اکتشاف، منابع معدنی و ذخایر کانسنگ' if fa else 'Relationship between Exploration Results, Mineral Resources and Ore Reserves'
    capd = ('بازطراحی‌شده بر اساس شکل ۱ کد JORC (۲۰۱۲). پیکان خط‌چین: منبع اندازه‌گیری‌شده ممکن است به‌دلیل عدم قطعیت عوامل تعدیل‌کننده به ذخیرهٔ احتمالی تبدیل شود.' if fa else
            'Redrawn after Figure 1 of the JORC Code (2012). Dashed arrow: a Measured Resource may convert to a Probable Reserve where Modifying Factors carry uncertainty.')
    return figure(''.join(svg), cap, capd, '', '', None, W, H, cap)

FIGS = {'variogram': fig_variogram, 'kriging': fig_kriging_weights, 'grade_tonnage': fig_grade_tonnage, 'control': fig_control_chart, 'jorc': fig_jorc}
