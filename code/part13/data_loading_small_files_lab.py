"""Chapter 13.6 Verification Lab: Data loading, small files and metadata.

Run with:
    python3 -B code/part13/data_loading_small_files_lab.py
"""

from __future__ import annotations

import os
import sys
from typing import Callable, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loading_small_files import (
    MMapIndexedDatasetSimulator,
    analyze_io_wait_and_scaling_efficiency,
    calculate_dataloader_memory_and_shm,
    evaluate_batch_wait_and_cache_decay,
    evaluate_dali_gpu_offload,
    evaluate_dataset_repackaging,
    evaluate_imagenet_small_file_bottleneck,
    evaluate_nemo_curator_indexed_dataset,
    evaluate_png_strace_syscall_breakdown,
    evaluate_sequential_vs_random_io_syscalls,
    evaluate_strace_metadata_saturation,
)


def run_checks() -> int:
    checks: List[Tuple[str, Callable[[], bool]]] = []

    def add(desc: str, fn: Callable[[], bool]) -> None:
        checks.append((desc, fn))

    # --- Section 1: Small-File Metadata Amplification & Strace Diagnostics (V15 Ch. 09, Vol 06 Ch. 03) ---
    add(
        "1. ImageNet 1.2M small-file per-sample cost is 4.0 ms metadata/syscall + 15.0 ms CPU decode/augment = 19.0 ms total",
        lambda: (
            (im := evaluate_imagenet_small_file_bottleneck())["metadata_syscall_ms_per_file"]
            == 4.0
            and im["cpu_preprocess_ms_per_file"] == 15.0
            and im["total_ms_per_file"] == 19.0
        ),
    )

    add(
        "2. ImageNet 1.2M files at batch_size=256 yields 4,688 batches/epoch, 4,864 ms serial batch time, and 608 ms across 8 workers",
        lambda: (
            (im := evaluate_imagenet_small_file_bottleneck())["batches_per_epoch"]
            == 4688
            and im["serial_batch_ms"] == 4864.0
            and im["parallel_batch_ms"] == 608.0
        ),
    )

    add(
        "3. Ideal 256 x 85 KB batch over a 2 GB/s link takes 10.88 ms (~11 ms), leaving 597 ms overhead/batch and ~2,798.74 s (~46.65 min) lost per epoch",
        lambda: (
            (im := evaluate_imagenet_small_file_bottleneck())["ideal_wire_batch_ms"]
            == 10.88
            and im["ideal_wire_batch_ms_rounded"] == 11
            and im["overhead_per_batch_ms"] == 597.0
            and im["epoch_overhead_seconds"] == 2798.74
            and im["epoch_overhead_minutes"] == 46.65
        ),
    )

    add(
        "4. strace with 267,500 openat calls in 2.14 s equals 125,000 opens/sec (8 usecs/call), exceeding the 50K-100K ops/sec MDS ceiling by 2.5x",
        lambda: (
            (st := evaluate_strace_metadata_saturation())["opens_per_sec"] == 125000.0
            and st["avg_usecs_per_call"] == 8.0
            and st["exceeds_mds_min_capacity"] is True
            and st["exceeds_mds_max_capacity"] is True
            and st["overload_ratio_vs_50k"] == 2.5
        ),
    )

    add(
        "5. Vol 06 14M x 20 KB PNG strace spends 85.12% in stat, 10.05% in openat, 4.02% in close, and only 0.81% in read (99.19% metadata)",
        lambda: (
            (png := evaluate_png_strace_syscall_breakdown())["stat_pct"] == 85.12
            and png["openat_pct"] == 10.05
            and png["close_pct"] == 4.02
            and png["read_pct"] == 0.81
            and png["metadata_syscall_pct"] == 99.19
            and png["stat_usecs_per_call"] == 452
            and png["openat_usecs_per_call"] == 106
            and png["close_usecs_per_call"] == 42
            and png["read_usecs_per_call"] == 8
        ),
    )

    add(
        "6. Vol 06 14M x 20 KB PNG workload achieves only 1.25% of a 400 GB/s array (5 GB/s), and 50,000-file 1 GB tar shards cut stat calls by 50,000x to 280 shards",
        lambda: (
            (png := evaluate_png_strace_syscall_breakdown())[
                "array_bandwidth_utilization_pct"
            ]
            == 1.25
            and png["repackaged_shard_count"] == 280
            and png["repackaged_shard_size_gb"] == 1.0
            and png["stat_reduction_factor"] == 50000
        ),
    )

    add(
        "7. Loader batch wait of 600 ms vs 100 ms GPU compute makes the loader 6.0x slower than GPU and leaves the GPU idle 85.71% (~86%) of the step",
        lambda: (
            (bw := evaluate_batch_wait_and_cache_decay())["loader_slowdown_factor"]
            == 6.0
            and bw["gpu_idle_pct"] == 85.71
            and bw["gpu_utilization_pct"] == 14.29
            and bw["stalls_gpu"] is True
            and bw["exceeds_lab04_500ms_threshold"] is True
        ),
    )

    add(
        "8. Cold-cache eviction drops open rate from 2,410 to 820 opens/sec (2.94x) and throughput from 189.1 to 68.7 MB/s (2.75x)",
        lambda: (
            (bw := evaluate_batch_wait_and_cache_decay())[
                "warm_to_cold_open_rate_ratio"
            ]
            == 2.94
            and bw["warm_to_cold_throughput_ratio"] == 2.75
        ),
    )

    # --- Section 2: Dataset Repackaging (.tar, WebDataset, HDF5) & Sequential I/O Math ---
    add(
        "9. Repackaging 1.2M files into 10,000-file tar shards cuts opens by 10,000x (to 120) and batch wait from 600 ms to 50 ms (12.0x speedup, 91.7% Lab 04 improvement)",
        lambda: (
            (rp := evaluate_dataset_repackaging())["tar_shard_opens"] == 120
            and rp["tar_open_reduction_factor"] == 10000.0
            and rp["tar_batch_speedup_x"] == 12.0
            and rp["lab04_wait_improvement_pct"] == 91.7
        ),
    )

    add(
        "10. Repackaging 1.2M files into 1,000-file WebDataset shards cuts opens by 1,000x (to 1,200) and 256-GPU batch stall from 30,000 ms to 20 ms (1,500x speedup)",
        lambda: (
            (rp := evaluate_dataset_repackaging())["wds_shard_opens"] == 1200
            and rp["wds_open_reduction_factor"] == 1000.0
            and rp["cluster_256gpu_speedup_x"] == 1500.0
        ),
    )

    add(
        "11. Lab 04 synthetic 10,000-file dataset repackaged into 100-file tar shards produces 100 shards (100x open reduction)",
        lambda: (
            (
                rp10k := evaluate_dataset_repackaging(
                    num_files=10_000, tar_files_per_shard=100
                )
            )["tar_shard_opens"]
            == 100
            and rp10k["tar_open_reduction_factor"] == 100.0
        ),
    )

    add(
        "12. HDF5 dataset of (1200000, 224, 224, 3) uint8 occupies 180.63 GB with 9.63 MB chunks for (64, 224, 224, 3) and 4.8 MB for int32 labels",
        lambda: (
            (rp := evaluate_dataset_repackaging())["hdf5_uncompressed_gb"] == 180.63
            and rp["hdf5_chunk_mb"] == 9.63
            and rp["hdf5_labels_mb"] == 4.8
        ),
    )

    add(
        "13. Reading 1 GiB in 1 MiB sequential blocks requires 1,024 syscalls vs 262,144 for 4 KB random blocks (256x reduction), and read_ahead_kb 128 KB -> 4,096 KB is 32x",
        lambda: (
            (seq := evaluate_sequential_vs_random_io_syscalls())["random_syscalls"]
            == 262144
            and seq["sequential_syscalls"] == 1024
            and seq["syscall_reduction_factor"] == 256
            and seq["readahead_multiplier"] == 32
        ),
    )

    add(
        "14. mdtest with branch factor -b 10, depth -z 3 (-L leaf-only), and -I 100000 items creates 1,000 leaf directories and 100,000,000 items per iteration",
        lambda: (
            (seq := evaluate_sequential_vs_random_io_syscalls())[
                "mdtest_leaf_directories"
            ]
            == 1000
            and seq["mdtest_total_items_per_iter"] == 100_000_000
        ),
    )

    # --- Section 3: PyTorch DataLoader Queue Sizing, /dev/shm & I/O Wait Isolation (AISPE Ch. 5) ---
    add(
        "15. PyTorch DataLoader with batch_size=32, shape=(3,224,224) float32 uses 602,112 B/sample and 19,267,584 B (18.375 MiB) per batch",
        lambda: (
            (dl := calculate_dataloader_memory_and_shm())["bytes_per_sample"] == 602112
            and dl["bytes_per_batch"] == 19267584
            and dl["mib_per_batch"] == 18.375
        ),
    )

    add(
        "16. DataLoader with num_workers=8 and prefetch_factor=4 queues 32 batches (588.0 MiB/rank, 4,704.0 MiB = 4.59375 GiB across 8 GPUs), overflowing default 64 MiB /dev/shm",
        lambda: (
            (dl := calculate_dataloader_memory_and_shm())["queued_batches_per_rank"]
            == 32
            and dl["inflight_mib_per_rank"] == 588.0
            and dl["node_inflight_mib"] == 4704.0
            and dl["node_inflight_gib"] == 4.59375
            and dl["fits_in_default_64mib_docker_shm"] is False
            and dl["fits_in_k8s_shm"] is True
        ),
    )

    add(
        "17. Default PyTorch prefetch_factor=2 with num_workers=8 queues 16 batches (294.0 MiB/rank, 2,352.0 MiB across 8 GPUs)",
        lambda: (
            (dl2 := calculate_dataloader_memory_and_shm(prefetch_factor=2))[
                "queued_batches_per_rank"
            ]
            == 16
            and dl2["inflight_mib_per_rank"] == 294.0
            and dl2["node_inflight_mib"] == 2352.0
        ),
    )

    add(
        "18. Reducing GPU I/O wait from 30% to 5% cuts I/O stall time by 6.0x (recovering 25 pct pts of GPU time and yielding a 6.0x step-rate gain when I/O-bound)",
        lambda: (
            (io := analyze_io_wait_and_scaling_efficiency())["io_wait_reduction_factor"]
            == 6.0
            and io["io_bound_step_rate_speedup_x"] == 6.0
            and io["recovered_compute_pct_pts"] == 25.0
        ),
    )

    add(
        "19. 8 GPUs achieving only a 5.0x throughput speedup operate at 62.5% scaling efficiency",
        lambda: (
            analyze_io_wait_and_scaling_efficiency()["scaling_efficiency_pct"] == 62.5
        ),
    )

    add(
        "20. At 200 MB/s per GPU, 8 GPUs need 1.6 GB/s, a 72-GPU GB200/GB300 NVL72 rack needs 14.4 GB/s, and a 100 TB dataset presplit across 10 nodes uses 10 TB/node",
        lambda: (
            (io := analyze_io_wait_and_scaling_efficiency())["node_8gpu_gb_s"] == 1.6
            and io["nvl72_gb_s"] == 14.4
            and io["local_shard_tb_per_node"] == 10.0
        ),
    )

    # --- Section 4: Multimodal GPU Preprocessing with NVIDIA DALI (AISPE Ch. 5) ---
    add(
        "21. NVIDIA DALI drops host CPU utilization from 800% (8 cores) to 200% (2 cores), a 4.0x reduction (75.0% CPU savings)",
        lambda: (
            (dali := evaluate_dali_gpu_offload())["cpu_cores_before"] == 8.0
            and dali["cpu_cores_after"] == 2.0
            and dali["cpu_reduction_factor"] == 4.0
            and dali["cpu_savings_pct"] == 75.0
        ),
    )

    add(
        "22. Fused GPU DALI pipeline (8.0 ms) outperforms CPU-only (92.0 ms, 11.5x) and avoids the D2H/H2D ping-pong DALI anti-pattern (67.5 ms, 8.44x)",
        lambda: (
            (dali := evaluate_dali_gpu_offload())["cpu_only_batch_ms"] == 92.0
            and dali["ping_pong_dali_batch_ms"] == 67.5
            and dali["fused_gpu_dali_batch_ms"] == 8.0
            and dali["fused_vs_cpu_speedup_x"] == 11.5
            and dali["fused_vs_ping_pong_speedup_x"] == 8.44
        ),
    )

    add(
        "23. Grace Blackwell NVLink-C2C provides 900 GB/s bidirectional bandwidth and hardware Decompression Engine supports LZ4, Snappy, and Deflate",
        lambda: (
            (dali := evaluate_dali_gpu_offload())["nvlink_c2c_bidirectional_gb_s"]
            == 900.0
            and dali["blackwell_hw_decompression_formats"]
            == ("LZ4", "Snappy", "Deflate")
        ),
    )

    # --- Section 5: NeMo Curator .bin + .idx Memory-Mapped Indexed Dataset (AISPE Ch. 5) ---
    add(
        "24. NeMo Curator .bin + .idx simulator performs exact O(1) byte-offset lookup for document 2 (offset 22 bytes, length 8 uint16 tokens, 38 bytes total)",
        lambda: (
            (nc := evaluate_nemo_curator_indexed_dataset())["sample_bin_bytes"] == 38
            and nc["sample_doc2_offset_bytes"] == 22
            and nc["sample_doc2_token_len"] == 8
            and nc["sample_doc2_matches"] is True
        ),
    )

    add(
        "25. 1B uint16 tokens across 500,000 documents produce a 2.0 GB .bin file and a 6.0 MB .idx file (0.3% index overhead)",
        lambda: (
            (nc := evaluate_nemo_curator_indexed_dataset())["bin_size_gb"] == 2.0
            and nc["idx_size_mb"] == 6.0
            and nc["idx_overhead_pct"] == 0.3
            and nc["single_copy_gb"] == 2.006
        ),
    )

    add(
        "26. Storing 4 offline pre-shuffled epoch copies of a 2.006 GB .bin+.idx dataset requires 8.024 GB on disk to eliminate runtime shuffle overhead",
        lambda: (
            (nc := evaluate_nemo_curator_indexed_dataset())["preshuffled_epoch_copies"]
            == 4
            and nc["preshuffled_total_gb"] == 8.024
        ),
    )

    passed = 0
    for desc, fn in checks:
        try:
            ok = bool(fn())
        except Exception as exc:
            print(f"[FAIL] {desc} (raised {exc!r})")
            continue
        if ok:
            print(f"[PASS] {desc}")
            passed += 1
        else:
            print(f"[FAIL] {desc}")

    failed = len(checks) - passed
    print(f"\nSummary: {passed} passed, {failed} failed (out of {len(checks)} checks)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_checks())
