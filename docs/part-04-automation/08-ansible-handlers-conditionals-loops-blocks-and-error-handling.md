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

Picture a fleet change that goes wrong halfway. A config file changes on a GPU node, a later step fails, and the node is left half-configured. Nobody on the team notices until a job that should have run on that node stalls, and by then the logs no longer show what happened first. Real fleet changes are not straight lines. A service should restart only if its file actually changed. A GPU task should run only on nodes that have a GPU. A node should be drained before you change it, and if the driver install fails, the node must be left in a known state with a clear message.

Think of a surgical team with a checklist. Some steps happen only for certain patients, some steps must be repeated until the vital signs settle, and one step must happen even when something went wrong. Ansible's control-flow features give a playbook the same kind of structure. These features are handlers, `when`, loops, `block`/`rescue`/`always`, failure keywords and retries. Each one answers a question a real change raises. Did anything change? Does this apply to this host? Should I repeat this step? What do I do when it fails?

Subtle bugs also hide in these features. Handlers that never fire, conditions that evaluate strings instead of booleans, rescue blocks that hide errors and loops that quietly skip are all easy to write and hard to spot. The rest of this chapter takes each feature in turn, shows the situation it was built for, and names the trap that comes with it.

## Prerequisites and outcomes

This chapter builds on 4.6 and 4.7. By the end, you will be able to:

- Use handlers correctly, including `notify`, `listen`, flushing, ordering and behaviour on failure, and avoid restart storms.
- Write robust conditionals with facts, registered results and type-safe tests.
- Use loops (`loop`, `until`, `loop_control`), including nested data, with correct `register` handling.
- Structure error handling with `block`/`rescue`/`always`, `failed_when`, `changed_when`, `ignore_errors`, `any_errors_fatal`, `max_fail_percentage`, `meta: end_host`, and `assert`/`fail`.
- Choose between `import_*` (static) and `include_*` (dynamic) for tasks and roles.
- Implement drain, change, validate and return-to-service flows, and safe rolling updates.

## 1. Handlers

![A changed config task queues a restart, a later task fails and the handler is skipped, and the second run reports ok so no restart happens.](./img/a08-handler-lost.svg)

*Figure 4.8.1. A handler can be lost when a later task fails in the same run, because the next run sees an unchanged file and never notifies it.*

A template changes the nginx config on three web servers. The new config is correct, but nginx keeps serving the old settings until someone restarts it. Handlers exist for exactly that moment. A handler runs once, at the end of the play, and only when a task reports a change. The restart happens when it is needed, and never when it is not.

Suppose you update the DCGM exporter configuration on a GPU node. DCGM is NVIDIA's data center GPU manager, and its exporter publishes GPU health numbers that monitoring reads. The service has to restart before it can read the new file. Restarting it on every run, though, is unnecessary, and it briefly interrupts the metrics that your dashboards depend on. A handler solves this. A handler is a task that runs only when another task reports `changed`. It also runs once per play, at the end of the current section, even when many tasks notify it.

Here is the flow in plain steps. The template task compares the rendered file with the file on disk. If they differ, the task writes the new file and reports `changed`. That report adds the named handlers to a queue. When the section ends, Ansible takes each queued handler once, in the order the handlers are defined, and runs it. If the template found no difference, nothing is queued, and the restart never happens.

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

The third task does not depend on the handlers. It makes sure the service runs whatever happens to them. Its effect is simple. If the service is already running, the task does nothing. If it is stopped, the task starts it. That gives you a safety net that works even when the handlers have nothing to do.

Handler names must be unique within a play. A `notify` can point to a handler name or to a `listen` topic string. A topic lets one notification trigger several handlers, so roles and playbooks can hook into each other without depending on each other's names. Picture a doorbell with several chimes wired to it. The person pressing the button does not need to know how many chimes there are.

Handlers run at the end of each of the `pre_tasks`, `roles/tasks` and `post_tasks` sections. To force one earlier, use `- ansible.builtin.meta: flush_handlers`. You might do this to restart a service before a task that depends on its new config, such as a health check that must see the new settings. Handlers run in the order they are defined in the handlers section, not in the order they were notified. A handler defined first runs first, even if a later task notified it earlier.

A task notifies only when it reports `changed`. Skipped tasks and `ok` tasks notify nothing. Here is the trap. A first run changes the file, but a later task fails before the handler runs. On the next run, the file is already correct, so nothing changes and the handler does not run. The service stays on the old config, and the second run looks perfectly clean. You have three ways out. Set `force_handlers: true` on the play to run notified handlers even after failures. Add an idempotent state task that compares the running config with the desired one, next to the handler. Or run `meta: flush_handlers` right after the config task, so the restart happens before anything else can fail.

Handler execution is tracked per host. Each host keeps its own queue of notified handlers. A host that failed drops its queue, while the other hosts still run theirs. That is why a single failed host can leave its own service stale without affecting the rest of the fleet.

Handlers can also notify other handlers, since 2.x, and they may use `when`. *Ansible: Up and Running*, Chapter 11, covers both patterns in `Examples 11-27` to `11-30`. The first is handler chaining. In an `ssl` role, `Copy SSL certs` notifies `check nginx configuration`, which notifies `restart nginx`, which notifies `after config check`. Each step runs only because the previous one reported a change, so a new certificate leads to a config check, then a restart, then a final verification. The second is `listen:` topic fan-out. With `listen: Ssl_certs_changed`, one topic triggers `check nginx configuration`, `restart nginx` and `after config check` in handler definition order. No task has to name those handlers directly, so roles stay loosely coupled.

Avoid restart storms. A restart storm is what happens when a service is restarted over and over, and each restart drops the work it was doing. Reload rather than restart when you can, because a reload asks the service to re-read its config without dropping connections. Use `serial` so restarts do not happen everywhere at once. Use `throttle` for services with expensive restarts. Make sure the notifying task is idempotent, because a template with a changing timestamp notifies on every run, and every run then restarts the service for no reason.

Handlers in roles live in `roles/x/handlers/main.yml`. The play and the other roles can see them, so a shared handler can be reused across roles.

The flowchart below shows the drain, change and return sequence that section 6 builds in code. Read it from top to bottom. The left branch is the happy path, and the right branch is what happens when the change fails. Both branches end with the node in a state you can explain to the next person on call.

![Handlers](./img/m4-08-1.svg)

*Figure 4.8.2. Handlers, as a diagram.*

For each handler, check that the task notifying it reports `changed` only when something real has changed. A quick test helps here. Run the playbook twice in a row with nothing edited between the runs. The second run should report `ok` for the notifying task and should not restart anything. If it still restarts, the notifying task is not idempotent, and the handler is doing work it should not.

## 2. Conditionals: when

![Two lanes showing a string false passed with -e being treated as true and the bool filter fixing it.](./img/p4-0408-when-string-trap.svg)

