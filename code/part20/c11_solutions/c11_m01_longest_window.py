"""M1: longest stretch of requests with at most k failures."""


def longest_window(flags, k):
    """flags[i] is 1 for a failure, 0 for success. Two pointers, O(n) time, O(1) space."""
    if k < 0:
        raise ValueError("k must be >= 0")
    best = left = bad = 0
    for right, f in enumerate(flags):
        bad += f
        while bad > k:
            bad -= flags[left]
            left += 1
        best = max(best, right - left + 1)
    return best
