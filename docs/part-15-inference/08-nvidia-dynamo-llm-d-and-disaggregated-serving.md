---
id: "c15-08"
title: "15.8 NVIDIA Dynamo, llm-d and disaggregated serving"
sidebar_label: "15.8 NVIDIA Dynamo, llm-d and disaggregated serving"
sidebar_position: 8
description: "Disaggregated prefill and decode serving with NVIDIA Dynamo, Smart Router KV-cache-aware routing, GPU Planner SLO-driven worker scaling, NIXL asynchronous transfers, 4-tier KV cache offloading, and Kubernetes llm-d Gateway API Inference Extension."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 15.8 NVIDIA Dynamo, llm-d and disaggregated serving

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE + Local Python Verification Lab |
| Part | Part 15: LLM inference and serving |
| Primary sources | *AI Systems Performance Engineering* (`ai-systems-performance-engineering`) Chapters 4, 15, 17, 18; *Generative AI on Kubernetes* (`generative-ai-on-kubernetes`) Chapter 4; *Distributed AI Systems* (`distributed-ai-systems`) Chapter 9; *Hands-On LLM Serving and Optimization* (`hands-on-llm-serving-and-optimization`) Chapter 7; NVIDIA Zero-to-Hero Volume 12 (`chapter-01-why-inference-infrastructure-is-different.md`, `chapter-08-kv-cache-memory-and-concurrency.md`, `chapter-09-scaling-multi-gpu-and-multi-node-inference.md`) |
| Cross-references | Chapter 15.1 (Anatomy of an inference request); Chapter 15.3 (vLLM in depth); Chapter 15.4 (SGLang and RadixAttention); Chapter 15.5 (TensorRT-LLM); Chapters 15.10–15.11 (Prefill and decode disaggregation and advanced KV tuning) |
| Code | `code/part15/dynamo_disaggregated_serving.py`, `code/part15/dynamo_disaggregated_serving_lab.py` |
| Coverage file | `planning/coverage/chapters/15-08.md` |
| Claim & number ledger | `planning/ledgers/15-08.md` |

## Why this matters for AI infrastructure

Running prefill and decode on the same GPU pool forces two incompatible workloads to fight for the same silicon. When a user submits a long document prompt alongside dozens of active chat sessions, the compute-heavy prefill pass monopolizes the Tensor Cores. Every ongoing token stream stalls until that prompt finishes.

Engineers call this bottleneck prefill-decode interference. It forces traditional monolithic serving clusters into a painful compromise.
- **Head-of-line blocking on streaming tokens:** A single multi-thousand-token prompt can pause ongoing decode iterations for hundreds of milliseconds. Users see frozen text streams and severe spikes in Time Per Output Token.
- **Mismatched hardware and parallelism:** Prefill is compute bound and thrives on high Tensor Parallelism and dense matrix math. Decode is memory-bandwidth bound and suffers when cross-GPU synchronization is too wide. A colocated server must apply one hardware type and one parallelism degree to both phases.
- **Collapsed cluster goodput:** Goodput counts only the requests per second that satisfy both Time To First Token and Time Per Output Token Service Level Objectives simultaneously. In a colocated cluster, whichever phase saturates first drags down the usable capacity of the entire GPU fleet.

```text
Colocated vs Disaggregated Serving Reference Numbers (ASP Chapters 4, 17, 18; HLS Chapter 7; GAK Chapter 4):
- MLPerf Inference v5.0 (2025) p99 SLOs:
  Llama-2-70B:       TTFT <= 450 ms,   TPOT <= 40 ms
  Llama-3.1-405B:    TTFT <= 6,000 ms (6 s), TPOT <= 175 ms
- DistServe Colocated vs 2P1D Disaggregated Goodput (P90 TTFT <= 400 ms [0.4 s], P90 TPOT <= 40 ms [0.04 s]):
  Colocated (1 GPU): ~3.0 RPS under TTFT bound, 1.6 RPS under TPOT bound -> Goodput = min(3.0, 1.6) = 1.6 RPS/GPU
  Disaggregated 2P1D (2 Prefill GPUs + 1 Decode GPU = 3 GPUs total):
    Prefill pool: 5.6 RPS/GPU * 2 GPUs = 11.2 RPS; Decode pool: 10.0 RPS on 1 GPU
    Total Goodput = min(11.2, 10.0) = 10.0 RPS across 3 GPUs = 3.33 RPS/GPU (3.3 RPS/GPU, 2.08x per-GPU gain)
  DistServe broad benchmark gains: up to 7.4x higher goodput or 12.6x tighter latency SLOs
- NVIDIA Dynamo + NIXL Fleet Benchmarks:
  Up to 30x higher inference throughput on a 680B-parameter MoE LLM (DeepSeek-R1) on a 72-GPU GB200 NVL72 rack (130 TB/s)
  KV cache offload TTFT speedup: 14x on x86 + H100 PCIe vs recompute; additional 2x on Grace Hopper GH200 (900 GB/s NVLink-C2C)
- Disaggregated KV Transfer Fabric Demand (16 RPS * 1.5 GB KV/req = 24.0 GB/s [~25 GB/s]):
  Fits NVLink 4 (900 GB/s), NVLink 5 (1,800 GB/s), and 400G/800G InfiniBand/RoCE RDMA (50–100 GB/s, 500–600 Gbps pod fabric)
  Saturates non-RDMA PCIe/TCP fallback (10 GB/s) and standard Kubernetes pod Ethernet (10–20 Gbps)
```

Two open-source production stacks solve this problem at cluster scale. NVIDIA Dynamo coordinates disaggregated prefill and decode pools using a KV-cache-aware Smart Router, an SLO-driven GPU Planner, the NVIDIA Inference Transfer Library, and a four-tier Distributed KV Cache Manager. In parallel, the llm-d project brings disaggregated vLLM serving and the Gateway API Inference Extension natively into Kubernetes. **Before you scale a large model cluster by adding more monolithic replicas, separate prefill from decode so each phase can scale and route independently**.

## Prerequisites and outcomes

### Prerequisites
- Inference latency metrics, arithmetic intensity, and KV cache sizing equations from Chapters 15.1 and 15.2.
- PagedAttention block tables, continuous batching, and RadixAttention prefix caching from Chapters 15.3 and 15.4.
- TensorRT-LLM and Triton execution backends from Chapters 15.5 and 15.6.
- GPUDirect RDMA, NVLink, and GPUDirect Storage fundamentals from Parts 12 and 13.

### Outcomes
After completing this chapter, you will be able to.
1. Quantify prefill-decode interference and calculate cluster goodput across colocated and disaggregated worker pools under strict TTFT and TPOT Service Level Objectives.
2. Architect an NVIDIA Dynamo cluster using etcd service discovery, NATS request queues, and decode-centric request orchestration.
3. Implement Dynamo Smart Router policies that combine prefix cache hit length, queue depth, KV occupancy, and memory bandwidth into a single routing decision.
4. Configure Dynamo GPU Planner autoscaling rules, Quality of Service capacity reservations, and early rejection admission control.
5. Program nonblocking KV cache transfers with NIXL, collate PagedAttention blocks for RDMA efficiency. Size a four-tier KV cache offloading hierarchy across GPU HBM, Grace CPU DRAM, local NVMe, and remote storage.
6. Deploy llm-d on Kubernetes using InferencePool, InferenceObjective, and the Envoy Endpoint Picker protocol.

---

## 1. Why Colocated Serving Breaks Under Dual SLOs

### 1.1 Prefill-Decode Interference and Head-of-Line Blocking

Every large language model request passes through two distinct computational phases. First, the prefill phase ingests all tokens of the user prompt in parallel to populate the attention Key-Value cache and emit the first token. Second, the decode phase generates subsequent tokens one by one by reading the model weights and the growing KV cache on every step.

Those two phases stress completely different parts of the GPU. Prefill executes large matrix-matrix multiplications that saturate the Tensor Cores and reach high arithmetic intensity. Decode executes skinny matrix-vector products that are starved by High Bandwidth Memory transfer speed. On an eighty-gigabyte H100 GPU with 3,350 GB/s of HBM3 bandwidth, simply reading 140 GB of FP16 weights for a seventy-billion-parameter model takes 41.7 ms per step. That memory wall caps a single decode stream at roughly 24 tokens per second regardless of how much compute the chip has.

When a monolithic server colocates prefill and decode on the same GPU, the scheduler must interleave massive prompt prefills with latency-sensitive decode iterations. If a user submits a multi-thousand-token prompt, that prefill batch locks the GPU for hundreds of milliseconds. Every active user waiting for their next streaming token experiences a sudden pause. Even when chunked prefill slices long prompts into smaller pieces, both phases still compete for the same HBM capacity, memory bandwidth, and CUDA streams.

### 1.2 The Goodput Imperative and DistServe Math

Raw token throughput is a misleading metric for interactive AI services. If a cluster generates thousands of tokens per second while violating user latency budgets, those delayed responses are useless. **Goodput measures the number of completed requests per second that simultaneously satisfy both the Time To First Token and Time Per Output Token Service Level Objectives**.

Consider the benchmark evaluation from DistServe and *AI Systems Performance Engineering* Chapter 17. The service enforces a ninetieth-percentile TTFT budget of 0.4 seconds and a ninetieth-percentile TPOT budget of 0.04 seconds. When prefill and decode are colocated on a single GPU, the server can sustain 3.0 RPS within the TTFT ceiling alone. However, prefill interference degrades token generation so severely that the server can sustain only 1.6 RPS within the TPOT ceiling. Because goodput requires meeting both targets at once, the colocated GPU delivers only 1.6 RPS of goodput.

Now separate the workload into a disaggregated pool with two prefill GPUs and one decode GPU, known as a 2P1D topology. Freed from decode interruptions, each prefill worker reaches 5.6 RPS, giving 11.2 RPS of aggregate prefill capacity across the two prefill GPUs. Freed from heavy prompt GEMMs, the dedicated decode GPU sustains 10.0 RPS within the 40 ms TPOT budget.

```text
DistServe Colocated vs Disaggregated 2P1D Goodput Derivation (ASP Chapter 17):
1. Target SLOs:
   P90 TTFT <= 0.4 s (400 ms)
   P90 TPOT <= 0.04 s (40 ms)

2. Colocated Baseline (1 GPU handling both Prefill and Decode):
   Max RPS meeting TTFT SLO:  R_ttft = 3.0 RPS
   Max RPS meeting TPOT SLO:  R_tpot = 1.6 RPS
   Colocated Goodput per GPU: G_colocated = min(3.0, 1.6) = 1.6 RPS/GPU

3. Disaggregated 2P1D Pool (N_p = 2 Prefill GPUs, N_d = 1 Decode GPU, N_total = 3 GPUs):
   Prefill pool capacity:     R_prefill_total = 2 * 5.6 RPS = 11.2 RPS
   Decode pool capacity:      R_decode_total  = 1 * 10.0 RPS = 10.0 RPS
   Cluster Goodput (3 GPUs):  G_cluster       = min(11.2, 10.0) = 10.0 RPS
   Disaggregated Goodput/GPU: G_disagg        = 10.0 RPS / 3 GPUs = 3.33 RPS/GPU (reported as 3.3 RPS/GPU)
   Per-GPU Goodput Speedup:   3.33 / 1.6      = 2.08x higher goodput per GPU
```

