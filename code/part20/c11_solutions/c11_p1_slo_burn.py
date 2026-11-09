"""P1: read an access-log stream and report SLO burn rate over several windows.

Line shape: '<ISO-8601 UTC ts> <method> <path> <status> <latency_ms>'.
A request is bad if status >= 500 or latency is above the SLO latency limit.
Burn rate = (bad / total) / (1 - target). A burn rate of 1 spends the error
budget exactly at the pace that would use it all by the end of the SLO period.

Memory is bounded: counts live in per-minute buckets and old buckets are evicted.
Windows are bucket-aligned: a window of W seconds ending at `now` covers the
W/bucket buckets that end with the bucket holding `now`.
"""
from datetime import datetime, timezone


def parse_line(line):
    """Return (epoch_seconds, is_5xx, latency_ms) or None for a malformed line."""
    parts = line.split()
    if len(parts) != 5:
        return None
    try:
        ts = datetime.fromisoformat(parts[0].replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        status, ms = int(parts[3]), float(parts[4])
    except ValueError:
        return None
    return ts.timestamp(), status >= 500, ms


class SloTracker:
    def __init__(self, target=0.999, latency_ms=2000.0, bucket_s=60, retention_s=6 * 3600):
        if not 0 < target < 1:
            raise ValueError("target must be between 0 and 1")
        self.budget = 1 - target
        self.latency_ms = latency_ms
        self.bucket_s = bucket_s
        self.retention_s = retention_s
        self._buckets = {}  # bucket id -> [bad, total]
        self._newest = None
        self.malformed = 0

    def ingest(self, line):
        parsed = parse_line(line)
        if parsed is None:
            self.malformed += 1
            return False
        epoch, is_5xx, ms = parsed
        bad = is_5xx or ms > self.latency_ms
        b = int(epoch // self.bucket_s)
        cell = self._buckets.setdefault(b, [0, 0])
        cell[0] += bad
        cell[1] += 1
        if self._newest is None or b > self._newest:
            self._newest = b
            horizon = b - self.retention_s // self.bucket_s
            for old in [k for k in self._buckets if k <= horizon]:
                del self._buckets[old]
        return True

    def ingest_all(self, lines):
        for line in lines:
            self.ingest(line)

    def counts(self, now, window_s):
        end = int(now // self.bucket_s)
        start = end - window_s // self.bucket_s
        bad = total = 0
        for b, (x, t) in self._buckets.items():
            if start < b <= end:
                bad += x
                total += t
        return bad, total

    def burn_rate(self, now, window_s):
        """Return the burn rate, or 0.0 when the window saw no traffic."""
        bad, total = self.counts(now, window_s)
        return 0.0 if total == 0 else (bad / total) / self.budget

    def alerts(self, now, rules):
        """rules: [(name, long_window_s, short_window_s, threshold)].

        An alert fires only when BOTH windows are at or above the threshold. The long
        window proves the burn is large, the short one proves it is still happening.
        """
        fired = []
        for name, long_w, short_w, threshold in rules:
            if self.burn_rate(now, long_w) >= threshold and self.burn_rate(now, short_w) >= threshold:
                fired.append(name)
        return fired
