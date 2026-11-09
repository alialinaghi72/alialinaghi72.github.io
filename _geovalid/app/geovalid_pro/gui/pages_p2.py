"""Phase 2 pages of the desktop app: Cross-table, Lab & QA/QC, Topography & boundary, Versions; the mineralised /
barren code dialog, the random-audit export and import, and the accepted-snapshot dialog. Mixed into MainWindow."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QMessageBox, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout)

TR_P2 = {
    "nav_xtable": ("سازگاری جدول‌ها", "Cross-table"), "nav_lab": ("آزمایشگاه و QA/QC", "Lab & QA/QC"),
    "nav_topo": ("توپوگرافی و محدوده", "Topography & boundary"), "nav_versions": ("نسخه‌ها", "Versions"),
    "sub_xtable": ("زون کانه‌دار بدون آنالیز، پوشش جدول‌ها، وارونگی هوازدگی، عیار در واحد بی‌کانه، بازیافت و چگالی",
                   "Mineralised zones without assays, table coverage, weathering inversions, grade in barren units, recovery and density"),
    "sub_lab": ("تطبیق پایگاه داده با فایل آزمایشگاه (GEOQAQC)، مواد مرجع، نمونه‌های تکراری، آزمایشگاه داور و ممیزی تصادفی",
                "Database vs laboratory file (GEOQAQC), CRMs, duplicates, umpire laboratory and the random audit"),
    "sub_topo": ("خواندن توپوگرافی و محدودهٔ پروانه، بررسی‌های اولیهٔ سیستم مختصات و اختلاف ارتفاع دهانه‌ها",
                 "Topography and licence boundary as read, coordinate sanity checks and collar elevation differences"),
    "sub_versions": ("تغییرات نسبت به نسخهٔ قبلی، تغییر فلز، و تصویرهای پذیرفته‌شده با گمانه‌های قفل‌شده",
                     "Changes since the previous version, metal change, and accepted snapshots with locked holes"),
    "lab": ("فایل آزمایشگاه / QA-QC (GEOQAQC)", "Laboratory / QA-QC file (GEOQAQC)"), "umpire": ("فایل آزمایشگاه داور", "Umpire laboratory file"),
    "baseline": ("پوشهٔ نسخهٔ قبلی داده‌ها", "Previous version (folder)"), "snapshot": ("تصویر پذیرفته‌شده (JSON)", "Accepted snapshot (JSON)"),
    "set_codes": ("کدهای کانه‌دار و بی‌کانه…", "Mineralised / barren codes…"), "coverage": ("پوشش جدول‌ها", "Table coverage"),
    "issues_f": ("مسائل سازگاری جدول‌ها (دستهٔ F)", "Cross-table issues (category F)"),
    "audit_export": ("خروجی چک‌لیست ممیزی…", "Export audit checklist…"), "audit_import": ("ورود نتایج ممیزی…", "Import audit results…"),
    "recon": ("پایگاه داده در برابر آزمایشگاه", "Database vs laboratory"), "issues_g": ("مسائل آزمایشگاه و QA/QC (دستهٔ G)", "Lab and QA/QC issues (category G)"),
    "topo_info": ("آنچه خوانده شد", "What was read"), "issues_topo": ("مسائل توپوگرافی و محدوده", "Topography and boundary issues"),
    "accept": ("پذیرش این نسخه (تصویر)…", "Accept this version (snapshot)…"), "export_log": ("خروجی گزارش تغییرات…", "Export change log…"),
    "classes": ("گونه‌های تغییر", "Change classes"), "change_log": ("گزارش تغییرات", "Change log"), "all_classes": ("همهٔ گونه‌ها", "All classes"),
    "reviewer": ("نام بازبین", "Reviewer"), "note_": ("یادداشت", "Note"), "lock": ("گمانه‌های قفل‌شده", "Locked holes"),
    "lock_all": ("همهٔ گمانه‌ها", "All holes"), "lock_none": ("هیچ‌کدام", "None"), "lock_list": ("فهرست (با کاما)", "List (comma-separated)"),
    "mineralised": ("کانه‌دار", "Mineralised"), "barren": ("بی‌کانه", "Barren"), "field": ("فیلد", "Field"), "code": ("کد", "Code"),
    "metres": ("متر", "Metres"), "no_version": ("نسخهٔ قبلی یا تصویر پذیرفته‌شده‌ای داده نشده است.", "No previous version or accepted snapshot was given."),
    "no_lab": ("فایل آزمایشگاه داده نشده است؛ QA/QC از جدول آنالیز پایگاه داده محاسبه شده است.", "No laboratory file given; QA/QC was computed from the database assay table."),
    "chart_recon": ("تطبیق با آزمایشگاه", "Lab reconciliation"), "chart_crm": ("نمودار کنترل CRM", "CRM control chart"),
    "chart_ump": ("آزمایشگاه داور", "Umpire laboratory"), "chart_hard": ("دقت نمونه‌های تکراری", "Duplicate precision"),
    "chart_dz": ("اختلاف ارتفاع دهانه‌ها", "Collar ΔZ"), "chart_map": ("نقشهٔ دهانه‌ها و محدوده", "Collars and licence"),
}

XT_RULES = ["ASY-008", "INT-011", "WTH-001", "CRS-001", "GEO-001", "GEO-002", "DEN-001"]
LAB_RULES = ["SMP-004", "ASY-020", "ASY-009", "CRS-008", "QAQ-001", "QAQ-002", "QAQ-003", "QAQ-004", "QAQ-006", "QAQ-007", "QAQ-008", "QAQ-010", "SMP-002"]
TOPO_RULES = ["COL-025", "COL-011", "COL-012", "COL-005", "SUR-016"]


class P2Pages:
    """Phase 2 pages; they use MainWindow's helpers (_page_frame, _table_view, tr_, t, chart_theme, log)."""

    def _issue_subset(self, rules):
        res = self.result
        if res is None or res.issues.empty:
            return pd.DataFrame()
        i = res.issues[res.issues["rule_id"].isin(rules)]
        msg = "message_fa" if self.lang == "fa" else "message_en"
        return i[["severity", "rule_id", "rule_alias", "hole_id", "from_m", "to_m", msg]]

    def _fit(self, view, max_w=520):
        view.resizeColumnsToContents()
        for c in range(view.model().columnCount()):
            if view.columnWidth(c) > max_w:
                view.setColumnWidth(c, max_w)

    # ------------------------------------------------------------------ Cross-table
    def _page_xtable(self):
        from .app import ChartView, PandasModel, card, label
        page, lay = self._page_frame("nav_xtable", "sub_xtable")
        bc, bl0 = card()
        bl = QHBoxLayout()
        bl0.addLayout(bl)
        b = QPushButton()
        b.clicked.connect(self._codes_dialog)
        self.tr_(b, "set_codes")
        bl.addWidget(b)
        self.xt_info = label("Muted", 9)
        self.xt_info.setWordWrap(True)
        bl.addWidget(self.xt_info, 1)
        lay.addWidget(bc)
        sp = QSplitter(Qt.Horizontal)
        cc, cl = card()
        cl.addWidget(self.tr_(label("H2", 11), "coverage"))
        self.xt_chart = ChartView()
        cl.addWidget(self.xt_chart, 1)
        sp.addWidget(cc)
        rc, rl = card()
        rl.addWidget(self.tr_(label("H2", 11), "issues_f"))
        self.xt_model = PandasModel()
        self.xt_view = self._table_view(self.xt_model)
        rl.addWidget(self.xt_view, 1)
        sp.addWidget(rc)
        sp.setSizes([560, 620])
        lay.addWidget(sp, 1)
        return page

    def _fill_xtable(self):
        from ..report import charts as K
        res = self.result
        if res is None:
            return
        self.xt_chart.show_figure(K.coverage_heatmap(res.ctx.stats.get("coverage"), self.lang, self.chart_theme), self.t("nodata"))
        self.xt_model.set(self._issue_subset(XT_RULES))
        self._fit(self.xt_view)
        mc = res.ctx.params.get("mineralised_codes") or {}
        bc = res.ctx.params.get("barren_codes") or {}
        fmt = lambda d: "; ".join(f"{k}: {', '.join(map(str, v))}" for k, v in d.items() if v) or "—"
        cov = res.ctx.stats.get("mineralised_assay_coverage")
        extra = f" · {cov['unassayed_m']:.1f} / {cov['logged_m']:.1f} m" if cov else ""
        self.xt_info.setText(f"{self.t('mineralised')}: {fmt(mc)}   ·   {self.t('barren')}: {fmt(bc)}{extra}")

    def _codes_dialog(self):
        """Pick the project's mineralised and barren codes from the codes actually logged (no inference from names)."""
        res = self.result
        rows = []
        if res is not None:
            for t in res.ctx.tables:
                if not t.is_interval or t.kind in ("assay", "density"):
                    continue
                for f in ("lith_code", "alt_type", "weathering"):
                    if f in t.df:
                        d = t.df[[f, "from_m", "to_m"]].dropna()
                        for code, g in d.groupby(d[f].astype(str).str.strip()):
                            rows.append((f, code, float((g["to_m"] - g["from_m"]).sum())))
        if not rows:
            QMessageBox.information(self, self.t("set_codes"), self.t("nodata"))
            return
        rows = sorted(set(rows), key=lambda r: (r[0], -r[2]))
        mc = {f: {str(c).upper() for c in v} for f, v in (self.params.get("mineralised_codes") or {}).items()}
        bc = {f: {str(c).upper() for c in v} for f, v in (self.params.get("barren_codes") or {}).items()}
        dlg = QDialog(self)
        dlg.setWindowTitle(self.t("set_codes"))
        dlg.resize(560, 560)
        v = QVBoxLayout(dlg)
        tw = QTableWidget(len(rows), 5)
        tw.setHorizontalHeaderLabels([self.t("field"), self.t("code"), self.t("metres"), self.t("mineralised"), self.t("barren")])
        for r, (f, code, m) in enumerate(rows):
            tw.setItem(r, 0, QTableWidgetItem(f))
            tw.setItem(r, 1, QTableWidgetItem(code))
            tw.setItem(r, 2, QTableWidgetItem(f"{m:,.1f}"))
            for col, src in ((3, mc), (4, bc)):
                it = QTableWidgetItem()
                it.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                it.setCheckState(Qt.Checked if code.upper() in src.get(f, set()) else Qt.Unchecked)
                tw.setItem(r, col, it)
        tw.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        v.addWidget(tw, 1)
        note = QLabel(self.t("rerun_note"))
        v.addWidget(note)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        v.addWidget(bb)
        if not dlg.exec():
            return
        new_m, new_b = {}, {}
        for r, (f, code, _) in enumerate(rows):
            if tw.item(r, 3).checkState() == Qt.Checked:
                new_m.setdefault(f, []).append(code)
            if tw.item(r, 4).checkState() == Qt.Checked:
                new_b.setdefault(f, []).append(code)
        self.params["mineralised_codes"], self.params["barren_codes"] = new_m, new_b
        self.log(f"mineralised codes: {new_m}; barren codes: {new_b} ({self.t('rerun_note')})")
        self._fill_xtable()

    # ------------------------------------------------------------------ Lab & QA/QC
    def _page_lab(self):
        from .app import ChartView, PandasModel, card, label
        page, lay = self._page_frame("nav_lab", "sub_lab")
        bc, bl0 = card()
        bl = QHBoxLayout()
        bl0.addLayout(bl)
        for k, fn in (("audit_export", self._audit_export), ("audit_import", self._audit_import)):
            b = QPushButton()
            b.clicked.connect(fn)
            self.tr_(b, k)
            bl.addWidget(b)
        self.lab_info = label("Muted", 9)
        self.lab_info.setWordWrap(True)
        bl.addWidget(self.lab_info, 1)
        lay.addWidget(bc)
        sp = QSplitter(Qt.Horizontal)
        cc, cl = card()
        self.lab_sel = QComboBox()
        self.lab_sel.currentIndexChanged.connect(lambda *_: self._draw_lab())
        cl.addWidget(self.lab_sel)
        self.lab_chart = ChartView()
        cl.addWidget(self.lab_chart, 1)
        sp.addWidget(cc)
        rc, rl = card()
        rl.addWidget(self.tr_(label("H2", 11), "recon"))
        self.lab_rec_model = PandasModel()
        self.lab_rec = self._table_view(self.lab_rec_model)
        rl.addWidget(self.lab_rec, 1)
        rl.addWidget(self.tr_(label("H2", 11), "issues_g"))
        self.lab_iss_model = PandasModel()
        self.lab_iss = self._table_view(self.lab_iss_model)
        rl.addWidget(self.lab_iss, 2)
        sp.addWidget(rc)
        sp.setSizes([600, 600])
        lay.addWidget(sp, 1)
        return page

    def _fill_lab(self):
        res = self.result
        if res is None:
            return
        st = res.ctx.stats
        rec = st.get("lab_reconciliation") or {}
        cur = self.lab_sel.currentData()
        self.lab_sel.blockSignals(True)
        self.lab_sel.clear()
        for key in ("recon", "crm", "ump", "hard"):
            self.lab_sel.addItem(self.t("chart_" + key), key)
        if cur:
            i = self.lab_sel.findData(cur)
            self.lab_sel.setCurrentIndex(max(i, 0))
        self.lab_sel.blockSignals(False)
        self.lab_rec_model.set(pd.DataFrame(rec.get("values") or []))
        self._fit(self.lab_rec, 200)
        self.lab_iss_model.set(self._issue_subset(LAB_RULES))
        self._fit(self.lab_iss)
        parts = []
        if not rec:
            parts.append(self.t("no_lab"))
        else:
            s = rec.get("samples", {})
            er = rec.get("error_rate") or {}
            parts.append(f"{rec.get('lab_file')}: {s.get('lab_rows', 0):,} rows · {s.get('lab_routine_not_in_db', 0)} not in DB · "
                         f"{s.get('db_samples_not_in_lab', 0)} DB samples not in the lab file")
            if er:
                parts.append(f"error rate {er['rate_pct']:.2f} % (95 % upper {er['upper95_pct']:.2f} %) on {er['compared']:,} values")
        ra = st.get("random_audit") or {}
        if ra:
            parts.append(f"audit: {ra.get('status')}")
        self.lab_info.setText("   ·   ".join(parts))
        self._draw_lab()

    def _draw_lab(self):
        from ..report import charts as K
        res = self.result
        if res is None:
            return
        key = self.lab_sel.currentData() or "recon"
        st, th, lg = res.ctx.stats, self.chart_theme, self.lang
        if key == "recon":
            fig = K.reconciliation_bar((st.get("lab_reconciliation") or {}).get("values"), lg, th)
        elif key == "crm":
            s = st.get("crm_results") or {}
            fig = K.crm_chart(pd.concat(s.values(), ignore_index=True), lg, th) if s else None
        elif key == "ump":
            fig = K.umpire_scatter(st.get("umpire_pairs"), lg, th)
        else:
            fig = K.hard_chart(st.get("dup_pairs") or st.get("hard_pairs") or {}, lg, th)
        self.lab_chart.show_figure(fig, self.t("nodata"))

    def _audit_export(self):
        from .. import audit
        res = self.result
        if res is None:
            return
        base = Path(res.outputs.get("folder") or Path.home()) / f"audit_checklist_{date.today():%Y%m%d}.xlsx"
        f, _ = QFileDialog.getSaveFileName(self, self.t("audit_export"), str(base), "Excel (*.xlsx);;CSV (*.csv)")
        if not f:
            return
        m = audit.export(res.ctx, res.ctx.params, f)
        self.log(f"audit checklist: {f} ({m['selected']} of {m['population']} samples, seed {m['seed']})")

    def _audit_import(self):
        from .. import audit
        res = self.result
        if res is None:
            return
        f, _ = QFileDialog.getOpenFileName(self, self.t("audit_import"), str(res.outputs.get("folder") or ""), "Excel / CSV (*.xlsx *.csv)")
        if not f:
            return
        try:
            res.ctx.stats["random_audit"] = audit.summarise(res.ctx, res.ctx.params, f)
            res.spec.audit_path = f
        except Exception as e:
            QMessageBox.warning(self, self.t("audit_import"), str(e))
            return
        ra = res.ctx.stats["random_audit"]
        self.log(f"audit results: {ra['checked']} checked, {ra['discrepancies']} discrepancies ({ra['status']})")
        if res.outputs.get("folder"):
            self._rebuild_evidence()
        self._fill_lab()

    # ------------------------------------------------------------------ Topography & boundary
    def _page_topo(self):
        from .app import ChartView, PandasModel, card, label
        page, lay = self._page_frame("nav_topo", "sub_topo")
        bc, bl0 = card()
        bl = QHBoxLayout()
        bl0.addLayout(bl)
        self.topo_sel = QComboBox()
        self.topo_sel.currentIndexChanged.connect(lambda *_: self._draw_topo())
        bl.addWidget(self.topo_sel)
        self.topo_info = label("Muted", 9)
        self.topo_info.setWordWrap(True)
        bl.addWidget(self.topo_info, 1)
        lay.addWidget(bc)
        sp = QSplitter(Qt.Horizontal)
        cc, cl = card()
        self.topo_chart = ChartView()
        cl.addWidget(self.topo_chart, 1)
        sp.addWidget(cc)
        rc, rl = card()
        rl.addWidget(self.tr_(label("H2", 11), "topo_info"))
        self.topo_model = PandasModel()
        self.topo_view = self._table_view(self.topo_model)
        rl.addWidget(self.topo_view, 1)
        rl.addWidget(self.tr_(label("H2", 11), "issues_topo"))
        self.topo_iss_model = PandasModel()
        self.topo_iss = self._table_view(self.topo_iss_model)
        rl.addWidget(self.topo_iss, 2)
        sp.addWidget(rc)
        sp.setSizes([600, 600])
        lay.addWidget(sp, 1)
        return page

    def _fill_topo(self):
        res = self.result
        if res is None:
            return
        st = res.ctx.stats
        cur = self.topo_sel.currentData()
        self.topo_sel.blockSignals(True)
        self.topo_sel.clear()
        for key in ("dz", "map"):
            self.topo_sel.addItem(self.t("chart_" + key), key)
        if cur:
            self.topo_sel.setCurrentIndex(max(self.topo_sel.findData(cur), 0))
        self.topo_sel.blockSignals(False)
        rows = []
        for t in st.get("topography") or []:
            ext = t.get("extent")
            rows += [{"item": f"topography · {t['label']}", "value": f"{t['file']} — {t.get('format')}"},
                     {"item": "extent", "value": ", ".join(f"{v:,.2f}" for v in ext) if ext else "—"},
                     {"item": "resolution / points", "value": f"{t.get('resolution') or '—'} / {t.get('n_points') or t.get('n_cells') or t.get('n_triangles') or '—'}"},
                     {"item": "CRS", "value": ", ".join(f"{k}={v}" for k, v in (t.get("crs") or {}).items() if k != "wkt") or "as file"}]
            rows += [{"item": "note", "value": n} for n in t.get("notes", [])]
        li = st.get("licence_info")
        if li:
            rows += [{"item": "licence boundary", "value": f"{li['format']}: {li['polygons']} polygon(s), {li['rings']} ring(s), {li['vertices']} vertices"}]
            rows += [{"item": "note", "value": n} for n in li.get("notes", []) + li.get("alignment", [])]
        san = st.get("topo_sanity") or {}
        if san:
            rows.append({"item": "collars with topography", "value": f"{san.get('n_with_topography', 0)} of {san.get('n_collars', 0)}"})
            if san.get("elevation_ratio"):
                rows.append({"item": "elevation ratio collar / topography", "value": san["elevation_ratio"]})
            rows += [{"item": f"sanity {sev}", "value": msg} for sev, msg in san.get("findings", [])]
        self.topo_model.set(pd.DataFrame(rows))
        self._fit(self.topo_view, 640)
        self.topo_iss_model.set(self._issue_subset(TOPO_RULES))
        self._fit(self.topo_iss)
        dz = st.get("dz")
        self.topo_info.setText(f"ΔZ: median {dz.median():+.2f} m, n {int(dz.notna().sum())}" if dz is not None and dz.notna().any() else "")
        self._draw_topo()

    def _draw_topo(self):
        from ..report import charts as K
        res = self.result
        if res is None:
            return
        if (self.topo_sel.currentData() or "dz") == "dz":
            fig = K.dz_map(res.ctx, self.lang, self.chart_theme)
        else:
            iss = res.issues
            worst = (iss.dropna(subset=["hole_id"]).groupby("hole_id")["severity"].agg(lambda s: min(s, key=lambda v: ["CRITICAL", "ERROR", "WARNING", "INFO"].index(v)))
                     if not iss.empty else pd.Series(dtype=object))
            fig = K.collar_map(res.ctx, worst, self.lang, self.chart_theme)
        self.topo_chart.show_figure(fig, self.t("nodata"))

    # ------------------------------------------------------------------ Versions
    def _page_versions(self):
        from .app import ChartView, PandasModel, card, label
        page, lay = self._page_frame("nav_versions", "sub_versions")
        bc, bl0 = card()
        bl = QHBoxLayout()
        bl0.addLayout(bl)
        for k, fn in (("accept", self._accept_dialog), ("export_log", self._export_change_log)):
            b = QPushButton()
            b.clicked.connect(fn)
            self.tr_(b, k)
            bl.addWidget(b)
        self.ver_info = label("Muted", 9)
        self.ver_info.setWordWrap(True)
        bl.addWidget(self.ver_info, 1)
        lay.addWidget(bc)
        sp = QSplitter(Qt.Horizontal)
        cc, cl = card()
        self.ver_chart = ChartView()
        cl.addWidget(self.ver_chart, 2)
        cl.addWidget(self.tr_(label("H2", 11), "classes"))
        self.ver_cls_model = PandasModel()
        self.ver_cls = self._table_view(self.ver_cls_model)
        cl.addWidget(self.ver_cls, 1)
        sp.addWidget(cc)
        rc, rl = card()
        row = QHBoxLayout()
        row.addWidget(self.tr_(label("H2", 11), "change_log"))
        row.addStretch(1)
        self.ver_filter = QComboBox()
        self.ver_filter.currentIndexChanged.connect(lambda *_: self._filter_versions())
        row.addWidget(self.ver_filter)
        rl.addLayout(row)
        self.ver_log_model = PandasModel()
        self.ver_log = self._table_view(self.ver_log_model)
        rl.addWidget(self.ver_log, 1)
        sp.addWidget(rc)
        sp.setSizes([560, 640])
        lay.addWidget(sp, 1)
        return page

    def _fill_versions(self):
        from ..report import charts as K
        res = self.result
        if res is None:
            return
        v = res.ctx.stats.get("version")
        snap = res.ctx.stats.get("snapshot")
        parts = []
        if v is None and snap is None:
            parts.append(self.t("no_version"))
        if v is not None:
            h = v["summary"]["holes"]
            parts.append(f"baseline {h['baseline']} · current {h['current']} · unchanged {h['unchanged']} · changed {h['changed']} · added {h['added']} · deleted {h['deleted']}")
        if snap is not None:
            n_crit = int(((res.issues["rule_id"] == "VER-009") & (res.issues["severity"] == "CRITICAL")).sum()) if not res.issues.empty else 0
            parts.append(f"snapshot {snap.get('_file')} ({snap.get('accepted_at')}, {snap.get('reviewer')}): {len(snap.get('locked_holes', []))} locked, {n_crit} locked holes changed")
        self.ver_info.setText("   ·   ".join(parts))
        self.ver_chart.show_figure(K.metal_delta(v["metal"], self.lang, self.chart_theme) if v is not None else None, self.t("nodata"))
        cls = pd.DataFrame(sorted((v["summary"]["change_classes"] if v else {}).items(), key=lambda kv: -kv[1]), columns=["class", "n"])
        self.ver_cls_model.set(cls)
        self._fit(self.ver_cls)
        self.ver_filter.blockSignals(True)
        self.ver_filter.clear()
        self.ver_filter.addItem(self.t("all_classes"), None)
        for c in cls["class"]:
            self.ver_filter.addItem(c, c)
        self.ver_filter.blockSignals(False)
        self._filter_versions()

    def _filter_versions(self):
        res = self.result
        v = res.ctx.stats.get("version") if res is not None else None
        if v is None:
            self.ver_log_model.set(pd.DataFrame())
            return
        ch = v["changes"]
        c = self.ver_filter.currentData()
        if c:
            ch = ch[ch["change_class"] == c]
        self.ver_log_model.set(ch.head(5000))
        self._fit(self.ver_log, 360)

    def _export_change_log(self):
        res = self.result
        v = res.ctx.stats.get("version") if res is not None else None
        if v is None:
            QMessageBox.information(self, self.t("export_log"), self.t("no_version"))
            return
        f, _ = QFileDialog.getSaveFileName(self, self.t("export_log"), str(Path(res.outputs.get("folder") or Path.home()) / "change_log.xlsx"),
                                           "Excel (*.xlsx);;CSV (*.csv)")
        if not f:
            return
        if f.lower().endswith(".csv"):
            v["changes"].to_csv(f, index=False, encoding="utf-8-sig")
        else:
            with pd.ExcelWriter(f, engine="openpyxl") as w:
                v["changes"].to_excel(w, sheet_name="changes", index=False)
                v["metal"].to_excel(w, sheet_name="metal", index=False)
                v["metal_by_hole"].to_excel(w, sheet_name="metal_by_hole", index=False)
        self.log(f"change log: {f}")

    def _accept_dialog(self):
        from .. import versions
        res = self.result
        if res is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(self.t("accept"))
        f = QFormLayout(dlg)
        rev, note = QLineEdit(), QLineEdit()
        lock = QComboBox()
        for k in ("lock_all", "lock_none", "lock_list"):
            lock.addItem(self.t(k), k)
        holes = QLineEdit()
        holes.setEnabled(False)
        lock.currentIndexChanged.connect(lambda *_: holes.setEnabled(lock.currentData() == "lock_list"))
        f.addRow(self.t("reviewer"), rev)
        f.addRow(self.t("note_"), note)
        f.addRow(self.t("lock"), lock)
        f.addRow("", holes)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        f.addRow(bb)
        if not dlg.exec():
            return
        if not rev.text().strip():
            QMessageBox.warning(self, self.t("accept"), self.t("reviewer"))
            return
        path, _ = QFileDialog.getSaveFileName(self, self.t("accept"), str(Path(res.outputs.get("folder") or Path.home()) / f"accepted_snapshot_{date.today():%Y%m%d}.json"), "JSON (*.json)")
        if not path:
            return
        mode = lock.currentData()
        lk = "all" if mode == "lock_all" else "none" if mode == "lock_none" else [h.strip() for h in holes.text().split(",") if h.strip()]
        m = versions.accept(res, path, rev.text().strip(), note.text().strip(), lk)
        self.log(f"accepted snapshot: {path} ({len(m['locked_holes'])} holes locked)")
        self.paths["snapshot"].setText(path)

    def _refresh_p2(self):
        for fn in (self._fill_xtable, self._fill_lab, self._fill_topo, self._fill_versions):
            try:
                fn()
            except Exception as e:      # a page that cannot be filled must not stop the others
                self.log(f"! {fn.__name__}: {e}")
