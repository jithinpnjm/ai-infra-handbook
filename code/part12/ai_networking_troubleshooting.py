"""AI Networking & Cross-Layer Troubleshooting Playbook toolkit (Chapter 12.24).

Encodes deterministic decision trees, counter analyzers, and bisection algorithms for:
1. InfiniBand 7-gate bottom-up troubleshooting (ibstat, sminfo, P_Key/routing/credit-loop,
   perfquery SymbolErrorCounter vs PortXmitWait, ib_write_lat tail percentiles, GPUDirect,
   and multi-rail collectives).
2. RoCEv2 / AI Ethernet 6-gate troubleshooting (ethtool FEC/CRC vs secondary ECN,
   ping vs QP RTR failure from MTU/GID/route mismatch, DSCP/QoS trust boundary,
   DCQCN/CNP feedback vs persistent PFC pause-tree backtrace).
3. PCIe, DMA engine, NVLink, and Xid 3-tier + Xid 74 hardware triage (lspci down-training
   Gen4 x16 -> Gen3 x8, Xid 79 bus fall-off, Xid 31/45/48/63/64/74/92/94/95, MIG vs broken
   NVLink topology, asymmetric dcgmi nvlink -e transceiver isolation).
4. NCCL collective timeout classification (starved/straggler rank vs code deadlock vs
   fabric stall), O(log2 N) multi-node straggler binary search, and cross-layer
   "when metrics lie" / Heisenbug / throttle-bitmask disambiguation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. InfiniBand 7-Gate Bottom-Up Decision Tree & Counter Analyzer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IBPortEvidence:
    hca_id: str
    port: int
    physical_state: str          # e.g., "LinkUp", "Polling", "Disabled"
    logical_state: str           # e.g., "Active", "Initializing", "Down"
    negotiated_rate_gbps: int    # e.g., 400 (NDR), 200 (HDR), 100 (EDR)
    expected_rate_gbps: int
    negotiated_width: int        # e.g., 4 (4x), 2 (2x), 1 (1x)
    expected_width: int
    base_lid: int                # 0 when unprogrammed
    sm_lid: int
    sm_master_count: int         # 1 = healthy single master; 0 = missing; >1 = split-brain
    sm_activity_advancing: bool
    pkey_compatible: bool
    route_valid: bool
    credit_loop_detected: bool
    symbol_error_delta: int
    link_downed_delta: int
    port_rcv_errors_delta: int
    port_xmit_discards_delta: int
    port_xmit_wait_delta: int
    host_rdma_bw_gbps: float
    expected_host_rdma_bw_gbps: float
    host_rdma_p999_lat_us: float
    baseline_p999_lat_us: float
    gdr_bw_gbps: float
    expected_gdr_bw_gbps: float
    pcie_topo_distance: str      # "PIX", "PXB", "PHB", "NODE", "SYS"
    collective_bw_gbps: float
    expected_collective_bw_gbps: float


@dataclass(frozen=True)
class IBDiagnosisResult:
    first_failed_gate: str
    root_cause_category: str
    summary: str
    recommended_action: str


def evaluate_ib_layered_gates(ev: IBPortEvidence) -> IBDiagnosisResult:
    """Evaluate the 7 InfiniBand troubleshooting gates strictly from bottom to top.

    Stops at the FIRST gate that diverges from the known-good baseline:
      Gate 1: Physical layer (Physical state, Rate, Width, SymbolError/LinkDowned deltas)
      Gate 2: Subnet Manager / Control Plane (Logical state Active, Base LID > 0, 1 Master SM)
      Gate 3: Routing, Partition (P_Key), and Credit-Loop freedom
      Gate 4: Host-Memory RDMA transport (ib_write_bw / ib_write_lat p99.9 tail)
      Gate 5: GPUDirect RDMA & PCIe/NUMA locality (ib_write_bw --use_cuda, PIX/PXB)
      Gate 6: Multi-node Collective & Fabric Congestion (PortXmitWait with clean SymbolError)
      Gate 7: Application / Rank Straggler layer
    """
    # Gate 1: Physical layer
    if ev.physical_state != "LinkUp":
        return IBDiagnosisResult(
            first_failed_gate="Gate 1: Physical Layer",
            root_cause_category="port_down_no_carrier",
            summary=f"{ev.hca_id}:{ev.port} Physical state is {ev.physical_state} (not LinkUp).",
            recommended_action="Inspect cable seating, optical transceiver, switch port admin state, and HCA firmware before testing any upper layer.",
        )
    if ev.negotiated_rate_gbps < ev.expected_rate_gbps or ev.negotiated_width < ev.expected_width:
        return IBDiagnosisResult(
            first_failed_gate="Gate 1: Physical Layer",
            root_cause_category="reduced_rate_or_width",
            summary=(
                f"{ev.hca_id}:{ev.port} down-trained to {ev.negotiated_rate_gbps} Gbps ({ev.negotiated_width}x) "
                f"vs expected {ev.expected_rate_gbps} Gbps ({ev.expected_width}x)."
            ),
            recommended_action="Clean or replace damaged DAC/AOC/optical transceiver and check peer switch port lanes.",
        )
    if ev.symbol_error_delta > 0 or ev.link_downed_delta > 0 or ev.port_rcv_errors_delta > 0:
        return IBDiagnosisResult(
            first_failed_gate="Gate 1: Physical Layer",
            root_cause_category="rising_physical_link_errors",
            summary=(
                f"{ev.hca_id}:{ev.port} physical error deltas rising "
                f"(SymbolError={ev.symbol_error_delta}, LinkDowned={ev.link_downed_delta}, "
                f"PortRcvErrors={ev.port_rcv_errors_delta})."
            ),
            recommended_action="Replace defective cable/transceiver or marginal port; do not mask with larger NCCL timeouts.",
        )

    # Gate 2: Subnet Manager & Logical Port State
    if ev.logical_state != "Active" or ev.base_lid == 0 or ev.sm_master_count != 1 or not ev.sm_activity_advancing:
        return IBDiagnosisResult(
            first_failed_gate="Gate 2: Subnet Management (Control Plane)",
            root_cause_category="sm_or_lid_unprogrammed",
            summary=(
                f"{ev.hca_id}:{ev.port} is Physical LinkUp but State={ev.logical_state}, "
                f"Base lid={ev.base_lid}, master_SMs={ev.sm_master_count}, sweep_active={ev.sm_activity_advancing}."
            ),
            recommended_action="Check sminfo and OpenSM/UFM logs to restore a single authoritative master SM and complete fabric sweep.",
        )

    # Gate 3: Routing, P_Key, and Credit Loops
    if not ev.pkey_compatible or not ev.route_valid or ev.credit_loop_detected:
        cause = (
            "credit_loop_deadlock"
            if ev.credit_loop_detected
            else ("pkey_mismatch" if not ev.pkey_compatible else "missing_or_invalid_route")
        )
        return IBDiagnosisResult(
            first_failed_gate="Gate 3: Routing, Partition (P_Key), and Credit Loop",
            root_cause_category=cause,
            summary=(
                f"Addressing/routing fault: pkey_ok={ev.pkey_compatible}, "
                f"route_ok={ev.route_valid}, credit_loop={ev.credit_loop_detected}."
            ),
            recommended_action="Verify partition membership (P_Key) on both endpoints, inspect ibroute LFTs, and enforce loop-free routing engine (updn/ftree/dfp).",
        )

    # Gate 4: Host-Memory RDMA Transport
    tail_ratio = ev.host_rdma_p999_lat_us / max(ev.baseline_p999_lat_us, 0.01)
    if ev.host_rdma_bw_gbps < 0.85 * ev.expected_host_rdma_bw_gbps or tail_ratio > 2.0:
        return IBDiagnosisResult(
            first_failed_gate="Gate 4: Host-Memory RDMA Transport",
            root_cause_category="host_rdma_transport_or_tail_degradation",
            summary=(
                f"Host RDMA below baseline: bw={ev.host_rdma_bw_gbps:.1f}/{ev.expected_host_rdma_bw_gbps:.1f} Gbps, "
                f"p99.9={ev.host_rdma_p999_lat_us:.2f} us ({tail_ratio:.2f}x baseline {ev.baseline_p999_lat_us:.2f} us)."
            ),
            recommended_action="Check NUMA CPU/memory pinning (numactl), QP/CQ completion status, PCIe link speed, and switch transit congestion before testing GPUDirect.",
        )

    # Gate 5: GPUDirect RDMA & PCIe Locality
    if ev.gdr_bw_gbps < 0.85 * ev.expected_gdr_bw_gbps or ev.pcie_topo_distance not in ("PIX", "PXB"):
        return IBDiagnosisResult(
            first_failed_gate="Gate 5: GPUDirect RDMA and Locality",
            root_cause_category="gpudirect_fallback_or_locality_mismatch",
            summary=(
                f"Host RDMA passed ({ev.host_rdma_bw_gbps:.1f} Gbps) but GPU RDMA degraded to "
                f"{ev.gdr_bw_gbps:.1f}/{ev.expected_gdr_bw_gbps:.1f} Gbps (topo={ev.pcie_topo_distance})."
            ),
            recommended_action="Verify nvidia-peermem/dma-buf loaded, PCIe ACS disabled (ECAP_ACS+0x6.w=0000), Large BAR1 enabled, and GPU-NIC pair is PIX/PXB.",
        )

    # Gate 6: Multi-Node Collective & Fabric Congestion
    if ev.collective_bw_gbps < 0.85 * ev.expected_collective_bw_gbps:
        if ev.port_xmit_wait_delta > 0 and ev.symbol_error_delta == 0 and ev.link_downed_delta == 0:
            return IBDiagnosisResult(
                first_failed_gate="Gate 6: Multi-Node Collective / Fabric Congestion",
                root_cause_category="fabric_congestion_without_physical_errors",
                summary=(
                    f"Pairwise GDR healthy, but collective bw={ev.collective_bw_gbps:.1f}/{ev.expected_collective_bw_gbps:.1f} Gbps "
                    f"with PortXmitWait delta={ev.port_xmit_wait_delta} and 0 physical errors."
                ),
                recommended_action="Trace PortXmitWait gradient toward the congested cut/receiver, rebalance routes or enable adaptive routing, and fix rank/rail placement.",
            )
        return IBDiagnosisResult(
            first_failed_gate="Gate 6: Multi-Node Collective / Topology Scale",
            root_cause_category="collective_rail_or_algorithm_imbalance",
            summary=(
                f"Collective bw={ev.collective_bw_gbps:.1f}/{ev.expected_collective_bw_gbps:.1f} Gbps "
                f"despite clean pairwise GDR."
            ),
            recommended_action="Inspect rail symmetry, NCCL_ALGO/NCCL_PROTO selection, and cross-rack oversubscription.",
        )

    # Gate 7: Application / Straggler
    return IBDiagnosisResult(
        first_failed_gate="Gate 7: Application and Rank Synchronization",
        root_cause_category="application_or_straggler_layer",
        summary="All 6 fabric, transport, and GPUDirect gates match baseline; investigate rank stragglers or application collective call order.",
        recommended_action="Inspect NCCL_DEBUG=INFO / ncclras opCount progression and per-rank data loader / GPU clock / thermal telemetry.",
    )


@dataclass(frozen=True)
class LatencyDistributionComparison:
    typical_ratio: float
    avg_ratio: float
    p99_ratio: float
    p999_ratio: float
    averages_look_healthy: bool
    tail_is_degraded: bool


def compare_ib_write_lat_tail(
    baseline_typical_us: float = 1.55,
    baseline_avg_us: float = 1.56,
    baseline_p99_us: float = 1.71,
    baseline_p999_us: float = 1.98,
    observed_typical_us: float = 1.58,
    observed_avg_us: float = 1.61,
    observed_p99_us: float = 2.90,
    observed_p999_us: float = 5.77,
) -> LatencyDistributionComparison:
    """Compare ib_write_lat typical/average latency against 99% and 99.9% tail latency.

    Models Volume 08 Chapter 10's 2-byte 1,000-iteration RDMA_Write latency check:
      Baseline: t_min=1.41, t_max=2.03, t_typical=1.55, t_avg=1.56, p99=1.71, p99.9=1.98 us
      Observed: t_min=1.42, t_max=6.81, t_typical=1.58, t_avg=1.61, p99=2.90, p99.9=5.77 us
    """
    typ_r = round(observed_typical_us / baseline_typical_us, 4)
    avg_r = round(observed_avg_us / baseline_avg_us, 4)
    p99_r = round(observed_p99_us / baseline_p99_us, 4)
    p999_r = round(observed_p999_us / baseline_p999_us, 4)
    return LatencyDistributionComparison(
        typical_ratio=typ_r,
        avg_ratio=avg_r,
        p99_ratio=p99_r,
        p999_ratio=p999_r,
        averages_look_healthy=(typ_r < 1.05 and avg_r < 1.05),
        tail_is_degraded=(p99_r > 1.5 or p999_r > 2.0),
    )


# ---------------------------------------------------------------------------
# 2. RoCEv2 / AI Ethernet 6-Gate Troubleshooter & PFC/ECN Analyzer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RoCEPathEvidence:
    netdev: str
    rdma_dev: str
    link_up: bool
    speed_gbps: int
    expected_speed_gbps: int
    fec_corrected_delta: int
    fec_uncorrected_delta: int
    rx_crc_errors_delta: int
    icmp_ping_ok: bool
    local_mtu: int
    path_mtu: int
    expected_mtu: int
    gid_index: int
    expected_gid_index: int
    gid_subnet_matches_route: bool
    qp_rtr_success: bool
    retry_exc_err_count: int
    dscp_value: int
    expected_dscp_value: int
    prio3_packets_delta: int
    rx_ecn_marked_prio3_delta: int
    rx_pfc_prio3_delta: int
    tx_pfc_prio3_delta: int
    cnp_packets_handled_delta: int
    sender_rate_reduced: bool
    pfc_pause_pinned_100pct: bool


@dataclass(frozen=True)
class RoCEDiagnosisResult:
    first_failed_gate: str
    fault_class: str
    explanation: str
    remediation: str


def evaluate_roce_layered_gates(ev: RoCEPathEvidence) -> RoCEDiagnosisResult:
    """Evaluate the 6 RoCEv2 / AI Ethernet troubleshooting gates in strict bottom-up order.

    Models Volume 09 Chapter 11 and Labs 01-04:
      Gate 1: Physical / FEC / CRC layer (fec_uncorrected_blocks & rx_crc_errors)
      Gate 2: L3 IP Route & MTU consistency (9000 jumbo frames end-to-end)
      Gate 3: RoCE Endpoint / GID / QP RTR transition (why ping works but RoCE fails)
      Gate 4: QoS Classification & Trust Boundary (DSCP -> Priority 3 queue)
      Gate 5: Congestion Control Loop (ECN -> CNP -> DCQCN rate cut vs PFC storm)
      Gate 6: Host / GPU / Collective layer
    """
    # Gate 1: Physical & FEC
    if not ev.link_up or ev.speed_gbps < ev.expected_speed_gbps:
        return RoCEDiagnosisResult(
            first_failed_gate="Gate 1: Physical Layer",
            fault_class="link_down_or_downtrained",
            explanation=f"{ev.netdev} ({ev.rdma_dev}) link_up={ev.link_up}, speed={ev.speed_gbps}/{ev.expected_speed_gbps} Gbps.",
            remediation="Inspect optic/DAC seating, switch port state, and Auto-Negotiation/FEC profile.",
        )
    if ev.fec_uncorrected_delta > 0 or ev.rx_crc_errors_delta > 0:
        secondary_ecn_note = (
            f" Note: rx_ecn_marked_prio3_delta={ev.rx_ecn_marked_prio3_delta} rose secondarily due to RDMA retransmission load."
            if ev.rx_ecn_marked_prio3_delta > 0
            else ""
        )
        return RoCEDiagnosisResult(
            first_failed_gate="Gate 1: Physical Layer (Uncorrectable FEC / CRC)",
            fault_class="physical_bit_errors_with_crc_loss",
            explanation=(
                f"{ev.netdev} has fec_uncorrected_blocks={ev.fec_uncorrected_delta} and "
                f"rx_crc_errors={ev.rx_crc_errors_delta} (fec_corrected={ev.fec_corrected_delta})."
                + secondary_ecn_note
            ),
            remediation="Replace marginal DAC/AOC cable or clean fiber optic before touching QoS/ECN thresholds.",
        )

    # Gate 2: L3 IP & MTU
    if ev.local_mtu != ev.expected_mtu or ev.path_mtu < ev.expected_mtu:
        return RoCEDiagnosisResult(
            first_failed_gate="Gate 2: L3 IP and MTU Path",
            fault_class="mtu_mismatch_silent_drop",
            explanation=(
                f"Ping ok={ev.icmp_ping_ok} (64B ICMP passes), but local_mtu={ev.local_mtu}, "
                f"path_mtu={ev.path_mtu} vs expected_mtu={ev.expected_mtu} drops full-MTU RoCEv2 frames."
            ),
            remediation="Configure consistent jumbo MTU (9000) on host netdevs and every leaf/spine switch hop.",
        )

    # Gate 3: RoCE Endpoint / GID / QP RTR
    if (
        not ev.qp_rtr_success
        or ev.gid_index != ev.expected_gid_index
        or not ev.gid_subnet_matches_route
        or ev.retry_exc_err_count > 0
    ):
        return RoCEDiagnosisResult(
            first_failed_gate="Gate 3: RoCEv2 Endpoint / GID / QP State",
            fault_class="gid_or_endpoint_selection_fault",
            explanation=(
                f"Ping ok={ev.icmp_ping_ok}, but QP RTR={ev.qp_rtr_success}, "
                f"gid_index={ev.gid_index} (expected {ev.expected_gid_index}), "
                f"gid_subnet_ok={ev.gid_subnet_matches_route}, retries={ev.retry_exc_err_count}."
            ),
            remediation="Align NIC device (-d mlx5_X), NCCL_IB_GID_INDEX (RoCEv2 IPv4/IPv6), and source IP route per rail.",
        )

    # Gate 4: QoS Classification & Trust Boundary
    if ev.dscp_value != ev.expected_dscp_value or ev.prio3_packets_delta == 0:
        return RoCEDiagnosisResult(
            first_failed_gate="Gate 4: QoS Classification and Trust Boundary",
            fault_class="qos_dscp_trust_mismatch",
            explanation=(
                f"RoCE traffic sent with DSCP={ev.dscp_value} (expected {ev.expected_dscp_value}), "
                f"prio3_packets_delta={ev.prio3_packets_delta} (traffic falling into lossy default queue 0)."
            ),
            remediation="Set mlx5_qos / NCCL_IB_TC=106 (DSCP 26) and verify switch ingress DSCP trust mapping to lossless Priority 3.",
        )

    # Gate 5: ECN / DCQCN / PFC Congestion Loop
    if ev.rx_ecn_marked_prio3_delta > 0 and not ev.sender_rate_reduced:
        return RoCEDiagnosisResult(
            first_failed_gate="Gate 5: Congestion Feedback Loop (ECN / DCQCN)",
            fault_class="ecn_marks_without_sender_backoff",
            explanation=(
                f"Switch marked rx_ecn_marked_prio3={ev.rx_ecn_marked_prio3_delta}, "
                f"cnp_handled={ev.cnp_packets_handled_delta}, but sender_rate_reduced=False."
            ),
            remediation="Verify DCQCN is enabled on ConnectX NICs on Priority 3 and CNP packets (DSCP 48 / Priority 6) are not dropped.",
        )
    if ev.pfc_pause_pinned_100pct:
        return RoCEDiagnosisResult(
            first_failed_gate="Gate 5: Congestion Feedback Loop (Persistent PFC Storm)",
            fault_class="persistent_pfc_pause_tree",
            explanation=(
                f"Persistent PFC pause on Priority 3 (rx_pfc={ev.rx_pfc_prio3_delta}, "
                f"tx_pfc={ev.tx_pfc_prio3_delta}); queue pinned at 100% pause duration."
            ),
            remediation="Do NOT blindly disable PFC; trace pause frames downstream to the root congested egress port/receiver and verify ECN Kmin < Kmax < PFC Xoff.",
        )

    # Gate 6: Healthy fabric / move to Host/GPU/Collective
    return RoCEDiagnosisResult(
        first_failed_gate="Gate 6: Host / GPU / Collective Layer",
        fault_class="roce_fabric_healthy_or_bounded_contention",
        explanation="Physical, MTU, GID/QP, QoS trust, and ECN/DCQCN feedback loop are operating within qualified bounds.",
        remediation="Proceed to GPU/NIC locality (nvidia-smi topo -m) and per-rank collective timing.",
    )


def trace_pfc_pause_root_port(
    switch_ports: Sequence[Dict[str, object]],
) -> str:
    """Identify the root downstream congested egress port in a PFC pause propagation tree.

    In a lossless pause tree:
      - Upstream hops BOTH receive PFC pauses from downstream (`rx_pfc > 0`) AND
        transmit PFC pauses upstream (`tx_pfc > 0`) as their ingress buffers fill.
      - The root congested egress bottleneck port at the head of the tree has high queue
        occupancy and receives pauses from the slow/stuck receiver (`rx_pfc > 0`) or generates
        the initial pause (`tx_pfc > 0` toward senders with `downstream_rx_pfc == 0`),
        i.e., it is the most downstream port where congestion originates.
    Each dict in `switch_ports` has:
      - "port_id": str
      - "hop_order_from_sender": int (1 = ingress leaf from sender, 2 = spine, 3 = egress leaf to receiver)
      - "queue3_occupancy_pct": float (e.g., 95%, 96%, 98%)
      - "tx_pfc_prio3_delta": int
      - "rx_pfc_prio3_delta": int
    Returns the `port_id` of the most downstream congested port (`queue3_occupancy_pct >= 80.0`).
    """
    congested = [
        p for p in switch_ports if float(p["queue3_occupancy_pct"]) >= 80.0
    ]
    if not congested:
        return "none"
    # Sort by hop_order_from_sender descending (most downstream first), tie-break by occupancy
    congested.sort(
        key=lambda p: (int(p["hop_order_from_sender"]), float(p["queue3_occupancy_pct"])),
        reverse=True,
    )
    return str(congested[0]["port_id"])


# ---------------------------------------------------------------------------
# 3. Xid 3-Tier + Xid 74 Classifier, PCIe Down-Train & NVLink Isolator
# ---------------------------------------------------------------------------

XID_CATALOG: Dict[int, Tuple[str, str, str]] = {
    # code: (tier, short_meaning, action)
    13: ("Tier 2", "Graphics Engine Exception", "Process-recoverable unless recurring on same GPU across unrelated apps."),
    31: ("Tier 2", "GPU memory page fault", "Check app out-of-bounds access or DMA engine fault if recurring with PCIe errors."),
    32: ("Tier 2", "Invalid or corrupted push buffer stream", "Usually process-recoverable; check PCIe replay counter if recurring."),
    43: ("Tier 2", "GPU stopped processing", "Reset GPU and inspect dmesg for an earlier root-cause Xid."),
    45: ("Tier 1", "Preemptive cleanup, due to previous errors", "Downstream symptom; inspect the Xid logged immediately before Xid 45."),
    48: ("Tier 3", "Double Bit ECC Error (uncorrectable)", "Cordon and drain node immediately; retire page or RMA GPU."),
    61: ("Tier 3", "Internal micro-controller breakpoint/warning", "Unrecoverable firmware fault; drain node and escalate to hardware."),
    62: ("Tier 3", "Internal micro-controller halt", "Unrecoverable embedded controller halt; drain node and RMA GPU."),
    63: ("Tier 1", "ECC page retirement or row remapping recording event", "Self-healing informational event; log and track trailing 7-day rate."),
    64: ("Tier 3", "ECC page retirement or row remapping failure", "Self-healing mechanism failed; drain node immediately and RMA GPU."),
    74: ("NVLink", "NVLink Error (fatal link-level error)", "Run nvidia-smi topo -m and dcgmi nvlink -e on both peer GPUs; reset or RMA."),
    79: ("Tier 3", "GPU has fallen off the bus", "GPU missing from lspci; drain node, attempt PCIe remove/rescan or reseat power/slot."),
    92: ("Tier 1", "High single-bit ECC error rate", "Precursor warning; monitor SBE acceleration rate and schedule preventive maintenance."),
    94: ("Tier 2", "Contained ECC error", "Uncorrectable ECC contained to one process; restart app and reset GPU when convenient."),
    95: ("Tier 3", "Uncontained ECC error", "Data integrity at risk; drain GPU immediately and invalidate job output."),
}


def classify_xid_sequence(xid_events: Sequence[int]) -> Dict[str, object]:
    """Classify a chronological sequence of Xid codes from dmesg (oldest first).

    Handles precursor chains such as Volume 20 Chapter 02's:
      [Xid 92 (SBE rate), Xid 45 (preemptive cleanup), Xid 79 (fell off bus)]
    """
    tiers = [XID_CATALOG.get(x, ("Unknown", "Unknown Xid", "Inspect dmesg"))[0] for x in xid_events]
    immediate_drain = any(t in ("Tier 3", "NVLink") for t in tiers)
    # Primary root Xid: ignore Xid 45 (which is always cleanup of a prior Xid)
    non_cleanup = [x for x in xid_events if x != 45]
    terminal_xid = non_cleanup[-1] if non_cleanup else xid_events[-1]
    precursor_xids = non_cleanup[:-1] if len(non_cleanup) > 1 else []
    tier, meaning, action = XID_CATALOG.get(
        terminal_xid, ("Unknown", "Unknown Xid", "Inspect dmesg")
    )
    return {
        "xid_sequence": list(xid_events),
        "terminal_xid": terminal_xid,
        "terminal_tier": tier,
        "terminal_meaning": meaning,
        "precursor_xids": precursor_xids,
        "had_preemptive_cleanup_45": (45 in xid_events),
        "immediate_drain_required": immediate_drain,
        "recommended_action": action,
    }


@dataclass(frozen=True)
class NVLinkPairDiagnosis:
    gpu_a: int
    gpu_b: int
    topo_entry: str              # e.g., "NV12", "NV18", "PIX", "PHB"
    expected_topo_entry: str
    mig_enabled: bool
    gpu_a_crc_errors: int
    gpu_a_replay_errors: int
    gpu_b_crc_errors: int
    gpu_b_replay_errors: int
    xid_74_present: bool
    status: str
    faulty_side: str
    action: str


def diagnose_nvlink_pair(
    gpu_a: int,
    gpu_b: int,
    topo_entry: str,
    expected_topo_entry: str = "NV12",
    mig_enabled: bool = False,
    gpu_a_crc_errors: int = 0,
    gpu_a_replay_errors: int = 0,
    gpu_b_crc_errors: int = 0,
    gpu_b_replay_errors: int = 0,
    xid_74_present: bool = False,
) -> NVLinkPairDiagnosis:
    """Diagnose NVLink topology fallback (`PIX`/`PHB` vs `NV#`) and isolate transceiver side.

    Models Volume 20 Chapter 04:
      - If MIG mode is enabled, NVLink P2P is intentionally disabled by design.
      - If MIG is disabled and topo shows PIX/PHB where NV12 is expected, check
        asymmetric `dcgmi nvlink -e` counters (e.g., GPU2 has 184,213 CRC / 92,104 replay
        errors while GPU3 has 0 errors) to isolate the faulty GPU transceiver.
    """
    if mig_enabled and not topo_entry.startswith("NV"):
        return NVLinkPairDiagnosis(
            gpu_a=gpu_a,
            gpu_b=gpu_b,
            topo_entry=topo_entry,
            expected_topo_entry=expected_topo_entry,
            mig_enabled=mig_enabled,
            gpu_a_crc_errors=gpu_a_crc_errors,
            gpu_a_replay_errors=gpu_a_replay_errors,
            gpu_b_crc_errors=gpu_b_crc_errors,
            gpu_b_replay_errors=gpu_b_replay_errors,
            xid_74_present=xid_74_present,
            status="working_as_designed_mig_isolation",
            faulty_side="none",
            action="No hardware action; MIG mode intentionally disables NVLink P2P between instances.",
        )

    if topo_entry == expected_topo_entry and gpu_a_crc_errors == 0 and gpu_b_crc_errors == 0 and not xid_74_present:
        return NVLinkPairDiagnosis(
            gpu_a=gpu_a,
            gpu_b=gpu_b,
            topo_entry=topo_entry,
            expected_topo_entry=expected_topo_entry,
            mig_enabled=mig_enabled,
            gpu_a_crc_errors=0,
            gpu_a_replay_errors=0,
            gpu_b_crc_errors=0,
            gpu_b_replay_errors=0,
            xid_74_present=False,
            status="healthy_nvlink",
            faulty_side="none",
            action="NVLink topology and error counters are clean; investigate NCCL algorithm or rank stragglers.",
        )

    a_err = gpu_a_crc_errors + gpu_a_replay_errors
    b_err = gpu_b_crc_errors + gpu_b_replay_errors
    if a_err > 0 and b_err == 0:
        side = f"GPU{gpu_a}_transceiver"
    elif b_err > 0 and a_err == 0:
        side = f"GPU{gpu_b}_transceiver"
    elif a_err > 0 and b_err > 0:
        side = f"shared_bridge_or_both_GPU{gpu_a}_GPU{gpu_b}"
    else:
        side = f"link_down_between_GPU{gpu_a}_and_GPU{gpu_b}"

    return NVLinkPairDiagnosis(
        gpu_a=gpu_a,
        gpu_b=gpu_b,
        topo_entry=topo_entry,
        expected_topo_entry=expected_topo_entry,
        mig_enabled=mig_enabled,
        gpu_a_crc_errors=gpu_a_crc_errors,
        gpu_a_replay_errors=gpu_a_replay_errors,
        gpu_b_crc_errors=gpu_b_crc_errors,
        gpu_b_replay_errors=gpu_b_replay_errors,
        xid_74_present=xid_74_present,
        status="nvlink_hardware_fallback_to_pcie",
        faulty_side=side,
        action=f"Drain node, attempt nvidia-smi -i {gpu_a} --gpu-reset, and escalate {side} to hardware RMA if {topo_entry} persists.",
    )


@dataclass(frozen=True)
class PCIeLinkAudit:
    bdf: str
    cap_gen: int
    cap_width: int
    sta_gen: int
    sta_width: int
    measured_h2d_gb_s: float
    expected_baseline_gb_s: float
    pcie_replay_counter: int
    is_downtrained: bool
    bandwidth_ratio: float
    status: str


def audit_pcie_link_and_dma(
    bdf: str,
    cap_gen: int = 4,
    cap_width: int = 16,
    sta_gen: int = 3,
    sta_width: int = 8,
    measured_h2d_gb_s: float = 2.3,
    expected_baseline_gb_s: float = 22.0,
    pcie_replay_counter: int = 127,
) -> PCIeLinkAudit:
    """Audit PCIe LnkCap vs LnkSta negotiation and DMA H2D bandwidthTest throughput.

    Models Volume 20 Chapter 07:
      Expected Gen4 x16 (16 GT/s, x16) -> 20-26 GB/s H2D bandwidthTest (22.0 GB/s ref, >=17.6 GB/s 80% threshold).
      Down-trained Gen3 x8 (8 GT/s, x8) with 127 replays -> 2.3 GB/s (~90% drop vs 22.0 GB/s or ~81% drop vs 12.0 GB/s).
    """
    downtrained = (sta_gen < cap_gen) or (sta_width < cap_width)
    ratio = round(measured_h2d_gb_s / expected_baseline_gb_s, 4)
    if downtrained or ratio < 0.80 or pcie_replay_counter > 5:
        status = "degraded_pcie_link_or_dma"
    else:
        status = "healthy_pcie_link"
    return PCIeLinkAudit(
        bdf=bdf,
        cap_gen=cap_gen,
        cap_width=cap_width,
        sta_gen=sta_gen,
        sta_width=sta_width,
        measured_h2d_gb_s=measured_h2d_gb_s,
        expected_baseline_gb_s=expected_baseline_gb_s,
        pcie_replay_counter=pcie_replay_counter,
        is_downtrained=downtrained,
        bandwidth_ratio=ratio,
        status=status,
    )


# ---------------------------------------------------------------------------
# 4. NCCL Timeout Classifier, O(log2 N) Straggler Bisection & Cross-Layer Triage
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NCCLTimeoutDiagnosis:
    failure_mode: str            # "starved_or_straggler_rank", "code_level_deadlock", "fabric_stall_all_ranks"
    lagging_ranks: Tuple[int, ...]
    max_op_count: int
    min_op_count: int
    explanation: str
    recommended_fix: str


def classify_nccl_timeout(
    rank_op_counts: Dict[int, int],
    rank_op_types: Optional[Dict[int, str]] = None,
    lagging_rank_gpu_util_pct: float = 2.0,
    lagging_rank_xid: Optional[int] = None,
    lagging_rank_batch_fetch_s: float = 47.31,
) -> NCCLTimeoutDiagnosis:
    """Classify an NCCL collective hang using per-rank opCount progression.

    Models Volume 20 Chapter 03:
      Case 1 (Starved / Straggler rank): Most ranks reach opCount 4821, while rank 3 is
        stuck at opCount 4820. If rank 3 has Xid -> GPU fault. If rank 3 is alive with
        2% SM util and 47.31s batch fetch -> upstream data pipeline starvation.
      Case 2 (Code-level deadlock): Ranks issue different collective types at the same
        step or diverge across multiple distinct non-converging opCounts due to a conditional
        branch (`if rank == 0:`).
      Case 3 (True network / fabric stall): Every rank reaches the exact same opCount
        and collective type, and all stall inside the network transfer simultaneously.
    """
    counts = list(rank_op_counts.values())
    max_op = max(counts)
    min_op = min(counts)
    distinct_counts = sorted(set(counts))

    if rank_op_types and len(set(rank_op_types.values())) > 1:
        lagging = tuple(sorted(r for r, c in rank_op_counts.items() if c < max_op))
        return NCCLTimeoutDiagnosis(
            failure_mode="code_level_deadlock",
            lagging_ranks=lagging,
            max_op_count=max_op,
            min_op_count=min_op,
            explanation="Ranks invoked mismatched collective operations (divergent conditional code path).",
            recommended_fix="Audit distributed PyTorch code to ensure all ranks call identical collectives unconditionally.",
        )

    if max_op == min_op:
        return NCCLTimeoutDiagnosis(
            failure_mode="fabric_stall_all_ranks",
            lagging_ranks=(),
            max_op_count=max_op,
            min_op_count=min_op,
            explanation=f"All {len(rank_op_counts)} ranks reached opCount {max_op} and stalled together in the network transfer.",
            recommended_fix="Inspect switch logs, ibstat/ethtool counters, PFC pause storms, or routing loops across the fabric.",
        )

    # Check if >2 distinct static opCounts indicate structural multi-branch divergence
    if len(distinct_counts) >= 3:
        lagging = tuple(sorted(r for r, c in rank_op_counts.items() if c < max_op))
        return NCCLTimeoutDiagnosis(
            failure_mode="code_level_deadlock",
            lagging_ranks=lagging,
            max_op_count=max_op,
            min_op_count=min_op,
            explanation=f"Ranks diverged across {len(distinct_counts)} non-converging opCounts {distinct_counts}.",
            recommended_fix="Inspect rank-conditional branches calling different numbers of collectives.",
        )

    lagging = tuple(sorted(r for r, c in rank_op_counts.items() if c == min_op))
    if lagging_rank_xid is not None:
        return NCCLTimeoutDiagnosis(
            failure_mode="crashed_or_xid_rank",
            lagging_ranks=lagging,
            max_op_count=max_op,
            min_op_count=min_op,
            explanation=f"Rank(s) {lagging} lagged at opCount {min_op} (others at {max_op}) due to GPU Xid {lagging_rank_xid}.",
            recommended_fix=f"Handle Xid {lagging_rank_xid} on rank {lagging}, cordon faulty node if Tier 3, and restart from checkpoint.",
        )

    if lagging_rank_gpu_util_pct < 10.0 and lagging_rank_batch_fetch_s > 5.0:
        return NCCLTimeoutDiagnosis(
            failure_mode="starved_or_straggler_rank",
            lagging_ranks=lagging,
            max_op_count=max_op,
            min_op_count=min_op,
            explanation=(
                f"Rank(s) {lagging} stuck at opCount {min_op} (others waiting at {max_op}); "
                f"GPU SM util is {lagging_rank_gpu_util_pct:.1f}% and batch fetch took {lagging_rank_batch_fetch_s:.2f}s."
            ),
            recommended_fix="Fix upstream CPU/storage data loader bottleneck or uneven shard size (e.g., 187G vs 41G shard); do not blame NCCL.",
        )

    return NCCLTimeoutDiagnosis(
        failure_mode="starved_or_straggler_rank",
        lagging_ranks=lagging,
        max_op_count=max_op,
        min_op_count=min_op,
        explanation=f"Rank(s) {lagging} lagging at opCount {min_op} while peers wait at {max_op}.",
        recommended_fix="Inspect thermal/power clock throttling or degraded NIC/NVLink bandwidth on the lagging rank.",
    )


@dataclass(frozen=True)
class BisectionResult:
    total_nodes: int
    isolated_node: str
    tests_executed: int
    linear_tests_saved: int
    trace: Tuple[Tuple[str, float], ...]


def bisect_straggler_node(
    nodes: Sequence[str],
    measure_subset_bw_gb_s: Callable[[Sequence[str]], float],
    healthy_threshold_gb_s: float = 150.0,
) -> BisectionResult:
    """Binary-search (O(log2 N)) multi-node collective straggler isolation.

    At each step, splits candidate `nodes` into left and right halves and benchmarks
    the left half (and right half when needed) to isolate the single degraded node in
    O(log2 N) collective runs instead of N linear runs.
    """
    candidates = list(nodes)
    trace: List[Tuple[str, float]] = []
    tests = 0

    while len(candidates) > 1:
        mid = len(candidates) // 2
        left = candidates[:mid]
        right = candidates[mid:]

        if len(left) == 1:
            # Test the right side or single node probe
            bw_left = measure_subset_bw_gb_s(left)
            tests += 1
            trace.append((",".join(left), bw_left))
            if bw_left < healthy_threshold_gb_s:
                candidates = left
            else:
                candidates = right
        else:
            bw_left = measure_subset_bw_gb_s(left)
            tests += 1
            trace.append((f"{left[0]}..{left[-1]} ({len(left)}n)", bw_left))
            if bw_left < healthy_threshold_gb_s:
                candidates = left
            else:
                candidates = right

    return BisectionResult(
        total_nodes=len(nodes),
        isolated_node=candidates[0],
        tests_executed=tests,
        linear_tests_saved=max(0, len(nodes) - tests),
        trace=tuple(trace),
    )


def analyze_cross_layer_iteration(
    timings_ms: Dict[str, float],
    nvidia_smi_util_pct: float = 100.0,
    kernel_launch_rate_hz: float = 50.0,
    expected_launch_rate_hz: float = 1000.0,
    throughput_no_profiler: float = 500.0,
    throughput_smi_poll: float = 450.0,
    throughput_nsys: float = 250.0,
) -> Dict[str, object]:
    """Analyze a 7-stage iteration breakdown, utilization lie, and profiler Heisenbug overhead.

    Models Volume 20 Chapter 12:
      - timings_ms: e.g. data_load_cpu=450, allreduce_network=150, backward_gpu=60,
        forward_gpu=30, data_transfer_pcie=10, optimizer_gpu=10, loss_gpu=8
      - Utilization lie: nvidia-smi reports 100% GPU util while kernel launch rate is 50/s
        (vs 1000+/s expected), meaning the GPU is waiting on CPU kernel launch / data load.
      - Heisenbug: nsys overhead = (1 - 250/500) = 50.0%, nvidia-smi polling overhead = 10.0%.
    """
    total_ms = sum(timings_ms.values())
    ranked = sorted(timings_ms.items(), key=lambda kv: kv[1], reverse=True)
    dominant_layer, dominant_ms = ranked[0]
    dominant_pct = round(100.0 * dominant_ms / total_ms, 2) if total_ms > 0 else 0.0

    gpu_compute_ms = (
        timings_ms.get("forward_gpu", 0.0)
        + timings_ms.get("backward_gpu", 0.0)
        + timings_ms.get("loss_gpu", 0.0)
        + timings_ms.get("optimizer_gpu", 0.0)
    )
    gpu_compute_pct = round(100.0 * gpu_compute_ms / total_ms, 2) if total_ms > 0 else 0.0

    utilization_lie_detected = (
        nvidia_smi_util_pct >= 90.0
        and (gpu_compute_pct < 30.0 or kernel_launch_rate_hz < 0.2 * expected_launch_rate_hz)
    )
    smi_overhead_pct = round(100.0 * (1.0 - throughput_smi_poll / throughput_no_profiler), 2)
    nsys_overhead_pct = round(100.0 * (1.0 - throughput_nsys / throughput_no_profiler), 2)

    return {
        "total_ms": round(total_ms, 2),
        "dominant_layer": dominant_layer,
        "dominant_ms": round(dominant_ms, 2),
        "dominant_pct": dominant_pct,
        "gpu_compute_ms": round(gpu_compute_ms, 2),
        "gpu_compute_pct": gpu_compute_pct,
        "utilization_lie_detected": utilization_lie_detected,
        "smi_overhead_pct": smi_overhead_pct,
        "nsys_overhead_pct": nsys_overhead_pct,
        "heisenbug_risk": nsys_overhead_pct >= 25.0,
    }


def evaluate_thermal_power_ecc_health(
    temp_start_c: float,
    temp_end_c: float,
    window_s: float,
    throttle_reason: str,
    power_limit_w: float,
    default_power_limit_w: float,
    ecc_sbe_delta: int,
    ecc_window_minutes: float,
    uncorrectable_ecc_delta: int = 0,
) -> Dict[str, object]:
    """Disambiguate thermal vs power throttling and evaluate ECC error escalation rate.

    Models Volume 20 Chapters 05, 06, 08, 09 and Labs 02-04:
      - Temperature rise rate = (temp_end_c - temp_start_c) / window_s (normal 0.05-0.10 C/s;
        > 0.20 C/s indicates cooling/fan degradation, e.g. (83-55)/30 = 0.933 C/s).
      - Throttle reason bitmask disambiguates thermal (`HW Thermal Slowdown` / `SW Thermal Slowdown`)
        from software power cap (`SW Power Cap` with `power_limit_w < default_power_limit_w`)
        and platform PSU brownout (`HW Power Brake Slowdown`).
      - ECC rate per hour = ecc_sbe_delta * (60 / ecc_window_minutes).
        < 1/hr: monitor; 1-10/hr: warning; > 10/hr (e.g. 50 in 30 min = 100/hr or 50 in 10 min = 300/hr)
        or any uncorrectable ECC: STOP job and drain GPU immediately.
    """
    temp_rise_c_per_s = round((temp_end_c - temp_start_c) / max(window_s, 1e-6), 4)
    cooling_degraded = temp_rise_c_per_s > 0.20

    if "Thermal" in throttle_reason:
        clock_drop_cause = "thermal_slowdown"
    elif "Power Brake" in throttle_reason:
        clock_drop_cause = "psu_brownout_power_brake"
    elif "SW Power Cap" in throttle_reason and power_limit_w < default_power_limit_w:
        clock_drop_cause = "software_power_cap_below_default"
    else:
        clock_drop_cause = "none_or_undetermined_without_bitmask"

    ecc_rate_per_hour = round(ecc_sbe_delta * (60.0 / max(ecc_window_minutes, 1e-6)), 2)
    if uncorrectable_ecc_delta > 0 or ecc_rate_per_hour > 10.0:
        ecc_action = "stop_job_and_drain_gpu_immediately"
    elif ecc_rate_per_hour >= 1.0:
        ecc_action = "reduce_workload_and_schedule_replacement"
    else:
        ecc_action = "monitor_only"

    return {
        "temp_rise_c_per_s": temp_rise_c_per_s,
        "cooling_degraded": cooling_degraded,
        "clock_drop_cause": clock_drop_cause,
        "ecc_rate_per_hour": ecc_rate_per_hour,
        "ecc_action": ecc_action,
    }
