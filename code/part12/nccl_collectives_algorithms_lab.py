#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.15: NCCL: collectives and algorithms."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nccl_collectives_algorithms import (
    COLLECTIVE_PRIMITIVES,
    NCCL_ALGORITHMS,
    NCCL_PROTOCOLS,
    NCCLCollectiveModelError,
    compare_ring_vs_tree_crossover,
    compute_collective_volume_and_busbw,
    compute_sharp_and_nvls_offload_math,
    evaluate_dai_ch2_benchmarks,
    evaluate_overlap_and_communicator_pitfalls,
    evaluate_protocol_framing,
    evaluate_zero_copy_registration,
    plan_nvl72_wave_schedule,
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
    print("=== Chapter 12.15 Lab: NCCL Collectives and Algorithms ===")

    # 1. Core 6 NCCL Collectives Taxonomy
    check(
        "Core 6 NCCL collectives (AllReduce, ReduceScatter, AllGather, Broadcast, Reduce, AllToAll) are modeled",
        set(COLLECTIVE_PRIMITIVES.keys())
        == {"AllReduce", "ReduceScatter", "AllGather", "Broadcast", "Reduce", "AllToAll"}
        and COLLECTIVE_PRIMITIVES["AllReduce"].in_place_supported is True
        and COLLECTIVE_PRIMITIVES["AllToAll"].in_place_supported is False,
    )

    # 2. Ring AllReduce 2*(N-1) steps and 2*(N-1)/N * S volume math for N=2, 4, 8, 72
    ar_n2 = compute_collective_volume_and_busbw("AllReduce", tensor_bytes=100_000_000, num_gpus=2, elapsed_sec=0.001)
    ar_n4 = compute_collective_volume_and_busbw("AllReduce", tensor_bytes=100_000_000, num_gpus=4, elapsed_sec=0.001)
    ar_n8 = compute_collective_volume_and_busbw("AllReduce", tensor_bytes=100_000_000, num_gpus=8, elapsed_sec=0.001)
    ar_n72 = compute_collective_volume_and_busbw("AllReduce", tensor_bytes=72_000_000, num_gpus=72, elapsed_sec=0.001)

    print(
        f"  [INFO] Ring AllReduce (100 MB): N=2 steps={int(ar_n2['ring_steps'])}, factor={ar_n2['busbw_factor']}; "
        f"N=4 steps={int(ar_n4['ring_steps'])}, factor={ar_n4['busbw_factor']}; "
        f"N=8 steps={int(ar_n8['ring_steps'])}, factor={ar_n8['busbw_factor']}, bytes={int(ar_n8['per_rank_bytes_transferred'])}"
    )
    check(
        "DAI Ch2 & ASP Ch4: Ring AllReduce for N=2 has 2 steps and busbw factor 1.0 (algbw == busbw)",
        ar_n2["ring_steps"] == 2.0
        and ar_n2["busbw_factor"] == 1.0
        and ar_n2["per_rank_bytes_transferred"] == 100_000_000.0
        and ar_n2["algbw_gbps"] == ar_n2["busbw_gbps"],
    )
    check(
        "DAI Ch2: Ring AllReduce for N=4 has 6 steps and busbw factor 1.5x (150 MB per GPU for 100 MB tensor)",
        ar_n4["ring_steps"] == 6.0
        and ar_n4["busbw_factor"] == 1.5
        and ar_n4["per_rank_bytes_transferred"] == 150_000_000.0,
    )
    check(
        "ASP Ch4: Ring AllReduce for N=8 has 14 steps (7 RS + 7 AG) and busbw factor 1.75x (175 MB per GPU for 100 MB tensor)",
        ar_n8["ring_steps"] == 14.0
        and ar_n8["busbw_factor"] == 1.75
        and ar_n8["per_rank_bytes_transferred"] == 175_000_000.0
        and ar_n8["chunk_bytes"] == 12_500_000.0,
    )
    check(
        "ASP Ch4 & Ch19: Ring AllReduce for N=72 (NVL72) has 142 steps (71 per pass) and busbw factor 142/72 = 1.972222",
        ar_n72["ring_steps"] == 142.0
        and ar_n72["busbw_factor"] == round(142.0 / 72.0, 6)
        and ar_n72["per_rank_bytes_transferred"] == 142_000_000.0,
    )

    # 3. Busbw conversion factors across ReduceScatter, AllGather, AllToAll, Broadcast, Reduce
    rs_n8 = compute_collective_volume_and_busbw("ReduceScatter", tensor_bytes=100_000_000, num_gpus=8, elapsed_sec=0.001)
    ag_n8 = compute_collective_volume_and_busbw("AllGather", tensor_bytes=100_000_000, num_gpus=8, elapsed_sec=0.001)
    a2a_n8 = compute_collective_volume_and_busbw("AllToAll", tensor_bytes=100_000_000, num_gpus=8, elapsed_sec=0.001)
    bcast_n8 = compute_collective_volume_and_busbw("Broadcast", tensor_bytes=100_000_000, num_gpus=8, elapsed_sec=0.001)
    red_n8 = compute_collective_volume_and_busbw("Reduce", tensor_bytes=100_000_000, num_gpus=8, elapsed_sec=0.001)

    check(
        "DAI Ch1-2: ReduceScatter and AllGather on N=8 each take N-1=7 steps, factor (N-1)/N=0.875, and sum to AllReduce (14 steps, 175 MB)",
        rs_n8["ring_steps"] == 7.0
        and ag_n8["ring_steps"] == 7.0
        and rs_n8["busbw_factor"] == 0.875
        and ag_n8["busbw_factor"] == 0.875
        and (rs_n8["per_rank_bytes_transferred"] + ag_n8["per_rank_bytes_transferred"])
        == ar_n8["per_rank_bytes_transferred"],
    )
    check(
        "nccl-tests busbw factors: AllToAll uses (N-1)/N=0.875 on N=8 (87.5 MB remote), while Broadcast and Reduce use factor 1.0",
        a2a_n8["busbw_factor"] == 0.875
        and a2a_n8["per_rank_bytes_transferred"] == 87_500_000.0
        and bcast_n8["busbw_factor"] == 1.0
        and red_n8["busbw_factor"] == 1.0,
    )

    # 4. DAI Ch 2 Exact Microbenchmark & MFU Reproduction
    dai_bench = evaluate_dai_ch2_benchmarks()
    print(
        f"  [INFO] DAI Ch2 allreduce_microbench (N=2, 100 MiB, 50 iters, 0.248 s): "
        f"alg_bw={dai_bench['alg_bw_mb_s']} MB/s ({dai_bench['alg_bw_gib_s']} GB/s), "
        f"bus_bw={dai_bench['bus_bw_mb_s']} MB/s ({dai_bench['bus_bw_gib_s']} GB/s), "
        f"HBM_copy={dai_bench['single_gpu_copy_gib_s']} GB/s, 70B_MFU={dai_bench['mfu_pct']}%"
    )
    check(
        "DAI Ch2 p.793-795: 2-GPU 100 MiB AllReduce (50 iters in 0.248 s) yields 40,322.58 MB/s (39.38 GB/s) algbw and busbw",
        dai_bench["alg_bw_mb_s"] == 40322.58
        and dai_bench["bus_bw_mb_s"] == 40322.58
        and dai_bench["alg_bw_gib_s"] == 39.38
        and dai_bench["bus_bw_gib_s"] == 39.38,
    )
    check(
        "DAI Ch2 p.41-47 & p.745: Single-GPU 64 MiB read+write copy yields 1,980.45 GB/s and 70B model on H100 (860 TFLOP / 2.0 s / 989 TFLOPS) yields 430 TFLOPS (43.48% MFU)",
        dai_bench["single_gpu_copy_gib_s"] == 1980.45
        and dai_bench["actual_tflops"] == 430.0
        and dai_bench["mfu_pct"] == 43.48,
    )

    # 5. NCCL Algorithms Catalog & Ring vs Tree Crossover Math
    check(
        "ASP Ch4: All 5 NCCL algorithm families (RING, TREE, COLLNET, NVLS, PAT) are cataloged",
        set(NCCL_ALGORITHMS.keys()) == {"RING", "TREE", "COLLNET", "NVLS", "PAT"}
        and "NVLSTree" in NCCL_ALGORITHMS["NVLS"].nccl_algo_token,
    )

    cross_72_small = compare_ring_vs_tree_crossover(
        num_gpus=72, message_bytes=1_048_576, per_hop_latency_us=1.0, link_bw_gbps=100.0
    )
    cross_72_large = compare_ring_vs_tree_crossover(
        num_gpus=72, message_bytes=268_435_456, per_hop_latency_us=1.0, link_bw_gbps=100.0
    )
    print(
        f"  [INFO] 72-GPU Ring vs Tree: ring_1way={cross_72_small['ring_one_way_steps']} hops, "
        f"tree_floor_log2={cross_72_small['tree_floor_log2_steps']} steps (ceil={cross_72_small['tree_ceil_log2_steps']}), "
        f"1 MiB winner={cross_72_small['faster_algorithm']} ({cross_72_small['tree_total_us']} vs {cross_72_small['ring_total_us']} us), "
        f"256 MiB winner={cross_72_large['faster_algorithm']} ({cross_72_large['ring_total_us']} vs {cross_72_large['tree_total_us']} us), "
        f"crossover={cross_72_small['crossover_mib']} MiB"
    )
    check(
        "ASP Ch19 p.1122: On 72 GPUs (NVL72), 1-way Ring takes 71 sequential hops (142 AllReduce steps) vs floor(log2(72))=6 (ceil=7, 14 AllReduce steps) for Tree",
        cross_72_small["ring_one_way_steps"] == 71
        and cross_72_small["ring_allreduce_steps"] == 142
        and cross_72_small["tree_floor_log2_steps"] == 6
        and cross_72_small["tree_ceil_log2_steps"] == 7
        and cross_72_small["tree_allreduce_steps"] == 14,
    )
    check(
        "ASP Ch4 & Ch19: Tree wins for small 1 MiB messages on 72 GPUs while Ring wins above the crossover (~37.24 MiB)",
        cross_72_small["faster_algorithm"] == "TREE"
        and cross_72_large["faster_algorithm"] == "RING"
        and cross_72_small["crossover_mib"] == 37.24,
    )

    # 6. SHARP and NVLS In-Network Reduction & Multicast Math (ASP Ch 4)
    sharp_8 = compute_sharp_and_nvls_offload_math(tensor_bytes=800_000_000, num_gpus=8, ag_time_ms=10.0, rs_time_ms=10.0)
    sharp_72 = compute_sharp_and_nvls_offload_math(tensor_bytes=720_000_000, num_gpus=72, ag_time_ms=12.0, rs_time_ms=12.0)
    print(
        f"  [INFO] SHARP/NVLS offload: N=8 ring_RS={int(sharp_8['ring_rs_bytes_per_gpu'])} B vs "
        f"SHARP_RS={int(sharp_8['sharp_rs_bytes_per_gpu'])} B (ratio=1/{int(sharp_8['endpoint_reduction_factor'])}); "
        f"N=72 ratio=1/{int(sharp_72['endpoint_reduction_factor'])}; overlapped_wall_ratio={sharp_8['overlapped_wall_time_ratio']}"
    )
    check(
        "ASP Ch4 p.736-737: On N=8 GPUs (800 MB), SHARP/NVLS cuts ReduceScatter receive and AllGather send from 700 MB to 100 MB (1/(N-1) = 1/7)",
        sharp_8["ring_rs_bytes_per_gpu"] == 700_000_000.0
        and sharp_8["sharp_rs_bytes_per_gpu"] == 100_000_000.0
        and sharp_8["endpoint_reduction_factor"] == 7.0
        and sharp_8["endpoint_volume_ratio_vs_ring"] == round(1.0 / 7.0, 6),
    )
    check(
        "ASP Ch4 p.736-737: On N=72 GPUs (NVL72, 720 MB), NVLS cuts per-endpoint RS/AG volume from 710 MB to 10 MB (1/(N-1) = 1/71)",
        sharp_72["ring_rs_bytes_per_gpu"] == 710_000_000.0
        and sharp_72["sharp_rs_bytes_per_gpu"] == 10_000_000.0
        and sharp_72["endpoint_reduction_factor"] == 71.0,
    )
    check(
        "ASP Ch4 p.407 & p.737-740: Overlapped NVLS multicast AG + in-network RS cuts phase wall time by 1/2 (0.5), with 7.6x NVLink small-msg and 2x-5x SHARP speedups",
        sharp_8["overlapped_wall_time_ratio"] == 0.5
        and sharp_8["nvlink_small_msg_max_speedup_x"] == 7.6
        and sharp_8["sharp_large_scale_min_speedup_x"] == 2.0
        and sharp_8["sharp_large_scale_max_speedup_x"] == 5.0,
    )

    # 7. NCCL Protocols: LL (4B data + 4B flag = 50%), LL128 (120B data + 8B flag = 93.75%), Simple (100%)
    framing = evaluate_protocol_framing(payload_bytes=120_000)
    print(
        f"  [INFO] Protocol framing for 120 KB payload: "
        f"LL wire={int(framing['LL']['total_wire_bytes'])} B ({framing['LL']['efficiency_pct']}% eff), "
        f"LL128 wire={int(framing['LL128']['total_wire_bytes'])} B ({framing['LL128']['efficiency_pct']}% eff), "
        f"Simple wire={int(framing['Simple']['total_wire_bytes'])} B ({framing['Simple']['efficiency_pct']}% eff)"
    )
    check(
        "NCCL LL protocol: 8-byte atomic packet (4B payload + 4B flag) has 50.0% efficiency and 50.0% overhead (240 KB wire for 120 KB payload)",
        NCCL_PROTOCOLS["LL"].word_packet_bytes == 8
        and NCCL_PROTOCOLS["LL"].payload_bytes == 4
        and NCCL_PROTOCOLS["LL"].flag_bytes == 4
        and framing["LL"]["efficiency_pct"] == 50.0
        and framing["LL"]["overhead_pct"] == 50.0
        and framing["LL"]["total_wire_bytes"] == 240_000.0,
    )
    check(
        "NCCL LL128 protocol: 128-byte atomic transaction (120B payload + 8B flag) has 93.75% efficiency and 6.25% overhead (128 KB wire for 120 KB payload)",
        NCCL_PROTOCOLS["LL128"].word_packet_bytes == 128
        and NCCL_PROTOCOLS["LL128"].payload_bytes == 120
        and NCCL_PROTOCOLS["LL128"].flag_bytes == 8
        and framing["LL128"]["efficiency_pct"] == 93.75
        and framing["LL128"]["overhead_pct"] == 6.25
        and framing["LL128"]["total_wire_bytes"] == 128_000.0,
    )
    check(
        "NCCL Simple protocol: Bulk DMA into 4 MiB default NCCL_BUFFSIZE with __threadfence_system() has 100.0% framing efficiency",
        NCCL_PROTOCOLS["Simple"].word_packet_bytes == 4_194_304
        and framing["Simple"]["efficiency_pct"] == 100.0
        and framing["Simple"]["flag_bytes"] == 0.0,
    )

    # 8. Zero-Copy User Buffer Registration (`ncclCommRegister` / `ncclMemAlloc`, ASP Ch 4)
    zc_ok = evaluate_zero_copy_registration(
        all_ranks_registered=True, symmetric_head_offsets=True, allocator_type="ncclMemAlloc",
        num_channels_default=16, num_channels_zero_copy=4,
    )
    zc_asymmetric = evaluate_zero_copy_registration(
        all_ranks_registered=True, symmetric_head_offsets=False, allocator_type="ncclMemAlloc"
    )
    zc_partial = evaluate_zero_copy_registration(
        all_ranks_registered=False, symmetric_head_offsets=True, allocator_type="ncclMemAlloc"
    )
    check(
        "ASP Ch4 p.748-751: ncclCommRegister + ncclMemAlloc activates zero-copy, bypasses staging buffers, and saves 12 SM channel blocks when all ranks register with matching head offsets",
        zc_ok["zero_copy_active"] is True
        and zc_ok["staging_buffer_bypassed"] is True
        and zc_ok["nvls_sharp_zero_copy_eligible"] is True
        and zc_ok["sm_blocks_saved_per_gpu"] == 12
        and zc_ok["status"] == "ZERO_COPY_REGISTERED_ACTIVE",
    )
    check(
        "ASP Ch4 p.751: Zero-copy registration falls back to internal staging buffers if any rank omits registration or buffer head offsets mismatch",
        zc_asymmetric["zero_copy_active"] is False
        and zc_partial["zero_copy_active"] is False
        and zc_asymmetric["status"] == "FALLBACK_INTERNAL_STAGING_BUFFER",
    )

    # 9. NVL72 Wave Scheduling & Rotating Ring Endpoints (ASP Ch 19)
    waves = plan_nvl72_wave_schedule(
        total_gpus=72, ports_per_gpu=18, num_waves=4,
        total_concurrent_collectives=12, max_collectives_per_wave=4,
    )
    print(
        f"  [INFO] ASP Ch19 NVL72 wave schedule: {waves['num_waves']} waves of {waves['gpus_per_wave']} GPUs "
        f"(fits {waves['ports_per_gpu']} NVLink ports/GPU={waves['fits_port_capacity']}), "
        f"12 collectives -> {waves['collective_waves_for_burst']} waves of 4, rotated starts={waves['rotated_ring_start_ranks']}"
    )
    check(
        "ASP Ch19 p.1135 & p.1202: Splitting 72-GPU AllToAll into 4 waves of 18 GPUs matches 18 NVLink 5 ports per GPU without NVSwitch queueing",
        waves["gpus_per_wave"] == 18
        and waves["fits_port_capacity"] is True
        and waves["rotated_ring_start_ranks"] == [0, 18, 36, 54],
    )
    check(
        "ASP Ch19 p.1208-1209: Staggering 12 concurrent expert collectives into 3 waves of 4 stays within the 2-4 concurrency sweet spot",
        waves["collective_waves_for_burst"] == 3,
    )

    # 10. Overlap, Backend, Communicator Lifecycle, Fragmentation, Llama 3 405B, and NIXL Metrics (ASP Ch 4)
    pitfalls = evaluate_overlap_and_communicator_pitfalls()
    check(
        "ASP Ch4 p.86 & Tables 4-1/4-2: Manual no-overlap takes 22 ms (10+12) vs 12 ms overlapped; 50% overlap cuts 100 ms baseline to 70 ms and raises SM busy from 60% to 90%",
        pitfalls["no_overlap_total_ms"] == 22.0
        and pitfalls["full_overlap_total_ms"] == 12.0
        and pitfalls["table_4_1_baseline_ms"] == 100.0
        and pitfalls["table_4_1_overlapped_ms"] == 70.0
        and pitfalls["table_4_1_sm_busy_before_pct"] == 60.0
        and pitfalls["table_4_1_sm_busy_after_pct"] == 90.0,
    )
    check(
        "ASP Ch4 p.32 & p.521-525: DDP uses 25 MiB default buckets and finishes in 30.0 ms vs DataParallel's 45.0 ms (33.33% faster)",
        pitfalls["ddp_default_bucket_cap_mb"] == 25.0
        and pitfalls["dp_step_ms"] == 45.0
        and pitfalls["ddp_step_ms"] == 30.0
        and pitfalls["ddp_speedup_over_dp_pct"] == 33.33,
    )
    check(
        "ASP Ch4 p.274-281: 400 MB AllReduce on 800 Gb/s IB takes 200.0 ms (2.0 GB/s) on Gloo vs 4.0 ms (100.0 GB/s) on NCCL (50x faster)",
        pitfalls["gloo_400mb_ms"] == 200.0
        and pitfalls["gloo_400mb_gbps"] == 2.0
        and pitfalls["nccl_400mb_ms"] == 4.0
        and pitfalls["nccl_400mb_gbps"] == 100.0,
    )
    check(
        "ASP Ch4 Table 4-3 & p.605-618: Avoiding per-iteration init_process_group (48.0 ms) cuts 48.5 ms step to 0.5 ms (98.97% reduction); socket cap is 64 and default NCCL_BUFFSIZE is 4 MiB",
        pitfalls["repeated_init_overhead_ms"] == 48.0
        and pitfalls["repeated_init_total_ms"] == 48.5
        and pitfalls["tiny_allreduce_ms"] == 0.5
        and pitfalls["repeated_init_reduction_pct"] == 98.97
        and pitfalls["max_socket_connections_per_comm"] == 64
        and pitfalls["nccl_default_buffsize_bytes"] == 4_194_304,
    )
    check(
        "ASP Ch4 p.344-349 & Table 4-4: UCX reserved memory grows 0.800 -> 1.040 -> 1.240 GB; Llama 3 405B logged 419 interruptions (35 switch/cable, 7 NIC, 7 NCCL watchdog)",
        pitfalls["ucx_reserved_iter0_gb"] == 0.800
        and pitfalls["ucx_reserved_iter1_gb"] == 1.040
        and pitfalls["ucx_reserved_iter2_gb"] == 1.240
        and pitfalls["llama3_405b_total_interruptions"] == 419
        and pitfalls["llama3_405b_network_switch_cable"] == 35
        and pitfalls["llama3_405b_nic"] == 7
        and pitfalls["llama3_405b_nccl_watchdog"] == 7,
    )
    check(
        "ASP Ch4 p.888-895: NIXL KV cache offload yields 14x TTFT speedup on x86 H100, 2x additional speedup on GH200 (900 GB/s NVLink-C2C), and 30x Dynamo throughput on 680B NVL72",
        pitfalls["nixl_x86_h100_ttft_speedup_x"] == 14.0
        and pitfalls["nixl_gh200_vs_x86_ttft_speedup_x"] == 2.0
        and pitfalls["nixl_dynamo_680b_nvl72_speedup_x"] == 30.0,
    )

    # 11. Input Validation Guardrails
    raised = False
    try:
        compute_collective_volume_and_busbw("InvalidOp", tensor_bytes=100, num_gpus=8)
    except NCCLCollectiveModelError:
        raised = True
    check("Guardrail: Invalid collective name raises NCCLCollectiveModelError", raised)

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
