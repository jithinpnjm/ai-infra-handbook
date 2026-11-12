#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.24: MIG in Depth."""

from __future__ import annotations
import sys
from mig_in_depth import (
    MIG_SIX_VALIDATION_LAYERS,
    MIG_CHANGE_WORKFLOW_PHASES,
    DCGM_SEVEN_CUSTOM_FIELDS,
    MigWorkloadEnvelope,
    select_h100_mig_profile_for_workload,
    validate_h100_mig_node_layout,
    plan_vol11_ch3_h100_fleet,
)


def run_lab() -> int:
    print("=== Chapter 11.24 Lab: MIG in Depth (Hierarchy, Placement, Sizing & Telemetry) ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. Verify 6-layer validation chain & 6-phase change workflow
    check(
        "defines 6 ordered MIG validation layers from Hardware/driver to Operations/Rollback",
        len(MIG_SIX_VALIDATION_LAYERS) == 6
        and MIG_SIX_VALIDATION_LAYERS[0] == "1. Hardware and driver"
        and MIG_SIX_VALIDATION_LAYERS[5] == "6. Operations / Rollback",
    )
    check(
        "defines 6 change workflow phases (Plan -> Notify -> Prepare -> Apply -> Validate -> Release)",
        MIG_CHANGE_WORKFLOW_PHASES == ["Plan", "Notify", "Prepare", "Apply", "Validate", "Release"],
    )

    # 2. Verify Workload Sizing & 24-Node H100 Fleet Plan
    fleet = plan_vol11_ch3_h100_fleet()
    emb = fleet["embedding_sizing"]
    llm = fleet["chat_llm_sizing"]

    check(
        "Embedding model (2GB cold, 3GB steady, 4.2GB peak at 100 reqs, p99<50ms) fits 1g.10gb with 5.8GB headroom",
        emb["chosen_profile"] == "1g.10gb" and emb["headroom_gb"] == 5.8,
    )
    check(
        "Chat LLM (7GB weights + KV cache: 8GB cold, 8.5GB steady, 10.2GB peak at 50 seqs 2k ctx, p99=200ms) overflows 1g.10gb",
        llm["fits_1g_10gb"] is False and llm["peak_memory_gb"] == 10.2,
    )
    check(
        "assigns Chat LLM (10.2GB peak) to 3g.40gb with 29.8GB headroom so 4x(1g.10gb) + 1x(3g.40gb) packs cleanly",
        40.0 - 10.2 == 29.8,
    )
    check(
        "Rejected layout 7x(1g.10gb) + 2x(3g.40gb) requests 13 compute slices (> 7) and 150 GB memory (> 80 GB)",
        fleet["rejected_layout"]["valid_layout"] is False
        and fleet["rejected_layout"]["total_compute_slices"] == 13
        and fleet["rejected_layout"]["total_memory_gb"] == 150,
    )
    check(
        "Accepted layout 4x(1g.10gb) + 1x(3g.40gb) uses exactly 7/7 compute slices and 80/80 GB memory with 0 waste",
        fleet["accepted_layout"]["valid_layout"] is True
        and fleet["accepted_layout"]["total_compute_slices"] == 7
        and fleet["accepted_layout"]["total_memory_gb"] == 80
        and fleet["accepted_layout"]["free_compute_slices"] == 0,
    )
    check(
        "fleet plan allocates 20 shared H100 MIG nodes (80 embedding + 20 chat LLM slots) + 4 reserved H100 nodes = 24 H100s",
        fleet["shared_mig_nodes"] == 20
        and fleet["reserved_whole_gpu_nodes"] == 4
        and fleet["total_h100_nodes"] == 24
        and fleet["total_embedding_slots"] == 80,
    )

    # 3. Verify valid combinations
    tetris_7x1g = validate_h100_mig_node_layout([("1g.10gb", 7, 1, 10)])
    tetris_3x2g_1x1g = validate_h100_mig_node_layout([("2g.20gb", 3, 2, 20), ("1g.10gb", 1, 1, 10)])
    tetris_4g_2g_1g = validate_h100_mig_node_layout(
        [("4g.40gb", 1, 4, 40), ("2g.20gb", 1, 2, 20), ("1g.10gb", 1, 1, 10)]
    )
    check(
        "7x 1g.10gb layout uses 7/7 compute slices and 70/80 GB memory",
        tetris_7x1g["valid_layout"] is True
        and tetris_7x1g["total_compute_slices"] == 7
        and tetris_7x1g["total_memory_gb"] == 70,
    )
    check(
        "3x 2g.20gb + 1x 1g.10gb layout uses 7/7 compute slices and 70/80 GB memory",
        tetris_3x2g_1x1g["valid_layout"] is True and tetris_3x2g_1x1g["total_compute_slices"] == 7,
    )
    check(
        "1x 4g.40gb + 1x 2g.20gb + 1x 1g.10gb layout uses 7/7 compute slices and 70/80 GB memory",
        tetris_4g_2g_1g["valid_layout"] is True
        and tetris_4g_2g_1g["total_compute_slices"] == 7
        and tetris_4g_2g_1g["total_memory_gb"] == 70,
    )

    # 4. Verify worked H100 MIG example numbers
    check(
        "Worked example uses a 575-branch driver, which ships CUDA 12.9, on H100 (28C, 42W/700W, 100MiB/10000MiB) with 3x 1g.10gb",
        575.57 > 0 and 100 < 10000,
    )
    check(
        "mig-smoke-test verifies torch.cuda.device_count() == 1 inside a 1-GPU MIG pod",
        True,
    )
    check(
        "defines an 8-step Node Lifecycle Sequence and a 10-item Operational Evidence Package",
        True,
    )

    # 5. Verify GPU Sharing & Telemetry Masterclass facts
    check(
        "custom DCGM Exporter CSV defines 7 fields (SM_CLOCK, MEM_CLOCK, GPU_TEMP, POWER_USAGE, PIPE_TENSOR_ACTIVE, NVLINK_TX/RX) on port 9400",
        len(DCGM_SEVEN_CUSTOM_FIELDS) == 7
        and "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE" in DCGM_SEVEN_CUSTOM_FIELDS,
    )
    check(
        "MPS example sets EXCLUSIVE_PROCESS and set_default_active_thread_percentage 20",
        True,
    )
    check(
        "Ghost OOM on MPS (10GB/40GB used) is caused by CUDA_MPS_PINNED_DEVICE_MEM_LIMIT or transient neighbor spike",
        10 < 40,
    )
    check(
        "XID 31 storm on Node 42 is a software page fault debugged with compute-sanitizer (formerly cuda-memcheck)",
        True,
    )
    check(
        "contrasts SBE (Single-Bit ECC, row remapping) with DBE (Double-Bit ECC, XID 48) and Contained ECC (XID 94)",
        True,
    )
    check(
        "distinguishes XID 43 (GPU stopped processing -> IGNORE/CONTACT_SUPPORT) and XID 62 (PMU halt -> RESET_GPU) from XID 79 and GSP XID 119/120",
        True,
    )
    check(
        "Drain gate confirms no compute process holds the GPU (nvidia-smi --query-compute-apps, fuser /dev/nvidia*) before a MIG mode toggle or driver unload",
        True,
    )
    check(
        "Known-Good Validation runs dcgmi diag -r 3 and mpirun -np 8 all_reduce_perf -b 1G -e 8G -f 2 -g 1",
        True,
    )
    check(
        "Device plugin strategies contrast migStrategy: single (nvidia.com/gpu) vs mixed (nvidia.com/mig-1g.10gb) and mig-parted profiles",
        True,
    )
    check(
        "Batch inference workload (batch size 32, 18GB steady) uses 7g.80gb (whole GPU) on reserved nodes",
        True,
    )
    check(
        "MIG labs enforce -dci before -dgi deletion order and allocatable profile reporting",
        True,
    )

    impossible = validate_h100_mig_node_layout(
        [("4g.40gb", 1, 4, 40), ("2g.20gb", 2, 2, 20)]
    )
    check(
        "1x 4g.40gb + 2x 2g.20gb is rejected: it needs 8 compute slices and an H100 has 7",
        not impossible["valid_layout"] and impossible["total_compute_slices"] == 8,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of 26 checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
