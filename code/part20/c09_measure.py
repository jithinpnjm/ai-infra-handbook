"""Measure the complexity claims in chapter 20.9. Run: python3 c09_measure.py"""
import heapq
import random
import time
from c09_window import sliding_max, sliding_max_naive
from c09_heaps import top_k_slowest
from c09_lru import LRUList, LRUOrdered
from c09_hashring import Ring, balance
from c09_ratelimit import SlidingLog
from c09_percentiles import LogHistogram, percentile
from c09_concurrency import UnsafeCounter, hammer


def timed(f, *a):
    t = time.perf_counter()
    f(*a)
    return time.perf_counter() - t


def main():
    rng = random.Random(1)
    print("sliding max, k=1000: deque vs naive (seconds)")
    for n in (10_000, 20_000, 40_000):
        v = [rng.random() for _ in range(n)]
        print(f"  n={n:6d} deque={timed(sliding_max, v, 1000):.4f} naive={timed(sliding_max_naive, v, 1000):.4f}")

    print("top-k slowest, k=10: heap vs full sort (seconds)")
    for n in (100_000, 400_000):
        data = [("e", rng.random()) for _ in range(n)]
        full = lambda d: sorted(d, key=lambda x: x[1])[-10:]
        print(f"  n={n:7d} heap={timed(top_k_slowest, data, 10):.4f} sort={timed(full, data):.4f}")

    print("LRU 200k ops, capacity 1000 (seconds)")
    for cls in (LRUOrdered, LRUList):
        c = cls(1000)
        ops = [rng.randrange(2000) for _ in range(200_000)]

        def run():
            for k in ops:
                if c.get(k) is None:
                    c.put(k, k)
        print(f"  {cls.__name__:10s} {timed(run):.3f}")

    print("ring balance (max load / mean) 10 nodes, 100k keys")
    keys = [f"k{i}" for i in range(100_000)]
    nodes = [f"n{i}" for i in range(10)]
    for vn in (1, 10, 100, 1000):
        r, _ = balance(Ring(nodes, vn), keys)
        print(f"  vnodes={vn:5d} ratio={r:.3f}")

    print("ring lookup cost vs ring size (200k lookups, seconds)")
    for n_nodes in (10, 1000):
        ring = Ring([f"n{i}" for i in range(n_nodes)], 20)
        ks = keys[:200_000 // 2]
        print(f"  nodes={n_nodes:5d} points={len(ring.points):6d} {timed(lambda: [ring.lookup(k) for k in ks]):.3f}")

    print("sliding log memory: entries kept after 50k requests offered at 100k per second")
    for limit in (100, 10_000):
        s = SlidingLog(limit, 1.0)
        for i in range(50_000):
            s.allow(i * 0.00001)
        print(f"  limit={limit:6d} entries={len(s.log)}")

    print("percentile accuracy: lognormal, 200k samples, p99")
    data = [rng.lognormvariate(4, 1) for _ in range(200_000)]
    exact = percentile(sorted(data), 99)
    for ratio in (1.1, 1.02):
        hgm = LogHistogram(ratio=ratio)
        for x in data:
            hgm.add(x)
        print(f"  ratio={ratio} buckets={len(hgm.counts)} exact={exact:.2f} approx={hgm.quantile(0.99):.2f}")

    print("unsafe counter, 8 threads x 200k increments, expected 1600000")
    print("  got", hammer(UnsafeCounter(), 8, 200_000))


if __name__ == "__main__":
    main()