| Deployment Architecture | Prefill Pool Capacity | Decode Pool Capacity | Cluster Goodput | Goodput per GPU | Bottleneck & Operational Behavior |
|---|---|---|---|---|---|
| Colocated Monolith (1 GPU) | 3.0 RPS (TTFT bound) | 1.6 RPS (TPOT bound) | 1.6 RPS | 1.6 RPS/GPU | Long prefills stall active decode streams and breach the 40 ms TPOT SLO. |
| Disaggregated 2P1D (3 GPUs) | 11.2 RPS (2 x 5.6 RPS) | 10.0 RPS (1 x 10.0 RPS) | 10.0 RPS | 3.3 RPS/GPU | Isolated phases meet both 400 ms TTFT and 40 ms TPOT SLOs simultaneously (2.08x per GPU). |
| DistServe Full Fleet Range | Tuned per workload | Tuned per workload | Up to 7.4x baseline | Up to 7.4x | Supports up to 12.6x tighter latency SLOs before goodput collapses. |
| NVIDIA Dynamo on GB200 NVL72 | Dedicated Prefill GPUs | Dedicated Decode GPUs | Up to 30x baseline | Up to 30x | 680B MoE model (DeepSeek-R1) across 72 Blackwell GPUs linked at 130 TB/s. |

Before you provision extra GPUs to fix p99 token stalls, check whether colocated prefill bursts are starving your decode loop and calculate the goodput gain of splitting the pools.

---

## 2. NVIDIA Dynamo Architecture: Control Plane, Smart Router, and GPU Planner

### 2.1 The Four Pillars of NVIDIA Dynamo

Disaggregating prefill and decode turns a single-node engine into a distributed pipeline. If a router sends a prompt to a worker that lacks the cached prefix. If the KV cache transfer stalls over TCP sockets, network overhead erases the gains of disaggregation.

NVIDIA released the open-source Dynamo distributed inference framework to orchestrate disaggregated serving across multi-node clusters and rack-scale superchips. Written in Rust and Python, Dynamo sits above execution engines such as TensorRT-LLM, vLLM, SGLang, and PyTorch. It coordinates the cluster through four specialized subsystems.
1. **Dynamo Smart Router:** A KV-cache-aware and load-aware request router that tracks cached prefixes across the fleet and decides whether each prompt should prefill locally or remotely.
2. **Dynamo GPU Planner:** An SLO-driven capacity controller that continuously monitors TTFT, TPOT, queue depth. KV saturation to scale prefill and decode workers or flip GPU roles on the fly.
3. **NVIDIA Inference Transfer Library, NIXL,:** A nonblocking point-to-point data transport engine that streams KV cache blocks directly between GPU HBM, CPU DRAM, local NVMe SSDs, and remote storage.
4. **Distributed KV Cache Manager:** A multi-tier memory manager that evicts colder KV blocks from scarce GPU HBM into larger, cheaper memory tiers and prefetches them back when needed.

```mermaid
flowchart TB
    Client["Client HTTP / gRPC Request"] --> Router["Dynamo Smart Router<br/>(KV-Cache & Load Aware)"]

    subgraph ControlPlane["Distributed Control Plane"]
        Etcd["etcd Registry<br/>(Worker Discovery & Leases)"]
        NATS["NATS Event & Queue Bus<br/>(KV Events & Prefill Queue)"]
        Planner["Dynamo GPU Planner<br/>(SLO-Driven Autoscale & Flip)"]
    end

    subgraph DecodePool["Decode Worker Pool (e.g., 8x B300 / H200)"]
        DecW["Decode Worker (Ingress Coordinator)<br/>Allocate KV Blocks & Stream Tokens"]
    end

    subgraph PrefillPool["Prefill Worker Pool (e.g., 4x B200 / H100)"]
        PreW["Prefill Worker<br/>Compute Prompt GEMMs & Populate KV"]
    end

    subgraph KVPool["4-Tier Distributed KV Cache Manager"]
        T1["Tier 1: GPU HBM"] --> T2["Tier 2: Grace / Host DRAM"]
        T2 --> T3["Tier 3: Local NVMe (GDS)"]
        T3 --> T4["Tier 4: Remote Object / Lustre"]
    end

    Router -->|"1. Route to Warm/Free Worker"| DecW
    DecW -->|"2. should_offload_prefill() -> Put Queue"| NATS
    NATS -->|"3. Pull RemotePrefillRequest"| PreW
    PreW <==>|"4. NIXL Zero-Copy RDMA / NVLink Write"| DecW
    PreW <-->|"Read/Offload Prefix KV"| KVPool
    DecW <-->|"Read/Evict Active KV"| KVPool
    Planner -.->|"Watch TTFT/TPOT & Scale Leases"| Etcd
    Etcd -.->|"Register NIXL Descriptors"| DecW
    Etcd -.->|"Register NIXL Descriptors"| PreW
```

### 2.2 Decode-Centric Request Flow with `etcd` and NATS

Under the hood, Dynamo relies on etcd for worker registration, health leases, and NIXL memory descriptor exchange, while using NATS for high-speed messaging and global work queues. Rather than forcing a central proxy to manage every byte of intermediate state, Dynamo uses a **decode-centric request lifecycle**.
1. **Worker registration and descriptor trim:** At startup, each decode and prefill worker registers its presence and lease in etcd. Each decode worker pre-registers a pinned GPU HBM region with NIXL and publishes compact transfer descriptors so peers can write to its memory using a lightweight buffer ID.
2. **Decode-side ingress and pre-allocation:** When a new request arrives at a decode worker, its local scheduler allocates PagedAttention KV blocks for the prompt and runs should_offload_prefill() to decide whether remote prefill is worthwhile.
3. **Global prefill queue handoff:** If remote prefill is selected, the decode worker publishes a RemotePrefillRequest message containing the prompt tokens, its origin worker ID. The target KV block IDs onto the NATS global prefill queue. While waiting, the decode worker continues running decode steps for other active sequences.
4. **Prefill execution and NIXL RDMA push:** An available prefill worker pulls the task from NATS. Reads any matching prefix blocks from the KV cache pool, computes the prefill forward pass for the remaining tokens. Uses NIXL to push the resulting KV tensors directly into the decode worker's GPU HBM via NVLink or GPUDirect RDMA.
5. **Autoregressive decode resumption:** Once the NIXL transfer completes, the decode worker slots the request into its continuous batching loop and streams output tokens back to the client.

```yaml
# NVIDIA Dynamo Heterogeneous Cluster Role Definition (ASP Chapter 17)
roles:
  - name: prefill_worker          # Compute-bound prompt ingestion pool
    model_path: models/llm-70b
    instance_count: 4             # 4 prefill workers
    gpu_type: B200                # Blackwell B200 (or Rubin CPX) for dense GEMM FLOPS
  - name: decode_worker           # Memory-bandwidth-bound token generation pool
    model_path: models/llm-70b
    instance_count: 8             # 8 decode workers
    gpu_type: B300                # Blackwell Ultra B300 (180 GB HBM -> ~122 GB KV pool)
```

### 2.3 Smart Router: Conditional Disaggregation and Composite Cost Scoring

Not every request should be offloaded to a remote prefill worker. Sending a five-token greeting or a prompt that is already ninety percent cached in local HBM across the network wastes queue time and RDMA bandwidth. **The Smart Router only disaggregates a request when the compute saved by remote prefill exceeds the queueing and transfer overhead**.

The router first calculates the effective uncached prompt length by subtracting the matched prefix cache length from the total prompt length. It then checks three runtime thresholds.

```python
# Decode-worker conditional prefill offload policy (B200/B300 tuned, ASP Chapter 17)
def should_offload_prefill(
    prompt_length: int,
    prefix_cached_length: int,
    prefill_queue_size: int,
    decode_active_reqs: int,
    ttft_slo_ms: int = 500,
) -> bool:
    eff_len = max(0, prompt_length - prefix_cached_length)

    PREFILL_LENGTH_THRESHOLD = 256  # split_policy.prompt_length_threshold
    PREFILL_QUEUE_MAX = 10          # max pending tasks before prefill pool is saturated
    DECODE_LOAD_THRESHOLD = 8       # active decode streams on local worker

    long_prefill = eff_len >= PREFILL_LENGTH_THRESHOLD
    prefill_available = prefill_queue_size < PREFILL_QUEUE_MAX

    # 1. Offload when uncached prompt is long and prefill pool has queue headroom
    if long_prefill and prefill_available:
        return True
    # 2. Offload moderate prompts when local decode worker is heavily loaded
    if decode_active_reqs >= DECODE_LOAD_THRESHOLD and eff_len >= 64 and prefill_available:
        return True
    # 3. Otherwise execute prefill locally on the decode GPU
    return False
```

Notice how PREFILL_QUEUE_MAX acts as an automatic circuit breaker. If a sudden burst of long prompts pushes the global prefill queue to ten or more waiting tasks. Prefill_available turns false and decode workers automatically fall back to computing prefills locally. Once the prefill tier drains its backlog, remote offloading resumes seamlessly.

 Dynamo also exposes this conditional policy declaratively in YAML by computing a weighted remote prefill score and comparing it against remote_prefill_min_score.

```yaml
# NVIDIA Dynamo conditional disaggregation scoring policy (ASP Chapter 17)
disaggregated_router:
  enable: true
  policies:
    - metric: prefill_length        # Effective prompt length after prefix cache hit
      threshold: 256
      action: prefer_remote         # Vote for remote prefill when eff_len > 256
      weight: 0.7
    - metric: prefill_queue_depth   # Tasks waiting in global prefill queue
      threshold: 10
      action: prefer_local          # Vote for local prefill when queue > 10
      weight: 0.3
  remote_prefill_min_score: 0.5     # Offload if weighted remote score > 0.5
```

When selecting *which* worker in a pool should receive a request, the Smart Router evaluates a latency cost function where lower cost is preferred. A basic load-only router combines GPU occupancy and active request count.

```text
Simple Load Cost = 0.7 * occupancy_percent + 0.3 * active_req_count
```

However, a load-only router ignores data locality and will happily send a request to an empty worker that must recompute thousands of prefix tokens from scratch. Dynamo's KV-aware Smart Router listens to KV cache allocation and eviction events published by workers over NATS and adds cache locality and memory bus pressure into a five-factor composite cost.

