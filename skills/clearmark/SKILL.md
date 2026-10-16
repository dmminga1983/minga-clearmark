---
name: clearmark
description: Strip AI provenance marks (invisible Unicode, EXIF/XMP/C2PA metadata, doc properties) from the user's own text, image, PDF, or DOCX/XLSX/PPTX files, for privacy — not for passing AI output off as human-written. Use when the user asks to "remove watermarks/AI marks", "strip metadata", "clean this for privacy", or similar, on a file they own.
license: MIT
---

# clearmark

A privacy tool, not a plagiarism-evasion tool. Before using it, confirm the
request is about the user's own content (drafts, their own photos/documents)
— not about disguising AI-generated work as human-written for an academic,
journalistic, or similar integrity context. If that's what's being asked,
decline and say why instead of running the tool.

## Requirements

This skill shells out to the `clearmark` CLI. It must be installed in the
environment running this skill:

```bash
pip install -e /path/to/clearmark   # or: pip install clearmark, once published
```

If `clearmark` is not on PATH, tell the user to install it (see the
repository README) rather than trying to reimplement its logic inline.

## Usage

1. Identify the file the user wants cleaned and confirm it's their own
   content.
2. Inspect first, so the user knows what's actually there before anything
   is changed:

   ```bash
   clearmark inspect "<path>"
   ```

3. If marks are found and the user wants them removed:

   ```bash
   clearmark clean "<path>" -o "<path>.cleaned<ext>"
   ```

4. Report what was found/removed in plain language (which categories —
   invisible Unicode, EXIF, document properties — not a raw dump of every
   codepoint), and where the cleaned file was written.

## Scope reminder

This only handles the metadata/invisible-character layer (see the main
README's "what it deliberately doesn't do" section). If the user is
asking about statistical text watermarks (token-sampling marks) or
pixel-domain image watermarks, say that's out of scope for this tool
rather than guessing at a workaround.
