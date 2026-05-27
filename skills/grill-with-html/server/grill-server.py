#!/usr/bin/env python3
# ruff: noqa: I001
"""Localhost sync server for grill-with-html sessions.

Single canonical file: <design-dir>/design.html. The HTML carries the design
surface, the conversation (as `<article>` elements inside `<section data-chat>`),
the decisions (as `<article>` elements inside `<aside data-decisions>`), and any
user annotations (as `<mark>` elements with paired `<aside>` comments). The
agent reads and edits design.html directly; this server is here so the BROWSER
can also write to the file (user composer Send, user inline annotations).

Run:
    python3 grill-server.py <design-dir> [--port 4388]

Endpoints:
    GET  /                 — redirects to /design.html
    GET  /design.html      — the file
    GET  /healthz          — liveness for client server-detect
    GET  /chat/latest-reply — text of most recent <article data-from="user">
    GET  /chat/recent?turns=3 — last N turn-blocks (agent + user articles)
    GET  /decisions        — current <aside data-decisions> contents
    GET  /design           — design surface only (no chat, no decisions)
    GET  /annotations/pending — <aside data-comment-target> blocks not yet replied to
    POST /reply            — body {text} — appends <article data-from="user"> to <section data-chat>
    POST /annotation       — body {element_id, selected_text, comment} — wraps first occurrence
                             of selected_text in element_id with <mark>, adds paired <aside>
                             in <section data-chat>

No external deps, no install, no global config. Listens on 127.0.0.1 only.
Ctrl-C to stop.
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import re
import socketserver
import sys
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DESIGN_FILE = "design.html"


def read_design(design_path: Path) -> str:
    return design_path.read_text() if design_path.exists() else ""


def write_design(design_path: Path, text: str) -> None:
    design_path.write_text(text)


def find_section(html: str, attr: str) -> tuple[int, int] | None:
    """Find the open and close positions of the first <section> or <aside> with attr.

    Returns (open_tag_end, close_tag_start) — positions inside the element's content.
    Assumes no nested <section>/<aside> with the same attr.
    """
    open_match = re.search(rf"<(section|aside)[^>]*\b{attr}\b[^>]*>", html)
    if not open_match:
        return None
    tag = open_match.group(1)
    open_end = open_match.end()
    close_match = re.search(rf"</{tag}>", html[open_end:])
    if not close_match:
        return None
    return open_end, open_end + close_match.start()


def next_id(html: str, prefix: str) -> str:
    """Pick the next unused id like m1, m2, ... or a1, a2, ... based on what's already in html."""
    nums = [int(m) for m in re.findall(rf'\bid="{re.escape(prefix)}(\d+)"', html)]
    return f"{prefix}{(max(nums) + 1) if nums else 1}"


def append_user_reply(html: str, text: str, turn: int | None = None) -> str:
    section = find_section(html, 'data-chat')
    if section is None:
        return html
    open_end, close_start = section
    turn_attr = f' data-turn="{turn}"' if turn is not None else ""
    article = (
        f'\n    <article data-from="user"{turn_attr}>\n'
        f'      <p>{html_escape(text)}</p>\n'
        f'    </article>\n'
    )
    return html[:close_start] + article + html[close_start:]


def add_annotation(html: str, element_id: str, selected_text: str, comment: str) -> tuple[str, str | None]:
    """Wrap first occurrence of selected_text inside element_id with <mark>, add paired <aside>.

    Returns (new_html, mark_id) on success, (html, None) on failure.
    """
    element_re = re.compile(
        rf'(<(?P<tag>\w+)[^>]*\bid="{re.escape(element_id)}"[^>]*>)(?P<body>.*?)(</(?P=tag)>)',
        re.DOTALL,
    )
    m = element_re.search(html)
    if not m:
        return html, None
    body = m.group("body")
    if selected_text not in body:
        return html, None
    mark_id = next_id(html, "m")
    annot_id = next_id(html, "a")
    wrapped = body.replace(
        selected_text,
        f'<mark id="{mark_id}" data-annotation="{annot_id}">{selected_text}</mark>',
        1,
    )
    new_element = m.group(1) + wrapped + m.group(4)
    html2 = html[: m.start()] + new_element + html[m.end():]

    section = find_section(html2, 'data-chat')
    if section is None:
        return html2, mark_id
    open_end, close_start = section
    aside = (
        f'\n    <aside id="{annot_id}" data-comment-target="{mark_id}" data-from="user">\n'
        f'      <p>{html_escape(comment)}</p>\n'
        f'    </aside>\n'
    )
    return html2[:close_start] + aside + html2[close_start:], mark_id


