"""Metadata stripping for PDF: document Info dictionary + XMP metadata
stream. Uses pypdf, which rebuilds the PDF object graph on write (unlike
some tools that only append an incremental update), so stripped objects do
not linger as recoverable bytes in the output file.

Scope: document-level metadata only. Metadata embedded *inside* images
placed on the page (EXIF in a scanned JPEG, for instance) is a separate,
deeper problem this module does not attempt — see README for the caveat.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# clearmark signs its own output with this Producer string, the same way
# exiftool/qpdf leave their name behind. That is honest tool attribution,
# not a provenance leak, so inspect_pdf() does not flag it — but any other
# value (an AI generator's name, a third-party editor) still is.
OWN_PRODUCER = "clearmark"


@dataclass
class PdfFinding:
    kind: str
    detail: str


@dataclass
class PdfReport:
    findings: list[PdfFinding] = field(default_factory=list)

    @property
    def suspicious(self) -> bool:
        return bool(self.findings)


def inspect_pdf(path: str | Path) -> PdfReport:
    findings: list[PdfFinding] = []
    reader = PdfReader(str(path))
    info = reader.metadata
    if info:
        for key, value in info.items():
            if value and not (key == "/Producer" and str(value) == OWN_PRODUCER):
                findings.append(PdfFinding("info", f"{key}={str(value)[:80]!r}"))
    xmp = reader.xmp_metadata
    if xmp is not None:
        findings.append(PdfFinding("xmp", "XMP metadata stream present"))
    return PdfReport(findings=findings)


def clean_pdf(src: str | Path, dst: str | Path) -> int:
    reader = PdfReader(str(src))
    writer = PdfWriter()
    writer.append(reader)

    removed = len(reader.metadata or {})
    if reader.xmp_metadata is not None:
        removed += 1

    # Overwrite the Info dictionary rather than deleting it outright —
    # pypdf expects *some* /Info; an empty-but-present dict reads as
    # "scrubbed", not "never had metadata" (which a forensic diff would
    # find more suspicious than honest, deliberate blanking).
    writer.add_metadata({"/Producer": OWN_PRODUCER})
    try:
        writer.xmp_metadata = None  # type: ignore[attr-defined]
    except Exception:
        pass

    with open(dst, "wb") as fh:
        writer.write(fh)
    return removed
