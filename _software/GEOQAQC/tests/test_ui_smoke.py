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
    a.do_analyse(quiet=True)
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
