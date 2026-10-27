#!/usr/bin/env python3
"""Chapter 15.9 model: Multinode Inference Parallelism, Speculative Decoding, and Routing.

Models:
1. Tensor Parallelism (TP) vs Pipeline Parallelism (PP) vs Data Parallelism (DP) & Interconnect Cliff:
   - Megatron-LM style Column-Parallel (`W_q, W_k, W_v`, MLP gate/up) + Row-Parallel (`W_o`, MLP down)
     linear layers require 2 synchronous AllReduce operations per Transformer layer (`2 * L` AllReduces
     per generated token; `160` AllReduces/token for an `80`-layer Llama-3-70B model, or `8,000`
     AllReduces/sec at `50 tokens/s`).
   - Ring AllReduce executes `2 * (N - 1)` sequential transfer steps per collective and moves
     `Data_Volume = 2 * ((N - 1) / N) * B * S * H * Bytes` per rank.
   - Interconnect latency and bandwidth comparison:
     * NVLink 5 (Blackwell B200 / GB200 NVL72): `1,800 GB/s` (`1.8 TB/s`) per GPU, `130 TB/s` aggregate across `72` GPUs (`576` GPUs across `8` racks), `< 1.0 us` latency.
     * NVLink 4 (H100 / H200 SXM): `900 GB/s` per GPU (`< 1.0 us` latency).
     * NVLink 3 (A100 SXM) / H100 NVL 2-GPU Bridge: `600 GB/s` (`< 1.5 us`).
     * H800 NVLink: `400 GB/s`.
     * PCIe Gen5 x16: `64 GB/s` per direction (`128 GB/s` bidirectional, `5 - 10 us` latency).
     * InfiniBand NDR / RoCEv2 (`400 Gbps` = `50 GB/s` per port, `1.5 - 3.0 us` with GPUDirect RDMA `NCCL_NET_GDR_LEVEL=5`, `4x - 6x` lower P2P latency than host-staged copy).
     * ConnectX-8 SuperNIC (`800 Gbps` = `100 GB/s` per port).
     * Standard `100GbE` TCP/IP host stack: `100 Gbps` (`12.5 GB/s`, `50 - 150 us` latency).
   - Explains why `TP > 8` across PCIe or Ethernet adds `50 ms` to `200 ms` of AllReduce latency per
     token (`> 90%` of execution time stalled on network synchronization), whereas PP transfers only
     `B * S * (H / TP) * Bytes` once per stage boundary (`P - 1` P2P hops per forward pass).

2. Wide Expert Parallelism (EP), DeepSeek-R1 671B, and Hybrid 5D Parallelism:
   - DeepSeek-V3 / DeepSeek-R1 (`671B` total parameters, `~680B` nominal, `37B` active per token across
     `1` shared + `8` of `256` routed experts = `9` active experts/token; trained on `2,048` H800 GPUs
     for `$5.5M`; distilled `70B` variant `94.5%` vs `97.3%` on MATH-500, `65.2%` vs `71.5%` GPQA,
     `57.5%` vs `65.9%` LiveCodeBench).
   - vLLM / SGLang Expert Parallelism: `EP_SIZE = TP_SIZE * DP_SIZE` (requires `TP * DP > 1`), hosting
     `Total_Experts / EP_SIZE` complete experts per GPU (`32` experts/GPU on `8` GPUs, `4` experts/GPU
     on `64` GPUs).
   - Compares `TP+EP` (AllReduce, duplicated Multi-Head Latent Attention `MLA` KV cache across `TP`
     ranks) against `DP+EP` (`--enable-dp-attention`, request-partitioned KV cache eliminating `8x`
     duplication for up to `1.9x` decode throughput + `AllToAll` expert routing via `DeepEP`/`DeepGEMM`
     when activation density `> 3%`).
   - Models the `64`-GPU (`16 x 4`) hybrid configuration (`PP=4` with `15` layers/stage across `60`
     layers, `TP=2`, `EP=16` across `64` experts with `top-2` gating, plus `DP=2` on `128` GPUs) and
     `32`-GPU (`TP=4, PP=8`) DeepSeek-R1 deployment (`~84B` parameters/stage, `2,048`-element shard).
   - Models Context / Sequence / Helix Parallelism for `100,000` to `1,000,000+` token contexts (`3.31x`
     prefill throughput, `81%` TTFT reduction, `82.8%` scaling efficiency).

3. Dynamic MoE Routing, Wave Scheduling, Capacity Factor, and EPLB:
   - Models monolithic `AllToAll` message storm on `72`-GPU NVL72 (`72 * 71 = 5,112` messages) vs
     `4`-wave scheduling of `18` GPUs (`18 * 17 = 306` intra-wave messages per wave).
   - Models MoE capacity factor (`CF = 1.0`, `1.2` [`20%` overflow allowance], `1.5` on `32`-token base
     load -> `32`, `38`, `48` max tokens), hot-expert straggler (`99%` vs `60%` GPU utilization),
     co-activated expert collocation (experts `5` and `7`), and DeepSeek `EPLB` redundant expert cloning
     with `80%` utilization alert threshold.

4. Speculative Decoding Draft-Verify Math, EAGLE, Medusa, MTP, and Lookahead:
   - Rejection sampling acceptance probability `min(1.0, p_target(x) / q_draft(x))` (`0.8 / 0.6 -> 1.0`,
     `0.4 / 0.6 -> 0.6667`) and expected generated tokens per verification pass:
     `E[tokens] = (1 - alpha^(K + 1)) / (1 - alpha)` for uniform acceptance rate `alpha`, or exact
     positional prefix product for position-dependent acceptance rates `[0.8, 0.7, 0.6, 0.5, 0.10, 0.02]`.
   - Net wall-clock speedup `S = E[tokens] / (1 + K * c_draft)` where `c_draft = t_draft / t_target`
     (requiring draft model `>= 4x` faster, `c_draft <= 0.25`).
   - Compares Two-Model Draft-Verify (`1.5x - 2.5x`, `3x - 4x` on code/JSON), EAGLE-1 (`3.5x` on
     `4`-token draft), EAGLE-2 (`+20% - 40%` dynamic draft tree), EAGLE-3 (`1.4x` over EAGLE-2, `6.5x`
     over baseline; `56.5` vs `28.9 tok/s` = `1.96x` on `Qwen3-32B` at `C=1`), Medusa (`2.2x - 3.6x`,
     depth-2 binary tree of `4` tokens cutting `100` tokens from `100` to `25` iterations), DeepSeek
     Multi-Token Prediction (`MTP`), Lookahead / N-gram prompt lookup (`+16%` at `C=1`), self-speculative
     layer skipping (`~2x`), and consistent decoding (`~3x`).

5. Kubernetes LeaderWorkerSet (LWS), Prefix-Aware Routing, and Failure Modes:
   - Models Kubernetes `LeaderWorkerSet` (`leaderworkerset.x-k8s.io/v1`) gang-scheduled multi-node pods
     (`size = 1 leader + (N - 1) workers`) and failure domain recovery.
   - Models prefix-aware routing (`> 85%` KV cache hit rate, up to `90%` TTFT reduction) vs round-robin
     (`110 tok/s` vs `240 tok/s` across `4` nodes with GPU util `[95%, 45%, 88%, 22%]` and KV usage
     `[91%, 32%, 85%, 18%]`) and pure prefix hash hotspot (`Node 0: 3,600 reqs / 280K tokens` vs
     `Node 1: 1,100 reqs / 95K tokens` = `3.27x` imbalance), resolved by bounded-load prefix routing.
   - Models Failure Scenario 1 (`405B` `TP=16` across `2` nodes hitting `30 s` NCCL timeout -> fixed by
     `TP=8, PP=2` `< 45 s` init) and Failure Scenario 2 (`TP=4, PP=2` Stage 0 `99.2%` vs Stage 1 `38.5%`
     KV cache starvation with `4,500 ms` queue delay -> fixed by chunked prefill or `DP=2, TP=8` at
     `72%` / `74%`).
"""

