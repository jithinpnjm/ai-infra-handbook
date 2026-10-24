---
id: "c04-27"
title: "4.27 Lab: provision a GPU cluster with Terraform and Ansible"
sidebar_label: "4.27 Lab: provision a GPU cluster with Terraform and Ansible"
sidebar_position: 27
description: "End-to-end lab: Terraform creates a network, storage and a small Slurm-style GPU cluster (with a zero-cost local rehearsal path), exports an Ansible inventory, Ansible configures drivers/monitoring/Slurm and validates the nodes, with pipeline, drift, upgrade and teardown exercises"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 4.27 Lab: provision a GPU cluster with Terraform and Ansible

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Path A: Docker or Multipass, Terraform/OpenTofu, ansible-core. Path B: cloud sandbox, optionally one GPU VM |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** (all steps below are unexecuted) |

## Purpose

This lab ties Part 4 together by building one small but realistic platform: **Terraform creates infrastructure** (network, storage, nodes, outputs); **Ansible configures it** (base OS, GPU stack, monitoring, a small Slurm cluster); **validation proves it works**; **a pipeline** runs the same flow repeatably; **drift and upgrade exercises** show Day-2 behaviour; **teardown** returns everything to zero. Everything uses the patterns from earlier chapters: Git workflow (4.1), pipeline design (4.2), Ansible roles/variables/handlers/testing (4.3 to 4.17), Terraform modules/state/loops/secrets/team workflow (4.18 to 4.25).

The lab has two paths so you can learn without spending money:

- **Path A: local rehearsal (default).** Terraform's Docker provider (or Multipass via `local-exec`/a community provider) creates "nodes" as systemd-enabled containers or VMs on your machine. No GPUs: GPU-specific tasks run against stub `nvidia-smi`/`dcgmi` scripts. Everything else (inventory export, roles, Slurm, validation, CI, drift) is real.
- **Path B: cloud.** The same Terraform root, with a cloud module instead of the Docker module, creates VPC, firewall, bucket and VMs in a sandbox project (use small CPU VMs, optionally one L4/A100 VM if you have quota and a budget cap). The Ansible side is unchanged except for the driver role running for real.

> **Warning.** Cloud GPU resources cost money by the hour. Set a budget and alert first (4.24), prefer Spot, apply only when ready to test, and destroy at the end. Never run this in a production project.

## Learning outcomes

After the lab you can:

1. Structure a repo with `modules/`, `live/`, `ansible/`, `ci/` and explain how Terraform outputs feed Ansible.
2. Provision nodes and a network with Terraform using `for_each`, modules, variables with validation, outputs, remote or local state, and a generated inventory.
3. Configure the nodes with Ansible roles in the correct order with idempotent tasks, handlers, `serial`, validation and `no_log`.
4. Run an automated end-to-end pipeline (lint, plan, apply, configure, verify) and a nightly drift check.
5. Perform a safe change (add a node, upgrade a package/driver stub) and a rollback.
6. Tear down completely and verify nothing is left.

## Architecture

```mermaid
flowchart LR
  subgraph Git["Git repo"]
    TF["terraform/ (modules + live/lab)"]
    AN["ansible/ (roles, playbooks, inventory plugin)"]
    CI["ci/ (pipeline)"]
  end
  TF -->|plan/apply| INF["Infrastructure\nnetwork + storage + nodes\n(Docker or cloud)"]
  INF -->|terraform output -json| INV["inventory.yml (generated)"]
  INV --> AN
  AN -->|"ssh"| N["Nodes: login01, ctl01, gpu01-gpu03"]
  N --> V["Validation: nvidia-smi (stub), DCGM, Slurm sinfo, NCCL stub"]
  CI --> TF
  CI --> AN
  DRIFT["Nightly drift job\nterraform plan -detailed-exitcode\nansible --check --diff"] --> INF
  DRIFT --> N
```

Nodes: `login01` (bastion/login), `ctl01` (Slurm controller + monitoring), `gpu01` to `gpu03` (workers). Path B adds a bucket for shared data and a service account.

## Part 0: Prerequisites and repository skeleton

Tools: Git, Terraform or OpenTofu 1.6+, Ansible-core 2.16+, `ansible-lint`, `yamllint`, `pre-commit`, Docker (Path A), optionally Multipass; for Path B `gcloud` authenticated with a sandbox project.

