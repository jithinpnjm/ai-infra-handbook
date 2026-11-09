"""Arithmetic behind retries: attempts, layers, budgets, jitter and hedging.

Every function is plain math or a seeded simulation, so the numbers in the
chapter can be reproduced. Standard library only.
"""
import random


def expected_attempts(p, k):
    """Expected attempts per request when each attempt fails with probability p
    and the client makes at most k attempts: 1 + p + p^2 + ... + p^(k-1)."""
    if not 0 <= p <= 1 or k < 1:
        raise ValueError("need 0 <= p <= 1 and k >= 1")
    return sum(p ** i for i in range(k))


def layered_attempts(attempts_per_layer, layers):
    """Worst-case attempts at the bottom layer when every layer retries."""
    return attempts_per_layer ** layers


def budget_amplification_cap(budget_ratio):
    """With a budget of b retries per original request, load is at most 1 + b."""
    return 1.0 + budget_ratio


def backoff_ceiling(retry_no, base, cap):
    """Upper bound of the sleep before retry number retry_no (1 is the first)."""
    return min(cap, base * 2 ** (retry_no - 1))


def full_jitter_mean(retry_no, base, cap):
    """Full jitter sleeps a uniform amount in [0, ceiling], so the mean is half."""
    return backoff_ceiling(retry_no, base, cap) / 2.0


def herd_peak(n_clients, jitter, base=0.1, cap=5.0, rounds=3, bin_s=0.01, seed=1):
    """N clients all fail at t=0 and keep failing. Return the largest number of
    retries that land in one bin of bin_s seconds, over all rounds.
    jitter is 'none' or 'full'."""
    rng = random.Random(seed)
    counts = {}
    for _ in range(n_clients):
        t = 0.0
        for r in range(1, rounds + 1):
            ceiling = backoff_ceiling(r, base, cap)
            t += ceiling if jitter == "none" else rng.uniform(0.0, ceiling)
            key = int(t / bin_s)
            counts[key] = counts.get(key, 0) + 1
    return max(counts.values())


def hedge_effect(delay_quantile, n=200_000, mu=0.0, sigma=0.6, seed=3):
    """Latencies are lognormal and independent between attempts. A second copy
    is sent when the first has not answered by the delay, which is the given
    quantile of the latency distribution. Returns p99 before and after, and
    the share of requests that were duplicated.
    Independence is an assumption. Under overload the copies are not
    independent, and the duplicates make the slowness worse."""
    rng = random.Random(seed)
    base, hedged, sent = [], [], 0
    lat = sorted(rng.lognormvariate(mu, sigma) for _ in range(20_000))
    delay = lat[int(delay_quantile * len(lat)) - 1]
    for _ in range(n):
        first = rng.lognormvariate(mu, sigma)
        base.append(first)
        if first > delay:
            sent += 1
            hedged.append(min(first, delay + rng.lognormvariate(mu, sigma)))
        else:
            hedged.append(first)
    base.sort()
    hedged.sort()
    q99 = int(0.99 * n) - 1
    return {"delay": round(delay, 3), "p99_before": round(base[q99], 3),
            "p99_after": round(hedged[q99], 3), "duplicated_share": round(sent / n, 4)}


if __name__ == "__main__":
    for p in (0.1, 0.5, 0.8):
        print(f"p={p}: expected attempts with k=4 is {expected_attempts(p, 4):.3f}")
    print("layers: 4 attempts per layer, 3 layers ->", layered_attempts(4, 3))
    print("layers: 3 attempts per layer, 5 layers ->", layered_attempts(3, 5))
    print("layers: 4 attempts per layer, 5 layers ->", layered_attempts(4, 5))
    for r in (1, 2, 3, 4):
        print(f"retry {r}: ceiling {backoff_ceiling(r, 0.1, 5):.1f} s, "
              f"full-jitter mean {full_jitter_mean(r, 0.1, 5):.2f} s")
    for j in ("none", "full"):
        print(f"1000 clients failing together, {j} jitter: peak "
              f"{herd_peak(1000, j)} retries in one 10 ms bin")
    for q in (0.9, 0.95):
        print(f"hedge at p{int(q * 100)}:", hedge_effect(q))
