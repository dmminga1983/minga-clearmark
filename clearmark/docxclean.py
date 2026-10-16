"""Metadata stripping for OOXML documents (DOCX/XLSX/PPTX share the same
container shape): core.xml / app.xml document properties, and any
custom.xml part some generators use to stash provenance data.

A DOCX is a zip archive; we rewrite it entry-by-entry so unrelated parts
(styles, media, body text) are preserved byte-for-byte.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

_CORE_PROPS = "docProps/core.xml"
_APP_PROPS = "docProps/app.xml"
_CUSTOM_PROPS_RE = re.compile(r"^docProps/custom\.xml$")

# Tags inside core.xml whose text content we blank (never delete the tag
# itself — OOXML readers expect the element to exist, even if empty).
_SCRUB_CORE_TAGS = ["creator", "lastModifiedBy", "description", "subject", "keywords", "title"]


@dataclass
class DocxFinding:
    kind: str
    detail: str


@dataclass
class DocxReport:
    findings: list[DocxFinding] = field(default_factory=list)

    @property
    def suspicious(self) -> bool:
        return bool(self.findings)


def _scrub_core_xml(xml_bytes: bytes) -> tuple[bytes, int]:
    text = xml_bytes.decode("utf-8", errors="replace")
    removed = 0
    for tag in _SCRUB_CORE_TAGS:
        pattern = re.compile(rf"(<dc:{tag}[^>]*>)(.*?)(</dc:{tag}>)|(<cp:{tag}[^>]*>)(.*?)(</cp:{tag}>)")

        def _blank(m: re.Match) -> str:
            nonlocal removed
            groups = m.groups()
            if groups[1] and groups[1].strip():
                removed += 1
                return f"{groups[0]}{groups[2]}"
            if len(groups) > 4 and groups[4] and groups[4].strip():
                removed += 1
                return f"{groups[3]}{groups[5]}"
            return m.group(0)

        text = pattern.sub(_blank, text)
    return text.encode("utf-8"), removed


def inspect_docx(path: str | Path) -> DocxReport:
    findings: list[DocxFinding] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if _CORE_PROPS in names:
            core = zf.read(_CORE_PROPS).decode("utf-8", errors="replace")
            for tag in _SCRUB_CORE_TAGS:
                m = re.search(rf"<(?:dc|cp):{tag}[^>]*>(.*?)</(?:dc|cp):{tag}>", core)
                if m and m.group(1).strip():
                    findings.append(DocxFinding("core_property", f"{tag}={m.group(1)[:60]!r}"))
        for name in names:
            if _CUSTOM_PROPS_RE.match(name):
                findings.append(DocxFinding("custom_xml", name))
    return DocxReport(findings=findings)


def clean_docx(src: str | Path, dst: str | Path) -> int:
    removed = 0
    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == _CORE_PROPS:
                    data, n = _scrub_core_xml(data)
                    removed += n
                elif _CUSTOM_PROPS_RE.match(item.filename):
                    removed += 1
                    continue  # drop the whole custom.xml part
                zout.writestr(item, data)
        # Drop the now-dangling relationship to custom.xml, if any.
        if any(_CUSTOM_PROPS_RE.match(n) for n in names):
            _prune_custom_xml_relationship(dst)
    return removed


def _prune_custom_xml_relationship(path: str | Path) -> None:
    rels_path = "[Content_Types].xml"
    try:
        with zipfile.ZipFile(path) as zf:
            if rels_path not in zf.namelist():
                return
            data = zf.read(rels_path).decode("utf-8", errors="replace")
    except (KeyError, zipfile.BadZipFile):
        return
    new_data = re.sub(r'<Override[^>]*PartName="/docProps/custom\.xml"[^>]*/>', "", data)
    if new_data == data:
        return
    _rewrite_single_entry(path, rels_path, new_data.encode("utf-8"))


def _rewrite_single_entry(path: str | Path, entry_name: str, new_bytes: bytes) -> None:
    tmp = Path(str(path) + ".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = new_bytes if item.filename == entry_name else zin.read(item.filename)
            zout.writestr(item, data)
    tmp.replace(path)
