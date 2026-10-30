---
id: "c11-29"
title: "11.29 Multi-tenancy, quotas, fault tolerance and health on GPU clusters"
sidebar_label: "11.29 Multi-tenancy, quotas, fault tolerance and health on GPU clusters"
sidebar_position: 29
description: "Production Day-2 operations for multi-tenant GPU clusters: compute/network/storage isolation, IRSA workload identity, FinOps zombie reapers, rolling driver upgrades, Thanos observability, WORM disaster recovery, and the Universal AI SRE Diagnostic Matrix."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 11.29 Multi-tenancy, quotas, fault tolerance and health on GPU clusters

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE, plus local Python 3 simulation lab |
| Part | Part 11: GPUs on Kubernetes, scheduling and virtualization |
| Sources used | Author's Volume 19 and Volume 11 notes; Ajay Vohra, *Scalable Kubernetes Infrastructure for AI Platforms* |
| Coverage file | `planning/coverage/chapters/11-29.md` |

## Why this matters for AI infrastructure

Building a cluster is only the beginning of an AI platform team's work. Day-two operations bring hardware decay, noisy neighbors, and runaway cloud bills. Without strict isolation and automated recovery, a single user mistake or uncoordinated patch can take down hundreds of GPUs.

The table below summarizes five real production failures from our operational notes that motivate the controls in this chapter.

| Incident name | Source chapter | Triggering event | Production impact | Primary fix |
|---|---|---|---|---|
| Big-Bang Kernel Upgrade Outage | `volume-19/chapter-01` | Emergency `apt-get upgrade -y && reboot` across 500 GPU nodes at 2:00 AM without GPU Operator coordination | 400 nodes (80% of the cluster) booted with 0 `nvidia.com/gpu` capacity because `nvidia.ko` mismatched the new kernel headers | 6-Step Safe Eviction Pipeline and 3-Stage Canary Rollout (`1` Vanguard Node `24h` -> `1` Rack -> Global `>= 90%`) |
| 1-GPU Student Loop Crash | `volume-19/chapter-07` | 500 students and 5 research labs shared 80 GB A100 GPUs via Namespace `ResourceQuotas` (1 GPU) and software Time-Slicing | One infinite tensor loop consumed 100% of physical VRAM in 5 minutes and crashed 10 professor jobs with CUDA OOM | Partition shared 80 GB GPUs into 7 hardware `1g.10gb` MIG slices |
| $5 Million Empty Hotel | `volume-19/chapter-03` & `06` | Team requested $5 Million for 16 HGX H100 servers because Kubernetes GPU allocation stayed at 98% for 3 weeks | 30-day DCGM audit showed `DCGM_FI_PROF_SM_ACTIVE` averaged 12% while idle `p4d.24xlarge` notebooks wasted $2,000+ per weekend vs $20 for a CPU VM | Automated FinOps Reaper (`< 5%` SM activity for 4 hours), `7 × 1g.10gb` MIG, and `10:1` dev time-slicing |
| 60-Second Grafana 504 Timeout | `volume-19/chapter-09` | 1,000 GPUs emitting 500 metrics/sec with ephemeral pod labels overwhelmed a monolithic Prometheus server on a 200-node cluster | Dashboards spun for 60 seconds and failed with `504 Gateway Timeout` during an active outage | 4-Tier Thanos / Cortex architecture plus 5-minute Prometheus Recording Rules (`cluster:gpu:utilization_avg_5m`) |
| 1-Petabyte Dataset Corruption | `volume-19/chapter-10` | A data-cleaning script corrupted a 1 PB NVMe training directory, and 10 PB over 10 Gbps takes ~92 days to back up over the network | Nightly network backups were impossible, risking months of lost training progress | Hourly Copy-on-Write (`CoW`) storage snapshots (`<= 60 min` loss) and 30-day S3 Object Lock (`WORM`) Compliance mode |

This chapter synthesizes Volume 19 and Volume 11 of our operational notes alongside *Scalable Kubernetes Infrastructure for AI Platforms* into a complete operational blueprint. You will learn how to isolate competing tenants, cut cloud GPU bills in half, upgrade drivers without downtime, and diagnose silent hardware stalls.

## Prerequisites and outcomes

### Prerequisites

- Completion of Chapters 11.1 through 11.28. Those chapters cover the GPU Operator, Network Operator, KAI Scheduler, MIG, Time-Slicing, MPS, vGPU, KubeVirt, Kata, and BlueField DPUs.
- Working familiarity with Prometheus, DCGM Exporter, Kubernetes RBAC, ServiceAccounts, and parallel file systems.

### Outcomes

- Enforce three-pillar multi-tenant isolation across compute, network, and storage. Pair those boundaries with IAM Roles for Service Accounts, Golden Base Image pipelines, and Falco runtime security.
- Execute the six-step safe eviction pipeline and three-stage canary rollout. Run an automated FinOps zombie reaper to cut cloud GPU waste in half.
- Architect a four-tier Thanos observability stack with five-minute recording rules. Build a petabyte-scale disaster recovery plan using Copy-on-Write snapshots and S3 Object Lock.
- Apply the Universal AI SRE Diagnostic Matrix to isolate cluster bottlenecks. Separate thermal throttling, PCIe stalls, VRAM fragmentation, and optical transceiver drops from genuine compute saturation.

## Concepts: basics to intermediate to advanced

### 1. Basics: Three-pillar multi-tenancy, DevSecOps identity, and FinOps reapers

#### 1. The Three Pillars of Multi-Tenant Workload Isolation

Sharing a large GPU cluster across competing departments or university labs requires more than Kubernetes Namespaces and ResourceQuotas. Those API objects only restrict resource counts inside `etcd`. They do nothing to stop a process from exhausting shared silicon, network links, or storage arrays. When a student ran an infinite tensor loop on a time-sliced card, it consumed all physical VRAM and crashed ten research jobs sharing that board.

To prevent noisy neighbors from crossing tenant boundaries, platform engineers must enforce hardware isolation across three physical pillars. Compute isolation partitions shared cards into hardware MIG instances so an out-of-memory error stays confined inside a single ten-gigabyte slice. Strict compliance workloads get dedicated physical nodes using Kubernetes Node Taints and Tolerations.

Network and storage isolation complete the boundary. Default-deny NetworkPolicies in Calico or Cilium block unauthorized pod-to-pod scans, while SR-IOV Virtual Functions isolate kernel-bypass RDMA traffic on ConnectX NICs. On the shared Weka or Lustre parallel file system, per-tenant IOPS and bandwidth QoS rules prevent a massive checkpoint write from starving latency-sensitive inference APIs.

| Isolation pillar | Source reference | Unisolated failure mode | Hardware and software enforcement |
|---|---|---|---|
| Pillar 1: Compute Isolation | `volume-19/chapter-07` Sec. 1 & `volume-11/chapter-08` | Infinite tensor loop on time-sliced 80 GB A100 exhausts 100% VRAM in 5 minutes and kills 10 co-located jobs | Partition shared 80 GB GPUs into `7 × 1g.10gb` MIG slices; dedicate regulated PCI/HIPAA nodes via Node Taints and Tolerations |
| Pillar 2: Network Isolation | `volume-19/chapter-07` Sec. 2 & Chapter 11.22 | Marketing pods scan Finance pods over TCP/IP, or RDMA traffic bypasses Linux kernel software policies | Enforce Default-Deny `NetworkPolicies` (Calico/Cilium) per namespace and slice ConnectX NICs into hardware SR-IOV Virtual Functions (`VFs`) |
| Pillar 3: Storage Isolation | `volume-19/chapter-07` Sec. 3 | Multi-terabyte Marketing checkpoint saturates 100% of Weka/Lustre IOPS and stalls Finance inference APIs | Configure hard per-tenant IOPS and bandwidth QoS limits with guaranteed minimum IOPS reserves, plus scoped subdirectory `chroot` mounts (never root `/`) |

#### 2. DevSecOps Operations: Nightly Scanning, Golden Base Images, and IRSA

