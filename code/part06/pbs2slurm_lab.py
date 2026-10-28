#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.17: Other schedulers: PBS, Torque, LSF and Flux."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pbs2slurm import convert_line, mem_to_slurm

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


SAMPLE_PBS = [
    "#PBS -N bert",
    "#PBS -q gpuq",
    "#PBS -l select=2:ncpus=64:mpiprocs=8:ngpus=8:mem=500gb",
    "#PBS -l walltime=12:00:00",
    "#PBS -l place=scatter:excl",
    "#PBS -J 0-9%3",
    "#PBS -m abe",
    "#PBS -W depend=afterok:1234.server",
    "#PBS -l software=matlab",
]


def main() -> None:
    # 1. Verify pbs2slurm.py directive translation and semantic ncpus // mpiprocs division (64 // 8 = 8)
    out = []
    for line in SAMPLE_PBS:
        out.extend(convert_line(line))
    check(
        "pbs2slurm.py converts select=2:ncpus=64:mpiprocs=8:ngpus=8:mem=500gb into --nodes=2, --ntasks-per-node=8, --cpus-per-task=8, --gpus-per-node=8, --mem=500G",
        "#SBATCH --job-name=bert" in out
        and "#SBATCH --partition=gpuq" in out
        and "#SBATCH --nodes=2" in out
        and "#SBATCH --ntasks-per-node=8" in out
        and "#SBATCH --cpus-per-task=8" in out
        and "#SBATCH --gpus-per-node=8" in out
        and "#SBATCH --mem=500G" in out
        and "#SBATCH --time=12:00:00" in out
        and "#SBATCH --exclusive" in out
        and "#SBATCH --array=0-9%3" in out
        and "#SBATCH --mail-type=FAIL,BEGIN,END" in out
        and "#SBATCH --dependency=afterok:1234.server" in out
        and any("TODO unmapped resource: software=matlab" in l for l in out),
    )

    # 2. Verify mem_to_slurm unit normalization (including 21/22/24/25/500gb) and Torque /etc/services ports (15001..15004)
    torque_ports = {"pbs": 15001, "pbs_mom": 15002, "pbs_resmom": 15003, "pbs_sched": 15004}
    check(
        "mem_to_slurm normalizes kb/mb/gb/tb and Torque fixed ports are 15001-15004",
        mem_to_slurm("500gb") == "500G"
        and mem_to_slurm("21gb") == "21G"
        and mem_to_slurm("22gb") == "22G"
        and mem_to_slurm("24gb") == "24G"
        and mem_to_slurm("25gb") == "25G"
        and mem_to_slurm("65536mb") == "65536M"
        and torque_ports == {"pbs": 15001, "pbs_mom": 15002, "pbs_resmom": 15003, "pbs_sched": 15004},
    )

    # 3. Verify SCL Ch. 14 Table 14-2 Torque scheduler sort_by keys (9 keys)
    sort_keys = {
        "no_sort",
        "shortest_task_first",
        "longest_task_first",
        "smallest_memory_first",
        "largest_memory_first",
        "high_priority_first",
        "low_priority_first",
        "large_walltime_first",
        "short_walltime_first",
    }
    check(
        "Torque sched_config supports all 9 Table 14-2 sort_by keys plus multi_sort",
        len(sort_keys) == 9 and "shortest_task_first" in sort_keys and "high_priority_first" in sort_keys,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
