"""Token-bucket rate limiter that counts LLM tokens, not requests.

The clock is passed in, so tests and simulations never sleep.
"""
from dataclasses import dataclass


@dataclass
class TokenBucket:
    rate: float          # tokens added per second
    burst: float         # bucket size in tokens
    level: float = None  # current tokens, starts full
    last: float = 0.0    # time of last refill

    def __post_init__(self):
        if self.level is None:
            self.level = self.burst

    def _refill(self, now):
        elapsed = max(0.0, now - self.last)
        self.level = min(self.burst, self.level + elapsed * self.rate)
        self.last = now

    def try_take(self, cost, now):
        """Take cost tokens if available. Return (allowed, retry_after_s)."""
        self._refill(now)
        if cost > self.burst:
            return False, float("inf")   # can never fit: reject, do not queue
        if self.level >= cost:
            self.level -= cost
            return True, 0.0
        return False, (cost - self.level) / self.rate

    def refund(self, tokens, now):
        """Give back tokens that were reserved but not used."""
        self._refill(now)
        self.level = min(self.burst, self.level + tokens)


class TenantLimiter:
    """Two buckets per tenant: requests per second and tokens per second.

    Admission charges prompt tokens plus the requested max_tokens up front.
    When the response ends, finish() refunds the output tokens not generated.
    """

    def __init__(self, rpm, tpm):
        self.rps_bucket = TokenBucket(rate=rpm / 60.0, burst=max(1.0, rpm / 6.0))
        self.tok_bucket = TokenBucket(rate=tpm / 60.0, burst=tpm / 6.0)

    def admit(self, prompt_tokens, max_tokens, now):
        reserve = prompt_tokens + max_tokens
        ok_r, wait_r = self.rps_bucket.try_take(1, now)
        if not ok_r:
            return False, wait_r, 0
        ok_t, wait_t = self.tok_bucket.try_take(reserve, now)
        if not ok_t:
            self.rps_bucket.refund(1, now)   # a rejected call must not cost a request slot
            return False, wait_t, 0
        return True, 0.0, reserve

    def finish(self, reserved, prompt_tokens, generated, now):
        unused = reserved - (prompt_tokens + generated)
        if unused > 0:
            self.tok_bucket.refund(unused, now)
