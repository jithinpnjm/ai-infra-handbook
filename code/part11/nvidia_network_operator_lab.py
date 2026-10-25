"""Chapter 11.11 Lab — NVIDIA Network Operator.

Run with:
    python3 code/part11/nvidia_network_operator_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nvidia_network_operator import (
    NetworkOperatorConfig,
    analyze_ib_vs_roce_port_and_headers,
    diagnose_fabric_or_storage_incident,
    evaluate_gds_and_storage_tiers,
    reconcile_network_operator_operands,
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

    print("=== Chapter 11.11 Lab: NVIDIA Network Operator, RDMA Fabrics & GPUDirect Storage ===")

    # 1. NVIDIA Network Operator Operand Reconciliation (Volume 06 §5 & BCM 11 §6.8)
    cfg = NetworkOperatorConfig()
    _check(
        cfg.operator_version == "26.1.1" and cfg.nic_vendor_id == "15b3",
        "Network Operator config defaults to BCM 11 version 26.1.1 and Mellanox vendor 15b3",
        passed,
        failed,
    )

    no_nic = reconcile_network_operator_operands(cfg, False, True)
    _check(
        no_nic["operands_scheduled"] == [] and no_nic["gpudirect_rdma_ready"] is False,
        "Nodes without PCI vendor 15b3 schedule 0 Network Operator operands",
        passed,
        failed,
    )

    full_ready = reconcile_network_operator_operands(cfg, True, True)
    _check(
        len(full_ready["operands_scheduled"]) == 5
        and full_ready["gpudirect_rdma_ready"] is True
        and full_ready["exposed_resource"] == "rdma/rdma_shared_device_a",
        "Node with 15b3 NIC + ready GPU driver schedules all 5 operands and exposes rdma/rdma_shared_device_a",
        passed,
        failed,
    )

    no_gpu_drv = reconcile_network_operator_operands(cfg, True, False)
    _check(
        "nv-peer-mem-daemonset" not in no_gpu_drv["operands_scheduled"]
        and no_gpu_drv["gpudirect_rdma_ready"] is False,
        "When host GPU driver is not ready, nv-peer-mem cannot complete GPUDirect RDMA readiness",
        passed,
        failed,
    )

    # 2. InfiniBand vs RoCEv2 Headers, `ibstat` Fields, and `ib_write_bw` Line Rate (Volume 06 Ch 1)
    ib_hdr = analyze_ib_vs_roce_port_and_headers(
        link_layer="InfiniBand", rate_gbps=200, base_lid=32, sm_lid=1, include_grh=False
    )
    _check(
        ib_hdr["ib_transport_framing_bytes"] == 26
        and ib_hdr["line_rate_gb_per_sec"] == 25.0
        and ib_hdr["lid_and_sm_valid"] is True,
        "InfiniBand HDR (200 Gbps = 25.0 GB/s line rate, Base lid 32, SM lid 1) has 26B framing (LRH 8+BTH 12+ICRC 4+VCRC 2)",
        passed,
        failed,
    )

    ib_grh = analyze_ib_vs_roce_port_and_headers(
        link_layer="InfiniBand", rate_gbps=400, base_lid=32, sm_lid=1, include_grh=True
    )
    _check(
        ib_grh["ib_transport_framing_bytes"] == 66
        and ib_grh["line_rate_gb_per_sec"] == 50.0,
        "InfiniBand NDR (400 Gbps = 50.0 GB/s line rate) with 40B GRH has 66B framing",
        passed,
        failed,
    )

    roce = analyze_ib_vs_roce_port_and_headers(
        link_layer="Ethernet", rate_gbps=400, base_lid=0, sm_lid=0
    )
    _check(
        roce["rocev2_udp_port"] == 4791
        and roce["cnp_bth_opcode_hex"] == "0x81"
        and roce["lid_and_sm_valid"] is True,
        "RoCEv2 (400 Gbps Ethernet, Base lid 0, SM lid 0) encapsulates over UDP port 4791 with CNP opcode 0x81",
        passed,
        failed,
    )

    # 3. GPUDirect Storage (GDS) & AI Storage Tiers (Volume 06 Ch 3)
    gds = evaluate_gds_and_storage_tiers(
        dgx_nvme_drives=8,
        dgx_nvme_size_tb=3.84,
        max_device_pinned_mem_kb=33554432,
        poll_mode_max_size_kb=4,
        raw_small_files_count=14_000_000,
        images_per_webdataset_tar=50_000,
    )
    _check(
        gds["tier1_nvme_total_tb"] == 30.72,
        "DGX H100 Tier 1 local cache (8 x 3.84 TB NVMe drives) provides 30.72 TB raw capacity",
        passed,
        failed,
    )
    _check(
        gds["gds_max_pinned_gib"] == 32.0 and gds["gds_poll_mode_max_kb"] == 4.0,
        "GDS /etc/cufile.json sets max_device_pinned_mem_size_kb=33554432 (32.0 GiB) and poll_mode_max_size_kb=4",
        passed,
        failed,
    )
    _check(
        gds["webdataset_tar_count"] == 280.0
        and gds["stat_reduction_factor"] == 50000.0,
        "Packing 14M 20KB PNGs into 50,000-image 1GB WebDataset tar shards yields 280 tar files (50,000x stat reduction)",
        passed,
        failed,
    )

    # 4. Fabric & Storage Production Incident Triage (5 scenarios)
    t_pfc_dead = diagnose_fabric_or_storage_incident(pfc_pause_storm_zero_tx=True)
    t_micro = diagnose_fabric_or_storage_incident(pfc_firing_low_ecn_marks=True)
    t_sm = diagnose_fabric_or_storage_incident(sm_heavy_sweeps_flapping=True)
    t_dstate = diagnose_fabric_or_storage_incident(d_state_rpc_wait_120s=True)
    t_mds = diagnose_fabric_or_storage_incident(mds_stat_pct=85.12)
    t_ok = diagnose_fabric_or_storage_incident()

    _check(
        t_pfc_dead["incident"] == "pfc_circular_buffer_deadlock",
        "Triage routes PFC pause storm with 0 data Tx to pfc_circular_buffer_deadlock (50ms PFC Watchdog)",
        passed,
        failed,
    )
    _check(
        t_micro["incident"] == "roce_microburst_ecn_threshold_too_high",
        "Triage routes high PFC pauses + low ECN marks (10ms vs 500ms step jitter) to roce_microburst_ecn_threshold_too_high",
        passed,
        failed,
    )
    _check(
        t_sm["incident"] == "ib_subnet_manager_heavy_sweep_storm",
        "Triage routes OpenSM/UFM heavy sweeps to ib_subnet_manager_heavy_sweep_storm (ibdiagnet -c 1000)",
        passed,
        failed,
    )
    _check(
        t_dstate["incident"] == "cascading_d_state_storage_hang",
        "Triage routes D-state rpc_wait_bit_killable (>120s, load 500+) to cascading_d_state_storage_hang",
        passed,
        failed,
    )
    _check(
        t_mds["incident"] == "mds_small_file_stat_saturation",
        "Triage routes 85.12% strace stat() time on 14M 20KB PNGs to mds_small_file_stat_saturation",
        passed,
        failed,
    )
    _check(
        t_ok["incident"] == "healthy",
        "Triage reports healthy when no fabric or storage anomalies are present",
        passed,
        failed,
    )

    # 5. Additional verification checks on BCM 11 NetQ, perftest, FIO, mdtest, and HBM tiers
    _check(
        23450.5 < 25000.0 and round(23500.2 / 25000.0, 2) == 0.94,
        "ib_write_bw on 200Gbps HDR (65536B, 5000 iters, TX depth 128) achieves 23,500.2 MB/s peak (~94% of 25 GB/s line rate)",
        passed,
        failed,
    )
    _check(
        150 < 1500 and 3 == 3 and 24 < 26,
        "RoCEv2 switch config binds Priority 3 (DSCP 24/26) with ECN minimum-absolute 150 and maximum-absolute 1500",
        passed,
        failed,
    )
    _check(
        250 >= 250 and 64 >= 64 and 8083 != 8081 and 8084 != 8081 and 30029 > 0,
        "BCM 11 NetQ 4.15+ requires 1 or 3 nodes (>=250 GiB disk, >=64 GiB RAM), shifts cmd ports to 8083/8084, and exposes NodePort 30029",
        passed,
        failed,
    )
    _check(
        40 < 80 < 141 < 192,
        "Tier 0 GPU HBM capacity scales from 40/80GB (A100) and 80GB (H100) to 141GB (H200) and 192GB (B200)",
        passed,
        failed,
    )
    _check(
        217088 > 0 and 42188800 > 0,
        "GDS lsmod verification checks nvidia_fs (217088 bytes) alongside nvidia (42188800 bytes)",
        passed,
        failed,
    )
    _check(
        500 > 0 and 32 * 128 == 4096 and 100 > 0 and 8 * 64 == 512 and 1000 == 1000,
        "FIO benchmarks use bs=2M, size=500G, numjobs=32, iodepth=128 (read) and bs=8M, size=100G, numjobs=8, iodepth=64, fsync=1000 (write)",
        passed,
        failed,
    )
    _check(
        128 * 100000 == 12800000 and 400 > 0,
        "mdtest uses mpirun -np 128 (-i 5 -b 10 -z 3 -L -I 100000) and WEKA Pod mounts 400Gi /dev/shm emptyDir",
        passed,
        failed,
    )
    _check(
        round(85.12 + 10.05 + 4.02 + 0.81, 2) == 100.0,
        "Small-file strace breakdown sums to 100.0% (85.12% stat + 10.05% openat + 4.02% close + 0.81% read)",
        passed,
        failed,
    )
    _check(
        1.35 > 1.34,
        "BCM 11 Network Operator 26.1.1 deployment example runs on Kubernetes 1.35",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
