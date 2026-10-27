"""Chapter 12.21 Verification Lab: Storage networks, Ultra Ethernet and scale-up fabrics.

Run with:
    python3 -B code/part12/storage_uec_scaleup_lab.py
"""

from __future__ import annotations

import os
import sys
from typing import Callable, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage_uec_scaleup import (
    NVME_IO_OPCODES,
    NVME_TCP_CAPSULE_TYPES,
    RDMA_PRTYPE_MAP,
    UEC_DELIVERY_MODES,
    build_uet_packet_spec,
    calculate_nvme_tcp_pdu_packing,
    calculate_uec_rccc_and_cbfc,
    compare_rocev2_go_back_n_vs_uet_selective,
    compare_scaleup_technologies,
    evaluate_infiniband_storage_fabric,
    evaluate_suet_scaleup_fabric,
    evaluate_ualink_scaleup_fabric,
    trace_nvme_of_session,
)


def run_checks() -> int:
    checks: List[Tuple[str, Callable[[], bool]]] = []

    def add(desc: str, fn: Callable[[], bool]) -> None:
        checks.append((desc, fn))

    # --- Section 1: Storage Networks (ADC Ch 9) ---
    add(
        "1. NVMe-o-TCP session uses TCP port 8009, ICReq/ICResp PDUs, and runs on lossy IP fabrics",
        lambda: (
            (t := trace_nvme_of_session("tcp", in_capsule_write=False)).discovery_tcp_port == 8009
            and t.data_port == 8009
            and t.cm_udp_port is None
            and t.requires_lossless is False
            and "NVMe_TCP_ICReq_PDU" in t.ordered_stages
            and "CapsuleCmd(0x01,opcode=0x02)->C2HData(0x04)x4->CapsuleResp(CQE)" in t.ordered_stages
        ),
    )

    add(
        "2. NVMe-o-TCP capsule IDs map 0x01=CapsuleCmd, 0x02=CapsuleResp, 0x03=H2CData, 0x04=C2HData and opcodes 0x01=Write, 0x02=Read",
        lambda: (
            NVME_TCP_CAPSULE_TYPES[0x01] == "CapsuleCmd"
            and NVME_TCP_CAPSULE_TYPES[0x03] == "H2CData"
            and NVME_TCP_CAPSULE_TYPES[0x04] == "C2HData"
            and NVME_IO_OPCODES[0x01] == "Write"
            and NVME_IO_OPCODES[0x02] == "Read"
        ),
    )

    add(
        "3. Jumbo-frame MTU 9000 (MSS 8960B) packs 2 NVMe-o-TCP 4 KB in-capsule PDUs (4192B each) into one TCP segment",
        lambda: (
            (p := calculate_nvme_tcp_pdu_packing(mtu_bytes=9000, in_capsule_data_bytes=4096))["mss_bytes"] == 8960
            and p["single_pdu_bytes"] == 4192
            and p["pdus_per_segment"] == 2
        ),
    )

    add(
        "4. NVMe-o-RDMA over RoCEv2 discovers over TCP 8009 (RDMA_PRTYPE=0x04), negotiates QPs over UDP 4420, and transfers data over UDP 4791",
        lambda: (
            (r := trace_nvme_of_session("rdma", rdma_prtype=0x04)).discovery_tcp_port == 8009
            and r.cm_udp_port == 4420
            and r.data_port == 4791
            and r.rdma_prtype == 0x04
            and r.requires_lossless is True
            and "1:1" in r.sq_cq_to_qp_mapping
        ),
    )

    add(
        "5. NVMe-o-RDMA RDMA_PRTYPE codes map 0x02=InfiniBand, 0x04=RoCEv2, and 0x05=iWARP",
        lambda: (
            RDMA_PRTYPE_MAP[0x02] == "InfiniBand"
            and RDMA_PRTYPE_MAP[0x04] == "RoCEv2"
            and RDMA_PRTYPE_MAP[0x05] == "iWARP"
        ),
    )

    add(
        "6. InfiniBand storage fabric uses 16-bit LID (up to 48,000 nodes per subnet), 16 VLs, and 64-byte CBFC credits (64 credits for 4096B)",
        lambda: (
            (ib := evaluate_infiniband_storage_fabric(num_nodes=32000, active_vls=12, credit_bytes_Requested=4096))[
                "lid_bits"
            ]
            == 16
            and ib["max_subnet_nodes"] == 48000
            and ib["fits_single_subnet"] is True
            and ib["needs_grh"] is False
            and ib["max_vls"] == 16
            and ib["credit_unit_bytes"] == 64
            and ib["credits_needed"] == 64
        ),
    )

    add(
        "7. InfiniBand deployment exceeding 48,000 nodes requires inter-subnet routing with the Global Routing Header (GRH)",
        lambda: (
            (ib2 := evaluate_infiniband_storage_fabric(num_nodes=60000))["fits_single_subnet"] is False
            and ib2["needs_grh"] is True
        ),
    )

    # --- Section 2: Ultra Ethernet Consortium (UEC Spec v1.0, ADC Ch 12) ---
    add(
        "8. UET over UDP uses IP protocol 17, destination UDP port 49150, and UDP source port for dynamic path-spraying entropy",
        lambda: (
            (u := build_uet_packet_spec("udp", use_tss_security=False, use_uet_crc=True)).ip_protocol == 17
            and u.udp_dst_port == 49150
            and u.entropy_carrier == "UDP_Source_Port"
            and "JobID" in u.ses_fields
            and "PIDonFEP" in u.ses_fields
            and "ResourceIndex" in u.ses_fields
        ),
    )

    add(
        "9. UET over native IP uses IP protocol 253, omits the UDP header, and places Entropy directly in the PDS header within the 128B switch parse depth",
        lambda: (
            (ip_pkt := build_uet_packet_spec("ip", use_tss_security=False, use_uet_crc=True)).ip_protocol == 253
            and ip_pkt.udp_dst_port is None
            and ip_pkt.entropy_carrier == "PDS_Entropy_Field"
            and ip_pkt.pds_fields[0] == "Entropy"
            and ip_pkt.switch_parse_budget_bytes == 128
        ),
    )

    add(
        "10. UET enforces mutual exclusion between UET CRC and TSS (AES-GCM + ICV) security on the same packet",
        lambda: (
            build_uet_packet_spec("udp", use_tss_security=True, use_uet_crc=False).security_or_crc == "TSS(AES-GCM+ICV)"
            and _raises_value_error(lambda: build_uet_packet_spec("udp", use_tss_security=True, use_uet_crc=True))
        ),
    )

    add(
        "11. UEC delivery modes ROD and RUD are supported across AI Base, AI Full, and HPC profiles",
        lambda: (
            UEC_DELIVERY_MODES["ROD"]["reliable"] is True
            and UEC_DELIVERY_MODES["ROD"]["ordered"] is True
            and UEC_DELIVERY_MODES["RUD"]["reliable"] is True
            and UEC_DELIVERY_MODES["RUD"]["ordered"] is False
            and "AI Base" in UEC_DELIVERY_MODES["ROD"]["profiles"]
            and "AI Base" in UEC_DELIVERY_MODES["RUD"]["profiles"]
        ),
    )

    add(
        "12. UEC RUDI supports idempotent multi-writer gradient retries, while UUD omits PSNs/ACKs and is incompatible with TSS security",
        lambda: (
            UEC_DELIVERY_MODES["RUDI"]["idempotent_retry"] is True
            and UEC_DELIVERY_MODES["UUD"]["uses_psn_and_ack"] is False
            and UEC_DELIVERY_MODES["UUD"]["supports_tss_security"] is False
        ),
    )

    add(
        "13. UEC RCCC allocates receiver credits in 256-byte units inside a 24-bit ACK field (256 credits for a 64 KB transfer)",
        lambda: (
            (cm := calculate_uec_rccc_and_cbfc(requested_payload_bytes=65536))["rccc_credit_unit_bytes"] == 256
            and cm["rccc_ack_bits"] == 24
            and cm["rccc_credits_granted"] == 256
            and cm["rccc_fits_24bit_ack"] is True
        ),
    )

    add(
        "14. UEC link-level CBFC doubles virtual channels from 16 (InfiniBand VLs) to 32 VCs per port using PCS CtlOS CP_Update messages",
        lambda: (
            (cm := calculate_uec_rccc_and_cbfc(requested_payload_bytes=4096, cbfc_active_vcs=32))["uec_max_vcs"] == 32
            and cm["ib_max_vls"] == 16
            and cm["vc_expansion_vs_ib"] == 2
            and "CtlOS" in str(cm["cbfc_signaling"])
        ),
    )

    add(
        "15. Dropping packet 1 of a 64-packet window triggers 64 retransmissions under RoCEv2 Go-Back-N vs 1 selective retry under UET (64.0x reduction)",
        lambda: (
            (gbn := compare_rocev2_go_back_n_vs_uet_selective(window_packets=64, dropped_packet_index=1))[
                "rocev2_go_back_n_retransmissions"
            ]
            == 64
            and gbn["uet_selective_retransmissions"] == 1
            and gbn["bandwidth_saved_packets"] == 63
            and gbn["retransmission_reduction_factor"] == 64.0
        ),
    )

    # --- Section 3: Scale-Up Fabrics: SUE-T / ESUN and UALink 1.0 (ADC Ch 13) ---
    add(
        "16. SUE-T AFH Generation 2 uses a 6-byte compressed header for single-hop scale-up pods and a 12-byte non-compressed header for two-hop topologies",
        lambda: (
            evaluate_suet_scaleup_fabric(single_hop=True)["afh_gen2_bytes"] == 6
            and evaluate_suet_scaleup_fabric(single_hop=False)["afh_gen2_bytes"] == 12
        ),
    )

    add(
        "17. SUE-T Reliability Header (RH) encodes a 10-bit xPU ID (up to 1,024 endpoints) and 16-bit NPSN/APSN sequence numbers with up to 4096B SUE PDUs",
        lambda: (
            (sue := evaluate_suet_scaleup_fabric())["xpu_id_bits"] == 10
            and sue["max_xpus_addressed"] == 1024
            and sue["sequence_number_bits"] == 16
            and sue["max_sue_pdu_bytes"] == 4096
            and sue["base_flit_frame_bytes"] == 256
        ),
    )

    add(
        "18. SUE-T on-die ARM AXI 4.0 interface maps 5 channels (AR, AW, W requests on VC0; B, R responses on VC1) vs 1 raw stream on FIFO",
        lambda: (
            evaluate_suet_scaleup_fabric(on_die_interface="AXI4")["on_die_channels"]["channel_count"] == 5
            and len(evaluate_suet_scaleup_fabric(on_die_interface="AXI4")["on_die_channels"]["VC0_requests"]) == 3
            and len(evaluate_suet_scaleup_fabric(on_die_interface="AXI4")["on_die_channels"]["VC1_responses"]) == 2
            and evaluate_suet_scaleup_fabric(on_die_interface="FIFO")["on_die_channels"]["channel_count"] == 1
        ),
    )

    add(
        "19. UALink 1.0 supports 8 stations x 4 lanes x 200 Gbps = 32 lanes = 6.4 Tbps aggregate bandwidth per xPU accelerator",
        lambda: (
            (ual := evaluate_ualink_scaleup_fabric(stations_per_xpu=8, lanes_per_station=4, lane_rate_gbps=200))[
                "total_lanes_per_xpu"
            ]
            == 32
            and ual["aggregate_gbps"] == 6400
            and ual["aggregate_tbps"] == 6.4
        ),
    )

    add(
        "20. UALink Transaction Layer (TL) flits are 64 bytes (16 x 4B sectors, split into upper and lower 32B half-flits)",
        lambda: (
            (ual := evaluate_ualink_scaleup_fabric())["tl_flit_bytes"] == 64
            and ual["tl_half_flit_bytes"] == 32
            and ual["sectors_per_tl_flit"] == 16
        ),
    )

    add(
        "21. UALink Data Link (DL) packs 10 x 64B TL flits into one 640B DL flit (+ 40B FEC = 680B wire unit) aligned 1:1 with an RS(544,514)x10b PCS codeword",
        lambda: (
            (ual := evaluate_ualink_scaleup_fabric())["tl_flits_per_dl_flit"] == 10
            and ual["dl_flit_bytes"] == 640
            and ual["fec_overhead_bytes"] == 40
            and ual["wire_unit_bytes"] == 680
            and ual["pcs_codeword"] == "RS(544,514)x10b"
            and ual["dl_flits_per_pcs_codeword"] == 1
        ),
    )

    add(
        "22. UALink 1-way and 2-way PCS codeword interleaving cut FEC serialization latency by 4.0x and 2.0x compared to standard 4-way Ethernet interleaving",
        lambda: (
            evaluate_ualink_scaleup_fabric(interleave_way=1)["interleave_speedup_vs_4way_eth"] == 4.0
            and evaluate_ualink_scaleup_fabric(interleave_way=2)["interleave_speedup_vs_4way_eth"] == 2.0
        ),
    )

    add(
        "23. UALink UPLI exposes 4 channels (Req, OrigData, RD Res, WR Res) with 57-bit ReqAddr and 10-bit ACC-ID (up to 1,000 accelerators per pod)",
        lambda: (
            (ual := evaluate_ualink_scaleup_fabric())["upli_channels"] == ("Req", "OrigData", "RD Res", "WR Res")
            and ual["req_addr_bits"] == 57
            and ual["acc_id_bits"] == 10
            and ual["max_pod_accelerators"] == 1000
        ),
    )

    add(
        "24. UALink MMU address handle pipeline translates GVA -> NPA -> SPA across UALink Switches (ULS) using software PGAS coherence",
        lambda: (
            "GVA" in (ual := evaluate_ualink_scaleup_fabric())["address_translation"]
            and "NPA" in ual["address_translation"]
            and "SPA" in ual["address_translation"]
            and "PGAS" in ual["coherence_model"]
        ),
    )

    add(
        "25. Scale-up technology comparison verifies NVLink 5 (18 switches, 72 GPUs, 1.8 Tbps, 100-300 ns hardware coherence) vs PCIe 5.0 (500-1000 ns, 32 GT/s, 64 Gbps x16)",
        lambda: (
            (cmp := compare_scaleup_technologies())["NVLink_5_NVL72"]["switches_per_rack"] == 18
            and cmp["NVLink_5_NVL72"]["gpus_per_rack"] == 72
            and cmp["NVLink_5_NVL72"]["bidirectional_tbps_per_gpu"] == 1.8
            and cmp["NVLink_5_NVL72"]["latency_ns_range"] == (100, 300)
            and cmp["PCIe_5_x16"]["latency_ns_range"] == (500, 1000)
            and cmp["PCIe_5_x16"]["unidirectional_gbps"] == 64
            and cmp["CXL_3"]["latency_ns_range"] == (100, 300)
        ),
    )

    print("=== Chapter 12.21 Lab: Storage Networks, Ultra Ethernet and Scale-Up Fabrics ===")
    passed = 0
    failed = 0
    for desc, fn in checks:
        try:
            ok = bool(fn())
        except Exception as exc:
            ok = False
            print(f"  [FAIL] {desc} (exception: {exc})")
        else:
            if ok:
                print(f"  [PASS] {desc}")
            else:
                print(f"  [FAIL] {desc}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def _raises_value_error(fn: Callable[[], object]) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(run_checks())
