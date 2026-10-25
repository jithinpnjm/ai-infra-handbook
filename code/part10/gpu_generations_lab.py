#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.7: GPU Generations and Product Line: Ampere, Hopper, Blackwell; PCIe vs SXM."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gpu_generations import (
    GPU_CATALOG,
    GPUSelectionError,
    calc_inference_vram_and_concurrency,
    evaluate_gpu_selection_gates_and_scorecard,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main() -> int:
    print("=== Chapter 10.7 Lab: GPU Generations & Product Line (Ampere, Hopper, Blackwell; PCIe vs SXM) ===")

    # 1. Hardware Catalog Specifications (V4 Ch 1-7 & ASP Ch 2)
    rtx4090 = GPU_CATALOG["RTX_4090"]
    l4 = GPU_CATALOG["L4"]
    l40s = GPU_CATALOG["L40S"]
    v100 = GPU_CATALOG["V100_SXM2_32GB"]
    a100 = GPU_CATALOG["A100_SXM4_80GB"]
    h100_pcie = GPU_CATALOG["H100_PCIE_80GB"]
    h100_sxm = GPU_CATALOG["H100_SXM5_80GB"]
    h200_sxm = GPU_CATALOG["H200_SXM_141GB"]
    b200 = GPU_CATALOG["B200_SXM6_180GB"]
    b300 = GPU_CATALOG["B300_NVL_288GB"]
    gh200 = GPU_CATALOG["GH200_480GB_96GB"]

    check(
        "V4 Ch1: RTX 4090 is GEFORCE tier, active-cooled, lacks ECC, lacks NVLink, and is not datacenter EULA compliant",
        rtx4090.tier == "GEFORCE"
        and rtx4090.has_ecc is False
        and rtx4090.has_nvlink is False
        and rtx4090.is_datacenter_eula_compliant is False,
    )
    check(
        "V4 Ch5: L4 is 72W single-slot PCIe, 24GB GDDR6, FP8, with hardware NVENC/NVDEC video engines",
        l4.max_tdp_watts == 72.0
        and l4.vram_gb == 24.0
        and l4.has_fp8 is True
        and l4.has_nvenc_nvdec_engines is True,
    )
    check(
        "V4 Ch5: L40S is 350W PCIe, 48GB GDDR6, 864 GB/s, FP8, but physically lacks NVLink (has_nvlink is False)",
        l40s.max_tdp_watts == 350.0
        and l40s.vram_gb == 48.0
        and l40s.has_nvlink is False,
    )
    check(
        "V4 Ch3 & Ch6: Volta V100 was 300W (FP16); Ampere A100 added MIG and 80GB HBM2e at 2.0 TB/s (400W)",
        v100.max_tdp_watts == 300.0
        and a100.has_mig is True
        and a100.vram_gb == 80.0
        and a100.memory_bandwidth_gbps > 2000.0,
    )
    check(
        "V4 Ch4: H100 PCIe is capped at 350W and 2.0 TB/s HBM2e vs H100 SXM5 at 700W and 3.35 TB/s HBM3 (900 GB/s NVLink 4)",
        h100_pcie.max_tdp_watts == 350.0
        and h100_pcie.memory_bandwidth_gbps == 2000.0
        and h100_sxm.max_tdp_watts == 700.0
        and h100_sxm.memory_bandwidth_gbps == 3350.0
        and h100_sxm.nvlink_bandwidth_gbps == 900.0,
    )
    check(
        "V4 Ch6: H200 SXM increases memory to 141GB HBM3e at 4.8 TB/s within the same 700W envelope as H100 SXM",
        h200_sxm.vram_gb == 141.0
        and h200_sxm.memory_bandwidth_gbps == 4800.0
        and h200_sxm.max_tdp_watts == 700.0,
    )
    check(
        "ASP Ch2 p.28: Blackwell B200 SXM has 180 GB usable HBM3e at 8.0 TB/s, FP4 Tensor Cores, and 1,800 GB/s NVLink 5",
        b200.vram_gb == 180.0
        and b200.memory_bandwidth_gbps == 8000.0
        and b200.has_fp4 is True
        and b200.nvlink_bandwidth_gbps == 1800.0,
    )
    check(
        "ASP Ch2 p.38: Blackwell Ultra B300 upgrades memory to 288GB HBM3e",
        b300.vram_gb == 288.0 and b300.has_fp4 is True,
    )
    check(
        "V4 Ch7 & ASP Ch2: GH200 provides 576GB unified memory (480GB LPDDR5X + 96GB HBM3) over 900 GB/s NVLink-C2C",
        gh200.vram_gb == 576.0 and gh200.nvlink_bandwidth_gbps == 900.0,
    )

    # 2. Worked VRAM & KV Cache Concurrency (V4 Ch 1 & Ch 2)
    sz_70b_fp16 = calc_inference_vram_and_concurrency(
        model_params_billions=70.0,
        precision_bytes=2.0,
        context_tokens=8192,
        concurrent_users=64,
    )
    check(
        "V4 Ch1: 70B FP16 weights require 140.0 GB; 64 concurrent users at 8k context require ~85.9 GB KV cache",
        sz_70b_fp16["weight_gb"] == 140.0
        and abs(sz_70b_fp16["total_kv_cache_gb"] - 85.9) < 0.2,
    )
    check(
        "V4 Ch1: Total 70B FP16 + 64 users KV cache with 1.2x overhead == ~271 GB VRAM",
        abs(sz_70b_fp16["total_required_vram_gb"] - 271.08) < 0.2,
    )

    # 3. Gate G1: Software EULA Gate (V4 Ch 1 Customer Scenario)
    g1_eval = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="RTX_4090",
        workload_type="LLM_INFERENCE",
        target_environment="COMMERCIAL_DATACENTER",
        required_vram_gb=48.0,
        gpu_count=2,
    )
    check(
        "V4 Ch1 Customer Scenario: RTX 4090 fails G1 EULA and G3 active-cooling in commercial datacenter",
        g1_eval["passed_all_gates"] is False
        and g1_eval["gate_results"]["G1_SOFTWARE_EULA"] is False
        and g1_eval["gate_results"]["G3_POWER_COOLING"] is False,
    )

    # 4. Gate G3: Edge Power Ceiling Gate (V4 Ch 2 Customer Scenario)
    edge_h100 = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="H100_SXM5_80GB",
        workload_type="COMPUTER_VISION_VIDEO",
        target_environment="RETAIL_EDGE",
        required_vram_gb=32.0,
        gpu_count=4,
    )
    check(
        "V4 Ch2 Customer Scenario: 4x H100 (700W/GPU) fails G3 power ceiling at retail store edge",
        edge_h100["passed_all_gates"] is False
        and edge_h100["gate_results"]["G3_POWER_COOLING"] is False,
    )

    edge_l4 = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="L4",
        workload_type="COMPUTER_VISION_VIDEO",
        target_environment="RETAIL_EDGE",
        required_vram_gb=32.0,
        gpu_count=4,
        requires_hardware_video_transcode=True,
    )
    check(
        "V4 Ch2 Customer Scenario: 4x L4 (72W/GPU, NVENC/NVDEC) passes all gates at retail store edge",
        edge_l4["passed_all_gates"] is True,
    )

    # 5. Gate G5: NVLink Requirement for Pretraining / Tensor Parallelism (V4 Ch 4 & Ch 5)
    train_l40s = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="L40S",
        workload_type="LLM_PRETRAINING",
        target_environment="COMMERCIAL_DATACENTER",
        required_vram_gb=300.0,
        gpu_count=8,
        requires_tensor_parallelism=True,
    )
    check(
        "V4 Ch4 & Ch5: L40S fails G5 platform compatibility for LLM Pretraining / Tensor Parallelism (no NVLink)",
        train_l40s["passed_all_gates"] is False
        and train_l40s["gate_results"]["G5_PLATFORM_COMPAT"] is False,
    )

    train_h100_sxm = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="H100_SXM5_80GB",
        workload_type="LLM_PRETRAINING",
        target_environment="COMMERCIAL_DATACENTER",
        required_vram_gb=500.0,
        gpu_count=8,
        requires_tensor_parallelism=True,
        rack_power_ceiling_kw=40.0,
    )
    check(
        "V4 Ch2 & Ch6: 8x H100 SXM (640GB, NVSwitch 900 GB/s) passes all gates for LLM Pretraining",
        train_h100_sxm["passed_all_gates"] is True
        and train_h100_sxm["scores"]["weighted_score"] >= 3.8,
    )

    # 6. Gate G5: Video Transcode Engines (V4 Ch 5 Media Pipeline Scenario)
    media_a100 = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="A100_SXM4_80GB",
        workload_type="COMPUTER_VISION_VIDEO",
        target_environment="COMMERCIAL_DATACENTER",
        required_vram_gb=40.0,
        gpu_count=2,
        requires_hardware_video_transcode=True,
    )
    check(
        "V4 Ch5 Customer Scenario: A100 fails G5 for video transcode workload due to missing NVENC engines",
        media_a100["passed_all_gates"] is False
        and media_a100["gate_results"]["G5_PLATFORM_COMPAT"] is False,
    )

    # 7. Gate G2: Usable Memory Headroom & H200 KV-Cache Concurrency (V4 Ch 6 Customer Scenario)
    h100_kv = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="H100_SXM5_80GB",
        workload_type="LLM_INFERENCE",
        target_environment="COMMERCIAL_DATACENTER",
        required_vram_gb=1000.0,  # Massive concurrent KV cache requirement
        gpu_count=8,
        rack_power_ceiling_kw=40.0,
    )
    check(
        "V4 Ch6 Customer Scenario: 8x H100 (640GB) fails G2 memory capacity when required VRAM is 1,000 GB",
        h100_kv["passed_all_gates"] is False
        and h100_kv["gate_results"]["G2_USABLE_MEMORY"] is False,
    )

    h200_kv = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="H200_SXM_141GB",
        workload_type="LLM_INFERENCE",
        target_environment="COMMERCIAL_DATACENTER",
        required_vram_gb=1000.0,
        gpu_count=8,
        rack_power_ceiling_kw=40.0,
    )
    check(
        "V4 Ch6 Customer Scenario: 8x H200 (1,128GB) passes G2 memory capacity and scores high headroom",
        h200_kv["passed_all_gates"] is True
        and h200_kv["scores"]["headroom_score"] >= 3.0,
    )

    # 8. Single-GPU Serving on L40S (V4 Ch 5)
    l40s_single = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="L40S",
        workload_type="LLM_INFERENCE",
        target_environment="COMMERCIAL_DATACENTER",
        required_vram_gb=32.0,
        gpu_count=1,
        requires_tensor_parallelism=False,
    )
    check(
        "V4 Ch5: Single L40S passes all gates for model that fits in 48GB without Tensor Parallelism",
        l40s_single["passed_all_gates"] is True,
    )

    # 9. Workstation Tier: RTX 6000 Ada (V4 Ch 1)
    rtx6000 = GPU_CATALOG["RTX_6000_ADA"]
    check(
        "V4 Ch1: RTX 6000 Ada is RTX_PRO tier, blower-cooled, 48GB ECC GDDR6, and datacenter EULA compliant",
        rtx6000.tier == "RTX_PRO"
        and rtx6000.cooling_type == "BLOWER"
        and rtx6000.vram_gb == 48.0
        and rtx6000.has_ecc is True
        and rtx6000.is_datacenter_eula_compliant is True,
    )

    # 10. Superchip Coherent EGM Recommendation (V4 Ch 7 Quantitative Hedge Fund Scenario)
    gh200_eval = evaluate_gpu_selection_gates_and_scorecard(
        candidate_key="GH200_480GB_96GB",
        workload_type="RECSYS_EMBEDDINGS",
        target_environment="COMMERCIAL_DATACENTER",
        required_vram_gb=400.0,
        gpu_count=1,
    )
    check(
        "V4 Ch7 Customer Scenario: Single GH200 (576GB unified memory) satisfies 400GB graph/recsys dataset on 1 node",
        gh200_eval["passed_all_gates"] is True,
    )

    # 11. Error Handling
    try:
        evaluate_gpu_selection_gates_and_scorecard("INVALID_GPU", "LLM_INFERENCE")
        check("Rejects invalid GPU candidate key", False)
    except GPUSelectionError:
        check("Rejects invalid GPU candidate key", True)

    try:
        evaluate_gpu_selection_gates_and_scorecard("L4", "LLM_INFERENCE", required_vram_gb=0.0)
        check("Rejects non-positive required_vram_gb", False)
    except GPUSelectionError:
        check("Rejects non-positive required_vram_gb", True)

    try:
        calc_inference_vram_and_concurrency(0.0)
        check("Rejects non-positive model_params_billions", False)
    except GPUSelectionError:
        check("Rejects non-positive model_params_billions", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
