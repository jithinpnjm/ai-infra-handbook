# Voice sample 5: parts part-04-automation, part-12-ai-networking

## FILE docs/part-04-automation/01-git-from-scratch-for-infrastructure-engineers.md

In an AI factory, almost everything that matters is, or should be, text in a repository. That includes Terraform that creates networks and GPU VMs, Ansible roles that install drivers and tune kernels, Slurm configuration, Kubernetes manifests and Helm values, Dockerfiles for training images, CI pipelines and runbooks. Git is the evidence trail for all of it. It tells you who changed the NCCL settings, when the MTU went from 9000 to 1500, which commit introduced the regression that halved training throughput, and how to go back. A cluster that cannot be rebuilt from Git is a pet, and a change that did not pass through review is an incident waiting to happen. This chapter teaches Git from the object model up. Then it covers the workflows that infrastructure teams use, namely trunk-based development, review, rebase and recovery, and it connects Git to CI/CD (4.2) and GitOps (4.26).

---

Trunk-based development fits infrastructure better. Branches are short-lived and merge back to `main` within a day or two, and `main` stays deployable at all times. Incomplete work hides behind feature flags or variables, and environments differ by configuration rather than by branch. The repository then mirrors reality, every change is small and easy to review, and rollback is a `revert`. CI promotes the same commit through each environment. Cut a release branch only when you must maintain several supported versions at once, such as an internal Helm chart or Ansible collection that many teams consume.

---

Model environments as directories or variable files, not as branches, as in `envs/staging` and `envs/prod`. Separate `staging` and `prod` branches drift apart, and then cherry-picks turn into folklore. To promote a change, edit the version pin in the prod directory and send it through a reviewed commit. If you are choosing a model, pick trunk-based development and keep each environment in its own directory. With that setup, the repository tells you what is deployed.

---

The reflog is your local safety net. Git records every movement of `HEAD` and of the branch tips. By default, reachable entries are kept for about 90 days, and unreachable entries for 30 days. Suppose you run `reset --hard` by mistake. `git reflog` then shows `HEAD@{1}: commit: ...`, and `git branch rescue HEAD@{1}` recovers the commit. The reflog is local only, and it does not survive a fresh clone. Treat it as a seat belt, not a backup.

---

## FILE docs/part-04-automation/02-ci-cd-pipelines-concepts-and-design.md

Rollback policy depends on what you are changing. For stateless pieces, revert the change and redeploy. For stateful pieces, prefer a roll-forward with a prepared fix, backed by backups and a restore procedure you have tested. Document any change that cannot be reversed.

---

A few design rules hold across all of these tools. Only a merge to the protected branch may apply. The applied plan must match the commit that was reviewed. Use concurrency groups for each environment or state. Keep secrets out of pull request comments by masking outputs and marking sensitive values. Fork pull requests must never receive credentials.

---

For secrets, fetch values at run time from a secret manager such as Vault or a cloud secret manager, using the OIDC identity. Use masked variables only when you cannot avoid them, and never print them. Remember that values read into Terraform data sources land in the **state file**. The state backend is therefore a secret store, so you must encrypt it and control access to it (4.19, 4.22). For secrets that live in Git, use SOPS with KMS or age, or sealed secrets (4.12).

---

Schedule rollouts inside a maintenance window. A rollout should never drain more than the SLO allows, and every step should be recorded for the post-incident timeline. Firmware and BIOS changes need extra care. Stage them by hardware generation, keep the previous version available, and confirm the BMC is reachable before and after the change (Part 7).

---

## FILE docs/part-04-automation/03-ansible-from-zero-what-it-is-how-it-works-installation-and-ad-hoc-comm.md

Ansible is not a continuous reconciliation loop. It acts when you run it, unless a scheduler, `ansible-pull` or AAP triggers it. It is also not a provisioning engine with state, like Terraform. It has no state file and learns the state of a host by inspecting it on every run. Keep complex programming logic out of playbooks and push it into modules instead.

---

Connection reuse saves round trips. SSH **ControlMaster** and **ControlPersist** let many commands share one connection. **Pipelining**, set with `pipelining = True`, streams the module over stdin and cuts SSH round trips. It requires `requiretty` to be off in `sudoers`. Together these two settings are the biggest easy speed-ups.

---

Prefer purpose-built modules such as `package`, `service`, `user`, `file`, `lineinfile`, `template`, `sysctl`, `systemd`, `mount` and `cron`. They are idempotent, support check mode and return structured results. A shell one-liner in a playbook always reports `changed`, cannot be dry-run and hides intent. If you cannot avoid one, add `creates` or `removes`, a guard task, or `changed_when` and `failed_when` expressions.

---

Interviewers often start with the basics. Ask yourself, "What does agentless mean? What happens when `ansible-playbook` runs a task?" Your answer should cover SSH, the module payload, the JSON result and the cleanup. A related question compares tools: "Ansible versus Terraform; versus Puppet/Chef/Salt." That answer contrasts procedural push configuration with declarative stateful provisioning and with agent-based convergence.

---

## FILE docs/part-04-automation/04-yaml-and-jinja2-for-infrastructure-code.md

A YAML file looks like plain text, but a parser turns each value into a typed object before any tool reads it. Those types are the source of several traps. YAML ("YAML Ain't Markup Language") is a human-friendly serialisation format, which means a way of writing data as text. In practice it is a superset of JSON, because JSON is valid YAML 1.2. So `{"a": 1}` works anywhere YAML does. Every YAML file is built from three structures, shown in the table below.

---

Anchors (`&name`) mark a node, and aliases (`*name`) reuse it. The merge key `<<` merges one mapping into another. It is a YAML 1.1 convention that PyYAML and Kubernetes tooling support. It is not part of the YAML 1.2 core, and not every parser honours it. The example below shows the idea.

---

The `ansible.builtin.template` module renders on the control node and copies the result to the target. Its options include `owner`, `group`, `mode`, `backup`, `variable_start_string` for different delimiters, and `validate: "visudo -cf %s"`. The `validate` option checks the file before it is installed, which is essential for sudoers, sshd and nginx. The `{{ ansible_managed }}` variable gives you a "do not edit" header.

---

Untrusted data is the main risk when templates are involved. Never render a user-provided string as a template, because that opens the door to server-side template injection. Ansible marks values from facts as "unsafe", which stops them from being templated again. Do not remove that `!unsafe` marking, and avoid `eval`-like constructs.

---

## FILE docs/part-04-automation/05-ansible-inventory-hosts-groups-dynamic-inventory-and-variables.md

Set `inventory = inventory` in `ansible.cfg`, where `inventory/` is a directory. Suppose that directory holds `vagrant.py`, `aws_ec2.yml` (`plugin: aws_ec2`), `gcp.yml` (`plugin: gcp_compute`), `azure_rm.yml` (`plugin: azure_rm`, `plain_host_names: true`), `group_vars/` and `host_vars/`. Ansible then runs and merges **every** static file, dynamic script and inventory plugin in that directory into one unified inventory.

---

At thousands of hosts, scale starts to matter. Avoid per-host `--host` script calls by returning `_meta`. Use `keyed_groups` and caching, split the inventory into several sources, and raise `forks`. Choose `strategy: free` or `serial` on purpose, as chapter 4.14 covers. When a host belongs to many groups, set `ansible_group_priority` and use consistent names, so the result stays unambiguous.

---

Most inventory trouble comes from a few habits. A giant flat inventory repeats the same variables on every host, and `host_vars` sprawls as a result. Variables placed in role `vars/` are hard to override, and you may reach for `-e` to "fix" precedence problems. Storing shared secrets in plaintext inventory files is a mistake, and so is putting `ansible_password` in vars.

---

1. Use `expand_inventory_range()` in `code/part04/ansible_inventory_model.py` to explain three things from *Ansible: Up and Running*, chapter 4. First, why listing `127.0.0.1:2222`, `127.0.0.1:2200` and `127.0.0.1:2201` without aliases collapses to a single host (`Example 4-5`). Then show how the `vagrant1..3` aliases with `ansible_host` solve it. Second, how zero-padded numeric ranges such as `gpu[001:032]` and alphabetic ranges such as `web-[a:t]` work. Third, what `ansible_connection`, `ansible_shell_type` and the implicit `localhost` are for.
2. Explain how `--limit` combines with the `hosts:` pattern you set on a play. Then explain the intersection in `gpu:&rack_r01`, the exclusion in `gpu:!gpu_a100`, the group slice in `gpu[0:2]`, and what `--limit @failed_hosts.txt` does. Finally, decide when `order: sorted` fits a play better than `order: shuffle`.
3. Use `resolve_variable_precedence()` in `code/part04/ansible_inventory_model.py` to explain three things. First, how splitting `group_vars/prod/` into a directory with `main.yml` and `vault.yml` works, or with `db` and `rabbitmq`, as in *Ansible: Up and Running*, chapter 4. Second, why role `defaults/main.yml` and role `vars/main.yml` behave differently next to inventory `group_vars/`. Third, why overriding a dictionary in `host_vars/` wipes out sibling keys unless you merge it with `combine(recursive=True)`.
4. Contrast `ansible.builtin.group_by` with `ansible.builtin.add_host`. `group_by` partitions existing hosts into dynamic groups, such as `Ubuntu` or `gpu_model_h100`, based on gathered facts. `add_host` registers a newly provisioned VM IP in an in-memory group during a run. Then explain where `meta: refresh_inventory` fits, in *Ansible: Up and Running*, chapter 4.
5. Using `parse_vagrant_machine_readable_inventory()`, explain two things. First, how `keyed_groups`, `groups`, `compose`, `filters` and `cache` work in the cloud and NetBox plugins, such as `gcp_compute`, `aws_ec2`, `nb_inventory` and `constructed`. Second, the JSON contract for custom inventory scripts, such as `vagrant.py` and `slurm_inventory.py`, meaning `--list` versus `--host <name>`. Then explain why including `_meta.hostvars` is essential on a 5,000-node cluster.
6. Suppose you must design an inventory group hierarchy for a 512-GPU cluster. The cluster spans H100 and GB200 nodes across 16 racks, with out-of-band Redfish BMCs. Then write an `assert` task that checks the required per-host metadata (`rack`, `bmc_address`, `gpu_count` and `ib_hcas`) before any disruptive role runs.

---

## FILE docs/part-04-automation/06-ansible-playbooks-tasks-modules-idempotency-and-check-mode.md

The fourth pattern is handler deduplication. Four tasks all carry `notify: Restart nginx`: `Copy TLS files`, `Manage nginx config template`, `Enable configuration` and `Install home page`. Even if all four report `changed` on the first run, Ansible deduplicates the notifications. It runs the `Restart nginx` handler once, at the end of the `tasks` phase and before `post_tasks`. On the second run, when all four tasks report `ok`, the handler runs zero times. This behaviour is tested in `code/part04/ansible_playbook_execution_lab.py`.

---

Most keywords can be set at the play, block or task level, and they pass down to the levels below. Examples include `become`, `environment`, `tags`, `when`, `vars` and `ignore_errors`. Run `ansible-doc -t keyword -l` to see the full list. Name tasks as desired states, such as "Ensure X is Y", rather than as actions.

---

1. Build a multi-play playbook. Create `site.yml` with `pre_tasks`, `roles` (empty), `tasks`, `post_tasks` and handlers. Then use `debug` tasks and `--list-tasks` to watch the order of execution.
2. Take a tour of the modules. Give each of `package`, `service`, `user`, `file`, `copy`, `lineinfile`, `blockinfile`, `template`, `stat`, `get_url` (with checksum), `unarchive`, `sysctl`, `cron` and `wait_for` one task. Run the playbook twice. The second run should confirm `changed=0`.
3. Make the playbook idempotent. Start from a naive playbook that uses `shell: echo "x" >> file` and `command: useradd`. Refactor those into `lineinfile` and `user`. For the one command that remains, add `creates`, `changed_when` and `failed_when`.
4. Check and diff. Run `--check --diff` on a templated file change. Show a `command` task being skipped, and mark a read-only probe with `check_mode: false`. Then demonstrate a dependent task failing in check mode, and fix it with `when: not ansible_check_mode`.
5. Fall into the idempotency trap on purpose. Put `{{ ansible_date_time.iso8601 }}` into a template, and watch every run report a change and trigger handlers. Then remove it.
6. Control execution. Use `--tags/--skip-tags`, `--limit`, `--start-at-task` and `--step`. Add `always` and `never` tags. Try `serial: [1, 50%, 100%]` on 6 hosts, and print the batch composition with `ansible_play_batch`.
7. Test the failure policy. Make one host fail on purpose. Compare `any_errors_fatal`, `max_fail_percentage`, `ignore_errors` and `force_handlers`. Record each exit code with `echo $?`.
8. Try delegation and async. Use `delegate_to: localhost` to write per-host results to the control node. Run a 60-second command with `async/poll`, then run it again with `poll: 0` plus `async_status`.
9. Build a retry. Write a task that polls a service with `until/retries/delay`. Stop the service to see the retry output.
10. Run a canary rollout. Implement the worked example against containers. Inject a validation failure on the canary, and confirm that the play halts.
11. Lint the playbook. Run `ansible-lint`, and fix the FQCN, naming, `command-instead-of-module`, `no-changed-when` and `risky-file-permissions` findings.
12. Clean up.

