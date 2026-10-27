#!/usr/bin/env python3
"""
Chapter 14.2: Transformers and LLM Architecture
Deterministic infrastructure engineering models for:
  1. Transformer parameter counting (Embedding, MHA/GQA/MQA Attention, SwiGLU vs 2-Layer MLP, LM Head)
  2. Attention quadratic FLOPs (4 * B * s^2 * d_model) vs linear projection FLOPs & crossover sequence length
  3. KV cache byte footprint per token & total context (2 * n_layers * n_kv_heads * d_head * bytes_per_elem)
     across MHA, GQA, MQA, and DeepSeek MLA
  4. Dense vs Mixture-of-Experts (MoE) active vs total parameter and FLOPs math (Mixtral 8x7B, DeepSeek-V3, Jamba)
  5. Chinchilla compute-optimal scaling (D ~= 20 * N, C ~= 6 * N * D), training cluster time/cost (GPT-3 175B, 100T)
  6. Temperature-scaled softmax, logprobs, top-k / top-p (nucleus) sampling, and sequence average logprob
  7. Multilingual tokenization inflation and cost/latency impact (English=7, Hindi=32, Burmese=72)
"""

from dataclasses import dataclass
import math
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class TransformerSpec:
    name: str
    n_layers: int
    d_model: int
    d_ff: int
    n_heads: int
    n_kv_heads: int
    vocab_size: int
    context_len: int
    swiglu: bool = True
    tie_embeddings: bool = False
    norm_params_per_layer: int = 2  # input_layernorm + post_attention_layernorm (RMSNorm)

    @property
    def d_head(self) -> int:
        return self.d_model // self.n_heads


# Canonical model specs from AIE Ch 2 Table 2-4, AISPE Ch 17/18, and Hands-On LLM Serving Ch 2
LLAMA2_7B = TransformerSpec(
    name="Llama 2-7B (MHA)",
    n_layers=32,
    d_model=4096,
    d_ff=11008,
    n_heads=32,
    n_kv_heads=32,
    vocab_size=32000,
    context_len=4096,
    swiglu=True,
    tie_embeddings=False,
)

LLAMA2_13B = TransformerSpec(
    name="Llama 2-13B (MHA)",
    n_layers=40,
    d_model=5120,
    d_ff=13824,
    n_heads=40,
    n_kv_heads=40,
    vocab_size=32000,
    context_len=4096,
    swiglu=True,
    tie_embeddings=False,
)

LLAMA2_70B = TransformerSpec(
    name="Llama 2-70B (GQA-8)",
    n_layers=80,
    d_model=8192,
    d_ff=28672,  # AIE Table 2-4 lists 22,016 (Llama 2) and 28,672 (Llama 3-70B)
    n_heads=64,
    n_kv_heads=8,
    vocab_size=32000,
    context_len=4096,
    swiglu=True,
    tie_embeddings=False,
)

LLAMA3_8B = TransformerSpec(
    name="Llama 3-8B / 7B (GQA-8)",
    n_layers=32,
    d_model=4096,
    d_ff=14336,
    n_heads=32,
    n_kv_heads=8,
    vocab_size=128256,
    context_len=128000,
    swiglu=True,
    tie_embeddings=False,
)

LLAMA3_70B = TransformerSpec(
    name="Llama 3-70B (GQA-8)",
    n_layers=80,
    d_model=8192,
    d_ff=28672,
    n_heads=64,
    n_kv_heads=8,
    vocab_size=128256,
    context_len=128000,
    swiglu=True,
    tie_embeddings=False,
)

LLAMA3_405B = TransformerSpec(
    name="Llama 3-405B (GQA-8)",
    n_layers=126,
    d_model=16384,
    d_ff=53248,
    n_heads=128,
    n_kv_heads=8,
    vocab_size=128256,
    context_len=128000,
    swiglu=True,
    tie_embeddings=False,
)

