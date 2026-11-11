"""A guard around an API client: rate limit, retry budget, safe retries, mutation cap.

The guard is a design for fleet automation, not a Nebius component. It uses the
error model the public API documents (gRPC code plus ServiceError retry_type) and
the X-Idempotency-Key convention. Time is injected, so tests need no real sleeping.
Standard library only.
"""
import uuid
from dataclasses import dataclass, field

from c35_operation_poller import ApiError, RETRY_CALL, RETRY_NOTHING, RETRY_UNIT_OF_WORK

# ServiceError details that mean "do not hammer this": a quota or capacity answer
# does not change in a second. (Design choice: the API sends RESOURCE_EXHAUSTED for
# these too, and the Go SDK retries that code unless retry_type says otherwise.)
NON_RETRIABLE_SERVICE_CODES = frozenset({"QuotaFailure", "NotEnoughResources"})


_EPS = 1e-9


class RateLimited(Exception):
    """The local rate limiter would have to wait longer than max_wait."""


class RetryBudgetExhausted(Exception):
    """Retries are cut off so a failing dependency is not hit harder."""

    def __init__(self, last):
        super().__init__(f"retry budget exhausted after: {last}")
        self.last = last


class MutationCapExceeded(Exception):
    """This run already made its allowed number of mutating calls."""


class TokenBucket:
    def __init__(self, rate_per_s, burst, clock):
        if rate_per_s <= 0 or burst < 1:
            raise ValueError("rate must be positive and burst at least 1")
        self.rate, self.burst, self.clock = rate_per_s, burst, clock
        self.tokens = float(burst)
        self.last = clock.monotonic()

    def _refill(self):
        now = self.clock.monotonic()
        self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rate)
        self.last = now

    def wait_time(self):
        self._refill()
        return 0.0 if self.tokens >= 1 - _EPS else (1 - self.tokens) / self.rate

    def take(self):
        self._refill()
        if self.tokens < 1 - _EPS:
            raise RuntimeError("take() without tokens")
        self.tokens = max(0.0, self.tokens - 1)


class RetryBudget:
    """Retries may add at most `ratio` extra calls per original call, on average.
    `reserve` lets a quiet client retry a few times after a cold start."""

    def __init__(self, ratio=0.1, reserve=10):
        self.ratio, self.reserve = ratio, float(reserve)
        self.tokens = float(reserve)

    def on_request(self):
        self.tokens = min(self.reserve, self.tokens + self.ratio)

    def try_spend(self):
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


@dataclass
class GuardStats:
    calls: int = 0
    attempts: int = 0
    retries: int = 0
    rate_waits: float = 0.0
    mutations: int = 0
    dry_runs: int = 0
    refused_retries: list = field(default_factory=list)


class ClientGuard:
    def __init__(self, clock, *, limiter, budget, max_attempts=3, base_delay=0.2,
                 max_delay=10.0, max_rate_wait=30.0, max_mutations=None, dry_run=False,
                 key_factory=lambda: str(uuid.uuid4())):
        self.clock, self.limiter, self.budget = clock, limiter, budget
        self.max_attempts, self.base_delay, self.max_delay = max_attempts, base_delay, max_delay
        self.max_rate_wait = max_rate_wait
        self.max_mutations, self.dry_run = max_mutations, dry_run
        self.key_factory = key_factory
        self.stats = GuardStats()

    def retriable(self, err):
        if not isinstance(err, ApiError):
            return False
        if err.service_code in NON_RETRIABLE_SERVICE_CODES:
            return False
        if err.code == "CANCELLED":
            return False
        if err.code == "DEADLINE_EXCEEDED":
            # The docs say a write can time out yet complete. Retrying is safe only because
            # call() reuses the idempotency key of a mutating request.
            return True
        if err.retry_type == RETRY_CALL:
            return True
        if err.retry_type in (RETRY_NOTHING, RETRY_UNIT_OF_WORK):
            return False
        return err.code in ("RESOURCE_EXHAUSTED", "UNAVAILABLE")

    def _acquire(self):
        wait = self.limiter.wait_time()
        if wait > self.max_rate_wait:
            raise RateLimited(f"would wait {wait:.1f}s")
        if wait > 0:
            self.clock.sleep(wait)
            self.stats.rate_waits += wait
        self.limiter.take()

    def call(self, fn, *, mutating=False):
        """Run fn(idempotency_key). Reads pass key=None. A mutating call gets one key,
        reused on every attempt, and is never retried when no key could be sent."""
        self.stats.calls += 1
        key = None
        if mutating:
            if self.max_mutations is not None and self.stats.mutations >= self.max_mutations:
                raise MutationCapExceeded(f"cap of {self.max_mutations} mutations reached")
            self.stats.mutations += 1
            if self.dry_run:
                self.stats.dry_runs += 1
                return None
            key = self.key_factory()
        self.budget.on_request()
        attempt = 0
        while True:
            attempt += 1
            self._acquire()
            self.stats.attempts += 1
            try:
                return fn(key)
            except ApiError as err:
                if not self.retriable(err):
                    raise
                if attempt >= self.max_attempts:
                    raise
                if not self.budget.try_spend():
                    self.stats.refused_retries.append(err.code)
                    raise RetryBudgetExhausted(err) from err
                self.stats.retries += 1
                self.clock.sleep(min(self.max_delay, self.base_delay * 2 ** (attempt - 1)))
