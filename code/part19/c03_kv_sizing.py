#!/usr/bin/env python3
"""KV cache and concurrency arithmetic for chapter 19.3.

Standard library only. Every input is a parameter, so you can re-run it for another model.
Model numbers for Llama 3.1 8B come from the config.json of a public mirror and the
Hugging Face model API, fetched 2026-11-10 (see the chapter's sources). The memory
overhead is an assumption, not a measurement: read the real value from the vLLM start-up log.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

GIB = 1024**3


@dataclass(frozen=True)
class Model:
    name: str
    params: int          # parameter count
    layers: int
    kv_heads: int
    head_dim: int
    attn_heads: int      # query heads, used only for the MHA comparison
    weight_bytes: int = 2  # bf16
    kv_bytes: int = 2      # bf16 KV cache


LLAMA31_8B = Model(
    name="Llama-3.1-8B-Instruct",
    params=8_030_261_248,
    layers=32,
    kv_heads=8,
    head_dim=128,
    attn_heads=32,
)


def kv_bytes_per_token(m: Model, kv_heads: int | None = None) -> int:
    """Keys and values (the factor 2), for every layer."""
    heads = m.kv_heads if kv_heads is None else kv_heads
    return 2 * m.layers * heads * m.head_dim * m.kv_bytes


def weights_bytes(m: Model) -> int:
    return m.params * m.weight_bytes


def kv_budget_bytes(gpu_gib: float, utilization: float, m: Model, overhead_gib: float) -> int:
    """Memory left for the KV cache: utilization x GPU, minus weights, minus other use."""
    if not 0 < utilization <= 1:
        raise ValueError("utilization must be in (0, 1]")
    budget = utilization * gpu_gib * GIB - weights_bytes(m) - overhead_gib * GIB
    return int(budget)


def token_capacity(budget_bytes: int, m: Model) -> int:
    if budget_bytes <= 0:
        return 0
    return budget_bytes // kv_bytes_per_token(m)


def sequences_that_fit(capacity_tokens: int, seq_len: int) -> int:
    if seq_len <= 0:
        raise ValueError("seq_len must be positive")
    return capacity_tokens // seq_len


def plan(m: Model, gpu_gib: float, utilization: float, overhead_gib: float,
         avg_in: int, avg_out: int, max_model_len: int, max_num_seqs: int) -> dict:
    per_tok = kv_bytes_per_token(m)
    budget = kv_budget_bytes(gpu_gib, utilization, m, overhead_gib)
    cap = token_capacity(budget, m)
    avg_len = avg_in + avg_out
    need_typical = max_num_seqs * avg_len
    return {
        "model": m.name,
        "kv_bytes_per_token": per_tok,
        "kv_kib_per_token": per_tok / 1024,
        "weights_gib": weights_bytes(m) / GIB,
        "kv_budget_gib": budget / GIB,
        "capacity_tokens": cap,
        "seqs_at_avg_len": sequences_that_fit(cap, avg_len),
        "seqs_at_max_model_len": sequences_that_fit(cap, max_model_len),
        "typical_batch_tokens": need_typical,
        "typical_batch_gib": need_typical * per_tok / GIB,
        "typical_batch_fits": need_typical <= cap,
        "worst_case_tokens": max_num_seqs * max_model_len,
        "worst_case_fits": max_num_seqs * max_model_len <= cap,
        "mha_over_gqa": kv_bytes_per_token(m, m.attn_heads) / per_tok,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gpu-gib", type=float, default=40.0)
    ap.add_argument("--utilization", type=float, default=0.90)
    ap.add_argument("--overhead-gib", type=float, default=3.0,
                    help="assumed activation and runtime memory; read the real value from the vLLM log")
    ap.add_argument("--avg-in", type=int, default=1024)
    ap.add_argument("--avg-out", type=int, default=256)
    ap.add_argument("--max-model-len", type=int, default=16384)
    ap.add_argument("--max-num-seqs", type=int, default=64)
    a = ap.parse_args()
    print(json.dumps(plan(LLAMA31_8B, a.gpu_gib, a.utilization, a.overhead_gib,
                          a.avg_in, a.avg_out, a.max_model_len, a.max_num_seqs), indent=2))


if __name__ == "__main__":
    main()
