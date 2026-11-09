import math

import c17_estimates as e


def test_kv_and_decode_ceiling_match_chapter_12():
    assert e.KV_BYTES_PER_TOKEN == 147_456
    assert round(e.decode_ceiling(64)) == 5361


def test_p01_scheduler():
    r = e.p01_scheduler()
    assert r["nodes"] == 512 and round(r["fail_per_day"], 2) == 1.97
    assert round(r["job_mtbi_h"], 1) == 97.7
    assert round(r["ckpt_interval_min"]) == 153
    assert round(r["lost_min_per_failure"], 1) == 86.5
    assert round(r["overhead_pct"], 1) == 2.8
    assert [round(x) for x in r["fair_gpus"]] == [2048, 1229, 819]
    assert (r["jobs_fit_fragmented"], r["jobs_fit_clean"]) == (3, 4)


def test_p02_serving():
    r = e.p02_serving()
    assert r["demand_tok_s"] == 90_000
    assert round(r["per_gpu_tok_s"]) == 3217
    assert (r["gpus"], r["gpus_n_plus_1"], r["burst_gpus"]) == (28, 29, 84)


def test_p03_storage():
    r = e.p03_training_storage()
    assert round(r["read_gb_s"], 1) == 204.8 and r["ckpt_gb"] == 980
    assert round(r["write_gb_s"], 2) == 16.33 and round(r["avg_write_gb_s"], 2) == 0.54
    assert round(r["kept_tb"], 1) == 4.9
    assert (round(r["all_hot_usd"]), round(r["tiered_usd"])) == (200_000, 56_000)


def test_p04_detection():
    r = e.p04_gpu_detection()
    assert r["gpus"] == 16_000 and round(r["failures_per_day"], 2) == 2.19
    assert r["series"] == 640_000 and round(r["samples_s"]) == 42_667
    assert r["requests_saved_per_event"] == 1560


def test_p05_sre():
    r = e.p05_sre()
    assert round(r["budget_min"], 1) == 43.2
    assert [round(r[k], 1) for k in ("budget_pct_14_4_for_1h", "budget_pct_6_for_6h",
                                     "budget_pct_1_for_72h")] == [2.0, 5.0, 10.0]
    assert round(r["demand_in_lead"], 1) == 403.1
    assert (r["gpus_needed"], r["gpus_to_order"]) == (484, 84)


def test_p06_failover():
    r = e.p06_failover()
    assert r["gpus"] == 16 and r["active_usd"] == 35_040 and r["warm_usd"] == 8_760
    assert (r["cold_outage_min"], r["warm_outage_min"]) == (25, 10)
    assert round(r["cold_budget_pct"], 1) == 57.9 and round(r["warm_budget_pct"], 1) == 23.1


def test_p07_metering():
    r = e.p07_metering()
    assert r["events_day"] == 86_400_000 and round(r["gb_day"], 2) == 17.28
    assert round(r["dedupe_gb"], 2) == 1.38
    assert round(r["revenue_day"], 2) == 17_280
    assert round(r["loss_usd_day"], 2) == 17.28 and round(r["overbill_usd_day"], 1) == 345.6


def test_p08_cache_tier():
    r = e.p08_cache_tier()
    assert round(r["prefix_gb"], 3) == 0.295 and round(r["hot_set_tb"], 3) == 1.475
    assert (r["hbm_fit"], r["dram_fit"], r["nvme_fit"]) == (171, 1736, 27126)
    assert round(r["recompute_ms"]) == 82
    assert round(r["dram_load_ms"], 1) == 4.6 and round(r["nvme_load_ms"]) == 42


def test_p09_weights():
    r = e.p09_weights()
    assert r["naive_s"] == 700 and r["seed_s"] == 70 and r["rack_rounds"] == 4
    assert round(r["tree_s"]) == 163 and r["gpu_load_s"] == 10


def test_p10_rate_limiter():
    r = e.p10_rate_limiter()
    assert round(r["refill_tok_s"]) == 1667 and r["reserve"] == 1824
    assert (r["burst_reqs_reserve"], r["burst_reqs_actual"], r["refund_per_req"]) == (54, 90, 724)
    assert r["state_mb"] == 16 and r["store_ops_s"] == 4000


def test_p11_noisy_neighbour():
    r = e.p11_noisy_neighbour()
    assert round(r["long_gb"], 2) == 4.42 and round(r["normal_gb"], 2) == 0.37
    assert (r["normal_alone"], r["long_fill"], r["normal_while_long"], r["capped_long"]) == (137, 11, 5, 2)


def test_p12_slo_platform():
    r = e.p12_slo_platform()
    assert r["raw_series"] == 468_000 and r["slos"] == 4000
    assert r["recorded"] == 20_000 and r["alert_rules"] == 12_000
    assert math.isclose(r["evals_s"], 200)


def test_all_run():
    assert all(fn() for fn in e.ALL) and len(e.ALL) == 12
