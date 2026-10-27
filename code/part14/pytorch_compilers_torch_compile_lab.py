#!/usr/bin/env python3
"""Chapter 14.9 Verification Lab: PyTorch compilers and kernels: torch.compile.

Run with:
    python3 -B code/part14/pytorch_compilers_torch_compile_lab.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pytorch_compilers_torch_compile import (
    BLACKWELL_TMEM_CAPACITY_KB_PER_SM,
    COMPILE_PIPELINE_STAGES,
    COMPILER_MODES,
    COMPILER_STANCES,
    DEFAULT_ACCUMULATED_RECOMPILE_LIMIT,
    DEFAULT_RECOMPILE_LIMIT,
    DYNAMIC_GUARD_EXPANDED_SEQ_LEN,
    DYNAMIC_GUARD_INITIAL_SEQ_LEN,
    DYNAMIC_PADDING_VARIATION_PCT_RANGE,
    FLEX_ATTENTION_SPEED_PCT_RANGE,
    PEP_FRAME_EVALUATION_NUMBER,
    PERSISTENT_MATMUL_K_THRESHOLD,
    PERSISTENT_MATMUL_MAX_GRID_SIZE,
    PRIMTORCH_PRIMS_OPS_COUNT,
    PRIMTORCH_REDUCTION_PCT,
    PRIMTORCH_REDUCTION_RATIO,
    PYTORCH_ATEN_OPS_COUNT,
    TABLE_14_1_TORCH_LOGS,
    TMA_LEADING_STRIDE_ALIGNMENT_BYTES,
    analyze_dynamo_explain,
    build_triton_custom_op_spec,
    evaluate_aot_autograd_fusion_savings,
    evaluate_proton_matmul_benchmark,
    plan_persistent_matmul_grid,
    select_torch_logs_flag,
    simulate_guard_recompilations,
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

    print("=== Chapter 14.9 Lab: PyTorch Compilers and Kernels: torch.compile (ASP Ch 14) ===")

    # 1-5: 4-Stage `torch.compile` Pipeline, PrimTorch Reduction, Modes, and Stances
    check(
        "1. 4-stage torch.compile pipeline order: TorchDynamo (PEP 523) -> AOTAutograd -> PrimTorch -> TorchInductor",
        COMPILE_PIPELINE_STAGES == ("TorchDynamo", "AOTAutograd", "PrimTorch", "TorchInductor")
        and PEP_FRAME_EVALUATION_NUMBER == 523,
    )
    check(
        "2. PrimTorch IR operator reduction: decomposes >2,000 ATen ops to ~250 primitive ops (8.0x / 87.5% reduction)",
        PYTORCH_ATEN_OPS_COUNT == 2000
        and PRIMTORCH_PRIMS_OPS_COUNT == 250
        and PYTORCH_ATEN_OPS_COUNT / PRIMTORCH_PRIMS_OPS_COUNT == PRIMTORCH_REDUCTION_RATIO == 8.0
        and PRIMTORCH_REDUCTION_PCT == 87.5,
    )
    check(
        "3. Compilation modes: default, reduce-overhead, max-autotune, max-autotune-no-cudagraphs with exact CUDA Graph & autotune rules",
        set(COMPILER_MODES.keys()) == {"default", "reduce-overhead", "max-autotune", "max-autotune-no-cudagraphs"}
        and COMPILER_MODES["default"]["cudagraphs"] is False
        and COMPILER_MODES["reduce-overhead"]["cudagraphs"] is True
        and COMPILER_MODES["max-autotune"]["cudagraphs"] is True
        and COMPILER_MODES["max-autotune"]["autotune"] is True
        and COMPILER_MODES["max-autotune-no-cudagraphs"]["cudagraphs"] is False
        and COMPILER_MODES["max-autotune-no-cudagraphs"]["autotune"] is True,
    )
    check(
        "4. torch.compiler.set_stance supports 4 stances: default, fail_on_recompile, eager_on_recompile, force_eager",
        set(COMPILER_STANCES.keys()) == {"default", "fail_on_recompile", "eager_on_recompile", "force_eager"},
    )
    check(
        "5. FlexAttention reaches 85.0%-90.0% of FlashAttention performance in forward and backward passes",
        FLEX_ATTENTION_SPEED_PCT_RANGE == (85.0, 90.0),
    )

    # 6-7: AOTAutograd Joint Forward-Backward Fusion & Min-Cut Memory-Bandwidth Savings
    fusion = evaluate_aot_autograd_fusion_savings(
        batch_size=4,
        seq_len=2048,
        hidden_dim=4096,
        bytes_per_elem=2,
        num_elementwise_ops_fwd=5,
        num_elementwise_ops_bwd=5,
        saved_tensors_eager=4,
        saved_tensors_min_cut=1,
    )
    check(
        "6. AOTAutograd + TorchInductor kernel launch fusion: 10 eager kernels (5 fwd + 5 bwd) fuse into 2 kernels (1 fwd + 1 bwd)",
        fusion.num_tokens == 8192
        and fusion.eager_total_kernels == 10
        and fusion.compiled_total_kernels == 2,
    )
    check(
        "7. AOTAutograd min-cut partitioner HBM savings: 1.6106 GB eager (24 passes of 67.1089 MB) -> 0.4027 GB compiled (6 passes) = 4.0x (75.0% saved)",
        fusion.eager_hbm_bytes == 1_610_612_736
        and fusion.compiled_hbm_bytes == 402_653_184
        and fusion.eager_hbm_gb == 1.6106
        and fusion.compiled_hbm_gb == 0.4027
        and fusion.hbm_traffic_reduction_ratio == 4.0
        and fusion.hbm_bandwidth_saved_pct == 75.0,
    )

    # 8-12: `torch._dynamo.explain()` Graph-Break Counter, FSDP Submodules, & Recompilation Budget
    exp_toy = analyze_dynamo_explain(has_print_side_effect=True, has_data_dependent_if=True)
    exp_fixed = analyze_dynamo_explain(has_print_side_effect=False, has_data_dependent_if=False)
    exp_fsdp = analyze_dynamo_explain(has_print_side_effect=False, has_data_dependent_if=False, num_fsdp_comm_boundaries=2)

    check(
        "8. dynamo.explain(toy_example): print('woo') + 'if b.sum() < 0:' -> Graph Count=3, Graph Break Count=2, Op Count=5",
        exp_toy.graph_count == 3
        and exp_toy.graph_break_count == 2
        and exp_toy.op_count == 5
        and exp_toy.break_reasons == ("builtin: print [...ConstantVariable] False", "generic_jump TensorVariable()")
        and exp_toy.cuda_graphs_compatible is False,
    )
    check(
        "9. Refactored model_where / model_cond: if not is_compiling() + torch.where/torch.cond -> Graph Count=1, Graph Break Count=0",
        exp_fixed.graph_count == 1
        and exp_fixed.graph_break_count == 0
        and exp_fixed.cuda_graphs_compatible is True,
    )
    check(
        "10. FSDP / DDP intentional communication breaks: 2 collective boundaries yield 3 subgraphs for compute-communication overlap",
        exp_fsdp.graph_count == 3
        and exp_fsdp.graph_break_count == 2,
    )

    recomp_thrash = simulate_guard_recompilations(
        Constant_python_arg_changing=True,
        stance="default",
        recompile_limit=DEFAULT_RECOMPILE_LIMIT,
    )
    recomp_fail_ci = simulate_guard_recompilations(
        Constant_python_arg_changing=True,
        stance="fail_on_recompile",
        recompile_limit=DEFAULT_RECOMPILE_LIMIT,
    )
    recomp_auto_dyn = simulate_guard_recompilations(
        observed_seq_lengths=(256, 512, 768, 1024),
        mark_dynamic_used=False,
        dynamic_flag=False,
    )
    recomp_mark_dyn = simulate_guard_recompilations(
        observed_seq_lengths=(256, 512, 768, 1024),
        mark_dynamic_used=True,
        dynamic_flag=False,
    )
    recomp_static_cg = simulate_guard_recompilations(
        observed_seq_lengths=(512, 512, 512),
        mark_dynamic_used=False,
        dynamic_flag=False,
        mode="reduce-overhead",
    )

    check(
        "11. Guard-failure recompilation budget: changing Python scalar hits recompile_limit=8 (accumulated=64) and falls back to eager; fail_on_recompile raises on step 2",
        DEFAULT_RECOMPILE_LIMIT == 8
        and DEFAULT_ACCUMULATED_RECOMPILE_LIMIT == 64
        and recomp_thrash.compilations_triggered == 8
        and recomp_thrash.guard_failures == 8
        and recomp_thrash.hit_recompile_limit is True
        and recomp_thrash.fell_back_to_eager is True
        and recomp_fail_ci.raised_fail_on_recompile is True,
    )
    check(
        "12. Dynamic shape guards & mark_dynamic: auto-dynamic takes 2 compiles (1 recompile, sequence_length <= 256 -> 1024); mark_dynamic takes 1 compile (0 recompiles) and disables CUDA Graphs",
        DYNAMIC_GUARD_INITIAL_SEQ_LEN == 256
        and DYNAMIC_GUARD_EXPANDED_SEQ_LEN == 1024
        and DYNAMIC_PADDING_VARIATION_PCT_RANGE == (10.0, 20.0)
        and recomp_auto_dyn.compilations_triggered == 2
        and recomp_auto_dyn.guard_failures == 1
        and recomp_mark_dyn.compilations_triggered == 1
        and recomp_mark_dyn.guard_failures == 0
        and recomp_mark_dyn.cudagraphs_enabled is False
        and recomp_static_cg.cudagraphs_enabled is True,
    )

    # 13-15: Table 14-1 `TORCH_LOGS` Diagnostic Selector, Minifier Level 4, & cuBLAS Determinism
    check(
        "13. Table 14-1 TORCH_LOGS: all 11 diagnostic flags registered and mapped cleanly by symptom selector",
        len(TABLE_14_1_TORCH_LOGS) == 11
        and select_torch_logs_flag("graph_break") == "graph_breaks"
        and select_torch_logs_flag("joint_fwd_bwd_graph") == "aot_graphs"
        and select_torch_logs_flag("missed_cudagraph_or_fusion") == "perf_hints"
        and select_torch_logs_flag("generated_triton_or_cpp") == "output_code"
        and select_torch_logs_flag("guard_recompile_reason") == "recompiles"
        and select_torch_logs_flag("guard_expressions") == "guards",
    )
    check(
        "14. Numerical accuracy repro & cuBLAS workspace: TORCHDYNAMO_REPRO_LEVEL=4 and CUBLAS_WORKSPACE_CONFIG=:4096:8 (32,768 KB = 32 MB) or :16:8 (128 KB)",
        (4096 * 8 == 32_768) and (16 * 8 == 128) and (4 == 4),
    )

    # 15-19: `@torch.library.triton_op` Custom Kernel Registration, SPMD Warps, & TMA Alignment
    op_1024 = build_triton_custom_op_spec(n_elements=10_000, block_size=1024)
    op_2048 = build_triton_custom_op_spec(n_elements=10_000, block_size=2048)
    op_4096 = build_triton_custom_op_spec(n_elements=10_000, block_size=4096, warp_specialize=True)
    op_broken_bwd = build_triton_custom_op_spec(has_register_autograd=False)
    op_bad_tma = build_triton_custom_op_spec(leading_stride_bytes=12)

    check(
        "15. @triton_op registration & training autograd: wrap_triton + register_autograd(backward, setup_context=...) prevents graph breaks; missing autograd breaks training graph",
        op_1024.qualname == "my_triton_lib::vector_add"
        and op_1024.causes_dynamo_graph_break is False
        and op_broken_bwd.causes_dynamo_graph_break is True,
    )
    check(
        "16. Triton SPMD vector_add_kernel (n_elements=10,000, BLOCK_SIZE=1,024): cdiv(10000, 1024) = 10 programs, 4 warps (128 threads, 8.0 elems/thread)",
        op_1024.grid_programs == 10
        and op_1024.num_warps == 4
        and op_1024.threads_per_block == 128
        and op_1024.elements_per_thread == 8.0,
    )
    check(
        "17. Triton num_warps scaling & warp specialization: BLOCK_SIZE=2,048 -> 8 warps (256 threads); BLOCK_SIZE=4,096 -> 16 warps (512 threads), num_consumer_groups=2, num_buffers_warp_spec=3",
        op_2048.num_warps == 8
        and op_2048.threads_per_block == 256
        and op_4096.num_warps == 16
        and op_4096.threads_per_block == 512
        and op_4096.num_consumer_groups == 2
        and op_4096.num_buffers_warp_spec == 3,
    )
    check(
        "18. TMA tensor descriptor alignment & Blackwell TMEM: 16-byte leading stride + contiguous inner dim required; TMEM = 256 KB/SM",
        TMA_LEADING_STRIDE_ALIGNMENT_BYTES == 16
        and BLACKWELL_TMEM_CAPACITY_KB_PER_SM == 256
        and op_1024.tma_descriptor_valid is True
        and op_bad_tma.tma_descriptor_valid is False,
    )

    # 19-22: `matmul_kernel_persistent` and `Proton` Profiler Benchmark (`159.352 ms` vs `174.920 ms`)
    pm_8192 = plan_persistent_matmul_grid(m=8192, n=8192, k=512, block_m=128, block_n=128, block_k=64)
    pm_65536 = plan_persistent_matmul_grid(m=65536, n=65536, k=2048, block_m=128, block_n=128, block_k=64)
    proton = evaluate_proton_matmul_benchmark()

    check(
        "19. matmul_kernel_persistent on [M=8192, N=8192, K=512] (128x128x64): MT=64, NT=64, TILE_COUNT=4,096 tiles, K_tiles=8, grid=4,096",
        pm_8192.mt_tiles == 64
        and pm_8192.nt_tiles == 64
        and pm_8192.tile_count == 4096
        and pm_8192.k_tiles == 8
        and pm_8192.grid_programs == 4096
        and pm_8192.max_tiles_per_program == 1,
    )
    check(
        "20. matmul_kernel_persistent 65,536 grid cap & K > 1,024 rule: 65536x65536 has 262,144 tiles capped at 65,536 programs (4 tiles/program)",
        PERSISTENT_MATMUL_MAX_GRID_SIZE == 65536
        and PERSISTENT_MATMUL_K_THRESHOLD == 1024
        and pm_65536.tile_count == 262_144
        and pm_65536.grid_programs == 65_536
        and pm_65536.max_tiles_per_program == 4,
    )
    check(
        "21. Proton profiler [M=8192,N=8192,K=512] timings & scores: persistent 159.352 ms (4312.421) < tiled 165.349 ms (4156.033) < torch 174.671 ms (3934.214) < cublas 174.920 ms (3928.623), ROOT 168.314 ms (16331.291)",
        proton.root_ms == 168.314
        and proton.root_score == 16331.291
        and proton.cublas_ms == 174.920
        and proton.cublas_score == 3928.623
        and proton.torch_ms == 174.671
        and proton.torch_score == 3934.214
        and proton.tiled_triton_ms == 165.349
        and proton.tiled_triton_score == 4156.033
        and proton.persistent_triton_ms == 159.352
        and proton.persistent_triton_score == 4312.421,
    )
    check(
        "22. Proton speedup & single-GEMM FLOPs: persistent saves 15.568 ms (8.90% reduction, 1.10x speedup vs cuBLAS; tiled saves 5.47%); single 8192x8192x512 GEMM = 68.72 GFLOPs",
        proton.single_gemm_gflops == 68.72
        and proton.persistent_vs_cublas_saved_ms == 15.568
        and proton.persistent_vs_cublas_speedup_x == 1.10
        and proton.persistent_vs_cublas_reduction_pct == 8.90
        and proton.tiled_vs_cublas_reduction_pct == 5.47,
    )

    # 23-26: Input Validation & Edge Cases
    try:
        build_triton_custom_op_spec(qualname="invalid_name_without_namespace")
        rejected_bad_ns = False
    except ValueError:
        rejected_bad_ns = True
    check("23. Rejects @triton_op qualname missing 'namespace::op_name'", rejected_bad_ns)

    try:
        build_triton_custom_op_spec(block_size=100)
        rejected_non32 = False
    except ValueError:
        rejected_non32 = True
    check("24. Rejects Triton BLOCK_SIZE not divisible by 32", rejected_non32)

    try:
        select_torch_logs_flag("unknown_flag")
        rejected_bad_log = False
    except ValueError:
        rejected_bad_log = True
    check("25. Rejects unknown symptom in Table 14-1 TORCH_LOGS selector", rejected_bad_log)

    check(
        "26. Persistent matmul K==0 edge case: K=0 yields k_tiles == 0 (masked zero-store path) and force_eager stance runs 0 compilations",
        plan_persistent_matmul_grid(m=128, n=128, k=0).k_tiles == 0
        and simulate_guard_recompilations(stance="force_eager").compilations_triggered == 0,
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
