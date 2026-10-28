"""Chapter 5.26 model: Cgroup v2 CFS CPU throttling & `working_set` memory
calculator, GPU node `sysctl` & `protectKernelDefaults` auditor, and Linux
kernel version feature checker (`HLW` Ch. 17, `NK` Ch. 2–5, `PK` Ch. 3–5).

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition, HLW),
  Chapter 17 ("Virtualization").
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 2–5 ("Linux Networking", "Container Networking
  Basics", "Kubernetes Networking Introduction", "Kubernetes Networking
  Abstractions").
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 3–5 ("Container Runtime", "Container
  Storage", "Pod Networking") & Chapter 12 (CPU CFS throttling).
"""
from typing import Any, Dict, List, Mapping, Tuple


def simulate_cgroup_v2_cpu_and_memory(
    *,
    cpu_limit_cores: float,
    active_threads: int,
    period_ms: float = 100.0,
    anon_rss_mi: int = 0,
    tmpfs_shm_mi: int = 0,
    active_file_cache_mi: int = 0,
    inactive_file_cache_mi: int = 0,
    kernel_slab_mi: int = 0,
    memory_max_mi: int = 102400,
) -> Dict[str, Any]:
    """Model Section 3 Cgroup v2 CPU CFS quota throttling and memory working_set:
    - A limit of `cpu_limit_cores` grants `quota_ms = cpu_limit_cores * period_ms`
      of CPU time per `period_ms` window.
    - `active_threads` burning simultaneously consume `active_threads` ms of
      quota per 1 ms of wall-clock time, exhausting the period's quota after
      `wall_active_ms = min(period_ms, quota_ms / active_threads)` and stalling
      for `throttled_wall_ms = period_ms - wall_active_ms`.
    - `memory_current_mi` includes `anon_rss + tmpfs_shm + active_file +
      inactive_file + kernel_slab`.
    - Kubelet's `working_set_mi` = `memory_current_mi - inactive_file_cache_mi`.
    """
    quota_ms = cpu_limit_cores * period_ms
    wall_active_ms = min(period_ms, quota_ms / max(1, active_threads))
    throttled_wall_ms = round(period_ms - wall_active_ms, 2)

    memory_current = anon_rss_mi + tmpfs_shm_mi + active_file_cache_mi + inactive_file_cache_mi + kernel_slab_mi
    working_set = memory_current - inactive_file_cache_mi

    return {
        "quota_ms_per_period": round(quota_ms, 2),
        "wall_active_ms": round(wall_active_ms, 2),
        "throttled_wall_ms": throttled_wall_ms,
        "is_throttled": (throttled_wall_ms > 0.0),
        "memory_current_mi": memory_current,
        "working_set_mi": working_set,
        "oom_triggered": (working_set > memory_max_mi),
    }


def audit_gpu_node_kernel_sysctls(sysctls: Mapping[str, int]) -> Tuple[bool, List[str]]:
    """Model Section 9 GPU Kubernetes node sysctl baseline & kubelet
    `protectKernelDefaults` requirements.
    """
    errors: List[str] = []
    # Kubelet protectKernelDefaults requirements
    if sysctls.get("vm.overcommit_memory") != 1:
        errors.append("vm.overcommit_memory must be 1 (required by protectKernelDefaults)")
    if sysctls.get("kernel.panic") != 10:
        errors.append("kernel.panic must be 10 (required by protectKernelDefaults)")
    if sysctls.get("kernel.panic_on_oops") != 1:
        errors.append("kernel.panic_on_oops must be 1 (required by protectKernelDefaults)")

    # Networking & GPU node requirements
    if sysctls.get("net.ipv4.ip_forward") != 1:
        errors.append("net.ipv4.ip_forward must be 1 for Pod routing")
    if sysctls.get("net.bridge.bridge-nf-call-iptables") != 1:
        errors.append("net.bridge.bridge-nf-call-iptables must be 1")
    if sysctls.get("kernel.numa_balancing", 1) != 0:
        errors.append("kernel.numa_balancing should be 0 on multi-NUMA GPU nodes")
    if sysctls.get("net.ipv4.conf.all.rp_filter", 1) not in {0, 2}:
        errors.append("net.ipv4.conf.all.rp_filter must be 0 or 2 on multi-NIC RDMA GPU nodes")

    return (len(errors) == 0), errors


def check_kernel_version_features(major: int, minor: int) -> Dict[str, bool]:
    """Model Section 2, 6, & 9 Linux kernel version capability matrix."""
    ver = (major, minor)
    return {
        "cgroup_v2_mature": ver >= (5, 2),
        "bpf_host_routing": ver >= (5, 10),
        "idmapped_mounts": ver >= (5, 12),
        "idmapped_overlay_userns_pods": ver >= (5, 19),
        "eevdf_scheduler": ver >= (6, 6),
        "netkit_bpf_devices": ver >= (6, 7),
    }
