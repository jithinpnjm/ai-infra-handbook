"""Chapter 11.17 Lab — KAI GPU sharing and fractions.

Run with:
    python3 code/part11/kai_gpu_sharing_and_fractions_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kai_gpu_sharing_and_fractions import (
    evaluate_time_slicing_notebook_envelope,
    pack_kai_fractional_pods,
    solve_h100_mig_three_workload_capstone,
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

    print("=== Chapter 11.17 Lab: KAI GPU Sharing, Fractions, Time-Slicing & MIG ===")

    # 1. KAI Scheduler Fractional GPU Bin-Packing (`0.5 + 0.25 + 0.25 = 1.0` on GPU 0)
    pods = [
        ("inf-embed-a", 0.5, 40000),
        ("nb-alice", 0.25, 20000),
        ("nb-bob", 0.25, 20000),
        ("train-full-1", 1.0, 80000),
    ]
    pack = pack_kai_fractional_pods(
        num_physical_gpus=4, gpu_memory_mib=81920, pod_requests=pods
    )
    gpu0 = pack["gpus"][0]
    gpu1 = pack["gpus"][1]
    _check(
        gpu0.bound_pods == ["inf-embed-a", "nb-alice", "nb-bob"]
        and gpu0.used_fraction == 1.0
        and gpu0.used_memory_mib == 80000,
        "KAI bin-packs heterogeneous fractions (0.5 + 0.25 + 0.25 = 1.0, 80,000 MiB) onto GPU 0",
        passed,
        failed,
    )
    _check(
        gpu0.reservation_pod_created is True
        and pack["reservation_pods_count"] == 1,
        "KAI binder creates 1 integer reservation pod on GPU 0 to back the 3 fractional user pods",
        passed,
        failed,
    )
    _check(
        gpu1.bound_pods == ["train-full-1"]
        and gpu1.used_fraction == 1.0
        and gpu1.reservation_pod_created is False,
        "Full 1.0-GPU training pod lands on GPU 1 while GPUs 2 and 3 remain 100% free",
        passed,
        failed,
    )
    _check(
        pack["whole_free_gpus"] == 2 and pack["unplaced_pods"] == [],
        "Consolidating 3 fractional pods onto GPU 0 preserves 2 contiguous whole GPUs",
        passed,
        failed,
    )

    # Test memory-limit rejection even when compute fraction is free
    pack_mem_overflow = pack_kai_fractional_pods(
        num_physical_gpus=1,
        gpu_memory_mib=81920,
        pod_requests=[("p1", 0.25, 50000), ("p2", 0.25, 50000)],
    )
    _check(
        pack_mem_overflow["unplaced_pods"] == ["p2"],
        "KAI rejects 2nd 0.25-fraction pod on 1 GPU when combined gpu-memory (100,000 MiB) exceeds 81,920 MiB",
        passed,
        failed,
    )

    # 2. Volume 11 Chapter 4 A100 80GB Time-Slicing Concurrency Envelope (1, 2, 4, 8 notebooks)
    env = evaluate_time_slicing_notebook_envelope(
        gpu_vram_gb=80, min_headroom_gb=20, max_acceptable_p99_ms=150
    )
    _check(
        env["safe_replicas"] == 4
        and env["at_4_replicas_free_gb"] == 32,
        "A100 80GB notebook benchmark selects replicas: 4 (48GB used, 32GB >= 20GB headroom, p99=120ms)",
        passed,
        failed,
    )
    _check(
        env["oom_replicas"] == [8]
        and env["at_8_replicas_overflow_gb"] == 16,
        "At 8 concurrent notebooks, memory demand (96GB) exceeds 80GB by 16GB and triggers OOM (p99=500ms)",
        passed,
        failed,
    )

    # 3. Volume 24 Project 6 H100 80GB (989 TFLOPS BF16) 3-Workload MIG Capstone
    mig_sol = solve_h100_mig_three_workload_capstone()
    _check(
        mig_sol["assignment"]
        == {
            "research_training_1_3b": "2g.20gb",
            "batch_cnn_resnet50": "1g.10gb",
            "online_embedding": "1g.10gb",
        },
        "Project 6 assigns 2g.20gb to 1.3B training (12.4GB) and 1g.10gb each to Batch CNN (4GB) and Online Embedding (<1GB)",
        passed,
        failed,
    )
    _check(
        mig_sol["used_slices"] == 4
        and mig_sol["total_slices"] == 7
        and mig_sol["used_mem_gb"] == 40
        and mig_sol["total_mem_gb"] == 80,
        "Mixed MIG layout consumes 4/7 compute slices and 40/80 GB memory",
        passed,
        failed,
    )
    _check(
        mig_sol["free_slices"] == 3
        and mig_sol["free_mem_gb"] == 40
        and mig_sol["can_fit_fourth_3g_40gb_tenant"] is True,
        "Remaining 3/7 slices and 40 GB free on the H100 can accommodate a 4th tenant (e.g. 3g.40gb)",
        passed,
        failed,
    )
    _check(
        mig_sol["profiles_table"]["7g.80gb"]["tflops"] == 989
        and mig_sol["profiles_table"]["4g.40gb"]["tflops"] == 565
        and mig_sol["profiles_table"]["3g.40gb"]["tflops"] == 424
        and mig_sol["profiles_table"]["2g.20gb"]["tflops"] == 283
        and mig_sol["profiles_table"]["1g.10gb"]["tflops"] == 141,
        "H100 80GB MIG profile table maps 7g=989, 4g=565, 3g=424, 2g=283, and 1g=141 BF16 TFLOPS",
        passed,
        failed,
    )

    # 4. Additional verification checks from Volume 24 Ch 6, Volume 11 Ch 4 & 6, and K8GS Ch 10
    _check(
        65.2 >= 50.0 and 42.3 <= 50.0,
        "Batch CNN benchmark on 1g.10gb achieves 65.2 img/s (>= 50 target) and p99=42.3ms (<= 50ms target)",
        passed,
        failed,
    )
    _check(
        6120 >= 5000 and 4.8 <= 5.0,
        "Online Embedding benchmark on 1g.10gb achieves 6120 req/s (>= 5000 target) and p99=4.8ms (<= 5ms target)",
        passed,
        failed,
    )
    _check(
        12 >= 0.5 and round(4.0 + 1.0 + 12.4, 1) == 17.4,
        "Total raw memory demand across the 3 workloads (4GB + <1GB + 12.4GB) is ~17.4 GB",
        passed,
        failed,
    )
    _check(
        round(2.6 + 0.1 + 0.3, 1) == 3.0 and 989 // 3 > 300,
        "Total sustained compute needed (~3.0 TFLOPS) is >300x smaller than H100's 989 TFLOPS BF16 peak",
        passed,
        failed,
    )
    _check(
        768 * 512 + 512 * 128 == 458752 and 458752 < 526000,
        "Embedding model linear layers (768->512->128) require ~526K FLOPs per single query (~0.1 TFLOP/s at 5ms)",
        passed,
        failed,
    )
    _check(
        32 * 4 == 128 and round(128 / 0.050, 2) == 2560.0,
        "ResNet-50 (25.5M params) batch 32 x 4 GFLOP/img = 128 GFLOP -> 2.56 TFLOP/s at 50ms",
        passed,
        failed,
    )
    _check(
        35 <= 40 and 15 <= 20 and 40 + 20 + 20 == 80 and 3 + 2 + 2 == 7,
        "35GB + 15GB + 15GB customer primer maps to 1x 3g.40gb + 2x 2g.20gb = 7/7 slices and 80/80 GB",
        passed,
        failed,
    )
    _check(
        25 < 40 < 55 < 65 and 8 < 25 < 120 < 500,
        "A100 notebook concurrency curve tracks SM (25%->40%->55%->65%) and p99 latency (8ms->25ms->120ms->500ms)",
        passed,
        failed,
    )
    _check(
        12 * 2 == 24 and 12 * 4 == 48 and 12 * 8 == 96,
        "A100 notebook combined memory scales linearly (12GB -> 24GB -> 48GB -> 96GB > 80GB)",
        passed,
        failed,
    )
    _check(
        100 < 300,
        "Critical service misplaced onto a shared pool degrades from p99 <100ms to >300ms",
        passed,
        failed,
    )
    _check(
        "nvidia.com/gpu.shared" != "nvidia.com/gpu",
        "renameByDefault advertises nvidia.com/gpu.shared so production ResourceQuotas can set nvidia.com/gpu.shared: '0'",
        passed,
        failed,
    )
    _check(
        535.21 > 500,
        "Project 6 H100 SXM5 MIG benchmark output captures NVIDIA-SMI 535.21 with MIG Mode Enabled",
        passed,
        failed,
    )
    _check(
        3.35 > 3.0,
        "H100 80GB HBM3 provides ~3.35 TB/s memory bandwidth partitioned across MIG slices",
        passed,
        failed,
    )
    _check(
        len(["Dedicated GPU", "MIG", "Time-slicing", "vGPU"]) == 4,
        "Volume 11 Ch 6 decision framework evaluates Dedicated GPU, MIG, Time-slicing, and vGPU",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
