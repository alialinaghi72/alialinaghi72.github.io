# -*- coding: utf-8 -*-
"""Input files and the data model: tables, samples and the project.

The sample ID is the key of everything (see the 1.1 design note): a CRM or a
blank has no position, and a trench sample is not a drillhole interval, so
location is an optional attribute of a sample, never its identity.
"""

from __future__ import annotations

import csv
import re
import zipfile
import xml.etree.ElementTree as ET

from .core import (T_CRM, T_NORMAL, classify_type, dl_flag, fnum, is_blank,
                   to_latin_digits)


# ===========================================================================
#  Reading files
# ===========================================================================
def sniff_and_read(path, max_rows=None):
    """Read a delimited text file. Returns (header, rows, delimiter)."""
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        sample = fh.read(64 * 1024)
        fh.seek(0)
        delim = ","
        try:
            delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except Exception:
            counts = {d: sample.count(d) for d in ",;\t|"}
            delim = max(counts, key=counts.get) if max(counts.values()) else ","
        rdr = csv.reader(fh, delimiter=delim)
        try:
            header = next(rdr)
        except StopIteration:
            return [], [], delim
        header = [h.strip().lstrip("\ufeff") for h in header]
        seen, clean = {}, []
        for i, h in enumerate(header):
            h = h if h else f"COLUMN_{i + 1}"
            if h in seen:
                seen[h] += 1
                h = f"{h}_{seen[h]}"
            else:
                seen[h] = 0
            clean.append(h)
        rows = []
        n = len(clean)
        for r in rdr:
            if not any(str(x).strip() for x in r):
                continue
            if len(r) < n:
                r = list(r) + [""] * (n - len(r))
            elif len(r) > n:
                r = list(r[:n])
            rows.append(r)
            if max_rows and len(rows) >= max_rows:
                break
        return clean, rows, delim

# --- Excel workbooks (2.0) ----------------------------------------------------
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
       "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _col_index(ref):
    """'B12' -> 1 (zero-based column)."""
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def _cell_text(c, shared):
    t = c.get("t", "")
    if t == "inlineStr":
        return "".join(x.text or "" for x in c.iter(f"{{{_NS['m']}}}t"))
    v = c.find("m:v", _NS)
    if v is None or v.text is None:
        return ""
    if t == "s":
        return shared[int(v.text)]
    if t in ("str", "b", "e"):
        return v.text
    try:
        f = float(v.text)
    except ValueError:
        return v.text
    s = repr(f)
    return s[:-2] if s.endswith(".0") else s


def read_xlsx(path):
    """First worksheet of an .xlsx workbook -> (header, rows, 'xlsx').
    Values only (no formulas, no formatting), standard library only."""
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            shared = []
            if "xl/sharedStrings.xml" in names:
                root = ET.fromstring(z.read("xl/sharedStrings.xml"))
                for si in root.findall("m:si", _NS):
                    shared.append("".join(x.text or "" for x in
                                          si.iter(f"{{{_NS['m']}}}t")))
            sheet = "xl/worksheets/sheet1.xml"
            wb = ET.fromstring(z.read("xl/workbook.xml"))
            first = wb.find("m:sheets/m:sheet", _NS)
            if first is not None and "xl/_rels/workbook.xml.rels" in names:
                rid = first.get(f"{{{_NS['r']}}}id")
                rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
                for rel in rels.findall("pr:Relationship", _NS):
                    if rel.get("Id") == rid:
                        target = rel.get("Target").lstrip("/")
                        sheet = target if target.startswith("xl/") else "xl/" + target
            root = ET.fromstring(z.read(sheet))
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError) as ex:
        raise ValueError(f"Could not read the Excel workbook ({ex}). Open it in "
                         f"Excel and save it as CSV, then import the CSV.")
    table = []
    for row in root.iter(f"{{{_NS['m']}}}row"):
        cells = {}
        for c in row.findall("m:c", _NS):
            ref = c.get("r")
            i = _col_index(ref) if ref else len(cells)
            cells[i] = _cell_text(c, shared)
        if cells:
            out = [""] * (max(cells) + 1)
            for i, v in cells.items():
                out[i] = v
            table.append(out)
    if not table:
        return [], [], "xlsx"
    header = _clean_header(table[0])
    n = len(header)
    rows = []
    for r in table[1:]:
        if not any(str(x).strip() for x in r):
            continue
        r = (r + [""] * n)[:n]
        rows.append(r)
    return header, rows, "xlsx"