---

1. Start with the phase order, `pre_tasks -> roles -> tasks -> post_tasks`, and handler deduplication, as covered in *Ansible: Up and Running*, Chapter 3. Use `simulate_play_execution_and_handlers()` in `code/part04/ansible_playbook_execution.py` to trace the exact order in which `pre_tasks`, `roles`, `tasks`, `post_tasks` and their handler flushes run. Then explain why four tasks that notify `Restart nginx` in `webservers-tls.yml` trigger only a single restart.
2. Look at the core module families you will use most: `package`, `dpkg_selections`, `file`, `copy`, `template`, `lineinfile`, `get_url`, `sysctl`, `systemd_service` and `uri`. Explain how each one checks the current state before it acts. Then explain why `dpkg_selections` with `selection: hold` on `nvidia-driver-550` and `linux-image-generic`, and `state: present` with pinned versions, beat `state: latest` on GPU nodes. Finish by explaining how `webservers-tls.yml` uses `file: state=link` and `uri: return_content=true` with `failed_when`.
3. Make your `command` and `shell` tasks idempotent and safe, using `creates`, `removes`, `changed_when` and `failed_when`. Use `evaluate_command_task_guards()` in `code/part04/ansible_playbook_execution.py` to explain two things. First, explain why embedding `{{ ansible_date_time.iso8601 }}` in a config template breaks idempotency and triggers handler storms. Second, explain how `creates:`, `changed_when: false`, `failed_when:` and `set -o pipefail` (with `executable: /bin/bash`) make these tasks safe.
4. Work through check mode with `--check`, unified diffs with `--diff`, and the per-task `check_mode:` and `diff:` overrides. Explain why `command` and `shell` tasks without `creates` or `removes` are skipped under `--check`. Explain why read-only pre-flight probes, such as `scontrol show node` and `nvidia-smi -L`, must set `check_mode: false` and `changed_when: false`. Then explain how dependent tasks behave in check mode, and why secret tasks must set `diff: false` and `no_log: true`.
5. Trace how the execution controls work together: tags (`always`, `never`), `serial: [1, '10%', '100%']`, `strategy: linear` versus `free`, `throttle`, `delegate_to`, `run_once` and `async`/`poll`. Using `compute_serial_batches()` in `code/part04/ansible_playbook_execution.py`, trace how `serial: [1, "10%", "100%"]` and `max_fail_percentage: 5` implement a progressive canary rollout. Then contrast `strategy: linear` with `strategy: free` and `throttle: 5`. Finish by explaining for yourself how `delegate_to` and `async: 3600` with `poll: 0` or `poll: 15` work.
6. Trace the worked example from Section 7 from start to finish, so you can see how each part connects. Follow the `pre_tasks` that check Slurm `DRAIN` through `delegate_to: "{{ groups['slurm_controller'][0] }}"`, the `tasks` that apply `sysctl` and the `nvidia-persistenced` override, the `handlers` that restart `nvidia-persistenced` with `daemon_reload: true`, and the `post_tasks` that verify the `nvidia-smi` GPU count. Then list what the `ansible-playbook` exit codes `0`, `1`, `2`, `3`, `4`, `5` and `99` mean.

---

## FILE docs/part-04-automation/07-ansible-variables-facts-templates-and-filters.md

Three things make that work. Variables describe what you intend. Facts describe what each host actually is. Templates turn that data into Slurm, NCCL, chrony, netplan or Prometheus configuration. Knowing where a value comes from, and which one wins when two sources disagree, is what separates a playbook that is correct on 1,000 nodes from one that is only correct on your laptop.

---

Play and task `vars` are scoped to the place where they are defined. Inventory, group and host variables apply to each host for the whole run. `set_fact` and `register` create host-scoped variables that stay in place for the rest of the play run. With `cacheable: true` and fact caching enabled, they can also carry over into later runs.

---

The `RealMemory` value is 95 percent of each node's memory, because the template multiplies by `0.95`. For large clusters, compress the node list into Slurm's hostlist syntax, such as `gpu[001-032]`. You can do that with a custom filter or with a precomputed variable.

---

Secrets belong in Vault-encrypted files, or in a secret manager that you query at runtime (4.12). Set `no_log: true` on any task that handles them. Registered results and `-vvv` output can leak secrets too, so keep both in mind. For rendered secret files, set `diff: false`.

---

## FILE docs/part-04-automation/08-ansible-handlers-conditionals-loops-blocks-and-error-handling.md

Picture a fleet change that goes wrong halfway. A config file changes on a GPU node, a later step fails, and the node is left half-configured. Real fleet changes are not straight lines. A service should restart only if its file actually changed. A GPU task should run only on nodes that have a GPU. A node should be drained before you change it, and if the driver install fails, the node must be left in a known state with a clear message.

---

The `rescue` section runs only if a task in the block fails. Here it logs the failed task, rolls back to the previous driver and fails the host with a clear message. The `always` section runs in every case, and it collects kernel log diagnostics.

---

Start on your own machine. Run the self-checking Python lab, `code/part04/ansible_control_flow_lab.py`, before you touch any hosts. It checks *Ansible: Up and Running* Chapter 10's custom `FilterModule` (`surround_by_quotes`). It also checks Chapter 11's handler `listen:` topic fan-out, and the "lost handler after failure" case, comparing it with `force_handlers: true` (`simulate_handler_listen_and_failure_loss`). Last, it runs the `block`/`rescue`/`always` GPU node maintenance flow (`simulate_block_rescue_always_maintenance`).

---

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

---

## FILE docs/part-04-automation/09-a-real-playbook-end-to-end-deploying-an-application.md

Two plays come first. The baseline play runs on every host and prepares the operating system. The database play runs on the `db` group and sets up PostgreSQL, so only the app hosts can reach it. Read the code first, then the notes that follow it.

---

Two details in these plays need your attention. `become_user: postgres` needs the `acl` package for the temporary files that the unprivileged user reads. `no_log: true` hides the password in the output. Real databases also need backups, WAL archiving and monitoring, which are outside this chapter's scope.

---

Four release habits follow from this design. Pin each release to a tag or commit SHA. Build the dependencies from a lock file inside the release directory, so the old release's venv stays intact for rollback. Rollback means setting `app_version` back and running the play again, or repointing `current` by hand and restarting. Because old releases stay on disk, no rebuild is needed: `ansible-playbook playbooks/app.yml -e app_version=v1.4.1`.

---

1. First, compare running `manage.py runserver` or `uvicorn --reload` on a laptop with a production multi-tier deployment: NGINX with TLS and rate limiting, Gunicorn or Uvicorn under systemd or Supervisor, PostgreSQL and Memcached. Then explain why `site.yml` splits the deployment into `baseline.yml`, `database.yml`, `app.yml`, `web.yml` and `verify.yml`, imported with `import_playbook`. This exercise draws on *Ansible: Up and Running*, Chapters 6 and 7.
2. Trace `database.yml` and explain three things. First, why `become_user: postgres` needs the `acl` package on Ubuntu or Debian. Second, why *Ansible: Up and Running*, Chapter 7, passes `encoding='UTF8'`, `lc_ctype='en_US.UTF-8'`, `lc_collate='en_US.UTF-8'` and `template='template0'` to `postgresql_db`. Third, how `listen_addresses`, `pg_hba.conf` (`scram-sha-256`) and `ufw` (`src: "{{ hostvars[item]['ansible_host'] }}"`) limit database access to the `app` group.
3. Using `validate_pinned_version()` and `AtomicReleaseDeployer` in `code/part04/ansible_app_deployment.py`, explain three things you would need to know. Why must `app_version` be a tag or commit SHA rather than `main`? How does building each release in `/opt/fleetapp/releases/v1.4.2/{src,venv}` and atomically switching `/opt/fleetapp/current` allow 5-second rollbacks (`-e app_version=v1.4.1`) without a rebuild? And how are old releases pruned while the last `N=5` are kept?
4. Trace `app.yml`. Explain why `alembic upgrade head` uses `run_once: true`, and why schema migrations must follow the expand/contract pattern during a rolling deploy. Explain why `meta: flush_handlers` must run *before* the `uri` `/readyz` polling loop and the `post_tasks` load-balancer undrain. Then say what `NoNewPrivileges=yes`, `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateTmp=yes` and `ReadWritePaths={{ app_root }}/shared` enforce in `fleetapp.service.j2`.
5. Explain how `nginx-site.conf.j2` generates the `upstream` block from `groups['app']`, and how the TLS settings, `limit_req_zone` and `proxy_buffering off` fit in. Then explain why `proxy_read_timeout 300s` matters for streaming AI and SSE gateways. Explain how `192.168.33.10.nip.io` and `ALLOWED_HOSTS` work in *Ansible: Up and Running*, Chapter 7. Then explain how `verify.yml` proves behavioral correctness beyond module state.
6. Compare the host virtualenv deployment in Section 5 that you built (`git`, `pip` and `systemd`) with the containerized deployment in Section 9. The container version uses `community.docker.docker_container` pinned by `@sha256:{{ app_image_digest }}`, with `read_only: true`, `cap_drop: [ALL]`, `security_opts: ["no-new-privileges:true"]` and `memory: 1g`. Then explain when you would move from Ansible-managed containers to Kubernetes.

---

## FILE docs/part-04-automation/10-debugging-ansible-playbooks.md

A few `ansible.cfg` settings make the output easier to read. `stdout_callback = yaml` shows multi-line values clearly, and newer releases use `result_format = yaml` with the default callback. `callbacks_enabled = timer, profile_tasks, profile_roles` adds timing, and `display_skipped_hosts = false` hides skipped hosts. `log_path = ansible.log` keeps a persistent log, which may hold secrets unless `no_log` is used. Set `ANSIBLE_NOCOLOR=1` in CI logs. For machine-readable output, use `ANSIBLE_STDOUT_CALLBACK=json` or `ansible.posix.json`, which print one JSON document at the end. You can also use `ansible.posix.jsonl`, or send events to a log pipeline.

---

`profile_tasks` prints the slowest tasks and their cumulative time. The usual culprits are fact gathering, which a subset or cache reduces, and `apt update` on every run, which `cache_valid_time` addresses. Others include per-item loops that should be single calls, a `git clone` on every host, and serial execution such as `serial: 1` over a huge group. Slow SSH setup with no `ControlPersist` and reverse DNS in sshd also add up. A single `forks=5` limits parallelism, and `strategy: linear` waits on stragglers, where `strategy: free` suits independent work. A low-quality network or an overloaded control node adds more delay.

---

1. Run `ansible-lint` and `yamllint` in pre-commit and CI, and always run `--syntax-check`.
2. Keep playbooks small, and test one change per run on a canary.
3. Name every task, use `assert` for preconditions, and avoid cleverness in Jinja.
4. Run `--check --diff` before real runs, and add verification tasks after changes.
5. Pin the versions of ansible-core, collections and target packages.
6. Keep `command` and `shell` tasks rare and guarded, and be explicit about `changed_when` and `failed_when`.
7. Avoid `ignore_errors`, and use a targeted `failed_when` instead.
8. When you find a bug, write the failing case as a Molecule test (4.13).

---

1. Classify seven common error messages. Use `classify_ansible_failure_layer()` in `code/part04/ansible_debugging_toolkit.py` to sort each message into its exact layer: Parse/Syntax, Connection `UNREACHABLE`, Data/Template, Privilege/Module, or Application Command. Then state what `-v`, `-vv`, `-vvv` and `-vvvv` each add to the output. This follows the 5-layer method and the verbosity ladder in *Ansible: Up and Running*, chapter 8, through `-vvvvv`.
2. Write a task pair that runs `ansible.builtin.stat` on `/etc/slurm/slurm.conf`. Then use `ansible.builtin.assert` with `quiet: true` to verify `exists`, `isreg`, `pw_name == 'slurm'`, `mode == '0644'` and a non-zero `size`. Finally, explain how `verbosity: 1` on `debug` and `{{ var | type_debug }}` work. Use Table 8-3 in *Ansible: Up and Running*, chapter 8, as your reference.
3. Explain the difference between `task.args['name'] = 'chrony'` and `task_vars['ntp_pkg'] = 'chrony'` followed by `update_task` (`u`) and `redo` (`r`). Use `InteractiveTaskDebuggerSession` in `code/part04/ansible_debugging_toolkit.py` to show it. Cover `strategy: debug`, `debugger: on_failed` and `ANSIBLE_ENABLE_TASK_DEBUGGER` as well. Then list the five `debugger:` trigger values.
4. Work through the SSH failures. First, explain how to resolve `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED` safely with `ssh-keygen -R` and `ssh-keyscan`. Then explain how `authorized_key` with `key_options: 'no-port-forwarding,from="..."'` and `exclusive: true` hardens SSH access. Last, explain why a remote `git` task that uses SSH agent forwarding fails with `Permission denied (publickey)` when `become: true` is set on the task.
5. Reproduce a module run by hand on the target. Walk through the exact commands to keep the temporary `AnsiballZ_*.py` wrapper on a target GPU node, using `ANSIBLE_KEEP_REMOTE_FILES=1`. Then unpack the module source and the `args` JSON file with `explode`, and execute it under `python3` or `pdb` as the target user.
6. Cover two topics. First, explain how `callbacks_enabled = timer, profile_tasks, profile_roles` identifies playbook bottlenecks, and list the six highest-impact speedups. Second, show the shell pipeline that aggregates and ranks `FAILED` and `UNREACHABLE` reasons across a 200-node run.

