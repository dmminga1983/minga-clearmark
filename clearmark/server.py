"""Stdlib-only HTTP service exposing inspect/clean over JSON+base64, so any
app (or the Claude Code skill in skills/clearmark/) can use this without a
Python runtime of its own.

    python3 -m clearmark.server --host 127.0.0.1 --port 8765

Endpoints:
    GET  /health            -> {"ok": true, "version": "..."}
    POST /inspect            {"file": "<base64>", "name": "notes.md"}
    POST /clean               {"file": "<base64>", "name": "notes.md"}

Auth: set CLEARMARK_API_KEY to require `Authorization: Bearer <key>` on
every request. Binds to 127.0.0.1 by default — pass --host to change that
for a trusted network only; this service has no rate limiting or TLS of
its own and is not meant to be exposed directly to the internet.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__, dispatch
from .i18n import detect_language, t

_API_KEY = os.environ.get("CLEARMARK_API_KEY")
_MAX_BODY = 50 * 1024 * 1024  # 50 MiB


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    server_version = f"clearmark/{__version__}"

    def _authorized(self) -> bool:
        if not _API_KEY:
            return True
        return self.headers.get("Authorization") == f"Bearer {_API_KEY}"

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > _MAX_BODY:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def do_GET(self):  # noqa: N802 (stdlib naming convention)
        if self.path == "/health":
            _json_response(self, 200, {"ok": True, "version": __version__})
            return
        _json_response(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self):  # noqa: N802
        if not self._authorized():
            _json_response(self, 401, {"ok": False, "error": "unauthorized"})
            return

        if self.path not in ("/inspect", "/clean"):
            _json_response(self, 404, {"ok": False, "error": "not found"})
            return

        lang = detect_language()
        body = self._read_json_body()
        if body is None or "file" not in body or "name" not in body:
            _json_response(self, 400, {"ok": False, "error": t("server.error.bad_request", lang, detail="expected {file, name}")})
            return

        try:
            raw = base64.b64decode(body["file"])
        except Exception:
            _json_response(self, 400, {"ok": False, "error": t("server.error.bad_request", lang, detail="bad base64")})
            return

        name = str(body["name"])
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / name
            src.write_bytes(raw)
            kind = dispatch.classify(src)
            if kind == "unknown":
                _json_response(self, 400, {"ok": False, "error": t("server.error.unknown_format", lang, name=name)})
                return

            if self.path == "/inspect":
                report = dispatch.inspect_file(src)
                _json_response(self, 200, {
                    "ok": True,
                    "kind": report.kind,
                    "suspicious": report.suspicious,
                    "findings": report.detail,
                })
                return

            dst = Path(tmp) / f"out_{name}"
            kind, removed = dispatch.clean_file(src, dst)
            cleaned_b64 = base64.b64encode(dst.read_bytes()).decode("ascii")
            _json_response(self, 200, {
                "ok": True,
                "kind": kind,
                "removed": removed,
                "cleaned": cleaned_b64,
            })

    def log_message(self, fmt, *fmt_args):  # quieter default logging
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="clearmark HTTP service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(t("server.starting", detect_language(), host=args.host, port=args.port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
