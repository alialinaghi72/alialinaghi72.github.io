"""SUR rules: downhole survey integrity and deviation (03 §2.3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..analysis.desurvey import dogleg_deg, resample
from ..core.normalise import hole_key
from .base import rule


def _sv(ctx):
    return ctx.survey.df, ctx.survey.name


def _sentinel_mask(ctx, s: pd.Series) -> pd.Series:
    return s.isin(ctx.p("SUR-020").get("sentinels", []))


@rule("SUR-001", ("survey", "collar"))
def sur_001(ctx):
    s, tn = _sv(ctx)
    ids, keys = ctx.collar_ids, ctx.collar_keys()
    for h, g in s[s["hole_id"].notna() & ~s["hole_id"].isin(ids)].groupby("hole_id"):
        k = keys.get(hole_key(h))
        hint_en = f" It matches collar '{k}' after case/separator folding: a join error." if k else ""
        hint_fa = f" پس از یکسان‌سازی با دهانهٔ «{k}» منطبق است: خطای اتصال." if k else ""
        ctx.add("SUR-001", "ERROR", tn, f"{len(g)} survey rows for hole '{h}', which is not in the collar table.{hint_en}",
                f"{len(g)} ردیف انحراف‌سنجی برای گمانهٔ «{h}» که در جدول دهانه نیست.{hint_fa}", hole_id=h, field="hole_id",
                value=len(g), src_row=int(g["src_row"].iloc[0]))


@rule("SUR-002", ("survey",))
def sur_002(ctx):
    s, tn = _sv(ctx)
    p, eps = ctx.p("SUR-002"), ctx.eps
    for h, g in s[s["depth_m"].notna()].groupby("hole_id"):
        g = g.sort_values("depth_m")
        d = g["depth_m"].to_numpy()
        same = np.where(np.diff(d) <= eps)[0]
        for i in same:
            a, b = g.iloc[i], g.iloc[i + 1]
            daz = abs(((a["azimuth"] - b["azimuth"]) + 180) % 360 - 180) if np.isfinite(a["azimuth"]) and np.isfinite(b["azimuth"]) else 0
            ddip = abs(a["dip"] - b["dip"]) if np.isfinite(a["dip"]) and np.isfinite(b["dip"]) else 0
            if daz <= p["dup_angle_tol_deg"] and ddip <= p["dup_angle_tol_deg"]:
                ctx.add("SUR-002", "INFO", tn, f"Duplicate survey station at {a['depth_m']:g} m with identical values.",
                        f"ایستگاه تکراری در عمق {a['depth_m']:g} متر با مقادیر یکسان.", hole_id=h, from_m=a["depth_m"],
                        field="depth_m", value=a["depth_m"], src_row=int(b["src_row"]), suggested_fix="Remove one copy (change set).")
            else:
                ctx.add("SUR-002", "ERROR", tn,
                        f"Two survey stations at {a['depth_m']:g} m disagree (az {a['azimuth']:g}/{b['azimuth']:g}, dip {a['dip']:g}/{b['dip']:g}).",
                        f"دو ایستگاه در عمق {a['depth_m']:g} متر مقادیر متفاوت دارند (آزیموت {a['azimuth']:g}/{b['azimuth']:g}، شیب {a['dip']:g}/{b['dip']:g}).",
                        hole_id=h, from_m=a["depth_m"], field="depth_m", value=a["depth_m"], src_row=int(b["src_row"]))


@rule("SUR-003", ("survey",))
def sur_003(ctx):
    s, tn = _sv(ctx)
    bad = s["dip"].notna() & ~_sentinel_mask(ctx, s["dip"]) & (s["dip"].abs() > 90)
    for i, r in s[bad].iterrows():
        ctx.add("SUR-003", "ERROR", tn, f"Dip {r['dip']:g}° is outside −90…+90°.", f"شیب {r['dip']:g} درجه خارج از بازهٔ ۹۰- تا ۹۰+ است.",
                hole_id=r["hole_id"], from_m=r["depth_m"], field="dip", value=r["dip"], src_row=int(r["src_row"]))


@rule("SUR-004", ("survey",))
def sur_004(ctx):
    s, tn = _sv(ctx)
    a = s["azimuth"]
    m = a.notna() & ~_sentinel_mask(ctx, a) & ((a < 0) | (a >= 360))
    for i, r in s[m].iterrows():
        v = r["azimuth"]
        if v == 360:
            sev, en, fa, fix = "INFO", "Azimuth 360° (normalised to 0°).", "آزیموت ۳۶۰ درجه (به صفر یکسان می‌شود).", None
        else:
            sev = "ERROR"
            fix = "Subtract 360 (declination added without modulo)" if 360 < v <= 720 else ("Add 360 (west-negative notation)" if -360 <= v < 0 else None)
            en, fa = f"Azimuth {v:g}° is outside 0–360°.", f"آزیموت {v:g} درجه خارج از بازهٔ ۰ تا ۳۶۰ است."
        ctx.add("SUR-004", sev, tn, en, fa, hole_id=r["hole_id"], from_m=r["depth_m"], field="azimuth", value=v,
                src_row=int(r["src_row"]), suggested_fix=fix)


@rule("SUR-005", ("survey",))
def sur_005(ctx):
    s, tn = _sv(ctx)
    p = ctx.p("SUR-005")
    d = s[s["dip"].notna() & ~_sentinel_mask(ctx, s["dip"]) & (s["dip"].abs() > p["near_horizontal_deg"]) & (s["dip"].abs() <= 90)]
    if ctx.dip_convention == "POSITIVE_DOWN_CONVERTED":
        ctx.add("SUR-005", "WARNING", tn, "All dips are positive: the survey uses positive-down dips. They were converted to the negative-down convention for desurvey (confirm).",
                "همهٔ شیب‌ها مثبت‌اند: شیب مثبت به معنای رو به پایین فرض شد و برای محاسبهٔ مسیر به قرارداد منفی رو به پایین تبدیل شد (تأیید کنید).",
                field="dip", value="POSITIVE_DOWN")
    sign = np.sign(d["dip"])
    for h, g in sign.groupby(d["hole_id"]):
        if g.nunique() > 1:
            rows = d.loc[g.index]
            ctx.add("SUR-005", "ERROR", tn, f"Hole mixes positive and negative dips ({(g > 0).sum()} positive, {(g < 0).sum()} negative).",
                    f"گمانه شیب‌های مثبت و منفی را با هم دارد ({(g > 0).sum()} مثبت، {(g < 0).sum()} منفی).", hole_id=h,
                    field="dip", value=f"{rows['dip'].min():g}…{rows['dip'].max():g}", src_row=int(rows["src_row"].iloc[0]))
    per_hole = sign.groupby(d["hole_id"]).agg(lambda x: x.iloc[0] if x.nunique() == 1 else 0)
    pos, neg = (per_hole > 0).sum(), (per_hole < 0).sum()
    if pos and neg and ctx.dip_convention != "POSITIVE_DOWN_CONVERTED":
        minority = per_hole[per_hole > 0] if pos < neg else per_hole[per_hole < 0]
        ctx.add("SUR-005", "ERROR", tn, f"{pos} holes use positive dips and {neg} negative: mixed dip-sign conventions (minority: {', '.join(map(str, minority.index[:10]))}).",
                f"{pos} گمانه شیب مثبت و {neg} گمانه شیب منفی دارند: قرارداد علامت شیب مختلط است.", field="dip",
                value=f"{pos}+/{neg}-", hole_id=minority.index[0])


@rule("SUR-006", ("survey", "collar"))
def sur_006(ctx):
    s, tn = _sv(ctx)
    p = ctx.p("SUR-006")
    eoh = ctx.collar_u["eoh_m"] if "eoh_m" in ctx.collar_u else pd.Series(dtype=float)
    over = s["depth_m"] - s["hole_id"].map(eoh)
    for i, r in s[over > 0].iterrows():
        o = over[i]
        sev = "ERROR" if o > p["survey_overrun_tol_m"] else "INFO"
        ctx.add("SUR-006", sev, tn, f"Survey station at {r['depth_m']:g} m is {o:.2f} m beyond EOH.",
                f"ایستگاه انحراف‌سنجی در عمق {r['depth_m']:g} متر، {o:.2f} متر پایین‌تر از عمق نهایی است.", hole_id=r["hole_id"],
                from_m=r["depth_m"], field="depth_m", value=r["depth_m"], src_row=int(r["src_row"]))


def _groups(ctx):
    s, _ = _sv(ctx)
    s = s[s["depth_m"].notna() & (s["depth_m"] >= 0)]
    return s.sort_values(["hole_id", "depth_m"]).groupby("hole_id")


@rule("SUR-007", ("survey",))
def sur_007(ctx):
    _, tn = _sv(ctx)
    lim = ctx.p("SUR-007")["first_station_max_m"]
    for h, g in _groups(ctx):
        first = g["depth_m"].iloc[0]
        if first > lim:
            has_c = h in ctx.collar_ids and np.isfinite(ctx.collar_u.loc[h].get("dip", np.nan))
            note = "the collar orientation is used for the top of the hole" if has_c else "the top of the hole is extrapolated from the first station"
            note_fa = "جهت دهانه برای بخش بالایی به کار رفته است" if has_c else "بخش بالایی از نخستین ایستگاه برون‌یابی شده است"
            ctx.add("SUR-007", "WARNING", tn, f"First survey station at {first:g} m; {note}.", f"نخستین ایستگاه در عمق {first:g} متر است؛ {note_fa}.",
                    hole_id=h, from_m=first, field="depth_m", value=first, src_row=int(g["src_row"].iloc[0]))


@rule("SUR-008", ("survey", "collar"))
def sur_008(ctx):
    _, tn = _sv(ctx)
    p = ctx.p("SUR-008")
    eoh = ctx.collar_u["eoh_m"] if "eoh_m" in ctx.collar_u else pd.Series(dtype=float)
    for h, g in _groups(ctx):
        d = np.r_[0.0, g["depth_m"].to_numpy()]
        gaps = np.diff(d)
        for k in np.where(gaps > p["max_spacing_m"])[0]:
            ctx.add("SUR-008", "WARNING", tn, f"Survey gap of {gaps[k]:.0f} m between {d[k]:g} and {d[k + 1]:g} m.",
                    f"فاصلهٔ {gaps[k]:.0f} متری بین ایستگاه‌های {d[k]:g} و {d[k + 1]:g} متر.", hole_id=h, from_m=d[k], to_m=d[k + 1],
                    field="depth_m", value=round(gaps[k], 1))
        e = eoh.get(h, np.nan)
        if np.isfinite(e) and e > 0:
            ext = e - d[-1]
            if ext > p["extrap_max_m"] or ext > p["extrap_max_frac"] * e:
                ctx.add("SUR-008", "WARNING", tn, f"Last station at {d[-1]:g} m: the bottom {ext:.0f} m of the trace is extrapolated.",
                        f"آخرین ایستگاه در عمق {d[-1]:g} متر است: {ext:.0f} متر پایانی مسیر برون‌یابی شده است.", hole_id=h,
                        from_m=d[-1], to_m=e, field="depth_m", value=round(ext, 1))


@rule("SUR-009", ("survey",))
def sur_009(ctx):
    _, tn = _sv(ctx)
    p = ctx.p("SUR-009")
    eoh = ctx.collar_u["eoh_m"] if ctx.has("collar") and "eoh_m" in ctx.collar_u else pd.Series(dtype=float)
    for h, g in _groups(ctx):
        length = eoh.get(h, g["depth_m"].max())
        if len(g) >= 2 and length > p["min_length_m"]:
            if g["azimuth"].max() - g["azimuth"].min() <= p["const_tol_deg"] and g["dip"].max() - g["dip"].min() <= p["const_tol_deg"]:
                ctx.add("SUR-009", "WARNING", tn, f"All {len(g)} stations are identical (az {g['azimuth'].iloc[0]:g}, dip {g['dip'].iloc[0]:g}): design values, not a measured survey.",
                        f"همهٔ {len(g)} ایستگاه یکسان‌اند (آزیموت {g['azimuth'].iloc[0]:g}، شیب {g['dip'].iloc[0]:g}): مقادیر طراحی هستند، نه برداشت واقعی.",
                        hole_id=h, field="azimuth,dip", value=len(g), suggested_fix="Survey the hole; count it as unsurveyed in JORC T1.08.")


def _pairs(g):
    a, p, d = g["azimuth"].to_numpy(float), g["dip"].to_numpy(float), g["depth_m"].to_numpy(float)
    ok = np.isfinite(a) & np.isfinite(p)
    return a[ok], p[ok], d[ok], g["src_row"].to_numpy()[ok]


@rule("SUR-010", ("survey",))
def sur_010(ctx):
    _, tn = _sv(ctx)
    p = ctx.p("SUR-010")
    for h, g in _groups(ctx):
        a, dip, d, rows = _pairs(g)
        if len(a) < 2:
            continue
        beta = dogleg_deg(a[:-1], dip[:-1], a[1:], dip[1:])
        dmd = np.diff(d)
        dls = np.where(dmd >= p["min_dmd_m"], beta * 30.0 / np.maximum(dmd, 1e-9), beta)
        for k in np.where(dls >= p["warn_deg_30m"])[0]:
            sev = "ERROR" if dls[k] >= p["error_deg_30m"] else "WARNING"
            ctx.add("SUR-010", sev, tn, f"Dogleg {dls[k]:.1f}°/30 m between {d[k]:g} and {d[k + 1]:g} m (angle change {beta[k]:.1f}°).",
                    f"شدت خمیدگی {dls[k]:.1f} درجه بر ۳۰ متر بین عمق {d[k]:g} و {d[k + 1]:g} متر (تغییر زاویه {beta[k]:.1f} درجه).",
                    hole_id=h, from_m=d[k], to_m=d[k + 1], field="azimuth,dip", value=round(dls[k], 2), src_row=int(rows[k + 1]))


@rule("SUR-011", ("survey",))
def sur_011(ctx):
    _, tn = _sv(ctx)
    p = ctx.p("SUR-011")
    for h, g in _groups(ctx):
        a, dip, d, rows = _pairs(g)
        if len(dip) < 2:
            continue
        dd, dmd = np.abs(np.diff(dip)), np.maximum(np.diff(d), 1e-9)
        for k in np.where((dd > p["max_dip_change_deg"]) | (dd * 30 / dmd > p["max_dip_change_deg_30m"]))[0]:
            ctx.add("SUR-011", "WARNING", tn, f"Dip changes by {dd[k]:.1f}° between {d[k]:g} and {d[k + 1]:g} m.",
                    f"شیب بین عمق {d[k]:g} و {d[k + 1]:g} متر {dd[k]:.1f} درجه تغییر می‌کند.", hole_id=h, from_m=d[k], to_m=d[k + 1],
                    field="dip", value=round(dd[k], 2), src_row=int(rows[k + 1]))


@rule("SUR-012", ("survey",))
def sur_012(ctx):
    _, tn = _sv(ctx)
    p = ctx.p("SUR-012")
    for h, g in _groups(ctx):
        a, dip, d, rows = _pairs(g)
        if len(a) < 2:
            continue
        da = np.abs((np.diff(a) + 180) % 360 - 180)
        dmd = np.maximum(np.diff(d), 1e-9)
        steep = (dip[:-1] < p["suppress_steeper_than_dip_deg"]) | (dip[1:] < p["suppress_steeper_than_dip_deg"])
        hit = ((da > p["max_az_change_deg"]) | (da * 30 / dmd > p["max_az_change_deg_30m"])) & ~steep
        for k in np.where(hit)[0]:
            ctx.add("SUR-012", "WARNING", tn, f"Azimuth changes by {da[k]:.1f}° between {d[k]:g} and {d[k + 1]:g} m.",
                    f"آزیموت بین عمق {d[k]:g} و {d[k + 1]:g} متر {da[k]:.1f} درجه تغییر می‌کند.", hole_id=h, from_m=d[k], to_m=d[k + 1],
                    field="azimuth", value=round(da[k], 2), src_row=int(rows[k + 1]))


@rule("SUR-013", ("survey",))
def sur_013(ctx):
    _, tn = _sv(ctx)
    p = ctx.p("SUR-013")
    for h, g in _groups(ctx):
        a, dip, d, rows = _pairs(g)
        if len(a) < 3:
            continue
        au = np.degrees(np.unwrap(np.radians(a)))
        med = pd.Series(au).rolling(5, center=True, min_periods=3).median().to_numpy()
        n = 0
        for i in range(1, len(au) - 1):
            dm, dp = au[i] - au[i - 1], au[i + 1] - au[i]
            if abs(dm) > p["spike_deg"] and abs(dp) > p["spike_deg"] and np.sign(dm) != np.sign(dp) \
                    and abs(au[i] - med[i]) > p["spike_deg"] and dip[i] >= -85:
                n += 1
                ctx.add("SUR-013", "WARNING", tn, f"Azimuth spike at {d[i]:g} m ({a[i]:g}° between {a[i - 1]:g}° and {a[i + 1]:g}°): probable magnetic interference or reading error.",
                        f"جهش آزیموت در عمق {d[i]:g} متر ({a[i]:g} درجه بین {a[i - 1]:g} و {a[i + 1]:g}): احتمال تداخل مغناطیسی یا خطای قرائت.",
                        hole_id=h, from_m=d[i], field="azimuth", value=a[i], src_row=int(rows[i]),
                        suggested_fix="Exclude the station from desurvey (change set) or re-survey with a gyro.")
        if n >= 3:
            ctx.add("SUR-013", "ERROR", tn, f"{n} azimuth spikes in one hole: survey unreliable (consider a gyro re-survey).",
                    f"{n} جهش آزیموت در یک گمانه: برداشت قابل اعتماد نیست (برداشت مجدد با ژیروسکوپ را در نظر بگیرید).", hole_id=h, value=n)


@rule("SUR-015", ("traces",))
def sur_015(ctx):
    p = ctx.p("SUR-015")
    tn = ctx.survey.name if ctx.survey is not None else ctx.collar.name
    for h, tr in ctx.traces.items():
        tt = ctx.traces_tan.get(h)
        if tt is None or len(tr) < 3:
            continue
        diff = float(np.linalg.norm(tr[["x", "y", "z"]].iloc[-1].to_numpy() - tt[["x", "y", "z"]].iloc[-1].to_numpy()))
        if diff > p["eoh_diff_m"]:
            ctx.add("SUR-015", "INFO", tn, f"End-of-hole positions from minimum curvature and tangential desurvey differ by {diff:.1f} m.",
                    f"موقعیت انتهای گمانه با روش کمینهٔ انحنا و روش مماسی {diff:.1f} متر اختلاف دارد.", hole_id=h, value=round(diff, 2))


@rule("SUR-016", ("traces",))
def sur_016(ctx):
    from scipy.spatial import cKDTree
    p = ctx.p("SUR-016")
    tn = ctx.survey.name if ctx.survey is not None else ctx.collar.name
    pts, hid, dep = [], [], []
    for i, (h, tr) in enumerate(ctx.traces.items()):
        xyz = resample(tr, p["step_m"])
        dd = np.arange(len(xyz)) * p["step_m"]
        keep = dd > p["collar_zone_m"]
        pts.append(xyz[keep])
        hid.append(np.full(keep.sum(), i))
        dep.append(dd[keep])
    if not pts:
        return
    P, H, D = np.vstack(pts), np.concatenate(hid), np.concatenate(dep)
    names = list(ctx.traces)
    if len(P) > 1:
        pairs = cKDTree(P).query_pairs(p["cross_dist_m"], output_type="ndarray")
        if len(pairs):
            pairs = pairs[H[pairs[:, 0]] != H[pairs[:, 1]]]
            seen = set()
            for i, j in pairs:
                a, b = sorted((H[i], H[j]))
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                dist = float(np.linalg.norm(P[i] - P[j]))
                ctx.add("SUR-016", "ERROR", tn, f"Traces of {names[a]} and {names[b]} pass within {dist:.2f} m of each other (depth {D[i]:.0f} m / {D[j]:.0f} m): probable survey or collar error.",
                        f"مسیر گمانه‌های {names[a]} و {names[b]} در فاصلهٔ {dist:.2f} متری از هم می‌گذرند (عمق {D[i]:.0f} و {D[j]:.0f} متر): احتمال خطای انحراف‌سنجی یا مختصات.",
                        hole_id=names[a], from_m=float(D[i]), field="trace", value=names[b])
    if ctx.dem is not None:
        zt = ctx.dem.sample(P[:, 0], P[:, 1])
        out = np.isfinite(zt) & (P[:, 2] > zt + p["exit_tol_m"])
        done = set()
        for k in np.where(out)[0]:
            if H[k] in done:
                continue
            done.add(H[k])
            ctx.add("SUR-016", "ERROR", tn, f"Trace exits above the topographic surface at {D[k]:.0f} m depth ({P[k, 2] - zt[k]:.1f} m above).",
                    f"مسیر گمانه در عمق {D[k]:.0f} متر از سطح توپوگرافی بالاتر می‌رود ({P[k, 2] - zt[k]:.1f} متر).",
                    hole_id=names[H[k]], from_m=float(D[k]), field="trace", value=round(float(P[k, 2] - zt[k]), 2))


@rule("SUR-017", ("survey",))
def sur_017(ctx):
    s, tn = _sv(ctx)
    for i, r in s[s["depth_m"] < 0].iterrows():
        ctx.add("SUR-017", "ERROR", tn, f"Negative survey depth {r['depth_m']:g} m.", f"عمق منفی {r['depth_m']:g} متر.", hole_id=r["hole_id"],
                field="depth_m", value=r["depth_m"], src_row=int(r["src_row"]))
    for h, g in s[s["depth_m"].notna()].groupby("hole_id", sort=False):
        dec = np.where(np.diff(g["depth_m"].to_numpy()) < 0)[0]
        if len(dec):
            r = g.iloc[dec[0] + 1]
            ctx.add("SUR-017", "WARNING", tn, f"Survey rows are out of depth order (row {int(r['src_row'])}); possibly a block of rows of another hole.",
                    f"ردیف‌های انحراف‌سنجی به ترتیب عمق نیستند (ردیف {int(r['src_row'])})؛ ممکن است بلوکی از ردیف‌ها مربوط به گمانهٔ دیگری باشد.",
                    hole_id=h, field="depth_m", value=r["depth_m"], src_row=int(r["src_row"]))


@rule("SUR-020", ("survey",))
def sur_020(ctx):
    s, tn = _sv(ctx)
    p = ctx.p("SUR-020")
    sent = p.get("sentinels", [])
    for i, r in s.iterrows():
        dip, az, d = r["dip"], r["azimuth"], r["depth_m"]
        if not np.isfinite(d) or d in sent:
            ctx.add("SUR-020", "ERROR", tn, "Survey depth missing or a placeholder value.", "عمق ایستگاه وجود ندارد یا مقدار جانشین است.",
                    hole_id=r["hole_id"], field="depth_m", value=d, src_row=int(r["src_row"]))
            continue
        if not np.isfinite(dip) or dip in sent:
            ctx.add("SUR-020", "ERROR", tn, f"Dip missing or placeholder at {d:g} m.", f"شیب در عمق {d:g} متر وجود ندارد یا مقدار جانشین است.",
                    hole_id=r["hole_id"], from_m=d, field="dip", value=dip, src_row=int(r["src_row"]))
        elif "azimuth" in s and (not np.isfinite(az) or az in sent):
            steep = dip < p["steep_dip_cutoff_deg"]
            ctx.add("SUR-020", "INFO" if steep else "WARNING", tn,
                    f"Azimuth missing at {d:g} m" + (" (immaterial for a near-vertical station)." if steep else "."),
                    f"آزیموت در عمق {d:g} متر وجود ندارد" + (" (برای ایستگاه تقریباً قائم اهمیتی ندارد)." if steep else "."),
                    hole_id=r["hole_id"], from_m=d, field="azimuth", value=az, src_row=int(r["src_row"]))
