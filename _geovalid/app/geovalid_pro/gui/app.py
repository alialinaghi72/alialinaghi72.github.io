"""GEOVALID PRO desktop application (PySide6). Bilingual fa/en, right-to-left layout for Persian, two visual themes."""
from __future__ import annotations

import sys
import traceback
from importlib import resources
from pathlib import Path

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSize, QSortFilterProxyModel, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
                               QPushButton, QScrollArea, QSizePolicy, QSplitter, QStackedWidget, QTableView, QTableWidget,
                               QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget)

from .. import APP_NAME, __version__
from ..io.mapping import FIELDS, KINDS, propose_mapping
from ..report import theme as T
from . import style

TR = {
    "title": ("اعتبارسنجی و تحلیل پایگاه دادهٔ گمانه‌های اکتشافی", "Exploration drillhole database validation and analysis"),
    "nav_data": ("داده و اجرا", "Data & run"), "nav_dash": ("داشبورد", "Dashboard"), "nav_issues": ("مسائل", "Issues"),
    "nav_geo": ("تحلیل عیار و نمودارها", "Grade analysis & charts"), "nav_rules": ("قواعد", "Rules"), "nav_log": ("گزارش اجرا", "Run log"),
    "add": ("افزودن فایل…", "Add files…"), "remove": ("حذف", "Remove"), "mapping": ("نگاشت فیلدها…", "Field mapping…"),
    "sample": ("دادهٔ نمونه", "Sample data"), "run": ("اجرای اعتبارسنجی", "Run validation"),
    "report": ("باز کردن گزارش", "Open report"), "folder": ("پوشهٔ خروجی", "Output folder"),
    "lang": ("English", "فارسی"), "about": ("دربارهٔ نرم‌افزار", "About"), "thresholds": ("آستانه‌ها…", "Thresholds…"),
    "theme": ("پوسته", "Theme"),
    "inputs": ("جدول‌های ورودی", "Input tables"), "optional": ("ورودی‌های اختیاری و خروجی", "Optional inputs and output"),
    "runbox": ("اجرا", "Run"),
    "use": ("استفاده", "Use"), "table": ("جدول", "Table"), "type": ("نوع", "Type"), "rows": ("ردیف", "Rows"),
    "mapped": ("نگاشت", "Mapping"), "dem": ("مدل رقومی ارتفاع (DEM)", "Topography DEM"),
    "licence": ("محدودهٔ پروانه (رئوس x,y)", "Licence boundary (x,y)"),
    "crm": ("جدول مواد مرجع (CRM)", "CRM standards table"),
    "profile": ("پروفایل اعتبارسنجی (YAML)", "Validation profile (YAML)"), "out": ("پوشهٔ خروجی", "Output folder"),
    "name": ("نام پروژه", "Project name"), "rlang": ("زبان گزارش", "Report language"),
    "critical": ("بحرانی", "Critical"), "error": ("خطا", "Error"), "warning": ("هشدار", "Warning"), "info": ("اطلاعات", "Info"),
    "holes": ("گمانه", "Holes"), "metres": ("متراژ حفاری", "Metres drilled"), "samples": ("نمونهٔ اصلی", "Original samples"),
    "rules_run": ("قاعدهٔ اجراشده", "Rules run"),
    "all": ("همه", "All"), "search": ("جستجو در مسائل…", "Search issues…"), "ready": ("آماده", "Ready"),
    "noinput": ("ابتدا فایل‌های پایگاه داده را اضافه کنید.", "Add the database files first."),
    "nocollar": ("هیچ جدول دهانه‌ای (collar) انتخاب نشده است؛ بیشتر قواعد اجرا نمی‌شوند. ادامه می‌دهید؟",
                 "No collar table is selected; most rules will not run. Continue?"),
    "done": ("اعتبارسنجی انجام شد.", "Validation finished."), "failed": ("اجرا با خطا متوقف شد", "Run failed"),
    "na": ("قابل اجرا نبود", "Not applicable"), "by_rule": ("مسائل بر پایهٔ قاعده", "Issues by rule"),
    "matrix": ("ماتریس اجرای قواعد", "Rule execution matrix"), "findings": ("مهم‌ترین یافته‌ها", "Key findings"),
    "never": ("هیچ داده‌ای تغییر داده نمی‌شود؛ خروجی‌ها در پوشهٔ جداگانه نوشته می‌شوند.",
              "Source data are never modified; outputs are written to a separate folder."),
    "depth_unit": ("واحد عمق", "Depth unit"), "analytes": ("ستون‌های عیار شناسایی‌شده", "Detected assay columns"),
    "empty": ("هنوز اعتبارسنجی اجرا نشده است. از بخش «داده و اجرا» فایل‌ها یا دادهٔ نمونه را بارگذاری و اجرا کنید.",
              "No validation has been run yet. Load files or the sample data in “Data & run” and run."),
    "nodata": ("دادهٔ کافی برای این نمودار وجود ندارد.", "Not enough data for this chart."),
    "analyte": ("عنصر", "Analyte"), "analyte2": ("عنصر دوم", "Second analyte"), "field": ("ویژگی توصیفی", "Logged attribute"),
    "field2": ("ویژگی دوم", "Second attribute"), "hole": ("گمانه", "Hole"), "variable": ("متغیر", "Variable"),
    "cutoff": ("عیار حد", "Cut-off"), "insight": ("تفسیر", "Interpretation"), "detail": ("جزئیات مسئله", "Issue detail"),
    "subtitle_dash": ("نمای کلی کیفیت پایگاه داده", "Database quality at a glance"),
    "cols": ({"issue_id": "#", "severity": "شدت", "rule_id": "قاعده", "table": "جدول", "hole_id": "گمانه", "from_m": "از", "to_m": "تا",
              "src_row": "ردیف فایل", "message_fa": "شرح", "message_en": "شرح", "title_fa": "عنوان", "title_en": "عنوان", "status": "وضعیت",
              "n_issues": "تعداد", "jorc": "JORC", "note": "یادداشت"},
             {"issue_id": "#", "severity": "Severity", "rule_id": "Rule", "table": "Table", "hole_id": "Hole", "from_m": "From", "to_m": "To",
              "src_row": "File row", "message_fa": "Message", "message_en": "Message", "title_fa": "Title", "title_en": "Title",
              "status": "Status", "n_issues": "Issues", "jorc": "JORC", "note": "Note"}),
    "subtitle_geo": ("ارتباط عیار با سنگ‌شناسی، دگرسانی، هوازدگی و سایر ویژگی‌های توصیفی",
                     "Grade against lithology, alteration, weathering and other logged attributes"),
}
SEV_COLORS = {"CRITICAL": "#C0392B", "ERROR": "#E07B24", "WARNING": "#E9B000", "INFO": "#1BA6A6"}

THRESHOLDS = [  # (rule, key, label_fa, label_en, step)
    ("COL-004", "near_dup_distance_m", "فاصلهٔ دهانه‌های تقریباً تکراری (متر)", "Near-duplicate collar distance (m)", 0.1),
    ("COL-011", "warn_m", "ΔZ هشدار، برداشت دقیق (متر)", "ΔZ warning, surveyed (m)", 0.5),
    ("COL-011", "error_m", "ΔZ خطا، برداشت دقیق (متر)", "ΔZ error, surveyed (m)", 0.5),
    ("COL-011", "handheld_warn_m", "ΔZ هشدار، GPS دستی (متر)", "ΔZ warning, handheld GPS (m)", 1.0),
    ("COL-011", "handheld_error_m", "ΔZ خطا، GPS دستی (متر)", "ΔZ error, handheld GPS (m)", 1.0),
    ("SUR-007", "first_station_max_m", "حداکثر عمق نخستین ایستگاه (متر)", "Max first-station depth (m)", 5),
    ("SUR-008", "max_spacing_m", "حداکثر فاصلهٔ ایستگاه‌ها (متر)", "Max survey station spacing (m)", 5),
    ("SUR-010", "warn_deg_30m", "داگ‌لگ هشدار (درجه بر ۳۰ متر)", "Dogleg warning (°/30 m)", 0.5),
    ("SUR-010", "error_deg_30m", "داگ‌لگ خطا (درجه بر ۳۰ متر)", "Dogleg error (°/30 m)", 0.5),
    ("INT-002", "micro_overlap_m", "هم‌پوشانی جزئی مجاز (متر)", "Micro-overlap tolerance (m)", 0.005),
    ("INT-004", "top_gap_tol_m", "شکاف بالایی مجاز (متر)", "Top gap tolerance (m)", 0.1),
    ("LIT-002", "thin_m", "بازهٔ نازک سنگ‌شناسی (متر)", "Thin lithology interval (m)", 0.1),
    ("QAQ-004", "max_fail_frac", "سهم مجاز جفت‌های مردود HARD", "Allowed share of failing HARD pairs", 0.01),
    ("ASY-011", "bdl_share_warn_frac", "سهم مجاز زیر حد تشخیص (عناصر کلیدی)", "Allowed BDL share (key analytes)", 0.05),
    ("CRS-004", "effect_min", "حداقل اندازهٔ اثر برای تفکیک دامنه‌ها", "Minimum effect size to separate domains", 0.05),
]

