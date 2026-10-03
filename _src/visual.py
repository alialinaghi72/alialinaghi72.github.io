# تولید گرافیک‌های SVG: مدل بلوکی صفحهٔ اول، تصویر مراحل تخمین، QR کارت ویزیت
import math, random

def _orebody(NX, NY, NZ, seed=7):
    random.seed(seed)
    def g(i, j, k):
        x = (i - NX * .47) / (NX * .42); y = (j - NY * .45) / (NY * .41); z = (k - NZ * .46) / (NZ * .52)
        xr = x * math.cos(.5) + z * math.sin(.5); zr = -x * math.sin(.5) + z * math.cos(.5)
        return 1 - (xr * xr + y * y * 1.1 + zr * zr * 1.6) + random.uniform(-.12, .12)
    return {(i, j, k): g(i, j, k) for i in range(NX) for j in range(NY) for k in range(NZ)}

RAMP = [(46, 58, 62), (192, 122, 69), (240, 190, 128)]
def _grade_col(v, shade, lo=.08):
    t = max(0, min(1, (v - lo) / .75)); a, b, c = RAMP
    if t < .55: u = t / .55; r = [a[x] + (b[x] - a[x]) * u for x in range(3)]
    else: u = (t - .55) / .45; r = [b[x] + (c[x] - b[x]) * u for x in range(3)]
    return '#%02x%02x%02x' % tuple(int(x * shade) for x in r)
CLASS = {'m': (94, 156, 139), 'i': (192, 122, 69), 'f': (88, 100, 106)}
def _class_col(c, shade): return '#%02x%02x%02x' % tuple(int(x * shade) for x in CLASS[c])

class Iso:
    def __init__(s, W=16, H=9.2, Z=17, ox=300, oy=40): s.W, s.H, s.Z, s.ox, s.oy = W, H, Z, ox, oy
    def P(s, i, j, k): return (s.ox + (i - j) * s.W, s.oy + (i + j) * s.H - k * s.Z)
    def pt(s, i, j, k): x, y = s.P(i, j, k); return f"{x:.1f},{y:.1f}"

def _faces(iso, on, colfn):
    out = []
    for (i, j, k) in sorted(on, key=lambda c: (c[0] + c[1], c[2])):
        pt = iso.pt
        if (i, j, k + 1) not in on: out.append((pt(i, j, k + 1) + ' ' + pt(i + 1, j, k + 1) + ' ' + pt(i + 1, j + 1, k + 1) + ' ' + pt(i, j + 1, k + 1), colfn((i, j, k), 1.0)))
        if (i + 1, j, k) not in on: out.append((pt(i + 1, j, k) + ' ' + pt(i + 1, j + 1, k) + ' ' + pt(i + 1, j + 1, k + 1) + ' ' + pt(i + 1, j, k + 1), colfn((i, j, k), .72)))
        if (i, j + 1, k) not in on: out.append((pt(i, j + 1, k) + ' ' + pt(i + 1, j + 1, k) + ' ' + pt(i + 1, j + 1, k + 1) + ' ' + pt(i, j + 1, k + 1), colfn((i, j, k), .55)))
    return out

def _poly(faces, fill=True):
    if fill: return ''.join(f'<polygon points="{p}" fill="{c}"/>' for p, c in faces)
    return ''.join(f'<polygon points="{p}"/>' for p, c in faces)

def _line(a, b): return f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>'

def _grid(iso, NX, NY):
    return ''.join(_line(iso.P(i, 0, 0), iso.P(i, NY, 0)) for i in range(NX + 1)) + ''.join(_line(iso.P(0, j, 0), iso.P(NX, j, 0)) for j in range(NY + 1))

def hero_svg():
    NX, NY, NZ = 11, 8, 5
    G = _orebody(NX, NY, NZ); on = {c for c, v in G.items() if v > .08}; iso = Iso()
    blocks = _poly(_faces(iso, on, lambda c, sh: _grade_col(G[c], sh)))
    dh = ''
    for (i, j) in [(3, 2), (6, 3), (8, 5), (5, 6)]:
        a = iso.P(i + .5, j + .5, NZ + 1.2); b = iso.P(i + .5, j + .5, -.2)
        dh += _line(a, b) + f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2.2"/>'
    return (f'<svg class="bm" viewBox="160 -10 330 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            f'<g class="bm-grid">{_grid(iso, NX, NY)}</g>'
            f'<g class="bm-blocks" stroke="#0B0E10" stroke-width=".6" stroke-linejoin="round">{blocks}</g>'
            f'<g class="bm-dh">{dh}</g></svg>')

