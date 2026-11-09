"""Code dictionary files (v2 VAL-08): a table with columns `field, code[, description]`, CSV or XLSX."""
from __future__ import annotations

from ..core.normalise import header_key
from .readers import read_file

_FIELD = {"lith": "lith_code", "lithology": "lith_code", "lithcode": "lith_code", "rock": "lith_code", "سنگشناسی": "lith_code",
          "alt": "alt_type", "alteration": "alt_type", "alttype": "alt_type", "دگرسانی": "alt_type",
          "weathering": "weathering", "weath": "weathering", "oxidation": "weathering", "هوازدگی": "weathering",
          "drilltype": "drill_method", "drillmethod": "drill_method", "holetype": "drill_method", "method": "drill_method"}


def read_code_dictionary(path: str) -> dict[str, list[str]]:
    df = read_file(path)[0].df
    keys = {c: header_key(c) for c in df.columns}
    pick = lambda *cands: next((c for c, k in keys.items() if k in cands), None)
    c_field = pick("field", "table", "type", "category", "attribute", "فیلد")
    c_code = pick("code", "value", "codes", "کد")
    if c_field is None or c_code is None:
        raise ValueError("Code dictionary needs columns 'field' and 'code' (and optionally 'description').")
    out: dict[str, list[str]] = {}
    for f, c in zip(df[c_field].astype(str).str.strip(), df[c_code].astype(str).str.strip()):
        if not f or not c or c.lower() == "nan":
            continue
        out.setdefault(_FIELD.get(header_key(f), f), []).append(c)
    return out