# Chart catalogue of the analysis page: key, group (None = heading), fa, en, selectors used
CHARTS = [
    ("g_geo", None, "عیار و زمین‌شناسی", "Grade & geology", ()),
    ("assoc", "geo", "ماتریس کنترل زمین‌شناختی (η²)", "Geological control matrix (η²)", ()),
    ("box", "geo", "عیار به تفکیک واحد", "Grade by unit", ("analyte", "field", "cutoff")),
    ("twoway", "geo", "میانهٔ عیار در ترکیب دو ویژگی", "Median grade: attribute × attribute", ("analyte", "field", "field2")),
    ("cramer", "geo", "هم‌رخدادی ویژگی‌ها (V کرامر)", "Attribute overlap (Cramér's V)", ()),
    ("contact", "geo", "تحلیل همبری (مرز سخت/نرم)", "Contact analysis (hard/soft)", ()),
    ("comp", "geo", "ترکیب واحدها با عمق", "Units with depth", ("field",)),
    ("strip", "geo", "لاگ ستونی گمانه", "Downhole strip log", ("hole",)),
    ("phys", "geo", "ویژگی فیزیکی به تفکیک واحد", "Physical property by unit", ("field", "variable")),
    ("g_sp", None, "روندهای مکانی", "Spatial trends", ()),
    ("swath", "sp", "نمودارهای نواری (Swath)", "Swath plots", ("analyte",)),
    ("gt", "sp", "نقشهٔ عیار × ضخامت", "Grade × thickness map", ("analyte", "cutoff")),
    ("glc", "sp", "منحنی عیار–متراژ", "Grade–length curve", ("analyte",)),
    ("g_as", None, "عیار", "Assays", ()),
    ("logprob", "as", "نمودار احتمال لگاریتمی", "Log-probability plot", ("analyte",)),
    ("corr", "as", "همبستگی بین عناصر", "Inter-element correlation", ()),
    ("scatter", "as", "پراکنش دو عنصر", "Scatter of two analytes", ("analyte", "analyte2", "field")),
    ("g_col", None, "دهانه و موقعیت", "Collars & location", ()),
    ("collar", "col", "نقشهٔ دهانه‌ها", "Collar map", ()),
    ("dz", "col", "اختلاف ارتفاع با توپوگرافی", "Collar vs topography", ()),
    ("method", "col", "روش برداشت مختصات", "Collar survey method", ()),
    ("g_qc", None, "کنترل کیفیت", "QA/QC", ()),
    ("crm", "qc", "نمودار کنترل CRM", "CRM control chart", ()),
    ("blank", "qc", "نتایج بلانک", "Blank results", ()),
    ("hard", "qc", "نمودار HARD تکراری‌ها", "Duplicate HARD plot", ()),
    ("rec", "qc", "بازیافت مغزه و عیار", "Core recovery vs grade", ()),
    ("g_ov", None, "نمای کلی", "Overview", ()),
    ("donut", "ov", "مسائل بر پایهٔ شدت", "Issues by severity", ()),
    ("family", "ov", "مسائل بر پایهٔ خانوادهٔ قاعده", "Issues by rule family", ()),
]


