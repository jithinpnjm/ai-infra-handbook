---
id: "c04-08"
title: "4.8 Ansible handlers, conditionals, loops, blocks and error handling"
sidebar_label: "4.8 Ansible handlers, conditionals, loops, blocks and error handling"
sidebar_position: 8
description: "Control flow in Ansible: handlers and notify semantics, when conditionals, loops, blocks with rescue and always, failure handling, retries, assertions, delegation patterns, imports versus includes and rolling-update orchestration"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 4.8 Ansible handlers, conditionals, loops, blocks and error handling

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | ansible-core; 2 to 3 Linux targets (containers with systemd or VMs) |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Real fleet changes are not straight lines. A configuration change must restart a service only if the file actually changed; only on nodes that have a GPU; only after the node is drained; and if the driver install fails the node must be left in a known state with a clear message, not half-configured. Ansible's control-flow features (handlers, `when`, loops, `block`/`rescue`/`always`, failure keywords, retries) are what turn a list of tasks into a reliable procedure. They are also where subtle bugs live: handlers that never fire, conditions that evaluate strings instead of booleans, rescue blocks that hide errors, loops that quietly skip.

## Prerequisites and outcomes

Needs 4.6 and 4.7. After this chapter you can:

- Use handlers correctly (`notify`, `listen`, flushing, ordering, behaviour on failure) and avoid restart storms.
- Write robust conditionals with facts, registered results and type-safe tests.
- Use loops (`loop`, `until`, `loop_control`), including nested data, with correct `register` handling.
- Structure error handling with `block`/`rescue`/`always`, `failed_when`, `changed_when`, `ignore_errors`, `any_errors_fatal`, `max_fail_percentage`, `meta: end_host`, and `assert`/`fail`.
- Choose between `import_*` (static) and `include_*` (dynamic) for tasks and roles.
- Implement drain → change → validate → return-to-service flows and safe rolling updates.

## 1. Handlers

A **handler** is a task that runs only when notified by another task that reported `changed`, and runs **once** per play, at the end of the current section, even if notified many times. They exist to restart or reload services only when configuration changed.

```yaml
- hosts: gpu
  become: true
  tasks:
    - name: Configure DCGM exporter options
      ansible.builtin.template:
        src: dcgm-exporter.env.j2
        dest: /etc/default/dcgm-exporter
        mode: "0644"
      notify:
        - Restart dcgm-exporter
        - Record config change

    - name: Install exporter unit file
      ansible.builtin.copy:
        src: dcgm-exporter.service
        dest: /etc/systemd/system/dcgm-exporter.service
        mode: "0644"
      notify: Reload systemd and restart dcgm-exporter

    - name: Make sure it is running (idempotent, independent of handlers)
      ansible.builtin.systemd_service:
        name: dcgm-exporter
        state: started
        enabled: true

  handlers:
    - name: Restart dcgm-exporter
      ansible.builtin.systemd_service:
        name: dcgm-exporter
        state: restarted
      listen: "Reload systemd and restart dcgm-exporter"       # topics: several handlers can listen to one name
    - name: Record config change
      ansible.builtin.lineinfile:
        path: /var/log/config-changes.log
        line: "{{ ansible_date_time.iso8601 }} dcgm-exporter configuration changed"
        create: true
```

Semantics to know:

- **Names and `listen`**: `notify` can reference a handler name or a `listen` topic string; handler names must be unique per play; the `listen` mechanism lets one notification trigger several handlers (and lets roles and playbooks hook each other without name coupling).
- **When do they run?** At the end of each of: `pre_tasks`, `roles/tasks`, `post_tasks` sections. Force earlier execution with `- ansible.builtin.meta: flush_handlers` (for example restart a service before a task that depends on the new config).
- **Handlers run in the order defined in the handlers section**, not the order notified.
- **Changed, not "ran"**: a task notifies only if it reports `changed`; skipped or ok tasks do not. If the first run changed the file but a later task failed before the handler ran, **the handler will not run on the next execution** (the file is already correct, so nothing is changed): the service stays on an old config. Mitigations: `force_handlers: true` on the play (run notified handlers even after failures), or design the restart as an idempotent state task (compare running config with desired) in addition to the handler, or `meta: flush_handlers` right after the config task.
- **Per host**: handler execution is tracked per host.
- **Handlers can notify other handlers** (since 2.x) and may use `when`.
- **Avoid restart storms**: reload rather than restart when possible; use `serial` so restarts do not happen everywhere at once; `throttle` for services with expensive restarts; ensure the notifying task is idempotent (a template with a changing timestamp notifies every run).
- Handlers in roles live in `roles/x/handlers/main.yml`; they are visible to the play and to other roles.

