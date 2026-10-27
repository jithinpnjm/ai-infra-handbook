---
id: "c05-22"
title: "5.22 Multitenancy and platform services"
sidebar_label: "5.22 Multitenancy and platform services"
sidebar_position: 22
description: "Designing a multi-tenant Kubernetes platform for AI teams: tenancy models and isolation levels, namespaces, quotas and LimitRanges, RBAC/network/policy/storage/GPU isolation, hierarchical namespaces and vCluster/virtual clusters, self-service, platform services (ingress, registries, CI, observability, notebooks, queueing), cost allocation and the platform-as-a-product model"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 5.22 Multitenancy and platform services

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | kind/kubeadm; Kyverno or VAP; Kueue; optional Capsule, HNC, vCluster, JupyterHub, OpenCost |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

A GPU cluster is rarely built for one team. Research groups, product teams, external customers and platform engineers share the same scarce, expensive hardware, and each expects fairness, security, performance isolation and self-service. Without a deliberate tenancy model you get noisy neighbours (one job floods the API or the storage), security incidents (cross-tenant data access), unfair allocation (one team squats on GPUs), unmanageable support load, and no cost visibility. With a good model, teams onboard in minutes via a pull request, get quotas and queues automatically, run in isolated namespaces with default-deny networking, and see their usage and cost. This chapter turns the individual mechanisms (RBAC, quotas, network policy, admission, scheduling, storage) into a coherent multi-tenant platform and describes the platform services that sit around the cluster.

## Prerequisites and outcomes

Needs 5.7, 5.15, 5.16, 5.18, 5.21. After this chapter you can:

- Compare tenancy models (soft vs hard, namespace-per-tenant, cluster-per-tenant, virtual clusters) and match them to trust levels.
- Implement namespace-level isolation: RBAC, ResourceQuota/LimitRange, NetworkPolicy, Pod Security, storage, secrets, priority, and node isolation (dedicated pools, taints, sandboxed runtimes).
- Provide fair GPU sharing with Kueue (queues, cohorts, preemption, fair sharing), MIG/time-slicing/MPS where appropriate, and enforce quotas at multiple layers.
- Use hierarchical namespaces/Capsule/vCluster or similar to delegate administration.
- Automate tenant onboarding and offboarding (GitOps, Terraform, generators) and expose self-service interfaces.
- Design platform services (registry, ingress, notebooks, CI/CD, storage, observability, model serving, experiment tracking) and operate the platform as a product with SLOs, docs and support.
- Allocate and report cost per tenant.

## 1. Tenancy models and trust levels

| Model | Isolation boundary | Trust assumption | Typical use |
|---|---|---|---|
| **Namespace per team** (soft multi-tenancy) | Namespace + RBAC + quota + network policy + PSA | Tenants are cooperative but may make mistakes; internal teams | Most internal AI platforms |
| **Namespace per team + dedicated node pools** | Adds node-level isolation (taints, labels, separate hardware) | Reduce noisy neighbours, compliance for sensitive data | Regulated data, performance-critical |
| **Namespace + sandboxed runtimes** (gVisor/Kata) | Adds kernel-level isolation for untrusted code | Untrusted code (notebooks, customer containers) | Public/semi-public notebooks, SaaS |
| **Virtual clusters** (vCluster, Kamaji, HyperShift hosted control planes) | Tenant gets their own API server/CRDs/RBAC; shared workers | Tenants need cluster-admin-like autonomy (CRDs, operators) | Platform teams, CI environments, labs |
| **Cluster per tenant** (hard multi-tenancy) | Separate control and data planes | Hostile or contractually separate tenants | External customers, regulated tenants |
| **Multi-cluster fleet with workload placement** | Many clusters, federated scheduling | Scale and failure isolation | Large orgs (5.35) |

Kubernetes itself provides **soft multi-tenancy**: the control plane is shared; tenants share the API server, scheduler, etcd, nodes' kernel, DNS, and often storage and network. Hard guarantees require separation at the layer you worry about (nodes, kernel, control plane). Choose by **threat model and compliance**, not by default.

