import math

import pytest

import c10_latency_math as m


def test_reads_per_round_trip():
    assert m.reads_per_round_trip() == 5000


def test_table_is_ordered_by_cost():
    values = list(m.DEAN_2009_NS.values())
    assert values == sorted(values)


def test_failures_and_downtime():
    assert m.failures_in(1_000_000, 0.999) == pytest.approx(1000)
    assert m.downtime_seconds(86400, 0.999) == pytest.approx(86.4)
    with pytest.raises(ValueError):
        m.failures_in(10, 1.5)


def test_fanout_probability():
    assert m.prob_any_slow(0.01, 1) == pytest.approx(0.01)
    assert m.prob_any_slow(0.01, 100) == pytest.approx(0.634, abs=0.001)
    # more calls never makes the chance smaller
    chances = [m.prob_any_slow(0.01, n) for n in (1, 10, 100, 1000)]
    assert chances == sorted(chances)


def test_per_call_quantile_needed():
    q = m.per_call_percentile_needed(0.99, 100)
    assert q ** 100 == pytest.approx(0.99)
    assert q > 0.9998


def test_loop_budget():
    assert m.loop_seconds(10_000_000, 100) == pytest.approx(1.0)
    assert m.items_per_second_budget(100) == pytest.approx(10_000_000)


def test_md1_response_grows_and_matches_hand_values():
    assert m.md1_response(1.0, 0.0) == 1.0
    assert m.md1_response(1.0, 0.6) == pytest.approx(1.75)
    assert m.md1_response(1.0, 0.8) == pytest.approx(3.0)
    rs = [m.md1_response(1.0, u) for u in (0.1, 0.5, 0.9, 0.99)]
    assert rs == sorted(rs)
    with pytest.raises(ValueError):
        m.md1_response(1.0, 1.0)
