# clearmark

**Русская версия: [README.md](README.md)**

A privacy tool that strips AI provenance marks — invisible Unicode
characters, EXIF/XMP/C2PA metadata, and document properties — from
**your own** text, images, PDFs, and DOCX/XLSX/PPTX files.

**This is not a tool for academic fraud or for passing AI-generated text
off as human-written.** It exists for privacy and metadata hygiene on
content you own or are authorized to process — drafts, working documents,
your own photos. Whether it's appropriate for your situation is your call
— see "Ethics" below.

[![CI](https://github.com/dmminga1983/minga-clearmark/actions/workflows/ci.yml/badge.svg)](https://github.com/dmminga1983/minga-clearmark/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What it does

| Layer | Removes | How |
| --- | --- | --- |
| **Text (Layer A)** | Invisible Unicode carriers: zero-width spaces, bidi control characters, language-tag characters, exotic spaces, soft hyphen | Deterministic Python, no external services |
| **Images** | EXIF, XMP, PNG text chunks (`Software`, `parameters`, `C2PA`, etc.) | PNG, JPEG, WebP, BMP, GIF, TIFF — via Pillow |
| **PDF** | Document Info dictionary (Author, Producer, Creator…), XMP stream | pypdf (full object-graph rebuild, not an incremental edit) |
| **DOCX/XLSX/PPTX** | `docProps/core.xml` (author, subject, keywords…), `docProps/custom.xml` | Entry-by-entry zip container rebuild |

**What it deliberately doesn't do:** statistical watermarks embedded in
token-sampling choices during text generation (what's sometimes called
SynthID-text/KGW-class schemes). Reliably removing those requires
rewriting the text with another model, which unavoidably degrades style
and precision — that's a tradeoff the user should make deliberately, not
one a tool should apply by default. Pixel-domain image watermarks
(steganographic, resave-resistant) are also out of scope for this project.

## Install

```bash
git clone https://github.com/dmminga1983/minga-clearmark.git
cd clearmark
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Requires Python 3.10+. Dependencies: `Pillow`, `pypdf` (see `requirements.txt`).

## CLI usage

CLI messages are multilingual: auto-detected from the system locale, or
set explicitly with `--lang ru` / `--lang en`, or the `CLEARMARK_LANG`
environment variable. List available languages with `clearmark languages`.

```bash
# Report findings without modifying the file
clearmark inspect draft.md

# Write a cleaned copy
clearmark clean draft.md -o draft.cleaned.md
clearmark clean photo.png -o photo.cleaned.png
clearmark clean report.docx -o report.cleaned.docx

# Dry run — report only, nothing written
clearmark clean --dry-run draft.md

# For languages where a non-breaking space is meaningful typography
# (e.g. French), keep exotic spaces instead of normalizing them:
clearmark clean --no-normalize-spaces draft.md
```

`clearmark inspect` exit codes: `0` clean, `2` marks found (handy for a
pre-commit hook), `1` error (file not found, unsupported format).

## HTTP service

```bash
python3 -m clearmark.server --host 127.0.0.1 --port 8765
```

```bash
curl -s http://127.0.0.1:8765/health

curl -s -X POST http://127.0.0.1:8765/inspect \
  -H 'Content-Type: application/json' \
  -d "{\"file\": \"$(base64 < draft.md | tr -d '\n')\", \"name\": \"draft.md\"}"
```

Binds to `127.0.0.1` only by default. Set `CLEARMARK_API_KEY` to require
`Authorization: Bearer <key>` on every request (see `.env.example`).

## Development

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

## Ethics and responsibility

This project is for privacy and metadata hygiene on **your own** content
— not for academic fraud, not for passing AI output off as human-written,
and not for evading plagiarism detection. You're responsible for
complying with applicable law, your organization's/institution's rules,
and the terms of service of whatever produced the content you process.
The developers disclaim liability for misuse.

## License

MIT — see [LICENSE](LICENSE).
