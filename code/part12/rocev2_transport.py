#!/usr/bin/env python3
"""Chapter 12.3: RoCEv2 Transport and Congestion Management (stdlib only).

Covers:
1. RoCEv1 (EtherType 0x8915, IB GRH 40B) vs RoCEv2 (UDP port 4791, IPv4 20B / IPv6 40B)
   header overhead and payload efficiency across 1500B, 4200B, and 9000B MTUs.
2. Per-port GID table resolution: semantic selection of RoCEv2 (v2) IPv4-mapped GIDs
   (0000:0000:0000:0000:0000:ffff:...) and VLAN/netdev matching vs link-local RoCEv1 (fe80::).
3. End-to-end QoS trust boundary: DSCP 26 (AF31, or DSCP 24 CS3) -> 802.1p PCP/CoS 3 ->
   lossless Traffic Class 3 queue mapping and ECN 2-bit IP ToS encoding (00, 01, 10, 11)
   with CNP IB BTH opcode 129 (0x81).
4. Six Clos fabric congestion points from ADC Ch 7 (local leaf south-facing, leaf-to-spine,
   spine-to-leaf, leaf-to-server egress, spine-to-super-spine, super-spine-to-spine) and
   progressive DCQCN buffer threshold ordering (XON < ECN < XOFF) plus PFC frame anatomy
   (EtherType 0x8808, opcode 0x0101, multicast MAC 01:80:c2:00:00:01, Class Enable Vector
   0x0008 for CoS 3, pause quanta 0..65535) and PFC Watchdog (Detection, Mitigation, Restoration).
5. Go-Back-N vs Selective Repeat RDMA retransmission amplifier math and straggler JCT impact.
6. Next-generation congestion signaling: IEEE 802.1Qdw Source Flow Control (SFC) fast switch-to-source
   signaling vs ECN/CNP RTT delay, and IETF draft-ravi-ippm-csig-01 Congestion Signaling (CSIG)
   L2.5 header telemetry (min ABW/C, min ABW, max PD, and 4 locator metadata fields).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. RoCEv1 vs RoCEv2 Encapsulation & Header Efficiency
# ---------------------------------------------------------------------------
ETH_L2_OVERHEAD_BYTES = 18       # 14B Ethernet II header + 4B FCS (or +4B with 802.1Q VLAN = 22B)
ETH_VLAN_TAG_BYTES = 4
IB_GRH_BYTES = 40                # RoCEv1 Global Routing Header (IPv6-formatted GID addressing)
IPV4_HEADER_BYTES = 20           # RoCEv2 IPv4 outer header
IPV6_HEADER_BYTES = 40           # RoCEv2 IPv6 outer header
UDP_HEADER_BYTES = 8             # RoCEv2 UDP outer header (dst port 4791, src port = QP hash)
IB_BTH_BYTES = 12                # InfiniBand Base Transport Header (Opcode, Dest QP, PSN)
IB_RETH_BYTES = 16               # RDMA Extended Transport Header (Virtual Addr 8B, RKey 4B, DMA Len 4B)
IB_AETH_BYTES = 4                # ACK Extended Transport Header (Syndrome 1B + MSN 3B)
IB_ICRC_BYTES = 4                # Invariant CRC (32-bit end-to-end integrity)

ROCEV1_ETHERTYPE = 0x8915
ROCEV2_UDP_DST_PORT = 4791
PFC_ETHERTYPE = 0x8808
PFC_OPCODE = 0x0101
PFC_DEST_MAC = "01:80:c2:00:00:01"
PFC_CLASS3_ENABLE_VECTOR = 0x0008
PFC_MAX_PAUSE_QUANTA = 65535
CNP_BTH_OPCODE = 129             # 0x81 (10000001 binary)
RC_RDMA_READ_REQ_OPCODE = 12
RC_RDMA_READ_RESP_MID_OPCODE = 14
RC_RDMA_ACK_OPCODE = 17
DEFAULT_ROCE_PKEY = 65535        # 0xffff default partition key


@dataclass(frozen=True)
class EncapsulationProfile:
    variant: str                 # "RoCEv1", "RoCEv2-IPv4", "RoCEv2-IPv6"
    ethertype_or_port: int
    l2_bytes: int
    l3_bytes: int
    l4_bytes: int
    bth_bytes: int
    reth_bytes: int
    icrc_bytes: int
    payload_bytes: int

    @property
    def total_header_and_trailer_bytes(self) -> int:
        return (
            self.l2_bytes
            + self.l3_bytes
            + self.l4_bytes
            + self.bth_bytes
            + self.reth_bytes
            + self.icrc_bytes
        )

    @property
    def wire_frame_bytes(self) -> int:
        return self.total_header_and_trailer_bytes + self.payload_bytes

    @property
    def payload_efficiency_pct(self) -> float:
        return round((self.payload_bytes / self.wire_frame_bytes) * 100.0, 2)


def compare_roce_encapsulation(
    payload_bytes: int = 4096,
    include_vlan: bool = False,
    include_reth: bool = False,
) -> Dict[str, EncapsulationProfile]:
    """Compare wire overhead of RoCEv1 (0x8915) vs RoCEv2 IPv4/IPv6 (UDP 4791)."""
    l2 = ETH_L2_OVERHEAD_BYTES + (ETH_VLAN_TAG_BYTES if include_vlan else 0)
    reth = IB_RETH_BYTES if include_reth else 0
    return {
        "RoCEv1": EncapsulationProfile(
            variant="RoCEv1",
            ethertype_or_port=ROCEV1_ETHERTYPE,
            l2_bytes=l2,
            l3_bytes=IB_GRH_BYTES,
            l4_bytes=0,
            bth_bytes=IB_BTH_BYTES,
            reth_bytes=reth,
            icrc_bytes=IB_ICRC_BYTES,
            payload_bytes=payload_bytes,
        ),
        "RoCEv2-IPv4": EncapsulationProfile(
            variant="RoCEv2-IPv4",
            ethertype_or_port=ROCEV2_UDP_DST_PORT,
            l2_bytes=l2,
            l3_bytes=IPV4_HEADER_BYTES,
            l4_bytes=UDP_HEADER_BYTES,
            bth_bytes=IB_BTH_BYTES,
            reth_bytes=reth,
            icrc_bytes=IB_ICRC_BYTES,
            payload_bytes=payload_bytes,
        ),
        "RoCEv2-IPv6": EncapsulationProfile(
            variant="RoCEv2-IPv6",
            ethertype_or_port=ROCEV2_UDP_DST_PORT,
            l2_bytes=l2,
            l3_bytes=IPV6_HEADER_BYTES,
            l4_bytes=UDP_HEADER_BYTES,
            bth_bytes=IB_BTH_BYTES,
            reth_bytes=reth,
            icrc_bytes=IB_ICRC_BYTES,
            payload_bytes=payload_bytes,
        ),
    }


# ---------------------------------------------------------------------------
# 2. GID Table Semantic Selection (v1 vs v2, IPv4-mapped GID, Netdev/VLAN)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GidEntry:
    rdma_dev: str
    port: int
    index: int
    gid: str
    ipv4: str
    version: str                 # "v1" or "v2"
    netdev: str


def ipv4_to_rocev2_gid(ipv4: str) -> str:
    """Convert dotted-quad IPv4 (e.g. '10.20.4.15') to IPv4-mapped IPv6 GID."""
    octets = [int(x) for x in ipv4.split(".")]
    if len(octets) != 4 or any(o < 0 or o > 255 for o in octets):
        raise ValueError(f"Invalid IPv4 address: {ipv4}")
    hi = (octets[0] << 8) | octets[1]
    lo = (octets[2] << 8) | octets[3]
    return f"0000:0000:0000:0000:0000:ffff:{hi:04x}:{lo:04x}"


def select_semantic_gid(
    entries: List[GidEntry],
    expected_rdma_dev: str,
    expected_port: int,
    expected_netdev: str,
    expected_ipv4: str,
    expected_version: str = "v2",
) -> Optional[GidEntry]:
    """Select a GID entry by semantic attributes rather than hard-coding an index."""
    expected_gid = ipv4_to_rocev2_gid(expected_ipv4)
    for entry in entries:
        if (
            entry.rdma_dev == expected_rdma_dev
            and entry.port == expected_port
            and entry.netdev == expected_netdev
            and entry.ipv4 == expected_ipv4
            and entry.version == expected_version
            and entry.gid == expected_gid
        ):
            return entry
    return None


# ---------------------------------------------------------------------------
# 3. QoS Trust Mapping (DSCP 26 / AF31 -> CoS 3) & ECN 2-Bit Codepoints
# ---------------------------------------------------------------------------
ECN_CODEPOINTS: Dict[str, str] = {
    "00": "Non-ECT (Not ECN-Capable Transport; dropped on congestion)",
    "01": "ECT(1) (ECN-Capable Transport; also carried by RoCEv2 CNPs)",
    "10": "ECT(0) (ECN-Capable Transport set by sender toward receiver)",
    "11": "CE (Congestion Experienced; marked by congested switch when queue > ECN threshold)",
}

DSCP_AF31 = 26                   # 011010 binary (Class 3, low drop precedence)
DSCP_CS3 = 24                    # 011000 binary (Class Selector 3)
ROCE_LOSSLESS_COS = 3            # IEEE 802.1p Priority Code Point / Traffic Class 3


def build_ip_tos_byte(dscp: int, ecn_bits: str) -> int:
    """Combine 6-bit DSCP (0..63) and 2-bit ECN ('00','01','10','11') into an 8-bit IP ToS/Traffic Class byte."""
    if not (0 <= dscp <= 63) or ecn_bits not in ECN_CODEPOINTS:
        raise ValueError("Invalid DSCP or ECN bits")
    return (dscp << 2) | int(ecn_bits, 2)


def decode_ip_tos_byte(tos_byte: int) -> Tuple[int, str]:
    """Extract (dscp, ecn_bits) from an 8-bit IP ToS/Traffic Class byte."""
    dscp = (tos_byte >> 2) & 0x3F
    ecn_bits = f"{tos_byte & 0x03:02b}"
    return dscp, ecn_bits


def validate_qos_path(
    host_dscp: int,
    vlan_pcp: int,
    switch_trust_mode: str,
    switch_dscp_to_tc_map: Dict[int, int],
    pfc_enabled_priorities: List[int],
    ecn_enabled_tcs: List[int],
) -> Dict[str, object]:
    """Validate end-to-end QoS trust, traffic class mapping, PFC, and ECN enablement."""
    if switch_trust_mode == "dscp":
        mapped_tc = switch_dscp_to_tc_map.get(host_dscp, 0)
    elif switch_trust_mode == "pcp":
        mapped_tc = vlan_pcp
    else:
        mapped_tc = 0

    is_lossless_tc = mapped_tc in pfc_enabled_priorities
    is_ecn_tc = mapped_tc in ecn_enabled_tcs
    return {
        "mapped_tc": mapped_tc,
        "is_lossless_tc": is_lossless_tc,
        "is_ecn_tc": is_ecn_tc,
        "healthy_roce_qos": (
            mapped_tc == ROCE_LOSSLESS_COS and is_lossless_tc and is_ecn_tc
        ),
    }


# ---------------------------------------------------------------------------
# 4. Clos Congestion Points (ADC Ch 7), DCQCN Thresholds & PFC Watchdog
# ---------------------------------------------------------------------------
SIX_CLOS_CONGESTION_POINTS: List[Dict[str, str]] = [
    {
        "id": "1. Local leaf link congestion",
        "figure": "Figure 7-1 (Incast congestion toward south-facing links)",
        "mechanism": "Multiple servers on LeafA send line-rate traffic to a locally attached storage or compute node on the same south-facing link without spine load balancing.",
    },
    {
        "id": "2. Leaf-to-spine link congestion",
        "figure": "Figure 7-2 (Incast congestion at an ingress leaf)",
        "mechanism": "Multiple servers on LeafA send line-rate flows that ECMP hash onto the same LeafA-to-SpineA uplink while SpineB paths sit underutilized.",
    },
    {
        "id": "3. Spine-to-leaf link congestion",
        "figure": "Figure 7-3 (Incast congestion at a transit spine)",
        "mechanism": "Flows from LeafA and LeafB reach SpineA uncongested but converge onto the single SpineA-to-LeafD downlink.",
    },
    {
        "id": "4. Leaf-to-server link congestion",
        "figure": "Figure 7-4 (Incast congestion at an egress leaf)",
        "mechanism": "Flows from LeafA and LeafB traverse SpineA and SpineB uncongested but aggregate at egress LeafD, exceeding the bandwidth of the single server link.",
    },
    {
        "id": "5. Spine-to-super spine link congestion",
        "figure": "Figure 7-5 (Incast congestion at the spine-to-super spine link)",
        "mechanism": "In a 5-stage Clos (LeafA..LeafH, SpineA..SpineD, SuperSpineA..SuperSpineB), flows from LeafA and LeafB collide on the SpineA-to-SuperSpineA uplink.",
    },
    {
        "id": "6. Super spine-to-spine link congestion",
        "figure": "Figure 7-6 (Incast congestion at the super spine-to-spine link)",
        "mechanism": "Traffic reaches SuperSpineA across multiple uplinks but converges onto a single SuperSpineA-to-SpineC downlink toward the destination pod.",
    },
]


@dataclass(frozen=True)
class DcqcnBufferProfile:
    xon_threshold_kb: int
    ecn_min_threshold_kb: int
    ecn_max_threshold_kb: int
    xoff_threshold_kb: int
    total_buffer_kb: int

    def is_valid_ordering(self) -> bool:
        """DCQCN requires XON < ECN_min <= ECN_max < XOFF < total_buffer."""
        return (
            0
            < self.xon_threshold_kb
            < self.ecn_min_threshold_kb
            <= self.ecn_max_threshold_kb
            < self.xoff_threshold_kb
            < self.total_buffer_kb
        )

    def evaluate_queue_state(self, occupancy_kb: int) -> Dict[str, object]:
        if occupancy_kb >= self.xoff_threshold_kb:
            return {
                "zone": "PFC_XOFF_PAUSE",
                "ecn_mark": True,
                "pfc_xoff": True,
                "pfc_xon": False,
                "pfc_pause_quanta": PFC_MAX_PAUSE_QUANTA,
            }
        if occupancy_kb >= self.ecn_min_threshold_kb:
            return {
                "zone": "ECN_MARKING_DCQCN",
                "ecn_mark": True,
                "pfc_xoff": False,
                "pfc_xon": False,
                "pfc_pause_quanta": 0,
            }
        if occupancy_kb <= self.xon_threshold_kb:
            return {
                "zone": "NORMAL_XON_RESUME",
                "ecn_mark": False,
                "pfc_xoff": False,
                "pfc_xon": True,
                "pfc_pause_quanta": 0,
            }
        return {
            "zone": "HYSTERESIS_BAND",
            "ecn_mark": False,
            "pfc_xoff": False,
            "pfc_xon": False,
            "pfc_pause_quanta": 0,
        }


PFC_WATCHDOG_BLOCKS: Tuple[str, str, str] = (
    "Detection",
    "Mitigation",
    "Restoration",
)


def simulate_pfc_watchdog(
    paused_duration_ms: float,
    watchdog_threshold_ms: float = 50.0,
    mitigation_mode: str = "drop",
    post_storm_pause_rate: int = 0,
) -> Dict[str, object]:
    """Model the 3 PFC Watchdog functional blocks from ADC Ch 7 (Fig 7-15) and VL6 Ch 1."""
    storm_detected = paused_duration_ms >= watchdog_threshold_ms
    if not storm_detected:
        return {
            "blocks": PFC_WATCHDOG_BLOCKS,
            "storm_detected": False,
            "action": "none",
            "upstream_pause_propagated": True,
            "restored_lossless": True,
        }
    if mitigation_mode == "drop":
        action = (
            "Discard queued packets, discard new packets for output queue, "
            "and discard incoming priority-group packets/pause frames so SpineA does not pause LeafA/LeafB"
        )
    else:
        action = "Ignore received PFC pause frames and forward queued/new packets"

    return {
        "blocks": PFC_WATCHDOG_BLOCKS,
        "storm_detected": True,
        "action": action,
        "upstream_pause_propagated": False,
        "restored_lossless": post_storm_pause_rate == 0,
    }


# ---------------------------------------------------------------------------
# 5. Go-Back-N vs Selective Repeat Retransmission & Tail-Latency JCT Math
# ---------------------------------------------------------------------------
def calculate_retransmission_amplification(
    bandwidth_gbps: float,
    rtt_us: float,
    mtu_bytes: int = 4096,
    loss_events: int = 1,
) -> Dict[str, float]:
    """Compare Go-Back-N full-window retransmission vs Selective Repeat single-packet recovery."""
    bytes_in_flight = (bandwidth_gbps * 1e9 / 8.0) * (rtt_us * 1e-6)
    packets_in_flight = max(1, int(round(bytes_in_flight / mtu_bytes)))
    gbn_retransmitted_packets = packets_in_flight * loss_events
    sr_retransmitted_packets = 1 * loss_events
    return {
        "bdp_bytes": round(bytes_in_flight, 1),
        "packets_in_flight": packets_in_flight,
        "gbn_retransmitted_packets": gbn_retransmitted_packets,
        "sr_retransmitted_packets": sr_retransmitted_packets,
        "amplification_factor": round(gbn_retransmitted_packets / sr_retransmitted_packets, 2),
    }


def calculate_jct_tail_latency(
    num_tasks: int = 10,
    normal_task_ms: float = 1.0,
    straggler_task_ms: float = 1000.0,
) -> Dict[str, float]:
    """Reproduce ADC Ch 1 Fig 1-5 (serial) and Fig 1-6 (parallel) tail-latency JCT math."""
    serial_jct_s = (straggler_task_ms + num_tasks * normal_task_ms) / 1000.0
    parallel_jct_s = max(normal_task_ms, straggler_task_ms) / 1000.0
    parallel_wait_ms = straggler_task_ms - normal_task_ms
    return {
        "serial_jct_s": round(serial_jct_s, 3),
        "parallel_jct_s": round(parallel_jct_s, 3),
        "parallel_wait_ms": round(parallel_wait_ms, 1),
    }


# ---------------------------------------------------------------------------
# 6. Next-Gen Congestion Control: Source Flow Control (SFC 802.1Qdw) & CSIG
# ---------------------------------------------------------------------------
CSIG_SIGNAL_TYPES: Tuple[str, str, str] = (
    "min(ABW/C)",
    "min(ABW)",
    "max(PD)",
)

CSIG_LOCATOR_METADATA_FIELDS: Tuple[str, str, str, str] = (
    "Capacity of the bottlenecks",
    "Stage of the bottlenecks",
    "Device ID",
    "Link identification (uplink or downlink)",
)


def compare_congestion_signaling_latency(
    sender_to_switch_us: float = 2.0,
    switch_to_receiver_us: float = 6.0,
    receiver_to_sender_us: float = 8.0,
) -> Dict[str, object]:
    """Compare feedback loop latency of ECN/CNP (end-to-end), PFC (hop-by-hop class pause),
    SFC (802.1Qdw direct switch-to-source flow signal), and CSIG (draft-ravi-ippm-csig-01)."""
    ecn_cnp_Notification_us = switch_to_receiver_us + receiver_to_sender_us
    sfc_direct_Notification_us = sender_to_switch_us
    return {
        "ecn_cnp_feedback_us": round(ecn_cnp_Notification_us, 2),
        "sfc_direct_feedback_us": round(sfc_direct_Notification_us, 2),
        "sfc_speedup_factor": round(ecn_cnp_Notification_us / sfc_direct_Notification_us, 2),
        "sfc_standard": "IEEE 802.1Qdw",
        "sfc_granularity": "flow-based (trimmed payload, reversed IP src/dst)",
        "pfc_granularity": "class-based (entire CoS queue, risks HoL blocking)",
        "csig_draft": "draft-ravi-ippm-csig-01",
        "csig_header_layer": "Layer 2.5 (between Layer 2 Ethernet and Layer 3 IP headers)",
        "csig_signal_types": CSIG_SIGNAL_TYPES,
        "csig_locator_fields": CSIG_LOCATOR_METADATA_FIELDS,
    }
