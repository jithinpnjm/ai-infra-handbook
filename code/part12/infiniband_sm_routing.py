#!/usr/bin/env python3
"""Chapter 12.7: InfiniBand subnet manager, routing, topologies and rails.

Pure-stdlib deterministic models for:
  1. OpenSM Master/Standby election (`priority` 0..15, lowest Port/SM GUID tie-breaker,
     `sminfo` states 0..3, activity-count liveness, and split-authority detection).
  2. InfiniBand physical & logical port state machine (`Down -> Initialize -> Armed -> Active`,
     where `Armed -> Active` requires Subnet Manager SMP configuration) and Directed Route
     SMP hop-pointer traversal (`D=0` forward, `D=1` return).
  3. Subnet addressing limits (`49,151` unicast LIDs `1..0xBFFF`, multicast `0xC000..0xFFFE`,
     permissive `0xFFFF`, `LMC` multipath LID ranges `2^LMC`) and Linear Forwarding Table
     (`LFT`) programming + uplink balance auditing (`PortXmitData` 4-octet words).
  4. Routing engine selector and validator (`minhop`, `updn`, `ftree`, `dor`, `dfsssp`).
  5. Fat-Tree / Folded Clos radix, oversubscription (`1:1` vs `2:1`..`7:1`), AllReduce step
     time impact, and 3-stage vs 5-stage scale calculators (`256` to `32,768` GPUs).
  6. Rail-Optimized Design (`ROD`), Rail-Only, Rail-Unified Design (`RUD`), Multi-Planar
     (`4 x 200G` breakout from `800G`), and AI IP fabric routing protocol comparison
     (`eBGP` unnumbered `RFC 5549`/`RFC 7938`, `BGP DPF`, `RIFT` `RFC 9692`, `IS-IS`
     Flex Algo `RFC 9350`/`RFC 9502`, and `SRv6` `uSID`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# InfiniBand Subnet & OpenSM Protocol Constants (SCL Ch 5, V8 Ch 5-6)
# ---------------------------------------------------------------------------
IB_RESERVED_LID: int = 0x0000
IB_MIN_UNICAST_LID: int = 0x0001
IB_MAX_UNICAST_LID: int = 0xBFFF  # 49,151 (2^15 + 2^14 - 1)
IB_MIN_MULTICAST_LID: int = 0xC000  # 49,152
IB_MAX_MULTICAST_LID: int = 0xFFFE  # 65,534
IB_PERMISSIVE_LID: int = 0xFFFF  # 65,535 (Directed Route SMPs)
IB_DEFAULT_GID_PREFIX: int = 0xFE80000000000000
IB_SITE_LOCAL_GID_PREFIX: int = 0xFEC0000000000000
IB_SMP_VL: int = 15  # VL15 dedicated to Subnet Management Packets
IB_UNROUTED_PORT: int = 0xFF  # 255 in LFT dump indicates unrouted LID
IB_TRAP_LINK_STATE_CHANGE: int = 128  # OpenSM Trap 128 (link state change)
PERFQUERY_OCTETS_PER_WORD: int = 4  # PortXmitData / PortRcvData count 4-byte words

# OpenSM priority & SMInfo states
SM_MIN_PRIORITY: int = 0
SM_MAX_PRIORITY: int = 15
SMINFO_NOTACTIVE: int = 0
SMINFO_DISCOVERING: int = 1
SMINFO_STANDBY: int = 2
SMINFO_MASTER: int = 3

# Logical Port States (IB Architecture Spec & ibstat / ibstatus)
PORT_STATE_DOWN: int = 1
PORT_STATE_INITIALIZE: int = 2
PORT_STATE_ARMED: int = 3
PORT_STATE_ACTIVE: int = 4

# Physical Port States
PHYS_STATE_DISABLED: int = 3
PHYS_STATE_POLLING: int = 2
PHYS_STATE_LINKUP: int = 5

# AI Fabric IP Routing Constants (ADC Ch 8)
BGP_TCP_PORT: int = 179
BGP_EXT_NEXTHOP_CAP_CODE: int = 5
BGP_EXT_NEXTHOP_CAP_LEN: int = 6
BGP_AFI_IPV4: int = 1
BGP_SAFI_UNICAST: int = 1
BGP_NH_AFI_IPV6: int = 2
ASN_PRIVATE_16BIT_MIN: int = 64512
ASN_PRIVATE_16BIT_MAX: int = 65535
ASN_PRIVATE_32BIT_MIN: int = 4200000000
ASN_PRIVATE_32BIT_MAX: int = 4294967294
RIFT_MIN_SWITCH_SCALE: int = 1000
ISIS_MAX_SWITCH_SCALE: int = 2500
SRV6_SID_BITS: int = 128
SRV6_USID_BITS: int = 16
TOPOGRAPH_DEFAULT_PORT: int = 49021


@dataclass(frozen=True)
class CandidateSM:
    """A Subnet Manager instance participating in master election."""

    name: str
    guid: int
    lid: int
    priority: int
    state: int = SMINFO_DISCOVERING
    activity_count: int = 0


@dataclass(frozen=True)
class ElectionResult:
    """Outcome of OpenSM master election across a subnet."""

    master: CandidateSM
    standbys: Tuple[CandidateSM, ...]
    won_by_guid_tiebreaker: bool
    roles_by_name: Dict[str, str]


def elect_master_sm(candidates: Sequence[CandidateSM]) -> ElectionResult:
    """Elect the authoritative Master SM.

    Rule:
      1. Highest priority (`0..15`) wins.
      2. If two or more SMs share the highest priority, the SM with the
         **lowest** Port/SM GUID wins the tie-breaker.
    """
    if not candidates:
        raise ValueError("At least one candidate SM is required")
    for c in candidates:
        if not (SM_MIN_PRIORITY <= c.priority <= SM_MAX_PRIORITY):
            raise ValueError(f"SM priority {c.priority} outside valid range 0..15")

    ordered = sorted(candidates, key=lambda c: (-c.priority, c.guid))
    winner = CandidateSM(
        name=ordered[0].name,
        guid=ordered[0].guid,
        lid=ordered[0].lid,
        priority=ordered[0].priority,
        state=SMINFO_MASTER,
        activity_count=ordered[0].activity_count,
    )
    standbys = tuple(
        CandidateSM(
            name=c.name,
            guid=c.guid,
            lid=c.lid,
            priority=c.priority,
            state=SMINFO_STANDBY,
            activity_count=c.activity_count,
        )
        for c in ordered[1:]
    )
    top_prio_count = sum(1 for c in candidates if c.priority == winner.priority)
    roles = {winner.name: "SMINFO_MASTER"}
    for s in standbys:
        roles[s.name] = "SMINFO_STANDBY"
    return ElectionResult(
        master=winner,
        standbys=standbys,
        won_by_guid_tiebreaker=(top_prio_count > 1),
        roles_by_name=roles,
    )


def audit_sm_authority(
    observed_sms: Sequence[CandidateSM],
    previous_master_activity: Optional[int] = None,
) -> str:
    """Classify subnet control-plane authority from `sminfo` observations."""
    masters = [sm for sm in observed_sms if sm.state == SMINFO_MASTER]
    if len(masters) == 0:
        return "ZERO_MASTERS_PORTS_STUCK_INITIALIZING"
    if len(masters) > 1:
        return "SPLIT_AUTHORITY_MULTIPLE_MASTERS"
    master = masters[0]
    if previous_master_activity is not None and master.activity_count <= previous_master_activity:
        return "FROZEN_MASTER_ACTIVITY_COUNT"
    return "HEALTHY_SINGLE_MASTER"


@dataclass(frozen=True)
class PortStateTransitionResult:
    """State of an InfiniBand port across physical and SM lifecycle events."""

    phys_state_code: int
    phys_state_name: str
    logical_state_code: int
    logical_state_name: str
    base_lid: int
    sm_lid: int
    can_carry_smp_vl15: bool
    can_carry_user_rdma_vl0_14: bool


def evaluate_ib_port_state(
    phys_link_up: bool,
    sm_discovered_and_assigned_lid: bool,
    sm_programmed_lft_and_activated: bool,
    assigned_lid: int = 12,
    sm_lid: int = 1,
) -> PortStateTransitionResult:
    """Evaluate the IB port state machine (`Down -> Initialize -> Armed -> Active`).

    - Without physical signal negotiation (`LinkUp`), the port is `Down` (1).
    - Once physical lanes lock (`LinkUp`, code 5), the port enters `Initialize` (2):
      only VL15 Subnet Management Packets (SMPs) can pass; user QPs cannot transmit.
    - After the SM assigns a Base LID, SM LID, and P_Key table via SMPs, the port
      transitions to `Armed` (3): VL15 works, user traffic still waits for activation.
    - Only after the SM programs switch forwarding tables (LFTs) and sends `PortInfo`
      setting `PortState=Active` (4) can user RDMA traffic flow over VL0..VL14.
    """
    if not phys_link_up:
        return PortStateTransitionResult(
            phys_state_code=PHYS_STATE_POLLING,
            phys_state_name="Polling",
            logical_state_code=PORT_STATE_DOWN,
            logical_state_name="Down",
            base_lid=0,
            sm_lid=0,
            can_carry_smp_vl15=False,
            can_carry_user_rdma_vl0_14=False,
        )
    if not sm_discovered_and_assigned_lid:
        return PortStateTransitionResult(
            phys_state_code=PHYS_STATE_LINKUP,
            phys_state_name="LinkUp",
            logical_state_code=PORT_STATE_INITIALIZE,
            logical_state_name="Initialize",
            base_lid=0,
            sm_lid=0,
            can_carry_smp_vl15=True,
            can_carry_user_rdma_vl0_14=False,
        )
    if not sm_programmed_lft_and_activated:
        return PortStateTransitionResult(
            phys_state_code=PHYS_STATE_LINKUP,
            phys_state_name="LinkUp",
            logical_state_code=PORT_STATE_ARMED,
            logical_state_name="Armed",
            base_lid=assigned_lid,
            sm_lid=sm_lid,
            can_carry_smp_vl15=True,
            can_carry_user_rdma_vl0_14=False,
        )
    return PortStateTransitionResult(
        phys_state_code=PHYS_STATE_LINKUP,
        phys_state_name="LinkUp",
        logical_state_code=PORT_STATE_ACTIVE,
        logical_state_name="Active",
        base_lid=assigned_lid,
        sm_lid=sm_lid,
        can_carry_smp_vl15=True,
        can_carry_user_rdma_vl0_14=True,
    )


@dataclass(frozen=True)
class DirectedRouteTrace:
    """Step-by-step Directed Route SMP (`DLID=0xFFFF`) traversal."""

    hop_count: int
    initial_path: Tuple[int, ...]
    return_path: Tuple[int, ...]
    forward_hop_pointers: Tuple[int, ...]
    reverse_hop_pointers: Tuple[int, ...]


def simulate_directed_route_smp(
    egress_ports: Sequence[int],
    ingress_ports_at_hops: Sequence[int],
) -> DirectedRouteTrace:
    """Simulate a pure Directed Route SMP (`DLID = 0xFFFF`, `SLID = 0xFFFF`) from SCL Ch 5.

    - Forward (`D = 0`): `hop_pointer` increments from `1` to `hop_count`, recording each
      receiving switch's ingress port into `return_path`.
    - Reverse (`D = 1`): target sets `D = 1`; switches follow `return_path` in reverse
      while decrementing `hop_pointer` back to `0`.
    """
    if len(egress_ports) != len(ingress_ports_at_hops):
        raise ValueError("egress_ports and ingress_ports_at_hops must have equal length")
    hop_count = len(egress_ports)
    initial_path = (0,) + tuple(egress_ports)
    return_path = [0] * (hop_count + 1)
    fwd_ptrs: List[int] = []
    for step in range(1, hop_count + 1):
        fwd_ptrs.append(step)
        return_path[step] = ingress_ports_at_hops[step - 1]
    rev_ptrs = tuple(range(hop_count, 0, -1))
    return DirectedRouteTrace(
        hop_count=hop_count,
        initial_path=initial_path,
        return_path=tuple(return_path),
        forward_hop_pointers=tuple(fwd_ptrs),
        reverse_hop_pointers=rev_ptrs,
    )


def compute_lmc_lid_block(base_lid: int, lmc: int) -> Tuple[int, ...]:
    """Compute the block of `2^LMC` consecutive LIDs assigned to a port (`SCL Ch 5`).

    - `base_lid` must have its lower `lmc` bits set to zero (`base_lid % (2**lmc) == 0`)
      in strict alignment, or spans `base_lid .. base_lid + 2^lmc - 1`.
    """
    if not (0 <= lmc <= 7):
        raise ValueError("LMC must be in 0..7")
    count = 1 << lmc
    if base_lid < IB_MIN_UNICAST_LID or (base_lid + count - 1) > IB_MAX_UNICAST_LID:
        raise ValueError("LID block outside valid unicast range 1..0xBFFF")
    return tuple(range(base_lid, base_lid + count))


@dataclass(frozen=True)
class LFTProgramResult:
    """Programmed Linear Forwarding Table (`DLID -> egress port`) for a leaf switch."""

    switch_name: str
    lft: Dict[int, int]
    uplink_lid_counts: Dict[int, int]
    max_to_min_ratio: float
    is_balanced: bool


def program_leaf_lft(
    switch_name: str,
    local_lid_to_downlink: Dict[int, int],
    remote_destination_lids: Sequence[int],
    active_uplink_ports: Sequence[int],
    policy: str = "ftree_round_robin",
) -> LFTProgramResult:
    """Program a switch Linear Forwarding Table (`LFT`) and evaluate uplink balance.

    - `ftree_round_robin`: spreads remote destination LIDs evenly across all active uplinks.
    - `static_naive`: pins most destinations onto the first two uplinks (reproducing the
      20:1 hot-uplink imbalance in V8 Ch 6 Scenario 1).
    """
    if not active_uplink_ports:
        raise ValueError("At least one uplink port is required")
    lft: Dict[int, int] = dict(local_lid_to_downlink)
    uplink_counts: Dict[int, int] = {p: 0 for p in active_uplink_ports}

    for idx, dlid in enumerate(remote_destination_lids):
        if policy == "ftree_round_robin":
            out_port = active_uplink_ports[idx % len(active_uplink_ports)]
        elif policy == "static_naive":
            # Concentrate 20 out of every 21 destinations onto the first half of uplinks
            half = max(1, len(active_uplink_ports) // 2)
            if (idx % 21) < 20:
                out_port = active_uplink_ports[idx % half]
            else:
                out_port = active_uplink_ports[half + (idx % max(1, len(active_uplink_ports) - half))]
        else:
            raise ValueError(f"Unknown LFT policy: {policy}")
        lft[dlid] = out_port
        uplink_counts[out_port] += 1

    counts = list(uplink_counts.values())
    min_c = min(counts) if counts else 0
    max_c = max(counts) if counts else 0
    ratio = (max_c / min_c) if min_c > 0 else float("inf")
    return LFTProgramResult(
        switch_name=switch_name,
        lft=lft,
        uplink_lid_counts=uplink_counts,
        max_to_min_ratio=round(ratio, 2),
        is_balanced=(ratio <= 1.25),
    )


@dataclass(frozen=True)
class UplinkCounterAudit:
    """Result of auditing `perfquery` `PortXmitData` across leaf uplinks (`V8 Ch 6`)."""

    bytes_by_port: Dict[int, int]
    words_by_port: Dict[int, int]
    imbalance_ratio: float
    hot_ports: Tuple[int, ...]
    idle_ports: Tuple[int, ...]
    diagnosis: str


def audit_uplink_port_xmit_bytes(bytes_by_port: Dict[int, int]) -> UplinkCounterAudit:
    """Convert byte deltas to 4-octet `PortXmitData` words and detect route concentration."""
    words_by_port = {p: b // PERFQUERY_OCTETS_PER_WORD for p, b in bytes_by_port.items()}
    vals = list(bytes_by_port.values())
    max_b = max(vals)
    min_b = max(1, min(vals))
    ratio = round(max_b / min_b, 2)
    median_b = sum(vals) / len(vals)
    hot = tuple(sorted(p for p, b in bytes_by_port.items() if b > 1.3 * median_b))
    idle = tuple(sorted(p for p, b in bytes_by_port.items() if b < 0.5 * median_b))
    diag = (
        "ROUTE_OR_LID_CONCENTRATION_HOT_UPLINKS"
        if ratio >= 2.0
        else "BALANCED_UPLINK_DISTRIBUTION"
    )
    return UplinkCounterAudit(
        bytes_by_port=bytes_by_port,
        words_by_port=words_by_port,
        imbalance_ratio=ratio,
        hot_ports=hot,
        idle_ports=idle,
        diagnosis=diag,
    )


@dataclass(frozen=True)
class RoutingEngineProfile:
    """Capabilities and constraints of an OpenSM routing engine."""

    engine_name: str
    target_topology: str
    loop_avoidance_mechanism: str
    min_vls_required: int
    supports_adaptive_routing_variant: Optional[str]


ROUTING_ENGINES: Dict[str, RoutingEngineProfile] = {
    "minhop": RoutingEngineProfile(
        engine_name="minhop",
        target_topology="Small or regular single-switch / simple tree subnets",
        loop_avoidance_mechanism="Shortest hop count only (no credit-loop prevention on cyclic graphs)",
        min_vls_required=1,
        supports_adaptive_routing_variant=None,
    ),
    "updn": RoutingEngineProfile(
        engine_name="updn",
        target_topology="Irregular trees or degraded Clos fabrics with designated root switches",
        loop_avoidance_mechanism="Prohibits Down->Up turns below root nodes to break credit loops",
        min_vls_required=1,
        supports_adaptive_routing_variant="ar_updn",
    ),
    "ftree": RoutingEngineProfile(
        engine_name="ftree",
        target_topology="Symmetric or asymmetric Fat-Tree / Folded Clos AI clusters",
        loop_avoidance_mechanism="Upward then downward stage indexing with deterministic port spreading",
        min_vls_required=1,
        supports_adaptive_routing_variant="ar_ftree",
    ),
    "dor": RoutingEngineProfile(
        engine_name="dor",
        target_topology="1D, 2D, or 3D Torus and Mesh interconnects",
        loop_avoidance_mechanism="Dimension-Ordered Routing (X->Y->Z) + dateline VL split on wrap links",
        min_vls_required=2,
        supports_adaptive_routing_variant="ar_dor",
    ),
    "dfsssp": RoutingEngineProfile(
        engine_name="dfsssp",
        target_topology="Arbitrary / irregular graphs and Dragonfly-like topologies",
        loop_avoidance_mechanism="Deadlock-Free Single-Source Shortest-Path using Virtual Lane transitions",
        min_vls_required=2,
        supports_adaptive_routing_variant=None,
    ),
}


def validate_updn_turn_sequence(steps: Sequence[str]) -> bool:
    """Validate an `updn` path (`UP` steps followed by `DOWN` steps; `DOWN -> UP` is illegal)."""
    seen_down = False
    for step in steps:
        s = step.upper()
        if s not in ("UP", "DOWN"):
            raise ValueError(f"Invalid step direction: {step}")
        if s == "DOWN":
            seen_down = True
        elif s == "UP" and seen_down:
            return False
    return True


@dataclass(frozen=True)
class LeafOversubscriptionReport:
    """Oversubscription, bisection, and AllReduce timing analysis for a leaf switch."""

    downlink_ports: int
    uplink_ports: int
    port_rate_gbps: float
    downlink_bw_gbps: float
    uplink_bw_gbps: float
    oversubscription_ratio: float
    per_node_cross_leaf_gbps: float
    per_node_cross_leaf_gb_s: float
    allreduce_step_time_ms: float
    degraded_oversubscription_one_spine_lost: float


def evaluate_leaf_oversubscription(
    downlink_ports: int,
    uplink_ports: int,
    port_rate_gbps: float = 400.0,
    gradient_bytes_per_node: float = 2_000_000_000.0,
    num_spines: int = 2,
    lost_spines: int = 1,
) -> LeafOversubscriptionReport:
    """Compute the V8 Ch 6 leaf oversubscription and AllReduce penalty math.

    For `16 x 400 Gbps` downlinks (`6,400 Gbps`) and `8 x 400 Gbps` uplinks (`3,200 Gbps`):
      - `oversubscription_ratio = 6,400 / 3,200 = 2.0` (`2:1`).
      - Under full-fleet cross-leaf AllReduce, each node gets `3,200 / 16 = 200 Gbps` (`25 GB/s`),
        so `2 GB` takes `2 GB / 25 GB/s = 80 ms` vs `40 ms` at `1:1` (`50 GB/s`).
      - Losing `1` of `2` spines drops `8` uplinks to `4`, doubling oversubscription to `4:1`.
    """
    down_bw = downlink_ports * port_rate_gbps
    up_bw = uplink_ports * port_rate_gbps
    ratio = down_bw / up_bw
    eff_gbps = min(port_rate_gbps, up_bw / downlink_ports)
    eff_gb_s = eff_gbps / 8.0
    step_ms = (gradient_bytes_per_node / (eff_gb_s * 1e9)) * 1000.0

    surviving_spines = max(1, num_spines - lost_spines)
    surviving_uplinks = uplink_ports * (surviving_spines / num_spines)
    degraded_ratio = down_bw / (surviving_uplinks * port_rate_gbps)

    return LeafOversubscriptionReport(
        downlink_ports=downlink_ports,
        uplink_ports=uplink_ports,
        port_rate_gbps=port_rate_gbps,
        downlink_bw_gbps=round(down_bw, 2),
        uplink_bw_gbps=round(up_bw, 2),
        oversubscription_ratio=round(ratio, 2),
        per_node_cross_leaf_gbps=round(eff_gbps, 2),
        per_node_cross_leaf_gb_s=round(eff_gb_s, 2),
        allreduce_step_time_ms=round(step_ms, 2),
        degraded_oversubscription_one_spine_lost=round(degraded_ratio, 2),
    )


@dataclass(frozen=True)
class ClosScalePlan:
    """Switch and port counts for 3-stage and 5-stage rail-optimized Clos fabrics (`ADC Ch 3`)."""

    stages: int
    rows: int
    blocks: int
    total_servers: int
    total_gpus: int
    leaf_switches: int
    spine_switches: int
    super_spine_switches: int
    super_spine_oversubscription: str


def plan_three_stage_rail_clos(
    rows: int,
    switch_radix: int = 64,
    spine_radix: int = 64,
    gpus_per_server: int = 8,
) -> ClosScalePlan:
    """Compute ADC Ch 3 Fig 3-9 / 3-10 3-stage Clos scale for `rows` rail stripes.

    - Each row has `8` leaf switches (`64 x 400G`: `32` server downlinks + `32` spine uplinks),
      serving `32` servers = `256` GPUs (`256` server ports + `256` spine ports per row).
    - Max rows with `64`-port spines is `64 / 8 = 8` rows (`2,048` GPUs, `64` leaves, `32` spines,
      or `8` chassis spines of radix `256`).
    """
    downlinks_per_leaf = switch_radix // 2
    servers_per_row = downlinks_per_leaf
    gpus_per_row = servers_per_row * gpus_per_server
    leaves_per_row = gpus_per_server

    total_servers = rows * servers_per_row
    total_gpus = rows * gpus_per_row
    total_leaves = rows * leaves_per_row
    total_spine_ports_needed = total_gpus  # 1:1 non-blocking
    total_spines = total_spine_ports_needed // spine_radix

    return ClosScalePlan(
        stages=3,
        rows=rows,
        blocks=1,
        total_servers=total_servers,
        total_gpus=total_gpus,
        leaf_switches=total_leaves,
        spine_switches=total_spines,
        super_spine_switches=0,
        super_spine_oversubscription="1:1",
    )


def plan_five_stage_rail_clos(
    blocks: int,
    super_spine_switches: int = 32,
    super_spine_radix: int = 64,
) -> ClosScalePlan:
    """Compute ADC Ch 3 Fig 3-11 / 3-12 5-stage Clos scale across `blocks` bricks.

    - Each block (`4` rows) has `1,024` GPUs (`128` servers), `32` leaf switches (`64 x 400G`),
      and `32` spine switches (`64 x 400G`: `1,024` leaf-facing ports + `1,024` super-spine ports).
    - With `32` fixed `64 x 400G` super-spine switches (`2,048` total super-spine ports),
      `2` blocks (`2,048` GPUs) run at `1:1`, `4` blocks (`4,096` GPUs) at `2:1`, ...,
      `14` blocks (`14,336` GPUs) at `7:1`.
    """
    rows = blocks * 4
    total_gpus = blocks * 1024
    total_servers = total_gpus // 8
    leaves = blocks * 32
    spines = blocks * 32
    super_spine_ports = super_spine_switches * super_spine_radix
    oversub_num = total_gpus // super_spine_ports
    return ClosScalePlan(
        stages=5,
        rows=rows,
        blocks=blocks,
        total_servers=total_servers,
        total_gpus=total_gpus,
        leaf_switches=leaves,
        spine_switches=spines,
        super_spine_switches=super_spine_switches,
        super_spine_oversubscription=f"{oversub_num}:1",
    )


@dataclass(frozen=True)
class RailTopologyComparison:
    """Comparison of Rail-Optimized (`ROD`) vs Rail-Unified (`RUD`) and Multi-Planar designs."""

    design: str
    leaves_per_server: int
    intra_rail_switch_hops: int
    inter_rail_switch_hops: int
    servers_completely_isolated_on_single_leaf_failure: int
    servers_degraded_by_one_eighth_on_single_leaf_failure: int


def compare_rail_designs(
    servers_per_row: int = 32,
    gpus_per_server: int = 8,
    leaf_downlinks: int = 32,
) -> Tuple[RailTopologyComparison, RailTopologyComparison]:
    """Compare Rail-Optimized Design (`ROD`) and Rail-Unified Design (`RUD`) (`ADC Ch 3`).

    - In `ROD`, each of the `8` GPUs in a server connects to a distinct leaf switch
      (`NIC k -> Leaf k`). A single leaf failure degrades `1/8` of the rails across `32`
      servers (`0` servers completely isolated).
    - In `RUD`, all `8` GPUs of a server connect to the same leaf switch (`4` servers
      per `32`-downlink leaf). A single leaf failure completely isolates `4` servers (`32` GPUs).
    """
    rod = RailTopologyComparison(
        design="ROD (Rail-Optimized Design)",
        leaves_per_server=gpus_per_server,
        intra_rail_switch_hops=1,
        inter_rail_switch_hops=3,
        servers_completely_isolated_on_single_leaf_failure=0,
        servers_degraded_by_one_eighth_on_single_leaf_failure=servers_per_row,
    )
    rud_servers_per_leaf = leaf_downlinks // gpus_per_server
    rud = RailTopologyComparison(
        design="RUD (Rail-Unified Design)",
        leaves_per_server=1,
        intra_rail_switch_hops=1,
        inter_rail_switch_hops=1,  # within same 4-server leaf; 3 across leaves
        servers_completely_isolated_on_single_leaf_failure=rud_servers_per_leaf,
        servers_degraded_by_one_eighth_on_single_leaf_failure=0,
    )
    return rod, rud
