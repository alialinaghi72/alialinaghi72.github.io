import zipfile

import pytest

from geoqaqc.core import fnum
from geoqaqc.model import (DataTable, Project, Sample, build_samples,
                           detection_limit, read_table, usable)
from geoqaqc.protocol import DEFAULT_SETTINGS

_CT = ('<?xml version="1.0" encoding="UTF-8"?>'
       '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
       '<Default Extension="xml" ContentType="application/xml"/></Types>')
_WB = ('<?xml version="1.0" encoding="UTF-8"?>'
       '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
       '<sheets><sheet name="Assays" sheetId="1" r:id="rId1"/></sheets></workbook>')
_RELS = ('<?xml version="1.0" encoding="UTF-8"?>'
         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '<Relationship Id="rId1" Target="worksheets/data.xml" '
         'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
         '</Relationships>')
_SST = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<si><t>SAMPLE_ID</t></si><si><t>Cu_pct</t></si><si><t>S1</t></si></sst>')
_SHEET = ('<?xml version="1.0" encoding="UTF-8"?>'
          '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
          '<sheetData>'
          '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
          '<row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2"><v>0.25</v></c></row>'
          '<row r="3"><c r="A3" t="inlineStr"><is><t>S2</t></is></c>'
          '<c r="B3"><v>3</v></c></row>'
          '</sheetData></worksheet>')


def make_xlsx(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("xl/workbook.xml", _WB)
        z.writestr("xl/_rels/workbook.xml.rels", _RELS)
        z.writestr("xl/sharedStrings.xml", _SST)
        z.writestr("xl/worksheets/data.xml", _SHEET)


def test_read_xlsx_first_sheet(tmp_path):
    p = str(tmp_path / "tiny.xlsx")
    make_xlsx(p)
    header, rows, delim = read_table(p)
    assert header == ["SAMPLE_ID", "Cu_pct"]
    assert rows == [["S1", "0.25"], ["S2", "3"]]
    assert delim == "xlsx"


def test_read_xlsx_error(tmp_path):
    p = tmp_path / "broken.xlsx"
    p.write_bytes(b"not a zip at all")
    with pytest.raises(ValueError) as ex:
        read_table(str(p))
    assert "save it as CSV" in str(ex.value)


def test_semicolon_decimal_comma_table(tmp_path):
    p = tmp_path / "eu.csv"
    p.write_text("SAMPLE_ID;Cu_pct\nS1;1,234\nS2;0,5\nS3;<0,01\n", encoding="utf-8")
    t = _assay_table(str(p))
    assert t.decimal_comma is True
    pr = Project()
    pr.assay = t
    build_samples(pr, dict(DEFAULT_SETTINGS), log=lambda m: None)
    assert [s.vals["Cu_pct"] for s in pr.samples] == pytest.approx([1.234, 0.5, 0.01])


def test_fnum_decimal_comma_mode():
    assert fnum("1.234,5", decimal_comma=True) == pytest.approx(1234.5)
    assert fnum("1,234", decimal_comma=True) == pytest.approx(1.234)


def _assay_table(path, mapping=None):
    h, r, d = read_table(path)
    t = DataTable("assay", "A", path, h, r, d)
    t.mapping = mapping or {"sampleid": "SAMPLE_ID"}
    t.value_cols = [("Cu_pct", "numeric")]
    return t


def test_build_samples_raw_and_dropped(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("SAMPLE_ID,Cu_pct\nS1,<0.01\n,0.5\nS3,0.2\n", encoding="utf-8")
    pr = Project()
    pr.assay = _assay_table(str(p))
    build_samples(pr, dict(DEFAULT_SETTINGS), log=lambda m: None)
    assert [s.sid for s in pr.samples] == ["S1", "S3"]
    assert pr.dropped_rows == [(3, "empty sample ID")]
    assert pr.samples[0].raw["Cu_pct"] == "<0.01"
    assert pr.samples[0].flags["Cu_pct"] == "<"
    assert pr.samples[0].crm_key == ""


def test_usable_and_detection_limit():
    s1, s2 = Sample("A", 2), Sample("B", 3)
    s1.vals = {"Cu": 0.01, "Au": 0.5}
    s1.flags = {"Cu": "<", "Au": ""}
    s1.excl = {"Cu": "C12 slip"}
    s2.vals = {"Cu": 0.02, "Au": 0.4}
    s2.flags = {"Cu": "<", "Au": ""}
    assert not usable(s1, "Cu")
    assert usable(s1, "Au")
    s2.dropped = True
    assert not usable(s2, "Au")
    pr = Project()
    pr.samples = [s1, s2]
    # both '<' results are unusable, so the DL falls back to the smallest
    # positive usable value
    assert detection_limit(pr, "Au", {}) == pytest.approx(0.5)


def test_detection_limit_ignores_zero_below_dl():
    # a laboratory that writes below-DL as 0 (C07 turns it into '<' 0) must not
    # give a detection limit of zero, which would switch the blank test off
    pr = Project()
    for i, (v, f) in enumerate([(0.0, "<"), (0.0, "<"), (0.01, ""), (0.25, "")]):
        s = Sample(f"S{i}", i + 2)
        s.vals, s.flags = {"Au": v}, {"Au": f}
        pr.samples.append(s)
    assert detection_limit(pr, "Au", {}) == pytest.approx(0.01)
    pr.samples[1].vals["Au"] = 0.005               # a real '<0.005' is preferred
    assert detection_limit(pr, "Au", {}) == pytest.approx(0.005)
