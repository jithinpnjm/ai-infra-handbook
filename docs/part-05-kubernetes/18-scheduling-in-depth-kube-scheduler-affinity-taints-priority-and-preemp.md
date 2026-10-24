---
id: "c05-18"
title: "5.18 Scheduling in depth: kube-scheduler, affinity, taints, priority and preemption"
sidebar_label: "5.18 Scheduling in depth: kube-scheduler, affinity, taints, priority and preemption"
sidebar_position: 18
description: "How Kubernetes places pods: the scheduling framework (queues, filter/score, bind), node and pod affinity, taints and tolerations, topology spread, priority and preemption, resource fit and extended resources, topology/NUMA awareness, gang scheduling and queueing (Kueue, Volcano), DRA, scheduler tuning and scale, and GPU-cluster scheduling patterns with troubleshooting"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 5.18 Scheduling in depth: kube-scheduler, affinity, taints, priority and preemption

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | kind/kubeadm with 4+ nodes; labels/taints; Kueue, Volcano or scheduler-plugins for gang/queueing; `kwok` for simulated nodes at scale |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

GPUs are scarce, expensive and topologically structured; the scheduler decides where each pod goes, and bad decisions cost real money. A default scheduler that places eight 8-GPU training pods one at a time can strand seven of them waiting for the eighth (deadlock), spread a latency-sensitive inference service onto the same failing node, fragment a cluster so that no node has 8 free GPUs even though 40 are free, let background jobs hold GPUs that production inference needs, or put two GPUs of one pod across NUMA nodes and halve their bandwidth. Doing this well requires understanding the built-in scheduler's mechanics (filters, scores, affinity, taints, priority, preemption), where it falls short for batch/gang workloads, and how queueing systems (Kueue, Volcano) and device allocation (device plugins, DRA) complete the picture.

## Prerequisites and outcomes

Needs 5.3, 5.7, 5.9. After this chapter you can:

- Describe the scheduling cycle (queues, PreFilter/Filter/PostFilter/Score/Reserve/Permit/Bind) and what the scheduler does and does not know.
- Use `nodeSelector`, node affinity, pod affinity/anti-affinity, `topologySpreadConstraints`, taints/tolerations, and `nodeName`; choose the right one and write correct manifests; understand required vs preferred, `IgnoredDuringExecution`, and AND/OR semantics.
- Use PriorityClasses, preemption policies, and PodDisruptionBudgets; explain victim selection and why preemption can cascade; design priority tiers for training/inference/interactive/system.
- Explain resource accounting (requests, extended resources, overhead, allocatable), bin-packing vs spreading strategies (`NodeResourcesFit` scoring strategies), and fragmentation.
- Describe gang scheduling and queueing: why pod-by-pod scheduling fails for distributed jobs; Kueue (admission control, ResourceFlavors, ClusterQueues, LocalQueues, cohorts, preemption, fair sharing), Volcano (PodGroup, queues, actions/plugins), coscheduling plugin, JobSet; Slurm integration notions.
- Reason about topology: NUMA/Topology Manager, NodeResourceTopology (NFD) scheduling, rack/rail/NVLink-domain awareness via labels, DRA and structured parameters.
- Tune and scale the scheduler (parallelism, percentageOfNodesToScore, profiles, plugins, multiple schedulers) and debug Pending pods and unexpected placements.

## 1. The scheduler's job and model

The scheduler watches Pods with no `spec.nodeName`, picks a node per pod, and writes a binding. It reasons over the API's view: Node `allocatable`, existing pods' requests, labels, taints, volumes, and policies. It does **not** observe actual utilisation (unless a plugin is added), network proximity (beyond labels), or GPU health (beyond what device plugins/labels/taints expose). It schedules **one pod at a time** (with a snapshot of the cluster) and is not aware of job-level groups unless a plugin provides it.

```mermaid
flowchart LR
  subgraph Queues["Scheduling queue"]
    AQ["activeQ (heap by priority/QueueSort)"]
    BQ["backoffQ (recently failed, exponential backoff)"]
    UQ["unschedulablePods (waiting for a cluster event that could help)"]
  end
  API["API server: new/updated Pods, Nodes, PVs, ..."] --> AQ
  AQ --> SC["Scheduling cycle (serial per pod)"]
  SC --> PF["PreFilter → Filter (nodes, parallel) → PostFilter (preemption if none fit)"]
  PF --> PS["PreScore → Score (parallel) → NormalizeScore → select best"]
  PS --> RS["Reserve → Permit (approve/deny/wait)"]
  RS --> BC["Binding cycle (async): PreBind → Bind → PostBind"]
  BC --> API2["Binding written (spec.nodeName)"]
  SC -. "no node fits" .-> UQ
  UQ -. "relevant event (node added, pod deleted, ...)" .-> AQ
```

Details:

