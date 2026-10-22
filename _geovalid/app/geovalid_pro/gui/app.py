"""GEOVALID PRO desktop application (PySide6). Bilingual fa/en, right-to-left layout for Persian."""
from __future__ import annotations

import sys
import traceback
from importlib import resources
from pathlib import Path

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPlainTextEdit,
                               QProgressBar, QPushButton, QScrollArea, QSplitter, QTableView, QTableWidget,
                               QTableWidgetItem, QTabWidget, QTextBrowser, QToolBar, QVBoxLayout, QWidget)

from .. import APP_NAME, __version__
from ..io.mapping import FIELDS, KINDS, propose_mapping

TR = {
    "title": ("اعتبارسنجی پایگاه دادهٔ گمانه‌های اکتشافی", "Exploration drillhole database validation"),
    "add": ("افزودن فایل…", "Add files…"), "remove": ("حذف", "Remove"), "mapping": ("نگاشت فیلدها…", "Field mapping…"),
    "sample": ("دادهٔ نمونه", "Sample data"), "run": ("اجرای اعتبارسنجی", "Run validation"),
    "report": ("باز کردن گزارش", "Open report"), "folder": ("پوشهٔ خروجی", "Output folder"),
    "lang": ("English", "فارسی"), "about": ("دربارهٔ نرم‌افزار", "About"), "thresholds": ("آستانه‌ها…", "Thresholds…"),
    "inputs": ("جدول‌های ورودی", "Input tables"), "optional": ("ورودی‌های اختیاری و خروجی", "Optional inputs and output"),
    "use": ("استفاده", "Use"), "table": ("جدول", "Table"), "type": ("نوع", "Type"), "rows": ("ردیف", "Rows"),
    "mapped": ("نگاشت", "Mapping"), "dem": ("مدل رقومی ارتفاع (DEM: ‎.asc‎ یا ‎.xyz/.csv‎)", "Topography DEM (.asc grid or .xyz/.csv points)"),
    "licence": ("محدودهٔ پروانه (فهرست رئوس x,y)", "Licence boundary (x,y vertex list)"),
    "crm": ("جدول مواد مرجع (crm_id, analyte, certified, sd)", "CRM standards table (crm_id, analyte, certified, sd)"),
    "profile": ("پروفایل اعتبارسنجی (YAML)", "Validation profile (YAML)"), "out": ("پوشهٔ خروجی", "Output folder"),
    "name": ("نام پروژه", "Project name"), "rlang": ("زبان گزارش", "Report language"), "browse": ("…", "…"),
    "summary": ("خلاصه", "Summary"), "issues": ("مسائل", "Issues"), "log": ("گزارش اجرا", "Run log"),
    "critical": ("بحرانی", "Critical"), "error": ("خطا", "Error"), "warning": ("هشدار", "Warning"), "info": ("اطلاعات", "Info"),
    "all": ("همه", "All"), "search": ("جستجو…", "Search…"), "ready": ("آماده", "Ready"),
    "noinput": ("ابتدا فایل‌های پایگاه داده را اضافه کنید.", "Add the database files first."),
    "nocollar": ("هیچ جدول دهانه‌ای (collar) انتخاب نشده است؛ بیشتر قواعد اجرا نمی‌شوند. ادامه می‌دهید؟",
                 "No collar table is selected; most rules will not run. Continue?"),
    "done": ("اعتبارسنجی انجام شد.", "Validation finished."), "failed": ("اجرا با خطا متوقف شد", "Run failed"),
    "rules_run": ("قواعد اجراشده", "Rules run"), "na": ("قابل اجرا نبود", "Not applicable"),
    "detail": ("جزئیات مسئله", "Issue detail"), "by_rule": ("مسائل بر پایهٔ قاعده", "Issues by rule"),
    "never": ("هیچ داده‌ای تغییر داده نمی‌شود؛ خروجی‌ها در پوشهٔ جداگانه نوشته می‌شوند.",
              "Source data are never modified; outputs are written to a separate folder."),
    "depth_unit": ("واحد عمق", "Depth unit"), "analytes": ("ستون‌های عیار شناسایی‌شده", "Detected assay columns"),
    "save_profile": ("ذخیرهٔ پروفایل…", "Save profile…"),
}
SEV_COLORS = {"CRITICAL": "#B2182B", "ERROR": "#E66101", "WARNING": "#C98F00", "INFO": "#3A7FC0"}

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
]


