"""clearmark CLI: inspect and clean files from the command line.

    clearmark inspect notes.md
    clearmark clean notes.md -o notes.cleaned.md
    clearmark clean --lang ru photo.png -o photo.cleaned.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, dispatch
from .i18n import available_languages, detect_language, t


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("path", help="file to process")
    p.add_argument("--lang", default=None, help="message language (default: auto-detect)")


def cmd_inspect(args: argparse.Namespace) -> int:
    lang = args.lang or detect_language()
    path = Path(args.path)
    if not path.exists():
        print(t("cli.error.not_found", lang, path=path), file=sys.stderr)
        return 1
    print(t("cli.inspect.header", lang, path=path))
    report = dispatch.inspect_file(path)
    if not report.suspicious:
        print(t("cli.inspect.clean", lang))
        return 0
    print(t("cli.inspect.found", lang, count=len(report.detail)))
    for line in report.detail:
        print(t("cli.inspect.marker_line", lang, kind=report.kind, detail=line))
    return 2  # non-zero so this is scriptable (e.g. in a pre-commit hook)


def cmd_clean(args: argparse.Namespace) -> int:
    lang = args.lang or detect_language()
    path = Path(args.path)
    if not path.exists():
        print(t("cli.error.not_found", lang, path=path), file=sys.stderr)
        return 1

    out = Path(args.output) if args.output else path.with_suffix(f".cleaned{path.suffix}")
    if out.exists() and not args.force:
        print(t("cli.error.output_exists", lang, path=out), file=sys.stderr)
        return 1

    if args.dry_run:
        report = dispatch.inspect_file(path)
        print(t("cli.clean.dry_run", lang, path=path, count=len(report.detail)))
        return 0

    try:
        kind, removed = dispatch.clean_file(path, out, normalize_spaces=not args.no_normalize_spaces)
    except ValueError:
        print(t("cli.error.unsupported", lang, ext=path.suffix), file=sys.stderr)
        return 1

    if removed == 0:
        out.unlink(missing_ok=True)
        print(t("cli.clean.already_clean", lang, path=path))
        return 0

    print(t("cli.clean.done", lang, input=path, output=out, removed=removed))
    return 0


def cmd_languages(args: argparse.Namespace) -> int:
    print(t("cli.lang.list", args.lang, langs=", ".join(available_languages())))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clearmark", description="Strip AI provenance marks from your own content.")
    parser.add_argument("--version", action="version", version=f"clearmark {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect", help="report provenance marks without modifying the file")
    _add_common(p_inspect)
    p_inspect.set_defaults(func=cmd_inspect)

    p_clean = sub.add_parser("clean", help="write a cleaned copy of the file")
    _add_common(p_clean)
    p_clean.add_argument("-o", "--output", default=None, help="output path (default: <name>.cleaned<ext>)")
    p_clean.add_argument("--force", action="store_true", help="overwrite an existing output file")
    p_clean.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    p_clean.add_argument(
        "--no-normalize-spaces",
        action="store_true",
        help="keep exotic spaces as-is instead of replacing them with a plain space "
        "(use for languages where a non-breaking space is meaningful typography, e.g. French)",
    )
    p_clean.set_defaults(func=cmd_clean)

    p_langs = sub.add_parser("languages", help="list available CLI message languages")
    p_langs.add_argument("--lang", default=None)
    p_langs.set_defaults(func=cmd_languages)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
