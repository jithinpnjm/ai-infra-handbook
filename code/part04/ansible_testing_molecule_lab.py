#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.13: Testing Ansible: ansible-lint, Molecule and CI."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_testing_molecule import (
    check_ansible_lint_rules,
    evaluate_goss_sshd_spec,
    run_molecule_lifecycle,
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
    # 1. Section 2: ansible-lint rule checks (name[missing], fqcn, command-instead-of-module, no-changed-when, risky-shell-pipe, package-latest)
    bad_shell = {"shell": "apt-get update | tee /tmp/log"}
    v_shell = check_ansible_lint_rules(bad_shell)
    bad_pkg = {"name": "Install chrony", "ansible.builtin.apt": {"name": "chrony", "state": "latest"}}
    v_pkg = check_ansible_lint_rules(bad_pkg)
    clean_task = {
        "name": "Install chrony",
        "ansible.builtin.apt": {"name": "chrony", "state": "present"},
    }
    check(
        "check_ansible_lint_rules flags missing name, short module name, command-instead-of-module, no-changed-when, risky-shell-pipe, and package-latest",
        set(v_shell)
        == {"name[missing]", "fqcn[action-core]", "command-instead-of-module", "no-changed-when", "risky-shell-pipe"}
        and v_pkg == ["package-latest"]
        and check_ansible_lint_rules(clean_task) == [],
    )

    # 2. Section 4: Molecule lifecycle (converge -> idempotence -> side_effect drift -> repair -> verify -> destroy)
    def converge(state):
        changes = 0
        if state.get("swappiness") != 1:
            state["swappiness"] = 1
            changes += 1
        if not state.get("sysctl_conf"):
            state["sysctl_conf"] = "vm.swappiness = 1\n"
            changes += 1
        return changes

    def side_effect(state):
        # Simulate drift: delete config file
        state.pop("sysctl_conf", None)

    def verify(state):
        return state.get("swappiness") == 1 and "vm.swappiness" in state.get("sysctl_conf", "")

    mol = run_molecule_lifecycle(converge, side_effect, verify)
    check(
        "Molecule lifecycle converges (2 changes), passes idempotence (0 changes), repairs side_effect drift, and verifies state",
        mol["changed_run1"] == 2
        and mol["changed_run2"] == 0
        and mol["idempotent"] is True
        and mol["repaired_drift"] is True
        and mol["verified"] is True
        and mol["destroyed"] is True,
    )

    # 3. AUR Ch. 14 Example 14-7: Goss test_sshd.yml verifier
    sshd_host = {
        "file_ed25519_pub_mode": "0644",
        "file_ed25519_pub_content": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5...",
        "port_tcp_22_listening": True,
        "service_sshd_enabled": True,
        "service_sshd_running": True,
        "user_sshd_exists": True,
    }
    ok_cnt, total_cnt = evaluate_goss_sshd_spec(sshd_host)
    check(
        "Goss sshd verifier passes 6/6 checks (ed25519 0644 key, tcp:22 listening, sshd service enabled/running, sshd user)",
        (ok_cnt, total_cnt) == (6, 6),
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
