---
id: "c04-05"
title: "4.5 Ansible inventory: hosts, groups, dynamic inventory and variables"
sidebar_label: "4.5 Ansible inventory: hosts, groups, dynamic inventory and variables"
sidebar_position: 5
description: "Static and dynamic Ansible inventory: INI/YAML formats, groups and nesting, host and group variables, patterns and limits, inventory plugins for clouds and Kubernetes, variable precedence, multi-environment layouts and large-fleet design"
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP / GKE"
---

# 4.5 Ansible inventory: hosts, groups, dynamic inventory and variables

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Control node with ansible-core; 3+ targets or `local` connections; optional GCP/AWS credentials |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

The inventory is the model of your fleet: which machines exist, what role each plays (login, compute, storage, BMC, switch), which rack and fabric rail they sit on, what hardware they carry (GPU count and model, NIC type), and which environment they belong to. Every playbook is only as good as that model. A clean inventory lets you roll a driver update across "all H100 nodes in rack 3 of cluster B" with one `--limit`; a messy one produces wrong NCCL settings on the wrong hardware. For large clusters the inventory should be **generated** from a source of truth (NetBox, a CMDB, cloud APIs, Terraform state, Slurm, or BCM) so it never drifts from reality.

## Prerequisites and outcomes

Needs 4.3 and 4.4. After this chapter you can:

- Write inventories in INI and YAML with groups, children, host and group variables, and ranges.
- Select hosts with patterns, `--limit`, `--list-hosts`; understand `all`, `ungrouped`, implicit `localhost`.
- Organise `group_vars/` and `host_vars/` directories for multiple environments and keep secrets separate.
- Use dynamic inventory plugins (constructed, cloud, Kubernetes, script) and write a simple custom inventory plugin or script; use `add_host` and `group_by` at runtime.
- Reason about variable precedence and merge behaviour, and debug "which value won?".
- Design inventory for GPU clusters: role groups, hardware-trait groups, rack/fabric groups, BMC addressing.

## 1. Inventory formats

### INI

```ini
# inventories/prod/hosts.ini
mgmt01 ansible_host=10.1.0.2

[login]
login01 ansible_host=10.1.1.5

[gpu_h100]
gpu[001:032] ansible_user=automation              # range: gpu001 ... gpu032
gpu033 gpu_count=4                                # a node with a different build

[gpu_a100]
dgx-a100-[01:08].mgmt.example.com

[gpu:children]                                    # group of groups
gpu_h100
gpu_a100

[slurm_controller]
slurmctl01

[cluster:children]
login
gpu
slurm_controller

[gpu:vars]                                        # group variables inline
nvidia_driver_branch=550
ansible_python_interpreter=/usr/bin/python3
```

INI quirks: values on host lines are parsed as Python literals loosely (strings with spaces need quotes); `[group:children]` and `[group:vars]` are special suffixes; ranges support alpha (`[a:f]`) and zero-padded numeric ranges; hosts can appear in several groups.

### YAML

```yaml
# inventories/prod/hosts.yml
all:
  vars:
    ansible_user: automation
    ansible_python_interpreter: /usr/bin/python3
  children:
    login:
      hosts:
        login01: { ansible_host: 10.1.1.5 }
    gpu:
      vars:
        nvidia_driver_branch: 550
      children:
        gpu_h100:
          hosts:
            gpu001: { ansible_host: 10.1.10.1, rack: r01 }
            gpu002: { ansible_host: 10.1.10.2, rack: r01 }
        gpu_a100:
          hosts:
            dgx-a100-01: { ansible_host: 10.1.20.1, rack: r09 }
    slurm_controller:
      hosts:
        slurmctl01:
```

YAML is better for structured variables (lists and dicts as host variables) and for generated output; INI is quicker to type for small static fleets. Many teams keep only **hosts and group membership** in the inventory file and put variables in `group_vars`/`host_vars` directories.

### Special groups, names and connection variables