```bash
mkdir gpu-lab && cd gpu-lab && git init -b main
mkdir -p terraform/modules/{network,nodes_docker,nodes_gcp} terraform/live/lab ansible/{inventories/lab,playbooks,roles,collections} ci
cat > .gitignore <<'EOF'
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
*tfplan*
crash.log
*.tfvars
!*.tfvars.example
.vault_pass*
ansible/inventories/lab/generated/
*.retry
.venv/
EOF
python3 -m venv .venv && . .venv/bin/activate
pip install ansible-core ansible-lint yamllint pre-commit
ansible-galaxy collection install ansible.posix community.general community.docker
```

Add a `.pre-commit-config.yaml` (4.1: terraform fmt/validate, yamllint, ansible-lint, gitleaks) and commit. Branch for the work: `git switch -c lab/initial-cluster`.

## Part 1: Terraform: nodes and network (Path A: Docker)

### 1.1 Variables and the node model

```hcl
# terraform/live/lab/variables.tf
variable "cluster_name" {
  type    = string
  default = "gpulab"
}

variable "nodes" {
  description = "Node definitions keyed by hostname"
  type = map(object({
    role = string                       # login | controller | gpu
    gpus = optional(number, 0)
  }))
  default = {
    login01 = { role = "login" }
    ctl01   = { role = "controller" }
    gpu01   = { role = "gpu", gpus = 8 }
    gpu02   = { role = "gpu", gpus = 8 }
    gpu03   = { role = "gpu", gpus = 4 }
  }
  validation {
    condition     = alltrue([for n in values(var.nodes) : contains(["login", "controller", "gpu"], n.role)])
    error_message = "role must be login, controller or gpu."
  }
}

variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/id_ed25519.pub"
}
```

### 1.2 The Docker node module (systemd + sshd containers)

```hcl
# terraform/modules/nodes_docker/main.tf
terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
    local  = { source = "hashicorp/local", version = "~> 2.5" }
  }
}

variable "cluster_name" { type = string }
variable "nodes" {
  type = map(object({ role = string, gpus = optional(number, 0) }))
}
variable "ssh_public_key" { type = string }

resource "docker_network" "cluster" {
  name = "${var.cluster_name}-net"
  ipam_config { subnet = "172.28.0.0/24" }
}

resource "docker_image" "node" {
  name = "${var.cluster_name}-node:latest"
  build {
    context = "${path.module}/image"        # Dockerfile: ubuntu + systemd + openssh-server + python3 + sudo (provide yourself)
    build_args = { SSH_PUBLIC_KEY = var.ssh_public_key }
  }
  triggers = { dir_sha = sha1(join("", [for f in fileset("${path.module}/image", "**") : filesha1("${path.module}/image/${f}")])) }
}

locals {
  ordered = sort(keys(var.nodes))
  ips     = { for i, n in local.ordered : n => cidrhost("172.28.0.0/24", 10 + i) }
  ports   = { for i, n in local.ordered : n => 2200 + i }              # published SSH ports on the host
}

resource "docker_container" "node" {
  for_each   = var.nodes
  name       = each.key
  hostname   = each.key
  image      = docker_image.node.image_id
  privileged = false
  tmpfs      = { "/run" = "", "/run/lock" = "", "/tmp" = "" }
  volumes {
    host_path      = "/sys/fs/cgroup"
    container_path = "/sys/fs/cgroup"
    read_only      = false
  }
  cgroupns_mode = "host"
  networks_advanced {
    name         = docker_network.cluster.name
    ipv4_address = local.ips[each.key]
  }
  ports {
    internal = 22
    external = local.ports[each.key]
  }
  labels {
    label = "role"
    value = each.value.role
  }
  labels {
    label = "gpus"
    value = tostring(each.value.gpus)
  }
}

output "nodes" {
  value = {
    for n, c in var.nodes : n => {
      role     = c.role
      gpus     = c.gpus
      address  = local.ips[n]
      ssh_host = "127.0.0.1"
      ssh_port = local.ports[n]
    }
  }
}
```

