"""Chapter 4.16 model: Network resource-module state engine (`merged`,
`replaced`, `overridden`, `deleted`, `gathered`, `rendered`), LLDP topology vs
cabling-plan verifier, and `ec2_ami_info` latest-AMI selector (`AUR` Ch. 17).

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapters 12, 13, 16, 17, and 21:
  * Ch. 12 ("Managing Windows Hosts"): `winrm` connection, `win_ping`,
    `win_chocolatey`, `win_feature`, `win_reboot`, `win_updates`, `win_stat`.
  * Ch. 13 ("Ansible and Containers"): `docker_image`, `docker_image_info`,
    `docker_login`, `docker_network`, `docker_container` (Ghost + NGINX + MySQL).
  * Ch. 16 ("Creating Images"): Packer `.pkr.hcl` with Ansible provisioner for
    Vagrant/VirtualBox, GCP, Azure, AWS EC2, and Docker (`gcc.pkr.hcl`).
  * Ch. 17 ("Cloud Computing"): `amazon.aws.aws_ec2` dynamic inventory,
    `ec2_ami_info` (`images | sort(attribute='creation_date') | last`),
    `ec2_key`, `ec2_group`, `ec2_vpc_net`, `ec2_vpc_subnet`, `ec2_instance` +
    `add_host`.
  * Ch. 21 ("Network and Security Automation"): `ansible.netcommon.network_cli`,
    `ansible_network_os`, Sunshine IT vs Shadow IT, Zero Trust, `ansible-lockdown`,
    OpenSCAP `oscap xccdf eval --profile ospp`, and `ssh-audit`.
- Christian Adell, Scott Lowe, Matt Oswalt & Jason Edelman, Network
  Programmability and Automation, 2nd ed. (network-programmability-and-automation-
  2nd-edition, NPA), Chapter 12 ("Automation Tools"):
  * Multi-vendor network playbooks (`arista.eos`, `cisco.ios`, `cisco.nxos`,
    `junipernetworks.junos`), resource modules, SNMP compliance checks, and
    comparing Ansible with Python **Nornir + NAPALM** (`InitNornir`,
    `SimpleInventory`, `threaded` runner, `napalm_get`, `napalm_configure`) and
    **Terraform** (`cidrsubnet`).
- volume-10/04-ansible-for-infrastructure-automation.md.
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def apply_vlan_resource_module(
    running_vlans: Mapping[int, str],
    config_vlans: Sequence[Mapping[str, Any]],
    state: str = "merged",
) -> Dict[str, Any]:
    """Model Section 3 network resource module states (`merged`, `replaced`,
    `overridden`, `deleted`, `gathered`, `rendered`) over a switch VLAN table.
    """
    before = dict(running_vlans)
    if state == "gathered":
        return {"changed": False, "before": before, "after": before, "commands": []}

    desired_map = {int(v["vlan_id"]): str(v["name"]) for v in config_vlans}
    after = dict(before)
    commands: List[str] = []

    if state in {"merged", "replaced"}:
        for vid, name in sorted(desired_map.items()):
            if after.get(vid) != name:
                after[vid] = name
                commands.append(f"vlan {vid} / name {name}")
    elif state == "overridden":
        for vid in sorted(set(after.keys()) - set(desired_map.keys())):
            del after[vid]
            commands.append(f"no vlan {vid}")
        for vid, name in sorted(desired_map.items()):
            if after.get(vid) != name:
                after[vid] = name
                commands.append(f"vlan {vid} / name {name}")
    elif state == "deleted":
        target_ids = set(desired_map.keys()) if desired_map else set(after.keys())
        for vid in sorted(target_ids):
            if vid in after:
                del after[vid]
                commands.append(f"no vlan {vid}")
    elif state == "rendered":
        for vid, name in sorted(desired_map.items()):
            commands.append(f"vlan {vid} / name {name}")
        return {"changed": False, "rendered": commands}
    else:
        raise ValueError(f"unsupported state {state!r}")

    return {
        "changed": after != before,
        "before": before,
        "after": after,
        "commands": commands,
    }


def verify_lldp_against_cabling_plan(
    expected_links: Mapping[Tuple[str, str], Tuple[str, str]],
    discovered_lldp: Mapping[Tuple[str, str], Tuple[str, str]],
) -> List[str]:
    """Compare discovered `(local_sw, local_port) -> (remote_sw, remote_port)`
    LLDP neighbors against the intended cabling plan (`fabric.yml`).
    """
    mismatches: List[str] = []
    for loc, exp_rem in sorted(expected_links.items()):
        actual_rem = discovered_lldp.get(loc)
        if actual_rem is None:
            mismatches.append(f"missing LLDP neighbor on {loc[0]}:{loc[1]} (expected {exp_rem[0]}:{exp_rem[1]})")
        elif actual_rem != exp_rem:
            mismatches.append(
                f"cabling mismatch on {loc[0]}:{loc[1]}: got {actual_rem[0]}:{actual_rem[1]}, expected {exp_rem[0]}:{exp_rem[1]}"
            )
    return mismatches


def select_latest_ami(images: Sequence[Mapping[str, str]]) -> Mapping[str, str]:
    """Model AUR Ch. 17 Example 17-9 `ec2_ami_info.images | sort(attribute='creation_date') | last`."""
    if not images:
        raise ValueError("no AMIs matched filter")
    return sorted(images, key=lambda img: img["creation_date"])[-1]
