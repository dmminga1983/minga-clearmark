from pypdf import PdfWriter

from clearmark.pdfclean import clean_pdf, inspect_pdf


def _make_pdf_with_metadata(path):
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Producer": "SomeAIGenerator 1.0", "/Author": "AI"})
    with open(path, "wb") as fh:
        writer.write(fh)


def test_inspect_finds_metadata(tmp_path):
    p = tmp_path / "doc.pdf"
    _make_pdf_with_metadata(p)
    report = inspect_pdf(p)
    assert report.suspicious
    assert any("Producer" in f.detail or "Author" in f.detail for f in report.findings)


def test_clean_strips_metadata(tmp_path):
    src = tmp_path / "doc.pdf"
    dst = tmp_path / "doc.cleaned.pdf"
    _make_pdf_with_metadata(src)
    removed = clean_pdf(src, dst)
    assert removed >= 1
    report_after = inspect_pdf(dst)
    assert not report_after.suspicious
