---
id: "c04-07"
title: "4.7 Ansible variables, facts, templates and filters"
sidebar_label: "4.7 Ansible variables, facts, templates and filters"
sidebar_position: 7
description: "Defining and using Ansible variables, registered results, facts and custom facts, magic variables, lookups, filters and templates for generating configuration, with worked GPU-cluster examples and precedence debugging"
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP / GKE"
---

# 4.7 Ansible variables, facts, templates and filters

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | ansible-core; 2 to 3 Linux targets; (a GPU host helps for the custom-fact examples) |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

One playbook has to configure heterogeneous machines: nodes with 8 or 4 GPUs, H100 or A100, ConnectX-7 or BlueField NICs, in different racks with different management subnets. The way you do that without writing a playbook per machine type is data: variables that describe intent, **facts** that describe what each host actually is, and **templates** that turn data into Slurm, NCCL, chrony, netplan or Prometheus configuration. Understanding where values come from (and which one wins) is the difference between a playbook that is correct on 1,000 nodes and one that is correct on your laptop.

## Prerequisites and outcomes

Needs 4.4 to 4.6. After this chapter you can:

- Define variables at the right layer (play, vars files, inventory, role defaults, extra vars) and read them safely with defaults, asserts and type conversion.
- Capture and use task results (`register`), `set_fact`, `include_vars`, `vars_prompt`, and understand variable scoping and lifetime.
- Use facts (`ansible_facts`), gather subsets, cache facts, write custom local facts (`facts.d`), and use magic variables (`hostvars`, `groups`, `group_names`, `inventory_hostname`, `play_hosts`).
- Use lookups (`env`, `file`, `template`, `pipe`, `url`, `password`, `vault`, `community.hashi_vault.hashi_vault`) and understand their execution location.
- Write templates with loops and filters to generate real configurations, and validate them.
- Debug variable and template problems quickly.

## 1. Defining variables

### Where and how

```yaml
- hosts: gpu
  vars:                              # play-level
    nvidia_driver_branch: 550
    nccl_env:
      debug: WARN
      ib_hca: "mlx5_0,mlx5_1"
  vars_files:
    - vars/common.yml
    - "vars/{{ ansible_facts['os_family'] | lower }}.yml"    # OS-specific variables chosen at runtime
  vars_prompt:                        # interactive; avoid in automation
    - name: reason
      prompt: "Maintenance reason"
      private: false
  tasks:
    - name: Use a variable
      ansible.builtin.debug:
        msg: "Driver branch {{ nvidia_driver_branch }}"
      vars:                           # task-level
        extra: 1
```

