#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEOQAQC 2.0 -- Analytical Quality Control Suite
===============================================
QA/QC of geochemical analytical data from any sampling medium, with automatic
data cleaning, diagnosis of the source of every error by stage of the sample
chain, and a Persian consultant report (HTML, PDF, Word).

Run        : double-click RUN_GEOQAQC.bat, or  python GEOQAQC.py
Self-test  : python GEOQAQC.py --selftest [output folder]
Requires   : Python 3.9+, matplotlib, python-docx  (pip install -r requirements.txt)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _missing():
    out = []
    for mod, pkg in (("matplotlib", "matplotlib"), ("docx", "python-docx")):
        try:
            __import__(mod)
        except ImportError:
            out.append(pkg)
    return out


def selftest(folder=None):
    """Run the demo end to end without a window: analysis, diagnosis, CSV,
    HTML, PDF (when a browser is found) and Word."""
    import tempfile
    from geoqaqc.analysis import run_analysis
    from geoqaqc.diagnosis import diagnose
    from geoqaqc.export_csv import export_results
    from geoqaqc.loader import load_project
    from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS, DEFAULT_SETTINGS,
                                  FormulaBook, RuleBook)
    from geoqaqc.report.builder import build_report
    from geoqaqc.report.document import ReportMeta
    from geoqaqc.report.docx_writer import write_docx
    from geoqaqc.report.html_writer import write_html
    from geoqaqc.report.pdf import html_to_pdf

    base = getattr(sys, "_MEIPASS", HERE)
    data = os.path.join(base, "sample_data")
    folder = folder or tempfile.mkdtemp(prefix="geoqaqc_selftest_")
    os.makedirs(folder, exist_ok=True)
    p = load_project(os.path.join(data, "demo_assay.csv"),
                     os.path.join(data, "demo_crm_certificates.csv"),
                     os.path.join(data, "demo_umpire.csv"))
    F, S, RB = FormulaBook(DEFAULT_FORMULAS), dict(DEFAULT_SETTINGS), RuleBook()
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    R = run_analysis(p, F, C, S, RB, log=print)
    d = diagnose(p, R, C, S, RB)
    for el in p.elements:
        print(f"  {el}: {d.verdict(el)[0]}")
    files = export_results(p, F, C, S, RB, d, folder, "demo", log=lambda m: None)
    meta = ReportMeta(project="Demonstration dataset (synthetic)", report_no="SELFTEST")
    doc = build_report(p, R, d, meta, F, C, S, RB)
    html = write_html(doc, os.path.join(folder, "demo_report.html"))
    files.append(html)
    try:
        files.append(html_to_pdf(html, os.path.join(folder, "demo_report.pdf")))
    except RuntimeError as ex:
        print(f"  PDF skipped: {ex}")
    files.append(write_docx(doc, os.path.join(folder, "demo_report.docx")))
    print(f"{len(files)} file(s) written to {folder}")
    for f in files:
        print("  ", os.path.basename(f))
    return 0


def main():
    missing = _missing()
    if missing:
        msg = ("GEOQAQC needs these Python packages:\n\n    " + ", ".join(missing)
               + "\n\nInstall them with:\n\n    python -m pip install -r requirements.txt")
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror("GEOQAQC", msg)
            r.destroy()
        except Exception:
            print(msg)
        return 1
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest(sys.argv[2] if len(sys.argv) > 2 else None)
    from geoqaqc.ui.app import main as run_app
    run_app()
    return 0


if __name__ == "__main__":
    sys.exit(main())
