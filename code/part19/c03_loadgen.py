#!/usr/bin/env python3
"""Load generator for an OpenAI-compatible streaming chat endpoint. Standard library only.

Two arrival models:
  closed  N workers; each sends its next request after the previous one finishes.
  open    requests arrive on a Poisson schedule at a fixed rate, whatever the server does.
Per request it records time to first token (TTFT), the mean gap between later tokens
(TPOT), end-to-end time, token count and status. The summary reports nearest-rank
percentiles, throughput, error rate, and request-level goodput: requests that met every
latency objective, per second.

Prompt length is approximated by repeating a short word. A real tokenizer would count
differently, so treat input length as approximate and read real counts from the server.
"""
from __future__ import annotations

import argparse
import http.client
import json
import math
import random
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class Result:
    ok: bool
    status: int
    ttft_s: float | None
    tpot_s: float | None
    e2e_s: float
    tokens: int
    start_s: float
    error: str = ""


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile. p in (0, 100]. Empty input gives None."""
    if not values:
        return None
    if not 0 < p <= 100:
        raise ValueError("p must be in (0, 100]")
    s = sorted(values)
    rank = max(1, math.ceil(p / 100.0 * len(s)))
    return s[rank - 1]


def make_prompt(rng: random.Random, mean: int, stddev: int) -> str:
    n = max(1, int(rng.gauss(mean, stddev)))
    return "word " * n


def one_request(base_url: str, model: str, prompt: str, max_tokens: int,
                timeout_s: float = 120.0) -> Result:
    u = urlparse(base_url)
    t0 = time.perf_counter()
    start_wall = time.time()
    conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout_s)
    body = json.dumps({"model": model, "stream": True, "max_tokens": max_tokens,
                       "messages": [{"role": "user", "content": prompt}]})
    ttft = None
    last = None
    gaps: list[float] = []
    tokens = 0
    try:
        conn.request("POST", "/v1/chat/completions", body=body,
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        if resp.status != 200:
            resp.read()
            return Result(False, resp.status, None, None, time.perf_counter() - t0, 0,
                          start_wall, f"http {resp.status}")
        while True:
            line = resp.readline()
            if not line:
                break
            line = line.strip()
            if not line.startswith(b"data:"):
                continue
            payload = line[5:].strip()
            if payload == b"[DONE]":
                break
            now = time.perf_counter()
            try:
                obj = json.loads(payload)
            except json.JSONDecodeError:
                return Result(False, 200, ttft, None, now - t0, tokens, start_wall, "bad chunk")
            delta = obj.get("choices", [{}])[0].get("delta", {})
            if delta.get("content"):
                tokens += 1
                if ttft is None:
                    ttft = now - t0
                else:
                    gaps.append(now - last)
                last = now
        e2e = time.perf_counter() - t0
        if ttft is None:
            return Result(False, 200, None, None, e2e, 0, start_wall, "no tokens")
        tpot = (sum(gaps) / len(gaps)) if gaps else 0.0
        return Result(True, 200, ttft, tpot, e2e, tokens, start_wall)
    except (OSError, http.client.HTTPException) as e:
        return Result(False, 0, None, None, time.perf_counter() - t0, tokens, start_wall, type(e).__name__)
    finally:
        conn.close()


def run_closed(base_url: str, model: str, concurrency: int, duration_s: float,
               prompt_mean: int, prompt_std: int, max_tokens: int, seed: int) -> tuple[list[Result], float]:
    results: list[Result] = []
    lock = threading.Lock()
    stop_at = time.perf_counter() + duration_s

    def worker(wid: int) -> None:
        rng = random.Random(seed * 1000 + wid)
        while time.perf_counter() < stop_at:
            r = one_request(base_url, model, make_prompt(rng, prompt_mean, prompt_std), max_tokens)
            with lock:
                results.append(r)

    t0 = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(concurrency)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results, time.perf_counter() - t0


def run_open(base_url: str, model: str, rate: float, duration_s: float,
             prompt_mean: int, prompt_std: int, max_tokens: int, seed: int,
             max_in_flight: int = 1000) -> tuple[list[Result], float]:
    """Poisson arrivals: gaps are exponential with mean 1/rate. Requests are never held back
    by slow responses, except by max_in_flight, which counts as a dropped request."""
    rng = random.Random(seed)
    results: list[Result] = []
    lock = threading.Lock()
    in_flight = [0]
    threads: list[threading.Thread] = []

    def fire(prompt: str) -> None:
        r = one_request(base_url, model, prompt, max_tokens)
        with lock:
            results.append(r)
            in_flight[0] -= 1

    t0 = time.perf_counter()
    next_at = t0
    while True:
        next_at += rng.expovariate(rate)
        if next_at - t0 >= duration_s:
            break
        delay = next_at - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
        with lock:
            if in_flight[0] >= max_in_flight:
                results.append(Result(False, 0, None, None, 0.0, 0, time.time(), "client in-flight cap"))
                continue
            in_flight[0] += 1
        th = threading.Thread(target=fire, args=(make_prompt(rng, prompt_mean, prompt_std),))
        th.start()
        threads.append(th)
    for th in threads:
        th.join()
    return results, time.perf_counter() - t0


def summarize(results: list[Result], wall_s: float, slo_ttft_ms: float | None = None,
              slo_tpot_ms: float | None = None) -> dict:
    ok = [r for r in results if r.ok]
    n = len(results)
    ttft = [r.ttft_s * 1000 for r in ok]
    tpot = [r.tpot_s * 1000 for r in ok]
    e2e = [r.e2e_s * 1000 for r in ok]
    tokens = sum(r.tokens for r in ok)

    def meets(r: Result) -> bool:
        if slo_ttft_ms is not None and r.ttft_s * 1000 > slo_ttft_ms:
            return False
        if slo_tpot_ms is not None and r.tpot_s * 1000 > slo_tpot_ms:
            return False
        return True

    good = [r for r in ok if meets(r)]
    return {
        "requests": n,
        "ok": len(ok),
        "error_rate": (n - len(ok)) / n if n else 0.0,
        "wall_s": wall_s,
        "req_per_s": len(ok) / wall_s if wall_s else 0.0,
        "output_tok_per_s": tokens / wall_s if wall_s else 0.0,
        "ttft_ms": {f"p{p}": percentile(ttft, p) for p in (50, 95, 99)},
        "tpot_ms": {f"p{p}": percentile(tpot, p) for p in (50, 95, 99)},
        "e2e_ms": {f"p{p}": percentile(e2e, p) for p in (50, 95, 99)},
        "mean_e2e_s": (sum(e2e) / len(e2e) / 1000) if e2e else None,
        "goodput_req_per_s": len(good) / wall_s if wall_s else 0.0,
        "goodput_fraction": (len(good) / n) if n else 0.0,
        "good_tok_per_s": sum(r.tokens for r in good) / wall_s if wall_s else 0.0,
        "slo": {"ttft_ms": slo_ttft_ms, "tpot_ms": slo_tpot_ms},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--model", default="mock-model")
    ap.add_argument("--mode", choices=["closed", "open"], default="closed")
    ap.add_argument("--concurrency", type=int, nargs="+", default=[8],
                    help="closed mode: one run per value (a sweep)")
    ap.add_argument("--rate", type=float, default=5.0, help="open mode: requests per second")
    ap.add_argument("--duration", type=float, default=20.0)
    ap.add_argument("--prompt-mean", type=int, default=1024)
    ap.add_argument("--prompt-std", type=int, default=128)
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--slo-ttft-ms", type=float, default=None)
    ap.add_argument("--slo-tpot-ms", type=float, default=None)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None, help="write the JSON summary list here")
    a = ap.parse_args()
    runs = []
    if a.mode == "closed":
        for c in a.concurrency:
            res, wall = run_closed(a.url, a.model, c, a.duration, a.prompt_mean, a.prompt_std,
                                   a.max_tokens, a.seed)
            s = summarize(res, wall, a.slo_ttft_ms, a.slo_tpot_ms)
            s["mode"], s["concurrency"] = "closed", c
            runs.append(s)
    else:
        res, wall = run_open(a.url, a.model, a.rate, a.duration, a.prompt_mean, a.prompt_std,
                             a.max_tokens, a.seed)
        s = summarize(res, wall, a.slo_ttft_ms, a.slo_tpot_ms)
        s["mode"], s["rate"] = "open", a.rate
        runs.append(s)
    text = json.dumps(runs, indent=2)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
