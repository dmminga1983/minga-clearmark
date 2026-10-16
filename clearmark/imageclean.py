"""Metadata stripping for raster images: EXIF, XMP, and C2PA/AI-provenance
chunks (PNG tEXt/iTXt/zTXt, JPEG APP1/APP11, WebP EXIF/XMP chunks).

Uses Pillow, which already round-trips PNG/JPEG/WebP byte-for-byte for the
pixel data — we only touch the metadata containers around it.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}

# PNG text chunk keywords commonly used by AI tools / C2PA for provenance.
_SUSPECT_PNG_KEYWORDS = {
    "ai", "aigenerated", "generator", "software", "c2pa", "xml:com.adobe.xmp",
    "dall-e", "midjourney", "stable diffusion", "comment", "description",
    "parameters",  # Automatic1111/ComfyUI-style generation params
}


@dataclass
class ImageFinding:
    kind: str
    detail: str


@dataclass
class ImageReport:
    findings: list[ImageFinding] = field(default_factory=list)

    @property
    def suspicious(self) -> bool:
        return bool(self.findings)


def inspect_image(path: str | Path) -> ImageReport:
    findings: list[ImageFinding] = []
    with Image.open(path) as img:
        exif = img.getexif()
        if exif:
            findings.append(ImageFinding("exif", f"{len(exif)} EXIF tag(s)"))
        info = img.info or {}
        if "xmp" in info or "XML:com.adobe.xmp" in info:
            findings.append(ImageFinding("xmp", "XMP packet present"))
        for key, value in info.items():
            if isinstance(key, str) and key.lower() in _SUSPECT_PNG_KEYWORDS:
                snippet = str(value)[:80]
                findings.append(ImageFinding("text_chunk", f"{key}={snippet!r}"))
        icc = info.get("icc_profile")
        # ICC profiles are not AI-provenance by themselves; not flagged.
        del icc
    return ImageReport(findings=findings)


def _count_metadata(img: Image.Image) -> int:
    removed = len(img.getexif() or {})
    info = img.info or {}
    removed += sum(1 for k in info if isinstance(k, str) and k.lower() in _SUSPECT_PNG_KEYWORDS)
    removed += 1 if ("xmp" in info or "XML:com.adobe.xmp" in info) else 0
    return removed


def clean_image(src: str | Path, dst: str | Path) -> int:
    """Re-save the image with metadata stripped. Returns a rough count of
    metadata items removed (for reporting, not a cryptographic guarantee).

    Pillow's Image.save() does not carry EXIF/XMP/text-chunk metadata
    forward unless it is explicitly passed back in (via exif=, pnginfo=,
    icc_profile=, …) — so a plain re-save from decoded pixel data is
    already a clean copy; we never pass .info back to save().
    """
    with Image.open(src) as img:
        removed = _count_metadata(img)
        img.load()  # fully decode before the context manager closes
        img.save(dst, format=img.format)
    return removed


def clean_image_bytes(data: bytes) -> tuple[bytes, int]:
    buf_in = io.BytesIO(data)
    buf_out = io.BytesIO()
    with Image.open(buf_in) as img:
        removed = _count_metadata(img)
        img.load()
        img.save(buf_out, format=img.format)
    return buf_out.getvalue(), removed
