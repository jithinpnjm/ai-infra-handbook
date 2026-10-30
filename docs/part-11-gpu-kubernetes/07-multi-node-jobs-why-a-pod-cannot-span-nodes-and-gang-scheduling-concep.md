---
id: "c11-07"
title: "11.7 Multi-node jobs: why a pod cannot span nodes, and gang scheduling concepts"
sidebar_label: "11.7 Multi-node jobs: why a pod cannot span nodes, and gang scheduling concepts"
sidebar_position: 7
description: "Why a Kubernetes Pod is bounded to a single node, how partial Pod placement deadlocks PyTorch rendezvous barriers, and how gang scheduling, bin packing, descheduling, and backfill queues solve multi-node GPU orchestration."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 11.7 Multi-node jobs: why a pod cannot span nodes, and gang scheduling concepts

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE and local Python 3 simulation lab |
| Part | Part 11: GPUs on Kubernetes, scheduling and virtualization |
| Sources used | `volume-06/04-distributed-orchestration-masterclass.md`; Roland Huß et al., *Generative AI on Kubernetes* (O'Reilly, 2026, Ch. 3, Ch. 7); *Kubernetes for Generative AI Solutions* (Packt, 2025, Ch. 10); Chris Fregly, *AI Systems Performance Engineering* (O'Reilly, 2025, Ch. 3) |
| Coverage file | `planning/coverage/chapters/11-07.md` |

## Why this matters for AI infrastructure

Every single-node Kubernetes concept from the previous chapters hits a hard architectural wall when a model or training run exceeds the capacity of one server. A Kubernetes Pod cannot span multiple nodes. When a researcher submits a single Pod requesting 64 GPUs on a cluster of 8-GPU servers, the Pod stays Pending forever because no single machine holds 64 GPUs.

In the Kubernetes object model, a Pod is the smallest atomic unit of placement. Its `spec.nodeName` field is a single string naming one Node. Every container inside that Pod shares a single Linux network namespace, an IPC namespace, and a local kubelet lifecycle. Physical GPU servers typically hold at most 8 or 16 GPUs per baseboard. Consequently, any large training job or sharded inference pipeline must be split into a group of coordinated Pods across multiple nodes.

Decomposing one logical training run into multiple Pods immediately exposes three failure modes between Kubernetes microservice scheduling and distributed AI workloads. First, standard per-Pod scheduling creates partial-allocation rendezvous deadlocks when only a subset of the required Pods can fit on the cluster. Second, adding strict all-or-nothing gang scheduling introduces head-of-line blocking unless the queue supports wall-time backfill scheduling. Third, unthrottled job submission bursts and oversized gang requests can exhaust etcd memory and stall the cluster control plane.

```text
Multi-Node Scheduling Failure Modes and Scales:
- Single-Pod node limit: 8 or 16 GPUs per baseboard (a 64-GPU or 1,024-GPU job or 175B+ LLM on two 8-GPU 80 GB A100 nodes cannot fit in 1 Pod).
- 7-of-8 partial placement deadlock: 8-Pod (64-GPU) job on 56 free GPUs (7 nodes) places Pods 0..6 and leaves Pod 7 Pending.
- Deadlock cost: 56 GPUs sit at 0% compute utilization, burning $140/hour at $20/hour per 8-GPU node ($10-$30/hour typical range).
- Two-job mutual deadlock: Two 8-Pod (64-GPU) jobs on a 12-node (96-GPU) cluster split 6 + 6 nodes (48 + 48 GPUs), deadlocking 100% of the cluster.
- Head-of-line blocking: 1,024-GPU (128-node) head job waiting 45 minutes for 24 GPUs holds 1,000 free GPUs idle (750 GPU-hours wasted).
- Thundering herd & impossible gang: 50,000 jobs in 2 seconds (25,000 jobs/s) or minAvailable: 1000 on a 500-node cluster OOM-kills etcd/kube-apiserver.
```

This chapter explains why a Pod is bounded to one node and how PyTorch rendezvous barriers couple multi-Pod jobs. We then examine how gang scheduling via PodGroup, Kueue, Volcano, NVIDIA KAI Scheduler, and KEP-4671 eliminates partial-allocation deadlocks. Finally, we cover bin packing, descheduling, backfill queues, Slurm integration, shared checkpoint storage, and network policies.

## Prerequisites and outcomes

### Prerequisites
- Completion of Chapters 11.1 through 11.6, especially the four placement questions of capacity, eligibility, locality, and coordination.
- Basic familiarity with distributed training concepts including worker ranks, world size, data parallelism, and model parallelism.

### Outcomes
After completing this chapter, you will be able to:
- Explain why a Kubernetes Pod cannot span multiple Nodes and decompose a multi-node GPU workload into coordinated worker Pods.
- Trace the four steps of a PyTorch distributed rendezvous barrier and quantify the waste of partial placements and mutual deadlocks.
- Compare the four Kubernetes gang-scheduling architectures alongside KEP-4671 Workload support and protect running gangs with a PodDisruptionBudget.
- Configure kube-scheduler bin packing with MostAllocated weights and pair it safely with the Kubernetes Descheduler without eviction loops.
- Solve queue head-of-line blocking using wall-time backfill scheduling and prevent control-plane crashes from thundering herds and oversized gangs.
- Size shared ReadWriteMany checkpoint storage for fine-tuning runs and enforce zero-trust NetworkPolicy isolation around PyTorch and Ray clusters.

## Concepts: basics to intermediate to advanced

### 1. Basics: Why a Pod cannot span nodes and why microservices scheduling breaks batch AI

#### Why a Kubernetes Pod is strictly bound to one Node
Engineers new to Kubernetes often ask why a single Pod manifest cannot request 64 GPUs across an 8-node cluster. When a user tries this, the Pod remains permanently Pending with an insufficient GPU event. The user is blocked because Kubernetes never splits a single Pod across machines.

In the Kubernetes architecture, a Pod is a co-located execution sandbox managed by a single kubelet on a single Node. First, when kube-scheduler binds a Pod, it writes a single host string into `spec.nodeName`. Only the kubelet watching that specific node creates the Pod sandbox. Second, all containers inside a Pod share one Linux network namespace and one IPC namespace for `/dev/shm` shared memory. Sharing a single kernel IPC or network namespace across separate physical servers is impossible without a distributed operating system hypervisor.

Third, during the Filter phase, the NodeResourcesFit plugin checks whether one single node has enough allocatable GPUs to satisfy the Pod request. As shown in Chapter 11.6, even requesting two MIG slices requires a single node that holds both free slices simultaneously. If two nodes each hold 1 free slice, a Pod requesting 2 slices stays Pending.

```text
Single-Node Pod Resource Boundary Examples:
- Full-GPU request: Pod requesting nvidia.com/gpu: 64 on 8-GPU nodes -> Pending (Insufficient nvidia.com/gpu).
- Multi-slice MIG request: Pod requesting nvidia.com/mig-2g.45gb: "2" (~76 SMs) when two nodes each have 1 free slice -> Pending.
- Multi-node decomposition: 64-GPU training job or 175B-parameter inference server -> 8 coordinated Pods (1 Pod x 8 GPUs per node).
```

