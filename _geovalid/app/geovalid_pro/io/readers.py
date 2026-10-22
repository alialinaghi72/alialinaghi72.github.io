"""Tabular readers (CSV/TXT any delimiter, XLSX/XLS multi-sheet). Everything is read as text,
so raw values (decimals, codes such as '<0.01') are preserved for the rules."""
from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

TEXT_EXT = {".csv", ".txt", ".tsv", ".dat", ".prn"}
EXCEL_EXT = {".xlsx", ".xlsm", ".xls"}


@dataclass
class RawTable:
    source: str           # file path
    sheet: str | None     # sheet name for workbooks
    df: pd.DataFrame      # all columns as text
    encoding: str = ""
    delimiter: str = ""
    sha256: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        stem = Path(self.source).stem
        return f"{stem}:{self.sheet}" if self.sheet else stem


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _decode(data: bytes) -> tuple[str, str]:
    for bom, enc in ((b"\xef\xbb\xbf", "utf-8-sig"), (b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16")):
        if data.startswith(bom):
            return data.decode(enc), enc
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data[:400000]).best()
        if best is not None and best.encoding:
            enc = best.encoding
            return data.decode(enc, errors="replace"), enc
    except Exception:  # pragma: no cover - detection is best effort
        pass
    return data.decode("cp1256", errors="replace"), "cp1256"


def _sniff_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:50])
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        counts = {d: sample.count(d) for d in (",", ";", "\t", "|")}
        return max(counts, key=counts.get)


def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cols, seen = [], {}
    for c in df.columns:
        name = str(c).strip().replace("﻿", "") or "unnamed"
        if name.lower().startswith("unnamed:"):
            name = "unnamed"
        k = seen.get(name, 0)
        seen[name] = k + 1
        cols.append(name if k == 0 else f"{name}_{k + 1}")
    df.columns = cols
    df = df.dropna(how="all")
    keep = [c for c in df.columns if not (c.startswith("unnamed") and df[c].isna().all())]
    return df[keep].reset_index(drop=True)


def read_file(path: str) -> list[RawTable]:
    """Read one file. Workbooks return one RawTable per non-empty sheet."""
    p = Path(path)
    ext = p.suffix.lower()
    digest = sha256_of(path)
    if ext in EXCEL_EXT:
        engine = "xlrd" if ext == ".xls" else "openpyxl"
        sheets = pd.read_excel(path, sheet_name=None, dtype=str, engine=engine)
        out = []
        for name, df in sheets.items():
            df = _tidy(df)
            if len(df.columns) >= 2 and len(df) > 0:
                out.append(RawTable(str(p), str(name), df, sha256=digest))
        return out
    data = p.read_bytes()
    text, enc = _decode(data)
    delim = "\t" if ext == ".tsv" else _sniff_delimiter(text)
    df = pd.read_csv(io.StringIO(text), sep=delim, dtype=str, keep_default_na=False,
                     na_values=[""], skipinitialspace=True, engine="python")
    return [RawTable(str(p), None, _tidy(df), encoding=enc, delimiter=delim, sha256=digest)]