Static image scanning at build time cannot protect a long-running AI cluster on its own. Researchers frequently open interactive shells inside running training pods and install unverified Python packages from the internet. Furthermore, waiting several weeks for fifty separate data science teams to patch a critical library vulnerability leaves the entire platform exposed.

Securing a multi-tenant cluster requires three continuous operational loops. First, scan container images in Harbor or ECR every night. Run Falco, Prisma Cloud, or Aqua on every worker node to catch unauthorized `kubectl exec` package installations immediately. Second, maintain a central Golden Base Image built on signed NVIDIA AI Enterprise containers so CI/CD can rebuild downstream model images and trigger a Kubernetes RollingUpdate within hours.

Third, never attach broad cloud storage permissions to the worker node IAM profile. When a healthcare team attached `s3:GetObject` to the EC2 node role, every pod on those GPU servers inherited access to millions of patient records. Instead, bind a prefix-scoped IAM role via OIDC to a specific Kubernetes ServiceAccount such as `medical-training-sa` so only authorized pods receive short-lived STS credentials. Stream all Kubernetes Audit Logs, `/var/log/auth.log`, and API logs to Splunk or Elastic.

#### 3. FinOps Capacity Forecasting, the 3-Tier Purchasing Model, and the Zombie Reaper Bot

Linear capacity forecasting fails for generative AI because batching and sequence length pull hardware utilization in opposite directions. Doubling inference traffic rarely requires twice as many GPUs because Triton dynamic batching packs extra requests into existing CUDA kernels. Conversely, keeping user count flat while expanding prompt context from single-page documents to hundred-page PDFs scales KV-cache memory linearly. That memory growth triggers immediate out-of-memory crashes.

At the same time, Kubernetes allocation metrics routinely lie about actual hardware usage. A cluster can report ninety-eight percent GPU allocation for weeks while DCGM shows the Streaming Multiprocessors sitting idle in abandoned Jupyter notebooks over the weekend. Combining a three-tier purchasing strategy with an automated FinOps Reaper cuts cloud GPU bills in half and prevents unnecessary multi-million-dollar hardware purchases.

| Capacity / FinOps lever | Source reference | Target workload or scenario | Mechanism and exact thresholds | Verified financial impact |
|---|---|---|---|---|
| Forecasting: Batching vs Context | `volume-19/chapter-03` Sec. 1 | Inference traffic doubling (`10 -> 20 req/s`) vs `1 -> 100`-page PDF uploads | Dynamic batching raises GPU util from `40%` to `55%`; `100`-page PDFs explode KV-cache linearly into CUDA OOM | Prevents over-buying compute for RPS growth while sizing VRAM for sequence length |
| 1. Baseline Tier (Reserved / On-Prem) | `volume-19/chapter-03` & `06` | `24/7` steady-state production inference and baseline R&D | Commit to 1-to-3-Year Reserved Instances (`RIs`), Savings Plans, or on-premises bare metal | `40%–50%` off (1-Year RI) to `60%+` cheaper than On-Demand |
| 2. Burst Tier (On-Demand Cloud) | `volume-19/chapter-03` & `06` | Daily traffic peaks, seasonal spikes, urgent ad-hoc runs | Autoscale elastic On-Demand instances only during active peak hours | Eliminates idle reservation waste during off-peak hours |
| 3. Spot / Preemptible ("Scavenger Tier") | `volume-19/chapter-03` & `06` | Fault-tolerant batch training and async data processing | Save async S3 checkpoints every `15 minutes` and use AWS Node Termination Handler to catch the `2-minute` warning for a final sync flush | Up to `60%–70%` discount with `< 15 minutes` (or `0` steps) lost on preemption |
| 4. Dev/Staging Sharing (MIG + Time-Slicing) | `volume-19/chapter-03` & `06` | Dev/staging using `5 GB` VRAM and `12%` `SM_ACTIVE` behind `98%` K8s allocation | Partition staging H100s into `7 × 1g.10gb` MIG slices and set `10:1` dev time-slicing (`80` devs on `1` `8`-GPU node); cuts `$500,000/month` AWS bill in half in `30 days` | Rejected premature `$5 Million` (`16` HGX H100) CapEx request for `12 months` |
| 5. Automated FinOps Reaper Bot | `volume-19/chapter-03` & `06` | Zombie Jupyter notebooks left running over weekends (`$2,000+` per `p4d.24xlarge` vs `$20` CPU VM) | Kubernetes Operator queries Prometheus: if `DCGM_FI_PROF_SM_ACTIVE < 5%` continuously for `4 hours`, evict Pod and send Slack alert | Reclaims stranded `$30,000` GPUs automatically |

---

### 2. Intermediate: Zero-downtime rolling upgrades, Thanos observability at scale, and petabyte DR

#### 1. The Jenga Tower of AI Upgrades: 6-Step Eviction and 3-Stage Canary Rollouts

Upgrading an AI cluster is perilous because PyTorch, CUDA, the NVIDIA kernel driver, and the Linux kernel form a fragile dependency chain. When an operations team ran an uncoordinated kernel upgrade and reboot across five hundred GPU servers at two in the morning, four hundred nodes came back online with zero GPUs. The new kernel broke ABI compatibility with the pre-compiled `nvidia.ko` driver module, taking down eighty percent of the fleet before market open.

To prevent fleet-wide outages, never bake NVIDIA drivers statically into the host OS or trigger global reboots. Let the GPU Operator manage driver containers that recompile against matching kernel headers on boot, and orchestrate maintenance through a Node Upgrade Operator such as Kured. Every node upgrade must follow a six-step eviction pipeline and progress through a three-stage canary rollout that keeps at least ninety percent of cluster capacity online.

```text
Upgrade Blast-Radius Tiers (volume-19/chapter-01):
  Tier 1: Application / Container upgrades          -> Low Risk
  Tier 2: GPU Operator / Driver (nvidia.ko) reload  -> High Risk
  Tier 3: OS Kernel / System Firmware reboot        -> Extreme Risk

6-Step Safe Eviction Pipeline:
  1. Cordon      -> kubectl cordon node-42
  2. Drain       -> kubectl drain node-42 --ignore-daemonsets --delete-emptydir-data (triggers checkpoint save)
  3. Verify Idle -> nvidia-smi confirms 0 active GPU processes
  4. Upgrade     -> Apply Helm driver update or reboot into new kernel with driver-container header compile
  5. Validation  -> Run dcgmi diag hardware burn-in
  6. Uncordon    -> kubectl uncordon node-42

3-Stage Canary Rollout Strategy:
  Stage 1 (The Vanguard Node) -> Upgrade 1 isolated node and soak on low-priority batch jobs for 24 hours
  Stage 2 (Rack-Level Rollout)-> Upgrade 1 full rack (1 leaf-switch InfiniBand fault domain)
  Stage 3 (Global Rollout)    -> Roll across remaining racks while keeping >= 90% of cluster capacity online
```

#### 2. Surviving the Cardinality Explosion: 4-Tier Thanos / Cortex and Recording Rules

A single monolithic Prometheus server works well on a small cluster, but it collapses on a thousand-GPU AI factory. Each GPU emits hundreds of hardware metrics per second, and Kubernetes attaches a unique pod label to every short-lived training job. Within days, this high-cardinality label explosion creates millions of distinct time-series that exhaust server memory.

When engineers open Grafana dashboards during a two-hundred-node incident, simultaneous thirty-day queries stall Prometheus for a full minute and fail with `504 Gateway Timeout`. Surviving this scale requires decoupling metric ingestion from querying across a four-tier Thanos, Cortex, or VictoriaMetrics architecture. In addition, Prometheus Recording Rules pre-compute fleet averages every five minutes in the background so executive and incident dashboards load instantaneously.

