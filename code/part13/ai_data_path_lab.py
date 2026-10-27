"""Self-checking verification lab for Chapter 13.1: The AI data path: from storage to GPU.

Run directly with:
    python3 -B code/part13/ai_data_path_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_data_path import (  # noqa: E402
    EIGHT_LAYER_DATA_PATH,
    FIVE_AI_WORKLOAD_PHASES,
    STORAGE_TIERS,
    compare_traditional_vs_gds_path,
    compute_cluster_storage_scaling,
    evaluate_metadata_bottleneck,
    evaluate_numa_pcie_locality,
    evaluate_page_cache_vs_odirect,
)


def main() -> int:
    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"[PASS] {name}")
        else:
            failed += 1
            print(f"[FAIL] {name}: {detail}")

    # 1. Verify all 5 AI storage lifecycle workload phases
    phase_names = [p.phase for p in FIVE_AI_WORKLOAD_PHASES]
    check(
        "five_workload_phases_defined",
        phase_names
        == [
            "ingest",
            "preprocessing",
            "training_reads",
            "checkpoint_writes",
            "inference_rag_kv",
        ],
        f"got {phase_names}",
    )

    phase_map = {p.phase: p for p in FIVE_AI_WORKLOAD_PHASES}
    check(
        "ingest_phase_write_dominant",
        phase_map["ingest"].write_fraction == 0.80
        and phase_map["ingest"].block_size_kb == 4096,
        f"got {phase_map['ingest']}",
    )
    check(
        "preprocessing_phase_balanced_io",
        phase_map["preprocessing"].read_fraction == 0.55
        and phase_map["preprocessing"].write_fraction == 0.45,
        f"got {phase_map['preprocessing']}",
    )
    check(
        "training_reads_phase_high_read_and_metadata",
        phase_map["training_reads"].read_fraction == 0.98
        and phase_map["training_reads"].metadata_ops_per_sec_max == 500_000,
        f"got {phase_map['training_reads']}",
    )
    check(
        "checkpoint_writes_phase_burst_write",
        phase_map["checkpoint_writes"].write_fraction == 0.99
        and phase_map["checkpoint_writes"].block_size_kb == 8192,
        f"got {phase_map['checkpoint_writes']}",
    )
    check(
        "inference_rag_kv_phase_low_latency_64kb",
        phase_map["inference_rag_kv"].block_size_kb == 64
        and phase_map["inference_rag_kv"].read_fraction == 0.85,
        f"got {phase_map['inference_rag_kv']}",
    )

    # 2. Verify 4 storage tiers and 8 data-path layers
    check(
        "four_storage_tiers_ordered",
        [t.tier_id for t in STORAGE_TIERS] == [0, 1, 2, 3]
        and STORAGE_TIERS[0].typical_bandwidth_gbps == 3350.0
        and STORAGE_TIERS[1].typical_capacity_gb == 30_720.0,
        f"got {STORAGE_TIERS}",
    )
    check(
        "eight_data_path_layers_complete",
        len(EIGHT_LAYER_DATA_PATH) == 8
        and EIGHT_LAYER_DATA_PATH[0].order == 1
        and EIGHT_LAYER_DATA_PATH[-1].order == 8,
        f"got len={len(EIGHT_LAYER_DATA_PATH)}",
    )

    # 3. Verify Metadata Server (MDS) bottleneck math (128 workers, 150 MB/s, 220 KB vs 10 MB shards)
    small_file_run = evaluate_metadata_bottleneck(
        num_workers=128,
        target_mb_per_s_per_worker=150.0,
        avg_file_size_kb=220.0,
        mds_capacity_ops_per_s=50_000,
        num_osts=48,
        ost_bw_mb_per_s=800.0,
    )
    check(
        "lustre_raw_ost_bandwidth_38_4_gbs",
        small_file_run["raw_array_bw_gb_s"] == 38.4
        and small_file_run["expected_agg_bw_gb_s"] == 19.2,
        f"got {small_file_run}",
    )
    check(
        "small_files_220kb_saturate_mds",
        small_file_run["is_mds_bottlenecked"] is True
        and 87_000 <= small_file_run["required_open_ops_per_s"] <= 87_500
        and small_file_run["mds_overload_pct"] >= 74.0,
        f"got {small_file_run}",
    )

    sharded_run = evaluate_metadata_bottleneck(
        num_workers=128,
        target_mb_per_s_per_worker=150.0,
        avg_file_size_kb=10_000.0,  # 10 MB shards
        mds_capacity_ops_per_s=50_000,
        num_osts=48,
        ost_bw_mb_per_s=800.0,
    )
    check(
        "sharded_10mb_files_relieve_mds",
        sharded_run["is_mds_bottlenecked"] is False
        and sharded_run["required_open_ops_per_s"] == 1920.0
        and sharded_run["estimated_delivered_bw_gb_s"] == 19.2,
        f"got {sharded_run}",
    )

    # 10-node (80 A100) production story: 800 MB shards -> metadata drops well below 50K/s
    ten_node_sharded = evaluate_metadata_bottleneck(
        num_workers=10,
        target_mb_per_s_per_worker=150.0,
        avg_file_size_kb=800_000.0,
        mds_capacity_ops_per_s=50_000,
    )
    check(
        "ten_node_sharded_bandwidth_restored",
        ten_node_sharded["is_mds_bottlenecked"] is False
        and ten_node_sharded["estimated_delivered_bw_gb_s"] == 1.5,
        f"got {ten_node_sharded}",
    )

    # 4. Verify Traditional Bounce-Buffer Path (3+ copies) vs GPUDirect Storage (1 DMA copy)
    pinned_cmp = compare_traditional_vs_gds_path(
        payload_gb=10.0,
        pcie_gen_bw_gb_s=32.0,
        host_dram_bw_gb_s=32.0,
        pinned_memory=True,
    )
    check(
        "traditional_pinned_path_has_3_copies_and_2_pcie_crossings",
        pinned_cmp["traditional_memory_copies"] == 3
        and pinned_cmp["traditional_pcie_traversals"] == 2
        and pinned_cmp["traditional_dram_traffic_gb"] == 40.0,
        f"got {pinned_cmp}",
    )
    check(
        "gds_path_has_1_dma_copy_and_0_host_dram_payload",
        pinned_cmp["gds_memory_copies"] == 1
        and pinned_cmp["gds_pcie_traversals"] == 1
        and pinned_cmp["gds_cpu_memcpy_calls"] == 0
        and pinned_cmp["gds_dram_traffic_gb"] == 0.0,
        f"got {pinned_cmp}",
    )
    check(
        "gdsio_benchmark_8_0_vs_9_6_gbs_uplift_20_pct",
        pinned_cmp["traditional_effective_bw_gb_s"] == 8.0
        and pinned_cmp["gds_effective_bw_gb_s"] == 9.6
        and pinned_cmp["throughput_uplift_pct"] == 20.0,
        f"got {pinned_cmp}",
    )

    unpinned_cmp = compare_traditional_vs_gds_path(
        payload_gb=10.0,
        pcie_gen_bw_gb_s=32.0,
        host_dram_bw_gb_s=32.0,
        pinned_memory=False,
    )
    check(
        "unpinned_pageable_path_has_4_copies_and_lower_bw",
        unpinned_cmp["traditional_memory_copies"] == 4
        and unpinned_cmp["traditional_cpu_memcpy_calls"] == 2
        and unpinned_cmp["traditional_effective_bw_gb_s"]
        < pinned_cmp["traditional_effective_bw_gb_s"],
        f"got {unpinned_cmp}",
    )

    # 5. Verify Per-GPU (200 MB/s), 8-GPU Node (1.6 GB/s), 72-GPU NVL72 Rack (14.4 GB/s), and Checkpoint Math
    scaling = compute_cluster_storage_scaling(
        per_gpu_mb_s=200.0,
        gpus_per_node=8,
        gpus_per_nvl_rack=72,
        cluster_gpus=1024,
        checkpoint_size_gb=2000.0,
        max_checkpoint_stall_s=60.0,
        single_ost_mb_s=800.0,
    )
    check(
        "node_8gpu_bandwidth_is_1_6_gbs",
        scaling["node_8gpu_read_gb_s"] == 1.6,
        f"got {scaling['node_8gpu_read_gb_s']}",
    )
    check(
        "nvl72_rack_bandwidth_is_14_4_gbs_within_14_to_20_gbs_band",
        scaling["nvl72_rack_read_gb_s"] == 14.4
        and 14.0 <= scaling["nvl72_rack_read_gb_s"] <= 20.0,
        f"got {scaling['nvl72_rack_read_gb_s']}",
    )
    check(
        "cluster_1024gpu_bandwidth_is_204_8_gbs",
        scaling["cluster_read_gb_s"] == 204.8,
        f"got {scaling['cluster_read_gb_s']}",
    )
    check(
        "checkpoint_2tb_in_60s_requires_33_33_gbs_and_42_osts",
        scaling["required_ckpt_write_gb_s"] == 33.33
        and scaling["min_ost_stripes_for_ckpt"] == 42,
        f"got {scaling}",
    )

    # 500 GB checkpoint at 4 OSTs (3.2 GB/s) vs 32 OSTs (25.6 GB/s)
    ckpt_500gb = compute_cluster_storage_scaling(
        per_gpu_mb_s=200.0,
        gpus_per_node=8,
        gpus_per_nvl_rack=72,
        cluster_gpus=256,
        checkpoint_size_gb=500.0,
        max_checkpoint_stall_s=25.0,
        single_ost_mb_s=800.0,
    )
    check(
        "checkpoint_500gb_in_25s_requires_20_gbs_and_25_osts",
        ckpt_500gb["required_ckpt_write_gb_s"] == 20.0
        and ckpt_500gb["min_ost_stripes_for_ckpt"] == 25,
        f"got {ckpt_500gb}",
    )

    # 6. Verify NUMA & PCIe Topology Alignment (PIX/PHB vs SYS cross-socket penalty)
    aligned_topo = evaluate_numa_pcie_locality(
        gpu_numa_node=0,
        nic_or_nvme_numa_node=0,
        dataloader_cpu_numa_node=0,
        pcie_topo_relation="PIX",
        base_bandwidth_gb_s=10.0,
    )
    check(
        "aligned_numa0_pix_retains_100_pct_bandwidth_and_gds",
        aligned_topo["gds_p2p_supported_and_optimal"] is True
        and aligned_topo["cpu_loader_numa_aligned"] is True
        and aligned_topo["dram_access_latency_ns"] == 55.0
        and aligned_topo["throughput_retention_pct"] == 100.0,
        f"got {aligned_topo}",
    )

    misaligned_sys = evaluate_numa_pcie_locality(
        gpu_numa_node=0,
        nic_or_nvme_numa_node=1,
        dataloader_cpu_numa_node=1,
        pcie_topo_relation="SYS",
        base_bandwidth_gb_s=10.0,
    )
    check(
        "cross_socket_sys_and_wrong_numa_degrades_bw_and_disables_optimal_gds",
        misaligned_sys["gds_p2p_supported_and_optimal"] is False
        and misaligned_sys["cpu_loader_numa_aligned"] is False
        and misaligned_sys["dram_access_latency_ns"] == 110.0
        and misaligned_sys["delivered_bandwidth_gb_s"] == 5.76,
        f"got {misaligned_sys}",
    )

    # 7. Verify Page Cache Pollution vs O_DIRECT tradeoffs
    warm_cache = evaluate_page_cache_vs_odirect(
        dataset_working_set_gb=120.0,
        host_free_ram_gb=256.0,
        access_pattern="sequential",
        use_o_direct=False,
    )
    check(
        "working_set_fitting_in_ram_warms_page_cache",
        warm_cache["fits_in_ram"] is True
        and warm_cache["page_cache_thrashing"] is False
        and warm_cache["estimated_cache_hit_rate"] == 0.95,
        f"got {warm_cache}",
    )

    thrash_cache = evaluate_page_cache_vs_odirect(
        dataset_working_set_gb=4000.0,
        host_free_ram_gb=512.0,
        access_pattern="random_epoch_shuffle",
        use_o_direct=False,
    )
    check(
        "multi_tb_shuffled_dataset_thrashes_page_cache_without_odirect",
        thrash_cache["fits_in_ram"] is False
        and thrash_cache["page_cache_thrashing"] is True
        and thrash_cache["estimated_cache_hit_rate"] == 0.04
        and thrash_cache["estimated_cpu_iowait_pct"] == 15.0,
        f"got {thrash_cache}",
    )

    odirect_bypass = evaluate_page_cache_vs_odirect(
        dataset_working_set_gb=4000.0,
        host_free_ram_gb=512.0,
        access_pattern="random_epoch_shuffle",
        use_o_direct=True,
    )
    check(
        "o_direct_eliminates_page_cache_thrashing_on_large_datasets",
        odirect_bypass["page_cache_thrashing"] is False
        and odirect_bypass["estimated_cache_hit_rate"] == 0.0
        and odirect_bypass["estimated_cpu_iowait_pct"] == 2.0,
        f"got {odirect_bypass}",
    )

    total = passed + failed
    print(f"Summary: {passed} passed, {failed} failed (total {total})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
