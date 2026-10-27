"""Chapter 2.24 model: NUMA-local RSS queue and IRQ CPU affinity planner, NCCL
socket-transport connection limit validator (NCCL_NSOCKS_PERTHREAD *
NCCL_SOCKET_NTHREADS <= 64) and ephemeral port range checker, and BDP-based
tcp_rmem / tcp_wmem max buffer recommender.

Sources modeled:
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 10 ("Network": system-wide tunables, production streaming example,
  socket/TCP buffers, backlog, congestion control, device queues, socket options).
- Chris Fregly, AI Systems Performance Engineering (ai-systems-performance-engineering),
  Chapter 4 ("Tuning Distributed Networking Communication": MTU 9000, rmem/wmem,
  NUMA-local NIC IRQ affinity, NCCL bootstrap ip_local_port_range 50000..51000,
  NCCL_SOCKET_IFNAME, NCCL_NSOCKS_PERTHREAD * NCCL_SOCKET_NTHREADS <= 64).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9.
- nvidia-devops/volume-01/03-linux-networking-masterclass.md.
"""
from typing import Dict, List


def plan_numa_local_rss_and_irq(
    nic_numa_node: int,
    numa_node_cpus: Dict[int, List[int]],
    max_nic_channels: int = 64,
) -> Dict[str, object]:
    """Select RSS combined queue count and 1:1 CPU IRQ pinning restricted to the NIC's local NUMA node."""
    if nic_numa_node not in numa_node_cpus or not numa_node_cpus[nic_numa_node]:
        raise ValueError(f"Invalid or empty NUMA node: {nic_numa_node}")
    local_cpus = sorted(numa_node_cpus[nic_numa_node])
    rss_queues = min(len(local_cpus), max_nic_channels)
    irq_cpu_map = {q: local_cpus[q] for q in range(rss_queues)}
    return {
        "nic_numa_node": nic_numa_node,
        "rss_combined_queues": rss_queues,
        "irq_to_cpu_map": irq_cpu_map,
    }


def validate_nccl_socket_and_port_config(
    nsocks_per_thread: int,
    socket_nthreads: int,
    port_range_low: int,
    port_range_high: int,
    nccl_socket_ifname: str,
) -> Dict[str, object]:
    """Validate NCCL socket transport limits (<= 64 total sockets) and bootstrap port/interface config."""
    if nsocks_per_thread <= 0 or socket_nthreads <= 0 or port_range_high <= port_range_low:
        raise ValueError("Invalid NCCL socket or port parameters")
    total_sockets = nsocks_per_thread * socket_nthreads
    available_ports = port_range_high - port_range_low + 1
    issues: List[str] = []
    if total_sockets > 64:
        issues.append("nccl_total_sockets_exceeds_64_limit")
    if available_ports < 1000:
        issues.append("ephemeral_port_range_too_narrow_for_nccl_bootstrap")
    if nccl_socket_ifname in {"lo", "docker0", ""}:
        issues.append("invalid_nccl_socket_ifname_loopback_or_docker")
    return {
        "total_sockets": total_sockets,
        "available_ports": available_ports,
        "valid": len(issues) == 0,
        "issues": issues,
    }


def recommend_tcp_max_buffer_bytes(bandwidth_gbps: float, rtt_ms: float) -> Dict[str, int]:
    """Compute BDP in bytes and recommend a power-of-two rmem_max / wmem_max ceiling (16 MiB .. 128 MiB)."""
    if bandwidth_gbps <= 0 or rtt_ms <= 0:
        raise ValueError("bandwidth_gbps and rtt_ms must be positive")
    bdp_bytes = int(round((bandwidth_gbps * 1e9 / 8.0) * (rtt_ms / 1000.0)))
    # Pick smallest power-of-two MiB >= 2 * BDP, clamped to [16 MiB, 128 MiB]
    mib = 1024 * 1024
    target = max(16 * mib, min(128 * mib, 1 << (max(1, (2 * bdp_bytes - 1)).bit_length())))
    return {"bdp_bytes": bdp_bytes, "recommended_max_buf_bytes": target}