### Isolation layers (what to configure)

| Layer | Mechanisms | Notes |
|---|---|---|
| **API/Control plane** | RBAC (namespaced roles), admission policy, API Priority & Fairness per tenant, audit | One tenant's controller can overload the API; give operators their own APF levels (5.5) |
| **Identity** | OIDC groups per team; workload identity per ServiceAccount | Avoid shared credentials |
| **Compute (CPU/memory/GPU)** | ResourceQuota, LimitRange, Kueue ClusterQueues, priority classes, node pools/taints, CPU/Topology Manager | GPUs are the contested resource |
| **Network** | Default-deny NetworkPolicy, per-tenant egress allowlists, separate ingress classes/domains, secondary networks isolated by VLAN/PKey | RDMA fabrics need fabric-level isolation (5.15, Part 12) |
| **Storage** | Per-tenant StorageClasses, quotas per class, per-tenant subdirectories/exports, encryption keys per tenant, snapshots/backups scoped | Shared parallel FS requires quotas and ACLs |
| **Secrets** | Namespaced Secrets, external secret store paths per tenant, workload identity | Never share cloud credentials |
| **Runtime/kernel** | PSA, seccomp/AppArmor, sandboxed RuntimeClass, `hostUsers: false`, no host namespaces | Kernel is shared in runc: kernel exploits cross tenants |
| **Observability** | Per-tenant dashboards/log access (Grafana orgs/folders, Loki tenants), metrics label scoping | Do not expose other tenants' data |
| **Cost** | Labels, namespace attribution, OpenCost/Kubecost, GPU-hour accounting | Chargeback/showback drives behaviour |

## 2. Namespace-level building blocks

### ResourceQuota and LimitRange

```yaml
apiVersion: v1
kind: ResourceQuota
metadata: { name: team-a-compute, namespace: team-a }
spec:
  hard:
    requests.cpu: "512"
    requests.memory: 4Ti
    requests.nvidia.com/gpu: "32"            # extended resources use the requests. prefix
    limits.memory: 4Ti
    requests.ephemeral-storage: 20Ti
    persistentvolumeclaims: "50"
    requests.storage: 100Ti
    fast-nvme.storageclass.storage.k8s.io/requests.storage: 20Ti
    count/jobs.batch: "500"
    count/pods: "2000"
    services.loadbalancers: "0"
    services.nodeports: "0"
  scopeSelector:                              # optional: quota only for a priority class
    matchExpressions: [ { scopeName: PriorityClass, operator: In, values: [training-normal] } ]
---
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: team-a }
spec:
  limits:
    - type: Container
      default: { cpu: "2", memory: 8Gi }
      defaultRequest: { cpu: "1", memory: 4Gi }
      max: { cpu: "128", memory: 1Ti }
    - type: PersistentVolumeClaim
      max: { storage: 10Ti }
      min: { storage: 1Gi }
```

Behaviour: ResourceQuota is enforced at admission (creation fails with `exceeded quota`), counts requests of *all* pods (including Pending) in the namespace; if a quota covers compute resources, pods must specify requests/limits for those resources (LimitRange defaults help). Quotas on `count/*` protect the API server from object floods (thousands of Jobs/Pods/ConfigMaps). Quotas are namespace-bound; per-team quota across many namespaces needs hierarchical tools (HNC, Capsule) or Kueue cohorts.

### Priority and fair sharing

Combine **PriorityClasses** with **ResourceQuota scopeSelector** to cap how many high-priority pods a team may run (prevents priority abuse), and **Kueue** for dynamic GPU sharing: each team has a `ClusterQueue` with `nominalQuota`, can borrow idle quota from a `cohort`, and is preempted when owners reclaim (5.18). Provide a few **WorkloadPriorityClasses** (`production`, `high`, `normal`, `best-effort`). Provide **fair-share** weights so large teams don't starve small ones; show queue positions and wait times to users.