---

## FILE docs/part-04-automation/11-ansible-roles-and-collections.md

You are about to write a role for the NVIDIA driver, and the first question is where each piece goes. A role is a directory with a fixed layout, and each subdirectory has one job. Once you know the layout, anyone who opens the role can find the part they need. The tree below shows what a driver role looks like on disk.

---

Suppose the driver must run on every GPU node, but only after a drain step on some of them. A `roles:` list alone cannot express that. Ansible offers three ways to call a role, and each suits a different case.

---

Use semantic versioning with a changelog, and bump the major version for breaking changes. Set `requires_ansible` and any deprecations in `meta/runtime.yml`. Document modules in `DOCUMENTATION`, `EXAMPLES` and `RETURN` blocks, which 4.15 covers. Run a CI job that builds, lints, tests and publishes whenever you push a tag. Treat the collection like a library, with a public interface and a deprecation policy.

---

NVIDIA-provided automation, such as DeepOps, `nvidia.nvue` for Cumulus and Spectrum switches, network operator manifests and the BCM Python and CLI tools, can be consumed as roles or collections. Pin and review it the same way you would any other dependency.

---

## FILE docs/part-04-automation/12-ansible-vault-and-secrets-management.md

AWS Secrets Manager and SSM Parameter Store are reached through `amazon.aws.aws_secret` and the `aws_ssm` lookup. GCP Secret Manager uses `google.cloud.gcp_secret_manager`, as a lookup or a module. Azure Key Vault comes through `azure.azcollection`. Authenticate with workload identity, such as CI OIDC, rather than static keys. The advantages are IAM-based access, audit logs, rotation hooks and regional availability. The usual pattern is to bootstrap a minimal identity, fetch the secrets, write them to hosts with strict modes, and never persist them in logs.

---

SOPS encrypts the values in YAML, JSON, ENV and INI files, and leaves the keys readable. It uses KMS keys from AWS, GCP or Azure, age keys, or PGP keys. Each file records which recipients can decrypt it. The result gives you diffs a reviewer can read, such as "`db_password` changed", and per-recipient access without a shared password.

---

In Ansible, the `community.sops` collection does the rest. Its vars plugin decrypts `*.sops.yml` files in `group_vars` automatically. Its lookup, `community.sops.sops`, is available, and its action decrypts on the controller. Compared with Ansible Vault, SOPS has no single shared password. It adds KMS-backed access control and an audit trail, and it supports partial-file encryption. The cost is a dependency on KMS or age tooling, and a different workflow. SOPS is also the standard for GitOps secrets. Flux integrates it natively, and Argo CD supports it through plugins. That is why it keeps coming up in Kubernetes automation, covered in 4.26.

---

Start with the self-checking Python lab. Run it on your own machine with the command below. It checks header parsing for `$ANSIBLE_VAULT;1.1;AES256` and `$ANSIBLE_VAULT;1.2;AES256;prod`, and it confirms that plaintext is rejected by the pre-commit check, through `parse_ansible_vault_header`. It tests isolation between Vault IDs with `can_decrypt_vault_blob`, which Ansible: Up and Running covers in chapter 10. Last, it tests two-phase zero-downtime secret rotation with `TwoPhaseSecretRotator`.

---

## FILE docs/part-04-automation/13-testing-ansible-ansible-lint-molecule-and-ci.md

Sometimes a rule must be broken on purpose. In that case, add an inline skip with a reason, such as `# noqa: command-instead-of-module` on the task line. The older `tags: [skip_ansible_lint]` form is legacy. Every skip is debt, so review them regularly. The profiles climb from basic correctness to full production hygiene. Start new repositories at `production`, and raise legacy code one profile at a time.

---

Many bugs live in templates. You can render each template with the `template` module against `localhost`, or with Python Jinja2 in unit tests, as covered in 3.9. Use representative variable sets, including optional values left unset, and compare the output with golden files. Golden-file tests make the diffs visible in code review. Then validate the rendered file with the target tool, such as `nginx -t`, `sshd -t`, `visudo -cf` or `promtool check config`.

---

The Ansible-native verifier (`verifier: ansible`) uses assertions built from modules such as `assert`, `stat`, `slurp`, `uri`, `command`, `service_facts` and `package_facts`. It needs no extra dependency, so it suits most roles. The testinfra verifier, which runs on Python and pytest, gives you expressive host assertions.

---

Some roles install and remove themselves with one `desired_state` variable. The dispatch in `tasks/main.yml` runs `include_tasks: "{{ desired_state }}.yml"`, which picks `present.yml` or `absent.yml` (Examples 14-4 and 14-5). Test both `desired_state: present` and `desired_state: absent` in Molecule, so you know the role can also clean up after itself.

---

## FILE docs/part-04-automation/14-ansible-at-scale-performance-strategies-and-callbacks.md

Other tools help too. Set `ANSIBLE_LOG_PATH` to keep a log, and run `ansible-playbook -vv` to see connection timing. Use `time` for the whole-run wall clock. If the controller is CPU-bound, `strace -c -f -p` or `py-spy dump` shows where its time goes. For socket and file descriptor limits, check `ss -s` and `ulimit -n`.

---

Each fork is a Python process. It uses roughly 50 to 150 MiB of memory and some CPU while it templates and parses results. Templating is CPU-bound, so too many forks can saturate the CPU. Watch memory, CPU saturation, file descriptors (`ulimit -n`), and the ephemeral port range. On the targets, watch SSH rate limits such as `MaxStartups`, fail2ban and bastion limits.

---

`gather_facts: false` skips facts in plays that do not use them. `gather_subset: [min]` or `!all,!min,network` collects only what you need. You can also run one early play to gather and cache facts, and let later plays rely on that cache with `gather_facts: false`. Cached facts keep the `ansible_facts` access patterns working.

---

Some dashboards pay for themselves. Track changes per environment per day, failure rate per play or role, and mean run duration. Also track hosts not converged in N days, which shows drift, and tasks that always change, which points to idempotency regressions. Finish with the slowest tasks.

---

## FILE docs/part-04-automation/15-custom-modules-plug-ins-and-ansible-automation-platform.md

A custom module or plugin turns a fragile shell snippet into an idempotent, testable, documented task. Once more than a handful of people run automation, you also need a **platform**. A platform gives you central credentials, role-based access, audit trails, scheduling, approvals and an API. Ansible Automation Platform (AAP, and its upstream AWX) is that layer. This chapter shows how to extend Ansible and how to operate it as a shared service.

---

The third point is "Releasing software is a one-bit decision, not a transfer of bytes." Store pre-built packages, wheels and container images in an artifact repository such as `Nexus`, `Artifactory` or `Automation Hub`. Test every role with `yamllint`, `ansible-lint`, `ansible-later`, `ShellCheck` and `Molecule`, plus `ssh-audit` for SSH crypto hardening. Then roll changes out continuously, in stages with `serial`, and run smoke tests after each stage.

---

Most mature setups combine these options. CI runs the tests and builds the EEs and images. AAP runs the scheduled and operator-driven production jobs. `ansible-pull` or images handle the baseline of each node. Decide which of these jobs belongs to which option, and write that down. Read the watch-out column before you commit, because it names the cost you will pay.

---

Without a backup of the controller database and secret key, or an upgrade plan, you have no recovery path. EDA rulebooks that trigger destructive actions without rate limits or approvals are a risk too. Treat AAP as a controlled executor of tested code, not as a replacement for testing and review.

---

## FILE docs/part-04-automation/16-ansible-for-containers-cloud-and-network-devices.md

Read the play from top to bottom, the way you would read a runbook. The first task installs and starts Docker. The second pulls the image, and the third starts the GPU container with the NVIDIA Container Toolkit in place. Watch the `device_requests` block, because it is what hands the GPUs to the container.

---

The VLAN task merges its data into the device. The BGP task uses `state: replaced`, which replaces the resources it names. The seven resource-module states are `merged` (add or update), `replaced` (replace the given resources), `overridden` (replace everything of this type), `deleted`, `gathered` (read the device into structured data), `rendered` (produce commands offline) and `parsed` (turn config text into data). The `rendered` and `parsed` states let you test without a device. Compare the `before`, `after` and `commands` return keys of the vendor module with `--diff` or `--check` to see what would change.

---

Start with the self-checking Python lab, which runs on your own machine: `code/part04/ansible_cloud_network_lab.py`. It checks three things. The first is the resource-module state engine, `apply_vlan_resource_module`. It compares `merged`, `overridden`, `deleted` and `gathered`, and it generates offline `rendered` CLI (*Network Programmability and Automation*, Chapter 12). The second is the LLDP verifier, `verify_lldp_against_cabling_plan`, which checks the topology against the cabling plan. The third is `select_latest_ami`, which picks the latest AMI dynamically (*Ansible: Up and Running*, Chapter 17).

---

1. Start with containers and images, using `community.docker` and `containers.podman`. (a) Explain how you would use `docker_container` with `device_requests` for GPUs and `comparisons`, and how `docker_image` and `docker_image_info` fit in. Then explain when to use Packer (`rhel8.pkr.hcl`, `gcp.pkr.hcl`, `aws.pkr.hcl`, `gcc.pkr.hcl`) with the `ansible` provisioner. (b) Explain where you draw the line between `kubernetes.core` and GitOps controllers. `k8s`, `helm`, `k8s_info` and `k8s_drain` handle cluster bootstrap and day-2 node maintenance, while Argo CD or Flux handles ongoing workloads. This item draws on *Ansible: Up and Running*, Chapters 13 and 16.
2. For cloud resources and Windows hosts, which involve `amazon.aws`, `google.cloud` and `azure.azcollection`, use `select_latest_ami()` in `code/part04/ansible_cloud_network.py` to explain two things. (a) Why Terraform is preferred for stateful cloud resource lifecycles, while Ansible excels at dynamic inventory (`aws_ec2`, `gcp_compute`), `ec2_ami_info` discovery, `add_host` post-provisioning and day-2 actions. (b) How Ansible manages Windows hosts over WinRM, using `win_ping`, `win_chocolatey`, `win_feature`, `win_reboot` and `win_updates`. This item draws on *Ansible: Up and Running*, Chapters 12 and 17.
3. For network devices, use `apply_vlan_resource_module()` in `code/part04/ansible_cloud_network.py`. Explain why network modules run on the control node rather than on the switch. Contrast `network_cli`, `httpapi` (NX-API and eAPI) and `netconf`. Then trace all seven resource-module states: `merged`, `replaced`, `overridden`, `deleted`, `gathered`, `rendered` and `parsed`. This item draws on *Network Programmability and Automation*, Chapter 12.
4. As you trace the Section 3 `nvidia.nvue.config` play. It sets `mtu: 9216` on `swp1-32` and configures RFC 7938 BGP unnumbered on a leaf switch. Then explain how Ansible works with Quantum InfiniBand switches and UFM through the `uri` REST API, and with BlueField DPUs through standard Linux SSH and `mlxconfig` or DOCA.
5. Using `verify_lldp_against_cabling_plan()` in `code/part04/ansible_cloud_network.py`, trace the 6-step safe rollout pipeline. The steps are backup, then `--check --diff` or `rendered`, then commit-confirm on 1 canary leaf, then verify the BGP `Established` count and LLDP against the cabling plan, then batch rollout, and finally save config.
6. Work on multi-vendor automation and security auditing, and check your reasoning. (a) Compare Ansible with pure-Python Nornir and NAPALM (`InitNornir`, `SimpleInventory`, `napalm_get`, `napalm_configure`), using *Network Programmability and Automation*, Chapter 12. (b) Explain why *Ansible: Up and Running*, Chapter 21, pairs `ansible-lockdown` hardening playbooks with independent scanners, OpenSCAP (`oscap xccdf eval --profile ospp`) and `ssh-audit`.

---

## FILE docs/part-04-automation/17-ansible-for-gpu-nodes-and-clusters.md

The GPU tuning role handles the persistence daemon, clocks, power, ECC, compute mode and MIG. It enables `nvidia-persistenced`, or sets persistence mode with `nvidia-smi -pm 1`. It sets application or locked clocks with `nvidia-smi -lgc` when policy requires them, and power limits with `-pl`, which is the `gpu_power_limit` module from 4.15. It sets ECC mode and compute mode, such as `EXCLUSIVE_PROCESS` or the default. For MIG, it runs `nvidia-smi -mig 1`, then creates GPU and compute instances with `nvidia-smi mig -cgi ... -C`. Changing MIG mode may need a GPU reset or a reboot, and no processes can be running on the GPU. Finally, the role takes an `nvidia-smi topo -m` snapshot for inventory, installs the GDRCopy kernel module, and loads `nvidia-peermem` at boot through `modules-load.d`. It can also set udev rules under `/etc/udev` for device nodes, if non-root runtimes need them.

