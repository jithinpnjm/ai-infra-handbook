"""Chapter 4.15 model: Idempotent check-mode-aware `gpu_power_limit` custom
Ansible module simulator, `slurm_hostlist` / `slurm_expand_hostlist` filter
plugin round-trip (`gpu[001-003,005]`), and `can_reach` (`AUR` Ch. 19) module
simulator.

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapters 19, 23, and 24:
  * Chapter 19 ("Creating Custom Modules"): When to write a module vs role vs
    `command`/`script`, `can_reach` module in Python (`AnsibleModule`,
    `module.run_command`, `add_file_common_args=True`, `supports_check_mode=True`,
    `exit_json`, `fail_json`), Bash (`# WANT_JSON` + `jq` parsing `$1`), and
    Perl (`JSON::PP`), shebang interpreter selection (`#!/usr/bin/python3` ->
    `ansible_python_interpreter`, `#!/bin/bash` -> `ansible_bash_interpreter`,
    and why `#!/usr/bin/env bash` bypasses `ansible_*_interpreter`), and debugging
    modules locally with `./hacking/test-module -m library/can_reach.py`.
  * Chapter 23 ("Ansible Automation Platform"): AAP 2 architecture (Automation
    Controller replacing Ansible Tower, Automation Hub, Execution Environments
    built with `ansible-builder` from `execution-environment.yml` + `requirements.yml`
    + `requirements.txt` + `bindep.txt` and run with `ansible-navigator`, and
    configuring Controller as code via `awx.awx` `tower_organization`,
    `tower_inventory`, `tower_host`, `tower_credential`, `tower_project`,
    `tower_job_template`, and `tower_job_launch` + `tower_job_wait`).
  * Chapter 24 ("Best Practices"): High modularity & high option value
    (composability, Tao of HashiCorp), decoupling inventories from projects and
    roles from collections, "releasing software is a one-bit decision, not a
    transfer of bytes", and Jez Humble's CALMS framework (Culture, Automation,
    Lean, Measurement, Sharing).
"""
import re
from typing import Dict, Iterable, List, Sequence


def execute_gpu_power_limit_module(
    *,
    current_watts_by_gpu: Dict[int, float],
    target_watts: int,
    gpu_index: int | None = None,
    tolerance: float = 1.0,
    check_mode: bool = False,
    diff_mode: bool = False,
) -> Dict[str, object]:
    """Model Section 2 `gpu_power_limit.py` custom module with `supports_check_mode=True`
    and `--diff` support.
    """
    if target_watts < 100 or target_watts > 1000:
        return {"failed": True, "changed": False, "msg": "watts must be in [100, 1000]"}

    indices = sorted(current_watts_by_gpu.keys()) if gpu_index is None else [gpu_index]
    before = {i: current_watts_by_gpu[i] for i in indices}
    to_change = [i for i in indices if abs(before[i] - target_watts) > tolerance]
    changed = bool(to_change)

    if changed and not check_mode:
        for i in to_change:
            current_watts_by_gpu[i] = float(target_watts)

    after = {i: (float(target_watts) if (changed and i in to_change) else before[i]) for i in indices}
    res: Dict[str, object] = {
        "failed": False,
        "changed": changed,
        "previous_watts": before,
        "applied_watts": after,
    }
    if diff_mode:
        res["diff"] = {"before": f"{before}\n", "after": f"{after}\n"}
    return res


def slurm_hostlist(hosts: Iterable[str]) -> str:
    """Model Section 3 `slurm_hostlist` filter plugin folding hostnames into
    Slurm bracket notation (`gpu[001-003,005]`).
    """
    pat = re.compile(r"^(.*?)(\d+)$")
    parsed = []
    for h in sorted(set(hosts)):
        m = pat.match(h)
        if not m:
            return ",".join(sorted(set(hosts)))
        parsed.append((m.group(1), int(m.group(2)), len(m.group(2))))
    if not parsed or len({(p[0], p[2]) for p in parsed}) != 1:
        return ",".join(sorted(set(hosts)))
    prefix, _, width = parsed[0]
    nums = [p[1] for p in parsed]
    ranges: List[str] = []
    start = prev = nums[0]
    for n in nums[1:] + [None]:  # type: ignore[list-item]
        if n == prev + 1:
            prev = n
            continue
        ranges.append(f"{start:0{width}d}" if start == prev else f"{start:0{width}d}-{prev:0{width}d}")
        if n is not None:
            start = prev = n
    return f"{prefix}[{','.join(ranges)}]"


def slurm_expand_hostlist(expr: str) -> List[str]:
    """Inverse of `slurm_hostlist`: expand `gpu[001-003,005]` back into host list."""
    m = re.match(r"^(.*?)\[([0-9,\-]+)\]$", expr)
    if not m:
        return [h for h in expr.split(",") if h]
    prefix, body = m.group(1), m.group(2)
    out: List[str] = []
    for token in body.split(","):
        if "-" in token:
            s_str, e_str = token.split("-", 1)
            width = len(s_str)
            for i in range(int(s_str), int(e_str) + 1):
                out.append(f"{prefix}{i:0{width}d}")
        else:
            out.append(f"{prefix}{token}")
    return out
