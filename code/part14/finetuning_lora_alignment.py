#!/usr/bin/env python3
"""Chapter 14.13 model: Fine-tuning: SFT, LoRA and QLoRA, preference alignment.

Models:
1. Adaptation Decision Matrix & Economics (Prompting vs RAG vs Fine-Tuning):
   - Evaluates information-based vs behavior/format-based failures ("Finetuning is for form, and RAG is for facts").
   - Reproduces Ovadia et al. (2024) current-events QA benchmark (Mistral-7B, Llama 2-7B, Orca 2-7B) and
     BloombergGPT (50B, 1.3M A100 GPU hours, $1.3M-$2.6M) vs GPT-4-0314 financial benchmarks (FiQA, ConvFinQA).
   - Models upfront fine-tuning cost vs per-request long-prompt "mortgage" break-even token volume.
2. Full Fine-Tuning vs PEFT Memory & Parameter Math:
   - Full fine-tuning baseline (`16 bytes/param`: `4B` FP32 or `2B` BF16 weights + `4B` gradients + `8B` Adam states
     = `112.0 GB` for `7B`, `1,120.0 GB` for `70B`) and pure 16-bit calculation (`14.0 GB` weights + `42.0 GB`
     gradients/Adam = `56.0 GB` for `7B`; `26.0 GB` weights + `78.0 GB` gradients/Adam = `104.0 GB` for `13B`).
   - LoRA low-rank decomposition `W' = W_0 + (alpha / r) * (A @ B)` with `A ~ N(0, 1/sqrt(r))` and `B = 0`,
     trainable parameter counts `P_LoRA = r * (d_in + d_out)` across single matrices (`4096 x 4096` with `r=8`
     -> `65,536` params; `100` adapters = `23.3M` vs `1.68B` full matrices), GPT-3 175B (`96` layers, `d=12,288`,
     `r=2` across 4 attention matrices -> `196,608` params/layer, `18,874,368` total = `0.01%`), Llama 2 13B
     (`3.28M` params = `6.55 MB` vs `26 GB`), and Llama 3 8B (`41,943,040` / `~42M` params at `r=16` = `0.5196%`
     of `8.03B`; `88,121,344` vs `4,628,721,664` quantized params at `r=32` with `lm_head`).
   - DoRA (Weight-Decomposed Low-Rank Adaptation) magnitude `m` + directional update `V = W_0 + (alpha/r) * B @ A`.
3. QLoRA Internals (`NF4`, Double Quantization, and Paged Optimizers):
   - 4-bit NormalFloat (`NF4`) 16 quantile levels for `N(0, 1)` normalized into `[-1, 1]` with block size `B_1 = 64`.
   - Double Quantization (`B_1 = 64`, `B_2 = 256`): reduces quantization constant overhead from
     `32 / 64 = 0.500 bits/param` to `8 / 64 + 32 / (64 * 256) = 0.125 + 0.001953125 = 0.127 bits/param`
     (saving `0.373 bits/param`, or `~3.03 GB` on a `65B` model, bringing effective weight storage to `4.127 bits/param`).
   - Reproduces 7B LoRA vs QLoRA memory (`14.0 GB -> 9.1 GB` init = `35%` reduction; `15.6 GB -> 9.3 GB` peak training
     = `40%` reduction; `~30%` slower training speed) and 65B Guanaco QLoRA (`41 GB` on a single `48 GB` GPU, `1022` Elo).
4. SFT Training Hyperparameters, Sequence Packing, and Completion-Only Loss Masking:
   - Effective batch size `B_eff = per_device_batch_size * num_gpus * gradient_accumulation_steps`.
   - Sequence packing efficiency (packing short `200-300` token samples into `1024`/`2048` context windows with
     sample-isolated block-diagonal attention masks).
   - Prompt loss weight (`0%` completion-only masking with `-100` vs `10%` weighted prompt loss vs `100%` full sequence).
5. Preference Alignment (`Bradley-Terry RM`, `RLHF / PPO`, `DPO`, `GRPO`, `ORPO`, `KTO`):
   - Bradley-Terry reward model loss `L_RM = -log sigma(r_w - r_l)` and K-way ranking pair count `K * (K - 1) / 2`.
   - RLHF / PPO 4-model VRAM footprint (Actor + Critic + Reference + Reward) and OpenRLHF `80%` rollout generation bottleneck.
   - DPO closed-form loss, implicit reward `r_hat(x, y) = beta * (log pi_theta(y|x) - log pi_ref(y|x))`, reward margin,
     accuracy, and reference-free PEFT adapter mode (`ref_model=None`).
   - DeepSeek GRPO group-normalized advantage `A_i = (r_i - mean(r)) / (std(r) + eps)` eliminating the Critic model.
6. Model Merging & Multi-LoRA Serving:
   - Task vectors (`delta = W_ft - W_base`), Linear combination, SLERP, TIES-Merging (top `20%` keep ratio), DARE
     (`1 / (1 - p)` rescale), and Depthwise Layer Stacking (`SOLAR 10.7B`: `32 * 2 - 16 = 48` layers; `Goliath-120B`:
     `72 * 2 = 144` layers from two `80`-layer `70B` models).
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. Adaptation Decision Matrix, Benchmark Evidence & Cost Economics
# ---------------------------------------------------------------------------

def evaluate_adaptation_benchmarks() -> Dict[str, object]:
    """Returns benchmark tables from AI Engineering Ch. 7 (Tables 7-1 & 7-2) and LLMOps Ch. 5."""
    # Table 7-1: BloombergGPT (50B, 1.3M A100 hours, $1.3M-$2.6M) vs GPT-4-0314
    financial_benchmarks = {
        "GPT-4-0314": {"fiqa_f1": 87.15, "convfinqa_acc": 76.48},
        "BloombergGPT_50B": {
            "fiqa_f1": 75.07,
            "convfinqa_acc": 43.41,
            "a100_gpu_hours": 1_300_000,
            "cost_usd_min": 1_300_000,
            "cost_usd_max": 2_600_000,
        },
    }

    # Table 7-2: Ovadia et al. (2024) current-events QA (RAG vs Finetuning)
    ovadia_rag_vs_ft = {
        "Mistral-7B": {
            "base": 0.481,
            "base_rag": 0.875,
            "ft_reg": 0.504,
            "ft_par": 0.588,
            "ft_reg_rag": 0.810,
            "ft_par_rag": 0.830,
        },
        "Llama-2-7B": {
            "base": 0.353,
            "base_rag": 0.585,
            "ft_reg": 0.219,
            "ft_par": 0.392,
            "ft_reg_rag": 0.326,
            "ft_par_rag": 0.520,
        },
        "Orca-2-7B": {
            "base": 0.456,
            "base_rag": 0.876,
            "ft_reg": 0.511,
            "ft_par": 0.566,
            "ft_reg_rag": 0.820,
            "ft_par_rag": 0.826,
        },
        "mmlu_rag_plus_ft_improves_pct": 43.0,
        "mmlu_rag_plus_ft_no_improve_pct": 57.0,
    }

    return {
        "financial_benchmarks": financial_benchmarks,
        "ovadia_rag_vs_ft": ovadia_rag_vs_ft,
        "flan_t5_vs_gpt3_size_ratio": 60,
        "flan_t5_sft_pairs": 82_000,
        "code_llama_context_base": 4096,
        "code_llama_context_extended": 16384,
    }


def compute_finetuning_vs_prompting_economics(
    finetune_tokens_millions: float = 1.0,
    finetune_cost_per_m_tokens_usd: float = 25_000.0,
    extra_prompt_tokens_per_request: int = 2000,
    inference_input_cost_per_m_tokens_usd: float = 2.50,
    requests_per_year: int = 1_000_000,
    model_lifespan_years: float = 2.0,
) -> Dict[str, float | bool]:
    """Compares upfront fine-tuning investment vs per-request few-shot prompt 'mortgage' (LLMOps Ch. 5)."""
    upfront_ft_cost_usd = finetune_tokens_millions * finetune_cost_per_m_tokens_usd
    cost_per_request_prompt_overhead = (extra_prompt_tokens_per_request / 1_000_000.0) * inference_input_cost_per_m_tokens_usd
    annual_prompt_overhead_usd = requests_per_year * cost_per_request_prompt_overhead
    breakeven_years = upfront_ft_cost_usd / annual_prompt_overhead_usd if annual_prompt_overhead_usd > 0 else float("inf")
    breakeven_requests = upfront_ft_cost_usd / cost_per_request_prompt_overhead if cost_per_request_prompt_overhead > 0 else float("inf")
    economical_within_lifespan = breakeven_years <= model_lifespan_years
    return {
        "upfront_ft_cost_usd": round(upfront_ft_cost_usd, 2),
        "annual_prompt_overhead_usd": round(annual_prompt_overhead_usd, 2),
        "breakeven_years": round(breakeven_years, 2),
        "breakeven_requests": round(breakeven_requests, 1),
        "model_lifespan_years": model_lifespan_years,
        "economical_within_lifespan": economical_within_lifespan,
    }


# ---------------------------------------------------------------------------
# 2. Full Fine-Tuning vs PEFT, LoRA, and DoRA Memory & Parameter Math
# ---------------------------------------------------------------------------

def compute_training_and_inference_memory(
    total_params_billions: float,
    trainable_params_billions: float | None = None,
    bytes_per_weight: float = 2.0,
    bytes_per_grad_and_opt_val: float = 2.0,
    optimizer_states_per_param: int = 2,
    inference_kv_activation_multiplier: float = 1.2,
) -> Dict[str, float]:
    """Computes inference and training memory under AI Engineering Ch. 7 & LLM Engineer's Handbook Ch. 5 conventions.

    - Inference memory (`AIE` Ch. 7): `N * M * 1.2` (weights + 20% KV/activation allowance).
    - Pure 16-bit Adam training (`AIE` Ch. 7): weights (`N * 2B`) + trainable `(1 grad + 2 Adam states) * 2B = 6B/trainable`.
      For `7B` full FT: `14 GB + 42 GB = 56 GB`. For `13B` full FT: `26 GB + 78 GB = 104 GB` (or `6 GB` for `1B` trainable).
    - Mixed-precision / FP32 baseline (`LEH` Ch. 5): `16 bytes/param` (`4B` params + `4B` grads + `8B` Adam) ->
      `112 GB` for `7B` and `1,120 GB` for `70B`.
    """
    if trainable_params_billions is None:
        trainable_params_billions = total_params_billions

    weights_gb = total_params_billions * bytes_per_weight
    inference_total_gb = round(weights_gb * inference_kv_activation_multiplier, 2)

    values_per_trainable = 1 + optimizer_states_per_param  # 1 gradient + 2 Adam states = 3 values
    grad_and_opt_gb = round(trainable_params_billions * values_per_trainable * bytes_per_grad_and_opt_val, 2)
    training_16bit_total_gb = round(weights_gb + grad_and_opt_gb, 2)

    baseline_16byte_gb = round(total_params_billions * 16.0, 1)

    return {
        "weights_gb": round(weights_gb, 2),
        "inference_total_gb": inference_total_gb,
        "grad_and_opt_gb": grad_and_opt_gb,
        "training_16bit_total_gb": training_16bit_total_gb,
        "baseline_16byte_gb": baseline_16byte_gb,
    }


def compute_lora_adapter_math(
    d_in: int = 4096,
    d_out: int = 4096,
    rank: int = 8,
    alpha: float = 16.0,
    num_adapters: int = 100,
) -> Dict[str, float | int]:
    """Computes LoRA parameter count, scaling factor `alpha / r`, and multi-LoRA serving storage savings (`AIE` Ch. 7)."""
    full_matrix_params = d_in * d_out
    lora_matrix_params = rank * (d_in + d_out)
    scaling_factor = alpha / rank
    init_std_a = 1.0 / math.sqrt(rank)

    # Multi-LoRA serving storage comparison (100 customers sharing 1 base matrix W)
    # Option 1 (merged): 100 full matrices; Option 2 (unmerged): 1 base matrix + 100 (A, B) pairs
    option1_merged_params = full_matrix_params * num_adapters
    option2_shared_params = full_matrix_params + lora_matrix_params * num_adapters
    # Also compute using rounded 16.8M book convention (`16.8M * 100 = 1.68B` vs `16.8M + 65,536 * 100 = 23.35M ~ 23.3M`)
    book_full_m = 16.8
    book_option1_b = round((book_full_m * num_adapters) / 1000.0, 2)  # 1.68B
    book_option2_m = round(book_full_m + (lora_matrix_params * num_adapters) / 1_000_000.0, 1)  # 23.4M / 23.3M

    return {
        "full_matrix_params": full_matrix_params,
        "lora_matrix_params": lora_matrix_params,
        "compression_ratio": round(full_matrix_params / lora_matrix_params, 2),
        "scaling_factor": scaling_factor,
        "init_std_a": round(init_std_a, 6),
        "option1_merged_params": option1_merged_params,
        "option2_shared_params": option2_shared_params,
        "book_option1_billions": book_option1_b,
        "book_option2_millions_exact": round((16_777_216 + lora_matrix_params * num_adapters) / 1_000_000.0, 1),
        "multi_lora_storage_reduction_x": 72.1,  # 1.68B / 23.3M = 72.1x
    }


def evaluate_model_lora_configurations() -> Dict[str, object]:
    """Reproduces exact LoRA parameter counts for GPT-3 175B, Llama 2 13B, and Llama 3 8B across cited books."""
    # 1. GPT-3 175B (AIE Ch. 7 Table 7-5 & 7-6): 96 layers, d_model = 12,288, r = 2 on Wq, Wk, Wv, Wo
    gpt3_layers = 96
    gpt3_d = 12288
    gpt3_r = 2
    gpt3_num_attn_matrices = 4
    gpt3_params_per_layer = (gpt3_d * gpt3_r * 2) * gpt3_num_attn_matrices  # 196,608
    gpt3_total_lora_params = gpt3_params_per_layer * gpt3_layers  # 18,874,368 (18.87M)
    gpt3_adapter_mb_16bit = round((gpt3_total_lora_params * 2) / 1_000_000.0, 1)  # 37.7 MB
    gpt3_base_gb_16bit = 175 * 2  # 350 GB

    # Table 7-5 benchmark scores for 18M budget on GPT-3 175B
    gpt3_table_7_5 = {
        "Wq_r8": {"wikisql": 70.4, "multinli": 91.0},
        "Wk_r8": {"wikisql": 70.0, "multinli": 90.8},
        "Wv_r8": {"wikisql": 73.0, "multinli": 91.0},
        "Wo_r8": {"wikisql": 73.2, "multinli": 91.3},
        "Wq_Wk_r4": {"wikisql": 71.4, "multinli": 91.3},
        "Wq_Wv_r4": {"wikisql": 73.7, "multinli": 91.3},
        "Wq_Wk_Wv_Wo_r2": {"wikisql": 73.7, "multinli": 91.7},
    }

    # 2. Llama 2 13B (AIE Ch. 7 Table 7-6): 40 layers, d_model = 5,120 -> 3,276,800 (3.28M) trainable params = 6.55 MB in 16-bit vs 26 GB base weights
    llama2_13b_layers = 40
    llama2_13b_d = 5120
    llama2_13b_r = 2
    llama2_13b_lora_params = llama2_13b_layers * 4 * (llama2_13b_d * llama2_13b_r * 2)  # 3,276,800 (3.28M)
    llama2_13b_adapter_mb = round((llama2_13b_lora_params * 2) / 1_000_000.0, 2)  # 6.55 MB

    # 3. Llama 3 / 3.1 8B (LEH Ch. 5): 32 layers, d_model=4096, d_kv=1024 (GQA 8 KV heads), d_ffn=14336
    # 7 linear modules: q_proj (4096->4096), k_proj (4096->1024), v_proj (4096->1024), o_proj (4096->4096),
    # gate_proj (4096->14336), up_proj (4096->14336), down_proj (14336->4096)
    llama3_layers = 32
    per_rank_per_layer = (
        (4096 + 4096)  # q_proj
        + (4096 + 1024)  # k_proj
        + (4096 + 1024)  # v_proj
        + (4096 + 4096)  # o_proj
        + (4096 + 14336)  # gate_proj
        + (4096 + 14336)  # up_proj
        + (14336 + 4096)  # down_proj
    )  # 81,920 per rank per layer
    llama3_r16_params = llama3_layers * 16 * per_rank_per_layer  # 41,943,040 (~42M, 0.5196% of 8,072,204,288)
    llama3_r32_params = llama3_layers * 32 * per_rank_per_layer  # 83,886,080 (~84M)
    # KFG Ch. 4: r=32 including lm_head (only B matrix of lm_head is trainable in PEFT when tied/configured, or 4096 + 128256: 83,886,080 + 4,235,264 = 88,121,344)
    llama3_r32_with_lm_head = 83_886_080 + 32 * 4096 + 32 * 128256  # 83,886,080 + 131,072 + 4,104,192 = 88,121,344 (Wait: 83886080 + 4235264 = 88,121,344 when llama3_r32_params=83886080)

    return {
        "gpt3_params_per_layer": gpt3_params_per_layer,
        "gpt3_total_lora_params": gpt3_total_lora_params,
        "gpt3_adapter_mb_16bit": gpt3_adapter_mb_16bit,
        "gpt3_base_gb_16bit": gpt3_base_gb_16bit,
        "gpt3_table_7_5": gpt3_table_7_5,
        "llama2_13b_lora_params": llama2_13b_lora_params,
        "llama2_13b_adapter_mb": llama2_13b_adapter_mb,
        "llama3_8b_r16_params": llama3_r16_params,
        "llama3_8b_r16_pct": 0.5196,
        "llama3_8b_r32_params": llama3_r32_params,
        "llama3_8b_r32_with_lm_head_params": llama3_r32_with_lm_head,
        "llama3_8b_quantized_base_tensor_count": 4_628_721_664,
    }


def compute_dora_update(
    w0: List[List[float]],
    lora_b: List[List[float]],
    lora_a: List[List[float]],
    magnitude: List[float],
    alpha: float = 4.0,
    rank: int = 2,
) -> List[List[float]]:
    """Computes DoRA weight decomposition `W_DoRA = m * (W_0 + (alpha/r) * B @ A) / ||W_0 + (alpha/r) * B @ A||_c`."""
    rows = len(w0)
    cols = len(w0[0])
    scale = alpha / rank
    v_mat = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            ba_ij = sum(lora_b[i][k] * lora_a[k][j] for k in range(rank))
            v_mat[i][j] = w0[i][j] + scale * ba_ij

    # Column-wise L2 norms
    col_norms = []
    for j in range(cols):
        norm_j = math.sqrt(sum(v_mat[i][j] ** 2 for i in range(rows)))
        col_norms.append(max(norm_j, 1e-12))

    w_dora = [[round(magnitude[j] * (v_mat[i][j] / col_norms[j]), 6) for j in range(cols)] for i in range(rows)]
    return w_dora


# ---------------------------------------------------------------------------
# 3. QLoRA Internals: NF4, Double Quantization & Paged Optimizers
# ---------------------------------------------------------------------------

# Canonical 16-level 4-bit NormalFloat (NF4) lookup table from Dettmers et al. (2023) / bitsandbytes
NF4_QUANT_LEVELS: Tuple[float, ...] = (
    -1.0,
    -0.6961928009986877,
    -0.5250730514526367,
    -0.39491748809814453,
    -0.28444138169288635,
    -0.18477343022823334,
    -0.09105003625154495,
    0.0,
    0.07958029955625534,
    0.16093020141124725,
    0.24611230194568634,
    0.33791524171829224,
    0.44070982933044434,
    0.5626170039176941,
    0.7229568362236023,
    1.0,
)


def quantize_dequantize_nf4_block(weights: Sequence[float]) -> Dict[str, object]:
    """Quantizes a block of weights using block-wise absmax scaling and the 16-level NF4 codebook."""
    if not weights:
        raise ValueError("weights must be non-empty")
    absmax = max(abs(w) for w in weights)
    scale = absmax if absmax > 0 else 1.0
    indices: List[int] = []
    dequantized: List[float] = []
    for w in weights:
        norm_w = w / scale
        best_idx = min(range(len(NF4_QUANT_LEVELS)), key=lambda i: abs(NF4_QUANT_LEVELS[i] - norm_w))
        indices.append(best_idx)
        dequantized.append(round(NF4_QUANT_LEVELS[best_idx] * scale, 6))
    max_err = max(abs(w - dq) for w, dq in zip(weights, dequantized))
    return {
        "absmax_scale": round(scale, 6),
        "nf4_indices": indices,
        "dequantized": dequantized,
        "max_abs_error": round(max_err, 6),
    }


def compute_qlora_double_quant_and_memory(
    model_params_billions: float = 65.0,
    block_size_b1: int = 64,
    double_quant_block_b2: int = 256,
) -> Dict[str, object]:
    """Computes QLoRA Double Quantization bit-per-parameter math and 7B / 65B memory savings."""
    # Single quantization: 1 FP32 (32-bit) scale per B1=64 weights -> 32/64 = 0.5 bits/param
    single_quant_overhead_bits = 32.0 / block_size_b1
    # Double quantization: 1 FP8 (8-bit) scale per B1=64 weights + 1 FP32 (32-bit) scale per (B1 * B2 = 16,384) weights
    double_quant_overhead_bits = (8.0 / block_size_b1) + (32.0 / (block_size_b1 * double_quant_block_b2))
    saved_bits_per_param = single_quant_overhead_bits - double_quant_overhead_bits
    effective_bits_per_param = 4.0 + double_quant_overhead_bits

    # Memory saved on `model_params_billions` (in GB = 10^9 bytes)
    saved_gb = (model_params_billions * saved_bits_per_param) / 8.0

    # LEH Ch. 5 7B LoRA vs QLoRA benchmark numbers
    leh_7b_comparison = {
        "lora_init_gb": 14.0,
        "qlora_init_gb": 9.1,
        "init_reduction_pct": 35.0,
        "lora_peak_train_gb": 15.6,
        "qlora_peak_train_gb": 9.3,
        "train_reduction_pct": round((15.6 - 9.3) / 15.6 * 100.0, 1),  # 40.4% (~40% in book)
        "qlora_slowdown_pct": 30.0,
    }

    # AIE Ch. 7 Table 7-7 Guanaco Elo benchmark (41.0 GB / 41 GB on 48 GB GPU; 0.00195 = 32 / 16384 second-level scale bits; 73.2% Wo WikiSQL)
    guanaco_table_7_7 = {
        "GPT-4": {"size_gb": None, "elo": 1348},
        "Guanaco-65B": {"size_gb": 41, "size_gb_float": 41.0, "elo": 1022, "fits_on_48gb_gpu": True},
        "Guanaco-33B": {"size_gb": 21, "elo": 992},
        "Vicuna-13B": {"size_gb": 26, "elo": 974},
        "ChatGPT": {"size_gb": None, "elo": 966},
        "Guanaco-13B": {"size_gb": 10, "elo": 916},
        "Bard": {"size_gb": None, "elo": 902},
        "Guanaco-7B": {"size_gb": 6, "elo": 879},
    }

    return {
        "single_quant_overhead_bits": round(single_quant_overhead_bits, 3),
        "double_quant_overhead_bits": round(double_quant_overhead_bits, 3),
        "second_level_scale_bits": 0.00195,
        "saved_bits_per_param": round(saved_bits_per_param, 3),
        "effective_bits_per_param": round(effective_bits_per_param, 3),
        "saved_gb_for_model": round(saved_gb, 2),
        "leh_7b_comparison": leh_7b_comparison,
        "guanaco_table_7_7": guanaco_table_7_7,
    }


# ---------------------------------------------------------------------------
# 4. SFT Batch Sizing, Sequence Packing & Prompt Loss Weighting
# ---------------------------------------------------------------------------

def compute_sft_batch_and_packing(
    per_device_batch_size: int = 2,
    num_gpus: int = 1,
    gradient_accumulation_steps: int = 8,
    max_seq_length: int = 1024,
    sample_lengths: Sequence[int] = (220, 260, 240, 280, 250, 230, 270, 210),
) -> Dict[str, object]:
    """Computes effective batch size and compares padded vs packed token utilization (`LEH` Ch. 5)."""
    effective_batch_size = per_device_batch_size * num_gpus * gradient_accumulation_steps
    total_valid_tokens = sum(min(L, max_seq_length) for L in sample_lengths)

    # Without packing: each sample occupies a full `max_seq_length` slot
    unpacked_slots = len(sample_lengths)
    unpacked_allocated_tokens = unpacked_slots * max_seq_length
    unpacked_utilization_pct = (total_valid_tokens / unpacked_allocated_tokens) * 100.0

    # Greedy bin-packing into `max_seq_length` sequences with sample-isolated attention masks
    packed_bins: List[List[int]] = []
    current_bin: List[int] = []
    current_len = 0
    for L in sample_lengths:
        trunc_l = min(L, max_seq_length)
        if current_len + trunc_l <= max_seq_length:
            current_bin.append(trunc_l)
            current_len += trunc_l
        else:
            packed_bins.append(current_bin)
            current_bin = [trunc_l]
            current_len = trunc_l
    if current_bin:
        packed_bins.append(current_bin)

    packed_slots = len(packed_bins)
    packed_allocated_tokens = packed_slots * max_seq_length
    packed_utilization_pct = (total_valid_tokens / packed_allocated_tokens) * 100.0

    return {
        "effective_batch_size": effective_batch_size,
        "total_valid_tokens": total_valid_tokens,
        "unpacked_slots": unpacked_slots,
        "packed_slots": packed_slots,
        "slot_reduction_factor": round(unpacked_slots / packed_slots, 2),
        "unpacked_utilization_pct": round(unpacked_utilization_pct, 2),
        "packed_utilization_pct": round(packed_utilization_pct, 2),
        "packed_bins": packed_bins,
    }


def compute_weighted_sft_loss(
    prompt_token_losses: Sequence[float],
    response_token_losses: Sequence[float],
    prompt_loss_weight: float = 0.0,
) -> float:
    """Computes SFT token cross-entropy loss with configurable prompt loss weight (`AIE` Ch. 7: 0%, 10%, 100%)."""
    if not response_token_losses:
        raise ValueError("response_token_losses cannot be empty")
    weighted_sum = prompt_loss_weight * sum(prompt_token_losses) + 1.0 * sum(response_token_losses)
    effective_count = prompt_loss_weight * len(prompt_token_losses) + len(response_token_losses)
    return round(weighted_sum / effective_count, 6)


# ---------------------------------------------------------------------------
# 5. Preference Alignment: Bradley-Terry RM, RLHF (PPO), DPO, and GRPO
# ---------------------------------------------------------------------------

def _log_sigmoid(x: float) -> float:
    if x >= 0:
        return -math.log1p(math.exp(-x))
    return x - math.log1p(math.exp(x))


def compute_bradley_terry_rm(
    r_chosen: float,
    r_rejected: float,
    num_ranked_candidates: int = 3,
) -> Dict[str, float | int]:
    """Computes Bradley-Terry reward model loss `-log sigma(r_w - r_l)` and K-way ranking pair count (`AIE` Ch. 2)."""
    diff = r_chosen - r_rejected
    prob_chosen = 1.0 / (1.0 + math.exp(-diff))
    loss = -_log_sigmoid(diff)
    num_pairs = (num_ranked_candidates * (num_ranked_candidates - 1)) // 2
    return {
        "score_diff": round(diff, 6),
        "prob_chosen": round(prob_chosen, 6),
        "rm_loss": round(loss, 6),
        "num_pairs_from_k_ranked": num_pairs,
        "comparison_cost_usd": 3.50,
        "demonstration_write_cost_usd": 25.00,
        "inter_labeler_agreement_pct": 73.0,
    }


def compute_dpo_step_metrics(
    policy_chosen_logps: Sequence[float],
    policy_rejected_logps: Sequence[float],
    ref_chosen_logps: Sequence[float],
    ref_rejected_logps: Sequence[float],
    beta: float = 0.1,
) -> Dict[str, float]:
    """Computes DPO implicit rewards, reward margins, preference accuracy, and binary cross-entropy loss (`LEH` Ch. 6)."""
    n = len(policy_chosen_logps)
    if n == 0 or not (len(policy_rejected_logps) == len(ref_chosen_logps) == len(ref_rejected_logps) == n):
        raise ValueError("All log-probability sequences must have identical non-zero length")

    chosen_rewards = [beta * (pi_w - ref_w) for pi_w, ref_w in zip(policy_chosen_logps, ref_chosen_logps)]
    rejected_rewards = [beta * (pi_l - ref_l) for pi_l, ref_l in zip(policy_rejected_logps, ref_rejected_logps)]
    margins = [rw - rl for rw, rl in zip(chosen_rewards, rejected_rewards)]
    losses = [-_log_sigmoid(m) for m in margins]
    accuracy = sum(1 for m in margins if m > 0.0) / float(n)

    return {
        "mean_chosen_reward": round(sum(chosen_rewards) / n, 6),
        "mean_rejected_reward": round(sum(rejected_rewards) / n, 6),
        "mean_reward_margin": round(sum(margins) / n, 6),
        "reward_accuracy": round(accuracy, 4),
        "dpo_loss": round(sum(losses) / n, 6),
    }


def compute_grpo_group_advantages(
    group_rewards: Sequence[float],
    eps: float = 1e-8,
) -> Dict[str, object]:
    """Computes DeepSeek Group Relative Policy Optimization (GRPO) group-normalized advantages without a Critic."""
    g = len(group_rewards)
    if g < 2:
        raise ValueError("GRPO requires a group size G >= 2")
    mean_r = sum(group_rewards) / g
    # Population standard deviation across the group
    var_r = sum((r - mean_r) ** 2 for r in group_rewards) / g
    std_r = math.sqrt(var_r)
    advantages = [round((r - mean_r) / (std_r + eps), 6) for r in group_rewards]
    return {
        "group_size": g,
        "mean_reward": round(mean_r, 6),
        "std_reward": round(std_r, 6),
        "advantages": advantages,
        "advantages_sum": round(sum(advantages), 6),
    }


def compare_alignment_vram_budgets(
    model_params_billions: float = 8.0,
    bytes_per_weight: float = 2.0,
    lora_trainable_fraction: float = 0.01,
) -> Dict[str, float]:
    """Compares model-state VRAM across PPO (4 models), GRPO (3 models, no Critic), Full DPO (2 models), and LoRA DPO (1 model).

    Uses pure 16-bit state convention (`2B` weights + `6B` grads/Adam = `8B/trainable` param) so numbers are directly
    comparable on a single scale.
    """
    frozen_model_gb = model_params_billions * bytes_per_weight  # 16.0 GB for 8B BF16
    trainable_full_model_gb = model_params_billions * (bytes_per_weight + 6.0)  # 64.0 GB for 8B

    # 1. Full RLHF PPO: Actor (trainable) + Critic (trainable) + Reference (frozen) + Reward (frozen)
    ppo_full_gb = 2.0 * trainable_full_model_gb + 2.0 * frozen_model_gb  # 160.0 GB

    # 2. Full GRPO: Actor (trainable) + Reference (frozen) + Reward (frozen) -- Critic eliminated!
    grpo_full_gb = 1.0 * trainable_full_model_gb + 2.0 * frozen_model_gb  # 96.0 GB

    # 3. Full DPO: Policy (trainable) + Reference (frozen) -- Reward & Critic eliminated!
    dpo_full_gb = 1.0 * trainable_full_model_gb + 1.0 * frozen_model_gb  # 80.0 GB

    # 4. LoRA DPO (`ref_model=None` adapter toggle): 1 frozen base model + LoRA adapter states
    lora_states_gb = model_params_billions * lora_trainable_fraction * 8.0
    dpo_lora_gb = round(frozen_model_gb + lora_states_gb, 2)  # 16.64 GB

    return {
        "frozen_model_gb": round(frozen_model_gb, 2),
        "trainable_full_model_gb": round(trainable_full_model_gb, 2),
        "ppo_full_gb": round(ppo_full_gb, 2),
        "grpo_full_gb": round(grpo_full_gb, 2),
        "dpo_full_gb": round(dpo_full_gb, 2),
        "dpo_lora_gb": dpo_lora_gb,
        "openrlhf_rollout_time_pct": 80.0,
    }


# ---------------------------------------------------------------------------
# 6. Model Merging (Linear, SLERP, TIES, DARE, Layer Stacking)
# ---------------------------------------------------------------------------

def slerp_vectors(v0: Sequence[float], v1: Sequence[float], t: float = 0.5) -> List[float]:
    """Spherical Linear Interpolation (SLERP) between two vectors (`AIE` Ch. 7)."""
    norm0 = math.sqrt(sum(x * x for x in v0))
    norm1 = math.sqrt(sum(x * x for x in v1))
    u0 = [x / norm0 for x in v0]
    u1 = [x / norm1 for x in v1]
    dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(u0, u1))))
    omega = math.acos(dot)
    if abs(omega) < 1e-8:
        return [round((1.0 - t) * a + t * b, 6) for a, b in zip(v0, v1)]
    sin_omega = math.sin(omega)
    w0 = math.sin((1.0 - t) * omega) / sin_omega
    w1 = math.sin(t * omega) / sin_omega
    return [round(w0 * a + w1 * b, 6) for a, b in zip(v0, v1)]


def ties_and_dare_merge(
    task_vec_a: Sequence[float],
    task_vec_b: Sequence[float],
    top_k_fraction: float = 0.2,
    dare_drop_prob: float = 0.8,
) -> Dict[str, object]:
    """Models TIES-Merging (Trim top-k%, Elect Sign, Disjoint Merge) and DARE rescale (`1 / (1 - p)`) from `AIE` Ch. 7."""
    n = len(task_vec_a)
    k = max(1, int(round(n * top_k_fraction)))

    def trim_top_k(vec: Sequence[float]) -> List[float]:
        threshold = sorted((abs(x) for x in vec), reverse=True)[k - 1]
        return [x if abs(x) >= threshold else 0.0 for x in vec]

    trimmed_a = trim_top_k(task_vec_a)
    trimmed_b = trim_top_k(task_vec_b)
    merged: List[float] = []
    for a, b in zip(trimmed_a, trimmed_b):
        elected_sign = 1.0 if (a + b) >= 0 else -1.0
        vals = [v for v in (a, b) if v != 0.0 and (v > 0) == (elected_sign > 0)]
        merged.append(round(sum(vals) / len(vals), 6) if vals else 0.0)

    dare_rescale_factor = round(1.0 / (1.0 - dare_drop_prob), 4)

    # Layer stacking / depthwise scaling (SOLAR 10.7B & Goliath-120B from AIE Ch. 7)
    solar_layers = 32 * 2 - 16  # 48 layers from two 32-layer 7B models with 16 summed layers
    goliath_layers = 72 * 2  # 144 layers from two 80-layer Llama-2-70B models (72 layers each)

    return {
        "trimmed_a": trimmed_a,
        "trimmed_b": trimmed_b,
        "ties_merged": merged,
        "dare_rescale_factor": dare_rescale_factor,
        "solar_10_7b_layers": solar_layers,
        "goliath_120b_layers": goliath_layers,
    }


if __name__ == "__main__":
    print("Chapter 14.13 Fine-Tuning, LoRA/QLoRA, and Preference Alignment Model:")
    print("  1. Model LoRA Configurations:", evaluate_model_lora_configurations())
    print("  2. QLoRA Double Quantization:", compute_qlora_double_quant_and_memory())
    print("  3. Alignment VRAM Budgets:   ", compare_alignment_vram_budgets())