Therefore, any workload that needs more GPUs than exist on one physical server must run as multiple Pods across the network. Each worker Pod typically claims all 8 GPUs on its host node and coordinates with its peers over InfiniBand, RoCE, or Ethernet.

#### The paradigm shift: Microservices vs Distributed AI Batch Jobs
When platform teams run multi-Pod training jobs on a default Kubernetes cluster, they quickly hit operational friction. Kubernetes was originally engineered for stateless web microservices where replicas are independent and interchangeable. Distributed AI training behaves like a tightly coupled supercomputer job where every replica must run simultaneously or the entire job stalls.

| Architectural Dimension | Traditional Microservices (Default Kubernetes) | Distributed AI Training & Multi-Node Inference |
|---|---|---|
| **Pod Lifecycle** | Long-running servers; restart individual failed Pod in place | Run-to-completion batch jobs or sharded model groups; exit code `0` and coordinated checkpoint recovery govern lifecycle |
| **Pod Coupling & Scheduling** | **Independent per-Pod scheduling:** `3` of `4` web replicas can serve `75%` of traffic | **Gang Scheduling (All-or-Nothing):** `7` of `8` training Pods serve **`0%`** of traffic and deadlock at the rendezvous barrier |
| **When Capacity is Full** | Immediate placement or `Pending` Pod churn in `etcd` | Hold the entire job suspended in a **Queue** (`Kueue` / `Slurm`) until full quota and topology are available |
| **Preemption Model** | Node-pressure eviction (`DiskPressure`, `MemoryPressure`) | Priority, cohort borrowing reclamation (`reclaimWithinCohort`), and fair-share preemption with checkpoint grace periods |
| **Network Traffic Pattern** | Primarily **North-South** client-to-API ingress and light East-West RPCs over TCP/IP CNI overlays | Massive synchronous **East-West** collective bursts (`AllReduce`, `AllGather`, `ReduceScatter`) requiring `200–400 Gbps` InfiniBand / RoCE with GPUDirect RDMA (`40%–60%` latency reduction) |

#### PyTorch Rendezvous and the 7-of-8 Partial-Allocation Deadlock
Why cannot 7 out of 8 training Pods make partial progress while waiting for the 8th Pod to schedule? If 7 Pods start on 7 nodes while the 8th Pod waits in Pending, all 56 allocated GPUs sit at 0% compute utilization and burn $140 per hour for zero training steps.

Distributed training frameworks such as PyTorch DDP, FSDP, DeepSpeed, and Megatron-LM execute a synchronous rendezvous and collective communication loop. First, at startup, every worker connects to a shared rendezvous endpoint on `MASTER_ADDR` and `MASTER_PORT` using a c10d TCP store or etcd. Second, the rendezvous store waits until all expected participants from rank 0 through `world_size - 1` register. Third, an atomic barrier blocks every worker inside `torch.distributed.init_process_group()` until all `world_size` workers arrive.

Fourth, even after initialization completes, every training step executes synchronous collective operations across the gang. Data parallelism runs AllReduce to average tens of gigabytes of gradients, while tensor parallelism and FSDP run per-layer AllGather and ReduceScatter collectives. If a single worker is missing or stalls, every other worker blocks at the collective barrier.

```mermaid
flowchart TD
    subgraph Standard["Standard Per-Pod Scheduling (Deadlock)"]
        J1["Submit 8-Pod Job (64 GPUs)"] --> S1["Default kube-scheduler (56 GPUs Free)"]
        S1 -->|"Places Pods 0..6"| R1["7 Pods Running (56 GPUs Allocated)"]
        S1 -->|"Pod 7 Pending"| P1["Waiting for 8th Node"]
        R1 -->|"Blocked at PyTorch Rendezvous Barrier"| W1["56 GPUs Idle at 0% Compute ($140/hr wasted)"]
    end
    subgraph Gang["Gang Scheduling / Coscheduling (All-or-Nothing)"]
        J2["Submit 8-Pod Job (minMember / minAvailable: 8)"] --> Q2{"Are all 64 GPUs (8 Nodes) Available?"}
        Q2 -->|"No (only 56 GPUs free)"| Hold["Hold all 8 Pods in Queue (0 GPUs reserved; 56 GPUs free for other jobs)"]
        Q2 -->|"Yes (64 GPUs free)"| Start["Bind all 8 Pods Atomically -> Rendezvous Succeeds Immediately"]
    end
```

Worse still is the two-job mutual deadlock on a shared cluster. Suppose a cluster has 12 nodes with 96 GPUs free, and two researchers submit 8-node training jobs requesting 64 GPUs each. Under default per-Pod scheduling, Job A claims 6 nodes and waits for 2 more. Job B claims the other 6 nodes and also waits for 2 more. Neither job can ever reach 8 nodes, and all 96 GPUs across the cluster are deadlocked forever until an operator deletes one job.

---

### 2. Intermediate: Gang scheduling architectures, bin packing, and the Descheduler

#### Gang scheduling and the PodGroup contract
To prevent partial-allocation waste and mutual deadlocks, the cluster scheduler must stop treating multi-node training Pods as independent microservices. Without group awareness, any partially placed job strands expensive GPUs and blocks other tenants from running smaller workloads.

Gang scheduling, also called coscheduling, enforces an all-or-nothing placement contract across a group of Pods. The scheduler holds all Pods belonging to a group in a pending or reserve state. It binds them to nodes only when the entire minimum group can be placed simultaneously within a configured timeout. Four primary gang-scheduling solutions are used in production Kubernetes today, alongside the upstream KEP-4671 proposal for a native Workload API.

| Solution | Architectural Layer | Gang & Topology Mechanism | Best Production Fit |
|---|---|---|---|
| **1. Coscheduling Plugin (`PodGroup` CRD, `scheduling.x-k8s.io/v1alpha1`)** | Scheduler extension plugin inside `kube-scheduler` (`scheduler-plugins`) | Groups Pods labeled `scheduling.x-k8s.io/pod-group: <name>`; holds binding until `minMember` Pods fit within `scheduleTimeoutSeconds: 300`. No native topology or quota management. | Existing clusters wanting lightweight all-or-nothing gang scheduling without replacing `kube-scheduler`. |
| **2. Kueue (`kueue.x-k8s.io/v1beta1`)** | Job-level **Admission Controller** & Queue Manager sitting above the scheduler | Suspends jobs until `ClusterQueue` / `LocalQueue` has quota; evaluates ordered `ResourceFlavor`s (`gpu-nvlink-infiniband` before `gpu-standard-ethernet`) and `cohort` borrowing (`nominalQuota: 10`, `borrowingLimit: 22`). | Multi-tenant GPU-as-a-Service (`GPUaaS`) needing hierarchical quotas, cohort borrowing, priority preemption (`WorkloadPriorityClass`), and compatibility with `kube-scheduler`, KAI, or Volcano. |
| **3. NVIDIA KAI Scheduler (`kai.run.ai/v1`)** | Full alternative GPU scheduler open-sourced from Run:ai by NVIDIA | Native gang scheduling (`schedulerName: kai-scheduler`) + `Project` quotas (`gpuQuota: 8`) + fractional/time-sliced GPUs + deep NVLink/NVSwitch/InfiniBand topology placement. | Large-scale NVIDIA GPU clusters (`100s–1,000s` of GPUs) requiring unified gang scheduling, fractional sharing, and hardware topology optimization. |
| **4. Volcano (`batch.volcano.sh/v1alpha1`)** | Monolithic batch scheduler (`schedulerName: volcano`) | Replaces or complements `kube-scheduler` with `Job`, `PodGroup` (`minAvailable: 8`), `Queue`, `RestartJob` policies on `PodEvicted`, backfill, and topology plugins. | HPC-style Kubernetes clusters running mixed PyTorch, MPI, Ray, and Apache Spark batch workloads. |

