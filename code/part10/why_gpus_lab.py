#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.1: Why GPUs — CPU versus GPU and throughput design."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from why_gpus import (
    PCIE_SPECS,
    PRECISION_BYTES,
    SILICON_BUDGET_PCT,
    TERMINOLOGY_MAP,
    ThroughputDesignError,
    calc_dense_training_flops,
    calc_energy_kwh,
    calc_goodput_efficiency,
    calc_job_suite_turnaround,
    calc_pcie_bandwidth_gbps,
    calc_peak_memory_bandwidth_gbps,
    calc_peak_tflops,
    calc_warp_lane_efficiency,
    calc_weight_memory_gb,
    compare_scalar_vs_tensor_core_4x4,
    diagnose_host_and_request_stage,
    evaluate_deepseek_v3_moe,
    size_100t_weight_cluster,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main() -> int:
    print("=== Chapter 10.1 Lab: Why GPUs — CPU vs GPU & Throughput Design ===")

    # 1. Silicon area allocation (nvidia-devops V1 Ch 2)
    check(
        "V1 Ch2: CPU silicon budget sums to 100% (35% control, 45% cache, 20% ALUs)",
        sum(SILICON_BUDGET_PCT["CPU"].values()) == 100
        and SILICON_BUDGET_PCT["CPU"]["compute_alus"] == 20,
    )
    check(
        "V1 Ch2: GPU silicon budget sums to 100% (80% ALUs, 15% registers/L1, 5% control)",
        sum(SILICON_BUDGET_PCT["GPU"].values()) == 100
        and SILICON_BUDGET_PCT["GPU"]["compute_alus"] == 80,
    )

    # 2. Cross-vendor terminology mapping (PHPC Ch 9 Tables 9.1 & 9.2)
    check(
        "PHPC Ch9 Table 9.1: OpenCL Compute unit (CU) maps to NVIDIA Streaming multiprocessor (SM)",
        TERMINOLOGY_MAP["multiprocessor"]["nvidia"] == "Streaming multiprocessor (SM)"
        and TERMINOLOGY_MAP["multiprocessor"]["intel"] == "Subslice",
    )
    check(
        "PHPC Ch9 Table 9.1: OpenCL Processing element (PE) maps to NVIDIA CUDA core and SIMT Warp (32)",
        TERMINOLOGY_MAP["processing_core"]["nvidia"] == "CUDA core (Compute core)"
        and TERMINOLOGY_MAP["simd_group"]["nvidia"] == "SIMT Warp (32)",
    )

    # 3. Peak theoretical scalar/vector FLOPs worked examples (PHPC Ch 9 §9.2.4 p. 291)
    check(
        "PHPC Ch9 §9.2.4: V100 peak FP32 (80 SMs, 64 cores/SM, 1530 MHz, FMA=2) == 15.67 TFLOPS (15.6 truncated in book)",
        calc_peak_tflops(1530, 80, 64, 2) == 15.67
        and int(calc_peak_tflops(1530, 80, 64, 2) * 10) / 10.0 == 15.6,
    )
    check(
        "PHPC Ch9 §9.2.4: V100 peak FP64 (80 SMs, 32 cores/SM, 1530 MHz, FMA=2) == 7.83 TFLOPS (7.8 in book, 1:2 ratio)",
        round(calc_peak_tflops(1530, 80, 32, 2), 1) == 7.8,
    )
    check(
        "PHPC Ch9 §9.2.4: A100 peak FP32 (108 SMs, 64 cores/SM, 1410 MHz) == 19.49 TFLOPS (19.5 rounded) & FP64 == 9.75 TFLOPS (9.7 truncated)",
        calc_peak_tflops(1410, 108, 64, 2) == 19.49
        and calc_peak_tflops(1410, 108, 32, 2) == 9.75,
    )
    check(
        "PHPC Ch9 §9.2.4: AMD Vega 20 MI50 (60 CUs, 1746 MHz) == 13.4 TFLOPS FP32 & 6.7 TFLOPS FP64",
        round(calc_peak_tflops(1746, 60, 64, 2), 1) == 13.4
        and round(calc_peak_tflops(1746, 60, 32, 2), 1) == 6.7,
    )
    check(
        "PHPC Ch9 §9.2.4: AMD Arcturus MI100 (120 CUs, 1502 MHz) == 23.1 TFLOPS FP32 & 11.5 TFLOPS FP64",
        round(calc_peak_tflops(1502, 120, 64, 2), 1) == 23.1
        and round(calc_peak_tflops(1502, 120, 32, 2), 1) == 11.5,
    )
    check(
        "PHPC Ch9 §9.2.4: Intel Ice Lake Gen11 integrated GPU (8 CUs, 64 EUs, 1000 MHz) == 1.0 TFLOPS FP32",
        round(calc_peak_tflops(1000, 8, 64, 2), 1) == 1.0,
    )

    # 4. Peak theoretical memory bandwidth worked examples (PHPC Ch 9 §9.3.1 p. 294)
    check(
        "PHPC Ch9 §9.3.1: V100 HBM2 (0.876 GHz, 4096-bit bus, DDR multiplier 2) == 897.0 GB/s",
        calc_peak_memory_bandwidth_gbps(0.876, 4096, 2) == 897.0,
    )
    check(
        "PHPC Ch9 §9.3.1: AMD MI50 HBM2 (1.000 GHz, 4096-bit bus, DDR multiplier 2) == 1024.0 GB/s",
        calc_peak_memory_bandwidth_gbps(1.000, 4096, 2) == 1024.0,
    )
    check(
        "PHPC Ch9 Table 9.4: GDDR6 (2.0 GHz, 384-bit bus, multiplier 8) == 768.0 GB/s",
        calc_peak_memory_bandwidth_gbps(2.0, 384, 8) == 768.0,
    )

    # 5. PCIe Gen1-Gen6 theoretical bandwidth (PHPC Ch 9 §9.4.1 Table 9.5 p. 299)
    check(
        "PHPC Ch9 Table 9.5: PCIe Gen1 x16 (2.5 GT/s, 80% factor) == 4.0 GB/s and Gen2 x16 == 8.0 GB/s",
        calc_pcie_bandwidth_gbps(1, 16) == 4.0
        and calc_pcie_bandwidth_gbps(2, 16) == 8.0,
    )
    check(
        "PHPC Ch9 Table 9.5: PCIe Gen3 x16 (8.0 GT/s, 98.46% factor) == 15.75 GB/s",
        calc_pcie_bandwidth_gbps(3, 16) == 15.75,
    )
    check(
        "PHPC Ch9 Table 9.5: PCIe Gen4 x16 == 31.51 GB/s, Gen5 x16 == 63.01 GB/s, Gen6 x16 == 126.03 GB/s",
        round(calc_pcie_bandwidth_gbps(4, 16), 1) == 31.5
        and round(calc_pcie_bandwidth_gbps(5, 16), 0) == 63.0
        and round(calc_pcie_bandwidth_gbps(6, 16), 0) == 126.0
        and PCIE_SPECS[5].encoding_overhead_pct == 1.54,
    )

    # 6. SIMT warp lane alignment & Tensor Core 4x4 math (V1 Ch 3)
    w31 = calc_warp_lane_efficiency(31, 32)
    w32 = calc_warp_lane_efficiency(32, 32)
    check(
        "V1 Ch3: Batch size 31 allocates 32 warp lanes (1 wasted lane, 96.88% efficiency) vs 32 (100%)",
        w31["total_lanes"] == 32
        and w31["wasted_lanes"] == 1
        and w31["efficiency_pct"] == 96.88
        and w32["wasted_lanes"] == 0
        and w32["efficiency_pct"] == 100.0,
    )
    tc = compare_scalar_vs_tensor_core_4x4()
    check(
        "V1 Ch3: 4x4 matrix multiply-accumulate requires 64 scalar CUDA MAC ops vs 1 Tensor Core op",
        tc["scalar_mac_ops"] == 64 and tc["tensor_core_ops"] == 1 and tc["operation_reduction_factor"] == 64,
    )

    # 7. Precision byte cascade & weight footprint (V2 Ch 1, V1 Ch 1, ASP Ch 1)
    check(
        "V2 Ch1: Precision byte cascade FP64 (8B) -> FP32 (4B) -> FP16/BF16 (2B) -> FP8 (1B) -> FP4 (0.5B)",
        PRECISION_BYTES["FP64"] == 8.0
        and PRECISION_BYTES["FP32"] == 4.0
        and PRECISION_BYTES["BF16"] == 2.0
        and PRECISION_BYTES["FP8"] == 1.0
        and PRECISION_BYTES["FP4"] == 0.5,
    )
    check(
        "V1 Ch1 & ASP Ch1: 70B FP16 weights == 140.0 GB; 8B FP16 weights == 16.0 GB (leaving 8 GB on 24 GB GPU)",
        calc_weight_memory_gb(70.0, "FP16") == 140.0
        and calc_weight_memory_gb(8.0, "FP16") == 16.0,
    )

    # 8. Goodput worked examples (ASP Ch 1 pp. 13-14)
    gp1 = calc_goodput_efficiency(100_000, 10.0, 8, 1_500.0)
    check(
        "ASP Ch1 p.13: 8 GPUs processing 100k tokens in 10s == 10,000 tok/s goodput (83.3% of 12,000 peak)",
        gp1["achieved_goodput_per_sec"] == 10_000.0
        and gp1["speed_of_light_per_sec"] == 12_000.0
        and gp1["efficiency_pct"] == 83.3,
    )
    gp2 = calc_goodput_efficiency(300.0, 1.0, 1, 1_000.0)
    check(
        "ASP Ch1 p.14: 300 samples/s achieved out of 1,000 samples/s ideal == 30.0% goodput (70.0% wasted)",
        gp2["efficiency_pct"] == 30.0 and gp2["wasted_pct"] == 70.0,
    )

    # 9. 100-Trillion-Parameter dense compute & memory sizing (ASP Ch 1 pp. 6-7)
    flops_100t = calc_dense_training_flops(1e14, 2.9e13)
    check(
        "ASP Ch1 p.6: Dense 100T model on 29T tokens requires C = 6*N*D == 1.74e28 FLOPs",
        abs(flops_100t - 1.74e28) / 1.74e28 < 1e-9,
    )
    b200_100t = size_100t_weight_cluster(100.0, 2.0, 180.0, 8)
    b300_100t = size_100t_weight_cluster(100.0, 2.0, 288.0, 8)
    check(
        "ASP Ch1 p.7: 100T FP16 weights == 200 TB (~1,112 B200 GPUs @ 180 GB; 695 B300 GPUs @ 288 GB / 87 nodes)",
        b200_100t["total_weight_tb"] == 200
        and b200_100t["min_gpus_exact_ceil"] == 1112
        and b300_100t["min_gpus_exact_ceil"] == 695
        and b300_100t["min_nodes_exact_ceil"] == 87,
    )

    # 10. DeepSeek-V3 MoE & H800 vs H100 constraints (ASP Ch 1 pp. 4-7)
    ds = evaluate_deepseek_v3_moe()
    check(
        "ASP Ch1 pp.4-7: DeepSeek-V3 activates 9 experts (1 shared + 8 of 256 routed) = 37B of 680B params (5.44%) on 400 GB/s H800",
        ds["active_experts_per_token"] == 9
        and ds["active_param_fraction_pct"] == 5.44
        and ds["h800_nvlink_gbps"] == 400.0
        and ds["h100_nvlink_gbps"] == 900.0,
    )

    # 11. Energy & 100-job suite turnaround worked examples (PHPC Ch 9 §9.6.2 pp. 306-309)
    cpu_kwh = calc_energy_kwh(45, 140.0, 24.0)
    gpu_kwh = calc_energy_kwh(12, 300.0, 24.0)
    check(
        "PHPC Ch9 Table 9.6: 10 TB/s system energy for 24h is 151.2 kWh (45x 140W CPUs) vs 86.4 kWh (12x 300W V100s)",
        cpu_kwh == 151.2 and gpu_kwh == 86.4 and round((1.0 - gpu_kwh / cpu_kwh) * 100.0, 1) == 42.9,
    )
    suite = calc_job_suite_turnaround(100, 200, 20, 10.0, 40, 0.80)
    check(
        "PHPC Ch9 p.309: 100-job suite on 200 procs takes 100h at 20 procs/job vs 125h at 40 procs/job (80% efficiency -> 6.25h/job)",
        suite["speedup"] == 1.6
        and suite["scaled_hours_per_job"] == 6.25
        and suite["base_suite_hours"] == 100.0
        and suite["scaled_suite_hours"] == 125.0,
    )

    # 12. Host inspection (V1 Lab 01) & staged request path (V1 Lab 02)
    h_missing = diagnose_host_and_request_stage(False, False, False)
    h_no_tool = diagnose_host_and_request_stage(True, False, False)
    h_drv_err = diagnose_host_and_request_stage(True, True, False)
    h_healthy = diagnose_host_and_request_stage(True, True, True, 20.0, 80.0, 1.0)
    h_broken = diagnose_host_and_request_stage(True, True, True, 500.0, 80.0, 1.0)
    check(
        "V1 Lab 01: Distinguishes missing PCIe GPU, missing nvidia-smi binary, and broken driver communication",
        h_missing["host_state"] == "NO_PCI_GPU_VISIBLE"
        and h_no_tool["host_state"] == "GPU_VISIBLE_TOOLING_MISSING"
        and h_drv_err["host_state"] == "DRIVER_COMMUNICATION_FAILED"
        and h_healthy["host_state"] == "HOST_GPU_READY",
    )
    check(
        "V1 Lab 02: Healthy request (20ms prep, 80ms exec) is execution-dominated (~101ms); injected 500ms prep delay is CPU-bottlenecked (~581ms)",
        h_healthy["dominant_stage"] == "MODEL_EXECUTION_STAGE"
        and h_healthy["total_ms"] == 101.0
        and h_broken["dominant_stage"] == "CPU_PREPROCESSING_BOTTLENECK"
        and h_broken["total_ms"] == 581.0
        and h_broken["preprocess_share_pct"] == 86.1,
    )

    # 13. Negative / boundary checks
    raised = False
    try:
        calc_pcie_bandwidth_gbps(7, 16)
    except ThroughputDesignError:
        raised = True
    check("Rejects unsupported PCIe generation", raised)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
