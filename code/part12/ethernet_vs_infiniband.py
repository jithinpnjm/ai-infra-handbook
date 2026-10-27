#!/usr/bin/env python3
"""Chapter 12.12 model: Ethernet versus InfiniBand: a design decision guide.

Models the end-to-end architectural, operational, and economic decision matrix
between InfiniBand (Quantum-2 / Quantum-X800), Standard RoCEv2 Ethernet,
NVIDIA Spectrum-X (Spectrum-4 + BlueField-3 SuperNIC), and Ultra Ethernet
Consortium (UEC Specification v1.0 / UET):
  1. Training vs Inference AI Data Center Requirements & Advantages/Disadvantages
     of InfiniBand vs Ethernet (ADC Ch 2 Fig 2-1, Fig 2-2, Fig 2-3, Fig 2-4, Fig 2-5):
     - Training (petabytes/exabytes, hours to weeks/months, synchronized collectives,
       east-west elephant flows, UDP 4791 low entropy, flowlets, non-blocking 1:1
       or rail-optimized design ROD vs rail-unified design RUD, undersubscribed
       leaf-to-spine option for shallow buffers) vs Inference (milliseconds to
       seconds, TTFT, terabytes/petabytes, 100G/200G switches, edge/RAG, EVPN-VXLAN
       multi-tenancy).
     - Proactive congestion avoidance (SLB 5-tuple CRC32, DLB link/queue-aware,
       GLB next-to-next-hop NNH quality, sDLB BTH opcode per-packet spraying,
       flow pinning) vs Reactive congestion control (ECN IP bits 11 -> CNP IP ECN 01
       -> DCQCN rate cut, PFC 802.1Qbb per-queue pause quanta).
  2. Multi-Generation Fabric Architecture Matrix (ADC Ch 9 Table 9-2 & Ch 12
     Table 12-1..12-4, V9 Ch 1–12):
     - InfiniBand vs Standard RoCEv2 vs Spectrum-X vs UET v1.0 (June 11, 2025,
       70+ vendors, <100,000 IB vs >100,000 RoCEv2 vs ~1,000,000 UET scale,
       300 ns IB vs 800 ns Ethernet storage switch port-to-port latency, 100 ns
       PCIe Gen5 local SSD latency, 700–900 ns 1–3 hop storage target,
       16-bit LID up to 48,000 / 49,151 nodes, 16 VLs with 8..12 active queues
       and 64B CBFC credits in LLH vs 8 IEEE 802.1Qbb PFC priorities vs 32 UEC
       CBFC Virtual Channels with 256B RCCC credits and CtlOS/CP_Update out-of-band
       64B/66B PCS signaling, UDP 49150 vs raw IP protocol 253 with 128-byte switch
       parse depth, ROD/RUD/RUDI/UUD delivery modes, NSCC/RCCC/packet trimming/LLR,
       SHARP vs UEC INC manager/sFEP switch agents over gRPC).
  3. ConnectX VPI (Virtual Protocol Interconnect) Personality & Host Locality
     Validator (V9 Ch 2, Ch 3, Ch 8, Ch 9, BCM11 §3.6.2):
     - `mlxconfig -d <bdf> set LINK_TYPE_P1=1` (IB) vs `LINK_TYPE_P1=2` (ETH),
       BCM `cmsh` `MLX_` precedence (`category.extra_values < node.extra_values <
       interface.extra_values`), PCIe Gen5 x16 (32 GT/s, ~63–64 GB/s) vs downgraded
       Gen4 x8 (16 GT/s, ~16 GB/s capping a 200 Gbps / 25 GB/s NIC), `nvidia-smi topo -m`
       `PIX` vs `SYS` NUMA crossing, dual-rail `rx_bytes_phy` imbalance (`88.7 GB`
       on `ens1f0` vs `412,992 B` on `ens1f1`), and BlueField-3 DPU mode (`ECPF`
       arm-side representor + embedded switch fast path) vs SuperNIC mode (`NIC` mode).
  4. 64-GPU H100 Training Pod TCO & Break-Even Utilization Calculator (V21 Ch 2 Part 6
     & Part 3.2):
     - 128-GPU (16-node) DGX/HGX H100 SXM5 reference ($285,000/node, $4.56M nodes,
       $5.26M CapEx, $644K/yr OpEx, $7.19M 3-year TCO -> $2.14/GPU-hour, $22/TFLOP-year
       at 107,603 TFLOPS sustained / 126,592 TFLOPS peak, 989 TFLOPS BF16/GPU,
       900 GB/s NVLink 4 vs 50 GB/s 400G port vs 64 GB/s PCIe Gen5 x16).
     - 64-GPU H100 cluster interconnect justification: IB NDR ($15,000/node) vs
       400GbE RoCEv2 ($8,000/node) -> $7,000/node delta = $448,000 upfront savings.
     - 100 ms base training step + 2 ms IB AllReduce (102 ms, 1.96% / ~2% overhead)
       vs 10 ms Ethernet AllReduce (110 ms, 9.09% / ~10% overhead, ~8% throughput loss).
     - 7-day (168-hour) Llama-70B run on 64 GPUs: 8% loss adds 13.44 hours (~13.4 hours,
       181.44 hours / 7.56 days total); at $2.14/GPU-hour, each run costs $1,835.11
       (~$1,835) extra; at 24 runs/year (twice monthly), annual penalty is $44,043
       (~$44K/year) or $132,128 (~$132K over 3 years) — proving pure compute-overhead
       math alone requires ~244 runs (10.17 years) to break even at 64 GPUs, and that
       IB's true justification is nonlinear congestion scaling past 128–256 GPUs,
       multi-model 2x gradient growth (30 ms Ethernet -> 130 ms vs 102 ms IB, 27%
       overhead, ~$12K/yr for 2 extra runs), and avoiding mid-life fabric swaps and
       senior-engineer troubleshooting stalls.
  5. Workload-Driven Fabric Selection & 7-Stage Validation Ladder (V9 Ch 1, 2, 4,
     5, 6, 7, 10, 11, 12 & Labs 01–04):
     - 16-node rack capacity cut math: 16 nodes * 800 Gbps (2x400G rails) = 12,800 Gbps
       downlink vs 8x400G = 3,200 Gbps uplink (4.00:1 normal oversubscription) and
       7x400G = 2,800 Gbps N-1 degraded uplink (4.57:1 oversubscription).
     - PFC buffer hysteresis math (65,536 B prio 3 buffer, Xoff 49,152 B = 75%,
       Xon 32,768 B = 50%, headroom 16,384 B = 25%, hysteresis 16,384 B = 25%).
     - Telemetry signature classifier across Volume 09 production incidents (Job 2
       contention `rx_pfc_prio3=118,344` & `rx_ecn_marked_prio3=198,220`; `mlnx_qos`
       `prio6` leak; `swp19` `pcp` vs `dscp` trust drift with `tos 0xb8` DSCP 46 and
       `rx_prio0_discard=18,420`; Spectrum WJH `Tail drop (queue full)` `18,402` /
       `52,100` / `38,210`; pause tree `leaf03=210,500 -> leaf07=198,200 -> leaf12=41,100`;
       DCQCN weak throttle `np_cnp_handled=409,500` at `rp_current_rate=98 Gbps`;
       optical fault `fec_uncorrected_blocks=3` == `rx_crc_errors=3`; Lab 03 bounded
       contention `47,829` ECN marks, `412` RX PFC, `89.2`/`87.1` Gbps; Lab 04 `mlx5_1`
       injection `392.11 -> 156.0` Gbps with `24` `RETRY_EXC_ERR`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# --- 1. Architectural & Protocol Constants (ADC Ch 2, Ch 9, Ch 12 & V9) ---
ROCEV2_UDP_PORT: int = 4791
ROCEV2_CM_UDP_PORT: int = 4420
NVME_TCP_DISCOVERY_PORT: int = 8009
UET_UDP_PORT: int = 49150
UET_NATIVE_IP_PROTO: int = 253
SWITCH_PARSE_DEPTH_BYTES: int = 128

RDMA_PRTYPE_IB: int = 2
RDMA_PRTYPE_ROCEV2: int = 4
RDMA_PRTYPE_IWARP: int = 5

PCIE_GEN5_LOCAL_SSD_LATENCY_NS: int = 100
IB_SWITCH_PORT_LATENCY_NS: int = 300
ETH_SWITCH_PORT_LATENCY_NS: int = 800
STORAGE_HOP_LATENCY_MIN_NS: int = 700
STORAGE_HOP_LATENCY_MAX_NS: int = 900
PCIE_GEN5_GT_PER_SEC: int = 32
PCIE_GEN5_X16_UNIDIR_GBPS: int = 63  # ADC Ch 9 (~63 Gbps / ~64 GB/s)
NVME_RDMA_WRITE_LATENCY_REDUCTION_PCT: int = 66
WAN_LONG_DISTANCE_KM: int = 40
IB_SPEC_MAX_OPTICS_KM: int = 10

IB_LID_BITS: int = 16
IB_MAX_SUBNET_NODES: int = 48000  # ADC Ch 9 (exact unicast 49,151)
IB_EXACT_UNICAST_LIDS: int = 49151
IB_VIRTUAL_LANES: int = 16
IB_WORKLOAD_QUEUES_MIN: int = 8
IB_WORKLOAD_QUEUES_MAX: int = 12
IB_CBFC_CREDIT_BYTES: int = 64

ETH_PFC_PRIORITIES: int = 8
UEC_CBFC_VIRTUAL_CHANNELS: int = 32
UEC_RCCC_CREDIT_UNIT_BYTES: int = 256
UEC_RCCC_ACK_CC_BITS: int = 24
UEC_SPEC_RELEASE_DATE: str = "2025-06-11"
UEC_VENDOR_COUNT_MIN: int = 70
IB_MAX_SCALE_GPUS: int = 100000
ROCEV2_MIN_LARGE_SCALE_GPUS: int = 100000
UET_TARGET_SCALE_GPUS: int = 1000000

# ConnectX VPImlxconfig constants (BCM11 §3.6.2 & V9 Ch 8)
MLXCONFIG_LINK_TYPE_IB: int = 1
MLXCONFIG_LINK_TYPE_ETH: int = 2
BCM_DEFAULT_NUM_VFS: int = 16

# --- 2. Volume 21 Ch 2 GPU & Cluster TCO Constants ---
H100_SXM5_BF16_TFLOPS: int = 989
H100_SXM5_FP8_TFLOPS: int = 1979
H100_SXM5_HBM3_GB: int = 80
H100_SXM5_BW_TBPS: float = 3.35
H100_SXM5_TDP_W: int = 700
H100_SXM5_UNIT_PRICE_USD: int = 30000
H100_SXM5_PRICE_PER_TFLOP_USD: int = 30
H100_PCIE_BF16_TFLOPS: int = 756
H100_PCIE_TDP_W: int = 350
H100_PCIE_UNIT_PRICE_USD: int = 20000
H200_SXM_HBM3E_GB: int = 141
H200_SXM_BW_TBPS: float = 4.8
H200_SXM_UNIT_PRICE_USD: int = 40000
L40S_GDDR6_GB: int = 48
L40S_BF16_TFLOPS: int = 362
L40S_UNIT_PRICE_USD: int = 8000

NVLINK4_PER_GPU_GBPS: int = 900  # 900 GB/s inside 8-GPU HGX/DGX H100 node
PCIE_GEN5_X16_PER_DIR_GBPS: int = 64  # ~64 GB/s per direction
PCIE_GEN4_X8_DEGRADED_GBPS: int = 16  # ~16 GB/s downgraded slot in V9 Ch 8
NDR_400G_PORT_GBPS_BYTES: int = 50  # 400 Gb/s = 50 GB/s
ETH_200G_PORT_GBPS_BYTES: int = 25  # 200 Gb/s = 25 GB/s

DGX_H100_NODE_GPUS: int = 8
DGX_H100_NODE_COST_USD: int = 285000
DGX_H100_COST_PER_GPU_USD: float = 35625.0
PCIE_H100_NODE_COST_USD: int = 215000
PCIE_H100_COST_PER_GPU_USD: float = 26875.0
DGX_H100_SYSTEM_POWER_KW: float = 10.2
QM9700_NDR_PORTS: int = 64
QM9700_OSFP_CAGES: int = 32

# 64-GPU IB vs RoCEv2 TCO Constants (V21 Ch 2 Part 6)
POD_64_GPUS: int = 64
IB_NDR_COST_PER_UNIT_USD: int = 15000
ETH_400G_COST_PER_UNIT_USD: int = 8000
GPU_HOUR_AMORTIZED_COST_USD: float = 2.14
BASE_COMPUTE_STEP_MS: float = 100.0
IB_ALLREDUCE_STEP_MS: float = 2.0
ETH_ALLREDUCE_STEP_MS: float = 10.0
ETH_LARGE_MODEL_ALLREDUCE_MS: float = 30.0
LLAMA70B_BASELINE_HOURS: float = 168.0  # 7 days continuous on 64 GPUs
DEFAULT_RUNS_PER_YEAR: int = 24  # twice per month


@dataclass(frozen=True)
class FabricArchitectureProfile:
    """Architectural comparison row for IB, Standard RoCEv2, Spectrum-X, and UET v1.0."""

    name: str
    transport_encapsulation: str
    flow_control_mechanism: str
    congestion_control_loop: str
    routing_and_multipathing: str
    delivery_modes: Tuple[str, ...]
    in_network_collectives: str
    max_scale_gpus: int
    switch_latency_ns: int
    security_layer: str
    nic_and_switch_ecosystem: str
    deployment_readiness: str


def build_fabric_comparison_matrix() -> Dict[str, FabricArchitectureProfile]:
    """Return the 4-way architectural comparison matrix (ADC Ch 9 Table 9-2, Ch 12 Table 12-4, V9)."""
    return {
        "InfiniBand": FabricArchitectureProfile(
            name="InfiniBand (Quantum-2 NDR / Quantum-X800 XDR)",
            transport_encapsulation="Native IB LRH (8B, 16-bit LID) + optional GRH (40B) + BTH (12B) + ICRC (4B) + VCRC (2B)",
            flow_control_mechanism="Hardware Credit-Based Flow Control (CBFC, 64B credit units in LLH across 16 VLs: VL0..VL14 data + VL15 SMP)",
            congestion_control_loop="IBTA hardware FECN -> BECN -> HCA CCTI injection-rate table",
            routing_and_multipathing="Centralized Subnet Manager (OpenSM / UFM) LFT + hardware Adaptive Routing (AR) + SHIELD fast recovery",
            delivery_modes=("RC (in-order + HCA OOO reordering)", "UC", "UD"),
            in_network_collectives="Hardware SHARP (Scalable Hierarchical Aggregation and Reduction Protocol) in Quantum switches",
            max_scale_gpus=IB_MAX_SCALE_GPUS,
            switch_latency_ns=IB_SWITCH_PORT_LATENCY_NS,
            security_layer="16-bit P_Key hardware partitioning (0x8000 full-member bit); no native payload encryption in Table 12-4",
            nic_and_switch_ecosystem="Single-vendor vertically integrated (NVIDIA ConnectX HCA + Quantum switch + UFM)",
            deployment_readiness="Deployed in production networks (<48,000 nodes/subnet via 16-bit LID; multi-subnet beyond)",
        ),
        "Standard_RoCEv2": FabricArchitectureProfile(
            name="Standard RoCEv2 Ethernet (IEEE 802.1Qbb / DCQCN)",
            transport_encapsulation="Ethernet II + IPv4/IPv6 + UDP (DST PORT 4791) + IB BTH (12B) + Payload + Ethernet FCS",
            flow_control_mechanism="Reactive IEEE 802.1Qbb Priority Flow Control (PFC pause frames across 8 priorities, Xoff/Xon buffer thresholds)",
            congestion_control_loop="DCQCN: Switch RED/ECN marks IP CE=11 -> Receiver NIC sends CNP (IP ECN 01) -> Sender NIC hardware rate limiter",
            routing_and_multipathing="Distributed BGP / EVPN-VXLAN with 5-tuple ECMP (SLB), Dynamic LB (DLB flowlets), or Global LB (GLB NNH)",
            delivery_modes=("RC (in-order go-back-N or ConnectX Write OOO)", "UC", "UD"),
            in_network_collectives="No switch-resident collective offload (host xCCL / NCCL Ring and Tree only)",
            max_scale_gpus=ROCEV2_MIN_LARGE_SCALE_GPUS,
            switch_latency_ns=ETH_SWITCH_PORT_LATENCY_NS,
            security_layer="External security stack (MACsec / IPsec, plus VLAN/VRF/EVPN multi-tenancy)",
            nic_and_switch_ecosystem="Multi-vendor open Ethernet switches (Broadcom Tomahawk, Cisco, Arista, NVIDIA Spectrum) + RoCEv2 NICs",
            deployment_readiness="Deployed in production networks (100,000+ GPU clusters; requires careful PFC/ECN/DCQCN and load-balancing tuning)",
        ),
        "Spectrum_X": FabricArchitectureProfile(
            name="NVIDIA Spectrum-X AI Ethernet (Spectrum-4 + BlueField-3 SuperNIC)",
            transport_encapsulation="RoCEv2 (UDP 4791 + BTH) with hardware-assisted adaptive packet spraying and Direct Data Placement (DDP)",
            flow_control_mechanism="Monolithic fully shared switch buffer + narrow PFC safety net (priority 3) with WJH drop-reason telemetry",
            congestion_control_loop="Hardware-coordinated Spectrum-4 congestion telemetry + BlueField-3 SuperNIC RTT/ECN rate control",
            routing_and_multipathing="BGP / EVPN control plane + per-packet Spectrum-X adaptive routing with BlueField-3 hardware out-of-order reassembly",
            delivery_modes=("RC with hardware OOO Direct Data Placement (DDP)", "Selective DLB Write spraying"),
            in_network_collectives="NCCL topology-aware rail optimization (NVLink intra-node + rail-aligned Spectrum leaves)",
            max_scale_gpus=ROCEV2_MIN_LARGE_SCALE_GPUS,
            switch_latency_ns=ETH_SWITCH_PORT_LATENCY_NS,
            security_layer="Multi-tenant EVPN-VXLAN isolation + BlueField-3 DPU/SuperNIC zero-trust host-edge boundary and IPsec/MACsec",
            nic_and_switch_ecosystem="Co-engineered Ethernet platform (NVIDIA Spectrum-4 / Cumulus NVUE / NetQ + BlueField-3 SuperNIC / ConnectX-7/8)",
            deployment_readiness="Deployed in production AI factories requiring Ethernet standards with turnkey RoCE predictability",
        ),
        "UET_UEC": FabricArchitectureProfile(
            name="Ultra Ethernet Consortium (UEC Spec v1.0 / UET)",
            transport_encapsulation="Ethernet + IPv4/IPv6 + UDP (DST PORT 49150, dynamic SRC PORT entropy) OR native IP (Proto 253 + PDS Entropy) + PDS + SES",
            flow_control_mechanism="Optional link-level CBFC across 32 Virtual Channels (VCs) using 64B/66B PCS CtlOS / CP_Update + Link Layer Retry (LLR)",
            congestion_control_loop="End-to-end NSCC (RTT + ECN window) and RCCC (receiver-managed 256B credits in 24-bit ACK_CC) + switch packet trimming",
            routing_and_multipathing="IP Clos / Dragonfly+ with dynamic UDP source port or PDS Entropy adaptation on NACK + SES JobID/PIDonFEP/Resource Index hashing",
            delivery_modes=("ROD (Reliable Ordered)", "RUD (Reliable Unordered)", "RUDI (Reliable Unordered Idempotent)", "UUD (Unreliable Unordered)"),
            in_network_collectives="UEC In-Network Collectives (INC): INC Manager (gRPC OOB) + switch sFEP INC agents + Libfabric fi_collective API",
            max_scale_gpus=UET_TARGET_SCALE_GPUS,
            switch_latency_ns=ETH_SWITCH_PORT_LATENCY_NS,
            security_layer="Built-in Transport Security Sublayer (TSS with AES-GCM ICV after UET payload; mutually exclusive with optional UET CRC)",
            nic_and_switch_ecosystem="Open 70+ member multi-vendor consortium (AI Base, AI Full, and HPC compliance profiles over Libfabric)",
            deployment_readiness="Spec v1.0 released June 11, 2025; first pilot deployments expected late 2026",
        ),
    }


@dataclass(frozen=True)
class ConnectXVPIValidation:
    """Result of validating ConnectX VPI port personality, BCM precedence, and host locality."""

    pci_bdf: str
    link_type_code: int
    effective_personality: str
    resolved_bcm_source: str
    resolved_bcm_link_type: str
    pcie_speed_gt_s: int
    pcie_width_lanes: int
    usable_pcie_bw_gbps_bytes: float
    required_port_bw_gbps_bytes: float
    pcie_bottlenecked: bool
    gpu_nic_locality: str
    numa_crossing_penalty: bool
    rail0_delta_gb: float
    rail1_delta_gb: float
    multi_rail_imbalanced: bool
    verdict: str


def evaluate_connectx_vpi_and_locality(
    pci_bdf: str,
    link_type_p1: int,
    category_extra_link_type: Optional[str],
    node_extra_link_type: Optional[str],
    interface_extra_link_type: Optional[str],
    pcie_speed_gt_s: int,
    pcie_width_lanes: int,
    port_rate_gbps: int,
    gpu_nic_topo_relation: str,
    rail0_rx_bytes_delta: int,
    rail1_rx_bytes_delta: int,
) -> ConnectXVPIValidation:
    """Validate ConnectX VPI mode (`1`=IB, `2`=ETH), BCM `MLX_` precedence, PCIe speed/width, and rail balance."""
    if link_type_p1 not in (MLXCONFIG_LINK_TYPE_IB, MLXCONFIG_LINK_TYPE_ETH):
        raise ValueError(f"Unsupported mlxconfig LINK_TYPE_P1={link_type_p1}; expected 1 (IB) or 2 (ETH)")

    effective_personality = "InfiniBand" if link_type_p1 == MLXCONFIG_LINK_TYPE_IB else "Ethernet"

    # BCM11 §3.6.2 precedence: category.extra_values < node.extra_values < interface.extra_values
    if interface_extra_link_type is not None:
        resolved_source = "interface.extra_values"
        resolved_val = interface_extra_link_type
    elif node_extra_link_type is not None:
        resolved_source = "node.extra_values"
        resolved_val = node_extra_link_type
    elif category_extra_link_type is not None:
        resolved_source = "category.extra_values"
        resolved_val = category_extra_link_type
    else:
        resolved_source = "firmware_default"
        resolved_val = "IB" if link_type_p1 == 1 else "ETH"

    # PCIe Gen4 (16 GT/s) or Gen5 (32 GT/s): x16 Gen5 ~ 64 GB/s, x8 Gen4 ~ 16 GB/s (V9 Ch 8 & V21 Ch 2)
    usable_pcie_bw_gbps_bytes = (pcie_speed_gt_s / 32.0) * (pcie_width_lanes / 16.0) * 64.0
    required_port_bw_gbps_bytes = port_rate_gbps / 8.0
    pcie_bottlenecked = usable_pcie_bw_gbps_bytes < required_port_bw_gbps_bytes

    numa_crossing_penalty = gpu_nic_topo_relation.upper() == "SYS"
    rail0_delta_gb = round(rail0_rx_bytes_delta / 1e9, 1)
    rail1_delta_gb = round(rail1_rx_bytes_delta / 1e9, 4)
    total_delta = rail0_rx_bytes_delta + rail1_rx_bytes_delta
    multi_rail_imbalanced = total_delta > 0 and (
        min(rail0_rx_bytes_delta, rail1_rx_bytes_delta) / total_delta < 0.10
    )

    issues: List[str] = []
    if (resolved_val == "IB" and link_type_p1 != 1) or (resolved_val == "ETH" and link_type_p1 != 2):
        issues.append("VPI_PERSONALITY_DRIFT_PENDING_REBOOT")
    if pcie_bottlenecked:
        issues.append("PCIE_DOWNGRADED_BELOW_LINE_RATE")
    if numa_crossing_penalty:
        issues.append("SYS_NUMA_CROSSING_PENALTY")
    if multi_rail_imbalanced:
        issues.append("SINGLE_RAIL_IDLE_NCCL_DEVICE_COLLISION")

    verdict = "HEALTHY_ENDPOINT_AND_LOCALITY" if not issues else "+".join(issues)
    return ConnectXVPIValidation(
        pci_bdf=pci_bdf,
        link_type_code=link_type_p1,
        effective_personality=effective_personality,
        resolved_bcm_source=resolved_source,
        resolved_bcm_link_type=resolved_val,
        pcie_speed_gt_s=pcie_speed_gt_s,
        pcie_width_lanes=pcie_width_lanes,
        usable_pcie_bw_gbps_bytes=round(usable_pcie_bw_gbps_bytes, 2),
        required_port_bw_gbps_bytes=round(required_port_bw_gbps_bytes, 2),
        pcie_bottlenecked=pcie_bottlenecked,
        gpu_nic_locality=gpu_nic_topo_relation.upper(),
        numa_crossing_penalty=numa_crossing_penalty,
        rail0_delta_gb=rail0_delta_gb,
        rail1_delta_gb=rail1_delta_gb,
        multi_rail_imbalanced=multi_rail_imbalanced,
        verdict=verdict,
    )


@dataclass(frozen=True)
class PodTCOCalculation:
    """Volume 21 Ch 2 Part 6 TCO and break-even model for InfiniBand NDR vs 400GbE RoCEv2."""

    num_gpus: int
    ib_capex_usd: int
    eth_capex_usd: int
    upfront_ib_premium_usd: int
    base_compute_ms: float
    ib_allreduce_ms: float
    eth_allreduce_ms: float
    ib_step_ms: float
    eth_step_ms: float
    ib_comm_overhead_pct: float
    eth_comm_overhead_pct: float
    approx_throughput_loss_pct: float
    exact_step_slowdown_pct: float
    baseline_run_hours: float
    eth_extra_hours_per_run: float
    eth_total_run_hours: float
    eth_total_run_days: float
    extra_cost_per_run_usd: float
    runs_per_year: int
    annual_extra_compute_cost_usd: float
    three_year_extra_compute_cost_usd: float
    large_model_eth_allreduce_ms: float
    large_model_eth_step_ms: float
    large_model_overhead_pct: float
    large_model_extra_annual_usd: float
    runs_needed_to_break_even: float
    years_to_break_even_at_24_runs: float
    pure_compute_math_justifies_ib_at_64_gpus: bool
    architectural_recommendation: str


def calculate_64gpu_ib_vs_roce_tco(
    num_gpus: int = POD_64_GPUS,
    ib_unit_cost_usd: int = IB_NDR_COST_PER_UNIT_USD,
    eth_unit_cost_usd: int = ETH_400G_COST_PER_UNIT_USD,
    base_compute_ms: float = BASE_COMPUTE_STEP_MS,
    ib_allreduce_ms: float = IB_ALLREDUCE_STEP_MS,
    eth_allreduce_ms: float = ETH_ALLREDUCE_STEP_MS,
    baseline_run_hours: float = LLAMA70B_BASELINE_HOURS,
    gpu_hour_cost_usd: float = GPU_HOUR_AMORTIZED_COST_USD,
    runs_per_year: int = DEFAULT_RUNS_PER_YEAR,
    large_model_eth_allreduce_ms: float = ETH_LARGE_MODEL_ALLREDUCE_MS,
    large_model_extra_runs_per_year: int = 2,
) -> PodTCOCalculation:
    """Compute the Volume 21 Ch 2 Part 6 64-GPU IB NDR vs 400GbE TCO and break-even analysis."""
    if num_gpus <= 0 or base_compute_ms <= 0 or baseline_run_hours <= 0:
        raise ValueError("num_gpus, base_compute_ms, and baseline_run_hours must be positive")

    ib_capex = num_gpus * ib_unit_cost_usd
    eth_capex = num_gpus * eth_unit_cost_usd
    upfront_premium = ib_capex - eth_capex  # $7,000 * 64 = $448,000

    ib_step_ms = base_compute_ms + ib_allreduce_ms  # 102 ms
    eth_step_ms = base_compute_ms + eth_allreduce_ms  # 110 ms

    ib_comm_overhead_pct = round((ib_allreduce_ms / base_compute_ms) * 100.0, 2)  # 2.0%
    eth_comm_overhead_pct = round((eth_allreduce_ms / base_compute_ms) * 100.0, 2)  # 10.0%
    approx_throughput_loss_pct = round(eth_comm_overhead_pct - ib_comm_overhead_pct, 2)  # 8.0%
    exact_step_slowdown_pct = round(((eth_step_ms - ib_step_ms) / ib_step_ms) * 100.0, 2)  # 7.84%

    # Volume 21 Ch 2 Part 6 uses the 8% overhead delta: 168 * 0.08 = 13.44 hours (~13.4 hours -> 181.4 hours / 7.56 days)
    eth_extra_hours_exact = baseline_run_hours * (approx_throughput_loss_pct / 100.0)  # 13.44 h
    eth_extra_hours_rounded = round(eth_extra_hours_exact, 1)  # 13.4 h
    eth_total_run_hours = round(baseline_run_hours + eth_extra_hours_rounded, 1)  # 181.4 h
    eth_total_run_days = round((baseline_run_hours + eth_extra_hours_exact) / 24.0, 2)  # 7.56 days

    extra_cost_per_run = round(gpu_hour_cost_usd * num_gpus * eth_extra_hours_rounded, 2)  # $1,835.11 (~$1,835)
    annual_extra_cost = round(round(extra_cost_per_run) * runs_per_year, 2)  # $1,835 * 24 = $44,040 (~$44K)
    three_year_extra_cost = round(annual_extra_cost * 3, 2)  # $132,120 (~$132K)

    # Larger model (2x gradient tensor): 30 ms on Ethernet -> 130 ms vs 102 ms on IB (~27% overhead)
    large_eth_step_ms = base_compute_ms + large_model_eth_allreduce_ms  # 130 ms
    large_overhead_pct = round(((large_eth_step_ms - ib_step_ms) / ib_step_ms) * 100.0)  # 27%
    large_extra_annual_usd = round(
        (large_overhead_pct / 100.0)
        * gpu_hour_cost_usd
        * num_gpus
        * baseline_run_hours
        * large_model_extra_runs_per_year
    )  # $12,415 (~$12K/year)

    runs_to_break_even = round(upfront_premium / round(extra_cost_per_run), 2)  # 448,000 / 1,835 = 244.14 runs
    years_to_break_even = round(runs_to_break_even / runs_per_year, 2)  # 10.17 years
    justifies_by_compute_alone = three_year_extra_cost >= upfront_premium

    recommendation = (
        "DEFENSIBLE_ETHERNET_AT_FIXED_64_GPUS"
        if not justifies_by_compute_alone
        else "INFINIBAND_JUSTIFIED_BY_COMPUTE_SAVINGS_ALONE"
    )
    return PodTCOCalculation(
        num_gpus=num_gpus,
        ib_capex_usd=ib_capex,
        eth_capex_usd=eth_capex,
        upfront_ib_premium_usd=upfront_premium,
        base_compute_ms=base_compute_ms,
        ib_allreduce_ms=ib_allreduce_ms,
        eth_allreduce_ms=eth_allreduce_ms,
        ib_step_ms=ib_step_ms,
        eth_step_ms=eth_step_ms,
        ib_comm_overhead_pct=ib_comm_overhead_pct,
        eth_comm_overhead_pct=eth_comm_overhead_pct,
        approx_throughput_loss_pct=approx_throughput_loss_pct,
        exact_step_slowdown_pct=exact_step_slowdown_pct,
        baseline_run_hours=baseline_run_hours,
        eth_extra_hours_per_run=eth_extra_hours_rounded,
        eth_total_run_hours=eth_total_run_hours,
        eth_total_run_days=eth_total_run_days,
        extra_cost_per_run_usd=round(extra_cost_per_run),
        runs_per_year=runs_per_year,
        annual_extra_compute_cost_usd=annual_extra_cost,
        three_year_extra_compute_cost_usd=three_year_extra_cost,
        large_model_eth_allreduce_ms=large_model_eth_allreduce_ms,
        large_model_eth_step_ms=large_eth_step_ms,
        large_model_overhead_pct=float(large_overhead_pct),
        large_model_extra_annual_usd=float(large_extra_annual_usd),
        runs_needed_to_break_even=runs_to_break_even,
        years_to_break_even_at_24_runs=years_to_break_even,
        pure_compute_math_justifies_ib_at_64_gpus=justifies_by_compute_alone,
        architectural_recommendation=recommendation,
    )


@dataclass(frozen=True)
class RackCutAndBufferResult:
    """Capacity bottleneck-cut (V9 Ch 10) and PFC buffer threshold/hysteresis math (V9 Ch 4)."""

    nodes_per_rack: int
    rails_per_node: int
    port_speed_gbps: int
    downlink_demand_gbps: int
    normal_uplinks: int
    normal_uplink_capacity_gbps: int
    normal_oversubscription_ratio: float
    degraded_uplinks: int
    degraded_uplink_capacity_gbps: int
    degraded_oversubscription_ratio: float
    prio3_buffer_bytes: int
    xoff_threshold_bytes: int
    xon_threshold_bytes: int
    xoff_pct: float
    xon_pct: float
    headroom_bytes: int
    headroom_pct: float
    hysteresis_bytes: int
    hysteresis_pct: float


def compute_rack_cut_and_pfc_buffer(
    nodes_per_rack: int = 16,
    rails_per_node: int = 2,
    port_speed_gbps: int = 400,
    normal_uplinks: int = 8,
    failed_uplinks: int = 1,
    prio3_buffer_bytes: int = 65536,
    xoff_threshold_bytes: int = 49152,
    xon_threshold_bytes: int = 32768,
) -> RackCutAndBufferResult:
    """Compute the V9 Ch 10 leaf-to-spine oversubscription cut and V9 Ch 4 PFC headroom/hysteresis."""
    if normal_uplinks <= failed_uplinks or prio3_buffer_bytes <= 0:
        raise ValueError("Invalid uplink counts or buffer size")

    downlink_demand = nodes_per_rack * rails_per_node * port_speed_gbps  # 16 * 2 * 400 = 12,800 Gbps
    normal_cap = normal_uplinks * port_speed_gbps  # 8 * 400 = 3,200 Gbps
    degraded_uplinks = normal_uplinks - failed_uplinks  # 7
    degraded_cap = degraded_uplinks * port_speed_gbps  # 7 * 400 = 2,800 Gbps

    normal_ratio = round(downlink_demand / normal_cap, 2)  # 4.00
    degraded_ratio = round(downlink_demand / degraded_cap, 2)  # 4.57

    xoff_pct = round((xoff_threshold_bytes / prio3_buffer_bytes) * 100.0, 2)  # 75.0%
    xon_pct = round((xon_threshold_bytes / prio3_buffer_bytes) * 100.0, 2)  # 50.0%
    headroom_bytes = prio3_buffer_bytes - xoff_threshold_bytes  # 16,384 B
    headroom_pct = round((headroom_bytes / prio3_buffer_bytes) * 100.0, 2)  # 25.0%
    hysteresis_bytes = xoff_threshold_bytes - xon_threshold_bytes  # 16,384 B
    hysteresis_pct = round((hysteresis_bytes / prio3_buffer_bytes) * 100.0, 2)  # 25.0%

    return RackCutAndBufferResult(
        nodes_per_rack=nodes_per_rack,
        rails_per_node=rails_per_node,
        port_speed_gbps=port_speed_gbps,
        downlink_demand_gbps=downlink_demand,
        normal_uplinks=normal_uplinks,
        normal_uplink_capacity_gbps=normal_cap,
        normal_oversubscription_ratio=normal_ratio,
        degraded_uplinks=degraded_uplinks,
        degraded_uplink_capacity_gbps=degraded_cap,
        degraded_oversubscription_ratio=degraded_ratio,
        prio3_buffer_bytes=prio3_buffer_bytes,
        xoff_threshold_bytes=xoff_threshold_bytes,
        xon_threshold_bytes=xon_threshold_bytes,
        xoff_pct=xoff_pct,
        xon_pct=xon_pct,
        headroom_bytes=headroom_bytes,
        headroom_pct=headroom_pct,
        hysteresis_bytes=hysteresis_bytes,
        hysteresis_pct=hysteresis_pct,
    )


@dataclass(frozen=True)
class FabricSelectionRecommendation:
    """Workload-driven fabric selection output across Training, Inference, and Multi-Tenant Clouds."""

    workload_profile: str
    gpu_scale: int
    recommended_primary_fabric: str
    recommended_secondary_fabric: str
    storage_fabric_transport: str
    dpu_host_edge_mode: str
    rationale: str


def select_ai_fabric_for_workload(
    workload_type: str,
    gpu_scale: int,
    planned_growth_gpus: int,
    multi_tenant_untrusted_hosts: bool,
    existing_ethernet_ops_maturity: bool,
    wan_replication_distance_km: int = 0,
) -> FabricSelectionRecommendation:
    """Apply the Chapter 12.12 workload-backward architecture decision rules."""
    wtype = workload_type.lower().strip()
    storage_transport = (
        "NVMe-o-TCP (lossy IP core, port 8009, MSS-adaptable over >=40 km WAN)"
        if wan_replication_distance_km >= WAN_LONG_DISTANCE_KM
        else "NVMe-o-RDMA / GPUDirect Storage (UDP 4420 CM -> UDP 4791 BTH or native IB, ~66% lower write latency)"
    )
    dpu_mode = (
        "BlueField-3 DPU mode (ECPF embedded Arm trust boundary + OVS fast path)"
        if multi_tenant_untrusted_hosts
        else "ConnectX-7 / BlueField-3 SuperNIC mode (NIC mode, 400G/800G rail per GPU)"
    )

    if wtype == "inference":
        return FabricSelectionRecommendation(
            workload_profile="AI Inference & RAG Serving",
            gpu_scale=gpu_scale,
            recommended_primary_fabric="Ethernet (100G/200G/400G Leaf-Spine with EVPN-VXLAN multi-tenancy)",
            recommended_secondary_fabric="Spectrum-X / UET (UUD or RUD delivery for low-latency disaggregated prefill/decode)",
            storage_fabric_transport=storage_transport,
            dpu_host_edge_mode=dpu_mode,
            rationale=(
                "Inference prioritizes real-time North-South/East-West query latency (ms to s), "
                "EVPN-VXLAN multi-tenancy, edge/cloud compatibility, and cost per million tokens ($0.70/1M tokens at 2,000 QPS)."
            ),
        )

    if wtype == "synchronous_training":
        effective_scale = max(gpu_scale, planned_growth_gpus)
        if effective_scale <= 64 and existing_ethernet_ops_maturity and not multi_tenant_untrusted_hosts:
            return FabricSelectionRecommendation(
                workload_profile="Small/Fixed-Pod Synchronous Training (<=64 GPUs)",
                gpu_scale=gpu_scale,
                recommended_primary_fabric="400GbE RoCEv2 (or Single-Pod Leaf-Only InfiniBand NDR)",
                recommended_secondary_fabric="InfiniBand NDR (if zero-touch lossless operations preferred over $448K CapEx savings)",
                storage_fabric_transport=storage_transport,
                dpu_host_edge_mode=dpu_mode,
                rationale=(
                    "At <=64 GPUs with no planned expansion past 128 GPUs, the ~8% AllReduce overhead penalty "
                    "(~$44K/year at 24 runs/year) does not exceed the $448K upfront Ethernet savings over a 3-year lifecycle."
                ),
            )
        if multi_tenant_untrusted_hosts or existing_ethernet_ops_maturity and effective_scale >= 100000:
            return FabricSelectionRecommendation(
                workload_profile="Hyperscale / Multi-Tenant AI Factory Training",
                gpu_scale=gpu_scale,
                recommended_primary_fabric="NVIDIA Spectrum-X AI Ethernet (or UEC/UET v1.0 for 100K–1M+ GPU IP Clos)",
                recommended_secondary_fabric="Multi-Subnet InfiniBand Quantum-X800 (with P_Key isolation and UFM)",
                storage_fabric_transport=storage_transport,
                dpu_host_edge_mode=dpu_mode,
                rationale=(
                    "Multi-tenant cloud isolation (BlueField-3 ECPF + EVPN) or >100,000-endpoint IP Clos scale "
                    "beyond a single 48,000-node 16-bit LID InfiniBand subnet favors Spectrum-X or UET."
                ),
            )
        return FabricSelectionRecommendation(
            workload_profile="Large-Scale Synchronous Foundation Model Training (128+ GPUs)",
            gpu_scale=gpu_scale,
            recommended_primary_fabric="InfiniBand NDR 400G / XDR 800G (Rail-Optimized Fat-Tree with AR, SHARP, and SHIELD)",
            recommended_secondary_fabric="NVIDIA Spectrum-X 400G/800G AI Ethernet",
            storage_fabric_transport=storage_transport,
            dpu_host_edge_mode=dpu_mode,
            rationale=(
                "Beyond 128–256 GPUs, native 64B CBFC credits, sub-microsecond 300 ns switch latency, "
                "SHARP in-network reductions, and 10 us SHIELD healing prevent nonlinear tail-latency stalls."
            ),
        )

    raise ValueError(f"Unknown workload_type: {workload_type!r}")


def diagnose_v9_ethernet_incident(
    fec_uncorrected_delta: int = 0,
    rx_crc_errors_delta: int = 0,
    rdma_link_count: int = 1,
    qp_rtr_success: bool = True,
    switch_trust_mode: str = "dscp",
    roce_dscp_value: int = 46,
    pfc_enabled_priorities: Tuple[int, ...] = (3,),
    prio3_tsa_mode: str = "dwrr",
    rx_prio0_discard_delta: int = 0,
    rx_ecn_marked_prio3_delta: int = 0,
    rx_pfc_prio3_delta: int = 0,
    np_cnp_handled_delta: int = 0,
    rp_current_rate_gbps: float = 400.0,
    wjh_tail_drop_count: int = 0,
    dpu_uplink_up: bool = True,
    dpu_arm_policy_loaded: bool = True,
) -> Tuple[str, str]:
    """Classify a Volume 09 production Ethernet AI incident along the 7-stage validation ladder."""
    # Gate 1: Physical & FEC (V9 Ch 11 swp17 fec_uncorrected_blocks=3, rx_crc_errors=3)
    if fec_uncorrected_delta > 0 or rx_crc_errors_delta > 0:
        return (
            "GATE1_PHYSICAL_LINK_OR_CABLE_FAULT",
            f"fec_uncorrected={fec_uncorrected_delta}, rx_crc_errors={rx_crc_errors_delta}: replace degraded DAC/optic before touching QoS.",
        )

    # Gate 1b: BlueField DPU 3-layer boundary (V9 Ch 9 swp14 up, openvswitch-policy-load failed, host enp1s0f0np0 DOWN)
    if dpu_uplink_up and not dpu_arm_policy_loaded:
        return (
            "GATE1_DPU_ARM_POLICY_LOAD_FAILURE",
            "External switch port is UP, but BlueField Arm control plane failed to load embedded-switch policy; host representor remains DOWN/DORMANT.",
        )

    # Gate 2: RDMA Verbs device registration (V9 Ch 2 mlx5_core loaded without mlx5_ib -> Socket fallback)
    if rdma_link_count == 0:
        return (
            "GATE2_MISSING_RDMA_VERBS_DEVICE_SOCKET_FALLBACK",
            "rdma link show returned 0 devices (mlx5_ib not loaded); NCCL silently falls back from NET/IB to NET/Socket.",
        )

    # Gate 3: RoCE QP RTR transition / GID / MTU mismatch (V9 Ch 3 & Ch 11 ping works, Failed to modify QP to RTR)
    if not qp_rtr_success:
        return (
            "GATE3_ROCE_GID_OR_PATH_MTU_RTR_FAILURE",
            "ICMP ping succeeds, but QP failed to transition to RTR; verify show_gids v2 netdev/VLAN context and hop-by-hop 9000 MTU.",
        )

    # Gate 4: QoS trust boundary drift (V9 Ch 6 swp19 trust pcp instead of dscp -> drops on prio 0)
    if switch_trust_mode.lower() == "pcp" and roce_dscp_value > 0 and rx_prio0_discard_delta > 0:
        return (
            "GATE4_QOS_TRUST_MODE_DRIFT_PRIO0_DROPS",
            f"Switch trusts PCP instead of DSCP ({roce_dscp_value}); routed untagged RoCEv2 packets fall into priority 0 with {rx_prio0_discard_delta} discards.",
        )

    # Gate 4b: Overly broad PFC pause domain or strict-priority management starvation (V9 Ch 1 & Ch 6)
    if len(pfc_enabled_priorities) > 1 or (3 in pfc_enabled_priorities and 6 in pfc_enabled_priorities):
        return (
            "GATE4_BROAD_PFC_PAUSE_DOMAIN_CONTAMINATION",
            f"PFC enabled on multiple priorities {pfc_enabled_priorities}; unrelated traffic sharing tc2 stalls when RoCE pauses.",
        )
    if prio3_tsa_mode.lower() == "strict" and rx_pfc_prio3_delta > 0:
        return (
            "GATE4_STRICT_PRIORITY_MANAGEMENT_STARVATION",
            "RoCE tc1 is scheduled 'strict' over dwrr management tc0; sustained RoCE bursts starve SSH/control-plane traffic.",
        )

    # Gate 5: ECN/DCQCN loop vs PFC backstop (V9 Ch 1, Ch 5, Ch 7, Ch 10)
    if rx_ecn_marked_prio3_delta > 0 and np_cnp_handled_delta == 0:
        return (
            "GATE5_BROKEN_CNP_RETURN_OR_NIC_DCQCN_DISABLED",
            f"Switch marked {rx_ecn_marked_prio3_delta} CE packets, but sender handled 0 CNPs; check reverse CNP path and NIC DCQCN profile.",
        )
    if rx_ecn_marked_prio3_delta > 0 and rx_pfc_prio3_delta == 0 and wjh_tail_drop_count == 0:
        return (
            "GATE5_HEALTHY_PROACTIVE_ECN_DCQCN_LOOP",
            f"ECN marked {rx_ecn_marked_prio3_delta} packets and senders handled {np_cnp_handled_delta} CNPs with 0 PFC pauses and 0 drops.",
        )
    if rx_ecn_marked_prio3_delta > 100000 and rx_pfc_prio3_delta > 10000 and rp_current_rate_gbps >= 90.0:
        return (
            "GATE5_CONGESTED_CUT_OR_WEAK_DCQCN_THROTTLE",
            f"Switch marked {rx_ecn_marked_prio3_delta} packets and paused {rx_pfc_prio3_delta} times while sender remained at {rp_current_rate_gbps} Gbps.",
        )
    if wjh_tail_drop_count > 0:
        return (
            "GATE6_OVERSUBSCRIBED_LEAF_UPLINK_TAIL_DROP",
            f"Spectrum WJH recorded {wjh_tail_drop_count} 'Tail drop (queue full)' packets on the leaf uplink cut under concurrent jobs.",
        )

    return ("ALL_GATES_CLEAN", "All physical, RDMA, QoS, ECN/PFC, and uplink cut gates match baseline.")
