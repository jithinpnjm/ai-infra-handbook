"""Why the p99 of a fan-out request is worse than the p99 of one call.

One request calls `fanout` backends in parallel and waits for all of them,
so its latency is the maximum of the calls. Each call is drawn from a
lognormal distribution. Seeded, standard library only.
"""
import math
import random


def percentile(sorted_values, q):
    """Nearest-rank percentile, q between 0 and 1."""
    if not sorted_values:
        raise ValueError("no values")
    k = max(0, min(len(sorted_values) - 1, math.ceil(q * len(sorted_values)) - 1))
    return sorted_values[k]


def simulate(fanout, requests=20_000, mu=math.log(10.0), sigma=0.6, seed=1):
    """Return (p50, p99) of the request latency, in the unit of mu (ms)."""
    rng = random.Random(seed)
    lat = sorted(
        max(rng.lognormvariate(mu, sigma) for _ in range(fanout))
        for _ in range(requests)
    )
    return percentile(lat, 0.50), percentile(lat, 0.99)


def single_call_p99(mu=math.log(10.0), sigma=0.6, z99=2.3263478740408408):
    """Closed form p99 of a lognormal: exp(mu + z * sigma)."""
    return math.exp(mu + z99 * sigma)


if __name__ == "__main__":
    print(f"closed-form single-call p99: {single_call_p99():.1f} ms")
    print("fanout   p50 ms   p99 ms")
    for n in (1, 10, 100):
        p50, p99 = simulate(n)
        print(f"{n:>6}  {p50:7.1f}  {p99:7.1f}")
