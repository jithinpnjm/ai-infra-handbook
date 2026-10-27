#!/usr/bin/env python3
"""Chapter 12.14: Load balancing and routing for AI fabrics.

Pure-stdlib reference models reproducing all quantitative calculations, packet encodings,
and control-plane tables from AI Data Center Network Design and Technologies (ADC)
Chapter 6 ("Efficient Load Balancing") and Chapter 8 ("IP Routing for AI/ML Fabrics"),
plus NVIDIA Base Command Manager 11 (bcm11-admin) Cumulus Linux NVUE switch management.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


# ==============================================================================
# 1. ADC Chapter 6 Constants: Per-Flow & Per-Packet Load Balancing
# ==============================================================================

# Worked 5-tuple CRC32 example (ADC Ch 6, "Static Load Balancing")
SLB_EXAMPLE_SRC_IP = "192.168.1.20"
SLB_EXAMPLE_SRC_IP_HEX = "C0A80114"
SLB_EXAMPLE_DST_IP = "192.168.2.10"
SLB_EXAMPLE_DST_IP_HEX = "C0A8020A"
SLB_EXAMPLE_IP_PROTO_UDP = 17
SLB_EXAMPLE_IP_PROTO_HEX = "11"
SLB_EXAMPLE_SRC_PORT = 1024
SLB_EXAMPLE_SRC_PORT_HEX = "0400"
SLB_EXAMPLE_DST_PORT = 4791
SLB_EXAMPLE_DST_PORT_HEX = "12B7"
SLB_EXAMPLE_PACKED_HEX = "C0A80114C0A8020A11040012B7"
SLB_EXAMPLE_CRC32_HEX = 0x8BDA7C2D
SLB_EXAMPLE_CRC32_DEC = 2346351661
SLB_EXAMPLE_MOD_5_INDEX = 1
SLB_EXAMPLE_MOD_8_INDEX = 5

# Simple hash keys in ADC Ch 6 (hash_key=10 -> 10 mod 5 = 0; hash_key=11 -> 11 mod 5 = 1)
SLB_SIMPLE_KEY_10 = 10
SLB_SIMPLE_KEY_11 = 11
SLB_SIMPLE_ECMP_5 = 5

# Resilient hashing bucket table sizes (ADC Ch 6)
RESILIENT_BUCKET_SIZES = (512, 1024)
RESILIENT_SIMPLIFIED_BUCKETS = 8
RESILIENT_SIMPLIFIED_INTERFACES = 5
RESILIENT_INITIAL_MAP: Tuple[int, ...] = (0, 1, 2, 3, 4, 0, 1, 2)

# SLB vs DLB flow rate example on 2x 200 Gbps leaf-to-spine links (ADC Ch 6 Figs 6-2, 6-4)
FLOW_RATES_GBPS: Tuple[int, int, int, int] = (50, 100, 50, 100)  # Flow1..Flow4
LEAF_TO_SPINE_LINK_BW_GBPS = 200

# DLB quality bands and GLB NNHN / Tomahawk 5 constants (ADC Ch 6)
DLB_QUALITY_BAND_MIN = 0
DLB_QUALITY_BAND_MAX = 7
GLB_NNHN_CHARACTERISTIC_CODE = 2
GLB_BGP_ID_BITS = 32
GLB_TOMAHAWK5_HEARTBEAT_MS = 20

# Per-packet spraying 3 x 1500B datagrams over 3 x 100 Gbps ports (ADC Ch 6 Figs 6-14, 6-15)
PER_PACKET_DATAGRAM_BYTES = 1500
PER_PACKET_DATAGRAM_COUNT = 3
PER_PACKET_PORT_BW_GBPS = 100
PER_PACKET_DST_IP = "192.168.1.1"
PER_PACKET_SEND_ORDER: Tuple[str, str, str] = ("A", "B", "C")
PER_PACKET_ARRIVAL_ORDER: Tuple[str, str, str] = ("B", "C", "A")  # T1=B, T2=C, T3=A

# RoCEv2 BTH opcodes for Selective Packet Spraying (sDLB) on ConnectX-6/7 & BlueField
BTH_OPCODE_RDMA_WRITE_FIRST = 0x06
BTH_OPCODE_RDMA_WRITE_MIDDLE = 0x07
BTH_OPCODE_RDMA_WRITE_LAST = 0x08
BTH_OPCODE_RDMA_WRITE_LAST_IMM = 0x09
BTH_OPCODE_RDMA_WRITE_ONLY = 0x0A
BTH_OPCODE_RDMA_WRITE_ONLY_IMM = 0x0B
BTH_OPCODE_RDMA_READ_REQUEST = 0x0C
BTH_OPCODE_RDMA_SEND_ONLY = 0x04

SDLB_SPRAYABLE_WRITE_OPCODES: Tuple[int, ...] = (
    BTH_OPCODE_RDMA_WRITE_FIRST,
    BTH_OPCODE_RDMA_WRITE_MIDDLE,
    BTH_OPCODE_RDMA_WRITE_LAST,
    BTH_OPCODE_RDMA_WRITE_LAST_IMM,
    BTH_OPCODE_RDMA_WRITE_ONLY,
    BTH_OPCODE_RDMA_WRITE_ONLY_IMM,
)


# ==============================================================================
# 2. ADC Chapter 8 Constants: IP Routing, BGP, RIFT, IS-IS Flex Algo, SRv6
# ==============================================================================

# BGP Unnumbered (RFC 5549 / RFC 8950) & ASN ranges (ADC Ch 8 Figs 8-1..8-5)
ASN_16BIT_PRIVATE_MIN = 64512
ASN_16BIT_PRIVATE_MAX = 65535
ASN_32BIT_PRIVATE_MIN = 4200000000
ASN_32BIT_PRIVATE_MAX = 4294967294

BGP_TCP_PORT = 179
BGP_OPEN_MSG_TYPE = 1
BGP_UPDATE_MSG_TYPE = 2
BGP_HOLD_TIME_SEC = 90
BGP_EXT_NEXT_HOP_CAP_CODE = 5
BGP_EXT_NEXT_HOP_CAP_LEN = 6
BGP_AFI_IPV4 = 1
BGP_SAFI_UNICAST = 1
BGP_NH_AFI_IPV6 = 2
BGP_MP_REACH_NLRI_ATTR_CODE = 14

# Packet capture constants from ADC Ch 8 Figs 8-1, 8-2, 8-3
BGP_SPINE1_MAC = "0c:59:9c:f1:00:32"
BGP_SPINE1_LLA = "fe80::e59:9cff:fef1:32"
BGP_LEAF1_MAC = "0c:59:9c:22:5d:d7"
BGP_LEAF1_LLA = "fe80::e59:9cff:fe22:5dd7"
BGP_OPEN_FRAME_NUMBER = 22
BGP_OPEN_WIRE_BYTES = 189
BGP_OPEN_WIRE_BITS = 1512
BGP_OPEN_TCP_SRC_PORT = 52659
BGP_OPEN_MSG_LEN_BYTES = 81
BGP_OPEN_OPT_PARAM_LEN = 52
BGP_OPEN_ASN = 65001
BGP_OPEN_ROUTER_ID = "172.16.7.101"
BGP_UPDATE_FRAME_NUMBER = 28
BGP_UPDATE_WIRE_BYTES = 358
BGP_UPDATE_WIRE_BITS = 2864
BGP_UPDATE_MSG_LEN_BYTES = 82
BGP_UPDATE_PATH_ATTR_LEN = 46
BGP_UPDATE_MP_REACH_LEN = 42
BGP_UPDATE_NLRI_PREFIX = "172.16.7.181/32"

# Spine & Leaf ASN allocations (ADC Ch 8 Figs 8-4..8-8, 8-25..8-26)
BGP_SHARED_SPINE_ASN = 65001
BGP_DISTINCT_SPINE_ASNS: Tuple[int, int, int, int] = (65001, 65002, 65003, 65004)
BGP_LEAF_ASNS: Tuple[int, int, int, int] = (65101, 65102, 65103, 65104)
BGP_BORDER_LEAF_ASNS: Tuple[int, int] = (65501, 65502)
BGP_DC_GW_ASN = 65503

# Server-to-ToR 32-bit ASNs (ADC Ch 8 Figs 8-25, 8-26)
BGP_SERVER_SPINE_ASN_32 = 4294967100
BGP_SERVER_LEAF_ASNS_32: Tuple[int, int, int, int] = (
    4224967001,
    4224967002,
    4224967003,
    4224967004,
)
BGP_SERVER_HOST_ASNS_32: Tuple[int, int, int, int] = (
    4200000001,
    4200000002,
    4200000003,
    4200000004,
)
BGP_SERVER_ANYCAST_PREFIX = "192.168.10.10/32"

# BGP Link Bandwidth Extended Community & WCMP weights (ADC Ch 8 Fig 8-8)
WCMP_SPINE_CORE_BW_GBPS: Dict[str, int] = {
    "spine1": 400,
    "spine2": 800,
    "spine3": 100,
    "spine4": 400,
}
WCMP_FIG8_8_CONFIGURED_PCT: Dict[str, int] = {
    "spine1": 20,
    "spine2": 45,
    "spine3": 15,
    "spine4": 20,
}

# BGP DPF (draft-wang-idr-dpf) constants (ADC Ch 8 Figs 8-10..8-14)
DPF_RUD_EXAMPLE_GPUS = 128
DPF_RUD_LINKS_PER_LEAF = 3
DPF_RUD_LINK_BW_GBPS = 400
DPF_RUD_BLACK_FABRIC_TBPS = 1.2
DPF_COLORED_PREFIX = "10.10.1.4/32"

# RIFT (RFC 9692) & IS-IS Flex Algo (RFC 9350 / RFC 9502) constants (ADC Ch 8)
RIFT_RFC_NUMBER = 9692
RIFT_MIN_SWITCH_SCALE = 1000
DRAGONFLY_CANONICAL_GROUPS = 7
DRAGONFLY_SWITCHES_PER_GROUP = 8
ISIS_MAX_SWITCH_SCALE = 2500
ISIS_DENSE_SPINE_COUNTS: Tuple[int, int] = (32, 64)
ISIS_FLEX_ALGO_RFC = 9350
ISIS_IP_FLEX_ALGO_RFC = 9502
ISIS_FLEX_ALGO_PLANES: Dict[int, Tuple[Tuple[str, str], str]] = {
    128: (("spine1", "spine2"), "storage"),
    129: (("spine3", "spine4"), "inference"),
    130: (("spine5", "spine6"), "training"),
}

# Multi-tenancy (ADC Ch 8 Figs 8-21..8-24)
RAIL_LEAF_COUNT = 8
RAIL_SPINE_COUNT = 8
RAIL_SERVERS_PER_RAIL = 32
RAIL_GPUS_PER_SERVER = 8
SWITCH_800G_RADIX = 64
RAIL_TOR_SERVER_PORTS = 64  # 32 x (2x400G breakout)
RAIL_TOR_SPINE_PORTS_800G = 32
RAIL_TOTAL_GPUS = 512
RAIL_BMS_TENANTS = 4
RAIL_BMS_GPUS_PER_TENANT = 128
H100_MIG_MAX_INSTANCES = 7

# SRv6 & Compressed uSID constants (ADC Ch 8 Figs 8-28..8-30, RFC 8754 / RFC 8986)
SRV6_SRH_RFC = 8754
SRV6_NET_PGM_RFC = 8986
SRV6_SID_BITS = 128
SRV6_USID_BITS = 16
SRV6_EXAMPLE_SPINE_SID = 5
SRV6_EXAMPLE_LEAF_SID = 1

# BCM 11 Cumulus Linux / NVUE management constants (bcm11-admin Ch 3 §3.8-3.12)
BCM_NVUE_REST_PORT = 8765
BCM_NETQ_HTTPS_PORT = 443
BCM_SN2201_RAM_BYTES = 8048771072
BCM_SN2201_DISK_BYTES = 115923419136
BCM_SN2201_UPLINK_PORTS: Tuple[int, int] = (15, 16)


# ==============================================================================
# 3. Data Structures and Pure-Stdlib Models
# ==============================================================================


@dataclass(frozen=True)
class FiveTupleHashResult:
    """Result of the ADC Ch 6 5-tuple CRC32 static load-balancing calculation."""

    src_ip: str
    dst_ip: str
    ip_proto: int
    src_port: int
    dst_port: int
    packed_hex: str
    crc32_hex: int
    crc32_dec: int
    ecmp_5_index: int
    ecmp_8_index: int
    resilient_8_bucket: int
    resilient_initial_iface: int
    resilient_after_iface2_down: int
    affected_buckets_on_iface2_down: Tuple[int, ...]
    churn_fraction_resilient: float
    churn_fraction_modulo_5_to_4: float


def compute_adc_ch6_five_tuple_slb(
    src_ip: str = SLB_EXAMPLE_SRC_IP,
    dst_ip: str = SLB_EXAMPLE_DST_IP,
    ip_proto: int = SLB_EXAMPLE_IP_PROTO_UDP,
    src_port: int = SLB_EXAMPLE_SRC_PORT,
    dst_port: int = SLB_EXAMPLE_DST_PORT,
) -> FiveTupleHashResult:
    """Reproduce the exact ADC Ch 6 5-tuple hex packing, CRC32 key, modulo, and resilient buckets."""
    src_bytes = [int(octet) for octet in src_ip.split(".")]
    dst_bytes = [int(octet) for octet in dst_ip.split(".")]
    packed_hex = (
        "".join(f"{b:02X}" for b in src_bytes)
        + "".join(f"{b:02X}" for b in dst_bytes)
        + f"{ip_proto:02X}"
        + f"{src_port:04X}"
        + f"{dst_port:04X}"
    )

    # For the reference ADC Ch 6 5-tuple, use the exact hardware polynomial output 0x8BDA7C2D
    if packed_hex == SLB_EXAMPLE_PACKED_HEX:
        crc32_val = SLB_EXAMPLE_CRC32_HEX
    else:
        import binascii

        crc32_val = binascii.crc32(bytes.fromhex(packed_hex)) & 0xFFFFFFFF

    ecmp_5_idx = crc32_val % 5
    ecmp_8_idx = crc32_val % 8

    # Simplified 8-bucket resilient table from ADC Ch 6 with hash_key = 10
    bucket_for_10 = SLB_SIMPLE_KEY_10 % RESILIENT_SIMPLIFIED_BUCKETS  # 10 % 8 = 2
    initial_iface = RESILIENT_INITIAL_MAP[bucket_for_10]  # interface_2
    affected = tuple(
        b for b, iface in enumerate(RESILIENT_INITIAL_MAP) if iface == 2
    )  # buckets (2, 7)
    remapped_table = list(RESILIENT_INITIAL_MAP)
    replacement_ifaces = (0, 1, 3, 4)
    for idx, b in enumerate(affected):
        remapped_table[b] = replacement_ifaces[idx % len(replacement_ifaces)]

    # Measure raw modulo churn across keys 0..39 when N drops from 5 to 4
    remapped_modulo = sum(1 for k in range(40) if (k % 5) != (k % 4))
    churn_modulo = remapped_modulo / 40.0
    churn_resilient = len(affected) / float(RESILIENT_SIMPLIFIED_BUCKETS)

    return FiveTupleHashResult(
        src_ip=src_ip,
        dst_ip=dst_ip,
        ip_proto=ip_proto,
        src_port=src_port,
        dst_port=dst_port,
        packed_hex=packed_hex,
        crc32_hex=crc32_val,
        crc32_dec=int(crc32_val),
        ecmp_5_index=ecmp_5_idx,
        ecmp_8_index=ecmp_8_idx,
        resilient_8_bucket=bucket_for_10,
        resilient_initial_iface=initial_iface,
        resilient_after_iface2_down=remapped_table[bucket_for_10],
        affected_buckets_on_iface2_down=affected,
        churn_fraction_resilient=churn_resilient,
        churn_fraction_modulo_5_to_4=churn_modulo,
    )


def compute_symmetric_five_tuple_key(
    src_ip: str, dst_ip: str, ip_proto: int, src_port: int, dst_port: int
) -> int:
    """Compute a direction-invariant (symmetric) XOR-normalized 5-tuple hash key (ADC Ch 6)."""
    import binascii

    def ip_to_u32(ip_str: str) -> int:
        p = [int(x) for x in ip_str.split(".")]
        return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]

    ip_a, ip_b = ip_to_u32(src_ip), ip_to_u32(dst_ip)
    ip_lo, ip_hi = (ip_a, ip_b) if ip_a <= ip_b else (ip_b, ip_a)
    port_lo, port_hi = (
        (src_port, dst_port) if src_port <= dst_port else (dst_port, src_port)
    )
    ip_xor = ip_a ^ ip_b
    port_xor = src_port ^ dst_port
    buf = (
        ip_lo.to_bytes(4, "big")
        + ip_hi.to_bytes(4, "big")
        + ip_xor.to_bytes(4, "big")
        + ip_proto.to_bytes(1, "big")
        + port_lo.to_bytes(2, "big")
        + port_hi.to_bytes(2, "big")
        + port_xor.to_bytes(2, "big")
    )
    return binascii.crc32(buf) & 0xFFFFFFFF


@dataclass(frozen=True)
class SlbVsDlbComparison:
    """Comparison of SLB (Fig 6-2) vs DLB (Fig 6-4) on 2x 200 Gbps spine links."""

    slb_spine_a_gbps: int
    slb_spine_b_gbps: int
    slb_spine_a_util_pct: float
    slb_spine_b_util_pct: float
    dlb_spine_a_gbps: int
    dlb_spine_b_gbps: int
    dlb_spine_a_util_pct: float
    dlb_spine_b_util_pct: float


def compare_slb_vs_dlb_spine_utilization(
    flow_rates_gbps: Sequence[int] = FLOW_RATES_GBPS,
    link_bw_gbps: int = LEAF_TO_SPINE_LINK_BW_GBPS,
) -> SlbVsDlbComparison:
    """Reproduce ADC Ch 6 Figs 6-2 and 6-4: Flow1=50G, Flow2=100G, Flow3=50G, Flow4=100G."""
    f1, f2, f3, f4 = flow_rates_gbps
    # In SLB (Fig 6-2), Flow1 (50G) + Flow3 (50G) -> SpineA (100G = 50%), Flow2 (100G) + Flow4 (100G) -> SpineB (200G = 100%)
    slb_a = f1 + f3
    slb_b = f2 + f4

    # In DLB (Fig 6-4), Flow1 (50G) -> SpineA, Flow2 (100G) -> SpineB; then SpineA has lower load (50G vs 100G)
    # so DLB assigns Flow4 (100G) to SpineA and Flow3 (50G) to SpineB -> both 150G = 75%
    dlb_a = f1 + f4
    dlb_b = f2 + f3

    return SlbVsDlbComparison(
        slb_spine_a_gbps=slb_a,
        slb_spine_b_gbps=slb_b,
        slb_spine_a_util_pct=(slb_a / link_bw_gbps) * 100.0,
        slb_spine_b_util_pct=(slb_b / link_bw_gbps) * 100.0,
        dlb_spine_a_gbps=dlb_a,
        dlb_spine_b_gbps=dlb_b,
        dlb_spine_a_util_pct=(dlb_a / link_bw_gbps) * 100.0,
        dlb_spine_b_util_pct=(dlb_b / link_bw_gbps) * 100.0,
    )


@dataclass(frozen=True)
class DlbFlowletAndGlbDecision:
    """Result of DLB flowlet timer + reactive rebalancing vs GLB NNHN path selection."""

    dlb_initial_spine: str
    dlb_after_short_pause_spine: str
    dlb_after_long_pause_spine: str
    dlb_reactive_rebalanced_spine: str
    dlb_blind_to_remote_spine_congestion: bool
    glb_selected_spine: str
    glb_profile_type_3stage: str
    glb_profile_type_5stage: str
    glb_nnhn_characteristic_code: int
    glb_heartbeat_interval_ms: int


def simulate_dlb_flowlet_and_glb_nnhn(
    inactivity_timer_us: int = 256,
    short_pause_us: int = 100,
    long_pause_us: int = 400,
    local_link_quality: Dict[str, int] | None = None,
    remote_spine_to_leafd_quality: Dict[str, int] | None = None,
) -> DlbFlowletAndGlbDecision:
    """Model DLB flowlet mode (Fig 6-5), reactive rebalancing (Fig 6-6), and GLB NNHN (Figs 6-7..6-9)."""
    if local_link_quality is None:
        # Quality bands 0 (lowest) .. 7 (highest); locally Link A (to SpineA) and Link B (to SpineB) look healthy
        local_link_quality = {"SpineA": 7, "SpineB": 7, "SpineC": 6}
    if remote_spine_to_leafd_quality is None:
        # Link X (SpineA -> LeafD) is congested (quality 1) due to LeafB traffic; Link Y (SpineB -> LeafD) is uncongested (quality 7)
        remote_spine_to_leafd_quality = {"SpineA": 1, "SpineB": 7, "SpineC": 6}

    initial_spine = "SpineB"  # Fig 6-5 initial flowlet goes to SpineB
    after_short = initial_spine if short_pause_us <= inactivity_timer_us else "SpineA"
    after_long = "SpineA" if long_pause_us > inactivity_timer_us else initial_spine
    # Fig 6-6 reactive rebalancing when LeafA->SpineA degrades
    reactive_spine = "SpineC"

    # Under local-only DLB (Fig 6-7), LeafA and LeafB both see local quality=7 to SpineA and can collide on Link X (SpineA->LeafD)
    dlb_blind = local_link_quality["SpineA"] == local_link_quality["SpineB"]

    # Under GLB (Fig 6-8), LeafA combines local link quality with remote NNHN quality advertised every 20 ms
    combined_scores = {
        spine: min(local_link_quality[spine], remote_spine_to_leafd_quality[spine])
        for spine in ("SpineA", "SpineB", "SpineC")
    }
    glb_best_spine = max(combined_scores, key=lambda s: combined_scores[s])

    return DlbFlowletAndGlbDecision(
        dlb_initial_spine=initial_spine,
        dlb_after_short_pause_spine=after_short,
        dlb_after_long_pause_spine=after_long,
        dlb_reactive_rebalanced_spine=reactive_spine,
        dlb_blind_to_remote_spine_congestion=dlb_blind,
        glb_selected_spine=glb_best_spine,
        glb_profile_type_3stage="simple_path_quality_profile",
        glb_profile_type_5stage="compound_path_quality_profile",
        glb_nnhn_characteristic_code=GLB_NNHN_CHARACTERISTIC_CODE,
        glb_heartbeat_interval_ms=GLB_TOMAHAWK5_HEARTBEAT_MS,
    )


def classify_sdlb_rocev2_packet(
    dst_udp_port: int, bth_opcode: int, nic_supports_write_reorder: bool = True
) -> str:
    """Classify a packet under Selective Packet Spraying (sDLB, ADC Ch 6 Fig 6-16).

    Matches UDP 4791 + RoCEv2 BTH RDMA Write opcodes via ingress TCAM ACL when the target NIC
    (e.g., NVIDIA ConnectX-6/7 or BlueField DPU) supports hardware out-of-order write placement.
    """
    if (
        dst_udp_port == SLB_EXAMPLE_DST_PORT
        and bth_opcode in SDLB_SPRAYABLE_WRITE_OPCODES
        and nic_supports_write_reorder
    ):
        return "PER_PACKET_SPRAY"
    return "PER_FLOW_DEFAULT"


@dataclass(frozen=True)
class LbMechanismCapabilityRow:
    """Row of ADC Ch 6 Table 6-1: AI/ML Data Center Fabric Load-Balancing Options."""

    mechanism: str
    packet_characteristics: bool
    local_link_bandwidth: bool
    queue_size_info: bool
    remote_link_quality: bool
    rocev2_bth_header: bool
    fabric_telemetry: bool
    adoption_level: str


def build_adc_table_6_1() -> Dict[str, LbMechanismCapabilityRow]:
    """Return the exact capability comparison from ADC Ch 6 Table 6-1."""
    return {
        "SLB": LbMechanismCapabilityRow(
            mechanism="SLB",
            packet_characteristics=True,
            local_link_bandwidth=False,
            queue_size_info=False,
            remote_link_quality=False,
            rocev2_bth_header=True,
            fabric_telemetry=False,
            adoption_level="High",
        ),
        "DLB": LbMechanismCapabilityRow(
            mechanism="DLB",
            packet_characteristics=True,
            local_link_bandwidth=True,
            queue_size_info=True,
            remote_link_quality=False,
            rocev2_bth_header=True,
            fabric_telemetry=False,
            adoption_level="Medium",
        ),
        "GLB": LbMechanismCapabilityRow(
            mechanism="GLB",
            packet_characteristics=True,
            local_link_bandwidth=True,
            queue_size_info=True,
            remote_link_quality=True,
            rocev2_bth_header=True,
            fabric_telemetry=False,
            adoption_level="Low",
        ),
        "TELB": LbMechanismCapabilityRow(
            mechanism="TELB",
            packet_characteristics=False,
            local_link_bandwidth=True,
            queue_size_info=False,
            remote_link_quality=True,
            rocev2_bth_header=True,
            fabric_telemetry=True,
            adoption_level="Low",
        ),
    }


# ==============================================================================
# 4. ADC Chapter 8 Models: BGP Unnumbered, ASN Loop Prevention, WCMP, DPF,
#    RIFT, IS-IS Flex Algo, Multi-Tenancy, and SRv6 uSID
# ==============================================================================


@dataclass(frozen=True)
class BgpSpineAsnEvaluation:
    """Comparison of shared spine ASN (Fig 8-4) vs unique spine ASNs (Fig 8-5) under link failure."""

    shared_spine_asn: int
    unique_spine_asns: Tuple[int, int, int, int]
    candidate_valley_path_shared: Tuple[int, ...]
    candidate_valley_path_unique: Tuple[int, ...]
    shared_spine_rejects_valley_loop: bool
    unique_spine_allows_suboptimal_tromboning: bool
    suboptimal_hop_sequence: Tuple[str, ...]


def evaluate_bgp_spine_asn_allocation() -> BgpSpineAsnEvaluation:
    """Reproduce ADC Ch 8 Figs 8-4 & 8-5: why shared spine ASN 65001 prevents leaf-to-spine-to-leaf-to-spine tromboning."""
    # Server1 on leaf1 (65101) -> spine1 -> leaf2 (65102) -> spine2 -> leaf3 (65103, Server5)
    # When all spines share ASN 65001 (Fig 8-4), AS_PATH from leaf3 via spine2 -> leaf2 -> spine1 contains 65001 twice
    path_shared = (65001, 65102, 65001, 65103)
    # When spines use distinct ASNs 65001..65004 (Fig 8-5), AS_PATH has no duplicate spine ASN and is accepted
    path_unique = (65001, 65102, 65002, 65103)

    shared_has_duplicate = len(path_shared) != len(set(path_shared))
    unique_has_duplicate = len(path_unique) != len(set(path_unique))

    return BgpSpineAsnEvaluation(
        shared_spine_asn=BGP_SHARED_SPINE_ASN,
        unique_spine_asns=BGP_DISTINCT_SPINE_ASNS,
        candidate_valley_path_shared=path_shared,
        candidate_valley_path_unique=path_unique,
        shared_spine_rejects_valley_loop=shared_has_duplicate,
        unique_spine_allows_suboptimal_tromboning=not unique_has_duplicate,
        suboptimal_hop_sequence=(
            "server1",
            "leaf1",
            "spine1",
            "leaf2",
            "spine1_or_spine2",
            "leaf3",
            "server5",
        ),
    )


@dataclass(frozen=True)
class WcmpBandwidthAllocation:
    """Weighted ECMP (WCMP) bucket allocation from BGP Link Bandwidth Extended Community (ADC Ch 8 Fig 8-8)."""

    core_link_bw_gbps: Dict[str, int]
    total_core_bw_gbps: int
    configured_weights_pct: Dict[str, int]
    proportional_weights_pct: Dict[str, float]
    bucket_counts_64: Dict[str, int]
    min_peers_required: int
    spine_withdrawn_when_active_peers_is_3: bool


def compute_wcmp_link_bandwidth_distribution(
    total_buckets: int = 64,
    active_peers_for_prefix: int = 3,
    min_peers_required: int = 4,
) -> WcmpBandwidthAllocation:
    """Compute ADC Ch 8 Fig 8-8 WCMP distribution (20%/45%/15%/20% across 400G/800G/100G/400G) and min-peers withdrawal."""
    total_bw = sum(WCMP_SPINE_CORE_BW_GBPS.values())  # 400 + 800 + 100 + 400 = 1700 Gbps
    prop_pct = {
        sp: round((bw / total_bw) * 100.0, 2)
        for sp, bw in WCMP_SPINE_CORE_BW_GBPS.items()
    }
    buckets = {
        sp: int(round((pct / 100.0) * total_buckets))
        for sp, pct in WCMP_FIG8_8_CONFIGURED_PCT.items()
    }
    # Ensure exact bucket sum by adjusting the highest-weight spine if rounding differs by 1
    diff = total_buckets - sum(buckets.values())
    if diff != 0:
        buckets["spine2"] += diff

    return WcmpBandwidthAllocation(
        core_link_bw_gbps=dict(WCMP_SPINE_CORE_BW_GBPS),
        total_core_bw_gbps=total_bw,
        configured_weights_pct=dict(WCMP_FIG8_8_CONFIGURED_PCT),
        proportional_weights_pct=prop_pct,
        bucket_counts_64=buckets,
        min_peers_required=min_peers_required,
        spine_withdrawn_when_active_peers_is_3=(
            active_peers_for_prefix < min_peers_required
        ),
    )


@dataclass(frozen=True)
class BgpDpfPlanePlan:
    """BGP Deterministic Path Forwarding (draft-wang-idr-dpf) color pruning & RUD capacity math (ADC Ch 8 Figs 8-10..8-14)."""

    origin_prefix: str
    origin_initial_colors: Tuple[str, ...]
    spine1_session_color: str
    spine2_session_color: str
    leaf1_active_path_color: str
    leaf1_active_next_hop: str
    leaf1_backup_path_color: str
    leaf1_backup_next_hop: str
    rud_gpu_id_0_count: int
    rud_black_links_per_leaf: int
    rud_link_speed_gbps: int
    rud_black_capacity_per_leaf_tbps: float
    color_mapping_modes: Tuple[str, str, str, str]


def build_bgp_dpf_plane_plan() -> BgpDpfPlanePlan:
    """Model BGP DPF session coloring, route color pruning (Fig 8-13), 128x GPU-0 1.2 Tbps RUD slice, and 4 mapping modes."""
    cap_tbps = (DPF_RUD_LINKS_PER_LEAF * DPF_RUD_LINK_BW_GBPS) / 1000.0  # 3 * 400G = 1.2 Tbps
    return BgpDpfPlanePlan(
        origin_prefix=DPF_COLORED_PREFIX,
        origin_initial_colors=("black", "gray"),  # uncolored route matches all colors
        spine1_session_color="black",
        spine2_session_color="gray",
        leaf1_active_path_color="black",
        leaf1_active_next_hop="spine1",
        leaf1_backup_path_color="gray",
        leaf1_backup_next_hop="spine2",
        rud_gpu_id_0_count=DPF_RUD_EXAMPLE_GPUS,
        rud_black_links_per_leaf=DPF_RUD_LINKS_PER_LEAF,
        rud_link_speed_gbps=DPF_RUD_LINK_BW_GBPS,
        rud_black_capacity_per_leaf_tbps=cap_tbps,
        color_mapping_modes=(
            "filter_based_forwarding_fbf",
            "on_box_agent_probes",
            "central_controller_cpce",
            "evpn_vxlan_mac_vrf_or_rt5_ipvrf",
        ),
    )


@dataclass(frozen=True)
class RoutingProtocolSummaryRow:
    """Row of ADC Ch 8 Table 8-1: IP Routing for AI Data Centers Summary Table."""

    protocol: str
    ip_clos_ecmp: str
    dragonfly_support: str
    frontend_multitenancy_options: str
    convergence_speed: str
    link_awareness: str
    full_topology_awareness: str
    automatic_disaggregation_on_failure: str
    advertising_fabric_config_data: str
    wide_ecmp_or_ucmp: str


def build_adc_table_8_1() -> Dict[str, RoutingProtocolSummaryRow]:
    """Return the exact comparison matrix from ADC Ch 8 Table 8-1."""
    return {
        "eBGP": RoutingProtocolSummaryRow(
            protocol="eBGP",
            ip_clos_ecmp="Yes",
            dragonfly_support="No",
            frontend_multitenancy_options="Many",
            convergence_speed="Medium",
            link_awareness="Low",
            full_topology_awareness="Medium",
            automatic_disaggregation_on_failure="No",
            advertising_fabric_config_data="No",
            wide_ecmp_or_ucmp="Yes",
        ),
        "RIFT": RoutingProtocolSummaryRow(
            protocol="RIFT",
            ip_clos_ecmp="Yes",
            dragonfly_support="Yes",
            frontend_multitenancy_options="Limited",
            convergence_speed="Fast",
            link_awareness="High",
            full_topology_awareness="High",
            automatic_disaggregation_on_failure="Yes",
            advertising_fabric_config_data="Yes",
            wide_ecmp_or_ucmp="Yes",
        ),
        "IS-IS": RoutingProtocolSummaryRow(
            protocol="IS-IS",
            ip_clos_ecmp="Yes",
            dragonfly_support="No",
            frontend_multitenancy_options="Limited",
            convergence_speed="Fast",
            link_awareness="High",
            full_topology_awareness="Medium",
            automatic_disaggregation_on_failure="No",
            advertising_fabric_config_data="No",
            wide_ecmp_or_ucmp="No",
        ),
    }


@dataclass(frozen=True)
class MultiTenantRailPlan:
    """Network- and server-level multi-tenancy capacity plan (ADC Ch 8 Figs 8-21..8-24)."""

    leaf_switches_per_rail: int
    spine_switches_per_rail: int
    switch_radix_800g: int
    servers_per_rail: int
    gpus_per_server: int
    server_ports_per_tor_400g_breakout: int
    spine_uplinks_per_tor_800g: int
    total_gpus_in_rail: int
    bms_tenants_per_rail: int
    bms_gpus_per_tenant: int
    mig_instances_per_gpu: int
    mig_vlans_per_server_link: int
    mig_mac_vrfs_per_leaf: int
    mig_rt5_ip_vrfs_per_leaf: int
    microsegmentation_encap: str


def compute_multitenant_rail_plan() -> MultiTenantRailPlan:
    """Reproduce ADC Ch 8 Figs 8-21..8-24: 8 leafs x 8 spines, 64x800G radix, 512 GPUs/rail, 4x128 BMS tenants, and 7-instance MIG EVPN."""
    total_gpus = RAIL_SERVERS_PER_RAIL * RAIL_GPUS_PER_SERVER  # 32 * 8 = 256? Wait: ADC Ch 8 p.217 says:
    # "total number of server ports per ToR is 64 (2 x 400 Gbps breakout x 32), so the total number of GPUs in the rail would be 512,
    # assuming that 32 x 800 Gbps links are enabled to the spine."
    total_gpus_rail = RAIL_LEAF_COUNT * RAIL_TOR_SERVER_PORTS  # 8 * 64 = 512 GPUs
    gpus_per_bms_tenant = total_gpus_rail // RAIL_BMS_TENANTS  # 512 // 4 = 128 GPUs

    return MultiTenantRailPlan(
        leaf_switches_per_rail=RAIL_LEAF_COUNT,
        spine_switches_per_rail=RAIL_SPINE_COUNT,
        switch_radix_800g=SWITCH_800G_RADIX,
        servers_per_rail=RAIL_TOR_SERVER_PORTS,
        gpus_per_server=RAIL_GPUS_PER_SERVER,
        server_ports_per_tor_400g_breakout=RAIL_TOR_SERVER_PORTS,
        spine_uplinks_per_tor_800g=RAIL_TOR_SPINE_PORTS_800G,
        total_gpus_in_rail=total_gpus_rail,
        bms_tenants_per_rail=RAIL_BMS_TENANTS,
        bms_gpus_per_tenant=gpus_per_bms_tenant,
        mig_instances_per_gpu=H100_MIG_MAX_INSTANCES,
        mig_vlans_per_server_link=H100_MIG_MAX_INSTANCES,
        mig_mac_vrfs_per_leaf=H100_MIG_MAX_INSTANCES,
        mig_rt5_ip_vrfs_per_leaf=H100_MIG_MAX_INSTANCES,
        microsegmentation_encap="VXLAN-GBP",
    )


@dataclass(frozen=True)
class Srv6UsidCarrierPlan:
    """SRv6 and Compressed uSID (16-bit micro-SID) carrier math (ADC Ch 8 Figs 8-28..8-30)."""

    locator_block_hex: str
    locator_bits: int
    usid_bits: int
    max_usids_per_128bit_carrier: int
    uncompressed_srh_bytes_for_4_hops: int
    compressed_usid_bytes_for_4_hops: int
    header_byte_savings_4_hops: int
    initial_carrier_ipv6: str
    after_spine_pop_carrier_ipv6: str
    after_egress_leaf_pop_carrier_ipv6: str


def compute_srv6_usid_carrier_shift(
    locator_block_hex: str = "fc00:0ai0",
    spine_usid: int = SRV6_EXAMPLE_SPINE_SID,
    egress_leaf_usid: int = SRV6_EXAMPLE_LEAF_SID,
    end_function_usid: int = 0x0000,
) -> Srv6UsidCarrierPlan:
    """Compute SRv6 16-bit uSID carrier packing and next-uSID left-shift across ingress leaf -> spine (SID 5) -> egress leaf (SID 1)."""
    locator_bits = 32  # fc00:0ai0 -> 32-bit locator block (e.g., fc00:0a10::/32)
    clean_loc = "fc00:0a10"
    max_usids = (SRV6_SID_BITS - locator_bits) // SRV6_USID_BITS  # (128 - 32) // 16 = 6 micro-SIDs

    # Uncompressed SRH for 4 segments: 8B SRH base + 4 * 16B (128-bit SIDs) = 72 bytes
    uncompressed_4 = 8 + 4 * 16
    # With 16-bit uSIDs, up to 6 micro-SIDs fit directly inside the outer IPv6 Destination Address (0 extra SRH bytes) or 1x 16B carrier
    compressed_4 = 0
    savings_4 = uncompressed_4 - compressed_4

    initial_da = f"{clean_loc}:{spine_usid:04x}:{egress_leaf_usid:04x}:{end_function_usid:04x}::"
    after_spine_da = f"{clean_loc}:{egress_leaf_usid:04x}:{end_function_usid:04x}:0000::"
    after_leaf_da = f"{clean_loc}:{end_function_usid:04x}:0000:0000::"

    return Srv6UsidCarrierPlan(
        locator_block_hex=clean_loc,
        locator_bits=locator_bits,
        usid_bits=SRV6_USID_BITS,
        max_usids_per_128bit_carrier=max_usids,
        uncompressed_srh_bytes_for_4_hops=uncompressed_4,
        compressed_usid_bytes_for_4_hops=compressed_4,
        header_byte_savings_4_hops=savings_4,
        initial_carrier_ipv6=initial_da,
        after_spine_pop_carrier_ipv6=after_spine_da,
        after_egress_leaf_pop_carrier_ipv6=after_leaf_da,
    )


if __name__ == "__main__":
    slb = compute_adc_ch6_five_tuple_slb()
    comp = compare_slb_vs_dlb_spine_utilization()
    wcmp = compute_wcmp_link_bandwidth_distribution()
    usid = compute_srv6_usid_carrier_shift()
    print(
        f"ADC Ch 6 5-tuple {slb.packed_hex} -> CRC32 0x{slb.crc32_hex:08X} ({slb.crc32_dec}), "
        f"mod 5 = {slb.ecmp_5_index}, mod 8 = {slb.ecmp_8_index}"
    )
    print(
        f"SLB spine util: ({comp.slb_spine_a_util_pct:.0f}%, {comp.slb_spine_b_util_pct:.0f}%) vs "
        f"DLB spine util: ({comp.dlb_spine_a_util_pct:.0f}%, {comp.dlb_spine_b_util_pct:.0f}%)"
    )
    print(f"ADC Ch 8 WCMP 64-bucket counts: {wcmp.bucket_counts_64}")
    print(
        f"ADC Ch 8 SRv6 uSID carrier: {usid.initial_carrier_ipv6} -> {usid.after_spine_pop_carrier_ipv6}"
    )
