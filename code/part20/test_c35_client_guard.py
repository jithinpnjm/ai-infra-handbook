import pytest

from c35_client_guard import (
    ClientGuard, MutationCapExceeded, RateLimited, RetryBudget, RetryBudgetExhausted,
    TokenBucket)
from c35_operation_poller import ApiError, FakeClock, RETRY_CALL, RETRY_NOTHING


def make(clock=None, rate=10, burst=5, ratio=0.1, reserve=10, **kw):
    clock = clock or FakeClock()
    return clock, ClientGuard(clock, limiter=TokenBucket(rate, burst, clock),
                              budget=RetryBudget(ratio, reserve), **kw)


def flaky(failures, err):
    state = {"n": 0, "keys": []}

    def fn(key):
        state["keys"].append(key)
        state["n"] += 1
        if state["n"] <= failures:
            raise err
        return "ok"
    return fn, state


def test_bucket_allows_burst_then_throttles():
    c = FakeClock()
    b = TokenBucket(2, 3, c)
    for _ in range(3):
        assert b.wait_time() == 0
        b.take()
    assert b.wait_time() == pytest.approx(0.5)
    c.now += 0.5
    assert b.wait_time() == 0


def test_guard_sleeps_to_respect_rate():
    c, g = make(rate=2, burst=1)
    for _ in range(3):
        g.call(lambda k: "ok")
    assert c.now == pytest.approx(1.0)               # 2 extra calls at 2 per second
    assert g.stats.rate_waits == pytest.approx(1.0)


def test_rate_wait_above_limit_raises():
    c, g = make(rate=0.01, burst=1, max_rate_wait=5)
    g.call(lambda k: "ok")
    with pytest.raises(RateLimited):
        g.call(lambda k: "ok")


def test_retries_unavailable_with_backoff_then_succeeds():
    c, g = make(base_delay=0.5)
    fn, st = flaky(2, ApiError("UNAVAILABLE", "x"))
    assert g.call(fn) == "ok"
    assert st["n"] == 3 and g.stats.retries == 2
    assert [s for s in c.sleeps if s >= 0.5] == [0.5, 1.0]


def test_gives_up_after_max_attempts():
    c, g = make(max_attempts=3)
    fn, st = flaky(99, ApiError("UNAVAILABLE", "x"))
    with pytest.raises(ApiError):
        g.call(fn)
    assert st["n"] == 3


def test_quota_failure_is_not_retried_even_though_code_is_resource_exhausted():
    c, g = make()
    fn, st = flaky(99, ApiError("RESOURCE_EXHAUSTED", "gpu quota", service_code="QuotaFailure"))
    with pytest.raises(ApiError):
        g.call(fn)
    assert st["n"] == 1


def test_plain_resource_exhausted_is_retried_as_rate_limit():
    c, g = make()
    fn, st = flaky(1, ApiError("RESOURCE_EXHAUSTED", "slow down", service_code="TooManyRequests"))
    assert g.call(fn) == "ok" and st["n"] == 2


def test_retry_type_nothing_stops_retry():
    c, g = make()
    fn, st = flaky(99, ApiError("UNAVAILABLE", "x", retry_type=RETRY_NOTHING))
    with pytest.raises(ApiError):
        g.call(fn)
    assert st["n"] == 1


def test_retry_type_call_retries_odd_codes():
    c, g = make()
    fn, st = flaky(1, ApiError("INTERNAL", "x", retry_type=RETRY_CALL))
    assert g.call(fn) == "ok"


def test_permission_denied_is_never_retried():
    c, g = make()
    fn, st = flaky(99, ApiError("PERMISSION_DENIED", "x"))
    with pytest.raises(ApiError):
        g.call(fn)
    assert st["n"] == 1


def test_mutation_reuses_one_idempotency_key_across_attempts():
    c, g = make(key_factory=iter(["k1", "k2", "k3"]).__next__)
    fn, st = flaky(2, ApiError("UNAVAILABLE", "x"))
    g.call(fn, mutating=True)
    assert st["keys"] == ["k1", "k1", "k1"]


def test_read_sends_no_key_and_two_mutations_get_two_keys():
    c, g = make(key_factory=iter(["k1", "k2"]).__next__)
    seen = []
    g.call(lambda k: seen.append(k))
    g.call(lambda k: seen.append(k), mutating=True)
    g.call(lambda k: seen.append(k), mutating=True)
    assert seen == [None, "k1", "k2"]


def test_retry_budget_stops_a_retry_storm():
    c, g = make(ratio=0.1, reserve=3, max_attempts=5)
    refused = 0
    for _ in range(20):
        fn, _st = flaky(99, ApiError("UNAVAILABLE", "x"))
        try:
            g.call(fn)
        except RetryBudgetExhausted:
            refused += 1
        except ApiError:
            pass
    # 20 calls with a 0.1 ratio and 3 in reserve: far fewer than 4 retries per call
    assert g.stats.retries <= 3 + 20 * 0.1 + 1e-9
    assert refused > 10 and g.stats.refused_retries


def test_budget_refills_from_successful_traffic():
    b = RetryBudget(ratio=0.5, reserve=2)
    assert b.try_spend() and b.try_spend() and not b.try_spend()
    b.on_request(); b.on_request()
    assert b.try_spend()


def test_mutation_cap_limits_blast_radius():
    c, g = make(max_mutations=2)
    g.call(lambda k: "ok", mutating=True)
    g.call(lambda k: "ok", mutating=True)
    with pytest.raises(MutationCapExceeded):
        g.call(lambda k: "ok", mutating=True)
    assert g.call(lambda k: "ok") == "ok"            # reads are not capped


def test_dry_run_counts_but_never_calls():
    c, g = make(dry_run=True)
    called = []
    assert g.call(lambda k: called.append(1), mutating=True) is None
    assert called == [] and g.stats.dry_runs == 1


def test_bucket_rejects_bad_config():
    with pytest.raises(ValueError):
        TokenBucket(0, 1, FakeClock())


def test_deadline_exceeded_on_a_write_is_retried_with_the_same_key():
    c, g = make(key_factory=iter(["k1", "k2"]).__next__)
    fn, st = flaky(1, ApiError("DEADLINE_EXCEEDED", "slow"))
    g.call(fn, mutating=True)
    assert st["keys"] == ["k1", "k1"]


def test_cancelled_is_not_retried():
    c, g = make()
    fn, st = flaky(5, ApiError("CANCELLED", "x"))
    with pytest.raises(ApiError):
        g.call(fn)
    assert st["n"] == 1
