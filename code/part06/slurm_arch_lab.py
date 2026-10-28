#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.7: Slurm architecture and installation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slurm_arch import (
    SLURM_DAEMON_PORTS,
    check_test_partition_policy,
    compute_rpc_tree_depth,
    validate_munge_credential,
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
    # 1. Section 1 & 2: Slurm daemon ports (6817, 6818, 6819) and SCL Ch. 13 test partition rule (10-15m, 3-5 tasks)
    check(
        "SLURM_DAEMON_PORTS (6817, 6818, 6819, 17001, 17002) and check_test_partition_policy (10-15m, 3-5 queued tasks) pass",
        SLURM_DAEMON_PORTS["slurmctld"] == 6817
        and SLURM_DAEMON_PORTS["slurmd"] == 6818
        and SLURM_DAEMON_PORTS["slurmdbd"] == 6819
        and SLURM_DAEMON_PORTS["vn1_virtual_slurmd"] == 17001
        and SLURM_DAEMON_PORTS["vn2_virtual_slurmd"] == 17002
        and check_test_partition_policy(15, 4) is True
        and check_test_partition_policy(120, 20) is False,
    )

    # 2. Section 3: Hierarchical RPC fan-out depth (TreeWidth=50 -> 50 direct RPCs, depth 2 for 1024 nodes)
    tree = compute_rpc_tree_depth(num_nodes=1024, tree_width=50)
    check(
        "compute_rpc_tree_depth bounds controller direct RPCs to 50 and reaches 1024 nodes in 2 tree hops",
        tree["controller_direct_rpcs"] == 50 and tree["depth"] == 2,
    )

    # 3. Section 6 & 12: Munge credential validator (shared key match + 300s clock-skew window)
    ok_cred = validate_munge_credential("sha256:abc", "sha256:abc", 1000.0, 1120.0)
    bad_key = validate_munge_credential("sha256:abc", "sha256:def", 1000.0, 1005.0)
    rewound = validate_munge_credential("sha256:abc", "sha256:abc", 2000.0, 1000.0)
    expired = validate_munge_credential("sha256:abc", "sha256:abc", 1000.0, 1600.0)
    check(
        "validate_munge_credential accepts valid credential and catches key mismatch, rewound clock, and expired TTL",
        ok_cred["valid"] is True
        and "Invalid credential" in str(bad_key["error"])
        and "Rewound credential" in str(rewound["error"])
        and "Expired credential" in str(expired["error"]),
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
