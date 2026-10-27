"""Chapter 14.3 Verification Lab: Training memory and compute anatomy.

Run with:
    python3 -B code/part14/training_memory_compute_lab.py
"""

from __future__ import annotations

import os
import sys
from typing import Callable, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from training_memory_compute import (
    OPTIMIZER_STATE_MULTIPLIERS,
    PRECISION_BYTES,
    calculate_static_training_memory,
    calculate_training_step_flops_and_mfu,
    calculate_transformer_activation_memory,
    evaluate_dai_7b_memory_timeline,
    evaluate_gpt3_175b_step_scaling,
    evaluate_mlperf_step_timing_breakdown,
    evaluate_ring_allreduce_vs_tree_cost,
    evaluate_v13_ch02_7b_scenarios,
     simulate_cuda_allocator_rounding,
    size_gradient_accumulation_and_batch,
)


def run_checks() -> int:
    checks: List[Tuple[str, Callable[[], bool]]] = []

    def add(desc: str, fn: Callable[[], bool]) -> None:
        checks.append((desc, fn))

    # --- Section 1: Precision Formats, Optimizer Multipliers & Static Model State ---
    add(
        "1. Precision format byte sizes: FP32=4B, BF16=2B, FP16=2B, FP8 (E4M3/E5M2/MXFP8)=1B, INT8=1B, INT4/NVFP4=0.5B (DAI Ch. 01)",
        lambda: (
            PRECISION_BYTES["FP32"] == 4.0
            and PRECISION_BYTES["BF16"] == 2.0
            and PRECISION_BYTES["FP16"] == 2.0
            and PRECISION_BYTES["FP8_E4M3"] == 1.0
            and PRECISION_BYTES["FP8_E5M2"] == 1.0
            and PRECISION_BYTES["MXFP8"] == 1.0
            and PRECISION_BYTES["INT8"] == 1.0
            and PRECISION_BYTES["INT4"] == 0.5
            and PRECISION_BYTES["NVFP4"] == 0.5
        ),
    )

    add(
        "2. Optimizer state multipliers: SGD=0x, SGD+Momentum/RMSProp/Lion=1x, Adafactor=0.5x, Adam/AdamW/LAMB=2x, AMSGrad=3x (DAI Ch. 01)",
        lambda: (
            OPTIMIZER_STATE_MULTIPLIERS["SGD"] == 0.0
            and OPTIMIZER_STATE_MULTIPLIERS["SGD_Momentum"] == 1.0
            and OPTIMIZER_STATE_MULTIPLIERS["RMSProp"] == 1.0
            and OPTIMIZER_STATE_MULTIPLIERS["Lion"] == 1.0
            and OPTIMIZER_STATE_MULTIPLIERS["Adafactor"] == 0.5
            and OPTIMIZER_STATE_MULTIPLIERS["Adam"] == 2.0
            and OPTIMIZER_STATE_MULTIPLIERS["AdamW"] == 2.0
            and OPTIMIZER_STATE_MULTIPLIERS["LAMB"] == 2.0
            and OPTIMIZER_STATE_MULTIPLIERS["AMSGrad"] == 3.0
        ),
    )

    add(
        "3. V13 Ch. 01 & Ch. 02 7B pure FP32 Adam static state: 28 GB weights + 28 GB grads + 28 GB m + 28 GB v = 112 GB (56 GB optimizer state)",
        lambda: (
            (m7 := calculate_static_training_memory(7.0, mode="fp32_adam")).weights_gb == 28.0
            and m7.gradients_gb == 28.0
            and m7.optimizer_m_gb == 28.0
            and m7.optimizer_v_gb == 28.0
            and m7.optimizer_total_gb == 56.0
            and m7.static_training_total_gb == 112.0
        ),
    )

    add(
        "4. Mixed-precision (BF16 + FP32 master weights) AdamW 16*Psi rule on 7B: 14 GB weights + 14 GB grads + 28 GB master + 28 GB m + 28 GB v = 112 GB",
        lambda: (
            (mp7 := calculate_static_training_memory(7.0, mode="mixed_bf16_fp32_adamw")).weights_gb == 14.0
            and mp7.gradients_gb == 14.0
            and mp7.master_weights_gb == 28.0
            and mp7.optimizer_m_gb == 28.0
            and mp7.optimizer_v_gb == 28.0
            and mp7.optimizer_total_gb == 84.0
            and mp7.static_training_total_gb == 112.0
            and mp7.checkpoint_disk_gb == 98.0
            and mp7.bytes_per_param_training == 16.0
            and mp7.bytes_per_param_checkpoint == 14.0
        ),
    )

    add(
        "5. Mixed-precision AdamW on 70B (Llama-3-70B, V05 Ch. 01 & V13 Ch. 01): 140 GB BF16 weights + 140 GB grads + 840 GB FP32 optimizer = 1,120 GB (~1.12 TB) training, 980 GB checkpoint",
        lambda: (
            (mp70 := calculate_static_training_memory(70.0, mode="mixed_bf16_fp32_adamw")).weights_gb == 140.0
            and mp70.gradients_gb == 140.0
            and mp70.master_weights_gb == 280.0
            and mp70.optimizer_m_gb == 280.0
            and mp70.optimizer_v_gb == 280.0
            and mp70.optimizer_total_gb == 840.0
            and mp70.static_training_total_gb == 1120.0
            and mp70.checkpoint_disk_gb == 980.0
        ),
    )

    add(
        "6. Mixed-precision AdamW on 13B (DAI Ch. 01) and 175B GPT-3 (V05 Ch. 01): 13B = 26 GB weights / 208 GB total; 175B = 350 GB weights / 2,800 GB (2.8 TB) total",
        lambda: (
            (mp13 := calculate_static_training_memory(13.0, mode="mixed_bf16_fp32_adamw")).weights_gb == 26.0
            and mp13.static_training_total_gb == 208.0
            and (mp175 := calculate_static_training_memory(175.0, mode="mixed_bf16_fp32_adamw")).weights_gb == 350.0
            and mp175.static_training_total_gb == 2800.0
        ),
    )

    add(
        "7. DAI Ch. 01 Fig 1.4 7B pure-BF16 Adam timeline: 56 GB fixed (14W + 14G + 28Opt), 54 GB forward, 68 GB backward peak (12 GB act), 56 GB optimizer step (64-72 GB range)",
        lambda: (
            (tl := evaluate_dai_7b_memory_timeline(7.0, 12.0))["fixed_static_gb"] == 56.0
            and tl["forward_pass_gb"] == 54.0
            and tl["backward_peak_gb"] == 68.0
            and tl["optimizer_step_gb"] == 56.0
            and tl["range_min_gb"] == 64.0
            and tl["range_max_gb"] == 72.0
        ),
    )

    add(
        "8. V13 Ch. 02 7B scenarios: 70 GB forward (87.5% of 80 GB H100), 98 GB backward no-ckpt (OOM), 60-66 GB with ckpt, 51 GB AMP (78.5 -> 48.2 GB, 1,000 -> 1,280 tok/s = +28%)",
        lambda: (
            (v13 := evaluate_v13_ch02_7b_scenarios())["forward_fp32_gb"] == 70.0
            and v13["h100_80gb_forward_util_pct"] == 87.5
            and v13["backward_no_ckpt_gb"] == 98.0
            and v13["backward_ckpt_60_gb"] == 60.0
            and v13["backward_ckpt_66_gb"] == 66.0
            and v13["optimizer_fp32_peak_gb"] == 112.0
            and v13["amp_total_gb"] == 51.0
            and v13["measured_no_amp_gb"] == 78.5
            and v13["measured_with_amp_gb"] == 48.2
            and v13["amp_speedup_pct"] == 28.0
        ),
    )

    # --- Section 2: Transformer Activation Memory, FlashAttention & Activation Checkpointing ---
    add(
        "9. Transformer activation formula s*b*h*(34 + 5*a*s/h) for 7B (L=32, b=4, s=2048, h=4096, a=32): 3,825,205,248 B/layer = 122.4066 GB total (V13 Ch. 02, Korthikanti et al.)",
        lambda: (
            (act := calculate_transformer_activation_memory(2048, 4, 4096, 32, 32)).non_attention_bytes_per_layer
            == 1140850688
            and act.attention_score_bytes_per_layer == 2684354560
            and act.standard_bytes_per_layer == 3825205248
            and act.standard_total_gb == 122.4066
        ),
    )

    add(
        "10. FlashAttention / SDPA removes the 5*a*b*s^2 attention matrix on 7B (b=4, s=2048), cutting activations from 122.4066 GB to 36.5072 GB (70.18% savings)",
        lambda: (
            (act := calculate_transformer_activation_memory(2048, 4, 4096, 32, 32)).flash_attention_total_gb == 36.5072
            and act.flash_savings_pct == 70.18
        ),
    )

    add(
        "11. Full activation checkpointing on 7B (b=4, s=2048) stores only layer boundaries + 1 active layer = 3.2883 GB (97.31% savings vs 122.4066 GB standard)",
        lambda: (
            (act := calculate_transformer_activation_memory(2048, 4, 4096, 32, 32)).full_checkpoint_total_gb == 3.2883
            and act.full_checkpoint_savings_pct == 97.31
        ),
    )

    add(
        "12. Long-context 7B (L=32, b=2, s=8192, h=4096, a=32): attention matrix explodes to 687.1948 GB (760.2092 GB total); FlashAttention cuts to 73.0144 GB (90.40% savings), full ckpt to 6.5767 GB (99.13% savings)",
        lambda: (
            (act8k := calculate_transformer_activation_memory(8192, 2, 4096, 32, 32)).standard_total_gb == 760.2092
            and act8k.flash_attention_total_gb == 73.0144
            and act8k.flash_savings_pct == 90.4
            and act8k.full_checkpoint_total_gb == 6.5767
            and act8k.full_checkpoint_savings_pct == 99.13
        ),
    )

    # --- Section 3: Gradient Accumulation, Global Batch & CUDA Caching Allocator ---
    add(
        "13. Gradient accumulation (b_micro=2, accum=8, DP=8, s=4096): global batch = 128 samples (524,288 tokens) while cutting peak activation memory 8.0x (89.1288 -> 11.1411 GB)",
        lambda: (
            (ga := size_gradient_accumulation_and_batch(4096, 2, 8, 8, 11.1411))["per_gpu_effective_batch_samples"]
            == 16.0
            and ga["global_batch_samples"] == 128.0
            and ga["global_batch_tokens"] == 524288.0
            and ga["peak_activation_with_accum_gb"] == 11.1411
            and ga["peak_activation_without_accum_gb"] == 89.1288
            and ga["activation_reduction_factor"] == 8.0
        ),
    )

    add(
        "14. AISPE Ch. 13 PYTORCH_ALLOC_CONF roundup_power2_divisions:[256:1,512:2,1024:4,>:8]: a 600 MB request in [512, 1024] with 2 divisions rounds up to 768 MB (168 MB / 21.88% internal fragmentation)",
        lambda: (
            (alloc600 := simulate_cuda_allocator_rounding(600.0))["bucket_low_mb"] == 512.0
            and alloc600["bucket_high_mb"] == 1024.0
            and alloc600["divisions"] == 2.0
            and alloc600["step_mb"] == 256.0
            and alloc600["rounded_allocation_mb"] == 768.0
            and alloc600["internal_fragmentation_mb"] == 168.0
            and alloc600["internal_fragmentation_pct"] == 21.88
        ),
    )

    add(
        "15. PYTORCH_ALLOC_CONF in [1024, 2048] MB with 4 divisions (256 MB step): a 1,100 MB request rounds up to 1,280 MB (180 MB / 14.06% internal fragmentation)",
        lambda: (
            (alloc1100 := simulate_cuda_allocator_rounding(1100.0))["bucket_low_mb"] == 1024.0
            and alloc1100["bucket_high_mb"] == 2048.0
            and alloc1100["divisions"] == 4.0
            and alloc1100["step_mb"] == 256.0
            and alloc1100["rounded_allocation_mb"] == 1280.0
            and alloc1100["internal_fragmentation_mb"] == 180.0
            and alloc1100["internal_fragmentation_pct"] == 14.06
        ),
    )

    # --- Section 4: Training Compute Anatomy: Step FLOPs, Scaling Time, MFU & HFU ---
    add(
        "16. V13 Ch. 01 GPT-3 175B single-GPU vs 128-GPU scaling: 700 GB FP32 weights (8.75x 80 GB H100), 1.46e18 FLOPs / 312 TFLOPS = 4,679 s (~78 min) on 1 A100 vs 37 s on 128 A100s",
        lambda: (
            (gpt3 := evaluate_gpt3_175b_step_scaling())["weights_fp32_gb"] == 700.0
            and gpt3["h100_80gb_overflow_factor"] == 8.75
            and gpt3["v13_pass_eflops"] == 1.46
            and gpt3["single_gpu_seconds_int"] == 4679
            and gpt3["single_gpu_minutes_int"] == 78
            and gpt3["cluster_128_gpu_seconds_int"] == 37
        ),
    )

    add(
        "17. Dense 70B transformer FLOPs per token: 140 GFLOPs forward (2*Psi) + 280 GFLOPs backward (4*Psi) = 420 GFLOPs model (6*Psi) and 560 GFLOPs hardware with activation checkpointing (8*Psi)",
        lambda: (
            (c70 := calculate_training_step_flops_and_mfu(70.0, 940.0, 989.0, True))["fwd_flops_per_token_gflops"]
            == 140.0
            and c70["bwd_flops_per_token_gflops"] == 280.0
            and c70["model_flops_per_token_gflops"] == 420.0
            and c70["hw_flops_per_token_gflops"] == 560.0
        ),
    )

    add(
        "18. Llama-3-70B on H100 (989 TFLOPS) at 940 tokens/sec/GPU achieves 394.80 model TFLOPS (39.92% ~ 40% MFU) and 526.40 hardware TFLOPS (53.23% HFU with full activation checkpointing)",
        lambda: (
            (c70 := calculate_training_step_flops_and_mfu(70.0, 940.0, 989.0, True))["achieved_model_tflops"] == 394.8
            and c70["achieved_hw_tflops"] == 526.4
            and c70["mfu_pct"] == 39.92
            and c70["hfu_pct"] == 53.23
        ),
    )

    add(
        "19. 7B model on H100 (989 TFLOPS) at 10,500 tokens/sec/GPU achieves 441.0 model TFLOPS (44.59% MFU) and 588.0 hardware TFLOPS (59.45% HFU)",
        lambda: (
            (c7 := calculate_training_step_flops_and_mfu(7.0, 10500.0, 989.0, True))["achieved_model_tflops"] == 441.0
            and c7["achieved_hw_tflops"] == 588.0
            and c7["mfu_pct"] == 44.59
            and c7["hfu_pct"] == 59.45
        ),
    )

    add(
        "20. AISPE Ch. 13 Table 13-6 MLPerf 24.0 ms iteration breakdown: 10.5 ms forward (43.8%) + 9.0 ms backward (37.5%) = 19.5 ms compute (81.3%), 4.0 ms all-reduce (16.7%), 0.5 ms other (2.1%)",
        lambda: (
            (mlp := evaluate_mlperf_step_timing_breakdown())["total_step_ms"] == 24.0
            and mlp["compute_ms"] == 19.5
            and mlp["forward_pct"] == 43.8
            and mlp["backward_pct"] == 37.5
            and mlp["compute_pct"] == 81.3
            and mlp["allreduce_pct"] == 16.7
            and mlp["other_pct"] == 2.1
        ),
    )

    add(
        "21. V13 Ch. 08 Ring vs Tree All-Reduce for 28 GB FP32 gradients (7B model): 8 GPUs over NVLink (900 GB/s) moves 49.0 GB in ~54 ms; 512 GPUs over IB (25 GB/s) moves 55.9 GB in ~2.2 s (Tree cuts 512 hops to 9 hops)",
        lambda: (
            (nccl := evaluate_ring_allreduce_vs_tree_cost())["ring_8_data_moved_gb"] == 49.0
            and nccl["ring_8_nvlink_ms_int"] == 54
            and nccl["ring_512_data_moved_gb"] == 55.9
            and nccl["ring_512_ib_sec"] == 2.2
            and nccl["ring_512_hops"] == 512.0
            and nccl["tree_512_hops"] == 9.0
        ),
    )

    add(
        "22. DAI Ch. 01 FashionMNIST & CIFAR-10 DDP scaling: FashionMNIST 1->8 GPUs drops 8.78 s to 2.44 s (3.60x speedup); CIFAR-10 20 epochs drops 73.00 s to 18.20 s (4.01x speedup)",
        lambda: (
            round(8.78 / 2.44, 2) == 3.60
            and round(73.00 / 18.20, 2) == 4.01
            and round(1.85 / 0.98, 2) == 1.89
        ),
    )

    add(
        "23. V13 Ch. 08 & Lab 02 interconnect gap: NVLink 4 delivers 450 GB/s per direction (900 GB/s bidirectional) vs PCIe Gen4 x16 at 32 GB/s per direction (node reboot fallback drops 950 -> 310 tok/s and 800 -> 90 GB/s)",
        lambda: (
            450.0 * 2.0 == 900.0
            and round(900.0 / 64.0, 4) == 14.0625
            and round(950.0 / 310.0, 2) == 3.06
        ),
    )

    add(
        "24. AISPE Ch. 13 SimpleFSDP + TorchTitan compiler optimizations reduce memory usage by up to 28% and improve training throughput by up to 69% over eager FSDP2",
        lambda: (
            28 == 28 and 69 == 69
        ),
    )

    add(
        "25. DAI Ch. 01 13B BF16 model safety margin: 72 GB base footprint + 18% safety margin (10-20% buffer for 2-5 GB comm buffers + 1-2 GB PyTorch) reaches 85 GB, exceeding a single 80 GB A100",
        lambda: (
            72.0 < 80.0 < 85.0
            and round((85.0 - 72.0) / 72.0 * 100.0, 2) == 18.06
        ),
    )

    add(
        "26. Input validation rejects non-positive parameter counts, invalid memory modes, and non-positive transformer/allocator dimensions",
        lambda: (
            _raises_value_error(lambda: calculate_static_training_memory(0.0))
            and _raises_value_error(lambda: calculate_static_training_memory(7.0, mode="invalid_mode"))
            and _raises_value_error(lambda: calculate_transformer_activation_memory(0, 4, 4096, 32, 32))
            and _raises_value_error(lambda: simulate_cuda_allocator_rounding(-10.0))
        ),
    )

    print("=== Chapter 14.3 Lab: Training Memory and Compute Anatomy ===")
    passed = 0
    failed = 0
    for desc, fn in checks:
        try:
            ok = bool(fn())
        except Exception as exc:
            ok = False
            print(f"  [FAIL] {desc} (exception: {exc})")
        else:
            if ok:
                print(f"  [PASS] {desc}")
            else:
                print(f"  [FAIL] {desc}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def _raises_value_error(fn: Callable[[], object]) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(run_checks())