def story_svg():
    """یک SVG با لایه‌های جدا برای هر مرحله؛ CSS بر اساس data-step آن‌ها را نشان می‌دهد."""
    NX, NY, NZ = 12, 9, 6
    G = _orebody(NX, NY, NZ, seed=11); on = {c for c, v in G.items() if v > .05}
    iso = Iso(W=15, H=8.6, Z=15, ox=300, oy=30)
    holes = [(2, 2), (5, 2), (8, 3), (3, 5), (6, 5), (9, 6), (5, 7), (7, 8), (10, 4)]
    def cls(c):
        i, j, k = c
        d = min(math.hypot(i + .5 - (a + .5), j + .5 - (b + .5)) for a, b in holes)
        return 'm' if d <= .75 else ('i' if d <= 1.25 else 'f')
    grade = _poly(_faces(iso, on, lambda c, sh: _grade_col(G[c], sh, lo=.05)))
    klass = _poly(_faces(iso, on, lambda c, sh: _class_col(cls(c), sh)))
    shell = _poly(_faces(iso, on, lambda c, sh: ''), fill=False)
    dh = ''; ticks = ''
    for (i, j) in holes:
        a = iso.P(i + .5, j + .5, NZ + 1.4); b = iso.P(i + .5, j + .5, 0)
        dh += _line(a, b) + f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2.4"/>'
        for k in range(NZ):
            v = G[(i, j, k)]; p0 = iso.P(i + .5, j + .5, k + .15); p1 = iso.P(i + .5, j + .5, k + .85)
            col = _grade_col(v, 1, lo=.05) if (i, j, k) in on else '#3A464C'
            ticks += f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="{col}"/>'
    return (f'<svg class="story-svg" viewBox="150 -92 345 312" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            f'<g class="s-grid">{_grid(iso, NX, NY)}</g>'
            f'<g class="s-layer s-shell" fill="rgba(94,156,139,.07)" stroke="#5E9C8B" stroke-width=".6" stroke-linejoin="round">{shell}</g>'
            f'<g class="s-layer s-grade" stroke="#0B0E10" stroke-width=".5" stroke-linejoin="round">{grade}</g>'
            f'<g class="s-layer s-class" stroke="#0B0E10" stroke-width=".5" stroke-linejoin="round">{klass}</g>'
            f'<g class="s-dh">{dh}</g><g class="s-ticks" stroke-width="3.2">{ticks}</g></svg>')

def variogram_svg():
    # واریوگرام تجربی با مدل کروی و نشانه‌گذاری اثر قطعه‌ای، سقف و دامنه (نمایشی)
    W, H, L, B = 280, 160, 30, 26; a, c0, c = 62, .2, .8
    def model(h): return c0 + c * (1.5 * h / a - .5 * (h / a) ** 3) if h < a else c0 + c
    random.seed(3)
    pts = [(h, model(h) + random.uniform(-.05, .05), 30 + random.randint(0, 90)) for h in range(8, 104, 8)]
    X = lambda h: L + h / 110 * (W - L - 10); Y = lambda g: H - B - g / 1.2 * (H - B - 12)
    curve = ' '.join(f'{X(h):.1f},{Y(model(h)):.1f}' for h in [0.01] + list(range(1, 111)))
    dots = ''.join(f'<circle cx="{X(h):.1f}" cy="{Y(g):.1f}" r="{1.6 + n / 60:.1f}"/>' for h, g, n in pts)
    ticks = ''.join(f'<text x="{X(v):.1f}" y="{H - B + 12}" text-anchor="middle">{v}</text>' for v in (0, 50, 100))
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" direction="ltr" aria-hidden="true">'
            f'<path class="ax" d="M{L} 8V{H-B}H{W-6}"/>'
            f'<line class="ann" x1="{L}" y1="{Y(c0+c):.1f}" x2="{W-6}" y2="{Y(c0+c):.1f}"/>'
            f'<line class="ann" x1="{X(a):.1f}" y1="{Y(c0+c):.1f}" x2="{X(a):.1f}" y2="{H-B}"/>'
            f'<polyline class="model" points="{curve}"/><g class="pts">{dots}</g>'
            f'<text class="ann-t" x="{W-8}" y="{Y(c0+c)-4:.1f}" text-anchor="end">sill</text>'
            f'<text class="ann-t" x="{X(a)+4:.1f}" y="{H-B-5}">range ≈ {a} m</text>'
            f'<text class="ann-t" x="{L+4}" y="{Y(c0)+3:.1f}">nugget</text>'
            f'{ticks}<text x="{W-6}" y="{H-4}" text-anchor="end">lag h (m)</text>'
            f'<text x="{L-4}" y="12" text-anchor="end">γ</text></svg>')

def swath_svg():
    # نمودار Swath: میانگین ترکیب‌ها در برابر میانگین مدل بلوکی در نوارهای شرقی (نمایشی)
    W, H, L, B = 280, 160, 30, 26; random.seed(5); n = 12
    base = [math.sin(i / 2.2) * .25 + .55 + i * .01 for i in range(n)]
    comp = [b + random.uniform(-.09, .09) for b in base]; est = [b + random.uniform(-.025, .025) for b in base]
    X = lambda i: L + 6 + i / (n - 1) * (W - L - 18); Y = lambda v: H - B - v * (H - B - 14)
    l1 = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(comp)); l2 = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(est))
    d1 = ''.join(f'<circle class="lg-c" cx="{X(i):.1f}" cy="{Y(v):.1f}" r="2"/>' for i, v in enumerate(comp))
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" direction="ltr" aria-hidden="true">'
            f'<path class="ax" d="M{L} 8V{H-B}H{W-6}"/>'
            f'<polyline class="comp" points="{l1}"/>{d1}<polyline class="est" points="{l2}"/>'
            f'<rect class="lg-c" x="{L+8}" y="10" width="10" height="2.5"/><text x="{L+22}" y="14">composites</text>'
            f'<rect class="lg-e" x="{L+92}" y="10" width="10" height="2.5"/><text x="{L+106}" y="14">block estimate</text>'
            f'<text x="{W-6}" y="{H-4}" text-anchor="end">easting (swath)</text>'
            f'<text x="{L-4}" y="12" text-anchor="end">grade</text></svg>')

def qr_svg(vcard, label):
    import segno
    q = segno.make(vcard, error='l', micro=False); m = [list(r) for r in q.matrix]; n = len(m); d = []
    for y, row in enumerate(m):
        x = 0
        while x < n:
            if row[x]:
                s0 = x
                while x < n and row[x]: x += 1
                d.append(f"M{s0+1} {y+1}h{x-s0}v1h-{x-s0}z")
            else: x += 1
    return (f'<svg role="img" aria-label="{label}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n+2} {n+2}" '
            f'shape-rendering="crispEdges"><path fill="currentColor" d="{"".join(d)}"/></svg>')