class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame | None = None, cols: list[str] | None = None):
        super().__init__()
        self.dark = True
        self.headers = {}
        self.set(df if df is not None else pd.DataFrame(), cols)

    def set(self, df: pd.DataFrame, cols=None):
        self.beginResetModel()
        self.df = df[cols] if cols and not df.empty else df
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.df)

    def columnCount(self, parent=QModelIndex()):
        return len(self.df.columns)

    def data(self, idx, role=Qt.DisplayRole):
        if not idx.isValid():
            return None
        v = self.df.iat[idx.row(), idx.column()]
        col = self.df.columns[idx.column()]
        if role == Qt.DisplayRole:
            if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
                return ""
            return f"{v:.6g}" if isinstance(v, float) else str(v)
        if col == "severity" and str(v) in SEV_COLORS:
            if role == Qt.ForegroundRole:
                return QColor(SEV_COLORS[str(v)]).lighter(125 if self.dark else 85)
            if role == Qt.BackgroundRole:
                c = QColor(SEV_COLORS[str(v)])
                c.setAlpha(46)
                return c
            if role == Qt.FontRole:
                f = QFont()
                f.setBold(True)
                return f
        if role == Qt.UserRole:
            return v
        return None

    def headerData(self, s, o, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if o != Qt.Horizontal:
                return str(s + 1)
            col = str(self.df.columns[s])
            return self.headers.get(col, col)
        return None


class Worker(QThread):
    progress = Signal(int, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, spec, out_dir, lang):
        super().__init__()
        self.spec, self.out_dir, self.lang = spec, out_dir, lang

    def run(self):
        try:
            from ..engine import run
            from ..io.writers import write_outputs
            res = run(self.spec, lambda p, m: self.progress.emit(p, m))
            write_outputs(res, self.out_dir, self.lang, lambda p, m: self.progress.emit(p, m))
            self.progress.emit(100, "done")
            self.done.emit(res)
        except Exception:
            self.failed.emit(traceback.format_exc())


class MappingDialog(QDialog):
    def __init__(self, parent, inp, fa: bool):
        super().__init__(parent)
        self.inp, self.fa = inp, fa
        self.setWindowTitle(f"{TR['mapping'][0 if fa else 1]} – {inp.name}")
        self.setMinimumWidth(540)
        lay = QVBoxLayout(self)
        form = QFormLayout()
        cols = ["—"] + list(inp.raw.df.columns)
        req, opt = FIELDS.get(inp.kind, ([], []))
        self.boxes = {}
        for f in req + opt:
            cb = QComboBox()
            cb.addItems(cols)
            cur = inp.mapping.fields.get(f)
            cb.setCurrentText(cur if cur else "—")
            form.addRow(f + (" *" if f in req else ""), cb)
            self.boxes[f] = cb
        self.unit = QComboBox()
        self.unit.addItems(["m", "ft"])
        self.unit.setCurrentText(inp.mapping.depth_unit)
        form.addRow(TR["depth_unit"][0 if fa else 1], self.unit)
        lay.addLayout(form)
        if inp.mapping.analytes:
            lay.addWidget(QLabel(TR["analytes"][0 if fa else 1]))
            lw = QListWidget()
            for a in inp.mapping.analytes:
                lw.addItem(f"{a.column}  →  {a.analyte}  ({a.unit or 'unit inferred'}){'  partial' if a.partial else ''}")
            lw.setMaximumHeight(150)
            lay.addWidget(lw)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def apply(self):
        for f, cb in self.boxes.items():
            v = cb.currentText()
            self.inp.mapping.fields[f] = None if v == "—" else v
        self.inp.mapping.depth_unit = self.unit.currentText()


class ThresholdDialog(QDialog):
    def __init__(self, parent, params: dict, fa: bool):
        super().__init__(parent)
        self.params = params
        self.setWindowTitle(TR["thresholds"][0 if fa else 1].rstrip("…"))
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.spins = {}
        for rid, key, lfa, len_, step in THRESHOLDS:
            sp = QDoubleSpinBox()
            sp.setDecimals(3)
            sp.setRange(0, 100000)
            sp.setSingleStep(step)
            sp.setValue(float(params["rules"].get(rid, {}).get(key, 0)))
            form.addRow(f"{rid}  {lfa if fa else len_}", sp)
            self.spins[(rid, key)] = sp
        lay.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def apply(self):
        for (rid, key), sp in self.spins.items():
            self.params["rules"].setdefault(rid, {})[key] = sp.value()


def card() -> tuple[QFrame, QVBoxLayout]:
    f = QFrame()
    f.setObjectName("Card")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(18, 14, 18, 16)
    lay.setSpacing(8)
    return f, lay


def label(obj: str, size: float | None = None, bold: bool = False) -> QLabel:
    lab = QLabel()
    lab.setObjectName(obj)
    if size or bold:
        f = lab.font()
        if size:
            f.setPointSizeF(size)
        f.setBold(bold)
        lab.setFont(f)
    return lab


def _toolbar_class():
    """Matplotlib's Qt toolbar with icons tinted to the app theme (its own light/dark guess fails under style sheets)."""
    from matplotlib import cbook
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
    from PySide6.QtGui import QPixmap

    class GVToolbar(NavigationToolbar2QT):
        tint = "#ECE6DA"

        def _icon(self, name):
            p = cbook._get_data_path("images", name)
            large = p.with_name(p.name.replace(".png", "_large.png"))
            pm = QPixmap(str(large if large.exists() else p))
            mask = pm.createMaskFromColor(QColor("black"), Qt.MaskOutColor)
            pm.fill(QColor(self.tint))
            pm.setMask(mask)
            return QIcon(pm)
    return GVToolbar


class ChartView(QWidget):
    """A matplotlib Figure embedded with the navigation toolbar (zoom, pan, save as PNG/SVG/PDF)."""
    TINT = "#ECE6DA"

    def __init__(self, parent=None, toolbar=True):
        super().__init__(parent)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(2)
        self.with_toolbar = toolbar
        self.canvas = self.toolbar = None
        self.msg = QLabel()
        self.msg.setObjectName("Muted")
        self.msg.setAlignment(Qt.AlignCenter)
        self.msg.setWordWrap(True)
        self.lay.addWidget(self.msg)
        self.setMinimumHeight(220)

    def show_figure(self, fig, empty_text=""):
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        for w in (self.canvas, self.toolbar):
            if w is not None:
                self.lay.removeWidget(w)
                w.setParent(None)
                w.deleteLater()
        self.canvas = self.toolbar = None
        if fig is None:
            self.msg.setText(empty_text)
            self.msg.show()
            return
        self.msg.hide()
        self.canvas = FigureCanvasQTAgg(fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if self.with_toolbar:
            tb = _toolbar_class()
            tb.tint = self.TINT
            self.toolbar = tb(self.canvas, self)
            self.toolbar.setIconSize(QSize(18, 18))
            self.lay.addWidget(self.toolbar)
        self.lay.addWidget(self.canvas, 1)
        self.canvas.draw_idle()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        from ..engine import default_params
        self.lang = "fa"
        self.theme = "obsidian"
        self.inputs = []
        self.result = None
        self.worker = None
        self.params = default_params()
        self._tr = []          # (widget, key, method) for retranslation
        self._suspend_draw = False
        self._cut_for = None
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 760)
        ic = resources.files("geovalid_pro.resources").joinpath("icon.png")
        if ic.is_file():
            self.setWindowIcon(QIcon(str(ic)))
        self._build()
        self.apply_theme()
        self.retranslate()

    # ================================================================ helpers
    def t(self, key):
        return TR[key][0 if self.lang == "fa" else 1]

    def tr_(self, widget, key, method="setText"):
        self._tr.append((widget, key, method))
        return widget

    @property
    def chart_theme(self):
        return T.OBSIDIAN if self.theme == "obsidian" else T.IVORY

    def c(self, key):
        return style.colour(self.theme, key)

    # ================================================================ layout
    def _build(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self._header())
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._sidebar())
        line = QFrame()
        line.setObjectName("VLine")
        body.addWidget(line)
        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)
        v.addLayout(body, 1)
        self.status = self.statusBar()
        self.pages = {}
        for key, builder in (("data", self._page_data), ("dash", self._page_dash), ("issues", self._page_issues),
                             ("geo", self._page_geo), ("rules", self._page_rules), ("log", self._page_log)):
            self.pages[key] = self.stack.addWidget(builder())
        self.go("data")

    def _header(self):
        h = QFrame()
        h.setObjectName("Header")
        h.setFixedHeight(66)
        lay = QHBoxLayout(h)
        lay.setContentsMargins(20, 8, 16, 8)
        logo = QLabel()
        logo.setPixmap(style.brand_pixmap(34))
        lay.addWidget(logo)
        txt = QVBoxLayout()
        txt.setSpacing(0)
        self.brand = label("Brand", 10.5, True)
        self.brand.setText("GEOVALID PRO")
        self.h_title = self.tr_(label("Title", 12.5), "title")
        txt.addWidget(self.brand)
        txt.addWidget(self.h_title)
        lay.addLayout(txt)
        lay.addStretch(1)
        self.b_theme, self.b_lang, self.b_about = QPushButton(), QPushButton(), QPushButton()
        for b, fn, k in ((self.b_theme, self.toggle_theme, "theme"), (self.b_lang, self.toggle_lang, "lang"),
                         (self.b_about, self.about, "about")):
            b.setObjectName("Chip")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(fn)
            self.tr_(b, k)
            lay.addWidget(b)
        return h

    def _sidebar(self):
        s = QFrame()
        s.setObjectName("Sidebar")
        s.setFixedWidth(236)
        lay = QVBoxLayout(s)
        lay.setContentsMargins(12, 16, 12, 14)
        lay.setSpacing(4)
        self.nav = QButtonGroup(self)
        self.nav.setExclusive(True)
        self.nav_btns = {}
        for key, ic, tk in (("data", "data", "nav_data"), ("dash", "dash", "nav_dash"), ("issues", "issues", "nav_issues"),
                            ("geo", "geo", "nav_geo"), ("rules", "rules", "nav_rules"), ("log", "log", "nav_log")):
            b = QPushButton()
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setIconSize(QSize(20, 20))
            b.setProperty("icon_kind", ic)
            b.clicked.connect(lambda _=False, k=key: self.go(k))
            self.nav.addButton(b)
            self.nav_btns[key] = b
            self.tr_(b, tk)
            lay.addWidget(b)
        lay.addStretch(1)
        self.side_btns = {}
        for key, ic, fn in (("report", "report", self.open_report), ("folder", "folder", self.open_folder),
                            ("thresholds", "sliders", self.edit_thresholds)):
            b = QPushButton()
            b.setObjectName("Side")
            b.setCursor(Qt.PointingHandCursor)
            b.setIconSize(QSize(18, 18))
            b.setProperty("icon_kind", ic)
            b.clicked.connect(fn)
            self.tr_(b, key)
            self.side_btns[key] = b
            lay.addWidget(b)
        ver = label("Muted", 8.5)
        ver.setText(f"v{__version__} · offline")
        ver.setAlignment(Qt.AlignCenter)
        lay.addSpacing(6)
        lay.addWidget(ver)
        return s

    def _page_frame(self, title_key, sub_key=None, scroll=False):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(26, 20, 26, 18)
        outer.setSpacing(12)
        head = QVBoxLayout()
        head.setSpacing(0)
        head.addWidget(self.tr_(label("H1", 16), title_key))
        if sub_key:
            head.addWidget(self.tr_(label("Muted", 9.5), sub_key))
        outer.addLayout(head)
        if scroll:
            sa = QScrollArea()
            sa.setWidgetResizable(True)
            inner = QWidget()
            lay = QVBoxLayout(inner)
            lay.setContentsMargins(0, 0, 6, 0)
            lay.setSpacing(14)
            sa.setWidget(inner)
            outer.addWidget(sa, 1)
            return page, lay
        return page, outer

    # ---------------------------------------------------------------- page: data & run
    def _page_data(self):
        page, lay = self._page_frame("nav_data", "never")
        row = QHBoxLayout()
        row.setSpacing(16)
        c1, l1 = card()
        l1.addWidget(self.tr_(label("H2", 11), "inputs"))
        self.tbl = QTableWidget(0, 5)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        l1.addWidget(self.tbl, 1)
        bl = QHBoxLayout()
        self.b_add, self.b_sample, self.b_remove, self.b_map = QPushButton(), QPushButton(), QPushButton(), QPushButton()
        for b, fn, k in ((self.b_add, self.add_files, "add"), (self.b_sample, self.load_sample, "sample"),
                         (self.b_remove, self.remove_selected, "remove"), (self.b_map, self.edit_mapping, "mapping")):
            b.clicked.connect(fn)
            b.setCursor(Qt.PointingHandCursor)
            self.tr_(b, k)
            bl.addWidget(b)
        bl.addStretch(1)
        l1.addLayout(bl)
        row.addWidget(c1, 3)
        right = QVBoxLayout()
        right.setSpacing(16)
        c2, l2 = card()
        l2.addWidget(self.tr_(label("H2", 11), "optional"))
        og = QGridLayout()
        og.setHorizontalSpacing(8)
        og.setVerticalSpacing(6)
        self.paths = {}
        for r, key in enumerate(("dem", "licence", "crm", "profile", "out")):
            lab = self.tr_(label("Muted", 9), key)
            le = QLineEdit()
            btn = QPushButton("…")
            btn.setFixedWidth(36)
            btn.clicked.connect(lambda _=False, k=key: self.browse(k))
            og.addWidget(lab, 2 * r, 0, 1, 2)
            og.addWidget(le, 2 * r + 1, 0)
            og.addWidget(btn, 2 * r + 1, 1)
            self.paths[key] = le
        self.paths["out"].setText(str(Path.home() / "GEOVALID_PRO" / "output"))
        l2.addLayout(og)
        right.addWidget(c2)
        c3, l3 = card()
        l3.addWidget(self.tr_(label("H2", 11), "runbox"))
        f = QFormLayout()
        self.e_name = QLineEdit("GEOVALID project")
        self.c_rlang = QComboBox()
        self.c_rlang.addItems(["fa", "en", "both"])
        f.addRow(self.tr_(label("Muted", 9), "name"), self.e_name)
        f.addRow(self.tr_(label("Muted", 9), "rlang"), self.c_rlang)
        l3.addLayout(f)
        self.b_run = QPushButton()
        self.b_run.setObjectName("Primary")
        self.b_run.setCursor(Qt.PointingHandCursor)
        self.b_run.setIconSize(QSize(18, 18))
        self.b_run.clicked.connect(self.run)
        self.tr_(self.b_run, "run")
        l3.addWidget(self.b_run)
        self.prog = QProgressBar()
        self.prog.setValue(0)
        l3.addWidget(self.prog)
        self.prog_lbl = label("Muted", 8.5)
        l3.addWidget(self.prog_lbl)
        right.addWidget(c3)
        right.addStretch(1)
        row.addLayout(right, 2)
        lay.addLayout(row, 1)
        return page

    # ---------------------------------------------------------------- page: dashboard
    def _page_dash(self):
        page, lay = self._page_frame("nav_dash", "subtitle_dash", scroll=True)
        self.dash_empty = self.tr_(label("Muted", 10), "empty")
        self.dash_empty.setWordWrap(True)
        lay.addWidget(self.dash_empty)
        grid = QGridLayout()
        grid.setSpacing(12)
        self.kpi = {}
        for i, (key, accent) in enumerate((("CRITICAL", SEV_COLORS["CRITICAL"]), ("ERROR", SEV_COLORS["ERROR"]),
                                           ("WARNING", SEV_COLORS["WARNING"]), ("INFO", SEV_COLORS["INFO"]),
                                           ("holes", None), ("metres", None), ("samples", None), ("rules_run", None))):
            f, fl = card()
            fl.setContentsMargins(16, 10, 16, 12)
            bar = QFrame()
            bar.setFixedHeight(3)
            bar.setProperty("accent", accent or "gold")
            fl.addWidget(bar)
            fl.addWidget(self.tr_(label("KpiName", 9), key.lower() if key.isupper() else key))
            val = label("KpiValue", 21, True)
            val.setText("–")
            fl.addWidget(val)
            self.kpi[key] = (bar, val)
            grid.addWidget(f, 0, i)
        lay.addLayout(grid)
        self.dash_views = {}
        for cells in ((("donut", 2, 340), ("family", 3, 340)), (("findings", 2, 340), ("assoc", 3, 340)), (("map", 1, 470),)):
            r = QHBoxLayout()
            r.setSpacing(14)
            for key, stretch, h in cells:
                c, cl = card()
                if key == "findings":
                    cl.addWidget(self.tr_(label("H2", 11), "findings"))
                    self.findings = QTextBrowser()
                    self.findings.setFrameShape(QFrame.NoFrame)
                    self.findings.setMinimumHeight(h - 40)
                    cl.addWidget(self.findings)
                else:
                    v = ChartView(toolbar=False)
                    v.setMinimumHeight(h)
                    cl.addWidget(v)
                    self.dash_views[key] = v
                r.addWidget(c, stretch)
            lay.addLayout(r)
        lay.addStretch(1)
        return page

    # ---------------------------------------------------------------- page: issues
    def _page_issues(self):
        page, lay = self._page_frame("nav_issues")
        fc, fl0 = card()
        fl = QHBoxLayout()
        fl0.addLayout(fl)
        self.f_sev, self.f_table, self.f_text = QComboBox(), QComboBox(), QLineEdit()
        self.f_sev.setMinimumWidth(140)
        self.f_table.setMinimumWidth(170)
        for w in (self.f_sev, self.f_table):
            w.currentIndexChanged.connect(self.apply_filter)
        self.f_text.textChanged.connect(self.apply_filter)
        self.tr_(self.f_text, "search", "setPlaceholderText")
        fl.addWidget(self.f_sev)
        fl.addWidget(self.f_table)
        fl.addWidget(self.f_text, 1)
        self.iss_count = label("Muted", 9)
        fl.addWidget(self.iss_count)
        lay.addWidget(fc)
        sp = QSplitter(Qt.Vertical)
        self.iss_view = QTableView()
        self.iss_model = PandasModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.iss_model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.iss_view.setModel(self.proxy)
        self.iss_view.setSortingEnabled(True)
        self.iss_view.setAlternatingRowColors(True)
        self.iss_view.setShowGrid(False)
        self.iss_view.verticalHeader().setVisible(False)
        self.iss_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.iss_view.horizontalHeader().setStretchLastSection(True)
        self.iss_view.selectionModel().selectionChanged.connect(self.show_detail)
        sp.addWidget(self.iss_view)
        self.detail = QTextBrowser()
        sp.addWidget(self.detail)
        sp.setSizes([560, 190])
        lay.addWidget(sp, 1)
        return page

    # ---------------------------------------------------------------- page: grade analysis & charts
    def _page_geo(self):
        page, lay = self._page_frame("nav_geo", "subtitle_geo")
        row = QHBoxLayout()
        row.setSpacing(14)
        self.chart_list = QListWidget()
        self.chart_list.setObjectName("ChartList")
        self.chart_list.setFixedWidth(250)
        self.chart_list.currentItemChanged.connect(lambda *_: self.draw_chart())
        row.addWidget(self.chart_list)
        mid = QVBoxLayout()
        mid.setSpacing(10)
        sc, sl0 = card()
        sc.setMinimumHeight(74)
        sl = QHBoxLayout()
        sl.setSpacing(10)
        sl0.addLayout(sl)
        self.sel = {}
        for key in ("analyte", "analyte2", "field", "field2", "hole", "variable"):
            box = QVBoxLayout()
            box.setSpacing(2)
            lab = self.tr_(label("Muted", 8.5), key)
            cb = QComboBox()
            cb.setMinimumWidth(110)
            cb.currentIndexChanged.connect(lambda *_: self.draw_chart())
            box.addWidget(lab)
            box.addWidget(cb)
            sl.addLayout(box)
            self.sel[key] = (lab, cb)
        box = QVBoxLayout()
        box.setSpacing(2)
        lab = self.tr_(label("Muted", 8.5), "cutoff")
        self.cut = QDoubleSpinBox()
        self.cut.setDecimals(4)
        self.cut.setRange(0, 1e7)
        self.cut.setKeyboardTracking(False)
        self.cut.valueChanged.connect(lambda *_: self.draw_chart())
        box.addWidget(lab)
        box.addWidget(self.cut)
        sl.addLayout(box)
        self.sel["cutoff"] = (lab, self.cut)
        sl.addStretch(1)
        mid.addWidget(sc)
        cc, cl = card()
        self.chart = ChartView()
        cl.addWidget(self.chart, 1)
        mid.addWidget(cc, 1)
        row.addLayout(mid, 1)
        ic, il = card()
        ic.setFixedWidth(320)
        il.addWidget(self.tr_(label("H2", 11), "insight"))
        self.insight = QTextBrowser()
        self.insight.setFrameShape(QFrame.NoFrame)
        il.addWidget(self.insight, 1)
        row.addWidget(ic)
        lay.addLayout(row, 1)
        return page

    # ---------------------------------------------------------------- page: rules & log
    def _table_view(self, model):
        v = QTableView()
        v.setModel(model)
        v.setAlternatingRowColors(True)
        v.setShowGrid(False)
        v.verticalHeader().setVisible(False)
        v.horizontalHeader().setStretchLastSection(True)
        return v

    def _page_rules(self):
        page, lay = self._page_frame("nav_rules")
        sp = QSplitter(Qt.Vertical)
        c1, l1 = card()
        l1.addWidget(self.tr_(label("H2", 11), "by_rule"))
        self.rules_lbl = label("Muted", 9.5)
        l1.addWidget(self.rules_lbl)
        self.by_rule_model = PandasModel()
        self.by_rule = self._table_view(self.by_rule_model)
        l1.addWidget(self.by_rule, 1)
        c2, l2 = card()
        l2.addWidget(self.tr_(label("H2", 11), "matrix"))
        self.matrix_model = PandasModel()
        self.matrix = self._table_view(self.matrix_model)
        l2.addWidget(self.matrix, 1)
        sp.addWidget(c1)
        sp.addWidget(c2)
        lay.addWidget(sp, 1)
        return page

    def _page_log(self):
        page, lay = self._page_frame("nav_log")
        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        f = QFont("Consolas")
        f.setStyleHint(QFont.Monospace)
        f.setPointSizeF(9.5)
        self.logbox.setFont(f)
        lay.addWidget(self.logbox, 1)
        return page

    # ================================================================ theme & language
    def apply_theme(self):
        from PySide6.QtGui import QPalette
        app = QApplication.instance()
        pal = QPalette()
        for role, key in ((QPalette.Window, "bg"), (QPalette.Base, "card"), (QPalette.AlternateBase, "alt"), (QPalette.Button, "card"),
                          (QPalette.WindowText, "ink"), (QPalette.Text, "ink"), (QPalette.ButtonText, "ink"),
                          (QPalette.ToolTipBase, "card"), (QPalette.ToolTipText, "ink"), (QPalette.PlaceholderText, "muted")):
            pal.setColor(role, QColor(self.c(key)))
        pal.setColor(QPalette.Highlight, QColor(self.c("gold_lo")))
        pal.setColor(QPalette.HighlightedText, QColor(self.c("on_gold")))
        app.setPalette(pal)
        app.setStyleSheet(style.qss(self.theme))
        ChartView.TINT = self.c("ink")
        muted, gold = self.c("muted"), self.c("gold")
        for b in list(self.nav_btns.values()) + list(self.side_btns.values()):
            b.setIcon(style.icon(b.property("icon_kind"), muted, gold))
        self.b_run.setIcon(style.icon("run", self.c("on_gold")))
        self.b_add.setIcon(style.icon("add", self.c("ink")))
        self.b_sample.setIcon(style.icon("sample", self.c("ink")))
        self.b_theme.setIcon(style.icon("theme", gold))
        self.b_lang.setIcon(style.icon("lang", gold))
        self.b_about.setIcon(style.icon("info", gold))
        for bar, _ in self.kpi.values():
            acc = bar.property("accent")
            bar.setStyleSheet(f"background:{gold if acc == 'gold' else acc};border:none;border-radius:1px")
        for m in (self.iss_model, self.by_rule_model, self.matrix_model):
            m.dark = self.theme == "obsidian"
        if self.result is not None:
            self._fill_chart_list()
        self.refresh_charts()

    def toggle_theme(self):
        self.theme = "ivory" if self.theme == "obsidian" else "obsidian"
        self.apply_theme()

    def retranslate(self):
        fa = self.lang == "fa"
        app = QApplication.instance()
        app.setLayoutDirection(Qt.RightToLeft if fa else Qt.LeftToRight)
        f = app.font()
        f.setFamilies(["Vazirmatn", "Inter"] if fa else ["Inter", "Vazirmatn"])
        app.setFont(f)
        for w, key, method in self._tr:
            getattr(w, method)(self.t(key))
        self.tbl.setHorizontalHeaderLabels([self.t(k) for k in ("use", "table", "type", "rows", "mapped")])
        for m in (self.iss_model, self.matrix_model, self.by_rule_model):
            m.headers = self.t("cols")
        self.c_rlang.setCurrentText("fa" if fa else "en")
        self._fill_filters()
        self._fill_chart_list()
        self.status.showMessage(self.t("ready"))
        if self.result is not None:
            self.show_result(self.result)

    def toggle_lang(self):
        self.lang = "en" if self.lang == "fa" else "fa"
        self.retranslate()

    def go(self, key):
        self.stack.setCurrentIndex(self.pages[key])
        self.nav_btns[key].setChecked(True)
        if key == "geo" and self.result is not None and self.chart.canvas is None:
            self.draw_chart()

    # ================================================================ inputs
    def refresh_table(self):
        self.tbl.setRowCount(len(self.inputs))
        for r, inp in enumerate(self.inputs):
            cb = QCheckBox()
            cb.setChecked(inp.enabled and inp.kind != "ignore")
            cb.stateChanged.connect(lambda s, i=inp: setattr(i, "enabled", bool(s)))
            w = QWidget()
            wl = QHBoxLayout(w)
            wl.setContentsMargins(8, 0, 8, 0)
            wl.addWidget(cb)
            self.tbl.setCellWidget(r, 0, w)
            self.tbl.setItem(r, 1, QTableWidgetItem(inp.name))
            kc = QComboBox()
            kc.setMinimumWidth(130)
            kc.addItems(KINDS)
            kc.setCurrentText(inp.kind)
            kc.currentTextChanged.connect(lambda k, i=inp: self.change_kind(i, k))
            self.tbl.setCellWidget(r, 2, kc)
            self.tbl.setItem(r, 3, QTableWidgetItem(f"{len(inp.raw.df):,}"))
            req = FIELDS.get(inp.kind, ([], []))[0]
            ok = all(inp.mapping.fields.get(f) for f in req)
            n_an = len(inp.mapping.analytes)
            txt = ("✔" if ok else "✖ " + ", ".join(f for f in req if not inp.mapping.fields.get(f))) + (f"  ·  {n_an} analytes" if n_an else "")
            it = QTableWidgetItem(txt)
            it.setForeground(QColor("#3DBE8B") if ok else QColor(SEV_COLORS["CRITICAL"]))
            self.tbl.setItem(r, 4, it)
            self.tbl.setRowHeight(r, 38)
        self.tbl.resizeColumnsToContents()
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def change_kind(self, inp, kind):
        inp.kind = kind
        inp.mapping = propose_mapping(inp.raw.df, kind)
        inp.enabled = kind != "ignore"
        self.refresh_table()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, self.t("add"), "", "Tables (*.csv *.txt *.tsv *.xlsx *.xlsm *.xls);;All (*)")
        if files:
            self._load(files)

    def _load(self, files):
        from ..engine import load_inputs
        try:
            new = load_inputs(files)
        except Exception as e:
            QMessageBox.critical(self, APP_NAME, f"{e}")
            return
        names = {i.name for i in self.inputs}
        for n in new:
            if n.name in names:
                n.name += "_2"
        self.inputs += new
        self.log(f"+ {len(new)} " + ", ".join(f"{i.name} [{i.kind}]" for i in new))
        self.refresh_table()

    def remove_selected(self):
        rows = sorted({i.row() for i in self.tbl.selectedIndexes()}, reverse=True)
        for r in rows:
            del self.inputs[r]
        self.refresh_table()

    def edit_mapping(self):
        rows = sorted({i.row() for i in self.tbl.selectedIndexes()})
        if not rows:
            return
        dlg = MappingDialog(self, self.inputs[rows[0]], self.lang == "fa")
        if dlg.exec():
            dlg.apply()
            self.refresh_table()

    def browse(self, key):
        if key == "out":
            d = QFileDialog.getExistingDirectory(self, self.t("out"), self.paths["out"].text())
            if d:
                self.paths["out"].setText(d)
            return
        filt = {"dem": "DEM (*.asc *.xyz *.csv *.txt)", "licence": "Polygon (*.csv *.txt *.xlsx)",
                "crm": "CRM (*.csv *.xlsx)", "profile": "YAML (*.yaml *.yml)"}[key]
        f, _ = QFileDialog.getOpenFileName(self, self.t(key), "", filt + ";;All (*)")
        if f:
            self.paths[key].setText(f)

    def load_sample(self):
        from .. import synth
        d = Path.home() / "GEOVALID_PRO" / "sample_data"
        synth.generate(str(d), inject=True)
        self.inputs = []
        self._load([str(d / f"{n}.csv") for n in synth.SAMPLE_TABLES])
        self.paths["dem"].setText(str(d / "dem.asc"))
        self.paths["licence"].setText(str(d / "licence.csv"))
        self.paths["crm"].setText(str(d / "crm_standards.csv"))
        self.e_name.setText("Sample porphyry Cu-Au-Mo (synthetic)")
        self.log(f"sample data: {d}  (manifest.csv lists the injected errors)")

    def edit_thresholds(self):
        dlg = ThresholdDialog(self, self.params, self.lang == "fa")
        if dlg.exec():
            dlg.apply()
            self.log("thresholds updated")

    # ================================================================ run
    def run(self):
        from ..engine import ProjectSpec, _merge, load_params
        if not self.inputs:
            QMessageBox.information(self, APP_NAME, self.t("noinput"))
            return
        if not any(i.enabled and i.kind == "collar" for i in self.inputs):
            if QMessageBox.question(self, APP_NAME, self.t("nocollar")) != QMessageBox.Yes:
                return
        params = self.params
        prof = self.paths["profile"].text().strip()
        if prof:
            params = _merge(load_params(prof), {"rules": self.params["rules"]})
        g = lambda k: self.paths[k].text().strip() or None
        spec = ProjectSpec([i for i in self.inputs if i.enabled and i.kind != "ignore"], g("dem"), g("licence"), g("crm"),
                           None, self.e_name.text().strip() or "GEOVALID project", params)
        out = self.paths["out"].text().strip() or str(Path.home() / "GEOVALID_PRO" / "output")
        self.b_run.setEnabled(False)
        self.prog.setValue(0)
        self.worker = Worker(spec, out, self.c_rlang.currentText())
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_progress(self, p, msg):
        self.prog.setValue(p)
        self.prog_lbl.setText(msg)
        self.status.showMessage(msg)

    def on_done(self, res):
        self.result = res
        self.b_run.setEnabled(True)
        self.chart.show_figure(None, "")
        self.show_result(res)
        self.log(f"{self.t('done')}  {res.outputs.get('folder')}")
        for e in res.errors:
            self.log("! " + e.splitlines()[0] if e.strip() else "")
        self.status.showMessage(f"{self.t('done')}  {res.outputs.get('folder')}")
        self.go("dash")

    def on_failed(self, tb):
        self.b_run.setEnabled(True)
        self.log(tb)
        QMessageBox.critical(self, APP_NAME, f"{self.t('failed')}\n\n{tb.splitlines()[-1]}")

    # ================================================================ results
    def show_result(self, res):
        from ..io.writers import summaries
        from ..rules.interval import QC_TYPES
        iss = res.issues
        counts = iss["severity"].value_counts().to_dict() if not iss.empty else {}
        ctx = res.ctx
        n_orig = sum(int((~t.df["qc_class"].isin(QC_TYPES)).sum()) if "qc_class" in t.df else len(t.df) for t in ctx.by_kind("assay"))
        nh = len(ctx.collar_u) if ctx.has("collar") else 0
        m = float(ctx.collar_u["eoh_m"].sum()) if nh and "eoh_m" in ctx.collar_u else 0
        st = res.matrix["status"].value_counts().to_dict()
        vals = {"CRITICAL": counts.get("CRITICAL", 0), "ERROR": counts.get("ERROR", 0), "WARNING": counts.get("WARNING", 0),
                "INFO": counts.get("INFO", 0), "holes": nh, "metres": round(m), "samples": n_orig, "rules_run": st.get("RUN", 0)}
        for k, (_, lab) in self.kpi.items():
            lab.setText(f"{vals[k]:,}")
        self.dash_empty.hide()
        self.rules_lbl.setText(f"{self.t('rules_run')}: {st.get('RUN', 0)}   ·   {self.t('na')}: {st.get('NOT_APPLICABLE', 0)}"
                               + (f"   ·   FAILED: {st['FAILED']}" if st.get("FAILED") else ""))
        br = summaries(res)["by_rule"].reset_index()
        title = "title_fa" if self.lang == "fa" else "title_en"
        if not br.empty:
            br = br[["rule_id", title, "CRITICAL", "ERROR", "WARNING", "INFO", "total"]].rename(
                columns={title: "عنوان قاعده" if self.lang == "fa" else "Rule title", "CRITICAL": self.t("critical"),
                         "ERROR": self.t("error"), "WARNING": self.t("warning"), "INFO": self.t("info"), "total": "Σ"})
            self.by_rule_model.set(br)
            self.by_rule.resizeColumnsToContents()
        self.matrix_model.set(res.matrix[["rule_id", title, "status", "n_issues", "jorc", "note"]])
        self.matrix.resizeColumnsToContents()
        msg = "message_fa" if self.lang == "fa" else "message_en"
        self.iss_model.set(iss, ["issue_id", "severity", "rule_id", "table", "hole_id", "from_m", "to_m", "src_row", msg])
        self.iss_view.resizeColumnsToContents()
        self.iss_count.setText(f"{len(iss):,}")
        self._fill_filters()
        self._fill_selectors()
        self.refresh_charts()

    def _findings_html(self, res):
        from ..analysis import categorical as C
        from ..io.writers import inventory
        from ..report.html import _narrative
        counts = res.issues["severity"].value_counts().to_dict() if not res.issues.empty else {}
        lines = _narrative(res, self.lang, counts, inventory(res))
        cat = res.ctx.stats.get("categorical", {})
        assoc = cat.get("association")
        if isinstance(assoc, pd.DataFrame) and not assoc.empty:
            a = C.primary_analytes(assoc, cat["units"], res.ctx.params, 1)[0]
            lines += C.narrative(assoc, cat["fields"], cat["units"], a, self.lang)[:3]
        gold, ink = self.c("gold"), self.c("ink")
        items = "".join(f"<tr><td style='color:{gold};padding:5px 6px;vertical-align:top'>◆</td><td style='padding:5px 0'>{x}</td></tr>"
                        for x in lines)
        return f"<div style='color:{ink};line-height:165%'><table cellspacing='0'>{items}</table></div>"

    def refresh_charts(self):
        if self.result is None:
            return
        from ..report import charts as K
        from ..report.html import _worst_by_hole
        th, lang, res = self.chart_theme, self.lang, self.result
        cat = res.ctx.stats.get("categorical", {})
        labels = {f: (v[1] if lang == "fa" else v[0]) for f, v in cat.get("fields", {}).items()}
        dv = self.dash_views
        dv["donut"].show_figure(K.severity_donut(res.issues, lang, th), self.t("nodata"))
        dv["family"].show_figure(K.family_bar(res.issues, lang, th), self.t("nodata"))
        dv["assoc"].show_figure(K.association_heatmap(cat.get("association"), labels, lang, th), self.t("nodata"))
        dv["map"].show_figure(K.collar_map(res.ctx, _worst_by_hole(res.issues), lang, th) if res.ctx.has("collar") else None,
                              self.t("nodata"))
        self.findings.setHtml(self._findings_html(res))
        if self.stack.currentIndex() == self.pages["geo"] or self.chart.canvas is not None:
            self.draw_chart()

    # ---------------------------------------------------------------- analysis page
    def _fill_chart_list(self):
        cur = self.chart_list.currentItem().data(Qt.UserRole) if self.chart_list.currentItem() else "box"
        self.chart_list.blockSignals(True)
        self.chart_list.clear()
        sel = None
        for key, group, fa, en, _ in CHARTS:
            it = QListWidgetItem(fa if self.lang == "fa" else en)
            if group is None:
                it.setFlags(Qt.NoItemFlags)
                f = it.font()
                f.setBold(True)
                f.setPointSizeF(8.5)
                it.setFont(f)
                it.setForeground(QColor(self.c("gold")))
            else:
                it.setData(Qt.UserRole, key)
                if key == cur:
                    sel = it
            self.chart_list.addItem(it)
        if sel is not None:
            self.chart_list.setCurrentItem(sel)
        self.chart_list.blockSignals(False)

    def _fill_selectors(self):
        res = self.result
        if res is None:
            return
        from ..analysis import categorical as C
        smp, units, fields = C.sample_table(res.ctx)
        cat = res.ctx.stats["categorical"]
        assoc = cat.get("association")
        if assoc is None and fields:
            assoc = cat["association"] = C.association(smp, fields, list(units))
        prim = C.primary_analytes(assoc, units, res.ctx.params, 2) if units else []
        order = prim + [a for a in units if a not in prim]
        fa = self.lang == "fa"
        logging = [f for f, v in fields.items() if v[2] == "logging"]
        forder = logging + [f for f in fields if f not in logging]
        flabels = {f: fields[f][1] if fa else fields[f][0] for f in forder}
        holes = []
        if not smp.empty and order:
            hg = C.hole_grades(smp, res.ctx, order[0], C.cutoff_for(smp, order[0], units[order[0]], res.ctx.params))
            holes = list(hg.sort_values("gt", ascending=False)["hole_id"]) if not hg.empty else []
            holes += sorted(set(smp["hole_id"].dropna()) - set(holes))
        phys = C.physical_table(res.ctx)
        variables = list(dict.fromkeys(phys["variable"])) if not phys.empty else []
        self._suspend_draw = True
        for key, items, labs in (("analyte", order, None), ("analyte2", order[1:] + order[:1], None), ("field", forder, flabels),
                                 ("field2", forder[1:] + forder[:1], flabels), ("hole", holes, None), ("variable", variables, None)):
            cb = self.sel[key][1]
            prev = cb.currentData()
            cb.blockSignals(True)
            cb.clear()
            for x in items:
                cb.addItem(str(labs.get(x, x)) if labs else str(x), x)
            i = cb.findData(prev)
            cb.setCurrentIndex(i if i >= 0 else 0)
            cb.blockSignals(False)
        self._suspend_draw = False
        self._set_cutoff_default()

    def _set_cutoff_default(self):
        from ..analysis import categorical as C
        res = self.result
        a = self.sel["analyte"][1].currentData()
        if res is None or not a:
            return
        smp, units, _ = C.sample_table(res.ctx)
        cut = C.cutoff_for(smp, a, units.get(a, ""), res.ctx.params) or 0
        self.cut.blockSignals(True)
        self.cut.setValue(cut)
        self.cut.setSuffix(f" {units.get(a, '')}")
        self.cut.blockSignals(False)
        self._cut_for = a

    def draw_chart(self):
        if self._suspend_draw or self.result is None:
            return
        it = self.chart_list.currentItem()
        key = it.data(Qt.UserRole) if it else None
        if not key:
            for r in range(self.chart_list.count()):
                if self.chart_list.item(r).data(Qt.UserRole) == "box":
                    self.chart_list.blockSignals(True)
                    self.chart_list.setCurrentRow(r)
                    self.chart_list.blockSignals(False)
                    key = "box"
                    break
            if not key:
                return
        used = next(c[4] for c in CHARTS if c[0] == key)
        for k, (lab, w) in self.sel.items():
            lab.setVisible(k in used)
            w.setVisible(k in used)
        if "analyte" in used and self._cut_for != self.sel["analyte"][1].currentData():
            self._set_cutoff_default()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            fig, html = self._build_chart(key)
        except Exception:
            fig, html = None, f"<pre>{traceback.format_exc()[-1500:]}</pre>"
        finally:
            QApplication.restoreOverrideCursor()
        self.chart.show_figure(fig, self.t("nodata"))
        self.insight.setHtml(html or "")

    def _table_html(self, df, cols, heads):
        if df is None or df.empty:
            return ""
        muted, line = self.c("muted"), self.c("line")
        th_ = "".join(f"<th style='text-align:start;color:{muted};padding:3px 6px;border-bottom:1px solid {line}'>{h}</th>" for h in heads)
        rows = "".join("<tr>" + "".join(f"<td nowrap style='padding:3px 6px'>{(f'{v:.3g}' if isinstance(v, float) else v)}</td>" for v in r) + "</tr>"
                       for r in df[cols].itertuples(index=False))
        return f"<table cellspacing='0' style='font-size:9pt'><tr>{th_}</tr>{rows}</table>"

    def _build_chart(self, key):
        from ..analysis import categorical as C
        from ..report import charts as K
        from ..report.html import _worst_by_hole
        res, ctx, th, lang = self.result, self.result.ctx, self.chart_theme, self.lang
        fa = lang == "fa"
        smp, units, fields = C.sample_table(ctx)
        cat = ctx.stats["categorical"]
        assoc = cat.get("association")
        labels = {f: (v[1] if fa else v[0]) for f, v in fields.items()}
        g = lambda k: self.sel[k][1].currentData()
        a, a2, f1, f2 = g("analyte"), g("analyte2"), g("field"), g("field2")
        cut = self.cut.value() or None
        unit = units.get(a, "")
        gold = self.c("gold")
        html, fig = "", None
        if key == "assoc":
            fig = K.association_heatmap(assoc, labels, lang, th)
            if a and assoc is not None:
                html = "".join(f"<p>{x}</p>" for x in C.narrative(assoc, fields, units, a, lang))
        elif key == "box" and f1 and a:
            row = assoc[(assoc["field"] == f1) & (assoc["analyte"] == a)] if assoc is not None and not assoc.empty else pd.DataFrame()
            fig = K.grade_by_category(smp, f1, a, unit, labels.get(f1), cut, row.iloc[0].to_dict() if len(row) else None, lang, th)
            st = C.category_stats(smp, f1, a, cut)
            html = (f"<p style='color:{gold}'><b>{labels.get(f1, f1)} · {a} ({unit})</b></p>" +
                    self._table_html(st, ["category", "n", "median", "mean_lw", "pct_above_cutoff"],
                                     ["", "n", "P50", "LW", f"≥{cut:.3g}" if cut else "%"]))
            if len(row):
                r = row.iloc[0]
                html += f"<p>η² = <b>{r['eta2']:.3f}</b> · Kruskal–Wallis p {K._pfmt(r['kw_p'])}</p>"
            dom = cat.get("domains")
            if isinstance(dom, pd.DataFrame) and not dom.empty:
                d = dom[(dom["field"] == f1) & (dom["analyte"] == a)]
                if len(d):
                    html += f"<p style='color:{gold}'>{'دامنه‌های پیشنهادی تخمین' if fa else 'Suggested estimation domains'}</p><p>{d['suggested_domains'].iloc[0]}</p>"
        elif key == "twoway" and f1 and f2 and f1 != f2 and a:
            med, cnt = C.two_way(smp, f1, f2, a)
            fig = K.two_way_heatmap(med, cnt, labels[f1], labels[f2], a, unit, lang, th)
            html = f"<p>Cramér's V ({labels[f1]} × {labels[f2]}) = <b>{C.cramers_v(smp, f1, f2):.2f}</b></p>"
        elif key == "cramer":
            fig = K.field_association(smp, fields, lang, th)
        elif key == "contact":
            fig = K.contact_plot(cat.get("contacts"), units, lang, th, labels)
            html = "".join(f"<p><b>{labels.get(c['field'], c['field'])} · {c['unit']}</b>: {c['boundary']}"
                           + (f" ≈ {c['width_m']:.0f} m" if c["boundary"] == "soft" else "") + "</p>" for c in cat.get("contacts") or [])
        elif key == "comp" and f1:
            fig = K.composition_depth(smp, f1, labels.get(f1), lang, th)
        elif key == "strip" and g("hole"):
            prim = C.primary_analytes(assoc, units, ctx.params, 3)
            fig = K.strip_log(smp, g("hole"), prim, fields, units, lang, th)
            hs = smp[smp["hole_id"] == g("hole")]
            rows = []
            for x in prim:
                v, w = hs[x], hs["length_m"]
                ok = v.notna()
                rows.append({"analyte": x, "n": int(ok.sum()), "lw": float((v[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else float("nan"),
                             "max": float(v.max())})
            html = (f"<p style='color:{gold}'><b>{g('hole')}</b> · {hs['to_m'].max():.1f} m</p>" +
                    self._table_html(pd.DataFrame(rows), ["analyte", "n", "lw", "max"], ["", "n", "LW mean", "max"]))
            iss = res.issues[res.issues["hole_id"] == g("hole")]
            if not iss.empty:
                html += "<p>" + " · ".join(f"{r} ({n})" for r, n in iss["rule_id"].value_counts().items()) + "</p>"
        elif key == "phys" and f1 and g("variable"):
            fig = K.physical_by_category(C.physical_table(ctx), f1, g("variable"), labels.get(f1), lang, th)
        elif key == "swath" and a:
            fig = K.swath_plots(smp, a, unit, lang, th)
        elif key == "gt" and a:
            hg = C.hole_grades(smp, ctx, a, cut)
            fig = K.gt_map(hg, a, unit, cut, ctx.licence, lang, th)
            if not hg.empty:
                html = self._table_html(hg.sort_values("gt", ascending=False).head(15).round(3), ["hole_id", "mean_lw", "metres_above", "gt"],
                                        [self.t("hole"), "LW mean", "m ≥ cut", "GT"])
        elif key == "glc" and a:
            fig = K.grade_length_curve(smp, a, unit, lang, th)
            gl = C.grade_length(smp, a)
            if not gl.empty:
                html = self._table_html(gl.iloc[::5].round(4), ["cutoff", "metres", "grade", "metal_pct"], ["cut-off", "m", "grade", "% metal"])
        elif key == "logprob" and a:
            fig = K.logprob({a: smp[a]}, units, lang, th)
        elif key == "corr" and units:
            fig = K.corr_heatmap(smp[list(units)], lang, th)
        elif key == "scatter" and a and a2 and a != a2:
            fig = K.scatter_pair(smp, a, a2, f1, units, lang, th)
        elif key == "collar" and ctx.has("collar"):
            fig = K.collar_map(ctx, _worst_by_hole(res.issues), lang, th)
        elif key == "dz":
            fig = K.dz_map(ctx, lang, th)
        elif key == "method":
            fig = K.method_bar(ctx.stats.get("collar_method"), lang, th)
        elif key == "crm":
            fig = K.crm_chart(next(iter(ctx.stats.get("crm_results", {}).values()), None), lang, th)
        elif key == "blank":
            fig = K.blank_chart(next(iter(ctx.stats.get("blank_results", {}).values()), None), lang, th)
        elif key == "hard":
            pairs = ctx.stats.get("dup_pairs", {})
            keys = [k for k in ctx.params.get("key_analytes", []) if any(p[2] == k for p in pairs)][:2]
            fig = K.hard_chart(pairs, lang, th, keys or None)
        elif key == "rec":
            rg = next(iter(ctx.stats.get("recovery_grade", {}).values()), None)
            fig = K.recovery_grade(rg[1], rg[2], rg[0], lang, th) if rg else None
        elif key == "donut":
            fig = K.severity_donut(res.issues, lang, th)
        elif key == "family":
            fig = K.family_bar(res.issues, lang, th)
        return fig, (f"<div style='color:{self.c('ink')};line-height:150%'>{html}</div>" if html else "")

    # ---------------------------------------------------------------- issues page
    def _fill_filters(self):
        for w in (self.f_sev, self.f_table):
            w.blockSignals(True)
        self.f_sev.clear()
        self.f_sev.addItems([self.t("all"), "CRITICAL", "ERROR", "WARNING", "INFO"])
        self.f_table.clear()
        self.f_table.addItem(self.t("all"))
        if self.result is not None and not self.result.issues.empty:
            self.f_table.addItems(sorted(self.result.issues["table"].dropna().unique()))
        for w in (self.f_sev, self.f_table):
            w.blockSignals(False)

    def apply_filter(self):
        if self.result is None:
            return
        iss = self.result.issues
        if self.f_sev.currentIndex() > 0:
            iss = iss[iss["severity"] == self.f_sev.currentText()]
        if self.f_table.currentIndex() > 0:
            iss = iss[iss["table"] == self.f_table.currentText()]
        msg = "message_fa" if self.lang == "fa" else "message_en"
        self.iss_model.set(iss, ["issue_id", "severity", "rule_id", "table", "hole_id", "from_m", "to_m", "src_row", msg])
        self.proxy.setFilterFixedString(self.f_text.text())
        self.iss_count.setText(f"{self.proxy.rowCount():,} / {len(self.result.issues):,}")

    def show_detail(self, *_):
        idx = self.iss_view.selectionModel().selectedRows()
        if not idx or self.result is None:
            return
        src = self.proxy.mapToSource(idx[0])
        issue_id = self.iss_model.df.iloc[src.row()]["issue_id"]
        r = self.result.issues.set_index("issue_id").loc[issue_id]
        from ..core.issues import rules_meta
        meta = rules_meta().get(r["rule_id"], {})
        title = meta.get("title_fa" if self.lang == "fa" else "title_en", "")

        def f(x):
            return "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x)
        muted, ink = self.c("muted"), self.c("ink")
        sev = SEV_COLORS[r["severity"]]
        html = (f"<div style='color:{ink}'><p><span style='background:{sev};color:white'>&nbsp;{r['severity']}&nbsp;</span>"
                f"&nbsp; <b style='color:{self.c('gold')}'>{r['rule_id']}</b> · <b>{title}</b></p>"
                f"<p>{f(r['table'])} · {f(r['hole_id'])} {f(r['from_m'])}–{f(r['to_m'])} · row {f(r['src_row'])}</p>"
                f"<p>{f(r['message_fa'])}</p><p dir='ltr'>{f(r['message_en'])}</p>"
                f"<p><i>{f(r['suggested_fix'])}</i></p><p style='color:{muted};font-size:9pt' dir='ltr'>{meta.get('logic', '')[:700]}</p>"
                f"<p style='color:{muted};font-size:9pt' dir='ltr'>JORC/NI: {meta.get('jorc', '')} · {meta.get('reference', '')}</p></div>")
        self.detail.setHtml(html)

    # ================================================================ misc
    def open_report(self):
        if self.result is None or not self.result.outputs:
            return
        rep = self.result.outputs.get(f"report_{self.lang}") or self.result.outputs.get("report_fa") or self.result.outputs.get("report_en")
        if rep:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(rep)))

    def open_folder(self):
        d = self.result.outputs.get("folder") if self.result is not None else Path(self.paths["out"].text())
        if d:
            Path(d).mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))

    def about(self):
        from ..rules import REGISTRY
        from ..engine import IMPORT_RULES
        n = len(REGISTRY) + len(IMPORT_RULES)
        QMessageBox.about(self, APP_NAME, f"<h3>{APP_NAME} {__version__}</h3><p>{self.t('title')}</p>"
                          f"<p>Design: A. Alinaghi · Rule catalogue 03 (229 rules; this version runs {n}).</p>"
                          "<p>Decision-support tool: final acceptance of data for public reporting remains with the "
                          "Competent / Qualified Person.</p><p>Fonts: Vazirmatn and Inter (SIL OFL 1.1).</p>")

    def log(self, msg):
        self.logbox.appendPlainText(msg)


