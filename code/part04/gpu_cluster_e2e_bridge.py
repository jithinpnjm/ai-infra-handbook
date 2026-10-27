"""Chapter 4.27 model: End-to-end Terraform `var.nodes` -> IP/port allocator ->
Ansible `hosts.yml` inventory generator (`Section 1.2 & 1.3`), stub `nvidia-smi`
renderer (`Section 2.2`), and end-to-end cluster verification (`Section 3`).

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR).
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR).
- volume-10/04-ansible-for-infrastructure-automation.md,
  volume-10/05-terraform-for-infrastructure-as-code.md, and
  volume-10/11-cicd-for-infrastructure-and-cluster-configuration.md.
"""
from typing import Any, Dict, List, Mapping, Tuple


def generate_ansible_inventory_from_tf_nodes(
    cluster_name: str,
    nodes: Mapping[str, Mapping[str, Any]],
    subnet_prefix: str = "172.28.0.",
) -> Dict[str, Any]:
    """Model Section 1.1, 1.2 & 1.3 Terraform `var.nodes` validation, deterministic
    IP (`172.28.0.10 + i`) and SSH port (`2200 + i`) assignment over `sort(keys(var.nodes))`,
    and `local_file.inventory` (`ansible/inventories/lab/generated/hosts.yml`) structure.
    """
    valid_roles = {"login", "controller", "gpu"}
    for host, spec in nodes.items():
        if spec.get("role") not in valid_roles:
            raise ValueError(f"node {host!r}: role must be login, controller or gpu")

    ordered = sorted(nodes.keys())
    node_outputs: Dict[str, Dict[str, Any]] = {}
    for idx, name in enumerate(ordered):
        spec = nodes[name]
        node_outputs[name] = {
            "role": spec["role"],
            "gpus": int(spec.get("gpus", 0)),
            "address": f"{subnet_prefix}{10 + idx}",
            "ssh_host": "127.0.0.1",
            "ssh_port": 2200 + idx,
        }

    roles_present = sorted({n["role"] for n in node_outputs.values()})
    children: Dict[str, Dict[str, Any]] = {}
    for r in roles_present:
        children[r] = {
            "hosts": {
                name: {
                    "ansible_host": n["ssh_host"],
                    "ansible_port": n["ssh_port"],
                    "node_ip": n["address"],
                    "gpu_count": n["gpus"],
                }
                for name, n in sorted(node_outputs.items())
                if n["role"] == r
            }
        }

    return {
        "all": {
            "vars": {
                "ansible_user": "automation",
                "ansible_python_interpreter": "/usr/bin/python3",
                "ansible_ssh_common_args": "-o StrictHostKeyChecking=accept-new",
                "cluster_name": cluster_name,
            },
            "children": children,
        }
    }


def render_stub_nvidia_smi_list(inventory_hostname: str, gpu_count: int) -> List[str]:
    """Model Section 2.2 `roles/gpu_stub/templates/nvidia-smi.j2` `-L` output."""
    return [
        f"GPU {i}: NVIDIA H100 80GB HBM3 (UUID: GPU-stub-{inventory_hostname}-{i})"
        for i in range(gpu_count)
    ]


def verify_cluster_end_to_end(
    inventory: Mapping[str, Any],
    chrony_offsets_sec: Mapping[str, float],
    nvidia_smi_lines_by_host: Mapping[str, List[str]],
    prometheus_targets_up: Mapping[str, bool],
    slurm_idle_gpu_nodes: set[str],
) -> Tuple[bool, List[str]]:
    """Model Part 3 `playbooks/verify.yml` end-to-end checks."""
    failures: List[str] = []
    children = inventory["all"]["children"]

    all_hosts: Dict[str, Mapping[str, Any]] = {}
    for group_data in children.values():
        for h, hvars in group_data["hosts"].items():
            all_hosts[h] = hvars

    for h in sorted(all_hosts.keys()):
        if abs(chrony_offsets_sec.get(h, 999.0)) > 0.050:
            failures.append(f"{h}: chrony offset {chrony_offsets_sec.get(h)}s exceeds 50ms")
        if not prometheus_targets_up.get(h, False):
            failures.append(f"{h}: Prometheus target not UP")

    gpu_hosts = children.get("gpu", {}).get("hosts", {})
    for h, hvars in sorted(gpu_hosts.items()):
        exp = int(hvars["gpu_count"])
        actual = len(nvidia_smi_lines_by_host.get(h, []))
        if actual != exp:
            failures.append(f"{h}: nvidia-smi -L count {actual} != expected {exp}")
        if h not in slurm_idle_gpu_nodes:
            failures.append(f"{h}: not idle in Slurm sinfo")

    return (len(failures) == 0), failures