In enterprise production environments, platform teams often layer Kueue on top of a gang-aware scheduler or workload operator. Common workload operators include Kubeflow PyTorchJob, TrainJob, and LeaderWorkerSet for multi-node sharded LLM inference. Kueue governs which job is admitted and which hardware tier it may consume. Once Kueue unsuspends the job, the underlying scheduler executes atomic gang binding and intra-rack placement.

#### Resource Bin Packing vs Default Spreading
Even with gang scheduling enabled, default Kubernetes node scoring fragments GPU capacity across the cluster. By default, the NodeResourcesFit plugin in kube-scheduler uses the LeastAllocated strategy. That strategy spreads Pods across as many nodes as possible so a hardware failure impacts fewer replicas.

For GPU clusters where nodes cost $10 to $30 per hour, spreading small jobs across nodes is a costly anti-pattern. Spreading 1-GPU or 2-GPU jobs across 8-GPU servers leaves every node partially occupied. Fragmentation blocks 4-GPU or 8-GPU jobs from finding contiguous free nodes and prevents the Cluster Autoscaler from terminating empty machines. Configuring a `binpack-scheduler` profile with `MostAllocated` and a weight of 5 on `nvidia.com/gpu` versus 1 on CPU and memory packs GPU Pods onto fuller nodes.

```text
MostAllocated Bin-Packing Node Score Formula (Weights: GPU = 5, CPU = 1, Memory = 1):
- Node 1 (6/8 GPUs = 75%, 32/64 CPUs = 50%, 256/512 GiB = 50%): (75*5 + 50*1 + 50*1) / 7 = 67.86 (Selected)
- Node 2 (2/8 GPUs = 25%, 48/64 CPUs = 75%, 384/512 GiB = 75%): (25*5 + 75*1 + 75*1) / 7 = 39.29
```

#### Dynamic re-optimization with the Kubernetes Descheduler
Initial bin packing degrades over time as short jobs finish at different rates and leave fragmented "Swiss cheese" nodes across the cluster. When nodes become fragmented, multi-GPU training jobs sit queued even though total free GPUs across the cluster exceed the job request.

The Kubernetes Descheduler runs periodically as a CronJob or Deployment to evict sub-optimally placed Pods so kube-scheduler can pack them cleanly. However, running the Descheduler on a GPU cluster without strict guardrails can tear down active training gangs or trigger infinite eviction loops. You must enforce two rules whenever the Descheduler is active on GPU nodes.

First, protect every running gang job with a PodDisruptionBudget. Evicting one worker Pod from a running 4-node LLM training job breaks the rendezvous group and forces an expensive checkpoint-and-resume cycle. Attaching a PodDisruptionBudget with `minAvailable: 4` matching `scheduling.x-k8s.io/pod-group: llm-training-group` prevents the Descheduler from evicting any active gang worker.

Second, align the Descheduler plugin strategy with the kube-scheduler scoring strategy. The `HighNodeUtilization` plugin evicts Pods from underutilized nodes so a `MostAllocated` bin-packing scheduler can pack them onto fuller nodes. Pairing `HighNodeUtilization` with the default `LeastAllocated` scheduler causes an infinite eviction loop because `LeastAllocated` schedules evicted Pods right back onto lightly loaded nodes.

| Descheduler Plugin | Required `kube-scheduler` Strategy | Behavior When Misaligned |
|---|---|---|
| **`HighNodeUtilization`** | **`MostAllocated`** (Bin Packing) | Infinite eviction loop if paired with `LeastAllocated` |
| **`LowNodeUtilization`** | **`LeastAllocated`** (Spreading) | Infinite eviction loop if paired with `MostAllocated` |
| **Both Enabled Together** | **Invalid in all cases** | Immediate self-contradictory eviction churn |

---

### 3. Advanced: Head-of-line blocking, backfill, thundering herds, Slurm/Slinky, storage, and security

#### 1. Head-of-Line Blocking and Backfill Scheduling
Once strict gang scheduling is enabled, a naive First-In-First-Out queue creates Head-of-Line blocking whenever a massive job reaches the front of the line. Suppose a 1,024-GPU job sits at the head of the queue when 1,000 GPUs are free and 24 GPUs will finish in 45 minutes. Strict FIFO holds those 1,000 GPUs idle for 45 minutes, wasting 750 GPU-hours while short 8-GPU and 16-GPU jobs wait behind the head job.

Backfill scheduling in Slurm (`SchedulerType=sched/backfill`), Volcano, and KAI resolves this starvation without delaying the head job. The scheduler calculates the shadow start time of the 1,024-GPU head job at `T + 45` minutes. It then scans the queue behind the head job and allows smaller jobs to run immediately if their declared `TimeLimit` finishes within 45 minutes.

```text
Backfill Scheduling Scenario (Head Job: 1,024 GPUs; Free: 1,000 GPUs; Missing 24 GPUs free in 45 min):
- Candidate short-8gpu-a (8 GPUs, TimeLimit = 30 min <= 45 min): ADMITTED via backfill.
- Candidate short-16gpu-d (16 GPUs, TimeLimit = 45 min <= 45 min): ADMITTED via backfill (976 free GPUs remain).
- Candidate long-8gpu-b (8 GPUs, TimeLimit = 90 min > 45 min): BLOCKED (would delay the 1,024-GPU head job).
- Candidate no-timelimit-c (8 GPUs, TimeLimit = None / NO_VAL): BLOCKED (cannot prove completion before T + 45 min).
```

Backfill math is impossible if users omit job runtimes. If a job has no maximum wall time (`time_limit == NO_VAL`), the scheduler cannot prove it will finish before the head job starts. Production AI factories therefore enforce mandatory wall-clock time limits via Kubernetes admission webhooks or Slurm `job_submit` plugins returning `ESLURM_INVALID_TIME_LIMIT`.

#### 2. Control-Plane Thundering Herds and Impossible Gangs
At AI factory scale, careless user submission scripts routinely take down cluster control planes through two failure patterns. In the first pattern, a user loop submits 50,000 individual hyperparameter sweep jobs in 2 seconds. In Kubernetes, creating 50,000 Pod objects overwhelms etcd Raft consensus and kube-apiserver memory. In Slurm, 50,000 `sbatch` RPCs saturate `slurmctld` state locks on one CPU core, causing `slurmd` pings to time out and flip healthy nodes to `UNKNOWN`.

To prevent thundering-herd lockups, platform teams enforce API Priority and Fairness alongside JobSet or Indexed Job completions in Kubernetes. In Slurm, administrators require Job Arrays (`sbatch --array=1-50000`) and raise `MaxArraySize` above its default of 1001 in `slurm.conf` alongside `MaxJobCount=500000` and `MinJobAge=300`. A `job_submit.lua` or C `job_submit` plugin rejects rapid single-job loops automatically.