QWEN25_05B = TransformerSpec(
    name="Qwen 2.5-0.5B (GQA-2)",
    n_layers=24,
    d_model=896,
    d_ff=4864,
    n_heads=14,
    n_kv_heads=2,
    vocab_size=151936,
    context_len=32768,
    swiglu=True,
    tie_embeddings=True,
)


def count_attention_params_per_layer(
    d_model: int, n_heads: int, n_kv_heads: int, d_head: int = None
) -> Dict[str, int]:
    """
    Count Q, K, V, O projection parameters for a single Transformer layer.
      - W_Q: d_model x (n_heads * d_head)
      - W_K: d_model x (n_kv_heads * d_head)
      - W_V: d_model x (n_kv_heads * d_head)
      - W_O: (n_heads * d_head) x d_model
    For standard MHA (n_kv_heads == n_heads and n_heads * d_head == d_model):
      total = 4 * d_model^2
    For GQA / MQA:
      total = 2 * d_model * (n_heads * d_head) + 2 * d_model * (n_kv_heads * d_head)
    """
    if d_head is None:
        d_head = d_model // n_heads
    q_params = d_model * (n_heads * d_head)
    k_params = d_model * (n_kv_heads * d_head)
    v_params = d_model * (n_kv_heads * d_head)
    o_params = (n_heads * d_head) * d_model
    total = q_params + k_params + v_params + o_params
    return {
        "q_proj": q_params,
        "k_proj": k_params,
        "v_proj": v_params,
        "o_proj": o_params,
        "total_attn_params": total,
    }


def count_mlp_params_per_layer(d_model: int, d_ff: int, swiglu: bool = True) -> Dict[str, int]:
    """
    Count Feedforward (MLP) parameters for a single Transformer layer:
      - Standard 2-layer MLP (ReLU/GELU): up_proj (d_model * d_ff) + down_proj (d_ff * d_model) = 2 * d_model * d_ff
      - SwiGLU 3-matrix MLP (gate_proj, up_proj, down_proj): 3 * d_model * d_ff
    """
    if swiglu:
        gate = d_model * d_ff
        up = d_model * d_ff
        down = d_ff * d_model
        return {
            "gate_proj": gate,
            "up_proj": up,
            "down_proj": down,
            "total_mlp_params": gate + up + down,
        }
    up = d_model * d_ff
    down = d_ff * d_model
    return {
        "gate_proj": 0,
        "up_proj": up,
        "down_proj": down,
        "total_mlp_params": up + down,
    }


def count_transformer_parameters(spec: TransformerSpec) -> Dict[str, int]:
    """Full parameter breakdown for a decoder-only Transformer."""
    embed_params = spec.vocab_size * spec.d_model
    lm_head_params = 0 if spec.tie_embeddings else (spec.vocab_size * spec.d_model)
    attn = count_attention_params_per_layer(
        spec.d_model, spec.n_heads, spec.n_kv_heads, spec.d_head
    )
    mlp = count_mlp_params_per_layer(spec.d_model, spec.d_ff, spec.swiglu)
    norm_per_layer = spec.norm_params_per_layer * spec.d_model
    final_norm = spec.d_model
    per_layer_total = attn["total_attn_params"] + mlp["total_mlp_params"] + norm_per_layer
    all_layers_total = spec.n_layers * per_layer_total
    total_params = embed_params + all_layers_total + final_norm + lm_head_params
    return {
        "embedding_params": embed_params,
        "lm_head_params": lm_head_params,
        "attn_params_per_layer": attn["total_attn_params"],
        "mlp_params_per_layer": mlp["total_mlp_params"],
        "norm_params_per_layer": norm_per_layer,
        "params_per_layer": per_layer_total,
        "all_layers_params": all_layers_total,
        "final_norm_params": final_norm,
        "total_params": total_params,
        "fp16_weight_bytes": total_params * 2,
    }


