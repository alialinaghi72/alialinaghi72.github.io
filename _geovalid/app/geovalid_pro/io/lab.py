"""Laboratory / QA-QC files in the GEOQAQC format (v2 brief R1; format and confirmed assumptions: docs/QAQC_FORMAT.md).

Three readers, all on top of GEOVALID's generic table reader (any delimiter or encoding, XLSX/XLS):
  read_lab_file      the laboratory / QA-QC file (SAMPLE_ID, SAMPLE_TYPE, CRM_ID, PARENT_ID, BATCH, SEQ, … elements)
  read_umpire_file   the separate check / umpire file (SAMPLE_ID, LAB, BATCH, elements)
  read_crm_certificates  CRM_ID, ELEMENT, CERTIFIED, SD[, UNIT]; ELEMENT is a column name (Cu_pct) or a symbol (Cu)
Values are parsed but never converted or substituted; unknown sample-type codes are kept as UNKNOWN and reported.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from ..analysis.assay import TO_PPM, infer_unit, parse_assay
from ..core.normalise import clean_text, header_key, parse_numbers
from ..core.project import Analyte, Canon
from .mapping import parse_analyte_header, propose_mapping
from .readers import read_file

# Confirmed by the owner, 2026-11-09 (QAQC_FORMAT.md §3). Keys are upper-case with spaces, `_` and `-` removed.
SAMPLE_TYPES = {
    "SAMPLE": "ORIGINAL", "STD": "CRM", "CRM": "CRM", "BLANK": "BLANK", "CBLK": "BLANK", "PBLK": "BLANK",
    "FD": "FIELD_DUP", "FIELDDUP": "FIELD_DUP", "CD": "COARSE_DUP", "COARSEDUP": "COARSE_DUP",
    "PD": "PULP_DUP", "PULPDUP": "PULP_DUP",
}
SUBTYPE = {"CBLK": "COARSE_BLANK", "PBLK": "PULP_BLANK"}
NOT_ANALYSED_CODES = {"IS", "LNR"}            # insufficient sample; listed not received (confirmed)


def _key(v) -> str:
    return re.sub(r"[\s_\-]+", "", str(v).upper()) if isinstance(v, str) else ""


def sample_type_map(params: dict | None = None) -> dict:
    m = dict(SAMPLE_TYPES)
    for k, v in ((params or {}).get("lab_sample_types") or {}).items():
        m[_key(k)] = str(v).upper()
    return m


def _canon(raw, role: str, params: dict | None) -> Canon:
    df = raw.df
    m = propose_mapping(df, "assay")
    out = pd.DataFrame(index=df.index)
    out["src_row"] = df.index.to_numpy() + 2
    for f in ("sample_id", "sample_type", "crm_id", "parent_id", "batch", "lab", "hole_id"):
        c = m.fields.get(f)
        out[f] = clean_text(df[c]) if c else pd.NA
    for f in ("from_m", "to_m"):
        c = m.fields.get(f)
        out[f] = parse_numbers(df[c])[0] if c else np.nan
    keys = {c: header_key(c) for c in df.columns}
    seq = next((c for c, k in keys.items() if k in ("seq", "sequence", "order", "insertorder")), None)
    out["seq"] = parse_numbers(df[seq])[0] if seq else np.arange(len(df), dtype=float) + 1
    if role == "umpire":
        out["sample_type"] = out["sample_type"].fillna("UMPIRE")
        out["qc_class"] = "UMPIRE"
    else:
        tmap = sample_type_map(params)
        k = out["sample_type"].map(_key)
        out["qc_class"] = k.map(tmap).fillna("UNKNOWN")
        out["qc_subclass"] = k.map(SUBTYPE)
    canon = Canon(raw.name, role, raw.source, out, raw=df, fieldmap={f: c for f, c in m.fields.items() if c})
    for a in m.analytes:
        parsed = parse_assay(df[a.column])
        if a.unit:
            unit, declared, ev = a.unit, True, "declared in header"
        else:
            unit, ev = infer_unit(a.analyte, parsed)
            declared = False
        code = parsed["code"].astype("string").str.upper().str.strip()
        parsed["not_analysed"] = (parsed["flag"] == "NA") | code.isin(NOT_ANALYSED_CODES).fillna(False)
        canon.analytes.append(Analyte(a.column, a.analyte, unit, declared, ev, a.qualifier, a.partial, parsed))
    canon.sha256 = raw.sha256
    return canon


def read_lab_file(path: str, params: dict | None = None) -> Canon:
    """GEOQAQC laboratory / QA-QC file → Canon (kind "lab") with qc_class per row and parsed analytes."""
    raws = read_file(path)
    raw = max(raws, key=lambda r: len(r.df))
    c = _canon(raw, "lab", params)
    if c.df["sample_id"].isna().all():
        raise ValueError(f"{raw.name}: no SAMPLE_ID column found")
    if not c.analytes:
        raise ValueError(f"{raw.name}: no element columns (e.g. Cu_pct, Au_ppm) found")
    return c


def read_umpire_file(path: str, params: dict | None = None) -> Canon:
    raws = read_file(path)
    raw = max(raws, key=lambda r: len(r.df))
    c = _canon(raw, "umpire", params)
    if c.df["sample_id"].isna().all() or not c.analytes:
        raise ValueError(f"{raw.name}: a check / umpire file needs SAMPLE_ID and element columns")
    return c


def read_crm_certificates(path: str) -> pd.DataFrame:
    """crm_id, analyte, certified, sd, unit, element (as written). ELEMENT may be a column name (Cu_pct → Cu, %) or a
    symbol (Cu) with a UNIT column. Values are as declared; conversion to an assay column's unit happens at use."""
    df = read_file(path)[0].df
    keys = {c: header_key(c) for c in df.columns}

    def pick(*cands):
        for c, k in keys.items():
            if any(k == x for x in cands):
                return c
        for c, k in keys.items():
            if any(k.startswith(x) for x in cands):
                return c
        return None
    c_id = pick("crmid", "crm", "standard", "std", "stdid", "standardid")
    c_el = pick("element", "analyte", "el")
    c_v = pick("certified", "certifiedvalue", "expected", "value", "mean", "cert")
    c_sd = pick("sd", "1sd", "sd1", "stdev", "std1", "stddev")
    c_u = pick("unit", "units", "uom")
    if None in (c_id, c_el, c_v, c_sd):
        raise ValueError("CRM file needs columns: CRM_ID, ELEMENT, CERTIFIED, SD (and optionally UNIT)")
    rows = []
    for _, r in df.iterrows():
        el = str(r[c_el]).strip()
        head = parse_analyte_header(el)
        analyte = head.analyte if head else el
        unit_hdr = head.unit if head else None
        unit = str(r[c_u]).strip() if c_u and pd.notna(r[c_u]) and str(r[c_u]).strip() else unit_hdr
        unit = {"pct": "%", "percent": "%", "g/t": "g/t", "gpt": "g/t"}.get(str(unit).lower(), unit) if unit else None
        rows.append({"crm_id": str(r[c_id]).strip(), "analyte": analyte, "element": el, "unit": unit,
                     "certified": parse_numbers(pd.Series([r[c_v]]))[0].iloc[0], "sd": parse_numbers(pd.Series([r[c_sd]]))[0].iloc[0]})
    out = pd.DataFrame(rows).dropna(subset=["certified", "sd"])
    return out


def convert(value: float, from_unit: str | None, to_unit: str | None) -> float:
    """Declared unit conversion (ppb, ppm, g/t, %, oz/t); unknown or equal units return the value unchanged."""
    if not from_unit or not to_unit or from_unit == to_unit or from_unit not in TO_PPM or to_unit not in TO_PPM:
        return value
    return value * TO_PPM[from_unit] / TO_PPM[to_unit]


def counts_by_type(c: Canon) -> dict:
    """Rows per SAMPLE_TYPE class (subclasses for coarse / pulp blanks), for the R1 acceptance check."""
    cls = c.df["qc_class"].where(c.df.get("qc_subclass").isna(), c.df.get("qc_subclass")) if "qc_subclass" in c.df else c.df["qc_class"]
    return {k: int(v) for k, v in cls.value_counts().items()}
