#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.19: Cluster deployment models and day-2 operations."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from day2_node_lifecycle_sim import (
    analyze_gpu_fleet_and_etcd_sizing,
    evaluate_node_validation_and_drain,
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
    # 1. Section 3: Node validation gate and PDB-aware kubectl drain
    pods = [
        {"name": "dcgm-exporter-x1", "is_daemonset": True},
        {"name": "trainer-0", "is_daemonset": False, "has_controller": True, "has_emptydir": True, "pdb_disruptions_allowed": 1},
        {"name": "vllm-locked", "is_daemonset": False, "has_controller": True, "has_emptydir": False, "pdb_disruptions_allowed": 0},
    ]
    res_blocked = evaluate_node_validation_and_drain(
        validation_checks={"dcgmi_diag": True, "nccl_allreduce": True, "ib_write_bw": False},
        pods_on_node=pods,
        ignore_daemonsets=True,
        delete_emptydir_data=True,
    )
    res_ok = evaluate_node_validation_and_drain(
        validation_checks={"dcgmi_diag": True, "nccl_allreduce": True, "ib_write_bw": True},
        pods_on_node=pods[:2],
        ignore_daemonsets=True,
        delete_emptydir_data=True,
    )
    check(
        "Validation gate keeps taint when ib_write_bw fails, drain blocks on PDB (disruptionsAllowed=0), and passes when healthy & PDB allows",
        res_blocked["remove_validating_taint"] is False
        and res_blocked["drain_succeeded"] is False
        and len(res_blocked["drain_blockers"]) == 1
        and res_ok["remove_validating_taint"] is True
        and res_ok["drain_succeeded"] is True
        and res_ok["evicted_pods"] == ["trainer-0"],
    )

    # 2. Section 2 & 4 & PK Ch. 2: etcd sizing thresholds (50 / 200 nodes) and GPU allocation vs utilization waste
    fleet = [
        {"name": "gpu-01", "allocatable_gpus": 8, "requested_gpus": 8, "busy_gpus": 7.5},
        {"name": "gpu-02", "allocatable_gpus": 8, "requested_gpus": 8, "busy_gpus": 0.0},  # idle notebook holding 8 GPUs!
        {"name": "gpu-03", "allocatable_gpus": 8, "requested_gpus": 4, "busy_gpus": 3.5},
    ]
    report = analyze_gpu_fleet_and_etcd_sizing(worker_node_count=250, nodes=fleet)
    check(
        "analyze_gpu_fleet_and_etcd_sizing recommends dedicated_required at 250 nodes, detects 8 idle_allocated_gpus, and reports largest_free_block=4",
        report["etcd_recommendation"] == "dedicated_required"
        and report["idle_allocated_gpus"] == 8
        and report["largest_free_block"] == 4,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
