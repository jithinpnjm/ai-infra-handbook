---
id: "c04-21"
title: "4.21 Terraform loops, conditionals, lifecycle and gotchas"
sidebar_label: "4.21 Terraform loops, conditionals, lifecycle and gotchas"
sidebar_position: 21
description: "count, for_each, for expressions and dynamic blocks; conditionals; lifecycle rules (prevent_destroy, create_before_destroy, ignore_changes, replace_triggered_by, preconditions); zero-downtime deployment patterns; and the sharp edges of Terraform"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 4.21 Terraform loops, conditionals, lifecycle and gotchas

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Terraform/OpenTofu 1.6+; local providers suffice |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

GPU platforms are repetitive by nature: eight node pools that differ in two attributes, per-team namespaces and quotas, per-rack firewall rules, N identical training nodes plus a few special ones. Loops and conditionals let you describe those patterns compactly; lifecycle rules let you protect the irreplaceable (checkpoint buckets, databases, clusters) and orchestrate safe replacement of the replaceable (GPU instances, launch templates). Misusing these features is how teams accidentally destroy a node pool because they removed an item from the middle of a list. This chapter covers the iteration and conditional constructs, how to avoid their traps, the lifecycle block, and the known sharp edges.

## Prerequisites and outcomes

Needs 4.18 to 4.20. After this chapter you can:

- Use `count`, `for_each`, `for` expressions, splats and `dynamic` blocks correctly; choose between them and explain index shifting and key stability.
- Express conditionals with ternaries, `count = cond ? 1 : 0`, `for_each` over filtered maps; avoid invalid cycles and unknown-value errors.
- Apply lifecycle arguments: `create_before_destroy`, `prevent_destroy`, `ignore_changes`, `replace_triggered_by`, `precondition`/`postcondition`; understand `moved`, `removed`.
- Implement zero-downtime replacement patterns and rolling changes for fleets.
- Diagnose gotchas: inconsistent plans, unknown `for_each` keys, dependency cycles, perpetual diffs, eventual consistency, provider bugs, and limits of the language.

## 1. count

`count` creates N instances of a resource or module, addressed by index `type.name[0]`.

```hcl
variable "gpu_node_count" { type = number }

resource "google_compute_instance" "gpu" {
  count        = var.gpu_node_count
  name         = "gpu-${format("%02d", count.index)}"
  machine_type = "a2-highgpu-8g"
  # ...
}

output "gpu_ips" { value = google_compute_instance.gpu[*].network_interface[0].network_ip }
```

Strengths: simplest way to make N identical things; conditional creation (`count = var.enabled ? 1 : 0`). Weaknesses:

- **Identity is the index.** Removing an element from the middle of a *list* that drives `count`/indexing shifts all later items, so Terraform plans to destroy and recreate them.

```hcl
variable "names" { default = ["a100-train", "h100-train", "a100-infer"] }
resource "some_pool" "p" {
  count = length(var.names)
  name  = var.names[count.index]       # remove "h100-train" => indices 1 and 2 change => pool a100-infer is replaced
}
```

- Cannot loop over inline blocks (use `dynamic`), and cannot make a resource conditional per key.
- Referencing an instance that may not exist needs care (`one(resource.x[*].id)`, `try(resource.x[0].id, null)`).

Use `count` for homogeneous, interchangeable instances where only the number matters, and for on/off switches. Even there, prefer `for_each` with stable keys when instances can be individually removed or renamed.

## 2. for_each

`for_each` takes a map or a set of strings and creates one instance per element, addressed by key `type.name["key"]`; `each.key` and `each.value` are available.

```hcl
variable "pools" {
  type = map(object({
    machine_type = string
    gpu_count    = number
    max_nodes    = number
  }))
  default = {
    h100-train = { machine_type = "a3-highgpu-8g", gpu_count = 8, max_nodes = 16 }
    l4-infer   = { machine_type = "g2-standard-24", gpu_count = 2, max_nodes = 8 }
  }
}

resource "google_container_node_pool" "gpu" {
  for_each = var.pools
  name     = each.key
  cluster  = google_container_cluster.main.name
  autoscaling { max_node_count = each.value.max_nodes }
  node_config { machine_type = each.value.machine_type }
}
```

Removing `l4-infer` from the map destroys only that pool; adding a key adds only that pool: identity is the key, not the position. This is the default choice for collections of distinct things.

Rules and limits:

- `for_each` accepts a map or a `set(string)`; convert lists with `toset(list)` (requires unique strings) or build a map with a `for` expression: `{ for p in var.pool_list : p.name => p }`.
- **Keys must be known at plan time.** `for_each = toset(aws_instance.x[*].id)` fails if IDs are unknown until apply ("The for_each map includes keys derived from resource attributes that cannot be determined until apply"). Derive keys from static inputs (names), and use values (which may be unknown) as map values.
- `count` and `for_each` cannot be used together on the same resource; `for_each` instances are removed individually by deleting keys.
- Sensitive values cannot be used as `for_each` keys.
- Chain loops by transforming data: build a flat map of "pairs" with `for` and `flatten` / `setproduct`:

```hcl
locals {
  # one firewall rule per (team, port)
  rules = {
    for pair in setproduct(keys(var.teams), var.ports) :
    "${pair[0]}-${pair[1]}" => { team = pair[0], port = pair[1] }
  }
}
resource "google_compute_firewall" "team" {
  for_each = local.rules
  name     = "allow-${each.key}"
  # ...
}
```

## 3. for expressions and splats

`for` expressions transform collections (they build values; they do not create resources):

```hcl
locals {
  upper_names   = [for n in var.names : upper(n)]                         # list -> list
  name_to_gpus  = { for k, v in var.pools : k => v.gpu_count }            # map -> map
  big_pools     = { for k, v in var.pools : k => v if v.gpu_count >= 8 }  # filter
  ip_list       = [for i in google_compute_instance.gpu : i.network_interface[0].network_ip]
  grouped       = { for p in var.pool_list : p.region => p.name... }       # "..." groups values into lists per key
  total_gpus    = sum([for p in values(var.pools) : p.gpu_count * p.max_nodes])
}
```

Splat `resource.name[*].attr` is shorthand for a `for` over a list of instances (for maps use `values(resource.name)[*].attr`). `flatten`, `merge`, `zipmap`, `lookup`, `setunion`, `setproduct`, `distinct`, `compact`, `concat`, `slice`, `range`, `chunklist` and `try`/`can` cover most reshaping needs. Test with `terraform console`.

## 4. dynamic blocks

Dynamic blocks generate repeated *nested blocks* inside a resource (firewall `allow` rules, `ingress` rules, labels as blocks, `taint` blocks, disks).

```hcl
resource "aws_security_group" "cluster" {
  name   = "${local.name}-cluster"
  vpc_id = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules                     # map or list of objects
    content {
      from_port   = ingress.value.from
      to_port     = ingress.value.to
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidrs
      description = ingress.key
    }
  }

  ingress {                                          # EFA requires all traffic allowed within the group itself
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }
}
```

Use sparingly: dynamic blocks hurt readability. Also: some resources manage rules as separate resources (`aws_security_group_rule`, `aws_vpc_security_group_ingress_rule`); mixing inline blocks and separate rule resources for the same group causes perpetual fights, so choose one.

## 5. Conditionals

```hcl
# Ternary
instance_type = var.env == "prod" ? "p5.48xlarge" : "g5.xlarge"

# Optional resource
resource "aws_cloudwatch_dashboard" "gpu" {
  count          = var.enable_dashboard ? 1 : 0
  dashboard_name = "${local.name}-gpu"
  dashboard_body = file("${path.module}/dashboard.json")
}
output "dashboard_name" { value = one(aws_cloudwatch_dashboard.gpu[*].dashboard_name) }   # null if absent

# Optional per-key resource via filtered map
resource "aws_ebs_volume" "scratch" {
  for_each = { for k, n in var.nodes : k => n if n.scratch_gb > 0 }
  size     = each.value.scratch_gb
  # ...
}

# Optional block
dynamic "kms_key" {
  for_each = var.kms_key_arn == null ? [] : [var.kms_key_arn]
  content { arn = kms_key.value }
}

# Defaults and null handling
name = coalesce(var.name_override, "${local.name}-default")
size = try(var.disk.size, 100)
```

Caveats: both branches of a ternary must have the same type (use `tolist`, `tomap` or `null` consistently); conditionals are evaluated at plan time and cannot depend on values known only after apply when used in `count`/`for_each` ("count value depends on resource attributes that cannot be determined until apply"): pass booleans/known inputs, not resource attributes. Each boolean toggle multiplies test cases; prefer composition over toggles in shared modules (4.20). There is no `if` statement in HCL: conditional logic is expression-level only.

## 6. The lifecycle block

