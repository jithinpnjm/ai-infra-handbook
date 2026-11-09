"""E10: moving average over a window of k samples."""


def moving_average(xs, k):
    """Average of every full window. Running sum, O(n) time. Ints keep the sum exact."""
    if k <= 0:
        raise ValueError("k must be positive")
    if k > len(xs):
        return []
    total = sum(xs[:k])
    out = [total / k]
    for i in range(k, len(xs)):
        total += xs[i] - xs[i - k]
        out.append(total / k)
    return out
