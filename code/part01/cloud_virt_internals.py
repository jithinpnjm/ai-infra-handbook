"""Chapter 1.27 model: Container CPU throttling decision tree (5 inputs from SP
Ch. 11.3.4), CPU shares burst-to-minimum 'bait-and-switch' drop calculation,
NSpid host-to-container PID translation, and cloud GPU training total cost and
goodput-adjusted cost modeling.

Sources modeled:
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 11 ("Cloud Computing": instance types, capacity planning, storage,
  multitenancy, hardware vs OS vs lightweight virtualization, CPU shares vs
  bandwidth, 5-fact container CPU throttling decision rule, NSpid mapping,
  in-container tool visibility matrix).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 17.
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 17 ("Clouds":
  5-15% HPC VM performance drop vs bare metal, single performance subnet/domain
  placement, 5-minute checkpoint simulation test).
"""
from typing import Dict, List


def diagnose_container_cpu_limit_cause(
    throttled_time_increasing: bool,
    involuntary_ctxt_switches_increasing: bool,
    host_has_idle_cpus: bool,
    cpuset_cpus_100pct_busy: bool,
    other_tenants_idle: bool,
) -> str:
    """Apply Gregg's 5-fact decision rule (SP Ch. 11.3.4, Section 5) for container CPU limiting."""
    if throttled_time_increasing:
        return "cfs_bandwidth_quota_cap_binding"
    if cpuset_cpus_100pct_busy and host_has_idle_cpus:
        return "cpuset_cores_saturated"
    if involuntary_ctxt_switches_increasing and not other_tenants_idle and not host_has_idle_cpus:
        return "cpu_shares_contention_with_busy_neighbors"
    if other_tenants_idle and host_has_idle_cpus:
        return "no_cpu_limit_binding"
    return "mixed_or_external_wait"


def compute_shares_burst_vs_contended_drop(
    container_shares: int,
    sibling_busy_shares: List[int],
) -> Dict[str, float]:
    """Compute CPU % on an idle host (100% burst) vs when siblings are busy, and the slowdown factor."""
    if container_shares <= 0 or any(s < 0 for s in sibling_busy_shares):
        raise ValueError("Shares must be positive")
    idle_host_pct = 100.0
    total_active_shares = container_shares + sum(sibling_busy_shares)
    contended_pct = round(100.0 * container_shares / float(total_active_shares), 2)
    slowdown_factor = round(idle_host_pct / contended_pct, 2)
    return {
        "idle_host_burst_pct": idle_host_pct,
        "contended_share_pct": contended_pct,
        "slowdown_factor_x": slowdown_factor,
    }


def parse_proc_status_nspid(nspid_line: str) -> Dict[str, object]:
    """Parse '/proc/<hostpid>/status' line 'NSpid:\\t4915\\t753' into host_pid and innermost container_pid."""
    parts = nspid_line.replace("NSpid:", "").strip().split()
    if not parts:
        raise ValueError(f"Empty NSpid line: {nspid_line}")
    pids = [int(p) for p in parts]
    return {
        "host_pid": pids[0],
        "container_pid": pids[-1],
        "nesting_depth": len(pids) - 1,
    }


def compute_cloud_gpu_effective_cost(
    num_gpus: int,
    useful_gpu_hours_needed: float,
    price_per_gpu_hour: float,
    goodput_fraction: float,
    storage_and_egress_usd: float = 0.0,
) -> Dict[str, float]:
    """Compute wall-clock hours and total USD cost for a cloud training run given goodput_fraction in (0, 1]."""
    if num_gpus <= 0 or useful_gpu_hours_needed <= 0 or price_per_gpu_hour < 0 or not (0.0 < goodput_fraction <= 1.0):
        raise ValueError("Invalid cloud cost parameters")
    paid_gpu_hours = useful_gpu_hours_needed / goodput_fraction
    wall_hours = paid_gpu_hours / float(num_gpus)
    compute_usd = paid_gpu_hours * price_per_gpu_hour
    total_usd = compute_usd + storage_and_egress_usd
    return {
        "paid_gpu_hours": round(paid_gpu_hours, 2),
        "wall_clock_hours": round(wall_hours, 2),
        "compute_cost_usd": round(compute_usd, 2),
        "total_cost_usd": round(total_usd, 2),
    }
