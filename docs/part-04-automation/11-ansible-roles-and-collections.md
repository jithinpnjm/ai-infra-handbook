---
id: "c04-11"
title: "4.11 Ansible roles and collections"
sidebar_label: "4.11 Ansible roles and collections"
sidebar_position: 11
description: "Reusable Ansible: role structure and conventions, defaults versus vars, argument specs, dependencies, role design for GPU nodes, Galaxy and collections, building and publishing a collection, versioning and repository layout"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 4.11 Ansible roles and collections

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | ansible-core, ansible-galaxy, Molecule optional |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

A GPU cluster's configuration is a stack of concerns that repeat on every node: base OS hardening, time sync, drivers, container runtime, monitoring agents, Slurm clients, filesystem mounts, NCCL tuning. If each lives as an ad-hoc block in a giant playbook, nothing can be reused, tested or versioned. Roles package a unit of configuration behind a clean interface; collections package roles, modules and plugins for distribution. NVIDIA's DeepOps, Kubespray, and most vendor automation are role- and collection-based, and your own platform repository will be too. Good role design is what lets a team of five operate a thousand nodes.

## Prerequisites and outcomes

Needs 4.3 to 4.10. After this chapter you can:

- Create and structure roles with `tasks`, `handlers`, `defaults`, `vars`, `templates`, `files`, `meta`, `library`, `molecule`, and know what each directory is for.
- Apply the interface principle: inputs through documented `defaults/` variables validated by `argument_specs`, no hidden coupling.
- Use roles from playbooks (`roles:`, `import_role`, `include_role`, `tasks_from`), pass parameters, handle dependencies and run order.
- Write OS-portable roles (variables per OS family, `first_found`), idempotent and testable.
- Install and pin third-party roles and collections (Galaxy, Git, Automation Hub, `requirements.yml`), and build, test, version and publish your own collection.
- Organise a repository with playbooks, roles, collections and inventories for a multi-team platform.

## 1. Anatomy of a role

```text
roles/gpu_driver/
├── defaults/main.yml          # public interface: low-precedence defaults users override
├── vars/main.yml              # internal constants (high precedence; avoid user-facing settings here)
├── vars/Debian.yml            # OS-specific internal values (loaded with include_vars/first_found)
├── tasks/main.yml             # entry point
├── tasks/install.yml          # split big roles into task files
├── tasks/configure.yml
├── tasks/validate.yml
├── handlers/main.yml
├── templates/                 # Jinja2 (*.j2)
├── files/                     # static files copied as-is
├── meta/main.yml              # galaxy metadata, dependencies, supported platforms
├── meta/argument_specs.yml    # input validation + documentation
├── library/                   # role-local modules (optional)
├── module_utils/, plugins/    # role-local plugins (optional; usually in collections)
├── README.md                  # purpose, variables, examples, tested platforms
└── molecule/default/          # tests (4.13)
```

Create a skeleton with `ansible-galaxy role init gpu_driver` (or `ansible-galaxy init`). Ansible searches `roles_path`, a `roles/` directory next to the playbook, and installed collections (`namespace.collection.role`).

### defaults versus vars

- **`defaults/main.yml`** are the lowest-precedence variables: the role's **public API**. Everything a user may reasonably change belongs here with safe defaults.
- **`vars/main.yml`** have high precedence and cannot be overridden by inventory: use sparingly for internal constants or OS-specific mappings the user should not change. A setting placed here and later needed by someone becomes a fight with precedence; if in doubt use `defaults`.
- **Prefix every variable with the role name** (`gpu_driver_branch`, `gpu_driver_blacklist_nouveau`) to avoid collisions across roles (variables are global to the play) and to document origin.
- Distinguish **public** (documented, stable) from **private** variables (prefix with `__role_` by convention).