*Figure 4.8.3. The bool filter turns the string false into a real false so the condition evaluates as intended.*

A driver install should run on GPU nodes and be skipped on login nodes. A `when` clause states that condition beside the task, so a reader can see the rule without tracing the whole play. If the condition is false, Ansible reports the task as skipped, and the recap shows it. A skipped task is not a failure. It is the play saying that this task does not apply to this host.

Not every host should run every task. A driver install belongs on GPU hosts, not on every machine in the inventory. The `when:` keyword makes that decision for each host. It takes a Jinja2 expression, written without the `{{ }}` wrapper, and evaluates it per host. If the expression is false, the task is skipped. Think of it as a bouncer at a door with a short list of rules. Each host walks up, the rule is checked against that host's facts, and the host either goes in or waits outside.

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

The first task needs all three of its conditions to hold. Read it as "GPU group, and Debian family, and at least one GPU". The last one uses `or`, so its two parts sit in parentheses. The parentheses matter, because without them the rule would bind differently than the reader expects.

Items in a `when:` list are ANDed, so you need every item to be true. When you need an `or`, write it as one expression with parentheses. A list is a convenient way to stack conditions that must all hold, and it reads almost like a checklist.

Strings cause the most trouble. `when: some_flag` is truthy for a boolean true, but it is also truthy for a non-empty string such as `"false"`. That happens with `-e flag=false` on the command line, because the value arrives as a string. The condition sees a non-empty word, and a non-empty word counts as true. Use `when: some_flag | bool` for values that might be strings, such as `"yes"` or `"False"`. Compare numbers with `| int`, as in `when: (count | int) > 4`, because a count that arrived as text would otherwise compare as text.

Tests on registered results read close to plain English. The list includes `is succeeded`, `is failed`, `is changed`, `is skipped`, `is defined`, `result.rc == 0`, `'text' in result.stdout`, `result.stdout is search('regex')` and `result.stdout_lines | length > 0`. A line such as `when: probe is succeeded` says what you mean, so a reviewer can follow it without decoding a string comparison.

A skipped task still leaves its registered variable behind. That variable has `skipped: true` and no `stdout`. Guard it with `when: res is defined and res.stdout is defined`, so the check never reads a field that is not there.

Conditions are checked before the task runs. With `loop`, they are checked for each item, and `item` is available inside the check. That lets one loop skip some items and run others, based on each item's own values.

The `when` keyword behaves differently on imports and includes. On `import_tasks`, the condition is copied to every imported task, which makes it static, decided once while the playbook is read. On `include_tasks`, the condition controls whether the include happens at all, which makes it dynamic, decided while the play runs. On a `block`, the condition applies to every task inside it, so you write it once for the whole group.

Common predicates include `ansible_check_mode`, `ansible_run_tags`, and `inventory_hostname == groups['x'][0]`, which means the first host in a group. The last one is handy for work that should happen on exactly one host of a group, such as one controller. A predicate is a test that returns true or false, so these are simply the questions your conditions ask.

For emptiness checks, avoid `when: result.stdout` when the key may be missing. Use `| length > 0` instead. An empty string and a missing key both look falsy to a quick reader, but a missing key raises an error, and a length test handles both cases safely.

When you write a condition, check the real type of its value, because a string and a boolean behave differently. Print the value once with `debug` if you are not sure what type it is.

## 3. Loops

![A diagram showing how Ansible loops populate a results array in registered variables and how loop_control loop_var prevents inner loops from overwriting outer loop items.](./img/p4-0408-loop-register-results.svg)

*Figure 4.0.0. Loops store per-iteration output inside a results list on the registered dictionary, and loop_control loop_var prevents inner nested loops from clobbering outer loop variables.*

A loop repeats one task over a list. This section shows how to loop over lists of dictionaries, how to keep the output readable, and how to stop a loop from doing the wrong work on the wrong items. A loop is only as safe as the list it reads, so check the list first. A typo in one entry can send the change to the wrong host, and a loop makes that typo repeat for every item.

Installing packages one call at a time repeats work that a single call could do. Each call makes the package manager check its cache and resolve dependencies again, so three calls cost more than one call with three names. You can avoid that waste by passing a list, and loops handle the cases where each item needs its own call, such as one template per service.

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

The first task passes the whole package list in one transaction, which is the preferred form where the module accepts a list. A transaction here means one install run that either succeeds for every package or reports a problem for the set as a whole. The second repeats a template for each item, so each service gets its own file. The third loops over a list of dicts and labels each item with a short name. The last task retries until the metrics endpoint returns 200, which is a standard web success code. Each one matches a real need, and the choice between them comes down to whether the module can take the whole list at once.

The `loop:` keyword replaces most of the older `with_*` forms. Filters such as `dict2items`, `subelements`, `product`, `zip` and `flatten` reshape data for a loop, so that each pass of the loop gets exactly the pair or group it needs. Older code still uses `with_fileglob` (`keys/*.pub`), `with_lines` (`cat files/turing.txt`), `with_first_found` (`~/.ssh/id_ed25519.pub`, `id_rsa.pub`), `with_dict` (`ansible_enp0s8.ipv4`), `with_nested` and `with_subelements`. You will meet these in inherited roles, so it helps to recognise them. When you write new code, translate them into `loop:` with a filter.

You can also write your own Jinja2 filter plugins. Put them in `filter_plugins/` next to your playbook, and put custom lookup plugins in `lookup_plugins/`. *Ansible: Up and Running*, Chapter 10, gives an example. Its file `filter_plugins/surround_by_quotes.py` defines `class FilterModule:` with a `surround_by_quotes(a_list)` method. With that filter, `ALLOWED_HOSTS = [{{ domains | surround_by_quotes | join(", ") }}]` renders `["www.example.com", "example.com"]`. Read it as an assembly line. The list enters, each item is wrapped in quotes, and `join` glues the pieces together with commas. The code is tested in `code/part04/ansible_control_flow_lab.py`.

A task that uses both `loop` and `register` stores its output in `register.results`, a list of per-item results. Each entry is the return value for one item, and it includes `item`, so you can tell which entry came from which input. You can aggregate that list with `results | map(attribute='rc')`, which gives you every exit code in one list, or pick out the failures with `results | selectattr('failed')`. A common pattern is to run the whole loop, collect the failures, and then fail once with a summary, instead of stopping at the first bad item.

`until` reruns the task until its condition holds or the retries run out. `delay` sets the seconds between attempts. Picture a service that takes about a minute to become ready. A handful of retries spaced a few seconds apart gives it that minute to finish starting, and the task succeeds on the attempt where the port finally answers. When you combine `until` with `loop`, each item gets its own retry sequence. Retry only a read or a probe, or another idempotent operation. Never retry a non-idempotent write, such as one that creates a row or sends a message, because a retry then creates a second copy.