- **Queues**: pods sorted by `QueueSort` (default: priority, then arrival time). Failing pods go to the **unschedulable** pool with the plugins that rejected them; they are retried when an event they care about happens (node added/changed, pod deleted, PVC bound...) or after `podMaxInUnschedulablePodsDuration` (5 min); backoff increases to a maximum (default 10 s).
- **Filter** removes nodes that can't run the pod: `NodeResourcesFit` (requests vs allocatable minus assigned), `NodePorts`, `NodeAffinity`/`NodeSelector`, `TaintToleration`, `InterPodAffinity` (hard rules), `PodTopologySpread` (hard), `VolumeBinding`/`VolumeZone`/`VolumeRestrictions`/`NodeVolumeLimits`, `NodeUnschedulable` (cordon), `NodeName`, `DynamicResources` (DRA), plus custom plugins. Only a fraction of nodes may be examined in big clusters (`percentageOfNodesToScore`).
- **PostFilter** runs when no node passes: default plugin `DefaultPreemption` tries to free room by evicting lower-priority pods (section 5).
- **Score** ranks feasible nodes 0 to 100 with weights: `NodeResourcesFit` (strategy `LeastAllocated` default, `MostAllocated` for bin-packing, `RequestedToCapacityRatio` custom curves), `NodeResourcesBalancedAllocation`, `ImageLocality` (nodes that already have the image), `InterPodAffinity` (preferred), `NodeAffinity` (preferred), `TaintToleration` (prefer fewer intolerable PreferNoSchedule taints), `PodTopologySpread` (soft), `VolumeBinding`. Highest total wins; ties are broken randomly.
- **Reserve** assumes the placement in the scheduler cache (so the next pod sees it); **Permit** can hold the pod "waiting" (coscheduling/gang plugins wait here until the group can all be placed, then release); **Bind** writes the Binding (or lets a plugin bind) asynchronously; failures roll back via `Unreserve`.
- **Scheduler configuration**: `KubeSchedulerConfiguration` with **profiles** (named schedulers, each with plugin sets/weights/args, selected by `pod.spec.schedulerName`), `percentageOfNodesToScore`, `parallelism`, leader election, extenders (webhooks, deprecated in favour of plugins). Example: a `gpu-binpack` profile using `MostAllocated` to fill nodes before opening new ones, and a `default-scheduler` profile spreading.

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
percentageOfNodesToScore: 50
parallelism: 16
profiles:
  - schedulerName: default-scheduler
  - schedulerName: gpu-binpack
    pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
            resources:
              - { name: nvidia.com/gpu, weight: 5 }
              - { name: cpu, weight: 1 }
              - { name: memory, weight: 1 }
    plugins:
      score:
        disabled: [ { name: NodeResourcesBalancedAllocation } ]