def compute_layer_forward_flops(
    batch_size: int,
    seq_len: int,
    d_model: int,
    d_ff: int,
    n_heads: int = 32,
    n_kv_heads: int = 32,
    swiglu: bool = True,
    causal_triangular: bool = False,
) -> Dict[str, float]:
    """
    Compute forward-pass FLOPs for one Transformer block at batch B and sequence length s:
      1. Q, K, V, O linear projections:
         2 * B * s * (2 * d_model^2 + 2 * d_model * d_kv)
         (for MHA where d_kv == d_model, this is 8 * B * s * d_model^2)
      2. Self-attention core (QK^T and Score * V):
         Full matrix form: 4 * B * s^2 * d_model (2 * B * s^2 * d_model for QK^T + 2 * B * s^2 * d_model for PV)
         If causal_triangular=True (fused causal kernel over valid tokens): ~ 2 * B * s^2 * d_model
      3. MLP projections:
         SwiGLU: 6 * B * s * d_model * d_ff (3 matmuls of 2 * B * s * d_model * d_ff)
         Standard 2-layer: 4 * B * s * d_model * d_ff
    """
    d_head = d_model // n_heads
    d_kv = n_kv_heads * d_head
    qkv_o_linear_flops = 2 * batch_size * seq_len * (2 * d_model * d_model + 2 * d_model * d_kv)
    attn_core_flops = (
        2 * batch_size * (seq_len * seq_len) * d_model
        if causal_triangular
        else 4 * batch_size * (seq_len * seq_len) * d_model
    )
    mlp_flops = (
        6 * batch_size * seq_len * d_model * d_ff
        if swiglu
        else 4 * batch_size * seq_len * d_model * d_ff
    )
    linear_total = qkv_o_linear_flops + mlp_flops
    total = linear_total + attn_core_flops
    # Crossover sequence length s* where full attention core FLOPs (4*B*s^2*d) == linear FLOPs
    # 4 * B * s * d_model = linear_total / (B * s) -> s_crossover = (linear_total / (B * s)) / (4 * d_model)
    per_token_linear = (2 * (2 * d_model * d_model + 2 * d_model * d_kv)) + (
        6 * d_model * d_ff if swiglu else 4 * d_model * d_ff
    )
    s_crossover = per_token_linear / (4.0 * d_model)
    return {
        "qkv_o_linear_flops": qkv_o_linear_flops,
        "attn_core_flops": attn_core_flops,
        "mlp_flops": mlp_flops,
        "linear_total_flops": linear_total,
        "total_layer_flops": total,
        "attn_core_share_pct": (attn_core_flops / total) * 100.0,
        "crossover_seq_len": s_crossover,
    }


def compute_triangular_qk_ops(seq_len: int) -> int:
    """
    From AISPE Ch 16 Table 16-6 / 16-7:
    Number of causal self-attention QK dot products for sequence length N is T(N) = N(N + 1) // 2.
    For N = 20,000 -> 200,010,000 (~200M).
    For N = 6,000 -> 18,003,000; N = 2,000 -> 2,001,000.
    """
    return (seq_len * (seq_len + 1)) // 2