Loops over thousands of items are slow, because each item means one module call per host. Where you can, push the iteration into the module by passing a list, into a template, or into a single script or module. A single call that handles the whole batch is almost always faster than a loop that calls the module once per item.

Nested loops need their own variable names. When one loop sits inside another, both use `item` by default, and the inner one hides the outer one. Set `loop_control: loop_var: outer_item` on the outer loop to avoid name clashes. A common case is `loop_var: vhost` when `vhost-tasks.yml` is included inside a loop over virtual hosts, and that file loops over `logs`, `public_http`, `public_https` and `includes`. Without the rename, the inner loop would overwrite the virtual host you are working on. When an included task file also loops, rename the outer `item`.

Loops across hosts that depend on each other are a different case. When each node of a quorum must upgrade one at a time, use `serial: 1` at the play level rather than a loop. A quorum is the minimum group of members that must stay up for the whole cluster to keep working, so upgrading two of them at once could take the cluster down. `serial` controls how many hosts run each batch, which is the right tool when the hosts depend on each other.

Before you write a loop over many items, check whether the module can take the whole list in one call. If it can, the list is almost always the better choice.

## 4. Error handling

A command fails on one node out of forty. Should the whole play stop, or should the other thirty-nine continue? The default answer is to stop that host, but many operational flows need a different answer. This section explains how Ansible decides, and how to override that decision on purpose rather than by accident. Error handling is the part of a playbook that matters most during an incident, because that is when a wrong default does the most damage.

### Default behaviour

![In a play with four hosts, one host with a failed task leaves the rest of the play while the other three continue to the end.](./img/p2-0408-host-leaves-play.svg)

*Figure 4.8.4. A host whose task fails leaves the rest of the play while the other hosts keep running, and the recap records the failure.*

Suppose a task fails on one host while the rest of the play is still running. By default, that host leaves the rest of the play, and the other hosts carry on. Think of a relay race where one runner drops out, but the other runners keep going with their own legs. The exception is when `any_errors_fatal` or `max_fail_percentage` stops the play. The play recap reports `failed`, and the exit code is non-zero (2). `unreachable` hosts behave similarly, but the recap counts them separately, with exit 3. The separate count matters, because a host you could not reach is a different problem from a host where a command failed.

### Overriding judgement

![A decision pipeline showing how task exit codes and stdout are evaluated by default versus how failed_when, changed_when, and ignore_errors override host status and play recap.](./img/p4-0408-task-verdict-pipeline.svg)

*Figure 4.0.0. The task verdict pipeline shows how failed_when and changed_when override Ansible default exit-code evaluation and change detection before updating the play recap.*

Sometimes Ansible's verdict is wrong. `grep` returns 1 when nothing matches, and in that case that is not an error. It is an answer. Ansible reads any non-zero exit code as a failure, so the default is too strict for this case. The examples below replace a blanket decision with a narrow rule, so only the outcomes you actually care about count as failures.

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

The first example accepts exit codes 0 and 1, and it never reports a change. The `changed_when: false` line matters, because a search does not alter anything on the host, and reporting a change would make every run look like it did work. The second fails when the output contains `ERROR`, even if the exit code is 0. That catches tools that print an error and still exit cleanly. The last example, with `ignore_errors`, continues after a failure but still records it, so it shows as 'ignored' in the recap. `ignore_errors` is a blunt tool, because it hides the failure from the decision, so prefer a precise `failed_when` that names the acceptable cases. The comment on the last line shows the matching option for hosts that cannot be reached at all.

### Blocks: rescue and always

![A block runs the driver change tasks, a failed task hands control to rescue for rollback and a clear failure, and always collects diagnostics in every case.](./img/p2-0408-block-rescue.svg)

*Figure 4.8.5. A block runs the driver change, rescue rolls back and fails the host clearly if a task breaks, and always collects diagnostics either way.*

A block groups tasks, so that a failure inside the group can trigger a cleanup or a rollback. Think of it as a `try` with a `finally`, written in YAML. The block holds the change, the rescue holds the recovery, and the always section runs whether or not anything failed. In plain terms, the block says what to try, the rescue says what to do if the attempt breaks, and the always says what must happen no matter what.

A driver upgrade can fail after the new package is already in place. A package can install cleanly and the kernel module still fail to load, so the node is halfway into the new state. The node then needs a rollback to the old driver, a clear message and diagnostics that show what the kernel said. A `block` with `rescue` and `always` covers all three, and it does so in one place that a reviewer can read from top to bottom.

A **block** groups tasks so they can share keywords such as `when`, `become`, `tags`, `vars` and `environment`. A keyword set on the block applies to every task inside it, so you do not repeat it on each line. It also gives you structured error handling, much like try, except and finally in Python.

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

The `rescue` section runs only if a task in the block fails. Here it logs the failed task, rolls back to the previous driver and fails the host with a clear message. The `always` section runs in every case, and it collects kernel log diagnostics. Walk through a failure step by step. The install task fails, so the block stops there. The rescue runs its three tasks in order, and the rollback puts the old driver back. The fail task then stops the host with a note that says the node is left drained. The always section runs last, so the kernel messages from the failed attempt are saved for whoever investigates.

If `rescue` finishes without failing, Ansible marks the host **recovered**. It treats the block as handled and carries on, and the recap shows `rescued`. To keep the failure visible, re-raise it with `fail`, as the example does. The `fail` task is what makes the run red again, so that nobody reads a green recap and assumes the upgrade worked.

Inside `rescue`, `ansible_failed_task` and `ansible_failed_result` tell you what broke. They are the reason the first rescue task can print a useful message. Handlers inside a block still run at the end of their section. `always` runs even after `rescue`. Blocks can nest, and variables registered inside a block remain available afterwards, so the `smi` result from the verification task can still be read later in the play.

A `rescue` that swallows errors is a common cause of runs that look green but leave the system broken. For fleet changes, log the failure, send an alert and usually stop the run. A rescue is a place to clean up, not a place to hide the problem.

### Stopping the play and fleet-level policies

![A grouped comparison of meta end_host, end_play, clear_host_errors and fail showing which are clean exits and which stop the run.](./img/p4-0408-meta-exits.svg)

*Figure 4.8.6. Meta exits are planned and clean, fail is an explicit stop, and clearing host errors hides the reason for a failure.*

![Fleet changes pass five layers of defence: input validation, a serial canary, a post-change health check, a failure limit, and rollback with an alert.](./img/p2-0408-fleet-defence.svg)

*Figure 4.8.7. A fleet change is protected by five layers, from input assertions and a canary to a health check, a failure limit and a rollback with an alert.*

A single flaky host should not halt a whole fleet. One dangerous global step, though, should stop everything at once. The keywords and tasks below set those policies. Read the play from the top. The first three lines decide how far a failure may spread, and the tasks below them decide when a host or the whole play should stop on purpose.

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