```

Pods choose with `schedulerName: gpu-binpack`. Running multiple schedulers (or profiles) that manage overlapping nodes without coordination causes races; profiles inside one scheduler share its cache and avoid that.

## 2. Resource fit and accounting

- **Requests, not usage**: the scheduler sums `requests` of pods already assigned (including those still starting) and compares to `allocatable` (5.9). Limits are ignored for fit (except when requests default to limits). Pods with no requests (BestEffort) consume 0 for fit, which can overload nodes (use `LimitRange` defaults).
- **Extended resources** (`nvidia.com/gpu`, `rdma/*`, hugepages): integers advertised by device plugins in `status.capacity/allocatable`; requested in `limits` (and requests equal limits). GPU counting is by number, not identity: the scheduler knows "node has 8 free" but not which GPUs; the **kubelet device manager** picks specific devices (with `GetPreferredAllocation` hints for NVLink-aware choices). Fractional GPUs only exist via MIG/time-slicing/MPS advertised as separate resource names (`nvidia.com/mig-1g.10gb`) or DRA.
- **Init container and sidecar math**: effective pod request = max(largest init container, sum of app containers) (+ sidecar contributions), plus RuntimeClass overhead.
- **Pod overhead**, **ephemeral storage**, **PVC attach limits per node** are also filters.
- **Fragmentation**: a cluster with 64 GPUs free spread as 4 per node cannot run an 8-GPU pod. Mitigations: bin-packing profile (`MostAllocated`) for GPU nodes, node pools of homogeneous sizes, scheduling large jobs first (priority), reserving whole nodes for multi-GPU jobs via taints/labels, defragmentation by preemption/consolidation (descheduler), and gang/queue systems that admit big jobs when capacity exists.

## 3. Placement constraints

### nodeSelector and node affinity

```yaml
spec:
  nodeSelector:
    nvidia.com/gpu.product: NVIDIA-H100-80GB-HBM3        # simple equality (AND of all pairs)
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:      # hard rule (filter)
        nodeSelectorTerms:                                  # terms are OR'd
          - matchExpressions:                               # expressions within a term are AND'd
              - { key: topology.kubernetes.io/zone, operator: In, values: [us-central1-a, us-central1-b] }
              - { key: node.kubernetes.io/instance-type, operator: NotIn, values: [a3-edgegpu-8g] }
      preferredDuringSchedulingIgnoredDuringExecution:     # soft rule (score)
        - weight: 80
          preference:
            matchExpressions: [ { key: example.com/nvlink-domain, operator: In, values: [domain-3] } ]
```

Operators: `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`. "IgnoredDuringExecution" means running pods are not evicted if node labels change. Labels come from kubelet (zone, region, hostname, os, arch, instance-type), cloud providers, NFD (CPU flags, PCI devices), GPU Feature Discovery (`nvidia.com/gpu.product`, `.count`, `.memory`, `nvidia.com/mig.capable`), and your own platform labels (rack, rail, NVLink domain/clique, pool, tenant, lifecycle).

### Pod affinity and anti-affinity

Attract/repel pods relative to other pods' **topology domains** (`topologyKey` = a node label; `kubernetes.io/hostname` = same node, `topology.kubernetes.io/zone` = same zone, rack label = same rack).

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector: { matchLabels: { app: vllm } }
        topologyKey: kubernetes.io/hostname              # at most one vllm pod per node
  podAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 50
        podAffinityTerm:
          labelSelector: { matchLabels: { app: embedding-cache } }
          topologyKey: topology.example.com/rack         # prefer same rack as the cache
```

Costs: pod (anti-)affinity is computationally expensive (O(pods × nodes) per cycle); avoid cluster-wide `required` anti-affinity at thousands of nodes; prefer `topologySpreadConstraints` for spreading. `namespaceSelector` and `matchLabelKeys`/`mismatchLabelKeys` (newer) refine the target set.

### Topology spread constraints

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule                     # or ScheduleAnyway (soft)
    labelSelector: { matchLabels: { app: vllm } }
    matchLabelKeys: [pod-template-hash]                  # skew computed per ReplicaSet revision
    minDomains: 3
```

`maxSkew` bounds the difference in matching-pod counts between the most and least populated domains. Use for HA spreading across zones/nodes/racks; combine `hostname` + `zone` constraints. `nodeAffinityPolicy`/`nodeTaintsPolicy` control whether non-matching nodes count as domains.

### Taints and tolerations

A **taint** on a node (`key=value:effect`) repels pods that do not **tolerate** it: effects `NoSchedule` (new pods not scheduled), `PreferNoSchedule` (soft), `NoExecute` (also evicts running pods unless tolerated, optionally for `tolerationSeconds`).

```bash
kubectl taint nodes gpu-node-1 nvidia.com/gpu=present:NoSchedule
kubectl taint nodes gpu-node-1 nvidia.com/gpu=present:NoSchedule-            # remove
kubectl taint nodes gpu-node-2 maintenance=true:NoExecute
```

```yaml
tolerations:
  - { key: nvidia.com/gpu, operator: Exists, effect: NoSchedule }
  - { key: node.kubernetes.io/unreachable, operator: Exists, effect: NoExecute, tolerationSeconds: 60 }   # faster failover than default 300
```

System taints applied automatically: `node.kubernetes.io/not-ready`, `unreachable`, `memory-pressure`, `disk-pressure`, `pid-pressure`, `network-unavailable`, `unschedulable` (cordon), cloud `uninitialized`. Patterns: **dedicated GPU pools** (taint + node label; workloads need toleration *and* nodeSelector/affinity, since a toleration only permits placement), **per-tenant pools** (taint `tenant=a`), **spot/preemptible pools** (taint and tolerate only workloads that checkpoint), **reserved system nodes**. Admission plugins like `ExtendedResourceToleration` can auto-add tolerations for pods requesting `nvidia.com/gpu` when nodes are tainted by that key (convenient: users need not add tolerations).

### Other fields

`nodeName` bypasses the scheduler (no checks!), `schedulerName`, `priorityClassName`, `runtimeClassName`, `hostPort` conflicts, `resourceClaims`, `schedulingGates` (hold a pod from scheduling until a controller removes gates: used by Kueue/queueing and capacity controllers), `readinessGates`, `topologySpreadConstraints`, `affinity`. Cordon: `kubectl cordon` sets `spec.unschedulable` (tainted `unschedulable`); `drain` cordons + evicts respecting PDBs.

## 4. Priority, preemption and disruption

### PriorityClass

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata: { name: inference-critical }
value: 1000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority            # or Never
description: "Production serving; may preempt training"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata: { name: training-low }
value: 1000
preemptionPolicy: Never                            # waits in queue; never evicts others
```

- Priority is an integer; larger = more important. System classes: `system-cluster-critical` (2000000000) and `system-node-critical` (2000001000) are reserved for core components. User values should stay well below. `globalDefault: true` for at most one class sets the default priority for pods without a class (default 0 if none).
- Priority orders the **scheduling queue**, decides **preemption** victims, and influences **node-pressure eviction** order (after QoS/over-request, 5.9).
- **Preemption** (PostFilter): when a high-priority pod fits nowhere, the scheduler simulates removing lower-priority pods on candidate nodes (respecting PodDisruptionBudgets on a best-effort basis and graceful termination), selects the candidate node minimising victims (fewest PDB violations, lowest highest-victim-priority, fewest victims, latest start time), sets `status.nominatedNodeName`, deletes victims (with their grace periods), and the preemptor schedules once resources free (other pods may take the room meanwhile). `preemptionPolicy: Never` pods are placed ahead in the queue but never evict.
- Pitfalls: preemption cascades (victims get rescheduled and preempt others); evicting a multi-pod training job by killing one pod wastes the entire job's progress (the rest idle until the operator restarts all) — so give training pods non-preemptible, higher or equal priority within their tier, or use queue-level preemption (Kueue preempts whole workloads, checkpoint-aware), and ensure workloads handle SIGTERM with checkpointing; priority inversion if low-priority pods hold resources needed by high-priority pods that cannot preempt due to PDBs or affinity; abuse of `system-*` classes (restricted by ResourceQuota scopes `PriorityClass`); high-priority pods can starve others forever.
- **PodDisruptionBudget** protects availability from *voluntary* disruption (drains, autoscaler, preemption best-effort): `minAvailable`/`maxUnavailable`, `unhealthyPodEvictionPolicy`. For single-replica jobs a PDB `maxUnavailable: 0` blocks node drains (5.19); prefer Job-level resilience.
- **Suggested tiers for AI platforms**: `system-*` (infra), `inference-prod` (high), `training-high/normal` (non-preempting among themselves, quota-controlled), `interactive-notebook` (medium, with time limits), `training-best-effort/spot` (low, preemptible, checkpoints often). Pair with Kueue preemption policies (section 6) so the queue system, not raw kube preemption, resolves contention among batch jobs.

## 5. Why default scheduling fails for distributed jobs

A distributed training job of N pods needs all N running to make progress. The default scheduler places pods independently: if only N−1 fit, N−1 pods start and **hold their GPUs idle** waiting for the last; another job may do the same; both stall in deadlock (resource hold-and-wait). Also, partial placement ignores locality (pods spread across racks/IB leaf domains).

Required capabilities: **all-or-nothing admission** (gang), **queueing with fairness/quotas** across teams, **preemption at job granularity**, **topology awareness** (same rack/NVLink domain/leaf), **backfilling** (small jobs fill gaps), **elasticity**, and **checkpoint-aware** disruption. Kubernetes provides building blocks; add-ons provide the policy.

### Kueue

Kueue (SIG Scheduling) is a **job queueing and quota controller** that sits in front of kube-scheduler: it controls *when* a workload's pods may be created/run; kube-scheduler still places pods. Objects:

| Object | Purpose |
|---|---|
| `ResourceFlavor` | A variant of resources (GPU model/pool/spot vs on-demand), mapped to node labels/taints/tolerations injected into admitted workloads |
| `ClusterQueue` | Cluster-scoped quota per flavor (`nominalQuota`, `borrowingLimit`, `lendingLimit`), queueing strategy (`StrictFIFO`/`BestEffortFIFO`), cohort membership, preemption policy, namespace selector, admission checks |
| `LocalQueue` | Namespaced entry point that points to a ClusterQueue; users label jobs `kueue.x-k8s.io/queue-name` |
| `Cohort` | Group of ClusterQueues that can borrow unused quota from each other (fair sharing, hierarchical cohorts) |
| `Workload` | Kueue's internal representation of a job (resource requests, priority); admitted/evicted by Kueue |
| `WorkloadPriorityClass` | Priority for queueing decisions independent of pod priority |
| `AdmissionCheck` | Gate admission on external conditions (e.g., ProvisioningRequest to a cluster autoscaler for atomic capacity, MultiKueue for multi-cluster dispatch) |

Supported job types: batch/v1 Job, JobSet, MPIJob, PyTorchJob/TFJob (Kubeflow Training Operator), RayJob/RayCluster, plain Pods and groups, Deployments/StatefulSets (newer), AppWrapper; frameworks integrate by suspending (`spec.suspend: true`) the job until admitted, then unsuspending with injected node selectors (flavor). Pods of a job are created only after quota is reserved, avoiding partial starts; for all-or-nothing readiness, `waitForPodsReady` can evict workloads whose pods don't become ready in time.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: h100-ondemand }
spec:
  nodeLabels: { nvidia.com/gpu.product: NVIDIA-H100-80GB-HBM3, pool: h100-ondemand }
  tolerations: [ { key: nvidia.com/gpu, operator: Exists, effect: NoSchedule } ]
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: research }
spec:
  cohort: gpu-fleet
  namespaceSelector: { matchLabels: { team: research } }
  queueingStrategy: BestEffortFIFO
  preemption:
    reclaimWithinCohort: Any                 # take back lent quota from borrowers
    borrowWithinCohort: { policy: LowerPriority, maxPriorityThreshold: 100 }
    withinClusterQueue: LowerPriority
  resourceGroups:
    - coveredResources: [cpu, memory, nvidia.com/gpu]
      flavors:
        - name: h100-ondemand
          resources:
            - { name: cpu,            nominalQuota: 1024 }
            - { name: memory,         nominalQuota: 8Ti }
            - { name: nvidia.com/gpu, nominalQuota: 128, borrowingLimit: 64, lendingLimit: 32 }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata: { name: research-gpu, namespace: research-ns }
spec: { clusterQueue: research }
---
apiVersion: batch/v1
kind: Job
metadata:
  name: pretrain-llama
  namespace: research-ns
  labels: { kueue.x-k8s.io/queue-name: research-gpu, kueue.x-k8s.io/priority-class: training-normal }
spec:
  suspend: true
  parallelism: 8
  completions: 8
  # template with 8-GPU pods ...
```

Kueue also offers **topology-aware scheduling (TAS)** (placing a workload's pods in the best-fitting topology level such as block/rack using node labels), fair sharing with weights, partial admission, elastic jobs, dynamic resource requests, and MultiKueue for federation (5.35).

### Volcano

A batch scheduler (CNCF) with its own scheduler binary and CRDs: `Queue` (weight, capability, reclaimable), `PodGroup` (minMember, minResources → gang), `Job` (vcjob with tasks, lifecycle policies), plugins/actions (`enqueue`, `allocate`, `preempt`, `reclaim`, `backfill`) with plugins (`gang`, `priority`, `drf` fairness, `proportion`, `binpack`, `nodeorder`, `predicates`, `task-topology`, `numa-aware`, network-topology-aware via HyperNode). Pods set `schedulerName: volcano` and a PodGroup. Compared with Kueue: Volcano replaces kube-scheduler for batch pods (richer batch-specific policy in one place, more intrusive), Kueue complements the default scheduler (lighter integration with standard Jobs and operators). Often chosen: Kueue for new platform builds; Volcano where its HPC-style policies or existing deployments are established.

### Other gang mechanisms

- **Coscheduling plugin** (scheduler-plugins project): `PodGroup` CRD and a Permit plugin that holds pods until `minMember` can be placed; same scheduler, additional plugins (also `CapacityScheduling` elastic quotas, `NodeResourceTopologyMatch`, `Trimaran` load-aware scoring, `NetworkAware` scheduling).
- **JobSet** (Kubernetes SIG Apps/Batch): API for groups of Jobs with success/failure policies, startup order, and DNS (headless Service) — the base for multi-slice/multi-host training; integrates with Kueue.
- **Kubeflow Training Operator / MPI Operator v2 / KubeRay** use PodGroup/Kueue integration for gang semantics.
- **Native gang scheduling** work in Kubernetes (Workload API, PodGroup concepts in recent releases) is emerging; check release notes before adopting external solutions.
- **Slurm on Kubernetes** (SchedMD/Slinky, SUNK on CoreWeave, Soperator on Nebius): run Slurm as the batch scheduler with Kubernetes managing the nodes; useful for HPC teams (Part 6).

## 6. Topology-aware and device-aware scheduling

- **Why**: GPU↔GPU bandwidth depends on NVLink domain, GPU↔NIC on PCIe/NUMA proximity, node↔node on rail/leaf/spine hops; mis-placement reduces NCCL bandwidth substantially (Part 12).
- **Kubelet side**: Topology Manager aligns CPU/memory/devices on a NUMA node at admission (5.9); but the scheduler isn't aware, so pods may be scheduled and then rejected (`TopologyAffinityError`) — use **NodeResourceTopology** (NFD topology updater exports per-NUMA allocatable via `NodeResourceTopology` CRDs) with the scheduler-plugins `NodeResourceTopologyMatch` plugin, or DRA.
- **Fabric side**: label nodes with `topology.example.com/block`, `/rack`, `/leaf`, `/nvlink-domain` (or use cloud-provided `topology.kubernetes.io/*` and `cloud.google.com/gce-topology-block/subblock/host` labels); use required node affinity or topology spread/pod affinity with those keys for job pods; Kueue TAS and Volcano network-topology plugins automate "fit this job within the lowest topology level that has capacity". For multi-node NVLink systems (NVL72) the domain is a rack-scale unit: schedule whole-domain jobs onto one domain and respect IMEX/NVLink partition boundaries (Part 9, 12).
- **DRA (Dynamic Resource Allocation)**: devices are described in `ResourceSlice`s published by drivers (attributes like product, memory, MIG profile, PCI root, NVLink domain), pods reference `ResourceClaim`/`ResourceClaimTemplate`s with CEL selectors and constraints (e.g., "4 GPUs on the same PCIe root", "GPU and NIC aligned"); the scheduler's `DynamicResources` plugin allocates during scheduling, so placement is topology-aware without kubelet rejections; supports sharing claims, admin access, prioritized alternatives, partitionable devices (MIG), and consumable capacity (newer features). NVIDIA's DRA driver provides `gpu.nvidia.com` and (for multi-node NVLink) `compute-domain` device classes. Migration path: device plugin and DRA can coexist per resource; verify your Kubernetes and driver versions (Part 11).

```yaml
apiVersion: resource.k8s.io/v1
kind: ResourceClaimTemplate
metadata: { name: four-gpus-same-root }
spec:
  spec:
    devices:
      requests:
        - name: gpu
          exactly:
            deviceClassName: gpu.nvidia.com
            count: 4
            selectors:
              - cel: { expression: "device.attributes['gpu.nvidia.com'].productName == 'NVIDIA H100 80GB HBM3'" }
      constraints:
        - requests: [gpu]
          matchAttribute: "resource.kubernetes.io/pcieRoot"
```

(Attribute names and API versions differ by driver and Kubernetes release; verify.)

## 7. Descheduling, autoscaling and scheduler tuning

- **Descheduler**: periodically evicts pods to improve placement (remove duplicates, balance utilisation, violate-affinity fixes, node-taint cleanup, low node utilisation consolidation); use with PDBs and on non-training pods only.
- **Cluster autoscaler / Karpenter** react to Pending pods by adding nodes (and removing underused ones): GPU node scale-up takes minutes and capacity is not guaranteed; combine with Kueue ProvisioningRequest for atomic multi-node provisioning (5.23).
- **Scale tuning** (1,000+ nodes): `percentageOfNodesToScore` (default adaptive 50% down to 5%; lower speeds up large clusters, fewer candidates), `parallelism`, minimising expensive plugins (inter-pod affinity), scheduler QPS/burst for the client, high-availability with leader election, avoiding webhook latency on pod creation, `unschedulable` queue behaviour; metrics: `scheduler_pending_pods{queue}`, `scheduler_schedule_attempts_total{result}`, `scheduler_e2e_scheduling_duration_seconds`, `scheduler_scheduling_attempt_duration_seconds`, `scheduler_plugin_execution_duration_seconds`, `scheduler_preemption_attempts_total`, `scheduler_queue_incoming_pods_total`. Typical default throughput hundreds of pods/second in small clusters, tens to ~100 pods/s with complex constraints; a 10,000-pod job creation burst takes minutes — gang jobs should be created suspended and admitted by Kueue so pods arrive in controlled bursts.
- **Image locality** scoring helps large GPU images (pods prefer nodes with the image); pre-pull DaemonSets reduce skew.
- **Node pools** (labels + taints) simplify scheduling rules and autoscaling; avoid gigantic heterogeneous pools.

## 8. Debugging scheduling

```bash
kubectl get pod p -o wide; kubectl describe pod p | sed -n '/Events/,$p'
# FailedScheduling: 0/20 nodes are available: 8 Insufficient nvidia.com/gpu, 6 node(s) had untolerated taint {nvidia.com/gpu: present}, 6 node(s) didn't match Pod's node affinity/selector. preemption: 0/20 nodes are available: ...
kubectl get nodes -L nvidia.com/gpu.product,topology.kubernetes.io/zone
kubectl describe node n | sed -n '/Allocated resources/,/Events/p'               # requests vs allocatable
kubectl get pods -A -o wide --field-selector spec.nodeName=n                       # what is on the node
kubectl get events -A --field-selector reason=FailedScheduling --sort-by=.lastTimestamp
kubectl logs -n kube-system -l component=kube-scheduler --tail=200                 # -v=4 for filter/score traces
kubectl get --raw /metrics | grep -E '^scheduler_(pending_pods|schedule_attempts_total|preemption)'
kubectl get workloads -A; kubectl describe workload <w> -n ns                       # Kueue admission state & reasons
kubectl get clusterqueue research -o yaml | yq '.status'                            # usage, pending, admitted
kubectl get resourceclaims,resourceslices -A                                         # DRA
kubectl get priorityclass; kubectl get pdb -A
kubectl get --raw "/api/v1/nodes/n/proxy/configz" | jq '.kubeletconfig.topologyManagerPolicy'
```

| Symptom | Likely cause | Fix |
|---|---|---|
| `Insufficient nvidia.com/gpu` but GPUs free | GPUs used by non-listed pods (e.g., terminating, in other namespaces), device plugin not updated, fragmentation, node cordoned | `describe node` allocated; check plugin; defrag; uncordon |
| `didn't match Pod's node affinity/selector` | Labels missing (GFD not running), typos | Check labels, NFD/GFD DaemonSets |
| `untolerated taint` | Missing toleration | Add toleration/enable ExtendedResourceToleration |
| `didn't satisfy existing pods anti-affinity rules` / `topology spread constraints` | Too strict required rules | Relax to preferred, add capacity/domains, adjust `maxSkew` |
| `volume node affinity conflict` | PV zone differs from schedulable nodes | `WaitForFirstConsumer`, same-zone capacity (5.17) |
| `pod has unbound immediate PersistentVolumeClaims` | PVC pending | Fix storage class/provisioner |
| Pending forever with Kueue | Not admitted: quota, flavor mismatch, wrong queue label, `suspend` | `describe workload`, ClusterQueue status |
| Pods scheduled then `TopologyAffinityError` | Kubelet topology policy rejects | Align policy/NUMA-aware scheduling/DRA |
| Training job partially running | No gang control | Use Kueue/Volcano/PodGroup |
| Preempted unexpectedly | Higher-priority pod needed room | Review PriorityClasses, `preemptionPolicy`, PDB; use Kueue to decide |
| Hot node, empty neighbours | `LeastAllocated` vs requests not reflecting usage; node affinity pull | Scoring strategy, spread constraints, descheduler, load-aware scoring |
| Scheduling slow at scale | Heavy plugins (inter-pod affinity), API latency, single scheduler throughput | Reduce affinity, tune percentage, check API (5.5), batch admission |
| DRA claim pending | No matching ResourceSlice/device attributes, driver not running | `get resourceslices`, driver pods, CEL expression |

## 9. Reference patterns for a GPU platform

1. **Pools**: `gpu-h100-training` (tainted, labelled, homogeneous 8-GPU nodes), `gpu-l4-inference`, `cpu-system`, `spot-experimental`; workloads select via labels and Kueue ResourceFlavors rather than users writing node selectors.
2. **Admission**: all batch jobs go through Kueue LocalQueues; ClusterQueues per team with nominal quotas, cohort borrowing and preemption policies; inference runs as Deployments with high PriorityClass and its own reserved pool (or a ClusterQueue with reservation).
3. **Placement**: `MostAllocated` (bin-pack) for GPU pools so whole nodes remain free for large jobs; topology constraints for training; `topologySpreadConstraints` across zones/racks for inference replicas.
4. **Resilience**: PDBs for inference; checkpoint-aware training with SIGTERM handling and `terminationGracePeriodSeconds`; node health taints from NPD/DCGM-based remediation (Part 17) so unhealthy GPUs are excluded automatically.
5. **Visibility**: dashboards for pending reasons, queue wait time, GPU allocation vs utilisation (DCGM), fragmentation (largest placeable GPU block), preemption counts, admission latency, per-team usage versus quota.
6. **Governance**: ResourceQuota for objects and storage; LimitRange defaults; admission policy to require queue labels and priority classes from an allow-list; namespace-to-team mapping through GitOps (4.26).

## 10. Lab (untested)

1. **Predict placement**: create a 4-node kind cluster with labels (zone, rack, gpu type) and taints; write pods with various constraints; predict and verify placement; read scheduler logs at `-v=4`.
2. **Required vs preferred**: node affinity required with unsatisfiable terms (Pending + event) vs preferred (placed); show OR-of-terms vs AND-of-expressions with a truth table of manifests.
3. **Taints**: dedicate a pool with `NoSchedule`; show that tolerations don't force placement; add `nodeSelector`; use `NoExecute` with `tolerationSeconds` and watch eviction; enable `ExtendedResourceToleration` behaviour.
4. **Spread vs anti-affinity**: deploy 6 replicas with `topologySpreadConstraints` (hostname + zone) and compare to required pod anti-affinity (hits capacity limit); measure scheduling latency of both on a 500-node KWOK cluster.
5. **Bin-packing vs spreading**: configure a second profile with `MostAllocated`; schedule 40 small GPU-like pods (fake extended resource `example.com/gpu`) under each profile and compare per-node utilisation and the largest remaining free block.
6. **Fragmentation incident**: fill nodes with 1-GPU pods under spreading; submit an 8-GPU pod (Pending despite many free GPUs); fix by bin-packing, preemption, or descheduler; record steps.
7. **Priority and preemption**: create low/high PriorityClasses; saturate the cluster with low-priority pods; create a high-priority pod; observe victim selection, `nominatedNodeName`, events; test `preemptionPolicy: Never` and PDB interaction.
8. **Gang deadlock**: submit two 4-pod "jobs" each needing 4 of 6 available slots with default scheduling to reproduce deadlock; fix with Kueue (suspended Jobs, ClusterQueue quota) or coscheduling PodGroup; verify all-or-nothing.
9. **Kueue fair sharing**: two teams with ClusterQueues in one cohort; team A borrows idle quota; team B submits and reclaims via preemption; observe `Workload` conditions and metrics; add WorkloadPriorityClass.
10. **Volcano (optional)**: install Volcano; run a vcjob with `minAvailable`; compare behaviours and policies with Kueue.
11. **Topology**: label nodes with racks; implement required-affinity placement for a job; try Kueue TAS if available; measure a synthetic network benchmark (iperf) intra- vs inter-rack to quantify.
12. **DRA (if your cluster supports)**: install the example DRA driver or NVIDIA's; create a ResourceClaimTemplate with CEL and constraints; observe allocation and scheduling decisions in events.
13. **Scale**: use KWOK to simulate 2,000 nodes; create 20,000 pods; capture scheduler metrics; tune `percentageOfNodesToScore`, `parallelism`; identify bottlenecks.
14. **Dashboard**: build panels for pending pods by reason, queue wait time, GPU fragmentation, preemptions; define alerts.
15. **Clean up**.

Mark tested only after execution.

## 11. Common mistakes

- Expecting a toleration to attract pods (it only permits); forgetting node selectors/affinity for dedicated pools.
- Using required pod anti-affinity at large scale (slow, brittle); misusing `topologyKey`.
- Running distributed jobs without gang/queue control; partial starts holding GPUs.
- Priority inflation (everything "critical"); preemption of single pods of multi-pod jobs; no checkpointing for preemptible work.
- PDBs that block all evictions; PDBs on single-replica workloads.
- Relying on `nodeName` or manual scheduling hacks.
- Ignoring fragmentation (spreading policy on GPU pools); mixing heterogeneous GPU types in one pool without labels/resource names.
- Assuming the scheduler sees GPU utilisation or health; leaving unhealthy GPUs schedulable.
- Running multiple schedulers/profiles over the same nodes without coordination.
- Kubelet topology policy stricter than scheduler awareness (pods rejected after binding).
- Misreading `FailedScheduling` messages (counts are per reason and may overlap).

## 12. Interview angles

- "How does kube-scheduler pick a node? Explain filters, scores, and the binding cycle." 
- "Taints vs node affinity; why do GPU pools need both?" 
- "Pod anti-affinity vs topology spread constraints." 
- "Explain priority and preemption; what can go wrong with training jobs?" 
- "Why is the default scheduler unsuitable for distributed training? How do Kueue and Volcano solve it?" 
- "How do you avoid GPU fragmentation?" 
- "How do you make scheduling topology-aware (NUMA, NVLink, rack)? What is DRA?" 
- "A pod is Pending with 'Insufficient nvidia.com/gpu' but monitoring shows idle GPUs. Why?" 

## 13. Checkpoint questions (40)

1. Scheduler input? **A:** Pods without nodeName.
2. Scheduler output? **A:** Binding setting `spec.nodeName`.
3. Filter vs score? **A:** Eliminate infeasible nodes vs rank feasible ones.
4. PostFilter default plugin? **A:** DefaultPreemption.
5. Permit used for? **A:** Delay/approve binding (gang).
6. Where do unschedulable pods wait? **A:** unschedulable pool until events.
7. Default fit strategy? **A:** LeastAllocated.
8. Bin-packing strategy? **A:** MostAllocated.
9. Does scheduler use limits? **A:** No, requests.
10. Does scheduler see utilisation? **A:** No (by default).
11. GPU resource name? **A:** `nvidia.com/gpu`.
12. Who picks specific GPUs? **A:** Kubelet device manager/plugin.
13. nodeSelector semantics? **A:** AND of equality pairs.
14. nodeSelectorTerms semantics? **A:** OR of terms, AND within.
15. `IgnoredDuringExecution`? **A:** Running pods not evicted on label change.
16. topologyKey meaning? **A:** Node label defining a domain.
17. Anti-affinity cost? **A:** Expensive at scale.
18. `maxSkew` meaning? **A:** Max pod-count difference between domains.
19. `whenUnsatisfiable` options? **A:** DoNotSchedule, ScheduleAnyway.
20. Taint effects? **A:** NoSchedule, PreferNoSchedule, NoExecute.
21. Does a toleration schedule pods there? **A:** No, only allows.
22. `tolerationSeconds` use? **A:** Grace before NoExecute eviction.
23. System-critical priority classes? **A:** `system-cluster-critical`, `system-node-critical`.
24. `preemptionPolicy: Never` effect? **A:** Pod doesn't evict others.
25. Victim selection criteria? **A:** Fewest PDB violations, lowest priority, fewest victims.
26. `nominatedNodeName` meaning? **A:** Node reserved for a preemptor.
27. PDB applies to? **A:** Voluntary disruptions.
28. Gang scheduling means? **A:** All-or-nothing placement.
29. Deadlock cause? **A:** Partial allocation holding resources.
30. Kueue vs kube-scheduler? **A:** Admission/quota vs placement.
31. Kueue objects? **A:** ResourceFlavor, ClusterQueue, LocalQueue, Workload.
32. How Kueue holds jobs? **A:** `suspend: true` until admitted.
33. Cohort purpose? **A:** Borrow/lend quota between queues.
34. Volcano key CRDs? **A:** Queue, PodGroup, Job.
35. Coscheduling plugin gate? **A:** Permit with PodGroup minMember.
36. JobSet is? **A:** API for groups of Jobs with policies.
37. Topology Manager scheduling gap? **A:** Scheduler unaware, kubelet rejects.
38. NodeResourceTopology provides? **A:** Per-NUMA allocatable to scheduler plugins.
39. DRA objects? **A:** ResourceClaim, ResourceClaimTemplate, ResourceSlice, DeviceClass.
40. Descheduler does? **A:** Evicts pods to improve placement.

## 14. Sources and review notes

**Written in original words.** Principal sources:

- Brendan Burns et al., *Kubernetes: Up and Running* (3rd edition; scheduler and scheduling-related material in chapters on pods, labels and cluster operations).
- The author's `nvidia-devops` repository, volume 03 (control plane and scheduling masterclass: scheduling framework, preemption and priority classes, topology and NUMA alignment, gang scheduling with Kueue/Volcano, Dynamic Resource Allocation).
- Kubernetes documentation (scheduling framework, assigning pods to nodes, taints and tolerations, pod priority and preemption, topology spread, DRA), Kueue, Volcano and scheduler-plugins project documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** scheduling feature status by Kubernetes release (DRA API version and fields, `matchLabelKeys`, `minDomains`, scheduling gates, native gang/Workload APIs, queue behaviour changes), Kueue API versions and TAS/MultiKueue maturity, Volcano API groups, default percentages and timings, and every manifest; all labs are **untested**.
