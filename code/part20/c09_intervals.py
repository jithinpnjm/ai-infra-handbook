"""Interval merging and scheduling."""
import heapq


def merge_intervals(intervals):
    """Merge overlapping or touching [start, end] intervals."""
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)   # max: the new one may sit inside the old one
        else:
            out.append([s, e])
    return [tuple(x) for x in out]


def free_slots(busy, day_start, day_end):
    """Gaps inside [day_start, day_end] not covered by any busy interval."""
    gaps, cursor = [], day_start
    for s, e in merge_intervals(busy):
        if s > cursor:
            gaps.append((cursor, min(s, day_end)))
        cursor = max(cursor, e)
        if cursor >= day_end:
            break
    if cursor < day_end:
        gaps.append((cursor, day_end))
    return [g for g in gaps if g[0] < g[1]]


def min_gpu_nodes(reservations):
    """Fewest nodes so that no two overlapping reservations share one.

    Half-open [start, end): a job ending at 10 frees its node for one starting at 10.
    """
    ends = []  # min-heap of end times of reservations currently holding a node
    for s, e in sorted(reservations):
        if ends and ends[0] <= s:
            heapq.heapreplace(ends, e)
        else:
            heapq.heappush(ends, e)
    return len(ends)


def max_overlap_sweep(reservations):
    """Same answer with an event sweep. Ends sort before starts at the same time."""
    events = []
    for s, e in reservations:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()                 # (t, -1) < (t, +1)
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best


def fits_window(existing, new):
    """True if the half-open interval `new` overlaps none of `existing`."""
    ns, ne = new
    return all(ne <= s or e <= ns for s, e in existing)
