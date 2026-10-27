"""Chapter 12.10: HDR, NDR, XDR, Optics, and Cabling.

Pure-stdlib deterministic models covering:
1. InfiniBand link generations (SDR, DDR, QDR, FDR, EDR, HDR, NDR, XDR, GDR):
   per-lane raw baud/bit rate, line coding (8b/10b, 64b/66b, 256b/257b),
   4x and 12x effective bandwidth, negotiated lane width degradation (4X vs 2X),
   RDMA message transfer time penalties, and PCIe host-injection ceilings.
2. AI server scale-up (NVLink Volta -> Blackwell) vs scale-out (A100, H100,
   GB300) port/breakout topologies and Dell'Oro 2020-2029 optics adoption shares.
3. SerDes mux/demux lane mapping (50G, 100G, 200G SerDes), NRZ (PAM-2, 1 bit/sym)
   vs PAM-4 (2 bits/sym, 4 levels, 3 eye openings, ~9.54 dB SNR penalty), and
   DSP functions (FFE/DFE equalization, CDR, LDPC/BCH FEC).
4. Optical fiber grades (MMF OM1-OM5 62.5/50 um @ 850/953/1300 nm vs SMF 8-10 um
   @ 1310/1550 nm and coherent DWDM) and ADC Table 4-1 transceiver types
   (VR, SR, DR, FR, LR, ZR, CR).
5. Connectors (LC vs MPO-8/12/16/24/32, UPC vs APC), cable assemblies (Passive
   DAC, Active DAC, AEC, AOC), twin-port OSFP breakout fan-out rules, and the
   NVIDIA SuperPOD <90% maximum cable length derating rule (27 m on 30 m AOC,
   45 m on 50 m AOC, 2.7 m on 3 m DAC, no patch panels).
6. Form factors (ADC Tables 4-2 & 4-3: QSFP28, QSFP56, QSFP-DD Type 1/2/2A/2B,
   OSFP, CFP/CFP2/CFP4/CFP8) and Pluggable vs LPO vs LRO vs CPO power & BOM math.
7. mlxlink (-c / -m) physical layer BER, per-lane error, CDR, and DDM optical
   power/temperature health evaluation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 1. InfiniBand Link Generations, Width Degradation & Host Injection Ceilings
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InfiniBandGenerationSpec:
    """InfiniBand generation parameters from Supercomputers for Linux SysAdmins Table 5-1."""

    generation: str
    raw_lane_rate_gbps: float
    coding_data_bits: int
    coding_total_bits: int
    modulation: str
    nominal_4x_bw_gbps: float
    nominal_12x_bw_gbps: float

    @property
    def coding_label(self) -> str:
        return f"{self.coding_data_bits}/{self.coding_total_bits}"

    @property
    def coding_efficiency(self) -> float:
        return self.coding_data_bits / self.coding_total_bits


IB_GENERATION_TABLE: Dict[str, InfiniBandGenerationSpec] = {
    "SDR": InfiniBandGenerationSpec("SDR", 2.5, 8, 10, "NRZ", 8.0, 24.0),
    "DDR": InfiniBandGenerationSpec("DDR", 5.0, 8, 10, "NRZ", 16.0, 48.0),
    "QDR": InfiniBandGenerationSpec("QDR", 10.0, 8, 10, "NRZ", 32.0, 96.0),
    "FDR": InfiniBandGenerationSpec("FDR", 14.0625, 64, 66, "NRZ", 54.4, 163.2),
    "EDR": InfiniBandGenerationSpec("EDR", 25.78125, 64, 66, "NRZ", 100.0, 300.0),
    "HDR": InfiniBandGenerationSpec("HDR", 53.125, 64, 66, "PAM4", 200.0, 600.0),
    "NDR": InfiniBandGenerationSpec("NDR", 106.25, 256, 257, "PAM4", 400.0, 1200.0),
    "XDR": InfiniBandGenerationSpec("XDR", 200.0, 256, 257, "PAM4", 800.0, 2400.0),
    "GDR": InfiniBandGenerationSpec("GDR", 400.0, 256, 257, "PAM4", 1600.0, 4800.0),
}


@dataclass(frozen=True)
class LinkNegotiationResult:
    """Evaluated InfiniBand link capacity, width state, and PCIe ceiling."""

    generation: str
    designed_lanes: int
    active_lanes: int
    raw_lane_rate_gbps: float
    symbol_rate_gbaud: float
    bits_per_symbol: int
    raw_aggregate_gbps: float
    coding_efficiency: float
    nominal_link_bw_gbps: float
    negotiated_link_bw_gbps: float
    pcie_ceiling_gbps: float
    delivered_payload_bw_gbps: float
    bottleneck_stage: str
    rdma_2mib_transfer_us: float


def evaluate_ib_link_negotiation(
    generation: str,
    designed_lanes: int = 4,
    active_lanes: int = 4,
    negotiated_rate_override_gbps: float | None = None,
    pcie_gen: int = 5,
    pcie_lanes: int = 16,
    protocol_efficiency: float = 1.0,
) -> LinkNegotiationResult:
    """Compute effective bandwidth across lane width, rate, coding, and PCIe slot."""
    if generation not in IB_GENERATION_TABLE:
        raise ValueError(f"Unknown InfiniBand generation: {generation}")
    if designed_lanes <= 0 or active_lanes < 0 or active_lanes > designed_lanes:
        raise ValueError("Invalid lane counts")

    spec = IB_GENERATION_TABLE[generation]
    bits_per_symbol = 2 if spec.modulation == "PAM4" else 1
    symbol_rate_gbaud = spec.raw_lane_rate_gbps / bits_per_symbol
    raw_aggregate_gbps = spec.raw_lane_rate_gbps * active_lanes

    per_lane_nominal = spec.nominal_4x_bw_gbps / 4.0
    nominal_link_bw_gbps = per_lane_nominal * designed_lanes

    if negotiated_rate_override_gbps is not None:
        base_rate_gbps = negotiated_rate_override_gbps
    else:
        base_rate_gbps = nominal_link_bw_gbps

    negotiated_link_bw_gbps = base_rate_gbps * (active_lanes / designed_lanes)

    # PCIe per-lane raw rates (GT/s) and encoding: Gen3/4/5 use 128b/130b; Gen6 PAM4 FLIT
    pcie_raw_gt_s = {3: 8.0, 4: 16.0, 5: 32.0, 6: 64.0}[pcie_gen]
    pcie_eff = (128.0 / 130.0) if pcie_gen in (3, 4, 5) else (242.0 / 256.0)
    pcie_ceiling_gbps = round(pcie_raw_gt_s * pcie_lanes * pcie_eff, 2)

    effective_link_payload = negotiated_link_bw_gbps * protocol_efficiency
    delivered_payload_bw_gbps = round(min(effective_link_payload, pcie_ceiling_gbps), 2)

    if active_lanes == 0:
        bottleneck_stage = "LINK_DOWN"
    elif negotiated_rate_override_gbps is not None and negotiated_rate_override_gbps < nominal_link_bw_gbps:
        bottleneck_stage = "RATE_DOWN_NEGOTIATION"
    elif active_lanes < designed_lanes:
        bottleneck_stage = "LANE_WIDTH_DEGRADATION"
    elif pcie_ceiling_gbps < effective_link_payload:
        bottleneck_stage = "HOST_PCIE_INJECTION_CEILING"
    else:
        bottleneck_stage = "FULL_DESIGN_RATE"

    # 2 MiB = 2 * 1024 * 1024 bytes = 2,097,152 bytes = 16,777,216 bits
    two_mib_bits = 2 * 1024 * 1024 * 8
    if delivered_payload_bw_gbps > 0:
        # 1 Gbps = 10^9 bits/s = 10^3 bits/us
        rdma_2mib_transfer_us = round(two_mib_bits / (delivered_payload_bw_gbps * 1000.0), 2)
    else:
        rdma_2mib_transfer_us = float("inf")

    return LinkNegotiationResult(
        generation=generation,
        designed_lanes=designed_lanes,
        active_lanes=active_lanes,
        raw_lane_rate_gbps=spec.raw_lane_rate_gbps,
        symbol_rate_gbaud=symbol_rate_gbaud,
        bits_per_symbol=bits_per_symbol,
        raw_aggregate_gbps=round(raw_aggregate_gbps, 4),
        coding_efficiency=round(spec.coding_efficiency, 6),
        nominal_link_bw_gbps=round(nominal_link_bw_gbps, 2),
        negotiated_link_bw_gbps=round(negotiated_link_bw_gbps, 2),
        pcie_ceiling_gbps=pcie_ceiling_gbps,
        delivered_payload_bw_gbps=delivered_payload_bw_gbps,
        bottleneck_stage=bottleneck_stage,
        rdma_2mib_transfer_us=rdma_2mib_transfer_us,
    )


# ---------------------------------------------------------------------------
# 2. Scale-Up NVLink vs Scale-Out Optics & Dell'Oro Market Adoption
# ---------------------------------------------------------------------------

NVLINK_GENERATION_BW_GBPS: Dict[str, int] = {
    "Volta": 300,
    "Ampere": 600,
    "Hopper": 900,
    "Blackwell": 1800,
}

# Dell'Oro 2020-2027 AI cluster optics adoption percentages (ADC Figure 4-2)
DELLORO_2020_2027_SHARES: Dict[int, Dict[str, int]] = {
    2020: {"100G": 55, "200G": 30, "400G": 15, "800G": 0, "1600G": 0},
    2021: {"100G": 40, "200G": 35, "400G": 25, "800G": 0, "1600G": 0},
    2022: {"100G": 25, "200G": 40, "400G": 35, "800G": 0, "1600G": 0},
    2023: {"100G": 10, "200G": 30, "400G": 50, "800G": 10, "1600G": 0},
    2024: {"100G": 5, "200G": 10, "400G": 55, "800G": 30, "1600G": 0},
    2025: {"100G": 2, "200G": 5, "400G": 10, "800G": 70, "1600G": 13},
    2026: {"100G": 1, "200G": 3, "400G": 5, "800G": 45, "1600G": 46},
    2027: {"100G": 1, "200G": 2, "400G": 3, "800G": 30, "1600G": 64},
}

# Dell'Oro 2025 update (2025e, 2027e, 2029e) port shipment share % (ADC Figure 4-2.1)
DELLORO_2025_REPORT_SHARES: Dict[str, Dict[str, int]] = {
    "2025e": {"<=100G": 2, "200G": 3, "400G": 25, "800G": 70, "1600G": 0, ">=3200G": 0},
    "2027e": {"<=100G": 1, "200G": 2, "400G": 4, "800G": 43, "1600G": 50, ">=3200G": 0},
    "2029e": {"<=100G": 1, "200G": 1, "400G": 2, "800G": 16, "1600G": 50, ">=3200G": 30},
}


# ---------------------------------------------------------------------------
# 3. SerDes Mux/Demux Ratios & NRZ vs PAM4 DSP Signal Processing
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SerDesMuxDemuxPlan:
    """Mapping between PFE ASIC SerDes lanes and optical module lanes."""

    optics_rate_gbps: int
    asic_serdes_rate_gbps: int
    asic_serdes_lanes: int
    optical_lane_rate_gbps: int
    optical_lanes: int
    mux_ratio: str
    modulation: str
    bits_per_symbol: int
    voltage_levels: int
    eye_openings: int
    snr_penalty_vs_nrz_db: float


def plan_serdes_mux_demux(
    optics_rate_gbps: int,
    asic_serdes_rate_gbps: int,
    optical_lane_rate_gbps: int,
    modulation: str = "PAM4",
) -> SerDesMuxDemuxPlan:
    """Compute ASIC SerDes lane count, optical lane count, mux ratio, and PAM4 eye metrics."""
    if optics_rate_gbps % asic_serdes_rate_gbps != 0:
        raise ValueError("Optics rate must be an integer multiple of ASIC SerDes rate")
    if optics_rate_gbps % optical_lane_rate_gbps != 0:
        raise ValueError("Optics rate must be an integer multiple of optical lane rate")

    asic_lanes = optics_rate_gbps // asic_serdes_rate_gbps
    opt_lanes = optics_rate_gbps // optical_lane_rate_gbps
    gcd_val = math.gcd(asic_lanes, opt_lanes)
    mux_ratio = f"{asic_lanes // gcd_val}:{opt_lanes // gcd_val}"

    if modulation == "NRZ":
        bits_per_symbol = 1
        voltage_levels = 2
        eye_openings = 1
        snr_penalty_db = 0.0
    elif modulation == "PAM4":
        bits_per_symbol = 2
        voltage_levels = 4
        eye_openings = 3
        # 3 vertical eye openings each 1/3 amplitude of NRZ -> 20*log10(3) = 9.54 dB
        snr_penalty_db = round(20.0 * math.log10(3.0), 2)
    elif modulation == "PAM8":
        bits_per_symbol = 3
        voltage_levels = 8
        eye_openings = 7
        snr_penalty_db = round(20.0 * math.log10(7.0), 2)
    else:
        raise ValueError(f"Unsupported modulation: {modulation}")

    return SerDesMuxDemuxPlan(
        optics_rate_gbps=optics_rate_gbps,
        asic_serdes_rate_gbps=asic_serdes_rate_gbps,
        asic_serdes_lanes=asic_lanes,
        optical_lane_rate_gbps=optical_lane_rate_gbps,
        optical_lanes=opt_lanes,
        mux_ratio=mux_ratio,
        modulation=modulation,
        bits_per_symbol=bits_per_symbol,
        voltage_levels=voltage_levels,
        eye_openings=eye_openings,
        snr_penalty_vs_nrz_db=snr_penalty_db,
    )


# ---------------------------------------------------------------------------
# 4. Fiber Grades (MMF OM1-OM5 vs SMF) & ADC Table 4-1 Transceiver Types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FiberGradeSpec:
    """Multi-Mode Fiber (OM1-OM5) and Single-Mode Fiber (SMF) specifications (ADC Ch 4)."""

    grade: str
    mode: str
    core_diameter_um: Tuple[float, ...]
    wavelengths_nm: Tuple[int, ...]
    max_reach_1g_m: int
    max_reach_10g_m: int
    max_reach_40g_m: int
    max_reach_100g_400g_m: int
    light_source: str


FIBER_GRADE_SPECS: Dict[str, FiberGradeSpec] = {
    "OM1": FiberGradeSpec("OM1", "MMF", (62.5,), (850, 1300), 300, 33, 0, 0, "LED/VCSEL"),
    "OM2": FiberGradeSpec("OM2", "MMF", (50.0,), (850, 1300), 550, 82, 0, 0, "LED/VCSEL"),
    "OM3": FiberGradeSpec("OM3", "MMF", (50.0,), (850, 1300), 1000, 300, 240, 100, "VCSEL"),
    "OM4": FiberGradeSpec("OM4", "MMF", (50.0,), (850, 1300), 1000, 400, 300, 150, "VCSEL"),
    "OM5": FiberGradeSpec("OM5", "MMF", (50.0,), (850, 953), 1000, 400, 400, 150, "SWDM VCSEL"),
    "SMF": FiberGradeSpec("SMF", "SMF", (8.0, 10.0), (1310, 1550), 10000, 10000, 10000, 10000, "Laser"),
}


@dataclass(frozen=True)
class TransceiverTypeSpec:
    """ADC Chapter 4 Table 4-1 Transceiver Types."""

    code: str
    full_form: str
    max_reach_m: int
    mode: str
    typical_connector: str


ADC_TABLE_4_1_TRANSCEIVERS: Dict[str, TransceiverTypeSpec] = {
    "VR": TransceiverTypeSpec("VR", "Very short reach", 50, "MMF", "MPO-12 / MPO-16"),
    "SR": TransceiverTypeSpec("SR", "Short reach", 100, "MMF", "MPO-12 / MPO-16"),
    "DR": TransceiverTypeSpec("DR", "Data center reach", 500, "SMF", "MPO-12 / MPO-16"),
    "FR": TransceiverTypeSpec("FR", "Far reach", 2000, "SMF", "Dual LC (Duplex)"),
    "LR": TransceiverTypeSpec("LR", "Long reach", 10000, "SMF", "Dual LC (Duplex)"),
    "ZR": TransceiverTypeSpec("ZR", "Extended reach", 80000, "DWDM", "Dual LC (Coherent)"),
    "CR_PASSIVE": TransceiverTypeSpec("CR_PASSIVE", "Copper (Passive DAC)", 7, "Copper", "QSFP/OSFP DAC"),
    "CR_ACTIVE": TransceiverTypeSpec("CR_ACTIVE", "Copper (Active DAC)", 10, "Copper", "QSFP/OSFP Active DAC"),
}


def select_transceiver_and_fiber(
    distance_m: float,
    data_rate_gbps: int = 400,
    prefer_copper_in_rack: bool = True,
) -> Dict[str, object]:
    """Select the lowest-cost standards-compliant transceiver and media for a distance."""
    if distance_m <= 0:
        raise ValueError("Distance must be positive")

    # Apply SuperPOD 90% derating check alongside standard reach
    if prefer_copper_in_rack and distance_m <= 3.0 and data_rate_gbps <= 400:
        return {
            "transceiver": "CR_PASSIVE",
            "media": "Passive DAC (<0.15 W)",
            "max_standard_reach_m": 7 if data_rate_gbps <= 100 else 3,
            "connector": "Integrated QSFP-DD / OSFP",
        }
    if prefer_copper_in_rack and distance_m <= 7.0 and data_rate_gbps <= 800:
        return {
            "transceiver": "AEC / CR_PASSIVE",
            "media": "Active Electrical Cable (AEC) or DAC",
            "max_standard_reach_m": 7,
            "connector": "Integrated QSFP-DD / OSFP",
        }
    if distance_m <= 50.0:
        return {
            "transceiver": "VR",
            "media": "MMF (OM4/OM5) or AOC",
            "max_standard_reach_m": 50,
            "connector": "MPO-12 / MPO-16",
        }
    if distance_m <= 100.0:
        return {
            "transceiver": "SR",
            "media": "MMF (OM3/OM4/OM5) or AOC",
            "max_standard_reach_m": 100,
            "connector": "MPO-16 (400G-SR8) or MPO-12 (400G-SR4)",
        }
    if distance_m <= 500.0:
        return {
            "transceiver": "DR",
            "media": "SMF (8-10 um core, 1310 nm)",
            "max_standard_reach_m": 500,
            "connector": "MPO-12 (4 Tx + 4 Rx parallel SMF)",
        }
    if distance_m <= 2000.0:
        return {
            "transceiver": "FR",
            "media": "SMF (CWDM4/FR4 over 2 fibers)",
            "max_standard_reach_m": 2000,
            "connector": "Dual LC (Duplex SMF)",
        }
    if distance_m <= 10000.0:
        return {
            "transceiver": "LR",
            "media": "SMF (1310/1550 nm LWDM/LR4)",
            "max_standard_reach_m": 10000,
            "connector": "Dual LC (Duplex SMF)",
        }
    return {
        "transceiver": "ZR",
        "media": "SMF Coherent DWDM (1550 nm)",
        "max_standard_reach_m": 80000,
        "connector": "Dual LC (Coherent DWDM)",
    }


# ---------------------------------------------------------------------------
# 5. MPO Breakout Fan-Out & SuperPOD <90% Cable Length Derating Rule
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MPOBreakoutPlan:
    """MPO connector fiber allocation and twin-port OSFP breakout mapping."""

    module_name: str
    mpo_variant: str
    total_fibers: int
    tx_fibers: int
    rx_fibers: int
    dark_fibers: int
    switch_port_rate_gbps: int
    breakout_branches: int
    endpoint_port_rate_gbps: int
    lanes_per_endpoint: int


def evaluate_mpo_breakout(
    module_name: str,
    mpo_total_fibers: int,
    active_lanes: int,
    switch_port_rate_gbps: int,
    breakout_branches: int,
) -> MPOBreakoutPlan:
    """Calculate Tx/Rx/dark fiber counts in MPO-8/12/16/24/32 and breakout port speeds."""
    if mpo_total_fibers not in (8, 12, 16, 24, 32):
        raise ValueError(f"Unsupported MPO fiber count: {mpo_total_fibers}")
    tx_fibers = active_lanes
    rx_fibers = active_lanes
    if tx_fibers + rx_fibers > mpo_total_fibers:
        raise ValueError("Active Tx+Rx fibers exceed MPO connector fiber count")
    dark_fibers = mpo_total_fibers - (tx_fibers + rx_fibers)
    if switch_port_rate_gbps % breakout_branches != 0 or active_lanes % breakout_branches != 0:
        raise ValueError("Switch port rate and active lanes must divide evenly by breakout branches")

    mpo_label = f"MPO-{mpo_total_fibers}" if mpo_total_fibers != 32 else "MPO-32 (2x16)"
    return MPOBreakoutPlan(
        module_name=module_name,
        mpo_variant=mpo_label,
        total_fibers=mpo_total_fibers,
        tx_fibers=tx_fibers,
        rx_fibers=rx_fibers,
        dark_fibers=dark_fibers,
        switch_port_rate_gbps=switch_port_rate_gbps,
        breakout_branches=breakout_branches,
        endpoint_port_rate_gbps=switch_port_rate_gbps // breakout_branches,
        lanes_per_endpoint=active_lanes // breakout_branches,
    )


def evaluate_superpod_cable_derating(
    media_type: str,
    standard_max_reach_m: float,
    planned_run_m: float,
    uses_patch_panel: bool = False,
    derating_factor: float = 0.90,
) -> Dict[str, object]:
    """Enforce NVIDIA SuperPOD <90% max cable distance rule and no-patch-panel rule."""
    max_allowed_run_m = round(standard_max_reach_m * derating_factor, 2)
    margin_m = round(max_allowed_run_m - planned_run_m, 2)
    within_90pct_rule = planned_run_m <= max_allowed_run_m
    is_compliant = within_90pct_rule and (not uses_patch_panel)

    if uses_patch_panel:
        reason = "NON_COMPLIANT_PATCH_PANEL_ATTENUATION"
    elif not within_90pct_rule:
        reason = "EXCEEDS_90PCT_MAX_DISTANCE_RULE"
    else:
        reason = "COMPLIANT"

    return {
        "media_type": media_type,
        "standard_max_reach_m": standard_max_reach_m,
        "max_allowed_run_m": max_allowed_run_m,
        "planned_run_m": planned_run_m,
        "margin_m": margin_m,
        "uses_patch_panel": uses_patch_panel,
        "within_90pct_rule": within_90pct_rule,
        "is_compliant": is_compliant,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# 6. Form Factors (ADC Tables 4-2 & 4-3) & Pluggable vs LPO vs LRO vs CPO
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FormFactorSpec:
    """ADC Chapter 4 Table 4-2 & Table 4-3 form factor specifications."""

    name: str
    standard: str
    max_data_rate_gbps: int
    channels: int
    per_channel_gbps: int
    modulation: str
    ports_per_ru: int
    connectors: Tuple[str, ...]
    backward_compatible_with: Tuple[str, ...]


FORM_FACTOR_TABLE: Dict[str, FormFactorSpec] = {
    "QSFP28": FormFactorSpec(
        "QSFP28", "IEEE 802.3bm", 100, 4, 25, "NRZ", 36,
        ("MPO", "LC"), ("QSFP+",),
    ),
    "QSFP56": FormFactorSpec(
        "QSFP56", "IEEE 802.3cd", 200, 4, 50, "PAM4", 36,
        ("MPO", "LC", "CS"), ("QSFP+", "QSFP28"),
    ),
    "QSFP-DD": FormFactorSpec(
        "QSFP-DD", "IEEE 802.3bs", 400, 8, 50, "PAM4", 36,
        ("MPO", "LC", "CS"), ("QSFP+", "QSFP28", "QSFP56"),
    ),
    "OSFP": FormFactorSpec(
        "OSFP", "OIF-OSFP-01.0", 800, 8, 100, "PAM4", 36,
        ("MPO", "LC"), (),
    ),
    "CFP8": FormFactorSpec(
        "CFP8", "ITU-T G.959.1", 400, 8, 50, "PAM4", 16,
        ("MPO", "LC"), (),
    ),
}

QSFP_DD_CAGE_TYPES: Dict[str, str] = {
    "Type 1": "Similar to QSFP28 in size (flush front)",
    "Type 2": "Longer back/external cage to provide more room for optical design",
    "Type 2A": "Extruded heat sink packaged on top of the optics for thermal dissipation",
    "Type 2B": "Taller heat sink to make room for internal connector and port separation",
}


@dataclass(frozen=True)
class OpticsPackagingComparison:
    """Power, BOM cost, and serviceability trade-off for Pluggable, LPO, LRO, and CPO."""

    architecture: str
    tx_dsp_in_module: bool
    rx_dsp_in_module: bool
    field_pluggable: bool
    per_port_power_w: float
    dsp_power_w: float
    switch_64port_optics_power_w: float
    power_savings_vs_pluggable_pct: float
    bom_dsp_cost_share_range_pct: Tuple[int, int]


def compare_optics_packaging_power(
    pluggable_port_power_w: float = 16.0,
    dsp_power_fraction: float = 0.50,
    switch_ports: int = 64,
) -> Dict[str, OpticsPackagingComparison]:
    """Model Pluggable, LPO, LRO, and CPO power consumption from ADC Chapter 4.

    In ADC Ch. 4:
    - The DSP represents 20% to 40% of module BOM cost and ~50% of transceiver power.
    - LPO removes both Tx and Rx DSP from the module (eliminating ~100% of module DSP power,
      i.e., ~50% of total module power).
    - LRO removes the Rx DSP only while retaining the Tx DSP (~50% of module DSP power removed,
      i.e., ~25% of total module power).
    - CPO co-packages optics on the ASIC substrate, eliminating module DSP and long PCB trace
      driver losses (~68.75% total optics power savings, e.g., 16 W -> 5 W per 800G port).
    """
    full_dsp_w = pluggable_port_power_w * dsp_power_fraction
    non_dsp_w = pluggable_port_power_w - full_dsp_w

    pluggable_total = pluggable_port_power_w * switch_ports

    lro_port_w = non_dsp_w + (0.5 * full_dsp_w)
    lpo_port_w = non_dsp_w
    cpo_port_w = round(pluggable_port_power_w * 0.3125, 2)  # 5.0 W at 16.0 W baseline

    results: Dict[str, OpticsPackagingComparison] = {}
    specs = [
        ("Pluggable", True, True, True, pluggable_port_power_w, full_dsp_w, (20, 40)),
        ("LRO", True, False, True, lro_port_w, 0.5 * full_dsp_w, (10, 20)),
        ("LPO", False, False, True, lpo_port_w, 0.0, (0, 0)),
        ("CPO", False, False, False, cpo_port_w, 0.0, (0, 0)),
    ]
    for name, tx_dsp, rx_dsp, pluggable, port_w, dsp_w, bom_range in specs:
        sw_power = round(port_w * switch_ports, 2)
        savings_pct = round((1.0 - (sw_power / pluggable_total)) * 100.0, 2)
        results[name] = OpticsPackagingComparison(
            architecture=name,
            tx_dsp_in_module=tx_dsp,
            rx_dsp_in_module=rx_dsp,
            field_pluggable=pluggable,
            per_port_power_w=round(port_w, 2),
            dsp_power_w=round(dsp_w, 2),
            switch_64port_optics_power_w=sw_power,
            power_savings_vs_pluggable_pct=savings_pct,
            bom_dsp_cost_share_range_pct=bom_range,
        )
    return results


# ---------------------------------------------------------------------------
# 7. mlxlink (-c / -m) Optical Module & BER Health Diagnostics
# ---------------------------------------------------------------------------

def evaluate_mlxlink_module_health(
    state: str,
    physical_state: str,
    effective_ber: float,
    raw_errors_per_lane: Tuple[int, ...],
    link_down_counter: int,
    link_error_recovery_counter: int,
    temperature_c: float,
    temp_range_c: Tuple[float, float] = (-10.0, 80.0),
    voltage_mv: float = 3255.2,
    voltage_range_mv: Tuple[float, float] = (3100.0, 3500.0),
    bias_ma_per_lane: Tuple[float, ...] = (6.75, 6.75, 6.75, 6.75),
    bias_range_ma: Tuple[float, float] = (5.492, 8.5),
    rx_power_dbm_per_lane: Tuple[float, ...] = (0.0, 0.0, 0.0, 0.0),
    rx_power_range_dbm: Tuple[float, float] = (-14.0, 6.0),
    tx_power_dbm_per_lane: Tuple[float, ...] = (0.0, 0.0, 0.0, 0.0),
    tx_power_range_dbm: Tuple[float, float] = (-12.0, 6.0),
    cdr_rx_per_lane: Tuple[str, ...] = ("ON", "ON", "ON", "ON"),
    cdr_tx_per_lane: Tuple[str, ...] = ("ON", "ON", "ON", "ON"),
) -> Dict[str, object]:
    """Evaluate mlxlink -c and -m telemetry against DDM and BER thresholds."""
    anomalies: List[str] = []

    if state != "Active" or physical_state != "LinkUp":
        anomalies.append(f"PORT_STATE_{state}_{physical_state}")
    if effective_ber > 1e-12:
        anomalies.append(f"HIGH_EFFECTIVE_BER_{effective_ber:.1e}")
    if any(err > 0 for err in raw_errors_per_lane):
        anomalies.append("NONZERO_LANE_PHYSICAL_ERRORS")
    if link_down_counter > 0 or link_error_recovery_counter > 0:
        anomalies.append("LINK_FLAP_OR_ERROR_RECOVERY")
    if not (temp_range_c[0] <= temperature_c <= temp_range_c[1]):
        anomalies.append(f"MODULE_TEMP_OUT_OF_RANGE_{temperature_c}C")
    if not (voltage_range_mv[0] <= voltage_mv <= voltage_range_mv[1]):
        anomalies.append(f"MODULE_VOLTAGE_OUT_OF_RANGE_{voltage_mv}mV")
    if any(not (bias_range_ma[0] <= b <= bias_range_ma[1]) for b in bias_ma_per_lane):
        anomalies.append("LASER_BIAS_CURRENT_OUT_OF_RANGE")
    if any(not (rx_power_range_dbm[0] <= p <= rx_power_range_dbm[1]) for p in rx_power_dbm_per_lane):
        anomalies.append("RX_OPTICAL_POWER_OUT_OF_RANGE")
    if any(not (tx_power_range_dbm[0] <= p <= tx_power_range_dbm[1]) for p in tx_power_dbm_per_lane):
        anomalies.append("TX_OPTICAL_POWER_OUT_OF_RANGE")
    if any(c != "ON" for c in cdr_rx_per_lane) or any(c != "ON" for c in cdr_tx_per_lane):
        anomalies.append("CDR_LOCK_LOST")

    return {
        "is_healthy": len(anomalies) == 0,
        "status": "HEALTHY_MODULE" if len(anomalies) == 0 else "DEGRADED_MODULE",
        "active_lanes": len(raw_errors_per_lane),
        "total_raw_lane_errors": sum(raw_errors_per_lane),
        "anomalies": tuple(anomalies),
    }
