import zipfile

from clearmark.docxclean import clean_docx, inspect_docx

_CORE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:creator>ChatGPT</dc:creator>
  <cp:lastModifiedBy>AI Assistant</cp:lastModifiedBy>
  <dc:title>Report</dc:title>
</cp:coreProperties>
"""

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/>
</Types>
"""


def _make_minimal_docx(path, with_custom=True):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("docProps/core.xml", _CORE_XML)
        zf.writestr("word/document.xml", "<w:document/>")
        if with_custom:
            zf.writestr("docProps/custom.xml", "<Properties/>")


def test_inspect_finds_core_properties_and_custom_xml(tmp_path):
    p = tmp_path / "doc.docx"
    _make_minimal_docx(p)
    report = inspect_docx(p)
    assert report.suspicious
    kinds = {f.kind for f in report.findings}
    assert "core_property" in kinds
    assert "custom_xml" in kinds


def test_clean_scrubs_core_and_drops_custom(tmp_path):
    src = tmp_path / "doc.docx"
    dst = tmp_path / "doc.cleaned.docx"
    _make_minimal_docx(src)
    removed = clean_docx(src, dst)
    assert removed >= 2

    with zipfile.ZipFile(dst) as zf:
        names = zf.namelist()
        assert "docProps/custom.xml" not in names
        # unrelated part preserved byte-for-byte
        assert zf.read("word/document.xml") == b"<w:document/>"

    report_after = inspect_docx(dst)
    assert not report_after.suspicious
