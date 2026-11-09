import math
from gw13_token_bucket import TokenBucket, TenantLimiter
from gw13_router_sim import simulate


def test_bucket_burst_then_refill():
    b = TokenBucket(rate=100, burst=1000)
    assert b.try_take(1000, now=0)[0]
    ok, wait = b.try_take(500, now=0)
    assert not ok and math.isclose(wait, 5.0)
    assert b.try_take(500, now=5.0)[0]


def test_bucket_rejects_request_larger_than_burst():
    ok, wait = TokenBucket(rate=100, burst=1000).try_take(1001, now=0)
    assert not ok and wait == float("inf")


def test_refill_never_exceeds_burst():
    b = TokenBucket(rate=100, burst=1000)
    b.try_take(10, now=0)
    b.try_take(0, now=1000)
    assert b.level == 1000


def test_tokens_not_requests_decide_admission():
    lim = TenantLimiter(rpm=600, tpm=6000)   # 10 req/s, 100 tok/s, burst 1000 tok
    assert lim.admit(100, 100, now=0)[0]     # 200 tokens, many request slots left
    big = lim.admit(500, 500, now=0)         # 1000 tokens, only 800 left
    assert not big[0] and big[1] > 0


def test_rejected_call_does_not_burn_request_slot():
    lim = TenantLimiter(rpm=60, tpm=600)     # request burst 10, token burst 100
    before = lim.rps_bucket.level
    assert not lim.admit(90, 90, now=0)[0]   # 180 > 100 burst
    assert lim.rps_bucket.level == before


def test_finish_refunds_unused_output_tokens():
    lim = TenantLimiter(rpm=600, tpm=6000)
    ok, _, reserved = lim.admit(100, 400, now=0)
    assert ok and reserved == 500
    lim.finish(reserved, prompt_tokens=100, generated=50, now=0)
    assert math.isclose(lim.tok_bucket.level, 1000 - 150)


def test_simulation_is_deterministic():
    assert simulate("cache_bounded") == simulate("cache_bounded")


def test_cache_only_creates_hotspot_and_bounded_fixes_it():
    rr, co, cb = (simulate(p) for p in ("round_robin", "cache_only", "cache_bounded"))
    assert co["hit_rate"] > rr["hit_rate"] + 0.3
    assert co["max_over_mean_load"] > 3.0
    assert cb["max_over_mean_load"] < co["max_over_mean_load"]
    assert cb["p99_s"] < co["p99_s"] / 3
    assert cb["hit_rate"] > rr["hit_rate"] + 0.3
