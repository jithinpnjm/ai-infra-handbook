#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.4: YAML and Jinja2 for infrastructure code."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yaml_jinja2_templates import (
    apply_yaml_block_chomping,
    classify_yaml11_unquoted_scalar,
    get_interface_speed,
    render_slurm_nodes_template,
    render_switchport_template,
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
    # 1. Section 1 YAML 1.1 scalar coercion traps (NO, 1.10, 010, 0x1f, 22:30, ~)
    check(
        "YAML 1.1 coerces 'NO'->False, '1.10'->1.1, '010'->8 (octal), '0x1f'->31 (hex), '22:30'->1350 (sexagesimal), and '~'->None",
        classify_yaml11_unquoted_scalar("NO") == ("bool", False)
        and classify_yaml11_unquoted_scalar("1.10") == ("float", 1.1)
        and classify_yaml11_unquoted_scalar("010") == ("int_octal_yaml11", 8)
        and classify_yaml11_unquoted_scalar("0x1f") == ("int_hex", 31)
        and classify_yaml11_unquoted_scalar("22:30") == ("int_sexagesimal_yaml11", 1350)
        and classify_yaml11_unquoted_scalar("~") == ("null", None),
    )

    # 2. Section 1 & AUR Ch. 3 block scalar chomping (|, |-, |+, >, >-)
    lines = ["line1", "line2"]
    check(
        "block scalars preserve newlines in '|' ('line1\\nline2\\n'), strip trailing newline in '|-', keep extra in '|+', and fold in '>-'",
        apply_yaml_block_chomping(lines, "|") == "line1\nline2\n"
        and apply_yaml_block_chomping(lines, "|-") == "line1\nline2"
        and apply_yaml_block_chomping(lines, "|+") == "line1\nline2\n\n"
        and apply_yaml_block_chomping(lines, ">-") == "line1 line2",
    )

    # 3. NPA Ch. 9 switchport Jinja template with trunk/access conditionals, upper|reverse, and get_interface_speed
    ifaces = [
        {"name": "GigabitEthernet0/1", "desc": "uplink port", "uplink": True},
        {"name": "FastEthernet0/2", "desc": "Server port one", "uplink": False, "vlan": 10},
    ]
    rendered_sw = render_switchport_template(ifaces, chain_reverse=True)
    check(
        "NPA Ch. 9 switchport template renders trunk/access modes, upper|reverse ('TROP KNILPU'), and custom speed filter (1000 / 100)",
        "description TROP KNILPU" in rendered_sw
        and "switchport mode trunk" in rendered_sw
        and "speed 1000" in rendered_sw
        and "switchport access vlan 10" in rendered_sw
        and "speed 100" in rendered_sw
        and get_interface_speed("Eth0") == 0,
    )

    # 4. Section 3 Slurm node template rendering and StrictUndefined validation
    nodes = [
        {"name": "gpu02", "addr": "10.0.10.12", "cpus": 128, "mem_mb": 2000000, "gpus": 8},
        {"name": "gpu01", "addr": "10.0.10.11", "cpus": 128, "mem_mb": 2000000},
    ]
    slurm_cfg = render_slurm_nodes_template(nodes)
    undef_raised = False
    try:
        render_slurm_nodes_template([{"name": "gpu03"}])
    except KeyError:
        undef_raised = True
    check(
        "Slurm template sorts nodes, computes 95% RealMemory (1900000), defaults gpus=8, and raises on StrictUndefined missing keys",
        slurm_cfg.splitlines()[0] == "NodeName=gpu01 NodeAddr=10.0.10.11 CPUs=128 RealMemory=1900000 Gres=gpu:8 State=UNKNOWN"
        and "PartitionName=gpu Nodes=gpu01,gpu02" in slurm_cfg
        and undef_raised is True,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
