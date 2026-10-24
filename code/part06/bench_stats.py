#!/usr/bin/env python3
"""Benchmarking hygiene demo: an HPL-style dense solve and a STREAM-style triad, with repetitions and statistics.

HPL-style: solve A x = b by LU (numpy.linalg.solve -> LAPACK), flops = 2/3 n^3 + 2 n^2 (the HPL operation count),
verify with a scaled residual (HPL accepts the run only if the residual check passes).
STREAM-style triad: a = b + s*c, bytes = 3 * 8 * n (two reads, one write, ignoring write-allocate traffic).
Prints mean, std, coefficient of variation, min/median/max and a 95% confidence interval (Student t) over repeats.
Usage: bench_stats.py [--n 3000] [--reps 10]
"""
import argparse
import math
import statistics as st
import time

import numpy as np

T95 = {4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 14: 2.145, 19: 2.093, 29: 2.045}


def summarize(name, unit, xs):
    n = len(xs)
    m, s = st.mean(xs), st.stdev(xs)
    t = T95.get(n - 1, 1.96)
    print(f"{name:14s} n={n:2d} mean={m:9.2f} {unit}  std={s:7.2f}  CV={100 * s / m:5.1f}%  "
          f"min/med/max={min(xs):.2f}/{st.median(xs):.2f}/{max(xs):.2f}  95%CI=[{m - t * s / math.sqrt(n):.2f}, {m + t * s / math.sqrt(n):.2f}]")


def hpl_like(n, reps):
    rng = np.random.default_rng(1)
    A = rng.standard_normal((n, n))
    b = rng.standard_normal(n)
    np.linalg.solve(A, b)                           # warm-up (page faults, thread pool, caches)
    gf = []
    for _ in range(reps):
        t = time.perf_counter()
        x = np.linalg.solve(A, b)
        dt = time.perf_counter() - t
        gf.append((2 / 3 * n ** 3 + 2 * n ** 2) / dt / 1e9)
    resid = np.linalg.norm(A @ x - b, np.inf) / (np.finfo(float).eps * (np.linalg.norm(A, np.inf) * np.linalg.norm(x, np.inf) + np.linalg.norm(b, np.inf)) * n)
    return gf, resid


def triad(n, reps):
    a = np.zeros(n)
    b = np.random.rand(n)
    c = np.random.rand(n)
    s = 3.0
    np.add(b, s * c, out=a)                         # warm-up
    bw = []
    for _ in range(reps):
        t = time.perf_counter()
        np.multiply(c, s, out=a)                    # two passes: numpy cannot fuse; counts as 5 streams here
        np.add(a, b, out=a)
        dt = time.perf_counter() - t
        bw.append(5 * 8 * n / dt / 1e9)
    return bw


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--reps", type=int, default=10)
    a = ap.parse_args()
    gf, resid = hpl_like(a.n, a.reps)
    summarize("HPL-like LU", "GFLOP/s", gf)
    print(f"scaled residual = {resid:.3f}  ({'PASS' if resid < 16 else 'FAIL'}, HPL threshold is 16)")
    summarize("triad (numpy)", "GB/s", triad(40_000_000, a.reps))
