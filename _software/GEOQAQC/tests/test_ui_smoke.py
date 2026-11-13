import os

import pytest

tk = pytest.importorskip("tkinter")
pytestmark = [pytest.mark.ui,
              pytest.mark.skipif(not os.environ.get("DISPLAY") and os.name != "nt",
                                 reason="no display")]

from conftest import DATA  # noqa: E402


@pytest.fixture(scope="module")
def app():
    from geoqaqc.ui.app import App
    a = App()
    a.withdraw()
    a.load_files(os.path.join(DATA, "demo_assay.csv"),
                 os.path.join(DATA, "demo_crm_certificates.csv"),
                 os.path.join(DATA, "demo_umpire.csv"))
    a.do_analyse(quiet=True, wait=True)
    a.update()
    yield a
    a.destroy()


def test_every_page_renders(app):
    for name in app.page_names():
        app.select_page(name)
        app.update()
    assert app.current_page == app.page_names()[-1]


def test_dashboard_and_diagnosis(app):
    app.select_page("Dashboard")
    app.update()
    assert len(app.kpi_cards) == 4
    app.select_page("Diagnosis")
    assert len(app.diag_tree.get_children()) > 0
    assert len(app.clean_tree.get_children()) > 0


def test_rules_page_applies(app):
    app.select_page("Rules")
    app.rule_vars["drift_p"].set("0.01")
    assert app.apply_rules(quiet=True) == []
    assert app.RB["drift_p"] == 0.01
    app.rule_vars["swap_frac"].set("5")
    bad = app.apply_rules(quiet=True)
    assert bad and "swap" in bad[0].lower() or "C13" in bad[0]


def test_report_generation(app, tmp_path):
    app.report_vars["project"].set("Demo")
    paths = app.generate_report(str(tmp_path), "demo", pdf=False, word=True, wait=True)
    assert any(p.endswith(".html") for p in paths)
    assert any(p.endswith(".docx") for p in paths)


def test_analysis_runs_off_the_interface_thread(app):
    # a large project must not freeze the window ('Not responding')
    import time
    app.R = {}
    app.do_analyse(quiet=True)
    assert app._busy                                 # returned at once, worker running
    app.do_analyse(quiet=True)                       # a second start is refused
    t0 = time.time()
    while app._busy and time.time() - t0 < 120:
        app.update()
        time.sleep(0.05)
    assert not app._busy
    assert app.R and app.diag is not None
    assert app.current_page == "Dashboard"


def test_elements_page_sets_methods_and_thresholds(app):
    app.select_page("Elements")
    app.update()
    col = app._element_columns()[0]
    v = app.el_cfg_vars[col]
    v["method"].set("AR")
    v[("out", "PULP DUP")].set("40")
    v["outlier_action"].set("exclude")
    assert app.apply_elements(quiet=True) == []
    assert app.RB.el.method(col) == "AR"
    assert app.RB.el.profile(col)["outlier_hard"]["PULP DUP"] == 40.0
    app.reset_elements()
    assert app.RB.el.method(col) != "AR" or col.startswith("Au") is False


def test_review_window_records_decisions(app):
    from geoqaqc.exclusions import REASONS
    from geoqaqc.ui.review import ReviewDialog
    rows = [{"key": "COARSE DUP|Cu_pct|S1|C1", "dtype": "COARSE DUP", "element": "Cu_pct",
             "orig": "S1", "dup": "C1", "a": 0.2, "b": 2.0, "mean": 1.1, "hard": 81.8,
             "ratio": 10.0, "trigger": "outlier", "action": "ask", "decision": "exclude",
             "reason": REASONS[1], "source": "default", "pending": True, "order": 3,
             "batch": "J1", "limit": 50.0, "preselect": "exclude"}]
    dlg = ReviewDialog(app, app.project, rows, app.R.get("dup_all", {}))
    app.update()
    dlg.tree.selection_set("0")
    dlg.reason.set(REASONS[0])
    dlg._set("exclude", True)
    dlg._apply()
    d = app.project.pair_decisions["COARSE DUP|Cu_pct|S1|C1"]
    assert d["decision"] == "exclude" and d["reason"] == REASONS[0]
