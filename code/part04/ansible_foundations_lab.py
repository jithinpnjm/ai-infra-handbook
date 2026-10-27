#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.3: Ansible from zero: what it is, how it works, installation and ad-hoc commands."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_foundations import (
    match_host_pattern,
    resolve_ansible_cfg_path,
    simulate_idempotent_file_module,
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
    # 1. AUR Ch. 2 & Section 4: ansible.cfg 4-level precedence and world-writable CWD guard
    check(
        "ansible.cfg search obeys ANSIBLE_CONFIG > ./ansible.cfg (if not world-writable) > ~/.ansible.cfg > /etc/ansible/ansible.cfg",
        resolve_ansible_cfg_path("/custom/ansible.cfg", True, False, True) == "/custom/ansible.cfg"
        and resolve_ansible_cfg_path(None, True, False, True) == "./ansible.cfg"
        and resolve_ansible_cfg_path(None, True, True, True) == "~/.ansible.cfg"
        and resolve_ansible_cfg_path(None, False, False, False) == "/etc/ansible/ansible.cfg",
    )

    # 2. Section 5 & 6: Host pattern matching (union, intersection, exclusion, regex)
    inv = {
        "gpu": ["gpu01", "gpu02", "gpu03"],
        "login": ["login01"],
        "rack1": ["gpu01", "gpu02", "login01"],
    }
    check(
        "match_host_pattern resolves union (gpu:login), intersection (gpu:&rack1), exclusion (gpu:!gpu02), and regex (~gpu0[12])",
        match_host_pattern(inv, "gpu:login") == ["gpu01", "gpu02", "gpu03", "login01"]
        and match_host_pattern(inv, "gpu:&rack1") == ["gpu01", "gpu02"]
        and match_host_pattern(inv, "gpu:!gpu02") == ["gpu01", "gpu03"]
        and match_host_pattern(inv, "~gpu0[12]") == ["gpu01", "gpu02"],
    )

    # 3. AUR Ch. 1 & Section 6: Idempotent file module & --check dry-run mode
    fs = {}
    dry = simulate_idempotent_file_module(fs, "/etc/skel/.ssh", "root", "root", "0700", check_mode=True)
    run1 = simulate_idempotent_file_module(fs, "/etc/skel/.ssh", "root", "root", "0700", check_mode=False)
    run2 = simulate_idempotent_file_module(fs, "/etc/skel/.ssh", "root", "root", "0700", check_mode=False)
    check(
        "file module reports changed=True without mutating in --check mode, mutates on run 1 (changed=True), and is a no-op on run 2 (changed=False)",
        dry["changed"] is True
        and "/etc/skel/.ssh" not in fs
        or (dry["changed"] is True and run1["changed"] is True and run2["changed"] is False and run2["status"] == "ok"),
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
