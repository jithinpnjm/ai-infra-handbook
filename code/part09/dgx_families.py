#!/usr/bin/env python3
"""Part 9, Chapter 9.1: DGX system families and accelerator selection model.

Every rule, formula, and specification in this module is grounded in:
- AI Systems Performance Engineering (Chris Fregly), Chapters 1 and 2 (pp. 1-55)
- NVIDIA DGX B200 Data Center Best Practices (superpod-b200-dc, pp. 4-10)
- NVIDIA DGX SuperPOD Reference Architecture Featuring DGX GB300 Systems
  (superpod-gb300-ra, pp. 1-11)
- nvidia-devops Volume 04 (Hardware Portfolio, Chapters 1-7 & Labs 1-2)
- nvidia-devops Volume 05 (DGX Systems, Chapters 1-7 & Labs 1-2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class AcceleratorSpec:
    """Hardware specification for an NVIDIA data center accelerator.

    Sources:
    - nvidia-devops Volume 04 Chapters 3-7 & Lab 01/02
    - AI Systems Performance Engineering Chapter 2 (pp. 20-35)
    """

    name: str
    architecture: str
    form_factor: str  # "PCIe", "SXM", or "Superchip"
    vram_gb: int
    mem_bw_gbps: float
    nvlink_bw_gbps: float  # 0.0 if no NVLink fabric support
    max_tdp_w: int
    supports_fp8: bool
    supports_fp4: bool
    supports_mig: bool
    media_engines: bool


ACCELERATOR_CATALOG: Dict[str, AcceleratorSpec] = {
    "T4": AcceleratorSpec(
        name="T4",
        architecture="Turing",
        form_factor="PCIe",
        vram_gb=16,
        mem_bw_gbps=320.0,
        nvlink_bw_gbps=0.0,
        max_tdp_w=70,
        supports_fp8=False,
        supports_fp4=False,
        supports_mig=False,
        media_engines=True,
    ),
    "L4": AcceleratorSpec(
        name="L4",
        architecture="Ada Lovelace",
        form_factor="PCIe",
        vram_gb=24,
        mem_bw_gbps=300.0,
        nvlink_bw_gbps=0.0,
        max_tdp_w=72,
        supports_fp8=True,
        supports_fp4=False,
        supports_mig=False,
        media_engines=True,
    ),
    "L40S": AcceleratorSpec(
        name="L40S",
        architecture="Ada Lovelace",
        form_factor="PCIe",
        vram_gb=48,
        mem_bw_gbps=864.0,
        nvlink_bw_gbps=0.0,
        max_tdp_w=350,
        supports_fp8=True,
        supports_fp4=False,
        supports_mig=False,
        media_engines=True,
    ),
    "A100-SXM4-80GB": AcceleratorSpec(
        name="A100-SXM4-80GB",
        architecture="Ampere",
        form_factor="SXM",
        vram_gb=80,
        mem_bw_gbps=2039.0,
        nvlink_bw_gbps=600.0,
        max_tdp_w=400,
        supports_fp8=False,
        supports_fp4=False,
        supports_mig=True,
        media_engines=False,
    ),
    "H100-PCIe-80GB": AcceleratorSpec(
        name="H100-PCIe-80GB",
        architecture="Hopper",
        form_factor="PCIe",
        vram_gb=80,
        mem_bw_gbps=2000.0,
        nvlink_bw_gbps=0.0,  # Only optional 2-way bridge, no 8-GPU NVSwitch fabric
        max_tdp_w=350,
        supports_fp8=True,
        supports_fp4=False,
        supports_mig=True,
        media_engines=False,
    ),
    "H100-SXM5-80GB": AcceleratorSpec(
        name="H100-SXM5-80GB",
        architecture="Hopper",
        form_factor="SXM",
        vram_gb=80,
        mem_bw_gbps=3350.0,
        nvlink_bw_gbps=900.0,
        max_tdp_w=700,
        supports_fp8=True,
        supports_fp4=False,
        supports_mig=True,
        media_engines=False,
    ),
    "H200-SXM-141GB": AcceleratorSpec(
        name="H200-SXM-141GB",
        architecture="Hopper",
        form_factor="SXM",
        vram_gb=141,
        mem_bw_gbps=4800.0,
        nvlink_bw_gbps=900.0,
        max_tdp_w=700,
        supports_fp8=True,
        supports_fp4=False,
        supports_mig=True,
        media_engines=False,
    ),
    "B200-SXM6-180GB": AcceleratorSpec(
        name="B200-SXM6-180GB",
        architecture="Blackwell",
        form_factor="SXM",
        vram_gb=180,
        mem_bw_gbps=8000.0,
        nvlink_bw_gbps=1800.0,
        max_tdp_w=1000,
        supports_fp8=True,
        supports_fp4=True,
        supports_mig=True,
        media_engines=False,
    ),
    "GB200-Superchip": AcceleratorSpec(
        name="GB200-Superchip",
        architecture="Grace Blackwell",
        form_factor="Superchip",
        vram_gb=384,  # 2x B200 GPUs combined HBM3e capacity in V4 Ch 6 / ASP Ch 2
        mem_bw_gbps=16000.0,
        nvlink_bw_gbps=3600.0,  # 2x 1.8 TB/s NVLink 5
        max_tdp_w=2700,
        supports_fp8=True,
        supports_fp4=True,
        supports_mig=True,
        media_engines=False,
    ),
}


@dataclass(frozen=True)
class DGXSystemSpec:
    """System-level specification for an NVIDIA DGX appliance.

    Sources:
    - nvidia-devops Volume 05 Chapters 2, 4, 5, 6, 7
    - AI Systems Performance Engineering Chapter 2 (pp. 26-34)
    - superpod-b200-dc (pp. 4-10)
    - superpod-gb300-ra (pp. 7-11)
    """

    model: str
    form_factor: str  # "node-air" or "rack-liquid"
    rack_units: int
    gpu_model: str
    gpu_count: int
    total_gpu_memory_gb: int
    aggregate_hbm_bw_tbps: float
    nvlink_gen: int
    per_gpu_nvlink_gbps: float
    aggregate_nvlink_tbps: float
    nvswitch_count: int
    compute_nics: int
    compute_nic_speed_gbps: int
    max_power_kw: float
    cooling: str  # "air", "liquid", or "hybrid-liquid-air"
    weight_lbs: float


DGX_SYSTEM_CATALOG: Dict[str, DGXSystemSpec] = {
    "DGX-A100": DGXSystemSpec(
        model="DGX-A100",
        form_factor="node-air",
        rack_units=6,
        gpu_model="A100-SXM4-80GB",
        gpu_count=8,
        total_gpu_memory_gb=640,
        aggregate_hbm_bw_tbps=16.3,
        nvlink_gen=3,
        per_gpu_nvlink_gbps=600.0,
        aggregate_nvlink_tbps=4.8,
        nvswitch_count=6,
        compute_nics=8,
        compute_nic_speed_gbps=200,
        max_power_kw=6.5,
        cooling="air",
        weight_lbs=271.5,
    ),
    "DGX-H100": DGXSystemSpec(
        model="DGX-H100",
        form_factor="node-air",
        rack_units=8,
        gpu_model="H100-SXM5-80GB",
        gpu_count=8,
        total_gpu_memory_gb=640,
        aggregate_hbm_bw_tbps=26.8,
        nvlink_gen=4,
        per_gpu_nvlink_gbps=900.0,
        aggregate_nvlink_tbps=7.2,
        nvswitch_count=4,
        compute_nics=8,
        compute_nic_speed_gbps=400,
        max_power_kw=10.2,
        cooling="air",
        weight_lbs=287.6,  # nearly 300 lbs (130 kg) per the DGX hardware notes
    ),
    "DGX-H200": DGXSystemSpec(
        model="DGX-H200",
        form_factor="node-air",
        rack_units=8,
        gpu_model="H200-SXM-141GB",
        gpu_count=8,
        total_gpu_memory_gb=1128,
        aggregate_hbm_bw_tbps=38.4,
        nvlink_gen=4,
        per_gpu_nvlink_gbps=900.0,
        aggregate_nvlink_tbps=7.2,
        nvswitch_count=4,
        compute_nics=8,
        compute_nic_speed_gbps=400,
        max_power_kw=10.2,
        cooling="air",
        weight_lbs=287.6,  # nearly 300 lbs (130 kg) per the DGX hardware notes
    ),
    "DGX-B200": DGXSystemSpec(
        model="DGX-B200",
        form_factor="node-air",
        rack_units=10,
        gpu_model="B200-SXM6-180GB",
        gpu_count=8,
        total_gpu_memory_gb=1440,
        aggregate_hbm_bw_tbps=64.0,
        nvlink_gen=5,
        per_gpu_nvlink_gbps=1800.0,
        aggregate_nvlink_tbps=14.4,
        nvswitch_count=4,
        compute_nics=8,
        compute_nic_speed_gbps=400,
        max_power_kw=14.3,
        cooling="air",
        weight_lbs=287.6,
    ),
    "DGX-GB200-NVL72": DGXSystemSpec(
        model="DGX-GB200-NVL72",
        form_factor="rack-liquid",
        rack_units=48,
        gpu_model="B200-SXM6-180GB",
        gpu_count=72,
        total_gpu_memory_gb=13824,  # 72 * 192 GB or 13,440 GB usable in ASP Ch 2
        aggregate_hbm_bw_tbps=576.0,
        nvlink_gen=5,
        per_gpu_nvlink_gbps=1800.0,
        aggregate_nvlink_tbps=130.0,
        nvswitch_count=18,  # 9 switch trays * 2 NVSwitch ASICs per tray
        compute_nics=72,
        compute_nic_speed_gbps=400,
        max_power_kw=120.0,
        cooling="liquid",
        weight_lbs=3000.0,
    ),
    "DGX-GB300-NVL72": DGXSystemSpec(
        model="DGX-GB300-NVL72",
        form_factor="rack-liquid",
        rack_units=48,
        gpu_model="B300",
        gpu_count=72,
        total_gpu_memory_gb=20736,  # 72 * 288 GB HBM3e
        aggregate_hbm_bw_tbps=576.0,
        nvlink_gen=5,
        per_gpu_nvlink_gbps=1800.0,
        aggregate_nvlink_tbps=130.0,
        nvswitch_count=18,  # 9 switch trays
        compute_nics=72,  # 18 compute trays * 4 ConnectX-8 800G NICs
        compute_nic_speed_gbps=800,
        max_power_kw=150.0,  # 1.2 MW per 8-rack SU (superpod-gb300-ra p. 5)
        cooling="hybrid-liquid-air",
        weight_lbs=3200.0,
    ),
}


def estimate_kv_cache_gb(
    num_layers: int,
    num_kv_heads: int,
    head_dim: int,
    bytes_per_element: int,
    seq_len: int,
    concurrent_users: int,
) -> float:
    """Calculate the KV-cache footprint in decimal GB.

    Per token, each layer stores one key vector and one value vector per KV head:
    bytes_per_token = 2 (K and V) * num_layers * num_kv_heads * head_dim * bytes_per_element.
    Llama-3-70B uses grouped-query attention (80 layers, 8 KV heads, head_dim 128):
    FP16 gives 327,680 bytes per token, so 4,096 tokens take 1.34 GB per user
    and 64 users take about 85.9 GB.
    """
    if min(num_layers, num_kv_heads, head_dim, bytes_per_element, seq_len, concurrent_users) <= 0:
        raise ValueError("All KV cache parameters must be positive integers.")
    bytes_per_token = 2 * num_layers * num_kv_heads * head_dim * bytes_per_element
    total_bytes = bytes_per_token * seq_len * concurrent_users
    return round(total_bytes / 1_000_000_000, 2)


def estimate_workload_vram_gb(
    params_billions: float,
    bytes_per_param: float,
    mode: str,
    kv_cache_gb: float = 0.0,
    training_multiplier: float = 5.0,
    inference_overhead: float = 1.2,
) -> Dict[str, float]:
    """Estimate total VRAM required for inference or training.

    Sources:
    - nvidia-devops Volume 04 Chapter 2 ("Step 2: Calculate the Memory Footprint")
    - nvidia-devops Volume 04 Lab 01 ("Step 1: Translate Business Requirements")
    Rules:
    - Inference weights = params_billions * bytes_per_param.
      Total inference VRAM = (weights + kv_cache_gb) * inference_overhead (default 1.2x).
    - Full training requires 4x to 6x parameter weight size (weights, FP32 master
      weights, Adam momentum/variance states, gradients, activations).
    """
    if params_billions <= 0 or bytes_per_param <= 0:
        raise ValueError("params_billions and bytes_per_param must be positive.")
    weights_gb = params_billions * bytes_per_param
    if mode == "inference":
        raw_gb = weights_gb + kv_cache_gb
        total_gb = round(raw_gb * inference_overhead, 2)
        return {
            "weights_gb": round(weights_gb, 2),
            "kv_cache_gb": round(kv_cache_gb, 2),
            "raw_gb": round(raw_gb, 2),
            "total_with_overhead_gb": total_gb,
        }
    if mode == "training":
        if not (4.0 <= training_multiplier <= 8.0):
            raise ValueError("training_multiplier must be between 4.0 and 8.0.")
        total_gb = round(weights_gb * training_multiplier, 2)
        return {
            "weights_gb": round(weights_gb, 2),
            "kv_cache_gb": 0.0,
            "raw_gb": round(weights_gb, 2),
            "total_with_overhead_gb": total_gb,
        }
    raise ValueError(f"Unsupported mode: {mode}")


def score_gpu_for_workload(
    gpu_name: str,
    gpus_per_node: int,
    required_vram_gb: float,
    rack_power_limit_kw: float,
    nodes_per_rack: int,
    host_system_overhead_w: int = 1000,
    require_nvlink: bool = False,
    require_fp8: bool = False,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    """Evaluate a GPU candidate using the Volume 04 Lab 01 Selection Scorecard.

    Source: nvidia-devops Volume 04 Lab 01 ("Build a GPU Selection Scorecard").
    Hard disqualifiers:
    1. Node power * nodes_per_rack > rack_power_limit_kw
    2. Total node VRAM < required_vram_gb (when single-node fit is required)
    3. require_nvlink is True and gpu.nvlink_bw_gbps == 0
    4. require_fp8 is True and not gpu.supports_fp8
    """
    if gpu_name not in ACCELERATOR_CATALOG:
        raise KeyError(f"Unknown GPU: {gpu_name}")
    spec = ACCELERATOR_CATALOG[gpu_name]
    w = weights or {
        "compute": 0.20,
        "memory_capacity": 0.25,
        "memory_bandwidth": 0.25,
        "interconnect": 0.15,
        "power_fit": 0.15,
    }

    node_vram_gb = spec.vram_gb * gpus_per_node
    node_power_kw = (spec.max_tdp_w * gpus_per_node + host_system_overhead_w) / 1000.0
    rack_power_kw = round(node_power_kw * nodes_per_rack, 2)

    disqualifiers: List[str] = []
    if rack_power_kw > rack_power_limit_kw:
        disqualifiers.append(
            f"rack_power_exceeded ({rack_power_kw} kW > {rack_power_limit_kw} kW limit)"
        )
    if node_vram_gb < required_vram_gb:
        disqualifiers.append(
            f"insufficient_node_vram ({node_vram_gb} GB < {required_vram_gb} GB required)"
        )
    if require_nvlink and spec.nvlink_bw_gbps <= 0.0:
        disqualifiers.append("missing_nvlink_fabric")
    if require_fp8 and not spec.supports_fp8:
        disqualifiers.append("missing_fp8_support")

    # Component scores (1.0 to 5.0 scale as in V4 Lab 01)
    cap_ratio = node_vram_gb / max(required_vram_gb, 1.0)
    cap_score = min(5.0, max(1.0, round(cap_ratio * 3.0, 2)))
    bw_score = min(5.0, max(1.0, round(spec.mem_bw_gbps / 800.0, 2)))
    ic_score = 5.0 if spec.nvlink_bw_gbps >= 900.0 else (4.0 if spec.nvlink_bw_gbps >= 600.0 else 1.5)
    comp_score = 5.0 if spec.supports_fp4 else (4.5 if spec.supports_fp8 and spec.form_factor != "PCIe" else (3.5 if spec.supports_fp8 else 2.0))
    pwr_margin = (rack_power_limit_kw - rack_power_kw) / max(rack_power_limit_kw, 1.0)
    pwr_score = 5.0 if pwr_margin >= 0.25 else (3.5 if pwr_margin >= 0.0 else 1.0)

    weighted = round(
        comp_score * w["compute"]
        + cap_score * w["memory_capacity"]
        + bw_score * w["memory_bandwidth"]
        + ic_score * w["interconnect"]
        + pwr_score * w["power_fit"],
        2,
    )

    return {
        "gpu": gpu_name,
        "disqualified": len(disqualifiers) > 0,
        "disqualifiers": disqualifiers,
        "node_vram_gb": node_vram_gb,
        "rack_power_kw": rack_power_kw,
        "weighted_score": 0.0 if disqualifiers else weighted,
    }


def evaluate_inference_shortlist(
    name: str,
    hourly_cost_usd: float,
    ttft_p99_ms: float,
    itl_p99_ms: float,
    total_tokens_per_sec: float,
    max_ttft_ms: float = 500.0,
    max_itl_ms: float = 30.0,
) -> Dict[str, object]:
    """Evaluate an inference benchmark candidate against latency SLOs and cost/1M tokens.

    Source: nvidia-devops Volume 04 Lab 02 ("Benchmark an Inference Accelerator Shortlist"):
    Cost per 1M tokens = (Hourly System Cost / (Total Tokens/sec * 3600)) * 1,000,000.
    """
    if hourly_cost_usd <= 0 or total_tokens_per_sec <= 0:
        raise ValueError("hourly_cost_usd and total_tokens_per_sec must be positive.")
    meets_ttft = ttft_p99_ms <= max_ttft_ms
    meets_itl = itl_p99_ms <= max_itl_ms
    meets_slo = meets_ttft and meets_itl
    cost_per_1m = round((hourly_cost_usd / (total_tokens_per_sec * 3600.0)) * 1_000_000.0, 4)
    return {
        "candidate": name,
        "meets_slo": meets_slo,
        "meets_ttft": meets_ttft,
        "meets_itl": meets_itl,
        "cost_per_1m_tokens_usd": cost_per_1m,
    }


def plan_dgx_rack_deployment(
    system_model: str,
    systems_per_rack: int,
    power_feeds_available: int = 2,
) -> Dict[str, object]:
    """Calculate rack power, heat load (BTU/hr), airflow (CFM), and PSU survival.

    Sources:
    - nvidia-devops Volume 05 Chapter 4 ("Power, Cooling, and Facility Readiness"):
      - DGX H100 = 10.2 kW max, ~34,800 BTU/hr per node, >1,000 CFM, 370 lbs (168 kg)
      - 6x 3.3 kW PSUs in 3+3 redundancy: survives loss of 3 PSUs or 1 entire power feed
        (remaining 3 PSUs run near 100% capacity: 3 * 3.3 kW = 9.9 kW ~ 10.2 kW peak).
    - superpod-b200-dc (pp. 4, 10):
      - DGX B200 = 14.3 kW max, 10 RU, >287.6 lbs (130 kg)
      - 2 systems/rack = 28.6 kW, 4,290 CFM (at 150 CFM/kW), 2x 380V 3-phase 32A
      - 4 systems/rack = 57.2 kW, 8,580 CFM (at 150 CFM/kW), 52U rack, 2x 415V 3-phase 60A
      - N = 2 power circuits, each rated to handle 50% of peak rack demand.
    - superpod-gb300-ra (pp. 5, 10-11):
      - DGX GB300 NVL72 rack has 8 power shelves; each shelf has 6x 5.5 kW PSUs
        delivering up to 33 kW.
    """
    if system_model not in DGX_SYSTEM_CATALOG:
        raise KeyError(f"Unknown DGX system: {system_model}")
    if systems_per_rack <= 0:
        raise ValueError("systems_per_rack must be >= 1.")

    spec = DGX_SYSTEM_CATALOG[system_model]
    rack_power_kw = round(spec.max_power_kw * systems_per_rack, 2)
    btu_per_hr = round(rack_power_kw * 3412.14)
    # 150 CFM per kW rule from superpod-b200-dc p. 10
    airflow_cfm = round(rack_power_kw * 150.0) if spec.cooling == "air" else 0
    total_rack_units = spec.rack_units * systems_per_rack
    total_equipment_weight_lbs = round(spec.weight_lbs * systems_per_rack, 1)

    warnings: List[str] = []
    if spec.form_factor == "rack-liquid" and systems_per_rack > 1:
        warnings.append("Rack-scale NVL72 occupies an entire 48U rack per system.")
    if system_model == "DGX-B200" and systems_per_rack == 4:
        warnings.append("4x DGX B200 (57.2 kW) requires a 52U rack and specialized extreme-density air cooling.")
    if spec.cooling == "air" and rack_power_kw > 60.0:
        warnings.append("Rack power exceeds 60 kW air-cooling ceiling; reduce nodes per rack or use liquid cooling.")
    if power_feeds_available < 2:
        warnings.append("Single power feed eliminates whip redundancy; dual feeds (A+B) required.")

    return {
        "system_model": system_model,
        "systems_per_rack": systems_per_rack,
        "rack_power_kw": rack_power_kw,
        "per_circuit_kw_n2": round(rack_power_kw / 2.0, 2),
        "heat_load_btu_hr": btu_per_hr,
        "estimated_airflow_cfm": airflow_cfm,
        "total_rack_units": total_rack_units,
        "equipment_weight_lbs": total_equipment_weight_lbs,
        "cooling_mode": spec.cooling,
        "requires_mechanical_lift": spec.weight_lbs >= 130.0,
        "warnings": warnings,
    }


def audit_dgx_node_baseline(snapshot: Dict[str, object]) -> Dict[str, object]:
    """Validate a DGX node against the Volume 05 Lab 01 & Lab 02 readiness checklist.

    Sources:
    - nvidia-devops Volume 05 Chapters 3, 5, 6
    - nvidia-devops Volume 05 Lab 01 ("Build a DGX Health Baseline")
    - nvidia-devops Volume 05 Lab 02 ("Validate DGX Data and Network Paths")
    """
    failures: List[str] = []
    expected_gpus = int(snapshot.get("expected_gpus", 8))
    detected_gpus = int(snapshot.get("detected_gpus", 0))
    if detected_gpus != expected_gpus:
        failures.append(f"gpu_count_mismatch ({detected_gpus}/{expected_gpus})")

    nvlink_links_per_gpu = int(snapshot.get("nvlink_links_per_gpu", 0))
    if nvlink_links_per_gpu != 18:
        failures.append(f"nvlink_degraded ({nvlink_links_per_gpu}/18 active links per GPU)")

    uncorrected_ecc = int(snapshot.get("uncorrected_ecc_errors", 0))
    if uncorrected_ecc > 0:
        failures.append(f"uncorrected_ecc_errors ({uncorrected_ecc})")

    active_compute_ib_ports = int(snapshot.get("active_compute_ib_ports", 0))
    expected_ib_ports = int(snapshot.get("expected_compute_ib_ports", 8))
    if active_compute_ib_ports != expected_ib_ports:
        failures.append(
            f"compute_fabric_links_down ({active_compute_ib_ports}/{expected_ib_ports} Active)"
        )

    if not bool(snapshot.get("raid_mounted", False)):
        failures.append("ephemeral_raid_not_mounted (/raid missing)")

    if bool(snapshot.get("sole_checkpoints_on_raid", False)):
        failures.append("unsafe_checkpoint_storage (/raid is ephemeral RAID 0; must replicate to shared PFS)")

    if not bool(snapshot.get("nvidia_peermem_loaded", False)):
        failures.append("nvidia_peermem_missing (GPUDirect RDMA disabled)")

    if not bool(snapshot.get("nvidia_fs_loaded", False)):
        failures.append("nvidia_fs_missing (GPUDirect Storage disabled; falls back to CPU bounce buffer)")

    if bool(snapshot.get("pcie_acs_enabled", False)):
        failures.append("pcie_acs_enabled (P2P traffic forced through CPU root complex)")

    if bool(snapshot.get("out_of_band_individual_fw_flash", False)):
        failures.append("uncoordinated_firmware_flash (must use unified DGX Firmware Container)")

    return {
        "ready_for_production": len(failures) == 0,
        "failure_count": len(failures),
        "failures": failures,
    }
