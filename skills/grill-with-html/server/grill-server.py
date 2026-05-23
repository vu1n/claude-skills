#!/usr/bin/env python3
"""Minimal localhost sync server for grill-with-html sessions.

Run:
    python3 grill-server.py <design-dir> [--port 4388]

The server is the sync layer over chat.md, the canonical record. It serves the
turn-NN.html files, exposes chat.md via HTTP, and accepts user replies posted
from the in-page composer (appending them to chat.md under the latest turn's
**User**: block). No persistent state of its own — kill it, restart it,
nothing is lost.

No external dependencies. No global config mutation. Listens on 127.0.0.1
only. Ctrl-C to stop.
"""

import argparse
import http.server
import json
import os
import socketserver
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse

LATEST_USER_HEADING = "**User**:"


def append_user_reply(chat_path: Path, text: str) -> None:
    """Append the user's reply to the latest turn's `**User**:` block in chat.md.

    Semantics: the user block extends from `**User**:` until the next `---`
    separator, the next `## Turn` heading, or EOF. The reply is appended to
    the end of that block (after any existing content), separated by a blank
    line. If the block has no content yet, the reply becomes its first content.
    """
    if not chat_path.exists():
        chat_path.write_text(f"# Chat\n\n## Turn 1\n\n{LATEST_USER_HEADING}\n\n{text.rstrip()}\n")
        return

    content = chat_path.read_text()
    lines = content.split("\n")

    last_user_idx = None
    for i, line in enumerate(lines):
        if line.strip() == LATEST_USER_HEADING:
            last_user_idx = i

    if last_user_idx is None:
        chat_path.write_text(content.rstrip() + f"\n\n{LATEST_USER_HEADING}\n\n{text.rstrip()}\n")
        return

    block_end = len(lines)
    for i in range(last_user_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped == "---" or stripped.startswith("## Turn "):
            block_end = i
            break

    content_end = block_end
    while content_end > last_user_idx + 1 and lines[content_end - 1].strip() == "":
        content_end -= 1

    if content_end == last_user_idx + 1:
        insertion = ["", text.rstrip(), ""]
    else:
        insertion = ["", text.rstrip(), ""]
    new_lines = lines[:content_end] + insertion + lines[block_end:]
    chat_path.write_text("\n".join(new_lines))


class GrillHandler(http.server.SimpleHTTPRequestHandler):
    design_dir: Path = None
    chat_path: Path = None
    lock = threading.Lock()

    def do_GET(self):  # noqa: N802 - stdlib API
        path = urlparse(self.path).path
        if path == "/healthz":
            self._send_json({"ok": True, "design_dir": str(self.design_dir)})
            return
        if path == "/chat.md":
            self._send_file(self.chat_path, "text/markdown; charset=utf-8")
            return
        if path == "/decisions.md":
            self._send_file(self.design_dir / "decisions.md", "text/markdown; charset=utf-8")
            return
        super().do_GET()

    def do_POST(self):  # noqa: N802 - stdlib API
        path = urlparse(self.path).path
        if path != "/reply":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body or b"{}")
            text = str(payload.get("text", "")).strip()
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "invalid json"}, status=400)
            return
        if not text:
            self._send_json({"ok": False, "error": "empty text"}, status=400)
            return
        with self.lock:
            append_user_reply(self.chat_path, text)
        self._send_json({"ok": True})

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_response(404)
            self.end_headers()
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, obj: dict, status: int = 200) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):  # noqa: A002 - stdlib API
        return  # quiet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("design_dir", help="path to docs/design/<slug>/ directory")
    parser.add_argument("--port", type=int, default=4388, help="port (default 4388)")
    args = parser.parse_args()

    design_dir = Path(args.design_dir).resolve()
    if not design_dir.is_dir():
        sys.exit(f"error: {design_dir} is not a directory")

    GrillHandler.design_dir = design_dir
    GrillHandler.chat_path = design_dir / "chat.md"
    os.chdir(design_dir)

    with socketserver.TCPServer(("127.0.0.1", args.port), GrillHandler) as httpd:
        url = f"http://127.0.0.1:{args.port}"
        print(f"grill-server: serving {design_dir} at {url}")
        latest_turn = sorted(design_dir.glob("turn-*.html"))[-1].name if list(design_dir.glob("turn-*.html")) else "turn-01.html"
        print(f"  open {url}/{latest_turn}")
        print("  Ctrl-C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\ngrill-server: stopping")


if __name__ == "__main__":
    main()