```yaml
# roles/gpu_driver/defaults/main.yml
gpu_driver_branch: "550"                     # nvidia driver branch
gpu_driver_package_type: "open"              # open | proprietary
gpu_driver_persistence_mode: true
gpu_driver_blacklist_nouveau: true
gpu_driver_hold_packages: true
gpu_driver_fabric_manager: "{{ ansible_local.gpu.nvswitch | default(false) }}"
gpu_driver_validate_gpu_count: 0             # 0 disables the count check
```

### tasks, handlers and entry points

```yaml
# roles/gpu_driver/tasks/main.yml
- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ lookup('ansible.builtin.first_found', params) }}"
  vars:
    params:
      files:
        - "{{ ansible_facts['distribution'] }}-{{ ansible_facts['distribution_major_version'] }}.yml"
        - "{{ ansible_facts['os_family'] }}.yml"
        - default.yml
      paths: ["{{ role_path }}/vars"]

- name: Prerequisites
  ansible.builtin.import_tasks: prerequisites.yml
  tags: [gpu_driver_prereq]

- name: Install driver
  ansible.builtin.import_tasks: install.yml
  tags: [gpu_driver_install]

- name: Configure
  ansible.builtin.import_tasks: configure.yml
  tags: [gpu_driver_config]

- name: Validate
  ansible.builtin.import_tasks: validate.yml
  when: gpu_driver_validate_gpu_count | int > 0
  tags: [gpu_driver_validate]
```

```yaml
# roles/gpu_driver/handlers/main.yml
- name: gpu_driver | reload nvidia persistence daemon
  ansible.builtin.systemd_service:
    name: nvidia-persistenced
    state: restarted
    daemon_reload: true
```

Handler names are global in a play: namespace them (`role | action`) to avoid collisions.

### meta and dependencies

```yaml
# roles/gpu_driver/meta/main.yml
galaxy_info:
  author: Platform team
  description: Install and configure NVIDIA data-centre drivers
  license: Apache-2.0
  min_ansible_version: "2.16"
  platforms:
    - { name: Ubuntu, versions: [jammy, noble] }
    - { name: EL, versions: ["8", "9"] }
  galaxy_tags: [nvidia, gpu, driver]
dependencies:
  - role: common_base                # runs before this role; keep dependency lists short
```

Dependencies run first, once per play unless `allow_duplicates: true` or parameters differ. Prefer explicit composition in playbooks over deep implicit dependency chains (hard to read, hard to test); use dependencies only for true prerequisites.

### Argument specs: the role's contract

```yaml
# roles/gpu_driver/meta/argument_specs.yml
argument_specs:
  main:
    short_description: Install and configure the NVIDIA driver
    options:
      gpu_driver_branch:
        type: str
        default: "550"
        description: Driver branch to install.
        choices: ["535", "550", "555"]
      gpu_driver_persistence_mode:
        type: bool
        default: true
      gpu_driver_validate_gpu_count:
        type: int
        default: 0
        description: Expected number of GPUs (0 disables validation).
```

Ansible validates role parameters and variables against the spec at run time, fails early with a clear message, and the spec doubles as documentation (`ansible-doc -t role`). Define separate entry points (`main`, `upgrade`, `validate`) when a role has multiple task files callable via `tasks_from`.

## 2. Using roles

```yaml
# Classic: roles run before tasks in the play
- hosts: gpu
  become: true
  roles:
    - common_base
    - role: gpu_driver
      vars: { gpu_driver_branch: "550", gpu_driver_validate_gpu_count: 8 }
      tags: [driver]
    - { role: dcgm, when: "'gpu' in group_names" }

# Static import (fixed at parse time)
- hosts: gpu
  tasks:
    - ansible.builtin.import_role: { name: gpu_driver }

# Dynamic include (runtime decisions, loops, other entry point)
- hosts: gpu
  tasks:
    - name: Run only the validation entry point
      ansible.builtin.include_role:
        name: gpu_driver
        tasks_from: validate
      vars: { gpu_driver_validate_gpu_count: 8 }

    - name: Apply a role once per item
      ansible.builtin.include_role: { name: mount_fs, apply: { tags: [mounts] } }
      loop: "{{ filesystems }}"
      loop_control: { loop_var: fs }
```

