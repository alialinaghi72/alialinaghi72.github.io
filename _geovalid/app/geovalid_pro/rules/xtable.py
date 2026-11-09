"""Cross-table consistency (v2 brief F8, category F). Catalogue IDs with the brief IDs as aliases:

  ASY-008  XTB-01  interval logged as mineralised (user-defined codes) without assay coverage
  INT-011  XTB-05  coverage mismatch between tables per hole (and within mineralised zones)
  WTH-001  XTB-06  weathering / oxidation profile inversion downhole
  CRS-001  XTB-07  high grade inside a barren-logged unit; low grade in a logged ore zone
XTB-02/03/04 extend GEO-001, GEO-002 and DEN-001 (logging_rules.py).

Mineralised and barren codes are the user's (profile `mineralised_codes`, `barren_codes`: {field: [codes]}); codes
compare case-insensitively after trimming spaces. Nothing is inferred from code names.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .base import rule
from .interval import QC_TYPES

LOG_FIELDS = ("lith_code", "alt_type", "weathering")
_FAULT = re.compile(r"FAULT|FLT|SHEAR|SHR|GOUGE|گسل|برشی", re.I)
# downhole order: 0 = most weathered. Extra or project codes: profile `weathering_rank` {code: rank}.
RANK = {"LEACHED": 0, "LEACH": 0, "LCH": 0, "LX": 0, "SOIL": 0, "W6": 0, "OXIDE": 1, "OXIDISED": 1, "OXIDIZED": 1, "OX": 1, "OXD": 1, "W5": 1,
        "COMPLETE": 1, "MIXED": 2, "MIX": 2, "MX": 2, "TRANSITION": 2, "TRANSITIONAL": 2, "TRANS": 2, "TR": 2, "PARTIAL": 2, "W4": 2,
        "SUPERGENE": 3, "SUP": 3, "SG": 3, "ENRICHED": 3, "W3": 3, "PRIMARY": 4, "PRI": 4, "HYPOGENE": 4, "HYP": 4, "SULPHIDE": 4,
        "SULFIDE": 4, "SUL": 4, "W2": 4, "FRESH": 5, "FR": 5, "W1": 5,
        "اکسید": 1, "اکسیدی": 1, "مختلط": 2, "انتقالی": 2, "سوپرژن": 3, "غنی‌شده": 3, "سولفیدی": 4, "اولیه": 4, "هیپوژن": 4, "تازه": 5}


def _codes(params: dict, key: str) -> dict[str, set]:
    return {f: {str(c).strip().upper() for c in v} for f, v in (params.get(key) or {}).items() if v}


def _norm(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.upper()


def _union_len(fr: np.ndarray, to: np.ndarray) -> float:
    if len(fr) == 0:
        return 0.0
    o = np.argsort(fr)
    fr, to = fr[o], to[o]
    tot, cs, ce = 0.0, fr[0], to[0]
    for a, b in zip(fr[1:], to[1:]):
        if a > ce:
            tot += ce - cs
            cs, ce = a, b
        else:
            ce = max(ce, b)
    return tot + ce - cs


def _clip_len(fr: np.ndarray, to: np.ndarray, lo: float, hi: float) -> float:
    a, b = np.maximum(fr, lo), np.minimum(to, hi)
    k = b > a
    return _union_len(a[k], b[k])


def _zones(ctx, codes: dict[str, set]) -> pd.DataFrame:
    """Logged intervals whose code is in `codes`, merged per hole where they touch (hole_id, from_m, to_m, codes)."""
    rows = []
    for t in ctx.tables:
        if not t.is_interval or t.kind in ("assay", "density"):
            continue
        for f, cs in codes.items():
            if f not in t.df:
                continue
            df = t.df
            hit = df[_norm(df[f]).isin(cs).fillna(False) & df["hole_id"].notna() & (df["to_m"] > df["from_m"])]
            for r in hit.itertuples():
                rows.append((r.hole_id, float(r.from_m), float(r.to_m), f"{getattr(r, f)}", t.name, int(r.src_row)))
    if not rows:
        return pd.DataFrame(columns=["hole_id", "from_m", "to_m", "codes", "table", "src_row"])
    z = pd.DataFrame(rows, columns=["hole_id", "from_m", "to_m", "codes", "table", "src_row"]).sort_values(["hole_id", "from_m"])
    out = []
    for h, g in z.groupby("hole_id", sort=False):
        cur = None
        for r in g.itertuples():
            if cur and r.from_m <= cur[2] + ctx.eps:
                cur[2] = max(cur[2], r.to_m)
                cur[3].add(r.codes)
            else:
                if cur:
                    out.append(cur)
                cur = [h, r.from_m, r.to_m, {r.codes}, r.table, r.src_row]
        out.append(cur)
    return pd.DataFrame([(a, b, c, ", ".join(sorted(d)), e, f) for a, b, c, d, e, f in out], columns=z.columns)


def _assayed(ctx) -> pd.DataFrame:
    """Routine assay intervals with their state for the key analytes: ANALYSED (any VAL/BDL/ODL) or EXPLAINED
    (only codes such as NS, IS, LNR) or EMPTY."""
    keys = set(ctx.params.get("key_analytes") or [])
    parts = []
    for t in ctx.by_kind("assay"):
        df = t.df
        ok = df["hole_id"].notna() & (df["to_m"] > df["from_m"])
        if "qc_class" in df:
            ok &= ~df["qc_class"].isin(QC_TYPES)
        an = [a for a in t.analytes if not a.partial and (a.analyte in keys or not keys)] or [a for a in t.analytes if not a.partial]
        val = np.zeros(len(df), bool)
        txt = np.zeros(len(df), bool)
        for a in an:
            val |= a.parsed["flag"].isin(["VAL", "BDL", "ODL"]).to_numpy()
            txt |= a.parsed["flag"].isin(["TXT", "SNT"]).to_numpy()
        state = np.where(val, "ANALYSED", np.where(txt, "EXPLAINED", "EMPTY"))
        parts.append(pd.DataFrame({"hole_id": df["hole_id"], "from_m": df["from_m"], "to_m": df["to_m"], "state": state})[ok.to_numpy()])
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["hole_id", "from_m", "to_m", "state"])


@rule("ASY-008", ("assay", "logging", "mineralised_codes"))
def asy_008(ctx):
    """XTB-01. Each zone logged with a mineralised code (profile `mineralised_codes`), merged where intervals touch,
    is compared with the routine assay intervals that hold a result for a key analyte. A zone with no assay at all →
    ERROR; uncovered metres ≥ `min_len_m` inside a partly assayed zone → WARNING; a gap covered only by explained
    codes (NS, IS, LNR, …) → INFO. Silent zero-filling of such gaps dilutes the composite grade."""
    p = ctx.p("ASY-008")
    min_len = float(p.get("min_len_m", 1.0))
    z = _zones(ctx, _codes(ctx.params, "mineralised_codes"))
    if z.empty:
        return
    a = _assayed(ctx)
    by = {h: g for h, g in a.groupby("hole_id")}
    tot_z = tot_gap = 0.0
    for r in z.itertuples():
        L = r.to_m - r.from_m
        g = by.get(r.hole_id, a.iloc[0:0])
        an = g[g["state"] == "ANALYSED"]
        ex = g[g["state"] == "EXPLAINED"]
        cov = _clip_len(an["from_m"].to_numpy(float), an["to_m"].to_numpy(float), r.from_m, r.to_m)
        exp = _clip_len(np.r_[an["from_m"], ex["from_m"]].astype(float), np.r_[an["to_m"], ex["to_m"]].astype(float), r.from_m, r.to_m) - cov
        gap = L - cov - exp
        tot_z += L
        tot_gap += max(gap, 0)
        loc = dict(hole_id=r.hole_id, from_m=r.from_m, to_m=r.to_m, field="mineralised", value=r.codes, src_row=r.src_row, alias="XTB-01")
        if cov <= ctx.eps and gap > ctx.eps:
            ctx.add("ASY-008", "ERROR", r.table, f"Zone logged as mineralised ({r.codes}) {r.from_m:g}–{r.to_m:g} m ({L:.1f} m) has no assay.",
                    f"زون کانه‌دار لاگ‌شده ({r.codes}) در عمق {r.from_m:g} تا {r.to_m:g} متر ({L:.1f} متر) هیچ نتیجهٔ آنالیزی ندارد.", **loc,
                    suggested_fix="Sample the interval, or record why it was not sampled (NS) so composites do not treat it as zero grade.")
        elif gap >= min_len:
            ctx.add("ASY-008", "WARNING", r.table, f"Zone logged as mineralised ({r.codes}) {r.from_m:g}–{r.to_m:g} m: {gap:.1f} of {L:.1f} m have no assay.",
                    f"زون کانه‌دار لاگ‌شده ({r.codes}) در عمق {r.from_m:g} تا {r.to_m:g} متر: {gap:.1f} متر از {L:.1f} متر بدون نتیجهٔ آنالیز است.", **loc)
        elif exp >= min_len:
            ctx.add("ASY-008", "INFO", r.table, f"Zone logged as mineralised ({r.codes}) {r.from_m:g}–{r.to_m:g} m: {exp:.1f} m carry only explained codes (not sampled / insufficient).",
                    f"زون کانه‌دار ({r.codes}) در عمق {r.from_m:g} تا {r.to_m:g} متر: {exp:.1f} متر فقط کد توضیحی (نمونه‌برداری‌نشده یا ناکافی) دارد.", **loc)
    ctx.stats["mineralised_assay_coverage"] = {"zones": int(len(z)), "logged_m": round(tot_z, 2), "unassayed_m": round(tot_gap, 2)}


def _hole_extent(ctx) -> pd.Series:
    c = ctx.collar_u
    return c["eoh_m"].astype(float) if not c.empty and "eoh_m" in c else pd.Series(dtype=float)


@rule("INT-011", ("intervals",))
def int_011(ctx):
    """XTB-05. Per hole and table kind (lithology, alteration, weathering, geotech, assay): covered length (union of
    intervals) against the hole's EOH (or the deepest logged depth). An expected kind (`expected_tables`) covering less
    than `cov_warn_frac` of the hole, or absent from a hole other tables cover → WARNING, one issue per hole listing
    every coverage. Within zones logged as mineralised, a logging kind covering less than `min_cov_mineralised_frac`
    → WARNING (JORC T1.04: share of relevant intersections logged). The holes × tables matrix feeds the heat map."""
    p = ctx.p("INT-011")
    warn, warn_min = float(p.get("cov_warn_frac", 0.9)), float(p.get("min_cov_mineralised_frac", 0.95))
    expected = [k for k in (p.get("expected_tables") or ["lithology", "assay"]) if ctx.by_kind(k)]
    kinds = [k for k in ("lithology", "alteration", "weathering", "geotech", "assay") if ctx.by_kind(k)]
    if len(kinds) < 1:
        return
    eoh = _hole_extent(ctx)
    ivs = {}
    for k in kinds:
        parts = []
        for t in ctx.by_kind(k):
            df = t.df
            ok = df["hole_id"].notna() & (df["to_m"] > df["from_m"])
            if "qc_class" in df:
                ok &= ~df["qc_class"].isin(QC_TYPES)
            parts.append(df.loc[ok, ["hole_id", "from_m", "to_m"]])
        ivs[k] = pd.concat(parts).groupby("hole_id") if parts else None
    holes = sorted(set().union(*[set(g.groups) for g in ivs.values() if g is not None]))
    rows = []
    for h in holes:
        deepest = max(float(g.get_group(h)["to_m"].max()) for g in ivs.values() if g is not None and h in g.groups)
        ref = float(eoh.get(h)) if h in eoh.index and pd.notna(eoh.get(h)) and eoh.get(h) > 0 else deepest
        row = {"hole_id": h, "ref_m": ref}
        for k in kinds:
            g = ivs[k]
            if g is None or h not in g.groups:
                row[k] = 0.0
                continue
            d = g.get_group(h)
            row[k] = min(1.0, _clip_len(d["from_m"].to_numpy(float), d["to_m"].to_numpy(float), 0.0, ref) / ref) if ref > 0 else np.nan
        rows.append(row)
    cov = pd.DataFrame(rows).set_index("hole_id") if rows else pd.DataFrame()
    ctx.stats["coverage"] = cov
    for h, r in cov.iterrows():
        low = [k for k in expected if r[k] < warn]
        if not low:
            continue
        txt = ", ".join(f"{k} {100 * r[k]:.0f} %" for k in kinds)
        ctx.add("INT-011", "WARNING", ctx.by_kind(low[0])[0].name, f"Coverage of {r['ref_m']:.1f} m: {txt}; {', '.join(low)} below {100 * warn:.0f} %.",
                f"پوشش جدول‌ها در طول {r['ref_m']:.1f} متر: {txt}؛ {', '.join(low)} کمتر از {100 * warn:.0f} درصد است.",
                hole_id=h, field="coverage", value=", ".join(f"{k}={r[k]:.2f}" for k in low), alias="XTB-05")
    z = _zones(ctx, _codes(ctx.params, "mineralised_codes"))
    if z.empty:
        return
    logk = [k for k in ("lithology", "alteration", "weathering", "geotech") if k in kinds]
    tot = z.assign(L=z["to_m"] - z["from_m"])["L"].sum()
    for k in logk:
        g = ivs[k]
        got = 0.0
        for r in z.itertuples():
            if g is not None and r.hole_id in g.groups:
                d = g.get_group(r.hole_id)
                got += _clip_len(d["from_m"].to_numpy(float), d["to_m"].to_numpy(float), r.from_m, r.to_m)
        frac = got / tot if tot > 0 else 1.0
        ctx.stats.setdefault("coverage_mineralised", {})[k] = round(frac, 4)
        if frac < warn_min:
            ctx.add("INT-011", "WARNING", ctx.by_kind(k)[0].name, f"{k} covers {100 * frac:.1f} % of the {tot:.1f} m logged as mineralised (target {100 * warn_min:.0f} %).",
                    f"جدول {k} تنها {100 * frac:.1f} درصد از {tot:.1f} متر زون کانه‌دار را پوشش می‌دهد.", field="coverage_mineralised",
                    value=round(frac, 4), alias="XTB-05")


def _rank_map(params: dict) -> dict:
    m = dict(RANK)
    m.update({str(k).strip().upper(): int(v) for k, v in (params.get("weathering_rank") or {}).items()})
    return m


@rule("WTH-001", ("logging",))
def wth_001(ctx):
    """XTB-06. Downhole order of weathering / oxidation codes by rank (0 = leached … 5 = fresh; profile
    `weathering_rank` adds project codes). An inversion is a more weathered zone ≥ `min_inversion_m` thick below a
    fresher one. One issue per hole lists every inversion: WARNING, or INFO when a fault or shear is logged within
    `fault_buffer_m` (deep oxidation along faults is real). Unknown codes are ignored and counted."""
    p = ctx.p("WTH-001")
    mn, buf = float(p.get("min_inversion_m", 2)), float(p.get("fault_buffer_m", 5))
    rank = _rank_map(ctx.params)
    faults = []
    for t in ctx.tables:
        if t.is_interval and "lith_code" in t.df:
            f = t.df[t.df["lith_code"].astype("string").str.contains(_FAULT, na=False)]
            faults.append(f[["hole_id", "from_m", "to_m"]])
    for t in ctx.tables:
        if not t.is_interval or "weathering" not in t.df:
            continue
        df = t.df[t.df["hole_id"].notna() & t.df["weathering"].notna() & (t.df["to_m"] > t.df["from_m"])].copy()
        df["rank"] = _norm(df["weathering"]).map(rank)
        unknown = sorted(set(df.loc[df["rank"].isna(), "weathering"].astype(str)))
        if unknown:
            ctx.stats.setdefault("weathering_unknown_codes", {})[t.name] = unknown[:20]
        df = df[df["rank"].notna()]
        for h, g in df.sort_values(["hole_id", "from_m"]).groupby("hole_id"):
            # merge consecutive intervals of equal rank into zones
            zones = []
            for r in g.itertuples():
                if zones and zones[-1][2] == r.rank:
                    zones[-1][1] = r.to_m
                else:
                    zones.append([r.from_m, r.to_m, r.rank, r.weathering, int(r.src_row)])
            inv, fresh, fresh_code, fresh_at = [], -1, None, None
            for fr, to, rk, code, srow in zones:
                if rk < fresh and to - fr >= mn:
                    inv.append((fr, to, code, fresh_code, fresh_at, srow))
                if rk > fresh:
                    fresh, fresh_code, fresh_at = rk, code, fr
            if not inv:
                continue
            near = False
            for f in faults:
                ff = f[f["hole_id"] == h]
                for fr, to, *_ in inv:
                    if ((ff["from_m"] <= to + buf) & (ff["to_m"] >= fr - buf)).any():
                        near = True
            txt = "; ".join(f"{c} at {fr:g}–{to:g} m below {fc} from {fa:g} m" for fr, to, c, fc, fa, _ in inv)
            sev = "INFO" if near else "WARNING"
            ctx.add("WTH-001", sev, t.name, f"Weathering profile inverted: {txt}." + (" A fault or shear is logged nearby: possibly fault-controlled oxidation." if near else ""),
                    f"وارونگی نیمرخ هوازدگی: {txt}." + (" گسل یا زون برشی در نزدیکی لاگ شده است." if near else ""),
                    hole_id=h, from_m=inv[0][0], to_m=inv[0][1], field="weathering", value=inv[0][2], src_row=inv[0][5], alias="XTB-06")


@rule("CRS-001", ("assay", "logging", "barren_or_mineralised_codes"))
def crs_001(ctx):
    """XTB-07. Per routine sample (code at the sample mid-point): logged barren (profile `barren_codes`) with grade >
    `hi_factor` × the analysis cut-off of a key analyte → INFO; ≥ `cluster_n` consecutive such samples in a hole → one
    WARNING (systematic mislogging or a hole / sample mismatch). A zone logged as mineralised ≥ `min_len_m` whose
    length-weighted grade is below `lo_factor` × cut-off → INFO."""
    from ..analysis import categorical as C
    p = ctx.p("CRS-001")
    hi_f, lo_f, min_len, cl_n = float(p.get("hi_factor", 2)), float(p.get("lo_factor", 0.25)), float(p.get("min_len_m", 2)), int(p.get("cluster_n", 3))
    smp, units, _ = C.sample_table(ctx)
    if smp.empty:
        return
    keys = [a for a in (ctx.params.get("key_analytes") or []) if a in smp]
    cuts = {a: C.cutoff_for(smp, a, units[a], ctx.params) for a in keys if (ctx.params.get("analysis_cutoffs") or {}).get(a)}
    cuts = {a: c for a, c in cuts.items() if c}
    if not cuts:
        return
    barren = _codes(ctx.params, "barren_codes")
    s = smp[["hole_id", "from_m", "to_m", "mid_m", *cuts]].copy()
    code = pd.Series(pd.NA, index=s.index, dtype="object")
    for t in ctx.tables:
        if not t.is_interval or t.kind in ("assay", "density"):
            continue
        for f, cs in barren.items():
            if f in t.df:
                v = C._assign(s, t.df, f)
                hit = _norm(v).isin(cs).fillna(False) & code.isna()
                code[hit] = v[hit]
    s["barren"] = code
    s["ord"] = s.sort_values(["hole_id", "from_m"]).groupby("hole_id").cumcount()     # sample order downhole
    tname = ctx.by_kind("assay")[0].name
    for a, cut in cuts.items():
        hi = s[s["barren"].notna() & (s[a] > hi_f * cut)].sort_values(["hole_id", "from_m"])
        for h, g in hi.groupby("hole_id"):
            pos = g["ord"].to_numpy()          # consecutive = adjacent samples, no other sample between them
            runs, cur = [], [0]
            for k in range(1, len(g)):
                if pos[k] == pos[k - 1] + 1:
                    cur.append(k)
                else:
                    runs.append(cur)
                    cur = [k]
            runs.append(cur)
            for run in runs:
                rr = g.iloc[run]
                if len(run) >= cl_n:
                    ctx.add("CRS-001", "WARNING", tname, f"{len(run)} consecutive samples {rr['from_m'].min():g}–{rr['to_m'].max():g} m logged barren ({', '.join(sorted(set(rr['barren'].astype(str))))}) carry {a} up to {rr[a].max():.3g} (> {hi_f:g} × cut-off {cut:g}): systematic mislogging or a sample/hole mismatch.",
                            f"{len(run)} نمونهٔ پیاپی در عمق {rr['from_m'].min():g} تا {rr['to_m'].max():g} متر که بی‌کانه لاگ شده‌اند عیار {a} بالا دارند.",
                            hole_id=h, from_m=float(rr["from_m"].min()), to_m=float(rr["to_m"].max()), field=a, value=round(float(rr[a].max()), 4), alias="XTB-07")
                else:
                    for r in rr.itertuples():
                        ctx.add("CRS-001", "INFO", tname, f"{a} = {getattr(r, a):.3g} (> {hi_f:g} × cut-off {cut:g}) in a unit logged barren ({r.barren}).",
                                f"عیار {a} برابر {getattr(r, a):.3g} در واحدی که بی‌کانه لاگ شده است ({r.barren}).", hole_id=h, from_m=r.from_m,
                                to_m=r.to_m, field=a, value=round(float(getattr(r, a)), 4), alias="XTB-07")
    z = _zones(ctx, _codes(ctx.params, "mineralised_codes"))
    for r in z.itertuples():
        if r.to_m - r.from_m < min_len:
            continue
        ss = s[(s["hole_id"] == r.hole_id) & (s["mid_m"] >= r.from_m) & (s["mid_m"] < r.to_m)]
        if ss.empty:
            continue
        w = (ss["to_m"] - ss["from_m"]).to_numpy(float)
        for a, cut in cuts.items():
            v = ss[a].to_numpy(float)
            ok = ~np.isnan(v)
            if not ok.any():
                continue
            g = float(np.sum(v[ok] * w[ok]) / np.sum(w[ok]))
            if g < lo_f * cut:
                ctx.add("CRS-001", "INFO", r.table, f"Zone logged as mineralised ({r.codes}) {r.from_m:g}–{r.to_m:g} m averages {a} {g:.3g} (< {lo_f:g} × cut-off {cut:g}).",
                        f"زون کانه‌دار لاگ‌شده ({r.codes}) در عمق {r.from_m:g} تا {r.to_m:g} متر میانگین عیار {a} برابر {g:.3g} دارد (کمتر از {lo_f:g} برابر عیار حد).",
                        hole_id=r.hole_id, from_m=r.from_m, to_m=r.to_m, field=a, value=round(g, 4), alias="XTB-07")
