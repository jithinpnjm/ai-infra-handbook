#!/usr/bin/env python3
"""Go or no-go rule for the chapter 19.3 capstone. Standard library only.

Input: a concurrency sweep, one c03_loadgen summary per concurrency level.
Output: the operating concurrency per replica, a scale target with headroom, the replicas
needed for a stated peak request rate, and GO or NO-GO with the reasons.

Rule, in words:
  1. A level passes when p95 TTFT and p95 TPOT are within the objectives, the error rate is
     within its limit, and enough requests met every objective.
  2. The operating point is the highest level in the unbroken run of passing levels that
     starts at the lowest level. A pass above a failure is treated as noise, not capacity.
  3. The scale target is the operating point times a headroom factor (my reasoning, not a
     standard value: it keeps the autoscaler away from the edge).
  4. Little's law gives the concurrent requests at peak: rate x mean end-to-end time.
     Replicas needed is that number divided by the scale target, rounded up.
  5. GO only if the replicas needed fit in the GPUs you can run.
"""
from __future__ import annotations

import json
import math
import sys


def level_passes(s: dict, slo_ttft_ms: float, slo_tpot_ms: float,
                 max_error_rate: float, min_goodput_fraction: float) -> tuple[bool, list[str]]:
    why: list[str] = []
    p95_ttft = s["ttft_ms"]["p95"]
    p95_tpot = s["tpot_ms"]["p95"]
    if p95_ttft is None or p95_tpot is None:
        return False, ["no successful requests"]
    if p95_ttft > slo_ttft_ms:
        why.append(f"p95 TTFT {p95_ttft:.0f} ms above {slo_ttft_ms:.0f} ms")
    if p95_tpot > slo_tpot_ms:
        why.append(f"p95 TPOT {p95_tpot:.1f} ms above {slo_tpot_ms:.1f} ms")
    if s["error_rate"] > max_error_rate:
        why.append(f"error rate {s['error_rate']:.3f} above {max_error_rate:.3f}")
    if s["goodput_fraction"] < min_goodput_fraction:
        why.append(f"only {s['goodput_fraction']:.2f} of requests met the objectives")
    return (not why), why


def decide(sweep: list[dict], slo_ttft_ms: float, slo_tpot_ms: float, peak_rps: float,
           max_replicas: int, headroom: float = 0.8, max_error_rate: float = 0.01,
           min_goodput_fraction: float = 0.95) -> dict:
    if not sweep:
        raise ValueError("empty sweep")
    if not 0 < headroom <= 1:
        raise ValueError("headroom must be in (0, 1]")
    levels = sorted(sweep, key=lambda s: s["concurrency"])
    table = []
    op = None
    broken = False
    for s in levels:
        ok, why = level_passes(s, slo_ttft_ms, slo_tpot_ms, max_error_rate, min_goodput_fraction)
        table.append({"concurrency": s["concurrency"], "pass": ok, "why_not": why})
        if ok and not broken:
            op = s
        if not ok:
            broken = True
    out: dict = {"levels": table}
    if op is None:
        out.update(decision="NO-GO", operating_concurrency=None, scale_target=None,
                   replicas_needed=None,
                   reasons=["the lowest tested concurrency already breaks an objective"])
        return out
    target = max(1, math.floor(op["concurrency"] * headroom))
    demand = peak_rps * op["mean_e2e_s"]
    needed = math.ceil(demand / target)
    reasons = []
    go = needed <= max_replicas
    if not go:
        reasons.append(f"peak needs {needed} replicas, only {max_replicas} GPUs available")
    stray = [t["concurrency"] for t in table
             if t["pass"] and t["concurrency"] > op["concurrency"]]
    if stray:
        reasons.append(f"levels {stray} passed above a failure and were ignored")
    out.update(decision="GO" if go else "NO-GO",
               operating_concurrency=op["concurrency"], scale_target=target,
               concurrent_at_peak=demand, replicas_needed=needed, reasons=reasons)
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sweep_json", help="JSON list written by c03_loadgen.py --out")
    ap.add_argument("--slo-ttft-ms", type=float, required=True)
    ap.add_argument("--slo-tpot-ms", type=float, required=True)
    ap.add_argument("--peak-rps", type=float, required=True)
    ap.add_argument("--max-replicas", type=int, required=True)
    ap.add_argument("--headroom", type=float, default=0.8)
    a = ap.parse_args()
    with open(a.sweep_json) as f:
        sweep = json.load(f)
    res = decide(sweep, a.slo_ttft_ms, a.slo_tpot_ms, a.peak_rps, a.max_replicas, a.headroom)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["decision"] == "GO" else 1)


if __name__ == "__main__":
    main()
