#!/usr/bin/env python3
"""Cluster anatomy, 3D torus hops, power headroom, and runbook validator for Chapter 6.2."""


def torus_3d_max_hops(n: int, m: int, k: int) -> int:
    """Return maximum hop count [N/2] + [M/2] + [K/2] in an N x M x K 3D torus (SCL Ch. 4)."""
    return (n // 2) + (m // 2) + (k // 2)


def scheduler_declared_cores(sockets: int, physical_cores_per_socket: int, threads_per_core: int = 2) -> dict[str, int]:
    """Return OS logical CPUs vs physical core count to declare to the scheduler with BIOS HT enabled (SCL Ch. 4)."""
    physical_total = sockets * physical_cores_per_socket
    logical_total = physical_total * threads_per_core
    return {
        "os_logical_cpus": logical_total,
        "scheduler_declared_cores": physical_total,
        "reserved_daemon_threads": logical_total - physical_total,
    }


def plan_cluster_power_and_ports(
    compute_nodes: int,
    gpus_per_node: int = 8,
    kw_per_compute_node: float = 10.0,
    login_nodes: int = 2,
    head_nodes: int = 2,
    headroom_fraction: float = 0.10,
) -> dict[str, float | int]:
    """Compute fabric ports, management ports, and power budget with 5-10% headroom (SCL Ch. 3 & Sec. 9)."""
    compute_fabric_ports = compute_nodes * gpus_per_node
    total_servers = compute_nodes + login_nodes + head_nodes
    raw_compute_kw = compute_nodes * kw_per_compute_node
    budget_kw = round(raw_compute_kw * (1.0 + headroom_fraction), 1)
    return {
        "compute_fabric_ports": compute_fabric_ports,
        "inband_eth_ports": total_servers,
        "oob_bmc_ports": total_servers,
        "raw_compute_kw": raw_compute_kw,
        "budget_kw_with_headroom": budget_kw,
    }


REQUIRED_RUNBOOK_COLUMNS = ("phase", "action", "start", "duration", "dependency", "owner", "status", "info")


def validate_runbook_schema(columns: list[str] | tuple[str, ...]) -> bool:
    """Verify that a maintenance runbook includes all 8 standard columns from SCL Ch. 3."""
    col_set = {c.strip().lower() for c in columns}
    return all(req in col_set for req in REQUIRED_RUNBOOK_COLUMNS)


if __name__ == "__main__":
    print("8x8x8 3D torus max hops:", torus_3d_max_hops(8, 8, 8))
    print("2x64 node HT trick:", scheduler_declared_cores(2, 64, 2))
    # 32-node GPU cluster: 320.0 kW raw compute power, 352.0 kW with 10% headroom
    print("32-node GPU cluster plan (320.0 kW raw, 352.0 kW with headroom):", plan_cluster_power_and_ports(32, 8, 10.0, 2, 2, 0.10))