from __future__ import annotations
import math
from typing import Dict, List, Sequence


def evaluate_tp_vs_pp_communication(
    num_layers: int = 80,
    tp_size: int = 8,
    pp_size: int = 1,
    batch_size: int = 1,
    seq_len: int = 1,
    hidden_size: int = 8192,
    precision_bytes: float = 2.0,
    interconnect_bw_gbps: float = 900.0,
    per_step_latency_us: float = 0.8,
    compute_ms_per_token: float = 14.0,
    target_tokens_per_sec: float = 50.0,
) -> Dict[str, float]:
    """Computes TP AllReduce and PP point-to-point communication volume, steps, and ITL impact."""
    allreduces_per_layer = 2
    allreduces_per_token = num_layers * allreduces_per_layer if tp_size > 1 else 0
    allreduces_per_sec = allreduces_per_token * target_tokens_per_sec
    ring_steps_per_allreduce = 2 * (tp_size - 1) if tp_size > 1 else 0
    total_ring_steps_per_token = allreduces_per_token * ring_steps_per_allreduce

    tensor_bytes = batch_size * seq_len * hidden_size * precision_bytes
    per_allreduce_bytes = (
        2.0 * ((tp_size - 1) / tp_size) * tensor_bytes if tp_size > 1 else 0.0
    )
    tp_total_bytes_per_token = allreduces_per_token * per_allreduce_bytes

    # Bandwidth time + per-collective / per-hop latency
    bw_bytes_per_sec = interconnect_bw_gbps * 1e9
    tp_bw_ms = (tp_total_bytes_per_token / bw_bytes_per_sec) * 1e3 if bw_bytes_per_sec > 0 else 0.0
    tp_lat_ms = (allreduces_per_token * per_step_latency_us) / 1e3
    tp_comm_ms_per_token = tp_bw_ms + tp_lat_ms

    # Pipeline Parallelism P2P across (pp_size - 1) stage boundaries, sharded by tp_size
    pp_hops = max(0, pp_size - 1)
    pp_elements_per_token_per_rank = hidden_size // tp_size
    pp_bytes_per_hop = batch_size * seq_len * pp_elements_per_token_per_rank * precision_bytes
    pp_total_bytes_per_token = pp_hops * pp_bytes_per_hop
    pp_comm_ms_per_token = (
        (pp_total_bytes_per_token / bw_bytes_per_sec) * 1e3
        + (pp_hops * per_step_latency_us) / 1e3
        if pp_hops > 0
        else 0.0
    )

    total_itl_ms = compute_ms_per_token + tp_comm_ms_per_token + pp_comm_ms_per_token
    comm_fraction_pct = (
        ((tp_comm_ms_per_token + pp_comm_ms_per_token) / total_itl_ms) * 100.0
        if total_itl_ms > 0
        else 0.0
    )

    return {
        "allreduces_per_layer": float(allreduces_per_layer),
        "allreduces_per_token": float(allreduces_per_token),
        "allreduces_per_sec": float(allreduces_per_sec),
        "ring_steps_per_allreduce": float(ring_steps_per_allreduce),
        "total_ring_steps_per_token": float(total_ring_steps_per_token),
        "per_allreduce_bytes": round(per_allreduce_bytes, 2),
        "tp_total_bytes_per_token": round(tp_total_bytes_per_token, 2),
        "tp_comm_ms_per_token": round(tp_comm_ms_per_token, 4),
        "pp_hops": float(pp_hops),
        "pp_elements_per_token_per_rank": float(pp_elements_per_token_per_rank),
        "pp_bytes_per_hop": round(pp_bytes_per_hop, 2),
        "pp_comm_ms_per_token": round(pp_comm_ms_per_token, 4),
        "total_itl_ms": round(total_itl_ms, 2),
        "comm_fraction_pct": round(comm_fraction_pct, 2),
    }