```text
Composite Latency Cost (ASP Chapter 17, Table 17-3 — lower score is better):
latency_cost = 3.0 * occupancy_percent
             + 1.0 * active_reqs
             - 10.0 * int(cache_match_flag)
             + 0.5 * mem_bw_percent
             - 1.0 * int(recent_prefix_flag)

Worked Routing Comparison:
- Worker 0 (Cold, lightly loaded): occupancy = 1.0, active_reqs = 2, cache_match = 0, mem_bw = 2.0, recent_prefix = 0
  Simple cost    = 0.7*(1.0) + 0.3*(2) = 1.3 (picked by naive router)
  Composite cost = 3.0*(1.0) + 1.0*(2) - 10.0*(0) + 0.5*(2.0) - 1.0*(0) = 6.0
- Worker 1 (Warm, slightly busier): occupancy = 2.0, active_reqs = 3, cache_match = 1, mem_bw = 4.0, recent_prefix = 1
  Simple cost    = 0.7*(2.0) + 0.3*(3) = 2.3
  Composite cost = 3.0*(2.0) + 1.0*(3) - 10.0*(1) + 0.5*(4.0) - 1.0*(1) = 0.0 (picked by KV-aware Smart Router)
```

| Routing Factor | Telemetry Variable | Weight | Engineering Purpose |
|---|---|---|---|
| KV Occupancy (%) | `occupancy_percent` | `+3.0` | Penalizes workers approaching HBM KV pool exhaustion. |
| Active Requests | `active_reqs` | `+1.0` | Penalizes workers with deep in-flight continuous batches. |
| Exact KV Cache Match | `cache_match_flag` | `-10.0` | Strongly rewards workers that already hold the prompt prefix in HBM. |
| Memory Bandwidth (%) | `mem_bw_percent` | `+0.5` | Avoids decode GPUs whose HBM buses are saturated by long sequences. |
| Recent Prefix Use | `recent_prefix_flag` | `-1.0` | Rewards workers where the prefix is warm in L2 or already in flight via NIXL. |

### 2.4 Dynamo GPU Planner, QoS Tiers, and Early Rejection

Even with optimal per-request routing, a fixed ratio of prefill to decode GPUs will fail when traffic patterns shift. An afternoon surge of document summarization requests requires heavy prefill capacity and minimal decode capacity. An evening surge of chain-of-thought reasoning requests with short prompts and multi-thousand-token outputs requires the exact opposite.

The **Dynamo GPU Planner** closes this control loop. It continuously scrapes worker telemetry and compares realized TTFT and TPOT percentiles against application SLOs. When prefill queues grow, the Planner scales up prefill replicas or revokes etcd leases on idle decode workers to flip their role to prefill. In research evaluations such as Arrow, adaptive instance scaling across shifting input-output ratios achieved up to 5.6x higher request serving rates than static prefill-decode partitions.

```yaml
# NVIDIA Dynamo GPU Planner Policy Configuration (ASP Chapter 17)
model: meta-llama/Llama-3.1-70B-Instruct
split_policy:
  prompt_length_threshold: 256
  prefix_cache_weight: 10.0
  queue_length_weight: 1.5
  decode_load_weight: 0.5
  enable_hotspot_prevention: true
cache:
  reuse_prefix: true
  min_cache_hit_ratio: 0.75
autoscale:
  prefill:
    min_replicas: 4
    max_replicas: 12
    scale_up: { queue_length: 8, gpu_utilization: 80 }
    scale_down: { queue_length: 2, gpu_utilization: 40 }
  decode:
    min_replicas: 8
    max_replicas: 24
    scale_up: { queue_length: 16, kv_cache_usage: 75 }
    scale_down: { queue_length: 4, kv_cache_usage: 30 }
qos:
  enable_early_rejection: true
  low_priority_threshold_ms: 500
  reject_on_slo_violation: true
```

When traffic bursts exceed the maximum physical size of the cluster, autoscaling alone cannot protect tail latency. If the cluster admits every arriving request, queues build up and every user misses their latency target. Dynamo prevents overload cascades by combining **tiered QoS capacity reservations** with **early rejection admission control**.

```yaml
# NVIDIA Dynamo QoS Tier Reservation Policy (configs/qos.yaml, ASP Chapter 18)
scheduler:
  qos_classes:
    - name: premium
      reserved_fraction: 0.10   # Reserve 10% of prefill/decode workers exclusively for premium
      priority: 100
    - name: standard
      reserved_fraction: 0.30   # Reserve 30% of workers for standard tier
      priority: 50
    - name: free
      reserved_fraction: 0.60   # Share remaining 60% capacity for free/batch tier
      priority: 10
  request_router:
    routes:
      - match: { header: "x-customer-tier: premium" }
        qos: premium
      - match: { header: "x-customer-tier: standard" }
        qos: standard
      - match: {}
        qos: free
```

Before admitting a request into the prefill or decode queues, the QoSController estimates the expected TTFT from the current queue lengths and exponential moving averages of per-request prefill and decode durations. If the estimated TTFT exceeds the 500 ms SLO budget and the request belongs to a low-priority tier, the controller immediately sheds the request. Disables remote prefill for it, so premium and standard traffic continue meeting their latency guarantees. Always pair conditional disaggregation in the Smart Router with GPU Planner autoscaling and early rejection so traffic spikes degrade gracefully instead of stalling the cluster.

### 2.5 Worker Discovery, Leases, and Role Swapping

A disaggregated pool only works if the router knows which workers are alive. NVIDIA Dynamo's distributed runtime uses etcd for worker discovery and leases. A worker that joins the cluster becomes visible to the rest of the system. A lease tracks whether that worker is still part of the pool.

The Planner uses the same mechanism to change the cluster's shape. It can scale workers down by revoking their leases. It can scale them up by launching new workers, which are discovered automatically. Think of a lease as a timed pass: revoke it, and the worker leaves the pool.

This flexibility matters most at ultrascale, where load rises and falls often. When it does, you want to swap workers between roles as needed, not restart the cluster.

---

## 3. NIXL: The NVIDIA Inference Transfer Library

### 3.1 Why Disaggregated Serving Needs NIXL Alongside NCCL

In distributed training and intra-node Tensor Parallelism, every GPU participates in synchronized group collectives such as AllReduce. NVIDIA NCCL is purpose-built for those many-to-many barriers. Disaggregated inference, however, introduces a completely different communication pattern. When a prefill worker finishes a prompt, it must push a multi-gigabyte KV cache to a single target decode worker or offload cold KV blocks to CPU DRAM or NVMe storage. Both GPUs keep running independent forward passes.

Using synchronous NCCL collectives for dynamic, one-to-one KV handoffs forces ranks into lockstep barriers and cannot address heterogeneous memory tiers like host DRAM, NVMe SSDs, or S3 object stores. **NVIDIA created the NVIDIA Inference Transfer Library, NIXL, to provide a unified, nonblocking, point-to-point data transport across GPU HBM, CPU DRAM, local NVMe storage, and network filesystems**.

| Dimension | NCCL (Collective Communication) | NIXL (Point-to-Point Inference Transfer) |
|---|---|---|
| Primary Use Case | Many-to-many collectives (AllReduce, AllGather, ReduceScatter) for training and intra-layer TP. | One-to-one or one-to-few transfers of KV caches and pipeline states across disaggregated stages. |
| Synchronization Semantics | Synchronized group barrier; all participating ranks must invoke the collective together. | Fully asynchronous initiator-to-target read/write (`prepXfer`, `postXfer`, `checkXfer` polling). |
| Supported Memory Tiers | GPU HBM (plus host-staged network buffers). | Unified across GPU HBM (`VRAM_SEG`), CPU DRAM (`DRAM_SEG`), local NVMe SSD via GDS, and remote S3/Lustre. |
| Transport Selection | Rings, trees, NVLS, and SHARP over NVLink and InfiniBand/RoCE. | Interconnect-agnostic via plugins (NVLink/NVSwitch, GPUDirect RDMA / UCX, IBGDA, GPUDirect Storage). |
| Typical Payload Scope | Small-to-medium tensor buckets (e.g., 25 MB to 100 MB gradients) reduced across all ranks. | Large KV cache slabs (hundreds of megabytes to multiple gigabytes) moved point-to-point. |

### 3.2 NIXL 0.5.x Architecture, `nixlAgent` Lifecycle, and IBGDA

NIXL exposes a single endpoint abstraction called nixlAgent. Each prefill worker, decode worker, or storage node instantiates its own nixlAgent configured with transport backend plugins such as UCX for GPU-to-GPU RDMA and GDS for GPUDirect Storage.

Under the hood, NIXL eliminates host CPU bounce buffers and kernel context switches. Within a server or a seventy-two-GPU GB200 NVL72 rack, NIXL routes transfers directly across NVLink and the 130 TB/s NVSwitch fabric. Across nodes or racks, NIXL uses GPUDirect RDMA over InfiniBand or RoCEv2 together with InfiniBand GPUDirect Async. IBGDA, allowing the GPU itself to ring NIC doorbells and initiate RDMA writes without waiting for a host CPU thread.

```cpp
// NIXL 0.5.x nonblocking VRAM-to-VRAM transfer lifecycle (ASP Chapter 4)
#include <nixl.h>
#include <nixl_types.h>
#include <cuda_runtime.h>
#include <thread>
#include <vector>

int run_nixl_kv_transfer() {
    nixl_agent_config cfg{};
    cfg.backends = {"UCX"};         // Add "GDS" when offloading to NVMe storage
    cfg.thread_safe = true;

    nixlAgent agentSrc("srcAgent", cfg);
    nixlAgent agentDst("dstAgent", cfg);

    int deviceId = 0;
    cudaSetDevice(deviceId);
    const size_t bytes = 1 << 20;   // 1 MiB (1,048,576 bytes) illustrative slab
    void *d_src = nullptr, *d_dst = nullptr;
    cudaMalloc(&d_src, bytes);
    cudaMalloc(&d_dst, bytes);

    nixl_desc_t srcDesc{reinterpret_cast<uintptr_t>(d_src), bytes, deviceId, VRAM_SEG};
    nixl_desc_t dstDesc{reinterpret_cast<uintptr_t>(d_dst), bytes, deviceId, VRAM_SEG};

    auto srcRegs = agentSrc.registerMem(std::vector<nixl_desc_t>{srcDesc});
    auto dstRegs = agentDst.registerMem(std::vector<nixl_desc_t>{dstDesc});
    auto srcXfer = srcRegs.trim();  // Compact metadata-free descriptors shared via etcd
    auto dstXfer = dstRegs.trim();

    nixlReqH reqHandle = nullptr;
    agentSrc.prepXfer(NIXL_WRITE, srcXfer, dstXfer, "dstAgent", reqHandle);
    agentSrc.postXfer(NIXL_WRITE, srcXfer, dstXfer, "dstAgent", reqHandle);

    // Nonblocking poll while GPU compute stream continues decoding other sequences
    nixl_status_t st;
    do {
        st = agentSrc.checkXfer(reqHandle);
        if (st == NIXL_INPROGRESS) std::this_thread::yield();
    } while (st == NIXL_INPROGRESS);

    agentSrc.releaseReqH(reqHandle);
    agentSrc.deregisterMem(srcRegs);
    agentDst.deregisterMem(dstRegs);
    cudaFree(d_src);
    cudaFree(d_dst);
    return (st == NIXL_SUCCESS) ? 0 : 1;
}
```

### 3.3 PagedAttention Block Collation and Fabric Bandwidth Math

