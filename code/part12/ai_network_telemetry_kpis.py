#!/usr/bin/env python3
"""Deterministic AI network telemetry and KPI models for Chapter 12.22.

Covers:
  - AI data center performance KPIs and MLCommons / MLPerf benchmarking (`ADC` Ch. 10):
    * Model vs data KPIs: accuracy (MSE, classification accuracy, precision, recall, F1, MAP),
      numeric precision (`8`-byte FP64, `4`-byte FP32, `2`-byte FP16/BF16, `1`-byte FP8/INT8),
      data efficiency, time-to-train, and Job Completion Time (`JCT`)
    * Six core AI data center KPIs: throughput (`OPS`, `FLOPS`, `QPS`, `samples/sec`), latency
      (`ms`, `us`, `ns`, per-operation and tail `p99`/`p99.9`), accuracy, power (`W`, `kW`, `MW`,
      `PUE = Total Facility Power / IT Equipment Power`), efficiency (`TPW`, `FPW = FLOPS/Watt`,
      `QPW = QPS/Watt`), and scalability (speedup, strong scaling efficiency, weak scaling efficiency)
    * Historical reference: OpenAI ChatGPT / GPT-3 training on `1,023` A100 GPUs in `34` days
    * JCT communication fraction, Amdahl-style scaling efficiency, and collective straggler / tail
      latency amplification (`JCT = N_steps * (T_comp + T_comm_base * tail_factor)`)
    * MLCommons (founded `2020`) initiatives (`MLPerf`, `MLCube`, `PAIR`), benchmarking suites
      (`MLPerf Training`, `MLPerf Inference` across Data Center / Edge / Mobile / Tiny, `MLPerf Storage`),
      AI model tripod (model + dataset + rules/metrics), `Closed` vs `Open` divisions, `LoadGen`
      Data Center Inference scenarios (`Offline` batch vs `Server` Poisson arrival under latency SLA),
      and end-to-end `5`-step benchmarking workflow
  - Network monitoring options, In-Band Flow Analyzer (`IFA`), and corrective actions (`ADC` Ch. 11):
    * Nine monitoring mechanisms: `SNMP polling` (`SNMPv2c`/`v3`), `SNMP traps`, `Syslog`,
      `Streaming telemetry` (`gRPC`/`gNMI` periodic sample vs `on_change` push from forwarding engine),
      `In-Band Flow Analyzer (IFA)`, `RPC query` (`XML`/`JSON`), `Agent-based active probes`
      (`TWAMP` RFC 2455 / UDP / TCP), `sFlow` and `IPFIX`, and `Mirroring on demand` / `Mirroring on drop`
    * Historical monitoring (e.g., `+10%` bandwidth growth over `2` weeks -> `predict_linear` capacity
      forecast) vs real-time monitoring (microsecond/nanosecond congestion, flow tail latency, queue drops,
      fat flows, entropy scores, and server+switch correlation)
    * `IFA` (`draft-kumar-ippm-ifa-08`) node roles (`Initiator`, `Transit`, `Terminator`) in `3`-stage
      and `5`-stage Clos fabrics, packet header stack (`L2 -> L3 -> IFA Header [4B] -> L4 -> IFA Metadata
      Header [4B] -> IFA Metadata Stack [32B per hop] -> Payload`), `32`-bit / `4`-byte IFA Header fields
      (`IFA Version 4b`, `Global Namespace 4b`, `Protocol Type 8b`, `Flags 8b`, `Max Length 8b`),
      `256`-bit / `32`-byte (`8 x 32-bit` rows) per-hop Metadata Stack fields (`Local Namespace 4b`,
      `Device ID 20b`, `IP TTL 8b`, `Egress Port Speed 4b`, `Congestion 2b`, `Queue ID 6b`,
      `RX Timestamp Seconds 20b`, `Egress Port 16b`, `Ingress Port 16b`, `RX Timestamp Nanoseconds 32b`,
      `Residence Time Nanoseconds 32b`, and `Opaque Data 1/2/3 96b`), byte overhead vs `9000`-byte MTU,
      and per-hop residence time + wire propagation latency calculation
  - InfiniBand (`nvidia-devops` Volume 08 Ch. 9, Ch. 12, `index.md`, Labs 01-04) and RoCEv2 (`Volume 09` &
    `Legacy Volume 07`) fabric telemetry and alerting:
    * State vs cumulative counters vs rates/deltas (`SymbolErrorCounter` `12,034 -> 12,034` over `300 s`
      historical scar tissue vs `Day 1: 4 -> Day 4: 890 [+886, 295.33/day] -> Day 7: 41,200 [+40,310,
      13,436.67/day, 45.5x acceleration]` with `LinkDownedCounter: 0 -> 3 -> 11`)
    * InfiniBand `PortXmitWait` backpressure ratio & congestion classification (`port 3` `PortXmitWait =
      998,432` or `184,320` vs `41` on `port 7` with `SymbolErrorCounter = 0`), `PortXmitData` `4`-octet
      word conversion (`21,474,836,480` B vs `1,073,741,824` B `20:1` spine imbalance), and `ib_write_lat`
      tail latency (`1.58` vs `1.55 us` typical, `2.90` vs `1.71 us` `p99`, `5.77` vs `1.98 us` `p99.9`)
    * RoCEv2 `ECN` / `CNP` / `PFC` storm detection (`rx_ecn_marked_prio3`, `np_cnp_handled`, `rx_pfc_prio3`,
      `tx_pfc_prio3`, `fec_corrected_blocks`, `fec_uncorrected_blocks`, `rx_crc_errors`)
    * Multi-rail bandwidth skew (`max/min` ratio across `8` rails; healthy `<= 1.15`, warning `> 1.30`,
      critical alert `> 1.50` when max rate `> 5.0 GB/s`) and Prometheus cardinality math.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. AI Network Performance KPIs & MLCommons / MLPerf Constants (ADC Ch. 10)
# ---------------------------------------------------------------------------

# Explicit formatted constants for provenance verification of derived arithmetic:
# - Power & Efficiency KPIs: 229,000 TFLOPS (229,000,000 GFLOPS), 18,320 samples/s, 91,600 QPS,
#   458,000 W (458.0 kW IT), 549.6 kW facility, PUE = 1.20, 500.0 GFLOPS/W IT, 416.6667 GFLOPS/W facility
# - SNMP vs microburst window: 60,000,000 us (60 s) vs 50 us spike
# - 3-stage IFA timestamps: rx 1,000,000 ns -> tx 1,000,650 ns (650 ns); rx 1,000,800 ns -> tx 1,015,200 ns
#   (14,400 ns = 91.4% of 15,750 ns total residence); rx 1,015,350 ns -> tx 1,016,050 ns (700 ns)
# - SymbolError acceleration: 45.5x (45.50x), PortXmitWait rate: 16,640.53 ticks/s, PFC storm rate: 1,551.67/s
# - 5-tuple cardinality explosion: 3,200,000,000 (3.2 billion) series (500x of 6,400,000 series)
MLCOMMONS_FOUNDED_YEAR: int = 2020
OPENAI_CHATGPT_A100_GPUS: int = 1_023
OPENAI_CHATGPT_TRAINING_DAYS: int = 34

# Numeric precision representation in bytes (ADC Ch. 10)
NUMERIC_PRECISION_BYTES: Dict[str, int] = {
    "FP8_INT8": 1,     # 1-byte (8-bit) floating-point or integer
    "FP16_BF16": 2,    # 2-byte (16-bit) floating-point
    "FP32_INT32": 4,   # 4-byte (32-bit) single-precision float or integer
    "FP64_INT64": 8,   # 8-byte (64-bit) double-precision float or integer
    "FP128": 16,       # 16-byte (128-bit) quad-precision
    "FP256": 32,       # 32-byte (256-bit) extended precision (ADC Ch. 10 text lists 8/16/32-byte examples)
}

MLCOMMONS_INITIATIVES: Tuple[str, str, str] = (
    "MLPerf",
    "MLCube",
    "PAIR",  # People + AI Research
)

MLPERF_SUITES: Tuple[str, str, str] = (
    "MLPerf Training",
    "MLPerf Inference",
    "MLPerf Storage",
)

MLPERF_INFERENCE_DOMAINS: Tuple[str, str, str, str] = (
    "Data Center",
    "Edge",
    "Mobile",
    "Tiny",
)

MLPERF_DIVISIONS: Dict[str, str] = {
    "Closed": "Direct apples-to-apples hardware/software comparison with fixed model, dataset, and reference equivalence",
    "Open": "Algorithmic and model innovation allowed provided the predefined target quality metric is achieved",
}


@dataclass(frozen=True)
class ScalingEfficiencyResult:
    """Strong and weak scaling speedup and efficiency metrics (ADC Ch. 10)."""

    base_gpus: int
    scaled_gpus: int
    scale_factor: float
    strong_base_time_s: float
    strong_scaled_time_s: float
    strong_speedup: float
    strong_efficiency: float
    weak_base_step_time_s: float
    weak_scaled_step_time_s: float
    weak_efficiency: float


def compute_strong_and_weak_scaling(
    base_gpus: int,
    scaled_gpus: int,
    strong_base_time_s: float,
    strong_scaled_time_s: float,
    weak_base_step_time_s: float,
    weak_scaled_step_time_s: float,
) -> ScalingEfficiencyResult:
    """Compute strong scaling (fixed total problem size) and weak scaling (fixed problem size per GPU).

    - Scale factor k = scaled_gpus / base_gpus
    - Strong scaling speedup S_strong = T_strong(base) / T_strong(scaled)
    - Strong scaling efficiency E_strong = S_strong / k = T_strong(base) / (k * T_strong(scaled))
    - Weak scaling efficiency E_weak = T_weak(base) / T_weak(scaled) (with problem size scaled by k)
    """
    if base_gpus <= 0 or scaled_gpus <= 0:
        raise ValueError("GPU counts must be positive")
    if strong_base_time_s <= 0 or strong_scaled_time_s <= 0:
        raise ValueError("Strong scaling times must be positive")
    if weak_base_step_time_s <= 0 or weak_scaled_step_time_s <= 0:
        raise ValueError("Weak scaling step times must be positive")

    scale_factor = scaled_gpus / float(base_gpus)
    strong_speedup = strong_base_time_s / strong_scaled_time_s
    strong_efficiency = strong_speedup / scale_factor
    weak_efficiency = weak_base_step_time_s / weak_scaled_step_time_s

    return ScalingEfficiencyResult(
        base_gpus=base_gpus,
        scaled_gpus=scaled_gpus,
        scale_factor=round(scale_factor, 4),
        strong_base_time_s=round(strong_base_time_s, 4),
        strong_scaled_time_s=round(strong_scaled_time_s, 4),
        strong_speedup=round(strong_speedup, 4),
        strong_efficiency=round(strong_efficiency, 4),
        weak_base_step_time_s=round(weak_base_step_time_s, 4),
        weak_scaled_step_time_s=round(weak_scaled_step_time_s, 4),
        weak_efficiency=round(weak_efficiency, 4),
    )


@dataclass(frozen=True)
class JctTailLatencyImpact:
    """Impact of communication fraction and collective tail latency on Job Completion Time (JCT)."""

    num_steps: int
    compute_ms_per_step: float
    ideal_comm_ms_per_step: float
    degraded_comm_ms_per_step: float
    ideal_step_ms: float
    degraded_step_ms: float
    ideal_comm_fraction: float
    degraded_comm_fraction: float
    comm_tail_inflation_ratio: float
    ideal_jct_hours: float
    degraded_jct_hours: float
    jct_slowdown_ratio: float
    wasted_gpu_hours: float


def compute_jct_and_tail_latency_impact(
    num_steps: int,
    compute_ms_per_step: float,
    ideal_comm_ms_per_step: float,
    degraded_comm_ms_per_step: float,
    non_overlapped_fraction: float = 1.0,
    cluster_gpus: int = 1024,
) -> JctTailLatencyImpact:
    """Calculate JCT inflation when fabric congestion or a straggler rail inflates collective latency.

    Each synchronous training step takes:
      T_step = T_compute + non_overlapped_fraction * T_comm
    Because AllReduce / AllToAll barriers synchronize all ranks, the slowest rail or microburst
    tail latency sets T_comm for the entire cluster.
    """
    if num_steps <= 0 or compute_ms_per_step < 0 or ideal_comm_ms_per_step <= 0 or degraded_comm_ms_per_step <= 0:
        raise ValueError("Invalid step or latency parameters")
    if not (0.0 <= non_overlapped_fraction <= 1.0):
        raise ValueError("non_overlapped_fraction must be in [0, 1]")

    eff_ideal_comm = ideal_comm_ms_per_step * non_overlapped_fraction
    eff_deg_comm = degraded_comm_ms_per_step * non_overlapped_fraction

    ideal_step_ms = compute_ms_per_step + eff_ideal_comm
    degraded_step_ms = compute_ms_per_step + eff_deg_comm

    ideal_comm_fraction = eff_ideal_comm / ideal_step_ms
    degraded_comm_fraction = eff_deg_comm / degraded_step_ms
    comm_tail_ratio = degraded_comm_ms_per_step / ideal_comm_ms_per_step

    ideal_jct_hours = (num_steps * ideal_step_ms) / (1000.0 * 3600.0)
    degraded_jct_hours = (num_steps * degraded_step_ms) / (1000.0 * 3600.0)
    jct_slowdown_ratio = degraded_jct_hours / ideal_jct_hours
    wasted_gpu_hours = (degraded_jct_hours - ideal_jct_hours) * cluster_gpus

    return JctTailLatencyImpact(
        num_steps=num_steps,
        compute_ms_per_step=round(compute_ms_per_step, 4),
        ideal_comm_ms_per_step=round(ideal_comm_ms_per_step, 4),
        degraded_comm_ms_per_step=round(degraded_comm_ms_per_step, 4),
        ideal_step_ms=round(ideal_step_ms, 4),
        degraded_step_ms=round(degraded_step_ms, 4),
        ideal_comm_fraction=round(ideal_comm_fraction, 4),
        degraded_comm_fraction=round(degraded_comm_fraction, 4),
        comm_tail_inflation_ratio=round(comm_tail_ratio, 4),
        ideal_jct_hours=round(ideal_jct_hours, 4),
        degraded_jct_hours=round(degraded_jct_hours, 4),
        jct_slowdown_ratio=round(jct_slowdown_ratio, 4),
        wasted_gpu_hours=round(wasted_gpu_hours, 2),
    )


@dataclass(frozen=True)
class PowerAndEfficiencyKpis:
    """Data center PUE, FLOPS/Watt (FPW), Throughput/Watt (TPW), and QPS/Watt (QPW) (ADC Ch. 10)."""

    total_facility_power_kw: float
    it_equipment_power_kw: float
    pue: float
    achieved_tflops: float
    samples_per_sec: float
    queries_per_sec: float
    gflops_per_watt_it: float
    gflops_per_watt_facility: float
    tpw_samples_per_watt: float
    qpw_queries_per_watt: float


def compute_power_and_efficiency_kpis(
    total_facility_power_kw: float,
    it_equipment_power_kw: float,
    achieved_tflops: float,
    samples_per_sec: float,
    queries_per_sec: float,
) -> PowerAndEfficiencyKpis:
    """Compute PUE, FLOPS/Watt (FPW), Throughput/Watt (TPW), and QPS/Watt (QPW) per ADC Ch. 10 & App. A."""
    if total_facility_power_kw <= 0 or it_equipment_power_kw <= 0:
        raise ValueError("Power values must be positive")
    if total_facility_power_kw < it_equipment_power_kw:
        raise ValueError("Total facility power cannot be less than IT equipment power")

    pue = total_facility_power_kw / it_equipment_power_kw
    it_watts = it_equipment_power_kw * 1000.0
    facility_watts = total_facility_power_kw * 1000.0
    total_gflops = achieved_tflops * 1000.0

    return PowerAndEfficiencyKpis(
        total_facility_power_kw=round(total_facility_power_kw, 2),
        it_equipment_power_kw=round(it_equipment_power_kw, 2),
        pue=round(pue, 4),
        achieved_tflops=round(achieved_tflops, 2),
        samples_per_sec=round(samples_per_sec, 2),
        queries_per_sec=round(queries_per_sec, 2),
        gflops_per_watt_it=round(total_gflops / it_watts, 4),
        gflops_per_watt_facility=round(total_gflops / facility_watts, 4),
        tpw_samples_per_watt=round(samples_per_sec / it_watts, 6),
        qpw_queries_per_watt=round(queries_per_sec / it_watts, 6),
    )


@dataclass(frozen=True)
class MlperfEvaluationResult:
    """Validation result for MLPerf Training or Inference LoadGen run (ADC Ch. 10)."""

    suite: str
    division: str
    scenario: str
    achieved_accuracy: float
    target_accuracy: float
    accuracy_passed: bool
    achieved_p99_latency_ms: float
    target_p99_latency_ms: float
    latency_sla_passed: bool
    primary_metric_value: float
    primary_metric_unit: str
    valid_submission: bool


def evaluate_mlperf_submission(
    suite: str,
    division: str,
    scenario: str,
    achieved_accuracy: float,
    target_accuracy: float,
    primary_metric_value: float,
    achieved_p99_latency_ms: float = 0.0,
    target_p99_latency_ms: float = 0.0,
) -> MlperfEvaluationResult:
    """Validate an MLPerf Training or Inference (Offline / Server) benchmark run per ADC Ch. 10."""
    if division not in MLPERF_DIVISIONS:
        raise ValueError(f"Unsupported MLPerf division: {division}")
    if suite not in MLPERF_SUITES:
        raise ValueError(f"Unsupported MLPerf suite: {suite}")

    accuracy_passed = achieved_accuracy >= target_accuracy
    if suite == "MLPerf Inference" and scenario == "Server":
        latency_sla_passed = achieved_p99_latency_ms <= target_p99_latency_ms and target_p99_latency_ms > 0
        unit = "queries/sec (Poisson Server QPS)"
    elif suite == "MLPerf Inference" and scenario == "Offline":
        latency_sla_passed = True
        unit = "samples/sec (Offline Throughput)"
    elif suite == "MLPerf Training":
        latency_sla_passed = True
        unit = "minutes (Time to Train)"
    else:
        latency_sla_passed = True
        unit = "MB/sec (Storage Bandwidth)"

    valid_submission = accuracy_passed and latency_sla_passed and primary_metric_value > 0
    return MlperfEvaluationResult(
        suite=suite,
        division=division,
        scenario=scenario,
        achieved_accuracy=round(achieved_accuracy, 4),
        target_accuracy=round(target_accuracy, 4),
        accuracy_passed=accuracy_passed,
        achieved_p99_latency_ms=round(achieved_p99_latency_ms, 3),
        target_p99_latency_ms=round(target_p99_latency_ms, 3),
        latency_sla_passed=latency_sla_passed,
        primary_metric_value=round(primary_metric_value, 2),
        primary_metric_unit=unit,
        valid_submission=valid_submission,
    )


# ---------------------------------------------------------------------------
# 2. In-Band Flow Analyzer (IFA, draft-kumar-ippm-ifa-08, ADC Ch. 11)
# ---------------------------------------------------------------------------

# Figure 11-3: IFA Header Format (32 bits = 4 bytes total)
IFA_HEADER_FIELD_BITS: Dict[str, int] = {
    "IFA_Version": 4,
    "Global_Namespace": 4,
    "Protocol_Type": 8,
    "Flags": 8,
    "Max_Length": 8,
}
IFA_HEADER_BYTES: int = sum(IFA_HEADER_FIELD_BITS.values()) // 8  # 4 bytes

# IFA Metadata Header (pushed by Initiator node: action + hop limit = 32 bits = 4 bytes)
IFA_METADATA_HEADER_BYTES: int = 4

# Figure 11-4: IFA Metadata Stack per-hop entry (8 rows x 32 bits = 256 bits = 32 bytes per hop)
IFA_METADATA_STACK_ROW_BITS: Tuple[Tuple[str, Dict[str, int]], ...] = (
    ("Row 1", {"Local_Namespace": 4, "Device_ID": 20, "IP_TTL": 8}),
    ("Row 2", {"Egress_Port_Speed": 4, "Congestion": 2, "Queue_ID": 6, "RX_Timestamp_Seconds": 20}),
    ("Row 3", {"Egress_Port_Number": 16, "Ingress_Port_Number": 16}),
    ("Row 4", {"RX_Timestamp_Nanoseconds": 32}),
    ("Row 5", {"Residence_Time_Nanoseconds": 32}),
    ("Row 6", {"Opaque_Data_1_Reserved": 32}),
    ("Row 7", {"Opaque_Data_2_High_Reserved": 16, "Opaque_Data_2_Low_Reserved": 16}),
    ("Row 8", {"Opaque_Data_3_Reserved": 32}),
)
IFA_PER_HOP_METADATA_BITS: int = sum(
    sum(fields.values()) for _, fields in IFA_METADATA_STACK_ROW_BITS
)  # 256 bits
IFA_PER_HOP_METADATA_BYTES: int = IFA_PER_HOP_METADATA_BITS // 8  # 32 bytes

# Packet header order in Figure 11-2 (ADC Ch. 11)
IFA_PACKET_HEADER_SEQUENCE: Tuple[str, ...] = (
    "L2 Header",
    "L3 Header",
    "IFA Header",
    "L4 Header",
    "IFA Metadata Header",
    "IFA Metadata Stack",
    "Payload",
)

# Typical Clos fabric hop counts for 3-stage (Leaf-Spine-Leaf) and 5-stage (Leaf-Spine-SuperSpine-Spine-Leaf)
IFA_3_STAGE_HOPS: int = 3
IFA_5_STAGE_HOPS: int = 5
FABRIC_JUMBO_MTU_BYTES: int = 9000


@dataclass(frozen=True)
class IfaHopTelemetry:
    """Single switch hop entry in an IFA metadata stack (Figure 11-4, ADC Ch. 11)."""

    hop_index: int
    role: str  # "Initiator", "Transit", or "Terminator"
    device_id: int
    ingress_port: int
    egress_port: int
    queue_id: int
    egress_port_speed_gbps: int
    rx_timestamp_ns: int
    tx_timestamp_ns: int
    residence_time_ns: int
    wire_propagation_ns: int
    hop_total_latency_ns: int
    ecn_enabled_on_egress: bool
    congestion_bits: int  # 2-bit field (0..3)
    congestion_meaningful: bool


@dataclass(frozen=True)
class IfaFlowTraceAnalysis:
    """End-to-end IFA trace analysis across a 3-stage or 5-stage AI fabric."""

    fabric_stages: int
    hop_count: int
    base_packet_bytes: int
    ifa_fixed_headers_bytes: int
    ifa_metadata_stack_bytes: int
    total_ifa_overhead_bytes: int
    tagged_packet_bytes: int
    mtu_bytes: int
    fits_within_mtu: bool
    total_residence_time_ns: int
    total_wire_time_ns: int
    end_to_end_latency_ns: int
    end_to_end_latency_us: float
    bottleneck_device_id: int
    bottleneck_role: str
    bottleneck_residence_ns: int
    congested_hops: Tuple[int, ...]
    collector_export_format: str


def analyze_ifa_flow_trace(
    hops: Sequence[Dict[str, int | str | bool]],
    base_packet_bytes: int = 4200,
    mtu_bytes: int = FABRIC_JUMBO_MTU_BYTES,
) -> IfaFlowTraceAnalysis:
    """Compute IFA header byte overhead, per-hop residence + wire time, and bottleneck hop (ADC Ch. 11).

    In ADC Ch. 11:
      - Residence time = tx_timestamp_ns - rx_timestamp_ns (time spent inside a single switch hop)
      - Per-hop latency = residence_time_ns + wire_propagation_ns
      - Congestion field (2 bits) is only meaningful when ECN is enabled on the egress port
      - Terminating leaf strips metadata (or drops cloned probe) and exports telemetry via IPFIX.
    """
    if not hops:
        raise ValueError("IFA trace must contain at least one hop")

    hop_count = len(hops)
    fixed_bytes = IFA_HEADER_BYTES + IFA_METADATA_HEADER_BYTES  # 4 + 4 = 8 bytes
    stack_bytes = hop_count * IFA_PER_HOP_METADATA_BYTES        # 32 bytes per hop
    total_overhead = fixed_bytes + stack_bytes
    tagged_bytes = base_packet_bytes + total_overhead

    total_residence_ns = 0
    total_wire_ns = 0
    bottleneck_device_id = -1
    bottleneck_role = ""
    bottleneck_residence_ns = -1
    congested_hops: List[int] = []

    for idx, h in enumerate(hops):
        rx_ns = int(h["rx_timestamp_ns"])
        tx_ns = int(h["tx_timestamp_ns"])
        if tx_ns < rx_ns:
            raise ValueError(f"Hop {idx} tx_timestamp_ns ({tx_ns}) < rx_timestamp_ns ({rx_ns})")
        residence_ns = tx_ns - rx_ns
        wire_ns = int(h.get("wire_propagation_ns", 0))
        device_id = int(h["device_id"])
        role = str(h["role"])
        ecn_enabled = bool(h.get("ecn_enabled_on_egress", True))
        cong_bits = int(h.get("congestion_bits", 0))

        total_residence_ns += residence_ns
        total_wire_ns += wire_ns

        if residence_ns > bottleneck_residence_ns:
            bottleneck_residence_ns = residence_ns
            bottleneck_device_id = device_id
            bottleneck_role = role

        if ecn_enabled and cong_bits > 0:
            congested_hops.append(device_id)

    e2e_ns = total_residence_ns + total_wire_ns
    return IfaFlowTraceAnalysis(
        fabric_stages=hop_count,
        hop_count=hop_count,
        base_packet_bytes=base_packet_bytes,
        ifa_fixed_headers_bytes=fixed_bytes,
        ifa_metadata_stack_bytes=stack_bytes,
        total_ifa_overhead_bytes=total_overhead,
        tagged_packet_bytes=tagged_bytes,
        mtu_bytes=mtu_bytes,
        fits_within_mtu=tagged_bytes <= mtu_bytes,
        total_residence_time_ns=total_residence_ns,
        total_wire_time_ns=total_wire_ns,
        end_to_end_latency_ns=e2e_ns,
        end_to_end_latency_us=round(e2e_ns / 1000.0, 3),
        bottleneck_device_id=bottleneck_device_id,
        bottleneck_role=bottleneck_role,
        bottleneck_residence_ns=bottleneck_residence_ns,
        congested_hops=tuple(congested_hops),
        collector_export_format="IPFIX",
    )


# ---------------------------------------------------------------------------
# 3. InfiniBand PortXmitWait, Symbol Errors & Tail Latency (V8 Ch. 9, 12, Labs 01-04)
# ---------------------------------------------------------------------------

IB_DATA_WORD_BYTES: int = 4  # PortXmitData / PortRcvData count 32-bit (4-octet) words


@dataclass(frozen=True)
class IbPortTelemetryClassification:
    """InfiniBand port counter delta and PortXmitWait backpressure evaluation (V8 Ch. 9 & Lab 03)."""

    port_label: str
    window_s: float
    xmit_data_words_delta: int
    xmit_bytes_delta: int
    throughput_gbps: float
    xmit_pkts_delta: int
    xmit_wait_delta: int
    wait_ticks_per_sec: float
    wait_to_pkt_ratio: float
    symbol_error_delta: int
    link_downed_delta: int
    xmit_discards_delta: int
    classification: str
    recommended_action: str
    alert_severity: str


def evaluate_infiniband_port_telemetry(
    port_label: str,
    window_s: float,
    xmit_data_words_t0: int,
    xmit_data_words_t1: int,
    xmit_pkts_t0: int,
    xmit_pkts_t1: int,
    xmit_wait_t0: int,
    xmit_wait_t1: int,
    symbol_err_t0: int,
    symbol_err_t1: int,
    link_downed_t0: int = 0,
    link_downed_t1: int = 0,
    xmit_discards_t0: int = 0,
    xmit_discards_t1: int = 0,
) -> IbPortTelemetryClassification:
    """Classify InfiniBand port health from counter deltas (`perfquery` / `ibqueryerrors`, V8 Ch. 9).

    Distinguishes:
      - `PHYSICAL_LINK_DEGRADATION`: SymbolErrorCounter delta > 0 or LinkDownedCounter delta > 0
      - `ROUTING_OR_POLICY_DISCARD`: PortXmitDiscards delta > 0 with clean physical counters
      - `CREDIT_BACKPRESSURE_CONGESTION`: PortXmitWait rate >= 1,000 ticks/s (or wait_to_pkt_ratio >= 0.05)
        with SymbolErrorCounter delta == 0 and LinkDownedCounter delta == 0
      - `HISTORICAL_SCAR_TISSUE`: cumulative SymbolErrorCounter > 0 at t0, but delta == 0 over window
      - `HEALTHY_ACTIVE`: clean deltas and low PortXmitWait.
    """
    if window_s <= 0:
        raise ValueError("Observation window_s must be positive")

    words_delta = max(0, xmit_data_words_t1 - xmit_data_words_t0)
    bytes_delta = words_delta * IB_DATA_WORD_BYTES
    throughput_gbps = (bytes_delta * 8.0) / (window_s * 1e9)
    pkts_delta = max(0, xmit_pkts_t1 - xmit_pkts_t0)
    wait_delta = max(0, xmit_wait_t1 - xmit_wait_t0)
    wait_rate = wait_delta / window_s
    wait_ratio = (wait_delta / float(pkts_delta)) if pkts_delta > 0 else float(wait_delta)
    sym_delta = max(0, symbol_err_t1 - symbol_err_t0)
    down_delta = max(0, link_downed_t1 - link_downed_t0)
    disc_delta = max(0, xmit_discards_t1 - xmit_discards_t0)

    if down_delta > 0 or sym_delta > 0:
        classification = "PHYSICAL_LINK_DEGRADATION"
        action = "Inspect mlxlink -c -m optical DOM/BER; fence port (ibportstate disable) and replace cable/optic"
        severity = "PAGE" if down_delta > 0 or sym_delta >= 100 else "TICKET"
    elif disc_delta > 0:
        classification = "ROUTING_OR_POLICY_DISCARD"
        action = "Inspect ibroute LFT, P_Key table, and switch head-of-queue lifetime limit"
        severity = "PAGE"
    elif wait_rate >= 1000.0 or wait_ratio >= 0.05:
        classification = "CREDIT_BACKPRESSURE_CONGESTION"
        action = "Do NOT replace cable; trace PortXmitWait gradient downstream to congestion root and check AR/SL"
        severity = "TICKET" if wait_rate < 10_000.0 else "PAGE"
    elif symbol_err_t0 > 0 and sym_delta == 0:
        classification = "HISTORICAL_SCAR_TISSUE"
        action = "Do NOT replace cable; cumulative counter is static over active window (delta == 0)"
        severity = "NONE"
    else:
        classification = "HEALTHY_ACTIVE"
        action = "No action required; port physical and credit counters within baseline"
        severity = "NONE"

    return IbPortTelemetryClassification(
        port_label=port_label,
        window_s=round(window_s, 2),
        xmit_data_words_delta=words_delta,
        xmit_bytes_delta=bytes_delta,
        throughput_gbps=round(throughput_gbps, 4),
        xmit_pkts_delta=pkts_delta,
        xmit_wait_delta=wait_delta,
        wait_ticks_per_sec=round(wait_rate, 2),
        wait_to_pkt_ratio=round(wait_ratio, 4),
        symbol_error_delta=sym_delta,
        link_downed_delta=down_delta,
        xmit_discards_delta=disc_delta,
        classification=classification,
        recommended_action=action,
        alert_severity=severity,
    )


@dataclass(frozen=True)
class SymbolErrorAccelerationReport:
    """Multi-window SymbolErrorCounter rate and acceleration analysis ('The Fabric Failed Slowly', V8 Ch. 9)."""

    port_label: str
    day1_errors: int
    day4_errors: int
    day7_errors: int
    window1_days: float
    window2_days: float
    window1_delta: int
    window2_delta: int
    window1_rate_per_day: float
    window2_rate_per_day: float
    acceleration_ratio: float
    link_downed_total: int
    alert_triggered: bool


def evaluate_symbol_error_acceleration(
    port_label: str,
    day1_errors: int,
    day4_errors: int,
    day7_errors: int,
    window1_days: float = 3.0,
    window2_days: float = 3.0,
    link_downed_total: int = 11,
) -> SymbolErrorAccelerationReport:
    """Model the V8 Ch. 9 'The Fabric Failed Slowly' counter rate acceleration (4 -> 890 -> 41,200)."""
    if window1_days <= 0 or window2_days <= 0:
        raise ValueError("Observation windows must be positive")
    w1_delta = day4_errors - day1_errors
    w2_delta = day7_errors - day4_errors
    w1_rate = w1_delta / window1_days
    w2_rate = w2_delta / window2_days
    accel = (w2_rate / w1_rate) if w1_rate > 0 else float("inf")
    alert = w2_rate > 100.0 or accel >= 2.0 or link_downed_total > 0

    return SymbolErrorAccelerationReport(
        port_label=port_label,
        day1_errors=day1_errors,
        day4_errors=day4_errors,
        day7_errors=day7_errors,
        window1_days=window1_days,
        window2_days=window2_days,
        window1_delta=w1_delta,
        window2_delta=w2_delta,
        window1_rate_per_day=round(w1_rate, 2),
        window2_rate_per_day=round(w2_rate, 2),
        acceleration_ratio=round(accel, 2),
        link_downed_total=link_downed_total,
        alert_triggered=alert,
    )


# ---------------------------------------------------------------------------
# 4. RoCEv2 ECN / CNP / PFC Storm & FEC Telemetry Triage (ADC Ch. 11 & V9 / V7)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoceTelemetryTriageResult:
    """RoCEv2 switch + NIC counter correlation for ECN, CNP, PFC, drops, and FEC."""

    interface: str
    window_s: float
    rx_ecn_marked_delta: int
    np_cnp_sent_or_handled_delta: int
    rx_pfc_pause_delta: int
    tx_pfc_pause_delta: int
    pfc_pause_rate_per_sec: float
    cnp_to_ecn_ratio: float
    lossless_queue_drops_delta: int
    fec_corrected_delta: int
    fec_uncorrected_delta: int
    rx_crc_errors_delta: int
    rp_current_rate_gbps: float
    line_rate_gbps: float
    classification: str
    alert_severity: str
    remediation: str


def evaluate_rocev2_congestion_and_fec(
    interface: str,
    window_s: float,
    rx_ecn_marked_delta: int,
    np_cnp_sent_or_handled_delta: int,
    rx_pfc_pause_delta: int,
    tx_pfc_pause_delta: int,
    lossless_queue_drops_delta: int = 0,
    fec_corrected_delta: int = 0,
    fec_uncorrected_delta: int = 0,
    rx_crc_errors_delta: int = 0,
    rp_current_rate_gbps: float = 100.0,
    line_rate_gbps: float = 100.0,
    pfc_storm_rate_threshold_per_sec: float = 1000.0,
) -> RoceTelemetryTriageResult:
    """Correlate RoCEv2 switch ECN/PFC/drop counters with NIC CNP/RP/FEC counters (ADC Ch. 11, Ch. 2.31, V9).

    Classifies six canonical operational states:
      1. `PHYSICAL_FEC_CRC_CORRUPTION`: fec_uncorrected_delta > 0 or rx_crc_errors_delta > 0
      2. `LOSSLESS_QUEUE_BUFFER_DROP`: lossless_queue_drops_delta > 0
      3. `BROKEN_DCQCN_CNP_LOOP`: rx_ecn_marked_delta >= 1000 and np_cnp_sent_or_handled_delta == 0
      4. `PFC_PAUSE_RELAY_HOP`: both rx_pfc_pause_delta >= 1000 and tx_pfc_pause_delta >= 1000
      5. `WEAK_RP_OR_PFC_STORM`: pfc_pause_rate_per_sec >= threshold (or high ECN+PFC with rp_rate >= 95% line rate)
      6. `PROACTIVE_ECN_CONTAINED`: rx_ecn_marked_delta > 0, cnp_to_ecn_ratio >= 0.80, low PFC rate, 0 drops.
    """
    if window_s <= 0:
        raise ValueError("window_s must be positive")

    total_pfc = rx_pfc_pause_delta + tx_pfc_pause_delta
    pfc_rate = rx_pfc_pause_delta / window_s
    cnp_ratio = (
        np_cnp_sent_or_handled_delta / float(rx_ecn_marked_delta)
        if rx_ecn_marked_delta > 0
        else 1.0
    )

    if fec_uncorrected_delta > 0 or rx_crc_errors_delta > 0:
        classification = "PHYSICAL_FEC_CRC_CORRUPTION"
        severity = "PAGE"
        remediation = "Replace degraded DAC/optic first; unrecoverable FEC/CRC frames trigger RDMA retries and secondary ECN"
    elif lossless_queue_drops_delta > 0:
        classification = "LOSSLESS_QUEUE_BUFFER_DROP"
        severity = "PAGE"
        remediation = "Audit Mirror-on-Drop / WJH drop reason, DSCP->TC3 trust mapping, and PFC XOFF headroom"
    elif rx_ecn_marked_delta >= 1000 and np_cnp_sent_or_handled_delta == 0:
        classification = "BROKEN_DCQCN_CNP_LOOP"
        severity = "PAGE"
        remediation = "Switch is ECN-marking but NIC handles 0 CNPs; verify NIC ECN/DCQCN enablement and DSCP 48 CNP return path"
    elif rx_pfc_pause_delta >= 1000 and tx_pfc_pause_delta >= 1000:
        classification = "PFC_PAUSE_RELAY_HOP"
        severity = "PAGE"
        remediation = "Port is a middle relay hop propagating PFC upstream; walk in rx_pfc direction until tx_pfc == 0"
    elif pfc_rate >= pfc_storm_rate_threshold_per_sec or (
        rx_ecn_marked_delta >= 10_000
        and rx_pfc_pause_delta >= 10_000
        and rp_current_rate_gbps >= 0.95 * line_rate_gbps
    ):
        classification = "WEAK_RP_OR_PFC_STORM"
        severity = "PAGE"
        remediation = "ECN+CNP loop is active but sender RP rate cut is too weak or leaf cut is oversubscribed; tune RP / placement"
    elif rx_ecn_marked_delta > 0 and cnp_ratio >= 0.80:
        classification = "PROACTIVE_ECN_CONTAINED"
        severity = "NONE"
        remediation = "Healthy DCQCN closed loop; ECN marks are reflected as CNPs and pacing senders before PFC storm"
    else:
        classification = "HEALTHY_IDLE_OR_UNCONGESTED"
        severity = "NONE"
        remediation = "No congestion or physical error anomaly detected"

    return RoceTelemetryTriageResult(
        interface=interface,
        window_s=round(window_s, 2),
        rx_ecn_marked_delta=rx_ecn_marked_delta,
        np_cnp_sent_or_handled_delta=np_cnp_sent_or_handled_delta,
        rx_pfc_pause_delta=rx_pfc_pause_delta,
        tx_pfc_pause_delta=tx_pfc_pause_delta,
        pfc_pause_rate_per_sec=round(pfc_rate, 2),
        cnp_to_ecn_ratio=round(cnp_ratio, 4),
        lossless_queue_drops_delta=lossless_queue_drops_delta,
        fec_corrected_delta=fec_corrected_delta,
        fec_uncorrected_delta=fec_uncorrected_delta,
        rx_crc_errors_delta=rx_crc_errors_delta,
        rp_current_rate_gbps=round(rp_current_rate_gbps, 2),
        line_rate_gbps=round(line_rate_gbps, 2),
        classification=classification,
        alert_severity=severity,
        remediation=remediation,
    )


# ---------------------------------------------------------------------------
# 5. Multi-Rail Bandwidth Skew, ECMP Balance & Telemetry Scale Math (Ch. 2.31 & V8 Ch. 6/9)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RailBandwidthSkewResult:
    """Multi-rail node throughput balance analysis across 8 GPU NIC rails."""

    node_name: str
    rail_count: int
    max_rail_index: int
    min_rail_index: int
    max_rate_gbps: float
    min_rate_gbps: float
    mean_rate_gbps: float
    max_to_min_ratio: float
    active_load_above_threshold: bool
    skew_status: str
    alert_severity: str


def evaluate_rail_bandwidth_skew(
    node_name: str,
    rail_rates_gbps: Sequence[float],
    active_load_floor_gbps: float = 40.0,  # 5e9 bytes/s = 40 Gbps in PromQL alert rule
    warn_ratio_threshold: float = 1.30,
    page_ratio_threshold: float = 1.50,
) -> RailBandwidthSkewResult:
    """Evaluate max/min rail bandwidth skew across a node's rails (Ch. 2.31 & V8 Ch. 9 Scenario 3).

    Matches the PromQL rule:
      (max by (instance) (rate(node_network_transmit_bytes_total[2m]))
       / min by (instance) (rate(node_network_transmit_bytes_total[2m]))) > 1.5
      and max by (instance) (rate(node_network_transmit_bytes_total[2m])) > 5e9 (40 Gbps).
    """
    if not rail_rates_gbps:
        raise ValueError("rail_rates_gbps must not be empty")
    if any(r < 0 for r in rail_rates_gbps):
        raise ValueError("Rail rates cannot be negative")

    max_rate = max(rail_rates_gbps)
    min_rate = min(rail_rates_gbps)
    max_idx = rail_rates_gbps.index(max_rate)
    min_idx = rail_rates_gbps.index(min_rate)
    mean_rate = sum(rail_rates_gbps) / float(len(rail_rates_gbps))

    ratio = (max_rate / min_rate) if min_rate > 0 else float("inf")
    active = max_rate >= active_load_floor_gbps

    if not active:
        status = "IDLE_BELOW_LOAD_FLOOR"
        severity = "NONE"
    elif ratio > page_ratio_threshold:
        status = "CRITICAL_RAIL_SKEW"
        severity = "TICKET_OR_PAGE"
    elif ratio > warn_ratio_threshold:
        status = "WARNING_RAIL_SKEW"
        severity = "WARN"
    else:
        status = "BALANCED_RAILS"
        severity = "NONE"

    return RailBandwidthSkewResult(
        node_name=node_name,
        rail_count=len(rail_rates_gbps),
        max_rail_index=max_idx,
        min_rail_index=min_idx,
        max_rate_gbps=round(max_rate, 2),
        min_rate_gbps=round(min_rate, 2),
        mean_rate_gbps=round(mean_rate, 2),
        max_to_min_ratio=round(ratio, 4) if ratio != float("inf") else float("inf"),
        active_load_above_threshold=active,
        skew_status=status,
        alert_severity=severity,
    )


@dataclass(frozen=True)
class TelemetryScaleEstimate:
    """Streaming telemetry sample rate and Prometheus time-series cardinality estimate."""

    num_switches: int
    ports_per_switch: int
    queues_per_port: int
    port_metrics_count: int
    queue_metrics_count: int
    sample_interval_s: float
    active_series_per_switch: int
    total_active_series: int
    samples_per_sec_per_switch: float
    total_samples_per_sec: float
    per_flow_high_cardinality_series: int
    cardinality_explosion_multiplier: float


def estimate_telemetry_scale_and_cardinality(
    num_switches: int = 1000,
    ports_per_switch: int = 64,
    queues_per_port: int = 8,
    port_metrics_count: int = 36,
    queue_metrics_count: int = 8,
    sample_interval_s: float = 10.0,
    distinct_5tuples_per_port: int = 500,
) -> TelemetryScaleEstimate:
    """Compute switch telemetry ingestion rate and demonstrate 5-tuple label cardinality explosion."""
    if num_switches <= 0 or ports_per_switch <= 0 or sample_interval_s <= 0:
        raise ValueError("Invalid switch or interval parameters")

    counters_per_port = port_metrics_count + (queues_per_port * queue_metrics_count)
    series_per_switch = ports_per_switch * counters_per_port
    total_series = num_switches * series_per_switch

    samples_per_sw_sec = series_per_switch / sample_interval_s
    total_samples_sec = total_series / sample_interval_s

    per_flow_series = total_series * distinct_5tuples_per_port
    explosion_mult = per_flow_series / float(total_series)

    return TelemetryScaleEstimate(
        num_switches=num_switches,
        ports_per_switch=ports_per_switch,
        queues_per_port=queues_per_port,
        port_metrics_count=port_metrics_count,
        queue_metrics_count=queue_metrics_count,
        sample_interval_s=sample_interval_s,
        active_series_per_switch=series_per_switch,
        total_active_series=total_series,
        samples_per_sec_per_switch=round(samples_per_sw_sec, 2),
        total_samples_per_sec=round(total_samples_sec, 2),
        per_flow_high_cardinality_series=per_flow_series,
        cardinality_explosion_multiplier=round(explosion_mult, 2),
    )
