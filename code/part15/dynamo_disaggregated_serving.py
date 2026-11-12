#!/usr/bin/env python3
"""Chapter 15.8 model: NVIDIA Dynamo, llm-d and disaggregated serving.

Models:
1. Colocated vs Disaggregated Prefill-Decode Goodput and MLPerf v5.0 SLOs:
   - Quantifies DistServe 2P1D goodput (`1.6 RPS` colocated vs `3.33 RPS` / `3.3 RPS` per GPU
     disaggregated across `2` prefill GPUs at `5.6 RPS` each [`11.2 RPS` total] and `1` decode GPU
     at `10.0 RPS` under `P90 TTFT <= 400 ms` [`0.4 s`] and `P90 TPOT <= 40 ms` [`0.04 s`]).
   - Captures DistServe peak gains (`7.4x` goodput, `12.6x` tighter latency SLOs) and NVIDIA Dynamo
     `30x` inference throughput on a `680B` MoE model across a `72`-GPU `GB200 NVL72` rack (`130 TB/s`).
   - Evaluates MLPerf Inference v5.0 (2025) p99 SLOs (`Llama-2-70B`: `450 ms` TTFT, `40 ms` TPOT;
     `Llama-3.1-405B`: `6,000 ms` [`6 s`] TTFT, `175 ms` TPOT) and single-stream H100 memory-bandwidth
     ceiling (`140 GB / 3,350 GB/s = 41.79 ms` / `~41.7 ms`, `23.93 tok/s` / `~24 tok/s`).
2. NVIDIA Dynamo Smart Router (`should_offload_prefill`, Composite `latency_cost`, and Remote Score):
   - Models decode-centric conditional prefill offloading (`PREFILL_LENGTH_THRESHOLD = 256`,
     `PREFILL_QUEUE_MAX = 10`, `DECODE_LOAD_THRESHOLD = 8`, secondary `eff_len >= 64` threshold)
     using `eff_len = max(0, prompt_length - prefix_cached_length)`.
   - Computes two-term worker latency cost (`0.7 * occupancy_percent + 0.3 * active_req_count`) and
     five-factor composite `latency_cost` (`+3.0 * occupancy_percent + 1.0 * active_reqs - 10.0 * cache_match
     + 0.5 * mem_bw_percent - 1.0 * recent_prefix`).
   - Computes Dynamo YAML `disaggregated_router` remote prefill score (`0.7` weight for `prefill_length > 256`,
     `0.3` weight for `prefill_queue_depth <= 10`, compared against `remote_prefill_min_score = 0.5`).
3. NVIDIA Dynamo GPU Planner, QoS Tiers, and Early Rejection (`QoSController`):
   - Evaluates Dynamo Planner replica scaling (`prefill`: `min_replicas=4, max_replicas=12`, scale up at
     `queue_length >= 8` or `gpu_utilization >= 80%`, scale down at `queue_length <= 2` and `gpu_utilization <= 40%`;
     `decode`: `min_replicas=8, max_replicas=24`, scale up at `queue_length >= 16` or `kv_cache_usage >= 75%`,
     scale down at `queue_length <= 4` and `kv_cache_usage <= 30%`).
   - Models QoS capacity reservation (`premium`: `10%`, `priority=100`; `standard`: `30%`, `priority=50`;
     `free`: `60%`, `priority=10`) and early rejection admission control (`est_ttft = Q_p * t_p + Q_d * t_d > 500 ms`).
4. NIXL (`NVIDIA Inference Xfer Library`) & Distributed KV Cache Manager Offloading Hierarchy:
   - Models `nixlAgent` (`0.5.x`) nonblocking lifecycle (`registerMem -> trim -> prepXfer -> postXfer -> checkXfer ->
     releaseReqH -> deregisterMem`) over `VRAM_SEG` (`1 MiB = 1,048,576 B` test buffer and `1 GiB = 1,073,741,824 B`
     LMCache/NIXL `pd_buffer_size` on ports `7300`, `7400`, `7500` with `UCX_RNDV_THRESH = 16384`).
   - Quantifies PagedAttention block collation (`7,500` tokens across `16`-token blocks = `469` [`~470`] WQEs
     taking `20.0 ms` vs `128`-token collated slabs = `59` WQEs taking `8.0 ms`, a `2.5x` speedup).
   - Quantifies KV cache transfer demand at `16 RPS` (`1.5 GB`/req = `24.0 GB/s`, `~25 GB/s`) across
     `NVLink 4` (`900 GB/s`), `NVLink 5` (`1,800 GB/s`), `ConnectX-7 NDR` (`400 Gbps = 50 GB/s`),
     `ConnectX-8 XDR/800GbE` (`800 Gbps = 100 GB/s`), and non-RDMA PCIe/TCP (`10 GB/s`).
   - Quantifies the 4-tier KV Cache Manager hierarchy (`GPU HBM -> Grace/Host DRAM -> Local NVMe SSD via GDS ->
     Remote Shared Storage`), `250,000`-token `70B` MHA KV footprint (`328 GB` FP16 -> `100–150 GB` FP8),
     `x86 + H100` `14x` TTFT speedup, `GH200` `900 GB/s` NVLink-C2C `2x` additional speedup (`28x` vs recompute),
     and `LMCache` `3x` CPU / `50x` SSD capacity expansion (`1.0 s` vs `6.0–7.0 s` TTFT, `16x` throughput over `4,700 tok/s`).
   - Models heterogeneous hardware (`B200` prefill + `B300` decode with `288 GB` HBM / `70 GB` weights / `218 GB` left for KV;
     Splitwise `4x H100 + 4x A100` `2.35x` RPS at iso-cost/power and `1.4x` at `-20%` cost; HexGen-2 `2.0x` peak /
     `1.3x` avg or `-30%` cost; Arrow `5.6x` adaptive scaling) and `TP_p -> TP_d` KV layout transpose.
5. `llm-d` and Kubernetes Gateway API Inference Extension (`InferencePool`, `InferenceObjective`, `EPP`):
   - Validates `InferencePool` (`inference.networking.k8s.io/v1`, port `8000`) and `InferenceObjective` /
     `InferenceModel` (`inference.networking.x-k8s.io/v1alpha2`, priorities `1` and `2`) + Envoy `ext_proc`
     Endpoint Picker (`EPP`, port `9002`, `failureMode: FailClose`) routing across waiting queues, KV cache
     usage, prefix cache hits, and loaded LoRA adapters.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class DisaggClusterGoodputSpec:
    colocated_ttft_rps: float = 3.0
    colocated_tpot_rps: float = 1.6
    prefill_worker_rps: float = 5.6
    decode_worker_rps: float = 10.0
    num_prefill_gpus: int = 2
    num_decode_gpus: int = 1
    ttft_slo_ms: float = 400.0
    tpot_slo_ms: float = 40.0


def evaluate_colocated_vs_disagg_goodput(
    spec: DisaggClusterGoodputSpec = DisaggClusterGoodputSpec(),
) -> Dict[str, float]:
    """Computes colocated vs disaggregated 2P1D goodput and MLPerf v5.0 reference bounds (ASP Ch. 17)."""
    colocated_goodput_per_gpu = min(spec.colocated_ttft_rps, spec.colocated_tpot_rps)
    total_prefill_rps = spec.prefill_worker_rps * spec.num_prefill_gpus
    total_decode_rps = spec.decode_worker_rps * spec.num_decode_gpus
    total_disagg_goodput = min(total_prefill_rps, total_decode_rps)
    total_gpus = spec.num_prefill_gpus + spec.num_decode_gpus
    disagg_goodput_per_gpu = round(total_disagg_goodput / total_gpus, 2)
    disagg_goodput_reported = round(total_disagg_goodput / total_gpus, 1)
    goodput_gain_ratio = round(disagg_goodput_per_gpu / colocated_goodput_per_gpu, 2)

    # Single-stream 70B FP16 decode ceiling on H100 (140 GB weights / 3350 GB/s HBM3)
    h100_70b_weight_load_ms = round((140.0 / 3350.0) * 1000.0, 2)
    h100_70b_max_tok_per_s = round(1000.0 / h100_70b_weight_load_ms, 2)

    return {
        "colocated_ttft_rps": spec.colocated_ttft_rps,
        "colocated_tpot_rps": spec.colocated_tpot_rps,
        "colocated_goodput_per_gpu": colocated_goodput_per_gpu,
        "total_prefill_rps": round(total_prefill_rps, 2),
        "total_decode_rps": round(total_decode_rps, 2),
        "total_disagg_goodput_rps": round(total_disagg_goodput, 2),
        "total_gpus": float(total_gpus),
        "disagg_goodput_per_gpu_exact": disagg_goodput_per_gpu,
        "disagg_goodput_per_gpu_reported": disagg_goodput_reported,
        "per_gpu_goodput_gain_x": goodput_gain_ratio,
        "distserve_max_goodput_gain_x": 7.4,
        "distserve_tighter_slo_x": 12.6,
        "dynamo_680b_nvl72_throughput_gain_x": 30.0,
        "mlperf_v5_70b_ttft_slo_ms": 450.0,
        "mlperf_v5_70b_tpot_slo_ms": 40.0,
        "mlperf_v5_405b_ttft_slo_ms": 6000.0,
        "mlperf_v5_405b_tpot_slo_ms": 175.0,
        "h100_70b_weight_load_ms": h100_70b_weight_load_ms,
        "h100_70b_single_stream_tok_s": h100_70b_max_tok_per_s,
    }


def should_offload_prefill(
    prompt_length: int,
    prefix_cached_length: int,
    prefill_queue_size: int,
    decode_active_reqs: int,
    ttft_slo_ms: int = 500,
    prefill_length_threshold: int = 256,
    prefill_queue_max: int = 10,
    decode_load_threshold: int = 8,
    moderate_eff_len_threshold: int = 64,
) -> Dict[str, object]:
    """Implements Dynamo / B200-tuned conditional prefill offload logic (ASP Ch. 17)."""
    eff_len = max(0, prompt_length - prefix_cached_length)
    long_prefill = eff_len >= prefill_length_threshold
    prefill_available = prefill_queue_size < prefill_queue_max

    if long_prefill and prefill_available:
        offload = True
        reason = "long_prefill_and_pool_available"
    elif decode_active_reqs >= decode_load_threshold and eff_len >= moderate_eff_len_threshold and prefill_available:
        offload = True
        reason = "decode_busy_and_moderate_prefill"
    else:
        offload = False
        reason = "keep_local_on_decode_worker"

    # Dynamo YAML `disaggregated_router` remote prefill score (higher = remote, threshold = 0.5)
    score_len = 0.7 if eff_len > prefill_length_threshold else 0.0
    score_queue = 0.3 if prefill_queue_size <= prefill_queue_max else 0.0
    remote_prefill_score = round(score_len + score_queue, 2)
    yaml_policy_offload = remote_prefill_score > 0.5

    return {
        "effective_prompt_length": eff_len,
        "should_offload": offload,
        "decision_reason": reason,
        "remote_prefill_score": remote_prefill_score,
        "yaml_policy_offload": yaml_policy_offload,
        "ttft_slo_ms": ttft_slo_ms,
    }


@dataclass(frozen=True)
class WorkerRoutingTelemetry:
    worker_id: str
    occupancy_percent: float
    active_reqs: int
    cache_match_flag: bool
    mem_bw_percent: float
    recent_prefix_flag: bool


def compute_smart_router_latency_costs(
    workers: Sequence[WorkerRoutingTelemetry],
) -> Dict[str, object]:
    """Computes simple (2-term) and composite (5-factor) Smart Router latency costs (ASP Ch. 17 Table 17-3)."""
    scored: List[Dict[str, object]] = []
    for w in workers:
        simple_cost = round(0.7 * w.occupancy_percent + 0.3 * w.active_reqs, 2)
        composite_cost = round(
            3.0 * w.occupancy_percent
            + 1.0 * w.active_reqs
            - 10.0 * int(w.cache_match_flag)
            + 0.5 * w.mem_bw_percent
            - 1.0 * int(w.recent_prefix_flag),
            2,
        )
        scored.append(
            {
                "worker_id": w.worker_id,
                "simple_cost": simple_cost,
                "composite_cost": composite_cost,
                "cache_match_flag": w.cache_match_flag,
                "recent_prefix_flag": w.recent_prefix_flag,
            }
        )

    best_simple = min(scored, key=lambda x: float(x["simple_cost"]))["worker_id"]
    best_composite = min(scored, key=lambda x: float(x["composite_cost"]))["worker_id"]
    return {
        "workers": {d["worker_id"]: d for d in scored},
        "selected_simple_worker": best_simple,
        "selected_composite_worker": best_composite,
    }


def evaluate_dynamo_planner_and_qos(
    prefill_replicas: int,
    prefill_queue_len: int,
    prefill_gpu_util_pct: float,
    decode_replicas: int,
    decode_queue_len: int,
    decode_kv_usage_pct: float,
    avg_prefill_ms_per_req: float = 35.0,
    avg_decode_ms_per_req: float = 20.0,
    ttft_slo_ms: float = 500.0,
    total_cluster_workers: int = 20,
) -> Dict[str, object]:
    """Evaluates Dynamo GPU Planner autoscaling decisions, QoS capacity tiers, and early rejection (ASP Ch. 17 & 18)."""
    # Prefill autoscale bounds: min=4, max=12; scale_up: queue>=8 or util>=80; scale_down: queue<=2 and util<=40
    if (prefill_queue_len >= 8 or prefill_gpu_util_pct >= 80.0) and prefill_replicas < 12:
        new_prefill_replicas = min(12, prefill_replicas + 1)
        prefill_action = "scale_up"
    elif (prefill_queue_len <= 2 and prefill_gpu_util_pct <= 40.0) and prefill_replicas > 4:
        new_prefill_replicas = max(4, prefill_replicas - 1)
        prefill_action = "scale_down"
    else:
        new_prefill_replicas = prefill_replicas
        prefill_action = "hold"

    # Decode autoscale bounds: min=8, max=24; scale_up: queue>=16 or kv>=75; scale_down: queue<=4 and kv<=30
    if (decode_queue_len >= 16 or decode_kv_usage_pct >= 75.0) and decode_replicas < 24:
        new_decode_replicas = min(24, decode_replicas + 1)
        decode_action = "scale_up"
    elif (decode_queue_len <= 4 and decode_kv_usage_pct <= 30.0) and decode_replicas > 8:
        new_decode_replicas = max(8, decode_replicas - 1)
        decode_action = "scale_down"
    else:
        new_decode_replicas = decode_replicas
        decode_action = "hold"

    # QoSController estimated TTFT and admission control
    est_ttft_ms = round(
        prefill_queue_len * avg_prefill_ms_per_req + decode_queue_len * avg_decode_ms_per_req,
        2,
    )
    admit_low_priority = est_ttft_ms <= ttft_slo_ms
    admit_high_priority = True

    # QoS reserved fractions (ASP Ch. 18 configs/qos.yaml: premium 10%, standard 30%, free 60%)
    qos_reservations = {
        "premium": {"reserved_fraction": 0.10, "priority": 100, "reserved_workers": int(total_cluster_workers * 0.10)},
        "standard": {"reserved_fraction": 0.30, "priority": 50, "reserved_workers": int(total_cluster_workers * 0.30)},
        "free": {"reserved_fraction": 0.60, "priority": 10, "shared_workers": int(total_cluster_workers * 0.60)},
    }

    return {
        "prefill_action": prefill_action,
        "new_prefill_replicas": new_prefill_replicas,
        "decode_action": decode_action,
        "new_decode_replicas": new_decode_replicas,
        "estimated_ttft_ms": est_ttft_ms,
        "admit_low_priority": admit_low_priority,
        "admit_high_priority": admit_high_priority,
        "qos_reservations": qos_reservations,
    }


def evaluate_nixl_transfer_and_kv_hierarchy(
    prompt_tokens: int = 7500,
    small_block_tokens: int = 16,
    collated_block_tokens: int = 128,
    cluster_rps: float = 16.0,
    kv_gb_per_req: float = 1.5,
) -> Dict[str, object]:
    """Models NIXL 0.5.x transfer lifecycle, page collation, fabric bandwidths, and 4-tier KV offloading (ASP Ch. 4, 17, 18; HLS Ch. 7)."""
    uncollated_wqes = math.ceil(prompt_tokens / small_block_tokens)
    collated_wqes = math.ceil(prompt_tokens / collated_block_tokens)
    uncollated_rdma_ms = 20.0
    collated_rdma_ms = 8.0
    collation_speedup_x = round(uncollated_rdma_ms / collated_rdma_ms, 2)

    aggregate_kv_bw_gb_s = round(cluster_rps * kv_gb_per_req, 2)

    # Interconnect capacities (GB/s)
    fabrics_gb_s = {
        "nvlink4_h100_intra_node": 900.0,
        "nvlink5_b200_intra_rack": 1800.0,
        "nvlink_c2c_grace_superchip": 900.0,
        "ib_ndr_400g_rdma": 50.0,
        "ib_xdr_cx8_800g_rdma": 100.0,
        "pcie_non_rdma_tcp_fallback": 10.0,
    }

    # 250,000-token 70B MHA KV footprint (ASP Ch. 18: 80 layers, 32 heads, 128 dim, FP16=2B)
    floats_per_layer_per_tok = 2 * 32 * 128  # 8,192
    floats_per_tok_all_layers = 80 * floats_per_layer_per_tok  # 655,360
    bytes_per_tok_fp16 = floats_per_tok_all_layers * 2  # 1,310,720 B (~1.31 MB)
    kv_250k_fp16_gb = round((250_000 * bytes_per_tok_fp16) / 1e9, 1)  # 327.7 -> ~328 GB
    kv_250k_fp8_gb = round(kv_250k_fp16_gb / 2.0, 1)

    # Llama-3-70B GQA (8 KV heads) per-token footprint (V12 Ch. 8)
    gqa_bytes_per_tok_fp16 = 2 * 80 * 8 * 128 * 2  # 327,680 B (320 KiB)

    return {
        "nixl_test_buffer_bytes": 1 << 20,  # 1,048,576 B (1 MiB)
        "lmcache_pd_buffer_bytes": 1073741824,  # 1 GiB
        "pd_proxy_port": 7500,
        "pd_peer_init_port": 7300,
        "pd_peer_alloc_port": 7400,
        "ucx_rndv_thresh_bytes": 16384,
        "uncollated_wqes": uncollated_wqes,
        "collated_wqes": collated_wqes,
        "uncollated_rdma_ms": uncollated_rdma_ms,
        "collated_rdma_ms": collated_rdma_ms,
        "collation_speedup_x": collation_speedup_x,
        "aggregate_kv_bw_gb_s": aggregate_kv_bw_gb_s,
        "fits_nvlink4": aggregate_kv_bw_gb_s < fabrics_gb_s["nvlink4_h100_intra_node"],
        "fits_ib_ndr_rdma": aggregate_kv_bw_gb_s < fabrics_gb_s["ib_ndr_400g_rdma"],
        "saturates_non_rdMA_tcp": aggregate_kv_bw_gb_s > fabrics_gb_s["pcie_non_rdma_tcp_fallback"],
        "fabrics_gb_s": fabrics_gb_s,
        "mha_bytes_per_tok_fp16": bytes_per_tok_fp16,
        "gqa_bytes_per_tok_fp16": gqa_bytes_per_tok_fp16,
        "kv_250k_fp16_gb": kv_250k_fp16_gb,
        "kv_250k_fp8_gb": kv_250k_fp8_gb,
        "x86_h100_kv_offload_ttft_speedup_x": 14.0,
        "gh200_vs_x86_kv_offload_ttft_speedup_x": 2.0,
        "gh200_vs_recompute_ttft_speedup_x": 28.0,
        "lmcache_cpu_capacity_multiplier_x": 3.0,
        "lmcache_ssd_capacity_multiplier_x": 50.0,
        "lmcache_throughput_gain_x": 16.0,
        "vllm_baseline_throughput_tok_s": 4700.0,
        "lmcache_offload_throughput_tok_s": 75200.0,
        "splitwise_heterogeneous_rps_gain_x": 2.35,
        "splitwise_iso_perf_cost_reduction_pct": 20.0,
        "hexgen2_max_throughput_gain_x": 2.0,
        "hexgen2_cost_reduction_pct": 30.0,
        "arrow_adaptive_scaling_gain_x": 5.6,
    }


def compute_kv_layout_transpose_plan(
    num_layers: int = 80,
    num_kv_heads: int = 8,
    tp_prefill: int = 2,
    pp_prefill: int = 2,
    tp_decode: int = 4,
    pp_decode: int = 1,
) -> Dict[str, int | bool]:
    """Computes KV cache shard shapes across asymmetric prefill (`TP_p, PP_p`) and decode (`TP_d, PP_d`) pools (ASP Ch. 18)."""
    layers_per_prefill_stage = num_layers // pp_prefill
    kv_heads_per_prefill_rank = num_kv_heads // tp_prefill

    layers_per_decode_stage = num_layers // pp_decode
    kv_heads_per_decode_rank = num_kv_heads // tp_decode

    requires_transpose = (tp_prefill != tp_decode) or (pp_prefill != pp_decode)
    return {
        "tp_prefill": tp_prefill,
        "pp_prefill": pp_prefill,
        "tp_decode": tp_decode,
        "pp_decode": pp_decode,
        "layers_per_prefill_stage": layers_per_prefill_stage,
        "kv_heads_per_prefill_rank": kv_heads_per_prefill_rank,
        "layers_per_decode_stage": layers_per_decode_stage,
        "kv_heads_per_decode_rank": kv_heads_per_decode_rank,
        "requires_transpose": requires_transpose,
    }


@dataclass(frozen=True)
class LLMDReplicaEndpoint:
    pod_name: str
    waiting_requests: int
    kv_cache_usage_pct: float
    cached_prefixes: Tuple[str, ...] = ()
    loaded_loras: Tuple[str, ...] = ()
    role: str = "decode"


def simulate_llmd_epp_routing(
    endpoints: Sequence[LLMDReplicaEndpoint],
    prefix_hash: str,
    requested_lora: str | None = None,
    priority: int = 1,
    kv_saturation_limit_pct: float = 95.0,
) -> Dict[str, object]:
    """Simulates `llm-d` Endpoint Picker (`EPP` on port `9002`) pod scoring over an `InferencePool` (`8000`) (GAK Ch. 4, DAI Ch. 9)."""
    decode_pods = [ep for ep in endpoints if ep.role == "decode"]
    # Admit high priority (priority=1) up to 98% KV, reject low priority (priority>=2) above kv_saturation_limit_pct
    eligible = [
        ep
        for ep in decode_pods
        if ep.kv_cache_usage_pct < (98.0 if priority == 1 else kv_saturation_limit_pct)
    ]
    if not eligible:
        return {
            "admitted": False,
            "http_status": 429,
            "selected_pod": None,
            "target_port": 8000,
            "epp_port": 9002,
            "failure_mode": "FailClose",
        }

    def score_pod(ep: LLMDReplicaEndpoint) -> float:
        prefix_bonus = 50.0 if prefix_hash in ep.cached_prefixes else 0.0
        lora_bonus = 25.0 if (requested_lora and requested_lora in ep.loaded_loras) else 0.0
        queue_penalty = 4.0 * ep.waiting_requests
        kv_penalty = 0.5 * ep.kv_cache_usage_pct
        return round(prefix_bonus + lora_bonus - queue_penalty - kv_penalty, 2)

    scored = {ep.pod_name: score_pod(ep) for ep in eligible}
    best_pod = max(eligible, key=score_pod)

    return {
        "admitted": True,
        "http_status": 200,
        "selected_pod": best_pod.pod_name,
        "pod_scores": scored,
        "prefix_hit": prefix_hash in best_pod.cached_prefixes,
        "lora_hit": bool(requested_lora and requested_lora in best_pod.loaded_loras),
        "target_port": 8000,
        "epp_port": 9002,
        "failure_mode": "FailClose",
    }


if __name__ == "__main__":
    gp = evaluate_colocated_vs_disagg_goodput()
    print(f"Colocated goodput: {gp['colocated_goodput_per_gpu']} RPS/GPU -> 2P1D Disagg: {gp['disagg_goodput_per_gpu_reported']} RPS/GPU")
    nx = evaluate_nixl_transfer_and_kv_hierarchy()
    print(f"NIXL 7.5k-token collation: {nx['uncollated_rdma_ms']} ms -> {nx['collated_rdma_ms']} ms ({nx['collation_speedup_x']}x)")
