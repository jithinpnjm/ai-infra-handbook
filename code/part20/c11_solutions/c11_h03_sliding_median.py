"""H3: median of every window of k samples, two heaps with lazy deletion."""
import heapq
from collections import defaultdict


def sliding_median(nums, k):
    """O(n log k). Even k returns the mean of the two middle values as a float."""
    if k <= 0:
        raise ValueError("k must be positive")
    small, large = [], []  # small: max-heap by negation. large: min-heap
    delayed = defaultdict(int)  # values removed from the window but still inside a heap
    sizes = [0, 0]  # live sizes of small and large

    def prune(heap, negated):
        while heap:
            v = -heap[0] if negated else heap[0]
            if delayed[v] > 0:
                delayed[v] -= 1
                heapq.heappop(heap)
            else:
                break

    def rebalance():
        if sizes[0] > sizes[1] + 1:
            heapq.heappush(large, -heapq.heappop(small))
            sizes[0] -= 1
            sizes[1] += 1
            prune(small, True)
        elif sizes[0] < sizes[1]:
            heapq.heappush(small, -heapq.heappop(large))
            sizes[0] += 1
            sizes[1] -= 1
            prune(large, False)

    def add(x):
        if not small or x <= -small[0]:
            heapq.heappush(small, -x)
            sizes[0] += 1
        else:
            heapq.heappush(large, x)
            sizes[1] += 1
        rebalance()

    def remove(x):
        delayed[x] += 1
        if x <= -small[0]:
            sizes[0] -= 1
            if x == -small[0]:
                prune(small, True)
        else:
            sizes[1] -= 1
            if large and x == large[0]:
                prune(large, False)
        rebalance()

    out = []
    for i, x in enumerate(nums):
        add(x)
        if i >= k:
            remove(nums[i - k])
        if i >= k - 1:
            out.append(-small[0] if k % 2 else (-small[0] + large[0]) / 2)
    return out
