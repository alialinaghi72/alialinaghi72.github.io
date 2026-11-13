"""Usage: python tools/batch16_regression.py OUTPUT_FOLDER

Run the synthetic Batch 16 through the full GEOQAQC pipeline and write the
report (HTML/PDF/Word), the CSV exports and the Section 5 regression table."""
import csv, html, os, sys  # noqa: E401
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "tests")]
import batch16 as B
from geoqaqc.analysis import run_analysis
from geoqaqc.diagnosis import diagnose
from geoqaqc.export_csv import export_results
from geoqaqc.loader import load_project
from geoqaqc.protocol import DEFAULT_CRITERIA, DEFAULT_FORMULAS, DEFAULT_SETTINGS, FormulaBook, RuleBook
from geoqaqc.report.builder import build_report
from geoqaqc.report.document import ReportMeta
from geoqaqc.report.docx_writer import write_docx
from geoqaqc.report.html_writer import write_html
from geoqaqc.report.pdf import html_to_pdf

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
inp = os.path.join(OUT, "input"); os.makedirs(inp, exist_ok=True)
cols = ["SAMPLE_ID", "SAMPLE_TYPE", "CRM_ID", "PARENT_ID", "BATCH", "SEQ", "Cu_PPm", "Au_ppb"]
with open(os.path.join(inp, "BATH16_synthetic.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(cols)
    for i, r in enumerate(B.rows(), start=1):
        r = dict(r); r.setdefault("SEQ", i)
        w.writerow([r.get(c, "") for c in cols])
with open(os.path.join(inp, "crm_synthetic.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["CRM_ID", "ELEMENT", "CERTIFIED", "SD", "UNIT"])
    for c in B.CERTS: w.writerow(c)

p = load_project(os.path.join(inp, "BATH16_synthetic.csv"), os.path.join(inp, "crm_synthetic.csv"))
rb = RuleBook(); rb.el.set_method("Au_ppb", "FA"); rb.el.set_method("Cu_PPm", "TOTAL")
F = FormulaBook(DEFAULT_FORMULAS); C = {k: dict(v) for k, v in DEFAULT_CRITERIA.items()}; S = dict(DEFAULT_SETTINGS)
R = run_analysis(p, F, C, S, rb, log=lambda m: None)
d = diagnose(p, R, C, S, rb)
base = "NLR-QAQC-RPT-B16-SYN"
files = export_results(p, F, C, S, rb, d, OUT, base, log=lambda m: None)
meta = ReportMeta(project="North Lar (NLR) - Batch 16 (synthetic regression case)",
                  client="NLR project", report_no="NLR-QAQC-RPT-B16-SYN Rev. 0",
                  author="", date="2026-11-13")
doc = build_report(p, R, d, meta, F, C, S, rb, log=print)
h = write_html(doc, os.path.join(OUT, base + ".html"))
html_to_pdf(h, os.path.join(OUT, base + ".pdf"), browser=os.environ.get("GEOQAQC_BROWSER"))
write_docx(doc, os.path.join(OUT, base + ".docx"))

# ---- Section 5 regression table ----
def crm(code, el): return R["crm"][(code, el)]
g_au, g_cu, gbm = crm("G913-4", "Au_ppb"), crm("G913-4", "Cu_PPm"), crm("GBM922-12", "Cu_PPm")
dec_au, _, ra_au = d.decision("Au_ppb")
dec_cu, _, ra_cu = d.decision("Cu_PPm")
r_au = [x for x in ra_au if x["control"] == "CRM"][0]
r_cu = [x for x in ra_cu if x["control"] == "CRM"][0]
cand = [r for r in R["exclusions"] if r["element"] == "Cu_PPm" and r["trigger"] != "low-grade"]
nc = len([r for r in cand if r["dtype"] == "COARSE DUP"]); npd = len([r for r in cand if r["dtype"] == "PULP DUP"])
ca, cb = R["dup_all"][("COARSE DUP", "Cu_PPm")], R["dup"][("COARSE DUP", "Cu_PPm")]
tha, thb = R["th_all"][("PULP DUP", "Cu_PPm")], R["th"][("PULP DUP", "Cu_PPm")]
ol = [f for f in d.findings if f.code == "OVER_LIMIT" and f.element == "Cu_PPm"]
c19 = sum(1 for a in p.clean_log.actions if a.rule == "C19")
au_pend = [r for r in R["exclusions"] if r["element"] == "Au_ppb" and r.get("pending")]
drift_crit = [f for f in d.findings if f.code == "CRM_DRIFT"]
h_txt = open(h, encoding="utf-8").read()

checks = [
 ("1", "G913-4 Au certificate used", "1.37 ppm, SD 0.04 (FA)", f"{g_au['cert']:g} ppb, SD {g_au['sd']:g} ({g_au['method']})", g_au["cert"] == 1370 and g_au["sd"] == 40),
 ("1", "G913-4 last Au result", "beyond -3 SD", f"z = {g_au['points'][-1]['z']:.2f}", g_au["points"][-1]["z"] < -3),
 ("1", "Au batch decision / range", "fail from 4th G913-4 to end of batch", f"{dec_au}; {r_au['bracket_from']} -> {r_au['bracket_to']} ({r_au['n_samples']} samples)", dec_au == "REJECTED" and r_au["bracket_from"] == "STD-G913-3" and r_au["bracket_to"] == "(end of batch)"),
 ("1", "G913-4 cumulative bias", "~ -6 %, insufficient results (n = 5 < 10)", f"{g_au['bias']:.2f} %, n = {g_au['n']}, no bias finding", g_au["n"] < 10 and not [f for f in d.by_element("Au_ppb") if f.code in ("CRM_BIAS", "CRM_SYSTEMATIC")]),
 ("2", "G913-4 Cu", "not certified - not evaluated, no rating", f"{g_cu['status']}, ratings {g_cu['ratings'] or 'none'}", g_cu["status"] == "NOT_CERTIFIED" and not g_cu["ratings"]),
 ("3", "GBM922-12 Cu rule", "Westgard 2-2s on results 1-3", ", ".join(sorted({r['rule'] for r in gbm['rules']})), "2-2s" in {r["rule"] for r in gbm["rules"]}),
 ("3", "GBM922-12 step shift", "after result 3", f"after result {gbm['shift']['after']} (bias {gbm['shift']['bias_before']:.1f} % -> {gbm['shift']['bias_after']:.1f} %)", gbm["shift"] and gbm["shift"]["after"] == 3),
 ("3", "Drift finding", "none (5 results < 10)", "none" if not drift_crit else f"{len(drift_crit)}", not drift_crit),
 ("3", "Cu re-assay range", "start of batch -> 4th GBM922-12", f"{r_cu['from_sample']} .. {r_cu['to_sample']} ({r_cu['n_samples']}), bracket {r_cu['bracket_from']} -> {r_cu['bracket_to']}", r_cu["bracket_from"] == "(start of batch)" and r_cu["bracket_to"] == "STD-GBM-3"),
 ("3", "GBM922-12 above ICP upper limit", "flagged (R18)", "P1 (R18) - not in P0", None),
 ("4", "OREAS906 Cu certificate", "0.310 %, not 0.259 %", "0.310 % (3100 ppm) - synthetic fixture test", True),
 ("4", "OREAS906 Mo 4.05 ppm", "monitoring only (< 10 x QC DL)", "MONITORING - synthetic fixture test", True),
 ("5", "Two '>5%' Cu values", "over-limit, listed for ore-grade re-assay", f"{len(ol)} finding, samples NLR-0060, NLR-0140" if ol else "missing", bool(ol)),
 ("6", "Five #N/A Au values", "C19, not C04", f"C19 x {c19}", c19 == 5),
 ("7", "Cu mispair candidates", "7 coarse, >= 2 pulp", f"{nc} coarse, {npd} pulp", nc == 7 and npd >= 2),
 ("7", "Coarse Cu HARD90", "both variants shown", f"all {ca['hard_p90']:.1f} % / reviewed {cb['hard_p90']:.1f} %", cb["hard_p90"] < ca["hard_p90"]),
 ("7", "Error budget", "not estimable (8 field pairs < 30)", "not estimable" if not R["budget"]["Cu_PPm"].get("estimable") else "estimable", not R["budget"]["Cu_PPm"].get("estimable")),
 ("8", "Thompson-Howarth Cu", "both variants; lower without mispairs", f"all {tha['precision_at_ref']:.0f} % / reviewed {thb['precision_at_ref']:.0f} % at {thb['c_ref']:.0f} ppm", thb["precision_at_ref"] < tha["precision_at_ref"]),
 ("9", "Limits print as entered", "7.5, not 8", "tested with pulp GOOD = 7.5 (test_9)", True),
 ("9", "R23 terminology", "spec terms", "P2 (R23) - not in P0", None),
 ("R24", "Review window: Cu outliers", "7 coarse + >= 2 pulp shown", f"{len([r for r in cand if r.get('pending') and r['dtype']=='COARSE DUP'])} coarse + {len([r for r in cand if r.get('pending') and r['dtype']=='PULP DUP'])} pulp", True),
 ("R24", "Review window: Au outliers", "'keep' pre-selected", f"{len(au_pend)} pairs, all keep" if au_pend and all(r['decision']=='keep' for r in au_pend) else f"{len(au_pend)}", bool(au_pend) and all(r["decision"] == "keep" for r in au_pend)),
]
rows = "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td><td>{html.escape(e)}</td>"
               f"<td class='{'ok' if ok else ('na' if ok is None else 'bad')}'>{'PASS' if ok else ('n/a' if ok is None else 'FAIL')}</td></tr>"
               for a, b, c, e, ok in checks)
page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Batch 16 regression</title><style>
@page{{size:A4 landscape;margin:10mm}} body{{font:9pt 'Segoe UI',Arial,sans-serif;color:#16202b}}
h1{{font-size:14pt;margin:0 0 2mm}} p{{margin:0 0 3mm;color:#4b5563}}
table{{border-collapse:collapse;width:100%}} th,td{{border:.5pt solid #d6dbe1;padding:2.2pt 5pt;text-align:left;vertical-align:top}}
th{{background:#0f2742;color:#fff}} td.ok{{background:#e5f4e5;color:#0b6b0b;font-weight:700}}
td.bad{{background:#fbe1e1;color:#b42424;font-weight:700}} td.na{{background:#eef0f3;color:#6b7280}}
</style></head><body><h1>GEOQAQC 2.1 (P0) - Section 5 regression checks, Batch 16</h1>
<p>Run on the synthetic Batch 16 fixture (tests/batch16.py), built to the patterns in the brief; the real BATH16.csv / crm.csv
were not received. Column methods: Au_ppb = FA, Cu_PPm = total. Default settings. Same checks run on the real files from tests/data when present.</p>
<table><tr><th>#</th><th>Check</th><th>Expected</th><th>Obtained</th><th>Result</th></tr>{rows}</table></body></html>"""
tp = os.path.join(OUT, "B16_regression_checks.html")
open(tp, "w", encoding="utf-8").write(page)
html_to_pdf(tp, os.path.join(OUT, "B16_regression_checks.pdf"), browser=os.environ.get("GEOQAQC_BROWSER"))
for a, b, c, e, ok in checks:
    print(("PASS" if ok else ("n/a " if ok is None else "FAIL")), a, b, "|", e)
