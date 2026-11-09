"""M3: peak number of overlapping jobs. Jobs are half-open [start, end)."""


def peak_concurrency(jobs):
    """Sweep line over sorted events. An end at t is processed before a start at t."""
    events = []
    for s, e in jobs:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()  # (t, -1) sorts before (t, 1)
    cur = best = 0
    for _, delta in events:
        cur += delta
        best = max(best, cur)
    return best
