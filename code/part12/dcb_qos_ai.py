#!/usr/bin/env python3
"""Chapter 12.5 model: Data center bridging and QoS for AI.

Models the end-to-end Data Center Bridging (DCB) and Quality of Service (QoS)
pipeline for AI Ethernet fabrics:
  1. DSCP-to-Traffic-Class / IEEE 802.1p PCP mapping tables and IP ToS byte
     encoding (`(dscp << 2) | ecn`), including standard IETF DSCP codepoints
     (`CS0/DF = 0`, `AF11 = 10`, `AF21 = 18`, `AF31 = 26`, `AF41 = 34`,
     `EF = 46` where `tos 0xb8 >> 2 == 46`, `CS6 = 48`, `CS7 = 56`) and the
     4-class AI Ethernet fabric model (`TC0` Best Effort, `TC1` Infrastructure/Control,
     `TC3` Lossless RoCEv2 Compute, `TC4` Storage/Checkpointing, `TC6` Strict-Priority
     CNP Feedback).
  2. IEEE 802.1Qaz Enhanced Transmission Selection (ETS) bandwidth allocation,
     strict-priority (`strict` / LLQ with rate-cap policing) versus Deficit
     Weighted Round Robin (`dwrr` / CBWFQ work-conserving weight redistribution),
     and starvation analysis when `TC1`/`TC3` (RoCE) runs `strict` without a cap
     over `TC0` (`dwrr`, weight `5`).
  3. IEEE 802.1Qaz Data Center Bridging Exchange (DCBX) over LLDP (`EtherType 0x88CC`,
     IEEE `802.1` OUI `00-80-C2`, subtypes `9` Configuration, `10` Recommendation,
     `11` PFC, `12` Application Priority for RoCEv2 UDP port `4791` selector `2`),
     symmetric (`PFC`) vs asymmetric (`ETS`) `Willing` bit state machine, and
     mismatch detection between host (`lldptool` / `mlnx_qos`) and switch port.
  4. Switch buffer pool carving across lossless RDMA (`TC3` with `XON`, `K_min`,
     `K_max`, `XOFF`, and cable flight-time headroom) and lossy TCP/storage/CNP/control
     traffic classes (`TC0`, `TC4`, `TC6`), demonstrating why enabling PFC on too
     many priorities fragments shared buffer memory.
  5. End-to-end QoS trust boundary and configuration-drift verification across
     host NIC (`ens1f0`), source leaf (`swp4`, `trust: dscp`), spine, and
     destination leaf (`swp19`, `trust: pcp`), reproducing the silent
     misclassification (`rx_prio0_discard = 18,420`, `rx_pfc_prio3 = 0`) and
     the Volume 09 Chapter 6 & Labs 01-04 diagnostic workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# --- IEEE 802.1Q / 802.1Qaz / 802.1Qbb / IETF DiffServ Constants ---
LLDP_ETHERTYPE: int = 0x88CC
LLDP_DEST_MAC: str = "01:80:C2:00:00:0E"
IEEE_8021_OUI: str = "00:80:C2"
DCBX_SUBTYPE_ETS_CONFIG: int = 9
DCBX_SUBTYPE_ETS_RECOMMEND: int = 10
DCBX_SUBTYPE_PFC_CONFIG: int = 11
DCBX_SUBTYPE_APP_PRIORITY: int = 12
DCBX_APP_SELECTOR_UDP_OR_DCCP: int = 2  # IEEE 802.1Qaz selector 2 = TCP/UDP, 3 = UDP/DCCP; Linux dcb/lldptool UDP port 4791
ROCEV2_UDP_PORT: int = 4791
NVME_TCP_PORT: int = 8009

# Standard DSCP values (6-bit field 0..63 in 8-bit IP ToS / Traffic Class byte)
# Binary 6-bit DSCP representations:
#   0 = 000000, 18 = 010010, 24 = 011000, 26 = 011010, 46 = 101110, 48 = 110000, 56 = 111000
# At 400 Gbps, 9000B = 180.0 ns and 64B = 1.28 ns (ratio 180.0 / 1.28 = 140.625x)
DSCP_CS0_DF: int = 0       # Best Effort (000000)
DSCP_AF11: int = 10
DSCP_AF21: int = 18        # Storage / NVMe-o-TCP / Checkpoint data (010010)
DSCP_AF31_ROCE: int = 26   # Standard NVIDIA RoCEv2 data marking -> Priority 3 (011010)
DSCP_AF41: int = 34
DSCP_EF: int = 46          # Expedited Forwarding (101110, tos 0xb8 >> 2 == 46)
DSCP_CS6_CNP: int = 48     # Network Control / RoCEv2 CNP -> Priority 6 (110000)
DSCP_CS7: int = 56         # Network Control (111000)

# IEEE 802.1Qaz Transmission Selection Algorithm (TSA) identifiers
TSA_STRICT_PRIORITY: int = 0   # Strict Priority
TSA_CBSHAPER: int = 1          # Credit-Based Shaper
TSA_ETS_DWRR: int = 2          # Enhanced Transmission Selection (DWRR / WFQ)
TSA_VENDOR_SPECIFIC: int = 255


@dataclass(frozen=True)
class IpTosDecoding:
    """Decoded 8-bit IPv4 ToS / IPv6 Traffic Class byte (`(dscp << 2) | ecn`)."""

    tos_byte: int
    tos_hex: str
    dscp: int
    ecn: int
    ecn_bits: str
    dscp_name: str
    mlnx_dscp_bucket: str


def encode_ip_tos_byte(dscp: int, ecn: int = 2) -> int:
    """Encode a 6-bit DSCP (`0..63`) and 2-bit ECN (`0..3`, default `2` = `ECT(0)` `10`) into an 8-bit ToS byte."""
    if not (0 <= dscp <= 63):
        raise ValueError(f"dscp must be in 0..63, got {dscp}")
    if not (0 <= ecn <= 3):
        raise ValueError(f"ecn must be in 0..3, got {ecn}")
    return (dscp << 2) | ecn


def decode_ip_tos_byte(tos_byte: int) -> IpTosDecoding:
    """Decode an 8-bit IP ToS byte into 6-bit DSCP (`tos_byte >> 2`) and 2-bit ECN (`tos_byte & 0x03`).

    Reproduces Volume 09 Chapter 6 `tcpdump` capture:
      `tos 0xb8` (184) -> `0xb8 >> 2 == 46` (EF), `ecn == 0`.
      `DSCP 26` with `ECT(0)` (`10` = 2) -> `(26 << 2) | 2 == 106` (`0x6a`).
      `DSCP 48` with `ECT(1)` (`01` = 1) -> `(48 << 2) | 1 == 193` (`0xc1`).
    """
    if not (0 <= tos_byte <= 255):
        raise ValueError(f"tos_byte must be in 0..255, got {tos_byte}")
    dscp = (tos_byte >> 2) & 0x3F
    ecn = tos_byte & 0x03
    names = {
        0: "CS0_DF_BEST_EFFORT",
        10: "AF11",
        18: "AF21_STORAGE",
        24: "CS3",
        26: "AF31_ROCE_DATA",
        34: "AF41",
        46: "EF_EXPEDITED_FORWARDING",
        48: "CS6_CNP_CONTROL",
        56: "CS7_NETWORK_CONTROL",
    }
    bucket_start = (dscp // 8) * 8
    bucket_end = bucket_start + 7
    return IpTosDecoding(
        tos_byte=tos_byte,
        tos_hex=f"0x{tos_byte:02x}",
        dscp=dscp,
        ecn=ecn,
        ecn_bits=f"{ecn:02b}",
        dscp_name=names.get(dscp, f"DSCP_{dscp}"),
        mlnx_dscp_bucket=f"{bucket_start}-{bucket_end}",
    )


@dataclass(frozen=True)
class QoSTrafficClassEntry:
    """Single row of an AI Ethernet fabric QoS source-of-truth mapping table."""

    intent: str
    dscp_values: Tuple[int, ...]
    pcp_priority: int
    traffic_class: int
    is_lossless_pfc: bool
    ecn_enabled: bool
    tsa_mode: str  # "strict" or "dwrr"
    ets_weight_pct: int
    strict_rate_cap_gbps: Optional[float]


def build_ai_fabric_qos_model() -> List[QoSTrafficClassEntry]:
    """Return the standard small, explainable AI Ethernet QoS class model (V9 Ch 6 & Handbook 2.19).

    Maps 4 operational workload intents + dedicated CNP feedback across hardware queues:
      - Best Effort (`DSCP 0`, `PCP 0` -> `TC0`, lossy, `dwrr` `10%`)
      - Storage / Checkpointing (`DSCP 18`, `PCP 4` -> `TC4`, lossy TCP/NVMe-o-TCP, `dwrr` `30%`)
      - RoCEv2 AI Compute (`DSCP 26` / `46`, `PCP 3` -> `TC3`, lossless `PFC` + `ECN`, `dwrr` `50%`)
      - Infrastructure / Control (`DSCP 24` / `34`, `PCP 2` -> `TC2`, lossy, `dwrr` `10%`)
      - CNP / Routing Control (`DSCP 48` / `56`, `PCP 6` -> `TC6`, lossy, `strict` priority with rate cap `20 Gbps` on `400G`)
    """
    return [
        QoSTrafficClassEntry(
            intent="Best Effort (Bulk, SSH, Image Pulls)",
            dscp_values=(0, 10),
            pcp_priority=0,
            traffic_class=0,
            is_lossless_pfc=False,
            ecn_enabled=False,
            tsa_mode="dwrr",
            ets_weight_pct=10,
            strict_rate_cap_gbps=None,
        ),
        QoSTrafficClassEntry(
            intent="Infrastructure & Cluster Control (Kubernetes, Monitoring, BGP)",
            dscp_values=(24, 34),
            pcp_priority=2,
            traffic_class=2,
            is_lossless_pfc=False,
            ecn_enabled=False,
            tsa_mode="dwrr",
            ets_weight_pct=10,
            strict_rate_cap_gbps=None,
        ),
        QoSTrafficClassEntry(
            intent="RoCEv2 AI Compute (NCCL Collectives, RDMA Data)",
            dscp_values=(26, 46),
            pcp_priority=3,
            traffic_class=3,
            is_lossless_pfc=True,
            ecn_enabled=True,
            tsa_mode="dwrr",
            ets_weight_pct=50,
            strict_rate_cap_gbps=None,
        ),
        QoSTrafficClassEntry(
            intent="Storage & Checkpointing (NVMe-o-TCP, Parallel FS)",
            dscp_values=(18,),
            pcp_priority=4,
            traffic_class=4,
            is_lossless_pfc=False,
            ecn_enabled=True,
            tsa_mode="dwrr",
            ets_weight_pct=30,
            strict_rate_cap_gbps=None,
        ),
        QoSTrafficClassEntry(
            intent="CNP Feedback & Critical Link Control (RoCEv2 CNP Opcode 0x81)",
            dscp_values=(48, 56),
            pcp_priority=6,
            traffic_class=6,
            is_lossless_pfc=False,
            ecn_enabled=False,
            tsa_mode="strict",
            ets_weight_pct=0,
            strict_rate_cap_gbps=20.0,
        ),
    ]


def build_dscp_to_priority_table(entries: Optional[List[QoSTrafficClassEntry]] = None) -> Dict[int, int]:
    """Map all 64 DSCP codepoints (`0..63`) to 802.1p priority (`0..7`), defaulting unmapped DSCPs to priority `0`."""
    model = entries if entries is not None else build_ai_fabric_qos_model()
    table: Dict[int, int] = {dscp: 0 for dscp in range(64)}
    for entry in model:
        for dscp in entry.dscp_values:
            table[dscp] = entry.pcp_priority
    return table


@dataclass(frozen=True)
class EtsScheduleResult:
    """Bandwidth allocation result under IEEE 802.1Qaz ETS (strict priority + work-conserving DWRR)."""

    line_rate_gbps: float
    strict_allocated_gbps: Dict[int, float]
    strict_dropped_policed_gbps: Dict[int, float]
    dwrr_allocated_gbps: Dict[int, float]
    total_allocated_gbps: Dict[int, float]
    starved_classes: Tuple[int, ...]
    unallocated_link_gbps: float


def simulate_ets_scheduling(
    line_rate_gbps: float,
    tc_configs: List[Tuple[int, str, int, Optional[float]]],
    offered_load_gbps: Dict[int, float],
) -> EtsScheduleResult:
    """Simulate IEEE 802.1Qaz ETS + Strict Priority / LLQ scheduling under contention.

    Args:
      line_rate_gbps: Total egress link capacity (e.g. `400.0` Gbps or `1.024` Mbps in CNPS Ch 8).
      tc_configs: List of `(tc_id, tsa_mode, dwrr_weight, strict_cap_gbps)` tuples.
        - `tsa_mode == "strict"`: served before any `"dwrr"` class. If `strict_cap_gbps` is set
          and the link is congested (total offered load > `line_rate_gbps`), traffic above
          `strict_cap_gbps` is policed/dropped (CNPS Ch 8 LLQ rule); if uncongested, it can pass.
        - `tsa_mode == "dwrr"`: shares remaining capacity after `"strict"` classes in proportion
          to `dwrr_weight` (work-conserving iterative water-filling: unused share is redistributed
          proportionally among backlogged DWRR classes).
      offered_load_gbps: Offered demand per `tc_id`.
    """
    if line_rate_gbps <= 0:
        raise ValueError("line_rate_gbps must be positive")

    total_offered = sum(max(0.0, v) for v in offered_load_gbps.values())
    link_congested = total_offered > line_rate_gbps + 1e-9

    remaining = line_rate_gbps
    strict_alloc: Dict[int, float] = {}
    strict_policed: Dict[int, float] = {}
    dwrr_alloc: Dict[int, float] = {}

    # 1. Serve strict-priority classes in order
    for tc_id, tsa_mode, weight, cap in tc_configs:
        if tsa_mode != "strict":
            continue
        demand = max(0.0, offered_load_gbps.get(tc_id, 0.0))
        if link_congested and cap is not None:
            effective_demand = min(demand, cap)
            policed = max(0.0, demand - effective_demand)
        else:
            effective_demand = demand
            policed = 0.0
        served = min(remaining, effective_demand)
        strict_alloc[tc_id] = round(served, 6)
        strict_policed[tc_id] = round(policed, 6)
        remaining = max(0.0, remaining - served)

    # 2. Serve DWRR / ETS classes work-conservingly across remaining capacity
    dwrr_classes = [(tc_id, weight) for tc_id, tsa_mode, weight, _ in tc_configs if tsa_mode == "dwrr"]
    for tc_id, _ in dwrr_classes:
        dwrr_alloc[tc_id] = 0.0

    active = {
        tc_id: weight
        for tc_id, weight in dwrr_classes
        if offered_load_gbps.get(tc_id, 0.0) > 0.0 and weight > 0
    }

    while remaining > 1e-9 and active:
        weight_sum = sum(active.values())
        if weight_sum <= 0:
            break
        progress = False
        satisfied: List[int] = []
        for tc_id, weight in list(active.items()):
            share = remaining * (weight / weight_sum)
            needed = offered_load_gbps[tc_id] - dwrr_alloc[tc_id]
            if needed <= share + 1e-9:
                dwrr_alloc[tc_id] += needed
                remaining = max(0.0, remaining - needed)
                satisfied.append(tc_id)
                progress = True
        if satisfied:
            for tc_id in satisfied:
                active.pop(tc_id, None)
        else:
            for tc_id, weight in active.items():
                share = remaining * (weight / weight_sum)
                dwrr_alloc[tc_id] += share
            remaining = 0.0
            break

    dwrr_alloc = {k: round(v, 6) for k, v in dwrr_alloc.items()}
    total_alloc = {**strict_alloc, **dwrr_alloc}
    starved = tuple(
        sorted(
            tc_id
            for tc_id, demand in offered_load_gbps.items()
            if demand > 0.0 and total_alloc.get(tc_id, 0.0) == 0.0
        )
    )
    return EtsScheduleResult(
        line_rate_gbps=line_rate_gbps,
        strict_allocated_gbps=strict_alloc,
        strict_dropped_policed_gbps=strict_policed,
        dwrr_allocated_gbps=dwrr_alloc,
        total_allocated_gbps=total_alloc,
        starved_classes=starved,
        unallocated_link_gbps=round(remaining, 6),
    )


@dataclass(frozen=True)
class DcbxTlvEndpointProfile:
    """IEEE 802.1Qaz DCBX TLV configuration advertised by a host NIC or switch port over LLDP."""

    role: str  # "host" or "switch"
    ets_willing: bool
    pfc_willing: bool
    pfc_enabled_priorities: Tuple[int, ...]
    pfc_mbc: bool  # MACsec Bypass Capability
    prio_to_tc: Dict[int, int]
    tc_ets_weights: Dict[int, int]
    tc_tsa: Dict[int, str]
    app_priority_table: Dict[Tuple[int, int], int]  # (selector, protocol_id) -> priority
    trust_mode: str  # "dscp" or "pcp"


@dataclass(frozen=True)
class DcbxNegotiationOutcome:
    """Result of IEEE 802.1Qaz DCBX TLV exchange and operational mismatch audit on a link."""

    operational_state_source: str  # "SWITCH_PEER", "HOST_LOCAL", "BOTH_LOCAL_STATIC", or "CONFLICT_BOTH_WILLING"
    pfc_operational_host: Tuple[int, ...]
    pfc_operational_switch: Tuple[int, ...]
    pfc_matched: bool
    ets_weights_matched: bool
    app_roce_priority_matched: bool
    trust_mode_matched: bool
    mismatches: Tuple[str, ...]
    is_healthy: bool


def evaluate_dcbx_negotiation(
    host: DcbxTlvEndpointProfile,
    switch: DcbxTlvEndpointProfile,
) -> DcbxNegotiationOutcome:
    """Evaluate IEEE 802.1Qaz DCBX TLV negotiation between a host NIC and leaf switch port.

    In IEEE 802.1Qaz DCBX:
      - If `host.willing == True` and `switch.willing == False`: the host adopts the
        switch's advertised configuration (`SWITCH_PEER`).
      - If `host.willing == False` and `switch.willing == True`: the switch adopts the
        host's configuration (`HOST_LOCAL`).
      - If `host.willing == False` and `switch.willing == False`: neither side accepts peer
        overrides (`BOTH_LOCAL_STATIC`, common in automated AI clusters); both local static
        profiles must match exactly or a silent QoS mismatch occurs.
      - If `host.willing == True` and `switch.willing == True`: symmetric/asymmetric resolution
        can be ambiguous across vendors (`CONFLICT_BOTH_WILLING`); flagged if configs differ.
    """
    if host.pfc_willing and not switch.pfc_willing:
        source = "SWITCH_PEER"
        op_pfc_host = switch.pfc_enabled_priorities
        op_pfc_switch = switch.pfc_enabled_priorities
    elif not host.pfc_willing and switch.pfc_willing:
        source = "HOST_LOCAL"
        op_pfc_host = host.pfc_enabled_priorities
        op_pfc_switch = host.pfc_enabled_priorities
    elif not host.pfc_willing and not switch.pfc_willing:
        source = "BOTH_LOCAL_STATIC"
        op_pfc_host = host.pfc_enabled_priorities
        op_pfc_switch = switch.pfc_enabled_priorities
    else:
        source = "CONFLICT_BOTH_WILLING"
        op_pfc_host = host.pfc_enabled_priorities
        op_pfc_switch = switch.pfc_enabled_priorities

    if host.ets_willing and not switch.ets_willing:
        op_ets_host = switch.tc_ets_weights
        op_ets_switch = switch.tc_ets_weights
    elif not host.ets_willing and switch.ets_willing:
        op_ets_host = host.tc_ets_weights
        op_ets_switch = host.tc_ets_weights
    else:
        op_ets_host = host.tc_ets_weights
        op_ets_switch = switch.tc_ets_weights

    mismatches: List[str] = []
    pfc_ok = tuple(sorted(op_pfc_host)) == tuple(sorted(op_pfc_switch))
    if not pfc_ok:
        mismatches.append(f"PFC_MISMATCH: host={op_pfc_host} vs switch={op_pfc_switch}")

    ets_ok = op_ets_host == op_ets_switch
    if not ets_ok:
        mismatches.append(f"ETS_WEIGHT_MISMATCH: host={op_ets_host} vs switch={op_ets_switch}")

    if source == "CONFLICT_BOTH_WILLING":
        mismatches.append("WILLING_BIT_CONFLICT: both host and switch advertise Willing=1")

    roce_key = (DCBX_APP_SELECTOR_UDP_OR_DCCP, ROCEV2_UDP_PORT)
    host_roce_prio = host.app_priority_table.get(roce_key)
    sw_roce_prio = switch.app_priority_table.get(roce_key)
    if host.pfc_willing and not switch.pfc_willing and sw_roce_prio is not None:
        host_roce_prio = sw_roce_prio
    app_ok = host_roce_prio == sw_roce_prio and host_roce_prio in op_pfc_switch
    if not app_ok:
        mismatches.append(
            f"APP_TLV_ROCE_4791_MISMATCH: host_prio={host_roce_prio}, switch_prio={sw_roce_prio}, lossless={op_pfc_switch}"
        )

    trust_ok = host.trust_mode == switch.trust_mode
    if not trust_ok:
        mismatches.append(f"TRUST_MODE_MISMATCH: host={host.trust_mode} vs switch={switch.trust_mode}")

    return DcbxNegotiationOutcome(
        operational_state_source=source,
        pfc_operational_host=op_pfc_host,
        pfc_operational_switch=op_pfc_switch,
        pfc_matched=pfc_ok,
        ets_weights_matched=ets_ok,
        app_roce_priority_matched=app_ok,
        trust_mode_matched=trust_ok,
        mismatches=tuple(mismatches),
        is_healthy=len(mismatches) == 0,
    )


@dataclass(frozen=True)
class BufferPoolCarvingPlan:
    """Switch port / ASIC buffer carving across lossless RDMA, headroom, and lossy pools."""

    total_port_buffer_bytes: int
    lossless_priorities: Tuple[int, ...]
    per_lossless_prio_reserved_bytes: int
    per_lossless_prio_xoff_bytes: int
    per_lossless_prio_xon_bytes: int
    per_lossless_prio_headroom_bytes: int
    total_lossless_reserved_bytes: int
    remaining_lossy_shared_bytes: int
    lossless_share_pct: float
    lossy_share_pct: float
    is_valid_carving: bool
    finding: str


def evaluate_buffer_pool_carving(
    total_port_buffer_bytes: int = 262_144,
    lossless_priorities: Tuple[int, ...] = (3,),
    per_lossless_prio_reserved_bytes: int = 65_536,
    xoff_bytes: int = 49_152,
    xon_bytes: int = 32_768,
    min_required_headroom_bytes: int = 16_384,
    min_required_lossy_pool_pct: float = 20.0,
) -> BufferPoolCarvingPlan:
    """Evaluate switch port buffer carving across lossless (`PFC`) and lossy traffic classes.

    Defaults match Volume 09 Chapter 4 (`mlnx_qos -i swp12`):
      - `total_port_buffer_bytes = 262,144` B (`256 KiB`)
      - `1` lossless priority (`Priority 3`): `65,536` B (`25.0%` of port buffer),
        with `XOFF = 49,152` B (`75%`), `XON = 32,768` B (`50%`), `headroom = 16,384` B (`25%`),
        leaving `196,608` B (`75.0%`) for lossy `TC0`/`TC2`/`TC4`/`TC6` traffic.
      - If an operator enables PFC on `4` priorities (`4 * 65,536 = 262,144` B), `100.0%` of the
        port buffer is locked in lossless reservations and `0` B (`0.0%`) remains for lossy
        TCP/storage/control/CNP queues (`BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES`).
    """
    num_lossless = len(lossless_priorities)
    headroom = per_lossless_prio_reserved_bytes - xoff_bytes
    total_lossless = num_lossless * per_lossless_prio_reserved_bytes
    remaining_lossy = total_port_buffer_bytes - total_lossless
    lossless_pct = round((total_lossless / total_port_buffer_bytes) * 100.0, 2)
    lossy_pct = round((remaining_lossy / total_port_buffer_bytes) * 100.0, 2)

    if headroom < min_required_headroom_bytes:
        valid = False
        finding = f"INSUFFICIENT_HEADROOM: {headroom} B < required {min_required_headroom_bytes} B"
    elif xon_bytes >= xoff_bytes:
        valid = False
        finding = f"INVALID_HYSTERESIS: XON ({xon_bytes} B) >= XOFF ({xoff_bytes} B)"
    elif remaining_lossy < 0 or lossy_pct < min_required_lossy_pool_pct:
        valid = False
        finding = (
            f"BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES: {num_lossless} lossless classes consume "
            f"{lossless_pct:.1f}% ({total_lossless} B), leaving only {lossy_pct:.1f}% ({remaining_lossy} B) for lossy TCs"
        )
    else:
        valid = True
        finding = (
            f"HEALTHY_BUFFER_CARVING: {num_lossless} lossless class(es) use {lossless_pct:.1f}% "
            f"({total_lossless} B); {lossy_pct:.1f}% ({remaining_lossy} B) remains for lossy TCs"
        )

    return BufferPoolCarvingPlan(
        total_port_buffer_bytes=total_port_buffer_bytes,
        lossless_priorities=lossless_priorities,
        per_lossless_prio_reserved_bytes=per_lossless_prio_reserved_bytes,
        per_lossless_prio_xoff_bytes=xoff_bytes,
        per_lossless_prio_xon_bytes=xon_bytes,
        per_lossless_prio_headroom_bytes=headroom,
        total_lossless_reserved_bytes=total_lossless,
        remaining_lossy_shared_bytes=remaining_lossy,
        lossless_share_pct=lossless_pct,
        lossy_share_pct=lossy_pct,
        is_valid_carving=valid,
        finding=finding,
    )


@dataclass(frozen=True)
class HopQoSConfig:
    """Per-hop classification, trust boundary, and queue policy along an Ethernet path."""

    hop_name: str
    trust_mode: str  # "dscp", "pcp", or "untrusted_rewrite_zero"
    dscp_to_prio: Dict[int, int]
    pcp_to_prio: Dict[int, int]
    pfc_enabled_prios: Tuple[int, ...]
    ecn_enabled_prios: Tuple[int, ...]


@dataclass(frozen=True)
class HopPacketClassification:
    """Observed packet marking, internal priority, and protection state at one hop."""

    hop_name: str
    trust_mode: str
    ingress_dscp: int
    ingress_pcp: Optional[int]
    resolved_priority: int
    is_lossless_pfc: bool
    is_ecn_protected: bool
    matches_expected_priority: bool


@dataclass(frozen=True)
class EndToEndQoSTrace:
    """Hop-by-hop trace of a packet across host, leaf, spine, and destination leaf."""

    expected_priority: int
    hop_results: Tuple[HopPacketClassification, ...]
    first_drift_hop: Optional[str]
    end_to_end_lossless: bool
    diagnosis: str


def trace_end_to_end_qos_path(
    initial_dscp: int,
    initial_pcp: Optional[int],
    expected_priority: int,
    hops: List[HopQoSConfig],
) -> EndToEndQoSTrace:
    """Trace packet classification hop by hop across L2/L3 boundaries (V9 Ch 6 drift scenario).

    Reproduces the Volume 09 Chapter 6 incident:
      - Host emits routed IP/UDP port `4791` packet with `tos 0xb8` (`DSCP 46` or `DSCP 26`)
        and `initial_pcp = None` (untagged routed L3 frame).
      - `swp4` (source leaf) has `trust_mode = "dscp"` -> maps `DSCP 46` (`40-47` bucket) to
        `Priority 3` (lossless `PFC` + `ECN`).
      - `swp19` (destination leaf) has drifted to `trust_mode = "pcp"` -> ignores DSCP; since the
        routed IP packet has no `802.1Q` VLAN tag (`initial_pcp = None`), it falls through to
        `Priority 0` (lossy best-effort), causing `rx_prio0_discard = 18,420` while `rx_pfc_prio3 = 0`.
    """
    current_dscp = initial_dscp
    current_pcp = initial_pcp
    results: List[HopPacketClassification] = []
    first_drift: Optional[str] = None

    for hop in hops:
        if hop.trust_mode == "untrusted_rewrite_zero":
            current_dscp = 0
            current_pcp = 0
            prio = 0
        elif hop.trust_mode == "dscp":
            prio = hop.dscp_to_prio.get(current_dscp, 0)
        elif hop.trust_mode == "pcp":
            if current_pcp is None:
                prio = 0
            else:
                prio = hop.pcp_to_prio.get(current_pcp, 0)
        else:
            raise ValueError(f"Unknown trust_mode: {hop.trust_mode}")

        lossless = prio in hop.pfc_enabled_prios
        ecn_ok = prio in hop.ecn_enabled_prios
        matches = prio == expected_priority and lossless and ecn_ok
        if not matches and first_drift is None:
            first_drift = hop.hop_name

        results.append(
            HopPacketClassification(
                hop_name=hop.hop_name,
                trust_mode=hop.trust_mode,
                ingress_dscp=current_dscp,
                ingress_pcp=current_pcp,
                resolved_priority=prio,
                is_lossless_pfc=lossless,
                is_ecn_protected=ecn_ok,
                matches_expected_priority=matches,
            )
        )

    all_ok = first_drift is None
    if all_ok:
        diag = f"END_TO_END_CONTRACT_VERIFIED: all {len(hops)} hops classify into lossless Priority {expected_priority}"
    else:
        bad_hop = next(r for r in results if r.hop_name == first_drift)
        diag = (
            f"QOS_DRIFT_AT_{first_drift}: trust_mode={bad_hop.trust_mode} mapped packet to "
            f"Priority {bad_hop.resolved_priority} (lossless={bad_hop.is_lossless_pfc}, ecn={bad_hop.is_ecn_protected}) "
            f"instead of expected Priority {expected_priority}"
        )

    return EndToEndQoSTrace(
        expected_priority=expected_priority,
        hop_results=tuple(results),
        first_drift_hop=first_drift,
        end_to_end_lossless=all_ok,
        diagnosis=diag,
    )