`assert` checks preconditions at the start, so a run fails early and clearly. A precondition is a fact that must be true before any change is safe, such as a variable that names the expected GPU count. `fail` is for an explicit stop, where you have decided the run must not continue. `meta: end_host`, `meta: end_play` and `meta: end_batch` exit cleanly, which means they are a planned exit and not an error. `meta: clear_host_errors` resets failed hosts, which is rare, because clearing a failure hides the reason it happened.

For fleet changes, the order of defence is this. Validate the inputs with `assert`, so a missing value stops the run before anything is touched. Canary the change with `serial`, so one host goes first and proves the change works. Check health after the change, because a change that installs cleanly can still leave a service broken. Limit failures with `max_fail_percentage` or `any_errors_fatal`, so a bad change cannot spread past a set limit. Roll back in `rescue`, and then alert a person. Each layer catches what the one before it missed, so a single slip rarely becomes an outage.

The toolkit from 4.6 adds `force_handlers`, `ignore_unreachable`, a `timeout` on tasks, and `async` for long steps. The `async` keyword lets a long step, such as a large download, run in the background while the playbook polls it, so one slow task does not hold the others back.

### Retries and eventual consistency

![A two-lane timeline diagram contrasting the waste and failure modes of fixed pause 60 seconds against active until polling across fast and slow service restarts.](./img/p4-0408-pause-vs-poll.svg)

*Figure 4.0.0. Active polling with until and delay dynamically adapts to service readiness, avoiding the wasted latency and false failures caused by a blind pause.*

A service takes a few seconds to come back after a restart. The first health check fails, and the next one succeeds. Retries let a task wait for the system to settle, instead of failing on a race that would have resolved itself a moment later. The term eventual consistency describes a system that becomes correct after a short wait, and not instantly. A playbook that expects instant correctness will fail on a system like that, so the playbook has to allow for the wait.

Services take time to come up after a start or a reboot, so the playbook has to wait for them. Use `wait_for`, `uri` with `until`, `ansible.builtin.wait_for_connection` after reboots, and `ansible.builtin.reboot` with `reboot_timeout`. Never replace verification with `pause: seconds=60`. Poll the condition you care about instead, such as a port that is open, GPUs that are visible, a node that is `idle` in Slurm, or a Kubernetes node that is `Ready`. Let the playbook wait for the condition itself, not for a guessed number of seconds. A guessed number is either too short on a slow day or wastes time on a fast one, and a real condition is correct on both.

## 5. Imports versus includes

![Imports are read when the playbook is parsed and includes are read when the run reaches them, so a file name that depends on runtime facts needs an include.](./img/a08-import-include.svg)

*Figure 4.8.8. An import is fixed when the playbook is read, while an include is decided when the run reaches it, so the choice depends on whether the file name can change at runtime.*

Two ways to bring tasks into a play look alike but behave differently. An import is resolved when the playbook is read, and an include is resolved when the play runs. That difference decides whether tags, conditionals and loops apply the way you expect, so it is worth checking before you rely on either one.

Ansible can pull tasks or roles into a play in two ways. An import is read at parse time, which means before the first task runs, while an include is read when execution reaches it. Parse time is like reading a whole recipe before you start cooking, so you know every step in advance. Runtime is like reading each step as you reach it, which lets the next step depend on what the last one produced. The table shows what that difference changes.

| | `import_tasks` / `import_role` / `import_playbook` | `include_tasks` / `include_role` |
|---|---|---|
| Processing | **Static**, at parse time | **Dynamic**, at runtime when reached |
| `--list-tasks`, `--tags`, `--start-at-task` | Fully visible and usable | Included tasks not listed; tags apply to the include itself unless `apply:` |
| Loops on the statement | Not supported | Supported (include once per item) |
| Variables in the filename | Limited (known at parse time) | Fully dynamic (`"{{ ansible_facts['os_family'] }}.yml"`) |
| `when` | Applied to every imported task | Applied to the include; included tasks inherit it |
| Handlers | Visible at parse time | Handlers inside included files are visible only after inclusion |

Prefer an import for fixed structure, because tags, `--list-tasks` and lint then behave cleanly. Imports are visible before the run starts, so a tool can list them and a reviewer can read them. Choose an include when the choice depends on runtime data, such as OS-specific task files, loops over items or conditional roles. When you need tags to flow into an include, use `apply: { tags: [x] }`, which pushes the tag down to the tasks inside. Roles are the main reuse unit, which you will meet again in 4.11.

Choose an import by default, and switch to an include only when runtime data forces your hand. A useful test is to ask whether the file you want to load can change its name or its existence based on something the run discovers. If the answer is yes, use an include. If the answer is no, use an import.

## 6. Patterns for operational flows

Most operational work follows a small number of shapes, and the most common one is drain, change, validate, return. The patterns below are reusable skeletons for those shapes. Using them means you do not have to invent the ordering under pressure, when a wrong order is the easiest mistake to make. A skeleton is a starting point you fill in with your own commands, and the order of its steps is the part that keeps a node safe.

### Drain → change → validate → return

![A flow showing one node drained, waited empty, changed and validated, then resumed, with a failure path that leaves the node drained.](./img/p4-0408-drain-node-path.svg)

*Figure 4.8.9. The failure path leaves the node drained, and only full success reaches the resume step.*

![The serial list runs a one-node canary first, then 10 percent and 25 percent slices, with a failure limit of 5 percent.](./img/a08-serial-batches.svg)

*Figure 4.8.10. The serial list starts with a single-node canary and then works through larger slices of the fleet, with a failure limit that stops the run.*

Taking a GPU node out of service is a sequence. You drain it, wait for its jobs to finish, change it, check it, and only then return it to service. Drain means "stop new work from arriving, but let the work already running finish". The play below does that in batches that start at one node, so the first change is always small enough to watch.

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

Walk through one node's path. The drain command runs on the Slurm controller, because that is where the scheduler lives, so `delegate_to` sends the command there. The wait loop then asks the controller whether any job is still on that node, and it repeats until the answer is empty. Only after the node is empty does the change start. If the change or its validation fails, the rescue leaves the node drained, so nothing new lands on a machine that is not known to be good. Only a full success reaches the final resume step.

The failure path leaves the node drained, which is the safe default. Success explicitly resumes the node. The canary batch has size 1, and the waiting step polls the actual state instead of pausing for a fixed time. The `serial` list also grows in steps, so the first node is a test, the next group is a small slice, and only after that does the play work through larger slices of the fleet.

The same shape fits Kubernetes, with `kubectl drain` and uncordon, and load-balancer rotation, with `delegate_to: localhost` calling an API. Uncordon is the Kubernetes word for putting a drained node back in service. Whatever the tool, the sequence stays the same: stop new work, wait for old work, change, check, and resume.

