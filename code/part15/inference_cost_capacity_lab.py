#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 15.18:
Inference cost, capacity and cost per token.

Runs 28 deterministic self-checks across all six chapter domains and prints:
`Summary: 28 passed, 0 failed`
"""

from __future__ import annotations
import sys
from inference_cost_capacity import (
    compute_cost_per_million_tokens,
    compute_decomposed_request_cost,
    evaluate_tco_cluster_economics,
    evaluate_goodput_and_slo_economics,
    size_vram_and_kv_concurrency,
    evaluate_llama2_7b_and_qwen3_14b_vram_economics,
    plan_gpu_fleet_capacity,
    evaluate_diurnal_three_tier_finops,
    compare_gpu_economics_matrix,
    evaluate_disaggregated_pd_goodput,
    evaluate_speculative_and_precision_economics,
    compute_self_hosted_vs_api_breakeven,
)


def run_lab() -> int:
    print("=== Chapter 15.18 Lab: Inference Cost, Capacity and Cost per Token ===")
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
    # 1. Cost per 1M Input/Output Tokens, Prefill/Decode Split & 3-Year TCO
    # -----------------------------------------------------------------------
    decomp = compute_decomposed_request_cost(
        hourly_cost_usd=2.00,
        decode_tokens_per_sec=100.0,
        prefill_requests_per_min=100.0,
        avg_input_tokens=500,
        avg_output_tokens=200,
        num_requests=1000,
    )
    check(
        "1. AIE Ch. 9: $2.00/hr GPU at 100 tok/s output costs $5.556 per 1M output tokens ($1.11 decode per 1K requests of 200 tokens)",
        decomp["decode_cost_per_1m_output_tokens_usd"] == 5.556
        and decomp["decode_cost_per_1k_requests_usd"] == 1.11,
    )
    check(
        "2. AIE Ch. 9: $2.00/hr GPU prefilling 100 req/min (500 tok/req = $0.667/1M input tok) costs $0.33 prefill and $1.44 total per 1K requests",
        decomp["input_cost_per_1m_input_tokens_usd"] == 0.667
        and decomp["prefill_cost_per_1k_requests_usd"] == 0.33
        and decomp["total_cost_per_1k_requests_usd"] == 1.44
        and decomp["output_to_input_token_cost_ratio"] == 8.33,
    )

    tco = evaluate_tco_cluster_economics()
    c40 = tco["cluster_40_h100"]
    check(
        "3. V21 Ch. 1: 40x H100 (60,000 tok/s, 37.8 kW at 1.35 PUE) takes 16.7 s and 0.175 kWh ($0.021 electricity) per 1M tokens",
        c40["facility_power_kw"] == 37.8
        and c40["aggregate_tps"] == 60000
        and c40["seconds_per_1m_tokens"] == 16.7
        and c40["kwh_per_1m_tokens"] == 0.175
        and c40["electricity_cost_per_1m_usd"] == 0.021,
    )
    check(
        "4. V21 Ch. 1: 40x H100 ($1.2M CapEx/3yr + $100K OpEx = $500K/yr) costs $0.28/1M ($0.0003/1K) at 100% util vs $0.68/1M ($0.0007/1K) at 40% util",
        c40["hw_opex_cost_per_1m_100pct_usd"] == 0.26
        and c40["total_cost_per_1m_100pct_usd"] == 0.28
        and c40["hw_opex_cost_per_1m_40pct_usd"] == 0.66
        and c40["total_cost_per_1m_40pct_usd"] == 0.68,
    )

    g2k = tco["global_2000_qps"]
    check(
        "5. V21 Ch. 8/12/14: 2,000 QPS global cluster (25.9B tok/day, 9.46T tok/yr) costs $0.70/1M (Ch. 12), $0.83/1M (Ch. 8 408 GPUs), and $1.16/1M (Ch. 14 424 GPUs) at peak vs $1.75/1M at 40% load",
        g2k["tokens_per_day_billions"] == 25.9
        and g2k["tokens_per_year_trillions"] == 9.46
        and g2k["ch12_408gpu_cost_per_1m_peak_usd"] == 0.70
        and g2k["ch8_408gpu_cost_per_1m_peak_usd"] == 0.83
        and g2k["ch14_424gpu_cost_per_1m_peak_usd"] == 1.16
        and g2k["ch12_408gpu_cost_per_1m_40pct_usd"] == 1.75,
    )

    # -----------------------------------------------------------------------
    # 2. Goodput-Adjusted Cost per 1M Tokens under P99 TTFT and ITL SLOs
    # -----------------------------------------------------------------------
    gp = evaluate_goodput_and_slo_economics(raw_rps=10.0, slo_compliant_rps=3.0, raw_cost_per_1m_usd=1.00)
    check(
        "6. AIE Ch. 9 Fig. 9-4: 10 RPS (100 RPM) raw throughput with 3 RPS (30 RPM) meeting TTFT <= 200 ms & TPOT <= 100 ms has 30.0% Goodput and 3.33x Goodput-adjusted cost per 1M tokens",
        gp["goodput_pct"] == 30.0
        and gp["cost_inflation_multiplier_x"] == 3.33
        and gp["goodput_adjusted_cost_per_1m_usd"] == 3.33,
    )
    check(
        "7. ASP Ch. 1 & Ch. 17: 8-GPU node at 10,000/12,000 tok/s achieves 83.3% goodput (vs Meta 30.0% effective ratio), and MLPerf v5.0 sets P99 TTFT/TPOT at 450 ms/40 ms (70B) and 6,000 ms/175 ms (405B)",
        gp["asp_8gpu_node_goodput_pct"] == 83.3
        and gp["meta_effective_ratio_pct"] == 30.0
        and gp["mlperf_v5_slos"]["llama2_70b_p99_ttft_ms"] == 450
        and gp["mlperf_v5_slos"]["llama2_70b_p99_tpot_ms"] == 40
        and gp["mlperf_v5_slos"]["llama3_1_405b_p99_ttft_ms"] == 6000
        and gp["mlperf_v5_slos"]["llama3_1_405b_p99_tpot_ms"] == 175,
    )
    check(
        "8. V12 Ch. 1 & Ch. 10: Real 4,096-token RAG prompts drop RPS from 45.0 to 6.2 (-86%) and spike P95 TTFT from 38 ms to 4,820 ms until Chunked Prefill restores 290 ms P95 TTFT and 22.8 ms P99 ITL",
        gp["synthetic_vs_prod_rag"]["rps_drop_pct"] == -86
        and gp["synthetic_vs_prod_rag"]["prod_4096tok_chunked_p95_ttft_ms"] == 290.0
        and gp["synthetic_vs_prod_rag"]["chunked_p99_itl_ms"] == 22.8,
    )

    # -----------------------------------------------------------------------
    # 3. KV Cache + Weight VRAM Sizing Across FP16/BF16, FP8 & INT4
    # -----------------------------------------------------------------------
    kv70_4k = size_vram_and_kv_concurrency(
        params_billions=70.0,
        num_layers=80,
        num_q_heads=64,
        num_kv_heads=8,
        head_dim=128,
        weight_bytes=2.0,
        kv_bytes=2.0,
        tp_size=4,
        gpu_vram_gb=80.0,
        seq_len=4096,
        override_kv_pool_gb=140.0,
    )
    kv70_128k = size_vram_and_kv_concurrency(
        params_billions=70.0,
        num_layers=80,
        num_q_heads=64,
        num_kv_heads=8,
        head_dim=128,
        weight_bytes=2.0,
        kv_bytes=2.0,
        tp_size=8,
        gpu_vram_gb=80.0,
        seq_len=128000,
        override_kv_pool_gb=428.0,
    )
    check(
        "9. V12 Ch. 1 & Ch. 8: Llama-3-70B GQA (8:1, 87.5% savings vs MHA) uses 327,680 B (320 KiB/tok), or 1.25 GiB (1.342 GB) at 4,096 tokens and 39.06 GiB at 128,000 tokens (vs 312.5 GB MHA)",
        kv70_4k["kv_bytes_per_token"] == 327680
        and kv70_4k["kv_kib_per_token"] == 320.0
        and kv70_4k["gqa_reduction_factor_x"] == 8.0
        and kv70_4k["gqa_savings_pct"] == 87.5
        and kv70_4k["kv_seq_gib_binary"] == 1.25
        and kv70_4k["kv_seq_gb_decimal"] == 1.342
        and kv70_128k["kv_seq_gib_binary"] == 39.06,
    )

    tp4_2k = size_vram_and_kv_concurrency(70.0, 80, 64, 8, 128, 2.0, 2.0, 4, 80.0, seq_len=2048, override_kv_pool_gb=140.0)
    tp4_8k = size_vram_and_kv_concurrency(70.0, 80, 64, 8, 128, 2.0, 2.0, 4, 80.0, seq_len=8192, override_kv_pool_gb=140.0)
    tp4_32k = size_vram_and_kv_concurrency(70.0, 80, 64, 8, 128, 2.0, 2.0, 4, 80.0, seq_len=32768, override_kv_pool_gb=140.0)
    tp8_2k = size_vram_and_kv_concurrency(70.0, 80, 64, 8, 128, 2.0, 2.0, 8, 80.0, seq_len=2048, override_kv_pool_gb=428.0)
    tp8_8k = size_vram_and_kv_concurrency(70.0, 80, 64, 8, 128, 2.0, 2.0, 8, 80.0, seq_len=8192, override_kv_pool_gb=428.0)
    tp8_32k = size_vram_and_kv_concurrency(70.0, 80, 64, 8, 128, 2.0, 2.0, 8, 80.0, seq_len=32768, override_kv_pool_gb=428.0)
    check(
        "10. V12 Ch. 8 Capacity Matrix: Llama-3-70B on 4x H100 (TP=4, 140 GB KV pool) supports [218, 54, 13] seqs and on 8x H100 (TP=8, 428 GB KV pool) supports [668, 167, 41] seqs at S=[2048, 8192, 32768]",
        (tp4_2k["max_concurrent_seqs"], tp4_8k["max_concurrent_seqs"], tp4_32k["max_concurrent_seqs"]) == (218, 54, 13)
        and (tp8_2k["max_concurrent_seqs"], tp8_8k["max_concurrent_seqs"], tp8_32k["max_concurrent_seqs"]) == (668, 167, 41),
    )

    vram_econ = evaluate_llama2_7b_and_qwen3_14b_vram_economics()
    l7b = vram_econ["llama2_7b"]
    check(
        "11. HLS Ch. 5 Table 5-7: Llama-2-7B (14 GB weights, 0.5 MiB/tok KV = 2.0 GB/4K seq) fits 4 seqs on A10 24GB ($2.00/hr) vs 16 seqs on L40S 48GB ($3.75/hr), making L40S 2.13x more cost-efficient per slot",
        l7b["kv_per_token_bytes"] == 524288
        and l7b["kv_4k_seq_gb"] == 2.0
        and l7b["a10_24gb"]["theoretical_batch"] == 5
        and l7b["a10_24gb"]["practical_batch"] == 4
        and l7b["l40s_48gb"]["theoretical_batch"] == 17
        and l7b["l40s_48gb"]["practical_batch"] == 16
        and l7b["l40s_vs_a10_slot_efficiency_x"] == 2.13,
    )

    q14 = vram_econ["qwen3_14b_l40s"]
    check(
        "12. HLS Ch. 9: Qwen3-14B on L40S (46,068 MiB) cuts weights from 27.52 GiB (BF16) to 9.36 GiB (4-bit AWQ), expanding KV cache from 11.00 GiB (72,064 tok, 1.76x) to 29.15 GiB (191,056 tok, 4.66x = 2.65x more KV tokens)",
        q14["bf16"]["kv_cache_tokens"] == 72064
        and q14["awq_4bit"]["kv_cache_tokens"] == 191056
        and q14["kv_token_expansion_x"] == 2.65,
    )

    # -----------------------------------------------------------------------
    # 4. GPU Fleet Capacity Planning from Peak RPS, Little's Law & Diurnal
    # -----------------------------------------------------------------------
    fleet = plan_gpu_fleet_capacity()
    check(
        "13. V21 Ch. 8: Llama-3-70B 2-GPU H100 replica (36 tok/s/seq, 150 tok = 4.2 s, B=64) sustains 15.2 QPS/replica (7.6 QPS/GPU)",
        fleet["req_duration_s"] == 4.2
        and fleet["replica_qps"] == 15.2
        and fleet["qps_per_gpu"] == 7.6,
    )
    check(
        "14. V21 Ch. 8: 2,000 QPS global peak with 3-region N+1 failover (1,000 QPS/region) requires 66 min replicas (132 GPUs) -> 17 8-GPU nodes (136 GPUs, 68 replicas = 1,034 QPS/region), or 51 nodes (408 GPUs) total",
        fleet["min_replicas_per_region"] == 66
        and fleet["min_gpus_per_region"] == 132
        and fleet["nodes_per_region"] == 17
        and fleet["deployed_gpus_per_region"] == 136
        and fleet["deployed_replicas_per_region"] == 68
        and fleet["region_qps_capacity"] == 1034
        and fleet["total_nodes_3_regions"] == 51
        and fleet["total_gpus_3_regions"] == 408,
    )
    check(
        "15. V21 Ch. 11: 12-month forecast from 286 QPS (+10%/mo growth, 15% seasonality) projects Month +0 = (286 QPS, 38 GPUs), Month +6 = (507 QPS, 67 GPUs), Month +11 = (755 QPS, 99 GPUs)",
        fleet["forecast_month_0_qps_gpus"] == (286, 38)
        and fleet["forecast_month_6_qps_gpus"] == (507, 67)
        and fleet["forecast_month_11_qps_gpus"] == (755, 99),
    )

    finops = evaluate_diurnal_three_tier_finops()
    check(
        "16. V19 Ch. 3 & Ch. 6: Three-Tier capacity purchasing (50% Reserved baseline at 45% off + 50% On-Demand diurnal burst at 30% duty cycle) saves 57.5% vs 24/7 On-Demand, and Spot saves 65% ($2.63/GPU/hr vs $7.50/GPU/hr)",
        finops["monthly_savings_pct"] == 57.5
        and finops["spot_gpu_hr_usd"] == 2.63,
    )
    check(
        "17. V19 Ch. 3: DCGM FinOps Reaper rejects $5M 16-node HGX H100 expansion when 98% K8s allocation masks 12% average SM activity, evicting pods with < 5% SM_ACTIVE for 4 hours and slicing 80GB GPUs into 7x 1g.10gb MIG instances",
        finops["reaper_policy"]["k8s_allocated_pct"] == 98.0
        and finops["reaper_policy"]["dcgm_sm_active_avg_pct"] == 12.0
        and finops["reaper_policy"]["zombie_sm_active_threshold_pct"] == 5.0
        and finops["reaper_policy"]["zombie_idle_hours"] == 4
        and finops["reaper_policy"]["mig_slices_per_80gb_gpu"] == 7
        and finops["reaper_policy"]["rejected_capex_request_usd"] == 5_000_000,
    )

    # -----------------------------------------------------------------------
    # 5. Accelerator Economics Matrix: L4, L40S, A100, H100, H200, B200, NVL72
    # -----------------------------------------------------------------------
    hw = compare_gpu_economics_matrix()
    check(
        "18. V04 Ch. 5 & V21 Ch. 2: L4 (24 GB, 72 W, PCIe single-slot) and L40S (48 GB, 0.864 TB/s, 362 BF16 / 733 FP8 TFLOPS, 419 FLOPS/B ridge point, 350 W, $8,000 = $22/TFLOP) lead single-GPU PCIe inference economics",
        hw["gpus"]["L4"]["vram_gb"] == 24
        and hw["gpus"]["L4"]["tdp_w"] == 72
        and hw["gpus"]["L40S"]["vram_gb"] == 48
        and hw["gpus"]["L40S"]["ridge_point_flops_per_byte"] == 419
        and hw["gpus"]["L40S"]["unit_price_usd"] == 8000,
    )
    check(
        "19. V21 Ch. 2 & HLS Table 5-4: H200 SXM (141 GB HBM3e, 4.8 TB/s, $40K CapEx, ~$6.30/hr cloud) provides +76.25% VRAM and +43.28% memory bandwidth over H100 SXM5 (80 GB, 3.35 TB/s, $30K CapEx, ~$6.20/hr cloud)",
        hw["h200_vs_h100_vram_gain_pct"] == 76.25
        and hw["h200_vs_h100_bw_gain_pct"] == 43.28
        and hw["gpus"]["H100_80GB_SXM5"]["cloud_hr_usd"] == 6.20
        and hw["gpus"]["H200_141GB_SXM"]["cloud_hr_usd"] == 6.30,
    )
    check(
        "20. ASP Ch. 1 & V06 Ch. 7: Blackwell B200 (192 GB, 8.0 TB/s, 1.8 TB/s NVLink 5, 1,000 W) and GB200 NVL72 rack (36 Grace + 72 B200, 13.5 TB HBM3e, 130 TB/s bisection, 720 PFLOPS FP8 / 1.44 EFLOPS FP4, 120-132 kW, 20 kW saved via copper backplane) achieve 3.4x MLPerf v5.0 inference throughput and 30x Dynamo 680B MoE throughput",
        hw["gpus"]["B200_SXM"]["bw_tb_s"] == 8.00
        and hw["gpus"]["GB200_NVL72_Rack"]["num_b200_gpus"] == 72
        and hw["gpus"]["GB200_NVL72_Rack"]["rack_bisection_tb_s"] == 130.0
        and hw["gpus"]["GB200_NVL72_Rack"]["mlperf_v5_infer_vs_hopper_x"] == 3.4
        and hw["gpus"]["GB200_NVL72_Rack"]["dynamo_680b_throughput_gain_x"] == 30.0,
    )
    check(
        "21. HLS Ch. 9: On 4x A100 (p4d.24xlarge), 4 independent DP=1 replicas deliver 9,816 TPS vs 3,926 TPS for 1x TP=4 (2.50x higher throughput), while TP=4 over NVLink cuts TTFT by 50.0% (66 ms -> 33 ms)",
        hw["distributed_tradeoff"]["a100_4x_dp1_tps"] == 9816
        and hw["distributed_tradeoff"]["a100_1x_tp4_tps"] == 3926
        and hw["distributed_tradeoff"]["dp_vs_tp_throughput_ratio_x"] == 2.50
        and hw["distributed_tradeoff"]["tp4_ttft_reduction_pct"] == 50.0,
    )

    # -----------------------------------------------------------------------
    # 6. Economic Impact of Quantization, Prefix Caching, Speculative Decoding,
    #    P/D Disaggregation & Self-Hosted vs Managed API Break-Even
    # -----------------------------------------------------------------------
    check(
        "22. HLS Ch. 9: 4-bit AWQ quantization on Qwen3-14B boosts ShareGPT throughput 2.70x (474.38 -> 1,280.0 tok/s, cutting cost/token by 63%) and cuts mean TTFT by 42.78% (103.61 -> 59.29 ms)",
        q14["sharegpt_throughput_gain_x"] == 2.70
        and q14["ttft_reduction_pct"] == 42.78,
    )
    check(
        "23. HLS Ch. 9: Prefix caching on Qwen3-14B boosts total token throughput 2.37x (474.38 -> 1,123.13 tok/s, cutting blended token cost by 57.8%) while holding ITL steady (43.24 vs 43.95 ms)",
        q14["prefix_caching_gain_x"] == 2.37,
    )

    spec_prec = evaluate_speculative_and_precision_economics()
    check(
        "24. ASP Ch. 15 & AIE Ch. 9: Chinchilla-70B (14.1 ms) + 4B draft (1.8 ms) at K=5, alpha=0.80 yields 3.6893 tokens in 23.1 ms (6.2614 ms/tok = 2.25x decode speedup, 55.59% decode cost reduction)",
        spec_prec["speculative"]["expected_tokens_per_cycle"] == 3.6893
        and spec_prec["speculative"]["cycle_time_ms"] == 23.1
        and spec_prec["speculative"]["effective_itl_ms"] == 6.2614
        and spec_prec["speculative"]["speedup_x"] == 2.25
        and spec_prec["speculative"]["decode_cost_reduction_pct"] == 55.59,
    )
    check(
        "25. ASP Ch. 19 Table 19-2: Dynamic precision scaling from FP16 (1.0x) to FP16+FP8 (0.50x mem, 1.5x speed), INT4+FP8 (0.25x mem, 1.8x speed), and INT4+FP4 (0.20x mem, 3.5x speed) cuts relative cost/token to 0.67x, 0.56x, and 0.29x",
        spec_prec["table_19_2"]["FP16_FP8"]["cost_x"] == 0.67
        and spec_prec["table_19_2"]["INT4_FP8"]["cost_x"] == 0.56
        and spec_prec["table_19_2"]["INT4_FP4"]["cost_x"] == 0.29,
    )

    pd = evaluate_disaggregated_pd_goodput()
    check(
        "26. ASP Ch. 17: Disaggregating prefill and decode in 2P1D (2x 5.6 = 11.2 RPS prefill, 1x 10.0 RPS decode across 3 GPUs) raises SLO goodput from 1.6 RPS/GPU to 3.3 RPS/GPU (3.33 exact = 2.08x gain, 52.0% lower Goodput cost/token)",
        pd["colocated_goodput_rps_per_gpu"] == 1.6
        and pd["total_prefill_rps"] == 11.2
        and pd["total_2p1d_goodput_rps"] == 10.0
        and pd["disagg_goodput_rps_per_gpu_book"] == 3.3
        and pd["disagg_goodput_rps_per_gpu_exact"] == 3.33
        and pd["per_gpu_goodput_gain_x"] == 2.08
        and pd["goodput_cost_reduction_pct"] == 52.0,
    )

    be_cluster = compute_self_hosted_vs_api_breakeven(
        hourly_replica_cost_usd=0.83 * 3.6,  # normalized so 1,000 tok/s = $0.83/1M at 100% util
        peak_replica_tps=1000.0,
        managed_api_price_per_1m_usd=2.00,
    )
    be_2h100 = compute_self_hosted_vs_api_breakeven(
        hourly_replica_cost_usd=12.40,       # 2x H100 SXM at $6.20/hr (HLS Table 5-4)
        peak_replica_tps=2100.0,             # ~2,100 tok/s per 2-GPU Llama-3-70B replica (V21 Ch. 8)
        managed_api_price_per_1m_usd=4.00,
    )
    check(
        "27. V21 Ch. 8 & Ch. 14: Self-hosted cluster at $0.83/1M peak token cost vs $2.00/1M managed API reaches break-even at exactly 41.50% average utilization",
        be_cluster["full_util_cost_per_1m_usd"] == 0.83
        and be_cluster["breakeven_utilization_pct"] == 41.50,
    )
    check(
        "28. 2x H100 SXM replica ($12.40/hr, 2,100 tok/s peak = $1.6402/1M at 100% util) vs $4.00/1M managed API breaks even at 41.01% utilization (861.11 tok/s = 74.40M tokens/day)",
        be_2h100["full_util_cost_per_1m_usd"] == 1.6402
        and be_2h100["breakeven_utilization_pct"] == 41.01
        and be_2h100["breakeven_daily_tokens_millions"] == 74.40,
    )

    failed = total - passed
    print(f"Summary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
