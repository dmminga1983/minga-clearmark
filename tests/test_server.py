import base64
import json
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from clearmark.server import Handler

ZWSP = chr(0x200B)


@pytest.fixture()
def running_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    thread.join(timeout=2)


def test_health(running_server):
    with urllib.request.urlopen(f"{running_server}/health") as resp:
        data = json.loads(resp.read())
    assert data["ok"] is True


def test_inspect_text_with_marker(running_server):
    payload = {
        "file": base64.b64encode(("hello" + ZWSP + "world").encode("utf-8")).decode("ascii"),
        "name": "notes.txt",
    }
    req = urllib.request.Request(
        f"{running_server}/inspect",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    assert data["ok"] is True
    assert data["suspicious"] is True


def test_clean_text_roundtrip(running_server):
    payload = {
        "file": base64.b64encode(("hello" + ZWSP + "world").encode("utf-8")).decode("ascii"),
        "name": "notes.txt",
    }
    req = urllib.request.Request(
        f"{running_server}/clean",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    assert data["ok"] is True
    cleaned = base64.b64decode(data["cleaned"]).decode("utf-8")
    assert cleaned == "helloworld"