- `all` contains every host; `ungrouped` contains hosts in no other group; `localhost` is implicit (connection `local`) and not part of `all` unless defined explicitly.
- Host aliases: the name in the inventory (`inventory_hostname`) can differ from the address (`ansible_host`); use stable logical names plus `ansible_host` for addresses.
- Connection variables: `ansible_host`, `ansible_port`, `ansible_user`, `ansible_connection` (`ssh`, `local`, `docker`, `winrm`, `network_cli`, `httpapi`, `kubectl`), `ansible_ssh_private_key_file`, `ansible_ssh_common_args` (ProxyJump), `ansible_become`, `ansible_become_method`, `ansible_become_user`, `ansible_python_interpreter`, `ansible_shell_type`. Passwords belong in Vault or a secrets lookup, never plaintext in inventory.
- Naming rules: group names should use letters, digits and underscores (hyphens produce warnings); avoid names that collide with variables or keywords.

Inspect your model:

```bash
ansible-inventory -i inventories/prod --graph          # tree of groups/hosts
ansible-inventory -i inventories/prod --graph --vars   # include variables
ansible-inventory -i inventories/prod --host gpu001    # fully merged variables for one host
ansible-inventory -i inventories/prod --list --yaml    # whole inventory as data
ansible gpu_h100 -i inventories/prod --list-hosts      # who would a pattern match
```

## 2. Host patterns

| Pattern | Meaning |
|---|---|
| `all` or `*` | Every host |
| `gpu` | Group |
| `gpu:login` | Union |
| `gpu:&rack_r01` | Intersection |
| `gpu:!gpu_a100` | Exclusion |
| `gpu00*` | Wildcard |
| `~gpu0(0[1-9]\|1[0-6])` | Regex |
| `gpu[0:2]` | Group subscript (first three hosts) |
| `gpu001,gpu002` | Explicit list (commas or colons) |
| `@retry.txt` | Hosts listed in a file |

`--limit` (or `-l`) applies an extra pattern on top of the play's `hosts:`. Ordering and sorting: `ansible-playbook --limit @failed_hosts.txt` reruns only failures from a previous run (enable retry files or capture failures). `order: sorted|reverse_sorted|reverse_inventory|shuffle` on a play controls processing order (shuffle spreads risk and load).

## 3. Variables: group_vars, host_vars, and layout

```text
inventories/
├── prod/
│   ├── hosts.yml
│   ├── group_vars/
│   │   ├── all/
│   │   │   ├── main.yml            # non-secret defaults for all hosts in prod
│   │   │   └── vault.yml           # encrypted secrets (4.12)
│   │   ├── gpu/
│   │   │   └── main.yml            # driver, CUDA, NCCL defaults
│   │   ├── gpu_h100.yml            # single-file form also works
│   │   └── slurm_controller.yml
│   └── host_vars/
│       └── gpu033.yml              # one-off exceptions
├── staging/
│   ├── hosts.yml
│   └── group_vars/ ...
└── shared_vars/                    # optional; load with vars_files or include_vars
```

Rules of thumb:

- Ansible loads `group_vars/` and `host_vars/` **adjacent to the inventory file or directory** (and adjacent to the playbook). Files can be `name.yml` or a directory `name/` containing multiple files (merged alphabetically, allowing `main.yml` plus `vault.yml`).
- One inventory directory per environment (`prod`, `staging`, `lab`) with its own variable tree, selected with `-i inventories/prod`; **never** use different branches per environment (4.1).
- Keep variables **close to the group that owns them**: hardware traits on hardware groups, role settings on role groups, cluster-wide settings on `all`. Avoid host-level overrides except for true exceptions; every host_var is a snowflake.
- **Prefix variable names with the role** (`nvidia_driver_branch`, `slurm_cluster_name`) to avoid collisions and to make precedence debuggable.
- Separate secrets into encrypted files or an external secret store (4.12); reference them by name from plain variables (`slurm_db_password: "{{ vault_slurm_db_password }}"`) so grepping shows where secrets are used.
- Use `ansible-inventory --host` to see the merged result; use `debug: var=hostvars[inventory_hostname]` to inspect inside a play.

### Variable precedence (summary)

Ansible has about 22 precedence levels. The practical order (lowest to highest):

