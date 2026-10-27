#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.6: Triton Inference Server."""

from __future__ import annotations
import sys
from triton_inference_server import (
    TritonModelConfigSpec,
    resolve_active_versions,
    validate_config_and_trt_profile,
    evaluate_dynamic_batching_profiles,
    simulate_sequence_batcher_routing,
    compare_request_vs_continuous_llm_batching,
    evaluate_instance_group_scaling,
    evaluate_transport_and_shared_memory,
    compute_prometheus_kpis,
    select_model_analyzer_pareto_optimal,
    evaluate_k8s_probes_and_lifecycle,
)


def run_lab() -> int:
    print("=== Chapter 15.6 Lab: Triton Inference Server Verification ===")
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

    # 1. Model Repository Version Policies (`latest`, `all`, `specific`)
    check(
        "1. Version policy 'latest: { count: 1 }' on versions [1, 2, 3] serves only version [3]",
        resolve_active_versions([1, 2, 3], policy="latest", count=1) == [3],
    )
    check(
        "2. Version policy 'all: {}' on versions [1, 2, 3] serves [1, 2, 3] simultaneously",
        resolve_active_versions([1, 2, 3], policy="all") == [1, 2, 3],
    )
    check(
        "3. Version policy 'specific: { versions: [1, 2] }' on [1, 2, 3] serves explicitly [1, 2]",
        resolve_active_versions([1, 2, 3], policy="specific", specific_versions=[1, 2]) == [1, 2],
    )

    # 2. `config.pbtxt` Validation & TensorRT Optimization Profile (`min=1, opt=16, max=64`)
    resnet_cfg = TritonModelConfigSpec(
        name="resnet50",
        platform="tensorrt_plan",
        max_batch_size=64,
        input_dims=(3, 224, 224),
        output_dims=(1000,),
        preferred_batch_sizes=(16, 32, 64),
        max_queue_delay_us=5000,
        instance_count=2,
        gpus=(0, 1),
        trt_profile_min=1,
        trt_profile_opt=16,
        trt_profile_max=64,
    )
    res_ok = validate_config_and_trt_profile(resnet_cfg, incoming_request_batch=32)
    check(
        "4. resnet50 config.pbtxt (max_batch_size=64 <= TRT profile max=64) prepends implicit batch dim 0 -> (32, 3, 224, 224) and returns HTTP 200",
        res_ok["profile_compatible"] is True
        and res_ok["http_status"] == 200
        and res_ok["effective_input_shape"] == (32, 3, 224, 224)
        and res_ok["effective_output_shape"] == (32, 1000),
    )

    res_exceed = validate_config_and_trt_profile(resnet_cfg, incoming_request_batch=128)
    check(
        "5. Request batch size 128 exceeding max_batch_size=64 is rejected at ingress with HTTP 400 Bad Request",
        res_exceed["request_accepted"] is False and res_exceed["http_status"] == 400,
    )

    densenet_bad_dtype = TritonModelConfigSpec(
        name="dense_net",
        platform="onnxruntime_onnx",
        max_batch_size=8,
        input_dims=(3, 224, 224),
        output_dims=(1000, 1, 1),
        input_dtype="TYPE_STRING",
    )
    res_bad_dtype = validate_config_and_trt_profile(densenet_bad_dtype, incoming_request_batch=1)
    check(
        "6. Lab 01 failure injection (TYPE_FP32 -> TYPE_STRING on dense_net ONNX) fails validation with HTTP 400",
        res_bad_dtype["dtype_valid"] is False and res_bad_dtype["http_status"] == 400,
    )

    # 3. Dynamic Batching Profiles (Volume 12 Lab 02 `dense_net` Benchmarks)
    db_profiles = evaluate_dynamic_batching_profiles()
    nobatch = db_profiles["dense_net_nobatch"]
    cons = db_profiles["dense_net_conservative"]
    aggr = db_profiles["dense_net_aggressive"]
    misc = db_profiles["dense_net_misconfigured"]

    check(
        "7. Profile A (dense_net_nobatch, max_batch_size=0) reaches 520 RPS at C=64 with p99=121.5 ms and realized batch 1.0",
        nobatch["throughput_rps_c64"] == 520.0
        and nobatch["p99_latency_ms_c64"] == 121.5
        and nobatch["realized_avg_batch_size"] == 1.0,
    )

    check(
        "8. Profile B (dense_net_conservative, max_batch=16, delay=5000 us) at C=1 decomposes server 1950 us into 150 us overhead + 200 us queue + 1600 us compute",
        cons["server_avg_latency_us_c1"] == 1950
        and cons["server_overhead_us_c1"] + cons["server_queue_us_c1"] + cons["server_compute_input_us_c1"] == 1950
        and cons["throughput_rps_c1"] == 450.0,
    )

    check(
        "9. Profile B (dense_net_conservative) at C=64 reaches 2850 RPS (5.48x speedup vs no-batch), p99=8.9 ms, and realized avg batch 13.0",
        cons["throughput_rps_c64"] == 2850.0
        and cons["speedup_vs_nobatch"] == 5.48
        and cons["p99_latency_ms_c64"] == 8.9
        and cons["realized_avg_batch_size"] == 13.0,
    )

    check(
        "10. Profile C (dense_net_aggressive, max_batch=64, delay=50000 us) reaches 3400 RPS (realized batch 48.2) at C=64 but inflates C=1 p99 to 51.2 ms",
        aggr["throughput_rps_c64"] == 3400.0
        and aggr["realized_avg_batch_size"] == 48.2
        and aggr["p99_latency_ms_c1"] == 51.2,
    )

    check(
        "11. Lab 02 failure injection (500,000 us / 500 ms queue delay at C=2) collapses throughput to 4.0 RPS and spikes p99 >= 500 ms with realized batch 2.0",
        misc["throughput_rps_c2"] == 4.0
        and misc["p99_latency_ms_c2"] == 500.0
        and misc["realized_avg_batch_size"] == 2.0,
    )

    # 4. Stateful Sequence Batcher (`correlation_id` Routing)
    seq_res = simulate_sequence_batcher_routing(
        num_slots=2,
        events=[
            (1001, "START"),
            (1002, "START"),
            (1001, "READY"),
            (1002, "READY"),
            (1001, "END"),
            (1003, "START"),
            (1003, "END"),
            (1002, "END"),
        ],
    )
    check(
        "12. Sequence Batcher routes correlation_id=1001 consistently to slot 0, frees slot 0 on END, and assigns correlation_id=1003 to freed slot 0",
        seq_res["sticky_preserved"] is True
        and seq_res["routed_slots"][0] == (1001, "START", 0)
        and seq_res["routed_slots"][2] == (1001, "READY", 0)
        and seq_res["routed_slots"][5] == (1003, "START", 0)
        and seq_res["free_slots_remaining"] == 2,
    )

    # 5. Request-Level Dynamic Batching vs Decoupled Continuous Batching (`TensorRT-LLM` & `vLLM`)
    llm_batch = compare_request_vs_continuous_llm_batching()
    check(
        "13. Request-level dynamic batching traps a 10-token query behind a 2048-token query for 2038 padded decode steps (p99 ITL=420 ms, p99 TTFT=14.2 s, SM occ=18%)",
        llm_batch["wasted_pad_iterations"] == 2038
        and llm_batch["request_batch_p99_itl_ms"] == 420.0
        and llm_batch["request_batch_p99_ttft_s"] == 14.2
        and llm_batch["request_batch_sm_occupancy_pct"] == 18.0,
    )

    check(
        "14. Decoupled continuous batching with chunked prefill lowers p99 ITL from 420 ms to 19.1 ms (3.8x throughput gain) and 70B TP=8 ITL from 115 ms to 18.4 ms",
        llm_batch["continuous_batch_p99_itl_ms"] == 19.1
        and llm_batch["continuous_batch_throughput_gain_x"] == 3.8
        and llm_batch["trtllm_70b_naive_itl_ms"] == 115.0
        and llm_batch["trtllm_70b_executor_itl_ms"] == 18.4,
    )

    check(
        "15. Llama-3-70B KV cache per token equals 327,680 bytes in FP16 (1.31 GB per 4096-token session) and 163,840 bytes in FP8 (0.65 GB), scaling sessions 64 -> 210 (52% -> 91% util)",
        llm_batch["kv_bytes_per_token_fp16"] == 327680
        and llm_batch["kv_bytes_per_token_fp8"] == 163840
        and llm_batch["kv_4k_session_fp16_gb"] == 1.31
        and llm_batch["kv_4k_session_fp8_gb"] == 0.65
        and llm_batch["kv_max_sessions_before"] == 64
        and llm_batch["kv_max_sessions_after"] == 210,
    )

    # 6. Instance Group Scaling & CUDA Stream Contention (`transformer_enc` on 80 GB A100)
    ig = evaluate_instance_group_scaling()
    check(
        "16. Setting instance_group count=8 for a 9.5 GB model consumes 76.0 GB VRAM on an 80 GB A100 (4.0 GB free), causing 84 ms stream mutex stalls and spiking latency 25 ms -> 110 ms",
        ig["oversub_vram_gb"] == 76.0
        and ig["oversub_free_gb"] == 4.0
        and ig["oversub_workspace_ok"] is False
        and ig["oversub_stream_stall_ms"] == 84.0
        and ig["oversub_latency_ms"] == 110.0,
    )

    check(
        "17. Right-sizing instance_group to count=2 (19.0 GB VRAM, 61.0 GB free) + dynamic batching increases throughput +340.0% (4.4x, 180 -> 792 RPS) and cuts p99 to 18.4 ms",
        ig["tuned_vram_gb"] == 19.0
        and ig["tuned_free_gb"] == 61.0
        and ig["tuned_workspace_ok"] is True
        and ig["throughput_increase_pct"] == 340.0
        and ig["throughput_multiplier_x"] == 4.4
        and ig["tuned_rps"] == 792.0
        and ig["tuned_p99_latency_ms"] == 18.4,
    )

    # 7. Transport Protocols, gRPC Message Limit, and Host/CUDA Shared Memory
    shm = evaluate_transport_and_shared_memory()
    check(
        "18. A 6.2 MB tensor payload exceeds the default 4.0 MB gRPC max_receive_bytes limit unless channel limits are raised or Shared Memory is used",
        shm["grpc_exceeds_default"] is True
        and shm["payload_mb"] == 6.2
        and shm["grpc_default_limit_mb"] == 4.0,
    )

    check(
        "19. Pinned / POSIX Shared Memory (58.5 GB/s on 64 GB/s PCIe Gen5) is 4.88x faster than Pageable malloc (12.0 GB/s), cutting 64-image batch H2D copy from 3.21 ms to 0.66 ms",
        shm["dma_speedup_x"] == 4.88
        and shm["pageable_copy_ms"] == 3.21
        and shm["pinned_copy_ms"] == 0.66,
    )

    check(
        "20. Ensemble and BLS pipelines using CUDA IPC (64-byte cudaIpcMemHandle) eliminate all 4 intermediate PCIe D2H/H2D crossings in a 3-stage pipeline",
        shm["naive_intermediate_pcie_crossings"] == 4
        and shm["ensemble_bls_cuda_ipc_crossings"] == 0
        and shm["cuda_ipc_handle_bytes"] == 64,
    )

    # 8. Prometheus Telemetry KPIs (`:8002/metrics`)
    kpis = compute_prometheus_kpis()
    check(
        "21. resnet50 Prometheus counters (14,280,590 us total, 2,180,400 us queue, 10,892,000 us compute) yield 76.27% GPU execution efficiency and 15.27% queue share",
        kpis["gpu_execution_efficiency_pct"] == 76.27
        and kpis["queue_fraction_pct"] == 15.27
        and kpis["avg_queue_wait_us"] == 2180.4,
    )

    check(
        "22. Prometheus nv_gpu_memory_used_bytes=24,589,211,648 equals 24.59 GB (22.90 GiB) and 1000 requests / 50 executions equals realized batch 20.0",
        kpis["gpu_memory_gb_decimal"] == 24.59
        and kpis["gpu_memory_gib"] == 22.90
        and kpis["realized_avg_batch_size"] == 20.0,
    )

    # 9. Model Analyzer Pareto Frontier Selection
    ma_candidates = [
        {"config_id": "cfg_c1_bs8", "instance_count": 1, "max_batch_size": 8, "throughput_rps": 310.0, "p99_ms": 9.2, "vram_gb": 9.5},
        {"config_id": "cfg_c2_bs16", "instance_count": 2, "max_batch_size": 16, "throughput_rps": 610.0, "p99_ms": 14.5, "vram_gb": 19.0},
        {"config_id": "cfg_c2_bs32", "instance_count": 2, "max_batch_size": 32, "throughput_rps": 792.0, "p99_ms": 18.4, "vram_gb": 19.0},
        {"config_id": "cfg_c4_bs16_dom", "instance_count": 4, "max_batch_size": 16, "throughput_rps": 580.0, "p99_ms": 21.0, "vram_gb": 38.0},
        {"config_id": "cfg_c8_bs32_slo_viol", "instance_count": 8, "max_batch_size": 32, "throughput_rps": 180.0, "p99_ms": 110.0, "vram_gb": 76.0},
    ]
    ma_res = select_model_analyzer_pareto_optimal(ma_candidates, max_p99_ms=25.0, max_vram_gb=40.0)
    check(
        "23. Model Analyzer filters out count=8 (110.0 ms > 25.0 ms SLO, 76.0 GB > 40.0 GB), eliminates dominated count=4, and selects cfg_c2_bs32 (792.0 RPS at 18.4 ms p99)",
        ma_res["feasible_count"] == 4
        and ma_res["pareto_frontier"] == ["cfg_c2_bs32", "cfg_c2_bs16", "cfg_c1_bs8"]
        and ma_res["selected_config"] == "cfg_c2_bs32"
        and ma_res["selected_rps"] == 792.0,
    )

    # 10. Kubernetes Health Probes & Model Lifecycle Drain
    k8s = evaluate_k8s_probes_and_lifecycle()
    check(
        "24. Kubernetes startupProbe (failureThreshold=30 * periodSeconds=10 = 300 s) safely covers 30-90 s 70B model loads while /v2/health/live returns 200 and /v2/health/ready returns 503",
        k8s["max_startup_window_s"] == 300
        and k8s["survives_70b_load"] is True
        and k8s["liveness_during_load_http"] == 200
        and k8s["readiness_during_load_http"] == 503,
    )

    check(
        "25. Uncoordinated model unload causes 15.0% HTTP 503 MODEL_UNAVAILABLE errors (85.0% 200 OK), prevented by explicit control mode + preStop drain within 120 s grace period",
        k8s["uncoordinated_unload_503_pct"] == 15.0
        and k8s["uncoordinated_unload_200_pct"] == 85.0
        and k8s["grace_covers_drain"] is True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
