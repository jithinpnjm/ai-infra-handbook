"""M11: token bucket with an injected clock."""


class TokenBucket:
    """Starts full. Refill is rate tokens per second, capped at capacity.

    The caller passes `now` so tests need no sleep. A clock that goes backwards
    is clamped: it never removes tokens and never adds them.
    """

    def __init__(self, rate, capacity, now=0.0):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be positive")
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last = now

    def _refill(self, now):
        if now > self._last:
            self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
            self._last = now

    def allow(self, now, cost=1):
        """Take cost tokens if available. Costs above capacity can never succeed."""
        self._refill(now)
        if cost <= self._tokens:
            self._tokens -= cost
            return True
        return False

    def wait_time(self, now, cost=1):
        """Seconds until cost tokens are available. inf if cost > capacity."""
        if cost > self.capacity:
            return float("inf")
        self._refill(now)
        return max(0.0, (cost - self._tokens) / self.rate)
