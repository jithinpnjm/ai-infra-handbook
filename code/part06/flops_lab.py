#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.1: What a supercomputer is: TOP500, Linpack, HPC versus AI factory."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flops import (
    filter_nodes_missing_ram,
    gpu_cluster_peak_pflops,
    hpl_efficiency,
    rpeak_cpu,
    vector_pipeline_cycles,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Section 1: Vector pipeline cycle formula K*(N-1)+S (SCL Ch. 2, S=5 stages, K=1 cycle/stage)
    check(
        "vector_pipeline_cycles computes K*(N-1)+S = 1*(100-1)+5 = 104 cycles vs 500 unpipelined cycles",
        vector_pipeline_cycles(num_elements=100, slowest_stage_cycles=1, total_pipeline_cycles=5) == 104
        and vector_pipeline_cycles(num_elements=1, slowest_stage_cycles=1, total_pipeline_cycles=5) == 5,
    )

    # 2. Section 2: CPU & GPU Rpeak, HPL efficiency, and BF16 MFU calculations
    cpu_gflops = rpeak_cpu(nodes=100, sockets=2, cores=64, ghz=2.4, flops_per_cycle=32)
    cpu_no_avx512 = rpeak_cpu(nodes=100, sockets=2, cores=64, ghz=2.4, flops_per_cycle=16)
    gpu_fp64_pf = gpu_cluster_peak_pflops(nodes=100, gpus_per_node=8, tflops_per_gpu=60)
    gpu_bf16_pf = gpu_cluster_peak_pflops(nodes=100, gpus_per_node=8, tflops_per_gpu=1000)
    eff = hpl_efficiency(38.0, gpu_fp64_pf)
    check(
        "rpeak_cpu (983.04 TF vs 491.52 TF), gpu_cluster_peak_pflops (48.0 PF FP64, 800 PF BF16), and hpl_efficiency (79.17%)",
        abs(cpu_gflops / 1000.0 - 983.04) < 1e-6
        and abs(cpu_no_avx512 / 1000.0 - 491.52) < 1e-6
        and abs(gpu_fp64_pf - 48.0) < 1e-6
        and abs(gpu_bf16_pf - 800.0) < 1e-6
        and round(eff * 100) == 79,
    )

    # 3. Section 6: Parallel shell RAM check (SCL Ch. 1, grep MemTotal /proc/meminfo | awk '{print $2}')
    sample_meminfo = {
        "node001": 528482304,
        "node002": 528482304,
        "node003": 494927872,  # Lost a 32 GB DIMM on boot!
        "node004": 264241152,  # Half memory missing!
    }
    bad_nodes = filter_nodes_missing_ram(sample_meminfo, expected_kb=528482304, tolerance_fraction=0.02)
    check(
        "filter_nodes_missing_ram flags node003 and node004 whose detected MemTotal falls below tolerance",
        bad_nodes == ["node003", "node004"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