```hcl
resource "aws_instance" "login" {
  # ...
  lifecycle {
    create_before_destroy = true
    prevent_destroy       = false
    ignore_changes        = [tags["last_patched"], user_data]
    replace_triggered_by  = [aws_launch_template.gpu.latest_version]
    precondition {
      condition     = data.aws_ec2_instance_type.selected.default_vcpus >= 16
      error_message = "Login nodes need at least 16 vCPUs."
    }
    postcondition {
      condition     = self.public_ip == ""
      error_message = "Login nodes must not have public IPs."
    }
  }
}
```

| Setting | Effect | Use |
|---|---|---|
| `create_before_destroy = true` | Create the replacement first, then destroy the old one | Zero-downtime replacement (launch templates, load-balanced instances, certificates); requires unique names or `name_prefix`/random suffix to avoid collisions; propagates to dependencies |
| `prevent_destroy = true` | Any plan that would destroy the resource errors | Checkpoint buckets, databases, state buckets, KMS keys; not a security control (removing the argument allows destroy) and it does not stop `terraform destroy` of the whole config from erroring only for that resource |
| `ignore_changes = [attrs]` or `all` | Changes to these attributes in the real world (or config) do not trigger updates | Fields managed elsewhere: autoscaler `desired_size`, tags added by controllers, rotating passwords; avoid `all` (hides drift) |
| `replace_triggered_by = [refs]` | Replace this resource when referenced resources/attributes change | Force instance replacement when a template/image changes without editing the instance |
| `precondition` | Validates assumptions before evaluating/creating (input/data sanity) | Check data source results, cross-variable constraints |
| `postcondition` | Validates the created object's attributes (`self`) | Assert provider returned expected values (encryption on, no public IP) |
| `ignore_changes` with `moved`/`removed` | See 4.19 | Refactors |

Related constructs: `check` blocks (non-blocking assertions with scoped data sources, good for health checks of the deployed system), `terraform_data` with `triggers_replace` (the modern `null_resource`), and the `-replace` flag for ad-hoc replacement. `depends_on` handles hidden ordering; use sparingly because it makes modules less parallel and sometimes defers data sources to apply time.

## 7. Zero-downtime and rolling patterns

Terraform replaces; it does not orchestrate rolling restarts of a fleet. Choose the pattern that delegates orchestration to a system that can do it:

1. **Instance group / node-pool update policies**: let the platform roll nodes (GCE managed instance group `update_policy` with `max_surge`/`max_unavailable`, GKE node pool upgrade settings, EKS managed node group `update_config`, AWS ASG `instance_refresh`). Terraform changes the template; the platform replaces instances gradually.
2. **Blue/green with `create_before_destroy`**: create a new node pool/launch template version (unique suffix), shift traffic or workloads (cordon/drain old), then destroy the old; scripted via CI or a controller. For Slurm clusters, add new nodes, drain old nodes through Slurm (4.17), then remove them.
3. **Immutable images**: new image ID triggers new launch template version; combine with `replace_triggered_by` or ASG refresh; pair with image pipelines (4.2).
4. **Terraform-driven canary**: variable `canary_count` for a new template version; apply; validate (4.2); then set to full.
5. **Avoid in-place mutation of stateful nodes** (kernel or driver upgrades by `remote-exec`); use images and replacement or Ansible with drain workflows (4.17).

Create-before-destroy gotchas: resources with unique naming constraints (security groups, node pool names, IAM roles) collide unless names include a random suffix (`name_prefix` or `random_id`); dependency chains get CBD propagated; some resources cannot coexist (a static IP attached to two instances); capacity-limited GPUs may not be available for both old and new simultaneously, so destroy-first (with disruption) may be the only option; plan for it with drains.

## 8. Gotchas and sharp edges