In the second pattern, a user submits a Volcano Job with `minAvailable: 1000` on a cluster that only has 500 physical nodes. If all 1,000 Pods are created directly in kube-apiserver, the gang condition can never be satisfied. The 1,000 Pending Pods churn continuously in scheduler retry loops and event emission until etcd and kube-apiserver crash with `MemoryPressure` OOM.

To prevent impossible gangs from crashing etcd, gate all batch job creation with Kueue (`kueue.x-k8s.io/queue-name`). Kueue keeps the job suspended as a single lightweight Workload object (`reason: InsufficientQuota`) without creating a single Pod in etcd until quota is available. Admission webhooks also reject any job whose `minAvailable` or `min_nodes > 16` request exceeds the target partition or cluster capacity.

#### 3. Slurm vs Kubernetes and Hybrid Orchestration
Many supercomputing centers run Slurm alongside or inside Kubernetes to orchestrate large-scale training runs. Slurm uses four lightweight components: the `slurmctld` central controller, the `slurmd` compute node daemon, the `slurmdbd` accounting daemon, and the `MUNGE` authentication service. Separating `slurmdbd` from `slurmctld` ensures that MariaDB or MySQL database latency never blocks the main scheduling loop.

```text
Reference 128-Node DGX H100 Slurm & MPI Configuration (volume-06):
- Node spec: NodeName=dgx-h100-[001-128] CPUs=224 Sockets=2 CoresPerSocket=56 ThreadsPerCore=2 RealMemory=2000000 Gres=gpu:h100:8 (1,024 H100 GPUs).
- Scheduler & tracking: SelectType=select/cons_tres, TopologyPlugin=topology/tree, ProctrackType=proctrack/cgroup, MessageTimeout=30, SlurmdTimeout=120.
- NUMA GRES mapping (gres.conf): AutoDetect=nvml or explicit physical core ranges COREs=0-27, 28-55, 56-83, 84-111 across 112 physical cores.
- Job launch: srun --mpi=pmix -n 1024 ./train_script or Kubeflow MPIJob (2 Worker pods x 8 slotsPerWorker) running mpirun -np 16 all_reduce_perf -b 8 -e 128M -f 2.
```

To bridge Slurm and Kubernetes cleanly, SchedMD provides Slinky, which includes a Kubernetes Slurm Operator, a REST client, and a Prometheus exporter. Another pattern is Sunk or Virtual Kubelet, which exposes a Slurm cluster as a virtual Kubernetes node that translates Kubernetes Jobs into `sbatch` submissions. Never run unpartitioned co-resident `kubelet` and `slurmd` daemons claiming the same 8 GPUs on one host. Without static node partitioning, MIG slices, and disjoint `slurmstepd` versus `kubepods` cgroups, both schedulers will double-book GPUs and trigger immediate CUDA OOM crashes.

#### 4. High-Speed Collectives, Checkpoint Storms, RWX Storage Sizing, and Zero-Trust Security
Multi-node jobs also stress East-West networks, shared storage, and cluster security boundaries. During distributed training, standard 10 to 100 Gbps TCP/IP Ethernet suffices for 2 to 8 data-parallel nodes when communication stays below 15% of step time. Once communication exceeds 20% to 25% of step time, clusters require 200 to 400 Gbps InfiniBand with `MTU 4,096` or RoCEv2 with GPUDirect RDMA.

```text
Multus Secondary RDMA Pod Environment & Storage Sizing Parameters (GAK Ch. 7):
- Secondary network: Multus IPoIB / RoCEv2 subnet 10.0.0.0/24 via whereabouts IPAM; Pod requests rdma/hca: 2 and Linux capability IPC_LOCK.
- GPUDirect RDMA: Reduces collective latency by 40% to 60% over RoCEv2 (100-400 Gbps) and InfiniBand (200-400 Gbps).
- NCCL environment: NCCL_DEBUG=INFO, NCCL_IB_HCA="mlx5_0,mlx5_1", NCCL_IB_GID_INDEX="3" (RoCEv2), NCCL_NET_GDR_LEVEL="5", NCCL_SOCKET_IFNAME="net1".
- RWX storage formula: Storage Required = 2 * base_model_size + checkpoint_overhead.
- Llama 3.1 8B LoRA: 2 * 16 GB base weights + 68 GB checkpoint history = 100 GB on RWX storage.
- 70B full fine-tuning: 2 * 140 GB base weights + 220 GB+ optimizer/checkpoint overhead = 500 GB+ on RWX storage.
- Ray head node NetworkPolicy TCP ports: 6379 (Ray GCS), 8265 (Ray dashboard via oauth2-proxy), 10001 (Ray client server).
```

When a 10,000-GPU gang job writes a checkpoint simultaneously, storage I/O stalls can block every GPU in the cluster. Production platforms combine S3, GCS, or MinIO object storage for datasets with local NVMe burst buffers (`burst_buffer/datawarp` or CSI scratch volumes) for write spikes. Shared ReadWriteMany (`RWX`) filesystems such as CephFS, Lustre, WEKA, VAST, EFS, or Filestore let resumed Pods on any node read the latest checkpoint. Finally, because PyTorch Distributed and Ray use `cloudpickle` serialization without built-in authentication, wrap every job in a default-deny ingress NetworkPolicy. Allow only intra-job pod traffic and restrict Ray head node ports 6379, 8265, and 10001 to authorized internal pods.

## Commands and configurations that matter

### 1. Configuring kube-scheduler for GPU Bin Packing

```yaml
# binpack-scheduler-config.yaml (untested here)
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: binpack-scheduler
    pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
            resources:
              - name: nvidia.com/gpu
                weight: 5
              - name: cpu
                weight: 1
              - name: memory
                weight: 1
```

### 2. Defining a Coscheduling PodGroup and protecting it with a PodDisruptionBudget

```yaml
# podgroup-and-pdb.yaml (untested here)
apiVersion: scheduling.x-k8s.io/v1alpha1
kind: PodGroup
metadata:
  name: llm-training-group
spec:
  minMember: 4
  scheduleTimeoutSeconds: 300
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: llm-training-pdb
spec:
  minAvailable: 4
  selector:
    matchLabels:
      scheduling.x-k8s.io/pod-group: llm-training-group
---
apiVersion: v1
kind: Pod
metadata:
  name: llm-training-0
  labels:
    scheduling.x-k8s.io/pod-group: llm-training-group
    job-role: leader
spec:
  schedulerName: default-scheduler
  containers:
    - name: trainer
      image: nvcr.io/nvidia/pytorch:24.08-py3
      resources:
        limits:
          nvidia.com/gpu: 8
```

### 3. Volcano Gang Job and Kubeflow MPIJob

```yaml
# volcano-gang-job.yaml (untested here)
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata:
  name: pytorch-training-job
spec:
  minAvailable: 8
  schedulerName: volcano
  policies:
    - event: PodEvicted
      action: RestartJob
  tasks:
    - replicas: 8
      name: worker
      template:
        spec:
          containers:
            - name: pytorch
              image: nvcr.io/nvidia/pytorch:23.10-py3
              resources:
                limits:
                  nvidia.com/gpu: 8
```