def evaluate_wide_ep_and_hybrid_moe(
    total_params_b: float = 671.0,
    active_params_b: float = 37.0,
    num_routed_experts: int = 256,
    num_shared_experts: int = 1,
    routed_top_k: int = 8,
    tp_size: int = 1,
    dp_size: int = 8,
    pp_size: int = 1,
    nvl72_gpus_per_rack: int = 72,
    nvl_racks: int = 8,
) -> Dict[str, float]:
    """Models DeepSeek-R1 671B / MoE Expert Parallelism, NVL72 fabric, and hybrid 5D layouts."""
    ep_size = tp_size * dp_size
    ep_enabled = ep_size > 1
    experts_per_gpu = num_routed_experts / ep_size if ep_enabled else float(num_routed_experts)
    total_active_experts_per_token = num_shared_experts + routed_top_k
    routed_activation_density_pct = (routed_top_k / num_routed_experts) * 100.0
    active_param_fraction_pct = (active_params_b / total_params_b) * 100.0

    # Communication mode in vLLM/SGLang: DP == 1 -> AllReduce; DP > 1 -> AllToAll + DP Attention
    uses_all_to_all = dp_size > 1 and ep_enabled
    kv_duplication_factor_without_dp_attn = float(tp_size)

    # 32-GPU TP=4, PP=8 DeepSeek-R1 stage sharding
    total_gpus_tp4_pp8 = 4 * 8
    params_per_pp8_stage_b = total_params_b / 8.0

    # 64-GPU (16 groups of 4) hybrid MoE from ASP Ch. 15: 60 layers, 64 experts, PP=4, TP=2, EP=16, DP=2
    asp_hybrid_layers_per_stage = 60 // 4
    asp_hybrid_total_gpus_with_dp2 = 64 * 2

    # NVL72 and 8-rack NVLink Switch fabric metrics
    nvl72_per_gpu_bw_tbps = 1.8
    nvl72_rack_bw_tbps = 130.0
    nvl72_hbm_gb = 72 * 192
    nvl_max_gpus_8_racks = nvl72_gpus_per_rack * nvl_racks

    return {
        "ep_size": float(ep_size),
        "ep_enabled": 1.0 if ep_enabled else 0.0,
        "experts_per_gpu": round(experts_per_gpu, 2),
        "total_active_experts_per_token": float(total_active_experts_per_token),
        "routed_activation_density_pct": round(routed_activation_density_pct, 2),
        "active_param_fraction_pct": round(active_param_fraction_pct, 2),
        "uses_all_to_all": 1.0 if uses_all_to_all else 0.0,
        "kv_duplication_factor_without_dp_attn": kv_duplication_factor_without_dp_attn,
        "total_gpus_tp4_pp8": float(total_gpus_tp4_pp8),
        "params_per_pp8_stage_b": round(params_per_pp8_stage_b, 3),
        "asp_hybrid_layers_per_stage": float(asp_hybrid_layers_per_stage),
        "asp_hybrid_total_gpus_with_dp2": float(asp_hybrid_total_gpus_with_dp2),
        "nvl72_per_gpu_bw_tbps": nvl72_per_gpu_bw_tbps,
        "nvl72_rack_bw_tbps": nvl72_rack_bw_tbps,
        "nvl72_hbm_gb": float(nvl72_hbm_gb),
        "nvl_max_gpus_8_racks": float(nvl_max_gpus_8_racks),
    }


