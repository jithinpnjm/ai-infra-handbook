"""Size a shared GPU pool for several internal models (chapter 19.12).

Per-replica capacity comes from code/part20/capacity_estimator.py (chapter 20.12). Nothing is
recomputed here. This file adds what 20.12 does not have: several workloads on one pool,
hourly demand, 8-GPU node packing, and an LRU cache for rarely used models.
Every workload number is an assumption for teaching, not a measurement. Standard library only.
"""
import math
import os
import sys
from collections import OrderedDict
from dataclasses import dataclass, field

_P20 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "part20")
if _P20 not in sys.path:
    sys.path.insert(0, _P20)
import capacity_estimator as est  # noqa: E402

NODE_GPUS = 8
SIZING_UTIL = 0.9  # same default as 20.12: plan to run replicas at 90 percent of the ceiling


def _flat(v):
    return [v] * 24


# Fraction of peak QPS in each hour of the day. Assumed shapes, not measured traffic.
OFFICE = [0.05] * 8 + [0.6, 0.9, 1.0, 1.0, 0.8, 0.7, 1.0, 1.0, 0.9, 0.7] + [0.3, 0.2, 0.1, 0.05, 0.05, 0.05]
NIGHT_BATCH = [1.0] * 5 + [0.15] * 19
MIDDAY = [0.0] * 9 + [0.5, 1.0, 1.0, 0.8, 0.6, 1.0, 1.0, 0.8, 0.5] + [0.0] * 6


@dataclass(frozen=True)
class Workload:
    name: str
    model: str          # key into capacity_estimator.MODELS
    tier: str           # hot, warm, batch or cold
    peak_qps: float
    in_tokens: int
    out_tokens: int
    batch: int
    tp: int = 1
    min_replicas: int = 0
    profile: tuple = field(default_factory=lambda: tuple(_flat(1.0)))


WORKLOADS = [
    Workload("assistant", "qwen3-8b", "hot", 30, 1500, 300, 64, 1, 2, tuple(OFFICE)),
    Workload("docsum", "qwen3-8b", "batch", 8, 6000, 400, 32, 1, 0, tuple(NIGHT_BATCH)),
    Workload("analyst", "qwen2.5-72b", "warm", 4, 3000, 600, 16, 4, 1, tuple(MIDDAY)),
]
# Three rarely used fine-tunes of the 8B model. Each loads on demand into one of a few cold slots.
COLD_MODELS = {"contracts-8b": 16.4, "hr-8b": 16.4, "finance-8b": 16.4}  # weights GB, BF16


def replica_capacity(w, gpu="h100", mfu=0.40, mem_util=0.90, overhead_gb=5, bytes_per_param=2):
    """One replica's ceiling, from the 20.12 functions. Raises if the weights plus one request do not fit."""
    params, layers, kvh, hd = est.MODELS[w.model]
    mem, bw, tflops, price = est.GPUS[gpu]
    wgb = est.weights_gb(params, bytes_per_param)
    bpt = est.kv_bytes_per_token(layers, kvh, hd)
    req_gb = (w.in_tokens + w.out_tokens) * bpt / est.GB
    fit = est.max_concurrent(mem, w.tp, mem_util, wgb, overhead_gb, req_gb)
    if fit < 1:
        raise ValueError(f"{w.name}: {wgb:.1f} GB of weights do not fit on {w.tp} x {gpu}")
    ctx = w.in_tokens + w.out_tokens
    d_tps = est.decode_tps(w.batch, ctx, wgb, bpt, bw * w.tp)
    p_tps = est.prefill_tps(tflops * w.tp, mfu, params)
    rate, latency, tpot = est.per_gpu_capacity(w.in_tokens, w.out_tokens, w.batch, p_tps, d_tps)
    return {"rate_qps": rate, "latency_s": latency, "tpot_s": tpot, "weights_gb": wgb,
            "fits_requests": fit, "price": price, "gpus": w.tp}


def replicas_at(w, qps, cap=None, util=SIZING_UTIL):
    """Replicas needed at a given QPS. No spare here: spare is a pool decision, not a model decision."""
    cap = cap or replica_capacity(w)
    if qps <= 0:
        return w.min_replicas
    return max(w.min_replicas, est.replicas_needed(qps, cap["rate_qps"], util, spare=0))


def hourly_gpus(workloads=None, gpu="h100"):
    """GPUs needed in each hour if every model follows its own load (autoscaled shared pool)."""
    out = []
    caps = {w.name: replica_capacity(w, gpu) for w in (workloads or WORKLOADS)}
    for h in range(24):
        total = 0
        for w in workloads or WORKLOADS:
            total += replicas_at(w, w.peak_qps * w.profile[h], caps[w.name]) * w.tp
        out.append(total)
    return out


def dedicated_gpus(workloads=None, gpu="h100"):
    """GPUs if each model owns a pool sized for its own peak."""
    total = 0
    for w in workloads or WORKLOADS:
        total += replicas_at(w, w.peak_qps, replica_capacity(w, gpu)) * w.tp
    return total


def pack_nodes(replica_gpus, node_gpus=NODE_GPUS):
    """First-fit decreasing. A replica never spans nodes, so a 4-GPU replica sits on one node."""
    if any(g > node_gpus for g in replica_gpus):
        raise ValueError("a replica needs more GPUs than one node has")
    nodes = []
    for g in sorted(replica_gpus, reverse=True):
        for n in nodes:
            if sum(n) + g <= node_gpus:
                n.append(g)
                break
        else:
            nodes.append([g])
    return nodes


