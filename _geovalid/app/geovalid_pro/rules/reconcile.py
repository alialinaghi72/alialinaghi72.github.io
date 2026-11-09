"""Laboratory-file reconciliation (v2 brief F7: REC-01…06; file format and confirmed assumptions in docs/QAQC_FORMAT.md).

The laboratory file (GEOQAQC format, `io/lab.py`) is compared with the database assay tables by SAMPLE_ID, matched
exactly after trimming surrounding spaces. Nothing is merged, converted in the data or chosen: closest IDs are offered as
suggestions, declared units are converted only for the comparison (and reported), and re-assays are listed, never
resolved. Catalogue IDs with the brief IDs as aliases:

  SMP-004  REC-01  sample in the laboratory file but not in the database, and vice versa
  ASY-020  REC-02  value mismatch, tolerance max(½·DL, 0.1 % relative); sample-ID offset runs; project error rate
           REC-03  unit or scale mismatch (ratio ≈ 10³ or 10⁴)
           REC-04  below-detection (and over-limit) coding mismatch
  ASY-009  REC-05  several results for one sample (re-assays): all listed, with the one the database holds
  CRS-008  REC-06  QC samples in the primary assay table; expected QC samples missing; unknown sample-type codes
"""
from __future__ import annotations

import difflib
import math

import numpy as np
import pandas as pd

from .base import rule
from .interval import QC_TYPES

# status of one database–laboratory pair, best first (used to pick the closest of several re-assays)
OK, CODING, ROUND, SCALE, MISMATCH, MISSING_DB, NO_SOURCE = range(7)
_STATUS = {OK: "match", CODING: "coding", ROUND: "rounded", SCALE: "scale", MISMATCH: "mismatch",
           MISSING_DB: "missing in database", NO_SOURCE: "no laboratory result"}
_DUPS = {"FIELD_DUP", "COARSE_DUP"}


def _key(s: pd.Series) -> pd.Series:
    k = s.astype("string").str.strip()
    return k.where(k != "")


def _db_samples(ctx) -> pd.DataFrame:
    """Database assay rows that carry a sample ID: table, key, row index, location, own QC class."""
    parts = []
    for t in ctx.by_kind("assay"):
        df = t.df
        if "sample_id" not in df or df["sample_id"].isna().all():
            continue
        parts.append(pd.DataFrame({"table": t.name, "key": _key(df["sample_id"]), "idx": df.index, "src_row": df["src_row"],
                                   "hole_id": df["hole_id"], "from_m": df.get("from_m"), "to_m": df.get("to_m"),
                                   "qc_class": df["qc_class"] if "qc_class" in df else "ORIGINAL"}))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["table", "key", "idx", "src_row", "hole_id", "from_m", "to_m", "qc_class"])


def _norm(k: str) -> str:
    return "".join(ch for ch in k.upper() if ch.isalnum())


def _suggest(key: str, pool: list[str], cutoff: float) -> str | None:
    """A candidate for an unmatched ID, taken only from the unmatched IDs of the other side (a mis-keyed ID is an orphan
    on both sides): the same ID apart from letter case and separators, else the closest by difflib ratio."""
    nk = _norm(key)
    same = [c for c in pool if _norm(c) == nk]
    if same:
        return same[0]
    hit = difflib.get_close_matches(key, pool, n=1, cutoff=cutoff)
    return hit[0] if hit else None


def _rec_stats(ctx) -> dict:
    return ctx.stats.setdefault("lab_reconciliation", {"status": "run", "lab_file": ctx.lab.name if ctx.lab is not None else None})


