"""Visual identity of the desktop app: two themes (Obsidian dark, Ivory light) as Qt style sheets, and vector icons."""
from __future__ import annotations

import re

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap

TOKENS = {
    "obsidian": dict(bg="#0F141A", side="#121820", hdr1="#121820", hdr2="#1B2431", card="#18202A", alt="#1B2430", head="#1D2631",
                     field="#141B23", line="#283241", hover="#1E2733", sel="rgba(212,168,90,0.20)", ink="#E6E0D4", ink_strong="#FBF7EF",
                     muted="#9AA3AE", gold="#D4A85A", gold_hi="#E9C989", gold_lo="#B07D3A", gold_dim="#5A4728", on_gold="#17120A",
                     btn="#1C2530", scroll="#334150"),
    "ivory": dict(bg="#F3F0E9", side="#FBF9F4", hdr1="#FFFFFF", hdr2="#F6EFE1", card="#FFFFFF", alt="#FAF8F3", head="#F6F2E9",
                  field="#FFFFFF", line="#E3DDD1", hover="#F1ECE1", sel="rgba(176,125,58,0.16)", ink="#1E2A32", ink_strong="#10181E",
                  muted="#6B747C", gold="#9C6B2A", gold_hi="#D9B06A", gold_lo="#A8742F", gold_dim="#E5D6B8", on_gold="#FFFFFF",
                  btn="#FFFFFF", scroll="#CFC8BA"),
}

QSS = """
QMainWindow, QWidget#Root, QDialog { background: @bg; }
QWidget { color: @ink; }
QFrame#Header { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @hdr1, stop:1 @hdr2); border-bottom: 1px solid @gold_dim; }
QLabel#Brand { color: @gold; font-weight: 700; letter-spacing: 3px; }
QLabel#Title { color: @ink_strong; font-weight: 600; }
QLabel#Muted, QLabel#Sub { color: @muted; }
QFrame#Sidebar { background: @side; }
QFrame#VLine { background: @line; max-width: 1px; min-width: 1px; }
QPushButton#Nav { text-align: left; padding: 9px 14px; border: none; border-radius: 10px; color: @muted; background: transparent; }
QPushButton#Nav:hover { background: @hover; color: @ink; }
QPushButton#Nav:checked { background: @sel; color: @gold; font-weight: 600; }
QPushButton#Side { text-align: left; padding: 7px 12px; border: 1px solid @line; border-radius: 9px; color: @ink; background: transparent; }
QPushButton#Side:hover { border-color: @gold; color: @gold; }
QFrame#Card { background: @card; border: 1px solid @line; border-radius: 14px; }
QLabel#KpiName { color: @muted; }
QLabel#KpiValue { color: @ink_strong; font-weight: 700; }
QLabel#H1 { color: @ink_strong; font-weight: 700; }
QLabel#H2 { color: @gold; font-weight: 600; }
QPushButton { background: @btn; border: 1px solid @line; border-radius: 9px; padding: 7px 14px; color: @ink; }
QPushButton:hover { border-color: @gold; }
QPushButton:pressed { background: @sel; }
QPushButton:disabled { color: @muted; }
QPushButton#Primary { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 @gold_hi, stop:1 @gold_lo); color: @on_gold;
                      border: none; font-weight: 700; padding: 12px; }
QPushButton#Primary:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 @gold_hi, stop:1 @gold); }
QPushButton#Primary:disabled { background: @line; color: @muted; }
QPushButton#Chip { border-radius: 14px; padding: 4px 12px; }
QLineEdit, QComboBox, QDoubleSpinBox { background: @field; border: 1px solid @line; border-radius: 8px; padding: 5px 8px;
                                       selection-background-color: @gold_lo; selection-color: @on_gold; }
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus { border-color: @gold; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background: @card; border: 1px solid @line; selection-background-color: @sel; selection-color: @ink_strong;
                              outline: 0; padding: 4px; }
QTableView, QTableWidget, QListWidget, QTextBrowser, QPlainTextEdit { background: @card; alternate-background-color: @alt;
    border: 1px solid @line; border-radius: 12px; gridline-color: @line; selection-background-color: @sel; selection-color: @ink_strong; }
QTableView::item, QTableWidget::item { padding: 2px 6px; }
QHeaderView { background: transparent; }
QHeaderView::section { background: @head; color: @muted; border: none; border-bottom: 1px solid @line; padding: 6px 8px; font-weight: 600; }
QTableCornerButton::section { background: @head; border: none; }
QProgressBar { background: @field; border: 1px solid @line; border-radius: 6px; max-height: 10px; text-align: center; color: transparent; }
QProgressBar::chunk { border-radius: 5px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @gold_lo, stop:1 @gold_hi); }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: @scroll; border-radius: 4px; min-height: 30px; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: @scroll; border-radius: 4px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page { background: none; height: 0; width: 0; }
QStatusBar { background: @side; color: @muted; border-top: 1px solid @line; }
QStatusBar QLabel { color: @muted; }
QToolTip { background: @card; color: @ink; border: 1px solid @gold; padding: 6px; border-radius: 6px; }
QCheckBox::indicator { width: 15px; height: 15px; border-radius: 4px; border: 1px solid @muted; background: @field; }
QCheckBox::indicator:checked { background: @gold; border-color: @gold; }
QSplitter::handle { background: transparent; }
QListWidget#ChartList { padding: 6px; }
QListWidget#ChartList::item { padding: 6px 10px; border-radius: 8px; }
QListWidget#ChartList::item:selected { background: @sel; color: @gold; }
QListWidget#ChartList::item:hover { background: @hover; }
QToolBar { background: transparent; border: none; spacing: 2px; }
QToolButton { background: transparent; border: none; border-radius: 6px; padding: 3px; }
QToolButton:hover { background: @hover; }
QMessageBox QLabel { color: @ink; }
"""


