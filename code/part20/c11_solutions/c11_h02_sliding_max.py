"""H2: maximum of every window of k samples."""
from collections import deque


def sliding_max(xs, k):
    """Monotonic deque of indices whose values decrease. Each index enters and leaves once: O(n)."""
    if k <= 0:
        raise ValueError("k must be positive")
    dq = deque()
    out = []
    for i, x in enumerate(xs):
        while dq and xs[dq[-1]] <= x:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            out.append(xs[dq[0]])
    return out
