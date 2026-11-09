"""SUR rules: downhole survey integrity and deviation (03 §2.3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..analysis.desurvey import dogleg_deg, resample
from ..core.normalise import hole_key
from .base import closest_collars, rule


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
        near = closest_collars(h, ids)
        ctx.add("SUR-001", "ERROR", tn, f"{len(g)} survey rows for hole '{h}', which is not in the collar table.{hint_en}",
                f"{len(g)} ردیف انحراف‌سنجی برای گمانهٔ «{h}» که در جدول دهانه نیست.{hint_fa}", hole_id=h, field="hole_id",
                value=len(g), src_row=int(g["src_row"].iloc[0]), fix_class="ID_MAP" if k else None,
                suggested_fix=(f"Closest collar IDs (suggestion only): {', '.join(near)}" if near else "Add the collar record or correct the hole ID."))


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
                        field="depth_m", value=a["depth_m"], src_row=int(b["src_row"]), suggested_fix="Remove one copy (fix class SURVEY_DUP_IDENTICAL).",
                        fix_class="SURVEY_DUP_IDENTICAL")
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
        fc = "AZ_360" if v == 360 else ("AZ_WRAP" if (360 < v <= 720 or -360 <= v < 0) else None)
        ctx.add("SUR-004", sev, tn, en, fa, hole_id=r["hole_id"], from_m=r["depth_m"], field="azimuth", value=v,
                src_row=int(r["src_row"]), suggested_fix=fix, fix_class=fc)


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
    """SRV-01: no station at 0 m. States what the desurvey assumes between the collar and the first station: the collar
    orientation when the collar has azimuth and dip, otherwise the first station's direction extended to the collar.
    WARNING (Minor); the message adds "far from the collar" beyond `first_station_max_m` (30 m)."""
    _, tn = _sv(ctx)
    lim = ctx.p("SUR-007")["first_station_max_m"]
    for h, g in _groups(ctx):
        first = g["depth_m"].iloc[0]
        if first <= ctx.eps:
            continue
        cu = ctx.collar_u.loc[h] if h in ctx.collar_ids else None
        has_c = cu is not None and np.isfinite(cu.get("dip", np.nan)) and np.isfinite(cu.get("azimuth", np.nan))
        if has_c:
            note = f"desurvey uses the collar orientation (az {cu['azimuth']:g}°, dip {cu['dip']:g}°) from 0 to {first:g} m"
            note_fa = f"برای ۰ تا {first:g} متر جهت دهانه (آزیموت {cu['azimuth']:g}، شیب {cu['dip']:g}) به کار رفته است"
        else:
            note = f"desurvey extends the first station's direction from {first:g} m up to the collar"
            note_fa = f"جهت نخستین ایستگاه از عمق {first:g} متر تا دهانه امتداد داده شده است"
        far = f" The first station is far from the collar (> {lim:g} m)." if first > lim else ""
        far_fa = f" نخستین ایستگاه از دهانه دور است (بیش از {lim:g} متر)." if first > lim else ""
        ctx.add("SUR-007", "WARNING", tn, f"No survey station at 0 m (first at {first:g} m): {note}.{far}",
                f"ایستگاهی در عمق صفر نیست (نخستین در {first:g} متر): {note_fa}.{far_fa}",
                hole_id=h, from_m=0.0, to_m=first, field="depth_m", value=first, src_row=int(g["src_row"].iloc[0]))


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
    # SRV-15: holes desurveyed as a straight line (no station or a single station) longer than `straight_min_m`
    if ctx.has("collar"):
        counts = _groups(ctx).size()
        for h, length in eoh.items():
            n = int(counts.get(h, 0))
            if n <= 1 and np.isfinite(length) and length > p["straight_min_m"]:
                ctx.add("SUR-009", "INFO", tn, f"{'No survey station' if n == 0 else 'A single survey station'} over {length:g} m: the trace is a straight-line assumption.",
                        f"{'هیچ ایستگاهی' if n == 0 else 'تنها یک ایستگاه'} در طول {length:g} متر: مسیر گمانه خط راست فرض شده است.",
                        hole_id=h, field="depth_m", value=n, to_m=float(length))


def _near_vertical(ctx, dip) -> np.ndarray:
    """SRV-11: inclination from vertical I = 90° + dip below `near_vertical_incl_deg` (3°): azimuth is meaningless there."""
    lim = float(ctx.p("SUR-012").get("near_vertical_incl_deg", 3.0))
    return (90.0 + np.asarray(dip, float)) < lim


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
    """Azimuth change between stations above `max_az_change_deg` (10°) or `max_az_change_deg_30m` (20°/30 m), WARNING.
    SRV-11: stations with inclination below 3° are excluded from every azimuth-based check (SUR-012, SUR-013, SUR-023,
    SUR-027); one INFO per hole states that the suppression was applied."""
    _, tn = _sv(ctx)
    p = ctx.p("SUR-012")
    for h, g in _groups(ctx):
        a, dip, d, rows = _pairs(g)
        if len(a) < 1:
            continue
        nv = _near_vertical(ctx, dip)
        if nv.any():
            ctx.add("SUR-012", "INFO", tn, f"{int(nv.sum())} of {len(nv)} stations are near-vertical (inclination < {p.get('near_vertical_incl_deg', 3):g}°): azimuth-based checks were suppressed there.",
                    f"{int(nv.sum())} ایستگاه از {len(nv)} تقریباً قائم‌اند (انحراف از قائم کمتر از {p.get('near_vertical_incl_deg', 3):g} درجه): کنترل‌های مبتنی بر آزیموت برای آن‌ها اجرا نشد.",
                    hole_id=h, field="azimuth", value=int(nv.sum()))
        if len(a) < 2:
            continue
        da = np.abs((np.diff(a) + 180) % 360 - 180)
        dmd = np.maximum(np.diff(d), 1e-9)
        steep = nv[:-1] | nv[1:]
        hit = ((da > p["max_az_change_deg"]) | (da * 30 / dmd > p["max_az_change_deg_30m"])) & ~steep
        for k in np.where(hit)[0]:
            ctx.add("SUR-012", "WARNING", tn, f"Azimuth changes by {da[k]:.1f}° between {d[k]:g} and {d[k + 1]:g} m.",
                    f"آزیموت بین عمق {d[k]:g} و {d[k + 1]:g} متر {da[k]:.1f} درجه تغییر می‌کند.", hole_id=h, from_m=d[k], to_m=d[k + 1],
                    field="azimuth", value=round(da[k], 2), src_row=int(rows[k + 1]))


@rule("SUR-013", ("survey",))
def sur_013(ctx):
    """SRV-09: neighbour-inconsistent station. Station i deviates by more than `dev_deg` (2°) from the direction
    interpolated between stations i−1 and i+1, while i−1 and i+1 agree within `agree_dls_30m` (1°/30 m). Likely a typo
    or magnetic interference. ERROR (Major); `unreliable_n` (3) such stations in one hole add a hole-level ERROR.
    Near-vertical stations (SRV-11) are compared on dip only."""
    from ..analysis.desurvey import _unit
    _, tn = _sv(ctx)
    p = ctx.p("SUR-013")
    for h, g in _groups(ctx):
        a, dip, d, rows = _pairs(g)
        if len(a) < 3:
            continue
        u = _unit(a, dip)
        nv = _near_vertical(ctx, dip)
        n = 0
        for i in range(1, len(a) - 1):
            span, f0 = d[i + 1] - d[i - 1], d[i] - d[i - 1]
            if span <= ctx.eps or f0 <= ctx.eps or d[i + 1] - d[i] <= ctx.eps:
                continue                                   # duplicate depths are SUR-002
            agree = np.degrees(np.arccos(np.clip(u[i - 1] @ u[i + 1], -1, 1))) * 30.0 / span
            if agree > p["agree_dls_30m"]:
                continue
            f = f0 / span
            if nv[i]:
                dev = abs(dip[i] - ((1 - f) * dip[i - 1] + f * dip[i + 1]))
            else:
                v = (1 - f) * u[i - 1] + f * u[i + 1]
                v /= np.linalg.norm(v)
                dev = float(np.degrees(np.arccos(np.clip(u[i] @ v, -1, 1))))
            if dev > p["dev_deg"]:
                n += 1
                ctx.add("SUR-013", "ERROR", tn,
                        f"Station at {d[i]:g} m (az {a[i]:g}°, dip {dip[i]:g}°) deviates {dev:.1f}° from its neighbours at {d[i - 1]:g} and {d[i + 1]:g} m, which agree: probable typo or magnetic interference.",
                        f"ایستگاه عمق {d[i]:g} متر (آزیموت {a[i]:g}، شیب {dip[i]:g}) {dev:.1f} درجه با ایستگاه‌های مجاور ({d[i - 1]:g} و {d[i + 1]:g} متر) که با هم سازگارند اختلاف دارد: احتمال اشتباه تایپی یا تداخل مغناطیسی.",
                        hole_id=h, from_m=d[i], field="azimuth,dip", value=round(dev, 2), src_row=int(rows[i]),
                        suggested_fix="Check the station against the survey certificate; exclude it from desurvey or re-survey with a gyro.")
        if n >= p["unreliable_n"]:
            ctx.add("SUR-013", "ERROR", tn, f"{n} neighbour-inconsistent stations in one hole: the survey is unreliable (consider a gyro re-survey).",
                    f"{n} ایستگاه ناسازگار با ایستگاه‌های مجاور در یک گمانه: برداشت قابل اعتماد نیست (برداشت مجدد با ژیروسکوپ را در نظر بگیرید).", hole_id=h, value=n)


@rule("SUR-023", ("survey", "collar"))
def sur_023(ctx):
    """SRV-07: collar azimuth/dip against the first survey station within `max_first_depth_m` (50 m). ERROR (Major) when
    dip differs by more than `dip_tol_deg` (5°) or azimuth by more than `az_tol_deg` (10°, wrapped at 0/360; not tested
    for near-vertical holes)."""
    _, tn = _sv(ctx)
    p = ctx.p("SUR-023")
    cu = ctx.collar_u
    if "azimuth" not in cu or "dip" not in cu:
        return
    for h, g in _groups(ctx):
        if h not in cu.index:
            continue
        ca, cd = cu.at[h, "azimuth"], cu.at[h, "dip"]
        a, dip, d, rows = _pairs(g)
        if not len(d) or d[0] > p["max_first_depth_m"]:
            continue
        msgs_en, msgs_fa, worst = [], [], 0.0
        if np.isfinite(cd) and abs(cd - dip[0]) > p["dip_tol_deg"]:
            msgs_en.append(f"dip {cd:g}° vs {dip[0]:g}°")
            msgs_fa.append(f"شیب {cd:g} در برابر {dip[0]:g}")
            worst = max(worst, abs(cd - dip[0]))
        if np.isfinite(ca) and not _near_vertical(ctx, [dip[0]])[0] and not (np.isfinite(cd) and _near_vertical(ctx, [cd])[0]):
            daz = abs((ca - a[0] + 180) % 360 - 180)
            if daz > p["az_tol_deg"]:
                msgs_en.append(f"azimuth {ca:g}° vs {a[0]:g}°")
                msgs_fa.append(f"آزیموت {ca:g} در برابر {a[0]:g}")
                worst = max(worst, daz)
        if msgs_en:
            ctx.add("SUR-023", "ERROR", tn, f"Collar orientation disagrees with the first station at {d[0]:g} m: {'; '.join(msgs_en)}.",
                    f"جهت دهانه با نخستین ایستگاه (عمق {d[0]:g} متر) ناسازگار است: {'؛ '.join(msgs_fa)}.", hole_id=h, from_m=d[0],
                    field="azimuth,dip", value=round(worst, 2), src_row=int(rows[0]),
                    suggested_fix="Check the planned vs surveyed collar orientation; the desurvey uses the collar values above the first station.")


def _north(v) -> str | None:
    if not isinstance(v, str) or not v.strip():
        return None
    t = v.strip().upper()
    if t.startswith("M") or "مغناطیس" in v:
        return "MAGNETIC"
    if t.startswith("T") or "جغرافیا" in v or "حقیقی" in v:
        return "TRUE"
    if t.startswith("G") or t.startswith("UTM") or "شبکه" in v:
        return "GRID"
    return "UNKNOWN:" + v.strip()


@rule("SUR-014", ("survey",))
def sur_014(ctx):
    """SRV-12: azimuth north reference. (a) Undeclared (no `north_ref` field and no profile `north_reference`): WARNING.
    (b) Mixed references in one project: ERROR. (c) When magnetic and corrected azimuths both exist, their difference
    must equal the declination (TRUE) or declination − grid convergence (GRID) within `tol_deg` (1°); without a
    declination parameter, holes differing from the project median correction by more than `tol_deg` are flagged.
    ERROR (Major)."""
    s, tn = _sv(ctx)
    p = ctx.p("SUR-014")
    refs = []
    if "north_ref" in s:
        refs += [x for x in s["north_ref"].map(_north).dropna()]
    if ctx.has("collar") and "north_ref" in ctx.collar_u:
        refs += [x for x in ctx.collar_u["north_ref"].map(_north).dropna()]
    declared = ctx.params.get("north_reference")
    kinds = sorted(set(refs))
    if not kinds and not declared:
        ctx.add("SUR-014", "WARNING", tn, "The azimuth north reference (magnetic, true or grid) is not declared in the data or the profile.",
                "مرجع شمال آزیموت‌ها (مغناطیسی، جغرافیایی یا شبکه) نه در داده‌ها و نه در پروفایل اعلام شده است.", field="north_ref",
                suggested_fix="Add a north-reference column or set `north_reference` in the profile.")
    if len(kinds) > 1:
        ctx.add("SUR-014", "ERROR", tn, f"Mixed azimuth north references in the project: {', '.join(kinds)}.",
                f"مرجع‌های شمال مختلف در پروژه: {', '.join(kinds)}.", field="north_ref", value=", ".join(kinds))
    ref = (kinds[0] if len(kinds) == 1 else None) or (str(declared).upper() if declared else None)
    if "azimuth_mag" not in s or "azimuth" not in s:
        return
    both = s[s["azimuth_mag"].notna() & s["azimuth"].notna()]
    if both.empty:
        return
    diff = ((both["azimuth"] - both["azimuth_mag"] + 180) % 360) - 180
    decl = p.get("declination_deg")
    if decl is not None:
        expected = float(decl) - (float(p.get("grid_convergence_deg") or 0.0) if ref == "GRID" else 0.0)
        if ref == "MAGNETIC":
            expected = 0.0
        basis = f"expected {expected:+.2f}° ({ref or 'reference unknown'}: declination {float(decl):+.2f}°)"
    else:
        expected = float(diff.median())
        basis = f"project median correction {expected:+.2f}° (no declination given)"
    off = (diff - expected).abs()
    for h, g in off[off > p["tol_deg"]].groupby(both.loc[off.index[off > p["tol_deg"]], "hole_id"]):
        r = both.loc[g.index[0]]
        ctx.add("SUR-014", "ERROR", tn, f"{len(g)} stations: corrected minus magnetic azimuth = {diff[g.index[0]]:+.2f}°, {basis}.",
                f"{len(g)} ایستگاه: اختلاف آزیموت اصلاح‌شده و مغناطیسی {diff[g.index[0]]:+.2f} درجه است، در حالی که {basis}.",
                hole_id=h, from_m=r["depth_m"], field="azimuth,azimuth_mag", value=round(float(diff[g.index[0]]), 2),
                src_row=int(r["src_row"]))


_MAG_TOOL = r"mag|eastman|single.?shot|multi.?shot|\bems\b|ez.?shot|ez.?trac|tropari|compass|camera"


@rule("SUR-027", ("survey",))
def sur_027(ctx):
    """SRV-13: magnetic interference indicators. (a) Total field strength (`mag_field`) differs from the expected value
    (`expected_field_nt`, or the project median) by more than `field_tol_nt` (300 nT). (b) On magnetic instruments,
    azimuth swings above `az_swing_deg` (5°) between consecutive stations while dip is stable within `dip_stable_deg`
    (0.5°). WARNING (Minor). Gyro surveys and near-vertical stations are skipped."""
    s, tn = _sv(ctx)
    p = ctx.p("SUR-027")
    if "mag_field" in s and s["mag_field"].notna().any():
        b = s["mag_field"]
        ref = p.get("expected_field_nt")
        ref = float(ref) if ref is not None else float(b.median())
        bad = (b - ref).abs() > p["field_tol_nt"]
        for i, r in s[bad & b.notna()].iterrows():
            ctx.add("SUR-027", "WARNING", tn, f"Magnetic field {r['mag_field']:.0f} nT differs from {ref:.0f} nT by more than {p['field_tol_nt']:g} nT: magnetic azimuth unreliable.",
                    f"میدان مغناطیسی {r['mag_field']:.0f} نانوتسلا بیش از {p['field_tol_nt']:g} با مقدار مرجع {ref:.0f} اختلاف دارد: آزیموت مغناطیسی قابل اعتماد نیست.",
                    hole_id=r["hole_id"], from_m=r["depth_m"], field="mag_field", value=r["mag_field"], src_row=int(r["src_row"]))
    if "instrument" not in s:
        return
    inst = s["instrument"].astype("string").fillna("")
    magnetic = inst.str.contains(_MAG_TOOL, case=False, regex=True) & ~inst.str.contains("gyro", case=False)
    for h, g in s[magnetic].sort_values(["hole_id", "depth_m"]).groupby("hole_id"):
        a, dip, d, rows = _pairs(g)
        if len(a) < 2:
            continue
        nv = _near_vertical(ctx, dip)
        da = np.abs((np.diff(a) + 180) % 360 - 180)
        dd = np.abs(np.diff(dip))
        for k in np.where((da > p["az_swing_deg"]) & (dd <= p["dip_stable_deg"]) & ~(nv[:-1] | nv[1:]))[0]:
            ctx.add("SUR-027", "WARNING", tn, f"Azimuth swings {da[k]:.1f}° between {d[k]:g} and {d[k + 1]:g} m while dip is stable ({dd[k]:.2f}°) on a magnetic instrument: possible magnetic interference.",
                    f"آزیموت بین عمق {d[k]:g} و {d[k + 1]:g} متر {da[k]:.1f} درجه تغییر می‌کند در حالی که شیب ثابت است ({dd[k]:.2f} درجه)؛ ابزار مغناطیسی: احتمال تداخل مغناطیسی.",
                    hole_id=h, from_m=d[k], to_m=d[k + 1], field="azimuth", value=round(float(da[k]), 2), src_row=int(rows[k + 1]))


@rule("SUR-015", ("traces",))
def sur_015(ctx):
    """SRV-14: desurvey sensitivity. EOH XYZ from tangential, balanced tangential and minimum curvature
    (RF = (2/β)·tan(β/2), RF = 1 as β → 0); the largest pairwise distance per hole. One INFO summary for the project;
    WARNING (Minor) for holes above `eoh_diff_m` (2 m)."""
    p = ctx.p("SUR-015")
    tn = ctx.survey.name if ctx.survey is not None else ctx.collar.name
    rows = []
    for h, tr in ctx.traces.items():
        tt, tb = ctx.traces_tan.get(h), ctx.traces_bt.get(h)
        if tt is None or tb is None or len(tr) < 2:
            continue
        e = [x[["x", "y", "z"]].iloc[-1].to_numpy(float) for x in (tr, tt, tb)]
        d_mt, d_mb, d_tb = (float(np.linalg.norm(e[0] - e[1])), float(np.linalg.norm(e[0] - e[2])), float(np.linalg.norm(e[1] - e[2])))
        rows.append({"hole_id": h, "eoh_m": float(tr["depth_m"].iloc[-1]), "mincurv_vs_tangent_m": d_mt,
                     "mincurv_vs_baltan_m": d_mb, "tangent_vs_baltan_m": d_tb, "max_m": max(d_mt, d_mb, d_tb)})
    df = pd.DataFrame(rows)
    ctx.stats["desurvey_sensitivity"] = df
    if df.empty:
        return
    top = df.loc[df["max_m"].idxmax()]
    ctx.add("SUR-015", "INFO", tn, f"Desurvey sensitivity at EOH (tangential, balanced tangential, minimum curvature): median {df['max_m'].median():.2f} m, maximum {top['max_m']:.2f} m ({top['hole_id']}); {int((df['max_m'] > p['eoh_diff_m']).sum())} holes above {p['eoh_diff_m']:g} m.",
            f"حساسیت موقعیت انتهای گمانه به روش محاسبهٔ مسیر (مماسی، مماسی متوازن، کمینهٔ انحنا): میانه {df['max_m'].median():.2f} متر، بیشینه {top['max_m']:.2f} متر ({top['hole_id']}).",
            field="desurvey", value=round(float(df["max_m"].max()), 3))
    for r in df[df["max_m"] > p["eoh_diff_m"]].itertuples():
        ctx.add("SUR-015", "WARNING", tn, f"End-of-hole position depends on the desurvey method by up to {r.max_m:.1f} m (min. curvature vs tangential {r.mincurv_vs_tangent_m:.1f} m, vs balanced tangential {r.mincurv_vs_baltan_m:.1f} m).",
                f"موقعیت انتهای گمانه تا {r.max_m:.1f} متر به روش محاسبهٔ مسیر وابسته است.", hole_id=r.hole_id, value=round(r.max_m, 2))


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
