#!/usr/bin/env python3
"""MPI MCA priority, NCCL_SOCKET_IFNAME prefix matcher, and AllReduce busbw models for Chapter 6.4."""

MCA_PRIORITY_ORDER = (
    "global_config_file",       # 1. /etc/openmpi-mca-params.conf (lowest)
    "user_config_file",         # 2. $HOME/.openmpi/mca-params.conf
    "tuned_option_file",        # 3. mpiexec --tune file1,file2
    "environment_variable",     # 4. export OMPI_MCA_xxx=value
    "command_line_flag",        # 5. mpiexec -mca xxx value (highest)
)


def resolve_openmpi_mca_param(sources: dict[str, str]) -> tuple[str, str]:
    """Return the winning (source_layer, value) according to SCL Chapter 21 5-level MCA priority."""
    winner_layer = ""
    winner_val = ""
    for layer in MCA_PRIORITY_ORDER:
        if layer in sources and sources[layer] != "":
            winner_layer = layer
            winner_val = sources[layer]
    return winner_layer, winner_val


def match_nccl_ifname(interfaces: list[str], spec: str) -> list[str]:
    """Filter network interface names using SCL Chapter 21 NCCL_SOCKET_IFNAME / NCCL_IB_HCA rules.

    Rules:
    - plain 'eth': prefix match (starts with 'eth')
    - '=eth1': exact match ('eth1' only, not 'eth11')
    - '^docker': exclude prefix (rejects anything starting with 'docker')
    - '^=eth0': exclude exact (rejects 'eth0' specifically)
    """
    tokens = [t.strip() for t in spec.split(",") if t.strip()]
    ex_exact = {t[2:] for t in tokens if t.startswith("^=")}
    ex_prefix = [t[1:] for t in tokens if t.startswith("^") and not t.startswith("^=")]
    inc_exact = {t[1:] for t in tokens if t.startswith("=")}
    inc_prefix = [t for t in tokens if not t.startswith(("^", "="))]

    selected = []
    for iface in interfaces:
        if iface in ex_exact or any(iface.startswith(p) for p in ex_prefix):
            continue
        if inc_exact or inc_prefix:
            if iface in inc_exact or any(iface.startswith(p) for p in inc_prefix):
                selected.append(iface)
        else:
            selected.append(iface)
    return selected


def compute_allreduce_algbw_and_busbw(tensor_bytes: int, elapsed_sec: float, num_ranks: int) -> dict[str, float]:
    """Return algorithmic bandwidth (GB/s) and ring bus bandwidth (GB/s) = algbw * 2*(n-1)/n."""
    algbw_gbps = (tensor_bytes / 1e9) / elapsed_sec
    factor = (2.0 * (num_ranks - 1) / num_ranks) if num_ranks > 1 else 1.0
    return {
        "algbw_gbps": round(algbw_gbps, 2),
        "busbw_gbps": round(algbw_gbps * factor, 2),
        "ring_factor": round(factor, 4),
    }


if __name__ == "__main__":
    print("MCA winner:", resolve_openmpi_mca_param({"global_config_file": "ob1", "environment_variable": "ucx"}))
    ifaces = ["lo", "docker0", "eth0", "eth1", "eth11", "bond0"]
    print("NCCL '=eth1':", match_nccl_ifname(ifaces, "=eth1"))
    print("NCCL '^docker,^=lo':", match_nccl_ifname(ifaces, "^docker,^=lo"))
    # Reference 1-rank mpi_allreduce.py timings on Apple Silicon (Open MPI 5.0.11):
    # 1 float: 0.001 ms, 1,000 floats: 0.001 ms, 1,000,000 floats: 0.228 ms, 8,000,000 floats: 1.363 ms
    print("AllReduce 1 GB in 0.005s on 8 ranks:", compute_allreduce_algbw_and_busbw(1_000_000_000, 0.005, 8))
