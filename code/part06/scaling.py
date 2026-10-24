"""Amdahl and Gustafson models, a measured strong-scaling run, and the Karp-Flatt metric."""
import math, os, time
from multiprocessing import Pool

def amdahl(p, n):            # strong scaling, p = parallel fraction
    return 1.0 / ((1 - p) + p / n)

def gustafson(p, n):         # weak scaling (scaled speedup)
    return (1 - p) + p * n

def karp_flatt(speedup, n):  # experimentally determined serial fraction
    return (1.0 / speedup - 1.0 / n) / (1.0 - 1.0 / n)

def work(args):
    lo, hi = args
    s = 0.0
    for i in range(lo, hi):
        s += math.sqrt(i) * math.sin(i)
    return s

def run(n_workers, total):
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
    cores = os.cpu_count() or 1
    total = 40_000_000
    t1 = run(1, total)
    print(f"\ncores={cores}  strong scaling, fixed problem={total}")
    print("workers  time_s  speedup  efficiency  karp_flatt")
    for n in sorted({1, 2, 4, cores}):
        if n > cores: continue
        t = t1 if n == 1 else run(n, total)
        s = t1 / t
        kf = "-" if n == 1 else f"{karp_flatt(s, n):.3f}"
        print(f"{n:7d}  {t:6.2f}  {s:7.2f}  {s/n:10.2f}  {kf}")