Run order: `pre_tasks` → role dependencies and roles → `tasks` → `post_tasks`; handlers flush between sections. A play can mix roles and tasks. `import_role`/`include_role` allow running roles inside the task flow (e.g., after a reboot or after a drain step), which `roles:` cannot.

## 3. Designing good roles

1. **Single responsibility.** One role installs and configures one thing (`gpu_driver`, `container_toolkit`, `chrony`, `slurm_client`, `dcgm_exporter`). A role named `everything` is a playbook in disguise.
2. **Declarative interface, idempotent tasks.** The role converges to the state described by variables; running twice changes nothing (4.6).
3. **No hidden dependencies on inventory structure.** A role should not assume `groups['gpu']` exists; pass the needed data as variables (or document the requirement and assert it) so it is reusable.
4. **Portable by default, explicit when not.** Use `ansible_facts['os_family']` mappings for package names and paths; fail with a clear `assert` on unsupported platforms rather than half-working.
5. **Validate inputs** with argument specs and early `assert`s; **validate outputs** with a `validate` task file that checks real behaviour (`nvidia-smi -L` count, service active, port open).
6. **Safe by default**: no destructive actions without an explicit variable (`gpu_driver_allow_downgrade: false`), no reboots unless `role_allow_reboot: true`, and handle reboot-required flows by returning a fact the playbook can act on (`gpu_driver_reboot_required`).
7. **Check-mode friendly**: read-only probes with `check_mode: false`; avoid failing in `--check` because of earlier unmade changes.
8. **Small, composable task files** (`install`, `configure`, `service`, `validate`) selectable by tags or `tasks_from`.
9. **Document** variables, tags, supported platforms and examples in `README.md`; keep `CHANGELOG.md`; semantic versions.
10. **Test** with Molecule scenarios and linters (4.13).
11. **Don't hide secrets in roles**: accept secrets via variables supplied from Vault/secret stores; use `no_log` internally.
12. **Avoid role-level `vars/` for knobs**, avoid `set_fact` leaking global names; prefer `__role_private` names.

### Example: a compact role for kernel tuning

```yaml
# roles/kernel_tuning/defaults/main.yml
kernel_tuning_sysctl:
  vm.swappiness: 1
  vm.max_map_count: 1048576
  kernel.numa_balancing: 0
  net.core.rmem_max: 268435456
kernel_tuning_sysctl_extra: {}
kernel_tuning_hugepages: 0
kernel_tuning_cpu_governor: performance
kernel_tuning_modules_load: []

# roles/kernel_tuning/tasks/main.yml
- name: Apply sysctl settings
  ansible.posix.sysctl:
    name: "{{ item.key }}"
    value: "{{ item.value }}"
    sysctl_file: /etc/sysctl.d/90-kernel-tuning.conf
    reload: true
  loop: "{{ kernel_tuning_sysctl | combine(kernel_tuning_sysctl_extra) | dict2items }}"
  loop_control: { label: "{{ item.key }}" }

- name: Load modules at boot
  ansible.builtin.copy:
    dest: /etc/modules-load.d/kernel-tuning.conf
    content: "{{ kernel_tuning_modules_load | join('\n') }}\n"
    mode: "0644"
  when: kernel_tuning_modules_load | length > 0

- name: Set CPU governor
  ansible.builtin.command: cpupower frequency-set -g {{ kernel_tuning_cpu_governor }}
  changed_when: false
  failed_when: false           # tolerate VMs without cpufreq; real roles probe /sys first
```

Users override with group_vars: `kernel_tuning_sysctl_extra: { vm.dirty_ratio: 10 }`, keeping the defaults intact via `combine`.

## 4. Galaxy, requirements and sourcing third-party content

```yaml
# requirements.yml
roles:
  - name: geerlingguy.docker
    version: "7.4.1"
  - src: https://git.example.com/platform/ansible-role-chrony.git
    scm: git
    version: v2.3.0
    name: platform.chrony

collections:
  - name: community.general
    version: ">=8.0.0,<10.0.0"
  - name: kubernetes.core
    version: "4.0.0"
  - name: https://git.example.com/platform/ansible-collection-gpu.git
    type: git
    version: 1.4.0
```