def _clean_header(header):
    header = [str(h).strip().lstrip("﻿") for h in header]
    seen, clean = {}, []
    for i, h in enumerate(header):
        h = h if h else f"COLUMN_{i + 1}"
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        clean.append(h)
    return clean


_COMMA_NUM = re.compile(r"^[<>]?-?\d+,\d+$")
_DOT_NUM = re.compile(r"^[<>]?-?\d*\.\d+$")


def uses_decimal_comma(rows, delim):
    """True when a non-comma-delimited table writes its decimals with commas
    (0,123) and never with dots -- the usual export of a European locale."""
    if delim == ",":
        return False
    commas = dots = 0
    for r in rows[:2000]:
        for v in r:
            s = to_latin_digits(v).strip()
            if _COMMA_NUM.match(s):
                commas += 1
            elif _DOT_NUM.match(s):
                dots += 1
    return commas > 0 and dots == 0


def read_table(path):
    """Any supported input file -> (header, rows, delimiter)."""
    if str(path).lower().endswith((".xlsx", ".xlsm")):
        return read_xlsx(path)
    if str(path).lower().endswith(".xls"):
        raise ValueError("The old .xls format is not supported. Open the file in "
                         "Excel and save it as CSV or .xlsx.")
    return sniff_and_read(path)



ROLE_HINTS = {
    "sampleid": ["sampleid", "sample_id", "sample id", "sample", "sampno", "sample_no",
                 "sampleno", "id", "labid", "lab_id", "sample_number", "samp"],
    "type": ["sampletype", "sample_type", "sample type", "type", "qc", "qctype",
             "qc_type", "class", "category", "sampclass"],
    "crmid": ["crmid", "crm_id", "crm", "standard", "std", "stdid", "std_id",
              "controlid", "reference", "refmat"],
    "parent": ["parent", "parentid", "parent_id", "original", "originalid",
               "orig_id", "origid", "source", "duplicateof", "twin_of", "master"],
    "batch": ["batch", "batchid", "batch_id", "job", "jobno", "job_no", "submission",
              "shipment", "dispatch", "workorder", "certificate", "report"],
    "lab": ["lab", "laboratory", "labname", "lab_name", "assayer", "provider"],
    "drilltype": ["drilltype", "drill_type", "drill type", "holetype", "hole_type",
                  "method", "drilling", "drill", "rig", "type_of_drilling",
                  "sampletype2", "media", "medium", "sample_medium"],
    "date": ["date", "assaydate", "assay_date", "reportdate", "analysisdate",
             "date_received", "datereported"],
    "order": ["order", "seq", "sequence", "position", "index", "runorder", "no", "row"],
    "element": ["element", "analyte", "el", "elem", "variable", "det"],
    "certified": ["certified", "cert", "certvalue", "cert_value", "expected", "value",
                  "mean", "recommended", "best_value"],
    "sd": ["sd", "stdev", "std_dev", "stddev", "sigma", "s", "1sd", "onesd",
           "standard_deviation", "uncertainty"],
    "unit": ["unit", "units", "uom"],
    "method": ["method", "technique", "digest", "analysismethod", "assay_method"],
    "dl": ["dl", "detectionlimit", "detection_limit", "lod", "mdl", "ldl"],
    # optional location roles
    "holeid": ["holeid", "hole_id", "hole", "bhid", "dhid", "drillhole", "trench",
               "trenchid", "site", "station", "line"],
    "from": ["from", "depth_from", "from_m", "fromdepth", "top", "start"],
    "to": ["to", "depth_to", "to_m", "todepth", "bottom", "base", "end"],
    "dupid": ["dupid", "dup_id", "duplicate", "duplicateid", "duplicate_id",
              "pair", "checkid", "check_id", "repeat_id"],
    "umplab": ["umpirelab", "umpire_lab", "checklab", "check_lab", "lab2",
               "second_lab", "external_lab", "referee"],
}


def guess_role(header, role, taken=()):
    hints = ROLE_HINTS.get(role, [])
    low = {h: h.strip().lower().replace(" ", "_") for h in header}
    for hint in hints:
        for h in header:
            if h in taken:
                continue
            if low[h] == hint:
                return h
    for hint in hints:
        for h in header:
            if h in taken:
                continue
            if hint in low[h]:
                return h
    return ""


