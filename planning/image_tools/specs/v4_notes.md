# Vol 4 (part-04-automation) figure notes, chapters 01-06 (read-only planning pass)

## ch01 git-from-scratch (01-git-from-scratch-for-infrastructure-engineers.md)
Topic: object model (blob/tree/commit/tag), index and three areas, daily workflow, ignore rules, remotes, branching, merge vs rebase, --onto, conflicts and lock files, reflog and bisect, repo layout, hooks, secrets remediation, CODEOWNERS, LFS, GitOps push vs pull.
Mermaid: 4 blocks. L80 object-model flowchart (keep). L134 three-areas flow (keep). L324 gitGraph merge vs rebase shape (keep). L535 push vs pull GitOps flow (keep). None flagged for redraw.
SVG specs (v4_01.json): a01-secret-order (L-section 11), a01-onto (rebase --onto, section 7), a01-reflog-rescue (section 8). Anchors verified unique with grep -cxF.
Note: the --onto figure anchors to the section 7 heading, since no sub-heading sits next to the --onto paragraph.
Raster candidates: none.

## part-04-automation (ch 07-12)

- ch07 Variables, facts, templates, filters: 1 mermaid (flowchart, sources to engine to targets, line ~217). Do NOT redraw it. Figures: register vs set_fact flow, --limit hostvars failure, lookups on control node vs module on target, map extract pipeline. Gemini raster: none (SVG suffices).
## ch02 CI/CD pipelines (02-ci-cd-pipelines-concepts-and-design.md)
Topic: infra vs app CI/CD, principles, pipeline gates, PRs as control plane (Atlantis etc.), OIDC auth, reference GitHub Actions, policy as code (Rego), golden images, staged fleet rollouts, testing layers, drift detection, pipeline security.
Mermaid: 3 blocks. L112 gate flowchart (10 nodes, core map; keep). L338 golden image build chain (linear, keep). L358 canary/batch rollout with decision diamonds (keep). None flagged for redraw. Note: the golden-image and gate charts overlap in concept (ordered stages), but both stay as mermaid.
SVG specs (v4_02.json): a02-wisb-replace (Templatizer merge vs Junos replace, anchor = Foundations h3), a02-oidc-exchange (section 5), a02-drift-classes (section 11, exit codes 0/1/2 and auto-heal vs alert). Anchors verified unique.
Raster candidates: none.

## ch03 Ansible from zero (03-ansible-from-zero-...md)
Topic: what Ansible is (agentless push, declarative vs procedural, idempotency), execution steps, forks/strategy/facts/pipelining, install and versions, Vagrant lab, ansible.cfg and become, inventory preview, ad-hoc commands, command/shell/raw, first playbook and recap, connection troubleshooting table, security.
Mermaid: 1 block. L94 sequenceDiagram of the per-task execution steps (control node vs target). Keep as is; it is the only sequence view and it covers the execution steps, so no new figure duplicates it.
SVG specs (v4_03.json): a03-push-pull (section 1, push vs pull), a03-split-tools (Where it fits, Terraform/cloud-init/Ansible chain), a03-linear-wait (section 2, linear strategy timeline). Anchors verified unique.
Raster candidates: none.

- ch08 Handlers, conditionals, loops, blocks, error handling: 1 mermaid (flowchart TD, drain/change/validate/return with block rescue always, line ~106). Do NOT redraw it; block/rescue/always and the drain flow are already in it. Figures: handler lost after failure (Run 1 vs Run 2), import vs include (parse time vs run time), serial batch canary. Gemini raster: none.
## ch04 YAML and Jinja2 (04-yaml-and-jinja2-for-infrastructure-code.md)
Topic: YAML structures, rules that bite (indent, colons, quoting, type coercion), anchors and merge keys, JSON/YAML tooling, schemas, YANG and wire formats, Jinja2 delimiters/expressions/filters/tests/control/whitespace/macros, Jinja2 in Ansible, templating in other tools, testing, error table, security.
Mermaid: 1 block. L136 flow (data source + template -> engine -> rendered artifact -> validator). Keep. No redraw flagged.
SVG specs (v4_04.json): a04-yaml-coercion (Rules that bite, unquoted NO/1.10/010/0644 -> parsed types), a04-anchor-merge (Anchors section, defaults + merge key + override), a04-validate-install (section 3, render on control node, validate, install). Anchors verified unique.
Skipped on purpose: block scalar styles (| vs >), the Jinja loop example and the switchport example (covered by text and the mermaid flow); keeping the chapter at 3 figures.
Raster candidates: none.

