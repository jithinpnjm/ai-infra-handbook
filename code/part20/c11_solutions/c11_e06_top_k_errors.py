"""E6: the k most frequent error messages, ties broken alphabetically."""
import heapq
from collections import Counter


def top_k_errors(messages, k):
    """Return [(message, count)]. O(n + u log k) time with u distinct messages."""
    if k <= 0:
        return []
    counts = Counter(messages)
    return heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))