### Idempotent restart-if-needed

![Two columns comparing a handler notification that can be lost after a failure with a state check that compares process start time to config file time.](./img/p4-0408-handler-vs-state-check.svg)

*Figure 4.8.11. A state check stays true after a failure that would erase a handler's notification.*

Handlers can miss a restart after an earlier failure, as section 1 showed. This task checks the running service instead of trusting a notification. It asks systemd when the current process started. A process that started before the config file was last written is still running the old settings. Comparing the two timestamps tells you whether a restart is owed, even when no handler remembers to ask for one.

```yaml
- name: Detect whether the running service uses the new config
  ansible.builtin.command: systemctl show -p ActiveEnterTimestampMonotonic dcgm-exporter
  register: started
  changed_when: false
# compare with config mtime (stat) to decide on restart: avoids missed restarts after earlier failures
```

When handler semantics are not enough, because a partial failure leaves services stale, replace handler-only logic with state checks. You can also run `meta: flush_handlers` immediately after the config change. The rule of thumb is simple. A handler says "something changed, so restart". A state check says "the thing that is running must match the thing on disk", and the second statement stays true even after a failure has wiped out the first.

### Waiting for the world

![After a reboot the host answers before the NVIDIA modules load, so the reboot task waits for a GPU test command to pass or the timeout to expire.](./img/p2-0408-wait-gpus.svg)

*Figure 4.8.12. After a reboot, the task waits through a short delay and repeats the GPU test until it passes or the timeout expires.*

A reboot can look finished before the GPUs are ready. The operating system answers on the network, and the login prompt appears, but the NVIDIA modules may still be loading. A task that moves on at that point would find no GPUs and fail in a confusing way.

```yaml
- name: Reboot and wait for GPUs
  ansible.builtin.reboot:
    reboot_timeout: 1800
    post_reboot_delay: 30
    test_command: nvidia-smi -L
```

What matters here is `test_command`. It checks the GPUs rather than trusting that the reboot finished. The module keeps running the test until it passes, or until `reboot_timeout` runs out. The `post_reboot_delay` adds a short pause before the first test, which gives slow hardware a moment to settle. Together, the three settings turn "the host answered" into "the GPUs answered".

After any reboot, test the thing you need, such as the GPUs, before you return the node to service.

## 7. Debugging control flow

![A table of control-flow symptoms with their likely causes and fixes.](./img/p4-0408-control-flow-symptoms.svg)

*Figure 4.8.13. Start from the symptom, check the likely cause, and use -vv or the debug strategy to see which branch ran.*

A task is skipped, or a handler never runs, and the playbook looks correct. Control-flow bugs are about which path the run took. The steps below show how to read the run output and find the branch that surprised you, without guessing at the cause. Each symptom in the table points to one kind of cause, so you can check the likely cause first.

Control-flow bugs rarely announce themselves. A handler silently does not run, or a task silently skips. Start from the symptom in the table, then check the likely cause. Read the table as a list of questions. If the handler never ran, ask whether the task reported a change. If the task skipped, ask which condition was false.

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

When a task is skipped unexpectedly, run it with `-vv`, because that output shows `false_condition`. The `false_condition` line quotes the expression that evaluated to false, so you see the exact rule that turned the task off. The `debug` strategy goes further. Set `strategy: debug`, or `ANSIBLE_STRATEGY=debug`, and Ansible drops into an interactive debugger when a task fails. From there you can run `p task_vars`, `p result._result`, `task.args`, `redo`, `continue` and `quit`. Those commands let you look at the failure as it stands, change an argument, and try the task again without starting the whole run over. You can also use `ansible-playbook -vv`, `--step` and `--start-at-task`. `--step` asks before each task, and `--start-at-task` skips straight to the task you care about. See 4.10 for more.

Start with `-vv` on the failing run, because it shows which condition turned a task off. If the output is still unclear, move to the debugger. Use the debugger when you need to see the state at the moment of failure, and use `-vv` when you only need to know which rule fired.

## 8. Lab

Start on your own machine. Run the self-checking Python lab, `code/part04/ansible_control_flow_lab.py`, before you touch any hosts. The lab is a rehearsal. It runs the same logic in a safe place, so a mistake costs a line of output instead of a node. It checks *Ansible: Up and Running* Chapter 10's custom `FilterModule` (`surround_by_quotes`). It also checks Chapter 11's handler `listen:` topic fan-out, and the "lost handler after failure" case, comparing it with `force_handlers: true` (`simulate_handler_listen_and_failure_loss`). Last, it runs the `block`/`rescue`/`always` GPU node maintenance flow (`simulate_block_rescue_always_maintenance`).

```bash
python3 code/part04/ansible_control_flow_lab.py
```

Next, move to a control node with 2–3 Linux targets. The interactive shell steps below were not run on live hardware, so expect small differences on your own setup. Work through these exercises in order. Each one builds on the idea of the one before it, and the first one sets up the handler behaviour that the later ones depend on:

1. Test handlers. Notify a restart from two tasks, and verify that only one restart happens. Use `listen` topics. Then reproduce the "handler lost after failure" case by failing a later task. Fix it once with `force_handlers` and once with `meta: flush_handlers`.
2. Break a restart storm. Make a template non-idempotent by adding a timestamp, and watch the service restart on every run. Then fix it.
3. Test conditionals. Gate tasks by group membership, OS family, facts and registered results. Reproduce the string-boolean bug using `-e flag=false`, and fix it with `| bool`.
4. Test loops. Create users from a list of dicts with `loop_control.label`. Register the loop results and summarise the failures. Implement `until` polling on a flaky service. Then compare the run time of a loop with the run time of a list-argument `package` task.
5. Check failure semantics. Write tasks whose `rc` of 1 is acceptable, as `grep` produces, and handle them with `failed_when`. Compare `ignore_errors` with `failed_when`. Then check the recap and the exit codes.
6. Test `block`, `rescue` and `always`. Implement the driver upgrade with rollback against a fake installer script that fails on one host. Make the `rescue` re-raise the failure, and then verify the `always` diagnostics.
7. Test fleet policies. Use `serial`, `max_fail_percentage` and `any_errors_fatal` on six hosts with injected failures. Document when the play aborts in each case.
8. Compare imports and includes. Restructure your tasks into separate files. Compare `--list-tasks`, `--tags` and loops between `import_tasks` and `include_tasks`. Then use `apply: tags`.
9. Run the drain flow. Simulate Slurm with scripts, or use a real Slurm lab. Run the drain, change, validate and resume play with an injected validation failure, and confirm that the node stays drained.
10. Use the debugger. Trigger a failure under `strategy: debug`, inspect `task_vars`, fix a variable, and then `redo` the task.
11. Clean up when you are done.

