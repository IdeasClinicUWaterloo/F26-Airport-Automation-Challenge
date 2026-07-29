"""
Minimal local HTTP server for the live radar view.

Serves the static page once, then the page's own JS polls /tracks.json on an
interval -- no full page reload, so aircraft can be animated smoothly between
updates instead of hard-snapping. Deliberately stdlib-only (no new
dependency): http.server is enough for a single-machine hackathon demo.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from snapshot import build_snapshot

STATIC_DIR = Path(__file__).parent / "static"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


def _make_handler(manager):
    class RadarHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # keep the poll-loop console output clean

        def do_GET(self):
            if self.path == "/tracks.json":
                self._serve_json(build_snapshot(manager))
                return
            self._serve_static()

        def _serve_json(self, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _serve_static(self):
            rel_path = "index.html" if self.path in ("/", "") else self.path.lstrip("/")
            file_path = (STATIC_DIR / rel_path).resolve()

            if STATIC_DIR not in file_path.parents or not file_path.is_file():
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPES.get(file_path.suffix, "text/plain"))
            self.end_headers()
            self.wfile.write(file_path.read_bytes())

    return RadarHandler


def start_server(manager, port=8765):
    """Starts the server on a background thread and returns it (call .shutdown() to stop)."""

    server = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(manager))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
