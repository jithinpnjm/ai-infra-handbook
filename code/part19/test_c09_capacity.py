"""Tests for the chapter 19.9 capacity model. They prove the formulas, the
fixed-point sizing, the forecast band, the cost crossover and a failure case."""
import copy
import math

import pytest

import c09_capacity_model as m
import c09_scenario_runner as sr
import c09_sensitivity as sens
import c09_worked_example as we


@pytest.fixture
def doc():
    return sr.load()


def test_6nd_and_gpu_hours():
    assert m.train_flops(13e9, 2e12) == pytest.approx(1.56e23)
    h = m.gpu_hours_ideal(1.56e23, 989.5, 0.40)
    assert h == pytest.approx(109483, abs=1)


def test_mfu_book_example_round_trip():
    # Distributed AI Systems ch. 2: 860 TFLOP per iteration, 2.0 s, 989 TFLOPS peak, MFU about 43 percent.
    seconds = m.gpu_hours_ideal(860e12, 989, 430 / 989) * 3600
    assert seconds == pytest.approx(2.0, rel=1e-9)


def test_checkpoint_seconds_by_hand():
    assert m.checkpoint_seconds(13e9, 6, 20) == pytest.approx(3.9)


def test_young_interval_is_near_the_minimum_of_inflation():
    c, mtbf, restart = 120.0, 36000.0, 600.0
    best = m.young_interval_seconds(c, mtbf)
    grid = [best * f for f in (0.25, 0.5, 1.0, 2.0, 4.0)]
    vals = [m.inflation(c, t, restart, mtbf) for t in grid]
    assert vals[2] == min(vals)


def test_slow_storage_raises_inflation_and_gpus():
    args = dict(params=13e9, tokens=2e12, deadline_h=1080, peak_tflops=989.5, mfu=0.4,
                ckpt_bytes_per_param=6, interval_s=3600, restart_s=900, gpu_mtbf_h=30000)
    fast = m.size_training(write_gb_per_s=20, **args)
    slow = m.size_training(write_gb_per_s=0.05, **args)
    assert slow["inflation"] > fast["inflation"] > 1.0
    assert slow["gpus"] > fast["gpus"]


def test_size_training_is_a_fixed_point_and_whole_nodes():
    t = m.size_training(13e9, 2e12, 1080, 989.5, 0.4, 6, 20, 3600, 900, 30000)
    assert t["gpus"] % 8 == 0
    assert t["wall_clock_h"] <= 1080
    assert (t["gpus"] - 8) * 1080 < t["effective_gpu_hours"]  # one node fewer would miss the deadline


def test_forecast_band_exact_exponential_has_no_width():
    b = m.forecast_band([10, 20, 40], 1)
    assert b["p50"] == pytest.approx(80)
    assert b["p10"] == pytest.approx(b["p90"])


def test_forecast_band_widens_with_horizon_and_noise():
    hist = [20, 22, 23, 26, 27, 31, 32, 36, 40]
    near, far = m.forecast_band(hist, 1), m.forecast_band(hist, 12)
    assert far["p90"] / far["p50"] > near["p90"] / near["p50"] > 1.0
    assert far["p10"] < far["p50"] < far["p90"]


def test_inference_matches_chapter_20_12():
    cfg = {"model": "qwen3-8b", "in_tokens": 2000, "out_tokens": 500, "batch": 64, "mfu": 0.4}
    rate, _lat, _tpot = m.inference_replica_rate(cfg, "h100")
    assert rate == pytest.approx(5.68, abs=0.005)
    assert m.inference_gpus(40, rate, 0.9, 1) == 9  # 20.12: 8 for headroom plus 1 spare


def test_spares_agree_with_chapter_20_16():
    assert m.sp.spares_needed(512, 0.10, 72) == 3
    assert m.sp.spares_needed(512, 0.10, 336) == 7


def test_notebooks_and_finetune_arithmetic():
    assert m.notebook_gpus(60, 0.3, 2) == 9
    avg = m.finetune_avg_gpus(10, 13e9, 1e10, 989.5, 0.4, 0.85)
    assert avg == pytest.approx(8.82, abs=0.01)


def test_cost_formulas_by_hand():
    assert m.reserved_price(5.0, 0.35) == pytest.approx(3.25)
    own = m.owned_cost_per_gpu_hour(40000, 4, 1.5)
    assert own == pytest.approx(2.6416, abs=1e-4)
    assert m.breakeven_utilisation(own, 5.0) == pytest.approx(0.5283, abs=1e-4)
    assert m.spot_effective_price(1.5, 0.25) == pytest.approx(2.0)
    flat = [10.0, 10.0]
    assert m.annual_cost_with_commit(flat, 10, 5.0, 3.0) == pytest.approx(2 * 10 * 3.0 * 730)


def test_commit_follows_the_load_shape():
    flat = [100.0] * 12
    assert m.best_commit(flat, 5.0, 3.25)[0] == 100
    spiky = [100.0] + [10.0] * 11
    c, _ = m.best_commit(spiky, 5.0, 3.25)
    assert c == 10  # committing to the spike would pay for idle GPUs 11 months out of 12
    assert m.best_commit(spiky, 3.0, 3.25)[0] == 0  # no discount, no reason to commit


def test_monte_carlo_is_seeded_and_ordered(doc):
    a = m.monte_carlo(doc["base"], 200, 19)
    b = m.monte_carlo(doc["base"], 200, 19)
    assert a == b
    assert a["pool"][0] <= a["pool"][1] <= a["pool"][2]
    assert a["cost"][0] < a["cost"][2]


def test_scenarios_move_the_right_way(doc):
    rows = sr.run_all(doc)
    assert rows["bigger_training_run"]["training_gpus"] > rows["base"]["training_gpus"]
    assert rows["demand_surge"]["inference_gpus_end"] > rows["base"]["inference_gpus_end"]
    assert rows["slow_repair"]["pool_gpus"] > rows["base"]["pool_gpus"]
    assert rows["price_shock"]["best_cost"] > rows["base"]["best_cost"]
    assert rows["base"]["best_strategy"] == "owned mix"
    assert rows["pricey_hardware"]["best_strategy"] == "reserved mix"


def test_unknown_override_path_fails_loudly(doc):
    with pytest.raises(KeyError):
        sr.apply_overrides(doc["base"], {"training.no_such_field.x": 1})


def test_base_assumptions_are_not_mutated(doc):
    before = copy.deepcopy(doc["base"])
    sr.run_all(doc)
    sens.sensitivity(doc)
    assert doc["base"] == before


def test_sensitivity_is_sorted_and_batch_util_leads(doc):
    _b, rows = sens.sensitivity(doc)
    swings = [r["cost_swing"] for r in rows]
    assert swings == sorted(swings, reverse=True)
    assert rows[0]["param"] == "batch_util"


def test_lead_time_months():
    assert m.horizon_months(1) == 1
    assert m.horizon_months(120) == 4
    assert m.horizon_months(31) == 2


def test_worked_example_prints_the_chapter_numbers(capsys):
    we.main()
    out = capsys.readouterr().out
    for needle in ("109,483", "104 (13 nodes)", "pool 176 GPUs", "3,285,036", "52.8%",
                   "168 / 192 / 224", "116.2"):
        assert needle in out
    assert math.isfinite(m.Z80)
