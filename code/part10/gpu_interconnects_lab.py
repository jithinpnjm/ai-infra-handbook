#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.6: GPU interconnects: PCIe, NVLink, NVSwitch and NVLink-C2C."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gpu_interconnects import (
    NVLINK_GENERATIONS,
    InterconnectError,
    audit_interconnect_and_placement,
    calc_pcie_link_bandwidth,
    classify_topo_path_label,
    compare_peer_transfer_time,
    evaluate_interconnect_scales,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main() -> int:
    print("=== Chapter 10.6 Lab: GPU Interconnects: PCIe, NVLink, NVSwitch & NVLink-C2C ===")

    # 1. PCIe Bandwidth & Lane Downgrade Math (V7 Ch 2, V7 Lab 01 Step 6, ASP Ch 2 p. 21)
    pcie4 = calc_pcie_link_bandwidth(4, 16, 16)
    pcie5 = calc_pcie_link_bandwidth(5, 16, 16)
    pcie6 = calc_pcie_link_bandwidth(6, 16, 16)
    pcie5_deg = calc_pcie_link_bandwidth(5, 16, 4)
    check(
        "V7 Ch2 & ASP Ch2 p.21: PCIe x16 unidirectional bandwidth is 32 GB/s (Gen4), 64 GB/s (Gen5), and 128 GB/s (Gen6)",
        pcie4["sta_unidirectional_gbps"] == 32.0
        and pcie5["sta_unidirectional_gbps"] == 64.0
        and pcie6["sta_unidirectional_gbps"] == 128.0,
    )
    check(
        "V7 Lab 01 Step 6: PCIe Gen5 x16 downgraded to Width x4 drops unidirectional bandwidth 4x from 64 GB/s to 16 GB/s",
        pcie5_deg["is_downgraded"] is True
        and pcie5_deg["sta_unidirectional_gbps"] == 16.0
        and pcie5_deg["bandwidth_loss_factor"] == 4.0,
    )

    # 2. NVLink Generational Bandwidths (V7 Ch 3 & ASP Ch 2 p. 27)
    check(
        "V7 Ch3: NVLink generations deliver 160 GB/s (P100), 300 GB/s (V100), 600 GB/s (A100), 900 GB/s (H100), and 1,800 GB/s (B200)",
        [NVLINK_GENERATIONS[g].total_bidirectional_gbps for g in (1, 2, 3, 4, 5)]
        == [160.0, 300.0, 600.0, 900.0, 1800.0],
    )
    check(
        "ASP Ch2 p.27: Hopper NVLink 4 uses 18 links x 50 GB/s (900 GB/s) and Blackwell NVLink 5 uses 18 links x 100 GB/s (1.8 TB/s)",
        NVLINK_GENERATIONS[4].max_links_per_gpu == 18
        and NVLINK_GENERATIONS[4].per_link_bidirectional_gbps == 50.0
        and NVLINK_GENERATIONS[5].max_links_per_gpu == 18
        and NVLINK_GENERATIONS[5].per_link_bidirectional_gbps == 100.0,
    )

    # 3. Worked 500 MB AllReduce Transfer Comparison (V2 Ch 10 line 196)
    xfer = compare_peer_transfer_time(0.5, fast_bw_gbps=900.0, slow_bw_gbps=28.0)
    check(
        "V2 Ch10 worked example: 500 MB (0.5 GB) takes 0.56 ms on 900 GB/s NVLink vs 17.86 ms (~18 ms) on 28 GB/s SYS PCIe (>30x slower)",
        xfer["fast_time_ms"] == 0.56
        and xfer["slow_time_ms"] == 17.86
        and xfer["slowdown_factor"] > 30.0,
    )

    # 4. Four Interconnect Tiers & Hardware Cache Coherence Rules (ASP Ch 2 pp. 20-31)
    scales = evaluate_interconnect_scales()
    check(
        "ASP Ch2 p.23: Blackwell NV-HBI die-to-die link is 10,000 GB/s (10 TB/s) and hardware cache-coherent",
        scales["NV_HBI"]["bidirectional_gbps"] == 10000.0
        and scales["NV_HBI"]["hardware_cache_coherent"] is True,
    )
    check(
        "ASP Ch2 pp.21,29: NVLink-C2C (900 GB/s, 450 GB/s/dir) is hardware cache-coherent, whereas GPU-to-GPU NVLink is NOT globally cache-coherent",
        scales["NVLINK_C2C"]["bidirectional_gbps"] == 900.0
        and scales["NVLINK_C2C"]["unidirectional_gbps"] == 450.0
        and scales["NVLINK_C2C"]["hardware_cache_coherent"] is True
        and scales["NVLINK_5_NVSWITCH"]["hardware_cache_coherent"] is False,
    )
    check(
        "ASP Ch2 pp.28,30: NVL72 NVSwitch crossbar provides 129.6 TB/s (~130 TB/s) bisection and NVLink SHARP (NVLS) in-switch reductions",
        scales["NVLINK_5_NVSWITCH"]["nvl72_aggregate_tbps"] == 129.6
        and scales["NVLINK_5_NVSWITCH"]["in_switch_reduction"] == "NVLink SHARP (NVLS)",
    )

    # 5. Topology Matrix Label Classification (`nvidia-smi topo -m`)
    nv18 = classify_topo_path_label("NV18")
    pix = classify_topo_path_label("PIX")
    pxb = classify_topo_path_label("PXB")
    phb = classify_topo_path_label("PHB")
    node = classify_topo_path_label("NODE")
    sys_lbl = classify_topo_path_label("SYS")
    check(
        "V7 Lab 01 Step 4: NV18 parses 18 bonded NVLink lanes and bypasses CPU root complex and NUMA socket links",
        nv18["tier"] == "NVLINK"
        and nv18["nvlink_bonded_lanes"] == 18
        and nv18["crosses_cpu_root_complex"] is False,
    )
    check(
        "V7 Ch2 & Lab 01: PIX and PXB stay on PCIe switches (preferred), whereas PHB and NODE hit CPU root complex and SYS crosses UPI/xGMI",
        pix["preferred_for_tp_or_rdma"] is True
        and pxb["preferred_for_tp_or_rdma"] is True
        and phb["crosses_cpu_root_complex"] is True
        and node["crosses_cpu_root_complex"] is True
        and sys_lbl["crosses_numa_socket"] is True
        and sys_lbl["preferred_for_tp_or_rdma"] is False,
    )

    # 6. Production Placement & Health Audits (V2 Ch 10/Lab 04 & V7 Ch 2-3/Labs 01-02)
    ok_dist = audit_interconnect_and_placement(
        workload_profile="distributed_training",
        gpu_pair_topo_label="NV18",
        gpu_to_nic_topo_label="PIX",
    )
    check(
        "Healthy NV18 GPU pair + PIX rail-aligned NIC + local NUMA CPU passes distributed_training audit",
        ok_dist["passed"] is True and len(ok_dist["findings"]) == 0,
    )

    single_inf = audit_interconnect_and_placement(
        workload_profile="single_gpu_inference",
        gpu_pair_topo_label="SYS",
        gpu_to_nic_topo_label="SYS",
    )
    check(
        "V2 Lab 04 Step 7: Single-GPU inference with local NUMA CPU passes even without NVLink peer group",
        single_inf["passed"] is True,
    )

    l40s_tp = audit_interconnect_and_placement(
        workload_profile="multi_gpu_training",
        gpu_pair_topo_label="SYS",
    )
    check(
        "V7 Ch3 Customer Scenario: Multi-GPU synchronized workload on PCIe-only/SYS pair (e.g., 4x L40S without NVLink) fails audit",
        l40s_tp["passed"] is False
        and any("weak GPU-to-GPU path" in f for f in l40s_tp["findings"]),
    )

    mig_p2p = audit_interconnect_and_placement(
        workload_profile="multi_gpu_training",
        gpu_pair_topo_label="NV18",
        mig_enabled=True,
        p2p_status="CNS",
    )
    check(
        "V7 Lab 02 §14: MIG-enabled GPU (topo -p2p == CNS) blocks P2P even when topo -m shows NV18",
        mig_p2p["passed"] is False
        and any("CNS / MIG" in f for f in mig_p2p["findings"]),
    )

    nvlink_lane_down = audit_interconnect_and_placement(
        workload_profile="multi_gpu_training",
        gpu_pair_topo_label="NV4",
        nvlink_inactive_lanes=1,
    )
    check(
        "V2 Lab 04 §14: Detects silent NVLink sub-link reporting 0.000 GB/s inside an NV4 pair",
        nvlink_lane_down["passed"] is False
        and any("0.000 GB/s" in f for f in nvlink_lane_down["findings"]),
    )

    nvlink_crc = audit_interconnect_and_placement(
        workload_profile="multi_gpu_training",
        gpu_pair_topo_label="NV18",
        nvlink_crc_or_replay_errors=18633,
    )
    check(
        "V7 Lab 02 §14: Detects NVLink replay/CRC errors (18,422 replay + 211 CRC) causing single-pair bandwidth drop",
        nvlink_crc["passed"] is False
        and any("replay/CRC" in f for f in nvlink_crc["findings"]),
    )

    numa_nic_bad = audit_interconnect_and_placement(
        workload_profile="distributed_training",
        gpu_pair_topo_label="NV4",
        gpu_to_nic_topo_label="SYS",
    )
    check(
        "V7 Ch2 Customer Scenario: Distributed job using remote SYS NIC across UPI/xGMI is flagged for K8s Topology Manager",
        numa_nic_bad["passed"] is False
        and any("Topology Manager" in f for f in numa_nic_bad["findings"]),
    )

    sysfs_neg1 = audit_interconnect_and_placement(
        workload_profile="single_gpu_inference",
        gpu_pair_topo_label="X",
        device_sysfs_numa=-1,
    )
    check(
        "V7 Lab 01 Step 5: Flags sysfs numa_node == -1 against silently defaulting to NUMA node 0",
        sysfs_neg1["passed"] is False
        and any("numa_node is -1" in f for f in sysfs_neg1["findings"]),
    )

    remote_cpu = audit_interconnect_and_placement(
        workload_profile="single_gpu_inference",
        gpu_pair_topo_label="X",
        cpu_numa_matches_gpu=False,
    )
    check(
        "V7 Lab 01 Step 1: Flags remote CPU/memory NUMA binding (2.1x SLIT distance 21 vs 10)",
        remote_cpu["passed"] is False
        and any("SLIT distance 21" in f for f in remote_cpu["findings"]),
    )

    pcie_down = audit_interconnect_and_placement(
        workload_profile="distributed_training",
        gpu_pair_topo_label="NV18",
        gpu_to_nic_topo_label="PIX",
        pcie_cap_width=16,
        pcie_sta_width=4,
    )
    check(
        "V7 Lab 01 Step 6: Flags PCIe LnkSta x4 downgrade during node acceptance audit",
        pcie_down["passed"] is False
        and any("PCIe link width downgraded" in f for f in pcie_down["findings"]),
    )

    # 7. Input Validation Checks
    try:
        calc_pcie_link_bandwidth(2, 16, 16)
        check("Rejects unsupported PCIe generation", False)
    except InterconnectError:
        check("Rejects unsupported PCIe generation", True)

    try:
        calc_pcie_link_bandwidth(5, 8, 16)
        check("Rejects sta_width > cap_width", False)
    except InterconnectError:
        check("Rejects sta_width > cap_width", True)

    try:
        compare_peer_transfer_time(0.0, 900.0, 28.0)
        check("Rejects non-positive payload_gb", False)
    except InterconnectError:
        check("Rejects non-positive payload_gb", True)

    try:
        classify_topo_path_label("UNKNOWN_PATH")
        check("Rejects invalid topo -m path label", False)
    except InterconnectError:
        check("Rejects invalid topo -m path label", True)

    try:
        audit_interconnect_and_placement("invalid_profile", "NV18")
        check("Rejects unknown workload_profile", False)
    except InterconnectError:
        check("Rejects unknown workload_profile", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