Notes: running systemd in containers needs cgroup settings that vary by host OS (Docker Desktop on macOS uses a Linux VM with cgroup v2). If this is troublesome, use Multipass VMs created by a `terraform_data`/`local-exec` wrapper or a community Multipass provider, or use Vagrant; the Terraform interface (a map of nodes with addresses/ports) stays the same, which is the point.

### 1.3 Live root and generated inventory

```hcl
# terraform/live/lab/main.tf
terraform {
  required_version = ">= 1.6"
  required_providers {
    local = { source = "hashicorp/local", version = "~> 2.5" }
  }
}

module "nodes" {
  source         = "../../modules/nodes_docker"
  cluster_name   = var.cluster_name
  nodes          = var.nodes
  ssh_public_key = trimspace(file(pathexpand(var.ssh_public_key_path)))
}

resource "local_file" "inventory" {
  filename        = "${path.module}/../../../ansible/inventories/lab/generated/hosts.yml"
  file_permission = "0644"
  content = yamlencode({
    all = {
      vars = {
        ansible_user                 = "automation"
        ansible_python_interpreter   = "/usr/bin/python3"
        ansible_ssh_common_args      = "-o StrictHostKeyChecking=accept-new"
        cluster_name                 = var.cluster_name
      }
      children = {
        for role in distinct([for n in values(module.nodes.nodes) : n.role]) :
        role => {
          hosts = {
            for name, n in module.nodes.nodes : name => {
              ansible_host = n.ssh_host
              ansible_port = n.ssh_port
              node_ip      = n.address
              gpu_count    = n.gpus
            } if n.role == role
          }
        }
      }
    }
  })
}

output "inventory_path" { value = local_file.inventory.filename }
output "nodes"          { value = module.nodes.nodes }
```

Run:

```bash
cd terraform/live/lab
terraform init
terraform fmt -check -recursive ../..
terraform validate
terraform plan -out=tfplan
terraform show tfplan | less          # read it: five containers, one network, one image, one file
terraform apply tfplan
terraform output -json nodes | jq .
cat ../../../ansible/inventories/lab/generated/hosts.yml
terraform plan                          # expect "No changes"
```

If the inventory file is gitignored (as in the skeleton), CI regenerates it each run, which is the point: Terraform is the source of truth for existence and addresses; Ansible's `group_vars` are the source of truth for configuration.

### Path B: cloud variant (summary)

Replace `nodes_docker` with `nodes_gcp` (a module taking the same `nodes` map): VPC + subnet + Cloud NAT + IAP firewall (4.24), a service account without keys, a versioned bucket with `prevent_destroy`, instances from an Ubuntu image with `enable-oslogin`, `machine_type` derived from role/GPU count (for example `e2-standard-4` for login/controller, `g2-standard-8` or `a2-highgpu-1g` for a single GPU worker), labels for cost allocation, `lifecycle.ignore_changes` on metadata keys, and outputs with the same shape (`address`, `ssh_host` = instance private IP via IAP or an external bastion, `ssh_port` = 22). The live root calls the cloud module instead; the Ansible side stays identical. Configure the remote state backend (4.19) with a versioned bucket.

## Part 2: Ansible: configure the cluster

### 2.1 Project settings

```ini
# ansible/ansible.cfg
[defaults]
inventory            = inventories/lab/generated/hosts.yml
roles_path           = roles
collections_path     = collections
forks                = 20
host_key_checking    = False        ; lab only: containers are rebuilt often; keep True in production (4.3)
interpreter_python   = auto_silent
stdout_callback      = yaml
callbacks_enabled    = timer, profile_tasks
retry_files_enabled  = False
[ssh_connection]
pipelining           = True
ssh_args             = -o ControlMaster=auto -o ControlPersist=60s
```

Group variables (excerpt):

```yaml
# ansible/inventories/lab/group_vars/all.yml
cluster_domain: lab.local
chrony_servers: [pool.ntp.org]
nccl_env: { debug: WARN, socket_ifname: eth0 }
slurm_cluster_name: "{{ cluster_name }}"
munge_key_b64: "{{ vault_munge_key_b64 }}"          # vault.yml (encrypted): ansible-vault create ... (4.12)

# group_vars/gpu.yml
nvidia_driver_branch: "550"
expected_gpus_default: 8
gpu_tools_stub: true            # Path A: install stub nvidia-smi/dcgmi; Path B: false (real driver)
```

