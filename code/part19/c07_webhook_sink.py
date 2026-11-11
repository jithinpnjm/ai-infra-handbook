#!/usr/bin/env python3
"""Webhook sink for the end-to-end test (Chapter 19.7). Standard library only.

Runs inside a container on the test network. Alertmanager POSTs to
/<receiver-name>. GET /dump returns every payload received, keyed by receiver.
Usage: python3 c07_webhook_sink.py [PORT]
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

got = {}
lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        with lock:
            got.setdefault(self.path.strip("/"), []).append(payload)
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        with lock:
            body = json.dumps(got).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9200
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