```mermaid
flowchart LR
    T1["1. Scraping Tier: Node/Rack Prometheus Agents or OTel Collectors (Scrape Local DCGM :9400 Only)"] -->|"Remote-Write Stream"| T2["2. Aggregation Tier: Horizontally Scalable Thanos Receive / Cortex / VictoriaMetrics"]
    T2 -->|"Compress Blocks"| T3["3. Storage Tier: S3 Object Storage (Multi-Month / Infinite Retention)"]
    T2 --> T4["4. Query Tier: Dedicated Thanos Queriers + 5-Min Prometheus Recording Rules (cluster:gpu:utilization_avg_5m)"]
    T3 --> T4
    T4 -->|"Instant Load (Zero 504 Timeouts)"| Graf["SRE Incident & CFO 30-Day Dashboards"]
```

#### 3. Petabyte-Scale Disaster Recovery: RPO, RTO, WORM Object Lock, and Hourly CoW Snapshots

Traditional nightly backup tools like Commvault or Veeam fail completely when applied to a multi-petabyte AI data lake. Moving ten petabytes over a ten-gigabit network link takes more than three months and saturates core spine switches needed for training. When a buggy script corrupts a petabyte-scale NVMe directory or ransomware targets model checkpoints, you cannot wait weeks to pull cold archives over the wire.

AI disaster recovery relies on three storage-native controls instead of nightly file copies. First, align your Recovery Point Objective with your training checkpoint interval and match your Recovery Time Objective to your storage tier. Second, lock model checkpoints in S3 using Object Lock Write Once Read Many in Compliance Mode so not even the cloud root account can delete them for thirty days. Third, configure Weka, NetApp, or ZFS-backed Lustre to take hourly read-only Copy-on-Write pointer snapshots. Pair those snapshots with dark-fiber asynchronous delta replication so a corrupted directory reverts via a single API call.

| DR metric or control | Source reference | Scale and timing numbers | Operational behavior and guarantee |
|---|---|---|---|
| Network Backup Bottleneck | `volume-19/chapter-10` Sec. 1 | `10 Petabytes` (`80 × 10^15` bits) over `10 Gbps` link = `~92 days` (`8,000,000 s`) | Proves traditional nightly network backups are physically impossible at petabyte scale |
| `RPO` and `RTO` Alignment | `volume-19/chapter-10` Sec. 1 | Checkpoint every `4 hours` -> `RPO = 4 hours`; `5 PB` cold S3 Glacier restore -> `RTO = 3 weeks` | Ties compute loss directly to checkpoint frequency and recovery speed to storage tier |
| S3 Object Lock (`WORM` Compliance Mode) | `volume-19/chapter-10` Sec. 2 | `50 TB` model checkpoints locked for a `30-day` retention window | Blocks ransomware and compromised `root` accounts from overwriting or deleting checkpoints (unlike bypassable Governance mode) |
| Hourly Copy-on-Write (`CoW`) Snapshots | `volume-19/chapter-10` Customer Scenario | `1-Petabyte` NVMe production directory snapped every `1 hour` (`<= 60 minutes` loss) | Reverts accidental `rm -rf` or data-cleaning corruption via `1` storage API call with zero network transfer |

---

### 3. Advanced: The Universal AI SRE Diagnostic Matrix

When an AI team reports that training is slow or an inference API is timing out, looking only at `nvidia-smi` leads to expensive mistakes. A GPU can report one hundred percent utilization while its Tensor Cores sit nearly idle or its clock speed is throttled by afternoon heat. The memory controller might also be stalled waiting on PCIe transfers. Similarly, a single degraded optical transceiver dropping one packet in ten thousand can stall a thousand-GPU collective operation while basic `ping` tests pass without error.

Instead of guessing or ordering new hardware, walk the Universal Diagnostic Matrix step by step. Compare coarse GPU utilization against hardware clock throttle flags, Triton queue latencies, HBM memory-copy utilization, and ConnectX RDMA hardware sequence counters.

```mermaid
flowchart TD
    Sym["AI Workload Degraded or Failing"] --> Branch{"What Does nvidia-smi & DCGM Show?"}
    Branch -->|"1. GPU Util Low (GPUs Idle)"| Idle["Check Host CPU (DALI), Disk iowait (WebDataset/NVMe), or IB Traffic (Keep TP <= 8 Intra-Node)"]
    Branch -->|"2. GPU Util 80-100%, But Job/API Slow"| Lie{"Check DCGM_FI_DEV_CLOCK_THROTTLE_REASONS"}
    Lie -->|"HW_SLOWDOWN Active (Temp >= 85C, Clock 1500->500MHz)"| Therm["Hardware Thermal Throttling (e.g. 2:00 PM HVAC / Fan Failure -> 40% Slowdown)"]
    Lie -->|"No Throttle"| Sub{"Check Queue, Mem Copy & Tensor Active"}
    Sub -->|"nv_inference_queue_duration_us Spiking"| QSat["Triton Software Queue Saturation -> Increase Instance Group Count in config.pbtxt"]
    Sub -->|"DCGM_FI_DEV_MEM_COPY_UTIL ~100%"| MemBW["Memory Bandwidth Bound (LLM Decode TPOT) -> TensorRT-LLM PagedAttention + FlashAttention + INT8"]
    Sub -->|"DCGM_FI_PROF_PCIE_RX_BYTES Maxed"| PCIe["PCIe Copy Stall -> Enable pin_memory=True or GPUDirect Storage (GDS)"]
    Sub -->|"DCGM_FI_PROF_PIPE_TENSOR_ACTIVE < 10% (FP32 High)"| Code["The Utilization Lie: Tiny Kernels or Missing AMP -> Enable BF16/FP16 AMP & Operator Fusion"]
    Branch -->|"3. Random Crashes (CUDA OOM or NCCL Error 12)"| Crash["CUDA OOM: Set expandable_segments:True or FSDP/ZeRO-3; NCCL Error 12: Check hw_counters on Node 84"]
```

#### Key Forensic Proofs in the Universal Diagnostic Matrix

Each branch of the diagnostic tree maps to a specific hardware counter or runtime configuration. For example, PyTorch jobs often crash with out-of-memory errors when plenty of free VRAM remains because the caching allocator has chopped free space into thousands of tiny gaps. Likewise, an afternoon training slowdown where utilization stays pegged at one hundred percent is proven to be a cooling failure. GPU temperature hits eighty-five degrees Celsius and hardware slowdown cuts clocks to a third of normal speed.

On the network and operations side, hunting down a silent RDMA drop across a large RoCEv2 fabric requires reading NIC hardware sequence counters rather than running ICMP pings. Once a fault is isolated, deterministic runbooks and structured Follow-the-Sun handoffs ensure that hardware replacements and maintenance windows happen without waking up engineers unnecessarily.