---

The sweep writes one JSON file per host. Aggregate those files into a report that counts nodes with fewer than 8 GPUs, PCIe links degraded below x16, nonzero uncorrected ECC, and active throttle reasons. That report is a typical first step when many jobs slow down during an incident. Run this sweep first when throughput drops, before you change any node.

---

Treating "service started" as "node healthy" is another trap, and so is skipping burn-in and collectives tests. Rolling out to the whole fleet without a canary, with no `max_fail_percentage`, is risky. So is retrying reboots on nodes that do not return.

---

Hard-coded package names across distributions cause failures. Roles that fail halfway can leave a node half-configured but visible to the scheduler. Compiling tools from moving branches at test time, or leaving benchmark versions unpinned, gives you results you cannot repeat. Without a record of results, repeat-offender nodes and slow regressions go unnoticed. Secrets in command lines and verbose logs with credentials are a risk of their own. Applying Ansible driver changes underneath the GPU Operator creates two managers for the same component.

---

## FILE docs/part-04-automation/18-terraform-refresher-why-providers-resources-and-the-workflow.md

The last axes are master server versus masterless, and agent-based versus agentless. Terraform is masterless and agentless by default. The CLI talks straight to cloud provider APIs over HTTPS, with no background agent on target VMs and no dedicated master daemon. HCP Terraform, Atlantis or CI runners can still host remote execution when you want it.

---

Terraform reads every `*.tf` file in a directory as one configuration, called the root module. It merges the files in lexical order. The filenames do not change how Terraform reads them, but conventions help people find things: `main.tf`, `variables.tf`, `outputs.tf`, `providers.tf` or `versions.tf`, `locals.tf` and `data.tf`.

---

A few symbols carry most of the meaning. `+` means create, `~` means update in place, and `-` means destroy. `-/+` means destroy and then create, while `+/-` means create before destroy. `<=` marks a data read. The phrase "known after apply" marks a value Terraform cannot know until apply runs, and "forces replacement" names the attribute that caused a replacement. Always read the summary line, which reads "Plan: X to add, Y to change, Z to destroy". Then look for unexpected destroys and replacements, especially of stateful objects.

---

`terraform plan` refreshes by default. With `-refresh-only`, you accept the real-world changes into state without changing the infrastructure. Without it, the plan shows the changes needed to revert reality to match the configuration. Decide each drift on its merits. You can revert it with an apply, codify it by editing the configuration to match, or ignore an attribute that changes legitimately outside Terraform with `lifecycle { ignore_changes = [...] }` (4.21). Schedule a nightly plan (4.2).

---

## FILE docs/part-04-automation/19-terraform-state-in-depth-backends-locking-and-drift.md

Workspaces share configuration and backend credentials, so the isolation is only logical, as covered in 4.18. If you use them anyway, pair each workspace with its own variable file, put the workspace name in resource names, and have CI check that the selected workspace matches the intended environment.

---

Splitting a resource from state A into state B needs no downtime. Step 1 is to add the resource configuration and an `import` block in state B. Step 2 is to apply B, so it tracks the resource. Step 3 is to add a `removed` block with `destroy = false` in state A and apply A. Step 4 deletes the code from A. Check that both plans are clean at each step.

---

Follow the same procedure for any surgery. Announce it, take a backup copy and make sure no CI run is active. Then operate, run `plan` and expect **no changes**, or only the changes you expected. Finally, record what you did.

---

Ignoring drift is a mistake that waits to show itself, usually on the day a plan wants to destroy a cluster. Avoid `ignore_changes = all`, and do not ignore fields that hide real problems. Finally, make sure you have a tested recovery plan, a protected state bucket, and no accidental change to the backend `key`, which would start you with empty state.

---

## FILE docs/part-04-automation/20-terraform-modules-and-reusable-infrastructure.md

1. Keep the interface small and focused. Expose the knobs that vary between uses, and hide the implementation details. Every variable becomes a public API that you must support and version, so give sensible defaults and require only the inputs the module cannot guess.
2. Use types and validation. Object types with `optional()` defaults (Terraform 1.3+), `validation` blocks, and `precondition` or `postcondition` blocks make a module fail at plan time with a useful message. Good `description`s double as documentation.
3. Treat outputs as the contract. Output IDs, names, ARNs/self-links, endpoints and structured maps that other modules consume. Mark secrets `sensitive`. Avoid outputting whole resources unless you mean to, because that couples consumers to the provider schema.
4. Keep provider configuration out of reusable modules. Declare requirements in `required_providers` and let the caller pass configured providers with `providers = { google = google.eu }`. A module with `provider` blocks is hard to use with `count` or `for_each`, and it complicates deletion. Use `configuration_aliases` when a module needs several providers.
5. Give each module one responsibility. A network, a storage bucket, a node pool and an IAM role each deserve their own module. A platform module that does everything is hard to evolve, so compose small modules in the root instead.
6. Do not wrap a single resource without adding value. A module that forwards 30 variables to `aws_instance` adds indirection and no policy. Add value by encoding conventions such as naming, tags, labels, encryption defaults and logging. You can also add validations, companion resources such as alarms or IAM, or several resources that belong together.
7. Use opinionated defaults, and open escape hatches sparingly. Make the module secure by default, with private access, encryption and deletion protection for stateful resources. Allow overrides on purpose, not through a catch-all `extra_config` map that bypasses validation.
8. Keep internal addresses stable. Renaming a resource inside a module is a breaking change for users' state. When you refactor, add `moved` blocks inside the module, because they travel with the module version.
9. Avoid data sources that depend on the caller's state. Accept IDs as inputs instead of looking things up by name, unless looking things up is the module's job. Loose coupling makes the module easier to test.
10. Keep the module idempotent and plan-stable. Avoid `timestamp()`, and avoid random values unless you use `random_*` resources. Do not let `for_each` keys depend on values unknown at plan time. Derive the keys from static inputs.
11. Respect how `count` and `for_each` behave on module calls. Modules that contain `provider` blocks or `configuration_aliases` have restrictions, so design the module so the caller can repeat it.
12. Learn the module gotchas from *Terraform: Up and Running*, chapter 4.
    - *Gotcha 1: file paths (`path.module` vs. `path.root` vs. `path.cwd`).* When a module calls `file(...)` or `templatefile(...)`, Terraform resolves relative paths from the root module directory (`path.root`), not from the child module directory. Suppose `modules/services/webserver-cluster/main.tf` writes `templatefile("user-data.sh", ...)` and a root in `stage/services/webserver-cluster/` calls it. Terraform fails, because `user-data.sh` is not in `stage/`. Always prefix module-internal files with **`${path.module}/user-data.sh`**. Here `path.module` is the directory of the module where the expression is written, `path.root` is the root module directory, and `path.cwd` is the current working directory.
    - *Gotcha 2: inline blocks vs. separate resources (`aws_security_group` vs. `aws_security_group_rule`).* Several cloud resources, such as `aws_security_group`, `aws_route_table` and `aws_network_acl`, accept rules either as inline blocks (`ingress { ... }`) or as separate standalone resources. Suppose your reusable module uses inline `ingress {}` blocks. A caller in `stage` then attaches an extra `aws_security_group_rule` (`allow_testing_inbound` on port `12345`) to `module.webserver_cluster.alb_security_group_id`. The inline block and the standalone rule overwrite each other on alternating `terraform apply` runs. Separate rules reference their group, as in `security_group_id = aws_security_group.alb.id`. Always use separate `aws_security_group_rule` (`aws_route`, `aws_network_acl_rule`) resources inside reusable modules, so callers can extend them safely.
    - *Locals for internal constants, outputs for external extension.* Put internal constants such as `http_port = 80`, `any_port = 0`, `any_protocol = "-1"`, `tcp_protocol = "tcp"` and `all_ips = ["0.0.0.0/0"]` in a **`locals` block**, not in `variable`s, when you do not want callers overriding them. Export key identifiers such as `output "asg_name"` and `output "alb_security_group_id"`. Callers such as `module.webserver_cluster.asg_name` can then attach environment-specific resources. For example, `prod` adds `aws_autoscaling_schedule` resources, `scale_out_during_business_hours` at `0 9 * * *` and `scale_in_at_night` at `0 17 * * *`, without putting environment conditionals in the module.

---

The `lifecycle` block at the bottom of the resource refuses accidental destroys. Checkpoints cannot be replaced, so that refusal is the point. The IAM bindings take a typed list of writer service accounts, and the outputs expose only the bucket name and URL.

---

Start with the self-checking Python lab, which you run locally before you touch any cloud. It checks the `gke-gpu-pool` input `validation` and `precondition` rules, which match `tests/validation.tftest.hcl` (see `validate_gke_gpu_pool_inputs`). It also checks the Git module `source` rules: the `//` subdirectory and the `?ref=` immutability (`parse_git_module_source`, from *Terraform: Up and Running*, chapter 4). Last, it looks for the inline-versus-separate `aws_security_group_rule` conflict (`detect_inline_vs_separate_sg_conflict`, from the same chapter).

---

1. Start with the root and child module split, the interface design across `variables.tf`, `locals.tf` and `outputs.tf`, and the two module gotchas. Use `validate_gke_gpu_pool_inputs()` and `detect_inline_vs_separate_sg_conflict()` in `code/part04/terraform_modules_validator.py` as your reference. First, explain how `variables.tf`, `locals.tf` and `outputs.tf` work together, with outputs read as `module.<NAME>.<OUTPUT>`. Second, explain why child modules must use `${path.module}/...` for local files. Third, explain why reusable modules must use standalone `aws_security_group_rule` (`aws_route`) resources rather than inline `ingress {}` blocks.
2. Explain provider inheritance and `configuration_aliases`, then explain why defining a `provider "google" {}` block inside a child module breaks `count`, `for_each` and module removal. Then show how a multi-region root module passes `providers = { google = google.eu }` into a child module.
3. Trace how `envs/prod/main.tf` composes `module.network`, `module.checkpoints`, `module.cluster` and `module.gpu_pool`. Pay attention to `for_each = yamldecode(file("${path.module}/gpu-pools.yaml"))`. Then explain why `subnet_id = module.network.subnet_ids["compute"]`, which is dependency inversion, beats looking up the VPC inside `gke-gpu-pool`.
4. Using `parse_git_module_source()` in `code/part04/terraform_modules_validator.py`, explain the double slash `//` in Git and registry module sources, and what a pin such as `?ref=v2.3.1` means. Explain why `stage` can test `?ref=v0.0.2` while `prod` stays pinned on `?ref=v0.0.1`. Then explain how embedding a `moved {}` block inside a module's v2 release prevents resource recreation across consumers. The source material is *Terraform: Up and Running*, chapter 4.
5. Trace `tests/validation.tftest.hcl` in Section 5. Follow `run "valid_gpu_pool_plans" { command = plan ... }` and `run "rejects_bad_gpu_count" { expect_failures = [var.gpu_count] }`. Then compare fast plan-level `.tftest.hcl` unit tests with Go `Terratest` integration tests, which use `terraform.InitAndApply` and `defer terraform.Destroy`.
6. Explain why a 150-variable "God module", a one-to-one resource wrapper and a pile of boolean `create_x` toggles all hurt maintainability. Then explain why `if var.env == "prod"` inside a shared module is an anti-pattern, as *Terraform: Up and Running*, chapter 4, describes. Finally, say what value `modules/checkpoint-bucket` adds over a raw `google_storage_bucket` resource.

---

## FILE docs/part-04-automation/21-terraform-loops-conditionals-lifecycle-and-gotchas.md

Removing `l4-infer` from the map destroys only that pool. Adding a key adds only that pool. The identity is the key, not the position, so the rest of the fleet stays untouched. This is the default choice for a collection of distinct things.

---

Keys must be known at plan time. `for_each = toset(aws_instance.x[*].id)` fails when the IDs are unknown until apply. The error reads "The for_each map includes keys derived from resource attributes that cannot be determined until apply". Derive keys from static inputs, such as names, and let the values, which may be unknown, sit in the map values.

---

Several related constructs sit beside the lifecycle block. `check` blocks give non-blocking assertions with scoped data sources, which suits health checks of the deployed system. `terraform_data` with `triggers_replace` is the modern `null_resource`, and the `-replace` flag handles an ad-hoc replacement. `depends_on` handles hidden ordering, but use it sparingly. It makes modules less parallel and sometimes defers data sources to apply time.

---

