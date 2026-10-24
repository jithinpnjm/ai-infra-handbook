---
id: "c04-06"
title: "4.6 Ansible playbooks: tasks, modules, idempotency and check mode"
sidebar_label: "4.6 Ansible playbooks: tasks, modules, idempotency and check mode"
sidebar_position: 6
description: "Playbook structure, plays and tasks, the essential module families, idempotency patterns, command/shell guards, check mode and diff, tags, limits, serial, strategies and exit codes for operating fleets safely"
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP / GKE"
---

# 4.6 Ansible playbooks: tasks, modules, idempotency and check mode

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | ansible-core on the control node; 2 to 3 Linux targets (containers with sshd are fine for most modules) |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Playbooks are the unit of operational change on a fleet: install a driver, set kernel parameters, deploy a Slurm configuration, rotate a certificate, drain and patch a node. Written well they are readable runbooks that are safe to run twice, show you the diff before changing anything, and stop at the first sign of trouble. Written badly they are shell scripts in YAML that always report "changed", cannot be dry-run, and break differently on every host. This chapter teaches playbook anatomy, the module families you will use constantly, the mechanics of idempotency, and the operational controls (check mode, diff, tags, limits, serial) that make fleet changes safe.

## Prerequisites and outcomes

Needs 4.3 to 4.5. After this chapter you can:

- Write multi-play playbooks with play keywords (`hosts`, `become`, `gather_facts`, `vars`, `serial`, `strategy`, `any_errors_fatal`, `max_fail_percentage`) and task keywords.
- Choose the right module for packages, services, files, users, kernel parameters, mounts, cron/systemd timers, downloads, archives, Git, and system commands; explain how each achieves idempotency.
- Make `command`/`shell` tasks safe with `creates`, `removes`, `changed_when`, `failed_when`, and guards.
- Use `--check`, `--diff`, `check_mode:`, `diff:` and understand their limits.
- Control execution with tags, `--limit`, `--start-at-task`, `--step`, `serial`, `strategy`, `async`/`poll`, `run_once`, `delegate_to`, `throttle`.
- Read play recaps and exit codes and design CI-friendly runs.

## 1. Playbook anatomy

```yaml
# site.yml
- name: Baseline configuration for all cluster nodes     # play 1
  hosts: cluster
  become: true
  gather_facts: true
  any_errors_fatal: false
  max_fail_percentage: 10
  serial: "20%"                                            # batch rolling execution
  vars:
    ntp_servers: [0.pool.ntp.org, 1.pool.ntp.org]
  pre_tasks:
    - name: Assert supported OS
      ansible.builtin.assert:
        that: ansible_facts['os_family'] in ['Debian', 'RedHat']
        fail_msg: "Unsupported OS {{ ansible_facts['os_family'] }}"
  roles:
    - role: common                                         # roles run after pre_tasks (4.11)
  tasks:
    - name: Install baseline packages
      ansible.builtin.package:
        name: [chrony, rsync, htop, tmux]
        state: present
      tags: [packages]
  post_tasks:
    - name: Record run
      ansible.builtin.copy:
        content: "configured {{ ansible_date_time.iso8601 }} by {{ lookup('env', 'USER') }}\n"
        dest: /etc/ansible-last-run
        mode: "0644"
  handlers:
    - name: Restart chrony
      ansible.builtin.service: { name: chronyd, state: restarted }

- name: Slurm controller only                              # play 2
  hosts: slurm_controller
  become: true
  tasks: [ ... ]
```

Order within a play: `pre_tasks` → handlers flushed → `roles` → `tasks` → handlers flushed → `post_tasks` → handlers. Plays run in file order, each across all its hosts; later plays can use facts gathered earlier. Use multiple plays when different host groups need different steps, or when you want a **gate** (a play that validates the world before the destructive one).

### Task anatomy and common keywords