## 2. Conditionals: when

`when:` is a Jinja2 **expression** (no `{{ }}` wrapper) evaluated per host; the task is skipped if it is false.

```yaml
- name: Install NVIDIA driver on GPU hosts
  ansible.builtin.package:
    name: "nvidia-driver-{{ nvidia_driver_branch }}"
  when:
    - "'gpu' in group_names"                                  # list items are ANDed
    - ansible_facts['os_family'] == 'Debian'
    - gpu_count | default(0) | int > 0

- name: Run only on old kernels
  ansible.builtin.debug: msg="upgrade me"
  when: ansible_facts['kernel'] is version('5.15', '<')

- name: React to a previous task
  ansible.builtin.command: /usr/local/bin/post-install.sh
  when: driver_install is changed and driver_install is not failed

- name: OR conditions
  ansible.builtin.debug: msg="x"
  when: (a == 1) or (b == 2)
```

Rules and gotchas:

- Multiple list items are ANDed. Use parentheses with `or`.
- **Booleans vs strings**: `when: some_flag` is truthy for a boolean true or a non-empty string such as `"false"`! Use `when: some_flag | bool` for values that might be strings (`"yes"`, `"False"`, `-e flag=false` from the command line comes as a string). Compare numbers with `| int`: `when: (count | int) > 4`.
- **Tests on registered results**: `is succeeded`, `is failed`, `is changed`, `is skipped`, `is defined`, `result.rc == 0`, `'text' in result.stdout`, `result.stdout is search('regex')`, `result.stdout_lines | length > 0`.
- **A skipped task's registered variable** exists with `skipped: true` and no `stdout`; guard with `when: res is defined and res.stdout is defined`.
- **Conditions evaluate before the task, but per item in loops**: `when` with `loop` is evaluated for each item; `item` is available.
- **Conditionals on imports vs includes**: `when` on `import_tasks` applies the condition to each imported task (static), while on `include_tasks` it controls whether the include happens (dynamic). On `block`, the condition applies to every task in the block.
- `ansible_check_mode`, `ansible_run_tags`, and `inventory_hostname == groups['x'][0]` ("first host in group") are common predicates.
- Avoid `when: result.stdout` for emptiness checks on missing keys; use `| length > 0`.

## 3. Loops

```yaml
- name: Install packages one transaction (preferred where the module accepts a list)
  ansible.builtin.package: { name: [chrony, tmux, htop], state: present }

- name: Loop where each item needs a separate call
  ansible.builtin.template:
    src: "{{ item }}.conf.j2"
    dest: "/etc/{{ item }}.conf"
    mode: "0644"
  loop: [chrony, rsyslog, logrotate]

- name: Loop over a list of dicts with a short label
  ansible.builtin.user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
  loop: "{{ team_users }}"
  loop_control:
    label: "{{ item.name }}"
    index_var: i
    pause: 1                      # seconds between items

- name: Poll until healthy (retry loop)
  ansible.builtin.uri:
    url: "http://{{ inventory_hostname }}:9400/metrics"
    status_code: 200
  register: probe
  until: probe.status == 200
  retries: 12
  delay: 10
```

