#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.1: AI traffic: collectives, incast and elephant flows."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_traffic_collectives import (
     AITrafficModelError,
    LOAD_BALANCING_PYRAMID,
    PARALLELISM_TRAFFIC_PROFILES,
    audit_rocev2_and_fabric_design,
    compute_collective_bytes_and_steps,
    compute_synchronous_efficiency,
    compute_tail_latency_jct,
    evaluate_multinode_pitfalls,
    size_two_tier_nonblocking_fattree,
    summarize_llama3_405b_interruptions,
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
    print("=== Chapter 12.1 Lab: AI Traffic, Collectives, Incast, and Elephant Flows ===")

    # 1. Parallelism Traffic Profiles (ADC Ch 1 & V7 Ch 1 / Ch 3)
    check(
        "ADC Ch1 & V7 Ch1: Data, Pipeline, and Tensor parallelism traffic profiles are modeled",
        set(PARALLELISM_TRAFFIC_PROFILES.keys())
        == {"DATA_PARALLELISM", "PIPELINE_PARALLELISM", "TENSOR_PARALLELISM"}
        and "AllReduce" in PARALLELISM_TRAFFIC_PROFILES["DATA_PARALLELISM"].primary_collectives
        and "900 GB/s" in PARALLELISM_TRAFFIC_PROFILES["TENSOR_PARALLELISM"].typical_interconnect_domain,
    )

    # 2. Job Completion Time (JCT) and Tail Latency Math (ADC Ch 1 Figs 1-4, 1-5, 1-6)
    jct_10 = compute_tail_latency_jct(num_tasks=10, normal_task_ms=1.0, straggler_task_ms=1000.0)
    print(
        f"  [INFO] ADC Ch1 n=10 tasks (1 ms normal, 1000 ms straggler): "
        f"serial_book_formula={jct_10['serial_book_formula_s']}s ({jct_10['serial_book_formula_ms']} ms), "
        f"serial_strict={jct_10['serial_strict_ms']} ms, parallel_wait={jct_10['parallel_wait_ms']} ms, "
        f"parallel_JCT={jct_10['parallel_actual_ms']} ms ({jct_10['parallel_inflation_factor']}x)"
    )
    check(
        "ADC Ch1 Fig 1-5: Serial tail latency for n=10 tasks (1 ms normal, 1 s taskX) yields 1.010 s (1010 ms) book formula and 1009 ms strict sum",
        jct_10["serial_book_formula_s"] == 1.010
        and jct_10["serial_book_formula_ms"] == 1010.0
        and jct_10["serial_strict_ms"] == 1009.0,
    )
    check(
        "ADC Ch1 Fig 1-6: Parallel tail latency for n=10 tasks (1 ms normal, 1000 ms taskX) makes fast tasks wait 999 ms for a 1000 ms (1 s) JCT",
        jct_10["parallel_wait_ms"] == 999.0
        and jct_10["parallel_actual_ms"] == 1000.0
        and jct_10["parallel_inflation_factor"] == 1000.0,
    )

    jct_100 = compute_tail_latency_jct(num_tasks=100, normal_task_ms=1.0, straggler_task_ms=1000.0)
    check(
        "ADC Ch1 Fig 1-4: In a 100-thread parallel job where 99 finish in 1 ms and 1 straggles at 1000 ms, JCT is governed by the worst thread (1000 ms)",
        jct_100["parallel_actual_ms"] == 1000.0 and jct_100["parallel_wait_ms"] == 999.0,
    )

    # 3. Synchronous Compute vs Communication Efficiency & Overlap (V7 Ch 1 & ASP Ch 4)
    v7_sync = compute_synchronous_efficiency(compute_ms=2.0, comm_sync_ms=50.0, overlapped_comm_fraction=0.0)
    print(
        f"  [INFO] V7 Ch1 10,000-GPU example (2 ms compute, 50 ms sync): "
        f"compute_to_comm_ratio={v7_sync['ratio_compute_to_comm_pct']}%, "
        f"serial_step={v7_sync['serial_step_ms']} ms, compute_share={v7_sync['serial_compute_share_pct']}%"
    )
    check(
        "V7 Ch1 §1: 2 ms compute vs 50 ms network sync yields 4.0% compute-to-sync ratio (3.85% of 52 ms step)",
        v7_sync["ratio_compute_to_comm_pct"] == 4.0
        and v7_sync["serial_step_ms"] == 52.0
        and v7_sync["serial_compute_share_pct"] == 3.85,
    )

    asp_overlap_1 = compute_synchronous_efficiency(compute_ms=10.0, comm_sync_ms=12.0, overlapped_comm_fraction=0.8333333)
    print(
        f"  [INFO] ASP Ch4 manual sync vs full overlap (10 ms compute, 12 ms all-reduce): "
        f"serial={asp_overlap_1['serial_step_ms']} ms, ideal_full_overlap={asp_overlap_1['ideal_full_overlap_ms']} ms "
        f"({asp_overlap_1['ideal_overlap_reduction_pct']}% reduction)"
    )
    check(
        "ASP Ch4 p.86: 10 ms compute + 12 ms all-reduce takes 22 ms without overlap vs 12 ms with full overlap (45.45% reduction)",
        asp_overlap_1["serial_step_ms"] == 22.0
        and asp_overlap_1["ideal_full_overlap_ms"] == 12.0
        and asp_overlap_1["ideal_overlap_reduction_pct"] == 45.45,
    )

    asp_table_4_2 = compute_synchronous_efficiency(compute_ms=40.0, comm_sync_ms=60.0, overlapped_comm_fraction=0.5)
    print(
        f"  [INFO] ASP Ch4 Tables 4-1 & 4-2 (100 ms no-overlap -> 70 ms with 50% comm overlap): "
        f"overlapped_step={asp_table_4_2['overlapped_step_ms']} ms, reduction={asp_table_4_2['step_time_reduction_pct']}%"
    )
    check(
        "ASP Ch4 Tables 4-1 & 4-2: 50% communication overlap cuts 100 ms iteration time to 70 ms (30.0% faster)",
        asp_table_4_2["serial_step_ms"] == 100.0
        and asp_table_4_2["overlapped_step_ms"] == 70.0
        and asp_table_4_2["step_time_reduction_pct"] == 30.0,
    )

    # 4. Collective Communication Algorithms: Ring, Tree, and SHARP / NVLS (ASP Ch 4)
    coll_8 = compute_collective_bytes_and_steps(data_size_bytes=100_000_000, num_gpus=8)
    print(
        f"  [INFO] ASP Ch4 8-GPU 100 MB collective: chunk={coll_8['chunk_bytes']/1e6:.2f} MB, "
        f"ring_RS={coll_8['ring_rs_or_ag_bytes']/1e6:.2f} MB, ring_AR={coll_8['ring_allreduce_bytes']/1e6:.2f} MB "
        f"({int(coll_8['ring_allreduce_steps'])} steps), tree_AR_steps={int(coll_8['tree_allreduce_steps'])}, "
        f"SHARP_RS={coll_8['sharp_endpoint_rs_bytes']/1e6:.2f} MB (1/{int(coll_8['sharp_volume_reduction_factor'])} of ring)"
    )
    check(
        "ASP Ch4 p.394: 8-GPU Ring All-Reduce of 100 MB transfers 2*B*(n-1)/n = 175 MB in 14 steps (12.5 MB per step, 87.5 MB per RS/AG phase)",
        coll_8["chunk_bytes"] == 12_500_000.0
        and coll_8["ring_rs_or_ag_bytes"] == 87_500_000.0
        and coll_8["ring_allreduce_bytes"] == 175_000_000.0
        and coll_8["ring_allreduce_steps"] == 14.0,
    )
    check(
        "ASP Ch4 p.736: On 8 GPUs, SHARP / NVLS in-network Reduce-Scatter cuts per-endpoint receive volume to B/n = 12.5 MB, which is 1/(n-1) = 1/7 of full-ring (87.5 MB)",
        coll_8["sharp_endpoint_rs_bytes"] == 12_500_000.0
        and coll_8["sharp_volume_reduction_factor"] == 7.0
        and abs(coll_8["sharp_vs_ring_volume_ratio"] - (1.0 / 7.0)) < 1e-5,
    )

    coll_1024 = compute_collective_bytes_and_steps(data_size_bytes=1_073_741_824, num_gpus=1024)
    print(
        f"  [INFO] 1024-GPU 1 GiB collective: ring_AR_steps={int(coll_1024['ring_allreduce_steps'])}, "
        f"tree_AR_steps={int(coll_1024['tree_allreduce_steps'])}, "
        f"SHARP_factor=1/{int(coll_1024['sharp_volume_reduction_factor'])}"
    )
    check(
        "ASP Ch4 & V7 Ch9: At 1,024 GPUs, Ring All-Reduce requires 2,046 steps O(N) vs 20 steps O(log N) for a binary Tree, and SHARP cuts endpoint RS volume by 1/1023",
        coll_1024["ring_allreduce_steps"] == 2046.0
        and coll_1024["tree_allreduce_steps"] == 20.0
        and coll_1024["sharp_volume_reduction_factor"] == 1023.0,
    )

    # 5. Multi-Node Pitfalls: Gloo vs NCCL, DP vs DDP, Repeated Init, Socket Limit (ASP Ch 4)
    pitfalls = evaluate_multinode_pitfalls()
    print(
        f"  [INFO] ASP Ch4 pitfalls: Gloo={pitfalls['gloo_gbps']} GB/s vs NCCL={pitfalls['nccl_gbps']} GB/s "
        f"({pitfalls['nccl_vs_gloo_speedup']}x); DP->DDP saving={pitfalls['ddp_time_saving_pct']}%; "
        f"Repeated init={pitfalls['bad_iter_ms']} ms -> {pitfalls['good_iter_ms']} ms ({pitfalls['init_saving_pct']}% reduction)"
    )
    check(
        "ASP Ch4 pp.274-281: 400 MB All-Reduce on Gloo (CPU/TCP) takes 200 ms (2.0 GB/s) vs 4 ms (100.0 GB/s, 50x faster) on NCCL over 800 Gb/s IB",
        pitfalls["gloo_gbps"] == 2.0
        and pitfalls["nccl_gbps"] == 100.0
        and pitfalls["nccl_vs_gloo_speedup"] == 50.0,
    )
    check(
        "ASP Ch4 pp.521-525: Switching from nn.DataParallel (45 ms) to DistributedDataParallel (30 ms) reduces step time by 33.33% (~33%)",
        pitfalls["ddp_time_saving_pct"] == 33.33,
    )
    check(
        "ASP Ch4 Table 4-3: Moving init_process_group (48.0 ms) outside the loop cuts per-iteration time from 48.5 ms to 0.5 ms (98.97% > 98% reduction)",
        pitfalls["bad_iter_ms"] == 48.5
        and pitfalls["good_iter_ms"] == 0.5
        and pitfalls["init_saving_pct"] == 98.97,
    )
    check(
        "ASP Ch4 p.299 & p.617: NCCL_SOCKET_NTHREADS=2 * NCCL_NSOCKS_PERTHREAD=2 = 4 connections (<= 64 limit)",
        pitfalls["total_socket_connections"] == 4 and pitfalls["socket_limit_ok"] is True,
    )
    bad_sockets = evaluate_multinode_pitfalls(socket_nthreads=16, nsocks_per_thread=8)
    check(
        "ASP Ch4 p.617: NCCL_SOCKET_NTHREADS=16 * NCCL_NSOCKS_PERTHREAD=8 = 128 connections violates the 64-connection ceiling",
        bad_sockets["total_socket_connections"] == 128 and bad_sockets["socket_limit_ok"] is False,
    )

    # 6. Meta Llama 3 405B 54-Day Interruption Root-Cause Breakdown (ASP Ch 4 Table 4-4)
    llama_stats = summarize_llama3_405b_interruptions()
    print(
        f"  [INFO] ASP Ch4 Table 4-4 (Llama 3 405B 54-day run): total={llama_stats['total_interruptions']} interruptions "
        f"across {llama_stats['num_categories']} categories; network+NIC+watchdog={llama_stats['network_nic_watchdog_total']}"
    )
    check(
        "ASP Ch4 Table 4-4: Meta 54-day Llama 3 405B run recorded 419 total interruptions across 18 categories (148 Faulty GPU = 35.3%, 72 HBM3 = 17.2%)",
        llama_stats["duration_days"] == 54
        and llama_stats["num_categories"] == 18
        and llama_stats["total_interruptions"] == 419
        and llama_stats["faulty_gpu_count"] == 148
        and llama_stats["faulty_gpu_pct"] == 35.3,
    )
    check(
        "ASP Ch4 Table 4-4: Network switches/cables caused 35 interruptions (8.4%), NICs 7 (1.7%), and NCCL watchdog timeouts 7 (1.7%), totaling 49 events",
        llama_stats["network_switch_cable_count"] == 35
        and llama_stats["network_switch_cable_pct"] == 8.4
        and llama_stats["nic_count"] == 7
        and llama_stats["nccl_watchdog_count"] == 7
        and llama_stats["network_nic_watchdog_total"] == 49,
    )

    # 7. Load-Balancing Pyramid & Lossless RoCEv2 / Fabric Design Audits (ADC Ch 1 & 2, V7 Ch 11)
    check(
        "ADC Ch2 Fig 2-3: Four-tier load-balancing pyramid orders SLB (1) < DLB (2) < GLB (3) < sDLB (4)",
        [LOAD_BALANCING_PYRAMID[k].pyramid_level for k in ("SLB", "DLB", "GLB", "SDLB")] == [1, 2, 3, 4]
        and "4791" in LOAD_BALANCING_PYRAMID["SLB"].decision_inputs
        and "Next-to-Next-Hop" in LOAD_BALANCING_PYRAMID["GLB"].decision_inputs
        and "Base Transport Header" in LOAD_BALANCING_PYRAMID["SDLB"].decision_inputs,
    )

    good_fabric = audit_rocev2_and_fabric_design(
        udp_dest_port=4791,
        load_balancing_mode="GLB",
        ecn_enabled=True,
        pfc_enabled=True,
        spine_oversubscription_ratio=1.0,
        compute_and_storage_share_switch=False,
    )
    check(
        "ADC Ch1/Ch2 & V7 Ch11: RoCEv2 port 4791 + GLB/sDLB + DCQCN (ECN+PFC) + 1:1 non-blocking + isolated storage plane passes audit",
        good_fabric["healthy"] is True and len(good_fabric["findings"]) == 0,
    )

    bad_fabric = audit_rocev2_and_fabric_design(
        udp_dest_port=4791,
        load_balancing_mode="SLB",
        ecn_enabled=False,
        pfc_enabled=False,
        spine_oversubscription_ratio=2.0,
        compute_and_storage_share_switch=True,
    )
    check(
        "ADC Ch2 & V7 Ch1/Ch11: Flags SLB 5-tuple collisions, missing ECN/PFC, 2:1 spine oversubscription, and storage/compute switch sharing",
        bad_fabric["healthy"] is False and len(bad_fabric["findings"]) == 4,
    )

    # 8. 2-Tier Non-Blocking Fat-Tree Port Math (V7 Ch 11 Scenario 1)
    ft_1024 = size_two_tier_nonblocking_fattree(num_servers=128, nics_per_server=8, switch_radix_ports=64)
    print(
        f"  [INFO] V7 Ch11 128-server (1,024-GPU) fat-tree on 64-port Quantum-2: "
        f"leaf_groups={ft_1024['num_leaf_groups']}, leaves={ft_1024['total_leaf_switches']}, "
        f"spines={ft_1024['total_spine_switches']}, uplinks={ft_1024['total_uplinks']}"
    )
    check(
        "V7 Ch11 Scenario 1: 128 DGX H100 servers (1,024 GPUs) on 64-port switches require 4 leaf groups (32 leaves, 32 down / 32 up) and 16 spines (1:1 non-blocking)",
        ft_1024["total_gpus"] == 1024
        and ft_1024["downlinks_per_leaf"] == 32
        and ft_1024["uplinks_per_leaf"] == 32
        and ft_1024["num_leaf_groups"] == 4
        and ft_1024["total_leaf_switches"] == 32
        and ft_1024["total_uplinks"] == 1024
        and ft_1024["total_spine_switches"] == 16,
    )

    # 9. Input Validation & Error Handling Checks
    raised_jct = False
    try:
        compute_tail_latency_jct(num_tasks=1, normal_task_ms=1.0, straggler_task_ms=1000.0)
    except AITrafficModelError:
        raised_jct = True
    check("compute_tail_latency_jct rejects num_tasks < 2", raised_jct)

    raised_sync = False
    try:
        compute_synchronous_efficiency(compute_ms=10.0, comm_sync_ms=12.0, overlapped_comm_fraction=1.5)
    except AITrafficModelError:
        raised_sync = True
    check("compute_synchronous_efficiency rejects overlapped_comm_fraction outside [0, 1]", raised_sync)

    raised_coll = False
    try:
        compute_collective_bytes_and_steps(data_size_bytes=0, num_gpus=8)
    except AITrafficModelError:
        raised_coll = True
    check("compute_collective_bytes_and_steps rejects non-positive data_size_bytes", raised_coll)

    raised_lb = False
    try:
        audit_rocev2_and_fabric_design(4791, "INVALID_LB", True, True, 1.0, False)
    except AITrafficModelError:
        raised_lb = True
    check("audit_rocev2_and_fabric_design rejects unknown load-balancing mode", raised_lb)

    raised_ft = False
    try:
        size_two_tier_nonblocking_fattree(num_servers=100, nics_per_server=8, switch_radix_ports=64)
    except AITrafficModelError:
        raised_ft = True
    check("size_two_tier_nonblocking_fattree rejects server counts not divisible by downlinks_per_leaf", raised_ft)

    raised_pitfall = False
    try:
        evaluate_multinode_pitfalls(tensor_mb=0.0)
    except AITrafficModelError:
        raised_pitfall = True
    check("evaluate_multinode_pitfalls rejects non-positive tensor_mb", raised_pitfall)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
