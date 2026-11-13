# -*- coding: utf-8 -*-
"""Per-element configuration: the analytical method of a column, the QC
reference detection limit, the upper limit of the method, and the triggers
and actions of the exclusion review (R1, R11, R14, R24).

A profile is looked up by chemical symbol, so it follows the element from one
batch file to the next whatever the column is called (Cu_PPm, Cu_pct, ...).
Unset values fall back to the defaults below, which hold for every element
unless the element has its own entry.
"""

from __future__ import annotations

import copy
import re

from .core import T_CDUP, T_FDUP, T_PDUP, element_symbol, unit_factor

# ---- analytical methods ---------------------------------------------------------
# families a method string normalises to; anything else keeps its own name
METHOD_FAMILIES = {
    "FA": ["FA", "FIRE", "FIREASSAY", "FAA", "FAAAS", "FA50", "FA30", "FAAA"],
    "AR": ["AR", "AQUAREGIA", "AQUA", "ARICP", "ARAAS"],
    "TOTAL": ["TOTAL", "4AD", "4A", "4ACID", "FOURACID", "FOURACIDDIGEST", "MA",
              "MULTIACID", "NEARTOTAL", "4ADICP", "ICP4A"],
    "SOL": ["SOL", "SOLUBLE", "ACIDSOLUBLE", "SEQ", "SEQACID", "SEQUENTIAL",
            "H2SO4", "SULPHURIC", "SULFURIC", "ASCU", "CUSOL"],
    "OREGRADE": ["OREGRADE", "OG", "ORE", "OG4A", "OGICP"],
    "GRAV": ["GRAV", "GRAVIMETRIC", "FAGRAV", "FAG"],
}
METHOD_LABEL = {"FA": "fire assay", "AR": "aqua regia", "TOTAL": "four-acid (total)",
                "SOL": "acid-soluble", "OREGRADE": "ore-grade", "GRAV": "gravimetric"}
METHOD_CHOICES = ["FA", "AR", "TOTAL", "SOL", "OREGRADE", "GRAV"]
_LOOKUP = {a: fam for fam, al in METHOD_FAMILIES.items() for a in al}

# the method an element name without a suffix stands for
PRIMARY_METHOD = {"Au": "FA", "Pt": "FA", "Pd": "FA"}
DEFAULT_PRIMARY = "TOTAL"


def norm_method(m):
    """'Fire Assay' -> 'FA', '4AD' -> 'TOTAL', '' -> ''."""
    key = re.sub(r"[^A-Z0-9]", "", str(m or "").upper())
    if not key:
        return ""
    return _LOOKUP.get(key, key)


def primary_method(symbol):
    return PRIMARY_METHOD.get(symbol, DEFAULT_PRIMARY)


_SUFFIX = re.compile(r"^([A-Za-z]{1,2})(?:[_\-\s]?(.*))?$")


def parse_cert_element(name, method=""):
    """Element name of a certificate row -> (symbol, method family).
    'Au' -> ('Au', 'FA'); 'Au_AR' -> ('Au', 'AR'); 'CuSol' / 'Cu_Sol' ->
    ('Cu', 'SOL'); 'Cu_pct' -> ('Cu', 'TOTAL'). An explicit METHOD column
    wins over the name."""
    s = str(name or "").strip()
    sym = element_symbol(s)
    rest = s[len(sym):] if s.lower().startswith(sym.lower()) else ""
    rest = re.sub(r"^[_\-\s]+", "", rest)
    from_name = ""
    for tok in re.split(r"[_\-\s\(\)]+", rest):
        if not tok:
            continue
        fam = norm_method(tok)
        if fam in METHOD_FAMILIES:
            from_name = fam
            break
    m = norm_method(method) or from_name or primary_method(sym)
    return sym, m


# ---- profiles ---------------------------------------------------------------------
DUP_CLASSES = (T_FDUP, T_CDUP, T_PDUP)
ACTIONS = ("ask", "exclude", "keep")

DEFAULT_PROFILE = {
    "qc_dl": None, "qc_dl_unit": "",          # QC reference DL (R11); None: lab DL
    "upper": None, "upper_unit": "",          # upper limit of the routine method
    "low_kdl": {T_FDUP: None, T_CDUP: None, T_PDUP: None},   # None: rule default
    "low_action": "exclude",
    "outlier_hard": {T_FDUP: 67.0, T_CDUP: 67.0, T_PDUP: 67.0},
    "outlier_action": "ask",
    "outlier_preselect": "keep",
    "single_vote": False,                     # may vote alone in C16 (R5)
}
_LOW_NUGGET = ("Cu", "Mo", "Pb", "Zn", "Fe", "S")
ELEMENT_DEFAULTS = {s: {"outlier_hard": {T_FDUP: 67.0, T_CDUP: 50.0, T_PDUP: 50.0},
                        "outlier_preselect": "exclude", "single_vote": True}
                    for s in _LOW_NUGGET}
ELEMENT_DEFAULTS["Au"] = {"outlier_preselect": "keep", "single_vote": False}


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


class ElementBook:
    """Profiles by chemical symbol, plus the analytical method of each assay
    column. Only values the user changed are stored."""

    def __init__(self, state=None):
        self.overrides = {}          # symbol -> partial profile
        self.column_methods = {}     # column -> method family
        if state:
            self.from_state(state)

    # -- lookup -----------------------------------------------------------------
    def profile(self, element):
        sym = element_symbol(element)
        p = _merge(DEFAULT_PROFILE, ELEMENT_DEFAULTS.get(sym))
        return _merge(p, self.overrides.get(sym))

    def method(self, column):
        return norm_method(self.column_methods.get(column)) or \
            primary_method(element_symbol(column))

    def qc_dl(self, column, unit):
        """QC reference DL in the column's unit, or None."""
        p = self.profile(column)
        if p["qc_dl"] is None:
            return None
        f = unit_factor(p["qc_dl_unit"], unit) if p["qc_dl_unit"] and unit else 1
        return p["qc_dl"] * (f if f is not None else 1)

    def upper(self, column, unit):
        p = self.profile(column)
        if p["upper"] is None:
            return None
        f = unit_factor(p["upper_unit"], unit) if p["upper_unit"] and unit else 1
        return p["upper"] * (f if f is not None else 1)

    # -- editing ----------------------------------------------------------------
    def set(self, element, key, value):
        if key not in DEFAULT_PROFILE:
            raise KeyError(key)
        if key.endswith("_action") or key == "outlier_preselect":
            allowed = ACTIONS if key.endswith("_action") else ("exclude", "keep")
            if value not in allowed:
                raise ValueError(f"{key}: choose one of {', '.join(allowed)}")
        sym = element_symbol(element)
        cur = self.overrides.setdefault(sym, {})
        if isinstance(DEFAULT_PROFILE[key], dict):
            cur.setdefault(key, {}).update(value)
        else:
            cur[key] = value

    def set_method(self, column, method):
        m = norm_method(method)
        if m:
            self.column_methods[column] = m
        else:
            self.column_methods.pop(column, None)

    def reset(self):
        self.overrides, self.column_methods = {}, {}

    def to_state(self):
        return {"overrides": copy.deepcopy(self.overrides),
                "column_methods": dict(self.column_methods)}

    def from_state(self, st):
        self.overrides = copy.deepcopy((st or {}).get("overrides") or {})
        self.column_methods = dict((st or {}).get("column_methods") or {})
