"""Canary and rollback as code for a model on a shared GPU pool (chapter 19.12).

The pass, hold or rollback decision is decide() from chapter 20.14 and is imported, not copied.
This file adds what a shared pool needs: a plan that fits the spare GPUs, a check that the canary
is not hurting neighbouring models, and a rollback order. All thresholds are teaching defaults.
Standard library only.
"""
import math
import os
import sys
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "..", "part20")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import c12_size_inference_pool as pool  # noqa: E402
from c14_rollout_sim import Gates, Metrics, decide  # noqa: E402,F401

STEPS = (5, 25, 50, 100)  # percent of traffic. Distributed AI Systems chapter 9 starts at 10 percent. A smaller first step is my choice.


@dataclass(frozen=True)
class Step:
    weight_pct: int
    canary_replicas: int
    extra_gpus: int
    fits_spare: bool


def canary_replicas_for(weight_pct, qps, rate_qps, util=pool.SIZING_UTIL):
    """Replicas the canary needs to carry its share of traffic at the planned utilisation."""
    return max(1, math.ceil(qps * weight_pct / 100 / (rate_qps * util)))


def plan(w, qps, spare_gpus, steps=STEPS):
    """Traffic ladder for a new version of workload w. Each step says how many GPUs the canary needs
    beyond the stable fleet, and whether the pool's spare GPUs cover it. Steps that do not fit must
    wait for a batch pod to be preempted or for a node to be added. Never skip the check."""
    cap = pool.replica_capacity(w)
    out = []
    for pct in steps:
        n = canary_replicas_for(pct, qps, cap["rate_qps"])
        extra = n * w.tp
        out.append(Step(pct, n, extra, extra <= spare_gpus))
    return out


def neighbour_impact(before_ttft_p99, during_ttft_p99, max_ratio=1.2):
    """Models that share nodes with the canary must not get slower. Returns the names that did."""
    hurt = []
    for name, b in before_ttft_p99.items():
        d = during_ttft_p99.get(name, b)
        if b > 0 and d / b > max_ratio:
            hurt.append(name)
    return hurt


def evaluate(base, canary, before_ttft, during_ttft, gates=None):
    """One decision for one step. A neighbour regression forces a rollback even if the canary looks fine."""
    d = decide(base, canary, gates or Gates())
    hurt = neighbour_impact(before_ttft, during_ttft)
    if hurt:
        return "rollback", d.reasons + [f"neighbour model slower during canary: {', '.join(hurt)}"]
    return d.action, d.reasons


def rollback_order(weight_pct):
    """Rollback is three actions in this order. Traffic first, because it stops the harm at once."""
    return [
        "set canary weight to 0 at the gateway",
        "wait for canary in-flight requests to drain, then scale canary replicas to 0",
        "return the freed GPUs to the pool and re-enable batch pods that were paused",
    ] if weight_pct > 0 else ["nothing to roll back"]


def run_ladder(w, qps, spare_gpus, observe):
    """Walk the ladder. observe(step) returns (base, canary, before_ttft, during_ttft).
    Stops at the first hold or rollback and reports where."""
    for s in plan(w, qps, spare_gpus):
        if not s.fits_spare:
            return {"action": "hold", "at": s.weight_pct, "reasons": ["canary does not fit the spare GPUs"]}
        action, reasons = evaluate(*observe(s))
        if action != "promote":
            return {"action": action, "at": s.weight_pct, "reasons": reasons}
    return {"action": "promote", "at": 100, "reasons": ["all steps passed"]}


if __name__ == "__main__":
    w = pool.WORKLOADS[0]
    for s in plan(w, w.peak_qps, spare_gpus=8):
        print(s)