- `loop:` replaces most `with_*` forms; transform data with filters (`dict2items`, `subelements`, `product`, `zip`, `flatten`); `with_fileglob` and `with_nested` still appear in older code.
- A task with `loop` and `register` stores `register.results`, a list of per-item results (each including `item`). Aggregate with `results | map(attribute='rc')`, `results | selectattr('failed')`.
- `until` re-runs the task until the condition holds or retries are exhausted; `delay` seconds between attempts; combined with `loop` each item has its own retry sequence. Retry a **read/probe** or an idempotent operation, never a non-idempotent write.
- Loops over thousands of items are slow (one module invocation per item per host); push iteration into the module (lists), into a template, or into a single script/module where possible.
- `loop_control: loop_var: outer_item` avoids name clashes in nested includes (when an included task file also loops, rename `item`).
- **Loop across hosts with serial dependencies** (e.g., upgrade one node of a quorum at a time) uses `serial: 1` at the play level rather than a loop.

## 4. Error handling

### Default behaviour

A failed task on a host removes that host from the remainder of the play; other hosts continue (unless `any_errors_fatal` / `max_fail_percentage` stops the play). The play recap reports `failed` and the exit code is non-zero (2). `unreachable` hosts are similar but counted separately (exit 3).

### Overriding judgement

```yaml
- name: Grep returns 1 when no match: not an error
  ansible.builtin.command: grep -q 'Xid' /var/log/kern.log
  register: xid
  failed_when: xid.rc not in [0, 1]
  changed_when: false

- name: Command whose stderr indicates a problem despite rc=0
  ansible.builtin.command: some-tool --check
  register: out
  failed_when: "'ERROR' in out.stdout or out.rc != 0"

- name: Best-effort cleanup
  ansible.builtin.file: { path: /tmp/stale, state: absent }
  ignore_errors: true                        # continue after failure but record it (visible as 'ignored' in recap)
  # ignore_unreachable: true                 # for unreachable hosts
```

`ignore_errors` is a blunt tool: prefer a precise `failed_when` that names the acceptable cases.

### Blocks: rescue and always

A **block** groups tasks to share keywords (`when`, `become`, `tags`, `vars`, `environment`) and provides structured error handling like try/except/finally.

```yaml
- name: Upgrade driver with automatic rollback
  block:
    - name: Install new driver
      ansible.builtin.apt:
        name: "nvidia-driver-{{ new_branch }}"
        state: present
      register: install

    - name: Reload kernel module
      ansible.builtin.command: /usr/local/bin/reload-nvidia.sh

    - name: Verify GPUs
      ansible.builtin.command: nvidia-smi -L
      register: smi
      failed_when: (smi.stdout_lines | length) != expected_gpus
      changed_when: false

  rescue:                                           # runs if any task in block fails
    - name: Record what failed
      ansible.builtin.debug:
        msg: "Failed task: {{ ansible_failed_task.name }}; result: {{ ansible_failed_result | default({}) }}"
    - name: Roll back to the previous driver
      ansible.builtin.apt:
        name: "nvidia-driver-{{ old_branch }}"
        state: present
        allow_downgrade: true
    - name: Keep node out of service and fail the host loudly
      ansible.builtin.fail:
        msg: "Driver upgrade failed on {{ inventory_hostname }}; rolled back; node left drained"

  always:                                           # runs regardless
    - name: Collect diagnostics
      ansible.builtin.shell: "journalctl -k --since '-10min' | tail -n 200"
      register: kernel_tail
      changed_when: false
      failed_when: false
```

Notes: if `rescue` completes without failing, the host is **recovered**: Ansible treats the block as handled and continues (recap shows `rescued`); to keep the failure visible re-raise with `fail` as above. `ansible_failed_task` and `ansible_failed_result` are available in `rescue`. Handlers inside a block still run at section ends; `always` runs even after `rescue`. Blocks nest. Variables registered inside survive afterwards. A `rescue` that silently swallows errors is a common source of "green but broken" runs: log, alert and (for fleet changes) usually stop.

### Stopping the play and fleet-level policies

```yaml
- hosts: gpu
  any_errors_fatal: true            # any failure aborts all hosts immediately (use for dangerous global steps)
  max_fail_percentage: 5            # tolerate small failure rates per batch
  serial: 10
  tasks:
    - ansible.builtin.meta: end_host           # stop processing this host without failure
      when: skip_this_host | default(false)
    - ansible.builtin.meta: end_play           # end the play for everyone (not a failure)
      when: dry_run_only | default(false)
    - ansible.builtin.assert:
        that:
          - expected_gpus is defined
          - expected_gpus | int > 0
        fail_msg: "Set expected_gpus for {{ inventory_hostname }}"
        success_msg: "Inputs OK"
    - ansible.builtin.fail:
        msg: "Refusing to run in production without change ticket"
      when: env == 'prod' and change_ticket is not defined
```

