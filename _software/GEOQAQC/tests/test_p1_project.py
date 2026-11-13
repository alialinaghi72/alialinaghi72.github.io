"""P1 R20: project mode -- several batch files, cross-batch pairing, per-
batch and combined reports, the batch x element acceptance matrix."""

import csv
import os

import pytest

import batch16 as B

COLS = ["SAMPLE_ID", "SAMPLE_TYPE", "CRM_ID", "PARENT_ID", "Cu_PPm", "Au_ppb"]


@pytest.fixture(scope="module")
def files(tmp_path_factory):
    d = tmp_path_factory.mktemp("proj")
    rows = list(B.rows())
    half = len(rows) // 2
    # move one duplicate of the first half into the second batch file
    k = next(i for i, r in enumerate(rows[:half]) if r.get("PARENT_ID"))
    rows.insert(half, rows.pop(k))
    half -= 1
    # a coarse duplicate in the second file whose parent is in the first
    paths = []
    for name, part in (("B15", rows[:half]), ("B16", rows[half:])):
        p = d / f"{name}.csv"
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(COLS + ["SEQ"])
            for i, r in enumerate(part, start=1):           # order restarts per file
                w.writerow([r.get(c, "") for c in COLS] + [i])
        paths.append(str(p))
    cert = d / "crm.csv"
    with open(cert, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["CRM_ID", "ELEMENT", "CERTIFIED", "SD", "UNIT"])
        for c in B.CERTS:
            w.writerow(c)
    single = d / "single.csv"
    with open(single, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLS + ["SEQ"])
        for i, r in enumerate(rows, start=1):
            w.writerow([r.get(c, "") for c in COLS] + [i])
    return d, paths, str(cert), str(single)


def _setup():
    from geoqaqc.protocol import (DEFAULT_CRITERIA, DEFAULT_FORMULAS,
                                  DEFAULT_SETTINGS, FormulaBook, RuleBook)
    rb = RuleBook()
    rb.el.set_method("Au_ppb", "FA")
    rb.el.set_method("Cu_PPm", "TOTAL")
    return (FormulaBook(DEFAULT_FORMULAS), {k: dict(v) for k, v in DEFAULT_CRITERIA.items()},
            dict(DEFAULT_SETTINGS), rb)


def test_merge_names_batches_and_keeps_file_order(files):
    from geoqaqc.project_mode import SEQ_COL, batches_of, load_batches
    d, paths, cert, _ = files
    p = load_batches(paths, cert, log=lambda m: None)
    t = p.assay
    assert batches_of(p) == ["B15", "B16"]
    assert t.mapping["order"] == SEQ_COL and t.mapping["batch"] == "BATCH"
    assert [c for c, _ in t.value_cols] == ["Cu_PPm", "Au_ppb"]
    seq = [int(t.col(r, SEQ_COL)) for r in t.rows]
    assert seq == list(range(1, len(seq) + 1))
    assert t.col(t.rows[0], "SEQ") == "1"          # original order column unchanged


def test_cross_batch_pairing_matches_single_file(files):
    from geoqaqc.analysis import build_pairs, run_analysis
    from geoqaqc.loader import load_project
    from geoqaqc.project_mode import load_batches
    d, paths, cert, single = files
    F, C, S, rb = _setup()
    a = load_batches(paths, cert, log=lambda m: None)
    run_analysis(a, F, C, S, rb, log=lambda m: None)
    b = load_project(single, cert)
    run_analysis(b, F, C, S, rb, log=lambda m: None)
    pa, pb = build_pairs(a, S, log=lambda m: None), build_pairs(b, S, log=lambda m: None)
    assert {t: len(v) for t, v in pa.items()} == {t: len(v) for t, v in pb.items()}
    # at least one pair has its two halves in different batches
    assert any(o.batch != du.batch for v in pa.values() for o, du in v)


def test_batch_matrix_and_reports(files, tmp_path):
    from geoqaqc.project_mode import load_batches, run_project, split_by_batch
    from geoqaqc.report.document import ReportMeta
    d, paths, cert, _ = files
    F, C, S, rb = _setup()
    p = load_batches(paths, cert, log=lambda m: None)
    parts = split_by_batch(p)
    assert [b for b, _ in parts] == ["B15", "B16"]
    assert sum(len(x.assay.rows) for _, x in parts) == len(p.assay.rows)
    res = run_project(p, F, C, S, rb, str(tmp_path), "NLR", ReportMeta(project="NLR"),
                      per_batch=True, pdf=False, log=lambda m: None)
    order, mx = res["matrix"]
    assert order == ["B15", "B16"]
    assert set(mx["B16"]) == {"Cu_PPm", "Au_ppb"}
    codes = {mx[b][el][0] for b in order for el in mx[b]}
    assert codes <= {"ACCEPTED", "CONDITIONAL", "REJECTED", "NOT_ASSESSABLE"}
    assert "REJECTED" in codes
    assert os.path.exists(tmp_path / "NLR_batch_matrix.csv")
    html = open(tmp_path / "NLR.html", encoding="utf-8").read()
    assert "ماتریس پذیرش بچ" in html
    assert len(res["batches"]) == 2
    for b, dec, fs in res["batches"]:
        assert all(os.path.exists(f) for f in fs)
        assert any(f.endswith(".docx") for f in fs)
