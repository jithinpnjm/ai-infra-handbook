#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.2: Cluster anatomy: head, login, compute, storage and management nodes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cluster_anatomy import (
    REQUIRED_RUNBOOK_COLUMNS,
    plan_cluster_power_and_ports,
    scheduler_declared_cores,
    torus_3d_max_hops,
    validate_runbook_schema,
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
    # 1. Section 3: 3D torus maximum hop formula [N/2] + [M/2] + [K/2] (SCL Ch. 4)
    check(
        "torus_3d_max_hops computes [N/2]+[M/2]+[K/2] = 4+4+4 = 12 hops for 8x8x8 and 2+3+4 = 9 hops for 5x7x9",
        torus_3d_max_hops(8, 8, 8) == 12 and torus_3d_max_hops(5, 7, 9) == 9,
    )

    # 2. Section 4: HyperThreading BIOS enabled vs scheduler physical core declaration trick (SCL Ch. 4)
    cores = scheduler_declared_cores(sockets=2, physical_cores_per_socket=64, threads_per_core=2)
    check(
        "scheduler_declared_cores exposes 256 OS logical CPUs while declaring 128 physical cores to Slurm",
        cores["os_logical_cpus"] == 256
        and cores["scheduler_declared_cores"] == 128
        and cores["reserved_daemon_threads"] == 128,
    )

    # 3. Section 5 & 9: 32-node GPU cluster sizing (256 compute ports, 36 mgmt ports, 352.0 kW with 10% headroom) + runbook schema
    plan = plan_cluster_power_and_ports(
        compute_nodes=32, gpus_per_node=8, kw_per_compute_node=10.0, login_nodes=2, head_nodes=2, headroom_fraction=0.10
    )
    check(
        "plan_cluster_power_and_ports (256 fabric ports, 36 OOB ports, 352.0 kW) and 8-column runbook validator pass",
        plan["compute_fabric_ports"] == 256
        and plan["oob_bmc_ports"] == 36
        and plan["raw_compute_kw"] == 320.0
        and plan["budget_kw_with_headroom"] == 352.0
        and validate_runbook_schema(list(REQUIRED_RUNBOOK_COLUMNS) + ["rollback"]) is True
        and validate_runbook_schema(["phase", "action"]) is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