```yaml
- name: Ensure the DCGM exporter is running            # always name tasks: it is the log and the documentation
  ansible.builtin.systemd_service:                      # FQCN of the module
    name: dcgm-exporter
    state: started
    enabled: true
    daemon_reload: true
  become: true                                          # privilege escalation for this task
  when: "'gpu' in group_names"                          # conditional (Jinja expression, no braces)
  register: dcgm_result                                 # save the module's return dict
  notify: Restart dcgm-exporter                         # trigger a handler if changed
  tags: [monitoring, dcgm]
  retries: 5                                            # with until: retry loops
  delay: 10
  until: dcgm_result is succeeded
  ignore_errors: false
  changed_when: false                                   # override what counts as a change
  failed_when: dcgm_result.rc not in [0, 3]             # override what counts as failure
  delegate_to: localhost                                # run the task elsewhere for this host's context
  run_once: false
  throttle: 5                                           # at most 5 hosts concurrently on this task
  timeout: 120                                          # per-task timeout (seconds)
  no_log: false                                         # true for secrets
  environment: { HTTP_PROXY: "{{ proxy }}" }
  vars: { x: 1 }                                        # task-scoped variables
  check_mode: false                                     # force run (or skip) even in check mode
  diff: true                                            # show diffs for this task
```

Keyword scoping: most keywords can be set at play, block or task level and inherit downward (`become`, `environment`, `tags`, `when`, `vars`, `ignore_errors`...). Read `ansible-doc -t keyword -l`. Task names should read as desired states ("Ensure X is Y"), not actions.

## 2. Idempotency, the heart of playbooks

A module is idempotent when running it again with the same arguments changes nothing. It achieves this by **comparing desired and actual state** (does the package exist? is the file content identical? does the line exist?) before acting. Your job in a playbook is to preserve that property:

- Use the **declarative module** for the thing you are managing (`package`, `service`, `user`, `file`, `template`, `lineinfile`, `sysctl`, `mount`, `cron`, `git`, `get_url`, `unarchive`) rather than `command`/`shell`.
- Express **final state**, not actions (`state: present`/`absent`/`started`/`latest`/`directory`), and avoid toggles.
- For `command`/`shell` use guards: `creates:` (skip if the path exists), `removes:` (skip if the path is missing), a preceding `stat` or check task with `when`, or `changed_when` computed from output.
- Do not use timestamps, random values or `ansible_date_time` in rendered content (the file changes every run, so every run reports `changed` and triggers handlers).
- Prefer `state: present` over `state: latest` for reproducibility, using `latest` only deliberately in a patch play (and pinning versions otherwise: `name: "nvidia-driver-550=550.90.07-1"`).
- Test idempotency: run the playbook twice; the second recap must show `changed=0`. Molecule automates this check (4.13).

```yaml
- name: Create the scratch dir once
  ansible.builtin.command: mkdir -p /scratch
  args: { creates: /scratch }                 # skipped if /scratch exists (still, `file` is better)

- name: Read the current DCGM profiling mode (read-only, never "changed")
  ansible.builtin.command: dcgmi profile --status
  register: prof
  changed_when: false
  failed_when: prof.rc != 0 and 'not supported' not in prof.stderr

- name: Enable MIG only if currently disabled
  ansible.builtin.command: nvidia-smi -i 0 -mig 1
  when: "'Disabled' in mig_state.stdout"
  register: mig_set
  changed_when: "'Enabled' in mig_set.stdout"
```

## 3. Module families you will use daily

Find modules with `ansible-doc -l | grep -i <topic>`, `ansible-doc ansible.builtin.copy` (examples at the end), or the module index per collection. The list below is a practical map.

### Packages and repositories

| Module | Notes |
|---|---|
| `ansible.builtin.package` | Generic; uses the right backend. Package names often differ between distros, so use `when` or vars per OS family |
| `ansible.builtin.apt`, `dnf`/`yum`, `zypper` | Backend-specific: `update_cache`, `cache_valid_time`, `autoremove`, `install_recommends`, `lock_timeout`, `allow_downgrade` |
| `ansible.builtin.apt_repository`, `ansible.builtin.deb822_repository`, `ansible.builtin.yum_repository`, `ansible.builtin.apt_key` (deprecated; use keyrings with `get_url`) | Add NVIDIA CUDA / Docker / Kubernetes repositories securely with signed-by keyrings |
| `ansible.builtin.pip` | Use `virtualenv:` and pinned versions; avoid system Python |
| `ansible.builtin.dpkg_selections`, `ansible.builtin.package_facts` | Hold package versions (e.g. kernel, driver) and inspect installed packages |