| Forensic scenario | Source reference | Telemetry proof and exact numbers | Root cause and remediation |
|---|---|---|---|
| 1. PyTorch VRAM Fragmentation vs Model Size OOM | `volume-19/chapter-04` Sec. 2 & `chapter-11` | `torch.cuda.memory_summary()` shows `Max Reserved = 80 GB` vs `Max Allocated = 40 GB`; `20 GB` (`15 GB`) free in `10,000 × 2 MB` gaps fails a contiguous `5 GB` tensor alloc | Swiss-cheese allocator fragmentation -> set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. (`1B` model OOM = lower batch size / grad accum; `70B` model OOM on `80 GB` GPU = shard via FSDP / ZeRO-3) |
| 2. The 2:00 PM 40% Thermal Slowdown | `volume-19/chapter-04` Customer Scenario | `nvidia-smi` shows `100%` util, but `DCGM_FI_DEV_GPU_TEMP` hits `85°C` and `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` asserts `HW_SLOWDOWN` (`1,500 MHz -> 500 MHz`) | Afternoon HVAC strain / fan failure downclocked the GPU `3x` -> alert on throttle bitmask and escalate rack cooling to Facilities |
| 3. The 100% Utilization Lie & Triton 200 ms SLA Breach | `volume-19/chapter-04` & `chapter-11` | `TENSOR_ACTIVE < 10%` (`5%`) vs `> 50%` target; `PCIE_RX_BYTES` maxed; Triton breaches `200 ms` `p99` at `80–100%` util with `nv_inference_queue_duration_us` or `DCGM_FI_DEV_MEM_COPY_UTIL` at `100%` | Enable AMP (`BF16`/`FP16`) for Tensor Cores; set `pin_memory=True` / GDS for PCIe; raise `Instance Group` count in `config.pbtxt` and enable TensorRT-LLM `PagedAttention` + `INT8` |
| 4. Node 84 Degraded Optic in 128-Node 400G RoCEv2 | `volume-19/chapter-05` Customer Scenario | `NCCL WARN NET/IB : Got completion ... with error 12` (retry exceeded), `0` PFC storms (`rx_prio<N>_pause`), `1` in `10,000` RDMA drop stalls `1,000` GPUs; `Node 84` spikes `packet_seq_err` | Dying laser on `Node 84` -> scan `/sys/class/infiniband/<dev>/ports/<port>/hw_counters/` (`packet_seq_err`, `out_of_sequence`, `implied_nak_seq_err`, `local_ack_timeout_err`) and `perfquery` (`SymbolErrorCounter`, `LinkDownedCounter`), cordon `Node 84`, and replace optic |
| 5. Zero-Touch XID 48 Runbook & Follow-the-Sun Handoff | `volume-19/chapter-12` & `chapter-02` | `XID 48` (double-bit ECC) on `node-worker-42` GPU `3`; handoff logs `3` NCCL timeouts on `Llama-3-FineTune`, PCIe drops on `node-55`, `14:00 UTC` `dcgmi diag` window, Jira `#4092`; Game Day tests `< 5s` (`99.999%`) master failover | Automate `XID 48` via Alertmanager webhook (`1. Cordon` -> `2. dmesg -T \| grep NVRM` -> `3. Drain & Reset/Reboot` for row remap -> `4. RMA Jira` if recurring) |

## Commands and configurations that matter

Every command and manifest below targets one of the failure modes we just examined. Before running network replacements, granting pod S3 access, or deploying a FinOps reaper, operators need exact queries that work cleanly across the cluster.

### 1. Scanning RDMA Hardware Sequence-Error Counters Across a Node

When a multi-node job fails with an RDMA transport retry error, standard TCP tools cannot see the dropped packets. Run this loop on your GPU nodes to inspect the ConnectX hardware sequence counters and InfiniBand symbol error registers directly.

```bash
# Inspect ConnectX RDMA hardware sequence and timeout error counters for silent optic drops (untested here)
for dev in /sys/class/infiniband/mlx5_*; do
    echo "=== ${dev##*/} ==="
    grep -H . "$dev"/ports/1/hw_counters/{packet_seq_err,out_of_sequence,implied_nak_seq_err,local_ack_timeout_err} 2>/dev/null || true
done

# On InfiniBand switches/hosts, query SymbolErrorCounter and LinkDownedCounter (untested here)
perfquery | grep -E "SymbolErrorCounter|LinkDownedCounter"
```

### 2. Least-Privilege AWS S3 Access via IAM Roles for Service Accounts

Granting S3 bucket access to the underlying EC2 node profile exposes sensitive training datasets to every container scheduled on that machine. This manifest binds a read-only IAM role to the `medical-training-sa` ServiceAccount, requests a hardware MIG slice, and enables expandable CUDA memory segments to prevent allocator fragmentation.

```yaml
# irsa-medical-training-pod.yaml (volume-19/chapter-08, untested here)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: medical-training-sa
  namespace: medical-llm
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/medical-s3-prefix-readonly
---
apiVersion: v1
kind: Pod
metadata:
  name: medical-llm-trainer
  namespace: medical-llm
spec:
  serviceAccountName: medical-training-sa
  containers:
    - name: pytorch
      image: nvcr.io/nvidia/pytorch:24.08-py3
      env:
        - name: PYTORCH_CUDA_ALLOC_CONF
          value: "expandable_segments:True"
      resources:
        limits:
          nvidia.com/mig-1g.10gb: 1
```

### 3. Prometheus Recording Rule and FinOps Zombie Reaper Query

Querying raw per-pod GPU metrics across a thirty-day window can time out Prometheus during an outage, and abandoned notebooks quietly drain cloud budgets. This rule file pre-computes fleet utilization every five minutes and flags any pod whose Streaming Multiprocessor activity stays below five percent for four hours.

```yaml
# prometheus-recording-and-finops-reaper-rules.yaml (volume-19/chapter-03 & 09, untested here)
groups:
  - name: gpu-fleet-recording-and-finops
    interval: 5m
    rules:
      # Pre-compute fleet average utilization every 5m so 30-day CFO dashboards load instantly
      - record: cluster:gpu:utilization_avg_5m
        expr: avg(DCGM_FI_DEV_GPU_UTIL)

      # Identify zombie pods holding a GPU with < 5% SM activity for 4 hours
      - alert: ZombieGpuPodDetected
        expr: avg_over_time(DCGM_FI_PROF_SM_ACTIVE[4h]) < 0.05
        for: 5m
        labels:
          severity: warning
          action: finops-reap
```

## How it fails

Even mature platform teams hit subtle operational traps when upgrading kernels, cooling high-density racks, or scaling inference services. The table below maps five high-impact production symptoms to their exact command evidence, root cause boundaries, and remediation steps.

| Failure mode | Exact symptom & command evidence | Root cause boundary | Remediation |
|---|---|---|---|
| 1. `400` of `500` GPU nodes lose all `nvidia.com/gpu` capacity after a `2:00 AM` `apt-get upgrade -y && reboot` (`volume-19/chapter-01`) | `kubectl get nodes` shows `0` allocatable GPUs on `400` nodes after an emergency Ubuntu kernel patch; `dmesg` shows `nvidia.ko` module version mismatch. | Big-Bang Kernel Reboot Breaking Driver Compatibility: Upgrading the host kernel without matching headers and GPU Operator driver-container recompilation blinded `80%` of the fleet at once. | Restart `nvidia-driver-daemonset` with matching kernel headers to rebuild `nvidia.ko`, ban raw Ansible reboots, and enforce the 6-Step Eviction Pipeline + 3-Stage Canary Rollout (`1` Vanguard `24h` -> `1` Rack -> Global `>= 90%`). |
| 2. Training iteration time spikes `40%` every day at `2:00 PM` while `nvidia-smi` shows `100%` utilization (`volume-19/chapter-04`) | Network switches are idle and `nvidia-smi` reports `100%` GPU-Util, but overlaying `DCGM_FI_DEV_GPU_TEMP` and `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` shows `85°C` and `HW_SLOWDOWN` (`1500 -> 500 MHz`). | Data Center HVAC Thermal Throttling: Afternoon heat strained rack cooling; the GPU downclocked `3x` to protect silicon while `nvidia-smi` stayed at `100%`. | Alert on `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` bitmask and escalate rack cooling / fan failures to Data Center Facilities. |
| 3. `128`-node `400G` RoCEv2 training jobs fail randomly with `NCCL WARN NET/IB : Got completion ... with error 12` (`volume-19/chapter-05`) | Core switches show links `UP` and `0` PFC storms, `ping` succeeds, but `Node 84`'s `/sys/class/infiniband/.../hw_counters/packet_seq_err` and `local_ack_timeout_err` climb rapidly. | Silent Layer 1 Optical Transceiver Degradation: A dying laser on `Node 84` drops `1` in `10,000` RDMA packets, triggering Go-Back-N retransmissions that poison the synchronous `128`-node `AllReduce` ring. | Monitor NIC RDMA `hw_counters` (`packet_seq_err`, `out_of_sequence`, `implied_nak_seq_err`, `local_ack_timeout_err`) and switch FEC/CRC counters; cordon `Node 84` and replace the optical transceiver. |
| 4. Triton LLM inference breaches `200 ms` `p99` SLA at `80–100%` GPU-Util, and team demands new GPUs (`volume-19/chapter-11`) | `nvidia-smi` bounces between `80%` and `100%`, while `nv_inference_queue_duration_us` spikes and/or `DCGM_FI_DEV_MEM_COPY_UTIL` is pegged at `100%`. | Software Queue Saturation & KV-Cache Memory-Bandwidth Bottleneck: Requests wait in Triton's thread queue, and token decoding (`TPOT`) is memory-bandwidth-bound rather than compute-bound. | Increase `Instance Group` count in Triton `config.pbtxt`, deploy TensorRT-LLM with PagedAttention, and apply INT8 quantization to halve memory bandwidth per token. |
| 5. Grafana dashboards spin for `60 seconds` and fail with `504 Gateway Timeout` during a `200`-node outage (`volume-19/chapter-09`) | Single monolithic Prometheus server hits `100%` RAM/CPU when incident error series spike and SREs query `30-day` raw DCGM metrics simultaneously. | High-Cardinality Ingest + Query Coupling: Ephemeral pod labels created millions of series on a single server with no read/write separation or pre-computation. | Deploy the 4-Tier Thanos / Cortex Architecture (decoupling `Scraping Agents` and `Thanos Receive` from `Thanos Querier` + S3) and pre-compute aggregations with `5-minute` Prometheus Recording Rules (`cluster:gpu:utilization_avg_5m`). |

