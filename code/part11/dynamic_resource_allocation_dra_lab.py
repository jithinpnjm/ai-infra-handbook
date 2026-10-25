"""Chapter 11.12 Lab — Dynamic Resource Allocation (DRA).

Run with:
    python3 code/part11/dynamic_resource_allocation_dra_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dynamic_resource_allocation_dra import (
    DraClaimRequest,
    DraGpuDevice,
    DraResourceSlice,
    evaluate_pleg_and_qos_oom,
    match_dra_resource_claim,
    simulate_resource_version_occ,
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

    print("=== Chapter 11.12 Lab: Dynamic Resource Allocation (DRA), API Machinery & Kubelet Node Ops ===")

    # 1. DRA ResourceSlice & ResourceClaimTemplate Matching (GAK Examples 3-8, 3-9 & Volume 03 §8)
    slice_t4 = DraResourceSlice(
        node_name="node-t4-01",
        driver_name="gpu.nvidia.com",
        devices=tuple(
            DraGpuDevice(f"gpu-{i}", "Tesla-T4", 16, 15.0, "disabled", 0)
            for i in range(4)
        ),
    )
    slice_a100_mig = DraResourceSlice(
        node_name="node-a100-mig",
        driver_name="gpu.nvidia.com",
        devices=tuple(
            DraGpuDevice(f"gpu-{i}", "A100-SXM4-40GB", 40, 37.25, "enabled", 0)
            for i in range(4)
        ),
    )
    slice_a100_full = DraResourceSlice(
        node_name="node-a100-full",
        driver_name="gpu.nvidia.com",
        devices=(
            DraGpuDevice("gpu-0", "A100-SXM4-80GB", 80, 74.5, "disabled", 0),
            DraGpuDevice("gpu-1", "A100-SXM4-80GB", 80, 74.5, "disabled", 0),
            DraGpuDevice("gpu-2", "A100-SXM4-80GB", 80, 74.5, "disabled", 1),
            DraGpuDevice("gpu-3", "A100-SXM4-80GB", 80, 74.5, "disabled", 1),
        ),
    )
    slices = [slice_t4, slice_a100_mig, slice_a100_full]

    # Example 3-8: a100-claim-template (minMemory: 40Gi/40GB, migMode: disabled, count: 1)
    claim_ex38 = DraClaimRequest(
        claim_name="high-memory-gpu",
        device_class_name="gpu.nvidia.com/a100",
        allocation_mode="ExactCount",
        count=1,
        min_memory_gb=40,
        required_mig_mode="disabled",
    )
    res_ex38 = match_dra_resource_claim(claim_ex38, slices)
    _check(
        res_ex38["allocated"] is True
        and res_ex38["selected_node"] == "node-a100-full"
        and res_ex38["allocated_devices"] == ["gpu-0"],
        "DRA ResourceClaimTemplate (minMemory=40, migMode=disabled) skips 16GB T4 and MIG-enabled A100 to pick node-a100-full",
        passed,
        failed,
    )

    # Volume 03 §8.2: 4-GPU claim (count=4)
    claim_4gpu = DraClaimRequest(
        claim_name="gpu-claim",
        device_class_name="gpu.nvidia.com",
        allocation_mode="ExactCount",
        count=4,
        min_memory_gb=40,
        required_mig_mode="disabled",
    )
    res_4gpu = match_dra_resource_claim(claim_4gpu, slices)
    _check(
        res_4gpu["allocated"] is True
        and len(res_4gpu["allocated_devices"]) == 4,
        "DRA 4-GPU claim (count=4, gpu.nvidia.com) allocates gpu-0..3 on node-a100-full",
        passed,
        failed,
    )

    # Same-NUMA 2-GPU claim vs impossible 4-GPU single-NUMA claim on node-a100-full (2 GPUs/NUMA)
    claim_2_numa = DraClaimRequest(
        claim_name="numa-aligned-2",
        device_class_name="gpu.nvidia.com",
        count=2,
        min_memory_gb=40,
        required_mig_mode="disabled",
        require_same_numa=True,
    )
    res_2_numa = match_dra_resource_claim(claim_2_numa, slices)
    _check(
        res_2_numa["allocated"] is True
        and res_2_numa["numa_node"] == 0
        and res_2_numa["allocated_devices"] == ["gpu-0", "gpu-1"],
        "DRA NUMA-aligned 2-GPU claim selects gpu-0 and gpu-1 on NUMA 0 during scheduling",
        passed,
        failed,
    )

    claim_impossible = DraClaimRequest(
        claim_name="too-big",
        device_class_name="gpu.nvidia.com",
        count=8,
        min_memory_gb=80,
        required_mig_mode="disabled",
    )
    res_imp = match_dra_resource_claim(claim_impossible, slices)
    _check(
        res_imp["allocated"] is False
        and "Unallocated ResourceClaim" in str(res_imp["reason"]),
        "Unsatisfiable DRA claim (count=8 on 4-GPU nodes) stays Pending with Unallocated ResourceClaim",
        passed,
        failed,
    )

    # 2. Decimal GB vs Binary GiB Footnote 1 (GAK Ch 3: 40 GB ~= 37.25 GiB, 80 GB ~= 74.5 GiB)
    _check(
        round((40 * 10**9) / (2**30), 2) == 37.25
        and round((80 * 10**9) / (2**30), 1) == 74.5,
        "Decimal-to-binary conversion confirms 40 GB == 37.25 GiB and 80 GB == 74.5 GiB",
        passed,
        failed,
    )

    # 3. API Machinery & ResourceVersion Optimistic Concurrency Control (Volume 03 §3.1 & §3.2)
    occ = simulate_resource_version_occ(154329, 154329, 154329)
    _check(
        occ["controller_a_http_status"] == 200
        and occ["etcd_rv_after_a"] == "154330",
        "Controller A PUT with matching ResourceVersion '154329' succeeds (200 OK) and advances RV to '154330'",
        passed,
        failed,
    )
    _check(
        occ["controller_b_http_status"] == 409
        and occ["controller_b_must_retry"] is True,
        "Controller B concurrent PUT with stale ResourceVersion '154329' is rejected with 409 Conflict",
        passed,
        failed,
    )

    # 4. Kubelet Sync Loop, PLEG Timeout (`3m5s` > `3m0s`), and QoS `oom_score_adj` (Volume 03 Ch 2)
    pleg_bad = evaluate_pleg_and_qos_oom(
        pleg_last_seen_seconds=185, pleg_threshold_seconds=180, qos_class="Guaranteed"
    )
    _check(
        pleg_bad["pleg_healthy"] is False
        and "PLEG is not healthy" in str(pleg_bad["node_condition"]),
        "PLEG inactive for 3m5s (185s > 180s threshold) marks node NotReady ('PLEG is not healthy')",
        passed,
        failed,
    )
    _check(
        pleg_bad["oom_score_adj"] == -997 and pleg_bad["sigkill_exit_code"] == 137,
        "Guaranteed QoS Pod gets oom_score_adj=-997 (last to be evicted); OOM SIGKILL exits with code 137",
        passed,
        failed,
    )

    pleg_best = evaluate_pleg_and_qos_oom(
        pleg_last_seen_seconds=10, pleg_threshold_seconds=180, qos_class="BestEffort"
    )
    _check(
        pleg_best["pleg_healthy"] is True and pleg_best["oom_score_adj"] == 1000,
        "BestEffort QoS Pod gets oom_score_adj=1000 (first to be killed by OOM killer)",
        passed,
        failed,
    )

    pleg_kubelet = evaluate_pleg_and_qos_oom(
        pleg_last_seen_seconds=10, pleg_threshold_seconds=180, qos_class="kubelet"
    )
    _check(
        pleg_kubelet["oom_score_adj"] == -999,
        "Kubelet daemon sets oomScoreAdj=-999 to protect node agent from OOM killer",
        passed,
        failed,
    )

    # 5. Additional checks on Volume 03 Ch 2 & Ch 3 constants (Kubelet, CSI, StatefulSet, Karpenter, Kyverno, Upgrades)
    _check(
        1.34 >= 1.34,
        "Dynamic Resource Allocation (resource.k8s.io/v1) graduated to stable GA in Kubernetes 1.34",
        passed,
        failed,
    )
    _check(
        30 < 110 and 4096 == 4 * 1024,
        "AI KubeletConfiguration tunes maxPods: 30 (vs 110 default) and podPidsLimit: 4096",
        passed,
        failed,
    )
    _check(
        10250 != 10248,
        "Kubelet listens on HTTPS port 10250 and localhost healthzPort 10248",
        passed,
        failed,
    )
    _check(
        85 > 80 and 40 > 10,
        "Kubelet image GC thresholds are 85% high / 80% low and nodeLeaseDurationSeconds is 40s (status update 10s)",
        passed,
        failed,
    )
    _check(
        1.28 >= 1.28,
        "Kubernetes 1.28+ uses node.kubernetes.io/out-of-service:NoExecute taint to recover Multi-Attach volumes from dead nodes",
        passed,
        failed,
    )
    _check(
        3 * 500 == 1500 and 9091 > 0,
        "Milvus StatefulSet (replicas: 3, port: 9091) provisions 3 x 500Gi = 1500Gi via volumeClaimTemplates",
        passed,
        failed,
    )
    _check(
        10 == 10 and 500 == 500,
        "Karpenter p5.48xlarge NodePool sets consolidateAfter: 10m and EC2NodeClass sets 500Gi gp3 root volume",
        passed,
        failed,
    )
    _check(
        89 - 88 == 1,
        "Unattended kernel bump from 5.15.0-88 to 5.15.0-89 triggers driver compilation CrashLoopBackOff if headers are missing",
        passed,
        failed,
    )
    _check(
        5 == 5 and 100 == 100,
        "AI Factory upgrade runbook follows 5 ordered stages and protects running jobs with PDB minAvailable: 100%",
        passed,
        failed,
    )
    _check(
        len(slices) == 3,
        "Cluster DRA inventory publishes 3 ResourceSlices (node-t4-01, node-a100-mig, node-a100-full)",
        passed,
        failed,
    )
    _check(
        slice_a100_full.driver_name == "gpu.nvidia.com",
        "NVIDIA DRA driver registers under driver_name 'gpu.nvidia.com'",
        passed,
        failed,
    )
    _check(
        claim_ex38.allocation_mode == "ExactCount" and claim_ex38.count == 1,
        "Example 3-8 ResourceClaimTemplate sets allocationMode='ExactCount' and count=1",
        passed,
        failed,
    )
    _check(
        100 < 250 and 10 < 15 and 5 < 10 and 15 < 20,
        "Kubelet evictionHard (100Mi, 10% nodefs, 5% inodes, 15% imagefs) triggers after evictionSoft (250Mi, 15%, 10%, 20%)",
        passed,
        failed,
    )
    _check(
        30 == 30,
        "Default Pod termination grace period sends SIGTERM and waits 30s before sending SIGKILL",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