### GPU sharing options

| Method | Isolation | Use | Caveats |
|---|---|---|---|
| **Whole GPUs** (`nvidia.com/gpu: N`) | Strong | Training, large inference | Fragmentation risk |
| **MIG** (A100/H100/B200 partition into instances with dedicated SMs/memory/bandwidth) | Hardware-level QoS and fault isolation | Many small inference/dev workloads; multi-tenant | Fixed profiles; reconfiguration needs idle GPU; fewer cross-instance features (no NVLink peer P2P) |
| **Time-slicing** (device plugin oversubscription) | None (context switching) | Dev notebooks, light inference | No memory/fault isolation, unpredictable latency |
| **MPS** (CUDA Multi-Process Service) | Weak/shared (memory limits via `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT`, active thread %) | Concurrent small jobs from one tenant | Single-tenant trust; fault propagation |
| **vGPU** (virtualised GPUs via hypervisor, licence) | Strong | VM-based multi-tenancy | Licensing, hypervisor stack |
| **DRA with partitionable devices** | Depends on partition type | Flexible claims for MIG/shared devices | Maturity varies |

For multi-tenant security, prefer whole GPUs or MIG; avoid time-slicing/MPS between mutually untrusted tenants (side channels, DoS). Dedicated node pools per tenant class simplify driver/config differences (MIG strategy `single`/`mixed`, GPU Operator configs per pool).

### Node isolation

Dedicated pools per tenant or sensitivity level via taints/labels + admission (inject tolerations/nodeSelector for the namespace's pool, forbid overrides); separate nodes for system components, for untrusted notebooks (sandboxed RuntimeClass), for production inference. Avoid pod-level `hostNetwork`/`hostPID`. Consider node-level encryption, secure boot/measured boot, and wiping local NVMe between tenants (init containers can't guarantee; use node recycling for strict cases).

## 3. Delegated administration and virtual clusters

- **Hierarchical Namespace Controller (HNC)** (`hnc.x-k8s.io`): parent/child namespaces inherit RBAC, NetworkPolicies, quotas (propagated objects); team leads create sub-namespaces via `SubnamespaceAnchor`. Maintenance mode of the project: evaluate alternatives.
- **Capsule** (Tenant CRD): a `Tenant` groups namespaces, owners, quotas across namespaces, network/storage/ingress class restrictions, node selectors, allowed registries, namespace limits; owners create namespaces self-service; lightweight.
- **Kubernetes multi-tenancy benchmarks** (kubernetes-sigs/multi-tenancy) and **Kyverno/VAP policies** codify rules; Argo CD AppProjects and Flux tenants constrain what each team's GitOps deploys (4.26).
- **Virtual clusters**: **vCluster** runs a tenant control plane (API server + syncer, often k3s) inside a namespace; tenant pods are synced to the host as ordinary pods, so the host scheduler and nodes are shared while tenants get their own API, CRDs, RBAC and namespaces; strong DX for platform teams and CI. **Kamaji**, **HyperShift (hosted control planes)**, **Cluster API** for full separate clusters at scale. Trade-offs: extra control-plane overhead, syncing complexity, isolation still depends on the host's node security and policies on synced pods (enforce policies on the host).

## 4. Self-service and onboarding

Tenant onboarding as code (GitOps/Terraform, 4.25, 4.26):

```yaml
# tenants/team-a.yaml  (data-driven; rendered by Terraform/Helm/Kustomize/Kyverno-generate)
name: team-a
owners: ["oidc:team-a-leads"]
members: ["oidc:team-a-researchers"]
namespaces: [team-a-dev, team-a-train, team-a-serve]
quotas:
  gpu: { nominal: 32, borrowingLimit: 16, flavor: h100 }
  cpu: 512
  memory: 4Ti
  storage: { fast-nvme: 20Ti, shared-rwx: 100Ti }
priority: normal
egress: [object-store, registry, pypi-mirror]
cost: { center: CC-1042, budgetMonthlyUsd: 120000 }
```

