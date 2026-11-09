"""Sample-identifier rules (v2 INT-07): unique sample IDs (SMP-001) and QC-insert-aware numbering (SMP-002)."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .base import rule
from .interval import QC_TYPES

_ID = re.compile(r"^(.*?)(\d+)$")


def _sample_rows(ctx) -> pd.DataFrame:
    parts = []
    for t in ctx.by_kind("assay"):
        df = t.df
        if "sample_id" not in df or df["sample_id"].isna().all():
            continue
        cls = df["qc_class"] if "qc_class" in df else pd.Series("ORIGINAL", index=df.index)
        parts.append(pd.DataFrame({"table": t.name, "sample_id": df["sample_id"].astype("string").str.strip(), "hole_id": df["hole_id"],
                                   "from_m": df.get("from_m"), "qc": cls.isin(QC_TYPES), "src_row": df["src_row"]}))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _lab_numbers(ctx) -> pd.DataFrame:
    """Sample IDs issued in the laboratory file (routine and QC): numbers the database is not expected to hold as
    routine samples, so they never count as gaps in SMP-002."""
    if ctx.lab is None:
        return pd.DataFrame()
    df = ctx.lab.df
    return pd.DataFrame({"table": ctx.lab.name, "sample_id": df["sample_id"].astype("string").str.strip(), "hole_id": df["hole_id"],
                         "from_m": df.get("from_m"), "qc": df["qc_class"] != "ORIGINAL", "src_row": df["src_row"], "lab": True})


@rule("SMP-001", ("assay",))
def smp_001(ctx):
    """INT-07: a sample ID used by more than one row anywhere in the assay tables (QC samples included). CRITICAL: two
    results under one ID cannot both be right, and the wrong one may be used in estimation."""
    s = _sample_rows(ctx)
    if s.empty:
        return
    s = s[s["sample_id"].notna() & (s["sample_id"] != "")]
    dup = s[s.duplicated("sample_id", keep=False)]
    for sid, g in dup.groupby("sample_id"):
        where = "; ".join(f"{r.table} row {r.src_row} ({r.hole_id if isinstance(r.hole_id, str) else 'QC'} {r.from_m if pd.notna(r.from_m) else ''})" for r in g.head(4).itertuples())
        ctx.add("SMP-001", "CRITICAL", g["table"].iloc[0], f"Sample ID '{sid}' is used by {len(g)} rows: {where}.",
                f"شناسهٔ نمونهٔ «{sid}» در {len(g)} ردیف به کار رفته است: {where}.", hole_id=g["hole_id"].dropna().iloc[0] if g["hole_id"].notna().any() else None,
                field="sample_id", value=sid, src_row=int(g["src_row"].iloc[1]))


@rule("SMP-002", ("assay",))
def smp_002(ctx):
    """INT-07: numbering of sample IDs (prefix + number). (a) Missing numbers inside a numbering run, counting QC
    samples inserted in the same sequence as used numbers so CRMs, blanks and duplicates never create false gaps;
    jumps larger than `max_gap_n` (100) start a new block (INFO). (b) Original samples whose numbers do not increase
    (or decrease) monotonically downhole. WARNING (Minor)."""
    p = ctx.p("SMP-002")
    s = _sample_rows(ctx)
    if s.empty:
        return
    lab = _lab_numbers(ctx)
    if not lab.empty:      # QC inserts known only from the laboratory file also count as used numbers (R1)
        lab = lab[~lab["sample_id"].isin(set(s["sample_id"].dropna()))].drop_duplicates("sample_id")
        s = pd.concat([s.assign(lab=False), lab], ignore_index=True)
    m = s["sample_id"].fillna("").str.extract(_ID)
    s["prefix"], s["num"] = m[0], pd.to_numeric(m[1], errors="coerce")
    s = s[s["num"].notna()]
    for pre, g in s.groupby("prefix"):
        nums = np.unique(g["num"].to_numpy(np.int64))
        if len(nums) < 2:
            continue
        gaps = np.diff(nums)
        ranges, blocks, missing = [], 0, 0
        for k in np.where(gaps > 1)[0]:
            if gaps[k] > p["max_gap_n"]:
                blocks += 1
                continue
            missing += int(gaps[k] - 1)
            ranges.append(f"{pre}{nums[k] + 1}" + (f"–{pre}{nums[k + 1] - 1}" if gaps[k] > 2 else ""))
        if ranges:
            ctx.add("SMP-002", "WARNING", g["table"].iloc[0], f"Prefix '{pre}': {missing} sample numbers missing inside the sequence (QC inserts counted as used): {', '.join(ranges[:15])}{' …' if len(ranges) > 15 else ''}.",
                    f"پیشوند «{pre}»: {missing} شمارهٔ نمونه در میان دنباله وجود ندارد (نمونه‌های کنترلی شمرده شده‌اند): {', '.join(ranges[:15])}.",
                    field="sample_id", value=missing)
        if blocks:
            ctx.add("SMP-002", "INFO", g["table"].iloc[0], f"Prefix '{pre}': {blocks} jumps of more than {p['max_gap_n']} numbers (separate ticket books or blocks).",
                    f"پیشوند «{pre}»: {blocks} جهش بیش از {p['max_gap_n']} شماره (دفترچه یا بلوک جداگانه).", field="sample_id", value=blocks)
    from_lab = s["lab"].fillna(False).astype(bool) if "lab" in s else pd.Series(False, index=s.index)
    o = s[~s["qc"].astype(bool) & ~from_lab & s["hole_id"].notna() & s["from_m"].notna()]
    for h, g in o.sort_values(["hole_id", "from_m"]).groupby("hole_id"):
        if len(g) < 3:
            continue
        d = np.diff(g["num"].to_numpy(float))
        up, down = (d > 0).sum(), (d < 0).sum()
        bad = min(up, down)
        if bad:
            k = int(np.where(d < 0)[0][0] if up >= down else np.where(d > 0)[0][0])
            r = g.iloc[k + 1]
            ctx.add("SMP-002", "WARNING", g["table"].iloc[0], f"{bad} sample numbers out of downhole order (first at {r['from_m']:g} m: {r['sample_id']} after {g['sample_id'].iloc[k]}): possible sample swap or mis-assigned depths.",
                    f"{bad} شمارهٔ نمونه خارج از ترتیب درون‌چاهی است (نخستین در عمق {r['from_m']:g} متر): احتمال جابه‌جایی نمونه یا عمق.",
                    hole_id=h, from_m=r["from_m"], field="sample_id", value=bad, src_row=int(r["src_row"]))
