# -*- coding: utf-8 -*-
"""Exclusion review window (R24): decide, pair by pair, which low-grade and
outlier duplicate pairs stay out of the precision statistics, and why."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .. import APP_NAME
from ..exclusions import REASONS, record
from ..figures import Figure
from .theme import BG1
from .widgets import FigureView, make_grid

COLS = ("Element", "Class", "Original", "Duplicate", "Original value", "Duplicate value",
        "Pair mean", "HARD %", "Ratio", "Trigger", "Seq / batch", "Decision", "Reason")
WIDTHS = (80, 100, 120, 120, 95, 95, 90, 70, 60, 80, 110, 80, 260)


def _f(v, d=6):
    if v is None:
        return ""
    return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.{d}g}"


class ReviewDialog(tk.Toplevel):
    """rows: exclusions.review_rows() of the last run; dup_all: the duplicate
    records with every outlier kept (for the max-min plot). On 'Apply', each
    shown decision is stored in project.pair_decisions and self.applied is
    True."""

    def __init__(self, master, project, rows, dup_all, only_pending=True):
        super().__init__(master)
        self.title(f"{APP_NAME} -- review of excluded duplicate pairs")
        self.configure(bg=BG1)
        self.transient(master)
        self.geometry("1360x860")
        self.project, self.dup_all = project, dup_all
        self.rows = [dict(r) for r in rows]
        self.applied = False
        self.show_all = tk.BooleanVar(value=not only_pending)
        self._build()
        self._fill()
        self.grab_set()

    # -- layout -----------------------------------------------------------------
    def _build(self):
        top = ttk.Frame(self, padding=(12, 10, 12, 4))
        top.pack(fill="x")
        ttk.Label(top, text="Pairs that meet a trigger. Decide for each one; every excluded "
                            "outlier needs a reason. Exclusions only take a pair out of the "
                            "statistics -- no data are deleted or changed.",
                  style="Dim.TLabel", wraplength=1250).pack(anchor="w")
        bar = ttk.Frame(self, padding=(12, 4))
        bar.pack(fill="x")
        self.f_el = self._filter(bar, "Element")
        self.f_cls = self._filter(bar, "Class")
        self.f_trg = self._filter(bar, "Trigger")
        ttk.Checkbutton(bar, text="Show decided pairs too", variable=self.show_all,
                        command=self._fill).pack(side="left", padx=10)
        bar2 = ttk.Frame(self, padding=(12, 4))
        bar2.pack(fill="x")
        ttk.Label(bar2, text="Reason", style="Sec.TLabel").pack(side="left")
        self.reason = tk.StringVar(value=REASONS[1])
        ttk.Combobox(bar2, textvariable=self.reason, values=REASONS, state="readonly",
                     width=38).pack(side="left", padx=6)
        ttk.Label(bar2, text="Note (for 'other')", style="Sec.TLabel").pack(side="left")
        self.note = tk.StringVar()
        ttk.Entry(bar2, textvariable=self.note, width=18).pack(side="left", padx=6)
        for text, cmd in (("Exclude selected", lambda: self._set("exclude", True)),
                          ("Keep selected", lambda: self._set("keep", True)),
                          ("Exclude all shown", lambda: self._set("exclude", False)),
                          ("Keep all shown", lambda: self._set("keep", False))):
            ttk.Button(bar2, text=text, command=cmd).pack(side="left", padx=3)
        bot = ttk.Frame(self, padding=(12, 6))
        bot.pack(side="bottom", fill="x")
        self.count = ttk.Label(bot, text="", style="Dim.TLabel")
        self.count.pack(side="left")
        ttk.Button(bot, text="Apply and run the analysis", style="Accent.TButton",
                   command=self._apply).pack(side="right")
        ttk.Button(bot, text="Cancel", command=self.destroy).pack(side="right", padx=8)
        mid = ttk.Panedwindow(self, orient="vertical")
        mid.pack(fill="both", expand=True, padx=12, pady=6)
        holder = ttk.Frame(mid)
        self.tree = make_grid(holder, COLS, WIDTHS, height=14)
        self.tree.configure(selectmode="extended")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._plot())
        mid.add(holder, weight=3)
        self.view = FigureView(mid)
        mid.add(self.view, weight=2)

    def _filter(self, bar, label):
        ttk.Label(bar, text=label, style="Sec.TLabel").pack(side="left", padx=(0, 4))
        v = tk.StringVar(value="All")
        key = {"Element": "element", "Class": "dtype", "Trigger": "trigger"}[label]
        vals = ["All"] + sorted({r[key] for r in self.rows})
        cb = ttk.Combobox(bar, textvariable=v, values=vals, state="readonly", width=16)
        cb.pack(side="left", padx=(0, 14))
        cb.bind("<<ComboboxSelected>>", lambda e: self._fill())
        return v

    # -- content ----------------------------------------------------------------
    def _shown(self):
        out = []
        for i, r in enumerate(self.rows):
            if not self.show_all.get() and not r.get("pending") and r.get("source") != "edited":
                continue
            if self.f_el.get() not in ("All", r["element"]):
                continue
            if self.f_cls.get() not in ("All", r["dtype"]):
                continue
            if self.f_trg.get() not in ("All", r["trigger"]):
                continue
            out.append(i)
        return out

    def _fill(self):
        self.tree.delete(*self.tree.get_children())
        for i in self._shown():
            r = self.rows[i]
            seq = f"{r['order'] if r.get('order') is not None else ''} / {r.get('batch') or ''}"
            self.tree.insert("", "end", iid=str(i), values=(
                r["element"], r["dtype"], r["orig"], r["dup"], _f(r["a"]), _f(r["b"]),
                _f(r["mean"]), _f(r["hard"], 3), _f(r["ratio"], 3), r["trigger"], seq,
                r["decision"] + (" (pre-set)" if r.get("pending") else ""),
                r.get("reason", "") + (f": {r['note']}" if r.get("note") else "")),
                tags=("FAIL" if r["decision"] == "exclude" else "OK",))
        n_p = sum(1 for r in self.rows if r.get("pending"))
        self.count.configure(text=f"{len(self._shown())} shown, {n_p} still undecided, "
                                  f"{len(self.rows)} in total")
        self._plot()

    def _set(self, decision, selected_only):
        idx = ([int(x) for x in self.tree.selection()] if selected_only
               else self._shown())
        if not idx:
            return
        reason, note = self.reason.get(), self.note.get().strip()
        if decision == "exclude" and reason == REASONS[3] and not note:
            messagebox.showwarning(APP_NAME, "Write the reason in the note for 'other'.",
                                   parent=self)
            return
        for i in idx:
            r = self.rows[i]
            r["decision"] = decision
            r["pending"] = False
            r["source"] = "edited"
            if decision == "exclude":
                r["reason"] = (r.get("reason") or "pair mean below the minimum grade") \
                    if r["trigger"] == "low-grade" else reason
                r["note"] = note if r["trigger"] != "low-grade" else ""
            else:
                r["reason"], r["note"] = "", ""
        self._fill()

    def _plot(self):
        sel = [self.rows[int(x)] for x in self.tree.selection()]
        ref = sel[0] if sel else (self.rows[self._shown()[0]] if self._shown() else None)
        if ref is None:
            self.view.clear("No pair shown.")
            return
        rec = self.dup_all.get((ref["dtype"], ref["element"]))
        f = Figure(f"Max-Min plot · {ref['dtype']} · {ref['element']}",
                   "Larger against smaller value of each pair; selected pairs highlighted",
                   "smaller value of the pair", "larger value of the pair")
        f.xlog = f.ylog = True
        pts = [(min(r["a"], r["b"]), max(r["a"], r["b"]), r["dup"])
               for r in (rec["rows"] if rec else []) if r["a"] > 0 and r["b"] > 0]
        cand = [r for r in self.rows if r["dtype"] == ref["dtype"]
                and r["element"] == ref["element"] and r["a"] > 0 and r["b"] > 0]
        pts += [(min(r["a"], r["b"]), max(r["a"], r["b"]), r["dup"]) for r in cand
                if r["trigger"] == "low-grade" or r["decision"] == "exclude"]
        if pts:
            lo = min(p[0] for p in pts)
            hi = max(p[1] for p in pts)
            f.line([lo, hi], [lo, hi], "fg", 1.2, None, "1:1")
            f.points([p[0] for p in pts], [p[1] for p in pts], "s1", 3.0, "pairs",
                     ids=[p[2] for p in pts])
        ex = [r for r in cand if r["decision"] == "exclude"]
        if ex:
            f.points([min(r["a"], r["b"]) for r in ex], [max(r["a"], r["b"]) for r in ex],
                     "muted", 4.0, "excluded", "x", ids=[r["dup"] for r in ex])
        if sel:
            f.points([min(r["a"], r["b"]) for r in sel], [max(r["a"], r["b"]) for r in sel],
                     "crit", 6.0, "selected", "s", ids=[r["dup"] for r in sel])
        self.view.show(f)

    def _apply(self):
        bad = [r for r in self.rows if r["decision"] == "exclude"
               and r["trigger"] != "low-grade" and not r.get("reason")]
        if bad:
            messagebox.showwarning(APP_NAME, f"{len(bad)} excluded outlier(s) have no "
                                             f"reason.", parent=self)
            return
        for r in self.rows:
            if r.get("source") == "edited" or (r.get("pending") and r["action"] == "ask"):
                record(self.project, r, r["decision"], r.get("reason", ""),
                       r.get("note", ""))
        self.applied = True
        self.destroy()