## 9. Common mistakes

Control-flow mistakes hide in plain sight. A handler that never fires, a `when` that is always true, or a block that swallows an error. Check each one against the run output, not against your memory of what the playbook was supposed to do. Memory tends to describe the intent, and the run output shows what actually happened.

You might expect handlers to run when the notifying task did not change, or after a failed play. That is a common mistake. Handlers follow changes, not intentions. So is writing `when: "{{ var }}"`, which puts templating inside a conditional and invites string-boolean confusion. Write the bare expression instead, as `when: var`, so the condition is evaluated once, as a real test. Leaving out `changed_when` on commands that notify handlers is another, because the command then always reports `changed`, and the handler restarts a service on every run.

Using `ignore_errors: true` as a default is a mistake, and so is a rescue block that swallows failures. Loops of single-item package installs, and heavy loops over many hosts and items, waste time. Each extra call costs a round trip and a package-manager pass. Using `pause` instead of polling a real condition is also a mistake, for the reasons the retries section gave.

Mixing `include_*` with expectations about tags or `--list-tasks` causes surprises. Returning drained nodes to service in an `always:` section, whatever the validation result, is dangerous, because it puts a bad node back under the scheduler. Assuming `serial` guards against every failure, without `max_fail_percentage` and validation steps, is a mistake. `serial` limits how many hosts run at once, but it does not judge whether the change worked. Forgetting that registered variables from skipped tasks lack fields is also a mistake. Using `any_errors_fatal` everywhere lets a single flaky host halt the fleet, and using it nowhere lets a bad change spread. The right setting sits between those two, and it depends on how dangerous the step is.

Check each of these before you ship a playbook that touches a fleet.

## 10. Interview angles

Interviewers ask about handlers, conditionals and error handling because those are where real playbooks go wrong. Explain what each one does on the second run as well as on the first.

Use these questions to test yourself. Answer each one in your own words before you check the section that covers it. A good answer explains what happens on the first run and on the second run, because the second run is where most control-flow bugs show up.

- "How do handlers work? When do they not run? How would you guarantee a restart after a partial failure?"
- "Explain `block`, `rescue`, `always` and how a rescued failure is reported."
- "`failed_when`/`changed_when` vs `ignore_errors`."
- "Static vs dynamic includes: differences and consequences for tags and `--list-tasks`."
- "How do you perform a rolling update with a canary and automatic stop on failure?"
- "How do you wait for a node to rejoin the cluster after reboot?"
- "What causes a handler to run on every run?"
- "How do you debug a playbook that skips a task?"

## Exercises

Work through these exercises in order. Each one names the function or playbook you will use.

1. A dcgm-exporter config changed on Run 1, but a later task failed, so the handler never restarted the service. Why does Run 2 not restart it either? Which of the three fixes would you choose for this node, and why? Use `simulate_handler_listen_and_failure_loss()` in `code/part04/ansible_control_flow.py` to check your reasoning.
2. A teammate runs `-e flag=false`, and a task guarded by `when: flag` runs anyway. Why does the condition see a true value? Which filter fixes it? How would you guard a `when:` check on a registered variable whose task might have been skipped?
3. A nested include loops over virtual hosts, and the inner loop overwrites the outer `item`. Which `loop_control` setting renames the outer variable? What does `register` hold after a loop, and how would you count the failures in it?
4. A driver upgrade installs the new package, then fails on one host. Which section runs first after the failure? Why does `always` still collect diagnostics? Why must `scontrol State=RESUME` stay out of `always:` on GPU nodes? Use `simulate_block_rescue_always_maintenance()` in `code/part04/ansible_control_flow.py` to trace it.
5. Your OS-specific task file name depends on a fact. Should it be an import or an include? What does `--list-tasks` show for each choice?
6. A maintenance play upgrades GPU nodes in batches, and a Slurm controller drains each one. Which `serial` value makes the first batch a single node? Why does the drain command use `delegate_to` on the controller?

## Checkpoint questions (20)

<details>
<summary>1. Why does a handler get "lost" if a subsequent task fails during Run 1, and why doesn't simply re-running the playbook in Run 2 trigger the handler?</summary>

Suppose Task 1 (`template: dest=/etc/default/dcgm-exporter`) changes the file on `gpu01` and notifies `Restart dcgm-exporter`. Then Task 2 fails on `gpu01`.
- **On Run 1:** `gpu01` fails in Task 2, before the end-of-section handler flush. Ansible drops `gpu01` and skips its pending handlers, so `dcgm-exporter` keeps running with the old configuration in memory.
- **On Run 2, after you fix Task 2:** Task 1 compares the template with `/etc/default/dcgm-exporter`. The file on disk already matches from Run 1, so Task 1 reports `ok` with `changed=false`. The handler is not notified on Run 2 either.

Fix this with `force_handlers: true` on the play, with `meta: flush_handlers` right after the critical config tasks, or with an idempotent task that checks the service uptime against the config file `mtime`.
</details>

<details>
<summary>2. How does the `listen:` keyword on handlers decouple notifications across roles and tasks (*Ansible: Up and Running*, Chapter 11)?</summary>

Instead of a task naming three separate handlers in `notify:`, the handlers can subscribe to a shared topic. Each one sets `listen: "Reload systemd and restart dcgm-exporter"`, or `listen: Ssl_certs_changed` as in *Ansible: Up and Running*, Chapter 11. Handlers can even come from different roles. When a task notifies that topic string, every handler listening to it runs, in the order the handlers are defined in the play.
</details>

<details>
<summary>3. Why does passing `-e some_flag=false` on the command line cause `when: some_flag` to evaluate to `True`?</summary>

Extra variables passed as `key=value` on the command line, such as `-e some_flag=false`, arrive as strings, not YAML booleans. The JSON form, `-e '{"some_flag": false}'`, keeps a real boolean. In Python and Jinja2, any non-empty string counts as true, and that includes `"false"`, `"no"` and `"0"`. So `when: some_flag` treats the string as true. Whenever a variable might arrive as a string, from `-e`, an environment lookup or an INI inventory, write `when: some_flag | bool`.
</details>

<details>
<summary>4. How are multiple items in a `when:` list combined, and how do you safely check a registered variable from a task that might have been skipped?</summary>

- **List items in `when:`** are combined with logical **`AND`**:
  ```yaml
  when:
    - "'gpu' in group_names"
    - ansible_facts['os_family'] == 'Debian'
  ```
- **Skipped registered variable:** A skipped task still gets its `register:` variable, but that variable is `{"changed": false, "skipped": true}`, with no `stdout`, `stderr` or `rc` keys. Reading `res.stdout` directly raises an `UndefinedError`. Guard it with `when: res is not skipped and 'text' in res.stdout`, or with `res.stdout is defined`.
</details>

<details>
<summary>5. How does `register` work when combined with `loop:`, and how do you inspect per-item failures?</summary>

