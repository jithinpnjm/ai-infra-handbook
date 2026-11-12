"""Chapter 13.7 Verification Lab: Checkpoint architecture and recovery.

Run with:
    python3 -B code/part13/checkpoint_architecture_lab.py
"""

from __future__ import annotations

import hashlib
import os
import sys
from typing import Callable, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checkpoint_architecture import (
    REQUIRED_CHECKPOINT_KEYS,
    SUPERPOD_GB300_STORAGE_TIERS,
    CudaCheckpointStateMachine,
    analyze_checkpoint_phases_and_straggler,
    compute_adamw_checkpoint_footprint,
    evaluate_checkpoint_retention_policy,
    evaluate_parallel_ost_restore_rto,
    execute_dcp_1d_reshard,
    plan_dcp_1d_resharding,
    simulate_two_stage_async_checkpoint,
    verify_checkpoint_manifest_and_completeness,
)


def run_checks() -> int:
    checks: List[Tuple[str, Callable[[], bool]]] = []

    def add(desc: str, fn: Callable[[], bool]) -> None:
        checks.append((desc, fn))

    # --- Section 1: Checkpoint State Footprint & Memory Accounting  ---
    add(
        "1. 70B model mixed-precision AdamW footprint is 980.0 GB persistent (14 B/param) vs 1,120.0 GB active training state (16 B/param), or 7.65625 GB vs 8.75 GB per GPU across 128 GPUs",
        lambda: (
            (f70 := compute_adamw_checkpoint_footprint(70.0, num_gpus=128)).persistent_12b_gb == 840.0
            and f70.persistent_14b_gb == 980.0
            and f70.active_training_16b_gb == 1120.0
            and f70.shard_14b_per_gpu_gb == 7.65625
            and f70.shard_16b_per_gpu_gb == 8.75
        ),
    )

    add(
        "2. 400B model mixed-precision AdamW footprint is 5,600.0 GB persistent (14 B/param) and 6,400.0 GB active state (16 B/param), or 2.73438 GB vs 3.125 GB per GPU across 2,048 GPUs",
        lambda: (
            (f400 := compute_adamw_checkpoint_footprint(400.0, num_gpus=2048)).persistent_14b_gb == 5600.0
            and f400.active_training_16b_gb == 6400.0
            and f400.shard_14b_per_gpu_gb == 2.73438
            and f400.shard_16b_per_gpu_gb == 3.125
        ),
    )

    # --- Section 2: Gather-to-Rank-0 vs Sharded Write & Straggler Analysis  ---
    add(
        "3. Checkpoint phase breakdown: 3.1 s serialize + 28.3 s straggler barrier (Rank 7) + 450.2 s slow write (8.25 GB at 18.33 MB/s) = 481.6 s (~8 min) stall",
        lambda: (
            (p := analyze_checkpoint_phases_and_straggler())["total_sync_sec"] == 481.6
            and p["shared_write_mb_s"] == 18.33
            and p["sync_barrier_sec"] == 28.3
        ),
    )

    add(
        "4. Over 1,000 checkpoints, reducing GPU stall from 8 minutes (480 s) to 5 seconds via local NVMe staging cuts lost time from 8,000 min (133.33 h) to 1.3889 h (~1.4 h, 96.0x reduction)",
        lambda: (
            (p := analyze_checkpoint_phases_and_straggler())["sync_stall_minutes_1000"] == 8000.0
            and p["sync_stall_hours_1000"] == 133.33
            and p["async_stall_hours_1000"] == 1.3889
            and p["per_ckpt_stall_reduction_x"] == 96.0
        ),
    )

    # --- Section 3: Young-Daly Optimal Checkpoint Interval & MTBF Scaling  ---
    add(
        "5. Two-stage async checkpointing of 70 GB/node (50 GB/s DtoH, 20 GB/s local NVMe, 2 GB/s remote PFS) cuts GPU pause from 35.0 s to 1.4 s (25.0x speedup)",
        lambda: (
            (sim := simulate_two_stage_async_checkpoint())["stage1_dtoh_pause_sec"] == 1.4
            and sim["stage1_nvme_flush_sec"] == 3.5
            and sim["stage2_pfs_flush_sec"] == 35.0
            and sim["gpu_pause_speedup_vs_sync_x"] == 25.0
            and sim["oom_triggered"] is False
        ),
    )

    add(
        "6. Stacking 5 unflushed 70 GB async checkpoints (350 GB pinned buffer + 180 GB RSS = 530 GB > 512 GB host RAM) triggers Linux OOM killer unless gated on prior flush completion",
        lambda: (
            (sim_oom := simulate_two_stage_async_checkpoint(in_flight_unflushed_snapshots=5))[
                "total_host_mem_used_gb"
            ]
            == 530.0
            and sim_oom["oom_triggered"] is True
        ),
    )

    add(
        "7. Tiered checkpoint retention keeps the last 5 checkpoints plus every 100-epoch milestone while deleting intermediate checkpoints",
        lambda: (
            (
                ret := evaluate_checkpoint_retention_policy(
                    [50, 100, 150, 200, 210, 220, 230, 240, 250],
                    keep_recent=5,
                    milestone_interval=100,
                )
            )["kept_epochs"]
            == [100, 200, 210, 220, 230, 240, 250]
            and ret["deleted_epochs"] == [50, 150]
        ),
    )

    add(
        "8. Restoring a 500 GB checkpoint across 8 Lustre OSTs at 2 GB/s/OST (16 GB/s aggregate) cuts read time from 250.0 s to 31.25 s (8.0x faster; total RTO 46.25 s vs 265.0 s = 4.42 min)",
        lambda: (
            (rto := evaluate_parallel_ost_restore_rto())["per_ost_shard_gb"] == 62.5
            and rto["serial_read_sec"] == 250.0
            and rto["serial_total_rto_sec"] == 265.0
            and rto["serial_total_rto_min"] == 4.42
            and rto["aggregate_parallel_gb_s"] == 16.0
            and rto["parallel_read_sec"] == 31.25
            and rto["parallel_total_rto_sec"] == 46.25
            and rto["read_speedup_x"] == 8.0
        ),
    )

    add(
        "9. DGX SuperPOD GB300 storage tiers specify 90/45 GB/s (1 SU Standard), 280/140 GB/s (1 SU Enhanced), 360/180 GB/s (4 SU Standard), and 1,120/560 GB/s (4 SU Enhanced)",
        lambda: (
            SUPERPOD_GB300_STORAGE_TIERS["1_SU_Standard"] == {"read_gb_s": 90.0, "write_gb_s": 45.0}
            and SUPERPOD_GB300_STORAGE_TIERS["1_SU_Enhanced"] == {"read_gb_s": 280.0, "write_gb_s": 140.0}
            and SUPERPOD_GB300_STORAGE_TIERS["4_SU_Standard"] == {"read_gb_s": 360.0, "write_gb_s": 180.0}
            and SUPERPOD_GB300_STORAGE_TIERS["4_SU_Enhanced"] == {"read_gb_s": 1120.0, "write_gb_s": 560.0}
        ),
    )

    # --- Section 5: PyTorch DCP N -> M Resharding & Atomic Manifest Verification ---
    add(
        "10. PyTorch DCP 1D resharding planner maps a 64-GPU checkpoint to a 48-GPU allocation across 96 copy slices with zero element loss",
        lambda: (
            len(plan64_48 := plan_dcp_1d_resharding(global_num_elements=19200, src_world_size=64, dst_world_size=48))
            == 96
            and sum(s.num_elements for s in plan64_48) == 19200
            and plan64_48[0].dst_rank == 0
            and plan64_48[0].src_rank == 0
            and plan64_48[0].num_elements == 300
            and plan64_48[1].dst_rank == 0
            and plan64_48[1].src_rank == 1
            and plan64_48[1].num_elements == 100
        ),
    )

    add(
        "11. Executing DCP N=64 -> M=48 resharding and M=48 -> N=64 round-trip preserves exact element ordering for all 19,200 parameters",
        lambda: (
            (orig := [[float(r * 300 + i) for i in range(300)] for r in range(64)]) is not None
            and len(resharded_48 := execute_dcp_1d_reshard(orig, 48)) == 48
            and all(len(sh) == 400 for sh in resharded_48)
            and [x for sh in resharded_48 for x in sh] == [x for sh in orig for x in sh]
            and execute_dcp_1d_reshard(resharded_48, 64) == orig
        ),
    )

    add(
        "12. Executing DCP N=4 -> M=8 scale-out resharding splits each 4-GPU shard into two exact 8-GPU sub-shards",
        lambda: (
            len(plan4_8 := plan_dcp_1d_resharding(global_num_elements=800, src_world_size=4, dst_world_size=8)) == 8
            and (orig4 := [[float(r * 200 + i) for i in range(200)] for r in range(4)]) is not None
            and len(resharded_8 := execute_dcp_1d_reshard(orig4, 8)) == 8
            and all(len(sh) == 100 for sh in resharded_8)
            and [x for sh in resharded_8 for x in sh] == [x for sh in orig4 for x in sh]
        ),
    )

    add(
        "13. Atomic manifest validator accepts a complete checkpoint with valid SHA-256 shard hashes and all 6 required deterministic recovery keys",
        lambda: (
            (b0 := b"rank0-shard-bytes") is not None
            and (b1 := b"rank1-shard-bytes") is not None
            and verify_checkpoint_manifest_and_completeness(
                {
                    "completed": True,
                    "included_state_keys": list(REQUIRED_CHECKPOINT_KEYS),
                    "shard_sha256": {
                        "rank0.pt": hashlib.sha256(b0).hexdigest(),
                        "rank1.pt": hashlib.sha256(b1).hexdigest(),
                    },
                },
                {"rank0.pt": b0, "rank1.pt": b1},
            )
            == (True, "VALID")
        ),
    )

    add(
        "14. Atomic manifest validator rejects an incomplete checkpoint (completed=False) caused by a mid-write crash",
        lambda: (
            verify_checkpoint_manifest_and_completeness(
                {
                    "completed": False,
                    "included_state_keys": list(REQUIRED_CHECKPOINT_KEYS),
                    "shard_sha256": {"rank0.pt": hashlib.sha256(b"abc").hexdigest()},
                },
                {"rank0.pt": b"abc"},
            )[0]
            is False
        ),
    )

    add(
        "15. Atomic manifest validator rejects a checkpoint missing optimizer_state_dict or rng_state",
        lambda: (
            verify_checkpoint_manifest_and_completeness(
                {
                    "completed": True,
                    "included_state_keys": ["model_state_dict"],
                    "shard_sha256": {"rank0.pt": hashlib.sha256(b"abc").hexdigest()},
                },
                {"rank0.pt": b"abc"},
            )[0]
            is False
        ),
    )

    add(
        "16. Atomic manifest validator detects truncated or corrupted shard bytes via SHA-256 mismatch",
        lambda: (
            verify_checkpoint_manifest_and_completeness(
                {
                    "completed": True,
                    "included_state_keys": list(REQUIRED_CHECKPOINT_KEYS),
                    "shard_sha256": {"rank0.pt": hashlib.sha256(b"full-valid-shard").hexdigest()},
                },
                {"rank0.pt": b"truncated"},
            )[0]
            is False
        ),
    )

    # --- Section 6: Transparent Driver-Level GPU Checkpointing (`cuda-checkpoint` + CRIU) ---
    add(
        "17. cuda-checkpoint state machine enforces RUNNING -> LOCKED -> CHECKPOINTED -> LOCKED -> RUNNING via the four CUDA Driver API calls",
        lambda: (
            (sm := CudaCheckpointStateMachine(active_hbm_gb=64.0, host_link_gb_s=50.0)).state == "RUNNING"
            and sm.call_driver_api("cuCheckpointProcessLock") == "LOCKED"
            and sm.call_driver_api("cuCheckpointProcessCheckpoint") == "CHECKPOINTED"
            and sm.gpu_resources_allocated is False
            and sm.host_shadow_image_gb == 64.0
            and sm.call_driver_api("cuCheckpointProcessRestore") == "LOCKED"
            and sm.gpu_resources_allocated is True
            and sm.call_driver_api("cuCheckpointProcessUnlock") == "RUNNING"
            and sm.estimate_suspend_or_restore_sec() == 1.28
        ),
    )

    add(
        "18. cuda-checkpoint state machine rejects out-of-order Driver API calls (e.g., calling cuCheckpointProcessCheckpoint before cuCheckpointProcessLock)",
        lambda: _expect_runtime_error(
            lambda: CudaCheckpointStateMachine().call_driver_api("cuCheckpointProcessCheckpoint")
        ),
    )


    passed = 0
    failed = 0
    for desc, fn in checks:
        try:
            ok = bool(fn())
        except Exception as exc:
            print(f"  [FAIL] {desc} (raised {exc!r})")
            failed += 1
            continue
        if ok:
            print(f"  [PASS] {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {desc}")
            failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def _expect_runtime_error(fn: Callable[[], object]) -> bool:
    try:
        fn()
    except RuntimeError:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(run_checks())
