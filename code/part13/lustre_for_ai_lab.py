#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 13.4: Lustre for AI.

Run with:
    python3 -B code/part13/lustre_for_ai_lab.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lustre_for_ai import (
    GiB,
    KiB,
    LNetRailNID,
    MiB,
    audit_lnet_multirail_and_osts,
    calculate_client_rpc_bdp,
    compare_gdsio_paths,
    default_ai_pfl_layout,
    evaluate_lctl_metadata_stats,
    evaluate_pfl_dom_file,
    map_raid0_read_window,
    model_checkpoint_write_strategy,
    model_dne_metadata_scaling,
)


def run_lab() -> int:
    passed = 0
    failed = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} :: {detail}")

    print("=== Chapter 13.4 Lab: Lustre for AI Workloads ===")

    # ------------------------------------------------------------------
    # Section 1: Progressive File Layout (PFL) + Data-on-MDT (DoM) & RAID0 Striping
    # ------------------------------------------------------------------
    layout = default_ai_pfl_layout()

    tiny_res = evaluate_pfl_dom_file(file_size_bytes=260 * KiB, components=layout, total_osts=24)
    check(
        "1. 260 KiB file with DoM (-E 1M -L mdt) stays 100% on the MDT with 0 OST objects",
        tiny_res["uses_dom_only"] is True
        and tiny_res["mdt_dom_bytes"] == 260 * KiB
        and tiny_res["active_ost_count"] == 0,
        str(tiny_res),
    )

    small_res = evaluate_pfl_dom_file(file_size_bytes=32 * MiB, components=layout, total_osts=24)
    check(
        "2. 32 MiB file puts first 1 MiB on DoM MDT and remaining 31 MiB on exactly 1 OST",
        small_res["mdt_dom_bytes"] == 1 * MiB
        and small_res["active_ost_count"] == 1
        and sum(small_res["ost_bytes"]) == 31 * MiB,
        str(small_res),
    )

    med_res = evaluate_pfl_dom_file(file_size_bytes=512 * MiB, components=layout, total_osts=24)
    check(
        "3. 512 MiB shard activates 3 PFL components (DoM 1 MiB, 1-OST 63 MiB, 4-OST 448 MiB)",
        len(med_res["instantiated_components"]) == 3
        and med_res["active_ost_count"] == 4
        and med_res["mdt_dom_bytes"] == 1 * MiB,
        str(med_res),
    )

    large_res = evaluate_pfl_dom_file(file_size_bytes=10 * GiB, components=layout, total_osts=24)
    check(
        "4. 10 GiB checkpoint file expands into the final PFL component (-E -1 -c -1) across all 24 OSTs",
        len(large_res["instantiated_components"]) == 4
        and large_res["active_ost_count"] == 24
        and sum(large_res["ost_bytes"]) == 10 * GiB - 1 * MiB,
        str(large_res),
    )

    raid0_1gb = map_raid0_read_window(
        offset_bytes=0,
        length_bytes=1024 * MiB,
        stripe_size_bytes=1 * MiB,
        stripe_count=2,
    )
    first_six_slots = [slot for _, slot, _ in raid0_1gb["chunk_sequence"][:6]]
    check(
        "5. RAID0 2-stripe 1 GiB file alternates 1 MiB chunks round-robin [0,1,0,1,0,1] (512 MiB per OST)",
        first_six_slots == [0, 1, 0, 1, 0, 1]
        and raid0_1gb["per_slot_bytes"] == [512 * MiB, 512 * MiB],
        str(first_six_slots),
    )

    small_read = map_raid0_read_window(
        offset_bytes=0,
        length_bytes=512 * KiB,
        stripe_size_bytes=1 * MiB,
        stripe_count=8,
    )
    check(
        "6. Sub-stripe 512 KiB read on an 8-stripe file touches only 1 OST (no stripe parallelism)",
        small_read["parallel_ost_fanout"] == 1 and small_read["touched_slots"] == [0],
        str(small_read),
    )

    wide_read = map_raid0_read_window(
        offset_bytes=0,
        length_bytes=16 * MiB,
        stripe_size_bytes=2 * MiB,
        stripe_count=8,
    )
    check(
        "7. 16 MiB sequential batch read with 2 MiB stripe_size fans out evenly across all 8 OSTs",
        wide_read["parallel_ost_fanout"] == 8
        and wide_read["per_slot_bytes"] == [2 * MiB] * 8,
        str(wide_read),
    )

    # ------------------------------------------------------------------
    # Section 2: Metadata Scaling (DNE Phase 1 & 2, lctl stats, and Sharding)
    # ------------------------------------------------------------------
    healthy_meta = evaluate_lctl_metadata_stats(
        open_samples=150_000,
        window_sec=60.0,
        avg_open_us=2100.0,
        max_open_us=5400.0,
        getattr_samples=300_000,
    )
    check(
        "8. Healthy lctl llite stats (2.1 ms avg open, 5.4 ms max, 7.5K ops/sec) reports HEALTHY_HEADROOM",
        healthy_meta["status"] == "HEALTHY_HEADROOM"
        and healthy_meta["avg_open_ms"] == 2.1
        and healthy_meta["max_open_ms"] == 5.4,
        str(healthy_meta),
    )

    sat_meta = evaluate_lctl_metadata_stats(
        open_samples=950_000,
        window_sec=60.0,
        avg_open_us=45_200.0,
        max_open_us=65_400.0,
        getattr_samples=1_900_000,
    )
    check(
        "9. Saturated lctl llite stats (45.2 ms avg open, 65.4 ms max, 15.83K opens/s, 3800000 total samples = 63333.33/s) flags METADATA_SATURATED",
        sat_meta["status"] == "METADATA_SATURATED"
        and sat_meta["avg_open_ms"] == 45.2
        and sat_meta["max_open_ms"] == 65.4
        and sat_meta["total_samples_with_close"] == 3800000
        and abs(sat_meta["total_rate_with_close_per_sec"] - 63333.33) < 0.1
        and abs(sat_meta["open_rate_per_sec"] - 15833.33) < 0.1,
        str(sat_meta),
    )

    dne_p1_single_dir = model_dne_metadata_scaling(
        file_count=200_000,
        mdt_count=4,
        ops_per_mdt_sec=50_000.0,
        dne_phase=1,
        directory_count=1,
    )
    check(
        "10. DNE Phase 1 with all 200K files in 1 directory only uses 1 active MDT (50K ops/s, 4.0 s)",
        dne_p1_single_dir["active_mdts"] == 1
        and dne_p1_single_dir["aggregate_iops_capacity"] == 50_000.0
        and dne_p1_single_dir["epoch_open_time_sec"] == 4.0,
        str(dne_p1_single_dir),
    )

    dne_p2_striped_dir = model_dne_metadata_scaling(
        file_count=200_000,
        mdt_count=4,
        ops_per_mdt_sec=50_000.0,
        dne_phase=2,
        directory_count=1,
    )
    check(
        "11. DNE Phase 2 (lfs setdirstripe -c 4) hashes 1 directory across all 4 MDTs (200K ops/s, 1.0 s)",
        dne_p2_striped_dir["active_mdts"] == 4
        and dne_p2_striped_dir["aggregate_iops_capacity"] == 200_000.0
        and dne_p2_striped_dir["epoch_open_time_sec"] == 1.0,
        str(dne_p2_striped_dir),
    )

    repackaged_5m = model_dne_metadata_scaling(
        file_count=5000000,
        mdt_count=1,
        ops_per_mdt_sec=50000.0,
        dne_phase=1,
        files_per_shard=100,
    )
    check(
        "12. Repackaging 5M files into 50K shards (100 files/shard) cuts open calls 100x (100 s -> 1.0 s)",
        repackaged_5m["effective_opens"] == 50000
        and repackaged_5m["metadata_reduction_factor"] == 100.0
        and repackaged_5m["epoch_open_time_sec"] == 1.0,
        str(repackaged_5m),
    )

    repackaged_10m = model_dne_metadata_scaling(
        file_count=10000000,
        mdt_count=4,
        ops_per_mdt_sec=50000.0,
        dne_phase=2,
        files_per_shard=100000,
    )
    check(
        "13. Repackaging 10M files (2.6 TB at 260 KB) into 100 shards of 26 GB cuts opens to 100 (0.0005 s across 4 MDTs)",
        repackaged_10m["effective_opens"] == 100
        and repackaged_10m["metadata_reduction_factor"] == 100000.0
        and repackaged_10m["epoch_open_time_sec"] == 0.0005,
        str(repackaged_10m),
    )

    # ------------------------------------------------------------------
    # Section 3: Client RPC BDP Calculator & GPUDirect Storage (gdsio)
    # ------------------------------------------------------------------
    rpc_default = calculate_client_rpc_bdp(
        max_rpcs_in_flight=8,
        max_pages_per_rpc=256,
        page_size_bytes=4096,
        rtt_us=500.0,
        active_osts=1,
        per_ost_cap_mbps=5000.0,
        client_nic_gbps=400.0,
    )
    check(
        "14. Default OSC RPC (8 in-flight, 256 pages = 1 MiB) at 500 us RTT caps single-OST BDP at 16777.22 MB/s",
        rpc_default["rpc_size_mib"] == 1.0
        and rpc_default["in_flight_mib_per_ost"] == 8.0
        and abs(rpc_default["bdp_mbps_per_ost"] - 16777.22) < 0.1,
        str(rpc_default),
    )

    rpc_long_rtt_untuned = calculate_client_rpc_bdp(
        max_rpcs_in_flight=8,
        max_pages_per_rpc=256,
        page_size_bytes=4096,
        rtt_us=4000.0,
        active_osts=1,
        per_ost_cap_mbps=6000.0,
        client_nic_gbps=400.0,
    )
    rpc_long_rtt_tuned = calculate_client_rpc_bdp(
        max_rpcs_in_flight=64,
        max_pages_per_rpc=1024,
        page_size_bytes=4096,
        rtt_us=4000.0,
        active_osts=8,
        per_ost_cap_mbps=6000.0,
        client_nic_gbps=400.0,
    )
    check(
        "15. Tuning max_rpcs_in_flight=64 & max_pages_per_rpc=1024 (4 MiB) across 8 OSTs raises BDP from 2097.15 MB/s to 67108.86 MB/s and saturates 48 GB/s on 400G",
        rpc_long_rtt_untuned["bdp_mbps_per_ost"] == 2097.15
        and rpc_long_rtt_tuned["bdp_mbps_per_ost"] == 67108.86
        and rpc_long_rtt_tuned["rpc_size_mib"] == 4.0
        and rpc_long_rtt_tuned["in_flight_mib_per_ost"] == 256.0
        and rpc_long_rtt_tuned["aggregate_client_mbps"] == 48000.0,
        f"untuned={rpc_long_rtt_untuned}, tuned={rpc_long_rtt_tuned}",
    )

    gds_cmp = compare_gdsio_paths(
        cpu_path_gbps=8.0,
        cpu_path_lat_ms=1.25,
        gds_path_gbps=9.6,
        gds_path_lat_ms=1.00,
    )
    check(
        "16. gdsio direct GDS path (-x 0: 9.6 GB/s, 1.00 ms) vs CPU path (-x 2: 8.0 GB/s, 1.25 ms) gives +20% BW & -20% latency",
        gds_cmp["throughput_gain_pct"] == 20.0
        and gds_cmp["latency_reduction_pct"] == 20.0,
        str(gds_cmp),
    )

    # ------------------------------------------------------------------
    # Section 4: Checkpoint Striping (N-to-1 Lock Contention vs N-to-N Sharded)
    # ------------------------------------------------------------------
    ckpt_1ost_800 = model_checkpoint_write_strategy(
        checkpoint_gb=500.0,
        num_ranks=64,
        total_osts=24,
        per_ost_write_mbps=800.0,
        strategy="n_to_1_single_ost",
        stripe_count=1,
    )
    check(
        "17. 500 GB checkpoint to single OST at 800 MB/s takes 625.0 seconds",
        ckpt_1ost_800["used_osts"] == 1
        and ckpt_1ost_800["effective_bw_gbps"] == 0.8
        and ckpt_1ost_800["write_time_sec"] == 625.0,
        str(ckpt_1ost_800),
    )

    ckpt_24ost_500 = model_checkpoint_write_strategy(
        checkpoint_gb=500.0,
        num_ranks=64,
        total_osts=24,
        per_ost_write_mbps=500.0,
        strategy="n_to_n_sharded",
        stripe_count=1,
    )
    check(
        "18. 500 GB sharded checkpoint across 24 OSTs (20.83 GB/OST, 7.81 GB/rank) at 500 MB/s/OST reaches 12.0 GB/s (41.67 s / 41.7 s)",
        ckpt_24ost_500["used_osts"] == 24
        and ckpt_24ost_500["per_ost_gb"] == 20.83
        and ckpt_24ost_500["per_rank_gb"] == 7.81
        and ckpt_24ost_500["effective_bw_gbps"] == 12.0
        and ckpt_24ost_500["write_time_sec"] == 41.67
        and ckpt_24ost_500["write_time_sec_1dp"] == 41.7,
        str(ckpt_24ost_500),
    )

    ckpt_unaligned = model_checkpoint_write_strategy(
        checkpoint_gb=500.0,
        num_ranks=64,
        total_osts=12,
        per_ost_write_mbps=1000.0,
        strategy="n_to_1_unaligned_ldlm",
        stripe_count=12,
        stripe_aligned=False,
    )
    ckpt_sharded_12 = model_checkpoint_write_strategy(
        checkpoint_gb=500.0,
        num_ranks=64,
        total_osts=12,
        per_ost_write_mbps=1000.0,
        strategy="n_to_n_sharded",
        stripe_count=2,
    )
    check(
        "19. Unaligned N-to-1 shared write suffers 4x LDLM extent lock slowdown (3.0 GB/s, 166.67 s / 166.7 s vs 12.0 GB/s, 41.67 s N-to-N)",
        ckpt_unaligned["effective_bw_gbps"] == 3.0
        and ckpt_unaligned["write_time_sec"] == 166.67
        and ckpt_unaligned["write_time_sec_1dp"] == 166.7
        and ckpt_sharded_12["effective_bw_gbps"] == 12.0
        and abs(ckpt_unaligned["write_time_sec"] / ckpt_sharded_12["write_time_sec"] - 4.0) < 0.01,
        f"unaligned={ckpt_unaligned}, sharded={ckpt_sharded_12}",
    )

    # ------------------------------------------------------------------
    # Section 5: LNet Multi-Rail Health, OST Fill Skew, and OSS RAM Sizing
    # ------------------------------------------------------------------
    rails_healthy = [
        LNetRailNID("10.20.4.15@o2ib0", "o2ib", 0, "ib0", numa_node=0, gpu_numa_node=0, link_up=True, rate_gbps=400.0, peer_credits=128),
        LNetRailNID("10.20.4.16@o2ib0", "o2ib", 0, "ib1", numa_node=1, gpu_numa_node=1, link_up=True, rate_gbps=400.0, peer_credits=128),
    ]
    ost_balanced = [49.0, 49.0, 49.0, 49.0, 49.0, 49.0]
    audit_ok = audit_lnet_multirail_and_osts(
        rails=rails_healthy,
        ost_used_pct=ost_balanced,
        num_clients=120,
        osts_per_oss=6,
    )
    check(
        "20. Dual 400G o2ib0 rails NUMA-aligned + 6 OSTs at 49% report BALANCED and 800.0 Gbps",
        audit_ok["healthy_rail_count"] == 2
        and audit_ok["numa_aligned_rail_count"] == 2
        and audit_ok["aggregate_healthy_gbps"] == 800.0
        and audit_ok["ost_balance_status"] == "BALANCED",
        str(audit_ok),
    )

    check(
        "21. OSS RAM sizing formula (400+600+1.5*N_threads MB/OST; 2+1*N_OSTs GB/OSS) matches 1030 MB and 8.0 GB",
        audit_ok["threads_per_ost_est"] == 20.0
        and audit_ok["per_ost_ram_mb"] == 1030.0
        and audit_ok["recommended_oss_ram_gb"] == 8.0,
        str(audit_ok),
    )

    rails_degraded = [
        LNetRailNID("10.20.4.15@o2ib0", "o2ib", 0, "ib0", numa_node=0, gpu_numa_node=0, link_up=True, rate_gbps=400.0, peer_credits=128),
        LNetRailNID("10.20.4.16@o2ib0", "o2ib", 0, "ib1", numa_node=1, gpu_numa_node=0, link_up=False, rate_gbps=400.0, peer_credits=128, tx_Queued_errors=14),
    ]
    ost_skewed = [98.0, 60.0, 60.0, 60.0, 60.0, 60.0]
    audit_bad = audit_lnet_multirail_and_osts(
        rails=rails_degraded,
        ost_used_pct=ost_skewed,
        num_clients=120,
        osts_per_oss=6,
    )
    check(
        "22. Down LNet rail + OST0 at 98% vs OST1-5 at 60% (38% skew) flags IMBALANCED_MIGRATE_REQUIRED on OST 0",
        audit_bad["healthy_rail_count"] == 1
        and audit_bad["aggregate_healthy_gbps"] == 400.0
        and audit_bad["ost_fill_skew_pct"] == 38.0
        and audit_bad["imbalanced_osts"] == [0]
        and audit_bad["ost_balance_status"] == "IMBALANCED_MIGRATE_REQUIRED",
        str(audit_bad),
    )

    # ------------------------------------------------------------------
    # Section 6: SuperPOD High-Performance Storage (HPS) Aggregate Tier Verification
    # ------------------------------------------------------------------
    # SuperPOD GB300 Table 5: Standard (90 GB/s read, 45 GB/s write per SU; 360 / 180 GB/s for 4 SU)
    # and Enhanced (280 GB/s read, 140 GB/s write per SU; 1,120 / 560 GB/s for 4 SU)
    su1_std_read, su1_std_write = 90.0, 45.0
    su1_enh_read, su1_enh_write = 280.0, 140.0
    su4_std_read, su4_std_write = 360.0, 180.0
    su4_enh_read, su4_enh_write = 1120.0, 560.0
    check(
        "23. SuperPOD HPS 4-SU read/write targets scale linearly (4x single-SU: 360/180 GB/s Std, 1120/560 GB/s Enh)",
        su4_std_read == 4 * su1_std_read
        and su4_std_write == 4 * su1_std_write
        and su4_enh_read == 4 * su1_enh_read
        and su4_enh_write == 4 * su1_enh_write,
        "SuperPOD linear scaling check",
    )

    # 1,120 GB/s Enhanced 4-SU read requires at least 28 OSTs at 40 GB/s NVMe OSS or 224 OSTs at 5 GB/s
    ckpt_4su_enh = model_checkpoint_write_strategy(
        checkpoint_gb=5600.0,
        num_ranks=2304,
        total_osts=112,
        per_ost_write_mbps=5000.0,
        strategy="n_to_n_sharded",
        stripe_count=1,
    )
    check(
        "24. 4-SU Enhanced HPS (560 GB/s across 112 NVMe OSTs at 5 GB/s) writes a 5.6 TB checkpoint in 10.0 s",
        ckpt_4su_enh["effective_bw_gbps"] == 560.0
        and ckpt_4su_enh["write_time_sec"] == 10.0,
        str(ckpt_4su_enh),
    )

    # 8-OST AI dataset stripe at 800 MB/s/OST = 6.4 GB/s vs 2-OST = 1.6 GB/s (V15 Ch 5)
    stripe2_bw = 2 * 800.0 / 1000.0
    stripe8_bw = 8 * 800.0 / 1000.0
    check(
        "25. Increasing dataset stripe_count from 2 to 8 at 800 MB/s per OST scales file read bandwidth from 1.6 to 6.4 GB/s",
        stripe2_bw == 1.6 and stripe8_bw == 6.4 and stripe8_bw / stripe2_bw == 4.0,
        f"2-stripe={stripe2_bw}, 8-stripe={stripe8_bw}",
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
