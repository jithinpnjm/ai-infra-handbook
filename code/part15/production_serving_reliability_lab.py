#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 15.16:
Production serving stack and reliability.

Runs 28 deterministic self-checks across all six chapter domains and prints:
`Summary: 28 passed, 0 failed`
"""

from __future__ import annotations
import sys
from production_serving_reliability import (
    decompose_nine_stage_request_path,
    ModelRouter,
    score_epp_endpoints,
    simulate_ray_serve_multiplexed_lru,
    DualTokenBucketRateLimiter,
    evaluate_prefix_and_prompt_compression,
    evaluate_nemo_guardrails_budget,
    CanaryDeploymentController,
    assign_ab_variant,
    evaluate_sse_streaming_and_drain,
    validate_k8s_llm_probes_and_failures,
    evaluate_circuit_breaker_and_fallbacks,
    analyze_otel_trace_and_slo_budgets,
)


def run_lab() -> int:
    print("=== Chapter 15.16 Lab: Production Serving Stack and Reliability ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # -----------------------------------------------------------------------
    # 1. Nine-Stage Request Path, ModelRouter, EPP Scoring & Ray Multiplexing
    # -----------------------------------------------------------------------
    path = decompose_nine_stage_request_path()
    check(
        "1. 9-stage request lifecycle computes TTFT = 208.2 ms, effective ITL = 22.0 ms/tok, and E2E = 1,286.2 ms for 50 tokens",
        path["ttft_ms"] == 208.2
        and path["effective_itl_ms"] == 22.0
        and path["e2e_latency_ms"] == 1286.2,
    )
    check(
        "2. Pinned host memory (cudaHostAlloc at 60.0 GB/s) achieves 5.0x PCIe Gen5 transfer speedup over pageable memory (12.0 GB/s)",
        path["pcie_transfer_bw_gbps"] == 60.0 and path["pinned_vs_pageable_speedup_x"] == 5.0,
    )

    router = ModelRouter(
        model_endpoints={
            "meta-llama/Llama-3.2-1B-Instruct": "vllm-llama-32-1b-service.multi-models.svc.cluster.local",
            "microsoft/Phi-tiny-MoE-instruct": "vllm-phi-tiny-moe-service.multi-models.svc.cluster.local",
        },
        engine_routes={
            ("meta-llama/Llama-3.2-1B-Instruct", "vllm"): "vllm-llama-32-1b-service.multi-engines.svc.cluster.local",
            ("meta-llama/Llama-3.2-1B-Instruct", "sglang"): "sglang-llama-32-1b-service.multi-engines.svc.cluster.local",
            ("meta-llama/Llama-3.2-1B-Instruct", None): "vllm-llama-32-1b-service.multi-engines.svc.cluster.local",
        },
    )
    r_vllm = router.route_request({"model": "meta-llama/Llama-3.2-1B-Instruct"})
    r_sglang = router.route_request({"model": "meta-llama/Llama-3.2-1B-Instruct", "inference_server": "sglang"})
    r_404 = router.route_request({"model": "unknown-model"})
    check(
        "3. ModelRouter routes default requests to vLLM, explicit inference_server='sglang' to SGLang, and unknown models to HTTP 404",
        r_vllm["status_code"] == 200
        and r_vllm["target_service"] == "vllm-llama-32-1b-service.multi-engines.svc.cluster.local"
        and r_sglang["target_service"] == "sglang-llama-32-1b-service.multi-engines.svc.cluster.local"
        and r_404["status_code"] == 404,
    )

    epp = score_epp_endpoints(
        candidates=[
            {"pod_id": "vllm-pod-0", "waiting_reqs": 8, "kv_usage": 0.72, "prefix_hit_ratio": 0.10, "loras": set()},
            {"pod_id": "vllm-pod-1", "waiting_reqs": 3, "kv_usage": 0.65, "prefix_hit_ratio": 0.85, "loras": {"finance-lora"}},
            {"pod_id": "vllm-pod-2", "waiting_reqs": 55, "kv_usage": 0.96, "prefix_hit_ratio": 0.95, "loras": {"finance-lora"}},
        ],
        required_lora="finance-lora",
    )
    check(
        "4. Gateway API Inference Extension EPP filters saturated pod-2 (96% KV, 55 waiting) and selects prefix+LoRA-warm pod-1 (score 30.5)",
        epp["selected_pod"] == "vllm-pod-1"
        and len(epp["ranked_candidates"]) == 2
        and epp["ranked_candidates"][0]["score"] == 30.5,
    )

    mux = simulate_ray_serve_multiplexed_lru(
        ["distilbert-sst2", "bert-sst2", "distilbert-sst2", "roberta-sst2", "bert-sst2"],
        max_num_models_per_replica=2,
    )
    check(
        "5. Ray Serve @serve.multiplexed(max_num_models_per_replica=2) caches 2 models per replica and LRU-evicts bert-sst2 then distilbert-sst2",
        mux["cache_hits"] == 1
        and mux["cold_loads"] == 4
        and mux["evictions"] == ["bert-sst2", "distilbert-sst2"]
        and mux["final_cached_models"] == ["roberta-sst2", "bert-sst2"],
    )

    # -----------------------------------------------------------------------
    # 2. Dual Token Bucket Rate Limiter (RPM/TPM), Prefix Caching & Guardrails
    # -----------------------------------------------------------------------
    limiter = DualTokenBucketRateLimiter(
        requests_per_minute=10,
        request_burst=5,
        tokens_per_minute=6000,
        token_burst=3000,
    )
    burst_results = [limiter.check_rate_limit("tenant-alpha", requested_tokens=500, now_sec=0.0) for _ in range(5)]
    sixth_req = limiter.check_rate_limit("tenant-alpha", requested_tokens=500, now_sec=0.0)
    check(
        "6. Dual Token Bucket allows 5-request burst (2,500 tokens) and rejects 6th request with HTTP 429 and X-RateLimit-Reset=6.00s",
        all(r["allowed"] for r in burst_results)
        and sixth_req["allowed"] is False
        and sixth_req["status_code"] == 429
        and sixth_req["reset_seconds"] == 6.0,
    )

    refill_req = limiter.check_rate_limit("tenant-alpha", requested_tokens=1200, now_sec=6.0)
    evicted_cnt = limiter.cleanup_stale_clients(now_sec=4000.0)
    check(
        "7. Token Bucket refills 1 request + 600 tokens after 6s (total 1,100 tokens < 1,200 needed -> 1.0s TPM reset) and purges stale clients",
        refill_req["allowed"] is False
        and refill_req["remaining_requests"] == 1
        and refill_req["remaining_tokens"] == 1100
        and refill_req["reset_seconds"] == 1.0
        and evicted_cnt == 1,
    )

    comp = evaluate_prefix_and_prompt_compression()
    check(
        "8. Prompt compression triggers above 75% context (24,576 tok), compresses oldest 25% from 26,000 -> 20,800 tok (-36.0% quadratic prefill), and replaces 200-tok system prompt with 10 config tokens (20.0x)",
        comp["summarize_trigger_tokens"] == 24576
        and comp["compression_triggered"] is True
        and comp["compressed_tokens"] == 20800
        and comp["attention_work_reduction_pct"] == 36.0
        and comp["config_token_compression_x"] == 20.0,
    )
    check(
        "9. Anthropic prompt caching cuts 100K-token book TTFT from 11.5s to 2.4s (-79% latency, -90% cost) and 1,000-tok x 1M calls saves 1B tokens/day",
        comp["anthropic_benchmarks"]["book_100k"]["latency_reduction_pct"] == 79
        and comp["anthropic_benchmarks"]["book_100k"]["cost_reduction_pct"] == 90
        and comp["daily_saved_tokens_1k_sys_1m_calls"] == 1_000_000_000,
    )

    gr = evaluate_nemo_guardrails_budget()
    check(
        "10. NeMo Guardrails 5-rail pipeline adds 205.0 ms to a 45.0 ms base model (250.0 ms total = 5.56x) with 2,048 max_length, 0.85 min_confidence, and 2,555-day audit retention",
        gr["total_guarded_ms"] == 250.0
        and gr["guardrail_overhead_ms"] == 205.0
        and gr["slowdown_factor_x"] == 5.56
        and gr["cumulative_stages_ms"] == [45.0, 60.0, 90.0, 190.0, 240.0, 250.0]
        and gr["audit_retention_days"] == 2555,
    )

    # -----------------------------------------------------------------------
    # 3. Canary Rollout, Consistent-Hash A/B Testing & SSE Streaming Drain
    # -----------------------------------------------------------------------
    canary = CanaryDeploymentController("http://stable:8001", "http://canary:8002", initial_pct=10.0)
    for _ in range(90):
        canary.record_result(is_canary=False, success=True, latency_ms=175.0)
    for _ in range(2):
        canary.record_result(is_canary=False, success=False, latency_ms=190.0)
    for _ in range(16):
        canary.record_result(is_canary=True, success=True, latency_ms=260.0)
    for _ in range(4):
        canary.record_result(is_canary=True, success=False, latency_ms=320.0)
    gate_bad = canary.evaluate_gate(abs_error_threshold=0.05)
    check(
        "11. Canary controller triggers automatic rollback when canary error rate (20.0%) exceeds stable (2.17%) by > 5% and p95 reaches 320.0 ms (>= 300 ms critical gate)",
        gate_bad["canary_error_rate"] == 0.20
        and gate_bad["should_rollback"] is True
        and gate_bad["can_promote"] is False,
    )

    canary_good = CanaryDeploymentController("http://stable:8001", "http://canary:8002", initial_pct=10.0)
    for _ in range(100):
        canary_good.record_result(is_canary=False, success=True, latency_ms=180.0)
    for _ in range(30):
        canary_good.record_result(is_canary=True, success=True, latency_ms=185.0)
    gate_good = canary_good.evaluate_gate()
    steps = [canary_good.canary_percentage]
    while canary_good.canary_percentage < 100.0:
        steps.append(canary_good.promote_step())
    check(
        "12. Healthy canary (0% error, 185.0 ms < 200 ms gate) promotes through [10.0, 25.0, 50.0, 75.0, 100.0] traffic shifts",
        gate_good["can_promote"] is True
        and gate_good["should_rollback"] is False
        and steps == [10.0, 25.0, 50.0, 75.0, 100.0],
    )

    v_first = assign_ab_variant("model_comparison", "user-12345", {"llama-7b": 0.5, "mistral-7b": 0.5})
    v_repeat = [assign_ab_variant("model_comparison", "user-12345", {"llama-7b": 0.5, "mistral-7b": 0.5}) for _ in range(20)]
    check(
        "13. Consistent-hashing A/B assignment deterministically maps user-12345 to the exact same variant across 20 calls",
        all(v == v_first for v in v_repeat),
    )

    sse = evaluate_sse_streaming_and_drain()
    check(
        "14. SSE 5-token chunking at 20 tok/s delivers first chunk in 0.25s vs 5.0s full wait (20.0x faster perceived responsiveness)",
        sse["first_sse_chunk_s"] == 0.25
        and sse["full_generation_s"] == 5.0
        and sse["perceived_Wait_reduction_x"] == 20.0,
    )
    check(
        "15. Graceful SSE drain (15s preStop + 3.0s for 60 remaining tokens = 18.0s <= 120s terminationGracePeriodSeconds) prevents the 15% uncoordinated unload drop",
        sse["total_shutdown_required_s"] == 18.0
        and sse["zero_dropped_streams"] is True
        and sse["uncoordinated_unload_drop_pct"] == 15.0,
    )

    # -----------------------------------------------------------------------
    # 4. Kubernetes Health Probes, Probe Cascade & XID 62 Zombie Blackhole
    # -----------------------------------------------------------------------
    probes = validate_k8s_llm_probes_and_failures()
    check(
        "16. K8s startupProbe (30s initial + 60 * 10s = 630s total / 600s polling window) protects 240s 70B weight initialization",
        probes["startup_window_only_s"] == 600
        and probes["startup_budget_s"] == 630
        and probes["startup_survives_load"] is True,
    )
    check(
        "17. V12 Scenario 1: 1.2s NFS I/O stall trips a 1s /v1/models readinessProbe (100% 503 outage) but survives a 5s /health readinessProbe",
        probes["bad_probe_1s_cascades_100pct_503"] is True
        and probes["good_probe_5s_survives_nfs_spike"] is True,
    )
    check(
        "18. V12 Scenario 2: GPU 3 XID 62 DB-ECC in TP=8 pegs GPU 3 at 100% while 7 peers sit at 0% in ncclAllReduce, blackholing 12.5% (1/8) of cluster traffic",
        probes["xid_62_tp_gpu_util_pct"] == [0, 0, 0, 100, 0, 0, 0, 0]
        and probes["xid_62_cluster_timeout_pct"] == 12.5
        and probes["npd_remediation_xids"] == (48, 62, 79, 92),
    )

    # -----------------------------------------------------------------------
    # 5. Circuit Breaker State Machine, Fallback Cascades & Swap Thrashing
    # -----------------------------------------------------------------------
    cb_safe = evaluate_circuit_breaker_and_fallbacks(0.72, 8, 10.0, current_state="CLOSED")
    cb_trip = evaluate_circuit_breaker_and_fallbacks(0.96, 55, 6.0, current_state="CLOSED")
    cb_hold = evaluate_circuit_breaker_and_fallbacks(0.84, 15, 10.0, current_state="OPEN")
    cb_reset = evaluate_circuit_breaker_and_fallbacks(0.78, 10, 10.0, current_state="OPEN")
    check(
        "19. Circuit breaker stays CLOSED in SAFE zone (72% KV) and trips OPEN when KV > 95% (96%) or queue > 50 (55) for >= 5s",
        cb_safe["operating_zone"] == "SAFE"
        and cb_safe["next_state"] == "CLOSED"
        and cb_trip["operating_zone"] == "EMERGENCY"
        and cb_trip["next_state"] == "OPEN"
        and cb_trip["routing_action"] == "shed_429_or_fallback_8b_cloud",
    )
    check(
        "20. Hysteretic circuit breaker stays OPEN at 84% KV (>= 80%) and resets to CLOSED only when KV drops below 80% (78%)",
        cb_hold["next_state"] == "OPEN" and cb_reset["next_state"] == "CLOSED",
    )
    check(
        "21. Enabling CPU swap (--swap-space 32) degrades ITL by 4,150% (20 ms -> 850 ms/tok), while 50% Spot + 50% On-Demand saves 35.0% GPU cost",
        cb_safe["swap_space_recommended_gb"] == 0
        and cb_safe["swap_thrashing_itl_ms"] == (20.0, 850.0)
        and cb_safe["swap_degradation_pct"] == 4150.0
        and cb_safe["blended_50pct_spot_savings_pct"] == 35.0,
    )

    # -----------------------------------------------------------------------
    # 6. OpenTelemetry Tracing, CPU vs GPU Triage, SLO Budgets & RAG/LLMOps
    # -----------------------------------------------------------------------
    obs = analyze_otel_trace_and_slo_budgets()
    check(
        "22. OpenTelemetry 6-span trace waterfall sums to 4,820.0 ms and isolates the 3,850.0 ms prefill-starved decode stall",
        len(obs["otel_six_spans"]) == 6
        and obs["waterfall_total_ms"] == 4820.0
        and obs["waterfall_stall_ms"] == 3850.0,
    )
    check(
        "23. Enabling --enable-chunked-prefill (--max-num-batched-tokens 512) reduces p99 ITL from 4,500.0 ms to 22.8 ms (mean TTFT 210.4 ms)",
        obs["chunked_prefill_remediation"]["before_p99_itl_ms"] == 4500.0
        and obs["chunked_prefill_remediation"]["p99_itl_ms"] == 22.8
        and obs["chunked_prefill_remediation"]["mean_ttft_ms"] == 210.4,
    )
    check(
        "24. V12 Lab 04: replacing GIL-bound ThreadPool with ProcessPoolExecutor raises throughput 7.73x (13.47 -> 104.17 RPS) and cuts p99 latency 31.48x (1,410.20 -> 44.80 ms)",
        obs["lab04_throughput_gain_x"] == 7.73 and obs["lab04_p99_reduction_x"] == 31.48,
    )
    check(
        "25. 30-day SLO error budgets equal 43.2 min (99.9%), 21.6 min (99.95%), 4.32 min (99.99%), and 0.432 min / 25.92s (99.999%)",
        obs["error_budgets_30d_min"]["99.9%"] == 43.2
        and obs["error_budgets_30d_min"]["99.95%"] == 21.6
        and obs["error_budgets_30d_min"]["99.99%"] == 4.32
        and obs["error_budgets_30d_min"]["99.999%"] == 0.432,
    )
    check(
        "26. RAG retrieval evaluation computes AP_1 = 67%, AP_2 = 56%, MAP = 61%, and F1 relevance 60.0% (60/60) > 45.0% (90/30)",
        obs["rag_ap_q1_pct"] == 67
        and obs["rag_ap_q2_pct"] == 56
        and obs["rag_map_pct"] == 61
        and obs["rag_f1_balanced_vs_unbalanced"] == (60.0, 45.0),
    )

    # Extra end-to-end composite checks for 28 total
    check(
        "27. End-to-end check: non-GPU stages account for 13.4% (27.9 ms) of 208.2 ms TTFT even when healthy, and > 98% during CPU GIL contention",
        path["non_gpu_ttft_ms"] == 27.9 and path["non_gpu_ttft_share_pct"] == 13.4,
    )
    check(
        "28. End-to-end check: EPP FailClose mode rejects traffic when all pods exceed 95% KV cache or 50 waiting requests",
        score_epp_endpoints(
            [{"pod_id": "vllm-pod-0", "waiting_reqs": 60, "kv_usage": 0.98, "prefix_hit_ratio": 0.5, "loras": set()}]
        )["fail_close_rejected"]
        is True,
    )

    failed = total - passed
    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