## How it fails

| Failure mode | Exact symptom & command evidence | Root cause boundary | Remediation |
|---|---|---|---|
| **1. `7`-of-`8` Partial-Allocation Rendezvous Deadlock (`56` GPUs at `0%` compute)** | An `8`-Pod (`64`-GPU) `PyTorchJob` shows `7` Pods `Running` (`56` GPUs allocated) and `1` Pod `Pending` (`Insufficient nvidia.com/gpu`). `DCGM_FI_DEV_GPU_UTIL` on all `56` GPUs is `0%`, and `kubectl logs` on rank `0` hangs at `Waiting for 1 more peers in c10d TCPStore`. | **Missing Gang Scheduling Boundary:** Default `kube-scheduler` placed `7` Pods independently when only `56` GPUs were free; PyTorch's atomic rendezvous barrier blocks until all `8` ranks connect. | Enable gang scheduling (`PodGroup` with `minMember: 8`, `Kueue`, `Volcano` `minAvailable: 8`, or `kai-scheduler`) so `0` Pods are bound until all `64` GPUs are available simultaneously. |
| **2. Descheduler infinite eviction loop on GPU training nodes** | Prometheus shows `descheduler_pods_evicted` climbing continuously every CronJob run, training jobs repeatedly restart from checkpoints, yet node consolidation never improves. | **Scheduler / Descheduler Strategy Mismatch:** `HighNodeUtilization` was enabled in the Descheduler while `kube-scheduler` remained on default `LeastAllocated`, or both `HighNodeUtilization` and `LowNodeUtilization` were enabled. | Pair `HighNodeUtilization` strictly with `MostAllocated` (`binpack-scheduler`), never enable `HighNodeUtilization` and `LowNodeUtilization` together, and protect running gangs with a `PodDisruptionBudget` (`minAvailable: 4`). |
| **3. `kube-apiserver` / `etcd` OOM crash during `1,000`-Pod gang submission** | `kube-apiserver` restarts repeatedly and `kubectl` times out. Master nodes report `MemoryPressure` and `etcd` DB size spikes after a user submits a Volcano Job with `minAvailable: 1000` on a `500`-node cluster. | **Un-gated Oversize Gang Churn:** Creating `1,000` unschedulable Pending Pods directly in the API server causes continuous scheduler and controller retry events that exhaust `etcd` watch caches. | Delete the offending `Job`, place **Kueue** in front of batch workloads so jobs remain suspended as a single `Workload` CR (`InsufficientQuota`) until capacity exists, and reject `minAvailable > cluster_capacity` via an admission webhook. |
| **4. `slurmctld` hang and healthy nodes flipping to `UNKNOWN` during `10k`–`50k` job burst** | `sbatch` and `sinfo` time out; `top` shows `slurmctld` at `100%` of one CPU core; compute nodes drop into `UNKNOWN` state. `slurmctld.log` warns of RPC queue saturation. | **Thundering Herd RPC Lock Contention:** A user loop submitted thousands of single jobs instead of a Job Array, starving `slurmd` ping RPCs (`SlurmdTimeout=120`). | Kill the submission loop, restart `slurmctld` from state save files, enforce `sbatch --array` (`MaxArraySize` raised above `1001`) via `job_submit.lua` / C plugin, and configure API Priority and Fairness (`APF`) on Kubernetes. |
| **5. `1,000` GPUs sitting idle behind a `1,024`-GPU queued job (Head-of-Line Blocking)** | Queue has dozens of pending `8`-GPU jobs and the cluster has `1,000` free GPUs, yet `0` new jobs start because the first job in the FIFO queue requires `1,024` GPUs (`24` GPUs short). | **Missing Backfill or Missing Wall-Clock `TimeLimits`:** Either backfill scheduling is disabled or queued jobs omitted a wall-time limit (`time_limit == NO_VAL`), preventing the scheduler from proving they will finish before the `1,024`-GPU job starts. | Enable backfill scheduling (`sched/backfill` or Volcano/KAI backfill) and reject GPU jobs that omit an explicit wall-clock `TimeLimit`. |

## Hands-on lab

### Venue and scope
This lab runs locally using the Python 3 standard library (`code/part11/multi_node_and_gang_scheduling.py` and `code/part11/multi_node_and_gang_scheduling_lab.py`). It simulates the single-node Pod boundary, the partial-allocation rendezvous deadlock versus all-or-nothing gang scheduling, MostAllocated bin-packing node scoring, Scheduler and Descheduler alignment checks, head-of-line backfill scheduling, and ReadWriteMany checkpoint storage sizing. Cluster manifests are marked `(untested here)`.

### Step 1: Run the self-checking multi-node and gang scheduling lab (tested here)

Run the lab script from the repository root.

```bash
python3 code/part11/multi_node_and_gang_scheduling_lab.py
```

Captured output from this repository:
```text
=== Chapter 11.7 Lab: Multi-Node Jobs, Pod Node Boundary & Gang Scheduling ===
  [PASS] Single Pod requesting 64 GPUs on 8-GPU nodes is unschedulable (a Pod cannot span nodes)
  [PASS] 64-GPU training job decomposes into 8 coordinated Pods x 8 GPUs/Pod
  [PASS] Without gang scheduling, 56 free GPUs place 7 of 8 Pods and deadlock at PyTorch rendezvous barrier
  [PASS] 7-of-8 partial allocation strands 56 GPUs idle ($140.0/hr at $20/hr per 8-GPU node)
  [PASS] With gang scheduling (minMember/minAvailable=8), 0 Pods are placed when only 56 GPUs are free (0 GPUs wasted)
  [PASS] With gang scheduling and 64 free GPUs, all 8 Pods start atomically and complete rendezvous
  [PASS] MostAllocated (GPU weight 5, CPU 1, Mem 1) scores 6/8-GPU node (67.86) above 2/8-GPU node (39.29)
  [PASS] HighNodeUtilization+MostAllocated and LowNodeUtilization+LeastAllocated are valid pairings
  [PASS] Enabling HighNodeUtilization and LowNodeUtilization simultaneously is rejected
  [PASS] Mismatched HighNodeUtilization+LeastAllocated or LowNodeUtilization+MostAllocated is rejected (eviction loop)
  [PASS] 1024-GPU head-of-line job on 1000 free GPUs waits for 24 more GPUs
  [PASS] Backfill admits 30-min (8-GPU) and 45-min (16-GPU) jobs that finish within the 45-min shadow window
  [PASS] Backfill blocks 90-min job (> 45-min window) and job missing TimeLimit (NO_VAL)
  [PASS] Storage sizing rule (2 * base + overhead) yields 100.0 GB for 8B LoRA and 500.0 GB for 70B fine-tuning
  [PASS] Kueue nominalQuota (10) + borrowingLimit (22) caps team at 32 GPUs; premium (16) + standard (32) = 48 GPUs
  [PASS] Ray NetworkPolicy isolates GCS port 6379, dashboard port 8265, and client server port 10001
  [PASS] Slurm dgx-h100-[001-128] node has 2 sockets x 56 cores x 2 threads = 224 CPUs and 128 x 8 = 1024 H100 GPUs
  [PASS] Slurm gres.conf maps 8 H100 GPUs across 4 core blocks of 28 physical cores (0-27, 28-55, 56-83, 84-111 = 112 cores)
  [PASS] Secondary RDMA network sets NCCL_IB_GID_INDEX=3 (RoCEv2), NCCL_NET_GDR_LEVEL=5, and NCCL_SOCKET_IFNAME=net1
  [PASS] PodGroup sets minMember=4 and scheduleTimeoutSeconds=300 (5 min), protected by PDB minAvailable=4
  [PASS] 50,000 jobs in 2s (25,000 jobs/s) requires Job Arrays (> default MaxArraySize 1001); 1000-pod gang on 500 nodes must be gated by Kueue
  [PASS] Without gang scheduling, two 8-node jobs on a 12-node (96-GPU) cluster split 6+6 nodes and deadlock all 96 GPUs
  [PASS] GPUDirect RDMA reduces latency by 40-60%; communication overhead >20-25% (>15% baseline) requires RDMA over TCP Ethernet
  [PASS] MPIJob with 2 Worker pods x 8 slotsPerWorker launches mpirun -np 16 all_reduce_perf
  [PASS] Kueue WorkloadPriorityClass production-priority sets value=10000 for preemption ordering

Summary: 25 passed, 0 failed out of 25 checks.
```

