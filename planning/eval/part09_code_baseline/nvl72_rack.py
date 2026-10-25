#!/usr/bin/env python3
"""Part 9, Chapter 9.5: GB200 and GB300 NVL72 rack-scale systems model.

Models the physical rack elevation (48U slot map), 18-compute-tray + 9-switch-tray
1-stage NVLink 5 crossbar math (72 GPUs x 18 links = 1,296 links across 18 NVSwitch
ASICs = 129.6 TB/s / ~130 TB/s), GB200 vs GB300 NVL72 rack specs, 8x 33 kW power
shelves, and the BCM 11.34.0 dual-protocol (Redfish + NVOS REST) firmware lifecycle.

Sources:
- AI Systems Performance Engineering Chapter 2 (pp. 26-40, chunks 6-9)
- NVIDIA DGX SuperPOD Reference Architecture Featuring DGX GB300 Systems (pp. 1-20)
- NVIDIA Base Command Manager 11 Administrator Manual Section 3.16 (pp. 190-191)
  and Section 14.5 (pp. 762-765)
- nvidia-devops Volume 05 Chapter 7 & Volume 06 Chapter 7
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class NVL72RackSpec:
    """Rack-level specification for a DGX GB200 NVL72 or DGX GB300 NVL72 system."""

    model: str
    rack_units: int
    compute_trays: int
    superchips_per_tray: int
    grace_cpus_per_rack: int
    gpus_per_tray: int
    gpus_per_rack: int
    per_gpu_hbm_gb: int
    total_hbm_tb: float
    total_lpddr5x_tb: float
    total_fast_memory_tb: float
    switch_trays: int
    nvswitch_asics_per_tray: int
    total_nvswitch_asics: int
    nvlink5_links_per_gpu: int
    nvlink5_bw_per_link_gbps: float
    per_gpu_nvlink_tbps: float
    aggregate_nvlink_tbps: float
    compute_nics_per_tray: int
    compute_nic_model: str
    compute_nic_speed_gbps: int
    dpu_per_tray: int
    dpu_model: str
    e1s_nvme_per_tray: int
    e1s_nvme_size_tb: float
    m2_os_nvme_per_tray: int
    m2_os_nvme_size_tb: float
    power_shelves: int
    psus_per_shelf: int
    psu_rating_kw: float
    shelf_max_kw: float
    typical_rack_power_kw: float
    rack_weight_lbs: int
    cooling_mode: str


NVL72_CATALOG: Dict[str, NVL72RackSpec] = {
    "DGX-GB200-NVL72": NVL72RackSpec(
        model="DGX-GB200-NVL72",
        rack_units=48,
        compute_trays=18,
        superchips_per_tray=2,
        grace_cpus_per_rack=36,
        gpus_per_tray=4,
        gpus_per_rack=72,
        per_gpu_hbm_gb=180,  # 180 GB usable per GPU in ASP Ch 2 (13.4 TB) or 192 GB raw (13.8 TB)
        total_hbm_tb=13.4,
        total_lpddr5x_tb=17.0,
        total_fast_memory_tb=30.4,
        switch_trays=9,
        nvswitch_asics_per_tray=2,
        total_nvswitch_asics=18,
        nvlink5_links_per_gpu=18,
        nvlink5_bw_per_link_gbps=100.0,
        per_gpu_nvlink_tbps=1.8,
        aggregate_nvlink_tbps=130.0,
        compute_nics_per_tray=4,
        compute_nic_model="ConnectX-7",
        compute_nic_speed_gbps=400,
        dpu_per_tray=1,
        dpu_model="BlueField-3",
        e1s_nvme_per_tray=4,
        e1s_nvme_size_tb=3.84,
        m2_os_nvme_per_tray=1,
        m2_os_nvme_size_tb=1.92,
        power_shelves=8,
        psus_per_shelf=6,
        psu_rating_kw=5.5,
        shelf_max_kw=33.0,
        typical_rack_power_kw=130.0,  # 18 * 6 kW + ~20 kW NVSwitch/cooling/overhead in ASP Ch 2 chunk 9
        rack_weight_lbs=3000,
        cooling_mode="direct-liquid-cooling",
    ),
    "DGX-GB300-NVL72": NVL72RackSpec(
        model="DGX-GB300-NVL72",
        rack_units=48,
        compute_trays=18,
        superchips_per_tray=2,
        grace_cpus_per_rack=36,
        gpus_per_tray=4,
        gpus_per_rack=72,
        per_gpu_hbm_gb=288,  # 288 GB HBM3e per B300 GPU (1.5x B200)
        total_hbm_tb=20.7,   # 72 * 288 GB = 20,736 GB (~20.7 TB)
        total_lpddr5x_tb=18.0,  # 36 * 500 GB = 18,000 GB (18 TB)
        total_fast_memory_tb=38.7,
        switch_trays=9,
        nvswitch_asics_per_tray=2,
        total_nvswitch_asics=18,
        nvlink5_links_per_gpu=18,
        nvlink5_bw_per_link_gbps=100.0,
        per_gpu_nvlink_tbps=1.8,
        aggregate_nvlink_tbps=130.0,
        compute_nics_per_tray=4,
        compute_nic_model="ConnectX-8",
        compute_nic_speed_gbps=800,
        dpu_per_tray=1,
        dpu_model="BlueField-3",
        e1s_nvme_per_tray=4,
        e1s_nvme_size_tb=3.84,
        m2_os_nvme_per_tray=1,
        m2_os_nvme_size_tb=1.92,
        power_shelves=8,
        psus_per_shelf=6,
        psu_rating_kw=5.5,
        shelf_max_kw=33.0,
        typical_rack_power_kw=150.0,  # 1.2 MW per 8-rack SU in superpod-gb300-ra p. 5
        rack_weight_lbs=3200,
        cooling_mode="hybrid-liquid-air",
    ),
}

# Exact 30 Compute-Tray and 16 Switch-Tray firmware components from BCM 11 Section 14.5 (pp. 763-764)
GB200_COMPUTE_TRAY_FW_COMPONENTS: Tuple[str, ...] = (
    "CX8_0",
    "CX8_1",
    "CX8_2",
    "CX8_3",
    "FW_BMC_0",
    "FW_CPLD_0",
    "FW_CPLD_1",
    "FW_ERoT_BMC_0",
    "HGX_FW_BMC_0",
    "HGX_FW_CPLD_0",
    "HGX_FW_CPU_0",
    "HGX_FW_CPU_1",
    "HGX_FW_ERoT_BMC_0",
    "HGX_FW_ERoT_CPU_0",
    "HGX_FW_ERoT_CPU_1",
    "HGX_FW_ERoT_FPGA_0",
    "HGX_FW_ERoT_FPGA_1",
    "HGX_FW_FPGA_0",
    "HGX_FW_FPGA_1",
    "HGX_FW_GPU_0",
    "HGX_FW_GPU_1",
    "HGX_FW_GPU_2",
    "HGX_FW_GPU_3",
    "HGX_InfoROM_GPU_0",
    "HGX_InfoROM_GPU_1",
    "HGX_InfoROM_GPU_2",
    "HGX_InfoROM_GPU_3",
    "HGX_PCIeSwitchConfig_0",
    "NIC_1",  # Reported as NIC_0 on GB300 compute tray (bcm11-admin p. 764)
    "UEFI",
)

NVL72_SWITCH_TRAY_FW_COMPONENTS: Tuple[str, ...] = (
    "ASIC",
    "BIOS",
    "BMC",
    "CPLD1",
    "CPLD2",
    "CPLD3",
    "CPLD4",
    "EROT",
    "EROT-ASIC1",
    "EROT-ASIC2",
    "EROT-BMC",
    "EROT-CPU",
    "EROT-FPGA",
    "FPGA",
    "SSD",
    "transceiver",
)


def verify_nvl72_crossbar_topology(
    compute_trays: int = 18,
    gpus_per_tray: int = 4,
    links_per_gpu: int = 18,
    bw_per_link_gbps: float = 100.0,
    switch_trays: int = 9,
    asics_per_switch_tray: int = 2,
) -> Dict[str, object]:
    """Calculate the 1-stage NVLink 5 crossbar port and bandwidth math for NVL72.

    Sources:
    - AI Systems Performance Engineering Chapter 2 (chunk 7, "NVLink and NVSwitch")
    - superpod-gb300-ra (p. 19, "Multi-node NVLink Fabric (NVL5)")
    Math:
    - 18 compute trays * 4 GPUs = 72 GPUs.
    - 9 switch trays * 2 NVSwitch ASICs = 18 NVSwitch ASICs.
    - Each GPU has 18 NVLink 5 links (100 GB/s bidirectional per link = 1,800 GB/s = 1.8 TB/s).
    - Every GPU wires exactly 1 NVLink 5 link to each of the 18 NVSwitch ASICs.
    - Each NVSwitch ASIC terminates 72 NVLink 5 ports (1 from each GPU); each 2-ASIC switch
      tray terminates 144 NVLink 5 ports at 100 GB/s (1,296 total ports across 9 switch trays).
    - Aggregate bidirectional NVLink bandwidth = 72 GPUs * 1.8 TB/s = 129.6 TB/s (~130 TB/s).
    """
    if compute_trays <= 0 or gpus_per_tray <= 0 or links_per_gpu <= 0 or switch_trays <= 0 or asics_per_switch_tray <= 0:
        raise ValueError("All crossbar dimensions must be positive integers.")

    total_gpus = compute_trays * gpus_per_tray
    total_switch_asics = switch_trays * asics_per_switch_tray
    is_full_1stage_crossbar = links_per_gpu == total_switch_asics

    ports_per_asic = total_gpus if is_full_1stage_crossbar else 0
    ports_per_switch_tray = ports_per_asic * asics_per_switch_tray
    total_backplane_links = total_gpus * links_per_gpu
    per_gpu_bw_tbps = round((links_per_gpu * bw_per_link_gbps) / 1000.0, 2)
    exact_aggregate_tbps = round(total_gpus * per_gpu_bw_tbps, 1)

    return {
        "total_gpus": total_gpus,
        "total_switch_asics": total_switch_asics,
        "is_nonblocking_1stage_crossbar": is_full_1stage_crossbar,
        "links_from_each_gpu_to_each_asic": 1 if is_full_1stage_crossbar else 0,
        "ports_per_nvswitch_asic": ports_per_asic,
        "ports_per_switch_tray": ports_per_switch_tray,
        "total_backplane_nvlink_ports": total_backplane_links,
        "per_gpu_bw_tbps": per_gpu_bw_tbps,
        "exact_aggregate_bw_tbps": exact_aggregate_tbps,
    }


def map_nvl72_rack_unit_zone(ru: int) -> str:
    """Return the physical equipment zone for a rack unit (1..48) in an NVL72 48U rack.

    Source: NVIDIA Base Command Manager 11 Administrator Manual Section 3.16.1 (pp. 190-191):
    - RU 01-10: Bottom Power Shelves (`pwr-01..04`)
    - RU 11-22: Lower Compute Tray Bank (`dgx-01-c01..c08`)
    - RU 23-31: Middle NVLink Switch Tray Bank (`nvsw-01..09`)
    - RU 32-41: Upper Compute Tray Bank (`dgx-01-c09..c18`)
    - RU 45-48: Top Power Shelves (`pwr-05..08`)
    """
    if not (1 <= ru <= 48):
        raise ValueError(f"Rack unit must be between 1 and 48; got {ru}")
    if 1 <= ru <= 10:
        return "bottom_power_shelves (pwr-01..04)"
    if 11 <= ru <= 22:
        return "lower_compute_trays (c01..c08)"
    if 23 <= ru <= 31:
        return "middle_nvlink_switch_trays (nvsw-01..09)"
    if 32 <= ru <= 44:
        return "upper_compute_trays (c09..c18)"
    return "top_power_shelves (pwr-05..08)"


def compare_moe_inference_h100_vs_nvl72() -> Dict[str, float]:
    """Compare 1.8T MoE real-time inference metrics on H100 vs GB200 NVL72.

    Source: AI Systems Performance Engineering Chapter 2 (chunk 6 & chunk 7):
    - 1.8-trillion-parameter MoE model on H100: ~3.4 tokens/sec/GPU, >5,000 ms (5s) TTFT.
    - Same 1.8T MoE model on GB200 NVL72: ~150 tokens/sec/GPU, ~50 ms TTFT.
    - Exact arithmetic throughput ratio = 150 / 3.4 = 44.12x (summarized as "roughly 30x" in prose).
    """
    h100_tps = 3.4
    nvl72_tps = 150.0
    h100_ttft_ms = 5000.0
    nvl72_ttft_ms = 50.0
    return {
        "h100_tps_per_gpu": h100_tps,
        "nvl72_tps_per_gpu": nvl72_tps,
        "exact_tps_ratio": round(nvl72_tps / h100_tps, 2),
        "ttft_speedup_factor": round(h100_ttft_ms / nvl72_ttft_ms, 1),
    }


def validate_nvl72_bcm_firmware_workflow(config: Dict[str, object]) -> Dict[str, object]:
    """Validate BCM 11.34.0 (`cm-nvfwupd` 2.1.2) firmware configuration for GB200/GB300 NVL72.

    Source: NVIDIA Base Command Manager 11 Administrator Manual Section 14.5 (pp. 762-765):
    - Requires `cm-nvfwupd` >= 2.1.2 (introduced in BCM 11.34.0).
    - Compute trays require `firmwaremanagemode` in (`gb200`, `gb300`), communicate via `Redfish`,
      and must flash BOTH packages (`nvfw_DGX-GBX00_*` and `nvfw_HGX-GBX00_*`) in `/cm/local/apps/cmd/etc/htdocs/bios/firmware/gb200`.
    - NVLink switch trays require `firmwaremanagemode` in (`gb200sw`, `gb300sw`), communicate via
      `NVOS_REST_API` (requiring `accesssettings` username/password), and must flash ALL THREE packages
      (`nvfw_GB200-P4978_0004`, `nvfw_GB200-P4978_0006`, `nvfw_GB200-P4978_0007`) in `.../firmware/gb200sw`.
    - Flashing only a subset of packages leaves the tray in a partially updated state.
    """
    errors: List[str] = []

    if str(config.get("compute_tray_mode", "")) not in ("gb200", "gb300"):
        errors.append("invalid_compute_firmwaremanagemode (must be gb200 or gb300)")

    if str(config.get("switch_tray_mode", "")) not in ("gb200sw", "gb300sw"):
        errors.append("invalid_switch_firmwaremanagemode (must be gb200sw or gb300sw)")

    if str(config.get("switch_tray_protocol", "")) != "NVOS_REST_API":
        errors.append("wrong_switch_tray_protocol (NVLink switch tray uses NVOS REST API, not Redfish)")

    if not bool(config.get("switch_accesssettings_configured", False)):
        errors.append("missing_switch_accesssettings (must set username and password in cmsh accesssettings)")

    compute_pkgs = int(config.get("compute_fwpkg_count_flashed", 0))
    if compute_pkgs != 2:
        errors.append(f"partial_compute_tray_flash ({compute_pkgs}/2 packages flashed; need DGX-GBX00 + HGX-GBX00)")

    switch_pkgs = int(config.get("switch_fwpkg_count_flashed", 0))
    if switch_pkgs != 3:
        errors.append(f"partial_switch_tray_flash ({switch_pkgs}/3 packages flashed; need 0004 + 0006 + 0007)")

    return {
        "valid_workflow": len(errors) == 0,
        "errors": errors,
    }
