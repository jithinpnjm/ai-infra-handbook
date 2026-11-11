#!/usr/bin/env python3
"""A local mock of an OpenAI-compatible streaming chat server, for testing a load generator.

Standard library only. It is NOT a model and says nothing about real engine speed. It
imitates the behaviours a load test must handle: server-sent-event streaming, a fixed
first-token delay, a fixed inter-token delay, a limit on requests served at once with
queueing behind it, a queue limit that answers HTTP 429, and a switch that makes every
Nth request fail.

Endpoints: GET /health, GET /v1/models, POST /v1/chat/completions (stream true or false).
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class MockState:
    def __init__(self, ttft_ms: float = 20.0, itl_ms: float = 5.0, slots: int = 4,
                 max_queue: int = 1000, fail_every: int = 0, model: str = "mock-model"):
        self.ttft_s = ttft_ms / 1000.0
        self.itl_s = itl_ms / 1000.0
        self.slots = threading.BoundedSemaphore(slots)
        self.max_queue = max_queue
        self.fail_every = fail_every
        self.model = model
        self.lock = threading.Lock()
        self.waiting = 0
        self.running = 0
        self.total = 0

    def next_index(self) -> int:
        with self.lock:
            self.total += 1
            return self.total

    def try_enter_queue(self) -> bool:
        with self.lock:
            if self.waiting >= self.max_queue:
                return False
            self.waiting += 1
            return True

    def start_running(self) -> None:
        with self.lock:
            self.waiting -= 1
            self.running += 1

    def stop_running(self) -> None:
        with self.lock:
            self.running -= 1


def make_handler(state: MockState):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):  # keep test output quiet
            pass

        def _json(self, code: int, obj: dict) -> None:
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._json(200, {"status": "ok"})
            elif self.path == "/v1/models":
                self._json(200, {"object": "list", "data": [{"id": state.model, "object": "model"}]})
            elif self.path == "/stats":
                with state.lock:
                    self._json(200, {"waiting": state.waiting, "running": state.running, "total": state.total})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                self._json(404, {"error": "not found"})
                return
            n = int(self.headers.get("Content-Length", "0"))
            try:
                req = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                self._json(400, {"error": "bad json"})
                return
            idx = state.next_index()
            if state.fail_every and idx % state.fail_every == 0:
                self._json(500, {"error": "injected failure"})
                return
            if not state.try_enter_queue():
                self._json(429, {"error": "queue full"})
                return
            max_tokens = int(req.get("max_tokens", 16))
            stream = bool(req.get("stream", False))
            state.slots.acquire()
            state.start_running()
            try:
                time.sleep(state.ttft_s)
                if not stream:
                    time.sleep(state.itl_s * max(max_tokens - 1, 0))
                    self._json(200, {"model": state.model, "choices": [
                        {"message": {"role": "assistant", "content": "tok " * max_tokens}}],
                        "usage": {"completion_tokens": max_tokens}})
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                for i in range(max_tokens):
                    if i:
                        time.sleep(state.itl_s)
                    chunk = {"model": state.model, "choices": [{"delta": {"content": "tok "}}]}
                    self._chunk(f"data: {json.dumps(chunk)}\n\n".encode())
                self._chunk(b"data: [DONE]\n\n")
                self.wfile.write(b"0\r\n\r\n")
            finally:
                state.stop_running()
                state.slots.release()

        def _chunk(self, data: bytes) -> None:
            self.wfile.write(f"{len(data):X}\r\n".encode() + data + b"\r\n")
            self.wfile.flush()

    return Handler


def start(state: MockState | None = None, host: str = "127.0.0.1", port: int = 0):
    """Start in a background thread. Returns (server, state, base_url). Call server.shutdown() to stop."""
    state = state or MockState()
    srv = ThreadingHTTPServer((host, port), make_handler(state))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, state, f"http://{host}:{srv.server_address[1]}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--ttft-ms", type=float, default=20.0)
    ap.add_argument("--itl-ms", type=float, default=5.0)
    ap.add_argument("--slots", type=int, default=4)
    ap.add_argument("--max-queue", type=int, default=1000)
    ap.add_argument("--fail-every", type=int, default=0)
    a = ap.parse_args()
    st = MockState(a.ttft_ms, a.itl_ms, a.slots, a.max_queue, a.fail_every)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(st))
    print(f"mock server on http://127.0.0.1:{a.port}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
