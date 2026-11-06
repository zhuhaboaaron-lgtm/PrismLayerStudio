"""Secure localhost-only static app server, reused by CLI and desktop entrypoints."""
from __future__ import annotations

import http.server
import sys
from pathlib import Path


def app_directory() -> Path:
    # PyInstaller extracts --onefile assets under sys._MEIPASS.
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    folder = base / "app"
    if not (folder / "index.html").is_file():
        raise FileNotFoundError(f"无法找到网页文件: {folder / 'index.html'}")
    return folder


def create_server(host: str = "127.0.0.1", port: int = 0):
    if host != "127.0.0.1":
        raise ValueError("Only the IPv4 loopback interface is supported")
    directory = str(app_directory())

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' blob:; object-src 'none'; frame-src 'none'; base-uri 'none'")
            self.send_header("Referrer-Policy", "no-referrer")
            super().end_headers()

        def parse_request(self):
            if not super().parse_request():
                return False
            if self.headers.get("Host") not in {"127.0.0.1:" + str(self.server.server_port),
                                                "localhost:" + str(self.server.server_port)}:
                self.send_error(403)
                return False
            return True

        def send_head(self):
            target = Path(self.translate_path(self.path)).resolve()
            if not target.is_relative_to(Path(directory).resolve()):
                self.send_error(403)
                return None
            if target.is_dir() and not (target / "index.html").is_file():
                self.send_error(403)
                return None
            return super().send_head()

        def log_message(self, fmt, *args):
            return  # quiet desktop app

    return http.server.ThreadingHTTPServer((host, port), Handler)