1. Command-line **values** such as `-u` (not `-e`) and role **defaults** (`roles/x/defaults/main.yml`: designed to be overridden)
2. Inventory file or script group vars; `group_vars/all`; `group_vars/<group>` (parent groups before child groups; same level alphabetical, then `ansible_group_priority`)
3. Inventory/playbook-adjacent `host_vars`; inventory host vars
4. Host facts and `set_fact`/registered vars (facts rank among play-level vars)
5. Play `vars`, `vars_files`, `vars_prompt`, role `vars/` (**higher than inventory**, so avoid putting overridable settings in role `vars/`)
6. Block and task `vars`, `include_vars`, `set_fact`, registered variables, role parameters
7. **Extra vars `-e`**: always win

Practical consequences: put defaults in role `defaults/`, environment values in `group_vars`, per-host exceptions in `host_vars`, and use `-e` only for one-off overrides and CI parameters. The same variable defined in two sibling groups is a conflict resolved by group order (use `ansible_group_priority` or restructure). By default dictionaries are **replaced, not merged** across layers; set `hash_behaviour = merge` (discouraged, global side effects) or use the `combine` filter explicitly: `{{ base_cfg | combine(env_cfg, recursive=True) }}`.

## 4. Runtime grouping: add_host and group_by

Inventory can change during a run:

```yaml
- name: Build dynamic groups from facts
  hosts: all
  gather_facts: true
  tasks:
    - name: Group by GPU model detected on the host
      ansible.builtin.group_by:
        key: "gpu_model_{{ gpu_model | default('none') | lower | replace(' ', '_') }}"
        parents: gpu_by_model

- name: Act only on H100 nodes
  hosts: gpu_model_h100
  tasks:
    - ansible.builtin.debug: msg="H100 here"

- name: Create a host from provisioning output
  hosts: localhost
  tasks:
    - ansible.builtin.add_host:
        name: "{{ new_vm_ip }}"
        groups: new_nodes
        ansible_user: automation
```

`group_by` is the standard way to branch plays on facts (OS family, GPU model); `add_host` is used right after provisioning a VM so the following play can configure it. Both affect only the current run; `meta: refresh_inventory` re-reads inventory sources mid-run.

## 5. Dynamic inventory

Static files go stale. **Inventory plugins** build inventory from authoritative sources at runtime; you point Ansible at a small YAML config file whose name ends in the plugin's required suffix.

```yaml
# inventories/gcp/gcp.gcp_compute.yml
plugin: google.cloud.gcp_compute
projects: [my-ai-project]
zones: [us-central1-a, us-central1-b]
auth_kind: application                   # use ADC / workload identity, not key files
filters:
  - labels.env = prod
  - status = RUNNING
hostnames: [name]
compose:
  ansible_host: networkInterfaces[0].networkIP
keyed_groups:
  - key: labels.role                     # creates groups role_gpu, role_login ...
    prefix: role
  - key: zone
    prefix: zone
groups:
  gpu_a3: "machineType.endswith('a3-highgpu-8g')"
```

```yaml
# aws_ec2.yml
plugin: amazon.aws.aws_ec2
regions: [us-east-1]
filters: { instance-state-name: running, "tag:Env": prod }
keyed_groups:
  - { key: tags.Role, prefix: role }
  - { key: instance_type, prefix: type }
compose:
  ansible_host: private_ip_address
```

