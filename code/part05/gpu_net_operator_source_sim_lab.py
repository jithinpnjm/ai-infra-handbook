#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.33: Reading the GPU Operator and Network Operator source."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpu_net_operator_source_sim import (
    compute_gpu_node_deploy_labels,
    evaluate_node_operand_gating_and_stale_objects,
    is_daemonset_ready,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Section 5: gpuStateLabels mapping (container vs vm-passthrough vs operands=false)
    lbl_ctr = compute_gpu_node_deploy_labels({"feature.node.kubernetes.io/pci-10de.present": "true"})
    lbl_vm = compute_gpu_node_deploy_labels(
        {
            "feature.node.kubernetes.io/pci-10de.present": "true",
            "nvidia.com/gpu.workload.config": "vm-passthrough",
        }
    )
    lbl_off = compute_gpu_node_deploy_labels(
        {
            "feature.node.kubernetes.io/pci-10de.present": "true",
            "nvidia.com/gpu.deploy.operands": "false",
        }
    )
    check(
        "compute_gpu_node_deploy_labels maps container->driver/toolkit/device-plugin, vm-passthrough->vfio-manager, and respects operands=false",
        lbl_ctr.get("nvidia.com/gpu.deploy.device-plugin") == "true"
        and lbl_vm.get("nvidia.com/gpu.deploy.vfio-manager") == "true"
        and "nvidia.com/gpu.deploy.device-plugin" not in lbl_vm
        and "nvidia.com/gpu.deploy.driver" not in lbl_off,
    )

    # 2. Section 4: isDaemonSetReady for OnDelete driver DaemonSet (stale revision vs current revision)
    not_ready_ondelete = is_daemonset_ready(
        generation=2,
        observed_generation=2,
        desired_scheduled=2,
        number_unavailable=0,
        updated_scheduled=1,
        update_strategy="OnDelete",
        current_revision_hash="rev-2",
        pods_on_daemonset=[
            {"controller-revision-hash": "rev-2", "all_containers_ready": True},
            {"controller-revision-hash": "rev-1", "all_containers_ready": True},  # old revision not yet restarted by upgrade controller!
        ],
    )
    ready_ondelete = is_daemonset_ready(
        generation=2,
        observed_generation=2,
        desired_scheduled=2,
        number_unavailable=0,
        updated_scheduled=2,
        update_strategy="OnDelete",
        current_revision_hash="rev-2",
        pods_on_daemonset=[
            {"controller-revision-hash": "rev-2", "all_containers_ready": True},
            {"controller-revision-hash": "rev-2", "all_containers_ready": True},
        ],
    )
    check(
        "is_daemonset_ready returns False for OnDelete DaemonSet when 1 pod still runs old controller-revision-hash and True when all match",
        not_ready_ondelete is False and ready_ondelete is True,
    )

    # 3. Section 5, 9, 10: /run/nvidia/validations chain, mofed.wait label, and state_skel stale object deletion
    gating = evaluate_node_operand_gating_and_stale_objects(
        validation_files_present={"driver-ready"},  # toolkit-ready not yet written!
        mofed_pod_ready=True,
        previously_rendered_objects={"DaemonSet/mofed", "DaemonSet/rdma-dp", "DaemonSet/sriov-dp"},
        currently_rendered_objects={"DaemonSet/mofed", "DaemonSet/rdma-dp"},
    )
    check(
        "With only driver-ready, toolkit init unblocks while device-plugin init waits; mofed_pod_ready sets mofed.wait='false'; sriov-dp flagged stale",
        gating["toolkit_init_unblocked"] is True
        and gating["device_plugin_init_unblocked"] is False
        and gating["mofed_wait_label"] == "false"
        and gating["rdma_dp_can_schedule"] is True
        and gating["stale_objects_to_delete"] == ["DaemonSet/sriov-dp"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
