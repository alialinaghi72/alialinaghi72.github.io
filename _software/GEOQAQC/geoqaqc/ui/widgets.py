# -*- coding: utf-8 -*-
"""Reusable widgets: the chart view, the navigation rail, element cards."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure as MplFigure

from .. import APP_NAME
from ..render import THEMES, draw_figure, to_png, to_svg
from .theme import (ACCENT, BG1, BG2, BG3, C_ERR, C_OK, C_WARN, FG,
                    FG_DIM, MONO, RATING_COLOR, UI, UI_B, UI_H, UI_SMALL,
                    VERDICT_COLOR, VERDICT_EN)


class FigureView(ttk.Frame):
    """A Figure drawn by matplotlib inside Tk: zoom and pan from the toolbar,
    the sample ID of a point under the mouse, and Save as PNG / SVG / PDF in
    the light print theme."""

    def __init__(self, parent, theme="dark"):
        super().__init__(parent, style="Panel.TFrame")
        self.theme = theme
        self.fig = None
        self.hover = {}
        self.mfig = MplFigure(figsize=(7.2, 3.6), dpi=96)
        self.mfig.set_facecolor(THEMES[theme]["bg"])
        self.canvas = FigureCanvasTkAgg(self.mfig, master=self)
        bar = tk.Frame(self, bg=BG1)
        bar.pack(side="bottom", fill="x")
        # matplotlib's own toolbar carries black icons that vanish on the dark
        # theme: keep it for its logic, drive it from themed buttons instead
        self.toolbar = NavigationToolbar2Tk(self.canvas, bar, pack_toolbar=False)
        for text, cmd in (("Reset view", self.toolbar.home), ("Pan", self.toolbar.pan),
                          ("Zoom", self.toolbar.zoom)):
            ttk.Button(bar, text=text, style="Ghost.TButton", command=cmd).pack(
                side="left", padx=(4, 0))
        ttk.Button(bar, text="Save chart", style="Ghost.TButton",
                   command=self.save).pack(side="right", padx=4)
        self.tip = tk.Label(bar, text="", bg=BG1, fg=ACCENT, font=MONO)
        self.tip.pack(side="right", padx=10)
        self.canvas.get_tk_widget().configure(bg=THEMES[theme]["bg"], highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._motion)
        self._resize_job = None
        self.canvas.get_tk_widget().bind("<Configure>", self._on_resize, add="+")

    def show(self, fig):
        self.fig = fig
        self._draw()

    def clear(self, message=""):
        from ..figures import Figure
        f = Figure(message or " ")
        if message:
            f.note(message)
        self.show(f)

    def _draw(self):
        if self.fig is None:
            return
        self.hover = draw_figure(self.fig, self.mfig, self.theme)
        self.canvas.draw_idle()

    def _on_resize(self, _e):
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._draw)

    def _motion(self, ev):
        if not self.hover or ev.inaxes is None:
            self.tip.configure(text="")
            return
        for art, ids in self.hover.items():
            ok, info = art.contains(ev)
            if ok and info.get("ind") is not None and len(info["ind"]):
                i = int(info["ind"][0])
                if 0 <= i < len(ids):
                    self.tip.configure(text=f"{ids[i]}")
                    return
        self.tip.configure(text="")

    def save(self):
        if self.fig is None:
            return
        p = filedialog.asksaveasfilename(
            parent=self, defaultextension=".png", title="Save the chart",
            filetypes=[("PNG image (300 dpi)", "*.png"), ("SVG vector", "*.svg"),
                       ("PDF vector", "*.pdf")])
        if not p:
            return
        try:
            low = p.lower()
            if low.endswith(".svg"):
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(to_svg(self.fig, "light"))
            elif low.endswith(".pdf"):
                mf = MplFigure(figsize=self.fig.size or (7.2, 3.6))
                from matplotlib.backends.backend_agg import FigureCanvasAgg
                FigureCanvasAgg(mf)
                draw_figure(self.fig, mf, "light")
                mf.savefig(p, format="pdf", facecolor=THEMES["light"]["bg"])
            else:
                with open(p, "wb") as fh:
                    fh.write(to_png(self.fig, "light", dpi=300))
        except Exception as ex:                           # noqa: BLE001
            messagebox.showerror(APP_NAME, f"Could not save the chart:\n{ex}", parent=self)


class NavRail(tk.Frame):
    """Grouped page list on the left: OVERVIEW, METHODS, PROTOCOL, OUTPUT."""

    def __init__(self, parent, groups, on_select):
        super().__init__(parent, bg=BG1)
        self.on_select = on_select
        self.items = {}
        self.current = None
        for group, names in groups:
            tk.Label(self, text=group, bg=BG1, fg=FG_DIM, font=UI_SMALL, anchor="w",
                     padx=14, pady=4).pack(fill="x", pady=(10, 0))
            for name in names:
                row = tk.Frame(self, bg=BG1, cursor="hand2")
                row.pack(fill="x")
                bar = tk.Frame(row, bg=BG1, width=3)
                bar.pack(side="left", fill="y")
                lab = tk.Label(row, text=name, bg=BG1, fg=FG, font=UI, anchor="w",
                               padx=14, pady=5)
                lab.pack(side="left", fill="x", expand=True)
                dot = tk.Label(row, text="", bg=BG1, fg=FG_DIM, font=UI_SMALL, padx=10)
                dot.pack(side="right")
                self.items[name] = (row, bar, lab, dot)
                for w in (row, lab, dot):
                    w.bind("<Button-1>", lambda e, n=name: self.on_select(n))
                    w.bind("<Enter>", lambda e, n=name: self._hover(n, True))
                    w.bind("<Leave>", lambda e, n=name: self._hover(n, False))

    def _paint(self, name, bg):
        row, bar, lab, dot = self.items[name]
        for w in (row, lab, dot):
            w.configure(bg=bg)

    def _hover(self, name, on):
        if name != self.current:
            self._paint(name, BG3 if on else BG1)

    def select(self, name):
        if self.current in self.items:
            self._paint(self.current, BG1)
            self.items[self.current][1].configure(bg=BG1)
            self.items[self.current][2].configure(fg=FG, font=UI)
        self.current = name
        self._paint(name, BG2)
        self.items[name][1].configure(bg=ACCENT)
        self.items[name][2].configure(fg=ACCENT, font=UI_B)

    def badge(self, name, text, color=FG_DIM):
        if name in self.items:
            self.items[name][3].configure(text=text, fg=color)


class KpiCard(tk.Frame):
    """One element: name, verdict, finding counts, worst rating."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG2, highlightthickness=1, highlightbackground=BG3)
        self.stripe = tk.Frame(self, bg=BG3, height=4)
        self.stripe.pack(fill="x")
        body = tk.Frame(self, bg=BG2, padx=14, pady=10)
        body.pack(fill="both", expand=True)
        self.name = tk.Label(body, text="", bg=BG2, fg=FG, font=UI_H, anchor="w")
        self.name.pack(fill="x")
        self.verdict = tk.Label(body, text="", bg=BG2, fg=FG_DIM, font=UI_B, anchor="w")
        self.verdict.pack(fill="x", pady=(4, 2))
        self.counts = tk.Label(body, text="", bg=BG2, fg=FG_DIM, font=MONO, anchor="w")
        self.counts.pack(fill="x")
        self.rating = tk.Label(body, text="", bg=BG2, fg=FG_DIM, font=UI_SMALL, anchor="w")
        self.rating.pack(fill="x", pady=(4, 0))

    def set(self, element, verdict, counts, worst_rating=None):
        col = VERDICT_COLOR.get(verdict, FG_DIM)
        self.stripe.configure(bg=col)
        self.name.configure(text=element)
        self.verdict.configure(text=VERDICT_EN.get(verdict, verdict), fg=col)
        self.counts.configure(
            text=f"critical {counts['CRITICAL']}   material {counts['MATERIAL']}   "
                 f"minor {counts['MINOR']}")
        if worst_rating:
            self.rating.configure(text=f"worst method rating: {worst_rating}",
                                  fg=RATING_COLOR.get(worst_rating, FG_DIM))


class ScrollFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.canvas = tk.Canvas(self, bg=BG1, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, style="Panel.TFrame")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all(
            "<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _wheel(self, e):
        self.canvas.yview_scroll(int(-e.delta / 120) or (-1 if e.delta > 0 else 1), "units")


def make_grid(parent, cols, widths, height=None):
    """A dark Treeview with scrollbars and the rating / status colour tags."""
    holder = ttk.Frame(parent)
    holder.pack(fill="both", expand=True)
    kw = {"height": height} if height else {}
    tv = ttk.Treeview(holder, columns=cols, show="headings", **kw)
    for c, w in zip(cols, widths):
        tv.heading(c, text=c)
        tv.column(c, width=w, anchor="w")
    vs = ttk.Scrollbar(holder, orient="vertical", command=tv.yview)
    hs = ttk.Scrollbar(holder, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
    tv.grid(row=0, column=0, sticky="nsew")
    vs.grid(row=0, column=1, sticky="ns")
    hs.grid(row=1, column=0, sticky="ew")
    holder.rowconfigure(0, weight=1)
    holder.columnconfigure(0, weight=1)
    for r, c in RATING_COLOR.items():
        tv.tag_configure(r, foreground=c)
    for tag, c in (("FAIL", C_ERR), ("WARN", C_WARN), ("OK", C_OK), ("PASS", C_OK),
                   ("ERROR", C_ERR), ("WARNING", C_WARN), ("CRITICAL", C_ERR),
                   ("MATERIAL", "#e08a4a"), ("MINOR", C_WARN),
                   ("SUITABLE", VERDICT_COLOR["SUITABLE"]),
                   ("RESTRICTED", VERDICT_COLOR["RESTRICTED"]),
                   ("REMEDIATE", VERDICT_COLOR["REMEDIATE"])):
        tv.tag_configure(tag, foreground=c)

    return tv


def fill(tv, rows, tags=None):
    tv.delete(*tv.get_children())
    for i, r in enumerate(rows):
        tv.insert("", "end", values=r, tags=((tags[i],) if tags and tags[i] else ()))
