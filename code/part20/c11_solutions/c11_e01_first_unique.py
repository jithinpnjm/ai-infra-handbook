"""E1: first request id that appears exactly once."""
from collections import Counter


def first_unique(ids):
    """Return the first id that occurs once, or None. O(n) time, O(u) space."""
    counts = Counter(ids)
    for x in ids:
        if counts[x] == 1:
            return x
    return None
