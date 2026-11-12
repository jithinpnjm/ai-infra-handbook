#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.11: checkpointing, fault tolerance and elastic training."""

from __future__ import annotations
import sys
from checkpoint_fault_tolerance import (
    CheckpointWriteScenario,
    evaluate_checkpoint_write_strategies,
    compute_fleet_reliability_and_young_daly,
    evaluate_async_checkpoint_and_host_ram,
    simulate_resume,
    evaluate_elastic_training_and_watchdogs,
)


def run_lab() -> int:
    print("=== Chapter 14.11 Lab: Checkpointing, Fault Tolerance, and Elastic Training Verification ===")
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

    # 1. Checkpoint size and write strategies
    ckpt = evaluate_checkpoint_write_strategies(CheckpointWriteScenario())
    check(
        "1. 70B model at 14 bytes/param (weights and optimizer state, no gradients) is 980.0 GB, 7.65625 GB per GPU on 128 GPUs",
        ckpt["total_payload_gb"] == 980.0 and ckpt["per_gpu_shard_gb"] == 7.65625,
    )
    check(
        "2. Gather-to-rank-0 takes 39.2 s to gather at 25 GB/s plus 196.0 s to write at 5 GB/s = 235.2 s",
        ckpt["gather_network_s"] == 39.2 and ckpt["single_node_write_s"] == 196.0 and ckpt["naive_total_s"] == 235.2,
    )
    check(
        "3. Ideal per-GPU shard write at 5 GB/s is 1.53 s, but 128 writers demand 640.0 GB/s and the 400 GB/s filesystem ceiling gives 3.125 GB/s each",
        ckpt["ideal_parallel_write_s"] == 1.53
        and ckpt["aggregate_demand_gbps"] == 640.0
        and ckpt["effective_per_gpu_gbps"] == 3.125,
    )
    check(
        "4. Every rank writing its own shard finishes in 2.45 s, 96.0 times faster than gathering",
        ckpt["realistic_parallel_write_s"] == 2.45 and ckpt["speedup_vs_naive"] == 96.0,
    )

    # 2. Failure arithmetic and Young-Daly
    yd_1024 = compute_fleet_reliability_and_young_daly(mtbf_s=28800.0, tc_s=180.0)
    check(
        "5. Young-Daly with M = 28,800 s and Tc = 180 s gives sqrt(10,368,000) - 180 = 3,220 - 180 = 3,040 s (50.7 min)",
        yd_1024["radicand"] == 10368000.0
        and yd_1024["sqrt_term_rounded"] == 3220
        and yd_1024["t_opt_rounded_s"] == 3040.0
        and yd_1024["t_opt_minutes"] == 50.7,
    )
    yd_2048 = compute_fleet_reliability_and_young_daly(mtbf_s=21600.0, tc_s=240.0)
    check(
        "6. Young-Daly with M = 21,600 s and Tc = 240 s gives 3,220 - 240 = 2,980 s (49.7 min)",
        yd_2048["radicand"] == 10368000.0 and yd_2048["t_opt_rounded_s"] == 2980.0 and yd_2048["t_opt_minutes"] == 49.7,
    )
    check(
        "7. At 99.9% daily reliability per GPU, 100,000 GPUs all survive 24 h with probability 3.5e-44 and fail 100 times a day (14.4 min MTBF); 1,024 GPUs over 30 days almost surely fail",
        yd_1024["survival_mantissa"] == 3.5
        and yd_1024["survival_exponent"] == -44
        and yd_1024["expected_daily_failures"] == 100.0
        and yd_1024["fleet_mtbf_minutes"] == 14.4
        and yd_1024["prob_failure_1024_30d_pct"] > 99.9999,
    )
    check(
        "8. A 5 min pause per hour wastes 8.33%; goodput is 89.13% at the Young-Daly interval, 61.98% at 5 min and 73.77% at 4 h",
        yd_1024["pause_5min_per_hour_pct"] == 8.33
        and yd_1024["goodput_opt_pct"] == 89.13
        and yd_1024["goodput_5min_pct"] == 61.98
        and yd_1024["goodput_4hr_pct"] == 73.77,
    )
    check(
        "9. A 2 s device-to-host pause instead of a 180 s blocking write lifts goodput at the same interval to 94.66%",
        yd_1024["goodput_async_opt_pct"] == 94.66,
    )

    # 3. Asynchronous checkpointing and host RAM
    async_ok = evaluate_async_checkpoint_and_host_ram(in_flight_buffers=1)
    check(
        "10. A 100 GB node shard reaches pinned host RAM in 1.82 s and flushes in 20.0 s in the background, a 12.0x shorter pause than writing synchronously",
        async_ok["dtoh_pause_s"] == 1.82
        and async_ok["background_flush_s"] == 20.0
        and async_ok["pause_reduction_factor"] == 12.0,
    )
    check(
        "11. One in-flight 100 GB buffer fits in 132 GB of free host RAM",
        async_ok["available_ram_gb"] == 132.0 and async_ok["oom_killed"] is False,
    )
    async_oom = evaluate_async_checkpoint_and_host_ram(in_flight_buffers=2)
    check(
        "12. Two overlapping 100 GB buffers need 200 GB against 132 GB free and trigger the Linux OOM killer",
        async_oom["required_staging_ram_gb"] == 200.0
        and async_oom["oom_killed"] is True
        and async_oom["dmesg_signature"] == "[Node 3] dmesg: Out of memory: Killed process 1234 (python)",
    )

    # 4. Resume completeness and resharding
    reshard_fail = simulate_resume(old_world_size=64, new_world_size=48, checkpoint_format="naive_per_rank")
    check(
        "13. A per-rank checkpoint written by 64 ranks fails on 48 ranks with a shard-count mismatch",
        reshard_fail["reshard_success"] is False
        and reshard_fail["error_message"]
        == "RuntimeError: Number of shards in checkpoint (64) does not match world size (48)",
    )
    reshard_dcp = simulate_resume(old_world_size=64, new_world_size=48, checkpoint_format="dcp")
    check(
        "14. A metadata-driven checkpoint reshards 980 GB from 64 shards of 15.3125 GB to 48 shards of 20.4167 GB and the resume is complete",
        reshard_dcp["reshard_success"] is True
        and reshard_dcp["old_shard_gb"] == 15.3125
        and reshard_dcp["new_shard_gb"] == 20.4167
        and reshard_dcp["deterministic_match"] is True,
    )
    no_optim = simulate_resume(
        saved_components=["model_state_dict", "scheduler_state_dict", "dataloader_state", "rng_state_every_rank"]
    )
    check(
        "15. Without optimizer state the Adam moments restart from zero and the loss spikes on resume",
        no_optim["loss_spike_on_resume"] is True and no_optim["deterministic_match"] is False,
    )
    rank0_only_rng = simulate_resume(
        saved_components=["model_state_dict", "optimizer_state_dict", "scheduler_state_dict", "dataloader_state"]
    )
    check(
        "16. Saving RNG state for rank 0 only leaves every other rank with different dropout and shuffling and no error is raised",
        rank0_only_rng["silent_rng_divergence"] is True
        and rank0_only_rng["reshard_success"] is True
        and rank0_only_rng["deterministic_match"] is False,
    )
    no_loader = simulate_resume(
        saved_components=["model_state_dict", "optimizer_state_dict", "scheduler_state_dict", "rng_state_every_rank"]
    )
    check(
        "17. Without data loader state the resumed job replays or skips samples",
        no_loader["data_replayed_or_skipped"] is True and no_loader["deterministic_match"] is False,
    )

    # 5. Elastic training and failure detection
    elastic = evaluate_elastic_training_and_watchdogs()
    check(
        "18. torchrun --nnodes=2:4 with 8 GPUs per node spans 16 to 32 GPUs and continues on 3 surviving nodes (24 GPUs)",
        elastic["nnodes_spec"] == "2:4"
        and elastic["min_world_size"] == 16
        and elastic["max_world_size"] == 32
        and elastic["active_world_size"] == 24
        and elastic["within_elastic_bounds"] is True
        and elastic["valid_rdzv"] is True,
    )
    check(
        "19. At 24 GPUs with micro-batch 2, 4 accumulation steps keep the global batch at 192; square-root scaling takes 1e-4 at batch 32 to 1.6e-3 at batch 8,192",
        elastic["grad_accum_steps"] == 4
        and elastic["preserved_global_batch"] is True
        and elastic["scaled_global_batch"] == 8192
        and elastic["sqrt_factor"] == 16.0
        and elastic["scaled_lr"] == 0.0016,
    )
    check(
        "20. A crash at step 5,243 with a 500-step interval loads step 5,000, resumes at 5,001 and loses 243 steps",
        elastic["last_saved_step"] == 5000 and elastic["resume_step"] == 5001 and elastic["lost_steps"] == 243,
    )
    check(
        "21. A heartbeat detector (2.0 s interval, 4 missed) notices a dead rank in 8.0 s, 75.0 times faster than the 600 s default NCCL timeout",
        elastic["heartbeat_detect_s"] == 8.0
        and elastic["nccl_default_timeout_s"] == 600.0
        and elastic["detection_speedup"] == 75.0,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