class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame | None = None, cols: list[str] | None = None):
        super().__init__()
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
        if role == Qt.ForegroundRole and col == "severity":
            from PySide6.QtGui import QColor
            return QColor(SEV_COLORS.get(str(v), "#333"))
        if role == Qt.UserRole:
            return v
        return None

    def headerData(self, s, o, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self.df.columns[s]) if o == Qt.Horizontal else str(s + 1)
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
        self.setMinimumWidth(520)
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
            label = f + (" *" if f in req else "")
            form.addRow(label, cb)
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
            lw.setMaximumHeight(140)
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        from ..engine import default_params
        self.lang = "fa"
        self.inputs = []
        self.result = None
        self.worker = None
        self.params = default_params()
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.resize(1360, 860)
        icon = resources.files("geovalid_pro.resources").joinpath("icon.png")
        if icon.is_file():
            self.setWindowIcon(QIcon(str(icon)))
        self._build()
        self.retranslate()

    # ---------------- UI ----------------
    def _build(self):
        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)
        self.a_add, self.a_sample, self.a_run = QAction(self), QAction(self), QAction(self)
        self.a_report, self.a_folder, self.a_thr = QAction(self), QAction(self), QAction(self)
        self.a_lang, self.a_about = QAction(self), QAction(self)
        for a, fn in ((self.a_add, self.add_files), (self.a_sample, self.load_sample), (self.a_run, self.run),
                      (self.a_report, self.open_report), (self.a_folder, self.open_folder), (self.a_thr, self.edit_thresholds),
                      (self.a_lang, self.toggle_lang), (self.a_about, self.about)):
            a.triggered.connect(fn)
            tb.addAction(a)
            if a in (self.a_run, self.a_folder, self.a_thr):
                tb.addSeparator()
        split = QSplitter()
        self.setCentralWidget(split)
        left = QWidget()
        ll = QVBoxLayout(left)
        self.title_lbl = QLabel()
        self.title_lbl.setStyleSheet("font-size:17px;font-weight:600;color:#8A5A2B;padding:4px 0")
        ll.addWidget(self.title_lbl)
        self.g_inputs = QGroupBox()
        gl = QVBoxLayout(self.g_inputs)
        self.tbl = QTableWidget(0, 5)
        self.tbl.setMinimumHeight(230)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        gl.addWidget(self.tbl)
        bl = QHBoxLayout()
        self.b_add, self.b_remove, self.b_map = QPushButton(), QPushButton(), QPushButton()
        self.b_add.clicked.connect(self.add_files)
        self.b_remove.clicked.connect(self.remove_selected)
        self.b_map.clicked.connect(self.edit_mapping)
        for b in (self.b_add, self.b_remove, self.b_map):
            bl.addWidget(b)
        gl.addLayout(bl)
        ll.addWidget(self.g_inputs, 3)
        self.g_opt = QGroupBox()
        og = QGridLayout(self.g_opt)
        self.paths = {}
        self.opt_labels = {}
        for r, key in enumerate(("dem", "licence", "crm", "profile", "out")):
            lab = QLabel()
            le = QLineEdit()
            btn = QPushButton("…")
            btn.setFixedWidth(34)
            btn.clicked.connect(lambda _=False, k=key: self.browse(k))
            lab.setWordWrap(True)
            lab.setMaximumWidth(190)
            og.addWidget(lab, r, 0)
            og.addWidget(le, r, 1)
            og.addWidget(btn, r, 2)
            self.paths[key], self.opt_labels[key] = le, lab
        self.paths["out"].setText(str(Path.home() / "GEOVALID_PRO" / "output"))
        self.l_name, self.e_name = QLabel(), QLineEdit("GEOVALID project")
        self.l_rlang, self.c_rlang = QLabel(), QComboBox()
        self.c_rlang.addItems(["fa", "en", "both"])
        og.addWidget(self.l_name, 5, 0)
        og.addWidget(self.e_name, 5, 1, 1, 2)
        og.addWidget(self.l_rlang, 6, 0)
        og.addWidget(self.c_rlang, 6, 1, 1, 2)
        ll.addWidget(self.g_opt, 0)
        self.b_run = QPushButton()
        self.b_run.setMinimumHeight(40)
        self.b_run.setStyleSheet("QPushButton{background:#8A5A2B;color:white;font-weight:600;border-radius:6px}"
                                 "QPushButton:disabled{background:#B9A28C}")
        self.b_run.clicked.connect(self.run)
        ll.addWidget(self.b_run)
        self.prog = QProgressBar()
        self.prog.setValue(0)
        ll.addWidget(self.prog)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setStyleSheet("color:#5F6B71;font-size:11px")
        ll.addWidget(self.note)
        split.addWidget(left)

        self.tabs = QTabWidget()
        # summary tab
        sw = QWidget()
        sl = QVBoxLayout(sw)
        cards = QHBoxLayout()
        self.cards = {}
        for sev in ("CRITICAL", "ERROR", "WARNING", "INFO"):
            f = QFrame()
            f.setStyleSheet(f"QFrame{{border:1px solid #DDE2E5;border-radius:8px;background:#F4F6F7}}")
            fl = QVBoxLayout(f)
            name, num = QLabel(), QLabel("0")
            num.setStyleSheet(f"font-size:26px;font-weight:700;color:{SEV_COLORS[sev]};border:0")
            name.setStyleSheet("border:0")
            fl.addWidget(name)
            fl.addWidget(num)
            cards.addWidget(f)
            self.cards[sev] = (name, num)
        sl.addLayout(cards)
        self.rules_lbl = QLabel()
        sl.addWidget(self.rules_lbl)
        self.by_rule = QTableView()
        self.by_rule_model = PandasModel()
        self.by_rule.setModel(self.by_rule_model)
        self.by_rule.horizontalHeader().setStretchLastSection(False)
        self.by_rule_lbl = QLabel()
        sl.addWidget(self.by_rule_lbl)
        sl.addWidget(self.by_rule)
        self.tabs.addTab(sw, "")
        # issues tab
        iw = QWidget()
        il = QVBoxLayout(iw)
        fl = QHBoxLayout()
        self.f_sev, self.f_table, self.f_text = QComboBox(), QComboBox(), QLineEdit()
        for w in (self.f_sev, self.f_table):
            w.currentIndexChanged.connect(self.apply_filter)
        self.f_text.textChanged.connect(self.apply_filter)
        fl.addWidget(self.f_sev)
        fl.addWidget(self.f_table)
        fl.addWidget(self.f_text, 1)
        il.addLayout(fl)
        isplit = QSplitter(Qt.Vertical)
        self.iss_view = QTableView()
        self.iss_model = PandasModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.iss_model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.iss_view.setModel(self.proxy)
        self.iss_view.setSortingEnabled(True)
        self.iss_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.iss_view.horizontalHeader().setStretchLastSection(True)
        self.iss_view.selectionModel().selectionChanged.connect(self.show_detail)
        isplit.addWidget(self.iss_view)
        self.detail = QTextBrowser()
        isplit.addWidget(self.detail)
        isplit.setSizes([520, 160])
        il.addWidget(isplit)
        self.tabs.addTab(iw, "")
        # log tab
        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        self.tabs.addTab(self.logbox, "")
        split.addWidget(self.tabs)
        split.setSizes([480, 880])
        self.statusBar()

    def t(self, key):
        return TR[key][0 if self.lang == "fa" else 1]

    def retranslate(self):
        fa = self.lang == "fa"
        QApplication.instance().setLayoutDirection(Qt.RightToLeft if fa else Qt.LeftToRight)
        self.title_lbl.setText(self.t("title"))
        for a, k in ((self.a_add, "add"), (self.a_sample, "sample"), (self.a_run, "run"), (self.a_report, "report"),
                     (self.a_folder, "folder"), (self.a_thr, "thresholds"), (self.a_lang, "lang"), (self.a_about, "about")):
            a.setText(self.t(k))
        self.g_inputs.setTitle(self.t("inputs"))
        self.g_opt.setTitle(self.t("optional"))
        self.tbl.setHorizontalHeaderLabels([self.t(k) for k in ("use", "table", "type", "rows", "mapped")])
        self.b_add.setText(self.t("add"))
        self.b_remove.setText(self.t("remove"))
        self.b_map.setText(self.t("mapping"))
        for k, lab in self.opt_labels.items():
            lab.setText(self.t(k))
        self.l_name.setText(self.t("name"))
        self.l_rlang.setText(self.t("rlang"))
        self.b_run.setText(self.t("run"))
        self.note.setText(self.t("never"))
        for sev, (name, _) in self.cards.items():
            name.setText(self.t(sev.lower()))
        self.tabs.setTabText(0, self.t("summary"))
        self.tabs.setTabText(1, self.t("issues"))
        self.tabs.setTabText(2, self.t("log"))
        self.by_rule_lbl.setText(self.t("by_rule"))
        self.f_text.setPlaceholderText(self.t("search"))
        self.c_rlang.setCurrentText("fa" if fa else "en")
        self._fill_filters()
        self.statusBar().showMessage(self.t("ready"))
        if self.result is not None:
            self.show_result(self.result)

    # ---------------- inputs ----------------
    def refresh_table(self):
        self.tbl.setRowCount(len(self.inputs))
        for r, inp in enumerate(self.inputs):
            cb = QCheckBox()
            cb.setChecked(inp.enabled and inp.kind != "ignore")
            cb.stateChanged.connect(lambda s, i=inp: setattr(i, "enabled", bool(s)))
            self.tbl.setCellWidget(r, 0, cb)
            self.tbl.setItem(r, 1, QTableWidgetItem(inp.name))
            kc = QComboBox()
            kc.addItems(KINDS)
            kc.setCurrentText(inp.kind)
            kc.currentTextChanged.connect(lambda k, i=inp: self.change_kind(i, k))
            self.tbl.setCellWidget(r, 2, kc)
            self.tbl.setItem(r, 3, QTableWidgetItem(str(len(inp.raw.df))))
            req = FIELDS.get(inp.kind, ([], []))[0]
            ok = all(inp.mapping.fields.get(f) for f in req)
            n_an = len(inp.mapping.analytes)
            txt = ("✔" if ok else "✖ " + ", ".join(f for f in req if not inp.mapping.fields.get(f))) + (f"  ({n_an} analytes)" if n_an else "")
            it = QTableWidgetItem(txt)
            it.setForeground(Qt.darkGreen if ok else Qt.red)
            self.tbl.setItem(r, 4, it)
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
        inp = self.inputs[rows[0]]
        dlg = MappingDialog(self, inp, self.lang == "fa")
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
        self._load([str(d / f"{n}.csv") for n in ("collar", "survey", "assay", "lithology", "geotech", "density")])
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

    # ---------------- run ----------------
    def run(self):
        from ..engine import ProjectSpec, load_params, _merge
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
        self.a_run.setEnabled(False)
        self.prog.setValue(0)
        self.worker = Worker(spec, out, self.c_rlang.currentText())
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_progress(self, p, msg):
        self.prog.setValue(p)
        self.statusBar().showMessage(msg)

    def on_done(self, res):
        self.result = res
        self.b_run.setEnabled(True)
        self.a_run.setEnabled(True)
        self.show_result(res)
        self.log(f"{self.t('done')}  {res.outputs.get('folder')}")
        for e in res.errors:
            self.log("! " + e.splitlines()[0] if e.strip() else "")
        self.statusBar().showMessage(f"{self.t('done')}  {res.outputs.get('folder')}")
        self.tabs.setCurrentIndex(0)

    def on_failed(self, tb):
        self.b_run.setEnabled(True)
        self.a_run.setEnabled(True)
        self.log(tb)
        QMessageBox.critical(self, APP_NAME, f"{self.t('failed')}\n\n{tb.splitlines()[-1]}")

    def show_result(self, res):
        iss = res.issues
        counts = iss["severity"].value_counts().to_dict() if not iss.empty else {}
        for sev, (_, num) in self.cards.items():
            num.setText(str(counts.get(sev, 0)))
        st = res.matrix["status"].value_counts().to_dict()
        self.rules_lbl.setText(f"{self.t('rules_run')}: {st.get('RUN', 0)}   ·   {self.t('na')}: {st.get('NOT_APPLICABLE', 0)}"
                               + (f"   ·   FAILED: {st['FAILED']}" if st.get("FAILED") else ""))
        from ..io.writers import summaries
        br = summaries(res)["by_rule"].reset_index()
        if not br.empty:
            title = "title_fa" if self.lang == "fa" else "title_en"
            br = br[["rule_id", title, "CRITICAL", "ERROR", "WARNING", "INFO", "total"]].rename(
                columns={title: self.t("table") if False else ("عنوان قاعده" if self.lang == "fa" else "Rule title"),
                         "CRITICAL": self.t("critical"), "ERROR": self.t("error"), "WARNING": self.t("warning"),
                         "INFO": self.t("info"), "total": "Σ"})
            self.by_rule_model.set(br)
            self.by_rule.resizeColumnsToContents()
        msg = "message_fa" if self.lang == "fa" else "message_en"
        self.iss_model.set(iss, ["issue_id", "severity", "rule_id", "table", "hole_id", "from_m", "to_m", "src_row", msg])
        self.iss_view.resizeColumnsToContents()
        self._fill_filters()

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
        html = (f"<h3 style='color:{SEV_COLORS[r['severity']]}'>{r['severity']} · {r['rule_id']} · {title}</h3>"
                f"<p><b>{f(r['table'])}</b> · {f(r['hole_id'])} {f(r['from_m'])}–{f(r['to_m'])} · row {f(r['src_row'])}</p>"
                f"<p>{f(r['message_fa'])}</p><p dir='ltr'>{f(r['message_en'])}</p>"
                f"<p><i>{f(r['suggested_fix'])}</i></p><p style='color:#777;font-size:11px' dir='ltr'>{meta.get('logic', '')[:600]}</p>"
                f"<p style='color:#777;font-size:11px' dir='ltr'>JORC/NI: {meta.get('jorc', '')} · {meta.get('reference', '')}</p>")
        self.detail.setHtml(html)

    # ---------------- misc ----------------
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

    def toggle_lang(self):
        self.lang = "en" if self.lang == "fa" else "fa"
        self.retranslate()

    def about(self):
        QMessageBox.about(self, APP_NAME, f"<h3>{APP_NAME} {__version__}</h3><p>{self.t('title')}</p>"
                          "<p>Design: A. Alinaghi · Rule catalogue 03 (229 rules; v0.1 implements 74).</p>"
                          "<p>Decision-support tool: final acceptance of data for public reporting remains with the "
                          "Competent / Qualified Person.</p><p>Fonts: Vazirmatn (SIL OFL 1.1).</p>")

    def log(self, msg):
        self.logbox.appendPlainText(msg)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    try:
        data = resources.files("geovalid_pro.resources").joinpath("Vazirmatn.woff2").read_bytes()
        fid = QFontDatabase.addApplicationFontFromData(data)
        fams = QFontDatabase.applicationFontFamilies(fid)
        if fams:
            app.setFont(QFont(fams[0], 10))
    except Exception:
        pass
    w = MainWindow()
    w.show()
    if "--smoke-test" in sys.argv:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, lambda: (w.load_sample(), w.run()))
        def check():
            if w.result is not None:
                print("GUI smoke test OK", w.result.issues["severity"].value_counts().to_dict(), flush=True)
                w.grab().save(str(Path.home() / "GEOVALID_PRO" / "gui_smoke.png"))
                app.quit()
            else:
                QTimer.singleShot(500, check)
        QTimer.singleShot(1500, check)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