@rule("SMP-004", ("lab_db",))
def smp_004(ctx):
    """REC-01. (a) Routine samples of the laboratory file whose SAMPLE_ID is not in any database assay table → ERROR.
    (b) Database samples not in the laboratory file → ERROR; when the laboratory file carries HOLE_ID, (b) is limited to
    the holes it covers, so a file for one campaign does not flag the rest of the database. QC samples are excluded from
    (a); CRS-008 deals with them. The same ID in another letter case, or the closest ID (difflib ratio ≥ `suggest_cutoff`),
    is offered as a suggestion, never applied."""
    p = ctx.p("SMP-004")
    cutoff, max_sugg = float(p.get("suggest_cutoff", 0.85)), int(p.get("max_suggestions", 200))
    lab = ctx.lab.df
    lk = _key(lab["sample_id"])
    db = _db_samples(ctx)
    db_keys, lab_keys = set(db["key"].dropna()), set(lk.dropna())
    routine = lab[(lab["qc_class"] == "ORIGINAL") & lk.notna()]
    miss = routine[~lk[routine.index].isin(db_keys)]
    miss = miss[~lk[miss.index].duplicated()]
    scope, note = db, ""
    lab_holes = set(lab["hole_id"].dropna().astype(str)) if "hole_id" in lab else set()
    if lab_holes:
        scope = db[db["hole_id"].astype("string").isin(lab_holes).fillna(False)]
        note = " (holes covered by the laboratory file only)"
    orphan = scope[scope["key"].notna() & ~scope["key"].isin(lab_keys)]
    db_pool = sorted(set(db.loc[~db["key"].isin(lab_keys), "key"].dropna()))
    lab_pool = sorted(set(lk[miss.index]))
    for n, (i, r) in enumerate(miss.iterrows()):
        k = lk[i]
        s = _suggest(k, db_pool, cutoff) if n < max_sugg else None
        ctx.add("SMP-004", "ERROR", ctx.lab.name, f"Sample {k} is in the laboratory file (batch {r.get('batch') or '—'}) but in no database assay table." + (f" Closest database ID: {s}." if s else ""),
                f"نمونهٔ {k} در فایل آزمایشگاه هست ولی در هیچ جدول آنالیز پایگاه داده نیست." + (f" نزدیک‌ترین شناسه: {s}." if s else ""),
                hole_id=r.get("hole_id") if isinstance(r.get("hole_id"), str) else None, field="sample_id", value=k, src_row=int(r["src_row"]),
                suggested_fix=f"Is {k} the same sample as {s}? Correct the ID at the source." if s else "Import the result, or explain why it is not in the database.", alias="REC-01")
    for n, r in enumerate(orphan.itertuples()):
        s = _suggest(r.key, lab_pool, cutoff) if n < max_sugg else None
        ctx.add("SMP-004", "ERROR", r.table, f"Database sample {r.key} has no result in the laboratory file{note}." + (f" Closest laboratory ID: {s}." if s else ""),
                f"نمونهٔ {r.key} پایگاه داده در فایل آزمایشگاه نتیجه‌ای ندارد." + (f" نزدیک‌ترین شناسه: {s}." if s else ""),
                hole_id=r.hole_id if isinstance(r.hole_id, str) else None, from_m=r.from_m if pd.notna(r.from_m) else None,
                to_m=r.to_m if pd.notna(r.to_m) else None, field="sample_id", value=r.key, src_row=int(r.src_row), alias="REC-01")
    st = _rec_stats(ctx)
    st["samples"] = {"lab_rows": int(len(lab)), "lab_routine": int(len(routine)), "lab_routine_not_in_db": int(len(miss)),
                     "db_samples_in_scope": int(scope["key"].notna().sum()), "db_samples_not_in_lab": int(len(orphan)),
                     "scope": "holes in the laboratory file" if lab_holes else "all database samples"}


def _dl_lookup(lab_df, la) -> tuple[pd.Series, float]:
    """Detection limit per laboratory batch (largest `<x` written in the batch) and for the whole column."""
    p = la.parsed
    bdl = p["flag"] == "BDL"
    col = float(p.loc[bdl, "dl"].max()) if bdl.any() else np.nan
    if "batch" in lab_df and bdl.any():
        by = p.loc[bdl, "dl"].groupby(lab_df.loc[bdl[bdl].index, "batch"]).max()
    else:
        by = pd.Series(dtype=float)
    return by, col


def _decimals(s) -> int | None:
    if not isinstance(s, str):
        s = None if s is None or (isinstance(s, float) and math.isnan(s)) else str(s)
    if not s:
        return None
    s = s.strip().replace(",", ".")
    if "e" in s.lower() or not any(ch.isdigit() for ch in s):
        return None
    return len(s.split(".", 1)[1]) if "." in s else 0