## Hands-on lab

### Venue and scope

Running a live five-hundred-node reboot or injecting hardware ECC errors requires a dedicated staging fleet. This lab provides a local Python 3 verification suite in `code/part11/multi_tenancy_quotas_fault_tolerance_health.py` and `code/part11/multi_tenancy_quotas_fault_tolerance_health_lab.py`. It validates the six-step eviction pipeline, the three-stage canary rollout, the FinOps zombie reaper, petabyte disaster recovery math, and the Universal AI SRE Diagnostic Matrix. All cluster CLI commands are marked `(untested here)`.

### Step 1: Run the self-checking multi-tenancy, FinOps, fault tolerance and health lab (tested here)

Run the self-checking lab script from the repository root to verify all twenty-five operational checks.

```bash
python3 code/part11/multi_tenancy_quotas_fault_tolerance_health_lab.py
```

Captured output from this repository.

```text
=== Chapter 11.29 Lab: Multi-Tenancy, Quotas, Fault Tolerance, FinOps & Health ===
  [PASS] Volume 19 Ch 1 Safe Eviction Pipeline defines 6 ordered steps from Cordon to Uncordon
  [PASS] Volume 19 Ch 1 Canary Rollout progresses from 1 Vanguard Node (24h) -> 1 Rack -> Global (>= 90% capacity online)
  [PASS] Volume 19 Ch 1 Customer Scenario: 500-node uncoordinated kernel reboot at 2:00 AM blinded 400 nodes (80%) to nvidia.com/gpu
  [PASS] Volume 19 Ch 3 FinOps Reaper evicts zombie pods when DCGM_FI_PROF_SM_ACTIVE < 5% for >= 4 hours
  [PASS] Volume 19 Ch 3 rejects $5M (16 HGX H100) purchase when 98% K8s allocation hides 12% SM_ACTIVE over 30 days, slicing into 7x 1g.10gb MIG
  [PASS] Volume 19 Ch 6 cuts $500,000/mo AWS bill in half using 1-Year RIs (40-50% off), Spot (70% off, 15m S3 ckpt + 2m warning), and 80 devs on 1 8-GPU node (10x time-slicing)
  [PASS] Volume 19 Ch 10 DR math: 10 Petabytes over a 10 Gbps link takes ~92 days, requiring S3 Object Lock WORM (30d Compliance) and 1-hour CoW snapshots (<=60m loss)
  [PASS] Volume 19 Ch 5: 128-node 400G RoCEv2 NCCL error 12 (retry exceeded) isolates Node 84 via hw_counters/packet_seq_err
  [PASS] Volume 19 Ch 4: 2:00 PM 40% slowdown at 100% nvidia-smi util is caused by 85C HW_SLOWDOWN downclocking from 1500 MHz to 500 MHz
  [PASS] Volume 19 Ch 11: Triton 200ms p99 breach with spiking nv_inference_queue_duration_us is fixed by increasing Instance Group count in config.pbtxt
  [PASS] Volume 19 Ch 11: LLM decoding pegged at ~100% DCGM_FI_DEV_MEM_COPY_UTIL is fixed by TensorRT-LLM PagedAttention + INT8 quantization
  [PASS] Volume 19 Ch 4: Saturated DCGM_FI_PROF_PCIE_RX_BYTES at 100% util is fixed by pin_memory=True, NVIDIA DALI, or GPUDirect Storage
  [PASS] Volume 19 Ch 4: 100% nvidia-smi util with 5% (< 10%) TENSOR_ACTIVE proves unoptimized FP32 / tiny kernels needing AMP (BF16/FP16)
  [PASS] Volume 19 Ch 4: PyTorch 80GB Reserved vs 40GB Allocated VRAM fragmentation (10,000 x 2MB gaps = 20GB free failing 5GB alloc) is fixed by PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
  [PASS] Volume 19 Ch 7: 3 multi-tenant isolation pillars span Compute (MIG/Taints), Network (Default-Deny NetworkPolicy + SR-IOV VFs for RDMA), and Storage (Weka/Lustre IOPS QoS + chroot)
  [PASS] Volume 19 Ch 7 University Scenario: 500 students + 5 labs where 1 student infinite tensor loop crashed 10 professor jobs on time-slicing -> fixed via 7x 1g.10gb MIG
  [PASS] Volume 19 Ch 8: Replaces broad EC2 Node IAM s3:GetObject with OIDC IAM Roles for Service Accounts (IRSA) bound to medical-training-sa + Falco runtime scanning
  [PASS] Volume 19 Ch 9: 4-tier Thanos/Cortex architecture + 5m Recording Rules (cluster:gpu:utilization_avg_5m) prevents 60s 504 Gateway Timeout on 200-1,000 node clusters
  [PASS] Volume 19 Ch 12: XID 48 (double-bit ECC) runbook on node-worker-42 GPU 3 cordons node, verifies dmesg NVRM, resets/reboots after drain for row remap, and opens RMA Jira if recurring
  [PASS] Volume 19 Ch 12: Follow-the-Sun handoff records 3 NCCL timeouts on Llama-3-FineTune, PCIe drops on node-55, 14:00 UTC dcgmi diag window, and Jira #4092
  [PASS] Volume 19 Ch 11 distinguishes 1B model OOM (lower batch size / gradient accumulation) from 70B model OOM on 80GB GPU (requires FSDP / ZeRO-3)
  [PASS] Volume 11 Ch 8, 9, 10, 11, 12 & Labs 01-04 integrate 7-layer tenant isolation, N=ceil((D+F)/(A*(1-H))) capacity, >120s DCGM freshness, and 6-layer triage
  [PASS] Volume 19 Ch 2 Game Day validates XID 48 (dcgmi test --inject), IB port disable (ibportstate), and 99.999% (<5s) master failover liveness probe tuning
  [PASS] Volume 19 Index organizes 12 chapters and 4 operational labs across Mechanism -> Real Evidence -> Decision Trees -> Troubleshooting -> Interview Prep
  [PASS] Scalable Kubernetes Infrastructure for AI Platforms (SKI Ch 2) reinforces namespace quota governance and resilient AI job execution

Summary: 25 passed, 0 failed out of 25 checks.
```

### Exercises

