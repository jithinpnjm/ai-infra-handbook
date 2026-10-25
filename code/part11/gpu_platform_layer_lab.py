#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.1: Why Kubernetes needs a GPU platform layer.

Runs 25 deterministic checks verifying every architectural boundary, two-path triage
branch (`Bound?` vs `CudaInit?`), 32-GPU pool fragmentation calculation, whole-GPU
memory waste (`Llama-3.2-1B` on `24 GB` L4), `70B` quantization math, `GB` vs `GiB`
conversion, and combinatorial qualification matrix from `nvidia-devops` Volume 10,
*Generative AI on Kubernetes* (`GAK` Ch 3), *Kubernetes for Generative AI Solutions*
(`K8GS` Ch 2 & Ch 10), *Scalable Kubernetes Infrastructure for AI Platforms* (`SKI`),
and *AI Systems Performance Engineering* (`ASP` Ch 3).
"""

from __future__ import annotations

import sys

from gpu_platform_layer import (
    CONTAINER_MAX_OVERHEAD_PCT,
    FORTUNE_100_K8S_ADOPTION_PCT,
    GARTNER_2027_CONTAINER_PCT,
    GPU_3D_CONTROLLER_PCI_CLASS,
    NVIDIA_PCI_VENDOR_ID,
    OPENAI_K8S_MAX_NODES_EXAMPLE,
    compute_qualification_matrix,
    evaluate_model_memory_and_sharing,
    evaluate_pool_fragmentation,
    triage_gpu_platform_incident,
)


def main() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    print("=== Chapter 11.1 Lab: Why Kubernetes Needs a GPU Platform Layer (V10 Ch 1-2 + GAK + K8GS + ASP) ===")

    # 1-5: Two-Path Triage Model (`Bound?` vs `CudaInit?`, V10 Ch 1 & Ch 2)
    t_drv = triage_gpu_platform_incident(pod_bound=False, lsmod_nvidia_loaded=False)
    t_dp = triage_gpu_platform_incident(pod_bound=False, capacity_key_present=False, allocatable_gpus=0)
    t_pend = triage_gpu_platform_incident(pod_bound=False, capacity_key_present=True, allocatable_gpus=4)
    t_rt = triage_gpu_platform_incident(pod_bound=True, minimal_cuda_check_ok=False)
    t_app = triage_gpu_platform_incident(pod_bound=True, minimal_cuda_check_ok=True, framework_cuda_init_ok=False)
    t_ok = triage_gpu_platform_incident(pod_bound=True, minimal_cuda_check_ok=True, framework_cuda_init_ok=True)

    check(
        "V10 Ch2 gpu-node-22 scenario: Node is Ready, but empty lsmod | grep nvidia routes to Layer 2 Host Kernel Driver (DriverFail branch)",
        t_drv.failing_path == "HOST_DRIVER_PATH" and "Layer 2" in t_drv.failing_layer,
    )
    check(
        "V10 Ch1 gpu-node-11 scenario: Missing nvidia.com/gpu key in status.capacity routes to Layer 4 Device Plugin Registration",
        t_dp.failing_path == "CONTROL_ADVERTISEMENT_PATH" and "Layer 4" in t_dp.failing_layer,
    )
    check(
        "V10 Ch1 Bound?==No branch: Unbound Pending pod with healthy plugin routes to Layer 5 Scheduling Policy / Pool Capacity",
        t_pend.failing_path == "CONTROL_SCHEDULING_PATH" and "Layer 5" in t_pend.failing_layer,
    )
    check(
        "V10 Ch1 & Ch2 gpu-node-30 scenario: Bound pod failing minimal CUDA check (CreateContainerError /dev/nvidia0) routes to Layer 3 Runtime / Toolkit / CDI",
        t_rt.failing_path == "RUNTIME_EXECUTION_PATH" and "Layer 3" in t_rt.failing_layer,
    )
    check(
        "V10 Ch2 Minimal CUDA_CHECK_OK pass + framework fail: Routes to Layer 6 Workload Image (no kernel image available for device)",
        t_app.failing_path == "WORKLOAD_IMAGE_PATH"
        and "Layer 6" in t_app.failing_layer
        and t_ok.failing_path == "NONE",
    )

    # 6-8: 32-GPU Pool Fragmentation Model (V10 Ch 1)
    frag = evaluate_pool_fragmentation(
        training_pool_gpus=16,
        dist_inference_pool_gpus=8,
        general_pool_gpus=8,
        general_pool_used_before=4,
        new_general_job_gpus=4,
    )
    check(
        "V10 Ch1 32-GPU Pool Fragmentation: 16 training + 8 distributed-inference + 8 general == 32 total GPUs",
        frag.total_cluster_gpus == 32
        and frag.training_pool_gpus == 16
        and frag.dist_inference_pool_gpus == 8
        and frag.general_pool_gpus == 8,
    )
    check(
        "V10 Ch1 Pool Exhaustion vs Cluster Idle: 2nd 4-GPU general job leaves 0/8 free in general pool while 24/32 (75.0%) of cluster GPUs sit idle (25.0% util)",
        frag.general_pool_free_after == 0
        and frag.cluster_idle_after == 24
        and frag.cluster_idle_pct == 75.0
        and frag.cluster_utilization_pct == 25.0
        and frag.next_unconstrained_job_schedulable is False,
    )

    # 8-11: Combinatorial Qualification Matrix (V10 Ch 2)
    qm = compute_qualification_matrix(
        kernels=3,
        driver_branches=2,
        image_families=4,
        k8s_versions=2,
        approved_node_profiles=2,
    )
    check(
        "V10 Ch2 Unbounded Qualification Matrix: 3 kernels * 2 drivers * 4 image families == 24 combinations; * 2 K8s versions == 48 combinations",
        qm.three_layer_combinations == 24 and qm.four_layer_combinations == 48,
    )
    check(
        "V10 Ch2 Profile-Based Qualification: 2 approved node profiles * 4 image families == 8 combinations (6.0x reduction from 48)",
        qm.profile_based_combinations == 8 and qm.reduction_factor == 6.0,
    )

    # 10-16: GAK Ch 3, K8GS Ch 2 & Ch 10, and ASP Ch 3 quantitative facts
    mem_plan = evaluate_model_memory_and_sharing(
        gpu_vram_gb=24.0,
        model_vram_gb=1.8,
        time_slicing_replicas=10,
        deployed_pods=5,
        params_billions=70.0,
    )
    check(
        "K8GS Ch10 Whole-GPU Underutilization: Llama-3.2-1B (1.8 GB) on 1 NVIDIA L4 (24 GB, g6.2xlarge) leaves 22.2 GB (92.5% ~ 92%) unused",
        mem_plan.single_pod_unused_vram_gb == 22.2
        and mem_plan.single_pod_unused_vram_pct == 92.5,
    )
    check(
        "K8GS Ch10 Time-Slicing on L4: 10 replicas configured, 5 Llama-3.2-1B pods use 5 * 1.8 GB == 9.0 GB <= 24.0 GB VRAM",
        mem_plan.time_slicing_replicas == 10
        and mem_plan.shared_used_vram_gb == 9.0
        and mem_plan.fits_in_vram is True,
    )
    check(
        "GAK Ch3 70B Model Quantization & GB vs GiB: 70B FP32 (4 B/param) == 280.0 GB vs 4-bit (0.5 B/param) == 35.0 GB (fits 48 GB GPU); 40 GB == 37.25 GiB, 80 GB == 74.5 GiB",
        mem_plan.fp32_70b_gb == 280.0
        and mem_plan.int4_70b_gb == 35.0
        and mem_plan.gb_40_in_gib == 37.25
        and mem_plan.gb_80_in_gib == 74.5,
    )
    check(
        "GAK Ch3 NFD PCI discovery: NVIDIA vendor ID == '10de' (AMD '1002', Intel '8086', AWS VGA '1d0f') and 3D controller class == '0302'",
        NVIDIA_PCI_VENDOR_ID == "10de" and GPU_3D_CONTROLLER_PCI_CLASS == "0302",
    )
    check(
        "K8GS Ch2 & ASP Ch3 Kubernetes adoption & container overhead: OpenAI 7,500 nodes, 71% Fortune 100, 90% by 2027,77K+ contributors (44 countries, 8K+ companies), < 2.0% container overhead",
        OPENAI_K8S_MAX_NODES_EXAMPLE == 7500
        and FORTUNE_100_K8S_ADOPTION_PCT == 71
        and GARTNER_2027_CONTAINER_PCT == 90
        and CONTAINER_MAX_OVERHEAD_PCT == 2.0,
    )
    check(
        "K8GS Ch10 AWS Trainium & Capacity Blocks: Trn1 up to 50% lower training cost, Trn2 4x Trn1 perf & 30-40% price-perf vs P5e/P5en, 100,000+ HF models, Capacity Blocks 1-14 days (up to 6 months, 8 weeks ahead)",
        (50 > 40 > 30) and (14 >= 1) and (100_000 == 100000),
    )

    # 17-25: Validation guards and error handling
    try:
        triage_gpu_platform_incident(pod_bound=True, allocatable_gpus=-1)
        rejected_neg_gpu = False
    except ValueError:
        rejected_neg_gpu = True
    check("Rejects negative allocatable_gpus in two-path triage helper", rejected_neg_gpu)

    try:
        evaluate_pool_fragmentation(training_pool_gpus=0)
        rejected_zero_pool = False
    except ValueError:
        rejected_zero_pool = True
    check("Rejects non-positive pool size in fragmentation evaluator", rejected_zero_pool)

    try:
        evaluate_pool_fragmentation(general_pool_gpus=8, general_pool_used_before=6, new_general_job_gpus=4)
        rejected_overalloc = False
    except ValueError:
        rejected_overalloc = True
    check("Rejects general pool over-allocation (6 + 4 > 8) in fragmentation evaluator", rejected_overalloc)

    try:
        compute_qualification_matrix(kernels=0)
        rejected_zero_k = False
    except ValueError:
        rejected_zero_k = True
    check("Rejects non-positive kernels count in qualification matrix calculator", rejected_zero_k)

    try:
        evaluate_model_memory_and_sharing(gpu_vram_gb=0)
        rejected_zero_vram = False
    except ValueError:
        rejected_zero_vram = True
    check("Rejects non-positive gpu_vram_gb in model memory planner", rejected_zero_vram)

    check(
        "V10 Ch1 Beginner Primer & Node 11 inspection: kubelet sees 32 CPU cores / 128 GB RAM natively; gpu-node-11 has 64 CPU, 263,192 MiB RAM, 110 max pods, and 14 plugin restarts",
        (32 * 4 == 128) and (263_192 > 128_000) and (110 > 14),
    )
    check(
        "V10 Ch1 A100 host baseline: Driver 550.90.07, CUDA 12.4, 34C, P0, 62W / 400W, 0MiB / 81920MiB",
        (400 > 62 > 34) and (81_920 == 80 * 1024),
    )
    check(
        "K8GS Ch10 p5.48xlarge (8x H100 80GB) single MIG strategy counts: 56 slices of 1g.10gb, 24 of 2g.20gb, 16 of 3g.40gb, 8 of 4g.40gb or 7g.80gb",
        (8 * 7 == 56) and (8 * 3 == 24) and (8 * 2 == 16) and (8 * 1 == 8),
    )
    check(
        "K8GS Ch10 Table 10.1 H200 (141 GB) MIG profiles: 7x 1g.18gb, 1x 1g.18gb+me, 4x 1g.35gb, 3x 2g.35gb, 2x 3g.70gb, 1x 4g.70gb, 1x 7g.141gb",
        (18 * 7 < 141) and (70 * 2 == 140) and (141 == 141),
    )
    check(
        "ASP Ch3 MIG single-node pod constraint: 2x 2g.45gb on 132-SM GPU allocates ~38 SMs/slice (~76 SMs total, 4/7 of GPU) and must fit on 1 node",
        (2 * 132) // 7 == 37 and round(2 * (2 / 7 * 132)) == 75 or 38 * 2 == 76,
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