```yaml
- name: Hold the NVIDIA driver and kernel to avoid surprise upgrades
  ansible.builtin.dpkg_selections:
    name: "{{ item }}"
    selection: hold
  loop: [nvidia-driver-550, linux-image-generic]
  when: ansible_facts['os_family'] == 'Debian'
```

### Files, templates and content

`ansible.builtin.file` (state: file/directory/link/absent/touch; owner/group/mode; recurse), `copy` (static file or inline `content:`; `backup`, `validate`, `force`, `remote_src`), `template` (Jinja2 rendering, 4.4), `lineinfile` (ensure one line; use `regexp` and `backrefs`; careful, regexes can match multiple lines or none), `blockinfile` (managed block with markers), `replace` (regex over file), `stat` (inspect files), `find`, `fetch` (pull files back), `synchronize` (rsync wrapper), `unarchive`, `get_url` (with `checksum:`), `uri` (call HTTP APIs), `assemble` (concatenate fragments, e.g. `conf.d`), `ini_file` (community.general), `slurp`, `tempfile`.

```yaml
- name: Install sshd hardening drop-in
  ansible.builtin.copy:
    dest: /etc/ssh/sshd_config.d/10-hardening.conf
    content: |
      PermitRootLogin no
      PasswordAuthentication no
    owner: root
    group: root
    mode: "0644"
    validate: "sshd -t -f %s"        # NOTE: validating a drop-in standalone may need the main config; test carefully
  notify: Reload sshd

- name: Download a release with checksum verification
  ansible.builtin.get_url:
    url: "https://example.com/tool-{{ tool_version }}.tar.gz"
    dest: "/opt/dl/tool-{{ tool_version }}.tar.gz"
    checksum: "sha256:{{ tool_sha256 }}"
    mode: "0644"
```

### Users, groups, SSH, sudo

`user`, `group`, `authorized_key` (ansible.posix), `known_hosts`, `ansible.builtin.lineinfile` with `validate: visudo -cf %s` for sudoers or, better, a drop-in file in `/etc/sudoers.d/`. For many users iterate over a data structure.

### Services and boot

`service`, `systemd_service` (daemon_reload, masked, enabled, state), `ansible.builtin.reboot` (reboot and wait; `reboot_timeout`, `test_command`), `wait_for` (port/file/regex), `wait_for_connection`, `ansible.posix.sysctl` (persist kernel parameters with `sysctl_file`, `reload`), `ansible.posix.mount`, `community.general.modprobe` (kernel modules), `community.general.kernel_blacklist`, `community.general.timezone`, `ansible.builtin.hostname`, `ansible.builtin.cron`, `ansible.posix.at`, `community.general.alternatives`, `ansible.posix.firewalld`, `community.general.ufw`, `ansible.posix.seboolean`, `ansible.posix.selinux`.

```yaml
- name: Kernel parameters for training nodes
  ansible.posix.sysctl:
    name: "{{ item.key }}"
    value: "{{ item.value }}"
    sysctl_file: /etc/sysctl.d/90-ai.conf
    state: present
    reload: true
  loop: "{{ sysctl_settings | dict2items }}"
  vars:
    sysctl_settings:
      vm.swappiness: 1
      net.core.rmem_max: 268435456
      net.core.wmem_max: 268435456
      net.ipv4.tcp_congestion_control: bbr
      kernel.numa_balancing: 0
```

### Information, control flow and debugging

