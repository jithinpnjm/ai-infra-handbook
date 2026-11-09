"""Binary search on the answer: find the smallest value for which a monotonic check passes."""
import math


def first_true(lo, hi, ok):
    """Smallest x in [lo, hi] with ok(x) True, assuming ok is False...False True...True.

    Returns hi + 1 if ok is never True. Integer search, so it always terminates.
    """
    while lo <= hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid - 1
        else:
            lo = mid + 1
    return lo


def min_replicas(peak_rps, per_replica_rps_fn, max_replicas=10_000):
    """Fewest replicas whose total capacity covers peak_rps, when per-replica
    capacity falls as replicas are added (shared-state overhead). Monotonic in n.
    """
    def ok(n):
        return n * per_replica_rps_fn(n) >= peak_rps
    n = first_true(1, max_replicas, ok)
    return None if n > max_replicas else n


def min_timeout_ms(latencies_ms, target_success):
    """Smallest integer timeout that lets at least target_success of requests finish."""
    n = len(latencies_ms)
    ok = lambda t: sum(x <= t for x in latencies_ms) >= math.ceil(target_success * n)
    return first_true(0, int(max(latencies_ms)) + 1, ok)


def min_window_hours(job_hours, nodes):
    """Smallest maintenance window (hours per node) so that jobs, run in the given order
    and split into at most `nodes` contiguous groups, each fit in the window.
    This is the classic 'split array largest sum' form of the pattern.
    """
    def ok(cap):
        groups, load = 1, 0
        for j in job_hours:
            if load + j > cap:
                groups += 1
                load = 0
            load += j
        return groups <= nodes

    return first_true(max(job_hours), sum(job_hours), ok)


def float_search(lo, hi, ok, iterations=60):
    """Binary search on reals: fixed iteration count, never `while lo != hi`."""
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi
