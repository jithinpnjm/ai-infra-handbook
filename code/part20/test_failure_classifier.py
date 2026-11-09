# code/part20/test_failure_classifier.py
import json
import pathlib

import pytest

from classify_failures import main
from failure_model import Readings, rank
from failure_rules import RULES

HERE = pathlib.Path(__file__).parent


def top(current, baseline=None):
    found = rank(RULES, current, baseline)
    return found[0].cause if found else None


def causes(current, baseline=None):
    return [h.cause for h in rank(RULES, current, baseline)]


def test_kv_exhaustion_beats_queue_growth():
    data = json.load(open(HERE / "samples/kv_exhaustion.json"))
    assert top(data["current"], data["baseline"]) == "kv_cache_exhaustion_preemption"


def test_queue_growth_when_kv_has_room():
    cur = {"vllm:num_requests_waiting": 60, "vllm:num_requests_running": 128,
           "sig:max_num_seqs": 128, "vllm:kv_cache_usage_perc": 0.6,
           "vllm:generation_tokens@rate": 2000,
           "vllm:request_queue_time_seconds@p99": 9.0}
    base = {"vllm:request_queue_time_seconds@p99": 0.5}
    assert top(cur, base) == "queue_growth_capacity_saturated"
    assert "kv_cache_exhaustion_preemption" not in causes(cur, base)


def test_long_context_head_of_line_blocking():
    cur = {"vllm:request_prompt_tokens@p50": 500, "vllm:request_prompt_tokens@p99": 60000,
           "vllm:inter_token_latency_seconds@p99": 0.5, "vllm:kv_cache_usage_perc": 0.7,
           "vllm:num_preemptions@rate": 0.0}
    base = {"vllm:inter_token_latency_seconds@p99": 0.05}
    assert top(cur, base) == "long_context_head_of_line_blocking"


def test_engine_hang_with_healthy_endpoint():
    cur = {"vllm:num_requests_running": 20, "vllm:num_requests_waiting": 50,
           "vllm:generation_tokens@rate": 0, "sig:nccl_error_in_log": True,
           "sig:health_http_status": 200}
    h = rank(RULES, cur)[0]
    assert h.cause == "engine_hang_no_progress"
    assert "/health still returns 200" in h.evidence


def test_idle_engine_is_not_a_hang():
    cur = {"vllm:num_requests_running": 0, "vllm:num_requests_waiting": 0,
           "vllm:generation_tokens@rate": 0}
    assert "engine_hang_no_progress" not in causes(cur)


def test_liveness_kill_and_pool_shrink_are_both_reported():
    data = json.load(open(HERE / "samples/liveness_kill.json"))
    found = causes(data["current"], data["baseline"])
    assert found[:2] == ["liveness_probe_kills_busy_worker", "silent_pool_shrink"]


def test_real_hang_is_not_blamed_on_liveness_probe():
    cur = {"sig:restart_reason": "liveness", "vllm:generation_tokens@rate": 0,
           "sig:nccl_error_in_log": True, "sig:xid_codes": [74]}
    first = causes(cur)
    assert first[0] != "liveness_probe_kills_busy_worker" or len(first) > 1
    h = [h for h in rank(RULES, cur) if h.cause == "liveness_probe_kills_busy_worker"][0]
    assert h.score < 0.6


def test_startup_vs_runtime_oom():
    assert top({"sig:oom_phase": "startup"}) == "oom_at_startup"
    assert top({"sig:oom_phase": "runtime"}) == "oom_at_runtime"


def test_xid_fault():
    assert top({"sig:xid_codes": [79], "vllm:generation_tokens@rate": 0}) == "gpu_xid_fault"


def test_thundering_herd_versus_slow_load():
    herd = {"sig:replicas_loading": 6, "sig:desired_replicas": 8,
            "sig:model_load_seconds": 900, "sig:ready_replicas": 2}
    base = {"sig:model_load_seconds": 200}
    assert top(herd, base) == "thundering_herd_on_restart"
    one = {"sig:replicas_loading": 1, "sig:desired_replicas": 8, "sig:model_load_seconds": 900}
    assert "thundering_herd_on_restart" not in causes(one)
    assert top(one) == "slow_weight_load_cold_start"


def test_finish_reason_drift_detected_from_shares():
    base = {"vllm:request_success@rate:stop": 90, "vllm:request_success@rate:length": 10}
    cur = {"vllm:request_success@rate:stop": 60, "vllm:request_success@rate:length": 40,
           "vllm:request_success@rate:repetition": 2}
    assert top(cur, base) == "quality_regression_finish_reason_drift"
    assert top(base, base) is None


def test_speculative_acceptance_low():
    cur = {"vllm:spec_decode_num_accepted_tokens@rate": 100,
           "vllm:spec_decode_num_draft_tokens@rate": 400,
           "vllm:inter_token_latency_seconds@p99": 0.09}
    assert top(cur, {"vllm:inter_token_latency_seconds@p99": 0.05}) == "speculative_decoding_low_acceptance"
    good = dict(cur, **{"vllm:spec_decode_num_accepted_tokens@rate": 300})
    assert "speculative_decoding_low_acceptance" not in causes(good)


def test_prefix_cache_collapse():
    cur = {"vllm:prefix_cache_hits@rate": 100, "vllm:prefix_cache_queries@rate": 1000,
           "vllm:time_to_first_token_seconds@p99": 4.0}
    base = {"vllm:prefix_cache_hits@rate": 600, "vllm:prefix_cache_queries@rate": 1000,
            "vllm:time_to_first_token_seconds@p99": 1.0}
    assert top(cur, base) == "prefix_cache_hit_collapse"


def test_retry_amplification_noisy_tenant_and_skew():
    retry = {"sig:attempts_per_unique_request": 3.0, "vllm:admission_rejections@rate": 5,
             "vllm:num_requests_waiting": 30}
    assert "retry_amplification" in causes(retry)
    assert top({"sig:top_tenant_token_share": 0.8, "vllm:num_requests_waiting": 30}) == "noisy_tenant"
    assert top({"sig:router_engine_version_skew": True}) == "version_skew_router_engine"


def test_missing_readings_are_reported_not_guessed():
    r = Readings({"vllm:num_requests_waiting": 50})
    found = rank(RULES, r.current)
    assert found and found[0].unknown
    assert rank(RULES, {}) == []


def test_ranking_is_stable_and_sorted():
    data = json.load(open(HERE / "samples/liveness_kill.json"))
    a = rank(RULES, data["current"])
    scores = [h.score for h in a]
    assert scores == sorted(scores, reverse=True)
    assert [h.cause for h in a] == [h.cause for h in rank(RULES, data["current"])]


@pytest.mark.parametrize("name", ["kv_exhaustion", "liveness_kill"])
def test_cli_prints_ranked_causes(name, capsys):
    assert main([str(HERE / f"samples/{name}.json")]) == 0
    out = capsys.readouterr().out
    assert out.startswith("1. ") and "now:" in out


def test_every_rule_has_actions_and_unique_cause():
    names = [r.cause for r in RULES]
    assert len(names) == len(set(names))
    for r in RULES:
        assert r.confirm and r.mitigate_now and r.fix_later and len(r.checks) >= 2
