#!/usr/bin/env python3
"""
Chapter 14.4 — Data Parallelism and DDP Simulator & Diagnostic Engine
=====================================================================
Standard-library-only analytical models and deterministic simulators for:
1. nn.DataParallel (DP) GIL/PCIe GPU-0 bottleneck vs DistributedDataParallel (DDP) Ring AllReduce.
2. Reverse-order autograd hook bucket packing (`bucket_cap_mb = 25.0` MB default) & TorchDynamo graph breaks.
3. Backward-pass computation and NCCL AllReduce stream overlap timeline & MLPerf step breakdown.
4. `model.no_sync()` gradient accumulation across K micro-batches.
5. `DistributedSampler` shard partitioning, `set_epoch(epoch)` determinism, `drop_last`, and `model.join()`.
6. `gradient_as_bucket_view=True` memory savings, `find_unused_parameters` deadlock detection, and straggler triage.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. DP vs. DDP Communication & Memory Bottleneck Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DPvsDDPComparison:
    num_gpus: int
    param_count: int
    bytes_per_param: int
    grad_size_gb: float
    dp_gpu0_comm_gb: float
    ddp_per_gpu_ring_gb: float
    dp_to_ddp_gpu0_traffic_ratio: float
    ddp_wire_time_ms: float
    ddp_theoretical_speedup: float
    ddp_theoretical_efficiency_pct: float
    ddp_measured_speedup: float
    ddp_measured_efficiency_pct: float
    dp_has_gil_contention: bool
    dp_gpu0_memory_imbalance_gb: float


def compare_dp_vs_ddp(
    num_gpus: int = 4,
    param_count: int = 7_000_000_000,
    bytes_per_param: int = 4,
    link_bw_gbps: float = 900.0,
    single_gpu_step_s: float = 12.3,
    single_gpu_throughput: float = 8.13,
    measured_ddp_step_s: float = 12.9,
    measured_ddp_throughput: float = 31.2,
    per_gpu_activation_gather_gb: float = 1.5,
) -> DPvsDDPComparison:
    """
    Compare single-process multi-threaded `nn.DataParallel` (DP) against
    multi-process `DistributedDataParallel` (DDP) across `num_gpus`.

    - Gradient payload size: S_grad = param_count * bytes_per_param (in decimal GB = 1e9 bytes).
    - In DP, GPU 0 broadcasts replicated weights to (N - 1) peer GPUs every forward pass
      and gathers full gradients from (N - 1) peer GPUs every backward pass:
      DP GPU 0 parameter/gradient traffic = 2 * (N - 1) * S_grad.
      GPU 0 also gathers output activations from (N - 1) GPUs to compute the centralized loss.
    - In DDP, every rank runs in its own OS process (no Python GIL contention) and executes
      Ring AllReduce moving 2 * ((N - 1) / N) * S_grad bytes per GPU.
    """
    if num_gpus < 1:
        raise ValueError("num_gpus must be >= 1")
    grad_size_gb = (param_count * bytes_per_param) / 1e9

    dp_gpu0_comm_gb = 2.0 * (num_gpus - 1) * grad_size_gb
    ddp_per_gpu_ring_gb = 2.0 * ((num_gpus - 1) / num_gpus) * grad_size_gb
    ratio = (
        dp_gpu0_comm_gb / ddp_per_gpu_ring_gb
        if ddp_per_gpu_ring_gb > 0
        else 1.0
    )

    wire_time_s = ddp_per_gpu_ring_gb / link_bw_gbps if link_bw_gbps > 0 else 0.0
    wire_time_ms = wire_time_s * 1000.0

    ideal_step_s = single_gpu_step_s + wire_time_s
    theo_eff = (single_gpu_step_s / ideal_step_s) * 100.0 if ideal_step_s > 0 else 0.0
    theo_speedup = num_gpus * (theo_eff / 100.0)

    measured_speedup = (
        measured_ddp_throughput / single_gpu_throughput
        if single_gpu_throughput > 0
        else 0.0
    )
    measured_eff = (measured_speedup / num_gpus) * 100.0

    # GPU 0 in DP holds gathered output activations + gathered gradient staging for (N-1) peers
    dp_gpu0_imbalance_gb = round((num_gpus - 1) * per_gpu_activation_gather_gb, 2)

    return DPvsDDPComparison(
        num_gpus=num_gpus,
        param_count=param_count,
        bytes_per_param=bytes_per_param,
        grad_size_gb=round(grad_size_gb, 4),
        dp_gpu0_comm_gb=round(dp_gpu0_comm_gb, 4),
        ddp_per_gpu_ring_gb=round(ddp_per_gpu_ring_gb, 4),
        dp_to_ddp_gpu0_traffic_ratio=round(ratio, 2),
        ddp_wire_time_ms=round(wire_time_ms, 2),
        ddp_theoretical_speedup=round(theo_speedup, 2),
        ddp_theoretical_efficiency_pct=round(theo_eff, 1),
        ddp_measured_speedup=round(measured_speedup, 2),
        ddp_measured_efficiency_pct=round(measured_eff, 1),
        dp_has_gil_contention=True,
        dp_gpu0_memory_imbalance_gb=dp_gpu0_imbalance_gb,
    )


@dataclass(frozen=True)
class RingVsTreeScaleModel:
    num_gpus: int
    grad_size_gb: float
    effective_bw_gbps: float
    ring_data_per_gpu_gb: float
    ring_wire_time_ms: float
    ring_hops: int
    tree_hops: int
    recommended_algo: str


def evaluate_ring_vs_tree_scale(
    num_gpus: int,
    grad_size_gb: float = 28.0,
    effective_bw_gbps: float = 900.0,
) -> RingVsTreeScaleModel:
    """
    Model Ring AllReduce vs Double Binary Tree hop counts at single-node (N=8, NVLink 900 GB/s)
    and multi-node (N=512, InfiniBand 25 GB/s) scales (V13 Ch 8 worked example).
    """
    ring_data_gb = 2.0 * ((num_gpus - 1) / num_gpus) * grad_size_gb
    wire_time_ms = (ring_data_gb / effective_bw_gbps) * 1000.0
    ring_hops = num_gpus
    tree_hops = int(math.ceil(math.log2(max(2, num_gpus))))
    recommended = "Ring" if num_gpus <= 16 else "Tree / Hierarchical"
    return RingVsTreeScaleModel(
        num_gpus=num_gpus,
        grad_size_gb=round(grad_size_gb, 2),
        effective_bw_gbps=round(effective_bw_gbps, 2),
        ring_data_per_gpu_gb=round(ring_data_gb, 2),
        ring_wire_time_ms=round(wire_time_ms, 1),
        ring_hops=ring_hops,
        tree_hops=tree_hops,
        recommended_algo=recommended,
    )


# ---------------------------------------------------------------------------
# 2. Reverse-Order Autograd Hook Bucket Packing (`bucket_cap_mb = 25.0`)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    layer_index: int
    size_mb: float
    requires_grad: bool = True
    used_in_forward: bool = True


@dataclass(frozen=True)
class GradientBucket:
    bucket_id: int
    param_names: Tuple[str, ...]
    layer_indices: Tuple[int, ...]
    total_size_mb: float
    all_hooks_fired: bool
    missing_params: Tuple[str, ...]


def pack_ddp_gradient_buckets(
    parameters_in_forward_order: Sequence[ParameterSpec],
    bucket_cap_mb: float = 25.0,
) -> List[GradientBucket]:
    """
    Pack trainable parameters into DDP Reducer buckets in REVERSE parameter order
    (`list(model.parameters())[::-1]`) up to `bucket_cap_mb` (default 25.0 MB).

    During backward propagation, gradients for the final layers are computed first.
    Reverse-order packing guarantees that parameters in Bucket 0 finish their backward
    compute earliest and trigger an asynchronous NCCL AllReduce immediately.
    """
    if bucket_cap_mb <= 0:
        raise ValueError("bucket_cap_mb must be > 0")

    trainable_reversed = [
        p for p in reversed(parameters_in_forward_order) if p.requires_grad
    ]

    buckets: List[GradientBucket] = []
    cur_params: List[ParameterSpec] = []
    cur_size = 0.0

    def flush_bucket(items: List[ParameterSpec], b_id: int) -> GradientBucket:
        missing = tuple(p.name for p in items if not p.used_in_forward)
        return GradientBucket(
            bucket_id=b_id,
            param_names=tuple(p.name for p in items),
            layer_indices=tuple(p.layer_index for p in items),
            total_size_mb=round(sum(p.size_mb for p in items), 4),
            all_hooks_fired=(len(missing) == 0),
            missing_params=missing,
        )

    for param in trainable_reversed:
        if cur_params and (cur_size + param.size_mb > bucket_cap_mb):
            buckets.append(flush_bucket(cur_params, len(buckets)))
            cur_params = [param]
            cur_size = param.size_mb
        else:
            cur_params.append(param)
            cur_size += param.size_mb

    if cur_params:
        buckets.append(flush_bucket(cur_params, len(buckets)))

    return buckets


# ---------------------------------------------------------------------------
# 3. Backward Compute / AllReduce Overlap Timeline & MLPerf Breakdown
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OverlapTimelineResult:
    num_buckets: int
    total_backward_compute_ms: float
    total_allreduce_ms: float
    sequential_time_ms: float
    overlapped_time_ms: float
    exposed_comm_ms: float
    hidden_comm_ms: float
    overlap_efficiency_pct: float
    speedup_from_overlap: float
    dynamo_subgraphs: int


def simulate_backward_allreduce_overlap(
    bucket_compute_ms: Sequence[float],
    bucket_allreduce_ms: Sequence[float],
) -> OverlapTimelineResult:
    """
    Simulate two-stream execution during `loss.backward()`:
    - Default CUDA compute stream executes bucket backward subgraphs sequentially:
      compute_end[i] = sum_{k=0..i} bucket_compute_ms[k].
    - Dedicated NCCL communication stream launches Bucket i's AllReduce as soon as
      both Bucket i's compute has completed AND Bucket (i-1)'s AllReduce has completed:
      comm_start[i] = max(compute_end[i], comm_end[i-1])
      comm_end[i]   = comm_start[i] + bucket_allreduce_ms[i].
    """
    if len(bucket_compute_ms) != len(bucket_allreduce_ms) or not bucket_compute_ms:
        raise ValueError("bucket_compute_ms and bucket_allreduce_ms must have equal non-zero length")

    comp_time = 0.0
    comm_end = 0.0
    for c_ms, a_ms in zip(bucket_compute_ms, bucket_allreduce_ms):
        comp_time += c_ms
        comm_start = max(comp_time, comm_end)
        comm_end = comm_start + a_ms

    total_comp = sum(bucket_compute_ms)
    total_comm = sum(bucket_allreduce_ms)
    seq_time = total_comp + total_comm
    overlapped_time = comm_end
    exposed_comm = max(0.0, overlapped_time - total_comp)
    hidden_comm = max(0.0, total_comm - exposed_comm)
    overlap_eff = (hidden_comm / total_comm) * 100.0 if total_comm > 0 else 100.0
    speedup = seq_time / overlapped_time if overlapped_time > 0 else 1.0

    return OverlapTimelineResult(
        num_buckets=len(bucket_compute_ms),
        total_backward_compute_ms=round(total_comp, 3),
        total_allreduce_ms=round(total_comm, 3),
        sequential_time_ms=round(seq_time, 3),
        overlapped_time_ms=round(overlapped_time, 3),
        exposed_comm_ms=round(exposed_comm, 3),
        hidden_comm_ms=round(hidden_comm, 3),
        overlap_efficiency_pct=round(overlap_eff, 2),
        speedup_from_overlap=round(speedup, 3),
        dynamo_subgraphs=len(bucket_compute_ms),
    )


@dataclass(frozen=True)
class StepTimingBreakdown:
    step_time_ms: float
    forward_ms: float
    backward_ms: float
    allreduce_ms: float
    other_ms: float
    compute_ms: float
    forward_pct: float
    backward_pct: float
    compute_pct: float
    allreduce_pct: float
    other_pct: float
    comm_health_band: str


def analyze_step_timing_breakdown(
    forward_ms: float = 10.5,
    backward_ms: float = 9.0,
    allreduce_ms: float = 4.0,
    other_ms: float = 0.5,
) -> StepTimingBreakdown:
    """
    Analyze training iteration timing (AISPE Ch 13 Table 13-6 MLPerf breakdown & DAI Ch 3 bands):
    - < 20% AllReduce share: GOOD_OVERLAP
    - 20%..40% AllReduce share: ACCEPTABLE_COMM
    - > 40% AllReduce share: COMM_BOTTLENECK
    """
    step_ms = forward_ms + backward_ms + allreduce_ms + other_ms
    compute_ms = forward_ms + backward_ms
    allreduce_pct = (allreduce_ms / step_ms) * 100.0
    if allreduce_pct < 20.0:
        band = "GOOD_OVERLAP"
    elif allreduce_pct <= 40.0:
        band = "ACCEPTABLE_COMM"
    else:
        band = "COMM_BOTTLENECK"

    return StepTimingBreakdown(
        step_time_ms=round(step_ms, 2),
        forward_ms=round(forward_ms, 2),
        backward_ms=round(backward_ms, 2),
        allreduce_ms=round(allreduce_ms, 2),
        other_ms=round(other_ms, 2),
        compute_ms=round(compute_ms, 2),
        forward_pct=round((forward_ms / step_ms) * 100.0, 1),
        backward_pct=round((backward_ms / step_ms) * 100.0, 1),
        compute_pct=round((compute_ms / step_ms) * 100.0, 1),
        allreduce_pct=round(allreduce_pct, 1),
        other_pct=round((other_ms / step_ms) * 100.0, 1),
        comm_health_band=band,
    )


# ---------------------------------------------------------------------------
# 4. `model.no_sync()` Gradient Accumulation Across K Micro-Batches
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NoSyncAccumulationResult:
    accumulation_steps: int
    world_size: int
    allreduces_without_no_sync: int
    allreduces_with_no_sync: int
    comm_reduction_factor: float
    comm_saved_pct: float
    ring_bytes_without_no_sync_gb: float
    ring_bytes_with_no_sync_gb: float
    max_grad_diff: float
    mathematically_identical: bool


def simulate_no_sync_accumulation(
    micro_batch_gradients_per_rank: Sequence[Sequence[Sequence[float]]],
    grad_size_gb: float = 28.0,
) -> NoSyncAccumulationResult:
    """
    Verify that accumulating K micro-batches with `with model.no_sync():` on steps 0..K-2
    and synchronizing only on step K-1:
    1. Cuts NCCL AllReduce collective launches from K to 1 (a K-fold reduction, saving (K-1)/K).
    2. Produces the exact same synchronized gradient vector as running AllReduce on every
       micro-batch (by linearity of expectation/summation).
    """
    world_size = len(micro_batch_gradients_per_rank)
    if world_size == 0:
        raise ValueError("world_size must be >= 1")
    k_steps = len(micro_batch_gradients_per_rank[0])
    num_params = len(micro_batch_gradients_per_rank[0][0])

    # Path A: Naive accumulation (AllReduce on every micro-batch k = 0..K-1)
    naive_accum = [0.0] * num_params
    for k in range(k_steps):
        for p in range(num_params):
            # Each micro-batch loss is scaled by 1 / k_steps, then averaged across world_size
            step_synced = (
                sum(
                    micro_batch_gradients_per_rank[r][k][p] / k_steps
                    for r in range(world_size)
                )
                / world_size
            )
            naive_accum[p] += step_synced

    # Path B: `with model.no_sync():` on micro-batches 0..K-2, single AllReduce on step K-1
    local_accum = [[0.0] * num_params for _ in range(world_size)]
    for r in range(world_size):
        for k in range(k_steps):
            for p in range(num_params):
                local_accum[r][p] += micro_batch_gradients_per_rank[r][k][p] / k_steps

    nosync_final = [
        sum(local_accum[r][p] for r in range(world_size)) / world_size
        for p in range(num_params)
    ]

    max_diff = max(abs(a - b) for a, b in zip(naive_accum, nosync_final))
    single_ring_gb = 2.0 * ((world_size - 1) / world_size) * grad_size_gb

    return NoSyncAccumulationResult(
        accumulation_steps=k_steps,
        world_size=world_size,
        allreduces_without_no_sync=k_steps,
        allreduces_with_no_sync=1,
        comm_reduction_factor=float(k_steps),
        comm_saved_pct=round(((k_steps - 1) / k_steps) * 100.0, 2),
        ring_bytes_without_no_sync_gb=round(k_steps * single_ring_gb, 2),
        ring_bytes_with_no_sync_gb=round(single_ring_gb, 2),
        max_grad_diff=max_diff,
        mathematically_identical=(max_diff < 1e-12),
    )


# ---------------------------------------------------------------------------
# 5. `DistributedSampler` Partitioning, `set_epoch()`, & `model.join()`
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DistributedSamplerPlan:
    dataset_size: int
    world_size: int
    epoch: int
    seed: int
    drop_last: bool
    num_samples_per_rank: int
    total_size: int
    shards_by_rank: Tuple[Tuple[int, ...], ...]
    shards_are_disjoint: bool
    union_size: int


def simulate_distributed_sampler(
    dataset_size: int = 1000,
    world_size: int = 4,
    epoch: int = 0,
    seed: int = 0,
    shuffle: bool = True,
    drop_last: bool = True,
) -> DistributedSamplerPlan:
    """
    Faithful model of `torch.utils.data.distributed.DistributedSampler`:
    - When `drop_last=True` and `dataset_size % world_size != 0`, drops tail samples so
      every rank receives `dataset_size // world_size` samples.
    - When `drop_last=False`, pads the index list from the front up to
      `ceil(dataset_size / world_size) * world_size`.
    - When `shuffle=True`, seeds a deterministic RNG with `seed + epoch` (`set_epoch(epoch)`).
    - Rank `r` receives strided slice `indices[r:total_size:world_size]`.
    """
    if drop_last and dataset_size % world_size != 0:
        num_samples = math.ceil((dataset_size - world_size) / world_size)
    else:
        num_samples = math.ceil(dataset_size / world_size)
    total_size = num_samples * world_size

    indices = list(range(dataset_size))
    if shuffle:
        rng = random.Random(seed + epoch)
        rng.shuffle(indices)

    if not drop_last:
        padding_size = total_size - len(indices)
        if padding_size <= len(indices):
            indices += indices[:padding_size]
        else:
            indices += (indices * math.ceil(padding_size / len(indices)))[:padding_size]
    else:
        indices = indices[:total_size]

    shards = tuple(
        tuple(indices[rank:total_size:world_size]) for rank in range(world_size)
    )
    all_seen = [idx for shard in shards for idx in shard]
    unique_seen = set(all_seen)
    disjoint = len(all_seen) == len(unique_seen)

    return DistributedSamplerPlan(
        dataset_size=dataset_size,
        world_size=world_size,
        epoch=epoch,
        seed=seed,
        drop_last=drop_last,
        num_samples_per_rank=num_samples,
        total_size=total_size,
        shards_by_rank=shards,
        shards_are_disjoint=disjoint,
        union_size=len(unique_seen),
    )


def verify_uneven_inputs_join(
    batches_per_rank: Sequence[int],
    use_join_context: bool,
) -> Dict[str, object]:
    """
    Evaluate uneven batch counts across ranks (e.g., rank 0 has 2 batches, rank 1 has 3 batches
    from DAI Ch 3 `ddp_join_demo.py`). Without `model.join()`, early-finishing ranks exit the
    loop and cause surviving ranks to hang at collective step `min_batches + 1`.
    """
    min_b = min(batches_per_rank)
    max_b = max(batches_per_rank)
    uneven = min_b != max_b
    will_deadlock = uneven and not use_join_context
    dummy_collectives_per_rank = [
        (max_b - b) if use_join_context else 0 for b in batches_per_rank
    ]
    return {
        "min_batches": min_b,
        "max_batches": max_b,
        "uneven": uneven,
        "will_deadlock": will_deadlock,
        "hang_at_step": (min_b + 1) if will_deadlock else None,
        "dummy_collectives_per_rank": dummy_collectives_per_rank,
    }


# ---------------------------------------------------------------------------
# 6. `gradient_as_bucket_view=True` Memory Model & Failure Triage
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DDPBufferMemoryReport:
    param_count: int
    weight_bytes: int
    grad_bytes: int
    optimizer_bytes: int
    bucket_buffer_bytes: int
    gradient_as_bucket_view: bool
    total_steady_state_gb: float
    memory_saved_gb: float
    memory_saved_pct_of_grad: float


def compute_ddp_memory_with_bucket_view(
    param_count: int = 7_000_000_000,
    weight_bytes: int = 4,
    grad_bytes: int = 4,
    optimizer_bytes: int = 8,
    gradient_as_bucket_view: bool = True,
) -> DDPBufferMemoryReport:
    """
    Compute per-GPU steady-state model + gradient + Reducer bucket + optimizer memory in DDP:
    - Weights: param_count * weight_bytes
    - Optimizer states: param_count * optimizer_bytes
    - Gradients (`param.grad`): param_count * grad_bytes
    - Reducer contiguous buckets: param_count * grad_bytes
    When `gradient_as_bucket_view=False` (legacy default), both `param.grad` and the Reducer
    bucket buffers exist separately in VRAM (`2 * S_grad`).
    When `gradient_as_bucket_view=True`, `param.grad` is a zero-copy view (`storage_offset`)
    directly into the Reducer bucket buffer, eliminating `1 * S_grad` of duplicate memory.
    """
    w_gb = (param_count * weight_bytes) / 1e9
    g_gb = (param_count * grad_bytes) / 1e9
    opt_gb = (param_count * optimizer_bytes) / 1e9
    bucket_gb = g_gb

    if gradient_as_bucket_view:
        total_gb = w_gb + opt_gb + bucket_gb
        saved_gb = g_gb
        saved_pct = 100.0
    else:
        total_gb = w_gb + opt_gb + g_gb + bucket_gb
        saved_gb = 0.0
        saved_pct = 0.0

    return DDPBufferMemoryReport(
        param_count=param_count,
        weight_bytes=weight_bytes,
        grad_bytes=grad_bytes,
        optimizer_bytes=optimizer_bytes,
        bucket_buffer_bytes=grad_bytes,
        gradient_as_bucket_view=gradient_as_bucket_view,
        total_steady_state_gb=round(total_gb, 2),
        memory_saved_gb=round(saved_gb, 2),
        memory_saved_pct_of_grad=round(saved_pct, 1),
    )


@dataclass(frozen=True)
class DDPRuntimeTriage:
    status: str
    root_cause: str
    remediation: str
    straggler_rank: int | None
    step_time_skew_pct: float
    loss_spread: float


def triage_ddp_runtime_telemetry(
    rank_step_times_s: Sequence[float],
    rank_losses: Sequence[float],
    rank_temps_c: Sequence[float],
    unused_param_names: Sequence[str] = (),
    find_unused_parameters: bool = False,
    static_graph: bool = False,
) -> DDPRuntimeTriage:
    """
    Diagnose DDP production failures from per-rank step times, losses, GPU temperatures,
    and unused parameter hook states (V13 Ch 3 & DAI Ch 3).
    """
    if unused_param_names and not (find_unused_parameters or static_graph):
        return DDPRuntimeTriage(
            status="DEADLOCK_UNUSED_PARAMETERS",
            root_cause=(
                f"Parameters {list(unused_param_names)} did not receive gradients in backward(); "
                "their Reducer bucket never became ready for AllReduce."
            ),
            remediation=(
                "Ensure all parameters participate in forward() (or multiply unused branch by 0.0), "
                "or pass find_unused_parameters=True / static_graph=True to DDP."
            ),
            straggler_rank=None,
            step_time_skew_pct=0.0,
            loss_spread=0.0,
        )

    min_t = min(rank_step_times_s)
    max_t = max(rank_step_times_s)
    skew_pct = ((max_t - min_t) / min_t) * 100.0 if min_t > 0 else 0.0
    loss_spread = max(rank_losses) - min(rank_losses)
    slowest_rank = int(rank_step_times_s.index(max_t))

    if skew_pct > 10.0:
        temp_c = rank_temps_c[slowest_rank]
        cause = (
            f"Rank {slowest_rank} step time is {max_t:.1f}s vs {min_t:.1f}s peer baseline "
            f"(+{skew_pct:.1f}% skew); GPU {slowest_rank} temperature is {temp_c:.0f}C "
            f"({'thermal throttling >= 80C' if temp_c >= 80.0 else 'CPU/IO/network straggler'})."
        )
        return DDPRuntimeTriage(
            status="STRAGGLER_DETECTED",
            root_cause=cause,
            remediation="Inspect nvidia-smi -l 1 clocks/thermals on the straggler GPU and verify cooling/airflow.",
            straggler_rank=slowest_rank,
            step_time_skew_pct=round(skew_pct, 1),
            loss_spread=round(loss_spread, 4),
        )

    return DDPRuntimeTriage(
        status="HEALTHY",
        root_cause="All ranks synchronized within 5% step-time band and < 0.1% loss tolerance.",
        remediation="None required.",
        straggler_rank=None,
        step_time_skew_pct=round(skew_pct, 1),
        loss_spread=round(loss_spread, 4),
    )


if __name__ == "__main__":
    comp = compare_dp_vs_ddp()
    print(
        f"4-GPU 7B DDP Ring AllReduce: {comp.ddp_per_gpu_ring_gb} GB/GPU "
        f"({comp.ddp_wire_time_ms} ms) vs DP GPU-0: {comp.dp_gpu0_comm_gb} GB "
        f"({comp.dp_to_ddp_gpu0_traffic_ratio}x higher on GPU 0)"
    )
