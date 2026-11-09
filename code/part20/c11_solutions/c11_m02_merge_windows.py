"""M2: merge maintenance windows. Intervals are half-open [start, end)."""


def merge_windows(intervals):
    """Touching windows merge: [1,3) and [3,5) become [1,5). O(n log n)."""
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            if e > out[-1][1]:
                out[-1][1] = e
        else:
            out.append([s, e])
    return [tuple(x) for x in out]
