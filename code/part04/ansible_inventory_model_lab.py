#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.5: Ansible inventory: hosts, groups, dynamic inventory and variables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_inventory_model import (
    expand_inventory_range,
    parse_vagrant_machine_readable_inventory,
    resolve_variable_precedence,
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
    # 1. Section 1 & AUR Ch. 4: Zero-padded numeric and alphabetic host range expansion
    num_hosts = expand_inventory_range("gpu[001:004]")
    alpha_hosts = expand_inventory_range("web-[a:d].example.com")
    check(
        "expand_inventory_range expands gpu[001:004] with zero padding and web-[a:d].example.com alphabetically",
        num_hosts == ["gpu001", "gpu002", "gpu003", "gpu004"]
        and alpha_hosts == ["web-a.example.com", "web-b.example.com", "web-c.example.com", "web-d.example.com"],
    )

    # 2. Section 3 Variable precedence & dictionary replacement vs combine(recursive=True)
    layers = {
        "role_defaults": {"driver": 535, "nccl": {"debug": "INFO", "ib_hca": "mlx5_0"}},
        "group_vars_all": {"driver": 550},
        "host_vars": {"driver": 555, "nccl": {"debug": "WARN"}},
        "role_vars": {"locked_by_role": True},
        "extra_vars": {"driver": 560},
    }
    replaced = resolve_variable_precedence(layers, recursive_combine=False)
    combined = resolve_variable_precedence(layers, recursive_combine=True)
    check(
        "extra_vars (-e) beats host_vars/group_vars/role_defaults (driver=560), and default dict replacement drops ib_hca unless combined",
        replaced["driver"] == 560
        and replaced["nccl"] == {"debug": "WARN"}
        and combined["nccl"] == {"debug": "WARN", "ib_hca": "mlx5_0"},
    )

    # 3. AUR Ch. 4 Example 4-12 vagrant.py dynamic inventory parser with _meta.hostvars
    mr_lines = [
        "1620831619,vagrant1,state,running",
        "1620831620,vagrant2,state,running",
        "1620831620,vagrant3,state,poweroff",
    ]
    inv = parse_vagrant_machine_readable_inventory(mr_lines, {"vagrant1": 2222, "vagrant2": 2200})
    check(
        "vagrant.py dynamic inventory includes running VMs ('vagrant1', 'vagrant2') and populates _meta.hostvars ports",
        inv["vagrant"]["hosts"] == ["vagrant1", "vagrant2"]
        and inv["_meta"]["hostvars"]["vagrant2"]["ansible_port"] == 2200
        and "vagrant3" not in inv["_meta"]["hostvars"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