def qss(theme: str) -> str:
    tok = TOKENS[theme]
    return re.sub(r"@([a-z_]+)", lambda m: tok.get(m.group(1), m.group(0)), QSS)


def colour(theme: str, key: str) -> str:
    return TOKENS[theme][key]


# ------------------------------------------------------------------ icons (drawn, so they stay crisp and on-theme)
def _pen(c, w=3.2):
    p = QPen(QColor(c), w)
    p.setCapStyle(Qt.RoundCap)
    p.setJoinStyle(Qt.RoundJoin)
    return p


def _draw(kind: str, c: str, p: QPainter):
    p.setPen(_pen(c))
    p.setBrush(Qt.NoBrush)
    if kind == "data":          # database cylinders
        for y in (10, 22, 34):
            p.drawEllipse(QRectF(10, y - 4, 28, 9))
        p.drawLine(10, 10, 10, 38)
        p.drawLine(38, 10, 38, 38)
    elif kind == "dash":        # four tiles
        for x, y, w, h in ((8, 8, 14, 18), (26, 8, 14, 10), (26, 22, 14, 18), (8, 30, 14, 10)):
            p.drawRoundedRect(QRectF(x, y, w, h), 3, 3)
    elif kind == "issues":      # warning triangle
        path = QPainterPath(QPointF(24, 7))
        path.lineTo(42, 39)
        path.lineTo(6, 39)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(24, 18, 24, 28)
        p.drawPoint(24, 34)
    elif kind == "geo":         # strata with a drill hole
        for y, a in ((14, 4), (24, -4), (34, 3)):
            path = QPainterPath(QPointF(6, y))
            path.cubicTo(16, y - a, 30, y + a, 42, y)
            p.drawPath(path)
        p.setPen(_pen(c, 2.4))
        p.drawLine(30, 4, 22, 44)
    elif kind == "chart":       # bars
        for i, h in enumerate((14, 26, 20, 32)):
            p.drawLine(10 + i * 9, 40, 10 + i * 9, 40 - h)
    elif kind == "rules":       # checklist
        for i, y in enumerate((12, 24, 36)):
            p.drawLine(10, y, 13, y + 3)
            p.drawLine(13, y + 3, 18, y - 3)
            p.drawLine(23, y, 40, y)
    elif kind == "log":         # terminal
        p.drawRoundedRect(QRectF(6, 9, 36, 30), 4, 4)
        p.drawLine(12, 18, 18, 24)
        p.drawLine(18, 24, 12, 30)
        p.drawLine(22, 31, 32, 31)
    elif kind == "report":      # document
        path = QPainterPath(QPointF(12, 6))
        path.lineTo(30, 6)
        path.lineTo(38, 14)
        path.lineTo(38, 42)
        path.lineTo(12, 42)
        path.closeSubpath()
        p.drawPath(path)
        for y in (20, 27, 34):
            p.drawLine(18, y, 32, y)
    elif kind == "folder":
        path = QPainterPath(QPointF(6, 14))
        path.lineTo(18, 14)
        path.lineTo(22, 18)
        path.lineTo(42, 18)
        path.lineTo(42, 38)
        path.lineTo(6, 38)
        path.closeSubpath()
        p.drawPath(path)
    elif kind == "sliders":
        for y, x in ((14, 30), (24, 16), (34, 26)):
            p.drawLine(8, y, 40, y)
            p.setBrush(QColor(c))
            p.drawEllipse(QPointF(x, y), 3.5, 3.5)
            p.setBrush(Qt.NoBrush)
    elif kind == "run":         # play
        path = QPainterPath(QPointF(16, 10))
        path.lineTo(38, 24)
        path.lineTo(16, 38)
        path.closeSubpath()
        p.setBrush(QColor(c))
        p.drawPath(path)
    elif kind == "add":
        p.drawLine(24, 10, 24, 38)
        p.drawLine(10, 24, 38, 24)
    elif kind == "sample":      # flask
        path = QPainterPath(QPointF(19, 6))
        path.lineTo(19, 18)
        path.lineTo(9, 38)
        path.lineTo(39, 38)
        path.lineTo(29, 18)
        path.lineTo(29, 6)
        p.drawPath(path)
        p.drawLine(15, 6, 33, 6)
    elif kind == "theme":       # half-moon
        p.drawEllipse(QRectF(9, 9, 30, 30))
        p.setBrush(QColor(c))
        path = QPainterPath()
        path.moveTo(24, 9)
        path.arcTo(QRectF(9, 9, 30, 30), 90, -180)
        path.closeSubpath()
        p.drawPath(path)
    elif kind == "lang":
        f = QFont()
        f.setPixelSize(22)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, 0, 48, 48), Qt.AlignCenter, "A|ع")
    elif kind == "info":
        p.drawEllipse(QRectF(8, 8, 32, 32))
        p.drawLine(24, 22, 24, 32)
        p.drawPoint(24, 16)


