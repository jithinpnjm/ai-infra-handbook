#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.10: Fabric Manager, NVSM and NVLink domains."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fabric_manager_nvlink import (
    CONNECTX_GENERATIONS,
    NVLINK_DOMAINS,
    FabricDomainError,
    audit_fabric_manager_and_nvlink_domain,
    diagnose_three_step_data_path_benchmarks,
    simulate_k8s_single_numa_pod_admission,
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
    print("=== Chapter 10.10 Lab: Fabric Manager, NVSM, NVLink Domains & Data-Path Triage ===")

    # 1. NVLink Domains: PCIe Bridge vs 8-GPU HGX vs 72-GPU NVL72 (V7 Ch 3, V6 Ch 2/7, ASP Ch 2)
    d_bridge = NVLINK_DOMAINS["PCIE_2WAY_BRIDGE"]
    d_hgx_h100 = NVLINK_DOMAINS["HGX_8GPU_H100"]
    d_hgx_b200 = NVLINK_DOMAINS["HGX_8GPU_B200"]
    d_nvl72 = NVLINK_DOMAINS["NVL72_RACK_GB200_GB300"]

    check(
        "V4 Ch4 & V7 Ch3: 2-way PCIe NVLink bridge domain has 0 NVSwitches, 600 GB/s per GPU, and does not use Fabric Manager",
        d_bridge.max_gpus_in_domain == 2
        and d_bridge.nvswitch_asics == 0
        and d_bridge.per_gpu_bidirectional_gbps == 600.0
        and d_bridge.supports_nvls_sharp is False,
    )
    check(
        "V7 Ch3 & V1 Ch4: 8-GPU HGX H100 (4 NVSwitches, 7.2 TB/s) and B200 (14.4 TB/s) require host nvidia-fabricmanager",
        d_hgx_h100.nvswitch_asics == 4
        and d_hgx_h100.aggregate_domain_tbps == 7.2
        and d_hgx_b200.aggregate_domain_tbps == 14.4
        and "nvidia-fabricmanager" in d_hgx_h100.fabric_control_plane,
    )
    check(
        "ASP Ch2 & SuperPOD GB300 RA: 72-GPU NVL72 domain uses 18 NVSwitches across 9 switch trays (129.6 TB/s) managed by NVOS + NMX-M",
        d_nvl72.max_gpus_in_domain == 72
        and d_nvl72.nvswitch_asics == 18
        and d_nvl72.aggregate_domain_tbps == 129.6
        and "NMX-M" in d_nvl72.fabric_control_plane,
    )

    # 2. ConnectX Generations & PCIe Physics (V7 Ch 7)
    cx6 = CONNECTX_GENERATIONS["CONNECTX_6"]
    cx7 = CONNECTX_GENERATIONS["CONNECTX_7"]
    cx8 = CONNECTX_GENERATIONS["CONNECTX_8"]
    check(
        "V7 Ch7: ConnectX-6 (200G HDR = 25 GB/s on PCIe Gen4 QSFP56), ConnectX-7 (400G NDR = 50 GB/s on PCIe Gen5 64 GB/s OSFP), ConnectX-8 (800G XDR = 100 GB/s on PCIe Gen6)",
        cx6.max_rate_gbps == 200
        and cx7.max_rate_gbps == 400
        and cx7.unidirectional_line_rate_gb_per_s == 50.0
        and cx7.pcie_x16_unidirectional_gb_per_s == 64.0
        and cx8.max_rate_gbps == 800,
    )

    # 3. Fabric Manager & NVSwitch Domain Health Audits (V1 Ch 4, V4 Ch 1, V13 Ch 8, BCM 11 §10.13)
    fm_ok = audit_fabric_manager_and_nvlink_domain(
        has_nvswitch=True,
        driver_version="570.59",
        fabricmanager_version="570.59-1",
        fm_service_active=True,
        kubelet_ordered_after_fm=True,
        topo_gpu_pair_label="NV18",
    )
    check(
        "BCM 11 p.670 & V1 Ch4: Matching driver 570.59 + fabricmanager 570.59-1 + active service + systemd ordering passes",
        fm_ok["healthy"] is True and len(fm_ok["findings"]) == 0,
    )

    fm_ver_mismatch = audit_fabric_manager_and_nvlink_domain(
        has_nvswitch=True,
        driver_version="570.59",
        fabricmanager_version="550.90.07-1",
        fm_service_active=True,
        kubelet_ordered_after_fm=True,
    )
    check(
        "V10 Ch4 & V16 Ch4: Flags driver (570.59) vs nvidia-fabricmanager (550.90.07-1) version mismatch",
        fm_ver_mismatch["healthy"] is False
        and any("version mismatch" in f for f in fm_ver_mismatch["findings"]),
    )

    fm_down = audit_fabric_manager_and_nvlink_domain(
        has_nvswitch=True,
        driver_version="570.59",
        fabricmanager_version="570.59-1",
        fm_service_active=False,
        kubelet_ordered_after_fm=True,
        topo_gpu_pair_label="SYS",
    )
    check(
        "V4 Ch1 §5.3 & V13 Ch8: Stopped nvidia-fabricmanager with SYS fallback (~800 GB/s -> ~90 GB/s) is flagged",
        fm_down["healthy"] is False
        and any("NOT active" in f for f in fm_down["findings"])
        and any("instead of 'NV#'" in f for f in fm_down["findings"]),
    )

    fm_boot_race = audit_fabric_manager_and_nvlink_domain(
        has_nvswitch=True,
        driver_version="570.59",
        fabricmanager_version="570.59-1",
        fm_service_active=True,
        kubelet_ordered_after_fm=False,
    )
    check(
        "V1 Ch4 §2.2: Flags missing After=nvidia-fabricmanager.service / Wants= drop-in on containerd/kubelet",
        fm_boot_race["healthy"] is False
        and any("After=nvidia-fabricmanager.service" in f for f in fm_boot_race["findings"]),
    )

    fm_xid74 = audit_fabric_manager_and_nvlink_domain(
        has_nvswitch=True,
        driver_version="570.59",
        fabricmanager_version="570.59-1",
        fm_service_active=True,
        kubelet_ordered_after_fm=True,
        xid_74_count=1,
    )
    check(
        "VL4 Ch3 §220 & V10 Ch9: Flags Xid 74 (NVLink Error) and recommends nvlink --errorcounters, nvsm alerts, and dcgmi diag -r 2",
        fm_xid74["healthy"] is False
        and any("Xid 74" in f for f in fm_xid74["findings"]),
    )

    # 4. Kubernetes Topology Manager `single-numa-node` Pod Admission Math (V7 Ch 8 Customer Scenario)
    tm_16c = simulate_k8s_single_numa_pod_admission(
        numa_nodes=2,
        total_cpus=128,
        total_gpus=8,
        system_reserved_cpus_numa0=0,
        system_reserved_cpus_numa1=2,
        pod_cpu_request=16,
        pod_gpu_request=1,
        pods_requested=8,
    )
    check(
        "V7 Ch8 Customer Scenario: Requesting 16 CPUs + 1 GPU on 128-core (64/NUMA) node with 2 OS cores on NUMA 1 leaves 14 free cores and fails with TopologyAffinityError",
        tm_16c["all_admitted"] is False
        and tm_16c["remaining_free_cpus_per_numa"] == [0, 14]
        and tm_16c["remaining_free_gpus_per_numa"] == [0, 1]
        and any("TopologyAffinityError" in r for r in tm_16c["rejection_reasons"]),
    )

    tm_12c = simulate_k8s_single_numa_pod_admission(
        numa_nodes=2,
        total_cpus=128,
        total_gpus=8,
        system_reserved_cpus_numa0=0,
        system_reserved_cpus_numa1=2,
        pod_cpu_request=12,
        pod_gpu_request=1,
        pods_requested=8,
    )
    check(
        "V7 Ch8 Customer Scenario: Reducing pod CPU request from 16 to 12 cores admits all 8 pods cleanly under single-numa-node",
        tm_12c["all_admitted"] is True
        and tm_12c["admitted_pods"] == 8
        and tm_12c["remaining_free_gpus_per_numa"] == [0, 0],
    )

    # 5. Three-Step Hardware-to-Application Benchmark Hierarchy (V7 Ch 10 & Labs 03-04)
    bench_ok = diagnose_three_step_data_path_benchmarks()
    check(
        "V7 Ch10: Healthy nvbandwidth (56 GB/s), ib_write_bw (392 Gbps), and nccl-tests (NET/IB + GDR) passes",
        bench_ok["healthy"] is True and bench_ok["bottleneck_stage"] == "NONE",
    )

    bench_sm = diagnose_three_step_data_path_benchmarks(
        ib_port_state="Initializing",
        ib_physical_state="LinkUp",
    )
    check(
        "V7 Lab 03 Step 1: Physical state LinkUp + State Initializing isolates to InfiniBand Subnet Manager (OpenSM/UFM)",
        bench_sm["healthy"] is False and bench_sm["bottleneck_stage"] == "STEP_0_SUBNET_MANAGER_INIT",
    )

    bench_cnt = diagnose_three_step_data_path_benchmarks(ib_symbol_or_rcv_errors=14)
    check(
        "V7 Lab 03 Step 2: Rising symbol_error / port_rcv_errors isolates to dirty fiber optic connector or cable",
        bench_cnt["healthy"] is False and bench_cnt["bottleneck_stage"] == "STEP_0_FABRIC_ERROR_COUNTERS",
    )

    bench_pcie = diagnose_three_step_data_path_benchmarks(nvbandwidth_d2h_gbps=28.0)
    check(
        "V7 Ch10 §1: nvbandwidth dropping from 50-60 GB/s to 28 GB/s isolates to PCIe lane downtraining (x16 -> x8)",
        bench_pcie["healthy"] is False and bench_pcie["bottleneck_stage"] == "STEP_1_MOTHERBOARD_PCIE_DOWNTRAIN",
    )

    bench_wire = diagnose_three_step_data_path_benchmarks(ib_write_bw_gbps=195.0)
    check(
        "V7 Ch10 §2: Healthy nvbandwidth + half-rate ib_write_bw (195 Gbps vs 390 Gbps) isolates to physical RDMA link",
        bench_wire["healthy"] is False and bench_wire["bottleneck_stage"] == "STEP_2_PHYSICAL_RDMA_WIRE",
    )

    bench_sock = diagnose_three_step_data_path_benchmarks(nccl_debug_transport="NET/Socket")
    check(
        "V7 Ch10 §3: Healthy ib_write_bw + NCCL_DEBUG=INFO 'NET/Socket' isolates to TCP socket fallback",
        bench_sock["healthy"] is False and bench_sock["bottleneck_stage"] == "STEP_3A_NCCL_TCP_SOCKET_FALLBACK",
    )

    bench_gdr = diagnose_three_step_data_path_benchmarks(nccl_gdr_enabled=False, nccl_bus_bw_gbps=6.25)
    check(
        "V7 Ch5 Customer Scenario: Healthy ib_write_bw + disabled GPUDirect RDMA (~50 Gbps / 6.25 GB/s) isolates to Host Bounce Buffer (nvidia-peermem / ACS / Large BAR)",
        bench_gdr["healthy"] is False and bench_gdr["bottleneck_stage"] == "STEP_3B_GPUDIRECT_RDMA_BOUNCE_BUFFER",
    )

    bench_msg = diagnose_three_step_data_path_benchmarks(app_allreduce_msg_kb=256.0, ddp_bucket_cap_mb=25)
    check(
        "V7 Ch10 Customer Scenario: Healthy nccl-tests + slow PyTorch job with 256 KB messages isolates to DDP bucket_cap_mb (25 MB -> 50 MB)",
        bench_msg["healthy"] is False and bench_msg["bottleneck_stage"] == "STEP_4_APPLICATION_SMALL_MESSAGE_LATENCY",
    )

    # 6. Input Validation Checks
    try:
        audit_fabric_manager_and_nvlink_domain(True, "", "570.59-1", True, True)
        check("Rejects empty driver_version in Fabric Manager auditor", False)
    except FabricDomainError:
        check("Rejects empty driver_version in Fabric Manager auditor", True)

    try:
        simulate_k8s_single_numa_pod_admission(numa_nodes=0)
        check("Rejects non-positive numa_nodes in Topology Manager simulator", False)
    except FabricDomainError:
        check("Rejects non-positive numa_nodes in Topology Manager simulator", True)

    try:
        simulate_k8s_single_numa_pod_admission(numa_nodes=3, total_cpus=128, total_gpus=8)
        check("Rejects total_cpus/total_gpus not divisible by numa_nodes", False)
    except FabricDomainError:
        check("Rejects total_cpus/total_gpus not divisible by numa_nodes", True)

    try:
        diagnose_three_step_data_path_benchmarks(nvbandwidth_d2h_gbps=0.0)
        check("Rejects non-positive nvbandwidth_d2h_gbps", False)
    except FabricDomainError:
        check("Rejects non-positive nvbandwidth_d2h_gbps", True)

    try:
        diagnose_three_step_data_path_benchmarks(app_allreduce_msg_kb=-10.0)
        check("Rejects negative app_allreduce_msg_kb", False)
    except FabricDomainError:
        check("Rejects negative app_allreduce_msg_kb", True)

    check(
        "ConnectX-7 400 Gbps line rate (50.0 GB/s) is <= PCIe Gen5 x16 unidirectional payload (64.0 GB/s)",
        cx7.unidirectional_line_rate_gb_per_s <= cx7.pcie_x16_unidirectional_gb_per_s,
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