def _pairs(ctx, t, a, la, lab, lk, db_t, p) -> pd.DataFrame:
    """All database–laboratory pairs for one analyte, with a status per pair (vectorised)."""
    from ..io.lab import convert
    d = pd.DataFrame({"idx": db_t["idx"].to_numpy(), "key": db_t["key"].to_numpy(), "src_row": db_t["src_row"].to_numpy(),
                      "hole_id": db_t["hole_id"].to_numpy(), "from_m": db_t["from_m"].to_numpy(), "to_m": db_t["to_m"].to_numpy()})
    lab_rows = pd.DataFrame({"lidx": lk.index, "key": lk.to_numpy()}).dropna()
    m = d.merge(lab_rows, on="key", how="inner")
    if m.empty:
        return m
    pd_, pl = a.parsed, la.parsed
    f = convert(1.0, la.unit, a.unit) if (a.unit_declared and la.unit_declared) else 1.0
    m["fd"], m["vd"], m["dld"] = pd_.loc[m["idx"], "flag"].to_numpy(), pd_.loc[m["idx"], "value"].to_numpy(float), pd_.loc[m["idx"], "dl"].to_numpy(float)
    m["fl"] = pl.loc[m["lidx"], "flag"].to_numpy()
    m["vl"] = pl.loc[m["lidx"], "value"].to_numpy(float) * f
    m["dll"] = pl.loc[m["lidx"], "dl"].to_numpy(float) * f
    m["na_l"] = pl.loc[m["lidx"], "not_analysed"].to_numpy(bool)
    m["code_l"] = pl.loc[m["lidx"], "code"].to_numpy(object)
    m["batch"] = lab.loc[m["lidx"], "batch"].to_numpy(object) if "batch" in lab else None
    by, col = _dl_lookup(lab, la)
    dl = m["batch"].map(by).astype(float) * f if len(by) else pd.Series(np.nan, index=m.index)
    dl = dl.fillna(col * f if not np.isnan(col) else np.nan)
    db_dl = pd_.loc[pd_["flag"] == "BDL", "dl"].max()
    m["dl"] = dl.fillna(db_dl if pd.notna(db_dl) else 0.0).to_numpy(float)
    tol = np.maximum(float(p.get("dl_frac", 0.5)) * m["dl"], float(p.get("rel_tol", 0.001)) * np.abs(m["vl"].fillna(0)))
    m["tol"] = tol
    fd, fl, vd, vl = m["fd"], m["fl"], m["vd"], m["vl"]
    num_d, num_l = fd.isin(["VAL", "ODL"]), fl.isin(["VAL", "ODL"])
    diff = (vd - vl).abs()
    both = num_d & num_l
    ok_val = both & (diff <= tol + 1e-12) & (fd == fl)
    # over-limit coding: the database holds the limit as a plain value (or the reverse)
    odl_code = both & (fd != fl) & (diff <= tol + 1e-12)
    ratio = np.where(both & (vd > 0) & (vl > 0), vd / vl.where(vl > 0, np.nan), np.nan)
    lr = np.log10(ratio)
    scale_k = np.full(len(m), np.nan)
    st = math.log10(1 + float(p.get("scale_tol", 0.03)))
    for k in (3, 4, -3, -4):
        scale_k[np.abs(lr - k) < st] = k
    m["scale_k"] = scale_k
    raw = t.raw[a.column].reindex(m["idx"]).to_numpy(object) if t.raw is not None and a.column in t.raw else [None] * len(m)
    dec = pd.Series([_decimals(x) for x in raw], index=m.index, dtype=object)
    rounded = both & ~ok_val & ~odl_code & dec.notna() & np.isnan(scale_k)
    if rounded.any():
        rr = [abs(round(v, int(n)) - w) <= 10 ** (-int(n)) * 0.5 + 1e-12 if n is not None and not pd.isna(n) else False
              for v, w, n in zip(vl[rounded], vd[rounded], dec[rounded])]
        rounded.loc[rounded] = rr
    bdl_d, bdl_l = fd == "BDL", fl == "BDL"
    coding = (bdl_d & bdl_l & ~(np.abs(m["dld"] - m["dll"]) <= np.maximum(m["tol"], 1e-12))) \
        | (bdl_l & num_d & (vd <= m["dll"] * 1.0001)) | (bdl_d & num_l & (vl <= m["dld"] * 1.0001)) | odl_code
    same_bdl = bdl_d & bdl_l & (np.abs(m["dld"] - m["dll"]) <= np.maximum(m["tol"], 1e-12))
    empty_d = fd == "NA"
    lab_none = m["na_l"] | (fl == "NA")
    m["code_d"] = pd_.loc[m["idx"], "code"].to_numpy(object)
    code_d = m["code_d"].astype("string").str.strip().str.upper().fillna("")
    code_l = m["code_l"].astype("string").str.strip().str.upper().fillna("")
    same_code = (fd == fl) & fd.isin(["TXT", "SNT"]) & ((fd == "SNT") | ((code_d == code_l) & (code_d != "")))
    txt_vs_none = fd.isin(["TXT", "SNT"]) & lab_none & ~same_code   # both say "no value", written differently
    status = np.select(
        [empty_d & lab_none, ok_val | same_bdl | same_code, txt_vs_none, lab_none & ~empty_d, empty_d & ~lab_none, coding, rounded, ~np.isnan(scale_k)],
        [-1, OK, CODING, NO_SOURCE, MISSING_DB, CODING, ROUND, SCALE], default=MISMATCH)
    m["status"] = status
    m["diff"] = diff
    return m[m["status"] >= 0]


