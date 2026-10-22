"""INT rules: generic interval-table integrity, applied to every interval table (03 §2.4); IMP-011."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core.normalise import hole_key
from .base import rule

QC_TYPES = {"CRM", "BLANK", "FIELD_DUP", "COARSE_DUP", "PULP_DUP", "UMPIRE"}
CONTIGUOUS = {"lithology", "weathering", "alteration", "geotech"}


def originals(t) -> pd.DataFrame:
    """INT rules run on ORIGINAL samples only: duplicates and QC legitimately overlap or have no depths."""
    df = t.df
    if t.kind == "assay" and "qc_class" in df:
        df = df[~df["qc_class"].isin(QC_TYPES)]
    return df


def _valid(df, eps):
    return df[df["hole_id"].notna() & df["from_m"].notna() & df["to_m"].notna() & (df["to_m"] > df["from_m"] + eps)]


@rule("INT-010", ("intervals",))
def int_010(ctx):
    for t in ctx.interval_tables:
        df = originals(t)
        bad = df["hole_id"].isna() | df["from_m"].isna() | df["to_m"].isna()
        for i, r in df[bad].iterrows():
            miss = [f for f in ("hole_id", "from_m", "to_m") if pd.isna(r[f])]
            ctx.add("INT-010", "ERROR", t.name, f"Missing {', '.join(miss)}: the row cannot be placed downhole.",
                    f"فیلد {', '.join(miss)} وجود ندارد: ردیف در طول گمانه قابل جای‌گذاری نیست.", hole_id=r["hole_id"],
                    field=",".join(miss), src_row=int(r["src_row"]))


@rule("INT-001", ("intervals",))
def int_001(ctx):
    eps = ctx.eps
    for t in ctx.interval_tables:
        df = originals(t)
        df = df[df["from_m"].notna() & df["to_m"].notna()]
        bad = (df["from_m"] >= df["to_m"] - eps) | (df["from_m"] < 0) | (df["to_m"] < 0)
        for i, r in df[bad].iterrows():
            what = "negative depth" if min(r["from_m"], r["to_m"]) < 0 else ("zero length" if abs(r["to_m"] - r["from_m"]) <= eps else "From > To")
            what_fa = {"negative depth": "عمق منفی", "zero length": "طول صفر", "From > To": "عمق «از» بزرگ‌تر از «تا»"}[what]
            ctx.add("INT-001", "ERROR", t.name, f"Interval {r['from_m']:g}–{r['to_m']:g} m: {what}.", f"بازهٔ {r['from_m']:g} تا {r['to_m']:g} متر: {what_fa}.",
                    hole_id=r["hole_id"], from_m=r["from_m"], to_m=r["to_m"], field="from_m,to_m", src_row=int(r["src_row"]))


@rule("INT-002", ("intervals",))
def int_002(ctx):
    eps, micro = ctx.eps, ctx.p("INT-002")["micro_overlap_m"]
    for t in ctx.interval_tables:
        df = _valid(originals(t), eps).sort_values(["hole_id", "from_m", "to_m"])
        prev_max = df.groupby("hole_id")["to_m"].transform(lambda s: s.cummax().shift())
        ov = prev_max - df["from_m"]
        dup = df.duplicated(["hole_id", "from_m", "to_m"], keep=False)
        for i in df.index[(ov > eps) & ~dup]:
            r = df.loc[i]
            sev = "INFO" if ov[i] <= micro else "ERROR"
            ctx.add("INT-002", sev, t.name, f"Interval {r['from_m']:g}–{r['to_m']:g} m overlaps the previous interval by {ov[i]:.3g} m.",
                    f"بازهٔ {r['from_m']:g} تا {r['to_m']:g} متر با بازهٔ قبلی {ov[i]:.3g} متر هم‌پوشانی دارد.", hole_id=r["hole_id"],
                    from_m=r["from_m"], to_m=r["to_m"], field="from_m", value=round(float(ov[i]), 4), src_row=int(r["src_row"]))


@rule("INT-003", ("intervals",))
def int_003(ctx):
    eps = ctx.eps
    for t in ctx.interval_tables:
        df = _valid(originals(t), eps)
        vals = [c for c in df.columns if c.startswith("attr:") or c in ("lith_code", "sample_id", "cr_pct", "rqd_pct", "density")]
        acols = [a.column for a in t.analytes]
        key = df[["hole_id", "from_m", "to_m"]].round(3)
        dmask = key.duplicated(keep=False)
        for _, g in df[dmask].groupby([key["hole_id"], key["from_m"], key["to_m"]]):
            r = g.iloc[0]
            raw = t.raw.loc[g.index, acols] if acols else pd.DataFrame(index=g.index)
            same = all(g[c].nunique(dropna=False) == 1 for c in vals) and all(raw[c].nunique(dropna=False) == 1 for c in raw)
            kind_en, kind_fa = ("duplicate (identical values)", "تکراری (مقادیر یکسان)") if same else ("conflict (different values)", "متناقض (مقادیر متفاوت)")
            ctx.add("INT-003", "ERROR", t.name, f"{len(g)} records for {r['from_m']:g}–{r['to_m']:g} m: {kind_en}.",
                    f"{len(g)} رکورد برای بازهٔ {r['from_m']:g} تا {r['to_m']:g} متر: {kind_fa}.", hole_id=r["hole_id"],
                    from_m=r["from_m"], to_m=r["to_m"], value=len(g), src_row=int(g["src_row"].iloc[1]),
                    suggested_fix="Keep one record (identical) or resolve the conflict from the source document.")


@rule("INT-004", ("intervals", "collar"))
def int_004(ctx):
    eps, p = ctx.eps, ctx.p("INT-004")
    eoh = ctx.collar_u["eoh_m"] if "eoh_m" in ctx.collar_u else pd.Series(dtype=float)
    for t in ctx.interval_tables:
        if t.kind == "density":
            continue                      # density pieces are point measurements: gaps are meaningless
        contiguous = t.kind in CONTIGUOUS
        df = _valid(originals(t), eps).sort_values(["hole_id", "from_m", "to_m"])
        for h, g in df.groupby("hole_id"):
            f, to = g["from_m"].to_numpy(), g["to_m"].to_numpy()
            runmax = np.maximum.accumulate(to)
            gaps = [("top", 0.0, f[0])] if f[0] > p["top_gap_tol_m"] else []
            gi = np.where(f[1:] - runmax[:-1] > eps)[0]
            gaps += [("internal", runmax[k], f[k + 1]) for k in gi]
            e = eoh.get(h, np.nan)
            if np.isfinite(e) and e - runmax[-1] > p["bottom_gap_tol_m"]:
                gaps.append(("bottom", runmax[-1], e))
            for kind, a, b in gaps:
                size = b - a
                sev = "WARNING" if contiguous and size >= p["micro_gap_m"] else "INFO"
                fa = {"top": "بالایی", "internal": "میانی", "bottom": "پایینی"}[kind]
                ctx.add("INT-004", sev, t.name, f"{kind.capitalize()} gap {a:g}–{b:g} m ({size:.2f} m) in a {'contiguous' if contiguous else 'sampled'} table.",
                        f"شکاف {fa} از {a:g} تا {b:g} متر ({size:.2f} متر).", hole_id=h, from_m=float(a), to_m=float(b), field="from_m",
                        value=round(float(size), 3))


@rule("INT-005", ("intervals", "collar"))
def int_005(ctx):
    eps = ctx.eps
    eoh = ctx.collar_u["eoh_m"] if "eoh_m" in ctx.collar_u else pd.Series(dtype=float)
    for t in ctx.interval_tables:
        df = originals(t)
        over = df["to_m"] - df["hole_id"].map(eoh)
        for i in df.index[over > eps]:
            r = df.loc[i]
            ctx.add("INT-005", "ERROR", t.name, f"Interval ends at {r['to_m']:g} m, {over[i]:.2f} m beyond EOH.",
                    f"بازه در عمق {r['to_m']:g} متر پایان می‌یابد، {over[i]:.2f} متر پایین‌تر از عمق نهایی.", hole_id=r["hole_id"],
                    from_m=r["from_m"], to_m=r["to_m"], field="to_m", value=r["to_m"], src_row=int(r["src_row"]))


@rule("INT-006", ("intervals", "collar"))
def int_006(ctx):
    ids, keys = ctx.collar_ids, ctx.collar_keys()
    for t in ctx.tables:
        df = originals(t)
        for h, g in df[df["hole_id"].notna() & ~df["hole_id"].isin(ids)].groupby("hole_id"):
            k = keys.get(hole_key(h))
            hint = f" Matches collar '{k}' after folding: a join error." if k else ""
            ctx.add("INT-006", "ERROR", t.name, f"{len(g)} rows for hole '{h}', which is not in the collar table.{hint}",
                    f"{len(g)} ردیف برای گمانهٔ «{h}» که در جدول دهانه نیست.", hole_id=h, field="hole_id", value=len(g),
                    src_row=int(g["src_row"].iloc[0]))


@rule("INT-007", ("assay",))
def int_007(ctx):
    p = ctx.p("INT-007")
    for t in ctx.by_kind("assay"):
        df = _valid(originals(t), ctx.eps)
        L = df["to_m"] - df["from_m"]
        for i in df.index[(L < p["short_m"]) | (L > p["long_sample_m"])]:
            r = df.loc[i]
            ctx.add("INT-007", "INFO", t.name, f"Sample length {L[i]:.2f} m is outside {p['short_m']}–{p['long_sample_m']} m.",
                    f"طول نمونه {L[i]:.2f} متر خارج از بازهٔ {p['short_m']} تا {p['long_sample_m']} متر است.", hole_id=r["hole_id"],
                    from_m=r["from_m"], to_m=r["to_m"], field="length_m", value=round(float(L[i]), 3), src_row=int(r["src_row"]))
        key = next((a for a in t.analytes if a.analyte in ctx.params.get("key_analytes", []) and not a.partial), None)
        if key is not None and len(df) >= 100:
            v = key.parsed.loc[df.index, "value_policy"]
            ok = v.notna() & L.notna()
            if ok.sum() >= 100:
                rho = pd.Series(L[ok].to_numpy()).corr(pd.Series(v[ok].to_numpy()), method="spearman")
                if abs(rho) > 0.2:
                    ctx.add("INT-007", "INFO", t.name, f"Sample length correlates with {key.analyte} (Spearman ρ = {rho:.2f}): use length-weighted statistics and composites.",
                            f"طول نمونه با {key.analyte} همبستگی دارد (ρ اسپیرمن = {rho:.2f}): آمار وزنی طولی و کامپوزیت لازم است.",
                            field="length_m", value=round(float(rho), 3))


@rule("INT-008", ("assay", "lithology"))
def int_008(ctx):
    tol = ctx.p("INT-008")["contact_tol_m"]
    lith = pd.concat([_valid(t.df, ctx.eps) for t in ctx.by_kind("lithology")])
    contacts = {}
    for h, g in lith.sort_values(["hole_id", "from_m"]).groupby("hole_id"):
        codes = g["lith_code"].to_numpy()
        b = g["from_m"].to_numpy()[1:][codes[1:] != codes[:-1]]
        contacts[h] = np.sort(b)
    for t in ctx.by_kind("assay"):
        df = _valid(originals(t), ctx.eps)
        n_cross = 0
        for h, g in df.groupby("hole_id"):
            c = contacts.get(h)
            if c is None or len(c) == 0:
                continue
            lo = np.searchsorted(c, g["from_m"].to_numpy() + tol, side="left")
            hi = np.searchsorted(c, g["to_m"].to_numpy() - tol, side="right")
            crossing = g[(hi - lo) > 0]
            if len(crossing):
                n_cross += len(crossing)
                depths = ", ".join(f"{a:g}–{b:g}" for a, b in zip(crossing["from_m"].head(8), crossing["to_m"].head(8)))
                more = " …" if len(crossing) > 8 else ""
                ctx.add("INT-008", "INFO", t.name, f"{len(crossing)} of {len(g)} samples cross a lithology contact ({depths}{more} m): sampling does not follow geology.",
                        f"{len(crossing)} از {len(g)} نمونه از همبری سنگ‌شناسی عبور می‌کنند ({depths}{more} متر): نمونه‌برداری از مرزهای زمین‌شناسی پیروی نمی‌کند.",
                        hole_id=h, value=len(crossing))
        ctx.stats.setdefault("contact_crossing", {})[t.name] = (n_cross, len(df))


@rule("INT-009", ("intervals",))
def int_009(ctx):
    k = ctx.p("INT-009")["min_window_n"]
    for t in ctx.interval_tables:
        df = _valid(originals(t), ctx.eps).sort_values(["hole_id", "from_m"])
        vcols = [c for c in df.columns if c.startswith("attr:") or c in ("lith_code", "cr_pct", "rqd_pct", "density")]
        acols = [a.column for a in t.analytes]
        if not vcols and not acols:
            continue
        frame = pd.concat([df[vcols].astype("string"), t.raw.loc[df.index, acols].astype("string")], axis=1).fillna("")
        hashes = pd.util.hash_pandas_object(frame, index=False).to_numpy()
        seen = {}
        for h, idx in df.groupby("hole_id").indices.items():
            hh = hashes[idx]
            for s in range(0, len(hh) - k + 1):
                w = hh[s:s + k]
                if len(set(w)) < 3:
                    continue
                win = frame.iloc[idx[s:s + k]]
                if all(win[c].nunique() <= 1 for c in win.columns):
                    continue
                seen.setdefault(tuple(w), []).append((h, idx[s]))
        reported = set()
        for w, occ in seen.items():
            holes = {o[0] for o in occ}
            if len(occ) >= 2 and (len(holes) >= 2 or len(occ) >= 2):
                for h, start in occ:
                    r = df.iloc[start]
                    if (h, r["from_m"]) in reported:
                        continue
                    reported.add((h, r["from_m"]))
                    others = ", ".join(sorted({o[0] for o in occ} - {h})) or "same hole"
                    ctx.add("INT-009", "WARNING", t.name, f"A block of {k} consecutive rows from {r['from_m']:g} m is repeated elsewhere ({others}): possible copy-paste.",
                            f"بلوکی از {k} ردیف پیاپی از عمق {r['from_m']:g} متر در جای دیگری تکرار شده است ({others}): احتمال کپی‌کردن.",
                            hole_id=h, from_m=r["from_m"], value=others, src_row=int(r["src_row"]))


@rule("INT-013", ("intervals",))
def int_013(ctx):
    for t in ctx.interval_tables:
        if t.kind in ("lithology", "assay"):
            continue
        df = _valid(t.df, ctx.eps).sort_values(["hole_id", "from_m"])
        vcols = [c for c in df.columns if c.startswith("attr:") or c in ("alt_type", "weathering", "cr_pct", "rqd_pct")]
        if not vcols:
            continue
        v = df[vcols].astype("string").fillna("")
        same_hole = df["hole_id"].eq(df["hole_id"].shift())
        contiguous = (df["from_m"] - df["to_m"].shift()).abs() <= ctx.eps
        same_vals = (v == v.shift()).all(axis=1)
        for i in df.index[same_hole & contiguous & same_vals]:
            r = df.loc[i]
            ctx.add("INT-013", "INFO", t.name, f"Interval at {r['from_m']:g} m repeats the previous one exactly (unmerged records).",
                    f"بازه در عمق {r['from_m']:g} متر دقیقاً تکرار بازهٔ قبلی است (رکوردهای ادغام‌نشده).", hole_id=r["hole_id"],
                    from_m=r["from_m"], to_m=r["to_m"], src_row=int(r["src_row"]))


@rule("IMP-011", ("collar",))
def imp_011(ctx):
    eoh = ctx.collar_u["eoh_m"] if "eoh_m" in ctx.collar_u else None
    if eoh is None:
        return
    tables = ctx.tables + ([ctx.survey] if ctx.survey is not None else [])
    for t in tables:
        col = "to_m" if "to_m" in t.df and t.df["to_m"].notna().any() else "depth_m"
        if col not in t.df:
            continue
        ratio = (t.df.groupby("hole_id")[col].max() / eoh).dropna()
        ratio = ratio[np.isfinite(ratio)]
        if len(ratio) >= 5 and 3.1 <= ratio.median() <= 3.45:
            ctx.add("IMP-011", "WARNING", t.name, f"Depths are about {ratio.median():.2f} × EOH in {len(ratio)} holes: the table is probably in feet.",
                    f"عمق‌ها در {len(ratio)} گمانه حدود {ratio.median():.2f} برابر عمق نهایی‌اند: احتمالاً واحد جدول فوت است.",
                    field=col, value=round(float(ratio.median()), 3), suggested_fix="Set the depth unit of this table to ft in the mapping.")
