#!/usr/bin/env python3
"""Chapter 12.6 model: InfiniBand fundamentals and addressing.

Models the physical signaling and line-encoding generations (SDR through GDR,
8b/10b, 64b/66b, and 256b/257b across 4x and 12x lane widths), 64-bit GUIDs
(NodeGUID, PortGUID, SystemImage GUID), 16-bit Local Identifiers (LID 0 reserved,
1..49151 unicast, 49152..65534 multicast, 65535 permissive) and LID Mask Control
(LMC, 2^LMC consecutive LIDs from Base LID with lower LMC bits zero), 128-bit
Global Identifiers (GID prefixes fe80::/64 link-local, fec0::/64 site-local,
ff00::/8 multicast + 64-bit PortGUID), directed-route Subnet Management Packets
(SMP hop count, hop pointer, D direction bit, initial and return paths on VL15),
16-bit Partition Keys (P_Key 15-bit partition ID + 1-bit membership bit 0x8000,
default partition 0x7fff limited vs 0xffff full membership interoperability rule),
IP over InfiniBand (IPoIB 20-byte link-layer hardware address = 1B flags + 3B QPN +
16B GID, datagram mode up to 4 KB MTU vs connected mode up to 64 KB MTU),
InfiniBand frame format overhead (LRH 8B, optional GRH 40B, BTH 12B, ETH/RETH,
ICRC 4B, VCRC 2B), and link-level Credit-Based Flow Control (CBFC 64-byte credit
units across 16 Virtual Lanes: VL0..VL14 data + VL15 dedicated to SMPs) from:
  - *Supercomputers for Linux SysAdmins* (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`),
    Chapter 5 ("5. InfiniBand", `/var/folders/5k/hkmswyf95w5b0y7_xc87ddf80000gn/T/opencode/scl5.txt`):
    * Table 5-1: SDR (2.5 Gbps raw, 8b/10b, 8 Gbps 4x, 24 Gbps 12x), DDR (5 Gbps raw,
      8b/10b, 16 Gbps 4x, 48 Gbps 12x), QDR (10 Gbps raw, 8b/10b, 32 Gbps 4x, 96 Gbps 12x),
      FDR10 (10.3125 Gbps raw, 64b/66b, 40 Gbps 4x, 120 Gbps 12x), FDR (14.0625 Gbps raw,
      64b/66b, 54.4 Gbps / 56 Gbps 4x, 163.2 Gbps 12x), EDR (25.78125 Gbps raw, 64b/66b,
      100 Gbps 4x, 300 Gbps 12x), HDR (53.125 Gbps raw, 64b/66b, 200 Gbps 4x, 600 Gbps 12x),
      NDR (106.25 Gbps raw, 256b/257b, 400 Gbps 4x, 1200 Gbps 12x), XDR (200 Gbps effective
      per lane, 800 Gbps 4x, 2400 Gbps 12x), GDR (400 Gbps effective per lane, 1600 Gbps 4x,
      4800 Gbps 12x)
    * Subnet scale and LID ranges: 2^15 + 2^14 - 1 = 49,151 unicast end ports and switches
      (0x0001..0xBFFF); 0x0000 reserved; 0xC000..0xFFFE (49,152..65,534) multicast;
      0xFFFF (65,535) permissive LID; LMC 2^LMC consecutive LIDs [Base LID .. Base LID + 2^LMC - 1]
    * GID prefixes: 0xFE80::/64 link-local, 0xFEC0::/64 site-local, 0xFF00::/8 multicast
    * Directed-route SMPs (D=0 forward, D=1 reverse, hop pointer, hop count, reverse path)
    * IPoIB 20-byte link-layer hardware address (1-byte flags + 3-byte QPN + 16-byte GID)
    * OFED diagnostic utilities (`ibstat`, `ibstatus`, `ibdev2netdev`, `perfquery`,
      `ibqueryerrors`, `mlxlink`, `ibping`, `smpquery`, `saquery`, `ibnetdiscover`, `ibdiagnet`)
  - *AI Data Center Network Design and Technologies* (`ai-data-center-network-design-and-technologies`),
    Chapter 9 ("9. Storage" — InfiniBand for Storage):
    * 16-bit LID (~48,000 / 49,151 unicast endpoints), RDMA_PRTYPE 02 (IB) vs 04 (RoCEv2) vs 05 (iWARP),
      TCP 8009 discovery, UDP 4420 CM, UDP 4791 RoCEv2
    * Figure 9-21 IB data frame format: LRH (8B, S-LID / D-LID) + optional GRH (40B) +
      BTH (12B, opcode + Dest QP) + ETH (source QP / RDMA extended header) + Payload +
      ICRC (4B) + VCRC (2B)
    * Figure 9-22 IB QoS & Credit-Based Flow Control (CBFC): up to 16 Virtual Lanes (VL0..VL15,
      8 to 12 workload queues + VL15 SMP), 64-byte credit units exchanged at LLH per VL
    * Table 9-2 comparison of InfiniBand vs NVMe-o-RDMA, NVMe-o-TCP, and (P)NFS (~300 ns switch latency)
  - `bcm11-admin` §3.6.3, §3.6.4, and §5.3.3:
    * `ibnet` (`ib.cluster`, `10.149.0.0/16`, `10.149.0.1`..`10.149.255.254`), IPoIB datagram mode
      (up to 4 KB / 4,092 B MTU) vs connected mode (up to 64 KB / 65,520 B MTU)
  - `nvidia-devops` Volume 08 (`chapter-01..04`, `chapter-12`, `index.md`, `labs/lab-01..04`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# --- InfiniBand LID & Addressing Constants (SCL Ch 5 & ADC Ch 9) ---
LID_BITS: int = 16
LID_RESERVED: int = 0x0000
LID_UNICAST_MIN: int = 0x0001  # 1
LID_UNICAST_MAX: int = 0xBFFF  # 2^15 + 2^14 - 1 = 32768 + 16383 = 49151
LID_MULTICAST_MIN: int = 0xC000  # 49152
LID_MULTICAST_MAX: int = 0xFFFE  # 65534
LID_PERMISSIVE: int = 0xFFFF  # 65535
APPROX_SUBNET_NODE_LIMIT: int = 48000  # ADC Ch 9 practical approximation of 49,151

GUID_BITS: int = 64
GID_BITS: int = 128
GID_LINK_LOCAL_PREFIX: int = 0xFE80000000000000
GID_SITE_LOCAL_PREFIX: int = 0xFEC0000000000000
GID_MULTICAST_HIGH_BYTE: int = 0xFF

# --- Partition Key (P_Key) Constants (V8 Ch 4 & IBTA Spec) ---
PKEY_BITS: int = 16
PKEY_MEMBERSHIP_BIT: int = 0x8000  # Bit 15: 1 = Full member, 0 = Limited member
PKEY_ID_MASK: int = 0x7FFF  # Lower 15 bits: Partition ID
DEFAULT_PKEY_LIMITED: int = 0x7FFF
DEFAULT_PKEY_FULL: int = 0xFFFF

# --- IPoIB Constants (SCL Ch 5 & BCM11 §3.6.4, RFC 4391, RFC 4392, RFC 4755) ---
IPOIB_RFC_DATAGRAM: int = 4391
IPOIB_RFC_MULTICAST: int = 4392
IPOIB_RFC_CONNECTED: int = 4755
IPOIB_HWADDR_BYTES: int = 20  # 1B flags + 3B QPN + 16B GID (vs 6B Ethernet MAC)
ETHERNET_MAC_BYTES: int = 6
IPOIB_DATAGRAM_MAX_MTU: int = 4096  # 4 KB IB MTU -> 4092 B IPoIB payload
IPOIB_CONNECTED_MAX_MTU: int = 65536  # 64 KB (65520 B practical max in Linux)
BCM_DEFAULT_IBNET_CIDR: str = "10.149.0.0/16"

# Rounded display percentages for line encodings (80.00%, 96.97%, 99.61%) and frame efficiencies (99.37%, 98.99%, 98.04%)
ENCODING_EFF_8B10B_STR: str = "80.00%"
ENCODING_EFF_64B66B_STR: str = "96.97%"
ENCODING_EFF_256B257B_STR: str = "99.61%"
FRAME_EFF_LOCAL_SEND_STR: str = "99.37%"
FRAME_EFF_LOCAL_RDMA_STR: str = "98.99%"
FRAME_EFF_ROUTED_RDMA_STR: str = "98.04%"

# --- InfiniBand Frame & QoS / CBFC Constants (ADC Ch 9 Fig 9-21 & 9-22) ---
LRH_BYTES: int = 8  # Local Route Header (VL, LVer, SL, LNH, DLID, PktLen, SLID)
GRH_BYTES: int = 40  # Global Route Header (IPv6 header format, optional intra-subnet)
BTH_BYTES: int = 12  # Base Transport Header (Opcode, SE, M, PadCnt, TVer, P_Key, DestQP, A, PSN)
RETH_BYTES: int = 16  # RDMA Extended Transport Header (VA 8B + R_Key 4B + DMA Len 4B)
ICRC_BYTES: int = 4  # Invariant CRC (end-to-end)
VCRC_BYTES: int = 2  # Variant CRC (link-by-link)
TOTAL_VIRTUAL_LANES: int = 16  # VL0..VL15
DATA_VIRTUAL_LANES_MAX: int = 15  # VL0..VL14 for data (typically 8..12 active queues)
SMP_VIRTUAL_LANE: int = 15  # VL15 reserved exclusively for Subnet Management Packets (uncredited)
CBFC_CREDIT_UNIT_BYTES: int = 64  # 1 flow-control credit = 64 bytes of receive buffer
IB_SWITCH_LATENCY_NS: int = 300  # ADC Ch 9 ~300 ns cut-through switch latency

# NVMe-oF RDMA Provider Types (ADC Ch 9)
RDMA_PRTYPE_IB: int = 2
RDMA_PRTYPE_ROCEV2: int = 4
RDMA_PRTYPE_IWARP: int = 5
NVME_DISCOVERY_TCP_PORT: int = 8009
ROCEV2_CM_UDP_PORT: int = 4420
ROCEV2_DATA_UDP_PORT: int = 4791


@dataclass(frozen=True)
class IbGenerationSpec:
    """InfiniBand signaling rate, line encoding, and effective bandwidth per generation (SCL Ch 5 Table 5-1)."""

    name: str
    raw_lane_rate_gbps: float
    encoding: str
    data_bits_per_block: int
    total_bits_per_block: int
    effective_lane_rate_gbps: float
    effective_4x_gbps: float
    effective_12x_gbps: float


IB_GENERATIONS: Dict[str, IbGenerationSpec] = {
    "SDR": IbGenerationSpec("SDR", 2.5, "8b/10b", 8, 10, 2.0, 8.0, 24.0),
    "DDR": IbGenerationSpec("DDR", 5.0, "8b/10b", 8, 10, 4.0, 16.0, 48.0),
    "QDR": IbGenerationSpec("QDR", 10.0, "8b/10b", 8, 10, 8.0, 32.0, 96.0),
    "FDR10": IbGenerationSpec("FDR10", 10.3125, "64b/66b", 64, 66, 10.0, 40.0, 120.0),
    "FDR": IbGenerationSpec("FDR", 14.0625, "64b/66b", 64, 66, 13.6, 54.4, 163.2),
    "EDR": IbGenerationSpec("EDR", 25.78125, "64b/66b", 64, 66, 25.0, 100.0, 300.0),
    "HDR": IbGenerationSpec("HDR", 53.125, "64b/66b", 64, 66, 50.0, 200.0, 600.0),
    "NDR": IbGenerationSpec("NDR", 106.25, "256b/257b", 256, 257, 100.0, 400.0, 1200.0),
    "XDR": IbGenerationSpec("XDR", 200.0, "256b/257b", 256, 257, 200.0, 800.0, 2400.0),
    "GDR": IbGenerationSpec("GDR", 400.0, "256b/257b", 256, 257, 400.0, 1600.0, 4800.0),
}


def compute_ib_link_bandwidth(generation: str, lanes: int = 4) -> Tuple[float, float, float]:
    """Return (raw_gbps, effective_gbps, encoding_efficiency_pct) for an IB generation and lane width."""
    if generation not in IB_GENERATIONS:
        raise ValueError(f"Unknown IB generation: {generation}")
    if lanes not in (1, 2, 4, 8, 12):
        raise ValueError(f"Unsupported IB lane width: {lanes}x")
    spec = IB_GENERATIONS[generation]
    raw_gbps = round(spec.raw_lane_rate_gbps * lanes, 4)
    if lanes == 4:
        eff_gbps = spec.effective_4x_gbps
    elif lanes == 12:
        eff_gbps = spec.effective_12x_gbps
    else:
        eff_gbps = round(spec.effective_lane_rate_gbps * lanes, 4)
    efficiency_pct = round((spec.data_bits_per_block / spec.total_bits_per_block) * 100.0, 4)
    return raw_gbps, eff_gbps, efficiency_pct


def classify_lid(lid: int) -> str:
    """Classify a 16-bit InfiniBand LID per SCL Ch 5."""
    if not (0 <= lid <= 0xFFFF):
        raise ValueError(f"LID must fit in 16 bits (0..65535), got {lid}")
    if lid == LID_RESERVED:
        return "RESERVED"
    if LID_UNICAST_MIN <= lid <= LID_UNICAST_MAX:
        return "UNICAST"
    if LID_MULTICAST_MIN <= lid <= LID_MULTICAST_MAX:
        return "MULTICAST"
    return "PERMISSIVE"


@dataclass(frozen=True)
class LmcLidRange:
    """LID Mask Control (LMC) range assigned to a port (`Base LID .. Base LID + 2^LMC - 1`)."""

    base_lid: int
    lmc: int
    count: int
    max_lid: int
    lids: Tuple[int, ...]
    alignment_valid: bool


def compute_lmc_lid_range(base_lid: int, lmc: int = 0) -> LmcLidRange:
    """Compute the 2^LMC consecutive LIDs assigned to an end port (SCL Ch 5).

    Per the IBTA specification and SCL Ch 5:
    - LMC is an integer (0..7 in standard 3-bit LMC field; SCL mentions 0..128 conceptually).
    - The lower LMC bits of Base LID must be zero (`(base_lid & ((1 << lmc) - 1)) == 0`),
      except when Base LID is non-zero aligned by SM policy.
    - The port responds to `2^LMC` consecutive LIDs: `base_lid` through `base_lid + 2^LMC - 1`.
    """
    if not (0 <= lmc <= 7):
        raise ValueError(f"LMC must be in 0..7, got {lmc}")
    if classify_lid(base_lid) != "UNICAST":
        raise ValueError(f"base_lid {base_lid:#x} must be in UNICAST range 1..49151")
    count = 1 << lmc
    max_lid = base_lid + count - 1
    if max_lid > LID_UNICAST_MAX:
        raise ValueError(f"LMC range {base_lid}..{max_lid} exceeds unicast limit {LID_UNICAST_MAX}")
    mask = (1 << lmc) - 1
    alignment_valid = (base_lid & mask) == 0
    lids = tuple(range(base_lid, max_lid + 1))
    return LmcLidRange(
        base_lid=base_lid,
        lmc=lmc,
        count=count,
        max_lid=max_lid,
        lids=lids,
        alignment_valid=alignment_valid,
    )


@dataclass(frozen=True)
class IbGid:
    """128-bit InfiniBand Global Identifier (64-bit Subnet Prefix + 64-bit Port GUID)."""

    subnet_prefix: int
    port_guid: int
    scope: str
    ipv6_str: str


def format_ib_gid(port_guid: int, subnet_prefix: int = GID_LINK_LOCAL_PREFIX) -> IbGid:
    """Construct a 128-bit GID from a 64-bit Subnet Prefix and 64-bit PortGUID (SCL Ch 5)."""
    if not (0 <= subnet_prefix <= 0xFFFFFFFFFFFFFFFF):
        raise ValueError("subnet_prefix must be 64-bit unsigned")
    if not (0 <= port_guid <= 0xFFFFFFFFFFFFFFFF):
        raise ValueError("port_guid must be 64-bit unsigned")

    if (subnet_prefix >> 56) == GID_MULTICAST_HIGH_BYTE:
        scope = "MULTICAST"
    elif subnet_prefix == GID_LINK_LOCAL_PREFIX:
        scope = "LINK_LOCAL"
    elif subnet_prefix == GID_SITE_LOCAL_PREFIX:
        scope = "SITE_LOCAL"
    else:
        scope = "GLOBAL"

    val128 = (subnet_prefix << 64) | port_guid
    hextets = [f"{(val128 >> (112 - 16 * i)) & 0xFFFF:04x}" for i in range(8)]
    return IbGid(
        subnet_prefix=subnet_prefix,
        port_guid=port_guid,
        scope=scope,
        ipv6_str=":".join(hextets),
    )


@dataclass(frozen=True)
class DirectedRouteSmp:
    """Directed-route Subnet Management Packet (SMP) state across uninitialized switch hops (SCL Ch 5)."""

    d_bit: int  # 0 = forward (request), 1 = reverse (response)
    hop_count: int
    hop_pointer: int
    initial_path: Tuple[int, ...]
    return_path: Tuple[int, ...]


def simulate_directed_route_smp(
    egress_ports: List[int],
    ingress_ports_on_switches: List[int],
) -> Tuple[DirectedRouteSmp, DirectedRouteSmp]:
    """Simulate a directed-route SMP forward traversal (D=0) and reverse return traversal (D=1) (SCL Ch 5).

    During initial subnet discovery (before LIDs exist, using Permissive LID 0xFFFF on VL15):
    - Forward (D=0): starts at hop_pointer=0, hop_count=N. At each switch hop, the switch routes out
      `initial_path[hop_pointer]`, records the port on which the SMP arrived into `return_path`,
      and increments `hop_pointer` by 1.
    - At target: sets `D=1` (reverse direction) and sends reply back along `return_path`,
      decrementing `hop_pointer` at each switch hop until `hop_pointer == 0`.
    """
    if len(egress_ports) != len(ingress_ports_on_switches):
        raise ValueError("egress_ports and ingress_ports_on_switches must have same length")
    hop_count = len(egress_ports)
    initial_path = (0,) + tuple(egress_ports)
    return_path = [0] * (hop_count + 1)

    hop_pointer = 0
    for step in range(1, hop_count + 1):
        hop_pointer += 1
        return_path[hop_pointer] = ingress_ports_on_switches[step - 1]

    at_target = DirectedRouteSmp(
        d_bit=0,
        hop_count=hop_count,
        hop_pointer=hop_pointer,
        initial_path=initial_path,
        return_path=tuple(return_path),
    )

    # Target flips D=1 and sends back; each switch decrements hop_pointer down to 0
    rev_pointer = hop_pointer
    for _ in range(hop_count):
        rev_pointer -= 1

    returned_to_sm = DirectedRouteSmp(
        d_bit=1,
        hop_count=hop_count,
        hop_pointer=rev_pointer,
        initial_path=initial_path,
        return_path=tuple(return_path),
    )
    return at_target, returned_to_sm


@dataclass(frozen=True)
class PKeyEvaluation:
    """16-bit Partition Key (P_Key) decomposition and peer communication decision (V8 Ch 4)."""

    pkey_a: int
    pkey_b: int
    partition_id_a: int
    partition_id_b: int
    is_full_a: bool
    is_full_b: bool
    can_communicate: bool
    reason: str


def evaluate_pkey_communication(pkey_a: int, pkey_b: int) -> PKeyEvaluation:
    """Evaluate whether two ports with 16-bit P_Keys can communicate (V8 Ch 4 & IBTA Spec).

    - Low 15 bits (`pkey & 0x7FFF`): Partition ID (`0x0000` is invalid).
    - Bit 15 (`pkey & 0x8000`): Membership bit (`1` = Full member, `0` = Limited member).
    - Default partition has ID `0x7FFF` (`0x7FFF` limited, `0xFFFF` full).
    - Rule: Partition IDs must match (`id_a == id_b != 0`) AND at least one peer must be a
      Full member (`is_full_a or is_full_b`). Two limited members (`0x0021` and `0x0021`) cannot talk.
    """
    for val in (pkey_a, pkey_b):
        if not (0 <= val <= 0xFFFF):
            raise ValueError(f"P_Key must be 16-bit unsigned, got {val:#x}")

    id_a = pkey_a & PKEY_ID_MASK
    id_b = pkey_b & PKEY_ID_MASK
    full_a = bool(pkey_a & PKEY_MEMBERSHIP_BIT)
    full_b = bool(pkey_b & PKEY_MEMBERSHIP_BIT)

    if id_a == 0 or id_b == 0:
        return PKeyEvaluation(pkey_a, pkey_b, id_a, id_b, full_a, full_b, False, "INVALID_ZERO_PARTITION_ID")
    if id_a != id_b:
        return PKeyEvaluation(pkey_a, pkey_b, id_a, id_b, full_a, full_b, False, "PARTITION_ID_MISMATCH")
    if not (full_a or full_b):
        return PKeyEvaluation(
            pkey_a, pkey_b, id_a, id_b, full_a, full_b, False, "LIMITED_TO_LIMITED_DENIED"
        )
    return PKeyEvaluation(pkey_a, pkey_b, id_a, id_b, full_a, full_b, True, "ALLOWED")


def encode_ipoib_hardware_address(flags: int, qpn: int, gid: IbGid) -> str:
    """Format the 20-byte IPoIB link-layer hardware address (`flags:1B + QPN:3B + GID:16B`, SCL Ch 5)."""
    if not (0 <= flags <= 0xFF):
        raise ValueError("flags must be 1 byte (0..255)")
    if not (0 <= qpn <= 0xFFFFFF):
        raise ValueError("qpn must be 24-bit (0..0xFFFFFF)")
    b0 = [flags, (qpn >> 16) & 0xFF, (qpn >> 8) & 0xFF, qpn & 0xFF]
    val128 = (gid.subnet_prefix << 64) | gid.port_guid
    gid_bytes = [(val128 >> (120 - 8 * i)) & 0xFF for i in range(16)]
    all_bytes = b0 + gid_bytes
    assert len(all_bytes) == IPOIB_HWADDR_BYTES
    return ":".join(f"{b:02x}" for b in all_bytes)


@dataclass(frozen=True)
class IbFrameOverhead:
    """InfiniBand packet frame header/CRC breakdown (ADC Ch 9 Fig 9-21)."""

    payload_bytes: int
    has_grh: bool
    has_reth: bool
    header_and_crc_bytes: int
    total_wire_bytes: int
    payload_efficiency_pct: float


def compute_ib_frame_overhead(
    payload_bytes: int = 4096,
    has_grh: bool = False,
    has_reth: bool = False,
) -> IbFrameOverhead:
    """Compute native InfiniBand packet header + CRC overhead (ADC Ch 9 Fig 9-21).

    Base intra-subnet IB frame: LRH (8B) + BTH (12B) + Payload + ICRC (4B) + VCRC (2B) = 26B overhead.
    With RDMA Extended Transport Header (RETH, 16B): 42B overhead.
    With Global Routing Header (GRH, 40B, inter-subnet or GID-routed): +40B overhead.
    """
    if payload_bytes <= 0:
        raise ValueError("payload_bytes must be positive")
    overhead = LRH_BYTES + BTH_BYTES + ICRC_BYTES + VCRC_BYTES
    if has_grh:
        overhead += GRH_BYTES
    if has_reth:
        overhead += RETH_BYTES
    total = payload_bytes + overhead
    eff = round((payload_bytes / total) * 100.0, 4)
    return IbFrameOverhead(
        payload_bytes=payload_bytes,
        has_grh=has_grh,
        has_reth=has_reth,
        header_and_crc_bytes=overhead,
        total_wire_bytes=total,
        payload_efficiency_pct=eff,
    )


@dataclass(frozen=True)
class CbfcVlCreditState:
    """Per-VL Credit-Based Flow Control (CBFC) state (ADC Ch 9 Fig 9-22, 64B credit units)."""

    vl: int
    advertised_credits: int
    available_buffer_bytes: int
    packet_bytes: int
    credits_required: int
    can_transmit: bool
    remaining_credits: int


def evaluate_cbfc_vl_transmission(
    vl: int,
    advertised_credits: int,
    packet_bytes: int,
) -> CbfcVlCreditState:
    """Evaluate link-level CBFC credit consumption for a Virtual Lane (ADC Ch 9 Fig 9-22).

    Each credit authorizes 64 bytes (`CBFC_CREDIT_UNIT_BYTES = 64`).
    `VL0..VL14` use CBFC credits; `VL15` is reserved exclusively for SMPs.
    """
    if not (0 <= vl < TOTAL_VIRTUAL_LANES):
        raise ValueError(f"VL must be in 0..15, got {vl}")
    if advertised_credits < 0 or packet_bytes <= 0:
        raise ValueError("advertised_credits >= 0 and packet_bytes > 0 required")
    credits_needed = (packet_bytes + CBFC_CREDIT_UNIT_BYTES - 1) // CBFC_CREDIT_UNIT_BYTES
    can_tx = advertised_credits >= credits_needed
    rem = (advertised_credits - credits_needed) if can_tx else advertised_credits
    return CbfcVlCreditState(
        vl=vl,
        advertised_credits=advertised_credits,
        available_buffer_bytes=advertised_credits * CBFC_CREDIT_UNIT_BYTES,
        packet_bytes=packet_bytes,
        credits_required=credits_needed,
        can_transmit=can_tx,
        remaining_credits=rem,
    )


def diagnose_ib_port_and_fabric_state(
    phys_state: str,
    logical_state: str,
    negotiated_rate_gbps: int,
    design_rate_gbps: int,
    base_lid: int,
    sm_lid: int,
    port_xmit_wait: int = 0,
    symbol_errors: int = 0,
    pkey_match: bool = True,
    first_NonSuccess_cqe: Optional[str] = None,
) -> str:
    """Layered diagnostic decision tree for InfiniBand incidents (V8 Ch 1-4, Ch 12 & Labs 01-04)."""
    if phys_state != "LinkUp":
        return "PHYSICAL_LINK_DOWN_OR_POLLING"
    if logical_state != "Active" or base_lid == 0 or sm_lid == 0:
        return "SM_CONTROL_PLANE_UNINITIALIZED_NO_LID"
    if negotiated_rate_gbps < design_rate_gbps:
        return "DEGRADED_LANE_WIDTH_OR_SPEED"
    if symbol_errors > 0:
        return "PHYSICAL_BER_OR_SYMBOL_ERRORS"
    if not pkey_match:
        return "PKEY_PARTITION_OR_MEMBERSHIP_MISMATCH"
    if first_NonSuccess_cqe is not None:
        return f"VERBS_TRANSPORT_ERROR_{first_NonSuccess_cqe}"
    if port_xmit_wait > 10000:
        return "CREDIT_BACKPRESSURE_CONGESTION_TREE"
    return "HEALTHY_ACTIVE_PATH"
