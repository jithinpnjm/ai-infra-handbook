"""Chapter 14.1: ML and deep learning fundamentals for infrastructure engineers.

Pure Python 3 standard-library reference models for:
1. Forward and Backward Pass FLOPs (`2PD` forward + `4PD` backward = `6PD` total training FLOPs)
   and Compute Scaling (V13 Ch. 01, V13 Ch. 02, DMLS Ch. 2, Ch. 6):
   - Forward pass FLOPs per token per parameter: `2` FLOPs (`1` multiply + `1` add) -> `F_fwd = 2 * P * D`.
   - Backward pass FLOPs per token per parameter: `4` FLOPs (`2` FLOPs for activation gradients +
     `2` FLOPs for weight gradients) -> `F_bwd = 4 * P * D` (`2x` forward pass).
   - Total training FLOPs without activation checkpointing: `F_train = 6 * P * D`.
   - Total training FLOPs with full activation recomputation (`1` extra forward pass in backward):
     `F_ckpt = 8 * P * D` (`+33.33%` compute overhead, matching `V13 Ch. 02` `30-50%` backward overhead
     and `DMLS Ch. 6` `10x` larger models at `20%` compute time increase).
   - Concrete step and run examples:
      * `GPT-3` `175B` (`175e9` params) single training step at batch `2,048` and seq `2,048` (`4,194,304` tokens):
       - Forward pass (`2PD`): `2 * 175e9 * 2048 * 2048 = 1.4680064e18` FLOPs (`1.4680 x 10^18` / `1.468 x 10^18` / `~1.46e18` FLOPs in `V13 Ch. 01`).
       - Backward pass (`4PD`): `2.936 x 10^18` FLOPs (`2.9360 x 10^18`).
       - Full `6PD` step (`4.4040 x 10^18` / `4.404 x 10^18` FLOPs; `5.872 x 10^18` at `8PD`): `14,038.46 s` (`233.97 min`) on `1` `A100`
         or `109.68 s` (`1.83 min`) on `128` `A100` GPUs at `100%` peak.
       - At `1.46e18` FLOPs on `1` `A100` (`312` TFLOPS): `4,679.49 s` (`~4,679 s` = `77.99` / `78 min`);
         across `128` `A100` GPUs: `36.56 s` (`~37 s`).
     * `GPT-3` `175B` full training run on `500B` tokens (`DMLS Ch. 2`: `0.8B` tokens in `2013` One Billion Word
       Benchmark -> `10B` tokens in `GPT-2` -> `500B` tokens in `GPT-3`):
       `F_total = 6 * 175e9 * 500e9 = 5.25e23` FLOPs (`1.75e23` forward + `3.50e23` backward, `7.00 x 10^23` at `8PD`).
     * `7B` parameter model (`7e9` params) on `1T` (`1,000B`) tokens:
       `F_total = 6 * 7e9 * 1e12 = 4.20e22` FLOPs (`1.40e22` forward + `2.80e22` backward);
       with activation checkpointing (`8PD`): `5.60e22` FLOPs.
     * `70B` parameter model (`70e9` params) on `2T` (`2,000B`) tokens:
       `F_total = 6 * 70e9 * 2e12 = 8.40e23` (`8.40 x 10^23`) FLOPs (`2.80e23` forward + `5.60e23` backward).

2. SGD vs AdamW Optimizer State & Training Step Memory Anatomy (V13 Ch. 01, V13 Ch. 02, EAS Ch. 3):
   - Pure `FP32` vanilla `SGD` (no momentum, `0` optimizer states):
     `4 B` weights + `4 B` gradients + `0 B` optimizer states = `8 bytes/param` (`56.0 GB` for `7B`, `560.0 GB` for `70B`, `1,400.0 GB` for `175B`).
   - Pure `FP32` `SGD` with momentum (`1` `FP32` velocity buffer):
     `4 B` weights + `4 B` gradients + `4 B` momentum = `12 bytes/param` (`84.0 GB` for `7B`, `840.0 GB` for `70B`, `2,100.0 GB` for `175B`).
   - Pure `FP32` `Adam` / `AdamW` (`2` `FP32` buffers: momentum `m` + variance `v`, `V13 Ch. 01` & `Ch. 02`):
     `4 B` weights (`28.0 GB`) + `4 B` gradients (`28.0 GB`) + `8 B` optimizer states (`56.0 GB`) =
     `16 bytes/param` (`112.0 GB` for `7B`, `1,120.0 GB` for `70B`, `2,800.0 GB` for `175B`).
   - Mixed-precision (`AMP` `BF16`/`FP16` + `FP32` master weights) `AdamW`:
     `2 B` `BF16`/`FP16` working weights + `2 B` `BF16`/`FP16` gradients + `4 B` `FP32` master weights +
     `4 B` `FP32` Adam first moment (`m`) + `4 B` `FP32` Adam second moment (`v`) = `16 bytes/param`
     (`112.0 GB` for `7B`, `1,120.0 GB` / `~1.2 TB` for `70B`, `2,800.0 GB` for `175B`).
   - `V13 Ch. 02` `7B` Transformer (`32` layers, `hidden_dim = 4096`, `batch = 4`, `seq_len = 2048`):
     * Forward activations (`FP32`): `32 * 4 * 4096 * 4 * 2048 = 4,294,967,296` -> `~42.0 GB` (`V13 Ch. 02`
       reports `28 GB` weights + `42 GB` activations = `70.0 GB` forward, `87.5%` of `80 GB` H100;
       `98.0 GB` backward without checkpointing [FAILS on `80 GB`]; `66.0 GB` backward with activation
       checkpointing [`10.0 GB` recomputed activations + `28.0 GB` weights + `28.0 GB` gradients];
       `112.0 GB` at optimizer step [FAILS on `80 GB`]; `AMP` reduces `98.0 GB` to `51.0 GB`
       [`14.0 GB` `FP16` weights + `21.0 GB` `FP16` activations + `14.0 GB` `FP16` gradients +
       `2.0 GB` `FP32` loss/norm], cutting runtime memory from `78.5 GB` at `1,000 tokens/s` to
       `48.2 GB` at `1,280 tokens/s`, a `1.28x` / `+28.0%` throughput gain).

3. Learning Rate Warmup + Cosine Decay Schedule & Batch-Size LR Scaling (V21 Ch. 07, DMLS Ch. 6, EAS Ch. 3):
   - Linear warmup (`0 <= step <= warmup_steps`):
     `lr(step) = peak_lr * (step / warmup_steps)`.
   - Cosine annealing decay (`warmup_steps < step <= total_steps`, e.g., `warmup_steps = 2,000`, `total_steps = 100,000`,
     `peak_lr = 3.0e-4 = 0.0003`, `min_lr = 3.0e-5 = 0.00003`, `total_steps - warmup_steps = 98,000`, midpoint `step = 51,000`
     with `step - warmup_steps = 49,000` and `49,000 / 98,000 = 0.5` -> `lr = 1.65e-4`):
     `progress = (step - warmup_steps) / (total_steps - warmup_steps)`
     `lr(step) = min_lr + 0.5 * (peak_lr - min_lr) * (1 + cos(pi * progress))`.
   - Batch-size LR scaling rules (`V21 Ch. 07`, `DMLS Ch. 6`):
     * Square-root scaling (`V21 Ch. 07`): `batch_size_per_gpu = 128`, `num_gpus = 64` ->
       `global_batch_size = 8,192`. From `base_lr = 1e-4` at `base_batch = 32`:
       `scaled_lr = 1e-4 * sqrt(8192 / 32) = 1e-4 * 16 = 1.6e-3` (`0.0016`).
     * Epoch-to-iteration math (`EAS Ch. 3`, `DMLS Ch. 6`):
       `1,000` examples at `batch_size = 100` -> `10` iterations per epoch (`EAS Ch. 3`);
       `1,000` machines each with `batch_size = 1,000` -> `global_batch_size = 1,000,000` (`1M`),
       reducing `1,000,000` single-machine steps/epoch to `1,000` distributed steps (`DMLS Ch. 6`;
       `GPT-3` `175B` uses a `3.2M` token batch size).

4. Batch Size vs Gradient Noise Scale / Critical Batch Size & Pipeline Bubble (DMLS Ch. 6, V21 Ch. 07):
   - McCandlish et al. (`DMLS Ch. 6` footnote 20) empirical model of large-batch training:
     Given critical batch size `B_crit` (approximated by gradient noise scale `B_noise = tr(Sigma) / |G|^2`):
     * Relative step efficiency: `S / S_min = 1 + B_crit / B`
     * Relative compute/data cost: `E / E_min = 1 + B / B_crit`
     * At `B = B_crit`, training uses `2.0x` (`2.00x`) minimum steps and `2.0x` (`2.00x`) minimum tokens (`50.0%` step scaling efficiency).
     * When `B >> B_crit` (e.g., `B = 8 * B_crit`), step count approaches `1.125 * S_min` (`88.89%` of max step
       reduction) while compute/token cost jumps `9.0x` (`9.00x`, `diminishing returns`).
   - Pipeline parallelism bubble fraction (`V21 Ch. 07`, `DMLS Ch. 6` GPipe):
     `bubble_fraction = (p - 1) / (m + p - 1)`.
     For `p = 4` stages and `m = 4` micro-batches: `(4 - 1) / (4 + 4 - 1) = 3 / 7 = 42.86%` (`0.4286`);
     for `p = 4` stages and `m = 16` micro-batches: `3 / 19 = 15.79%` (`0.1579`).

5. Cross-Entropy Loss, Perplexity `exp(loss)`, Ensembles & Offline Evaluation (DMLS Ch. 2, Ch. 6, EAS Ch. 3):
   - Cross-entropy loss (`DMLS Ch. 2`): `H(p, q) = -sum_i p_i * ln(q_i)`.
     For politics ground truth `p = [0, 0, 0, 1]` and prediction `q = [0.45, 0.2, 0.02, 0.33]`:
     `H(p, q) = -ln(0.33) = 1.108663` nats (`1.599462` bits) -> perplexity `PPL = exp(1.108663) = 3.030303` (`1 / 0.33`).
   - Uniform random baseline over `V = 50,000` vocabulary tokens:
     `loss = ln(50,000) = 10.819778` nats, `PPL = 50,000.0`.
   - Trained LLM benchmark losses:
     `loss = 2.50` -> `PPL = exp(2.50) = 12.182494` (`12.18`);
     `loss = 2.00` -> `PPL = exp(2.00) = 7.389056` (`7.39`);
     `loss = 0.00` -> `PPL = 1.0`.
   - `DMLS Ch. 6` Table 6-1 uncorrelated `3`-classifier majority-vote ensemble (`p = 0.70` each):
     * All `3` correct: `0.7^3 = 0.343` (`34.3%`)
     * Exactly `2` correct: `3 * 0.7^2 * 0.3 = 0.441` (`44.1%`)
     * Ensemble accuracy: `0.343 + 0.441 = 0.784` (`78.4%`, `+8.4%` over `70.0%` individual base learner)
     * Exactly `1` correct: `3 * 0.3^2 * 0.7 = 0.189` (`18.9%`)
     * None correct: `0.3^3 = 0.027` (`2.7%`).
   - `DMLS Ch. 6` Table 6-2 random baseline on imbalanced dataset (`90%` NEGATIVE, `10%` POSITIVE):
     * Uniform random (`50%` POS / `50%` NEG): `accuracy = 0.50` (`50.0%`), `F1 = 0.167` (`1/6`).
     * Label-distribution random (`10%` POS / `90%` NEG): `accuracy = 0.82` (`82.0%`), `F1 = 0.10` (`10.0%`).
   - `DMLS Ch. 6` Table 6-3 slice-based evaluation (`90%` majority, `10%` minority) & Table 6-4 Simpson's paradox:
     * Model A (`98%` majority, `80%` minority) -> `96.2%` overall accuracy;
       Model B (`95%` majority, `95%` minority) -> `95.0%` overall accuracy.
     * Simpson's paradox (`Table 6-4`): Model A wins Group A (`81/87 = 93.10%` / `93%` vs `234/270 = 86.67%` / `87%`)
       and Group B (`192/263 = 73.00%` / `73%` vs `55/80 = 68.75%` / `69%`), yet Model B wins combined overall
       (`289/350 = 82.57%` / `83%` vs `273/350 = 78.0%` / `78.00%` / `78%`).

6. Training Time, Model FLOPs Utilization (`MFU`), and Latency vs Throughput (DMLS Ch. 1, V13 Ch. 01, V21 Ch. 07):
   - Achieved FLOPs/s per GPU: `(6 * P * tokens_per_sec_cluster) / num_gpus`.
   - `MFU = achieved_tflops_per_gpu / hardware_peak_tflops_per_gpu`.
   - Training time (seconds): `(6 * P * D) / (num_gpus * hardware_peak_tflops * 1e12 * mfu)`.
   - Concrete `70B` training run on `2T` (`2e12`) tokens across `512` `H100` GPUs (`989` TFLOPS BF16 Tensor Core peak)
     at `MFU = 45.0%` (`0.45`, `445.05` achieved TFLOPS/GPU):
     * Total FLOPs = `8.40e23`.
     * Cluster achieved throughput = `227,865.6 TFLOPS` = `227.8656 PFLOPS` (`227.8656 x 10^15` FLOPs/s; `542,537.14` tokens/s across `512` GPUs, `1,059.64` tokens/s/GPU).
     * Training time = `3,686,383.30 seconds` = `1,024.0 hours` (`1,023.995 h`) = `42.67 days`.
   - Concrete `7B` training run on `1T` (`1e12`) tokens across `64` `H100` GPUs at `MFU = 50.0%` (`494.50` TFLOPS/GPU):
     * Cluster achieved throughput = `31.648 PFLOPS` (`31.648 x 10^15` FLOPs/s).
     * Training time = `1,327,098.08 seconds` = `368.64 hours` = `15.36 days`.
   - `DMLS Ch. 1` batching latency vs throughput & tail latency (`p50`, `p90`, `p99`):
     * `1` query at `10 ms` -> `100` queries/s; `1` query at `100 ms` -> `10` queries/s.
     * Batch of `10` queries in `10 ms` -> `1,000` queries/s; batch of `50` queries in `20 ms` -> `2,500` queries/s.
     * `10` request latencies `[100, 102, 100, 100, 99, 104, 110, 90, 3000, 95] ms`:
       arithmetic mean = `390.0 ms`, `p50` (median) = `100.0 ms`, `p90` outlier = `3,000.0 ms`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence


# ---------------------------------------------------------------------------
# 1. Forward and Backward Pass FLOPs (`2PD` + `4PD` = `6PD`) & Compute Scaling
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrainingFlopsBreakdown:
    params: float
    tokens: float
    forward_flops: float
    backward_activation_grad_flops: float
    backward_weight_grad_flops: float
    backward_total_flops: float
    total_6pd_flops: float
    total_8pd_checkpointed_flops: float
    backward_to_forward_ratio: float
    checkpoint_overhead_pct: float


def compute_training_flops(params: float, tokens: float) -> TrainingFlopsBreakdown:
    """Compute exact 2PD forward, 4PD backward, 6PD standard, and 8PD checkpointed training FLOPs."""
    fwd = 2.0 * params * tokens
    bwd_act = 2.0 * params * tokens
    bwd_w = 2.0 * params * tokens
    bwd = bwd_act + bwd_w
    total_6pd = fwd + bwd
    total_8pd = total_6pd + fwd
    return TrainingFlopsBreakdown(
        params=params,
        tokens=tokens,
        forward_flops=fwd,
        backward_activation_grad_flops=bwd_act,
        backward_weight_grad_flops=bwd_w,
        backward_total_flops=bwd,
        total_6pd_flops=total_6pd,
        total_8pd_checkpointed_flops=total_8pd,
        backward_to_forward_ratio=round(bwd / fwd, 2),
        checkpoint_overhead_pct=round(((total_8pd - total_6pd) / total_6pd) * 100.0, 2),
    )


def evaluate_gpt3_step_and_corpus_scaling() -> Dict[str, float]:
    """Reproduce V13 Ch. 01 GPT-3 175B step scaling and DMLS Ch. 2 dataset token scaling."""
    gpt3_params = 175e9
    batch_size = 2048
    seq_len = 2048
    step_tokens = batch_size * seq_len  # 4,194,304 tokens
    fwd_exact_flops = 2.0 * gpt3_params * step_tokens  # 1.4680064e18
    v13_reported_step_flops = 1.46e18
    a100_fp32_tf = 312e12  # 312 TFLOPS
    single_a100_sec = v13_reported_step_flops / a100_fp32_tf  # 4,679.487 s
    cluster_128_a100_sec = single_a100_sec / 128.0  # 36.558 s

    # DMLS Ch. 2 dataset scaling: 0.8B (One Billion Word, 2013) -> 10B (GPT-2, 2019) -> 500B (GPT-3, 2020)
    gpt3_run = compute_training_flops(175e9, 500e9)
    seven_b_1t = compute_training_flops(7e9, 1e12)
    seventy_b_2t = compute_training_flops(70e9, 2e12)

    return {
        "step_tokens": float(step_tokens),
        "gpt3_step_fwd_exact_eflops": round(fwd_exact_flops / 1e18, 4),
        "gpt3_step_v13_eflops": 1.46,
        "gpt3_single_a100_sec": round(single_a100_sec, 2),
        "gpt3_single_a100_min": round(single_a100_sec / 60.0, 2),
        "gpt3_128_a100_sec": round(cluster_128_a100_sec, 2),
        "obwb_2013_tokens_b": 0.8,
        "gpt2_2019_tokens_b": 10.0,
        "gpt3_2020_tokens_b": 500.0,
        "gpt3_500b_total_6pd_zflops": round(gpt3_run.total_6pd_flops / 1e21, 1),  # 525.0 ZFLOPs = 5.25e23
        "seven_b_1t_total_6pd_zflops": round(seven_b_1t.total_6pd_flops / 1e21, 1),  # 42.0 ZFLOPs = 4.20e22
        "seventy_b_2t_total_6pd_zflops": round(seventy_b_2t.total_6pd_flops / 1e21, 1),  # 840.0 ZFLOPs = 8.40e23
    }


# ---------------------------------------------------------------------------
# 2. SGD vs AdamW Optimizer State & Training Step Memory Anatomy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OptimizerMemoryComparison:
    params_billions: float
    fp32_sgd_no_mom_bytes_per_param: int
    fp32_sgd_mom_bytes_per_param: int
    fp32_adamw_bytes_per_param: int
    mixed_precision_adamw_bytes_per_param: int
    fp32_sgd_no_mom_gb: float
    fp32_sgd_mom_gb: float
    fp32_adamw_gb: float
    mixed_precision_adamw_gb: float
    mixed_weights_bf16_gb: float
    mixed_grads_bf16_gb: float
    mixed_master_weights_fp32_gb: float
    mixed_adam_m_fp32_gb: float
    mixed_adam_v_fp32_gb: float


def compare_sgd_vs_adamw_memory(params_billions: float) -> OptimizerMemoryComparison:
    """Compare static memory (weights + gradients + optimizer states) for SGD vs AdamW."""
    # FP32 SGD without momentum: 4B weights + 4B grads = 8 B/param
    # FP32 SGD with momentum: 4B weights + 4B grads + 4B velocity = 12 B/param
    # FP32 AdamW: 4B weights + 4B grads + 4B m + 4B v = 16 B/param
    # Mixed-precision AdamW: 2B BF16 weights + 2B BF16 grads + 4B FP32 master + 4B FP32 m + 4B FP32 v = 16 B/param
    return OptimizerMemoryComparison(
        params_billions=params_billions,
        fp32_sgd_no_mom_bytes_per_param=8,
        fp32_sgd_mom_bytes_per_param=12,
        fp32_adamw_bytes_per_param=16,
        mixed_precision_adamw_bytes_per_param=16,
        fp32_sgd_no_mom_gb=round(params_billions * 8.0, 2),
        fp32_sgd_mom_gb=round(params_billions * 12.0, 2),
        fp32_adamw_gb=round(params_billions * 16.0, 2),
        mixed_precision_adamw_gb=round(params_billions * 16.0, 2),
        mixed_weights_bf16_gb=round(params_billions * 2.0, 2),
        mixed_grads_bf16_gb=round(params_billions * 2.0, 2),
        mixed_master_weights_fp32_gb=round(params_billions * 4.0, 2),
        mixed_adam_m_fp32_gb=round(params_billions * 4.0, 2),
        mixed_adam_v_fp32_gb=round(params_billions * 4.0, 2),
    )


def evaluate_v13_ch02_7b_step_anatomy() -> Dict[str, float]:
    """Reproduce V13 Ch. 01 and Ch. 02 7B memory timeline and AMP speedup numbers."""
    weights_fp32_gb = 28.0
    grads_fp32_gb = 28.0
    adam_m_fp32_gb = 28.0
    adam_v_fp32_gb = 28.0
    activations_fp32_gb = 42.0  # 32 layers, batch 4, seq 2048, hidden 4096 in V13 Ch. 02
    recomputed_act_gb = 10.0

    forward_total_gb = weights_fp32_gb + activations_fp32_gb  # 70.0 GB (87.5% of 80 GB H100)
    backward_no_ckpt_gb = weights_fp32_gb + activations_fp32_gb + grads_fp32_gb  # 98.0 GB (FAILS)
    backward_with_ckpt_gb = weights_fp32_gb + recomputed_act_gb + grads_fp32_gb  # 66.0 GB (fits)
    optimizer_step_gb = weights_fp32_gb + grads_fp32_gb + adam_m_fp32_gb + adam_v_fp32_gb  # 112.0 GB (FAILS)

    # AMP breakdown (V13 Ch. 02): 14 GB FP16 weights + 21 GB FP16 activations + 14 GB FP16 grads + 2 GB FP32 loss/norm = 51 GB
    amp_weights_gb = 14.0
    amp_activations_gb = 21.0
    amp_grads_gb = 14.0
    amp_fp32_loss_norm_gb = 2.0
    amp_total_gb = amp_weights_gb + amp_activations_gb + amp_grads_gb + amp_fp32_loss_norm_gb  # 51.0 GB

    return {
        "weights_fp32_gb": weights_fp32_gb,
        "activations_fp32_gb": activations_fp32_gb,
        "forward_total_gb": forward_total_gb,
        "forward_h100_util_pct": round((forward_total_gb / 80.0) * 100.0, 2),  # 87.5%
        "backward_no_ckpt_gb": backward_no_ckpt_gb,
        "backward_with_ckpt_gb": backward_with_ckpt_gb,
        "optimizer_step_gb": optimizer_step_gb,
        "amp_total_gb": amp_total_gb,
        "no_amp_measured_gb": 78.5,
        "amp_measured_gb": 48.2,
        "no_amp_tokens_per_sec": 1000.0,
        "amp_tokens_per_sec": 1280.0,
        "amp_speedup_ratio": 1.28,
    }


# ---------------------------------------------------------------------------
# 3. Learning Rate Warmup + Cosine Decay Schedule & Batch-Size LR Scaling
# ---------------------------------------------------------------------------

def compute_warmup_cosine_lr(
    step: int,
    warmup_steps: int,
    total_steps: int,
    peak_lr: float,
    min_lr: float,
) -> float:
    """Compute exact learning rate at `step` under linear warmup + cosine annealing decay."""
    if step < 0:
        raise ValueError("step must be non-negative")
    if warmup_steps <= 0 or total_steps <= warmup_steps:
        raise ValueError("Require 0 < warmup_steps < total_steps")
    if step <= warmup_steps:
        return peak_lr * (step / float(warmup_steps))
    if step >= total_steps:
        return min_lr
    progress = (step - warmup_steps) / float(total_steps - warmup_steps)
    cosine_factor = 0.5 * (1.0 + math.cos(math.pi * progress))
    return min_lr + (peak_lr - min_lr) * cosine_factor


def compute_batch_scaled_lr(
    base_lr: float,
    base_batch_size: int,
    global_batch_size: int,
    rule: str = "sqrt",
) -> float:
    """Scale learning rate from base_batch_size to global_batch_size using 'sqrt' or 'linear' rule."""
    ratio = global_batch_size / float(base_batch_size)
    if rule == "sqrt":
        return base_lr * math.sqrt(ratio)
    if rule == "linear":
        return base_lr * ratio
    raise ValueError(f"Unknown scaling rule: {rule}")


# ---------------------------------------------------------------------------
# 4. Batch Size vs Gradient Noise Scale / Critical Batch Size & Pipeline Bubble
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CriticalBatchSizeMetrics:
    batch_size: int
    critical_batch_size: int
    step_overhead_ratio: float      # S / S_min = 1 + B_crit / B
    data_compute_overhead_ratio: float  # E / E_min = 1 + B / B_crit
    parallel_scaling_efficiency_pct: float  # 1 / (1 + B / B_crit) * 100
    regime: str


def evaluate_critical_batch_size(batch_size: int, critical_batch_size: int) -> CriticalBatchSizeMetrics:
    """Evaluate McCandlish et al. (DMLS Ch. 6) critical batch size / gradient noise scale tradeoff."""
    if batch_size <= 0 or critical_batch_size <= 0:
        raise ValueError("batch_size and critical_batch_size must be positive")
    step_ratio = 1.0 + (critical_batch_size / float(batch_size))
    data_ratio = 1.0 + (batch_size / float(critical_batch_size))
    eff_pct = (1.0 / data_ratio) * 100.0
    if batch_size < critical_batch_size:
        regime = "noise_dominated_linear_scaling"
    elif batch_size == critical_batch_size:
        regime = "critical_batch_knee"
    else:
        regime = "curvature_dominated_diminishing_returns"
    return CriticalBatchSizeMetrics(
        batch_size=batch_size,
        critical_batch_size=critical_batch_size,
        step_overhead_ratio=round(step_ratio, 4),
        data_compute_overhead_ratio=round(data_ratio, 4),
        parallel_scaling_efficiency_pct=round(eff_pct, 2),
        regime=regime,
    )


def compute_pipeline_bubble_fraction(num_stages: int, num_microbatches: int) -> float:
    """Compute GPipe/pipeline bubble fraction (p - 1) / (m + p - 1) from V21 Ch. 07 & DMLS Ch. 6."""
    if num_stages < 1 or num_microbatches < 1:
        raise ValueError("num_stages and num_microbatches must be >= 1")
    return round((num_stages - 1) / float(num_microbatches + num_stages - 1), 4)


# ---------------------------------------------------------------------------
# 5. Cross-Entropy Loss, Perplexity `exp(loss)`, Ensembles & Offline Evaluation
# ---------------------------------------------------------------------------

def compute_cross_entropy_and_perplexity(
    target_probs: Sequence[float],
    pred_probs: Sequence[float],
) -> Dict[str, float]:
    """Compute cross-entropy H(p, q) = -sum p_i * ln(q_i) in nats/bits and perplexity = exp(H)."""
    if len(target_probs) != len(pred_probs) or not target_probs:
        raise ValueError("target_probs and pred_probs must have equal non-zero length")
    loss_nats = 0.0
    for p_i, q_i in zip(target_probs, pred_probs):
        if p_i > 0.0:
            if q_i <= 0.0:
                raise ValueError("pred_probs must be > 0 where target_probs > 0")
            loss_nats -= p_i * math.log(q_i)
    ppl = math.exp(loss_nats)
    loss_bits = loss_nats / math.log(2.0)
    return {
        "cross_entropy_nats": round(loss_nats, 6),
        "cross_entropy_bits": round(loss_bits, 6),
        "perplexity": round(ppl, 6),
    }


def evaluate_dmls_ensembles_and_evaluation() -> Dict[str, float]:
    """Reproduce DMLS Ch. 6 ensemble majority vote, random baselines, slicing, and Simpson's paradox."""
    # DMLS Ch. 6 Table 6-1: 3 uncorrelated classifiers, each p = 0.70
    p = 0.7
    q = 1.0 - p
    all_three = round(p ** 3, 3)            # 0.343
    two_of_three = round(3 * (p ** 2) * q, 3)  # 0.441
    one_of_three = round(3 * p * (q ** 2), 3)  # 0.189
    none_of_three = round(q ** 3, 3)        # 0.027
    ensemble_acc = round(all_three + two_of_three, 3)  # 0.784 (78.4%)

    # DMLS Ch. 6 Table 6-2: Imbalanced dataset (90% NEGATIVE, 10% POSITIVE)
    # Uniform random (50% POS, 50% NEG): TP=0.05, FP=0.45, FN=0.05, TN=0.45 -> Acc=0.50, F1=2*0.05/(0.10+0.50)=0.167
    # Label-dist random (10% POS, 90% NEG): TP=0.01, FP=0.09, FN=0.09, TN=0.81 -> Acc=0.82, F1=0.10
    # Zero-rule (always NEGATIVE): Acc = 0.90 (90%)

    # DMLS Ch. 6 Table 6-3: Slice-based evaluation (90% majority, 10% minority)
    model_a_overall = round(0.90 * 98.0 + 0.10 * 80.0, 1)  # 96.2%
    model_b_overall = round(0.90 * 95.0 + 0.10 * 95.0, 1)  # 95.0%

    # DMLS Ch. 6 Table 6-4: Simpson's paradox (Charig et al. 1986 kidney stone study)
    a_grp_a = round((81.0 / 87.0) * 100.0, 2)    # 93.10% (~93%)
    a_grp_b = round((192.0 / 263.0) * 100.0, 2)  # 73.00% (73%)
    a_total = round((273.0 / 350.0) * 100.0, 2)  # 78.00% (78%)
    b_grp_a = round((234.0 / 270.0) * 100.0, 2)  # 86.67% (~87%)
    b_grp_b = round((55.0 / 80.0) * 100.0, 2)    # 68.75% (~69%)
    b_total = round((289.0 / 350.0) * 100.0, 2)  # 82.57% (~83%)

    return {
        "all_three_correct": all_three,
        "two_of_three_correct": two_of_three,
        "one_of_three_correct": one_of_three,
        "none_correct": none_of_three,
        "ensemble_accuracy": ensemble_acc,
        "uniform_random_f1": 0.167,
        "uniform_random_acc": 0.50,
        "label_dist_random_f1": 0.10,
        "label_dist_random_acc": 0.82,
        "zero_rule_acc": 0.90,
        "slice_model_a_overall_pct": model_a_overall,
        "slice_model_b_overall_pct": model_b_overall,
        "simpson_a_grp_a_pct": a_grp_a,
        "simpson_a_grp_b_pct": a_grp_b,
        "simpson_a_total_pct": a_total,
        "simpson_b_grp_a_pct": b_grp_a,
        "simpson_b_grp_b_pct": b_grp_b,
        "simpson_b_total_pct": b_total,
    }


