"""Cache-aware router simulation: effect of the load-aware fallback.

Replicas keep an LRU set of cached prompt prefixes. A request whose prefix is
cached skips most of its prefill. Each replica is a single FIFO server, so
latency = queueing delay + service time. Standard library only.
"""
import random
from collections import OrderedDict


class Replica:
    def __init__(self, cache_slots):
        self.cache = OrderedDict()
        self.slots = cache_slots
        self.free_at = 0.0      # time when the queue drains
        self.served = 0

    def backlog(self, now):
        return max(0.0, self.free_at - now)

    def has(self, prefix):
        return prefix in self.cache

    def touch(self, prefix):
        self.cache[prefix] = True
        self.cache.move_to_end(prefix)
        while len(self.cache) > self.slots:
            self.cache.popitem(last=False)


def pick(policy, replicas, prefix, now, rr, bound_s):
    least = min(range(len(replicas)), key=lambda i: replicas[i].backlog(now))
    if policy == "round_robin":
        return rr % len(replicas)
    if policy == "least_loaded":
        return least
    holders = [i for i, r in enumerate(replicas) if r.has(prefix)]
    if not holders:
        return least
    best = min(holders, key=lambda i: replicas[i].backlog(now))
    if policy == "cache_only":
        return best
    # cache_bounded: use the cache holder only if it is not much busier than the idlest replica
    if replicas[best].backlog(now) <= replicas[least].backlog(now) + bound_s:
        return best
    return least


def percentile(values, q):
    s = sorted(values)
    return s[min(len(s) - 1, int(q * len(s)))]


def simulate(policy, n_req=6000, n_rep=8, n_prefix=40, hot_share=0.4,
             arrival_gap=0.05, miss_s=0.50, hit_s=0.10, bound_s=0.5,
             cache_slots=6, seed=7):
    rng = random.Random(seed)
    reps = [Replica(cache_slots) for _ in range(n_rep)]
    now, lat, hits = 0.0, [], 0
    for k in range(n_req):
        now += rng.expovariate(1.0 / arrival_gap)
        prefix = 0 if rng.random() < hot_share else rng.randrange(1, n_prefix)
        i = pick(policy, reps, prefix, now, k, bound_s)
        r = reps[i]
        hit = r.has(prefix)
        hits += hit
        start = max(now, r.free_at)
        r.free_at = start + (hit_s if hit else miss_s)
        r.touch(prefix)
        r.served += 1
        lat.append(r.free_at - now)
    loads = [r.served for r in reps]
    return {"policy": policy, "hit_rate": hits / n_req,
            "p50_s": percentile(lat, 0.5), "p99_s": percentile(lat, 0.99),
            "max_over_mean_load": max(loads) / (sum(loads) / len(loads))}


if __name__ == "__main__":
    print(f"{'policy':14} {'hit':>6} {'p50 s':>8} {'p99 s':>8} {'max/mean':>9}")
    for name in ("round_robin", "least_loaded", "cache_only", "cache_bounded"):
        r = simulate(name)
        print(f"{r['policy']:14} {r['hit_rate']:6.2f} {r['p50_s']:8.2f} "
              f"{r['p99_s']:8.2f} {r['max_over_mean_load']:9.2f}")