### Exercises

1. **Exercise 1 — Single-Pod node boundary vs multi-Pod decomposition:** Using `validate_pod_vs_multi_node_job()` in `code/part11/multi_node_and_gang_scheduling.py`, explain why requesting 64 GPUs on 8-GPU nodes as a single Pod returns `schedulable=False`. Then compute the required Pods and GPUs per Pod when `requested_as_single_pod=False`.
2. **Exercise 2 — Quantifying the 7-of-8 partial-allocation deadlock:** Using `simulate_partial_vs_gang_scheduling()` with 56 free GPUs and 8 Pods of 8 GPUs at 20.0 USD per hour, compare placed Pods, pending Pods, wasted idle GPUs, and hourly dollar waste when `gang_enabled=False` versus `gang_enabled=True`.
3. **Exercise 3 — MostAllocated bin-packing node score calculation:** Using `score_node_most_allocated()` with GPU weight 5, CPU weight 1, and memory weight 1, compute the exact scores for Node 1 and Node 2 from the table below. Explain why Node 1 wins even though Node 2 has higher CPU and memory utilization.
4. **Exercise 4 — Descheduler eviction-loop prevention:** Using `validate_scheduler_descheduler_alignment()`, test all four combinations of `MostAllocated` and `LeastAllocated` against `HighNodeUtilization`, `LowNodeUtilization`, and both plugins together. Identify which combinations are valid and which cause eviction loops.
5. **Exercise 5 — Backfill scheduling behind a 1,024-GPU head-of-line job:** A 1,024-GPU job is waiting at the head of a queue when 1,000 GPUs are free, and the missing 24 GPUs will free up in 45 minutes. Using `evaluate_backfill_candidates()` and the parameters below, determine which of the four queued jobs are backfilled and how many idle GPUs remain.
6. **Exercise 6 — Shared RWX checkpoint storage sizing:** Using `estimate_checkpoint_storage_gb()`, verify the total ReadWriteMany storage required for the 8B LoRA job and the 70B full fine-tuning job listed below.

```text
Exercise Input Parameters:
- Exercise 1: total_gpus=64, gpus_per_node=8.
- Exercise 2: cluster_free_gpus=56, job_pods=8, gpus_per_pod=8, node_cost_per_hour_usd=20.0.
- Exercise 3: Node 1 (6/8 GPUs, 32/64 CPUs, 256/512 GiB RAM) -> 67.86; Node 2 (2/8 GPUs, 48/64 CPUs, 384/512 GiB RAM) -> 39.29.
- Exercise 5: short-8gpu-a (8 GPUs, 30 min), long-8gpu-b (8 GPUs, 90 min), no-timelimit-c (8 GPUs, None), short-16gpu-d (16 GPUs, 45 min).
- Exercise 6: Llama 3.1 8B LoRA (16 GB base + 68 GB overhead = 100 GB); 70B fine-tuning (140 GB base + 220 GB overhead = 500 GB).
```

## Checkpoint questions

<details>
<summary>**1. Why can a single Kubernetes Pod never span multiple physical worker nodes?**</summary>

A Kubernetes Pod is the atomic unit of co-located execution on a single host. When kube-scheduler places a Pod, it binds `spec.nodeName` to one Node. On that Node, all containers share one Linux network namespace, one IPC namespace for `/dev/shm`, and one kubelet lifecycle. Consequently, the NodeResourcesFit filter rejects any Pod whose GPU request exceeds the allocatable GPU count of a single node.
</details>

<details>
<summary>**2. What are the four steps of PyTorch's distributed rendezvous mechanism, and why does a 7-of-8 Pod placement deadlock?**</summary>

When a PyTorch distributed job starts, workers connect to a rendezvous store such as a TCP store or etcd to complete four steps. They discover all peer workers, agree on the participant set to assign ranks 0 through `world_size - 1`, and synchronize at an atomic barrier. Once all workers arrive, they exchange peer connection details. If 7 of 8 Pods are scheduled and the 8th Pod stays Pending, the 7 running Pods wait indefinitely at the barrier and hold 56 GPUs at 0% compute.
</details>

<details>
<summary>**3. How can two 8-node training jobs submitted concurrently to a 12-node cluster deadlock 100% of the cluster if gang scheduling is disabled?**</summary>

Without gang scheduling, kube-scheduler binds Pods from both jobs independently as capacity appears. Job A can be assigned 6 nodes with 48 GPUs while Job B is assigned the remaining 6 nodes with 48 GPUs. Both jobs then wait at their 8-node rendezvous barriers for 2 more nodes that will never become free. All 96 GPUs across the 12 nodes remain locked in a permanent mutual deadlock.
</details>

<details>
<summary>**4. Why does Generative AI on Kubernetes Chapter 7 configure kube-scheduler with MostAllocated and weight 5 for GPUs instead of the default LeastAllocated strategy?**</summary>

The default LeastAllocated strategy spreads Pods across nodes and leaves partial GPU allocations on every server. That fragmentation blocks full-node jobs and prevents cluster autoscalers from terminating idle machines costing $10 to $30 per hour. Using MostAllocated with a GPU weight of 5 versus 1 for CPU and memory packs GPU Pods onto already-utilized nodes. That keeps remaining nodes completely empty so they can host full-node training gangs or scale down cleanly.
</details>

<details>
<summary>**5. What happens if you enable the HighNodeUtilization plugin in the Kubernetes Descheduler while kube-scheduler is using the default LeastAllocated strategy?**</summary>

The cluster enters an infinite eviction loop across its worker nodes. The HighNodeUtilization plugin evicts Pods from underutilized nodes to consolidate them, and the LeastAllocated scheduler immediately schedules the recreated Pods right back onto those same underutilized nodes. HighNodeUtilization must always be paired with MostAllocated, LowNodeUtilization must be paired with LeastAllocated, and both plugins must never be enabled together.
</details>

<details>
<summary>**6. How do you prevent the Kubernetes Descheduler from evicting a worker Pod belonging to an active gang-scheduled training job?**</summary>

