#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.2: Inside a DGX H100 and H200 system."""

from __future__ import annotations

import sys

from dgx_h100_h200 import (
    DGX_HOPPER_VARIANTS,
    GPU_TRAY_FW_COMPONENTS,
    MOTHERBOARD_TRAY_FW_COMPONENTS,
    calculate_training_mfu,
    classify_dgx_topology_hop,
    compute_host_ram_staging_ratio,
    simulate_dgx_firmware_activation,
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

    print("=== Chapter 9.2 Lab: Inside a DGX H100 and H200 System ===")

    h100 = DGX_HOPPER_VARIANTS["DGX-H100"]
    h200 = DGX_HOPPER_VARIANTS["DGX-H200"]

    # 1. Hardware Tray & Variant Specs (V5 Ch 2, V10 Ch 1, DAI Ch 2)
    check(
        "DGX H100 & H200 share 8U chassis, dual Xeon Platinum 8480C (112 cores), 2048 GB DDR5 across 16 channels",
        h100.chassis_ru == 8
        and h100.cpu_model == "Intel Xeon Platinum 8480C"
        and h100.cpu_sockets * h100.cores_per_socket == 112
        and h100.host_ram_gb == 2048
        and h100.host_ddr5_channels == 16,
    )
    check(
        "Each GPU has 18 NVLink 4.0 sub-links at 50 GB/s = 900 GB/s per GPU across 4 NVSwitches",
        h100.nvlink_sublinks_per_gpu * h100.nvlink_sublink_bw_gbps == 900.0
        and h100.nvswitch_count == 4,
    )
    check(
        "NVSwitch baseboard delivers 3.6 TB/s bisection and 7.2 TB/s aggregate bidirectional bandwidth",
        h100.nvswitch_bisection_tbps == 3.6 and h100.nvswitch_aggregate_tbps == 7.2,
    )
    check(
        "DGX H100 provides 8x 80 GB HBM3 = 640 GB total at 26.8 TB/s aggregate bandwidth",
        h100.total_hbm_gb == 640 and h100.aggregate_hbm_bw_tbps == 26.8,
    )
    check(
        "DGX H200 upgrades to 8x 141 GB HBM3e (143,771 MiB in nvidia-smi) = 1,128 GB at 38.4 TB/s",
        h200.per_gpu_vram_gb == 141
        and h200.nvidia_smi_mib == 143771
        and h200.total_hbm_gb == 1128
        and h200.aggregate_hbm_bw_tbps == 38.4,
    )
    check(
        "H200 provides 1.76x VRAM capacity and 1.43x HBM bandwidth over H100 in same 10.2 kW envelope",
        round(h200.total_hbm_gb / h100.total_hbm_gb, 2) == 1.76
        and round(h200.per_gpu_hbm_bw_tbps / h100.per_gpu_hbm_bw_tbps, 2) == 1.43
        and h200.max_system_power_kw == 10.2,
    )
    check(
        "Storage bay has 2x 1.92 TB M.2 (RAID 1 OS) and 8x 3.84 TB U.2 (30.72 TB raw RAID 0 /raid)",
        h100.os_m2_drives == 2
        and round(h100.scratch_u2_drives * h100.scratch_u2_size_tb, 2) == 30.72,
    )
    check(
        "Power bay has 6x 3.3 kW PSUs (19.8 kW installed capacity for 3+3 redundancy at 10.2 kW)",
        h100.psu_count == 6 and round(h100.psu_count * h100.psu_rating_kw, 1) == 19.8,
    )

    # 2. Host RAM Staging Ratio checks (V5 Ch 2 & DAI Ch 2)
    r_h100 = compute_host_ram_staging_ratio("DGX-H100")
    check(
        "DGX H100 host RAM ratio is 2048 / 640 == 3.2x (exceeds 2x-3x staging rule)",
        r_h100["ram_to_vram_ratio"] == 3.2 and r_h100["meets_2x_rule"] is True,
        f"got {r_h100}",
    )
    r_h200 = compute_host_ram_staging_ratio("DGX-H200")
    check(
        "DGX H200 host RAM ratio is 2048 / 1128 == 1.82x (meets 1.5x-2x staging rule)",
        r_h200["ram_to_vram_ratio"] == 1.82 and r_h200["meets_1_5x_minimum"] is True,
        f"got {r_h200}",
    )

    # 3. PCIe Gen5 Switch & NVSwitch Topology Matrix checks (V5 Ch 2 & V7 Ch 2)
    hop_self = classify_dgx_topology_hop("GPU0", "GPU0")
    check("GPU0 to GPU0 is X (Self)", hop_self["symbol"] == "X")

    hop_nv = classify_dgx_topology_hop("GPU0", "GPU7")
    check(
        "GPU0 to GPU7 is NV18 (900 GB/s via NVSwitch, bypasses CPU and UPI)",
        hop_nv["symbol"] == "NV18"
        and hop_nv["bandwidth_gbps"] == 900.0
        and hop_nv["bypasses_cpu"] is True
        and hop_nv["crosses_upi"] is False,
    )

    for g_idx in range(8):
        hop_pix = classify_dgx_topology_hop(f"GPU{g_idx}", f"mlx5_{g_idx}")
        check(
            f"GPU{g_idx} to paired mlx5_{g_idx} is PIX on shared PCIe Gen5 switch",
            hop_pix["symbol"] == "PIX" and hop_pix["bypasses_cpu"] is True,
            f"got {hop_pix}",
        )

    hop_nvme_pix = classify_dgx_topology_hop("GPU2", "nvme3")
    check(
        "GPU2 to nvme3 on PCIe Switch 1 is PIX (direct GDS DMA path)",
        hop_nvme_pix["symbol"] == "PIX" and hop_nvme_pix["bypasses_cpu"] is True,
    )

    hop_node = classify_dgx_topology_hop("GPU0", "mlx5_2")
    check(
        "GPU0 (Switch 0) to mlx5_2 (Switch 1) on NUMA 0 is NODE (hits CPU root complex)",
        hop_node["symbol"] == "NODE"
        and hop_node["bypasses_cpu"] is False
        and hop_node["crosses_upi"] is False,
    )

    hop_sys = classify_dgx_topology_hop("GPU0", "mlx5_6")
    check(
        "V5 Ch2 Customer Scenario: GPU0 (NUMA 0) to mlx5_6 (NUMA 1) is SYS (crosses Intel UPI)",
        hop_sys["symbol"] == "SYS"
        and hop_sys["bypasses_cpu"] is False
        and hop_sys["crosses_upi"] is True,
    )

    try:
        classify_dgx_topology_hop("GPU8", "mlx5_0")
        check("Rejects invalid GPU index GPU8", False, "did not raise ValueError")
    except ValueError:
        check("Rejects invalid GPU index GPU8", True)

    # 4. MFU physics checks (Distributed AI Systems Ch 2)
    mfu_70b = calculate_training_mfu(
        params_billions=70.0,
        tokens_per_iteration=2048,
        iteration_time_sec=2.0,
        gpu_count=1,
        peak_tflops_per_gpu=989.0,
        flops_per_Iteration_override_tflop=860.0,
    )
    check(
        "DAI Ch2 70B H100 worked example: 860 TFLOP / 2.0s = 430 TFLOPS / 989 peak == 43.48% MFU",
        mfu_70b["actual_tflops_per_gpu"] == 430.0 and mfu_70b["mfu_percent"] == 43.48,
        f"got {mfu_70b}",
    )

    mfu_formula = calculate_training_mfu(
        params_billions=70.0,
        tokens_per_iteration=2048,
        iteration_time_sec=2.0,
        gpu_count=1,
        peak_tflops_per_gpu=989.0,
    )
    check(
        "6 * N * T transformer FLOP formula for 70B * 2048 tokens == 860.16 TFLOP",
        mfu_formula["iter_tflop"] == 860.16,
        f"got {mfu_formula}",
    )

    # 5. BCM 11 Section 14.5 DGX H100 Firmware Inventory & AC Power Cycle checks
    check(
        "BCM 11 p.758: Motherboard tray has 16 firmware components and GPU tray has 30 (46 total)",
        len(MOTHERBOARD_TRAY_FW_COMPONENTS) == 16
        and len(GPU_TRAY_FW_COMPONENTS) == 30
        and len(MOTHERBOARD_TRAY_FW_COMPONENTS) + len(GPU_TRAY_FW_COMPONENTS) == 46,
    )

    fw_dc = simulate_dgx_firmware_activation("gpu_tray_fwpkg", reset_action="dc_reset")
    check(
        "BCM 11 p.761: DC board reset after GPU-tray flash leaves 30 HGX components pending AC power cycle",
        fw_dc["activated"] is False
        and fw_dc["state"] == "pending"
        and fw_dc["result"] == "success: AC power cycle to activate",
        f"got {fw_dc}",
    )

    fw_ac = simulate_dgx_firmware_activation("gpu_tray_fwpkg", reset_action="ac_power_cycle")
    check(
        "BCM 11 p.761: Full AC power cycle activates all 30 GPU-tray firmware components",
        fw_ac["activated"] is True
        and fw_ac["state"] == "completed"
        and fw_ac["result"] == "success: activated"
        and fw_ac["updated_components"] == 30,
        f"got {fw_ac}",
    )

    fw_mb = simulate_dgx_firmware_activation("motherboard_tray_fwpkg", reset_action="dc_reset")
    check(
        "Motherboard-tray firmware package updates 16 components and leaves 30 GPU-tray components untouched",
        fw_mb["updated_components"] == 16 and fw_mb["untouched_components"] == 30,
        f"got {fw_mb}",
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
