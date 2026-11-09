"""E12: does any request id repeat within k positions?"""


def duplicate_within_k(ids, k):
    """Sliding set of the last k ids. O(n) time, O(k) space."""
    if k <= 0:
        return False
    window = set()
    for i, x in enumerate(ids):
        if x in window:
            return True
        window.add(x)
        if i >= k:
            window.discard(ids[i - k])
    return False
