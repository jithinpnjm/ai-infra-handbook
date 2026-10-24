---
id: "c04-19"
title: "4.19 Terraform state in depth: backends, locking and drift"
sidebar_label: "4.19 Terraform state in depth: backends, locking and drift"
sidebar_position: 19
description: "How Terraform state works and fails: contents and risks, remote backends and locking (S3, GCS, Azure, HCP), state isolation and layout, migration, recovery, surgery, drift handling, secrets in state, and cross-stack data sharing"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 4.19 Terraform state in depth: backends, locking and drift

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Terraform/OpenTofu 1.6+; Docker with MinIO (S3-compatible) or a cloud sandbox bucket |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

State is the single most dangerous file in your platform. It maps names in code to real GPU clusters, buckets full of checkpoints and databases; it contains secrets in plaintext; if it is lost, Terraform forgets what it manages and tries to recreate it (duplicates, conflicts, outages); if it is corrupted or two people write it at once, resources can be orphaned or destroyed. In a team running training infrastructure across dev, staging and production, state design (where it lives, how it is locked, how it is split, who can read it) is a core architectural decision. This chapter covers state mechanics, remote backends, locking, layout strategies, migration, recovery and drift in practical depth.

## Prerequisites and outcomes

Needs 4.18. After this chapter you can:

- Explain what state contains, how plan/apply read and write it, and why it must be protected.
- Configure remote backends (S3, GCS, Azure Blob, HCP Terraform, PostgreSQL, Kubernetes) with encryption, versioning and locking, and bootstrap them safely.
- Choose a state layout (per environment, per layer/component, per team) that limits blast radius and plan time; share data across stacks safely.
- Migrate state between backends and workspaces; split and merge state with `moved`, `import`, `removed`, `state mv/rm`; recover from lost, corrupted or locked state.
- Detect and handle drift; manage secrets and sensitive values; encrypt state (OpenTofu) and restrict access.
- Operate state in CI/CD: locking, concurrency, least privilege.

## 1. What state is

