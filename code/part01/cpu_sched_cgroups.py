"""Chapter 1.18 model: Linux scheduler classes and CFS virtual runtime (vruntime),
IPC stall vs instruction-bound classification, cgroup v2 CPU weight proportional
shares, CFS bandwidth quota throttling (cpu.max $MAX $PERIOD across N threads),
and the cgroup v2 no-internal-processes rule.

Sources modeled:
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 6 ("CPUs": clock rate, IPC, SMT, user/kernel ratio, scheduler classes,
  CFS/EEVDF, mpstat/pidstat/perf/runqlat/turbostat/pmcarch, flame graphs) and
  Chapter 11 (cgroup v1/v2 CPU weight vs CFS bandwidth quota throttling).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 8
  (section 8.7 control groups cgroups v1 and v2).
- nvidia-devops/volume-01/01-linux-compute-memory-masterclass.md and
  04-linux-systemd-containers-masterclass.md.
"""
from typing import Dict, List


SCHED_CLASSES_HIGHEST_TO_LOWEST: List[str] = [
    "stop",
    "deadline",
    "realtime",
    "fair",
    "idle",
]


def classify_ipc_bottleneck(instructions: int, cycles: int) -> Dict[str, object]:
    """Compute IPC (instructions per cycle) and classify as memory_stall_bound or instruction_bound."""
    if instructions < 0 or cycles <= 0:
        raise ValueError("Invalid instruction or cycle count")
    ipc = round(instructions / float(cycles), 2)
    if ipc < 0.5:
        regime = "memory_stall_bound"
    elif ipc >= 1.0:
        regime = "instruction_execution_bound"
    else:
        regime = "mixed_regime"
    return {"ipc": ipc, "regime": regime}


def compute_cfs_vruntime_delta_ns(actual_runtime_ns: int, task_weight: int, nice_0_weight: int = 1024) -> int:
    """Compute CFS virtual runtime delta: actual_runtime_ns * (nice_0_weight / task_weight)."""
    if actual_runtime_ns < 0 or task_weight <= 0 or nice_0_weight <= 0:
        raise ValueError("Runtime and weights must be positive")
    return int(round(actual_runtime_ns * (nice_0_weight / float(task_weight))))


def compute_cpu_weight_shares_pct(weights: List[int]) -> List[float]:
    """Compute relative CPU share percentages under contention for sibling cgroups."""
    if not weights or any(w <= 0 for w in weights):
        raise ValueError("weights must be a non-empty list of positive integers")
    total = float(sum(weights))
    return [round(100.0 * w / total, 1) for w in weights]


def simulate_cfs_quota_period(
    quota_us: int,
    period_us: int,
    active_threads: int,
) -> Dict[str, float]:
    """Model how fast active_threads exhaust quota_us in a period_us window and how long they are throttled."""
    if quota_us <= 0 or period_us <= 0 or active_threads <= 0:
        raise ValueError("quota_us, period_us, and active_threads must be positive")
    effective_cores_cap = round(quota_us / float(period_us), 2)
    wall_time_to_exhaust_ms = round((quota_us / float(active_threads)) / 1000.0, 2)
    period_ms = round(period_us / 1000.0, 2)
    if wall_time_to_exhaust_ms < period_ms:
        throttled_wall_ms = round(period_ms - wall_time_to_exhaust_ms, 2)
        throttled = True
    else:
        throttled_wall_ms = 0.0
        throttled = False
    return {
        "effective_cores_cap": effective_cores_cap,
        "wall_active_ms": min(wall_time_to_exhaust_ms, period_ms),
        "wall_throttled_ms": throttled_wall_ms,
        "throttled": throttled,
    }


def check_cgroup_v2_no_internal_processes(
    is_root_cgroup: bool,
    num_direct_pids: int,
    subtree_controllers: List[str],
) -> Dict[str, object]:
    """Validate the cgroup v2 'no internal processes' rule when enabling subtree_control."""
    if is_root_cgroup or len(subtree_controllers) == 0:
        return {"valid": True, "error": None}
    if num_direct_pids > 0:
        return {"valid": False, "error": "EBUSY: non-root cgroup with subtree_control cannot hold processes"}
    return {"valid": True, "error": None}