- `assert` for preconditions at the start (fail early and clearly), `fail` for explicit stops, `meta: end_host`/`end_play`/`end_batch` to exit cleanly, `meta: clear_host_errors` to reset failed hosts (rare).
- **Order of defence for fleet changes**: validate inputs (assert) → canary via `serial` → health validation after change → `max_fail_percentage`/`any_errors_fatal` → rescue with rollback → alert.
- `force_handlers`, `ignore_unreachable`, `timeout` on tasks, and `async` for long steps complete the toolkit (4.6).

### Retries and eventual consistency

Services take time: use `wait_for`, `uri` with `until`, `ansible.builtin.wait_for_connection` after reboots, `ansible.builtin.reboot` with `reboot_timeout`. Never replace verification with `pause: seconds=60`; poll the condition you care about (port open, GPUs visible, node `idle` in Slurm, Kubernetes node `Ready`).

## 5. Imports versus includes

| | `import_tasks` / `import_role` / `import_playbook` | `include_tasks` / `include_role` |
|---|---|---|
| Processing | **Static**, at parse time | **Dynamic**, at runtime when reached |
| `--list-tasks`, `--tags`, `--start-at-task` | Fully visible and usable | Included tasks not listed; tags apply to the include itself unless `apply:` |
| Loops on the statement | Not supported | Supported (include once per item) |
| Variables in the filename | Limited (known at parse time) | Fully dynamic (`"{{ ansible_facts['os_family'] }}.yml"`) |
| `when` | Applied to every imported task | Applied to the include; included tasks inherit it |
| Handlers | Visible at parse time | Handlers inside included files are visible only after inclusion |

Guidance: prefer **import** for fixed structure (clean tags/list-tasks/lint), **include** when the choice depends on runtime data (OS-specific task files, loops over items, conditional roles). Use `apply: { tags: [x] }` when you need tags to flow into includes. Roles are the main reuse unit (4.11).

## 6. Patterns for operational flows

### Drain → change → validate → return

```yaml
- name: Safe GPU node maintenance
  hosts: gpu
  serial: [1, "10%", "25%"]
  max_fail_percentage: 5
  any_errors_fatal: false
  tasks:
    - name: Drain from Slurm
      ansible.builtin.command: >
        scontrol update NodeName={{ inventory_hostname }} State=DRAIN Reason="ansible maintenance {{ lookup('env','USER') }}"
      delegate_to: "{{ groups['slurm_controller'][0] }}"
      changed_when: true
    - name: Wait until no jobs remain
      ansible.builtin.command: "squeue -h -w {{ inventory_hostname }} -o %i"
      delegate_to: "{{ groups['slurm_controller'][0] }}"
      register: jobs
      until: jobs.stdout == ""
      retries: 120
      delay: 30
      changed_when: false

    - block:
        - ansible.builtin.include_role: { name: gpu_node, tasks_from: apply_changes }
        - name: Validate
          ansible.builtin.include_role: { name: gpu_node, tasks_from: validate }
      rescue:
        - ansible.builtin.fail:
            msg: "Maintenance failed on {{ inventory_hostname }}; node left DRAINED for investigation"
      # no 'always: resume' on purpose: only a healthy node returns to service

    - name: Return to service
      ansible.builtin.command: "scontrol update NodeName={{ inventory_hostname }} State=RESUME"
      delegate_to: "{{ groups['slurm_controller'][0] }}"
      changed_when: true
```

Principles encoded here: the failure path leaves the node drained (safe default), success explicitly resumes, the canary batch is size 1, and waiting polls actual state. The same shape fits Kubernetes (`kubectl drain`, uncordon) and load-balancer rotation (`delegate_to: localhost` calling an API).

### Idempotent restart-if-needed

