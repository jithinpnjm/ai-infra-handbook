"""M16: key-value store that answers 'what was the value at time t?'"""
import bisect


class TimeKV:
    """Timestamps per key must increase. set is O(1), get is O(log n)."""

    def __init__(self):
        self._ts = {}
        self._vals = {}

    def set(self, key, value, ts):
        times = self._ts.setdefault(key, [])
        if times and ts <= times[-1]:
            raise ValueError("timestamps must increase per key")
        times.append(ts)
        self._vals.setdefault(key, []).append(value)

    def get(self, key, ts):
        """Value with the largest timestamp <= ts, else None."""
        times = self._ts.get(key)
        if not times:
            return None
        i = bisect.bisect_right(times, ts)
        return self._vals[key][i - 1] if i else None
