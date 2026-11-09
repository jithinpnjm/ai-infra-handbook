# code/part20/test_sim_and_calc.py
import pytest

from herd_load_calc import load_seconds, weights_gb
from kv_pressure_sim import simulate


def test_book_capacity_numbers():
    assert simulate(n_req=1)["capacity_tokens"] == 20480  # 10 GB / 0.5 MB per token
    assert simulate(n_req=1, free_gb=34)["capacity_tokens"] == 69632


def test_overload_preempts_and_slows_everyone():
    tight, roomy = simulate(), simulate(free_gb=34)
    assert tight["preemptions"] > 0 and tight["recomputed_tokens"] > 0
    assert roomy["preemptions"] == 0
    assert tight["steps"] > 2 * roomy["steps"]
    assert tight["finished"] == roomy["finished"] == 16


def test_no_preemption_when_load_fits():
    r = simulate(n_req=4)
    assert r["preemptions"] == 0 and r["peak_kv_usage"] < 1


def test_load_time_scales_with_replicas():
    assert weights_gb(70, 2) == 140
    assert load_seconds(70, 2, 1, 14) == pytest.approx(10)
    assert load_seconds(70, 2, 8, 14) == pytest.approx(80)
    with pytest.raises(ValueError):
        load_seconds(70, 2, 0, 14)
