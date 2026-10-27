"""Chapter 13.5 Verification Lab: BeeGFS, Weka, VAST and object storage.

Run with:
    python3 -B code/part13/beegfs_weka_vast_object_lab.py
"""

from __future__ import annotations

import os
import sys
from typing import Callable, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from beegfs_weka_vast_object import (
    BEEGFS_SERVICES,
    analyze_beegfs_mds_scaling_and_sharding,
    evaluate_beegfs_stripe_throughput,
    evaluate_beegfs_target_fill_balance,
    evaluate_deepseek_3fs_benchmark,
    evaluate_nvme_staging_cache_epochs,
    evaluate_s3_prefix_sharding_and_multipart,
    evaluate_s3_small_object_trap_vs_sharded_pipeline,
    evaluate_vast_dase_and_gds,
    evaluate_wekafs_cluster_architecture,
    map_beegfs_file_offset,
)


def run_checks() -> int:
    checks: List[Tuple[str, Callable[[], bool]]] = []

    def add(desc: str, fn: Callable[[], bool]) -> None:
        checks.append((desc, fn))

    # --- Section 1: BeeGFS Services, Striping, Metadata & Target Balance (V15 Ch. 06) ---
    add(
        "1. BeeGFS defines four decoupled services: beegfs-mgmtd, beegfs-meta, beegfs-storage, and beegfs-client",
        lambda: (
            set(BEEGFS_SERVICES.keys())
            == {"beegfs-mgmtd", "beegfs-meta", "beegfs-storage", "beegfs-client"}
            and BEEGFS_SERVICES["beegfs-meta"]["ops_per_sec_min"] == 50000
            and BEEGFS_SERVICES["beegfs-meta"]["ops_per_sec_max"] == 100000
            and BEEGFS_SERVICES["beegfs-meta"]["healthy_latency_ms_max"] == 5
        ),
    )

    add(
        "2. BeeGFS storage node capacity ranges from 500 MB/s to 2000 MB/s (2 GB/s) with a +/-5% healthy target fill band",
        lambda: (
            BEEGFS_SERVICES["beegfs-storage"]["mb_per_sec_min"] == 500
            and BEEGFS_SERVICES["beegfs-storage"]["mb_per_sec_max"] == 2000
            and BEEGFS_SERVICES["beegfs-storage"]["healthy_fill_skew_pct_max"] == 5
        ),
    )

    add(
        "3. BeeGFS 1 MiB chunksize across 8 targets maps offset 0 to slot 0 (Target 1001) and offset 10 MiB to chunk 10, row 1, slot 2 (Target 2001)",
        lambda: (
            (m0 := map_beegfs_file_offset(0, chunk_size_bytes=1048576)).target_id == 1001
            and m0.chunk_index == 0
            and (m10 := map_beegfs_file_offset(10 * 1048576 + 512, chunk_size_bytes=1048576)).chunk_index == 10
            and m10.stripe_row == 1
            and m10.target_slot == 2
            and m10.target_id == 2001
            and m10.intra_chunk_offset_bytes == 512
        ),
    )

    add(
        "4. BeeGFS 500 GB checkpoint striped across 2 targets at 800 MB/s gets 1.6 GB/s (312.5 s) vs 8 targets getting 6.4 GB/s (78.125 s, 4.0x faster)",
        lambda: (
            (s2 := evaluate_beegfs_stripe_throughput(file_size_gb=500.0, num_targets=2, per_target_mb_s=800.0))[
                "theoretical_gb_s"
            ]
            == 1.6
            and s2["theoretical_write_sec"] == 312.5
            and (s8 := evaluate_beegfs_stripe_throughput(file_size_gb=500.0, num_targets=8, per_target_mb_s=800.0))[
                "theoretical_gb_s"
            ]
            == 6.4
            and s8["theoretical_write_sec"] == 78.125
            and s8["sustained_gb_s"] == 5.0
        ),
    )

    add(
        "5. BeeGFS 12-target training/checkpoint pattern at 800 MB/s/target yields 9.6 GB/s theoretical throughput (52.0833 s for 500 GB)",
        lambda: (
            (s12 := evaluate_beegfs_stripe_throughput(file_size_gb=500.0, num_targets=12, per_target_mb_s=800.0))[
                "theoretical_gb_s"
            ]
            == 9.6
            and s12["theoretical_write_sec"] == 52.0833
        ),
    )

    add(
        "6. 256 GPUs generating 204,800 metadata ops/sec saturate 1 MDS (50K ops/sec, needing >= 5 MDSs), while 100x WebDataset sharding drops load to 2,048 ops/sec",
        lambda: (
            (mds := analyze_beegfs_mds_scaling_and_sharding(num_gpus=256, raw_ops_per_gpu_epoch_start=800, mds_count=1))[
                "raw_peak_ops_sec"
            ]
            == 204800
            and mds["raw_saturated"] is True
            and mds["mds_needed_for_raw"] == 5
            and mds["sharded_ops_sec"] == 2048
            and mds["sharded_saturated"] is False
        ),
    )

    add(
        "7. BeeGFS target fill check flags storage1 (45%, 44%) vs storage2 (72%, 71%) as a 28% spread (> 10% investigation threshold, outside +/-5% band)",
        lambda: (
            (
                bal := evaluate_beegfs_target_fill_balance(
                    [
                        (1001, "storage1", 4.5, 10.0),
                        (1002, "storage1", 4.4, 10.0),
                        (2001, "storage2", 7.2, 10.0),
                        (2002, "storage2", 7.1, 10.0),
                    ]
                )
            )["max_spread_pct"]
            == 28.0
            and bal["within_healthy_plus_minus_5pct"] is False
            and bal["requires_rebalance_investigation"] is True
            and bal["overloaded_target_ids"] == [2001, 2002]
        ),
    )

    # --- Section 2: WekaFS Distributed Virtual Metadata & Tiering (ADC Ch. 9, AISPE Ch. 5) ---
    add(
        "8. WekaFS 8-node cluster with 6+2 erasure coding achieves 75.0% usable NVMe capacity (2.25x more usable capacity than 3x replication)",
        lambda: (
            (w := evaluate_wekafs_cluster_architecture(num_storage_nodes=8, data_chunks_n=6, parity_chunks_k=2))[
                "ec_efficiency_pct"
            ]
            == 75.0
            and w["capacity_gain_vs_3x_rep"] == 2.25
            and w["supports_gds_rdma"] is True
        ),
    )

    add(
        "9. WekaFS 18-node cluster with 16+2 erasure coding achieves 88.89% usable NVMe efficiency and pins dedicated client cores (4/128 = 3.125% core tax)",
        lambda: (
            (
                w18 := evaluate_wekafs_cluster_architecture(
                    num_storage_nodes=18,
                    data_chunks_n=16,
                    parity_chunks_k=2,
                    client_pinned_cores_per_gpu_node=4,
                    total_cores_per_gpu_node=128,
                )
            )["ec_efficiency_pct"]
            == 88.89
            and w18["client_core_tax_pct"] == 3.125
        ),
    )

    add(
        "10. WekaFS unifies Tier 1 hot NVMe-o-RDMA storage (737.28 TB usable on 8 nodes) with Tier 2 S3 object storage (2000 TB) into a 2737.28 TB POSIX namespace",
        lambda: (
            (w := evaluate_wekafs_cluster_architecture())["raw_nvme_tb"] == 983.04
            and w["usable_tier1_nvme_tb"] == 737.28
            and w["unified_posix_namespace_tb"] == 2737.28
        ),
    )

    add(
        "11. WekaFS rejects N+K stripe widths that exceed the number of failure-domain storage nodes",
        lambda: _raises_value_error(
            lambda: evaluate_wekafs_cluster_architecture(num_storage_nodes=6, data_chunks_n=6, parity_chunks_k=2)
        ),
    )

    # --- Section 3: VAST Data DASE Architecture & GPUDirect Storage (ADC Ch. 9, AISPE Ch. 5) ---
    add(
        "12. VAST DASE decouples stateless CNodes from NVMe-oF DNodes (SCM/Optane write buffer + QLC flash) with zero east-west CNode lock traffic",
        lambda: (
            (v := evaluate_vast_dase_and_gds())["cnode_stateful"] is False
            and v["cnode_east_west_lock_traffic"] is False
            and "SCM" in str(v["write_buffer_media"])
            and "QLC" in str(v["capacity_media"])
        ),
    )

    add(
        "13. VAST DASE wide 146+4 erasure stripe achieves 97.33% net capacity efficiency (only 2.67% parity overhead across DNodes)",
        lambda: (
            (v := evaluate_vast_dase_and_gds(ec_data_strips=146, ec_parity_strips=4))["ec_efficiency_pct"] == 97.33
            and v["ec_overhead_pct"] == 2.67
            and v["usable_qlc_tb"] == 1460.0
            and v["effective_logical_tb"] == 2920.0
        ),
    )

    add(
        "14. NVIDIA gdsio benchmark shows GDS (-x 0) raises throughput from 8.0 GB/s (-x 2 CPU path) to 9.6 GB/s (+20.0%) and cuts latency from 1.25 ms to 1.00 ms (-20.0%)",
        lambda: (
            (v := evaluate_vast_dase_and_gds())["gds_cpu_path_flag"] == "-x 2"
            and v["gds_direct_path_flag"] == "-x 0"
            and v["gds_a100_throughput_uplift_pct"] == 20.0
            and v["gds_latency_reduction_pct"] == 20.0
            and v["gds_h100_throughput_uplift_pct"] == 30.0
        ),
    )

    # --- Section 4: DeepSeek Fire-Flyer File System (3FS) vs Ceph (AISPE Ch. 5) ---
    add(
        "15. DeepSeek 3FS comprises 4 RDMA-connected components (Cluster Manager, Metadata Service, Storage Service, Client) and bypasses the OS page cache via O_DIRECT + io_uring",
        lambda: (
            (fs := evaluate_deepseek_3fs_benchmark())["components"]
            == ("Cluster Manager", "Metadata Service", "Storage Service", "Client")
            and fs["bypasses_os_page_cache"] is True
            and fs["uses_o_direct_and_io_uring_and_rdma"] is True
            and fs["standard_fuse_supports_kernel_gds"] is False
        ),
    )

    add(
        "16. DeepSeek 3FS 68-node cluster (680 x 16 TB NVMe = 10,880 TB, dual 100 Gb/s NICs) achieves 6.6 TB/s read (+ 1.4 TB/s background = 8.0 TB/s, up to 7.3 TB/s peak)",
        lambda: (
            (fs := evaluate_deepseek_3fs_benchmark())["total_nvme_drives"] == 680
            and fs["total_raw_capacity_tb"] == 10880
            and fs["per_node_network_gbps"] == 200
            and fs["cluster_line_rate_tb_s"] == 1.7
            and fs["achieved_read_tb_s"] == 6.6
            and fs["background_traffic_tb_s"] == 1.4
            and fs["combined_io_tb_s"] == 8.0
            and fs["peak_reported_tb_s"] == 7.3
        ),
    )

    add(
        "17. DeepSeek 3FS delivers 97.06 GB/s per storage node and outperforms Ceph (1.1 TB/s) by 6.0x at 6.6 TB/s and 6.64x at 7.3 TB/s",
        lambda: (
            (fs := evaluate_deepseek_3fs_benchmark())["per_node_achieved_gb_s"] == 97.06
            and fs["speedup_vs_ceph_at_6_6_tb_s"] == 6.0
            and fs["speedup_vs_ceph_at_peak"] == 6.64
        ),
    )

    # --- Section 5: Object Storage Prefix Sharding, Multipart Math & Cache Staging (V15 Ch. 07) ---
    add(
        "18. Fetching 2,000,000 small 260 KB objects serially from S3 at 150 ms/request wastes 300,000 seconds (83.33 hours) on HTTP/TLS API latency alone",
        lambda: (
            (s3 := evaluate_s3_small_object_trap_vs_sharded_pipeline())["serial_api_wait_sec"] == 300000.0
            and s3["serial_api_wait_hours"] == 83.33
        ),
    )

    add(
        "19. Prefetching 2 x 10 GB shards (20 GB) with 8 workers at 150 MB/s each (1.2 GB/s aggregate) takes 16.67 s transfer + 10.2 s API/TLS = 26.87 s (~27 s) to first batch",
        lambda: (
            (s3 := evaluate_s3_small_object_trap_vs_sharded_pipeline())["aggregate_worker_mb_s"] == 1200.0
            and s3["aggregate_worker_gb_s"] == 1.2
            and s3["prefetch_transfer_sec"] == 16.67
            and s3["api_and_tls_overhead_sec"] == 10.2
            and s3["startup_time_to_first_batch_sec"] == 26.87
        ),
    )

    add(
        "20. Doubling S3 download workers from 8 to 16 (2.4 GB/s aggregate) cuts 20 GB transfer time to 8.33 s (18.53 s total with API/TLS)",
        lambda: (
            (s16 := evaluate_s3_small_object_trap_vs_sharded_pipeline(num_download_workers=16))["aggregate_worker_gb_s"]
            == 2.4
            and s16["prefetch_transfer_sec"] == 8.33
            and s16["startup_time_to_first_batch_sec"] == 18.53
        ),
    )

    add(
        "21. S3 prefix sharding across 16 prefixes scales request ceilings from 5,500 GET/s and 3,500 PUT/s to 88,000 GET/s and 56,000 PUT/s",
        lambda: (
            (p := evaluate_s3_prefix_sharding_and_multipart(num_prefixes=16))["aggregate_get_ops_s"] == 88000
            and p["aggregate_put_ops_s"] == 56000
        ),
    )

    add(
        "22. Parallel 8 x 1 GB S3 download finishes in 7.5 s (1066.67 MB/s aggregate, 133.33 MB/s per worker) vs 6.2 s single-object (161.29 MB/s) and 49.6 s serial (6.61x speedup)",
        lambda: (
            (p := evaluate_s3_prefix_sharding_and_multipart())["single_object_mb_s"] == 161.29
            and p["serial_eight_elapsed_s"] == 49.6
            and p["parallel_aggregate_mb_s"] == 1066.67
            and p["parallel_per_worker_mb_s"] == 133.33
            and p["speedup_factor"] == 6.61
        ),
    )

    add(
        "23. Local NVMe staging cache warms from 0.1% hit rate (45.3 min wait) in Epoch 1 to 98.2% (2.1 min wait, 21.57x wait reduction) in Epoch 2",
        lambda: (
            (c := evaluate_nvme_staging_cache_epochs())["epoch_1_cold_hit_rate_pct"] == 0.1
            and c["epoch_1_download_wait_min"] == 45.3
            and c["epoch_2_warm_hit_rate_pct"] == 98.2
            and c["epoch_2_download_wait_min"] == 2.1
            and c["wait_reduction_ep1_to_ep2"] == 21.57
        ),
    )

    add(
        "24. Local NVMe staging cache detects LRU eviction onset in Epoch 3 when cache fill (88.0%) exceeds the 85.0% threshold and hit rate dips to 97.5% (3.5 min wait)",
        lambda: (
            (c := evaluate_nvme_staging_cache_epochs())["epoch_3_eviction_hit_rate_pct"] == 97.5
            and c["epoch_3_download_wait_min"] == 3.5
            and c["eviction_active_epochs"] == [3]
        ),
    )

    add(
        "25. GB200/GB300 NVL72 rack (72 GPUs x 200 MB/s per GPU) requires 14.4 GB/s (14-20 GB/s envelope) of sustained storage ingestion bandwidth",
        lambda: (72 * 200) / 1000.0 == 14.4 and 14.0 <= (72 * 200) / 1000.0 <= 20.0,
    )

    add(
        "26. Reducing GPU I/O wait time from 30% to 5% lowers the I/O stall fraction by 6.0x and recovers 25 percentage points of active GPU compute time",
        lambda: (30.0 / 5.0) == 6.0 and (30.0 - 5.0) == 25.0,
    )

    print("=== Chapter 13.5 Lab: BeeGFS, Weka, VAST and Object Storage ===")
    passed = 0
    failed = 0
    for desc, fn in checks:
        try:
            ok = bool(fn())
        except Exception as exc:
            ok = False
            print(f"  [FAIL] {desc} (exception: {exc})")
        else:
            if ok:
                print(f"  [PASS] {desc}")
            else:
                print(f"  [FAIL] {desc}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def _raises_value_error(fn: Callable[[], object]) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(run_checks())
