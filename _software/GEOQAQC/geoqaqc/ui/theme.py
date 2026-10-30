# -*- coding: utf-8 -*-
"""Application theme: the GEOVALID navy-and-amber family of 1.1, refined for
2.0 (navigation rail, cards, status pills)."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

from ..core import R_BAD, R_EXC, R_GOOD, R_NA, R_POOR, R_VBAD, R_VG

BG0 = "#0e131a"     # window
BG1 = "#151c25"     # panels
BG2 = "#1c2531"     # fields, table rows
BG3 = "#283444"     # borders, buttons
BG4 = "#33435a"     # hover
FG = "#dce4ee"
FG_DIM = "#8a98aa"
ACCENT = "#d99a3e"
ACCENT_D = "#a8752c"
C_OK = "#4fae7f"
C_WARN = "#e0b342"
C_ERR = "#e0605c"
C_INFO = "#5a9fd4"
C_SER = "#e08a4a"
C_PLOT = "#7cc0f0"

_SANS = "Segoe UI" if sys.platform.startswith("win") else "DejaVu Sans"
_MONO = "Consolas" if sys.platform.startswith("win") else "DejaVu Sans Mono"
MONO = (_MONO, 9)
MONO_B = (_MONO, 9, "bold")
UI = (_SANS, 9)
UI_B = (_SANS, 9, "bold")
UI_H = (_SANS, 11, "bold")
UI_BIG = (_SANS, 18, "bold")
UI_TITLE = (_SANS, 17)
UI_SMALL = (_SANS, 8)

RATING_COLOR = {R_EXC: "#3fbf8f", R_VG: "#4fae7f", R_GOOD: "#9ec46a",
                R_POOR: C_WARN, R_BAD: C_SER, R_VBAD: C_ERR, R_NA: FG_DIM}
SEVERITY_COLOR = {"CRITICAL": C_ERR, "MATERIAL": C_SER, "MINOR": C_WARN}
VERDICT_COLOR = {"SUITABLE": C_OK, "RESTRICTED": C_WARN, "REMEDIATE": C_ERR}
VERDICT_EN = {"SUITABLE": "Suitable for estimation", "RESTRICTED": "Usable with restrictions",
              "REMEDIATE": "Remediate before use"}


def apply_theme(root):
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    root.configure(bg=BG0)
    st.configure(".", background=BG1, foreground=FG, font=UI,
                 fieldbackground=BG2, bordercolor=BG3, focuscolor=ACCENT)
    st.configure("TFrame", background=BG1)
    st.configure("Dark.TFrame", background=BG0)
    st.configure("Panel.TFrame", background=BG1)
    st.configure("Head.TFrame", background=BG2)
    st.configure("TLabel", background=BG1, foreground=FG)
    st.configure("Dim.TLabel", background=BG1, foreground=FG_DIM)
    st.configure("Head.TLabel", background=BG2, foreground=ACCENT, font=UI_H)
    st.configure("Sec.TLabel", background=BG1, foreground=ACCENT, font=UI_B)
    st.configure("Mono.TLabel", background=BG1, foreground=FG, font=MONO)
    st.configure("TButton", background=BG3, foreground=FG, borderwidth=0,
                 focusthickness=0, padding=(12, 6))
    st.map("TButton", background=[("active", "#35455a"), ("disabled", BG2)],
           foreground=[("disabled", FG_DIM)])
    st.configure("Accent.TButton", background=ACCENT_D, foreground="#12161c",
                 font=UI_B, padding=(14, 7))
    st.map("Accent.TButton", background=[("active", ACCENT), ("disabled", BG3)],
           foreground=[("disabled", FG_DIM)])
    st.configure("Step.TButton", background=BG2, foreground=FG, padding=(10, 9),
                 anchor="w")
    st.map("Step.TButton", background=[("active", BG3)])
    st.configure("TEntry", fieldbackground=BG2, foreground=FG, insertcolor=ACCENT,
                 bordercolor=BG3, lightcolor=BG3, darkcolor=BG3)
    st.configure("TCombobox", fieldbackground=BG2, background=BG3, foreground=FG,
                 arrowcolor=ACCENT, bordercolor=BG3)
    st.map("TCombobox", fieldbackground=[("readonly", BG2)],
           foreground=[("readonly", FG)])
    st.configure("TCheckbutton", background=BG1, foreground=FG)
    st.map("TCheckbutton", background=[("active", BG1)])
    st.configure("TNotebook", background=BG0, borderwidth=0, tabmargins=(2, 4, 2, 0))
    st.configure("TNotebook.Tab", background=BG1, foreground=FG_DIM,
                 padding=(7, 7), borderwidth=0, font=UI)
    st.map("TNotebook.Tab", background=[("selected", BG2)],
           foreground=[("selected", ACCENT)], font=[("selected", UI_B)])
    st.configure("Treeview", background=BG2, fieldbackground=BG2, foreground=FG,
                 rowheight=21, borderwidth=0, font=MONO)
    st.configure("Treeview.Heading", background=BG3, foreground=ACCENT,
                 font=UI_B, relief="flat", padding=(6, 5))
    st.map("Treeview.Heading", background=[("active", "#35455a")])
    st.map("Treeview", background=[("selected", "#3c5a78")],
           foreground=[("selected", "#ffffff")])
    st.configure("TSeparator", background=BG3)
    st.configure("Vertical.TScrollbar", background=BG3, troughcolor=BG1,
                 arrowcolor=FG_DIM, bordercolor=BG1)
    st.configure("Horizontal.TScrollbar", background=BG3, troughcolor=BG1,
                 arrowcolor=FG_DIM, bordercolor=BG1)
    st.configure("TLabelframe", background=BG1, foreground=ACCENT, bordercolor=BG3)
    st.configure("TLabelframe.Label", background=BG1, foreground=ACCENT, font=UI_B)
    return st


def draw_logo(canvas, w=44, h=44):
    """Control chart mark: a centre line with points scattering around it."""
    canvas.delete("all")
    canvas.configure(bg=BG0, highlightthickness=0)
    x0, x1 = 5, w - 5
    mid = h / 2
    canvas.create_line(x0, mid - (h * 0.26), x1, mid - (h * 0.26),
                       fill=C_ERR, width=1, dash=(2, 2))
    canvas.create_line(x0, mid + (h * 0.26), x1, mid + (h * 0.26),
                       fill=C_ERR, width=1, dash=(2, 2))
    canvas.create_line(x0, mid, x1, mid, fill=ACCENT, width=2)
    pts = [0.10, -0.14, 0.05, 0.19, -0.08, 0.30, -0.05]
    n = len(pts)
    for i, dy in enumerate(pts):
        px = x0 + (x1 - x0) * i / (n - 1)
        py = mid + dy * h
        col = C_ERR if abs(dy) > 0.26 else (C_WARN if abs(dy) > 0.17 else C_PLOT)
        canvas.create_oval(px - 2.2, py - 2.2, px + 2.2, py + 2.2,
                           fill=col, outline="")


def extend_theme(st):
    """2.0 additions on top of the 1.1 styles."""
    st.configure("Card.TFrame", background=BG2)
    st.configure("Rail.TFrame", background=BG1)
    st.configure("Big.TLabel", background=BG1, foreground=FG, font=UI_BIG)
    st.configure("Card.TLabel", background=BG2, foreground=FG)
    st.configure("CardDim.TLabel", background=BG2, foreground=FG_DIM, font=UI_SMALL)
    st.configure("Ghost.TButton", background=BG1, foreground=FG_DIM, padding=(8, 5))
    st.map("Ghost.TButton", background=[("active", BG3)], foreground=[("active", FG)])
    st.configure("Treeview", rowheight=22)
    st.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=BG2,
                 bordercolor=BG2, lightcolor=ACCENT, darkcolor=ACCENT_D)
    # pages are switched by the navigation rail: hide the notebook tabs
    st.layout("Hidden.TNotebook.Tab", [])
    st.configure("Hidden.TNotebook", background=BG0, borderwidth=0, tabmargins=0)
    return st
