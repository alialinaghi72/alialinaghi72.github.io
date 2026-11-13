# -*- coding: utf-8 -*-
"""Project mode (R20): several batch files analysed as one project.

* merge_assay_files: the batch files become one assay table. Columns are
  matched by name (case and spaces ignored); a file without a batch column
  gets its file name as the batch; when the analytical order restarts from
  file to file a PROJECT_SEQ column keeps the files in the order given. The
  original values are never changed: the new columns are added beside them.
* Duplicates pair across batches (a duplicate in batch 12 finds its parent
  in batch 11) because pairing runs on the merged table; parents that are
  still missing get suggestions (normalised ID, edit distance <= 2) in
  orphan_duplicates.csv -- suggested only, never applied.
* split_by_batch: one project per batch, for the per-batch reports.
* run_project: the combined report, optionally one report per batch, and
  the batch x element acceptance matrix.
"""

from __future__ import annotations

import copy
import os
import re

from .core import fnum
from .model import DataTable, Project, guess_role, read_table

SOURCE_COL = "SOURCE_FILE"
BATCH_COL = "BATCH"
SEQ_COL = "PROJECT_SEQ"


def _key(h):
    return re.sub(r"[\s_\-]+", "", str(h or "").strip().lower())


def merge_assay_files(paths, log=print):
    """Batch files -> one DataTable (not yet mapped)."""
    if not paths:
        raise ValueError("No batch file given.")
    header, keys = [], {}
    parts = []
    for path in paths:
        h, rows, delim = read_table(path)
        if not h:
            raise ValueError(f"{os.path.basename(path)} has no readable rows.")
        for c in h:
            k = _key(c)
            if k not in keys:
                keys[k] = c
                header.append(c)
        parts.append((path, h, rows, delim))
    batch_col = guess_role(header, "batch") or None
    order_col = guess_role(header, "order") or None
    add_batch = batch_col is None
    out_header = list(header) + [SOURCE_COL] + ([BATCH_COL] if add_batch else [])
    # does the analytical order restart from file to file?
    spans, need_seq = [], False
    for path, h, rows, _ in parts:
        if order_col is None or _key(order_col) not in {_key(c) for c in h}:
            need_seq = True
            continue
        j = [_key(c) for c in h].index(_key(order_col))
        v = [fnum(r[j]) for r in rows if j < len(r)]
        v = [x for x in v if x is not None]
        if not v:
            need_seq = True
            continue
        lo, hi = min(v), max(v)
        if any(not (hi < a or lo > b) for a, b in spans):
            need_seq = True
        spans.append((lo, hi))
    if need_seq and len(parts) > 1:
        out_header.append(SEQ_COL)
    else:
        need_seq = False
    rows_out, seq, n_by_file = [], 0, []
    for path, h, rows, _ in parts:
        hk = [_key(c) for c in h]
        stem = os.path.splitext(os.path.basename(path))[0]
        oj = hk.index(_key(order_col)) if order_col and _key(order_col) in hk else None
        ordered = list(rows)
        if oj is not None:
            ordered.sort(key=lambda r: (fnum(r[oj]) if oj < len(r) and fnum(r[oj]) is not None
                                        else float("inf")))
        for r in ordered:
            row = []
            for c in header:
                k = _key(c)
                row.append(r[hk.index(k)] if k in hk and hk.index(k) < len(r) else "")
            row.append(os.path.basename(path))
            if add_batch:
                row.append(stem)
            if need_seq:
                seq += 1
                row.append(str(seq))
            rows_out.append(row)
        n_by_file.append((os.path.basename(path), len(rows)))
    t = DataTable("assay", "PROJECT", ";".join(paths), out_header, rows_out,
                  parts[0][3])
    for name, n in n_by_file:
        log(f"  {name}: {n} row(s)")
    if add_batch:
        log("  No batch column: each file is one batch, named after the file.")
    if need_seq:
        log(f"  The analytical order restarts between files: {SEQ_COL} keeps the "
            f"files in the order given (original order column unchanged).")
    return t


