"""M5: kth largest value in a stream."""
import heapq


class KthLargest:
    """Min-heap of the k largest values. add is O(log k), memory O(k)."""

    def __init__(self, k, initial=()):
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k
        self._h = []
        for x in initial:
            self.add(x)

    def add(self, x):
        """Insert x. Return the kth largest so far, or None if fewer than k values."""
        if len(self._h) < self.k:
            heapq.heappush(self._h, x)
        elif x > self._h[0]:
            heapq.heapreplace(self._h, x)
        return self._h[0] if len(self._h) == self.k else None
