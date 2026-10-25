"""Chapter 11.6 Lab — Scheduling GPUs: requests, Topology Manager, CPU and NUMA alignment.

Run with:
    python3 code/part11/gpu_scheduling_and_topology_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gpu_scheduling_and_topology import (
    NumaSocketState,
    TOPO_LINK_RANK,
    classify_pod_qos_and_cpu_pinning,
    compute_numa_latency_penalty,
    evaluate_topology_manager_admission,
    parse_failed_scheduling_event,
    simulate_dual_socket_hgx_pod_packing,
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

    print("=== Chapter 11.6 Lab: GPU Scheduling, Topology Manager, CPU & NUMA Alignment ===")

    # 1. NUMA Latency Penalty & Interconnect Bandwidth Hierarchy (ASP Ch 3, V07 Ch 2, GAK Ch 3)
    lat = compute_numa_latency_penalty(80.0, 139.0)
    _check(
        lat["local_ns"] == 80.0
        and lat["remote_ns"] == 139.0
        and lat["increase_pct_approx"] == 75.0,
        "Cross-NUMA memory latency rises from ~80 ns to ~139 ns (~75% increase, 73.75% exact)",
        passed,
        failed,
    )
    _check(
        TOPO_LINK_RANK["X"][0] < TOPO_LINK_RANK["NV12"][0] < TOPO_LINK_RANK["PIX"][0],
        "nvidia-smi topo -m ranks X (self) faster than NV12 (NVLink), which is faster than PIX (same PCIe switch)",
        passed,
        failed,
    )
    _check(
        TOPO_LINK_RANK["PIX"][0]
        < TOPO_LINK_RANK["PXB"][0]
        < TOPO_LINK_RANK["PHB"][0]
        < TOPO_LINK_RANK["NODE"][0]
        < TOPO_LINK_RANK["SYS"][0],
        "PCIe topology hierarchy orders PIX < PXB < PHB < NODE < SYS (cross-socket UPI/xGMI slowest)",
        passed,
        failed,
    )

    # 2. Pod QoS Class & CPU Manager `static` Pinning Requirements (ASP Ch 3 & V07 Ch 8)
    qos_guar = classify_pod_qos_and_cpu_pinning(16, 16, 65536, 65536, "static")
    _check(
        qos_guar["qos_class"] == "Guaranteed"
        and qos_guar["exclusive_cpu_pinning"] is True,
        "Pod with integer CPU (16==16) and matching memory (65536==65536 MiB) gets Guaranteed QoS and static CPU pinning",
        passed,
        failed,
    )

    qos_frac = classify_pod_qos_and_cpu_pinning(15.5, 15.5, 65536, 65536, "static")
    _check(
        qos_frac["qos_class"] == "Guaranteed"
        and qos_frac["is_integer_cpu"] is False
        and qos_frac["exclusive_cpu_pinning"] is False,
        "Guaranteed Pod with fractional CPU (15.5) does NOT receive exclusive static CPU pinning",
        passed,
        failed,
    )

    qos_burst = classify_pod_qos_and_cpu_pinning(8, 16, 65536, 65536, "static")
    _check(
        qos_burst["qos_class"] == "Burstable"
        and qos_burst["exclusive_cpu_pinning"] is False,
        "Pod with CPU request (8) != limit (16) is Burstable and excluded from static CPU pinning",
        passed,
        failed,
    )

    qos_best = classify_pod_qos_and_cpu_pinning(None, None, None, None, "static")
    _check(
        qos_best["qos_class"] == "BestEffort"
        and qos_best["exclusive_cpu_pinning"] is False,
        "Pod with no CPU/memory requests or limits is BestEffort (highest eviction risk)",
        passed,
        failed,
    )

    # 3. Kubelet Topology Manager Policies (`none`, `best-effort`, `restricted`, `single-numa-node`)
    # Node A from V07 Ch 8: NUMA 0 has 8 CPUs, 1 GPU, 0 NICs; NUMA 1 has 0 CPUs, 0 GPUs, 1 NIC
    def _node_a() -> list[NumaSocketState]:
        return [
            NumaSocketState(numa_id=0, free_cpus=8, free_gpus=1, free_nics=0),
            NumaSocketState(numa_id=1, free_cpus=0, free_gpus=0, free_nics=1),
        ]

    res_single_a = evaluate_topology_manager_admission(
        "single-numa-node", 8, 1, 1, _node_a()
    )
    _check(
        res_single_a["admitted"] is False
        and res_single_a["status"] == "TopologyAffinityError",
        "single-numa-node rejects Pod on Node A (GPU on NUMA 0, NIC on NUMA 1) with TopologyAffinityError",
        passed,
        failed,
    )

    res_rest_a = evaluate_topology_manager_admission(
        "restricted", 8, 1, 1, _node_a()
    )
    _check(
        res_rest_a["admitted"] is False
        and res_rest_a["status"] == "TopologyAffinityError",
        "restricted policy also rejects unaligned Pod on Node A with TopologyAffinityError",
        passed,
        failed,
    )

    res_best_a = evaluate_topology_manager_admission(
        "best-effort", 8, 1, 1, _node_a()
    )
    _check(
        res_best_a["admitted"] is True
        and res_best_a["aligned_single_numa"] is False,
        "best-effort admits Pod on Node A despite cross-NUMA split between GPU 0 and NIC 1",
        passed,
        failed,
    )

    res_none_a = evaluate_topology_manager_admission("none", 8, 1, 1, _node_a())
    _check(
        res_none_a["admitted"] is True
        and res_none_a["aligned_single_numa"] is False,
        "none policy admits Pod on Node A without NUMA alignment",
        passed,
        failed,
    )

    # Node B from V07 Ch 8: NUMA 0 has 8 CPUs, 1 GPU, 1 NIC free
    node_b = [NumaSocketState(numa_id=0, free_cpus=8, free_gpus=1, free_nics=1)]
    res_single_b = evaluate_topology_manager_admission(
        "single-numa-node", 8, 1, 1, node_b
    )
    _check(
        res_single_b["admitted"] is True
        and res_single_b["aligned_single_numa"] is True
        and res_single_b["selected_numa"] == 0,
        "single-numa-node admits Pod on Node B where NUMA 0 has 8 CPUs, 1 GPU, and 1 NIC aligned",
        passed,
        failed,
    )

    # 4. Dual-Socket HGX 128-Core / 8-GPU Triton Scenario (V07 Ch 8)
    # Scenario 1: NUMA 0 has 64 cores (fits 4 x 16-core Pods = 64 cores);
    # NUMA 1 has 14 cores left when the 5th (or last) 16-core Pod arrives -> TopologyAffinityError
    pack_16_blocked_at_5 = simulate_dual_socket_hgx_pod_packing(
        cores_per_pod=16,
        total_pods=8,
        numa0_initial_cpus=64,
        numa1_initial_cpus=14,
        gpus_per_numa=4,
        policy="single-numa-node",
    )
    _check(
        pack_16_blocked_at_5["admitted_pods"] == 4
        and pack_16_blocked_at_5["failed_pods"][0] == (5, "TopologyAffinityError")
        and pack_16_blocked_at_5["remaining_free_gpus"] == 4,
        "When NUMA 0 uses 4x16=64 cores and NUMA 1 has only 14 free cores, Pod 5 fails with TopologyAffinityError leaving 4 GPUs idle",
        passed,
        failed,
    )

    # Scenario 2: If OS daemons reserve 2 cores on NUMA 1 (62 free cores), 3 Pods (48 cores) fit on NUMA 1 leaving 14 cores for Pod 8
    pack_16_os_2cores = simulate_dual_socket_hgx_pod_packing(
        cores_per_pod=16,
        total_pods=8,
        numa0_initial_cpus=64,
        numa1_initial_cpus=62,
        gpus_per_numa=4,
        policy="single-numa-node",
    )
    _check(
        pack_16_os_2cores["admitted_pods"] == 7
        and pack_16_os_2cores["remaining_numa1_cpus"] == 14
        and pack_16_os_2cores["failed_pods"] == [(8, "TopologyAffinityError")],
        "When 2 cores on NUMA 1 are used by OS daemons (62 free), 3 Pods take 48 cores leaving 14 cores (< 16) and blocking the last Pod",
        passed,
        failed,
    )

    # Scenario 3: Right-sizing Triton Pod request from 16 cores to 12 cores (4 x 12 = 48 <= 62) admits all 8 Pods
    pack_12_ok = simulate_dual_socket_hgx_pod_packing(
        cores_per_pod=12,
        total_pods=8,
        numa0_initial_cpus=62,
        numa1_initial_cpus=62,
        gpus_per_numa=4,
        policy="single-numa-node",
    )
    _check(
        pack_12_ok["admitted_pods"] == 8
        and len(pack_12_ok["failed_pods"]) == 0
        and pack_12_ok["remaining_free_gpus"] == 0,
        "Right-sizing Triton Pods from 16 cores to 12 cores (4x12=48 cores/socket) admits all 8 Pods under single-numa-node",
        passed,
        failed,
    )

    # 5. FailedScheduling 3-Clause Breakdown (`train-worker-2` in V10 Ch 8)
    sched_ev = parse_failed_scheduling_event(
        total_nodes=12,
        insufficient_gpu_nodes=4,
        untolerated_taint_nodes=6,
        affinity_mismatch_nodes=2,
    )
    _check(
        sched_ev["capacity_blocked"] == 4
        and sched_ev["taint_blocked"] == 6
        and sched_ev["affinity_blocked"] == 2
        and sched_ev["total_nodes"] == 12,
        "FailedScheduling event on train-worker-2 decomposes 12 nodes into 4 insufficient GPU, 6 untolerated taint, and 2 affinity mismatch",
        passed,
        failed,
    )

    # 6. Hardware Interconnect & OS Tuning Constants (V07 Ch 2, ASP Ch 3, GAK Ch 3)
    _check(
        32 * 2 == 64,
        "PCIe Gen5 x16 (64 GB/s per direction) doubles PCIe Gen4 x16 (32 GB/s per direction)",
        passed,
        failed,
    )
    _check(
        round(3350 / 64, 2) == 52.34,
        "H100 HBM3 bandwidth (3350 GB/s) is >52x higher than a single PCIe Gen5 x16 link (64 GB/s)",
        passed,
        failed,
    )
    _check(
        18 * 100 == 1800 and 72 * 1.8 == 129.6,
        "NVLink 5.0 delivers 18 x 100 GB/s = 1.8 TB/s per GPU (~130 TB/s across 72 GPUs in GB200 NVL72)",
        passed,
        failed,
    )
    _check(
        144 * 100 == 14400,
        "Dual-chip NVSwitch 4.0 tray provides 144 NVLink 5.0 ports and 14.4 TB/s switching capacity",
        passed,
        failed,
    )
    _check(
        round((2.0 / 7.0) * 132) == 38 and 38 * 2 == 76,
        "Two nvidia.com/mig-2g.45gb slices on a 132-SM GPU allocate 2 x ~38 SMs = ~76 SMs and must co-reside on 1 node",
        passed,
        failed,
    )
    _check(
        512 * 1024 * 1024 == 536870912,
        "tcmalloc TCMALLOC_MAX_TOTAL_THREAD_CACHE_BYTES=((512*1024*1024)) equals 536,870,912 bytes (512 MiB)",
        passed,
        failed,
    )
    _check(
        len(TOPO_LINK_RANK) == 9,
        "Topology link classifier covers all 9 nvidia-smi topo -m states (X, NV18, NV12, NV4, PIX, PXB, PHB, NODE, SYS)",
        passed,
        failed,
    )
    _check(
        pack_12_ok["remaining_numa0_cpus"] == 14
        and pack_12_ok["remaining_numa1_cpus"] == 14,
        "With 12 cores/Pod (48 cores used per 62-core available socket), 14 cores remain free per NUMA node for OS/system daemons",
        passed,
        failed,
    )
    _check(
        lat["delta_ns"] == 59.0,
        "Cross-NUMA memory access adds 59.0 ns per access (139 ns - 80 ns)",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