`setup`, `gather_facts`, `set_fact`, `debug`, `assert`, `fail`, `meta` (`flush_handlers`, `end_play`, `end_host`, `refresh_inventory`, `clear_facts`), `pause`, `include_tasks`/`import_tasks`, `include_role`/`import_role`, `include_vars`, `add_host`, `group_by`, `wait_for`, `command`, `shell`, `raw`, `script`, `expect`, `async_status`.

### Platform/domain modules relevant to this handbook

Collections: `kubernetes.core` (k8s, helm), `community.docker`, `community.general` (many system and tool modules), `ansible.netcommon`/`cisco.*`/`arista.eos`/`nvidia.nvue`-style network modules (4.16), `community.crypto` (certificates), `community.postgresql`/`mysql`, `amazon.aws`, `google.cloud`, `azure.azcollection`, `community.hashi_vault`, `community.general.redfish_*` (BMC power, boot, firmware, inventory) (Part 7), `ansible.windows`. GPU-specific automation (drivers, Fabric Manager, DCGM, container toolkit) is built from package/service/template/command modules plus NVIDIA roles (4.17).

## 4. command, shell, script, raw: when and how

| Module | Shell features | Use |
|---|---|---|
| `command` | No (no pipes, redirects, `$VAR`, globs) | Default for running an executable; arguments are split safely |
| `shell` | Yes (`/bin/sh -c`) | Pipes, redirects, loops; quote variables with `\| quote` |
| `script` | Runs a local script remotely | Bigger logic that is hard in modules; make idempotent with `creates` |
| `raw` | Raw SSH; no Python needed | Bootstrap Python; network gear |

Guidelines: if a module exists, use it; when you must run commands, **make the task describe its effect on state**: guard with `creates`/`removes`/`when`, set `changed_when` and `failed_when` from the command's actual output/exit code, and never rely on stdout parsing without checking `rc`. Treat `shell` with interpolated variables as an injection risk: `"{{ var | quote }}"`. Example for a read-only probe:

```yaml
- name: Count visible GPUs
  ansible.builtin.shell: nvidia-smi -L | wc -l
  args: { executable: /bin/bash }
  register: gpu_count
  changed_when: false                       # read-only: never reports changed
  failed_when: gpu_count.rc != 0 or (gpu_count.stdout | int) != expected_gpus
  check_mode: false                         # run even under --check (safe, read-only)
```

Pipes hide failures (`set -o pipefail` requires bash: use `executable: /bin/bash` and `set -o pipefail;`), so keep probes simple or split into a module call plus Jinja filters.

## 5. Check mode and diff

`ansible-playbook --check` (`-C`) asks modules to report what they would change without changing it; `--diff` (`-D`) additionally shows before/after content for files and templates. Together they are the fleet's "terraform plan".

```bash
ansible-playbook site.yml --check --diff --limit gpu001
```

Behaviour and limits:

- Most core modules support check mode. `command`/`shell`/`raw` **skip** in check mode unless they have `creates`/`removes`, or you set `check_mode: false` (run anyway; only do this for read-only commands). Modules that do not support it are skipped with a note.
- Tasks that depend on earlier tasks' real effects (installing a package then configuring its file) can fail or mispredict in check mode; mitigate with `when: not ansible_check_mode` or `ignore_errors: "{{ ansible_check_mode }}"` for such tasks, and design playbooks where reads (`stat`, probes) are `check_mode: false`.
- `--diff` can leak secrets in diffs: set `diff: false` on tasks that render secrets.
- Treat check mode as a risk reducer, not a proof; follow with canary application and verification.
- **Drift detection**: scheduled `--check` runs that exit non-zero or report `changed>0` reveal manual changes (4.2). Use `--check --diff` output as evidence in pull requests.

Per-task overrides: `check_mode: true` forces a dry-run for one task even in a real run (useful to preview a risky step); `check_mode: false` forces execution in check mode (probes).

## 6. Controlling execution

### Targeting and iteration

