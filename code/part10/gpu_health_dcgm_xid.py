#!/usr/bin/env python3
"""Chapter 10.21 model: GPU health: DCGM, ECC, row remapping and Xid.

Models every DCGM field & watch setting, diagnostic level, ECC counter & thermal
correlation rule, HBM row-remapper bank histogram, authoritative 15-code Xid
3-tier classification, GPU sharing isolation matrix, and SRE error-budget
calculation from:
  - `nvidia-devops` Volume 16 (Chapters 1-12 & Labs 01-04):
    * DCGM host engine (`nv-hostengine` standalone port `5555` vs embedded `libdcgm`
      in `dcgm-exporter` port `9400`), default collect interval `30,000 ms` (`30 s`),
      Xid count window `300,000 ms` (`5 min`), min `16 GB` host RAM, DCGM 4.5 + driver 590
      runtime GPU bind/unbind
    * `dcgmi diag` levels `1` (seconds), `2` (~2 min), `3` (~15 min), `4` (xlong)
    * Failure signatures & SLOs: `99.0%` availability (`7.3 hours/month` error budget
      out of `730` hours; `6.0 hours` used -> `1.3 hours` remaining), `98.0%` GPUs healthy
      (`temp <= 82C`, power `> 50W` under load, `0` DBE), `99.5%` job completion rate,
      `p50 = 2,000` / `p99 = 1,900` samples/sec
  - `nvidia-devops` Volume 20 (Chapters 1, 2, 4, 5 & Labs 01-04):
    * Authoritative 15-code Xid reference table & 3-tier triage (`Tier 1`: `45, 63, 92`;
      `Tier 2`: `13, 31, 32, 43, 94`; `Tier 3`: `48, 61, 62, 64, 79, 95`; NVLink `74`;
      GSP `119, 120`)
    * `Xid 92 -> 45 -> 79` cascade (`14:21:52 -> 14:21:58 -> 14:22:03`; SBE rising
      `12 -> 31 -> 58 -> 94` per 2h; weekly `12 -> 94` = `+683%`)
    * ECC `SBE` vs `DBE` (`42` Device Memory + `3` L2 Cache = `45` Volatile SBE,
      `891` Aggregate SBE, weekly deltas `3 -> 4 -> 5 -> 8` = `+167%` / `2.67x ~ 2.7x`
      with `0.81` thermal correlation at `71.2C` avg / `84.6C` max)
    * Page Retirement (`12` SBE, `2` DBE, `Pending Page Blacklist: Yes` on `81,920 MiB` A100)
      vs Row Remapper (`12` correctable, `0` uncorrectable, `Remapping Failure Occurred: No`,
      `640` total banks = `630` Max + `8` High + `2` Partial + `0` Low + `0` None)
  - `nvidia-devops` Volume 04 Chapter 3 (`03-gpu-sharing-telemetry-masterclass.md`):
    * Time-Slicing (`replicas: 4`), MPS (`20%` thread limit, `10 GB / 40 GB` Ghost OOM),
      MIG (`3g.40gb, 2g.20gb, 1g.10gb`, up to `7` instances, `0 MiB` memory trap), and vGPU.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


DCGM_EXPORTER_DEFAULT_PORT: int = 9400
DCGM_STANDALONE_DEFAULT_PORT: int = 5555
DCGM_EXPORTER_DEFAULT_INTERVAL_MS: int = 30_000
DCGM_XID_WINDOW_DEFAULT_MS: int = 300_000
DCGM_MIN_HOST_RAM_GB: int = 16
A100_80GB_NAMEPLATE_MIB: int = 81_920
MAX_MIG_INSTANCES_PER_GPU: int = 7


@dataclass(frozen=True)
class XidSpec:
    """Authoritative Xid code specification from nvidia-devops Volume 20 Chapter 2 & Volume 04 Ch 3."""

    code: int
    name: str
    tier: str
    recoverable: str
    immediate_action: str


XID_ENCYCLOPEDIA: Dict[int, XidSpec] = {
    13: XidSpec(13, "Graphics Engine Exception", "Tier 2", "Usually yes (process-level)", "Debug kernel out-of-bounds / illegal instruction; escalate if recurring across unrelated apps"),
    31: XidSpec(31, "GPU Memory Page Fault", "Tier 2", "Usually yes (process-level)", "Terminate offending pod & run compute-sanitizer; escalate if recurring across unrelated apps"),
    32: XidSpec(32, "Invalid or Corrupted Push Buffer Stream", "Tier 2", "Usually yes", "Restart process; check PCIe errors if recurring"),
    43: XidSpec(43, "GPU Stopped Processing", "Tier 2", "Depends on root cause", "Catalog immediate=IGNORE, investigatory=CONTACT_SUPPORT; inspect preceding Xid & PCIe AER"),
    45: XidSpec(45, "Preemptive Cleanup Due to Previous Errors", "Tier 1", "Yes (symptom, not root cause)", "Inspect preceding Xid in dmesg / journalctl -k"),
    48: XidSpec(48, "Double Bit ECC Error (Uncorrectable)", "Tier 3", "No", "Cordon & drain immediately; flag active job outputs as corrupted; run dcgmi diag -r 3"),
    61: XidSpec(61, "Internal Micro-Controller Breakpoint/Warning", "Tier 3", "No", "Cordon & drain immediately; escalate firmware/hardware fault"),
    62: XidSpec(62, "Internal Micro-Controller Halt (PMU Halt)", "Tier 3", "No", "Catalog immediate=RESET_GPU, investigatory=CONTACT_SUPPORT; drain & RMA if recurring"),
    63: XidSpec(63, "ECC Page Retirement or Row Remapping Recording Event", "Tier 1", "Yes (self-healing)", "Catalog immediate=IGNORE; log and track 7d rate trend"),
    64: XidSpec(64, "ECC Page Retirement or Row Remapping Failure", "Tier 3", "No", "Self-healing row remapper failed; cordon & drain immediately and RMA"),
    74: XidSpec(74, "NVLink Error", "Fabric", "Depends on link state", "Check nvidia-smi topo -m (PIX fallback) and dcgmi nvlink -e CRC/replay counters"),
    79: XidSpec(79, "GPU Has Fallen Off the Bus", "Tier 3", "No (without intervention)", "Confirm missing in lspci; attempt PCIe remove/rescan + dcgmi diag -r 3 or RMA"),
    92: XidSpec(92, "High Single-Bit ECC Error Rate", "Tier 1", "Yes for now (precursor warning)", "Track 7d SBE rate trend & thermal correlation; schedule preventive maintenance if accelerating"),
    94: XidSpec(94, "Contained ECC Error", "Tier 2", "Partly (app-contained)", "Restart affected application; other apps unaffected; reset GPU when convenient"),
    95: XidSpec(95, "Uncontained ECC Error", "Tier 3", "No", "Cordon & drain immediately; treat running job outputs as compromised (same tier as Xid 48)"),
}


def triage_xid_event(
    xid_code: int,
    recurs_across_unrelated_apps: bool = False,
    prior_week_count: int = 1,
    current_week_count: int = 1,
) -> Dict[str, object]:
    """Classify an Xid event into operational action (V20 Ch 2)."""
    if xid_code not in XID_ENCYCLOPEDIA:
        raise ValueError(f"Unknown Xid code: {xid_code}")
    if prior_week_count < 0 or current_week_count < 0:
        raise ValueError("Counts must be non-negative")

    spec = XID_ENCYCLOPEDIA[xid_code]
    effective_tier = spec.tier
    if spec.tier == "Tier 2" and recurs_across_unrelated_apps:
        effective_tier = "Tier 3"

    wow_growth_pct = (
        round((current_week_count - prior_week_count) / prior_week_count * 100.0, 1)
        if prior_week_count > 0
        else 0.0
    )
    preventive_escalation = (
        spec.tier == "Tier 1"
        and prior_week_count > 0
        and (current_week_count / prior_week_count) > 3.0
    )

    return {
        "code": xid_code,
        "name": spec.name,
        "base_tier": spec.tier,
        "effective_tier": effective_tier,
        "drain_immediately": effective_tier == "Tier 3",
        "page_oncall_immediately": effective_tier == "Tier 3",
        "wow_growth_pct": wow_growth_pct,
        "preventive_maintenance_escalation": preventive_escalation,
        "immediate_action": spec.immediate_action,
    }


@dataclass(frozen=True)
class RowRemapperHealth:
    """Ampere/Hopper/Blackwell HBM Row Remapper status (`nvidia-smi -q -d ROW_REMAPPER`, V20 Ch 5)."""

    correctable_remapped_rows: int
    uncorrectable_remapped_rows: int
    pending: bool
    remapping_failure_occurred: bool
    bank_max: int
    bank_high: int
    bank_partial: int
    bank_low: int
    bank_none: int
    total_banks: int
    exhausted_or_failed: bool
    recommended_tier: str


def evaluate_row_remapper(
    correctable_rows: int = 12,
    uncorrectable_rows: int = 0,
    pending: bool = False,
    remapping_failure_occurred: bool = False,
    bank_max: int = 630,
    bank_high: int = 8,
    bank_partial: int = 2,
    bank_low: int = 0,
    bank_none: int = 0,
) -> RowRemapperHealth:
    """Evaluate `nvidia-smi -q -d ROW_REMAPPER` counters and bank availability histogram (V20 Ch 5)."""
    if any(x < 0 for x in (correctable_rows, uncorrectable_rows, bank_max, bank_high, bank_partial, bank_low, bank_none)):
        raise ValueError("Row remapper counts and bank buckets must be non-negative")

    total_banks = bank_max + bank_high + bank_partial + bank_low + bank_none
    exhausted = remapping_failure_occurred or (bank_none > 0)
    tier = "Tier 3 (Xid 64 - Drain & RMA)" if exhausted else "Tier 1 (Healthy Self-Healing)"
    return RowRemapperHealth(
        correctable_remapped_rows=correctable_rows,
        uncorrectable_remapped_rows=uncorrectable_rows,
        pending=pending,
        remapping_failure_occurred=remapping_failure_occurred,
        bank_max=bank_max,
        bank_high=bank_high,
        bank_partial=bank_partial,
        bank_low=bank_low,
        bank_none=bank_none,
        total_banks=total_banks,
        exhausted_or_failed=exhausted,
        recommended_tier=tier,
    )


@dataclass(frozen=True)
class EccTrendDiagnosis:
    """ECC SBE/DBE rate trend and thermal correlation diagnosis (V20 Ch 5)."""

    volatile_device_mem_sbe: int
    volatile_l2_sbe: int
    volatile_total_sbe: int
    aggregate_total_sbe: int
    aggregate_total_dbe: int
    week1_sbe_delta: int
    week4_sbe_delta: int
    monthly_delta_growth_pct: float
    monthly_delta_ratio: float
    temp_sbe_correlation: float
    diagnosis: str


def diagnose_ecc_trend(
    volatile_device_mem_sbe: int = 42,
    volatile_l2_sbe: int = 3,
    aggregate_total_sbe: int = 891,
    aggregate_total_dbe: int = 0,
    week1_sbe_delta: int = 3,
    week4_sbe_delta: int = 8,
    temp_sbe_correlation: float = 0.81,
) -> EccTrendDiagnosis:
    """Diagnose ECC counters and thermal correlation (`> 0.7` thermal vs silicon degradation, V20 Ch 5)."""
    if volatile_device_mem_sbe < 0 or volatile_l2_sbe < 0 or aggregate_total_sbe < 0 or aggregate_total_dbe < 0:
        raise ValueError("ECC counts must be non-negative")
    if week1_sbe_delta <= 0 or week4_sbe_delta < 0:
        raise ValueError("week1_sbe_delta must be > 0 and week4_sbe_delta >= 0")

    vol_total = volatile_device_mem_sbe + volatile_l2_sbe
    growth_pct = round((week4_sbe_delta - week1_sbe_delta) / week1_sbe_delta * 100.0, 0)
    ratio = round(week4_sbe_delta / week1_sbe_delta, 1)

    if aggregate_total_dbe > 0:
        diag = "UNCORRECTABLE_DBE_TIER3_DRAIN"
    elif growth_pct > 100.0 and temp_sbe_correlation >= 0.7:
        diag = "THERMAL_DRIVEN_SBE_FIX_COOLING_FIRST"
    elif growth_pct > 100.0 and temp_sbe_correlation < 0.7:
        diag = "PROGRESSIVE_SILICON_DEGRADATION_PREVENTIVE_RMA"
    else:
        diag = "NORMAL_ECC_BACKGROUND"

    return EccTrendDiagnosis(
        volatile_device_mem_sbe=volatile_device_mem_sbe,
        volatile_l2_sbe=volatile_l2_sbe,
        volatile_total_sbe=vol_total,
        aggregate_total_sbe=aggregate_total_sbe,
        aggregate_total_dbe=aggregate_total_dbe,
        week1_sbe_delta=week1_sbe_delta,
        week4_sbe_delta=week4_sbe_delta,
        monthly_delta_growth_pct=growth_pct,
        monthly_delta_ratio=ratio,
        temp_sbe_correlation=temp_sbe_correlation,
        diagnosis=diag,
    )


@dataclass(frozen=True)
class ClusterSloBudget:
    """GPU cluster availability SLO and monthly error budget calculation (V16 Ch 9)."""

    availability_slo_pct: float
    month_hours: float
    error_budget_hours: float
    downtime_used_hours: float
    remaining_budget_hours: float
    healthy_gpus_slo_pct: float
    job_completion_slo_pct: float
    freeze_deployments: bool


def evaluate_cluster_slo_budget(
    availability_slo_pct: float = 99.0,
    month_hours: float = 730.0,
    downtime_events_hours: Tuple[float, ...] = (1.5, 2.0, 2.0, 0.5),
    healthy_gpus_slo_pct: float = 98.0,
    job_completion_slo_pct: float = 99.5,
) -> ClusterSloBudget:
    """Compute monthly error budget (`(1 - SLO) * 730 hours = 7.3 hours` at `99.0%`, V16 Ch 9)."""
    if not (0.0 < availability_slo_pct < 100.0) or month_hours <= 0:
        raise ValueError("availability_slo_pct must be in (0, 100) and month_hours > 0")

    budget = round((1.0 - availability_slo_pct / 100.0) * month_hours, 2)
    used = round(sum(downtime_events_hours), 2)
    rem = round(budget - used, 2)
    # Freeze deployments when remaining budget is exhausted or < 20% of budget
    freeze = rem <= (0.2 * budget)
    return ClusterSloBudget(
        availability_slo_pct=availability_slo_pct,
        month_hours=month_hours,
        error_budget_hours=budget,
        downtime_used_hours=used,
        remaining_budget_hours=rem,
        healthy_gpus_slo_pct=healthy_gpus_slo_pct,
        job_completion_slo_pct=job_completion_slo_pct,
        freeze_deployments=freeze,
    )
