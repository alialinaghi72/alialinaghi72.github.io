#!/usr/bin/env python3
"""Run the GEOQAQC 1.1 analysis on sample_data and dump every scalar result.

The 1.1 program imports tkinter at module level and subclasses tk.Canvas, so a
stub tkinter is placed in sys.modules first; the analysis path never touches a
widget. The JSON written here is the reference that tests/test_regression_v11
compares GEOQAQC 2.0 against with every cleaning rule switched off.

    python tools/make_v11_baseline.py
"""

import importlib.util
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEGACY = os.path.join(HERE, "legacy", "GEOQAQC_v1_1.py")
DATA = os.path.join(ROOT, "sample_data")
OUT = os.path.join(ROOT, "tests", "data", "v11_baseline.json")


def _stub_tkinter():
    tk = types.ModuleType("tkinter")
    for name in ("Tk", "Toplevel", "Canvas", "Frame", "Label", "PanedWindow",
                 "Text", "StringVar", "BooleanVar"):
        setattr(tk, name, type(name, (), {}))
    tk.TclError = Exception
    for sub in ("ttk", "filedialog", "messagebox"):
        m = types.ModuleType(f"tkinter.{sub}")
        setattr(tk, sub, m)
        sys.modules[f"tkinter.{sub}"] = m
    sys.modules["tkinter"] = tk


def load_legacy():
    _stub_tkinter()
    spec = importlib.util.spec_from_file_location("geoqaqc_v11", LEGACY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def table(g, kind, fname, mapping, value_cols=None):
    h, r, d = g.sniff_and_read(os.path.join(DATA, fname))
    t = g.DataTable(kind, fname, os.path.join(DATA, fname), h, r, d)
    t.mapping = mapping
    if value_cols:
        t.value_cols = [(c, "numeric") for c in value_cols]
    if kind == "assay":
        i = h.index(mapping["type"])
        t.type_map = {row[i].strip(): g.classify_type(row[i]) for row in r}
    return t


def build_project(g):
    p = g.Project()
    p.assay = table(g, "assay", "assay.csv",
                    {"sampleid": "SAMPLE_ID", "type": "SAMPLE_TYPE",
                     "crmid": "CRM_ID", "parent": "PARENT_ID",
                     "batch": "BATCH", "order": "SEQ"},
                    ["Cu_pct", "Au_ppm"])
    p.crm = table(g, "crm", "crm_certificates.csv",
                  {"crmid": "CRM_ID", "element": "ELEMENT",
                   "certified": "CERTIFIED", "sd": "SD", "unit": "UNIT"})
    p.umpire = table(g, "umpire", "umpire_lab2.csv",
                     {"sampleid": "SAMPLE_ID", "lab": "LAB", "batch": "BATCH"},
                     ["Cu_pct", "Au_ppm"])
    return p


def flatten(obj, prefix, out):
    """Every number, string, bool and None reachable from obj, keyed by path.
    Sample objects (inside 'pairs') are skipped -- they are inputs, not results."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = "|".join(str(x) for x in k) if isinstance(k, tuple) else str(k)
            flatten(v, f"{prefix}/{key}" if prefix else key, out)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            flatten(v, f"{prefix}[{i}]", out)
    elif obj is None or isinstance(obj, (bool, int, float, str)):
        out[prefix] = obj


def main():
    g = load_legacy()
    p = build_project(g)
    F = g.FormulaBook(g.DEFAULT_FORMULAS)
    C = {k: dict(v) for k, v in g.DEFAULT_CRITERIA.items()}
    S = dict(g.DEFAULT_SETTINGS)
    R = g.run_analysis(p, F, C, S, log=lambda m: None)
    R = {k: v for k, v in R.items() if k != "pairs"}
    out = {}
    flatten(R, "", out)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=0, sort_keys=True)
    print(f"{len(out)} values written to {OUT}")


if __name__ == "__main__":
    main()
