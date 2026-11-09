"""M8: count contiguous windows whose values add up to k."""
from collections import defaultdict


def count_subarrays_with_sum(nums, k):
    """Prefix sums plus a hash of how often each prefix was seen. O(n) time. Negatives allowed."""
    seen = defaultdict(int)
    seen[0] = 1
    total = count = 0
    for x in nums:
        total += x
        count += seen[total - k]
        seen[total] += 1
    return count