1. **Index shifting with `count`** over lists (section 1): prefer `for_each` with keys.
2. **Unknown values in `count`/`for_each`**: arguments must be known during plan. Fix by deriving from static data, splitting into layers (apply network first, then dependent stack), or two-phase apply with `-target` only as a last resort.
3. **Dependency cycles**: A references B and B references A (security group rules referencing each other). Break with separate rule resources, `self` references, or reorganising.
4. **Inconsistent final plan / "Provider produced inconsistent result after apply"**: provider bug or eventual consistency; rerun apply; report upstream; pin provider versions.
5. **Eventual consistency**: IAM roles and policies take seconds to propagate; resources fail creating with "invalid principal". Mitigate with `depends_on` on the policy attachment, retries in provider settings, or `time_sleep` resource (as a last resort).
6. **Perpetual diffs**: attributes the provider normalises (case, ordering, defaults) differ from config. Use the normalised form, `ignore_changes`, or fix the provider version. Lists vs sets ordering.
7. **Renaming forces replacement**: many `name` attributes are immutable; check docs and the plan; use `name_prefix` and CBD.
8. **Large plans/API rate limits**: split state (4.19); lower `-parallelism`; provider retry settings; avoid refreshing thousands of resources in every PR.
9. **Secrets in plans and state** (4.22): `sensitive` is cosmetic.
10. **`depends_on` on modules** defers all data sources inside to apply, producing noisy diffs; prefer passing outputs as inputs to create implicit dependencies.
11. **Provisioners and `local-exec`** are outside the model; failures taint resources; avoid.
12. **Function limits**: no loops except `for`; no user functions; `timestamp()` changes every plan; `uuid()` changes every plan; use `random_*`/`time_static`.
13. **Type inference surprises**: `tolist` on sets sorts; lists of mixed types become tuples; empty list vs null; `any` types. Use explicit types.
14. **Large `for_each` of modules/resources** can slow planning; split by ownership.
15. **Multi-region/multi-account provider config** cannot be dynamic per `for_each`; repeat module calls or separate stacks (4.22).
16. **Zero-diff upgrades**: provider upgrades may introduce new defaults; review plans after `init -upgrade`.
17. **`terraform destroy` order and protected resources**: `prevent_destroy` makes destroy fail halfway (plan fails before any change, good); some resources need `force_destroy` (buckets with objects) deliberately set to false for data stores.
18. **Moving between `count` and `for_each`** changes addresses; use `moved` blocks (`from = x[0]`, `to = x["name"]`).
19. **Order of list elements from data sources** may change between runs; sort (`sort`, `sort by key`) before use.
20. **Time-based or non-deterministic data** (latest AMI) causes unplanned replacements; pin image IDs/families deliberately and update through PRs.

## 9. Worked example: GPU capacity by data

```hcl
variable "teams" {
  type = map(object({
    gpu_quota   = number
    namespaces  = list(string)
    admins      = list(string)
  }))
}

locals {
  # flatten to one entry per (team, namespace) for per-namespace resources
  team_namespaces = merge([
    for team, cfg in var.teams : {
      for ns in cfg.namespaces : "${team}/${ns}" => { team = team, ns = ns, quota = cfg.gpu_quota }
    }
  ]...)
}

resource "kubernetes_namespace" "ns" {
  for_each = local.team_namespaces
  metadata {
    name   = each.value.ns
    labels = { team = each.value.team }
  }
}

resource "kubernetes_resource_quota" "gpu" {
  for_each = local.team_namespaces
  metadata {
    name      = "gpu-quota"
    namespace = kubernetes_namespace.ns[each.key].metadata[0].name
  }
  spec {
    hard = { "requests.nvidia.com/gpu" = tostring(each.value.quota) }
  }
}
```

Adding a team or namespace adds only its resources; removing one removes only its resources (a reviewer should still confirm the destroy of a namespace is intended: it deletes workloads). Add `lifecycle { prevent_destroy = true }` on namespaces holding persistent volumes.

## 10. Lab (untested)

1. **count vs for_each**: create three `terraform_data`/`random_pet` resources with `count` driven by a list; remove the middle element and read the plan; repeat with `for_each` over a map; add `moved` blocks to convert one to the other without recreation.
2. **Unknown keys**: attempt `for_each = toset(random_id.x[*].hex)` and read the error; fix by using static keys.
3. **for expressions**: from a variable of pools compute: names list, GPU totals, filtered big pools, grouped-by-region map; explore in `terraform console`.
4. **Dynamic blocks**: generate firewall/ingress rules from a map; compare with separate rule resources; show the perpetual-diff problem from mixing the two (with a provider that supports both, or by reading docs).
5. **Conditionals**: optional resource with `count = var.enabled ? 1 : 0` and `one()` in the output; optional nested block via `dynamic`; ternary type mismatch error and fix.
6. **Lifecycle**: `prevent_destroy` on a local file or bucket and try to remove it; `ignore_changes` for a field mutated outside; `replace_triggered_by` on a `terraform_data` whose input changes; `precondition`/`postcondition` with failing messages.
7. **create_before_destroy**: with a resource requiring unique names (use `random_id` suffix), force replacement and observe ordering in the plan and apply output.
8. **Rolling pattern**: in a cloud sandbox change a launch template in an instance group with an update policy and watch the platform roll instances; compare with direct instance replacement.
9. **Cycle and eventual consistency**: reproduce a dependency cycle between two security-group-like resources (with `terraform_data` references) and break it; add a `time_sleep` to model propagation.
10. **Worked example**: implement the team/namespace quotas against a kind cluster; add and remove teams; verify minimal diffs.
11. **Gotcha audit**: review an existing configuration for index-shifting `count`, `timestamp()`, `ignore_changes = all`, provisioners; file fixes.
12. **Clean up.**