State is a JSON document (`terraform.tfstate`) with a `version`, a `lineage` (unique id for this state's history), a `serial` (incremented on each write), the Terraform version, outputs, and a list of resources. Each resource instance records its address, provider, attributes (including values the provider computed such as IDs, IPs, ARNs), dependencies, and schema version.

```json
{
  "version": 4,
  "terraform_version": "1.8.5",
  "serial": 42,
  "lineage": "b2a4c5f0-....",
  "outputs": { "cluster_endpoint": { "value": "34.1.2.3", "type": "string" } },
  "resources": [
    { "mode": "managed", "type": "google_compute_instance", "name": "gpu",
      "provider": "provider[\"registry.terraform.io/hashicorp/google\"]",
      "instances": [ { "index_key": 0, "attributes": { "id": "projects/p/zones/z/instances/lab-gpu-0", "name": "lab-gpu-0", "...": "..." } } ] }
  ]
}
```

Why Terraform needs it:

1. **Mapping**: config address (`google_compute_instance.gpu[0]`) to the real ID. Without it Terraform cannot know the resource already exists (cloud APIs generally lack a "which resources did Terraform make" query).
2. **Metadata and dependency order**, particularly for destroys of resources no longer in config.
3. **Performance**: caching attributes so plan need not query every object (though it refreshes by default).
4. **Collaboration and sync**: a shared record plus locking.

Properties to remember: state is **not a backup of the infrastructure**, it is not authoritative about reality (the cloud is), and it contains **sensitive values in plaintext** (database passwords, private keys from `tls_private_key`, access keys created by Terraform, secrets read via data sources, even values marked `sensitive`). Anyone who can read state can often compromise the resources it describes.

## 2. Local state and its limits

By default state is `terraform.tfstate` in the working directory (plus a `.backup` file). Acceptable for experiments; unacceptable for teams: no locking (two applies corrupt it), no backup/versioning, secrets on laptops, no access control, easily lost or committed to Git. **Never commit state to Git** (`.gitignore`, 4.1). Remote state is the baseline for anything shared.

## 3. Remote backends

A **backend** configures (a) where state is stored and (b) whether operations run locally or remotely. Most backends store state and run operations on your machine/CI runner; HCP Terraform can also run them remotely.

### Amazon S3 (with locking)

```hcl
terraform {
  backend "s3" {
    bucket         = "acme-tfstate-prod"
    key            = "ai-platform/network/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/abcd-..."
    use_lockfile   = true                    # native S3 locking (newer Terraform/OpenTofu)
    # dynamodb_table = "acme-tfstate-lock"   # legacy locking via DynamoDB (deprecated in newer releases)
  }
}
```

Bucket hardening: versioning enabled (recover previous states), default encryption with KMS, block all public access, bucket policy limiting principals, access logging, lifecycle rules for noncurrent versions, MFA delete or object lock for production, cross-region replication for disaster recovery.

### Google Cloud Storage

```hcl
terraform {
  backend "gcs" {
    bucket = "acme-tfstate-prod"
    prefix = "ai-platform/network"           # state at <prefix>/default.tfstate (+ workspaces)
  }
}
```

GCS provides native locking and object versioning (enable it); use CMEK for encryption; grant `roles/storage.objectAdmin` on the bucket only to the CI service account and a break-glass group.

### Azure Blob Storage

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "acmetfstate"
    container_name       = "tfstate"
    key                  = "ai-platform/network.tfstate"
    use_oidc             = true                  # CI identity via workload federation
  }
}
```

Blob leases provide locking; enable soft delete and versioning and private endpoints.

### HCP Terraform / Terraform Enterprise (`cloud` block)

```hcl
terraform {
  cloud {
    organization = "acme"
    workspaces { name = "ai-platform-network-prod" }
  }
}
```

Managed state with locking, versions, access control, run history and optionally remote execution; sensitive variables stored in the platform.

### Others

`pg` (PostgreSQL; advisory locks), `kubernetes` (Secret in a cluster; size limits ~1 MiB), `consul`, `http` (custom), `oss`, `cos`, `local`. Pick one with native locking, durable storage, versioning, encryption and access control; avoid backends that cannot lock.

### Backend rules and gotchas

- **Backend blocks cannot use variables or references** (partial configuration instead): pass values via `-backend-config=key=value` or `-backend-config=backend.hcl` at `init` (also how you reuse one code base across environments).
- Changing backend settings requires `terraform init -reconfigure` (no migration) or `-migrate-state` (copy state to the new location).
- The backend's own credentials are separate from provider credentials; scope them to the state bucket only.
- Authentication in CI via OIDC (4.2); no static keys.
- **Bootstrapping chicken-and-egg**: the state bucket must exist before use. Create it with a tiny bootstrap configuration using local state (then migrate that state into the bucket it created), or with a script/CloudFormation, or use a managed backend. Document and protect it; `prevent_destroy` and deletion protection on the bucket.

```bash
# environment-specific backend settings kept outside code
terraform init -backend-config=backends/prod.hcl
# backends/prod.hcl
#   bucket = "acme-tfstate-prod"
#   key    = "ai-platform/network/terraform.tfstate"
#   region = "us-east-1"
```

## 4. Locking

When a command that may write state starts (`plan` with refresh, `apply`, `destroy`, `import`, `state` subcommands), Terraform acquires a lock through the backend, preventing concurrent writes. If another process holds it, you see `Error acquiring the state lock` with the lock ID, who and when. Handling:

- Wait (`-lock-timeout=5m`) rather than fail immediately in CI.
- **Never disable locking** (`-lock=false`) except for read-only `plan` in drift jobs where you accept the risk (`plan -lock=false` is safe from corruption but may race with a running apply).
- A crashed process can leave a stale lock: verify nothing is running (CI jobs, colleagues), then `terraform force-unlock <LOCK_ID>`. For S3 lockfile or DynamoDB backends, you can also inspect and remove the lock object manually; for GCS delete the `.tflock` object.
- CI must also serialise applies per state (concurrency groups, Atlantis locks) to avoid queues of stale plans (4.2): a plan generated before another apply is stale, and Terraform will refuse to apply a saved plan if state changed ("Saved plan is stale").

## 5. State layout: how to split

One giant state for the whole company is slow (refresh of thousands of resources), risky (any change can touch anything) and awkward for ownership. Many tiny states create dependency tangles. Split along **blast radius, change frequency and ownership**.

```text
infra-live/
├── global/                 # identity, DNS root zone, state buckets (rarely changes)
│   └── iam/ dns/ tfstate-bootstrap/
├── prod/
│   ├── network/            # VPC, subnets, firewalls, peering (changes rarely)
│   ├── storage/            # buckets for datasets & checkpoints (never destroy casually)
│   ├── k8s-cluster/        # GKE/EKS/AKS or Slurm VMs (changes occasionally)
│   ├── gpu-pools/          # node pools & quotas (changes often)
│   └── observability/
├── staging/ ...
└── lab/ ...
modules/                    # reusable, versioned
```

Guidelines:

- **Separate by lifecycle**: networks and IAM change rarely and cannot be allowed to be destroyed by a routine node-pool change; GPU capacity changes often; datasets and checkpoint stores must be protected.
- **Separate environments** into different states, accounts/projects and credentials (prod apply roles cannot be assumed by dev pipelines).
- **Keep layers acyclic**: higher layers consume lower layers' outputs, never the reverse.
- **Small enough to plan in minutes**, large enough to avoid excessive wiring. Tools like Terragrunt, Terraform stacks (HCP), Atlantis project configs, or Terramate help orchestrate many states and dependency order.
- **Keys/paths mirror directory structure** for discoverability: `prod/network/terraform.tfstate`.

### Sharing data across states

| Mechanism | How | Trade-offs |
|---|---|---|
| `terraform_remote_state` data source | Reads another state's outputs | Gives read access to the whole state (secrets!); tight coupling to output names; permission to read entire state file |
| Provider data sources | Look up resources by name/tag/ID (`data "google_compute_network"`) | Loose coupling, no state access; relies on naming conventions |
| Published outputs to a parameter store | Write IDs to SSM Parameter Store / Secret Manager / Consul; read via data sources | Explicit contract; extra resource |
| Module composition in one root | Pass outputs as arguments | Same state (bigger blast radius) |
| Terraform stacks / `tfe_outputs` | Platform-managed | Platform dependency |

Prefer data sources or a parameter store for cross-team boundaries, `terraform_remote_state` for tightly-coupled layers owned by one team, and **restrict who can read each state** because remote state read implies secret read.

## 6. Workspaces and state keys

Workspaces create multiple state files under one backend (S3: `env:/<workspace>/<key>`; GCS: `<prefix>/<workspace>.tfstate`). They share configuration and backend credentials, so the isolation is only logical (4.18). If used, combine with explicit variable files per workspace, naming that includes the workspace, and CI checks that the selected workspace matches the intended environment. For production-critical separation prefer separate directories/accounts/backends.

## 7. Migrating and restructuring state

### Move between backends

```bash
# 1. Make sure nobody is applying; take a backup
terraform state pull > backup-$(date +%F-%H%M).tfstate
# 2. Edit the backend block (local -> s3)
# 3. Migrate
terraform init -migrate-state          # confirms copy of existing state to the new backend
terraform plan                         # must show "No changes"
```

### Split or merge states, rename resources

Prefer **declarative refactoring blocks** (reviewable, repeatable in CI):

```hcl
moved {                      # rename or move within the same state
  from = aws_instance.gpu
  to   = module.compute.aws_instance.gpu
}

