# -*- coding: utf-8 -*-
"""The GEOQAQC main window."""

from __future__ import annotations

import datetime as _dt
import os
import queue
import sys
import threading
import tkinter as tk
import traceback
import webbrowser
from tkinter import filedialog, messagebox, ttk

from .. import APP_NAME, APP_SUB, APP_VER, session
from ..analysis import dup_stats, group_breakdown, group_rows, group_values, run_analysis
from ..cleaning import RULE_TITLES
from ..core import (GROUP_CHOICES, GROUP_KEYS, R_NA, RATING_ORDER, T_CDUP, T_FDUP,
                    T_PDUP, fmt_num, linreg, mean, pctile, rma)
from ..diagnosis import STAGE_EN, diagnose
from ..export_csv import export_results
from ..figures import (fig_accuracy_curve, fig_batch_matrix, fig_blank,
                       fig_blank_prev, fig_coverage, fig_crm_batch, fig_crm_bias,
                       fig_crm_control, fig_crm_cusum, fig_crm_drift, fig_crm_zhist,
                       fig_dup_hist, fig_dup_maxmin, fig_dup_mean_hrd, fig_dup_qq,
                       fig_dup_quartile, fig_dup_rank_hard, fig_dup_scatter,
                       fig_error_budget, fig_group_summary,
                       fig_insertion, fig_source_matrix, fig_th, fig_th_curve,
                       fig_ump_bias_grade, fig_ump_qq, fig_ump_quartile, fig_ump_ratio,
                       fig_ump_scatter, figure_catalog)
from ..loader import auto_table
from ..model import Project, read_table
from ..protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS, DEFAULT_SETTINGS, RULES,
                        FormulaBook, FormulaError, RuleBook)
from ..report.builder import build_report
from ..report.docx_writer import write_docx
from ..report.document import ReportMeta
from ..report.html_writer import write_html
from ..report.pdf import html_to_pdf
from .dialogs import ExportDialog, MappingDialog, ProgressDialog
from .theme import (ACCENT, BG0, BG1, BG2, C_ERR, C_WARN, FG, FG_DIM, MONO, RATING_COLOR,
                    UI, UI_B, UI_SMALL, UI_TITLE, VERDICT_COLOR, VERDICT_EN, apply_theme,
                    draw_logo, extend_theme)
from .widgets import FigureView, KpiCard, NavRail, ScrollFrame, fill, make_grid

PAGES = [("OVERVIEW", ["Dashboard", "Diagnosis", "Data Cleaning"]),
         ("METHODS", ["Standards", "Blanks", "Duplicates", "Precision", "Error Budget",
                      "Check / Umpire", "Batches", "Insertion"]),
         ("PROTOCOL", ["Formulas", "Criteria", "Rules", "Settings"]),
         ("OUTPUT", ["Report", "Log"])]
CRIT_BY_DUP = {T_FDUP: "fdup_hard90", T_CDUP: "cdup_hard90", T_PDUP: "pdup_hard90"}
FA_FONTS = ["B Nazanin", "B Lotus", "B Mitra", "Vazirmatn", "IRANSans", "Tahoma", "Arial"]


def app_dir():
    base = getattr(sys, "_MEIPASS", None)
    return base or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _f(v, d=2, sign=False):
    if v is None:
        return ""
    return f"{v:+.{d}f}" if sign else f"{v:.{d}f}"