Mark tested only after execution.

## 11. Common mistakes

- Using `count` with lists of distinct items and then deleting from the middle.
- Making `for_each` keys depend on apply-time values.
- Toggling features with booleans in every module; enormous variable matrices.
- Overusing `ignore_changes = all`, `prevent_destroy` as a security control, or `-target` as workflow.
- Mixing inline rule blocks and standalone rule resources for the same parent.
- Assuming `create_before_destroy` works without unique names or capacity.
- Treating `terraform apply` as an orchestrator of rolling fleet updates.
- Using volatile functions (`timestamp`, `uuid`) in resource arguments.
- Not reading plans for replacements after provider or module upgrades.

## 12. Interview angles

- "`count` versus `for_each`: when and why? What happens when you remove an item from the middle?" 
- "What does `create_before_destroy` do and what breaks?" 
- "How do you stop someone from accidentally destroying a checkpoint bucket?" (prevent_destroy, deletion protection, IAM, policy.)
- "Why can't `for_each` use apply-time values? How do you work around it?" 
- "How do you handle fields modified outside Terraform, e.g. autoscaler node counts?" (ignore_changes.)
- "How do you do rolling updates of GPU nodes with Terraform?" (delegate to platform update policy/drain.)
- "What are the main reasons a plan shows unexpected diffs?" 
- "Explain dynamic blocks and when not to use them."

## 13. Checkpoint questions (30)

1. What identifies a `count` instance? **A:** Numeric index.
2. What identifies a `for_each` instance? **A:** Map key / set element.
3. Which is safer for distinct items? **A:** `for_each`.
4. Why does removing a middle list item hurt `count`? **A:** Later indices shift, causing recreation.
5. What types does `for_each` take? **A:** Map or set of strings.
6. Convert list to set? **A:** `toset()`.
7. Must keys be known at plan? **A:** Yes.
8. What does `one()` do? **A:** Returns the single element or null from a 0/1 list.
9. What does a `for` expression produce? **A:** A list or map value.
10. What does `...` do in a `for` map? **A:** Groups values into lists per key.
11. What is a splat? **A:** `[*]` shorthand to extract attributes from lists.
12. What is a dynamic block? **A:** Generates nested blocks.
13. Ternary rule? **A:** Both branches same type.
14. Conditional resource idiom? **A:** `count = cond ? 1 : 0`.
15. Optional block idiom? **A:** Dynamic with `[]` or single-element list.
16. What does `create_before_destroy` need? **A:** Unique names, capacity.
17. What does `prevent_destroy` do? **A:** Errors on plans that destroy it.
18. Is it a security control? **A:** No.
19. What does `ignore_changes` do? **A:** Ignores diffs on listed attributes.
20. Why avoid `ignore_changes = all`? **A:** Hides drift.
21. What does `replace_triggered_by` do? **A:** Forces replacement on referenced change.
22. `precondition` vs `postcondition`? **A:** Before vs after, `self`.
23. What is a `check` block? **A:** Non-blocking assertion with scoped data.
24. What replaces `null_resource`? **A:** `terraform_data`.
25. Why `timestamp()` is a problem? **A:** Changes every plan.
26. Cause of dependency cycles? **A:** Mutual references.
27. Fix for IAM eventual consistency? **A:** depends_on, retries, time_sleep.
28. How roll nodes gradually? **A:** Platform update policies, drain flow.
29. How convert count to for_each safely? **A:** `moved` blocks.
30. What causes perpetual diffs? **A:** Provider normalisation/ordering mismatches.

## 14. Sources and review notes

**Written in original words.** Principal sources:

- Yevgeniy Brikman, *Terraform: Up and Running* (chapter 5 on Terraform tips and tricks: loops, conditionals, zero-downtime deployment, and gotchas).
- The author's `nvidia-devops` repository, volume 10 chapter 5 (HCL masterclass: `count` versus `for_each`, dynamic blocks, lifecycle).
- Terraform and OpenTofu language documentation (meta-arguments, expressions, functions, lifecycle).
- Examples are the author's constructions.

**Flagged for verification before publishing:** behaviour of `replace_triggered_by`, `terraform_data` triggers, `removed` blocks and mock/test features by version; the `merge(...)...` expansion idiom; provider-specific attributes (security group rule styles, node pool update policies); and every code listing; all labs are **untested**.