```yaml
- name: Detect whether the running service uses the new config
  ansible.builtin.command: systemctl show -p ActiveEnterTimestampMonotonic dcgm-exporter
  register: started
  changed_when: false
# compare with config mtime (stat) to decide on restart: avoids missed restarts after earlier failures
```

When handler semantics are insufficient (partial failure leaves services stale), replace handler-only logic with state checks or run `meta: flush_handlers` immediately after the config change.

### Waiting for the world

```yaml
- name: Reboot and wait for GPUs
  ansible.builtin.reboot:
    reboot_timeout: 1800
    post_reboot_delay: 30
    test_command: nvidia-smi -L
```

## 7. Debugging control flow

| Symptom | Likely cause | Fix |
|---|---|---|
| Handler never ran | Task did not report changed; earlier failure aborted before handler; handler name typo (silently ignored in older versions; newer versions error) | `-v` to see `changed`; `force_handlers`; `flush_handlers` |
| Handler ran every time | Task not idempotent (timestamps, `command` without `changed_when`) | Fix the source of changes |
| Task skipped unexpectedly | `when` evaluated false (string vs bool), loop item missing, wrong group | `-vv` shows `false_condition`; `debug` the variables |
| Condition error `The conditional check failed` | Undefined variable, wrong type | `default()`, `is defined`, casts |
| `rescue` ran but play is green | Rescue handled the failure | Re-raise with `fail`; check `rescued` count in recap |
| Loop result weird | `register` in loop gives `results` list | Use `results \| map(...)` |
| Retries did not stop | `until` condition never true; stale variable | Print `register` each attempt (`-v`), fix condition |
| Included tasks not tagged | Dynamic include ignoring tags | Use `import_tasks` or `apply:` |

Use `ansible-playbook -vv`, `--step`, `--start-at-task`, and the `debug` strategy (`strategy: debug`, or `ANSIBLE_STRATEGY=debug`) which drops into an interactive debugger on failure (`p task_vars`, `p result._result`, `task.args`, `redo`, `continue`, `quit`); see 4.10.

## 8. Lab (untested)

1. **Handlers**: notify a restart from two tasks and verify one restart; use `listen` topics; reproduce the "handler lost after failure" scenario (fail a later task), then fix with `force_handlers` and with `meta: flush_handlers`.
2. **Restart storm**: make a template non-idempotent (timestamp) and observe constant restarts; fix.
3. **Conditionals**: gate tasks by group membership, OS family, facts and registered results; reproduce the string-boolean bug using `-e flag=false`; fix with `| bool`.
4. **Loops**: create users from a list of dicts with `loop_control.label`; register loop results and summarise failures; implement `until` polling on a flaky service; compare loop vs list-argument `package` run time.
5. **Failure semantics**: write tasks whose `rc` is 1 acceptably (grep) with `failed_when`; compare `ignore_errors` and `failed_when`; check the recap and exit codes.
6. **Block/rescue/always**: implement the driver upgrade with rollback against a fake installer script that fails on one host; make the rescue re-raise; verify the `always` diagnostics.
7. **Fleet policies**: use `serial`, `max_fail_percentage`, `any_errors_fatal` on six hosts with injected failures; document when the play aborts in each case.
8. **Import vs include**: restructure tasks into files; compare `--list-tasks`, `--tags`, and loops with `import_tasks` vs `include_tasks`; use `apply: tags`.
9. **Drain flow**: simulate Slurm with scripts or use a real Slurm lab; run the drain → change → validate → resume play with an injected validation failure and confirm the node stays drained.
10. **Debugger**: trigger a failure under `strategy: debug`, inspect `task_vars`, fix a variable and `redo`.
11. **Clean up.**

Mark tested only after execution.

## 9. Common mistakes