1. **Exercise 1 — Safe Eviction Pipeline and 3-Stage Canary Upgrade.** Inspect `SIX_SAFE_EVICTION_STEPS` and `THREE_CANARY_ROLLOUT_STAGES` in `code/part11/multi_tenancy_quotas_fault_tolerance_health.py`. Explain why rebooting five hundred nodes simultaneously into a new Ubuntu kernel caused four hundred nodes to lose `nvidia.com/gpu` capacity. List the six eviction steps and three canary stages that prevent this outage.
2. **Exercise 2 — FinOps Reaper and Cloud Bill Optimization.** Use `evaluate_finops_reaper_and_cloud_plan()` to state the DCGM threshold and duration used by the FinOps Reaper bot. Explain how you refute a five-million-dollar HGX H100 purchase request when Kubernetes allocation sits at ninety-eight percent while `DCGM_FI_PROF_SM_ACTIVE` is twelve percent. Detail the three-phase plan to cut a five-hundred-thousand-dollar monthly AWS GPU bill in half.
3. **Exercise 3 — Decoding the 100% Utilization Lie.** Use `diagnose_ai_sre_bottleneck()` to state the exact DCGM or Triton metric for an afternoon forty percent training slowdown and for full utilization with low Tensor Core activity. Provide the remediation for saturated PCIe receive bytes and a Triton latency SLA breach.
4. **Exercise 4 — Hunting Down Node 84's Degraded Optic on a RoCEv2 Fabric.** List the three network troubleshooting layers across optical links, PFC storms, and OpenSM routing. Name the exact `/sys/class/infiniband/.../hw_counters/` files used to isolate Node 84 when `NCCL error 12` strikes.
5. **Exercise 5 — 3-Pillar Multi-Tenancy, IRSA, and Thanos Observability.** State the controls required across compute, network, and storage to isolate Marketing and Finance on a shared cluster. Explain how IRSA on `medical-training-sa` replaces broad EC2 node IAM roles, and list the four tiers in `FOUR_THANOS_TIERS`.
6. **Exercise 6 — Petabyte-Scale Disaster Recovery and Zero-Touch XID 48 Runbooks.** Prove why backing up ten petabytes over a ten-gigabit link takes roughly ninety-two days. Contrast S3 Object Lock WORM Compliance mode with hourly Copy-on-Write storage snapshots, and write the five-step XID 48 runbook for `node-worker-42`.

## Checkpoint questions

<details>
<summary>**1. In Volume 19 Chapter 1, what are the three categories of AI cluster upgrades ranked by blast radius, and why did an emergency apt-get upgrade -y && reboot across 500 nodes blind 400 nodes (80%) to their GPUs?**</summary>

The three upgrade categories are low-risk application container updates, high-risk GPU Operator driver reloads, and extreme-risk OS kernel or firmware reboots. Rebooting into a new Linux kernel without coordinating with the GPU Operator broke the kernel-to-driver ABI because `nvidia.ko` no longer matched the new kernel headers. Restoring service required restarting `nvidia-driver-daemonset` with matching kernel headers so the driver container could recompile `nvidia.ko`.
</details>

<details>
<summary>**2. List the six steps of the Safe Eviction Pipeline and the three stages of the Canary Rollout Strategy in Volume 19 Chapter 1.**</summary>

The six eviction steps are cordoning the node, draining pods with checkpointing, verifying zero GPU processes in `nvidia-smi`, executing the upgrade, running a `dcgmi diag` burn-in, and uncordoning the node. The three canary stages start with soaking one Vanguard Node for twenty-four hours and then upgrading one full rack fault domain. The final stage rolls across the cluster while keeping at least ninety percent of capacity online.
</details>

<details>
<summary>**3. Contrast the Economies of Scale (Dynamic Batching) with the Diseconomies of Scale (Context Windows) in AI capacity forecasting (Volume 19 Chapter 3 Section 1).**</summary>

Dynamic batching provides economies of scale because doubling inference traffic from ten to twenty requests per second packs extra queries into existing CUDA kernels. That raises GPU utilization modestly from forty to fifty-five percent. Context windows create diseconomies of scale because expanding inputs from one-page documents to hundred-page PDFs grows KV-cache memory linearly and triggers immediate out-of-memory crashes.
</details>

<details>
<summary>**4. In Volume 19 Chapter 3, how does the automated FinOps Reaper bot identify and reclaim "zombie" Jupyter notebook pods, and how did DCGM metrics refute a $5 Million (16 HGX H100) hardware request?**</summary>

The FinOps Reaper queries Prometheus continuously and evicts any pod holding a GPU whose `DCGM_FI_PROF_SM_ACTIVE` metric stays below five percent for four hours. To refute the five-million-dollar hardware request, a thirty-day audit showed that ninety-eight percent Kubernetes allocation hid an average Streaming Multiprocessor utilization of only twelve percent. Partitioning staging GPUs into seven `1g.10gb` MIG slices absorbed twelve months of growth for zero capital outlay.
</details>

<details>
<summary>**5. Walk through the three-phase FinOps plan in Volume 19 Chapter 6 that cuts a $500,000/month all-On-Demand AWS GPU bill in half within 30 days.**</summary>

First, cover steady-state production inference with one-year Reserved Instances or Savings Plans for a forty to fifty percent discount, using On-Demand only for burst peaks. Second, move batch training to Spot GPU instances for up to seventy percent savings. Pair Spot nodes with fifteen-minute asynchronous S3 checkpoints and the AWS Node Termination Handler catching the two-minute warning. Third, enable ten-to-one GPU Time-Slicing on development nodes so eighty developers share a single eight-GPU machine.
</details>

<details>
<summary>**6. If nvidia-smi shows 100% GPU Utilization, how do you prove whether the GPU is stalled on PCIe transfers, missing Automatic Mixed Precision (AMP), or suffering from hardware thermal throttling (Volume 19 Chapter 4)?**</summary>

Query DCGM Exporter metrics to separate the three stalls. Maxed-out `DCGM_FI_PROF_PCIE_RX_BYTES` with low SM activity proves a PCIe copy bottleneck that needs `pin_memory=True` or GPUDirect Storage. High FP32 activity with `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` below ten percent proves the job is missing Automatic Mixed Precision. When `DCGM_FI_DEV_GPU_TEMP` hits eighty-five degrees Celsius and `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` asserts `HW_SLOWDOWN`, the GPU is suffering from hardware thermal throttling.
</details>

<details>
<summary>**7. How do you prove that a PyTorch CUDA Out of Memory crash was caused by VRAM fragmentation rather than genuine capacity exhaustion, and what environment variable fixes it (Volume 19 Chapter 4 Section 2)?**</summary>

Inspect the output of `torch.cuda.memory_summary()` after the crash. When `Max Reserved` sits near eighty gigabytes while `Max Allocated` is only forty gigabytes, the remaining free memory is chopped into thousands of small non-contiguous gaps. Setting `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` allows PyTorch to stitch non-contiguous pages together and eliminates the fragmentation crash.
</details>

<details>
<summary>**8. Why is fixing a CUDA OOM on a 70B parameter model fundamentally different from fixing a CUDA OOM on a 1B parameter model (Volume 19 Chapter 11 Interview Question 2)?**</summary>

An out-of-memory error on a one-billion-parameter model is usually caused by activation memory from a large batch size. Lowering the batch size or enabling Gradient Accumulation resolves it. A seventy-billion-parameter model physically cannot fit its static weights, gradients, and Adam optimizer states onto a single eighty-gigabyte GPU even at batch size one. It requires Fully Sharded Data Parallel or ZeRO-3 to shard model states across multiple GPUs.
</details>

<details>
<summary>**9. In Volume 19 Chapter 5, why is ping useless for diagnosing a degraded AI training fabric, and how do you isolate a single bad optical transceiver causing NCCL error 12 across a 128-node 400G RoCEv2 cluster?**</summary>

A degraded optical transceiver uses Forward Error Correction to keep the link up and pass tiny ICMP `ping` packets. However, it drops one in ten thousand burst RDMA packets and triggers Go-Back-N stalls across all nodes. Isolate Node 84 by reading `packet_seq_err`, `out_of_sequence`, `implied_nak_seq_err`, and `local_ack_timeout_err` under `/sys/class/infiniband/<device>/ports/<port>/hw_counters/` alongside `perfquery` symbol counters, then cordon the node and replace the optic.
</details>

<details>
<summary>**10. How do you distinguish a Layer 1 optical fault, a Layer 2 Priority Flow Control (PFC) storm, and a Layer 3 Subnet Manager (OpenSM) routing flap on an AI network (Volume 19 Chapter 5)?**</summary>