def _attempt(work, progress):
    """{'value': work(progress)} or {'error': message and traceback}."""
    try:
        return {"value": work(progress)}
    except Exception as ex:                              # noqa: BLE001
        return {"error": f"{ex}\n{traceback.format_exc()}"}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VER}  --  {APP_SUB}")
        self.geometry("1480x920")
        self.minsize(1180, 720)
        self.configure(bg=BG0)
        try:
            self.state("zoomed")
        except tk.TclError:
            pass
        extend_theme(apply_theme(self))
        self.project = Project()
        self.F = FormulaBook(DEFAULT_FORMULAS)
        self.C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
        self.S = dict(DEFAULT_SETTINGS)
        self.RB = RuleBook()
        self.meta = ReportMeta()
        self.diag = None
        self.R = {}
        self.cat = {}
        self.kpi_cards = []
        self.pages = {}
        self.current_page = None
        self._svars, self._fvars, self._cvars = {}, {}, {}
        self.rule_vars, self.report_vars, self.el_vars = {}, {}, {}
        self._jobs = queue.Queue()
        self._busy = False              # a worker thread is reading the project
        self._build_header()
        self._build_body()
        self._build_status()
        self.log(f"{APP_NAME} {APP_VER} ready. Import the assay table, or press "
                 f"'Load demo' to see the program at work.")
        self._sync()
        self.select_page("Dashboard")
        self.after(150, self._poll_jobs)

    # =====================================================================
    #  layout
    # =====================================================================
    def _build_header(self):
        hd = tk.Frame(self, bg=BG0, height=70)
        hd.pack(fill="x", side="top")
        hd.pack_propagate(False)
        cv = tk.Canvas(hd, width=46, height=46, bg=BG0, highlightthickness=0)
        cv.pack(side="left", padx=(16, 12), pady=12)
        draw_logo(cv, 46, 46)
        tl = tk.Frame(hd, bg=BG0)
        tl.pack(side="left", pady=12)
        tk.Label(tl, text=APP_NAME, bg=BG0, fg=FG, font=UI_TITLE, anchor="w").pack(anchor="w")
        tk.Label(tl, text=f"{APP_SUB.upper()}   ·   {APP_VER}", bg=BG0, fg=ACCENT,
                 anchor="w", font=UI_SMALL).pack(anchor="w")
        self.badge = tk.Label(hd, text="  NOT ANALYSED  ", bg=BG2, fg=FG_DIM,
                              font=UI_B, padx=12, pady=7)
        self.badge.pack(side="left", padx=26)
        rb = tk.Frame(hd, bg=BG0)
        rb.pack(side="right", padx=14)
        for text, cmd in (("Load demo", self.load_demo), ("Load session", self.load_session),
                          ("Save session", self.save_session),
                          ("Export CSV", self.do_export)):
            ttk.Button(rb, text=text, command=cmd).pack(side="left", padx=3)
        self.btn_run = ttk.Button(rb, text="RUN QA/QC", style="Accent.TButton",
                                  command=self.do_analyse)
        self.btn_run.pack(side="left", padx=(10, 0))
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

    def _build_body(self):
        body = tk.Frame(self, bg=BG0)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=BG1, width=250)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="  WORKFLOW", bg=BG2, fg=ACCENT, font=UI_B, anchor="w",
                 pady=7).pack(fill="x")
        sf = tk.Frame(left, bg=BG1, padx=10, pady=8)
        sf.pack(fill="x")
        self.step_btns = {}
        for key, num, txt in (("assay", "1", "Assay / results"),
                              ("crm", "2", "CRM certificates"),
                              ("pairs", "3", "Duplicate pairs"),
                              ("umpire", "4", "Check / umpire")):
            b = ttk.Button(sf, text=f"  {num}.  {txt}", style="Step.TButton",
                           command=lambda k=key: self.do_import(k))
            b.pack(fill="x", pady=2)
            self.step_btns[key] = b
        ttk.Label(sf, text="CSV, TXT or Excel (.xlsx). Only the assay table is required.",
                  style="Dim.TLabel", justify="left", wraplength=220).pack(anchor="w",
                                                                         pady=(4, 0))
        self.rail = NavRail(left, PAGES, self.select_page)
        self.rail.pack(fill="both", expand=True, pady=(4, 0))
        right = ttk.Frame(body, style="Dark.TFrame")
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self.nb = ttk.Notebook(right, style="Hidden.TNotebook")
        self.nb.pack(fill="both", expand=True)
        builders = {"Dashboard": self._pg_dashboard, "Diagnosis": self._pg_diagnosis,
                    "Data Cleaning": self._pg_cleaning, "Standards": self._pg_crm,
                    "Blanks": self._pg_blank, "Duplicates": self._pg_dup,
                    "Precision": self._pg_th, "Error Budget": self._pg_budget,
                    "Check / Umpire": self._pg_umpire, "Batches": self._pg_batches,
                    "Insertion": self._pg_insertion, "Formulas": self._pg_formulas,
                    "Criteria": self._pg_criteria, "Rules": self._pg_rules,
                    "Settings": self._pg_settings, "Report": self._pg_report,
                    "Log": self._pg_log}
        for name in self.page_names():
            f = ttk.Frame(self.nb, style="Panel.TFrame", padding=10)
            self.nb.add(f, text=name)
            self.pages[name] = f
            builders[name](f)

    def _build_status(self):
        s = tk.Frame(self, bg=BG2, height=26)
        s.pack(fill="x", side="bottom")
        s.pack_propagate(False)
        self.status = tk.Label(s, text="Ready", bg=BG2, fg=FG_DIM, font=MONO, anchor="w")
        self.status.pack(side="left", padx=12)
        tk.Label(s, text=f"{APP_NAME} {APP_VER}", bg=BG2, fg=FG_DIM, font=MONO).pack(
            side="right", padx=12)

    def page_names(self):
        return [n for _, names in PAGES for n in names]

    def select_page(self, name):
        self.nb.select(self.pages[name])
        self.rail.select(name)
        self.current_page = name

    # -- small builders ------------------------------------------------------
    def _bar(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 6))
        return bar

    def _combo(self, bar, label, values, width, command, var=None):
        ttk.Label(bar, text=label, style="Sec.TLabel").pack(side="left", padx=(0, 6))
        v = var or tk.StringVar(value=values[0] if values else "")
        cb = ttk.Combobox(bar, textvariable=v, values=values, state="readonly", width=width)
        cb.pack(side="left", padx=(0, 16))
        cb.bind("<<ComboboxSelected>>", lambda e: command())
        return v, cb

    def _info(self, parent):
        lab = tk.Label(parent, text="", bg=BG1, fg=FG_DIM, font=MONO, anchor="w",
                       justify="left")
        lab.pack(fill="x", pady=(0, 4))
        return lab

    def _split(self, parent, top_h=420):
        pane = tk.PanedWindow(parent, orient="vertical", bg=BG1, sashwidth=5, bd=0)
        pane.pack(fill="both", expand=True)
        top = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(top, minsize=240, height=top_h)
        bot = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(bot, minsize=110)
        view = FigureView(top)
        view.pack(fill="both", expand=True)
        return view, bot

    # =====================================================================
    #  pages -- overview
    # =====================================================================
    def _pg_dashboard(self, f):
        self.dash_hdr = tk.Label(f, text="Import data and press RUN QA/QC  (or Load demo).",
                                 bg=BG1, fg=FG_DIM, font=UI, anchor="w", justify="left")
        self.dash_hdr.pack(fill="x", pady=(0, 8))
        self.card_row = tk.Frame(f, bg=BG1)
        self.card_row.pack(fill="x", pady=(0, 8))
        view, bot = self._split(f, 330)
        self.dash_view = view
        self.sctree = make_grid(bot, ("Section", "Subject", "Element", "n", "Statistic",
                                      "Value", "Criterion", "Rating"),
                                (110, 130, 80, 60, 200, 90, 220, 110))

    def _pg_diagnosis(self, f):
        bar = self._bar(f)
        self.dg_el, self.dg_el_cb = self._combo(bar, "Element", ["All"], 18,
                                                self.render_diagnosis)
        self.dg_sev, _ = self._combo(bar, "Severity", ["All", "CRITICAL", "MATERIAL", "MINOR"],
                                     12, self.render_diagnosis)
        ttk.Button(bar, text="Preview report", command=self.preview_report).pack(side="right")
        self.dg_lbl = self._info(f)
        pane = tk.PanedWindow(f, orient="horizontal", bg=BG1, sashwidth=5, bd=0)
        pane.pack(fill="both", expand=True)
        lf = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(lf, minsize=420, width=640)
        rf = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(rf, minsize=380)
        self.diag_tree = make_grid(lf, ("Element", "Stage", "Severity", "Finding", "Owner",
                                        "Timing"), (80, 130, 80, 250, 80, 110))
        self.diag_tree.bind("<<TreeviewSelect>>", lambda e: self._diag_selected())
        self.diag_view = FigureView(rf)
        self.diag_view.pack(fill="both", expand=True)
        self.verdict_tree = make_grid(f, ("Element", "Verdict", "Critical", "Material",
                                          "Minor"), (120, 220, 80, 80, 80), height=5)
        self._diag_rows = []

    def _pg_cleaning(self, f):
        bar = self._bar(f)
        self.cl_rule, self.cl_cb = self._combo(bar, "Rule", ["All"], 40, self.render_cleaning)
        ttk.Label(bar, text="Data errors are excluded or corrected; QC failures are never "
                            "removed. Switch rules and thresholds in Rules.",
                  style="Dim.TLabel").pack(side="left")
        self.cl_lbl = self._info(f)
        self.clean_tree = make_grid(f, ("Rule", "Title", "Sample", "Element", "Original",
                                        "Action", "Reason"),
                                    (55, 210, 120, 80, 110, 80, 560))

    # =====================================================================
    #  pages -- methods
    # =====================================================================
    def _pg_crm(self, f):
        bar = self._bar(f)
        self.crm_sel, self.crm_cb = self._combo(bar, "CRM / element", [""], 32, self.render_crm)
        self.crm_chart, _ = self._combo(
            bar, "Chart", ["Control chart", "Bias sequence", "Z-score distribution", "CUSUM",
                           "Bias by batch", "Laboratory drift (element)",
                           "Accuracy curve (element)", "Grade coverage (element)"],
            26, self.render_crm)
        self.crm_lbl = self._info(f)
        self.crm_view, bot = self._split(f)
        self.crmtree = make_grid(bot, ("Sample ID", "Batch", "Sequence", "Measured",
                                       "Certified", "Bias %", "Z-score", "Status",
                                       "Rule violations"),
                                 (140, 100, 80, 100, 100, 90, 90, 70, 320))

    def _pg_blank(self, f):
        bar = self._bar(f)
        self.bl_sel, self.bl_cb = self._combo(bar, "Blank type / element", [""], 32,
                                              self.render_blank)
        self.bl_chart, _ = self._combo(bar, "Chart", ["Control chart",
                                                      "Against preceding sample"],
                                       24, self.render_blank)
        self.bl_lbl = self._info(f)
        self.bl_view, bot = self._split(f)
        self.bltree = make_grid(bot, ("Sample ID", "Batch", "Sequence", "Value", "x DL",
                                      "Preceding Sample", "Preceding Value", "Carry-over %",
                                      "Status"),
                                (140, 100, 80, 100, 80, 150, 120, 110, 70))

    def _pg_dup(self, f):
        bar = self._bar(f)
        self.dup_sel, self.dup_cb = self._combo(bar, "Set", [""], 30, self._dup_groups_changed)
        self.dup_chart, _ = self._combo(
            bar, "Method", ["Ranked HARD", "Original vs duplicate", "Max-Min plot",
                            "Precision by grade quartile", "Q-Q plot",
                            "Relative difference vs grade", "HARD distribution",
                            "Compare groups (bar)"], 28, self.render_dup)
        bar2 = self._bar(f)
        self.dup_groupby, _ = self._combo(bar2, "Group by", GROUP_CHOICES, 16,
                                          self._dup_groups_changed)
        self.dup_group, self.dup_group_cb = self._combo(bar2, "Show", ["All groups"], 24,
                                                        self.render_dup)
        ttk.Label(bar2, text="Statistics and charts are recomputed for the selected group.",
                  style="Dim.TLabel").pack(side="left")
        self.dup_lbl = self._info(f)
        self.dup_view, bot = self._split(f, 400)
        self.dup_bot = bot
        self.duptree = make_grid(bot, ("Original", "Duplicate", "Group", "Value 1",
                                       "Value 2", "Mean", "RD %", "ARD %", "HARD %", "HRD %",
                                       "CV %", "Precision 95 %"),
                                 (130, 130, 110, 90, 90, 90, 80, 80, 80, 80, 80, 110))
        self.dupgrouptree = make_grid(bot, ("Group", "n pairs", "P90 HARD %", "Median HARD %",
                                            "Mean RD %", "Pooled RP %", "r", "Rating"),
                                      (170, 80, 110, 120, 100, 110, 90, 110))
        self.dupgrouptree.master.pack_forget()

    def _pg_th(self, f):
        bar = self._bar(f)
        self.th_sel, self.th_cb = self._combo(bar, "Set", [""], 30, self.render_th)
        self.th_chart, _ = self._combo(bar, "Chart", ["Precision curve", "Binned regression"],
                                       22, self.render_th)
        self.th_lbl = self._info(f)
        self.th_view, bot = self._split(f)
        self.thtree = make_grid(bot, ("Bin", "n", "Mean concentration", "Mean abs difference"),
                                (80, 70, 190, 190))

    def _pg_budget(self, f):
        ttk.Label(f, text="Share of the total relative variance carried by sampling, "
                          "preparation and analysis, from the mean squared pair CV of the "
                          "field, coarse and pulp duplicates.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 6))
        self.bud_view, bot = self._split(f, 420)
        self.budtree = make_grid(bot, ("Element", "Total CV %", "% sampling", "% preparation",
                                       "% analysis", "Dominant", "Notes"),
                                 (100, 90, 100, 110, 90, 160, 520))

    def _pg_umpire(self, f):
        bar = self._bar(f)
        self.ump_sel, self.ump_cb = self._combo(bar, "Element", [""], 18,
                                                self._ump_groups_changed)
        self.ump_chart, _ = self._combo(bar, "Chart", ["Q-Q plot", "Primary vs umpire",
                                                       "Bias vs grade", "Bias by grade quartile",
                                                       "Ranked ratio"], 24, self.render_umpire)
        bar2 = self._bar(f)
        self.ump_groupby, _ = self._combo(bar2, "Group by", GROUP_CHOICES, 16,
                                          self._ump_groups_changed)
        self.ump_group, self.ump_group_cb = self._combo(bar2, "Show", ["All groups"], 24,
                                                        self.render_umpire)
        self.ump_lbl = self._info(f)
        self.ump_view, bot = self._split(f, 400)
        self.umptree = make_grid(bot, ("Sample ID", "Group", "Primary", "Umpire", "Difference",
                                       "Bias %", "Ratio", "HARD %"),
                                 (200, 120, 110, 110, 110, 100, 100, 100))

    def _pg_batches(self, f):
        bar = self._bar(f)
        self.bt_sel, self.bt_cb = self._combo(bar, "Element", [""], 18, self.render_batches)
        self.bt_lbl = self._info(f)
        self.bt_view, bot = self._split(f, 300)
        self.bttree = make_grid(bot, ("Batch", "Samples", "CRM", "Blank", "Status", "Reasons"),
                                (110, 80, 70, 70, 70, 600), height=7)
        self.ratree = make_grid(bot, ("CRM", "Failed CRM", "Rule", "Batch", "From sample",
                                      "To sample", "Samples to re-assay"),
                                (130, 160, 80, 100, 130, 130, 140), height=6)

    def _pg_insertion(self, f):
        ttk.Label(f, text="Control sample insertion rates against the 5 % per class "
                          "convention (one in twenty).", style="Dim.TLabel").pack(
            anchor="w", pady=(0, 6))
        self.ins_view, bot = self._split(f, 380)
        self.instree = make_grid(bot, ("Sample type", "Count", "Insertion rate %",
                                       "One in every", "Rating"), (170, 100, 150, 140, 130))

    # =====================================================================
    #  pages -- protocol
    # =====================================================================
    def _pg_formulas(self, f):
        ttk.Label(f, text="Every quantity is an editable expression. Edit, Apply, then RUN "
                          "QA/QC. Allowed: + - * / ** ( ) abs sqrt log log10 exp min max "
                          "round floor ceil pow", style="Dim.TLabel").pack(anchor="w")
        bb = self._bar(f)
        ttk.Button(bb, text="Apply formulas", style="Accent.TButton",
                   command=self.apply_formulas).pack(side="left")
        ttk.Button(bb, text="Restore defaults", command=self.reset_formulas).pack(
            side="left", padx=6)
        sf = ScrollFrame(f)
        sf.pack(fill="both", expand=True)
        group = None
        for key, d in self.F.defs.items():
            if d["group"] != group:
                group = d["group"]
                tk.Label(sf.inner, text=f"  {group}", bg=BG2, fg=ACCENT, font=UI_B,
                         anchor="w", pady=5, width=150).pack(fill="x", pady=(10, 4))
            row = ttk.Frame(sf.inner, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=d["label"], style="Sec.TLabel", width=40,
                      anchor="w").pack(side="left")
            v = tk.StringVar(value=d["expr"])
            self._fvars[key] = v
            ttk.Entry(row, textvariable=v, width=56).pack(side="left", padx=6)
            ttk.Label(sf.inner, text=f"      {d['vars']}", style="Dim.TLabel").pack(anchor="w")
            ttk.Label(sf.inner, text=f"      {d['note']}", style="Dim.TLabel",
                      wraplength=1000, justify="left").pack(anchor="w", pady=(0, 4))

    def _pg_criteria(self, f):
        ttk.Label(f, text="Five boundaries per criterion produce the six rating classes. "
                          "Finding severities follow these ratings (see Rules).",
                  style="Dim.TLabel").pack(anchor="w")
        bb = self._bar(f)
        ttk.Button(bb, text="Apply criteria", style="Accent.TButton",
                   command=self.apply_criteria).pack(side="left")
        ttk.Button(bb, text="Restore defaults", command=self.reset_criteria).pack(
            side="left", padx=6)
        hdr = ttk.Frame(f, style="Panel.TFrame")
        hdr.pack(fill="x", pady=(4, 2))
        ttk.Label(hdr, text="criterion", style="Sec.TLabel", width=44, anchor="w").pack(
            side="left")
        for name in RATING_ORDER[:5]:
            tk.Label(hdr, text=name, bg=BG1, fg=RATING_COLOR[name], font=MONO,
                     width=11).pack(side="left", padx=2)
        sf = ScrollFrame(f)
        sf.pack(fill="both", expand=True)
        group = None
        for key, d in self.C.items():
            if d["group"] != group:
                group = d["group"]
                tk.Label(sf.inner, text=f"  {group}", bg=BG2, fg=ACCENT, font=UI_B,
                         anchor="w", pady=5, width=150).pack(fill="x", pady=(10, 4))
            row = ttk.Frame(sf.inner, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{d['label']} [{d['unit']}]", style="Sec.TLabel",
                      width=44, anchor="w").pack(side="left")
            vs = []
            for c in d["cuts"]:
                v = tk.StringVar(value=f"{c:g}")
                vs.append(v)
                ttk.Entry(row, textvariable=v, width=10).pack(side="left", padx=2)
            self._cvars[key] = vs
            ttk.Label(row, text="lower is better" if d["dir"] == "low" else "higher is better",
                      style="Dim.TLabel").pack(side="left", padx=10)
            ttk.Label(sf.inner, text=f"      {d['note']}", style="Dim.TLabel",
                      wraplength=1000, justify="left").pack(anchor="w", pady=(0, 4))

    def _pg_rules(self, f):
        ttk.Label(f, text="Every cleaning rule, diagnosis threshold, batch rule and severity "
                          "mapping. Saved with the session and written to the protocol of "
                          "every report.", style="Dim.TLabel").pack(anchor="w")
        bb = self._bar(f)
        ttk.Button(bb, text="Apply rules", style="Accent.TButton",
                   command=self.apply_rules).pack(side="left")
        ttk.Button(bb, text="Restore defaults", command=self.reset_rules).pack(
            side="left", padx=6)
        sf = ScrollFrame(f)
        sf.pack(fill="both", expand=True)
        for group, keys in self.RB.groups():
            tk.Label(sf.inner, text=f"  {group}", bg=BG2, fg=ACCENT, font=UI_B, anchor="w",
                     pady=5, width=150).pack(fill="x", pady=(10, 4))
            for key in keys:
                d = RULES[key]
                row = ttk.Frame(sf.inner, style="Panel.TFrame")
                row.pack(fill="x", pady=1)
                ttk.Label(row, text=d["label"], style="Sec.TLabel", width=52,
                          anchor="w").pack(side="left")
                if d["kind"] == "bool":
                    v = tk.BooleanVar(value=self.RB[key])
                    ttk.Checkbutton(row, variable=v).pack(side="left", padx=6)
                elif d["kind"] == "choice":
                    v = tk.StringVar(value=self.RB[key])
                    ttk.Combobox(row, textvariable=v, values=d["choices"], state="readonly",
                                 width=16).pack(side="left", padx=6)
                else:
                    v = tk.StringVar(value=self.RB.describe(key))
                    ttk.Entry(row, textvariable=v,
                              width=60 if d["kind"] == "list" else 12).pack(side="left", padx=6)
                self.rule_vars[key] = v
                if d.get("note"):
                    ttk.Label(sf.inner, text=f"      {d['note']}", style="Dim.TLabel",
                              wraplength=1000, justify="left").pack(anchor="w", pady=(0, 3))

    def _pg_settings(self, f):
        spec = [("Control chart warning limit (SD)", "k_warn", "Shewhart warning limit."),
                ("Control chart action limit (SD)", "k_fail", "A result beyond fails."),
                ("Blank contamination limit (x DL)", "k_dl", "5 x DL strict, 10 x DL tolerant."),
                ("High-grade predecessor (x DL)", "carry_kdl",
                 "Minimum grade of a 'high-grade' sample before a blank."),
                ("HARD percentile for acceptance", "hard_pct", "Usually the 90th."),
                ("Thompson-Howarth bin size", "th_group", "Pairs per bin (11 in 1978)."),
                ("Report TH precision at (x DL)", "th_at_dl", "Concentration read and rated."),
                ("Minimum duplicate pairs to rate", "min_pairs", "Fewer: no rating."),
                ("Minimum CRM results to rate", "min_crm", "Fewer: no rating."),
                ("Consecutive same-side run", "run_len", "Run length reported as bias."),
                ("Below-DL substitution factor", "dl_substitute", "If below-DL pairs are kept.")]
        box = ttk.Labelframe(f, text="  Analysis parameters  ", padding=12)
        box.pack(fill="x")
        for i, (lbl, key, hint) in enumerate(spec):
            v = tk.StringVar(value=str(self.S[key]))
            self._svars[key] = v
            ttk.Label(box, text=lbl, style="Sec.TLabel").grid(row=i, column=0, sticky="w", pady=3)
            ttk.Entry(box, textvariable=v, width=12).grid(row=i, column=1, sticky="w", padx=12)
            ttk.Label(box, text=hint, style="Dim.TLabel").grid(row=i, column=2, sticky="w")
        box2 = ttk.Labelframe(f, text="  Options  ", padding=12)
        box2.pack(fill="x", pady=12)
        for key, lbl in (("drop_below_dl", "Exclude duplicate pairs where either value is "
                                           "below the detection limit (recommended)"),
                         ("log_axis", "Logarithmic axes on scatter plots")):
            v = tk.BooleanVar(value=self.S[key])
            self._svars[key] = v
            ttk.Checkbutton(box2, text=lbl, variable=v).pack(anchor="w", pady=2)
        ttk.Button(f, text="Apply settings", style="Accent.TButton",
                   command=self.apply_settings).pack(anchor="w")

    # =====================================================================
    #  pages -- output
    # =====================================================================
    def _pg_report(self, f):
        sf = ScrollFrame(f)
        sf.pack(fill="both", expand=True)
        root = sf.inner
        ttk.Label(root, text="CONSULTANT REPORT", style="Head.TLabel").pack(anchor="w",
                                                                            pady=(0, 4))
        ttk.Label(root, text="A Persian report for the client, by element, with the source of "
                             "every error and its remedy. HTML and PDF (printed by Microsoft "
                             "Edge / Chrome) and an editable Word file.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 8))
        box = ttk.Labelframe(root, text="  Report details  ", padding=12)
        box.pack(fill="x")
        fields = [("project", "Project"), ("client", "Client"), ("consultant", "Consultant"),
                  ("author", "Prepared by"), ("author_title", "Title of the author"),
                  ("reviewer", "Reviewed by"), ("approver", "Approved by"),
                  ("report_no", "Report number"), ("revision", "Revision"),
                  ("date", "Date (YYYY-MM-DD)"), ("location", "Location"),
                  ("logo_path", "Logo image (PNG/JPG)"),
                  ("font_fa", "Persian font for Word"), ("font_latin", "Latin font for Word")]
        defaults = ReportMeta()
        for i, (key, label) in enumerate(fields):
            ttk.Label(box, text=label, style="Sec.TLabel").grid(row=i % 7, column=(i // 7) * 3,
                                                               sticky="w", pady=3, padx=(0, 8))
            v = tk.StringVar(value=getattr(defaults, key) or (
                _dt.date.today().isoformat() if key == "date" else ""))
            self.report_vars[key] = v
            if key == "font_fa":
                w = ttk.Combobox(box, textvariable=v, values=FA_FONTS, width=30)
            else:
                w = ttk.Entry(box, textvariable=v, width=34)
            w.grid(row=i % 7, column=(i // 7) * 3 + 1, sticky="w", padx=(0, 24))
            if key == "logo_path":
                ttk.Button(box, text="...", width=3, command=self._pick_logo).grid(
                    row=i % 7, column=(i // 7) * 3 + 2, sticky="w")
        self.el_box = ttk.Labelframe(root, text="  Elements with a full chapter  ", padding=12)
        self.el_box.pack(fill="x", pady=10)
        ttk.Label(self.el_box, text="Run the analysis to list the elements.",
                  style="Dim.TLabel").pack(anchor="w")
        opt = ttk.Labelframe(root, text="  Appendices  ", padding=12)
        opt.pack(fill="x")
        self.opt_vars = {}
        for key, label in (("include_cleaning_log", "Cleaning log"),
                           ("include_failed", "Failed control samples"),
                           ("include_protocol", "Run protocol")):
            v = tk.BooleanVar(value=True)
            self.opt_vars[key] = v
            ttk.Checkbutton(opt, text=label, variable=v).pack(side="left", padx=(0, 18))
        out = ttk.Labelframe(root, text="  Output  ", padding=12)
        out.pack(fill="x", pady=10)
        self.out_dir = tk.StringVar(value=os.path.expanduser("~"))
        self.out_base = tk.StringVar(value="QAQC_report")
        ttk.Label(out, text="Folder", style="Sec.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(out, textvariable=self.out_dir, width=60).grid(row=0, column=1, padx=8)
        ttk.Button(out, text="Browse", command=lambda: self._pick_dir(self.out_dir)).grid(
            row=0, column=2)
        ttk.Label(out, text="File name", style="Sec.TLabel").grid(row=1, column=0, sticky="w",
                                                                 pady=6)
        ttk.Entry(out, textvariable=self.out_base, width=60).grid(row=1, column=1, padx=8)
        bb = ttk.Frame(root, style="Panel.TFrame")
        bb.pack(fill="x", pady=4)
        ttk.Button(bb, text="Generate HTML + PDF + Word", style="Accent.TButton",
                   command=lambda: self.generate_report(pdf=True, word=True)).pack(side="left")
        ttk.Button(bb, text="HTML + PDF only",
                   command=lambda: self.generate_report(pdf=True, word=False)).pack(
            side="left", padx=6)
        ttk.Button(bb, text="Word only",
                   command=lambda: self.generate_report(pdf=False, word=True, html=False)).pack(
            side="left")
        ttk.Button(bb, text="Open folder", command=self._open_out).pack(side="left", padx=6)
        self.rep_lbl = tk.Label(root, text="", bg=BG1, fg=FG_DIM, font=MONO, anchor="w",
                                justify="left")
        self.rep_lbl.pack(fill="x", pady=6)

    def _pg_log(self, f):
        self.txt = tk.Text(f, bg=BG2, fg=FG, insertbackground=ACCENT, font=MONO, bd=0,
                           wrap="none", padx=10, pady=8)
        sb = ttk.Scrollbar(f, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set, state="disabled")
        self.txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # =====================================================================
    #  helpers
    # =====================================================================
    def log(self, msg):
        ts = _dt.datetime.now().strftime("%H:%M:%S")
        self.txt.configure(state="normal")
        self.txt.insert("end", f"[{ts}] {msg}\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")
        self.status.configure(text=str(msg).split("\n")[0][:170])
        self.update_idletasks()

    def _pick_dir(self, var):
        p = filedialog.askdirectory(parent=self)
        if p:
            var.set(p)

    def _pick_logo(self):
        p = filedialog.askopenfilename(parent=self, filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if p:
            self.report_vars["logo_path"].set(p)

    def _open_out(self):
        _open_path(self.out_dir.get())

    def _sync(self):
        p = self.project
        labels = {"assay": "Assay / results", "crm": "CRM certificates",
                  "pairs": "Duplicate pairs", "umpire": "Check / umpire"}
        for i, (key, label) in enumerate(labels.items(), start=1):
            t = getattr(p, key)
            self.step_btns[key].configure(
                text=f"  {i}.  {label}" + (f"   [{len(t.rows)}]" if t else ""))
        self.btn_run.configure(state="normal" if p.assay else "disabled")

    def set_badge(self):
        if not self.diag:
            self.badge.configure(text="  NOT ANALYSED  ", bg=BG2, fg=FG_DIM)
            return
        order = ["REMEDIATE", "RESTRICTED", "SUITABLE"]
        codes = [self.diag.verdict(el)[0] for el in self.project.elements]
        worst = min(codes, key=order.index) if codes else "SUITABLE"
        n = codes.count(worst)
        text = VERDICT_EN[worst] + ("" if worst == "SUITABLE" else f" ({n} element"
                                                                    f"{'s' if n > 1 else ''})")
        self.badge.configure(text=f"  {text.upper()}  ", bg=VERDICT_COLOR[worst], fg="#10151c")

    # =====================================================================
    #  import, analyse
    # =====================================================================
    def do_import(self, kind):
        p = filedialog.askopenfilename(
            parent=self, title=f"Select the {kind} file",
            filetypes=[("Tables", "*.csv *.txt *.tsv *.xlsx *.xlsm"), ("All files", "*.*")])
        if not p:
            return
        try:
            h, r, d = read_table(p)
        except Exception as ex:                          # noqa: BLE001
            messagebox.showerror(APP_NAME, f"Could not read the file:\n{ex}", parent=self)
            return
        if not h or not r:
            messagebox.showwarning(APP_NAME, "The file has no readable rows.", parent=self)
            return
        dlg = MappingDialog(self, kind, p, h, r, d)
        if not dlg.result:
            return
        setattr(self.project, kind, dlg.result)
        self.project.clear_results()
        self.log(f"Imported {kind}: {dlg.result.name} -- {len(r)} rows, {len(h)} columns.")
        self._sync()

    def load_files(self, assay, crm=None, umpire=None, pairs=None):
        """Load tables with the automatic mapping (the guesses the dialog pre-fills)."""
        self.project = Project()
        for kind, path in (("assay", assay), ("crm", crm), ("umpire", umpire),
                           ("pairs", pairs)):
            if path:
                setattr(self.project, kind, auto_table(kind, path))
                self.log(f"Loaded {kind}: {os.path.basename(path)}")
        self._sync()

    def load_demo(self):
        d = os.path.join(app_dir(), "sample_data")
        files = [os.path.join(d, f) for f in ("demo_assay.csv", "demo_crm_certificates.csv",
                                              "demo_umpire.csv")]
        if not all(os.path.exists(f) for f in files):
            messagebox.showerror(APP_NAME, f"The demo files were not found in\n{d}", parent=self)
            return
        self.load_files(*files)
        self.report_vars["project"].set("Demonstration dataset (synthetic)")
        self.do_analyse()

    def do_analyse(self, quiet=False, wait=False):
        """Cleaning, analysis and diagnosis in a worker thread behind a progress
        window, so a large project does not freeze the interface. wait=True
        runs it in place (tests, scripts)."""
        if self._busy:
            return
        if not self.project.assay:
            if not quiet:
                messagebox.showinfo(APP_NAME, "Import the assay table first.", parent=self)
            return
        self.log("=" * 60)
        project, F, C, S, RB = self.project, self.F, self.C, self.S, self.RB

        def work(progress):
            R = run_analysis(project, F, C, S, RB, log=progress)
            return R, diagnose(project, R, C, S, RB)

        def done(result):
            if "error" in result:
                self.log(f"FAILED: {result['error']}")
                if not quiet:
                    messagebox.showerror(APP_NAME, "Analysis failed:\n"
                                         + result["error"].split("\n")[0], parent=self)
                return
            self.R, self.diag = result["value"]
            self.cat = figure_catalog(self.project, self.R, self.diag, self.S, self.C,
                                      self.RB)
            for el in self.project.elements:
                code, _ = self.diag.verdict(el)
                self.log(f"  {el}: {VERDICT_EN[code]}")
            self.render_all()
            self._sync()
            self.select_page("Dashboard")

        if wait:
            done(_attempt(work, self.log))
            return
        self._start_job("analysis", "Cleaning, analysing and diagnosing the data",
                        work, done, prefix="")

    def _start_job(self, title, text, work, done, prefix="  "):
        """Run work(progress) in a thread; done(result) runs on the interface
        thread with {'value': ...} or {'error': ...}."""
        self._busy = True
        dlg = ProgressDialog(self, title, text)

        def run():
            result = _attempt(work, lambda m: self._jobs.put(("progress", dlg,
                                                               prefix + str(m))))
            self._jobs.put(("done", dlg, (result, done)))
        threading.Thread(target=run, daemon=True).start()

    # =====================================================================
    #  rendering
    # =====================================================================
    def render_all(self):
        R = self.R
        self.set_badge()
        self.render_dashboard()
        self.render_diagnosis()
        self.render_cleaning()
        keys = [f"{c}  /  {e}" for (c, e) in sorted(R["crm"])]
        self._set_combo(self.crm_cb, self.crm_sel, keys)
        self.render_crm()
        keys = [f"{b}  /  {e}" for (b, e) in sorted(R["blank"])]
        self._set_combo(self.bl_cb, self.bl_sel, keys)
        self.render_blank()
        keys = [f"{t}  /  {e}" for (t, e) in sorted(R["dup"])]
        self._set_combo(self.dup_cb, self.dup_sel, keys)
        self._dup_groups_changed()
        keys = [f"{t}  /  {e}" for (t, e) in sorted(R["th"])]
        self._set_combo(self.th_cb, self.th_sel, keys)
        self.render_th()
        self.render_budget()
        self._set_combo(self.ump_cb, self.ump_sel, sorted(R.get("umpire", {})))
        self._ump_groups_changed()
        self._set_combo(self.bt_cb, self.bt_sel, list(R.get("batches", {})))
        self.render_batches()
        self.render_insertion()
        self._report_elements()
        c = self.diag.counts()
        self.rail.badge("Diagnosis", f"{c['CRITICAL']}/{c['MATERIAL']}/{c['MINOR']}",
                        C_ERR if c["CRITICAL"] else C_WARN if c["MATERIAL"] else FG_DIM)
        n = len(self.project.clean_log.actions) if self.project.clean_log else 0
        self.rail.badge("Data Cleaning", str(n) if n else "", FG_DIM)

    def _set_combo(self, cb, var, values):
        cb.configure(values=values)
        if values and var.get() not in values:
            var.set(values[0])
        if not values:
            var.set("")

    def render_dashboard(self):
        R, d = self.R, self.diag
        for w in self.card_row.winfo_children():
            w.destroy()
        self.kpi_cards = []
        for i, el in enumerate(self.project.elements[:8]):
            card = KpiCard(self.card_row)
            card.grid(row=0, column=i, sticky="nsew", padx=(0, 8))
            self.card_row.columnconfigure(i, weight=1)
            worst = None
            for sec in ("crm", "blank", "dup"):
                for k, rec in R.get(sec, {}).items():
                    if k[-1] == el and rec.get("rating") in RATING_ORDER:
                        if worst is None or RATING_ORDER.index(rec["rating"]) > \
                                RATING_ORDER.index(worst):
                            worst = rec["rating"]
            card.set(el, d.verdict(el)[0], d.counts(el), worst)
            self.kpi_cards.append(card)
        live = [s for s in self.project.samples if not s.dropped]
        self.dash_hdr.configure(
            text=f"{len(live)} samples   {len(self.project.elements)} element(s)   "
                 f"weighted QA/QC rating {R['overall']}"
                 + (f" ({R['score']:.0f}/100)" if R.get("score") is not None else "")
                 + f"   analysed {self.project.analysed_at:%Y-%m-%d %H:%M}\n"
                   "The weighted rating is an average; read the element verdicts and the "
                   "diagnosis before drawing a conclusion.", fg=FG)
        self.dash_view.show(fig_source_matrix(d))
        rows, tags = [], []

        def add(sec, subj, el, n, stat, val, crit, rating):
            rows.append((sec, subj, el, n, stat, "" if val is None else
                         (f"{val:.3f}" if isinstance(val, float) else val), crit, rating))
            tags.append(rating)
        for (code, el), rec in sorted(R["crm"].items()):
            add("CRM", code, el, rec["n"], "mean bias %", rec.get("bias"),
                self.C["crm_bias"]["label"], rec["ratings"].get("crm_bias", R_NA))
        for (bt, el), rec in sorted(R["blank"].items()):
            add("BLANK", bt, el, rec["n"], "failure rate %", rec["fail_pct"],
                self.C["blank_fail"]["label"], rec["ratings"].get("blank_fail", R_NA))
        for (dt, el), rec in sorted(R["dup"].items()):
            add(dt, "duplicates", el, rec["n"], f"P{rec['hard_pct_used']:g} HARD %",
                rec.get("hard_p90"), self.C[CRIT_BY_DUP[dt]]["label"],
                rec["ratings"].get(CRIT_BY_DUP[dt], R_NA))
        for el, rec in sorted(R.get("umpire", {}).items()):
            add("CHECK / UMPIRE", rec.get("lab") or "umpire", el, rec["n"],
                "grade-weighted bias %", rec.get("wbias"), self.C["ump_wbias"]["label"],
                rec["ratings"].get("ump_wbias", R_NA))
        for r in R["insertion"]["rows"]:
            if not r.get("info_only"):
                add("INSERTION", r["type"], "", r["n"], "insertion rate %", r["pct"],
                    self.C["insert_rate"]["label"], r["rating"])
        fill(self.sctree, rows, tags)

    def render_diagnosis(self):
        if not self.diag:
            return
        self._set_combo(self.dg_el_cb, self.dg_el,
                        ["All"] + list(self.project.elements) + ["(project)"])
        el, sev = self.dg_el.get(), self.dg_sev.get()
        rows, tags, self._diag_rows = [], [], []
        for f in self.diag.actions():
            fe = f.element or "(project)"
            if el not in ("", "All") and fe != el:
                continue
            if sev not in ("", "All") and f.severity != sev:
                continue
            title = f.title_en + (f" -- {f.subject.lower()}" if f.subject else "")
            rows.append((fe, STAGE_EN[f.stage], f.severity, title, f.owner, f.timing))
            tags.append(f.severity)
            self._diag_rows.append(f)
        fill(self.diag_tree, rows, tags)
        c = self.diag.counts()
        self.dg_lbl.configure(text=f"{len(self.diag.findings)} findings:  critical "
                                   f"{c['CRITICAL']}   material {c['MATERIAL']}   minor "
                                   f"{c['MINOR']}.   Select a finding to see its chart; the "
                                   f"evidence, cause and remedy are written out in the report.")
        vr, vt = [], []
        for e in self.project.elements:
            code, _ = self.diag.verdict(e)
            cc = self.diag.counts(e)
            vr.append((e, VERDICT_EN[code], cc["CRITICAL"], cc["MATERIAL"], cc["MINOR"]))
            vt.append(code)
        fill(self.verdict_tree, vr, vt)
        if self._diag_rows:
            self.diag_view.show(fig_source_matrix(self.diag))

    def _diag_selected(self):
        sel = self.diag_tree.selection()
        if not sel:
            return
        f = self._diag_rows[self.diag_tree.index(sel[0])]
        for ref in f.figures:
            hits = [k for k in self.cat if k == ref or k.startswith(ref + "/")]
            if hits:
                self.diag_view.show(self.cat[hits[0]]())
                return
        self.diag_view.show(fig_source_matrix(self.diag))

    def render_cleaning(self):
        L = self.project.clean_log
        if L is None:
            return
        rules = ["All"] + [f"{k}  {RULE_TITLES[k][0]}" for k in L.counts()]
        self.cl_cb.configure(values=rules)
        if self.cl_rule.get() not in rules:
            self.cl_rule.set("All")
        sel = self.cl_rule.get().split(" ")[0]
        rows, tags = [], []
        for a in L.actions:
            if sel not in ("", "All") and a.rule != sel:
                continue
            rows.append((a.rule, RULE_TITLES.get(a.rule, ("",))[0], a.sample, a.element,
                         a.original, a.action, a.reason))
            tags.append({"error": "FAIL", "warning": "WARN"}.get(a.severity, ""))
        fill(self.clean_tree, rows, tags)
        self.cl_lbl.configure(text="   ".join(f"{k}: {v}" for k, v in L.counts().items())
                              or "No data errors found.")

    # -- CRM ----------------------------------------------------------------
    def render_crm(self):
        R = self.R
        if not R or not self.crm_sel.get():
            return
        code, el = [s.strip() for s in self.crm_sel.get().rsplit("/", 1)]
        rec = R["crm"].get((code, el))
        if not rec:
            return
        mode = self.crm_chart.get()
        S, C = self.S, self.C
        if mode.startswith("Bias seq"):
            fig = fig_crm_bias(rec, S, C)
        elif mode.startswith("Z-score"):
            fig = fig_crm_zhist(rec, S)
        elif mode.startswith("CUSUM"):
            fig = fig_crm_cusum(rec, S, self.RB)
        elif mode.startswith("Bias by"):
            fig = fig_crm_batch(rec, S, C)
        elif mode.startswith("Laboratory") and el in R.get("drift", {}):
            fig = fig_crm_drift(R["drift"][el], el, S, C)
        elif mode.startswith("Accuracy") and el in R.get("accuracy", {}):
            fig = fig_accuracy_curve(R["accuracy"][el], el)
        elif mode.startswith("Grade") and el in R.get("coverage", {}):
            fig = fig_coverage(R["coverage"][el], el)
        else:
            fig = fig_crm_control(rec, S)
        self.crm_view.show(fig)
        bits = [f"RATING {rec['rating']}", f"n = {rec['n']}"]
        if rec.get("cert") is not None:
            bits.append(f"certified {fmt_num(rec['cert'])}"
                        + (f" +/- {fmt_num(rec['sd'])}" if rec.get("sd") else ""))
        if rec.get("bias") is not None:
            bits.append(f"mean bias {rec['bias']:+.2f} %")
        if rec.get("fail_pct") is not None:
            bits.append(f"beyond {S['k_fail']:g} SD {rec['fail_pct']:.1f} %")
        if rec.get("drift"):
            bits.append(f"drift {rec['drift']['total']:+.2f} % (p {rec['drift']['p']:.3f})")
        if rec.get("excluded"):
            bits.append(f"{len(rec['excluded'])} excluded by cleaning")
        txt = "     ".join(bits) + (("\n" + rec["note"]) if rec.get("note") else "")
        self.crm_lbl.configure(text=txt, fg=RATING_COLOR.get(rec["rating"], FG_DIM))
        by_sample = {}
        for r in rec["rules"]:
            by_sample.setdefault(r["sample"], []).append(f"{r['rule']} {r['desc']}")
        rows, tags = [], []
        for p in rec["points"]:
            z = p["z"]
            st = ("FAIL" if z is not None and abs(z) > S["k_fail"] else
                  "WARN" if z is not None and abs(z) > S["k_warn"] else "OK")
            rows.append((p["sample"], p["batch"], fmt_num(p["order"]), fmt_num(p["value"]),
                         fmt_num(rec.get("cert")), _f(p["bias"], 2, True), _f(z, 2, True), st,
                         " | ".join(by_sample.get(p["sample"], []))[:200]))
            tags.append(st)
        fill(self.crmtree, rows, tags)

    # -- blanks --------------------------------------------------------------
    def render_blank(self):
        R = self.R
        if not R or not self.bl_sel.get():
            return
        bt, el = [s.strip() for s in self.bl_sel.get().rsplit("/", 1)]
        rec = R["blank"].get((bt, el))
        if not rec:
            return
        if self.bl_chart.get().startswith("Against"):
            self.bl_view.show(fig_blank_prev(rec, self.S))
        else:
            self.bl_view.show(fig_blank(rec, self.S))
        self.bl_lbl.configure(
            text=f"RATING {rec['rating']}     n = {rec['n']}     DL = {fmt_num(rec['dl'])}     "
                 f"limit {fmt_num(rec['limit'])}     failures {rec['n_fail']} "
                 f"({rec['fail_pct']:.1f} %)     worst {rec['max_ratio']:.1f} x DL"
                 + (f"     after high grade {rec['fail_after_high_pct']:.0f} % failed"
                    if rec.get("fail_after_high_pct") is not None else ""),
            fg=RATING_COLOR.get(rec["rating"], FG_DIM))
        rows, tags = [], []
        for p in rec["points"]:
            rows.append((p["sample"], p["batch"], fmt_num(p["order"]), fmt_num(p["value"]),
                         _f(p["ratio"]), p["prev_sample"], fmt_num(p["prev_value"]),
                         _f(p["carry_pct"], 3), "FAIL" if p["fail"] else "OK"))
            tags.append("FAIL" if p["fail"] else "OK")
        fill(self.bltree, rows, tags)

    # -- duplicates -------------------------------------------------------------
    def _dup_context(self):
        R = self.R
        if not R or not self.dup_sel.get():
            return None
        dt, el = [x.strip() for x in self.dup_sel.get().rsplit("/", 1)]
        rec = R["dup"].get((dt, el))
        if not rec:
            return None
        key = GROUP_KEYS.get(self.dup_groupby.get())
        val = self.dup_group.get()
        if not key or val in ("", "All groups"):
            return rec, key, None, rec["rows"]
        return rec, key, val, group_rows(rec["rows"], key, val)

    def _dup_groups_changed(self):
        ctx = self._dup_context()
        key = GROUP_KEYS.get(self.dup_groupby.get())
        vals = ["All groups"] + (group_values(ctx[0]["rows"], key) if ctx and key else [])
        self.dup_group_cb.configure(values=vals)
        if self.dup_group.get() not in vals:
            self.dup_group.set("All groups")
        self.render_dup()

    def render_dup(self):
        ctx = self._dup_context()
        if not ctx:
            return
        rec, key, val, rows = ctx
        dt = rec["type"]
        crit_key = CRIT_BY_DUP[dt]
        mode = self.dup_chart.get()
        view = dict(rec)
        view["rows"] = rows
        st = dup_stats(rows, self.F, self.C, self.S, crit_key)
        if st:
            view.update(st)
        if mode.startswith("Compare groups") and key:
            bd = group_breakdown(rec, key, self.F, self.C, self.S, crit_key)
            self.dup_view.show(fig_group_summary(bd, self.dup_groupby.get(), self.S,
                                                 self.C[crit_key]))
            self.duptree.master.pack_forget()
            self.dupgrouptree.master.pack(fill="both", expand=True)
            fill(self.dupgrouptree, [(g["group"], g["n"], _f(g["hard_p90"]),
                                      _f(g["hard_median"]), _f(g["rd_mean"], 2, True),
                                      _f(g["pooled_rp"]), _f(g["r"], 4),
                                      g.get("rating", R_NA)) for g in bd],
                 [g.get("rating", R_NA) for g in bd])
            self.dup_lbl.configure(text=f"{len(bd)} group(s); worst first. Groups with fewer "
                                        f"than {self.S['min_pairs']} pairs are not rated.",
                                   fg=FG_DIM)
            return
        self.dupgrouptree.master.pack_forget()
        self.duptree.master.pack(fill="both", expand=True)
        if not rows:
            self.dup_view.clear("no pairs in this group")
            fill(self.duptree, [])
            return
        full = len(rows) == len(rec["rows"])
        if mode.startswith("Original"):
            fig = fig_dup_scatter(view, self.S)
        elif mode.startswith("Max") and full:
            fig = fig_dup_maxmin(view, self.S)
        elif mode.startswith("Precision by") and full:
            fig = fig_dup_quartile(view, self.S, self.C)
        elif mode.startswith("Q-Q"):
            fig = fig_dup_qq(view, self.S)
        elif mode.startswith("Relative"):
            fig = fig_dup_mean_hrd(view, self.S)
        elif mode.startswith("HARD dist"):
            fig = fig_dup_hist(view, self.S)
        else:
            fig = fig_dup_rank_hard(view, self.S, self.C)
        self.dup_view.show(fig)
        bits = [f"RATING {view.get('rating', R_NA)}", f"n = {view['n']} pairs"]
        if val:
            bits.insert(1, f"{self.dup_groupby.get()} = {val}")
        bits += [f"P{view['hard_pct_used']:g} HARD {_f(view['hard_p90'])} %",
                 f"mean RD {_f(view['rd_mean'], 2, True)} %"]
        if rec.get("split") and full and rec["split"].get("t"):
            bits.append(f"splitting-bias p {rec['split']['t']['p']:.4f}")
        self.dup_lbl.configure(text="     ".join(bits),
                               fg=RATING_COLOR.get(view.get("rating"), FG_DIM))
        out, tags = [], []
        for r in rows:
            h = r["hard"]
            tags.append("OK" if h is not None and h <= 10 else
                        "WARN" if h is not None and h <= 20 else "FAIL")
            g = ((r.get(key) or "").strip() or "(not recorded)") if key else (r.get("hole") or "")
            out.append((r["orig"], r["dup"], g, fmt_num(r["a"]), fmt_num(r["b"]),
                        fmt_num(r["mean"]), _f(r["rd"], 2, True), _f(r["ard"]), _f(h),
                        _f(r["hrd"], 2, True), _f(r["cv"]), _f(r.get("prec95"))))
        fill(self.duptree, out, tags)

    # -- Thompson-Howarth -----------------------------------------------------
    def render_th(self):
        R = self.R
        if not R:
            return
        if not self.th_sel.get():
            why = R.get("th_skipped") or []
            self.th_view.clear("no Thompson-Howarth fit")
            self.th_lbl.configure(text="\n".join(f"{d} / {e}: {w}" for d, e, w in why)
                                  or "No duplicate pairs.", fg=C_WARN if why else FG_DIM)
            fill(self.thtree, [])
            return
        dt, el = [s.strip() for s in self.th_sel.get().rsplit("/", 1)]
        rec = R["th"].get((dt, el))
        if not rec:
            return
        self.th_view.show(fig_th(rec, self.S) if self.th_chart.get().startswith("Binned")
                          else fig_th_curve(rec, self.S))
        self.th_lbl.configure(
            text=f"RATING {rec['rating']}     bins of {rec['group']}     precision at "
                 f"{fmt_num(rec['c_ref'])} = {rec['precision_at_ref']:.2f} %     practical DL "
                 f"{fmt_num(rec['pdl']) if rec.get('pdl') else 'not resolvable'}",
            fg=RATING_COLOR.get(rec["rating"], FG_DIM))
        fill(self.thtree, [(i, b["n"], fmt_num(b["conc"]), fmt_num(b["dbar"]))
                           for i, b in enumerate(rec["bins"], start=1)])

    def render_budget(self):
        B = self.R.get("budget", {})
        self.bud_view.show(fig_error_budget(B, self.project.elements))
        rows = []
        for el in self.project.elements:
            b = B.get(el)
            if not b:
                continue
            pct = b.get("pct", {})
            rows.append((el, _f(b.get("total_cv_pct"), 1),
                         _f(pct.get("sampling", pct.get("sampling+preparation")), 1),
                         _f(pct.get("preparation", pct.get("preparation+analytical")), 1),
                         _f(pct.get("analytical"), 1), b.get("dominant") or "",
                         " | ".join(b.get("notes", []))))
        fill(self.budtree, rows)

    # -- umpire -----------------------------------------------------------------
    def _ump_groups_changed(self):
        R = self.R
        rec = R.get("umpire", {}).get(self.ump_sel.get()) if R else None
        key = GROUP_KEYS.get(self.ump_groupby.get())
        vals = ["All groups"] + (group_values(rec["rows"], key) if rec and key else [])
        self.ump_group_cb.configure(values=vals)
        if self.ump_group.get() not in vals:
            self.ump_group.set("All groups")
        self.render_umpire()

    def render_umpire(self):
        R = self.R
        if not R:
            return
        rec = R.get("umpire", {}).get(self.ump_sel.get())
        if not rec:
            self.ump_view.clear("no check / umpire pairs")
            self.ump_lbl.configure(text="Import a second-laboratory file (step 4) or mark rows "
                                        "CHECK / UMPIRE with their parent sample ID.", fg=FG_DIM)
            fill(self.umptree, [])
            return
        key = GROUP_KEYS.get(self.ump_groupby.get())
        gval = self.ump_group.get()
        rows = rec["rows"]
        if key and gval not in ("", "All groups"):
            rows = group_rows(rec["rows"], key, gval)
        if not rows:
            self.ump_view.clear("no pairs in this group")
            fill(self.umptree, [])
            return
        rec = dict(rec)
        if len(rows) != len(R["umpire"][self.ump_sel.get()]["rows"]):
            sp = sum(r["primary"] for r in rows)
            su = sum(r["umpire"] for r in rows)
            hh = sorted(r["hard"] for r in rows if r["hard"] is not None)
            rec.update(rows=rows, n=len(rows), sum_primary=sp, sum_umpire=su,
                       wbias=self.F.calc("ump_weighted_bias", sum_pr=sp, sum_u=su),
                       pbias=mean([r["bias"] for r in rows if r["bias"] is not None]),
                       hard_p90=pctile(hh, self.S["hard_pct"]), quartiles=None,
                       ttest=None, rating=R_NA,
                       median_ratio=pctile(sorted(r["ratio"] for r in rows
                                                  if r["ratio"] is not None), 50))
            _, _, rec["r"] = linreg([r["primary"] for r in rows], [r["umpire"] for r in rows])
            rec["rma_a"], rec["rma_b"] = rma([r["primary"] for r in rows],
                                             [r["umpire"] for r in rows])
        mode = self.ump_chart.get()
        if mode.startswith("Primary"):
            fig = fig_ump_scatter(rec, self.S)
        elif mode.startswith("Bias vs"):
            fig = fig_ump_bias_grade(rec, self.S)
        elif mode.startswith("Bias by"):
            fig = fig_ump_quartile(rec, self.S, self.C)
        elif mode.startswith("Ranked"):
            fig = fig_ump_ratio(rec, self.S)
        else:
            fig = fig_ump_qq(rec, self.S)
        self.ump_view.show(fig)
        tt = rec.get("ttest") or {}
        self.ump_lbl.configure(
            text=f"RATING {rec['rating']}     n = {rec['n']} pairs     grade-weighted bias "
                 f"{_f(rec.get('wbias'), 2, True)} %     mean pair bias "
                 f"{_f(rec.get('pbias'), 2, True)} %"
                 + (f"     paired t p = {tt['p']:.4f}" if tt.get("p") is not None else ""),
            fg=RATING_COLOR.get(rec["rating"], FG_DIM))
        out, tags = [], []
        for r in rows:
            b = r["bias"]
            tags.append("OK" if b is not None and abs(b) <= 10 else
                        "WARN" if b is not None and abs(b) <= 20 else "FAIL")
            g = ((r.get(key) or "").strip() or "(not recorded)") if key else (r.get("hole") or "")
            out.append((r["sample"], g, fmt_num(r["primary"]), fmt_num(r["umpire"]),
                        fmt_num(r["diff"]), _f(b, 2, True), _f(r["ratio"], 4), _f(r["hard"])))
        fill(self.umptree, out, tags)

    # -- batches, insertion ---------------------------------------------------
    def render_batches(self):
        B = self.R.get("batches", {})
        if not B:
            return
        self.bt_view.show(fig_batch_matrix(B, self.project.elements))
        el = self.bt_sel.get()
        b = B.get(el)
        if not b:
            return
        self.bt_lbl.configure(text=f"{el}: {b['n_fail']} failed and {b['n_warn']} warning "
                                   f"batch(es) of {len(b['rows'])}; {len(b['reassay'])} "
                                   f"re-assay range(s).", fg=C_ERR if b["n_fail"] else FG_DIM)
        fill(self.bttree, [(r["batch"], r["n"], r["crm_status"], r["blank_status"],
                            r["status"], " | ".join(r["reasons"])) for r in b["rows"]],
             [r["status"] for r in b["rows"]])
        fill(self.ratree, [(r["crm"], r["failed_sample"], r["rule"], r["batch"],
                            r["from_sample"], r["to_sample"], r["n_samples"])
                           for r in b["reassay"]])

    def render_insertion(self):
        ins = self.R["insertion"]
        self.ins_view.show(fig_insertion(ins, self.S))
        fill(self.instree, [(r["type"], r["n"], _f(r["pct"]),
                             f"1 in {r['every']:.0f}" if r.get("every") else "",
                             "info" if r.get("info_only") else r["rating"])
                            for r in ins["rows"]],
             [r["rating"] for r in ins["rows"]])

    # =====================================================================
    #  protocol actions
    # =====================================================================
    def apply_settings(self):
        try:
            for k, v in self._svars.items():
                self.S[k] = v.get() if isinstance(v, tk.BooleanVar) else float(v.get())
        except ValueError:
            messagebox.showerror(APP_NAME, "All parameters must be numeric.", parent=self)
            return
        for k in ("th_group", "run_len", "min_pairs", "min_crm"):
            self.S[k] = int(self.S[k])
        self.log("Settings applied. Press RUN QA/QC to re-analyse.")

    def apply_formulas(self):
        bad = []
        for key, v in self._fvars.items():
            expr = v.get().strip()
            if expr == self.F.expr(key):
                continue
            try:
                self.F.set_expr(key, expr)
                self.log(f"formula '{self.F.defs[key]['label']}' = {expr}")
            except FormulaError as ex:
                bad.append(f"{self.F.defs[key]['label']}: {ex}")
                v.set(self.F.expr(key))
        if bad:
            messagebox.showerror(APP_NAME, "Rejected and reverted:\n\n" + "\n".join(bad),
                                 parent=self)
        else:
            self.log("Formulas applied. Press RUN QA/QC to re-analyse.")

    def reset_formulas(self):
        self.F = FormulaBook(DEFAULT_FORMULAS)
        for key, v in self._fvars.items():
            v.set(self.F.expr(key))
        self.log("Formulas restored to defaults.")

    def apply_criteria(self):
        try:
            for key, vs in self._cvars.items():
                cuts = [float(v.get()) for v in vs]
                d = self.C[key]
                ok = cuts == sorted(cuts) if d["dir"] == "low" else cuts == sorted(cuts,
                                                                                   reverse=True)
                if not ok:
                    raise ValueError(f"'{d['label']}': boundaries must run from best to worst.")
                d["cuts"] = cuts
        except ValueError as ex:
            messagebox.showerror(APP_NAME, str(ex), parent=self)
            return
        self.log("Criteria applied. Press RUN QA/QC to re-rate.")

    def reset_criteria(self):
        self.C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
        for key, vs in self._cvars.items():
            for v, c in zip(vs, self.C[key]["cuts"]):
                v.set(f"{c:g}")
        self.log("Criteria restored to defaults.")

    def apply_rules(self, quiet=False):
        """Validate every rule entry through the RuleBook. Returns the list of
        rejected entries (empty when all were accepted)."""
        bad = []
        for key, v in self.rule_vars.items():
            try:
                self.RB.set(key, v.get())
            except ValueError as ex:
                bad.append(str(ex))
                v.set(self.RB[key] if RULES[key]["kind"] in ("bool", "choice")
                      else self.RB.describe(key))
        if bad and not quiet:
            messagebox.showerror(APP_NAME, "These entries were rejected:\n\n" + "\n".join(bad),
                                 parent=self)
        if not bad:
            ch = self.RB.changed()
            self.log("Rules applied" + (f"; changed from the standard protocol: "
                                        f"{', '.join(ch)}" if ch else "") + ".")
        return bad

    def reset_rules(self):
        self.RB.reset()
        self._refresh_rule_vars()
        self.log("Rules restored to defaults.")

    def _refresh_rule_vars(self):
        for key, v in self.rule_vars.items():
            v.set(self.RB[key] if RULES[key]["kind"] in ("bool", "choice")
                  else self.RB.describe(key))

    # =====================================================================
    #  report
    # =====================================================================
    def _report_elements(self):
        for w in self.el_box.winfo_children():
            w.destroy()
        self.el_vars = {}
        for i, el in enumerate(self.project.elements):
            v = tk.BooleanVar(value=i < 8)
            self.el_vars[el] = v
            ttk.Checkbutton(self.el_box, text=el, variable=v).grid(row=i // 8, column=i % 8,
                                                                  sticky="w", padx=(0, 14))

    def _meta(self):
        d = {k: v.get().strip() for k, v in self.report_vars.items()}
        d.update({k: v.get() for k, v in self.opt_vars.items()})
        d["detail_elements"] = [e for e, v in self.el_vars.items() if v.get()]
        return ReportMeta.from_dict(d)

    def generate_report(self, folder=None, base=None, pdf=True, word=True, html=True,
                        wait=False):
        if self._busy:
            return []
        if not self.R or not self.diag:
            if not wait:
                messagebox.showinfo(APP_NAME, "Run the analysis first.", parent=self)
            return []
        folder = folder or self.out_dir.get()
        base = (base or self.out_base.get() or "QAQC_report").strip()
        if not os.path.isdir(folder):
            messagebox.showwarning(APP_NAME, "Choose a valid output folder.", parent=self)
            return []
        meta = self._meta()
        args = (self.project, self.R, self.diag, meta, self.F, self.C, self.S, self.RB)

        def work(progress):
            out = []
            progress("Building the report ...")
            doc = build_report(*args, log=lambda m: progress(m.split("\n")[0]))
            h = os.path.join(folder, base + ".html")
            if html or pdf:
                progress("Writing HTML (charts in vector) ...")
                out.append(write_html(doc, h))
            if pdf:
                progress("Printing PDF with the browser ...")
                try:
                    out.append(html_to_pdf(h, os.path.join(folder, base + ".pdf")))
                except RuntimeError as ex:
                    progress(f"PDF skipped: {ex}")
            if word:
                progress("Writing Word ...")
                out.append(write_docx(doc, os.path.join(folder, base + ".docx")))
            return out

        if wait:
            return work(lambda m: None)
        self._start_job("report", "Generating the consultant report",
                        work, self._report_done)
        return []

    def _report_done(self, result):
        if "error" in result:
            self.log(f"Report failed: {result['error']}")
            messagebox.showerror(APP_NAME, "The report could not be built:\n"
                                 + result["error"].split("\n")[0], parent=self)
            return
        paths = result["value"]
        self.rep_lbl.configure(text="Written:\n" + "\n".join(paths), fg=FG)
        self.log(f"Report written: {', '.join(os.path.basename(p) for p in paths)}")
        if paths and messagebox.askyesno(APP_NAME, "Report written.\n\nOpen it now?",
                                         parent=self):
            _open_path(next((p for p in paths if p.endswith(".pdf")), paths[0]))

    def _poll_jobs(self):
        try:
            while True:
                kind, dlg, payload = self._jobs.get_nowait()
                if kind == "progress":
                    dlg.set(payload.strip().split("\n")[0])
                    self.log(payload)
                else:
                    result, done = payload
                    dlg.close()
                    self._busy = False
                    done(result)
        except queue.Empty:
            pass
        self.after(150, self._poll_jobs)

    def preview_report(self):
        import tempfile
        if not self.diag:
            return
        folder = tempfile.mkdtemp(prefix="geoqaqc_")
        paths = self.generate_report(folder, "preview", pdf=False, word=False, wait=True)
        if paths:
            webbrowser.open(paths[0] if paths[0].startswith("http") else
                            "file:///" + paths[0].replace("\\", "/").lstrip("/"))

    # =====================================================================
    #  export and session
    # =====================================================================
    def do_export(self):
        if not self.R:
            messagebox.showinfo(APP_NAME, "Run the analysis first.", parent=self)
            return
        base = os.path.splitext(os.path.basename(self.project.assay.path))[0]
        dlg = ExportDialog(self, default_base=base)
        if not dlg.result:
            return
        folder, b = dlg.result
        try:
            files = export_results(self.project, self.F, self.C, self.S, self.RB, self.diag,
                                   folder, b, log=self.log)
        except Exception as ex:                          # noqa: BLE001
            messagebox.showerror(APP_NAME, f"Export failed:\n{ex}", parent=self)
            return
        self.log(f"Exported {len(files)} file(s) to {folder}.")
        if messagebox.askyesno(APP_NAME, f"{len(files)} file(s) written.\nOpen the folder?",
                               parent=self):
            _open_path(folder)

    def save_session(self):
        if not self.project.assay:
            messagebox.showinfo(APP_NAME, "Nothing to save yet.", parent=self)
            return
        p = filedialog.asksaveasfilename(parent=self, defaultextension=".qaproj",
                                         filetypes=[("GEOQAQC session", "*.qaproj")])
        if p:
            session.save(p, self.project, self.F, self.C, self.S, self.RB, self._meta())
            self.log(f"Session saved to {os.path.basename(p)}")

    def load_session(self):
        p = filedialog.askopenfilename(parent=self, filetypes=[("GEOQAQC session", "*.qaproj"),
                                                               ("All files", "*.*")])
        if not p:
            return
        try:
            out = session.restore(session.load(p), log=self.log)
        except ValueError as ex:
            messagebox.showerror(APP_NAME, str(ex), parent=self)
            return
        self.project, self.F, self.C, self.S, self.RB = (out["project"], out["F"], out["C"],
                                                         out["S"], out["RB"])
        for k, v in self._svars.items():
            v.set(self.S[k])
        for key, v in self._fvars.items():
            v.set(self.F.expr(key))
        for key, vs in self._cvars.items():
            for v, c in zip(vs, self.C[key]["cuts"]):
                v.set(f"{c:g}")
        self._refresh_rule_vars()
        meta = ReportMeta.from_dict(out["meta"])
        for k, v in self.report_vars.items():
            v.set(getattr(meta, k) or "")
        self.R, self.diag = {}, None
        self.set_badge()
        self._sync()
        self.log(f"Session loaded from {os.path.basename(p)}"
                 + (f"; missing files: {', '.join(out['missing'])}" if out["missing"] else ""))


def _open_path(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)                           # noqa: S606
        else:
            webbrowser.open("file://" + os.path.abspath(path))
    except Exception:                                    # noqa: BLE001
        pass


def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:                                    # noqa: BLE001
        pass
    app = App()
    app.mainloop()