A subtle trap in disaggregated serving occurs when PagedAttention meets RDMA. By default, vLLM allocates KV cache in small sixteen-token pages so memory fragmentation stays near zero. However, if a prefill worker finishes a 7,500-token prompt and posts 470 separate RDMA write requests—one for each sixteen-token page—NIC work queue element. WQE, setup and doorbell overhead choke the link.

In benchmarks reported by LMCache and *AI Systems Performance Engineering* Chapter 18, sending a 7,500-token KV cache as 470 small sixteen-token transfers over RDMA takes 20 ms. Gathering and collating those pages into contiguous slabs of 128 tokens or more in GPU memory before posting the NIXL transfer cuts the RDMA handoff time by 2.5x down to 8 ms. When that 8 ms transfer runs on a dedicated CUDA stream overlapped with ongoing decode iterations, net visible transfer latency drops near zero.

```text
Disaggregated KV Cache Transfer Bandwidth and Collation Math (ASP Chapters 17 & 18; HLS Chapter 7):
1. PagedAttention Block Collation (7,500-token prompt):
   Default 16-token blocks:  ceil(7,500 / 16)  = 469 (~470) small RDMA transfers -> 20.0 ms transfer time
   Collated 128-token slabs: ceil(7,500 / 128) = 59 large RDMA transfers        ->  8.0 ms transfer time (2.5x faster)

2. Cluster KV Transfer Bandwidth Demand (HLS Chapter 7):
   Per-request KV cache (long-context prompt): 1.0 to 1.5 GB
   Throughput: 16 requests/sec * 1.5 GB/req = 24.0 GB/s (~25 GB/s aggregate KV transfer rate)
   - Intra-node NVLink 4 (H100/H200):          900.0 GB/s bidirectional (2.7% link load -> effortless)
   - Intra-rack NVLink 5 (B200/GB200 NVL72): 1,800.0 GB/s per GPU / 130 TB/s rack (effortless)
   - Inter-node 400G InfiniBand NDR / RoCEv2:   50.0 GB/s per NIC (48% of 1 NIC; effortless across 8 rails)
   - Inter-node 800G ConnectX-8 / XDR IB:      100.0 GB/s per NIC (24% of 1 NIC)
   - Non-RDMA PCIe / Host TCP Socket Fallback: ~10.0 GB/s (or 10–20 Gbps pod Ethernet -> 2.4x oversubscribed, severe stall)
```

 Always collate PagedAttention blocks into slabs of at least 128 tokens and verify GPUDirect RDMA before enabling cross-node prefill-decode disaggregation.

---

## 4. Distributed KV Cache Manager, Tiered Offloading, and Heterogeneous Pools

### 4.1 The Four-Tier KV Cache Memory Hierarchy

As context windows stretch to hundreds of thousands of tokens and multi-turn agentic sessions stay open for minutes, GPU High Bandwidth Memory becomes the primary capacity bottleneck. Consider a seventy-billion-parameter model with eighty layers, thirty-two KV heads, and head dimension 128 running a 250,000-token conversation in FP16. Each token produces 8,192 floats per layer, or 655,360 floats across all eighty layers, 1.31 MB per token. Across 250,000 tokens, that single session's KV cache consumes 328 GB of memory—exceeding the entire HBM of four eighty-gigabyte GPUs. Even after FP8 KV quantization and selective-layer caching, the state still occupies 100 to 150 GB.

Instead of discarding cached prefixes and paying quadratic prefill recomputation costs on every turn. NVIDIA Dynamo's **Distributed KV Cache Manager** uses NIXL and LMCache to virtualize KV storage across four hardware tiers.
1. **Tier 1 — GPU HBM, Hot Active Working Set,:** Holds weights and the KV blocks of sequences currently executing prefill or decode iterations at 3.35 to 8.0 TB/s.
2. **Tier 2 — CPU / Superchip DRAM, Warm Session Cache,:** Offloads recently used KV blocks to host system RAM. On Grace Hopper, GH200, and Grace Blackwell, GB200, superchips, the GPU accesses up to ratusan gigabytes of coherent LPDDR5X CPU memory over the 900 GB/s NVLink-C2C interconnect. On x86 servers, pinned host DRAM provides roughly 3x the GPU HBM capacity over 64 GB/s PCIe Gen5.
3. **Tier 3 — Local NVMe SSD via GPUDirect Storage, Cool Multi-Tenant Cache,:** Streams evicted KV slabs directly between GPU HBM and local NVMe drives using cuFile and NIXL's GDS backend, expanding effective KV cache capacity by up to 50x without touching the CPU.
4. **Tier 4 — Remote Shared Storage and Object Stores, Cold Global Pool,:** Persists shared enterprise document contexts and RAG prefixes. Lustre, DeepSeek 3FS, Redis, or S3 so any replica in the cluster can hydrate warm state without recomputing attention.

```text
Tiered KV Cache Offloading Speedups (ASP Chapter 4 Figures 4-9 & 4-10; HLS Chapter 7 Figures 7-25 & 7-27):
- x86 + H100 PCIe System (NIXL DRAM offload vs full prefill recomputation):
  Up to 14x faster TTFT on long input sequences
- ARM Grace Hopper Superchip GH200 (900 GB/s NVLink-C2C vs x86 + H100 PCIe):
  2x faster TTFT than x86 + H100 (28x effective speedup over recomputation)
- LMCache + vLLM Multi-Turn Benchmark (Qwen/Qwen3-14B, 150 GB local CPU cache, 30 prefixes / 5 concurrent streams):
  Capacity expansion: ~3x with CPU DRAM, ~50x with local NVMe SSD
  Warm CPU cache retrieval latency: ~1.0 s TTFT vs 6.0–7.0 s cold prefill recomputation
  Throughput under 5 concurrent long-context streams: 16x higher than vanilla vLLM (75,200 tok/s vs 4,700 tok/s baseline)
```

| KV Storage Tier | Backing Medium & Interconnect | Typical Bandwidth | Capacity Multiplier | Primary Operational Role |
|---|---|---|---|---|
| Tier 1: GPU HBM | HBM3 / HBM3e on GPU package | 3,350–8,000 GB/s | 1.0x (80–192 GB/GPU) | Active forward-pass weights and in-flight batch KV blocks. |
| Tier 2: Superchip / Host DRAM | Grace LPDDR5X (`NVLink-C2C`) or x86 DDR5 (`PCIe Gen5`) | 900 GB/s (`C2C`) / 55–64 GB/s (`PCIe`) | ~3x GPU HBM | Multi-turn conversation history and warm tenant system prompts (14x–28x faster TTFT). |
| Tier 3: Local NVMe SSD | PCIe Gen5 NVMe array via GPUDirect Storage (`GDS`) | 10–50+ GB/s per node | ~50x GPU HBM | Large Cache-Augmented Generation (`CAG`) corpora and multi-tenant context pools. |
| Tier 4: Remote Shared Store | Lustre / 3FS / Redis / S3 over RDMA or Ethernet | 10–100 GB/s fabric | Virtually unbounded | Cluster-wide cross-replica prefix sharing and fault-tolerant KV recovery. |

### 4.2 Heterogeneous Hardware Pairing and Asymmetric Parallelism (`TP_p` vs `TP_d`)

Because prefill and decode workers live in separate pools, they do not need identical GPUs or identical model-parallel sharding. **Matching compute-dense GPUs and wide parallelism to prefill while matching memory-rich GPUs and narrow parallelism to decode cuts cost per token without sacrificing latency**.

On the hardware side, prefill workers can run on compute-optimized accelerators such as Blackwell B200, Hopper H100, or NVIDIA's specialized Rubin CPX context processor. Decode workers can run on memory-capacity and bandwidth-optimized accelerators such as Blackwell Ultra B300. 70 GB of weights on a 180 GB GPU leaves roughly 122 GB for KV cache. Hopper H200, 141 GB HBM3e at 4.8 TB/s vs H100's 80 GB at 3.35 TB/s. Cost-efficient L40S and A100 GPUs. In the Splitwise study, pairing four H100 GPUs for prefill with four A100 GPUs for decode achieved 2.35x the RPS of an eight-GPU homogeneous cluster at the same cost and power budget, and another configuration delivered 1.4x higher throughput at 20 percent lower cost. Similarly, HexGen-2 demonstrated up to 2.0x higher throughput, 1.3x on average, or 30 percent lower cost by co-optimizing heterogeneous GPU assignment.

On the parallelism side, prefill processes thousands of prompt tokens at once. Splitting layers across multiple GPUs with Tensor Parallelism, `TP_p = 2` or 8, and Pipeline Parallelism, `PP_p = 2`, drastically reduces TTFT. Decode generates one token per step, where wide Tensor Parallelism adds per-layer AllReduce overhead and Pipeline Parallelism introduces stage bubbles. Thus, decode pools prefer `PP_d = 1` and the smallest Tensor Parallelism degree that fits the model, `TP_d = 1`, 2, or 4.

When TP_p and TP_d differ—for instance, when prefill runs `TP_p = 2, PP_p = 2`, holding 40 layers and 4 KV heads per GPU for an 80-layer, 8-KV-head model. Decode runs `TP_d = 4, PP_d = 1`, expecting 80 layers and 2 KV heads per GPU,—the KV cache layout in memory does not match across pools. NVIDIA Dynamo solves this automatically by executing a high-speed **KV layout transpose kernel**, [TP_p] -> [TP_d], on the receiver GPU immediately after the NIXL read completes. Before you deploy asymmetric parallelism across prefill and decode pools, verify that your NIXL receiver buffer is sized for the collated slab and that layout transposition is enabled.

---

## 5. `llm-d` and the Kubernetes Gateway API Inference Extension

### 5.1 Architecture of `llm-d` on Kubernetes

While NVIDIA Dynamo provides a deeply integrated runtime for NVIDIA AI Factories, platform teams running multi-vendor Kubernetes clusters, `>= 1.29`, need a standard Kubernetes-native control plane for disaggregated serving. The open-source **llm-d** project combines Envoy Proxy, the Kubernetes Gateway API Inference Extension, IGW / GIE, vLLM's KVConnector, LMCache, and NIXL RDMA sidecars into a declarative Kubernetes stack.

```mermaid
flowchart LR
    Client["Client OpenAI API Request"] --> Envoy["Envoy Proxy<br/>(TLS, Auth, Token Rate Limit)"]
    Envoy <==>|"gRPC ext_proc (:9002)<br/>FailClose"| EPP["Endpoint Picker (EPP)<br/>(llm-d inference-scheduler)"]

    subgraph Pool["InferencePool: vllm-llama3-8b-instruct (:8000)"]
        direction TB
        PrefillPods["vLLM Prefill Worker Pods<br/>+ NIXL / LMCache Sender"]
        DecodePods["vLLM Decode Worker Pods<br/>+ NIXL / LMCache Receiver"]
        PrefillPods ==>|"NIXL GPUDirect RDMA<br/>(500–800 Gbps RoCE/IB)"| DecodePods
    end

    WVA["Workload Variant Autoscaler (WVA)"] -.->|"Adjust P/D Replicas<br/>by TTFT/TPOT SLOs"| Pool
    EPP -.->|"Scrape Waiting Queue,<br/>KV %, Prefix & LoRA"| Pool
    Envoy -->|"Forward to Picked Pod (:8000)"| DecodePods
```