### 2.2 Roles (compact versions)

Create roles with `ansible-galaxy role init` and implement the minimum: each has `defaults`, `tasks`, `handlers`, `meta/argument_specs.yml`, `README.md`.

1. **`base_os`**: packages (`chrony`, `rsync`, `curl`, `jq`, `htop`), users/groups (`slurm`, `munge`, `automation` sudoers drop-in with `validate: visudo -cf %s`), `/etc/hosts` from inventory (`hostvars` loop, 4.7), sysctl via `ansible.posix.sysctl`, time sync. Idempotent; handler restarts chrony.
2. **`gpu_stub`** (Path A) or **`nvidia_driver`** (Path B, see 4.17): installs stub scripts `/usr/local/bin/nvidia-smi` and `dcgmi` that emit plausible output based on `gpu_count` (Jinja template), including `-L` and `--query-gpu` CSV forms, so later roles and validations run unchanged.

```jinja
{# roles/gpu_stub/templates/nvidia-smi.j2 #}
#!/bin/bash
# {{ ansible_managed }}  (stub for lab; replaced by the real binary on GPU hosts)
case "$1" in
  -L) {% for i in range(gpu_count | int) %}echo "GPU {{ i }}: NVIDIA H100 80GB HBM3 (UUID: GPU-stub-{{ inventory_hostname }}-{{ i }})"; {% endfor %}
      ;;
  --query-gpu*) {% for i in range(gpu_count | int) %}echo "{{ i }}, NVIDIA H100 80GB HBM3, 550.90.07, 35, 0"; {% endfor %}
      ;;
  *) echo "stub nvidia-smi: unsupported arguments: $*" >&2; exit 1 ;;
esac
```

3. **`monitoring`**: `node_exporter` (package or binary with checksum) as a systemd unit; on `ctl01` Prometheus with a `file_sd` target file rendered from `groups['all']` (template in 4.7); DCGM exporter stub on GPU nodes (a tiny Python HTTP server exposing fake `DCGM_FI_DEV_GPU_UTIL` metrics) or the real exporter on Path B.
4. **`munge_slurm`**: munge key (vaulted) at mode 0400 owned by `munge`; `slurm.conf` and `gres.conf` templates from inventory (4.7 Slurm node template using `gpu_count`), `slurmctld` on `ctl01`, `slurmd` on GPU nodes (package installs from distro repos work for a lab; production builds Slurm from source/packages per Part 6). In containers, `slurmd` may need `-D` flags or cgroup settings; if it fights you, run Slurm in a single VM or use the lab's mock scheduler script and focus on the Ansible flow.
5. **`node_validate`**: tasks files `quick.yml` (inventory sanity), `standard.yml` (stub DCGM level-1 equivalent), asserting GPU count equals `gpu_count`, services active, ports open; writes a JSON report to the control node.

### 2.3 Site playbook with ordering and safety

```yaml
# ansible/playbooks/site.yml
- name: Base for every node
  hosts: all
  become: true
  roles: [base_os]

- name: GPU nodes
  hosts: gpu
  become: true
  serial: "{{ gpu_serial | default(['34%', '100%']) }}"      # first batch ~1 node of 3: canary
  max_fail_percentage: 0
  pre_tasks:
    - ansible.builtin.assert:
        that: [ gpu_count is defined, gpu_count | int > 0 ]
        fail_msg: "gpu_count missing for {{ inventory_hostname }}"
  roles:
    - { role: gpu_stub, when: gpu_tools_stub | default(true) }
    - { role: nvidia_driver, when: not (gpu_tools_stub | default(true)) }
    - node_validate

- name: Controller services
  hosts: controller
  become: true
  roles: [monitoring, munge_slurm]

- name: Workers join the scheduler
  hosts: gpu
  become: true
  roles: [munge_slurm]
  post_tasks:
    - ansible.builtin.import_role: { name: node_validate, tasks_from: standard }
```

### 2.4 Run it

