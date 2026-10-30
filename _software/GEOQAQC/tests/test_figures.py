import pytest
from matplotlib.figure import Figure as MplFigure

from geoqaqc.diagnosis import STAGES, diagnose
from geoqaqc.figures import Figure, fig_source_matrix, figure_catalog
from geoqaqc.protocol import DEFAULT_CRITERIA, DEFAULT_SETTINGS, RuleBook
from geoqaqc.render import THEMES, draw_figure, to_png, to_svg
from test_demo_detection import demo


@pytest.fixture(scope="module")
def ctx():
    p, R = demo()
    C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}
    S = dict(DEFAULT_SETTINGS)
    d = diagnose(p, R, C, S, RuleBook())
    return p, R, d, S, C


def test_catalog_ids(ctx):
    cat = figure_catalog(*ctx)
    for fid in ("crm/DEMO 501/Cu_pct/control", "crm/DEMO 501/Cu_pct/cusum",
                "drift/Cu_pct", "accuracy/Ag_ppm", "coverage/Mo_ppm",
                "blank/COARSE BLANK/Cu_pct", "blankprev/COARSE BLANK/Cu_pct",
                "dup/FIELD DUP/Au_ppm/rank", "dup/FIELD DUP/Au_ppm/maxmin",
                "dup/COARSE DUP/Au_ppm/quartile", "th/PULP DUP/Cu_pct/curve",
                "umpire/Cu_pct/qq", "umpire/Ag_ppm/quartile", "insertion",
                "budget", "batches", "source_matrix", "scores"):
        assert fid in cat, fid
    assert len(cat) >= 80


def test_every_figure_renders_svg(ctx):
    for fid, make in figure_catalog(*ctx).items():
        fig = make()
        assert isinstance(fig, Figure), fid
        assert fig.title, fid
        assert "--" not in fig.title, fid       # breaks the SVG text comments
        svg = to_svg(fig)
        assert svg.lstrip().startswith("<svg"), fid
        assert fig.title in svg, fid


def test_png_both_themes(ctx):
    cat = figure_catalog(*ctx)
    for fid in ("crm/DEMO 501/Cu_pct/control", "budget", "source_matrix",
                "dup/FIELD DUP/Au_ppm/maxmin"):
        for theme in THEMES:
            png = to_png(cat[fid](), theme=theme, dpi=80)
            assert png[:8] == b"\x89PNG\r\n\x1a\n", (fid, theme)


def test_source_matrix_shape(ctx):
    p, R, d, S, C = ctx
    fig = fig_source_matrix(d)
    assert fig.kind == "matrix"
    assert fig.matrix_data["rows"] == p.elements
    assert len(fig.matrix_data["cols"]) == len(STAGES) == 8


def test_log_axis_nonpositive():
    f = Figure("log axis with a zero")
    f.xlog = f.ylog = True
    f.points([0, 1, 10, None], [1, 0, 3, 4])
    f.line([0, 10], [0, 10])
    f.set_range(xr=(0, 100))
    assert "<svg" in to_svg(f)


def test_hover_index():
    f = Figure("hover")
    f.points([1, 2, 3], [1, 4, 9], ids=["A", "B", "C"], label="pts")
    f.points([1, 2], [2, 3], label="no ids")
    mf = MplFigure(figsize=(4, 3))
    idx = draw_figure(f, mf, "dark")
    assert len(idx) == 1
    ids = list(idx.values())[0]
    assert ids == ["A", "B", "C"]


def test_empty_figure_has_message():
    f = Figure("nothing to show")
    f.note("no data")
    assert "no data" in to_svg(f)


def test_short_log_range_keeps_tick_labels():
    # less than one decade: there must still be labelled ticks on the axis
    from matplotlib.figure import Figure as MF
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    f = Figure("short log range")
    f.xlog = True
    f.line([0.13, 0.2, 0.4, 0.6], [3, 3.2, 3.4, 3.3])
    mf = MF(figsize=(5, 3))
    FigureCanvasAgg(mf)
    draw_figure(f, mf, "light")
    mf.canvas.draw()
    ax = mf.axes[0]
    labels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()
              and ax.get_xlim()[0] <= t.get_position()[0] <= ax.get_xlim()[1]]
    assert len(labels) >= 2, labels