1. Start with the four HCL looping constructs: `count`, `for_each`, `for` expressions and `%{ for ... }` string directives, from *Terraform: Up and Running*, Chapter 5. Use `simulate_count_vs_for_each_removal()` in `code/part04/terraform_loops_lifecycle.py` so you can trace what happens when `"trinity"` is removed from `["neo", "trinity", "morpheus"]`. Compare `count` with `for_each = toset(var.user_names)`. Then show how you can use `moved` blocks to migrate the existing `count` state indices (`[0]`, `[1]`, `[2]`) to the `for_each` keys (`["neo"]`, `["trinity"]`, `["morpheus"]`) without recreating resources.
2. Reshape data with `for` expressions, the `...` grouping, `setproduct` and `merge([for ...])` flattening. Use `flatten_team_namespaces()` in `code/part04/terraform_loops_lifecycle.py` to explain how Section 9 flattens a nested `{ team => { gpu_quota, namespaces } }` map into a one-level `"team/ns"` map for `for_each`. Then explain how `{ for p in var.pool_list : p.region => p.name... }` groups items by key.
3. Work with `dynamic` blocks, using `ingress` and `tag`, and compare them with provider `default_tags`. Show how `dynamic "ingress"`, including `self = true` for EFA and NCCL traffic inside the group, generates nested blocks. Show how `dynamic "tag"`, filtered with `{ for k, v in var.custom_tags : k => upper(v) if k != "Name" }`, does the same for tags. Then explain when `provider "aws" { default_tags { tags = ... } }` is cleaner than `dynamic "tag"`, drawing on *Terraform: Up and Running*, Chapter 5.
4. Practice conditionals with `count = cond ? 1 : 0`, filtered `for_each`, optional `dynamic` blocks and `one(concat(...))`. Use `evaluate_one_concat_conditional()` in `code/part04/terraform_loops_lifecycle.py` to explain why `[0]` index access fails in an if/else `count` ternary output when one resource has `count = 0`. Then explain how `one(concat(full[*].policy_arn, ro[*].policy_arn))` solves the problem cleanly.
5. Study the `lifecycle` block, with `create_before_destroy`, `prevent_destroy`, `ignore_changes`, `replace_triggered_by`, `precondition` and `postcondition`, along with zero-downtime rolling patterns. Compare the two zero-downtime ASG deployment patterns in *Terraform: Up and Running*, Chapter 5. The first is `create_before_destroy = true` with `name = "${var.cluster_name}-${aws_launch_configuration.example.name}"` and `min_elb_capacity`. The second is the native `instance_refresh` with `strategy = "Rolling"` and `min_healthy_percentage = 50`, along with the GKE `update_policy`.
6. Diagnose the Terraform sharp edges: unknown `for_each` keys, dependency cycles, eventual consistency, `depends_on` on modules and perpetual diffs. You should explain why each one happens during `plan` or `apply`, and state the exact architectural fix for each.

---

## FILE docs/part-04-automation/22-terraform-secrets-and-multiple-providers.md

Strategy 4 uses the ephemeral and write-only features of newer Terraform and OpenTofu versions. Ephemeral resources and values exist only during the run, and they are not persisted to state or plan. One example is reading a secret from a secret manager to use in a provider configuration or a write-only argument. Write-only arguments, named like `password_wo`, accept a value that is sent to the provider but never stored. Support depends on version and on each provider and resource, so verify it before you rely on it.

---

Strategy 5 reads the value at apply time from a secret manager, using a data source, and passes it into the resource. The value is still stored in state if the resource attribute persists it. Pair this approach with encrypted, access-controlled state.

---

When no provider exists for a system, you have several options. You can use `null_resource` or `terraform_data` with `local-exec` to call an API or CLI, which is fragile. You can use the `restapi` or `http` provider. You can use an `external` data source, which runs a script that returns JSON. You can write a provider. Or you can hand that part to Ansible or Crossplane (4.16).

---

Start with the self-checking Python lab, which you can run on your own machine. It checks the state exposure classifier (`classify_secret_state_exposure`, which contrasts `sensitive_var_or_data_source` and `random_password_resource` with `manage_master_user_password` and `ephemeral_or_write_only`). It also checks the GitHub Actions OIDC `AssumeRoleWithWebIdentity` trust-policy evaluator (`verify_github_oidc_assume_role`, from *Terraform: Up and Running* chapter 6). Last, it checks the `configuration_aliases` wiring (`validate_child_module_provider_wiring`, from chapter 7).

---

## FILE docs/part-04-automation/23-production-grade-terraform-structure-testing-and-team-workflows.md

A new engineer's first question is usually where a change belongs. The repository layout answers that before anyone opens a file. Reusable building blocks live in one place, the stacks that actually deploy live in another, and each stack keeps its own state.

---

1. Dependency injection in modules. If a service module (`hello-world-app`) hardcodes `data "terraform_remote_state" "db"`, you cannot unit-test it without first setting up an S3 state bucket and deploying a database. Add an optional input, `variable "mysql_config" { type = object({ address = string, port = number }); default = null }`, and set `count = var.mysql_config == null ? 1 : 0` on `data "terraform_remote_state" "db"`. Tests can then inject a mock `{ address = "mock-mysql", port = 3306 }`, or wire `mysql_config = module.mysql` directly in memory.
2. Skipping slow stages during local development. Deploying and tearing down an RDS database or GKE cluster on every test edit takes 15–25 minutes (`795.63s`). Wrap each test phase in Terratest's **`test_structure.RunTestStage(t, "deploy_db", func() { ... })`**, which saves state to `/tmp` with `test_structure.SaveTerraformOptions`. Run `go test` once. Then iterate on `deploy_app` and `validate_app` in seconds with **`SKIP_deploy_db=true SKIP_teardown_db=true SKIP_teardown_app=true go test -timeout 30m`**. The pattern is modeled in `run_terratest_stages()` in `code/part04/terraform_production_guardrails.py`.

---

You can test a GPU module without a GPU. Validate it with plan-level tests, and apply it with the cheapest accelerator, or with a zero-GPU variant if the module supports one. Run a small GPU smoke test on a schedule rather than on every PR.

---

Read the diagram from top to bottom. Code moves through a pull request first, then through staging, and only then reaches production behind an approval gate. When you review a change, you will see most of the rules below in action.

---

## FILE docs/part-04-automation/24-terraform-on-gcp-and-nebius-networks-gpu-vms-and-gke.md

Next, choose regions and zones for GPUs. GPU families exist only in specific zones, and capacity varies from zone to zone. Check `gcloud compute accelerator-types list`, `gcloud compute machine-types list --filter="name~a3"` and the quota pages. Plan for zones where you actually hold quota or reservations. Multi-region fallbacks carry cost and data-gravity implications, so treat them as a deliberate choice.

---

Machine families differ in how they carry GPUs. These families bundle their GPUs into the machine type. A2 brings A100 GPUs. A3 brings H100 GPUs, in machine types such as `a3-highgpu-8g`, `a3-megagpu-8g` and `a3-edgegpu`. A3 Ultra brings H200, A4 brings B200, A4X brings GB200 NVL72, and G2 brings L4. N1 is the exception, because it uses attached accelerators. Machine types, GPU counts, networking and availability differ by zone and change over time. Verify them with `gcloud compute machine-types list` and the accelerator documentation.

---

For boot images, you have three options. Deep Learning VM images come with drivers preinstalled. Container-Optimized OS comes with a GPU driver installer. You can also build your own golden image with Packer and Ansible (4.2, 4.17). Whichever you pick, Secure Boot requires signed modules.

---

Suppose your team already runs Terraform on GCP and now needs GPU capacity from Nebius. Many of the concepts map across directly, but the names and the fabric model differ. The table shows where each concern lands in each cloud.

---

## FILE docs/part-04-automation/25-terraform-with-kubernetes-and-helm-providers-opentofu.md

Prefer `exec` plugins over static tokens. They fetch a short-lived token when Terraform runs, and the token never lands in state. The CI identity also needs Kubernetes RBAC. Give the Terraform service account a `cluster-admin` binding **only** in the bootstrap stack, and give later stacks narrower roles. The cluster API endpoint must be reachable from the runner. Private clusters need a self-hosted runner inside the VPC, a VPN, or an authorised-network entry or IAP tunnel.

---

Typed resources give the cleanest plans. `kubernetes_manifest` can manage any resource, including CRDs, but only when the CRD already exists at plan time. If you are unsure which one to use, start with the typed resource and reach for `kubernetes_manifest` only when you must.

---

Quotas and team lists come from the same data as cloud IAM and cost allocation. For that reason, Terraform is a reasonable owner of tenancy objects in a smaller organisation. Larger organisations move these objects to GitOps, with a self-service PR flow (4.26). With Kueue, ClusterQueues, ResourceFlavors and LocalQueues encode GPU quotas by team and accelerator type. You apply them through `kubectl_manifest` or GitOps, and only one system should own them.

---

Large manifests slow down `kubernetes_manifest`, because it diffs field by field. Chunk them, or use Helm for large bundles. `kubernetes_manifest` uses server-side apply with the field manager `Terraform`. Other controllers, such as HPA, operators and Argo, may fight over the same fields. Use `field_manager { force_conflicts = true }` carefully, or use `computed_fields`.

---

## FILE docs/part-04-automation/26-gitops-with-argo-cd-and-flux.md

Once application code and deployment files are both in source control, a common question follows. Should they share one repository? Small projects can. Larger projects often split them, because the builder and the deployer see the work from different sides, even when they are the same people.

---

That raises the next question. How do you bring a new feature from source control into production? The answer is a feature gate, a flag that turns a feature on or off. New code sits behind the gate, and looks something like this:

---

Suppose an upgrade of the GPU operator stalls at two in the morning. Before you touch anything, you need to know which object holds the desired state and which one holds the live state. Argo CD is built around a small set of objects that answer that question.

---

Least privilege matters because controllers often hold cluster-admin. You can reduce that with impersonation in Flux, with AppProjects that restrict destinations and kinds in Argo, or with per-tenant controllers. Protect the Git repos with branch protection, signed commits and required reviews, because **write access to the config repo equals cluster-admin**. Use separate repos or paths, plus approvals, for sensitive layers such as RBAC, policies and privileged operators.

---

## FILE docs/part-04-automation/27-lab-provision-a-gpu-cluster-with-terraform-and-ansible.md

Read the diagram from top to bottom, because that is the order you will work in. Terraform builds the infrastructure, its output becomes the Ansible inventory, and Ansible configures the nodes that validation then checks. The nightly drift job looks at both layers.

---

Suppose a node has to appear before anything else can run on it. In Path A, that node is a container, and Terraform is the tool that creates it. The three files below define the node model, the Docker module that builds the containers, and the live root that exports the inventory for Ansible.

---

The module returns the same output shape: `address`, `ssh_host` (the instance private IP through IAP, or an external bastion) and `ssh_port` set to 22. The live root calls the cloud module instead, and the Ansible side stays identical. Configure the remote state backend (4.19) with a versioned bucket.

---

You create each role with `ansible-galaxy role init`, then write the minimum it needs. Every role has `defaults`, `tasks`, `handlers`, `meta/argument_specs.yml` and a `README.md`. The five roles below do the real work of the cluster, and each one leaves its node in a state the next role can build on.

---

## FILE docs/part-12-ai-networking/01-ai-traffic-collectives-incast-and-elephant-flows.md

Suppose you design a network the way you would for a web service. Users send independent requests north-south, between clients and servers, and that model works well. Carry the same design onto an AI cluster, though, and congestion appears as soon as petabyte-scale training pipelines start running. Storage ingest stalls, or east-west collective synchronization saturates the spine switches. To see why, look at the whole lifecycle. A generative AI factory runs as a continuous five-stage cycle that moves massive datasets through preprocessing, training, deployment, retrieval, and retraining.

---

Picture a training team that scales a job from one server to two and watches per-GPU throughput fall ten-fold. Often the cause is a parallelism dimension placed across the wrong link. A frontier model with hundreds of billions of parameters cannot fit into a single GPU's memory, so the model has to be split. If the wrong dimension crosses slow inter-node links, communication overhead stalls every forward and backward pass. Modern clusters therefore combine Data Parallelism, Pipeline Parallelism, and Tensor Parallelism into 3D Parallelism. Each dimension needs its own tier of interconnect.

---

Start with the first pitfall. If PyTorch distributed initializes with the CPU-bound Gloo backend instead of NCCL, tensors pass through host RAM and TCP sockets, and collectives slow down fifty-fold. Set `NCCL_SOCKET_IFNAME` to the high-speed interface, so bootstrap handshakes do not cross a slow management network. The second pitfall is version mismatch. Mixing PyTorch's bundled NCCL with an incompatible system library causes silent transport fallbacks or hangs. The third is port exhaustion. Large jobs can run out of ephemeral TCP ports during bootstrap unless the host port range is widened.

---

Never debug a slow PyTorch job before you have isolated the hardware, one layer at a time. Start with `nvbandwidth`, which confirms local PCIe Gen5 x16 host-to-device bandwidth and rules out an x8 link downtrain. Next, run `ib_write_bw` with GPUDirect RDMA enabled. It verifies raw 400G wire and optics throughput, and you should use it instead of `iperf3`. Finally, run `all_reduce_perf` from `nccl-tests` across nodes to validate collective scaling.

---

## FILE docs/part-12-ai-networking/02-rdma-fundamentals-verbs-queue-pairs-and-memory-registration.md

RDMA solves this bottleneck by combining two hardware mechanisms. First, Direct Memory Access lets the adapter hardware engine read and write physical host RAM or GPU BAR1 VRAM directly across the PCIe bus. No CPU copy loops are required. Second, kernel bypass and transport offload remove the operating system from the hot transfer path.

---