When a task uses both `loop:` and `register: loop_reg`, Ansible stores a dictionary with a `results` list, at `loop_reg.results`. Each element is the return dictionary for one iteration, and it includes `"item": <loop_item>`. To pull out the exit codes, use `{{ loop_reg.results | map(attribute='rc') | list }}`. To see only the failed items, use `{{ loop_reg.results | selectattr('failed', 'defined') | selectattr('failed') | list }}`.
</details>

<details>
<summary>6. Why do nested `include_tasks` loops overwrite `{{ item }}`, and how does `loop_control: { loop_var: ... }` fix it (*Ansible: Up and Running*, Chapter 10)?</summary>

By default, each `loop:` puts its current element in a variable called `item`. Suppose a playbook loops over `[vhost1, vhost2]` and calls `include_tasks: vhost-tasks.yml`. If that file also loops, over `[logs, public_http, public_https]`, the inner loop overwrites `item` and hides the outer virtual host dictionary. Setting `loop_control: { loop_var: vhost }` on the outer `include_tasks` loop renames the outer variable to `vhost`. Then `{{ vhost.domain }}` and the inner `{{ item }}` never collide.
</details>

<details>
<summary>7. How do you write a custom Jinja2 Filter Plugin (`filter_plugins/surround_by_quotes.py`) in Ansible (*Ansible: Up and Running*, Chapter 10)?</summary>

Create a Python file inside a `filter_plugins/` directory next to your playbook, or inside a role or collection. In that file, define a class named `FilterModule` with a `filters(self)` method. The method returns a dictionary that maps filter names to functions. The pattern looks like this:
```python
class FilterModule:
    @staticmethod
    def surround_by_quotes(a_list):
        return ['"%s"' % x for x in a_list]

    def filters(self):
        return {'surround_by_quotes': self.surround_by_quotes}
```
Playbooks and templates can then pipe any list into `{{ domains | surround_by_quotes | join(', ') }}`.
</details>

<details>
<summary>8. In *Ansible: Up and Running*, Chapter 10, how does `changed_when` make modules like `django_manage` or `command` report accurate change status?</summary>

Some commands and framework wrappers exit with `rc=0` whether they created new state or did nothing. Take `django_manage` with `command="createdb --noinput"`, or `scontrol`. By inspecting the registered output (`register: result`), you can tell a first run from a second one. Set `changed_when: "'Creating tables' in result.out"`, and the task reports `changed` only when tables were actually created. On later idempotent runs, it reports `ok`.
</details>

<details>
<summary>9. How do `block`, `rescue`, and `always` work, and what special variables are available inside `rescue:`?</summary>

- **`block:`** groups tasks that share keywords, such as `when`, `become` and `tags`. It works like a `try` clause.
- **`rescue:`** runs only if a task inside `block:` fails. Two special variables are available inside it: `ansible_failed_task`, the task object that failed (`{{ ansible_failed_task.name }}`), and `ansible_failed_result`, the full return dictionary of that task (`rc`, `stdout`, `stderr`, `msg`).
- **`always:`** runs after `block:` every time, and after `rescue:` if `rescue:` ran. It works like `finally:`.
</details>

<details>
<summary>10. Why does a play report `failed=0` (`rescued=1`) when a `rescue:` block finishes normally, and how do you keep the host marked as failed after rolling back?</summary>

When every task in `rescue:` succeeds, Ansible counts the error as recovered. The recap shows `rescued=1, failed=0`, the exit code is 0, and the play carries on along that host. In a fleet upgrade, where `rescue:` rolled back a broken driver, carrying on or returning a green exit code is dangerous. Instead, end the `rescue:` block with an explicit **`ansible.builtin.fail`** task, such as `msg: "Driver upgrade failed on {{ inventory_hostname }}; rolled back; node left drained"`. The rollback still runs, `always:` still collects logs, and the host stays marked as failed.
</details>

<details>
<summary>11. Why did *Ansible: Up and Running*, Chapter 10's web-app example put "Re-add server to load balancer" in `always:`, whereas our GPU node maintenance playbook puts `scontrol State=RESUME` AFTER the `block`/`rescue`?</summary>

- In a rolling-upgrade example, the `rescue:` block reverted the VM to a known-good pre-upgrade snapshot, `cs_vmsnapshot: state=revert`. The web server was therefore healthy again before `always:` re-added it to the load balancer.
- A bare-metal GPU node cannot be reverted with a hypervisor snapshot. If a failed driver or firmware update, or a failed `nvidia-smi` validation, put the node back into Slurm with `State=RESUME` in `always:`, it would become a "black hole" node. It would crash every multi-node training job scheduled onto it. So on GPU nodes, `rescue:` leaves the node `DRAIN`ed and fails, and `State=RESUME` runs only after the `block` succeeds.
</details>

<details>
<summary>12. Compare `meta: end_host`, `meta: end_play`, `meta: end_batch`, and `meta: clear_host_errors`.</summary>

- **`meta: end_host`** cleanly stops the play for this one host, when a `when:` triggers it. The host is not marked as failed or skipped in the recap.
- **`meta: end_batch`** ends the current `serial` batch early and moves on to the next batch.
- **`meta: end_play`** ends the play for all hosts at once, with exit code `0`.
- **`meta: clear_host_errors`** clears the failed state of hosts, so later plays can target them.
</details>

<details>
<summary>13. Contrast Static `import_tasks` / `import_role` with Dynamic `include_tasks` / `include_role`.</summary>

The two kinds differ in when they are processed, and that changes how tags, loops and conditions behave.

| Feature | `import_tasks` / `import_role` (Static) | `include_tasks` / `include_role` (Dynamic) |
|---|---|---|
| **When processed** | Pre-processed once at **playbook parse time** | Processed dynamically at **runtime** as execution reaches it |
| **`--list-tasks` & `--start-at-task`** | Imported tasks are visible in `--list-tasks` and targetable | Hidden until runtime |
| **`when:` behaviour** | Copied onto **every** individual task inside the imported file | Evaluated once on the `include_*` statement itself to decide whether to load the file |
| **`tags:` behaviour** | Copied onto **every** task inside the imported file | Tags on `include_*` only select the include step itself (use `apply: { tags: [...] }` to push tags to inner tasks) |
| **Loops (`loop:`) & fact-based filenames** | **Cannot** use `loop:` or fact variables in the filename | **Supports `loop:`** and runtime filenames (`"{{ ansible_facts['os_family'] }}.yml"`) |
</details>

<details>
<summary>14. How do you pass tags down to every task inside a dynamic `include_tasks` or `include_role` call?</summary>

