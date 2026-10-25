#!/usr/bin/env python3
"""Part 9, Chapter 9.2: Inside a DGX H100 and H200 system model.

Models the internal hardware architecture, NVSwitch topology, 4-switch PCIe Gen5
P2P routing, NUMA alignment, H100 vs H200 memory/MFU physics, and motherboard
vs GPU-tray firmware activation lifecycle of an 8U NVIDIA DGX H100/H200 node.

Sources:
- nvidia-devops Volume 05 Chapter 2 ("Inside the DGX H100 System")
- nvidia-devops Volume 07 Chapter 2 ("PCIe, NUMA, and Host Data Paths")
- nvidia-devops Volume 10 Chapter 1 ("Bare-Metal and BMC/Redfish Lifecycle")
- Distributed AI Systems Chapter 2 ("GPU Hardware, Networking, and Parallelism")
- NVIDIA Base Command Manager 11 Administrator Manual Section 14.5 (pp. 758-762)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class DGXHopperVariant:
    """Hardware comparison between DGX H100 and DGX H200 (8U SXM5)."""

    model: str
    chassis_ru: int
    gpu_count: int
    per_gpu_vram_gb: int
    nvidia_smi_mib: int
    hbm_type: str
    per_gpu_hbm_bw_tbps: float
    total_hbm_gb: int
    aggregate_hbm_bw_tbps: float
    nvlink_sublinks_per_gpu: int
    nvlink_sublink_bw_gbps: float
    per_gpu_nvlink_bw_gbps: float
    nvswitch_count: int
    nvswitch_bisection_tbps: float
    nvswitch_aggregate_tbps: float
    cpu_model: str
    cpu_sockets: int
    cores_per_socket: int
    host_ram_gb: int
    host_ddr5_channels: int
    pcie_gen5_switches: int
    compute_cx7_nics: int
    storage_bf3_dpus: int
    os_m2_drives: int
    os_m2_size_tb: float
    scratch_u2_drives: int
    scratch_u2_size_tb: float
    psu_count: int
    psu_rating_kw: float
    max_system_power_kw: float
    bf16_peak_tflops_per_gpu: float


DGX_HOPPER_VARIANTS: Dict[str, DGXHopperVariant] = {
    "DGX-H100": DGXHopperVariant(
        model="DGX-H100",
        chassis_ru=8,
        gpu_count=8,
        per_gpu_vram_gb=80,
        nvidia_smi_mib=81920,
        hbm_type="HBM3",
        per_gpu_hbm_bw_tbps=3.35,
        total_hbm_gb=640,
        aggregate_hbm_bw_tbps=26.8,
        nvlink_sublinks_per_gpu=18,
        nvlink_sublink_bw_gbps=50.0,
        per_gpu_nvlink_bw_gbps=900.0,
        nvswitch_count=4,
        nvswitch_bisection_tbps=3.6,
        nvswitch_aggregate_tbps=7.2,
        cpu_model="Intel Xeon Platinum 8480C",
        cpu_sockets=2,
        cores_per_socket=56,
        host_ram_gb=2048,
        host_ddr5_channels=16,
        pcie_gen5_switches=4,
        compute_cx7_nics=8,
        storage_bf3_dpus=2,
        os_m2_drives=2,
        os_m2_size_tb=1.92,
        scratch_u2_drives=8,
        scratch_u2_size_tb=3.84,
        psu_count=6,
        psu_rating_kw=3.3,
        max_system_power_kw=10.2,
        bf16_peak_tflops_per_gpu=989.0,
    ),
    "DGX-H200": DGXHopperVariant(
        model="DGX-H200",
        chassis_ru=8,
        gpu_count=8,
        per_gpu_vram_gb=141,
        nvidia_smi_mib=143771,  # Exact MiB reported by nvidia-smi in Distributed AI Systems Ch 2
        hbm_type="HBM3e",
        per_gpu_hbm_bw_tbps=4.8,
        total_hbm_gb=1128,
        aggregate_hbm_bw_tbps=38.4,
        nvlink_sublinks_per_gpu=18,
        nvlink_sublink_bw_gbps=50.0,
        per_gpu_nvlink_bw_gbps=900.0,
        nvswitch_count=4,
        nvswitch_bisection_tbps=3.6,
        nvswitch_aggregate_tbps=7.2,
        cpu_model="Intel Xeon Platinum 8480C",
        cpu_sockets=2,
        cores_per_socket=56,
        host_ram_gb=2048,
        host_ddr5_channels=16,
        pcie_gen5_switches=4,
        compute_cx7_nics=8,
        storage_bf3_dpus=2,
        os_m2_drives=2,
        os_m2_size_tb=1.92,
        scratch_u2_drives=8,
        scratch_u2_size_tb=3.84,
        psu_count=6,
        psu_rating_kw=3.3,
        max_system_power_kw=10.2,
        bf16_peak_tflops_per_gpu=989.0,
    ),
}

# Exact 46 firmware component identifiers from BCM 11 Admin Manual Section 14.5 (pp. 758-762)
MOTHERBOARD_TRAY_FW_COMPONENTS: Tuple[str, ...] = (
    "CPLDMB_0",
    "CPLDMID_0",
    "EROT_BIOS_0",
    "EROT_BMC_0",
    "HostBIOS_0",
    "HostBMC_0",
    "PCIeRetimer_0",
    "PCIeRetimer_1",
    "PCIeSwitch_0",
    "PCIeSwitch_1",
    "PSU_0",
    "PSU_1",
    "PSU_2",
    "PSU_3",
    "PSU_4",
    "PSU_5",
)

GPU_TRAY_FW_COMPONENTS: Tuple[str, ...] = (
    "HGX_FW_BMC_0",
    "HGX_FW_ERoT_BMC_0",
    "HGX_FW_ERoT_FPGA_0",
    "HGX_FW_ERoT_NVSwitch_0",
    "HGX_FW_ERoT_NVSwitch_1",
    "HGX_FW_ERoT_NVSwitch_2",
    "HGX_FW_ERoT_NVSwitch_3",
    "HGX_FW_ERoT_PCIeSwitch_0",
    "HGX_FW_FPGA_0",
    "HGX_FW_GPU_SXM_1",
    "HGX_FW_GPU_SXM_2",
    "HGX_FW_GPU_SXM_3",
    "HGX_FW_GPU_SXM_4",
    "HGX_FW_GPU_SXM_5",
    "HGX_FW_GPU_SXM_6",
    "HGX_FW_GPU_SXM_7",
    "HGX_FW_GPU_SXM_8",
    "HGX_FW_NVSwitch_0",
    "HGX_FW_NVSwitch_1",
    "HGX_FW_NVSwitch_2",
    "HGX_FW_NVSwitch_3",
    "HGX_FW_PCIeRetimer_0",
    "HGX_FW_PCIeRetimer_1",
    "HGX_FW_PCIeRetimer_2",
    "HGX_FW_PCIeRetimer_3",
    "HGX_FW_PCIeRetimer_4",
    "HGX_FW_PCIeRetimer_5",
    "HGX_FW_PCIeRetimer_6",
    "HGX_FW_PCIeRetimer_7",
    "HGX_FW_PCIeSwitch_0",
)


def classify_dgx_topology_hop(source_dev: str, target_dev: str) -> Dict[str, object]:
    """Return the nvidia-smi topo -m symbol and data path between two DGX H100/H200 devices.

    Sources:
    - nvidia-devops Volume 05 Chapter 2 ("3. The PCIe Gen5 Switch Complex" & "5. Reading Topology")
    - nvidia-devops Volume 07 Chapter 2 ("4. Verifying Topology (nvidia-smi topo -m)")
    - Distributed AI Systems Chapter 2 (chunk 8)

    Layout modeled (4 PCIe Gen5 switches across 2 NUMA sockets):
    - Switch 0 (NUMA 0): GPU0, GPU1, mlx5_0, mlx5_1, nvme0, nvme1
    - Switch 1 (NUMA 0): GPU2, GPU3, mlx5_2, mlx5_3, nvme2, nvme3
    - Switch 2 (NUMA 1): GPU4, GPU5, mlx5_4, mlx5_5, nvme4, nvme5
    - Switch 3 (NUMA 1): GPU6, GPU7, mlx5_6, mlx5_7, nvme6, nvme7
    All 8 GPUs also connect to all 4 NVSwitch ASICs over 18 NVLink 4 sub-links (NV18).
    """

    def parse_dev(dev: str) -> Tuple[str, int]:
        if dev.startswith("GPU") and dev[3:].isdigit():
            idx = int(dev[3:])
            if 0 <= idx <= 7:
                return ("GPU", idx)
        if dev.startswith("mlx5_") and dev[5:].isdigit():
            idx = int(dev[5:])
            if 0 <= idx <= 7:
                return ("NIC", idx)
        if dev.startswith("nvme") and dev[4:].isdigit():
            idx = int(dev[4:])
            if 0 <= idx <= 7:
                return ("NVME", idx)
        raise ValueError(f"Unknown DGX device identifier: {dev}")

    kind_a, idx_a = parse_dev(source_dev)
    kind_b, idx_b = parse_dev(target_dev)

    if kind_a == kind_b and idx_a == idx_b:
        return {
            "symbol": "X",
            "bandwidth_gbps": 0.0,
            "bypasses_cpu": True,
            "crosses_upi": False,
            "description": "Self",
        }

    # GPU-to-GPU always traverses the 4 NVSwitches over 18 NVLink 4 sub-links
    if kind_a == "GPU" and kind_b == "GPU":
        return {
            "symbol": "NV18",
            "bandwidth_gbps": 900.0,
            "bypasses_cpu": True,
            "crosses_upi": False,
            "description": "18 bonded NVLink 4.0 sub-links via NVSwitch full mesh",
        }

    switch_a = idx_a // 2
    switch_b = idx_b // 2
    numa_a = 0 if idx_a < 4 else 1
    numa_b = 0 if idx_b < 4 else 1

    if switch_a == switch_b:
        return {
            "symbol": "PIX",
            "bandwidth_gbps": 64.0,  # PCIe Gen5 x16 unidirectional (128 GB/s bidirectional)
            "bypasses_cpu": True,
            "crosses_upi": False,
            "description": "Connection traverses at most a single PCIe Gen5 switch (optimal P2P)",
        }

    if numa_a == numa_b:
        return {
            "symbol": "NODE",
            "bandwidth_gbps": 32.0,
            "bypasses_cpu": False,
            "crosses_upi": False,
            "description": "Crosses PCIe host bridges within the same NUMA node (hits CPU root complex)",
        }

    return {
        "symbol": "SYS",
        "bandwidth_gbps": 16.0,
        "bypasses_cpu": False,
        "crosses_upi": True,
        "description": "Crosses Intel UPI inter-socket link between NUMA 0 and NUMA 1 (severe bottleneck)",
    }


def compute_host_ram_staging_ratio(variant_name: str) -> Dict[str, object]:
    """Evaluate the host DDR5 RAM to total GPU VRAM staging ratio.

    Sources:
    - nvidia-devops Volume 05 Chapter 2 ("Why 2TB of RAM?"): 2x-3x GPU VRAM rule for H100 (2048/640 = 3.2x).
    - Distributed AI Systems Chapter 2 ("CPU requirements for distributed training"): 1.5x-2x GPU VRAM rule
      (for H200: 2048/1128 = 1.82x, meeting the 1.5x-2x rule).
    """
    if variant_name not in DGX_HOPPER_VARIANTS:
        raise KeyError(f"Unknown variant: {variant_name}")
    v = DGX_HOPPER_VARIANTS[variant_name]
    ratio = round(v.host_ram_gb / float(v.total_hbm_gb), 2)
    return {
        "model": v.model,
        "host_ram_gb": v.host_ram_gb,
        "total_gpu_vram_gb": v.total_hbm_gb,
        "ram_to_vram_ratio": ratio,
        "meets_1_5x_minimum": ratio >= 1.5,
        "meets_2x_rule": ratio >= 2.0,
    }


def calculate_training_mfu(
    params_billions: float,
    tokens_per_iteration: int,
    iteration_time_sec: float,
    gpu_count: int = 1,
    peak_tflops_per_gpu: float = 989.0,
    flops_per_Iteration_override_tflop: float = 0.0,
) -> Dict[str, float]:
    """Calculate Model FLOPs Utilization (MFU) on H100/H200 GPUs.

    Source: Distributed AI Systems Chapter 2 ("Key metrics for AI clusters", chunks 1-2):
    - Worked example: 70B model, ~860 TFLOP per iteration, 2.0s iteration time ->
      430 TFLOPS actual / 989 TFLOPS BF16 peak = 43.48% (~43% MFU).
    - General dense transformer formula: FLOPs_per_iter ≈ 6 * params * tokens_per_iteration.
    """
    if iteration_time_sec <= 0 or gpu_count <= 0 or peak_tflops_per_gpu <= 0:
        raise ValueError("iteration_time_sec, gpu_count, and peak_tflops_per_gpu must be positive.")
    if flops_per_Iteration_override_tflop > 0:
        iter_tflops = flops_per_Iteration_override_tflop
    else:
        if params_billions <= 0 or tokens_per_iteration <= 0:
            raise ValueError("params_billions and tokens_per_iteration must be positive.")
        # 6 * N_params * N_tokens / 1e12 -> TFLOPs
        iter_tflops = (6.0 * (params_billions * 1e9) * tokens_per_iteration) / 1e12

    actual_tflops_total = iter_tflops / iteration_time_sec
    actual_tflops_per_gpu = actual_tflops_total / gpu_count
    mfu_pct = round((actual_tflops_per_gpu / peak_tflops_per_gpu) * 100.0, 2)
    return {
        "iter_tflop": round(iter_tflops, 2),
        "actual_tflops_per_gpu": round(actual_tflops_per_gpu, 2),
        "peak_tflops_per_gpu": peak_tflops_per_gpu,
        "mfu_percent": mfu_pct,
    }


def simulate_dgx_firmware_activation(
    package_flashed: str,
    reset_action: str,
) -> Dict[str, object]:
    """Model the DGX H100 firmware activation state machine in BCM 11 Section 14.5.

    Source: NVIDIA Base Command Manager 11 Administrator Manual Section 14.5 (pp. 758-762):
    - Flashing `nvfw_dgx-hgx-h100x8_*.fwpkg` updates the 30 GPU-tray components (`HGX_FW_*`),
      leaving the 16 motherboard-tray components untouched.
    - After flashing GPU-tray firmware, component State is `pending` with Result
      `success: AC power cycle to activate`.
    - A regular board-level `dc_reset` (`power reset` in cmsh) is NOT sufficient to initialize
      the GPU-tray components; they remain `pending`.
    - Only a full `ac_power_cycle` (cutting all AC inputs via PDU or pulling mains cords)
      transitions State to `completed` with Result `success: activated`.
    """
    if package_flashed == "gpu_tray_fwpkg":
        updated_count = len(GPU_TRAY_FW_COMPONENTS)
        untouched_count = len(MOTHERBOARD_TRAY_FW_COMPONENTS)
        if reset_action == "none" or reset_action == "dc_reset":
            return {
                "updated_components": updated_count,
                "untouched_components": untouched_count,
                "state": "pending",
                "result": "success: AC power cycle to activate",
                "activated": False,
            }
        if reset_action == "ac_power_cycle":
            return {
                "updated_components": updated_count,
                "untouched_components": untouched_count,
                "state": "completed",
                "result": "success: activated",
                "activated": True,
            }
        raise ValueError(f"Unknown reset_action: {reset_action}")

    if package_flashed == "motherboard_tray_fwpkg":
        updated_count = len(MOTHERBOARD_TRAY_FW_COMPONENTS)
        untouched_count = len(GPU_TRAY_FW_COMPONENTS)
        activated = reset_action in ("dc_reset", "ac_power_cycle")
        return {
            "updated_components": updated_count,
            "untouched_components": untouched_count,
            "state": "completed" if activated else "pending",
            "result": "success: activated" if activated else "pending reboot",
            "activated": activated,
        }

    raise ValueError(f"Unknown package_flashed: {package_flashed}")