You create a PodDisruptionBudget targeting the gang label such as `scheduling.x-k8s.io/pod-group: llm-training-group` with `minAvailable` set equal to the total worker count of 4. The Descheduler checks PodDisruptionBudgets before evicting any Pod. It therefore skips any Pod whose eviction would drop the running gang below its minimum required members.
</details>

<details>
<summary>**7. Compare the architectural layers of the four Kubernetes gang-scheduling solutions: Coscheduling plugin, Kueue, NVIDIA KAI Scheduler, and Volcano.**</summary>

The Coscheduling PodGroup plugin is a lightweight extension inside the default kube-scheduler. Kueue is a job-level admission controller and queue manager that sits above the scheduler and suspends jobs as Workload resources until quota is available. NVIDIA KAI Scheduler and Volcano are full alternative batch schedulers that combine PodGroup gang scheduling, hierarchical queues, and hardware topology optimization.
</details>

<details>
<summary>**8. What is KEP-4671 in upstream Kubernetes?**</summary>

KEP-4671 is the upstream Kubernetes Enhancement Proposal to introduce a native core Workload API and built-in all-or-nothing gang scheduling semantics directly into the Kubernetes scheduler. It standardizes how multi-Pod AI and ML workloads express atomic group scheduling without requiring third-party CRDs.
</details>

<details>
<summary>**9. In the Coscheduling PodGroup spec, what do minMember: 4 and scheduleTimeoutSeconds: 300 control?**</summary>

The `minMember: 4` field specifies the minimum number of Pods carrying the group label, including both leader and workers, that must be schedulable together before any Pod is bound. The `scheduleTimeoutSeconds: 300` field sets the 5-minute maximum duration that kube-scheduler will hold partial reservations waiting for all 4 members. If the timer expires first, the scheduler aborts the cycle and releases held resources.
</details>

<details>
<summary>**10. Why does LeaderWorkerSet exist alongside Kubeflow PyTorchJob, and what workload pattern does it target?**</summary>

While PyTorchJob is designed for run-to-completion distributed training runs, LeaderWorkerSet is purpose-built for multi-host sharded LLM inference. When a single model such as a 175B+ parameter LLM is too large for one node, it must be sharded across hosts. LeaderWorkerSet manages a leader Pod plus multiple worker Pods across nodes that scale, restart, and gang-schedule together as one atomic inference replica unit.
</details>

<details>
<summary>**11. How do Kueue's ResourceFlavor order, flavorFungibility, and WorkloadPriorityClass interact?**</summary>

The ResourceFlavor list order defines hardware topology preference so Kueue tries the first flavor, such as 16 NVLink and InfiniBand GPUs, before falling back to 32 standard Ethernet GPUs. Setting `whenCanBorrow: TryNextFlavor` instructs Kueue to check whether the next flavor has free nominal quota before borrowing quota in the first flavor. Meanwhile, WorkloadPriorityClass with value 10000 governs which queued job is admitted first and allows preempting lower-priority jobs.
</details>

<details>
<summary>**12. What is Head-of-Line Blocking in a gang-scheduled cluster, and how does Backfill Scheduling resolve it?**</summary>

If a 1,024-GPU job sits at the head of the queue when 1,000 GPUs are free and waits 45 minutes for 24 more GPUs, strict FIFO blocks all smaller jobs behind it. Backfill scheduling calculates the head job's shadow start time at `T + 45` minutes. It then allows smaller queued jobs to run immediately on the 1,000 free GPUs if their declared `TimeLimit` finishes before the 45-minute window expires.
</details>

<details>
<summary>**13. Why does submitting a Volcano Job with minAvailable: 1000 on a 500-node cluster risk OOM-killing kube-apiserver and etcd, and how does Kueue prevent this?**</summary>

When 1,000 Pod objects are created directly in kube-apiserver for an impossible gang on 500 nodes, controllers and the scheduler continuously retry and emit FailedScheduling events across all 1,000 Pods. That event churn bloats etcd watch caches until kube-apiserver runs out of memory. Kueue prevents this by keeping the job suspended (`spec.suspend: true`) as a single Workload object until quota exists, so zero Pod objects are created in etcd while the job waits.
</details>

<details>
<summary>**14. What happens to Slurm and Kubernetes when a script submits 50,000 individual jobs in 2 seconds, and what is the architectural fix on each platform?**</summary>

In Slurm, 50,000 individual `sbatch` RPCs saturate `slurmctld` internal state locks on one CPU core. That lock contention causes `slurmd` heartbeat pings (`SlurmdTimeout=120`) to time out in the queue and flip healthy nodes to `UNKNOWN`. In Kubernetes, 50,000 Pod creations overwhelm etcd. The fix is enforcing Slurm Job Arrays (`sbatch --array=1-50000` with `MaxArraySize` raised above 1001) via a `job_submit` plugin, and using Kubernetes API Priority and Fairness with Indexed Jobs or JobSets.
</details>

<details>
<summary>**15. What are the three core daemons and authentication service in Slurm's architecture, and why is slurmdbd separated from slurmctld?**</summary>

Slurm uses `slurmctld` as the central controller managing cluster state and allocations, `slurmd` as the node daemon launching tasks via `proctrack/cgroup`, and `slurmdbd` as the database daemon recording accounting in MariaDB or MySQL. Separating `slurmdbd` from `slurmctld` prevents SQL database latency from blocking the main scheduling loop. The `MUNGE` daemon provides cryptographic UID and GID credential authentication across all cluster nodes.
</details>

<details>
<summary>**16. How do SchedMD's Slinky project and Sunk bridge Slurm and Kubernetes, and why is running unpartitioned co-resident kubelet and slurmd daemons dangerous?**</summary>

Slinky provides a Kubernetes Operator for Slurm CRDs, a REST client for controllers, and a unified Prometheus exporter. Sunk exposes a Slurm cluster as a virtual Kubernetes node that translates Pods into `sbatch` jobs. Running co-resident `kubelet` and `slurmd` daemons on the same nodes without static node partitioning or MIG hardware partitioning causes both schedulers to double-book the same physical GPUs and trigger immediate CUDA OOM crashes.
</details>

<details>
<summary>**17. What are the three collective communication operations described in Generative AI on Kubernetes Chapter 7, and when is standard Ethernet sufficient versus InfiniBand or RoCE with GPUDirect RDMA?**</summary>

AllReduce sums or averages gradients across all workers in data parallelism, AllGather concatenates tensor shards across workers in tensor parallelism and FSDP, and Broadcast sends identical weights from rank 0 to all workers. Standard 10 to 100 Gbps Ethernet suffices for 2 to 8 data-parallel nodes when communication overhead is under 15% of step time. Once communication exceeds 20% to 25% of step time, 200 to 400 Gbps InfiniBand or 100 to 400 Gbps RoCEv2 with GPUDirect RDMA is required to cut latency by 40% to 60%.
</details>

<details>
<summary>**18. In Generative AI on Kubernetes Example 7-11, what do the five NCCL environment variables and the IPC_LOCK capability do on a Multus secondary RDMA network?**</summary>

