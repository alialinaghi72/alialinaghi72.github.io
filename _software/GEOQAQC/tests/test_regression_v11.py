"""GEOQAQC 2.0 against the numbers GEOQAQC 1.1 produced on sample_data."""

import json
import math
import os
import sys

import pytest

from conftest import DATA, ROOT, TEST_DATA
from geoqaqc.analysis import run_analysis
from geoqaqc.core import classify_type
from geoqaqc.model import DataTable, Project, read_table
from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                              DEFAULT_SETTINGS, RULES, FormulaBook, RuleBook)

sys.path.insert(0, os.path.join(ROOT, "tools"))
from make_v11_baseline import flatten  # noqa: E402


def _table(kind, fname, mapping, value_cols=None):
    path = os.path.join(DATA, fname)
    h, r, d = read_table(path)
    t = DataTable(kind, fname, path, h, r, d)
    t.mapping = mapping
    if value_cols:
        t.value_cols = [(c, "numeric") for c in value_cols]
    if kind == "assay":
        i = h.index(mapping["type"])
        t.type_map = {row[i].strip(): classify_type(row[i]) for row in r}
    return t


def sample_project():
    p = Project()
    p.assay = _table("assay", "assay.csv",
                     {"sampleid": "SAMPLE_ID", "type": "SAMPLE_TYPE",
                      "crmid": "CRM_ID", "parent": "PARENT_ID",
                      "batch": "BATCH", "order": "SEQ"}, ["Cu_pct", "Au_ppm"])
    p.crm = _table("crm", "crm_certificates.csv",
                   {"crmid": "CRM_ID", "element": "ELEMENT",
                    "certified": "CERTIFIED", "sd": "SD", "unit": "UNIT"})
    p.umpire = _table("umpire", "umpire_lab2.csv",
                      {"sampleid": "SAMPLE_ID", "lab": "LAB", "batch": "BATCH"},
                      ["Cu_pct", "Au_ppm"])
    return p


def analyse(rb):
    p = sample_project()
    R = run_analysis(p, FormulaBook(DEFAULT_FORMULAS),
                     {k: dict(v) for k, v in DEFAULT_CRITERIA.items()},
                     dict(DEFAULT_SETTINGS), rb, log=lambda m: None)
    return p, R


def _v2_key(k):
    """Translate a 1.1 result path into the 2.0 path."""
    if k.startswith("blank/"):
        return "blank/BLANK|" + k[len("blank/"):]
    return k


def _flat(R):
    out = {}
    flatten({k: v for k, v in R.items() if k not in ("pairs", "clean_log")},
            "", out)
    # CRM keys and labels: 1.1 upper-cased the code, 2.0 keeps the
    # certificate's spelling -- compare case-insensitively
    return {k.upper(): v for k, v in out.items()}


def _same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None:
            return a is b
        if math.isnan(a) and math.isnan(b):
            return True
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
    if isinstance(a, str) and isinstance(b, str):
        return a.upper() == b.upper()
    return a == b


def test_v11_parity_cleaning_off():
    base = json.load(open(os.path.join(TEST_DATA, "v11_baseline.json"),
                          encoding="utf-8"))
    rb = RuleBook()
    for k in RULES:
        if k.startswith("clean_"):
            rb.set(k, False)
    _, R = analyse(rb)
    got = _flat(R)
    missing, diff = [], []
    for k, v in base.items():
        k2 = _v2_key(k).upper()
        if k2 not in got:
            missing.append(k)
        elif not _same(v, got[k2]):
            diff.append((k, v, got[k2]))
    assert not missing, missing[:10]
    assert not diff, diff[:10]


def test_v11_cleaning_on_runs():
    p, R = analyse(RuleBook())
    assert R["overall"]
    assert R["clean_log"] is p.clean_log
    # every exclusion made by the cleaning is logged
    excluded = {s.sid for s in p.samples if s.dropped or s.excl_all or s.excl}
    assert excluded <= p.clean_log.excluded_samples()


@pytest.mark.parametrize("bt", ["BLANK"])
def test_blank_keyed_by_type(bt):
    _, R = analyse(RuleBook())
    assert all(k[0] == bt for k in R["blank"])
