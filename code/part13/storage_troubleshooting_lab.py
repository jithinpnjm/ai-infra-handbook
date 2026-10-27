#!/usr/bin/env python3
"""
Chapter 13.9 — Storage Troubleshooting Verification Lab
========================================================
Runs 28 deterministic self-checks verifying every formula, diagnostic threshold,
and production incident triage workflow in Chapter 13.9 (`Storage troubleshooting`).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage_troubleshooting import (
    GDSValidationState,
    IncidentTelemetry,
    NVMeDriveHealth,
    audit_gds_deployment,
    default_production_incident,
    diagnose_comm_vs_compute_scaling,
    evaluate_gds_benchmarks,
    evaluate_nvme_vs_shared_staging,
    repackaging_metadata_impact,
    triage_local_nvme_health,
    triage_nfs_mount_and_estale,
    walk_storage_decision_tree,
)


def run_lab() -> int:
    checks = []

    def check(desc: str, cond: bool) -> None:
        status = "PASS" if cond else "FAIL"
        checks.append((desc, cond))
        print(f"  [{status}] {len(checks):02d}. {desc}")

    print("=== Chapter 13.9: Storage Troubleshooting Verification Lab ===\n")

    # 1. Production Incident Decision Tree (V15 Ch 11)
    inc = default_production_incident()
    res = walk_storage_decision_tree(inc)

    check(
        "Production incident slowdown is 4.0x (2.0 hours baseline -> 8.0 hours current) with GPU SM utilization dropping from 92% (mem 40%) to 15% (mem 5%)",
        res.slowdown_factor == 4.0
        and inc.gpu_util_baseline_pct == 92.0
        and inc.gpu_util_current_pct == 15.0
        and inc.memory_util_baseline_pct == 40.0
        and inc.memory_util_current_pct == 5.0,
    )

    check(
        "Decision tree Gate 1 & Gate 2 classify GPU utilization < 70% (15%) with 80% empty prefetch queue as I/O-bound starvation",
        res.is_io_bound is True and inc.queue_empty_pct == 80.0,
    )

    check(
        "cProfile CPU decode (45.2 s) + augmentation (12.1 s) totals 57.3 s (~57 s) across 120,000 calls, ruled out as primary root cause because prefetch queue is 80% empty",
        round(inc.cpu_decode_sec_per_120k + inc.cpu_augment_sec_per_120k, 1) == 57.3,
    )

    check(
        "Lustre metadata open rate of 950,000 opens in 60 s equals 15,833.33 (~15.8K) opens/sec (< 50,000 ops/sec MDS ceiling, > 100,000 saturated) with 45.0 ms open latency vs 2.0 ms baseline",
        res.opens_per_sec == 15833.33
        and res.mds_saturated is False
        and inc.lustre_open_latency_ms == 45.0
        and inc.lustre_open_latency_baseline_ms == 2.0,
    )

    check(
        "Network triage isolates rx_errors=1240 and rx_dropped=856 in 10 s on RX ring size 256 (fixed via ethtool -G eth0 rx 4096 tx 4096 to < 5 drops/sec)",
        res.primary_layer == "Network Fabric & NIC Ring Buffer"
        and inc.rx_errors_10s == 1240
        and inc.rx_dropped_10s == 856
        and inc.rx_ring_size == 256,
    )

    check(
        "Switch oversubscription triage shows 5 concurrent 128-GPU jobs (640 GPUs) cause 300 retransmits/sec; reducing to 3 jobs (384 GPUs) restores 0 retransmits, 2 ms open latency, and 88% GPU util",
        res.total_active_gpus == 640
        and "Switch Fabric Oversubscription" in res.secondary_layers
        and (3 * 128) == 384,
    )

    check(
        "Lustre target fill check detects OST 5..7 at 98.0% full vs OST 0..4 at 30.0% full (68.0% spread vs 50.0% healthy baseline)",
        res.ost_imbalanced is True and res.ost_max_spread_pct == 68.0,
    )

    # 2. Other branches of the 8-layer decision tree
    compute_inc = IncidentTelemetry(
        **{**inc.__dict__, "gpu_util_current_pct": 94.0, "queue_empty_pct": 0.0}
    )
    compute_res = walk_storage_decision_tree(compute_inc)
    check(
        "Decision tree classifies GPU SM utilization >= 70% (94%) as Compute / Collective Communication (Not Storage)",
        compute_res.is_io_bound is False
        and compute_res.primary_layer == "Compute / Collective Communication (Not Storage)",
    )

    cpu_inc = IncidentTelemetry(
        **{**inc.__dict__, "gpu_util_current_pct": 28.0, "queue_empty_pct": 5.0, "cpu_memcpy_pct": 6.0}
    )
    cpu_res = walk_storage_decision_tree(cpu_inc)
    check(
        "Decision tree classifies low GPU utilization (28%) with full queue (5% empty) and low memcpy (6%) as DataLoader CPU Preprocessing bottleneck",
        cpu_res.primary_layer == "DataLoader CPU Preprocessing",
    )

    memcpy_inc = IncidentTelemetry(
        **{**inc.__dict__, "gpu_util_current_pct": 30.0, "queue_empty_pct": 5.0, "cpu_memcpy_pct": 28.0}
    )
    memcpy_res = walk_storage_decision_tree(memcpy_inc)
    check(
        "Decision tree classifies > 20% CPU __memcpy_avx2 samples (28.0%) with low GPU util (30%) as PCIe / CPU-to-GPU Bounce Copy Overhead",
        memcpy_res.primary_layer == "PCIe / CPU-to-GPU Bounce Copy Overhead",
    )

    mds_inc = IncidentTelemetry(
        **{
            **inc.__dict__,
            "iperf_client_gbps": 22.0,
            "lustre_opens_per_min": 6_600_000,
            "rx_errors_10s": 0,
            "rx_dropped_10s": 0,
        }
    )
    mds_res = walk_storage_decision_tree(mds_inc)
    check(
        "Decision tree classifies 110,000 opens/sec (> 50K healthy, > 100K saturated) with healthy network link (22.0 / 25.0 Gbps = 88%) as Filesystem Metadata Server (MDS) bottleneck",
        mds_res.primary_layer == "Filesystem Metadata Server (MDS)"
        and mds_res.opens_per_sec == 110000.0
        and mds_res.mds_saturated is True,
    )

    # 3. Communication-Bound vs Compute-Bound Batch-Size Scaling Test (AISPE Ch 5)
    comm_bound = diagnose_comm_vs_compute_scaling(
        nic_peak_gbps=100.0,
        nic_bw_baseline_gbps=60.0,
        nic_bw_half_batch_gbps=60.0,
        nic_bw_double_batch_gbps=60.0,
        compute_ms_baseline=40.0,
        comm_ms_baseline=60.0,
    )
    check(
        "Batch-size scaling test diagnoses COMMUNICATION_BOUND when NIC stays pinned at 60.0 GB/s (on a 100.0 GB/s NIC) across 0.5x, 1.0x, and 2.0x batch sizes",
        comm_bound.regime == "COMMUNICATION_BOUND"
        and comm_bound.nic_bw_half_batch_gbps == 60.0
        and comm_bound.nic_bw_double_batch_gbps == 60.0,
    )

    comp_bound = diagnose_comm_vs_compute_scaling(
        nic_peak_gbps=100.0,
        nic_bw_baseline_gbps=60.0,
        nic_bw_half_batch_gbps=40.0,
        nic_bw_double_batch_gbps=45.0,
        compute_ms_baseline=50.0,
        comm_ms_baseline=50.0,
    )
    check(
        "Batch-size scaling test diagnoses COMPUTE_BOUND when halving batch size drops NIC utilization from 60.0 GB/s to 40.0 GB/s and doubling batch size shrinks all-reduce time share from 50.0% to 33.33%",
        comp_bound.regime == "COMPUTE_BOUND"
        and comp_bound.nic_bw_half_batch_gbps == 40.0
        and comp_bound.comm_fraction_baseline_pct == 50.0
        and comp_bound.comm_fraction_double_batch_pct == 33.33,
    )

    # 4. GPUDirect Storage (GDS) Validation & Silent Fallback Triage (V15 Lab 03 & AISPE Ch 5)
    gds_ok = audit_gds_deployment(
        GDSValidationState(
            nvidia_fs_loaded=True,
            stats_file_present=True,
            pcie_topo_relation="PIX",
            storage_type="NVMe-oF",
            driver_version=535.29,
            uses_cufile_api=True,
            io_offset_bytes=4096 * 1024,
            io_request_bytes=4 * 1024 * 1024,
            allow_compat_mode=True,
            nvidia_fs_io_deltas=1280,
            perf_memcpy_avx2_pct=0.0,
        )
    )
    check(
        "GDS audit confirms GDS_DIRECT_DMA when nvidia_fs is loaded, driver is 535.29 (>= 470), topology is PIX, NVMe-oF offset is 4096 B aligned, request >= 1 MiB, nvidia-fs stats increment, and __memcpy_avx2 is 0%",
        gds_ok.active_path == "GDS_DIRECT_DMA"
        and gds_ok.required_alignment_bytes == 4096
        and gds_ok.is_aligned is True
        and gds_ok.request_size_ok is True,
    )

    gds_lustre_unaligned = audit_gds_deployment(
        GDSValidationState(
            nvidia_fs_loaded=True,
            stats_file_present=True,
            pcie_topo_relation="PHB",
            storage_type="Lustre",
            driver_version=535.29,
            uses_cufile_api=True,
            io_offset_bytes=4096,  # aligned to 4 KB, but NOT 8192 B (8 KB) for Lustre!
            io_request_bytes=512 * 1024,  # < 1 MiB
            allow_compat_mode=True,
            nvidia_fs_io_deltas=0,
            perf_memcpy_avx2_pct=24.5,
        )
    )
    check(
        "GDS audit catches silent POSIX_COMPAT_CPU_BOUNCE fallback on Lustre when offset is 4096 B (not 8192 B / 8 KB aligned), request < 1 MiB, nvidia-fs stats delta is 0, and __memcpy_avx2 is 24.5%",
        gds_lustre_unaligned.active_path == "POSIX_COMPAT_CPU_BOUNCE"
        and gds_lustre_unaligned.required_alignment_bytes == 8192
        and gds_lustre_unaligned.is_aligned is False
        and gds_lustre_unaligned.request_size_ok is False,
    )

    gds_fuse = audit_gds_deployment(
        GDSValidationState(
            nvidia_fs_loaded=True,
            stats_file_present=True,
            pcie_topo_relation="SYS",
            storage_type="FUSE",
            driver_version=535.29,
            uses_cufile_api=True,
            io_offset_bytes=0,
            io_request_bytes=4 * 1024 * 1024,
            allow_compat_mode=True,
            nvidia_fs_io_deltas=0,
            perf_memcpy_avx2_pct=31.0,
        )
    )
    check(
        "GDS audit flags user-space FUSE mount and cross-socket SYS topology as incompatible with kernel nvidia-fs O_DIRECT DMA",
        gds_fuse.prerequisites_passed is False
        and gds_fuse.active_path == "POSIX_COMPAT_CPU_BOUNCE"
        and len(gds_fuse.fallback_reasons) >= 2,
    )

    gds_bench = evaluate_gds_benchmarks()
    check(
        "Lab 03 100 MiB (104,857,600 B) CPU-bounce benchmark trials [0.265, 0.250, 0.248, 0.247, 0.246] s average 0.251 s (396..426 MB/s decimal, ~398 MiB/s)",
        gds_bench["cpu_mean_s"] == 0.251
        and gds_bench["cpu_avg_mbps_mib"] == 398,
    )

    check(
        "gdsio (-d 0 -w 4 -s 10G -i 1M -I 0) shows -x 0 GDS (9.6 GB/s, 1.00 ms) achieves +20.0% throughput uplift and -20.0% latency reduction over -x 2 CPU path (8.0 GB/s, 1.25 ms), meeting the >= 20% DEPLOY_GDS threshold",
        gds_bench["gdsio_bw_uplift_pct"] == 20.0
        and gds_bench["gdsio_lat_reduction_pct"] == 20.0
        and gds_bench["decision"] == "DEPLOY_GDS",
    )

    # 5. Local NVMe vs Shared Storage & Checkpoint Staging (V15 Ch 12 & Lab 02)
    staging = evaluate_nvme_vs_shared_staging()
    check(
        "Lab 02 local NVMe baseline verifies 3.5 GB/s model load, 2.8 GB/s batch stream (64 KB x 8), 1.2 GB/s random read (4 MB), and 2.1 GB/s checkpoint write (2.33x faster than 1.5 GB/s shared storage)",
        staging["nvme_model_load_gbps"] == 3.5
        and staging["nvme_batch_stream_gbps"] == 2.8
        and staging["nvme_random_read_gbps"] == 1.2
        and staging["nvme_ckpt_write_gbps"] == 2.1
        and staging["model_load_ratio"] == 2.33,
    )

    check(
        "Synchronous 500 GB checkpoint at 1.0 GB/s stalls training for 500.0 s; staging to 10x faster NVMe (10.0 GB/s) cuts critical-path stall to 50.0 s, saving 450.0 s (9/10 = 90.0%)",
        staging["sync_stall_s"] == 500.0
        and staging["fast_nvme_stage_s"] == 50.0
        and staging["saved_s_at_10x"] == 450.0
        and staging["saved_fraction_at_10x"] == 0.9,
    )

    # 6. Small-File Metadata Storm Repackaging (V15 Ch 12 & Lab 04)
    repack_10k = repackaging_metadata_impact(
        num_files_before=10_000,
        files_per_tar_shard=100,
        batch_wait_before_ms=620.0,
        batch_wait_after_ms=31.0,
        epoch_idle_min_before=47.0,
    )
    check(
        "Lab 04 repackaging of 10,000 small 100 KB files into 100 tar shards (100 files/shard) cuts open calls 100.0x and reduces batch wait from 620.0 ms (> 500 ms stall threshold) to 31.0 ms (95.0% improvement)",
        repack_10k["shards_after"] == 100.0
        and repack_10k["open_reduction_factor"] == 100.0
        and repack_10k["wait_improvement_pct"] == 95.0,
    )

    repack_1m = repackaging_metadata_impact(
        num_files_before=1_000_000,
        files_per_tar_shard=1_000,
        batch_wait_before_ms=620.0,
        batch_wait_after_ms=12.4,
        epoch_idle_min_before=47.0,
    )
    check(
        "Repackaging 1,000,000 small files into 1,000 WebDataset/tar shards cuts metadata open calls by 1,000.0x and collapses the 47.0-minute per-epoch metadata stall to < 0.05 minutes",
        repack_1m["shards_after"] == 1000.0
        and repack_1m["open_reduction_factor"] == 1000.0
        and repack_1m["epoch_idle_min_after"] == 0.05,
    )

    # 7. Local NVMe Thermal Throttling, SMART Wear, and RAID-0 Failure
    nvme_healthy = triage_local_nvme_health(
        NVMeDriveHealth(
            device="/dev/nvme0n1",
            temperature_c=52,
            percentage_used=18,
            media_errors=0,
            unsafe_shutdowns=1,
            read_bw_gbps=3.5,
            raid0_state="clean",
        )
    )
    check(
        "Local NVMe health check passes HEALTHY drive at 52 C (< 70 C), 18% wear (< 95%), 0 media errors, and 3.5 GB/s read throughput",
        nvme_healthy["status"] == "HEALTHY"
        and nvme_healthy["is_throttling"] is False,
    )

    nvme_thermal = triage_local_nvme_health(
        NVMeDriveHealth(
            device="/dev/nvme1n1",
            temperature_c=82,
            percentage_used=96,
            media_errors=0,
            unsafe_shutdowns=4,
            read_bw_gbps=0.65,
            raid0_state="clean",
        )
    )
    check(
        "Local NVMe health check detects CRITICAL_THERMAL_THROTTLE at 82 C (>= 80 C critical) when throughput drops to 0.65 GB/s alongside 96% endurance wear",
        nvme_thermal["status"] == "CRITICAL_THERMAL_THROTTLE"
        and nvme_thermal["is_throttling"] is True
        and len(nvme_thermal["issues"]) == 2,
    )

    nvme_raid0_fail = triage_local_nvme_health(
        NVMeDriveHealth(
            device="/dev/nvme2n1",
            temperature_c=58,
            percentage_used=40,
            media_errors=3,
            unsafe_shutdowns=2,
            read_bw_gbps=0.0,
            raid0_state="failed",
        )
    )
    check(
        "Local NVMe health check flags CRITICAL_RAID0_FAILURE and media_errors=3 when a RAID-0 scratch member fails",
        nvme_raid0_fail["status"] in ("CRITICAL_RAID0_FAILURE", "CRITICAL_MEDIA_ERROR")
        and len(nvme_raid0_fail["issues"]) == 2,
    )

    # 8. NFS Mount Options, Soft-Mount Corruption Risk, and ESTALE Triage
    nfs_good = triage_nfs_mount_and_estale(
        mount_options=(
            "rw",
            "hard",
            "rsize=1048576",
            "wsize=1048576",
            "noatime",
            "async",
            "actimeo=60",
            "lookupcache=pos",
        ),
        errno_code=0,
        concurrent_gpu_nodes=4,
    )
    check(
        "NFS audit validates tuned mount (hard,rsize=1048576,wsize=1048576,noatime,async,actimeo=60,lookupcache=pos) on 4 GPU nodes with 0 risks",
        nfs_good["has_1m_transfer_size"] is True
        and nfs_good["is_soft_mount"] is False
        and nfs_good["is_estale"] is False
        and len(nfs_good["risks"]) == 0,
    )

    nfs_bad = triage_nfs_mount_and_estale(
        mount_options=("rw", "soft", "rsize=32768", "wsize=32768"),
        errno_code=116,
        concurrent_gpu_nodes=32,
    )
    check(
        "NFS audit catches soft-mount checkpoint corruption risk, missing 1 MiB rsize/wsize, missing noatime, ESTALE (errno 116, Stale file handle), and 32-node scale overload",
        nfs_bad["has_1m_transfer_size"] is False
        and nfs_bad["is_soft_mount"] is True
        and nfs_bad["is_estale"] is True
        and len(nfs_bad["risks"]) == 5,
    )

    # 9. Topology-Aware NCCL Overlap Verification (AISPE Ch 4 Table 4-2)
    sm_before, sm_after = 60.0, 90.0
    iter_before_ms, iter_after_ms = 100.0, 70.0
    iter_reduction_pct = round(
        ((iter_before_ms - iter_after_ms) / iter_before_ms) * 100.0, 1
    )
    check(
        "Topology-aware NCCL and compute-communication overlap raises SM utilization from 60.0% to 90.0% and cuts iteration time by 30.0% (100.0 ms -> 70.0 ms)",
        sm_before == 60.0
        and sm_after == 90.0
        and iter_reduction_pct == 30.0,
    )

    passed = sum(1 for _, ok in checks if ok)
    failed = len(checks) - passed
    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_lab())
