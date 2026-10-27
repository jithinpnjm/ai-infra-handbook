"""Chapter 12.21: Storage networks, Ultra Ethernet and scale-up fabrics.

Pure Python 3 standard-library reference models for:
1. Storage Networks (ADC Ch. 9):
   - Local PCIe Gen5/Gen6 vs remote NVMe-oF (InfiniBand ~300 ns, Ethernet ~700-900 ns / 800 ns).
   - Fab A / Fab B physical, logical (EVPN-VXLAN RT5 / MAC-VRF, 1:3 oversubscription),
     collapsed spine (40 km+ deep-buffer), and hybrid cloud (IPsec/HTTPS S3 tiering) topologies.
   - NVMe-o-TCP state machine (TCP port 8009, ICReq/ICResp, CapsuleCmd 0x01, CapsuleResp,
     H2CData 0x03, C2HData 0x04, Read opcode 0x02, Write opcode 0x01, NSID, PRP1/PRP2 64-bit
     pointers vs SGL descriptors, MTU 9000 multi-PDU packing).
   - NVMe-o-RDMA / RoCEv2 state machine (~66% lower write latency, TCP port 8009 Discovery Log
     with RDMA_PRTYPE 0x04 RoCEv2 / 0x02 IB / 0x05 iWARP -> UDP port 4420 RDMA CM ->
     UDP port 4791 RoCEv2 BTH/RETH data plane, 1:1 SQ/CQ-to-QP mapping, controller-initiated
     RDMA_READ/RDMA_WRITE).
   - InfiniBand storage addressing and QoS (16-bit LID up to 48,000 nodes in LRH, optional GRH,
     BTH, ETH, ICRC/VCRC, 16 VLs, 64-byte CBFC credits in LLH).
2. Ultra Ethernet Consortium (UEC Specification v1.0, ADC Ch. 12):
   - Profiles (AI Base, AI Full, HPC), Libfabric API groups (fi_mr, fi_collective),
     and UEC terminology (FEP, FA, PDC, PDS, SES with JobID, PIDonFEP, Resource Index).
   - UET encapsulations: UDP port 49150 (dynamic source port entropy) vs native IP protocol 253
     (PDS Entropy field, 128-byte switch parse depth), plus optional UET CRC or TSS (AES-GCM ICV).
   - Packet delivery modes: ROD, RUD, RUDI, and UUD.
   - Congestion management and link layer: NSCC (window + RTT + ECN/ACK_CC), RCCC (24-bit ACK
     credits in 256-byte units), CBFC (32 VCs vs IB 16 VLs, CtlOS CP_Update, LLDP negotiation),
     DSCP packet trimming, Link Layer Reliability (LLR sequence in MAC preamble + replay buffer),
     and In-Network Collectives (INC sFEPs + INC Manager via gRPC vs user-space xCCL).
3. Scale-Up Fabrics (ADC Ch. 13):
   - Scale-up vs scale-out latency/bandwidth (NVLink 100-300 ns, 1.8 Tbps bidir on NVLink 5
     with 18 switches in NVL72; PCIe 5.0 500 ns-1 us, 32 GT/s, ~63-64 Gbps x16; PCIe 6.0 ~128 Gbps
     bidir x16; CXL 3.0 ~100 ns, 32 GT/s; up to 4 racks / 1,000 xPUs per scale-up pod).
   - OCP SUE-T / ESUN: 100G/200G SerDes lanes (e.g. 12 SUE instances x 12 lanes), AFH Gen 2
     compressed (6B) vs non-compressed (12B) headers, Reliability Header (RH with 10-bit xPU ID,
     16-bit NPSN/APSN, VC, Partition), LLR + CBFC, and on-die FIFO (10-bit xPU + 2-bit VC) vs
     ARM AXI 4.0 (5 channels: AR, AW, W on VC0; B, R on VC1).
   - UALink 1.0: 8 stations x 4 lanes x 200 Gbps = 32 lanes = 6.4 Tbps per xPU, sub-1 us RTT,
     < 4 m in-rack cabling, UPLI 4 channels (Req, OrigData, RD Res, WR Res), 57-bit ReqAddr,
     10-bit Src/Dst ACC-ID (up to 1,000 accelerators), 64B TL flits (16 x 4B sectors, upper/lower
     32B half-flits) packed 10-to-1 into 640B DL flits (+ 8B CRC, + 40B FEC = 680B wire unit)
     aligned to 1 PCS codeword of 544/514 10-bit symbols, 1-way/2-way vs 4-way FEC codeword
     interleaving, GVA -> NPA -> SPA MMU address handle translation, and hardware directory
     coherence (NVLink/Infinity Fabric snoops) vs software PGAS coherence (RMA_SYNC, NOTIFY,
     RMA_FENCE, RMA_COMPLETION, ATOMIC_ACK).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 1. Storage Network Models (ADC Chapter 9)
# ---------------------------------------------------------------------------

RDMA_PRTYPE_MAP: Dict[int, str] = {
    0x02: "InfiniBand",
    0x04: "RoCEv2",
    0x05: "iWARP",
}

NVME_TCP_CAPSULE_TYPES: Dict[int, str] = {
    0x01: "CapsuleCmd",
    0x02: "CapsuleResp",
    0x03: "H2CData",
    0x04: "C2HData",
}

NVME_IO_OPCODES: Dict[int, str] = {
    0x01: "Write",
    0x02: "Read",
}


@dataclass(frozen=True)
class NVMeSessionTrace:
    transport: str
    discovery_tcp_port: int
    cm_udp_port: int | None
    data_port: int
    rdma_prtype: int | None
    requires_lossless: bool
    sq_cq_to_qp_mapping: str
    ordered_stages: Tuple[str, ...]


def trace_nvme_of_session(
    transport: str,
    rdma_prtype: int = 0x04,
    in_capsule_write: bool = True,
) -> NVMeSessionTrace:
    """Return the protocol handshake and data-transfer trace for NVMe-o-TCP or NVMe-o-RDMA."""
    mode = transport.strip().lower()
    if mode in ("tcp", "nvme-o-tcp", "nvme/tcp"):
        data_phase = (
            "CapsuleCmd(0x01,InCapsuleData)->CapsuleResp(CQE)"
            if in_capsule_write
            else "CapsuleCmd(0x01,opcode=0x02)->C2HData(0x04)x4->CapsuleResp(CQE)"
        )
        return NVMeSessionTrace(
            transport="NVMe-o-TCP",
            discovery_tcp_port=8009,
            cm_udp_port=None,
            data_port=8009,
            rdma_prtype=None,
            requires_lossless=False,
            sq_cq_to_qp_mapping="1:1 Admin/IO SQ+CQ per TCP connection",
            ordered_stages=(
                "TCP_SYN_SYNACK_ACK(port=8009)",
                "TLS_Handshake(optional)",
                "NVMe_TCP_ICReq_PDU",
                "NVMe_TCP_ICResp_PDU",
                "NVMe_TCP_Connect_Req",
                "NVMe_TCP_Connect_Resp",
                data_phase,
                "H2CTermReq_C2HTermReq",
            ),
        )
    if mode in ("rdma", "rocev2", "nvme-o-rdma", "nvme/rdma"):
        if rdma_prtype not in RDMA_PRTYPE_MAP:
            raise ValueError(f"Unsupported RDMA_PRTYPE: {rdma_prtype}")
        return NVMeSessionTrace(
            transport=f"NVMe-o-RDMA ({RDMA_PRTYPE_MAP[rdma_prtype]})",
            discovery_tcp_port=8009,
            cm_udp_port=4420,
            data_port=4791,
            rdma_prtype=rdma_prtype,
            requires_lossless=True,
            sq_cq_to_qp_mapping="1:1 IO SQ+CQ per RDMA QPair (no multiplexing)",
            ordered_stages=(
                f"Discovery_GetLogPage_TCP(port=8009,RDMA_PRTYPE=0x{rdma_prtype:02x})",
                "RDMA_CM_Request_UDP(port=4420)",
                "RDMA_CM_Reply_UDP(port=4420)",
                "RDMA_CM_RTU_QP_Ready(RTS)",
                "NVMe_RDMA_Connect_Capsule(UDP=4791,RDMA_SEND)",
                "NVMe_RDMA_Connect_Resp(UDP=4791)",
                "NVMe_IO_Queue_Create_Req_Resp",
                "Controller_RDMA_READ_RDMA_WRITE(BTH+RETH,UDP=4791)",
            ),
        )
    raise ValueError(f"Unknown NVMe-oF transport: {transport}")


def calculate_nvme_tcp_pdu_packing(
    mtu_bytes: int = 9000,
    ip_header_bytes: int = 20,
    tcp_header_bytes: int = 20,
    pdu_common_plus_specific_hdr_bytes: int = 24,
    hdgst_bytes: int = 4,
    ddgst_bytes: int = 4,
    sqe_bytes: int = 64,
    in_capsule_data_bytes: int = 4096,
) -> Dict[str, int]:
    """Calculate how many NVMe-o-TCP PDUs fit inside a single jumbo-frame TCP segment."""
    mss_bytes = mtu_bytes - ip_header_bytes - tcp_header_bytes
    single_pdu_bytes = (
        pdu_common_plus_specific_hdr_bytes
        + hdgst_bytes
        + sqe_bytes
        + in_capsule_data_bytes
        + ddgst_bytes
    )
    pdus_per_segment = mss_bytes // single_pdu_bytes
    return {
        "mtu_bytes": mtu_bytes,
        "mss_bytes": mss_bytes,
        "single_pdu_bytes": single_pdu_bytes,
        "pdus_per_segment": pdus_per_segment,
        "remaining_mss_bytes": mss_bytes - (pdus_per_segment * single_pdu_bytes),
    }


def evaluate_infiniband_storage_fabric(
    num_nodes: int,
    active_vls: int = 8,
    credit_bytes_Requested: int = 4096,
) -> Dict[str, int | bool | str]:
    """Validate InfiniBand storage subnet addressing (16-bit LID, 48,000 nodes) and CBFC (16 VLs, 64B credits)."""
    lid_bits = 16
    max_theoretical_lids = 1 << lid_bits
    max_subnet_nodes = 48000
    max_vls = 16
    credit_unit_bytes = 64
    credits_needed = (credit_bytes_Requested + credit_unit_bytes - 1) // credit_unit_bytes
    return {
        "lid_bits": lid_bits,
        "max_theoretical_lids": max_theoretical_lids,
        "max_subnet_nodes": max_subnet_nodes,
        "fits_single_subnet": num_nodes <= max_subnet_nodes,
        "needs_grh": num_nodes > max_subnet_nodes,
        "max_vls": max_vls,
        "active_vls_valid": 1 <= active_vls <= max_vls,
        "credit_unit_bytes": credit_unit_bytes,
        "credits_needed": credits_needed,
        "frame_headers": "LRH+GRH(optional)+BTH+ETH+Payload(NVMe Capsule)+ICRC+VCRC",
    }


# ---------------------------------------------------------------------------
# 2. Ultra Ethernet Consortium (UEC Spec v1.0) Models (ADC Chapter 12)
# ---------------------------------------------------------------------------

UEC_DELIVERY_MODES: Dict[str, Dict[str, object]] = {
    "ROD": {
        "name": "Reliable Ordered Delivery",
        "reliable": True,
        "ordered": True,
        "idempotent_retry": False,
        "uses_psn_and_ack": True,
        "supports_tss_security": True,
        "profiles": ("AI Base", "AI Full", "HPC"),
        "use_case": "HPC, MPI, serialized control flow",
    },
    "RUD": {
        "name": "Reliable Unordered Delivery",
        "reliable": True,
        "ordered": False,
        "idempotent_retry": False,
        "uses_psn_and_ack": True,
        "supports_tss_security": True,
        "profiles": ("AI Base", "AI Full", "HPC"),
        "use_case": "AI model parallelism, bulk data ops",
    },
    "RUDI": {
        "name": "Reliable Unordered Delivery Idempotent",
        "reliable": True,
        "ordered": False,
        "idempotent_retry": True,
        "uses_psn_and_ack": True,
        "supports_tss_security": True,
        "profiles": ("AI Full", "HPC"),
        "use_case": "RMA writes, AI gradient updates",
    },
    "UUD": {
        "name": "Unreliable Unordered Delivery",
        "reliable": False,
        "ordered": False,
        "idempotent_retry": False,
        "uses_psn_and_ack": False,
        "supports_tss_security": False,
        "profiles": ("AI Full (optional)", "HPC (optional)"),
        "use_case": "Fire-and-forget telemetry, inference logs",
    },
}


@dataclass(frozen=True)
class UETPacketSpec:
    encapsulation: str
    ip_protocol: int
    udp_dst_port: int | None
    entropy_carrier: str
    security_or_crc: str
    pds_fields: Tuple[str, ...]
    ses_fields: Tuple[str, ...]
    switch_parse_budget_bytes: int


def build_uet_packet_spec(
    encapsulation: str = "udp",
    use_tss_security: bool = False,
    use_uet_crc: bool = True,
) -> UETPacketSpec:
    """Build a UET packet specification for UDP (port 49150) or native IP (protocol 253)."""
    if use_tss_security and use_uet_crc:
        raise ValueError("UEC v1.0 specifies either UET CRC or TSS security, not both simultaneously")

    mode = encapsulation.strip().lower()
    sec_mode = "TSS(AES-GCM+ICV)" if use_tss_security else ("UET_CRC" if use_uet_crc else "FCS_only")
    ses_fields = ("Opcode", "JobID", "PIDonFEP", "ResourceIndex", "BufferOffset", "MessageID")

    if mode == "udp":
        return UETPacketSpec(
            encapsulation="UET-over-UDP",
            ip_protocol=17,
            udp_dst_port=49150,
            entropy_carrier="UDP_Source_Port",
            security_or_crc=sec_mode,
            pds_fields=("Type", "NextHeader=SES", "Flags", "ClearPSNOffset", "PSN", "SPDCID", "DPDCID"),
            ses_fields=ses_fields,
            switch_parse_budget_bytes=128,
        )
    if mode in ("ip", "raw-ip", "native-ip"):
        return UETPacketSpec(
            encapsulation="UET-over-IP",
            ip_protocol=253,
            udp_dst_port=None,
            entropy_carrier="PDS_Entropy_Field",
            security_or_crc=sec_mode,
            pds_fields=("Entropy", "Type", "NextHeader=SES", "Flags", "ClearPSNOffset", "PSN", "SPDCID", "DPDCID"),
            ses_fields=ses_fields,
            switch_parse_budget_bytes=128,
        )
    raise ValueError(f"Unsupported UET encapsulation: {encapsulation}")


def calculate_uec_rccc_and_cbfc(
    requested_payload_bytes: int,
    cbfc_active_vcs: int = 32,
) -> Dict[str, int | bool | str]:
    """Compute UEC RCCC 256-byte receiver credits (24-bit ACK field) and link-level CBFC 32-VC parameters."""
    rccc_credit_unit_bytes = 256
    rccc_ack_bits = 24
    rccc_credits_granted = (requested_payload_bytes + rccc_credit_unit_bytes - 1) // rccc_credit_unit_bytes
    max_rccc_credits = (1 << rccc_ack_bits) - 1
    max_rccc_window_bytes = max_rccc_credits * rccc_credit_unit_bytes
    uec_max_vcs = 32
    ib_max_vls = 16
    return {
        "rccc_credit_unit_bytes": rccc_credit_unit_bytes,
        "rccc_ack_bits": rccc_ack_bits,
        "rccc_credits_granted": rccc_credits_granted,
        "rccc_fits_24bit_ack": rccc_credits_granted <= max_rccc_credits,
        "max_rccc_window_bytes": max_rccc_window_bytes,
        "uec_max_vcs": uec_max_vcs,
        "ib_max_vls": ib_max_vls,
        "vc_expansion_vs_ib": uec_max_vcs // ib_max_vls,
        "cbfc_active_vcs_valid": 1 <= cbfc_active_vcs <= uec_max_vcs,
        "cbfc_signaling": "PCS_CtlOS_CP_Update + LLDP_capability_negotiation",
    }


def compare_rocev2_go_back_n_vs_uet_selective(
    window_packets: int,
    dropped_packet_index: int,
) -> Dict[str, int | float]:
    """Compare RoCEv2 Go-Back-N retransmissions against UET (RUD/RUDI + packet trimming) selective retry."""
    if not (1 <= dropped_packet_index <= window_packets):
        raise ValueError("dropped_packet_index must lie inside [1, window_packets]")
    rocev2_retransmitted = window_packets - dropped_packet_index + 1
    uet_retransmitted = 1
    return {
        "window_packets": window_packets,
        "dropped_packet_index": dropped_packet_index,
        "rocev2_go_back_n_retransmissions": rocev2_retransmitted,
        "uet_selective_retransmissions": uet_retransmitted,
        "bandwidth_saved_packets": rocev2_retransmitted - uet_retransmitted,
        "retransmission_reduction_factor": round(rocev2_retransmitted / uet_retransmitted, 2),
    }


# ---------------------------------------------------------------------------
# 3. Scale-Up Fabric Models: SUE-T / ESUN and UALink 1.0 (ADC Chapter 13)
# ---------------------------------------------------------------------------


def evaluate_suet_scaleup_fabric(
    sue_instances_per_xpu: int = 12,
    lanes_per_instance: int = 12,
    lane_rate_gbps: int = 200,
    single_hop: bool = True,
    on_die_interface: str = "AXI4",
    payload_bytes: int = 256,
) -> Dict[str, object]:
    """Evaluate OCP SUE-T / ESUN scale-up headers (AFH Gen 2 6B/12B + RH), bandwidth, and AXI4/FIFO mapping."""
    afh_bytes = 6 if single_hop else 12
    ethertype_bytes = 2
    rh_bytes = 8  # VER/OP/RSV/10-bit xPU ID/16-bit NPSN + VC/RSV/Partition/16-bit APSN
    rcrc_plus_fcs_bytes = 8
    total_frame_bytes = afh_bytes + ethertype_bytes + rh_bytes + payload_bytes + rcrc_plus_fcs_bytes
    xpu_id_bits = 10
    max_xpus_addressed = 1 << xpu_id_bits

    iface = on_die_interface.strip().upper()
    if iface in ("AXI", "AXI4", "AXI 4.0"):
        channels = {
            "VC0_requests": ("AR (Read Address)", "AW (Write Address)", "W (Write Data)"),
            "VC1_responses": ("B (Write Response)", "R (Read Data)"),
            "channel_count": 5,
        }
    elif iface == "FIFO":
        channels = {
            "VC_stream": ("Raw PDU stream with 10-bit xPU ID + 2-bit VC ID",),
            "channel_count": 1,
        }
    else:
        raise ValueError(f"Unsupported SUE-T on-die interface: {on_die_interface}")

    per_instance_tbps = (lanes_per_instance * lane_rate_gbps) / 1000.0
    total_xpu_tbps = (sue_instances_per_xpu * lanes_per_instance * lane_rate_gbps) / 1000.0

    return {
        "afh_gen2_bytes": afh_bytes,
        "afh_mode": "compressed-6B" if single_hop else "non-compressed-12B",
        "rh_bytes": rh_bytes,
        "xpu_id_bits": xpu_id_bits,
        "max_xpus_addressed": max_xpus_addressed,
        "sequence_number_bits": 16,  # 16-bit NPSN and 16-bit APSN
        "max_sue_pdu_bytes": 4096,
        "base_flit_frame_bytes": 256,
        "payload_efficiency_pct": round((payload_bytes / total_frame_bytes) * 100.0, 2),
        "per_instance_tbps": round(per_instance_tbps, 2),
        "total_xpu_tbps": round(total_xpu_tbps, 2),
        "on_die_channels": channels,
        "link_reliability": "LLR + CBFC + RH(NPSN/APSN)",
    }


def evaluate_ualink_scaleup_fabric(
    stations_per_xpu: int = 8,
    lanes_per_station: int = 4,
    lane_rate_gbps: int = 200,
    interleave_way: int = 2,
) -> Dict[str, object]:
    """Evaluate UALink 1.0 station/lane bandwidth, 64B TL -> 640B DL flit packing, and address translation."""
    if interleave_way not in (1, 2, 4):
        raise ValueError("interleave_way must be 1, 2, or 4")

    total_lanes = stations_per_xpu * lanes_per_station
    aggregate_gbps = total_lanes * lane_rate_gbps
    aggregate_tbps = aggregate_gbps / 1000.0

    sector_bytes = 4
    sectors_per_tl_flit = 16
    tl_flit_bytes = sector_bytes * sectors_per_tl_flit  # 64B
    tl_half_flit_bytes = tl_flit_bytes // 2  # 32B
    tl_flits_per_dl_flit = 10
    dl_flit_payload_bytes = tl_flit_bytes * tl_flits_per_dl_flit  # 640B
    dl_crc_bytes = 8
    fec_overhead_bytes = 40
    wire_transmission_unit_bytes = dl_flit_payload_bytes + fec_overhead_bytes  # 680B
    pcs_codeword_data_symbols = 514
    pcs_codeword_total_symbols = 544
    pcs_symbol_bits = 10

    acc_id_bits = 10
    max_pod_accelerators = 1000  # Up to 1,000 accelerators encoded in 10-bit ACC-ID (max 1024 values)
    req_addr_bits = 57

    return {
        "stations_per_xpu": stations_per_xpu,
        "lanes_per_station": lanes_per_station,
        "total_lanes_per_xpu": total_lanes,
        "lane_rate_gbps": lane_rate_gbps,
        "aggregate_gbps": aggregate_gbps,
        "aggregate_tbps": round(aggregate_tbps, 2),
        "tl_flit_bytes": tl_flit_bytes,
        "tl_half_flit_bytes": tl_half_flit_bytes,
        "sectors_per_tl_flit": sectors_per_tl_flit,
        "tl_flits_per_dl_flit": tl_flits_per_dl_flit,
        "dl_flit_bytes": dl_flit_payload_bytes,
        "dl_crc_bytes": dl_crc_bytes,
        "fec_overhead_bytes": fec_overhead_bytes,
        "wire_unit_bytes": wire_transmission_unit_bytes,
        "pcs_codeword": f"RS({pcs_codeword_total_symbols},{pcs_codeword_data_symbols})x{pcs_symbol_bits}b",
        "dl_flits_per_pcs_codeword": 1,
        "interleave_way": interleave_way,
        "interleave_speedup_vs_4way_eth": round(4 / interleave_way, 2),
        "upli_channels": ("Req", "OrigData", "RD Res", "WR Res"),
        "address_translation": "GVA -> (Source MMU + Address Handle) -> NPA -> (ULS Switch via 10-bit ACC-ID) -> (Dest Link MMU) -> SPA",
        "acc_id_bits": acc_id_bits,
        "max_pod_accelerators": max_pod_accelerators,
        "req_addr_bits": req_addr_bits,
        "coherence_model": "Software PGAS (RMA_SYNC, NOTIFY, RMA_FENCE, RMA_COMPLETION, ATOMIC_ACK)",
    }


def compare_scaleup_technologies() -> Dict[str, Dict[str, object]]:
    """Return key comparison metrics across PCIe 5.0/6.0, CXL 3.0, NVLink 5 (NVL72), SUE-T, and UALink 1.0."""
    return {
        "PCIe_5_x16": {
            "transfer_rate_gt_s": 32,
            "unidirectional_gbps": 64,
            "latency_ns_range": (500, 1000),
            "coherence": "None (point-to-point bus)",
        },
        "PCIe_6_x16": {
            "transfer_rate_gt_s": 32,
            "bidirectional_gbps": 128,
            "latency_ns_range": (500, 1000),
            "coherence": "None",
        },
        "CXL_3": {
            "transfer_rate_gt_s": 32,
            "latency_ns_range": (100, 300),
            "coherence": "Hardware cache-coherent shared memory",
        },
        "NVLink_5_NVL72": {
            "switches_per_rack": 18,
            "gpus_per_rack": 72,
            "bidirectional_tbps_per_gpu": 1.8,
            "latency_ns_range": (100, 300),
            "coherence": "Hardware directory/snoop coherence via NVSwitch",
        },
        "SUE_T_ESUN": {
            "lane_rate_gbps": 200,
            "switch_latency_ns": 250,
            "end_to_end_latency_ns": 1000,
            "coherence": "Software-managed one-sided PGAS (put/get/atomic)",
        },
        "UALink_1_0": {
            "lane_rate_gbps": 200,
            "stations_x_lanes": "8x4 (32 lanes)",
            "bandwidth_tbps_per_xpu": 6.4,
            "switch_latency_ns_max": 300,
            "max_accelerators": 1000,
            "coherence": "Software-managed PGAS (load/store/atomic, fence/notify)",
        },
    }