def icon(kind: str, normal: str, active: str | None = None) -> QIcon:
    ic = QIcon()
    for state, c in ((QIcon.Off, normal), (QIcon.On, active or normal)):
        pm = QPixmap(96, 96)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(2, 2)
        _draw(kind, c, p)
        p.end()
        ic.addPixmap(pm, QIcon.Normal, state)
        ic.addPixmap(pm, QIcon.Active, state)
    return ic


def brand_pixmap(size: int = 30) -> QPixmap:
    """Gold gradient tile with a stylised drill trace: the app mark."""
    from PySide6.QtGui import QLinearGradient
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, size * 2, size * 2)
    g.setColorAt(0, QColor("#EBCB8B"))
    g.setColorAt(1, QColor("#A8742F"))
    p.setBrush(g)
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(0, 0, size * 2, size * 2), size * 0.45, size * 0.45)
    p.setPen(_pen("#17120A", size * 0.16))
    s = size * 2
    path = QPainterPath(QPointF(s * 0.30, s * 0.18))
    path.cubicTo(s * 0.36, s * 0.45, s * 0.52, s * 0.62, s * 0.74, s * 0.82)
    p.drawPath(path)
    p.setBrush(QColor("#17120A"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(s * 0.30, s * 0.18), s * 0.07, s * 0.07)
    p.end()
    pm.setDevicePixelRatio(2)
    return pm