def evaluate_moe_routing_and_eplb(
    num_gpus: int = 72,
    num_waves: int = 4,
    base_token_capacity: int = 32,
    capacity_factor: float = 1.2,
    expert_token_loads: Sequence[int] = (50, 28, 30, 20),
    hot_gpu_util_pct: float = 99.0,
    peer_gpu_util_pct: float = 60.0,
    alert_threshold_pct: float = 80.0,
) -> Dict[str, float]:
    """Models NVL72 AllToAll wave scheduling, capacity factor overflow, and EPLB hot-expert cloning."""
    monolithic_messages = num_gpus * (num_gpus - 1)
    gpus_per_wave = num_gpus // num_waves
    intra_wave_messages = gpus_per_wave * (gpus_per_wave - 1)
    instantaneous_message_reduction_x = monolithic_messages / intra_wave_messages

    max_tokens_per_expert = int(math.floor(base_token_capacity * capacity_factor))
    max_tokens_cf_1_0 = int(base_token_capacity * 1.0)
    max_tokens_cf_1_5 = int(base_token_capacity * 1.5)

    overflow_tokens = sum(max(0, load - max_tokens_per_expert) for load in expert_token_loads)
    accepted_primary_tokens = sum(min(load, max_tokens_per_expert) for load in expert_token_loads)

    # EPLB cloning of the hottest expert onto a redundant slot halves its per-replica load
    max_load_before_eplb = max(expert_token_loads)
    max_load_after_eplb = max(
        math.ceil(max_load_before_eplb / 2.0),
        max(expert_token_loads[1:]) if len(expert_token_loads) > 1 else 0,
    )
    straggler_gap_pct = hot_gpu_util_pct - peer_gpu_util_pct
    triggers_alert = hot_gpu_util_pct > alert_threshold_pct

    return {
        "monolithic_messages": float(monolithic_messages),
        "gpus_per_wave": float(gpus_per_wave),
        "intra_wave_messages": float(intra_wave_messages),
        "instantaneous_message_reduction_x": round(instantaneous_message_reduction_x, 2),
        "max_tokens_cf_1_0": float(max_tokens_cf_1_0),
        "max_tokens_per_expert": float(max_tokens_per_expert),
        "max_tokens_cf_1_5": float(max_tokens_cf_1_5),
        "accepted_primary_tokens": float(accepted_primary_tokens),
        "overflow_tokens": float(overflow_tokens),
        "max_load_before_eplb": float(max_load_before_eplb),
        "max_load_after_eplb": float(max_load_after_eplb),
        "straggler_gap_pct": round(straggler_gap_pct, 2),
        "triggers_alert": 1.0 if triggers_alert else 0.0,
    }


