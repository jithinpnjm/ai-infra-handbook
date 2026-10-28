#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.9: Slurm accounting and scheduling policy: QOS, fair-share, backfill, preemption."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairtree_sim import Node, decay, fair_tree, level_fs, priority

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


def compute_tres_billing(
    cpus: int, mem_gib: float, gpus: int, weights: dict[str, float], max_tres_mode: bool = False
) -> float:
    """Compute TRES billing score using either sum (default) or MAX_TRES (SCL Ch. 15 & Slurm docs)."""
    terms = [
        cpus * weights.get("CPU", 0.0),
        mem_gib * weights.get("Mem", 0.0),
        gpus * weights.get("GPU", 0.0),
    ]
    return round(max(terms) if max_tres_mode else sum(terms), 3)


def main() -> None:
    # 1. Section 4: Fair Tree Level Fairshare (LF = S / U) and depth-first ranking (5500 / 5700 = 0.965 vs 200 / 5700 = 0.035)
    tree = Node(
        "root",
        1,
        children=[
            Node("physics", 60, children=[Node("alice", 1, 5000), Node("bob", 1, 500)]),
            Node("biology", 40, children=[Node("carol", 1, 100), Node("dave", 1, 100)]),
        ],
    )
    total_usage = 5000 + 500 + 100 + 100  # 5700
    u_phys = round(5500 / total_usage, 3)  # 0.965
    u_bio = round(200 / total_usage, 3)  # 0.035
    lf_phys = round(level_fs(tree.children[0], tree.children), 3)
    lf_bio = round(level_fs(tree.children[1], tree.children), 3)
    ft = fair_tree(tree)
    check(
        "Fair Tree ranks biology (LF=11.400) ahead of physics (LF=0.622): carol=1.00, dave=0.75, bob=0.50, alice=0.25",
        total_usage == 5700
        and u_phys == 0.965
        and u_bio == 0.035
        and lf_phys == 0.622
        and lf_bio == 11.400
        and ft == {"carol": 1.0, "dave": 0.75, "bob": 0.5, "alice": 0.25},
    )

    # 2. Section 3 & 4: Half-life usage decay (7-day half-life on 8000), integer weight truncation (0.59534 vs 0.50002 / 0.595 vs 0.501), and Multifactor Priority calculation
    d7 = round(decay(8000, 7, 7.0))
    d28 = round(decay(8000, 28, 7.0))
    trunc_tie = int(10 * 0.59534) == int(10 * 0.50002) and int(10 * 0.595) == int(10 * 0.501)
    p_alice = priority(
        age_min=60, max_age_min=7 * 1440, fairshare=0.25, qos_prio=10, max_qos_prio=10, part_factor=1, max_part_factor=1
    )
    p_carol = priority(
        age_min=60 * 24 * 3,
        max_age_min=7 * 1440,
        fairshare=1.0,
        qos_prio=1,
        max_qos_prio=10,
        part_factor=1,
        max_part_factor=1,
    )
    check(
        "decay(8000) -> 4000 (7d) & 500 (28d), weight=10 truncates 0.59534 & 0.50002 to 5, and multifactor priority scores carol (102428) > alice (36005)",
        d7 == 4000 and d28 == 500 and trunc_tie and p_alice == 36005 and p_carol == 102428,
    )

    # 3. Section 1 & 4: TRESBillingWeights sum vs MAX_TRES (SCL Ch. 15 example: 2 GPUs, 16 CPUs, 1024G Mem at GPU=1.0,CPU=0.001,Mem=0.01G; 16*0.001=0.016)
    scl_w = {"GPU": 1.0, "CPU": 0.001, "Mem": 0.01}
    cpu_term = round(16 * scl_w["CPU"], 3)  # 0.016
    bill_sum = compute_tres_billing(cpus=16, mem_gib=1024, gpus=2, weights=scl_w, max_tres_mode=False)
    bill_max = compute_tres_billing(cpus=16, mem_gib=1024, gpus=2, weights=scl_w, max_tres_mode=True)
    check(
        "compute_tres_billing computes 2*1.0 + 16*0.001 (0.016) + 1024*0.01 = 12.256 (sum) vs 10.24 (MAX_TRES)",
        cpu_term == 0.016 and bill_sum == 12.256 and bill_max == 10.24,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
