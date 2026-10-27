#!/usr/bin/env python3
"""Chapter 14.5 model: FSDP and Parameter Sharding.

Models:
1. FSDP Sharding Strategies & Mixed-Precision Memory Anatomy (ZeRO-1 / ZeRO-2 / ZeRO-3 / HSDP):
   - NO_SHARD (DDP): 16 * Psi bytes per GPU with mixed-precision AdamW (2B FP16/BF16 weights +
     2B FP16/BF16 gradients + 12B FP32 master weights, momentum, and variance), or 12 * Psi bytes
     without a separate FP32 master copy (2B weights + 2B grads + 8B FP32 momentum/variance, e.g.,
     84 GB for 7B and 840 GB for 70B).
   - ZeRO-1 (Optimizer State Sharding): 2*Psi + 2*Psi + (optimizer_bytes * Psi / N).
     For 70B (2B weights=140 GB, 2B grads=140 GB, 8B optimizer=560 GB) on N=8 GPUs:
     140 + 140 + 560/8 = 350.0 GB per GPU.
   - SHARD_GRAD_OP (ZeRO-2, Shard Gradients + Optimizer States):
     2*Psi + (2*Psi + optimizer_bytes * Psi) / N.
     With 12B/param optimizer state (16*Psi convention): 2*Psi + 14*Psi / N.
     With 8B/param optimizer state on 70B, N=8: 140 + (140 + 560)/8 = 227.5 GB (~228 GB, saving
     122.5 GB vs Stage 1).
   - FULL_SHARD (ZeRO-3, Shard Weights + Gradients + Optimizer States):
     total_state_bytes / N at rest (16*Psi / N under 16B convention; 105.0 GB for 70B on N=8,
     52.5 GB on N=16, 10.5 GB for 7B on N=8) + peak unsharded layer buffer (2 * Psi_layer bytes
     during forward AllGather, or 4 * Psi_layer during backward AllGather + ReduceScatter) +
     inflight prefetch buffers controlled by limit_all_gathers=True.
   - HYBRID_SHARD (HSDP 2D DeviceMesh (replicate_nodes, shard_gpus_per_node)):
     Shards state across S intra-node GPUs over NVLink (16*Psi / S) and replicates across R
     inter-node groups via AllReduce over InfiniBand/RoCE.
2. Collectives & Communication Volume per Step:
   - DDP (NO_SHARD): Backward AllReduce = 2 * (N - 1)/N * Psi_bytes (~2 * Psi asymptotically).
   - FSDP SHARD_GRAD_OP (or FULL_SHARD with reshard_after_forward=False):
     1 Forward AllGather + 1 Backward ReduceScatter = 2 * (N - 1)/N * Psi_bytes (~2 * Psi).
   - FSDP FULL_SHARD (reshard_after_forward=True, default ZeRO-3):
     1 Forward AllGather + 1 Backward AllGather + 1 Backward ReduceScatter =
     3 * (N - 1)/N * Psi_bytes (~3 * Psi, 1.5x DDP communication volume).
   - HSDP (R nodes x S GPUs/node):
     Intra-node NVLink volume = 3 * (S - 1)/S * Psi_bytes;
     Inter-node IB AllReduce volume on sharded gradients = 2 * (R - 1)/R * (Psi_bytes / S),
     reducing cross-node traffic by a factor of S (e.g., 8x on 8-GPU nodes).
3. Wrapping Granularity, limit_all_gathers=True Rate Limiting & Activation Memory:
   - Monolithic root wrapping (entire 70B model as 1 unit = 140 GB AllGather spike) vs
     per-TransformerBlock wrapping (80 layers -> 1.75 GB per-layer AllGather buffer).
   - limit_all_gathers=True (CPU-GPU rate limiter preventing runaway CUDA stream queuing of
     unfreed AllGather buffers, capping inflight unsharded buffers to 2 units: current + 1 prefetch).
   - Transformer activation memory estimate: L * B * S * H * bytes * k (7B: 32 * 8 * 2048 * 4096 *
     2 * 12 = 51.54 GB ~ 52 GB) and 50-80% reduction with activation checkpointing.
4. FSDP1 FlatParameter vs FSDP2 fully_shard() DTensor(Shard(0)), TorchTitan SimpleFSDP,
   Checkpointing (FULL_STATE_DICT OOM vs SHARDED_STATE_DICT / DCP), and CPUOffload vs Grace-Blackwell SuperOffload.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


FSDP_SHARDING_STRATEGIES: List[str] = [
    "NO_SHARD",
    "ZERO1_OPTIM_ONLY",
    "SHARD_GRAD_OP",
    "FULL_SHARD",
    "HYBRID_SHARD",
]


@dataclass(frozen=True)
class FsdpMemoryConfig:
    params_billion: float
    num_gpus: int
    num_layers: int
    strategy: str = "FULL_SHARD"
    include_fp32_master_weights: bool = True
    reshard_after_forward: bool = True
    wrap_granularity: str = "transformer_block"  # "transformer_block" or "monolithic_root"
    limit_all_gathers: bool = True
    queued_all_gather_units: int = 1
    hsdp_gpus_per_node: int = 8
    activation_gb: float = 0.0


def compute_fsdp_memory_breakdown(cfg: FsdpMemoryConfig) -> Dict[str, float | str | bool]:
    """Computes steady-state and peak GPU memory (GB, 10^9 bytes) across FSDP sharding strategies.

    Supports both:
    - The 16*Psi mixed-precision AdamW convention (include_fp32_master_weights=True:
      2B weights + 2B grads + 4B FP32 master copy + 4B momentum + 4B variance = 16 bytes/param,
      giving 112.0 GB for 7B).
    - The 12*Psi convention from Volume 13 Ch 4 / DAI Ch 4 (include_fp32_master_weights=False:
      2B weights + 2B grads + 4B momentum + 4B variance = 12 bytes/param,
      giving 84.0 GB for 7B and 840.0 GB for 70B).
    """
    if cfg.strategy not in FSDP_SHARDING_STRATEGIES:
        raise ValueError(f"Unsupported strategy: {cfg.strategy}")

    psi = cfg.params_billion  # in billions (10^9 parameters)
    n = cfg.num_gpus
    weight_gb = 2.0 * psi
    grad_gb = 2.0 * psi
    optim_bytes_per_param = 12.0 if cfg.include_fp32_master_weights else 8.0
    optim_gb = optim_bytes_per_param * psi
    total_unsharded_state_gb = weight_gb + grad_gb + optim_gb

    if cfg.strategy == "NO_SHARD":
        steady_weights_gb = weight_gb
        steady_grads_gb = grad_gb
        steady_optim_gb = optim_gb
        shard_degree = 1
    elif cfg.strategy == "ZERO1_OPTIM_ONLY":
        steady_weights_gb = weight_gb
        steady_grads_gb = grad_gb
        steady_optim_gb = optim_gb / n
        shard_degree = n
    elif cfg.strategy == "SHARD_GRAD_OP":
        steady_weights_gb = weight_gb
        steady_grads_gb = grad_gb / n
        steady_optim_gb = optim_gb / n
        shard_degree = n
    elif cfg.strategy == "FULL_SHARD":
        steady_weights_gb = weight_gb / n
        steady_grads_gb = grad_gb / n
        steady_optim_gb = optim_gb / n
        shard_degree = n
    else:  # HYBRID_SHARD
        s = cfg.hsdp_gpus_per_node
        steady_weights_gb = weight_gb / s
        steady_grads_gb = grad_gb / s
        steady_optim_gb = optim_gb / s
        shard_degree = s

    steady_state_gb = steady_weights_gb + steady_grads_gb + steady_optim_gb

    # Unsharded parameter buffer materialized during AllGather
    layer_weight_gb = weight_gb / cfg.num_layers
    if cfg.strategy in ("NO_SHARD", "ZERO1_OPTIM_ONLY"):
        transient_buffer_gb = 0.0
    elif cfg.wrap_granularity == "monolithic_root":
        transient_buffer_gb = weight_gb
    else:
        inflight_units = 2 if cfg.limit_all_gathers else max(2, 1 + cfg.queued_all_gather_units)
        # Backward requires unsharded weights (AllGather) + full layer gradient before ReduceScatter
        if not cfg.reshard_after_forward and cfg.strategy == "FULL_SHARD":
            transient_buffer_gb = weight_gb + layer_weight_gb
        else:
            transient_buffer_gb = inflight_units * layer_weight_gb

    peak_memory_gb = steady_state_gb + transient_buffer_gb + cfg.activation_gb
    return {
        "strategy": cfg.strategy,
        "params_billion": psi,
        "num_gpus": n,
        "shard_degree": shard_degree,
        "bytes_per_param_total": 4.0 + optim_bytes_per_param,
        "total_unsharded_state_gb": round(total_unsharded_state_gb, 4),
        "steady_weights_gb": round(steady_weights_gb, 4),
        "steady_grads_gb": round(steady_grads_gb, 4),
        "steady_optim_gb": round(steady_optim_gb, 4),
        "steady_state_gb": round(steady_state_gb, 4),
        "layer_weight_gb": round(layer_weight_gb, 4),
        "transient_buffer_gb": round(transient_buffer_gb, 4),
        "peak_memory_gb": round(peak_memory_gb, 4),
        "limit_all_gathers": cfg.limit_all_gathers,
    }


def compute_communication_volume(
    params_billion: float,
    num_gpus: int,
    strategy: str = "FULL_SHARD",
    reshard_after_forward: bool = True,
    bytes_per_param: float = 2.0,
    hsdp_gpus_per_node: int = 8,
) -> Dict[str, float | int | str]:
    """Calculates per-step collective communication volume per GPU (GB, 10^9 bytes).

    - DDP (NO_SHARD): 1 AllReduce = 2 * (N-1)/N * M_weights (~2 * Psi).
    - SHARD_GRAD_OP (ZeRO-2) or FULL_SHARD with reshard_after_forward=False:
      1 Fwd AllGather + 1 Bwd ReduceScatter = 2 * (N-1)/N * M_weights (~2 * Psi).
    - FULL_SHARD (ZeRO-3, reshard_after_forward=True):
      1 Fwd AllGather + 1 Bwd AllGather + 1 Bwd ReduceScatter = 3 * (N-1)/N * M_weights (~3 * Psi).
    - HYBRID_SHARD (HSDP on R nodes x S GPUs/node):
      Intra-node NVLink volume = 3 * (S-1)/S * M_weights (when reshard_after_forward=True);
      Inter-node IB AllReduce on sharded gradients = 2 * (R-1)/R * (M_weights / S).
    """
    model_bytes_gb = params_billion * bytes_per_param
    n = num_gpus

    if strategy == "NO_SHARD":
        ring_factor = (n - 1) / n
        asymptotic_multiplier = 2.0
        exact_gb = 2.0 * ring_factor * model_bytes_gb
        return {
            "strategy": strategy,
            "model_bytes_gb": round(model_bytes_gb, 4),
            "asymptotic_multiplier_psi": asymptotic_multiplier,
            "asymptotic_volume_gb": round(asymptotic_multiplier * model_bytes_gb, 4),
            "exact_ring_volume_gb": round(exact_gb, 4),
            "inter_node_volume_gb": round(exact_gb, 4),
            "collectives": "1x Backward AllReduce (2 * (N-1)/N * M)",
        }

    if strategy == "SHARD_GRAD_OP" or (strategy == "FULL_SHARD" and not reshard_after_forward):
        ring_factor = (n - 1) / n
        asymptotic_multiplier = 2.0
        exact_gb = 2.0 * ring_factor * model_bytes_gb
        return {
            "strategy": strategy,
            "model_bytes_gb": round(model_bytes_gb, 4),
            "asymptotic_multiplier_psi": asymptotic_multiplier,
            "asymptotic_volume_gb": round(asymptotic_multiplier * model_bytes_gb, 4),
            "exact_ring_volume_gb": round(exact_gb, 4),
            "inter_node_volume_gb": round(exact_gb, 4),
            "collectives": "1x Fwd AllGather + 1x Bwd ReduceScatter (2 * (N-1)/N * M)",
        }

    if strategy == "FULL_SHARD":
        ring_factor = (n - 1) / n
        asymptotic_multiplier = 3.0
        exact_gb = 3.0 * ring_factor * model_bytes_gb
        return {
            "strategy": strategy,
            "model_bytes_gb": round(model_bytes_gb, 4),
            "asymptotic_multiplier_psi": asymptotic_multiplier,
            "asymptotic_volume_gb": round(asymptotic_multiplier * model_bytes_gb, 4),
            "exact_ring_volume_gb": round(exact_gb, 4),
            "inter_node_volume_gb": round(exact_gb, 4),
            "collectives": "1x Fwd AllGather + 1x Bwd AllGather + 1x Bwd ReduceScatter (3 * (N-1)/N * M)",
        }

    if strategy == "HYBRID_SHARD":
        s = hsdp_gpus_per_node
        r = n // s
        mult = 3.0 if reshard_after_forward else 2.0
        intra_node_gb = mult * ((s - 1) / s) * model_bytes_gb
        inter_node_gb = 2.0 * ((r - 1) / r) * (model_bytes_gb / s) if r > 1 else 0.0
        full_shard_inter_gb = mult * ((n - 1) / n) * model_bytes_gb
        return {
            "strategy": strategy,
            "num_nodes_replica_group": r,
            "gpus_per_node_shard_group": s,
            "model_bytes_gb": round(model_bytes_gb, 4),
            "asymptotic_multiplier_psi": mult,
            "intra_node_nvlink_gb": round(intra_node_gb, 4),
            "inter_node_ib_gb": round(inter_node_gb, 4),
            "full_shard_equivalent_gb": round(full_shard_inter_gb, 4),
            "inter_node_reduction_factor": round(full_shard_inter_gb / inter_node_gb, 2) if inter_node_gb > 0 else 0.0,
        }

    raise ValueError(f"Unsupported strategy: {strategy}")


def estimate_transformer_activation_memory_gb(
    num_layers: int,
    batch_size: int,
    seq_len: int,
    hidden_dim: int,
    bytes_per_elem: int = 2,
    k_factor: int = 12,
    checkpoint_reduction_fraction: float = 0.0,
) -> Dict[str, float]:
    """Estimates per-GPU Transformer activation memory: L * B * S * H * bytes * k."""
    raw_bytes = (
        num_layers
        * batch_size
        * seq_len
        * hidden_dim
        * bytes_per_elem
        * k_factor
    )
    raw_gb = raw_bytes / 1e9
    effective_gb = raw_gb * (1.0 - checkpoint_reduction_fraction)
    return {
        "raw_activation_gb": round(raw_gb, 2),
        "effective_activation_gb": round(effective_gb, 2),
        "saved_gb": round(raw_gb - effective_gb, 2),
    }


def evaluate_checkpoint_and_offload(
    params_billion: float,
    num_gpus: int,
    state_dict_type: str = "SHARDED_STATE_DICT",
    gpu_vram_gb: float = 80.0,
    cpu_offload_enabled: bool = False,
    interconnect: str = "PCIe_Gen4",
) -> Dict[str, float | str | bool]:
    """Evaluates FULL_STATE_DICT rank-0 OOM vs SHARDED_STATE_DICT/DCP and CPUOffload vs SuperOffload."""
    fp32_model_gb = params_billion * 4.0
    fp16_model_gb = params_billion * 2.0
    if state_dict_type == "FULL_STATE_DICT":
        rank0_ckpt_gb = fp32_model_gb
        ckpt_oom = rank0_ckpt_gb > gpu_vram_gb
    else:
        rank0_ckpt_gb = fp16_model_gb / num_gpus
        ckpt_oom = False

    # PCIe Gen4 (32 GB/s) vs HBM3 (3000 GB/s = 3 TB/s, ~100x faster) vs NVLink-C2C (900 GB/s)
    if not cpu_offload_enabled:
        step_time_s = 12.3
        tokens_per_sec = 10.4
        gpu_util_pct = 88.0
    elif interconnect == "PCIe_Gen4":
        step_time_s = 48.7
        tokens_per_sec = 2.6
        gpu_util_pct = 18.0
    else:  # Grace_Blackwell_NVLink_C2C SuperOffload + GraceAdam
        step_time_s = 13.5
        tokens_per_sec = 9.5
        gpu_util_pct = 82.0

    return {
        "state_dict_type": state_dict_type,
        "rank0_ckpt_gb": round(rank0_ckpt_gb, 4),
        "ckpt_oom_on_rank0": ckpt_oom,
        "step_time_s": step_time_s,
        "tokens_per_sec": tokens_per_sec,
        "gpu_util_pct": gpu_util_pct,
        "slowdown_factor": round(step_time_s / 12.3, 2),
    }


def simulate_manual_parameter_sharding(
    param_shapes: List[tuple[int, int]],
    world_size: int,
) -> Dict[str, object]:
    """Models FSDP1 FlatParameter vs FSDP2 per-parameter DTensor(Shard(0)) sharding."""
    total_numel = sum(r * c for r, c in param_shapes)
    flat_shard_numel = total_numel // world_size
    dtensor_local_shapes = [(r // world_size, c) for r, c in param_shapes]
    dtensor_shard_numel = sum(r * c for r, c in dtensor_local_shapes)
    reconstructed_numel = dtensor_shard_numel * world_size
    return {
        "total_numel": total_numel,
        "world_size": world_size,
        "fsdp1_flat_shard_numel": flat_shard_numel,
        "fsdp2_dtensor_local_shapes": dtensor_local_shapes,
        "fsdp2_dtensor_shard_numel": dtensor_shard_numel,
        "reconstructed_numel": reconstructed_numel,
        "lossless_reconstruction": reconstructed_numel == total_numel,
    }


if __name__ == "__main__":
    c70_ddp = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 8, 80, strategy="NO_SHARD", include_fp32_master_weights=False)
    )
    c70_fsdp = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 8, 80, strategy="FULL_SHARD", include_fp32_master_weights=False)
    )
    print(f"70B DDP per GPU: {c70_ddp['steady_state_gb']} GB | FSDP N=8: {c70_fsdp['steady_state_gb']} GB")
