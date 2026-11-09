"""Streaming percentiles: exact, reservoir sample, fixed-bucket histogram, and the averaging trap."""
import bisect
import math
import random


def percentile(sorted_vals, p):
    """Nearest-rank percentile, p in (0, 100]. The smallest value with at least p% at or below it."""
    if not sorted_vals:
        raise ValueError("empty")
    if not 0 < p <= 100:
        raise ValueError("p must be in (0, 100]")
    rank = math.ceil(p / 100 * len(sorted_vals))
    return sorted_vals[rank - 1]


class Reservoir:
    """Algorithm R: a uniform random sample of k items from a stream of unknown length."""

    def __init__(self, k, rng=None):
        self.k, self.n, self.items = k, 0, []
        self.rng = rng or random.Random()

    def add(self, x):
        self.n += 1
        if len(self.items) < self.k:
            self.items.append(x)
        else:
            j = self.rng.randrange(self.n)      # 0 .. n-1 inclusive
            if j < self.k:
                self.items[j] = x

    def percentile(self, p):
        return percentile(sorted(self.items), p)


class LogHistogram:
    """Fixed buckets with geometric boundaries, like a Prometheus histogram.

    Memory is the number of buckets. Error is bounded by the bucket ratio.
    Histograms from many servers can be added bucket by bucket.
    """

    def __init__(self, lo=1.0, hi=100_000.0, ratio=1.1):
        self.bounds = []
        b = lo
        while b < hi * ratio:
            self.bounds.append(b)
            b *= ratio
        self.counts = [0] * (len(self.bounds) + 1)   # last bucket: above every bound

    def add(self, x):
        self.counts[bisect.bisect_left(self.bounds, x)] += 1

    def merge(self, other):
        assert self.bounds == other.bounds
        for i, c in enumerate(other.counts):
            self.counts[i] += c

    def quantile(self, q):
        """Upper bound of the bucket holding the q-th quantile, q in (0, 1]."""
        total = sum(self.counts)
        target = math.ceil(q * total)
        seen = 0
        for i, c in enumerate(self.counts):
            seen += c
            if seen >= target:
                return self.bounds[min(i, len(self.bounds) - 1)]
        raise ValueError("empty")


def average_of_p99s(groups):
    """The wrong way to get a fleet p99: average each server's p99."""
    return sum(percentile(sorted(g), 99) for g in groups) / len(groups)


def true_p99(groups):
    return percentile(sorted(x for g in groups for x in g), 99)