The llm-d project organizes production rollouts around three **well-lit paths**.
1. **Intelligent Inference Scheduling:** Deploys vLLM behind Envoy and the Inference Gateway so requests are routed by prompt length, KV cache usage, waiting queue depth. Prefix cache hits rather than naive round-robin.
2. **Prefill/Decode Disaggregation:** Splits vLLM pods into dedicated prefill and decode pools connected by a 500 to 800 Gbps InfiniBand or RoCEv2 RDMA fabric. Using NIXL sidecars to transfer KV caches in milliseconds.
3. **Wide Expert-Parallelism:** Coordinates Data Parallel attention and Expert Parallelism across multi-node Mixture-of-Experts models such as DeepSeek-V3/R1 and Mixtral.

### 5.2 `InferencePool`, `InferenceObjective` (`InferenceModel`), and Envoy `EPP`

Standard Kubernetes Service load balancing distributes connections round-robin and has no visibility into prompt token length, GPU KV cache pressure, cached prefixes, or loaded LoRA adapters. The **Gateway API Inference Extension** introduces two Custom Resource Definitions and an Envoy External Processing, ext_proc, service to make Kubernetes LLM-aware.
1. **InferencePool, `inference.networking.k8s.io/v1`,:** Represents a homogeneous pool of model-serving pods sharing the same base model, accelerator type. Compute configuration, exposing up to eight targetPorts, such as port 8000, and binds them to an Endpoint Picker service via endpointPickerRef.
2. **InferenceObjective, `inference.networking.x-k8s.io/v1alpha2`, evolved from InferenceModel,:** Declares workload priorities, such as priority. 1 for critical real-time traffic and priority: 2 for standard traffic, SLO objectives, and LoRA adapter names targeting an InferencePool.
3. **Endpoint Picker, EPP on port 9002,:** Implements the Envoy ext_proc gRPC protocol. On every incoming request, Envoy pauses routing and calls the EPP on port 9002, with failureMode: FailClose. The llm-d inference-scheduler EPP inspects the JSON request body, model, prompt tokens, priority headers. Alongside live Prometheus metrics, vllm:num_requests_waiting, vllm:gpu_cache_usage_perc, prefix hashes, and loaded LoRA modules, and returns the exact pod IP to Envoy.

```yaml
# Kubernetes Gateway API Inference Extension Manifests (GAK Chapter 4 Example 4-7)
apiVersion: inference.networking.k8s.io/v1
kind: InferencePool
metadata:
  name: vllm-llama3-8b-instruct
spec:
  targetPorts:
    - number: 8000
  selector:
    matchLabels:
      app: vllm-llama3-8b-instruct
  endpointPickerRef:
    name: vllm-llama3-8b-epp
    port:
      number: 9002
    failureMode: FailClose
---
apiVersion: inference.networking.x-k8s.io/v1alpha2
kind: InferenceObjective
metadata:
  name: high-priority-inference
spec:
  priority: 1
  poolRef:
    group: inference.networking.k8s.io
    name: vllm-llama3-8b-instruct
---
apiVersion: inference.networking.x-k8s.io/v1alpha2
kind: InferenceObjective
metadata:
  name: standard-inference
spec:
  priority: 2
  poolRef:
    group: inference.networking.k8s.io
    name: vllm-llama3-8b-instruct
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-llama3-8b-epp
spec:
  selector:
    app: vllm-llama3-8b-epp
  ports:
    - port: 9002
      targetPort: 9002
```

In addition, llm-d pairs the Endpoint Picker with two caching directions and a custom autoscaler.
- **North/South, `N/S`, Independent Caching:** Offloads a single vLLM instance's KV cache vertically to local host DRAM and local NVMe storage via KVConnector.
- **East/West, `E/W`, Shared Caching:** Transfers cached KV blocks horizontally across peer vLLM instances over RDMA so a prefix computed on Pod A can be reused on Pod B.
- **Workload Variant Autoscaler, WVA,:** Measures actual token-per-second capacity under current memory pressure and scales prefill, decode, and batch server pools proactively before latency SLOs are breached.

---

## 6. Commands and Configurations That Matter

### 6.1 LMCache + NIXL Disaggregated Prefill and Decode Configuration

To wire vLLM workers for zero-copy NIXL KV handoff through LMCache, configure the prefill instance as sender and the decode instance as receiver with matching one-gigabyte. 1,073,741,824 byte, GPU transfer buffers and explicit UCX RDMA transport variables.

```yaml
# 1. Prefill Worker Configuration: lmcache-prefiller-config.yaml (ASP Chapter 18)
enable_pd: true
transfer_channel: "nixl"
pd_role: "sender"                 # Prefill worker pushes KV blocks via NIXL
pd_proxy_host: "decode-host"      # Decode coordinator host
pd_proxy_port: 7500               # Control-plane port on decode proxy
pd_buffer_size: 1073741824        # 1 GiB (use 2 GiB if FP16 prompts exceed ~7.5k tokens)
pd_buffer_device: "cuda"          # Keep transfer buffer pinned in GPU HBM
```

```yaml
# 2. Decode Worker Configuration: lmcache-decoder-config.yaml (ASP Chapter 18)
enable_pd: true
transfer_channel: "nixl"
pd_role: "receiver"               # Decode worker receives KV blocks into HBM
pd_peer_host: "0.0.0.0"           # Bind address for NIXL peer
pd_peer_init_port: 7300           # NIXL handshake/control port
pd_peer_alloc_port: 7400          # NIXL allocation/data port
pd_buffer_size: 1073741824        # 1 GiB matching sender buffer
pd_buffer_device: "cuda"          # Zero-copy GPU HBM buffer
nixl_backends: [UCX]              # Use UCX (GPUDirect RDMA / CUDA IPC) backend
```

```bash
# 3. Launch Disaggregated Decode Worker with UCX Rendezvous & Deterministic Hash Seed
export PYTHONHASHSEED=0
export UCX_RNDV_THRESH=16384
export UCX_MAX_EAGER_RAILS=1
export UCX_TLS=cuda_ipc,rc,rdmacm,cuda_copy,tcp
CUDA_VISIBLE_DEVICES=1 \
LMCACHE_CONFIG_FILE=lmcache-decoder-config.yaml \
python3 run_vllm_decoder.py --port 8200

# 4. Launch vLLM with LMCache Tiered CPU/NVMe Offloading (HLS Chapter 7)
export LMCACHE_USE_EXPERIMENTAL=True
export LMCACHE_LOCAL_CPU=True
export LMCACHE_MAX_LOCAL_CPU_SIZE=150.0
nohup vllm serve Qwen/Qwen3-14B \
  --disable-log-requests \
  --kv-transfer-config '{"kv_connector":"LMCacheConnectorV1","kv_role":"kv_both"}' \
  --max-model-len 40960 \
  --gpu-memory-utilization 0.90 > vllm.log 2>&1 &
```

### 6.2 End-to-End Nsight Systems Profiling of Disaggregated NIXL Transfers

To verify that NIXL RDMA transfers overlap with decode CUDA kernels and do not fall back to host TCP sockets, capture a unified Nsight Systems trace. CUDA hardware, UCX, GPUDirect Storage, and InfiniBand NIC/switch counters.

```bash
# Correlated CUDA + UCX + GDS + InfiniBand NIC/Switch Nsight Systems Trace (ASP Chapter 17)
nsys profile --trace=cuda-hw,osrt,nvtx,ucx,gds \
  --trace-fork-before-exec=true \
  --cuda-event-trace=true \
  --cuda-graph-trace=node \
  --cuda-memory-usage=true \
  --sample=cpu \
  --gpu-metrics-device=all \
  --nic-metrics=true \
  --ib-switch-metrics-device=<GUIDs> \
  --storage-metrics --storage-devices=all \
  --gds-metrics=driver \
  -o nsys_reports/prefill_decode \
  python3 run_vllm_decoder.py --port 8200
```

Always inspect ucx_info -f, lsmod | grep nvidia_peermem, and your nsys timeline to confirm that KV handoffs travel over GPUDirect RDMA, rc,rdmacm, or cuda_ipc rather than host-staged TCP.

---

## 7. How It Fails: Five Disaggregated Serving Failure Modes

| Failure Mode | Symptom | Root Cause | Diagnostic Command / Evidence | Fix |
|---|---|---|---|---|
| **1. Uncollated 16-Token Page RDMA Storm** | Disaggregated TTFT is 15–30 ms slower than expected despite 400G InfiniBand links showing low byte utilization. | Sending a 7,500-token prompt as 470 individual 16-token PagedAttention blocks saturates NIC WQE doorbells (20 ms transfer). | `nsys profile --trace=cuda-hw,ucx --nic-metrics=true` shows hundreds of tiny UCX transfers totaling 20 ms. | Collate KV pages into contiguous slabs of `>= 128` tokens (59 transfers), cutting RDMA handoff time to 8 ms (2.5x speedup). |
| **2. Silent Fallback to Pod Ethernet / Host TCP** | Disaggregated throughput collapses at 16 RPS; host CPU cores hit 100% and TTFT spikes above 2,000 ms. | Missing `/dev/infiniband` passthrough or unloaded `nvidia_peermem` forces 24 GB/s of KV traffic onto 10–20 Gbps pod Ethernet (`~10 GB/s` PCIe/TCP). | `lsmod \| grep nvidia_peermem` empty; `ucx_info -f` or `NCCL_DEBUG=INFO` shows TCP socket fallback. | Load `nvidia_peermem`, mount `/dev/infiniband`, set `UCX_TLS=rc,rdmacm,cuda_copy,cuda_ipc`, and provision 500–800 Gbps RoCE/IB. |
| **3. Asymmetric `TP_p != TP_d` KV Layout Corruption** | Decode worker outputs garbled tokens or crashes with tensor shape mismatch immediately after NIXL KV read. | Prefill runs `TP_p = 2, PP_p = 2` (4 KV heads/rank) while decode runs `TP_d = 4, PP_d = 1` (2 KV heads/rank) without layout conversion. | Worker logs show KV head/layer dimension mismatch on decode step 1 after remote prefill handoff. | Enable Dynamo's on-the-fly `[TP_p] -> [TP_d]` KV transpose kernel after the NIXL read and match `pd_buffer_size`. |
| **4. Cross-Process Prefix Hash Mismatch** | Multi-process workers report `< 10%` prefix cache hit rate on identical RAG prompts and re-run full prefill. | Python's randomized default `PYTHONHASHSEED` produces different block hashes across worker processes. | Compare prefix cache hit counters (`vllm:gpu_prefix_cache_queries` vs hits) across worker processes. | Set `export PYTHONHASHSEED=0` across all prefill, decode, and router containers so KV chunk hashes are deterministic. |
| **5. Static P/D Pool Ratio Starvation Under Workload Shift** | Prefill queue explodes during summarization bursts (or decode KV hits 99% during reasoning bursts) while the other pool sits at 30% utilization. | Fixed `X_p : Y_d` worker allocation cannot adapt when input-to-output token ratios shift over the day. | Prometheus shows `prefill_queue_length > 10` with `decode_kv_usage < 30%` (or vice versa). | Enable Dynamo GPU Planner / `llm-d` Variant Autoscaler (`WVA`) for dynamic role flipping and `QoSController` early rejection at 500 ms. |

