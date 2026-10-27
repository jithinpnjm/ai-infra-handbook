#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.24: Terraform on GCP and Nebius: networks, GPU VMs and GKE."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terraform_gcp_nebius_validator import (
    generate_multi_nic_gpu_subnets,
    validate_gcp_gpu_node_pool,
    validate_nebius_gpu_fabric_membership,
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
    # 1. Section 3 & 4: GCP GPU VM and GKE node-pool configuration checks
    good_pool = {
        "on_host_maintenance": "TERMINATE",
        "vpc_mtu": 8896,
        "has_reservation": True,
        "max_surge": 0,
        "max_unavailable": 1,
        "consume_reservation_type": "SPECIFIC_RESERVATION",
        "taints": [{"key": "nvidia.com/gpu", "value": "present", "effect": "NO_SCHEDULE"}],
    }
    bad_pool = {
        "on_host_maintenance": "MIGRATE",
        "vpc_mtu": 1460,
        "has_reservation": True,
        "max_surge": 1,
        "max_unavailable": 0,
        "consume_reservation_type": "NO_RESERVATION",
        "taints": [],
    }
    ok_good, _ = validate_gcp_gpu_node_pool(good_pool)
    ok_bad, errs = validate_gcp_gpu_node_pool(bad_pool)
    check(
        "validate_gcp_gpu_node_pool accepts compliant reserved H100 pool and flags MIGRATE, 1460 MTU, max_surge=1, and missing taint",
        ok_good is True and ok_bad is False and len(errs) == 5,
    )

    # 2. Section 2: Multi-NIC GPU rail VPC subnet generator
    rails = generate_multi_nic_gpu_subnets(base_second_octet=40, gpu_nic_count=4)
    check(
        "generate_multi_nic_gpu_subnets creates 4 non-overlapping /20 rail VPCs with MTU 8896",
        len(rails) == 4
        and rails[0]["subnet_cidr"] == "10.40.0.0/20"
        and rails[3]["subnet_cidr"] == "10.43.0.0/20"
        and all(r["mtu"] == 8896 for r in rails),
    )

    # 3. Section 7: Nebius InfiniBand gpu_cluster fabric membership check
    good_nodes = [
        {"name": "gpu-01", "gpu_cluster": {"id": "fab-h100-a"}},
        {"name": "gpu-02", "gpu_cluster": {"id": "fab-h100-a"}},
    ]
    bad_nodes = [
        {"name": "gpu-01", "gpu_cluster": {"id": "fab-h100-a"}},
        {"name": "gpu-02", "gpu_cluster": {"id": "fab-h100-b"}},
    ]
    check(
        "validate_nebius_gpu_fabric_membership passes uniform fabric nodes and flags cross-fabric mismatch",
        validate_nebius_gpu_fabric_membership(good_nodes, "fab-h100-a") == []
        and len(validate_nebius_gpu_fabric_membership(bad_nodes, "fab-h100-a")) == 1,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
