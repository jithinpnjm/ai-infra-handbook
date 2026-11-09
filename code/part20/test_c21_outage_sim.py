import pytest

from c21_outage_sim import Config, POLICIES, Policy, SCENARIOS, backoff_delay, simulate
import random


def by_name(name):
    return next(p for p in POLICIES if p.name == name)


def test_backoff_kinds():
    rng = random.Random(0)
    assert backoff_delay("none", 3, 0.2, 3, rng) == 0.0
    assert backoff_delay("exp", 3, 0.2, 3, rng) == 0.8
    assert backoff_delay("exp", 10, 0.2, 3, rng) == 3
    assert 0 <= backoff_delay("full", 3, 0.2, 3, rng) <= 0.8
    with pytest.raises(ValueError):
        backoff_delay("zigzag", 1, 0.2, 3, rng)


def test_runs_repeat():
    cfg = SCENARIOS["short queue (rejects fast)"]
    assert simulate(by_name("full_jitter_4"), cfg) == simulate(by_name("full_jitter_4"), cfg)


def test_healthy_period_has_no_amplification_for_any_policy():
    cfg = SCENARIOS["short queue (rejects fast)"]
    for p in POLICIES:
        assert simulate(p, cfg)["before"]["amplification"] < 1.05


def test_budget_caps_amplification_in_the_outage():
    cfg = SCENARIOS["short queue (rejects fast)"]
    naive = simulate(by_name("naive_4_immediate"), cfg)
    budget = simulate(by_name("full_jitter_4_budget10"), cfg)
    assert budget["during"]["amplification"] <= 1.15
    assert naive["during"]["amplification"] > 1.5
    assert budget["peak_attempts_per_s"] < naive["peak_attempts_per_s"]


def test_deep_queue_retry_storm_outlives_the_outage():
    cfg = SCENARIOS["deep queue (waits pass the timeout)"]
    naive = simulate(by_name("naive_4_immediate"), cfg)
    jit = simulate(by_name("full_jitter_4"), cfg)
    budget = simulate(by_name("full_jitter_4_budget10"), cfg)
    assert naive["after"]["success_rate"] < 0.2       # still failing after recovery
    assert jit["after"]["success_rate"] < 0.2         # jitter alone does not save it
    assert budget["after"]["success_rate"] > 0.9      # the budget does
    assert naive["wasted_completions"] > 10 * budget["wasted_completions"]


def test_no_outage_means_no_retries_needed():
    cfg = Config(failed=0, rate=30)
    r = simulate(Policy("p", 4, "full"), cfg)
    assert r["during"]["amplification"] < 1.02
