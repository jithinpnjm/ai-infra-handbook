"""Latency numbers and the arithmetic that makes them useful.

The table is the one on the last slides of Jeff Dean's LADIS 2009 keynote,
"Numbers Everyone Should Know". Hardware has changed since 2009, so use the
table for orders of magnitude and ratios, never for a prediction.
"""
import math

# name -> nanoseconds, copied from the 2009 slide
DEAN_2009_NS = {
    "L1 cache reference": 0.5,
    "Branch mispredict": 5,
    "L2 cache reference": 7,
    "Mutex lock/unlock": 25,
    "Main memory reference": 100,
    "Compress 1K bytes with Zippy": 3_000,
    "Send 2K bytes over 1 Gbps network": 20_000,
    "Read 1 MB sequentially from memory": 250_000,
    "Round trip within same datacenter": 500_000,
    "Disk seek": 10_000_000,
    "Read 1 MB sequentially from disk": 20_000_000,
    "Send packet CA->Netherlands->CA": 150_000_000,
}


def ratio(slow: str, fast: str) -> float:
    """How many times slower one operation is than another."""
    return DEAN_2009_NS[slow] / DEAN_2009_NS[fast]


def reads_per_round_trip(trip: str = "Round trip within same datacenter",
                         read: str = "Main memory reference") -> float:
    return ratio(trip, read)


def failures_in(requests: int, availability: float) -> float:
    """Requests that fail at a given availability, for example 0.999."""
    if not 0 <= availability <= 1:
        raise ValueError("availability must be between 0 and 1")
    return requests * (1 - availability)


def downtime_seconds(period_seconds: float, availability: float) -> float:
    return period_seconds * (1 - availability)


def prob_all_fast(p_slow: float, fanout: int) -> float:
    """Chance that none of `fanout` independent calls hits the slow tail."""
    return (1 - p_slow) ** fanout


def prob_any_slow(p_slow: float, fanout: int) -> float:
    return 1 - prob_all_fast(p_slow, fanout)


def per_call_percentile_needed(target: float, fanout: int) -> float:
    """Per-call quantile q so that q**fanout equals the target quantile."""
    return target ** (1 / fanout)


def md1_response(service_time: float, utilisation: float) -> float:
    """Mean response time of an M/D/1 queue: s(2 - u) / (2(1 - u)).

    The formula is in Systems Performance, chapter 2, "M/D/1 and 60% Utilization".
    """
    if not 0 <= utilisation < 1:
        raise ValueError("utilisation must be at least 0 and below 1")
    return service_time * (2 - utilisation) / (2 * (1 - utilisation))


def loop_seconds(items: int, ns_per_item: float) -> float:
    """Back-of-envelope time for a loop: items times cost per item."""
    return items * ns_per_item / 1e9


def items_per_second_budget(ns_per_item: float) -> float:
    return 1e9 / ns_per_item


if __name__ == "__main__":
    print(f"memory reads per datacenter round trip: {reads_per_round_trip():,.0f}")
    print(f"1M requests at 99.9%: {failures_in(1_000_000, 0.999):,.0f} fail")
    day = 24 * 3600
    print(f"99.9% over a day: {downtime_seconds(day, 0.999):,.1f} s of failure")
    for n in (1, 10, 100, 1000):
        print(f"fan-out {n:>4}: P(any call in the slow 1%) = {prob_any_slow(0.01, n):.3f}")
    for u in (0.5, 0.6, 0.8, 0.9, 0.95):
        print(f"M/D/1 at {u:.0%} busy: {md1_response(1.0, u):.2f} x service time")
    print(f"per-call quantile for a 99th overall at fan-out 100: "
          f"{per_call_percentile_needed(0.99, 100):.5f}")