def evaluate_fifo_vs_latency_aware_batches(
    arrivals: List[int] = None,
) -> Dict[str, float]:
    """
    Reproduce AISPE Ch 16 Table 16-6 & 16-7:
    Incoming prompts [6000, 2000, 6000, 2000, 2000, 2000] across 2 GPUs.
      - FIFO: GPU1=[6000, 2000, 6000] -> 38,007,000 QK ops (14K tokens); GPU2=[2000, 2000, 2000] -> 6,003,000 QK ops (6K tokens)
      - Latency-aware: GPU1=[2000, 2000, 6000] -> 22,005,000 QK ops (10K tokens); GPU2=[2000, 2000, 6000] -> 22,005,000 QK ops
      - Critical-path reduction: (38,007,000 - 22,005,000) / 38,007,000 = 42.10% (~42%)
    """
    if arrivals is None:
        arrivals = [6000, 2000, 6000, 2000, 2000, 2000]
    fifo_gpu1 = arrivals[:3]
    fifo_gpu2 = arrivals[3:]
    fifo_ops_1 = sum(compute_triangular_qk_ops(n) for n in fifo_gpu1)
    fifo_ops_2 = sum(compute_triangular_qk_ops(n) for n in fifo_gpu2)
    fifo_crit = max(fifo_ops_1, fifo_ops_2)

    balanced_gpu1 = [2000, 2000, 6000]
    balanced_gpu2 = [2000, 2000, 6000]
    bal_ops_1 = sum(compute_triangular_qk_ops(n) for n in balanced_gpu1)
    bal_ops_2 = sum(compute_triangular_qk_ops(n) for n in balanced_gpu2)
    bal_crit = max(bal_ops_1, bal_ops_2)

    reduction_pct = ((fifo_crit - bal_crit) / fifo_crit) * 100.0
    return {
        "fifo_gpu1_ops": fifo_ops_1,
        "fifo_gpu2_ops": fifo_ops_2,
        "fifo_critical_ops": fifo_crit,
        "balanced_gpu1_ops": bal_ops_1,
        "balanced_gpu2_ops": bal_ops_2,
        "balanced_critical_ops": bal_crit,
        "critical_path_reduction_pct": round(reduction_pct, 2),
    }


def compute_kv_cache_footprint(
    n_layers: int,
    n_kv_heads: int,
    d_head: int,
    bytes_per_elem: int = 2,
    seq_len: int = 4096,
    batch_size: int = 1,
) -> Dict[str, float]:
    """
    KV cache byte footprint formula from AISPE Ch 17 & Ch 18:
      bytes_per_token = 2 * n_layers * n_kv_heads * d_head * bytes_per_elem
      total_bytes = bytes_per_token * seq_len * batch_size
    """
    floats_per_layer_per_token = 2 * n_kv_heads * d_head
    floats_per_token = n_layers * floats_per_layer_per_token
    bytes_per_token = floats_per_token * bytes_per_elem
    total_bytes = bytes_per_token * seq_len * batch_size
    return {
        "floats_per_layer_per_token": floats_per_layer_per_token,
        "floats_per_token": floats_per_token,
        "bytes_per_token": bytes_per_token,
        "mb_per_token_decimal": bytes_per_token / 1e6,
        "total_bytes": total_bytes,
        "total_gb_decimal": total_bytes / 1e9,
        "total_gib_binary": total_bytes / (1024 ** 3),
    }


def compare_attention_kv_variants(
    n_layers: int = 40,
    n_heads: int = 40,
    d_head: int = 128,
    seq_len: int = 4096,
    gqa_groups: int = 8,
    mla_compressed_dim: int = 576,  # DeepSeek-V3/R1 kv_lora_rank (512) + qk_rope_head_dim (64) = 576 elements per layer
) -> Dict[str, Dict[str, float]]:
    """
    Compare KV cache footprints for AISPE Ch 17 13B model example (40 layers, 40 heads, d_head=128, seq=4096):
      - MHA (n_kv_heads=40): FP16 = 819,200 B/tok (~0.819 MB/tok), 3,355,443,200 B (~3.36 GB); FP8 = ~1.68 GB
      - GQA-8 (n_kv_heads=8): FP16 = 163,840 B/tok, 671,088,640 B (~0.671 GB); FP8 = ~0.336 GB (5x reduction vs MHA)
      - MQA (n_kv_heads=1): FP16 = 20,480 B/tok, 83,886,080 B (~0.084 GB) (40x reduction vs MHA)
      - DeepSeek MLA (compressed latent vector per layer = 576 elements instead of 2 * 40 * 128 = 10,240):
        40 * 576 * 2 B = 46,080 B/tok -> 188,743,680 B (~0.189 GB) at FP16 (17.78x reduction vs MHA)
    """
    mha_fp16 = compute_kv_cache_footprint(n_layers, n_heads, d_head, 2, seq_len)
    mha_fp8 = compute_kv_cache_footprint(n_layers, n_heads, d_head, 1, seq_len)
    gqa_fp16 = compute_kv_cache_footprint(n_layers, gqa_groups, d_head, 2, seq_len)
    gqa_fp8 = compute_kv_cache_footprint(n_layers, gqa_groups, d_head, 1, seq_len)
    mqa_fp16 = compute_kv_cache_footprint(n_layers, 1, d_head, 2, seq_len)
    mla_bytes_per_tok = n_layers * mla_compressed_dim * 2
    mla_total = mla_bytes_per_tok * seq_len
    return {
        "MHA_FP16": mha_fp16,
        "MHA_FP8": mha_fp8,
        "GQA8_FP16": gqa_fp16,
        "GQA8_FP8": gqa_fp8,
        "MQA_FP16": mqa_fp16,
        "MLA_FP16": {
            "bytes_per_token": mla_bytes_per_tok,
            "total_bytes": mla_total,
            "total_gb_decimal": mla_total / 1e9,
            "compression_vs_mha": mha_fp16["bytes_per_token"] / mla_bytes_per_tok,
        },
        "gqa_reduction_factor": mha_fp16["bytes_per_token"] / gqa_fp16["bytes_per_token"],
        "mqa_reduction_factor": mha_fp16["bytes_per_token"] / mqa_fp16["bytes_per_token"],
    }


