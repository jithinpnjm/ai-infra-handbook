#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.9: The kubelet and the node: CRI, cgroups, QoS classes, probes and eviction."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kubelet_node_managers import (
    evaluate_cpu_manager_static,
    evaluate_topology_manager,
    rank_memory_eviction_victims,
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
    # 1. Section 4: CPU Manager static + full-pcpus-only eligibility
    pool_guar_even, _ = evaluate_cpu_manager_static(qos_class="Guaranteed", cpu_request_m=16000, full_pcpus_only=True)
    pool_guar_odd, _ = evaluate_cpu_manager_static(qos_class="Guaranteed", cpu_request_m=3000, full_pcpus_only=True)
    pool_burst, _ = evaluate_cpu_manager_static(qos_class="Burstable", cpu_request_m=16000, full_pcpus_only=True)
    check(
        "CPU Manager static grants exclusive cores to Guaranteed 16-CPU pod, rejects odd 3-CPU under full-pcpus-only, and places Burstable in shared_pool",
        pool_guar_even == "exclusive_pinned"
        and pool_guar_odd == "rejected_smt"
        and pool_burst == "shared_pool",
    )

    # 2. Section 4: Topology Manager single-numa-node vs best-effort
    ok_1gpu, numa, _ = evaluate_topology_manager("single-numa-node", [{0}, {0}, {0}])
    fail_cross, _, msg = evaluate_topology_manager("single-numa-node", [{0}, {1}])
    ok_8gpu_be, _, _ = evaluate_topology_manager("best-effort", [{0, 1}, {0, 1}])
    check(
        "Topology Manager single-numa-node admits NUMA-0 aligned pod, rejects cross-NUMA pod with TopologyAffinityError, and best-effort admits 8-GPU pod",
        ok_1gpu is True
        and numa == {0}
        and fail_cross is False
        and "TopologyAffinityError" in msg
        and ok_8gpu_be is True,
    )

    # 3. Section 6: Node-pressure memory eviction ordering
    pods = [
        {"name": "guar-train", "request_mi": 64000, "usage_mi": 60000, "priority": 100},
        {"name": "burst-under", "request_mi": 16000, "usage_mi": 12000, "priority": 0},
        {"name": "burst-over-high-prio", "request_mi": 8000, "usage_mi": 20000, "priority": 100},
        {"name": "besteffort-scratch", "request_mi": 0, "usage_mi": 4000, "priority": 0},
        {"name": "burst-over-low-prio", "request_mi": 8000, "usage_mi": 18000, "priority": 0},
    ]
    order = rank_memory_eviction_victims(pods)
    check(
        "rank_memory_eviction_victims evicts over-request low-priority pods first (burst-over-low-prio, besteffort-scratch) and Guaranteed last",
        order == [
            "burst-over-low-prio",
            "besteffort-scratch",
            "burst-over-high-prio",
            "burst-under",
            "guar-train",
        ],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
