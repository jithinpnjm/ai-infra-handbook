#!/usr/bin/env python3
"""Chapter 10.1 model: Why GPUs — CPU vs GPU and Throughput Design.

Encodes the verifiable rules, formulas, and worked examples from:
- AI Systems Performance Engineering (ASP) Chapter 1 (pp. 1-19):
  Goodput ("effective training-time ratio" vs "speed of light"), dense
  transformer training compute heuristic (C = 6*N*D), 100T-parameter weight
  memory and node sizing (B200 180 GB vs B300 288 GB), DeepSeek-V3/R1 MoE
  expert activation (1 shared + 8 routed of 256 experts, ~37B active of ~680B
  total on export-restricted H800 400 GB/s NVLink vs H100 900 GB/s NVLink).
- Parallel and High Performance Computing (PHPC) Chapter 9 (Sections 9.1-9.7):
  OpenCL/AMD/NVIDIA/Intel terminology map, theoretical peak scalar/vector
  FLOPs formula (Clock_MHz * CUs * PEs_per_CU * 2 FMA), theoretical peak
  memory bandwidth formula (Clock_GHz * Bus_bits / 8 * Multiplier), PCIe
  Gen1-Gen6 theoretical unidirectional bandwidth formula with 8b/10b (20%
  overhead -> 80% factor) vs 128b/130b (1.54% overhead -> 98.46% factor),
  CloverLeaf time-to-solution comparison, 10 TB/s memory-bandwidth system
  energy comparison (12 V100 GPUs vs 45 Xeon Gold 6152 CPUs), and 100-job
  suite parallel-efficiency scheduling trade-off.
- nvidia-devops Volume 01 (Chapters 1-9, Labs 1-2) and Volume 02 (Chapter 1):
  CPU vs GPU silicon budget, warp lane utilization, scalar CUDA core vs
  4x4 Tensor Core operation ratio, precision byte cascade (FP64 -> FP4),
  host inspection 3-layer state machine (lspci -> which nvidia-smi ->
  nvidia-smi), and staged request-path latency analyzer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List


class ThroughputDesignError(ValueError):
    """Raised when invalid hardware or workload parameters are provided."""


# 1. Silicon budget and cross-vendor terminology (nvidia-devops V1 Ch 2; PHPC Ch 9 Table 9.1 & 9.2)
SILICON_BUDGET_PCT: Dict[str, Dict[str, int]] = {
    "CPU": {
        "control_and_branch_prediction": 35,
        "l1_l2_l3_caches": 45,
        "compute_alus": 20,
    },
    "GPU": {
        "compute_alus": 80,
        "registers_and_l1": 15,
        "control_logic": 5,
    },
}

TERMINOLOGY_MAP: Dict[str, Dict[str, str]] = {
    "multiprocessor": {
        "opencl": "Compute unit (CU)",
        "amd": "Compute unit (CU)",
        "nvidia": "Streaming multiprocessor (SM)",
        "intel": "Subslice",
    },
    "processing_core": {
        "opencl": "Processing element (PE)",
        "amd": "Processing element (PE)",
        "nvidia": "CUDA core (Compute core)",
        "intel": "Execution unit (EU)",
    },
    "thread": {
        "opencl": "Work Item",
        "amd": "Work Item",
        "nvidia": "Thread",
        "intel": "Thread",
    },
    "simd_group": {
        "opencl": "Subgroup / Vector",
        "amd": "Wavefront / Subgroup (64)",
        "nvidia": "SIMT Warp (32)",
        "intel": "SIMD",
    },
    "replication_block": {
        "opencl": "Compute device cluster",
        "amd": "Shader Engine (SE)",
        "nvidia": "Graphics Processing Cluster (GPC)",
        "intel": "Slice",
    },
}


def calc_peak_tflops(
    clock_mhz: float,
    compute_units: int,
    cores_per_cu: int,
    flops_per_cycle: int = 2,
) -> float:
    """Calculate theoretical peak TFLOP/s per PHPC Chapter 9 Section 9.2.4 (p. 291).

    Formula:
        Peak TFLOP/s = (Clock_MHz * Compute_Units * Cores_per_CU * Flops_per_cycle) / 10^6
    where Flops_per_cycle = 2 for fused multiply-add (FMA).
    Note: PHPC p. 291 prints 15.6 TFLOPS for V100 FP32 (where exact 2*1530*80*64/1e6 = 15.6672,
    truncated to 1 decimal place) and rounds the others to 1 decimal place.
    """
    if clock_mhz <= 0 or compute_units <= 0 or cores_per_cu <= 0 or flops_per_cycle <= 0:
        raise ThroughputDesignError("All peak FLOPs parameters must be positive")
    return round(
        (clock_mhz * compute_units * cores_per_cu * flops_per_cycle) / 1_000_000.0,
        2,
    )


def calc_peak_memory_bandwidth_gbps(
    mem_clock_ghz: float,
    bus_width_bits: int,
    transaction_multiplier: int,
) -> float:
    """Calculate theoretical peak memory bandwidth (GB/s) per PHPC Chapter 9 Section 9.3.1 (p. 294).

    Formula:
        Bandwidth (GB/s) = Memory_Clock_GHz * Bus_Width_bits * (1 byte / 8 bits) * Multiplier
    """
    if mem_clock_ghz <= 0 or bus_width_bits <= 0 or transaction_multiplier <= 0:
        raise ThroughputDesignError("All memory bandwidth parameters must be positive")
    bw = mem_clock_ghz * (bus_width_bits / 8.0) * transaction_multiplier
    return round(bw, 1)


@dataclass(frozen=True)
class PcieGenSpec:
    generation: int
    transfer_rate_gt_s: float
    encoding_overhead_pct: float
    overhead_factor: float


PCIE_SPECS: Dict[int, PcieGenSpec] = {
    1: PcieGenSpec(1, 2.5, 20.0, 0.80),
    2: PcieGenSpec(2, 5.0, 20.0, 0.80),
    3: PcieGenSpec(3, 8.0, 1.54, 0.9846),
    4: PcieGenSpec(4, 16.0, 1.54, 0.9846),
    5: PcieGenSpec(5, 32.0, 1.54, 0.9846),
    6: PcieGenSpec(6, 64.0, 1.54, 0.9846),
}


def calc_pcie_bandwidth_gbps(generation: int, lanes: int = 16) -> float:
    """Calculate theoretical PCIe bandwidth (GB/s) per PHPC Chapter 9 Section 9.4.1 Table 9.5 (p. 299).

    Formula:
        Bandwidth (GB/s) = Lanes * TransferRate (GT/s) * OverheadFactor * (1 byte / 8 bits)
    """
    if generation not in PCIE_SPECS:
        raise ThroughputDesignError(f"Unsupported PCIe generation: {generation}")
    if lanes <= 0:
        raise ThroughputDesignError("PCIe lanes must be positive")
    spec = PCIE_SPECS[generation]
    bw = lanes * spec.transfer_rate_gt_s * spec.overhead_factor / 8.0
    return round(bw, 2)


def calc_warp_lane_efficiency(active_items: int, warp_size: int = 32) -> Dict[str, float]:
    """Calculate SIMT warp allocation and lane efficiency per nvidia-devops V1 Ch 3 (§Production Deployment).

    Because an NVIDIA GPU schedules threads in warps of 32, a batch or thread
    count of 31 still allocates 32 hardware lanes, leaving 1 lane masked off.
    """
    if active_items <= 0 or warp_size <= 0:
        raise ThroughputDesignError("active_items and warp_size must be positive")
    warps_allocated = math.ceil(active_items / warp_size)
    total_lanes = warps_allocated * warp_size
    wasted_lanes = total_lanes - active_items
    efficiency_pct = round((active_items / total_lanes) * 100.0, 2)
    return {
        "warps_allocated": warps_allocated,
        "total_lanes": total_lanes,
        "wasted_lanes": wasted_lanes,
        "efficiency_pct": efficiency_pct,
    }


def compare_scalar_vs_tensor_core_4x4() -> Dict[str, int]:
    """Compare 4x4 matrix multiply-accumulate operations on scalar CUDA cores vs Volta Tensor Core (V1 Ch 3).

    Multiplying two 4x4 matrices and accumulating a 4x4 matrix requires
    4 * 4 * 4 = 64 scalar multiply-accumulate (MAC) operations, versus 1
    matrix operation on a 4x4 Tensor Core.
    """
    scalar_mac_ops = 4 * 4 * 4
    tensor_core_ops = 1
    return {
        "scalar_mac_ops": scalar_mac_ops,
        "tensor_core_ops": tensor_core_ops,
        "operation_reduction_factor": scalar_mac_ops // tensor_core_ops,
    }


PRECISION_BYTES: Dict[str, float] = {
    "FP64": 8.0,
    "FP32": 4.0,
    "TF32": 4.0,   # stored in 32-bit registers/memory, 19-bit internal mantissa/exponent math
    "FP16": 2.0,
    "BF16": 2.0,
    "FP8": 1.0,
    "INT8": 1.0,
    "FP4": 0.5,
    "INT4": 0.5,
}


def calc_weight_memory_gb(num_params_billions: float, precision: str) -> float:
    """Calculate raw weight footprint in decimal GB (10^9 bytes) per ASP Ch 1 (p. 7) & V1 Ch 1/Ch 7."""
    if num_params_billions <= 0:
        raise ThroughputDesignError("Parameter count must be positive")
    if precision not in PRECISION_BYTES:
        raise ThroughputDesignError(f"Unsupported precision: {precision}")
    return round(num_params_billions * PRECISION_BYTES[precision], 2)


def calc_goodput_efficiency(
    useful_work_completed: float,
    elapsed_seconds: float,
    num_gpus: int,
    peak_per_gpu_per_sec: float,
) -> Dict[str, float]:
    """Calculate Goodput and cluster efficiency per ASP Chapter 1 (p. 13).

    Worked example in ASP Ch 1:
        8 GPUs process 100,000 tokens in 10 seconds -> 10,000 tokens/s goodput.
        At 1,500 tokens/s peak per GPU (12,000 tokens/s across 8 GPUs),
        efficiency = 10,000 / 12,000 = 83.3%.
    """
    if useful_work_completed < 0 or elapsed_seconds <= 0 or num_gpus <= 0 or peak_per_gpu_per_sec <= 0:
        raise ThroughputDesignError("Invalid goodput parameters")
    achieved_goodput = useful_work_completed / elapsed_seconds
    cluster_speed_of_light = num_gpus * peak_per_gpu_per_sec
    efficiency_pct = round((achieved_goodput / cluster_speed_of_light) * 100.0, 1)
    wasted_pct = round(100.0 - efficiency_pct, 1)
    return {
        "achieved_goodput_per_sec": round(achieved_goodput, 2),
        "speed_of_light_per_sec": round(cluster_speed_of_light, 2),
        "efficiency_pct": efficiency_pct,
        "wasted_pct": wasted_pct,
    }


def calc_dense_training_flops(num_params: float, num_tokens: float) -> float:
    """Calculate dense transformer training compute C ≈ 6*N*D per ASP Chapter 1 (p. 6).

    For N = 100e12 (100T parameters) and D = 29e12 (29T tokens),
    C = 6 * 1e14 * 2.9e13 = 1.74e28 FLOPs.
    """
    if num_params <= 0 or num_tokens <= 0:
        raise ThroughputDesignError("num_params and num_tokens must be positive")
    return 6.0 * num_params * num_tokens


def size_100t_weight_cluster(
    total_params_trillions: float = 100.0,
    bytes_per_param: float = 2.0,
    gpu_hbm_gb: float = 180.0,
    gpus_per_node: int = 8,
) -> Dict[str, int]:
    """Size GPU and 8-GPU node counts to hold raw model weights per ASP Chapter 1 (p. 7).

    ASP Ch 1 p. 7 states:
    - 100T parameters at FP16 (2 bytes) = 200 TB (200,000 GB) of GPU memory.
    - At 180 GB per B200 GPU -> ~1,110 GPUs (~1,112 exact ceil) / ~125-139 8-GPU nodes.
    - At 288 GB per B300 GPU -> ~695 GPUs (ceil(200,000 / 288) = 695) / ~86-87 8-GPU nodes.
    """
    if total_params_trillions <= 0 or bytes_per_param <= 0 or gpu_hbm_gb <= 0 or gpus_per_node <= 0:
        raise ThroughputDesignError("All sizing parameters must be positive")
    total_weight_gb = total_params_trillions * 1000.0 * bytes_per_param
    min_gpus = math.ceil(total_weight_gb / gpu_hbm_gb)
    min_nodes = math.ceil(min_gpus / gpus_per_node)
    return {
        "total_weight_tb": int(total_weight_gb // 1000),
        "total_weight_gb": int(total_weight_gb),
        "min_gpus_exact_ceil": min_gpus,
        "min_nodes_exact_ceil": min_nodes,
    }


def evaluate_deepseek_v3_moe() -> Dict[str, float]:
    """Return the DeepSeek-V3 MoE architecture parameters stated in ASP Chapter 1 (pp. 4-7)."""
    total_params_b = 680.0
    active_params_b = 37.0
    shared_experts = 1
    routed_experts = 8
    total_routed_pool = 256
    active_experts = shared_experts + routed_experts
    h800_nvlink_gbps = 400.0
    h100_nvlink_gbps = 900.0
    return {
        "total_params_b": total_params_b,
        "active_params_b": active_params_b,
        "active_param_fraction_pct": round((active_params_b / total_params_b) * 100.0, 2),
        "shared_experts": shared_experts,
        "routed_experts": routed_experts,
        "total_routed_pool": total_routed_pool,
        "active_experts_per_token": active_experts,
        "h800_nvlink_gbps": h800_nvlink_gbps,
        "h100_nvlink_gbps": h100_nvlink_gbps,
        "nvlink_ratio_h800_to_h100": round(h800_nvlink_gbps / h100_nvlink_gbps, 3),
    }


def calc_energy_kwh(num_processors: int, tdp_watts: float, hours: float) -> float:
    """Calculate upper-bound energy consumption in kWh per PHPC Chapter 9 Section 9.6.2 (p. 306).

    Formula:
        Energy (Wh) = N_Processors * R_Watts_per_Processor * T_hours
        Energy (kWh) = Energy (Wh) / 1000
    """
    if num_processors <= 0 or tdp_watts <= 0 or hours <= 0:
        raise ThroughputDesignError("Energy calculation parameters must be positive")
    return round((num_processors * tdp_watts * hours) / 1000.0, 2)


def calc_job_suite_turnaround(
    num_jobs: int,
    cluster_processors: int,
    base_procs_per_job: int,
    base_hours_per_job: float,
    scaled_procs_per_job: int,
    parallel_efficiency: float,
) -> Dict[str, float]:
    """Compare total suite run time for base vs scaled per-job parallelism per PHPC Ch 9 Section 9.6.2 (p. 309).

    Worked example in PHPC Ch 9:
    - 100 jobs on a 200-processor cluster.
    - Case 1 (20 procs/job): 10 concurrent jobs * 10 hrs/job = 100 hrs total.
    - Case 2 (40 procs/job at 80% parallel efficiency):
      P_mult = 40 / 20 = 2.0
      Speedup S = P_efficiency * P_mult = 0.8 * 2 = 1.6
      T_new = T_base / S = 10 / 1.6 = 6.25 hrs/job
      Concurrent jobs = 200 / 40 = 5
      Total Suite Time = 6.25 * (100 / 5) = 125 hrs.
    """
    if (
        num_jobs <= 0
        or cluster_processors <= 0
        or base_procs_per_job <= 0
        or base_hours_per_job <= 0
        or scaled_procs_per_job <= base_procs_per_job
        or not (0.0 < parallel_efficiency <= 1.0)
    ):
        raise ThroughputDesignError("Invalid job suite parameters")

    base_concurrent = cluster_processors // base_procs_per_job
    scaled_concurrent = cluster_processors // scaled_procs_per_job
    if base_concurrent <= 0 or scaled_concurrent <= 0:
        raise ThroughputDesignError("procs_per_job exceeds cluster_processors")

    p_mult = scaled_procs_per_job / base_procs_per_job
    speedup = parallel_efficiency * p_mult
    scaled_hours_per_job = base_hours_per_job / speedup

    base_batches = math.ceil(num_jobs / base_concurrent)
    scaled_batches = math.ceil(num_jobs / scaled_concurrent)

    base_suite_hours = round(base_batches * base_hours_per_job, 2)
    scaled_suite_hours = round(scaled_batches * scaled_hours_per_job, 2)

    return {
        "p_mult": round(p_mult, 2),
        "speedup": round(speedup, 2),
        "scaled_hours_per_job": round(scaled_hours_per_job, 2),
        "base_suite_hours": base_suite_hours,
        "scaled_suite_hours": scaled_suite_hours,
    }


def diagnose_host_and_request_stage(
    lspci_has_nvidia: bool,
    nvidia_smi_binary_present: bool,
    nvidia_smi_comm_ok: bool,
    preprocess_ms: float = 20.0,
    execution_ms: float = 80.0,
    serialization_ms: float = 1.0,
) -> Dict[str, object]:
    """Classify host GPU readiness (V1 Lab 01) and staged request bottleneck (V1 Lab 02).

    Note: Combining the 3-layer host inspection state machine from V1 Lab 01
    with the staged request latency breakdown from V1 Lab 02 into a single
    diagnostic classifier is an authoring synthesis ("my inference").
    """
    if preprocess_ms < 0 or execution_ms < 0 or serialization_ms < 0:
        raise ThroughputDesignError("Stage durations cannot be negative")

    if not lspci_has_nvidia:
        host_state = "NO_PCI_GPU_VISIBLE"
        next_action = "Check VM SKU, PCIe seating, BIOS, or hypervisor passthrough before installing drivers"
    elif not nvidia_smi_binary_present:
        host_state = "GPU_VISIBLE_TOOLING_MISSING"
        next_action = "Hardware is on the PCIe bus; install NVIDIA driver and user-space utilities (nvidia-smi)"
    elif not nvidia_smi_comm_ok:
        host_state = "DRIVER_COMMUNICATION_FAILED"
        next_action = "Inspect dmesg/journalctl -k for nvidia.ko load failure or kernel/DKMS mismatch"
    else:
        host_state = "HOST_GPU_READY"
        next_action = "Proceed to workload and stage-latency inspection"

    total_ms = preprocess_ms + execution_ms + serialization_ms
    prep_share_pct = round((preprocess_ms / total_ms) * 100.0, 1) if total_ms > 0 else 0.0
    exec_share_pct = round((execution_ms / total_ms) * 100.0, 1) if total_ms > 0 else 0.0

    if preprocess_ms > execution_ms:
        dominant_stage = "CPU_PREPROCESSING_BOTTLENECK"
    else:
        dominant_stage = "MODEL_EXECUTION_STAGE"

    return {
        "host_state": host_state,
        "next_action": next_action,
        "total_ms": round(total_ms, 2),
        "preprocess_share_pct": prep_share_pct,
        "execution_share_pct": exec_share_pct,
        "dominant_stage": dominant_stage,
    }
