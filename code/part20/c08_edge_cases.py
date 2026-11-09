# code/part20/c08_edge_cases.py
"""Six small solutions plus the edge-case checklists you run by hand (chapter 20.8)."""
import heapq
from collections import Counter

# Probe inputs to try on any function, by input type. Say them aloud in the interview.
EDGE_CHECKLISTS = {
    "string": ["", "a", "aa", "ab", "aaabbb", " ", "AaAa"],
    "list": [[], [0], [1, 1], [3, 1, 2], [-1, -1, -1], [5, 4, 3, 2, 1]],
    "pair of lists": [([], []), ([1], []), ([], [1]), ([1], [1])],
    "intervals": [[], [(1, 2)], [(1, 2), (2, 3)], [(1, 5), (2, 3)], [(3, 4), (1, 2)]],
    "number": [0, 1, -1, 2 ** 31, 0.1 + 0.2],
}


def compress(s):
    """'aabcccccaaa' -> 'a2b1c5a3'. Return s if the result is not shorter.

    Ask first: should a single letter keep its '1'? Here it does.
    """
    if not s:
        return s
    parts = []
    run_char, run_len = s[0], 1
    for ch in s[1:]:
        if ch == run_char:
            run_len += 1
        else:
            parts.append(run_char + str(run_len))
            run_char, run_len = ch, 1
    parts.append(run_char + str(run_len))
    packed = "".join(parts)
    return packed if len(packed) < len(s) else s


def two_sum(nums, target):
    """Indices (i, j), i < j, with nums[i] + nums[j] == target, else None."""
    seen = {}
    for j, value in enumerate(nums):
        i = seen.get(target - value)
        if i is not None:
            return (i, j)
        seen.setdefault(value, j)
    return None


def top_k_frequent(items, k):
    """k most common items. Ties go to the smaller item, so output is stable."""
    counts = Counter(items)
    return [item for item, _ in heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def merge_intervals(intervals):
    """Merge closed intervals. Touching intervals merge: (1,2),(2,3) -> (1,3)."""
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def valid_brackets(text):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in text:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


def longest_unique_window(s):
    """Length of the longest substring with no repeated character."""
    last_seen = {}
    left = best = 0
    for right, ch in enumerate(s):
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best