def compute_moe_architecture_metrics(
    name: str,
    total_params_b: float,
    active_params_b: float,
    num_routed_experts: int,
    active_routed_experts: int,
    shared_experts: int = 0,
    bytes_per_param: int = 2,
) -> Dict[str, float]:
    """
    Compare Mixture-of-Experts (MoE) capacity vs active compute:
      - Total HBM weight footprint scales with total_params_b * bytes_per_param
      - Per-token forward/backward FLOPs scale with active_params_b (2 * N_active per token forward, 6 * N_active training)
      - Examples from AIE Ch 2 & AISPE Ch 1:
        * Mixtral 8x7B: 8 experts, 2 active -> 46.7B total (vs 8*7=56B unshared), 12.9B active
        * DeepSeek-V3 / R1: 256 routed experts (8 active) + 1 shared expert = 9 active experts -> 671B (~680B) total, 37B active
        * Jamba: 52B total, 12B active (256K context, fits in single 80 GB GPU)
    """
    total_active_experts = active_routed_experts + shared_experts
    total_experts = num_routed_experts + shared_experts
    active_param_ratio = active_params_b / total_params_b
    compute_savings_factor = total_params_b / active_params_b
    hbm_weight_gb = total_params_b * bytes_per_param
    fwd_flops_per_token_gflops = 2.0 * active_params_b
    train_flops_per_token_gflops = 6.0 * active_params_b
    return {
        "name": name,
        "total_params_b": total_params_b,
        "active_params_b": active_params_b,
        "num_routed_experts": num_routed_experts,
        "active_routed_experts": active_routed_experts,
        "shared_experts": shared_experts,
        "total_active_experts": total_active_experts,
        "total_experts": total_experts,
        "active_param_pct": round(active_param_ratio * 100.0, 2),
        "compute_savings_factor": round(compute_savings_factor, 2),
        "hbm_weight_gb": round(hbm_weight_gb, 2),
        "fwd_flops_per_token_gflops": round(fwd_flops_per_token_gflops, 2),
        "train_flops_per_token_gflops": round(train_flops_per_token_gflops, 2),
    }


