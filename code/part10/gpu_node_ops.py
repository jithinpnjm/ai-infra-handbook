#!/usr/bin/env python3
"""Chapter 10.8 model: Operating GPU Nodes: nvidia-smi, Topology, Clocks, and Throttling.

Encodes the verifiable operational mechanisms, throttle reason bitmasks,
PyTorch memory allocation vs caching allocator states, temperature headroom bands,
clock management policies, and node-level operational health diagnostics from:
- nvidia-devops Volume 16 Chapters 1-3:
  Why GPU observability is fundamentally different (Execution, Memory, Thermal/Power);
  The three deceptive metrics (The Utilization Lie, The Memory Lie, The Clock Speed Lie);
  Utilization vs memory bandwidth regimes (Compute-bound, Memory-bound, Spinning/Stalled);
  Temperature bands (<60C, 60-75C, 75-82C, 82-85C, >85C);
  Throttle reason decoding from NVML / nvidia-smi.
- nvidia-devops Volume 02 Labs 01-02:
  Durable device identity (UUID and PCI BDF);
  Persistence Mode (nvidia-smi -pm 1 vs driver teardown latency);
  Clock locking (nvidia-smi -lgc <min>,<max> vs -rgc);
  Power capping (nvidia-smi -pl <watts>);
  Real-time telemetry sampling with dmon and pmon.
- nvidia-devops Volume 20 Chapters 2, 6, 8, 9, 10 and Volume 19 Chapter 4 (added after review):
  Xid reference table and three tiers (Ch 2); thermal throttling, fan and cooling triage (Ch 6, 8);
  power limit and PSU triage (Ch 9); clock instability and the unique-clock stability test (Ch 10);
  SM_ACTIVE / TENSOR_ACTIVE decision for the utilization lie (V19 Ch 4).
  The V20 notes say their outputs are illustrative, so the numbers here are the notes' own examples, not specs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


class GPUOpsError(ValueError):
    """Raised when invalid operational metrics or configuration values are provided."""


# Bit values follow NVML's nvml.h as the author knows it. They are NOT in the corpus notes; verify with `nvidia-smi -q -d PERFORMANCE`.
THROTTLE_REASONS_MAP: Dict[int, str] = {
    0x0000000000000001: "GPU_IDLE",
    0x0000000000000002: "APPLICATIONS_CLOCKS_SETTING",
    0x0000000000000004: "SW_POWER_CAP",
    0x0000000000000008: "HW_SLOWDOWN",
    0x0000000000000010: "SYNC_BOOST",
    0x0000000000000020: "SW_THERMAL_SLOWDOWN",
    0x0000000000000040: "HW_THERMAL_SLOWDOWN",
    0x0000000000000080: "HW_POWER_BRAKE_SLOWDOWN",
    0x0000000000000100: "DISPLAY_CLOCK_SETTING",
}


def decode_throttle_reasons_bitmask(bitmask: int) -> List[str]:
    """Decode the 64-bit `clocks_throttle_reasons.active` integer from NVML / nvidia-smi.

    Returns a list of active throttle reason strings.
    If bitmask == 0, returns ["NOT_THROTTLED"].
    """
    if bitmask < 0:
        raise GPUOpsError("Throttle bitmask cannot be negative")
    if bitmask == 0:
        return ["NOT_THROTTLED"]

    reasons: List[str] = []
    for mask, name in THROTTLE_REASONS_MAP.items():
        if (bitmask & mask) == mask:
            reasons.append(name)

    if not reasons:
        reasons.append(f"UNKNOWN_THROTTLE_REASON_0x{bitmask:X}")
    return reasons


def evaluate_utilization_regime(
    sm_util_pct: float,
    mem_bw_util_pct: float,
    samples_per_sec: Optional[float] = None,
) -> Dict[str, object]:
    """Evaluate whether high GPU utilization reflects real work or data starvation / spinning.

    Source: V16 Ch 1 ("The Core Problem") & V16 Ch 3 ("Metric 1: GPU Utilization"):
    - SM Util ~85% + Mem BW Util ~80% = MEMORY_BOUND (healthy memory-bound kernel).
    - SM Util ~85% + Mem BW Util ~15-20% (with high samples/sec) = COMPUTE_BOUND.
    - SM Util ~85% + Mem BW Util < 5% (with ~0 samples/sec) = SPINNING_OR_SYNCHRONIZING (critical bug).
    """
    if not (0.0 <= sm_util_pct <= 100.0) or not (0.0 <= mem_bw_util_pct <= 100.0):
        raise GPUOpsError("Utilization percentages must be in range [0.0, 100.0]")
    if samples_per_sec is not None and samples_per_sec < 0.0:
        raise GPUOpsError("samples_per_sec cannot be negative")

    if sm_util_pct < 10.0:
        regime = "IDLE"
        assessment = "GPU is largely idle with no queued computational kernels."
    elif sm_util_pct >= 60.0 and mem_bw_util_pct < 5.0 and (samples_per_sec is None or samples_per_sec < 10.0):
        regime = "SPINNING_OR_STALLED"
        assessment = "CRITICAL: GPU reports high SM activity but negligible memory traffic; kernel is spinning, busy-waiting, or deadlocked at a barrier."
    elif mem_bw_util_pct >= 50.0:
        regime = "MEMORY_BOUND"
        assessment = "Normal memory-bound execution: SMs are frequently waiting on data fetches from HBM/DRAM."
    else:
        regime = "COMPUTE_BOUND"
        assessment = "Healthy compute-bound execution: arithmetic pipelines are saturated with adequate data reuse."

    return {
        "sm_util_pct": sm_util_pct,
        "mem_bw_util_pct": mem_bw_util_pct,
        "samples_per_sec": samples_per_sec,
        "regime": regime,
        "assessment": assessment,
    }


def analyze_pytorch_memory_state(
    total_vram_gb: float,
    allocated_gb: float,
    reserved_gb: float,
) -> Dict[str, object]:
    """Analyze PyTorch VRAM state to distinguish healthy reservation from real memory pressure.

    Source: V16 Ch 3 ("The Memory Lie" & "How to detect memory fragmentation"):
    - `allocated_gb` = tensor memory actively requested by the program.
    - `reserved_gb` = pool of memory held by PyTorch caching allocator from the CUDA driver.
    - `free_gb` = memory untouched by PyTorch (`total_vram_gb - reserved_gb`).
    - `reusable_pool_gb` = cached memory available for immediate reuse (`reserved_gb - allocated_gb`).
    """
    if total_vram_gb <= 0.0:
        raise GPUOpsError("total_vram_gb must be positive")
    if allocated_gb < 0.0 or reserved_gb < 0.0:
        raise GPUOpsError("allocated_gb and reserved_gb cannot be negative")
    if allocated_gb > reserved_gb:
        raise GPUOpsError("allocated_gb cannot exceed reserved_gb")
    if reserved_gb > total_vram_gb:
        raise GPUOpsError("reserved_gb cannot exceed total_vram_gb")

    free_gb = total_vram_gb - reserved_gb
    reusable_pool_gb = reserved_gb - allocated_gb
    true_available_gb = free_gb + reusable_pool_gb

    # Allocation ratios
    reserved_ratio = reserved_gb / total_vram_gb
    active_usage_ratio = allocated_gb / reserved_gb if reserved_gb > 0 else 0.0
    fragmentation_risk_pct = (reusable_pool_gb / total_vram_gb) * 100.0

    is_oom_imminent = (total_vram_gb - allocated_gb) < 1.0  # < 1 GB total headroom

    return {
        "total_vram_gb": round(total_vram_gb, 2),
        "allocated_gb": round(allocated_gb, 2),
        "reserved_gb": round(reserved_gb, 2),
        "free_from_driver_gb": round(free_gb, 2),
        "reusable_cache_gb": round(reusable_pool_gb, 2),
        "true_available_gb": round(true_available_gb, 2),
        "reserved_fraction_pct": round(reserved_ratio * 100.0, 1),
        "active_usage_pct": round(active_usage_ratio * 100.0, 1),
        "is_oom_imminent": is_oom_imminent,
    }


def classify_temperature_headroom(temp_celsius: float) -> Dict[str, object]:
    """Classify GPU core temperature into operational headroom bands per V16 Ch 3.

    Bands:
    - < 60C: HEALTHY (ample headroom, low thermal stress)
    - 60-75C: NORMAL (standard full-load operating envelope)
    - 75-82C: CAUTION (thermal headroom shrinking, monitor airflow)
    - 83-85C: THROTTLE_THRESHOLD (approaching target thermal limit)
    - > 85C: CRITICAL_THROTTLING (hardware thermal throttling active or imminent)
    """
    if temp_celsius < 0.0:
        raise GPUOpsError("Temperature cannot be negative in standard data center environments")

    if temp_celsius < 60.0:
        band = "HEALTHY"
        action = "Ample thermal headroom; no intervention required."
        headroom = round(85.0 - temp_celsius, 1)
    elif temp_celsius <= 75.0:
        band = "NORMAL"
        action = "Standard full-utilization operating envelope; cooling is adequate."
        headroom = round(85.0 - temp_celsius, 1)
    elif temp_celsius <= 82.0:
        band = "CAUTION"
        action = "Elevated temperature; verify fan speed and hot/cold aisle containment."
        headroom = round(85.0 - temp_celsius, 1)
    elif temp_celsius <= 85.0:
        band = "THROTTLE_THRESHOLD"
        action = "ALERT: GPU is at throttle boundary; thermal clock reduction likely imminent."
        headroom = round(85.0 - temp_celsius, 1)
    else:
        band = "CRITICAL_THROTTLING"
        action = "CRITICAL: Temperature exceeds 85C; clocks are actively throttled; inspect cooling immediately."
        headroom = 0.0

    return {
        "temp_celsius": temp_celsius,
        "band": band,
        "headroom_to_limit_c": headroom,
        "action": action,
    }


def audit_gpu_node_operational_health(
    persistence_mode_enabled: bool,
    temp_celsius: float,
    throttle_bitmask: int,
    power_draw_watts: float,
    power_limit_watts: float,
    current_sm_clock_mhz: float,
    max_sm_clock_mhz: float,
    ecc_uncorrected_volatile: int = 0,
    locked_clocks_range: Optional[tuple[float, float]] = None,
) -> Dict[str, object]:
    """Comprehensive operational health audit for an NVIDIA GPU node.

    Evaluates:
    - Persistence mode (must be True to prevent a driver re-initialization delay at job start).
    - Thermal headroom and throttle reasons.
    - Power draw relative to power limit.
    - Clock frequencies relative to maximum or locked range.
    - Volatile uncorrected ECC memory errors.
    """
    if power_draw_watts < 0.0 or power_limit_watts <= 0.0:
        raise GPUOpsError("Power values must be non-negative and limit must be positive")
    if current_sm_clock_mhz < 0.0 or max_sm_clock_mhz <= 0.0:
        raise GPUOpsError("Clock frequencies must be non-negative and max must be positive")
    if ecc_uncorrected_volatile < 0:
        raise GPUOpsError("ECC error count cannot be negative")

    issues: List[str] = []

    # 1. Persistence Mode Check
    if not persistence_mode_enabled:
        issues.append(
            "Persistence Mode is DISABLED: driver will tear down when no CUDA processes are active, adding a start-up delay per job launch."
        )

    # 2. Temperature Check
    temp_eval = classify_temperature_headroom(temp_celsius)
    if temp_eval["band"] in {"THROTTLE_THRESHOLD", "CRITICAL_THROTTLING"}:
        issues.append(f"Thermal degradation ({temp_celsius}C, band {temp_eval['band']}): {temp_eval['action']}")

    # 3. Throttle Reason Bitmask Check
    throttle_reasons = decode_throttle_reasons_bitmask(throttle_bitmask)
    severe_reasons = {"HW_SLOWDOWN", "SW_THERMAL_SLOWDOWN", "HW_THERMAL_SLOWDOWN", "HW_POWER_BRAKE_SLOWDOWN"}
    found_severe = severe_reasons.intersection(throttle_reasons)
    if found_severe:
        issues.append(f"Active severe hardware/thermal throttling reasons: {sorted(list(found_severe))}")

    # 4. Power Capping Check
    if "SW_POWER_CAP" in throttle_reasons and power_draw_watts >= (power_limit_watts * 0.98):
        issues.append(
            f"Power capping active: drawing {power_draw_watts}W at {power_limit_watts}W ceiling; SM clocks are being reduced."
        )

    # 5. Clock Frequency Audit
    if locked_clocks_range:
        min_lock, max_lock = locked_clocks_range
        if not (min_lock <= current_sm_clock_mhz <= max_lock):
            issues.append(
                f"SM clock {current_sm_clock_mhz} MHz is outside configured locked range [{min_lock}, {max_lock}] MHz."
            )
    else:
        # If active workload and clocks < 50% max without IDLE reason
        if current_sm_clock_mhz < (max_sm_clock_mhz * 0.5) and "GPU_IDLE" not in throttle_reasons:
            issues.append(
                f"Clock frequency severely depressed ({current_sm_clock_mhz} MHz < 50% of {max_sm_clock_mhz} MHz) without GPU_IDLE state."
            )

    # 6. ECC Errors Check
    if ecc_uncorrected_volatile > 0:
        issues.append(
            f"CRITICAL: {ecc_uncorrected_volatile} uncorrected volatile ECC memory errors detected; node must be cordoned."
        )

    return {
        "healthy": len(issues) == 0,
        "persistence_mode": persistence_mode_enabled,
        "temperature_c": temp_celsius,
        "temperature_band": temp_eval["band"],
        "throttle_reasons": throttle_reasons,
        "power_draw_watts": power_draw_watts,
        "power_limit_watts": power_limit_watts,
        "sm_clock_mhz": current_sm_clock_mhz,
        "max_sm_clock_mhz": max_sm_clock_mhz,
        "ecc_uncorrected": ecc_uncorrected_volatile,
        "issues": issues,
    }


# --- Added after review: Volume 20 / Volume 19 field-triage rules -------------------------------------------

# Volume 20 Chapter 2 Xid reference table: code -> (meaning, tier). Tier 0 means "depends, see the NVLink chapter".
XID_TABLE: Dict[int, tuple] = {
    13: ("Graphics Engine Exception", 2),
    31: ("GPU memory page fault", 2),
    32: ("Invalid or corrupted push buffer stream", 2),
    43: ("GPU stopped processing", 2),
    45: ("Preemptive cleanup, due to previous errors", 1),
    48: ("Double Bit ECC Error (uncorrectable)", 3),
    61: ("Internal micro-controller breakpoint/warning", 3),
    62: ("Internal micro-controller halt", 3),
    63: ("ECC page retirement or row remapping recording event", 1),
    64: ("ECC page retirement or row remapping failure", 3),
    74: ("NVLink Error", 0),
    79: ("GPU has fallen off the bus", 3),
    92: ("High single-bit ECC error rate", 1),
    94: ("Contained ECC error", 2),
    95: ("Uncontained ECC error", 3),
}


def classify_xid(code: int, recurs_on_same_gpu_across_unrelated_apps: bool = False) -> Dict[str, object]:
    """Classify an Xid code with the three-tier rule from Volume 20 Chapter 2."""
    if code not in XID_TABLE:
        return {"code": code, "tier": None, "action": "Unknown code: look it up in NVIDIA's Xid documentation; do not pattern-match the text."}
    meaning, tier = XID_TABLE[code]
    if tier == 2 and recurs_on_same_gpu_across_unrelated_apps:
        return {"code": code, "meaning": meaning, "tier": 3,
                "action": "Escalate to Tier 3 handling: same code on the same GPU across unrelated applications points to hardware."}
    actions = {
        0: "Depends on the cause: follow the NVLink diagnostic path.",
        1: "Informational / self-healing: log it and track the rate; look at what came just before it.",
        2: "Process-level: restart the affected application; escalate only if it recurs across unrelated apps.",
        3: "GPU-level failure: stop scheduling new work on this GPU now, drain, run diagnostics before returning it to service.",
    }
    return {"code": code, "meaning": meaning, "tier": tier, "action": actions[tier]}


def triage_slowdown(
    throttle_bitmask: int,
    temp_celsius: float,
    power_limit_watts: float,
    default_power_limit_watts: float,
    clock_below_max: bool,
) -> Dict[str, object]:
    """Pick the most likely cause of a slow-but-busy GPU (Volume 20 Ch 6, 9, 10; Volume 19 Ch 4).

    Order follows the notes: read the throttle reasons first, then temperature, then power limit, then workload."""
    reasons = decode_throttle_reasons_bitmask(throttle_bitmask)
    notes: List[str] = []
    if power_limit_watts < default_power_limit_watts:
        notes.append(f"Power limit {power_limit_watts}W is below the default {default_power_limit_watts}W: find out who set it.")
    if {"SW_THERMAL_SLOWDOWN", "HW_THERMAL_SLOWDOWN"} & set(reasons):
        cause = "thermal"
    elif "HW_SLOWDOWN" in reasons:
        cause = "hardware_slowdown_thermal_or_power"  # Volume 20 Ch 10 flowchart: HW_SLOWDOWN = thermal or power limit hit
    elif "HW_POWER_BRAKE_SLOWDOWN" in reasons:
        cause = "power_brake"
    elif "SW_POWER_CAP" in reasons:
        cause = "power_cap"
    elif "APPLICATIONS_CLOCKS_SETTING" in reasons:
        cause = "clock_lock_set_by_operator"
        notes.append("Check for a leftover `nvidia-smi -lgc`; clear it with `nvidia-smi -rgc`.")
    elif clock_below_max and temp_celsius < 80.0:
        cause = "workload_or_dvfs"
        notes.append("No throttle reason and a cool GPU: look for idle gaps in the workload (Nsight Systems); lock the clock only if a stable clock is required.")
    else:
        cause = "not_a_clock_problem"
    return {"cause": cause, "reasons": reasons, "notes": notes}


def classify_clock_stability(unique_clock_values: int) -> str:
    """Volume 20 Ch 10 test: count unique clock values over a 5-minute run.
    1 (or 2-3 within about 50 MHz) is stable; more than 5 means oscillation is still present."""
    if unique_clock_values < 1:
        raise GPUOpsError("unique_clock_values must be >= 1")
    if unique_clock_values <= 3:
        return "STABLE"
    if unique_clock_values <= 5:
        return "BORDERLINE"
    return "OSCILLATING"


def minimum_psu_watts(gpu_count: int, per_gpu_watts: float, overhead_fraction: float = 0.30) -> float:
    """Volume 20 Ch 9 planning rule: gpu_count * per_gpu_watts * (1 + overhead). Example: 4 x 300 x 1.3 = 1,560 W."""
    if gpu_count <= 0 or per_gpu_watts <= 0 or overhead_fraction < 0:
        raise GPUOpsError("gpu_count and per_gpu_watts must be positive and overhead non-negative")
    return round(gpu_count * per_gpu_watts * (1.0 + overhead_fraction), 2)


def diagnose_busy_but_slow(tensor_active_pct: float, throttle_hw_slowdown: bool) -> str:
    """Volume 19 Ch 4 decision flow for a GPU that nvidia-smi shows at 100% but the job is slow."""
    if not 0.0 <= tensor_active_pct <= 100.0:
        raise GPUOpsError("tensor_active_pct must be within [0, 100]")
    if throttle_hw_slowdown:
        return "HARDWARE_THERMAL_OR_POWER_LIMIT"
    if tensor_active_pct > 50.0:
        return "GPU_HEALTHY_CHECK_NETWORK_OR_DATALOADER"
    if tensor_active_pct < 10.0:
        return "SOFTWARE_ISSUE_GPU_BUSY_ON_OVERHEAD"
    return "INCONCLUSIVE_BETWEEN_10_AND_50_PERCENT"