```bash
cd ansible
ansible-lint && yamllint .
ansible all -m ansible.builtin.ping
ansible-playbook playbooks/site.yml --syntax-check
ansible-playbook playbooks/site.yml --check --diff --limit gpu01        # many tasks will report changes on first run; read the diff
ansible-playbook playbooks/site.yml                                      # full run
ansible-playbook playbooks/site.yml                                      # idempotency: expect changed=0 (except probes)
ansible gpu -m ansible.builtin.command -a "nvidia-smi -L" -o
ansible controller -m ansible.builtin.command -a "sinfo" -o              # if Slurm is running
```

Fix every spurious `changed` (4.6) until the second run is clean.

## Part 3: Verification

Write `playbooks/verify.yml` (read-only, safe anytime) that checks:

- Every host reachable; chrony synchronised (`chronyc tracking` offset below a threshold).
- GPU hosts: `nvidia-smi -L | wc -l == gpu_count`; exporter responds on 9400; `node_exporter` on 9100.
- Controller: Prometheus targets all `up` (query `http://ctl01:9090/api/v1/targets` via `uri`, assert); `sinfo` lists all GPU nodes `idle`; a test job (`srun -N3 hostname`) returns three distinct hostnames.
- NCCL-style test (stub or real): on Path B with GPUs run `nccl-tests`; on Path A run a stub that prints a plausible bus bandwidth, so the assertion logic is exercised.

Collect JSON reports into `reports/` and print a table summarising pass/fail per node. A failed node must make the playbook exit non-zero.

## Part 4: Pipeline

Create a pipeline that does the whole flow on a pull request and on a schedule (4.2). A GitHub Actions sketch (adapt for GitLab CI):

```yaml
# ci/lab-pipeline.yml  (copy to .github/workflows/)
name: gpu-lab
on:
  pull_request:
  schedule: [ { cron: "30 3 * * *" } ]            # nightly drift check
permissions: { contents: read }
concurrency: { group: lab-${{ github.ref }}, cancel-in-progress: false }

jobs:
  static:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: hashicorp/setup-terraform@v3
    - run: terraform fmt -check -recursive terraform/
    - run: cd terraform/live/lab && terraform init -backend=false && terraform validate
    - run: pip install ansible-core ansible-lint yamllint && yamllint . && ansible-lint ansible/
    - uses: gitleaks/gitleaks-action@v2

  plan-and-test:
    needs: static
    runs-on: ubuntu-latest            # Path A runs on the runner itself with Docker
    steps:
    - uses: actions/checkout@v4
    - uses: hashicorp/setup-terraform@v3
    - run: pip install ansible-core && ansible-galaxy collection install -r ansible/collections/requirements.yml
    - name: Apply ephemeral lab
      run: |
        cd terraform/live/lab
        terraform init -input=false
        terraform apply -input=false -auto-approve
    - name: Configure and verify
      run: |
        cd ansible
        ansible-playbook playbooks/site.yml
        ansible-playbook playbooks/site.yml | tee second.log && grep -E "changed=0" second.log     # idempotency gate
        ansible-playbook playbooks/verify.yml
    - name: Destroy (always)
      if: always()
      run: cd terraform/live/lab && terraform destroy -input=false -auto-approve
```

(The ephemeral lab applies and destroys on the runner, so no state needs to persist; for Path B use remote state, OIDC, plan/apply separation and approvals per 4.2/4.23.)

## Part 5: Day-2 exercises

1. **Add a node**: add `gpu04 = { role = "gpu", gpus = 8 }` to `var.nodes` via PR; read the plan (only one new container and inventory change; confirm existing nodes are untouched); apply; run Ansible limited with `--limit gpu04`, then full; verify Slurm picks it up.
2. **Remove a node safely**: drain `gpu03` in Slurm (`scontrol update ... State=DRAIN`), run a playbook that removes it from Slurm config and monitoring, then remove it from Terraform; confirm only that container is destroyed.
3. **Driver/package upgrade (stub)**: bump `nvidia_driver_branch` to `555` (the stub reports a new version); run with `serial: 1` and a failing validation on the canary (inject a mismatch) to observe the stop; fix and roll the remaining nodes.
4. **Configuration drift**: change `/etc/sysctl.d` or stop `chronyd` on `gpu02` manually; run `ansible-playbook site.yml --check --diff` and see the drift; apply to correct it; add the check as a scheduled CI job that fails when `changed>0`.
5. **Infrastructure drift**: `docker rm -f gpu02` out of band; `terraform plan` shows re-create; apply; re-run Ansible for that node; automate with the nightly job.
6. **Secret handling**: rotate the munge key (vault `rekey`, update, roll out in a controlled order: controller then workers, with service restarts through handlers); ensure `no_log` hides it and `--diff` doesn't print it.
7. **Failure injection**: kill SSH on one node mid-run; observe `unreachable`, `max_fail_percentage` behaviour and re-run with `--limit @failed.txt`; record exit codes.
8. **Rollback**: revert the upgrade commit in Git, push through the pipeline, confirm convergence to the previous state.
9. **Import**: create a new container manually, import it with an `import` block, align the code until the plan is clean (4.18).
10. **State**: migrate the Terraform state to a remote backend (MinIO/S3 or GCS) and show locking with two simultaneous plans (4.19).
11. **Cost/ownership labels** (Path B): add labels and a budget alert; verify they appear on resources; add a policy that fails a plan lacking `owner`/`ttl` labels (4.2).

