"""P2: per-key rate limiters with retry-after hints, ready for tests.

Two algorithms behind one small interface: check(key, now) -> Decision.
- TokenBucket (from c11_m11): allows bursts up to capacity, then a steady rate.
- SlidingWindowLog: at most `limit` events in any window of `window` seconds. Exact, O(limit) memory per key.
KeyedLimiter keeps one limiter per key, evicts idle keys (LRU) so memory stays bounded, and is safe to call from threads.
"""
import threading
from collections import OrderedDict, deque
from dataclasses import dataclass

from c11_m11_token_bucket import TokenBucket


@dataclass(frozen=True)
class Decision:
    allowed: bool
    retry_after: float  # seconds to wait before the same request could pass, 0 if allowed


class SlidingWindowLog:
    def __init__(self, limit, window):
        if limit <= 0 or window <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window
        self._times = deque()

    def check(self, now):
        # an event at time t counts while now - t < window
        while self._times and now - self._times[0] >= self.window:
            self._times.popleft()
        if len(self._times) < self.limit:
            self._times.append(now)
            return Decision(True, 0.0)
        return Decision(False, self._times[0] + self.window - now)


class BucketAdapter:
    def __init__(self, rate, capacity):
        self._b = TokenBucket(rate, capacity)
        self._started = False

    def check(self, now):
        if not self._started:  # the bucket starts full at the first call
            self._b = TokenBucket(self._b.rate, self._b.capacity, now=now)
            self._started = True
        if self._b.allow(now):
            return Decision(True, 0.0)
        return Decision(False, self._b.wait_time(now))


class KeyedLimiter:
    def __init__(self, factory, max_keys=10_000):
        self._factory = factory
        self._max = max_keys
        self._by_key = OrderedDict()
        self._lock = threading.Lock()

    def check(self, key, now):
        with self._lock:
            lim = self._by_key.pop(key, None)
            if lim is None:
                lim = self._factory()
            self._by_key[key] = lim  # most recently used goes last
            while len(self._by_key) > self._max:
                self._by_key.popitem(last=False)
            return lim.check(now)

    def __len__(self):
        return len(self._by_key)
