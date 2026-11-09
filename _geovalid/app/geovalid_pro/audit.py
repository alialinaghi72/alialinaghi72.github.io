"""Random verification audit (v2 brief REC-07; catalogue ASY-020 audit worksheet).

A seeded, reproducible random selection of database samples is exported as a checklist. The reviewer compares each
row with the original log or laboratory certificate, fills in the result columns and imports the file back. The
summary (and every discrepancy) goes to the evidence pack.

Reproducibility: the population is put in a canonical order (table kind, hole, from, sample ID, source row) before
drawing, so the same data, percentage and seed always give the same selection, whatever the file or row order. The
selection hash (SHA-256 of the seed, percentage and selected keys) is written into every row of the checklist and
checked on import.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd

RESULT_COLS = ["source_document", "verified (Y/N)", "discrepancy", "checked_by", "checked_date"]
YES = {"Y", "YES", "TRUE", "1", "OK", "بله", "آری"}
NO = {"N", "NO", "FALSE", "0", "خیر"}


def settings(params: dict) -> dict:
    s = {"pct": 5.0, "min_n": 100, "seed": 20261109}
    s.update({k: v for k, v in (params.get("random_audit") or {}).items() if v is not None})
    return s


def population(ctx) -> pd.DataFrame:
    """Routine database assay rows (QC excluded), one row per sample, with every analyte as reported."""
    from .rules.interval import QC_TYPES
    parts = []
    for t in ctx.by_kind("assay"):
        df = t.df
        keep = ~df["qc_class"].isin(QC_TYPES) if "qc_class" in df else pd.Series(True, index=df.index)
        d = pd.DataFrame({"table": t.name, "src_row": df["src_row"], "hole_id": df["hole_id"], "from_m": df.get("from_m"),
                          "to_m": df.get("to_m"), "sample_id": df["sample_id"] if "sample_id" in df else pd.NA})[keep]
        for a in t.analytes:
            raw = t.raw[a.column].reindex(d.index) if t.raw is not None and a.column in t.raw else a.parsed.loc[d.index, "value"]
            d[f"db {a.column}"] = raw.astype("string")
        parts.append(d)
    if not parts:
        return pd.DataFrame()
    pop = pd.concat(parts, ignore_index=True)
    pop = pop.sort_values(["table", "hole_id", "from_m", "sample_id", "src_row"], na_position="last", kind="stable").reset_index(drop=True)
    pop["audit_key"] = pop["table"].astype(str) + "|" + pop["src_row"].astype(str)
    return pop


def select(ctx, params: dict) -> tuple[pd.DataFrame, dict]:
    """The checklist (selected rows plus empty result columns) and the selection metadata."""
    s = settings(params)
    pop = population(ctx)
    meta = {"seed": int(s["seed"]), "pct": float(s["pct"]), "min_n": int(s["min_n"]), "population": int(len(pop))}
    if pop.empty:
        return pd.DataFrame(), meta | {"selected": 0, "selection_hash": None}
    n = min(len(pop), max(int(s["min_n"]), math.ceil(len(pop) * float(s["pct"]) / 100.0)))
    rng = np.random.default_rng(int(s["seed"]))
    pick = np.sort(rng.choice(len(pop), size=n, replace=False))
    sel = pop.iloc[pick].copy()
    h = hashlib.sha256(f"{meta['seed']}|{meta['pct']}|{meta['min_n']}|".encode() + "\n".join(sel["audit_key"]).encode()).hexdigest()
    # lab values beside the database values, when a laboratory file is loaded
    if ctx.lab is not None and sel["sample_id"].notna().any():
        lk = ctx.lab.df["sample_id"].astype("string").str.strip()
        first = pd.Series(lk.index, index=lk.values)
        first = first[~first.index.duplicated()]
        for la in ctx.lab.analytes:
            raw = ctx.lab.raw[la.column].astype("string") if ctx.lab.raw is not None and la.column in ctx.lab.raw else la.parsed["value"].astype("string")
            sel[f"lab {la.column}"] = sel["sample_id"].astype("string").str.strip().map(lambda k: raw.get(first.get(k)) if pd.notna(k) and k in first.index else pd.NA)
    sel.insert(0, "audit_id", [f"A{i + 1:04d}" for i in range(len(sel))])
    for c in RESULT_COLS:
        sel[c] = ""
    sel["selection_hash"] = h
    return sel.reset_index(drop=True), meta | {"selected": int(n), "selection_hash": h}


def export(ctx, params: dict, path: str) -> dict:
    """Write the checklist (CSV, or XLSX with a second sheet holding the selection metadata)."""
    sel, meta = select(ctx, params)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() in (".xlsx", ".xlsm"):
        with pd.ExcelWriter(p, engine="openpyxl") as w:
            sel.to_excel(w, sheet_name="checklist", index=False)
            pd.DataFrame([meta]).T.reset_index().rename(columns={"index": "item", 0: "value"}).to_excel(w, sheet_name="selection", index=False)
    else:
        sel.to_csv(p, index=False, encoding="utf-8-sig")
    return meta | {"path": str(p)}


def read_results(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(p, sheet_name=0, dtype=str).fillna("")
    from .io.readers import read_file
    return read_file(str(p))[0].df.astype("string").fillna("")


def summarise(ctx, params: dict, path: str) -> dict:
    """Import a filled checklist: check it is the selection this data and seed produce, and count the results. The 95 %
    Clopper–Pearson upper bound of the discrepancy rate is given, as for ASY-020."""
    from scipy.stats import beta
    df = read_results(path)
    cols = {c.strip().lower(): c for c in df.columns}
    need = ["audit_id", "verified (y/n)"]
    if any(c not in cols for c in need):
        raise ValueError("audit file needs the columns audit_id and 'verified (Y/N)' of the exported checklist")
    sel, meta = select(ctx, params)
    h_file = sorted(set(df[cols["selection_hash"]].astype(str))) if "selection_hash" in cols else []
    same = bool(h_file) and h_file == [meta["selection_hash"]]
    v = df[cols["verified (y/n)"]].astype(str).str.strip().str.upper()
    yes, no = v.isin(YES), v.isin(NO)
    checked = int((yes | no).sum())
    n_no = int(no.sum())
    ub = float(beta.ppf(0.975, n_no + 1, checked - n_no)) if checked and n_no < checked else (1.0 if checked else None)
    disc = []
    for i in df.index[no]:
        r = df.loc[i]
        disc.append({"audit_id": r[cols["audit_id"]], "hole_id": r.get(cols.get("hole_id", ""), ""), "sample_id": r.get(cols.get("sample_id", ""), ""),
                     "from_m": r.get(cols.get("from_m", ""), ""), "discrepancy": r.get(cols.get("discrepancy", ""), ""),
                     "checked_by": r.get(cols.get("checked_by", ""), "")})
    status = ("complete" if checked == len(df) else f"{checked} of {len(df)} rows checked") + ("" if same else " — WARNING: the file is not the selection this dataset and seed produce (data or settings changed since export)")
    return {"status": status, "file": Path(path).name, "seed": meta["seed"], "pct": meta["pct"], "population": meta["population"],
            "selected": meta["selected"], "rows_in_file": int(len(df)), "checked": checked, "verified": int(yes.sum()), "discrepancies": n_no,
            "unchecked": int(len(df) - checked), "rate_pct": round(100 * n_no / checked, 3) if checked else None,
            "upper95_pct": round(100 * ub, 3) if ub is not None else None, "selection_hash": meta["selection_hash"],
            "selection_matches": same, "checked_by": sorted({str(x) for x in df.get(cols.get("checked_by", ""), pd.Series(dtype=str)) if str(x).strip()}),
            "discrepancy_rows": disc}


def pending(ctx, params: dict) -> dict:
    """Evidence-pack entry when no results have been imported yet."""
    _, meta = select(ctx, params)
    if not meta["population"]:
        return {"status": "not applicable (no assay samples)"}
    return {"status": f"selection ready ({meta['selected']} of {meta['population']} samples, seed {meta['seed']}); results not imported yet",
            **meta}
