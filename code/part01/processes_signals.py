"""Chapter 1.8 model: Process states (R, S, D, T, Z), load average interpretation
(runnable + D state vs CPU core count), signal dispositions and PID 1 namespace
semantics, time real vs user+sys classification, and cgroup v2 cpu.max / memory.max.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 8
  ("Process and Resource Utilization": top, lsof, strace/ltrace, threads ps m,
  time, nice/renice, load averages, minor vs major page faults, vmstat, iostat,
  iotop, pidstat, cgroups v1 vs v2).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 7 (process
  states R/S/D/T/Z, load average, signals, kill/pkill, nice/renice, ionice) and
  Chapter 12 (ulimit and /etc/security/limits.conf).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 3 ("Operating Systems": mode switch vs context switch, vDSO, KPTI/PCID,
  stacks leaf-to-root, VFS, PGO/LTO/AutoFDO, unikernels/microkernels/hybrid).
"""
from typing import Dict, List


UNCATCHABLE_SIGNALS = {9: "SIGKILL", 19: "SIGSTOP"}


def evaluate_signal_delivery(
    sig_num: int,
    state: str,
    is_container_pid1: bool = False,
    has_custom_handler: bool = False,
) -> Dict[str, object]:
    """Model how the Linux kernel delivers a signal given process state and PID 1 rules."""
    if state == "Z":
        return {"delivered_immediately": False, "outcome": "ignored_already_dead_zombie"}
    if state == "D":
        return {"delivered_immediately": False, "outcome": "deferred_until_kernel_io_completes"}
    if sig_num == 9:
        return {"delivered_immediately": True, "outcome": "terminated_immediately_137"}
    if sig_num == 19:
        return {"delivered_immediately": True, "outcome": "stopped_T"}
    if is_container_pid1 and not has_custom_handler:
        return {"delivered_immediately": True, "outcome": "ignored_by_pid1_default_protection"}
    if has_custom_handler:
        return {"delivered_immediately": True, "outcome": "handler_invoked"}
    return {"delivered_immediately": True, "outcome": f"default_action_sig_{sig_num}"}


def diagnose_load_and_vmstat(
    load_1m: float,
    num_cpus: int,
    vmstat_r: int,
    vmstat_b: int,
    cpu_idle_pct: int,
    vmstat_so: int,
) -> str:
    """Classify node bottleneck from load average and vmstat columns (r, b, so, id)."""
    if vmstat_so > 0:
        return "memory_swapping_thrashing"
    if load_1m > num_cpus and vmstat_b > 0 and cpu_idle_pct > 70:
        return "uninterruptible_io_wait_D_state"
    if vmstat_r > num_cpus and cpu_idle_pct < 20:
        return "cpu_saturation_runqueue_backlog"
    return "healthy_under_capacity"


def classify_time_profile(real_sec: float, user_sec: float, sys_sec: float) -> str:
    """Classify a command's time output into multithreaded_cpu, single_cpu, kernel_heavy, or io_or_lock_wait."""
    cpu_total = user_sec + sys_sec
    if cpu_total > real_sec * 1.3:
        return "multithreaded_parallel_cpu"
    if cpu_total < real_sec * 0.5:
        return "io_network_or_lock_wait"
    if sys_sec > user_sec:
        return "kernel_syscall_heavy"
    return "single_thread_cpu_bound"


def evaluate_cgroup_v2_cpu_max(quota_usec: int, period_usec: int) -> float:
    """Compute effective CPU core ceiling for a cgroup v2 cpu.max 'quota period' pair."""
    if quota_usec <= 0 or period_usec <= 0:
        raise ValueError("quota_usec and period_usec must be positive")
    return round(quota_usec / period_usec, 3)


def check_cgroup_v2_leaf_rule(has_child_cgroups: bool, is_root_cgroup: bool = False) -> bool:
    """Under cgroup v2 'no internal process constraint', non-root cgroups with children cannot hold processes."""
    if is_root_cgroup:
        return True
    return not has_child_cgroups
