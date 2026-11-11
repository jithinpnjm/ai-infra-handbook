#!/usr/bin/env python3
"""Synthetic metrics exporter for the observability capstone (Chapter 19.7).

Standard library only. It serves /metrics in the Prometheus text format with
the metric names the platform rules and the dashboard use: DCGM 4.9.0 GPU
fields, vLLM engine gauges, gateway counters and a TTFT histogram, and one
OpenTelemetry Collector counter. Fault knobs are set with POST /set, so a test
can inject a GPU Xid, a probe signal or a gateway error rate and watch the
alert path react.

  GET  /metrics
  POST /set   JSON body, any of: xid {"node","gpu","value"}, probe 0|1,
              error_ratio 0..1, rps number, waiting number
Nothing here talks to a GPU.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BUCKETS = ["0.5", "1.0", "2.0", "+Inf"]


class State:
    def __init__(self, nodes=("n1", "n2"), gpus=2, models=("m1",)):
        self.lock = threading.Lock()
        self.nodes = list(nodes)
        self.gpus = gpus
        self.models = list(models)
        self.xid = {}               # (node, gpu) -> last Xid value
        self.probe = 0
        self.error_ratio = 0.0
        self.rps = 20.0
        self.waiting = 0
        self.good = {m: 0.0 for m in models}
        self.bad = {m: 0.0 for m in models}
        self.ttft = {m: [0.0] * len(BUCKETS) for m in models}
        self.last = time.monotonic()

    def advance(self):
        now = time.monotonic()
        dt, self.last = now - self.last, now
        for m in self.models:
            n = self.rps * dt
            self.bad[m] += n * self.error_ratio
            self.good[m] += n * (1 - self.error_ratio)
            for i, le in enumerate(BUCKETS):   # cumulative buckets: 90 percent under 0.5 s
                share = {"0.5": 0.9, "1.0": 0.97, "2.0": 0.99, "+Inf": 1.0}[le]
                self.ttft[m][i] += n * share

    def apply(self, body):
        with self.lock:
            self.advance()
            if "xid" in body:
                x = body["xid"]
                self.xid[(x["node"], str(x["gpu"]))] = float(x["value"])
            for key in ("probe", "error_ratio", "rps", "waiting"):
                if key in body:
                    setattr(self, key, body[key])

    def render(self):
        with self.lock:
            self.advance()
            out = []

            def gauge(name, help_, rows):
                out.append(f"# HELP {name} {help_}")
                out.append(f"# TYPE {name} gauge")
                out.extend(rows)

            def labels(**kw):
                return "{" + ",".join(f'{k}="{v}"' for k, v in kw.items()) + "}"

            util, used, cap, temp, xid, remap = [], [], [], [], [], []
            for n in self.nodes:
                for g in range(self.gpus):
                    lb = labels(node=n, gpu=g)
                    util.append(f"DCGM_FI_DEV_GPU_UTIL_RATIO{lb} 0.62")
                    used.append(f"DCGM_FI_DEV_FB_USED_BYTES{lb} 40000000000")
                    cap.append(f"DCGM_FI_DEV_FB_CAPACITY_BYTES{lb} 80000000000")
                    temp.append(f"DCGM_FI_DEV_GPU_TEMP_CELSIUS{lb} 64")
                    xid.append(f"DCGM_FI_DEV_XID_ERROR{lb} {self.xid.get((n, str(g)), 0.0)}")
                    remap.append(f"DCGM_FI_DEV_ROW_REMAP_FAILED{lb} 0")
            gauge("DCGM_FI_DEV_GPU_UTIL_RATIO", "GPU utilization as a ratio.", util)
            gauge("DCGM_FI_DEV_FB_USED_BYTES", "Used framebuffer memory in bytes.", used)
            gauge("DCGM_FI_DEV_FB_CAPACITY_BYTES", "Total framebuffer capacity in bytes.", cap)
            gauge("DCGM_FI_DEV_GPU_TEMP_CELSIUS", "GPU temperature (in C).", temp)
            gauge("DCGM_FI_DEV_XID_ERROR", "Value of the last XID error encountered.", xid)
            gauge("DCGM_FI_DEV_ROW_REMAP_FAILED", "Whether remapping of rows has failed", remap)
            for name, val in (("vllm:num_requests_waiting", self.waiting),
                              ("vllm:kv_cache_usage_perc", 0.42)):
                gauge(name, "synthetic", [f'{name}{labels(model_name=m, engine=0)} {val}'
                                          for m in self.models])
            out.append("# TYPE gateway_requests_total counter")
            for m in self.models:
                out.append(f'gateway_requests_total{labels(tenant="a", model=m, code=200, route="chat")} {self.good[m]:.3f}')
                out.append(f'gateway_requests_total{labels(tenant="a", model=m, code=500, route="chat")} {self.bad[m]:.3f}')
            out.append("# TYPE gateway_ttft_seconds histogram")
            for m in self.models:
                for le, v in zip(BUCKETS, self.ttft[m]):
                    out.append(f'gateway_ttft_seconds_bucket{labels(model=m, le=le)} {v:.3f}')
                out.append(f'gateway_ttft_seconds_count{labels(model=m)} {self.ttft[m][-1]:.3f}')
                out.append(f'gateway_ttft_seconds_sum{labels(model=m)} {self.ttft[m][-1] * 0.4:.3f}')
            out.append("# TYPE otelcol_receiver_refused_log_records counter")
            out.append('otelcol_receiver_refused_log_records{receiver="otlp",transport="http"} 0')
            gauge("c07_synthetic_probe", "1 while the probe is on", [f"c07_synthetic_probe {self.probe}"])
            return "\n".join(out) + "\n"


def make_server(state, host="127.0.0.1", port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path != "/metrics":
                self.send_error(404)
                return
            body = state.render().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != "/set":
                self.send_error(404)
                return
            n = int(self.headers.get("Content-Length", 0))
            try:
                state.apply(json.loads(self.rfile.read(n) or b"{}"))
            except (ValueError, KeyError, TypeError) as e:
                self.send_error(400, str(e))
                return
            self.send_response(204)
            self.end_headers()

    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9100
    make_server(State(), "0.0.0.0", port).serve_forever()