@rule("ASY-020", ("lab_db",))
def asy_020(ctx):
    """REC-02/03/04. Each database result is compared with the laboratory result of the same SAMPLE_ID and element
    (declared units converted for the comparison; every conversion is listed). Tolerance = max(`dl_frac`·DL,
    `rel_tol`·|lab value|), DL being the largest `<x` of the laboratory batch. With re-assays the closest laboratory
    result is used (ASY-009 lists them all). Classes: value mismatch → ERROR (REC-02); the database holds the laboratory
    value rounded to fewer decimals → WARNING; ratio ≈ 10³ / 10⁴ → ERROR (REC-03), one issue per column when most pairs
    share the factor; below-detection or over-limit coding differs → WARNING (REC-04); a database value with no laboratory
    result (IS, LNR, empty) or a laboratory result missing from the database → ERROR. A run of ≥ `offset_run_min`
    mismatches whose database values equal the laboratory values of samples ±1…±`offset_max` in laboratory order is one
    ERROR (sample-ID offset). The project error rate (mismatches / compared values) is reported with its 95 %
    Clopper–Pearson upper bound: WARNING above `err_warn_pct`, ERROR above `err_err_pct`."""
    from scipy.stats import beta
    p = ctx.p("ASY-020")
    lab = ctx.lab.df
    lk = _key(lab["sample_id"])
    db = _db_samples(ctx)
    # laboratory order of the routine samples only, so QC inserts never break a sample-ID offset run
    order = lab[lab["qc_class"] == "ORIGINAL"].sort_values([c for c in ("batch", "seq") if c in lab], kind="stable").index
    pos = pd.Series(np.arange(len(order)), index=order)
    summary, n_cmp, n_bad = [], 0, 0
    for t in ctx.by_kind("assay"):
        db_t = db[db["table"] == t.name]
        db_t = db_t[db_t["key"].notna()]
        if db_t.empty:
            continue
        for a in t.analytes:
            cands = [x for x in ctx.lab.analytes if x.analyte == a.analyte]
            if not cands:
                continue
            la = next((x for x in cands if x.qualifier == a.qualifier), cands[0])
            m = _pairs(ctx, t, a, la, lab, lk, db_t, p)
            if m.empty:
                continue
            if a.unit_declared and la.unit_declared and a.unit != la.unit:
                ctx.add("ASY-020", "INFO", t.name, f"{a.column} ({a.unit}) compared with laboratory {la.column} ({la.unit}) after converting the declared laboratory unit.",
                        f"{a.column} با {la.column} آزمایشگاه پس از تبدیل واحد اعلام‌شده مقایسه شد ({la.unit} → {a.unit}).", field=a.column, value=f"{la.unit}->{a.unit}", alias="REC-03")
            m = m.sort_values(["idx", "status", "diff"], na_position="last").drop_duplicates("idx")    # closest re-assay
            bad = m[m["status"] != OK]
            # REC-03 column-level scale
            sc = bad[bad["status"] == SCALE]
            col_scale = None
            n_both = int(m["fd"].isin(["VAL", "ODL"]).sum())
            if len(sc) >= int(p.get("min_scale_pairs", 5)):
                k = sc["scale_k"].mode().iloc[0]
                if (sc["scale_k"] == k).sum() >= 0.5 * max(n_both, 1):
                    col_scale = k
                    ctx.add("ASY-020", "ERROR", t.name, f"{a.column}: {int((sc['scale_k'] == k).sum())} of {n_both} database values are ×10^{int(k)} the laboratory {la.column} values: unit or scale mismatch for the column.",
                            f"{a.column}: {int((sc['scale_k'] == k).sum())} از {n_both} مقدار پایگاه داده ۱۰ به توان {int(k)} برابر مقدار آزمایشگاه است: عدم تطابق واحد یا مقیاس ستون.",
                            field=a.column, value=f"x1e{int(k)}", expected=f"{la.unit}", alias="REC-03",
                            suggested_fix="Check the unit of the database column against the laboratory certificate.")
            # sample-ID offset runs
            offset_rows = set()
            mm = bad[bad["status"] == MISMATCH]
            if len(mm) >= int(p.get("offset_run_min", 5)):
                lp = la.parsed
                from ..io.lab import convert
                f = convert(1.0, la.unit, a.unit) if (a.unit_declared and la.unit_declared) else 1.0
                lv = (lp["value"] * f).reindex(order).to_numpy(float)
                cand = {}                      # every offset each mismatched row agrees with
                omax = int(p.get("offset_max", 3))
                for r in mm.itertuples():
                    p0 = pos.get(r.lidx)
                    if p0 is None:
                        continue
                    ds = [dd for dd in range(-omax, omax + 1) if dd and 0 <= p0 + dd < len(lv) and abs(lv[p0 + dd] - r.vd) <= r.tol + 1e-12]
                    if ds:
                        cand[r.idx] = (ds, r)
                votes = pd.Series([dd for ds, _ in cand.values() for dd in ds], dtype=float).value_counts()
                by_d, taken = {}, set()
                for dd in votes.index:         # the offset most rows agree with wins; a chance match elsewhere does not split a run
                    for idx, (ds, r) in cand.items():
                        if idx not in taken and dd in ds:
                            by_d.setdefault(int(dd), []).append(r)
                            taken.add(idx)
                for dd, rows in by_d.items():
                    rows.sort(key=lambda r: r.src_row)
                    run = [rows[0]]
                    for r in rows[1:] + [None]:
                        if r is not None and r.src_row - run[-1].src_row <= 2:
                            run.append(r)
                            continue
                        if len(run) >= int(p.get("offset_run_min", 5)):
                            offset_rows |= {x.idx for x in run}
                            ctx.add("ASY-020", "ERROR", t.name, f"{a.column}: {len(run)} consecutive database values ({run[0].key} … {run[-1].key}) equal the laboratory results of the samples {dd:+d} place(s) away: sample-ID offset when the results were merged.",
                                    f"{a.column}: {len(run)} مقدار پیاپی پایگاه داده برابر نتیجهٔ نمونه‌های {dd:+d} ردیف آن‌سوتر در فایل آزمایشگاه است: جابه‌جایی شناسهٔ نمونه هنگام ادغام.",
                                    hole_id=run[0].hole_id if isinstance(run[0].hole_id, str) else None, from_m=run[0].from_m if pd.notna(run[0].from_m) else None,
                                    field=a.column, value=f"offset {dd:+d} x{len(run)}", src_row=int(run[0].src_row), alias="REC-02",
                                    suggested_fix="Re-merge the results by SAMPLE_ID for the run (reviewer).")
                        if r is not None:
                            run = [r]
            for r in bad.itertuples():
                if r.idx in offset_rows or (col_scale is not None and r.status == SCALE and r.scale_k == col_scale):
                    continue
                loc = dict(hole_id=r.hole_id if isinstance(r.hole_id, str) else None, from_m=r.from_m if pd.notna(r.from_m) else None,
                           to_m=r.to_m if pd.notna(r.to_m) else None, field=a.column, src_row=int(r.src_row))
                dtxt = _txt(r.fd, r.vd, r.dld, r.code_d)
                ltxt = _txt(r.fl, r.vl, r.dll, r.code_l)
                if r.status == CODING:
                    ctx.add("ASY-020", "WARNING", t.name, f"{r.key} {a.column}: detection-limit coding differs (database {dtxt}, laboratory {ltxt}).",
                            f"{r.key} {a.column}: کدگذاری حد تشخیص متفاوت است (پایگاه داده {dtxt}، آزمایشگاه {ltxt}).", value=dtxt, expected=ltxt, alias="REC-04", **loc)
                elif r.status == ROUND:
                    ctx.add("ASY-020", "WARNING", t.name, f"{r.key} {a.column}: the database holds the laboratory value rounded ({dtxt} vs {ltxt}).",
                            f"{r.key} {a.column}: پایگاه داده مقدار آزمایشگاه را گرد کرده است ({dtxt} در برابر {ltxt}).", value=dtxt, expected=ltxt, alias="REC-02", **loc)
                elif r.status == SCALE:
                    ctx.add("ASY-020", "ERROR", t.name, f"{r.key} {a.column}: database {dtxt} is ×10^{int(r.scale_k)} the laboratory {ltxt}: unit or scale error.",
                            f"{r.key} {a.column}: مقدار پایگاه داده {dtxt} برابر ۱۰ به توان {int(r.scale_k)} مقدار آزمایشگاه {ltxt} است.", value=dtxt, expected=ltxt, alias="REC-03", **loc)
                elif r.status == NO_SOURCE:
                    ctx.add("ASY-020", "ERROR", t.name, f"{r.key} {a.column}: the database holds {dtxt} but the laboratory reports {ltxt or 'nothing'} (not analysed).",
                            f"{r.key} {a.column}: پایگاه داده مقدار {dtxt} دارد ولی آزمایشگاه نتیجه‌ای گزارش نکرده است ({ltxt or '—'}).", value=dtxt, expected=ltxt or "not analysed", alias="REC-02", **loc)
                elif r.status == MISSING_DB:
                    ctx.add("ASY-020", "ERROR", t.name, f"{r.key} {a.column}: the laboratory reports {ltxt} but the database cell is empty.",
                            f"{r.key} {a.column}: آزمایشگاه {ltxt} گزارش کرده ولی خانهٔ پایگاه داده خالی است.", value=None, expected=ltxt, alias="REC-02", **loc)
                else:
                    ctx.add("ASY-020", "ERROR", t.name, f"{r.key} {a.column}: database {dtxt} ≠ laboratory {ltxt} (tolerance {r.tol:.3g}).",
                            f"{r.key} {a.column}: مقدار پایگاه داده {dtxt} با آزمایشگاه {ltxt} برابر نیست (رواداری {r.tol:.3g}).", value=dtxt, expected=ltxt, alias="REC-02", **loc)
            counts = {_STATUS[k]: int((m["status"] == k).sum()) for k in _STATUS}
            compared = int(m["status"].isin([OK, CODING, ROUND, SCALE, MISMATCH]).sum())
            wrong = int(m["status"].isin([SCALE, MISMATCH]).sum())
            n_cmp += compared
            n_bad += wrong
            summary.append({"table": t.name, "column": a.column, "lab_column": la.column, "unit": a.unit, "lab_unit": la.unit,
                            "pairs": int(len(m)), **counts})
    st = _rec_stats(ctx)
    st["values"] = summary
    if n_cmp:
        ub = float(beta.ppf(0.975, n_bad + 1, n_cmp - n_bad)) if n_bad < n_cmp else 1.0
        e = n_bad / n_cmp
        st["error_rate"] = {"compared": n_cmp, "mismatched": n_bad, "rate_pct": round(100 * e, 3), "upper95_pct": round(100 * ub, 3)}
        sev = "ERROR" if 100 * ub > float(p.get("err_err_pct", 1.0)) else "WARNING" if 100 * ub > float(p.get("err_warn_pct", 0.5)) else "INFO"
        ctx.add("ASY-020", sev, ctx.lab.name, f"Laboratory verification: {n_bad} of {n_cmp} compared values disagree beyond tolerance or scale ({100 * e:.2f} %; 95 % upper bound {100 * ub:.2f} %).",
                f"راستی‌آزمایی با فایل آزمایشگاه: {n_bad} از {n_cmp} مقدار مقایسه‌شده مغایرت دارند ({100 * e:.2f} درصد؛ حد بالای ۹۵ درصد {100 * ub:.2f} درصد).",
                field="error_rate", value=round(100 * e, 3), expected=f"upper bound ≤ {p.get('err_warn_pct', 0.5)} %", alias="REC-02")


