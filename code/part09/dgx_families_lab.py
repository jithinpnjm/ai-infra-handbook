#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.1: DGX system families and what they are for.

Runs 38 deterministic checks verifying workload VRAM estimation, KV-cache math,
the Volume 04 GPU Selection Scorecard, inference shortlist SLO/cost evaluation,
DGX rack power/cooling/airflow sizing, and the Volume 05 DGX node baseline audit.
"""

from __future__ import annotations

import sys

from dgx_families import (
    ACCELERATOR_CATALOG,
    DGX_SYSTEM_CATALOG,
    audit_dgx_node_baseline,
    estimate_kv_cache_gb,
    estimate_workload_vram_gb,
    evaluate_inference_shortlist,
    plan_dgx_rack_deployment,
    score_gpu_for_workload,
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

    print("=== Chapter 9.1 Lab: DGX System Families & Accelerator Selection ===")

    # 1. KV cache & workload VRAM checks (V4 Ch 1, Ch 2, Lab 01)
    kv_1_user = estimate_kv_cache_gb(
        num_layers=80, num_heads=128, bytes_per_element=8, seq_len=8192, concurrent_users=1
    )
    check(
        "V4 Ch1 70B 8k-context KV cache for 1 user == 1.34 GB",
        kv_1_user == 1.34,
        f"got {kv_1_user}",
    )

    kv_64_users = estimate_kv_cache_gb(
        num_layers=80, num_heads=128, bytes_per_element=8, seq_len=8192, concurrent_users=64
    )
    check(
        "V4 Ch1 70B 8k-context KV cache for 64 users == 85.90 GB",
        kv_64_users == 85.9,
        f"got {kv_64_users}",
    )

    inf_fp16 = estimate_workload_vram_gb(
        params_billions=70.0, bytes_per_param=2.0, mode="inference", kv_cache_gb=85.9
    )
    check(
        "70B FP16 weights == 140.0 GB",
        inf_fp16["weights_gb"] == 140.0,
        f"got {inf_fp16}",
    )
    check(
        "70B FP16 + 85.9 GB KV cache with 1.2x overhead == 271.08 GB",
        inf_fp16["total_with_overhead_gb"] == 271.08,
        f"got {inf_fp16}",
    )

    inf_fp8 = estimate_workload_vram_gb(
        params_billions=70.0, bytes_per_param=1.0, mode="inference", kv_cache_gb=42.95
    )
    check(
        "70B FP8 weights (70 GB) + FP8 KV cache (42.95 GB) * 1.2 == 135.54 GB",
        inf_fp8["total_with_overhead_gb"] == 135.54,
        f"got {inf_fp8}",
    )

    train_70b = estimate_workload_vram_gb(
        params_billions=70.0, bytes_per_param=2.0, mode="training", training_multiplier=5.0
    )
    check(
        "70B training VRAM at 5x rule == 700.0 GB",
        train_70b["total_with_overhead_gb"] == 700.0,
        f"got {train_70b}",
    )

    try:
        estimate_workload_vram_gb(70.0, 2.0, mode="training", training_multiplier=2.0)
        check("Rejects training multiplier < 4.0", False, "did not raise ValueError")
    except ValueError:
        check("Rejects training multiplier < 4.0", True)

    # 2. Accelerator catalog & V4 Lab 01 Scorecard checks
    check(
        "L40S has 48 GB GDDR6, 864 GB/s, 350W, no NVLink, FP8 + media engines",
        ACCELERATOR_CATALOG["L40S"].vram_gb == 48
        and ACCELERATOR_CATALOG["L40S"].nvlink_bw_gbps == 0.0
        and ACCELERATOR_CATALOG["L40S"].supports_fp8
        and ACCELERATOR_CATALOG["L40S"].media_engines,
    )
    check(
        "H100-SXM5-80GB has 3350 GB/s HBM3, 900 GB/s NVLink, 700W TDP",
        ACCELERATOR_CATALOG["H100-SXM5-80GB"].mem_bw_gbps == 3350.0
        and ACCELERATOR_CATALOG["H100-SXM5-80GB"].nvlink_bw_gbps == 900.0
        and ACCELERATOR_CATALOG["H100-SXM5-80GB"].max_tdp_w == 700,
    )
    check(
        "H200-SXM-141GB has 141 GB HBM3e and 4800 GB/s bandwidth at 700W",
        ACCELERATOR_CATALOG["H200-SXM-141GB"].vram_gb == 141
        and ACCELERATOR_CATALOG["H200-SXM-141GB"].mem_bw_gbps == 4800.0,
    )
    check(
        "B200-SXM6-180GB has 8000 GB/s HBM3e, 1800 GB/s NVLink 5, FP4 support",
        ACCELERATOR_CATALOG["B200-SXM6-180GB"].mem_bw_gbps == 8000.0
        and ACCELERATOR_CATALOG["B200-SXM6-180GB"].nvlink_bw_gbps == 1800.0
        and ACCELERATOR_CATALOG["B200-SXM6-180GB"].supports_fp4,
    )

    # V4 Lab 01 scenario: 8kW air-cooled rack ceiling, 2 nodes/rack, 150 GB VRAM needed
    h100_sxm_8kw = score_gpu_for_workload(
        gpu_name="H100-SXM5-80GB",
        gpus_per_node=8,
        required_vram_gb=150.0,
        rack_power_limit_kw=8.0,
        nodes_per_rack=1,
        host_system_overhead_w=4600,  # 8*700 + 4600 = 10.2 kW DGX H100
    )
    check(
        "V4 Lab 01: DGX H100 (10.2 kW) disqualified in an 8.0 kW rack ceiling",
        h100_sxm_8kw["disqualified"] is True
        and any("rack_power_exceeded" in d for d in h100_sxm_8kw["disqualifiers"]),
        f"got {h100_sxm_8kw}",
    )

    l40s_4gpu_8kw = score_gpu_for_workload(
        gpu_name="L40S",
        gpus_per_node=4,
        required_vram_gb=150.0,
        rack_power_limit_kw=8.0,
        nodes_per_rack=2,
        host_system_overhead_w=1000,  # 4*350 + 1000 = 2.4 kW/node -> 4.8 kW/rack
        require_nvlink=False,
        require_fp8=True,
    )
    check(
        "V4 Lab 01: 4x L40S (192 GB VRAM, 4.8 kW/rack for 2 nodes) passes 8 kW ceiling",
        l40s_4gpu_8kw["disqualified"] is False
        and l40s_4gpu_8kw["node_vram_gb"] == 192
        and l40s_4gpu_8kw["rack_power_kw"] == 4.8,
        f"got {l40s_4gpu_8kw}",
    )

    l40s_nvlink_req = score_gpu_for_workload(
        gpu_name="L40S",
        gpus_per_node=8,
        required_vram_gb=150.0,
        rack_power_limit_kw=15.0,
        nodes_per_rack=1,
        require_nvlink=True,
    )
    check(
        "V4 Lab 01: L40S disqualified when NVLink fabric is required for heavy TP/training",
        l40s_nvlink_req["disqualified"] is True
        and "missing_nvlink_fabric" in l40s_nvlink_req["disqualifiers"],
        f"got {l40s_nvlink_req}",
    )

    t4_fp8_req = score_gpu_for_workload(
        gpu_name="T4",
        gpus_per_node=8,
        required_vram_gb=100.0,
        rack_power_limit_kw=10.0,
        nodes_per_rack=1,
        require_fp8=True,
    )
    check(
        "V4 Lab 01: T4 disqualified when FP8 hardware support is required",
        t4_fp8_req["disqualified"] is True
        and "missing_fp8_support" in t4_fp8_req["disqualifiers"],
        f"got {t4_fp8_req}",
    )

    # 3. V4 Lab 02 Inference shortlist SLO and cost/1M tokens checks
    eval_l40s = evaluate_inference_shortlist(
        name="4x-L40S-PCIe",
        hourly_cost_usd=6.40,
        ttft_p99_ms=480.0,
        itl_p99_ms=34.5,  # Violates 30 ms ITL SLO at 64 users due to PCIe/GDDR6 bw
        total_tokens_per_sec=1420.0,
    )
    check(
        "V4 Lab 02: 4x L40S with 34.5 ms P99 ITL fails 30 ms decode SLO",
        eval_l40s["meets_slo"] is False and eval_l40s["meets_itl"] is False,
        f"got {eval_l40s}",
    )

    eval_h100 = evaluate_inference_shortlist(
        name="2x-H100-SXM",
        hourly_cost_usd=9.50,
        ttft_p99_ms=210.0,
        itl_p99_ms=16.2,
        total_tokens_per_sec=3200.0,
    )
    check(
        "V4 Lab 02: 2x H100 SXM passes TTFT/ITL SLOs and computes cost per 1M tokens == $0.8247",
        eval_h100["meets_slo"] is True and eval_h100["cost_per_1m_tokens_usd"] == 0.8247,
        f"got {eval_h100}",
    )

    # 4. DGX system family catalog & rack power/cooling checks (V5 Ch 2, 4, 7; SPB200; SPGB300)
    dgx_h100 = DGX_SYSTEM_CATALOG["DGX-H100"]
    check(
        "DGX H100 is 8U, 8x H100, 640 GB HBM3, 10.2 kW, 370 lbs, 4 NVSwitches",
        dgx_h100.rack_units == 8
        and dgx_h100.total_gpu_memory_gb == 640
        and dgx_h100.max_power_kw == 10.2
        and dgx_h100.nvswitch_count == 4,
    )

    dgx_h200 = DGX_SYSTEM_CATALOG["DGX-H200"]
    check(
        "DGX H200 upgrades memory to 1,128 GB HBM3e and 38.4 TB/s aggregate HBM bandwidth",
        dgx_h200.total_gpu_memory_gb == 1128 and dgx_h200.aggregate_hbm_bw_tbps == 38.4,
    )

    dgx_b200 = DGX_SYSTEM_CATALOG["DGX-B200"]
    check(
        "DGX B200 is 10U, 14.3 kW, 1,440 GB HBM3e, 64 TB/s HBM, 14.4 TB/s NVLink 5",
        dgx_b200.rack_units == 10
        and dgx_b200.max_power_kw == 14.3
        and dgx_b200.total_gpu_memory_gb == 1440
        and dgx_b200.aggregate_hbm_bw_tbps == 64.0
        and dgx_b200.aggregate_nvlink_tbps == 14.4,
    )

    dgx_gb200 = DGX_SYSTEM_CATALOG["DGX-GB200-NVL72"]
    check(
        "DGX GB200 NVL72 has 72 GPUs, 130 TB/s NVLink 5 fabric, 120 kW liquid cooling",
        dgx_gb200.gpu_count == 72
        and dgx_gb200.aggregate_nvlink_tbps == 130.0
        and dgx_gb200.cooling == "liquid",
    )

    dgx_gb300 = DGX_SYSTEM_CATALOG["DGX-GB300-NVL72"]
    check(
        "DGX GB300 NVL72 uses 800 Gbps ConnectX-8 NICs and hybrid liquid-air cooling",
        dgx_gb300.compute_nic_speed_gbps == 800
        and dgx_gb300.cooling == "hybrid-liquid-air",
    )

    plan_h100_1 = plan_dgx_rack_deployment("DGX-H100", systems_per_rack=1)
    check(
        "Single DGX H100 heat load == 34,804 BTU/hr (~34,800 BTU/hr in V5 Ch 4)",
        34800 <= plan_h100_1["heat_load_btu_hr"] <= 34810
        and plan_h100_1["requires_mechanical_lift"] is True,
        f"got {plan_h100_1}",
    )

    plan_b200_2 = plan_dgx_rack_deployment("DGX-B200", systems_per_rack=2)
    check(
        "SPB200 p.10: 2x DGX B200 per rack == 28.6 kW, 14.3 kW/circuit, 4,290 CFM",
        plan_b200_2["rack_power_kw"] == 28.6
        and plan_b200_2["per_circuit_kw_n2"] == 14.3
        and plan_b200_2["estimated_airflow_cfm"] == 4290,
        f"got {plan_b200_2}",
    )

    plan_b200_4 = plan_dgx_rack_deployment("DGX-B200", systems_per_rack=4)
    check(
        "SPB200 p.10: 4x DGX B200 per rack == 57.2 kW, 8,580 CFM, 40 RU, warns 52U rack needed",
        plan_b200_4["rack_power_kw"] == 57.2
        and plan_b200_4["estimated_airflow_cfm"] == 8580
        and plan_b200_4["total_rack_units"] == 40
        and any("52U rack" in w for w in plan_b200_4["warnings"]),
        f"got {plan_b200_4}",
    )

    plan_single_feed = plan_dgx_rack_deployment(
        "DGX-H100", systems_per_rack=2, power_feeds_available=1
    )
    check(
        "Single power feed triggers whip redundancy warning",
        any("Single power feed" in w for w in plan_single_feed["warnings"]),
        f"got {plan_single_feed}",
    )

    # 5. V5 Lab 01 & Lab 02 DGX Node Baseline Audit checks
    healthy_node = {
        "expected_gpus": 8,
        "detected_gpus": 8,
        "nvlink_links_per_gpu": 18,
        "uncorrected_ecc_errors": 0,
        "active_compute_ib_ports": 8,
        "expected_compute_ib_ports": 8,
        "raid_mounted": True,
        "sole_checkpoints_on_raid": False,
        "nvidia_peermem_loaded": True,
        "nvidia_fs_loaded": True,
        "pcie_acs_enabled": False,
        "out_of_band_individual_fw_flash": False,
    }
    res_ok = audit_dgx_node_baseline(healthy_node)
    check(
        "Healthy DGX H100 baseline passes all readiness checks",
        res_ok["ready_for_production"] is True and res_ok["failure_count"] == 0,
        f"got {res_ok}",
    )

    missing_gpu = dict(healthy_node, detected_gpus=7)
    check(
        "Detects fallen-off-the-bus GPU (7/8 detected)",
        "gpu_count_mismatch (7/8)" in audit_dgx_node_baseline(missing_gpu)["failures"],
    )

    degraded_nvlink = dict(healthy_node, nvlink_links_per_gpu=16)
    check(
        "Detects degraded NVLink sub-links (16/18 active)",
        "nvlink_degraded (16/18 active links per GPU)"
        in audit_dgx_node_baseline(degraded_nvlink)["failures"],
    )

    bad_ecc = dict(healthy_node, uncorrected_ecc_errors=2)
    check(
        "Detects uncorrected volatile ECC errors (> 0)",
        "uncorrected_ecc_errors (2)" in audit_dgx_node_baseline(bad_ecc)["failures"],
    )

    down_ib = dict(healthy_node, active_compute_ib_ports=7)
    check(
        "Detects down compute InfiniBand rail (7/8 Active)",
        "compute_fabric_links_down (7/8 Active)"
        in audit_dgx_node_baseline(down_ib)["failures"],
    )

    no_raid = dict(healthy_node, raid_mounted=False)
    check(
        "Detects unmounted /raid scratch array",
        "ephemeral_raid_not_mounted (/raid missing)"
        in audit_dgx_node_baseline(no_raid)["failures"],
    )

    unsafe_ckpt = dict(healthy_node, sole_checkpoints_on_raid=True)
    check(
        "Flags storing sole training checkpoints on ephemeral RAID 0 (/raid)",
        any("unsafe_checkpoint_storage" in f for f in audit_dgx_node_baseline(unsafe_ckpt)["failures"]),
    )

    no_peermem = dict(healthy_node, nvidia_peermem_loaded=False)
    check(
        "Flags missing nvidia-peermem module (GPUDirect RDMA disabled)",
        any("nvidia_peermem_missing" in f for f in audit_dgx_node_baseline(no_peermem)["failures"]),
    )

    no_gds = dict(healthy_node, nvidia_fs_loaded=False)
    check(
        "Flags missing nvidia-fs module (GPUDirect Storage disabled)",
        any("nvidia_fs_missing" in f for f in audit_dgx_node_baseline(no_gds)["failures"]),
    )

    acs_on = dict(healthy_node, pcie_acs_enabled=True)
    check(
        "Flags enabled PCIe ACS (SrcValid+) forcing P2P through CPU root complex",
        any("pcie_acs_enabled" in f for f in audit_dgx_node_baseline(acs_on)["failures"]),
    )

    bad_fw = dict(healthy_node, out_of_band_individual_fw_flash=True)
    check(
        "Flags ad-hoc individual firmware flashing outside the DGX Firmware Container",
        any("uncoordinated_firmware_flash" in f for f in audit_dgx_node_baseline(bad_fw)["failures"]),
    )

    try:
        estimate_kv_cache_gb(0, 128, 8, 8192, 1)
        check("Rejects non-positive KV cache parameters", False, "did not raise ValueError")
    except ValueError:
        check("Rejects non-positive KV cache parameters", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
