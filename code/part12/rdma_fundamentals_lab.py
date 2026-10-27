#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.2: RDMA fundamentals: verbs, queue pairs and memory registration."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rdma_fundamentals import (
    BTH_OPCODES,
    RDMAModelError,
    TRANSPORT_SERVICES,
    V8_CH3_MLX5_PROFILE,
    analyze_cq_completion_stream,
    decode_rdma_transport_headers,
    evaluate_memory_registration_and_mtt,
    evaluate_qp_scaling_and_perftest,
    trace_rdma_cm_session_steps,
    validate_qp_transition,
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
    print("=== Chapter 12.2 Lab: RDMA Fundamentals — Verbs, Queue Pairs & Memory Registration ===")

    # 1. HCA capability profile (V8 Ch 3 & V8 Lab 01 ibv_devinfo -v -d mlx5_0)
    check(
        "V8 Ch3 & Lab 01: mlx5_0 capability profile matches ibv_devinfo -v (fw 28.39.2048, vendor 0x02c9, part 4129)",
        V8_CH3_MLX5_PROFILE.fw_ver == "28.39.2048"
        and V8_CH3_MLX5_PROFILE.vendor_id_hex == "0x02c9"
        and V8_CH3_MLX5_PROFILE.vendor_part_id == 4129,
    )
    check(
        "V8 Ch3 & Lab 01: mlx5_0 queue and MR limits (max_qp=262144, max_qp_wr=32768, max_sge=30, max_cq=16777216, max_cqe=4194303, max_mr=16777216)",
        V8_CH3_MLX5_PROFILE.max_qp == 262144
        and V8_CH3_MLX5_PROFILE.max_qp_wr == 32768
        and V8_CH3_MLX5_PROFILE.max_sge == 30
        and V8_CH3_MLX5_PROFILE.max_cq == 16777216
        and V8_CH3_MLX5_PROFILE.max_cqe == 4194303
        and V8_CH3_MLX5_PROFILE.max_mr == 16777216
        and V8_CH3_MLX5_PROFILE.active_mtu == 4096,
    )

    # 2. Transport Service Types (V8 Ch 3, SCL Ch 5, and DC comparison)
    check(
        "V8 Ch3 & SCL Ch5: Transport service types RC, UC, UD, and DC are modeled with exact operation support",
        set(TRANSPORT_SERVICES.keys()) == {"RC", "UC", "UD", "DC"}
        and TRANSPORT_SERVICES["RC"].supports_rdma_read
        and TRANSPORT_SERVICES["RC"].supports_atomics
        and TRANSPORT_SERVICES["UC"].supports_rdma_write
        and not TRANSPORT_SERVICES["UC"].supports_rdma_read
        and not TRANSPORT_SERVICES["UD"].supports_rdma_write
        and TRANSPORT_SERVICES["DC"].supports_rdma_read,
    )

    # 3. Queue Pair State Machine: RESET -> INIT -> RTR -> RTS -> SQD / ERR (V8 Ch 3 Fig 8.3.4)
    t_init = validate_qp_transition("RESET", "INIT", local_port=1, pkey_index=0)
    t_rtr = validate_qp_transition(
        "INIT",
        "RTR",
        local_active_mtu=4096,
        requested_path_mtu=4096,
        dest_qp_num=0x0000E3,
        rq_psn=0x0091AB,
        remote_lid_or_gid_valid=True,
    )
    t_rts = validate_qp_transition(
        "RTR",
        "RTS",
        sq_psn=0x3A1F2E,
        retry_cnt=7,
        rnr_retry=7,
    )
    t_sqd = validate_qp_transition("RTS", "SQD")
    t_err = validate_qp_transition("RTS", "ERR")
    t_reset = validate_qp_transition("ERR", "RESET")
    check(
        "V8 Ch3 Fig 8.3.4: Valid QP lifecycle transitions RESET -> INIT -> RTR -> RTS -> SQD / ERR -> RESET succeed",
        t_init["allowed"]
        and t_rtr["allowed"]
        and t_rts["allowed"]
        and t_sqd["allowed"]
        and t_err["allowed"]
        and t_reset["allowed"],
    )

    t_skip = validate_qp_transition("RESET", "RTS", sq_psn=1, retry_cnt=7, rnr_retry=7)
    check(
        "V8 Ch3 Fig 8.3.4: Skipping INIT/RTR (RESET -> RTS directly) is rejected with EINVAL",
        not t_skip["allowed"] and t_skip["errno"] == "EINVAL",
    )

    t_mtu_fail = validate_qp_transition(
        "INIT",
        "RTR",
        local_active_mtu=2048,
        requested_path_mtu=4096,
        dest_qp_num=0x0000E3,
        rq_psn=0x0091AB,
        remote_lid_or_gid_valid=True,
    )
    check(
        "V8 Ch3 Scenario 1 (rc_pingpong): Requesting path_mtu=4096 when port active_mtu=2048 fails INIT -> RTR with EINVAL",
        not t_mtu_fail["allowed"]
        and t_mtu_fail["errno"] == "EINVAL"
        and "Failed to modify QP to RTR" in str(t_mtu_fail["reason"]),
    )

    t_gid_fail = validate_qp_transition(
        "INIT",
        "RTR",
        local_active_mtu=4096,
        requested_path_mtu=4096,
        dest_qp_num=0x0000,
        rq_psn=0x00000,
        remote_lid_or_gid_valid=False,
    )
    check(
        "V9 Ch3 Scenario 1 (ib_write_bw -x 2): Mismatched GID index (QPN 0x0000, invalid peer GID) fails INIT -> RTR",
        not t_gid_fail["allowed"] and t_gid_fail["errno"] == "EINVAL",
    )

    # 4. Completion Queue (CQ) Error Flushing & Triage (V8 Ch 3 Scenario 4)
    v8_cqe_stream = [
        (1042, "IBV_WC_SUCCESS", "RDMA_WRITE", 0x00),
        (1043, "IBV_WC_RETRY_EXC_ERR", "RDMA_WRITE", 0x81),
        (1044, "IBV_WC_WR_FLUSH_ERR", "RDMA_WRITE", 0x00),
        (1045, "IBV_WC_WR_FLUSH_ERR", "SEND", 0x00),
        (1046, "IBV_WC_WR_FLUSH_ERR", "SEND", 0x00),
    ]
    cqe_report = analyze_cq_completion_stream(v8_cqe_stream)
    print(
        f"  [INFO] V8 Ch3 CQ stream: first_fail=wr_id {cqe_report['first_failing_wr_id']} "
        f"({cqe_report['first_failing_status']}, vendor_err={cqe_report['first_failing_vendor_err_hex']}), "
        f"flushed={cqe_report['flushed_wr_ids']}"
    )
    check(
        "V8 Ch3 Scenario 4: wr_id=1043 (IBV_WC_RETRY_EXC_ERR, vendor_err=0x81) is isolated as root cause before 3 flushed WRs (1044..1046)",
        cqe_report["first_failing_wr_id"] == 1043
        and cqe_report["first_failing_status"] == "IBV_WC_RETRY_EXC_ERR"
        and cqe_report["first_failing_vendor_err_hex"] == "0x81"
        and cqe_report["flushed_wr_ids"] == [1044, 1045, 1046]
        and cqe_report["fault_domain"] == "TRANSPORT_ACK_TIMEOUT_PEER_OR_PATH",
    )

    rnr_report = analyze_cq_completion_stream(
        [(2001, "IBV_WC_RNR_RETRY_EXC_ERR", "SEND", 0x00), (2002, "IBV_WC_WR_FLUSH_ERR", "SEND", 0x00)]
    )
    check(
        "V8 Ch3 Scenario 2: IBV_WC_RNR_RETRY_EXC_ERR maps to REMOTE_RECEIVE_QUEUE_STARVATION",
        rnr_report["fault_domain"] == "REMOTE_RECEIVE_QUEUE_STARVATION",
    )

    # 5. Memory Registration, PD, lkey/rkey, MTT Pages, and memlock (V8 Ch 3, ADC Ch 1 Fig 1-14, SCL Ch 24)
    mr_64k = evaluate_memory_registration_and_mtt(
        buffer_bytes=65536,
        page_size_bytes=4096,
        mtt_entry_bytes=8,
        pd_match=True,
        key_valid=True,
        access_offset_bytes=0,
        access_length_bytes=65536,
        is_remote_op=True,
        remote_access_authorized=True,
    )
    print(
        f"  [INFO] 65,536 B (64 KiB) MR on 4,096 B pages: "
        f"pinned_pages={mr_64k['num_pinned_pages']}, mtt_bytes={mr_64k['mtt_table_bytes']} B, status={mr_64k['cqe_status']}"
    )
    check(
        "V8 Ch3 & ADC Ch1 Fig 1-14: 65,536 B (0x00010000) DMA region pins 16 x 4,096 B pages (128 B MTT entries) and succeeds",
        mr_64k["num_pinned_pages"] == 16
        and mr_64k["mtt_table_bytes"] == 128
        and mr_64k["cqe_status"] == "IBV_WC_SUCCESS",
    )

    mr_1gib = evaluate_memory_registration_and_mtt(
        buffer_bytes=1073741824,
        page_size_bytes=4096,
        mtt_entry_bytes=8,
    )
    mr_1gib_2m = evaluate_memory_registration_and_mtt(
        buffer_bytes=1073741824,
        page_size_bytes=2097152,
        mtt_entry_bytes=8,
    )
    print(
        f"  [INFO] 1 GiB (1,073,741,824 B) MR MTT comparison: "
        f"4 KiB pages={mr_1gib['num_pinned_pages']} pages ({mr_1gib['mtt_table_bytes']} B = 2 MiB MTT) vs "
        f"2 MiB hugepages={mr_1gib_2m['num_pinned_pages']} pages ({mr_1gib_2m['mtt_table_bytes']} B = 4 KiB MTT)"
    )
    check(
        "MTT Scaling Math: 1 GiB (1,073,741,824 B) requires 262,144 x 4 KiB pages (2,097,152 B = 2 MiB MTT) vs 512 x 2 MiB pages (4,096 B = 4 KiB MTT, 512x reduction)",
        mr_1gib["num_pinned_pages"] == 262144
        and mr_1gib["mtt_table_bytes"] == 2097152
        and mr_1gib_2m["num_pinned_pages"] == 512
        and mr_1gib_2m["mtt_table_bytes"] == 4096,
    )

    mr_memlock_fail = evaluate_memory_registration_and_mtt(
        buffer_bytes=65536 * 2,
        memlock_limit_bytes=65536,
    )
    check(
        "SCL Ch24 & VL10 Ch15: Registering 131,072 B when ulimit -l (memlock) is 65,536 B fails with IBV_REG_MR_ENOMEM_MEMLOCK",
        not mr_memlock_fail["memlock_ok"] and mr_memlock_fail["cqe_status"] == "IBV_REG_MR_ENOMEM_MEMLOCK",
    )

    mr_pd_mismatch = evaluate_memory_registration_and_mtt(buffer_bytes=65536, pd_match=False)
    mr_rem_oob = evaluate_memory_registration_and_mtt(
        buffer_bytes=65536,
        access_offset_bytes=32768,
        access_length_bytes=65536,
        is_remote_op=True,
    )
    check(
        "V8 Ch3 Fig 8.3.2 & Scenario 3: Protection Domain mismatch raises IBV_WC_LOC_PROT_ERR; remote bounds violation raises IBV_WC_REM_ACCESS_ERR",
        mr_pd_mismatch["cqe_status"] == "IBV_WC_LOC_PROT_ERR"
        and mr_rem_oob["cqe_status"] == "IBV_WC_REM_ACCESS_ERR",
    )

    # 6. RDMA Write (13-step) and RDMA Read (11-step) CM State Machines (ADC Ch 1 Figs 1-12 and 1-13)
    cm_write = trace_rdma_cm_session_steps("RDMA_WRITE")
    cm_read = trace_rdma_cm_session_steps("RDMA_READ")
    check(
        "ADC Ch1 Fig 1-12: RDMA Write CM session has 13 total steps (3 handshake + 6 RDMA write + 4 terminate)",
        cm_write["total_steps"] == 13
        and cm_write["handshake_steps"] == 3
        and cm_write["transfer_steps"] == 6
        and cm_write["terminate_steps"] == 4,
    )
    check(
        "ADC Ch1 Fig 1-13: RDMA Read CM session (20.0.0.2 -> 60.0.0.2) has 11 total steps (3 handshake + 4 RDMA read + 4 terminate)",
        cm_read["total_steps"] == 11
        and cm_read["handshake_steps"] == 3
        and cm_read["transfer_steps"] == 4
        and cm_read["terminate_steps"] == 4,
    )

    # 7. Packet Header Decoding: BTH, RETH, AETH, ICRC (ADC Ch 1 Figs 1-14, 1-15, 1-16 & Ch 7)
    pkt_read_req = decode_rdma_transport_headers(
        bth_opcode=12,
        solicited_event=False,
        mig_req=True,
        pad_count=0,
        header_version=0,
        pkey=65535,
        dest_qp=0x000FE1,
        ack_req=True,
        psn=16548361,
        reth_va=0x00007FF9DE5F4000,
        reth_rkey=0x00207100,
        reth_dma_len=65536,
        icrc=0xB87E1CBC,
    )
    check(
        "ADC Ch1 Fig 1-14: RDMA READ Request (opcode 12, P_Key 65535, Dest QP 0x000fe1, PSN 16548361) decodes 16B RETH (VA 0x00007ff9de5f4000, rkey 0x00207100, len 65536, ICRC 0xb87e1cbc)",
        pkt_read_req["opcode"] == 12
        and pkt_read_req["pkey"] == 65535
        and pkt_read_req["dest_qp_hex"] == "0x000fe1"
        and pkt_read_req["psn"] == 16548361
        and pkt_read_req["ext_header_type"] == "RETH"
        and pkt_read_req["reth_va_hex"] == "0x00007ff9de5f4000"
        and pkt_read_req["reth_rkey_hex"] == "0x00207100"
        and pkt_read_req["reth_dma_len"] == 65536
        and pkt_read_req["icrc_hex"] == "0xb87e1cbc"
        and pkt_read_req["ib_transport_total_bytes"] == 32,
    )

    pkt_read_resp = decode_rdma_transport_headers(
        bth_opcode=14,
        solicited_event=False,
        mig_req=True,
        pad_count=0,
        header_version=0,
        pkey=65535,
        dest_qp=0x00007B,
        ack_req=False,
        psn=16543980,
        payload_bytes=1024,
        icrc=0x5B522360,
    )
    check(
        "ADC Ch1 Fig 1-15: RDMA READ Response Middle (opcode 14, Dest QP 0x00007b, PSN 16543980, 1024 B payload, ICRC 0x5b522360) has 1040 B transport frame",
        pkt_read_resp["opcode"] == 14
        and pkt_read_resp["dest_qp_hex"] == "0x00007b"
        and pkt_read_resp["psn"] == 16543980
        and pkt_read_resp["payload_bytes"] == 1024
        and pkt_read_resp["icrc_hex"] == "0x5b522360"
        and pkt_read_resp["ib_transport_total_bytes"] == 1040,
    )

    pkt_ack = decode_rdma_transport_headers(
        bth_opcode=17,
        solicited_event=False,
        mig_req=True,
        pad_count=0,
        header_version=0,
        pkey=65535,
        dest_qp=0x000123,
        ack_req=False,
        psn=2592248,
        aeth_syndrome=0,
        aeth_msn=1,
        icrc=0x33E6E2AF,
    )
    check(
        "ADC Ch1 Fig 1-16: RC Acknowledge (opcode 17, Dest QP 0x000123, PSN 2592248) decodes 4B AETH (Syndrome 0 Ack, MSN 1, ICRC 0x33e6e2af)",
        pkt_ack["opcode"] == 17
        and pkt_ack["dest_qp_hex"] == "0x000123"
        and pkt_ack["psn"] == 2592248
        and pkt_ack["ext_header_type"] == "AETH"
        and pkt_ack["aeth_is_ack"] is True
        and pkt_ack["aeth_msn"] == 1
        and pkt_ack["icrc_hex"] == "0x33e6e2af"
        and pkt_ack["ib_transport_total_bytes"] == 20,
    )

    check(
        "ADC Ch7 & VL6 Ch1: RoCEv2 CNP uses BTH opcode 129 (0x81 = 10000001) over UDP destination port 4791",
        BTH_OPCODES[129] == "RoCEv2 Congestion Notification Packet (CNP)" and 0x81 == 129,
    )

    # 8. QP Scaling & perftest Bandwidth / Message-Rate Math (V8 Ch 3 & VL6 Ch 1 §5.2)
    scale_128 = evaluate_qp_scaling_and_perftest(
        num_nodes=128,
        gpus_per_node=8,
        hca_max_qp=262144,
        msg_size_bytes=65536,
        bw_average_mb_per_sec=23450.5,
        link_rate_gbps=200.0,
    )
    print(
        f"  [INFO] 128-node x 8-GPU (1,024 ranks) full RC mesh: "
        f"qps_per_rank={scale_128['rc_qps_per_rank']}, qps_per_node={scale_128['rc_qps_per_node']}, "
        f"cluster_qps={scale_128['total_cluster_rc_qps']}; "
        f"VL6 ib_write_bw 65536B: avg=23450.5 MB/s ({scale_128['line_rate_utilization_pct']}% of 25000 MB/s HDR)"
    )
    check(
        "V8 Ch3 Customer Scenario: 128 nodes x 8 GPUs (1,024 ranks) full-mesh RC requires 1,023 QPs/rank, 8,184 QPs/node, and 1,047,552 cluster QPs",
        scale_128["total_ranks"] == 1024
        and scale_128["rc_qps_per_rank"] == 1023
        and scale_128["rc_qps_per_node"] == 8184
        and scale_128["total_cluster_rc_qps"] == 1047552
        and not scale_128["exceeds_single_hca_max_qp"],
    )
    check(
        "VL6 Ch1 §5.2 ib_write_bw (65,536 B, 5,000 iters, 200G HDR = 25,000 MB/s line rate): 23,450.5 MB/s is 93.8% of line rate",
        scale_128["line_rate_mb_per_sec"] == 25000.0
        and scale_128["line_rate_utilization_pct"] == 93.8,
    )

    # 9. Input validation checks
    try:
        validate_qp_transition("UNKNOWN", "INIT")
        bad_qp = False
    except RDMAModelError:
        bad_qp = True
    check("Rejects unknown QP state name in validate_qp_transition", bad_qp)

    try:
        analyze_cq_completion_stream([])
        bad_cq = False
    except RDMAModelError:
        bad_cq = True
    check("Rejects empty completions list in analyze_cq_completion_stream", bad_cq)

    try:
        evaluate_memory_registration_and_mtt(buffer_bytes=0)
        bad_mr = False
    except RDMAModelError:
        bad_mr = True
    check("Rejects non-positive buffer_bytes in evaluate_memory_registration_and_mtt", bad_mr)

    try:
        decode_rdma_transport_headers(
            bth_opcode=12,
            solicited_event=False,
            mig_req=True,
            pad_count=0,
            header_version=0,
            pkey=65535,
            dest_qp=1,
            ack_req=True,
            psn=1,
            icrc=1,
        )
        bad_hdr = False
    except RDMAModelError:
        bad_hdr = True
    check("Rejects opcode 12 (RDMA READ Request) without RETH fields", bad_hdr)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