- ch09 A real playbook end to end (FastAPI, nginx, PostgreSQL, release dirs): 1 mermaid (flowchart LR, target architecture: clients to nginx to app01/app02 to PostgreSQL, Prometheus, line ~47). Do NOT redraw it. Figures: site.yml import order, release directory and current symlink switch with rollback, verification path (HTTPS via nginx, version assert, direct per-node check). Not drawn on purpose: app play four stages (covered by prose and code), nginx request path (duplicates the mermaid). Gemini raster: none.
## ch05 Ansible inventory (05-ansible-inventory-hosts-groups-dynamic-inventory-and-variables.md)
Topic: INI and YAML formats, special groups and connection variables, host patterns, group_vars/host_vars layout, variable precedence, add_host/group_by, dynamic inventory plugins and scripts, source of truth, GPU cluster group axes, debugging table, common mistakes.
Mermaid: 1 block. L227 flowchart BT of the 7-level precedence stack. Keep (it is the only stack view). Note for later: a05-hash-replace uses the 'Variable precedence (summary)' heading, which is text about dictionary replacement, not the stack itself, so no duplication.
SVG specs (v4_05.json): a05-vagrant-collapse (127.0.0.1 collapse, Special groups heading), a05-pattern-venn (section 2, union/intersection/exclusion), a05-dynamic-flow (section 5, plugin config to inventory), a05-hash-replace (dictionary replace vs combine, precedence summary heading). Anchors verified unique.
Raster candidates: none.

- ch10 Debugging Ansible playbooks: 1 mermaid (flowchart TD, layered method: parse, UNREACHABLE, FAILED data/privilege/application, line ~47). Do NOT redraw it; it already is the layer decision tree. Figures: reproduce a module by hand (keep remote files, explode, execute), agent forwarding breaks under become (sudo drops SSH_AUTH_SOCK), debugger two edit paths (task.args + redo vs task_vars + update_task + redo), failure grouping pipeline (grep, sed, sort, uniq -c, sort -rn). Not drawn: verbosity ladder (table covers it). Gemini raster: none.
## ch06 Ansible playbooks (06-ansible-playbooks-tasks-modules-idempotency-and-check-mode.md)
Topic: playbook anatomy and play phases, webservers-tls walkthrough, task keywords, idempotency and guards, module families, command/shell/raw/script, check mode and diff, execution control (tags, serial, strategies, failure policy, exit codes), worked canary rollout, lab, mistakes.
Mermaid: 1 block. L95 play phase flowchart (pre_tasks -> flush -> roles/tasks -> flush -> post_tasks -> flush). Keep. No redraw.
SVG specs (v4_06.json): a06-serial-gate (section 6 batching, serial [1,10%,25%] + max_fail_percentage gate), a06-idempotent-runs (section 2, changed=0 on second run vs timestamp trap), a06-check-scope (section 5, declarative modules vs command/shell/raw under --check). Anchors verified unique.
Skipped on purpose: the Section 7 worked canary example (its pre-check/validate/halt sequence overlaps the serial figure and the mermaid phase chart).
Raster candidates: none.