Setting `NCCL_DEBUG=INFO` logs detected network interfaces and ring initialization, while `NCCL_IB_HCA="mlx5_0,mlx5_1"` selects the ConnectX RDMA adapters. Setting `NCCL_IB_GID_INDEX="3"` selects RoCEv2 Global Identifier index 3, `NCCL_NET_GDR_LEVEL="5"` enables full GPUDirect RDMA across PCIe and host bridges, and `NCCL_SOCKET_IFNAME="net1"` binds bootstrap traffic to the Multus secondary interface. The `IPC_LOCK` Linux capability allows the container to pin memory pages in RAM for RDMA registration.
</details>

<details>
<summary>**19. What is the rule-of-thumb formula for sizing shared ReadWriteMany checkpoint storage, and what are the sizes for Llama 3.1 8B LoRA versus 70B full fine-tuning?**</summary>

The sizing formula is `2 * base_model_size + checkpoint_overhead`, which accounts for base weights, periodic intermediate checkpoints, and final output artifacts. A Llama 3.1 8B LoRA fine-tuning job requires roughly 100 GB, while full fine-tuning of a 70B model requires 500 GB or more on ReadWriteMany storage such as CephFS, NFS, EFS, Filestore, WEKA, or Lustre.
</details>

<details>
<summary>**20. Why must Ray clusters and PyTorch distributed jobs be wrapped in default-deny Kubernetes NetworkPolicies, and which three TCP ports does a Ray head node use internally?**</summary>

Both Ray and PyTorch Distributed are designed for trusted internal networks without built-in authentication or encryption. Both frameworks also use `cloudpickle` deserialization that allows any network client to execute arbitrary Python code. A default-deny NetworkPolicy isolates each job to its own pods and restricts Ray head node ingress exclusively to authorized internal pods on TCP ports 6379 for Ray GCS, 8265 for the Ray dashboard, and 10001 for the Ray client server.
</details>

## Sources and review notes

### Primary sources read in full for this chapter
```text
Primary Sources and Technical Details Integrated:
- volume-06/04-distributed-orchestration-masterclass.md:
  Slurm slurmctld/slurmd/slurmdbd/MUNGE architecture; slurm.conf for dgx-h100-[001-128] with CPUs=224 Sockets=2 CoresPerSocket=56 ThreadsPerCore=2 RealMemory=2000000 Gres=gpu:h100:8; MessageTimeout=30, SlurmdTimeout=120, MaxJobCount=500000, MinJobAge=300; gres.conf COREs=0-27..84-111; srun --mpi=pmix -n 1024; Microservices vs Batch table; Volcano minAvailable: 8 RestartJob; Kueue; Kubeflow MPIJob mpirun -np 16 all_reduce_perf -b 8 -e 128M -f 2; Sunk/Virtual Kubelet & co-resident daemon risks; 1024-GPU vs 1000-GPU Head-of-Line blocking & Backfill; 50,000-job thundering herd & MaxArraySize=1001; 1,000-Pod Volcano etcd OOM on 500 nodes; 10,000-GPU Checkpoint Storm & burst buffers; C job_submit NO_VAL / min_nodes > 16 super_train & SPANK plugins; PyTorchJob headless service discovery.
- Roland Huß et al., Generative AI on Kubernetes (O'Reilly, 2026), Chapter 3 and Chapter 7 (Job Scheduling Optimization):
  $10-$30/hour GPU node cost; Example 7-1 binpack-scheduler MostAllocated with nvidia.com/gpu weight: 5 and cpu/memory weight: 1; Table 7-1 Descheduler HighNodeUtilization vs LowNodeUtilization eviction-loop warning; Example 7-2 PodDisruptionBudget minAvailable: 4; 7-of-8 PyTorch rendezvous barrier deadlock; Table 7-2 & Table 7-3 gang/topology schedulers; KEP-4671; Example 7-3 PodGroup minMember: 4 scheduleTimeoutSeconds: 300; Examples 7-4 to 7-9 Kueue ResourceFlavor 16 + 32 nominalQuota, nominalQuota: 10, borrowingLimit: 22, WorkloadPriorityClass 10000; KAI Scheduler gpuQuota: 8; LeaderWorkerSet LWS; Table 7-5 network technologies 40%-60% GPUDirect RDMA latency reduction, <15% vs 20%-25% Ethernet communication threshold; Examples 7-10 to 7-12 Multus IPoIB 10.0.0.0/24 whereabouts, NCCL_IB_HCA="mlx5_0,mlx5_1", NCCL_IB_GID_INDEX="3", NCCL_NET_GDR_LEVEL="5", NCCL_SOCKET_IFNAME="net1", rdma/hca: 2, IPC_LOCK, MTU 4,096; SchedMD Slinky; Table 7-6 storage & 2 * base_model_size + checkpoint_overhead 100 GB / 500 GB; Example 7-13 Ray NetworkPolicy ports 6379, 8265, 10001.
- Kubernetes for Generative AI Solutions (Packt, 2025), Chapter 10:
  GPU scheduling and cluster fragmentation.
- Chris Fregly, AI Systems Performance Engineering (O'Reilly, 2025), Chapter 3:
  Slicing a GPU with MIG single-node Pod constraint and Job Scheduling with Kubernetes and SLURM (Slinky).
```

### Related source files mapped in MIGRATION_MAP.md
- `volume-06/04-distributed-orchestration-masterclass.md` is the primary mapped source for this chapter, and all of its sections, tables, configurations, and troubleshooting scenarios are integrated above.

### Run here
- `python3 code/part11/multi_node_and_gang_scheduling_lab.py` passes all 25 self-checking assertions.

### Explicitly labelled inferences
- The hourly dollar waste of $140.0 per hour for 7 idle 8-GPU nodes at the $20 per hour midpoint, the two-job 96-GPU mutual deadlock example, and the MostAllocated node scores of 67.86 versus 39.29 are deterministic arithmetic evaluations computed in `code/part11/multi_node_and_gang_scheduling.py`.

### Not verified on live hardware
- All `kubectl`, `sbatch`, `srun`, `mpirun`, and `KubeSchedulerConfiguration` snippets targeting multi-node clusters (`Pod.spec.nodeName`, `MASTER_ADDR:MASTER_PORT` on `rank-0`, `eth0` vs `ib-network` `NET/IB/GDRDMA` across `PHB` PCIe paths, `scheduler_strategy` with `gpu_weight=5`, `cpu_weight=1`, `mem_weight=1`, `enabled_descheduler_plugins`, `MayStopSearch`, across Sections `1.2`, `1.4`, `2.1`, `2.2`, `2.4`, `3.2`, `4.1`, `4.2`, `5.1`, `5.2`, and `6.1`) are marked `(untested here)`.

### Not in the corpus
- Finalized GA YAML schema for KEP-4671, which remains in the proposal stage as of early 2026.

### Corrections to the author's notes
- Validation pass 2026-10-25: `validate_chapter.py` and `check_coverage.py` pass. The YAML manifests and commands are marked untested and were not applied to a cluster. Custom resource API versions such as `kueue.x-k8s.io/v1beta1` and `resource.k8s.io/v1` change between releases, so check them against the version you install. Console outputs quoted from the Volume notes are illustrative unless the chapter says otherwise.
- Earlier author note: required; all Kubernetes and Slurm configurations match `volume-06/04-distributed-orchestration-masterclass.md` and *Generative AI on Kubernetes* Chapter 7 verbatim.