def extract_section_content(html: str, attr: str) -> str:
    section = find_section(html, attr)
    if section is None:
        return ""
    open_end, close_start = section
    return html[open_end:close_start].strip()


def extract_latest_user_reply(html: str) -> str:
    matches = re.findall(
        r'<article[^>]*\bdata-from="user"[^>]*>(.*?)</article>',
        html,
        re.DOTALL,
    )
    if not matches:
        return ""
    inner = matches[-1].strip()
    text = re.sub(r"<[^>]+>", "", inner).strip()
    return text


def extract_recent_turns(html: str, turns: int) -> str:
    chat = extract_section_content(html, 'data-chat')
    articles = re.findall(r'<article[^>]*>.*?</article>', chat, re.DOTALL)
    return "\n".join(articles[-turns * 2:])


def extract_pending_annotations(html: str) -> str:
    chat = extract_section_content(html, 'data-chat')
    asides = re.findall(
        r'<aside[^>]*\bdata-comment-target="[^"]+"[^>]*\bdata-from="user"[^>]*>.*?</aside>',
        chat,
        re.DOTALL,
    )
    answered_targets = set(
        re.findall(
            r'<aside[^>]*\bdata-comment-target="([^"]+)"[^>]*\bdata-from="agent"',
            chat,
        )
    )
    target_re = re.compile(r'\bdata-comment-target="([^"]+)"')
    pending = []
    for a in asides:
        t = target_re.search(a)
        if t and t.group(1) not in answered_targets:
            pending.append(a)
    return "\n".join(pending)


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class GrillHandler(http.server.SimpleHTTPRequestHandler):
    design_dir: Path = None
    design_path: Path = None
    write_lock = threading.Lock()

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/design.html")
            self.end_headers()
            return
        if path == "/healthz":
            self._send_json({"ok": True, "design_dir": str(self.design_dir)})
            return
        if path == "/chat/latest-reply":
            self._send_text(extract_latest_user_reply(read_design(self.design_path)))
            return
        if path == "/chat/recent":
            qs = parse_qs(urlparse(self.path).query)
            turns = int(qs.get("turns", ["3"])[0])
            self._send_text(extract_recent_turns(read_design(self.design_path), turns))
            return
        if path == "/decisions":
            self._send_text(extract_section_content(read_design(self.design_path), 'data-decisions'))
            return
        if path == "/design":
            self._send_text(extract_section_content(read_design(self.design_path), 'data-design-surface'))
            return
        if path == "/annotations/pending":
            self._send_text(extract_pending_annotations(read_design(self.design_path)))
            return
        super().do_GET()

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "invalid json"}, status=400)
            return

        if path == "/reply":
            text = str(payload.get("text", "")).strip()
            if not text:
                self._send_json({"ok": False, "error": "empty text"}, status=400)
                return
            with self.write_lock:
                html = read_design(self.design_path)
                html = append_user_reply(html, text)
                write_design(self.design_path, html)
            self._send_json({"ok": True})
            return

        if path == "/annotation":
            element_id = str(payload.get("element_id", "")).strip()
            selected_text = str(payload.get("selected_text", "")).strip()
            comment = str(payload.get("comment", "")).strip()
            if not (element_id and selected_text and comment):
                self._send_json({"ok": False, "error": "element_id, selected_text, comment all required"}, status=400)
                return
            with self.write_lock:
                html = read_design(self.design_path)
                html2, mark_id = add_annotation(html, element_id, selected_text, comment)
                if mark_id is None:
                    self._send_json({"ok": False, "error": "could not find element_id or selected_text"}, status=404)
                    return
                write_design(self.design_path, html2)
            self._send_json({"ok": True, "mark_id": mark_id})
            return

        self.send_response(404)
        self.end_headers()

    def _send_text(self, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
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

    def log_message(self, format, *args):  # noqa: A002
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("design_dir", help="directory containing design.html")
    parser.add_argument("--port", type=int, default=4388)
    args = parser.parse_args()

    design_dir = Path(args.design_dir).resolve()
    if not design_dir.is_dir():
        sys.exit(f"error: {design_dir} is not a directory")

    GrillHandler.design_dir = design_dir
    GrillHandler.design_path = design_dir / DESIGN_FILE
    os.chdir(design_dir)

    class _Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    with _Server(("127.0.0.1", args.port), GrillHandler) as httpd:
        url = f"http://127.0.0.1:{args.port}/design.html"
        print(f"grill-server: serving {design_dir}")
        print(f"  open {url}")
        print("  Ctrl-C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\ngrill-server: stopping")


if __name__ == "__main__":
    main()
