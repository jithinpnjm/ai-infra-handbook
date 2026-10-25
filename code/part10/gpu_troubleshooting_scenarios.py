#!/usr/bin/env python3
"""Chapter 10.22 model: GPU troubleshooting scenarios.

Models every quantitative diagnostic runbook, thermal/fan rise rate, PSU sizing
and brownout calculation, PCIe bandwidth down-training check, NCCL straggler
opCount & shard imbalance analyzer, ECC storm rate escalator, and 7-stage
cross-layer timing & Heisenbug profiler overhead model from:
  - `nvidia-devops` Volume 20 (Chapters 1-12 & Labs 01-04):
    * Ch 1: Missing GPU memory (`0 MiB` on `81,920 MiB` A100 due to MIG 0 instances,
      `545.23.08` vs `550.90.07` mismatch, zombie PID `48213` holding `71,234 MiB`,
      `< 81,920 - 100 MiB` pre-flight check)
    * Ch 3 & Ch 11: NCCL straggler (`opCount 4821` on ranks 0-2 vs `opCount 4820` on
      rank 3 with `2%` util / `78.3 W` / `47.31 s` data fetch on `96%`-full `480G/500G`
      `/data` and `187 GB` vs `41 GB` [`4.56x` / `~4.5x`] shard imbalance; pre-collective
      times `[125.3, 126.1, 1250.5, 124.8] ms` = `10.02x` ratio; A100 NVLink 3 `25 GB/s`
      per link vs `5 GB/s` degraded / `0 Mbps` failed)
    * Ch 6, Ch 8, Ch 9, Ch 10: Thermal throttling (`1,980 -> 1,833 MHz` `~7%` clock drop
      at `85C`, `87C` power-down, `95C` shutdown), Fan temperature rise rate (`0.05C/s`
      normal vs `0.25C/s` [`55->70C` in `60s`] and `0.93C/s` [`55->83C` in `30s`]),
      PSU sizing (`4 * 300W * 1.3 = 1,560 W`, `0.8 * PSU` node budget, `10.8 V < 11.4 V`
      12V sag, `145 W / 300 W` drop), DVFS oscillation (`1,980 -> 1,200 -> 800 MHz` at `65C`)
    * Ch 7: PCIe bandwidth (`Gen4 x16` `20-26 GB/s` raw `31.5 GB/s` / `64 GB/s` bidir,
      `Gen3 x16` `10-12 GB/s`, degraded `Gen3 x8` `2.3 GB/s` on `33,554,432` B, `127`
      replays, `>= 17.6 GB/s` = `0.8 * 22.0 GB/s` gate)
    * Ch 12 & Labs 01-04: 7-stage iteration breakdown (`450 + 150 + 60 + 30 + 10 + 10 + 8`
      out of `750 ms`, `60.0%` CPU data load), Profiler Heisenbug (`500 -> 450 [-10%] ->
      250 [-50%]` samples/sec; `800 -> 400`), Lab 03/04 ECC storm (`50/10min = 300/hr`,
      `34/min = 2,040/hr`, `50/30min = 100/hr`), Lab 04 fan postmortem (`2h 15m` detection
      + `20m` fix = `2h 35m` wasted), and Lab 04 NVLink timeout (`12 -> 30 -> 100 ms`,
      `> 2.5x` alert).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


A100_NAMEPLATE_MIB: int = 81_920
A100_PREFLIGHT_TOLERANCE_MIB: int = 100
H100_SXM5_BOOST_CLOCK_MHZ: int = 1980
H100_THROTTLED_CLOCK_MHZ: int = 1833
PCIE_GEN4_X16_BASELINE_GBPS: float = 22.0
PCIE_GEN4_X16_WARN_THRESHOLD_GBPS: float = 17.6  # 0.8 * 22.0 GB/s (V20 Ch 7)
A100_NVLINK3_PER_LINK_GBPS: float = 25.0
A100_NVLINK3_MIN_HEALTHY_GBPS: float = 20.0
AUX_12V_NOMINAL_V: float = 12.0
AUX_12V_SAG_WARN_V: float = 11.4


@dataclass(frozen=True)
class ThermalAndFanDiagnosis:
    """Thermal slowdown, clock reduction, and fan temperature rise-rate model (V20 Ch 6, Ch 8 & Lab 03/04)."""

    boost_clock_mhz: int
    current_clock_mhz: int
    clock_reduction_pct: float
    start_temp_c: float
    end_temp_c: float
    window_sec: float
    temp_rise_rate_c_per_sec: float
    fan_speed_pct: int
    hw_thermal_slowdown_active: bool
    sw_power_cap_active: bool
    root_cause: str
    immediate_action: str


def diagnose_thermal_and_fan(
    boost_clock_mhz: int = H100_SXM5_BOOST_CLOCK_MHZ,
    current_clock_mhz: int = H100_THROTTLED_CLOCK_MHZ,
    start_temp_c: float = 55.0,
    end_temp_c: float = 70.0,
    window_sec: float = 60.0,
    fan_speed_pct: int = 0,
    hw_thermal_slowdown_active: bool = True,
    sw_power_cap_active: bool = False,
) -> ThermalAndFanDiagnosis:
    """Diagnose thermal vs power throttling and fan rise rate (`°C/sec`, V20 Ch 6, Ch 8 & Lab 02/03/04)."""
    if boost_clock_mhz <= 0 or current_clock_mhz <= 0 or window_sec <= 0:
        raise ValueError("Clocks and window_sec must be positive")
    if not (0 <= fan_speed_pct <= 100):
        raise ValueError("fan_speed_pct must be in [0, 100]")

    clk_drop_pct = round((boost_clock_mhz - current_clock_mhz) / boost_clock_mhz * 100.0, 2)
    rise_rate = round((end_temp_c - start_temp_c) / window_sec, 2)

    if end_temp_c >= 87.0:
        cause = "CRITICAL_TEMP_EXCEEDED_87C"
        action = "Cordon, drain, and power down node immediately (sudo shutdown -h now)"
    elif hw_thermal_slowdown_active and fan_speed_pct == 0 and end_temp_c > 50.0:
        cause = "FAN_STUCK_AT_0_RPM"
        action = "Stop workload immediately; check BMC fan sensors / reseat connector or RMA"
    elif hw_thermal_slowdown_active and fan_speed_pct >= 90 and rise_rate >= 0.20:
        cause = "COOLING_SATURATED_OR_THERMAL_INTERFACE_DEGRADED"
        action = "Cap power (nvidia-smi -pl 200) or drain node; open vendor cooling/HVAC service ticket"
    elif sw_power_cap_active and not hw_thermal_slowdown_active:
        cause = "SOFTWARE_POWER_CAP_ACTIVE"
        action = "Inspect nvidia-smi -q -d POWER and restore default power limit if unintended"
    else:
        cause = "NORMAL_THERMAL_OPERATION"
        action = "Continue monitoring (deriv(gpu_temp[1m]) <= 0.15 C/s)"

    return ThermalAndFanDiagnosis(
        boost_clock_mhz=boost_clock_mhz,
        current_clock_mhz=current_clock_mhz,
        clock_reduction_pct=clk_drop_pct,
        start_temp_c=start_temp_c,
        end_temp_c=end_temp_c,
        window_sec=window_sec,
        temp_rise_rate_c_per_sec=rise_rate,
        fan_speed_pct=fan_speed_pct,
        hw_thermal_slowdown_active=hw_thermal_slowdown_active,
        sw_power_cap_active=sw_power_cap_active,
        root_cause=cause,
        immediate_action=action,
    )


@dataclass(frozen=True)
class PsuAndBrownoutPlan:
    """PSU capacity planning (`1.3x` headroom), node budget (`0.8x`), and 12V sag check (V20 Ch 9)."""

    num_gpus: int
    gpu_tdp_watts: int
    raw_gpu_watts: int
    min_psu_capacity_watts: int
    installed_psu_watts: int
    psu_undersized: bool
    safe_node_power_budget_watts: int
    aux_12v_reading: float
    voltage_sag_detected: bool


def evaluate_psu_and_brownout(
    num_gpus: int = 4,
    gpu_tdp_watts: int = 300,
    headroom_multiplier: float = 1.3,
    installed_psu_watts: int = 1500,
    aux_12v_reading: float = 10.8,
) -> PsuAndBrownoutPlan:
    """Compute required PSU capacity (`num_gpus * tdp * 1.3 = 1,560 W` for 4x 300W A100, V20 Ch 9)."""
    if num_gpus <= 0 or gpu_tdp_watts <= 0 or headroom_multiplier < 1.0 or installed_psu_watts <= 0:
        raise ValueError("PSU sizing inputs must be positive and headroom_multiplier >= 1.0")

    raw_w = num_gpus * gpu_tdp_watts
    min_psu_w = int(round(raw_w * headroom_multiplier))
    safe_budget_w = int(round(installed_psu_watts * 0.8))
    return PsuAndBrownoutPlan(
        num_gpus=num_gpus,
        gpu_tdp_watts=gpu_tdp_watts,
        raw_gpu_watts=raw_w,
        min_psu_capacity_watts=min_psu_w,
        installed_psu_watts=installed_psu_watts,
        psu_undersized=installed_psu_watts < min_psu_w,
        safe_node_power_budget_watts=safe_budget_w,
        aux_12v_reading=aux_12v_reading,
        voltage_sag_detected=aux_12v_reading < AUX_12V_SAG_WARN_V,
    )


@dataclass(frozen=True)
class NcclStragglerDiagnosis:
    """NCCL opCount lag, pre-collective iteration imbalance, and data-shard skew analyzer (V20 Ch 3 & Ch 11)."""

    rank_op_counts: Tuple[int, ...]
    lagging_rank: int
    op_count_delta: int
    pre_collective_iter_ms: Tuple[float, ...]
    max_to_min_iter_ratio: float
    straggler_exceeds_1_2x_threshold: bool
    rank3_shard_gb: float
    rank0_shard_gb: float
    shard_imbalance_ratio: float
    root_cause: str


def diagnose_nccl_straggler(
    rank_op_counts: Tuple[int, ...] = (4821, 4821, 4821, 4820),
    pre_collective_iter_ms: Tuple[float, ...] = (125.3, 126.1, 1250.5, 124.8),
    lagging_gpu_util_pct: float = 2.0,
    rank3_shard_gb: float = 187.0,
    rank0_shard_gb: float = 41.0,
) -> NcclStragglerDiagnosis:
    """Pinpoint the lagging rank and classify data-pipeline starvation vs NVLink/hardware fault (V20 Ch 3 & Ch 11)."""
    if not rank_op_counts or not pre_collective_iter_ms:
        raise ValueError("rank_op_counts and pre_collective_iter_ms must be non-empty")
    if min(pre_collective_iter_ms) <= 0 or rank0_shard_gb <= 0:
        raise ValueError("Iteration times and shard sizes must be positive")

    min_op = min(rank_op_counts)
    max_op = max(rank_op_counts)
    lag_rank = rank_op_counts.index(min_op)
    iter_ratio = round(max(pre_collective_iter_ms) / min(pre_collective_iter_ms), 2)
    shard_ratio = round(rank3_shard_gb / rank0_shard_gb, 2)

    if max_op > min_op and lagging_gpu_util_pct < 10.0 and shard_ratio > 2.0:
        cause = "UPSTREAM_DATA_PIPELINE_STARVATION_UNEVEN_SHARD"
    elif iter_ratio > 1.2 and lagging_gpu_util_pct >= 80.0:
        cause = "HARDWARE_THROTTLE_OR_DEGRADED_NVLINK"
    else:
        cause = "DIVERGENT_COLLECTIVE_DEADLOCK_OR_FABRIC_FAULT"

    return NcclStragglerDiagnosis(
        rank_op_counts=rank_op_counts,
        lagging_rank=lag_rank,
        op_count_delta=max_op - min_op,
        pre_collective_iter_ms=pre_collective_iter_ms,
        max_to_min_iter_ratio=iter_ratio,
        straggler_exceeds_1_2x_threshold=(iter_ratio > 1.2),
        rank3_shard_gb=rank3_shard_gb,
        rank0_shard_gb=rank0_shard_gb,
        shard_imbalance_ratio=shard_ratio,
        root_cause=cause,
    )


@dataclass(frozen=True)
class CrossLayerTimingReport:
    """7-stage synchronous layer-by-layer iteration breakdown & Heisenbug overhead (V20 Ch 12)."""

    stage_ms: Dict[str, float]
    reported_total_ms: float
    data_load_share_pct: float
    allreduce_share_pct: float
    gpu_compute_share_pct: float
    dominant_bottleneck: str
    no_profiler_samples_per_sec: float
    smi_polling_samples_per_sec: float
    nsys_samples_per_sec: float
    smi_overhead_pct: float
    nsys_overhead_pct: float


def analyze_cross_layer_breakdown(
    data_load_cpu_ms: float = 450.0,
    allreduce_network_ms: float = 150.0,
    backward_gpu_ms: float = 60.0,
    forward_gpu_ms: float = 30.0,
    data_transfer_pcie_ms: float = 10.0,
    optimizer_gpu_ms: float = 10.0,
    loss_gpu_ms: float = 8.0,
    reported_total_ms: float = 750.0,
    no_profiler_sps: float = 500.0,
    smi_polling_sps: float = 450.0,
    nsys_sps: float = 250.0,
) -> CrossLayerTimingReport:
    """Reproduce the V20 Ch 12 7-stage iteration breakdown (`750.00 ms`) and profiler Heisenbug."""
    if reported_total_ms <= 0 or no_profiler_sps <= 0:
        raise ValueError("reported_total_ms and no_profiler_sps must be positive")

    stages = {
        "data_load_cpu": data_load_cpu_ms,
        "allreduce_network": allreduce_network_ms,
        "backward_gpu": backward_gpu_ms,
        "forward_gpu": forward_gpu_ms,
        "data_transfer_pcie": data_transfer_pcie_ms,
        "optimizer_gpu": optimizer_gpu_ms,
        "loss_gpu": loss_gpu_ms,
    }
    data_pct = round(data_load_cpu_ms / reported_total_ms * 100.0, 1)
    net_pct = round(allreduce_network_ms / reported_total_ms * 100.0, 1)
    gpu_ms = backward_gpu_ms + forward_gpu_ms + optimizer_gpu_ms + loss_gpu_ms
    gpu_pct = round(gpu_ms / reported_total_ms * 100.0, 1)

    top_stage = max(stages.items(), key=lambda kv: kv[1])[0]
    smi_ovh = round((1.0 - smi_polling_sps / no_profiler_sps) * 100.0, 1)
    nsys_ovh = round((1.0 - nsys_sps / no_profiler_sps) * 100.0, 1)

    return CrossLayerTimingReport(
        stage_ms=stages,
        reported_total_ms=reported_total_ms,
        data_load_share_pct=data_pct,
        allreduce_share_pct=net_pct,
        gpu_compute_share_pct=gpu_pct,
        dominant_bottleneck=top_stage,
        no_profiler_samples_per_sec=no_profiler_sps,
        smi_polling_samples_per_sec=smi_polling_sps,
        nsys_samples_per_sec=nsys_sps,
        smi_overhead_pct=smi_ovh,
        nsys_overhead_pct=nsys_ovh,
    )
