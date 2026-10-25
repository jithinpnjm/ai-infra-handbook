"""Chapter 11.4 Lab — GPU Operator architecture and operands.

Run with:
    python3 code/part11/gpu_operator_and_operands_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gpu_operator_and_operands import (
    ClusterPolicyConfig,
    NodeOperandGates,
    OPERAND_DEPLOY_LABELS,
    calculate_canary_vs_unpooled_blast_radius,
    classify_gpu_vs_network_operator_fault,
    compare_policy_vs_daemonset_health,
    compute_node_deploy_labels,
    evaluate_operator_validator_pod,
    plan_driver_upgrade_window,
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

    print("=== Chapter 11.4 Lab: GPU Operator Architecture and Node Operands ===")

    # 1. Node Deploy Labels (`nvidia.com/gpu.deploy.*` from bcm11-containerization)
    _check(
        len(OPERAND_DEPLOY_LABELS) == 8,
        "GPU Operator tracks 8 nvidia.com/gpu.deploy.* operand targeting labels",
        passed,
        failed,
    )
    cpu_only_labels = compute_node_deploy_labels(False, ClusterPolicyConfig())
    _check(
        cpu_only_labels == {},
        "Nodes without pci-10de.present receive no nvidia.com/gpu.deploy.* labels",
        passed,
        failed,
    )
    op_managed = compute_node_deploy_labels(
        True, ClusterPolicyConfig(driver_enabled=True, toolkit_enabled=True)
    )
    _check(
        op_managed["nvidia.com/gpu.deploy.driver"] == "true"
        and op_managed["nvidia.com/gpu.deploy.container-toolkit"] == "true"
        and op_managed["nvidia.com/gpu.deploy.operator-validator"] == "true",
        "Operator-managed policy sets deploy.driver=true, deploy.container-toolkit=true, deploy.operator-validator=true",
        passed,
        failed,
    )
    host_managed = compute_node_deploy_labels(
        True, ClusterPolicyConfig(driver_enabled=False, toolkit_enabled=True)
    )
    _check(
        host_managed["nvidia.com/gpu.deploy.driver"] == "false"
        and host_managed["nvidia.com/gpu.deploy.container-toolkit"] == "true",
        "Host-managed driver policy (BCM/DGX default) sets deploy.driver=false and deploy.container-toolkit=true",
        passed,
        failed,
    )

    # 2. Validator Init-Container Chain (`driver-validation`, `toolkit-validation`, `cuda-validation`, `plugin-validation`)
    g_all_ok = evaluate_operator_validator_pod(
        NodeOperandGates("node001", True, True, True, True, True)
    )
    _check(
        g_all_ok["node_accepted"] is True
        and g_all_ok["validator_log"] == "all validations are successful"
        and len(g_all_ok["init_containers"]) == 4,
        "All 4 validator init containers pass on node001 and log 'all validations are successful'",
        passed,
        failed,
    )

    g_drv_err = evaluate_operator_validator_pod(
        NodeOperandGates("gpu-node-22", False, False, True, True, True)
    )
    _check(
        g_drv_err["node_accepted"] is False
        and g_drv_err["toolkit_pod_state"] == "Init:0/1"
        and g_drv_err["device_plugin_pod_state"] == "Init:0/1"
        and g_drv_err["validator_pod_state"] == "Init:0/4",
        "When driver gate fails, toolkit and device-plugin stay in Init:0/1 and validator stays in Init:0/4",
        passed,
        failed,
    )

    g_tk_err = evaluate_operator_validator_pod(
        NodeOperandGates("gpu-node-23", True, True, False, True, True)
    )
    _check(
        g_tk_err["init_containers"]["driver-validation"] == "Completed"
        and g_tk_err["init_containers"]["toolkit-validation"] == "Error"
        and g_tk_err["validator_pod_state"] == "Init:1/4",
        "When toolkit gate fails after driver succeeds, validator halts at Init:1/4 (toolkit-validation)",
        passed,
        failed,
    )

    g_cuda_err = evaluate_operator_validator_pod(
        NodeOperandGates("gpu-node-24", True, True, True, False, True)
    )
    _check(
        g_cuda_err["init_containers"]["cuda-validation"] == "Error"
        and g_cuda_err["validator_pod_state"] == "Init:2/4"
        and "no kernel image is available" in str(g_cuda_err["validator_log"]),
        "When CUDA sample fails (compute capability mismatch), validator halts at Init:2/4 (cuda-validation)",
        passed,
        failed,
    )

    g_dp_err = evaluate_operator_validator_pod(
        NodeOperandGates("gpu-node-25", True, True, True, True, False)
    )
    _check(
        g_dp_err["init_containers"]["plugin-validation"] == "Error"
        and g_dp_err["validator_pod_state"] == "Init:3/4",
        "When device plugin fails registration, validator halts at Init:3/4 (plugin-validation)",
        passed,
        failed,
    )

    # 3. ClusterPolicy.status.state vs Per-Node DaemonSet Readiness (25 nodes, 24 ready)
    pol_vs_ds = compare_policy_vs_daemonset_health(25, 25, 25, 24)
    _check(
        pol_vs_ds["cluster_policy_state"] == "ready"
        and pol_vs_ds["device_plugin_ready_ratio"] == "24/25"
        and pol_vs_ds["unhealthy_nodes_count"] == 1
        and pol_vs_ds["fleet_fully_healthy"] is False,
        "ClusterPolicy.status.state can report 'ready' while 1 of 25 device-plugin pods is in CrashLoopBackOff (24/25)",
        passed,
        failed,
    )

    pol_all_green = compare_policy_vs_daemonset_health(3, 3, 3, 3)
    _check(
        pol_all_green["fleet_fully_healthy"] is True
        and pol_all_green["driver_ready_ratio"] == "3/3",
        "3-node canary pool with 3/3 driver, toolkit, and plugin DaemonSets is fully healthy",
        passed,
        failed,
    )

    # 4. Canary vs Unpooled Blast Radius (60 nodes, 35 incompatible kernel = 58.33% vs 3-node canary = 5.0%)
    blast = calculate_canary_vs_unpooled_blast_radius(
        total_nodes=60, incompatible_kernel_nodes=35, canary_pool_nodes=3
    )
    _check(
        blast["unpooled_degraded_pct"] == 58.33
        and blast["unpooled_degraded_pct_rounded"] == 58.0,
        "Unpooled ClusterPolicy update across 60 nodes with 35 on kernel 6.5.0-1015-aws degrades 58.33% (~58%) of fleet",
        passed,
        failed,
    )
    _check(
        blast["canary_degraded_pct"] == 5.0
        and blast["canary_untouched_nodes"] == 57.0,
        "3-node canary pool caps blast radius at 5.0% (3/60) and leaves 57 production nodes untouched",
        passed,
        failed,
    )

    # 5. Rolling Driver Upgrade Capacity & Headroom Planner (40 nodes, 8 GPUs/node, 6 min/batch, 28-GPU headroom)
    plan_max4 = plan_driver_upgrade_window(
        total_nodes=40,
        gpus_per_node=8,
        minutes_per_node_batch=6,
        max_unavailable_nodes=4,
        required_headroom_gpus=28,
    )
    _check(
        plan_max4["batches"] == 10 and plan_max4["wall_clock_minutes"] == 60,
        "maxUnavailable: 4 across 40 nodes runs 10 batches x 6 min = 60 minutes total",
        passed,
        failed,
    )
    _check(
        plan_max4["concurrent_gpus_offline"] == 32
        and plan_max4["slo_safe"] is False
        and plan_max4["headroom_margin_gpus"] == -4,
        "maxUnavailable: 4 takes 32 GPUs offline concurrently, exceeding the 28-GPU headroom budget by 4 GPUs",
        passed,
        failed,
    )

    plan_max2 = plan_driver_upgrade_window(
        total_nodes=40,
        gpus_per_node=8,
        minutes_per_node_batch=6,
        max_unavailable_nodes=2,
        required_headroom_gpus=28,
    )
    _check(
        plan_max2["batches"] == 20 and plan_max2["wall_clock_minutes"] == 120,
        "maxUnavailable: 2 across 40 nodes runs 20 batches x 6 min = 120 minutes total",
        passed,
        failed,
    )
    _check(
        plan_max2["concurrent_gpus_offline"] == 16
        and plan_max2["slo_safe"] is True
        and plan_max2["headroom_margin_gpus"] == 12,
        "maxUnavailable: 2 takes 16 GPUs offline concurrently, staying within the 28-GPU headroom budget (+12 margin)",
        passed,
        failed,
    )

    # 6. GPU Operator vs NVIDIA Network Operator Fault Routing
    f_gpu = classify_gpu_vs_network_operator_fault(0, False, 8, True)
    f_mofed = classify_gpu_vs_network_operator_fault(8, True, 0, False)
    f_port = classify_gpu_vs_network_operator_fault(8, True, 8, False)
    f_both_ok = classify_gpu_vs_network_operator_fault(8, True, 8, True)

    _check(
        f_gpu["owner_operator"] == "GPU Operator",
        "Missing allocatable GPU or failed CUDA init routes to GPU Operator domain",
        passed,
        failed,
    )
    _check(
        f_mofed["owner_operator"] == "NVIDIA Network Operator"
        and "rdma/rdma_shared_device_a" in f_mofed["failing_layer"],
        "Healthy GPU + missing rdma/rdma_shared_device_a routes to NVIDIA Network Operator (MOFED/RDMA plugin)",
        passed,
        failed,
    )
    _check(
        f_port["owner_operator"] == "NVIDIA Network Operator"
        and "PORT_DOWN" in f_port["failing_layer"],
        "Allocated RDMA resource + ibv_devinfo PORT_DOWN routes to Network Operator SR-IOV/Multus/fabric layer",
        passed,
        failed,
    )
    _check(
        f_both_ok["owner_operator"] == "Healthy",
        "Allocatable GPU=8, CUDA init OK, rdma_shared_device_a=8, and PORT_ACTIVE (4) verifies both operators",
        passed,
        failed,
    )

    # 7. Additional checks for BCM 11 / V10 versions and metrics
    _check(
        ClusterPolicyConfig().driver_version == "550.90.07",
        "Default ClusterPolicyConfig pins reviewed driver version 550.90.07",
        passed,
        failed,
    )
    _check(
        ClusterPolicyConfig().use_precompiled is True,
        "Default ClusterPolicyConfig enables usePrecompiled=True to avoid 500-node GCC compilation storms",
        passed,
        failed,
    )
    _check(
        len([k for k, v in op_managed.items() if v == "true"]) == 8,
        "All 8 operand deployment labels evaluate to 'true' when all operands are enabled",
        passed,
        failed,
    )
    _check(
        len([k for k, v in host_managed.items() if v == "true"]) == 7,
        "Exactly 7 operand deployment labels evaluate to 'true' when driver.enabled=false",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
