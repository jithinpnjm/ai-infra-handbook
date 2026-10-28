#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.4: MPI in practice: Open MPI, ranks, collectives and tuning."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mpi_tuning import (
    compute_allreduce_algbw_and_busbw,
    match_nccl_ifname,
    resolve_openmpi_mca_param,
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
    # 1. Section 6: Open MPI 5-level MCA priority resolution (SCL Ch. 21)
    layer1, val1 = resolve_openmpi_mca_param(
        {
            "global_config_file": "ob1",
            "user_config_file": "cm",
            "tuned_option_file": "ucx",
        }
    )
    layer2, val2 = resolve_openmpi_mca_param(
        {
            "global_config_file": "ob1",
            "environment_variable": "ucx",
            "command_line_flag": "^ucx",
        }
    )
    check(
        "resolve_openmpi_mca_param enforces 5-level priority: global < user < --tune < OMPI_MCA_ env < -mca CLI flag",
        (layer1, val1) == ("tuned_option_file", "ucx") and (layer2, val2) == ("command_line_flag", "^ucx"),
    )

    # 2. Section 12: NCCL_SOCKET_IFNAME / NCCL_IB_HCA prefix & exact matching rules (SCL Ch. 21)
    ifaces = ["lo", "docker0", "eth0", "eth1", "eth11", "bond0"]
    check(
        "match_nccl_ifname handles prefix ('eth'), exact ('=eth1'), exclude-prefix ('^docker'), and exclude-exact ('^=eth0')",
        match_nccl_ifname(ifaces, "eth") == ["eth0", "eth1", "eth11"]
        and match_nccl_ifname(ifaces, "=eth1") == ["eth1"]
        and match_nccl_ifname(ifaces, "^docker,^=lo,^=eth0") == ["eth1", "eth11", "bond0"],
    )

    # 3. Section 10: Algorithmic Bandwidth vs Bus Bandwidth (algbw * 2*(n-1)/n)
    bw = compute_allreduce_algbw_and_busbw(tensor_bytes=1_000_000_000, elapsed_sec=0.005, num_ranks=8)
    check(
        "compute_allreduce_algbw_and_busbw computes algbw = 200.0 GB/s and busbw = 350.0 GB/s (factor 1.75 on 8 ranks)",
        bw["algbw_gbps"] == 200.0 and bw["busbw_gbps"] == 350.0 and bw["ring_factor"] == 1.75,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