---

## 8. Hands-on Lab: Disaggregated Serving, Smart Router, and NIXL Verification

### Lab Venue and Scope
- **Venue:** Local Python Verification Lab, runs deterministically on any workstation. The multi-node GKE / InfiniBand / GB200 NVL72 hardware commands in Section 6 are reference configurations and have not been executed on live multi-node GPU hardware in this local build environment — marked untested on live hardware.
- **Code files:** `code/part15/dynamo_disaggregated_serving.py` and `code/part15/dynamo_disaggregated_serving_lab.py`.

### Run the Verification Suite

```bash
python3 -B code/part15/dynamo_disaggregated_serving_lab.py
```

### Expected Output (`25 passed, 0 failed`)

```text
=== Chapter 15.8 Lab: NVIDIA Dynamo, llm-d and Disaggregated Serving Verification ===
  [PASS] 1. Colocated 1-GPU goodput under P90 TTFT<=400 ms (3.0 RPS) and P90 TPOT<=40 ms (1.6 RPS) is bounded by min(3.0, 1.6) = 1.6 RPS/GPU
  [PASS] 2. Disaggregated 2P1D (2 prefill GPUs at 5.6 RPS = 11.2 RPS, 1 decode GPU at 10.0 RPS) achieves min(11.2, 10.0) / 3 = 3.33 (3.3) RPS/GPU (2.08x gain)
  [PASS] 3. DistServe reports up to 7.4x goodput and 12.6x tighter SLOs; NVIDIA Dynamo achieves up to 30x throughput on 680B MoE across 72-GPU GB200 NVL72
  [PASS] 4. MLPerf v5.0 p99 SLOs: Llama-2-70B targets 450 ms TTFT / 40 ms TPOT; Llama-3.1-405B targets 6000 ms (6 s) TTFT / 175 ms TPOT
  [PASS] 5. Single-stream 70B FP16 decode on H100 (140 GB / 3350 GB/s HBM3) requires 41.79 ms/token (~23.93 tok/s ceiling)
  [PASS] 6. Smart Router offloads prefill when effective prompt length (1024 - 256 = 768 >= 256) and prefill queue (4 < 10) has capacity (remote score = 1.0 > 0.5)
  [PASS] 7. Smart Router keeps prefill local on decode worker when prefix cache hit leaves eff_len = 124 (< 256) and decode active reqs = 4 (< 8)
  [PASS] 8. Smart Router sheds load back to local prefill when global prefill queue is saturated (12 >= 10)
  [PASS] 9. Smart Router offloads moderate prompt (eff_len = 100 >= 64) when local decode worker is busy (9 >= 8 active streams)
  [PASS] 10. Simple 2-term cost (0.7*occ + 0.3*reqs) picks worker-0-cold (1.3 vs 2.3), whereas 5-factor KV-aware composite cost (+3*occ + 1*reqs - 10*match + 0.5*bw - 1*recent) picks worker-1-warm (0.0 vs 6.0)
  [PASS] 11. Dynamo GPU Planner scales up prefill (4 -> 5 when queue=9 >= 8, util=85% >= 80%) and decode (8 -> 9 when queue=18 >= 16, kv=78% >= 75%)
  [PASS] 12. QoSController estimates TTFT = 9*35 + 18*20 = 675.0 ms (> 500 ms SLO), rejecting low-priority requests while admitting high-priority traffic
  [PASS] 13. Dynamo GPU Planner scales down prefill (6 -> 5 when queue<=2, util<=40%) and decode (10 -> 9 when queue<=4, kv<=30%) and admits low-priority at 75.0 ms TTFT
  [PASS] 14. QoS tier reservations allocate 10% premium (priority=100, 2 workers), 30% standard (priority=50, 6 workers), and 60% free (priority=10, 12 workers) across 20 workers
  [PASS] 15. NIXL 0.5.x VRAM_SEG test buffer is 1 MiB (1,048,576 B) and LMCache/NIXL pd_buffer_size is 1 GiB (1,073,741,824 B) on ports 7300/7400/7500 with UCX_RNDV_THRESH=16384
  [PASS] 16. Collating 7,500-token KV cache from 16-token blocks (469 WQEs, 20.0 ms) into 128-token slabs (59 WQEs, 8.0 ms) cuts RDMA transfer time by 2.5x
  [PASS] 17. At 16 RPS and 1.5 GB KV/req, aggregate transfer rate is 24.0 GB/s (~25 GB/s), fitting NVLink 4 (900 GB/s) and IB NDR RDMA (50 GB/s) but saturating non-RDMA PCIe/TCP (10 GB/s)
  [PASS] 18. 70B 80-layer 32-head MHA KV cache is 1,310,720 B/tok (~1.31 MB/tok, vs 327,680 B/tok GQA), totaling 327.7 GB (~328 GB) in FP16 and 163.8 GB in FP8 for 250,000 tokens
  [PASS] 19. NIXL KV cache offloading to CPU DRAM yields 14x TTFT speedup on x86+H100 and an additional 2x on Grace Hopper GH200 (900 GB/s NVLink-C2C = 28x vs recompute)
  [PASS] 20. LMCache tiered offloading expands KV capacity 3x in CPU RAM and 50x on NVMe SSD, lifting 5-concurrency throughput 16x from 4,700 tok/s to 75,200 tok/s
  [PASS] 21. Heterogeneous & adaptive benchmarks: Splitwise 4xH100+4xA100 achieves 2.35x RPS (and 1.4x at -20% cost), HexGen-2 achieves 2.0x peak / -30% cost, and Arrow achieves 5.6x adaptive scaling
  [PASS] 22. Asymmetric parallelism (prefill TP_p=2, PP_p=2 -> 40 layers, 4 KV heads/rank vs decode TP_d=4, PP_d=1 -> 80 layers, 2 KV heads/rank) requires on-the-fly KV layout transpose
  [PASS] 23. llm-d EPP (port 9002, FailClose) routes request with prefix 'sys-rag-doc' and LoRA 'lora-finance' to vllm-llama3-8b-pod-1 (port 8000, score 42.0 vs -24.0)
  [PASS] 24. On a prefix miss with no LoRA match, llm-d EPP routes to least-loaded vllm-llama3-8b-pod-2 (waiting=1, kv=40%, score -24.0)
  [PASS] 25. Under >95% KV saturation (96.5%, 97.0%), InferenceObjective priority=2 (standard) is shed with HTTP 429 while priority=1 (high-priority) is admitted to pod-sat-0

Summary: 25 passed, 0 failed
```

---

## Key takeaways

1. **Colocated serving suffers from prefill-decode interference:** Compute-bound prompt prefills stall memory-bandwidth-bound decode iterations, dragging colocated goodput down to the bottlenecked phase. 1.6 RPS/GPU vs 3.3 RPS/GPU in a 2P1D disaggregated pool.
2. **Conditional disaggregation beats blind offloading:** NVIDIA Dynamo's Smart Router offloads prefill only. The uncached prompt, prompt_length - prefix_cached_length, exceeds the threshold, 256 tokens, or 64 tokens when decode has `>= 8` active requests, and the global prefill queue has headroom, < 10.
3. **KV-aware composite routing maximizes prefix reuse:** Weighting exact KV cache matches, `-10.0`. Recent prefix warmth, `-1.0`, alongside KV occupancy, +3.0, active requests, +1.0, and memory bandwidth, +0.5, steers requests to cache-warm workers while preventing hotspots.
4. **NIXL + page collation makes KV handoff near-free:** NIXL moves KV caches asynchronously across NVLink, GPUDirect RDMA, IBGDA, CPU DRAM, and GPUDirect Storage. Collating 16-token PagedAttention blocks into `>= 128`-token slabs cuts a 7,500-token RDMA transfer from 20 ms, 470 WQEs, to 8 ms, 59 WQEs.
5. **Four-tier KV offloading and llm-d scale long-context Kubernetes fleets:** Offloading cold KV blocks to CPU DRAM, 3x space, 14x x86 TTFT speedup, 28x on GH200 NVLink-C2C. NVMe SSDs, 50x space, 16x LMCache throughput gain, pairs cleanly with llm-d's InferencePool, InferenceObjective, Envoy ext_proc Endpoint Picker, :9002, and Variant Autoscaler.

---

## Exercises

1. **DistServe 2P1D Goodput and MLPerf v5.0 SLO Sizing:**.
   -, a, A colocated single-GPU server sustains 3.0 RPS under a `P90 TTFT <= 400 ms`, 0.4 s, SLO and 1.6 RPS under a `P90 TPOT <= 40 ms`, 0.04 s, SLO. When disaggregated into 2 prefill GPUs, 5.6 RPS per GPU. 1 decode GPU, 10.0 RPS, calculate the colocated goodput per GPU, the aggregate 3-GPU disaggregated goodput, the disaggregated goodput per GPU, and the per-GPU speedup ratio.
   -, b, State the MLPerf Inference v5.0 p99 TTFT and TPOT SLO targets for Llama-2-70B and Llama-3.1-405B. Verify the single-stream H100 decode latency and token-per-second ceiling for 140 GB of FP16 weights at `3,350 GB/s`.

2. **NVIDIA Dynamo Smart Router Decisions and Composite Latency Cost:**.
   -, a, Using `PREFILL_LENGTH_THRESHOLD = 256`, `PREFILL_QUEUE_MAX = 10`, and `DECODE_LOAD_THRESHOLD = 8`, evaluate should_offload_prefill() and the YAML remote_prefill_score, 0.7 length weight, 0.3 queue weight, 0.5 threshold, for. Request A, `prompt=1024, cached=256, queue=4, active=3`, Request B, `prompt=1024, cached=900, queue=3, active=4`, and Request C, `prompt=2048, cached=0, queue=12, active=2`.
   -, b, Calculate both the simple 2-term cost, 0.7 * occ + 0.3 * reqs. The 5-factor composite latency_cost, 3.0 * occ + 1.0 * reqs - 10.0 * match + 0.5 * bw - 1.0 * recent, for worker-0-cold, `occ=1.0, reqs=2, match=0, bw=2.0, recent=0`. Worker-1-warm, `occ=2.0, reqs=3, match=1, bw=4.0, recent=1`, and explain why their routing choices differ.

3. **Dynamo GPU Planner Autoscaling, QoS Reservations, and Early Rejection:**.
   -, a, Given the Planner thresholds, prefill. `min=4, max=12`, scale up at `queue>=8` or `util>=80%`, scale down at `queue<=2` and `util<=40%`. Decode: `min=8, max=24`, scale up at `queue>=16` or `kv>=75%`, scale down at `queue<=4` and `kv<=30%`, determine the scaling actions when `(prefill_replicas=4, queue=9, util=85%, decode_replicas=8, queue=18, kv=78%)`.
   -, b, If `avg_prefill_time = 35 ms` and `avg_decode_time = 20 ms` with `ttft_slo_ms = 500 ms`, compute est_ttft. That surge, determine whether QoSController admits "low" vs "high" priority requests, and calculate the worker counts reserved for premium, 10%, standard, 30%, and free, 60%, across 20 workers.

