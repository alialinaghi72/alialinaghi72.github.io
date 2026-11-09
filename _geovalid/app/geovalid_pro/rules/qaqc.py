"""QAQ rules (03 §2.6): insertion rates, CRM, blanks, duplicates. QC classes come from sample_type or ID patterns."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .base import rule

PATTERNS = [("CRM", r"^(CRM|STD|STANDARD|REF|SRM|OREAS|استاندارد)"), ("BLANK", r"^(BLK|BLANK|BL|CBLK|PBLK|بلانک)"),
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
    """Tables whose QC samples the QAQ rules evaluate: database assay tables carrying QC; when none of them holds a QC
    sample and a GEOQAQC laboratory file is loaded, its QC rows (R1)."""
    tabs = [t for t in ctx.by_kind("assay") if "qc_class" in t.df]
    if ctx.lab is not None and not any((t.df["qc_class"] != "ORIGINAL").any() for t in tabs):
        return [ctx.lab]
    return tabs


@rule("QAQ-001", ("assay_or_lab",))
def qaq_001(ctx):
    p = ctx.p("QAQ-001")
    tabs = _assays(ctx)
    if not tabs:
        ctx.add("QAQ-001", "CRITICAL", (ctx.by_kind("assay") or [ctx.lab])[0].name,
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
                ctx.add("QAQ-001", sev, t.name, f"{k} insertion rate {r:.2f} % is below the {tgt:g} % target.",
                        f"نرخ درج {k} برابر {r:.1f} درصد و کمتر از هدف {tgt:g} درصد است.", field="sample_type", value=round(r, 2),
                        expected=f">= {tgt:g} %")


def _crm_key(v) -> str:
    """CRM IDs match case-insensitively after trimming surrounding spaces only (QAQC_FORMAT.md §2); `DEMO 501` and
    `DEMO-501` are different IDs unless the profile maps one to the other (`crm_id_aliases`)."""
    return str(v).strip().upper()


def _crm_targets(ctx) -> dict:
    tv = {}
    if ctx.crm_values is None:
        return tv
    for _, r in ctx.crm_values.iterrows():
        unit = r["unit"] if "unit" in r and isinstance(r["unit"], str) else None
        tv[(_crm_key(r["crm_id"]), str(r["analyte"]))] = (float(r["certified"]), float(r["sd"]), unit)
    return tv


def _crm_ids(ctx, df) -> pd.Series:
    alias = {_crm_key(k): _crm_key(v) for k, v in (ctx.params.get("crm_id_aliases") or {}).items()}
    ids = df["crm_id"].map(lambda v: _crm_key(v) if isinstance(v, str) and v.strip() else None)
    return ids.map(lambda v: alias.get(v, v) if v else v)


@rule("QAQ-002", ("qc_any", "crm_values"))
def qaq_002(ctx):
    p = ctx.p("QAQ-002")
    tv = _crm_targets(ctx)
    for t in _assays(ctx):
        crm = t.df[t.df["qc_class"] == "CRM"]
        if crm.empty or "crm_id" not in t.df:
            continue
        ids = _crm_ids(ctx, crm)
        lbl = crm["crm_id"].astype("string").str.strip().fillna(ids)      # the ID as written, for messages
        series = []
        for a in t.analytes:
            done = set()
            for i in crm.index:
                key = (ids[i], a.analyte)
                if key not in tv or a.parsed.at[i, "flag"] not in ("VAL", "BDL"):
                    continue
                cert0, sd0, unit = tv[key]
                from ..io.lab import convert
                cert, sd = convert(cert0, unit, a.unit), convert(sd0, unit, a.unit)
                if unit and unit != a.unit and key not in done:          # declared-unit conversion, always reported
                    done.add(key)
                    ctx.add("QAQ-002", "INFO", t.name, f"CRM {lbl[i]} {a.analyte}: certified value converted from the declared {unit} to the column unit {a.unit} ({cert0:g} ± {sd0:g} {unit} → {cert:g} ± {sd:g} {a.unit}).",
                            f"ماده مرجع {lbl[i]}، {a.analyte}: مقدار تأییدشده از واحد اعلام‌شدهٔ {unit} به واحد ستون {a.unit} تبدیل شد ({cert0:g} → {cert:g}).",
                            field=a.column, value=f"{lbl[i]}: {unit}->{a.unit}")
                bdl = a.parsed.at[i, "flag"] == "BDL"
                v = a.parsed.at[i, "dl"] if bdl else a.parsed.at[i, "value"]      # a CRM reported <DL: z from the DL (upper bound)
                if bdl and not (cert > 3 * v):
                    continue                     # certified value near the DL: <DL is not evidence of failure
                z = (v - cert) / sd if sd > 0 else np.nan
                series.append((ids[i], a.analyte, i, v, cert, sd, z, lbl[i]))
                if abs(z) > p["sd_fail"]:
                    sev, en, fa = "ERROR", "fails", "مردود"
                elif abs(z) > p["sd_warn"]:
                    sev, en, fa = "WARNING", "is outside ±2 SD", "خارج از ±۲ انحراف معیار"
                else:
                    continue
                hint = ""
                if v > 0 and cert > 0:
                    lr = np.log10(v / cert)
                    k = next((k for k in (3, 4, -3, -4) if abs(lr - k) < 0.013), None)
                    if k is not None:
                        hint = f" The value is ≈10^{k} × certified: probable unit error."
                if bdl:
                    hint = " Reported below detection although certified well above it." + hint
                ctx.add("QAQ-002", sev, t.name, f"CRM {lbl[i]} {a.analyte} = {'<' if bdl else ''}{v:g} (certified {cert:g} ± {sd:g}, z = {z:+.1f}) {en}.{hint}",
                        f"ماده مرجع {lbl[i]}، {a.analyte} = {v:g} (مقدار تأییدشده {cert:g} ± {sd:g}، z = {z:+.1f}) {fa} است.",
                        hole_id=t.df.at[i, "hole_id"], field=a.column, value=v, expected=f"{cert:g} ± {3 * sd:g}",
                        src_row=int(t.df.at[i, "src_row"]), suggested_fix="Re-assay the batch or record a disposition (QAQ-018).")
        if series:
            s = pd.DataFrame(series, columns=["crm", "analyte", "idx", "value", "certified", "sd", "z", "label"])
            ctx.stats.setdefault("crm_results", {})[t.name] = s
            for (c, el), g in s.groupby(["crm", "analyte"]):
                if len(g) >= p["min_n_bias"]:
                    bias = 100 * (g["value"].mean() - g["certified"].iloc[0]) / g["certified"].iloc[0]
                    if abs(bias) > p["bias_warn_pct"]:
                        sev = "ERROR" if abs(bias) > p["bias_err_pct"] else "WARNING"
                        ctx.add("QAQ-002", sev, t.name, f"CRM {g['label'].iloc[0]} {el}: mean bias {bias:+.1f} % over {len(g)} results.",
                                f"ماده مرجع {g['label'].iloc[0]}، {el}: اریبی میانگین {bias:+.1f} درصد در {len(g)} نتیجه.", field=el, value=round(bias, 2))


@rule("QAQ-006", ("qc_any", "crm_values"))
def qaq_006(ctx):
    """Probable mislabelled CRM. For a CRM row failing its declared CRM (|z| > `sd_fail` on any analyte), every other
    certified CRM is tested on all analytes of that row: exactly one CRM matching within `match_sd` SD on at least
    `min_analytes_match` analytes (all, if fewer are certified) → WARNING "probable mislabel X → Y". A row whose
    values all lie below `blank_x_dl` × the column's detection limit → WARNING "probable CRM/blank swap". A suggestion
    for the reviewer; the CRM ID is never changed."""
    from ..io.lab import convert
    p = {"sd_fail": 3, **ctx.p("QAQ-002"), **ctx.p("QAQ-006")}
    match_sd, need, bx = float(p.get("match_sd", 2)), int(p.get("min_analytes_match", 2)), float(p.get("blank_x_dl", 5))
    tv = _crm_targets(ctx)
    crms = sorted({k[0] for k in tv})
    for t in _assays(ctx):
        res = ctx.stats.get("crm_results", {}).get(t.name)
        if res is None or res.empty:
            continue
        failed = res[res["z"].abs() > p["sd_fail"]]
        an = {a.analyte: a for a in t.analytes}
        for i, g in failed.groupby("idx"):
            dkey, declared = g["crm"].iloc[0], g["label"].iloc[0]
            vals = {a: (float(an[a].parsed.at[i, "value"]) if an[a].parsed.at[i, "flag"] == "VAL" else None, an[a]) for a in an}
            hits = []
            for c in crms:
                if c == dkey:
                    continue
                tested = ok = 0
                for el, (v, a) in vals.items():
                    if v is None or (c, el) not in tv:
                        continue
                    cert0, sd0, unit = tv[(c, el)]
                    cert, sd = convert(cert0, unit, a.unit), convert(sd0, unit, a.unit)
                    tested += 1
                    ok += sd > 0 and abs(v - cert) / sd < match_sd
                if tested and ok >= min(need, tested) and ok == tested:
                    hits.append(c)
            row = t.df.loc[i]
            loc = dict(hole_id=row.get("hole_id") if isinstance(row.get("hole_id"), str) else None, field="crm_id", value=declared,
                       src_row=int(row["src_row"]))
            sid = row.get("sample_id") or f"row {int(row['src_row'])}"
            if len(hits) == 1:
                ctx.add("QAQ-006", "WARNING", t.name, f"{sid}: fails its declared CRM {declared} but matches {hits[0]} on every certified element: probable mislabel {declared} → {hits[0]}.",
                        f"{sid}: با ماده مرجع اعلام‌شده {declared} ناسازگار ولی با {hits[0]} سازگار است: احتمال برچسب اشتباه.",
                        expected=hits[0], suggested_fix=f"Check the insertion sheet; if confirmed, SET crm_id = {hits[0]} (reviewer).", **loc)
                continue
            low = []
            for el, (v, a) in vals.items():
                dl = a.parsed.loc[a.parsed["flag"] == "BDL", "dl"].max()
                if a.parsed.at[i, "flag"] == "BDL":
                    low.append(True)
                elif v is not None and pd.notna(dl):
                    low.append(v <= bx * dl)
            if low and all(low):
                ctx.add("QAQ-006", "WARNING", t.name, f"{sid}: declared CRM {declared} but every element is at blank level (≤ {bx:g} × DL): probable CRM/blank swap.",
                        f"{sid}: ماده مرجع {declared} اعلام شده ولی همهٔ عناصر در حد بلانک‌اند: احتمال جابه‌جایی ماده مرجع و بلانک.",
                        expected="BLANK", **loc)


@rule("QAQ-003", ("qc_any",))
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
            ctx.stats.setdefault("blank_results", {}).setdefault(t.name, []).append((a.analyte, dlm, v[["flag", "value"]]))
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


@rule("QAQ-004", ("qc_any",))
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


@rule("QAQ-008", ("qc_any",))
def qaq_008(ctx):
    """CRM identity: a CRM row without CRM_ID, or whose CRM_ID has no certificate (IDs compare case-insensitively after
    trimming spaces; profile `crm_id_aliases` maps spellings explicitly). The closest certificate IDs are suggested,
    never applied. ERROR: those CRM results cannot be judged. WARNING when no certificate file is loaded at all."""
    import difflib
    tv = _crm_targets(ctx)
    cert_ids = sorted({k[0] for k in tv})
    for t in _assays(ctx):
        crm = t.df[t.df["qc_class"] == "CRM"]
        if crm.empty:
            continue
        if not tv:
            ctx.add("QAQ-008", "WARNING", t.name, f"{len(crm)} CRM results but no CRM certificate file is loaded: their accuracy cannot be judged.",
                    f"{len(crm)} نتیجهٔ ماده مرجع وجود دارد ولی فایل گواهی مواد مرجع بارگذاری نشده است.", field="crm_id", value=len(crm))
            continue
        ids = _crm_ids(ctx, crm) if "crm_id" in crm else pd.Series(None, index=crm.index)
        miss = crm[ids.isna()]
        if len(miss):
            ctx.add("QAQ-008", "ERROR", t.name, f"{len(miss)} CRM rows have no CRM_ID.", f"{len(miss)} ردیف ماده مرجع شناسهٔ CRM ندارند.",
                    field="crm_id", value=len(miss), src_row=int(miss["src_row"].iloc[0]))
        for cid, g in ids.dropna().groupby(ids.dropna()):
            if cid in cert_ids:
                continue
            same = [c for c in cert_ids if "".join(ch for ch in c if ch.isalnum()) == "".join(ch for ch in cid if ch.isalnum())]
            near = same + [c for c in difflib.get_close_matches(cid, cert_ids, n=2, cutoff=0.6) if c not in same]
            hint = (f" Certificate '{same[0]}' differs only in separators or case" if same else f" Closest certificate IDs: {', '.join(near)}" if near else "")
            hint += " (map it in `crm_id_aliases` if it is the same material)." if near else ""
            ctx.add("QAQ-008", "ERROR", t.name, f"CRM '{crm.loc[g.index[0], 'crm_id']}' ({len(g)} results) has no certificate.{hint}",
                    f"ماده مرجع «{crm.loc[g.index[0], 'crm_id']}» ({len(g)} نتیجه) گواهی ندارد.", field="crm_id",
                    value=str(crm.loc[g.index[0], "crm_id"]), src_row=int(crm.loc[g.index[0], "src_row"]),
                    suggested_fix=f"Same material as {near[0]}? Add crm_id_aliases: {{'{crm.loc[g.index[0], 'crm_id']}': '{near[0]}'}}" if near else "Load the certificate.")


@rule("QAQ-010", ("qc_any",))
def qaq_010(ctx):
    """Duplicate–parent linkage: a field, coarse or pulp duplicate without PARENT_ID, or whose PARENT_ID is not a sample
    in the same file (nor in the database for a laboratory file). The link is never inferred from the ID (no suffix
    stripping). WARNING; ERROR when more than 10 % of the duplicates are unlinked."""
    db_ids = set()
    for t in ctx.by_kind("assay"):
        if "sample_id" in t.df:
            db_ids |= set(t.df["sample_id"].dropna().astype(str).str.strip())
    for t in _assays(ctx):
        if "sample_id" not in t.df:
            continue
        df = t.df
        dups = df[df["qc_class"].isin(["FIELD_DUP", "COARSE_DUP", "PULP_DUP"])]
        if dups.empty:
            continue
        ids = set(df["sample_id"].dropna().astype(str).str.strip()) | (db_ids if t.kind == "lab" else set())
        par = dups["parent_id"].astype("string").str.strip() if "parent_id" in dups else pd.Series(pd.NA, index=dups.index)
        bad = dups[par.isna() | (par == "") | ~par.isin(ids).fillna(False)]
        if bad.empty:
            continue
        frac = len(bad) / len(dups)
        sev = "ERROR" if frac > 0.10 else "WARNING"
        for i, r in bad.head(50).iterrows():
            p = r.get("parent_id")
            why = "has no PARENT_ID" if not isinstance(p, str) or not p.strip() else f"points to PARENT_ID '{p}', which is not a sample here"
            ctx.add("QAQ-010", sev, t.name, f"Duplicate {r['sample_id']} ({r['qc_class']}) {why}: it cannot be paired.",
                    f"نمونهٔ تکراری {r['sample_id']} قابل جفت‌کردن نیست (شناسهٔ نمونهٔ اصلی ناموجود یا نامعتبر).",
                    field="parent_id", value=p if isinstance(p, str) else None, src_row=int(r["src_row"]))


@rule("QAQ-007", ("umpire",))
def qaq_007(ctx):
    """Inter-laboratory (umpire) bias: check-laboratory results paired with the primary results by SAMPLE_ID (the
    laboratory file when loaded, else the database). Per element with ≥ `min_pairs` pairs above 10 × DL: median relative
    difference (umpire − primary)/primary and a Wilcoxon signed-rank test on the log ratio. WARNING when |median| >
    `warn_pct` with p < `alpha`; ERROR above `err_pct`. Pairs are kept for the QQ chart."""
    from scipy.stats import wilcoxon
    p = ctx.p("QAQ-007")
    prim = ctx.lab if ctx.lab is not None else next((t for t in ctx.by_kind("assay") if "sample_id" in t.df), None)
    if prim is None:
        return
    pid = prim.df["sample_id"].astype("string").str.strip()
    uid = ctx.umpire.df["sample_id"].astype("string").str.strip()
    first = pd.Series(pid.index, index=pid.values)
    first = first[~first.index.duplicated()]
    for ua in ctx.umpire.analytes:
        pa = next((a for a in prim.analytes if a.analyte == ua.analyte and not a.partial), None)
        if pa is None:
            continue
        from ..io.lab import convert
        rows = []
        for i, s in uid.items():
            j = first.get(s)
            if j is None or ua.parsed.at[i, "flag"] != "VAL" or pa.parsed.at[j, "flag"] != "VAL":
                continue
            u = convert(float(ua.parsed.at[i, "value"]), ua.unit, pa.unit)
            v = float(pa.parsed.at[j, "value"])
            if u > 0 and v > 0:
                rows.append((s, v, u))
        if not rows:
            continue
        arr = pd.DataFrame(rows, columns=["sample_id", "primary", "umpire"])
        ctx.stats.setdefault("umpire_pairs", {})[ua.analyte] = arr
        if len(arr) < p["min_pairs"]:
            ctx.add("QAQ-007", "INFO", ctx.umpire.name, f"{ua.analyte}: only {len(arr)} umpire pairs (fewer than {p['min_pairs']}); bias not tested.",
                    f"{ua.analyte}: تنها {len(arr)} جفت نمونهٔ آزمایشگاه داور؛ اریبی آزمون نشد.", field=ua.column, value=len(arr))
            continue
        rel = 100 * (arr["umpire"] - arr["primary"]) / arr["primary"]
        med = float(rel.median())
        pv = float(wilcoxon(np.log(arr["umpire"] / arr["primary"])).pvalue)
        if abs(med) > p["warn_pct"] and pv < p["alpha"]:
            sev = "ERROR" if abs(med) > p["err_pct"] else "WARNING"
            ctx.add("QAQ-007", sev, ctx.umpire.name, f"{ua.analyte}: umpire laboratory differs from the primary by a median {med:+.1f} % over {len(arr)} pairs (Wilcoxon p = {pv:.1e}).",
                    f"{ua.analyte}: آزمایشگاه داور به‌طور میانه {med:+.1f} درصد با آزمایشگاه اصلی اختلاف دارد ({len(arr)} جفت).",
                    field=ua.column, value=round(med, 2))
        elif pv < p["alpha"]:
            ctx.add("QAQ-007", "INFO", ctx.umpire.name, f"{ua.analyte}: statistically significant inter-laboratory difference over {len(arr)} pairs (median {med:+.2f} %, Wilcoxon p = {pv:.1e}), within the ±{p['warn_pct']:g} % limit.",
                    f"{ua.analyte}: اختلاف بین آزمایشگاه‌ها از نظر آماری معنادار ولی در محدودهٔ ±{p['warn_pct']:g} درصد است ({len(arr)} جفت، میانه {med:+.2f} درصد).", field=ua.column, value=round(med, 2))
        else:
            ctx.add("QAQ-007", "INFO", ctx.umpire.name, f"{ua.analyte}: no significant inter-laboratory bias over {len(arr)} pairs (median {med:+.2f} %, Wilcoxon p = {pv:.2g}).",
                    f"{ua.analyte}: اریبی معنادار بین آزمایشگاه‌ها دیده نشد ({len(arr)} جفت، میانه {med:+.2f} درصد).", field=ua.column, value=round(med, 2))
