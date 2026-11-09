"""M14: shortest time span that contains every required event type."""
from collections import Counter


def shortest_span(events, required):
    """events: list of (timestamp, type) sorted by timestamp.

    Return (start_ts, end_ts) of a shortest span holding all required types, or
    None. Two pointers: O(n) time. Several spans may tie. Any one is correct.
    """
    need = set(required)
    if not need:
        return None
    have = Counter()
    missing = len(need)
    best = None
    left = 0
    for right, (ts_r, typ) in enumerate(events):
        if typ in need:
            have[typ] += 1
            if have[typ] == 1:
                missing -= 1
        while missing == 0:
            ts_l, typ_l = events[left]
            if best is None or ts_r - ts_l < best[1] - best[0]:
                best = (ts_l, ts_r)
            if typ_l in need:
                have[typ_l] -= 1
                if have[typ_l] == 0:
                    missing += 1
            left += 1
    return best