Automation creates: namespaces with labels (`team`, `tier`, `cost-center`, PSA labels); RoleBindings for OIDC groups; ResourceQuota/LimitRange; Kueue `LocalQueue`s and `ClusterQueue` (and ResourceFlavor mapping); default-deny and DNS NetworkPolicies plus approved egress; StorageClass access/PVC quotas and storage subdirectories/export policies; secret store paths and workload identity bindings; ingress/hostname allocations; Grafana folder/org and alert routes; registry project/robot accounts; ArgoCD AppProject; budget alerts. **Offboarding**: archive data per retention policy, revoke access, delete namespaces after notice, release quota, reclaim volumes (`Retain` → backup → delete).

Self-service interfaces: Git PR workflow (default), a **developer portal** (Backstage with Kubernetes, Argo, Kueue plugins; Port; internal CLI), notebook portals (JupyterHub/Kubeflow/Run:ai/ DGX Cloud UIs), a **job submission CLI/SDK** hiding YAML (`mlctl submit train.yaml --gpus 16`), templates (Helm charts/Kustomize bases/Cookiecutter) for jobs, services and pipelines with built-in best practices (resource requests, probes, checkpointing, labels).

### The `Team` custom resource operator pattern and the 4-stage spectrum of platform abstractions

Beyond rendering tenant YAML in CI/CD pipelines, *Production Kubernetes* (Chapter 16) shows how mature platforms implement self-service tenant onboarding natively inside the cluster using a custom **`Team` operator**. When a platform engineer or portal submits a `Team` custom resource specifying the owner and resource quotas, the in-cluster controller continuously reconciles the tenant's `Namespace`, `RoleBinding`s, `ResourceQuota`, `LimitRange`, `NetworkPolicy`, and even Grafana dashboards or Alertmanager routes—automatically restoring any role or quota that someone accidentally deletes. In the book's example (untested here):

```yaml
apiVersion: examples.namespace-operator.io/v1
kind: Team
metadata:
  name: team-a
spec:
  owner: Alice
  resourceQuotas:
    pods: "50"
    storage: "300Gi"
```

When deciding how much of Kubernetes to expose to application and ML developers after onboarding, *Production Kubernetes* (Chapter 16) organizes developer interfaces along a **4-stage spectrum of abstraction** (from least abstracted on the left to fully invisible Kubernetes on the right):