4. **NIXL Page Collation, 4-Tier KV Offloading, Asymmetric Transpose, and llm-d EPP:**.
   -, a, For a 7,500-token prompt, calculate the number of RDMA transfers required with 16-token blocks, 20.0 ms, versus 128-token collated slabs, 8.0 ms, and the speedup factor. Also compute the 250,000-token KV cache size in FP16 and FP8 for an 80-layer, 32-head, 128-dim model, `1,310,720 B/tok`. Verify whether `16 RPS * 1.5 GB = 24.0 GB/s` fits on NVLink 4, `900 GB/s`, NDR InfiniBand, `50 GB/s`, or non-RDMA PCIe/TCP, `10 GB/s`.
   -, b, When prefill uses `TP_p = 2, PP_p = 2` and decode uses `TP_d = 4, PP_d = 1` on an 80-layer, 8-KV-head model, compute the layers and KV heads per rank on each side. Then verify which pod llm-d's EPP, port 9002, FailClose, selects among pod-0, `waiting=6, kv=70%`, pod-1, `waiting=2, kv=50%, prefix='sys-rag-doc', lora='lora-finance'`, and pod-2, `waiting=1, kv=40%`, for a request matching 'sys-rag-doc' and 'lora-finance'.

---

## Checkpoint questions

<details>
<summary>**1. Why does colocating prefill and decode on the same GPU cause head-of-line blocking and degrade TPOT?**</summary>

Prefill is compute bound and processes all prompt tokens in parallel through large matrix multiplications, whereas decode is memory-bandwidth bound and generates one token per step. When a long prompt arrives on a colocated GPU, its heavy prefill GEMMs monopolize the Tensor Cores and stall ongoing decode iterations for hundreds of milliseconds, spiking inter-token latency for every active user.
</details>

<details>
<summary>**2. How is Goodput defined in LLM serving, and why did the colocated GPU in the DistServe benchmark achieve only 1.6 RPS of goodput despite reaching 3.0 RPS on TTFT?**</summary>

Goodput counts only the completed requests per second that simultaneously satisfy both the TTFT and TPOT Service Level Objectives. In the DistServe benchmark, `P90 TTFT <= 400 ms`, `P90 TPOT <= 40 ms`, the colocated GPU sustained 3.0 RPS under the TTFT target alone, but prefill-decode interference caused TPOT violations above 1.6 RPS. Thus, `min(3.0, 1.6) = 1.6 RPS/GPU`.
</details>

<details>
<summary>**3. How do you calculate the per-GPU goodput of the disaggregated 2P1D pool (`2` prefill GPUs at `5.6 RPS` each and `1` decode GPU at `10.0 RPS`), and what speedup does it achieve over the colocated baseline?**</summary>

Two prefill GPUs at 5.6 RPS each provide `2 * 5.6 = 11.2 RPS` of total prefill capacity, while the single decode GPU provides 10.0 RPS. The cluster goodput across all three GPUs is `min(11.2, 10.0) = 10.0 RPS`. Dividing by 3 GPUs gives `10.0 / 3 = 3.33 RPS/GPU`, reported as 3.3 RPS/GPU, which is a 2.08x improvement over the colocated 1.6 RPS/GPU baseline.
</details>

<details>
<summary>**4. What are the MLPerf Inference v5.0 (2025) p99 TTFT and TPOT latency targets for Llama-2-70B and Llama-3.1-405B?**</summary>

MLPerf Inference v5.0 specifies a 99th-percentile SLO of 450 ms TTFT and 40 ms TPOT for Llama-2-70B, and 6,000 ms, 6 seconds, TTFT and 175 ms TPOT for Llama-3.1-405B.
</details>

<details>
<summary>**5. What are the four core architectural components of NVIDIA Dynamo, and what role does each play?**</summary>

1. **Smart Router:** Routes requests based on prefix cache locality, queue depth, KV occupancy, and memory bandwidth, and decides whether to offload prefill remotely.
2. **GPU Planner:** Monitors real-time TTFT/TPOT SLOs and queue depths to autoscale or flip workers between prefill and decode roles.
3. **NIXL, NVIDIA Inference Transfer Library,:** Executes nonblocking point-to-point KV cache transfers across NVLink, RDMA, CPU DRAM, and NVMe storage.
4. **Distributed KV Cache Manager:** Manages the four-tier KV cache hierarchy across GPU HBM, CPU DRAM, local NVMe SSDs, and remote storage.
</details>

<details>
<summary>**6. How do `etcd` and NATS divide control-plane responsibilities inside an NVIDIA Dynamo cluster?**</summary>

Dynamo uses etcd for service discovery, worker health leases, and exchanging NIXL memory registration descriptors at startup. It uses NATS as the low-latency distributed message bus for publishing KV cache allocation/eviction events to the Smart Router and dispatching RemotePrefillRequest tasks through the global prefill queue.
</details>

<details>
<summary>**7. Why does NVIDIA Dynamo use a decode-centric request ingress design where requests arrive at a decode worker first?**</summary>

Prefill workers are already compute saturated executing dense prompt matrix multiplications. Having decode workers handle client I/O, session state, KV block allocation. The should_offload_prefill() check keeps prefill workers focused purely on compute and allows the decode worker to immediately run prefill locally whenever the prompt is short or the prefill pool is full.
</details>

<details>
<summary>**8. How does `should_offload_prefill()` use `prompt_length`, `prefix_cached_length`, `prefill_queue_size`, and `decode_active_reqs` to make a conditional disaggregation decision?**</summary>

It first computes `eff_len = max(0, prompt_length - prefix_cached_length)`. It offloads prefill to the remote prefill pool. `eff_len >= 256` and prefill_queue_size < 10, or if the local decode GPU is busy, `decode_active_reqs >= 8`, `eff_len >= 64`, and the prefill queue has room, < 10. Otherwise, it runs prefill locally on the decode GPU.
</details>

<details>
<summary>**9. In Dynamo's five-factor `latency_cost` equation, what are the weights for KV occupancy, active requests, exact cache match, memory bandwidth, and recent prefix use?**</summary>

The composite cost is 3.0 * occupancy_percent + 1.0 * active_reqs - 10.0 * int, cache_match_flag, + 0.5 * mem_bw_percent - 1.0 * int, recent_prefix_flag. Positive weights penalize high HBM occupancy, active request queues, and memory bus saturation, while negative weights, `-10.0` and `-1.0`, strongly favor workers with cached or warm prefixes.
</details>

<details>
<summary>**10. How does Dynamo GPU Planner adapt when a cluster shifts from document summarization to chain-of-thought reasoning, and how does `QoSController` protect SLOs under overload?**</summary>

During summarization surges, long prompts, short outputs, the GPU Planner scales up or reallocates GPUs to the prefill pool, `queue_length >= 8` or `gpu_utilization >= 80%`. During reasoning surges, short prompts, long outputs, it shifts GPUs to the decode pool, `queue_length >= 16` or `kv_cache_usage >= 75%`. When `est_ttft = Q_p * t_p + Q_d * t_d` exceeds 500 ms, QoSController rejects low-priority requests early while preserving reserved capacity, 10% premium, 30% standard.
</details>

<details>
<summary>**11. How does NIXL differ from NCCL in communication pattern, synchronization semantics, and supported memory tiers?**</summary>

NCCL is designed for synchronous many-to-many group collectives, AllReduce, AllGather, across GPU HBM where all ranks hit a barrier together. NIXL is designed for asynchronous, nonblocking one-to-one or one-to-few point-to-point transfers. Heterogeneous tiers, GPU VRAM, CPU DRAM, local NVMe SSD via GDS, and remote object/file storage, without stalling compute streams.
</details>

<details>
<summary>**12. What is the seven-step C++ API call sequence for executing a nonblocking GPU-to-GPU write with `nixlAgent` in NIXL 0.5.x?**</summary>

1. Configure nixl_agent_config, `backends = {"UCX"}`, `thread_safe = true`, and construct nixlAgent, "srcAgent", cfg, and nixlAgent, "dstAgent", cfg.
2. Build nixl_desc_t descriptors with VRAM_SEG.
3. Register buffers via registerMem().
4. Call trim() to obtain compact transfer descriptors.
5. Prepare the transfer with prepXfer, NIXL_WRITE....
6. Submit nonblockingly with postXfer, NIXL_WRITE... and poll completion via checkXfer, reqHandle.
7. Clean up with releaseReqH() and deregisterMem().
</details>

<details>
<summary>**13. Why does sending a 7,500-token KV cache as 16-token PagedAttention blocks take 20 ms over RDMA, and how does page collation reduce this to 8 ms?**</summary>

With 16-token blocks, a 7,500-token prompt requires `ceil(7500 / 16) = 469`, ~470, separate RDMA writes, so per-transfer WQE creation and NIC doorbell overhead dominate link time, 20 ms. Collating pages into `>= 128`-token contiguous buffers reduces the transfer to 59 large RDMA writes, saturating link bandwidth and cutting transfer time to 8 ms, 2.5x faster.
</details>

<details>
<summary>**14. At 16 RPS with 1.5 GB of KV cache per request, what is the aggregate KV transfer bandwidth demand, and which interconnects can sustain it?**</summary>

The aggregate transfer rate is `16 * 1.5 GB/s = 24.0 GB/s`, `~25 GB/s`. Intra-node NVLink 4, `900 GB/s`, NVLink 5, `1,800 GB/s`, 400G InfiniBand NDR / RoCEv2, `50 GB/s` per NIC. 800G ConnectX-8, `100 GB/s` per NIC, easily sustain 24 GB/s, whereas non-RDMA PCIe/TCP fallback, `~10 GB/s`, and standard 10–20 Gbps pod Ethernet saturate and stall the cluster.
</details>

<details>
<summary>**15. What are the four tiers of Dynamo's Distributed KV Cache Manager, and what TTFT speedups were measured on x86+H100 and Grace Hopper GH200 systems?**</summary>

The four tiers are:, 1, GPU HBM, 2, CPU / Superchip DRAM, LPDDR5X over 900 GB/s NVLink-C2C or x86 DDR5 over PCIe. 3, local NVMe SSDs via GPUDirect Storage, GDS, and, 4, remote shared/object storage, Lustre, 3FS, Redis, S3. Offloading KV cache to DRAM on x86+H100 achieved up to a 14x TTFT speedup over recomputing prefill. Grace Hopper GH200, `900 GB/s` NVLink-C2C, achieved an additional 2x TTFT speedup over x86+H100, 28x vs recompute.
</details>

<details>
<summary>**16. How much KV cache capacity and throughput gain did LMCache achieve when offloading to CPU memory and NVMe SSDs under 5 concurrent long-context streams?**</summary>

