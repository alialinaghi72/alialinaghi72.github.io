"""Grade versus logged geology (analysis/categorical.py, CRS-004/005) and the chart library in both themes."""
import pytest

from geovalid_pro.analysis import categorical as C
from geovalid_pro.report import charts as K
from geovalid_pro.report import theme as T
from geovalid_pro.report.html import _worst_by_hole


def test_samples_take_logged_categories(clean):
    _, res = clean
    smp, units, fields = C.sample_table(res.ctx)
    assert {"Lithology", "Alteration", "Weathering"} <= set(fields)
    assert fields["Lithology"][2] == "logging" and fields["Campaign"][2] == "collar"
    assert smp["Lithology"].notna().mean() > 0.99 and smp["Alteration"].notna().mean() > 0.99
    assert set(smp["Weathering"].dropna()) == {"OXIDE", "MIXED", "PRIMARY"}


def test_association_recovers_the_grade_model(clean):
    """The synthetic grade model puts Cu in BXH/QMP, potassic alteration, and not in random colour codes."""
    _, res = clean
    a = res.ctx.stats["categorical"]["association"]
    lith = a[(a["field"] == "Lithology") & (a["analyte"] == "Cu")].iloc[0]
    alt = a[(a["field"] == "Alteration") & (a["analyte"] == "Cu")].iloc[0]
    colour = a[a["field"].str.contains("رنگ") & (a["analyte"] == "Cu")].iloc[0]
    fe = a[(a["field"] == "Lithology") & (a["analyte"] == "Fe")].iloc[0]
    assert lith["eta2"] > 0.4 and lith["top_category"] in {"BXH", "QMP"} and lith["low_category"] == "ALLUV"
    assert alt["eta2"] > 0.3 and alt["top_category"] == "POTASSIC"
    assert colour["eta2"] < 0.05 and fe["eta2"] < 0.01
    assert C.primary_analytes(a, res.ctx.stats["categorical"]["units"], res.ctx.params, 1) == ["Cu"]


def test_domains_and_contacts(clean):
    _, res = clean
    cat = res.ctx.stats["categorical"]
    dom = cat["domains"]
    cu = dom[(dom["field"] == "Lithology") & (dom["analyte"] == "Cu")]["suggested_domains"].iloc[0]
    assert "BXH + QMP" in cu and cu.endswith("ALLUV")
    lith = [c for c in cat["contacts"] if c["field"] == "Lithology"]
    assert lith and all(c["boundary"] == "hard" for c in lith)
    assert (res.matrix.set_index("rule_id").loc[["CRS-004", "CRS-005"], "status"] == "RUN").all()
    assert set(res.issues.loc[res.issues["rule_id"].str.startswith("CRS"), "severity"]) == {"INFO"}


def test_cutoff_unit_conversion(clean):
    _, res = clean
    smp, units, _ = C.sample_table(res.ctx)
    p = {"analysis_cutoffs": {"Cu": [2000, "ppm"], "Au": [0.3, "g/t"]}}
    assert C.cutoff_for(smp, "Cu", "%", p) == pytest.approx(0.2)
    assert C.cutoff_for(smp, "Au", "ppm", p) == pytest.approx(0.3)
    assert C.cutoff_for(smp, "Mo", "ppm", {}) == pytest.approx(smp["Mo"][smp["Mo"] > 0].quantile(0.75))


def test_spatial_analyses_exclude_bad_collars(injected):
    _, res = injected
    smp, _, _ = C.sample_table(res.ctx)
    assert smp.loc[smp["hole_id"] == "GV-009", "x"].isna().all()        # X/Y swapped (COL-006)
    assert smp["x"].dropna().between(511_000, 514_000).all()


@pytest.mark.parametrize("th", [T.IVORY, T.OBSIDIAN], ids=["ivory", "obsidian"])
@pytest.mark.parametrize("lang", ["fa", "en"])
def test_every_chart_builds(injected, th, lang):
    _, res = injected
    ctx = res.ctx
    smp, units, fields = C.sample_table(ctx)
    cat = ctx.stats["categorical"]
    labels = {f: v[1] if lang == "fa" else v[0] for f, v in fields.items()}
    med, cnt = C.two_way(smp, "Lithology", "Alteration", "Cu")
    figs = {
        "donut": K.severity_donut(res.issues, lang, th), "family": K.family_bar(res.issues, lang, th),
        "map": K.collar_map(ctx, _worst_by_hole(res.issues), lang, th), "dz": K.dz_map(ctx, lang, th),
        "logprob": K.logprob({"Cu": smp["Cu"]}, units, lang, th), "corr": K.corr_heatmap(smp[list(units)], lang, th),
        "scatter": K.scatter_pair(smp, "Cu", "Au", "Lithology", units, lang, th),
        "box": K.grade_by_category(smp, "Lithology", "Cu", "%", labels["Lithology"], 0.2, None, lang, th),
        "assoc": K.association_heatmap(cat["association"], labels, lang, th),
        "twoway": K.two_way_heatmap(med, cnt, "Lithology", "Alteration", "Cu", "%", lang, th),
        "contact": K.contact_plot(cat["contacts"], units, lang, th, labels),
        "swath": K.swath_plots(smp, "Cu", "%", lang, th),
        "gt": K.gt_map(C.hole_grades(smp, ctx, "Cu", 0.2), "Cu", "%", 0.2, ctx.licence, lang, th),
        "glc": K.grade_length_curve(smp, "Cu", "%", lang, th),
        "comp": K.composition_depth(smp, "Alteration", None, lang, th),
        "phys": K.physical_by_category(C.physical_table(ctx), "Lithology", "Density g/cm³", None, lang, th),
        "cramer": K.field_association(smp, fields, lang, th),
        "strip": K.strip_log(smp, "GV-028", ["Cu", "Au"], fields, units, lang, th),
        "crm": K.crm_chart(next(iter(ctx.stats["crm_results"].values())), lang, th),
        "blank": K.blank_chart(next(iter(ctx.stats["blank_results"].values())), lang, th),
        "hard": K.hard_chart(ctx.stats["dup_pairs"], lang, th, ["Cu", "Au"]),
    }
    missing = [k for k, f in figs.items() if f is None]
    assert not missing, missing
    for k, f in figs.items():
        assert K.png(f, dpi=40).startswith("data:image/png;base64,"), k


def test_persian_text_is_not_reversed():
    s = "عیار به تفکیک سنگ‌شناسی"
    out = T.fa(s)
    assert T.fa(out) == out                      # idempotent
    if T.NATIVE_RTL:
        assert out == s                           # matplotlib lays out right-to-left text itself