- ch11 Roles and collections: 1 mermaid (flowchart TD, playbook to argument_specs to defaults to vars to tasks, plus collection dotted link, line ~85). Do NOT redraw it. Figures: six-path relative file search, roles/import_role/include_role run order in a play, GPU node role order (6 stages), collection init/build/install/test/publish. Not drawn: defaults vs vars (the mermaid and prose cover the precedence stack). Gemini raster: none.
## ch13 Testing Ansible (13-testing-ansible-ansible-lint-molecule-and-ci.md)
Topic: test pyramid, yamllint and ansible-lint configs, syntax/check/golden-file render tests, Molecule scenario files and test sequence, verifiers (Ansible-native, testinfra, Goss), multi-host and desired_state scenarios, driver limits table, GPU stub vs hardware tier, handler/upgrade tests, collection tests, CI workflow, checklist, troubleshooting table.
Mermaid: 1 block. L43 flowchart TB test pyramid (E/V/C/D/L tiers). Keep. Do NOT redraw it.
SVG specs (v4_13.json): a13-molecule-sequence (section 4 "The test sequence", create/prepare/converge/idempotence/side_effect/verify/destroy with failure meaning), a13-ci-job-graph (section 6 CI integration, lint needs-> molecule matrix, gpu-hw conditional). Anchors verified unique.
Skipped on purpose: driver limits table (already a table), GPU stub vs hardware split (duplicates the pyramid's top tiers), troubleshooting table (table), checkpoint Q&A.
Raster candidates: none.
- ch12 Ansible Vault and secrets management: 1 mermaid (flowchart LR, Git vault and SOPS to control node to target, external manager lookup, line ~251). Do NOT redraw it. Figures: vault_ indirection (plaintext pointers vs encrypted values), vault IDs isolate dev and prod, leak paths with matching controls, two-phase overlap rotation. Not drawn: incident response order (4-step list, prose is enough). Gemini raster: none.
## ch14 Ansible at scale (14-ansible-at-scale-performance-strategies-and-callbacks.md)
Topic: measure before tuning (timing callbacks, straggler arithmetic), forks, SSH multiplexing and pipelining, fact caching, loops and delegation costs, Mitogen, strategies (linear/free/host_pinned), failure containment list, async for long jobs, push vs pull architectures, pull mode rings, callbacks and a custom jsonl_audit plugin, cluster playbook skeleton, controller failure table, lab, checkpoints.
Mermaid: 1 block. L219 flowchart TB push-at-scale vs pull-at-scale subgraphs. Keep. Do NOT redraw it (push/pull is already there, so the rings figure is about promotion, not the architecture).
SVG specs (v4_14.json): a14-linear-vs-free (section 3, linear barrier vs free lanes), a14-async-background-job (### Long-running tasks, sequence of 5 messages across Controller, Rack host, Background job), a14-ring-promotion (section 6 pull mode, ring 0/1/2 canary to stable-1 to stable). Anchors verified unique.
Skipped on purpose: SSH multiplexing timing (numbers only, a table-like list), callback flow (plugin code is shown already), fact cache and failure-containment (lists), controller failure table.
Raster candidates: none.

## ch19 Terraform state in depth (19-terraform-state-in-depth-backends-locking-and-drift.md)
Topic: what state holds and why, local state limits, remote backends (S3, GCS, Azure, HCP cloud block, others), backend gotchas and bootstrap, locking, state layout and sharing data across states, workspaces, migration and moved/import/removed, state surgery, recovery table, drift, secrets in state, CI/CD state, lab, mistakes.
Mermaid: 1 block, L88 flowchart LR of the lock, read/verify, mutate, write-and-release sequence. Keep. Do NOT redraw it (it is the locking flow; the lock text in section 4 is prose).
SVG specs (v4_19.json): a19-move-resource-states (section 7, four-step import/apply/removed/delete across State A and B), a19-drift-decision (section 9, revert/adopt/tolerate decision).
Skipped on purpose: backend blocks (code), layout tree (text tree already), sharing-data table (table), recovery table (table), workspace paths (prose).
Anchors verified unique.
Raster candidates: none.
## ch15 Custom modules, plugins and AAP (15-custom-modules-plug-ins-and-ansible-automation-platform.md)
Topic: choosing the extension point (table), writing a module (AnsibleModule, check/diff, idempotency), gpu_power_limit example, when not to write a module, plugin types (filter, lookup, inventory, action, connection), execution environments with ansible-builder, AAP/AWX objects table, AAP operation and RBAC, API launch, awx.awx YAML, CALMS, EDA rulebook, where-to-run table, lab, checkpoints.
Mermaid: 1 block. L364 flowchart LR AAP architecture (controller, PostgreSQL, mesh, execution nodes, hub, EDA). Keep. Do NOT redraw it.
SVG specs (v4_15.json): a15-module-idempotency-loop (section 2, read/compute/change/report plus thermostat analogy), a15-module-test-ladder (### Testing a module, 5 steps), a15-eda-remediation-flow (### Event-Driven Ansible (EDA), alert to rule to job template to node).
Skipped on purpose: extension-point table, core objects table, where-to-run table, EE build steps (commands), API curl commands, CALMS list.
Raster candidates: none.

## ch20 Terraform modules (20-terraform-modules-and-reusable-infrastructure.md)
Topic: what a module is (root vs child, inputs/outputs), wiring example, module file layout, interface design (validation, precondition, small outputs, provider-free modules, secure defaults, stable names, path.module, inline vs separate SG rules, locals), composition patterns (thin roots, dependency inversion, facades, data-driven for_each), multi-region providers, source table, versioning and upgrades, test pyramid, worked checkpoint bucket, anti-patterns, ecosystem, lab.
Mermaid: 1 block, L49 flowchart TB of root module wiring child modules (network, storage, cluster, gpu_pool). Keep. Do NOT redraw it.
SVG specs (v4_20.json): a20-validation-flow (section 2, gpu_count list check and error message), a20-promote-pin (section 4, changelog/plan/promote/stop steps across dev, staging, prod), a20-provider-alias (section 3, two aliased providers passed to two module calls).
Skipped on purpose: source-type table, test pyramid table (table already), file tree (text), checkpoint bucket code, count-vs-for_each (only in checkpoint answers, not main body), anti-pattern list.
Anchors verified unique.
Raster candidates: none.
## ch16 Containers, cloud and network devices (16-ansible-for-containers-cloud-and-network-devices.md)
Topic: Docker/Podman modules and GPU container, Kubernetes via kubernetes.core and GitOps boundary, cloud provisioning (Terraform vs Ansible split, GCP VM example, cost safety), AWS AMI/VPC idempotence keys, WinRM, network device connection types, five-pattern safe change, NVUE, Nornir vs Ansible, security/compliance, layer table, lab, checkpoints.
Mermaid: 1 block. L457 flowchart LR data model -> templates -> dry run -> apply with commit-confirm -> verify -> rollback or next batch. Keep. Do NOT redraw it (the safe-change pipeline is exactly this concept; the commit-confirm net is not separately drawn).
SVG specs (v4_16.json): a16-network-connection (### How network automation differs, controller to device through network_cli/netconf/httpapi), a16-cluster-boundary (### Kubernetes, GitOps above the cluster boundary vs Ansible below it).
Skipped on purpose: resource-module state list and *_command/*_config/resource comparison (bullet/checkpoint content, and both read better as text), layer table (table), Docker module table, AWS VPC idempotence keys (list), Terraform-vs-Ansible split (covered by the layer table).
Raster candidates: none.

## ch21 Terraform loops, conditionals, lifecycle (21-terraform-loops-conditionals-lifecycle-and-gotchas.md)
Topic: count and index shifting, for_each keys, for expressions and splats, string directives, dynamic blocks, conditionals and the if/else [0] trap, lifecycle arguments and settings table, zero-downtime patterns, gotchas table, worked team/namespace quota example, lab.
Mermaid: 1 block, L170 flowchart TD choosing count vs for_each vs dynamic vs for expression vs string directive. Keep. Do NOT redraw it (it is the construct decision tree; the count/for_each figure shows the removal mechanism, not the choice).
SVG specs (v4_21.json): a21-count-vs-foreach (section 2, middle-item removal under count vs for_each), a21-lifecycle-order (section 6, precondition, create_before_destroy, destroy old, postcondition), a21-if-else-index-trap (section 5, opposite counts, [0] error, one(concat) fix).
Skipped on purpose: string directive example (code), dynamic block (code plus prose on EFA), gotchas table (table), rolling patterns list (list, no flow), lifecycle settings table (table).
Anchors verified unique.
Raster candidates: none.
## ch17 Ansible for GPU nodes and clusters (17-ansible-for-gpu-nodes-and-clusters.md)
Topic: bring-up dependency graph and five ordering rules, project layout, gpu_bringup.yml role order, role details (gpu_facts, base_os/kernel tuning, mofed with async and reboot handler, nvidia_driver, fabric_manager, GPU tuning/MIG table, dcgm, container toolkit, scheduler agents), reboot vs reload, validation stage table, burn-in and NCCL test, day-2 drain/patch/resume, fleet health sweep, incidents, lab, checkpoints.
Mermaid: 1 block. L45 flowchart TB bring-up dependency graph (firmware to scheduler, reboot markers). Keep. Do NOT redraw it; it is the bring-up order itself.
SVG specs (v4_17.json): a17-reload-or-reboot (## 4, stop services, unload top-down, modprobe, holder check, reboot fallback), a17-drain-patch-resume (## 6, drain, wait for jobs, apply, validate, resume or stay drained, serial canary band).
Skipped on purpose: validation stage table (a table, and it duplicates the bring-up order), GPU tuning settings table, incident list, project tree (text tree), OFED install and nvidia_driver code (code, not a figure).
Raster candidates: none.

## ch22 Terraform secrets and multiple providers (22-terraform-secrets-and-multiple-providers.md)
Topic: where secrets leak, seven strategies best to worst, TUTD secret taxonomy and universal state problem, examples (managed master password, secret container, ephemeral), generated credentials and rotation, provider authentication (OIDC/WIF, table, assume_role and impersonation), provider aliases and multi-region/account/cloud patterns, Kubernetes layering, dependency ordering, lock file/mirrors/custom providers, secure pipeline sketch, lab, mistakes.
Mermaid: 2 blocks. L47 flowchart LR of secret leak paths (variables, generators, data sources, plan files, backups, remote_state readers, shell history, outputs, TF_LOG). L355 flowchart LR of PR to plan (OIDC read-only) to policy checks to approval gate to apply to secret manager and encrypted state. Keep both. Do NOT redraw either. The strategy ladder and federation figure cover prose, not these flows.
SVG specs (v4_22.json): a22-strategy-ladder (section 2, seven strategies best to worst), a22-federated-auth (section 3, CI job to signed token to trust check to temporary role credential), a22-layered-k8s (section 4 dependency ordering, stack 1 cluster and stack 2 data sources plus kubernetes/helm/add-ons).
Skipped on purpose: alias and module-passing code (covered by ch20 provider-alias figure, avoid repeat), auth table (table), lock file and mirror config (code and prose), taxonomy list (list), Rego policy (code).
Anchors verified unique.
Raster candidates: none.
## ch18 Terraform refresher (18-terraform-refresher-why-providers-resources-and-the-workflow.md)
Topic: declarative vs imperative, idempotence and drift, saved plans, replacement, IaC categories and six axes, architecture (core, providers, state, backends, registry, OpenTofu), HCL essentials (terraform block, variables/locals/outputs, resources and data sources, dynamic blocks, provisioners), workflow and CLI reference with plan symbols, drift/import/refactoring (import blocks, moved/removed), state commands, providers and auth, workspaces vs directories, OSS vs HCP vs OpenTofu table, local end-to-end example, lab, checkpoints.
Mermaid: 3 blocks. L49 flowchart LR declarative loop (configuration, state, real world -> plan -> apply). L102 flowchart TB architecture (CLI core, provider plugins, backend, registry, lock file). L299 flowchart LR workflow loop (init, fmt, validate, plan, review, apply, output). All three keep; do NOT redraw any of them.
SVG specs (v4_18.json): a18-plan-symbols (## 4 plan symbol legend: +, ~, -, -/+, +/-, <=; summary line), a18-moved-block (### Refactoring safely: moved block vs destroy and create), a18-terraform-ansible-handoff (## 9 end-to-end example: random_pet and var.nodes into local_file, rendered inventory.ini handed to Ansible). Anchors verified unique.
Skipped on purpose: create_before_destroy ordering (the Brikman ASG walkthrough sits under the Resources heading with no nearer subheading, so an anchor there would misplace it; the text is clear as prose), workspace and OSS-vs-HCP content (a table already), provider auth, CLI command block (code block), IaC category list (list).
Raster candidates: none.

## ch23 Production-grade Terraform (23-production-grade-terraform-structure-testing-and-team-workflows.md)
Topic: repository layout (live vs modules), orchestration tools table, Terragrunt DRY, production-readiness checklist, testing strategy and pyramid, Terratest stages and dependency injection, team workflow and promotion, guardrails (cost, security, data, networking, tagging, blast radius), operating the estate, GPU capacity management, lab, mistakes.
Mermaid: 2 blocks. L176 flowchart TB test pyramid (static, policy, unit, integration, production canary). Keep. L241 sequenceDiagram of the change lifecycle (Dev, Git PR, CI, reviewers, environment). Keep. Do NOT redraw either.
SVG specs (v4_23.json): a23-live-vs-modules (section 1, modules/ vs live/ stacks with pinned versions), a23-terragrunt-dry (section 1, root remote_state, include find_in_parent_folders, dependency, run-all order), a23-test-stages (section 3, deploy_db through teardown_db with SKIP flags).
Skipped on purpose: orchestration tools table (table), production-readiness checklist (checkbox list), promotion code (overlaps the ch20 promote figure), guardrail Rego (code), GPU capacity bullets (list), checkpoint Q&A.
Anchors verified unique.
Raster candidates: none.

## ch24 Terraform on GCP and Nebius (24-terraform-on-gcp-and-nebius-networks-gpu-vms-and-gke.md)
Topic: GCP landing zone decisions, network (VPC, subnet, NAT, firewall, PGA, IAP, MTU), multi-NIC GPU VPCs, GPU VM families and capacity models, compact placement, GKE cluster and GPU node pools (upgrade settings, reservations, taints), Workload Identity, KMS/CMEK bucket, budgets, Cluster Toolkit, Nebius resource model table and fabric code, verification after apply, lab, mistakes, interview angles.
Mermaid: 1 block, L44 flowchart TB of landing zone (org, projects, VPC, GKE, VMs, buckets, IAM, Artifact Registry, monitoring). Keep. Do NOT redraw it (it is the high-level map; the new figures show the NAT/IAP egress, multi-NIC, surge and fabric mechanisms).
SVG specs (v4_24.json): a24-private-egress (section 2, PGA + Cloud NAT + IAP, no public IP), a24-multi-nic (section 2, primary NIC to management VPC, one extra VPC per GPU NIC, mtu 8896), a24-surge-upgrade (section 4, default surge vs max_surge 0 with max_unavailable 1 on a 16-node reservation), a24-nebius-fabric (section 7, gpu cluster fabric created first, instances refer to its ID).
Anchor note: a24-private-egress and a24-multi-nic both anchor to "## 2. Network" (the two paragraphs follow the same code block); place private-egress first, then multi-NIC.
Skipped on purpose: landing-zone decisions (prose), VM code, GKE code, KMS/bucket code, budget code, Nebius comparison table (table), verification list (list), CheckPoint Q&A.
Anchors verified unique.
Raster candidates: none.

## ch25 Terraform with Kubernetes and Helm providers, and OpenTofu (25-terraform-with-kubernetes-and-helm-providers-opentofu.md)
Topic: five-layer lifecycle and ownership, provider auth (GKE token, cluster CA, exec plugins, layering rule), resource types table, helm_release habits and GPU platform install order, CRD plan-time schema problem (four options), tenancy as code (teams map, locals flatten, namespace/quota/rolebinding/netpol), GitOps bootstrap (helm_release argocd, root Application), operational pitfalls, OpenTofu notes, lab, mistakes, interview angles.
Mermaid: 1 block. L44 flowchart TB five-layer foundation to workloads. Keep. Do NOT redraw it; the spec figures cover layering across states, the team fan-out and the GitOps handoff, not the layer stack.
SVG specs (v4_25.json): a25-two-stack-layering (### Layering rule (repeat from 4.22), avoid one state vs two states with data sources), a25-team-fanout (## 5. Tenancy and policy as code, ml -> ml-dev and ml-prod -> one copy per resource), a25-gitops-handoff (## 6. GitOps bootstrap, Terraform installs Argo CD and root app, Git and automated sync take over).
Skipped on purpose: resource types table (table), CRD four-option list and kubectl_manifest snippet (list and code), helm_release and kubernetes provider code blocks (code), GPU install order (ordered prose list, overlaps the ch26 wave mermaid), OpenTofu feature list and governance (prose and lists), exercises and checkpoints.
Anchors verified unique (grep -cxF = 1).
Raster candidates: none.

## ch26 GitOps with Argo CD and Flux (26-gitops-with-argo-cd-and-flux.md)
Topic: OpenGitOps principles and pull vs push, two-repo pattern, feature gates, secrets, drift alerts, Argo CD components and objects, Application and ApplicationSet YAML, sync vs health status, sync policy, sync waves and hooks, CLI, Flux toolkit and three objects, Argo vs Flux table, repo design and layout, versioning (tags, directories), stages HEAD to release, Helm parameterization, GPU bootstrap waves, Flagger and progressive delivery, troubleshooting table, DR and security, lab, mistakes, interview angles.
Mermaid: 2 blocks. L48 flowchart LR GitOps loop (engineer, CI, config repo, controller, API). Keep. L488 flowchart TB six-wave GPU bootstrap order. Keep. Do NOT redraw either: the wave chart is the bootstrap order itself, and the loop shows the reconcile flow.
SVG specs (v4_26.json): a26-argo-status (### Architecture and objects, Synced+Degraded vs OutOfSync+Healthy cards; placement is just after that heading, i.e. before the Application YAML, so the figure sits above the code), a26-flux-chain (### Argo CD vs Flux, GitRepository to Kustomization (dependsOn) to HelmRelease), a26-repo-layout (## 4. Repository design, clusters/prod-us to infrastructure and apps overlays/prod).
Skipped on purpose: Argo component list (list), Argo vs Flux table (table), Stages HEAD-to-release ladder and symlink layout (prose list plus text tree; considered but dropped to keep 3 figures), versioning branch/dir layouts (text trees and prose), canary/blue-green/A-B comparison (prose already short), troubleshooting table, checkpoint and YAML code blocks.
Anchors verified unique.
Raster candidates: none.

## ch27 Lab: provision a GPU cluster with Terraform and Ansible (27-lab-provision-a-gpu-cluster-with-terraform-and-ansible.md)
Topic: lab purpose and two paths (Docker rehearsal vs cloud), learning outcomes, repo skeleton and gitignore, node model variables, nodes_docker module (deterministic IPs and ports), live root and generated inventory, Path B summary, Ansible project settings and group vars, five roles (base_os, gpu_stub, monitoring, munge_slurm, node_validate), stub nvidia-smi template, site.yml four plays with serial gate, run/idempotency commands, verify.yml checks, CI pipeline, day-2 exercises, teardown checks, deliverables, mistakes, interview angles.
Mermaid: 1 block. L53 flowchart LR architecture (Git repo subgraph with terraform, ansible, ci; infrastructure; generated inventory; nodes; validation; nightly drift job). Keep. Do NOT redraw it; the spec figures cover site.yml play order, the Path A/Path B contract and the pipeline stages, which the diagram only names.
SVG specs (v4_27.json): a27-play-order (### 2.3 Site playbook with ordering and safety, four plays with canary gate), a27-path-contract (### Path B: cloud variant (summary), var.nodes into two modules, one output, one inventory, one playbook), a27-pipeline-stages (## Part 4: Pipeline, static then plan-and-test then destroy always).
Skipped on purpose: node model and Docker module code (code), locals IP/port worked example (prose and code), inventory children expression (code), five-role list (a list of roles, covered by prose), stub template (code), verify.yml checks (bullet list), Day-2 exercises and teardown commands (lists and commands), deliverables checklist, checkpoints.
Note: dcgm-exporter 4.9.0 callout is a tip box, not a figure.
Anchors verified unique (grep -cxF = 1).
Raster candidates: none.
