"""Four rate limiters. The clock is always passed in, so tests never sleep.

Each allow(now) returns True or False. Callers must pass non-decreasing times.
For a token bucket that counts LLM tokens and keeps per-tenant state, see
gw13_token_bucket.py in chapter 20.13.
"""
from collections import deque


class FixedWindow:
    """Count requests per window of `window_s`. Cheapest, but allows a 2x burst at the edge."""

    def __init__(self, limit, window_s):
        self.limit, self.window_s = limit, window_s
        self.window_id, self.count = None, 0

    def allow(self, now):
        wid = int(now // self.window_s)
        if wid != self.window_id:
            self.window_id, self.count = wid, 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


class SlidingLog:
    """Remember every accepted timestamp. Exact, but memory is O(limit) per key."""

    def __init__(self, limit, window_s):
        self.limit, self.window_s = limit, window_s
        self.log = deque()

    def allow(self, now):
        while self.log and self.log[0] <= now - self.window_s:
            self.log.popleft()
        if len(self.log) < self.limit:
            self.log.append(now)
            return True
        return False


class SlidingCounter:
    """Two fixed windows blended by overlap. O(1) memory, approximate."""

    def __init__(self, limit, window_s):
        self.limit, self.window_s = limit, window_s
        self.wid, self.cur, self.prev = None, 0, 0

    def allow(self, now):
        wid = int(now // self.window_s)
        if self.wid is None:
            self.wid = wid
        elif wid == self.wid + 1:
            self.prev, self.cur, self.wid = self.cur, 0, wid
        elif wid > self.wid + 1:
            self.prev, self.cur, self.wid = 0, 0, wid
        frac_prev = 1 - (now % self.window_s) / self.window_s
        if self.prev * frac_prev + self.cur + 1 <= self.limit:
            self.cur += 1
            return True
        return False


class TokenBucket:
    """Refill at `rate` per second up to `burst`. Allows bursts, enforces the long-run rate."""

    def __init__(self, rate, burst):
        self.rate, self.burst = rate, burst
        self.level, self.last = float(burst), None

    def allow(self, now, cost=1):
        if self.last is not None:
            self.level = min(self.burst, self.level + (now - self.last) * self.rate)
        self.last = now
        if self.level >= cost:
            self.level -= cost
            return True
        return False


class LeakyBucket:
    """Meter version: a queue that drains at `rate`; a request is refused if it would overflow.

    Output is smooth, so unlike the token bucket it does not let a burst through.
    """

    def __init__(self, rate, capacity):
        self.rate, self.capacity = rate, capacity
        self.water, self.last = 0.0, None

    def allow(self, now):
        if self.last is not None:
            self.water = max(0.0, self.water - (now - self.last) * self.rate)
        self.last = now
        if self.water + 1 <= self.capacity:
            self.water += 1
            return True
        return False
