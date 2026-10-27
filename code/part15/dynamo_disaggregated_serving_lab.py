#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.8: NVIDIA Dynamo, llm-d and disaggregated serving."""

from __future__ import annotations
import sys
from dynamo_disaggregated_serving import (
    DisaggClusterGoodputSpec,
    WorkerRoutingTelemetry,
    LLMDReplicaEndpoint,
    evaluate_colocated_vs_disagg_goodput,
    should_offload_prefill,
    compute_smart_router_latency_costs,
    evaluate_dynamo_planner_and_qos,
    evaluate_nixl_transfer_and_kv_hierarchy,
    compute_kv_layout_transpose_plan,
    simulate_llmd_epp_routing,
)


def run_lab() -> int:
    print("=== Chapter 15.8 Lab: NVIDIA Dynamo, llm-d and Disaggregated Serving Verification ===")
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

    # 1. DistServe Goodput Math, Dynamo NVL72 Benchmark & MLPerf v5.0 SLOs
    gp = evaluate_colocated_vs_disagg_goodput(DisaggClusterGoodputSpec())
    check(
        "1. Colocated 1-GPU goodput under P90 TTFT<=400 ms (3.0 RPS) and P90 TPOT<=40 ms (1.6 RPS) is bounded by min(3.0, 1.6) = 1.6 RPS/GPU",
        gp["colocated_goodput_per_gpu"] == 1.6
        and gp["colocated_ttft_rps"] == 3.0
        and gp["colocated_tpot_rps"] == 1.6,
    )
    check(
        "2. Disaggregated 2P1D (2 prefill GPUs at 5.6 RPS = 11.2 RPS, 1 decode GPU at 10.0 RPS) achieves min(11.2, 10.0) / 3 = 3.33 (3.3) RPS/GPU (2.08x gain)",
        gp["total_prefill_rps"] == 11.2
        and gp["total_decode_rps"] == 10.0
        and gp["total_disagg_goodput_rps"] == 10.0
        and gp["disagg_goodput_per_gpu_exact"] == 3.33
        and gp["disagg_goodput_per_gpu_reported"] == 3.3
        and gp["per_gpu_goodput_gain_x"] == 2.08,
    )
    check(
        "3. DistServe reports up to 7.4x goodput and 12.6x tighter SLOs; NVIDIA Dynamo achieves up to 30x throughput on 680B MoE across 72-GPU GB200 NVL72",
        gp["distserve_max_goodput_gain_x"] == 7.4
        and gp["distserve_tighter_slo_x"] == 12.6
        and gp["dynamo_680b_nvl72_throughput_gain_x"] == 30.0,
    )
    check(
        "4. MLPerf v5.0 p99 SLOs: Llama-2-70B targets 450 ms TTFT / 40 ms TPOT; Llama-3.1-405B targets 6000 ms (6 s) TTFT / 175 ms TPOT",
        gp["mlperf_v5_70b_ttft_slo_ms"] == 450.0
        and gp["mlperf_v5_70b_tpot_slo_ms"] == 40.0
        and gp["mlperf_v5_405b_ttft_slo_ms"] == 6000.0
        and gp["mlperf_v5_405b_tpot_slo_ms"] == 175.0,
    )
    check(
        "5. Single-stream 70B FP16 decode on H100 (140 GB / 3350 GB/s HBM3) requires 41.79 ms/token (~23.93 tok/s ceiling)",
        gp["h100_70b_weight_load_ms"] == 41.79 and gp["h100_70b_single_stream_tok_s"] == 23.93,
    )

    # 2. NVIDIA Dynamo Smart Router (`should_offload_prefill` & Composite `latency_cost`)
    r_long = should_offload_prefill(
        prompt_length=1024, prefix_cached_length=256, prefill_queue_size=4, decode_active_reqs=3
    )
    check(
        "6. Smart Router offloads prefill when effective prompt length (1024 - 256 = 768 >= 256) and prefill queue (4 < 10) has capacity (remote score = 1.0 > 0.5)",
        r_long["effective_prompt_length"] == 768
        and r_long["should_offload"] is True
        and r_long["remote_prefill_score"] == 1.0
        and r_long["yaml_policy_offload"] is True,
    )

    r_cached = should_offload_prefill(
        prompt_length=1024, prefix_cached_length=900, prefill_queue_size=3, decode_active_reqs=4
    )
    check(
        "7. Smart Router keeps prefill local on decode worker when prefix cache hit leaves eff_len = 124 (< 256) and decode active reqs = 4 (< 8)",
        r_cached["effective_prompt_length"] == 124
        and r_cached["should_offload"] is False
        and r_cached["remote_prefill_score"] == 0.3
        and r_cached["yaml_policy_offload"] is False,
    )

    r_sat = should_offload_prefill(
        prompt_length=2048, prefix_cached_length=0, prefill_queue_size=12, decode_active_reqs=2
    )
    check(
        "8. Smart Router sheds load back to local prefill when global prefill queue is saturated (12 >= 10)",
        r_sat["should_offload"] is False and r_sat["decision_reason"] == "keep_local_on_decode_worker",
    )

    r_busy_dec = should_offload_prefill(
        prompt_length=200, prefix_cached_length=100, prefill_queue_size=5, decode_active_reqs=9
    )
    check(
        "9. Smart Router offloads moderate prompt (eff_len = 100 >= 64) when local decode worker is busy (9 >= 8 active streams)",
        r_busy_dec["effective_prompt_length"] == 100
        and r_busy_dec["should_offload"] is True
        and r_busy_dec["decision_reason"] == "decode_busy_and_moderate_prefill",
    )

    # Composite Latency Cost (ASP Ch. 17 Table 17-3)
    w_cold = WorkerRoutingTelemetry(
        worker_id="worker-0-cold",
        occupancy_percent=1.0,
        active_reqs=2,
        cache_match_flag=False,
        mem_bw_percent=2.0,
        recent_prefix_flag=False,
    )
    w_warm = WorkerRoutingTelemetry(
        worker_id="worker-1-warm",
        occupancy_percent=2.0,
        active_reqs=3,
        cache_match_flag=True,
        mem_bw_percent=4.0,
        recent_prefix_flag=True,
    )
    costs = compute_smart_router_latency_costs([w_cold, w_warm])
    check(
        "10. Simple 2-term cost (0.7*occ + 0.3*reqs) picks worker-0-cold (1.3 vs 2.3), whereas 5-factor KV-aware composite cost (+3*occ + 1*reqs - 10*match + 0.5*bw - 1*recent) picks worker-1-warm (0.0 vs 6.0)",
        costs["workers"]["worker-0-cold"]["simple_cost"] == 1.3
        and costs["workers"]["worker-1-warm"]["simple_cost"] == 2.3
        and costs["selected_simple_worker"] == "worker-0-cold"
        and costs["workers"]["worker-0-cold"]["composite_cost"] == 6.0
        and costs["workers"]["worker-1-warm"]["composite_cost"] == 0.0
        and costs["selected_composite_worker"] == "worker-1-warm",
    )

    # 3. NVIDIA Dynamo GPU Planner Autoscaling, QoS Reservations & Early Rejection
    plan_up = evaluate_dynamo_planner_and_qos(
        prefill_replicas=4,
        prefill_queue_len=9,
        prefill_gpu_util_pct=85.0,
        decode_replicas=8,
        decode_queue_len=18,
        decode_kv_usage_pct=78.0,
        avg_prefill_ms_per_req=35.0,
        avg_decode_ms_per_req=20.0,
        ttft_slo_ms=500.0,
    )
    check(
        "11. Dynamo GPU Planner scales up prefill (4 -> 5 when queue=9 >= 8, util=85% >= 80%) and decode (8 -> 9 when queue=18 >= 16, kv=78% >= 75%)",
        plan_up["prefill_action"] == "scale_up"
        and plan_up["new_prefill_replicas"] == 5
        and plan_up["decode_action"] == "scale_up"
        and plan_up["new_decode_replicas"] == 9,
    )
    check(
        "12. QoSController estimates TTFT = 9*35 + 18*20 = 675.0 ms (> 500 ms SLO), rejecting low-priority requests while admitting high-priority traffic",
        plan_up["estimated_ttft_ms"] == 675.0
        and plan_up["admit_low_priority"] is False
        and plan_up["admit_high_priority"] is True,
    )

    plan_down = evaluate_dynamo_planner_and_qos(
        prefill_replicas=6,
        prefill_queue_len=1,
        prefill_gpu_util_pct=30.0,
        decode_replicas=10,
        decode_queue_len=2,
        decode_kv_usage_pct=25.0,
    )
    check(
        "13. Dynamo GPU Planner scales down prefill (6 -> 5 when queue<=2, util<=40%) and decode (10 -> 9 when queue<=4, kv<=30%) and admits low-priority at 75.0 ms TTFT",
        plan_down["prefill_action"] == "scale_down"
        and plan_down["new_prefill_replicas"] == 5
        and plan_down["decode_action"] == "scale_down"
        and plan_down["new_decode_replicas"] == 9
        and plan_down["estimated_ttft_ms"] == 75.0
        and plan_down["admit_low_priority"] is True,
    )
    check(
        "14. QoS tier reservations allocate 10% premium (priority=100, 2 workers), 30% standard (priority=50, 6 workers), and 60% free (priority=10, 12 workers) across 20 workers",
        plan_down["qos_reservations"]["premium"]["reserved_workers"] == 2
        and plan_down["qos_reservations"]["standard"]["reserved_workers"] == 6
        and plan_down["qos_reservations"]["free"]["shared_workers"] == 12,
    )

    # 4. NIXL (`NVIDIA Inference Xfer Library`) & Distributed KV Cache Manager Hierarchy
    nx = evaluate_nixl_transfer_and_kv_hierarchy()
    check(
        "15. NIXL 0.5.x VRAM_SEG test buffer is 1 MiB (1,048,576 B) and LMCache/NIXL pd_buffer_size is 1 GiB (1,073,741,824 B) on ports 7300/7400/7500 with UCX_RNDV_THRESH=16384",
        nx["nixl_test_buffer_bytes"] == 1048576
        and nx["lmcache_pd_buffer_bytes"] == 1073741824
        and (nx["pd_peer_init_port"], nx["pd_peer_alloc_port"], nx["pd_proxy_port"]) == (7300, 7400, 7500)
        and nx["ucx_rndv_thresh_bytes"] == 16384,
    )
    check(
        "16. Collating 7,500-token KV cache from 16-token blocks (469 WQEs, 20.0 ms) into 128-token slabs (59 WQEs, 8.0 ms) cuts RDMA transfer time by 2.5x",
        nx["uncollated_wqes"] == 469
        and nx["collated_wqes"] == 59
        and nx["uncollated_rdma_ms"] == 20.0
        and nx["collated_rdma_ms"] == 8.0
        and nx["collation_speedup_x"] == 2.5,
    )
    check(
        "17. At 16 RPS and 1.5 GB KV/req, aggregate transfer rate is 24.0 GB/s (~25 GB/s), fitting NVLink 4 (900 GB/s) and IB NDR RDMA (50 GB/s) but saturating non-RDMA PCIe/TCP (10 GB/s)",
        nx["aggregate_kv_bw_gb_s"] == 24.0
        and nx["fits_nvlink4"] is True
        and nx["fits_ib_ndr_rdma"] is True
        and nx["saturates_non_rdMA_tcp"] is True,
    )
    check(
        "18. 70B 80-layer 32-head MHA KV cache is 1,310,720 B/tok (~1.31 MB/tok, vs 327,680 B/tok GQA), totaling 327.7 GB (~328 GB) in FP16 and 163.8 GB in FP8 for 250,000 tokens",
        nx["mha_bytes_per_tok_fp16"] == 1310720
        and nx["gqa_bytes_per_tok_fp16"] == 327680
        and nx["kv_250k_fp16_gb"] == 327.7
        and nx["kv_250k_fp8_gb"] == 163.8,
    )
    check(
        "19. NIXL KV cache offloading to CPU DRAM yields 14x TTFT speedup on x86+H100 and an additional 2x on Grace Hopper GH200 (900 GB/s NVLink-C2C = 28x vs recompute)",
        nx["x86_h100_kv_offload_ttft_speedup_x"] == 14.0
        and nx["gh200_vs_x86_kv_offload_ttft_speedup_x"] == 2.0
        and nx["gh200_vs_recompute_ttft_speedup_x"] == 28.0,
    )
    check(
        "20. LMCache tiered offloading expands KV capacity 3x in CPU RAM and 50x on NVMe SSD, lifting 5-concurrency throughput 16x from 4,700 tok/s to 75,200 tok/s",
        nx["lmcache_cpu_capacity_multiplier_x"] == 3.0
        and nx["lmcache_ssd_capacity_multiplier_x"] == 50.0
        and nx["lmcache_throughput_gain_x"] == 16.0
        and nx["vllm_baseline_throughput_tok_s"] == 4700.0
        and nx["lmcache_offload_throughput_tok_s"] == 75200.0,
    )
    check(
        "21. Heterogeneous & adaptive benchmarks: Splitwise 4xH100+4xA100 achieves 2.35x RPS (and 1.4x at -20% cost), HexGen-2 achieves 2.0x peak / -30% cost, and Arrow achieves 5.6x adaptive scaling",
        nx["splitwise_heterogeneous_rps_gain_x"] == 2.35
        and nx["splitwise_iso_perf_cost_reduction_pct"] == 20.0
        and nx["hexgen2_max_throughput_gain_x"] == 2.0
        and nx["hexgen2_cost_reduction_pct"] == 30.0
        and nx["arrow_adaptive_scaling_gain_x"] == 5.6,
    )

    # 5. Asymmetric Parallelism (`TP_p -> TP_d`) KV Layout Transpose
    tp_plan = compute_kv_layout_transpose_plan(
        num_layers=80, num_kv_heads=8, tp_prefill=2, pp_prefill=2, tp_decode=4, pp_decode=1
    )
    check(
        "22. Asymmetric parallelism (prefill TP_p=2, PP_p=2 -> 40 layers, 4 KV heads/rank vs decode TP_d=4, PP_d=1 -> 80 layers, 2 KV heads/rank) requires on-the-fly KV layout transpose",
        tp_plan["layers_per_prefill_stage"] == 40
        and tp_plan["kv_heads_per_prefill_rank"] == 4
        and tp_plan["layers_per_decode_stage"] == 80
        and tp_plan["kv_heads_per_decode_rank"] == 2
        and tp_plan["requires_transpose"] is True,
    )

    # 6. `llm-d` and Kubernetes Gateway API Inference Extension (`InferencePool`, `InferenceObjective`, `EPP`)
    pods = [
        LLMDReplicaEndpoint(
            pod_name="vllm-llama3-8b-pod-0",
            waiting_requests=6,
            kv_cache_usage_pct=70.0,
            cached_prefixes=("sys-hr",),
            loaded_loras=("lora-legal",),
        ),
        LLMDReplicaEndpoint(
            pod_name="vllm-llama3-8b-pod-1",
            waiting_requests=2,
            kv_cache_usage_pct=50.0,
            cached_prefixes=("sys-rag-doc",),
            loaded_loras=("lora-finance",),
        ),
        LLMDReplicaEndpoint(
            pod_name="vllm-llama3-8b-pod-2",
            waiting_requests=1,
            kv_cache_usage_pct=40.0,
            cached_prefixes=(),
            loaded_loras=(),
        ),
    ]
    epp_hit = simulate_llmd_epp_routing(
        pods, prefix_hash="sys-rag-doc", requested_lora="lora-finance", priority=1
    )
    check(
        "23. llm-d EPP (port 9002, FailClose) routes request with prefix 'sys-rag-doc' and LoRA 'lora-finance' to vllm-llama3-8b-pod-1 (port 8000, score 42.0 vs -24.0)",
        epp_hit["admitted"] is True
        and epp_hit["selected_pod"] == "vllm-llama3-8b-pod-1"
        and epp_hit["prefix_hit"] is True
        and epp_hit["lora_hit"] is True
        and epp_hit["target_port"] == 8000
        and epp_hit["epp_port"] == 9002
        and epp_hit["failure_mode"] == "FailClose",
    )

    epp_cold = simulate_llmd_epp_routing(
        pods, prefix_hash="unseen-prefix", requested_lora=None, priority=2
    )
    check(
        "24. On a prefix miss with no LoRA match, llm-d EPP routes to least-loaded vllm-llama3-8b-pod-2 (waiting=1, kv=40%, score -24.0)",
        epp_cold["selected_pod"] == "vllm-llama3-8b-pod-2"
        and epp_cold["prefix_hit"] is False
        and epp_cold["pod_scores"]["vllm-llama3-8b-pod-2"] == -24.0,
    )

    saturated_pods = [
        LLMDReplicaEndpoint(pod_name="pod-sat-0", waiting_requests=25, kv_cache_usage_pct=96.5),
        LLMDReplicaEndpoint(pod_name="pod-sat-1", waiting_requests=28, kv_cache_usage_pct=97.0),
    ]
    epp_low_prio = simulate_llmd_epp_routing(saturated_pods, prefix_hash="any", priority=2)
    epp_high_prio = simulate_llmd_epp_routing(saturated_pods, prefix_hash="any", priority=1)
    check(
        "25. Under >95% KV saturation (96.5%, 97.0%), InferenceObjective priority=2 (standard) is shed with HTTP 429 while priority=1 (high-priority) is admitted to pod-sat-0",
        epp_low_prio["admitted"] is False
        and epp_low_prio["http_status"] == 429
        and epp_high_prio["admitted"] is True
        and epp_high_prio["selected_pod"] == "pod-sat-0",
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
