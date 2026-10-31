---
id: "c11-18"
title: "11.18 KAI operations and troubleshooting"
sidebar_label: "11.18 KAI operations and troubleshooting"
sidebar_position: 18
description: "Operating, monitoring, and troubleshooting NVIDIA KAI Scheduler and shared GPU clusters across hardware, MIG/time-slicing state, registration, scheduling policy, runtime binding, and service SLOs."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 11.18 KAI operations and troubleshooting

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE (plus local Python 3 simulation lab) |
| Part | Part 11: GPUs on Kubernetes, scheduling and virtualization |
| Sources used | Roland Huß et al., *Generative AI on Kubernetes* (O'Reilly, 2026, Ch. 7); `nvidia-zero-to-hero/volume-11/chapter-10-observability-and-slos-for-shared-gpus.md`; `nvidia-zero-to-hero/volume-11/chapter-11-production-troubleshooting.md`; `nvidia-zero-to-hero/volume-11/labs/lab-04-troubleshoot-a-multi-tenant-gpu-node.md`; `nvidia-zero-to-hero/volume-19/chapter-02-incident-response-and-game-day-execution.md` |
| Coverage file | `planning/coverage/chapters/11-18.md` |

## Why this matters for AI infrastructure

A developer submits a single-GPU Pod to a dedicated cluster, and it stays pending. On that cluster the troubleshooting has only two branches. Either the cluster is out of GPUs, or a worker node is broken. Running NVIDIA KAI Scheduler on a shared, multi-tenant cluster changes that picture. You now manage hierarchical Queue quotas, PodGroup gang scheduling, BindRequest reservation Pods, hardware MIG partitions, and software Time-Slicing or fractional GPUs. Each of these adds its own place to fail, so the failure surface spreads across six distinct layers.

The failures show up at different layers depending on where the workload is. A Pod that asks for a MIG profile or a fractional GPU share can stay pending for several reasons. A hardware XID fault sits at the first layer. MIG mode disabled on the host sits at the second, and a crashed device plugin sits at the third. At the fourth layer, the request can be blocked by a namespace ResourceQuota admission denial, a missing PodGroup, an exhausted Queue limit, or MIG slice fragmentation.

A Pod that is already running can still fail its users. The Binder microservice can stall while it waits for a fractional GPU reservation Pod, and that is the fifth layer. At the sixth layer, a noisy neighbor on a shared, time-sliced pool can push GPU memory past ninety percent. That contention drives tail latency beyond the service level objective, while the physical hardware health graphs stay green.

Guessing is the costly habit here. An on-call responder who restarts the device plugin or reboots a host on a hunch destroys the forensic timeline. Worse, that restart widens the blast radius to every co-tenant on the server. The rest of this chapter gives you a disciplined six-layer triage order, a shared-GPU telemetry contract, step-by-step incident playbooks, and chaos engineering Game Days.

The summary below collects the thresholds and rules that the rest of the chapter depends on. Treat it as the reference you come back to when a page fires. Notice that the stale-telemetry rule is written as UNKNOWN, never as healthy.

```text
Shared-GPU & KAI Scheduler Operational Thresholds Summary (volume-11 & volume-19)
---------------------------------------------------------------------------------
- Triage Architecture: 6 ordered layers, 7 KAI microservices, 6 KAI CRDs
- Reserved MIG Inference Tier:
    * Request success SLI target: > 99.5% (5m rate window)
    * Latency p99 SLI target:     < 100 ms (breach alert if > 120 ms, warning 100-120 ms)
- Best-Effort Time-Sliced / Fractional Pool:
    * Queue wait p95 SLI target:  < 30 seconds (10m rate window; breach >= 30 s)
    * Memory pressure threshold:  > 90% sustained (> 95% host contention trigger)
- Platform Foundation & Telemetry Freshness:
    * DCGM scrape age alert:      > 120 seconds -> mark state UNKNOWN (never healthy)
    * Recovery verification wait: 30 s after device-plugin restart; 5 min after pool patch
- AI Game Day Chaos Engineering:
    * Fault injections:           XID 48 (Double-Bit ECC), ibportstate ... disable (RDMA)
    * Availability target:        99.999% ("Five Nines") with < 5 seconds failover
    * Schedule discipline:        10:00 AM on a Tuesday instead of 3:00 AM on a Sunday
```

Use this summary to decide whether a symptom is a real breach or a gap in your telemetry. If the numbers look healthy but the scrape age is above 120 seconds, the first job is to restore the data, not to trust the dashboard.

## Prerequisites and outcomes

### Prerequisites

- You should have finished Chapters 11.13 through 11.17. They cover KAI Scheduler architecture, custom resources, gang scheduling, fractional GPUs, Time-Slicing, and MIG.
- You should be comfortable with `kubectl`, `nvidia-smi`, Prometheus PromQL queries, and the DCGM exporter.

### Outcomes

- Walk the six-layer shared-GPU and KAI Scheduler triage order, from physical hardware up to service telemetry. Before you change any cluster state, capture a five-file read-only forensic bundle.
- Map any stuck or failing workload to the exact KAI Scheduler microservice and custom resource definition that owns it. The owner tells you where to look first.
- Implement the shared-GPU telemetry contract and the service-class Prometheus rules. A stale scrape target is marked unknown, never healthy.
- Run the safe policy fault injection lab to tell an API admission ResourceQuota denial apart from a scheduler capacity event. Then run AI Game Days for hardware faults, RDMA blackholes, and control-plane leader elections.

If any prerequisite is new to you, go back to Chapters 11.13 through 11.17 before you continue.

## Concepts: basics to intermediate to advanced

### 1. Basics: The six-layer triage model for KAI Scheduler and shared GPUs

Picture an incident on a KAI-scheduled cluster. The pager goes off, and the first instinct is to restart a DaemonSet or reboot a worker node. Resist that instinct. Responders must never start by restarting DaemonSets or rebooting worker nodes. First, freeze nonessential automated rollouts in the affected scope and keep one healthy peer node for comparison. Next, capture a read-only evidence bundle, then walk the six architectural boundaries from bottom to top.

```mermaid
flowchart TD
    Symptom["User Symptom: Pending Pod, Stuck BindRequest, or Latency Breach"] --> L1{"Layer 1: Hardware & Driver Healthy? (nvidia-smi -L / -q / dmesg)"}
    L1 -->|"No or Uncertain"| Act1["Cordon Node, Preserve Evidence, Run Host Hardware Runbook"]
    L1 -->|"Yes"| L2{"Layer 2: Sharing State Valid? (mig.mode.current / mig -lgi)"}
    L2 -->|"No"| Act2["Repair MIG Layout or Time-Slice Config via Controlled Drain"]
    L2 -->|"Yes"| L3{"Layer 3: Resource Registered? (Node Allocatable & Device Plugin)"}
    L3 -->|"No"| Act3["Inspect nvidia-device-plugin & kubelet Registration Logs"]
    L3 -->|"Yes"| L4{"Layer 4: Scheduling & Policy Valid? (Quota / PodGroup / Queue / MIG Geometry)"}
    L4 -->|"No"| Act4["Inspect ResourceQuota, pod-grouper, queue-controller & Fragmentation"]
    L4 -->|"Yes"| L5{"Layer 5: Runtime & KAI Binder Initialized? (BindRequest & Reservation Pod)"}
    L5 -->|"No"| Act5["Inspect kai-binder Logs, Reservation Pod & Container Toolkit CDI"]
    L5 -->|"Yes"| L6["Layer 6: Service Outcome & Telemetry Freshness (p99 SLO & DCGM <= 120s)"]
```

Follow the diagram from the symptom at the top. A "No" or "Uncertain" answer sends you to the action on that branch. Only a "Yes" moves you one layer up.

#### Mapping Layer 4 and Layer 5 failures to KAI Scheduler microservices and CRDs

Layers four and five are where KAI Scheduler splits its work. Seven specialized microservices and six Custom Resource Definitions share those duties. Once you know which microservice owns which object, you can isolate a control-plane stall in seconds.

| KAI Microservice | CRD / Object Owned | Failure Symptom When This Component Breaks | Exact Triage Command |
|---|---|---|---|
| **`operator`** | `Config`, `SchedulingShard` | KAI control-plane pods missing after upgrade or shard partition out of sync | `kubectl get config,schedulingshards -A` |
| **`admission`** | Validating / Mutating Webhooks | Pod submission rejected immediately or fractional GPU defaults not mutated | `kubectl get mutatingwebhookconfigurations,validatingwebhookconfigurations \| grep kai` |
| **`pod-grouper`** | `PodGroup` | Workload Pods (`PyTorchJob`, `JobSet`, `RayCluster`, `LWS`) sit `Pending` with **no `PodGroup` created** | `kubectl get podgroups -n <ns>` and `kubectl logs -n kai-scheduler deploy/pod-grouper` |
| **`queue-controller`** | `Queue` (`parent`, `resources.gpu.quota` / `limit`) | `PodGroup` exists, but `kubectl get queues` shows `allocated` stuck or `Queue` status unhealthy | `kubectl get queues -o wide` and `kubectl describe queue <team-queue>` |
| **`kai-scheduler`** | Stage 1–6 Session Decisions (`Topology`, `PodGroup`) | `PodGroup` stays `Pending` (`Unschedulable: Queue over limit`, `gang minMember not met`, or `Topology constraint unsatisfied`) | `kubectl describe podgroup <pg-name> -n <ns>` and `kubectl logs -n kai-scheduler deploy/kai-scheduler` |
| **`pod-group-controller`** | `PodGroup` lifecycle & status sync | `PodGroup` phase fails to update when member pods complete or fail | `kubectl logs -n kai-scheduler deploy/pod-group-controller` |
| **`binder`** | `BindRequest` & Fractional GPU Reservation Pods | `kai-scheduler` allocated the `PodGroup`, but member Pods remain `Pending` (or fractional pods wait for their integer `nvidia.com/gpu: 1` reservation pod) | `kubectl get bindrequests -n <ns>` and `kubectl logs -n kai-scheduler deploy/binder` |

Start with the row whose symptom matches what you see. Then run its triage command before you change anything in the cluster.

---

### 2. Intermediate: Observability, telemetry contracts, and service-class SLIs and SLOs

A shared GPU node can report perfectly healthy hardware while one tenant suffers unacceptable tail latency. The reverse happens too. A node can show low average utilization while it properly holds reserved MIG capacity for a latency-critical service. Observability on a KAI-scheduled platform has to answer two separate questions. First, can the platform foundation allocate and run work safely? Second, is each service class delivering the latency and throughput it promised its tenants?

#### Build three audience-specific views rather than a single GPU health score

A single dashboard that collects all cluster telemetry leaks data across teams. It also hides localized saturation behind fleet-wide averages. Platform teams should publish three distinct views instead, all governed by a six-part telemetry contract. That contract covers node coverage, identity anchored on node and GPU UUID, metric semantics, bounded label cardinality, retention history, and multi-tenant access control.

| Operational View | Primary Audience | Core Questions Answered | Permitted vs Prohibited Data (Multi-Tenant Safety) |
|---|---|---|---|
| **1. Platform Health** | SRE & Platform Operations | Are nodes, GPUs, drivers, MIG layouts, KAI operands, and `dcgm-exporter` scrape paths healthy and fresh (`<= 120 s`)? | Sees fleet/node UUIDs, XIDs, and operand state; must not ingest tenant prompts, secrets, or payload data. |
| **2. Service Delivery** | Tenant & Service Owner | Is our `Queue` wait time, allocation rate, and application `p99` latency / error rate meeting our service tier's promise? | Sees only the tenant's own `Queue`, `PodGroup`, quota, and app metrics; **never** sees competing tenants' names or host inventory. |
| **3. Capacity & Fairness** | Platform Product & Finance | Which `Queue` or MIG profile shape is blocked, fragmented, or holding idle reservations? | Sees aggregated `gpu-hours` by `Queue`, Pending reasons by shape, and MIG fragmentation; no per-request traces. |

The last column is the rule that matters most. Each view sees only what its audience needs. The service delivery view, for example, never sees competing tenants' names or host inventory.

#### Concrete service-class SLIs, SLOs, and Prometheus rules

Never attach a strict tail-latency target to a best-effort time-sliced pool. That pool's admission policy cannot enforce hardware isolation, so a strict target there would not be enforceable. Instead, match each service level indicator to the isolation the sharing mechanism actually gives. That covers reserved MIG inference, best-effort time-sliced development, and platform scrape freshness.

- For the reserved MIG inference tier, track request success rate and ninety-ninth percentile latency over five-minute rolling windows. Page on-call when latency breaches the upper threshold, or when Pods queue on missing MIG slices.
- For the best-effort time-sliced development pool, track ninety-fifth percentile queue wait time and physical GPU memory utilization. Those two metrics show operators when high notebook concurrency drives expected memory pressure.
- For platform foundation and telemetry freshness, track the advertised GPU and MIG resource counts alongside the age of the latest DCGM exporter scrape. Flag stale metrics as unknown rather than healthy.

The recording rules below turn those targets into Prometheus queries. Each comment line carries the target or the alert threshold.

```yaml
# Reserved MIG inference SLI/SLO recording rules (volume-11/chapter-10, untested here)
sli_mig_inference_request_success: |
  rate(inference_requests_total{service="mig-inference", status="success"}[5m])
  / rate(inference_requests_total{service="mig-inference"}[5m])
  # Target: > 99.5%

sli_mig_inference_p99_latency: |
  histogram_quantile(0.99, rate(inference_request_duration_ms_bucket[5m]))
  # Target: < 100ms; breach alert if > 120ms

mig_pod_pending_reasons: |
  count by (reason) (kube_pod_container_status_state{state="pending"})
```

```yaml
# Best-effort time-sliced pool & telemetry freshness rules (volume-11/chapter-10, untested here)
timeslice_queue_time_p95: |
  histogram_quantile(0.95, rate(gpu_queue_wait_seconds_bucket{pool="time-sliced"}[10m]))
  # Target: < 30 seconds

timeslice_memory_utilization: |
  nvidia_smi_memory_used_mib{gpu_index="0"}
  / nvidia_smi_memory_total_mib{gpu_index="0"}
  # > 90% sustained with high concurrency indicates expected memory contention

gpu_device_available: |
  count(nvidia_smi_memory_total_mib)

mig_resource_advertised: |
  count(kube_allocatable{resource=~"nvidia.com/mig.*"})

dcgm_exporter_scrape_age_seconds: |
  time() - scrape_timestamp_seconds{job="dcgm-exporter"}
  # Alert if > 120 seconds: stale telemetry means hardware health is UNKNOWN, never healthy
```

Read the comment next to each expression as the contract. A stale series means the state is unknown, not healthy.

#### The five actionable alert families

Every alert that pages an on-call engineer needs two things. It needs a safe first containment action, and it needs an explicit guardrail that says what not to do first. That guardrail is what stops a responder from turning a single-node registration glitch into a cluster-wide outage.

| Alert Family | Trigger Condition | Safe First Action | Do NOT Do First |
|---|---|---|---|
| **1. Resource-Loss Alert** | Expected `nvidia.com/gpu` or `nvidia.com/mig-*` count drops in `status.allocatable` | Cordon affected node(s) to stop new placement; diff against a healthy peer node | Do not reconfigure every node or delete device-plugin pods fleet-wide |
| **2. Hardware-Evidence Alert** | XID / uncorrectable ECC / thermal fault correlated with workload impact | Preserve `nvidia-smi -q` and `dmesg` evidence, isolate node, follow hardware runbook | Do not reboot the host before capturing volatile driver/XID state |
| **3. Telemetry-Freshness Alert** | `dcgm_exporter_scrape_age_seconds > 120` or missing target | Restore exporter/scrape path and mark hardware health as **`UNKNOWN`** | Do not treat absent or zeroed metrics as a healthy GPU |
| **4. Protected-Service SLO Alert** | Reserved inference `p99 > 120 ms` or success `<= 99.5%` | Reduce best-effort admission or route traffic to approved reserve capacity | Do not raise time-slicing `replicas` count to hide queueing |
| **5. Capacity-Risk Alert** | Compatible MIG profile or `Queue` reserve exhausted with rising `Pending` demand | Review requested profile shapes, `Queue` usage, and MIG fragmentation | Do not page on-call solely because average GPU utilization moved |

Each row pairs the first safe action with the move that makes things worse. Read the last column as carefully as the first.

---

### 3. Advanced: Production incident playbooks and AI Game Days

#### Playbook A: MIG resource disappears after host or operator event

A workload that asks for a hardware MIG slice stays pending. Before anyone restarts anything, you need to know where the break is. It could sit in the host driver, in the host MIG partition table, or in the Kubernetes device-plugin registration layer. Five read-only checks, run in order, isolate the fault without disturbing the Pods already running on the node.

- At layer one, query `mig.mode.current` on the host to confirm MIG mode is still enabled. An unscheduled host reboot or driver reset can wipe MIG mode back to disabled.
- At layer two, list the active GPU Instances on the host. This confirms the expected slices still exist in silicon, and you should do it before you touch any Kubernetes DaemonSet.
- At layer three, inspect the node's allocatable resource counts in the Kubernetes API. That reveals whether the control plane can see the host slices.
- At layer four, suppose the host slices exist at layer two but the node advertises zero allocatable slices at layer three. Delete only that node's device-plugin Pod, then wait thirty seconds for registration to recover.
- At layer five, compare the affected node's description with a healthy peer node. Never change MIG mode on a node that carries live Pods without cordoning and draining it first.

Here are the same five checks as commands. Each step's arrow line says what a healthy answer looks like.

```text
Playbook A: 5-Step Read-Only MIG Absence Commands (volume-11/chapter-11, untested here)
---------------------------------------------------------------------------------------
1. Layer 1 (Host GPU & MIG Mode):
   ssh gpu-node-1 'nvidia-smi -i 0 --query-gpu=gpu_name,gpu_uuid,mig.mode.current --format=csv'
   -> Verify "Enabled". If "Disabled", reboot/reset wiped MIG mode.

2. Layer 2 (Host MIG Instances):
   ssh gpu-node-1 'nvidia-smi mig -lgi -i 0'
   -> Verify 1g.10gb / 2g.20gb exist. If "No GPU Instances are currently running",
      reapply approved MIG profile after cordoning.

3. Layer 3 (Node Allocatable):
   kubectl get nodes -o custom-columns=NAME:.metadata.name,MIG_10GB:.status.allocatable.nvidia\.com/mig-1g\.10gb,MIG_20GB:.status.allocatable.nvidia\.com/mig-1g\.20gb
   -> Verify counts > 0.

4. Layer 4 (Device Plugin Logs & Targeted Restart):
   kubectl logs -n nvidia-driver-install ds/nvidia-device-plugin-daemonset --tail=50 | grep -i "device\|mig\|error"
   kubectl delete pod -n nvidia-driver-install -l app=nvidia-device-plugin
   -> Wait 30 s for status.allocatable to repopulate when Layer 2 is OK but Layer 3 is 0.

5. Layer 5 (Healthy Peer Diff):
   kubectl describe node gpu-node-1 vs gpu-node-2 (never change MIG mode without cordon & drain).
```

#### Playbook B: Proving policy admission denial versus scheduler capacity shortage

In a multi-tenant incident, a namespace that has simply hit its policy ceiling can look exactly like a broken GPU. Responders often confuse a namespace ResourceQuota admission denial with a missing hardware resource in the scheduler. Telling the two apart stops the team from hunting for broken GPUs that are fine.

- An API admission denial comes from a ResourceQuota. Suppose a namespace carries a zero GPU quota such as `diagnostic-gpu-denial`. The API server rejects the Pod manifest at once, before any Pod or PodGroup object is written to cluster storage. The node's allocatable capacity stays untouched.
- A scheduler capacity shortage or KAI Queue wait looks different. When API admission succeeds, the Pod and PodGroup objects are created in the pending phase. Describing the Pod or PodGroup then reveals a scheduling event, such as insufficient MIG slices or a Queue over its limit.

When a namespace hits its quota, look at the policy first, not at the GPUs.

#### Playbook C: AI chaos engineering and Game Days

Suppose an unscheduled outage hits early on a Sunday morning, and nobody has ever tested fault recovery. Configuration drift will have built up by then, and it can turn one failure into a total platform blackout. Hope is not a strategy for multi-tenant GPU clusters, so run Game Days on a schedule instead. Run them during normal business hours, using the Incident Command System. That system splits the work into three roles. The Incident Commander coordinates decisions and the timeline without touching a keyboard. The Subject Matter Expert inspects cluster and host diagnostics, and the Communications Lead updates stakeholders.

```mermaid
flowchart LR
    Plan["1. Hypothesis (< 5s failover for 99.999% API)"] --> Blast["2. Scoped Blast Radius (Staging / Canary)"]
    Blast --> Inject["3. AI Fault Injection (XID 48 / IB Port Disable / Master Power-Off)"]
    Inject --> Observe["4. Observe Alerts, DCGM, Checkpoints & Pod Stability"]
    Observe --> Fix["5. Postmortem & Architectural Fix (Tune Device Plugin Liveness Probes)"]
```

The flow runs left to right. It starts with a hypothesis, and it ends with a postmortem and a fix.

Every AI infrastructure platform should execute three mandatory Game Day fault injections. Together they test hardware isolation, RDMA network recovery, and control-plane resilience.

- Start with a simulated GPU hardware death. Inject a double-bit ECC error on an isolated test GPU using `dcgmi test --inject`. Verify that the device plugin marks the card unhealthy, evicts the affected Pod, and cordons the node automatically.
- Next, test an RDMA and InfiniBand network blackhole. Disable a single InfiniBand switch port using `ibportstate` while a multi-node job runs collective benchmarks. Remember that host `iptables` rules only filter kernel TCP/IP sockets. They never touch RDMA verbs traffic that bypasses the OS kernel.
- Last, test control-plane master failover and device-plugin liveness probes. Power off one of three control-plane master nodes during synthetic peak load. Verify that worker-node device plugins tolerate transient API server leader elections without restarting and unregistering extended GPU resources.

The postmortem below shows why the failover test matters. The hypothesis looked safe on paper, and the outcome was not.

```text
Game Day Postmortem: The 99.999% Control-Plane Master Failover Trap (volume-19/chapter-02)
------------------------------------------------------------------------------------------
- Hypothesis: Powering off 1 of 3 master nodes keeps Triton inference degradation < 5 seconds
  to meet a Five Nines (99.999%) availability target.
- Actual Outcome: 100% of running Triton inference pods on every worker node crashed instantly.
- Root Cause Chain:
  1. Worker-node nvidia-device-plugin and GPU Operator DaemonSets had overly aggressive
     liveness probes tied to kube-apiserver responsiveness.
  2. During the brief control-plane leader-election pause, the device-plugin liveness probes
     timed out and restarted the plugin containers.
  3. Restarting the plugin briefly unregistered nvidia.com/gpu (Allocatable dropped to 0),
     causing local kubelets to terminate all running Triton GPU pods.
- Why PodDisruptionBudget (PDB) Failed: PDBs only govern voluntary evictions via the Eviction API
  (kubectl drain); they do not stop kubelet from killing pods when a hardware resource vanishes.
- Architectural Fix: Increase liveness probe timeouts and failure thresholds in the GPU Operator
  and device-plugin Helm chart so control-plane blips never restart worker-node device plugins.
```

Read the root cause chain in order. The fix changes the device-plugin probe settings in the Helm chart, not the control plane.

#### Change-surface review, containment gates, and tabletop exercises

Most shared-GPU and KAI Scheduler incidents are interface regressions. A legitimate platform or workload change usually starts them. Examples include a kernel upgrade, a driver bump, a MIG layout update, a Queue quota change, or a new model release with a larger key-value cache footprint. Resist the urge to blame the latest commit or to roll back unrelated components. Compare the affected node against a preserved healthy peer across all six change surfaces instead.

| Change Surface | First Boundary Likely to Break | Authoritative Evidence to Compare | Unsafe Shortcut to Avoid |
|---|---|---|---|
| **1. Node OS Image, Kernel, or NVIDIA Driver** | Layer 1: Host initialization & GPU enumeration | `uname -r`, `nvidia-smi -q`, `dmesg` boot/XID log vs healthy peer node | Assuming a Kubernetes manifest rollback repairs broken host kernel/driver state |
| **2. Container Runtime (`containerd`) or Toolkit (`CDI`)** | Layer 3/5: Device injection & container initialization | `containerd` logs, `/etc/cdi`, RuntimeClass handler, bounded `diagnostic-gpu-pod` (`DIAGNOSTIC_GPU_OK`) | Modifying application Python code before testing a minimal `nvidia-smi -L` diagnostic pod |
| **3. Device Plugin, GPU Operator, or KAI Operands** | Layer 3/4: Resource advertisement & `PodGroup` / `BindRequest` reconciliation | Helm/ConfigMap revision, DaemonSet/Deployment logs, node `status.allocatable` | Deleting all operator and scheduler pods at once without identifying the first non-ready operand |
| **4. MIG Profile Policy / Layout (`mig-parted`)** | Layer 2/4: GPU Instance inventory & profile placement | Approved layout baseline, node drain record, `nvidia-smi mig -lgi`, `status.allocatable["nvidia.com/mig-*"]` | Reconfiguring MIG mode on an active node carrying live tenant pods without cordoning and draining |
| **5. `Queue` Quota, `ResourceQuota`, or Admission Policy** | Layer 4: API admission or KAI `Queue` scheduling | Git policy revision, `quota-denial.txt` admission error or `PodGroup` event, `kubectl get queues` | Bypassing namespace or `Queue` governance with privileged cluster-admin overrides |
| **6. Model Weights, Context Length, or Batch Release** | Layer 6: HBM footprint, `p99` latency, and OOM rate | Application baseline metrics, concurrency count, `nvidia-smi --query-processes` memory usage | Declaring a physical GPU hardware defect when a new model checkpoint grew past its slice ceiling |

Each row names the first boundary likely to break, the evidence to compare against the healthy peer, and the shortcut to avoid. Use the evidence column as your checklist.

#### Containment gates and service-specific acceptance workloads

An incident is not over just because a DaemonSet shows as running, or because `nvidia-smi` prints a table on the host. Every containment action has to pass a service-class recovery gate. A version-controlled validation workload verifies that gate before the node or pool goes back to production traffic.

- For a suspected host or hardware fault at layer one, cordon the node to stop new placements. Then verify that host diagnostics and DCGM health checks pass, that allocatable counts match the baseline, and that the bounded diagnostic Pod prints `DIAGNOSTIC_GPU_OK`.
- For MIG discovery or layout drift at layers two and three, pause automated rollout propagation across the node pool so healthy peer nodes stay untouched. Then verify that host MIG instances match the node's advertised `nvidia.com/mig-*` counts, and that a test Pod initializes CUDA cleanly.
- For a KAI scheduling, quota, or fragmentation block at layers four and five, route urgent work to a compatible reserve pool without stripping tenant isolation labels. Verify that PodGroup and BindRequest objects bind cleanly, and that the recovery check Pod completes `QUOTA_DENIAL_RECOVERY_CHECK`.
- For shared-pool contention or a protected SLO breach at layer six, reduce best-effort admission or patch the protected deployment onto a dedicated or MIG pool. Confirm that request latency and success rates hold within target across a full five-minute observation window.
- For a telemetry pipeline outage at layer six, label the affected dashboards and status updates as unknown due to stale telemetry, not as healthy. Verify that scrape age drops below the threshold, and that test allocations correlate across node, GPU UUID, and PodGroup.

Do not return a node to production until its gate has passed.

#### Running the tabletop exercise before production launch

Picture a canary node upgrade going wrong. A protected inference tenant requests a MIG profile that is temporarily exhausted in its primary pool. A neighboring best-effort time-sliced pool has free capacity, but the protected tenant cannot silently move onto it. Before you certify an on-call rotation for a shared KAI and MIG cluster, platform leaders should run this tabletop exercise. Incident commanders grade the team on six concrete behaviors.

- Classify before mutating. Decide whether the pending Pod is blocked by device discovery, quota policy, total capacity exhaustion, or MIG geometry fragmentation. Do this before you touch any worker node.
- Freeze the canary rollout. Halt the node upgrade at once, so the remaining healthy comparison nodes stay available for side-by-side diffs.
- Protect multi-tenant privacy. Tell the affected service owner what is happening without leaking competing tenants' names, model weights, or Queue allocations.
- Choose an approved mitigation. Route the workload to a compatible reserve MIG pool, or run a controlled maintenance drain. Never silently downgrade a protected service onto a best-effort time-sliced pool.
- Preserve the forensic scene. Capture the complete five-file read-only evidence bundle before you apply any cluster change.
- Verify with acceptance workloads. Confirm full recovery with both a bounded diagnostic Pod and the tenant's application-level tail-latency indicator.

Run the exercise before the rotation goes live, so that the first classification is practice.

## Commands and configurations that matter

### 1. Preserving the read-only scene bundle

Before you restart a component or drain a node, preserve the scene. Capture the five-file read-only evidence bundle first. The files record node state, Pod placement, cluster events, allocatable resources, and KAI Scheduler custom resources. Once they exist, you can compare the node's state before and after any change.

```bash
# Preserve node, pod, event, allocatable, and KAI state before any mutation (untested here)
export GPU_NODE="gpu-node-1"
export LAB_NAMESPACE="gpu-sharing-incident-lab"
export EVIDENCE_DIR="shared-gpu-incident"

mkdir -p "$EVIDENCE_DIR"
kubectl describe node "$GPU_NODE" > "$EVIDENCE_DIR/node-describe.txt"
kubectl get pods -A --field-selector spec.nodeName="$GPU_NODE" -o wide > "$EVIDENCE_DIR/node-pods.txt"
kubectl get events -A --sort-by=.lastTimestamp > "$EVIDENCE_DIR/events.txt"
kubectl get node "$GPU_NODE" -o jsonpath='{.status.capacity}{"\n"}{.status.allocatable}{"\n"}' > "$EVIDENCE_DIR/node-resources.txt"
kubectl get resourcequota,queues,podgroups,bindrequests -A > "$EVIDENCE_DIR/kai-and-quotas.txt"
```

Each command writes one file into `shared-gpu-incident`. Run them all before you apply any fix, so the evidence reflects the incident and not your repair.

### 2. Bounded diagnostic Pod and safe ResourceQuota fault injection

A bounded diagnostic Pod in a disposable namespace tests GPU access on a single node. Pair it with a reversible zero-capacity ResourceQuota to test API admission denial. Neither object touches production workloads, because the lab namespace is the only place they run.

```yaml
# diagnostic-gpu-pod-and-quota-test.yaml (volume-11/labs/lab-04, untested here)
apiVersion: v1
kind: Namespace
metadata:
  name: gpu-sharing-incident-lab
---
apiVersion: v1
kind: Pod
metadata:
  name: diagnostic-gpu-pod
  namespace: gpu-sharing-incident-lab
spec:
  restartPolicy: Never
  nodeSelector:
    kubernetes.io/hostname: gpu-node-1
  containers:
    - name: diagnostic
      image: nvcr.io/nvidia/cuda:12.4.1-base-ubuntu22.04
      command: ["sh", "-c", "nvidia-smi -L; echo DIAGNOSTIC_GPU_OK"]
      resources:
        limits:
          nvidia.com/gpu: 1
---
# Safe reversible policy fault injection in disposable lab namespace only
apiVersion: v1
kind: ResourceQuota
metadata:
  name: diagnostic-gpu-denial
  namespace: gpu-sharing-incident-lab
spec:
  hard:
    requests.nvidia.com/gpu: "0"
    limits.nvidia.com/gpu: "0"
```

The Pod runs `nvidia-smi -L` and then prints `DIAGNOSTIC_GPU_OK`. The ResourceQuota is the control. With a zero GPU limit, the API server refuses the Pod at admission, before the Pod exists.

### 3. Time-correlated host contention triage

When a shared node suffers latency spikes, capture timestamped host metrics. The timestamps let you line up GPU memory, clocks, power, and processes against the moment users complained. Record GPU memory utilization, Streaming Multiprocessor clocks, power draw, active container process identifiers, and host swap state.

```bash
# Capture timestamped host GPU memory, SM clock, power, and PID breakdown (untested here)
INCIDENT_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ssh gpu-node-1 'nvidia-smi --query-gpu=name,memory.used,memory.total,clocks.current.sm,power.draw --format=csv -l 2' | tee /tmp/gpu-activity.txt
ssh gpu-node-1 'nvidia-smi --query-processes=pid,process_name,gpu_memory_usage --format=csv'
ssh gpu-node-1 'cat /proc/meminfo | grep -E "MemTotal|MemAvailable|SwapFree"'
```

The `INCIDENT_TIME` variable records when the capture started, so keep it with the output.

## How it fails

When you run a KAI-scheduled shared GPU cluster, most operational failures fall into five patterns. The device plugin loses registration. Workload Pods have no PodGroup. A BindRequest gets stuck. Stale DCGM telemetry hides contention. And overly aggressive liveness probes restart the plugin during a control-plane blip. The table below pairs each pattern with the evidence you will see, the layer where it breaks, and the fix.

| Failure mode | Exact symptom & command evidence | Root cause boundary | Remediation |
|---|---|---|---|
| **1. `nvidia.com/mig-1g.10gb` disappears from `status.allocatable` while `nvidia-smi mig -lgi` still shows instances (`volume-11/chapter-11`)** | `ssh gpu-node-1 'nvidia-smi mig -lgi -i 0'` lists active `1g.10gb` instances, but `kubectl describe node gpu-node-1` shows `0` allocatable MIG resources and `ds/nvidia-device-plugin-daemonset` logs `"failed to discover"`. | **Layer 3 Registration (`nvidia-device-plugin`):** The host MIG layout (`Layer 2`) is intact, but the device-plugin pod on that node lost synchronization with NVML / `kubelet`. | Restart only the device-plugin pod (`kubectl delete pod -n nvidia-driver-install -l app=nvidia-device-plugin`), wait `30 s`, and verify `status.allocatable` without reconfiguring MIG or draining running workloads. |
| **2. Workload Pods stay `Pending` with `schedulerName: kai-scheduler` and zero `PodGroup` objects in namespace (*Generative AI on Kubernetes* chapter 7)** | `kubectl get pods -n team-a` shows Pods `Pending`, `kubectl get podgroups -n team-a` returns `No resources found`, and `kai-scheduler` logs show no scheduling attempts for those pods. | **Layer 4 Scheduling Policy (`kai-pod-grouper`):** Either the `pod-grouper` deployment is down/missing RBAC watches for the workload CRD, or the workload is missing its `kai.scheduler/queue` label. | Check `kubectl logs -n kai-scheduler deploy/pod-grouper`, verify the workload carries `kai.scheduler/queue: <queue>`, and confirm `pod-grouper` watches the parent CRD (`PyTorchJob`, `JobSet`, `LWS`). |
| **3. `PodGroup` is allocated by `kai-scheduler`, but fractional GPU pods remain `Pending` (`BindRequest` stuck)** | `kubectl get podgroups` shows the group scheduled, `kubectl get bindrequests -n team-a` shows a `BindRequest` object that never completes, and the integer GPU reservation pod on the target node is `Pending` or failing. | **Layer 5 Runtime / KAI Binding (`kai-binder`):** `binder` created an integer `nvidia.com/gpu: 1` reservation pod to back the fractional user pods, but `kubelet` or `nvidia-device-plugin` rejected the reservation pod on the target node. | Inspect `kubectl get bindrequests -n team-a -o yaml`, check `kubectl logs -n kai-scheduler deploy/binder`, and verify `status.allocatable["nvidia.com/gpu"]` and CDI runtime health on the target node. |
| **4. Reserved MIG or shared inference `p99` breaches `> 120 ms` while DCGM dashboards appear flat or healthy (`volume-11/chapter-10`)** | Users report timeouts (`p99 = 135 ms > 120 ms` breach), while Grafana GPU health panels show `0` errors—and `dcgm_exporter_scrape_age_seconds` is `180 s` (`> 120 s`). | **Layer 6 Service & Telemetry (`UNKNOWN_STALE_TELEMETRY` + Contention):** Stale scrape targets (`> 120 s`) created a false green hardware view while co-tenant memory pressure (`> 90%`) degraded tail latency. | Immediately route the protected service to dedicated/MIG capacity (`kubectl patch deployment ...`), restore `dcgm-exporter` scraping, and alert on `dcgm_exporter_scrape_age_seconds > 120`. |
| **5. Killing `1` of `3` master nodes in a Game Day crashes all running Triton GPU pods on worker nodes (`volume-19/chapter-02`)** | During a brief `kube-apiserver` leader-election pause, `nvidia-device-plugin` pods on worker nodes restart, `nvidia.com/gpu` briefly drops to `0`, and `kubelet` terminates all running GPU pods despite `PodDisruptionBudgets`. | **Aggressive Device-Plugin Liveness Probes:** Device-plugin liveness probes timed out against the API server pause and restarted; `PDBs` only block voluntary Eviction API calls, not `kubelet` resource-loss termination. | Increase liveness probe timeouts and failure thresholds in the GPU Operator / device-plugin Helm chart so transient control-plane blips never restart the device plugin. |

Read each row from left to right. The symptom is what you see, the root cause boundary is where the break sits, and the remediation is the narrowest fix you can apply. Try the narrowest one first.

## Hands-on lab

### Venue and scope

You run this lab on your own machine, and it needs only the Python standard library. The two scripts, `code/part11/kai_operations_and_troubleshooting.py` and `code/part11/kai_operations_and_troubleshooting_lab.py`, check the six-layer triage classifier. The checks cover hardware, MIG state, device-plugin registration, scheduling policy, Binder runtime, and service telemetry. The lab also tests the Prometheus service level objective evaluator and the AI Game Day fault models. The host and cluster commands earlier in the chapter are marked untested here, because this lab does not run them.

### Step 1: Run the self-checking KAI operations and troubleshooting lab (tested here)

From the repository root, run the verification script. It checks its own results and prints one line per check.

```bash
python3 code/part11/kai_operations_and_troubleshooting_lab.py
```

The captured output below comes from this repository. Each line should read PASS, and the summary should report zero failures.

```text
=== Chapter 11.18 Lab: KAI Operations, Observability, SLIs/SLOs & Troubleshooting ===
  [PASS] Volume 11 Ch 11 / Lab 04 defines 6 ordered triage layers from Hardware/driver to Service & Telemetry
  [PASS] Layer 2 inspects sharing state (mig.mode.current / mig -lgi) before Layer 3 node Allocatable
  [PASS] Layer 4 inspects scheduling policy (PodGroup, Queue quota, ResourceQuota) before Layer 5 Runtime
  [PASS] Reserved MIG inference with 99.8% (> 99.5%) success and p99=85ms (< 100ms) is HEALTHY_SLO_MET
  [PASS] Reserved MIG inference with p99=135ms (> 120ms breach threshold) triggers SLO_BREACH
  [PASS] Reserved MIG inference between 100ms and 120ms (110ms) enters SLO_WARNING_100_TO_120MS
  [PASS] Best-effort time-sliced pool with p95 queue wait 18s (< 30s) and 60% (<= 90%) memory is HEALTHY_BEST_EFFORT
  [PASS] Time-sliced pool at 95% (> 90%) memory utilization flags MEMORY_CONTENTION_GT_90PCT
  [PASS] Time-sliced pool with p95 queue wait 45s (>= 30s) flags QUEUE_WAIT_BREACH_GE_30S
  [PASS] DCGM scrape age 180s (> 120s) marks state as UNKNOWN_STALE_TELEMETRY rather than healthy
  [PASS] Missing host GPU enumeration classifies as Layer 1: Hardware/driver
  [PASS] MIG mode enabled with 0 GPU instances classifies as Layer 2: Sharing state
  [PASS] Host MIG instances present but node Allocatable=0 classifies as Layer 3: Registration (nvidia-device-plugin)
  [PASS] Lab 04 zero-capacity ResourceQuota denial classifies at API Admission before Pod creation
  [PASS] Missing PodGroup CR for a pending workload classifies as Layer 4: kai-pod-grouper
  [PASS] PodGroup blocked by Queue limit classifies as Layer 4: kai-queue-controller
  [PASS] Unused MIG slices that cannot form requested profile classify as Layer 4: MIG Fragmentation
  [PASS] Stuck BindRequest CR or reservation pod classifies as Layer 5: kai-binder
  [PASS] Running pod with p99=240ms (> 100ms SLO) on healthy GPU classifies as Layer 6: Workload Contention
  [PASS] Game Day XID 48 (Double-Bit ECC) is injected via dcgmi test --inject and marks GPU Unhealthy
  [PASS] RDMA network blackhole requires switch port disable (ibportstate ... disable) because iptables ignores RDMA
  [PASS] 5-Nines (99.999%) Game Day hypotheses target < 5 seconds failover degradation
  [PASS] Control-plane master failover exposed aggressive device-plugin liveness probes unregistering nvidia.com/gpu
  [PASS] PodDisruptionBudgets do not stop kubelet from terminating pods when extended GPU resources disappear
  [PASS] Stale telemetry (> 120s) attaches UNKNOWN warning to incident classification

Summary: 25 passed, 0 failed out of 25 checks.
```

The classifier checks Layer 2 before Layer 3, and Layer 4 before Layer 5. That is the same six-layer order you saw earlier in this chapter.

### Exercises

1. Open `SIX_TRIAGE_LAYERS` in `code/part11/kai_operations_and_troubleshooting.py`. List the six triage layers in order, and state the primary diagnostic evidence collected at each layer.
2. Use `classify_kai_and_shared_gpu_incident()` to compare two cases. In the first, `nvidia-smi mig -lgi` shows zero instances on the host. In the second, it shows active instances on the host while the node's allocatable MIG count is zero. Contrast the diagnosis and the safe remediation for each.
3. Three different blocks leave three different trails of Kubernetes evidence. Compare a Pod blocked by the `diagnostic-gpu-denial` ResourceQuota, a failure in PodGrouper to create a PodGroup, and a Binder stall on a BindRequest.
4. Inspect `evaluate_shared_gpu_slo()`. State the numerical thresholds for reserved MIG inference success and latency, time-sliced queue wait and memory utilization, and DCGM exporter scrape age.
5. State the exact tool or command used to inject a double-bit ECC error on a test GPU, and the command used to create an InfiniBand link failure during collective benchmarks. Then explain why host `iptables` rules cannot test an RDMA link failure.
6. Explain why powering off one of three master nodes caused all worker-node Triton Pods to terminate. Then say why PodDisruptionBudgets did not protect them, and name the Helm configuration change that fixes the flaw.

Exercises 1, 2 and 4 name the function or constant to read first. For the others, check your answer against the lab output above.

## Checkpoint questions

<details>
<summary>**1. List the six triage layers for a shared-GPU and KAI Scheduler incident in order from bottom to top.**</summary>

Start at the bottom with physical device, host, and driver enumeration. The second layer checks the active MIG mode or time-slicing shape on the host. The third layer checks device-plugin discovery and node allocatable registration. The fourth layer checks ResourceQuota, PodGroup, Queue, and MIG geometry policy. The fifth layer checks Binder reservation Pods and container CUDA initialization. The sixth and last layer verifies service latency targets and DCGM telemetry freshness.
</details>

<details>
<summary>**2. Before running any remediation command during a shared-GPU incident, what five read-only evidence files should you capture?**</summary>

You save the node description to `node-describe.txt`, the node's running Pods to `node-pods.txt`, and the sorted cluster events to `events.txt`. Then record the node's capacity and allocatable JSON in `node-resources.txt`. Finally, save all ResourceQuotas and KAI scheduling objects in `resourcequotas.txt` or `kai-and-quotas.txt`.
</details>

<details>
<summary>**3. Which seven microservices and six CRDs make up the NVIDIA KAI Scheduler operational footprint?**</summary>

Seven microservices make up the footprint: `operator`, `kai-scheduler`, `pod-grouper`, `binder`, `queue-controller`, `admission`, and `pod-group-controller`. The six Custom Resource Definitions are Config, SchedulingShard, Queue, PodGroup, BindRequest, and Topology.
</details>

<details>
<summary>**4. If a distributed training job submitted with schedulerName set to kai-scheduler stays Pending and no PodGroup exists for it, which KAI microservice do you inspect first?**</summary>

Inspect the PodGrouper microservice first, starting with `kubectl logs -n kai-scheduler deploy/pod-grouper`. Verify that the workload carries the required `kai.scheduler/queue` label. Also confirm that PodGrouper has RBAC permission to watch the parent workload custom resource.
</details>

<details>
<summary>**5. If a PodGroup is marked scheduled by kai-scheduler, but its fractional GPU pods remain Pending on the target node, which KAI CRD and microservice do you inspect?**</summary>

Look at the BindRequest custom resource in the workload namespace, and check the logs of the Binder microservice in the `kai-scheduler` namespace. Then check the status of the integer `nvidia.com/gpu` reservation Pod that the Binder creates on the target worker node.
</details>

<details>
<summary>**6. Why is a single GPU Utilization dashboard insufficient as an SLI and SLO contract for a shared GPU platform?**</summary>

For example, high utilization on a shared time-sliced GPU can hide severe contention and tail-latency breaches. Low utilization on a reserved MIG slice can be a healthy, latency-sensitive endpoint that holds burst capacity. Utilization alone never shows queue wait time, allocation failures, or stale scrape pipelines.
</details>

<details>
<summary>**7. What are the three distinct operational views for shared GPUs, and who is the primary audience for each?**</summary>

The platform health view serves site reliability and platform operations. It tracks node readiness, device discovery, driver errors, and scrape freshness. The service delivery view serves tenant and service owners, with scoped queue wait and request latency. The capacity and fairness view serves platform product and finance teams, with allocation hours, pending reasons, and MIG fragmentation.
</details>

<details>
<summary>**8. What are the six pillars of the Shared-GPU Telemetry Contract?**</summary>

The first three pillars are coverage across every accepted GPU node, durable identity that links a workload to its node and GPU UUID without cross-tenant leaks, and documented metric semantics. The remaining three are bounded label cardinality, enough retention history to reconstruct an incident, and multi-tenant access controls that match the cluster's isolation boundaries.
</details>

<details>
<summary>**9. State the Prometheus SLI and SLO targets for a reserved MIG inference service and a best-effort time-sliced pool.**</summary>

A reserved MIG inference service targets a request success rate above ninety-nine point five percent and a ninety-ninth percentile latency below one hundred milliseconds. Above one hundred twenty milliseconds, it triggers a breach alert. A best-effort time-sliced pool targets a ninety-fifth percentile queue wait below thirty seconds. It flags expected memory contention when physical memory utilization exceeds ninety percent.
</details>

<details>
<summary>**10. Why must you alert when dcgm_exporter_scrape_age_seconds exceeds 120 seconds, and how must dashboards represent a node with stale telemetry?**</summary>

When you see the scrape age exceed one hundred twenty seconds, the hardware metrics are stale. They no longer reflect the current state of the silicon. Dashboards and responders must mark the node and GPU state as unknown. They must not replace missing series with zeroes or assume the card is healthy.
</details>

<details>
<summary>**11. In the MIG absence playbook, what does it mean when Layer 1 and Layer 2 succeed on the host, but Layer 3 shows zero allocatable MIG resources on the Kubernetes Node?**</summary>

Suppose Layers one and two pass on the host, but Layer three shows zero allocatable MIG resources. That proves the physical GPU and host MIG partitions are healthy, so the failure sits at Layer 3, device-plugin registration. The safe fix is to inspect the device-plugin logs and restart only that node's device-plugin Pod. Wait thirty seconds for the allocatable counts to repopulate. Do this without draining the node or repartitioning MIG on the host.
</details>

<details>
<summary>**12. How do you distinguish MIG profile fragmentation from a general GPU capacity shortage?**</summary>

When you face capacity exhaustion, every compatible MIG instance and every compute or memory slice is in use. In fragmentation, worker nodes still have unused compute and memory slices. But the remaining slice geometry cannot legally combine into the requested profile shape without a drain and repartition.
</details>

<details>
<summary>**13. How does the cluster behavior of a zero-capacity ResourceQuota differ from an Insufficient nvidia.com/gpu scheduler event?**</summary>

A ResourceQuota denial happens synchronously at API admission. So when you run `kubectl apply`, it fails immediately. No Pod object is created in storage, and the node's allocatable capacity stays untouched. An insufficient resource event happens after API admission succeeds. The Pod is created in the pending state, and the scheduler emits a `FailedScheduling` event.
</details>

<details>
<summary>**14. When time-sliced workloads fail with memory pressure, what host-side threshold confirms contention, and what is the immediate safe containment action for a critical inference service?**</summary>

Memory contention is confirmed when `nvidia-smi` shows GPU memory utilization above ninety-five percent. It is also confirmed when utilization sits above eighty to ninety percent alongside tail-latency spikes and host swap activity. The immediate safe containment action is to patch the sensitive service onto a dedicated or MIG node pool. Then compare your tail latency after five minutes, rather than raising the replica count on the shared node.
</details>

<details>
<summary>**15. What are the five incident roles during a shared-GPU outage, and why must the Incident Commander never be the person running terminal commands?**</summary>

The five roles are the incident lead or Incident Commander, the platform responder or Subject Matter Expert, the workload owner, the capacity or service owner, and the communications owner. The Incident Commander coordinates without touching a keyboard. Separating the commander from the Subject Matter Expert gives the engineer inspecting kernel logs, GPU counters, and scheduler traces uninterrupted focus. The commander handles cross-team decisions and status updates.
</details>

<details>
<summary>**16. Walk through the five-step workflow of a controlled AI Game Day.**</summary>

First, define a falsifiable recovery hypothesis. Second, restrict the blast radius to a staging mirror or canary pool. Third, run the specific fault injection. Fourth, observe whether the alerts fire and whether automated recovery holds the service level objective. Fifth, write a postmortem with a tracked engineering ticket for every gap you uncover.
</details>

<details>
<summary>**17. How do you inject a simulated GPU double-bit ECC fault and an RDMA link blackhole during an AI Game Day, and why does host iptables fail to test RDMA blackholes?**</summary>

Inject a simulated double-bit ECC fault on an isolated test GPU with `dcgmi test --inject`, then verify that the device plugin marks the card unhealthy and evicts the Pod. To test an RDMA blackhole, you disable the physical or switch port with `ibportstate ... disable` during collective benchmarks. Host `iptables` rules cannot block RDMA, because RDMA verbs bypass the Linux kernel TCP/IP stack entirely.
</details>

<details>
<summary>**18. Why did powering off one of three Kubernetes master nodes cause a complete outage of all Triton inference pods on the worker nodes?**</summary>

The worker-node device-plugin and GPU Operator DaemonSets had liveness probes that were too aggressive, and those probes were tied to API server responsiveness. When one master powered off, the brief leader-election pause made the probes fail, and they restarted the plugins. That restart unregistered `nvidia.com/gpu` on the worker nodes, so local node agents terminated all running Triton GPU Pods.
</details>

<details>
<summary>**19. Why did Kubernetes PodDisruptionBudgets fail to prevent the worker-node kubelets from terminating those Triton pods during the device-plugin restart?**</summary>

PodDisruptionBudgets govern only voluntary disruptions that go through the Kubernetes Eviction API, such as `kubectl drain`. They do not intercept the node-local terminations that happen when a worker node's extended hardware resource disappears from the node agent.
</details>

<details>
<summary>**20. What seven items must be included in an actionable vendor or engineering Escalation Package to avoid the log-request loop?**</summary>

Include the business impact and timestamps, plus precise, tenant-redacted reproduction steps. Add the node name, GPU UUID, and the active MIG or replica policy. Attach the exact software and driver versions across the stack, and side-by-side evidence from the affected node and a healthy peer. Finally, include time-correlated scheduler and DCGM logs, and the chronological history of changes and mitigations.
</details>

## Sources and review notes

```text
Sources, Provenance, and Review Ledger for Chapter 11.18
--------------------------------------------------------
Primary sources read in full for this chapter:
  - Book sources from the local TOON-RAG corpus:
    * Roland Huß et al., Generative AI on Kubernetes (O'Reilly, 2026), Chapter 7
      (Job Scheduling Optimization, NVIDIA KAI Scheduler components: operator,
      kai-scheduler, pod-grouper, binder, queue-controller, admission,
      pod-group-controller; CRDs: Config, SchedulingShard, Queue, PodGroup,
      BindRequest, Topology).
  - Author's Volume 11 and Volume 19 notes:
    * nvidia-zero-to-hero/volume-11/chapter-10-observability-and-slos-for-shared-gpus.md
      (Three operational views, 6-part telemetry contract, service-class SLIs and
      Prometheus rules > 99.5%, < 100 ms / > 120 ms breach, < 30 s p95 queue wait,
      > 90% memory utilization, > 120 s DCGM scrape staleness, 5 alert families,
      and multi-tenant data-leakage boundaries).
    * nvidia-zero-to-hero/volume-11/chapter-11-production-troubleshooting.md
      (Figure 11.11.1 6-layer triage flowchart, 5-layer MIG absence playbook,
      Pending Pod vs fragmentation playbook, time-sliced memory contention > 95% /
      > 80%–90% / 5 min recovery check, kubectl patch deployment critical-service
      -p '{"spec":{"nodeSelector":{"gpu.sharing":"dedicated"}}}', change-surface
      review table, and 5 incident roles: Incident lead, Platform responder,
      Workload owner, Capacity/service owner, Communications owner).
    * nvidia-zero-to-hero/volume-11/labs/lab-04-troubleshoot-a-multi-tenant-gpu-node.md
      (18-section incident runbook, scene preservation bundle: node-describe.txt,
      node-pods.txt, events.txt, node-resources.txt, resourcequotas.txt;
      DIAGNOSTIC_GPU_OK pod, diagnostic-gpu-denial zero-quota fault injection vs
      Insufficient scheduler events, quota-denial.txt, and
      QUOTA_DENIAL_RECOVERY_CHECK cleanup).
    * nvidia-zero-to-hero/volume-19/chapter-02-incident-response-and-game-day-execution.md
      (5-step Game Day workflow, XID 48 via dcgmi test --inject, RDMA blackhole
      via ibportstate ... disable vs iptables, ICS role separation IC / SME /
      Communications Lead, 3:00 AM Sunday vs 10:00 AM Tuesday, and the 99.999%
      < 5 s control-plane master failover postmortem on device-plugin liveness
      probes and PDB limits).

Related source files mapped in MIGRATION_MAP.md:
  - No separate nvidia-devops file was exclusively mapped to 11.18 in brief.py;
    this chapter integrates Generative AI on Kubernetes Chapter 7,
    volume-11/chapter-10, volume-11/chapter-11, volume-11/labs/lab-04, and
    volume-19/chapter-02.

Run here:
  - python3 code/part11/kai_operations_and_troubleshooting_lab.py
    (25 passed, 0 failed out of 25 checks).

Explicitly labelled inferences:
  - Combining the volume-11/chapter-11 6-layer shared-GPU triage tree with KAI
    Scheduler's pod-grouper (PodGroup), queue-controller (Queue), and binder
    (BindRequest) boundaries at Layers 4 and 5 is a deterministic operational
    synthesis verified by code/part11/kai_operations_and_troubleshooting_lab.py.

Not verified on live hardware:
  - All `kubectl`, `ssh`, `nvidia-smi`, `mig-manager` (`nvidia.com/mig-2g.20gb`, `3g.40gb`, `4g.40gb`, `3/7` slices, `0.25` fractions, `40` GB / `300`s windows, `quota-denied-gpu-pod`), `nccl-tests`, `dcgmi test --inject`, `ibportstate`, and Prometheus rules are marked `(untested here)`.

Not in the corpus:
  - Internal KAI Scheduler Prometheus metric names beyond the standard Kubernetes /
    DCGM Exporter / PodGroup status metrics documented in the corpus.

Corrections to the author's notes:
  - KAI Scheduler check 2026-10-25: this chapter's KAI details were compared with
    the upstream docs; see the note at the top of Chapter 11.14 for what was
    confirmed, corrected (kai.scheduler/queue label, kai.scheduler/topology*
    annotations, Topology group kai.scheduler/v1alpha1) and not confirmed (the
    book's Project kind). In Chapter 11.17 the example now requests gpu-fraction
    only; the upstream docs list gpu-fraction and gpu-memory as alternative ways
    to ask for a share.
  - Validation pass 2026-10-25: validate_chapter.py and check_coverage.py pass.
    The YAML manifests and commands are marked untested and were not applied to a
    cluster. Custom resource API versions (for example kueue.x-k8s.io/v1beta1,
    resource.k8s.io/v1) change between releases, so check them against the version
    you install. Console outputs quoted from the Volume notes are illustrative
    unless the chapter says otherwise.
  - Earlier author note: all SLI/SLO thresholds (> 99.5%, < 100 ms, > 120 ms,
    < 30 s, > 90%, > 120 s), triage commands, and Game Day numbers (XID 48,
    99.999%, < 5 s) match volume-11 and volume-19 verbatim.
```
