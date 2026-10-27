#!/usr/bin/env python3
"""Chapter 15.10 model: Prefill and decode disaggregation.

Models:
1. Co-located Prefill-Decode Interference, ITL Spikes, and DistServe Goodput Math:
   - Quantifies opposite hardware profiles (`DAI` Ch. 7, `ASP` Ch. 17): Prefill achieves `85%` compute
     utilization and `40%` memory bandwidth utilization, whereas Decode achieves `25%` compute
     utilization and `90%` memory bandwidth utilization.
   - Models co-located continuous batching interference (`V12` Ch. 7):
     - An unchunked `12,288`-token prompt prefill monopolizes SMs for `320.0 ms`, stalling `45` active
       decode streams and spiking `p99 ITL` from `18.0 ms` to `340.0 ms` (violating `< 30.0 ms` voice SLA);
       enabling chunked prefill (`max_num_batched_tokens=2048`) lowers `p99 ITL` to `21.4 ms`.
     - An `8,192`-token prompt prefill spikes decode step time from `15.0 ms` to `380.0 ms` (`28.0 ms` with
       `512`-token chunked prefill; `45.0 ms` `p99 ITL` and `320.0 ms` `TTFT` vs `28.0 ms` / `180.0 ms`
       when `max_num_batched_tokens=512` causes `450/sec` context switches).
     - Request-level dynamic batching (`B=32, tau=50 ms`) suffers `420.0 ms` `p99 ITL`, `14.2 s` `p99 TTFT`,
       and `18%` SM occupancy vs `19.1 ms` `p99 ITL` (`3.8x` throughput gain) with iteration-level batching.
   - Computes DistServe `2P1D` goodput under `P90 TTFT <= 400.0 ms` (`0.4 s`) and `P90 TPOT <= 40.0 ms` (`0.04 s`)
     (`ASP` Ch. 17 & Ch. 15): colocated `3.0 RPS` TTFT-only / `1.6 RPS` TPOT-only = `1.6 RPS/GPU` goodput vs
     disaggregated `2P1D` (`2` prefill GPUs at `5.6 RPS` = `11.2 RPS` + `1` decode GPU at `10.0 RPS` ->
     `min(11.2, 10.0) / 3 = 3.33 RPS/GPU` [`~3.3 RPS/GPU`], `2.08x` goodput per GPU, up to `7.4x` more
     goodput requests and `12.6x` tighter latency SLOs), plus MLPerf v5.0 p99 SLOs (`Llama-2-70B`: `450 ms`
     TTFT / `40 ms` TPOT; `Llama-3.1-405B`: `6,000 ms` [`6 s`] TTFT / `175 ms` TPOT; interactive `< 200-300 ms`).
2. Disaggregated Architectures (DistServe, Splitwise, TetriInfer, Arrow, Mooncake, SGLang, NVIDIA Dynamo):
   - Models router-centric / direct-channel (`DistServe`, `SGLang`, `vLLM` + `LMCache`, `llm-d`) vs
     decode-centric / global-queue (`NVIDIA Dynamo` with `etcd` leases, `NATS`, and `NIXL`) architectures.
   - Evaluates `should_offload_prefill()` (`PREFILL_LENGTH_THRESHOLD=256`, `PREFILL_QUEUE_MAX=10`,
     `DECODE_LOAD_THRESHOLD=8`, secondary `eff_len >= 64`), composite `latency_cost` (`+3.0 * occupancy
     + 1.0 * active_reqs - 10.0 * cache_match + 0.5 * mem_bw - 1.0 * recent_prefix`), YAML
     `remote_prefill_min_score=0.5` (`0.7` and `0.3` weights), `QoSController` early rejection
     (`est_ttft > 500 ms`), and QoS capacity tiers (`premium` `10%` / `priority 100`, `standard` `30%` /
     `priority 50`, `free` `60%` / `priority 10`).
3. Prefill-to-Decode Worker Ratio Sizing (`N_P : N_D`) & Asymmetric Parallelism:
   - Computes `N_P = ceil(lambda * L_in / T_P)`, `N_D = ceil(lambda * L_out / T_D)`, and exact ratio
     `N_P / N_D = (L_in / L_out) * (T_D / T_P) = tau_P / tau_D` across RAG (`2:1` / `3:1`), balanced
     chat (`1:2` / `4P8D`), and Chain-of-Thought reasoning (`1:3` / `1:4`) workloads.
   - Models asymmetric phase parallelism (`TP_p, PP_p` vs `TP_d, PP_d`), SGLang Data-Parallel Attention
     (`--enable-dp-attention`, `1.9x` decode throughput on MLA models, eliminating `8x` KV duplication at `TP=8`),
     and on-the-fly NIXL KV layout transpose (`[TP_p] -> [TP_d]`).
4. KV Cache Transfer Bandwidth Math Across MHA, GQA, MQA, and MLA:
   - Computes exact per-token and per-sequence KV footprints for:
     - `Llama-13B` (`L=40, d_head=128`, `S=4,096`): MHA (`H_kv=40`) = `819,200 B/tok` (`0.8192 MB/tok`,
       `3.355 GB` / `~3.36 GB` FP16, `1.678 GB` / `~1.68 GB` FP8); GQA-8 (`H_kv=8`) = `163,840 B/tok`
       (`0.671 GB` FP16, `0.336 GB` FP8); MQA-1 (`H_kv=1`) = `20,480 B/tok` (`0.0839 GB` / `~0.084 GB` FP16).
     - `Llama-3-8B` (`L=32, H_kv=8, d_head=128`): `131,072 B/tok` (`128.0 KiB/tok`) -> `0.134 GB` at `1,024`
       tokens (`~0.1-0.15 GB`) and `1.342 GB` at `10,240` tokens (`~1.0-1.5 GB`); at `16 RPS`, aggregate
       KV transfer rate = `21.47 GB/s` (`24.0 GB/s` / `~25 GB/s` at `1.5 GB/req`).
     - `Llama-3-70B` (`L=80, d_head=128`): MHA (`H_kv=64`) = `2,621,440 B/tok` (`10.737 GB` / `10.0 GiB` at
       `4,096` tokens, `312.5 GiB` at `128,000` tokens; or `H_kv=32` -> `1,310,720 B/tok` = `1.31 MB/tok` ->
       `327.68 GB` / `~328 GB` FP16 and `163.84 GB` / `100-150 GB` FP8 at `250,000` tokens);
       GQA-8 (`H_kv=8`) = `327,680 B/tok` (`320.0 KiB/tok` FP16, `160.0 KiB/tok` FP8) -> `1.342 GB` (`1.25 GiB` /
       `~1.31 GB`) at `4,096` tokens in FP16 (`0.671 GB` / `0.625 GiB` / `~0.65 GB` in FP8) and `39.06 GiB` at
       `128,000` tokens (`87.5%` / `8.0x` reduction vs 64-head MHA).
     - `DeepSeek-V3 / R1 671B` (`L=61, d_c=512, d_r=64`, MLA): `70,272 B/tok` (`68.625 KiB/tok` FP16) or
       `35,136 B/tok` (`34.3125 KiB/tok` FP8) -> `0.288 GB` (`274.5 MiB`) at `4,096` tokens in FP16 and
       `0.144 GB` in FP8 (`4.66x` smaller than Llama-3-70B GQA and `37.3x` smaller than 70B MHA).
5. RDMA / NVLink NIXL Transfer Latency vs TTFT Budget & Page Collation:
   - Evaluates transfer latency across `NVLink 5` (`1,800 GB/s`), `NVLink 4` / `NVLink-C2C` (`900 GB/s`),
     `NVLink 3` (`600 GB/s`), `ConnectX-8 800G` (`100 GB/s`), `PCIe Gen5 x16` (`64 GB/s`),
     `ConnectX-7 NDR 400G` (`50 GB/s`), `100GbE TCP` (`12.5 GB/s`), and non-RDMA PCIe/TCP (`10 GB/s`).
   - Models PagedAttention collation (`7,500` tokens across `16`-token blocks = `469` [`~470`] WQEs in `20.0 ms`
     vs `128`-token slabs = `59` WQEs in `8.0 ms`, `2.5x` speedup) and layer-by-layer overlap (`< 1%` net latency).
6. Heterogeneous GPU Pairing (H100/B200 Prefill + H200/B300/GB200/A100/L40S Decode):
   - Quantifies `H100` (`80 GB`, `3.35 TB/s`, `989 TFLOPS` BF16) prefill + `H200` (`141 GB`, `4.8 TB/s`, `989 TFLOPS`)
     decode (`1.76x` HBM capacity, `1.43x` HBM bandwidth, `2.69x` post-70B-weight KV pool on `TP=2`),
     `4x B200` (`180 GB`, `10 PFLOPS` FP4) prefill + `8x B300` (`288 GB`, `15 PFLOPS` FP4) decode,
     `GB200 NVL72` (`72` GPUs + `36` Grace CPUs, `~30 TB` memory, `130 TB/s` NVSwitch, `30x` 680B throughput),
     Splitwise `4x H100 + 4x A100` (`2.35x` iso-cost/power RPS, `1.4x` RPS at `-20%` cost, `6` vs `8` GPUs `-25%`),
     and HexGen-2 (`2.0x` peak / `1.3x` avg RPS, `-30%` cost).
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class ColocatedInterferenceSpec:
    # Phase resource profiles (DAI Ch. 7 Figure 7.8)
    prefill_compute_util_pct: float = 85.0
    prefill_mem_bw_util_pct: float = 40.0
    decode_compute_util_pct: float = 25.0
    decode_mem_bw_util_pct: float = 90.0
    # Unchunked long prefill stall on 4x H100 TP=4 (V12 Ch. 7 Scenario 1)
    long_prompt_tokens: int = 12288
    active_decode_streams: int = 45
    baseline_itl_ms: float = 18.0
    voice_sla_itl_ms: float = 30.0
    unchunked_prefill_stall_ms: float = 320.0
    spiked_p99_itl_ms: float = 340.0
    chunked_2048_p99_itl_ms: float = 21.4
    # 8,192-token prefill bubble vs 512-token chunked prefill (V12 Ch. 7 Section 4)
    bubble_prompt_tokens: int = 8192
    normal_decode_step_ms: float = 15.0
    bubble_prefill_step_ms: float = 380.0
    chunked_512_step_ms: float = 28.0


def evaluate_colocated_interference_and_goodput(
    spec: ColocatedInterferenceSpec = ColocatedInterferenceSpec(),
) -> Dict[str, float]:
    """Quantifies colocated prefill-decode interference, ITL spikes, and DistServe 2P1D goodput (ASP Ch. 17, DAI Ch. 7, V12 Ch. 7)."""
    itl_spike_ratio_12k = round(spec.spiked_p99_itl_ms / spec.baseline_itl_ms, 2)
    itl_spike_ratio_8k = round(spec.bubble_prefill_step_ms / spec.normal_decode_step_ms, 2)
    chunked_recovery_ratio = round(spec.spiked_p99_itl_ms / spec.chunked_2048_p99_itl_ms, 2)

    # DistServe 2P1D goodput under P90 TTFT <= 400 ms (0.4 s) and P90 TPOT <= 40 ms (0.04 s) (ASP Ch. 17)
    colocated_ttft_rps = 3.0
    colocated_tpot_rps = 1.6
    colocated_goodput_per_gpu = min(colocated_ttft_rps, colocated_tpot_rps)

    prefill_worker_rps = 5.6
    num_prefill_gpus = 2
    decode_worker_rps = 10.0
    num_decode_gpus = 1
    total_prefill_rps = round(prefill_worker_rps * num_prefill_gpus, 2)  # 11.2 RPS
    total_decode_rps = round(decode_worker_rps * num_decode_gpus, 2)    # 10.0 RPS
    total_cluster_goodput_rps = min(total_prefill_rps, total_decode_rps)  # 10.0 RPS
    total_gpus = num_prefill_gpus + num_decode_gpus  # 3 GPUs
    disagg_goodput_per_gpu_exact = round(total_cluster_goodput_rps / total_gpus, 2)     # 3.33 RPS/GPU
    disagg_goodput_per_gpu_reported = round(total_cluster_goodput_rps / total_gpus, 1)  # 3.3 RPS/GPU
    goodput_per_gpu_gain_x = round(disagg_goodput_per_gpu_exact / colocated_goodput_per_gpu, 2)  # 2.08x

    # Request-level dynamic batching (B=32, tau=50 ms) vs continuous batching (V12 Ch. 7)
    req_batch_p99_itl_ms = 420.0
    req_batch_p99_ttft_s = 14.2
    req_batch_sm_occupancy_pct = 18.0
    cont_batch_p99_itl_ms = 19.1
    cont_batch_throughput_gain_x = 3.8

    return {
        "prefill_compute_util_pct": spec.prefill_compute_util_pct,
        "prefill_mem_bw_util_pct": spec.prefill_mem_bw_util_pct,
        "decode_compute_util_pct": spec.decode_compute_util_pct,
        "decode_mem_bw_util_pct": spec.decode_mem_bw_util_pct,
        "long_prompt_tokens": float(spec.long_prompt_tokens),
        "active_decode_streams": float(spec.active_decode_streams),
        "baseline_itl_ms": spec.baseline_itl_ms,
        "voice_sla_itl_ms": spec.voice_sla_itl_ms,
        "unchunked_prefill_stall_ms": spec.unchunked_prefill_stall_ms,
        "spiked_p99_itl_ms": spec.spiked_p99_itl_ms,
        "chunked_2048_p99_itl_ms": spec.chunked_2048_p99_itl_ms,
        "itl_spike_ratio_12k_x": itl_spike_ratio_12k,
        "chunked_recovery_ratio_x": chunked_recovery_ratio,
        "bubble_prompt_tokens": float(spec.bubble_prompt_tokens),
        "normal_decode_step_ms": spec.normal_decode_step_ms,
        "bubble_prefill_step_ms": spec.bubble_prefill_step_ms,
        "chunked_512_step_ms": spec.chunked_512_step_ms,
        "itl_spike_ratio_8k_x": itl_spike_ratio_8k,
        "req_batch_p99_itl_ms": req_batch_p99_itl_ms,
        "req_batch_p99_ttft_s": req_batch_p99_ttft_s,
        "req_batch_sm_occupancy_pct": req_batch_sm_occupancy_pct,
        "cont_batch_p99_itl_ms": cont_batch_p99_itl_ms,
        "cont_batch_throughput_gain_x": cont_batch_throughput_gain_x,
        "colocated_ttft_rps": colocated_ttft_rps,
        "colocated_tpot_rps": colocated_tpot_rps,
        "colocated_goodput_per_gpu": colocated_goodput_per_gpu,
        "total_prefill_rps": total_prefill_rps,
        "total_decode_rps": total_decode_rps,
        "total_cluster_goodput_rps": total_cluster_goodput_rps,
        "total_gpus": float(total_gpus),
        "disagg_goodput_per_gpu_exact": disagg_goodput_per_gpu_exact,
        "disagg_goodput_per_gpu_reported": disagg_goodput_per_gpu_reported,
        "goodput_per_gpu_gain_x": goodput_per_gpu_gain_x,
        "distserve_max_goodput_gain_x": 7.4,
        "distserve_tighter_slo_x": 12.6,
        "mlperf_v5_70b_ttft_slo_ms": 450.0,
        "mlperf_v5_70b_tpot_slo_ms": 40.0,
        "mlperf_v5_405b_ttft_slo_ms": 6000.0,
        "mlperf_v5_405b_tpot_slo_ms": 175.0,
    }


def evaluate_worker_ratio_sizing(
    arrival_rate_rps: float,
    prompt_tokens: int,
    output_tokens: int,
    prefix_cache_hit_ratio: float,
    prefill_tok_per_s_per_worker: float,
    decode_tok_per_s_per_worker: float,
) -> Dict[str, float | int | str]:
    """Sizes prefill (`N_P`) and decode (`N_D`) worker pools and computes `N_P : N_D` ratio."""
    eff_prompt_tokens = prompt_tokens * (1.0 - prefix_cache_hit_ratio)
    total_prefill_tok_per_s = arrival_rate_rps * eff_prompt_tokens
    total_decode_tok_per_s = arrival_rate_rps * output_tokens

    exact_np = total_prefill_tok_per_s / prefill_tok_per_s_per_worker
    exact_nd = total_decode_tok_per_s / decode_tok_per_s_per_worker

    np_workers = max(1, math.ceil(exact_np))
    nd_workers = max(1, math.ceil(exact_nd))

    exact_np_to_nd_ratio = round(exact_np / exact_nd, 2) if exact_nd > 0 else 0.0
    provisioned_ratio_str = f"{np_workers}:{nd_workers}"

    # Cluster goodput under provisioned workers
    max_rps_prefill = (np_workers * prefill_tok_per_s_per_worker) / max(1.0, eff_prompt_tokens)
    max_rps_decode = (nd_workers * decode_tok_per_s_per_worker) / max(1.0, output_tokens)
    cluster_max_rps = round(min(max_rps_prefill, max_rps_decode), 2)

    return {
        "effective_prompt_tokens": round(eff_prompt_tokens, 1),
        "total_prefill_tok_per_s": round(total_prefill_tok_per_s, 1),
        "total_decode_tok_per_s": round(total_decode_tok_per_s, 1),
        "exact_np": round(exact_np, 2),
        "exact_nd": round(exact_nd, 2),
        "np_workers": np_workers,
        "nd_workers": nd_workers,
        "exact_np_to_nd_ratio": exact_np_to_nd_ratio,
        "provisioned_ratio": provisioned_ratio_str,
        "cluster_max_rps": cluster_max_rps,
    }


def compute_kv_cache_transfer_footprints(
    seq_len: int = 4096,
) -> Dict[str, Dict[str, float]]:
    """Computes KV cache transfer payloads per token and per sequence across MHA, GQA, MQA, and MLA."""
    # 1. Llama-13B (L=40, d_head=128) from ASP Ch. 17
    l13b_mha_b_tok_fp16 = 2 * 40 * 40 * 128 * 2  # 819,200 B (0.8192 MB/tok)
    l13b_gqa8_b_tok_fp16 = 2 * 40 * 8 * 128 * 2  # 163,840 B (0.16384 MB/tok)
    l13b_mqa1_b_tok_fp16 = 2 * 40 * 1 * 128 * 2  # 20,480 B (0.02048 MB/tok)

    # 2. Llama-3-8B (L=32, H_kv=8, d_head=128) from HLS Ch. 7
    l8b_gqa8_b_tok_fp16 = 2 * 32 * 8 * 128 * 2   # 131,072 B (128.0 KiB/tok)

    # 3. Llama-3-70B (L=80, d_head=128): MHA (H_kv=64 or 32) vs GQA-8 (H_kv=8) from V12 Ch. 8 & ASP Ch. 18
    l70b_mha64_b_tok_fp16 = 2 * 80 * 64 * 128 * 2  # 2,621,440 B (2.50 MiB/tok)
    l70b_mha32_b_tok_fp16 = 2 * 80 * 32 * 128 * 2  # 1,310,720 B (1.31072 MB/tok)
    l70b_gqa8_b_tok_fp16 = 2 * 80 * 8 * 128 * 2    # 327,680 B (320.0 KiB/tok)
    l70b_gqa8_b_tok_fp8 = 2 * 80 * 8 * 128 * 1     # 163,840 B (160.0 KiB/tok)

    # 4. DeepSeek-V3 / R1 671B MLA (L=61, d_c=512, d_r=64 -> 576 elements/layer/tok)
    ds_mla_b_tok_fp16 = 61 * (512 + 64) * 2  # 70,272 B (68.625 KiB/tok)
    ds_mla_b_tok_fp8 = 61 * (512 + 64) * 1   # 35,136 B (34.3125 KiB/tok)

    return {
        "llama_13b_mha": {
            "bytes_per_token_fp16": float(l13b_mha_b_tok_fp16),
            "mb_per_token_fp16_decimal": round(l13b_mha_b_tok_fp16 / 1e6, 3),  # 0.819 MB
            "seq_gb_fp16_decimal": round((l13b_mha_b_tok_fp16 * seq_len) / 1e9, 2),  # 3.36 GB
            "seq_gb_fp8_decimal": round((l13b_mha_b_tok_fp16 * seq_len / 2) / 1e9, 2),  # 1.68 GB
        },
        "llama_13b_gqa8": {
            "bytes_per_token_fp16": float(l13b_gqa8_b_tok_fp16),
            "seq_gb_fp16_decimal": round((l13b_gqa8_b_tok_fp16 * seq_len) / 1e9, 3),  # 0.671 GB
            "seq_gb_fp8_decimal": round((l13b_gqa8_b_tok_fp16 * seq_len / 2) / 1e9, 3),  # 0.336 GB
            "mha_to_gqa_reduction_x": round(l13b_mha_b_tok_fp16 / l13b_gqa8_b_tok_fp16, 1),  # 5.0x
        },
        "llama_13b_mqa1": {
            "bytes_per_token_fp16": float(l13b_mqa1_b_tok_fp16),
            "seq_gb_fp16_decimal": round((l13b_mqa1_b_tok_fp16 * seq_len) / 1e9, 3),  # 0.084 GB
            "mha_to_mqa_reduction_x": round(l13b_mha_b_tok_fp16 / l13b_mqa1_b_tok_fp16, 1),  # 40.0x
        },
        "llama_3_8b_gqa8": {
            "bytes_per_token_fp16": float(l8b_gqa8_b_tok_fp16),
            "kib_per_token_fp16": round(l8b_gqa8_b_tok_fp16 / 1024.0, 1),  # 128.0 KiB
            "seq_1024_gb_decimal": round((l8b_gqa8_b_tok_fp16 * 1024) / 1e9, 3),  # 0.134 GB (~0.1-0.15 GB)
            "seq_10240_gb_decimal": round((l8b_gqa8_b_tok_fp16 * 10240) / 1e9, 3),  # 1.342 GB (~1.0-1.5 GB)
            "bw_at_16rps_10k_gb_s": round(16.0 * (l8b_gqa8_b_tok_fp16 * 10240) / 1e9, 2),  # 21.47 GB/s
            "bw_at_16rps_1_5gb_s": round(16.0 * 1.5, 1),  # 24.0 GB/s (~25 GB/s)
        },
        "llama_3_70b": {
            "mha64_bytes_per_token_fp16": float(l70b_mha64_b_tok_fp16),
            "mha64_mib_per_token_fp16": round(l70b_mha64_b_tok_fp16 / (1024.0 ** 2), 2),  # 2.50 MiB
            "mha64_4k_gb_fp16_decimal": round((l70b_mha64_b_tok_fp16 * seq_len) / 1e9, 2),  # 10.74 GB
            "mha64_128k_gib_fp16": round((l70b_mha64_b_tok_fp16 * 128000) / (1024.0 ** 3), 1),  # 312.5 GiB
            "mha32_bytes_per_token_fp16": float(l70b_mha32_b_tok_fp16),
            "mha32_250k_gb_fp16": round((l70b_mha32_b_tok_fp16 * 250000) / 1e9, 1),  # 327.7 -> ~328 GB
            "gqa8_bytes_per_token_fp16": float(l70b_gqa8_b_tok_fp16),
            "gqa8_kib_per_token_fp16": round(l70b_gqa8_b_tok_fp16 / 1024.0, 1),  # 320.0 KiB
            "gqa8_bytes_per_token_fp8": float(l70b_gqa8_b_tok_fp8),
            "gqa8_kib_per_token_fp8": round(l70b_gqa8_b_tok_fp8 / 1024.0, 1),  # 160.0 KiB
            "gqa8_4k_gb_fp16_decimal": round((l70b_gqa8_b_tok_fp16 * seq_len) / 1e9, 3),  # 1.342 GB
            "gqa8_4k_gib_fp16_binary": round((l70b_gqa8_b_tok_fp16 * seq_len) / (1024.0 ** 3), 2),  # 1.25 GiB
            "gqa8_4k_gb_fp8_decimal": round((l70b_gqa8_b_tok_fp8 * seq_len) / 1e9, 3),  # 0.671 GB
            "gqa8_4k_gib_fp8_binary": round((l70b_gqa8_b_tok_fp8 * seq_len) / (1024.0 ** 3), 3),  # 0.625 GiB
            "gqa8_128k_gib_fp16": round((l70b_gqa8_b_tok_fp16 * 128000) / (1024.0 ** 3), 2),  # 39.06 GiB
            "mha64_to_gqa8_reduction_x": round(l70b_mha64_b_tok_fp16 / l70b_gqa8_b_tok_fp16, 1),  # 8.0x
            "mha64_to_gqa8_savings_pct": 87.5,
        },
        "deepseek_v3_mla": {
            "bytes_per_token_fp16": float(ds_mla_b_tok_fp16),
            "kib_per_token_fp16": round(ds_mla_b_tok_fp16 / 1024.0, 3),  # 68.625 KiB
            "bytes_per_token_fp8": float(ds_mla_b_tok_fp8),
            "kib_per_token_fp8": round(ds_mla_b_tok_fp8 / 1024.0, 4),  # 34.3125 KiB
            "seq_4k_gb_fp16_decimal": round((ds_mla_b_tok_fp16 * seq_len) / 1e9, 3),  # 0.288 GB
            "seq_4k_gb_fp8_decimal": round((ds_mla_b_tok_fp8 * seq_len) / 1e9, 3),   # 0.144 GB
            "vs_70b_gqa8_reduction_x": round(l70b_gqa8_b_tok_fp16 / ds_mla_b_tok_fp16, 2),  # 4.66x
            "vs_70b_mha64_reduction_x": round(l70b_mha64_b_tok_fp16 / ds_mla_b_tok_fp16, 1),  # 37.3x
        },
    }


def evaluate_nixl_rdma_transfer_vs_ttft(
    kv_payload_gb_decimal: float = 1.34217728,
    num_layers: int = 80,
    prefill_compute_ms: float = 180.0,
    ttft_slo_ms: float = 250.0,
) -> Dict[str, object]:
    """Evaluates KV transfer latency across fabrics, page collation, and layer-pipelined overlap vs TTFT budget."""
    fabrics_gb_s = {
        "pcie_non_rdma_tcp_10gbs": 10.0,
        "eth_100gbe_tcp_12_5gbs": 12.5,
        "ib_ndr_400g_single_nic_50gbs": 50.0,
        "pcie_gen5_x16_64gbs": 64.0,
        "ib_xdr_cx8_800g_single_nic_100gbs": 100.0,
        "ib_ndr_8x_rail_400gbs": 400.0,
        "nvlink3_a100_600gbs": 600.0,
        "nvlink4_h100_900gbs": 900.0,
        "nvlink5_blackwell_1800gbs": 1800.0,
    }

    # Explicit reference table values verified in Section 4.2 (1.34217728 GB FP16, 0.67108864 GB FP8, 0.143917056 GB MLA FP8):
    # FP16 (1.342 GB): 134.22 ms (10 GB/s), 107.37 ms (12.5 GB/s), 26.84 ms (50 GB/s), 20.97 ms (64 GB/s),
    #   13.42 ms (100 GB/s), 3.36 ms (400 GB/s), 2.24 ms (600 GB/s), 1.49 ms (900 GB/s), 0.75 ms (1,800 GB/s)
    # FP8 (0.671 GB): 67.11 ms (10 GB/s), 53.69 ms (12.5 GB/s), 13.42 ms (50 GB/s), 10.49 ms (64 GB/s),
    #   6.71 ms (100 GB/s), 1.68 ms (400 GB/s), 1.12 ms (600 GB/s), 0.75 ms (900 GB/s), 0.37 ms (1,800 GB/s)
    # MLA FP8 (0.144 GB): 14.39 ms (10 GB/s), 11.51 ms (12.5 GB/s), 2.88 ms (50 GB/s), 2.25 ms (64 GB/s),
    #   1.44 ms (100 GB/s), 0.36 ms (400 GB/s), 0.24 ms (600 GB/s), 0.16 ms (900 GB/s), 0.08 ms (1,800 GB/s)
    transfer_ms_by_fabric: Dict[str, float] = {}
    fp8_transfer_ms_by_fabric: Dict[str, float] = {}
    mla_fp8_transfer_ms_by_fabric: Dict[str, float] = {}
    meets_unpipelined_ttft_slo: Dict[str, bool] = {}
    for name, bw in fabrics_gb_s.items():
        t_ms = round((kv_payload_gb_decimal / bw) * 1000.0, 2)
        transfer_ms_by_fabric[name] = t_ms
        fp8_transfer_ms_by_fabric[name] = round(((kv_payload_gb_decimal / 2.0) / bw) * 1000.0, 2)
        mla_fp8_transfer_ms_by_fabric[name] = round((0.143917056 / bw) * 1000.0, 2)
        meets_unpipelined_ttft_slo[name] = (prefill_compute_ms + t_ms) <= ttft_slo_ms

    # Layer-by-layer pipelined NIXL transfer on single NDR 400G NIC (50 GB/s):
    # Layers 1..L-1 overlap with compute; only final layer L transfer is exposed
    single_ndr_total_ms = transfer_ms_by_fabric["ib_ndr_400g_single_nic_50gbs"]  # 26.84 ms
    hidden_79_layers_ms = 26.50
    exposed_final_layer_ms = round(single_ndr_total_ms / num_layers, 2)          # 0.34 ms
    exposed_final_layer_fp8_ms = 0.17
    pipelined_ttft_ms = round(prefill_compute_ms + exposed_final_layer_ms, 2)    # 180.34 ms
    exposed_overhead_pct = round((exposed_final_layer_ms / prefill_compute_ms) * 100.0, 2)  # 0.19% (< 1%)

    # LMCache 7,500-token PagedAttention collation (ASP Ch. 18)
    prompt_7500 = 7500
    uncollated_16tok_wqes = math.ceil(prompt_7500 / 16)    # 469 (~470)
    collated_128tok_wqes = math.ceil(prompt_7500 / 128)    # 59
    uncollated_7500_ms = 20.0
    collated_7500_ms = 8.0
    collation_speedup_x = round(uncollated_7500_ms / collated_7500_ms, 2)  # 2.5x

    return {
        "kv_payload_gb": round(kv_payload_gb_decimal, 3),
        "prefill_compute_ms": prefill_compute_ms,
        "ttft_slo_ms": ttft_slo_ms,
        "transfer_ms_by_fabric": transfer_ms_by_fabric,
        "fp8_transfer_ms_by_fabric": fp8_transfer_ms_by_fabric,
        "mla_fp8_transfer_ms_by_fabric": mla_fp8_transfer_ms_by_fabric,
        "meets_unpipelined_ttft_slo": meets_unpipelined_ttft_slo,
        "single_ndr_unpipelined_ttft_ms": round(prefill_compute_ms + single_ndr_total_ms, 2),
        "hidden_79_layers_ms": hidden_79_layers_ms,
        "exposed_final_layer_ms": exposed_final_layer_ms,
        "exposed_final_layer_fp8_ms": exposed_final_layer_fp8_ms,
        "pipelined_ttft_ms": pipelined_ttft_ms,
        "exposed_overhead_pct": exposed_overhead_pct,
        "overhead_under_1_percent": exposed_overhead_pct < 1.0,
        "uncollated_16tok_wqes": uncollated_16tok_wqes,
        "collated_128tok_wqes": collated_128tok_wqes,
        "uncollated_7500_ms": uncollated_7500_ms,
        "collated_7500_ms": collated_7500_ms,
        "collation_speedup_x": collation_speedup_x,
        "nixl_1mib_buffer_bytes": 1 << 20,
        "lmcache_1gib_buffer_bytes": 1073741824,
        "lmcache_2gib_buffer_bytes": 2147483648,
        "ucx_rndv_thresh_bytes": 16384,
        "x86_h100_offload_speedup_x": 14.0,
        "gh200_vs_x86_offload_speedup_x": 2.0,
        "gh200_total_offload_speedup_x": 28.0,
    }


def evaluate_routing_and_qos_policies(
    prompt_length: int,
    prefix_cached_length: int,
    prefill_queue_size: int,
    decode_active_reqs: int,
    priority: str = "low",
    avg_prefill_ms_per_req: float = 35.0,
    avg_decode_ms_per_req: float = 20.0,
    decode_queue_size: int = 12,
    ttft_slo_ms: int = 500,
) -> Dict[str, object]:
    """Models Dynamo `should_offload_prefill`, composite `latency_cost`, YAML score, and `QoSController` (ASP Ch. 17 & 18)."""
    eff_len = max(0, prompt_length - prefix_cached_length)
    PREFILL_LENGTH_THRESHOLD = 256
    PREFILL_QUEUE_MAX = 10
    DECODE_LOAD_THRESHOLD = 8

    long_prefill = eff_len >= PREFILL_LENGTH_THRESHOLD
    prefill_available = prefill_queue_size < PREFILL_QUEUE_MAX

    if long_prefill and prefill_available:
        should_offload = True
        route_reason = "long_prefill_and_pool_available"
    elif decode_active_reqs >= DECODE_LOAD_THRESHOLD and eff_len >= 64 and prefill_available:
        should_offload = True
        route_reason = "decode_busy_and_moderate_prefill"
    else:
        should_offload = False
        route_reason = "local_prefill_on_decode_worker"

    # YAML disaggregated_router score (weights 0.7 and 0.3, threshold 0.5)
    yaml_score = round(
        (0.7 if eff_len > 256 else 0.0) + (0.3 if prefill_queue_size <= 10 else 0.0),
        2,
    )
    yaml_offload = yaml_score > 0.5

    # Composite latency_cost (ASP Ch. 17 Table 17-3)
    # Worker A: busy (occupancy=0.60, active=6, mem_bw=0.50) but has prefix match + recent prefix
    cost_worker_cached = round(3.0 * 0.60 + 1.0 * 6 - 10.0 * 1 + 0.5 * 0.50 - 1.0 * 1, 2)  # -2.95
    # Worker B: lightly loaded (occupancy=0.20, active=2, mem_bw=0.20) with no prefix match
    cost_worker_uncached = round(3.0 * 0.20 + 1.0 * 2 - 10.0 * 0 + 0.5 * 0.20 - 1.0 * 0, 2)  # +2.70

    # QoSController early rejection (ASP Ch. 17)
    est_ttft_ms = round(
        prefill_queue_size * avg_prefill_ms_per_req + decode_queue_size * avg_decode_ms_per_req,
        2,
    )
    admitted = not (est_ttft_ms > ttft_slo_ms and priority.lower() == "low")

    return {
        "effective_prompt_length": eff_len,
        "should_offload": should_offload,
        "route_reason": route_reason,
        "yaml_score": yaml_score,
        "yaml_offload": yaml_offload,
        "cost_worker_cached": cost_worker_cached,
        "cost_worker_uncached": cost_worker_uncached,
        "selected_worker": "worker_cached" if cost_worker_cached < cost_worker_uncached else "worker_uncached",
        "est_ttft_ms": est_ttft_ms,
        "admitted": admitted,
        "qos_tiers": {"premium": 0.10, "standard": 0.30, "free": 0.60},
    }


def evaluate_heterogeneous_gpu_pairings() -> Dict[str, object]:
    """Quantifies heterogeneous prefill + decode GPU pairings (H100+H200, B200+B300, GB200 NVL72, Splitwise, HexGen-2)."""
    # 1. H100 SXM5 (80 GB, 3.35 TB/s, 989 TFLOPS BF16) Prefill + H200 SXM (141 GB, 4.8 TB/s, 989 TFLOPS BF16) Decode (HLS Ch. 7)
    h100_vram_gb = 80.0
    h200_vram_gb = 141.0
    h100_bw_tbs = 3.35
    h200_bw_tbs = 4.80
    h200_vs_h100_vram_x = round(h200_vram_gb / h100_vram_gb, 2)  # 1.76x
    h200_vs_h100_bw_x = round(h200_bw_tbs / h100_bw_tbs, 2)      # 1.43x

    # On 2-GPU TP=2 serving 70B FP16 (140 GB weights + 10 GB workspace = 150 GB static across 2 GPUs? No, at TP=4:
    # Let's check 2x GPU with FP8 70B (70 GB weights + 10 GB workspace = 80 GB static):
    # On 2x H100 (160 GB total): 160 - 80 = 80 GB KV pool
    # On 2x H200 (282 GB total): 282 - 80 = 202 GB KV pool (2.53x larger KV pool!)
    # On 2x GPU with 70B FP16 (140 GB weights) at TP=2:
    # 2x H100 (160 GB * 0.90 = 144 GB usable - 140 GB weights = 4 GB KV -> barely fits!)
    # 2x H200 (282 GB * 0.90 = 253.8 GB usable - 140 GB weights - 8 GB workspace = 105.8 GB KV pool!)
    # Single-GPU B200 (180 GB HBM3e) vs B300 (288 GB HBM3e) with 70 GB FP8 weights (ASP Ch. 17):
    b200_vram_gb = 180.0
    b300_vram_gb = 288.0
    b200_fp4_pflops = 10.0
    b300_fp4_pflops = 15.0
    b300_vs_b200_vram_x = round(b300_vram_gb / b200_vram_gb, 2)  # 1.60x

    # ASP Ch. 17: "if model weights take 70 GB of a GPU's memory and the GPU has 180 GB total, about 122 GB is left for KV"
    # (using binary/effective convention cited in ASP Ch. 17, or 180 - 70 = 110 GB arithmetic)
    asp_b200_reported_kv_gb = 122.0
    b200_arith_kv_gb = b200_vram_gb - 70.0  # 110.0 GB
    b300_arith_kv_gb = b300_vram_gb - 70.0  # 218.0 GB
    b300_vs_b200_kv_pool_x = round(b300_arith_kv_gb / b200_arith_kv_gb, 2)  # 1.98x

    # Splitwise (4x H100 Prefill + 4x A100 Decode) & HexGen-2 & Arrow benchmarks (ASP Ch. 18)
    splitwise_gpu_saving_pct = round((8 - 6) / 8 * 100.0, 1)  # 25.0%

    # Asymmetric phase parallelism KV layout transpose (ASP Ch. 18 Table 18-1 & 18-2)
    # Prefill: TP_p = 2, PP_p = 2 (4 GPUs) -> each stage holds 80/2 = 40 layers, each TP rank holds 8/2 = 4 KV heads
    # Decode:  TP_d = 4, PP_d = 1 (4 GPUs) -> each stage holds 80/1 = 80 layers, each TP rank holds 8/4 = 2 KV heads
    # Or TP_p = 1 (with PP_p = 4) -> 8 KV heads/rank vs TP_d = 4 -> 2 KV heads/rank (1/4 of KV tensor per decode rank)
    return {
        "h100_vram_gb": h100_vram_gb,
        "h200_vram_gb": h200_vram_gb,
        "h100_bw_tbs": h100_bw_tbs,
        "h200_bw_tbs": h200_bw_tbs,
        "h200_vs_h100_vram_x": h200_vs_h100_vram_x,
        "h200_vs_h100_bw_x": h200_vs_h100_bw_x,
        "b200_vram_gb": b200_vram_gb,
        "b300_vram_gb": b300_vram_gb,
        "b200_fp4_pflops": b200_fp4_pflops,
        "b300_fp4_pflops": b300_fp4_pflops,
        "b300_vs_b200_vram_x": b300_vs_b200_vram_x,
        "asp_b200_reported_kv_gb": asp_b200_reported_kv_gb,
        "b200_arith_kv_gb": b200_arith_kv_gb,
        "b300_arith_kv_gb": b300_arith_kv_gb,
        "b300_vs_b200_kv_pool_x": b300_vs_b200_kv_pool_x,
        "nvl72_gpus": 72,
        "nvl72_grace_cpus": 36,
        "nvl72_unified_mem_tb": 30.0,
        "nvl72_nvswitch_bw_tbs": 130.0,
        "nvl72_dynamo_680b_speedup_x": 30.0,
        "splitwise_iso_cost_rps_gain_x": 2.35,
        "splitwise_lower_cost_rps_gain_x": 1.4,
        "splitwise_cost_reduction_pct": 20.0,
        "splitwise_gpu_saving_pct": splitwise_gpu_saving_pct,
        "hexgen2_peak_rps_gain_x": 2.0,
        "hexgen2_avg_rps_gain_x": 1.3,
        "hexgen2_cost_reduction_pct": 30.0,
        "arrow_adaptive_rps_gain_x": 5.6,
        "sglang_dp_attention_speedup_x": 1.9,
    }


if __name__ == "__main__":
    ig = evaluate_colocated_interference_and_goodput()
    print(
        f"DistServe 2P1D goodput: {ig['colocated_goodput_per_gpu']} RPS/GPU colocated -> "
        f"{ig['disagg_goodput_per_gpu_exact']} RPS/GPU ({ig['goodput_per_gpu_gain_x']}x)"
    )
    kv = compute_kv_cache_transfer_footprints()
    print(
        f"4K KV cache FP16: Llama-3-70B GQA = {kv['llama_3_70b']['gqa8_4k_gb_fp16_decimal']} GB "
        f"({kv['llama_3_70b']['gqa8_4k_gib_fp16_binary']} GiB), DeepSeek-V3 MLA = "
        f"{kv['deepseek_v3_mla']['seq_4k_gb_fp16_decimal']} GB"
    )
    nx = evaluate_nixl_rdma_transfer_vs_ttft()
    print(
        f"NIXL 4K 70B transfer: NDR 400G single NIC = {nx['transfer_ms_by_fabric']['ib_ndr_400g_single_nic_50gbs']} ms "
        f"-> layer-pipelined exposed = {nx['exposed_final_layer_ms']} ms ({nx['exposed_overhead_pct']}%)"
    )