```bash
ansible-galaxy role install -r requirements.yml -p roles/
ansible-galaxy collection install -r requirements.yml -p collections/
ansible-galaxy collection list
ansible-doc -t role platform.chrony        # documentation from argument specs
```

Guidance: **pin exact versions** (or tight ranges) and commit `requirements.yml`; mirror dependencies in an internal Automation Hub/Artifactory/Git for availability and supply-chain control; review third-party code before use (roles run as root on your fleet); prefer maintained, collection-packaged roles; vendor critical roles if you cannot trust upstream continuity; run `ansible-lint` and Molecule against upgraded versions in CI before promoting.

## 5. Collections

A **collection** is the distribution format for Ansible content: a namespaced package (`namespace.name`) containing modules, plugins (filter, lookup, inventory, callback, connection), roles, playbooks and documentation. Content is referenced by FQCN (`community.general.ufw`, `nvidia.gpu.gpu_driver`).

```text
ansible_collections/acme/gpu/
├── galaxy.yml                  # name, namespace, version, dependencies, build_ignore
├── README.md, CHANGELOG.rst
├── meta/runtime.yml            # requires_ansible, plugin routing/deprecations
├── plugins/
│   ├── modules/                # custom modules (Python), e.g. gpu_facts.py
│   ├── module_utils/
│   ├── filter/                 # custom filters
│   ├── lookup/ inventory/ callback/ ...
│   └── doc_fragments/
├── roles/
│   ├── gpu_driver/ ...
│   └── dcgm/ ...
├── playbooks/                  # shipped example/entry playbooks
├── docs/ and tests/            # sanity, unit, integration tests (ansible-test)
└── changelogs/                 # antsibull-changelog fragments
```

```yaml
# galaxy.yml
namespace: acme
name: gpu
version: 1.4.0
readme: README.md
authors: [Platform team]
description: GPU node automation for the AI platform
license: [Apache-2.0]
dependencies:
  community.general: ">=8.0.0"
  ansible.posix: ">=1.5.0"
repository: https://git.example.com/platform/ansible-collection-gpu
build_ignore: [".git", "*.tar.gz", "molecule"]
```

Workflow:

```bash
ansible-galaxy collection init acme.gpu           # skeleton
ansible-galaxy collection build                   # creates acme-gpu-1.4.0.tar.gz
ansible-galaxy collection install ./acme-gpu-1.4.0.tar.gz -p collections/
ansible-galaxy collection publish acme-gpu-1.4.0.tar.gz --server automation_hub   # or upload to Artifactory/Galaxy-compatible server
ansible-test sanity --docker default              # style, docs and import checks (run from ansible_collections/acme/gpu)
ansible-test units
ansible-test integration
```

Practices: semantic versioning with a changelog (breaking changes bump major); `meta/runtime.yml` for `requires_ansible` and deprecations; module documentation in `DOCUMENTATION`/`EXAMPLES`/`RETURN` blocks (4.15); CI that builds, lints, tests and publishes on tags; treat the collection like a library with a public interface and a deprecation policy.

### Where to put what

| Content | Home |
|---|---|
| A playbook that glues a particular environment together | Environment/platform repo |
| A reusable unit of configuration | Role (inside a collection if shared across teams) |
| Custom module/filter/lookup/inventory plugin | Collection `plugins/` |
| Group/host variables and inventories | Environment repo (not in roles/collections) |
| Secrets | Vault/secret manager, never in roles |

## 6. Repository layout for a platform team

```text
platform-automation/
├── ansible.cfg
├── requirements.yml
├── collections/                 # installed deps (gitignored) or vendored
├── inventories/{prod,staging,lab}/
├── playbooks/
│   ├── site.yml
│   ├── gpu_nodes.yml
│   ├── slurm.yml
│   └── maintenance/{drain_and_patch.yml,rotate_certs.yml}
├── roles/                       # roles not yet promoted to a collection
├── molecule/ or tests/
├── .ansible-lint, .yamllint, .pre-commit-config.yaml
└── .github/workflows/ci.yml
```