1. **Stage 1 — Command-line tooling and local UIs (no API abstraction)**: developers use raw `kubectl` augmented by shell helpers (`kubectx` for switching contexts, `kubens` for switching namespaces, log-tailing plugins, SSO credential plugins) and workstation graphical clients such as `Octant` and `Lens` that render cluster state using the developer's local `kubeconfig`. Full flexibility, but requires RBAC, admission guardrails, and Kubernetes knowledge from every developer.
2. **Stage 2 — Abstraction through templating (`Helm` and `Kustomize`)**: platform engineers package the roughly ten underlying objects a typical service needs (`Deployment`, `StatefulSet`, `Service`, `PVC`, `ConfigMap`, `Secret`) into a `Helm` chart exposing a small `Values.yaml` interface, optionally piped into `Kustomize` (or a web UI generator such as Ambassador's K8s Initializer) to patch fields the chart did not template. Developers still apply native Kubernetes objects, preserving upstream community documentation and debugging familiarity.
3. **Stage 3 — Abstracting Kubernetes primitives with custom workload CRDs (`PinterestService`)**: the platform team defines a high-level Custom Resource and operator that encapsulates multiple native resources and external integrations (such as internal DNS registration). In the book's example from Pinterest (`PinterestService`, untested here), a 25-line custom resource replaces more than 350 lines of raw `Deployment`, `Service`, `Ingress`, IAM role, and sidecar YAML:

```yaml
apiVersion: pinterest.com/v1
kind: PinterestService
metadata:
  name: exampleservice
  project: exampleproject
  namespace: default
spec:
  iamrole: role1
  loadbalancer:
    port: 8080
  replicas: 3
  sidecarconfig:
    sidecar1:
      deps:
        - example.dep
    sidecar2:
      log_level: info
  template:
    spec:
      initcontainers:
        - name: init
          image: gcr.io/kuar-demo/kuard-amd64:1
      containers:
        - name: init
          image: gcr.io/kuar-demo/kuard-amd64:1
```

   When building custom workload CRDs, the book recommends keeping a **break-glass** window into the underlying native objects (`Pod`s, `PVC`s, events) so engineers can still use standard Kubernetes troubleshooting knowledge when an abstraction leaks.
4. **Stage 4 — Making Kubernetes invisible (full PaaS / developer portals)**: developers push source code or a minimal build/deploy/release file without writing Kubernetes YAML at all, using platforms ported to or built atop Kubernetes such as Cloud Foundry, Google App Engine, Red Hat OpenShift, Spotify's `Backstage` developer portal, or HashiCorp `Waypoint` (which encapsulates `build` with `pack`, `deploy` to `kubernetes`, and `release` in a single HCL file).

## 5. Platform services around the cluster

A "platform" is more than Kubernetes: these shared services turn raw GPUs into a usable AI platform. Each has tenancy implications.

| Service | Purpose | Tenancy/ops notes |
|---|---|---|
| **Identity & access** (OIDC, SSO, groups) | Authenticate humans and machines | Group sync from IdP; short tokens; machine identities |
| **Container registry & artifact repos** | Images, Helm charts, models, Python packages | Per-team projects/robot accounts, quotas, scanning, replication, pull-through caches (5.1) |
| **CI/CD & GitOps** | Build, test, deploy | Runners isolated per team (ephemeral, rootless), OIDC to cloud, Argo/Flux projects (4.2, 4.26) |
| **Ingress/Gateway & API gateway** | Expose services, auth, rate limits | Per-tenant hostnames/routes, quotas, WAF (5.12) |
| **Job queueing & scheduling** | Kueue/Volcano/Slurm bridge | Fair-share, preemption, visibility (5.18) |
| **Notebooks & IDEs** | Interactive development | Time-limited, culling idle, sandboxing, egress controls |
| **Pipelines/orchestration** | Airflow, Argo Workflows, Kubeflow Pipelines, Flyte, Metaflow | Per-team namespaces/executors; separate controller privileges |
| **Experiment tracking & registries** | MLflow, W&B, ClearML, model registry | Access control per project; artifact store buckets per team; DB sizing |
| **Feature stores / vector DBs / datastores** | Feast, Redis, Postgres, Qdrant, Milvus | Per-tenant instances vs shared with RBAC; backups |
| **Storage platform** | Parallel FS, object store, NFS | Quotas, ACLs, encryption, lifecycle (5.17, Part 13) |
| **Model serving** | KServe, vLLM/Triton, Ray Serve, gateways | Per-tenant endpoints, autoscaling, GPU pools, tokens/rate limits (Part 15) |
| **Observability** | Metrics, logs, traces, GPU telemetry, cost | Multi-tenant backends (Mimir/Loki/Tempo tenants), RBAC on dashboards (5.24) |
| **Security tooling** | Policy engines, scanners, runtime detection, secret manager, audit | Central policies, tenant exceptions via PR (5.21, 5.27) |
| **Data governance** | Catalog, lineage, retention, PII controls | Dataset access approval workflows |
| **Cost management** | OpenCost/Kubecost, GPU accounting | Showback dashboards, budgets, alerts |
| **Support & docs** | Runbooks, FAQ, office hours, status page | Platform as a product |

### Operating the platform as a product

- **Customers**: researchers, ML engineers, application teams; gather requirements, publish a roadmap, SLAs/SLOs (queue wait, start latency, availability), changelog, deprecation policy.
- **Golden paths**: documented, supported ways to do common tasks (train, fine-tune, serve, batch infer) with templates; discourage snowflakes but allow escape hatches.
- **Guardrails over gates**: automated policy and quotas instead of manual approvals; fast feedback in PRs.
- **Metrics**: onboarding time, support tickets per tenant, GPU utilisation and allocation efficiency, job success rate, queue wait p95, incident count, time to resolve, user satisfaction.
- **Fairness and governance**: transparent quota allocation process (annual/quarterly), burst/borrowing rules, priority policy, preemption notices, reserved capacity for critical teams, review forums.
- **Capacity planning** with tenants: demand forecasting, utilisation reviews, reclaim idle quotas, charge or show costs.
- **Communication**: maintenance calendars, incident comms, release notes, deprecation notices with migration help.

## 6. Cost allocation and showback

Labels propagate from namespaces to pods (via policy) so cost tools can attribute spend: **OpenCost/Kubecost** (CPU/memory/GPU/storage/network by namespace/label), cloud billing exports with resource labels (GCP labels, AWS tags), DCGM-based GPU-hour accounting (per pod via pod-resources mapping and `DCGM_FI_DEV_*` joins). Allocation methods: by requests (what you reserved), by usage (what you used), or hybrid with idle-cost distribution; for GPUs, allocation by requested GPU-hours is usually fair and encourages release of idle resources, with utilisation reports to coach teams. Include shared costs (control plane, storage, networking, platform team) proportionally. Report weekly to team leads; alert on budget thresholds; automate idle detection (GPU allocated but under 5% utilised for hours) with notifications and auto-culling of notebooks.

PromQL examples:

```promql
sum by (namespace) (kube_pod_container_resource_requests{resource="nvidia_com_gpu"} * on (pod,namespace) group_left() (kube_pod_status_phase{phase="Running"} == 1))   # GPUs allocated per namespace
avg by (namespace) (DCGM_FI_DEV_GPU_UTIL * on (pod,namespace) group_left() kube_pod_info) / 100                                                                      # utilisation per namespace (join via exported pod/namespace labels)
sum by (namespace) (increase(container_cpu_usage_seconds_total[24h])) / 3600                                                                                          # CPU-hours/day
```

## 7. Failure modes and troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Tenant can see/affect others | Missing default-deny, cluster-wide Role bindings, shared service accounts | Review RBAC, NetworkPolicy, `kubectl auth can-i` as tenant, remove broad bindings |
| One team starves GPUs | No quotas/queues; priority inflation | Kueue ClusterQueues, ResourceQuota, PriorityClass-scoped quotas |
| API server slow due to one tenant | Controller/list loops, object floods | APF level per tenant/controller, `count/*` quotas, rate limits |
| Quota exceeded unexpectedly | Pending pods and failed Jobs counted; terminated pods retained | Clean up completed pods (TTL), inspect `kubectl describe quota`, scope quotas |
| Noisy neighbour on node | No CPU/memory isolation, shared NVMe/NIC | Guaranteed QoS, dedicated pools, I/O limits, bandwidth manager |
| Storage cross-tenant visibility | Shared RWX export without per-tenant paths | Per-tenant subpaths/exports, quotas, ACLs, CSI `subPathExpr` |
| Cannot onboard quickly | Manual steps | Automate tenant objects as code; templates |
| Idle GPUs allocated | Notebooks left running, jobs stuck | Idle culling, TTLs, alerts, quotas/borrow limits |
| Cost disputes | Unlabelled workloads | Enforce labels with admission; allocation reports |
| vCluster pods violate host policy | Syncer creates pods with tenant-chosen specs | Host-level PSA/Kyverno on synced pods, node selectors for tenant pools |
| Operator upgrades break tenants | Cluster-wide CRDs shared | Version per tenant via vCluster or strict CRD upgrade policy and compatibility testing |

## 8. Lab (untested)

1. **Namespace baseline**: build a tenant template (namespace, labels, RBAC for an OIDC group, ResourceQuota/LimitRange, default-deny + DNS NetworkPolicy, PSA labels, StorageClass access) as Helm/Kustomize; instantiate for two teams; verify isolation with cross-tenant access tests (pod-to-pod, secrets, PVCs).
2. **Quota behaviour**: exceed each quota type (pods, GPUs via fake extended resource, storage, object counts); read errors; test quota with Pending and completed pods; apply PriorityClass scoped quotas.
3. **Kueue sharing**: two teams, one cohort; borrow, reclaim, and preempt; WorkloadPriorityClasses; measure fairness over time with a synthetic workload generator; expose queue metrics.
4. **GPU sharing**: on a GPU node (or simulate), configure MIG profiles and time-slicing via the GPU Operator; run tenants' workloads on each; compare isolation (latency under interference, memory limits, fault containment).
5. **Delegated admin**: install Capsule (or HNC); create a Tenant with owners and limits; let an owner self-create namespaces; demonstrate guardrails (allowed storage classes/registries); compare with plain namespaces + Kyverno.
6. **Virtual cluster**: create a vCluster for a team, install a CRD/operator inside it that conflicts with the host's version; show isolation; apply host policies to synced pods; measure overhead.
7. **Node isolation**: dedicate a node pool with taints and automatic toleration/nodeSelector injection via policy; try to bypass as a tenant; add a sandbox RuntimeClass pool for notebooks.
8. **Onboarding automation**: implement the YAML tenant spec → GitOps pipeline → all objects; time it; run offboarding (data retention, namespace deletion with finalizers).
9. **Self-service**: provide a CLI/portal template for job submission that injects labels, queue, priority, resource defaults and secrets references; validate with policy.
10. **Cost allocation**: install OpenCost; label namespaces; produce a per-team GPU-hour report and an idle GPU report; set budget alerts.
11. **Attack drills**: from a tenant account try privilege escalation (create privileged pod, hostPath, read other namespace secrets, list nodes, `nodes/proxy`), scanning the network, exhausting object counts; verify controls hold; document gaps.
12. **Platform product review**: define SLOs, build a dashboard (queue wait p95, job success, utilisation, onboarding time), write the tenant guide.
13. **Clean up**.

Mark tested only after execution.

## 9. Common mistakes

- Assuming namespaces alone provide isolation; skipping network policy, quotas, PSA, node isolation or runtime sandboxing where trust requires it.
- Giving tenants cluster-scoped permissions (CRDs, webhooks, nodes) that affect others; sharing one ServiceAccount or cloud identity across teams.
- Static ResourceQuotas only, with no queueing/borrowing (low utilisation, long waits) or no quotas at all (starvation).
- Time-slicing GPUs between untrusted tenants.
- Manual onboarding; snowflake namespaces; unlabelled workloads (no cost attribution).
- Overusing virtual clusters where simple namespaces suffice, or cluster-per-tenant without fleet automation.
- Ignoring API server protection (APF, object count quotas); one tenant's operator overwhelming control plane.
- Treating the platform as infrastructure rather than a product: no docs, no support model, no SLOs.
- No offboarding discipline; orphaned volumes and credentials.

## 10. Interview angles

- "How do you design multi-tenancy on a shared GPU Kubernetes cluster? What isolation layers?" 
- "Soft vs hard multi-tenancy; when virtual clusters; when a cluster per tenant?" 
- "How do you share GPUs fairly across teams? Kueue, quotas, preemption, MIG, time-slicing: trade-offs." 
- "How do you stop one tenant from DoSing the API server or the storage?" 
- "How would you onboard a new team in 10 minutes?" 
- "How do you attribute GPU cost to teams?" 
- "What platform services does an AI platform need beyond Kubernetes?" 
- "How do you provide self-service while keeping guardrails?" 

## 11. Checkpoint questions (35)

1. Namespace isolation strength? **A:** Soft (shared kernel/control plane).
2. Hard multi-tenancy options? **A:** Cluster per tenant, sandboxed runtimes + node isolation.
3. ResourceQuota prefix for GPUs? **A:** `requests.nvidia.com/gpu`.
4. What does LimitRange do? **A:** Defaults and min/max per container/PVC.
5. `count/*` quotas for? **A:** Protect API from object floods.
6. Kueue cohort purpose? **A:** Share/borrow quota among queues.
7. PriorityClass-scoped quota purpose? **A:** Cap high-priority usage per team.
8. MIG isolation? **A:** Hardware partition with dedicated resources.
9. Time-slicing isolation? **A:** None.
10. MPS suitable for? **A:** Single-tenant concurrent processes.
11. vGPU needs? **A:** Hypervisor and licences.
12. Node isolation mechanism? **A:** Taints/labels/dedicated pools.
13. Sandboxed runtime examples? **A:** gVisor, Kata.
14. HNC does? **A:** Hierarchical namespaces with propagation.
15. Capsule does? **A:** Tenant abstraction over namespaces.
16. vCluster does? **A:** Virtual control plane in a namespace.
17. Virtual cluster still shares? **A:** Host nodes/scheduler.
18. Tenant onboarding as code tools? **A:** GitOps/Terraform/Kyverno generate.
19. What are the four stages on *Production Kubernetes*'s spectrum of platform abstractions, and what does the `Team` CRD operator pattern automate? **A:** (1) CLI helpers/local UIs (`kubectl`, `kubectx`, `kubens`, `Octant`, `Lens`), (2) templating (`Helm`, `Kustomize`), (3) custom workload CRDs (`PinterestService`), and (4) invisible-Kubernetes PaaS/portals (`Backstage`, `Waypoint`); the `Team` operator reconciles a tenant's `Namespace`, RBAC, and `ResourceQuota`s from a single `Team` CR.
20. Registry multi-tenancy feature? **A:** Projects/robot accounts/quotas.
21. Notebook controls? **A:** Culling, time limits, egress policy.
22. Storage tenancy control? **A:** Per-tenant paths/quotas/ACLs.
23. Observability tenancy? **A:** Tenants in Mimir/Loki, Grafana RBAC.
24. Cost tools? **A:** OpenCost/Kubecost.
25. Allocation methods? **A:** Requests, usage, hybrid.
26. Idle GPU detection? **A:** Allocated but low DCGM utilisation.
27. Platform as product means? **A:** Customers, SLOs, docs, roadmap.
28. Golden path? **A:** Supported default workflow with templates.
29. APF per tenant helps? **A:** Prevents control-plane starvation.
30. RDMA tenant isolation? **A:** Fabric-level (VLAN/VRF/PKey).
31. Offboarding steps? **A:** Revoke, retain/backup, delete, reclaim.
32. Exposing LoadBalancer in tenant ns? **A:** Restrict by policy/quota.
33. Shared CRDs risk? **A:** Version conflicts affect all tenants.
34. Tenant secrets approach? **A:** Namespaced + external store per tenant.
35. Quota exceeded error source? **A:** Admission (ResourceQuota).

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Josh Rosso, Rich Lander, Alex Brand and John Harris, *Production Kubernetes* (`production-kubernetes`, chapters 11 on building platform services, 12 on multitenancy, and Chapter 16: `16. Platform Abstractions` — read in full for the 4-stage spectrum of abstraction, `Team` onboarding CRD, `PinterestService` custom workload CRD, and `Backstage`/`Waypoint`).
- Brendan Burns et al., *Kubernetes: Up and Running* (3rd edition; chapters on namespaces, quotas and role-based access).
- The author's `nvidia-devops` repository, volume 03 (multi-tenant RBAC, Kyverno guardrails, platform engineering sections).
- Kubernetes multi-tenancy documentation, Kueue, Capsule, HNC, vCluster, OpenCost documentation, NVIDIA GPU Operator (MIG/time-slicing) documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** project maintenance status (HNC), Kueue API versions, MIG/time-slicing/MPS configuration details per GPU generation, PromQL metric/label names in your exporters, and every manifest/command; all labs are **untested**.
