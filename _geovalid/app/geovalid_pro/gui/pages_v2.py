"""v2 pages of the desktop app: Survey QA, Values, Rules & Profiles, Evidence Pack, the fix-approval dialog and the
source-row viewer of the Issue Browser. Mixed into MainWindow (gui/app.py)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTableView,
                               QTableWidget, QTableWidgetItem, QVBoxLayout)
from PySide6.QtCore import QUrl

TR_V2 = {
    "nav_survey": ("کنترل انحراف‌سنجی", "Survey QA"), "nav_values": ("کنترل مقادیر", "Values"),
    "nav_profiles": ("قواعد و پروفایل", "Rules & profiles"), "nav_evidence": ("بستهٔ مستندات", "Evidence pack"),
    "sub_survey": ("انحراف، شدت خمیدگی و حساسیت روش محاسبهٔ مسیر برای هر گمانه", "Deviation, dogleg severity and desurvey sensitivity per hole"),
    "sub_values": ("شیوهٔ ثبت مقادیر زیر حد تشخیص، واحدها و مسائل مقادیر", "Below-detection coding, units and value issues"),
    "sub_profiles": ("فعال‌سازی قواعد، شدت، آستانه‌ها و فهرست کدها؛ ذخیره به‌صورت پروفایل JSON",
                     "Enable rules, set severities, thresholds and code dictionaries; save as a JSON profile"),
    "sub_evidence": ("مستندات راستی‌آزمایی داده‌ها بر پایهٔ بندهای JORC، NI 43-101، S-K 1300 و CIM",
                     "Data verification evidence by JORC, NI 43-101, S-K 1300 and CIM clauses"),
    "sensitivity": ("حساسیت روش محاسبهٔ مسیر (متر)", "Desurvey sensitivity (m)"), "hole_issues": ("مسائل این گمانه", "Issues of this hole"),
    "bdl": ("شیوهٔ ثبت زیر حد تشخیص به تفکیک بچ", "Below-detection coding by batch"), "units": ("واحد عناصر", "Analyte units"),
    "value_issues": ("مسائل مقادیر (دستهٔ E)", "Value issues (category E)"),
    "load_profile": ("بارگذاری پروفایل…", "Load profile…"), "save_profile": ("ذخیرهٔ پروفایل JSON…", "Save JSON profile…"),
    "reset": ("بازگشت به پیش‌فرض", "Reset to defaults"), "load_codes": ("بارگذاری فهرست کدها…", "Load code dictionary…"),
    "edit_params": ("ویرایش آستانه‌ها", "Edit thresholds"), "profile_hash": ("اثرانگشت پروفایل", "Profile hash"),
    "rerun_note": ("تغییرات در اجرای بعدی اعمال می‌شود.", "Changes apply to the next run."),
    "open_ev": ("باز کردن بستهٔ مستندات", "Open evidence pack"), "open_json": ("باز کردن JSON", "Open JSON"),
    "fixes": ("تأیید و اعمال اصلاحات…", "Approve and apply fixes…"), "rebuild": ("بازسازی بستهٔ مستندات", "Rebuild evidence pack"),
    "qp_note": ("سه بخش «روش‌های به‌کاررفته»، «محدودیت‌ها» و «نظر دربارهٔ کفایت» خالی می‌مانند تا شخص صلاحیت‌دار آن‌ها را بنویسد.",
                "The sections “Procedures applied”, “Limitations” and “Opinion on adequacy” are left empty for the Qualified Person."),
    "export": ("خروجی فهرست فیلترشده…", "Export filtered view…"), "all_cat": ("همهٔ دسته‌ها", "All categories"),
    "all_rules": ("همهٔ قواعد", "All rules"), "hole_filter": ("گمانه…", "Hole…"),
    "source": ("ردیف منبع", "Source row"), "fix_title": ("اصلاح با تأیید کاربر", "Approved fixes"),
    "fix_intro": ("هیچ داده‌ای بدون تأیید تغییر نمی‌کند. برای هر دسته از اصلاحات که تأیید کنید، یک نسخهٔ اصلاح‌شده از فایل‌ها و گزارش اصلاح (fix_log.csv) در پوشهٔ خروجی نوشته می‌شود؛ فایل‌های اصلی دست‌نخورده می‌مانند.",
                  "Nothing changes without approval. For each fix class you approve, a corrected copy of the files and a fix log (fix_log.csv) are written to the output folder; the source files stay untouched."),
    "idmap": ("جدول نگاشت شناسهٔ گمانه (فقط ردیف‌های تأییدشده اعمال می‌شوند)", "Hole-ID mapping table (only approved rows are applied)"),
    "user": ("نام تأییدکننده", "Approved by"), "apply": ("اعمال", "Apply"),
    "nofix": ("هیچ مسئلهٔ قابل‌اصلاحی وجود ندارد.", "No issue can be fixed automatically."),
}


def _model_df(model, df):
    model.set(df if df is not None else pd.DataFrame())


class V2Pages:
    """Methods added to MainWindow; they use its helpers (_page_frame, tr_, t, c, chart theme)."""

    # ------------------------------------------------------------------ Survey QA
    def _page_survey(self):
        from .app import ChartView, PandasModel, card, label
        page, lay = self._page_frame("nav_survey", "sub_survey")
        top, tl = card()
        row = QHBoxLayout()
        tl.addLayout(row)
        row.addWidget(self.tr_(label("Muted", 9), "hole"))
        self.sv_hole = QComboBox()
        self.sv_hole.setMinimumWidth(160)
        self.sv_hole.currentIndexChanged.connect(lambda *_: self._draw_survey())
        row.addWidget(self.sv_hole)
        row.addStretch(1)
        self.sv_info = label("Muted", 9)
        row.addWidget(self.sv_info)
        lay.addWidget(top)
        sp = QSplitter(Qt.Horizontal)
        cc, cl = card()
        self.sv_chart = ChartView()
        cl.addWidget(self.sv_chart, 1)
        sp.addWidget(cc)
        rc, rl = card()
        rl.addWidget(self.tr_(label("H2", 11), "sensitivity"))
        self.sv_sens_model = PandasModel()
        self.sv_sens = self._table_view(self.sv_sens_model)
        rl.addWidget(self.sv_sens, 1)
        rl.addWidget(self.tr_(label("H2", 11), "hole_issues"))
        self.sv_iss_model = PandasModel()
        self.sv_iss = self._table_view(self.sv_iss_model)
        rl.addWidget(self.sv_iss, 1)
        sp.addWidget(rc)
        sp.setSizes([760, 420])
        lay.addWidget(sp, 1)
        return page

    def _fill_survey(self):
        res = self.result
        if res is None:
            return
        sens = res.ctx.stats.get("desurvey_sensitivity")
        order = []
        if sens is not None and not sens.empty:
            s = sens.sort_values("max_m", ascending=False)
            _model_df(self.sv_sens_model, s.round(3))
            order = list(s["hole_id"])
        if res.ctx.survey is not None:
            order += [h for h in res.ctx.survey.df["hole_id"].dropna().unique() if h not in order]
        cur = self.sv_hole.currentText()
        self.sv_hole.blockSignals(True)
        self.sv_hole.clear()
        self.sv_hole.addItems([str(h) for h in order])
        if cur in order:
            self.sv_hole.setCurrentText(cur)
        self.sv_hole.blockSignals(False)
        self._draw_survey()

    def _draw_survey(self):
        from ..report import charts as K
        res = self.result
        if res is None or res.ctx.survey is None or not self.sv_hole.currentText():
            return
        h = self.sv_hole.currentText()
        p = res.ctx.p("SUR-010")
        self.sv_chart.show_figure(K.survey_qa(res.ctx.survey.df, h, p.get("warn_deg_30m", 3), p.get("error_deg_30m", 6), self.lang, self.chart_theme),
                                  self.t("nodata"))
        iss = res.issues
        sub = iss[(iss["hole_id"] == h) & (iss["category"] == "C")] if not iss.empty else iss
        msg = "message_fa" if self.lang == "fa" else "message_en"
        _model_df(self.sv_iss_model, sub[["severity", "rule_id", "from_m", msg]] if not sub.empty else pd.DataFrame())
        n = len(res.ctx.survey.df[res.ctx.survey.df["hole_id"] == h])
        self.sv_info.setText(f"{n} {'ایستگاه' if self.lang == 'fa' else 'stations'} · {len(sub)} {'مسئله' if self.lang == 'fa' else 'issues'}")

    # ------------------------------------------------------------------ Values
    def _page_values(self):
        from .app import PandasModel, card, label
        page, lay = self._page_frame("nav_values", "sub_values")
        sp = QSplitter(Qt.Vertical)
        top = QSplitter(Qt.Horizontal)
        c1, l1 = card()
        l1.addWidget(self.tr_(label("H2", 11), "bdl"))
        self.va_bdl_model = PandasModel()
        l1.addWidget(self._table_view(self.va_bdl_model), 1)
        c2, l2 = card()
        l2.addWidget(self.tr_(label("H2", 11), "units"))
        self.va_units_model = PandasModel()
        l2.addWidget(self._table_view(self.va_units_model), 1)
        top.addWidget(c1)
        top.addWidget(c2)
        c3, l3 = card()
        l3.addWidget(self.tr_(label("H2", 11), "value_issues"))
        self.va_iss_model = PandasModel()
        l3.addWidget(self._table_view(self.va_iss_model), 1)
        sp.addWidget(top)
        sp.addWidget(c3)
        lay.addWidget(sp, 1)
        return page

    def _fill_values(self):
        res = self.result
        if res is None:
            return
        inv = res.ctx.stats.get("bdl_inventory")
        if inv:
            df = pd.concat(inv, ignore_index=True)[["table", "column", "analyte", "form", "batch", "n"]]
            _model_df(self.va_bdl_model, df)
        ast = res.ctx.stats.get("assay_stats")
        if ast is not None and not ast.empty:
            _model_df(self.va_units_model, ast[["table", "column", "analyte", "unit", "unit_source", "n", "pct_bdl"]])
        iss = res.issues
        msg = "message_fa" if self.lang == "fa" else "message_en"
        sub = iss[iss["category"] == "E"] if not iss.empty else iss
        if not sub.empty:
            _model_df(self.va_iss_model, sub[["severity", "rule_id", "rule_alias", "table", "hole_id", "from_m", "src_row", msg]])

    # ------------------------------------------------------------------ Rules & Profiles
    def _page_profiles(self):
        from .app import card, label
        page, lay = self._page_frame("nav_profiles", "sub_profiles")
        bc, bl0 = card()
        bl = QHBoxLayout()
        bl0.addLayout(bl)
        self.pr_btns = {}
        for k, fn in (("load_profile", self._load_profile), ("save_profile", self._save_profile), ("load_codes", self._load_codes),
                      ("edit_params", self._edit_params), ("reset", self._reset_profile)):
            b = QPushButton()
            b.clicked.connect(fn)
            self.tr_(b, k)
            bl.addWidget(b)
            self.pr_btns[k] = b
        bl.addStretch(1)
        self.pr_hash = label("Muted", 8.5)
        bl.addWidget(self.pr_hash)
        lay.addWidget(bc)
        tc, tl = card()
        self.pr_note = self.tr_(label("Muted", 9), "rerun_note")
        tl.addWidget(self.pr_note)
        self.pr_tbl = QTableWidget(0, 8)
        self.pr_tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pr_tbl.verticalHeader().setVisible(False)
        self.pr_tbl.setAlternatingRowColors(True)
        self.pr_tbl.setShowGrid(False)
        tl.addWidget(self.pr_tbl, 1)
        lay.addWidget(tc, 1)
        self._fill_profiles()
        return page

    def _rule_ids(self):
        from ..engine import IMPORT_RULES
        from ..rules import REGISTRY
        return list(dict.fromkeys(IMPORT_RULES + [r.id for r in REGISTRY]))

    def _fill_profiles(self):
        from ..core.registry import describe, profile_hash
        fa = self.lang == "fa"
        ids = sorted(self._rule_ids(), key=lambda r: (describe(r)["category"], r))
        heads = ["", "ID", "v2", "Cat.", "نام قاعده" if fa else "Rule", "پیش‌فرض" if fa else "Catalogue severity",
                 "شدت جدید" if fa else "Severity override", "آستانه‌ها" if fa else "Thresholds"]
        self.pr_tbl.blockSignals(True)
        self.pr_tbl.setRowCount(len(ids))
        self.pr_tbl.setHorizontalHeaderLabels(heads)
        for r, rid in enumerate(ids):
            d = describe(rid, self.params)
            cb = QCheckBox()
            cb.setChecked(d["enabled"])
            cb.stateChanged.connect(lambda s, rid=rid: self._set_enabled(rid, bool(s)))
            self.pr_tbl.setCellWidget(r, 0, cb)
            for c, v in enumerate([rid, ", ".join(d["aliases"]), d["category"], d["name_fa"] if fa else d["name_en"], d["default_severity"]], 1):
                it = QTableWidgetItem(str(v))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if c == 4:
                    it.setToolTip(d["logic"][:900])
                self.pr_tbl.setItem(r, c, it)
            ov = d["severity_override"]
            combo = QComboBox()
            combo.addItems(["—", "CRITICAL", "ERROR", "WARNING", "INFO"])
            if isinstance(ov, str):
                combo.setCurrentText(ov)
            elif isinstance(ov, dict):
                combo.addItem(", ".join(f"{a}→{b}" for a, b in ov.items()))
                combo.setCurrentIndex(combo.count() - 1)
            combo.currentTextChanged.connect(lambda v, rid=rid: self._set_override(rid, v))
            self.pr_tbl.setCellWidget(r, 6, combo)
            it = QTableWidgetItem(json.dumps(d["parameters"], ensure_ascii=False) if d["parameters"] else "")
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.pr_tbl.setItem(r, 7, it)
        self.pr_tbl.resizeColumnsToContents()
        self.pr_tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.pr_tbl.setColumnWidth(7, 260)
        self.pr_tbl.blockSignals(False)
        self.pr_hash.setText(f"{self.t('profile_hash')}: {profile_hash(self.params)[:16]}…")

    def _set_enabled(self, rid, on):
        dis = set(self.params.get("disabled_rules") or [])
        (dis.discard if on else dis.add)(rid)
        self.params["disabled_rules"] = sorted(dis)
        self._fill_profile_hash()

    def _set_override(self, rid, v):
        ov = dict(self.params.get("severity_overrides") or {})
        if v == "—":
            ov.pop(rid, None)
        elif v in ("CRITICAL", "ERROR", "WARNING", "INFO"):
            ov[rid] = v
        self.params["severity_overrides"] = ov
        self._fill_profile_hash()

    def _fill_profile_hash(self):
        from ..core.registry import profile_hash
        self.pr_hash.setText(f"{self.t('profile_hash')}: {profile_hash(self.params)[:16]}…")

    def _selected_rule(self):
        rows = sorted({i.row() for i in self.pr_tbl.selectedIndexes()})
        return self.pr_tbl.item(rows[0], 1).text() if rows else None

    def _edit_params(self):
        rid = self._selected_rule()
        if not rid:
            return
        cur = (self.params.get("rules") or {}).get(rid, {})
        dlg = QDialog(self)
        dlg.setWindowTitle(f"{rid} — {self.t('edit_params')}")
        dlg.resize(560, 360)
        v = QVBoxLayout(dlg)
        from ..core.registry import describe
        d = describe(rid, self.params)
        info = QLabel(d["logic"][:700])
        info.setWordWrap(True)
        info.setObjectName("Muted")
        v.addWidget(info)
        ed = QPlainTextEdit(json.dumps(cur, ensure_ascii=False, indent=1))
        v.addWidget(ed, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        v.addWidget(bb)
        if dlg.exec():
            try:
                val = json.loads(ed.toPlainText() or "{}")
                if not isinstance(val, dict):
                    raise ValueError("a JSON object is expected")
            except Exception as e:
                QMessageBox.warning(self, rid, str(e))
                return
            self.params.setdefault("rules", {})[rid] = val
            self._fill_profiles()

    def _load_profile(self):
        from ..engine import load_params
        f, _ = QFileDialog.getOpenFileName(self, self.t("load_profile"), "", "Profile (*.json *.yaml *.yml)")
        if not f:
            return
        try:
            self.params = load_params(f)
        except Exception as e:
            QMessageBox.critical(self, "Profile", str(e))
            return
        self.paths["profile"].setText("")
        self._fill_profiles()
        self.log(f"profile loaded: {f}")

    def _save_profile(self):
        from ..engine import save_profile
        f, _ = QFileDialog.getSaveFileName(self, self.t("save_profile"), "geovalid_profile.json", "JSON (*.json)")
        if f:
            h = save_profile(self.params, f)
            self.log(f"profile saved: {f}  (hash {h[:16]})")

    def _load_codes(self):
        from ..io.codes import read_code_dictionary
        f, _ = QFileDialog.getOpenFileName(self, self.t("load_codes"), "", "Tables (*.csv *.txt *.xlsx *.xls)")
        if not f:
            return
        try:
            d = read_code_dictionary(f)
        except Exception as e:
            QMessageBox.critical(self, "Codes", str(e))
            return
        cd = self.params.setdefault("code_dictionaries", {})
        for k, v in d.items():
            cd[k] = sorted(set(cd.get(k, [])) | set(v))
        self._fill_profile_hash()
        self.log(f"code dictionary loaded: {f} → " + ", ".join(f"{k} ({len(v)})" for k, v in d.items()))

    def _reset_profile(self):
        from ..engine import default_params
        self.params = default_params()
        self._fill_profiles()

    # ------------------------------------------------------------------ Evidence pack
    def _page_evidence(self):
        from .app import PandasModel, card, label
        page, lay = self._page_frame("nav_evidence", "sub_evidence")
        bc, bl0 = card()
        bl = QHBoxLayout()
        bl0.addLayout(bl)
        for k, fn in (("open_ev", self._open_evidence), ("open_json", self._open_evidence_json), ("fixes", self._fix_dialog),
                      ("rebuild", self._rebuild_evidence)):
            b = QPushButton()
            b.clicked.connect(fn)
            self.tr_(b, k)
            bl.addWidget(b)
        bl.addStretch(1)
        lay.addWidget(bc)
        note = self.tr_(label("Muted", 9), "qp_note")
        note.setWordWrap(True)
        lay.addWidget(note)
        tc, tl = card()
        self.ev_model = PandasModel()
        self.ev_tbl = self._table_view(self.ev_model)
        tl.addWidget(self.ev_tbl, 1)
        lay.addWidget(tc, 1)
        return page

    def _fill_evidence(self):
        from ..report import evidence
        res = self.result
        if res is None:
            return
        pack = evidence.build(res)
        rows = []
        for c in pack["clauses"]:
            rows.append({"clause": c["tag"], "title": c["title"], "checks": len(c["rules"]), "PASS": c["results"]["PASS"],
                         "FAIL": c["results"]["FAIL"], "N/A": c["results"]["NOT_APPLICABLE"],
                         **{k: v for k, v in c["open_issues"].items()}})
        _model_df(self.ev_model, pd.DataFrame(rows))
        self.ev_tbl.resizeColumnsToContents()

    def _open_evidence(self):
        o = self.result.outputs if self.result is not None else {}
        p = o.get(f"evidence_{self.lang}") or o.get("evidence_en") or o.get("evidence_fa")
        if p:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    def _open_evidence_json(self):
        p = (self.result.outputs if self.result is not None else {}).get("evidence_json")
        if p:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    def _rebuild_evidence(self):
        from ..report import evidence
        res = self.result
        if res is None or not res.outputs.get("folder"):
            return
        files = evidence.write(res, res.outputs["folder"], self.c_rlang.currentText())
        res.outputs.update(files)
        self._fill_evidence()
        self.log(f"evidence pack rebuilt: {res.outputs['folder']}")

    # ------------------------------------------------------------------ fix approval
    def _fix_dialog(self):
        from ..core import fixes
        res = self.result
        if res is None:
            return
        cand = fixes.candidates(res)
        if cand.empty:
            QMessageBox.information(self, self.t("fix_title"), self.t("nofix"))
            return
        fa = self.lang == "fa"
        dlg = QDialog(self)
        dlg.setWindowTitle(self.t("fix_title"))
        dlg.resize(860, 600)
        v = QVBoxLayout(dlg)
        intro = QLabel(self.t("fix_intro"))
        intro.setWordWrap(True)
        v.addWidget(intro)
        boxes = {}
        for r in cand.itertuples():
            fc = fixes.FIX_CLASSES.get(r.fix_class)
            if fc is None:
                continue
            cb = QCheckBox(f"{fc.id} — {fc.title_fa if fa else fc.title_en}  ({r.n_issues})")
            cb.setToolTip(fc.description)
            v.addWidget(cb)
            d = QLabel(fc.description)
            d.setObjectName("Muted")
            d.setWordWrap(True)
            v.addWidget(d)
            boxes[fc.id] = cb
        idm = fixes.suggested_id_map(res)
        tbl = None
        if "ID_MAP" in boxes and not idm.empty:
            v.addWidget(QLabel(self.t("idmap")))
            tbl = QTableWidget(len(idm), 5)
            tbl.setHorizontalHeaderLabels(["raw_id", "target_id", "approved", "tables", "rows"])
            for i, r in enumerate(idm.itertuples()):
                tbl.setItem(i, 0, QTableWidgetItem(str(r.raw_id)))
                tbl.setItem(i, 1, QTableWidgetItem(str(r.target_id)))
                ok = QTableWidgetItem()
                ok.setFlags(ok.flags() | Qt.ItemIsUserCheckable)
                ok.setCheckState(Qt.Unchecked)
                tbl.setItem(i, 2, ok)
                tbl.setItem(i, 3, QTableWidgetItem(str(r.tables)))
                tbl.setItem(i, 4, QTableWidgetItem(str(r.rows)))
            tbl.resizeColumnsToContents()
            v.addWidget(tbl, 1)
        urow = QHBoxLayout()
        urow.addWidget(QLabel(self.t("user")))
        import getpass
        user = QLineEdit(getpass.getuser())
        urow.addWidget(user, 1)
        v.addLayout(urow)
        bb = QDialogButtonBox(QDialogButtonBox.Cancel)
        apply_b = bb.addButton(self.t("apply"), QDialogButtonBox.AcceptRole)
        apply_b.setObjectName("Primary")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        v.addWidget(bb)
        if not dlg.exec():
            return
        approved = [k for k, cb in boxes.items() if cb.isChecked()]
        if not approved:
            return
        id_map = None
        if tbl is not None:
            id_map = pd.DataFrame([{"raw_id": tbl.item(i, 0).text(), "target_id": tbl.item(i, 1).text(),
                                    "approved": tbl.item(i, 2).checkState() == Qt.Checked} for i in range(tbl.rowCount())])
        out = Path(res.outputs.get("folder") or Path(self.paths["out"].text())) / "corrected"
        r = fixes.apply_fixes(res, approved, str(out), id_map, user.text().strip() or None)
        self._rebuild_evidence()
        self.log(f"fixes applied: {', '.join(approved)} — {r['n']} changes; corrected copies in {out}")
        QMessageBox.information(self, self.t("fix_title"), f"{r['n']} {'تغییر' if fa else 'changes'} → {out}")

    # ------------------------------------------------------------------ issue browser additions
    def _export_issues(self):
        if self.result is None:
            return
        f, _ = QFileDialog.getSaveFileName(self, self.t("export"), "issues_filtered.csv", "CSV (*.csv);;Excel (*.xlsx)")
        if not f:
            return
        rows = [self.proxy.mapToSource(self.proxy.index(i, 0)).row() for i in range(self.proxy.rowCount())]
        ids = self.iss_model.df.iloc[rows]["issue_id"] if rows else []
        df = self.result.issues[self.result.issues["issue_id"].isin(ids)]
        (df.to_excel(f, index=False) if f.lower().endswith(".xlsx") else df.to_csv(f, index=False, encoding="utf-8-sig"))
        self.log(f"exported {len(df)} issues: {f}")

    def _show_source(self, idx):
        """Double-click in the Issue Browser: the source file, the line, and the raw row with its neighbours."""
        res = self.result
        if res is None:
            return
        src = self.proxy.mapToSource(idx)
        iid = self.iss_model.df.iloc[src.row()]["issue_id"]
        r = res.issues.set_index("issue_id").loc[iid]
        tab = str(r["table"]) if isinstance(r["table"], str) else ""
        inp = next((i for i in res.spec.inputs if i.name in tab.split("+")), None)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"{self.t('source')} — {iid}")
        dlg.resize(980, 380)
        v = QVBoxLayout(dlg)
        row = r.get("src_row")
        head = QLabel(f"<b>{r['rule_id']}</b> · {r['severity']} · {r.get('source_file') or ''} · "
                      f"{'ردیف' if self.lang == 'fa' else 'line'} {int(row) if pd.notna(row) else '—'}")
        v.addWidget(head)
        tv = QTableView()
        from .app import PandasModel
        m = PandasModel()
        if inp is not None and pd.notna(row):
            i = int(row) - 2
            df = inp.raw.df
            lo, hi = max(0, i - 3), min(len(df), i + 4)
            view = df.iloc[lo:hi].copy()
            view.insert(0, "line", [k + 2 for k in range(lo, hi)])
            m.set(view)
            tv.setModel(m)
            tv.selectRow(i - lo)
        elif inp is not None and isinstance(r.get("hole_id"), str):
            c = inp.mapping.fields.get("hole_id")
            df = inp.raw.df
            view = df[df[c].astype("string").str.strip() == r["hole_id"]].head(50).copy() if c in df else df.head(0)
            view.insert(0, "line", view.index + 2)
            m.set(view)
            tv.setModel(m)
        v.addWidget(tv, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(dlg.reject)
        v.addWidget(bb)
        dlg.exec()

    def _refresh_v2(self):
        for fn in (self._fill_survey, self._fill_values, self._fill_evidence, self._fill_profiles):
            try:
                fn()
            except Exception as e:      # a page that cannot be filled must not stop the others
                self.log(f"! {fn.__name__}: {e}")
