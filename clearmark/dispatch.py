"""Routes a file to the right cleaner/inspector by extension, and classifies
unknown bytes so the text tools can refuse to mangle a binary file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from . import docxclean, imageclean, pdfclean, textclean

Kind = Literal["text", "image", "pdf", "docx", "unknown"]

_IMAGE_EXT = imageclean.SUPPORTED_EXTENSIONS
_DOCX_EXT = {".docx", ".xlsx", ".pptx", ".dotx"}
_TEXT_EXT = {".txt", ".md", ".markdown", ".html", ".htm", ".csv", ".json", ".yaml", ".yml"}

# Magic bytes for the container formats we might be asked to treat as text.
_ZIP_MAGIC = b"PK\x03\x04"


def classify(path: str | Path) -> Kind:
    ext = Path(path).suffix.lower()
    if ext in _DOCX_EXT:
        return "docx"
    if ext in _IMAGE_EXT:
        return "image"
    if ext == ".pdf":
        return "pdf"
    if ext in _TEXT_EXT:
        return "text"
    # Fall back to sniffing bytes for an extensionless or mislabeled file.
    try:
        with open(path, "rb") as fh:
            head = fh.read(8)
    except OSError:
        return "unknown"
    if head.startswith(_ZIP_MAGIC):
        return "docx" if ext in _DOCX_EXT else "unknown"
    if head.startswith(b"%PDF"):
        return "pdf"
    if head[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1"):
        return "image"
    # Heuristic: mostly-printable bytes -> treat as text.
    try:
        head.decode("utf-8")
        return "text"
    except UnicodeDecodeError:
        return "unknown"


def looks_binary(data: bytes) -> bool:
    if data.startswith(_ZIP_MAGIC) or data.startswith(b"%PDF") or data[:4] == b"\x89PNG":
        return True
    control = sum(1 for b in data[:2048] if b < 9 or (13 < b < 32))
    return control / max(len(data[:2048]), 1) > 0.05


@dataclass
class Report:
    kind: Kind
    suspicious: bool
    detail: list[str]


def inspect_file(path: str | Path) -> Report:
    kind = classify(path)
    if kind == "text":
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        r = textclean.inspect_text(text)
        detail = [f"{f.category}:{f.name} x{f.count}" for f in r.findings]
        return Report("text", r.suspicious, detail)
    if kind == "image":
        r = imageclean.inspect_image(path)
        return Report("image", r.suspicious, [f"{f.kind}: {f.detail}" for f in r.findings])
    if kind == "pdf":
        r = pdfclean.inspect_pdf(path)
        return Report("pdf", r.suspicious, [f"{f.kind}: {f.detail}" for f in r.findings])
    if kind == "docx":
        r = docxclean.inspect_docx(path)
        return Report("docx", r.suspicious, [f"{f.kind}: {f.detail}" for f in r.findings])
    return Report("unknown", False, [])


def clean_file(src: str | Path, dst: str | Path, *, normalize_spaces: bool = True) -> tuple[Kind, int]:
    kind = classify(src)
    if kind == "text":
        text = Path(src).read_text(encoding="utf-8", errors="replace")
        cleaned, removed = textclean.clean_text(text, normalize_spaces=normalize_spaces)
        Path(dst).write_text(cleaned, encoding="utf-8")
        return "text", removed
    if kind == "image":
        return "image", imageclean.clean_image(src, dst)
    if kind == "pdf":
        return "pdf", pdfclean.clean_pdf(src, dst)
    if kind == "docx":
        return "docx", docxclean.clean_docx(src, dst)
    raise ValueError(f"unknown format: {src}")