```bash
ansible-playbook site.yml --limit 'gpu_h100:&rack_r01'        # slice of the fleet
ansible-playbook site.yml --tags packages,monitoring          # only tagged tasks
ansible-playbook site.yml --skip-tags slow
ansible-playbook site.yml --start-at-task "Install baseline packages"
ansible-playbook site.yml --step                               # confirm each task interactively
ansible-playbook site.yml --list-tasks --list-tags --list-hosts
ansible-playbook site.yml -e "nvidia_driver_branch=555" -e @extra.yml
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml -f 50 -vv
```

Tags: `tags:` on tasks/blocks/plays/roles/imports; special tags `always` (runs unless `--skip-tags always`) and `never` (runs only if requested). Use a small consistent tag vocabulary (`packages`, `config`, `services`, `firewall`, `monitoring`), because tags are a convenience, not a safety mechanism: tagged partial runs skip dependencies and can leave nodes half-configured.

### Batching, strategies and failure semantics

```yaml
- hosts: gpu
  serial: [1, "10%", "25%"]       # first batch 1 host (canary), then 10%, then 25% for the rest
  max_fail_percentage: 5          # abort the play if >5% of a batch fails
  any_errors_fatal: true          # one failure stops all hosts (use for dangerous steps)
  strategy: linear                # default: each task completes on all batch hosts before the next
  order: shuffle
```

- **`serial`** limits how many hosts are in play at once (integers, percentages or a list that grows): the foundation of rolling upgrades and canaries.
- **`strategy: free`** lets each host run ahead independently (faster for independent tasks; unsuitable when later tasks depend on all hosts finishing); `host_pinned` and `debug` are variations.
- **`throttle: N`** caps concurrency for a specific task (e.g. package-mirror load) regardless of forks.
- **`run_once: true`** executes a task on one host in the batch (with `delegate_to` for specific delegation); combine with `delegate_facts` carefully.
- **`delegate_to`**: run on another host while using the current host's variables (call a load balancer API to drain a node, update DNS, talk to a BMC from a bastion): `delegate_to: localhost` is the common case. Note that with `delegate_to`, connection variables come from the delegated host; `become` may differ.
- **`async` and `poll`**: `async: 3600` + `poll: 0` fires a long task in the background (check later with `async_status`); `poll: 15` waits while polling. Useful for firmware flashes, large package installs and avoiding SSH timeouts.
- **`any_errors_fatal`, `max_fail_percentage`, `ignore_errors`, `ignore_unreachable`, `force_handlers`**: failure policy knobs. By default a failed host is removed from the remaining play; handlers do not run for failed hosts unless `force_handlers: true`.
- **Timeouts**: `timeout:` on tasks, `ansible.cfg` `timeout` (SSH connect), and `async` for long operations; a hung command without a timeout blocks the run.

### Exit codes and recap

`ansible-playbook` exits 0 on success; 1 for generic error; 2 if one or more hosts failed; 3 if one or more hosts were unreachable; 4 for parse errors; 5 for bad or incomplete options; 99 interrupted; 250 unexpected error. In CI treat non-zero as failure; for drift detection parse the recap (`changed=` counts) or use `ANSIBLE_STDOUT_CALLBACK=json`/`ansible.posix.json` for machine-readable output.

```text
PLAY RECAP
gpu001 : ok=12 changed=3 unreachable=0 failed=0 skipped=2 rescued=0 ignored=0
gpu002 : ok=12 changed=3 unreachable=0 failed=1 skipped=2 rescued=0 ignored=0   <- failure
```

## 7. Worked example: a safe driver-parameter rollout

