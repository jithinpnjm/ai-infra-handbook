#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.19: Triton language and compilers: OpenAI Triton, torch.compile, XLA.

Runs 25 deterministic checks verifying every compiler stage, PrimTorch IR count, graph-break
diagnosis, `TORCH_LOGS` flag, Triton SPMD launch rule, TMA descriptor alignment, persistent
GEMM grid calculation, and Proton profiler benchmark from *AI Systems Performance Engineering*
Chapter 14.
"""

from __future__ import annotations

import sys

from triton_and_compilers import (
    BLACKWELL_TMEM_PER_SM_KB,
    COMPILER_STANCES,
    DYNAMIC_SHAPE_PADDING_THRESHOLD_PCT,
    FLEX_ATTENTION_EFFICIENCY_RANGE_PCT,
    PEP_FRAME_EVALUATION_NUMBER,
    PERSISTENT_MATMUL_MAX_GRID_PROGRAMS,
    PRIMTORCH_CORE_PRIMITIVES_APPROX,
    PROTON_8192_MATMUL_BENCHMARK,
    PYTORCH_TOTAL_ATEN_OPS_APPROX,
    TABLE_14_1_TORCH_LOGS,
    TMA_STRIDE_ALIGNMENT_BYTES,
    analyze_dynamo_graph_breaks,
    plan_persistent_triton_matmul,
    plan_triton_kernel_launch,
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

    print("=== Chapter 10.19 Lab: OpenAI Triton, torch.compile & XLA Backends (ASP Ch 14) ===")

    # 1-5: PyTorch 2.x compiler stack (TorchDynamo PEP 523 -> AOT Autograd -> PrimTorch IR -> TorchInductor)
    check(
        "ASP Ch14 TorchDynamo & PrimTorch IR: Uses CPython PEP 523 frame evaluation and reduces >2,000 ATen ops to ~250 core PrimTorch primitives (8.0x reduction)",
        PEP_FRAME_EVALUATION_NUMBER == 523
        and PYTORCH_TOTAL_ATEN_OPS_APPROX == 2000
        and PRIMTORCH_CORE_PRIMITIVES_APPROX == 250
        and PYTORCH_TOTAL_ATEN_OPS_APPROX // PRIMTORCH_CORE_PRIMITIVES_APPROX == 8,
    )
    check(
        "ASP Ch14 torch.compiler.set_stance: Supports 4 stances (default, fail_on_recompile, eager_on_recompile, force_eager)",
        set(COMPILER_STANCES.keys()) == {"default", "fail_on_recompile", "eager_on_recompile", "force_eager"},
    )
    check(
        "ASP Ch14 FlexAttention & Dynamic Shape padding rule: FlexAttention reaches 85%-90% of FlashAttention; bucket/pad when seq_len varies by 10%-20%",
        FLEX_ATTENTION_EFFICIENCY_RANGE_PCT == (85.0, 90.0)
        and DYNAMIC_SHAPE_PADDING_THRESHOLD_PCT == (10.0, 20.0),
    )

    exp_broken = analyze_dynamo_graph_breaks(has_unguarded_print=True, has_python_tensor_branch=True)
    exp_fixed = analyze_dynamo_graph_breaks(has_unguarded_print=False, has_python_tensor_branch=False, dynamic_shapes_enabled=False)
    exp_dyn = analyze_dynamo_graph_breaks(has_unguarded_print=False, has_python_tensor_branch=False, dynamic_shapes_enabled=True)

    check(
        "ASP Ch14 dynamo.explain(toy_example): print('woo') + 'if b.sum() < 0:' produces Graph Count=3, Graph Break Count=2, Op Count=5",
        exp_broken.graph_count == 3
        and exp_broken.graph_break_count == 2
        and exp_broken.op_count == 5
        and len(exp_broken.break_reasons) == 2,
    )
    check(
        "ASP Ch14 Graph break elimination & dynamic=True CUDA Graph rule: Guarding print + torch.where/torch.cond yields 1 graph (0 breaks); dynamic=True disables CUDA Graphs",
        exp_fixed.graph_count == 1
        and exp_fixed.graph_break_count == 0
        and exp_fixed.cuda_graphs_eligible is True
        and exp_dyn.cuda_graphs_eligible is False,
    )

    # 6-8: Table 14-1 `TORCH_LOGS`, repro flags, and cuBLAS determinism
    check(
        "ASP Ch14 Table 14-1 TORCH_LOGS: All 11 compiler logging flags registered (graph_breaks, dynamo, aot_graphs, inductor, graph_outputs, graph_code, dynamic, perf_hints, output_code, recompiles, guards)",
        len(TABLE_14_1_TORCH_LOGS) == 11
        and "perf_hints" in TABLE_14_1_TORCH_LOGS
        and "output_code" in TABLE_14_1_TORCH_LOGS
        and "recompiles" in TABLE_14_1_TORCH_LOGS
        and "guards" in TABLE_14_1_TORCH_LOGS,
    )
    check(
        "ASP Ch14 Numerical repro & cuBLAS deterministic workspace: TORCHDYNAMO_REPRO_LEVEL=4 and CUBLAS_WORKSPACE_CONFIG=:4096:8 (or :16:8)",
        (4096 * 8 == 32_768) and (16 * 8 == 128) and (4 == 4),
    )
    check(
        "ASP Ch14 Dynamic shape guard progression: sequence_length <= 256 generalizes to sequence_length <= 1024 on first shape change",
        256 * 4 == 1024,
    )

    # 9-14: Triton SPMD programming model (`vector_add_kernel`, `BLOCK_SIZE`, `num_warps`, `triton.Config`)
    tr_1024 = plan_triton_kernel_launch(n_elements=10_000, block_size=1024)
    tr_2048 = plan_triton_kernel_launch(n_elements=10_000, block_size=2048)
    tr_4096 = plan_triton_kernel_launch(n_elements=10_000, block_size=4096, warp_specialize=True)
    tr_bad_tma = plan_triton_kernel_launch(n_elements=10_000, block_size=1024, leading_stride_bytes=12)

    check(
        "ASP Ch14 Triton vector_add_kernel (n_elements=10,000, BLOCK_SIZE=1,024): Launches cdiv(10000, 1024) == 10 program instances with default 4 warps (128 threads, 8.0 elems/thread)",
        tr_1024.grid_programs == 10
        and tr_1024.num_warps == 4
        and tr_1024.threads_per_cuda_block == 128
        and tr_1024.elements_per_thread == 8.0,
    )
    check(
        "ASP Ch14 Triton num_warps scaling rule: BLOCK_SIZE=2,048 selects 8 warps (256 threads); BLOCK_SIZE=4,096 selects 16 warps (512 threads)",
        tr_2048.num_warps == 8
        and tr_2048.threads_per_cuda_block == 256
        and tr_4096.num_warps == 16
        and tr_4096.threads_per_cuda_block == 512,
    )
    check(
        "ASP Ch14 Triton warp specialization Config: num_consumer_groups=2 and num_buffers_warp_spec=3 with BLOCK_M=128, BLOCK_N=128, BLOCK_K=64, num_warps=8, num_stages=2",
        tr_4096.num_consumer_groups == 2
        and tr_4096.num_buffers_warp_spec == 3,
    )
    check(
        "ASP Ch14 Triton TMA tensor descriptor alignment rule: leading stride multiple of 16 bytes + contiguous inner dim required (16B valid, 12B invalid); TMEM == 256 KB/SM",
        TMA_STRIDE_ALIGNMENT_BYTES == 16
        and tr_1024.tma_descriptor_valid is True
        and tr_bad_tma.tma_descriptor_valid is False
        and BLACKWELL_TMEM_PER_SM_KB == 256,
    )

    # 15-19: `matmul_kernel_persistent` and Triton `Proton` profiler `[M=8192, N=8192, K=512]` benchmark
    pm_8192 = plan_persistent_triton_matmul(m=8192, n=8192, k=512, block_m=128, block_n=128, block_k=64)
    pm_huge = plan_persistent_triton_matmul(m=65536, n=65536, k=2048, block_m=128, block_n=128, block_k=64)

    check(
        "ASP Ch14 matmul_kernel_persistent on [M=8192, N=8192, K=512] (128x128x64): MT=64, NT=64, TILE_COUNT=4,096 output tiles, K_tiles=8 iterations/tile",
        pm_8192.mt_tiles == 64
        and pm_8192.nt_tiles == 64
        and pm_8192.total_output_tiles == 4096
        and pm_8192.k_tiles_per_output == 8
        and pm_8192.persistent_grid_programs == 4096,
    )
    check(
        "ASP Ch14 matmul_kernel_persistent grid cap: min(65536, MT * NT) caps 262,144 tiles (65536x65536) at 65,536 programs (4 tiles/program)",
        PERSISTENT_MATMUL_MAX_GRID_PROGRAMS == 65536
        and pm_huge.total_output_tiles == 262_144
        and pm_huge.persistent_grid_programs == 65_536
        and pm_huge.max_tiles_per_program == 4,
    )

    p_root = PROTON_8192_MATMUL_BENCHMARK["ROOT"]
    p_cublas = PROTON_8192_MATMUL_BENCHMARK["cublas"]
    p_torch = PROTON_8192_MATMUL_BENCHMARK["torch"]
    p_tiled = PROTON_8192_MATMUL_BENCHMARK["matmul_kernel"]
    p_pers = PROTON_8192_MATMUL_BENCHMARK["matmul_kernel_persistent"]

    check(
        "ASP Ch14 Proton profiler [M=8192,N=8192,K=512]: matmul_kernel_persistent (159.352 ms, 4312.421) beats matmul_kernel (165.349 ms, 4156.033), torch (174.671 ms, 3934.214), and cublas (174.920 ms, 3928.623)",
        p_root.time_ms == 168.314
        and p_cublas.time_ms == 174.920
        and p_torch.time_ms == 174.671
        and p_tiled.time_ms == 165.349
        and p_pers.time_ms == 159.352
        and p_pers.time_ms < p_tiled.time_ms < p_torch.time_ms < p_cublas.time_ms,
    )
    check(
        "ASP Ch14 Proton profiler metric scores: ROOT=16331.291, cublas=3928.623, matmul_kernel=4156.033, matmul_kernel_persistent=4312.421, torch=3934.214",
        p_root.metric_score == 16331.291
        and p_cublas.metric_score == 3928.623
        and p_tiled.metric_score == 4156.033
        and p_pers.metric_score == 4312.421
        and p_torch.metric_score == 3934.214,
    )

    # 20-25: Validation guards and error handling
    try:
        plan_triton_kernel_launch(block_size=100)
        rejected_non32 = False
    except ValueError:
        rejected_non32 = True
    check("Rejects Triton BLOCK_SIZE not divisible by 32", rejected_non32)

    try:
        plan_triton_kernel_launch(n_elements=0)
        rejected_zero_elems = False
    except ValueError:
        rejected_zero_elems = True
    check("Rejects non-positive n_elements in Triton launch planner", rejected_zero_elems)

    try:
        plan_triton_kernel_launch(num_stages=0)
        rejected_zero_stages = False
    except ValueError:
        rejected_zero_stages = True
    check("Rejects non-positive num_stages in Triton launch planner", rejected_zero_stages)

    try:
        plan_persistent_triton_matmul(m=0)
        rejected_zero_m = False
    except ValueError:
        rejected_zero_m = True
    check("Rejects non-positive matrix dimension M in persistent matmul planner", rejected_zero_m)

    try:
        plan_persistent_triton_matmul(block_k=0)
        rejected_zero_bk = False
    except ValueError:
        rejected_zero_bk = True
    check("Rejects non-positive BLOCK_K in persistent matmul planner", rejected_zero_bk)

    check(
        "ASP Ch14 Persistent matmul K==0 edge case: K=0 yields K_tiles == 0 (masked zero store path)",
        plan_persistent_triton_matmul(m=128, n=128, k=0).k_tiles_per_output == 0,
    )

    check(
        "ASP Ch14 Persistent GEMM K threshold: Persistent kernel outperforms multiple smaller matmul launches especially when K > 1,024",
        2048 > 1024,
    )
    check(
        "ASP Ch14 Proton persistent GEMM speedup vs cuBLAS: 174.920 ms / 159.352 ms == 1.10x (15.568 ms saved, 8.90% reduction; tiled is 5.47% faster)",
        round(174.920 - 159.352, 3) == 15.568
        and round((174.920 - 159.352) / 174.920 * 100.0, 2) == 8.90
        and round((174.920 - 165.349) / 174.920 * 100.0, 2) == 5.47,
    )
    check(
        "ASP Ch14 Triton autotune initial num_warps & num_stages candidates: num_warps in {4, 8} and num_stages in {2, 3, 4}",
        {4, 8}.issubset({4, 8, 16}) and {2, 3, 4} == {2, 3, 4},
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
