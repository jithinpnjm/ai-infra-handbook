#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.15: Fine-Tuning Infrastructure and Cost."""

from __future__ import annotations
import sys
from finetuning_infra_cost import (
    LoRAAdapterSpec,
    calculate_lora_adapter_footprint,
    evaluate_k8gs_llama3_8b_qlora_params,
    compare_customization_vram_profiles,
    evaluate_guanaco_qlora_table,
    evaluate_gpu_landscape_and_crossover,
    calculate_finetuning_batch_and_run_cost,
    evaluate_v22_llama2_7b_lora_case_study,
    evaluate_multilora_serving_and_rag_crossover,
    evaluate_cloud_capacity_and_finops,
)


def run_lab() -> int:
    print("=== Chapter 14.15 Lab: Fine-Tuning Infrastructure and Cost Verification ===")
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

    # 1. GPT-3 175B & Llama-2 13B LoRA Adapter Parameter & Memory Math (AIE Ch. 7 Table 7-5 & 7-6)
    gpt3_lora = calculate_lora_adapter_footprint(
        LoRAAdapterSpec(
            model_name="GPT-3-175B",
            total_params=175_000_000_000,
            num_layers=96,
            hidden_dim=12288,
            rank_r=2,
            lora_alpha=4,
            num_target_matrices_per_layer=4,
        )
    )
    check(
        "1. GPT-3 175B (96 layers, d=12288, r=2 across 4 attention matrices) yields 196,608 params/layer and 18,874,368 total trainable params (18.87M, ~0.01%)",
        gpt3_lora["params_per_layer"] == 196_608
        and gpt3_lora["trainable_params"] == 18_874_368
        and gpt3_lora["trainable_params_millions"] == 18.87
        and abs(gpt3_lora["pct_trainable"] - 0.0108) < 0.002,
    )

    check(
        "2. GPT-3 175B 16-bit LoRA adapter requires 37.75 MB (~37.7 MB) compared to 350.0 GB for 16-bit base model weights",
        abs(gpt3_lora["adapter_megabytes"] - 37.75) < 0.05 and gpt3_lora["base_weights_gb"] == 350.0,
    )

    llama2_13b_lora = calculate_lora_adapter_footprint(
        LoRAAdapterSpec(
            model_name="Llama-2-13B",
            total_params=13_000_000_000,
            num_layers=40,
            hidden_dim=5120,
            rank_r=2,
            lora_alpha=4,
            num_target_matrices_per_layer=4,
        )
    )
    check(
        "3. Llama-2 13B (40 layers, d=5120, r=2 on 4 attention matrices) yields 3,276,800 (~3.28M) trainable params and 6.55 MB adapter vs 26.0 GB base weights",
        llama2_13b_lora["trainable_params"] == 3_276_800
        and llama2_13b_lora["trainable_params_millions"] == 3.28
        and llama2_13b_lora["adapter_megabytes"] == 6.55
        and llama2_13b_lora["base_weights_gb"] == 26.0,
    )

    # 2. K8GS Ch. 4 Llama-3 8B QLoRA Parameter Reduction
    k8gs_qlora = evaluate_k8gs_llama3_8b_qlora_params()
    check(
        "4. K8GS Ch. 4 Llama-3 8B QLoRA (r=32, lora_alpha=64) reduces parameters from 4,628,721,664 to 88,121,344 trainable (1.90% / ~2%, ~98.10% reduction)",
        k8gs_qlora["quantized_tensor_elements"] == 4_628_721_664
        and k8gs_qlora["trainable_lora_params"] == 88_121_344
        and k8gs_qlora["trainable_pct"] == 1.90
        and k8gs_qlora["reduction_pct"] == 98.10
        and k8gs_qlora["scaling_factor"] == 2.0,
    )

    # 3. Full SFT vs LoRA vs QLoRA vs DPO / GRPO / PPO Memory Profiles (LEH Ch. 5 & 6, AIE Ch. 7)
    vram_7b = compare_customization_vram_profiles(7.0)
    vram_70b = compare_customization_vram_profiles(70.0)
    check(
        "5. Full SFT mixed-precision AdamW static memory (16*Psi) is 112.0 GB for 7B (98.0 GB checkpoint) and 1,120.0 GB for 70B (980.0 GB checkpoint), while pure BF16 Adam is 56.0 GB for 7B",
        vram_7b["full_sft"]["static_gb"] == 112.0
        and vram_7b["full_sft"]["checkpoint_gb"] == 98.0
        and vram_7b["full_sft"]["pure_bf16_static_gb"] == 56.0
        and vram_70b["full_sft"]["static_gb"] == 1120.0
        and vram_70b["full_sft"]["checkpoint_gb"] == 980.0,
    )

    check(
        "6. LEH Ch. 5 7B QLoRA vs LoRA benchmark: initialization drops 35.0% (14.0 GB -> 9.1 GB) and fine-tuning peak drops 40.38% (~40%, 15.6 GB -> 9.3 GB) with 30.0% throughput penalty",
        vram_7b["lora_16bit"]["init_gb"] == 14.0
        and vram_7b["lora_16bit"]["peak_gb"] == 15.6
        and vram_7b["qlora_4bit_nf4"]["init_gb"] == 9.1
        and vram_7b["qlora_4bit_nf4"]["peak_gb"] == 9.3
        and vram_7b["qlora_4bit_nf4"]["init_savings_vs_lora_pct"] == 35.0
        and vram_7b["qlora_4bit_nf4"]["peak_savings_vs_lora_pct"] == 40.38
        and vram_7b["qlora_4bit_nf4"]["throughput_penalty_pct"] == 30.0,
    )

    check(
        "7. Alignment static VRAM for 7B: Full DPO/GRPO requires 126.0 GB (18*Psi) vs Full PPO 4-model RLHF at 252.0 GB (36*Psi, saving 126.0 GB critic), while PEFT DPO with ref_model=None adds 0.0 GB reference weights",
        vram_7b["alignment_static_gb"]["full_dpo_static_gb"] == 126.0
        and vram_7b["alignment_static_gb"]["full_grpo_static_gb"] == 126.0
        and vram_7b["alignment_static_gb"]["full_ppo_static_gb"] == 252.0
        and vram_7b["alignment_static_gb"]["grpo_savings_vs_ppo_gb"] == 126.0
        and vram_7b["alignment_static_gb"]["peft_dpo_extra_ref_gb"] == 0.0,
    )

    check(
        "8. Alignment static VRAM for 70B: Full PPO requires 2,520.0 GB (36*Psi) vs 1,260.0 GB for Full DPO/GRPO (18*Psi)",
        vram_70b["alignment_static_gb"]["full_ppo_static_gb"] == 2520.0
        and vram_70b["alignment_static_gb"]["full_dpo_static_gb"] == 1260.0,
    )

    # 4. Guanaco QLoRA Table (AIE Ch. 7 Table 7-7)
    guanaco = evaluate_guanaco_qlora_table()
    check(
        "9. Guanaco 4-bit NF4 QLoRA memory footprints (6 GB for 7B, 10 GB for 13B, 21 GB for 33B, 41 GB for 65B) allow 65B fine-tuning on a single 48 GB L40S GPU (Elo 1022 vs ChatGPT 966)",
        guanaco["Guanaco-7B"]["vram_gb"] == 6
        and guanaco["Guanaco-13B"]["vram_gb"] == 10
        and guanaco["Guanaco-33B"]["vram_gb"] == 21
        and guanaco["Guanaco-65B"]["vram_gb"] == 41
        and guanaco["Guanaco-65B"]["elo"] == 1022
        and guanaco["Guanaco-65B"]["fits_single_48gb_l40s"] is True
        and guanaco["Guanaco-65B"]["fits_single_24gb_l4"] is False,
    )

    # 5. GPU Landscape, $/TFLOP, Node BOMs, and PCIe vs NVLink Crossover (V04 & V21 Ch. 2)
    hw = evaluate_gpu_landscape_and_crossover()
    tflop_costs = hw["cost_per_bf16_tflop"]
    check(
        "10. Price per dense BF16 TFLOP matches V21 Ch. 2 table: L40S=$22, H100 PCIe=$26, H100 SXM5=$30 ($10/yr over 3 yrs), A100 40GB PCIe=$32, H200 SXM=$40, A100 40GB SXM4=$48 ($16/yr), A100 80GB SXM4=$80",
        tflop_costs["L40S_48GB_PCIe"] == 22
        and tflop_costs["H100_80GB_PCIe"] == 26
        and tflop_costs["H100_80GB_SXM5"] == 30
        and tflop_costs["A100_40GB_PCIe"] == 32
        and tflop_costs["H200_141GB_SXM"] == 40
        and tflop_costs["A100_40GB_SXM4"] == 48
        and tflop_costs["A100_80GB_SXM4"] == 80,
    )

    check(
        "11. 8x H100 SXM5 node BOM is $285,000 ($35,625/GPU, 10.2 kW, 7,912 peak / 6,500 practical TFLOPS) vs $215,000 ($26,875/GPU, 4.5 kW, 6,048 peak TFLOPS, 24.56% cheaper) for 8x H100 PCIe",
        hw["node_8x_h100_sxm5"]["total_cost_usd"] == 285_000
        and hw["node_8x_h100_sxm5"]["cost_per_gpu_usd"] == 35_625.0
        and hw["node_8x_h100_sxm5"]["peak_bf16_tflops"] == 7912
        and hw["node_8x_h100_pcie"]["total_cost_usd"] == 215_000
        and hw["node_8x_h100_pcie"]["cost_per_gpu_usd"] == 26_875.0
        and hw["node_8x_h100_pcie"]["peak_bf16_tflops"] == 6048
        and hw["node_8x_h100_pcie"]["discount_vs_sxm_pct"] == 24.56,
    )

    check(
        "12. V04 Ch. 4 70B distributed fine-tuning crossover: SXM NVSwitch (900 GB/s) is 14.06x faster than PCIe Gen5 (64 GB/s); 30% PCIe hardware savings causes 90% comm stall and 5.0x longer training time",
        hw["pcie_vs_sxm_70b_crossover"]["bandwidth_ratio"] == 14.06
        and hw["pcie_vs_sxm_70b_crossover"]["hardware_capex_savings_pct"] == 30.0
        and hw["pcie_vs_sxm_70b_crossover"]["pcie_stall_fraction_pct"] == 90.0
        and hw["pcie_vs_sxm_70b_crossover"]["training_time_slowdown_factor"] == 5.0,
    )

    check(
        "13. H200 SXM provides 76.25% (~76%) more VRAM (141 GB vs 80 GB) and 43.28% (~43%) more bandwidth (4.8 vs 3.35 TB/s) than H100 SXM5 while B200 scales to 192 GB at 8.0 TB/s and 1,800 GB/s NVLink 5",
        round(100.0 * (141 - 80) / 80, 2) == 76.25
        and round(100.0 * (4.8 - 3.35) / 3.35, 2) == 43.28
        and hw["gpus"]["B200_192GB_SXM"]["vram_gb"] == 192
        and hw["gpus"]["B200_192GB_SXM"]["bw_tb_s"] == 8.0
        and hw["gpus"]["B200_192GB_SXM"]["nvlink_gb_s"] == 1800.0,
    )

    # 6. Effective Batch Size, Packing, and Run Economics (LEH Ch. 5 & V22 Ch. 3)
    batch_leh_dp = calculate_finetuning_batch_and_run_cost(
        per_device_batch_size=4,
        num_gpus=2,
        grad_accum_steps=4,
        max_seq_len=1024,
        total_tokens=32 * 1024 * 100,
        tokens_per_sec_per_gpu=2000.0,
        gpu_hourly_rate_usd=2.50,
    )
    check(
        "14. LEH Ch. 5 effective batch size formula: per_device_batch_size=4 * num_gpus=2 * grad_accum_steps=4 = 32 samples (32,768 tokens/step at seq_len=1024)",
        batch_leh_dp["effective_batch_size"] == 32 and batch_leh_dp["tokens_per_optimizer_step"] == 32_768,
    )

    batch_leh_unsloth = calculate_finetuning_batch_and_run_cost(
        per_device_batch_size=2,
        num_gpus=1,
        grad_accum_steps=8,
        max_seq_len=2048,
        total_tokens=15_000_000,
        tokens_per_sec_per_gpu=5000.0,
        gpu_hourly_rate_usd=2.40,
    )
    check(
        "15. LEH Ch. 5 TwinLlama-3.1-8B Unsloth SFT config (batch=2, gpus=1, grad_accum=8, seq=2048) yields effective_batch_size=16 and completes 15M tokens at 5,000 tok/s in 0.83 hours (50 minutes) on 1x A100",
        batch_leh_unsloth["effective_batch_size"] == 16
        and batch_leh_unsloth["wall_clock_hours"] == 0.83
        and round(batch_leh_unsloth["wall_clock_hours"] * 60) == 50,
    )

    v22_case = evaluate_v22_llama2_7b_lora_case_study()
    check(
        "16. V22 Ch. 3 Llama-2 7B LoRA case study: 7 GB INT8 weights + 0.8 GB grads + 1.6 GB opt + 2.0 GB act (+ 2.6 GB buffer) = 14.0 GB on 1x H100 (66.0 GB headroom), 50K conversations (1.5B tokens over 3 epochs), $5,100 total cost",
        v22_case["total_vram_gb"] == 14.0
        and v22_case["h100_headroom_gb"] == 66.0
        and v22_case["total_tokens"] == 1_500_000_000
        and v22_case["total_cost_usd"] == 5100.0,
    )

    # 7. Multi-LoRA Serving & RAG/Prompt vs Fine-Tuning Break-Even TCO (AIE Ch. 7 & V22 Ch. 3)
    multilora = evaluate_multilora_serving_and_rag_crossover()
    check(
        "17. AIE Ch. 7 Multi-LoRA storage proof: 4096x4096 base matrix (16,777,216 / 16.8M) + 100 adapters at r=8 (65,536 each) totals 23.3M params vs 1.68B merged (71.91x / ~72x compression)",
        multilora["base_matrix_params"] == 16_777_216
        and multilora["lora_ab_params"] == 65_536
        and multilora["merged_billions_book"] == 1.68
        and multilora["multilora_millions_book"] == 23.3
        and abs(multilora["compression_ratio"] - 71.91) < 0.05,
    )

    check(
        "18. Prompt/RAG context tax break-even: a $500 fine-tuning run that eliminates 2,000 recurring prompt tokens/query at $2.00/1M tokens ($0.004/query saved) breaks even at 125,000 queries",
        multilora["savings_per_query_usd"] == 0.004 and multilora["breakeven_queries"] == 125_000,
    )

    # 8. V22 Ch. 3 Inference TCO vs One-Time Fine-Tuning & V23 Ch. 9 Capacity Math
    check(
        "19. V22 Ch. 3 serving TCO: $110,000/yr for 63B tokens/yr = $0.00000174/token ($1.74/1M tokens vs $2.00/1M cloud = 1.15x cheaper), and 10M users at 100 tok/day costs $730,000/yr on cloud",
        abs(110_000 / 63_000_000_000 - 0.00000174) < 1e-8
        and round(2.00 / 1.74, 2) == 1.15
        and int(10_000_000 * 100 * 365 / 1_000_000 * 2.0) == 730_000,
    )

    # 9. Cloud Procurement Discounts, Spot Checkpointing, MIG, and Time-Slicing (K8GS Ch. 7 & 10, V19, V23)
    finops = evaluate_cloud_capacity_and_finops()
    disc = finops["discounts_pct"]
    check(
        "20. K8GS Ch. 7 & 10 cloud discount tiers: Reserved Instances up to 72% off, Spot Instances up to 90% off (70% baseline), Graviton up to 40% price-perf, Trainium Trn1 up to 50% lower cost, Trn2 30-40% better price-perf than P5e, gp3 20% cheaper than gp2",
        disc["reserved_instances_max_pct"] == 72
        and disc["spot_instances_max_pct"] == 90
        and disc["spot_baseline_pct"] == 70
        and disc["graviton_price_perf_pct"] == 40
        and disc["trn1_cost_savings_pct"] == 50
        and disc["trn2_vs_p5e_price_perf_pct_range"] == (30, 40)
        and disc["gp3_vs_gp2_savings_pct"] == 20,
    )

    check(
        "21. V19 Ch. 3 & 6 Spot & FinOps governance: 120-second (2-minute) Spot eviction warning with 15-minute async S3 checkpoints, and DCGM Reaper terminating pods with SM_ACTIVE < 5% for 4 hours",
        finops["spot_resilience"]["eviction_warning_seconds"] == 120
        and finops["spot_resilience"]["async_s3_checkpoint_interval_min"] == 15
        and finops["spot_resilience"]["dcgm_reaper_sm_active_threshold_pct"] == 5
        and finops["spot_resilience"]["dcgm_reaper_idle_hours"] == 4,
    )

    l4_ts = finops["l4_timeslicing_llama32_1b"]
    check(
        "22. K8GS Ch. 10 L4 (24 GB) time-slicing: single Llama-3.2-1B pod (1.8 GB) leaves 92.5% (~92%) VRAM underutilized; 10 time-sliced replicas allow 5 pods (9.0 GB total) to share 1 L4 GPU",
        l4_ts["single_pod_underutilized_pct"] == 92.5
        and l4_ts["timeslice_replicas"] == 10
        and l4_ts["five_replicas_vram_gb"] == 9.0,
    )

    h200_mig = finops["h200_mig_profiles"]
    check(
        "23. K8GS Ch. 10 Table 10.1 H200 (141 GB) MIG profiles: 7x 1g.18gb, 4x 1g.35gb, 3x 2g.35gb, 2x 3g.70gb, 1x 4g.70gb, and 1x 7g.141gb",
        h200_mig["1g.18gb"]["max_instances"] == 7
        and h200_mig["1g.35gb"]["max_instances"] == 4
        and h200_mig["2g.35gb"]["max_instances"] == 3
        and h200_mig["3g.70gb"]["max_instances"] == 2
        and h200_mig["4g.70gb"]["max_instances"] == 1
        and h200_mig["7g.141gb"]["memory_gb"] == 141,
    )

    c1000 = finops["cluster_1000_gpu_design"]
    check(
        "24. V23 Ch. 10 1,000-GPU $15M budget design: 600 L40S ($7.2M) + 400 L4 ($1.0M) + $0.625M IB + $2.5M NVMe + $0.375M servers + $1.0M power = $12.7M ($2.3M headroom), and 1 GB gradient (8,000 Mb) over 12.5 Gbps/GPU takes 640.0 ms",
        abs(c1000["total_m"] - 12.7) < 1e-6
        and abs(c1000["budget_headroom_m"] - 2.3) < 1e-6
        and finops["allreduce_1gb_at_12_5_gbps_ms"] == 640.0,
    )

    check(
        "25. V23 Ch. 9 3-year 40% YoY training capacity plan: 16 -> 24 -> 32 -> 48 GPUs ($1.92M 3-yr CapEx at $40K/H100; $1.53M/yr OpEx across 24 GPUs * 8,760 hrs = $7.28/GPU-hr raw and $18.20/GPU-hr at 84,058 GPU-hrs)",
        round(1_530_000 / (24 * 8760), 2) == 7.28
        and round(1_530_000 / 84_058, 2) == 18.20
        and (8 + 24 + 16) * 40_000 == 1_920_000,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
