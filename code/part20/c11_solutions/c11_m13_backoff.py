"""M13: retry delays with exponential backoff and full jitter."""
import random


def backoff_ceiling(attempt, base, cap):
    """Upper bound for the delay after attempt number `attempt` (0-based)."""
    return min(cap, base * (2 ** min(attempt, 60)))


def backoff_schedule(attempts, base, cap, rng=None, budget=None):
    """Each delay is uniform in [0, ceiling]. Stop early if the total would pass budget.

    Pass a seeded random.Random for repeatable tests.
    """
    rng = rng or random.Random()
    out = []
    total = 0.0
    for i in range(attempts):
        d = rng.uniform(0, backoff_ceiling(i, base, cap))
        if budget is not None and total + d > budget:
            break
        out.append(d)
        total += d
    return out
