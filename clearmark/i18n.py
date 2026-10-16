"""Minimal, dependency-free i18n for CLI/server user-facing messages.

Library/API code (docstrings, exceptions meant for developers, log lines)
stays in English, as is standard for open-source tooling. This module only
covers strings a *human user* reads: CLI output and HTTP error bodies.

Locale selection order:
    1. explicit `lang=` argument
    2. CLEARMARK_LANG environment variable
    3. the system locale (so a user on a Russian system gets Russian
       automatically, without any configuration)
    4. "en" as the final fallback

Adding a language: drop a `<code>.json` file next to this module in
`clearmark/locales/` with the same keys as `locales/en.json`. Missing keys
fall back to English automatically, so a partial translation is safe to ship.
"""

from __future__ import annotations

import json
import locale
import os
from functools import cache
from pathlib import Path

_LOCALES_DIR = Path(__file__).parent / "locales"
_FALLBACK_LANG = "en"


@cache
def _load(lang: str) -> dict:
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def available_languages() -> list[str]:
    if not _LOCALES_DIR.exists():
        return [_FALLBACK_LANG]
    return sorted(p.stem for p in _LOCALES_DIR.glob("*.json"))


def detect_language() -> str:
    env_lang = os.environ.get("CLEARMARK_LANG")
    if env_lang:
        return env_lang.split("_")[0].split("-")[0].lower()
    try:
        sys_lang, _ = locale.getlocale()
    except (ValueError, TypeError):
        sys_lang = None
    if not sys_lang:
        sys_lang = os.environ.get("LANG", "")
    if sys_lang:
        return sys_lang.split("_")[0].split(".")[0].lower()
    return _FALLBACK_LANG


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """Translate `key`, falling back to English, then to the key itself."""
    lang = (lang or detect_language()).lower()
    catalog = _load(lang)
    fallback = _load(_FALLBACK_LANG)
    template = catalog.get(key) or fallback.get(key) or key
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
