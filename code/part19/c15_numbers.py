#!/usr/bin/env python3
"""Worked arithmetic quoted in chapter 19.15. Standard library plus c04_checkpoint_interval.

Every function is a formula the cheat sheet states. The inputs are examples taken from the
cited chapters, not measurements. Run it to print the table used in the chapter.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c04_checkpoint_interval as ck  # noqa: E402


def gbps_to_gb_per_s(gbps: float) -> float:
    return gbps / 8.0


def train_flops(params: float, tokens: float) -> float:
    """The 6ND rule: about 6 x parameters x tokens FLOPs."""
    return 6.0 * params * tokens


def train_days(params, tokens, gpus, peak_tflops, mfu) -> float:
    return train_flops(params, tokens) / (gpus * peak_tflops * 1e12 * mfu) / 86400.0


def mfu(achieved_tflops: float, peak_tflops: float) -> float:
    return achieved_tflops / peak_tflops


def kv_bytes_per_token(layers, kv_heads, head_dim, bytes_per_elem=2) -> int:
    return 2 * layers * kv_heads * head_dim * bytes_per_elem


def decode_ceiling_tokens_per_s(bandwidth_gb_s: float, weight_gb: float) -> float:
    """Batch-one decode reads every weight once per token."""
    return bandwidth_gb_s / weight_gb


def e2e_latency(ttft_s, itl_s, tokens) -> float:
    return ttft_s + itl_s * (tokens - 1)


def burn_rate(error_ratio: float, slo: float) -> float:
    return error_ratio / (1.0 - slo)


def hours_to_empty(period_hours: float, burn: float) -> float:
    return period_hours / burn


def budget_minutes(slo: float, period_days: float) -> float:
    return period_days * 24 * 60 * (1.0 - slo)


def budget_used(burn: float, window_hours: float, period_hours: float = 720.0) -> float:
    return burn * window_hours / period_hours


def busbw_factor_allreduce(n: int) -> float:
    return 2.0 * (n - 1) / n


def busbw_from_algbw(algbw: float, n: int) -> float:
    return algbw * busbw_factor_allreduce(n)


def bisect_rounds(nodes: int) -> int:
    import math
    return math.ceil(math.log2(nodes))


def checkpoint_row(gpus: int, cost_s: float, restart_s: float = 600.0):
    """The 19.4 reference job: 8.03 B params, 14 bytes each, GPU MTBF 50,700 h scaled."""
    mtbf = 54 * 24 * 16384 / 419 / gpus * 3600.0
    t = ck.daly(cost_s, mtbf)
    return {"gpus": gpus, "mtbf_h": mtbf / 3600, "daly_s": t,
            "waste": ck.waste(t, cost_s, mtbf, 0.0, restart_s)}


def table() -> list[tuple[str, str]]:
    rows = [
        ("400 Gbps link in GB/s", f"{gbps_to_gb_per_s(400):.0f}"),
        ("70B x 100B tokens FLOPs", f"{train_flops(70e9, 100e9):.2e}"),
        ("days on 128 H100 at 40% MFU", f"{train_days(70e9, 100e9, 128, 989, 0.40):.1f}"),
        ("MFU 430 of 989 TFLOPS", f"{mfu(430, 989) * 100:.2f}%"),
        ("Llama 3.1 8B KV bytes per token", str(kv_bytes_per_token(32, 8, 128))),
        ("Qwen3-8B KV bytes per token", str(kv_bytes_per_token(36, 8, 128))),
        ("decode ceiling 3350 GB/s, 16.4 GB", f"{decode_ceiling_tokens_per_s(3350, 16.4):.0f}"),
        ("e2e 0.4 + 0.04 x 499", f"{e2e_latency(0.4, 0.04, 500):.2f}"),
        ("burn at 1% errors, 99.9% SLO", f"{burn_rate(0.01, 0.999):.0f}"),
        ("hours to empty at burn 10", f"{hours_to_empty(720, 10):.0f}"),
        ("minutes of budget, 99.9%, 30 d", f"{budget_minutes(0.999, 30):.1f}"),
        ("budget used, burn 14.4 for 1 h", f"{budget_used(14.4, 1) * 100:.0f}%"),
        ("AllReduce busbw, 24 GB/s at 16 ranks", f"{busbw_from_algbw(24.0, 16):.0f}"),
        ("bisect rounds, 8 and 128 nodes", f"{bisect_rounds(8)} and {bisect_rounds(128)}"),
    ]
    for g, c in ((16384, 22.5), (16384, 2.0)):
        r = checkpoint_row(g, c)
        rows.append((f"{g} GPUs, write {c} s: Daly s, waste",
                     f"{r['daly_s']:.0f} s, {r['waste'] * 100:.2f}%"))
    return rows


if __name__ == "__main__":
    for k, v in table():
        print(f"{k:42s} {v}")