def _same(d: pd.Series, lr: pd.Series, f: float) -> bool:
    """One database result and one laboratory result agree: equal flags and values within 0.1 % (or equal DLs)."""
    if d["flag"] != lr["flag"]:
        return False
    if d["flag"] in ("VAL", "ODL"):
        lv = float(lr["value"]) * f
        return abs(float(d["value"]) - lv) <= max(0.001 * abs(lv), 1e-12)
    if d["flag"] == "BDL":
        return abs(float(d["dl"]) - float(lr["dl"]) * f) <= max(0.001 * abs(float(d["dl"])), 1e-12)
    return d["flag"] == "NA" or str(d["code"]).strip().upper() == str(lr["code"]).strip().upper()


def _txt(flag, v, dl, code=None) -> str:
    if flag == "BDL":
        return f"<{dl:g}" if pd.notna(dl) else "<DL"
    if flag == "ODL":
        return f">{v:g}"
    if flag == "VAL":
        return f"{v:g}"
    if isinstance(code, str) and code:
        return code
    return "" if flag == "NA" else "sentinel" if flag == "SNT" else str(flag)


@rule("ASY-009", ("lab",))
def asy_009(ctx):
    """REC-05. A SAMPLE_ID that occurs more than once in the laboratory file is a re-assay (owner's confirmation). Every
    result is listed with its batch, and for each element the result the database holds (or none, or not in the
    database). GEOVALID never chooses one. INFO. A database value that equals the umpire laboratory's result and none of
    the primary results → ERROR: umpire results never replace the primary (02 §4.9.3, ladder step 5)."""
    from ..io.lab import convert
    lab = ctx.lab.df
    lk = _key(lab["sample_id"])
    db = _db_samples(ctx)
    dbk = db[db["key"].notna()].drop_duplicates("key").set_index("key")
    rep = lk[lk.duplicated(keep=False) & lk.notna()]
    tables = {t.name: t for t in ctx.by_kind("assay")}
    for k, g in rep.groupby(rep):
        rows = lab.loc[g.index]
        parts, held = [], []
        for la in ctx.lab.analytes:
            vals = [_txt(la.parsed.at[i, "flag"], la.parsed.at[i, "value"], la.parsed.at[i, "dl"], la.parsed.at[i, "code"]) for i in g.index]
            parts.append(f"{la.column}: {' / '.join(v or '—' for v in vals)}")
            if k in dbk.index:
                r = dbk.loc[k]
                t = tables[r["table"]]
                a = next((x for x in t.analytes if x.analyte == la.analyte), None)
                if a is None:
                    continue
                j = r["idx"]
                dv = _txt(a.parsed.at[j, "flag"], a.parsed.at[j, "value"], a.parsed.at[j, "dl"], a.parsed.at[j, "code"])
                f = convert(1.0, la.unit, a.unit) if (a.unit_declared and la.unit_declared) else 1.0
                which = [f"row {int(rows.loc[i, 'src_row'])}" for i in g.index if _same(a.parsed.loc[j], la.parsed.loc[i], f)]
                held.append(f"{a.column} = {dv} ({'= laboratory ' + ', '.join(which) if which else 'matches none of them'})")
        where = "database: " + ("; ".join(held) if held else "sample not in the database" if k not in dbk.index else "no common element")
        batches = ", ".join(f"{b if isinstance(b, str) else '—'} (row {int(r)})" for b, r in zip(rows["batch"] if "batch" in rows else [None] * len(rows), rows["src_row"]))
        ctx.add("ASY-009", "INFO", ctx.lab.name, f"Sample {k} has {len(g)} laboratory results ({batches}): {'; '.join(parts)}. {where}. GEOVALID does not choose between them.",
                f"نمونهٔ {k} دارای {len(g)} نتیجهٔ آزمایشگاهی است ({batches}). {where}. انتخاب میان آن‌ها با کاربر است.",
                field="sample_id", value=k, src_row=int(rows["src_row"].iloc[1]), alias="REC-05")
    if ctx.umpire is None or dbk.empty:
        return
    uk = _key(ctx.umpire.df["sample_id"])
    for ua in ctx.umpire.analytes:
        for t in ctx.by_kind("assay"):
            a = next((x for x in t.analytes if x.analyte == ua.analyte), None)
            la = next((x for x in ctx.lab.analytes if x.analyte == ua.analyte), None)
            if a is None:
                continue
            f_u = convert(1.0, ua.unit, a.unit) if (a.unit_declared and ua.unit_declared) else 1.0
            f_l = convert(1.0, la.unit, a.unit) if la is not None and a.unit_declared and la.unit_declared else 1.0
            for i, k in uk.dropna().items():
                if k not in dbk.index or dbk.loc[k, "table"] != t.name or ua.parsed.at[i, "flag"] != "VAL":
                    continue
                j = dbk.loc[k, "idx"]
                if a.parsed.at[j, "flag"] != "VAL":
                    continue
                dv, uv = float(a.parsed.at[j, "value"]), float(ua.parsed.at[i, "value"]) * f_u
                tol = max(0.001 * abs(uv), 1e-12)
                if abs(dv - uv) > tol:
                    continue
                prim = [float(la.parsed.at[x, "value"]) * f_l for x in lk[lk == k].index if la is not None and la.parsed.at[x, "flag"] == "VAL"]
                if prim and all(abs(dv - pv) > max(0.001 * abs(pv), 1e-12) for pv in prim):
                    ctx.add("ASY-009", "ERROR", t.name, f"{k} {a.column}: the database holds the umpire laboratory's result ({uv:g}), not the primary result ({', '.join(f'{x:g}' for x in prim)}).",
                            f"{k} {a.column}: پایگاه داده نتیجهٔ آزمایشگاه داور را نگه داشته است نه نتیجهٔ آزمایشگاه اصلی.",
                            hole_id=dbk.loc[k, "hole_id"] if isinstance(dbk.loc[k, "hole_id"], str) else None, field=a.column, value=dv,
                            expected=", ".join(f"{x:g}" for x in prim), src_row=int(dbk.loc[k, "src_row"]), alias="REC-05")


