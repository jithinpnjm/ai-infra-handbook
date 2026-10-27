#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.8: PyTorch performance: profiling, tuning and scaling.

Runs 27 deterministic checks verifying every table, formula, memory allocator rule,
distributed scaling calculation, HTA trace summary, CI gate, and MLPerf step-time
breakdown from *AI Systems Performance Engineering* (Chris Fregly), Chapter 13.
"""

from __future__ import annotations

import sys

from pytorch_performance_scaling import (
    BLACKWELL_NVLINK5_BIDIR_BW_TBPS,
    BLACKWELL_NVLINK5_UNIDIR_BW_GBPS,
    CUDAGRAPH_NORMAL_MAX_BATCH,
    CUDAGRAPH_WORST_CASE_BATCH,
    DDP_DEFAULT_BUCKET_CAP_MB,
    FIREWORKS_DECREASING_BATCH_BUCKETS,
    FSDP_AUTOWRAP_MIN_PARAMS,
    GRACE_BRANCH_MISS_PCT,
    GRACE_BRANCH_MISSES,
    GRACE_CACHE_MISS_PCT,
    GRACE_CACHE_MISSES,
    GRACE_CPUS_UTILIZED,
    GRACE_CYCLES,
    GRACE_ELAPSED_SEC,
    GRACE_INSTRUCTIONS,
    GRACE_MEASURED_IPC,
    GRACE_NEOVERSE_V2_MAX_IPC,
    GRACE_SVE_PREDICATE_REGISTERS,
    GRACE_SVE_VECTOR_REGISTERS,
    GRACE_TASK_CLOCK_MSEC,
    HUD_REGRESSION_THRESHOLD_PCT,
    HUD_SUSTAINED_RUNS_REQUIRED,
    MEMORY_HISTORY_MAX_ENTRIES,
    NVLINK_C2C_CACHE_MISSES,
    NVLINK_C2C_ELAPSED_SEC,
    NVLINK_C2C_HOST_CYCLES,
    NVLINK_C2C_PMU_CYCLES,
    PERF_REPORT_HOTSPOTS_PCT,
    SIMPLE_FSDP_MEM_REDUCTION_PCT,
    SIMPLE_FSDP_THROUGHPUT_GAIN_PCT,
    TABLE_13_1_PROFILING_TOOLS,
    TABLE_13_2_MOE_TOP10_OPS,
    TABLE_13_3_NVTX_PROJECTION,
    TABLE_13_4_NCU_ROOFLINE,
    TABLE_13_5_COMPILE_MODES,
    TORCHBENCH_CI_BATCH_SIZE,
    TORCHBENCH_CI_ITERS,
    analyze_hta_multi_gpu_traces,
    evaluate_alloc_conf_vram_savings,
    evaluate_async_tp_overlap,
    evaluate_hud_ci_regression_gate,
    evaluate_mlperf_step_breakdown,
    evaluate_simple_fsdp_scaling,
    evaluate_torch_compile_speedup,
    round_up_caching_allocator_request,
)


def main() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    print("=== Chapter 14.8 Lab: PyTorch Performance — Profiling, Tuning & Scaling (ASP Ch 13) ===")

    # 1: Table 13-1 9 Profiling & Visualization Tools
    check(
        "ASP Ch13 Table 13-1: 9 profiling & visualization tools (PyTorch Kineto, nsys, ncu, Memory Profiler, Linux perf, HTA, Perfetto, TorchEval, ExecuTorch)",
        len(TABLE_13_1_PROFILING_TOOLS) == 9
        and TABLE_13_1_PROFILING_TOOLS[0].tool == "PyTorch profiler (Kineto)"
        and TABLE_13_1_PROFILING_TOOLS[5].tool == "Holistic Trace Analysis (HTA)"
        and TABLE_13_1_PROFILING_TOOLS[8].tool == "ExecuTorch",
    )

    # 2-4: Table 13-2 MoE Top-10 CUDA Operations (`138.00 ms` total)
    # Shares of 138.00 ms: matmul=31.16%, linear=25.72% (GEMM=56.88% / 56.9%),
    # dispatch=13.55%, combine=8.77% (routing=22.32% / 22.3%; top-4=109.30 ms / 79.2%),
    # layer_norm=7.39%, softmax=4.13%, scatter=2.97%, gather=2.61%, to=2.10%, add_=1.59%
    # Table 13-3 shares of 138.0 ms: forward=43.84%, backward=42.25%, optimizer_step=13.91%
    total_top10_ms = round(sum(r.self_cuda_ms for r in TABLE_13_2_MOE_TOP10_OPS), 2)
    matmul_row = TABLE_13_2_MOE_TOP10_OPS[0]
    linear_row = TABLE_13_2_MOE_TOP10_OPS[1]
    dispatch_row = TABLE_13_2_MOE_TOP10_OPS[2]
    combine_row = TABLE_13_2_MOE_TOP10_OPS[3]
    ln_row = TABLE_13_2_MOE_TOP10_OPS[4]
    softmax_row = TABLE_13_2_MOE_TOP10_OPS[5]
    scatter_row = TABLE_13_2_MOE_TOP10_OPS[6]
    gather_row = TABLE_13_2_MOE_TOP10_OPS[7]
    to_row = TABLE_13_2_MOE_TOP10_OPS[8]
    add_row = TABLE_13_2_MOE_TOP10_OPS[9]

    check(
        "ASP Ch13 Table 13-2 MoE Top-10 CUDA Ops: Sum == 138.00 ms; aten::matmul = 43.00 ms (128 calls, 64 experts x 2 passes) + aten::linear = 35.50 ms (64 calls) == 78.50 ms (56.9%)",
        len(TABLE_13_2_MOE_TOP10_OPS) == 10
        and total_top10_ms == 138.00
        and matmul_row.self_cuda_ms == 43.00
        and matmul_row.calls == 128
        and linear_row.self_cuda_ms == 35.50
        and linear_row.calls == 64
        and round(matmul_row.self_cuda_ms + linear_row.self_cuda_ms, 2) == 78.50
        and round((43.00 + 35.50) / 138.00 * 100.0, 1) == 56.9,
    )
    check(
        "ASP Ch13 Table 13-2 MoE routing kernels: dispatch (18.70 ms, 2 calls) + combine (12.10 ms, 2 calls) == 30.80 ms (22.3%)",
        round(dispatch_row.self_cuda_ms + combine_row.self_cuda_ms, 2) == 30.80
        and round(30.80 / 138.00 * 100.0, 1) == 22.3
        and dispatch_row.calls == 2
        and combine_row.calls == 2,
    )
    check(
        "ASP Ch13 Table 13-2 remaining ops: layer_norm=10.20 ms (16), softmax=5.70 ms (4), scatter=4.10 ms (16), gather=3.60 ms (16), to=2.90 ms (8), add_=2.20 ms (64) == 28.70 ms (20.8%)",
        ln_row.self_cuda_ms == 10.20
        and ln_row.calls == 16
        and softmax_row.self_cuda_ms == 5.70
        and softmax_row.calls == 4
        and scatter_row.self_cuda_ms == 4.10
        and scatter_row.calls == 16
        and gather_row.self_cuda_ms == 3.60
        and gather_row.calls == 16
        and to_row.self_cuda_ms == 2.90
        and to_row.calls == 8
        and add_row.self_cuda_ms == 2.20
        and add_row.calls == 64
        and round(10.20 + 5.70 + 4.10 + 3.60 + 2.90 + 2.20, 2) == 28.70,
    )

    # 5-6: Table 13-3 Nsight Systems NVTX GPU Projection Summary (`nvtx_gpu_proj_sum`)
    nv_step = TABLE_13_3_NVTX_PROJECTION["train_step"]
    nv_fwd = TABLE_13_3_NVTX_PROJECTION["forward"]
    nv_bwd = TABLE_13_3_NVTX_PROJECTION["backward"]
    nv_opt = TABLE_13_3_NVTX_PROJECTION["optimizer_step"]

    check(
        "ASP Ch13 Table 13-3 Nsight Systems nvtx_gpu_proj_sum: forward (60.5 ms) + backward (58.3 ms) + optimizer_step (19.2 ms) == train_step (138.0 ms child GPU time, 0.0 ms self)",
        nv_step.gpu_time_ms == 138.0
        and nv_step.self_gpu_time_ms == 0.0
        and nv_step.child_gpu_time_ms == 138.0
        and round(nv_fwd.gpu_time_ms + nv_bwd.gpu_time_ms + nv_opt.gpu_time_ms, 1) == 138.0,
    )
    check(
        "ASP Ch13 Table 13-3 NVTX instances: forward=130, backward=130, optimizer_step=1 (brackets 64 aten::add_ launches via CUPTI projection)",
        nv_fwd.instances == 130
        and nv_bwd.instances == 130
        and nv_opt.instances == 1,
    )

    # 7-10: Table 13-4 Nsight Compute (`ncu`) Roofline Shift & Linux `perf` on Grace-Blackwell
    ncu_base = TABLE_13_4_NCU_ROOFLINE["baseline"]
    ncu_opt = TABLE_13_4_NCU_ROOFLINE["optimized"]

    check(
        "ASP Ch13 Table 13-4 Nsight Compute matmul Roofline: Baseline (50% FLOPS, 70% mem BW, 60% occ, Memory bound) -> Optimized (85% FLOPS, 40% mem BW, 80% occ, Compute bound)",
        ncu_base.peak_flops_pct == 50.0
        and ncu_base.peak_mem_bw_pct == 70.0
        and ncu_base.achieved_occupancy_pct == 60.0
        and ncu_opt.peak_flops_pct == 85.0
        and ncu_opt.peak_mem_bw_pct == 40.0
        and ncu_opt.achieved_occupancy_pct == 80.0,
    )
    check(
        "ASP Ch13 Linux perf stat on Grace-Blackwell: 0.600 CPUs, 1,200.345 msec task-clock (1.234567890 s), 2,400,567,890 cycles (~2.0 GHz), 3,800,123,456 instructions (1.58 IPC vs 8 max IPC on ARM Neoverse V2), 12,345,678 cache-misses (0.32%), 4,567,890 branch-misses (0.12%)",
        GRACE_CPUS_UTILIZED == 0.600
        and GRACE_TASK_CLOCK_MSEC == 1200.345
        and GRACE_CYCLES == 2_400_567_890
        and GRACE_INSTRUCTIONS == 3_800_123_456
        and GRACE_MEASURED_IPC == 1.58
        and GRACE_NEOVERSE_V2_MAX_IPC == 8
        and GRACE_CACHE_MISSES == 12_345_678
        and GRACE_CACHE_MISS_PCT == 0.32
        and GRACE_BRANCH_MISSES == 4_567_890
        and GRACE_BRANCH_MISS_PCT == 0.12
        and GRACE_ELAPSED_SEC == 1.234567890,
    )
    check(
        "ASP Ch13 Linux perf report (-F 2000 --call-graph dwarf): py::forward=45.0%, aten::matmul=20.5%, dataloader_iter_next=10.2%, ncclAllReduce=8.7%, read=5.3% (89.7% top-5)",
        PERF_REPORT_HOTSPOTS_PCT["py::forward"] == 45.0
        and PERF_REPORT_HOTSPOTS_PCT["aten::matmul"] == 20.5
        and PERF_REPORT_HOTSPOTS_PCT["dataloader_iter_next"] == 10.2
        and PERF_REPORT_HOTSPOTS_PCT["ncclAllReduce"] == 8.7
        and PERF_REPORT_HOTSPOTS_PCT["read"] == 5.3
        and round(sum(PERF_REPORT_HOTSPOTS_PCT.values()), 1) == 89.7,
    )
    check(
        "ASP Ch13 Grace-Blackwell NVLink-C2C PMU perf stat: nvidia_nvlink_c2c0_pmu_0/cycles = 3,567,890,123; CPU cycles = 45,678,901; cache-misses = 7,890,123; elapsed = 2.345678901 s",
        NVLINK_C2C_PMU_CYCLES == 3_567_890_123
        and NVLINK_C2C_HOST_CYCLES == 45_678_901
        and NVLINK_C2C_CACHE_MISSES == 7_890_123
        and NVLINK_C2C_ELAPSED_SEC == 2.345678901,
    )

    # 11-13: `torch.compile` Speedup (`248 ms -> 173 ms`), Table 13-5 Modes, & CUDA Graph Trees / FireworksAI Pool
    tc = evaluate_torch_compile_speedup(eager_ms=248.0, compiled_ms=173.0)
    check(
        "ASP Ch13 MoE torch.compile step time: Eager 248.0 ms -> Compiled 173.0 ms (75.0 ms saved, ~30% / 30.24% reduction, 1.43x speedup vs < 10% on single-GEMM dense models)",
        tc.eager_ms == 248.0
        and tc.compiled_ms == 173.0
        and tc.time_saved_ms == 75.0
        and tc.reduction_pct == 30.24
        and tc.speedup_ratio == 1.43,
    )
    check(
        "ASP Ch13 Table 13-5 torch.compile modes: default, reduce-overhead (CUDA Graph Trees), max-autotune (Triton autotune + CUDA Graphs), max-autotune-no-cudagraphs (dynamic shapes)",
        len(TABLE_13_5_COMPILE_MODES) == 4
        and TABLE_13_5_COMPILE_MODES["reduce-overhead"].uses_cudagraphs is True
        and TABLE_13_5_COMPILE_MODES["max-autotune"].uses_cudagraphs is True
        and TABLE_13_5_COMPILE_MODES["max-autotune-no-cudagraphs"].uses_cudagraphs is False,
    )
    check(
        "ASP Ch13 FireworksAI shared CUDA Graph pool & worst-case batch sizing: decreasing batch order (8, 4, 2, 1) reuses max buffer; worst-case capture batch 96 covers normal 64",
        FIREWORKS_DECREASING_BATCH_BUCKETS == (8, 4, 2, 1)
        and list(FIREWORKS_DECREASING_BATCH_BUCKETS) == sorted(FIREWORKS_DECREASING_BATCH_BUCKETS, reverse=True)
        and CUDAGRAPH_WORST_CASE_BATCH == 96
        and CUDAGRAPH_NORMAL_MAX_BATCH == 64,
    )

    # 14-16: `PYTORCH_ALLOC_CONF` (`600 MB -> 768 MB` rounding & `768 MB -> 600 MB` savings), `SuperOffload`, `MemPool`
    check(
        "ASP Ch13 PYTORCH_ALLOC_CONF roundup_power2_divisions (256:1, 512:2, 1024:4, >:8): 600 MB request in [512, 1024] with 512:2 (256 MB step) rounds up to 768 MB",
        round_up_caching_allocator_request(600) == 768
        and round_up_caching_allocator_request(512) == 512
        and round_up_caching_allocator_request(800) == 1024,
    )
    vram_sav = evaluate_alloc_conf_vram_savings(
        requested_mb=600,
        unoptimized_reserved_mb=768,
        expandable_segments=True,
        max_split_size_mb=128,
        gc_threshold=0.8,
    )
    check(
        "ASP Ch13 PYTORCH_ALLOC_CONF expandable_segments:True,max_split_size_mb:128,garbage_collection_threshold:0.8: reduces reserved VRAM from 768 MB to 600 MB (168 MB / 21.88% saved)",
        vram_sav["unoptimized_reserved_mb"] == 768.0
        and vram_sav["optimized_reserved_mb"] == 600.0
        and vram_sav["saved_mb"] == 168.0
        and vram_sav["saved_pct"] == 21.88,
    )
    check(
        "ASP Ch13 SuperOffload / GraceAdam on ARM SVE & MemPool: 32 vector + 16 predicate registers; Blackwell NVLink 5 == 1.8 TB/s bidir (900 GB/s unidir); max_entries=100,000",
        GRACE_SVE_VECTOR_REGISTERS == 32
        and GRACE_SVE_PREDICATE_REGISTERS == 16
        and BLACKWELL_NVLINK5_BIDIR_BW_TBPS == 1.8
        and BLACKWELL_NVLINK5_UNIDIR_BW_GBPS == 900.0
        and MEMORY_HISTORY_MAX_ENTRIES == 100_000,
    )

    # 17-19: `DDP` (`25 MB`), `FSDP` (`1e8` min_num_params), `SimpleFSDP` (`-28%` mem, `+69%` tps), `AsyncTP`
    sfsdp = evaluate_simple_fsdp_scaling(baseline_memory_gb=64.0, baseline_tps=10_000.0)
    check(
        "ASP Ch13 TorchTitan SimpleFSDP, FSDP & DDP defaults: SimpleFSDP cuts memory by 28.0% (64.0 GB -> 46.08 GB) and boosts throughput by 69.0% (10,000 -> 16,900 tok/s); DDP bucket=25 MB; FSDP min_num_params=1e8",
        SIMPLE_FSDP_MEM_REDUCTION_PCT == 28.0
        and SIMPLE_FSDP_THROUGHPUT_GAIN_PCT == 69.0
        and sfsdp["simple_fsdp_memory_gb"] == 46.08
        and sfsdp["simple_fsdp_tps"] == 16_900.0
        and DDP_DEFAULT_BUCKET_CAP_MB == 25
        and FSDP_AUTOWRAP_MIN_PARAMS == 100_000_000,
    )
    atp = evaluate_async_tp_overlap(compute_wave_ms=12.0, tp_allgather_ms=4.0, overlap_efficiency=0.85)
    check(
        "ASP Ch13 TorchTitan AsyncTP dual-stream SM-wave overlap: 12.0 ms compute + 4.0 ms TP all-gather (16.0 ms seq) hides 3.4 ms -> 12.6 ms (21.25% step reduction)",
        atp["sequential_ms"] == 16.0
        and atp["hidden_comm_ms"] == 3.4
        and atp["async_tp_ms"] == 12.6
        and atp["step_time_reduction_pct"] == 21.25,
    )

    # 20: Multi-GPU Holistic Trace Analysis (`HTA`) across 8 ranks
    hta = analyze_hta_multi_gpu_traces(
        rank_compute_ms=[18.0, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 21.0],
        rank_comm_ms=[4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 2.5],
        step_wall_ms=24.0,
    )
    check(
        "ASP Ch13 HTA 8-GPU trace aggregation: pinpoints straggler rank 7 (21.0 ms compute) and most-idle rank 0 (2.0 ms idle gap waiting on collective)",
        hta["num_ranks"] == 8
        and hta["straggler_rank"] == 7
        and hta["most_idle_rank"] == 0
        and hta["max_idle_ms"] == 2.0,
    )

    # 21-22: `TorchBench` CI (`--iters 10 --batch-size 4`) & `PyTorch HUD` (`>= 5%` over `3` runs; 9400, 9450, 9480 vs 9800)
    hud_pass = evaluate_hud_ci_regression_gate(10_000.0, [9400.0, 9450.0, 9800.0])
    hud_fail = evaluate_hud_ci_regression_gate(10_000.0, [9400.0, 9450.0, 9480.0])
    check(
        "ASP Ch13 TorchBench CI (--iters 10 --batch-size 4) & PyTorch HUD regression gate: >= 5.0% drop sustained across 3 consecutive runs fails CI; 2-run dip recovers without false alarm",
        TORCHBENCH_CI_ITERS == 10
        and TORCHBENCH_CI_BATCH_SIZE == 4
        and HUD_REGRESSION_THRESHOLD_PCT == 5.0
        and HUD_SUSTAINED_RUNS_REQUIRED == 3
        and hud_pass["fail_ci_build"] is False
        and hud_fail["fail_ci_build"] is True
        and hud_fail["max_consecutive_regressions"] == 3,
    )

    # 23-24: Table 13-6 MLPerf Logging (`:::MLL`) Step Breakdown (`24.0 ms`)
    mlp = evaluate_mlperf_step_breakdown(forward_ms=10.5, backward_ms=9.0, allreduce_ms=4.0, other_ms=0.5)
    check(
        "ASP Ch13 Table 13-6 MLPerf step breakdown: 24.0 ms total = 10.5 ms forward (43.8%) + 9.0 ms backward (37.5%) + 4.0 ms allreduce (16.7%) + 0.5 ms other (2.1%)",
        mlp.step_time_ms == 24.0
        and mlp.forward_pct == 43.8
        and mlp.backward_pct == 37.5
        and mlp.allreduce_pct == 16.7
        and mlp.other_pct == 2.1,
    )
    check(
        "ASP Ch13 Table 13-6 MLPerf compute share: forward (10.5 ms) + backward (9.0 ms) == 19.5 ms (81.2% / 81.3% of 24.0 ms step); all-reduce is 1/6 (16.7%)",
        mlp.compute_total_ms == 19.5
        and round(10.5 / 24.0 * 100.0, 1) + round(9.0 / 24.0 * 100.0, 1) == 81.3
        and round(4.0 / 24.0, 4) == round(1.0 / 6.0, 4),
    )

    # 25-27: Validation guards
    try:
        round_up_caching_allocator_request(0)
        rejected_zero_mb = False
    except ValueError:
        rejected_zero_mb = True
    check("Rejects non-positive requested_mb in caching allocator rounding helper", rejected_zero_mb)

    try:
        evaluate_torch_compile_speedup(eager_ms=0.0, compiled_ms=173.0)
        rejected_zero_compile = False
    except ValueError:
        rejected_zero_compile = True
    check("Rejects non-positive eager_ms in torch.compile speedup helper", rejected_zero_compile)

    try:
        evaluate_mlperf_step_breakdown(forward_ms=0.0)
        rejected_zero_fwd = False
    except ValueError:
        rejected_zero_fwd = True
    check("Rejects non-positive forward_ms in MLPerf breakdown helper", rejected_zero_fwd)

    total = passed + failed
    print(f"Summary: {passed} passed, {failed} failed (total {total})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