Put the **`apply:`** keyword inside the `include_tasks` or `include_role` arguments. Tag the include statement itself as well, or tag it `always`:
```yaml
- name: Dynamically include GPU validation tasks
  ansible.builtin.include_tasks:
    file: validate_gpu.yml
    apply:
      tags: [validate]
  tags: [validate]
```
</details>

<details>
<summary>15. How do you wait for a Slurm node to finish running jobs before starting disruptive maintenance in Ansible?</summary>

First set the node to `DRAIN`, with `scontrol update NodeName={{ inventory_hostname }} State=DRAIN Reason="..."` delegated to `groups['slurm_controller'][0]`. This stops new jobs from starting on the node, while active jobs keep running until they finish. Then poll `squeue` with **`until:`**:
```yaml
- name: Wait until all Slurm jobs drain from node
  ansible.builtin.command: "squeue -h -w {{ inventory_hostname }} -o %i"
  delegate_to: "{{ groups['slurm_controller'][0] }}"
  register: active_jobs
  until: active_jobs.stdout == ""
  retries: 120
  delay: 30
  changed_when: false
```
</details>

<details>
<summary>16. How does `ansible.builtin.reboot` verify that a GPU node is truly ready after a kernel or driver reboot?</summary>

By default, `reboot` reconnects over SSH and runs `whoami`. That succeeds as soon as `sshd` starts, which can happen before the NVIDIA kernel modules or the PCIe bus have finished initializing. Add `test_command: nvidia-smi -L`, along with `reboot_timeout: 1800` and `post_reboot_delay: 30` for long server BIOS POST times. Then `reboot` keeps polling until `nvidia-smi -L` exits `0` on the rebooted host.
</details>

<details>
<summary>17. In *Ansible: Up and Running*, Chapter 11, how do `delegate_to: localhost` and `run_once: true` solve downloading artifacts onto servers that have no internet access?</summary>

Suppose the target servers sit in an isolated data-center VLAN with no internet access. The control node or a bastion can reach external mirrors through an HTTP proxy. A task with `delegate_to: localhost` and `run_once: true`, plus `become: false` and `environment: { https_proxy: ... }`, downloads the binary once onto the control node, with `get_url: url=... dest=/tmp/goss`. The very next task uses `copy: src=/tmp/goss dest=/usr/local/bin/goss mode='0755'` to send it over SSH to all target hosts.
</details>

<details>
<summary>18. Why should you never replace `wait_for` or `until` polling with a fixed `pause: { seconds: 60 }`?</summary>

A fixed `pause: { seconds: 60 }` is both too slow and too fragile. If a service restarts in 2 seconds, the playbook wastes 58 seconds doing nothing. If a heavy node or a cold cache takes 65 seconds to start, the playbook moves on at 60 seconds and fails. Poll the real readiness condition instead. Use `wait_for` to check for an open TCP port, a file, or a regex in a log, or use `uri` or `command` with `until:`, `retries:` and `delay:`.
</details>

<details>
<summary>19. How does the interactive `debug` strategy (`strategy: debug` or `ANSIBLE_STRATEGY=debug`) work when a task fails?</summary>

When a play sets `strategy: debug`, or `ANSIBLE_STRATEGY=debug` is set, Ansible pauses as soon as a task fails. It opens an interactive `(debug)` prompt on the control node. The same applies when `debugger: on_failed` is set on a play, block or task. From the prompt, you can inspect the failure and the variables, for example with `p result._result`, `p task.args` or `p task_vars['nvidia_driver_branch']`. You can also change arguments or variables in memory, such as `task.args['name'] = 'chrony'`. Then type **`redo`** to run the task again on the spot, or **`continue`** or **`quit`**.
</details>

<details>
<summary>20. Summarize the six layers of defense in a production-grade fleet rollout playbook.</summary>

1. **Pre-flight `assert` gates (`pre_tasks`):** Check the required variables, the supported OS and hardware, and the change ticket before you touch any host.
2. **Progressive batching (`serial: [1, "10%", "25%"]`):** Test a 1-node canary first, before you expand the batch size.
3. **Scheduler or load-balancer drain (`scontrol State=DRAIN` with a `squeue` poll):** Evacuate workloads gracefully before you change the node.
4. **Structured `block` / `rescue` / `always`:** Roll back on failure, collect `journalctl` diagnostics in `always`, and leave failed nodes `DRAIN`ed.
5. **Active post-change validation (`nvidia-smi`, DCGM, NCCL):** Prove that the hardware and services are healthy before you run `State=RESUME`.
6. **Fleet circuit breaker (`max_fail_percentage: 5`):** Stop the line automatically if batch failures exceed the threshold.
</details>

## Sources and review notes

- **Sources read in full:**
  - `ansible-up-and-running-3rd-edition` — Bas Meijer, Lorin Hochstein & René Moser, *Ansible: Up and Running*, 3rd ed., **Chapter 10: Making Playbooks Appear More Complex** (read in full: `changed_when` and `failed_when` on `django_manage`, custom filter plugins `FilterModule.surround_by_quotes` in `filter_plugins/surround_by_quotes.py`, filepath filters `basename`/`dirname`/`expanduser`/`realpath`, lookups `file`/`pipe`/`env`/`password`/`csvfile`/`dig`/`redis`, looping constructs `loop`/`with_items`/`with_lines`/`with_fileglob`/`with_dict`/`with_subelements`, `include_tasks` with `loop_control: { loop_var: vhost }`, `block`/`rescue`/`always` in `app-upgrade.yml` with `cs_loadbalancer_rule_member` and `cs_vmsnapshot`, and `ansible-vault` `encrypt`/`decrypt`/`view`/`edit`/`rekey` and `vault_identity_list`) and **Chapter 11: Execution Strategies and Flow Control** (read in full: `linear` vs `free` vs `debug` strategies, host patterns, `delegate_to` with Nagios/ELB and `run_once: true` proxy downloads, `import_tasks`/`include_tasks` and `import_playbook`, and handler chaining and `listen: Ssl_certs_changed` topic fan-out).
- **Run here:** `python3 code/part04/ansible_control_flow_lab.py` (3 passed, 0 failed).
- **Explicitly labelled inferences:** The `simulate_handler_listen_and_failure_loss` and `simulate_block_rescue_always_maintenance` models in `code/part04/ansible_control_flow.py` and the Section 4 & 6 GPU driver rollback (`systemd_service`) and Slurm drain/validate/resume (`scontrol update`, `squeue -w`) playbooks are the author's constructions applying *Ansible: Up and Running* Chapters 10 & 11 to GPU cluster operations (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, and 35).
- **Not verified on live hardware:** Live `ansible-playbook`, `scontrol`, `squeue`, `systemctl`, and `reboot` commands (`5.15`, `9400`, `1800`s, `120` retries, `10.0.2.2`, `10.0.2.15`, `192.168.33.10`, `6379`) are marked as not run in this chapter where `ansible_control_flow_lab.py` does not execute them.
