#!/usr/bin/env python3
"""Amdahl and Gustafson models, Karp-Flatt metric, Hockney communication cost, and measured strong scaling for Chapter 6.3."""
import math
import os
import time
from multiprocessing import Pool


def amdahl(p: float, n: int) -> float:
    """Return strong-scaling speedup S(n) = 1 / ((1 - p) + p / n) for parallel fraction p."""
    return 1.0 / ((1.0 - p) + p / n)


def gustafson(p: float, n: int) -> float:
    """Return weak-scaling scaled speedup S_scaled(n) = (1 - p) + p * n."""
    return (1.0 - p) + p * n


def karp_flatt(speedup: float, n: int) -> float:
    """Return experimentally determined serial fraction e = (1/S - 1/n) / (1 - 1/n)."""
    return (1.0 / speedup - 1.0 / n) / (1.0 - 1.0 / n)


def hockney_message_time_us(message_bytes: int, alpha_us: float, beta_gbps: float) -> dict[str, float]:
    """Return Hockney latency-bandwidth model T(m) = alpha + m/beta in microseconds and crossover bytes."""
    bytes_per_us = beta_gbps * 1000.0  # 1 GB/s = 1000 bytes/us (decimal)
    transfer_us = message_bytes / bytes_per_us
    crossover_bytes = alpha_us * bytes_per_us
    return {
        "total_us": round(alpha_us + transfer_us, 3),
        "latency_share": round(alpha_us / (alpha_us + transfer_us), 3),
        "crossover_bytes": round(crossover_bytes, 1),
    }


def ring_allreduce_volume_per_rank(tensor_bytes: int, num_ranks: int) -> float:
    """Return bytes sent per rank in a ring AllReduce: 2 * (n - 1) / n * M."""
    return 2.0 * (num_ranks - 1) / num_ranks * tensor_bytes


def work(args: tuple[int, int]) -> float:
    lo, hi = args
    s = 0.0
    for i in range(lo, hi):
        s += math.sqrt(i) * math.sin(i)
    return s


def run(n_workers: int, total: int) -> float:
    chunks = [(k * total // n_workers, (k + 1) * total // n_workers) for k in range(n_workers)]
    t = time.perf_counter()
    if n_workers == 1:
        work(chunks[0])
    else:
        with Pool(n_workers) as pool:
            pool.map(work, chunks)
    return time.perf_counter() - t


if __name__ == "__main__":
    print("p     n=8   n=64  n=1024  limit")
    for p in (0.50, 0.90, 0.99, 0.999):
        print(f"{p:<5} {amdahl(p,8):5.1f} {amdahl(p,64):5.1f} {amdahl(p,1024):7.1f} {1/(1-p):6.0f}")
    # Reference Apple M3 8-core (4P+4E) 40,000,000-iteration (vs 36,000 processors) run:
    # 1w: 2.55s (1.00x, E=1.00), 2w: 1.38s (1.85x, E=0.92, e=0.083),
    # 4w: 0.90s (2.84x, E=0.71, e=0.135), 8w: 0.76s (3.37x, E=0.42, e=0.196)
    cores = os.cpu_count() or 1
    total = 40_000_000
    t1 = run(1, total)
    print(f"\ncores={cores}  strong scaling, fixed problem={total}")
    print("workers  time_s  speedup  efficiency  karp_flatt")
    for n in sorted({1, 2, 4, cores}):
        if n > cores:
            continue
        t = t1 if n == 1 else run(n, total)
        s = t1 / t
        kf = "-" if n == 1 else f"{karp_flatt(s, n):.3f}"
        print(f"{n:7d}  {t:6.2f}  {s:7.2f}  {s/n:10.2f}  {kf}")
