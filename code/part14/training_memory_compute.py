"""Chapter 14.3: Training memory and compute anatomy.

Pure Python 3 standard-library reference models for:
1. GPU Memory Consumers & Static Model State Breakdown (V13 Ch. 01 & Ch. 02, V05 Ch. 01, DAI Ch. 01, AISPE Ch. 13):
   - Precision byte sizes: FP32 (4 bytes: 1 sign, 8 exponent, 23 mantissa), BF16 (2 bytes: 1 sign, 8 exponent,
     7 mantissa), FP16 (2 bytes: 1 sign, 5 exponent, 10 mantissa), FP8 E4M3 / E5M2 / MXFP8 (1 byte),
     Int8 (1 byte), Int4 / NVFP4 (0.5 bytes).
   - Pure FP32 Adam/AdamW static state (V13 Ch. 01 & Ch. 02):
     * Model weights: 4 * Psi bytes (28 GB for 7B, 700 GB for 175B GPT-3 = 8.75x an 80 GB H100).
     * Gradients: 4 * Psi bytes (28 GB for 7B).
     * Adam momentum (m_t): 4 * Psi bytes (28 GB for 7B).
     * Adam variance (v_t): 4 * Psi bytes (28 GB for 7B).
     * Total FP32 Adam static state: 16 * Psi bytes (112 GB for 7B; 56 GB optimizer states alone).
   - Mixed-Precision (BF16/FP16 + FP32 Master Weights) AdamW static state (V05 Ch. 01, AISPE Ch. 13):
     * Model weights (BF16/FP16): 2 * Psi bytes (14 GB for 7B, 140 GB for 70B).
     * Gradients (BF16/FP16): 2 * Psi bytes (14 GB for 7B, 140 GB for 70B).
     * FP32 master weights: 4 * Psi bytes (28 GB for 7B, 280 GB for 70B).
     * FP32 Adam momentum (m_t): 4 * Psi bytes (28 GB for 7B, 280 GB for 70B).
     * FP32 Adam variance (v_t): 4 * Psi bytes (28 GB for 7B, 280 GB for 70B).
     * Total mixed-precision AdamW static state: (2 + 2 + 4 + 4 + 4) * Psi = 16 * Psi bytes
       (112 GB for 7B, 208 GB for 13B, 1,120 GB [~1.12 TB] for 70B, 2,800 GB [2.8 TB] for 175B);
       checkpoint on disk omits gradients and stores 14 * Psi bytes (980 GB for 70B).
   - Pure BF16 Adam teaching baseline (DAI Ch. 01 Fig 1.4):
     * BF16 weights (2 * Psi = 14 GB) + BF16 gradients (2 * Psi = 14 GB) + BF16 m_t & v_t (4 * Psi = 28 GB)
       = 8 * Psi bytes (56 GB static for 7B) + 12 GB activations = 68 GB peak during backward (54 GB forward,
       56 GB optimizer step; 64-72 GB range with 8-16 GB activations).
   - Optimizer state multipliers (DAI Ch. 01):
     * SGD: ~0x (scalar lr), SGD+Momentum / Nesterov / Adagrad / RMSProp / Lion: 1x,
       Adafactor: ~0.5x, Adam / AdamW / LAMB / Nadam / SparseAdam / AdaBelief: 2x, AMSGrad: 3x.
2. Transformer Activation Memory, FlashAttention & Activation Checkpointing (V13 Ch. 02, DAI Ch. 01, AISPE Ch. 13):
   - Megatron-LM / Korthikanti et al. standard per-layer transformer activation memory (BF16/FP16):
     A_layer = s * b * h * (34 + 5 * a * s / h) bytes, where s = sequence length, b = micro-batch size,
     h = hidden dimension, a = attention heads, and L = num_layers.
   - Standard attention score/dropout activation component per layer: 5 * s * b * a * s = 5 * b * a * s^2 bytes;
     non-attention (linear/MLP/norm) component per layer: 34 * s * b * h bytes.
   - FlashAttention / SDPA fused kernel eliminates the O(s^2) materialized attention matrix, reducing
     per-layer activation memory to 34 * s * b * h bytes (selective checkpointing equivalent).
   - Full activation checkpointing (`torch.utils.checkpoint`) stores only layer boundary inputs (2 * s * b * h bytes
     per layer in BF16/FP16) plus 1 layer's active recomputation working set, reducing total activation memory
     from O(L) to O(sqrt(L)) or O(1) active layer at ~30-33% (up to 30-50%) backward recompute overhead.
   - V13 Ch. 02 7B forward/backward example: 32 layers, batch=4, seq=2048, h=4096 -> 42 GB activations
     (FP32 weights 28 GB + 42 GB activations = 70 GB forward [87.5% of 80 GB H100]; 98 GB backward without
     checkpointing [OOM]; ~60-66 GB with activation checkpointing [5-10 GB recomputed activations];
     AMP cuts 98 GB -> 51 GB [14 GB weights + 21 GB activations + 14 GB grads + 2 GB FP32 loss/norm],
     reducing measured memory from 78.5 GB to 48.2 GB and boosting throughput from 1,000 to 1,280 tokens/sec).
3. Gradient Accumulation, Effective Global Batch & CUDA Caching Allocator Fragmentation (DAI Ch. 01, AISPE Ch. 13):
   - Global batch size (samples): B_global = b_micro * grad_accum_steps * DP_world_size.
   - Global batch tokens: T_global = s * b_micro * grad_accum_steps * DP_world_size.
   - Peak activation memory scales linearly with micro-batch size b_micro (1 / grad_accum_steps of single-step
     activation memory for a fixed global batch), while static model state (weights, gradients, optimizer states)
     is independent of b_micro.
   - PyTorch CUDA caching allocator (`PYTORCH_ALLOC_CONF=max_split_size_mb:256,roundup_power2_divisions:[256:1,512:2,1024:4,>:8],backend:cudaMallocAsync`):
     computes power-of-two sub-bucket rounding (e.g., 600 MB request in [512, 1024] with 2 divisions rounds up to
     768 MB) and fragmentation ratio = (reserved_bytes - allocated_bytes) / reserved_bytes.
4. Training Compute Anatomy: Forward/Backward FLOPs, Step Time, MFU & HFU (V13 Ch. 01, V13 Ch. 12, V05 Ch. 01):
   - Dense transformer FLOPs per token: 2 * Psi (forward) + 4 * Psi (backward: 2 * Psi input grads + 2 * Psi weight grads)
     = 6 * Psi model FLOPs per token; with full activation checkpointing (1 extra forward pass), hardware FLOPs
     per token = 8 * Psi.
   - GPT-3 175B example (V13 Ch. 01): 2 * 175e9 * 2048 * 2048 = 1.468e18 (~1.46e18) forward FLOPs; at 312 TFLOPS
     (A100), 1.46e18 / 312e12 = 4,679.49 s (~4,679 s = 77.99 min ~ 78 minutes) on 1 GPU vs 78 min / 128 GPUs
     = 36.56 s (~37 seconds).
   - MFU (Model FLOPs Utilization) = (6 * Psi * tokens_per_sec_per_gpu) / peak_hardware_flops.
   - HFU (Hardware FLOPs Utilization) = (8 * Psi * tokens_per_sec_per_gpu) / peak_hardware_flops (when full
     activation checkpointing is enabled, HFU = 4/3 * MFU = 1.3333 * MFU).
   - MLPerf iteration timing breakdown (AISPE Ch. 13 Table 13-6): 24.0 ms total step = 10.5 ms forward (43.8%)
     + 9.0 ms backward (37.5%) [19.5 ms compute = 81.3%] + 4.0 ms all-reduce (16.7%) + 0.5 ms other overhead (2.1%).
   - Transformer activation formula s * b * h * (34 + 5 * a * s / h) bytes:
     * Short context (7B, L=32, b=4, s=2048, h=4096, a=32): 1,140,850,688 B (1.1409 GB / 1.141 GB/layer)
       non-attention + 2,684,354,560 B (2.6844 GB / 2.684 GB/layer) attention matrix = 3,825,205,248 B
       (3.825 GB/layer) -> 122.4066 GB (122.41 GB) standard total across 32 layers; FlashAttention cuts
       to 36.5072 GB (36.51 GB, 70.18% savings); full activation checkpointing (2.1475 GB layer boundaries
       + 1.1409 GB active layer) cuts to 3.2883 GB (3.29 GB, 97.31% savings).
     * Long context (7B, L=32, b=2, s=8192, h=4096, a=32): 2,281,701,376 B (2.282 GB/layer) non-attention
       + 21,474,836,480 B (21.475 GB/layer, 687.1948 GB across 32 layers) attention matrix = 23,756,537,856 B
       (23.757 GB/layer) -> 760.2092 GB (760.21 GB) standard total; FlashAttention cuts to 73.0144 GB
       (73.01 GB, 90.40% savings); full activation checkpointing cuts to 6.5767 GB (6.58 GB, 99.13% savings).
     * Gradient accumulation (b_micro=2, K=8, DP=8, s=4096): cuts peak activation memory 8.0x from
       89.1288 GB (89.13 GB) down to 11.1411 GB (11.14 GB).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 1. Precision Formats, Optimizer Multipliers & Static Model State Breakdown
# ---------------------------------------------------------------------------

PRECISION_BYTES: Dict[str, float] = {
    "FP32": 4.0,
    "TF32": 4.0,       # 19-bit compute format stored in 32-bit (4-byte) container
    "BF16": 2.0,
    "FP16": 2.0,
    "FP8_E4M3": 1.0,
    "FP8_E5M2": 1.0,
    "MXFP8": 1.0,
    "INT8": 1.0,
    "INT4": 0.5,
    "NVFP4": 0.5,
}

# Optimizer state multipliers relative to parameter count (in native state precision) from DAI Ch. 01
OPTIMIZER_STATE_MULTIPLIERS: Dict[str, float] = {
    "SGD": 0.0,
    "SGD_Momentum": 1.0,
    "Nesterov": 1.0,
    "Adagrad": 1.0,
    "RMSProp": 1.0,
    "Lion": 1.0,
    "Adafactor": 0.5,
    "Adam": 2.0,
    "AdamW": 2.0,
    "LAMB": 2.0,
    "Nadam": 2.0,
    "SparseAdam": 2.0,
    "AdaBelief": 2.0,
    "AMSGrad": 3.0,
}


@dataclass(frozen=True)
class StaticTrainingMemoryBreakdown:
    params_billions: float
    mode: str
    weights_gb: float
    gradients_gb: float
    master_weights_gb: float
    optimizer_m_gb: float
    optimizer_v_gb: float
    optimizer_total_gb: float
    static_training_total_gb: float
    checkpoint_disk_gb: float
    bytes_per_param_training: float
    bytes_per_param_checkpoint: float


def calculate_static_training_memory(
    params_billions: float = 7.0,
    mode: str = "mixed_bf16_fp32_adamw",
) -> StaticTrainingMemoryBreakdown:
    """Compute static GPU memory (weights, gradients, master weights, optimizer state) in decimal GB (10^9 bytes).

    Supported modes:
    - 'fp32_adam': 4B weights + 4B grads + 4B m + 4B v = 16B/param (V13 Ch. 01 & Ch. 02: 7B -> 28+28+56 = 112 GB)
    - 'mixed_bf16_fp32_adamw': 2B BF16 weights + 2B BF16 grads + 4B FP32 master + 4B FP32 m + 4B FP32 v = 16B/param
      (V05 Ch. 01, AISPE Ch. 13: 7B -> 14+14+28+28+28 = 112 GB; 70B -> 1,120 GB training, 980 GB checkpoint)
    - 'bf16_all_adam': 2B BF16 weights + 2B BF16 grads + 2B BF16 m + 2B BF16 v = 8B/param
      (DAI Ch. 01 Fig 1.4: 7B -> 14+14+28 = 56 GB static)
    - 'mixed_bf16_sgd': 2B BF16 weights + 2B BF16 grads + 4B FP32 master = 8B/param (0B momentum state)
    """
    if params_billions <= 0:
        raise ValueError("params_billions must be positive")

    if mode == "fp32_adam":
        w = 4.0 * params_billions
        g = 4.0 * params_billions
        mw = 0.0
        m = 4.0 * params_billions
        v = 4.0 * params_billions
        opt_tot = m + v
        tot = w + g + opt_tot
        ckpt = w + opt_tot
        b_train = 16.0
        b_ckpt = 12.0
    elif mode == "mixed_bf16_fp32_adamw":
        w = 2.0 * params_billions
        g = 2.0 * params_billions
        mw = 4.0 * params_billions
        m = 4.0 * params_billions
        v = 4.0 * params_billions
        opt_tot = mw + m + v
        tot = w + g + opt_tot
        ckpt = w + opt_tot  # 14 bytes/param (2B BF16 weights + 12B FP32 optimizer state, omitting gradients)
        b_train = 16.0
        b_ckpt = 14.0
    elif mode == "bf16_all_adam":
        w = 2.0 * params_billions
        g = 2.0 * params_billions
        mw = 0.0
        m = 2.0 * params_billions
        v = 2.0 * params_billions
        opt_tot = m + v
        tot = w + g + opt_tot
        ckpt = w + opt_tot
        b_train = 8.0
        b_ckpt = 6.0
    elif mode == "mixed_bf16_sgd":
        w = 2.0 * params_billions
        g = 2.0 * params_billions
        mw = 4.0 * params_billions
        m = 0.0
        v = 0.0
        opt_tot = mw
        tot = w + g + opt_tot
        ckpt = w + opt_tot
        b_train = 8.0
        b_ckpt = 6.0
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return StaticTrainingMemoryBreakdown(
        params_billions=round(params_billions, 4),
        mode=mode,
        weights_gb=round(w, 4),
        gradients_gb=round(g, 4),
        master_weights_gb=round(mw, 4),
        optimizer_m_gb=round(m, 4),
        optimizer_v_gb=round(v, 4),
        optimizer_total_gb=round(opt_tot, 4),
        static_training_total_gb=round(tot, 4),
        checkpoint_disk_gb=round(ckpt, 4),
        bytes_per_param_training=b_train,
        bytes_per_param_checkpoint=b_ckpt,
    )


def evaluate_dai_7b_memory_timeline(
    params_billions: float = 7.0,
    activations_gb: float = 12.0,
) -> Dict[str, float]:
    """Reproduce DAI Ch. 01 Figure 1.4 training step memory timeline for a 7B model with pure-BF16 Adam."""
    if params_billions <= 0 or activations_gb < 0:
        raise ValueError("Invalid parameters for memory timeline")
    base = calculate_static_training_memory(params_billions=params_billions, mode="bf16_all_adam")
    # Forward: weights (14 GB) + optimizer states from previous step (28 GB) + activations (12 GB) = 54 GB
    forward_gb = base.weights_gb + base.optimizer_total_gb + activations_gb
    # Backward (peak): weights (14 GB) + optimizer states (28 GB) + activations (12 GB) + gradients (14 GB) = 68 GB
    backward_peak_gb = forward_gb + base.gradients_gb
    # Optimizer step (activations freed): weights (14 GB) + optimizer states (28 GB) + gradients (14 GB) = 56 GB
    optimizer_step_gb = base.weights_gb + base.optimizer_total_gb + base.gradients_gb
    return {
        "weights_gb": base.weights_gb,
        "gradients_gb": base.gradients_gb,
        "optimizer_states_gb": base.optimizer_total_gb,
        "fixed_static_gb": base.static_training_total_gb,
        "activations_gb": round(activations_gb, 4),
        "forward_pass_gb": round(forward_gb, 4),
        "backward_peak_gb": round(backward_peak_gb, 4),
        "optimizer_step_gb": round(optimizer_step_gb, 4),
        "range_min_gb": round(base.static_training_total_gb + 8.0, 4),
        "range_max_gb": round(base.static_training_total_gb + 16.0, 4),
    }


def evaluate_v13_ch02_7b_scenarios() -> Dict[str, float]:
    """Reproduce V13 Ch. 02 7B model memory numbers across FP32, Activation Checkpointing, and AMP."""
    weights_fp32_gb = 7.0 * 4.0          # 28 GB
    activations_fp32_gb = 42.0           # 32 layers, b=4, s=2048, h=4096 -> ~42 GB
    gradients_fp32_gb = 7.0 * 4.0        # 28 GB
    forward_fp32_gb = weights_fp32_gb + activations_fp32_gb  # 70 GB (87.5% of 80 GB H100)
    backward_no_ckpt_gb = forward_fp32_gb + gradients_fp32_gb  # 98 GB (OOM on 80 GB H100)
    backward_ckpt_low_gb = weights_fp32_gb + gradients_fp32_gb + 4.0   # ~60 GB (with ~4-5 GB recomputed peak)
    backward_ckpt_high_gb = weights_fp32_gb + gradients_fp32_gb + 10.0  # 66 GB (with 10 GB recomputed peak)
    optimizer_fp32_peak_gb = 28.0 * 4.0  # 112 GB (weights + grads + m + v)

    # AMP breakdown (V13 Ch. 02)
    amp_weights_gb = 14.0
    amp_activations_gb = 21.0
    amp_gradients_gb = 14.0
    amp_loss_norm_fp32_gb = 2.0
    amp_total_gb = amp_weights_gb + amp_activations_gb + amp_gradients_gb + amp_loss_norm_fp32_gb  # 51 GB

    return {
        "weights_fp32_gb": weights_fp32_gb,
        "activations_fp32_gb": activations_fp32_gb,
        "forward_fp32_gb": forward_fp32_gb,
        "h100_80gb_forward_util_pct": round(forward_fp32_gb / 80.0 * 100.0, 2),
        "backward_no_ckpt_gb": backward_no_ckpt_gb,
        "backward_ckpt_60_gb": backward_ckpt_low_gb,
        "backward_ckpt_66_gb": backward_ckpt_high_gb,
        "optimizer_fp32_peak_gb": optimizer_fp32_peak_gb,
        "amp_total_gb": amp_total_gb,
        "measured_no_amp_gb": 78.5,
        "measured_with_amp_gb": 48.2,
        "measured_no_amp_tok_s": 1000.0,
        "measured_with_amp_tok_s": 1280.0,
        "amp_speedup_pct": round((1280.0 - 1000.0) / 1000.0 * 100.0, 2),
    }


# ---------------------------------------------------------------------------
# 2. Transformer Activation Memory, FlashAttention & Activation Checkpointing
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TransformerActivationBreakdown:
    seq_len: int
    micro_batch_size: int
    hidden_dim: int
    num_heads: int
    num_layers: int
    non_attention_bytes_per_layer: int
    attention_score_bytes_per_layer: int
    standard_bytes_per_layer: int
    standard_total_gb: float
    flash_attention_bytes_per_layer: int
    flash_attention_total_gb: float
    full_checkpoint_total_gb: float
    flash_savings_pct: float
    full_checkpoint_savings_pct: float


def calculate_transformer_activation_memory(
    seq_len: int = 2048,
    micro_batch_size: int = 4,
    hidden_dim: int = 4096,
    num_heads: int = 32,
    num_layers: int = 32,
) -> TransformerActivationBreakdown:
    """Calculate exact transformer activation memory per layer and across L layers (Korthikanti et al. formula).

    Per transformer layer in 16-bit mixed precision (BF16/FP16):
      - Non-attention activations (QKV projections, output proj, MLP SwiGLU/GeLU, LayerNorms, residuals):
        34 * s * b * h bytes
      - Materialized attention matrix (QK^T softmax probabilities, attention dropout mask, dropout output):
        5 * a * b * s^2 = s * b * h * (5 * a * s / h) bytes
      - Total standard per-layer activation memory:
        s * b * h * (34 + 5 * a * s / h) bytes
      - With FlashAttention / SDPA (or selective activation checkpointing of attention):
        the 5 * a * b * s^2 term is recomputed on-chip in SRAM tiles, leaving 34 * s * b * h bytes/layer.
      - With Full Activation Checkpointing (saving only 2 * s * b * h layer-boundary inputs per layer +
        1 active layer's FlashAttention working set during backward):
        total bytes = L * (2 * s * b * h) + (34 * s * b * h).
    """
    if min(seq_len, micro_batch_size, hidden_dim, num_heads, num_layers) <= 0:
        raise ValueError("All transformer dimensions must be positive integers")

    s, b, h, a, L = seq_len, micro_batch_size, hidden_dim, num_heads, num_layers
    non_attn_layer = 34 * s * b * h
    attn_layer = 5 * a * b * (s ** 2)
    std_layer = non_attn_layer + attn_layer

    std_total_bytes = L * std_layer
    flash_total_bytes = L * non_attn_layer
    # Full checkpointing: save 2*s*b*h boundary input per layer + 1 layer active working set (34*s*b*h)
    full_ckpt_bytes = L * (2 * s * b * h) + non_attn_layer

    std_gb = std_total_bytes / 1e9
    flash_gb = flash_total_bytes / 1e9
    ckpt_gb = full_ckpt_bytes / 1e9

    flash_sav = (1.0 - flash_total_bytes / std_total_bytes) * 100.0
    ckpt_sav = (1.0 - full_ckpt_bytes / std_total_bytes) * 100.0

    return TransformerActivationBreakdown(
        seq_len=s,
        micro_batch_size=b,
        hidden_dim=h,
        num_heads=a,
        num_layers=L,
        non_attention_bytes_per_layer=non_attn_layer,
        attention_score_bytes_per_layer=attn_layer,
        standard_bytes_per_layer=std_layer,
        standard_total_gb=round(std_gb, 4),
        flash_attention_bytes_per_layer=non_attn_layer,
        flash_attention_total_gb=round(flash_gb, 4),
        full_checkpoint_total_gb=round(ckpt_gb, 4),
        flash_savings_pct=round(flash_sav, 2),
        full_checkpoint_savings_pct=round(ckpt_sav, 2),
    )


# ---------------------------------------------------------------------------
# 3. Gradient Accumulation, Global Batch & CUDA Caching Allocator Bucketing
# ---------------------------------------------------------------------------

def size_gradient_accumulation_and_batch(
    seq_len: int = 4096,
    micro_batch_size: int = 2,
    grad_accum_steps: int = 8,
    dp_world_size: int = 8,
    single_micro_batch_activation_gb: float = 11.1411,
) -> Dict[str, float]:
    """Calculate effective global batch size (samples & tokens) and activation memory savings from grad accumulation."""
    if min(seq_len, micro_batch_size, grad_accum_steps, dp_world_size) <= 0 or single_micro_batch_activation_gb <= 0:
        raise ValueError("Batch sizing inputs must be positive")

    per_gpu_effective_batch = micro_batch_size * grad_accum_steps
    global_batch_samples = per_gpu_effective_batch * dp_world_size
    global_batch_tokens = global_batch_samples * seq_len
    unaccumulated_activation_gb = single_micro_batch_activation_gb * grad_accum_steps

    return {
        "micro_batch_size": float(micro_batch_size),
        "grad_accum_steps": float(grad_accum_steps),
        "dp_world_size": float(dp_world_size),
        "per_gpu_effective_batch_samples": float(per_gpu_effective_batch),
        "global_batch_samples": float(global_batch_samples),
        "global_batch_tokens": float(global_batch_tokens),
        "peak_activation_with_accum_gb": round(single_micro_batch_activation_gb, 4),
        "peak_activation_without_accum_gb": round(unaccumulated_activation_gb, 4),
        "activation_reduction_factor": float(grad_accum_steps),
    }


def simulate_cuda_allocator_rounding(
    request_mb: float = 600.0,
    divisions_config: Dict[int, int] | None = None,
) -> Dict[str, float]:
    """Simulate PyTorch CUDA caching allocator `roundup_power2_divisions` (AISPE Ch. 13).

    Default config from AISPE Ch. 13:
      roundup_power2_divisions:[256:1,512:2,1024:4,>:8]
    For example, in the [512, 1024] MB range with 2 divisions, step_mb = (1024 - 512) / 2 = 256 MB,
    so buckets are [512, 768, 1024] MB and a 600 MB request rounds up to 768 MB.
    """
    if request_mb <= 0:
        raise ValueError("request_mb must be positive")
    if divisions_config is None:
        divisions_config = {256: 1, 512: 2, 1024: 4, 2048: 8}

    low_pow2 = 1 << int(math.floor(math.log2(request_mb)))
    if low_pow2 == request_mb:
        return {
            "request_mb": round(request_mb, 2),
            "bucket_low_mb": float(low_pow2),
            "bucket_high_mb": float(low_pow2),
            "divisions": 1.0,
            "rounded_allocation_mb": float(low_pow2),
            "internal_fragmentation_mb": 0.0,
            "internal_fragmentation_pct": 0.0,
        }

    high_pow2 = low_pow2 * 2
    divs = divisions_config.get(low_pow2, divisions_config.get(2048, 8))
    step_mb = (high_pow2 - low_pow2) / divs
    k = math.ceil((request_mb - low_pow2) / step_mb)
    rounded_mb = low_pow2 + k * step_mb
    frag_mb = rounded_mb - request_mb
    frag_pct = (frag_mb / rounded_mb) * 100.0

    return {
        "request_mb": round(request_mb, 2),
        "bucket_low_mb": float(low_pow2),
        "bucket_high_mb": float(high_pow2),
        "divisions": float(divs),
        "step_mb": float(step_mb),
        "rounded_allocation_mb": round(rounded_mb, 2),
        "internal_fragmentation_mb": round(frag_mb, 2),
        "internal_fragmentation_pct": round(frag_pct, 2),
    }


# ---------------------------------------------------------------------------
# 4. Training Compute Anatomy: Step FLOPs, Scaling Time, MFU & HFU
# ---------------------------------------------------------------------------

def calculate_training_step_flops_and_mfu(
    params_billions: float = 70.0,
    tokens_per_sec_per_gpu: float = 940.0,
    gpu_peak_tflops: float = 989.0,
    activation_checkpointing: bool = True,
) -> Dict[str, float]:
    """Compute per-token FLOPs (2*Psi fwd, 4*Psi bwd, 6*Psi model, 8*Psi hardware with ckpt) and MFU/HFU."""
    if params_billions <= 0 or tokens_per_sec_per_gpu <= 0 or gpu_peak_tflops <= 0:
        raise ValueError("All compute parameters must be positive")

    psi = params_billions * 1e9
    fwd_flops_per_token = 2.0 * psi
    bwd_flops_per_token = 4.0 * psi
    model_flops_per_token = 6.0 * psi
    hw_flops_per_token = 8.0 * psi if activation_checkpointing else 6.0 * psi

    achieved_model_tflops = (model_flops_per_token * tokens_per_sec_per_gpu) / 1e12
    achieved_hw_tflops = (hw_flops_per_token * tokens_per_sec_per_gpu) / 1e12

    mfu_pct = (achieved_model_tflops / gpu_peak_tflops) * 100.0
    hfu_pct = (achieved_hw_tflops / gpu_peak_tflops) * 100.0

    return {
        "fwd_flops_per_token_gflops": round(fwd_flops_per_token / 1e9, 4),
        "bwd_flops_per_token_gflops": round(bwd_flops_per_token / 1e9, 4),
        "model_flops_per_token_gflops": round(model_flops_per_token / 1e9, 4),
        "hw_flops_per_token_gflops": round(hw_flops_per_token / 1e9, 4),
        "achieved_model_tflops": round(achieved_model_tflops, 2),
        "achieved_hw_tflops": round(achieved_hw_tflops, 2),
        "mfu_pct": round(mfu_pct, 2),
        "hfu_pct": round(hfu_pct, 2),
    }


def evaluate_gpt3_175b_step_scaling(
    params_billions: float = 175.0,
    batch_size: int = 2048,
    seq_len: int = 2048,
    a100_tflops: float = 312.0,
    cluster_gpus: int = 128,
) -> Dict[str, float]:
    """Reproduce V13 Ch. 01 GPT-3 175B single-GPU vs 128-GPU step time calculation."""
    if params_billions <= 0 or batch_size <= 0 or seq_len <= 0 or a100_tflops <= 0 or cluster_gpus <= 0:
        raise ValueError("All GPT-3 scaling inputs must be positive")

    exact_flops = 2.0 * (params_billions * 1e9) * batch_size * seq_len  # 1.4680064e18
    # V13 Ch. 01 rounds 2 * 175B * 2048 * 2048 to 1.46e18 FLOPs:
    v13_rounded_flops = 1.46e18
    single_gpu_sec = v13_rounded_flops / (a100_tflops * 1e12)  # 4679.487... -> ~4679 s (~78 min)
    single_gpu_min = single_gpu_sec / 60.0
    cluster_step_sec = (78.0 * 60.0) / cluster_gpus            # 78 min / 128 = 36.5625 s (~37 s)

    return {
        "weights_fp32_gb": round(params_billions * 4.0, 2),
        "h100_80gb_overflow_factor": round((params_billions * 4.0) / 80.0, 2),
        "exact_pass_eflops": round(exact_flops / 1e18, 4),
        "v13_pass_eflops": 1.46,
        "single_gpu_seconds": round(single_gpu_sec, 2),
        "single_gpu_seconds_int": int(round(single_gpu_sec)),
        "single_gpu_minutes_int": int(round(single_gpu_min)),
        "cluster_128_gpu_seconds": round(cluster_step_sec, 2),
        "cluster_128_gpu_seconds_int": int(round(cluster_step_sec)),
    }


def evaluate_mlperf_step_timing_breakdown(
    forward_ms: float = 10.5,
    backward_ms: float = 9.0,
    allreduce_ms: float = 4.0,
    other_ms: float = 0.5,
) -> Dict[str, float]:
    """Reproduce AISPE Ch. 13 Table 13-6 MLPerf training iteration timing breakdown."""
    total_ms = forward_ms + backward_ms + allreduce_ms + other_ms
    compute_ms = forward_ms + backward_ms
    fwd_pct = round(forward_ms / total_ms * 100.0, 1)
    bwd_pct = round(backward_ms / total_ms * 100.0, 1)
    return {
        "total_step_ms": round(total_ms, 2),
        "compute_ms": round(compute_ms, 2),
        "forward_pct": fwd_pct,
        "backward_pct": bwd_pct,
        "compute_pct": round(fwd_pct + bwd_pct, 1),
        "allreduce_pct": round(allreduce_ms / total_ms * 100.0, 1),
        "other_pct": round(other_ms / total_ms * 100.0, 1),
    }


def evaluate_ring_allreduce_vs_tree_cost(
    num_gpus_node: int = 8,
    num_gpus_cluster: int = 512,
    gradient_size_gb: float = 28.0,
    nvlink_bw_gb_s: float = 900.0,
    ib_bw_gb_s: float = 25.0,
) -> Dict[str, float]:
    """Reproduce V13 Ch. 08 Ring vs Tree All-Reduce cost model at 8 GPUs (NVLink) and 512 GPUs (InfiniBand)."""
    ring_8_data_gb = 2.0 * ((num_gpus_node - 1.0) / num_gpus_node) * gradient_size_gb       # 49.0 GB
    ring_8_time_ms = (ring_8_data_gb / nvlink_bw_gb_s) * 1000.0                             # 54.44 ms (~54 ms)

    ring_512_data_gb = 2.0 * ((num_gpus_cluster - 1.0) / num_gpus_cluster) * gradient_size_gb  # 55.8906 GB (~55.9 GB)
    ring_512_time_s = ring_512_data_gb / ib_bw_gb_s                                            # 2.2356 s (~2.2 s)
    tree_512_hops = int(math.log2(num_gpus_cluster))                                           # 9 hops vs 512 hops

    return {
        "ring_8_data_moved_gb": round(ring_8_data_gb, 2),
        "ring_8_nvlink_ms": round(ring_8_time_ms, 2),
        "ring_8_nvlink_ms_int": int(round(ring_8_time_ms)),
        "ring_512_data_moved_gb": round(ring_512_data_gb, 1),
        "ring_512_ib_sec": round(ring_512_time_s, 1),
        "ring_512_hops": float(num_gpus_cluster),
        "tree_512_hops": float(tree_512_hops),
    }
