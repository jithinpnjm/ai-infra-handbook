#!/usr/bin/env python3
"""Chapter 14.7 model: Tensor, Pipeline, and Expert Parallelism; Megatron.

Models:
1. State Sharding vs. Computation Sharding & Megatron Distributed Optimizer Memory:
   - State sharding (FSDP2 / ZeRO-3) partitions storage (parameters, gradients, optimizer states)
     across N GPUs, but reconstructs full layer weights (e.g., 16384 x 16384 or 12288 x 49152 =
     603,979,776 params ~ 1.2 GB in FP16/BF16) on every GPU during compute.
   - Computation sharding (Megatron TP, PP, SP, CP, EP) partitions the forward/backward mathematical
     graph itself across devices.
   - Megatron Distributed Optimizer memory per parameter across d data-parallel GPUs:
     * fp16 params, fp16 grads: 20 bytes/param unsharded -> (4 + 16 / d) bytes/param sharded
     * bf16 params, fp32 grads: 18 bytes/param unsharded -> (6 + 12 / d) bytes/param sharded
       (e.g., for d = 8 GPUs: 6 + 12/8 = 7.5 bytes/param, a 2.4x reduction from 18 bytes/param)
     * fp32 params, fp32 grads: 16 bytes/param unsharded -> (8 + 8 / d) bytes/param sharded
2. Tensor Parallelism (TP), ColumnParallelLinear / RowParallelLinear, and Sequence Parallelism (SP):
   - MLP block pairs ColumnParallelLinear (W split column-wise [W_0 | ... | W_{TP-1}], GeLU applied
     independently with 0 communication) + RowParallelLinear (W' split row-wise, 1 AllReduce at the
     end of the block).
   - MHA block splits Q, K, V projections column-wise across attention heads and the output projection
     row-wise (1 AllReduce at the end of attention).
   - Total per Transformer layer: 2 AllReduces in forward + 2 AllReduces in backward = 4 AllReduces/layer.
   - Cross-node TP failure (V13 Ch 6): 120-layer model, 219 MB shard -> 0.25 ms/AllReduce on 900 GB/s
     NVLink (60 ms across 240 AllReduces) vs 9 ms/AllReduce on 25 GB/s InfiniBand (2,160 ms across
     240 AllReduces, 36x slower per collective, 1.2 tok/s vs 18-20 tok/s, 16.7x slowdown).
   - Sequence Parallelism (SP): partitions LayerNorm, Dropout, and residual activations along the
     sequence dimension (S / TP per rank), replacing each TP AllReduce with 1 AllGather + 1 ReduceScatter
     of identical collective volume (2 * (TP - 1)/TP * B * S * H * bytes) while cutting non-TP
     activation memory by 1 / TP.
3. Pipeline Parallelism (PP): GPipe vs. 1F1B vs. Interleaved 1F1B (Virtual Pipeline Parallelism) & DualPipe:
   - Bubble ratio (time fraction):
     * Standard GPipe / 1F1B bubble fraction = (PP - 1) / (m + PP - 1), or bubble-to-useful ratio
       (PP - 1) / m.
     * Interleaved 1F1B (v virtual stages per GPU): bubble-to-useful ratio = (PP - 1) / (m * v),
       reducing the bubble by factor v at the cost of v times more P2P communication.
   - In-flight activation memory: GPipe stores all m micro-batches (m * A_stage), whereas 1F1B caps
     in-flight micro-batches at PP on stage 0 (PP * A_stage), saving m / PP in activation memory.
   - Stage imbalance ("Ghost Straggler", V13 Ch 7): 50,000 x 12,288 x 2B = 1.2 GB embedding / lm_head
     causing stages 0 and 15 to run 40% slower than middle stages 1-14.
4. Long Context: Context Parallelism (CP Ring Attention) vs. DeepSpeed-Ulysses (2D All-to-All):
   - CP splits sequence S across CP ranks (S / CP tokens per GPU) and rotates K, V chunks in CP - 1
     ring P2P steps overlapped with attention compute.
   - DeepSpeed-Ulysses uses 2 All-to-All collectives per attention block to transpose from
     (B, S / P, H_all, D_h) sequence-parallel to (B, S_all, H / P, D_h) head-parallel (requires
     num_heads >= P).
5. Expert Parallelism (EP) for Mixture-of-Experts (MoE):
   - Distributes E experts across EP GPUs (E / EP local experts per GPU).
   - Top-k routing dispatches B * S * top_k token embeddings across EP ranks via All-to-All (dispatch
     + combine), bounded by Capacity Factor (CF): max_tokens_per_expert = ceil(CF * B * S * top_k / E).
   - DeepSeek-V3 (~671B-680B total, 37B active, 1 shared + 8 routed of 256 experts = 9 active/token)
     on H800 (400 GB/s NVLink vs 900 GB/s H100) using DeepEP and DualPipe.
6. 5D Hybrid Parallelism Grid Validator (DP * TP * PP * CP = WorldSize; EP for MoE layers) & Topology Mapping:
   - Validates GPT-3 175B (1024 GPUs: TP=8, PP=16, DP=8 -> 1.37B params/GPU = 22 GB state, 5.5% bubble;
     and 128 GPUs: TP=8, PP=16, DP=1), Llama-3 8B (8 GPUs: TP=1, PP=1, CP=2, DP=4), 70B hybrid
     (64 GPUs: TP=4, PP=2, DP=8), Mixtral 8x7B (64 GPUs: EP=8, TP=1, PP=4), and 1T on 1024 GPUs
     (TP=8, PP=4, DP=32).
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict


def compute_distributed_optimizer_bytes_per_param(
    precision_config: str, dp_size: int
) -> Dict[str, float | str]:
    """Computes Megatron Distributed Optimizer bytes/param vs unsharded baseline (DAI Ch 5).

    Supported precision_config values:
    - "fp16_params_fp16_grads": 20 B unsharded -> 4 + 16 / d B sharded
    - "bf16_params_fp32_grads": 18 B unsharded -> 6 + 12 / d B sharded
    - "fp32_params_fp32_grads": 16 B unsharded -> 8 + 8 / d B sharded
    """
    if dp_size < 1:
        raise ValueError("dp_size must be >= 1")

    if precision_config == "fp16_params_fp16_grads":
        unsharded = 20.0
        sharded = 4.0 + (16.0 / dp_size)
    elif precision_config == "bf16_params_fp32_grads":
        unsharded = 18.0
        sharded = 6.0 + (12.0 / dp_size)
    elif precision_config == "fp32_params_fp32_grads":
        unsharded = 16.0
        sharded = 8.0 + (8.0 / dp_size)
    else:
        raise ValueError(f"Unsupported precision_config: {precision_config}")

    return {
        "precision_config": precision_config,
        "dp_size": float(dp_size),
        "unsharded_bytes_per_param": unsharded,
        "sharded_bytes_per_param": sharded,
        "reduction_factor": unsharded / sharded,
    }


@dataclass(frozen=True)
class TensorParallelConfig:
    hidden_size: int
    ffn_hidden_size: int
    num_attention_heads: int
    num_query_groups: int
    num_layers: int
    batch_size: int
    seq_len: int
    tp_size: int
    bytes_per_element: int = 2
    sequence_parallel: bool = True


def analyze_tensor_and_sequence_parallelism(
    cfg: TensorParallelConfig,
) -> Dict[str, float | int | bool | tuple]:
    """Models Megatron ColumnParallel + RowParallel sharding, AllReduce vs SP, and activation savings."""
    if cfg.tp_size < 1:
        raise ValueError("tp_size must be >= 1")
    if cfg.ffn_hidden_size % cfg.tp_size != 0:
        raise ValueError("ffn_hidden_size must be divisible by tp_size")
    if cfg.num_attention_heads % cfg.tp_size != 0:
        raise ValueError("num_attention_heads must be divisible by tp_size")
    if cfg.seq_len % cfg.tp_size != 0:
        raise ValueError("seq_len must be divisible by tp_size")

    # MLP weight shapes: W1 is ColumnParallel (H, FFN/TP), W2 is RowParallel (FFN/TP, H)
    w1_full_params = cfg.hidden_size * cfg.ffn_hidden_size
    w1_full_mb = (w1_full_params * cfg.bytes_per_element) / 1e6
    w1_shard_shape = (cfg.hidden_size, cfg.ffn_hidden_size // cfg.tp_size)
    w2_shard_shape = (cfg.ffn_hidden_size // cfg.tp_size, cfg.hidden_size)
    local_heads = cfg.num_attention_heads // cfg.tp_size

    # Collectives per Transformer layer:
    # Standard TP: 1 AllReduce after Attention RowParallel + 1 AllReduce after MLP RowParallel
    # in forward (2), and 2 in backward = 4 AllReduces/layer.
    # With SP: each AllReduce is replaced by 1 AllGather + 1 ReduceScatter of the same total volume.
    fwd_collectives_per_layer = 2
    bwd_collectives_per_layer = 2
    total_allreduces_per_step = (fwd_collectives_per_layer + bwd_collectives_per_layer) * cfg.num_layers
    fwd_only_allreduces = fwd_collectives_per_layer * cfg.num_layers

    # Activation tensor size for one (B, S, H) buffer
    act_tensor_bytes = cfg.batch_size * cfg.seq_len * cfg.hidden_size * cfg.bytes_per_element
    ring_factor = (cfg.tp_size - 1) / cfg.tp_size if cfg.tp_size > 1 else 0.0

    # Ring AllReduce moves 2 * (TP-1)/TP * act_tensor_bytes per collective.
    # SP AllGather ((TP-1)/TP) + ReduceScatter ((TP-1)/TP) moves the exact same 2 * (TP-1)/TP bytes.
    bytes_per_tp_allreduce = 2.0 * ring_factor * act_tensor_bytes
    bytes_per_sp_ag_plus_rs = (ring_factor + ring_factor) * act_tensor_bytes

    # Non-TP LayerNorm/Dropout/Residual activation memory per layer (e.g., 4 buffers of (B, S, H))
    non_tp_buffers_per_layer = 4
    unsharded_non_tp_act_bytes = non_tp_buffers_per_layer * act_tensor_bytes * cfg.num_layers
    sp_non_tp_act_bytes = (
        unsharded_non_tp_act_bytes / cfg.tp_size if cfg.sequence_parallel else unsharded_non_tp_act_bytes
    )

    return {
        "w1_full_params": w1_full_params,
        "w1_full_mb": w1_full_mb,
        "w1_shard_shape": w1_shard_shape,
        "w2_shard_shape": w2_shard_shape,
        "local_attention_heads": local_heads,
        "fwd_allreduces_per_step": fwd_only_allreduces,
        "total_allreduces_per_step": total_allreduces_per_step,
        "bytes_per_tp_allreduce": bytes_per_tp_allreduce,
        "bytes_per_sp_ag_plus_rs": bytes_per_sp_ag_plus_rs,
        "comm_volume_identical": abs(bytes_per_tp_allreduce - bytes_per_sp_ag_plus_rs) < 1e-6,
        "unsharded_non_tp_act_gb": unsharded_non_tp_act_bytes / 1e9,
        "sp_non_tp_act_gb": sp_non_tp_act_bytes / 1e9,
        "sp_activation_reduction_factor": (
            float(cfg.tp_size) if cfg.sequence_parallel else 1.0
        ),
        "local_seq_len_sp": cfg.seq_len // cfg.tp_size if cfg.sequence_parallel else cfg.seq_len,
    }


def simulate_tp_cross_node_penalty(
    shard_mb: float = 219.0,
    num_layers: int = 120,
    allreduces_per_layer: int = 2,
    nvlink_bw_gbps: float = 900.0,
    ib_bw_gbps: float = 25.0,
) -> Dict[str, float]:
    """Models the V13 Ch 6 cross-node TP=32 failure vs intra-node NVLink TP=8."""
    total_allreduces = num_layers * allreduces_per_layer
    nvlink_ms_per_ar = shard_mb / nvlink_bw_gbps  # MB / (GB/s) = ms
    ib_ms_per_ar = shard_mb / ib_bw_gbps

    nvlink_total_ms = nvlink_ms_per_ar * total_allreduces
    ib_total_ms = ib_ms_per_ar * total_allreduces

    return {
        "total_allreduces": float(total_allreduces),
        "nvlink_ms_per_ar": nvlink_ms_per_ar,
        "ib_ms_per_ar": ib_ms_per_ar,
        "per_collective_slowdown": ib_ms_per_ar / nvlink_ms_per_ar,
        "nvlink_total_ms": nvlink_total_ms,
        "ib_total_ms": ib_total_ms,
    }


def compute_pipeline_parallel_metrics(
    pp_size: int,
    num_microbatches: int,
    virtual_stages: int = 1,
    activation_per_microbatch_gb: float = 1.0,
) -> Dict[str, float | int]:
    """Computes GPipe, 1F1B, and Interleaved 1F1B pipeline bubble ratios and activation memory."""
    if pp_size < 1 or num_microbatches < 1 or virtual_stages < 1:
        raise ValueError("pp_size, num_microbatches, and virtual_stages must be >= 1")

    # Time-fraction bubble formula from V13 Ch 6 & Ch 7: (PP - 1) / (m + PP - 1)
    bubble_time_fraction = (pp_size - 1) / (num_microbatches + pp_size - 1)
    # Interleaved 1F1B with v virtual stages reduces bubble by factor v:
    interleaved_bubble_time_fraction = (pp_size - 1) / (
        (num_microbatches * virtual_stages) + (pp_size - 1)
    )

    # Classic Narayanan et al. SC'21 bubble-to-useful ratio: (PP - 1) / m and (PP - 1) / (m * v)
    bubble_to_useful_ratio = (pp_size - 1) / num_microbatches
    interleaved_bubble_to_useful_ratio = (pp_size - 1) / (num_microbatches * virtual_stages)

    # Peak in-flight micro-batches on stage 0: GPipe holds all m; 1F1B holds min(m, PP)
    gpipe_inflight_microbatches = num_microbatches
    one_f_one_b_inflight_microbatches = min(num_microbatches, pp_size)

    return {
        "pp_size": pp_size,
        "num_microbatches": num_microbatches,
        "virtual_stages": virtual_stages,
        "bubble_time_fraction": bubble_time_fraction,
        "bubble_time_pct": bubble_time_fraction * 100.0,
        "interleaved_bubble_time_fraction": interleaved_bubble_time_fraction,
        "interleaved_bubble_time_pct": interleaved_bubble_time_fraction * 100.0,
        "bubble_to_useful_ratio": bubble_to_useful_ratio,
        "interleaved_bubble_to_useful_ratio": interleaved_bubble_to_useful_ratio,
        "interleaved_bubble_reduction_factor": float(virtual_stages),
        "p2p_comm_multiplier": float(virtual_stages),
        "gpipe_inflight_microbatches": gpipe_inflight_microbatches,
        "one_f_one_b_inflight_microbatches": one_f_one_b_inflight_microbatches,
        "gpipe_activation_gb": gpipe_inflight_microbatches * activation_per_microbatch_gb,
        "one_f_one_b_activation_gb": one_f_one_b_inflight_microbatches * activation_per_microbatch_gb,
        "activation_memory_saving_factor": (
            gpipe_inflight_microbatches / one_f_one_b_inflight_microbatches
        ),
    }


def analyze_context_parallelism_vs_ulysses(
    batch_size: int,
    seq_len: int,
    num_heads: int,
    num_kv_heads: int,
    head_dim: int,
    cp_degree: int,
    bytes_per_element: int = 2,
) -> Dict[str, float | int | tuple]:
    """Compares Context Parallelism (Ring Attention) vs DeepSpeed-Ulysses (2D All-to-All)."""
    if seq_len % cp_degree != 0:
        raise ValueError("seq_len must be divisible by cp_degree")
    if num_heads % cp_degree != 0:
        raise ValueError("num_heads must be divisible by cp_degree for DeepSpeed-Ulysses")

    local_seq = seq_len // cp_degree
    local_heads = num_heads // cp_degree
    hidden_size = num_heads * head_dim
    kv_hidden_size = num_kv_heads * head_dim

    # Ring Attention: rotates K and V chunks (each of shape (B, S/CP, num_kv_heads, head_dim))
    # across (CP - 1) ring steps per pass.
    kv_chunk_bytes = 2 * batch_size * local_seq * kv_hidden_size * bytes_per_element
    ring_steps = cp_degree - 1
    ring_fwd_comm_bytes_per_gpu = ring_steps * kv_chunk_bytes

    # DeepSpeed-Ulysses: 4 All-to-Alls in forward (Q, K, V seq->head + O head->seq).
    # Each All-to-All on a tensor of local size (B, S/P, H_total, D_h) sends (P - 1)/P of it.
    q_or_o_local_bytes = batch_size * local_seq * hidden_size * bytes_per_element
    kv_local_bytes = batch_size * local_seq * kv_hidden_size * bytes_per_element
    a2a_factor = (cp_degree - 1) / cp_degree
    ulysses_fwd_comm_bytes_per_gpu = a2a_factor * (2 * q_or_o_local_bytes + 2 * kv_local_bytes)

    return {
        "cp_degree": cp_degree,
        "local_seq_len": local_seq,
        "ulysses_seq_parallel_shape": (batch_size, local_seq, num_heads, head_dim),
        "ulysses_head_parallel_shape": (batch_size, seq_len, local_heads, head_dim),
        "ring_steps": ring_steps,
        "kv_chunk_mb": kv_chunk_bytes / 1e6,
        "ring_fwd_comm_mb": ring_fwd_comm_bytes_per_gpu / 1e6,
        "ulysses_fwd_comm_mb": ulysses_fwd_comm_bytes_per_gpu / 1e6,
    }


def analyze_expert_parallelism_moe(
    num_experts: int,
    ep_size: int,
    top_k: int,
    batch_size: int,
    seq_len: int,
    hidden_size: int,
    capacity_factor: float = 1.25,
    bytes_per_element: int = 2,
    shared_experts: int = 0,
) -> Dict[str, float | int]:
    """Models MoE Expert Parallelism token routing, All-to-All volume, and Capacity Factor."""
    if num_experts % ep_size != 0:
        raise ValueError("num_experts must be divisible by ep_size")

    experts_per_gpu = num_experts // ep_size
    tokens_per_gpu = batch_size * seq_len
    dispatched_tokens_per_gpu = tokens_per_gpu * top_k
    total_active_experts_per_token = shared_experts + top_k

    # Expected uniform tokens per expert across the EP group of ep_size GPUs
    total_tokens_in_ep_group = tokens_per_gpu * ep_size
    uniform_tokens_per_expert = (total_tokens_in_ep_group * top_k) / num_experts
    expert_capacity_tokens = math.ceil(capacity_factor * uniform_tokens_per_expert)

    # Under uniform routing, (ep_size - 1) / ep_size of dispatched tokens cross GPU boundaries
    # once during Dispatch All-to-All and once during Combine All-to-All.
    remote_fraction = (ep_size - 1) / ep_size if ep_size > 1 else 0.0
    bytes_per_token = hidden_size * bytes_per_element
    dispatch_a2a_bytes_per_gpu = dispatched_tokens_per_gpu * bytes_per_token * remote_fraction
    combine_a2a_bytes_per_gpu = dispatch_a2a_bytes_per_gpu
    total_fwd_a2a_bytes_per_gpu = dispatch_a2a_bytes_per_gpu + combine_a2a_bytes_per_gpu

    return {
        "num_experts": num_experts,
        "ep_size": ep_size,
        "experts_per_gpu": experts_per_gpu,
        "top_k": top_k,
        "shared_experts": shared_experts,
        "total_active_experts_per_token": total_active_experts_per_token,
        "tokens_per_gpu": tokens_per_gpu,
        "dispatched_tokens_per_gpu": dispatched_tokens_per_gpu,
        "uniform_tokens_per_expert": uniform_tokens_per_expert,
        "expert_capacity_tokens": expert_capacity_tokens,
        "dispatch_a2a_mb": dispatch_a2a_bytes_per_gpu / 1e6,
        "total_fwd_a2a_mb": total_fwd_a2a_bytes_per_gpu / 1e6,
    }


@dataclass(frozen=True)
class HybridParallelConfig:
    world_size: int
    gpus_per_node: int
    tp: int
    pp: int
    cp: int = 1
    ep: int = 1
    num_layers: int = 32
    params_billion: float = 70.0
    global_batch_size: int = 128
    micro_batch_size: int = 1
    bytes_per_param_state: float = 16.0


def validate_hybrid_5d_config(cfg: HybridParallelConfig) -> Dict[str, float | int | bool | str]:
    """Validates Megatron 3D/4D/5D process grid (DP * TP * PP * CP == WorldSize) and placement."""
    model_and_context_divisor = cfg.tp * cfg.pp * cfg.cp
    valid_world_size = (cfg.world_size % model_and_context_divisor) == 0
    dp = cfg.world_size // model_and_context_divisor if valid_world_size else 0

    tp_within_nvlink_domain = cfg.tp <= cfg.gpus_per_node and (cfg.gpus_per_node % cfg.tp == 0)
    layers_divisible_by_pp = (cfg.num_layers % cfg.pp) == 0
    layers_per_stage = cfg.num_layers // cfg.pp if layers_divisible_by_pp else 0

    # Effective micro-batches per DP replica: m = global_batch_size / (dp * micro_batch_size)
    denom = dp * cfg.micro_batch_size
    valid_batch = denom > 0 and (cfg.global_batch_size % denom == 0)
    num_microbatches = cfg.global_batch_size // denom if valid_batch else 0

    # Per-GPU parameter shard for dense layers: params_billion / (TP * PP)
    params_per_gpu_billion = cfg.params_billion / (cfg.tp * cfg.pp)
    # Without distributed optimizer: 16 bytes/param; with distributed optimizer (bf16/fp32): 6 + 12/dp
    unsharded_dp_state_gb = params_per_gpu_billion * cfg.bytes_per_param_state
    dist_opt_bytes_per_param = 6.0 + (12.0 / dp) if dp > 0 else cfg.bytes_per_param_state
    dist_opt_state_gb = params_per_gpu_billion * dist_opt_bytes_per_param

    bubble_pct = (
        ((cfg.pp - 1) / (num_microbatches + cfg.pp - 1)) * 100.0
        if (cfg.pp > 1 and num_microbatches > 0)
        else 0.0
    )

    return {
        "valid_world_size": valid_world_size,
        "dp_size": dp,
        "tp_size": cfg.tp,
        "pp_size": cfg.pp,
        "cp_size": cfg.cp,
        "ep_size": cfg.ep,
        "tp_within_nvlink_domain": tp_within_nvlink_domain,
        "layers_divisible_by_pp": layers_divisible_by_pp,
        "layers_per_stage": layers_per_stage,
        "num_microbatches_per_dp": num_microbatches,
        "params_per_gpu_billion": params_per_gpu_billion,
        "unsharded_dp_state_gb": unsharded_dp_state_gb,
        "dist_opt_state_gb": dist_opt_state_gb,
        "pipeline_bubble_pct": bubble_pct,
    }


def map_rank_to_3d_coordinates(
    rank: int, dp: int, tp: int, pp: int
) -> Dict[str, int]:
    """Maps a global rank in [0, dp*tp*pp) to (dp_rank, pp_rank, tp_rank) with TP innermost."""
    world_size = dp * tp * pp
    if not (0 <= rank < world_size):
        raise ValueError(f"rank {rank} out of [0, {world_size})")
    # Standard Megatron ordering: TP is innermost (contiguous ranks inside NVLink node),
    # then PP or DP depending on --order. Here TP innermost, PP middle, DP outermost:
    tp_rank = rank % tp
    pp_rank = (rank // tp) % pp
    dp_rank = rank // (tp * pp)
    return {"rank": rank, "dp_rank": dp_rank, "pp_rank": pp_rank, "tp_rank": tp_rank}


if __name__ == "__main__":
    gpt3 = validate_hybrid_5d_config(
        HybridParallelConfig(
            world_size=1024,
            gpus_per_node=8,
            tp=8,
            pp=16,
            cp=1,
            num_layers=96,
            params_billion=175.0,
            global_batch_size=2048,
            micro_batch_size=1,
        )
    )
    print("GPT-3 175B on 1024 H100s:", gpt3)
