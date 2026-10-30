# -*- coding: utf-8 -*-
"""Load tables without the mapping dialog: the same guesses the dialog
pre-fills (column roles, element columns, sample-type codes), applied
automatically. Used by the self-test, the demo button and the tests."""

from __future__ import annotations

import os

from .core import classify_type
from .model import DataTable, Project, guess_role, looks_numeric, read_table

ROLES = {
    "assay": ["sampleid", "type", "crmid", "parent", "batch", "lab", "date",
              "order", "holeid", "drilltype", "from", "to"],
    "crm": ["crmid", "element", "certified", "sd", "unit", "method"],
    "pairs": ["sampleid", "dupid", "type"],
    "umpire": ["sampleid", "lab", "batch", "date"],
}


def auto_table(kind, path, name=None):
    header, rows, delim = read_table(path)
    if not header:
        raise ValueError(f"{os.path.basename(path)} has no readable rows.")
    t = DataTable(kind, name or os.path.splitext(os.path.basename(path))[0].upper(),
                  path, header, rows, delim)
    taken = []
    for role in ROLES[kind]:
        g = guess_role(header, role, taken)
        if g:
            t.mapping[role] = g
            taken.append(g)
    if kind in ("assay", "umpire"):
        mapped = set(t.mapping.values())
        t.value_cols = [(c, "numeric") for c in header
                        if c not in mapped and looks_numeric(t.col_values(c))]
    if kind == "assay" and t.mapping.get("type"):
        t.type_map = {v.strip(): classify_type(v)
                      for v in t.col_values(t.mapping["type"]) if v.strip()}
    return t


def load_project(assay, crm=None, umpire=None, pairs=None):
    p = Project()
    p.assay = auto_table("assay", assay)
    if crm:
        p.crm = auto_table("crm", crm)
    if umpire:
        p.umpire = auto_table("umpire", umpire)
    if pairs:
        p.pairs = auto_table("pairs", pairs)
    return p