class ModelCache:
    """LRU slots for cold models, the policy in Hands-On LLM Serving and Optimization, chapter 3.
    A hit costs nothing. A miss costs a load, and evicts the least recently used model when full."""

    def __init__(self, slots, load_s):
        if slots < 1:
            raise ValueError("need at least one slot")
        self.slots, self.load_s = slots, dict(load_s)
        self.loaded = OrderedDict()
        self.hits = self.misses = 0
        self.wait_s = 0.0
        self.evictions = []

    def request(self, model):
        if model in self.loaded:
            self.loaded.move_to_end(model)
            self.hits += 1
            return 0.0
        if model not in self.load_s:
            raise KeyError(f"unknown model {model}")
        self.misses += 1
        if len(self.loaded) >= self.slots:
            old, _ = self.loaded.popitem(last=False)
            self.evictions.append(old)
        self.loaded[model] = True
        self.wait_s += self.load_s[model]
        return self.load_s[model]

    def hit_rate(self):
        n = self.hits + self.misses
        return self.hits / n if n else 0.0


def cold_load_s(weights_gb, read_gb_s=2.0, startup_s=45.0):
    """Assumed: node-local NVMe read speed plus engine start and warm-up. Measure your own."""
    return weights_gb / read_gb_s + startup_s


def cost_per_m_output(w, utilisation, gpu="h100"):
    """Dollars per million output tokens at a stated utilisation. Uses the 20.12 formula."""
    cap = replica_capacity(w, gpu)
    return est.cost_per_m_tokens(cap["price"], w.tp, cap["rate_qps"] * w.out_tokens, utilisation)


# A fixed request trace for the three cold models: a burst for one team, then the others take turns.
COLD_TRACE = ["contracts-8b"] * 6 + ["hr-8b", "contracts-8b", "finance-8b", "contracts-8b", "hr-8b",
                                      "hr-8b", "finance-8b", "contracts-8b", "hr-8b", "finance-8b"]


def cold_demo(slots, trace=COLD_TRACE):
    load = {m: cold_load_s(g) for m, g in COLD_MODELS.items()}
    c = ModelCache(slots, load)
    for m in trace:
        c.request(m)
    return {"slots": slots, "hit_rate": c.hit_rate(), "wait_s": c.wait_s, "evictions": len(c.evictions)}


def pool_plan(workloads=None, cold_slots=1, spare_gpus=NODE_GPUS, gpu="h100", days=30):
    ws = workloads or WORKLOADS
    caps = {w.name: replica_capacity(w, gpu) for w in ws}
    hourly = hourly_gpus(ws, gpu)
    peak_shared = max(hourly) + cold_slots
    dedicated = dedicated_gpus(ws, gpu) + cold_slots
    price = est.GPUS[gpu][3]
    static_gpus = peak_shared + spare_gpus
    needed_gpu_h = sum(
        w.peak_qps * w.profile[h] / caps[w.name]["rate_qps"] * w.tp for w in ws for h in range(24))
    paid_static = static_gpus * 24
    paid_auto = (sum(hourly) + cold_slots * 24 + spare_gpus * 24)
    return {
        "per_model": {w.name: {**caps[w.name], "peak_replicas": replicas_at(w, w.peak_qps, caps[w.name])}
                      for w in ws},
        "hourly_gpus": hourly,
        "peak_shared_gpus": peak_shared,
        "dedicated_gpus": dedicated,
        "spare_gpus": spare_gpus,
        "static_gpus": static_gpus,
        "nodes_at_peak": len(pack_nodes(_peak_layout(ws, caps, cold_slots))),
        "busy_gpu_hours_per_day": needed_gpu_h,
        "util_static": needed_gpu_h / paid_static,
        "util_autoscaled": needed_gpu_h / paid_auto,
        "usd_month_static": static_gpus * 24 * days * price,
        "usd_month_autoscaled": paid_auto * days * price,
        "usd_month_dedicated": (dedicated + spare_gpus) * 24 * days * price,
    }


def _peak_layout(ws, caps, cold_slots):
    layout = []
    for w in ws:
        layout += [w.tp] * replicas_at(w, w.peak_qps, caps[w.name])
    return layout + [1] * cold_slots


def main():
    p = pool_plan()
    for name, m in p["per_model"].items():
        print(f"{name}: {m['rate_qps']:.2f} req/s per replica ({m['gpus']} GPU), "
              f"{m['peak_replicas']} replicas at peak")
    print("hourly GPUs:", p["hourly_gpus"])
    for k in ("peak_shared_gpus", "dedicated_gpus", "spare_gpus", "static_gpus", "nodes_at_peak"):
        print(f"{k}: {p[k]}")
    for sl in (1, 2, 3):
        print("cold cache", cold_demo(sl))
    a = WORKLOADS[0]
    print(f"assistant $/M output tokens: full {cost_per_m_output(a, 1.0):.2f}, "
          f"autoscaled {cost_per_m_output(a, p['util_autoscaled']):.2f}, static {cost_per_m_output(a, p['util_static']):.2f}")
    print(f"utilisation static {p['util_static']:.0%}, autoscaled {p['util_autoscaled']:.0%}")
    for k in ("usd_month_static", "usd_month_autoscaled", "usd_month_dedicated"):
        print(f"{k}: {p[k]:,.0f}")


if __name__ == "__main__":
    main()
