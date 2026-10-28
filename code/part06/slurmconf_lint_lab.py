#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.8: Slurm configuration: nodes, partitions and cgroups."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slurmconf_lint import expand, lint

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


def reorder_nodes_switch_as_node_rank(
    allocated_nodes: list[str], switch_to_nodes: dict[str, list[str]]
) -> list[str]:
    """Sort allocated_nodes by leaf switch first, then by node name (TopologyParam=SwitchAsNodeRank, SCL Ch. 15)."""
    node_to_switch = {}
    for sw, nodes in switch_to_nodes.items():
        for n in nodes:
            node_to_switch[n] = sw
    return sorted(allocated_nodes, key=lambda n: (node_to_switch.get(n, "zzz"), n))


def main() -> None:
    # 1. Section 2 & 7: Hostlist expansion gpu[01-04,07]
    expanded = expand("gpu[01-04,07]")
    check(
        "expand('gpu[01-04,07]') returns ['gpu01', 'gpu02', 'gpu03', 'gpu04', 'gpu07']",
        expanded == ["gpu01", "gpu02", "gpu03", "gpu04", "gpu07"],
    )

    # 2. Section 7: slurmconf_lint.py catches broken CPU math, missing GresTypes, duplicate nodes, undefined partition nodes, and 2 Default=YES partitions
    broken_conf = """
ClusterName=test
SlurmctldHost=ctl1
SelectType=select/cons_tres
SelectTypeParameters=CR_Core
ProctrackType=proctrack/linuxproc
TaskPlugin=task/affinity
NodeName=gpu[01-04] CPUs=64 Sockets=2 CoresPerSocket=16 ThreadsPerCore=1 Gres=gpu:8 State=UNKNOWN
NodeName=gpu04 CPUs=32 Sockets=2 CoresPerSocket=16 ThreadsPerCore=1 RealMemory=500000 State=UNKNOWN
PartitionName=gpu Nodes=gpu[01-05] Default=YES State=UP
PartitionName=debug Nodes=gpu[01-02] Default=YES State=UP
"""
    good_conf = """
ClusterName=prod
SlurmctldHost=ctl1
SelectType=select/cons_tres
SelectTypeParameters=CR_Core_Memory
ProctrackType=proctrack/cgroup
TaskPlugin=task/affinity,task/cgroup
GresTypes=gpu
ReturnToService=1
NodeName=gpu[01-04] CPUs=64 Sockets=2 CoresPerSocket=16 ThreadsPerCore=2 RealMemory=500000 Gres=gpu:8 State=UNKNOWN
PartitionName=gpu Nodes=gpu[01-04] Default=YES State=UP
"""
    with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as fb, tempfile.NamedTemporaryFile(
        "w", suffix=".conf", delete=False
    ) as fg:
        fb.write(broken_conf)
        fg.write(good_conf)
        b_path, g_path = fb.name, fg.name

    probs_b, warns_b = lint(b_path)
    probs_g, warns_g = lint(g_path)
    check(
        "slurmconf_lint.py flags all 5 errors and 3 warnings on broken config and 0 findings on valid GPU config",
        len(probs_b) == 5 and len(warns_b) == 3 and len(probs_g) == 0 and len(warns_g) == 0,
    )

    # 3. Section 6: TopologyParam=SwitchAsNodeRank sorting across interleaved leaf switches (SCL Ch. 15)
    switches = {"s0": ["n0", "n2", "n4", "n6"], "s1": ["n1", "n3", "n5", "n7"]}
    default_order = ["n0", "n1", "n2", "n3"]
    ranked = reorder_nodes_switch_as_node_rank(default_order, switches)
    check(
        "reorder_nodes_switch_as_node_rank groups ['n0', 'n2'] on s0 before ['n1', 'n3'] on s1",
        ranked == ["n0", "n2", "n1", "n3"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
