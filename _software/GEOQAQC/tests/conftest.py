import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "sample_data")
TEST_DATA = os.path.join(ROOT, "tests", "data")


ASSAY_COLS = ["SAMPLE_ID", "SAMPLE_TYPE", "CRM_ID", "PARENT_ID", "BATCH", "SEQ"]
ASSAY_MAP = {"sampleid": "SAMPLE_ID", "type": "SAMPLE_TYPE", "crmid": "CRM_ID",
             "parent": "PARENT_ID", "batch": "BATCH", "order": "SEQ"}

# the three CRMs of the 1.1 sample data
CERTS = [("OREAS-501b", "Cu_pct", 0.283, 0.009, "%"),
         ("OREAS-501b", "Au_ppm", 0.312, 0.018, "ppm"),
         ("OREAS-504b", "Cu_pct", 1.052, 0.028, "%"),
         ("OREAS-504b", "Au_ppm", 0.905, 0.041, "ppm"),
         ("CDN-ME-1", "Cu_pct", 0.505, 0.015, "%"),
         ("CDN-ME-1", "Au_ppm", 1.48, 0.062, "ppm")]


def make_project(rows, certs=None, elements=("Cu_pct", "Au_ppm"),
                 settings=None):
    """A Project built in memory. rows: dicts keyed by ASSAY_COLS and element
    names (missing keys are empty cells; SEQ defaults to the row number).
    certs: (crm, element, certified, sd, unit) tuples."""
    from geoqaqc.model import DataTable, Project, build_samples
    from geoqaqc.protocol import DEFAULT_SETTINGS
    header = ASSAY_COLS + list(elements)
    data = []
    for i, r in enumerate(rows, start=1):
        r = dict(r)
        r.setdefault("SEQ", i)
        data.append([str(r.get(h, "")) for h in header])
    t = DataTable("assay", "A", "memory.csv", header, data, ",")
    t.mapping = dict(ASSAY_MAP)
    t.value_cols = [(e, "numeric") for e in elements]
    p = Project()
    p.assay = t
    if certs:
        ch = ["CRM_ID", "ELEMENT", "CERTIFIED", "SD", "UNIT"]
        cr = [[str(x) for x in c] for c in certs]
        ct = DataTable("crm", "C", "certs.csv", ch, cr, ",")
        ct.mapping = {"crmid": "CRM_ID", "element": "ELEMENT",
                      "certified": "CERTIFIED", "sd": "SD", "unit": "UNIT"}
        p.crm = ct
    S = dict(DEFAULT_SETTINGS)
    S.update(settings or {})
    build_samples(p, S, log=lambda m: None)
    return p, S


def crm_rows(code, cu, au, n=6, start=0, jitter=0.002):
    """n CRM rows reading close to (cu, au)."""
    out = []
    for i in range(n):
        d = (i % 3 - 1) * jitter
        out.append({"SAMPLE_ID": f"{code}-{start + i}", "SAMPLE_TYPE": "CRM",
                    "CRM_ID": code, "Cu_pct": f"{cu * (1 + d):.4f}",
                    "Au_ppm": f"{au * (1 + d):.4f}"})
    return out
