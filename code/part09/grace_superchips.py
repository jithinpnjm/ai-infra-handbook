#!/usr/bin/env python3
"""Part 9, Chapter 9.4: Grace CPU, GH200, GB200, and GB300 Superchips model.

Models the Grace Arm Neoverse V2 CPU, NVLink-C2C coherent interconnect physics
(900 GB/s bidirectional vs 64 GB/s PCIe Gen5), unified virtual memory tiering,
SuperOffload / GraceAdam (Arm SVE), and superchip specifications across:
- Grace CPU Superchip (2x Grace = 144 cores)
- GH200 Grace Hopper Superchip (1x Grace + 1x H100/H200)
- GB200 Grace Blackwell Superchip (1x Grace + 2x B200)
- GB300 Grace Blackwell Ultra Superchip (1x Grace + 2x B300)
- VR200 Vera Rubin Superchip (roadmap)

Sources:
- nvidia-devops Volume 04 Chapter 7 ("The Grace CPU and Superchips")
- AI Systems Performance Engineering Chapters 2, 3, and 13
- Distributed AI Systems Chapter 2
- superpod-gb300-ra (pp. 8-10)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SuperchipSpec:
    """Hardware specification for an NVIDIA Grace-based Superchip module."""

    name: str
    cpu_architecture: str
    cpu_count: int
    total_arm_cores: int
    lpddr_type: str
    lpddr_capacity_gb: int
    lpddr_bw_gbps: float
    gpu_architecture: str
    gpu_count: int
    total_hbm_gb: int
    total_hbm_bw_tbps: float
    c2c_bidirectional_gbps: float
    c2c_unidirectional_gbps: float
    c2c_pj_per_bit: float
    max_module_tdp_w: int


SUPERCHIP_CATALOG: Dict[str, SuperchipSpec] = {
    "Grace-CPU-Superchip": SuperchipSpec(
        name="Grace-CPU-Superchip",
        cpu_architecture="Arm Neoverse V2",
        cpu_count=2,
        total_arm_cores=144,
        lpddr_type="LPDDR5X",
        lpddr_capacity_gb=960,
        lpddr_bw_gbps=1000.0,
        gpu_architecture="None",
        gpu_count=0,
        total_hbm_gb=0,
        total_hbm_bw_tbps=0.0,
        c2c_bidirectional_gbps=900.0,
        c2c_unidirectional_gbps=450.0,
        c2c_pj_per_bit=5.0,
        max_module_tdp_w=500,
    ),
    "GH200-96GB": SuperchipSpec(
        name="GH200-96GB",
        cpu_architecture="Arm Neoverse V2",
        cpu_count=1,
        total_arm_cores=72,
        lpddr_type="LPDDR5X",
        lpddr_capacity_gb=480,  # 512 GB variant also noted in DAI Ch 2 (608 GB total)
        lpddr_bw_gbps=500.0,
        gpu_architecture="Hopper",
        gpu_count=1,
        total_hbm_gb=96,
        total_hbm_bw_tbps=4.0,
        c2c_bidirectional_gbps=900.0,
        c2c_unidirectional_gbps=450.0,
        c2c_pj_per_bit=5.0,
        max_module_tdp_w=1000,
    ),
    "GH200-144GB": SuperchipSpec(
        name="GH200-144GB",
        cpu_architecture="Arm Neoverse V2",
        cpu_count=1,
        total_arm_cores=72,
        lpddr_type="LPDDR5X",
        lpddr_capacity_gb=480,
        lpddr_bw_gbps=500.0,
        gpu_architecture="Hopper HBM3e",
        gpu_count=1,
        total_hbm_gb=144,
        total_hbm_bw_tbps=4.9,
        c2c_bidirectional_gbps=900.0,
        c2c_unidirectional_gbps=450.0,
        c2c_pj_per_bit=5.0,
        max_module_tdp_w=1000,
    ),
    "GB200": SuperchipSpec(
        name="GB200",
        cpu_architecture="Arm Neoverse V2",
        cpu_count=1,
        total_arm_cores=72,
        lpddr_type="LPDDR5X",
        lpddr_capacity_gb=480,
        lpddr_bw_gbps=500.0,
        gpu_architecture="Blackwell B200",
        gpu_count=2,
        total_hbm_gb=384,  # 2x 192 GB (or 2x 180 GB = 360 GB usable in ASP Ch 2 p.28)
        total_hbm_bw_tbps=16.0,
        c2c_bidirectional_gbps=900.0,
        c2c_unidirectional_gbps=450.0,
        c2c_pj_per_bit=5.0,
        max_module_tdp_w=2700,
    ),
    "GB300": SuperchipSpec(
        name="GB300",
        cpu_architecture="Arm Neoverse V2",
        cpu_count=1,
        total_arm_cores=72,
        lpddr_type="LPDDR5X",
        lpddr_capacity_gb=500,  # ~500 GB per module in ASP Ch 2 chunk 8 (18 TB / 36 modules)
        lpddr_bw_gbps=500.0,
        gpu_architecture="Blackwell Ultra B300",
        gpu_count=2,
        total_hbm_gb=576,  # 2x 288 GB HBM3e
        total_hbm_bw_tbps=16.0,
        c2c_bidirectional_gbps=900.0,
        c2c_unidirectional_gbps=450.0,
        c2c_pj_per_bit=5.0,
        max_module_tdp_w=2800,
    ),
}


def compare_c2c_vs_pcie_gen5() -> Dict[str, float]:
    """Compare NVLink-C2C against PCIe Gen5 x16 bandwidth and energy efficiency.

    Source: nvidia-devops Volume 04 Chapter 7 ("1. The Bottleneck", "3. NVLink-C2C"):
    - PCIe Gen5 x16: 64 GB/s unidirectional, 128 GB/s bidirectional.
    - NVLink-C2C: 450 GB/s unidirectional, 900 GB/s bidirectional (>7x PCIe Gen5),
      at <5 pJ/bit (>5x more energy-efficient than PCIe Gen5 on standard PCBs).
    """
    pcie_uni = 64.0
    pcie_bi = 128.0
    c2c_uni = 450.0
    c2c_bi = 900.0
    speedup = round(c2c_bi / pcie_bi, 2)
    uni_speedup = round(c2c_uni / pcie_uni, 2)
    return {
        "pcie_gen5_unidirectional_gbps": pcie_uni,
        "pcie_gen5_bidirectional_gbps": pcie_bi,
        "nvlink_c2c_unidirectional_gbps": c2c_uni,
        "nvlink_c2c_bidirectional_gbps": c2c_bi,
        "bandwidth_multiplier": speedup,
        "unidirectional_multiplier": uni_speedup,
    }


def estimate_host_to_gpu_transfer_seconds(payload_gb: float, link_type: str) -> float:
    """Estimate raw unidirectional transfer time (seconds) across PCIe Gen5 x16 vs NVLink-C2C.

    My inference: quantifies the V4 Ch 7 1.2 TB (1,200 GB) GNN feature-table streaming
    comparison across 64 GB/s PCIe Gen5 x16 (18.75 s per pass) vs 450 GB/s NVLink-C2C (2.67 s per pass).
    """
    if payload_gb <= 0:
        raise ValueError("payload_gb must be positive.")
    if link_type == "pcie_gen5_x16":
        return round(payload_gb / 64.0, 2)
    if link_type == "nvlink_c2c":
        return round(payload_gb / 450.0, 2)
    raise ValueError(f"Unknown link_type: {link_type}")


def evaluate_superchip_memory_placement(
    superchip_name: str,
    num_superchips: int,
    hot_working_set_gb: float,
    cold_overflow_gb: float,
) -> Dict[str, object]:
    """Evaluate how a workload's hot (HBM) and cold/overflow (LPDDR5X) tensors fit on Superchips.

    Sources:
    - nvidia-devops Volume 04 Chapter 7 ("4. The Superchip Lineup", Customer Scenario)
    - AI Systems Performance Engineering Chapter 13 ("Unified CPU-GPU Superchip Architecture"):
      Keep hot weights/activations/KV-cache in GPU HBM3/HBM3e (4-16 TB/s) and place overflow,
      embedding tables, or optimizer states in Grace LPDDR5X (~500 GB/s, accessed coherently
      at 450 GB/s per direction over NVLink-C2C with cudaMemPrefetchAsync).
    """
    if superchip_name not in SUPERCHIP_CATALOG:
        raise KeyError(f"Unknown superchip: {superchip_name}")
    if num_superchips <= 0 or hot_working_set_gb < 0 or cold_overflow_gb < 0:
        raise ValueError("num_superchips must be >= 1 and memory sizes >= 0.")

    spec = SUPERCHIP_CATALOG[superchip_name]
    total_hbm_gb = spec.total_hbm_gb * num_superchips
    total_lpddr_gb = spec.lpddr_capacity_gb * num_superchips
    total_coherent_gb = total_hbm_gb + total_lpddr_gb
    total_workload_gb = round(hot_working_set_gb + cold_overflow_gb, 2)

    hot_fits_in_hbm = hot_working_set_gb <= total_hbm_gb
    hbm_spill_to_lpddr_gb = max(0.0, round(hot_working_set_gb - total_hbm_gb, 2))
    used_lpddr_gb = round(cold_overflow_gb + hbm_spill_to_lpddr_gb, 2)
    fits_in_coherent_pool = total_workload_gb <= total_coherent_gb and used_lpddr_gb <= total_lpddr_gb

    return {
        "superchip": superchip_name,
        "num_superchips": num_superchips,
        "total_hbm_gb": total_hbm_gb,
        "total_lpddr_gb": total_lpddr_gb,
        "total_coherent_memory_gb": total_coherent_gb,
        "hot_fits_entirely_in_hbm": hot_fits_in_hbm,
        "hbm_spill_to_lpddr_gb": hbm_spill_to_lpddr_gb,
        "used_lpddr_gb": used_lpddr_gb,
        "fits_in_coherent_pool": fits_in_coherent_pool,
    }


def audit_superchip_runtime_config(config: Dict[str, object]) -> Dict[str, object]:
    """Audit OS, NUMA, memory allocator, and SuperOffload settings on a Grace Superchip node.

    Sources:
    - AI Systems Performance Engineering Chapter 2 (chunk 7):
      Only CPU-to-GPU over NVLink-C2C is hardware cache-coherent; GPU-to-GPU caches across
      NVSwitch are NOT hardware cache-coherent (require NCCL / NVSHMEM synchronization).
    - AI Systems Performance Engineering Chapter 3 (lines 52, 284-315):
      Linux models Grace LPDDR5X as CPU NUMA memory and HBM as device memory; pin CPU workers
      to local Grace NUMA node; enable large pages / THP (or madvise for low-latency inference)
      when using unified memory without pin_memory.
    - AI Systems Performance Engineering Chapter 13 (chunk 71):
      SuperOffload uses Speculation-Then-Validation (STV), heterogeneous optimizer split, and
      GraceAdam with Arm SVE (32 vector registers, 16 predicate registers).
    """
    issues: List[str] = []

    if bool(config.get("assumes_gpu_to_gpu_hardware_cache_coherence", False)):
        issues.append(
            "invalid_coherence_assumption (only CPU-GPU NVLink-C2C is cache-coherent; GPU-to-GPU requires NCCL/NVSHMEM sync)"
        )

    if not bool(config.get("cpu_threads_bound_to_local_grace_numa", False)):
        issues.append("unbound_cpu_threads (must pin workers to local Grace CPU NUMA node)")

    uses_unified_memory = bool(config.get("uses_unified_memory_without_pinning", False))
    large_pages_enabled = bool(config.get("large_pages_enabled", False))
    if uses_unified_memory and not large_pages_enabled:
        issues.append("unified_memory_missing_large_pages (causes TLB pressure and page-fault stalls)")

    if str(config.get("workload_type", "training")) == "low_latency_inference":
        thp_mode = str(config.get("thp_mode", "madvise"))
        if thp_mode == "always":
            issues.append("thp_always_on_inference (background THP compaction causes latency spikes; use madvise or never)")

    if bool(config.get("hot_activations_placed_in_lpddr", False)):
        issues.append("misplaced_hot_tensors (hot activations/KV-cache belong in HBM, not LPDDR5X)")

    if bool(config.get("uses_x86_avx_intrinsics", False)):
        issues.append("incompatible_x86_simd_on_grace (Grace uses Arm A64 SVE with 32 vector + 16 predicate registers)")

    return {
        "valid_configuration": len(issues) == 0,
        "issues": issues,
    }
