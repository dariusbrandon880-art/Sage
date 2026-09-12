"""Minimal external AIET disruption service used only by the deployment harness.
Returns a real HTTP 503 so Trial 3 observes an actual network/service failure.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(503)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"service_unavailable","source":"aiet-disruption-sidecar"}')

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8090"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
