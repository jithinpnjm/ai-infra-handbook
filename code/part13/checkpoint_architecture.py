"""Chapter 13.7: Checkpoint architecture and recovery.

Pure Python 3 standard-library reference models for:
1. Checkpoint State Footprint & Memory Accounting (V13 Ch. 01, V13 Ch. 09, V15 Ch. 08):
   - Mixed-precision AdamW checkpoint byte footprint vs active training state:
     - Active training memory per parameter (`16 bytes/param`): `2` bytes FP16/BF16 weights +
       `2` bytes FP16/BF16 gradients + `4` bytes FP32 master weights + `4` bytes FP32 Adam
       first moment (momentum `m`) + `4` bytes FP32 Adam second moment (variance `v`)
       (or equivalently in full FP32 gradient accounting: `4` B weights + `4` B gradients +
       `8` B optimizer momentum/variance = `16 bytes/param`).
     - Persistent checkpoint state per parameter (`14 bytes/param` when omitting transient
       gradients: `2` bytes BF16 working weights + `4` bytes FP32 master weights + `4` bytes
       FP32 momentum + `4` bytes FP32 variance, or `12 bytes/param` when BF16 working weights
       are reconstructed directly from FP32 master weights on load, vs `16 bytes/param` when
       gradients or full buffers are included).
     - Concrete model footprints:
      * `7B` parameter model (`V13 Ch. 01`): `28 GB` (`28.0 GB`) FP32 weights + `28 GB` FP32 gradients +
        `56 GB` Adam optimizer states = `112 GB` (`112.0 GB`) model/grad/opt state (`84.0 GB` at `12 B/p`,
        `98.0 GB` at `14 B/p`, `24.50 GB` and `28.00 GB` per GPU across `4` GPUs; `+ 60-80 GB` activations +
        `5-10 GB` buffers = `180-190 GB` total step footprint vs `80 GB` H100 HBM3).
      * `70B` parameter model (`V13 Ch. 09`): `280.0 GB` (`4 B/p`), `840.0 GB` (`12 B/p`),
        `70B x 14 B = 980.0 GB` persistent state; `70B x 16 B = 1,120.0 GB` (`~1.09 TB` / `1.2 TB`
        with metadata/buffers). Sharded across `128` H100 GPUs with FSDP = `8.75 GB` (`8.75000 GB`)
        per GPU shard (`16 B/param`) or `7.65625 GB` (`7.66 GB`, `14 B/param`).
      * `175B` parameter GPT-3 (`V13 Ch. 01`): `175B x 4 B = 700.0 GB` FP32 weights alone
        (`8.75x` single `80 GB` H100 HBM3), `2,100.0 GB` (`12 B/p`), `175B x 14 B = 2,450.0 GB`
        (`2.45 TB`) checkpoint (`19.14063 GB`/GPU on `128` GPUs), `175B x 16 B = 2,800.0 GB`
        (`2.80 TB` / `2.8 TB`, `21.87500 GB`/GPU) full state; single training step at batch `2048`,
        seq `2048` = `1.46e18` FLOPs (`4,679.49 s` / `679.49` / `4,679 s` = `78 min` on `1` A100 at
        `312 TFLOPS` vs `36.56 s` / `37 s` on `128` A100 GPUs).
      * `400B` parameter model: `1,600.0 GB` (`4 B/p`), `4,800.0 GB` (`12 B/p`), `5,600.0 GB` (`5.60 TB`,
        `2.73438 GB`/GPU across `2,048` GPUs at `14 B/p`), `6,400.0 GB` (`6.40 TB`, `3.12500 GB` /
        `3.125 GB`/GPU at `16 B/p`).
2. Naive Gather-to-Rank-0 vs Sharded Parallel Checkpoint Write & Straggler Stalls (V13 Ch. 09, V15 Ch. 08):
   - `70B` model (`1,120 GB` payload) across `128` GPUs:
     * Naive gather-to-rank-0: `1,120 GB / 25 GB/s = 44.8 s` (`~45 s`) network gather +
       `1,120 GB / 5 GB/s = 224.0 s` single-node storage write = `268.8 s` (`~269 s` / `4.5 min`).
     * Distributed sharded write: `8.75 GB` per GPU shard; at `5 GB/s` per writer (`1.75 s` ideal),
       `128 x 5 GB/s = 640 GB/s` exceeds `400 GB/s` parallel filesystem ceiling -> `3.125 GB/s`
       (`~3.1 GB/s`) effective per-GPU rate -> `8.75 / 3.125 = 2.8 s` (`96.0x` faster than `268.8 s`).
   - Phase instrumentation & straggler stall (`V15 Ch. 08`):
     * Rank 0 serialization `3.1 s` (`8.25 GB` shard) + collective barrier sync `28.3 s` (Rank 7
       straggler behind by `28.3 s`) + synchronous slow shared-storage write `450.2 s`
       (`8.25 GB / 450.2 s = 18.33 MB/s`, `~18 MB/s`) = `481.6 s` (`481.5 s` reported, `8+ min`
       GPU idle stall).
     * Across `1,000` checkpoints x `8 min` (`480 s`) synchronous stall = `8,000 min` (`133.33 hours` /
       `133 hours`, `20%` of a `500`-hour run vs `26.67%`), reduced via local NVMe staging (`5 s` stall)
       to `5,000 s` = `83.33 min` = `1.39 hours` (`~1.4 hours`, a `96.0x` stall reduction).
3. Young-Daly Optimal Checkpoint Interval & Cluster MTBF Scaling (V13 Ch. 09):
   - First-order Young formula: `tau_young = sqrt(2 * T_write * M)`
   - Higher-order Daly formula: `tau_daly = sqrt(2 * T_write * M) - T_write`
   - Cluster MTBF `M = M_device / N_devices`:
     * Case A (`V13 Ch. 09`): `1,024`-GPU cluster with `M = 8 hours` (`28,800 s`) and `T_write = 180.0 s`:
       `tau_young = sqrt(2 * 28800 * 180) = sqrt(10,368,000) = 3,219.94 s` (`219.94` / `~3,220 s` = `53.67 min`),
       `tau_daly = 3,219.94 - 180 = 3,039.94 s` (`039.94` / `~3,040 s` = `50.67 min` / `50.7 min`,
       `5.59%` write overhead, `1,519.97 s` / `519.97` = `25.33 min` expected rework).
     * Case B (`V13 Ch. 09` 400B on 2,048 GPUs): `M = 6 hours` (`21,600 s`) and `T_write = 240.0 s` (`4 min`):
       `tau_young = sqrt(2 * 21600 * 240) = sqrt(10,368,000) = 3,219.94 s` (`~3,220 s` = `53.67 min`),
       `tau_daly = 3,219.94 - 240 = 2,979.94 s` (`979.94` / `~2,980 s` = `49.67 min`, `7.45%` write
       overhead, rounded to `30-40 min`).
     * Case C (`V15 Ch. 08` async local NVMe staging): `M = 28,800 s` and `T_write = 5.0 s`:
       `tau_young = 536.66 s` (`8.94 min`), `tau_daly = 531.66 s` (`8.86 min`, `0.93%` write overhead,
       `265.83 s` = `4.43 min` expected rework).
4. Synchronous vs Two-Stage Asynchronous Checkpointing & SuperPOD Bandwidth (V15 Ch. 08, V13 Ch. 09, SuperPOD GB300 RA):
   - Stage 1 (GPU HBM -> Pinned Host DRAM via PCIe/NVLink-C2C DtoH copy at `50.0 GB/s` in `1.40 s` / `< 1-2 s`,
     or fast local NVMe `/raid` / `/local-nvme` write at `20.0 GB/s` in `3.50 s` / `3-5 s`), followed
     immediately by resuming GPU math (`25.0x` speedup vs `35.0 s` direct `2.0 GB/s` PFS write).
   - Stage 2 (Background CPU thread/process flushes from Host DRAM or `/local-nvme` to shared parallel
     filesystem `/shared-storage` / Lustre / BeeGFS / WekaFS / VAST over RDMA without blocking compute).
   - Host OOM protection: verify `pinned_buffer_gb + process_rss_gb < host_ram_gb` (`180.0 + 70.0 = 250.0 GB <= 512.0 GB`
     safe vs `5 x 70.0 = 350.0 GB` -> `180.0 + 350.0 = 530.0 GB > 512.0 GB` OOM) so background DtoH
     staging never triggers the Linux OOM killer (`dmesg: Out of memory: Killed process`), and gate
     the next checkpoint trigger if the prior background flush is still in flight.
   - DGX SuperPOD GB300 storage performance guidelines (`Table 5`, `superpod-gb300-ra`):
     * Single SU (`Scalable Unit`): Standard `90 GB/s` read / `45 GB/s` write; Enhanced `280 GB/s` read / `140 GB/s` write.
     * `4` SU cluster: Standard `360 GB/s` read / `180 GB/s` write; Enhanced `1,120 GB/s` read / `560 GB/s` write.
5. PyTorch Distributed Checkpoint (`DCP` / `torch.distributed.checkpoint`) `N -> M` Resharding & Atomic Manifests (V13 Ch. 09, V13 Lab 03, V13 Lab 04, V15 Ch. 08):
   - Global tensor metadata (`shape`, `dtype`, `global_offset`, `chunk_lengths`) decouples checkpoint
     storage from world size (`N = 64` GPUs -> `M = 48` GPUs after a node drain, or `N = 4` -> `M = 8`).
   - Deterministic `1D` / `2D` interval-intersection resharding planner maps every target rank `r_dst in [0, M)`
     to exact source shard slices `(src_rank, src_local_start, src_local_end, dst_local_start, dst_local_end)`
     with zero missing or duplicated elements.
   - Atomic publication & integrity verification: write shards to `.tmp` staging directory, compute `SHA-256`
     checksums, fsync, write `manifest.json` (`completed: true` + `model_state`, `optimizer_state`,
     `scheduler_state`, `rng_state`, `dataloader_state`), and atomically `os.replace()` into final step directory.
   - Parallel collective restore (`V15 Ch. 08`): `500 GB` checkpoint across `8` Lustre OSTs at `2 GB/s` per OST
     (`16 GB/s` aggregate with `lfs setstripe -c -1` + GDS) restores in `31.25 s` (`~31 s`) vs `250.0 s`
     single-OST serial read (`+ 10 s` deserialize + `5 s` distribute = `265 s` = `4.42 min`).
6. Transparent Driver-Level GPU Checkpointing with `cuda-checkpoint` and `CRIU` (AISPE Ch. 5):
   - Four CUDA Driver API state transitions:
     `RUNNING` --(`cuCheckpointProcessLock`)--> `LOCKED` --(`cuCheckpointProcessCheckpoint`)-->
     `CHECKPOINTED` (GPU HBM copied to driver-managed host memory, GPU resources released, CRIU snapshots
     process) --(`cuCheckpointProcessRestore`)--> `LOCKED` (GPUs reacquired, device memory mapped to original
     virtual addresses, streams/contexts restored) --(`cuCheckpointProcessUnlock`)--> `RUNNING`.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 1. Checkpoint State Footprint & Memory Accounting (V13 Ch. 01, V13 Ch. 09)
# ---------------------------------------------------------------------------

REQUIRED_CHECKPOINT_KEYS: Tuple[str, ...] = (
    "model_state_dict",
    "optimizer_state_dict",
    "scheduler_state_dict",
    "rng_state",
    "dataloader_state",
    "step_metadata",
)


@dataclass(frozen=True)
class ModelCheckpointFootprint:
    params_billions: float
    fp32_weights_only_gb: float
    persistent_12b_gb: float
    persistent_14b_gb: float
    active_training_16b_gb: float
    num_gpus: int
    shard_14b_per_gpu_gb: float
    shard_16b_per_gpu_gb: float


def compute_adamw_checkpoint_footprint(
    params_billions: float,
    num_gpus: int = 128,
) -> ModelCheckpointFootprint:
    """Compute mixed-precision AdamW memory and checkpoint footprints.

    Byte-per-parameter breakdown:
    - `4 B/param`: FP32 weights only (e.g., 175B GPT-3 = 700 GB; 7B = 28 GB).
    - `12 B/param`: Minimal persistent checkpoint (4 B FP32 master weights +
      4 B FP32 Adam momentum m + 4 B FP32 Adam variance v; BF16 working weights
      cast on restore).
    - `14 B/param`: Standard mixed-precision persistent checkpoint (2 B BF16/FP16
      working weights + 4 B FP32 master weights + 4 B FP32 momentum + 4 B FP32
      variance; transient 2 B BF16 gradients omitted on disk).
    - `16 B/param`: Full active training state / V13 Ch. 09 checkpoint accounting
      (2 B BF16 weights + 2 B BF16 gradients + 4 B FP32 master weights + 8 B FP32
      Adam moments, or 4 B FP32 weights + 4 B FP32 gradients + 8 B FP32 Adam moments).
    """
    if params_billions <= 0 or num_gpus <= 0:
        raise ValueError("params_billions and num_gpus must be positive")

    fp32_weights_gb = round(params_billions * 4.0, 4)
    ckpt_12b_gb = round(params_billions * 12.0, 4)
    ckpt_14b_gb = round(params_billions * 14.0, 4)
    train_16b_gb = round(params_billions * 16.0, 4)

    return ModelCheckpointFootprint(
        params_billions=params_billions,
        fp32_weights_only_gb=fp32_weights_gb,
        persistent_12b_gb=ckpt_12b_gb,
        persistent_14b_gb=ckpt_14b_gb,
        active_training_16b_gb=train_16b_gb,
        num_gpus=num_gpus,
        shard_14b_per_gpu_gb=round(ckpt_14b_gb / num_gpus, 5),
        shard_16b_per_gpu_gb=round(train_16b_gb / num_gpus, 5),
    )


def evaluate_v13_memory_and_compute_scaling() -> Dict[str, float]:
    """Return the exact V13 Ch. 01 memory and compute scaling figures.

    - 7B model in FP32 with Adam: 28 GB weights + 28 GB gradients + 56 GB Adam
      states = 112 GB static state (+ 60-80 GB activations + 5-10 GB buffers =
      180-190 GB total vs 80 GB H100 HBM3).
    - 175B GPT-3 in FP32: 700 GB weights alone (8.75x 80 GB H100).
    - 175B GPT-3 step FLOPs at batch 2048, seq 2048: 1.46e18 FLOPs -> 4,679.49 s
      (~4,679 s / 78.0 min) on 1 A100 (312 TFLOPS) vs 36.56 s (~37 s) on 128 A100s.
    """
    seven_b = compute_adamw_checkpoint_footprint(7.0, num_gpus=4)
    gpt3 = compute_adamw_checkpoint_footprint(175.0, num_gpus=128)
    step_flops = 1.46e18
    a100_flops = 312e12
    single_a100_sec = step_flops / a100_flops
    cluster_128_a100_sec = single_a100_sec / 128.0
    return {
        "seven_b_fp32_weights_gb": seven_b.fp32_weights_only_gb,
        "seven_b_fp32_gradients_gb": 28.0,
        "seven_b_adam_states_gb": 56.0,
        "seven_b_static_total_gb": seven_b.active_training_16b_gb,
        "seven_b_ckpt_14b_gb": seven_b.persistent_14b_gb,
        "seven_b_step_min_gb": 180.0,
        "seven_b_step_max_gb": 190.0,
        "gpt3_fp32_weights_gb": gpt3.fp32_weights_only_gb,
        "gpt3_vs_80gb_h100_ratio": round(gpt3.fp32_weights_only_gb / 80.0, 2),
        "gpt3_single_a100_sec": round(single_a100_sec, 2),
        "gpt3_single_a100_min": round(single_a100_sec / 60.0, 2),
        "gpt3_128_a100_sec": round(cluster_128_a100_sec, 2),
    }


# ---------------------------------------------------------------------------
# 2. Gather-to-Rank-0 vs Sharded Write & Straggler Analysis (V13 Ch. 09, V15 Ch. 08)
# ---------------------------------------------------------------------------

def compare_gather_vs_sharded_checkpoint_write(
    total_checkpoint_gb: float = 1120.0,
    num_gpus: int = 128,
    rank0_gather_bw_gb_s: float = 25.0,
    rank0_write_bw_gb_s: float = 5.0,
    per_gpu_writer_bw_gb_s: float = 5.0,
    filesystem_ceiling_gb_s: float = 400.0,
) -> Dict[str, float]:
    """Compare naive gather-to-rank-0 checkpointing against sharded parallel writes (V13 Ch. 09)."""
    gather_sec = total_checkpoint_gb / rank0_gather_bw_gb_s
    single_write_sec = total_checkpoint_gb / rank0_write_bw_gb_s
    naive_total_sec = gather_sec + single_write_sec

    shard_gb = total_checkpoint_gb / num_gpus
    uncapped_aggregate_gb_s = num_gpus * per_gpu_writer_bw_gb_s
    effective_aggregate_gb_s = min(uncapped_aggregate_gb_s, filesystem_ceiling_gb_s)
    effective_per_gpu_gb_s = effective_aggregate_gb_s / num_gpus
    ideal_sharded_sec = shard_gb / per_gpu_writer_bw_gb_s
    realistic_sharded_sec = shard_gb / effective_per_gpu_gb_s

    return {
        "total_checkpoint_gb": round(total_checkpoint_gb, 2),
        "shard_per_gpu_gb": round(shard_gb, 4),
        "naive_gather_sec": round(gather_sec, 2),
        "naive_write_sec": round(single_write_sec, 2),
        "naive_total_sec": round(naive_total_sec, 2),
        "uncapped_aggregate_gb_s": round(uncapped_aggregate_gb_s, 2),
        "filesystem_ceiling_gb_s": round(filesystem_ceiling_gb_s, 2),
        "effective_per_gpu_gb_s": round(effective_per_gpu_gb_s, 4),
        "ideal_sharded_sec": round(ideal_sharded_sec, 2),
        "realistic_sharded_sec": round(realistic_sharded_sec, 2),
        "speedup_factor": round(naive_total_sec / realistic_sharded_sec, 2),
    }


def analyze_checkpoint_phases_and_straggler(
    shard_size_gb: float = 8.25,
    serialize_sec: float = 3.1,
    sync_barrier_sec: float = 28.3,
    sync_write_sec: float = 450.2,
    local_nvme_write_sec: float = 5.0,
    planned_checkpoints: int = 1000,
    nominal_pause_min: float = 8.0,
) -> Dict[str, float]:
    """Analyze the V15 Ch. 08 checkpoint phase breakdown and 1,000-checkpoint stall math."""
    total_sync_sec = serialize_sec + sync_barrier_sec + sync_write_sec
    shared_write_mb_s = (shard_size_gb * 1000.0) / sync_write_sec
    sync_stall_hours_1000 = (planned_checkpoints * nominal_pause_min) / 60.0
    async_stall_hours_1000 = (planned_checkpoints * local_nvme_write_sec) / 3600.0
    stall_speedup = (nominal_pause_min * 60.0) / local_nvme_write_sec

    return {
        "shard_size_gb": shard_size_gb,
        "serialize_sec": serialize_sec,
        "sync_barrier_sec": sync_barrier_sec,
        "sync_write_sec": sync_write_sec,
        "total_sync_sec": round(total_sync_sec, 2),
        "shared_write_mb_s": round(shared_write_mb_s, 2),
        "sync_stall_minutes_1000": round(planned_checkpoints * nominal_pause_min, 2),
        "sync_stall_hours_1000": round(sync_stall_hours_1000, 2),
        "async_stall_hours_1000": round(async_stall_hours_1000, 4),
        "per_ckpt_stall_reduction_x": round(stall_speedup, 2),
    }


# ---------------------------------------------------------------------------
# 3. Young-Daly Optimal Checkpoint Interval & MTBF Math (V13 Ch. 09)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class YoungDalySchedule:
    cluster_mtbf_sec: float
    cluster_mtbf_hours: float
    checkpoint_write_sec: float
    tau_young_sec: float
    tau_young_min: float
    tau_daly_sec: float
    tau_daly_min: float
    steady_state_write_overhead_pct: float
    expected_rework_per_failure_sec: float


def compute_young_daly_interval(
    cluster_mtbf_sec: float,
    checkpoint_write_sec: float,
) -> YoungDalySchedule:
    """Compute Young's first-order and Daly's optimal checkpoint intervals.

    - Young's formula: `tau_opt = sqrt(2 * T_write * M)`
    - Daly's formula:  `tau_opt = sqrt(2 * T_write * M) - T_write`
    """
    if cluster_mtbf_sec <= 0 or checkpoint_write_sec <= 0:
        raise ValueError("cluster_mtbf_sec and checkpoint_write_sec must be positive")

    tau_young = math.sqrt(2.0 * cluster_mtbf_sec * checkpoint_write_sec)
    tau_daly = max(checkpoint_write_sec, tau_young - checkpoint_write_sec)
    overhead_pct = (checkpoint_write_sec / (tau_daly + checkpoint_write_sec)) * 100.0

    return YoungDalySchedule(
        cluster_mtbf_sec=round(cluster_mtbf_sec, 2),
        cluster_mtbf_hours=round(cluster_mtbf_sec / 3600.0, 4),
        checkpoint_write_sec=round(checkpoint_write_sec, 2),
        tau_young_sec=round(tau_young, 2),
        tau_young_min=round(tau_young / 60.0, 2),
        tau_daly_sec=round(tau_daly, 2),
        tau_daly_min=round(tau_daly / 60.0, 2),
        steady_state_write_overhead_pct=round(overhead_pct, 2),
        expected_rework_per_failure_sec=round(tau_daly / 2.0, 2),
    )


def compute_cluster_mtbf_hours(
    per_gpu_node_mtbf_hours: float,
    num_nodes_or_gpus: int,
) -> float:
    """Compute aggregate cluster MTBF (in hours) given component MTBF and count."""
    if per_gpu_node_mtbf_hours <= 0 or num_nodes_or_gpus <= 0:
        raise ValueError("per_gpu_node_mtbf_hours and num_nodes_or_gpus must be positive")
    return round(per_gpu_node_mtbf_hours / num_nodes_or_gpus, 4)


# ---------------------------------------------------------------------------
# 4. Two-Stage Async Checkpointing, Host OOM Guard & SuperPOD Tiers
# ---------------------------------------------------------------------------

SUPERPOD_GB300_STORAGE_TIERS: Dict[str, Dict[str, float]] = {
    "1_SU_Standard": {"read_gb_s": 90.0, "write_gb_s": 45.0},
    "1_SU_Enhanced": {"read_gb_s": 280.0, "write_gb_s": 140.0},
    "4_SU_Standard": {"read_gb_s": 360.0, "write_gb_s": 180.0},
    "4_SU_Enhanced": {"read_gb_s": 1120.0, "write_gb_s": 560.0},
}


def simulate_two_stage_async_checkpoint(
    node_checkpoint_gb: float = 70.0,
    dtoh_pcie_or_c2c_gb_s: float = 50.0,
    local_nvme_write_gb_s: float = 20.0,
    remote_pfs_write_gb_s: float = 2.0,
    host_total_ram_gb: float = 512.0,
    host_active_rss_gb: float = 180.0,
    in_flight_unflushed_snapshots: int = 1,
) -> Dict[str, float | bool]:
    """Simulate two-stage asynchronous checkpointing (GPU HBM -> Pinned Host RAM -> Local NVMe -> PFS)."""
    stage1_dtoh_pause_sec = node_checkpoint_gb / dtoh_pcie_or_c2c_gb_s
    stage1_nvme_flush_sec = node_checkpoint_gb / local_nvme_write_gb_s
    stage2_pfs_flush_sec = node_checkpoint_gb / remote_pfs_write_gb_s
    sync_direct_pfs_pause_sec = stage2_pfs_flush_sec

    required_pinned_ram_gb = node_checkpoint_gb * in_flight_unflushed_snapshots
    total_host_mem_used_gb = host_active_rss_gb + required_pinned_ram_gb
    oom_triggered = total_host_mem_used_gb > host_total_ram_gb

    return {
        "node_checkpoint_gb": round(node_checkpoint_gb, 2),
        "stage1_dtoh_pause_sec": round(stage1_dtoh_pause_sec, 3),
        "stage1_nvme_flush_sec": round(stage1_nvme_flush_sec, 3),
        "stage2_pfs_flush_sec": round(stage2_pfs_flush_sec, 3),
        "sync_direct_pfs_pause_sec": round(sync_direct_pfs_pause_sec, 3),
        "gpu_pause_speedup_vs_sync_x": round(sync_direct_pfs_pause_sec / stage1_dtoh_pause_sec, 2),
        "total_host_mem_used_gb": round(total_host_mem_used_gb, 2),
        "host_total_ram_gb": round(host_total_ram_gb, 2),
        "oom_triggered": oom_triggered,
    }


def evaluate_checkpoint_retention_policy(
    all_epochs: List[int],
    keep_recent: int = 5,
    milestone_interval: int = 100,
) -> Dict[str, List[int]]:
    """Evaluate tiered checkpoint retention (keep last N + periodic milestones, V15 Ch. 08)."""
    sorted_epochs = sorted(all_epochs)
    recent_set = set(sorted_epochs[-keep_recent:]) if keep_recent > 0 else set()
    kept: List[int] = []
    deleted: List[int] = []
    for ep in sorted_epochs:
        if ep in recent_set or (milestone_interval > 0 and ep % milestone_interval == 0):
            kept.append(ep)
        else:
            deleted.append(ep)
    return {"kept_epochs": kept, "deleted_epochs": deleted}


def evaluate_parallel_ost_restore_rto(
    checkpoint_size_gb: float = 500.0,
    num_osts: int = 8,
    per_ost_read_gb_s: float = 2.0,
    deserialize_sec: float = 10.0,
    distribute_sec: float = 5.0,
) -> Dict[str, float]:
    """Compute checkpoint recovery time objective (RTO) for single-OST vs multi-OST parallel read (V15 Ch. 08)."""
    serial_read_sec = checkpoint_size_gb / per_ost_read_gb_s
    serial_total_rto_sec = serial_read_sec + deserialize_sec + distribute_sec

    aggregate_parallel_gb_s = num_osts * per_ost_read_gb_s
    per_ost_shard_gb = checkpoint_size_gb / num_osts
    parallel_read_sec = checkpoint_size_gb / aggregate_parallel_gb_s
    parallel_total_rto_sec = parallel_read_sec + deserialize_sec + distribute_sec

    return {
        "checkpoint_size_gb": checkpoint_size_gb,
        "per_ost_shard_gb": round(per_ost_shard_gb, 2),
        "serial_read_sec": round(serial_read_sec, 2),
        "serial_total_rto_sec": round(serial_total_rto_sec, 2),
        "serial_total_rto_min": round(serial_total_rto_sec / 60.0, 2),
        "aggregate_parallel_gb_s": round(aggregate_parallel_gb_s, 2),
        "parallel_read_sec": round(parallel_read_sec, 2),
        "parallel_total_rto_sec": round(parallel_total_rto_sec, 2),
        "read_speedup_x": round(serial_read_sec / parallel_read_sec, 2),
    }


# ---------------------------------------------------------------------------
# 5. PyTorch DCP N -> M Resharding & Atomic Manifest Verification
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShardCopySlice:
    dst_rank: int
    src_rank: int
    global_start: int
    global_end: int
    src_local_start: int
    src_local_end: int
    dst_local_start: int
    dst_local_end: int

    @property
    def num_elements(self) -> int:
        return self.global_end - self.global_start


def plan_dcp_1d_resharding(
    global_num_elements: int,
    src_world_size: int,
    dst_world_size: int,
) -> List[ShardCopySlice]:
    """Compute an exact N -> M 1D tensor resharding plan (PyTorch DCP metadata model).

    Supports arbitrary divisible global sizes (e.g., 64 GPUs -> 48 GPUs after node
    drain in V13 Ch. 09 Scenario 3, or 4 GPUs -> 8 GPUs in V13 Lab 03).
    """
    if global_num_elements <= 0 or src_world_size <= 0 or dst_world_size <= 0:
        raise ValueError("All arguments must be positive")
    if global_num_elements % src_world_size != 0 or global_num_elements % dst_world_size != 0:
        raise ValueError("global_num_elements must be divisible by both src_world_size and dst_world_size")

    src_chunk = global_num_elements // src_world_size
    dst_chunk = global_num_elements // dst_world_size

    plan: List[ShardCopySlice] = []
    for dst_r in range(dst_world_size):
        d_start = dst_r * dst_chunk
        d_end = d_start + dst_chunk
        first_src = d_start // src_chunk
        last_src = (d_end - 1) // src_chunk
        for src_r in range(first_src, last_src + 1):
            s_start = src_r * src_chunk
            s_end = s_start + src_chunk
            g_start = max(d_start, s_start)
            g_end = min(d_end, s_end)
            if g_end > g_start:
                plan.append(
                    ShardCopySlice(
                        dst_rank=dst_r,
                        src_rank=src_r,
                        global_start=g_start,
                        global_end=g_end,
                        src_local_start=g_start - s_start,
                        src_local_end=g_end - s_start,
                        dst_local_start=g_start - d_start,
                        dst_local_end=g_end - d_start,
                    )
                )
    return plan


def execute_dcp_1d_reshard(
    src_shards: List[List[float]],
    dst_world_size: int,
) -> List[List[float]]:
    """Reshard a 1D tensor from `N = len(src_shards)` shards to `M = dst_world_size` shards."""
    src_world_size = len(src_shards)
    if src_world_size == 0:
        raise ValueError("src_shards cannot be empty")
    src_chunk = len(src_shards[0])
    global_len = src_world_size * src_chunk
    plan = plan_dcp_1d_resharding(global_len, src_world_size, dst_world_size)

    dst_chunk = global_len // dst_world_size
    dst_shards: List[List[float]] = [[0.0] * dst_chunk for _ in range(dst_world_size)]
    for sl in plan:
        dst_shards[sl.dst_rank][sl.dst_local_start : sl.dst_local_end] = src_shards[
            sl.src_rank
        ][sl.src_local_start : sl.src_local_end]
    return dst_shards


def verify_checkpoint_manifest_and_completeness(
    manifest: Dict[str, object],
    shard_payloads: Dict[str, bytes],
) -> Tuple[bool, str]:
    """Verify atomic checkpoint publication, SHA-256 shard integrity, and required state keys."""
    if not manifest.get("completed", False):
        return False, "Checkpoint manifest is marked incomplete (writer crashed before atomic commit)"

    state_keys = set(manifest.get("included_state_keys", []))
    missing_keys = [k for k in REQUIRED_CHECKPOINT_KEYS if k not in state_keys]
    if missing_keys:
        return False, f"Checkpoint missing required deterministic recovery keys: {missing_keys}"

    expected_hashes: Dict[str, str] = dict(manifest.get("shard_sha256", {}))
    if not expected_hashes:
        return False, "Checkpoint manifest contains no shard SHA-256 checksums"

    for shard_name, expected_hex in expected_hashes.items():
        if shard_name not in shard_payloads:
            return False, f"Missing shard file: {shard_name}"
        actual_hex = hashlib.sha256(shard_payloads[shard_name]).hexdigest()
        if actual_hex != expected_hex:
            return False, f"SHA-256 mismatch on {shard_name}: expected {expected_hex}, got {actual_hex}"

    return True, "VALID"


# ---------------------------------------------------------------------------
# 6. Transparent Driver-Level GPU Checkpointing (`cuda-checkpoint` + CRIU)
# ---------------------------------------------------------------------------

CUDA_CHECKPOINT_VALID_TRANSITIONS: Dict[str, Tuple[str, str]] = {
    "RUNNING": ("cuCheckpointProcessLock", "LOCKED"),
    "LOCKED_FOR_CKPT": ("cuCheckpointProcessCheckpoint", "CHECKPOINTED"),
    "CHECKPOINTED": ("cuCheckpointProcessRestore", "LOCKED_AFTER_RESTORE"),
    "LOCKED_AFTER_RESTORE": ("cuCheckpointProcessUnlock", "RUNNING"),
}


class CudaCheckpointStateMachine:
    """Deterministic state machine for NVIDIA `cuda-checkpoint` Driver API lifecycle (AISPE Ch. 5)."""

    def __init__(self, active_hbm_gb: float = 64.0, host_link_gb_s: float = 50.0) -> None:
        self.state: str = "RUNNING"
        self.active_hbm_gb: float = active_hbm_gb
        self.host_link_gb_s: float = host_link_gb_s
        self.gpu_resources_allocated: bool = True
        self.host_shadow_image_gb: float = 0.0
        self.history: List[str] = ["RUNNING"]

    def call_driver_api(self, api_name: str) -> str:
        if self.state == "RUNNING" and api_name == "cuCheckpointProcessLock":
            self.state = "LOCKED"
        elif self.state == "LOCKED" and api_name == "cuCheckpointProcessCheckpoint":
            self.state = "CHECKPOINTED"
            self.gpu_resources_allocated = False
            self.host_shadow_image_gb = self.active_hbm_gb
        elif self.state == "CHECKPOINTED" and api_name == "cuCheckpointProcessRestore":
            self.state = "LOCKED"
            self.gpu_resources_allocated = True
        elif self.state == "LOCKED" and api_name == "cuCheckpointProcessUnlock":
            self.state = "RUNNING"
        else:
            raise RuntimeError(f"Illegal cuda-checkpoint API call {api_name!r} from state {self.state!r}")
        self.history.append(f"{api_name}->{self.state}")
        return self.state

    def estimate_suspend_or_restore_sec(self) -> float:
        return round(self.active_hbm_gb / self.host_link_gb_s, 3)
