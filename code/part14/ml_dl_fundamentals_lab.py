"""Chapter 14.1 Verification Lab: ML and deep learning fundamentals for infrastructure engineers.

Run with:
    python3 -B code/part14/ml_dl_fundamentals_lab.py
"""

from __future__ import annotations

import math
import os
import sys
from typing import Callable, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_dl_fundamentals import (
    compare_sgd_vs_adamw_memory,
    compute_batch_scaled_lr,
    compute_cross_entropy_and_perplexity,
    compute_pipeline_bubble_fraction,
    compute_training_flops,
    compute_training_time_and_mfu,
    compute_warmup_cosine_lr,
    evaluate_critical_batch_size,
    evaluate_dmls_ch01_latency_and_batching,
    evaluate_dmls_ensembles_and_evaluation,
    evaluate_gpt3_step_and_corpus_scaling,
    evaluate_v13_ch02_7b_step_anatomy,
)


def run_checks() -> int:
    checks: List[Tuple[str, Callable[[], bool]]] = []

    def add(desc: str, fn: Callable[[], bool]) -> None:
        checks.append((desc, fn))

    # --- Section 1: Forward & Backward FLOPs (2PD + 4PD = 6PD) & Compute Scaling ---
    add(
        "1. Forward pass requires 2PD FLOPs, backward pass requires 4PD FLOPs (2PD activation grad + 2PD weight grad = 2x forward), and total training is 6PD FLOPs",
        lambda: (
            (f := compute_training_flops(7e9, 1e12)).forward_flops == 1.4e22
            and f.backward_activation_grad_flops == 1.4e22
            and f.backward_weight_grad_flops == 1.4e22
            and f.backward_total_flops == 2.8e22
            and f.total_6pd_flops == 4.2e22
            and f.backward_to_forward_ratio == 2.0
        ),
    )

    add(
        "2. Full activation checkpointing adds one extra forward pass during backward, raising total FLOPs from 6PD to 8PD (+33.33% compute overhead)",
        lambda: (
            (f := compute_training_flops(7e9, 1e12)).total_8pd_checkpointed_flops == 5.6e22
            and f.checkpoint_overhead_pct == 33.33
        ),
    )

    add(
        "3. V13 Ch. 01 GPT-3 175B single step (batch 2048, seq 2048 = 4,194,304 tokens) at 1.46e18 FLOPs takes 4,679.49 s (~78 min) on 1 A100 (312 TFLOPS) vs 36.56 s (~37 s) on 128 A100s",
        lambda: (
            (s := evaluate_gpt3_step_and_corpus_scaling())["step_tokens"] == 4194304.0
            and s["gpt3_single_a100_sec"] == 4679.49
            and s["gpt3_single_a100_min"] == 77.99
            and s["gpt3_128_a100_sec"] == 36.56
        ),
    )

    add(
        "4. DMLS Ch. 2 dataset scaling: 0.8B tokens (2013 One Billion Word) -> 10B (GPT-2) -> 500B (GPT-3 175B), requiring 6PD = 5.25e23 FLOPs (525.0 ZFLOPs)",
        lambda: (
            (s := evaluate_gpt3_step_and_corpus_scaling())["obwb_2013_tokens_b"] == 0.8
            and s["gpt2_2019_tokens_b"] == 10.0
            and s["gpt3_2020_tokens_b"] == 500.0
            and s["gpt3_500b_total_6pd_zflops"] == 525.0
            and s["seventy_b_2t_total_6pd_zflops"] == 840.0
        ),
    )

    # --- Section 2: SGD vs AdamW Optimizer State Memory (16 bytes/param) & Step Anatomy ---
    add(
        "5. Static memory per parameter is 8 B for vanilla FP32 SGD, 12 B for FP32 SGD with momentum, and 16 B for both FP32 AdamW and mixed-precision AdamW",
        lambda: (
            (m := compare_sgd_vs_adamw_memory(7.0)).fp32_sgd_no_mom_bytes_per_param == 8
            and m.fp32_sgd_mom_bytes_per_param == 12
            and m.fp32_adamw_bytes_per_param == 16
            and m.mixed_precision_adamw_bytes_per_param == 16
        ),
    )

    add(
        "6. Mixed-precision AdamW 16 B/param for a 7B model equals 14 GB BF16 weights + 14 GB BF16 grads + 28 GB FP32 master weights + 28 GB FP32 momentum m + 28 GB FP32 variance v = 112.0 GB (vs 56.0 GB vanilla SGD)",
        lambda: (
            (m := compare_sgd_vs_adamw_memory(7.0)).fp32_sgd_no_mom_gb == 56.0
            and m.fp32_sgd_mom_gb == 84.0
            and m.mixed_weights_bf16_gb == 14.0
            and m.mixed_grads_bf16_gb == 14.0
            and m.mixed_master_weights_fp32_gb == 28.0
            and m.mixed_adam_m_fp32_gb == 28.0
            and m.mixed_adam_v_fp32_gb == 28.0
            and m.mixed_precision_adamw_gb == 112.0
        ),
    )

    add(
        "7. Mixed-precision AdamW 16 B/param scales to 1,120.0 GB (~1.2 TB) for 70B parameters and 2,800.0 GB for 175B parameters",
        lambda: (
            compare_sgd_vs_adamw_memory(70.0).mixed_precision_adamw_gb == 1120.0
            and compare_sgd_vs_adamw_memory(175.0).mixed_precision_adamw_gb == 2800.0
        ),
    )

    add(
        "8. V13 Ch. 02 7B step anatomy: 70.0 GB forward (87.5% of 80 GB H100), 98.0 GB backward without checkpointing (OOM), 66.0 GB with checkpointing, and 51.0 GB with AMP (48.2 GB measured, 1,280 vs 1,000 tokens/s = 1.28x speedup)",
        lambda: (
            (a := evaluate_v13_ch02_7b_step_anatomy())["forward_total_gb"] == 70.0
            and a["forward_h100_util_pct"] == 87.5
            and a["backward_no_ckpt_gb"] == 98.0
            and a["backward_with_ckpt_gb"] == 66.0
            and a["optimizer_step_gb"] == 112.0
            and a["amp_total_gb"] == 51.0
            and a["no_amp_measured_gb"] == 78.5
            and a["amp_measured_gb"] == 48.2
            and a["amp_speedup_ratio"] == 1.28
        ),
    )

    # --- Section 3: Learning Rate Warmup + Cosine Decay Schedule & Batch Scaling ---
    add(
        "9. Linear warmup from step 0 to warmup_steps = 2,000 scales LR linearly from 0.0 to 1.5e-4 at midpoint (step 1,000) and 3.0e-4 at peak (step 2,000)",
        lambda: (
            compute_warmup_cosine_lr(0, 2000, 100000, 3e-4, 3e-5) == 0.0
            and math.isclose(compute_warmup_cosine_lr(1000, 2000, 100000, 3e-4, 3e-5), 1.5e-4, rel_tol=1e-9)
            and math.isclose(compute_warmup_cosine_lr(2000, 2000, 100000, 3e-4, 3e-5), 3.0e-4, rel_tol=1e-9)
        ),
    )

    add(
        "10. Cosine decay from step 2,000 to 100,000 hits exact midpoint 1.65e-4 at step 51,000 (progress = 0.5) and min_lr = 3.0e-5 at step 100,000",
        lambda: (
            math.isclose(compute_warmup_cosine_lr(51000, 2000, 100000, 3e-4, 3e-5), 1.65e-4, rel_tol=1e-9)
            and math.isclose(compute_warmup_cosine_lr(100000, 2000, 100000, 3e-4, 3e-5), 3.0e-5, rel_tol=1e-9)
        ),
    )

    add(
        "11. Cosine decay at quarter progress (step 26,500) and three-quarter progress (step 75,500) matches exact trigonometric schedule",
        lambda: (
            math.isclose(
                compute_warmup_cosine_lr(26500, 2000, 100000, 3e-4, 3e-5),
                3e-5 + 0.5 * (3e-4 - 3e-5) * (1.0 + math.cos(math.pi * 0.25)),
                rel_tol=1e-9,
            )
            and math.isclose(
                compute_warmup_cosine_lr(75500, 2000, 100000, 3e-4, 3e-5),
                3e-5 + 0.5 * (3e-4 - 3e-5) * (1.0 + math.cos(math.pi * 0.75)),
                rel_tol=1e-9,
            )
        ),
    )

    add(
        "12. V21 Ch. 07 square-root LR scaling from batch 32 (base_lr = 1e-4) to global batch 8,192 (128/GPU x 64 GPUs) multiplies LR by 16x to 1.6e-3",
        lambda: (
            math.isclose(compute_batch_scaled_lr(1e-4, 32, 8192, rule="sqrt"), 1.6e-3, rel_tol=1e-9)
            and math.isclose(compute_batch_scaled_lr(1e-4, 32, 8192, rule="linear"), 2.56e-2, rel_tol=1e-9)
        ),
    )

    # --- Section 4: Batch Size vs Gradient Noise Scale / Critical Batch Size & Pipeline Bubble ---
    add(
        "13. At B = B_crit (e.g., 2,048,000 tokens), training requires 2.0x minimum steps and 2.0x minimum tokens (50.0% parallel scaling efficiency)",
        lambda: (
            (c := evaluate_critical_batch_size(2048000, 2048000)).step_overhead_ratio == 2.0
            and c.data_compute_overhead_ratio == 2.0
            and c.parallel_scaling_efficiency_pct == 50.0
            and c.regime == "critical_batch_knee"
        ),
    )

    add(
        "14. In noise-dominated small-batch regime (B = 0.25 * B_crit = 512,000 tokens), parallel scaling efficiency is 80.0% (1.25x data cost, 5.0x step ratio)",
        lambda: (
            (c := evaluate_critical_batch_size(512000, 2048000)).step_overhead_ratio == 5.0
            and c.data_compute_overhead_ratio == 1.25
            and c.parallel_scaling_efficiency_pct == 80.0
            and c.regime == "noise_dominated_linear_scaling"
        ),
    )

    add(
        "15. In curvature-dominated large-batch regime (B = 8 * B_crit = 16,384,000 tokens), steps drop to 1.125x S_min but compute/data cost balloons 9.0x (11.11% efficiency)",
        lambda: (
            (c := evaluate_critical_batch_size(16384000, 2048000)).step_overhead_ratio == 1.125
            and c.data_compute_overhead_ratio == 9.0
            and c.parallel_scaling_efficiency_pct == 11.11
            and c.regime == "curvature_dominated_diminishing_returns"
        ),
    )

    add(
        "16. V21 Ch. 07 & DMLS Ch. 6 pipeline bubble fraction (p - 1)/(m + p - 1) for p = 4 stages drops from 3/7 = 42.86% at m = 4 micro-batches to 3/19 = 15.79% at m = 16 micro-batches",
        lambda: (
            compute_pipeline_bubble_fraction(4, 4) == 0.4286
            and compute_pipeline_bubble_fraction(4, 16) == 0.1579
        ),
    )

    # --- Section 5: Cross-Entropy Loss, Perplexity exp(loss), Ensembles & Offline Evaluation ---
    add(
        "17. DMLS Ch. 2 politics classification cross-entropy for p = [0, 0, 0, 1] and q = [0.45, 0.2, 0.02, 0.33] equals -ln(0.33) = 1.108663 nats and perplexity exp(loss) = 3.030303 (1 / 0.33)",
        lambda: (
            (ce := compute_cross_entropy_and_perplexity([0.0, 0.0, 0.0, 1.0], [0.45, 0.20, 0.02, 0.33]))[
                "cross_entropy_nats"
            ]
            == 1.108663
            and ce["perplexity"] == 3.030303
        ),
    )

    add(
        "18. Uniform random guessing over a 50,000-token vocabulary yields cross-entropy loss ln(50,000) = 10.819778 nats and perplexity exp(loss) = 50,000.0",
        lambda: (
            math.isclose(math.log(50000.0), 10.819778, rel_tol=1e-6)
            and math.isclose(math.exp(math.log(50000.0)), 50000.0, rel_tol=1e-9)
        ),
    )

    add(
        "19. Cross-entropy loss 2.50 nats corresponds to perplexity exp(2.50) = 12.182494, and loss 2.00 nats corresponds to perplexity exp(2.00) = 7.389056",
        lambda: (
            math.isclose(math.exp(2.50), 12.182494, rel_tol=1e-6)
            and math.isclose(math.exp(2.00), 7.389056, rel_tol=1e-6)
        ),
    )

    add(
        "20. DMLS Ch. 6 Table 6-1 majority-vote ensemble of 3 uncorrelated classifiers (70% accuracy each) achieves 0.343 + 0.441 = 0.784 (78.4%) accuracy",
        lambda: (
            (e := evaluate_dmls_ensembles_and_evaluation())["all_three_correct"] == 0.343
            and e["two_of_three_correct"] == 0.441
            and e["one_of_three_correct"] == 0.189
            and e["none_correct"] == 0.027
            and e["ensemble_accuracy"] == 0.784
        ),
    )

    add(
        "21. DMLS Ch. 6 Table 6-2 random baselines on 90%-NEGATIVE / 10%-POSITIVE data yield F1 = 0.167 / Acc = 0.50 (uniform) vs F1 = 0.10 / Acc = 0.82 (label-distribution) vs Acc = 0.90 (zero-rule)",
        lambda: (
            (e := evaluate_dmls_ensembles_and_evaluation())["uniform_random_f1"] == 0.167
            and e["uniform_random_acc"] == 0.50
            and e["label_dist_random_f1"] == 0.10
            and e["label_dist_random_acc"] == 0.82
            and e["zero_rule_acc"] == 0.90
        ),
    )

    add(
        "22. DMLS Ch. 6 Table 6-3 & 6-4: Model A (96.2% overall) hides an 80% minority slice vs Model B (95.0% uniform), and Simpson's paradox reverses subgroup winners (93%/73% vs 87%/69%) into overall 78% vs 83%",
        lambda: (
            (e := evaluate_dmls_ensembles_and_evaluation())["slice_model_a_overall_pct"] == 96.2
            and e["slice_model_b_overall_pct"] == 95.0
            and e["simpson_a_total_pct"] == 78.0
            and e["simpson_b_total_pct"] == 82.57
        ),
    )

    # --- Section 6: Training Time, MFU Calculator & Latency/Throughput (DMLS Ch. 1) ---
    add(
        "23. Training 70B parameters on 2T tokens (6PD = 8.40e23 FLOPs) across 512 H100 GPUs (989 TFLOPS peak) at 45% MFU (445.05 TFLOPS/GPU, 227.8656 PFLOPS cluster) takes 42.67 days (1,024.0 hours)",
        lambda: (
            (p := compute_training_time_and_mfu(70e9, 2e12, 512, 989.0, 0.45)).total_6pd_flops == 8.4e23
            and p.achieved_tflops_per_gpu == 445.05
            and p.cluster_achieved_pflops == 227.8656
            and p.training_hours == 1024.0
            and p.training_days == 42.67
        ),
    )

    add(
        "24. Achieving 542,537.14 tokens/s across 512 GPUs (1,059.64 tokens/s/GPU) on a 70B model corresponds to exactly 445.05 TFLOPS/GPU and 45.0% MFU on H100 (989 TFLOPS peak)",
        lambda: (
            (p := compute_training_time_and_mfu(70e9, 2e12, 512, 989.0, 0.45)).tokens_per_sec_cluster == 542537.14
            and p.tokens_per_sec_per_gpu == 1059.64
        ),
    )

    add(
        "25. Training 7B parameters on 1T tokens (6PD = 4.20e22 FLOPs) across 64 H100 GPUs at 50% MFU (494.50 TFLOPS/GPU, 31.648 PFLOPS cluster) completes in 15.36 days (368.64 hours)",
        lambda: (
            (p := compute_training_time_and_mfu(7e9, 1e12, 64, 989.0, 0.50)).achieved_tflops_per_gpu == 494.5
            and p.cluster_achieved_pflops == 31.648
            and p.training_hours == 368.64
            and p.training_days == 15.36
        ),
    )

    add(
        "26. DMLS Ch. 1 latency vs batching & percentiles: batching 50 queries at 20 ms yields 2,500 qps (vs 100 qps unbatched at 10 ms), and [100..3000 ms] has mean 390.0 ms, p50 = 100.0 ms, p90 = 3,000.0 ms",
        lambda: (
            (l := evaluate_dmls_ch01_latency_and_batching())["single_10ms_qps"] == 100.0
            and l["batch10_10ms_qps"] == 1000.0
            and l["batch50_20ms_qps"] == 2500.0
            and l["mean_latency_ms"] == 390.0
            and l["p50_latency_ms"] == 100.0
            and l["p90_latency_ms"] == 3000.0
        ),
    )

    passed = 0
    for desc, fn in checks:
        try:
            ok = bool(fn())
        except Exception as exc:
            print(f"  [FAIL] {desc} (raised {exc})")
            continue
        if ok:
            print(f"  [PASS] {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {desc}")

    failed = len(checks) - passed
    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
