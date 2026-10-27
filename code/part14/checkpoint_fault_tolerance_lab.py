#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.11: Checkpointing, Fault Tolerance, and Elastic Training."""

from __future__ import annotations
import sys
from checkpoint_fault_tolerance import (
    CheckpointWriteScenario,
    evaluate_checkpoint_write_strategies,
    compute_fleet_reliability_and_young_daly,
    evaluate_async_checkpoint_and_host_ram,
    simulate_dcp_resharding_and_recovery,
    evaluate_elastic_training_and_watchdogs,
    evaluate_volume13_cluster_baselines,
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

    # 1. Checkpoint Sizing & Gather-to-Rank-0 vs Distributed Sharded Writes (V13 Ch. 9)
    ckpt = evaluate_checkpoint_write_strategies(CheckpointWriteScenario())
    check(
        "1. 70B model at 16 bytes/param (4B weights + 4B grads + 8B Adam) equals 1,120.0 GB (~1.09 TB) total and 8.75 GB/GPU across 128 H100 GPUs",
        ckpt["total_payload_gb"] == 1120.0 and ckpt["per_gpu_shard_gb"] == 8.75,
    )

    check(
        "2. Naive gather-to-rank-0 takes 44.8 s (~45 s) network gather at 25 GB/s + 224.0 s disk write at 5 GB/s = 268.8 s (~269 s / 4.5 min)",
        ckpt["gather_network_s"] == 44.8
        and ckpt["single_node_write_s"] == 224.0
        and ckpt["naive_total_s"] == 268.8,
    )

    check(
        "3. Ideal per-GPU sharded write at 5 GB/s takes 1.75 s, while 128 GPUs x 5 GB/s = 640.0 GB/s demand caps at 400 GB/s Lustre ceiling (3.125 GB/s/GPU)",
        ckpt["ideal_parallel_write_s"] == 1.75
        and ckpt["aggregate_demand_gbps"] == 640.0
        and ckpt["effective_per_gpu_gbps"] == 3.125,
    )

    check(
        "4. Realistic parallel sharded write completes in 2.8 s (8.75 GB / 3.125 GB/s), achieving a 96.0x (~2 orders of magnitude) speedup over 268.8 s gather",
        ckpt["realistic_parallel_write_s"] == 2.8 and ckpt["speedup_vs_naive"] == 96.0,
    )

    check(
        "5. Omitting 2 B/param BF16 gradients (14 bytes/param) yields 980.0 GB total (~15.3125 GB/GPU on 64 GPUs, 122.5 GB/node), writing in 10.0 s to local NVMe vs 98.0 s to 10 GB/s NAS",
        ckpt["v21_total_gb"] == 980.0
        and ckpt["v21_per_gpu_64_gb"] == 15.3125
        and ckpt["v21_per_node_8gpu_gb"] == 122.5
        and ckpt["v21_nvme_write_s"] == 10.0
        and ckpt["v21_nas_write_s"] == 98.0,
    )

    check(
        "6. Megatron-LM 8.03B model requires 16.06 GB BF16 weights + 64.24 GB FP32 Adam = 80.30 GB theoretical and 108.0 GB actual (4 x 27 GB .distcp shards), writing in 4.32 s at 25 GB/s",
        ckpt["megatron_theoretical_gb"] == 80.30
        and ckpt["megatron_actual_gb"] == 108.0
        and ckpt["megatron_write_25gbps_s"] == 4.32,
    )

    # 2. Fleet Failure Probability, MTBF, and Young-Daly Optimal Checkpoint Interval (V13 Ch. 9 & DAI Ch. 11)
    yd_1024 = compute_fleet_reliability_and_young_daly(mtbf_s=28800.0, tc_s=180.0)
    check(
        "7. Young-Daly on 1,024 GPUs (M = 8 h = 28,800 s, Tc = 180 s) gives sqrt(10,368,000) - 180 = 3,220 - 180 = 3,040.0 s (~50.7 min)",
        yd_1024["radicand"] == 10368000.0
        and yd_1024["sqrt_term_rounded"] == 3220
        and yd_1024["t_opt_rounded_s"] == 3040.0
        and yd_1024["t_opt_minutes"] == 50.7,
    )

    yd_2048 = compute_fleet_reliability_and_young_daly(mtbf_s=21600.0, tc_s=240.0)
    check(
        "8. Young-Daly for 400B model on 2,048 GPUs (M = 6 h = 21,600 s, Tc = 240 s) gives sqrt(10,368,000) - 240 = 3,220 - 240 = 2,980.0 s (~49.7 min)",
        yd_2048["radicand"] == 10368000.0
        and yd_2048["sqrt_term_rounded"] == 3220
        and yd_2048["t_opt_rounded_s"] == 2980.0
        and yd_2048["t_opt_minutes"] == 49.7,
    )

    check(
        "9. At 99.9% daily GPU reliability on 100,000 GPUs, 24h survival probability is 3.7 x 10^-44 with 100.0 expected failures/day (14.4 min fleet MTBF); 1,024 GPUs over 30 days has >99.9999% failure certainty",
        yd_1024["survival_mantissa"] == 3.7
        and yd_1024["survival_exponent"] == -44
        and yd_1024["expected_daily_failures"] == 100.0
        and yd_1024["fleet_mtbf_minutes"] == 14.4
        and yd_1024["prob_failure_1024_30d_pct"] > 99.9999,
    )

    check(
        "10. Pausing 5 min per 60-min hour wastes 8.33% (~8%) of cluster time; Young-Daly T_opt = 3,040 s achieves 88.82% sync goodput vs 61.98% at 5-min intervals and 74.06% at 4-hr intervals",
        yd_1024["pause_5min_per_hour_pct"] == 8.33
        and yd_1024["goodput_opt_pct"] > yd_1024["goodput_5min_pct"]
        and yd_1024["goodput_opt_pct"] > yd_1024["goodput_4hr_pct"],
    )

    check(
        "11. Asynchronous checkpointing (2 s DtoH pause instead of 180 s sync write) boosts net training goodput at T_opt = 3,040 s from 88.82% to 94.66%",
        yd_1024["goodput_async_opt_pct"] > 94.0 and yd_1024["goodput_async_opt_pct"] > yd_1024["goodput_opt_pct"],
    )

    # 3. Asynchronous Checkpointing & Host CPU RAM / Swap Protection (V13 Ch. 9 & DAI Ch. 11)
    async_ok = evaluate_async_checkpoint_and_host_ram(
        node_shard_gb=100.0,
        dtoh_bandwidth_gbps=55.0,
        storage_flush_gbps=5.0,
        host_total_ram_gb=512.0,
        host_working_ram_gb=380.0,
        in_flight_buffers=1,
        swap_gb=0.0,
    )
    check(
        "12. Two-phase async checkpoint copies 100 GB GPU state to Host RAM in 1.82 s (< 2 s pause) and flushes in 20.0 s background thread (12.0x pause reduction; 6.0x DCP cached-plan speedup)",
        async_ok["dtoh_pause_s"] < 2.0
        and async_ok["background_flush_s"] == 20.0
        and async_ok["pause_reduction_factor"] == 12.0
        and async_ok["dcp_cached_plan_speedup"] == 6.0
        and async_ok["oom_killed"] is False,
    )

    async_oom = evaluate_async_checkpoint_and_host_ram(
        node_shard_gb=100.0,
        dtoh_bandwidth_gbps=55.0,
        storage_flush_gbps=5.0,
        host_total_ram_gb=512.0,
        host_working_ram_gb=380.0,
        in_flight_buffers=2,
        swap_gb=0.0,
    )
    check(
        "13. Overlapping 2 in-flight 100 GB async buffers (200 GB needed vs 132 GB free RAM) triggers Linux OOM killer: '[Node 3] dmesg: Out of memory: Killed process 1234 (python)'",
        async_oom["oom_killed"] is True
        and async_oom["dmesg_signature"] == "[Node 3] dmesg: Out of memory: Killed process 1234 (python)",
    )

    async_swap = evaluate_async_checkpoint_and_host_ram(
        node_shard_gb=100.0,
        dtoh_bandwidth_gbps=55.0,
        storage_flush_gbps=5.0,
        host_total_ram_gb=512.0,
        host_working_ram_gb=380.0,
        in_flight_buffers=2,
        swap_gb=100.0,
    )
    check(
        "14. Adding a 100.0 GB swap file (sudo fallocate -l 100G /swapfile; 232.0 GB total headroom) prevents the host OOM crash during burst staging",
        async_swap["available_ram_gb"] == 232.0 and async_swap["oom_killed"] is False,
    )

    # 4. Dynamic Checkpoint Resharding (64 -> 48 GPUs) & Deterministic Recovery (V13 Ch. 9 & Lab 04)
    reshard_fail = simulate_dcp_resharding_and_recovery(
        total_payload_gb=1120.0,
        old_world_size=64,
        new_world_size=48,
        checkpoint_format="naive_per_rank",
    )
    check(
        "15. Naive topology-coupled checkpoint fails on 64 -> 48 GPU resize with 'RuntimeError: Number of shards in checkpoint (64) does not match world size (48)'",
        reshard_fail["reshard_success"] is False
        and reshard_fail["error_message"]
        == "RuntimeError: Number of shards in checkpoint (64) does not match world size (48)",
    )

    reshard_dcp = simulate_dcp_resharding_and_recovery(
        total_payload_gb=1120.0,
        old_world_size=64,
        new_world_size=48,
        checkpoint_format="dcp",
    )
    check(
        "16. PyTorch DCP (FileSystemReader metadata) dynamically reshards 1,120.0 GB from 64 x 17.5 GB shards to 48 x 23.3333 GB shards and matches Lab 04 epochs 4-5 control losses",
        reshard_dcp["reshard_success"] is True
        and reshard_dcp["old_shard_gb"] == 17.5
        and reshard_dcp["new_shard_gb"] == 23.3333
        and reshard_dcp["deterministic_match"] is True,
    )

    no_optim = simulate_dcp_resharding_and_recovery(
        saved_components=["model_state_dict", "scheduler_state_dict", "dataloader_state", "rng_state"]
    )
    check(
        "17. Omitting optimizer_state_dict (Adam m, v buffers) causes an immediate epoch-4 loss spike on resume (1.9500 vs 0.9800 control) and fails deterministic recovery",
        no_optim["loss_spike_on_resume"] is True
        and no_optim["resumed_losses"][3] > no_optim["control_losses"][2]
        and no_optim["deterministic_match"] is False,
    )

    no_rng = simulate_dcp_resharding_and_recovery(
        saved_components=["model_state_dict", "optimizer_state_dict", "scheduler_state_dict", "dataloader_state"]
    )
    check(
        "18. Omitting rng_state (Python/NumPy/CUDA RNGs) causes silent epoch 4-5 trajectory divergence (1.0125 vs 0.9800 control) without throwing an exception",
        no_rng["silent_rng_divergence"] is True
        and no_rng["reshard_success"] is True
        and no_rng["deterministic_match"] is False,
    )

    # 5. Elastic Training (`torchrun`), Global Batch / LR Scaling, and Heartbeat Watchdogs
    elastic = evaluate_elastic_training_and_watchdogs()
    check(
        "19. TorchElastic --nnodes=2:4 --nproc_per_node=8 --max_restarts=3 with c10d spans 16..32 GPUs and continues cleanly on 3 surviving nodes (24 GPUs)",
        elastic["nnodes_spec"] == "2:4"
        and elastic["min_world_size"] == 16
        and elastic["max_world_size"] == 32
        and elastic["active_world_size"] == 24
        and elastic["within_elastic_bounds"] is True
        and elastic["valid_rdzv"] is True,
    )

    check(
        "20. Scaling gradient_accumulation_steps to 4 at 24 GPUs (micro_batch=2) preserves target global batch size of 192; V21 sqrt LR rule scales 1e-4 at batch 32 to 1.6e-3 (16x) at batch 8,192 (64 x 128)",
        elastic["grad_accum_steps"] == 4
        and elastic["preserved_global_batch"] is True
        and elastic["v21_global_batch"] == 8192
        and elastic["v21_sqrt_factor"] == 16.0
        and elastic["v21_scaled_lr"] == 0.0016,
    )

    check(
        "21. Crashing at step 5,243 with a 500-step checkpoint interval loads step 5,000, resumes at step 5,001, and bounds lost work to 243 steps (<= 500 max)",
        elastic["last_saved_step"] == 5000
        and elastic["resume_step"] == 5001
        and elastic["lost_steps"] == 243,
    )

    check(
        "22. Heartbeat FailureDetector (2.0 s interval x 4 missed = 8.0 s) detects dead ranks 225.0x faster than the 30-minute (1,800.0 s) default NCCL watchdog timeout",
        elastic["heartbeat_detect_s"] == 8.0
        and elastic["nccl_default_timeout_s"] == 1800.0
        and elastic["detection_speedup"] == 225.0,
    )

    # 6. Volume 13 Cluster Memory & Collective Baselines (V13 Ch. 1, Ch. 8, Ch. 12, Labs 01-03, DAI Ch. 4)
    v13 = evaluate_volume13_cluster_baselines()
    check(
        "23. GPT-3 (175B) FP32 weights require 700.0 GB (8.75x an 80 GB H100), and 1.46e18 FLOPs/step takes 4,679 s (~78 min) on 1 A100 vs 37 s on 128 A100s",
        v13["gpt3_fp32_weights_gb"] == 700.0
        and v13["gpt3_h100_ratio"] == 8.75
        and v13["gpt3_1gpu_a100_s"] == 4679.0
        and v13["gpt3_128gpu_a100_s"] == 37.0,
    )

    check(
        "24. 8-GPU NVLink Ring AllReduce on 28 GB FP32 gradients moves 49.0 GB in 54.4 ms (~54 ms), while 512-GPU IB moves 55.9 GB in 2.2 s (9 tree hops vs 512 ring hops)",
        v13["ring_8gpu_gb"] == 49.0
        and v13["ring_8gpu_ms"] == 54.4
        and v13["ring_512gpu_gb"] == 55.9
        and v13["ring_512gpu_s"] == 2.2
        and v13["tree_hops_512"] == 9.0,
    )

    check(
        "25. FSDP2 / ZeRO-3 shards a 7B model's 84.0 GB DDP parameter/gradient/optimizer state across 8 GPUs down to 10.5 GB/GPU (1/N reduction)",
        v13["ddp_7b_gb"] == 84.0 and v13["fsdp_7b_8gpu_gb"] == 10.5,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