import {                     # adopt into the new state
  to = aws_s3_bucket.checkpoints
  id = "acme-ml-checkpoints-prod"
}

removed {                    # stop managing in the old state without deleting the real thing
  from = aws_s3_bucket.checkpoints
  lifecycle { destroy = false }
}
```

Splitting a resource from state A into state B without downtime: (1) in B add the resource config and an `import` block; (2) apply B (state B now tracks it); (3) in A add a `removed` block with `destroy = false`; apply A; (4) delete the code from A. Verify both plans are clean at each step. The older imperative way: `terraform state mv -state-out=other.tfstate ADDR ADDR`, or `state rm` + `import`; use only with backups and locks held.

### State surgery commands

```bash
terraform state list
terraform state show ADDR
terraform state pull > s.json                         # inspect (jq) or back up
terraform state mv ADDR_OLD ADDR_NEW
terraform state rm ADDR                               # forget; real resource stays
terraform state replace-provider registry.terraform.io/-/aws registry.terraform.io/hashicorp/aws
terraform state push s.json                           # DANGEROUS: overwrites; refuses on lineage mismatch or lower serial unless -force
```

Procedure for any surgery: announce, take a backup copy, ensure no CI is running (lock), operate, run `plan` expecting **no changes** (or only expected ones), and record what you did.

## 8. Recovery scenarios

| Scenario | Action |
|---|---|
| **State file deleted/lost** (no versioning) | Restore from backup/versioned bucket or `.backup`; otherwise rebuild state by `import` of every resource (use import blocks and `-generate-config-out`), carefully verifying plans show no changes; costly, hence versioning and replication |
| **State is corrupted** or an apply was killed midway | The backend usually holds the last good version (versioning). Restore previous object version and rerun `plan`; partially created resources not in state need import or manual deletion; Terraform writes state incrementally during apply so most crashes lose little |
| **Resource deleted outside Terraform** | `plan` shows re-create; accept, or `state rm` if intentionally gone |
| **Resource created outside, same name** | `import`; or rename/delete the stray |
| **Stuck lock** | Verify no runs, `force-unlock` |
| **Saved plan stale** | Re-plan; ensure serialised pipeline |
| **Provider upgrade changed schema** | Read changelog; run `plan` on a copy; use `moved`/`state replace-provider`; upgrade states in order |
| **Two stacks manage the same resource** | Pick one owner; `removed`/`state rm` from the other |
| **Accidental `destroy` plan** | Do not apply; investigate (wrong workspace, wrong directory, variable). Use `prevent_destroy` on critical resources and review plans for destroys |
| **Secrets exposed through state/logs** | Rotate secrets, restrict access, check access logs, then fix design (4.22) |

Backups: versioned buckets (keep many versions), periodic `terraform state pull` snapshots into a separate account, cross-region replication, tested restore procedure. State recovery is only real if you have practised it.

## 9. Drift

**Drift** is divergence between state/config and the real world: console edits, autoscalers or controllers changing fields, other automation, provider-side defaults, manual hotfixes during incidents.

Detection and handling:

- `terraform plan` (refresh on by default) displays drift as changes needed to revert; `terraform plan -refresh-only` shows only real-world differences from state; `terraform apply -refresh-only` writes them into state.
- Schedule `terraform plan -detailed-exitcode` nightly per environment (4.2); alert on exit code 2; assign owners to triage.
- Decide per drift: **revert** (apply to restore intended config), **adopt** (edit config to match, plan clean), or **tolerate** (`lifecycle { ignore_changes = [...] }` for fields legitimately managed elsewhere, such as autoscaler-managed `desired_size` or labels added by controllers).
- Reduce drift causes: restrict console write access (read-only for humans in production, break-glass with audit), use tags/labels to mark managed resources, policy engines that deny out-of-band changes, and GitOps controllers where relevant.
- Beware refresh costs and API rate limits on large states (`-refresh=false` speeds a plan but can plan against stale state; use sparingly, and split state).
- Some resources have **write-only or computed fields** the provider cannot read back; they show perpetual diffs or hide drift; check provider docs.

```hcl
resource "google_container_node_pool" "gpu" {
  # ...
  node_count = 2
  lifecycle {
    ignore_changes = [node_count]          # cluster autoscaler adjusts it
  }
}
```

## 10. Secrets and sensitive data in state

- Assume everything in state is readable by anyone with state access. Control access with IAM: separate read vs write, use per-environment buckets, KMS keys with audit trails, and no human access in production except break-glass.
- `sensitive = true` only redacts CLI output; it does not encrypt state. Sources of secrets in state: `random_password`, `tls_private_key`, `aws_db_instance.password`, `aws_iam_access_key`, data sources reading from Vault/Secrets Manager, provisioner outputs.
- Reduce exposure: prefer **not creating secrets in Terraform** (let the service generate them and store in a secret manager; reference by ID), use write-only/ephemeral arguments and ephemeral resources where supported (newer Terraform/OpenTofu), use IAM database auth/OIDC/workload identity instead of passwords, and rotate externally.
- **State encryption at rest**: backend-provided (KMS, SSE) is the baseline; **OpenTofu** additionally supports client-side state and plan encryption (key providers: PBKDF2 passphrase, AWS/GCP KMS, OpenBao); Terraform OSS relies on backend encryption.
- **Plan files** also contain sensitive values: treat saved plan artefacts as secrets (CI artefact retention and access control).
- Logs: `TF_LOG` output can contain secrets; keep off in shared CI logs.

## 11. State in CI/CD

- Plan and apply jobs use the same backend with least privilege: plan identity with read access to state (and lock write only if refresh locking is needed), apply identity with read/write only on protected branches (4.2).
- Serialise applies per state, cancel stale plans, use `-lock-timeout`, set `TF_IN_AUTOMATION` and `-input=false`.
- Upload the plan artefact and apply the exact artefact; handle "stale plan" by re-running the plan job.
- Keep modules versioned and state paths stable; changing a `key` creates a new empty state.
- Protect the backend: deletion protection, separate admin account, audit logs, alerts on state bucket policy changes or unexpected reads.
- Include state hygiene in reviews: PRs that touch `backend`, `moved`, `import`, `removed` blocks get platform-owner review (CODEOWNERS, 4.1).

## 12. Lab (untested)

1. **Read a state file**: apply a small local-provider config, then inspect `terraform.tfstate` with `jq`: serial, lineage, resources, attributes; change something and watch `serial` increment; find a "secret" generated by `random_password` in plaintext.
2. **Remote backend with MinIO**: run MinIO in Docker; create a bucket with versioning; configure the S3 backend (endpoint override, path style); migrate local state with `-migrate-state`; verify locking by running two applies concurrently.
3. **Locking behaviour**: hold a lock (a long `local-exec` sleep), try a second plan with and without `-lock-timeout`; simulate a stale lock and `force-unlock`.
4. **Bootstrap**: write the bootstrap configuration that creates the state bucket (with versioning, encryption, public-access block), then migrate its own state into it; add deletion protection.
5. **Partial backend config**: create `backends/dev.hcl` and `backends/prod.hcl`; run `init -backend-config`; show `-reconfigure` vs `-migrate-state`.
6. **Layered layout**: build `network` and `compute` roots; expose outputs; consume with `terraform_remote_state`, then replace with data sources; compare permissions needed.
7. **Refactor with blocks**: rename a resource and move it to a module (`moved`); then split a resource into another state using `import` + `removed` (destroy=false) with clean plans at each step.
8. **State surgery**: take a backup, `state mv`, `state rm`, `import`; make a mistake deliberately (wrong ID) and recover; try `state push` with a lower serial to see the safeguard.
9. **Disaster recovery**: delete the state object (versioned bucket) and restore the previous version; then simulate loss with no versioning and rebuild with `import` blocks for 5 resources.
10. **Drift**: change a resource out-of-band; `plan`, `plan -refresh-only`, `apply -refresh-only`; add `ignore_changes` for an autoscaler-managed field; schedule a `-detailed-exitcode` job.
11. **Secrets**: show a generated password in state; mitigate by using a random provider with write-only/ephemeral features (if available), or by moving the secret to a secret manager; with OpenTofu configure state encryption and verify the state file is ciphertext.
12. **CI**: add `-lock-timeout`, concurrency control and saved-plan artefacts to a pipeline; trigger two PRs at once; show serialised behaviour and stale plan handling.
13. **Clean up** buckets, containers and cloud resources.

Mark tested only after execution.

## 13. Common mistakes

- Local state on laptops or in Git; no versioning on the backend bucket.
- Disabling locking, or force-unlocking without checking who holds it.
- One giant state; or hundreds of micro-states with circular data dependencies.
- Workspaces as the only production isolation; shared credentials across environments.
- `terraform_remote_state` everywhere (grants broad state read) instead of data sources.
- Hand-editing JSON state; `state push` without backup; surgery during active CI.
- Treating `sensitive = true` as encryption; secrets generated by Terraform with state readable by everyone.
- Ignoring drift until the day a plan wants to destroy a cluster.
- `ignore_changes = all` or ignoring fields that hide real problems.
- No tested recovery plan; state bucket not protected from deletion.
- Changing the backend `key` and unknowingly starting with empty state.

## 14. Interview angles

- "What is in the state file? Why is it sensitive? How do you protect it?" 
- "Local versus remote state; what does a backend provide? How does locking work?" 
- "How would you structure state for dev/stage/prod and for network/compute/storage?" 
- "How do you move a resource between states without downtime?" (import + removed, clean plans.)
- "Someone deleted the state. What now?" (versioning/restore; rebuild by import.)
- "What is drift and how do you detect and handle it?" 
- "`terraform_remote_state` vs data sources: trade-offs." 
- "How do you handle secrets that Terraform must create?" 
- "Two engineers apply at the same time. What prevents corruption?" 

## 15. Checkpoint questions (35)

1. What does state map? **A:** Config addresses to real resource IDs/attributes.
2. What is `serial`? **A:** Counter incremented on every state write.
3. What is `lineage`? **A:** Unique ID of a state's history.
4. Is state a backup of infrastructure? **A:** No.
5. Why is state sensitive? **A:** Contains plaintext secrets.
6. Why not local state for teams? **A:** No locking/versioning/access control.
7. What backend features are essential? **A:** Locking, versioning, encryption, access control.
8. S3 locking options? **A:** `use_lockfile` (native) or DynamoDB (legacy).
9. Can backend blocks use variables? **A:** No; use partial config.
10. How supply backend values per env? **A:** `-backend-config` files.
11. `-reconfigure` vs `-migrate-state`? **A:** Ignore old vs copy state.
12. Bootstrap problem? **A:** State bucket must exist first.
13. What does `-lock-timeout` do? **A:** Wait for the lock.
14. When `force-unlock`? **A:** After verifying a stale lock.
15. Why serialise CI applies per state? **A:** Prevent races and stale plans.
16. What is a stale saved plan? **A:** State changed since plan was made.
17. Criteria for splitting state? **A:** Blast radius, change frequency, ownership.
18. Why separate prod and dev state/credentials? **A:** Limit accidental/compromised access.
19. Risk of `terraform_remote_state`? **A:** Grants read of the whole state.
20. Alternative for cross-stack data? **A:** Data sources/parameter store.
21. Workspace isolation strength? **A:** Logical only.
22. How move state to new backend? **A:** Edit backend, `init -migrate-state`.
23. Declarative rename tool? **A:** `moved` block.
24. Declarative forget-without-destroy? **A:** `removed` with `destroy = false`.
25. Command to forget a resource? **A:** `terraform state rm`.
26. Why backup before surgery? **A:** Mistakes are hard to undo.
27. What does `state push` risk? **A:** Overwriting newer state.
28. First response to lost state? **A:** Restore from versions/backups.
29. If no backup? **A:** Rebuild via imports and verify plans.
30. What is drift? **A:** Real world differs from config/state.
31. Command showing only drift? **A:** `plan -refresh-only`.
32. How tolerate externally managed fields? **A:** `ignore_changes`.
33. Does `sensitive = true` encrypt state? **A:** No.
34. Which tool adds client-side state encryption? **A:** OpenTofu.
35. Are plan files sensitive? **A:** Yes.

## 16. Sources and review notes

**Written in original words.** Principal sources:

- Yevgeniy Brikman, *Terraform: Up and Running* (chapter 3 on how to manage Terraform state: shared storage, locking, isolation via workspaces and file layout, remote state data source).
- The author's `nvidia-devops` repository, volume 10 chapter 5 (state commands, drift handling, import and refactoring, workspaces).
- Terraform and OpenTofu documentation for backends, state, `moved`/`import`/`removed` blocks, and state encryption.
- Examples are the author's constructions.

**Flagged for verification before publishing:** S3 native locking (`use_lockfile`) availability and DynamoDB deprecation timeline, backend argument names per version, `removed` block semantics, OpenTofu state-encryption configuration syntax, write-only/ephemeral features by version, and every code listing; all labs are **untested**.
