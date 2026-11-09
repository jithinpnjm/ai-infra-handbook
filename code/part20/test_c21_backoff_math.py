import math

from c21_backoff_math import (expected_attempts, layered_attempts, budget_amplification_cap,
                              backoff_ceiling, full_jitter_mean, herd_peak, hedge_effect)


def test_expected_attempts_values_in_chapter():
    assert math.isclose(expected_attempts(0.5, 4), 1.875)
    assert math.isclose(expected_attempts(0.8, 4), 2.952)
    assert expected_attempts(0.0, 4) == 1.0
    assert expected_attempts(1.0, 4) == 4.0


def test_layers_multiply():
    assert layered_attempts(4, 3) == 64
    assert layered_attempts(3, 5) == 243
    assert layered_attempts(4, 5) == 1024


def test_budget_caps_amplification():
    assert budget_amplification_cap(0.1) == 1.1


def test_backoff_doubles_then_caps():
    assert [backoff_ceiling(n, 0.1, 0.5) for n in (1, 2, 3, 4)] == [0.1, 0.2, 0.4, 0.5]
    assert full_jitter_mean(3, 0.1, 5) == 0.2


def test_jitter_spreads_a_herd():
    assert herd_peak(1000, "none") == 1000
    assert herd_peak(1000, "full") < 300


def test_hedging_trades_load_for_tail():
    r = hedge_effect(0.95, n=40_000)
    assert 0.03 < r["duplicated_share"] < 0.07
    assert r["p99_after"] < r["p99_before"]