def compute_chinchilla_scaling(
    params_b: float = None,
    compute_budget_flops: float = None,
    tokens_per_param_ratio: float = 20.0,
) -> Dict[str, float]:
    """
    Chinchilla compute-optimal scaling law (DeepMind 2022, AIE Ch 2, AISPE Ch 1):
      - D_opt ~= 20 * N
      - C ~= 6 * N * D
    If params_b is provided, calculates optimal training tokens D and total FLOPs C.
    If compute_budget_flops is provided, solves C = 6 * N * (20 * N) = 120 * N^2 for N and D.
    """
    if params_b is not None:
        n_params = params_b * 1e9
        d_tokens = tokens_per_param_ratio * n_params
        c_flops = 6.0 * n_params * d_tokens
    elif compute_budget_flops is not None:
        c_flops = compute_budget_flops
        n_params = math.sqrt(c_flops / (6.0 * tokens_per_param_ratio))
        d_tokens = tokens_per_param_ratio * n_params
    else:
        raise ValueError("Provide either params_b or compute_budget_flops")

    return {
        "params_b": n_params / 1e9,
        "optimal_tokens_b": d_tokens / 1e9,
        "optimal_tokens_t": d_tokens / 1e12,
        "compute_flops": c_flops,
    }


def estimate_training_cluster_cost(
    total_flops: float = 3.14e23,
    num_gpus: int = 256,
    gpu_tflops_fp32: float = 60.0,  # AIE Ch 2: 6e13 FLOP/s = 5.2e18 FLOPs/day
    flops_per_gpu_day: float = 5.2e18,
    utilization: float = 0.70,
    hourly_cost_per_gpu: float = 2.0,
) -> Dict[str, float]:
    """
    Reproduce AIE Ch 2 GPT-3-175B training time and cost calculation:
      - Total FLOPs = 3.14e23
      - 1 FLOP/s-day = 60 * 60 * 24 = 86,400 FLOPs
      - At 60 TFLOP/s (6e13 FLOP/s), 1 GPU delivers ~5.184e18 (~5.2e18) FLOPs/day
      - Ideal days on 256 H100s = 3.14e23 / (256 * 5.2e18) = 235.88 (~236 days, ~7.8 months)
      - AIE Ch 2 cost formula at 70% utilization (using 256 days in book equation):
        $2 * 256 * 24 * 256 / 0.7 = $4,493,714.29 (or with 235.88 ideal days: $4,140,662.29;
        with 3.14e23 / (256 * 6e13 * 86400) = 236.56 days -> $4,152,685.71;
        note AIE Ch 2 prints $4,142,811.43 from 236.0 days * 24 * 256 * 2 / 0.7)
    """
    seconds_per_day = 60 * 60 * 24
    exact_flops_per_day = gpu_tflops_fp32 * 1e12 * seconds_per_day
    ideal_days = total_flops / (num_gpus * flops_per_gpu_day)
    ideal_days_rounded = round(ideal_days)  # 236 days
    realized_days_from_rounded = ideal_days_rounded / utilization
    cost_from_236_days = (hourly_cost_per_gpu * num_gpus * 24 * ideal_days_rounded) / utilization
    return {
        "seconds_per_day": seconds_per_day,
        "exact_flops_per_gpu_day": exact_flops_per_day,
        "quoted_flops_per_gpu_day": flops_per_gpu_day,
        "ideal_days": ideal_days,
        "ideal_days_rounded": ideal_days_rounded,
        "ideal_months": round(ideal_days / 30.25, 1),
        "realized_days_at_util": realized_days_from_rounded,
        "cost_usd_at_util": round(cost_from_236_days, 2),
    }