def looks_numeric(values, thresh=0.6):
    vals = [v for v in values if not is_blank(v)]
    if not vals:
        return False
    ok = sum(1 for v in vals if fnum(v) is not None)
    return ok / len(vals) >= thresh


# ===========================================================================
#  Data model
# ===========================================================================
# ===========================================================================
#  Data model
# ===========================================================================
class DataTable:
    """One imported table."""

    def __init__(self, kind, name, path, header, rows, delim=","):
        self.kind = kind            # 'assay' | 'crm' | 'pairs'
        self.name = name
        self.path = path
        self.header = header
        self.rows = rows
        self.delim = delim
        self.mapping = {}
        self.value_cols = []        # assay only: [(element, 'numeric')]
        self.type_map = {}          # assay only: raw code -> SAMPLE_TYPES
        self.dl = {}                # element -> detection limit
        self.decimal_comma = uses_decimal_comma(rows, delim)

    def idx(self, role):
        col = self.mapping.get(role)
        if not col or col not in self.header:
            return None
        return self.header.index(col)

    def get(self, row, role):
        i = self.idx(role)
        return row[i] if i is not None and i < len(row) else None

    def col(self, row, name):
        if name not in self.header:
            return None
        i = self.header.index(name)
        return row[i] if i < len(row) else None

    def col_values(self, colname):
        if colname not in self.header:
            return []
        i = self.header.index(colname)
        return [r[i] if i < len(r) else "" for r in self.rows]

    def to_state(self):
        return {"kind": self.kind, "name": self.name, "path": self.path,
                "mapping": self.mapping, "value_cols": self.value_cols,
                "type_map": self.type_map, "dl": self.dl}


class Sample:
    __slots__ = ("sid", "stype", "raw_type", "crmid", "parent", "batch", "lab",
                 "date", "order", "vals", "flags", "row_n", "loc",
                 "hole", "drilltype",
                 # 2.0 -- cleaning state
                 "raw", "excl", "excl_all", "dropped", "crm_key", "swap_to")

    def __init__(self, sid, row_n):
        self.sid = sid
        self.row_n = row_n
        self.stype = T_NORMAL
        self.raw_type = ""
        self.crmid = ""
        self.parent = ""
        self.batch = ""
        self.lab = ""
        self.date = ""
        self.order = None
        self.vals = {}              # element -> float or None
        self.flags = {}             # element -> '<' / '>' / ''
        self.loc = ""
        self.hole = ""              # hole / trench / station -- optional
        self.drilltype = ""         # DD / RC / AC / channel ... -- optional
        self.raw = {}               # element -> the string in the file
        self.excl = {}              # element -> reason it is left out
        self.excl_all = ""          # reason the whole sample is left out
        self.dropped = False        # duplicate row / re-assay: not a sample
        self.crm_key = ""           # normalised CRM code
        self.swap_to = ""           # CRM this result probably really is

    def group(self, key):
        """Value of a grouping dimension, '' when the column was not mapped."""
        return getattr(self, key, "") if key else ""


class Project:
    def __init__(self):
        self.assay = None
        self.crm = None             # certificate table
        self.pairs = None           # explicit duplicate pair table
        self.umpire = None          # second-laboratory results
        self.samples = []
        self.elements = []
        self.certs = {}             # (crmid, element) -> {'cert':, 'sd':, 'unit':}
        self.results = {}           # analysis output
        self.analysed_at = None
        self.orphan_dups = []       # duplicates whose parent could not be found
        self.clean_log = None       # cleaning.CleanLog of the last run
        self.dropped_rows = []      # [(file row, reason)] rows that made no sample
        self.crm_labels = {}        # normalised CRM code -> display label
        self.excluded_pairs = set() # {(original id, duplicate id)} left out
        self.report_meta = None     # report.document.ReportMeta

    def tables(self):
        return [t for t in (self.assay, self.crm, self.pairs, self.umpire) if t]

    def clear_results(self):
        self.results = {}
        self.analysed_at = None


