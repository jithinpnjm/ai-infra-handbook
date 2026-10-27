#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.17: nccl-tests and fabric benchmarking."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nccl_tests_benchmarking import (
    BUSBW_COLLECTIVES,
    FabricBenchmarkError,
    attribute_three_tier_bottleneck,
    bisect_straggler_node,
    compute_algbw_and_busbw,
    compute_busbw_factor,
    evaluate_inference_latency_and_percentiles,
    evaluate_training_scaling_and_bottlenecks,
    generate_nccl_tests_sweep,
    parse_nccl_tests_table,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main() -> int:
    print("=== Chapter 12.17 Lab: nccl-tests and Fabric Benchmarking ===")

    # 1. Exact busbw conversion factors across all 6 nccl-tests collectives
    check(
        "All 6 nccl-tests collective families (all_reduce, reduce_scatter, all_gather, alltoall, broadcast, reduce) are supported",
        set(BUSBW_COLLECTIVES.keys())
        == {"all_reduce", "reduce_scatter", "all_gather", "alltoall", "broadcast", "reduce"},
    )
    check(
        "AllReduce busbw factor 2*(n-1)/n equals 1.0 (n=2), 1.5 (n=4), 1.75 (n=8), 1.96875 (n=64), 142/72=1.972222 (n=72)",
        compute_busbw_factor("all_reduce", 2) == 1.0
        and compute_busbw_factor("all_reduce", 4) == 1.5
        and compute_busbw_factor("all_reduce", 8) == 1.75
        and compute_busbw_factor("all_reduce", 64) == 1.96875
        and round(compute_busbw_factor("all_reduce", 72), 6) == 1.972222,
    )
    check(
        "ReduceScatter, AllGather, and AllToAll busbw factor (n-1)/n equals 0.5 (n=2), 0.875 (n=8), 63/64=0.984375 (n=64)",
        compute_busbw_factor("reduce_scatter", 2) == 0.5
        and compute_busbw_factor("all_gather", 8) == 0.875
        and compute_busbw_factor("alltoall", 8) == 0.875
        and compute_busbw_factor("reduce_scatter", 64) == 0.984375,
    )
    check(
        "Broadcast and Reduce busbw factor equals 1.0 for any n >= 2 (and 0.0 for n == 1)",
        compute_busbw_factor("broadcast", 8) == 1.0
        and compute_busbw_factor("reduce", 64) == 1.0
        and compute_busbw_factor("all_reduce", 1) == 0.0,
    )

    # 2. Exact V5 Lab 02 `all_reduce_perf` rows (8 MiB, 64 MiB, 512 MiB on 8 GPUs)
    r_8m = compute_algbw_and_busbw("all_reduce", size_bytes=8_388_608, time_us=412.3, num_ranks=8)
    r_64m = compute_algbw_and_busbw("all_reduce", size_bytes=67_108_864, time_us=1653.1, num_ranks=8)
    r_512m = compute_algbw_and_busbw("all_reduce", size_bytes=536_870_912, time_us=9871.4, num_ranks=8)
    print(
        f"  [INFO] V5 Lab 02 8-GPU all_reduce_perf rows: "
        f"8MiB -> algbw={r_8m['algbw_gbps']}, busbw={r_8m['busbw_gbps']}; "
        f"64MiB -> algbw={r_64m['algbw_gbps']}, busbw={r_64m['busbw_gbps']}; "
        f"512MiB -> algbw={r_512m['algbw_gbps']}, busbw={r_512m['busbw_gbps']} GB/s"
    )
    check(
        "V5 Lab 02: 8 MiB (8,388,608 B) in 412.3 us on 8 GPUs -> algbw = 20.35 GB/s, busbw = 35.61 GB/s",
        r_8m["algbw_gbps"] == 20.35 and r_8m["busbw_gbps"] == 35.61,
    )
    check(
        "V5 Lab 02: 64 MiB (67,108,864 B) in 1653.1 us on 8 GPUs -> algbw = 40.60 GB/s, busbw = 71.05 GB/s",
        r_64m["algbw_gbps"] == 40.60 and r_64m["busbw_gbps"] == 71.05,
    )
    check(
        "V5 Lab 02: 512 MiB (536,870,912 B) in 9871.4 us on 8 GPUs -> algbw = 54.39 GB/s, busbw = 95.18 GB/s",
        r_512m["algbw_gbps"] == 54.39 and r_512m["busbw_gbps"] == 95.18,
    )

    # 3. Single-node HGX H100 (NVLink 4) vs Multi-node 8x400G NDR InfiniBand `all_reduce_perf`
    ar_hgx_1g = compute_algbw_and_busbw("all_reduce", size_bytes=1_073_741_824, time_us=2480.0, num_ranks=8)
    ar_ib64_1g = compute_algbw_and_busbw("all_reduce", size_bytes=1_073_741_824, time_us=5850.0, num_ranks=64)
    check(
        "Single-node 8x H100 SXM (NVLink 4, 900 GB/s): 1 GiB (1,073,741,824 B) in 2480.0 us -> algbw = 432.96 GB/s, busbw = 757.68 GB/s",
        ar_hgx_1g["algbw_gbps"] == 432.96 and ar_hgx_1g["busbw_gbps"] == 757.68,
    )
    check(
        "Multi-node 64-GPU (8 nodes x 8x400G NDR IB): 1 GiB in 5850.0 us -> algbw = 183.55 GB/s, busbw = 361.36 GB/s (45.17 GB/s per rail, 90.34% of 400 GB/s line rate)",
        ar_ib64_1g["algbw_gbps"] == 183.55
        and ar_ib64_1g["busbw_gbps"] == 361.36
        and round(ar_ib64_1g["busbw_gbps"] / 8.0, 2) == 45.17
        and round((ar_ib64_1g["busbw_gbps"] / 400.0) * 100.0, 2) == 90.34,
    )

    # 4. `nccl-tests` CLI sweep generator (-b 8M -e 1G -f 2 -g 1 -w 5 -n 20)
    sweep = generate_nccl_tests_sweep(
        min_bytes=8_388_608,
        max_bytes=1_073_741_824,
        step_factor=2,
        gpus_per_proc=1,
        num_procs=8,
        warmup_iters=5,
        measure_iters=20,
    )
    check(
        "nccl-tests sweep (-b 8M -e 1G -f 2 -g 1 on 8 MPI ranks, -w 5 -n 20) steps through 8 sizes and 400 total collective launches",
        sweep["total_ranks"] == 8
        and sweep["num_sizes"] == 8
        and sweep["sizes_bytes"][0] == 8_388_608
        and sweep["sizes_bytes"][-1] == 1_073_741_824
        and sweep["collectives_per_size"] == 50
        and sweep["total_collective_launches"] == 400,
    )

    # 5. `nccl-tests` 13-column dual-mode (out-of-place + in-place) table parser & #wrong validation
    sample_table_13col = """
#                                                              out-of-place                       in-place
#       size         count      type   redop    root     time   algbw   busbw #wrong     time   algbw   busbw #wrong
#        (B)    (elements)                               (us)  (GB/s)  (GB/s)            (us)  (GB/s)  (GB/s)
     8388608       2097152     float     sum      -1    412.3   20.35   35.61      0    410.0   20.46   35.81      0
    67108864      16777216     float     sum      -1   1653.1   40.60   71.05      0   1645.0   40.80   71.40      0
   536870912     134217728     float     sum      -1   9871.4   54.39   95.18      0   9820.0   54.67   95.67      0
"""
    parsed = parse_nccl_tests_table(sample_table_13col, collective="all_reduce", num_ranks=8)
    check(
        "13-column all_reduce_perf parser validates #wrong == 0, 0 formula mismatches, and peak busbw = 95.67 GB/s",
        parsed["num_rows"] == 3
        and parsed["correctness_pass"] is True
        and parsed["formula_mismatches"] == 0
        and parsed["peak_busbw_gbps"] == 95.67,
    )

    corrupted_table = sample_table_13col.replace("95.67      0", "95.67      3")
    parsed_bad = parse_nccl_tests_table(corrupted_table, collective="all_reduce", num_ranks=8)
    check(
        "Parser flags data-corruption failure when #wrong > 0",
        parsed_bad["correctness_pass"] is False and parsed_bad["total_wrong"] == 3,
    )

    # 6. Three-tier bottleneck attribution (V7 Ch. 10 & Lab 03, V8 Lab 02, V5 Lab 02)
    t1_pcie = attribute_three_tier_bottleneck(
        nvbandwidth_DtoH_gbps=28.0,
        ib_write_bw_host_gbps=390.0,
        ib_write_bw_cuda_gbps=385.0,
        nccl_single_node_busbw_gbps=95.18,
        nccl_multi_node_busbw_gbps=85.0,
        app_effective_busbw_gbps=80.0,
    )
    t2a_cable = attribute_three_tier_bottleneck(
        nvbandwidth_DtoH_gbps=56.0,
        ib_write_bw_host_gbps=195.0,
        ib_write_bw_cuda_gbps=190.0,
        nccl_single_node_busbw_gbps=95.18,
        nccl_multi_node_busbw_gbps=45.0,
        app_effective_busbw_gbps=42.0,
    )
    t2b_gdr = attribute_three_tier_bottleneck(
        nvbandwidth_DtoH_gbps=56.0,
        ib_write_bw_host_gbps=390.0,
        ib_write_bw_cuda_gbps=110.0,
        nccl_single_node_busbw_gbps=95.18,
        nccl_multi_node_busbw_gbps=24.0,
        app_effective_busbw_gbps=22.0,
    )
    t3b_multinode = attribute_three_tier_bottleneck(
        nvbandwidth_DtoH_gbps=56.0,
        ib_write_bw_host_gbps=390.0,
        ib_write_bw_cuda_gbps=385.0,
        nccl_single_node_busbw_gbps=95.18,
        nccl_multi_node_busbw_gbps=58.2,
        app_effective_busbw_gbps=55.0,
    )
    t4_buckets = attribute_three_tier_bottleneck(
        nvbandwidth_DtoH_gbps=56.0,
        ib_write_bw_host_gbps=390.0,
        ib_write_bw_cuda_gbps=385.0,
        nccl_single_node_busbw_gbps=95.18,
        nccl_multi_node_busbw_gbps=88.0,
        app_effective_busbw_gbps=32.0,
    )
    check(
        "V7 Ch10 Tier 1: nvbandwidth = 28.0 GB/s (vs 50-60 GB/s PCIe Gen5 x16) isolates downtrained x8 PCIe link",
        t1_pcie["bottleneck_layer"] == "Tier 1: Intra-node PCIe / Motherboard",
    )
    check(
        "V7 Ch10 Tier 2a: ib_write_bw = 195.0 Gbps (vs 390.0 Gbps on 400G NDR) isolates physical link/optics width degradation",
        t2a_cable["bottleneck_layer"] == "Tier 2a: Physical RDMA Link / Optics",
    )
    check(
        "V7 Lab 03 Tier 2b: host RDMA = 390.0 Gbps but --use_cuda = 110.0 Gbps isolates GPUDirect RDMA / peermem / SYS locality",
        t2b_gdr["bottleneck_layer"] == "Tier 2b: GPUDirect RDMA / PCIe Locality",
    )
    check(
        "V5 Lab 02 Tier 3b: multi-node 58.2 GB/s vs single-node 95.18 GB/s (61.15% < 80% gate of 76.14 GB/s) isolates multi-node NCCL path",
        t3b_multinode["bottleneck_layer"] == "Tier 3b: Multi-Node NCCL Collectives"
        and t3b_multinode["multi_to_single_node_ratio"] == 0.6115
        and round(0.80 * 95.18, 2) == 76.14
        and t3b_multinode["multi_node_passes_80pct_gate"] is False,
    )
    check(
        "V7 Ch10 Tier 4: hardware and nccl-tests pass (88.0 GB/s = 92.46% of 95.18 GB/s), but PyTorch DDP is at 32.0 GB/s due to 256 KB fragments",
        t4_buckets["bottleneck_layer"] == "Tier 4: Framework / Application Bucket Sizing"
        and round((88.0 / 95.18) * 100.0, 2) == 92.46,
    )

    # 7. Binary-search straggler node bisection across N = 8, 64, and 128 nodes
    nodes_8 = [f"dgx-{i:02d}" for i in range(8)]
    nodes_64 = [f"dgx-{i:02d}" for i in range(64)]
    nodes_128 = [f"dgx-{i:03d}" for i in range(128)]

    b8 = bisect_straggler_node(nodes_8, straggler_index=5)
    b64 = bisect_straggler_node(nodes_64, straggler_index=41)
    b128 = bisect_straggler_node(nodes_128, straggler_index=93)

    print(
        f"  [INFO] Binary-search straggler bisection: "
        f"N=8 -> {b8['split_steps']} splits ({b8[' isolated_node' if False else 'isolated_node']}); "
        f"N=64 -> {b64['split_steps']} splits ({b64['isolated_node']}, saves {b64['linear_pairwise_runs_saved']} runs); "
        f"N=128 -> {b128['split_steps']} splits ({b128['isolated_node']}, saves {b128['linear_pairwise_runs_saved']} runs)"
    )
    check(
        "Binary bisection on N=8 nodes isolates dgx-05 in exactly ceil(log2(8)) = 3 split steps (4 total runs)",
        b8["correct"] is True
        and b8["split_steps"] == 3
        and b8["total_runs_including_initial"] == 4,
    )
    check(
        "Binary bisection on N=64 nodes isolates dgx-41 in ceil(log2(64)) = 6 split steps (7 total runs vs 64 linear runs, saving 58)",
        b64["correct"] is True
        and b64["split_steps"] == 6
        and b64["total_runs_including_initial"] == 7
        and b64["linear_pairwise_runs_saved"] == 58,
    )
    check(
        "Binary bisection on N=128 nodes isolates dgx-093 in ceil(log2(128)) = 7 split steps (8 total runs vs 128 linear runs, saving 121)",
        b128["correct"] is True
        and b128["split_steps"] == 7
        and b128["total_runs_including_initial"] == 8
        and b128["linear_pairwise_runs_saved"] == 121,
    )

    # 8. DAI Ch. 10 Training Scaling Efficiency, 64-GPU Fleet Waste, Iteration Breakdown, and Amdahl's Law
    sc = evaluate_training_scaling_and_bottlenecks()
    print(
        f"  [INFO] DAI Ch10 scaling: 8-GPU eff={sc['eight_gpu_efficiency_pct']}%, "
        f"64-GPU effective={sc['effective_gpus_64']} GPUs (wasted={sc['wasted_gpus_64']} GPUs, ${sc['wasted_cost_usd']}), "
        f"16-GPU iter={sc['iter_16_gpu_ms']}ms ({sc['comm_time_16_gpu_ms']}ms comm)"
    )
    check(
        "DAI Ch10: 6.5x speedup on 8 GPUs yields 0.8125 (81.25%) scaling efficiency, 16.67 min epoch, and 16.99% -> 47.78% 70B H100 MFU",
        sc["eight_gpu_speedup"] == 6.5
        and sc["eight_gpu_efficiency_ratio"] == 0.8125
        and sc["eight_gpu_efficiency_pct"] == 81.25
        and sc["predicted_16_gpu_speedup"] == 13.0
        and sc["epoch_minutes"] == 16.67
        and sc["mfu_before_pct"] == 16.99
        and sc["mfu_after_pct"] == 47.78,
    )
    check(
        "DAI Ch10: 64 GPUs at 52% scaling efficiency yields 33.28 (~33) effective GPUs and 30.72 (~31) wasted GPUs ($46,448.64 / ~$50k over 336 h at $4.50/GPU-hr)",
        sc["effective_gpus_64"] == 33.28
        and sc["wasted_gpus_64"] == 30.72
        and sc["wasted_gpu_hours"] == 10321.92
        and sc["wasted_cost_usd"] == 46448.64,
    )
    check(
        "DAI Ch10 Fig 10.1: Iteration time drops 155 ms (1 GPU, 0% comm) -> 33 ms (16 GPUs, 55% comm = 18.15 ms comm + 14.85 ms compute, 4.70x speedup)",
        sc["iter_1_gpu_ms"] == 155.0
        and sc["iter_16_gpu_ms"] == 33.0
        and sc["comm_time_16_gpu_ms"] == 18.15
        and sc["compute_time_16_gpu_ms"] == 14.85
        and sc["iter_speedup_16_gpu"] == 4.70,
    )
    check(
        "DAI Ch10 Amdahl's Law: 10% serial work bounds max speedup to 10.0x at infinite GPUs (8.77x at 64 GPUs, 13.70% efficiency)",
        sc["amdahl_infinite_max"] == 10.0
        and sc["amdahl_64_gpu"] == 8.77
        and sc["amdahl_64_efficiency_pct"] == 13.70,
    )

    # 9. DAI Ch. 10 LLM Inference Latency (`e2e_latency = TTFT + (output_tokens - 1) * ITL`) and Percentiles
    # System A: 100 ms avg (all requests 90-110 ms) vs System B: 80 ms avg (95% at 57.89 ms, 5% at 500 ms -> P99 = 500 ms violates 200 ms SLA)
    sys_a_lats = [90.0 + (i % 21) for i in range(105)]  # 5 full cycles of 90..110 -> mean 100.0 ms, P95 = 109.0 ms, P99 = 110.0 ms
    sys_b_lats = [57.89] * 95 + [500.0] * 5             # mean 80.0 ms, P50/P95 = 57.89 ms, P99 = 500.0 ms

    inf_short = evaluate_inference_latency_and_percentiles(
        ttft_ms=45.0, itl_ms=10.0, output_tokens=16, latencies_ms=sys_a_lats, sla_p99_ms=200.0
    )
    inf_long = evaluate_inference_latency_and_percentiles(
        ttft_ms=45.0, itl_ms=10.0, output_tokens=201, latencies_ms=sys_b_lats, sla_p99_ms=200.0
    )
    check(
        "DAI Ch10 e2e_latency = TTFT + (output_tokens - 1) * ITL: 16 tokens -> 195.0 ms (23.08% TTFT); 201 tokens -> 2045.0 ms (97.80% decode)",
        inf_short["e2e_latency_ms"] == 195.0
        and inf_short["decode_ms"] == 150.0
        and inf_short["ttft_share_pct"] == 23.08
        and inf_long["e2e_latency_ms"] == 2045.0
        and inf_long["decode_ms"] == 2000.0
        and round(100.0 - inf_long["ttft_share_pct"], 2) == 97.80,
    )
    check(
        "DAI Ch10 System A (100 ms mean, P95 = 109.0 ms, P99 = 110.0 ms <= 200 ms SLA) passes while System B (80 ms mean, P50 = 57.89 ms, P99 = 500.0 ms) fails",
        inf_short["mean_ms"] == 100.0
        and inf_short["p95_ms"] == 109.0
        and inf_short["p99_ms"] == 110.0
        and inf_short["passes_p99_sla"] == 1.0
        and inf_long["mean_ms"] == 80.0
        and inf_long["p50_ms"] == 57.89
        and inf_long["p99_ms"] == 500.0
        and inf_long["passes_p99_sla"] == 0.0,
    )

    # 10. Input validation guard
    raised = False
    try:
        compute_algbw_and_busbw("unknown_collective", 1024, 10.0, 8)
    except FabricBenchmarkError:
        raised = True
    check("Invalid collective name raises FabricBenchmarkError", raised)

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
