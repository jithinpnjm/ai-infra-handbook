#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.18: NCCL debugging: hangs, timeouts and errors."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nccl_debugging_hangs import (
     FlightRecorderEntry,
    NCCL_RESULT_CODES,
    NCCLDebugModelError,
    analyze_flight_recorder_buffer,
    evaluate_asp_ch4_tables_and_pitfalls,
    evaluate_cross_layer_and_xid_triage,
    evaluate_shm_Requirement,
    parse_watchdog_and_classify_hang,
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
    print("=== Chapter 12.18 Lab: NCCL Debugging: Hangs, Timeouts and Errors ===")

    # 1. ncclResult_t error codes 0..6 verification
    check(
        "ncclResult_t error codes 0..6 (ncclSuccess..ncclRemoteError) are completely specified",
        set(NCCL_RESULT_CODES.keys()) == {0, 1, 2, 3, 4, 5, 6}
        and NCCL_RESULT_CODES[0].enum_name == "ncclSuccess"
        and NCCL_RESULT_CODES[1].enum_name == "ncclUnhandledCudaError"
        and NCCL_RESULT_CODES[2].enum_name == "ncclSystemError"
        and NCCL_RESULT_CODES[3].enum_name == "ncclInternalError"
        and NCCL_RESULT_CODES[4].enum_name == "ncclInvalidArgument"
        and NCCL_RESULT_CODES[5].enum_name == "ncclInvalidUsage"
        and NCCL_RESULT_CODES[6].enum_name == "ncclRemoteError",
    )
    check(
        "ncclUnhandledCudaError=1 and ncclRemoteError=6 map to exact log strings",
        NCCL_RESULT_CODES[1].log_string == "unhandled cuda error"
        and NCCL_RESULT_CODES[6].log_string == "remote process exited or there was a network error",
    )

    # 2. Watchdog caught collective operation timeout parsing & 4-way classification
    wd_line = (
        "[Rank 0] Watchdog caught collective operation timeout: "
        "WorkNCCL(SeqNum=4821, OpType=ALLREDUCE, NumelIn=268435456, "
        "NumelOut=268435456, Timeout(ms)=600000) ran for 600082.45 milliseconds"
    )

    # Case A: Upstream straggler starvation (Volume 20 Ch 3: rank 3 stuck at opCount 4820, SM=2%)
    rep_straggler = parse_watchdog_and_classify_hang(
        wd_line,
        world_size=4,
        rank_op_counts={0: 4821, 1: 4821, 2: 4821, 3: 4820},
        rank_sm_util_pct={0: 0.0, 1: 0.0, 2: 0.0, 3: 2.0},
    )
    print(
        f"  [INFO] Watchdog straggler parse: seq={rep_straggler.seq_num}, op={rep_straggler.op_type}, "
        f"timeout={rep_straggler.timeout_ms} ms, lagging={rep_straggler.lagging_ranks} -> {rep_straggler.classification}"
    )
    check(
        "Watchdog parser extracts Rank 0, SeqNum 4821, ALLREDUCE, 600000 ms (600.082 s)",
        rep_straggler.reporting_rank == 0
        and rep_straggler.seq_num == 4821
        and rep_straggler.op_type == "ALLREDUCE"
        and rep_straggler.timeout_ms == 600000
        and rep_straggler.work_ran_sec == 600.082,
    )
    check(
        "Volume 20 Ch 3: Rank 3 at opCount 4820 (2% SM util) vs Ranks 0..2 at 4821 classifies as upstream_straggler_starvation",
        rep_straggler.classification == "upstream_straggler_starvation"
        and rep_straggler.lagging_ranks == [3]
        and rep_straggler.dead_ranks == [],
    )

    # Case B: Dead rank / GPU Xid (e.g., Rank 2 hit Xid 79 fallen off bus)
    rep_dead = parse_watchdog_and_classify_hang(
        wd_line,
        world_size=4,
        rank_op_counts={0: 4821, 1: 4821, 2: 4820, 3: 4821},
        dead_or_xid_ranks=[2],
    )
    check(
        "Dead rank or GPU Tier 3 Xid (e.g. Xid 79 on Rank 2) classifies as dead_rank_or_gpu_xid",
        rep_dead.classification == "dead_rank_or_gpu_xid"
        and rep_dead.dead_ranks == [2]
        and rep_dead.lagging_ranks == [2],
    )

    # Case C: Rank desynchronization / missing conditional collective (divergent OpType or non-converging counts)
    rep_desync = parse_watchdog_and_classify_hang(
        wd_line,
        world_size=4,
        rank_op_counts={0: 4822, 1: 4821, 2: 4821, 3: 4821},
        rank_op_types={0: "ALLREDUCE", 1: "BROADCAST", 2: "BROADCAST", 3: "BROADCAST"},
    )
    check(
        "Divergent conditional collective across ranks classifies as rank_desync_divergent_collective",
        rep_desync.classification == "rank_desync_divergent_collective",
    )

    # Case D: Fabric transport drop (all ranks entered SeqNum 4821 ALLREDUCE together, RDMA retry errors > 0)
    rep_fabric = parse_watchdog_and_classify_hang(
        wd_line,
        world_size=4,
        rank_op_counts={0: 4821, 1: 4821, 2: 4821, 3: 4821},
        fabric_retry_errors=14,
    )
    check(
        "All ranks at SeqNum 4821 with RDMA retries classifies as fabric_transport_drop",
        rep_fabric.classification == "fabric_transport_drop"
        and rep_fabric.lagging_ranks == [],
    )

    # 3. PyTorch Flight Recorder (TORCH_FR_BUFFER_SIZE) ring buffer analysis
    fr_entries = [
        FlightRecorderEntry(rank=r, pg_name="0", seq_id=100, op_type="all_reduce", tensor_bytes=104857600, state="completed", duration_ms=4.1)
        for r in range(8)
    ] + [
        FlightRecorderEntry(rank=r, pg_name="0", seq_id=101, op_type="all_reduce", tensor_bytes=104857600, state="started", duration_ms=600000.0)
        for r in (0, 1, 2, 3, 4, 6, 7)  # Rank 5 never entered seq_id 101!
    ]
    fr_report = analyze_flight_recorder_buffer(fr_entries, world_size=8, buffer_capacity=2000)
    print(
        f"  [INFO] Flight Recorder analysis: target_seq_id={fr_report['target_seq_id']}, "
        f"missing_ranks={fr_report['missing_ranks']}, diagnosis={fr_report['diagnosis']}"
    )
    check(
        "Flight Recorder ring buffer pinpoints missing Rank 5 that never entered AllReduce seq_id 101",
        fr_report["target_seq_id"] == 101
        and fr_report["missing_ranks"] == [5]
        and fr_report["present_ranks"] == [0, 1, 2, 3, 4, 6, 7]
        and fr_report["diagnosis"] == "missing_rank_never_entered"
        and fr_report["highest_completed_per_rank"][5] == 100
        and fr_report["highest_seen_per_rank"][5] == 100,
    )

    # Flight Recorder collective desync check (mismatched op_type or tensor_bytes at seq_id 102)
    fr_desync_entries = [
        FlightRecorderEntry(rank=0, pg_name="0", seq_id=102, op_type="all_reduce", tensor_bytes=104857600, state="started", duration_ms=1000.0),
        FlightRecorderEntry(rank=1, pg_name="0", seq_id=102, op_type="all_gather", tensor_bytes=104857600, state="started", duration_ms=1000.0),
    ]
    fr_desync = analyze_flight_recorder_buffer(fr_desync_entries, world_size=2, buffer_capacity=2000)
    check(
        "Flight Recorder detects op_type mismatch (all_reduce vs all_gather) as collective_desync_mismatch",
        fr_desync["op_mismatch"] is True
        and fr_desync["diagnosis"] == "collective_desync_mismatch",
    )

    # Flight Recorder in-flight fabric stall check (all ranks entered seq_id 103, none completed)
    fr_in_flight = [
        FlightRecorderEntry(rank=r, pg_name="0", seq_id=103, op_type="all_reduce", tensor_bytes=104857600, state="started", duration_ms=600000.0)
        for r in range(4)
    ]
    fr_stall = analyze_flight_recorder_buffer(fr_in_flight, world_size=4, buffer_capacity=2000)
    check(
        "Flight Recorder detects all ranks started seq_id 103 without completion as in_flight_fabric_or_kernel_stall",
        fr_stall["missing_ranks"] == []
        and fr_stall["diagnosis"] == "in_flight_fabric_or_kernel_stall",
    )

    # 4. Container /dev/shm 64 MiB default exhaustion -> ncclSystemError (code 2, errno 28)
    shm_default = evaluate_shm_Requirement(
        local_ranks=8,
        num_channels=16,
        buffsize_bytes=4_194_304,
        num_communicators=2,
        container_shm_mib=64.0,
    )
    shm_fixed = evaluate_shm_Requirement(
        local_ranks=8,
        num_channels=16,
        buffsize_bytes=4_194_304,
        num_communicators=2,
        container_shm_mib=16384.0,  # 16 GiB /dev/shm
    )
    print(
        f"  [INFO] /dev/shm check: 8 GPUs x 16 channels x 4 MiB x 2 comms + control = {shm_default['required_shm_mib']} MiB "
        f"(64 MiB default -> {shm_default['nccl_result_enum']}, errno {shm_default['errno_code']})"
    )
    check(
        "Default 64 MiB container /dev/shm exhausts under 8 ranks (requires 1056.0 MiB) -> ncclSystemError (code 2, errno 28)",
        shm_default["required_shm_mib"] == 1056.0
        and shm_default["shm_exhausted"] is True
        and shm_default["nccl_result_code"] == 2
        and shm_default["nccl_result_enum"] == "ncclSystemError"
        and shm_default["errno_code"] == 28,
    )
    check(
        "Mounting 16 GiB (16384 MiB) /dev/shm in Docker/K8s resolves ncclSystemError -> ncclSuccess (code 0)",
        shm_fixed["shm_exhausted"] is False
        and shm_fixed["nccl_result_code"] == 0
        and shm_fixed["nccl_result_enum"] == "ncclSuccess",
    )

    # 5. ASP Ch 4 Tables 4-1, 4-2, 4-3, 4-4 and 6+6 Pitfalls
    asp = evaluate_asp_ch4_tables_and_pitfalls()
    check(
        "ASP Ch 4 Table 4-3: moving 48.0 ms init_process_group out of 0.5 ms AllReduce loop cuts step time 48.5 -> 0.5 ms (98.97%)",
        asp["table_4_3_init_destroy_ms"] == 48.0
        and asp["table_4_3_allreduce_ms"] == 0.5
        and asp["table_4_3_before_ms"] == 48.5
        and asp["table_4_3_after_ms"] == 0.5
        and asp["table_4_3_reduction_pct"] == 98.97,
    )
    check(
        "ASP Ch 4 Multinode Pitfall #1: Gloo 400 MB AllReduce (200.0 ms, 2.0 GB/s) vs NCCL (4.0 ms, 100.0 GB/s) = 50x speedup",
        asp["gloo_400mb_ms"] == 200.0
        and asp["gloo_400mb_gbps"] == 2.0
        and asp["nccl_400mb_ms"] == 4.0
        and asp["nccl_400mb_gbps"] == 100.0
        and asp["nccl_over_gloo_speedup_x"] == 50.0,
    )
    check(
        "ASP Ch 4 Tables 4-1 & 4-2 & DDP: 22.0->12.0 ms (45.45%), 100.0->70.0 ms (30.0%, SM 60%->90%), DP 45.0->DDP 30.0 ms (33.33%, 25 MiB bucket)",
        asp["overlap_reduction_pct"] == 45.45
        and asp["table_4_2_reduction_pct"] == 30.0
        and asp["table_4_2_sm_busy_before_pct"] == 60
        and asp["table_4_2_sm_busy_after_pct"] == 90
        and asp["ddp_speedup_pct"] == 33.33
        and asp["ddp_default_bucket_cap_mib"] == 25,
    )
    check(
        "ASP Ch 4 Multinode Pitfalls #3, #4, #6: ephemeral ports 50000..51000, 64 socket cap (2x2=4), UCX reserved 0.800->1.040->1.240 GB",
        asp["ephemeral_port_range"] == (50000, 51000)
        and asp["socket_max_connections"] == 64
        and asp["two_nic_socket_connections"] == 4
        and asp["ucx_reserved_gb_progression"] == [0.800, 1.040, 1.240]
        and asp["ucx_allocated_after_free_gb"] == 0.000,
    )
    check(
        "ASP Ch 4 Table 4-4: Meta Llama 3 405B 54-day run on 16,384 H100s had 419 interruptions (MTBI = 3.09 h, 1 GPU = 0.0061%)",
        asp["table_4_4_days"] == 54
        and asp["table_4_4_gpus"] == 16384
        and asp["table_4_4_single_gpu_fleet_share_pct"] == 0.0061
        and asp["table_4_4_total_interruptions"] == 419
        and asp["table_4_4_mtbi_hours"] == 3.09,
    )
    check(
        "ASP Ch 4 Table 4-4 GPU breakdown: Faulty GPU 148 (35.3%), HBM3 72 (17.2%), SRAM 19 (4.5%), GSP 17 (4.1%), SDC 6 (1.4%), Thermal 6 (1.4%) = 268 (64.0%)",
        asp["table_4_4_faulty_gpu_count"] == 148
        and asp["table_4_4_faulty_gpu_pct"] == 35.3
        and asp["table_4_4_hbm3_count"] == 72
        and asp["table_4_4_hbm3_pct"] == 17.2
        and asp["table_4_4_sram_count"] == 19
        and asp["table_4_4_gsp_count"] == 17
        and asp["table_4_4_sdc_count"] == 6
        and asp["table_4_4_thermal_count"] == 6
        and asp["table_4_4_gpu_category_count"] == 268
        and asp["table_4_4_gpu_category_pct"] == 64.0,
    )
    check(
        "ASP Ch 4 Table 4-4 Network/Software/Watchdog breakdown: SW bug 54 (12.9%), Switch/cable 35 (8.4%), Host maint 32 (7.6%), NIC 7 (1.7%), NCCL watchdog 7 (1.7%)",
        asp["table_4_4_sw_bug_count"] == 54
        and asp["table_4_4_sw_bug_pct"] == 12.9
        and asp["table_4_4_switch_cable_count"] == 35
        and asp["table_4_4_switch_cable_pct"] == 8.4
        and asp["table_4_4_host_maint_count"] == 32
        and asp["table_4_4_host_maint_pct"] == 7.6
        and asp["table_4_4_nic_count"] == 7
        and asp["table_4_4_nic_pct"] == 1.7
        and asp["table_4_4_nccl_watchdog_count"] == 7
        and asp["table_4_4_nccl_watchdog_pct"] == 1.7
        and asp["table_4_4_network_nic_watchdog_count"] == 49
        and asp["table_4_4_network_nic_watchdog_pct"] == 11.7,
    )
    check(
        "ASP Ch 4 NCCL Profiler Plugin API defines 5 callbacks and 32-bit event activation mask",
        asp["profiler_plugin_callbacks"] == ["init", "startEvent", "stopEvent", "recordEventState", "finalize"]
        and asp["profiler_plugin_event_mask_bits"] == 32,
    )

    # 6. Volume 20 & Volume 10 Ch 15 Cross-Layer Triage & Xid Verification
    triage = evaluate_cross_layer_and_xid_triage()
    check(
        "Volume 20 Ch 2, 4, 5, 7: Xid 3-tier classification (Tier 1: 45,63,92; Tier 2: 13,31,32,43,94; Tier 3: 48,61,62,64,79,95; NVLink: 74)",
        triage["xid_tier_1"] == [45, 63, 92]
        and triage["xid_tier_2"] == [13, 31, 32, 43, 94]
        and triage["xid_tier_3"] == [48, 61, 62, 64, 79, 95]
        and triage["xid_nvlink"] == 74,
    )
    check(
        "Volume 20 Ch 4: Asymmetric NVLink fault on GPU 2 Link 2 (184,213 CRC, 92,104 replay, 12 recovery errors -> Xid 74 & PIX fallback)",
        triage["nvlink_gpu2_link2_crc_errors"] == 184213
        and triage["nvlink_gpu2_link2_replay_errors"] == 92104
        and triage["nvlink_gpu2_link2_recovery_errors"] == 12,
    )
    check(
        "Volume 20 Ch 3: Starved Rank 3 (opCount 4820 vs 4821, 2% SM, 61C, 78.3W, 47.31s batch fetch, 96% disk, 187G/41G = 4.56x shard imbalance)",
        triage["ch03_fast_op_count"] == 4821
        and triage["ch03_stalled_op_count"] == 4820
        and triage["ch03_rank3_sm_util_pct"] == 2
        and triage["ch03_batch_fetch_sec"] == 47.31
        and triage["ch03_pv_used_pct"] == 96
        and triage["ch03_shard3_to_shard0_ratio"] == 4.56,
    )
    check(
        "Volume 20 Ch 11: Straggler timing [125.3, 126.1, 1250.5, 124.8] ms yields min=124.8 ms, max=1250.5 ms, ratio=10.02x",
        triage["ch11_min_ms"] == 124.8
        and triage["ch11_max_ms"] == 1250.5
        and triage["ch11_imbalance_ratio"] == 10.02,
    )
    check(
        "Volume 20 Ch 12: Cross-layer 750 ms breakdown (data_load 60.0%, allreduce 20.0%, backward 8.0%) and Heisenbug overhead (10.0% smi, 50.0% nsys)",
        triage["ch12_data_load_pct"] == 60.0
        and triage["ch12_allreduce_pct"] == 20.0
        and triage["ch12_backward_pct"] == 8.0
        and triage["ch12_heisenbug_smi_overhead_pct"] == 10.0
        and triage["ch12_heisenbug_nsys_overhead_pct"] == 50.0,
    )
    check(
        "Volume 10 Ch 15: NCCL 2.24+ RAS port 28028 and Cumulus 5.12 RoCE defaults (PFC prio 3, DSCP 26->TC3, CNP DSCP 48->TC6, UDP 4791)",
        triage["ras_default_port"] == 28028
        and triage["roce_pfc_priority"] == 3
        and triage["roce_data_dscp"] == 26
        and triage["roce_cnp_dscp"] == 48
        and triage["roce_cnp_priority"] == 6
        and triage["roce_udp_port"] == 4791,
    )

    # 7. Input validation error handling check
    raised = False
    try:
        parse_watchdog_and_classify_hang("invalid line", world_size=4, rank_op_counts={0: 1, 1: 1, 2: 1, 3: 1})
    except NCCLDebugModelError:
        raised = True
    check("Invalid watchdog log line raises NCCLDebugModelError", raised)

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
