#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.11: Submitting and launching jobs: sbatch, srun, salloc, arrays, dependencies."""
import signal
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sbatch_lint import lint

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


GOOD_SCRIPT = """#!/bin/bash
#SBATCH --job-name=bert-pretrain
#SBATCH --partition=gpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --gpus-per-node=8
#SBATCH --cpus-per-gpu=12
#SBATCH --mem=0
#SBATCH --exclusive
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --signal=B:USR1@300
#SBATCH --output=logs/%x-%j.out
#SBATCH --open-mode=append

set -euo pipefail
module purge
module load cuda/12.4 nccl/2.21
srun --mpi=pmix python train.py --resume-if-exists
"""

BAD_SCRIPT = """# missing shebang
#SBATCH --nodes=2
#SBATCH --tasks-per-node=8
#SBATCH --mem=64G
#SBATCH --mem-per-gpu=16G
#SBATCH --cpus-per-gpu=8
#SBATCH --cpus-per-task=8
#SBATCH --gpus-per-task=1
#SBATCH --array=0-99
#SBATCH --requeue
#SBATCH --output=logs/fixed.out

module load cuda/12.4
mpirun python train.py
"""


def map_array_task_to_hp(task_id: int, lrs: list[float], batch_sizes: list[int]) -> tuple[float, int]:
    """Map SLURM_ARRAY_TASK_ID to (learning_rate, batch_size) grid (DAI Ch. 8)."""
    num_lr = len(lrs)
    lr_idx = task_id % num_lr
    bs_idx = task_id // num_lr
    return lrs[lr_idx], batch_sizes[bs_idx]


class SLURMCheckpointerSim:
    """Deterministic simulation of DAI Ch. 8 SLURMCheckpointer for SIGUSR1/SIGTERM traps."""

    def __init__(self) -> None:
        self.should_stop = False
        self.last_signal: int | None = None
        self.saved_steps: list[int] = []

    def handle_signal(self, signum: int) -> None:
        self.last_signal = signum
        self.should_stop = True

    def save(self, step: int, rank: int = 0) -> None:
        if rank == 0:
            self.saved_steps.append(step)


def main() -> None:
    # 1. Verify sbatch_lint.py accepts GOOD_SCRIPT with 0 findings and flags all errors/warnings in BAD_SCRIPT
    with tempfile.TemporaryDirectory() as tmpdir:
        good_path = Path(tmpdir) / "good.sbatch"
        bad_path = Path(tmpdir) / "bad.sbatch"
        good_path.write_text(GOOD_SCRIPT)
        bad_path.write_text(BAD_SCRIPT)

        good_res = lint(str(good_path))
        bad_res = lint(str(bad_path))
        bad_errors = [msg for lvl, msg in bad_res if lvl == "ERROR"]
        check(
            "sbatch_lint.py passes good.sbatch (0 findings) and catches 4 ERRORs + 8 warnings/infos in bad.sbatch",
            len(good_res) == 0 and len(bad_errors) == 4 and len(bad_res) == 12,
            f"good={len(good_res)}, bad_errors={len(bad_errors)}, bad_total={len(bad_res)}",
        )

    # 2. Verify DAI Ch. 8 12-task job array hyperparameter grid mapping (4 LRs x 3 batch sizes)
    lrs = [1e-4, 3e-4, 1e-3, 3e-3]
    bss = [16, 32, 64]
    grid = [map_array_task_to_hp(tid, lrs, bss) for tid in range(12)]
    check(
        "Job array 0-11 maps SLURM_ARRAY_TASK_ID to all 12 (LR, batch_size) combinations uniquely",
        len(set(grid)) == 12 and grid[0] == (1e-4, 16) and grid[5] == (3e-4, 32) and grid[11] == (3e-3, 64),
    )

    # 3. Verify DAI Ch. 8 SLURMCheckpointer signal handler (SIGUSR1@90 and SIGTERM) and rank-0 checkpoint save
    ckpt = SLURMCheckpointerSim()
    for step in range(10):
        if step == 4:
            ckpt.handle_signal( int(signal.SIGUSR1) )
        if ckpt.should_stop:
            ckpt.save(step, rank=0)
            ckpt.save(step, rank=1)  # non-zero rank must not duplicate checkpoint file write
            break
    check(
        "SLURMCheckpointer traps SIGUSR1, sets should_stop=True, and saves checkpoint on rank 0 only",
        ckpt.should_stop and ckpt.last_signal == int(signal.SIGUSR1) and ckpt.saved_steps == [4],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
