"""LIT, GEO and DEN rules (03 §2.7, §2.8, §2.12)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core.normalise import header_key
from .base import rule


def _lev1(a: str, b: str) -> bool:
    if abs(len(a) - len(b)) > 1 or a == b:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


@rule("LIT-001", ("lithology",))
def lit_001(ctx):
    for t in ctx.by_kind("lithology"):
        df = t.df[t.df["lith_code"].notna()]
        metres = df.assign(L=df["to_m"] - df["from_m"]).groupby("lith_code")["L"].sum()
        counts = df["lith_code"].value_counts()
        ctx.stats.setdefault("lith_inventory", {})[t.name] = pd.DataFrame({"count": counts, "metres": metres}).sort_values("metres", ascending=False)
        fold = {}
        for code in counts.index:
            fold.setdefault(header_key(code), []).append(code)
        for k, codes in fold.items():
            if len(codes) > 1:
                ctx.add("LIT-001", "WARNING", t.name, f"Codes {', '.join(codes)} differ only by case, spaces or punctuation: harmonise them.",
                        f"کدهای {', '.join(codes)} فقط در حروف بزرگ و کوچک، فاصله یا نشانه‌گذاری تفاوت دارند: یکسان‌سازی شوند.",
                        field="lith_code", value=" / ".join(codes), suggested_fix="Add a dictionary alias to the most frequent code.")
        codes = list(counts.index)
        for i, a in enumerate(codes):
            for b in codes[i + 1:]:
                if len(a) >= 3 and _lev1(a.upper(), b.upper()) and header_key(a) != header_key(b):
                    rare, common = (a, b) if counts[a] < counts[b] else (b, a)
                    if counts[rare] < 0.05 * counts[common]:
                        ctx.add("LIT-001", "WARNING", t.name, f"Code '{rare}' ({counts[rare]}×) is one character from '{common}' ({counts[common]}×): probable typing variant.",
                                f"کد «{rare}» ({counts[rare]} بار) فقط یک نویسه با «{common}» ({counts[common]} بار) تفاوت دارد: احتمالاً اشتباه تایپی.",
                                field="lith_code", value=rare)


@rule("LIT-002", ("lithology",))
def lit_002(ctx):
    p = ctx.p("LIT-002")
    for t in ctx.by_kind("lithology"):
        df = t.df[t.df["from_m"].notna() & t.df["to_m"].notna()].sort_values(["hole_id", "from_m"])
        L = df["to_m"] - df["from_m"]
        thin = (L > 0) & (L < p["thin_m"])
        for i in df.index[thin]:
            r = df.loc[i]
            ctx.add("LIT-002", "INFO", t.name, f"Thin interval {L[i]:.2f} m of '{r['lith_code']}'.", f"بازهٔ نازک {L[i]:.2f} متری از «{r['lith_code']}».",
                    hole_id=r["hole_id"], from_m=r["from_m"], to_m=r["to_m"], value=round(float(L[i]), 3), src_row=int(r["src_row"]))
        share = thin.groupby(df["hole_id"]).mean()
        for h, s in share[share > p["thin_share_frac"]].items():
            ctx.add("LIT-002", "WARNING", t.name, f"{s:.0%} of the intervals in this hole are thinner than {p['thin_m']} m: over-split logging.",
                    f"{s:.0%} از بازه‌های این گمانه نازک‌تر از {p['thin_m']} متر هستند: لاگ بیش از حد تفکیک شده است.", hole_id=h, value=round(float(s), 3))
        same = df["hole_id"].eq(df["hole_id"].shift()) & df["lith_code"].eq(df["lith_code"].shift()) & \
            ((df["from_m"] - df["to_m"].shift()).abs() <= ctx.eps)
        for i in df.index[same]:
            r = df.loc[i]
            ctx.add("LIT-002", "INFO", t.name, f"Consecutive intervals with the same code '{r['lith_code']}' are not merged.",
                    f"بازه‌های پیاپی با کد یکسان «{r['lith_code']}» ادغام نشده‌اند.", hole_id=r["hole_id"], from_m=r["from_m"],
                    to_m=r["to_m"], src_row=int(r["src_row"]))


@rule("LIT-003", ("lithology",))
def lit_003(ctx):
    cover = {c.upper() for c in ctx.p("LIT-003")["cover_codes"]}
    for t in ctx.by_kind("lithology"):
        df = t.df[t.df["lith_code"].notna()].sort_values(["hole_id", "from_m"])
        for h, g in df.groupby("hole_id"):
            is_cover = g["lith_code"].str.upper().isin(cover).to_numpy()
            if not is_cover.any() or is_cover.all():
                continue
            first_bed = np.argmax(~is_cover)
            below = np.where(is_cover[first_bed:])[0]
            for k in below:
                r = g.iloc[first_bed + k]
                ctx.add("LIT-003", "WARNING", t.name, f"Cover unit '{r['lith_code']}' logged at {r['from_m']:g} m below bedrock.",
                        f"واحد پوششی «{r['lith_code']}» در عمق {r['from_m']:g} متر زیر سنگ بستر لاگ شده است.", hole_id=h,
                        from_m=r["from_m"], to_m=r["to_m"], field="lith_code", value=r["lith_code"], src_row=int(r["src_row"]))


def _cr_rqd(t):
    df = t.df.copy()
    cr = df["cr_pct"] if "cr_pct" in df else pd.Series(np.nan, index=df.index)
    rqd = df["rqd_pct"] if "rqd_pct" in df else pd.Series(np.nan, index=df.index)
    if cr.notna().any() and cr.dropna().max() <= 1.0:
        cr = cr * 100
    if rqd.notna().any() and rqd.dropna().max() <= 1.0:
        rqd = rqd * 100
    run = df["run_length_m"] if "run_length_m" in df and df["run_length_m"].notna().any() else df["to_m"] - df["from_m"]
    cr_c = 100 * df["recovered_length_m"] / run if "recovered_length_m" in df else pd.Series(np.nan, index=df.index)
    rqd_c = 100 * df["rqd_length_m"] / run if "rqd_length_m" in df else pd.Series(np.nan, index=df.index)
    return df, cr.astype(float), rqd.astype(float), cr_c.astype(float), rqd_c.astype(float)


@rule("GEO-001", ("geotech",))
def geo_001(ctx):
    tol = ctx.p("GEO-001")["cr_tol_pct"]
    for t in ctx.by_kind("geotech"):
        df, cr, rqd, cr_c, _ = _cr_rqd(t)
        used = cr_c.where(cr_c.notna(), cr)
        for i in used.index[used.notna() & ((used < 0) | (used > 100))]:
            v = used[i]
            sev = "ERROR" if v < 0 or v > 100 + tol else "INFO"
            ctx.add("GEO-001", sev, t.name, f"Core recovery {v:.1f} % is outside 0–100 %.", f"بازیافت مغزه {v:.1f} درصد خارج از بازهٔ ۰ تا ۱۰۰ است.",
                    hole_id=df.at[i, "hole_id"], from_m=df.at[i, "from_m"], to_m=df.at[i, "to_m"], field="cr_pct", value=round(float(v), 2),
                    src_row=int(df.at[i, "src_row"]))


@rule("GEO-002", ("geotech",))
def geo_002(ctx):
    tol = ctx.p("GEO-002")["tol_pct"]
    for t in ctx.by_kind("geotech"):
        df, cr, rqd, cr_c, rqd_c = _cr_rqd(t)
        cu, ru = cr_c.where(cr_c.notna(), cr), rqd_c.where(rqd_c.notna(), rqd)
        bad = ru.notna() & ((ru < 0) | (ru > 100 + tol) | (cu.notna() & (ru > cu + tol)))
        for i in ru.index[bad]:
            ctx.add("GEO-002", "ERROR", t.name, f"RQD {ru[i]:.1f} % exceeds core recovery {cu[i]:.1f} % or 100 %.",
                    f"RQD برابر {ru[i]:.1f} درصد از بازیافت مغزه ({cu[i]:.1f} درصد) یا ۱۰۰ درصد بیشتر است.", hole_id=df.at[i, "hole_id"],
                    from_m=df.at[i, "from_m"], to_m=df.at[i, "to_m"], field="rqd_pct", value=round(float(ru[i]), 2), src_row=int(df.at[i, "src_row"]))


@rule("GEO-003", ("geotech",))
def geo_003(ctx):
    p = ctx.p("GEO-003")
    for t in ctx.by_kind("geotech"):
        df, cr, rqd, cr_c, rqd_c = _cr_rqd(t)
        for name, rec, calc in (("CR", cr, cr_c), ("RQD", rqd, rqd_c)):
            d = (rec - calc).abs()
            for i in d.index[d > p["diff_tol_pct"]]:
                ctx.add("GEO-003", "WARNING", t.name, f"Recorded {name} {rec[i]:.1f} % differs from {calc[i]:.1f} % recomputed from the measured lengths.",
                        f"{name} ثبت‌شده {rec[i]:.1f} درصد با مقدار بازمحاسبه از طول‌های اندازه‌گیری‌شده ({calc[i]:.1f} درصد) تفاوت دارد.",
                        hole_id=df.at[i, "hole_id"], from_m=df.at[i, "from_m"], to_m=df.at[i, "to_m"], field=name.lower() + "_pct",
                        value=round(float(rec[i]), 2), expected=round(float(calc[i]), 2), src_row=int(df.at[i, "src_row"]))
        if "run_length_m" in df and df["run_length_m"].notna().any():
            dl = (df["run_length_m"] - (df["to_m"] - df["from_m"])).abs()
            for i in dl.index[dl > p["len_tol_m"]]:
                ctx.add("GEO-003", "WARNING", t.name, f"Run length {df.at[i, 'run_length_m']:g} m ≠ To − From ({df.at[i, 'to_m'] - df.at[i, 'from_m']:g} m).",
                        f"طول ران {df.at[i, 'run_length_m']:g} متر با اختلاف عمق «تا» و «از» برابر نیست.", hole_id=df.at[i, "hole_id"],
                        from_m=df.at[i, "from_m"], field="run_length_m", src_row=int(df.at[i, "src_row"]))


@rule("GEO-004", ("geotech", "assay"))
def geo_004(ctx):
    from scipy.stats import mannwhitneyu
    p = ctx.p("GEO-004")
    keys = ctx.params.get("key_analytes", [])
    geo = []
    for t in ctx.by_kind("geotech"):
        df, cr, _, cr_c, _ = _cr_rqd(t)
        geo.append(pd.DataFrame({"hole_id": df["hole_id"], "from_m": df["from_m"], "to_m": df["to_m"], "cr": cr_c.where(cr_c.notna(), cr)}))
    g = pd.concat(geo).dropna()
    for t in ctx.by_kind("assay"):
        a = next((x for x in t.analytes if x.analyte in keys and not x.partial), None)
        if a is None:
            continue
        s = t.df[["hole_id", "from_m", "to_m"]].assign(v=a.parsed["value_policy"]).dropna()
        s["mid"] = (s["from_m"] + s["to_m"]) / 2
        rec = pd.Series(np.nan, index=s.index)
        for h, gg in g.groupby("hole_id"):
            ss = s[s["hole_id"] == h]
            if ss.empty:
                continue
            gg = gg.sort_values("from_m")
            k = np.searchsorted(gg["from_m"].to_numpy(), ss["mid"].to_numpy(), side="right") - 1
            ok = (k >= 0) & (ss["mid"].to_numpy() < gg["to_m"].to_numpy()[np.clip(k, 0, None)])
            rec.loc[ss.index[ok]] = gg["cr"].to_numpy()[k[ok]]
        lo, hi = s["v"][rec < p["low_pct"]], s["v"][rec >= p["high_pct"]]
        lo, hi = lo[lo > 0], hi[hi > 0]
        ctx.stats.setdefault("recovery_grade", {})[t.name] = (a.analyte, rec, s["v"])
        if len(lo) >= p["min_n_per_class"] and len(hi) >= p["min_n_per_class"]:
            llo, lhi = np.log10(lo), np.log10(hi)
            pv = mannwhitneyu(llo, lhi).pvalue
            pooled = np.sqrt((llo.var() + lhi.var()) / 2)
            d = abs(llo.mean() - lhi.mean()) / pooled if pooled > 0 else 0.0
            mde = 3.86 * np.sqrt(2.0 / min(len(llo), len(lhi)))    # 03 §1.9: effect must also exceed the MDE
            if pv < p["alpha"] and d >= mde:
                direction = "higher" if lo.median() > hi.median() else "lower"
                ctx.add("GEO-004", "WARNING", t.name,
                        f"{a.analyte} is {direction} in low-recovery samples (CR < {p['low_pct']} %: median {lo.median():.3g}, n {len(lo)}) than in high-recovery samples (≥ {p['high_pct']} %: median {hi.median():.3g}, n {len(hi)}); Mann–Whitney p = {pv:.1e}. Check for recovery-induced sampling bias.",
                        f"عیار {a.analyte} در نمونه‌های با بازیافت پایین ({'بیشتر' if direction == 'higher' else 'کمتر'}) از نمونه‌های با بازیافت بالاست (آزمون من–ویتنی p = {pv:.1e}). اریبی ناشی از بازیافت بررسی شود.",
                        field=a.column, value=f"p={pv:.1e}")


@rule("DEN-001", ("density",))
def den_001(ctx):
    p = ctx.p("DEN-001")
    lo, hi = p["abs_bounds_gcm3"]
    for t in ctx.by_kind("density"):
        d = t.df["density"]
        if d.dropna().median() > 100:
            d = d / 1000.0
        med = d.median()
        mad = 1.4826 * (d - med).abs().median()
        for i in d.index[d.notna()]:
            v = d[i]
            if v < lo or v > hi:
                sev, en, fa = "ERROR", f"outside the physical range {lo}–{hi} g/cm³", f"خارج از بازهٔ فیزیکی {lo} تا {hi} گرم بر سانتی‌متر مکعب"
            elif mad > 0 and abs(v - med) > p["k_mad"] * mad:
                sev, en, fa = "WARNING", f"far from the median {med:.2f} g/cm³", f"دور از میانهٔ {med:.2f} گرم بر سانتی‌متر مکعب"
            else:
                continue
            r = t.df.loc[i]
            ctx.add("DEN-001", sev, t.name, f"Density {v:.2f} g/cm³ is {en}.", f"چگالی {v:.2f} گرم بر سانتی‌متر مکعب {fa} است.",
                    hole_id=r["hole_id"], from_m=r.get("from_m", r.get("depth_m")), field="density", value=round(float(v), 3),
                    src_row=int(r["src_row"]))
