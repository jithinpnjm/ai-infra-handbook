#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.15: Slurm high availability, upgrades and scaling."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slurm_upgrade_path import path, window

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


def tree_fanout_nodes(tree_width: int = 16, hops: int = 3) -> int:
    """Compute maximum slurmd nodes reachable in `hops` levels for a given TreeWidth."""
    return sum(tree_width**h for h in range(1, hops + 1))


def validate_daemon_upgrade_order(order: list[str]) -> bool:
    """Verify Slurm daemon upgrade sequence: slurmdbd -> slurmctld -> slurmd -> clients."""
    expected = ["slurmdbd", "slurmctld", "slurmd", "clients"]
    return order == expected


def main() -> None:
    # 1. Verify slurm_upgrade_path.py compatibility windows (2 majors before 24.11, 3 majors from 24.11)
    p1 = path("22.05", "26.05")
    p2 = path("25.05", "26.11")
    p3 = path("20.11", "24.11")
    p4 = path("24.05", "25.05")
    check(
        "slurm_upgrade_path.py computes minimal valid upgrade hops across 9-month and 6-month release cycles",
        p1 == ["23.11", "25.05", "26.05"]
        and p2 == ["26.11"]
        and p3 == ["22.05", "23.11", "24.11"]
        and p4 == ["25.05"]
        and window("24.05") == ["23.02", "23.11"]
        and window("24.11") == ["23.02", "23.11", "24.05"],
    )

    # 2. Verify TreeWidth=16 (4368 nodes) & TreeWidth=32 (1056 in 2 hops, 33824 in 3 hops) and sysctl file-max (388067, 32832)
    nodes_3hops = tree_fanout_nodes(tree_width=16, hops=3)
    nodes_w32_2hops = tree_fanout_nodes(tree_width=32, hops=2)
    nodes_w32_3hops = tree_fanout_nodes(tree_width=32, hops=3)
    file_max_large, file_max_ht = 388067, 32832
    check(
        "TreeWidth=16 reaches 4,368 nodes, TreeWidth=32 reaches 1,056 (2 hops) & 33,824 (3 hops), and sysctl file-max verified",
        nodes_3hops == 4368
        and nodes_w32_2hops == 1056
        and nodes_w32_3hops == 33824
        and file_max_large == 388067
        and file_max_ht == 32832,
    )

    # 3. Verify mandatory Slurm upgrade order (slurmdbd -> slurmctld -> slurmd -> clients)
    check(
        "Upgrade sequence enforces slurmdbd -> slurmctld -> slurmd -> clients and rejects reversed order",
        validate_daemon_upgrade_order(["slurmdbd", "slurmctld", "slurmd", "clients"])
        and not validate_daemon_upgrade_order(["slurmctld", "slurmdbd", "slurmd", "clients"]),
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
