"""COL rules: collar integrity, location, topography, spacing (03 §2.2)."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from ..analysis import collar_method
from ..analysis.spatial import clark_evans, distance_to_polyline, nn_distances, point_in_polygon
from .base import rule

T = "collar"


def _tab(ctx):
    return ctx.collar.name


@rule("COL-001", ("collar",))
def col_001(ctx):
    c = ctx.collar_df
    dup = c[c["hole_id"].notna() & c["hole_id"].duplicated(keep=False)]
    for h, g in dup.groupby("hole_id"):
        cols = [k for k in ("x", "y", "z", "eoh_m") if k in g]
        same = all(g[k].nunique(dropna=False) == 1 for k in cols)
        kind_en, kind_fa = ("identical", "یکسان") if same else ("conflicting", "متناقض")
        ctx.add("COL-001", "CRITICAL", _tab(ctx),
                f"HoleID '{h}' appears {len(g)} times in the collar table ({kind_en} records, rows {', '.join(map(str, g['src_row']))}).",
                f"شناسهٔ گمانه «{h}» {len(g)} بار در جدول دهانه آمده است (رکوردهای {kind_fa}، ردیف‌های {', '.join(map(str, g['src_row']))}).",
                hole_id=h, field="hole_id", value=len(g), src_row=int(g["src_row"].iloc[1]),
                suggested_fix="Keep one record per hole; rename re-drills or wedges with a suffix.")


@rule("COL-002", ("collar",))
def col_002(ctx):
    c, p = ctx.collar_df, ctx.p("COL-002")
    big = c["x"].abs().median() > 1000 if c["x"].notna().any() else False
    dummies = set(float(x) for x in p.get("dummy_values", [-99, -999, -9999, 9999, 99999]))
    for i, r in c.iterrows():
        for f in ("x", "y", "z"):
            v = r.get(f)
            if np.isfinite(v) and v in dummies:      # v2 COL-01: dummy coordinate codes
                ctx.add("COL-002", "ERROR", _tab(ctx), f"{f.upper()} = {v:g} is a dummy (missing-value) code, not a coordinate.",
                        f"مقدار {f.upper()} برابر {v:g} کد جانشین (مقدار ناموجود) است، نه مختصات.", hole_id=r["hole_id"], field=f,
                        value=v, src_row=int(r["src_row"]))
                continue
            if not np.isfinite(v):
                ctx.add("COL-002", "ERROR", _tab(ctx), f"{f.upper()} coordinate is missing or not numeric.",
                        f"مختصات {f.upper()} وجود ندارد یا عددی نیست.", hole_id=r["hole_id"], field=f, src_row=int(r["src_row"]))
            elif f in ("x", "y") and v == 0 and big:
                ctx.add("COL-002", "ERROR", _tab(ctx), f"{f.upper()} = 0 lies outside the project extent.",
                        f"مقدار {f.upper()} برابر صفر و خارج از محدودهٔ پروژه است.", hole_id=r["hole_id"], field=f, value=0,
                        src_row=int(r["src_row"]))
        eoh = r.get("eoh_m", np.nan)
        if "eoh_m" in c and (not np.isfinite(eoh) or eoh <= 0):
            ctx.add("COL-002", "ERROR", _tab(ctx), "End-of-hole depth is missing, zero or negative.",
                    "عمق نهایی گمانه وجود ندارد، صفر یا منفی است.", hole_id=r["hole_id"], field="eoh_m", value=eoh,
                    src_row=int(r["src_row"]), suggested_fix="Take EOH from the driller's log; COL-007 lists the deepest data.")
    z = c["z"]
    if (z == 0).any():
        zt = ctx.stats.get("z_topo")
        for i in c.index[z == 0]:
            if zt is not None and np.isfinite(zt.get(i, np.nan)):
                bad = abs(zt[i]) > p["z_zero_tol_m"]
            else:
                bad = z[z != 0].median() > p["z_zero_tol_m"] if (z != 0).any() else False
            if bad:
                ctx.add("COL-002", "ERROR", _tab(ctx), "Z = 0 is implausible here (placeholder for a missing elevation).",
                        "مقدار Z برابر صفر در این محل محتمل نیست (جانشین ارتفاع ناموجود).", hole_id=c.at[i, "hole_id"], field="z",
                        value=0, src_row=int(c.at[i, "src_row"]))


@rule("COL-003", ("collar",))
def col_003(ctx):
    """SCH-05: hole IDs that differ only by case, spaces, `-`, `_`, `.` or (optionally) leading zeros of numeric parts,
    across ALL tables (e.g. `DH-01`, `DH01`, `dh 01`). ERROR (Major), one issue per group, with a suggested target
    (the collar ID; else the most frequent spelling). Suggestion only: merges happen through the approved ID-mapping
    table (fix class ID_MAP), which is saved, applied to a corrected copy and logged."""
    p = ctx.p("COL-003")
    strip_zeros = p.get("strip_leading_zeros", True)

    def key(h):
        k = re.sub(r"[\s_\-\.]+", "", str(h).upper())
        return re.sub(r"(?<!\d)0+(?=\d)", "", k) if strip_zeros else k

    tabs = ([ctx.collar] if ctx.collar is not None else []) + ([ctx.survey] if ctx.survey is not None else []) + ctx.tables
    rows = []
    for t in tabs:
        for h, n in t.df["hole_id"].dropna().astype(str).value_counts().items():
            rows.append({"key": key(h), "raw_id": h, "table": t.name, "kind": t.kind, "rows": int(n)})
    occ = pd.DataFrame(rows)
    groups = []
    if not occ.empty:
        collar_ids = set(ctx.collar_df["hole_id"].dropna().astype(str))
        for k, g in occ.groupby("key"):
            ids = list(dict.fromkeys(g["raw_id"]))
            if len(ids) < 2:
                continue
            in_collar = [i for i in ids if i in collar_ids]
            tot = g.groupby("raw_id")["rows"].sum()
            target = max(in_collar, key=lambda i: tot.get(i, 0)) if in_collar else tot.idxmax()
            where = "; ".join(f"{i} ({', '.join(f'{r.table} {r.rows}' for r in g[g['raw_id'] == i].itertuples())})" for i in ids)
            groups.append(g.assign(suggested_target=target))
            ctx.add("COL-003", "ERROR", _tab(ctx),
                    f"Hole IDs that differ only by case, separators or leading zeros share the key '{k}': {where}. Suggested target: '{target}'. Approve or edit the merge in the ID-mapping table.",
                    f"شناسه‌هایی که فقط در حروف، جداکننده یا صفرهای آغازین تفاوت دارند کلید مشترک «{k}» دارند: {where}. پیشنهاد: «{target}». ادغام را در جدول نگاشت شناسه‌ها تأیید یا ویرایش کنید.",
                    hole_id=target, field="hole_id", value=" / ".join(ids), fix_class="ID_MAP",
                    suggested_fix=f"Map {', '.join(i for i in ids if i != target)} → {target} (ID mapping table)")
    ctx.stats["id_groups"] = pd.concat(groups, ignore_index=True) if groups else pd.DataFrame(columns=["key", "raw_id", "table", "kind", "rows", "suggested_target"])
    c = ctx.collar_df
    ids = c["hole_id"].dropna().unique()
    for h in ids:
        if not re.match(r"^[A-Za-z0-9_\-./]+$", str(h)):
            ctx.add("COL-003", "WARNING", _tab(ctx), f"HoleID '{h}' contains spaces or characters that export targets may reject.",
                    f"شناسهٔ «{h}» دارای فاصله یا نویسه‌هایی است که نرم‌افزارهای مقصد ممکن است نپذیرند.", hole_id=h, field="hole_id")
    if len(ids) >= 100:
        pref = pd.Series([re.match(r"^[A-Za-z]*", str(h)).group(0).upper() for h in ids])
        share = pref.value_counts(normalize=True)
        for pr, f in share.items():
            if f < 0.01:
                ctx.add("COL-003", "WARNING", _tab(ctx), f"Prefix '{pr}' is used by only {f:.1%} of holes (possible typo).",
                        f"پیشوند «{pr}» فقط در {f:.1%} گمانه‌ها به کار رفته است (احتمال اشتباه تایپی).", value=pr, field="hole_id")


@rule("COL-004", ("collar",))
def col_004(ctx):
    from scipy.spatial import cKDTree
    c, p = ctx.collar_u, ctx.p("COL-004")
    c = c[np.isfinite(c["x"]) & np.isfinite(c["y"])]
    if len(c) < 2:
        return
    xy = c[["x", "y"]].to_numpy(float)
    pairs = cKDTree(xy).query_pairs(p["near_dup_distance_m"])
    sv = ctx.survey.df if ctx.survey is not None else None
    for i, j in sorted(pairs):
        a, b = c.iloc[i], c.iloc[j]
        dz = abs((a["z"] if np.isfinite(a["z"]) else 0) - (b["z"] if np.isfinite(b["z"]) else 0))
        if dz >= p["near_dup_dz_m"]:
            continue
        d = float(np.hypot(*(xy[i] - xy[j])))
        same_survey = False
        if sv is not None:
            sa = sv[sv["hole_id"] == a["hole_id"]][["depth_m", "azimuth", "dip"]].round(2).sort_values("depth_m")
            sb = sv[sv["hole_id"] == b["hole_id"]][["depth_m", "azimuth", "dip"]].round(2).sort_values("depth_m")
            same_survey = len(sa) > 0 and sa.to_numpy().tolist() == sb.to_numpy().tolist()
        ta, tb = ctx.traces.get(a["hole_id"]), ctx.traces.get(b["hole_id"])
        sep = np.nan
        if ta is not None and tb is not None:
            from ..analysis.desurvey import position_at
            dd = min(50.0, ta["depth_m"].iloc[-1], tb["depth_m"].iloc[-1])
            sep = float(np.linalg.norm(position_at(ta, [dd])[0] - position_at(tb, [dd])[0]))
        if same_survey and np.isclose(a.get("eoh_m", 0), b.get("eoh_m", 0)):
            sev, cls, cls_fa = "ERROR", "probable TRUE DUPLICATE under two IDs (double counting)", "احتمالاً رکورد تکراری با دو شناسه (شمارش دوباره)"
        elif np.isfinite(sep) and sep < 1.0:
            sev, cls, cls_fa = "WARNING", "same collar and upper trace: wedge or re-drill", "دهانه و مسیر بالایی یکسان: گمانهٔ فرعی (وج) یا حفاری مجدد"
        else:
            sev, cls, cls_fa = "WARNING", "twin or re-drill (traces diverge)", "گمانهٔ دوقلو یا حفاری مجدد (مسیرها جدا می‌شوند)"
        sep_txt = f"; separation at 50 m depth {sep:.1f} m" if np.isfinite(sep) else ""
        ctx.add("COL-004", sev, _tab(ctx),
                f"Collars {a['hole_id']} and {b['hole_id']} are {d:.2f} m apart (ΔZ {dz:.2f} m): {cls}{sep_txt}.",
                f"دهانهٔ {a['hole_id']} و {b['hole_id']} فقط {d:.2f} متر فاصله دارند (ΔZ = {dz:.2f} متر): {cls_fa}.",
                hole_id=a["hole_id"], field="x,y", value=f"{b['hole_id']} @ {d:.2f} m", src_row=int(b["src_row"]))


@rule("COL-005", ("collar", "licence"))
def col_005(ctx):
    """Collar against the licence boundary (any format; multipart polygons and holes by the even–odd rule). Outside by
    more than `buffer_m` → ERROR; outside within `buffer_m` → INFO (tolerance); inside but within `edge_buffer_m` of the
    boundary → INFO."""
    c, p = ctx.collar_u, ctx.p("COL-005")
    buf = float(p.get("buffer_m", 0.0))
    c = c[np.isfinite(c["x"]) & np.isfinite(c["y"])]
    lic = ctx.licence
    if hasattr(lic, "contains"):
        inside, dist = lic.contains(c["x"].to_numpy(), c["y"].to_numpy()), lic.distance(c["x"].to_numpy(), c["y"].to_numpy())
    else:
        inside, dist = point_in_polygon(c["x"], c["y"], lic), distance_to_polyline(c["x"], c["y"], lic)
    ctx.stats["in_licence"] = pd.Series(inside, index=c.index)
    for (h, r), ins, d in zip(c.iterrows(), inside, dist):
        if not ins and d > buf:
            ctx.add("COL-005", "ERROR", _tab(ctx), f"Collar lies outside the licence boundary by {d:.0f} m.",
                    f"دهانه {d:.0f} متر خارج از محدودهٔ پروانه است.", hole_id=h, field="x,y", value=round(d, 1),
                    src_row=int(r["src_row"]), suggested_fix="Check the collar coordinates and the licence corner points.")
        elif not ins:
            ctx.add("COL-005", "INFO", _tab(ctx), f"Collar is {d:.1f} m outside the licence boundary, within the {buf:g} m tolerance.",
                    f"دهانه {d:.1f} متر خارج از محدوده ولی در حد رواداری {buf:g} متر است.", hole_id=h, value=round(d, 1), src_row=int(r["src_row"]))
        elif d <= p["edge_buffer_m"]:
            ctx.add("COL-005", "INFO", _tab(ctx), f"Collar is inside the licence but only {d:.0f} m from the boundary.",
                    f"دهانه داخل محدوده ولی فقط {d:.0f} متر تا مرز فاصله دارد.", hole_id=h, value=round(d, 1), src_row=int(r["src_row"]))


@rule("COL-006", ("collar",))
def col_006(ctx):
    c = ctx.collar_u
    c = c[np.isfinite(c["x"]) & np.isfinite(c["y"])]
    if c.empty:
        return
    geo = (c["x"].abs() <= 180) & (c["y"].abs() <= 90) & ((c["x"] != 0) | (c["y"] != 0))
    swapped = c["x"].between(1.0e6, 1.0e7) & c["y"].between(1.0e5, 1.0e6)
    for h, r in c[geo].iterrows():
        ctx.add("COL-006", "CRITICAL", _tab(ctx), f"X/Y = {r['x']}, {r['y']} look like longitude/latitude stored in projected (UTM) fields.",
                f"مقادیر X/Y = {r['x']}، {r['y']} شبیه طول و عرض جغرافیایی هستند که در فیلدهای UTM ثبت شده‌اند.",
                hole_id=h, field="x,y", value=f"{r['x']}, {r['y']}", src_row=int(r["src_row"]),
                suggested_fix="Convert geographic coordinates to the project UTM zone (EPSG 32638–32641 for Iran).")
    for h, r in c[swapped].iterrows():
        ctx.add("COL-006", "CRITICAL", _tab(ctx), f"X = {r['x']:.0f} is in the northing range and Y = {r['y']:.0f} in the easting range: X and Y appear swapped.",
                f"X = {r['x']:.0f} در محدودهٔ نورثینگ و Y = {r['y']:.0f} در محدودهٔ ایستینگ است: X و Y جابجا شده‌اند.",
                hole_id=h, field="x,y", value=f"{r['x']:.0f}, {r['y']:.0f}", src_row=int(r["src_row"]),
                suggested_fix="Swap X and Y for this record (change set, reviewer approval).")
    ok = c[~geo & ~swapped]
    xs = np.sort(ok["x"].to_numpy())
    if len(xs) >= 2 and xs.max() > 1000:
        gaps = np.diff(xs)
        k = int(np.argmax(gaps))
        if gaps[k] > 300000:
            lo = ok[ok["x"] <= xs[k]]
            hi = ok[ok["x"] > xs[k]]
            minority = lo if len(lo) < len(hi) else hi
            for h, r in minority.iterrows():
                ctx.add("COL-006", "CRITICAL", _tab(ctx),
                        f"Easting {r['x']:.0f} is {gaps[k] / 1000:.0f} km from the other collars: probably a different UTM zone.",
                        f"ایستینگ {r['x']:.0f} حدود {gaps[k] / 1000:.0f} کیلومتر با سایر دهانه‌ها فاصله دارد: احتمالاً زون UTM متفاوت است.",
                        hole_id=h, field="x", value=r["x"], src_row=int(r["src_row"]))


def _max_child_depths(ctx) -> pd.DataFrame:
    rows = []
    if ctx.survey is not None:
        s = ctx.survey.df.groupby("hole_id")["depth_m"].max()
        rows.append(s.rename(ctx.survey.name))
    for t in ctx.tables:
        col = "to_m" if "to_m" in t.df and t.df["to_m"].notna().any() else "depth_m"
        if col in t.df:
            rows.append(t.df.groupby("hole_id")[col].max().rename(t.name))
    return pd.concat(rows, axis=1) if rows else pd.DataFrame()


@rule("COL-007", ("collar",))
def col_007(ctx):
    c, p = ctx.collar_u, ctx.p("COL-007")
    m = _max_child_depths(ctx)
    if m.empty or "eoh_m" not in c:
        return
    m = m.reindex(c.index)
    deepest = m.max(axis=1)
    for h, r in c.iterrows():
        dmax, eoh = deepest.get(h, np.nan), r["eoh_m"]
        if np.isfinite(dmax) and np.isfinite(eoh) and dmax - eoh > p["eoh_tol_m"]:
            tab = m.loc[h].idxmax()
            ctx.add("COL-007", "ERROR", _tab(ctx),
                    f"EOH {eoh:g} m is shallower than the deepest data ({dmax:g} m in '{tab}').",
                    f"عمق نهایی {eoh:g} متر از عمیق‌ترین داده ({dmax:g} متر در «{tab}») کمتر است.",
                    hole_id=h, field="eoh_m", value=eoh, expected=f">= {dmax:g}", src_row=int(r["src_row"]),
                    suggested_fix="Correct EOH from the driller's log or the last core block; do not just copy the deepest sample.")


def _survey_counts(ctx) -> pd.Series:
    if ctx.survey is None:
        return pd.Series(dtype=int)
    return ctx.survey.df.groupby("hole_id").size()


@rule("COL-008", ("collar",))
def col_008(ctx):
    n = _survey_counts(ctx)
    for h, r in ctx.collar_u.iterrows():
        if n.get(h, 0) == 0 and "dip" in r and np.isfinite(r.get("dip", np.nan)):
            ctx.add("COL-008", "WARNING", _tab(ctx), "No downhole survey: the trace uses the collar orientation only.",
                    "برداشت انحراف درون‌چاهی وجود ندارد: مسیر فقط بر پایهٔ جهت دهانه است.", hole_id=h, src_row=int(r["src_row"]),
                    suggested_fix="Survey the hole (gyro if accessible) or document it as unsurveyed.")


@rule("COL-019", ("collar",))
def col_019(ctx):
    n, p = _survey_counts(ctx), ctx.p("COL-019")
    for h, r in ctx.collar_u.iterrows():
        if n.get(h, 0) > 0:
            continue
        dip, az = r.get("dip", np.nan), r.get("azimuth", np.nan)
        if not np.isfinite(dip) or (not np.isfinite(az) and dip > -90 + p["vertical_tol_deg"]):
            ctx.add("COL-019", "ERROR", _tab(ctx), "No survey and no collar orientation: software will silently treat the hole as vertical.",
                    "نه برداشت انحراف و نه جهت دهانه وجود دارد: نرم‌افزارها گمانه را بی‌صدا قائم فرض می‌کنند.",
                    hole_id=h, field="dip", src_row=int(r["src_row"]))


@rule("COL-009", ("collar",))
def col_009(ctx):
    have = set()
    for t in ctx.tables:
        have |= set(t.df["hole_id"].dropna().unique())
    if not ctx.tables:
        return
    for h, r in ctx.collar_u.iterrows():
        if h not in have:
            ctx.add("COL-009", "INFO", _tab(ctx), "Hole has no logging or sample data in any table.",
                    "این گمانه در هیچ جدولی داده لاگ یا نمونه ندارد.", hole_id=h, src_row=int(r["src_row"]))


@rule("COL-010", ("collar",), note="v0.1 preview: precision, grid, rounding and ΔZ evidence")
def col_010(ctx):
    c = ctx.collar_u
    res = collar_method.infer(c, ctx.stats.get("dz"), tuple(ctx.p("COL-010").get("grid_steps_m", (100, 50, 25))))
    ctx.stats["collar_method"] = res
    lbl = {"HANDHELD_GPS": ("handheld GPS", "GPS دستی"), "PLANNED": ("planned (design) coordinates", "مختصات طراحی (برنامه‌ریزی‌شده)"),
           "DIGITISED": ("digitised or map-derived", "رقومی‌شده از نقشه")}
    for h, r in res.iterrows():
        if r["inferred_method"] in lbl:
            en, fa = lbl[r["inferred_method"]]
            ctx.add("COL-010", "WARNING", _tab(ctx), f"Collar location probably from {en} ({r['confidence_pct']:.0f} %): {r['evidence']}.",
                    f"مختصات دهانه احتمالاً از {fa} است (اطمینان {r['confidence_pct']:.0f} درصد): {r['evidence']}.",
                    hole_id=r["hole_id"], field="x,y,z", value=r["inferred_method"],
                    src_row=int(c.loc[h, "src_row"]), suggested_fix="Re-survey with DGPS/RTK before resource estimation (JORC T1.08).")
    for k, g in res.groupby("campaign"):
        weak = g["inferred_method"].isin(lbl.keys()).mean()
        if len(g) >= 5 and weak >= 0.5:
            ctx.add("COL-010", "ERROR", _tab(ctx), f"Campaign '{k}': {weak:.0%} of {len(g)} collars have low-accuracy locations.",
                    f"فاز «{k}»: {weak:.0%} از {len(g)} دهانه مختصات کم‌دقت دارند.", value=f"{weak:.0%}", field="campaign")


@rule("COL-011", ("collar", "dem"))
def col_011(ctx):
    c, p = ctx.collar_u, ctx.p("COL-011")
    if (ctx.stats.get("topo_sanity") or {}).get("blocked"):
        return                    # a gross CRS / unit problem: COL-025 reports it; per-collar ΔZ would be noise
    dz = ctx.stats["dz"]
    ex = ctx.stats.get("topo_exempt")
    if ex is not None and ex.any():
        f = (ctx.params.get("topo_exempt") or {})
        ctx.add("COL-011", "INFO", _tab(ctx), f"{int(ex.sum())} collars exempt from the topography check ({f.get('field')} in {', '.join(map(str, f.get('values', [])))}).",
                f"{int(ex.sum())} دهانه از مقایسه با توپوگرافی معاف شدند ({f.get('field')}).", field=str(f.get("field")), value=int(ex.sum()))
    meth = ctx.stats.get("collar_method")
    for h, r in c.iterrows():
        d = dz.get(h, np.nan)
        if not np.isfinite(d):
            continue
        handheld = meth is not None and h in meth.index and meth.loc[h, "inferred_method"] == "HANDHELD_GPS"
        w, e = (p["handheld_warn_m"], p["handheld_error_m"]) if handheld else (p["warn_m"], p["error_m"])
        if abs(d) >= w:
            sev = "ERROR" if abs(d) >= e else "WARNING"
            side_en, side_fa = ("above", "بالای") if d > 0 else ("below", "زیر")
            ctx.add("COL-011", sev, _tab(ctx), f"Collar is {abs(d):.1f} m {side_en} the topographic surface (ΔZ = {d:+.1f} m).",
                    f"دهانه {abs(d):.1f} متر {side_fa} سطح توپوگرافی است (ΔZ = {d:+.1f} متر).", hole_id=h, field="z", value=round(d, 2),
                    expected=f"|ΔZ| < {w:g} m", src_row=int(r["src_row"]),
                    suggested_fix="Re-survey, drape to topography or keep and flag; record the decision.")


@rule("COL-012", ("collar", "dem"))
def col_012(ctx):
    p = ctx.p("COL-012")
    if (ctx.stats.get("topo_sanity") or {}).get("blocked"):
        return
    dz = ctx.stats["dz"].dropna()
    c = ctx.collar_u
    camp = c["campaign"].fillna("—") if "campaign" in c and c["campaign"].notna().any() else pd.Series("ALL", index=c.index)
    for k, idx in camp.loc[dz.index].groupby(camp.loc[dz.index]).groups.items():
        d = dz.loc[idx]
        n = len(d)
        if n < p["min_n"]:
            continue
        med = float(d.median())
        s = 1.4826 * float(np.median(np.abs(d - med)))
        iqr = float(d.quantile(0.75) - d.quantile(0.25))
        if abs(med) > p.get("datum_median_m", 3.0) and iqr < p.get("datum_iqr_m", 2.0):        # v2 COL-06b
            ctx.add("COL-012", "ERROR", ctx.collar.name,
                    f"Campaign '{k}': median ΔZ {med:+.2f} m with a tight spread (IQR {iqr:.2f} m, n = {n}): a vertical-datum mismatch (ellipsoidal vs orthometric heights, or a different topography datum).",
                    f"فاز «{k}»: میانهٔ اختلاف ارتفاع {med:+.2f} متر با پراکندگی کم (IQR {iqr:.2f} متر): ناسازگاری مبنای ارتفاعی.",
                    field="z", value=round(med, 2), expected=f"|median| ≤ {p.get('datum_median_m', 3.0):g} m", alias="COL-06b",
                    suggested_fix="Confirm the vertical datum of the collars and of the topography; apply one documented shift if justified.")
            continue
        if abs(med) >= max(p["offset_min_m"], 3.86 * s / np.sqrt(n)) and abs(med) > s:
            ctx.add("COL-012", "WARNING", ctx.collar.name,
                    f"Campaign '{k}': systematic ΔZ offset {med:+.2f} m (robust SD {s:.2f} m, n = {n}); a vertical-datum mismatch (ellipsoidal vs orthometric heights) is more likely than random GPS error.",
                    f"فاز «{k}»: اختلاف ارتفاع سیستماتیک {med:+.2f} متر (انحراف معیار مقاوم {s:.2f} متر، n = {n})؛ احتمال ناسازگاری مبنای ارتفاعی (بیضوی در برابر ارتومتریک) بیش از خطای تصادفی GPS است.",
                    field="z", value=round(med, 2), suggested_fix="Confirm the vertical datum; apply one documented datum shift if justified.")


@rule("COL-025", ("collar", "dem"))
def col_025(ctx):
    """Topographic control (v2 R2 sanity checks; catalogue COL-025 (c), (f)). Before any ΔZ comparison: no overlap
    between collars and topography → ERROR with the likely cause (swapped E/N, false easting or northing, other UTM
    zone, other CRS); elevations ≈ 3.28 × apart → ERROR (feet vs metres); collars outside the surface or on nodata →
    WARNING, listed as not checked (never as a pass). Alignment notes (geographic surface converted to UTM, non-WGS 84
    datum, zone mismatch) and global-DEM notes (SRTM: EGM96 geoid, 30 m class) → INFO."""
    st = ctx.stats.get("topo_sanity") or {}
    for sev, msg in st.get("findings", []):
        fa = "بررسی اولیهٔ توپوگرافی: " + msg
        nc = st.get("not_checked") or []
        extra = f" ({', '.join(map(str, nc[:12]))}{' …' if len(nc) > 12 else ''})" if sev == "WARNING" and nc else ""
        ctx.add("COL-025", sev, _tab(ctx), f"Topography check: {msg}{extra}.", fa, field="x,y,z", value=len(nc) if sev == "WARNING" else None,
                suggested_fix="Declare the CRS / zone (profile crs) or supply topography in the collars' coordinate system and units." if sev == "ERROR" else None)
    for t in ctx.stats.get("topography") or []:
        for note in t.get("notes", []):
            ctx.add("COL-025", "INFO", _tab(ctx), f"{t['file']}: {note}.", f"{t['file']}: {note}.", field="topography", value=note[:60])


@rule("COL-013", ("collar",))
def col_013(ctx):
    c, p = ctx.collar_u, ctx.p("COL-013")
    z = c["z"].dropna()
    if len(z) < p["min_group_n"]:
        return
    dec = float(c.loc[z.index, "z_dec"].astype(float).fillna(0).max())
    rng = float(z.max() - z.min())
    n_values = max(rng / (10.0 ** -dec), 1.0)
    lam = len(z) / n_values
    raw = c.loc[z.index, "z_raw"]
    for v, g in raw.groupby(raw):
        if len(g) >= p["min_group_n"] and (lam <= 0.5 or rng == 0):
            ctx.add("COL-013", "WARNING", ctx.collar.name,
                    f"{len(g)} collars share exactly Z = {v} ({', '.join(map(str, g.index[:8]))}{'…' if len(g) > 8 else ''}); Z was probably copied, assumed or taken from a map.",
                    f"{len(g)} دهانه دقیقاً Z = {v} دارند؛ احتمالاً ارتفاع کپی، فرض یا از نقشه برداشته شده است.",
                    hole_id=g.index[0], field="z", value=v)


@rule("COL-014", ("collar",))
def col_014(ctx):
    """Dates (future, before `min_year`, completion before start, implausible drilling rate) and, v2 COL-08, drill-type
    codes not in the known list (`drill_types`) or the `drill_method` code dictionary. WARNING (Minor)."""
    c, p = ctx.collar_u, ctx.p("COL-014")
    if "drill_method" in c and c["drill_method"].notna().any():
        known = {str(x).strip().upper() for x in p.get("drill_types", [])}
        known |= {str(x).strip().upper() for x in (ctx.params.get("code_dictionaries") or {}).get("drill_method", [])}
        dm = c["drill_method"].dropna().astype(str).str.strip()
        for code, g in dm.groupby(dm.str.upper()):
            if code not in known:
                ctx.add("COL-014", "WARNING", ctx.collar.name, f"Drill-type code '{g.iloc[0]}' ({len(g)} holes) is not a known drilling method.",
                        f"کد نوع حفاری «{g.iloc[0]}» ({len(g)} گمانه) روش حفاری شناخته‌شده‌ای نیست.", hole_id=g.index[0], field="drill_method",
                        value=g.iloc[0], src_row=int(c.loc[g.index[0], "src_row"]),
                        suggested_fix="Add the code to the drill_method dictionary, or correct it.")
    if "date_started" not in c and "date_completed" not in c:
        return
    today = pd.Timestamp.today().normalize()
    for h, r in c.iterrows():
        a, b = r.get("date_started"), r.get("date_completed")
        for f, v in (("date_started", a), ("date_completed", b)):
            if pd.notna(v) and (v > today or v.year < p["min_year"]):
                ctx.add("COL-014", "WARNING", ctx.collar.name, f"{f} {v.date()} is in the future or before {p['min_year']}.",
                        f"تاریخ {f} برابر {v.date()} در آینده یا پیش از {p['min_year']} است.", hole_id=h, field=f, value=str(v.date()),
                        src_row=int(r["src_row"]))
        if pd.notna(a) and pd.notna(b):
            if b < a:
                ctx.add("COL-014", "WARNING", ctx.collar.name, f"Completion date {b.date()} is before the start date {a.date()}.",
                        f"تاریخ پایان {b.date()} پیش از تاریخ شروع {a.date()} است.", hole_id=h, field="date_completed",
                        value=str(b.date()), src_row=int(r["src_row"]))
            elif np.isfinite(r.get("eoh_m", np.nan)):
                rate = r["eoh_m"] / ((b - a).days + 1)
                if rate > p["max_rate_m_day"]:
                    ctx.add("COL-014", "WARNING", ctx.collar.name, f"Drilling rate {rate:.0f} m/day is implausible.",
                            f"سرعت حفاری {rate:.0f} متر در روز غیرمحتمل است.", hole_id=h, field="date_completed",
                            value=round(rate, 1), src_row=int(r["src_row"]))


@rule("COL-015", ("collar",))
def col_015(ctx):
    p = ctx.p("COL-015")
    c, excluded = ctx.spatial_collars()
    ctx.stats["spatial_excluded"] = excluded
    xy = c[["x", "y"]].to_numpy(float)
    if len(xy) < 10:
        return
    nn = nn_distances(xy, 3)
    ctx.stats["nn"] = pd.DataFrame(nn, index=c.index, columns=["nn1_m", "nn2_m", "nn3_m"])
    ce = clark_evans(xy)
    ctx.stats["clark_evans"] = ce
    med = float(np.nanmedian(nn[:, 0]))
    for (h, r), d in zip(c.iterrows(), nn[:, 0]):
        if d > p["isolation_x_median"] * med:
            ctx.add("COL-015", "INFO", ctx.collar.name, f"Isolated hole: nearest collar {d:.0f} m away ({d / med:.1f} × median spacing).",
                    f"گمانهٔ منفرد: نزدیک‌ترین دهانه {d:.0f} متر فاصله دارد ({d / med:.1f} برابر فاصلهٔ میانه).", hole_id=h, value=round(d, 1))
    if ce.get("R", 1) < p["ce_clustered"]:
        ctx.add("COL-015", "INFO", ctx.collar.name,
                f"Collars are clustered (Clark–Evans R = {ce['R']:.2f}); declustering is needed before global statistics.",
                f"دهانه‌ها خوشه‌ای هستند (شاخص کلارک–ایوانز R = {ce['R']:.2f})؛ پیش از آمار کلی، واخوشه‌سازی لازم است.",
                value=round(ce["R"], 3))


@rule("COL-016", ("collar",))
def col_016(ctx):
    c, p = ctx.collar_u, ctx.p("COL-016")
    c = c[np.isfinite(c["x"]) & np.isfinite(c["y"])]
    if len(c) < 10:
        return
    xy = c[["x", "y"]].to_numpy(float)
    nn = nn_distances(xy, 1)[:, 0]
    med = np.nanmedian(nn)
    for f in ("x", "y"):
        v = c[f]
        mad = 1.4826 * np.median(np.abs(v - v.median()))
        if mad <= 0:
            continue
        z = (v - v.median()) / mad
        for (h, r), zz, d in zip(c.iterrows(), z, nn):
            if abs(zz) >= p["robust_z"] and d > 10 * med:
                ctx.add("COL-016", "WARNING", ctx.collar.name,
                        f"{f.upper()} = {r[f]:.1f} is an outlier (robust z {zz:.1f}; nearest collar {d:.0f} m); check for a dropped or transposed digit.",
                        f"{f.upper()} = {r[f]:.1f} دادهٔ پرت است (z مقاوم {zz:.1f}؛ نزدیک‌ترین دهانه {d:.0f} متر)؛ احتمال حذف یا جابجایی رقم را بررسی کنید.",
                        hole_id=h, field=f, value=r[f], src_row=int(r["src_row"]))
    lo, hi = p["z_range_m"]
    for h, r in c[(c["z"] < lo) | (c["z"] > hi)].iterrows():
        ctx.add("COL-016", "WARNING", ctx.collar.name, f"Z = {r['z']:g} m is outside the plausible range {lo}…{hi} m.",
                f"Z = {r['z']:g} متر خارج از بازهٔ محتمل {lo} تا {hi} متر است.", hole_id=h, field="z", value=r["z"], src_row=int(r["src_row"]))
    if not ctx.has("dem") and c["z"].notna().sum() >= 10:
        from scipy.spatial import cKDTree
        k = min(9, len(c))
        _, idx = cKDTree(xy).query(xy, k=k)
        zz = c["z"].to_numpy(float)
        for n_i, (h, r) in enumerate(c.iterrows()):
            nb = zz[idx[n_i, 1:]]
            nb = nb[np.isfinite(nb)]
            if len(nb) < 4 or not np.isfinite(zz[n_i]):
                continue
            mad = 1.4826 * np.median(np.abs(nb - np.median(nb)))
            mad = max(mad, 5.0)
            rz = (zz[n_i] - np.median(nb)) / mad
            if abs(rz) >= p["robust_z"]:
                ctx.add("COL-016", "WARNING", ctx.collar.name,
                        f"Z = {zz[n_i]:g} m differs from its 8 nearest collars (median {np.median(nb):.0f} m, robust z {rz:.1f}).",
                        f"Z = {zz[n_i]:g} متر با ۸ دهانهٔ نزدیک (میانه {np.median(nb):.0f} متر) ناسازگار است (z مقاوم {rz:.1f}).",
                        hole_id=h, field="z", value=zz[n_i], src_row=int(r["src_row"]))