def evaluate_speculative_decoding(
    k_draft: int = 4,
    alpha: float = 0.8,
    draft_cost_ratio: float = 0.10,
    p_target_sample: float = 0.4,
    q_draft_sample: float = 0.6,
    positional_accept_rates: Sequence[float] = (0.8, 0.7, 0.6, 0.5, 0.10, 0.02),
    medusa_tree_tokens_per_pass: int = 4,
    target_reply_tokens: int = 100,
) -> Dict[str, float]:
    """Computes speculative decoding rejection sampling, expected tokens, net speedup, and Medusa/EAGLE metrics."""
    # Rejection sampling acceptance probability min(1, p(x) / q(x))
    accept_prob_when_p_gt_q = min(1.0, 0.8 / 0.6)
    accept_prob_sample = min(1.0, p_target_sample / q_draft_sample)

    # Expected tokens generated per draft-verify cycle for uniform acceptance rate alpha
    if abs(1.0 - alpha) < 1e-9:
        expected_tokens = float(k_draft + 1)
    else:
        expected_tokens = (1.0 - (alpha ** (k_draft + 1))) / (1.0 - alpha)

    cycle_cost_units = 1.0 + (k_draft * draft_cost_ratio)
    net_speedup_x = expected_tokens / cycle_cost_units

    # Positional acceptance analysis for K=6: [0.8, 0.7, 0.6, 0.5, 0.10, 0.02]
    # Expected tokens = 1 + sum_{i=1..K} prod_{j=1..i} alpha_j
    prefix_prob = 1.0
    expected_tokens_k6 = 1.0
    expected_tokens_k4_trimmed = 1.0
    for idx, rate in enumerate(positional_accept_rates):
        prefix_prob *= rate
        expected_tokens_k6 += prefix_prob
        if idx < 4:
            expected_tokens_k4_trimmed += prefix_prob

    # Medusa depth-2 binary tree (4 tokens/pass) for 100-token reply
    medusa_ideal_iterations = target_reply_tokens // medusa_tree_tokens_per_pass

    # HLS Ch. 7 Qwen3-32B vLLM benchmark numbers (C=1)
    vanilla_vllm_tps = 28.9
    eagle3_vllm_tps = 56.5
    eagle3_measured_speedup_x = eagle3_vllm_tps / vanilla_vllm_tps

    return {
        "accept_prob_when_p_gt_q": round(accept_prob_when_p_gt_q, 4),
        "accept_prob_sample": round(accept_prob_sample, 4),
        "expected_tokens": round(expected_tokens, 4),
        "cycle_cost_units": round(cycle_cost_units, 4),
        "net_speedup_x": round(net_speedup_x, 2),
        "expected_tokens_k6": round(expected_tokens_k6, 4),
        "expected_tokens_k4_trimmed": round(expected_tokens_k4_trimmed, 4),
        "marginal_tokens_from_last_2_steps": round(expected_tokens_k6 - expected_tokens_k4_trimmed, 4),
        "medusa_ideal_iterations": float(medusa_ideal_iterations),
        "vanilla_vllm_tps": vanilla_vllm_tps,
        "eagle3_vllm_tps": eagle3_vllm_tps,
        "eagle3_measured_speedup_x": round(eagle3_measured_speedup_x, 2),
    }


