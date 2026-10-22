"""Project inputs and the canonical tables built from them (02 §4). Sources are never modified."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..analysis.assay import infer_unit, parse_assay
from ..io.mapping import FIELDS, INTERVAL_KINDS, TableMapping
from ..io.readers import RawTable
from .issues import IssueLog
from .normalise import clean_text, parse_dates, parse_numbers

NUMERIC = {"x", "y", "z", "eoh_m", "azimuth", "dip", "depth_m", "from_m", "to_m", "cr_pct", "rqd_pct",
           "run_length_m", "recovered_length_m", "rqd_length_m", "density"}
DATES = {"date_started", "date_completed"}
DEPTH_FIELDS = {"eoh_m", "depth_m", "from_m", "to_m", "run_length_m", "recovered_length_m", "rqd_length_m"}
KEY_NUMERIC = {"x", "y", "z", "eoh_m", "depth_m", "from_m", "to_m", "dip", "azimuth"}


@dataclass
class TableInput:
    raw: RawTable
    kind: str
    mapping: TableMapping
    enabled: bool = True
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = self.raw.name


@dataclass
class Analyte:
    column: str
    analyte: str
    unit: str
    unit_declared: bool
    unit_evidence: str
    qualifier: str
    partial: bool
    parsed: pd.DataFrame

    @property
    def label(self) -> str:
        q = f" {self.qualifier}" if self.qualifier else ""
        return f"{self.analyte}{q} ({self.unit})"


@dataclass
class Canon:
    name: str
    kind: str
    source: str
    df: pd.DataFrame
    analytes: list[Analyte] = field(default_factory=list)
    attrs: list[str] = field(default_factory=list)
    raw: pd.DataFrame | None = None

    @property
    def is_interval(self) -> bool:
        return self.kind in INTERVAL_KINDS or (self.kind == "density" and "from_m" in self.df and self.df["from_m"].notna().any())


def build_canonical(inp: TableInput, log: IssueLog) -> Canon:
    raw = inp.raw.df
    m = inp.mapping
    df = pd.DataFrame(index=raw.index)
    df["src_row"] = raw.index.to_numpy() + 2
    req, _ = FIELDS[inp.kind]
    for f in req:
        if not m.fields.get(f):
            log.add("IMP-010", "CRITICAL", inp.name,
                    f"Required field '{f}' is not mapped for a {inp.kind} table; dependent rules cannot run.",
                    f"فیلد الزامی «{f}» برای جدول {inp.kind} نگاشت نشده است؛ قواعد وابسته اجرا نمی‌شوند.",
                    field=f, suggested_fix="Map a source column to this field in the mapping dialog.")
    norm_counts = 0
    for f, col in m.fields.items():
        if not col:
            continue
        src = raw[col]
        if f in NUMERIC:
            val, dec, bad, note = parse_numbers(src)
            if f in DEPTH_FIELDS and m.depth_unit == "ft":
                val = val * 0.3048
            df[f] = val
            if f in ("x", "y", "z"):
                df[f + "_dec"] = dec
                df[f + "_raw"] = clean_text(src)
            if note:
                log.add("IMP-004", "INFO", inp.name, f"Column '{col}' ({f}): {note}.", f"ستون «{col}» ({f}): {note}.",
                        field=f)
            nbad = int(bad.sum())
            if nbad:
                sev = "ERROR" if f in KEY_NUMERIC else "WARNING"
                rows = df.loc[bad, "src_row"]
                if nbad <= 50:
                    for i in rows.index:
                        log.add("IMP-005", sev, inp.name,
                                f"Value '{src[i]}' in '{col}' is not a number; stored as missing (raw kept).",
                                f"مقدار «{src[i]}» در ستون «{col}» عدد نیست؛ تهی در نظر گرفته شد (مقدار خام حفظ شده است).",
                                field=f, value=src[i], src_row=int(df.at[i, "src_row"]))
                else:
                    log.add("IMP-005", sev, inp.name, f"{nbad} values in '{col}' are not numbers (first at row {int(rows.iloc[0])}).",
                            f"{nbad} مقدار در ستون «{col}» عدد نیستند (نخستین در ردیف {int(rows.iloc[0])}).",
                            field=f, value=nbad)
        elif f in DATES:
            dts, n_jal = parse_dates(src)
            df[f] = dts
            if n_jal:
                log.add("IMP-014", "INFO", inp.name, f"{n_jal} Jalali (Solar Hijri) dates in '{col}' converted to Gregorian.",
                        f"{n_jal} تاریخ شمسی در ستون «{col}» به میلادی تبدیل شد.", field=f, value=n_jal)
        else:
            txt = clean_text(src)
            changed = int(((src.astype("string").fillna("") != txt.fillna("")) & src.notna()).sum())
            norm_counts += changed
            df[f] = txt
    if norm_counts:
        log.add("IMP-003", "INFO", inp.name, f"{norm_counts} text values normalised (Persian/Arabic digits, letters, invisible characters, spaces).",
                f"{norm_counts} مقدار متنی یکسان‌سازی شد (ارقام و حروف فارسی/عربی، نویسه‌های نامرئی، فاصله‌ها).", value=norm_counts)
    for f in list(m.fields):
        if f not in df:
            df[f] = np.nan if f in NUMERIC else pd.NA
    canon = Canon(inp.name, inp.kind, inp.raw.source, df, raw=raw)
    used = {c for c in m.fields.values() if c}
    for a in m.analytes:
        parsed = parse_assay(raw[a.column])
        if a.unit:
            unit, declared, ev = a.unit, True, "declared in header"
        else:
            unit, ev = infer_unit(a.analyte, parsed)
            declared = False
        canon.analytes.append(Analyte(a.column, a.analyte, unit, declared, ev, a.qualifier, a.partial, parsed))
        used.add(a.column)
    for c in raw.columns:
        if c not in used:
            key = "attr:" + c
            df[key] = clean_text(raw[c])
            canon.attrs.append(key)
    if "from_m" in df and "to_m" in df:
        df["length_m"] = df["to_m"] - df["from_m"]
    return canon