## Part 6: Teardown and verification of cleanup

```bash
cd terraform/live/lab && terraform destroy
docker ps -a --filter "label=role"      # Path A: nothing left
docker network ls | grep gpulab
# Path B:
gcloud compute instances list --filter="labels.cluster=gpulab"
gcloud compute disks list --filter="labels.cluster=gpulab"
gcloud compute addresses list
gcloud storage buckets list --filter="name~gpulab"      # buckets with prevent_destroy need a deliberate override
```

Check billing the next day for stragglers (disks, IPs, snapshots, reserved capacity).

## Deliverables and review checklist

Submit/inspect:

- A Git repository with clear history of the lab changes (small PRs), CODEOWNERS and a README with quick start and teardown.
- `terraform plan`/`apply` outputs saved (redacted) and the generated inventory.
- Ansible roles passing `ansible-lint`, with `argument_specs`, and a second-run `changed=0` log.
- Verification report (JSON/table) showing all nodes pass.
- Pipeline definition and one green run plus one deliberately failed run (idempotency or validation failure) with explanations.
- A short postmortem note for the drift and failure-injection exercises: what happened, how detected, how fixed, how to prevent.

Self-review questions:

1. Where is the source of truth for node existence? For node configuration? How does information flow between them?
2. What prevents a typo from applying a change to all nodes at once?
3. What would you change to run this for 500 nodes across two regions? (Orchestration of stacks, forks/strategy, inventory from the cloud API, golden images, pull mode, 4.14, 4.23.)
4. Which parts are safe to rerun at 3 a.m., and which need approval?
5. How would you extend validation to cover InfiniBand links and NCCL bandwidth floors (4.17)?

## Common mistakes in this lab

- Running with `host_key_checking = False` and forgetting to turn it back on in real environments.
- Letting the generated inventory be edited by hand; or committing it.
- Applying Terraform and Ansible from different checkouts or versions; no pinned tool versions.
- Treating a green Ansible recap as validation; skipping the verify playbook.
- Forgetting teardown on Path B and paying for idle GPUs.
- Using real credentials or a production project.
- Hard-coding addresses instead of reading Terraform outputs.

## Interview angles

- "Walk me through provisioning and configuring a small GPU cluster from nothing, end to end, with IaC."
- "How do Terraform and Ansible hand off information? What are the alternatives (dynamic inventory plugins, tags, SSM)?"
- "How do you make the pipeline idempotent and safe to rerun?"
- "How would you detect and respond to drift on both layers?"
- "How do you test this without GPUs?"

## Sources and review notes

**Written in original words.** Principal sources:

- Yevgeniy Brikman, *Terraform: Up and Running* (end-to-end deployment patterns), and Rene Moser and Lorin Hochstein, *Ansible: Up and Running* (playbook, role and deployment patterns), as synthesised in chapters 4.1 to 4.26 of this handbook.
- The author's `nvidia-devops` repository, volume 10 (Ansible, Terraform and CI/CD chapters) for the node bring-up and validation concepts.
- Examples and the lab design are the author's constructions.

**Flagged for verification before publishing:** Docker provider arguments, the container image for systemd nodes, Slurm packaging and container behaviour, all cloud module details, CI syntax, and every command; this lab has **not been executed**. Replace this note with test results when it is.