def load_batches(paths, crm=None, umpire=None, pairs=None, log=print):
    """load_project for several batch files."""
    from .loader import auto_table, map_table
    p = Project()
    t = merge_assay_files(paths, log=log)
    map_table(t)
    if SEQ_COL in t.header:
        t.mapping["order"] = SEQ_COL
    if BATCH_COL in t.header and SOURCE_COL in t.header and not t.mapping.get("batch"):
        t.mapping["batch"] = BATCH_COL
    extra = {SOURCE_COL, SEQ_COL, BATCH_COL}
    t.value_cols = [(c, k) for c, k in t.value_cols if c not in extra]
    p.assay = t
    if crm:
        p.crm = auto_table("crm", crm)
    if umpire:
        p.umpire = auto_table("umpire", umpire)
    if pairs:
        p.pairs = auto_table("pairs", pairs)
    return p


def batches_of(project):
    """Batch names in file order."""
    t = project.assay
    if t is None or not t.mapping.get("batch"):
        return []
    seen = []
    for r in t.rows:
        b = str(t.get(r, "batch") or "").strip()
        if b and b not in seen:
            seen.append(b)
    return seen


def split_by_batch(project):
    """[(batch, Project)]: one project per batch, sharing the certificate,
    umpire and pair tables and the review decisions."""
    t = project.assay
    out = []
    for b in batches_of(project):
        sub = DataTable(t.kind, f"{t.name}-{b}", t.path, list(t.header),
                        [r for r in t.rows if str(t.get(r, "batch") or "").strip() == b],
                        t.delim)
        sub.mapping = dict(t.mapping)
        sub.value_cols = list(t.value_cols)
        sub.type_map = dict(t.type_map)
        sub.dl = dict(t.dl)
        sub.decimal_comma = t.decimal_comma
        p = Project()
        p.assay, p.crm, p.umpire, p.pairs = sub, project.crm, project.umpire, project.pairs
        p.pair_decisions = copy.deepcopy(project.pair_decisions)
        out.append((b, p))
    return out


def _safe(name):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name)).strip("_") or "batch"


def write_reports(project, R, d, meta, F, C, S, RB, folder, base, pdf=True,
                  browser=None, log=print):
    """HTML, PDF (when a browser is found) and Word of one analysed project."""
    from .report.builder import build_report
    from .report.docx_writer import write_docx
    from .report.html_writer import write_html
    os.makedirs(folder, exist_ok=True)
    doc = build_report(project, R, d, meta, F, C, S, RB, log=lambda m: None)
    files = [write_html(doc, os.path.join(folder, base + ".html"))]
    if pdf:
        try:
            from .report.pdf import html_to_pdf
            files.append(html_to_pdf(files[0], os.path.join(folder, base + ".pdf"),
                                     browser=browser))
        except Exception as ex:                  # noqa: BLE001 -- PDF is optional
            log(f"  PDF not written ({ex}).")
    files.append(write_docx(doc, os.path.join(folder, base + ".docx")))
    return files


def run_project(project, F, C, S, RB, folder, base, meta, per_batch=True, pdf=True,
                browser=None, log=print):
    """The combined analysis and report, and one report per batch.
    Returns {'combined': (R, d, files), 'batches': [(batch, decisions, files)],
    'matrix': (order, matrix)}."""
    from .analysis import run_analysis
    from .diagnosis import diagnose
    from .export_csv import export_results
    log("Project: combined analysis of every batch ...")
    R = run_analysis(project, F, C, S, RB, log=lambda m: None)
    d = diagnose(project, R, C, S, RB)
    files = export_results(project, F, C, S, RB, d, folder, base, log=lambda m: None)
    # the report fills empty metadata from the data: each report gets its own copy
    files += write_reports(project, R, d, copy.copy(meta), F, C, S, RB, folder, base, pdf,
                           browser, log)
    out = {"combined": (R, d, files), "batches": [], "matrix": d.batch_matrix()}
    if per_batch:
        for b, p in split_by_batch(project):
            log(f"Project: batch {b} ...")
            try:
                Rb = run_analysis(p, F, C, S, RB, log=lambda m: None)
            except ValueError as ex:
                log(f"  batch {b} skipped: {ex}")
                continue
            db = diagnose(p, Rb, C, S, RB)
            mb = copy.copy(meta)
            if mb is not None and hasattr(mb, "project"):
                mb.project = f"{meta.project} - batch {b}" if meta.project else f"Batch {b}"
            sub = os.path.join(folder, "batches", _safe(b))
            fb = write_reports(p, Rb, db, mb, F, C, S, RB, sub, f"{base}_B{_safe(b)}",
                               pdf, browser, log)
            out["batches"].append((b, {el: db.decision(el)[0] for el in p.elements}, fb))
    return out
