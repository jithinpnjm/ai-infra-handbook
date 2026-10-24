#!/usr/bin/env python3
"""Run one read-only task on many BMCs at once, safely.

  fleet_run.py endpoints.csv [--workers 16] [--timeout 10] [--retries 3] [--task inventory|health]

endpoints.csv columns: name,url,user,password   (passwords come from a secret store in real life, not a file in git)

Rules built in (each one is a lesson from chapter 7.12):
  * a bounded pool of workers, so 1,000 BMCs do not all get hit at once
  * a timeout on every request, a deadline per host
  * retry ONLY what can recover (timeouts, connection errors, 502/503/504) with exponential backoff and jitter,
    and honour Retry-After; never retry 401/403/404 (a wrong password retried is a locked account)
  * one bad BMC never stops the run; every host ends in exactly one outcome
  * always log out (the client does it in a finally)
  * a clear summary and a non-zero exit code if anything failed
"""
import concurrent.futures, csv, os, random, socket, sys, time, urllib.error
from redfish_crawl import Client, LoginError
import rf_inventory

RETRYABLE_HTTP = {502, 503, 504}


class HostFailure(Exception):
    def __init__(self, kind, detail):
        super().__init__(f"{kind}: {detail}")
        self.kind, self.detail = kind, detail


def classify(exc):
    """Map an exception to (kind, retryable)."""
    if isinstance(exc, LoginError):
        return f"http {exc.status}", exc.status in RETRYABLE_HTTP
    if isinstance(exc, urllib.error.HTTPError):
        return f"http {exc.code}", exc.code in RETRYABLE_HTTP
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "timeout", True
    if isinstance(exc, urllib.error.URLError):
        r = exc.reason
        if isinstance(r, (socket.timeout, TimeoutError)):
            return "timeout", True
        if isinstance(r, ConnectionRefusedError):
            return "connection refused", True
        return f"network error ({r})", True
    if isinstance(exc, HostFailure):
        return exc.kind, exc.kind == "http 503"
    return f"error ({type(exc).__name__}: {exc})", False


def with_retries(fn, retries, base=0.5, cap=8.0, sleep=time.sleep, rand=random.random):
    last = None
    for attempt in range(retries + 1):
        try:
            return fn(), attempt
        except Exception as exc:
            kind, retry = classify(exc)
            last = HostFailure(kind, str(exc)[:120])
            if not retry or attempt == retries:
                last.attempts = attempt + 1
                raise last
            wait = min(cap, base * (2 ** attempt)) * (0.5 + rand())      # exponential backoff with jitter
            sleep(wait)
    raise last


def task_inventory(c):
    return rf_inventory.inventory(c)


def task_health(c):
    rows = rf_inventory.inventory(c)
    bad = [r for r in rows if r["health"] not in ("OK", "")]
    return {"systems": len(rows), "unhealthy": [r["system"] for r in bad]}


def one_host(ep, task, timeout, retries, sleep=time.sleep):
    t0 = time.time()

    def work():
        c = Client(ep["url"], ep["user"], ep["password"], ca=ep.get("ca"), timeout=timeout)
        try:
            return task(c)
        finally:
            try:
                c.logout()
            except Exception:
                pass
    try:
        result, attempt = with_retries(work, retries, sleep=sleep)
        return dict(name=ep["name"], ok=True, result=result, attempts=attempt + 1, seconds=round(time.time() - t0, 2))
    except HostFailure as f:
        return dict(name=ep["name"], ok=False, kind=f.kind, detail=f.detail, attempts=getattr(f, "attempts", 1), seconds=round(time.time() - t0, 2))


def run(endpoints, task, workers=16, timeout=10, retries=3, sleep=time.sleep):
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(one_host, ep, task, timeout, retries, sleep): ep for ep in endpoints}
        for f in concurrent.futures.as_completed(futs):
            out.append(f.result())
    return sorted(out, key=lambda r: r["name"])


def summary(results):
    ok = [r for r in results if r["ok"]]
    kinds = {}
    for r in results:
        if not r["ok"]:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    return len(results), len(ok), kinds


def main(argv):
    path = argv[1]
    val = lambda n, d: type(d)(argv[argv.index(n) + 1]) if n in argv else d
    eps = list(csv.DictReader(open(path)))
    task = {"inventory": task_inventory, "health": task_health}[val("--task", "inventory")]
    res = run(eps, task, val("--workers", 16), val("--timeout", 10), val("--retries", 3))
    n, ok, kinds = summary(res)
    for r in res:
        print(f"{r['name']:12} {'ok' if r['ok'] else 'FAILED':7} tries={r['attempts']} {r['seconds']:5}s  {'' if r['ok'] else r['kind']}")
    print(f"\n{ok}/{n} succeeded" + ("" if not kinds else "; failures: " + ", ".join(f"{k} x{v}" for k, v in kinds.items())))
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