A Layer 1 optical fault increments `SymbolErrorCounter` and `LinkDownedCounter` in `perfquery` or `packet_seq_err` on the NIC, requiring fiber or transceiver replacement. A Layer 2 PFC congestion storm drives throughput to zero while `ethtool -S` shows skyrocketing `rx_prio<N>_pause` frames. A Layer 3 routing flap appears in OpenSM logs as continuous Heavy Sweeps triggered by a port flapping up and down.
</details>

<details>
<summary>**11. What are the three physical isolation pillars required to share a GPU cluster safely between competing departments (Volume 19 Chapter 7)?**</summary>

First, enforce compute isolation using hardware MIG slices on shared GPUs and Kubernetes Node Taints for dedicated compliance servers. Second, enforce network isolation using default-deny NetworkPolicies for TCP/IP pod traffic and ConnectX SR-IOV Virtual Functions for kernel-bypass RDMA traffic. Third, enforce storage isolation on Weka or Lustre using per-tenant IOPS and bandwidth QoS limits paired with scoped subdirectory `chroot` mounts.
</details>

<details>
<summary>**12. Why must vulnerability scanning run both in the container registry AND at runtime in the cluster, and how does the Golden Base Image pipeline patch CVEs with zero downtime (Volume 19 Chapter 8)?**</summary>

Nightly registry scans in Harbor or ECR catch vulnerabilities in built images. Runtime agents like Falco, Prisma Cloud, or Aqua catch researchers running `kubectl exec` to install unverified packages inside live pods. When a critical CVE drops, the Golden Base Image pipeline rebuilds and signs the central base image, triggers downstream model rebuilds automatically, and rolls out patched pods via Kubernetes RollingUpdate.
</details>

<details>
<summary>**13. In Volume 19 Chapter 8 Customer Scenario, why did auditors fail a healthcare company whose GPU worker nodes had an AWS IAM policy granting s3:GetObject on the patient-records bucket, and how does IRSA fix it?**</summary>

Attaching S3 permissions to the EC2 node instance profile grants every container scheduled on that machine full access to all patient records, violating least privilege. IAM Roles for Service Accounts removes S3 permissions from the node role and binds a prefix-scoped IAM role via OIDC to the `medical-training-sa` ServiceAccount. That setup injects short-lived STS tokens only into authorized training pods.
</details>

<details>
<summary>**14. What causes a "Cardinality Explosion" in Prometheus on a 1,000-GPU Kubernetes cluster, and how do the 4-Tier Thanos Architecture and Recording Rules prevent 504 Gateway Timeouts (Volume 19 Chapter 9)?**</summary>

Every short-lived training pod adds a unique pod label across hundreds of DCGM metrics per GPU. That creates millions of time-series that exhaust RAM on a single Prometheus server and cause `504 Gateway Timeout` errors during incident queries. The four-tier Thanos architecture separates Scraping Agents, Thanos Receive ingestion, S3 Object Storage, and Thanos Queriers, while Prometheus Recording Rules pre-compute `cluster:gpu:utilization_avg_5m` every five minutes.
</details>

<details>
<summary>**15. Why does traditional nightly backup software fail on a 10-Petabyte AI data lake, and how do Storage Snapshots and Asynchronous Replication replace it (Volume 19 Chapter 10)?**</summary>

Transferring ten petabytes over a ten-gigabit network link takes roughly ninety-two days and saturates core spine switches. Instead, AI storage arrays like Weka, NetApp, and ZFS-backed Lustre take hourly read-only Copy-on-Write pointer snapshots. Those snapshots revert a corrupted petabyte directory in a single API call with at most sixty minutes of lost work, while asynchronous delta replication over dark fiber handles site recovery.
</details>

<details>
<summary>**16. How do you define RPO and RTO for an AI training cluster, and how does S3 Object Lock (WORM) in Compliance Mode defeat ransomware (Volume 19 Chapter 10)?**</summary>

Recovery Point Objective equals your training checkpoint interval so a four-hour checkpoint cadence limits lost compute to four hours. Recovery Time Objective measures the time required to restore storage and resume training. Enabling S3 Object Lock Write Once Read Many in Compliance Mode locks checkpoint objects for a thirty-day retention window during which not even the cloud root account can overwrite or delete them.
</details>

<details>
<summary>**17. In Volume 19 Chapter 11, if GPUs are sitting idle (low compute utilization) during distributed training, what three checks isolate whether the bottleneck is Host CPU, Storage I/O, or 3D Parallelism Network configuration?**</summary>

First, check host CPU utilization: if CPUs are pegged at one hundred percent on image decoding or tokenization, increase dataloader workers or offload preprocessing to NVIDIA DALI. Second, if CPUs are idle with high disk `iowait`, pack small files into WebDataset tarballs or stage data to local NVMe. Third, if GPUs sit idle during heavy InfiniBand traffic, keep Tensor Parallelism strictly intra-node on NVLink with `TP <= 8`.
</details>

<details>
<summary>**18. In Volume 19 Chapter 11 Customer Scenario, a Triton LLM inference service misses its 200 ms p99 SLA while nvidia-smi shows 80–100% utilization. What two metrics prove you do NOT need to buy more GPUs, and what software fixes restore the SLA?**</summary>

First, inspect `nv_inference_queue_duration_us`: if queue latency is spiking, requests are waiting for a worker thread and you should increase the `Instance Group` count in Triton's `config.pbtxt`. Second, inspect `DCGM_FI_DEV_MEM_COPY_UTIL`. If memory bandwidth is pegged at one hundred percent during token decoding, deploy TensorRT-LLM with PagedAttention and INT8 quantization to halve memory bandwidth per token.
</details>

<details>
<summary>**19. Walk through the five-step Operational Runbook for an XID 48 (Double-Bit ECC Error) alert on node-worker-42 GPU 3, and explain how Zero-Touch Ops automates it (Volume 19 Chapter 12).**</summary>

When PagerDuty fires for `XID 48` on `node-worker-42` GPU 3, immediately run `kubectl cordon node-worker-42` and verify device-plugin health. Next, check `dmesg -T | grep NVRM` over SSH, drain the node, and execute a GPU reset or reboot so row remapping takes effect. Open a hardware RMA Jira ticket if the error recurs, and automate the sequence via a Prometheus Alertmanager webhook that cordons the node and files the ticket automatically.
</details>

<details>
<summary>**20. What makes a Senior SRE Follow-the-Sun On-Call Handoff effective compared to a vague status note (Volume 19 Chapter 12 Section 3)?**</summary>

A senior handoff never leaves vague notes about jobs failing earlier. Instead, it records the exact job name, failure count, hardware telemetry signal, affected node, containment status, scheduled UTC maintenance window, and tracking ticket in one concise block. In our reference scenario, the engineer reports three NCCL timeouts on `Llama-3-FineTune`, intermittent PCIe drops on cordoned `node-55`, a `14:00 UTC` `dcgmi diag` maintenance window, and Jira `#4092`.
</details>

## Sources and review notes

### Primary sources read in full for this chapter

All twenty-five mapped `nvidia-devops` files for Chapter 11.29 across Volume 19 and Volume 11, along with *Scalable Kubernetes Infrastructure for AI Platforms* Chapter 2, were read and migrated in full.

