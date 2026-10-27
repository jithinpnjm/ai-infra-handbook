"""Chapter 1.28 model: sysfs cpulist range parser (/sys/devices/system/node/nodeN/cpulist),
3-tier GPU-to-NUMA node resolution fallback chain (NVML -> sysfs -> CLI/default),
node_audit.sh pass/fail evaluator, and synchronous distributed training straggler
step-time impact.

Sources modeled:
- Chris Fregly, AI Systems Performance Engineering (ai-systems-performance-engineering),
  Chapter 3 ("OS, Docker, and Kubernetes Tuning for GPU-Based Environments":
  get_gpu_numa_node fallback chain, cpulist parsing, DataLoader worker_init_fn,
  pinned memory 2x-3x H2D speedup, persistence mode, clock locking).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 16 ("Case Study: An Unexplained Win": 48-CPU VM load 85, IPC 0.57,
  LLC hit ratio 30%, 2M cs/s vs 64-CPU container host load 18, IPC 1.52, LLC 90%,
  1,000 cs/s).
- nvidia-devops/volume-10/03-os-provisioning-and-linux-security-hardening.md.
"""
from typing import Dict, List, Optional


def parse_sysfs_cpulist(cpulist_str: str) -> List[int]:
    """Parse a sysfs cpulist string such as '0-3,8,12-15' into a sorted list of integer CPU IDs."""
    cpus: List[int] = []
    clean = cpulist_str.strip()
    if not clean:
        return cpus
    for part in clean.split(","):
        part = part.strip()
        if "-" in part:
            a_str, b_str = part.split("-", 1)
            cpus.extend(range(int(a_str), int(b_str) + 1))
        else:
            cpus.append(int(part))
    return cpus


def resolve_gpu_numa_node(
    nvml_numa_id: Optional[int],
    sysfs_numa_node: Optional[int],
    cli_topo_numa_id: Optional[int] = None,
) -> Dict[str, object]:
    """Resolve a GPU's home NUMA node following the 3-tier fallback chain (ASP Ch. 3, Section 7)."""
    if nvml_numa_id is not None and nvml_numa_id >= 0:
        return {"numa_node": nvml_numa_id, "source": "1_nvml"}
    if sysfs_numa_node is not None:
        return {"numa_node": sysfs_numa_node if sysfs_numa_node >= 0 else 0, "source": "2_sysfs"}
    if cli_topo_numa_id is not None and cli_topo_numa_id >= 0:
        return {"numa_node": cli_topo_numa_id, "source": "3_cli_topo"}
    return {"numa_node": 0, "source": "fallback_default_0"}


def evaluate_node_audit(
    cmdline_tokens: List[str],
    swappiness: int,
    max_map_count: int,
    numa_balancing: int,
    thp_mode: str,
    memlock_limit: str,
    governor: str,
    gpu_count: int,
    expected_gpus: int,
    persistence_enabled: bool,
    pcie_all_max: bool,
    uncorrected_ecc: int,
    fabric_manager_active: bool,
    recent_xid_count: int,
) -> Dict[str, object]:
    """Run the Section 11 node_audit.sh checks and return pass/fail status and failed check names."""
    failures: List[str] = []
    if "iommu=pt" not in cmdline_tokens:
        failures.append("missing_iommu_pt")
    if "numa_balancing=disable" not in cmdline_tokens:
        failures.append("missing_cmdline_numa_balancing_disable")
    if swappiness != 1:
        failures.append("swappiness_not_1")
    if max_map_count < 1048576:
        failures.append("max_map_count_below_1048576")
    if numa_balancing != 0:
        failures.append("sysctl_numa_balancing_not_0")
    if thp_mode != "madvise":
        failures.append("thp_not_madvise")
    if memlock_limit != "unlimited":
        failures.append("memlock_not_unlimited")
    if governor != "performance":
        failures.append("governor_not_performance")
    if gpu_count != expected_gpus:
        failures.append("gpu_count_mismatch")
    if not persistence_enabled:
        failures.append("persistence_mode_disabled")
    if not pcie_all_max:
        failures.append("pcie_link_downtrained")
    if uncorrected_ecc > 0:
        failures.append("uncorrected_ecc_errors")
    if not fabric_manager_active:
        failures.append("fabric_manager_inactive")
    if recent_xid_count > 0:
        failures.append("recent_xid_errors_in_journal")
    return {
        "passed": len(failures) == 0,
        "fail_count": len(failures),
        "failures": failures,
    }


def compute_synchronous_job_step_time(rank_step_times_ms: List[float]) -> Dict[str, float]:
    """Compute effective synchronous training step time (governed by the slowest straggler rank)."""
    if not rank_step_times_ms or any(t <= 0 for t in rank_step_times_ms):
        raise ValueError("rank_step_times_ms must be non-empty positive numbers")
    fastest = min(rank_step_times_ms)
    slowest = max(rank_step_times_ms)
    slowdown_pct = round(100.0 * (slowest - fastest) / fastest, 1)
    return {
        "ideal_step_ms": round(fastest, 2),
        "effective_job_step_ms": round(slowest, 2),
        "straggler_penalty_pct": slowdown_pct,
    }
