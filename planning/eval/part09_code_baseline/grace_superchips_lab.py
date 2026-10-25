#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.4: Grace CPU, GH200 and GB200 superchips."""

from __future__ import annotations

import sys

from grace_superchips import (
    SUPERCHIP_CATALOG,
    audit_superchip_runtime_config,
    compare_c2c_vs_pcie_gen5,
    estimate_host_to_gpu_transfer_seconds,
    evaluate_superchip_memory_placement,
)


def run_checks() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label} -- {detail}")

    print("=== Chapter 9.4 Lab: Grace CPU, GH200, GB200 & GB300 Superchips ===")

    # 1. NVLink-C2C vs PCIe Gen5 x16 physics checks (V4 Ch 7)
    c2c = compare_c2c_vs_pcie_gen5()
    check(
        "PCIe Gen5 x16 is 64 GB/s unidirectional and 128 GB/s bidirectional",
        c2c["pcie_gen5_unidirectional_gbps"] == 64.0
        and c2c["pcie_gen5_bidirectional_gbps"] == 128.0,
    )
    check(
        "NVLink-C2C is 450 GB/s unidirectional and 900 GB/s bidirectional (7.03x PCIe Gen5)",
        c2c["nvlink_c2c_unidirectional_gbps"] == 450.0
        and c2c["nvlink_c2c_bidirectional_gbps"] == 900.0
        and c2c["bandwidth_multiplier"] == 7.03,
        f"got {c2c}",
    )

    # 2. Superchip catalog checks (V4 Ch 7, ASP Ch 2, superpod-gb300-ra)
    grace_cpu = SUPERCHIP_CATALOG["Grace-CPU-Superchip"]
    check(
        "Grace CPU Superchip bonds 2x 72-core Arm Neoverse V2 CPUs (144 cores) + up to 960 GB LPDDR5X at ~1 TB/s",
        grace_cpu.cpu_count == 2
        and grace_cpu.total_arm_cores == 144
        and grace_cpu.lpddr_capacity_gb == 960
        and grace_cpu.lpddr_bw_gbps == 1000.0,
    )

    gh200_96 = SUPERCHIP_CATALOG["GH200-96GB"]
    check(
        "GH200-96GB combines 72-core Grace (480 GB LPDDR5X) + H100 (96 GB HBM3) = 576 GB coherent memory",
        gh200_96.total_arm_cores == 72
        and gh200_96.lpddr_capacity_gb + gh200_96.total_hbm_gb == 576,
    )

    gh200_144 = SUPERCHIP_CATALOG["GH200-144GB"]
    check(
        "GH200-144GB HBM3e variant delivers 480 + 144 = 624 GB coherent memory",
        gh200_144.lpddr_capacity_gb + gh200_144.total_hbm_gb == 624,
    )

    gb200 = SUPERCHIP_CATALOG["GB200"]
    check(
        "GB200 combines 1x 72-core Grace + 2x B200 GPUs (384 GB HBM3e @ 16 TB/s + 480 GB LPDDR5X = 864 GB)",
        gb200.cpu_count == 1
        and gb200.gpu_count == 2
        and gb200.total_hbm_gb == 384
        and gb200.total_hbm_bw_tbps == 16.0
        and gb200.total_hbm_gb + gb200.lpddr_capacity_gb == 864,
    )

    gb300 = SUPERCHIP_CATALOG["GB300"]
    check(
        "GB300 combines 1x Grace + 2x B300 GPUs (2x 288 GB = 576 GB HBM3e + 500 GB LPDDR5X = 1,076 GB)",
        gb300.gpu_count == 2
        and gb300.total_hbm_gb == 576
        and gb300.total_hbm_gb + gb300.lpddr_capacity_gb == 1076,
    )

    # 3. Unified memory placement & V4 Ch 7 1.2 TB GNN Customer Scenario checks
    gnn_2x_gh200_144 = evaluate_superchip_memory_placement(
        superchip_name="GH200-144GB",
        num_superchips=2,
        hot_working_set_gb=240.0,  # Active GNN weights & mini-batch activations in HBM3e (288 GB available)
        cold_overflow_gb=960.0,    # 960 GB graph node feature tables in LPDDR5X (1,200 GB total = 1.2 TB)
    )
    check(
        "V4 Ch7 Customer Scenario: 1.2 TB GNN (240 GB hot + 960 GB graph features) fits in 2x GH200-144GB (1,248 GB pool)",
        gnn_2x_gh200_144["total_coherent_memory_gb"] == 1248
        and gnn_2x_gh200_144["hot_fits_entirely_in_hbm"] is True
        and gnn_2x_gh200_144["fits_in_coherent_pool"] is True,
        f"got {gnn_2x_gh200_144}",
    )

    gb300_tray = evaluate_superchip_memory_placement(
        superchip_name="GB300",
        num_superchips=2,  # 1 compute tray in DGX GB300 NVL72 has 2x GB300 Superchips
        hot_working_set_gb=1100.0,
        cold_overflow_gb=900.0,
    )
    check(
        "Single DGX GB300 compute tray (2x GB300 Superchips) holds 1,152 GB HBM3e + 1,000 GB LPDDR5X = 2,152 GB",
        gb300_tray["total_hbm_gb"] == 1152
        and gb300_tray["total_lpddr_gb"] == 1000
        and gb300_tray["total_coherent_memory_gb"] == 2152
        and gb300_tray["fits_in_coherent_pool"] is True,
        f"got {gb300_tray}",
    )

    spill_case = evaluate_superchip_memory_placement(
        superchip_name="GB200",
        num_superchips=1,
        hot_working_set_gb=450.0,  # Exceeds 384 GB HBM3e by 66 GB -> spills 66 GB to LPDDR5X
        cold_overflow_gb=300.0,
    )
    check(
        "Detects 66 GB HBM spill into Grace LPDDR5X when hot working set (450 GB) > 384 GB HBM3e",
        spill_case["hot_fits_entirely_in_hbm"] is False
        and spill_case["hbm_spill_to_lpddr_gb"] == 66.0
        and spill_case["used_lpddr_gb"] == 366.0
        and spill_case["fits_in_coherent_pool"] is True,
        f"got {spill_case}",
    )

    oom_case = evaluate_superchip_memory_placement(
        superchip_name="GH200-96GB",
        num_superchips=1,
        hot_working_set_gb=200.0,
        cold_overflow_gb=500.0,  # 700 GB > 576 GB total coherent memory
    )
    check(
        "Detects coherent pool overflow when workload (700 GB) exceeds GH200-96GB capacity (576 GB)",
        oom_case["fits_in_coherent_pool"] is False,
        f"got {oom_case}",
    )

    try:
        evaluate_superchip_memory_placement("GB200", 0, 100.0, 100.0)
        check("Rejects num_superchips <= 0", False)
    except ValueError:
        check("Rejects num_superchips <= 0", True)

    # 4. Superchip OS, Coherence, and SuperOffload Runtime Audit checks (ASP Ch 2, 3, 13)
    good_cfg = {
        "assumes_gpu_to_gpu_hardware_cache_coherence": False,
        "cpu_threads_bound_to_local_grace_numa": True,
        "uses_unified_memory_without_pinning": True,
        "large_pages_enabled": True,
        "workload_type": "training",
        "thp_mode": "always",
        "hot_activations_placed_in_lpddr": False,
        "uses_x86_avx_intrinsics": False,
    }
    res_good = audit_superchip_runtime_config(good_cfg)
    check(
        "Properly tuned Grace Blackwell training config passes all runtime checks",
        res_good["valid_configuration"] is True and len(res_good["issues"]) == 0,
        f"got {res_good}",
    )

    bad_coherence = dict(good_cfg, assumes_gpu_to_gpu_hardware_cache_coherence=True)
    check(
        "ASP Ch2 chunk 7: Flags assuming hardware cache coherence across GPU-to-GPU NVLink (only CPU-GPU C2C is coherent)",
        any("invalid_coherence_assumption" in i for i in audit_superchip_runtime_config(bad_coherence)["issues"]),
    )

    bad_numa = dict(good_cfg, cpu_threads_bound_to_local_grace_numa=False)
    check(
        "ASP Ch3: Flags unbound CPU threads on dual-Superchip compute trays",
        any("unbound_cpu_threads" in i for i in audit_superchip_runtime_config(bad_numa)["issues"]),
    )

    bad_pages = dict(good_cfg, uses_unified_memory_without_pinning=True, large_pages_enabled=False)
    check(
        "ASP Ch13: Flags using unified CPU-GPU memory without enabling large pages",
        any("unified_memory_missing_large_pages" in i for i in audit_superchip_runtime_config(bad_pages)["issues"]),
    )

    bad_thp_inf = dict(good_cfg, workload_type="low_latency_inference", thp_mode="always")
    check(
        "ASP Ch3: Flags THP=always on latency-sensitive LLM inference (background compaction pauses)",
        any("thp_always_on_inference" in i for i in audit_superchip_runtime_config(bad_thp_inf)["issues"]),
    )

    good_thp_inf = dict(good_cfg, workload_type="low_latency_inference", thp_mode="madvise")
    check(
        "ASP Ch3: THP=madvise passes for low-latency LLM inference on Grace Superchips",
        audit_superchip_runtime_config(good_thp_inf)["valid_configuration"] is True,
    )

    bad_hot_lpddr = dict(good_cfg, hot_activations_placed_in_lpddr=True)
    check(
        "ASP Ch13: Flags placing hot activations/KV-cache in 500 GB/s LPDDR5X instead of 8 TB/s HBM3e",
        any("misplaced_hot_tensors" in i for i in audit_superchip_runtime_config(bad_hot_lpddr)["issues"]),
    )

    bad_avx = dict(good_cfg, uses_x86_avx_intrinsics=True)
    check(
        "ASP Ch13: Flags x86 AVX intrinsics on Grace Arm A64 SVE (32 vector + 16 predicate registers)",
        any("incompatible_x86_simd_on_grace" in i for i in audit_superchip_runtime_config(bad_avx)["issues"]),
    )

    # 5. Additional numerical verification checks across Superchip generations
    check(
        "NVLink-C2C energy efficiency is <= 5.0 pJ/bit across all Grace Superchips",
        all(s.c2c_pj_per_bit <= 5.0 for s in SUPERCHIP_CATALOG.values()),
    )
    check(
        "GB300 HBM3e capacity (576 GB) is 1.5x GB200 HBM3e capacity (384 GB)",
        round(gb300.total_hbm_gb / gb200.total_hbm_gb, 2) == 1.5,
    )
    check(
        "36x GB200 Superchips in an NVL72 rack provide 36 * 72 == 2,592 Arm Neoverse V2 CPU cores",
        36 * gb200.total_arm_cores == 2592,
    )
    check(
        "36x GB300 Superchips in an NVL72 rack provide 36 * 576 GB == 20,736 GB (~20.7 TB) HBM3e",
        36 * gb300.total_hbm_gb == 20736,
    )
    check(
        "36x GB300 Superchips in an NVL72 rack provide 36 * 500 GB == 18,000 GB (18 TB) LPDDR5X",
        36 * gb300.lpddr_capacity_gb == 18000,
    )

    t_pcie = estimate_host_to_gpu_transfer_seconds(1200.0, "pcie_gen5_x16")
    t_c2c = estimate_host_to_gpu_transfer_seconds(1200.0, "nvlink_c2c")
    check(
        "1.2 TB (1,200 GB) host-to-GPU pass takes 18.75 s over PCIe Gen5 x16 vs 2.67 s over NVLink-C2C",
        t_pcie == 18.75 and t_c2c == 2.67,
        f"got pcie={t_pcie}, c2c={t_c2c}",
    )

    try:
        evaluate_superchip_memory_placement("UnknownChip", 1, 10.0, 10.0)
        check("Rejects unknown superchip SKU", False)
    except KeyError:
        check("Rejects unknown superchip SKU", True)

    try:
        estimate_host_to_gpu_transfer_seconds(-5.0, "nvlink_c2c")
        check("Rejects negative payload in transfer time estimator", False)
    except ValueError:
        check("Rejects negative payload in transfer time estimator", True)

    try:
        estimate_host_to_gpu_transfer_seconds(100.0, "usb2")
        check("Rejects unsupported link_type in transfer time estimator", False)
    except ValueError:
        check("Rejects unsupported link_type in transfer time estimator", True)

    check(
        "Unidirectional NVLink-C2C (450 GB/s) is 7.03x unidirectional PCIe Gen5 x16 (64 GB/s)",
        c2c["unidirectional_multiplier"] == 7.03,
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
