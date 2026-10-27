"""Chapter 4.5 model: Ansible INI numeric/alphabetic range expansion (`gpu[001:032]`,
`web-[a:t]`), 7-tier variable precedence resolution & dictionary replacement vs
`combine(recursive=True)`, and dynamic inventory JSON builder with `_meta.hostvars`
(modeling both `slurm_inventory.py` and `AUR` Ch. 4's `vagrant.py` `--list` /
`--host` interface).

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapter 4 ("Inventory: Describing
  Your Servers"):
  * Implicit `localhost`, behavioral inventory parameters (`ansible_host`,
    `ansible_port`, `ansible_user`, `ansible_private_key_file`, `ansible_connection`,
    `ansible_shell_type`, `ansible_python_interpreter`), and why `127.0.0.1:2222`
    + `127.0.0.1:2200` collapses to one host unless distinct aliases (`vagrant1`,
    `vagrant2`, `vagrant3`) are used.
  * Groups, `[group:vars]`, `[group:children]`, `group_vars/` and `host_vars/`
    directories (splitting `group_vars/production/` into `db` and `rabbitmq`),
    and numbered/alphabetic ranges (`web[01:20]`, `web-[a:t]`, "Pets vs Cattle").
  * Dynamic inventory script interface (`vagrant.py --list` parsing
    `vagrant status --machine-readable` and `vagrant.py --host <name>` parsing
    `vagrant ssh-config` with `paramiko.SSHConfig`, plus `_meta.hostvars`
    fast-path), multi-source inventory directories mixing `vagrant.py`,
    `aws_ec2.yml`, `gcp.yml`, `azure_rm.yml`, and `group_by` / `add_host`.
"""
import string
from typing import Any, Dict, List, Mapping, Sequence


def expand_inventory_range(pattern: str) -> List[str]:
    """Expand a single Ansible numeric (`gpu[001:004]`) or alphabetic
    (`web-[a:d].example.com`) range pattern.
    """
    if "[" not in pattern or "]" not in pattern or ":" not in pattern:
        return [pattern]
    prefix, rest = pattern.split("[", 1)
    span, suffix = rest.split("]", 1)
    start_s, end_s = span.split(":", 1)
    if start_s.isdigit() and end_s.isdigit():
        width = len(start_s) if start_s.startswith("0") else 0
        return [
            f"{prefix}{i:0{width}d}{suffix}" if width else f"{prefix}{i}{suffix}"
            for i in range(int(start_s), int(end_s) + 1)
        ]
    if len(start_s) == 1 and len(end_s) == 1 and start_s.isalpha() and end_s.isalpha():
        letters = string.ascii_lowercase if start_s.islower() else string.ascii_uppercase
        i0, i1 = letters.index(start_s), letters.index(end_s)
        return [f"{prefix}{c}{suffix}" for c in letters[i0 : i1 + 1]]
    raise ValueError(f"unsupported range {pattern!r}")


PRECEDENCE_ORDER: Sequence[str] = (
    "role_defaults",
    "group_vars_all",
    "parent_group_vars",
    "child_group_vars",
    "host_vars",
    "play_vars",
    "role_vars",
    "task_vars",
    "set_fact",
    "extra_vars",
)


def resolve_variable_precedence(layers: Mapping[str, Mapping[str, Any]], recursive_combine: bool = False) -> Dict[str, Any]:
    """Resolve effective variables across `PRECEDENCE_ORDER`. By default,
    dictionaries replace earlier dictionaries; when `recursive_combine=True`,
    nested dictionaries merge recursively (like `combine(recursive=True)`).
    """
    effective: Dict[str, Any] = {}
    for layer_name in PRECEDENCE_ORDER:
        layer = layers.get(layer_name, {})
        for k, v in layer.items():
            if recursive_combine and isinstance(effective.get(k), dict) and isinstance(v, dict):
                merged = dict(effective[k])
                merged.update(v)
                effective[k] = merged
            else:
                effective[k] = v
    return effective


def parse_vagrant_machine_readable_inventory(
    machine_readable_lines: Sequence[str],
    ssh_ports: Mapping[str, int],
) -> Dict[str, Any]:
    """Model AUR Ch. 4 Example 4-12 `vagrant.py --list` + `_meta.hostvars`:
    parse `vagrant status --machine-readable` lines (`timestamp,host,key,value`)
    for `key == 'state' and value == 'running'` and attach per-host connection vars.
    """
    hosts: List[str] = []
    hostvars: Dict[str, Dict[str, Any]] = {}
    for line in machine_readable_lines:
        parts = line.split(",")
        if len(parts) >= 4:
            _, host, key, value = parts[:4]
            if key == "state" and value == "running":
                hosts.append(host)
                hostvars[host] = {
                    "ansible_host": "127.0.0.1",
                    "ansible_port": ssh_ports.get(host, 2222),
                    "ansible_user": "vagrant",
                }
    return {
        "vagrant": {"hosts": hosts},
        "_meta": {"hostvars": hostvars},
    }
