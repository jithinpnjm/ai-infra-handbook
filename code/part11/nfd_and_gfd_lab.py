"""Chapter 11.3 Lab — Node Feature Discovery and GPU Feature Discovery.

Run with:
    python3 code/part11/nfd_and_gfd_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nfd_and_gfd import (
    GpuNvmlProbe,
    HostHardwareProbe,
    PCI_CLASS_NAMES,
    PCI_VENDOR_NAMES,
    classify_label_tier,
    detect_discovery_drift,
    evaluate_fleet_refresh_blast_radius,
    evaluate_node_affinity_candidate,
    generate_gfd_labels,
    generate_nfd_labels,
)


def _check(condition: bool, label: str, passed: list[str], failed: list[str]) -> None:
    if condition:
        passed.append(label)
        print(f"  [PASS] {label}")
    else:
        failed.append(label)
        print(f"  [ERR]  {label}")


def main() -> int:
    passed: list[str] = []
    failed: list[str] = []

    print("=== Chapter 11.3 Lab: Node Feature Discovery (NFD) and GPU Feature Discovery (GFD) ===")

    # 1. PCI Class & Vendor ID Decoding (GAK Example 3-2)
    _check(
        PCI_VENDOR_NAMES["10de"] == "NVIDIA"
        and PCI_VENDOR_NAMES["1002"] == "AMD"
        and PCI_VENDOR_NAMES["8086"] == "Intel"
        and PCI_VENDOR_NAMES["1d0f"] == "AWS",
        "PCI vendor table maps 10de->NVIDIA, 1002->AMD, 8086->Intel, 1d0f->AWS",
        passed,
        failed,
    )
    _check(
        PCI_CLASS_NAMES["0302"] == "3D controller (GPU)"
        and PCI_CLASS_NAMES["0300"] == "VGA compatible controller",
        "PCI class table maps 0302->3D controller (GPU) and 0300->VGA controller",
        passed,
        failed,
    )

    # 2. NFD Label Generation (GAK Example 3-2 & V10 Ch 5 gpu-node-03)
    probe = HostHardwareProbe(
        pci_devices=(("0300", "1d0f"), ("0302", "10de")),
        avx512f=True,
        cpu_multithreading=True,
        cpu_family="6",
        cpu_model_id="85",
        cpu_vendor="Intel",
        selinux_enabled=True,
        kernel_full="5.14.0-427.62.1.el9_4.x86_64",
    )
    nfd_labels = generate_nfd_labels(probe)
    _check(
        nfd_labels["feature.node.kubernetes.io/pci-0302_10de.present"] == "true"
        and nfd_labels["feature.node.kubernetes.io/pci-0300_1d0f.present"] == "true",
        "NFD sets pci-0302_10de.present=true and pci-0300_1d0f.present=true",
        passed,
        failed,
    )
    _check(
        nfd_labels["feature.node.kubernetes.io/pci-10de.present"] == "true",
        "NFD sets pci-10de.present=true trigger label for GPU Operator",
        passed,
        failed,
    )
    _check(
        nfd_labels["feature.node.kubernetes.io/cpu-cpuid.AVX512F"] == "true"
        and nfd_labels["feature.node.kubernetes.io/cpu-model.family"] == "6"
        and nfd_labels["feature.node.kubernetes.io/cpu-model.id"] == "85"
        and nfd_labels["feature.node.kubernetes.io/cpu-model.vendor_id"] == "Intel",
        "NFD sets CPU AVX512F, family 6, model id 85, and vendor Intel",
        passed,
        failed,
    )
    _check(
        nfd_labels["feature.node.kubernetes.io/kernel-selinux.enabled"] == "true"
        and nfd_labels["feature.node.kubernetes.io/kernel-version.full"]
        == "5.14.0-427.62.1.el9_4.x86_64",
        "NFD sets kernel-selinux.enabled=true and kernel-version.full=5.14.0-427.62.1.el9_4.x86_64",
        passed,
        failed,
    )

    # 3. GFD Label Synthesis (GAK Table 3-1 & V10 Ch 5 gpu-node-03)
    a100_probe = GpuNvmlProbe(
        physical_gpu_count=4,
        product_name="A100-SXM4-40GB",
        memory_mib=40537,
        family="ampere",
        driver_version="525.105.17",
        cuda_runtime_version="12.2",
        compute_major=8,
        compute_minor=0,
        machine_type="dgx-a100",
        mig_capable=True,
    )
    gfd_a100 = generate_gfd_labels(a100_probe)
    _check(
        gfd_a100["nvidia.com/gpu.count"] == "4"
        and gfd_a100["nvidia.com/gpu.product"] == "A100-SXM4-40GB"
        and gfd_a100["nvidia.com/gpu.memory"] == "40537",
        "GFD Table 3-1 baseline sets count=4, product=A100-SXM4-40GB, memory=40537",
        passed,
        failed,
    )
    _check(
        gfd_a100["nvidia.com/gpu.family"] == "ampere"
        and gfd_a100["nvidia.com/cuda.driver-version.full"] == "525.105.17"
        and gfd_a100["nvidia.com/cuda.runtime.version.full"] == "12.2",
        "GFD sets family=ampere, driver=525.105.17, cuda.runtime=12.2",
        passed,
        failed,
    )
    _check(
        gfd_a100["nvidia.com/gpu.compute.major"] == "8"
        and gfd_a100["nvidia.com/gpu.compute.minor"] == "0"
        and gfd_a100["nvidia.com/gpu.machine"] == "dgx-a100",
        "GFD sets compute.major=8, compute.minor=0, machine=dgx-a100",
        passed,
        failed,
    )

    # H100 node from V10 Ch 5 (`gpu-node-03`)
    h100_probe = GpuNvmlProbe(
        physical_gpu_count=8,
        product_name="NVIDIA-H100-80GB-HBM3",
        memory_mib=81920,
        family="hopper",
        driver_version="550.90.07",
        cuda_runtime_version="12.4",
        compute_major=9,
        compute_minor=0,
        mig_capable=True,
        mig_strategy="single",
    )
    gfd_h100 = generate_gfd_labels(h100_probe)
    _check(
        gfd_h100["nvidia.com/gpu.product"] == "NVIDIA-H100-80GB-HBM3"
        and gfd_h100["nvidia.com/gpu.memory"] == "81920"
        and gfd_h100["nvidia.com/gpu.compute.major"] == "9"
        and gfd_h100["nvidia.com/cuda.driver-version.full"] == "550.90.07",
        "GFD on gpu-node-03 sets NVIDIA-H100-80GB-HBM3, memory=81920, compute.major=9, driver=550.90.07",
        passed,
        failed,
    )

    # Time-slicing (`-SHARED` suffix and `replicas=8` on 10 GPUs -> count=80)
    shared_probe = GpuNvmlProbe(
        physical_gpu_count=10,
        product_name="A100-SXM4-40GB",
        memory_mib=40537,
        family="ampere",
        driver_version="525.105.17",
        cuda_runtime_version="12.2",
        compute_major=8,
        compute_minor=0,
        time_slicing_replicas=8,
    )
    gfd_shared = generate_gfd_labels(shared_probe)
    _check(
        gfd_shared["nvidia.com/gpu.product"] == "A100-SXM4-40GB-SHARED"
        and gfd_shared["nvidia.com/gpu.replicas"] == "8"
        and gfd_shared["nvidia.com/gpu.count"] == "80",
        "Time-slicing (replicas=8 on 10 GPUs) appends -SHARED and sets gpu.count=80",
        passed,
        failed,
    )

    # Single MIG strategy (`2` A100s split into `7` x `1g.5gb` -> `gpu.count=14` and `-MIG-1g.5gb`)
    single_mig_probe = GpuNvmlProbe(
        physical_gpu_count=2,
        product_name="A100-SXM4-40GB",
        memory_mib=40537,
        family="ampere",
        driver_version="525.105.17",
        cuda_runtime_version="12.2",
        compute_major=8,
        compute_minor=0,
        mig_strategy="single",
        single_mig_profile="1g.5gb",
        single_mig_slices_per_gpu=7,
    )
    gfd_single_mig = generate_gfd_labels(single_mig_probe)
    _check(
        gfd_single_mig["nvidia.com/gpu.product"] == "A100-SXM4-40GB-MIG-1g.5gb"
        and gfd_single_mig["nvidia.com/gpu.count"] == "14"
        and gfd_single_mig["nvidia.com/mig.strategy"] == "single",
        "Single MIG strategy on 2 A100s (7x 1g.5gb) sets product=...-MIG-1g.5gb and gpu.count=14",
        passed,
        failed,
    )

    # Mixed MIG strategy (`mig-1g.5gb.count=2`)
    mixed_mig_probe = GpuNvmlProbe(
        physical_gpu_count=4,
        product_name="A100-SXM4-40GB",
        memory_mib=40537,
        family="ampere",
        driver_version="525.105.17",
        cuda_runtime_version="12.2",
        compute_major=8,
        compute_minor=0,
        mig_strategy="mixed",
        mixed_mig_counts={"1g.5gb": 2, "3g.20gb": 1},
    )
    gfd_mixed_mig = generate_gfd_labels(mixed_mig_probe)
    _check(
        gfd_mixed_mig["nvidia.com/mig.strategy"] == "mixed"
        and gfd_mixed_mig["nvidia.com/mig-1g.5gb.count"] == "2"
        and gfd_mixed_mig["nvidia.com/mig-3g.20gb.count"] == "1",
        "Mixed MIG strategy publishes per-profile counts (mig-1g.5gb.count=2, mig-3g.20gb.count=1)",
        passed,
        failed,
    )

    # Combined MIG + Time-Slicing (`-MIG-1g.5gb-SHARED`, 2 slices x 2 replicas = 4 units)
    mig_shared_probe = GpuNvmlProbe(
        physical_gpu_count=1,
        product_name="A100-SXM4-40GB",
        memory_mib=40537,
        family="ampere",
        driver_version="525.105.17",
        cuda_runtime_version="12.2",
        compute_major=8,
        compute_minor=0,
        mig_strategy="single",
        single_mig_profile="1g.5gb",
        single_mig_slices_per_gpu=2,
        time_slicing_replicas=2,
    )
    gfd_mig_shared = generate_gfd_labels(mig_shared_probe)
    _check(
        gfd_mig_shared["nvidia.com/gpu.product"].endswith("-MIG-1g.5gb-SHARED")
        and gfd_mig_shared["nvidia.com/gpu.count"] == "4",
        "Combined MIG (2 slices) + Time-Slicing (2 replicas) appends -SHARED and exposes 4 units",
        passed,
        failed,
    )

    # 4. Three-Tier Label Taxonomy Classification (V10 Ch 5)
    t_fact = classify_label_tier("nvidia.com/gpu.product")
    t_assert = classify_label_tier("gpu-validation")
    t_class = classify_label_tier("gpu.platform.example/class")
    _check(
        t_fact["kind"] == "discovered_fact"
        and t_fact["consumer"] == "platform_automation_and_diagnostics",
        "nvidia.com/gpu.product is classified as discovered_fact for platform automation",
        passed,
        failed,
    )
    _check(
        t_assert["kind"] == "lifecycle_assertion"
        and t_assert["consumer"] == "admission_and_operations",
        "gpu-validation is classified as lifecycle_assertion for admission and operations",
        passed,
        failed,
    )
    _check(
        t_class["kind"] == "service_class"
        and t_class["consumer"] == "workload_manifests",
        "gpu.platform.example/class is classified as service_class for workload manifests",
        passed,
        failed,
    )

    # 5. Fleet Refresh Blast Radius (80 nodes: 30 A100-80GB, 30 H100-80GB, 20 A100-40GB retired)
    refresh = evaluate_fleet_refresh_blast_radius(30, 30, 20, workload_manifests_count=45)
    _check(
        refresh["total_fleet_nodes"] == 80 and refresh["retired_nodes"] == 20,
        "Fleet refresh models 80 GPU nodes across 3 generations retiring 20 oldest nodes",
        passed,
        failed,
    )
    _check(
        refresh["sku_coupled_manifests_broken"] == 45
        and refresh["service_class_manifests_broken"] == 0
        and refresh["service_class_controller_configs_updated"] == 1,
        "Service-class abstraction reduces broken workload manifests from 45 to 0 (1 controller update)",
        passed,
        failed,
    )

    # 6. Label-Based Scheduling Evaluation (GAK Example 3-4: Gt 40000 required + hopper preferred weight 1)
    t4_labels = {"nvidia.com/gpu.memory": "16384", "nvidia.com/gpu.family": "turing"}
    t4_ok, t4_score, _ = evaluate_node_affinity_candidate(
        t4_labels, {"nvidia.com/gpu": "true"}, ["nvidia.com/gpu"]
    )
    a100_ok, a100_score, _ = evaluate_node_affinity_candidate(
        gfd_a100, {"nvidia.com/gpu": "true"}, ["nvidia.com/gpu"]
    )
    h100_ok, h100_score, _ = evaluate_node_affinity_candidate(
        gfd_h100, {"nvidia.com/gpu": "true"}, ["nvidia.com/gpu"]
    )
    untol_ok, _, _ = evaluate_node_affinity_candidate(
        gfd_h100, {"nvidia.com/gpu": "true"}, []
    )
    _check(
        not t4_ok,
        "16 GB T4 node is rejected by required Gt 40000 MiB memory matchExpression",
        passed,
        failed,
    )
    _check(
        a100_ok and a100_score == 0,
        "40537 MiB Ampere A100 passes Gt 40000 MiB required term with preferred score 0",
        passed,
        failed,
    )
    _check(
        h100_ok and h100_score == 1,
        "81920 MiB Hopper H100 passes Gt 40000 MiB required term and gains preferred score +1",
        passed,
        failed,
    )
    _check(
        not untol_ok,
        "Pod missing nvidia.com/gpu Exists toleration is repelled by NoSchedule taint",
        passed,
        failed,
    )

    # 7. Discovery Drift & Pool Asymmetry (V10 Ch 5: 08:40:11 vs 09:15:00, gpu-node-19 vs gpu-node-13)
    pool_labels = {
        "gpu-node-19": {
            "nvidia.com/mig.capable": "true",
            "nvidia.com/mig.strategy": "single",
        },
        "gpu-node-13": {
            "nvidia.com/mig.capable": "true",
        },
    }
    drift = detect_discovery_drift("08:40:11", "09:15:00", pool_labels)
    _check(
        drift["probe_stale"] is True,
        "Detects stale NFD/GFD probe when worker timestamp (08:40:11) precedes maintenance (09:15:00)",
        passed,
        failed,
    )
    _check(
        drift["asymmetric_nodes"] == ["gpu-node-13"]
        and drift["safe_for_admission"] is False,
        "Detects pool asymmetry on gpu-node-13 (missing nvidia.com/mig.strategy) and blocks admission",
        passed,
        failed,
    )

    clean_drift = detect_discovery_drift(
        "09:20:00",
        "09:15:00",
        {
            "gpu-node-19": {
                "nvidia.com/mig.capable": "true",
                "nvidia.com/mig.strategy": "single",
            },
            "gpu-node-13": {
                "nvidia.com/mig.capable": "true",
                "nvidia.com/mig.strategy": "single",
            },
        },
    )
    _check(
        clean_drift["safe_for_admission"] is True,
        "Approves pool admission once post-maintenance probe (09:20:00) reconciles uniform labels",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