Other common plugins: `kubernetes.core.k8s` (pods/nodes), `community.docker.docker_containers`, `ansible.builtin.constructed` (derive groups/vars from existing hosts' variables), `ansible.builtin.yaml`/`ini`/`script`/`host_list`/`auto`, `netbox.netbox.nb_inventory` (NetBox as source of truth: sites, racks, roles, tags, custom fields), VMware, Azure, OpenStack, Terraform state (`cloud.terraform.terraform_state`), Foreman. Check with `ansible-doc -t inventory -l`.

Key plugin features:

- **`keyed_groups`** build groups from attributes (tags, labels, zone, instance type), **`groups`** from Jinja conditions, **`compose`** computed variables (including `ansible_host`), **`filters`** server-side selection to keep large queries fast, **`cache`** (`cache: true`, `cache_plugin: jsonfile`, `cache_timeout: 300`) to avoid API calls on every command.
- **Combining sources**: `-i inventories/prod` can be a *directory* mixing static files and plugin configs; Ansible merges all of them. A common pattern is static inventory for on-prem plus cloud plugin for burst capacity, and a `constructed` plugin to derive uniform groups (`gpu`, `login`) regardless of source.
- **Authentication**: use workload identity/instance profiles/environment credentials; keep plugin configs free of secrets.

### Script and custom plugins

A legacy **inventory script** is any executable that prints JSON for `--list` and `--host <name>`; it is simple but unmaintained-by-convention. The recommended extension point is an **inventory plugin** (a Python class subclassing `BaseInventoryPlugin`, optionally `Constructable` and `Cacheable`) shipped in a collection.

```python
#!/usr/bin/env python3
# inventory/slurm_inventory.py: minimal dynamic inventory script from `sinfo`
import json, subprocess, sys

def build():
    out = subprocess.run(["sinfo", "-N", "-h", "-o", "%N|%P|%G"], capture_output=True, text=True, check=True).stdout
    inv = {"_meta": {"hostvars": {}}, "all": {"children": ["slurm_nodes"]}, "slurm_nodes": {"hosts": []}}
    for line in out.splitlines():
        node, part, gres = line.split("|")
        part = part.rstrip("*")
        inv["slurm_nodes"]["hosts"].append(node)
        inv.setdefault(f"part_{part}", {"hosts": []})["hosts"].append(node)
        inv["_meta"]["hostvars"][node] = {"slurm_partition": part, "slurm_gres": gres}
    return inv

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        print(json.dumps(build()))
    elif len(sys.argv) > 2 and sys.argv[1] == "--host":
        print(json.dumps({}))                 # hostvars already supplied via _meta (fast path)
    else:
        sys.exit(1)
```

Including `_meta.hostvars` makes Ansible skip the per-host `--host` call (a major performance difference for large inventories). Scripts must be executable and deterministic, return quickly, never print anything else on stdout, and handle API failures with non-zero exit.

### Source of truth for GPU fleets

Large AI clusters keep truth in **NetBox/Nautobot** (devices, interfaces, IPs, racks, cables, tags), in **BCM/Base Command Manager** (node categories and provisioning data), in the **scheduler** (Slurm node definitions), or in **cloud/Terraform state**. Generating Ansible inventory from that source eliminates the "inventory says gpu77 exists but it was RMA'd" problem and enables cabling-aware automation (which rail does each NIC connect to). Treat the inventory source like code: reviewed changes, validation (unique names, required fields), and tests that fail the build if a host lacks a role or rack.

## 6. Designing inventory for GPU clusters

Model three orthogonal axes using groups so playbooks can target any slice:

| Axis | Example groups | Used for |
|---|---|---|
| **Role** | `login`, `gpu`, `slurm_controller`, `slurm_db`, `storage_client`, `monitoring`, `bmc`, `switch_leaf`, `switch_spine` | What software/config the host runs |
| **Hardware trait** | `gpu_h100`, `gpu_a100`, `gpu_gb200`, `nic_cx7`, `nic_bf3`, `cpu_amd`, `cpu_intel` | Driver branch, NCCL tuning, kernel params |
| **Location/topology** | `site_dc1`, `pod_a`, `rack_r07`, `rail_0` ... `rail_7`, `fabric_ib1` | Rolling update batches, topology-aware Slurm config, failure domains |
| **Lifecycle** | `canary`, `maint_window_sat`, `retired` | Safe rollout and exclusions |

Variables then follow the groups: `group_vars/gpu_h100.yml` sets `gpu_clocks`, `nccl_env`, `nvidia_driver_branch`; `group_vars/rack_r07.yml` sets rack-specific values; BMC credentials and addresses live in a `bmc` group using `ansible_connection: local`/`httpapi` or the `redfish` modules with `baseuri: "{{ bmc_address }}"`.

Per-host data to keep: `ansible_host`, `bmc_address`, `rack`, `u_position`, `gpu_count`, `ib_hcas` (list of HCA device names), `mgmt_mac`, `serial_number`, `asset_tag`. Validate with an argument-spec or assert play (`assert: that: [ rack is defined, gpu_count | int > 0 ]`) at the start of every run.

Scale considerations: with thousands of hosts, avoid per-host `--host` script calls (use `_meta`), use `keyed_groups` and caching, split into several inventory sources, raise `forks`, and use `strategy: free`/`serial` deliberately (4.14). Use `ansible_group_priority` and consistent naming to avoid ambiguity when a host belongs to many groups.

## 7. Debugging inventory and variable problems

| Symptom | Likely cause | Check |
|---|---|---|
| "no hosts matched" | Pattern typo, empty group, wrong inventory path, `--limit` too narrow | `--list-hosts`, `ansible-inventory --graph` |
| Variable has the wrong value | Precedence: role `vars/` or `-e` overrides; sibling groups conflict | `ansible-inventory --host`, `debug: var=...`, `-vvv`; search all layers with `grep -r` |
| Variable undefined for some hosts | Defined on a group the host isn't in, loaded from adjacent dir of wrong inventory | `--graph --vars`, check `group_vars` placement beside the inventory in use |
| `group_vars` ignored | File not next to inventory/playbook, wrong name (`gpu.yaml` vs group `gpu-nodes`), invalid group name chars | Name must match group exactly |
| Dict overrides lose keys | Dicts replaced not merged | Use `combine(recursive=True)` |
| Dynamic inventory slow | No `_meta`, no cache, large unfiltered queries | Add cache, filters, `_meta` |
| Plugin not used | Config filename doesn't end with required suffix; plugin not enabled in `ansible.cfg` (`enable_plugins`) | `ansible-inventory -vvv`, `ansible-doc -t inventory <name>` |
| Wrong host connection | `ansible_host` missing/incorrect; bastion args | `ansible -m debug -a var=ansible_host`, `-vvvv` |

## 8. Lab (untested)

1. **Static inventory**: build a lab inventory in INI and again in YAML with `login`, `gpu_h100`, `gpu_a100`, `gpu` (children), `slurm_controller`; use ranges; inspect with `--graph`, `--list`, `--host`.
2. **Patterns**: practise union, intersection, exclusion, regex and subscripts with `--list-hosts`; create a canary group and show a rolling plan that targets `canary` first.
3. **Variables and precedence**: define the same variable at role defaults, `group_vars/all`, a parent group, a child group, `host_vars`, play `vars`, and `-e`; print the value with `debug` at each step and predict the winner before running; reproduce the dict replacement problem and fix with `combine`.
4. **Layout**: restructure into `inventories/prod` and `inventories/staging` with separate `group_vars`; verify that `-i inventories/staging` never sees prod values; add an encrypted `vault.yml` placeholder file.
5. **Runtime groups**: use `group_by` on a fact/variable and `add_host` after "provisioning" a container; confirm later plays see them.
6. **Constructed plugin**: write a `constructed.yml` that creates groups from variables such as `rack` and `gpu_count`; add `compose` to derive `ansible_host`.
7. **Cloud plugin**: configure the GCP or AWS inventory plugin for labelled instances with `keyed_groups`, `filters`, and caching; compare runtime with and without cache.
8. **Custom inventory**: implement the script above against a fake `sinfo` or a JSON file; add `_meta` and measure speed on 5,000 synthetic hosts with and without it; then port to a minimal inventory plugin (optional).
9. **Validation**: write an assert play that fails when any GPU host lacks `rack`, `bmc_address` or `gpu_count`; run it in CI.
10. **NetBox (optional)**: stand up NetBox in Docker, add devices and tags, and drive Ansible with the `nb_inventory` plugin.
11. **Clean up.**

Mark tested only after execution.

## 9. Common mistakes

- Giant flat inventories with variables repeated on every host; host_vars sprawl.
- Variables placed in role `vars/` (hard to override) or abuse of `-e` to "fix" precedence problems.
- Shared secrets in plaintext inventory files; ansible_password in vars.
- Branch-per-environment instead of inventory-directory-per-environment.
- Relying on group order to resolve conflicts silently; hosts belonging to groups with conflicting values.
- Static inventories that no one updates after RMAs and expansions; dynamic inventory with no cache hammering the API.
- Group names with hyphens or spaces; names colliding with variables.
- Expecting `localhost` in `all`; forgetting `connection: local` semantics.
- Forgetting that dictionaries replace rather than merge.
- No validation of required host data, so playbooks fail halfway across the fleet.

## 10. Interview angles

- "How do you structure inventory for multiple environments and a few thousand GPU nodes?" 
- "Explain Ansible variable precedence; where would you put defaults, environment config, per-host overrides, secrets?" 
- "Static versus dynamic inventory; how would you source it from NetBox or a cloud?" 
- "What are `keyed_groups`, `compose`, `constructed`? When `group_by` versus `add_host`?" 
- "How do you debug which value of a variable is used?" 
- "How would you roll a change out to one rack at a time using inventory?" (rack groups, `serial`, `--limit`.)
- "How do you keep secrets out of inventory?"

## 11. Checkpoint questions (35)

1. Two inventory file formats? **A:** INI and YAML.
2. What is `inventory_hostname` vs `ansible_host`? **A:** Logical name vs connection address.
3. How define a group of groups? **A:** `[group:children]` / `children:`.
4. How define a numeric range? **A:** `gpu[001:032]`.
5. Is `localhost` in `all`? **A:** No, unless defined explicitly.
6. What does `ungrouped` mean? **A:** Hosts in no other group.
7. Where are `group_vars` found? **A:** Adjacent to inventory (and playbook).
8. Can `group_vars/gpu` be a directory? **A:** Yes; files merged alphabetically.
9. Which beats role defaults: inventory vars? **A:** Yes.
10. Which beats inventory: role `vars/`? **A:** Yes, role vars are higher.
11. Highest precedence? **A:** `-e` extra vars.
12. Are dicts merged across layers? **A:** No, replaced (use `combine`).
13. How to see merged host vars? **A:** `ansible-inventory --host`.
14. How to list matched hosts? **A:** `--list-hosts`.
15. Pattern for intersection? **A:** `a:&b`.
16. Pattern for exclusion? **A:** `a:!b`.
17. What does `group_by` do? **A:** Creates groups from facts/vars at runtime.
18. What does `add_host` do? **A:** Adds a host to inventory during the run.
19. File name suffix requirement for plugins? **A:** Plugin-specific (e.g. `.gcp_compute.yml`).
20. What do `keyed_groups` do? **A:** Create groups from attribute values.
21. What does `compose` do? **A:** Defines computed host variables.
22. Why use inventory caching? **A:** Avoid repeated API calls.
23. What must a dynamic script print for `--list`? **A:** JSON inventory (with `_meta` for speed).
24. Why `_meta.hostvars`? **A:** Avoids per-host `--host` calls.
25. Recommended extension over scripts? **A:** Inventory plugins.
26. Which tool as source of truth? **A:** NetBox/CMDB/cloud/Terraform state.
27. Three axes for GPU inventory design? **A:** Role, hardware trait, location/topology.
28. Why prefix variable names? **A:** Avoid collisions, ease debugging.
29. Where keep secrets? **A:** Vault-encrypted files or external secret manager.
30. How reduce blast radius with inventory? **A:** Canary/rack groups with limits and `serial`.
31. What is `ansible_group_priority`? **A:** Tie-breaker for same-level group vars.
32. What does `meta: refresh_inventory` do? **A:** Re-reads inventory mid-run.
33. How to restrict a run to failed hosts? **A:** `--limit @file` of failures.
34. Why avoid per-host overrides? **A:** Snowflakes and hard debugging.
35. Why one inventory dir per environment? **A:** Isolation of variables and safe `-i` selection.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Rene Moser and Lorin Hochstein, *Ansible: Up and Running*, 3rd edition (chapter 4 on inventory: hosts, groups, host and group variables, dynamic inventory and plugins, `add_host` and `group_by`).
- Ansible documentation: inventory guide, variable precedence, inventory plugin reference, patterns.
- Examples are the author's constructions.

**Flagged for verification before publishing:** plugin option names for `google.cloud.gcp_compute`, `amazon.aws.aws_ec2`, `netbox.netbox.nb_inventory` against current collection versions, the exact precedence ordering details for the ansible-core version in use, and every code listing; all labs are **untested**.
