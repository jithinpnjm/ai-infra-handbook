#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 15.17:
Lab: serve and benchmark on GKE and Nebius.

Runs 28 deterministic self-checks across all six chapter domains and prints:
`Summary: 28 passed, 0 failed`
"""

from __future__ import annotations
import sys
from serve_benchmark_gke_nebius import (
    evaluate_gke_nebius_node_pools_and_parallelism,
    evaluate_weight_caching_and_startup,
    compute_vllm_memory_and_kv_budget,
    evaluate_gateway_epp_and_disaggregated_kv,
    simulate_keda_autoscaling_and_observability,
    evaluate_benchmark_sweeps_and_fleet_efficiency,
)


def run_lab() -> int:
    print("=== Chapter 15.17 Lab: Serve and Benchmark on GKE and Nebius ===")
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
    # 1. GKE & Nebius MK8s Node Pools, GFD/NFD/MIG/Time-Slicing & TP vs DP
    # -----------------------------------------------------------------------
    pools = evaluate_gke_nebius_node_pools_and_parallelism()
    np_dict = pools["node_pools"]
    ref = pools["nfd_gfd_reference"]

    check(
        "1. Nebius L40S reports 46,068 MiB total (45,469 MiB free idle, CC 8.9) and GKE/Nebius H100/H200 report 80 GB / 141 GB with 900 GB/s NVLink 4.0 and 3.2 Tbps IB",
        np_dict["nebius_gpu_l40s_d"]["vram_mib_per_gpu"] == 46068
        and np_dict["nebius_gpu_l40s_d"]["free_mib_idle"] == 45469
        and np_dict["nebius_gpu_l40s_d"]["compute_cap"] == "8.9"
        and np_dict["nebius_gpu_h100_sxm"]["bw_gbps_per_gpu"] == 900.0
        and np_dict["nebius_gpu_h200_sxm"]["vram_gb_per_gpu"] == 141
        and np_dict["nebius_gpu_h200_sxm"]["ib_total_tbps_per_node"] == 3.2,
    )
    check(
        "2. NFD labels NVIDIA GPUs as pci-0302_10de.present and GFD reports A100-40GB as 40,537 MiB (37.25 GiB) and A100-80GB as 74.5 GiB",
        ref["nfd_nvidia_pci_label"] == "feature.node.kubernetes.io/pci-0302_10de.present"
        and ref["gfd_a100_40gb_memory_mib"] == 40537
        and ref["gfd_a100_40gb_gib"] == 37.25
        and ref["gfd_a100_80gb_gib"] == 74.5,
    )
    check(
        "3. MIG splits A100-40GB into 7 x 1g.5gb slices (14 on 2x A100) while time-slicing with replicas=8 exposes 80 virtual GPUs across 10 GPUs",
        ref["mig_a100_max_slices_per_gpu"] == 7
        and ref["mig_smallest_profile"] == "1g.5gb"
        and ref["mig_2x_a100_total_1g_5gb"] == 14
        and ref["timeslicing_replicas_per_gpu"] == 8
        and ref["timeslicing_10_gpu_virtual_units"] == 80,
    )
    check(
        "4. NVLink 5.0 delivers 1,800 GB/s (18 x 100 GB/s links) and 130 TB/s on GB200 NVL72 (2.0x over 900 GB/s NVLink 4.0)",
        ref["nvlink5_bw_gbps"] == 1800.0
        and ref["nvlink5_links_per_gpu"] == 18
        and ref["nvl72_gpus"] == 72
        and ref["nvl72_total_gpu_bw_tbps"] == 130.0,
    )
    check(
        "5. On PCIe g6e.12xlarge (4x L40S), TP=1 beats TP=2/4; on NVLink p4d.24xlarge (8x A100), TP=4 cuts TTFT 50% (66 -> 33 ms) while 4x DP achieves 9,816 vs 3,926 TPS (2.50x)",
        pools["g6e_pcie_best_tp_degree"] == 1
        and pools["p4d_tp1_ttft_ms"] == 66.0
        and pools["p4d_tp4_ttft_ms"] == 33.0
        and pools["p4d_ttft_reduction_pct"] == 50.0
        and pools["p4d_tp4_tps"] == 3926.0
        and pools["p4d_dp4_tps"] == 9816.0
        and pools["p4d_dp4_vs_tp4_ratio"] == 2.5,
    )

    # -----------------------------------------------------------------------
    # 2. Startup Pipeline, Cold-Start Multipliers & Weight Caching
    # -----------------------------------------------------------------------
    start = evaluate_weight_caching_and_startup()
    check(
        "6. Caching 28 GB weights on Nebius NVMe + runai_streamer (concurrency=16, 6.0 GB/s) cuts load time from 448.0 s (500 Mbps HF download) to 4.67 s (95.93x faster)",
        start["hf_download_and_copy_s"] == 448.0
        and start["gcs_fuse_load_s"] == 11.2
        and start["nebius_nvme_load_s"] == 4.67
        and start["speedup_nvme_vs_hf_x"] == 95.93
        and start["streamer_format"] == "runai_streamer"
        and start["streamer_concurrency"] == 16,
    )
    check(
        "7. Qwen3-14B FP16 loads weights in 4.47 s (5.265852 s total) while Qwen3-14B-AWQ loads in 10.652314 s",
        start["qwen14b_fp16_weights_load_s"] == 4.47
        and start["qwen14b_fp16_total_load_s"] == 5.265852
        and start["qwen14b_awq_total_load_s"] == 10.652314,
    )
    check(
        "8. Cold-start latency is 3x-5x warm decode for 1B-3B, 16x for mid-size LLMs, and 50x+ for 70B+ (30 s cold start vs 100 ms warm = 300.0x delay)",
        start["cold_start_multipliers"]["small_1b_3b"] == (3, 5)
        and start["cold_start_multipliers"]["midsize_llm"] == 16
        and start["cold_start_multipliers"]["large_70b_plus"] == 50
        and start["cold_to_warm_request_ratio"] == 300.0,
    )
    check(
        "9. Benchmark methodology requires 5-10 warmup steps for eager PyTorch, 20-50 for torch.compile/CUDA graphs, and >= 100 measurement iterations",
        start["warmup_iterations_eager"] == (5, 10)
        and start["warmup_iterations_compiled_cudagraph"] == (20, 50)
        and start["min_benchmark_iterations"] == 100,
    )

    # -----------------------------------------------------------------------
    # 3. Serving Engine Memory Planning & Quantization (L40S & A100-80GB)
    # -----------------------------------------------------------------------
    mem = compute_vllm_memory_and_kv_budget()
    check(
        "10. On L40S (46,068 MiB), Qwen3-14B FP16 uses 27.5185 GiB weights + 11.00 GiB KV cache (38.5 GiB total) for 72,064 tokens (1.76x concurrency at 40,960 tokens)",
        mem["fp16_weights_gib"] == 27.5185
        and mem["fp16_kv_cache_gib"] == 11.00
        and mem["fp16_occupied_gib"] == 38.5
        and mem["fp16_kv_tokens"] == 72064
        and mem["fp16_max_concurrency_40k"] == 1.76,
    )
    check(
        "11. Qwen3-14B-AWQ (4-bit) cuts weights to 9.3619 GiB and expands KV cache to 29.15 GiB for 191,056 tokens (2.65x more tokens, 4.66x concurrency at 40,960 tokens)",
        mem["awq_weights_gib"] == 9.3619
        and mem["awq_kv_cache_gib"] == 29.15
        and mem["awq_kv_tokens"] == 191056
        and mem["awq_max_concurrency_40k"] == 4.66
        and mem["kv_token_expansion_x"] == 2.65
        and mem["concurrency_expansion_x"] == 2.65,
    )
    check(
        "12. On A100-80GB (79.14 GiB) at gpu_memory_utilization=0.90 (71.22 GiB usable), 14.99 GiB weights + 0.12 GiB non-torch + 1.19 GiB activations leaves 54.93 GiB KV cache",
        mem["a100_total_gib"] == 79.14
        and mem["a100_usable_gib"] == 71.22
        and mem["a100_weights_gib"] == 14.99
        and mem["a100_non_torch_gib"] == 0.12
        and mem["a100_activation_peak_gib"] == 1.19
        and mem["a100_kv_cache_gib"] == 54.93,
    )
    check(
        "13. 8B FP16 model at 2,048 context needs 17.3 GB (18.3 GB with 1 GB runtime buffer) at batch=1 and > 28.0 GB at batch=10; 70B needs 280 GB FP32, 140 GB FP16, or 35 GB INT4",
        mem["model_8b_batch1_total_gb"] == 17.3
        and mem["model_8b_batch1_with_infra_gb"] == 18.3
        and mem["model_8b_batch10_total_gb"] == 28.0
        and mem["model_70b_fp32_gb"] == 280.0
        and mem["model_70b_fp16_gb"] == 140.0
        and mem["model_70b_int4_gb"] == 35.0,
    )

    # -----------------------------------------------------------------------
    # 4. Gateway API Inference Extension (`EndpointPicker`) & Disaggregated KV
    # -----------------------------------------------------------------------
    gw = evaluate_gateway_epp_and_disaggregated_kv()
    check(
        "14. Gateway API InferencePool (v1, port 8000, up to 8 ports) and EndpointPicker (port 9002, FailClose) select vllm-replica-1 (queue=1, KV=42%, prefix hit) with score 12.8",
        gw["inference_pool_api"] == "inference.networking.k8s.io/v1"
        and gw["target_port"] == 8000
        and gw["max_supported_target_ports"] == 8
        and gw["epp_port"] == 9002
        and gw["epp_failure_mode"] == "FailClose"
        and gw["selected_pod"] == "vllm-replica-1"
        and gw["selected_score"] == 12.8,
    )
    check(
        "15. InferenceObjective (v1alpha2) assigns priority 1 to high-priority interactive traffic and priority 2 to standard/batch traffic",
        gw["inference_objective_api"] == "inference.networking.x-k8s.io/v1alpha2"
        and gw["high_priority_level"] == 1
        and gw["standard_priority_level"] == 2,
    )
    check(
        "16. Disaggregated KV transfer of 512 MB takes 409.6 ms on 10 Gbps pod Ethernet vs 6.83 ms on 600 Gbps RoCEv2 (60.0x faster) and 5.12 ms on 800 Gbps NDR IB",
        gw["eth_transfer_ms"] == 409.6
        and gw["roce_transfer_ms"] == 6.83
        and gw["ib_transfer_ms"] == 5.12
        and gw["rdma_speedup_vs_eth_x"] == 60.0,
    )

    # -----------------------------------------------------------------------
    # 5. Prometheus + DCGM Observability, TPOT Alerting & KEDA Autoscaling
    # -----------------------------------------------------------------------
    obs = simulate_keda_autoscaling_and_observability()
    check(
        "17. ServiceMonitor scrapes /metrics every 15s (KServe port 8080) and human reading speed (180 wpm = 3 words/s = 4-5 tokens/s) sets the 0.3 s (300 ms) TPOT alert threshold",
        obs["scrape_interval_s"] == 15
        and obs["kserve_prometheus_port"] == 8080
        and obs["human_reading_wpm"] == 180
        and obs["human_reading_wps"] == 3
        and obs["human_reading_tps_min"] == (4, 5)
        and obs["tpot_alert_threshold_s"] == 0.30
        and obs["tpot_alert_threshold_ms"] == 300.0
        and obs["vllm_latency_alert_fires"] is True,
    )
    check(
        "18. KEDA scales InferenceService (min=1, max=5, target=4 running/pod) from 3 pods (18 running, 6 waiting) to 5 replicas",
        obs["current_replicas"] == 3
        and obs["total_running"] == 18
        and obs["total_waiting"] == 6
        and obs["desired_replicas_running_only"] == 5
        and obs["desired_replicas_with_waiting"] == 5,
    )
    check(
        "19. Production LLM-as-a-judge quality monitoring asynchronously samples 1%-10% of responses to avoid blocking user requests",
        obs["llm_judge_async_sample_pct"] == (1, 10),
    )

    # -----------------------------------------------------------------------
    # 6. Concurrency Sweeps, E2E Latency Math & Fleet Efficiency / Cost Waste
    # -----------------------------------------------------------------------
    bench = evaluate_benchmark_sweeps_and_fleet_efficiency()
    sg = bench["sharegpt_stats"]
    fp16_sg = bench["fp16_sharegpt"]
    fp16_pr = bench["fp16_prefix_rep"]

    check(
        "20. ShareGPT 100-sample inspection reports prompt mean 232.60 (median 141.50, range 5-817) and output mean 220.61 (median 164.50, range 4-771)",
        sg["prompt_mean"] == 232.60
        and sg["prompt_median"] == 141.50
        and sg["prompt_min"] == 5
        and sg["prompt_max"] == 817
        and sg["output_mean"] == 220.61
        and sg["output_median"] == 164.50,
    )
    check(
        "21. Qwen3-14B FP16 on ShareGPT (2,000 prompts, 10 RPS, concurrency 10) achieves 474.38 total TPS (227.64 output TPS, 1.10 req/s), 104.15 ms TTFT, and 43.24 ms ITL (72.15 ms P99)",
        fp16_sg["total_tps"] == 474.38
        and fp16_sg["output_tps"] == 227.64
        and fp16_sg["req_throughput_rps"] == 1.10
        and fp16_sg["mean_ttft_ms"] == 104.15
        and fp16_sg["mean_itl_ms"] == 43.24
        and fp16_sg["p99_itl_ms"] == 72.15,
    )
    check(
        "22. Qwen3-14B FP16 on Prefix Repetition (1,000 prompts, 5 RPS, 256+256 in, 128 out) reaches 1,123.13 total TPS (2.37x over ShareGPT) at 97% GPU utilization",
        fp16_pr["total_tps"] == 1123.13
        and fp16_pr["gpu_util_pct"] == 97
        and bench["prefix_vs_sharegpt_tps_ratio"] == 2.37
        and fp16_pr["mean_ttft_ms"] == 104.64
        and fp16_pr["mean_itl_ms"] == 43.95,
    )
    check(
        "23. Qwen3-14B-AWQ on ShareGPT boosts total throughput 2.70x (474.38 -> 1,280.0 TPS) and reduces mean TTFT by 42.78% (103.61 -> 59.29 ms)",
        bench["awq_sharegpt_total_tps"] == 1280.0
        and bench["awq_sharegpt_ttft_ms"] == 59.29
        and bench["awq_tps_speedup_x"] == 2.70
        and bench["awq_ttft_reduction_pct"] == 42.78,
    )
    check(
        "24. End-to-end latency e2e = TTFT + (output_tokens - 1) * ITL equals 5,686.29 ms for 128 output tokens at 104.64 ms TTFT and 43.95 ms ITL",
        bench["e2e_prefix_rep_ms"] == 5686.29,
    )
    check(
        "25. SGLang RadixAttention delivers 40.0% higher throughput on variable-length prompts (50-5,000 tokens) compared to fixed-length benchmarks",
        bench["sglang_variable_prompt_gain_pct"] == 40.0,
    )
    check(
        "26. GuideLLM sweep uses 256 prompt tokens, 128 output tokens, 400 max seconds, and 20% warmup (warmup-percent=0.2)",
        bench["guidellm_default_prompt_tokens"] == 256
        and bench["guidellm_default_output_tokens"] == 128
        and bench["guidellm_max_seconds"] == 400
        and bench["guidellm_warmup_percent"] == 0.2,
    )
    check(
        "27. Scaling efficiency is 81.25% at 6.5x speedup on 8 GPUs, and a 64-GPU fleet at 52% scaling efficiency (45% util) wastes 31 GPUs (10,416 GPU-hrs = ~$50,000 over 336 hrs)",
        bench["eff_8gpu_pct"] == 81.25
        and bench["effective_gpus"] == 33
        and bench["wasted_gpus"] == 31
        and bench["wasted_gpu_hours"] == 10416
        and bench["cloud_cost_waste_usd"] == 50000,
    )
    check(
        "28. In multi-step agentic/reasoning workflows, >= 60% of end-to-end session latency originates from external tool/API/database calls",
        bench["agentic_external_latency_share_pct"] == 60,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
