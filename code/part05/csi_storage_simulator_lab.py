#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.17: Storage internals: volumes, PV and PVC, CSI and mounts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csi_storage_simulator import (
    check_csi_volume_attachment,
    compute_checkpoint_and_weight_timings,
    evaluate_zonal_pvc_binding,
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
    # 1. Section 2 & PK Ch. 4: Immediate vs WaitForFirstConsumer zonal GPU trap
    ok_imm, _, msg_imm = evaluate_zonal_pvc_binding(
        binding_mode="Immediate",
        Immediate_default_zone="us-central1-a",
        gpu_available_zones={"us-central1-b"},
    )
    ok_wffc, zone_wffc, _ = evaluate_zonal_pvc_binding(
        binding_mode="WaitForFirstConsumer",
        Immediate_default_zone="us-central1-a",
        gpu_available_zones={"us-central1-b"},
    )
    check(
        "Immediate binding deadlocks when volume lands in zone-a and GPUs are in zone-b, whereas WaitForFirstConsumer provisions in zone-b",
        ok_imm is False
        and "Unschedulable" in msg_imm
        and ok_wffc is True
        and zone_wffc == "us-central1-b",
    )

    # 2. Section 2 & 3: RWO Multi-Attach error vs same-node RWO vs RWOP vs RWX
    ok_rwo_same_node, _ = check_csi_volume_attachment(
        access_mode="ReadWriteOnce",
        currently_attached_nodes={"gpu-node-1"},
        currently_mounted_pods={"pod-a"},
        requesting_node="gpu-node-1",
        requesting_pod="pod-b",
    )
    ok_rwo_diff_node, msg_ma = check_csi_volume_attachment(
        access_mode="ReadWriteOnce",
        currently_attached_nodes={"gpu-node-1"},
        currently_mounted_pods={"pod-a"},
        requesting_node="gpu-node-2",
        requesting_pod="pod-b",
    )
    ok_rwop_same_node, _ = check_csi_volume_attachment(
        access_mode="ReadWriteOncePod",
        currently_attached_nodes={"gpu-node-1"},
        currently_mounted_pods={"pod-a"},
        requesting_node="gpu-node-1",
        requesting_pod="pod-b",
    )
    ok_rwx_diff_node, _ = check_csi_volume_attachment(
        access_mode="ReadWriteMany",
        currently_attached_nodes={"gpu-node-1"},
        currently_mounted_pods={"pod-a"},
        requesting_node="gpu-node-2",
        requesting_pod="pod-b",
    )
    check(
        "RWO allows 2 pods on same node but fails across nodes with Multi-Attach error; RWOP blocks 2nd pod on same node; RWX allows cross-node",
        ok_rwo_same_node is True
        and ok_rwo_diff_node is False
        and "Multi-Attach error" in msg_ma
        and ok_rwop_same_node is False
        and ok_rwx_diff_node is True,
    )

    # 3. Section 5: Checkpoint write stall and 140 GB model cold-start timing
    t = compute_checkpoint_and_weight_timings(
        checkpoint_size_gb=500.0,
        aggregate_write_gb_per_sec=25.0,
        model_weights_size_gb=140.0,
        per_pod_read_gb_per_sec=2.0,
    )
    check(
        "500 GB checkpoint at 25 GB/s takes 20.0s; 140 GB model weights at 2 GB/s takes 70.0s",
        t == {"checkpoint_stall_sec": 20.0, "weight_load_cold_start_sec": 70.0},
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
