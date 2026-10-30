# -*- coding: utf-8 -*-
"""Import mapping, export and progress dialogs."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .. import APP_NAME
from ..core import SAMPLE_TYPES, classify_type, fnum
from ..model import DataTable, guess_role, looks_numeric
from .theme import BG1


class MappingDialog(tk.Toplevel):
    """Column mapping, sample-type classification and element flagging."""

    ROLES = {
        "assay": [("sampleid", "Sample ID", True), ("type", "Sample Type", False),
                  ("crmid", "CRM code", False), ("parent", "Parent / original ID", False),
                  ("batch", "Batch / job", False), ("lab", "Laboratory", False),
                  ("date", "Date", False), ("order", "Sequence", False),
                  ("holeid", "Hole / trench (optional)", False),
                  ("drilltype", "Drill type (optional)", False),
                  ("from", "From (optional)", False), ("to", "To (optional)", False)],
        "crm": [("crmid", "CRM code", True), ("element", "Element", True),
                ("certified", "Certified value", True),
                ("sd", "Standard deviation", False), ("unit", "Unit", False),
                ("method", "Method", False)],
        "pairs": [("sampleid", "Original sample ID", True),
                  ("dupid", "Duplicate sample ID", True),
                  ("type", "Duplicate type", False)],
        "umpire": [("sampleid", "Sample ID", True), ("lab", "Umpire laboratory",
                                                     False),
                   ("batch", "Batch / job", False), ("date", "Date", False)],
    }
    TITLES = {"assay": "ASSAY / RESULTS TABLE",
              "crm": "CRM CERTIFICATE TABLE",
              "pairs": "DUPLICATE PAIR TABLE",
              "umpire": "CHECK / UMPIRE ASSAY TABLE  (second laboratory)"}

    def __init__(self, master, kind, path, header, rows, delim, suggested=""):
        super().__init__(master)
        self.title(f"{APP_NAME} -- map {kind} columns")
        self.configure(bg=BG1)
        self.transient(master)
        self.grab_set()
        self.kind, self.path, self.header = kind, path, header
        self.rows, self.delim = rows, delim
        self.result = None
        self._role_vars = {}
        self._el_vars = {}
        self._dl_vars = {}
        self._type_vars = {}

        top = ttk.Frame(self, style="Head.TFrame", padding=(14, 10))
        top.pack(fill="x")
        ttk.Label(top, text=self.TITLES[kind], style="Head.TLabel").pack(anchor="w")
        ttk.Label(self, text=f"{os.path.basename(path)}   --   {len(rows)} rows, "
                             f"{len(header)} columns",
                  style="Dim.TLabel").pack(anchor="w", padx=14, pady=(6, 2))

        body = ttk.Frame(self, style="Panel.TFrame", padding=(14, 8))
        body.pack(fill="both", expand=True)

        nf = ttk.Frame(body, style="Panel.TFrame")
        nf.pack(fill="x", pady=(0, 8))
        ttk.Label(nf, text="Table name", style="Sec.TLabel").pack(side="left")
        self.name_var = tk.StringVar(
            value=suggested or os.path.splitext(os.path.basename(path))[0].upper())
        ttk.Entry(nf, textvariable=self.name_var, width=26).pack(side="left", padx=8)

        box = ttk.Labelframe(body, text="  Column mapping  ", padding=10)
        box.pack(fill="x")
        taken = []
        for i, (role, label, req) in enumerate(self.ROLES[kind]):
            g = guess_role(header, role, taken)
            if g:
                taken.append(g)
            v = tk.StringVar(value=g)
            self._role_vars[role] = v
            ttk.Label(box, text=label + (" *" if req else ""),
                      style="Sec.TLabel" if req else "TLabel").grid(
                row=i % 6, column=(i // 6) * 2, sticky="w", pady=3, padx=(0, 8))
            ttk.Combobox(box, textvariable=v, values=[""] + list(header),
                         state="readonly", width=26).grid(
                row=i % 6, column=(i // 6) * 2 + 1, sticky="w", padx=(0, 20))

        if kind == "assay":
            self._build_types(body)
            self._build_elements(body)
        elif kind == "umpire":
            ttk.Label(body, text="Element columns are matched to the primary "
                                 "table by name; a laboratory suffix such as "
                                 "Cu_pct_UM is matched to Cu_pct automatically.",
                      style="Dim.TLabel").pack(anchor="w", pady=(8, 0))
            self._build_elements(body)

        bar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 12))
        bar.pack(fill="x")
        ttk.Label(bar, text="* required", style="Dim.TLabel").pack(side="left")
        ttk.Button(bar, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bar, text="Import", style="Accent.TButton",
                   command=self._ok).pack(side="right")

        self.update_idletasks()
        self.minsize(940, 480)
        self.wait_window(self)

    # -- sample type classification ---------------------------------------
    def _build_types(self, parent):
        box = ttk.Labelframe(parent, text="  Sample types  ", padding=10)
        box.pack(fill="x", pady=8)
        self._type_box = box
        ttk.Label(box, text="Tell GEOQAQC what each code in the sample-type column "
                            "means. The guesses below come from the usual industry "
                            "abbreviations -- correct anything that is wrong.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 6))
        self._type_holder = ttk.Frame(box, style="Panel.TFrame")
        self._type_holder.pack(fill="x")
        self._role_vars["type"].trace_add("write", lambda *_: self._refresh_types())
        self._refresh_types()

    def _refresh_types(self):
        for w in self._type_holder.winfo_children():
            w.destroy()
        self._type_vars = {}
        col = self._role_vars["type"].get()
        if not col or col not in self.header:
            ttk.Label(self._type_holder,
                      text="No sample-type column mapped. Every row will be treated "
                           "as a normal sample unless a CRM code or parent ID "
                           "identifies it.", style="Dim.TLabel").pack(anchor="w")
            return
        i = self.header.index(col)
        codes = []
        for r in self.rows:
            v = str(r[i]).strip() if i < len(r) else ""
            if v and v not in codes:
                codes.append(v)
            if len(codes) > 40:
                break
        counts = {}
        for r in self.rows:
            v = str(r[i]).strip() if i < len(r) else ""
            counts[v] = counts.get(v, 0) + 1
        for n, code in enumerate(sorted(codes)):
            row = ttk.Frame(self._type_holder, style="Panel.TFrame")
            row.grid(row=n % 8, column=(n // 8) * 2, sticky="w", pady=1, padx=(0, 16))
            ttk.Label(row, text=f"{code[:22]:<22} ({counts.get(code, 0)})",
                      style="Mono.TLabel").pack(side="left")
            v = tk.StringVar(value=classify_type(code))
            self._type_vars[code] = v
            ttk.Combobox(row, textvariable=v, values=SAMPLE_TYPES,
                         state="readonly", width=13).pack(side="left", padx=6)

    # -- element flagging --------------------------------------------------
    def _build_elements(self, parent):
        box = ttk.Labelframe(parent, text="  Element columns  ", padding=10)
        box.pack(fill="both", expand=True, pady=(0, 4))
        ttk.Label(box, text="Tick every column that holds an analytical result. "
                            "A detection limit is optional: leave it blank and "
                            "GEOQAQC infers it from the smallest '<' value.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 6))
        bb = ttk.Frame(box, style="Panel.TFrame")
        bb.pack(fill="x", pady=(0, 6))
        ttk.Button(bb, text="Select all numeric", width=18,
                   command=lambda: self._set_all(True)).pack(side="left", padx=2)
        ttk.Button(bb, text="Clear all", width=12,
                   command=lambda: self._set_all(False)).pack(side="left", padx=2)

        canvas = tk.Canvas(box, bg=BG1, highlightthickness=0, height=170)
        sb = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        holder = ttk.Frame(canvas, style="Panel.TFrame")
        holder.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=holder, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        mapped = {v.get() for v in self._role_vars.values() if v.get()}
        n = 0
        for c in self.header:
            if c in mapped:
                continue
            vals = self.col_values(c)
            num = looks_numeric(vals)
            row = ttk.Frame(holder, style="Panel.TFrame")
            row.grid(row=n % 12, column=n // 12, sticky="w", padx=(0, 22), pady=1)
            bv = tk.BooleanVar(value=num)
            self._el_vars[c] = bv
            ttk.Checkbutton(row, text=f"{c[:18]:<18}", variable=bv).pack(side="left")
            dv = tk.StringVar(value="")
            self._dl_vars[c] = dv
            ttk.Label(row, text="DL", style="Dim.TLabel").pack(side="left", padx=(4, 2))
            ttk.Entry(row, textvariable=dv, width=8).pack(side="left")
            n += 1

    def col_values(self, colname):
        if colname not in self.header:
            return []
        i = self.header.index(colname)
        return [r[i] if i < len(r) else "" for r in self.rows]

    def _set_all(self, val):
        for c, v in self._el_vars.items():
            v.set(val and looks_numeric(self.col_values(c)))

    def _ok(self):
        mapping = {}
        for role, label, req in self.ROLES[self.kind]:
            col = self._role_vars[role].get().strip()
            if req and not col:
                messagebox.showwarning(APP_NAME, f"'{label}' must be mapped.",
                                       parent=self)
                return
            if col:
                mapping[role] = col
        t = DataTable(self.kind, self.name_var.get().strip() or self.kind.upper(),
                      self.path, self.header, self.rows, self.delim)
        t.mapping = mapping
        if self.kind == "umpire":
            t.value_cols = [(c, "numeric") for c, v in self._el_vars.items()
                            if v.get()]
            if not t.value_cols:
                messagebox.showwarning(APP_NAME, "Tick at least one element "
                                                 "column.", parent=self)
                return
        if self.kind == "assay":
            t.value_cols = [(c, "numeric") for c, v in self._el_vars.items() if v.get()]
            if not t.value_cols:
                messagebox.showwarning(APP_NAME, "Tick at least one element column.",
                                       parent=self)
                return
            t.type_map = {k: v.get() for k, v in self._type_vars.items()}
            for c, v in self._dl_vars.items():
                d = fnum(v.get())
                if d is not None:
                    t.dl[c] = d
        self.result = t
        self.destroy()


class ExportDialog(tk.Toplevel):
    def __init__(self, master, default_base="qaqc"):
        super().__init__(master)
        self.title(f"{APP_NAME} -- export")
        self.configure(bg=BG1)
        self.transient(master)
        self.grab_set()
        self.result = None
        ttk.Label(self, text="  EXPORT QA/QC RESULTS", style="Head.TLabel").pack(
            fill="x", pady=(10, 8))
        f = ttk.Frame(self, style="Panel.TFrame", padding=(14, 6))
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Folder", style="Sec.TLabel").grid(row=0, column=0, sticky="w")
        self.folder = tk.StringVar(value=os.path.expanduser("~"))
        ttk.Entry(f, textvariable=self.folder, width=52).grid(row=0, column=1, padx=8)
        ttk.Button(f, text="Browse", command=self._browse).grid(row=0, column=2)
        ttk.Label(f, text="File prefix", style="Sec.TLabel").grid(
            row=1, column=0, sticky="w", pady=8)
        self.base = tk.StringVar(value=default_base)
        ttk.Entry(f, textvariable=self.base, width=52).grid(row=1, column=1, padx=8)
        ttk.Label(f, text="The protocol file records every formula, threshold and "
                          "setting used for this run, so the export is reproducible.",
                  style="Dim.TLabel", wraplength=520, justify="left").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))
        bar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 12))
        bar.pack(fill="x")
        ttk.Button(bar, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bar, text="Export", style="Accent.TButton",
                   command=self._ok).pack(side="right")
        self.update_idletasks()
        self.wait_window(self)

    def _browse(self):
        p = filedialog.askdirectory(parent=self)
        if p:
            self.folder.set(p)

    def _ok(self):
        if not os.path.isdir(self.folder.get()):
            messagebox.showwarning(APP_NAME, "Choose a valid folder.", parent=self)
            return
        self.result = (self.folder.get(), self.base.get())
        self.destroy()


class ProgressDialog(tk.Toplevel):
    """A small modal window with an indeterminate bar while the report builds."""

    def __init__(self, master, title, text):
        super().__init__(master)
        self.title(f"{APP_NAME} -- {title}")
        self.configure(bg=BG1)
        self.transient(master)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        f = ttk.Frame(self, style="Panel.TFrame", padding=(22, 18))
        f.pack(fill="both", expand=True)
        self.label = ttk.Label(f, text=text, style="Sec.TLabel")
        self.label.pack(anchor="w")
        self.detail = ttk.Label(f, text="", style="Dim.TLabel", width=60)
        self.detail.pack(anchor="w", pady=(4, 10))
        self.bar = ttk.Progressbar(f, mode="indeterminate", length=380)
        self.bar.pack(fill="x")
        self.bar.start(12)
        self.update_idletasks()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def set(self, text):
        self.detail.configure(text=str(text)[:90])

    def close(self):
        try:
            self.bar.stop()
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