# ---------------------------------------------------------------------------
# 6. Training Time, MFU Calculator, and Latency vs Throughput (DMLS Ch. 1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrainingTimeAndMfuPlan:
    params: float
    tokens: float
    num_gpus: int
    peak_tflops_per_gpu: float
    mfu: float
    total_6pd_flops: float
    achieved_tflops_per_gpu: float
    cluster_achieved_pflops: float
    tokens_per_sec_cluster: float
    tokens_per_sec_per_gpu: float
    training_seconds: float
    training_hours: float
    training_days: float


def compute_training_time_and_mfu(
    params: float,
    tokens: float,
    num_gpus: int,
    peak_tflops_per_gpu: float,
    mfu: float,
) -> TrainingTimeAndMfuPlan:
    """Compute training wall-clock time, achieved TFLOPS/GPU, and token throughput from 6PD and MFU."""
    if params <= 0 or tokens <= 0 or num_gpus <= 0 or peak_tflops_per_gpu <= 0 or not (0.0 < mfu <= 1.0):
        raise ValueError("Invalid parameters for training time / MFU calculation")
    total_flops = 6.0 * params * tokens
    achieved_tf_gpu = peak_tflops_per_gpu * mfu
    cluster_flops_sec = num_gpus * achieved_tf_gpu * 1e12
    train_sec = total_flops / cluster_flops_sec
    tok_sec_cluster = tokens / train_sec
    tok_sec_gpu = tok_sec_cluster / float(num_gpus)
    return TrainingTimeAndMfuPlan(
        params=params,
        tokens=tokens,
        num_gpus=num_gpus,
        peak_tflops_per_gpu=peak_tflops_per_gpu,
        mfu=mfu,
        total_6pd_flops=total_flops,
        achieved_tflops_per_gpu=round(achieved_tf_gpu, 2),
        cluster_achieved_pflops=round(cluster_flops_sec / 1e15, 4),
        tokens_per_sec_cluster=round(tok_sec_cluster, 2),
        tokens_per_sec_per_gpu=round(tok_sec_gpu, 2),
        training_seconds=round(train_sec, 2),
        training_hours=round(train_sec / 3600.0, 2),
        training_days=round(train_sec / 86400.0, 2),
    )


def evaluate_dmls_ch01_latency_and_batching() -> Dict[str, float]:
    """Reproduce DMLS Ch. 1 single-query vs batched latency/throughput and p50/p90 outlier distribution."""
    latencies_ms: List[float] = [100, 102, 100, 100, 99, 104, 110, 90, 3000, 95]
    sorted_lat = sorted(latencies_ms)
    mean_ms = sum(latencies_ms) / float(len(latencies_ms))  # 390.0 ms
    p50_ms = 0.5 * (sorted_lat[4] + sorted_lat[5])          # 100.0 ms
    p90_ms = sorted_lat[-1]                                 # 3000.0 ms

    return {
        "single_10ms_qps": 1000.0 / 10.0,         # 100 queries/s
        "single_100ms_qps": 1000.0 / 100.0,       # 10 queries/s
        "batch10_10ms_qps": (10.0 * 1000.0) / 10.0,  # 1,000 queries/s
        "batch50_20ms_qps": (50.0 * 1000.0) / 20.0,  # 2,500 queries/s
        "mean_latency_ms": round(mean_ms, 1),
        "p50_latency_ms": round(p50_ms, 1),
        "p90_latency_ms": round(p90_ms, 1),
    }