# ===========================================================================
#  Build the sample population from the imported tables
# ===========================================================================
def build_samples(project, S, log=print):
    t = project.assay
    if t is None:
        raise ValueError("An assay table must be imported before analysing.")

    elements = [c for c, k in t.value_cols if k == "numeric"]
    if not elements:
        raise ValueError("No element column has been flagged as numeric.")

    samples = []
    project.dropped_rows = []
    dc = getattr(t, "decimal_comma", False)
    for n, r in enumerate(t.rows, start=2):
        sid = str(t.get(r, "sampleid") or "").strip()
        if not sid:
            project.dropped_rows.append((n, "empty sample ID"))
            continue
        s = Sample(sid, n)
        raw = t.get(r, "type")
        s.raw_type = str(raw or "").strip()
        s.stype = t.type_map.get(s.raw_type) or classify_type(s.raw_type)
        s.crmid = str(t.get(r, "crmid") or "").strip()
        s.parent = str(t.get(r, "parent") or "").strip()
        s.batch = str(t.get(r, "batch") or "").strip()
        s.lab = str(t.get(r, "lab") or "").strip()
        s.date = str(t.get(r, "date") or "").strip()
        s.order = fnum(t.get(r, "order"))
        hid = str(t.get(r, "holeid") or "").strip()
        fr, to = t.get(r, "from"), t.get(r, "to")
        s.hole = hid
        s.drilltype = str(t.get(r, "drilltype") or "").strip()
        if hid:
            s.loc = f"{hid} {fr or ''}-{to or ''}".strip()
        # a CRM whose code lives in the type column rather than its own column
        if s.stype == T_CRM and not s.crmid and s.raw_type:
            s.crmid = s.raw_type
        s.crm_key = s.crmid.upper()
        for e in elements:
            raw_v = t.col(r, e)
            s.raw[e] = "" if raw_v is None else str(raw_v)
            s.vals[e] = fnum(raw_v, decimal_comma=dc)
            s.flags[e] = dl_flag(raw_v)
        samples.append(s)

    # sequence: explicit order column, else file order
    if all(s.order is None for s in samples):
        for i, s in enumerate(samples, start=1):
            s.order = float(i)

    project.samples = samples
    project.elements = elements

    # certificates
    certs = {}
    ct = project.crm
    if ct is not None:
        for r in ct.rows:
            cid = str(ct.get(r, "crmid") or "").strip()
            el = str(ct.get(r, "element") or "").strip()
            cdc = getattr(ct, "decimal_comma", False)
            cv = fnum(ct.get(r, "certified"), decimal_comma=cdc)
            sd = fnum(ct.get(r, "sd"), decimal_comma=cdc)
            if not cid or not el or cv is None:
                continue
            certs[(cid.upper(), el.upper())] = {
                "cert": cv, "sd": sd,
                "unit": str(ct.get(r, "unit") or "").strip(),
                "method": str(ct.get(r, "method") or "").strip()}
    project.certs = certs

    counts = {}
    for s in samples:
        counts[s.stype] = counts.get(s.stype, 0) + 1
    log(f"{len(samples)} samples, {len(elements)} element(s). "
        + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if certs:
        log(f"{len(certs)} certificate entries for "
            f"{len({k[0] for k in certs})} CRM code(s).")
    return samples


def detection_limit(project, element, S):
    """Detection limit for an element: the declared value if the user gave one,
    otherwise inferred from the largest '<' value, otherwise the smallest
    positive result in the dataset. A '<' of zero (a laboratory writing below
    detection as 0) says nothing about the limit and is ignored."""
    t = project.assay
    if t is not None and t.dl.get(element) is not None:
        return t.dl[element]
    below = [s.vals[element] for s in project.samples
             if s.flags.get(element) == "<" and usable(s, element)
             and s.vals[element] > 0]
    if below:
        return max(below)
    pos = [s.vals[element] for s in project.samples
           if usable(s, element) and s.vals[element] > 0]
    return min(pos) if pos else None


def usable(s, el):
    """True when sample s carries a result for el that may enter statistics."""
    return (not s.dropped and not s.excl_all and el not in s.excl
            and s.vals.get(el) is not None)


def pairable(s, el, RB):
    """usable, and not an over-range ('>') value when C08 is on: a censored
    value says nothing about the precision of a pair."""
    return usable(s, el) and not (RB["clean_C08"] and s.flags.get(el) == ">")
