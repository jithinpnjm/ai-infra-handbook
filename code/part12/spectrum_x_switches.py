#!/usr/bin/env python3
"""NVIDIA Spectrum-X and Spectrum switches simulator, models, and calculators.

Covers:
1. Spectrum-4 (`SN5600` / `SN5600D` 51.2 Tbps 64x800G / 128x400G / 256x200G / 512x100G)
   and `SN2201` (48x1GbE + 4x100GbE OOB management switch) port radix, breakout modes,
   monolithic fully shared buffer vs sliced port-allocated buffer microburst absorption,
   and DGX GB300 SuperPOD scale-out topology (`2, 4, 8, 16` SUs -> `1,152, 2,304, 4,608, 9,216` GPUs,
   `8, 16, 32, 64` compute leafs, `4, 8, 12, 24` spines, `2, 2, 4, 8` storage leafs,
   `64, 128, 256, 1024` x 400GbE max storage bandwidth, and `90/280 GB/s` single-SU vs
   `360/1,120 GB/s` 4-SU read/write throughput).
2. End-to-end Spectrum-X platform architecture pairing Spectrum-4 switch ASIC + BlueField-3
   (`BF3240` dual-port 400G SuperNIC / DPU) or ConnectX-7/8 + Cumulus Linux (`NVUE`) + DOCA:
   - BlueField-3 operating modes (`DPU_MODE_ECPF` vs `NIC_MODE_SUPERNIC`), three-layer host-edge
     fault isolation (external switch uplink `swp14 up`, Arm control plane `openvswitch-policy-load.service`,
     host netdev `enp1s0f0np0 DOWN`), and BFB image drift detection (`24.10-prod-3` vs `24.07-prod-1`).
   - ConnectX/BlueField PCIe & NUMA locality (`LnkCap: 32GT/s x16` vs downgraded `LnkSta: 16GT/s x8`,
     `16 GB/s` vs `25 GB/s` for 200GbE, and `nvidia-smi topo -m` `PIX` vs `SYS` multi-rail byte delta
     `892,481,200,384` -> `981,204,882,176` B = `+88.7 GB` in `60 s` on `ens1f0` vs `412,992` B on `ens1f1`).
3. Spectrum-X Adaptive Routing & Selective Dynamic Load Balancing (`sDLB` / per-packet RoCEv2
   spraying via `BTH` `RDMA Write` opcode matching) vs standard 5-tuple Static Load Balancing (`SLB` /
   `CRC32` `0x8BDA7C2D` over `192.168.1.20 -> 192.168.2.10` UDP `1024 -> 4791`, resilient hashing
   `512`/`1,024` buckets) raising effective AI fabric bandwidth from `~60%` to `~95%`.
4. BlueField-3 / ConnectX-7/8 hardware out-of-order Direct Data Placement (`DDP`) reassembly
   (writing out-of-order `RDMA Write` payloads directly into target GPU memory via `RETH` virtual
   address + `PSN` offset without `Go-Back-N` retransmission storms, deferring completion `CQE`
   until the full PSN bitmap fills).
5. Spectrum-X hardware telemetry-driven congestion control (in-band switch queue occupancy & drain
   rate telemetry vs classical reactive `ECN`/`DCQCN`), What Just Happened (`WJH`) hardware drop-reason
   classification (`Tail drop (queue full)` `18,402` and `52,100` vs `0` on healthy rack), and
   multi-leaf `rx_pfc_prio3` pause-tree origin tracing (`leaf03: 210,500` -> `leaf07: 198,200` ->
   `leaf12: 41,100`).
6. Declarative NVUE (`nv set` / `nv config apply`) and BCM `cmsh` (`nvconfigurationmode` `auto`/`manual`/`file`,
   REST port `8765`, `SN2201` `8,048,771,072` B RAM / `115,923,419,136` B NVMe ZTP inventory)
   validation for lossless RoCE (`MTU 9000`/`9216`, `DSCP 26`/`46` -> `prio 3`, `ECN`, `PFC`,
   `roce enable on`, Adaptive Routing, and BGP/EVPN).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

# ---------------------------------------------------------------------------
# 1. Hardware & Topology Constants (superpod-gb300-ra, superpod-b200-dc, ADC, BCM11)
# ---------------------------------------------------------------------------
SPECTRUM4_ASIC_TBPS: float = 51.2  # 51.2 Tbps switching capacity (SN5600 / SN5600D)
SPECTRUM4_SERDES_LANES: int = 512  # 512 x 100G PAM4 SerDes lanes
SN5600_PORTS_800G: int = 64  # 64 x 800GbE OSFP ports
SN5600_BREAKOUT_400G: int = 128  # 128 x 400GbE via 2x breakout
SN5600_BREAKOUT_200G: int = 256  # 256 x 200GbE via 4x breakout
SN5600_BREAKOUT_100G: int = 512  # 512 x 100GbE via 8x breakout

# Out-of-band (OOB) management switch: NVIDIA SN2201 (superpod-gb300-ra p. 13, 26; bcm11-admin p. 153)
SN2201_COPPER_1G_PORTS: int = 48  # 48 x 1 Gbps RJ45 copper downlink ports
SN2201_UPLINK_100G_PORTS: int = 4  # 4 x 100 Gbps QSFP28 uplink ports
SN2201_RAM_BYTES: int = 8_048_771_072  # 7.496 GB RAM reported in bcm11-admin sysinfo
SN2201_DISK_BYTES: int = 115_923_419_136  # 115 GB NVMe reported in bcm11-admin sysinfo
NVUE_DEFAULT_REST_PORT: int = 8765  # bcm11-admin p. 151 default NVUE REST API port

# BlueField-3 & ConnectX-8 per GB300 compute tray (superpod-gb300-ra p. 8-9, 22, 24)
GB300_TRAYS_PER_RACK: int = 18
GB300_GPUS_PER_RACK: int = 72
GB300_RACKS_PER_SU: int = 8
GB300_GPUS_PER_SU: int = 576
GB300_CX8_PER_TRAY: int = 4  # 4 x ConnectX-8 (800 Gbps) per tray
GB300_BF3_PORTS_PER_TRAY: int = 2  # 1 x BlueField-3 BF3240 dual-port 400 Gbps (1x400G storage, >=200G in-band)
GB300_STORAGE_PORT_GBPS: int = 400
GB300_INBAND_MIN_GBPS: int = 200
GB300_COMPUTE_LEAF_UPLINKS_400G: int = 24  # 24 x 400G uplinks per compute leaf (1:3 blocking ratio)
GB300_STORAGE_LEAF_LINKS_400G: int = 72  # 72 x 400G nonblocking links per storage leaf
GB300_MGMT_LEAF_LINKS_400G: int = 24  # 24 x 400G links per management leaf
GB300_CUSTOMER_EDGE_DR1_100G_MIN: int = 2  # >= 2 x 100GbE DR1 single-mode customer edge links

# Spectrum-X vs Traditional Ethernet effective bandwidth & RoCEv2 constants (ADC Ch. 2, Ch. 6)
TRADITIONAL_ECMP_EFFECTIVE_BW_PCT: float = 60.0  # ~60% effective bandwidth under standard 5-tuple ECMP
SPECTRUM_X_EFFECTIVE_BW_PCT: float = 95.0  # ~95% effective bandwidth with Spectrum-X AR + DDP
ROCEV2_UDP_PORT: int = 4791  # 0x12B7
ADC_SLB_SAMPLE_CRC32_HEX: int = 0x8BDA7C2D  # 2,346,351,661 decimal (ADC Ch. 6 p. 101)
ADC_RESILIENT_HASH_BUCKETS: Tuple[int, int] = (512, 1024)


# ---------------------------------------------------------------------------
# 1. Spectrum-4 Port Radix, Breakout Modes, Shared Buffer & SuperPOD Scale-Out
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SpectrumPortBreakoutPlan:
    switch_model: str
    asic_capacity_tbps: float
    physical_osfp_ports: int
    mode: str
    logical_ports: int
    port_speed_gbps: int
    aggregate_tbps: float
    serdes_lanes_per_logical_port: int


def compute_spectrum4_breakout(mode: str = "64x800G") -> SpectrumPortBreakoutPlan:
    """Compute logical port radix and lane mapping for Spectrum-4 SN5600 / SN5600D."""
    modes: Dict[str, Tuple[int, int, int]] = {
        "64x800G": (64, 800, 8),
        "128x400G": (128, 400, 4),
        "256x200G": (256, 200, 2),
        "512x100G": (512, 100, 1),
    }
    if mode not in modes:
        raise ValueError(f"Unsupported Spectrum-4 breakout mode: {mode}")
    logical_ports, speed_gbps, lanes = modes[mode]
    agg_tbps = round((logical_ports * speed_gbps) / 1000.0, 1)
    return SpectrumPortBreakoutPlan(
        switch_model="SN5600 / SN5600D",
        asic_capacity_tbps=SPECTRUM4_ASIC_TBPS,
        physical_osfp_ports=SN5600_PORTS_800G,
        mode=mode,
        logical_ports=logical_ports,
        port_speed_gbps=speed_gbps,
        aggregate_tbps=agg_tbps,
        serdes_lanes_per_logical_port=lanes,
    )


@dataclass(frozen=True)
class BufferArchitectureComparison:
    total_switch_buffer_mb: float
    num_ports: int
    hot_port_burst_mb: float
    sliced_per_port_cap_mb: float
    sliced_dropped_mb: float
    shared_dynamic_cap_mb: float
    shared_dropped_mb: float
    shared_absorbs_microburst: bool


def compare_sliced_vs_monolithic_shared_buffer(
    total_switch_buffer_mb: float = 64.0,
    num_ports: int = 64,
    hot_port_burst_mb: float = 8.0,
    shared_alpha_cap_fraction: float = 0.25,
) -> BufferArchitectureComparison:
    """Compare a port-sliced buffer vs Spectrum's monolithic fully shared buffer under AI incast.

    In a sliced switch (V9 Ch. 7), each port is restricted to `total / num_ports` (e.g., 1.0 MB),
    dropping 7.0 MB of an 8.0 MB microburst even when the other 63 ports are idle.
    In Spectrum's monolithic shared buffer, a hot port can dynamically borrow up to `alpha`
    of the free shared pool (e.g., 16.0 MB), absorbing the 8.0 MB microburst with zero drops.
    """
    sliced_cap = round(total_switch_buffer_mb / num_ports, 4)
    sliced_drop = round(max(0.0, hot_port_burst_mb - sliced_cap), 4)
    shared_cap = round(total_switch_buffer_mb * shared_alpha_cap_fraction, 4)
    shared_drop = round(max(0.0, hot_port_burst_mb - shared_cap), 4)
    return BufferArchitectureComparison(
        total_switch_buffer_mb=total_switch_buffer_mb,
        num_ports=num_ports,
        hot_port_burst_mb=hot_port_burst_mb,
        sliced_per_port_cap_mb=sliced_cap,
        sliced_dropped_mb=sliced_drop,
        shared_dynamic_cap_mb=shared_cap,
        shared_dropped_mb=shared_drop,
        shared_absorbs_microburst=(shared_drop == 0.0),
    )


@dataclass(frozen=True)
class GB300EthernetScaleOutPlan:
    num_sus: int
    num_gpus: int
    spine_switches_sn5600d: int
    compute_leaf_switches_sn5600d: int
    storage_leaf_switches_sn5600d: int
    max_storage_ports_400g: int
    max_storage_bandwidth_tbps: float
    mgmt_leafs: int
    oob_spines: int


def get_gb300_spectrum_ethernet_scaleout(num_sus: int) -> GB300EthernetScaleOutPlan:
    """Return DGX GB300 SuperPOD SN5600/SN5600D Ethernet fabric scale-out table (superpod-gb300-ra Table 4, p. 23)."""
    table: Dict[int, Tuple[int, int, int, int, int]] = {
        # num_sus: (gpus, spines, compute_leafs, storage_leafs, max_storage_400g_links)
        2: (1152, 4, 8, 2, 64),
        4: (2304, 8, 16, 2, 128),
        8: (4608, 12, 32, 4, 256),
        16: (9216, 24, 64, 8, 1024),
    }
    if num_sus not in table:
        raise ValueError(f"Unsupported GB300 SuperPOD SU count: {num_sus} (expected 2, 4, 8, or 16)")
    gpus, spines, comp_leafs, stor_leafs, stor_400g = table[num_sus]
    return GB300EthernetScaleOutPlan(
        num_sus=num_sus,
        num_gpus=gpus,
        spine_switches_sn5600d=spines,
        compute_leaf_switches_sn5600d=comp_leafs,
        storage_leaf_switches_sn5600d=stor_leafs,
        max_storage_ports_400g=stor_400g,
        max_storage_bandwidth_tbps=round(stor_400g * 0.4, 1),
        mgmt_leafs=2,
        oob_spines=2,
    )


@dataclass(frozen=True)
class SuperPODStorageTierThroughput:
    tier: str
    single_su_read_gbps: int
    single_su_write_gbps: int
    four_su_read_gbps: int
    four_su_write_gbps: int


def get_gb300_storage_throughput_guidelines(tier: str = "Enhanced") -> SuperPODStorageTierThroughput:
    """Return DGX GB300 SuperPOD RoCEv2 High-Performance Storage throughput guidelines (Table 5, p. 31)."""
    tiers = {
        "Standard": SuperPODStorageTierThroughput("Standard", 90, 45, 360, 180),
        "Enhanced": SuperPODStorageTierThroughput("Enhanced", 280, 140, 1120, 560),
    }
    if tier not in tiers:
        raise ValueError(f"Unknown storage tier: {tier}")
    return tiers[tier]


@dataclass(frozen=True)
class LeafCutCapacityModel:
    num_nodes: int
    rails_per_node: int
    rail_speed_gbps: int
    downlink_demand_gbps: int
    normal_uplinks: int
    normal_uplink_capacity_gbps: int
    normal_oversubscription_ratio: float
    degraded_uplinks: int
    degraded_uplink_capacity_gbps: int
    degraded_oversubscription_ratio: float


def evaluate_leaf_cut_oversubscription(
    num_nodes: int = 16,
    rails_per_node: int = 2,
    rail_speed_gbps: int = 400,
    normal_uplinks: int = 8,
    uplink_speed_gbps: int = 400,
    failed_uplinks: int = 1,
) -> LeafCutCapacityModel:
    """Compute normal and N-1 degraded leaf-to-spine cut capacity (V9 Ch. 10 worked example)."""
    downlink_gbps = num_nodes * rails_per_node * rail_speed_gbps
    norm_up_gbps = normal_uplinks * uplink_speed_gbps
    deg_uplinks = max(1, normal_uplinks - failed_uplinks)
    deg_up_gbps = deg_uplinks * uplink_speed_gbps
    return LeafCutCapacityModel(
        num_nodes=num_nodes,
        rails_per_node=rails_per_node,
        rail_speed_gbps=rail_speed_gbps,
        downlink_demand_gbps=downlink_gbps,
        normal_uplinks=normal_uplinks,
        normal_uplink_capacity_gbps=norm_up_gbps,
        normal_oversubscription_ratio=round(downlink_gbps / norm_up_gbps, 2),
        degraded_uplinks=deg_uplinks,
        degraded_uplink_capacity_gbps=deg_up_gbps,
        degraded_oversubscription_ratio=round(downlink_gbps / deg_up_gbps, 2),
    )


# ---------------------------------------------------------------------------
# 2. Spectrum-X End-to-End Platform: BlueField-3 Modes, ConnectX PCIe/NUMA & Rails
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BlueFieldOperatingModeSpec:
    sku_type: str
    default_mode: str
    arm_owns_eswitch: bool
    host_admin_isolated: bool
    separate_oob_required: bool


def evaluate_bluefield_sku_mode(sku_type: str) -> BlueFieldOperatingModeSpec:
    """Distinguish BlueField DPU SKU default mode (`DPU_MODE_ECPF`) from SuperNIC SKU default mode (`NIC_MODE_SUPERNIC`) (V9 Ch. 9)."""
    norm = sku_type.strip().upper()
    if norm == "DPU":
        return BlueFieldOperatingModeSpec(
            sku_type="DPU",
            default_mode="DPU_MODE_ECPF",
            arm_owns_eswitch=True,
            host_admin_isolated=True,
            separate_oob_required=True,
        )
    if norm == "SUPERNIC":
        return BlueFieldOperatingModeSpec(
            sku_type="SUPERNIC",
            default_mode="NIC_MODE_SUPERNIC",
            arm_owns_eswitch=False,
            host_admin_isolated=False,
            separate_oob_required=False,
        )
    raise ValueError(f"Unknown BlueField SKU type: {sku_type}")


@dataclass(frozen=True)
class DPUThreeLayerDiagnosis:
    switch_uplink_up: bool
    arm_policy_service_active: bool
    host_interface_up: bool
    fault_domain: str
    remediation: str


def diagnose_dpu_three_layer_path(
    switch_uplink_up: bool,
    arm_policy_service_active: bool,
    host_interface_up: bool,
) -> DPUThreeLayerDiagnosis:
    """Isolate faults across the 3 DPU layers: (3) Switch uplink, (2) Arm policy service, (1) Host netdev (V9 Ch. 9)."""
    if not switch_uplink_up:
        return DPUThreeLayerDiagnosis(
            switch_uplink_up=False,
            arm_policy_service_active=arm_policy_service_active,
            host_interface_up=host_interface_up,
            fault_domain="LAYER3_PHYSICAL_UPLINK_FAULT",
            remediation="Inspect leaf port, transceiver, cable, and FEC counters before checking DPU or host.",
        )
    if not arm_policy_service_active:
        return DPUThreeLayerDiagnosis(
            switch_uplink_up=True,
            arm_policy_service_active=False,
            host_interface_up=host_interface_up,
            fault_domain="LAYER2_DPU_ARM_POLICY_BOOT_FAILURE",
            remediation="Recover DPU Arm policy service via OOB BMC and gate host readiness on embedded-switch policy load.",
        )
    if not host_interface_up:
        return DPUThreeLayerDiagnosis(
            switch_uplink_up=True,
            arm_policy_service_active=True,
            host_interface_up=False,
            fault_domain="LAYER1_HOST_FUNCTION_REPRESENTOR_FAULT",
            remediation="Check host mlx5 driver, VF/SF representor binding, and PCIe link state.",
        )
    return DPUThreeLayerDiagnosis(
        switch_uplink_up=True,
        arm_policy_service_active=True,
        host_interface_up=True,
        fault_domain="ALL_THREE_DPU_LAYERS_HEALTHY",
        remediation="Proceed to RoCEv2 GID, QoS, and application collective checks.",
    )


@dataclass(frozen=True)
class PCIeLocalityAudit:
    cap_gt_per_s: int
    cap_width: int
    sta_gt_per_s: int
    sta_width: int
    cap_bw_gbps_raw: float
    negotiated_bw_gb_per_s: float
    required_bw_gb_per_s: float
    is_pcie_downgraded: bool
    can_sustain_port_line_rate: bool
    gpu_nic_topo: str
    crosses_numa_sys: bool


def audit_connectx_pcie_and_locality(
    cap_gt_per_s: int = 32,
    cap_width: int = 16,
    sta_gt_per_s: int = 16,
    sta_width: int = 8,
    eth_port_gbps: int = 200,
    gpu_nic_topo: str = "PIX",
) -> PCIeLocalityAudit:
    """Audit ConnectX PCIe `LnkCap` vs `LnkSta` bandwidth and `nvidia-smi topo -m` locality (V9 Ch. 8).

    In V9 Ch. 8: `LnkCap: Speed 32GT/s, Width x16` (~64 GB/s) vs downgraded `LnkSta: Speed 16GT/s, Width x8`
    (~16 GB/s). A 200GbE port requires ~25 GB/s (`200 / 8`), so Gen4 x8 (16 GB/s) caps host throughput at ~25%
    of Gen5 x16 capacity and cannot saturate a 200GbE link.
    """
    # Using standard 128b/130b encoding approximation where 16 GT/s x8 ~= 16 GB/s and 32 GT/s x16 ~= 64 GB/s
    cap_gb_s = round((cap_gt_per_s * cap_width) / 8.0, 2)
    neg_gb_s = round((sta_gt_per_s * sta_width) / 8.0, 2)
    req_gb_s = round(eth_port_gbps / 8.0, 2)
    downgraded = (sta_gt_per_s < cap_gt_per_s) or (sta_width < cap_width)
    return PCIeLocalityAudit(
        cap_gt_per_s=cap_gt_per_s,
        cap_width=cap_width,
        sta_gt_per_s=sta_gt_per_s,
        sta_width=sta_width,
        cap_bw_gbps_raw=cap_gb_s,
        negotiated_bw_gb_per_s=neg_gb_s,
        required_bw_gb_per_s=req_gb_s,
        is_pcie_downgraded=downgraded,
        can_sustain_port_line_rate=(neg_gb_s >= req_gb_s),
        gpu_nic_topo=gpu_nic_topo,
        crosses_numa_sys=(gpu_nic_topo.upper() == "SYS"),
    )


@dataclass(frozen=True)
class MultiRailByteDeltaAudit:
    rail0_delta_bytes: int
    rail0_delta_gb: float
    rail1_delta_bytes: int
    rail1_delta_gb: float
    window_seconds: int
    rail0_gbps: float
    rail1_gbps: float
    rail1_effectively_idle: bool


def analyze_multirail_byte_deltas(
    rail0_start_bytes: int = 892_481_200_384,
    rail0_end_bytes: int = 981_204_882_176,
    rail1_start_bytes: int = 0,
    rail1_end_bytes: int = 412_992,
    window_seconds: int = 60,
) -> MultiRailByteDeltaAudit:
    """Analyze 60-second `rx_bytes_phy` multi-rail counter deltas from V9 Ch. 8 Scenario 1."""
    d0 = rail0_end_bytes - rail0_start_bytes
    d1 = rail1_end_bytes - rail1_start_bytes
    gb0 = round(d0 / 1e9, 1)
    gb1 = round(d1 / 1e9, 4)
    gbps0 = round((d0 * 8) / (window_seconds * 1e9), 2)
    gbps1 = round((d1 * 8) / (window_seconds * 1e9), 4)
    return MultiRailByteDeltaAudit(
        rail0_delta_bytes=d0,
        rail0_delta_gb=gb0,
        rail1_delta_bytes=d1,
        rail1_delta_gb=gb1,
        window_seconds=window_seconds,
        rail0_gbps=gbps0,
        rail1_gbps=gbps1,
        rail1_effectively_idle=(gb1 < 0.01 and gb0 > 10.0),
    )


# ---------------------------------------------------------------------------
# 3. Spectrum-X Adaptive Routing & Selective Packet Spraying (sDLB) vs SLB
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SLBvsSpectrumXResult:
    hash_key_hex: str
    hash_key_dec: int
    mod_5_index: int
    mod_8_index: int
    slb_spine_loads_gbps: Tuple[float, ...]
    slb_max_link_utilization_pct: float
    slb_effective_fabric_bw_pct: float
    dlb_spine_loads_gbps: Tuple[float, ...]
    dlb_max_link_utilization_pct: float
    spectrum_x_sprayed_loads_gbps: Tuple[float, ...]
    spectrum_x_effective_fabric_bw_pct: float


def compare_slb_dlb_and_spectrum_x_spraying(
    link_capacity_gbps: float = 200.0,
    flow_rates_gbps: Sequence[float] = (50.0, 100.0, 50.0, 100.0),
) -> SLBvsSpectrumXResult:
    """Compare Static Load Balancing (SLB), Dynamic Load Balancing (DLB), and Spectrum-X per-packet spraying.

    Includes the exact ADC Ch. 6 CRC32 hash example (`0x8BDA7C2D` = `2,346,351,661` over
    `192.168.1.20 -> 192.168.2.10` UDP `1024 -> 4791`, `mod 5 = 1`, `mod 8 = 5`), the
    2-spine `(50, 100, 50, 100)` Gbps flow assignment (`SLB` puts `50+50=100G` on SpineA `50%`
    and `100+100=200G` on SpineB `100%`, whereas `DLB`/`Spectrum-X` balances `50+100=150G` `75%`
    on both spines), and the cluster-wide `~60%` -> `~95%` effective bandwidth gain.
    """
    h_val = ADC_SLB_SAMPLE_CRC32_HEX
    f1, f2, f3, f4 = flow_rates_gbps
    # SLB (ADC Fig 6-2): Flow1(50G) + Flow3(50G) -> SpineA (100G, 50%); Flow2(100G) + Flow4(100G) -> SpineB (200G, 100%)
    slb_loads = (round(f1 + f3, 2), round(f2 + f4, 2))
    slb_max_util = round(max(slb_loads) / link_capacity_gbps * 100.0, 1)
    # DLB (ADC Fig 6-4): Flow1(50G) + Flow2(100G) -> 150G (75%) on each spine
    dlb_loads = (round(f1 + f2, 2), round(f3 + f4, 2))
    dlb_max_util = round(max(dlb_loads) / link_capacity_gbps * 100.0, 1)
    # Spectrum-X per-packet spraying splits total offered load evenly across all active ECMP links
    total = sum(flow_rates_gbps)
    sprayed = (round(total / 2.0, 2), round(total / 2.0, 2))
    return SLBvsSpectrumXResult(
        hash_key_hex=f"0x{h_val:08X}",
        hash_key_dec=h_val,
        mod_5_index=h_val % 5,
        mod_8_index=h_val % 8,
        slb_spine_loads_gbps=slb_loads,
        slb_max_link_utilization_pct=slb_max_util,
        slb_effective_fabric_bw_pct=TRADITIONAL_ECMP_EFFECTIVE_BW_PCT,
        dlb_spine_loads_gbps=dlb_loads,
        dlb_max_link_utilization_pct=dlb_max_util,
        spectrum_x_sprayed_loads_gbps=sprayed,
        spectrum_x_effective_fabric_bw_pct=SPECTRUM_X_EFFECTIVE_BW_PCT,
    )


def select_packet_spray_mode_by_bth_opcode(
    udp_dst_port: int,
    bth_opcode_name: str,
    nic_supports_ddp_ooo: bool = True,
) -> str:
    """Selective Dynamic Load Balancing (`sDLB`, ADC Ch. 2 & Ch. 6 Fig 6-16):

    Matches RoCEv2 (`UDP 4791`) BTH `RDMA_WRITE` elephant flows via switch TCAM ACL and enables
    `PER_PACKET_SPRAY` when the endpoint (`ConnectX-6/7/8` or `BlueField-3`) supports hardware
    out-of-order `DDP`, while keeping control/non-matching flows on `FLOWLET_OR_PER_FLOW`.
    """
    if udp_dst_port == ROCEV2_UDP_PORT and nic_supports_ddp_ooo and "WRITE" in bth_opcode_name.upper():
        return "PER_PACKET_SPRAY"
    return "FLOWLET_OR_PER_FLOW"


# ---------------------------------------------------------------------------
# 4. BlueField-3 Hardware Out-of-Order Direct Data Placement (DDP) Reassembly
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DDPReassemblyResult:
    arriving_psns: Tuple[int, ...]
    base_va: int
    mtu_bytes: int
    placement_offsets_by_arrival: Tuple[Tuple[int, int], ...]
    final_contiguous_psns: Tuple[int, ...]
    ddp_enabled_go_back_n_retransmits: int
    legacy_nic_go_back_n_retransmits: int
    completion_cqe_emitted_after_all_psns: bool


def simulate_bluefield3_ddp_ooo_placement(
    arriving_psns: Sequence[int] = (200, 202, 203, 201, 205, 204),
    base_va: int = 0x7F00_0000_0000,
    mtu_bytes: int = 4096,
) -> DDPReassemblyResult:
    """Simulate BlueField-3 / ConnectX-7/8 hardware out-of-order Direct Data Placement (`DDP`).

    When Spectrum-X sprays a single RDMA Write flow across all spine links, packets arrive out
    of PSN order (`200, 202, 203, 201, 205, 204`). Instead of firing PSN-gap NAKs and triggering
    Go-Back-N retransmission storms, BlueField-3 calculates the exact target memory address
    `VA = base_va + (psn - base_psn) * mtu_bytes` for each arriving packet, DMAs every payload
    directly into GPU memory in place, tracks a PSN bitmap in hardware, and posts the completion
    CQE only after all PSNs `200..205` have arrived.
    """
    if not arriving_psns:
        raise ValueError("arriving_psns must not be empty")
    min_psn = min(arriving_psns)
    placements: List[Tuple[int, int]] = []
    expected = min_psn
    legacy_naks = 0
    seen = set()
    for psn in arriving_psns:
        offset = base_va + (psn - min_psn) * mtu_bytes
        placements.append((psn, offset))
        if psn > expected and expected not in seen:
            legacy_naks += 1
        seen.add(psn)
        while expected in seen:
            expected += 1
    ordered = tuple(sorted(seen))
    contiguous = ordered == tuple(range(min_psn, min_psn + len(seen)))
    return DDPReassemblyResult(
        arriving_psns=tuple(arriving_psns),
        base_va=base_va,
        mtu_bytes=mtu_bytes,
        placement_offsets_by_arrival=tuple(placements),
        final_contiguous_psns=ordered,
        ddp_enabled_go_back_n_retransmits=0,
        legacy_nic_go_back_n_retransmits=legacy_naks,
        completion_cqe_emitted_after_all_psns=contiguous,
    )


# ---------------------------------------------------------------------------
# 5. Spectrum-X Telemetry-Driven Congestion Control, WJH & PFC Tree Tracing
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SpectrumXCongestionStep:
    port_rate_gbps: float
    queue_occupancy_kb: float
    ecn_marked: bool
    inband_telemetry_occupancy_ratio: float
    classical_dcqcn_rate_gbps: float
    spectrum_x_telemetry_rate_gbps: float


def compute_spectrum_x_cc_rate(
    port_rate_gbps: float = 400.0,
    queue_occupancy_kb: float = 96.0,
    target_threshold_kb: float = 64.0,
    max_threshold_kb: float = 256.0,
    active_flows: int = 2,
) -> SpectrumXCongestionStep:
    """Compare Spectrum-X hardware telemetry-driven CC against classical binary ECN/DCQCN.

    Spectrum-4 embeds exact queue depth and drain-rate telemetry into congestion feedback so
    BlueField-3 SuperNICs pace each flow directly to its fair share (`port_rate / active_flows`)
    in a single RTT without over-cutting or sawtooth oscillation.
    """
    if queue_occupancy_kb <= target_threshold_kb:
        return SpectrumXCongestionStep(
            port_rate_gbps=port_rate_gbps,
            queue_occupancy_kb=queue_occupancy_kb,
            ecn_marked=False,
            inband_telemetry_occupancy_ratio=0.0,
            classical_dcqcn_rate_gbps=port_rate_gbps,
            spectrum_x_telemetry_rate_gbps=round(port_rate_gbps / max(1, active_flows), 2),
        )
    ratio = min(
        1.0,
        (queue_occupancy_kb - target_threshold_kb) / max(1.0, (max_threshold_kb - target_threshold_kb)),
    )
    # Classical DCQCN applies a blind binary multiplicative cut (e.g. 50% cut per step)
    classical_rate = round(port_rate_gbps * 0.5, 2)
    # Spectrum-X uses exact switch queue telemetry to converge immediately to fair share minus queue drain
    fair_share = port_rate_gbps / max(1, active_flows)
    spec_x_rate = round(fair_share * (1.0 - 0.15 * ratio), 2)
    return SpectrumXCongestionStep(
        port_rate_gbps=port_rate_gbps,
        queue_occupancy_kb=queue_occupancy_kb,
        ecn_marked=True,
        inband_telemetry_occupancy_ratio=round(ratio, 4),
        classical_dcqcn_rate_gbps=classical_rate,
        spectrum_x_telemetry_rate_gbps=spec_x_rate,
    )


@dataclass(frozen=True)
class WJHClassification:
    branch_name: str
    root_cause_category: str
    recommended_action: str


def classify_spectrum_wjh_and_counters(
    fec_uncorrected_delta: int,
    tail_drop_count: int,
    ecn_marks_delta: int,
    pfc_pause_delta: int,
    link_utilization_pct: float,
) -> WJHClassification:
    """Classify Spectrum switch telemetry into the 4 diagnostic branches of V9 Ch. 7 Fig 9.7.1."""
    if fec_uncorrected_delta > 0:
        return WJHClassification(
            branch_name="PHYSICAL_FAULT",
            root_cause_category="Physical cable, optic, or port signal degradation",
            recommended_action="Isolate and replace transceiver/cable on the port with fec_uncorrected_blocks > 0.",
        )
    if tail_drop_count > 0 or pfc_pause_delta > 10_000:
        return WJHClassification(
            branch_name="OVERSUBSCRIBED_CUT_OR_HOT_LEAF",
            root_cause_category="Sustained egress queue saturation (WJH tail drop or pause tree)",
            recommended_action="Trace destination IP / pause gradient (`leaf03 -> leaf07 -> leaf12`), fix placement or capacity.",
        )
    if ecn_marks_delta > 0 and pfc_pause_delta <= 1_000:
        return WJHClassification(
            branch_name="HEALTHY_CONGESTION_CONTROL",
            root_cause_category="ECN + endpoint rate control operating in normal feedback zone",
            recommended_action="No incident; retain counter deltas as operational baseline.",
        )
    if link_utilization_pct < 40.0:
        return WJHClassification(
            branch_name="ECMP_OR_RAIL_IMBALANCE",
            root_cause_category="Low path utilization with slow job step time (hash collision or idle rail)",
            recommended_action="Enable Spectrum-X Adaptive Routing / sDLB and verify multi-rail NIC binding.",
        )
    return WJHClassification(
        branch_name="NORMAL_STEADY_STATE",
        root_cause_category="Clean physical and queue counters",
        recommended_action="Continue normal monitoring.",
    )


def trace_pfc_pause_tree_origin(leaf_rx_pfc_prio3: Dict[str, int]) -> Tuple[str, Tuple[Tuple[str, int], ...]]:
    """Order leaves by `rx_pfc_prio3` count descending to identify the downstream pause-tree origin (V9 Ch. 7 Scenario 2).

    In V9 Ch. 7 Scenario 2: `leaf03: 210,500`, `leaf07: 198,200`, `leaf12: 41,100` -> `leaf03` is the origin.
    """
    if not leaf_rx_pfc_prio3:
        raise ValueError("leaf_rx_pfc_prio3 must not be empty")
    ordered = tuple(sorted(leaf_rx_pfc_prio3.items(), key=lambda kv: kv[1], reverse=True))
    return ordered[0][0], ordered


# ---------------------------------------------------------------------------
# 6. Declarative NVUE (`nv set`) Lossless RoCE / Adaptive Routing / EVPN Audit
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class NVUESpectrumXValidation:
    has_lossless_mtu: bool
    has_roce_enabled: bool
    has_dscp_trust_and_pfc_prio3: bool
    has_ecn_enabled: bool
    has_adaptive_routing_enabled: bool
    has_bgp_evpn_control_plane: bool
    is_valid_spectrum_x_config: bool


def validate_nvue_spectrum_x_commands(commands: Sequence[str]) -> NVUESpectrumXValidation:
    """Validate a list of Cumulus Linux NVUE (`nv set ...`) commands for a Spectrum-X AI leaf switch."""
    joined = "\n".join(commands).lower()
    has_mtu = ("mtu 9000" in joined) or ("mtu 9216" in joined)
    has_roce = "qos roce enable on" in joined
    has_pfc = ("pfc" in joined and "prio" in joined) or ("qos roce" in joined and "dscp" in joined)
    has_ecn = "ecn" in joined or "qos roce enable on" in joined
    has_ar = "adaptive-routing" in joined
    has_bgp = "router bgp" in joined and ("evpn" in joined or "underlay" in joined or "neighbor" in joined)
    all_ok = has_mtu and has_roce and has_pfc and has_ecn and has_ar and has_bgp
    return NVUESpectrumXValidation(
        has_lossless_mtu=has_mtu,
        has_roce_enabled=has_roce,
        has_dscp_trust_and_pfc_prio3=has_pfc,
        has_ecn_enabled=has_ecn,
        has_adaptive_routing_enabled=has_ar,
        has_bgp_evpn_control_plane=has_bgp,
        is_valid_spectrum_x_config=all_ok,
    )
