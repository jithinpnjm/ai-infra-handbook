#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.5: GB200 and GB300 NVL72 rack-scale systems."""

from __future__ import annotations

import sys

from nvl72_rack import (
    GB200_COMPUTE_TRAY_FW_COMPONENTS,
    NVL72_CATALOG,
    NVL72_SWITCH_TRAY_FW_COMPONENTS,
    compare_moe_inference_h100_vs_nvl72,
    map_nvl72_rack_unit_zone,
    validate_nvl72_bcm_firmware_workflow,
    verify_nvl72_crossbar_topology,
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

    print("=== Chapter 9.5 Lab: GB200 and GB300 NVL72 Rack-Scale Systems ===")

    # 1. NVL72 1-stage NVLink 5 crossbar math checks (ASP Ch 2 & superpod-gb300-ra)
    xbar = verify_nvl72_crossbar_topology()
    check(
        "18 compute trays * 4 GPUs == 72 GPUs and 9 switch trays * 2 ASICs == 18 NVSwitch ASICs",
        xbar["total_gpus"] == 72 and xbar["total_switch_asics"] == 18,
    )
    check(
        "18 NVLink 5 links/GPU matches 18 NVSwitch ASICs for a 1-hop non-blocking crossbar",
        xbar["is_nonblocking_1stage_crossbar"] is True
        and xbar["links_from_each_gpu_to_each_asic"] == 1,
    )
    check(
        "Each NVSwitch ASIC terminates 72 ports and each 1U switch tray terminates 144 ports (1,296 total)",
        xbar["ports_per_nvswitch_asic"] == 72
        and xbar["ports_per_switch_tray"] == 144
        and xbar["total_backplane_nvlink_ports"] == 1296,
    )
    check(
        "Per-GPU NVLink 5 bandwidth is 1.8 TB/s and exact 72-GPU aggregate is 129.6 TB/s (~130 TB/s)",
        xbar["per_gpu_bw_tbps"] == 1.8 and xbar["exact_aggregate_bw_tbps"] == 129.6,
    )

    try:
        verify_nvl72_crossbar_topology(compute_trays=0)
        check("Rejects non-positive compute_trays in crossbar verifier", False)
    except ValueError:
        check("Rejects non-positive compute_trays in crossbar verifier", True)

    # 2. GB200 NVL72 vs GB300 NVL72 rack catalog checks
    gb200 = NVL72_CATALOG["DGX-GB200-NVL72"]
    gb300 = NVL72_CATALOG["DGX-GB300-NVL72"]

    check(
        "GB200 NVL72 has 36 Grace CPUs, 72 B200 GPUs, 13.4 TB HBM3e + 17.0 TB LPDDR5X = 30.4 TB fast memory",
        gb200.grace_cpus_per_rack == 36
        and gb200.gpus_per_rack == 72
        and gb200.total_hbm_tb == 13.4
        and gb200.total_lpddr5x_tb == 17.0
        and gb200.total_fast_memory_tb == 30.4,
    )
    check(
        "GB300 NVL72 upgrades to 288 GB/GPU = 20.7 TB HBM3e + 18.0 TB LPDDR5X = 38.7 TB fast memory",
        gb300.per_gpu_hbm_gb == 288
        and gb300.total_hbm_tb == 20.7
        and gb300.total_lpddr5x_tb == 18.0
        and gb300.total_fast_memory_tb == 38.7,
    )
    check(
        "GB300 compute tray uses 4x ConnectX-8 (800 Gbps XDR IB) + 1x BlueField-3 (2x400G) at front aisle",
        gb300.compute_nics_per_tray == 4
        and gb300.compute_nic_model == "ConnectX-8"
        and gb300.compute_nic_speed_gbps == 800
        and gb300.dpu_per_tray == 1
        and gb300.dpu_model == "BlueField-3",
    )
    check(
        "GB300 compute tray local storage is 4x 3.84 TB E1.S RAID 0 (15.36 TB) + 1x 1.92 TB M.2 OS drive",
        round(gb300.e1s_nvme_per_tray * gb300.e1s_nvme_size_tb, 2) == 15.36
        and gb300.m2_os_nvme_per_tray == 1
        and gb300.m2_os_nvme_size_tb == 1.92,
    )
    check(
        "Each NVL72 rack has 8 power shelves x 33 kW (6x 5.5 kW PSUs per shelf = 264 kW installed shelf capacity)",
        gb300.power_shelves == 8
        and gb300.psus_per_shelf == 6
        and round(gb300.psus_per_shelf * gb300.psu_rating_kw, 1) == 33.0
        and round(gb300.power_shelves * gb300.shelf_max_kw, 1) == 264.0,
    )
    check(
        "ASP Ch2 chunk 8: NVL72 rack weighs ~3,000-3,200 lbs (1.3-1.4 metric tons) and draws 130-150 kW",
        gb200.rack_weight_lbs == 3000
        and gb200.typical_rack_power_kw == 130.0
        and gb300.typical_rack_power_kw == 150.0,
    )

    # 3. 48U NVL72 Physical Rack Elevation Zone checks (BCM 11 Section 3.16 pp. 190-191)
    check(
        "BCM 11 p.191: RU 01-10 holds bottom power shelves (pwr-01..04)",
        map_nvl72_rack_unit_zone(7) == "bottom_power_shelves (pwr-01..04)",
    )
    check(
        "BCM 11 p.191: RU 11-22 holds lower compute trays (c01..c08)",
        map_nvl72_rack_unit_zone(15) == "lower_compute_trays (c01..c08)",
    )
    check(
        "BCM 11 p.190: RU 23-31 holds middle 9 NVLink switch trays (nvsw-01..09)",
        map_nvl72_rack_unit_zone(27) == "middle_nvlink_switch_trays (nvsw-01..09)",
    )
    check(
        "BCM 11 p.190: RU 32-44 holds upper compute trays (c09..c18)",
        map_nvl72_rack_unit_zone(38) == "upper_compute_trays (c09..c18)",
    )
    check(
        "BCM 11 p.190: RU 45-48 holds top power shelves (pwr-05..08)",
        map_nvl72_rack_unit_zone(48) == "top_power_shelves (pwr-05..08)",
    )
    try:
        map_nvl72_rack_unit_zone(49)
        check("Rejects RU > 48", False)
    except ValueError:
        check("Rejects RU > 48", True)

    # 4. 1.8T MoE Inference Benchmark checks (ASP Ch 2 chunk 6)
    moe = compare_moe_inference_h100_vs_nvl72()
    check(
        "ASP Ch2 chunk 6: 1.8T MoE jumps from 3.4 tok/s/GPU (>5,000 ms TTFT) on H100 to 150 tok/s/GPU (50 ms TTFT) on NVL72",
        moe["h100_tps_per_gpu"] == 3.4
        and moe["nvl72_tps_per_gpu"] == 150.0
        and moe["exact_tps_ratio"] == 44.12
        and moe["ttft_speedup_factor"] == 100.0,
    )

    # 5. BCM 11.34.0 (cm-nvfwupd 2.1.2) GB200/GB300 Firmware Lifecycle checks (pp. 762-765)
    check(
        "BCM 11 p.763-764: GB200/GB300 compute tray tracks 30 firmware components and switch tray tracks 16",
        len(GB200_COMPUTE_TRAY_FW_COMPONENTS) == 30
        and len(NVL72_SWITCH_TRAY_FW_COMPONENTS) == 16,
    )

    valid_fw = {
        "compute_tray_mode": "gb300",
        "switch_tray_mode": "gb300sw",
        "switch_tray_protocol": "NVOS_REST_API",
        "switch_accesssettings_configured": True,
        "compute_fwpkg_count_flashed": 2,
        "switch_fwpkg_count_flashed": 3,
    }
    res_fw_ok = validate_nvl72_bcm_firmware_workflow(valid_fw)
    check(
        "Valid BCM 11.34.0 GB300 NVL72 firmware workflow (Redfish 2-pkg compute + NVOS REST 3-pkg switch) passes",
        res_fw_ok["valid_workflow"] is True and len(res_fw_ok["errors"]) == 0,
        f"got {res_fw_ok}",
    )

    bad_proto = dict(valid_fw, switch_tray_protocol="Redfish")
    check(
        "BCM 11 p.763: Flags using Redfish instead of NVOS REST API for NVLink switch tray firmware",
        any("wrong_switch_tray_protocol" in e for e in validate_nvl72_bcm_firmware_workflow(bad_proto)["errors"]),
    )

    no_creds = dict(valid_fw, switch_accesssettings_configured=False)
    check(
        "BCM 11 p.763: Flags missing cmsh accesssettings username/password on NVLink switch tray",
        any("missing_switch_accesssettings" in e for e in validate_nvl72_bcm_firmware_workflow(no_creds)["errors"]),
    )

    partial_compute = dict(valid_fw, compute_fwpkg_count_flashed=1)
    check(
        "BCM 11 p.764: Flags flashing only 1 of 2 compute-tray .fwpkg files (DGX-GBX00 + HGX-GBX00 required)",
        any("partial_compute_tray_flash" in e for e in validate_nvl72_bcm_firmware_workflow(partial_compute)["errors"]),
    )

    partial_switch = dict(valid_fw, switch_fwpkg_count_flashed=2)
    check(
        "BCM 11 p.764: Flags flashing only 2 of 3 switch-tray .fwpkg files (0004 + 0006 + 0007 required)",
        any("partial_switch_tray_flash" in e for e in validate_nvl72_bcm_firmware_workflow(partial_switch)["errors"]),
    )

    bad_mode = dict(valid_fw, compute_tray_mode="dgxh100", switch_tray_mode="dgxh100")
    check(
        "Flags wrong firmwaremanagemode (must be gb200/gb300 and gb200sw/gb300sw)",
        len(validate_nvl72_bcm_firmware_workflow(bad_mode)["errors"]) == 2,
    )

    # 6. Additional SU & crossbar edge-case checks
    check(
        "ASP Ch2 chunk 9 power decomposition: 18 compute trays * 6 kW + 22 kW NVSwitch/cooling == 130 kW",
        18 * 6 + 22 == int(gb200.typical_rack_power_kw),
    )
    check(
        "superpod-gb300-ra p.5: 8x DGX GB300 NVL72 racks per Scalable Unit == 576 GPUs and 1.2 MW (1,200 kW) TDP",
        8 * gb300.gpus_per_rack == 576 and 8 * gb300.typical_rack_power_kw == 1200.0,
    )
    check(
        "Total E1.S local NVMe scratch across 18 compute trays in a rack == 18 * 15.36 TB == 276.48 TB",
        round(gb300.compute_trays * gb300.e1s_nvme_per_tray * gb300.e1s_nvme_size_tb, 2) == 276.48,
    )
    check(
        "Total East-West ConnectX-8 ports across 18 compute trays in a GB300 rack == 72 x 800 Gbps (57.6 Tbps)",
        gb300.compute_trays * gb300.compute_nics_per_tray == 72
        and (72 * gb300.compute_nic_speed_gbps) / 1000.0 == 57.6,
    )
    broken_xbar = verify_nvl72_crossbar_topology(switch_trays=8)  # Only 16 ASICs vs 18 links/GPU
    check(
        "Detects broken 1-stage crossbar if switch_trays != 9 (16 ASICs != 18 links/GPU)",
        broken_xbar["is_nonblocking_1stage_crossbar"] is False,
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
