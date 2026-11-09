import math

import pytest

import c10_fanout_sim as f


def test_percentile_nearest_rank():
    assert f.percentile([1, 2, 3, 4], 0.5) == 2
    assert f.percentile([1, 2, 3, 4], 1.0) == 4
    with pytest.raises(ValueError):
        f.percentile([], 0.5)


def test_single_call_matches_closed_form():
    _, p99 = f.simulate(1, requests=40_000)
    assert p99 == pytest.approx(f.single_call_p99(), rel=0.1)


def test_request_p99_grows_with_fanout():
    p99s = [f.simulate(n, requests=5_000)[1] for n in (1, 10, 100)]
    assert p99s == sorted(p99s)
    assert p99s[2] > 1.5 * p99s[0]


def test_median_also_grows():
    # the median of a fan-out request is already above one call's median
    assert f.simulate(100, requests=3_000)[0] > f.simulate(1, requests=3_000)[0]


def test_seed_makes_runs_repeatable():
    assert f.simulate(5, requests=500, seed=7) == f.simulate(5, requests=500, seed=7)