Offloading to CPU DRAM expanded KV cache capacity by ~3x, and offloading to local NVMe SSDs expanded capacity by ~50x. Retrieving warm KV blocks from CPU memory took ~1.0 s versus 6.0–7.0 s for cold prefill recomputation. Under 5 concurrent long-context requests, LMCache delivered 16x higher throughput than vanilla vLLM, `75,200 tok/s` vs `4,700 tok/s`.
</details>

<details>
<summary>**17. Why is heterogeneous hardware pairing (such as B200 + B300, H100 + H200/L40S, or Splitwise 4xH100 + 4xA100) effective in disaggregated serving?**</summary>

Prefill is compute bound and benefits from high-FLOPS GPUs, B200, H100, Rubin CPX. Decode is memory-bandwidth and capacity bound and benefits from large, fast HBM, B300 with 180 GB HBM leaving ~122 GB KV pool. H200 with 141 GB at `4.8 TB/s`, or lower-cost A100/L40S. In Splitwise, pairing 4x H100, prefill, with 4x A100, decode, delivered 2.35x higher RPS at the same cost and power budget.
</details>

<details>
<summary>**18. What happens when the prefill pool and decode pool use different Tensor or Pipeline Parallelism degrees (`TP_p != TP_d`), and how does Dynamo resolve it?**</summary>

When TP_p and TP_d differ, for example, `TP_p = 2, PP_p = 2` vs `TP_d = 4, PP_d = 1`, each prefill GPU holds a different slice of layers and KV heads than each decode GPU expects. Dynamo resolves this by running a fast on-the-fly KV layout transpose kernel, [TP_p] -> [TP_d], on the decode GPU immediately after the NIXL read completes.
</details>

<details>
<summary>**19. In Kubernetes `llm-d` and the Gateway API Inference Extension, how do `InferencePool`, `InferenceObjective` (`InferenceModel`), and the Endpoint Picker (`EPP`) interact with Envoy Proxy?**</summary>

InferencePool, `inference.networking.k8s.io/v1`, selects the model-serving pods, port 8000, and references the Endpoint Picker service, port: 9002, failureMode: FailClose. InferenceObjective, `inference.networking.x-k8s.io/v1alpha2`, which replaced InferenceModel, defines request priorities, priority: 1 vs 2. When a request hits Envoy, Envoy invokes the EPP over gRPC ext_proc, :9002. The EPP picks the optimal pod based on waiting queue depth, KV cache usage, prefix hits, and loaded LoRA adapters.
</details>

<details>
<summary>**20. What are the three "well-lit paths" in `llm-d`, and how do North/South (`N/S`) and East/West (`E/W`) KV caching differ?**</summary>

The three well-lit paths are:, 1, Intelligent Inference Scheduling, prefix- and load-aware routing via IGW/EPP. 2, Prefill/Decode Disaggregation, separate P/D pools with NIXL RDMA KV transfer, and, 3, Wide Expert-Parallelism, distributed MoE serving. North/South, `N/S`, caching offloads KV blocks vertically from GPU HBM to local CPU RAM and NVMe on the same node. East/West, `E/W`, caching shares KV blocks horizontally between peer vLLM instances over RDMA.
</details>

---

## Sources and review notes

### Primary Sources (Read in Full and Cited)

| Source | What was read and used |
|---|---|
| *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chapters 4, 15, 17, 18; Ch. 17 *Scaling Disaggregated Prefill and Decode for Inference*) | Prefill-decode interference and head-of-line blocking; MLPerf Inference v5.0 (2025) p99 SLOs (`Llama-2-70B`: `450 ms` TTFT, `40 ms` TPOT; `Llama-3.1-405B`: `6,000 ms` [`6 s`] TTFT, `175 ms` TPOT); DistServe colocated (`1.6 RPS/GPU`, `3.0 RPS` TTFT / `1.6 RPS` TPOT) vs `2P1D` disaggregated (`5.6 * 2 = 11.2 RPS` prefill, `10.0 RPS` decode across `3` GPUs = `3.33` / `3.3 RPS/GPU`, `2.08x` gain; up to `7.4x` goodput and `12.6x` tighter SLOs); NVIDIA Dynamo `30x` throughput on `680B` MoE across `72`-GPU `GB200 NVL72` (`130 TB/s`); Dynamo decode-centric architecture with `etcd` leases, NATS queues, and `B200` prefill (`4` workers) + `B300` decode (`8` workers, `180 GB` HBM, `70 GB` weights, `122 GB` KV) roles; Smart Router `should_offload_prefill()` (`PREFILL_LENGTH_THRESHOLD = 256`, `PREFILL_QUEUE_MAX = 10`, `DECODE_LOAD_THRESHOLD = 8`, `eff_len >= 64`), YAML `disaggregated_router` (`0.7` / `0.3` / `0.5`), 2-term cost (`0.7 * occ + 0.3 * reqs`), and Table 17-3 5-factor `latency_cost` (`+3.0`, `+1.0`, `-10.0`, `+0.5`, `-1.0`); Dynamo GPU Planner autoscale policy (`prefill`: `4..12`, `8/80%`, `2/40%`; `decode`: `8..24`, `16/75%`, `4/30%`), `configs/qos.yaml` (`premium 10%/100`, `standard 30%/50`, `free 60%/10`), and `QoSController` (`500 ms`); NIXL `0.5.x` C++ API (`nixlAgent`, `VRAM_SEG`, `1 MiB` = `1,048,576 B`, `registerMem`, `trim`, `prepXfer`, `postXfer`, `checkXfer`), Table 4-5 NCCL vs NIXL, `14x` x86+H100 and `2x` GH200 (`900 GB/s` NVLink-C2C) TTFT speedups; `250,000`-token `70B` MHA KV math (`8,192` floats/layer, `655,360` floats/tok = `1.31 MB/tok`, `328 GB` FP16 -> `100–150 GB` FP8); `7,500`-token page collation (`470` `16`-token blocks at `20 ms` -> `128`-token slabs at `8 ms`, `2.5x`); LMCache + NIXL YAML (`1,073,741,824 B` = `1 GiB`, ports `7300`/`7400`/`7500`, `UCX_RNDV_THRESH=16384`, `PYTHONHASHSEED=0`); `TP_p -> TP_d` transpose; and Splitwise (`2.35x` RPS, `1.4x` at `-20%` cost), HexGen-2 (`2.0x` peak / `1.3x` avg / `-30%` cost), and Arrow (`5.6x`). |
| *Generative AI on Kubernetes* (`generative-ai-on-kubernetes`, Chapter 4: *Running in Production*) | Gateway API Inference Extension (`GIE` / `IGW`), `InferencePool` (`inference.networking.k8s.io/v1`, `targetPorts: 8000`, `endpointPickerRef` port `9002`, `failureMode: FailClose`), `InferenceObjective` and its predecessor `InferenceModel` (`inference.networking.x-k8s.io/v1alpha2`, `priority: 1` and `2`), Envoy External Processing (`ext_proc`) Endpoint Picker (`EPP`), `llm-d` `inference-scheduler` and Workload Variant Autoscaler (`WVA`), KServe `LLMInferenceService`, and disaggregated network requirements (`500–600 Gbps` up to `800 Gbps` RoCE/InfiniBand vs `10–20 Gbps` standard pod Ethernet). |
| *Distributed AI Systems* (`distributed-ai-systems`, Chapter 9: *Production LLM Serving Stack*) | `llm-d` production Kubernetes (`>= 1.29`) architecture combining Envoy Proxy, Inference Gateway (`IGW`), `vLLM`, and `NIXL` RDMA sidecars; North/South (`N/S` local CPU/NVMe) vs East/West (`E/W` peer instance) disaggregated prefix caching via `KVConnector`; the three well-lit paths (Intelligent Inference Scheduling, Prefill/Decode Disaggregation, Wide Expert-Parallelism); and multi-vendor accelerator support. |
| *Hands-On LLM Serving and Optimization* (`hands-on-llm-serving-and-optimization`, Chapter 7: *Advanced LLM Optimization Techniques*) | Prefill-decode disaggregation trade-offs and hardware pairing (`H100` prefill + `H200` `141 GB` `4.8 TB/s` or `L40S` decode); KV cache transfer bandwidth math (`16 RPS * 1.5 GB = 24.0 GB/s` [`~25 GB/s`] over `900 GB/s` NVLink vs `50–100 GB/s` InfiniBand RDMA vs `10 GB/s` non-RDMA PCIe/TCP); layer-by-layer overlapped KV streaming (`< 1%` latency overhead); and `LMCache` tiered KV offloading (`3x` CPU DRAM, `50x` SSD, `150 GB` local CPU cache on `Qwen3-14B` cutting TTFT from `6–7 s` to `1 s` and boosting 5-concurrency throughput `16x` from `4,700 tok/s` to `75,200 tok/s`). |
| NVIDIA Zero-to-Hero Volume 12 (`chapter-01-why-inference-infrastructure-is-different.md`, `chapter-08-kv-cache-memory-and-concurrency.md`, `chapter-09-scaling-multi-gpu-and-multi-node-inference.md`) | Single-stream `70B` FP16 decode memory-bandwidth ceiling on H100 (`140 GB / 3,350 GB/s = 41.79 ms` / `~41.7 ms`, `23.93 tok/s` / `~24 tok/s`); `Llama-3-70B` GQA (`8` KV heads) KV footprint (`327,680 B = 320 KiB/tok`); and intra-node NVLink (`900 GB/s`) vs inter-node InfiniBand NDR (`400 Gbps = 50 GB/s`, `NCCL_NET_GDR_LEVEL=5`) topology rules. |

### Inferences and Unverified Claims Note

| Note Type | Details |
|---|---|
| Hardware runtime notes | Multi-node NVIDIA Dynamo, NIXL C++ / UCX RDMA, `nsys profile` InfiniBand switch counter traces, and Kubernetes `llm-d` `InferencePool` manifests are reference production patterns from the cited sources and have not been executed on live multi-node GPU hardware in this local build environment (`untested` on live hardware). |
| Deterministic lab verification | All DistServe 2P1D goodput calculations (`1.6 RPS/GPU` vs `3.33` / `3.3 RPS/GPU`), Smart Router conditional offload rules and 5-factor composite latency costs (`6.0` vs `0.0`), GPU Planner autoscale transitions and `QoSController` admission checks (`675.0 ms > 500.0 ms`), NIXL page collation ratios (`469` vs `59` WQEs, `20.0 ms -> 8.0 ms`), 4-tier KV cache capacities (`327.7 GB` FP16 / `163.8 GB` FP8, `14x` / `28x` TTFT, `16x` throughput), `TP_p -> TP_d` layout transpose plans, and `llm-d` EPP scoring rules are verified deterministically by `code/part15/dynamo_disaggregated_serving.py` and `code/part15/dynamo_disaggregated_serving_lab.py` (`25 passed, 0 failed`). |

- Manifest checked against upstream CRDs on 2026-11-11 (versions: InferencePool inference.networking.k8s.io/v1 as shipped in the KServe main CRDs, 2026-11-11 clone).