If your application asks for more Queue Pairs, Work Requests, or Scatter-Gather Entries than the network adapter supports, allocation fails right at job startup. Before you post a single RDMA operation, your software must build a strict hierarchy of hardware-backed resource objects through the Verbs interface. It must also verify the hardware limits.

---

RDMA verbs split into two families: two-sided channel operations and one-sided memory operations. Whether the remote CPU and Receive Queue take part in a transfer matters for debugging hangs and data corruption. Suppose a burst arrives while the remote Receive Queue is empty. The remote HCA then returns an RNR NAK, as the table's risk column describes. The table compares the four operations.

---

Event-driven completion works differently. With `ibv_req_notify_cq` and `ibv_get_cq_event`, the application arms the Completion Queue doorbell and sleeps on a file descriptor until the HCA fires an MSI-X interrupt. Event mode saves CPU cycles during idle periods, but it costs 5 to 15 microseconds of kernel interrupt and thread wake-up latency. Production storage and RPC engines often use hybrid polling, which spins briefly before arming interrupts.

---

## FILE docs/part-12-ai-networking/03-rocev2-transport-and-congestion-management.md

The third is congestion at the fabric itself. Synchronized elephant flows, meaning large, long-lived transfers, with low entropy collide at six distinct Clos fabric congestion points. This happens even when the switch topology has a 1:1 non-oversubscribed ratio. When a switch buffer overflows and drops a single packet on a high-bandwidth link, classic Go-Back-N error recovery discards the entire in-flight window. The sender must then retransmit hundreds of intact packets, which multiplies fabric load at the worst possible moment.

---

The fourth is misordered congestion thresholds. They trigger Priority Flow Control pause storms and head-of-line blocking across innocent workloads. Explicit Congestion Notification marks packets end-to-end, so the receiver returns a Congestion Notification Packet. However, the round-trip delay leaves an ECN-only queue lossy under microbursts. Priority Flow Control prevents drops with hop-by-hop pause frames, yet it freezes all flows sharing that traffic class. Without ordered DCQCN thresholds and a PFC Watchdog, a pause wave can deadlock the entire fabric.

---

Three rules govern GID selection on GPU clusters. First, an IPv4 address is encoded into the lower 32 bits of an IPv4-mapped IPv6 GID, using hexadecimal octets. For example, the address `10.20.4.15` ends in `0a14:040f`. Second, two GID indices can show the exact same IPv4 address and RoCEv2 version while binding to different Layer 2 interfaces. In the output above, index 1 binds to untagged `eth0`, whereas index 2 binds to VLAN-tagged `eth0.100`. The Linux kernel populates the GID table in the order interfaces come up at boot. Hard-coding `NCCL_IB_GID_INDEX=2` or `-x 2` across nodes can therefore bind one peer to `eth0.100` and the other to a `v1` entry, failing with `Failed to modify QP to RTR`.

---

Picture an on-call engineer in the middle of a production training slowdown. The pull to tweak switch ECN thresholds or reboot nodes is strong. Blindly changing fabric parameters mid-incident, though, destroys forensic state. It often turns a single-node configuration bug into a cluster-wide outage. Before you run `perftest` benchmarks or change switch queues, capture a five-layer endpoint-to-endpoint path inventory and follow a disciplined evidence ladder.

---

## FILE docs/part-12-ai-networking/04-pfc-ecn-and-dcqcn-in-depth.md

A common architecture question is why AI Ethernet fabrics run both ECN and PFC rather than picking one. If you rely on ECN alone, the fabric stays open to packet drops during fast microbursts. If you rely on PFC alone, you get head-of-line blocking and fabric-wide pause trees that freeze innocent GPU jobs.

---

The lifecycle for Class 3 shows up in two captures. The first is the XOFF pause. It fires when the receiver's Priority 3 ingress buffer crosses the XOFF threshold. The port then transmits a 64-byte frame with Class Enable Vector `0x0008` and a Class 3 pause time of 65,535 quanta. The other seven class timers stay at zero. If congestion persists, each subsequent packet that crosses XOFF sends a fresh XOFF frame, which resets the upstream pause timer. The second is the XON un-pause. It fires once the congested queue drains below the XON threshold, before the pause timer expires. The receiver sends an identical 64-byte frame with the Class 3 pause time set to 0. That tells the upstream neighbor to resume Priority 3 transmission immediately.

---

Because $\alpha$ never exceeds 1.0, a single rate cut reduces $R_c$ by at most 50 percent. When no CNP arrives, the sender decays $\alpha$ toward zero as each rate-increase timer or byte counter expires. Recovery then runs in three stages, governed by the Fast Recovery threshold $F$: Fast Recovery, Additive Increase and Hyper-Additive Increase.

---

Picture a broken adapter driver or a PCIe credit loop that makes a downstream node, such as GPU102 on LeafC, emit XOFF frames continuously. The resulting PFC storm can lock up the entire fabric. Operators need an automated circuit breaker on every switch, one that isolates the broken sink before the upstream spine buffers freeze.

---

## FILE docs/part-12-ai-networking/05-data-center-bridging-and-qos-for-ai.md

The table rests on three design rules, and each one protects the fabric in a different way. The first rule is about the weights. The DWRR percentages across TC0, TC2, TC3, and TC4 sum to 100 percent (`10% + 10% + 50% + 30% = 100%`). That sum satisfies the IEEE 802.1Qaz requirement for Enhanced Transmission Selection classes.

---

Suppose you run `tcpdump -v` on a GPU server to check RoCEv2 markings. `tcpdump` prints the whole 8-bit IP Type of Service byte in hexadecimal. It does not print the 6-bit DSCP as a plain integer. Engineers who read the hex `tos` byte as a decimal DSCP value end up chasing marking bugs that do not exist, or they configure the wrong switch buckets.

---

The block above shows the policing arithmetic on a 1,024 Kbps WAN link with a 512 Kbps cap. Eight calls at 64 Kbps use exactly 512 Kbps, so they fit with no drops. A ninth call pushes the offer to 576 Kbps, and the policer drops 64 Kbps across all nine calls. The drop lands on the whole class, not on a single call.

---

The fifth layer checks failure and reroute. Simulate a planned uplink drain, and confirm that alternate paths keep the same trust, ETS, ECN, and PFC profiles. The sixth layer correlates switch queue counters with `nccl-tests` or `ib_write_bw`. It also audits host PCIe link width, NUMA locality, and cluster manager interface priorities.

---

## FILE docs/part-12-ai-networking/06-infiniband-fundamentals-and-addressing.md

When several nodes share an oversubscribed or poorly routed switch path, link-layer credit stalls pause the sending Queue Pair between bursts. The peak counter still records the brief moments when credits are available, so it hides a severe throughput collapse. To catch fabric contention, compare peak bandwidth against average bandwidth and message rate in `ib_write_bw`.

---

Each port holds a table of sixteen-bit Partition Keys that the Subnet Manager programs. The lower fifteen bits identify the partition number. The highest bit decides whether the port is a full member or a limited member. Switch and HCA hardware apply one strict rule to every packet. Two ports can communicate only when their fifteen-bit partition numbers match and at least one of them is a full member.

---

Only the GRH is optional for intra-subnet traffic. The ETH, RETH or DETH depends on the operation you run. The next block turns these headers into overhead and efficiency numbers. Work the first case by hand: 8 + 12 + 4 + 2 = 26 bytes.

---

During a long training run, checkpoint saves and dataset reads can stall your GPUs. That happens when storage traffic bounces through host CPU memory, or when it competes with TCP retransmission timers. When you design storage and compute networks, weigh native InfiniBand against Ethernet RoCEv2, HPE Slingshot and emerging Ultra Ethernet fabrics.

---

## FILE docs/part-12-ai-networking/07-infiniband-subnet-manager-routing-topologies-and-rails.md

Standby instances poll the Master at regular intervals. If the Master stops responding, the highest-priority standby takes over and sweeps the subnet to update every port's SM LID. Always verify in `sminfo` that exactly one Master exists and that its activity count is still climbing, not frozen.

---

A Rail-Optimized row of thirty-two servers spread over eight racks needs cables from every server to eight separate leaf switches. Where you put those leaf switches decides which limit you hit. Either you exceed the power budget of the GPU racks, or you exceed the reach of low-cost copper cables.

---

Suppose a collective runs slowly across a leaf, yet all four spine uplinks are active. Start by reading the switch's Linear Forwarding Table with `ibroute`. Next, trace the exact hop path between two LIDs with `ibtracert`. Then sample `PortXmitData` across the leaf uplinks with `perfquery`. Do not pass `-R` to `perfquery` on a shared production switch without change approval. That flag zeroes the hardware counters for every monitoring collector.

---

1. Three Subnet Manager instances start on the same subnet, as the block below shows.
   - Part A: Which instance wins Master state, which become Standby, and why?
   - Part B: If `sm-c` has its priority raised to fifteen, how does the election outcome change? Verify with `elect_master_sm` in `code/part12/infiniband_sm_routing.py`.

---

## FILE docs/part-12-ai-networking/08-infiniband-adaptive-routing-and-congestion-control.md

While switch queue occupancy stays below the threshold, the index stays at zero. The sender then transmits at full line rate. Each arriving BECN packet raises the index by the configured step. The extra delay between packets lets the downstream buffer drain before flow-control credits run out. After BECN notifications stop, each recovery timer expiry lowers the index by one. The Queue Pair returns smoothly to full line rate.

---

Counters from `perfquery` and UFM only go up, counting from the last counter clear or switch reboot. If you alert whenever a counter is above zero, you get two bad outcomes. You get false alarms about old history, and you miss slowly dying optics.

---

Suppose two snapshots, taken five minutes apart under active traffic, show the same nonzero `SymbolErrorCounter`. The delta is zero. That number is old scar tissue from an earlier cable seating event, not an active fault. Now take a port that starts with a tiny error count on Day 1. If its error rate accelerates forty-five times over a single week, and link-down recoveries rise with it, the optical transceiver is failing. It has to be replaced before it triggers continuous Trap 128 sweeps.

---

Work from the symptom to the root cause, confirm the evidence, and only then apply the fix in the last column. Row 4 shows the cost of skipping that order, because a cable fault that looks like congestion gets tuned instead of replaced.

---

## FILE docs/part-12-ai-networking/09-infiniband-diagnostics-ufm-and-operations.md

An alert built on the rate of change and its acceleration flags port twelve on Day 4. That is days before the degrading transceiver drags down training throughput across the cluster. The same rule leaves port nine alone, because its static total is harmless. Alert on the rate and the acceleration of errors, not on the raw total.

---

Experienced fabric engineers check three groups of fields in this output. First, they compare the raw pre-FEC error rates with the effective post-FEC rates on all four lanes. Second, they check every Digital Diagnostic Monitoring reading against the alarm bracket printed in square brackets. Third, they read the part and serial numbers from the module EEPROM. That way, a technician can replace the exact cable without guessing on the data center floor.

---

Checking ports one at a time, with `perfquery` and `mlxlink`, is too slow after a maintenance window. You want one command that sweeps every switch and adapter. It should check link widths, measure counter deltas across a timed pause, and audit routing tables for credit loops. NVIDIA's `ibdiagnet` runs that full multi-stage check from a management or UFM host. It writes structured, machine-readable reports to `/var/tmp/ibdiagnet2/`.

---

5. Next, work through the UFM High Availability election and the SuperPOD scaling. For Exercise 5 in the table below, determine which UFM appliance wins master election, and whether High Availability is ready, in both scenarios. Then explain the DGX B200 and DGX GB300 SuperPOD scaling numbers, and how Base Command Manager updates the Slurm topology configuration.

---

## FILE docs/part-12-ai-networking/10-hdr-ndr-xdr-optics-and-cabling.md

A link speed label hides three separate variables. They are the per-lane symbol rate, the physical coding overhead and the number of parallel lanes. When you read `Rate: 56` on an older FDR port, or `Rate: 400` on an NDR port, you need to translate those raw serial bits into usable payload.

---

1. Higher baud rates lose more signal on high-frequency traces, and optical dispersion and crosstalk add noise on top. The fix is multi-level modulation and strong Forward Error Correction.
2. The waveform arrives badly distorted at the photodiode and at the switch pins. Dedicated Digital Signal Processors must run continuous analog and digital equalization to restore it.
3. Pluggable transceivers pour heat out of the switch faceplate. Cooling them takes finned heat sinks, high-airflow fans, or liquid-cooled switch trays.
4. Optical sub-assemblies and DSP chips make up a large share of network cost and lead time. Open multi-vendor standards from IEEE, OIF and ITU-T help you avoid lock-in.

---

When a packet enters or leaves a switch port, its signal must bridge a speed gap. The switch ASIC pins run at one rate, and the optical fiber lanes run at another. Three hardware stages sit between the cable and the Packet Forwarding Engine ASIC: the multiplexer or demultiplexer gearbox, the optical Digital Signal Processor, and the PFE ASIC SerDes lanes.

---

Optical fiber sends light down a glass core, surrounded by glass cladding with a lower refractive index. That index step traps the light inside the core through total internal reflection. Light inside fiber is immune to electromagnetic interference, and fiber spans from tens of meters up to dozens of kilometers.

