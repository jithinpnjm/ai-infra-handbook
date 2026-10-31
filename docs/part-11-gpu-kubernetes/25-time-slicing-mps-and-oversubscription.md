---
id: "c11-25"
title: "11.25 Time-slicing, MPS and oversubscription"
sidebar_label: "11.25 Time-slicing, MPS and oversubscription"
sidebar_position: 25
description: "Deep dive into software GPU sharing on Kubernetes: device-plugin time-slicing, CUDA Multi-Process Service (MPS), replica-ratio benchmarking, and oversubscription governance."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 11.25 Time-slicing, MPS and oversubscription

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE and local Python 3 simulation lab |
| Part | Part 11: GPUs on Kubernetes, scheduling and virtualization |
| Sources used | `nvidia-zero-to-hero/volume-11/chapter-04-time-slicing-and-oversubscription.md`; `volume-04/03-gpu-sharing-telemetry-masterclass.md`; `nvidia-zero-to-hero/volume-11/chapter-01-why-gpu-sharing-exists.md`; `nvidia-zero-to-hero/volume-11/chapter-07-kubernetes-scheduling-for-shared-gpus.md`; `nvidia-zero-to-hero/volume-11/chapter-11-production-troubleshooting.md`; `nvidia-zero-to-hero/volume-11/chapter-12-volume-11-summary.md`; `nvidia-zero-to-hero/volume-11/index.md`; `nvidia-zero-to-hero/volume-11/labs/lab-01-configure-and-validate-mig.md`; `nvidia-zero-to-hero/volume-11/labs/lab-02-configure-kubernetes-gpu-time-slicing.md`; `nvidia-zero-to-hero/volume-11/labs/lab-03-compare-sharing-performance-and-isolation.md`; `nvidia-zero-to-hero/volume-11/labs/lab-04-troubleshoot-a-multi-tenant-gpu-node.md`; Roland Huß et al., *Generative AI on Kubernetes* (O'Reilly, 2026, Ch. 3) |
| Coverage file | `planning/coverage/chapters/11-25.md` |

## Why this matters for AI infrastructure

Picture a platform team with a busy cluster and a queue of developers who cannot get a GPU. Many GPUs in production clusters lack hardware Multi-Instance GPU silicon. NVIDIA T4, L4, L40S and A10G inference cards cannot split their compute engines or memory controllers in hardware. Even on A100 or H100 nodes that support MIG, interactive Jupyter notebooks, continuous integration runners and lightweight microservices sit idle most of the time between short bursts. You feel that pressure when dozens of developers wait in pending queues while the allocated accelerators burn budget at low utilization.

Without hardware partitioning, NVIDIA offers two software ways to share a GPU, and each one trades hard isolation for higher density. The first is temporal sharing, known as Time-Slicing. The NVIDIA Device Plugin advertises several logical tokens for each physical GPU. Every scheduled Pod mounts the exact same `/dev/nvidia0` device file and takes its turn through round-robin GPU context switching.

The second is spatial sharing, known as CUDA Multi-Process Service or MPS. A background proxy daemon runs in exclusive process compute mode. That proxy funnels CUDA calls from multiple client processes into a single shared GPU context, so small kernels run side by side on the Streaming Multiprocessors.

Both mechanisms raise access density, and both cause outages when a logical replica token gets mistaken for a hardware reservation. Standard Linux memory cgroups govern host system RAM, not GPU high-bandwidth memory. If one Pod leaks memory on a time-sliced card, every neighbor Pod on that physical GPU crashes with an out-of-memory error.

Even under CUDA MPS, you can cap active threads and pinned device memory for each client. All connected clients still share a single hardware fault domain.

The three failure modes below come from this chapter's sources. Each one is worth recognizing on sight.

```text
Software GPU Sharing Failure Modes (volume-11/chapter-04 and volume-04/03):
1. Time-Slicing Idle Pattern: Interactive notebooks and CI runners sit idle 80%+ of the time between bursts.
2. Time-Slicing OOM Blast Radius: On a 16 GB T4 GPU advertised with replicas: 10, all 10 Pods share one 16 GB VRAM pool.
   If Pod 1 leaks and allocates all 16 GB, Pods 2 through 10 (9 neighbor pods) crash with CUDA Out of Memory.
3. CUDA MPS Ghost OOM: Container A crashes with CUDA OOM on a 40 GB A100 while nvidia-smi reports only 10 GB / 40 GB used.
   Root cause: per-client CUDA_MPS_PINNED_DEVICE_MEM_LIMIT cap (for example 8 GB vs a 12 GB burst) or transient neighbor spike.
```

Notice that the first two modes come from one shared memory pool, while the third comes from a per-client MPS cap or a neighbor's spike. Decide early which workloads can tolerate shared memory, because that decision sets the failure modes you must guard against.

## Prerequisites and outcomes

### Prerequisites

- Finish Chapter 11.2 on Device Plugin ConfigMaps, Chapter 11.17 on KAI fractional GPUs and Chapter 11.24 on MIG in depth.
- Be comfortable with Kubernetes ResourceQuota, ClusterPolicy and `nvidia-smi` telemetry commands.

### Outcomes

By the end of this chapter, you should be able to do the following.

- Explain the architectural difference between Kubernetes Device-Plugin Time-Slicing and CUDA Multi-Process Service across context switching, SM execution and HBM isolation.
- Configure safe Time-Slicing ConfigMaps with explicit shared resource naming and single-token admission guards, plus CUDA MPS daemons with thread and memory limits.
- Run the five-phase replica-ratio benchmark on an A100 node, so you can choose a safe concurrency envelope with adequate memory headroom.
- Implement the six-step safe rollout sequence, the ten-field operating policy contract, the eight-item contention evidence package and production namespace ResourceQuota guards.

## Concepts: basics to intermediate to advanced

### 1. Basics: Time-slicing and CUDA Multi-Process Service

#### What device-plugin time-slicing actually changes

Suppose a platform team sets `replicas: N` in the NVIDIA Device Plugin ConfigMap. They picture the GPU sliced into smaller virtual cards. That picture causes noisy-neighbor incidents and surprise crashes for data scientists who share development nodes. In reality, the replica count changes only the Kubernetes control-plane accounting token count. Nothing changes on the GPU silicon, the memory controller or the Linux device driver.

Every Pod admitted onto a time-sliced GPU gets permission to open the same underlying device node. Asking for two shared tokens in one Pod does not double the memory or compute share. That trap is why production configurations always reject multi-token requests on shared pools. The table below compares what the Kubernetes control plane reports with what happens on the physical hardware.

| Control-Plane Claim | Actual Hardware and Runtime Reality (`volume-11/chapter-04` and `volume-04/03`) |
|---|---|
| The Pod is `Running` with `nvidia.com/gpu: 1` | The Pod received an admission token to open `/dev/nvidia0`; it did not receive a fixed share of SMs or a reserved slice of VRAM. |
| The Node has `8` or `10` Allocatable GPUs | One physical GPU (`16 GB` T4 or `80 GB` A100) is represented by `8` or `10` logical scheduler tokens; all pods contend in the same memory and fault domain. |
| A Pod requests `nvidia.com/gpu: 2` on a shared node | Requesting `2` time-sliced tokens does not grant `2x` the compute or `2x` the memory, which is why production configs set `failRequestsGreaterThanOne: true`. |
| Linux `cgroups` will protect neighbor pods from OOM | False: standard Linux `memory` cgroups only govern host system RAM, not GPU HBM/VRAM. If `Pod 1` leaks `16 GB` on a `16 GB` T4 with `replicas: 10`, `Pods 2..10` (`9` pods) crash with `CUDA OOM`. |

Pay close attention to the last row. The cgroup assumption is false for GPU memory, so a leak on one Pod can reach its neighbors.

#### Temporal time-slicing versus spatial CUDA MPS

Under standard Time-Slicing, each container gets its own independent CUDA context on the GPU. When MIG is not active, only one CUDA context can execute on the Streaming Multiprocessors at any instant. The hardware scheduler must pause the first process, save its register state, load the next process state and run the next time quantum.

Consider two inference microservices that each launch small kernels needing only twenty percent of the SMs. Temporal switching still serializes them, and it adds context-switch jitter.

CUDA Multi-Process Service removes this serialization by replacing separate contexts with one shared context. An administrator locks the GPU into exclusive process compute mode and starts the `nvidia-cuda-mps-control` background daemon. Client containers then connect to the `nvidia-cuda-mps-server` over UNIX domain sockets, not through separate hardware contexts.

The MPS server merges the client CUDA streams. Kernels from different containers can therefore run side by side on separate SMs at the exact same instant.

```mermaid
flowchart TD
    subgraph TS["1. Time-Slicing: Temporal Context Switching"]
        P1["Pod A: Own CUDA Context"] -->|"Context Switch Quanta t1"| GPU1["Physical GPU SMs & Unified HBM Pool"]
        P2["Pod B: Own CUDA Context"] -->|"Context Switch Quanta t2 + Jitter"| GPU1
    end
    subgraph MPS["2. CUDA MPS: Spatial Concurrent Execution"]
        C1["Client A: 20% Thread Cap"] -->|"UNIX Socket /tmp/nvidia-mps"| Srv["nvidia-cuda-mps-server: Single Context"]
        C2["Client B: 20% Thread Cap"] -->|"UNIX Socket /tmp/nvidia-mps"| Srv
        Srv -->|"Concurrent Spatial Execution on SMs"| GPU2["Physical GPU SMs & Shared Fault Domain"]
    end
```

In the diagram, the top branch shows separate contexts taking turns, and the bottom branch shows one shared context running kernels together.

---

### 2. Intermediate: Benchmarking the replica envelope and diagnosing the MPS Ghost OOM

#### The five-phase replica-ratio measurement protocol

Suppose you copy a replica ratio of eight or ten from an online tutorial. That is one of the fastest ways to destabilize a cluster. Without load testing, your team finds the true memory high-water mark only when notebooks start crashing during peak daytime hours. Treat the replica count as a capacity envelope that you measure for one workload class on one GPU model. Every shared pool needs a structured five-phase measurement protocol before it admits tenant traffic.

Engineers begin with a single-tenant baseline. That run measures normal tail latency and memory footprint with zero peer interference. Next they step through concurrent active neighbors, burst queueing, neighbor failure recovery and post-upgrade regression checks.

During each run, host telemetry tools sample SM utilization, memory consumption, power and thermal counters every second over a five-minute window. Take an eighty-gigabyte A100 hosting interactive PyTorch notebooks as an example. Keeping at least twenty gigabytes of free HBM headroom stops sudden allocation spikes from triggering out-of-memory kills.

```text
5-Phase Replica-Ratio Measurement Protocol (volume-11/chapter-04):
- Telemetry Commands:
  nvidia-smi dmon -s puctem -n 300 (5 minutes of 1-second samples)
  nvidia-smi --query-processes=gpu_uuid,pid,process_name,gpu_memory_usage --format=csv
- Phase 1 (Single tenant): Establish baseline p99 kernel launch latency and peak memory for 1 workload alone.
- Phase 2 (Concurrent active): Add neighbors (2, 4, 8) until latency SLO or memory headroom (>= 20 GB on an 80 GB card) is reached.
- Phase 3 (Burst): Verify application queueing or admission shedding bounds overload without crashing the node.
- Phase 4 (Failure/recovery): Confirm neighbor pod stability when one pod OOMs or restarts.
- Phase 5 (Upgrade repeat): Re-run the concurrency test after driver, CUDA runtime, or model updates.
```

The table below shows what happened as the notebook count rose on one 80 GB A100.

| Concurrent Notebooks on `1 × A100 80GB` | Per-Notebook SM Activity (`%`) | Combined HBM Used (`GB` of `80 GB`) | Observed `p99` Kernel Launch Latency | Engineering Verdict (`volume-11/chapter-04`) |
|---|---|---|---|---|
| `1` Notebook (Baseline) | `25%` SM | `12 GB` (`68 GB` free) | `8 ms` (imperceptible) | Clean single-tenant baseline |
| `2` Concurrent Notebooks | `~40%` SM | `24 GB` (`56 GB` free) | `25 ms` (interactive smooth) | Low interference |
| `4` Concurrent Notebooks | `~55%` SM | `48 GB` (`32 GB >= 20 GB` headroom) | `120 ms` (noticeable, acceptable for dev) | Selected Safe Envelope: `replicas: 4` |
| `8` Concurrent Notebooks | `~65%` SM | `96 GB > 80 GB` (`+16 GB` overflow) | `500 ms` (severe thrashing / host RAM spill) | UNSAFE: `nvidia-smi` shows process OOM-killed |

Walk through the arithmetic. One notebook uses 12 GB. Four notebooks use 4 × 12 GB, which is 48 GB. That leaves 32 GB free on the 80 GB card, more than the 20 GB headroom you need. Eight notebooks need 8 × 12 GB, or 96 GB. That is 16 GB more than the card holds, so four is the highest count that keeps the headroom.

#### Configuring CUDA MPS and diagnosing the Ghost OOM

Suppose several inference microservices share one GPU through CUDA MPS. A client without a cap can take over the compute threads or use up the device memory. To prevent that starvation, operators set an active thread percentage cap and a pinned device memory limit in the MPS control daemon.

Each client then sees only its permitted share of SM warps. It hits a software allocation ceiling before it can exhaust the physical HBM. These software ceilings, however, can produce a confusing failure when on-call responders check standard host tools.

Here is the classic Ghost OOM. Two inference containers share a forty-gigabyte A100 under CUDA MPS. One container crashes again and again with a CUDA out-of-memory exception. Yet `nvidia-smi` on the host shows only ten gigabytes in use. An on-call engineer can waste hours suspecting a driver bug, because thirty gigabytes of physical HBM look free. Three mechanisms explain the gap, and the architectural cure for strict, non-overlapping isolation is hardware MIG.

The block below lists the controls and the three root causes.

```text
CUDA MPS Controls and the Ghost OOM Diagnosis (volume-04/03 Part 1.2 and Part 6 Scenario 1):
- Thread Cap Control: echo "set_default_active_thread_percentage 20" | nvidia-cuda-mps-control (or CUDA_MPS_ACTIVE_THREAD_PERCENTAGE=20).
- Memory Cap Control: CUDA_MPS_PINNED_DEVICE_MEM_LIMIT or set_default_device_pinned_mem_limit in nvidia-cuda-mps-control.
- Ghost OOM Symptom: Container A crashes with CUDA Out of Memory on a 40 GB A100 while nvidia-smi shows only 10 GB / 40 GB (10000MiB / 40960MiB) used.
- Root Cause 1 (Per-Client MPS Memory Ceiling): CUDA_MPS_PINNED_DEVICE_MEM_LIMIT was set to 8 GB, so Container A hit its software limit during a 12 GB burst while 30 GB of physical HBM sat free.
- Root Cause 2 (Post-Crash Sampling Artifact): nvidia-smi was sampled after Container A crashed and released its GPU memory allocation.
- Root Cause 3 (Neighbor Burst Spike): Container B spiked to 32+ GB during a large batch and freed its buffers right after Container A failed.
- Architectural Fix: Migrate workloads requiring guaranteed hardware memory walls and separate fault domains to MIG (Chapter 11.24).
```

Notice that the three causes are different: a software cap, a late sample and a neighbor's spike.

---

### 3. Advanced: Production oversubscription governance, namespace guards, and the operating policy

#### Six controls that protect a shared pool and guarding production namespaces

Kubernetes treats each logical GPU token as a binary admission ticket. The default scheduler does not check physical HBM pressure, context-switch queue depth or tail latency before it places a Pod. Now picture a time-sliced node pool that advertises the default `nvidia.com/gpu` name. A latency-sensitive production deployment can land next to noisy development notebooks. Every Pod then reports healthy in Kubernetes, while customer tail latency triples.

You protect a cluster with six layered controls. They keep best-effort sharing apart from guaranteed production capacity. The first control renames the shared resource to `nvidia.com/gpu.shared`, so workloads must opt in to time-slicing on purpose. The second control is a ResourceQuota in every production namespace, with the shared resource hard limit set to zero. Controls three through six add application concurrency limits, bounded request queueing, workload-correlated host telemetry and a pre-approved dedicated escape pool.

```text
Six Operational Controls for Shared GPU Pools (volume-11/chapter-04):
1. Separate shared node pool and explicit resource naming: Set renameByDefault: true to advertise nvidia.com/gpu.shared.
   Prevents Scenario 3 where a critical service (p99 < 100 ms SLO) requests generic nvidia.com/gpu: 1, lands on a shared node, and degrades to p99 > 300 ms.
2. Namespace quota and admission control: Set nvidia.com/gpu.shared: "0" and nvidia.com/gpu: "unlimited" in production ResourceQuotas.
3. Application-level concurrency and request limits: Bound batch size and active in-flight requests inside vLLM or Triton.
4. Queueing or load shedding: Keep overload visible as bounded queue wait (timeslice_queue_time_p95 < 30 s) rather than 500 ms thrashing.
5. Workload-correlated telemetry (DCGM Attribution Gap): When device-plugin time-slicing is enabled, dcgm-exporter cannot associate GPU-level metrics (DCGM_FI_DEV_GPU_UTIL) with individual containers. Join scheduler records, Pod UIDs, app latency, and host nvidia-smi --query-processes / nvidia-smi pmon -c 1.
6. Dedicated escape hatch: Pre-approve a whole-GPU or MIG pool (kubectl set resources deployment/<name> --limits nvidia.com/gpu=1) for rapid evacuation.
```

The block above gives each control with the failure it prevents. Controls one and two work as a pair: the rename makes the shared pool visible in manifests, and the quota refuses shared requests in production. The manifest below puts the quota into practice.

```yaml
# Deny shared best-effort GPUs in production namespaces (volume-11/chapter-04, untested here)
apiVersion: v1
kind: ResourceQuota
metadata:
  name: deny-shared-gpus-in-prod
  namespace: prod-serving
spec:
  hard:
    nvidia.com/gpu.shared: "0"      # Forbid best-effort time-sliced GPUs
    nvidia.com/gpu: "unlimited"     # Permit dedicated GPUs
```

Notice the `0` on the shared line. That single value keeps best-effort pods out of the production namespace.

#### Safe rollout sequence, operating policy, and contention evidence package

Suppose you turn on time-slicing across a live cluster with no staged rollout. That invites immediate contention incidents. If a change goes wrong, responders need a rehearsed rollback path and a standard diagnostic bundle before users escalate. Platform teams therefore follow a six-step rollout sequence. It starts on a noncritical node pool labeled explicitly for sharing. The team validates allocation transitions, verifies latency and memory high-water marks, and rehearses reverting the ClusterPolicy to a single replica.

Every shared pool publishes a ten-field operating policy contract, and it defines an eight-item contention evidence package. The operating policy says which workloads may enter the pool, what memory ceiling each Pod must obey and who owns escalation when contention strikes. When a slowdown happens, responders collect the eight time-correlated evidence items, which close the container attribution gap in standard telemetry. The reference block below summarizes all three operational checklists.

```text
6-Step Safe Rollout Sequence, 10-Field Policy, and 8-Item Evidence Package (volume-11/chapter-04, labs/lab-02, GAK Ch. 3):
- 6-Step Safe Rollout Sequence:
  1. Select a noncritical node pool and label/taint it as shared (nvidia.com/device-plugin.config=all in Generative AI on Kubernetes Ch. 3 Examples 3-11/3-12) before configuring replicas.
  2. Capture single-tenant and concurrent baselines.
  3. Start with a conservative replica count (replicas: 4); validate allocation (1 -> 4 allocatable after 30 s in labs/lab-02), p99 latency, memory high-water mark, and recovery.
  4. Increase density only while the agreed service envelope passes.
  5. Publish the 10-Field Operating Policy Template.
  6. Rehearse configuration removal on a canary node (labs/lab-02 Section 17) and capture the 8-Item Contention Evidence Package during any slowdown.
- 10-Field Operating Policy Template:
  1. Shared-pool purpose | 2. Eligible and excluded workloads | 3. Advertised shared resource name (nvidia.com/gpu.shared)
  4. Tested replica envelope and date | 5. Memory and latency assumptions | 6. Quota scope and admission behavior
  7. Overload action (queue, throttle, shed, or evict at 80%-90% memory) | 8. Escalation owner
  9. Protected-service escape path | 10. Rollback action for configuration change
- 8-Item Contention Evidence Package:
  1. Workload version & request rate | 2. p50/p95/p99 latency & queue depth | 3. Pod allocation & placement history
  4. Active-process & memory evidence (nvidia-smi --query-processes) | 5. Device health, power, thermal & error events
  6. Node/device-plugin config & events | 7. Quota/admission decisions | 8. Actions taken & time to recovery
```

Notice that the policy template settles the rules in advance, while the evidence package covers the moment a slowdown happens.

#### Kubernetes primitives versus shared-GPU realities and post-upgrade validation

In architecture reviews, it is easy to assume that Kubernetes scheduling enforces fairness at runtime on a shared accelerator. You might expect resource requests, node selectors, taints, quotas and priority classes to police GPU memory and kernel execution. In practice, each of those objects works only at pod admission or placement time. Once two containers open the same physical device node, the Kubernetes control plane has zero visibility into their CUDA kernels or HBM allocations.

So each scheduling primitive needs a complementary runtime control, at the application, MPS or hardware MIG layer. Upgrades add another risk: a cluster upgrade can silently reset device-plugin ConfigMaps, alter node labels or change driver scheduling behavior. After every GPU Operator, device-plugin, driver or node-image update, you must run the eight-step pre-production and post-upgrade acceptance checklist. The table and checklist below map each Kubernetes primitive to its hardware gap and to its verification steps.

| Kubernetes Primitive (`volume-11/chapter-04`) | What It Contributes to a Shared GPU Pool | What It Cannot Protect on the Physical GPU | Complementary Runtime / Platform Control Required |
|---|---|---|---|
| 1. `resources.requests` / `limits` (`nvidia.com/gpu.shared: 1`) | Reserves `1` logical admission token in `kube-scheduler` accounting | Does not divide physical HBM memory or SMs; `1` pod can still allocate `100%` of VRAM | Application memory caps (`PYTORCH_CUDA_ALLOC_CONF`), KAI `gpu-memory` admission, or `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT` |
| 2. `nodeSelector` / `nodeAffinity` | Routes best-effort pods (`nvidia.com/device-plugin.config=all`) to the shared node pool | Does not validate workload memory or latency behavior once placed on the node | 5-phase pre-admission concurrency envelope test (`Single -> Concurrent -> Burst -> Failure -> Upgrade`) |
| 3. `taints` and `tolerations` | Prevents general workloads from landing on specialized GPU nodes (`node.kubernetes.io/unschedulable` in canary labs) | Does not provide tenant memory, fault, or process isolation between co-scheduled pods | Restrict time-slicing/MPS to trusted single-team cohorts; use MIG or vGPU for untrusted tenants |
| 4. `ResourceQuota` | Bounds total logical GPU tokens requested by a namespace (`one-logical-gpu` in `labs/lab-02`, or `nvidia.com/gpu.shared: "0"` in prod) | Does not arbitrate GPU kernel launch frequency or SM context-switch fairness | Application-level request queues, token-bucket rate limiters, or CUDA MPS `set_default_active_thread_percentage` |
| 5. `PriorityClass` | Controls which pending Pod schedules first and which Pod is evicted under node pressure | Does not create physical GPU capacity or pause an already-running CUDA kernel mid-flight | Graceful `SIGTERM` checkpoint handlers and a dedicated whole-GPU / MIG escape pool for critical services |

Notice that each row pairs a Kubernetes primitive with a runtime or platform control it still needs.

```text
8-Step Pre-Production and Post-Upgrade Acceptance Checklist (volume-11/chapter-04):
1. Schedule known concurrent benchmark workloads (time-slice-a, time-slice-b) on the target shared pool.
2. Confirm advertised resource name (nvidia.com/gpu.shared) and node labels/selectors match the design.
3. Measure application p50/p95/p99 latency and queue behavior under concurrent load.
4. Measure combined GPU memory high-water marks (nvidia-smi dmon -s puctem).
5. Confirm alert rules and the 8-item Contention Evidence Package (allocation history + host nvidia-smi --query-processes) function.
6. Reduce admission or replica density in a drill and confirm latency recovers to baseline.
7. Evacuate a test workload to the dedicated or MIG escape pool and verify SLO recovery.
8. Re-execute this checklist (and the 5 upgrade checks: allocatable names/counts, labels/selectors, namespace policy, concurrent smoke test, dashboard attribution) after every GPU Operator, device-plugin, driver, or runtime upgrade.
```

Run this checklist once before you admit traffic, and again after every upgrade.

## Commands and configurations that matter

### 1. Device-plugin time-slicing ConfigMap with explicit shared naming

Suppose a cluster turns on time-slicing but never renames the resource or blocks multi-token requests. Users inevitably schedule multi-GPU jobs or production APIs onto shared nodes. The ConfigMap below enables four logical replicas per physical GPU. It renames the resource to `nvidia.com/gpu.shared` and rejects any Pod that requests more than one token.

```yaml
# time-slicing-safe-configmap.yaml (volume-11/chapter-04 & labs/lab-02, untested here)
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
  namespace: gpu-operator
data:
  any: |-
    version: v1
    sharing:
      timeSlicing:
        renameByDefault: true
        failRequestsGreaterThanOne: true
        resources:
          - name: nvidia.com/gpu
            replicas: 4
```

After you create the ConfigMap, the operator patches the ClusterPolicy and verifies the updated allocatable count on the target node. The commands below do the patch and the check.

```bash
# Select the time-slicing ConfigMap in ClusterPolicy and check node allocatable (untested here)
kubectl patch clusterpolicy gpu-cluster-policy --type merge \
  --patch '{"spec":{"devicePlugin":{"config":{"name":"time-slicing-config","default":"any"}}}}'
kubectl get node gpu-node-1 -o jsonpath='{.status.allocatable.nvidia\.com/gpu\.shared}{" shared allocatable\n"}'
```

Check the allocatable count before any workload requests the shared name.

### 2. Enabling CUDA Multi-Process Service with thread and memory caps

Picture several small inference servers running under the default compute mode. They waste SM capacity on context-switch stalls. Locking the GPU into exclusive process mode and starting the CUDA MPS control daemon lets those servers run kernels spatially, side by side, inside one shared context. The script below sets the pipe and log directories, starts the daemon, caps each client at twenty percent of active threads and enforces an eight-gigabyte pinned memory limit.

```bash
#!/usr/bin/env bash
# Enable CUDA MPS on GPU 0 with 20% active thread cap and 8GiB pinned memory limit (volume-04/03, untested here)
export CUDA_VISIBLE_DEVICES=0
export CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps
export CUDA_MPS_LOG_DIRECTORY=/tmp/nvidia-log

# Lock GPU 0 to EXCLUSIVE_PROCESS so only nvidia-cuda-mps-server holds the hardware context
sudo nvidia-smi -i 0 -c EXCLUSIVE_PROCESS

# Start the MPS control daemon
nvidia-cuda-mps-control -d

# Cap each MPS client to 20% of SMs and 8GiB of device memory
echo "set_default_active_thread_percentage 20" | nvidia-cuda-mps-control
echo "set_default_device_pinned_mem_limit 0 8G" | nvidia-cuda-mps-control
```

Notice the order: the GPU is locked first, the daemon starts second, and the caps go in last. Set the caps before any client connects to the daemon.

### 3. Live contention triage on a time-sliced node

Suppose users report slow kernel execution on a shared node. Standard container metrics cannot show which neighbor Pod is hogging the GPU. On-call responders must read host-level device telemetry and process tables directly on the node. The commands below stream three hundred one-second samples of SM, memory, power and thermal counters. They also list the exact host PIDs and memory footprints on each GPU.

```bash
# Stream 5 minutes of 1-second SM/memory/power/thermal samples and list active PIDs (untested here)
nvidia-smi dmon -s puctem -n 300
nvidia-smi pmon -c 1
nvidia-smi --query-processes=gpu_uuid,pid,process_name,gpu_memory_usage --format=csv
```

The first command samples over time, while the other two show which processes are on the GPU at that moment. Run them during the slowdown, because the Ghost OOM example earlier in this chapter shows how a late sample can mislead you.

## How it fails

Software GPU sharing fails when the combined demand from workloads crosses physical HBM capacity, a latency budget or a shared fault boundary. The Kubernetes scheduler counts only logical admission tokens, so these failures show up as latency spikes, mysterious out-of-memory kills or crashes that hit several containers at once. When you see one of these symptoms, the table tells you which boundary failed. It maps the five main production failure modes to their exact symptoms, root cause boundaries and architectural fixes.

| Failure mode | Exact symptom and command evidence | Root cause boundary | Remediation |
|---|---|---|---|
| 1. `8` concurrent notebooks on an `80 GB` A100 hit `p99 = 500 ms` and crash with `CUDA OOM` (`volume-11/chapter-04`) | At `replicas: 8`, `nvidia-smi` shows combined memory demand (`8 × 12 GB = 96 GB`) exceeding `80 GB`, `p99` kernel latency jumps from `8 ms` to `500 ms`, and pods are OOM-killed. | Time-Slicing Memory Over-Subscription: logical tokens do not partition HBM; `8` active `12 GB` notebooks exceed physical memory by `16 GB`. | Reduce `replicas` to `4` (`48 GB` used, `32 GB >= 20 GB` headroom, `p99 = 120 ms`) or use KAI Scheduler's `gpu-memory` admission cap (Chapter 11.17). |
| 2. Production inference service (`p99 < 100 ms`) degrades to `p99 > 300 ms` while all Pods report `1/1 Running` (`volume-11/chapter-04` Scenario 3) | `kubectl get pods` is green, `curl .../metrics \| grep latency_p99_ms` reports `> 300 ms`, and `kubectl exec <pod> -- nvidia-smi` shows multiple notebook PIDs on the same GPU. | Critical Workload Scheduled onto Best-Effort Pool: time-sliced nodes advertised `nvidia.com/gpu` instead of `nvidia.com/gpu.shared`, and the prod namespace lacked a `ResourceQuota` guard. | Enable `renameByDefault: true` (`nvidia.com/gpu.shared`), enforce `ResourceQuota` `nvidia.com/gpu.shared: "0"` in production namespaces, and evacuate the deployment to a dedicated or MIG pool. |
| 3. Container A under CUDA MPS crashes with `CUDA OOM` on a `40 GB` A100 while `nvidia-smi` shows only `10 GB` used (`volume-04/03` Scenario 1) | Application logs `CUDA error: out of memory`, but host `nvidia-smi` shows `10000MiB / 40960MiB`. | MPS Ghost OOM (`CUDA_MPS_PINNED_DEVICE_MEM_LIMIT` or Transient Neighbor Spike): either a per-client MPS memory limit capped Container A below its burst need, or Container B spiked and freed memory before `nvidia-smi` was sampled. | Inspect `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT` / `get_default_device_pinned_mem_limit` in `nvidia-cuda-mps-control`, or migrate the services to MIG for hardware-isolated HBM slices. |
| 4. Pod requesting `nvidia.com/gpu: 2` on a time-sliced node receives two tokens on the same contended physical GPU (`volume-11/chapter-04`) | User requests `nvidia.com/gpu: 2` expecting `2x` the compute/memory of `1` replica, but gets zero extra memory isolation and still contends with `6` other pods. | Misunderstood Logical Replica Semantics: device-plugin replicas are access tokens, not additive hardware slices. | Set `failRequestsGreaterThanOne: true` in the time-slicing ConfigMap so any pod requesting `> 1` shared token is rejected clearly, and route multi-GPU jobs to dedicated whole-GPU nodes. |
| 5. Fatal GPU context fault (`XID 13` / `XID 31` / `XID 48`) in one CUDA MPS client terminates all co-running MPS containers (`volume-04/03` & `volume-11/chapter-04`) | One buggy inference container triggers an uncontained GPU fault, and all `5` containers connected to `/tmp/nvidia-mps` crash simultaneously. | Shared MPS Hardware Context Fault Domain: because `nvidia-cuda-mps-server` funnels all clients into a single hardware GPU context, a fatal context error tearing down that context kills every connected client. | Never use CUDA MPS across untrusted tenants; restrict MPS to cooperative single-tenant microservices and use MIG (Chapter 11.24) or vGPU (Chapter 11.23) for fault-isolated multi-tenancy. |

Notice that the fixes differ, so you can match each one to its symptom. Some change `replicas` or add an admission cap, while others move the workload to MIG or vGPU. If your workload needs a hard memory wall, act on the MIG fix in the table.

## Hands-on lab

### Venue and scope

Without a local simulation model, platform engineers often test oversubscription ratios on shared development clusters, and that causes preventable outages. This lab runs on your own machine with the Python 3 standard library. It checks every capacity envelope, failure boundary and governance rule before you touch a live node. It covers the T4 ten-replica memory leak model, the five-phase A100 notebook concurrency benchmark, the CUDA MPS Ghost OOM analyzer and the operational policy checklists. Host and cluster commands elsewhere in this chapter are marked untested here.

```text
Local Verification Scope (code/part11/time_slicing_mps_oversubscription.py and time_slicing_mps_oversubscription_lab.py):
- Volume 11 Ch 4 Primer: 16 GB T4 with replicas: 10 memory-leak blast radius (Pod 1 leaks 16 GB -> Pods 2..10 crash).
- Volume 11 Ch 4 5-Phase A100 80 GB Benchmark: 1, 2, 4, and 8 concurrent notebooks via nvidia-smi dmon -s puctem -n 300.
- Volume 04 Ch 3 CUDA MPS & Ghost OOM Analyzer: EXCLUSIVE_PROCESS, 20% thread cap, CUDA_MPS_PINNED_DEVICE_MEM_LIMIT on a 40 GB A100 at 10 GB used.
- Governance Checklists: 10-field Operating Policy Template, 8-item Contention Evidence Package, and volume-11/labs/lab-01..04 suite.
```

Each line in the scope block points to a model or checklist covered in this chapter.

### Step 1: Run the self-checking time-slicing, MPS and oversubscription lab (tested here)

Run the self-checking lab script from the repository root. It verifies all twenty-five assertions.

```bash
python3 code/part11/time_slicing_mps_oversubscription_lab.py
```

This is the output captured from this repository:

```text
=== Chapter 11.25 Lab: Time-Slicing, CUDA MPS & Oversubscription Governance ===
  [PASS] Volume 11 Ch 4 Primer: 16 GB T4 with replicas: 10 leaves 0 GB when Pod 1 leaks 16 GB, OOM-killing Pods 2..10 (9 pods)
  [PASS] Volume 11 Ch 4 defines 5 replica-ratio test phases (Single tenant, Concurrent active, Burst, Failure/recovery, Upgrade repeat)
  [PASS] A100 80GB baseline (1 notebook, dmon -s puctem -n 300 over 5 min) observes 25% SM, 12GB VRAM, and p99=8ms
  [PASS] A100 80GB with 2 concurrent notebooks observes ~40% SM each, 24GB VRAM, and p99=25ms
  [PASS] A100 80GB with 4 concurrent notebooks observes ~55% SM each, 48GB VRAM (32GB >= 20GB headroom), and p99=120ms -> max safe replicas = 4
  [PASS] A100 80GB with 8 concurrent notebooks hits ~65% SM each, 96GB > 80GB VRAM, p99=500ms, and OOM kill
  [PASS] CUDA MPS with EXCLUSIVE_PROCESS and 5 clients at 20% thread cap sums to 100% spatial SM allocation
  [PASS] Volume 04 Ch 3 Ghost OOM: Client A bursting to 12GB > 8GB CUDA_MPS_PINNED_DEVICE_MEM_LIMIT crashes even when nvidia-smi shows 10GB/40GB
  [PASS] CUDA MPS shares a single GPU fault domain across all connected client processes
  [PASS] Volume 11 Ch 4 Operating Policy Template specifies 10 mandatory fields
  [PASS] Volume 11 Ch 4 Contention Evidence Package specifies 8 time-correlated items
  [PASS] Volume 11 Ch 4 Scenario 3: critical service (p99 < 100ms) misplaced on shared pool degrades to p99 > 300ms
  [PASS] Volume 11 Ch 4 ResourceQuota sets nvidia.com/gpu.shared: '0' and nvidia.com/gpu: 'unlimited' in prod namespaces
  [PASS] Volume 11 Ch 4 documents that DCGM Exporter cannot attribute GPU metrics to individual containers under device-plugin time-slicing
  [PASS] Volume 11 Ch 4 defines a 6-step Safe Rollout Sequence and 5 upgrade validation checks
  [PASS] Volume 04 Ch 3 MPS daemon uses CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps and CUDA_MPS_LOG_DIRECTORY=/tmp/nvidia-log
  [PASS] Generative AI on Kubernetes Ch 3 Examples 3-11/3-12 label nodes with nvidia.com/device-plugin.config=all for time-slicing
  [PASS] Generative AI on Kubernetes Ch 3 appends -SHARED to GFD product label when MIG and time-slicing are combined
  [PASS] Volume 11 Lab 02 configures version: v1, renameByDefault: false, failRequestsGreaterThanOne: true, and replicas: 4
  [PASS] Volume 11 Lab 02 updates node allocatable from 1 to 4 in 30s and logs TIME_SLICE_A_COMPLETE and TIME_SLICE_B_COMPLETE
  [PASS] Volume 11 Lab 03 runs SHARING_RUNTIME_PROBE_COMPLETE and SHARING_NEIGHBOR_PROBE_COMPLETE for 60s
  [PASS] Volume 11 Lab 04 verifies DIAGNOSTIC_GPU_OK and QUOTA_DENIAL_RECOVERY_CHECK
  [PASS] Volume 11 Lab 01 verifies MIG_VALIDATION_COMPLETE across 6 H100 MIG profiles
  [PASS] Volume 11 Ch 1 & Ch 12 Summary separate logical replica allocation from physical reservation and SLO delivery
  [PASS] Volume 11 Ch 7 & Ch 11 align scheduler resource requests with 6-layer contention triage

Summary: 25 passed, 0 failed out of 25 checks.
```

The last line gives the result: 25 passed and 0 failed, so every check held.

### Exercises

Try the six exercises below once the lab passes.

1. On a 16 GB T4 configured with ten replicas, what happens when Pod 1 leaks 16 GB of VRAM? Work through the case with `simulate_t4_ten_replica_memory_leak()` in `code/part11/time_slicing_mps_oversubscription.py`. Then state why Linux memory cgroups do not stop Pod 1.
2. Using `evaluate_a100_timeslicing_envelope()`, list the five test phases in `FIVE_REPLICA_TEST_PHASES`. Then trace SM percentage, combined memory and p99 latency across one, two, four and eight concurrent notebooks on an 80 GB A100. Finish by stating why four replicas is the maximum safe setting.
3. Using `evaluate_cuda_mps_configuration()`, write the commands that start `nvidia-cuda-mps-control` in exclusive process mode with a twenty percent active thread cap. Then explain why Client A crashed with a CUDA out-of-memory error during a 12 GB burst on a 40 GB A100, even though `nvidia-smi` showed only 10 GB in use.
4. Write the device-plugin ConfigMap settings and the production namespace ResourceQuota manifest that keep a latency-sensitive service from landing on a shared pool.
5. List all ten fields in `TEN_OPERATING_POLICY_FIELDS` for a shared development notebook pool.
6. List all eight time-correlated items in `EIGHT_CONTENTION_EVIDENCE_ITEMS`. Then explain how operators work around the DCGM Exporter container-attribution limitation during a shared-pool slowdown.

Keep the lab script open while you work, since most of these exercises reuse its functions.

## Checkpoint questions

<details>
<summary>**1. In Volume 11 Chapter 4, what is the fundamental difference between a logical GPU replica under time-slicing and a hardware MIG instance?**</summary>

If you compare the two, a MIG instance is a slice of the GPU that the hardware itself partitions. The slice includes Streaming Multiprocessors, HBM capacity, L2 cache and memory controllers. A time-sliced replica is only a scheduler admission token for shared access to the whole physical GPU. It provides zero reserved memory, zero guaranteed SM share and zero fault isolation.
</details>

<details>
<summary>**2. On a 16 GB T4 GPU configured with replicas: 10, why don't Linux memory cgroups prevent Pod 1 from consuming all 16 GB of VRAM and crashing Pods 2 through 10?**</summary>

Picture Pod 1 leaking memory on a shared card. Standard Linux memory cgroups track and limit only host system RAM, which the Linux kernel memory management unit manages. They do not govern allocations inside the physical GPU HBM pool. That stays true when ten Pods mount the same `/dev/nvidia0` device node.
</details>

<details>
<summary>**3. What do renameByDefault: true and failRequestsGreaterThanOne: true do in the NVIDIA device-plugin time-slicing ConfigMap?**</summary>

- Setting `renameByDefault: true` advertises time-sliced tokens as `nvidia.com/gpu.shared` instead of `nvidia.com/gpu`. That makes best-effort shared semantics explicit in Pod manifests and ResourceQuotas.
- Setting `failRequestsGreaterThanOne: true` rejects any Pod that requests more than one shared token. This stops users from assuming that two tokens give twice the guaranteed compute or memory.
</details>

<details>
<summary>**4. How does CUDA Multi-Process Service differ architecturally from standard GPU time-slicing?**</summary>

- Time-slicing multiplexes separate per-process CUDA contexts in time, through round-robin context switching. It pauses one process while another runs. That adds context-switch latency, and the SMs stay underutilized when individual kernels are small.
- CUDA MPS runs a proxy daemon with the GPU in exclusive process mode. The daemon funnels multiple client processes into a single shared GPU context. Their kernels then run concurrently, side by side on the SMs.
</details>

<details>
<summary>**5. What environment variables and commands configure CUDA MPS on GPU 0 and cap each client to 20% of active threads?**</summary>

You run these four steps in this order.

1. Export `CUDA_VISIBLE_DEVICES=0`, `CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps` and `CUDA_MPS_LOG_DIRECTORY=/tmp/nvidia-log`.
2. Run `sudo nvidia-smi -i 0 -c EXCLUSIVE_PROCESS` so that only the MPS server accesses the GPU directly.
3. Run `nvidia-cuda-mps-control -d` to start the background control daemon.
4. Run `echo set_default_active_thread_percentage 20 | nvidia-cuda-mps-control` to cap each client to twenty percent of active threads.
</details>

<details>
<summary>**6. Explain the three possible causes of the Ghost OOM on MPS where Container A crashes with CUDA OOM on a 40 GB A100 while nvidia-smi shows only 10 GB used.**</summary>

If you see this on-call, the three causes below explain the gap.

1. A per-client MPS memory ceiling, set with `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT` or `set_default_device_pinned_mem_limit`, was lower than Container A needed during a burst.
2. The ten-gigabyte `nvidia-smi` reading was taken after Container A crashed and released its GPU memory.
3. Neighboring Container B spiked in memory use, then freed its buffers right after causing Container A's allocation to fail.
</details>

<details>
<summary>**7. List the five test phases for measuring a safe time-slicing replica ratio in Volume 11 Chapter 4.**</summary>

You work through the five phases in order.

1. Single tenant: establish normal baseline latency and memory high-water mark.
2. Concurrent active: add neighbors and measure the interference, while every protected SLO stays within its limit.
3. Burst: test queue and admission behavior, so that overload stays bounded and visible.
4. Failure and recovery: test the response to a bad neighbor or a restart, without manual guesswork.
5. Upgrade repeat: re-validate the envelope after driver, runtime or model updates.
</details>

<details>
<summary>**8. Summarize the observed SM utilization, combined memory, and p99 kernel launch latency across 1, 2, 4, and 8 concurrent PyTorch notebooks on an 80 GB A100.**</summary>

The Volume 11 Chapter 4 benchmark sampled one 80 GB A100 for five minutes with `nvidia-smi dmon -s puctem -n 300`.
```text
- 1 notebook:  25% SM, 12 GB / 80 GB memory, p99 = 8 ms.
- 2 notebooks: ~40% SM each, 24 GB / 80 GB memory, p99 = 25 ms.
- 4 notebooks: ~55% SM each, 48 GB / 80 GB memory (32 GB free), p99 = 120 ms (safe replica count = 4 with >= 20 GB headroom).
- 8 notebooks: ~65% SM each, 96 GB > 80 GB memory, p99 = 500 ms, triggering an OOM kill.
```
</details>

<details>
<summary>**9. What are the six operational controls listed in Volume 11 Chapter 4 for protecting a shared time-sliced pool?**</summary>

Use all six controls together, since each one covers a different gap.

1. A separate shared node pool with an explicit resource name, `nvidia.com/gpu.shared`.
2. Namespace quota and admission control to limit a single tenant's allocation burst.
3. Concurrency and request limits in the application, to protect memory and tail latency.
4. Queueing or load shedding, to make overload visible rather than silently slow.
5. Telemetry correlated by workload, to distinguish logical allocation from physical pressure.
6. A dedicated escape hatch to move critical workloads to MIG or whole GPUs during incidents.
</details>

<details>
<summary>**10. Walk through the six steps of the Safe Rollout Sequence for time-slicing in Volume 11 Chapter 4.**</summary>

You work through the six steps in order.

1. Select a noncritical node pool and label it as shared before configuring replicas.
2. Capture a baseline with the same workloads running one at a time and concurrently.
3. Start with a small replica count, and validate allocation, latency, memory use and recovery.
4. Increase density only while the agreed service envelope passes.
5. Publish the shared resource name, workload eligibility, escalation path and exit path to dedicated capacity.
6. Rehearse removal of the shared configuration in a canary, so responders can restore a conservative state.
</details>

<details>
<summary>**11. In Volume 11 Chapter 4 Troubleshooting Scenario 3, how do you diagnose and remediate a critical service that degraded to p99 over 300 ms after landing on a time-sliced pool?**</summary>

- Diagnosis: check the Pod resource requests, run `kubectl exec <pod> -- nvidia-smi` to see several containers sharing the same GPU, and confirm p99 latency above 300 ms on the service `/metrics` endpoint.
- Remediation and prevention: move the deployment to a protected dedicated pool, confirm that latency drops below 100 ms, and apply a ResourceQuota in the production namespace that sets `nvidia.com/gpu.shared: "0"` and `nvidia.com/gpu: "unlimited"`.
</details>

<details>
<summary>**12. What is the documented DCGM Exporter limitation when Kubernetes device-plugin time-slicing is enabled, and how do responders work around it?**</summary>

With device-plugin time-slicing on, `dcgm-exporter` cannot tie GPU-level metrics to individual containers. In that case, you correlate scheduler allocation history, Pod lifecycle events, application request latency metrics, and host-level `nvidia-smi --query-processes` or `nvidia-smi pmon -c 1` snapshots over the incident window.
</details>

<details>
<summary>**13. For each of the five Kubernetes primitives in Volume 11 Chapter 4, state what it contributes and what it cannot do for shared GPUs.**</summary>

- Resource requests and limits reserve a logical allocation token. They do not divide physical GPU memory.
- Node selectors and affinity target the intended node pool. They do not validate workload memory or latency behavior.
- Taints and tolerations restrict access to special nodes. They do not provide tenant hardware isolation.
- ResourceQuota bounds the logical request count by namespace. It does not arbitrate GPU kernel execution.
- PriorityClass influences scheduling and eviction order. It does not create physical GPU capacity.
</details>

<details>
<summary>**14. What are the five validation checks required after an Operator, device-plugin, driver, or node-image upgrade on a time-sliced pool?**</summary>

After an upgrade, you check these five things.

1. Node allocatable resource names and counts, to detect changed sharing semantics.
2. Labels and selectors, to confirm that pool separation stays intact.
3. Namespace policy, to prevent accidental production admission to shared resources.
4. A concurrent smoke test, to detect runtime behavior changes beyond mere scheduling.
5. Dashboard attribution, to confirm that incident correlation evidence stays usable.
</details>

<details>
<summary>**15. List the eight time-correlated items in the Contention Evidence Package in Volume 11 Chapter 4.**</summary>

1. Workload version and request rate.
2. Latency percentiles p50, p95 and p99, alongside queue depth.
3. Pod allocation and placement history.
4. Active-process and memory evidence from `nvidia-smi --query-processes`.
5. Device health, power, thermal and error events.
6. Node and device-plugin configuration and events.
7. Quota and admission decisions.
8. Actions taken and time to recovery.
</details>

<details>
<summary>**16. List the ten fields of the Shared-Pool Operating Policy Template in Volume 11 Chapter 4.**</summary>

Every shared pool you publish needs these ten fields.

1. Shared-pool purpose in one sentence.
2. Eligible workloads and excluded workloads.
3. Advertised shared resource name, such as `nvidia.com/gpu.shared`.
4. Tested replica envelope and its test date.
5. Memory and latency assumptions.
6. Quota scope and admission behavior.
7. Overload action: queue, throttle, shed or evict.
8. Escalation owner.
9. Protected-service escape path.
10. Rollback action for a configuration change.
</details>

<details>
<summary>**17. In Generative AI on Kubernetes Chapter 3, how do you apply a time-slicing profile only to specific nodes rather than the entire cluster?**</summary>

You create the time-slicing ConfigMap in the GPU Operator namespace, and reference it in the ClusterPolicy without setting a global default profile. Then label only the target nodes, with `kubectl label node <node-name> nvidia.com/device-plugin.config=all`.
</details>

<details>
<summary>**18. How can a platform team combine MIG and Time-Slicing on the same GPU, and what label suffix does GFD advertise?**</summary>

If you combine them, start by partitioning the physical GPU into hardware-isolated MIG instances, which enforce hard HBM walls between departments. Then enable Time-Slicing on the MIG resource names, so trusted Pods from the same team can share a single MIG slice. GPU Feature Discovery appends `-SHARED` to the product label, which gives values such as `...-MIG-3g.20gb-SHARED`.
</details>

<details>
<summary>**19. What five questions must a platform architect ask a service owner before admitting their workload to a time-sliced pool?**</summary>

Before you admit a workload, ask the service owner these five questions.

1. Can requests queue or be rejected safely?
2. What is the maximum acceptable latency during peer activity?
3. What memory envelope was observed at peak input?
4. Which workload may be throttled first during contention?
5. Where does the service move during a shared-device incident?
</details>

<details>
<summary>**20. Compare a time-sliced OOM incident with a MIG-profile OOM incident.**</summary>

When you compare them, start with a MIG-profile OOM incident. There, the hardware memory controller enforces a strict partition boundary. Only the Pod inside that GPU instance hits a CUDA out-of-memory error. Sibling tenants on other MIG slices keep running without impact. A time-sliced OOM incident works differently. All Pods share one unprotected HBM pool, so one runaway Pod can make unrelated neighbor Pods fail allocations and crash at the same time.
</details>

## Sources and review notes

### Primary sources read in full for this chapter

Each source file and book chapter below was read in full. Its content was carried into the prose, tables, diagrams and self-checking lab for this chapter.

```text
Primary Source Inventory and Coverage Map (11.25):
1. Author's Volume 11 and Volume 4 notes (all 11 mapped nvidia-devops files in brief.py 11.25):
   - nvidia-zero-to-hero/volume-11/chapter-04-time-slicing-and-oversubscription.md
     (16 GB T4 with replicas: 10 OOM-killing Pods 2..10, renameByDefault: true -> nvidia.com/gpu.shared,
      failRequestsGreaterThanOne: true, 6-step safe rollout sequence, 5-phase replica-ratio test,
      80 GB A100 1/2/4/8 notebook measurement via nvidia-smi dmon -s puctem -n 300 with replicas: 4 and 20 GB headroom,
      Scenario 3 p99 < 100 ms -> > 300 ms misplacement & ResourceQuota nvidia.com/gpu.shared: "0",
      Scenario 4 DCGM Exporter attribution limitation, 5 upgrade checks, 8-item contention evidence package,
      and 10-field operating policy template).
   - volume-04/03-gpu-sharing-telemetry-masterclass.md
     (Part 1.1 time-slicing cgroups warning, Part 1.2 CUDA MPS nvidia-cuda-mps-control -d, EXCLUSIVE_PROCESS,
      set_default_active_thread_percentage 20, CUDA_MPS_PINNED_DEVICE_MEM_LIMIT, and Part 6 Scenario 1 Ghost OOM
      on MPS at 10 GB / 40 GB on A100).
   - nvidia-zero-to-hero/volume-11/chapter-01-why-gpu-sharing-exists.md
   - nvidia-zero-to-hero/volume-11/chapter-07-kubernetes-scheduling-for-shared-gpus.md
   - nvidia-zero-to-hero/volume-11/chapter-11-production-troubleshooting.md
   - nvidia-zero-to-hero/volume-11/chapter-12-volume-11-summary.md
   - nvidia-zero-to-hero/volume-11/index.md
   - nvidia-zero-to-hero/volume-11/labs/lab-01-configure-and-validate-mig.md
   - nvidia-zero-to-hero/volume-11/labs/lab-02-configure-kubernetes-gpu-time-slicing.md
   - nvidia-zero-to-hero/volume-11/labs/lab-03-compare-sharing-performance-and-isolation.md
   - nvidia-zero-to-hero/volume-11/labs/lab-04-troubleshoot-a-multi-tenant-gpu-node.md
2. Book sources from the local TOON-RAG corpus (mapped in brief.py 11.25 as GAK 3):
   - Roland Huß et al., Generative AI on Kubernetes (O'Reilly, 2026), Chapter 3
     (Kubernetes and GPUs, Sub-GPU Allocation, Time slicing, Examples 3-11 & 3-12 time-slicing-config-all
      and nvidia.com/device-plugin.config=all, and -SHARED MIG + time-slicing label).
```

### Related source files mapped in MIGRATION_MAP.md

- All eleven mapped `nvidia-devops` files for Chapter 11.25 are cited and covered in the inventory above.

### Run here

- Verified locally. If you run `python3 code/part11/time_slicing_mps_oversubscription_lab.py`, you should see all checks pass.

### Explicitly labelled inferences

- The Ghost OOM simulation in `code/part11/time_slicing_mps_oversubscription.py` compares an eight-gigabyte pinned memory limit with a twelve-gigabyte Client A burst on a forty-gigabyte A100. That comparison is a concrete numerical illustration of the Volume 4 Chapter 3 diagnosis, and it is labelled as an inference.

### Not verified on live hardware

- Everything in this list is marked `(untested here)` because it did not run on live hardware. That covers all `nvidia-cuda-mps-control` items (`MpsServerConfig`, `8000` MiB limits), the `nvidia-smi dmon` and `nvidia-smi pmon` commands, and the `kubectl` commands. The `kubectl` items are `nvidia.com/gpu.product`, `1g.10gb`, `LimitRange`, request/limit and requests/limits, taint/toleration and taints/tolerations, `kueue.x-k8s.io/v1beta1` and `resource.k8s.io/v1`. They come from `chapter-07-kubernetes-scheduling-for-shared-gpus.md`, `chapter-11-production-troubleshooting.md` and `chapter-12-volume-11-summary.md`.

### Not in the corpus

- Experimental Kubernetes device-plugin MPS daemon auto-injection Helm flags are not in the local corpus. This chapter uses the documented host `nvidia-cuda-mps-control` workflow and the device-plugin `timeSlicing` ConfigMap from the primary sources.

### Corrections to the author's notes

- Validation pass 2026-10-26: `validate_chapter.py` and `check_coverage.py` pass with zero warnings. The YAML manifests and cluster commands are marked untested here and were not applied to a live cluster. Custom resource API versions change between releases, so check them against your installed operator version. Console outputs quoted from the Volume notes are illustrative unless marked tested here. The A100 concurrency benchmark in Question 8 comes from the Volume 11 Chapter 4 note and has no live hardware reproduction here.
