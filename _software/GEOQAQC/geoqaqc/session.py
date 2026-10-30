# -*- coding: utf-8 -*-
"""Save and restore a GEOQAQC session (.qaproj, JSON).

A session holds the paths and column mappings of the input files and the
whole protocol of the project -- formulas, criteria, settings, rules -- plus
the report details, so a project carries its agreed QA/QC protocol with it.
Sessions written by GEOQAQC 1.1 load unchanged (rules and report details then
take their defaults)."""

from __future__ import annotations

import dataclasses
import json
import os

from .model import DataTable, Project, read_table
from .protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS, DEFAULT_SETTINGS,
                       FormulaBook, RuleBook)

STATE_VERSION = "2.0"
_TABLES = ("assay", "crm", "pairs", "umpire")


def _meta_state(meta):
    if meta is None:
        return None
    if dataclasses.is_dataclass(meta):
        return dataclasses.asdict(meta)
    return dict(meta)


def state(project, F, C, S, RB, meta=None):
    out = {"version": STATE_VERSION, "settings": dict(S),
           "formulas": F.to_state(),
           "criteria": {k: list(v["cuts"]) for k, v in C.items()},
           "rules": RB.to_state(), "report_meta": _meta_state(meta)}
    for kind in _TABLES:
        t = getattr(project, kind)
        out[kind] = t.to_state() if t else None
    return out


def save(path, project, F, C, S, RB, meta=None):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state(project, F, C, S, RB, meta), fh, indent=2, ensure_ascii=False)
    return path


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            st = json.load(fh)
    except (OSError, ValueError) as ex:
        raise ValueError(f"Could not read the session: {ex}")
    if not isinstance(st, dict) or "assay" not in st:
        raise ValueError("This file is not a GEOQAQC session.")
    st.setdefault("version", "1.0")
    return st


def _rebuild(s, missing, log):
    if not s:
        return None
    path = s.get("path", "")
    if not path or not os.path.exists(path):
        missing.append(path)
        log(f"  ! missing file: {path}")
        return None
    h, r, d = read_table(path)
    t = DataTable(s["kind"], s.get("name", s["kind"].upper()), path, h, r, d)
    t.mapping = dict(s.get("mapping") or {})
    t.value_cols = [tuple(x) for x in s.get("value_cols", [])]
    t.type_map = dict(s.get("type_map") or {})
    t.dl = {k: float(v) for k, v in (s.get("dl") or {}).items()}
    return t


def restore(st, log=print):
    """Session state -> {'project', 'F', 'C', 'S', 'RB', 'meta', 'missing'}."""
    missing = []
    S = dict(DEFAULT_SETTINGS)
    S.update(st.get("settings") or {})
    F = FormulaBook(DEFAULT_FORMULAS)
    F.from_state(st.get("formulas"))
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    for key, cuts in (st.get("criteria") or {}).items():
        if key in C and len(cuts) == 5:
            C[key]["cuts"] = [float(c) for c in cuts]
    RB = RuleBook(st.get("rules"))
    p = Project()
    for kind in _TABLES:
        setattr(p, kind, _rebuild(st.get(kind), missing, log))
    return {"project": p, "F": F, "C": C, "S": S, "RB": RB,
            "meta": st.get("report_meta") or {}, "missing": missing}
