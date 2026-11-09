import pytest
from c14_rollout_sim import (Metrics, Gates, decide, rolling_update, blue_green_gpus,
                             canary_replicas, cold_start)
from c14_endpoint_lifecycle import EndpointSpec, validate, next_state, max_gpus

BASE = Metrics(5000, 0.8, 0.04, 0.001, 0.05, 0.90, 4000)


def m(**kw):
    d = BASE.__dict__.copy()
    d.update(kw)
    return Metrics(**d)


def test_promote_when_equal():
    assert decide(BASE, m()).action == "promote"


def test_hold_on_low_traffic():
    assert decide(BASE, m(requests=50)).action == "hold"


def test_hold_on_mild_latency():
    assert decide(BASE, m(ttft_p99_s=1.1)).action == "hold"


def test_rollback_on_big_latency():
    assert decide(BASE, m(ttft_p99_s=1.6)).action == "rollback"


def test_rollback_on_quality_even_with_few_requests():
    assert decide(BASE, m(requests=10, quality=0.80)).action == "rollback"


def test_rollback_on_length_drift():
    assert decide(BASE, m(length_share=0.30)).action == "rollback"


def test_rollback_on_zero_tokens():
    assert decide(BASE, m(tokens_per_s=0)).action == "rollback"


def test_rollback_on_hard_error_rate():
    assert decide(BASE, m(error_rate=0.05)).action == "rollback"


def test_small_error_delta_holds():
    assert decide(BASE, m(error_rate=0.008)).action == "hold"


def test_rolling_with_spare_gpu_keeps_full_capacity():
    r = rolling_update(8, 1, 0, 1, load_ticks=4)
    assert r["done"] and r["min_available"] == 8 and r["peak_gpus"] == 9


def test_rolling_without_spare_gpu_stalls_when_unavailable_zero():
    r = rolling_update(8, 1, 0, 0, load_ticks=4, max_ticks=50)
    assert not r["done"]
    assert r["peak_gpus"] == 8


def test_rolling_without_spare_gpu_finishes_by_dropping_capacity():
    r = rolling_update(8, 0, 1, 0, load_ticks=4)
    assert r["done"] and r["min_available"] == 7 and r["peak_gpus"] == 8


def test_bigger_surge_is_faster():
    slow = rolling_update(8, 1, 0, 4, load_ticks=4)["ticks"]
    fast = rolling_update(8, 4, 0, 4, load_ticks=4)["ticks"]
    assert fast < slow


def test_invalid_zero_zero():
    with pytest.raises(ValueError):
        rolling_update(8, 0, 0, 1, 4)


def test_blue_green_doubles():
    assert blue_green_gpus(8) == 16


def test_canary_replicas_rounds_up():
    assert canary_replicas(8, 5) == 1
    assert canary_replicas(8, 50) == 4
    with pytest.raises(ValueError):
        canary_replicas(8, 0)


def test_cold_start_arithmetic():
    c = cold_start(140, 2, 14, 60, 30)
    assert c["download_s"] == 70 and c["load_s"] == 10 and c["total_s"] == 170


def test_lifecycle():
    s = next_state(None, "create")
    assert s == "disabled"
    s = next_state(s, "enable")
    assert s == "enabled"
    with pytest.raises(ValueError):
        next_state(s, "delete")
    assert next_state(next_state(s, "disable"), "delete") == "deleted"


def test_validate_and_gpu_budget():
    ok = EndpointSpec("m", "H100", 4, 1, 3, "eu")
    assert validate(ok) == [] and max_gpus(ok) == 16
    bad = EndpointSpec("m", "A10", 0, 5, 2, "mars")
    assert len(validate(bad)) == 4