Promote roles from the monorepo into a versioned collection when more than one team consumes them; consume them via `requirements.yml` with pinned versions. Keep playbooks thin (host selection, variable wiring, ordering) and roles fat (the actual logic).

## 7. Role patterns specific to GPU infrastructure

- **Hardware-aware behaviour through facts and variables**: probe GPUs in a `gpu_facts` task (`lspci -d 10de:`, `nvidia-smi -L`, `nvidia-smi nvlink -s`, NVSwitch presence) and publish `ansible_local.gpu.*`; other roles branch on those facts rather than on group names alone.
- **Driver install flows**: handle pre-existing drivers and `nouveau` blacklisting, DKMS vs precompiled modules, package holds, reboot requirements, Fabric Manager on NVSwitch systems, `nvidia-persistenced`, MIG configuration, and validation (`nvidia-smi`, `dcgmi diag -r 1`). Expose a `reboot` decision to the caller.
- **Container runtime**: NVIDIA Container Toolkit configuration for containerd/Docker/CRI-O as a separate role from the driver.
- **Idempotent upgrades**: roles must support changing versions: detect installed version, unload modules if needed, install, verify; refuse to downgrade unless explicitly allowed.
- **Order of roles** on a node: base OS and kernel → drivers → container runtime → monitoring → scheduler/Kubernetes agents → workload prerequisites; document this in the playbook, not hidden in role dependencies.
- **NVIDIA-provided automation** (DeepOps, `nvidia.nvue` for Cumulus/Spectrum switches, network operator manifests, BCM Python/CLI) can be consumed as roles/collections but must be pinned and reviewed like any dependency.

## 8. Lab (untested)

1. **Extract a role**: take the playbook from 4.9 and extract `app_deploy`, `nginx_proxy`, `postgres` roles; keep behaviour identical (verify with `--check --diff` and a second run).
2. **Interface design**: write `defaults/main.yml` with prefixed variables, `meta/argument_specs.yml`, and `README.md`; test invalid input and see the argument spec error; view with `ansible-doc -t role`.
3. **OS portability**: add `vars/Debian.yml` and `vars/RedHat.yml` with package names; load with `first_found`; run on both families (containers).
4. **Entry points**: split `install`, `configure`, `validate`; call `validate` alone with `include_role: tasks_from`; show how `import_role` vs `roles:` differ for tags and `--list-tasks`.
5. **Dependencies**: create two roles with a dependency; observe run-once semantics and `allow_duplicates`; then replace the dependency with explicit playbook ordering and compare clarity.
6. **Precedence experiment**: put a variable in a role's `vars/main.yml` and `defaults/main.yml`; try overriding from `group_vars`; show why interface variables belong in `defaults`.
7. **Requirements**: write `requirements.yml` with pinned roles and collections (Galaxy and Git); install into local paths; list; break a pin and see the effect.
8. **Collection**: create `acme.gpu` with one role, one filter plugin (3.11 decorators) and one tiny module (4.15); build, install from the tarball, and use by FQCN; run `ansible-test sanity`.
9. **Kernel tuning role**: implement the example with `combine`; override with group vars; run in check mode; add a validate step reading `sysctl -n`.
10. **GPU facts role**: write a role publishing `ansible_local.gpu`; use it from a driver role to decide Fabric Manager installation.
11. **Lint and test**: run `ansible-lint` on the roles; add a Molecule scenario (4.13).
12. **Clean up.**

Mark tested only after execution.

## 9. Common mistakes