def estimate_100t_model_footprint(
    total_params_t: float = 100.0,
    training_tokens_t: float = 29.0,
    bytes_per_param: int = 2,
    b200_hbm_gb: int = 180,
    b300_hbm_gb: int = 288,
    gpus_per_node: int = 8,
) -> Dict[str, float]:
    """
    Reproduce AISPE Ch 1 "Toward 100-Trillion-Parameter Models" metrics:
      - Dense training FLOPs: C ~= 6 * N * D = 6 * 1e14 * 2.9e13 = 1.74e28 FLOPs
      - Weight memory in FP16 (2 bytes): 100e12 * 2 B = 200 TB (200,000 GB)
      - Minimum B200 GPUs (180 GB HBM each) for weights alone: 200,000 / 180 = 1,111.1 (~1,110 GPUs, ~125-139 nodes)
      - Minimum B300 GPUs (288 GB HBM each) for weights alone: 200,000 / 288 = 694.4 (~695 GPUs, ~86-87 nodes)
    """
    c_flops = 6.0 * (total_params_t * 1e12) * (training_tokens_t * 1e12)
    weight_tb = (total_params_t * bytes_per_param)  # 100T * 2B = 200 TB
    weight_gb = weight_tb * 1000.0
    b200_gpus = math.ceil(weight_gb / b200_hbm_gb)
    b300_gpus = math.ceil(weight_gb / b300_hbm_gb)
    return {
        "training_flops": c_flops,
        "weight_memory_tb": weight_tb,
        "weight_memory_gb": weight_gb,
        "min_b200_gpus_exact": b200_gpus,
        "min_b300_gpus_exact": b300_gpus,
        "b300_nodes": math.ceil(b300_gpus / gpus_per_node),
    }


def softmax_with_temperature(logits: List[float], temperature: float = 1.0) -> List[float]:
    """
    Compute temperature-scaled softmax probabilities:
      p_i = exp(x_i / T) / sum_j exp(x_j / T)
    For T == 0, greedy argmax returns 1.0 on the maximum logit.
    Reproduces AIE Ch 2 example:
      logits = [1.0, 2.0]
      T = 1.0 -> [0.27, 0.73] (exact: 0.2689, 0.7311)
      T = 0.5 -> [0.12, 0.88] (exact: 0.1192, 0.8808)
    """
    if temperature <= 0.0:
        max_idx = max(range(len(logits)), key=lambda i: logits[i])
        return [1.0 if i == max_idx else 0.0 for i in range(len(logits))]
    scaled = [x / temperature for x in logits]
    m = max(scaled)
    exps = [math.exp(x - m) for x in scaled]
    s = sum(exps)
    return [e / s for e in exps]


def filter_top_k_top_p(
    token_probs: Dict[str, float], top_k: int = None, top_p: float = None
) -> List[Tuple[str, float]]:
    """
    Apply top-k and/or top-p (nucleus) filtering in descending probability order.
    Stops accumulating in top-p as soon as cumulative probability reaches/exceeds p.
    """
    sorted_items = sorted(token_probs.items(), key=lambda kv: kv[1], reverse=True)
    if top_k is not None:
        sorted_items = sorted_items[:top_k]
    if top_p is not None:
        kept = []
        cum = 0.0
        for tok, p in sorted_items:
            kept.append((tok, p))
            cum += p
            if cum >= top_p:
                break
        sorted_items = kept
    return sorted_items


def compute_sequence_logprob_metrics(token_probs: List[float]) -> Dict[str, float]:
    """
    Reproduce AIE Ch 2 sequence probability and logprob math:
      For token_probs = [0.2, 0.1, 0.3] ("I", "love", "food"):
      seq_prob = 0.2 * 0.1 * 0.3 = 0.006
      total_logprob = sum(ln(p_i))
      avg_logprob = total_logprob / len(token_probs)
    """
    seq_prob = 1.0
    total_logprob = 0.0
    for p in token_probs:
        seq_prob *= p
        total_logprob += math.log(p)
    avg_logprob = total_logprob / len(token_probs)
    return {
        "seq_prob": round(seq_prob, 6),
        "total_logprob": round(total_logprob, 6),
        "avg_logprob": round(avg_logprob, 6),
    }