```yaml
- name: Apply GPU node tuning with canary and validation
  hosts: gpu
  become: true
  serial: [1, "10%", "100%"]
  max_fail_percentage: 5
  vars:
    expected_gpus: 8
  pre_tasks:
    - name: Verify node is drained (Slurm) before changing kernel settings
      ansible.builtin.command: "scontrol show node {{ inventory_hostname }}"
      delegate_to: "{{ groups['slurm_controller'][0] }}"
      register: node_state
      changed_when: false
      check_mode: false
      failed_when: "'DRAIN' not in node_state.stdout"
  tasks:
    - name: Persist kernel settings
      ansible.posix.sysctl:
        name: vm.swappiness
        value: "1"
        sysctl_file: /etc/sysctl.d/90-ai.conf
        reload: true
    - name: Install nvidia-persistenced unit override
      ansible.builtin.template:
        src: nvidia-persistenced.override.conf.j2
        dest: /etc/systemd/system/nvidia-persistenced.service.d/override.conf
        mode: "0644"
      notify: Restart persistenced
  post_tasks:
    - name: Validate GPUs are healthy
      ansible.builtin.command: nvidia-smi --query-gpu=index --format=csv,noheader
      register: smi
      changed_when: false
      failed_when: (smi.stdout_lines | length) != expected_gpus
  handlers:
    - name: Restart persistenced
      ansible.builtin.systemd_service:
        name: nvidia-persistenced
        state: restarted
        daemon_reload: true
```

Run: `--check --diff --limit gpu001` first; then the real run with the canary batch; the validation failure stops the play before the 10% batch (`max_fail_percentage`). Resume Slurm nodes in a separate, explicit play after validation.

## 8. Lab (untested)

1. **Multi-play playbook**: create `site.yml` with `pre_tasks`, `roles` (empty), `tasks`, `post_tasks`, handlers; observe execution order using `debug` tasks and `--list-tasks`.
2. **Modules tour**: with one task each, use `package`, `service`, `user`, `file`, `copy`, `lineinfile`, `blockinfile`, `template`, `stat`, `get_url` (with checksum), `unarchive`, `sysctl`, `cron`, `wait_for`; run twice and confirm `changed=0` the second time.
3. **Make it idempotent**: take a naive playbook using `shell: echo "x" >> file` and `command: useradd`; refactor into `lineinfile`/`user`; for one remaining command use `creates`, `changed_when`, `failed_when`.
4. **Check and diff**: run `--check --diff` on a templated file change; show a `command` task being skipped; mark a read-only probe `check_mode: false`; demonstrate a dependent task failing in check mode and fix with `when: not ansible_check_mode`.
5. **Idempotency trap**: put `{{ ansible_date_time.iso8601 }}` into a template and watch every run report changed and trigger handlers; remove it.
6. **Execution control**: use `--tags/--skip-tags`, `--limit`, `--start-at-task`, `--step`; add `always` and `never` tags; try `serial: [1, 50%, 100%]` on 6 hosts and print the batch composition with `ansible_play_batch`.
7. **Failure policy**: make one host fail intentionally; compare `any_errors_fatal`, `max_fail_percentage`, `ignore_errors`, `force_handlers`; record exit codes with `echo $?`.
8. **Delegation and async**: use `delegate_to: localhost` to write per-host results to the control node; run a 60-second command with `async/poll` and with `poll: 0` plus `async_status`.
9. **Retries**: write a task polling a service with `until/retries/delay`; stop the service to see the retry output.
10. **Canary rollout**: implement the worked example against containers; inject a validation failure on the canary and confirm the play halts.
11. **Lint**: run `ansible-lint` and fix FQCN, naming, `command-instead-of-module`, `no-changed-when`, and `risky-file-permissions` findings.
12. **Clean up.**

Mark tested only after execution.

## 9. Common mistakes

- Missing task names (the log becomes unreadable) or names that describe commands instead of desired state.
- `shell`/`command` for things modules do; missing `changed_when` so the recap lies; ignoring `rc`.
- `state: latest` in routine runs (unplanned upgrades); unpinned driver versions.
- `ignore_errors: true` sprinkled to silence problems instead of handling them.
- Non-idempotent templates (timestamps, random values) and handler storms.
- Assuming check mode is a perfect prediction; leaking secrets via `--diff`.
- Running against `all` with no `--limit` or `serial`; no canary.
- Overusing tags as the safety mechanism, skipping prerequisite tasks.
- Using `lineinfile` with a loose regex that rewrites unintended lines; editing files that should be fully templated or drop-ins.
- Not setting modes explicitly (YAML octal pitfalls: quote modes, `"0644"`).
- Long-running tasks without `async` or timeouts; SSH timeouts killing firmware updates.
- Relying on task order across plays without verifying dependencies.

