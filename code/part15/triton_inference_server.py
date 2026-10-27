#!/usr/bin/env python3
"""Chapter 15.6 model: Triton Inference Server Architecture.

Models:
1. Model Repository Layout, Version Policies (`latest`, `all`, `specific`), `config.pbtxt`,
   and TensorRT Optimization Profile (`[min, opt, max]`) Validation:
   - Validates `max_batch_size` (`0` vs `> 0` implicit batch dimension `0`) against the
     underlying TensorRT `.plan` profile (`min=1, opt=16, max=64`).
   - Models request admission (`HTTP 400 Bad Request` when `request_batch > max_batch_size`,
     e.g., `128 > 64`) and sub-batch splitting along `preferred_batch_size` (`[16, 32, 64]`).
   - Contrasts `--model-control-mode=poll` (`5 s` polling causing `1.2 GB` NFS partial-copy
     `Magic number mismatch` and `HTTP 503` readiness outage) with `--model-control-mode=explicit`.
2. Batch Schedulers: Dynamic Batcher (`dynamic_batching`), Sequence Batcher (`sequence_batching`),
   and Decoupled Continuous Batching (`TensorRT-LLM` `GptManager`/`Executor` and `vLLM` Backends):
   - Reproduces Volume 12 Lab 02 `dense_net` (`onnxruntime_onnx`) concurrency sweeps (`C=1..64`):
     * Profile A (`dense_net_nobatch`, `max_batch_size=0`): `520 RPS` at `C=64`, `p99=2.1 ms` at `C=1`,
       `p99=121.5 ms` at `C=64`, realized batch `1.0`.
     * Profile B (`dense_net_conservative`, `max_batch_size=16`, `preferred=[4, 8, 16]`, `delay=5,000 us`):
       `450.0 infer/sec` at `C=1` (`2,218 us` client avg, `3,100 us` / `3.1 ms` p99; server `1,950 us` =
       `150 us` overhead + `200 us` queue + `1,600 us` compute input), scaling to `2,850 RPS` at `C=64`
       (`5.48x` gain over no-batch) with `p99=8.9 ms` and realized avg batch `13.0`.
     * Profile C (`dense_net_aggressive`, `max_batch_size=64`, `delay=50,000 us`): `3,400 RPS` at `C=64`
       (realized batch `48.2`, `p99=48.5 ms`), but `p99=51.2 ms` at `C=1`.
     * Misconfigured (`dense_net_misconfigured`, `preferred=[64]`, `delay=500,000 us` at `C=2`):
       `~4 RPS` (`4.0 RPS`), `p99 > 500,000 us` (`500 ms`), realized batch `2.0`.
   - Models Stateful Sequence Batching (`correlation_id` routing with `START`, `READY`, `END` flags).
   - Contrasts Request-Level Dynamic Batching on variable-length LLM requests (`10`-token request trapped
     behind `2,048`-token request at `B=32, tau=50 ms`, spiking `p99 ITL` to `420 ms` and `p99 TTFT` to `14.2 s`
     at `18%` SM occupancy) against Decoupled Continuous Batching (`p99 ITL` `420 ms -> 19.1 ms`, `3.8x`
     throughput gain; `70B` `TP=8` `ITL` `115 ms -> 18.4 ms`; `Llama-3-70B` KV cache `327,680` bytes/token =
     `1.31 GB` FP16 vs `0.65 GB` FP8 at `4,096` tokens, scaling sessions from `64` at `52%` util to `210` at `91%` util).
3. Instance Groups (`instance_group`), VRAM Footprint, and CUDA Stream Mutex Contention:
   - Models `transformer_enc` (`9.5 GB` per instance on `80 GB` A100): `count=8` consumes `76.0 GB` VRAM
     (`81,180,000,000` bytes reported), leaves only `4.0 GB` free (`1,024 MB` workspace failure), stalls
     `84 ms` on `cudaLaunchKernel` stream mutex, and degrades latency from `25 ms` to `110 ms` (`110,400 us`)
     at `180 RPS`.
   - Models tuned `count=2` (`19.0 GB` VRAM, `61.0 GB` free) + `dynamic_batching` (`max_batch_size=32`,
     `preferred=[8, 16, 32]`, `delay=5,000 us`), achieving `792 RPS` (`4.4x` / `+340%` throughput) and `18.4 ms` p99.
4. Multi-Model Pipelines (Ensembles vs Business Logic Scripting BLS) & Transport / Shared Memory:
   - Quantifies intermediate tensor copy overhead across a multi-stage DAG (`Preprocess -> Backbone -> Postprocess`)
     under HTTP/REST JSON, gRPC Protobuf (`4 MB` default limit vs `6.2 MB` payload), Pageable Host Memory
     (`10–14 GB/s`, `12.0 GB/s` nominal), Pinned / POSIX System Shared Memory (`/dev/shm`, `55–62 GB/s`,
     `58.5 GB/s` nominal on `64 GB/s` PCIe Gen5 x16), and CUDA Shared Memory (`cudaIpcMemHandle`, zero PCIe copy).
5. Model Analyzer Pareto Frontier, Prometheus Telemetry KPIs (`:8002/metrics`), and Kubernetes Probes:
   - Computes Prometheus KPIs for `resnet50` (`request_duration_us=14,280,590`, `queue_duration_us=2,180,400`,
     `compute_infer_duration_us=10,892,000` -> `76.27%` GPU execution efficiency, `15.27%` queue share,
     `24,589,211,648` bytes = `24.59 GB` / `22.90 GiB` VRAM).
   - Evaluates Model Analyzer configurations under a `p99 <= 25.0 ms` SLO and `80.0 GB` VRAM budget.
   - Validates Kubernetes `/v2/health/live`, `/v2/health/ready`, and `startupProbe` (`failureThreshold=30 * periodSeconds=10 = 300 s`)
     for `30–90 s` `70B` model loads, plus `terminationGracePeriodSeconds=120` graceful drain (avoiding the `15%`
     `503 MODEL_UNAVAILABLE` race versus `85%` `200 OK`).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class TritonModelConfigSpec:
    name: str
    platform: str
    max_batch_size: int
    input_dims: Tuple[int, ...]
    output_dims: Tuple[int, ...]
    input_dtype: str = "TYPE_FP32"
    output_dtype: str = "TYPE_FP32"
    preferred_batch_sizes: Tuple[int, ...] = ()
    max_queue_delay_us: int = 0
    instance_count: int = 1
    gpus: Tuple[int, ...] = (0,)
    version_policy: str = "latest"
    version_policy_arg: Tuple[int, ...] = (1,)
    trt_profile_min: int = 1
    trt_profile_opt: int = 16
    trt_profile_max: int = 64
    decoupled: bool = False


def resolve_active_versions(
    available_versions: Sequence[int],
    policy: str = "latest",
    count: int = 1,
    specific_versions: Sequence[int] = (),
) -> List[int]:
    """Resolves active model versions in a Triton repository directory (`latest`, `all`, `specific`)."""
    sorted_vers = sorted(set(v for v in available_versions if v > 0))
    if not sorted_vers:
        return []
    if policy == "latest":
        return sorted_vers[-count:] if count > 0 else []
    if policy == "all":
        return sorted_vers
    if policy == "specific":
        wanted = set(specific_versions)
        return [v for v in sorted_vers if v in wanted]
    raise ValueError(f"Unsupported version_policy: {policy}")


def validate_config_and_trt_profile(
    cfg: TritonModelConfigSpec,
    incoming_request_batch: int = 1,
) -> Dict[str, object]:
    """Validates `config.pbtxt` batching, tensor shapes, data types, and TensorRT optimization profile bounds."""
    valid_dtypes = {"TYPE_FP32", "TYPE_FP16", "TYPE_BF16", "TYPE_INT8", "TYPE_INT32", "TYPE_INT64", "TYPE_FP8"}
    dtype_valid = (cfg.input_dtype in valid_dtypes) and (cfg.output_dtype in valid_dtypes)

    if cfg.max_batch_size > 0:
        effective_input_shape = (incoming_request_batch,) + cfg.input_dims
        effective_output_shape = (incoming_request_batch,) + cfg.output_dims
        profile_compatible = cfg.max_batch_size <= cfg.trt_profile_max and cfg.trt_profile_min >= 1
        request_accepted = incoming_request_batch <= cfg.max_batch_size
    else:
        effective_input_shape = cfg.input_dims
        effective_output_shape = cfg.output_dims
        profile_compatible = True
        request_accepted = incoming_request_batch == 1

    if not dtype_valid:
        http_status = 400
        status_msg = f"Backend {cfg.platform} does not support data type {cfg.input_dtype}"
    elif not request_accepted:
        http_status = 400
        status_msg = "HTTP 400 Bad Request: inference request batch size exceeds maximum allowed"
    else:
        http_status = 200
        status_msg = "HTTP 200 OK"

    return {
        "name": cfg.name,
        "platform": cfg.platform,
        "dtype_valid": dtype_valid,
        "profile_compatible": profile_compatible,
        "request_accepted": request_accepted,
        "http_status": http_status,
        "status_msg": status_msg,
        "effective_input_shape": effective_input_shape,
        "effective_output_shape": effective_output_shape,
        "trt_profile_bounds": (cfg.trt_profile_min, cfg.trt_profile_opt, cfg.trt_profile_max),
    }


def evaluate_dynamic_batching_profiles() -> Dict[str, Dict[str, float | int | str]]:
    """Returns Volume 12 Lab 02 `dense_net` (`onnxruntime_onnx`) dynamic batching benchmark profiles."""
    # At C=1 on `dense_net_conservative`: client avg 2218 us, p99 3100 us (3.1 ms), 450.0 infer/sec;
    # server avg 1950 us = 150 us overhead + 200 us queue + 1600 us compute input (`4500` requests in `10,000 ms`).
    server_overhead_us = 150
    server_queue_us = 200
    server_compute_input_us = 1600
    server_total_us = server_overhead_us + server_queue_us + server_compute_input_us  # 1950 us

    return {
        "dense_net_nobatch": {
            "max_batch_size": 0,
            "max_queue_delay_us": 0,
            "throughput_rps_c64": 520.0,
            "p99_latency_ms_c1": 2.1,
            "p99_latency_ms_c64": 121.5,
            "realized_avg_batch_size": 1.0,
        },
        "dense_net_conservative": {
            "max_batch_size": 16,
            "max_queue_delay_us": 5000,
            "throughput_rps_c1": 450.0,
            "client_avg_latency_us_c1": 2218,
            "server_avg_latency_us_c1": server_total_us,
            "server_overhead_us_c1": server_overhead_us,
            "server_queue_us_c1": server_queue_us,
            "server_compute_input_us_c1": server_compute_input_us,
            "throughput_rps_c64": 2850.0,
            "speedup_vs_nobatch": round(2850.0 / 520.0, 2),  # 5.48x
            "p99_latency_ms_c1": 3.1,
            "p99_latency_ms_c64": 8.9,
            "realized_avg_batch_size": 13.0,
        },
        "dense_net_aggressive": {
            "max_batch_size": 64,
            "max_queue_delay_us": 50000,
            "throughput_rps_c64": 3400.0,
            "speedup_vs_nobatch": round(3400.0 / 520.0, 2),  # 6.54x
            "p99_latency_ms_c1": 51.2,
            "p99_latency_ms_c64": 48.5,
            "realized_avg_batch_size": 48.2,
        },
        "dense_net_misconfigured": {
            "max_batch_size": 64,
            "preferred_batch_size": 64,
            "max_queue_delay_us": 500000,  # 500 ms
            "concurrency_tested": 2,
            "throughput_rps_c2": 4.0,
            "p99_latency_us_c2": 500000,
            "p99_latency_ms_c2": 500.0,
            "realized_avg_batch_size": 2.0,
        },
    }


def simulate_sequence_batcher_routing(
    num_slots: int,
    events: Sequence[Tuple[int, str]],
) -> Dict[str, object]:
    """Simulates Triton's Stateful Sequence Batcher (`Direct` slot assignment by `correlation_id`).

    Each event is `(correlation_id, flag)` where `flag` in `{"START", "READY", "END"}`.
    Guarantees all requests with the same `correlation_id` route to the exact same slot/instance.
    """
    active_map: Dict[int, int] = {}
    free_slots: List[int] = list(range(num_slots))
    routed_slots: List[Tuple[int, str, int]] = []
    sticky_preserved = True

    for corr_id, flag in events:
        if flag == "START":
            if corr_id in active_map:
                raise ValueError(f"Duplicate START for active correlation_id={corr_id}")
            if not free_slots:
                raise RuntimeError("Sequence batcher slot exhaustion")
            slot = free_slots.pop(0)
            active_map[corr_id] = slot
            routed_slots.append((corr_id, flag, slot))
        elif flag in ("READY", "END"):
            if corr_id not in active_map:
                sticky_preserved = False
                routed_slots.append((corr_id, flag, -1))
                continue
            slot = active_map[corr_id]
            routed_slots.append((corr_id, flag, slot))
            if flag == "END":
                del active_map[corr_id]
                free_slots.append(slot)
                free_slots.sort()
        else:
            raise ValueError(f"Unknown sequence flag: {flag}")

    return {
        "routed_slots": routed_slots,
        "active_correlations_remaining": len(active_map),
        "free_slots_remaining": len(free_slots),
        "sticky_preserved": sticky_preserved,
    }


def compare_request_vs_continuous_llm_batching() -> Dict[str, float | int]:
    """Compares request-level dynamic batching vs decoupled iteration-level continuous batching for LLMs
    (Volume 12 Chapter 5 & Chapter 7).
    """
    # Request-level dynamic batching trap: short 10-token greeting batched with 2048-token essay (B=32, tau=50 ms)
    short_seq_tokens = 10
    long_seq_tokens = 2048
    wasted_pad_iterations = long_seq_tokens - short_seq_tokens  # 2038 padded decode steps

    # Llama-3-70B KV cache per token: 2 * L(80) * H_kv(8) * d_head(128) * BytesPerElem
    layers = 80
    kv_heads = 8
    head_dim = 128
    kv_bytes_per_token_fp16 = 2 * layers * kv_heads * head_dim * 2  # 327,680 bytes (~320 KB)
    kv_bytes_per_token_fp8 = 2 * layers * kv_heads * head_dim * 1   # 163,840 bytes (~160 KB)
    seq_len_4k = 4096
    kv_gb_4k_fp16 = round((kv_bytes_per_token_fp16 * seq_len_4k) / (1024**3), 2)  # 1.25 GiB or 1.34 GB (1.31 GB in V12 Ch 5)
    kv_gb_4k_decimal_fp16 = round((kv_bytes_per_token_fp16 * seq_len_4k) / 1e9, 2)  # 1.34 GB

    return {
        "short_seq_tokens": short_seq_tokens,
        "long_seq_tokens": long_seq_tokens,
        "wasted_pad_iterations": wasted_pad_iterations,
        "request_batch_p99_itl_ms": 420.0,
        "request_batch_p99_ttft_s": 14.2,
        "request_batch_sm_occupancy_pct": 18.0,
        "continuous_batch_p99_itl_ms": 19.1,
        "continuous_batch_throughput_gain_x": 3.8,
        "trtllm_70b_naive_itl_ms": 115.0,
        "trtllm_70b_executor_itl_ms": 18.4,
        "kv_bytes_per_token_fp16": kv_bytes_per_token_fp16,
        "kv_bytes_per_token_fp8": kv_bytes_per_token_fp8,
        "kv_4k_session_fp16_gb": 1.31,
        "kv_4k_session_fp8_gb": 0.65,
        "kv_max_sessions_before": 64,
        "kv_max_sessions_after": 210,
        "kv_util_before_pct": 52.0,
        "kv_util_after_pct": 91.0,
    }


def evaluate_instance_group_scaling(
    gpu_vram_gb: float = 80.0,
    model_vram_per_instance_gb: float = 9.5,
    oversubscribed_count: int = 8,
    tuned_count: int = 2,
    required_workspace_gb: float = 5.0,
) -> Dict[str, float | int | bool]:
    """Models Volume 12 Ch. 3 Scenario 2 (`transformer_enc` ONNX instance group oversubscription vs dynamic batching)."""
    oversub_vram_gb = round(oversubscribed_count * model_vram_per_instance_gb, 2)  # 76.0 GB
    oversub_free_gb = round(gpu_vram_gb - oversub_vram_gb, 2)  # 4.0 GB
    oversub_workspace_ok = oversub_free_gb >= required_workspace_gb

    tuned_vram_gb = round(tuned_count * model_vram_per_instance_gb, 2)  # 19.0 GB
    tuned_free_gb = round(gpu_vram_gb - tuned_vram_gb, 2)  # 61.0 GB
    vram_saved_gb = round(oversub_vram_gb - tuned_vram_gb, 2)  # 57.0 GB
    oversub_reported_vram_gb = 81.18  # 81,180,000,000 bytes reported in Prometheus
    tuned_workspace_ok = tuned_free_gb >= required_workspace_gb

    oversub_rps = 180.0
    tuned_rps = 792.0
    throughput_increase_pct = round(((tuned_rps - oversub_rps) / oversub_rps) * 100.0, 1)  # 340.0%
    throughput_multiplier_x = round(tuned_rps / oversub_rps, 1)  # 4.4x

    return {
        "oversub_vram_gb": oversub_vram_gb,
        "oversub_free_gb": oversub_free_gb,
        "oversub_workspace_ok": oversub_workspace_ok,
        "oversub_stream_stall_ms": 84.0,
        "oversub_latency_ms": 110.0,
        "oversub_compute_infer_us": 110400,
        "oversub_reported_vram_bytes": 81180000000,
        "oversub_reported_vram_gb": oversub_reported_vram_gb,
        "baseline_single_latency_ms": 25.0,
        "tuned_vram_gb": tuned_vram_gb,
        "tuned_free_gb": tuned_free_gb,
        "vram_saved_gb": vram_saved_gb,
        "tuned_workspace_ok": tuned_workspace_ok,
        "oversub_rps": oversub_rps,
        "tuned_rps": tuned_rps,
        "throughput_increase_pct": throughput_increase_pct,
        "throughput_multiplier_x": throughput_multiplier_x,
        "tuned_p99_latency_ms": 18.4,
    }


def evaluate_transport_and_shared_memory(
    payload_mb: float = 6.2,
    grpc_default_limit_mb: float = 4.0,
    batch_size: int = 64,
    tensor_bytes_per_request: int = 3 * 224 * 224 * 4,  # 602,112 bytes (~0.60 MB FP32 image)
) -> Dict[str, float | int | bool]:
    """Evaluates gRPC message limits, PCIe Gen5 pageable vs pinned/SHM bandwidth, and Ensemble/BLS CUDA IPC savings."""
    grpc_exceeds_default = payload_mb > grpc_default_limit_mb
    total_batch_bytes = batch_size * tensor_bytes_per_request  # 38,535,168 bytes (~38.54 MB)
    total_batch_gb = total_batch_bytes / 1e9

    pcie_gen5_peak_gbps = 64.0
    pageable_bw_gbps = 12.0   # 10-14 GB/s range in V12 Ch 2
    pinned_shm_bw_gbps = 58.5  # 55-62 GB/s range in V12 Ch 2

    pageable_copy_ms = round((total_batch_gb / pageable_bw_gbps) * 1000.0, 2)
    pinned_copy_ms = round((total_batch_gb / pinned_shm_bw_gbps) * 1000.0, 2)
    dma_speedup_x = round(pinned_shm_bw_gbps / pageable_bw_gbps, 2)

    # In a 3-stage pipeline (Preprocess -> TensorRT -> Postprocess), naive HTTP/gRPC client orchestration
    # performs 2 round-trip D2H + H2D intermediate copies (4 PCIe crossings), whereas Ensemble / BLS with
    # CUDA IPC (`cudaIpcMemHandle`, 64 bytes) performs 0 intermediate PCIe copies.
    naive_intermediate_pcie_crossings = 4
    ensemble_bls_cuda_ipc_crossings = 0
    cuda_ipc_handle_bytes = 64

    return {
        "payload_mb": payload_mb,
        "grpc_default_limit_mb": grpc_default_limit_mb,
        "grpc_exceeds_default": grpc_exceeds_default,
        "total_batch_bytes": total_batch_bytes,
        "pcie_gen5_peak_gbps": pcie_gen5_peak_gbps,
        "pageable_bw_gbps": pageable_bw_gbps,
        "pinned_shm_bw_gbps": pinned_shm_bw_gbps,
        "pageable_copy_ms": pageable_copy_ms,
        "pinned_copy_ms": pinned_copy_ms,
        "dma_speedup_x": dma_speedup_x,
        "naive_intermediate_pcie_crossings": naive_intermediate_pcie_crossings,
        "ensemble_bls_cuda_ipc_crossings": ensemble_bls_cuda_ipc_crossings,
        "cuda_ipc_handle_bytes": cuda_ipc_handle_bytes,
    }


def compute_prometheus_kpis(
    request_duration_us: int = 14280590,
    queue_duration_us: int = 2180400,
    compute_infer_duration_us: int = 10892000,
    request_success_count: int = 1000,
    exec_count: int = 50,
    gpu_memory_used_bytes: int = 24589211648,
) -> Dict[str, float]:
    """Computes Triton operational KPIs from `:8002/metrics` counters (Volume 12 Ch. 3 & Lab 02)."""
    avg_request_latency_us = round(request_duration_us / request_success_count, 2)
    avg_queue_wait_us = round(queue_duration_us / request_success_count, 2)
    avg_compute_infer_us = round(compute_infer_duration_us / request_success_count, 2)
    other_overhead_us = request_duration_us - queue_duration_us - compute_infer_duration_us  # 1,208,190 us

    gpu_execution_efficiency_pct = round((compute_infer_duration_us / request_duration_us) * 100.0, 2)  # 76.27%
    queue_fraction_pct = round((queue_duration_us / request_duration_us) * 100.0, 2)  # 15.27%
    realized_avg_batch_size = round(request_success_count / exec_count, 2)
    gpu_memory_gb_decimal = round(gpu_memory_used_bytes / 1e9, 2)  # 24.59 GB
    gpu_memory_gib = round(gpu_memory_used_bytes / (1024**3), 2)   # 22.90 GiB

    return {
        "avg_request_latency_us": avg_request_latency_us,
        "avg_queue_wait_us": avg_queue_wait_us,
        "avg_compute_infer_us": avg_compute_infer_us,
        "other_overhead_us": float(other_overhead_us),
        "gpu_execution_efficiency_pct": gpu_execution_efficiency_pct,
        "queue_fraction_pct": queue_fraction_pct,
        "realized_avg_batch_size": realized_avg_batch_size,
        "gpu_memory_gb_decimal": gpu_memory_gb_decimal,
        "gpu_memory_gib": gpu_memory_gib,
    }


def select_model_analyzer_pareto_optimal(
    candidates: Sequence[Dict[str, float | int | str]],
    max_p99_ms: float = 25.0,
    max_vram_gb: float = 40.0,
) -> Dict[str, object]:
    """Filters Model Analyzer sweep candidates by SLO (`p99 <= max_p99_ms`) and VRAM (`vram_gb <= max_vram_gb`),
    computes the Pareto frontier (non-dominated in higher throughput & lower p99 latency), and picks the max-RPS winner.
    """
    feasible = [
        c for c in candidates
        if float(c["p99_ms"]) <= max_p99_ms and float(c["vram_gb"]) <= max_vram_gb
    ]
    pareto: List[Dict[str, float | int | str]] = []
    for c in feasible:
        dominated = False
        for other in feasible:
            if other is c:
                continue
            better_or_equal_rps = float(other["throughput_rps"]) >= float(c["throughput_rps"])
            better_or_equal_lat = float(other["p99_ms"]) <= float(c["p99_ms"])
            strictly_better = (
                float(other["throughput_rps"]) > float(c["throughput_rps"])
                or float(other["p99_ms"]) < float(c["p99_ms"])
            )
            if better_or_equal_rps and better_or_equal_lat and strictly_better:
                dominated = True
                break
        if not dominated:
            pareto.append(c)

    pareto.sort(key=lambda x: float(x["throughput_rps"]), reverse=True)
    best = pareto[0] if pareto else None
    return {
        "feasible_count": len(feasible),
        "pareto_frontier": [str(x["config_id"]) for x in pareto],
        "selected_config": best["config_id"] if best else None,
        "selected_rps": float(best["throughput_rps"]) if best else 0.0,
        "selected_p99_ms": float(best["p99_ms"]) if best else 0.0,
        "selected_vram_gb": float(best["vram_gb"]) if best else 0.0,
    }


def evaluate_k8s_probes_and_lifecycle(
    model_load_seconds: int = 75,
    startup_failure_threshold: int = 30,
    startup_period_seconds: int = 10,
    termination_grace_seconds: int = 120,
    inflight_drain_seconds: int = 30,
) -> Dict[str, int | float | bool]:
    """Validates Kubernetes startup/liveness/readiness probe decoupling and explicit model drain lifecycle."""
    max_startup_window_s = startup_failure_threshold * startup_period_seconds  # 300 s
    survives_70b_load = model_load_seconds <= max_startup_window_s
    grace_covers_drain = termination_grace_seconds > inflight_drain_seconds

    return {
        "model_load_seconds": model_load_seconds,
        "max_startup_window_s": max_startup_window_s,
        "survives_70b_load": survives_70b_load,
        "liveness_during_load_http": 200,
        "readiness_during_load_http": 503,
        "readiness_after_load_http": 200,
        "termination_grace_seconds": termination_grace_seconds,
        "grace_covers_drain": grace_covers_drain,
        "uncoordinated_unload_503_pct": 15.0,
        "uncoordinated_unload_200_pct": 85.0,
    }


if __name__ == "__main__":
    print("Triton Inference Server model summary:")
    print("  Dynamic batching profiles:", evaluate_dynamic_batching_profiles()["dense_net_conservative"])
    print("  Instance group scaling:", evaluate_instance_group_scaling())
    print("  Prometheus KPIs:", compute_prometheus_kpis())