- Expecting handlers to run when the notifying task did not change, or after a failed play.
- Using `when: "{{ var }}"` (templating inside conditionals) and string-boolean confusion.
- `ignore_errors: true` as a default; rescue blocks that swallow failures.
- No `changed_when` on commands that notify handlers (or always `changed`).
- Loops of single-item package installs; heavy loops over many hosts and items.
- `pause` instead of polling a real condition.
- Mixing `include_*` and tags/`--list-tasks` expectations.
- Returning drained nodes to service in an `always:` section regardless of validation.
- Assuming `serial` guards against every failure without `max_fail_percentage` and validation steps.
- Forgetting that registered variables from skipped tasks lack fields.
- Using `any_errors_fatal` everywhere (a single flaky host halts the fleet) or nowhere (a bad change spreads).

## 10. Interview angles

- "How do handlers work? When do they not run? How would you guarantee a restart after a partial failure?" 
- "Explain `block`, `rescue`, `always` and how a rescued failure is reported."
- "`failed_when`/`changed_when` vs `ignore_errors`." 
- "Static vs dynamic includes: differences and consequences for tags and `--list-tasks`."
- "How do you perform a rolling update with a canary and automatic stop on failure?" 
- "How do you wait for a node to rejoin the cluster after reboot?" 
- "What causes a handler to run on every run?" 
- "How do you debug a playbook that skips a task?" 

## 11. Checkpoint questions (35)

1. When does a handler run? **A:** At the end of a section if notified by a changed task.
2. How many times per play? **A:** Once per host.
3. What does `listen` do? **A:** Subscribes handlers to a topic name.
4. How force handlers earlier? **A:** `meta: flush_handlers`.
5. Handler lost after failure: why? **A:** Next run's task is unchanged so no notify.
6. Play keyword to run handlers despite failure? **A:** `force_handlers: true`.
7. What is `when` syntax? **A:** Raw Jinja expression without braces.
8. Multiple `when` list items combine how? **A:** AND.
9. Why `| bool` in `when`? **A:** Strings like "false" are truthy.
10. How test a registered result? **A:** `is succeeded/failed/changed/skipped`, fields like `rc`.
11. What is `register.results`? **A:** Per-item results of a looped task.
12. `loop_control.label` purpose? **A:** Shorter output.
13. `until/retries/delay` use? **A:** Poll a condition.
14. When retry safely? **A:** Reads and idempotent operations.
15. What does `failed_when` do? **A:** Redefines failure.
16. What does `changed_when: false` do? **A:** Marks probes as never changing.
17. `ignore_errors` visible how? **A:** Recap `ignored` count.
18. What does `rescue` run on? **A:** Failure in the block.
19. Does `always` run after rescue? **A:** Yes.
20. Variable holding failed task info? **A:** `ansible_failed_task` / `ansible_failed_result`.
21. How keep failure visible after rescue? **A:** `fail` inside rescue.
22. `any_errors_fatal` effect? **A:** First failure aborts everyone.
23. `max_fail_percentage` effect? **A:** Aborts when failure rate exceeds threshold.
24. `meta: end_host` vs `end_play`? **A:** Stop this host cleanly vs end the play.
25. `assert` vs `fail`? **A:** Condition check vs unconditional stop.
26. Static include keyword? **A:** `import_*`.
27. Dynamic include keyword? **A:** `include_*`.
28. Which supports loops? **A:** `include_*`.
29. Which supports `--list-tasks` fully? **A:** `import_*`.
30. How pass tags into includes? **A:** `apply: tags`.
31. Safe maintenance flow? **A:** Drain, change, validate, resume.
32. Where to leave a failed node? **A:** Drained/out of service.
33. How wait for reboot? **A:** `reboot` module / `wait_for_connection`.
34. Instead of `pause`? **A:** Poll the actual condition.
35. Debug strategy? **A:** `strategy: debug` interactive debugger.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Rene Moser and Lorin Hochstein, *Ansible: Up and Running*, 3rd edition (chapters on complex playbooks: handlers, conditionals, loops, blocks, error handling; and on debugging).
- Ansible documentation: handlers, conditionals, loops, blocks, error handling, `meta` module, playbook keywords.
- Examples are the author's constructions.

**Flagged for verification before publishing:** handler-name error behaviour and `listen` semantics in the ansible-core version used, `meta` options available, `systemd_service` module availability (older versions use `systemd`), Slurm command options (`scontrol update`, `squeue -w`), and every code listing; all labs are **untested**.
