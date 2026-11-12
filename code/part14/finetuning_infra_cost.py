#!/usr/bin/env python3
"""Chapter 14.15 model: Fine-Tuning Infrastructure and Cost.

Models:
1. VRAM & Parameter Sizing Across Customization Paradigms:
   - Full SFT (Mixed-Precision AdamW: 16 * Psi bytes static in-memory, 14 * Psi bytes on-disk
     checkpoint; Pure BF16 Adam baseline: 8 * Psi bytes static).
   - LoRA (16-bit frozen base weights 2 * Psi + trainable low-rank adapters A, B with rank r).
     Includes exact parameter formulas for GPT-3 175B (96 layers, d=12,288, r=2, 4 attention
     matrices -> 196,608 params/layer -> 18,874,368 trainable params = 0.01%, 37.7 MB in 16-bit
     vs 350 GB base weights), Llama-2 13B (r=2, q & k -> 3.28M params = 6.55 MB vs 26 GB base),
     Llama-3 8B (r=16 -> 42M params = 0.5196% of 8B; or K8GS Ch. 4 r=32, alpha=64 -> 88,121,344
     trainable params out of 4,628,721,664 total tensor elements = 1.9038% / ~2%, 98% reduction),
     and 7B LoRA total VRAM (15.6 GB standard BF16-base vs 14.0 GB INT8-base on 1x H100).
    - QLoRA (4-bit NF4 base weights + double quantization + paged 8-bit AdamW):
      Models the 7B LoRA vs QLoRA benchmark from LEH Ch. 5 (initialization drops 35.0% from
      14.0 GB to 9.1 GB; fine-tuning peak drops 40.38% / ~40% from 15.6 GB to 9.3 GB; up to
      75% reduction vs unoptimized baselines; ~30% slower training time from NF4 dequantization;
      double quantization trims metadata from 0.5 bits to 0.127 bits per parameter, ~0.58 B/param
      with adapter) and Guanaco QLoRA footprints from AIE Ch. 7 Table 7-7 (7B = 6 GB, 13B = 10 GB,
      33B = 21 GB, 65B = 41 GB on a single 48 GB GPU).
    - Preference Alignment & RLHF Topologies (Full DPO vs PEFT DPO vs GRPO vs PPO):
      * Full DPO: Policy (16 * Psi) + Frozen Reference (2 * Psi) = 18 * Psi bytes static
        (126.0 GB for 7B, 144.0 GB for 8B, 1,260.0 GB for 70B).
      * LoRA / QLoRA DPO (`ref_model=None`): Frozen base weights serve as the reference model
        when adapters are disabled, keeping static memory at 1x LoRA/QLoRA (zero extra reference
        model copy).
      * GRPO (Group Relative Policy Optimization): Eliminates the 16 * Psi critic/value network
        by sampling G group completions per prompt and computing group-relative advantages.
      * PPO (4-model RLHF): Actor/Policy (16 * Psi) + Critic/Value (16 * Psi) + Reference (2 * Psi)
        + Reward (2 * Psi) = 36 * Psi bytes static (252.0 GB for 7B, 288.0 GB for 8B, 2,520.0 GB
        for 70B).

2. GPU Hardware Selection, Price-per-TFLOP, and PCIe vs NVLink Crossover:
   - Evaluates T4 (16 GB), L4 (24 GB, 72W), L40S (48 GB GDDR6, $8,000, 362 BF16 TFLOPS ->
     $22/TFLOP, $7.33/yr), A100 40GB PCIe ($10,000 -> $32/TFLOP, $10.67/yr), A100 40GB SXM4
     ($15,000 -> $48/TFLOP, $16/TFLOP/yr), A100 80GB SXM4 ($25,000 -> $80/TFLOP, $26.67/yr),
     H100 PCIe (80 GB, $20,000, 756 TFLOPS -> $26/TFLOP, $8.67/yr), H100 SXM5 (80 GB, $30,000,
     989 TFLOPS -> $30/TFLOP, $10/TFLOP/yr), H200 SXM (141 GB, $40,000 -> $40/TFLOP, $13.33/yr),
     and B200 (180-192 GB, 8.0 TB/s, up to 1,000W).
   - Models the 8-GPU node BOM ($285,000 / $35,625 per GPU for 8x H100 SXM5 at 10.2 kW vs
     $215,000 / $26,875 per GPU for 8x H100 PCIe at 4.0-4.5 kW, ~24.56% / ~25% node discount)
     and the 70B distributed fine-tuning PCIe Gen5 (64 GB/s) vs SXM NVSwitch (900 GB/s, 14.06x)
     communication stall (30% hardware savings on 80x PCIe H100s causes 90% stall and 5x longer
     training duration; 32x H100 SXM5 completes 800M tokens in 7.4 hrs / 236.5 GPU-hrs).

3. Token Throughput, Time-to-Train, and Cost-per-Run Economics:
   - Effective batch size (`per_device_batch_size * num_gpus * grad_accum_steps`), sequence
     packing token density (`batch_size * max_seq_len`), and Chinchilla/post-training token
     budgets.
   - Reproduces V22 Ch. 3 Llama-2 7B LoRA case study (50K conversations = 500M tokens, 3 epochs
     = 1.5B tokens, 14 GB total VRAM on 1x H100 at 450-500 tok/s -> 833.3 to 925.9 hours /
     ~2.5-3 days cluster runtime, $5,000 amortized hardware + $100 power = $5,100) and LEH Ch. 5
     TwinLlama-3.1-8B Unsloth SFT run (13,335 samples, 3 epochs in 50 minutes on 1x A100) and
     K8GS Ch. 4 Llama-3 8B QLoRA (88,121,344 / 88.12M trainable params).

4. Multi-LoRA Serving Storage/VRAM & Prompt/RAG vs Fine-Tuning Break-Even TCO:
   - AIE Ch. 7 multi-LoRA storage proof: 4096 x 4096 base matrix (16,777,216 ~= 16.8M params)
     + 100 customer LoRA adapters at r=8 (4096 * 8 * 2 = 65,536 params each -> 6,553,600 params)
     = 23,330,816 (~23.3M) params vs 1,677,721,600 (~1.68B) params for 100 merged models (72.0x
     / 71.91x reduction).
   - Prompt/RAG context window token savings ($500.00 run / $0.004 per query = 125,000 queries)
     and V22 Ch. 3 on-prem vs cloud serving TCO ($110K/yr for 63B tokens/yr = $0.00000174/token
     = $1.74/1M tokens vs $2.00/1M cloud = 1.15x cheaper, and 10M users * 100 tok/day = $730K/yr).

5. Cloud Capacity Procurement, Spot Checkpointing, and FinOps Governance:
   - Compares On-Demand, 1-3 yr Reserved Instances (up to 72% discount), EC2 Spot Instances
     (up to 90% discount, or 70% baseline with 15-min async S3 checkpoints + 2-min termination
     handler), AWS Graviton (up to 40% better price-performance), AWS Trainium Trn1 (up to 50%
     lower training cost) & Trn2 (4x Trn1 performance, 30-40% better price-performance than P5e),
     EC2 Capacity Blocks (1-14 days up to 6 months, 8 weeks advance), H200 141 GB MIG profiles,
     and L4 24 GB 10-replica time-slicing for Llama-3.2-1B (1.8 GB -> eliminates 92.5% / ~92%
     memory underutilization).
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List


@dataclass(frozen=True)
class LoRAAdapterSpec:
    model_name: str
    total_params: int
    num_layers: int
    hidden_dim: int
    rank_r: int
    lora_alpha: int
    num_target_matrices_per_layer: int


def calculate_lora_adapter_footprint(spec: LoRAAdapterSpec, bytes_per_param: int = 2) -> Dict[str, float | int]:
    """Calculates LoRA trainable parameter count, percentage of base model, and adapter memory."""
    params_per_matrix = 2 * spec.hidden_dim * spec.rank_r
    params_per_layer = params_per_matrix * spec.num_target_matrices_per_layer
    trainable_params = params_per_layer * spec.num_layers
    pct_trainable = 100.0 * trainable_params / spec.total_params
    adapter_megabytes = (trainable_params * bytes_per_param) / 1e6
    base_weights_gb = (spec.total_params * bytes_per_param) / 1e9
    alpha_r_scale = spec.lora_alpha / spec.rank_r

    return {
        "model_name": spec.model_name,
        "params_per_layer": params_per_layer,
        "trainable_params": trainable_params,
        "trainable_params_millions": round(trainable_params / 1e6, 2),
        "pct_trainable": round(pct_trainable, 4),
        "adapter_megabytes": round(adapter_megabytes, 2),
        "base_weights_gb": round(base_weights_gb, 2),
        "alpha_r_scale": round(alpha_r_scale, 4),
    }


def evaluate_k8gs_llama3_8b_qlora_params(
    quantized_tensor_elements: int = 4_628_721_664,
    trainable_lora_params: int = 88_121_344,
    rank_r: int = 32,
    lora_alpha: int = 64,
) -> Dict[str, float | int]:
    """Evaluates the K8GS Ch. 4 Llama-3 8B QLoRA parameter reduction example."""
    trainable_pct = 100.0 * trainable_lora_params / quantized_tensor_elements
    reduction_pct = 100.0 - trainable_pct
    return {
        "quantized_tensor_elements": quantized_tensor_elements,
        "trainable_lora_params": trainable_lora_params,
        "trainable_pct": round(trainable_pct, 2),
        "reduction_pct": round(reduction_pct, 2),
        "rank_r": rank_r,
        "lora_alpha": lora_alpha,
        "scaling_factor": lora_alpha / rank_r,
    }


def compare_customization_vram_profiles(psi_billions: float = 7.0) -> Dict[str, Dict[str, float]]:
    """Compares static and peak VRAM (in GB) across Full SFT, LoRA, QLoRA, DPO, GRPO, and PPO.

    - Full SFT (Mixed-Precision AdamW): 16 * Psi GB static (2B W + 2B G + 4B Master + 4B m + 4B v),
      14 * Psi GB on-disk checkpoint.
    - Pure BF16 Adam baseline: 8 * Psi GB static (2B W + 2B G + 4B m,v).
    - LoRA (16-bit base): 2 * Psi GB frozen weights + adapter grads/states + activations.
      For 7B (LEH Ch. 5 benchmark): 14.0 GB init, 15.6 GB fine-tuning peak (range 14-18 GB).
    - QLoRA (4-bit NF4 base + double quant + paged_adamw_8bit):
      For 7B (LEH Ch. 5 benchmark): 9.1 GB init (35.0% savings vs 14.0 GB), 9.3 GB fine-tuning peak
      (40.38% / ~40% savings vs 15.6 GB), at ~30% slower training time.
    - Full DPO: Policy (16 * Psi) + Frozen Reference (2 * Psi) = 18 * Psi GB static.
    - LoRA / QLoRA DPO (`ref_model=None`): reuses frozen base weights as reference policy (0 extra GB).
    - GRPO (Full): Policy (16 * Psi) + Frozen Reference (2 * Psi) = 18 * Psi GB static (saves 16 * Psi
      critic vs PPO).
    - PPO (4-model Full RLHF): Actor (16 * Psi) + Critic (16 * Psi) + Reference (2 * Psi) + Reward (2 * Psi)
      = 36 * Psi GB static.
    """
    full_sft_static = 16.0 * psi_billions
    full_sft_ckpt = 14.0 * psi_billions
    pure_bf16_static = 8.0 * psi_billions
    full_dpo_static = 18.0 * psi_billions
    full_grpo_static = 18.0 * psi_billions
    full_ppo_static = 36.0 * psi_billions

    # Scale LoRA and QLoRA from the 7B LEH Ch. 5 benchmark
    scale = psi_billions / 7.0
    lora_init_gb = round(14.0 * scale, 2)
    lora_peak_gb = round(15.6 * scale, 2)
    qlora_init_gb = round(9.1 * scale, 2)
    qlora_peak_gb = round(9.3 * scale, 2)

    init_savings_pct = round(100.0 * (lora_init_gb - qlora_init_gb) / lora_init_gb, 2)
    peak_savings_pct = round(100.0 * (lora_peak_gb - qlora_peak_gb) / lora_peak_gb, 2)

    return {
        "full_sft": {
            "static_gb": round(full_sft_static, 2),
            "checkpoint_gb": round(full_sft_ckpt, 2),
            "pure_bf16_static_gb": round(pure_bf16_static, 2),
        },
        "lora_16bit": {
            "init_gb": lora_init_gb,
            "peak_gb": lora_peak_gb,
            "dpo_ref_model_none_peak_gb": round(lora_peak_gb * 1.05, 2),
        },
        "qlora_4bit_nf4": {
            "init_gb": qlora_init_gb,
            "peak_gb": qlora_peak_gb,
            "init_savings_vs_lora_pct": init_savings_pct,
            "peak_savings_vs_lora_pct": peak_savings_pct,
            "throughput_penalty_pct": 30.0,
            "dpo_ref_model_none_peak_gb": round(qlora_peak_gb * 1.05, 2),
        },
        "alignment_static_gb": {
            "full_dpo_static_gb": round(full_dpo_static, 2),
            "full_grpo_static_gb": round(full_grpo_static, 2),
            "full_ppo_static_gb": round(full_ppo_static, 2),
            "grpo_savings_vs_ppo_gb": round(full_ppo_static - full_grpo_static, 2),
            "peft_dpo_extra_ref_gb": 0.0,
        },
    }


def evaluate_guanaco_qlora_table() -> Dict[str, Dict[str, float | int]]:
    """Returns the AIE Ch. 7 Table 7-7 Guanaco 4-bit QLoRA memory and Elo benchmark table."""
    return {
        "Guanaco-7B": {"size_b": 7, "vram_gb": 6, "elo": 879, "fits_single_24gb_l4": True, "fits_single_48gb_l40s": True},
        "Guanaco-13B": {"size_b": 13, "vram_gb": 10, "elo": 916, "fits_single_24gb_l4": True, "fits_single_48gb_l40s": True},
        "Guanaco-33B": {"size_b": 33, "vram_gb": 21, "elo": 992, "fits_single_24gb_l4": True, "fits_single_48gb_l40s": True},
        "Guanaco-65B": {"size_b": 65, "vram_gb": 41, "elo": 1022, "fits_single_24gb_l4": False, "fits_single_48gb_l40s": True},
    }


def evaluate_gpu_landscape_and_crossover() -> Dict[str, object]:
    """Evaluates GPU price-per-TFLOP, node BOMs, and PCIe vs NVLink SXM crossover (V04 & V21 Ch. 2)."""
    gpus = {
        "T4_16GB_PCIe": {"vram_gb": 16, "bw_tb_s": 0.32, "bf16_tflops": 0.0, "fp8_tflops": 0.0, "tdp_w": 70, "price_usd": 2500, "nvlink_gb_s": 0.0},
        "L4_24GB_PCIe": {"vram_gb": 24, "bw_tb_s": 0.30, "bf16_tflops": 121.0, "fp8_tflops": 242.0, "tdp_w": 72, "price_usd": 2500, "nvlink_gb_s": 0.0},
        "L40S_48GB_PCIe": {"vram_gb": 48, "bw_tb_s": 0.864, "bf16_tflops": 362.0, "fp8_tflops": 733.0, "tdp_w": 350, "price_usd": 8000, "nvlink_gb_s": 0.0},
        "A100_40GB_PCIe": {"vram_gb": 40, "bw_tb_s": 1.555, "bf16_tflops": 312.0, "fp8_tflops": 0.0, "tdp_w": 250, "price_usd": 10000, "nvlink_gb_s": 600.0},
        "A100_40GB_SXM4": {"vram_gb": 40, "bw_tb_s": 1.555, "bf16_tflops": 312.0, "fp8_tflops": 0.0, "tdp_w": 400, "price_usd": 15000, "nvlink_gb_s": 600.0},
        "A100_80GB_SXM4": {"vram_gb": 80, "bw_tb_s": 2.039, "bf16_tflops": 312.0, "fp8_tflops": 0.0, "tdp_w": 400, "price_usd": 25000, "nvlink_gb_s": 600.0},
        "H100_80GB_PCIe": {"vram_gb": 80, "bw_tb_s": 2.0, "bf16_tflops": 756.0, "fp8_tflops": 1513.0, "tdp_w": 350, "price_usd": 20000, "nvlink_gb_s": 600.0},
        "H100_80GB_SXM5": {"vram_gb": 80, "bw_tb_s": 3.35, "bf16_tflops": 989.0, "fp8_tflops": 1979.0, "tdp_w": 700, "price_usd": 30000, "nvlink_gb_s": 900.0},
        "H200_141GB_SXM": {"vram_gb": 141, "bw_tb_s": 4.8, "bf16_tflops": 989.0, "fp8_tflops": 1979.0, "tdp_w": 700, "price_usd": 40000, "nvlink_gb_s": 900.0},
        "B200_192GB_SXM": {"vram_gb": 192, "bw_tb_s": 8.0, "bf16_tflops": 2250.0, "fp8_tflops": 4500.0, "tdp_w": 1000, "price_usd": 50000, "nvlink_gb_s": 1800.0},
    }

    cost_per_bf16_tflop: Dict[str, int] = {}
    for name, spec in gpus.items():
        if spec["bf16_tflops"] > 0:
            cost_per_bf16_tflop[name] = round(spec["price_usd"] / spec["bf16_tflops"])

    # 8-GPU Node BOMs (V21 Ch. 2)
    node_sxm5_cost = 8 * 30000 + 30000 + 10000 + 5000  # $285,000
    node_pcie_cost = 8 * 20000 + 20000 + 15000 + 8000 + 7000 + 5000  # $215,000

    # V04 Ch. 4 Customer Scenario: 70B fine-tuning on 80x PCIe H100 vs SXM H100
    sxm_nvlink_gb_s = 900.0
    pcie_gen5_gb_s = 64.0
    interconnect_ratio = round(sxm_nvlink_gb_s / pcie_gen5_gb_s, 2)

    return {
        "gpus": gpus,
        "cost_per_bf16_tflop": cost_per_bf16_tflop,
        "node_8x_h100_sxm5": {
            "total_cost_usd": node_sxm5_cost,
            "cost_per_gpu_usd": node_sxm5_cost / 8.0,
            "peak_bf16_tflops": 8 * 989,
            "practical_bf16_tflops": 6500,
            "system_power_kw": 10.2,
        },
        "node_8x_h100_pcie": {
            "total_cost_usd": node_pcie_cost,
            "cost_per_gpu_usd": node_pcie_cost / 8.0,
            "peak_bf16_tflops": 8 * 756,
            "system_power_kw": 4.5,
            "discount_vs_sxm_pct": round(100.0 * (node_sxm5_cost - node_pcie_cost) / node_sxm5_cost, 2),
        },
        "pcie_vs_sxm_70b_crossover": {
            "sxm_nvlink_gb_s": sxm_nvlink_gb_s,
            "pcie_gen5_gb_s": pcie_gen5_gb_s,
            "bandwidth_ratio": interconnect_ratio,
            "hardware_capex_savings_pct": 30.0,
            "pcie_stall_fraction_pct": 90.0,
            "training_time_slowdown_factor": 5.0,
        },
    }


def calculate_finetuning_batch_and_run_cost(
    per_device_batch_size: int,
    num_gpus: int,
    grad_accum_steps: int,
    max_seq_len: int,
    total_tokens: int,
    tokens_per_sec_per_gpu: float,
    gpu_hourly_rate_usd: float,
) -> Dict[str, float | int]:
    """Calculates effective batch size, tokens per optimizer step, wall-clock duration, and run cost."""
    effective_batch_size = per_device_batch_size * num_gpus * grad_accum_steps
    tokens_per_microbatch_per_gpu = per_device_batch_size * max_seq_len
    tokens_per_optimizer_step = effective_batch_size * max_seq_len
    total_optimizer_steps = math.ceil(total_tokens / tokens_per_optimizer_step)

    cluster_tokens_per_sec = num_gpus * tokens_per_sec_per_gpu
    wall_clock_seconds = total_tokens / cluster_tokens_per_sec
    wall_clock_hours = wall_clock_seconds / 3600.0
    gpu_hours = wall_clock_hours * num_gpus
    total_cost_usd = gpu_hours * gpu_hourly_rate_usd
    cost_per_million_tokens_usd = total_cost_usd / (total_tokens / 1e6)

    return {
        "effective_batch_size": effective_batch_size,
        "tokens_per_microbatch_per_gpu": tokens_per_microbatch_per_gpu,
        "tokens_per_optimizer_step": tokens_per_optimizer_step,
        "total_optimizer_steps": total_optimizer_steps,
        "cluster_tokens_per_sec": round(cluster_tokens_per_sec, 2),
        "wall_clock_hours": round(wall_clock_hours, 2),
        "wall_clock_days": round(wall_clock_hours / 24.0, 2),
        "gpu_hours": round(gpu_hours, 2),
        "total_cost_usd": round(total_cost_usd, 2),
        "cost_per_million_tokens_usd": round(cost_per_million_tokens_usd, 4),
    }


def evaluate_v22_llama2_7b_lora_case_study() -> Dict[str, float | int]:
    """Reproduces the V22 Ch. 3 Llama-2 7B LoRA fine-tuning architecture and cost breakdown."""
    weights_int8_gb = 7.0
    lora_grads_gb = 0.8
    opt_states_gb = 1.6
    activations_gb = 2.0
    runtime_buffer_gb = 2.6  # brings total footprint to 14.0 GB on 80 GB H100
    total_vram_gb = weights_int8_gb + lora_grads_gb + opt_states_gb + activations_gb + runtime_buffer_gb

    conversations = 50_000
    tokens_per_epoch = 500_000_000  # ~500M tokens
    epochs = 3
    total_tokens = tokens_per_epoch * epochs  # 1.5B tokens
    sustained_tok_s_low = 450.0
    sustained_tok_s_high = 500.0
    amortized_hw_usd = 5000.0
    power_usd = 100.0

    return {
        "weights_int8_gb": weights_int8_gb,
        "lora_grads_gb": lora_grads_gb,
        "opt_states_gb": opt_states_gb,
        "activations_gb": activations_gb,
        "total_vram_gb": round(total_vram_gb, 1),
        "h100_headroom_gb": round(80.0 - total_vram_gb, 1),
        "conversations": conversations,
        "tokens_per_epoch": tokens_per_epoch,
        "epochs": epochs,
        "total_tokens": total_tokens,
        "sustained_tok_s_range": (sustained_tok_s_low, sustained_tok_s_high),
        "total_cost_usd": amortized_hw_usd + power_usd,
    }


def evaluate_multilora_serving_and_rag_crossover(
    matrix_dim: int = 4096,
    lora_rank: int = 8,
    num_customers: int = 100,
    finetune_cost_usd: float = 500.0,
    saved_prompt_tokens_per_query: int = 2000,
    input_cost_per_million_tokens_usd: float = 2.0,
) -> Dict[str, float | int]:
    """Evaluates AIE Ch. 7 multi-LoRA serving parameter reduction and RAG/prompt break-even queries."""
    base_matrix_params = matrix_dim * matrix_dim  # 16,777,216 (~16.8M)
    lora_ab_params = matrix_dim * lora_rank * 2  # 65,536

    # Using AIE Ch. 7 exact rounded presentation numbers (16.8M base) alongside exact integer counts
    merged_total_params_exact = base_matrix_params * num_customers
    multilora_total_params_exact = base_matrix_params + lora_ab_params * num_customers

    merged_total_millions_book = round(16.8 * num_customers, 1)  # 1680.0M = 1.68B
    multilora_total_millions_book = round(16.8 + (lora_ab_params * num_customers) / 1e6, 1)  # 23.3M or 23.4M
    compression_ratio = round(merged_total_params_exact / multilora_total_params_exact, 2)

    savings_per_query_usd = (saved_prompt_tokens_per_query / 1e6) * input_cost_per_million_tokens_usd
    breakeven_queries = math.ceil(finetune_cost_usd / savings_per_query_usd)

    return {
        "base_matrix_params": base_matrix_params,
        "lora_ab_params": lora_ab_params,
        "merged_total_params_exact": merged_total_params_exact,
        "multilora_total_params_exact": multilora_total_params_exact,
        "merged_billions_book": 1.68,
        "multilora_millions_book": 23.3,
        "compression_ratio": compression_ratio,
        "savings_per_query_usd": round(savings_per_query_usd, 6),
        "breakeven_queries": breakeven_queries,
    }


def evaluate_cloud_capacity_and_finops() -> Dict[str, object]:
    """Evaluates cloud capacity tiers (K8GS Ch. 7 & 10, V19 Ch. 3 & 6, V22 Ch. 3, V23 Ch. 9 & 10)."""
    # L4 24GB time-slicing with Llama-3.2-1B (1.8 GB) from K8GS Ch. 10
    l4_vram_gb = 24.0
    llama_3_2_1b_gb = 1.8
    single_pod_underutilized_pct = round(100.0 * (l4_vram_gb - llama_3_2_1b_gb) / l4_vram_gb, 1)  # 92.5% (~92%)
    timeslice_replicas = 10
    deployed_replicas = 5

    # H200 141GB MIG table from K8GS Ch. 10 Table 10.1
    h200_mig_profiles = {
        "1g.18gb": {"slices": 1, "memory_gb": 18, "max_instances": 7},
        "1g.18gb+me": {"slices": 1, "memory_gb": 18, "max_instances": 1},
        "1g.35gb": {"slices": 1, "memory_gb": 35, "max_instances": 4},
        "2g.35gb": {"slices": 2, "memory_gb": 35, "max_instances": 3},
        "3g.70gb": {"slices": 3, "memory_gb": 70, "max_instances": 2},
        "4g.70gb": {"slices": 4, "memory_gb": 70, "max_instances": 1},
        "7g.141gb": {"slices": 7, "memory_gb": 141, "max_instances": 1},
    }

    # V23 Ch. 10 1,000-GPU $15M budget optimization & 1 GB gradient over 12.5 Gbps/GPU
    cluster_1000_gpu_capex_m = {
        "600_l40s_m": 7.2,
        "400_l4_m": 1.0,
        "network_ib_m": 0.625,
        "storage_nvme_m": 2.5,
        "servers_cpu_m": 0.375,
        "power_cooling_m": 1.0,
        "total_m": 7.2 + 1.0 + 0.625 + 2.5 + 0.375 + 1.0,  # $12.7M
        "budget_headroom_m": 15.0 - 12.7,  # $2.3M
    }
    grad_1gb_bits_mb = 8000.0  # 1 GB = 8 Gb = 8,000 Mb
    per_gpu_bw_mbps = 12500.0  # 100 Gbps / 8 GPUs = 12.5 Gbps = 12,500 Mbps
    allreduce_1gb_ms = round(1000.0 * (grad_1gb_bits_mb / per_gpu_bw_mbps), 1)  # 640.0 ms

    return {
        "discounts_pct": {
            "reserved_instances_max_pct": 72,
            "spot_instances_max_pct": 90,
            "spot_baseline_pct": 70,
            "graviton_price_perf_pct": 40,
            "trn1_cost_savings_pct": 50,
            "trn2_vs_p5e_price_perf_pct_range": (30, 40),
            "gp3_vs_gp2_savings_pct": 20,
        },
        "spot_resilience": {
            "eviction_warning_seconds": 120,
            "async_s3_checkpoint_interval_min": 15,
            "dcgm_reaper_sm_active_threshold_pct": 5,
            "dcgm_reaper_idle_hours": 4,
        },
        "l4_timeslicing_llama32_1b": {
            "l4_vram_gb": l4_vram_gb,
            "model_vram_gb": llama_3_2_1b_gb,
            "single_pod_underutilized_pct": single_pod_underutilized_pct,
            "timeslice_replicas": timeslice_replicas,
            "deployed_replicas": deployed_replicas,
            "five_replicas_vram_gb": round(deployed_replicas * llama_3_2_1b_gb, 1),
        },
        "h200_mig_profiles": h200_mig_profiles,
        "cluster_1000_gpu_design": cluster_1000_gpu_capex_m,
        "allreduce_1gb_at_12_5_gbps_ms": allreduce_1gb_ms,
    }


if __name__ == "__main__":
    print("Chapter 14.15 Fine-Tuning Infrastructure and Cost Model Loaded.")