@rule("CRS-008", ("assay",))
def crs_008(ctx):
    """REC-06 and the catalogue rule. (a) A database assay row whose type is CRM, BLANK, PULP_DUP or UMPIRE (its own
    sample-type column, or the laboratory file's SAMPLE_TYPE for the same SAMPLE_ID) and which carries a hole and depths
    → CRITICAL: it would be composited as a downhole interval. Field or coarse duplicates carried with depths that repeat
    their parent's interval → CRITICAL; with no depths → ERROR (QC in the primary table). (b) QC samples the database
    types as QC but the laboratory file does not contain → ERROR (expected QC missing). (c) Unknown SAMPLE_TYPE codes in
    the laboratory file → WARNING with counts; those rows are not used until the code is added to `lab_sample_types`.
    (d) Laboratory QC rows with no analysed value at all → WARNING."""
    db = _db_samples(ctx)
    lab = ctx.lab.df if ctx.lab is not None else None
    lab_cls = {}
    if lab is not None:
        lk = _key(lab["sample_id"])
        lab_cls = dict(zip(lk[lk.notna()], lab.loc[lk.notna(), "qc_class"]))
    hard = {"CRM", "BLANK", "PULP_DUP", "UMPIRE"}
    for t in ctx.by_kind("assay"):
        df = t.df
        own = df["qc_class"] if "qc_class" in df else pd.Series("ORIGINAL", index=df.index)
        key = _key(df["sample_id"]) if "sample_id" in df else pd.Series(pd.NA, index=df.index, dtype="string")
        from_lab = key.map(lab_cls) if lab_cls else pd.Series(None, index=df.index)
        cls = own.where(own.isin(QC_TYPES), from_lab)
        qc = cls.isin(QC_TYPES)
        if not qc.any():
            continue
        has_depth = df["hole_id"].notna() & df["from_m"].notna() & df["to_m"].notna()
        for i in df.index[qc]:
            c = cls[i]
            src = "laboratory file" if not own[i] in QC_TYPES else "sample type"
            k = key[i] if pd.notna(key[i]) else f"row {int(df.at[i, 'src_row'])}"
            loc = dict(hole_id=df.at[i, "hole_id"] if isinstance(df.at[i, "hole_id"], str) else None,
                       from_m=df.at[i, "from_m"] if pd.notna(df.at[i, "from_m"]) else None, to_m=df.at[i, "to_m"] if pd.notna(df.at[i, "to_m"]) else None,
                       field="sample_type", value=c, src_row=int(df.at[i, "src_row"]), alias="REC-06")
            if src == "sample type":
                continue          # typed as QC in the database itself: recognised and excluded from interval rules
            if c in hard and has_depth[i]:
                ctx.add("CRS-008", "CRITICAL", t.name, f"{k} is a {c} (by the {src}) but is stored as a downhole interval {loc['hole_id']} {loc['from_m']:g}–{loc['to_m']:g} m: it would enter composites as real grade.",
                        f"{k} یک نمونهٔ کنترلی ({c}) است ولی به‌صورت بازهٔ درون‌چاهی ذخیره شده و وارد کامپوزیت می‌شود.", **loc,
                        suggested_fix="Remove the QC row from the interval table (the QC record is kept in the QC register).")
            elif c in _DUPS and has_depth[i]:
                ctx.add("CRS-008", "CRITICAL", t.name, f"{k} is a {c} (by the laboratory file) stored as a routine interval {loc['hole_id']} {loc['from_m']:g}–{loc['to_m']:g} m: the interval is sampled twice.",
                        f"{k} نمونهٔ تکراری ({c}) است که به‌صورت بازهٔ عادی ذخیره شده است: بازه دو بار نمونه‌برداری شده است.", **loc)
            else:
                ctx.add("CRS-008", "ERROR", t.name, f"{k} is a {c} (by the laboratory file) but sits in the primary assay table as a routine sample.",
                        f"{k} یک نمونهٔ کنترلی ({c}) است ولی در جدول اصلی آنالیز به‌عنوان نمونهٔ عادی قرار دارد.", **loc)
        typed = own.isin(QC_TYPES) & has_depth
        if typed.any():
            ctx.add("CRS-008", "INFO", t.name, f"{int(typed.sum())} QC rows typed in the database carry a hole and depths; GEOVALID excludes them from interval checks, and exports to estimation must exclude them too.",
                    f"{int(typed.sum())} ردیف کنترلی که در پایگاه داده نوع‌گذاری شده‌اند چاه و عمق دارند؛ در خروجی برای تخمین باید حذف شوند.",
                    field="sample_type", value=int(typed.sum()), alias="REC-06")
        if lab is not None:
            lab_keys = set(lab_cls)
            miss = df.index[own.isin(QC_TYPES) & key.notna() & ~key.isin(lab_keys)]
            for i in miss[:200]:
                ctx.add("CRS-008", "ERROR", t.name, f"QC sample {key[i]} ({own[i]}) is in the database but not in the laboratory file: its result cannot be verified.",
                        f"نمونهٔ کنترلی {key[i]} ({own[i]}) در پایگاه داده هست ولی در فایل آزمایشگاه نیست.", field="sample_id", value=key[i],
                        src_row=int(df.at[i, "src_row"]), alias="REC-06")
    if lab is None:
        return
    unk = lab[lab["qc_class"] == "UNKNOWN"]
    if len(unk):
        codes = unk["sample_type"].fillna("(empty)").astype(str).value_counts()
        ctx.add("CRS-008", "WARNING", ctx.lab.name, f"{len(unk)} laboratory rows have unknown SAMPLE_TYPE codes ({', '.join(f'{c} × {n}' for c, n in codes.items())}); they are not used until the code is added to the profile (lab_sample_types).",
                f"{len(unk)} ردیف فایل آزمایشگاه کد نوع نمونهٔ ناشناخته دارند ({', '.join(f'{c} × {n}' for c, n in codes.items())}).",
                field="sample_type", value=", ".join(codes.index[:10]), src_row=int(unk["src_row"].iloc[0]), alias="REC-06")
    qcl = lab[lab["qc_class"].isin(QC_TYPES)]
    if len(qcl) and ctx.lab.analytes:
        anyval = np.zeros(len(qcl), bool)
        for la in ctx.lab.analytes:
            anyval |= la.parsed.loc[qcl.index, "flag"].isin(["VAL", "BDL", "ODL"]).to_numpy()
        for i in qcl.index[~anyval][:100]:
            ctx.add("CRS-008", "WARNING", ctx.lab.name, f"QC sample {lab.at[i, 'sample_id']} ({lab.at[i, 'qc_class']}) has no analysed result for any element.",
                    f"نمونهٔ کنترلی {lab.at[i, 'sample_id']} برای هیچ عنصری نتیجهٔ آنالیز ندارد.", field="sample_id", value=lab.at[i, "sample_id"],
                    src_row=int(lab.at[i, "src_row"]), alias="REC-06")