def evaluate_lws_and_prefix_routing(
    lws_replicas: int = 2,
    lws_group_size: int = 2,
    gpus_per_pod: int = 8,
    single_node_tps: float = 60.0,
    num_dp_nodes: int = 4,
    observed_round_robin_tps: float = 110.0,
    node_gpu_utils_pct: Sequence[float] = (95.0, 45.0, 88.0, 22.0),
    node_kv_usages_pct: Sequence[float] = (91.0, 32.0, 85.0, 18.0),
    hot_node_requests: int = 3600,
    cold_node_requests: int = 1100,
    pp_stage0_kv_perc: float = 0.992,
    pp_stage1_kv_perc: float = 0.385,
) -> Dict[str, float]:
    """Models Kubernetes LWS gang topology, DP routing skew, prefix hotspots, and PP stage KV imbalance."""
    pods_per_lws_replica = lws_group_size
    leader_pods_per_replica = 1
    worker_pods_per_replica = lws_group_size - 1
    gpus_per_lws_replica = lws_group_size * gpus_per_pod
    total_cluster_gpus = lws_replicas * gpus_per_lws_replica

    ideal_dp_tps = single_node_tps * num_dp_nodes
    round_robin_scaling_eff_pct = (observed_round_robin_tps / ideal_dp_tps) * 100.0
    gpu_util_spread_pct = max(node_gpu_utils_pct) - min(node_gpu_utils_pct)
    kv_usage_spread_pct = max(node_kv_usages_pct) - min(node_kv_usages_pct)

    prefix_skew_ratio = hot_node_requests / cold_node_requests

    pp_kv_imbalance_diff = pp_stage0_kv_perc - pp_stage1_kv_perc
    pp_imbalance_alert_triggered = pp_kv_imbalance_diff > 0.40

    return {
        "pods_per_lws_replica": float(pods_per_lws_replica),
        "leader_pods_per_replica": float(leader_pods_per_replica),
        "worker_pods_per_replica": float(worker_pods_per_replica),
        "gpus_per_lws_replica": float(gpus_per_lws_replica),
        "total_cluster_gpus": float(total_cluster_gpus),
        "ideal_dp_tps": round(ideal_dp_tps, 2),
        "round_robin_scaling_eff_pct": round(round_robin_scaling_eff_pct, 2),
        "gpu_util_spread_pct": round(gpu_util_spread_pct, 2),
        "kv_usage_spread_pct": round(kv_usage_spread_pct, 2),
        "prefix_skew_ratio": round(prefix_skew_ratio, 2),
        "pp_kv_imbalance_diff": round(pp_kv_imbalance_diff, 3),
        "pp_imbalance_alert_triggered": 1.0 if pp_imbalance_alert_triggered else 0.0,
    }


if __name__ == "__main__":
    tp_nvlink = evaluate_tp_vs_pp_communication(tp_size=8, interconnect_bw_gbps=900.0, per_step_latency_us=0.8)
    tp_eth = evaluate_tp_vs_pp_communication(tp_size=16, interconnect_bw_gbps=12.5, per_step_latency_us=500.0)
    moe = evaluate_wide_ep_and_hybrid_moe()
    eplb = evaluate_moe_routing_and_eplb()
    spec = evaluate_speculative_decoding()
    lws = evaluate_lws_and_prefix_routing()
    print("TP=8 NVLink ITL:", tp_nvlink["total_itl_ms"], "ms vs TP=16 Ethernet ITL:", tp_eth["total_itl_ms"], "ms")
    print("DeepSeek-R1 671B experts/GPU (EP=8):", moe["experts_per_gpu"], "Active experts/token:", moe["total_active_experts_per_token"])
    print("NVL72 AllToAll messages (monolithic vs 4 waves):", eplb["monolithic_messages"], "->", eplb["intra_wave_messages"])
    print("Speculative decoding E[tokens] (K=4, alpha=0.8):", spec["expected_tokens"], "Speedup:", spec["net_speedup_x"], "x")
    print("LWS total GPUs:", lws["total_cluster_gpus"], "Prefix skew ratio:", lws["prefix_skew_ratio"], "x")
