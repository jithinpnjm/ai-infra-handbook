"""Heaps: top-k and merging k sorted streams."""
import heapq


def top_k_slowest(samples, k):
    """samples: iterable of (endpoint, ms). Return the k slowest, slowest first.

    Keeps a min-heap of size k, so memory is O(k) and time is O(n log k).
    """
    if k <= 0:
        return []
    heap = []  # (ms, endpoint): the root is the fastest of the current top k
    for endpoint, ms in samples:
        item = (ms, endpoint)
        if len(heap) < k:
            heapq.heappush(heap, item)
        elif item > heap[0]:
            heapq.heapreplace(heap, item)
    return [(e, ms) for ms, e in sorted(heap, reverse=True)]


def merge_k_sorted(streams):
    """Merge k sorted iterables lazily. Heap entries carry the stream index as tiebreak."""
    heap = []
    iters = [iter(s) for s in streams]
    for idx, it in enumerate(iters):
        for first in it:
            heap.append((first, idx))
            break
    heapq.heapify(heap)
    while heap:
        value, idx = heap[0]
        yield value
        nxt = next(iters[idx], heap)     # sentinel: the heap itself
        if nxt is heap:
            heapq.heappop(heap)
        else:
            heapq.heapreplace(heap, (nxt, idx))


class RunningMedian:
    """Median of a stream with two heaps. O(log n) add, O(1) read."""

    def __init__(self):
        self.low = []    # max-heap by negation
        self.high = []   # min-heap

    def add(self, x):
        heapq.heappush(self.low, -x)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def median(self):
        if not self.low:
            raise ValueError("empty")
        if len(self.low) > len(self.high):
            return float(-self.low[0])
        return (-self.low[0] + self.high[0]) / 2
