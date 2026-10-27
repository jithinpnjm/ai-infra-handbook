#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.14: Ansible at scale: performance, strategies and callbacks."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_scale_performance import (
    estimate_play_wall_clock_seconds,
    format_jsonl_audit_event,
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
    # 1. Section 2 & AUR Ch. 20: ControlPersist (0.319s -> 0.010s) + Pipelining (3 -> 1 SSH trips) + forks speedup
    tasks = [0.2, 0.2, 0.2, 0.2, 0.2]
    t_unopt = estimate_play_wall_clock_seconds(
        num_hosts=50,
        forks=5,
        task_durations_normal=tasks,
        use_control_persist=False,
        use_pipelining=False,
    )
    t_opt = estimate_play_wall_clock_seconds(
        num_hosts=50,
        forks=50,
        task_durations_normal=tasks,
        use_control_persist=True,
        use_pipelining=True,
    )
    check(
        "forks=50 + ControlPersist + pipelining cuts 50-host 5-task run from 57.85s down to 1.359s (>40x speedup)",
        t_unopt == 57.85 and t_opt == 1.359 and t_unopt > 40 * t_opt,
    )

    # 2. Section 3: linear vs free strategy under a 5x straggler host across multiple waves
    t_linear = estimate_play_wall_clock_seconds(
        num_hosts=20,
        forks=10,
        task_durations_normal=tasks,
        straggler_duration_multiplier=5.0,
        strategy="linear",
    )
    t_free = estimate_play_wall_clock_seconds(
        num_hosts=20,
        forks=10,
        task_durations_normal=tasks,
        straggler_duration_multiplier=5.0,
        strategy="free",
    )
    check(
        "Under a 5x straggler across 2 waves, free strategy (6.718s) beats lockstep linear strategy (10.718s)",
        t_free < t_linear and t_linear == 10.718 and t_free == 6.718,
    )

    # 3. Section 5 & AUR Ch. 18: jsonl_audit callback plugin masks msg when no_log=True
    normal_line = json.loads(
        format_jsonl_audit_event(
            event="ok",
            host="gpu01",
            task="Install driver",
            changed=True,
            rc=0,
            msg="installed 550.90.07",
            no_log=False,
        )
    )
    secret_line = json.loads(
        format_jsonl_audit_event(
            event="ok",
            host="gpu01",
            task="Set DB password",
            changed=True,
            rc=0,
            msg="s3cr3t_password_leaked",
            no_log=True,
        )
    )
    check(
        "jsonl_audit callback records msg on normal tasks and strips msg completely when no_log=True",
        normal_line.get("msg") == "installed 550.90.07" and "msg" not in secret_line,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