---

## FILE docs/part-12-ai-networking/11-nvidia-spectrum-x-and-spectrum-switches.md

Now see how these pieces fit together in the NVIDIA DGX GB300 SuperPOD reference architecture. Each rack is a liquid-cooled DGX GB300 NVL72 system with eighteen compute trays. Eight racks form one Scalable Unit. Every compute tray has two network adapter families on its front cold-aisle panel. Four ConnectX-8 NICs serve the rail-aligned compute fabric. One dual-port BlueField-3 BF3240 DPU connects to a two-layer Spectrum-4 SN5600 and SN5600D Ethernet fabric.

---

Compare the GPU column with the storage column as you read down the table. They do not grow at the same rate. Plan the storage tier as its own line item, not as a side effect of the GPU count.

---

1. BlueField-3 DPU SKUs, such as the dual-port BF3240, default to DPU mode. Also called Embedded CPU Function Ownership, this mode puts the embedded Arm subsystem, running DOCA Linux, in charge of the NIC resources and the embedded switch.
2. In DPU mode, the first packet of a flow crosses an Arm representor slow path. There the Arm control plane checks policy and programs a hardware flow rule. Later packets then take the hardware fast path directly.
3. BlueField-3 SuperNIC SKUs, such as the BF3140, default to NIC mode and act as a dedicated Spectrum-X RoCEv2 endpoint. The host driver manages Queue Pairs directly. Hardware engines handle Adaptive Routing packet reordering and telemetry-driven congestion control, with no Arm virtual-switch dependency.

---

When a distributed training run slows down on an Ethernet fabric, do not treat the whole switch network as one suspect. That wastes critical triage time. Combine host `ethtool -S` deltas with Spectrum switch queue counters, ECN marks, PFC pause frames, and What Just Happened hardware drop-reason telemetry. Joining those signals routes any incident into one of four root-cause branches.

---

## FILE docs/part-12-ai-networking/12-ethernet-versus-infiniband-a-design-decision-guide.md

Picture a collective step where a single frame is dropped. In Standard RoCEv2, the InfiniBand transport header rides inside UDP, so packets can cross any Layer 3 Ethernet fabric. The catch is that standard Ethernet has no link-layer credit loop. On a traditional reliable connection, one dropped frame forces the sender to retransmit the entire in-flight window, and that retransmission stalls the collective step. Pause frames do not solve everything either, and you should not rely on them alone. Doing so makes upstream switches freeze one after another in a cascading pause tree.

---

Picture a cluster where half the nodes boot into Ethernet mode, while the other half wait for an InfiniBand Subnet Manager. The fix starts with knowing which personality each port is set to. NVIDIA ConnectX-6, ConnectX-7, and ConnectX-8 Virtual Protocol Interconnect adapters can speak either native InfiniBand or Ethernet RoCEv2. They use the same physical ASIC and optical cage for both. The port personality lives in non-volatile firmware configuration, and you control it per port with `mlxconfig`:

---

Suppose every switch port is lossless and congestion-free. A server can still run at a fraction of line rate, because the bottleneck sits inside its own chassis. The internal path does not care which mode the port runs in. Data travels from GPU HBM memory, through the PCIe switch, to the NIC DMA engine, and every hop on that path has to keep up with the wire speed:

---

3. **Run the 128-GPU and 64-GPU H100 TCO and break-even numbers (Volume 21, Chapter 2, Parts 3.2 and 6).** Use the `calculate_64gpu_ib_vs_roce_tco` function.
   - (a) Start from the sixteen-node DGX H100 SXM5 reference. Verify the amortized cost per GPU-hour and the cost per TFLOP-year. Then compare the SXM5 node configuration with the PCIe node configuration.
   - (b) Take a sixty-four-GPU H100 cluster that you might buy, one that compares InfiniBand NDR with 400GbE over a seven-day Llama-70B run. Compute the upfront CapEx savings and the per-run cost. Then add the one-year and three-year extra compute cost, the sensitivity for two larger-model runs, and the break-even run count.

---

## FILE docs/part-12-ai-networking/13-fabric-design-topology-oversubscription-and-scale.md

The training backend fabric uses dedicated high-speed NICs, one for each of the server's eight GPUs. Two NICs per GPU would be technically feasible. Optics cost, NIC power, and switch port scalability favor one NIC per GPU, though. The one-to-one mapping also removes server-side port redundancy and multi-homing overhead.

---

When an RDMA packet reaches an ingress leaf, the leaf slices it into uniform fixed-size cells. It sprays those cells evenly across every spine. The egress leaf reassembles them into the original packet, in exact order, before the packet reaches the destination server. Segmentation and reassembly happen only at the fabric edges. That keeps link utilization near 100 percent, without hash polarization on elephant flows.

---

Virtual Output Queueing handles the blocking problem. Every ingress leaf keeps a separate virtual queue for each egress port in the fabric. A hardware scheduler grants transmission credits only when the target egress port has buffer space. This credit loop keeps congestion inside the flow that causes it. It also gives tighter control than the reactive rate cuts of DCQCN.

---

Once the topology is built, verify the physical cut capacity, audit how evenly uplinks carry routes, and connect the fabric to the job scheduler. Even on a five-stage Clos with oversubscribed super-spines, a job runs at full non-blocking speed when its ranks stay inside one block. NVIDIA Base Command Manager Topograph discovers the physical switch tree. It then configures Slurm to pack communicating ranks inside the same 1,024-GPU block or 32-server rail leaf before they cross spines.

---

## FILE docs/part-12-ai-networking/14-load-balancing-and-routing-for-ai-fabrics.md

Take a three-stage Leaf-Spine Clos fabric. GPU1 connects to LeafA, GPU2 connects to LeafB, and both leaves connect to SpineA, SpineB and SpineC. LeafB advertises GPU2's IP subnet to all three spines. Each spine rewrites the BGP next-hop attribute to itself, then advertises the prefix to LeafA. All three paths carry identical routing metrics and BGP attributes, so LeafA installs one shared hardware ECMP group in its ASIC forwarding table.

---

Telemetry for MPLS and SRv6 is also weaker than in a plain IP fabric. DCQCN compatibility is usually limited or incompatible, and the lossless fabric depends on DCQCN. For that reason, a pure IP fabric is still the better choice for most AI data center deployments. Decide early that the AI fabric itself will run on IP, and keep MPLS at the gateway.

---

A misconfigured load-balancing mode or routing policy shows up in three ways. You see asymmetric link saturation, PFC pause cascades, or RDMA sequence number errors. Here the table maps six production failure modes to their root causes and to fixes you can apply deterministically. You usually meet the symptom first, on a port counter or in a log, so start there.

---

2. **Trace DLB flowlet timers, GLB NNHN, and selective packet spraying.** Use `simulate_dlb_flowlet_and_glb_nnhn`, `classify_sdlb_rocev2_packet` and `build_adc_table_6_1` to analyze path selection. Explain how DLB quality bands, flowlet inactivity timers and reactive path rebalancing work. Then explain why local-only DLB suffers downstream collisions. Finally, describe Tomahawk 5 GLB and sDLB TCAM opcode classification.

---

## FILE docs/part-12-ai-networking/15-nccl-collectives-and-algorithms.md

Treat the anchors in that block as the reference numbers for the rest of the chapter. Infrastructure and performance engineers need to understand the exact mathematics and execution mechanics of NCCL collectives. Those collectives include AllReduce, ReduceScatter, AllGather, Broadcast, Reduce, and AllToAll. You also need the trade-offs among Ring, Double Binary Tree, CollNet with SHARP, NVLS, and Parallel Aggregated Tree. Then come the wire-level details: the LL, LL128, and Simple protocols, bus bandwidth conversion factors, and persistent zero-copy buffer registration. By the end, you will also know when to pair NCCL with NIXL for disaggregated inference.

---

Suppose you try to train a frontier transformer on one GPU. The weights, gradients, optimizer states, and activations will not fit in local HBM. Training would also take far too long. So you spread the model across dozens or thousands of GPUs. That solves the memory problem, but it moves the bottleneck to the interconnect between GPU SMs, NVSwitches, and RDMA NICs. From then on, the network usually limits performance.

---

PyTorch `DistributedDataParallel` avoids much of this with Wait-Free Backpropagation. Autograd hooks group parameters in reverse layer order into 25 MiB gradient buckets. As soon as a bucket fills on the compute stream, DDP launches an asynchronous NCCL AllReduce on a dedicated communication stream. The compute stream keeps calculating gradients for earlier layers while that transfer runs.

---

4. You force `NCCL_ALGO=Ring` on large rank counts or small messages. At 72 GPUs, or at 1,000+ GPUs, Ring pays $2(N-1)$ serial hop latencies, which is 142 steps on 72 GPUs. Below 37.24 MiB, Tree or NVLSTree finishes in logarithmic steps. At 1 MiB on 72 GPUs, Tree runs 4.27x faster.

---

## FILE docs/part-12-ai-networking/16-nccl-topology-channels-transports-and-environment-variables.md

Picture a training run that slowed down after a container update. The GPUs still show work, the job still finishes, and no error appears anywhere. The first sign of trouble is that each iteration takes twice as long, or three times as long, as it did before.

---

When two GPUs on the same host sit on different sockets, or PCIe ACS is enabled in the BIOS, they cannot establish direct P2P. NCCL then uses the Shared Memory transport and stages buffers through `/dev/shm`. In Docker and Kubernetes containers, the default `/dev/shm` mount is tiny, and that is what triggers `NCCL WARN Call to posix_fallocate failed : No space left on device`. Mount a multi-gigabyte in-memory volume at `/dev/shm`, and never leave `NCCL_SHM_DISABLE=1` set in production.

---

When you read the script, start from the top. The first block turns on diagnostics and error handling, and the second makes the transports explicit. Uncomment the `NCCL_TOPO_FILE` line only on a VM or OEM server with a broken PCIe tree.

---

1. This one covers path scoring and the NVLink versus SYS step penalty. Using the `nvidia-smi topo -m` matrix in Section 1.2 and the parameters below, rank the seven NCCL topology levels from lowest cost to highest cost. Then compute the transfer time in milliseconds for a 500 MB tensor over NV4 and over SYS, along with the slowdown multiplier. Finally, state the SM utilization and iteration time before and after you switch to a topology-aware overlapped schedule.
2. This one asks you to read an XML topology graph. Using `parse_nccl_topo_xml` on the dual-socket XML hierarchy below, find the exact NCCL path level for each of the four GPU-to-NIC pairs. Then say which pairs qualify for GPUDirect RDMA when `NCCL_NET_GDR_LEVEL` is set to PIX, and which qualify when it is set to PXB.
3. This one is about channels, SM occupancy, and buffer memory. Using `evaluate_channels_and_buffers` on the 132-SM H100 configurations below, calculate the CUDA SM thread blocks used by the default 16-channel ring. Also compute the percentage of H100 SMs that it occupies, and the total channel buffer memory in MiB. Then repeat the calculation for the clamped 8-channel ring and for the zero-copy registered NVLS configuration.
4. This one tests transport selection under environment overrides. Using `select_nccl_transport`, state the exact selected transport, the log prefix, and the GPUDirect RDMA boolean for each of the five scenarios below.
5. This one covers interface and HCA filters and the 64-socket rule. Using `evaluate_nccl_filter` and `evaluate_socket_transport_limits`, write the exact list of matched interfaces and HCAs for each filter expression below. Then compute the total sockets for the three thread-and-socket pairs, and check each one against the 64-socket ceiling. Last, calculate the aggregate bandwidth in Tbps for two and for four 800 Gbps NICs.
6. This one works through the Kubernetes single-NUMA-node failure. Using `evaluate_k8s_numa_pod_scheduling` on the 128-core, 8-GPU server below, show why 8 pods requesting 16 CPU cores and 1 GPU each hit `TopologyAffinityError`. State the exact free cores and free GPUs that remain on each NUMA node. Then give the maximum integer CPU core request per pod that admits all 8 pods, and explain why `NCCL_IGNORE_CPU_AFFINITY=1` is needed.

---

## FILE docs/part-12-ai-networking/17-nccl-tests-and-fabric-benchmarking.md

Before you start, finish Chapter 12.14 on GPUDirect RDMA and GPUDirect Storage. It explains BAR1 peer memory, `nvidia_peermem`, PCIe Access Control Services, and PIX versus SYS NUMA locality. You also need Chapters 12.15 and 12.16. Those chapters cover the Ring, Tree, CollNet/SHARP, NVLS and PAT algorithms, and how NCCL picks a transport among P2P, SHM, NET/IB and NET/Socket.

---

Every figure in this block, including the 58.2 GB/s multi-node row and the 361.36 GB/s row with its 90 percent per-rail share, comes from the handbook's own arithmetic practice and not from a run on real hardware. Treat the 80 percent gate as unsourced policy. For what is sourced, see the nccl-tests lab in chapter 19.5.

---

When a large job hangs, or starts with a broken NVLink pair, digging through thousands of log files across hundreds of nodes can waste hours. Modern NCCL releases include two built-in diagnostics that name faulty hardware and lagging ranks directly.

---

