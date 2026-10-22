"""QAQ rules (03 §2.6): insertion rates, CRM, blanks, duplicates. QC classes come from sample_type or ID patterns."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .base import rule

PATTERNS = [("CRM", r"^(CRM|STD|STANDARD|REF|SRM|OREAS|استاندارد)"), ("BLANK", r"^(BLK|BLANK|BL|بلانک)"),
            ("FIELD_DUP", r"^(FD|FDUP|FIELD|DUP|DUPLICATE|DP|تکراری)"), ("COARSE_DUP", r"^(CD|COARSE|CRUSH|CRD|REJ)"),
            ("PULP_DUP", r"^(PD|PULP|PLP|PDUP)"), ("UMPIRE", r"^(UMP|UMPIRE|CHECK|CHK)")]


def classify(sample_type: pd.Series, sample_id: pd.Series) -> pd.Series:
    out = pd.Series("ORIGINAL", index=sample_type.index, dtype=object)
    st = sample_type.fillna("").astype(str).str.upper().str.replace(r"[\s_\-]", "", regex=True)
    sid = sample_id.fillna("").astype(str).str.upper() if sample_id is not None else pd.Series("", index=st.index)
    for cls, pat in PATTERNS:
        hit = st.str.match(pat) | (st.eq("") & sid.str.match(pat.replace("^(", "^(?:")))
        out[hit & (out == "ORIGINAL")] = cls
    return out


def _assays(ctx):
    return [t for t in ctx.by_kind("assay") if "qc_class" in t.df]


@rule("QAQ-001", ("assay",))
def qaq_001(ctx):
    p = ctx.p("QAQ-001")
    tabs = _assays(ctx)
    if not tabs:
        ctx.add("QAQ-001", "CRITICAL", ctx.by_kind("assay")[0].name,
                "No QA/QC samples could be identified (no sample-type column and no CRM/blank/duplicate ID pattern): assay accuracy, contamination and precision are unverified.",
                "هیچ نمونهٔ کنترل کیفیت شناسایی نشد (ستون نوع نمونه یا الگوی شناسهٔ استاندارد/بلانک/تکراری وجود ندارد): صحت، آلودگی و دقت نتایج آنالیز تأییدنشده است.",
                field="sample_type", suggested_fix="Supply the QA/QC register (sample type, CRM ID, parent sample) or map the sample-type column.")
        return
    for t in tabs:
        cls = t.df["qc_class"]
        n_orig = int((cls == "ORIGINAL").sum())
        rates = {k: 100.0 * int((cls == k).sum()) / max(n_orig, 1) for k in ("CRM", "BLANK", "FIELD_DUP", "COARSE_DUP", "PULP_DUP", "UMPIRE")}
        ctx.stats.setdefault("qaqc_rates", {})[t.name] = (n_orig, rates)
        if sum(rates.values()) == 0:
            ctx.add("QAQ-001", "CRITICAL", t.name, f"No QA/QC samples among {n_orig} assays.", f"در میان {n_orig} نمونه هیچ نمونهٔ کنترل کیفیت وجود ندارد.",
                    field="sample_type", value=0)
            continue
        if n_orig < p["min_originals_n"]:
            continue
        targets = {"CRM": p["target_crm_pct"], "BLANK": p["target_blank_pct"], "FIELD_DUP": p["target_field_dup_pct"],
                   "COARSE_DUP": p["target_coarse_dup_pct"], "PULP_DUP": p["target_pulp_dup_pct"]}
        for k, tgt in targets.items():
            r = rates[k]
            if r < tgt:
                sev = "ERROR" if r < tgt / 2 else "WARNING"
                ctx.add("QAQ-001", sev, t.name, f"{k} insertion rate {r:.1f} % is below the {tgt:g} % target.",
                        f"نرخ درج {k} برابر {r:.1f} درصد و کمتر از هدف {tgt:g} درصد است.", field="sample_type", value=round(r, 2),
                        expected=f">= {tgt:g} %")


def _crm_targets(ctx) -> dict:
    tv = {}
    if ctx.crm_values is None:
        return tv
    for _, r in ctx.crm_values.iterrows():
        tv[(str(r["crm_id"]).upper().replace(" ", ""), str(r["analyte"]))] = (float(r["certified"]), float(r["sd"]))
    return tv


@rule("QAQ-002", ("qaqc", "crm_values"))
def qaq_002(ctx):
    p = ctx.p("QAQ-002")
    tv = _crm_targets(ctx)
    for t in _assays(ctx):
        crm = t.df[t.df["qc_class"] == "CRM"]
        if crm.empty or "crm_id" not in t.df:
            continue
        ids = crm["crm_id"].fillna(crm.get("sample_id")).astype(str).str.upper().str.replace(" ", "", regex=False)
        series = []
        for a in t.analytes:
            for i in crm.index:
                key = (ids[i], a.analyte)
                if key not in tv or a.parsed.at[i, "flag"] != "VAL":
                    continue
                cert, sd = tv[key]
                v = a.parsed.at[i, "value"]
                z = (v - cert) / sd if sd > 0 else np.nan
                series.append((ids[i], a.analyte, i, v, cert, sd, z))
                if abs(z) > p["sd_fail"]:
                    sev, en, fa = "ERROR", "fails", "مردود"
                elif abs(z) > p["sd_warn"]:
                    sev, en, fa = "WARNING", "is outside ±2 SD", "خارج از ±۲ انحراف معیار"
                else:
                    continue
                ctx.add("QAQ-002", sev, t.name, f"CRM {ids[i]} {a.analyte} = {v:g} (certified {cert:g} ± {sd:g}, z = {z:+.1f}) {en}.",
                        f"ماده مرجع {ids[i]}، {a.analyte} = {v:g} (مقدار تأییدشده {cert:g} ± {sd:g}، z = {z:+.1f}) {fa} است.",
                        hole_id=t.df.at[i, "hole_id"], field=a.column, value=v, expected=f"{cert:g} ± {3 * sd:g}",
                        src_row=int(t.df.at[i, "src_row"]), suggested_fix="Re-assay the batch or record a disposition (QAQ-018).")
        if series:
            s = pd.DataFrame(series, columns=["crm", "analyte", "idx", "value", "certified", "sd", "z"])
            ctx.stats.setdefault("crm_results", {})[t.name] = s
            for (c, el), g in s.groupby(["crm", "analyte"]):
                if len(g) >= p["min_n_bias"]:
                    bias = 100 * (g["value"].mean() - g["certified"].iloc[0]) / g["certified"].iloc[0]
                    if abs(bias) > p["bias_warn_pct"]:
                        sev = "ERROR" if abs(bias) > p["bias_err_pct"] else "WARNING"
                        ctx.add("QAQ-002", sev, t.name, f"CRM {c} {el}: mean bias {bias:+.1f} % over {len(g)} results.",
                                f"ماده مرجع {c}، {el}: اریبی میانگین {bias:+.1f} درصد در {len(g)} نتیجه.", field=el, value=round(bias, 2))


@rule("QAQ-003", ("qaqc",))
def qaq_003(ctx):
    p = ctx.p("QAQ-003")
    for t in _assays(ctx):
        blanks = t.df.index[t.df["qc_class"] == "BLANK"]
        if len(blanks) == 0:
            continue
        for a in t.analytes:
            dl = a.parsed["dl"].dropna()
            if dl.empty:
                continue
            dlm = float(dl.mode().iloc[0])
            v = a.parsed.loc[blanks]
            vals = v.loc[v["flag"] == "VAL", "value"]
            ctx.stats.setdefault("blank_results", {}).setdefault(t.name, []).append((a.analyte, dlm, vals))
            for i, val in vals.items():
                ratio = val / dlm
                if ratio > p["blank_warn_x_dl"]:
                    sev = "ERROR" if ratio > p["blank_fail_x_dl"] else "WARNING"
                    pos = t.df.index.get_loc(i)
                    prev = a.parsed["value_policy"].iloc[pos - 1] if pos > 0 else np.nan
                    carry = np.isfinite(prev) and prev > a.parsed["value_policy"].quantile(0.95)
                    why_en = " (follows a high-grade sample: carry-over)" if carry else ""
                    why_fa = " (پس از یک نمونهٔ پرعیار: انتقال آلودگی)" if carry else ""
                    ctx.add("QAQ-003", sev, t.name, f"Blank {a.analyte} = {val:g} {a.unit} = {ratio:.0f} × DL{why_en}.",
                            f"بلانک {a.analyte} = {val:g} {a.unit} برابر {ratio:.0f} برابر حد تشخیص است{why_fa}.",
                            hole_id=t.df.at[i, "hole_id"], field=a.column, value=val, expected=f"< {p['blank_warn_x_dl'] * dlm:g}",
                            src_row=int(t.df.at[i, "src_row"]))


@rule("QAQ-004", ("qaqc",))
def qaq_004(ctx):
    p = ctx.p("QAQ-004")
    for t in _assays(ctx):
        if "parent_id" not in t.df or "sample_id" not in t.df:
            continue
        df = t.df
        sid_index = {s: i for i, s in df["sample_id"].dropna().items()}
        for kind, limit in p["hard_limit_pct"].items():
            dups = df.index[(df["qc_class"] == kind) & df["parent_id"].notna()]
            if len(dups) == 0:
                continue
            for a in t.analytes:
                if a.partial:
                    continue
                dl = a.parsed["dl"].dropna()
                dlm = float(dl.mode().iloc[0]) if len(dl) else 0.0
                pairs = []
                for i in dups:
                    j = sid_index.get(df.at[i, "parent_id"])
                    if j is None:
                        continue
                    va, vb = a.parsed.at[j, "value_policy"], a.parsed.at[i, "value_policy"]
                    if np.isfinite(va) and np.isfinite(vb) and (va + vb) > 0 and (va + vb) / 2 >= p["min_mean_x_dl"] * dlm:
                        pairs.append((va, vb))
                if len(pairs) < 10:
                    continue
                arr = np.array(pairs)
                hard = 100 * np.abs(arr[:, 0] - arr[:, 1]) / (arr[:, 0] + arr[:, 1])
                ctx.stats.setdefault("dup_pairs", {})[(t.name, kind, a.analyte)] = arr
                fail = float((hard > limit).mean())
                if fail > p["max_fail_frac"]:
                    sev = "ERROR" if kind == "PULP_DUP" and fail > 2 * p["max_fail_frac"] else "WARNING"
                    cv = 100 * np.sqrt(np.mean((np.sqrt(2) * np.abs(arr[:, 0] - arr[:, 1]) / (arr[:, 0] + arr[:, 1])) ** 2))
                    ctx.add("QAQ-004", sev, t.name, f"{kind} {a.analyte}: {fail:.0%} of {len(arr)} pairs exceed HARD {limit} % (allowed {p['max_fail_frac']:.0%}); RMS CV {cv:.0f} %.",
                            f"{kind} {a.analyte}: {fail:.0%} از {len(arr)} جفت از حد HARD برابر {limit} درصد فراترند (مجاز {p['max_fail_frac']:.0%})؛ RMS CV = {cv:.0f} درصد.",
                            field=a.column, value=round(fail, 3), expected=f"<= {p['max_fail_frac']:.0%}")
