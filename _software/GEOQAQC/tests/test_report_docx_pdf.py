import glob
import os
import zipfile

import pytest

from geoqaqc.report.docx_writer import write_docx
from geoqaqc.report.html_writer import write_html
from geoqaqc.report.pdf import find_browser, html_to_pdf
from test_report_html import _run
from test_demo_detection import demo

CHROMIUM = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome") or [None])[0]
needs_browser = pytest.mark.skipif(CHROMIUM is None and find_browser() is None,
                                   reason="no Chromium/Edge/Chrome available")


@pytest.fixture(scope="module")
def doc():
    p, R = demo()
    return _run(p, R)


@pytest.fixture(autouse=True)
def browser_env(monkeypatch):
    if CHROMIUM:
        monkeypatch.setenv("GEOQAQC_BROWSER", CHROMIUM)


def _xml(path, part):
    with zipfile.ZipFile(path) as z:
        return z.read(part).decode("utf-8")


def test_docx_demo(doc, tmp_path):
    import docx
    path = write_docx(doc, str(tmp_path / "report.docx"))
    d = docx.Document(path)
    assert len(d.inline_shapes) > 30
    body = _xml(path, "word/document.xml")
    assert "<w:bidi/>" in body or "<w:bidi " in body
    assert "<w:bidiVisual/>" in body
    assert "<w:rtl/>" in body
    assert "TOC \\o" in body
    assert 'w:w="11906"' in body                    # A4 width in twips
    assert "updateFields" in _xml(path, "word/settings.xml")
    texts = "\n".join(p.text for p in d.paragraphs)
    assert "QC-1405-01" in body
    assert "عنصر نقره" in texts or "نقره" in texts
    # Persian runs carry the complex-script font of the meta
    assert 'w:cs="B Nazanin"' in body


def test_docx_schema_order(doc, tmp_path):
    """Element order the OOXML schema requires (Word rejects files that break it)."""
    import re
    path = write_docx(doc, str(tmp_path / "o.docx"))
    settings = _xml(path, "word/settings.xml")
    assert settings.index("<w:updateFields") < settings.index("<w:compat")
    assert re.search(r'<w:zoom [^>]*w:percent="', settings)
    body = _xml(path, "word/document.xml")
    for ppr in re.findall(r"<w:pPr>.*?</w:pPr>", body):
        if "<w:pBdr>" in ppr and "<w:bidi/>" in ppr:
            assert ppr.index("<w:pBdr>") < ppr.index("<w:bidi/>"), ppr[:200]


def test_find_browser_env(monkeypatch, tmp_path):
    fake = tmp_path / "browser.exe"
    fake.write_text("x")
    monkeypatch.setenv("GEOQAQC_BROWSER", str(fake))
    assert find_browser() == str(fake)
    monkeypatch.setenv("GEOQAQC_BROWSER", str(tmp_path / "missing.exe"))
    assert find_browser() != str(tmp_path / "missing.exe")


def test_pdf_without_browser_raises(monkeypatch, tmp_path):
    import geoqaqc.report.pdf as pdf
    monkeypatch.setattr(pdf, "find_browser", lambda: None)
    (tmp_path / "a.html").write_text("<html></html>", encoding="utf-8")
    with pytest.raises(RuntimeError) as ex:
        pdf.html_to_pdf(str(tmp_path / "a.html"), str(tmp_path / "a.pdf"))
    assert "Edge" in str(ex.value)


@needs_browser
def test_pdf_demo(doc, tmp_path):
    html = write_html(doc, str(tmp_path / "r.html"))
    pdf = html_to_pdf(html, str(tmp_path / "r.pdf"))
    data = open(pdf, "rb").read()
    assert data[:4] == b"%PDF"
    assert len(data) > 200_000


@needs_browser
def test_non_ascii_paths(doc, tmp_path):
    folder = tmp_path / "گزارش پروژه"
    folder.mkdir()
    html = write_html(doc, str(folder / "گزارش.html"))
    pdf = html_to_pdf(html, str(folder / "گزارش.pdf"))
    dx = write_docx(doc, str(folder / "گزارش.docx"))
    for f in (html, pdf, dx):
        assert os.path.getsize(f) > 10_000, f


def test_pdf_uses_its_own_browser_profile(monkeypatch, tmp_path):
    # with Edge already open (or its startup boost), a headless run on the
    # shared profile can hand the job to that window and print nothing
    import geoqaqc.report.pdf as pdf
    seen = {}

    def fake_run(args, **kw):
        seen["args"] = args
        prof = [a for a in args if a.startswith("--user-data-dir=")]
        seen["profile"] = prof[0].split("=", 1)[1] if prof else None
        seen["existed"] = bool(prof) and os.path.isdir(seen["profile"])
        out = [a for a in args if a.startswith("--print-to-pdf=")][0].split("=", 1)[1]
        open(out, "wb").write(b"%PDF-1.4")
    monkeypatch.setattr(pdf.subprocess, "run", fake_run)
    monkeypatch.setattr(pdf, "PRIVATE_PROFILE", True)       # as on Windows
    (tmp_path / "a.html").write_text("<p>x</p>", encoding="utf-8")
    pdf.html_to_pdf(str(tmp_path / "a.html"), str(tmp_path / "a.pdf"), browser="edge")
    assert seen["profile"] and seen["existed"]
    assert not os.path.exists(seen["profile"])          # removed afterwards
