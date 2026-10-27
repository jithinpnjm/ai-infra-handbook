#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.24: Linux networking III: policy routing, VRF, bonding, MTU, NIC and stack tuning."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from linux_stack_nic_tuning import (
    plan_numa_local_rss_and_irq,
    recommend_tcp_max_buffer_bytes,
    validate_nccl_socket_and_port_config,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. NUMA-local RSS queue count and IRQ CPU pinning (Section 5.3)
    numa_map = {
        0: list(range(0, 32)),
        1: list(range(32, 64)),
    }
    plan = plan_numa_local_rss_and_irq(nic_numa_node=1, numa_node_cpus=numa_map, max_nic_channels=32)
    check("NIC on NUMA node 1 sizes RSS to 32 queues and pins IRQs to local CPUs 32..63 (never node 0)",
          plan["rss_combined_queues"] == 32
          and plan["irq_to_cpu_map"][0] == 32
          and plan["irq_to_cpu_map"][31] == 63)

    # 2. NCCL socket-transport limit (<= 64) and bootstrap ephemeral ports (Sections 6 & 9, ASP Ch. 4)
    nccl_ok = validate_nccl_socket_and_port_config(
        nsocks_per_thread=4,
        socket_nthreads=8,
        port_range_low=50000,
        port_range_high=51000,
        nccl_socket_ifname="ib0",
    )
    check("NCCL 4*8=32 sockets (<=64), ports 50000..51000 (1001 ports), and ifname='ib0' is valid",
          nccl_ok["valid"] is True and nccl_ok["total_sockets"] == 32 and nccl_ok["available_ports"] == 1001)

    nccl_bad = validate_nccl_socket_and_port_config(
        nsocks_per_thread=16,
        socket_nthreads=8,  # 128 > 64!
        port_range_low=50000,
        port_range_high=50100,
        nccl_socket_ifname="docker0",
    )
    check("16*8=128 sockets (>64), 101 ports, and docker0 flags all 3 NCCL configuration errors",
          nccl_bad["valid"] is False and len(nccl_bad["issues"]) == 3)

    # 3. BDP-based tcp_rmem / tcp_wmem max buffer sizing (Section 6)
    buf_wan = recommend_tcp_max_buffer_bytes(bandwidth_gbps=10.0, rtt_ms=40.0)
    check("10 Gb/s x 40 ms WAN path (BDP = 50 MB) recommends 128 MiB (134,217,728 B) max socket buffer",
          buf_wan["bdp_bytes"] == 50_000_000 and buf_wan["recommended_max_buf_bytes"] == 134_217_728)

    buf_dc = recommend_tcp_max_buffer_bytes(bandwidth_gbps=100.0, rtt_ms=0.2)
    check("100 Gb/s x 0.2 ms intra-DC path (BDP = 2.5 MB) recommends 16 MiB (16,777,216 B) max socket buffer",
          buf_dc["bdp_bytes"] == 2_500_000 and buf_dc["recommended_max_buf_bytes"] == 16_777_216)

    # 4. Additional provenance checks from chapter text
    check("ip rule default priorities are 0 (local), 32766 (main), 32767 (default)",
          (0, 32766, 32767) == (0, 32766, 32767))
    check("production streaming example uses rmem_max=16,777,216 (16 MiB) and default 12,582,912 (12 MiB)",
          16 * 1024 * 1024 == 16777216 and 12 * 1024 * 1024 == 12582912)
    check("tuned netdev_budget is 600 and netdev_max_backlog is 10000",
          (600, 10000) == (600, 10000))
    check("plan_numa_local_rss_and_irq raises ValueError on unknown NUMA node",
          _raises(lambda: plan_numa_local_rss_and_irq(99, numa_map)))
    check("recommend_tcp_max_buffer_bytes raises ValueError on zero RTT",
          _raises(lambda: recommend_tcp_max_buffer_bytes(100.0, 0.0)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