Other sources: inventory variables and `group_vars`/`host_vars` (4.5), role `defaults/` and `vars/` (4.11), `-e`/`--extra-vars` (`-e key=value`, `-e '{"k": [1,2]}'`, `-e @file.yml`), `set_fact`, `register`, `include_vars` (loads a file or directory at runtime into the host's variables), `lookup` results, and environment variables via `lookup('env', ...)`.

### Naming and types

- Names: letters, digits, underscores; must not start with a digit; avoid Python keywords and Ansible reserved names (`environment`, `name`, `hosts`, `tasks`, `connection`, `port`...). Prefix with the role or component (`slurm_`, `nvidia_`).
- Types follow YAML: strings, ints, floats, booleans, lists, dicts. Remember quoting rules (4.4): `nvidia_driver_branch: 550` is an int; `"550.90.07"` must be a string; `ansible_check_mode` and similar are booleans.
- Access: `{{ nccl_env.debug }}`, `{{ nccl_env['ib_hca'] }}`, `{{ list[0] }}`; use brackets when a key contains hyphens or conflicts with a dict method (`items`, `keys`, `values`).
- **Always provide a default or assertion for optional values:** `{{ optional_var | default('x') }}`, `{{ must_exist | mandatory }}`, or an `assert` at the top of a play/role (`that: [ rack is defined, gpu_count | int > 0 ]`) so failures are early and legible. Roles should validate inputs with an **argument spec** (`meta/argument_specs.yml`, 4.11).
- Type conversion: `| int`, `| float`, `| bool`, `| string`, `| list`; booleans in strings (`"yes"`, `"True"`) need `| bool`. Do not compare booleans to strings.

### Scope and lifetime

- Play/task `vars` are scoped to where they are defined. Inventory/group/host variables are per host for the whole run. `set_fact` and `register` create **host-scoped** variables that persist for the rest of the play run (and, with `cacheable: true` and fact caching, across runs).
- `set_fact` has the precedence of a task-level fact; registered variables behave similarly. They are set per host: a task with `run_once` sets the variable only on the host that ran it unless you distribute it (`delegate_facts` or `hostvars` iteration).
- `include_vars` loads variables at runtime (precedence above play vars); `vars_files` loads at play start.
- Variable names are not scoped by roles by default: variables set in one role are visible to later roles and tasks (a reason for prefixes).
- Because values are rendered lazily, a variable defined in terms of another (`b: "{{ a }}-x"`) is templated at the point of use, so you can define derived values in `group_vars` that reflect later overrides: powerful but can create recursion (`x: "{{ x }}"` errors).

## 2. Registered results and set_fact

```yaml
- name: Query driver version
  ansible.builtin.command: nvidia-smi --query-gpu=driver_version --format=csv,noheader
  register: drv
  changed_when: false

- name: Keep a clean value
  ansible.builtin.set_fact:
    current_driver: "{{ drv.stdout_lines[0] | trim }}"

- ansible.builtin.debug:
    var: drv                             # show the whole structure: rc, stdout, stdout_lines, stderr, changed, failed, start, end, delta, cmd
```

A registered variable always exists even if the task was skipped (with `skipped: true`), so test `drv is not skipped` / `drv is defined and drv.rc == 0` before use. Looped tasks register a `results` list (one entry per item). Use `failed_when`/`changed_when` expressions instead of ad-hoc post-processing.

`set_fact` guidelines: derive values once and reuse; do not use `set_fact` to emulate programming loops (use filters); mark expensive computed facts `cacheable: true` if you will reuse them across runs; avoid turning `set_fact` into hidden global state.

## 3. Facts

**Facts** are variables Ansible discovers about each host. The `setup` module (run by `gather_facts: true`) returns hundreds: distribution, kernel, CPU count, memory, mounts, network interfaces and addresses, DMI info, environment, date/time, SELinux, user, Python.

```bash
ansible gpu001 -m ansible.builtin.setup | less
ansible gpu001 -m ansible.builtin.setup -a 'filter=ansible_default_ipv4'
ansible gpu001 -m ansible.builtin.setup -a 'gather_subset=!all,!min,network,hardware'
```

Using facts:

```yaml
- name: Show key facts
  ansible.builtin.debug:
    msg: >-
      {{ inventory_hostname }}: {{ ansible_facts['distribution'] }} {{ ansible_facts['distribution_version'] }},
      kernel {{ ansible_facts['kernel'] }}, {{ ansible_facts['processor_vcpus'] }} vCPUs,
      {{ (ansible_facts['memtotal_mb'] / 1024) | round(1) }} GiB RAM,
      primary IP {{ ansible_facts['default_ipv4']['address'] }}
```

- The injected short names (`ansible_distribution`) are being de-emphasised: prefer `ansible_facts['distribution']` (the `ansible_facts` dict), enabled consistently and avoiding pollution of the variable namespace (`inject_facts_as_vars` setting).
- **Selecting facts**: `gather_subset` (`min`, `hardware`, `network`, `virtual`, `all`, negation with `!`), `gather_timeout`, `filter` in `setup`. Fact gathering costs seconds per host; for large fleets use `gathering = smart` with a cache (`fact_caching = jsonfile`/`redis`/`memcached`), or `gather_facts: false` and call `setup` with a small subset only where needed. `package_facts`, `service_facts`, `mount_facts` and `ansible.builtin.getent` gather additional state on demand.
- **Distribution branching**: `when: ansible_facts['os_family'] == 'Debian'`, `ansible_facts['distribution_major_version'] is version('9', '>=')`.
- **Hardware branching**: derive GPU data from probes (`nvidia-smi -L`, `lspci -d 10de:`, DCGM), not from `setup` alone; wrap them in a role that publishes facts like `gpu_count`, `gpu_model`, `nvlink_present`, `ib_hcas` for later plays and templates.

### Custom (local) facts

Any executable or `.fact` file in `/etc/ansible/facts.d/` on the target (INI or JSON, or an executable printing JSON) appears under `ansible_local.<name>` after fact gathering. This is the supported way for hosts to **declare their own attributes** (rack, role, hardware class) that persist independent of the control node.

```ini
# /etc/ansible/facts.d/site.fact
[location]
rack=r07
rail=3
```

```yaml
- name: Publish local fact
  ansible.builtin.copy:
    dest: /etc/ansible/facts.d/gpu.fact
    mode: "0755"
    content: |
      #!/bin/sh
      n=$(nvidia-smi -L 2>/dev/null | wc -l)
      echo "{\"count\": $n}"
- ansible.builtin.setup: { filter: ansible_local }
- ansible.builtin.debug: { msg: "{{ ansible_local.gpu.count }} GPUs on {{ inventory_hostname }}" }
```

### Magic variables

| Variable | Meaning |
|---|---|
| `inventory_hostname`, `inventory_hostname_short` | The host's name in inventory |
| `ansible_host`, `ansible_user`... | Connection variables |
| `groups` | Dict of group name to host list (`groups['gpu']`) |
| `group_names` | Groups the current host belongs to |
| `hostvars` | Dict of host to all of that host's variables and facts (`hostvars['slurmctl01']['ansible_default_ipv4']['address']`); only includes hosts whose facts were gathered earlier in the run for fact values |
| `play_hosts` / `ansible_play_hosts`, `ansible_play_batch` | Hosts in the current play / current serial batch |
| `ansible_play_name`, `ansible_check_mode`, `ansible_diff_mode`, `ansible_run_tags`, `ansible_limit` | Run metadata |
| `playbook_dir`, `role_path`, `inventory_dir` | Paths |
| `omit` | Special placeholder to drop a parameter |
| `ansible_version`, `ansible_python` | Controller details |

Cross-host data (e.g., all node addresses into `/etc/hosts` or Slurm config) uses `hostvars` and `groups`; the required facts must have been gathered for those hosts in this run (a prior play with `gather_facts`, or cached facts). A frequent bug: a play limited to one host templates a cluster-wide file using `hostvars` of hosts whose facts were never gathered (empty values). Gather facts for the whole group first (`- hosts: cluster / gather_facts: true / tasks: []`) or cache them.

## 4. Lookups

Lookups fetch data from outside the playbook **on the control node**, at templating time.

| Lookup | Use |
|---|---|
| `env` | `lookup('env', 'HOME')`; control-node environment |
| `file` | Read a local file's content (e.g., an SSH public key) |
| `template` | Render a local template to a string |
| `pipe` | Run a local command, return stdout (use sparingly; side effects on every evaluation) |
| `url` | Fetch a URL on the control node |
| `password` | Generate/persist a random password in a local file; `lookup('password', 'creds/db chars=ascii_letters,digits length=24')` |
| `community.hashi_vault.hashi_vault` | Read secrets from Vault |
| `ansible.builtin.vars` / `varnames` | Look up variables by name |
| `ansible.builtin.dict`, `items`, `subelements`, `together`, `nested`/`product`, `cartesian` | Build loops over structures |
| `ansible.builtin.first_found` | Pick the first existing file from a list (OS-specific vars) |
| `ansible.builtin.ini`, `csvfile`, `community.general.dig` (DNS), `community.general.random_pet` | Misc data sources |

`lookup()` returns a string (comma-joined) by default; `query()` (alias `q()`) always returns a list: prefer `query` for loops. Lookups run per evaluation: avoid expensive lookups inside loops, and remember they execute where Ansible runs, not on the targets (for target-side data use modules and `register`). `with_<lookup>:` loops are the legacy form of `loop:` plus lookup.

## 5. Loops over data

```yaml
- name: Create service accounts
  ansible.builtin.user:
    name: "{{ item.name }}"
    uid: "{{ item.uid }}"
    groups: "{{ item.groups | default([]) }}"
    shell: /bin/bash
  loop:
    - { name: slurm, uid: 990, groups: [] }
    - { name: munge, uid: 991 }
  loop_control:
    label: "{{ item.name }}"             # shorter output
    pause: 0
    index_var: idx

- name: Per-key iteration over a dict
  ansible.builtin.sysctl:
    name: "{{ item.key }}"
    value: "{{ item.value }}"
  loop: "{{ sysctl_settings | dict2items }}"

- name: Nested data
  ansible.builtin.debug:
    msg: "{{ item.0.name }} -> {{ item.1 }}"
  loop: "{{ users | subelements('keys') }}"
```

Use `loop` with filters (`dict2items`, `subelements`, `product`, `zip`, `flatten`, `batch`) in preference to hand-written logic; `until`/`retries` handle polling; avoid loops over hundreds of items when a single module call can take a list (`package: name: [a, b, c]` is one transaction, much faster than a loop).

## 6. Filters for configuration generation

Beyond Jinja2's builtins (4.4), Ansible provides filters you will use constantly:

| Need | Filter |
|---|---|
| Dict merge (recursive) | `base \| combine(override, recursive=True)` |
| List ↔ dict | `dict2items`, `items2dict`, `zip`, `zip_longest`, `product`, `permutations` |
| Set operations | `union`, `intersect`, `difference`, `symmetric_difference`, `unique` |
| Flatten/shape | `flatten`, `community.general.json_query` (JMESPath queries) |
| Regex | `regex_search`, `regex_findall`, `regex_replace('^(.*)\\.example\\.com$', '\\1')` |
| Paths | `basename`, `dirname`, `splitext` |
| Version | `is version('2.0', '>=')`, `ansible.builtin.version` |
| Hash/crypt | `hash('sha256')`, `password_hash('sha512', salt)`, `b64encode` |
| Serialise | `to_json`, `to_nice_json`, `to_yaml`, `to_nice_yaml`, `from_json`, `from_yaml` |
| IP/network | `ansible.utils.ipaddr`, `ipsubnet`, `ipmath`, `next_nth_usable`, `ansible.utils.cidr_merge`, `hwaddr` (needs `netaddr`) |
| Defaulting | `default`, `default(omit)`, `mandatory`, `ternary('a','b')` |
| Misc | `random`, `shuffle`, `human_readable`, `human_to_bytes`, `quote`, `comment`, `expanduser` |

Examples:

```jinja
{{ gpu_nodes | map('extract', hostvars, 'ansible_host') | list }}            {# list of addresses #}
{{ groups['gpu'] | map('extract', hostvars, 'rack') | unique | sort }}        {# racks in use #}
{{ (ansible_facts['memtotal_mb'] * 0.9) | int }}                              {# Slurm RealMemory ~90% #}
{{ base_cfg | combine({'log_level': 'debug'}, recursive=True) }}
{{ '10.1.0.0/24' | ansible.utils.ipaddr('10') }}                              {# 10th address: 10.1.0.10/24 #}
{{ (item.size | human_to_bytes) // (1024**3) }}                               {# GiB #}
{{ is_prod | ternary('warn', 'debug') }}
```

`extract` is an essential filter for projecting a hostvar across many hosts.

## 7. Templates in practice

Use the `ansible.builtin.template` module to render `.j2` files from the role's `templates/` directory (or any path):

```yaml
- name: Render slurm.conf
  ansible.builtin.template:
    src: slurm.conf.j2
    dest: /etc/slurm/slurm.conf
    owner: slurm
    group: slurm
    mode: "0644"
    backup: true                          # keep a timestamped copy when changed
    validate: "slurmd -f %s -C"           # example: validate before replacing (check the tool's actual option support)
  notify: Reload slurmctld
```

### Example 1: /etc/hosts for the cluster

```jinja
# {{ ansible_managed }}
127.0.0.1 localhost
{% for h in groups['cluster'] | sort %}
{{ hostvars[h]['ansible_host'] }} {{ h }}.{{ cluster_domain }} {{ h }}
{% endfor %}
```

### Example 2: Slurm node and GRES configuration derived from data

```jinja
# {{ ansible_managed }}
ClusterName={{ slurm_cluster_name }}
SlurmctldHost={{ groups['slurm_controller'][0] }}
{% for h in groups['gpu'] | sort %}
{%   set v = hostvars[h] %}
NodeName={{ h }} NodeAddr={{ v.ansible_host }} CPUs={{ v.ansible_facts.processor_vcpus }} Boards=1 SocketsPerBoard={{ v.sockets | default(2) }} CoresPerSocket={{ v.cores_per_socket | default(48) }} ThreadsPerCore=1 RealMemory={{ (v.ansible_facts.memtotal_mb * 0.95) | int }} Gres=gpu:{{ v.gpu_model | default('h100') }}:{{ v.gpu_count | default(8) }} State=UNKNOWN
{% endfor %}
PartitionName=gpu Nodes={{ groups['gpu'] | sort | join(',') }} Default=YES MaxTime=INFINITE State=UP
```

(Compress ranges with Slurm's hostlist syntax such as `gpu[001-032]` for large clusters, via a custom filter or a pre-computed variable.)

### Example 3: Prometheus file_sd targets

```jinja
{# rendered to /etc/prometheus/targets/gpu.json on the monitoring host #}
{{ [{'targets': groups['gpu'] | map('extract', hostvars, 'ansible_host') | map('regex_replace', '$', ':9400') | list,
     'labels': {'job': 'dcgm', 'cluster': cluster_name}}] | to_nice_json }}
```

### Example 4: YAML output from data

Render complex YAML with `to_nice_yaml` rather than hand-indenting: `{{ k8s_values | to_nice_yaml(indent=2) | indent(4) }}`. Validate the result (`yamllint`, `kubeconform`).

### Good template practice

- Keep logic simple; precompute data with `set_fact` or filters before the template; put long expressions in variables.
- Always render with `--check --diff` first; use `validate:` for configs with a syntax checker (`nginx -t -c %s`, `visudo -cf %s`, `named-checkconf %s`).
- Include `{{ ansible_managed }}` so humans know not to edit the generated file.
- Avoid volatile values; sort lists and dict keys (`| sort`, `dictsort`) so renders are deterministic and do not flap handlers.
- Preserve ownership and modes; for secrets set `0600`, `no_log: true`, `diff: false`.
- Keep a template test: render with fixtures in CI and compare to a golden file (3.9).

## 8. Variable precedence debugging toolkit

```bash
ansible-inventory -i inventories/prod --host gpu001 --yaml          # merged inventory-level vars
ansible gpu001 -i inventories/prod -m ansible.builtin.debug -a 'var=nvidia_driver_branch'
ansible-playbook site.yml -l gpu001 -e '' -vvv --tags never --list-tasks   # check what is loaded (with -vvv shows vars files)
grep -rn "nvidia_driver_branch" inventories roles playbooks            # find every definition
```

Inside a play: `debug: var=vars['nvidia_driver_branch']`, `debug: msg="{{ hostvars[inventory_hostname] | dict2items | selectattr('key','match','^nvidia_') | list }}"`. Remember the order summarised in 4.5; the most common surprises are role `vars/` overriding inventory, `-e` overriding everything, `set_fact` persisting for later plays, dictionary replacement instead of merge, and two sibling groups defining the same name.

## 9. Security of variables and templates

- Secrets: Vault-encrypt files or fetch from a secret manager at runtime (4.12); set `no_log: true` on tasks handling them; remember that registered results and `-vvv` output can leak them; `diff: false` for rendered secret files.
- `lookup('pipe')` and `shell` with interpolated variables are injection vectors; quote with `| quote`.
- Facts and registered output from targets are **untrusted data** (a compromised host can return anything); Ansible marks some values unsafe to avoid re-templating; do not strip that marking.
- Beware templating strings that came from untrusted users (template injection) and avoid `!unsafe` removal.

## 10. Lab (untested)

1. **Variable layers**: define one variable in role defaults, `group_vars/all`, `group_vars/gpu`, `host_vars`, play vars, `set_fact` and `-e`; predict, run, and record the winner at each stage; place a dict across two layers and use `combine`.
2. **Register and conditions**: capture `nvidia-smi` output (or a fake script) with `register`; branch on `rc`, `stdout`, `stdout_lines`; show behaviour of a skipped registered task and of looped `results`.
3. **Facts**: dump `setup`; filter subsets; compare run time with and without `gather_facts`, with `gather_subset=min`, and with a JSON file cache.
4. **Custom facts**: deploy `site.fact` and a script fact; read `ansible_local` in the next task; show that facts persist on the host.
5. **Magic variables**: render a cluster-wide `/etc/hosts` with `hostvars`/`groups`; reproduce the "facts not gathered" bug by limiting the play to one host, then fix with a gather play or cache.
6. **Lookups**: use `env`, `file`, `password` (persisted), `first_found` for OS-specific vars; compare `lookup` and `query` returns in a loop.
7. **Loops and filters**: create users from a list of dicts; generate sysctls from a dict; use `subelements`, `product`, `batch`; build a list of GPU node IPs with `map('extract', hostvars, ...)`.
8. **Templates**: write the hosts, Slurm and Prometheus targets templates; make the output deterministic; use `validate:`; show `--diff` and handler behaviour when only ordering changes (then sort to fix).
9. **Types and quoting**: reproduce a boolean-as-string bug and an unquoted `{{` YAML error; fix with `| bool` and quoting.
10. **Argument validation**: add an `assert` and, for a role, an `argument_specs.yml`; verify the failure message for a missing variable.
11. **Debug drill**: have a colleague (or yourself) plant a conflicting variable in three layers; find it with the toolkit in under five minutes.
12. **Clean up.**

Mark tested only after execution.

## 11. Common mistakes

- Using variables without defaults or validation; discovering missing values mid-fleet.
- Putting overridable settings in role `vars/` or using `-e` as the normal way to configure.
- Treating `set_fact` as global assignment; forgetting host scope and `run_once` behaviour.
- Cross-host templates relying on `hostvars` facts that were never gathered.
- Gathering all facts everywhere on huge fleets; or disabling facts and then using `ansible_*` variables.
- Using the old injected fact names inconsistently; mixing `ansible_distribution` and `ansible_facts[...]`.
- Non-deterministic template output (unsorted dicts/sets, timestamps) causing handler restarts.
- Booleans as strings; version strings parsed as floats.
- Complex Jinja in YAML where a small module, filter plugin or precomputed variable would be clearer.
- Secrets in `debug` output or registered variables printed at `-v`.

## 12. Interview angles

- "Where do you define variables and what wins?" (precedence summary; role defaults, group_vars, host_vars, extra vars.)
- "What are facts? How do you speed up fact gathering? How would you add custom facts?" 
- "How do you generate per-node configuration (Slurm, /etc/hosts, Prometheus targets) from inventory?" 
- "What is `hostvars` and when does it break?" 
- "`register` vs `set_fact`; scope and lifetime?" 
- "`lookup` vs `query`; where do lookups run?" 
- "How do you merge dictionaries from several layers?" (`combine`.)
- "How do you validate a rendered configuration before it replaces the live one?" 
- "How do you keep secrets out of logs and diffs?" 

## 13. Checkpoint questions (35)

1. What do facts describe? **A:** Discovered properties of each host.
2. Which module gathers facts? **A:** `setup`.
3. How to restrict fact gathering? **A:** `gather_subset`, `filter`, or `gather_facts: false`.
4. Preferred fact access style? **A:** `ansible_facts['key']`.
5. How to cache facts? **A:** `fact_caching` (jsonfile/redis) with `gathering = smart`.
6. Where do custom facts live? **A:** `/etc/ansible/facts.d/` on the target.
7. Where do custom facts appear? **A:** Under `ansible_local`.
8. What does `register` store? **A:** The module's return dictionary.
9. What does `set_fact` create? **A:** A host-scoped variable for the rest of the run.
10. What is `hostvars`? **A:** Variables/facts of all hosts, keyed by host.
11. What is `group_names`? **A:** Groups the current host belongs to.
12. What does `omit` do? **A:** Drops an optional module parameter.
13. `lookup` runs where? **A:** On the control node.
14. `lookup` vs `query`? **A:** String vs list return.
15. What does `first_found` do? **A:** Picks the first existing file from a list.
16. What does `password` lookup do? **A:** Generates and persists a random password.
17. How merge dicts recursively? **A:** `combine(..., recursive=True)`.
18. How turn dict into list of pairs? **A:** `dict2items`.
19. What does `extract` do? **A:** Maps keys to values in a dict (e.g., hostvars).
20. What does `json_query` use? **A:** JMESPath.
21. How to validate a template's output? **A:** `validate:` on `template`.
22. What is `ansible_managed`? **A:** Marker comment for generated files.
23. How make renders deterministic? **A:** Sort lists/keys, avoid timestamps.
24. Why prefix variable names? **A:** Avoid collisions.
25. What does `mandatory` do? **A:** Fails if variable is undefined.
26. How handle optional booleans in strings? **A:** `| bool`.
27. Loop with labels? **A:** `loop_control: label`.
28. Why pass a list to `package` instead of looping? **A:** One transaction, faster.
29. Which var shows the current serial batch? **A:** `ansible_play_batch`.
30. Which var is true in check mode? **A:** `ansible_check_mode`.
31. How to see merged host vars? **A:** `ansible-inventory --host`.
32. Highest-precedence source? **A:** `-e` extra vars.
33. What does `include_vars` do? **A:** Load variables from files at runtime.
34. Why `no_log` on secret tasks? **A:** Prevent leaking in output.
35. Why treat facts as untrusted? **A:** A compromised host can return anything.

## 14. Sources and review notes

**Written in original words.** Principal sources:

- Rene Moser and Lorin Hochstein, *Ansible: Up and Running*, 3rd edition (chapter 5 on variables and facts; templating and filters in the playbook chapters).
- Ansible documentation: variables, facts, special variables, lookups, filters and tests, templating.
- Examples are the author's constructions.

**Flagged for verification before publishing:** fact names across OS versions, `validate:` support of the Slurm tools shown (verify actual command-line options), filter locations after collection migrations (`ansible.utils`, `community.general`), injected-facts default behaviour in the ansible-core version used, and every code listing; all labs are **untested**.
