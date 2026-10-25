#!/usr/bin/env python3
"""Chapter 10.7 model: GPU Generations and Product Line: Ampere, Hopper, Blackwell; PCIe vs SXM.

Encodes the verifiable hardware specifications, silicon shifts, form-factor
power/cooling ceilings, inference video engines, KV-cache concurrency headroom,
and two-tier (pass/fail gate + weighted criteria) GPU selection scorecard from:
- AI Systems Performance Engineering (ASP) Chapter 2 (pp. 20-42):
  Blackwell B200 (208B transistors, 10 TB/s NV-HBI, 180 GB usable HBM3e @ 8 TB/s,
  FP4 Tensor Cores), B300 Blackwell Ultra (288 GB HBM3e), Grace Superchips
  (72-core Arm Neoverse V2, 480 GB LPDDR5X @ 500 GB/s, 900 GB/s NVLink-C2C),
  and NVIDIA future roadmap (Vera Rubin 2026, Rubin Ultra 2027, Feynman 2028).
- nvidia-devops Volume 04 Chapters 1-7 & Labs 01-02:
  GeForce vs RTX Pro vs Data Center (4 technical showstoppers + EULA legal showstopper),
  Volta V100 -> Ampere A100 -> Hopper H100/H200 -> Blackwell B200 design shifts,
  PCIe (350W, underclocked, bridge clips) vs SXM (700-1000W, HGX NVSwitch mesh),
  Inference tier (T4 -> L4 with 4x NVDEC/NVENC -> L40S with 733 TFLOPS FP8 but NO NVLink),
  Training heavy iron (H200 141GB HBM3e KV-cache doubling), and 5 Gate Criteria (G1-G5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


class GPUSelectionError(ValueError):
    """Raised when invalid hardware specifications or workload requirements are supplied."""


@dataclass(frozen=True)
class GPUSpec:
    name: str
    tier: str  # "GEFORCE", "RTX_PRO", "DATA_CENTER", "SUPERCHIP"
    architecture: str
    form_factor: str  # "PCIE", "SXM", "SUPERCHIP"
    vram_gb: float
    memory_type: str  # "GDDR6", "GDDR6X", "HBM2", "HBM2e", "HBM3", "HBM3e", "UNIFIED_LPDDR5X_HBM"
    memory_bandwidth_gbps: float
    max_tdp_watts: float
    has_ecc: bool
    has_nvlink: bool
    nvlink_bandwidth_gbps: float
    has_gpudirect_rdma: bool
    has_mig: bool
    has_fp8: bool
    has_fp4: bool
    has_nvenc_nvdec_engines: bool
    is_datacenter_eula_compliant: bool
    cooling_type: str  # "ACTIVE", "BLOWER", "PASSIVE_AIR", "PASSIVE_AIR_OR_DLC", "DLC_RACK"


GPU_CATALOG: Dict[str, GPUSpec] = {
    "RTX_4090": GPUSpec(
        name="NVIDIA GeForce RTX 4090",
        tier="GEFORCE",
        architecture="Ada Lovelace",
        form_factor="PCIE",
        vram_gb=24.0,
        memory_type="GDDR6X",
        memory_bandwidth_gbps=1008.0,
        max_tdp_watts=450.0,
        has_ecc=False,
        has_nvlink=False,
        nvlink_bandwidth_gbps=0.0,
        has_gpudirect_rdma=False,
        has_mig=False,
        has_fp8=True,
        has_fp4=False,
        has_nvenc_nvdec_engines=True,
        is_datacenter_eula_compliant=False,
        cooling_type="ACTIVE",
    ),
    "RTX_6000_ADA": GPUSpec(
        name="NVIDIA RTX 6000 Ada Generation",
        tier="RTX_PRO",
        architecture="Ada Lovelace",
        form_factor="PCIE",
        vram_gb=48.0,
        memory_type="GDDR6",
        memory_bandwidth_gbps=960.0,
        max_tdp_watts=300.0,
        has_ecc=True,
        has_nvlink=False,
        nvlink_bandwidth_gbps=0.0,
        has_gpudirect_rdma=True,
        has_mig=False,
        has_fp8=True,
        has_fp4=False,
        has_nvenc_nvdec_engines=True,
        is_datacenter_eula_compliant=True,
        cooling_type="BLOWER",
    ),
    "T4": GPUSpec(
        name="NVIDIA T4",
        tier="DATA_CENTER",
        architecture="Turing",
        form_factor="PCIE",
        vram_gb=16.0,
        memory_type="GDDR6",
        memory_bandwidth_gbps=320.0,
        max_tdp_watts=70.0,
        has_ecc=True,
        has_nvlink=False,
        nvlink_bandwidth_gbps=0.0,
        has_gpudirect_rdma=True,
        has_mig=False,
        has_fp8=False,
        has_fp4=False,
        has_nvenc_nvdec_engines=True,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR",
    ),
    "L4": GPUSpec(
        name="NVIDIA L4",
        tier="DATA_CENTER",
        architecture="Ada Lovelace",
        form_factor="PCIE",
        vram_gb=24.0,
        memory_type="GDDR6",
        memory_bandwidth_gbps=300.0,
        max_tdp_watts=72.0,
        has_ecc=True,
        has_nvlink=False,
        nvlink_bandwidth_gbps=0.0,
        has_gpudirect_rdma=True,
        has_mig=True,
        has_fp8=True,
        has_fp4=False,
        has_nvenc_nvdec_engines=True,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR",
    ),
    "L40S": GPUSpec(
        name="NVIDIA L40S",
        tier="DATA_CENTER",
        architecture="Ada Lovelace",
        form_factor="PCIE",
        vram_gb=48.0,
        memory_type="GDDR6",
        memory_bandwidth_gbps=864.0,
        max_tdp_watts=350.0,
        has_ecc=True,
        has_nvlink=False,
        nvlink_bandwidth_gbps=0.0,
        has_gpudirect_rdma=True,
        has_mig=False,
        has_fp8=True,
        has_fp4=False,
        has_nvenc_nvdec_engines=True,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR",
    ),
    "V100_SXM2_32GB": GPUSpec(
        name="NVIDIA V100 SXM2 32GB",
        tier="DATA_CENTER",
        architecture="Volta",
        form_factor="SXM",
        vram_gb=32.0,
        memory_type="HBM2",
        memory_bandwidth_gbps=900.0,
        max_tdp_watts=300.0,
        has_ecc=True,
        has_nvlink=True,
        nvlink_bandwidth_gbps=300.0,
        has_gpudirect_rdma=True,
        has_mig=False,
        has_fp8=False,
        has_fp4=False,
        has_nvenc_nvdec_engines=True,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR",
    ),
    "A100_SXM4_80GB": GPUSpec(
        name="NVIDIA A100 SXM4 80GB",
        tier="DATA_CENTER",
        architecture="Ampere",
        form_factor="SXM",
        vram_gb=80.0,
        memory_type="HBM2e",
        memory_bandwidth_gbps=2039.0,
        max_tdp_watts=400.0,
        has_ecc=True,
        has_nvlink=True,
        nvlink_bandwidth_gbps=600.0,
        has_gpudirect_rdma=True,
        has_mig=True,
        has_fp8=False,
        has_fp4=False,
        has_nvenc_nvdec_engines=False,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR",
    ),
    "H100_PCIE_80GB": GPUSpec(
        name="NVIDIA H100 PCIe 80GB",
        tier="DATA_CENTER",
        architecture="Hopper",
        form_factor="PCIE",
        vram_gb=80.0,
        memory_type="HBM2e",
        memory_bandwidth_gbps=2000.0,
        max_tdp_watts=350.0,
        has_ecc=True,
        has_nvlink=True,
        nvlink_bandwidth_gbps=600.0,  # 2-way bridge clip only
        has_gpudirect_rdma=True,
        has_mig=True,
        has_fp8=True,
        has_fp4=False,
        has_nvenc_nvdec_engines=False,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR",
    ),
    "H100_SXM5_80GB": GPUSpec(
        name="NVIDIA H100 SXM5 80GB",
        tier="DATA_CENTER",
        architecture="Hopper",
        form_factor="SXM",
        vram_gb=80.0,
        memory_type="HBM3",
        memory_bandwidth_gbps=3350.0,
        max_tdp_watts=700.0,
        has_ecc=True,
        has_nvlink=True,
        nvlink_bandwidth_gbps=900.0,
        has_gpudirect_rdma=True,
        has_mig=True,
        has_fp8=True,
        has_fp4=False,
        has_nvenc_nvdec_engines=False,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR_OR_DLC",
    ),
    "H200_SXM_141GB": GPUSpec(
        name="NVIDIA H200 SXM 141GB",
        tier="DATA_CENTER",
        architecture="Hopper",
        form_factor="SXM",
        vram_gb=141.0,
        memory_type="HBM3e",
        memory_bandwidth_gbps=4800.0,
        max_tdp_watts=700.0,
        has_ecc=True,
        has_nvlink=True,
        nvlink_bandwidth_gbps=900.0,
        has_gpudirect_rdma=True,
        has_mig=True,
        has_fp8=True,
        has_fp4=False,
        has_nvenc_nvdec_engines=False,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR_OR_DLC",
    ),
    "B200_SXM6_180GB": GPUSpec(
        name="NVIDIA Blackwell B200 SXM6 180GB",
        tier="DATA_CENTER",
        architecture="Blackwell",
        form_factor="SXM",
        vram_gb=180.0,  # 192 GB raw, 180 GB usable per ASP Ch 2 p. 28
        memory_type="HBM3e",
        memory_bandwidth_gbps=8000.0,
        max_tdp_watts=1000.0,
        has_ecc=True,
        has_nvlink=True,
        nvlink_bandwidth_gbps=1800.0,
        has_gpudirect_rdma=True,
        has_mig=True,
        has_fp8=True,
        has_fp4=True,
        has_nvenc_nvdec_engines=False,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR_OR_DLC",
    ),
    "B300_NVL_288GB": GPUSpec(
        name="NVIDIA Blackwell Ultra B300 NVL 288GB",
        tier="DATA_CENTER",
        architecture="Blackwell Ultra",
        form_factor="SXM",
        vram_gb=288.0,
        memory_type="HBM3e",
        memory_bandwidth_gbps=8000.0,
        max_tdp_watts=1000.0,
        has_ecc=True,
        has_nvlink=True,
        nvlink_bandwidth_gbps=1800.0,
        has_gpudirect_rdma=True,
        has_mig=True,
        has_fp8=True,
        has_fp4=True,
        has_nvenc_nvdec_engines=False,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR_OR_DLC",
    ),
    "GH200_480GB_96GB": GPUSpec(
        name="NVIDIA Grace Hopper GH200 576GB",
        tier="SUPERCHIP",
        architecture="Grace Hopper",
        form_factor="SUPERCHIP",
        vram_gb=576.0,  # 480 GB LPDDR5X + 96 GB HBM3
        memory_type="UNIFIED_LPDDR5X_HBM",
        memory_bandwidth_gbps=4000.0,  # 3.35 TB/s HBM3 + ~500 GB/s LPDDR5X
        max_tdp_watts=1000.0,
        has_ecc=True,
        has_nvlink=True,
        nvlink_bandwidth_gbps=900.0,  # NVLink-C2C
        has_gpudirect_rdma=True,
        has_mig=True,
        has_fp8=True,
        has_fp4=False,
        has_nvenc_nvdec_engines=False,
        is_datacenter_eula_compliant=True,
        cooling_type="PASSIVE_AIR_OR_DLC",
    ),
}


def calc_inference_vram_and_concurrency(
    model_params_billions: float,
    precision_bytes: float = 2.0,  # 2.0 = FP16/BF16, 1.0 = FP8, 0.5 = FP4
    num_layers: int = 80,
    num_heads: int = 128,
    bytes_per_token: int = 8,
    context_tokens: int = 8192,
    concurrent_users: int = 64,
    vram_overhead_factor: float = 1.2,
) -> Dict[str, float]:
    """Calculate inference model weight, KV cache, and required VRAM per V4 Ch 1 & Ch 2."""
    if model_params_billions <= 0 or precision_bytes <= 0 or context_tokens <= 0 or concurrent_users <= 0:
        raise GPUSelectionError("Model parameters, precision bytes, context, and users must be positive")

    weight_gb = model_params_billions * precision_bytes
    # V4 Ch 1 formula: bytes_per_token (8) * 2 (K and V) * num_layers * num_heads * seq_len
    bytes_per_user = bytes_per_token * 2 * num_layers * num_heads * context_tokens
    kv_cache_per_user_gb = round(bytes_per_user / 1_000_000_000, 2)  # 1.34 GB
    total_kv_cache_gb = round((bytes_per_user * concurrent_users) / 1_000_000_000, 2)  # 85.90 GB

    total_required_gb = round((weight_gb + total_kv_cache_gb) * vram_overhead_factor, 2)

    return {
        "model_params_billions": round(model_params_billions, 1),
        "precision_bytes": precision_bytes,
        "weight_gb": round(weight_gb, 2),
        "kv_cache_per_user_gb": kv_cache_per_user_gb,
        "total_kv_cache_gb": total_kv_cache_gb,
        "total_required_vram_gb": total_required_gb,
    }


def evaluate_gpu_selection_gates_and_scorecard(
    candidate_key: str,
    workload_type: str,  # "LLM_PRETRAINING", "LLM_INFERENCE", "COMPUTER_VISION_VIDEO", "RECSYS_EMBEDDINGS"
    target_environment: str = "COMMERCIAL_DATACENTER",  # "COMMERCIAL_DATACENTER", "RETAIL_EDGE"
    required_vram_gb: float = 140.0,
    gpu_count: int = 8,
    rack_power_ceiling_kw: float = 40.0,
    requires_tensor_parallelism: bool = False,
    requires_hardware_video_transcode: bool = False,
    weights_profile: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    """Evaluate candidate GPU across 5 Gate Criteria (G1-G5) and weighted scorecard per V4 Lab 01.

    Mandatory Gates (Pass/Fail):
    - G1: Software stack & EULA support (GeForce fails in commercial datacenter).
    - G2: Usable memory capacity (total candidate VRAM >= required_vram_gb).
    - G3: Power & cooling fit (cluster power <= rack ceiling; active cooling fails in standard 4U datacenter).
    - G4: Enterprise vendor support model (requires passive cooling, ECC memory, BMC/IPMI).
    - G5: Deployment platform compatibility (requires NVLink if Tensor Parallelism > 1 or pretraining;
      requires NVDEC/NVENC if video transcode required).
    """
    if candidate_key not in GPU_CATALOG:
        raise GPUSelectionError(f"Candidate {candidate_key} not in catalog")
    if gpu_count <= 0 or required_vram_gb <= 0 or rack_power_ceiling_kw <= 0:
        raise GPUSelectionError("gpu_count, required_vram_gb, and rack_power_ceiling_kw must be positive")

    gpu = GPU_CATALOG[candidate_key]
    total_vram_gb = gpu.vram_gb * gpu_count
    # Add 1.5 kW for dual host CPUs, motherboard, and NICs in an enterprise server
    server_power_kw = (gpu.max_tdp_watts * gpu_count + 1500.0) / 1000.0

    gate_results: Dict[str, bool] = {}
    gate_failures: List[str] = []

    # G1: Software & EULA
    if target_environment == "COMMERCIAL_DATACENTER" and not gpu.is_datacenter_eula_compliant:
        gate_results["G1_SOFTWARE_EULA"] = False
        gate_failures.append("Fails G1: GeForce driver EULA prohibits commercial datacenter deployment.")
    else:
        gate_results["G1_SOFTWARE_EULA"] = True

    # G2: Usable memory
    if total_vram_gb < required_vram_gb:
        gate_results["G2_USABLE_MEMORY"] = False
        gate_failures.append(
            f"Fails G2: Total VRAM {total_vram_gb:.1f} GB < required {required_vram_gb:.1f} GB."
        )
    else:
        gate_results["G2_USABLE_MEMORY"] = True

    # G3: Power & Cooling
    if server_power_kw > rack_power_ceiling_kw:
        gate_results["G3_POWER_COOLING"] = False
        gate_failures.append(
            f"Fails G3: Server power {server_power_kw:.1f} kW exceeds rack ceiling {rack_power_ceiling_kw:.1f} kW."
        )
    elif target_environment == "COMMERCIAL_DATACENTER" and gpu.cooling_type == "ACTIVE":
        gate_results["G3_POWER_COOLING"] = False
        gate_failures.append(
            "Fails G3: Active consumer fan cooling is incompatible with linear front-to-back datacenter airflow."
        )
    elif target_environment == "RETAIL_EDGE" and gpu.max_tdp_watts > 100.0:
        gate_results["G3_POWER_COOLING"] = False
        gate_failures.append(
            f"Fails G3: GPU TDP {gpu.max_tdp_watts}W exceeds retail store 120V wall/rack power limit (max 75-100W/GPU)."
        )
    else:
        gate_results["G3_POWER_COOLING"] = True

    # G4: Enterprise vendor support & ECC
    if not gpu.has_ecc:
        gate_results["G4_ENTERPRISE_SUPPORT"] = False
        gate_failures.append("Fails G4: Lacks ECC memory (unacceptable silent bit-flip risk).")
    else:
        gate_results["G4_ENTERPRISE_SUPPORT"] = True

    # G5: Platform compatibility & Interconnect
    if (requires_tensor_parallelism or workload_type == "LLM_PRETRAINING") and not gpu.has_nvlink:
        gate_results["G5_PLATFORM_COMPAT"] = False
        gate_failures.append(
            "Fails G5: Workload requires Tensor Parallelism / Pretraining, but candidate lacks NVLink (e.g. L40S or PCIe)."
        )
    elif requires_hardware_video_transcode and not gpu.has_nvenc_nvdec_engines:
        gate_results["G5_PLATFORM_COMPAT"] = False
        gate_failures.append(
            "Fails G5: Workload requires hardware video decode/encode, but candidate lacks NVENC/NVDEC engines (e.g. H100 SXM)."
        )
    else:
        gate_results["G5_PLATFORM_COMPAT"] = True

    passed_all_gates = all(gate_results.values())

    # Weighted Scorecard (1-5 scale) per V4 Lab 01 Step 3
    scores: Dict[str, float] = {}
    if passed_all_gates:
        # Default weights: Headroom (20), Latency/BW (20), Throughput/Math (15), Power Fit (15), K8s Sharing (10), Observability (10), Lifecycle Cost (10)
        w = weights_profile or {
            "headroom": 20.0,
            "bandwidth": 20.0,
            "throughput": 15.0,
            "power_fit": 15.0,
            "k8s_sharing": 10.0,
            "observability": 10.0,
            "cost_fit": 10.0,
        }

        # 1. Headroom score
        headroom_ratio = total_vram_gb / required_vram_gb
        s_headroom = min(5.0, max(1.0, 3.0 + (headroom_ratio - 1.0) * 2.0))

        # 2. Bandwidth score (normalized to 800 GB/s: 800 GB/s = 1.0, 3.35 TB/s HBM3 = 4.2, 8 TB/s = 5.0)
        s_bw = min(5.0, max(1.0, round(gpu.memory_bandwidth_gbps / 800.0, 2)))

        # 3. Throughput score (FP8/FP4 support)
        s_throughput = 5.0 if gpu.has_fp4 else (4.0 if gpu.has_fp8 else 2.5)

        # 4. Power fit score (lower power fraction of rack ceiling scores higher)
        pwr_fraction = server_power_kw / rack_power_ceiling_kw
        s_pwr = min(5.0, max(1.0, 5.0 - pwr_fraction * 3.0))

        # 5. K8s sharing (MIG support)
        s_k8s = 5.0 if gpu.has_mig else 3.0

        # 6. Observability
        s_obs = 5.0 if gpu.tier in {"DATA_CENTER", "SUPERCHIP"} else 3.0

        # 7. Lifecycle cost fit
        s_cost = 5.0 if gpu.max_tdp_watts <= 100.0 else (4.0 if gpu.form_factor == "PCIE" else 3.0)

        raw_score = (
            s_headroom * w["headroom"]
            + s_bw * w["bandwidth"]
            + s_throughput * w["throughput"]
            + s_pwr * w["power_fit"]
            + s_k8s * w["k8s_sharing"]
            + s_obs * w["observability"]
            + s_cost * w["cost_fit"]
        ) / 100.0

        scores = {
            "headroom_score": round(s_headroom, 1),
            "bandwidth_score": round(s_bw, 1),
            "throughput_score": round(s_throughput, 1),
            "power_score": round(s_pwr, 1),
            "k8s_score": round(s_k8s, 1),
            "weighted_score": round(raw_score, 2),
        }

    return {
        "candidate": candidate_key,
        "gpu_name": gpu.name,
        "total_vram_gb": total_vram_gb,
        "server_power_kw": round(server_power_kw, 2),
        "passed_all_gates": passed_all_gates,
        "gate_results": gate_results,
        "gate_failures": gate_failures,
        "scores": scores,
    }
