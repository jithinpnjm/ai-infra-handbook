#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.34: GKE for GPU workloads: setup, node pools and quotas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gke_gpu_pool_planner import (
    classify_gke_gpu_capacity_error,
    evaluate_gke_gpu_node_pool_config,
    validate_gpu_pool_upgrade_surge,
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
    # 1. Section 4, 7, 8 & GAK Ch. 3: GKE GPU node pool config & MIG 2x A100 x 7 slices = 14 units
    ok_mig, mig_info, _ = evaluate_gke_gpu_node_pool_config(
        {
            "image_type": "COS_CONTAINERD",
            "gpu_driver_version": "default",
            "gpu_count": 2,
            "mig_slices_per_gpu": 7,
            "additional_node_networks": 4,
            "reservation_affinity": "specific",
            "reservation_name": "my-a100-res",
        }
    )
    bad_cfg, _, cfg_errs = evaluate_gke_gpu_node_pool_config(
        {
            "image_type": "UBUNTU_CONTAINERD",
            "gpu_driver_version": "latest",  # requires COS!
            "gpu_operator_manages_driver": True,  # requires disabled!
            "additional_node_networks": 8,  # > 7!
            "reservation_affinity": "specific",  # missing reservation_name!
        }
    )
    check(
        "evaluate_gke_gpu_node_pool_config computes 14 MIG slices (2 GPUs x 7) and catches 4 invalid GKE flag combinations",
        ok_mig is True
        and mig_info["allocatable_gpu_units_per_node"] == 14
        and bad_cfg is False
        and len(cfg_errs) == 4,
    )

    # 2. Section 5 & 12: QUOTA_EXCEEDED vs ZONE_RESOURCE_POOL_EXHAUSTED stockout
    q_err = classify_gke_gpu_capacity_error("QUOTA_EXCEEDED: Quota 'NVIDIA_H100_GPUS' exceeded")
    s_err = classify_gke_gpu_capacity_error("ZONE_RESOURCE_POOL_EXHAUSTED: does not have enough resources")
    check(
        "classify_gke_gpu_capacity_error distinguishes project_quota (QUOTA_EXCEEDED) from zone_stockout (ZONE_RESOURCE_POOL_EXHAUSTED)",
        q_err["category"] == "project_quota" and s_err["category"] == "zone_stockout",
    )

    # 3. Section 9: GPU node pool upgrade surge failure when spare reservation/quota is 0
    surge_ok, _ = validate_gpu_pool_upgrade_surge(
        pool_nodes=8,
        spare_quota_or_reservation_nodes=0,
        max_surge_upgrade=1,
        max_unavailable_upgrade=0,
    )
    unavail_ok, _ = validate_gpu_pool_upgrade_surge(
        pool_nodes=8,
        spare_quota_or_reservation_nodes=0,
        max_surge_upgrade=0,
        max_unavailable_upgrade=1,
    )
    check(
        "validate_gpu_pool_upgrade_surge rejects max-surge-upgrade=1 when spare capacity is 0 and approves max-surge=0 / max-unavailable=1",
        surge_ok is False and unavail_ok is True,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
