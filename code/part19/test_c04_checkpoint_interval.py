import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import c04_checkpoint_interval as ci  # noqa: E402


def test_young_matches_hand_calculation():
    # 2 * 180 * 28800 = 10,368,000 ; sqrt = 3219.94...
    assert ci.young(180, 28800) == pytest.approx(3219.94, abs=0.01)


def test_daly_subtracts_cost():
    assert ci.daly(180, 28800) == pytest.approx(3219.94 - 180, abs=0.01)


def test_daly_falls_back_to_mtbf_when_cost_is_large():
    assert ci.daly(cost=600, mtbf=1000) == 1000  # cost >= M/2


def test_cluster_mtbf_scales_inversely_with_nodes():
    node = 50_000 * 3600.0
    assert ci.cluster_mtbf(node, 100) == pytest.approx(node / 100)
    with pytest.raises(ValueError):
        ci.cluster_mtbf(node, 0)


def test_write_seconds():
    assert ci.write_seconds(1200, 10) == 120


@pytest.mark.parametrize("cost,mtbf", [(60, 8 * 3600), (180, 8 * 3600), (30, 24 * 3600)])
def test_closed_forms_are_close_to_numeric_minimum(cost, mtbf):
    r = ci.report(cost, mtbf)
    # The first-order formulas land within 2 percent of the numeric optimum
    # and the waste at the formula is within 0.1 percentage points of the minimum.
    assert r["daly_s"] == pytest.approx(r["numeric_opt_s"], rel=0.02)
    assert r["waste_at_daly"] - r["waste_at_numeric"] < 0.001


def test_waste_has_an_interior_minimum_and_both_extremes_are_worse():
    r = ci.report(180, 8 * 3600)
    assert r["waste_at_numeric"] < r["waste_every_5min"]
    assert r["waste_at_numeric"] < r["waste_every_4h"]


def test_restart_cost_raises_waste_but_barely_moves_the_optimum():
    base = ci.report(180, 8 * 3600)
    slow = ci.report(180, 8 * 3600, downtime=0, restart=900)
    assert slow["waste_at_numeric"] > base["waste_at_numeric"]
    assert slow["numeric_opt_s"] == pytest.approx(base["numeric_opt_s"], rel=0.02)


def test_asynchronous_write_shrinks_interval_and_waste():
    sync = ci.report(180, 8 * 3600)
    asyn = ci.report(2, 8 * 3600)
    assert asyn["daly_s"] < sync["daly_s"]
    assert asyn["waste_at_numeric"] < sync["waste_at_numeric"]


def test_cli_prints_a_report(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["x", "--mtbf-hours", "8", "--cost-seconds", "180"])
    ci.main()
    out = capsys.readouterr().out
    assert "daly_s" in out and "3039.9" in out


# ---- numbers quoted in chapter 19.4 ------------------------------------
GPU_HOURS_PER_INTERRUPTION = 54 * 24 * 16384 / 419  # Llama 3 405B run: 419 interruptions, 54 days, 16,384 GPUs


def job_mtbf_s(gpus):
    return GPU_HOURS_PER_INTERRUPTION / gpus * 3600


def test_chapter_mtbf_values():
    assert job_mtbf_s(16384) / 3600 == pytest.approx(3.09, abs=0.01)
    assert job_mtbf_s(1024) / 3600 == pytest.approx(49.5, abs=0.1)
    assert job_mtbf_s(32) / 3600 == pytest.approx(1583.7, abs=0.1)


@pytest.mark.parametrize("gpus,cost,daly_s,waste_pct", [
    (32, 22.5, 15995, 0.29),
    (1024, 22.5, 2809, 1.92),
    (16384, 22.5, 685, 11.47),
    (16384, 2.0, 209, 7.22),
])
def test_chapter_interval_table(gpus, cost, daly_s, waste_pct):
    r = ci.report(cost, job_mtbf_s(gpus), downtime=0, restart=600)
    assert r["daly_s"] == pytest.approx(daly_s, abs=1)
    assert 100 * r["waste_at_daly"] == pytest.approx(waste_pct, abs=0.01)


def test_handbook_14_11_example_is_reproduced():
    # Chapter 14.11: M = 8 h, C = 180 s gives about 3,040 s
    assert ci.daly(180, 8 * 3600) == pytest.approx(3040, abs=1)


def test_checkpoint_size_and_write_time_for_the_reference_model():
    gb = 8.03 * 14  # 8.03B parameters at 14 bytes per parameter (chapter 14.11 accounting)
    assert gb == pytest.approx(112.4, abs=0.1)
    assert ci.write_seconds(gb, 5) == pytest.approx(22.5, abs=0.1)


def test_gpu_hours_per_interruption_is_about_50_700():
    assert GPU_HOURS_PER_INTERRUPTION == pytest.approx(50_700, abs=50)  # "50,700" in the chapter


def test_exercise_1_answer():
    # 256 GPUs, 400 GB at 10 GB/s -> 40 s, interruption every 20 h, 900 s restart
    r = ci.report(ci.write_seconds(400, 10), 20 * 3600, restart=900)
    assert r["daly_s"] == pytest.approx(2360, abs=1)  # "2,360 seconds" in the chapter
    assert 100 * r["waste_at_daly"] == pytest.approx(4.5, abs=0.1)
