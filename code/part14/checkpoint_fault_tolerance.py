#!/usr/bin/env python3
"""Chapter 14.11 model: checkpointing, fault tolerance and elastic training.

Models, all plain arithmetic with no GPU needed:
1. Checkpoint size and the write pause: gathering every shard to rank 0 against every rank writing its own
   shard. The checkpoint holds weights and optimizer state, not gradients: 14 bytes per parameter for a BF16
   working copy plus FP32 master weights plus two FP32 Adam moments.
2. Fleet failure probability, cluster MTBF and the Young-Daly checkpoint interval, with goodput.
3. Two-phase asynchronous checkpointing and the host-RAM limit on staged shards.
4. Resume completeness: which saved components keep a resumed run identical to an uninterrupted one, and why a
   shard-count mismatch breaks a resume on a smaller world size.
5. Elastic training: world size bounds, global batch preservation, learning-rate scaling, and how much faster
   a heartbeat detector notices a dead rank than the default NCCL watchdog timeout (10 minutes).
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, Iterable, List

# Bytes per parameter that a checkpoint stores (gradients are NOT stored: they are rebuilt by the next backward pass).
CHECKPOINT_BYTES_PER_PARAM = 14  # 2 BF16 working weights + 4 FP32 master weights + 8 FP32 Adam moments
MINIMAL_CHECKPOINT_BYTES_PER_PARAM = 12  # FP32 master weights + Adam moments, BF16 copy rebuilt on load

# PyTorch default for the NCCL process group timeout (torch.distributed.init_process_group), in seconds.
NCCL_DEFAULT_TIMEOUT_S = 600.0

REQUIRED_COMPONENTS = (
    "model_state_dict",
    "optimizer_state_dict",
    "scheduler_state_dict",
    "dataloader_state",
    "rng_state_every_rank",
)


@dataclass(frozen=True)
class CheckpointWriteScenario:
    params_b: float = 70.0
    bytes_per_param: int = CHECKPOINT_BYTES_PER_PARAM
    num_gpus: int = 128
    gather_inbound_gbps: float = 25.0
    single_node_write_gbps: float = 5.0
    per_gpu_writer_gbps: float = 5.0
    filesystem_ceiling_gbps: float = 400.0


def evaluate_checkpoint_write_strategies(
    cfg: CheckpointWriteScenario = CheckpointWriteScenario(),
) -> Dict[str, float]:
    """Compare gather-to-rank-0 with every rank writing its own shard."""
    total_payload_gb = cfg.params_b * cfg.bytes_per_param
    per_gpu_shard_gb = total_payload_gb / cfg.num_gpus

    gather_network_s = total_payload_gb / cfg.gather_inbound_gbps
    single_node_write_s = total_payload_gb / cfg.single_node_write_gbps
    naive_total_s = gather_network_s + single_node_write_s

    ideal_parallel_write_s = per_gpu_shard_gb / cfg.per_gpu_writer_gbps
    aggregate_demand_gbps = cfg.num_gpus * cfg.per_gpu_writer_gbps
    effective_aggregate_gbps = min(aggregate_demand_gbps, cfg.filesystem_ceiling_gbps)
    effective_per_gpu_gbps = effective_aggregate_gbps / cfg.num_gpus
    realistic_parallel_write_s = per_gpu_shard_gb / effective_per_gpu_gbps

    return {
        "total_payload_gb": round(total_payload_gb, 2),
        "per_gpu_shard_gb": round(per_gpu_shard_gb, 5),
        "gather_network_s": round(gather_network_s, 2),
        "single_node_write_s": round(single_node_write_s, 2),
        "naive_total_s": round(naive_total_s, 2),
        "ideal_parallel_write_s": round(ideal_parallel_write_s, 2),
        "aggregate_demand_gbps": round(aggregate_demand_gbps, 2),
        "effective_per_gpu_gbps": round(effective_per_gpu_gbps, 4),
        "realistic_parallel_write_s": round(realistic_parallel_write_s, 2),
        "speedup_vs_naive": round(naive_total_s / realistic_parallel_write_s, 1),
    }


def compute_fleet_reliability_and_young_daly(
    mtbf_s: float = 28800.0,
    tc_s: float = 180.0,
    daily_gpu_reliability: float = 0.999,
    fleet_gpus: int = 100000,
) -> Dict[str, float]:
    """Fleet survival probability, Young-Daly interval and goodput trade-offs."""
    radicand = 2.0 * mtbf_s * tc_s
    sqrt_term = math.sqrt(radicand)
    t_opt_exact_s = sqrt_term - tc_s
    t_opt_rounded_s = round(sqrt_term) - tc_s  # round the square root to whole seconds first, as the chapter does

    log10_survival = fleet_gpus * math.log10(daily_gpu_reliability)
    survival_exponent = int(math.floor(log10_survival))
    survival_mantissa = round(10.0 ** (log10_survival - survival_exponent), 1)
    expected_daily_failures = fleet_gpus * (1.0 - daily_gpu_reliability)
    fleet_mtbf_minutes = (24.0 * 60.0) / expected_daily_failures

    prob_survive_1024_30d = daily_gpu_reliability ** (1024 * 30)
    prob_failure_1024_30d_pct = (1.0 - prob_survive_1024_30d) * 100.0
    pause_5min_per_hour_pct = (5.0 / 60.0) * 100.0

    def goodput_pct(interval_s: float, write_s: float) -> float:
        cycle_s = interval_s + write_s
        write_efficiency = interval_s / cycle_s
        rework_fraction = min(0.99, cycle_s / (2.0 * mtbf_s))
        return round(write_efficiency * (1.0 - rework_fraction) * 100.0, 2)

    return {
        "radicand": radicand,
        "sqrt_term_rounded": round(sqrt_term),
        "t_opt_exact_s": round(t_opt_exact_s, 2),
        "t_opt_rounded_s": round(t_opt_rounded_s, 1),
        "t_opt_minutes": round(t_opt_rounded_s / 60.0, 1),
        "survival_mantissa": survival_mantissa,
        "survival_exponent": survival_exponent,
        "expected_daily_failures": round(expected_daily_failures, 1),
        "fleet_mtbf_minutes": round(fleet_mtbf_minutes, 1),
        "prob_failure_1024_30d_pct": round(prob_failure_1024_30d_pct, 6),
        "pause_5min_per_hour_pct": round(pause_5min_per_hour_pct, 2),
        "goodput_5min_pct": goodput_pct(300.0, tc_s),
        "goodput_opt_pct": goodput_pct(t_opt_rounded_s, tc_s),
        "goodput_4hr_pct": goodput_pct(14400.0, tc_s),
        "goodput_async_opt_pct": goodput_pct(t_opt_rounded_s, 2.0),
    }


def evaluate_async_checkpoint_and_host_ram(
    node_shard_gb: float = 100.0,
    dtoh_bandwidth_gbps: float = 55.0,
    storage_flush_gbps: float = 5.0,
    host_total_ram_gb: float = 512.0,
    host_working_ram_gb: float = 380.0,
    in_flight_buffers: int = 1,
) -> Dict[str, float | bool | str]:
    """Two-phase asynchronous checkpoint (GPU to pinned host RAM, then host RAM to storage) and the host-RAM limit.

    Pinned host memory is locked in RAM and cannot be swapped, so the only safe rule is that the staged shards must
    fit in free RAM: allow one save in flight, and wait for the previous flush before staging the next.
    """
    dtoh_pause_s = node_shard_gb / dtoh_bandwidth_gbps
    background_flush_s = node_shard_gb / storage_flush_gbps
    sync_pause_s = dtoh_pause_s + background_flush_s

    required_staging_ram_gb = node_shard_gb * in_flight_buffers
    available_ram_gb = host_total_ram_gb - host_working_ram_gb
    oom_killed = required_staging_ram_gb > available_ram_gb

    return {
        "dtoh_pause_s": round(dtoh_pause_s, 2),
        "background_flush_s": round(background_flush_s, 2),
        "sync_pause_s": round(sync_pause_s, 2),
        "pause_reduction_factor": round(sync_pause_s / dtoh_pause_s, 1),
        "required_staging_ram_gb": round(required_staging_ram_gb, 1),
        "available_ram_gb": round(available_ram_gb, 1),
        "oom_killed": oom_killed,
        "dmesg_signature": (
            "[Node 3] dmesg: Out of memory: Killed process 1234 (python)" if oom_killed else "OK"
        ),
    }


def simulate_resume(
    total_payload_gb: float = 980.0,
    old_world_size: int = 64,
    new_world_size: int = 48,
    checkpoint_format: str = "dcp",  # "naive_per_rank" or "dcp"
    saved_components: Iterable[str] | None = None,
) -> Dict[str, object]:
    """Which resume problems appear for a given checkpoint format and set of saved components."""
    saved = set(REQUIRED_COMPONENTS if saved_components is None else saved_components)
    old_shard_gb = total_payload_gb / old_world_size
    new_shard_gb = total_payload_gb / new_world_size

    if old_world_size != new_world_size and checkpoint_format == "naive_per_rank":
        reshard_success = False
        error_message = (
            f"RuntimeError: Number of shards in checkpoint ({old_world_size}) "
            f"does not match world size ({new_world_size})"
        )
    else:
        reshard_success = True
        error_message = "OK"

    missing = sorted(set(REQUIRED_COMPONENTS) - saved)
    return {
        "old_shard_gb": round(old_shard_gb, 5),
        "new_shard_gb": round(new_shard_gb, 4),
        "reshard_success": reshard_success,
        "error_message": error_message,
        "missing_components": missing,
        "loss_spike_on_resume": "optimizer_state_dict" not in saved,
        "wrong_learning_rate": "scheduler_state_dict" not in saved,
        "data_replayed_or_skipped": "dataloader_state" not in saved,
        "silent_rng_divergence": "rng_state_every_rank" not in saved,
        "deterministic_match": reshard_success and not missing,
    }


def evaluate_elastic_training_and_watchdogs(
    min_nodes: int = 2,
    max_nodes: int = 4,
    active_nodes: int = 3,
    gpus_per_node: int = 8,
    max_restarts: int = 3,
    rdzv_backend: str = "c10d",
    rdzv_endpoint: str = "dgx-001:29400",
    micro_batch_per_gpu: int = 2,
    target_global_batch: int = 192,
    heartbeat_interval_s: float = 2.0,
    missed_heartbeats_threshold: int = 4,
    nccl_default_timeout_s: float = NCCL_DEFAULT_TIMEOUT_S,
) -> Dict[str, object]:
    """torchrun elastic world sizing, batch and learning-rate adjustment, and failure-detection latency."""
    min_world_size = min_nodes * gpus_per_node
    max_world_size = max_nodes * gpus_per_node
    active_world_size = active_nodes * gpus_per_node

    within_elastic_bounds = min_nodes <= active_nodes <= max_nodes
    valid_rdzv = rdzv_backend in ("c10d", "etcd-v2") and not (
        max_nodes > 1 and rdzv_endpoint.startswith("127.0.0.1")
    )

    step_batch = active_world_size * micro_batch_per_gpu
    grad_accum_steps = target_global_batch // step_batch
    preserved_global_batch = step_batch * grad_accum_steps == target_global_batch

    scaled_global_batch = 64 * 128  # 8,192 sequences
    sqrt_factor = math.sqrt(scaled_global_batch / 32.0)
    scaled_lr = round(1e-4 * sqrt_factor, 6)

    crash_step = 5243
    ckpt_interval_steps = 500
    last_saved_step = (crash_step // ckpt_interval_steps) * ckpt_interval_steps
    resume_step = last_saved_step + 1
    lost_steps = crash_step - last_saved_step

    heartbeat_detect_s = heartbeat_interval_s * missed_heartbeats_threshold
    detection_speedup = nccl_default_timeout_s / heartbeat_detect_s

    return {
        "nnodes_spec": f"{min_nodes}:{max_nodes}",
        "min_world_size": min_world_size,
        "max_world_size": max_world_size,
        "active_world_size": active_world_size,
        "max_restarts": max_restarts,
        "within_elastic_bounds": within_elastic_bounds,
        "valid_rdzv": valid_rdzv,
        "grad_accum_steps": grad_accum_steps,
        "preserved_global_batch": preserved_global_batch,
        "scaled_global_batch": scaled_global_batch,
        "sqrt_factor": sqrt_factor,
        "scaled_lr": scaled_lr,
        "last_saved_step": last_saved_step,
        "resume_step": resume_step,
        "lost_steps": lost_steps,
        "heartbeat_detect_s": round(heartbeat_detect_s, 1),
        "nccl_default_timeout_s": round(nccl_default_timeout_s, 1),
        "detection_speedup": round(detection_speedup, 1),
    }


if __name__ == "__main__":
    print("Checkpoint write strategies:", evaluate_checkpoint_write_strategies())
    print("Young-Daly and fleet reliability:", compute_fleet_reliability_and_young_daly())
    print("Async checkpoint and host RAM:", evaluate_async_checkpoint_and_host_ram())
    print("Resume simulation:", simulate_resume())
    print("Elastic training and watchdogs:", evaluate_elastic_training_and_watchdogs())
