"""
Chapter 13.2 Verification Lab — Local NVMe and Data Staging
Runs 28 deterministic self-checks covering:
  1. DGX H100/H200 and GB200/GB300 NVL72 2-tier NVMe topology (OS RAID 1 vs /raid RAID 0)
  2. mdadm RAID 0 chunk size, full stripe width, and XFS sunit/swidth alignment math
  3. Multi-epoch dataset staging break-even calculator & async checkpoint staging speedup
  4. Linux blk-mq scheduler (`none`/`mq-deadline`), `read_ahead_kb`, `noatime`, and NUMA checks
  5. NVMe SMART `percentage_used`, `available_spare`, thermal throttling, and DWPD/TBW math
  6. Slurm Prolog / Epilog `/raid/job_$SLURM_JOB_ID` isolation and orphan-reclamation lifecycle
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from local_nvme_staging import (
    SlurmScratchNodeState,
    audit_nvme_tuning,
    build_dgx_h100_nvme_profile,
    build_gb200_compute_tray_nvme_profile,
    compute_raid0_geometry,
    evaluate_checkpoint_staging,
    evaluate_io_stripe_efficiency,
    evaluate_nvme_endurance_and_smart,
    evaluate_staging_break_even,
    run_slurm_epilog,
    run_slurm_prolog,
)


def run_lab() -> int:
    passed = 0
    failed = 0

    def check(idx: int, description: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {idx}. {description}")
            passed += 1
        else:
            print(f"  [FAIL] {idx}. {description}")
            failed += 1

    print("=== Chapter 13.2 Lab: Local NVMe and Data Staging ===")

    # ------------------------------------------------------------------
    # Group 1: DGX H100/H200 and GB200/GB300 2-Tier NVMe Hardware Layout
    # ------------------------------------------------------------------
    dgx = build_dgx_h100_nvme_profile()
    gb200 = build_gb200_compute_tray_nvme_profile()

    check(
        1,
        "DGX H100/H200 OS tier uses 2x 1.92 TB M.2 NVMe in RAID 1 (3.84 TB raw, 1.92 TB usable, non-ephemeral)",
        dgx.os_tier.drive_count == 2
        and dgx.os_tier.form_factor == "M.2"
        and dgx.os_tier.raid_level == "RAID 1"
        and dgx.os_tier.raw_capacity_tb == 3.84
        and dgx.os_tier.usable_capacity_tb == 1.92
        and not dgx.os_tier.ephemeral,
    )

    check(
        2,
        "DGX H100/H200 scratch tier uses 8x 3.84 TB U.2 NVMe in RAID 0 at /raid (30.72 TB usable, 50.0 GB/s seq read)",
        dgx.scratch_tier.drive_count == 8
        and dgx.scratch_tier.form_factor == "U.2"
        and dgx.scratch_tier.raid_level == "RAID 0"
        and dgx.scratch_tier.mount_point == "/raid"
        and dgx.scratch_tier.usable_capacity_tb == 30.72
        and dgx.scratch_tier.sustained_seq_read_gbps == 50.0
        and dgx.scratch_tier.ephemeral,
    )

    check(
        3,
        "GB200/GB300 1U compute tray uses 1x 1.92 TB M.2 OS drive + 4x 3.84 TB E1.S RAID 0 scratch (15.36 TB/tray, 276.48 TB/rack)",
        gb200.os_tier.drive_count == 1
        and gb200.os_tier.usable_capacity_tb == 1.92
        and gb200.scratch_tier.drive_count == 4
        and gb200.scratch_tier.form_factor == "E1.S"
        and gb200.scratch_tier.usable_capacity_tb == 15.36
        and round(gb200.scratch_tier.usable_capacity_tb * gb200.racks_or_trays, 2) == 276.48,
    )

    # ------------------------------------------------------------------
    # Group 2: mdadm RAID 0 Chunk Size and Stripe Width Alignment
    # ------------------------------------------------------------------
    geom_8x512 = compute_raid0_geometry(
        num_drives=8, drive_size_tb=3.84, chunk_size_kb=512, filesystem_block_bytes=4096
    )
    geom_4x256 = compute_raid0_geometry(
        num_drives=4, drive_size_tb=3.84, chunk_size_kb=256, filesystem_block_bytes=4096
    )

    check(
        4,
        "8-drive RAID 0 with 512 KB chunk yields 4096 KB (4.0 MB) full stripe, sunit=128, swidth=1024 blocks",
        geom_8x512.full_stripe_kb == 4096
        and geom_8x512.full_stripe_mb == 4.0
        and geom_8x512.xfs_sunit_blocks == 128
        and geom_8x512.xfs_swidth_blocks == 1024
        and geom_8x512.usable_capacity_tb == 30.72
        and geom_8x512.mkfs_xfs_cmd == "mkfs.xfs -f -d su=512k,sw=8 /dev/md0",
    )

    check(
        5,
        "4-drive E1.S RAID 0 with 256 KB chunk yields 1024 KB (1.0 MB) full stripe, sunit=64, swidth=256 blocks",
        geom_4x256.full_stripe_kb == 1024
        and geom_4x256.full_stripe_mb == 1.0
        and geom_4x256.xfs_sunit_blocks == 64
        and geom_4x256.xfs_swidth_blocks == 256
        and geom_4x256.usable_capacity_tb == 15.36,
    )

    io_small = evaluate_io_stripe_efficiency(64, geom_8x512)
    io_1m = evaluate_io_stripe_efficiency(1024, geom_8x512)
    io_4m = evaluate_io_stripe_efficiency(4096, geom_8x512)

    check(
        6,
        "A single 64 KB read on an 8x 512 KB RAID 0 hits only 1 drive (12.5% stripe utilization), whereas 4 MB hits all 8 drives (100%)",
        io_small["active_drives"] == 1.0
        and io_small["stripe_utilization"] == 0.125
        and io_1m["active_drives"] == 2.0
        and io_1m["stripe_utilization"] == 0.25
        and io_4m["active_drives"] == 8.0
        and io_4m["stripe_utilization"] == 1.0
        and io_4m["is_full_stripe_multiple"] == 1.0,
    )

    # ------------------------------------------------------------------
    # Group 3: Dataset Staging Break-Even & Async Checkpoint Staging
    # ------------------------------------------------------------------
    # V15 Ch 3 inline cache-fill scenario: 500 GB dataset on 2000 GB NVMe,
    # Epoch 1 = 245s (cold fetch from Lustre), Epoch 2..N = 200s (warm local NVMe) vs 245s uncached
    v15_inline_10ep = evaluate_staging_break_even(
        dataset_gb=500.0,
        nvme_capacity_gb=2000.0,
        num_epochs=10,
        stage_copy_bw_gbps=2.0,
        epoch_time_remote_sec=245.0,
        epoch_time_local_sec=200.0,
        inline_epoch1_staging=True,
    )

    check(
        7,
        "V15 Ch 3 inline staging (245s cold -> 200s warm, 45s/epoch saved): 10 epochs take 2045s vs 2450s (405s saved, 16.53% speedup)",
        v15_inline_10ep.per_epoch_savings_sec == 45.0
        and v15_inline_10ep.total_time_no_staging_sec == 2450.0
        and v15_inline_10ep.total_time_with_staging_sec == 2045.0
        and v15_inline_10ep.net_wall_clock_saved_sec == 405.0
        and v15_inline_10ep.speedup_pct == 16.53
        and v15_inline_10ep.recommendation == "STAGE_TO_LOCAL_NVME",
    )

    # Explicit pre-stage scenario: 500 GB dataset copied before Epoch 1 at 2.0 GB/s (250s copy),
    # saving 45s/epoch (245s -> 200s): break-even = 250 / 45 = 5.5556 (~5.56) epochs -> 6 epochs minimum.
    # For 6 epochs: 1450s vs 1470s (saves 20s); for 1000 epochs: saves 44750 seconds (12.4 hours).
    prestage_6ep = evaluate_staging_break_even(
        dataset_gb=500.0,
        nvme_capacity_gb=2000.0,
        num_epochs=6,
        stage_copy_bw_gbps=2.0,
        epoch_time_remote_sec=245.0,
        epoch_time_local_sec=200.0,
        inline_epoch1_staging=False,
    )
    prestage_1000ep = evaluate_staging_break_even(
        dataset_gb=500.0,
        nvme_capacity_gb=2000.0,
        num_epochs=1000,
        stage_copy_bw_gbps=2.0,
        epoch_time_remote_sec=245.0,
        epoch_time_local_sec=200.0,
        inline_epoch1_staging=False,
    )
    prestage_3ep = evaluate_staging_break_even(
        dataset_gb=500.0,
        nvme_capacity_gb=2000.0,
        num_epochs=3,
        stage_copy_bw_gbps=2.0,
        epoch_time_remote_sec=245.0,
        epoch_time_local_sec=200.0,
        inline_epoch1_staging=False,
    )

    check(
        8,
        "Explicit pre-staging of 500 GB at 2.0 GB/s (250s copy, 45s/epoch saved) breaks even at 5.5556 (5.56) epochs (6 epochs: 1450s vs 1470s = 20s saved; 1000 epochs: 44750s saved)",
        prestage_6ep.copy_stage_time_sec == 250.0
        and prestage_6ep.break_even_epochs_exact == 5.5556
        and round(prestage_6ep.break_even_epochs_exact, 2) == 5.56
        and prestage_6ep.min_integer_epochs_to_pay_back == 6
        and prestage_6ep.total_time_no_staging_sec == 1470.0
        and prestage_6ep.total_time_with_staging_sec == 1450.0
        and prestage_6ep.net_wall_clock_saved_sec == 20.0
        and prestage_1000ep.net_wall_clock_saved_sec == 44750.0
        and prestage_6ep.recommendation == "STAGE_TO_LOCAL_NVME",
    )

    check(
        9,
        "Pre-staging for a 3-epoch fine-tuning run loses 115s of wall-clock time (850s vs 735s) and recommends DO_NOT_STAGE_TOO_FEW_EPOCHS",
        prestage_3ep.total_time_no_staging_sec == 735.0
        and prestage_3ep.total_time_with_staging_sec == 850.0
        and prestage_3ep.net_wall_clock_saved_sec == -115.0
        and prestage_3ep.recommendation == "DO_NOT_STAGE_TOO_FEW_EPOCHS",
    )

    oversized_stage = evaluate_staging_break_even(
        dataset_gb=1800.0,  # 90% of 2000 GB (>85% safe limit)
        nvme_capacity_gb=2000.0,
        num_epochs=50,
        stage_copy_bw_gbps=2.0,
        epoch_time_remote_sec=245.0,
        epoch_time_local_sec=200.0,
    )

    check(
        10,
        "Dataset exceeding 85% of NVMe capacity (1800 GB on 2000 GB = 90%) is rejected to prevent eviction thrashing and SSD write amplification",
        not oversized_stage.fits_in_nvme
        and oversized_stage.recommendation
        == "DO_NOT_STAGE_DATASET_EXCEEDS_SAFE_85PCT_NVME_OR_NO_EPOCH_GAIN",
    )

    ckpt = evaluate_checkpoint_staging(
        checkpoint_gb=500.0,
        shared_write_bw_gbps=1.2,
        local_nvme_write_bw_gbps=3.5,
        async_ack_sec=1.0,
    )

    check(
        11,
        "V15 Ch 3 checkpoint staging (500 GB): sync Lustre write is 416.67s (~417s), local NVMe write is 142.86s (~143s), async handoff gives 416.67x critical-path speedup",
        ckpt.sync_shared_write_sec == 416.67
        and ckpt.local_nvme_write_sec == 142.86
        and ckpt.async_visible_stall_sec == 1.0
        and ckpt.critical_path_speedup_x == 416.67,
    )

    # ------------------------------------------------------------------
    # Group 4: Linux NVMe Queue, Read-Ahead, Filesystem, and NUMA Audit
    # ------------------------------------------------------------------
    healthy_tuning = audit_nvme_tuning(
        device="nvme0n1",
        scheduler="none",
        nr_requests=1023,
        read_ahead_kb=4096,
        mount_options=["rw", "noatime", "attr2", "inode64"],
        numa_node_nvme=0,
        numa_node_workers=0,
        workload_pattern="large_sequential",
    )

    check(
        12,
        "Properly tuned NVMe (scheduler=none, nr_requests=1023, read_ahead_kb=4096, noatime, NUMA-aligned) passes HEALTHY with 0 issues",
        healthy_tuning.status == "HEALTHY" and len(healthy_tuning.issues) == 0,
    )

    bad_sched_ra = audit_nvme_tuning(
        device="nvme0n1",
        scheduler="bfq",
        nr_requests=128,
        read_ahead_kb=128,
        mount_options=["rw", "relatime"],
        numa_node_nvme=0,
        numa_node_workers=1,
        workload_pattern="large_sequential",
    )

    check(
        13,
        "Audit catches BFQ scheduler, shallow nr_requests=128, default 128 KB read-ahead, missing noatime, and NUMA 0 vs 1 mismatch (5 issues)",
        bad_sched_ra.status == "DEGRADED"
        and len(bad_sched_ra.issues) == 5
        and any("scheduler" in r for r in bad_sched_ra.remediations)
        and any("blockdev --setra 8192" in r for r in bad_sched_ra.remediations)
        and any("noatime" in r for r in bad_sched_ra.remediations)
        and any("numactl" in r for r in bad_sched_ra.remediations),
    )

    random_odirect_tuning = audit_nvme_tuning(
        device="nvme1n1",
        scheduler="mq-deadline",
        nr_requests=1023,
        read_ahead_kb=128,
        mount_options=["rw", "noatime"],
        numa_node_nvme=1,
        numa_node_workers=1,
        workload_pattern="pure_random_o_direct",
    )

    check(
        14,
        "mq-deadline with 128 KB read-ahead is accepted as HEALTHY when workload_pattern is pure_random_o_direct (e.g., 3FS / GDS random reads)",
        random_odirect_tuning.status == "HEALTHY" and len(random_odirect_tuning.issues) == 0,
    )

    # ------------------------------------------------------------------
    # Group 5: SMART Telemetry, Wear-Leveling, and DWPD Endurance Math
    # ------------------------------------------------------------------
    smart_healthy = evaluate_nvme_endurance_and_smart(
        drive_size_tb=3.84,
        rated_dwpd=1.0,
        warranty_years=5,
        daily_host_writes_tb=2.5,
        write_amplification_factor=1.2,
        percentage_used=18,
        available_spare_pct=100,
        available_spare_threshold_pct=10,
        composite_temp_c=46,
        media_errors=0,
    )

    check(
        15,
        "3.84 TB 1-DWPD 5-year (1825-day) drive has 7008.0 TBW rating (56064.0 TB = 56.06 PB across 8 drives); 2.5 TB/day host writes at WAF 1.2 = 3.0 TB/day NAND (0.7812 DWPD, 6.4 years lifespan)",
        smart_healthy.total_tbw_rating_tb == 7008.0
        and (5 * 365) == 1825
        and round(8 * smart_healthy.total_tbw_rating_tb, 1) == 56064.0
        and round((8 * smart_healthy.total_tbw_rating_tb) / 1000.0, 2) == 56.06
        and smart_healthy.effective_nand_daily_tb == 3.0
        and smart_healthy.effective_dwpd_used == 0.7812
        and smart_healthy.estimated_lifespan_years == 6.4
        and smart_healthy.health_status == "HEALTHY",
    )

    smart_thermal = evaluate_nvme_endurance_and_smart(
        drive_size_tb=3.84,
        rated_dwpd=1.0,
        warranty_years=5,
        daily_host_writes_tb=2.0,
        write_amplification_factor=1.1,
        percentage_used=25,
        available_spare_pct=98,
        available_spare_threshold_pct=10,
        composite_temp_c=74,
        media_errors=0,
    )

    check(
        16,
        "NVMe composite temperature of 74 C (>= 70 C threshold) flags WARNING_THERMAL_THROTTLING",
        smart_thermal.health_status == "WARNING_THERMAL_THROTTLING"
        and "fan" in smart_thermal.recommended_action.lower(),
    )

    smart_wear = evaluate_nvme_endurance_and_smart(
        drive_size_tb=3.84,
        rated_dwpd=1.0,
        warranty_years=5,
        daily_host_writes_tb=12.0,
        write_amplification_factor=1.5,
        percentage_used=92,
        available_spare_pct=35,
        available_spare_threshold_pct=10,
        composite_temp_c=52,
        media_errors=0,
    )

    check(
        17,
        "percentage_used=92% with 18.0 TB/day NAND writes (4.6875 DWPD, 1.07 years lifespan) flags WARNING_WEAR_OUT_NEAR",
        smart_wear.effective_nand_daily_tb == 18.0
        and smart_wear.effective_dwpd_used == 4.6875
        and smart_wear.health_status == "WARNING_WEAR_OUT_NEAR",
    )

    smart_critical_spare = evaluate_nvme_endurance_and_smart(
        drive_size_tb=3.84,
        rated_dwpd=1.0,
        warranty_years=5,
        daily_host_writes_tb=2.0,
        write_amplification_factor=1.1,
        percentage_used=99,
        available_spare_pct=8,
        available_spare_threshold_pct=10,
        composite_temp_c=50,
        media_errors=0,
    )

    smart_critical_media = evaluate_nvme_endurance_and_smart(
        drive_size_tb=3.84,
        rated_dwpd=1.0,
        warranty_years=5,
        daily_host_writes_tb=2.0,
        write_amplification_factor=1.1,
        percentage_used=12,
        available_spare_pct=100,
        available_spare_threshold_pct=10,
        composite_temp_c=48,
        media_errors=3,
    )

    check(
        18,
        "available_spare <= threshold (8% <= 10%) or non-zero media_errors (3) triggers CRITICAL_REPLACE_DRIVE",
        smart_critical_spare.health_status == "CRITICAL_REPLACE_DRIVE"
        and smart_critical_media.health_status == "CRITICAL_REPLACE_DRIVE",
    )

    # ------------------------------------------------------------------
    # Group 6: Slurm Prolog / Epilog Per-Job Scratch Lifecycle
    # ------------------------------------------------------------------
    node_state = SlurmScratchNodeState(
        total_capacity_gb=30720.0,  # 30.72 TB = 30,720 GB
        reserved_headroom_pct=15.0,  # 85% max safe usable = 26,112 GB
        active_job_dirs={},
        orphan_dirs={},
    )

    check(
        19,
        "30,720 GB /raid array with 15% reserved headroom enforces a 26,112.0 GB (85%) safe allocation ceiling",
        node_state.max_safe_usable_gb == 26112.0,
    )

    p1 = run_slurm_prolog(node_state, job_id=1001, requested_gb=12000.0)
    check(
        20,
        "Slurm Prolog admits job 1001 requesting 12,000 GB, creates /raid/job_1001, and reports 39.06% fill",
        bool(p1["admitted"])
        and p1["job_path"] == "/raid/job_1001"
        and p1["env_var"] == "LOCAL_SCRATCH=/raid/job_1001"
        and p1["fill_pct"] == 39.06,
    )

    # Simulate job 1001 crashing without a Slurm Epilog (epilog_enabled=False)
    e1_bad = run_slurm_epilog(node_state, job_id=1001, epilog_enabled=False)
    check(
        21,
        "Missing Slurm Epilog leaves /raid/job_1001 as a 12,000 GB orphan directory (39.06% leaked fill)",
        not bool(e1_bad["cleaned"])
        and e1_bad["leaked_gb"] == 12000.0
        and "/raid/job_1001" in node_state.orphan_dirs
        and node_state.fill_pct == 39.06,
    )

    # Without orphan purging, a new 16,000 GB job (12,000 + 16,000 = 28,000 > 26,112 GB) is rejected
    p2_blocked = run_slurm_prolog(
        node_state, job_id=1002, requested_gb=16000.0, purge_orphans=False
    )
    check(
        22,
        "Without orphan cleanup, job 1002 requesting 16,000 GB fails admission (28,000 GB = 91.15% > 85% safe ceiling)",
        not bool(p2_blocked["admitted"])
        and p2_blocked["projected_fill_pct"] == 91.15
        and p2_blocked["reason"] == "INSUFFICIENT_SAFE_NVME_SCRATCH_CAPACITY",
    )

    # With Prolog orphan purging enabled, the 12,000 GB orphan is reclaimed and job 1002 is admitted
    p2_admitted = run_slurm_prolog(
        node_state, job_id=1002, requested_gb=16000.0, purge_orphans=True
    )
    check(
        23,
        "With Prolog orphan sweep enabled, 12,000 GB is reclaimed and job 1002 is admitted at 52.08% fill",
        bool(p2_admitted["admitted"])
        and p2_admitted["reclaimed_orphan_gb"] == 12000.0
        and p2_admitted["fill_pct"] == 52.08,
    )

    e2_clean = run_slurm_epilog(node_state, job_id=1002, epilog_enabled=True)
    check(
        24,
        "Slurm Epilog cleans /raid/job_1002 on job exit and returns /raid usage to 0.0 GB (0.0% fill)",
        bool(e2_clean["cleaned"])
        and e2_clean["freed_gb"] == 16000.0
        and e2_clean["remaining_used_gb"] == 0.0
        and e2_clean["fill_pct"] == 0.0,
    )

    # ------------------------------------------------------------------
    # Group 7: End-to-End Chapter Numerical Verification Checks
    # ------------------------------------------------------------------
    # V15 Ch 3 8-node 256-GPU Lustre scenario math:
    # 256 GPUs * 120 MB/s = 30,720 MB/s (30.72 GB/s, ~30.7 GB/s) aggregate demand;
    # 25 Gbps link = 3125 MB/s; shared across 20 GPUs (1.25 Gbps/GPU) = 156.25 MB/s (~156 MB/s) raw -> ~110 MB/s after 30% metadata penalty
    agg_demand_gbps = round((256 * 120.0) / 1000.0, 2)
    per_gpu_link_mbps = (1.25 * 1000.0) / 8.0
    check(
        25,
        "V15 Ch 3 cluster sizing: 256 GPUs * 120 MB/s requires 30.72 GB/s (~30.7 GB/s); 1.25 Gbps/GPU is 156.25 MB/s raw (~110 MB/s with 30% metadata overhead)",
        agg_demand_gbps == 30.72 and per_gpu_link_mbps == 156.25,
    )

    # V15 Lab 02NVMe vs Shared Storage ratio: 3.5 GB/s NVMe vs 1.5 GB/s shared = 2.33x (> 2.0x caching threshold)
    nvme_vs_shared_ratio = round(3.5 / 1.5, 2)
    check(
        26,
        "V15 Lab 02 model-load ratio: 3.5 GB/s local NVMe vs 1.5 GB/s shared storage = 2.33x (> 2.0x caching rule)",
        nvme_vs_shared_ratio == 2.33 and nvme_vs_shared_ratio > 2.0,
    )

    # ASP Ch 5 GB200 NVL72 aggregate storage ingestion demand: 72 GPUs * 200 MB/s = 14,400 MB/s (14.4 GB/s)
    nvl72_ingest_gbps = round((72 * 200.0) / 1000.0, 2)
    check(
        27,
        "ASP Ch 5 NVL72 rack ingestion: 72 GPUs * 200 MB/s = 14.4 GB/s (within the 14–20 GB/s rack streaming range)",
        nvl72_ingest_gbps == 14.4 and 14.0 <= nvl72_ingest_gbps <= 20.0,
    )

    # Exercise 5 DWPD & TBW check: 8x 3.84 TB drives = 30.72 TB array; 15 TB/day host writes across 8 drives
    # = 1.875 TB/day per drive; with WAF 1.2 -> 2.25 TB/day NAND writes = 0.5859 DWPD (8.53 years lifespan)
    ex5_smart = evaluate_nvme_endurance_and_smart(
        drive_size_tb=3.84,
        rated_dwpd=1.0,
        warranty_years=5,
        daily_host_writes_tb=15.0 / 8.0,
        write_amplification_factor=1.2,
    )
    check(
        28,
        "Striping 15 TB/day of checkpoints across 8x 3.84 TB drives (1.875 TB/drive/day, WAF 1.2) yields 2.25 TB/day NAND writes (0.5859 DWPD, 8.53 years lifespan)",
        ex5_smart.daily_write_tb == 1.875
        and ex5_smart.effective_nand_daily_tb == 2.25
        and ex5_smart.effective_dwpd_used == 0.5859
        and ex5_smart.estimated_lifespan_years == 8.53,
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_lab())