```text
Primary Corpus & Volume Notes Mapped to Chapter 11.29:
  1. Volume 19 (Production Operations — all 13 files):
     - nvidia-zero-to-hero/volume-19/index.md
     - nvidia-zero-to-hero/volume-19/chapter-01-cluster-lifecycle-and-upgrade-operations.md
       (3 upgrade blast-radius tiers, 6-step Safe Eviction Pipeline, 3-stage Canary Rollout
        1 Vanguard 24h -> 1 Rack -> Global >= 90%, and 500-node apt-get upgrade 400-node outage)
     - nvidia-zero-to-hero/volume-19/chapter-02-incident-response-and-game-day-execution.md
       (Game Days, XID 48 dcgmi test --inject, ibportstate ... disable, ICS IC/SME/Communications Lead,
        and 99.999% < 5s control-plane master failover)
     - nvidia-zero-to-hero/volume-19/chapter-03-capacity-planning-and-forecasting.md
       (10 -> 20 req/s 40% -> 55% batching vs 100-page PDF KV-cache diseconomy, 3-tier Baseline/Burst/Spot
        model, FinOps Reaper < 5% SM_ACTIVE for 4h, and $5M 16 HGX H100 rejection at 98% allocation vs 12% SM_ACTIVE over 30 days)
     - nvidia-zero-to-hero/volume-19/chapter-04-gpu-memory-and-utilization-troubleshooting.md
       (100% utilization lie vs SM_ACTIVE, TENSOR_ACTIVE < 10%, PCIE_RX_BYTES, FP16 vs FP32; 80 GB Reserved
        vs 40 GB Allocated fragmentation with 10,000 x 2 MB gaps fixed by PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True;
        and 2:00 PM 40% slowdown from 85C HW_SLOWDOWN 1500 -> 500 MHz)
     - nvidia-zero-to-hero/volume-19/chapter-05-network-reliability-and-fabric-validation.md
       (1 in 10,000 RDMA drop Go-Back-N stall across 1,000 GPUs, Layer 1 perfquery SymbolErrorCounter/LinkDownedCounter,
        Layer 2 PFC storm rx_prio<N>_pause, Layer 3 OpenSM heavy sweep, and 128-node 400G RoCEv2 NCCL error 12
        isolated to Node 84 via hw_counters/packet_seq_err)
     - nvidia-zero-to-hero/volume-19/chapter-06-cost-optimization-and-resource-efficiency.md
       ($20 CPU VM vs $2,000+ p4d.24xlarge weekend waste, Spot 15-min async S3 checkpoints + 2-min AWS Node
        Termination Handler, and cutting a $500,000/month AWS bill in half within 30 days via 1-Year RIs 40-50% off,
        Spot 70% off, and 80 devs on 1 8-GPU node via 10:1 time-slicing)
     - nvidia-zero-to-hero/volume-19/chapter-07-multi-tenancy-and-workload-isolation.md
       (Compute MIG/Taints, Network NetworkPolicy + SR-IOV VFs, Storage Weka/Lustre IOPS QoS + chroot, and
        500 students + 5 labs 10-job OOM scenario fixed via 7 x 1g.10gb MIG)
     - nvidia-zero-to-hero/volume-19/chapter-08-security-operations-and-compliance.md
       (Nightly Harbor/ECR scan + runtime Falco/Prisma/Aqua, Golden Base Image rolling updates, SIEM audit logs,
        and IRSA medical-training-sa)
     - nvidia-zero-to-hero/volume-19/chapter-09-monitoring-and-observability-at-scale.md
       (1,000 GPUs x 500 metrics/sec cardinality explosion, 4-tier Thanos/Cortex architecture, 5-min Recording Rules
        cluster:gpu:utilization_avg_5m, and 200-node 60s 504 Gateway Timeout scenario)
     - nvidia-zero-to-hero/volume-19/chapter-10-disaster-recovery-and-data-resilience.md
       (10 PB over 10 Gbps = ~92 days, RPO = 4h checkpoint interval, RTO = 3 weeks for 5 PB Glacier, 50 TB checkpoints
        with S3 Object Lock WORM 30-day Compliance mode, and 1 PB NVMe 1-hour Copy-on-Write snapshots)
     - nvidia-zero-to-hero/volume-19/chapter-11-performance-debugging-and-bottleneck-identification.md
       (Universal Diagnostic Matrix, Triton 200 ms p99 SLA breach nv_inference_queue_duration_us config.pbtxt +
        DCGM_FI_DEV_MEM_COPY_UTIL TensorRT-LLM PagedAttention + INT8, and 1B vs 70B FSDP/ZeRO-3 OOM)
     - nvidia-zero-to-hero/volume-19/chapter-12-on-call-handoff-and-operational-runbooks.md
       (XID 48 5-step runbook on node-worker-42 GPU 3, Alertmanager webhook zero-touch remediation, and
        Follow-the-Sun handoff on node-55 Jira #4092)
  2. Volume 11 (GPU Sharing — all 12 mapped files):
     - nvidia-zero-to-hero/volume-11/index.md
     - nvidia-zero-to-hero/volume-11/chapter-01-why-gpu-sharing-exists.md
     - nvidia-zero-to-hero/volume-11/chapter-07-kubernetes-scheduling-for-shared-gpus.md
     - nvidia-zero-to-hero/volume-11/chapter-08-tenant-isolation-security-and-fairness.md
     - nvidia-zero-to-hero/volume-11/chapter-09-capacity-planning-and-chargeback.md
     - nvidia-zero-to-hero/volume-11/chapter-10-observability-and-slos-for-shared-gpus.md
     - nvidia-zero-to-hero/volume-11/chapter-11-production-troubleshooting.md
     - nvidia-zero-to-hero/volume-11/chapter-12-volume-11-summary.md
     - nvidia-zero-to-hero/volume-11/labs/lab-01-configure-and-validate-mig.md
     - nvidia-zero-to-hero/volume-11/labs/lab-02-configure-kubernetes-gpu-time-slicing.md
     - nvidia-zero-to-hero/volume-11/labs/lab-03-compare-sharing-performance-and-isolation.md
     - nvidia-zero-to-hero/volume-11/labs/lab-04-troubleshoot-a-multi-tenant-gpu-node.md
  3. Book Sources from the Local TOON-RAG Corpus:
     - Ajay Vohra, Scalable Kubernetes Infrastructure for AI Platforms
       (scalable-kubernetes-infrastructure-for-ai-platfo, 2026, Chapter 2: Model Development on Kubernetes)
```

### Related source files mapped in MIGRATION_MAP.md

- Every mapped file in Volume 11 and Volume 19 for Chapter 11.29 is cited and covered in the text and tables above.

### Run here

- The local verification suite `python3 code/part11/multi_tenancy_quotas_fault_tolerance_health_lab.py` was executed here and passed all twenty-five checks.

### Explicitly labelled inferences

- None; every scenario, threshold, and metric name comes directly from Volume 19 and Volume 11.

### Not verified on live hardware

- All cluster commands for `kubectl` (`NVAIE` licensing, `num_workers`), `perfquery`, `sysfs` hardware counters (`rx_pause_ctrl_phy`, `FP16_ACTIVE`, `FP32_ACTIVE`), and Prometheus rules (from `chapter-01-cluster-lifecycle-and-upgrade-operations.md`, `chapter-02-incident-response-and-game-day-execution.md`, `chapter-03-capacity-planning-and-forecasting.md`, `chapter-04-gpu-memory-and-utilization-troubleshooting.md`, `chapter-05-network-reliability-and-fabric-validation.md`, `chapter-06-cost-optimization-and-resource-efficiency.md`, `chapter-07-multi-tenancy-and-workload-isolation.md`, `chapter-08-security-operations-and-compliance.md`, `chapter-09-monitoring-and-observability-at-scale.md`, `chapter-10-disaster-recovery-and-data-resilience.md`, `chapter-11-performance-debugging-and-bottleneck-identification.md`, and `chapter-12-on-call-handoff-and-operational-runbooks.md`) are marked `(untested here)`.

### Not in the corpus

- Cloud-provider-specific Terraform modules for provisioning Thanos Receive S3 buckets are outside the corpus scope, so this chapter focuses on the four-tier Thanos architecture and Recording Rules from Volume 19 Chapter 9.

### Corrections to the author's notes

- Validation pass 2026-10-25 confirmed that `validate_chapter.py` and `check_coverage.py` pass, and all YAML manifests and commands are marked untested. Custom resource API versions such as `kueue.x-k8s.io/v1beta1` or `resource.k8s.io/v1` change across releases, so verify them against your cluster version.
- Native Copy-on-Write filesystem snapshots work out of the box on Weka and NetApp, whereas Lustre requires ZFS-backed OST and MDT storage targets.

