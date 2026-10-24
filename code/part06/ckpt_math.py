#!/usr/bin/env python3
"""Checkpoint size and storage-bandwidth arithmetic for LLM training.

Bytes per parameter in a full training checkpoint (mixed precision with Adam), a common accounting:
  bf16 weights 2 + fp32 master weights 4 + Adam first/second moments 4+4 = 14 (some stacks add fp32 grads: 18)
Inference-only checkpoint: 2 bytes/param in bf16.  These are the usual numbers, not universal: check your stack.
"""
import sys


def ckpt_bytes(params, bytes_per_param=14):
    return params * bytes_per_param


def need_gbs(size_bytes, seconds):
    return size_bytes / seconds / 1e9


def overhead(size_bytes, bandwidth_gbs, interval_s):
    t = size_bytes / (bandwidth_gbs * 1e9)
    return t, t / interval_s


if __name__ == "__main__":
    print(f"{'params':>8} {'train ckpt':>11} {'to write in 60 s':>17} {'at 10 GB/s: time':>17} {'every 1h: lost':>15}")
    for p in (7e9, 70e9, 405e9, 1e12):
        sz = ckpt_bytes(p)
        t, frac = overhead(sz, 10, 3600)
        print(f"{p/1e9:>6.0f}B {sz/1e12:>9.2f}TB {need_gbs(sz, 60):>14.0f}GB/s {t:>15.0f} s {frac*100:>13.1f}%")
    # dataset read: tokens/s * bytes/token across the cluster
    gpus, tok_s_per_gpu, bytes_per_token = 4096, 3000, 4   # illustrative
    print(f"\ndata loading (illustrative): {gpus} GPUs x {tok_s_per_gpu} tok/s x {bytes_per_token} B/token = "
          f"{gpus*tok_s_per_gpu*bytes_per_token/1e6:.0f} MB/s of pre-tokenised data (small!); images/video are far larger")
