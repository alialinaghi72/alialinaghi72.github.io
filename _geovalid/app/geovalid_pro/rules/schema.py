"""Schema-level rules added for the v2 brief (category A/B): missing-value ambiguity (IMP-006) and CRS plausibility (IMP-012)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import rule

_PLACEHOLDERS = {"-", "--", "?", "NA", "N/A", "N.A.", "NULL", "NONE", "NIL", "NAN", "X", "*", "نامشخص", "ندارد"}
_NUMERIC_FIELDS = ["x", "y", "z", "eoh_m", "azimuth", "dip", "depth_m", "from_m", "to_m", "cr_pct", "rqd_pct",
                   "run_length_m", "recovered_length_m", "rqd_length_m", "density", "azimuth_mag", "mag_field"]
_ZERO_SUSPECT = {"x", "y", "eoh_m", "density", "run_length_m", "mag_field"}
_KEY = {"x", "y", "z", "eoh_m", "depth_m", "from_m", "to_m", "dip", "azimuth"}


def _classify(raw: pd.Series, sentinels: set) -> pd.Series:
    t = raw.astype("string").str.strip()
    num = pd.to_numeric(t.str.replace(",", ".", regex=False), errors="coerce")
    kind = pd.Series("value", index=raw.index, dtype=object)
    kind[t.isna() | (t == "")] = "blank"
    kind[t.str.upper().isin(_PLACEHOLDERS).fillna(False)] = "placeholder"
    kind[num.isin(sentinels)] = "sentinel"
    kind[(num == 0)] = "zero"
    return kind


@rule("IMP-006", ())
def imp_006(ctx):
    """SCH-06: blank vs zero vs missing-code ambiguity in one numeric field. Per (table, field) the raw cells are classed
    as blank, zero (only where zero is not a natural value: X, Y, EOH, density, run length, field strength), numeric
    sentinel (`sentinels`) or text placeholder (`-`, `NA`, `?` …). Two or more of these representations of "missing" in
    the same field → WARNING (Minor). Sentinels or placeholders alone → INFO, raised to WARNING in coordinate, depth or
    angle fields. Nothing is converted: the counts are reported so the user can decide."""
    p = ctx.p("IMP-006")
    sentinels = {float(x) for x in p.get("sentinels", [-99, -999, -9999, 9999])}
    tabs = ([ctx.collar] if ctx.collar is not None else []) + ([ctx.survey] if ctx.survey is not None else []) + ctx.tables
    for t in tabs:
        if t.raw is None:
            continue
        for f in _NUMERIC_FIELDS:
            col = t.fieldmap.get(f)
            if not col or col not in t.raw:
                continue
            kind = _classify(t.raw[col], sentinels)
            if f not in _ZERO_SUSPECT:
                kind = kind.replace("zero", "value")
            counts = kind[kind != "value"].value_counts()
            if counts.empty:
                continue
            forms = {k: int(v) for k, v in counts.items()}
            first = kind.index[kind != "value"][0]
            row = int(t.df.at[first, "src_row"]) if "src_row" in t.df else None
            desc = ", ".join(f"{k} {v}" for k, v in forms.items())
            if len(forms) >= 2:
                ctx.add("IMP-006", "WARNING", t.name, f"Column '{col}' ({f}) mixes {len(forms)} representations of missing values: {desc}. They are kept distinct; confirm which mean 'not measured' and which are real values.",
                        f"ستون «{col}» ({f}) چند شکل مختلف برای مقدار ناموجود دارد: {desc}. از هم جدا نگه داشته شده‌اند؛ معنای هر یک را تأیید کنید.",
                        field=f, value=desc, src_row=row)
            elif "sentinel" in forms or "placeholder" in forms:
                sev = "WARNING" if f in _KEY else "INFO"
                ctx.add("IMP-006", sev, t.name, f"Column '{col}' ({f}) holds {desc} (missing-value codes); they are treated as missing, raw values kept.",
                        f"ستون «{col}» ({f}) دارای {desc} (کد مقدار ناموجود) است؛ ناموجود در نظر گرفته شد و مقدار خام حفظ شده است.",
                        field=f, value=desc, src_row=row)


def _utm_zone_from(params) -> tuple[int | None, str | None]:
    crs = params.get("crs") or {}
    epsg = crs.get("epsg")
    if epsg:
        e = int(epsg)
        if 32601 <= e <= 32660:
            return e - 32600, "N"
        if 32701 <= e <= 32760:
            return e - 32700, "S"
    z = crs.get("utm_zone")
    return (int(z), str(crs.get("hemisphere", "N")).upper()[0]) if z else (None, None)


@rule("IMP-012", ("collar",))
def imp_012(ctx):
    """COL-04: CRS plausibility. (a) With a declared UTM zone (profile `crs: {utm_zone, hemisphere}` or `epsg`), collars
    outside the zone's easting range (100–900 km) or the hemisphere's northing range → ERROR (Major). (b) Mixed
    coordinate systems: clusters of ≥ 2 collars whose centre lies more than `cluster_sep_km` (20 km) from the main
    cluster → ERROR, with the offset (a constant offset suggests a false-easting, zone or datum mix). (c) No CRS
    declared → one INFO describing what the coordinates look like (never assumed)."""
    p = ctx.p("IMP-012")
    c = ctx.collar_u
    c = c[np.isfinite(c["x"]) & np.isfinite(c["y"])]
    if c.empty:
        return
    zone, hemi = _utm_zone_from(ctx.params)
    x, y = c["x"].to_numpy(float), c["y"].to_numpy(float)
    if zone is None:
        looks = ("UTM-like (6-digit easting, 7-digit northing)" if np.median(np.abs(x)) > 1e5 and np.median(np.abs(y)) > 1e6 else
                 "geographic degrees" if (np.abs(x) <= 180).all() and (np.abs(y) <= 90).all() else "a local grid")
        ctx.add("IMP-012", "INFO", ctx.collar.name, f"No coordinate reference system is declared; the collar coordinates look {looks}. Declare the CRS in the profile (`crs`).",
                f"سیستم مختصات اعلام نشده است؛ مختصات دهانه‌ها شبیه {looks} است. سیستم مختصات را در پروفایل اعلام کنید.", field="crs", value=looks)
    else:
        bad_e = (x < 100_000) | (x > 900_000)
        bad_n = (y < 0) | (y > 10_000_000) if hemi == "N" else (y < 1_000_000) | (y > 10_000_000)
        for (h, r), be, bn in zip(c.iterrows(), bad_e, bad_n):
            if be or bn:
                ctx.add("IMP-012", "ERROR", ctx.collar.name, f"Collar ({r['x']:.0f}, {r['y']:.0f}) is outside the valid range of the declared UTM zone {zone}{hemi}.",
                        f"دهانه ({r['x']:.0f}، {r['y']:.0f}) خارج از محدودهٔ معتبر منطقهٔ UTM اعلام‌شده ({zone}{hemi}) است.", hole_id=h,
                        field="x" if be else "y", value=r["x"] if be else r["y"], src_row=int(r["src_row"]))
    if len(c) < 4:
        return
    xy = np.column_stack([x, y])
    lab = _cell_clusters(xy, p["cluster_sep_km"] * 1000 / 4)
    n = lab.max() + 1
    if n < 2:
        return
    sizes = np.bincount(lab)
    main = int(np.argmax(sizes))
    centre = xy[lab == main].mean(axis=0)
    for k in range(n):
        if k == main or sizes[k] < 2:
            continue
        off = xy[lab == k].mean(axis=0) - centre
        if np.hypot(*off) / 1000 > p["cluster_sep_km"]:
            ids = list(c.index[lab == k])
            ctx.add("IMP-012", "ERROR", ctx.collar.name,
                    f"{len(ids)} collars ({', '.join(map(str, ids[:8]))}) form a separate cluster offset by ΔE {off[0] / 1000:+.1f} km, ΔN {off[1] / 1000:+.1f} km from the main cluster: probably mixed coordinate systems, zones or false eastings.",
                    f"{len(ids)} دهانه خوشهٔ جداگانه‌ای با جابه‌جایی شرقی {off[0] / 1000:+.1f} و شمالی {off[1] / 1000:+.1f} کیلومتر از خوشهٔ اصلی می‌سازند: احتمالاً سیستم‌های مختصات یا منطقه‌های مختلط.",
                    hole_id=ids[0], field="x,y", value=f"{off[0]:.0f},{off[1]:.0f}")


def _cell_clusters(xy: np.ndarray, cell: float) -> np.ndarray:
    """Cluster labels from occupied grid cells joined with their 8 neighbours (union-find): linear time, any density."""
    ij = np.floor(xy / cell).astype(np.int64)
    cells, inv = np.unique(ij, axis=0, return_inverse=True)
    index = {tuple(cl): k for k, cl in enumerate(cells)}
    parent = list(range(len(cells)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for k, (i, j) in enumerate(cells):
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                o = index.get((i + di, j + dj))
                if o is not None:
                    ra, rb = find(k), find(o)
                    if ra != rb:
                        parent[ra] = rb
    roots = np.array([find(k) for k in range(len(cells))])
    _, lab = np.unique(roots, return_inverse=True)
    return lab[inv.ravel()]
