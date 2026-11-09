"""Value-validation rules added for the v2 brief (category E): VAL-04, VAL-06, VAL-08, VAL-09, VAL-10."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..analysis.assay import TO_PPM
from .base import rule
from .interval import QC_TYPES

_CODE_FIELDS = {"lith_code": "lithology", "alt_type": "alteration", "weathering": "weathering"}


def _orig(t) -> pd.Series:
    if "qc_class" in t.df:
        return ~t.df["qc_class"].isin(QC_TYPES)
    return pd.Series(True, index=t.df.index)


def _ctx_row(t, i):
    r = t.df.loc[i]
    return dict(hole_id=r["hole_id"], from_m=r.get("from_m"), to_m=r.get("to_m"), src_row=int(r["src_row"]))


@rule("ASY-010", ("analytes",))
def asy_010(ctx):
    """VAL-04 (detection limits): more than one detection limit within one analyte column, with counts and the batches
    using each. WARNING (Minor): ½DL substitution then steps at the DL change and the low-grade tail mixes populations."""
    for t in ctx.tables:
        m = _orig(t)
        batch = t.df["batch"] if "batch" in t.df else None
        for a in t.analytes:
            dl = a.parsed.loc[m & (a.parsed["flag"] == "BDL"), "dl"].round(9).dropna()
            if dl.nunique() < 2:
                continue
            parts = []
            for v, g in dl.groupby(dl):
                bs = sorted(batch.loc[g.index].dropna().astype(str).unique()) if batch is not None else []
                parts.append(f"{v:g} (n {len(g)}{', batches ' + (bs[0] + '…' + bs[-1] if len(bs) > 2 else ', '.join(bs)) if bs else ''})")
            ctx.add("ASY-010", "WARNING", t.name, f"Column '{a.column}' uses {dl.nunique()} detection limits: {'; '.join(parts)}.",
                    f"ستون «{a.column}» {dl.nunique()} حد تشخیص متفاوت دارد: {'؛ '.join(parts)}.", field=a.column, value=dl.nunique())


@rule("ASY-019", ("assay",))
def asy_019(ctx):
    """VAL-04 (laboratories and methods): an assay table whose rows come from more than one laboratory or analytical
    method (mapped `lab` / `method` columns). WARNING (Minor): mixed methods in one field must be shown to be comparable."""
    for t in ctx.by_kind("assay"):
        m = _orig(t)
        for f, en, fa in (("lab", "laboratories", "آزمایشگاه"), ("method", "analytical methods", "روش آنالیز")):
            if f not in t.df:
                continue
            v = t.df.loc[m, f].dropna().astype(str).str.strip()
            v = v[v != ""]
            if v.nunique() > 1:
                counts = v.value_counts()
                ctx.add("ASY-019", "WARNING", t.name, f"{v.nunique()} {en} in one table: {', '.join(f'{k} ({n})' for k, n in counts.head(8).items())}.",
                        f"{v.nunique()} {fa} مختلف در یک جدول: {', '.join(f'{k} ({n})' for k, n in counts.head(8).items())}.",
                        field=f, value=v.nunique())


@rule("ASY-028", ("analytes",))
def asy_028(ctx):
    """VAL-06: mineral-stoichiometric caps (wt %, by the dominant mineral; editable `caps_pct`). Defaults: Cu 79.9
    (chalcocite), Pb 86.6 (galena), Zn 67.1 (sphalerite), Fe 72.4 (magnetite), S 53.4 (pyrite), Mo 59.9 (molybdenite),
    Ba 58.8 (barite). A value above its cap cannot occur in any rock of that mineralogy. ERROR (Major)."""
    caps = ctx.p("ASY-028").get("caps_pct", {})
    for t in ctx.tables:
        m = _orig(t)
        for a in t.analytes:
            cap = caps.get(a.analyte)
            if cap is None or a.partial:
                continue
            pct = a.parsed["value"].where(m & (a.parsed["flag"] == "VAL")) * TO_PPM[a.unit] / 1e4
            for i in pct.index[pct > float(cap)]:
                ctx.add("ASY-028", "ERROR", t.name, f"{a.analyte} = {pct[i]:.3g} % exceeds the stoichiometric cap of {cap:g} %.",
                        f"{a.analyte} برابر {pct[i]:.3g} درصد و بیش از سقف استوکیومتری {cap:g} درصد است.", field=a.column,
                        value=round(float(pct[i]), 4), **_ctx_row(t, i))


@rule("ASY-029", ("analytes",))
def asy_029(ctx):
    """VAL-09: downhole spike: a value more than `factor` (10) times both downhole neighbours and above the field's
    `quantile` (P95). INFO: often real (nugget), sometimes a decimal or sample-order error worth a look."""
    p = ctx.p("ASY-029")
    for t in ctx.by_kind("assay"):
        m = _orig(t) & t.df["hole_id"].notna() & t.df["from_m"].notna()
        order = t.df[m].sort_values(["hole_id", "from_m"]).index
        hole = t.df.loc[order, "hole_id"].to_numpy()
        for a in t.analytes:
            if a.partial:
                continue
            v = a.parsed.loc[order, "value_policy"].to_numpy(float)
            if np.isfinite(v).sum() < 20:
                continue
            q = np.nanquantile(v, p["quantile"])
            prev, nxt = np.r_[np.nan, v[:-1]], np.r_[v[1:], np.nan]
            same_prev = np.r_[False, hole[1:] == hole[:-1]]
            same_next = np.r_[hole[:-1] == hole[1:], False]
            hit = same_prev & same_next & (v > q) & (prev > 0) & (nxt > 0) & (v > p["factor"] * prev) & (v > p["factor"] * nxt)
            for k in np.where(hit)[0]:
                i = order[k]
                ctx.add("ASY-029", "INFO", t.name, f"{a.analyte} spike {v[k]:.4g} {a.unit}: more than {p['factor']:g}× both neighbours ({prev[k]:.3g}, {nxt[k]:.3g}) and above P{p['quantile'] * 100:g}.",
                        f"جهش {a.analyte} برابر {v[k]:.4g} {a.unit}: بیش از {p['factor']:g} برابر هر دو نمونهٔ مجاور.", field=a.column,
                        value=round(float(v[k]), 6), **_ctx_row(t, i))


@rule("ASY-030", ("analytes",))
def asy_030(ctx):
    """VAL-10: `min_run` (5) or more consecutive identical values above detection in one hole and analyte: possible
    copy-paste or fill-down. "Above detection" means above the largest detection limit of the column and above its
    lowest reported value (a reporting floor without `<` codes). WARNING (Minor). Block copies between holes are INT-009."""
    p = ctx.p("ASY-030")
    for t in ctx.by_kind("assay"):
        m = _orig(t) & t.df["hole_id"].notna() & t.df["from_m"].notna()
        order = t.df[m].sort_values(["hole_id", "from_m"]).index
        hole = t.df.loc[order, "hole_id"].to_numpy()
        for a in t.analytes:
            pr = a.parsed.loc[order]
            v = pr["value"].where(pr["flag"] == "VAL").to_numpy(float)
            dl = a.parsed["dl"].dropna()
            vals = a.parsed.loc[a.parsed["flag"] == "VAL", "value"]
            # above detection: above the largest DL and above the lowest reported value (an unstated reporting floor)
            floor = max(float(dl.max()) if len(dl) else 0.0, float(vals[vals > 0].min()) if (vals > 0).any() else 0.0)
            ok = np.isfinite(v) & (v > floor)
            start = 0
            for k in range(1, len(v) + 1):
                if k < len(v) and ok[k] and ok[k - 1] and v[k] == v[k - 1] and hole[k] == hole[k - 1]:
                    continue
                if k - start >= p["min_run"] and ok[start]:
                    i0, i1 = order[start], order[k - 1]
                    ctx.add("ASY-030", "WARNING", t.name, f"{k - start} consecutive {a.analyte} values equal to {v[start]:g} from {t.df.at[i0, 'from_m']:g} to {t.df.at[i1, 'to_m']:g} m: possible copy-paste or fill-down.",
                            f"{k - start} مقدار متوالی {a.analyte} برابر {v[start]:g} از عمق {t.df.at[i0, 'from_m']:g} تا {t.df.at[i1, 'to_m']:g} متر: احتمال کپی یا پرکردن خودکار.",
                            hole_id=hole[start], from_m=t.df.at[i0, "from_m"], to_m=t.df.at[i1, "to_m"], field=a.column,
                            value=k - start, src_row=int(t.df.at[i0, "src_row"]))
                start = k


@rule("INT-015", ("code_dictionary",))
def int_015(ctx):
    """VAL-08: logged codes not in the user's code dictionary (profile `code_dictionaries`, or a dictionary file).
    Keys are canonical fields (lith_code, alt_type, weathering, drill_method …) or source column names. Matching ignores
    case and surrounding spaces. ERROR (Major), one issue per (table, field, code) with its count."""
    dic = {str(k).lower(): {str(c).strip().upper() for c in v} for k, v in (ctx.params.get("code_dictionaries") or {}).items()}
    tabs = ([ctx.collar] if ctx.collar is not None else []) + ctx.tables
    for t in tabs:
        cols = {}
        for f in ("lith_code", "alt_type", "weathering", "drill_method"):
            if f in t.df and f in dic:
                cols[f] = f
        for c in t.attrs:
            name = c.split(":", 1)[1]
            if name.lower() in dic:
                cols[c] = name.lower()
        for col, key in cols.items():
            v = t.df[col].dropna().astype(str).str.strip()
            v = v[v != ""]
            bad = v[~v.str.upper().isin(dic[key])]
            for code, g in bad.groupby(bad):
                i = g.index[0]
                ctx.add("INT-015", "ERROR", t.name, f"Code '{code}' in {key} ({len(g)} rows) is not in the code dictionary.",
                        f"کد «{code}» در {key} ({len(g)} ردیف) در فهرست کدها نیست.", hole_id=t.df.at[i, "hole_id"],
                        from_m=t.df.at[i, "from_m"] if "from_m" in t.df else None, field=key, value=code,
                        src_row=int(t.df.at[i, "src_row"]), suggested_fix="Correct the code or add it to the dictionary.")
