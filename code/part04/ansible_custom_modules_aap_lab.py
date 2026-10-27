#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.15: Custom modules, plug-ins and Ansible Automation Platform."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_custom_modules_aap import (
    execute_gpu_power_limit_module,
    slurm_expand_hostlist,
    slurm_hostlist,
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
    # 1. Section 2: gpu_power_limit custom module (bounds check, --check mode, apply, and idempotent second run)
    gpus = {0: 700.0, 1: 700.0}
    bad = execute_gpu_power_limit_module(current_watts_by_gpu=gpus, target_watts=1200)
    dry = execute_gpu_power_limit_module(current_watts_by_gpu=gpus, target_watts=650, check_mode=True, diff_mode=True)
    gpus_after_dry = dict(gpus)
    run1 = execute_gpu_power_limit_module(current_watts_by_gpu=gpus, target_watts=650, check_mode=False)
    run2 = execute_gpu_power_limit_module(current_watts_by_gpu=gpus, target_watts=650, check_mode=False)
    check(
        "gpu_power_limit rejects watts>1000, previews diff without mutating in --check mode, mutates on run 1, and is idempotent on run 2",
        bad["failed"] is True
        and dry["changed"] is True
        and gpus_after_dry == {0: 700.0, 1: 700.0}
        and "diff" in dry
        and run1["changed"] is True
        and gpus == {0: 650.0, 1: 650.0}
        and run2["changed"] is False,
    )

    # 2. Section 3: slurm_hostlist and slurm_expand_hostlist round-trip
    hosts = ["gpu001", "gpu002", "gpu003", "gpu005"]
    folded = slurm_hostlist(hosts)
    expanded = slurm_expand_hostlist(folded)
    check(
        "slurm_hostlist folds ['gpu001', 'gpu002', 'gpu003', 'gpu005'] to 'gpu[001-003,005]' and expands back losslessly",
        folded == "gpu[001-003,005]" and expanded == hosts,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
