#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.10: Debugging Ansible playbooks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_debugging_toolkit import (
    InteractiveTaskDebuggerSession,
    classify_ansible_failure_layer,
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
    # 1. Section 1 & 5: Classify Ansible errors across all 5 diagnostic layers
    check(
        "classify_ansible_failure_layer maps YAML, UNREACHABLE, undefined variable, sudo, and command errors to exact layers",
        classify_ansible_failure_layer("ERROR! Syntax Error while loading YAML: mapping values are not allowed here")
        == "parse_or_syntax"
        and classify_ansible_failure_layer("UNREACHABLE! => Failed to connect to the host via ssh: Host key verification failed")
        == "connection_unreachable"
        and classify_ansible_failure_layer("AnsibleUndefinedVariable: 'dict object' has no attribute 'gpu_count'")
        == "data_or_template"
        and classify_ansible_failure_layer("Missing sudo password")
        == "privilege_or_module"
        and classify_ansible_failure_layer("non-zero return code: nvidia-smi exited 9")
        == "application_command",
    )

    # 2. Section 4 & AUR Ch. 8 Table 8-2: Interactive task debugger (`task_vars[...] = ...`, `update_task`, `redo`)
    dbg = InteractiveTaskDebuggerSession(
        task_name="Install NTP package",
        args_template={"name": "{{ ntp_pkg }}", "state": "present"},
        task_vars={"ntp_pkg": "chrny-typo"},
    )
    initial_status = dbg.redo(valid_packages={"chrony", "ntp"})
    updated_args = dbg.set_var_and_update_task("ntp_pkg", "chrony")
    after_redo = dbg.redo(valid_packages={"chrony", "ntp"})
    check(
        "InteractiveTaskDebuggerSession fails on 'chrny-typo', updates task_vars + update_task to 'chrony', and succeeds on redo",
        initial_status == "failed" and updated_args["name"] == "chrony" and after_redo == "ok",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