## 10. Interview angles

- "How do you make a playbook idempotent? What breaks idempotency?" 
- "Explain check mode and its limits. How would you do a safe production change?" (check/diff, canary via `serial`, validation, `max_fail_percentage`.)
- "`command` vs `shell` vs `raw` vs `script`?" 
- "How do you perform a rolling update across 500 nodes with a canary?" 
- "What does `delegate_to` do and when do you use `run_once`?" 
- "How do you handle long-running tasks and SSH timeouts?" (async/poll.)
- "What do `changed_when` and `failed_when` do?" 
- "Tags: how do you use them and what are the risks?" 
- "How do you know the playbook is safe to rerun?" (second run `changed=0`, Molecule idempotence test.)

## 11. Checkpoint questions (35)

1. Order of execution in a play? **A:** pre_tasks, roles, tasks, post_tasks, with handlers flushed between.
2. What is idempotency in modules? **A:** Compares desired vs actual and changes only when different.
3. Task names should describe what? **A:** Desired state.
4. What does `register` do? **A:** Stores the module result in a variable.
5. What does `changed_when: false` do? **A:** Task never reports changed (read-only probes).
6. What does `creates:` do? **A:** Skips the command if the path exists.
7. When does `command` skip in check mode? **A:** Always, unless `creates/removes` or `check_mode: false`.
8. What does `--diff` show? **A:** Before/after content of changed files.
9. How leak-proof is `--diff`? **A:** Not; use `diff: false` for secrets.
10. What is `serial`? **A:** Limits batch size of hosts per play iteration.
11. Meaning of `serial: [1, "10%", "100%"]`? **A:** Canary then growing batches.
12. `max_fail_percentage` effect? **A:** Aborts play if too many hosts in a batch fail.
13. `any_errors_fatal`? **A:** First failure aborts the play for all hosts.
14. `strategy: free`? **A:** Hosts run independently without waiting.
15. `throttle`? **A:** Concurrency cap for a task.
16. `run_once`? **A:** Execute task on one host only.
17. `delegate_to`? **A:** Run the task on another host with current host context.
18. `async` with `poll: 0`? **A:** Fire and forget; check later with `async_status`.
19. Special tags? **A:** `always` and `never`.
20. How to start at a task? **A:** `--start-at-task`.
21. Exit code for failed hosts? **A:** 2.
22. Exit code for unreachable hosts? **A:** 3.
23. Module for kernel parameters? **A:** `ansible.posix.sysctl`.
24. Module to pin packages on Debian? **A:** `dpkg_selections` (hold).
25. `state: latest` risk? **A:** Unplanned upgrades.
26. How to validate before installing a config? **A:** `validate:` on `copy`/`template`.
27. How to make downloads safe? **A:** `checksum:` on `get_url`.
28. How to reboot and wait? **A:** `ansible.builtin.reboot`.
29. Module for waiting on ports? **A:** `wait_for`.
30. Handler trigger condition? **A:** Notified task reports changed.
31. `meta: flush_handlers` effect? **A:** Runs pending handlers immediately.
32. `force_handlers`? **A:** Run handlers even if a later task fails.
33. Why avoid timestamps in templates? **A:** Breaks idempotency.
34. What does `lineinfile` do? **A:** Ensures a single line matches desired state.
35. Why tags are not a safety mechanism? **A:** Partial runs skip prerequisites.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Rene Moser and Lorin Hochstein, *Ansible: Up and Running*, 3rd edition (chapter 3 on playbook basics, plus chapters on error handling and execution control).
- Ansible documentation: playbook keywords, modules index, check mode and diff, strategies, async, delegation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** collection ownership of modules (several moved between `ansible.builtin`, `ansible.posix` and `community.general`), module option names for your ansible-core version, `ansible-playbook` exit code table, `validate` behaviour for `sshd` drop-ins, and every code listing; all labs are **untested**.
