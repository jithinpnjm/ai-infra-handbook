#!/usr/bin/env python3
"""Chapter 12.13: Fabric design: topology, oversubscription and scale.

Deterministic reference models and calculators for AI data center fabric design:
- Training vs Inference vs Storage data center network associations (ADC Ch 3)
- Rail-Optimized Design (ROD), Rail-Only Design, and Rail-Unified Design (RUD)
- Leaf physical placement: Top-of-Rack (ToR), Middle-of-Row (MoR), End-of-Row (EoR) (Table 3-1)
- 3-stage Clos scaling with 64x400G (QM9700, 2,048 GPUs) and 144x800G (Q3400-RD, 9,216 GPUs)
  plus 256x400G chassis spine reduction (ADC Fig 3-9, 3-10; superpod-gb300-ra Table 3)
- 5-stage Clos scaling with 1,024-GPU blocks/bricks, 1:1 to 7:1 super-spine oversubscription
  (2,048 to 14,336 GPUs across 32 fixed 64x400G super-spines), and 16,384-GPU chassis super-spine
  (ADC Fig 3-11, 3-12, 3-13)
- Scheduled Fabric (64/128/256-byte cells + Virtual Output Queueing VOQ, Jericho3-AI/Ramon3 & Silicon One)
- Dragonfly (DF/DF+, full-graph vs Butterfly+ bipartite intra-group) and 1D/2D/3D Torus hop math
- Multi-Planar Scale-Out architectures (800G NIC -> 4x200G breakout across FP1..FP4, 64x800G ToR ->
  128x200G downlinks + 32x800G / 64x400G uplinks, shuffle cables, LPO/LRO DSP reduction)
- Production oversubscription, N-1 spine cut, 20:1 uplink imbalance, and shared-vs-separated VL/plane
  scenarios (V7 Ch 11, V8 Ch 6 & Ch 11, V9 Ch 10)
- Thermal, power efficiency, PUE, fan airflow directions, and 5 liquid cooling methods (ADC Ch 5)
- BCM 11 Topograph Slurm topology discovery parameters (bcm11-admin §7.5)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# 1. Constants from ADC Ch 3, ADC Ch 5, V7 Ch 11, V8 Ch 6/11, V9 Ch 10, BCM 11 §7.5
# ---------------------------------------------------------------------------

# Server & rack physical dimensions and power budgets (ADC Ch 3 & Ch 5)
STANDARD_RACK_WIDTH_IN: int = 19
STANDARD_RACK_DEPTH_IN: int = 36
STANDARD_RACK_HEIGHT_U: int = 42
DGX_H100_WIDTH_IN: int = 19
DGX_H100_DEPTH_IN: float = 35.3
DGX_H100_HEIGHT_U: int = 8
DGX_A100_HEIGHT_U: int = 6

TRADITIONAL_DC_RACK_POWER_MIN_KW: int = 10
TRADITIONAL_DC_RACK_POWER_MAX_KW: int = 25
TRADITIONAL_DC_RACK_AVG_MIN_KW: int = 16
TRADITIONAL_DC_RACK_AVG_MAX_KW: int = 25  # 16-18 kW in Ch 5, 20-25 kW in Ch 3
AI_DGX_H100_RACK_SERVERS_MIN: int = 4
AI_DGX_H100_RACK_SERVERS_MAX: int = 5
AI_DGX_H100_RACK_POWER_MIN_KW: int = 48
AI_DGX_H100_RACK_POWER_MAX_KW: int = 60

# DGX H100 PSU and switch/optics thermal constants (ADC Ch 5)
GLOBAL_DC_POWER_SHARE_PCT: float = 2.0
DGX_H100_PSU_COUNT: int = 6
DGX_H100_PSU_RATING_KW: float = 3.3
DGX_H100_ACTIVE_PSUS_4PLUS2: int = 4
DGX_H100_REDUNDANT_PSUS_4PLUS2: int = 2
DGX_H100_4PLUS2_POWER_KW: float = 13.2  # 4 * 3.3 kW (ADC Ch 5)
SWITCH_64X400G_QFX5230_POWER_KW: float = 3.0
OPTICS_QSFP28_MAX_W: float = 3.2
OPTICS_QSFP56_DD_MAX_W: float = 12.0
OPTICS_OSFP_MAX_W: float = 15.0

DC_IT_POWER_SHARE_MIN_PCT: int = 40
DC_IT_POWER_SHARE_MAX_PCT: int = 45
DC_COOLING_POWER_SHARE_MIN_PCT: int = 35
DC_COOLING_POWER_SHARE_MAX_PCT: int = 40
IDEAL_PUE: float = 1.0
LIQUID_COOLING_POWER_REDUCTION_PCT: float = 70.0
LIQUID_COOLING_MARKET_2026_USD_BILLIONS: float = 3.0
RDHX_RACK_COOLING_CAPACITY_KW: float = 20.0
SPRAYED_LIQUID_ENERGY_REDUCTION_PCT: float = 25.8

# Switch & topology constants (ADC Ch 3 & superpod-gb300-ra)
GPUS_PER_STANDARD_SERVER: int = 8
NVSWITCH_INTERNAL_BW_GBPS: int = 900
SWITCH_RADIX_64_400G: int = 64
SWITCH_RADIX_144_800G: int = 144
CHASSIS_SPINE_RADIX_256_400G: int = 256
CLOS_3STAGE_64PORT_MAX_GPUS: int = 2048
CLOS_3STAGE_144PORT_MAX_GPUS: int = 9216
CLOS_5STAGE_BLOCK_GPUS: int = 1024
CLOS_5STAGE_BLOCK_ROWS: int = 4
CLOS_5STAGE_FIXED_SUPER_SPINES: int = 32
CLOS_5STAGE_MAX_OVERSUB_RATIO: int = 7
CLOS_5STAGE_CHASSIS_MAX_GPUS: int = 16384

# Scheduled fabric cell sizes (ADC Ch 3)
SCHEDULED_FABRIC_CELL_SIZES_BYTES: Tuple[int, int, int] = (64, 128, 256)

# Multi-planar breakout constants (ADC Ch 3 Fig 3-36)
MULTI_PLANAR_NIC_BW_GBPS: int = 800
MULTI_PLANAR_PLANES: int = 4
MULTI_PLANAR_LANE_BW_GBPS: int = 200
MULTI_PLANAR_TOR_800G_PORTS: int = 64
MULTI_PLANAR_TOR_DOWNLINKS_200G: int = 128
MULTI_PLANAR_TOR_UPLINKS_800G: int = 32
MULTI_PLANAR_TOR_UPLINKS_400G: int = 64

# BCM 11 Topograph constants (bcm11-admin §7.5)
TOPOGRAPH_HTTPS_PORT: int = 49021
TOPOGRAPH_FETCH_TIMEOUT_S: int = 20
TOPOGRAPH_FETCH_ATTEMPTS: int = 12
TOPOGRAPH_FETCH_WAIT_S: int = 15
TOPOGRAPH_AGGREGATION_DELAY_S: int = 15
TOPOGRAPH_PAGE_SIZE: int = 100
TOPOGRAPH_PROMETHEUS_MEASURABLES: int = 26


# ---------------------------------------------------------------------------
# 2. Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RailDesignProfile:
    name: str
    code: str
    gpu_to_leaf_mapping: str
    intra_rail_network_hops: int
    inter_rail_network_hops: int  # 0 if handled only inside server NVSwitch
    single_leaf_failure_blast_radius: str
    requires_deterministic_path_forwarding: bool
    cabling_complexity: str


@dataclass(frozen=True)
class LeafPlacementProfile:
    placement: str
    rack_space_requirement: str
    power_requirement_per_compute_rack: str
    cooling_requirement_per_compute_rack: str
    cabling_within_compute_rack: bool
    max_cable_span_racks: int
    ideal_for_rud_with_dac_aec: bool


@dataclass(frozen=True)
class ClosScaleResult:
    stages: int
    switch_radix_ports: int
    port_speed_gbps: int
    rows_or_su_count: int
    blocks: int
    oversubscription_ratio: int
    total_servers: int
    total_gpus: int
    server_facing_ports: int
    spine_facing_ports: int
    super_spine_facing_ports: int
    leaf_switches: int
    spine_switches: int
    super_spine_switches: int
    chassis_spine_used: bool


@dataclass(frozen=True)
class ScheduledFabricAnalysis:
    packet_bytes: int
    cell_size_bytes: int
    cells_per_packet: int
    padded_wire_bytes: int
    cell_padding_overhead_pct: float
    voq_queues_Across_fabric: int
    hol_blocking_eliminated: bool


@dataclass(frozen=True)
class TopologyComparisonResult:
    topology: str
    total_endpoints: int
    degree_per_node_or_switch: int
    max_network_hops: int
    supports_global_adaptive_routing: bool
    primary_tradeoff: str


@dataclass(frozen=True)
class MultiPlanarBreakoutProfile:
    nic_speed_gbps: int
    fabric_planes: int
    breakout_lane_speed_gbps: int
    tor_native_800g_ports: int
    tor_server_downlinks_200g: int
    tor_spine_uplinks_800g: int
    tor_spine_uplinks_400g: int
    surviving_bw_pct_on_single_plane_loss: float
    requires_nic_ooo_reassembly: bool


@dataclass(frozen=True)
class OversubscriptionScenarioResult:
    scenario_name: str
    downlink_gbps: float
    uplink_gbps_normal: float
    uplink_gbps_degraded: float
    oversubscription_normal: float
    oversubscription_degraded: float
    effective_per_node_gbps: float
    allreduce_2gb_time_ms: float
    verdict: str


@dataclass(frozen=True)
class ThermalPowerBudgetResult:
    servers_per_rack: int
    server_power_kw: float
    switches_in_rack: int
    switch_chassis_power_kw: float
    optics_per_switch: int
    optic_power_w: float
    total_switch_plus_optics_kw: float
    total_rack_it_power_kw: float
    facility_pue: float
    total_facility_power_kw: float
    recommended_cooling_method: str


# ---------------------------------------------------------------------------
# 3. Core Modeling Functions
# ---------------------------------------------------------------------------

def compare_rail_designs() -> Dict[str, RailDesignProfile]:
    """Compare Rail-Optimized (ROD), Rail-Only, and Rail-Unified (RUD) designs (ADC Ch 3)."""
    return {
        "ROD": RailDesignProfile(
            name="Rail-Optimized Design",
            code="ROD",
            gpu_to_leaf_mapping="1:1 GPU i -> NIC i -> Leaf i (Rail i across 8 leaves per stripe)",
            intra_rail_network_hops=1,
            inter_rail_network_hops=2,
            single_leaf_failure_blast_radius="1 of 8 rails degraded (7/8 rails remain active per server)",
            requires_deterministic_path_forwarding=False,
            cabling_complexity="High across 8 racks in a row/stripe",
        ),
        "Rail-Only": RailDesignProfile(
            name="Rail-Only Design",
            code="Rail-Only",
            gpu_to_leaf_mapping="1:1 GPU i -> Leaf i with rail-isolated spines; no cross-rail fabric links",
            intra_rail_network_hops=1,
            inter_rail_network_hops=0,  # Cross-rail handled via internal 900 GB/s NVSwitch
            single_leaf_failure_blast_radius="Isolated strictly to 1 rail; zero cross-rail fault propagation",
            requires_deterministic_path_forwarding=False,
            cabling_complexity="Medium (no cross-rail spine mesh required)",
        ),
        "RUD": RailDesignProfile(
            name="Rail-Unified Design",
            code="RUD",
            gpu_to_leaf_mapping="All 8 NICs of a server to 1 leaf (or 4 NICs to each of 2 leaves); up to 4 servers/leaf",
            intra_rail_network_hops=1,  # 1 hop within the 4 servers on the same leaf; 2 hops via spine otherwise
            inter_rail_network_hops=2,
            single_leaf_failure_blast_radius="Entire server (all 8 GPUs) isolated if connected to a single leaf",
            requires_deterministic_path_forwarding=True,
            cabling_complexity="Low (intra-rack copper DAC or AEC cables)",
        ),
    }


def compare_leaf_placements() -> Dict[str, LeafPlacementProfile]:
    """Return ADC Ch 3 Table 3-1 leaf placement comparison for an 8-rack (32-server, 256-GPU) row."""
    return {
        "ToR": LeafPlacementProfile(
            placement="Top-of-Rack (ToR)",
            rack_space_requirement="Less",
            power_requirement_per_compute_rack="More",
            cooling_requirement_per_compute_rack="More",
            cabling_within_compute_rack=True,
            max_cable_span_racks=8,
            ideal_for_rud_with_dac_aec=True,
        ),
        "MoR": LeafPlacementProfile(
            placement="Middle-of-Row (MoR)",
            rack_space_requirement="More",
            power_requirement_per_compute_rack="Less",
            cooling_requirement_per_compute_rack="Less",
            cabling_within_compute_rack=False,
            max_cable_span_racks=6,
            ideal_for_rud_with_dac_aec=False,
        ),
        "EoR": LeafPlacementProfile(
            placement="End-of-Row (EoR)",
            rack_space_requirement="More",
            power_requirement_per_compute_rack="Less",
            cooling_requirement_per_compute_rack="Less",
            cabling_within_compute_rack=False,
            max_cable_span_racks=10,
            ideal_for_rud_with_dac_aec=False,
        ),
    }


def calculate_3stage_clos_scale(
    switch_radix_ports: int = 64,
    rows_or_su_count: int = 8,
    use_chassis_spine_256: bool = False,
) -> ClosScaleResult:
    """Calculate 3-stage (2-tier leaf-spine) Clos scaling (ADC Fig 3-9, 3-10 & superpod-gb300-ra Table 3).

    - 64x400G switches (32 down + 32 up):
      1 row = 256 GPUs (32 servers, 8 leaves, 4 spines)
      2 rows = 512 GPUs (64 servers, 16 leaves, 8 spines)
      4 rows = 1,024 GPUs (128 servers, 32 leaves, 16 spines) — V7 Ch 11 Scenario 1
      8 rows = 2,048 GPUs (256 servers, 64 leaves, 32 spines; or 8 spines with 256x400G chassis)
    - 144x800G switches (Q3400-RD, 72 down + 72 up, 8 leaves per 576-GPU SU):
      2 SUs = 1,152 GPUs (16 leaves, 8 spines)
      4 SUs = 2,304 GPUs (32 leaves, 18 spines)
      8 SUs = 4,608 GPUs (64 leaves, 36 spines)
      16 SUs = 9,216 GPUs (128 leaves, 72 spines)
    """
    if switch_radix_ports == 64:
        port_speed_gbps = 400
        gpus_per_row = 256
        servers_per_row = 32
        total_gpus = rows_or_su_count * gpus_per_row
        total_servers = rows_or_su_count * servers_per_row
        leaf_switches = rows_or_su_count * 8
        spine_port_capacity = CHASSIS_SPINE_RADIX_256_400G if use_chassis_spine_256 else 64
        spine_switches = total_gpus // spine_port_capacity
        return ClosScaleResult(
            stages=3,
            switch_radix_ports=switch_radix_ports,
            port_speed_gbps=port_speed_gbps,
            rows_or_su_count=rows_or_su_count,
            blocks=1,
            oversubscription_ratio=1,
            total_servers=total_servers,
            total_gpus=total_gpus,
            server_facing_ports=total_gpus,
            spine_facing_ports=total_gpus,
            super_spine_facing_ports=0,
            leaf_switches=leaf_switches,
            spine_switches=spine_switches,
            super_spine_switches=0,
            chassis_spine_used=use_chassis_spine_256,
        )
    if switch_radix_ports == 144:
        port_speed_gbps = 800
        gpus_per_su = 576  # 8 leaves * 72 downlinks
        trays_per_su = 144  # 144 four-GPU compute trays (or 8 NVL72 racks)
        total_gpus = rows_or_su_count * gpus_per_su
        total_servers = rows_or_su_count * trays_per_su
        leaf_switches = rows_or_su_count * 8
        if rows_or_su_count == 1:
            spine_switches = 4
        elif rows_or_su_count == 2:
            spine_switches = 8
        else:
            spine_switches = (rows_or_su_count * 9) // 2
        return ClosScaleResult(
            stages=3,
            switch_radix_ports=switch_radix_ports,
            port_speed_gbps=port_speed_gbps,
            rows_or_su_count=rows_or_su_count,
            blocks=1,
            oversubscription_ratio=1,
            total_servers=total_servers,
            total_gpus=total_gpus,
            server_facing_ports=total_gpus,
            spine_facing_ports=total_gpus,
            super_spine_facing_ports=0,
            leaf_switches=leaf_switches,
            spine_switches=spine_switches,
            super_spine_switches=0,
            chassis_spine_used=False,
        )
    raise ValueError(f"Unsupported switch_radix_ports: {switch_radix_ports}")


def calculate_5stage_clos_scale(
    oversubscription_ratio: int = 1,
    chassis_super_spine_target_gpus: int | None = None,
) -> ClosScaleResult:
    """Calculate 5-stage (3-tier leaf-spine-superspine) Clos scaling (ADC Fig 3-11, 3-12, 3-13).

    In ADC Fig 3-11 & 3-12:
    - 1 Block (Brick) = 4 Rows = 1,024 GPUs (32 leaf switches, 32 spine switches of 64x400G,
      1,024 server-facing ports, 1,024 spine-facing ports, 1,024 super-spine-facing ports).
    - With a fixed tier of 32 super-spine switches (64x400G = 2,048 super-spine ports):
      oversubscription k:1 (k in 1..7) supports:
      blocks = 2 * k
      rows = 8 * k
      GPUs = 2,048 * k (from 2,048 at 1:1 up to 14,336 at 7:1)
      leaf_switches = 64 * k
      spine_switches = 64 * k
      super_spine_facing_ports = 2,048 (constant)
    - In ADC Fig 3-13 (chassis-based super-spine at 1:1 oversubscription):
      scales 2,048 GPUs (2 blocks), 8,192 GPUs (8 blocks), and 16,384 GPUs (16 blocks = 64 rows)
      at 1:1 oversubscription with 16,384 super-spine-facing ports.
    """
    if chassis_super_spine_target_gpus is not None:
        if chassis_super_spine_target_gpus not in (2048, 8192, 16384):
            raise ValueError("Supported Fig 3-13 chassis_super_spine_target_gpus are 2048, 8192, 16384.")
        blocks = chassis_super_spine_target_gpus // CLOS_5STAGE_BLOCK_GPUS
        rows = blocks * CLOS_5STAGE_BLOCK_ROWS
        return ClosScaleResult(
            stages=5,
            switch_radix_ports=64,
            port_speed_gbps=400,
            rows_or_su_count=rows,
            blocks=blocks,
            oversubscription_ratio=1,
            total_servers=chassis_super_spine_target_gpus // GPUS_PER_STANDARD_SERVER,
            total_gpus=chassis_super_spine_target_gpus,
            server_facing_ports=chassis_super_spine_target_gpus,
            spine_facing_ports=chassis_super_spine_target_gpus,
            super_spine_facing_ports=chassis_super_spine_target_gpus,
            leaf_switches=blocks * 32,
            spine_switches=blocks * 32,
            super_spine_switches=CLOS_5STAGE_FIXED_SUPER_SPINES,
            chassis_spine_used=True,
        )

    if not (1 <= oversubscription_ratio <= CLOS_5STAGE_MAX_OVERSUB_RATIO):
        raise ValueError("oversubscription_ratio must be between 1 and 7 (ADC Fig 3-12).")

    blocks = 2 * oversubscription_ratio
    rows = blocks * CLOS_5STAGE_BLOCK_ROWS
    total_gpus = blocks * CLOS_5STAGE_BLOCK_GPUS
    return ClosScaleResult(
        stages=5,
        switch_radix_ports=64,
        port_speed_gbps=400,
        rows_or_su_count=rows,
        blocks=blocks,
        oversubscription_ratio=oversubscription_ratio,
        total_servers=total_gpus // GPUS_PER_STANDARD_SERVER,
        total_gpus=total_gpus,
        server_facing_ports=total_gpus,
        spine_facing_ports=total_gpus,
        super_spine_facing_ports=2048,
        leaf_switches=blocks * 32,
        spine_switches=blocks * 32,
        super_spine_switches=CLOS_5STAGE_FIXED_SUPER_SPINES,
        chassis_spine_used=False,
    )


def analyze_scheduled_fabric_cells(
    packet_bytes: int,
    cell_size_bytes: int,
    egress_endpoints: int = 1024,
    traffic_classes: int = 8,
) -> ScheduledFabricAnalysis:
    """Analyze Scheduled Fabric cell segmentation and VOQ scaling (ADC Ch 3 Fig 3-24).

    Supported cell sizes in ADC Ch 3: 64, 128, or 256 bytes (Cisco Silicon One,
    Broadcom Jericho3-AI / Ramon3).
    """
    if cell_size_bytes not in SCHEDULED_FABRIC_CELL_SIZES_BYTES:
        raise ValueError(f"cell_size_bytes must be one of {SCHEDULED_FABRIC_CELL_SIZES_BYTES}")
    if packet_bytes <= 0:
        raise ValueError("packet_bytes must be > 0")

    cells = math.ceil(packet_bytes / cell_size_bytes)
    padded_bytes = cells * cell_size_bytes
    overhead_pct = round(((padded_bytes - packet_bytes) / packet_bytes) * 100.0, 2)
    return ScheduledFabricAnalysis(
        packet_bytes=packet_bytes,
        cell_size_bytes=cell_size_bytes,
        cells_per_packet=cells,
        padded_wire_bytes=padded_bytes,
        cell_padding_overhead_pct=overhead_pct,
        voq_queues_Across_fabric=egress_endpoints * traffic_classes,
        hol_blocking_eliminated=True,
    )


def compare_scale_out_topologies(
    torus_dim_size: int = 8,
) -> Dict[str, TopologyComparisonResult]:
    """Compare 5-stage Clos, Dragonfly (DF/DF+), and 1D/2D/3D Torus topologies (ADC Ch 3)."""
    return {
        "Clos_5Stage": TopologyComparisonResult(
            topology="5-Stage Clos (Leaf-Spine-SuperSpine)",
            total_endpoints=14336,
            degree_per_node_or_switch=64,
            max_network_hops=4,  # Leaf -> Spine -> Super-Spine -> Spine -> Leaf (4 switch-to-switch hops)
            supports_global_adaptive_routing=True,
            primary_tradeoff="Uniform non-blocking/bounded oversubscription, but high optics count and 3-tier hop latency",
        ),
        "Dragonfly_DF_Plus": TopologyComparisonResult(
            topology="Dragonfly (DF / DF+ with Clos/Butterfly+ intra-group & full-mesh inter-group)",
            total_endpoints=16384,
            degree_per_node_or_switch=64,
            max_network_hops=3,  # Intra-group local -> 1 global inter-group link -> intra-group remote
            supports_global_adaptive_routing=True,
            primary_tradeoff="Lower network diameter, latency, and inter-group fiber cost than 5-stage Clos; requires UGAL/adaptive routing",
        ),
        "Torus_1D": TopologyComparisonResult(
            topology="1D Torus (Ring with wrap-around)",
            total_endpoints=torus_dim_size,
            degree_per_node_or_switch=2,
            max_network_hops=torus_dim_size // 2,
            supports_global_adaptive_routing=False,
            primary_tradeoff="2 links per node; minimal switch cost, suitable for 1D inter-leaf rail rings (Fig 3-35)",
        ),
        "Torus_2D": TopologyComparisonResult(
            topology="2D Torus (X, Y grid with wrap-around)",
            total_endpoints=torus_dim_size ** 2,
            degree_per_node_or_switch=4,
            max_network_hops=2 * (torus_dim_size // 2),
            supports_global_adaptive_routing=True,
            primary_tradeoff="4 links per node; high nearest-neighbor efficiency",
        ),
        "Torus_3D": TopologyComparisonResult(
            topology="3D Torus (X, Y, Z cube with wrap-around)",
            total_endpoints=torus_dim_size ** 3,
            degree_per_node_or_switch=6,
            max_network_hops=3 * (torus_dim_size // 2),
            supports_global_adaptive_routing=True,
            primary_tradeoff="6 links per node; cost-effective at scale for 3D nearest-neighbor jobs, higher arbitrary-pair hop count",
        ),
    }


def evaluate_multi_planar_breakout(
    failed_planes: int = 0,
) -> MultiPlanarBreakoutProfile:
    """Evaluate ADC Ch 3 Fig 3-36..3-39 Multi-Planar 800G -> 4x200G breakout architecture."""
    if not (0 <= failed_planes <= MULTI_PLANAR_PLANES):
        raise ValueError("failed_planes must be between 0 and 4")
    surviving_pct = round(((MULTI_PLANAR_PLANES - failed_planes) / MULTI_PLANAR_PLANES) * 100.0, 2)
    return MultiPlanarBreakoutProfile(
        nic_speed_gbps=MULTI_PLANAR_NIC_BW_GBPS,
        fabric_planes=MULTI_PLANAR_PLANES,
        breakout_lane_speed_gbps=MULTI_PLANAR_LANE_BW_GBPS,
        tor_native_800g_ports=MULTI_PLANAR_TOR_800G_PORTS,
        tor_server_downlinks_200g=MULTI_PLANAR_TOR_DOWNLINKS_200G,
        tor_spine_uplinks_800g=MULTI_PLANAR_TOR_UPLINKS_800G,
        tor_spine_uplinks_400g=MULTI_PLANAR_TOR_UPLINKS_400G,
        surviving_bw_pct_on_single_plane_loss=surviving_pct,
        requires_nic_ooo_reassembly=True,
    )


def evaluate_oversubscription_and_cut_scenarios() -> Dict[str, OversubscriptionScenarioResult]:
    """Evaluate the production oversubscription and cut scenarios from V7 Ch 11, V8 Ch 6, and V9 Ch 10.

    1. V7 Ch 11 Scenario 1: 128 DGX H100 (1,024 GPUs) on 64-port 400G NDR switches at 1:1 non-blocking
       (32 downlinks = 12,800 Gbps, 32 uplinks = 12,800 Gbps -> 400 Gbps/node, 2 GB AllReduce = 40.0 ms).
    2. V7 Ch 11 Scenario 2 & V8 Ch 6 Worked Example: 2:1 leaf oversubscription (16 downlinks @ 400G = 6,400 Gbps,
       8 uplinks @ 400G = 3,200 Gbps -> 200 Gbps/node effective, 2 GB AllReduce jumps from 40.0 ms to 80.0 ms;
       if 1 of 2 spines fails, 4 uplinks = 1,600 Gbps -> 4:1 oversubscription, 100 Gbps/node).
       Matches V8 Ch 6 Scenario 3 paired ib_write_bw: 397.62 Gbps same-leaf vs 201.18 Gbps cross-rack.
    3. V9 Ch 10 Rack Cut: 16 nodes x 800 Gbps = 12,800 Gbps downlink; 8x400G uplinks = 3,200 Gbps (4.00:1 normal),
       N-1 single uplink failure -> 7x400G = 2,800 Gbps (4.57:1 degraded).
    """
    return {
        "V7_1024GPU_NonBlocking_1to1": OversubscriptionScenarioResult(
            scenario_name="V7 Ch 11 Scenario 1: 1,024-GPU Non-Blocking Fat-Tree (32 down : 32 up @ 400G)",
            downlink_gbps=12800.0,
            uplink_gbps_normal=12800.0,
            uplink_gbps_degraded=12400.0,
            oversubscription_normal=1.0,
            oversubscription_degraded=round(12800.0 / 12400.0, 2),
            effective_per_node_gbps=400.0,
            allreduce_2gb_time_ms=40.0,
            verdict="NON_BLOCKING_1_TO_1",
        ),
        "V7_V8_Leaf_2to1_Oversubscribed": OversubscriptionScenarioResult(
            scenario_name="V7 Ch 11 Scenario 2 & V8 Ch 6: 2:1 Oversubscribed Leaf (16 down : 8 up @ 400G, 1-spine loss -> 4:1)",
            downlink_gbps=6400.0,
            uplink_gbps_normal=3200.0,
            uplink_gbps_degraded=1600.0,
            oversubscription_normal=2.0,
            oversubscription_degraded=4.0,
            effective_per_node_gbps=200.0,
            allreduce_2gb_time_ms=80.0,
            verdict="BOTTLENECK_2_TO_1_DOUBLES_ALLREDUCE_TIME",
        ),
        "V9_Rack_4to1_And_N_Minus_1": OversubscriptionScenarioResult(
            scenario_name="V9 Ch 10 Rack Cut: 16x800G Downlinks (12,800G) vs 8x400G Uplinks (3,200G -> 4.00:1; 7x400G -> 4.57:1)",
            downlink_gbps=12800.0,
            uplink_gbps_normal=3200.0,
            uplink_gbps_degraded=2800.0,
            oversubscription_normal=4.0,
            oversubscription_degraded=round(12800.0 / 2800.0, 2),
            effective_per_node_gbps=200.0,
            allreduce_2gb_time_ms=80.0,
            verdict="OVERSUBSCRIBED_4_TO_1_N_MINUS_1_4_57_TO_1",
        ),
    }


def calculate_rack_thermal_and_power_budget(
    servers_per_rack: int = 4,
    server_power_kw: float = DGX_H100_4PLUS2_POWER_KW,
    switches_in_rack: int = 1,
    switch_chassis_power_kw: float = SWITCH_64X400G_QFX5230_POWER_KW,
    optics_per_switch: int = 64,
    optic_power_w: float = OPTICS_OSFP_MAX_W,
    facility_pue: float = 1.25,
) -> ThermalPowerBudgetResult:
    """Calculate rack IT power, switch + optics thermal load, PUE, and cooling tier (ADC Ch 3 & Ch 5)."""
    optics_kw_per_switch = (optics_per_switch * optic_power_w) / 1000.0
    total_switch_kw = switches_in_rack * (switch_chassis_power_kw + optics_kw_per_switch)
    total_it_kw = round((servers_per_rack * server_power_kw) + total_switch_kw, 3)
    total_facility_kw = round(total_it_kw * facility_pue, 3)

    if total_it_kw <= RDHX_RACK_COOLING_CAPACITY_KW:
        cooling = "Air Cooling (Front-to-Back) or Rear-Door Heat Exchanger (RDHx <= 20 kW)"
    elif total_it_kw <= 60.0:
        cooling = "Direct-to-Chip Cold Plate Liquid Cooling (with RDHx/Air for switches & optics)"
    else:
        cooling = "Direct-to-Chip Cold Plate or Single/Two-Phase Immersion Liquid Cooling (>60 kW)"

    return ThermalPowerBudgetResult(
        servers_per_rack=servers_per_rack,
        server_power_kw=server_power_kw,
        switches_in_rack=switches_in_rack,
        switch_chassis_power_kw=switch_chassis_power_kw,
        optics_per_switch=optics_per_switch,
        optic_power_w=optic_power_w,
        total_switch_plus_optics_kw=round(total_switch_kw, 3),
        total_rack_it_power_kw=total_it_kw,
        facility_pue=facility_pue,
        total_facility_power_kw=total_facility_kw,
        recommended_cooling_method=cooling,
    )


if __name__ == "__main__":
    clos_2k = calculate_3stage_clos_scale(64, 8)
    print(f"3-Stage 64x400G max scale: {clos_2k.total_gpus} GPUs ({clos_2k.leaf_switches} leaves, {clos_2k.spine_switches} spines)")
    clos_14k = calculate_5stage_clos_scale(oversubscription_ratio=7)
    print(f"5-Stage 64x400G 7:1 scale: {clos_14k.total_gpus} GPUs ({clos_14k.blocks} blocks, {clos_14k.super_spine_switches} super-spines)")