Split the $N$ nodes into two halves of $N/2$ nodes each, and run `all_reduce_perf` on each half. The half with the degraded `busbw` holds the straggler. The other half is proven healthy, so it becomes a known-good partner once the suspect group shrinks to a single node. Keep halving the suspect group until one node is left. That takes $\lceil \log_2 N \rceil$ split steps. Then test each InfiniBand rail on that node separately, by restricting `NCCL_IB_HCA` or by running `ib_write_bw` per rail alongside `ibdiagnet` and `perfquery`.

---

## FILE docs/part-12-ai-networking/18-nccl-debugging-hangs-timeouts-and-errors.md

Even when a job does not crash, it can quietly lose most of its speed. A silent fallback to CPU-staged communication, or a communicator rebuilt inside the training step, wastes nearly all the accelerator capacity you paid for. A single degraded NVLink lane or an imbalanced storage shard can stall a whole multi-node job the same way. This chapter gives you a deterministic, four-layer debugging method. It covers process launch limits, bootstrap rendezvous, runtime Flight Recorder and RAS telemetry, and hardware Xid and fabric correlation.

---

Read the category column first, then the signature column, which tells you which log line to search for. Two lessons stand out from these 419 interruptions. GPU silicon and memory faults caused 268 of them, which is 64.0% of the total. That outnumbers network switch, cable, and NIC failures by more than 6.3x. The second lesson comes from the barrier behaviour of collectives. One faulty GPU blocks the other 16,383 GPUs inside `ncclAllReduce` until the watchdog aborts the job.

---

Even with a correctly sized `/dev/shm`, your job can fail at Layer 1, or hang at Layer 2, before a single collective kernel runs. Host memory-pinning ceilings block RDMA verb registration. Mismatched Slurm PMI plugins, unreachable container bridges, or narrow ephemeral port ranges stall the TCP bootstrap handshake.

---

When a 1,024-GPU job times out on collective sequence 4821, reading 1,024 separate log files by hand is slow and error-prone. Without structured per-rank state, you cannot tell whether one rank never called the collective, or whether all 1,024 ranks stalled mid-transfer on the network.

---

## FILE docs/part-12-ai-networking/19-gpudirect-rdma-and-gpudirect-storage.md

GPUDirect RDMA and GPUDirect Storage are the two halves of the NVIDIA Magnum IO zero-copy architecture. Together they take the host memory bounce buffer out of the data plane. The CPU stays in the control plane, but it no longer touches the bytes. GPUDirect RDMA maps GPU HBM directly to the network adapter over the local PCIe switch. GPUDirect Storage streams dataset shards and checkpoints straight between NVMe or NVMe-oF storage and GPU memory.

---

1. The GPU must expose its HBM physical pages in the system's 64-bit PCIe Memory-Mapped I/O address space, through Base Address Register 1 (BAR1).
2. The GPU driver must pin the virtual CUDA allocation from `cudaMalloc` or `cuMemCreate`. Pinning keeps the physical HBM pages from being migrated or evicted while the RDMA Memory Region is active.
3. A kernel bridge must translate the GPU virtual address range into PCIe BAR1 physical bus addresses. It then hands that scatter-gather table to the RDMA ib_core subsystem.

---

Take the `gdsio` rows as a worked example. The GDS path reaches 9.6 GB/s. The CPU-staged path reaches 8.0 GB/s. Measure the gap against the 8.0 GB/s baseline, and you get the 20 percent throughput gain in the table. Latency runs the other way: it falls from 1.25 ms to 1.00 ms, and that drop is the same 20 percent of the baseline. If your training jobs spend their time waiting in dataloader workers, check whether the storage path still goes through the page cache.

---

An application, or a framework plugin such as NVIDIA DALI, PyTorch v2.7.0+, kvikio, cuDF, or the NIXL GDS backend, runs the `cuFile` API sequence to use GPUDirect Storage. One limit matters before you start. If a filesystem is mounted through user-space FUSE rather than a kernel module with direct I/O support, `nvidia-fs.ko` cannot intercept the DMA mapping callbacks. True zero-copy GDS is therefore impossible on FUSE mounts.

---

## FILE docs/part-12-ai-networking/20-sharp-and-in-network-computing.md

Notice the last row, because it is the one you will feel in your job. The wall-time saving comes from overlapping the two phases, so the volume figures alone do not show it. When you estimate collective traffic, first decide which path it takes, because the two paths differ by roughly a factor of $N - 1$.

---

In exact real arithmetic, addition is associative: $(a + b) + c = a + (b + c)$. Floating-point arithmetic does not share that property. Every intermediate sum rounds to a finite mantissa, so the order of the additions can change the result.

---

On a traditional HPC cluster, or a hybrid MPI plus PyTorch cluster launched with Slurm PMIx and OpenMPI, MPI collectives skip NCCL. They go through the OpenMPI Modular Component Architecture instead. Without explicit configuration, `MPI_Allreduce` runs on host CPUs over standard point-to-point RDMA. NVIDIA speeds up MPI collectives with the Hierarchical Collectives library, `coll_hcoll`.

---

SHARP and NVLS failures seldom crash a job with a clean stack trace. Instead, the job slows down, falling back to host-based Ring or Tree algorithms with a 2x to 5x collective slowdown. Or it stalls during communicator initialization, when switch AN quotas leak. The table is a symptom-to-fix lookup. Each row names what you see, the cause behind it, and the fix.

---

## FILE docs/part-12-ai-networking/21-storage-networks-ultra-ethernet-and-scale-up-fabrics.md

1. **AI storage networks.** Curated training datasets must stream continuously into GPU memory. Multi-terabyte checkpoints must also flush to flash without pausing the training steps. A local PCIe drive responds in roughly a hundred nanoseconds. But a drive inside one server cannot hold a petabyte-scale corpus, and it cannot give thousands of nodes a shared namespace. Dedicated storage fabrics bridge that gap. They connect compute servers to shared flash arrays using NVMe-o-TCP, NVMe-o-RDMA over RoCEv2, and parallel file systems with GPUDirect Storage.

---

Figure 9-8 shows this hybrid layout. At the bottom, an artificial intelligence server has storage network interface cards A and B. Network interface card A connects to leaf1, and network interface card B connects to leaf2. Both connections support read and write operations. Two fabrics carry the on-premises traffic. Fabric A holds leaves 1 and 2 and connects to spine 1 and spine 2. Fabric B holds spines 3 and 4, with leaves 3 and 4 to on-premises storage arrays. Leaves 5 and 6 reach a firewall cluster. Two data center gateways then connect to cloud1 and cloud2 storage. Fabric B also carries spine3 and spine4, with leaf3 and leaf4 connected to both. Cloud-based replication keeps snapshots of the local training cluster from being lost.

---

Two servers form a one-to-one relationship during session setup. The initiator and target start that relationship at the API and Libfabric levels. Libfabric turns the requirements into network and target memory parameters, and SES and PDS then use those parameters. Each server's stack runs from the application down through Libfabric, SES, PDC, PDS, UDP, IP, and MAC.

---

A misconfigured storage fabric, UEC link, or scale-up pod rarely prints an obvious protocol error. The job just runs slowly, stalls, or produces wrong numbers. The table maps each of the common symptoms to its likely cause and to the fix. Start from the symptom you can see, then work back to the layer that caused it. When a job fails, match the symptom against this list first.

---

## FILE docs/part-12-ai-networking/22-ai-network-telemetry-and-kpis.md

Follow the diagram from left to right, as you would follow a packet through the fabric. The original flow arrives at the destination untouched. The clone collects a record at each hop, and the terminating node sends that record to the collector.

---

This chapter includes a lab that checks its own math. The lab lives in `code/part12/ai_network_telemetry_kpis.py` and `code/part12/ai_network_telemetry_kpis_lab.py`, so you can read the code next to the results. It runs locally on a Nebius GPU node or a workstation, and it uses only the Python standard library. The 31 self-checks cover every KPI equation, the MLPerf rules, the IFA header and stack layouts, the `perfquery` delta classification, RoCEv2 correlation, and the telemetry cardinality math.

---

Work the exercises in order, because later ones reuse ideas from earlier ones. You will need your own notes for each answer. Each one names the function to use from the chapter's code. The inputs for all six are collected in the block at the end of this section, so use them exactly as written.

---

1. Exercise 1 asks how a tail stall inflates Job Completion Time. Use `compute_jct_and_tail_latency_impact` with the inputs below. First calculate the ideal step time, the communication fraction, and the total Job Completion Time in hours. Then compute the degraded step time, the communication fraction, the degraded JCT, the slowdown ratio, and the wasted GPU-hours under the spine microburst.
2. Exercise 2 compares scaling efficiency with power efficiency. Use `compute_strong_and_weak_scaling` and `compute_power_and_efficiency_kpis` with the parameters below. Find the strong speedup, the strong efficiency, and the weak efficiency. Then calculate PUE, GFLOPS per watt, TPW, and QPW for the Scalable Unit.
3. Exercise 3 traces one packet through a three-stage fabric. Use `analyze_ifa_flow_trace` on the trace below. Compute the fixed IFA header bytes, the metadata stack bytes, the total overhead, and the tagged packet size. Then find each hop's residence time, the total residence time, the wire time, the end-to-end latency, the bottleneck device ID, and the export protocol.
4. Exercise 4 triages four InfiniBand switch ports. Use `evaluate_infiniband_port_telemetry` and `evaluate_symbol_error_acceleration` to classify the health state, alert severity, and remediation for each port below. Then compute the daily symbol error rate across both three-day windows, and the acceleration factor for switch port 12.
5. Exercise 5 triages five RoCEv2 interfaces. Use `evaluate_rocev2_congestion_and_fec`, and classify the operational state and required fix for each interface in the input block.
6. Exercise 6 looks at rail skew and telemetry cardinality, the kind of check you would run before you turn on flow labels. Use `evaluate_rail_bandwidth_skew` and `estimate_telemetry_scale_and_cardinality` with the parameters below. Compute the max/min rail skew ratio and explain the `> 5e9` bytes/s PromQL floor clause. Then calculate the active time-series count and the sample ingestion rate, with and without the 5-tuple flow labels.

---

## FILE docs/part-12-ai-networking/23-fabric-validation-and-capacity-planning.md

The same trap appears on RoCEv2 Ethernet. A new GPU rack passes optical checks, an ICMP `ping`, and a two-node bandwidth test. One week after it joins shared production, multi-rank AllReduce and AllToAll jobs stall. The switches show heavy ECN marking, which is a signal that queues are filling, along with Priority Flow Control pauses and hardware tail drops.

---

Good cabling is not enough by itself. If Slurm's static `topology.conf` file drifts out of sync, Slurm places jobs across switches that are far apart. In NVIDIA Base Command Manager clusters, `cmsh` can discover MAC addresses and map them to switch ports. It also works with Topograph to generate Slurm tree and block topologies automatically. From `cmsh`, operators can look up host MAC locations, map breakout ports, preview switch MAC assignments, and rotate factory default switch passwords.

---

Size a fabric by summing switch port speeds and you will build bottlenecks that stall the synchronous collective jobs running on it. A rigorous capacity model starts by finding the bottleneck cut. That is the exact set of links separating the active senders from their receivers. It then divides the demand crossing that cut by the usable link capacity. Production clusters must survive planned maintenance and single hardware faults. So you evaluate every cut twice: in its normal state and in its N-1 state, where one link or spine is out of service.

---

The same cut math also decides InfiniBand leaf radix and AllReduce step time. Take a constrained leaf with half as many uplinks as downlinks, instead of a non-blocking leaf. Cross-rack bandwidth per node drops in half, so a large AllReduce transfer takes twice as long. Now suppose that two-spine fabric loses one spine during a job. Per-node bandwidth falls to a quarter of line rate, and the AllReduce takes four times as long.

---

## FILE docs/part-12-ai-networking/24-ai-networking-troubleshooting-playbook.md

Guessing makes the outage longer. Tuning NCCL environment variables at random, raising process-group timeouts or disabling flow control on live switches only prolongs the outage. Clearing port counters or rebooting nodes before you capture evidence destroys the trail you need to prove the root cause. A reliable response follows a deterministic, bottom-up playbook with three rules:

---

Suppose an InfiniBand training job hangs halfway through a collective, or one that starts slowly and never recovers. Guessing at software flags wastes hours in that moment. A better approach is a strict bottom-up sequence. Check the physical signal, the Subnet Manager, routing, host RDMA, GPUDirect RDMA, fabric congestion and rank health, in that order. Do not move to the next gate until the current one passes with concrete counter evidence.

---

A path can pass a bandwidth check and still stall a large training run. Averages are the trap here. Synchronous collectives across hundreds of GPUs run at the speed of the slowest completion, so tail latency sets the step time. If you look only at typical or average latency in `ib_write_lat`, you miss these intermittent micro-stalls. For example, the degraded path below reports a typical latency of 1.58 us, which looks healthy on its own.

---

Read the table column by column. Case A rises on the error counters, Case B rises only on the wait counters, and Case C pins the wait counter inside a closed loop. Each case has its own fix. If the error counters rise, clean or replace the media first. If only the wait counters rise, rebalance the routes or the placement.

---

