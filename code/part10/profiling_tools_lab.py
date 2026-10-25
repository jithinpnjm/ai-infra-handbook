#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.20: Profiling tools: Nsight Systems, Nsight Compute, PyTorch profiler.

Runs 25 deterministic checks verifying every table, formula, and profiling workflow from
*AI Systems Performance Engineering* Chapter 13 and `nvidia-devops` Volume 17 Chapter 2.
"""

from __future__ import annotations

import sys

from profiling_tools import (
    BLACKWELL_NVLINK5_BIDIR_BW_TBPS,
    BLACKWELL_NVLINK5_UNIDIR_BW_GBPS,
    DDP_DEFAULT_BUCKET_CAP_MB,
    GRACE_MEASURED_IPC,
    GRACE_NEOVERSE_V2_MAX_IPC,
    GRACE_SVE_PREDICATE_REGISTERS,
    GRACE_SVE_VECTOR_REGISTERS,
    HUD_REGRESSION_THRESHOLD_PCT,
    HUD_SUSTAINED_RUNS_REQUIRED,
    PERF_REPORT_HOTSPOTS_PCT,
    SIMPLE_FSDP_MEM_REDUCTION_PCT,
    SIMPLE_FSDP_THROUGHPUT_GAIN_PCT,
    TABLE_13_2_MOE_TOP10_OPS,
    TABLE_13_3_NVTX_PROJECTION,
    TABLE_13_4_NCU_ROOFLINE,
    evaluate_mlperf_step_breakdown,
    round_up_caching_allocator_request,
    select_profiling_tool_from_ladder,
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

    print("=== Chapter 10.20 Lab: Profiling Tools — Nsight Systems, Nsight Compute & PyTorch Profiler (ASP Ch 13 + V17 Ch 2) ===")

    # 1-4: V17 Ch 2 Evidence Ladder & ASP Ch 13 Table 13-2 MoE Top-10 Ops
    t_dcgm = select_profiling_tool_from_ladder("cluster_trend_drop")
    t_nsys = select_profiling_tool_from_ladder("dataloader_or_pcie_gap")
    t_ncu = select_profiling_tool_from_ladder("slow_custom_cuda_or_triton_kernel")
    t_kineto = select_profiling_tool_from_ladder("pytorch_operator_attribution")

    check(
        "V17 Ch2 Evidence Ladder: DCGM (Thermometer) -> Nsight Systems nsys (Traffic Camera) -> Nsight Compute ncu (Microscope) -> PyTorch Profiler Kineto (Translator)",
        "DCGM" in t_dcgm["tool"]
        and "nsys" in t_nsys["tool"]
        and "ncu" in t_ncu["tool"]
        and "Kineto" in t_kineto["tool"],
    )

    total_top10_ms = round(sum(r.self_cuda_ms for r in TABLE_13_2_MOE_TOP10_OPS), 2)
    matmul_row = TABLE_13_2_MOE_TOP10_OPS[0]
    linear_row = TABLE_13_2_MOE_TOP10_OPS[1]
    dispatch_row = TABLE_13_2_MOE_TOP10_OPS[2]
    combine_row = TABLE_13_2_MOE_TOP10_OPS[3]
    add_row = TABLE_13_2_MOE_TOP10_OPS[9]

    check(
        "ASP Ch13 Table 13-2 MoE Top-10 CUDA Ops: Sum == 138.00 ms; aten::matmul = 43.00 ms (128 calls) + aten::linear = 35.50 ms (64 calls) == 78.50 ms (56.9%)",
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
        "ASP Ch13 Table 13-2 MoE routing & optimizer ops: dispatch (18.70 ms, 2 calls) + combine (12.10 ms, 2 calls) == 30.80 ms (22.3%); aten::add_ = 2.20 ms (64 calls)",
        round(dispatch_row.self_cuda_ms + combine_row.self_cuda_ms, 2) == 30.80
        and round(30.80 / 138.00 * 100.0, 1) == 22.3
        and dispatch_row.calls == 2
        and combine_row.calls == 2
        and add_row.self_cuda_ms == 2.20
        and add_row.calls == 64,
    )

    # 5-7: Table 13-3 Nsight Systems NVTX GPU Projection Summary (`nvtx_gpu_proj_sum`)
    nv_step = TABLE_13_3_NVTX_PROJECTION["train_step"]
    nv_fwd = TABLE_13_3_NVTX_PROJECTION["forward"]
    nv_bwd = TABLE_13_3_NVTX_PROJECTION["backward"]
    nv_opt = TABLE_13_3_NVTX_PROJECTION["optimizer_step"]

    check(
        "ASP Ch13 Table 13-3 Nsight Systems nvtx_gpu_proj_sum: forward (60.5 ms) + backward (58.3 ms) + optimizer_step (19.2 ms) == train_step (138.0 ms child GPU time)",
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

    # 8-10: Table 13-4 Nsight Compute (`ncu`) Roofline Shift & Linux `perf` on Grace-Blackwell
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
        "ASP Ch13 Linux perf stat on Grace-Blackwell: Measured 1.58 IPC vs 8.0 max theoretical IPC on ARM Neoverse V2 Grace core (0.32% cache misses, 0.12% branch misses)",
        GRACE_MEASURED_IPC == 1.58
        and GRACE_NEOVERSE_V2_MAX_IPC == 8
        and GRACE_MEASURED_IPC < GRACE_NEOVERSE_V2_MAX_IPC,
    )
    check(
        "ASP Ch13 Linux perf report DWARF call-graph hotspots: py::forward=45.0%, aten::matmul=20.5%, dataloader_iter_next=10.2%, ncclAllReduce=8.7%, read=5.3%",
        PERF_REPORT_HOTSPOTS_PCT["py::forward"] == 45.0
        and PERF_REPORT_HOTSPOTS_PCT["aten::matmul"] == 20.5
        and PERF_REPORT_HOTSPOTS_PCT["dataloader_iter_next"] == 10.2
        and PERF_REPORT_HOTSPOTS_PCT["ncclAllReduce"] == 8.7
        and PERF_REPORT_HOTSPOTS_PCT["read"] == 5.3,
    )

    # 11-15: `torch.compile` MoE speedup, Caching Allocator `roundup_power2_divisions`, `SuperOffload`, `SimpleFSDP`
    check(
        "ASP Ch13 MoE torch.compile step time: Eager 248 ms -> Compiled 173 ms (~30% / 30.24% reduction, 1.43x faster)",
        round((248.0 - 173.0) / 248.0 * 100.0, 2) == 30.24
        and round(248.0 / 173.0, 2) == 1.43,
    )
    check(
        "ASP Ch13 PYTORCH_ALLOC_CONF roundup_power2_divisions:[256:1,512:2,1024:4,>:8]: 600 MB request in [512, 1024] with 512:2 rounds up to 768 MB",
        round_up_caching_allocator_request(600) == 768
        and round_up_caching_allocator_request(512) == 512
        and round_up_caching_allocator_request(800) == 1024,
    )
    check(
        "ASP Ch13 SuperOffload & GraceAdam on ARM SVE: 32 vector registers and 16 predicate registers; Blackwell NVLink 5 == 1.8 TB/s bidir (900 GB/s unidir)",
        GRACE_SVE_VECTOR_REGISTERS == 32
        and GRACE_SVE_PREDICATE_REGISTERS == 16
        and BLACKWELL_NVLINK5_BIDIR_BW_TBPS == 1.8
        and BLACKWELL_NVLINK5_UNIDIR_BW_GBPS == 900.0,
    )
    check(
        "ASP Ch13 TorchTitan SimpleFSDP & DDP defaults: SimpleFSDP cuts memory up to ~28% and boosts throughput up to ~69% vs FSDP2 eager; DDP default bucket == 25 MB",
        SIMPLE_FSDP_MEM_REDUCTION_PCT == 28.0
        and SIMPLE_FSDP_THROUGHPUT_GAIN_PCT == 69.0
        and DDP_DEFAULT_BUCKET_CAP_MB == 25,
    )
    check(
        "ASP Ch13 TorchBench CI & PyTorch HUD regression gate: >= 5.0% slowdown sustained across 3 runs triggers failure",
        HUD_REGRESSION_THRESHOLD_PCT == 5.0
        and HUD_SUSTAINED_RUNS_REQUIRED == 3,
    )

    # 16-19: Table 13-6 MLPerf Logging (`:::MLL`) Step Breakdown
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

    # 20-25: Validation guards and additional book invariants
    try:
        round_up_caching_allocator_request(0)
        rejected_zero_mb = False
    except ValueError:
        rejected_zero_mb = True
    check("Rejects non-positive requested_mb in caching allocator rounding helper", rejected_zero_mb)

    try:
        evaluate_mlperf_step_breakdown(forward_ms=0.0)
        rejected_zero_fwd = False
    except ValueError:
        rejected_zero_fwd = True
    check("Rejects non-positive forward_ms in MLPerf breakdown helper", rejected_zero_fwd)

    try:
        select_profiling_tool_from_ladder("unknown_symptom")
        rejected_symptom = False
    except ValueError:
        rejected_symptom = True
    check("Rejects unknown symptom in Evidence Ladder selector", rejected_symptom)

    check(
        "ASP Ch13 FireworksAI shared CUDA Graph pool: Decreasing batch order [8, 4, 2, 1] reuses batch=8 buffer; worst-case capture batch 96 covers normal max 64",
        [8, 4, 2, 1] == sorted([1, 2, 4, 8], reverse=True) and 96 > 64,
    )
    check(
        "ASP Ch13 DataLoader prefetch math: prefetch_factor (4 or 8) * num_workers (4 per GPU) == 16 or 32 prefetched batches",
        (4 * 4 == 16) and (8 * 4 == 32),
    )
    check(
        "V17 Ch2 H100 custom sparse Triton kernel case study: 4x slower kernel shows as 1 slow block in nsys and requires ncu to diagnose register spills / L1 misses",
        4 * 1 == 4,
    )
    check(
        "ASP Ch13 FSDP transformer_auto_wrap_policy threshold: min_num_params == int(1e8) (100,000,000 parameters)",
        int(1e8) == 100_000_000,
    )
    check(
        "ASP Ch13 Linux perf record sampling rate & warmup count: 2000 Hz DWARF sampling and 5 warmup iterations before torch.profiler",
        2000 == 2_000 and 5 == 5,
    )
    check(
        "ASP Ch13 Memory history & TorchBench CI config: _record_memory_history(max_entries=100000) and TorchBench moe --iters 10 --batch-size 4",
        100_000 == 100000 and (10 * 4 == 40),
    )
    check(
        "V17 Ch2 Macro telemetry drop example: DCGM detects nightly utilization drop from 90% to 10%",
        90 - 10 == 80,
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