def evaluate_multilingual_token_tax() -> Dict[str, Dict[str, float]]:
    """
    From AIE Ch 2 Table 2-1, Table 2-2, Table 2-3 & MASSIVE benchmark:
    MASSIVE dataset (1M short texts across 52 languages) median token lengths on GPT-4:
      - English: 7 tokens (1.0x baseline)
      - Hindi: 32 tokens (4.57x English)
      - Burmese: 72 tokens (10.29x, ~10x English latency & API token cost)
    Common Crawl representation (Lai et al., 2023 Table 2-1 & 2-2):
      - English: 45.8786% (45.88%) CC vs 18.15% world pop (ratio 0.40)
      - Russian: 5.9692% (5.97%), German: 5.8811% (5.88%), Chinese: 4.8747% (4.87%),
        Japanese: 4.7884% (4.79%), French: 4.7254% (4.73%), Spanish: 4.4690% (4.47%),
        Italian: 2.5712% (2.57%), Dutch: 2.0585% (2.06%), Polish: 1.6636% (1.66%),
        Portuguese: 1.1505% (1.15%), Vietnamese: 1.0299% (1.03%)
      - Punjabi: 0.0061% CC vs 1.41% world pop (ratio 231.56)
      - Swahili: 0.0077% CC vs 0.89% world pop (ratio 115.26)
      - Telugu: 0.0183% CC vs 1.19% world pop (ratio 64.89)
    Table 2-3 CLIP vs OpenCLIP ViT-B/32 accuracy (%):
      - ImageNet: 63.2% vs 62.9%, ImageNet v2: 62.6%, Birdsnap: 37.8% vs 46.0%,
        Country211: 17.8% vs 14.8%, Flower: 66.7% vs 66.0%, GTSRB: 32.2% vs 42.0%,
        Stanford Cars: 59.4% vs 79.3%, UCF101: 64.5% vs 63.1%
    Exact derived parameter & KV cache reference table:
      - Llama 2-7B: 6,476,267,520 all_layers_params, 13,476,831,232 FP16 bytes (67.11M attn + 135.27M SwiGLU vs 90.18M 2-matrix = 202.38M/layer)
      - Llama 3-8B: 176,160,768 SwiGLU/layer, 525,336,576 embed/head
      - Llama 2-13B: 13,015,864,320 params (13.02B, 26.03 GB FP16)
      - Llama 2-70B: 68,976,648,192 params (68.98B, 137.95 GB FP16)
      - Llama 3-70B: 70,553,706,496 params (70.55B, 141.11 GB FP16)
      - Llama 3-405B: 405,853,388,800 params (405.85B, 811.71 GB FP16)
      - Llama 2-7B linear FLOPs/tok: 404,750,336 (85.78% linear vs 14.22% attn core at s=4096)
      - 13B KV cache @ 4096 tok: MHA FP8 = 409,600 B/tok (0.410 MB), 1,677,721,600 B (1.68 GB);
        GQA-8 FP16 = 163,840 B/tok (0.164 MB), 671,088,640 B (0.671 GB);
        GQA-8 FP8 = 81,920 B/tok (0.082 MB), 335,544,320 B (0.336 GB);
        MQA FP16 = 20,480 B/tok (0.020 MB), 83,886,080 B (0.084 GB);
        MLA FP16 = 46,080 B/tok (0.046 MB), 188,743,680 B (0.189 GB)
    """
    en_tokens = 7
    hi_tokens = 32
    my_tokens = 72
    return {
        "English": {"median_tokens": en_tokens, "cost_latency_multiplier": 1.0, "cc_pct": 45.88, "pop_cc_ratio": 0.40},
        "Hindi": {
            "median_tokens": hi_tokens,
            "cost_latency_multiplier": round(hi_tokens / en_tokens, 2),
        },
        "Burmese": {
            "median_tokens": my_tokens,
            "cost_latency_multiplier": round(my_tokens / en_tokens, 2),
        },
        "Punjabi": {"cc_pct": 0.0061, "world_pop_pct": 1.41, "pop_cc_ratio": 231.56},
        "Swahili": {"cc_pct": 0.0077, "world_pop_pct": 0.89, "pop_cc_ratio": 115.26},
        "Telugu": {"cc_pct": 0.0183, "world_pop_pct": 1.19, "pop_cc_ratio": 64.89},
    }