- Roles that are really whole playbooks, or roles split so finely that every playbook needs twenty of them.
- Unprefixed variable names causing collisions; interface variables in `vars/`; hidden reliance on inventory groups.
- Deep dependency chains and `allow_duplicates` tricks; implicit ordering nobody can see.
- Missing input validation: the role fails with obscure errors on a typo.
- Hard-coded package names/paths for one distro; no platform assertions.
- Unpinned Galaxy dependencies that change underneath you; unreviewed third-party roles running as root.
- Non-idempotent roles; handlers with unnamespaced names clobbering each other.
- Secrets embedded in role files; roles that reboot machines unexpectedly.
- No README, no tests, no changelog; breaking interface changes without a major version bump.
- Mixing environment data (inventories) into shared roles/collections.

## 10. Interview angles

- "What is a role? Structure? `defaults` vs `vars`?" 
- "How do you design a role interface? How do you validate arguments?" (prefixed defaults, argument specs, asserts.)
- "Role vs collection; when do you build a collection?" 
- "How do you manage third-party dependencies safely?" (pin, mirror, review, test upgrades.)
- "`import_role` vs `include_role` vs `roles:`?" 
- "How would you make a role portable across Ubuntu and RHEL?" 
- "How do you structure automation for several teams and environments?" 
- "How do you version and release shared Ansible content?" (SemVer, changelog, CI, Hub/Artifactory.)

## 11. Checkpoint questions (30)

1. What command creates a role skeleton? **A:** `ansible-galaxy role init`.
2. What is `defaults/main.yml` for? **A:** Overridable public variables with lowest precedence.
3. When use `vars/main.yml`? **A:** Internal constants not meant to be overridden.
4. Why prefix variables? **A:** Avoid collisions in global play scope.
5. What are argument specs? **A:** Validation and documentation of role inputs.
6. Where do argument specs live? **A:** `meta/argument_specs.yml`.
7. What is `meta/main.yml` for? **A:** Galaxy info and dependencies.
8. When do dependencies run? **A:** Before the role, once per play unless duplicates allowed.
9. `import_role` vs `include_role`? **A:** Static vs dynamic.
10. How call one entry point? **A:** `include_role: tasks_from`.
11. What order do roles run relative to tasks? **A:** Before `tasks` (after `pre_tasks`).
12. How make roles portable? **A:** Per-OS vars via facts and `first_found`.
13. Why namespace handler names? **A:** Handlers are global to the play.
14. What file pins dependencies? **A:** `requirements.yml`.
15. How install collections from it? **A:** `ansible-galaxy collection install -r`.
16. What is a collection? **A:** Namespaced package of modules, plugins, roles.
17. Collection metadata file? **A:** `galaxy.yml`.
18. How build a collection? **A:** `ansible-galaxy collection build`.
19. Tool for collection tests? **A:** `ansible-test`.
20. Where does `requires_ansible` live? **A:** `meta/runtime.yml`.
21. What is FQCN? **A:** Namespace.collection.name reference.
22. Where keep inventories? **A:** Environment repo, not in roles.
23. Why not secrets in roles? **A:** Roles are shared/versioned code.
24. What makes roles check-mode friendly? **A:** Read-only probes with `check_mode: false`, guarded dependent tasks.
25. Why avoid reboots in roles by default? **A:** Surprise outages; let the caller decide.
26. How expose reboot-needed? **A:** Return a fact/variable.
27. How document a role? **A:** README plus argument specs (`ansible-doc -t role`).
28. What is `combine` used for in roles? **A:** Merge default and user dicts.
29. When promote a role to a collection? **A:** When multiple teams reuse it.
30. How reduce supply-chain risk? **A:** Pin, mirror, review and test upgrades.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Rene Moser and Lorin Hochstein, *Ansible: Up and Running*, 3rd edition (chapter 9 on roles for scalable playbooks, chapter 15 on collections and sharing content).
- Ansible documentation: roles, argument specs, collections development, `ansible-galaxy`, `ansible-test`.
- Examples are the author's constructions.

**Flagged for verification before publishing:** `ansible-galaxy` and `ansible-test` option syntax for your version, argument-spec feature support in your ansible-core, Automation Hub publishing steps, and every code listing; all labs are **untested**.
