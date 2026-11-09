"""Sliding windows: rolling error rate and max in a window, both with a deque."""
from collections import deque


class RollingErrorRate:
    """Error rate over the last `window_s` seconds. Events must arrive in time order."""

    def __init__(self, window_s):
        self.window_s = window_s
        self.events = deque()   # (timestamp, is_error)
        self.errors = 0

    def _evict(self, now):
        # Keep events with now - window_s < ts, so the window is half-open.
        while self.events and self.events[0][0] <= now - self.window_s:
            _, was_error = self.events.popleft()
            self.errors -= was_error

    def add(self, ts, is_error):
        self.events.append((ts, bool(is_error)))
        self.errors += bool(is_error)
        self._evict(ts)

    def rate(self, now):
        self._evict(now)
        return self.errors / len(self.events) if self.events else 0.0


def sliding_max(values, k):
    """Maximum of every window of k values. The deque holds indexes of decreasing values."""
    if k <= 0:
        raise ValueError("k must be positive")
    dq, out = deque(), []
    for i, v in enumerate(values):
        while dq and values[dq[-1]] <= v:
            dq.pop()                    # smaller older values can never be a max again
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()                # front index fell out of the window
        if i >= k - 1:
            out.append(values[dq[0]])
    return out


def sliding_max_naive(values, k):
    return [max(values[i:i + k]) for i in range(len(values) - k + 1)]


def longest_run_below(values, limit):
    """Longest stretch whose sum stays <= limit (all values >= 0). Variable window."""
    best = left = total = 0
    for right, v in enumerate(values):
        total += v
        while total > limit:
            total -= values[left]
            left += 1
        best = max(best, right - left + 1)
    return best
