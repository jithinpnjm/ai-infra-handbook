#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.35: Multicluster and fleet management."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from multicluster_fleet_dispatcher import (
    audit_fleet_cidrs_and_silo_overhead,
    plan_applicationset_ring_rollout,
    simulate_multikueue_dispatch,
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
    # 1. Section 5: Kueue MultiKueue Incremental dispatcher (batches of 3, 5m interval, ordered spill-over)
    workers = [
        {"name": "onprem-dgx-1", "free_gpus": 8},
        {"name": "onprem-dgx-2", "free_gpus": 16},
        {"name": "gke-reserved-us", "free_gpus": 0},
        {"name": "coreweave-burst-eu", "free_gpus": 64},  # Round 2!
    ]
    inc = simulate_multikueue_dispatch(
        ordered_worker_clusters=workers,
        job_gpu_demand=32,
        dispatcher_mode="Incremental",
        incremental_batch_size=3,
    )
    all_once = simulate_multikueue_dispatch(
        ordered_worker_clusters=workers,
        job_gpu_demand=32,
        dispatcher_mode="AllAtOnce",
    )
    check(
        "MultiKueue Incremental spills over to Round 2 ('coreweave-burst-eu', 5m wait) when Round 1 on-prem/reserved clusters lack 32 GPUs",
        inc["rounds_taken"] == 2
        and inc["elapsed_wait_minutes"] == 5
        and inc["admitted_cluster"] == "coreweave-burst-eu"
        and all_once["rounds_taken"] == 1
        and len(all_once["remote_workloads_cleaned_up"]) == 3,
    )

    # 2. Section 4 & 9: ApplicationSet label selector + ring-ordered rollout
    fleet = [
        {"name": "prod-us-east", "gpu": "true", "ring": "prod-ring-2"},
        {"name": "canary-gpu", "gpu": "true", "ring": "canary"},
        {"name": "cpu-only-mgmt", "gpu": "false", "ring": "canary"},
        {"name": "prod-eu-west", "gpu": "true", "ring": "prod-ring-1"},
        {"name": "staging-gpu", "gpu": "true", "ring": "staging"},
    ]
    waves = plan_applicationset_ring_rollout(fleet, required_labels={"gpu": "true"})
    check(
        "plan_applicationset_ring_rollout filters out cpu-only-mgmt and orders waves canary -> staging -> prod-ring-1 -> prod-ring-2",
        waves
        == [
            ("canary", ["canary-gpu"]),
            ("staging", ["staging-gpu"]),
            ("prod-ring-1", ["prod-eu-west"]),
            ("prod-ring-2", ["prod-us-east"]),
        ],
    )

    # 3. Section 6 & KUR Ch. 21: Fleet Pod CIDR overlap detector + Replicated-Silo minimum-replica overhead
    bad_cidrs = audit_fleet_cidrs_and_silo_overhead(
        {"cluster-a": "10.244.0.0/16", "cluster-b": "10.244.128.0/17"},
        num_regions=8,
        min_ha_replicas_per_region=3,
        global_demand_replicas=10,
    )
    good_cidrs = audit_fleet_cidrs_and_silo_overhead(
        {"cluster-a": "10.240.0.0/16", "cluster-b": "10.241.0.0/16"},
        num_regions=8,
        min_ha_replicas_per_region=3,
        global_demand_replicas=10,
    )
    check(
        "audit_fleet_cidrs_and_silo_overhead catches 10.244.0.0/16 vs 10.244.128.0/17 overlap and computes 24 silo replicas (14 overprovisioned)",
        bad_cidrs["cidrs_valid_for_clustermesh"] is False
        and good_cidrs["cidrs_valid_for_clustermesh"] is True
        and good_cidrs["silo_total_replicas"] == 24
        and good_cidrs["silo_overprovisioned_replicas"] == 14,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
