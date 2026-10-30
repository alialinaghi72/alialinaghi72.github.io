"""ASY rules (03 §2.5): units, codes, impossible values, mixed units, ratios, outliers, detection limits."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..analysis.assay import TO_PPM
from ..io.mapping import OXIDES
from .base import rule
from .interval import QC_TYPES

MAJORS = ["SiO2", "TiO2", "Al2O3", "Fe2O3", "Fe2O3T", "FeO", "MnO", "MgO", "CaO", "Na2O", "K2O", "P2O5", "Cr2O3", "BaO",
          "SrO", "SO3", "V2O5", "LOI"]


def _orig_mask(t) -> pd.Series:
    if "qc_class" in t.df:
        return ~t.df["qc_class"].isin(QC_TYPES)
    return pd.Series(True, index=t.df.index)


def _pct(a) -> pd.Series:
    return a.parsed["value"] * TO_PPM[a.unit] / 1e4


def _row_ctx(t, i):
    r = t.df.loc[i]
    return dict(hole_id=r["hole_id"], from_m=r.get("from_m"), to_m=r.get("to_m"), src_row=int(r["src_row"]))


@rule("ASY-001", ("analytes",))
def asy_001(ctx):
    for t in ctx.tables:
        for a in t.analytes:
            if not a.unit_declared:
                ctx.add("ASY-001", "WARNING", t.name, f"Column '{a.column}': no unit in the header; inferred {a.unit} ({a.unit_evidence}). Confirm.",
                        f"ستون «{a.column}»: واحد در سرستون نیامده است؛ واحد {a.unit} استنتاج شد ({a.unit_evidence}). تأیید کنید.",
                        field=a.column, value=a.unit, suggested_fix="Confirm or correct the unit in the mapping dialog.")


@rule("ASY-002", ("analytes",))
def asy_002(ctx):
    for t in ctx.tables:
        m = _orig_mask(t)
        for a in t.analytes:
            f = a.parsed.loc[m, "flag"]
            n = len(f)
            counts = f.value_counts()
            parts = {k: int(counts.get(k, 0)) for k in ("BDL", "ODL", "TXT", "SNT", "NA")}
            if sum(v for k, v in parts.items() if k != "NA") == 0:
                continue
            codes = a.parsed.loc[m & (a.parsed["flag"] == "TXT"), "code"].value_counts().head(6)
            ctext = ", ".join(f"'{k}'×{v}" for k, v in codes.items())
            sev = "WARNING" if n and parts["TXT"] / n > 0.01 else "INFO"
            ctx.add("ASY-002", sev, t.name,
                    f"Column '{a.column}': {parts['BDL']} below detection, {parts['ODL']} over-range, {parts['TXT']} text codes {ctext}, {parts['SNT']} sentinels, {parts['NA']} blank (not analysed). BDL values use ½ DL in statistics.",
                    f"ستون «{a.column}»: {parts['BDL']} زیر حد تشخیص، {parts['ODL']} بالای حد، {parts['TXT']} کد متنی، {parts['SNT']} مقدار جانشین، {parts['NA']} خالی (آنالیزنشده). در آمار، نصف حد تشخیص به کار رفته است.",
                    field=a.column, value=parts["BDL"] + parts["ODL"] + parts["TXT"] + parts["SNT"])


@rule("ASY-003", ("analytes",))
def asy_003(ctx):
    p = ctx.p("ASY-003")
    for t in ctx.tables:
        m = _orig_mask(t)
        for a in t.analytes:
            v = a.parsed["value"].where(m & (a.parsed["flag"] == "VAL"))
            ppm = v * TO_PPM[a.unit]
            bad_neg = v < 0
            bad_hi = ppm > 1e6
            if a.analyte == "Au":
                bad_hi |= ppm > p["au_max_ppm"]
            for i in v.index[bad_neg | bad_hi]:
                why_en = "negative grade" if v[i] < 0 else f"above the physical maximum ({v[i]:g} {a.unit})"
                why_fa = "عیار منفی" if v[i] < 0 else f"بیش از حد فیزیکی ممکن ({v[i]:g} {a.unit})"
                ctx.add("ASY-003", "ERROR", t.name, f"{a.analyte}: impossible value, {why_en}.", f"{a.analyte}: مقدار ناممکن، {why_fa}.",
                        field=a.column, value=v[i], **_row_ctx(t, i))
        ox = [a for a in t.analytes if a.analyte in MAJORS and not a.partial]
        names = {a.analyte for a in ox}
        if len(ox) >= 5:
            tot = sum(_pct(a).where(a.parsed["flag"] == "VAL").fillna(0)
                      for a in ox if not (a.analyte in ("FeO", "Fe2O3") and "Fe2O3T" in names))
            for i in tot.index[(tot > p["total_max_pct"]) & m]:
                ctx.add("ASY-003", "ERROR", t.name, f"Major-oxide total {tot[i]:.1f} % exceeds {p['total_max_pct']} %.",
                        f"مجموع اکسیدهای اصلی {tot[i]:.1f} درصد و بیش از {p['total_max_pct']} درصد است.", field="oxide total",
                        value=round(float(tot[i]), 2), **_row_ctx(t, i))


def _group_shift(x: pd.Series, groups: pd.Series, p):
    """Group medians of log values split by the widest gap; return (minority groups, factor, value share) or None."""
    d = pd.DataFrame({"x": x, "g": groups}).dropna()
    size = d.groupby("g")["x"].size()
    med = d.groupby("g")["x"].median()[size >= p.get("min_group_n", 10)].sort_values()
    if len(med) < 6:
        return None
    gaps = med.diff().to_numpy()[1:]
    k = int(np.argmax(gaps)) + 1
    lower, upper = med.iloc[:k], med.iloc[k:]
    sep = float(upper.median() - lower.median())
    if gaps[k - 1] < p.get("group_gap_decades", 1.0) or sep < p.get("group_separation_decades", 2.0):
        return None
    minority = upper if size[upper.index].sum() <= size[lower.index].sum() else lower
    return list(minority.index), 10 ** sep, float(size[minority.index].sum() / size[med.index].sum())


def _two_means(x: np.ndarray):
    lo, hi = np.percentile(x, 25), np.percentile(x, 75)
    for _ in range(50):
        lab = np.abs(x - lo) > np.abs(x - hi)
        if lab.all() or (~lab).all():
            return None
        nlo, nhi = x[~lab].mean(), x[lab].mean()
        if np.isclose(nlo, lo) and np.isclose(nhi, hi):
            break
        lo, hi = nlo, nhi
    return lab, lo, hi


@rule("ASY-004", ("analytes",))
def asy_004(ctx):
    p = ctx.p("ASY-004")
    for t in ctx.tables:
        for a in t.analytes:
            v = a.parsed.loc[(a.parsed["flag"] == "VAL") & (a.parsed["value"] > 0), "value"]
            if len(v) < p["min_n"]:
                continue
            x = np.log10(v.to_numpy())
            res = _two_means(x)
            if res is None:
                continue
            lab, lo, hi = res
            minority = min(lab.mean(), 1 - lab.mean())
            s1, s2 = x[~lab].std(), x[lab].std()
            ashman = np.sqrt(2) * abs(hi - lo) / np.sqrt(s1 ** 2 + s2 ** 2 + 1e-12)
            if hi - lo >= p["min_separation_decades"] and minority >= p["min_minority_frac"] and ashman > 3:
                factor = 10 ** (hi - lo)
                ctx.add("ASY-004", "ERROR", t.name,
                        f"Column '{a.column}' holds two populations about {factor:,.0f}× apart ({minority:.0%} minority): units are probably mixed (e.g. ppb with ppm, or % with ppm).",
                        f"ستون «{a.column}» دو جامعه با اختلاف حدود {factor:,.0f} برابر دارد ({minority:.0%} اقلیت): احتمالاً واحدها مختلط‌اند (مثلاً ppb با ppm یا درصد با ppm).",
                        field=a.column, value=round(float(factor), 1), suggested_fix="Identify the batches in the minority population and convert them by a change set.")
                continue
            # (b) unit mix-ups arrive per lab job or per hole: medians of those groups split into separated clusters
            for gcol in ("batch", "hole_id"):
                if gcol not in t.df:
                    continue
                res = _group_shift(pd.Series(np.log10(v.to_numpy()), index=v.index), t.df.loc[v.index, gcol], p)
                if res is None:
                    continue
                groups, factor, share = res
                name = "batches" if gcol == "batch" else "holes"
                name_fa = "بچ" if gcol == "batch" else "گمانه"
                shown = ", ".join(map(str, groups[:12])) + (" …" if len(groups) > 12 else "")
                ctx.add("ASY-004", "ERROR", t.name,
                        f"Column '{a.column}': {len(groups)} {name} ({share:.0%} of values) have median values about {factor:,.0f}× those of the rest, with no {name[:-2] if gcol == 'batch' else 'hole'}s in between: units are probably mixed ({shown}).",
                        f"ستون «{a.column}»: میانهٔ {len(groups)} {name_fa} ({share:.0%} مقادیر) حدود {factor:,.0f} برابر بقیه است و {name_fa}ی در میانه وجود ندارد: احتمالاً واحدها مختلط‌اند ({shown}).",
                        field=a.column, value=round(float(factor), 1),
                        suggested_fix=f"Check the certificates of these {name}; convert their values by a change set.")
                for g in groups:
                    if gcol == "hole_id":
                        ctx.add("ASY-004", "ERROR", t.name, f"Hole {g}: {a.column} values about {factor:,.0f}× those of other holes (probable unit error).",
                                f"گمانهٔ {g}: مقادیر {a.column} حدود {factor:,.0f} برابر سایر گمانه‌هاست (خطای احتمالی واحد).",
                                hole_id=g, field=a.column, value=round(float(factor), 1))
                break


@rule("ASY-005", ("analytes",))
def asy_005(ctx):
    for t in ctx.tables:
        by_el = {}
        for a in t.analytes:
            by_el.setdefault(a.analyte, []).append(a)
        for el, cols in by_el.items():
            for a in cols:
                odl = a.parsed["flag"] == "ODL"
                for i in a.parsed.index[odl]:
                    other = any(b is not a and b.parsed.at[i, "flag"] == "VAL" for b in cols)
                    if not other:
                        ctx.add("ASY-005", "WARNING", t.name, f"{a.analyte} over range ('{t.raw.at[i, a.column]}') with no over-limit re-assay: the high-grade tail is truncated.",
                                f"{a.analyte} بالای حد بالایی روش («{t.raw.at[i, a.column]}») بدون آنالیز مجدد: دنبالهٔ عیار بالا بریده شده است.",
                                field=a.column, value=t.raw.at[i, a.column], **_row_ctx(t, i),
                                suggested_fix="Request an ore-grade (over-limit) analysis for this sample.")


@rule("ASY-006", ("analytes",))
def asy_006(ctx):
    p = ctx.p("ASY-006")
    for t in ctx.tables:
        tot = {a.analyte: a for a in t.analytes if not a.partial and a.parsed["flag"].eq("VAL").any()}
        part = [a for a in t.analytes if a.partial]
        m = _orig_mask(t)
        if "Fe" in tot and ("Fe2O3" in tot or "FeO" in tot):
            fe = _pct(tot["Fe"])
            calc = 0.6994 * _pct(tot["Fe2O3"]).fillna(0) if "Fe2O3" in tot else 0
            calc = calc + (0.7773 * _pct(tot["FeO"]).fillna(0) if "FeO" in tot else 0)
            rel = (fe - calc).abs() / fe
            for i in rel.index[(rel > p["fe_rel_tol_frac"]) & (fe > 1) & m]:
                ctx.add("ASY-006", "WARNING", t.name, f"Fe {fe[i]:.2f} % vs 0.6994·Fe2O3 + 0.7773·FeO = {calc[i]:.2f} % ({rel[i]:.0%} apart).",
                        f"آهن {fe[i]:.2f} درصد در برابر مقدار محاسبه‌شده از Fe2O3 و FeO = {calc[i]:.2f} درصد ({rel[i]:.0%} اختلاف).",
                        field="Fe", value=round(float(fe[i]), 3), **_row_ctx(t, i))
        for a in part:
            if a.analyte in tot:
                tv, pv = _pct(tot[a.analyte]), _pct(a)
                for i in pv.index[(pv > tv * (1 + p["partial_tol_frac"])) & tv.notna() & m]:
                    ctx.add("ASY-006", "WARNING", t.name, f"Partial {a.column} = {pv[i]:.3g} % exceeds total {a.analyte} = {tv[i]:.3g} %.",
                            f"مقدار بخشی {a.column} = {pv[i]:.3g} درصد بیش از کل {a.analyte} = {tv[i]:.3g} درصد است.",
                            field=a.column, value=round(float(pv[i]), 4), **_row_ctx(t, i))
        if "Cu" in tot and "S" in tot:
            cu, s = _pct(tot["Cu"]), _pct(tot["S"])
            ox_mask = pd.Series(False, index=cu.index)
            for a in part:
                if a.analyte == "Cu":
                    ox_mask |= _pct(a) > 0.5 * cu
            bad = (cu > p["cu_min_pct"]) & (s > 0) & (cu > p["cu_s_max_ratio"] * s) & ~ox_mask & m
            for i in cu.index[bad]:
                ctx.add("ASY-006", "WARNING", t.name, f"Cu {cu[i]:.2f} % exceeds {p['cu_s_max_ratio']:g} × S ({s[i]:.2f} %): more Cu than any sulphide can carry (oxide Cu, sample swap or unit error).",
                        f"مس {cu[i]:.2f} درصد بیش از {p['cu_s_max_ratio']:g} برابر گوگرد ({s[i]:.2f} درصد) است: بیش از ظرفیت هر کانی سولفیدی (مس اکسیدی، جابجایی نمونه یا خطای واحد).",
                        field="Cu,S", value=round(float(cu[i] / s[i]), 2), **_row_ctx(t, i))


@rule("ASY-007", ("analytes",))
def asy_007(ctx):
    p = ctx.p("ASY-007")
    for t in ctx.tables:
        m = _orig_mask(t)
        for a in t.analytes:
            v = a.parsed.loc[m & (a.parsed["flag"] == "VAL") & (a.parsed["value"] > 0), "value"]
            if len(v) < 30:
                continue
            lv = np.log10(v)
            q1, q3 = lv.quantile(0.25), lv.quantile(0.75)
            fence = q3 + p["tukey_k"] * (q3 - q1)
            for i in lv.index[lv > fence]:
                ctx.add("ASY-007", "INFO", t.name, f"{a.analyte} = {v[i]:g} {a.unit} is above the log far-out fence ({10 ** fence:.3g}); verify before top-cutting.",
                        f"{a.analyte} = {v[i]:g} {a.unit} بالاتر از مرز داده‌های پرت لگاریتمی ({10 ** fence:.3g}) است؛ پیش از برش عیار بالا بررسی شود.",
                        field=a.column, value=v[i], **_row_ctx(t, i))
            cv = float(v.std() / v.mean()) if v.mean() > 0 else 0
            if cv > p["cv_topcut"]:
                s = np.sort(v.to_numpy())[::-1]
                top10 = s[: max(1, len(s) // 10)].sum() / s.sum()
                ctx.add("ASY-007", "INFO", t.name, f"{a.analyte}: CV = {cv:.2f}; top 10 % of samples hold {top10:.0%} of the metal. Top-cut analysis is recommended (suggestion only).",
                        f"{a.analyte}: ضریب تغییرات {cv:.2f}؛ ۱۰ درصد بالایی نمونه‌ها {top10:.0%} فلز را دارند. تحلیل برش عیار بالا توصیه می‌شود (فقط پیشنهاد).",
                        field=a.column, value=round(cv, 3))


@rule("ASY-011", ("analytes",))
def asy_011(ctx):
    p = ctx.p("ASY-011")
    keys = set(ctx.params.get("key_analytes", []))
    for t in ctx.tables:
        m = _orig_mask(t)
        for a in t.analytes:
            f = a.parsed.loc[m, "flag"]
            rep = f.isin(["VAL", "BDL"]).sum()
            if rep < 20:
                continue
            share = (f == "BDL").sum() / rep
            if a.analyte in keys and not a.partial and share > p["bdl_share_warn_frac"]:
                ctx.add("ASY-011", "WARNING", t.name, f"{share:.0%} of {a.analyte} results are below detection: the method may be too insensitive for the grade range.",
                        f"{share:.0%} از نتایج {a.analyte} زیر حد تشخیص‌اند: روش آنالیز ممکن است برای بازهٔ عیار حساسیت کافی نداشته باشد.",
                        field=a.column, value=round(float(share), 3))
            elif share > p["bdl_share_info_frac"]:
                ctx.add("ASY-011", "INFO", t.name, f"{share:.0%} of {a.analyte} results are below detection.",
                        f"{share:.0%} از نتایج {a.analyte} زیر حد تشخیص‌اند.", field=a.column, value=round(float(share), 3))


@rule("ASY-012", ("analytes",))
def asy_012(ctx):
    for t in ctx.tables:
        for a in t.analytes:
            dl = a.parsed["dl"].dropna()
            if len(dl) < 5:
                continue
            dlm = float(dl.mode().iloc[0])
            v = a.parsed.loc[a.parsed["flag"] == "VAL", "value"]
            below = v[(v > 0) & (v < dlm * (1 - 1e-9))]
            if len(below):
                ctx.add("ASY-012", "WARNING", t.name, f"{len(below)} numeric {a.analyte} values are below the detection limit {dlm:g} {a.unit} reported in the same column.",
                        f"{len(below)} مقدار عددی {a.analyte} کمتر از حد تشخیص {dlm:g} {a.unit} همان ستون است.", field=a.column,
                        value=len(below), expected=f">= {dlm:g}")


@rule("ASY-014", ("analytes",))
def asy_014(ctx):
    for t in ctx.tables:
        for a in t.analytes:
            z = a.parsed[(a.parsed["flag"] == "VAL") & (a.parsed["value"] == 0)]
            if len(z):
                ctx.add("ASY-014", "WARNING", t.name, f"{len(z)} values of exactly 0 in '{a.column}': zero is not a measurement (BDL, not sampled or blank?).",
                        f"{len(z)} مقدار دقیقاً صفر در ستون «{a.column}»: صفر یک اندازه‌گیری نیست (زیر حد تشخیص، نمونه‌برداری‌نشده یا خالی؟).",
                        field=a.column, value=len(z), src_row=int(t.df.loc[z.index[0], "src_row"]))


@rule("ASY-015", ("analytes",))
def asy_015(ctx):
    p = ctx.p("ASY-015")
    for t in ctx.tables:
        ox = [a for a in t.analytes if a.analyte in MAJORS and not a.partial]
        names = {a.analyte for a in ox}
        if len(ox) < 6 or not {"SiO2", "Al2O3"} <= names:
            continue
        vals = [_pct(a).where(a.parsed["flag"] == "VAL") for a in ox if not (a.analyte in ("FeO", "Fe2O3") and "Fe2O3T" in names)]
        tot = sum(v.fillna(0) for v in vals)
        n_rep = sum(v.notna().astype(int) for v in vals)
        for i in tot.index[(tot < p["total_min_pct"]) & (n_rep >= 5) & _orig_mask(t)]:
            ctx.add("ASY-015", "WARNING", t.name, f"Major-oxide total {tot[i]:.1f} % is below {p['total_min_pct']} %: a missing component, LOI or incomplete package.",
                    f"مجموع اکسیدهای اصلی {tot[i]:.1f} درصد و کمتر از {p['total_min_pct']} درصد است: جزء یا LOI ناموجود یا بستهٔ آنالیز ناقص.",
                    field="oxide total", value=round(float(tot[i]), 2), **_row_ctx(t, i))
