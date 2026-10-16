"""Layer A: deterministic removal of invisible/steganographic Unicode
carriers used by some AI-generation pipelines as an edit-based watermark
channel (zero-width joiners, bidi overrides, language-tag characters,
exotic spaces used as a binary carrier, etc).

This is *not* a statistical-watermark remover — token-sampling marks (the
kind embedded in which words a model chose) are not addressed here, because
removing them reliably requires rewriting the text with another model and
necessarily degrades the prose. That tradeoff belongs to the user, explicitly,
not to a silent default — so this module sticks to the lossless, verifiable
layer: characters that have no legitimate reason to be sitting invisibly in
plain prose.

Detection and removal share one table so a human-readable report and the
actual scrub can never disagree about what counts.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

# --- Carrier definitions -----------------------------------------------
# Each entry: (label, predicate(codepoint) -> bool, is_space_like)
# "space_like" carriers are only normalized to U+0020 when normalize_spaces
# is on; everything else is always stripped outright (it is never meant to
# be seen or to affect layout — it exists only to hide a payload).

_ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}
_BIDI_CONTROL = {0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)}
_TAG_CHARS = {0xE0001, *range(0xE0020, 0xE0080)}
_DEFAULT_IGNORABLE_EXTRA = {0x2065, *range(0xFFF0, 0xFFF9)}
_NONCHARACTERS = (
    set(range(0xFDD0, 0xFDF0))
    | {0xFFFE + 0x10000 * plane for plane in range(17)}
    | {0xFFFF + 0x10000 * plane for plane in range(17)}
)
_SOFT_HYPHEN = {0x00AD}

_EXOTIC_SPACES = {
    0x00A0,  # no-break space
    0x1680,
    *range(0x2000, 0x200B),  # en/em spaces etc (0x2000-0x200A)
    0x202F,  # narrow no-break space
    0x205F,
    0x3000,  # ideographic space
}


@dataclass
class TextFinding:
    codepoint: int
    name: str
    category: str  # zero_width | bidi | tag | ignorable | noncharacter | exotic_space
    count: int = 1


@dataclass
class TextReport:
    findings: list[TextFinding] = field(default_factory=list)
    total: int = 0

    @property
    def suspicious(self) -> bool:
        return self.total > 0


def _classify(cp: int) -> str | None:
    if cp in _ZERO_WIDTH:
        return "zero_width"
    if cp in _BIDI_CONTROL:
        return "bidi"
    if cp in _TAG_CHARS:
        return "tag"
    if cp in _SOFT_HYPHEN:
        return "soft_hyphen"
    if cp in _DEFAULT_IGNORABLE_EXTRA or cp in _NONCHARACTERS:
        return "ignorable"
    if cp in _EXOTIC_SPACES:
        return "exotic_space"
    return None


def inspect_text(text: str) -> TextReport:
    counts: dict[int, int] = {}
    categories: dict[int, str] = {}
    for ch in text:
        cp = ord(ch)
        cat = _classify(cp)
        if cat is None:
            continue
        counts[cp] = counts.get(cp, 0) + 1
        categories[cp] = cat

    findings = [
        TextFinding(
            codepoint=cp,
            name=unicodedata.name(chr(cp), f"U+{cp:04X}"),
            category=categories[cp],
            count=n,
        )
        for cp, n in sorted(counts.items())
    ]
    return TextReport(findings=findings, total=sum(counts.values()))


def clean_text(text: str, *, normalize_spaces: bool = True) -> tuple[str, int]:
    """Strip invisible carriers. Returns (cleaned_text, removed_count).

    normalize_spaces: when True (default), exotic spaces are replaced with
    a regular U+0020 instead of being dropped outright, since dropping a
    word-separating space would corrupt layout. Languages whose typography
    relies on a non-breaking space before punctuation (French `« ... »`,
    `; : ! ?`) should pass normalize_spaces=False to leave those alone —
    only the zero-width/bidi/tag carriers are removed either way.
    """
    out = []
    removed = 0
    for ch in text:
        cat = _classify(ord(ch))
        if cat is None:
            out.append(ch)
            continue
        removed += 1
        if cat == "exotic_space" and not normalize_spaces:
            out.append(ch)
            removed -= 1
            continue
        if cat == "exotic_space" and normalize_spaces:
            out.append(" ")
            continue
        # zero_width / bidi / tag / ignorable / soft_hyphen: drop entirely
    return "".join(out), removed
