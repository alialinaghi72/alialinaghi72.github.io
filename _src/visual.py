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
    # واریوگرام تجربی و مدل کروی (نمایشی)
    W, H, pad = 220, 130, 22; a, c0, c = 60, .18, .82
    def model(h): return c0 + c * (1.5 * h / a - .5 * (h / a) ** 3) if h < a else c0 + c
    random.seed(3)
    pts = [(h, model(h) + random.uniform(-.06, .06)) for h in range(8, 100, 8)]
    X = lambda h: pad + h / 100 * (W - pad - 6); Y = lambda g: H - pad - g / 1.15 * (H - pad - 8)
    curve = ' '.join(f'{X(h):.1f},{Y(model(h)):.1f}' for h in range(0, 101, 2))
    dots = ''.join(f'<circle cx="{X(h):.1f}" cy="{Y(g):.1f}" r="2.6"/>' for h, g in pts)
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            f'<path class="ax" d="M{pad} 6V{H-pad}H{W-4}"/><line class="sill" x1="{pad}" y1="{Y(c0+c):.1f}" x2="{W-4}" y2="{Y(c0+c):.1f}"/>'
            f'<polyline class="model" points="0,0 {curve}" /><g class="pts">{dots}</g>'
            f'<text x="{W-6}" y="{H-8}" text-anchor="end">h</text><text x="{pad+4}" y="14">γ(h)</text></svg>').replace('points="0,0 ', 'points="')

def swath_svg():
    W, H, pad = 220, 130, 22; random.seed(5)
    n = 12; base = [math.sin(i / 2.2) * .25 + .55 + i * .01 for i in range(n)]
    comp = [b + random.uniform(-.09, .09) for b in base]; est = [b + random.uniform(-.03, .03) for b in base]
    X = lambda i: pad + i / (n - 1) * (W - pad - 8); Y = lambda v: H - pad - v * (H - pad - 10)
    l1 = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(comp)); l2 = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(est))
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            f'<path class="ax" d="M{pad} 6V{H-pad}H{W-4}"/><polyline class="comp" points="{l1}"/><polyline class="est" points="{l2}"/></svg>')

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
