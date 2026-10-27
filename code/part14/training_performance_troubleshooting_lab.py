#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.12: Training Performance Engineering and Troubleshooting."""

from __future__ import annotations
import sys
from training_performance_troubleshooting import (
    compute_mfu_hfu_and_goodput,
    evaluate_wasted_cluster_cost,
    analyze_step_scaling_and_amdahl,
    reconcile_moe_and_mlperf_profiles,
    classify_training_bottleneck,
    evaluate_compiler_allocator_and_overlap,
    analyze_nccl_collectives_and_stragglers,
    summarize_llama3_405b_interruptions,
    evaluate_ci_regression_and_hardware_degradation,
)


def run_lab() -> int:
    print("=== Chapter 14.12 Lab: Training Performance Engineering and Troubleshooting ===")
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

    # 1. MFU, HFU, and Goodput (`V13` Ch. 11, `ASP` Ch. 1)
    mfu_before = compute_mfu_hfu_and_goodput(params_b=70.0, tokens_per_sec=3200.0, num_gpus=8, peak_tflops_per_gpu=989.0)
    check(
        "1. 70B model on 8x H100 SXM (989 TFLOPS/GPU = 7,912 TFLOPS peak) at 3,200 tok/s yields 1,344 TFLOPS and 16.99% (~17%) MFU",
        mfu_before["cluster_peak_tflops"] == 7912.0
        and mfu_before["achieved_tflops"] == 1344.0
        and mfu_before["mfu_pct"] == 16.99,
    )

    mfu_after = compute_mfu_hfu_and_goodput(params_b=70.0, tokens_per_sec=9000.0, num_gpus=8, peak_tflops_per_gpu=989.0)
    check(
        "2. Fixing DataLoader bottleneck raises throughput to 9,000 tok/s -> 3,780 TFLOPS and 47.78% (~48%) MFU (2.8125x gain)",
        mfu_after["achieved_tflops"] == 3780.0
        and mfu_after["mfu_pct"] == 47.78
        and round(9000.0 / 3200.0, 4) == 2.8125,
    )

    check(
        "3. With full activation recomputation (8N vs 6N), 47.78% MFU corresponds to 5,040 TFLOPS and 63.70% HFU (HFU > MFU)",
        mfu_after["hfu_tflops"] == 5040.0
        and mfu_after["hfu_pct"] == 63.70
        and mfu_after["hfu_pct"] > mfu_after["mfu_pct"],
    )

    check(
        "4. Cluster goodput of 100,000 tokens in 10 s (10,000 tok/s) vs 8 x 1,500 = 12,000 tok/s peak yields 83.33% (~83.3%) efficiency",
        mfu_after["realized_goodput_tok_s"] == 10000.0
        and mfu_after["peak_cluster_tok_s"] == 12000.0
        and mfu_after["goodput_efficiency_pct"] == 83.33,
    )

    # 2. Wasted Cluster Cost (`DAI` Ch. 10 64-GPU Case Study)
    waste = evaluate_wasted_cluster_cost(num_gpus=64, gpu_util_pct=45.0, scaling_efficiency_pct=52.0, run_hours=336.0)
    check(
        "5. 64 GPUs at 52% scaling efficiency deliver 33.28 (~33) effective GPUs and waste 30.72 (~31) GPUs (10,321.92 GPU-hours over 336 hours)",
        waste["effective_gpus"] == 33.28
        and waste["wasted_gpus"] == 30.72
        and waste["wasted_gpu_hours"] == 10321.92,
    )

    check(
        "6. Over a 2-week (336-hour) run, 30.72 wasted GPUs cost $41,287.68 at $4/GPU-hr and $51,609.60 (~$50,000) at $5/GPU-hr",
        waste["wasted_cost_low_usd"] == 41287.68 and waste["wasted_cost_high_usd"] == 51609.60,
    )

    # 3. Step-Time Scaling & Amdahl's Law (`DAI` Ch. 10)
    scaling = analyze_step_scaling_and_amdahl(single_gpu_step_ms=155.0, scaled_gpu_step_ms=33.0, num_gpus=16, scaled_comm_share_pct=55.0, serial_fraction=0.10)
    check(
        "7. Scaling from 1 GPU (155.0 ms, 0% comm) to 16 GPUs (33.0 ms, 55% comm = 18.15 ms comm + 14.85 ms compute) yields 4.697x speedup (29.36% efficiency)",
        scaling["speedup"] == 4.697
        and scaling["scaling_efficiency_pct"] == 29.36
        and scaling["comm_ms"] == 18.15
        and scaling["compute_ms"] == 14.85,
    )

    check(
        "8. Amdahl's Law with 10% serial work (s=0.10) caps asymptotic speedup at 10.0x (and 8.77x at N=64 GPUs)",
        scaling["amdahl_max_speedup"] == 10.0 and scaling["amdahl_speedup_64"] == 8.77,
    )

    # 4. MoE & MLPerf Profile Reconciliation (`ASP` Ch. 13 Tables 13-2, 13-3, 13-6)
    prof = reconcile_moe_and_mlperf_profiles()
    check(
        "9. 64-expert MoE torch.profiler top-10 ops sum to 138.00 ms across 320 calls: GEMMs = 78.50 ms (56.88%), routing = 30.80 ms (22.32%), other 6 ops = 28.70 ms (20.80%)",
        prof["moe_total_cuda_ms"] == 138.0
        and prof["moe_total_calls"] == 320
        and prof["moe_gemm_ms"] == 78.5
        and prof["moe_gemm_pct"] == 56.88
        and prof["moe_routing_ms"] == 30.8
        and prof["moe_routing_pct"] == 22.32
        and prof["moe_other_ops_ms"] == 28.7
        and prof["moe_other_ops_pct"] == 20.80,
    )

    check(
        "10. Nsight Systems nvtx_gpu_proj_sum reconciles forward (60.5 ms, 43.84%) + backward (58.3 ms, 42.25%) + optimizer_step (19.2 ms, 13.91%) = 138.0 ms",
        prof["nvtx_total_ms"] == 138.0
        and prof["nvtx_forward_pct"] == 43.84
        and prof["nvtx_backward_pct"] == 42.25
        and prof["nvtx_optimizer_pct"] == 13.91,
    )

    check(
        "11. MLPerf Logging 24.0 ms step decomposes into 19.5 ms compute (10.5 ms fwd + 9.0 ms bwd = 81.2% / 81.3%), 4.0 ms AllReduce (16.7% = 1/6), and 0.5 ms other (2.1%)",
        prof["mlperf_step_ms"] == 24.0
        and prof["mlperf_compute_ms"] == 19.5
        and prof["mlperf_allreduce_ms"] == 4.0
        and prof["mlperf_allreduce_pct"] == 16.7
        and prof["mlperf_other_pct"] == 2.1,
    )

    # 5. Top-Down Bottleneck Decision Tree (`V13` Ch. 11)
    b_dl = classify_training_bottleneck(gpu_util_pct=30.0, mfu_pct=10.0, cpu_util_or_iowait_pct=95.0, tensor_core_active_pct=15.0)
    check(
        "12. Low GPU util (30%) + low MFU (10%-17%) + high CPU/IO-wait (95%) is classified as DATALOADER_CPU_IO_BOTTLENECK",
        b_dl["category"] == "DATALOADER_CPU_IO_BOTTLENECK" and "iostat -x 1" in b_dl["first_command"],
    )

    b_mem = classify_training_bottleneck(gpu_util_pct=99.0, mfu_pct=22.0, cpu_util_or_iowait_pct=25.0, tensor_core_active_pct=18.0, nccl_wait_ms=2.0)
    check(
        "13. 98%-100% GPU util + 22% MFU + low Tensor Core activity (18%) is classified as MEMORY_BANDWIDTH_BOUND_UNFUSED_KERNELS",
        b_mem["category"] == "MEMORY_BANDWIDTH_BOUND_UNFUSED_KERNELS"
        and "sm__throughput.avg.pct_of_peak_sustained_elapsed" in b_mem["first_command"],
    )

    b_strag = classify_training_bottleneck(gpu_util_pct=95.0, mfu_pct=24.0, cpu_util_or_iowait_pct=20.0, tensor_core_active_pct=25.0, nccl_wait_ms=200.0)
    check(
        "14. 200 ms NCCL Wait state across 63/64 nodes is classified as STRAGGLER_NCCL_SPIN_WAIT (dmesg | grep -i 'AER' & kubectl cordon node-14-straggler)",
        b_strag["category"] == "STRAGGLER_NCCL_SPIN_WAIT" and "node-14-straggler" in b_strag["first_command"],
    )

    b_therm = classify_training_bottleneck(gpu_util_pct=98.0, mfu_pct=28.0, cpu_util_or_iowait_pct=25.0, tensor_core_active_pct=45.0, sm_clock_drop_pct=37.78)
    check(
        "15. Gradual MFU decay from 45% to 28% with a 37.78% SM clock drop is classified as THERMAL_THROTTLING (nvidia-smi -q -d TEMPERATURE,CLOCK)",
        b_therm["category"] == "THERMAL_THROTTLING" and "TEMPERATURE,CLOCK" in b_therm["first_command"],
    )

    # 6. Compiler, Allocator, CUDA Graph Pools, SimpleFSDP, and AsyncTP (`ASP` Ch. 13)
    comp = evaluate_compiler_allocator_and_overlap()
    check(
        "16. torch.compile(mode='max-autotune') reduces MoE step time from 248.0 ms to 173.0 ms (75.0 ms / 30.24% saved, 1.43x speedup)",
        comp["compile_saved_ms"] == 75.0
        and comp["compile_reduction_pct"] == 30.24
        and comp["compile_speedup"] == 1.43,
    )

    check(
        "17. PYTORCH_ALLOC_CONF 512:2 rounds 600 MB to 768 MB, whereas expandable_segments:True keeps reserved VRAM at 600 MB (saving 168 MB / 21.88%) alongside [8, 4, 2, 1] CUDA Graph capture",
        comp["rounded_vram_mb"] == 768.0
        and comp["expandable_vram_mb"] == 600.0
        and comp["vram_saved_mb"] == 168.0
        and comp["vram_saved_pct"] == 21.88
        and comp["cudagraph_capture_order"] == [8, 4, 2, 1],
    )

    check(
        "18. TorchTitan SimpleFSDP cuts peak memory by 28% (64.0 -> 46.08 GB) and raises throughput by 69% (10,000 -> 16,900 tok/s); AsyncTP cuts 16.0 ms to 12.6 ms (21.25% reduction)",
        comp["simplefsdp_mem_gb"] == 46.08
        and comp["simplefsdp_tok_s"] == 16900.0
        and comp["asynctp_ms"] == 12.6
        and comp["asynctp_reduction_pct"] == 21.25,
    )

    # 7. NCCL Collectives, Communicator Lifecycle, SHARP, and HTA Stragglers (`ASP` Ch. 4 & 13, `V13` Ch. 8)
    nccl = analyze_nccl_collectives_and_stragglers()
    check(
        "19. Reusing NCCL communicator eliminates 48.0 ms per-step init/destroy overhead, reducing iteration time from 48.5 ms to 0.5 ms (98.97% reduction)",
        nccl["iter_bad_ms"] == 48.5
        and nccl["iter_good_ms"] == 0.5
        and nccl["init_overhead_reduction_pct"] == 98.97,
    )

    check(
        "20. For 28 GB FP32 gradients, 8-GPU Ring on 900 GB/s NVLink moves 49.0 GB in 54.4 ms (8 hops), while 512-GPU Ring on 25 GB/s IB moves 55.89 GB in 2.24 s (512 Ring hops vs 9 Tree hops)",
        nccl["ring_8_data_gb"] == 49.0
        and nccl["ring_8_time_ms"] == 54.4
        and nccl["ring_512_data_gb"] == 55.89
        and nccl["ring_512_time_s"] == 2.24
        and nccl["ring_512_hops"] == 512
        and nccl["tree_512_hops"] == 9,
    )

    check(
        "21. In an 8-rank HTA profile (24.0 ms step), Rank 7 is identified as the compute straggler (21.0 ms compute, 0.0 ms idle) and Rank 0 has the largest idle wait (2.0 ms)",
        nccl["compute_straggler_rank"] == 7
        and nccl["most_idle_rank"] == 0
        and nccl["max_socket_connections"] == 64,
    )

    # 8. Llama 3 405B 54-Day Reliability & Hardware Degradation / CI Gates (`ASP` Ch. 4 Table 4-4, `V13` Ch. 8, 11, 12)
    llama = summarize_llama3_405b_interruptions()
    check(
        "22. Meta's 54-day Llama 3 405B run recorded 419 unexpected interruptions, with Faulty GPU (148, 30.1%) + HBM3 (72, 17.2%) = 220 (47.3%) and all GPU categories = 268 (64.0%)",
        llama["duration_days"] == 54
        and llama["total_interruptions"] == 419
        and llama["top_two_gpu_count"] == 220
        and llama["top_two_gpu_pct"] == 47.3
        and llama["gpu_category_count"] == 268
        and llama["gpu_category_pct"] == 64.0,
    )

    ci_pass = evaluate_ci_regression_and_hardware_degradation(
        baseline_tok_s=10000.0, run_series_tok_s=[9400.0, 9450.0, 9800.0]
    )
    ci_fail = evaluate_ci_regression_and_hardware_degradation(
        baseline_tok_s=10000.0, run_series_tok_s=[9400.0, 9450.0, 9480.0]
    )
    check(
        "23. PyTorch HUD CI regression gate (>=5% drop across 3 consecutive runs) passes transient 2-run noise [9400, 9450, 9800] and fails sustained 3-run regression [9400, 9450, 9480]",
        ci_pass["ci_build_failed"] is False and ci_fail["ci_build_failed"] is True,
    )

    check(
        "24. Thermal throttling MFU drift from 45.0% to 28.0% represents a 37.78% relative drop in achieved compute throughput",
        ci_fail["mfu_initial_pct"] == 45.0
        and ci_fail["mfu_throttled_pct"] == 28.0
        and ci_fail["mfu_relative_drop_pct"] == 37.78,
    )

    check(
        "25. Stopped nvidia-fabricmanager or broken NVLink bridge drops training throughput from 950 to 310 tok/s (-67.37%) and nccl-tests busbw by 20x (400 GB/s -> 20 GB/s)",
        ci_fail["reboot_tok_s_drop_pct"] == 67.37 and ci_fail["nvlink_bridge_bw_drop_factor"] == 20.0,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