def _load_fonts(app):
    fams = set()
    try:
        folder = resources.files("geovalid_pro.resources").joinpath("fonts")
        for f in folder.iterdir():
            if f.name.lower().endswith((".ttf", ".otf")):
                fid = QFontDatabase.addApplicationFontFromData(f.read_bytes())
                fams.update(QFontDatabase.applicationFontFamilies(fid))
    except Exception:
        pass
    f = QFont()
    f.setFamilies([x for x in ("Vazirmatn", "Inter") if x in fams] or ["Segoe UI"])
    f.setPointSizeF(9.8)
    f.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(f)


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    _load_fonts(app)
    T.register_fonts()
    w = MainWindow()
    w.show()
    if "--smoke-test" in sys.argv:
        out = Path.home() / "GEOVALID_PRO"
        out.mkdir(parents=True, exist_ok=True)
        QTimer.singleShot(500, lambda: (w.load_sample(), w.run()))
        steps = [("dash", None, "gui_smoke.png"), ("geo", "box", "gui_smoke_grade.png"), ("geo", "twoway", "gui_smoke_twoway.png"),
                 ("geo", "strip", "gui_smoke_strip.png"), ("issues", None, "gui_smoke_issues.png"), ("data", None, "gui_smoke_data.png")]

        def step(i):
            if i >= len(steps):
                w.toggle_theme()
                w.go("geo")
                QTimer.singleShot(900, lambda: (w.grab().save(str(out / "gui_smoke_ivory.png")), app.quit()))
                return
            page, chart, name = steps[i]
            w.go(page)
            if chart:
                for r in range(w.chart_list.count()):
                    if w.chart_list.item(r).data(Qt.UserRole) == chart:
                        w.chart_list.setCurrentRow(r)
            QTimer.singleShot(900, lambda: (w.grab().save(str(out / name)), step(i + 1)))

        def check():
            if w.result is not None:
                print("GUI smoke test OK", w.result.issues["severity"].value_counts().to_dict(), flush=True)
                QTimer.singleShot(800, lambda: step(0))
            else:
                QTimer.singleShot(500, check)
        QTimer.singleShot(1500, check)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
