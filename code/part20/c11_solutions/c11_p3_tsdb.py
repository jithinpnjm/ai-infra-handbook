"""P3: in-memory time-series store with range queries, downsampling and retention.

Each series is a name mapped to two parallel sorted lists (timestamps, values).
Insert is O(log n) to find the place, O(n) worst case to shift (append is O(1)).
Range query is O(log n + k). Ranges are half-open: start <= t < end.
"""
import bisect

AGGS = {
    "sum": sum,
    "min": min,
    "max": max,
    "count": len,
    "avg": lambda xs: sum(xs) / len(xs),
    "last": lambda xs: xs[-1],
}


class TimeSeriesStore:
    def __init__(self):
        self._ts = {}
        self._vals = {}

    def insert(self, name, ts, value):
        """Out-of-order points are placed correctly. The same timestamp overwrites."""
        times = self._ts.setdefault(name, [])
        vals = self._vals.setdefault(name, [])
        i = bisect.bisect_left(times, ts)
        if i < len(times) and times[i] == ts:
            vals[i] = value
        else:
            times.insert(i, ts)
            vals.insert(i, value)

    def query(self, name, start, end):
        times = self._ts.get(name)
        if not times:
            return []
        lo = bisect.bisect_left(times, start)
        hi = bisect.bisect_left(times, end)
        return list(zip(times[lo:hi], self._vals[name][lo:hi]))

    def downsample(self, name, start, end, step, agg="avg"):
        """Return [(bucket_start, aggregate)] for non-empty buckets.

        Buckets are aligned to start: [start, start+step), ... Empty buckets are skipped.
        """
        if step <= 0:
            raise ValueError("step must be positive")
        fn = AGGS[agg]
        buckets = {}
        for ts, v in self.query(name, start, end):
            buckets.setdefault(start + ((ts - start) // step) * step, []).append(v)
        return [(b, fn(vs)) for b, vs in sorted(buckets.items())]

    def drop_before(self, name, cutoff):
        """Retention: delete points older than cutoff. Return how many were removed."""
        times = self._ts.get(name)
        if not times:
            return 0
        i = bisect.bisect_left(times, cutoff)
        del times[:i]
        del self._vals[name][:i]
        return i
