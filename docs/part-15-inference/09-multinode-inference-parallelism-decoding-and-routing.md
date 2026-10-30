---
id: "c15-09"
title: "15.9 Multinode inference: parallelism, decoding and routing"
sidebar_label: "15.9 Multinode inference: parallelism, decoding and routing"
sidebar_position: 9
description: "Multi-node LLM inference architecture: 5D parallelism (Tensor, Pipeline, Expert, Data, and Context/Helix Parallelism), why cross-node TP breaks Inter-Token Latency via 2*(N-1) AllReduces, wide Expert Parallelism on DeepSeek-R1 671B and GB200 NVL72, dynamic MoE routing and EPLB, speculative decoding (draft-verify math, Medusa, EAGLE, Multi-Token Prediction MTP, Lookahead), Kubernetes LeaderWorkerSet (LWS) serving, and prefix-aware routing."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 15.9 Multinode inference: parallelism, decoding and routing

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE + Local Python Verification Lab |
| Part | Part 15: LLM inference and serving |
| Primary sources | *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chapters 1, 2, 15, 19); *Hands-On LLM Serving and Optimization* (`hands-on-llm-serving-and-optimization`, Chapters 5, 6, 7); *Generative AI on Kubernetes* (`generative-ai-on-kubernetes`, Chapters 3, 7); *Distributed AI Systems* (`distributed-ai-systems`, Chapters 6, 7, 11); NVIDIA Zero-to-Hero Volume 12 (`chapter-09-scaling-multi-gpu-and-multi-node-inference.md`, `chapter-05-tensorrt-llm-and-llm-execution.md`, `chapter-08-kv-cache-memory-and-concurrency.md`, `chapter-12-volume-12-summary.md`) |
| Cross-references | Chapter 11.7 on Kubernetes gang scheduling; Chapter 12.15 on NCCL collectives; Chapter 14.10 on multi-node training; Chapters 15.3 and 15.4 on vLLM and SGLang; Chapters 15.8 and 15.10 on disaggregated serving |
| Code | `code/part15/multinode_inference_parallelism.py`, `code/part15/multinode_inference_parallelism_lab.py` |
| Coverage file | `planning/coverage/chapters/15-09.md` |
| Claim & number ledger | `planning/ledgers/15-09.md` |

## Why this matters for AI infrastructure

A single high-end GPU cannot hold a frontier foundation model. Even an eight-GPU server runs out of memory when serving massive dense models like Llama-3-405B. The same memory wall hits sparse Mixture-of-Experts models like DeepSeek-R1 with 671 billion parameters. You must split these models across multiple GPUs and multiple physical nodes.

Scaling inference across nodes is much harder than scaling distributed training. Training jobs optimize for aggregate token throughput over hours or days. They can easily hide network latency behind large micro-batches. Online inference must deliver each output token in under 25 milliseconds while handling unpredictable user prompts. Partitioning a model places network communication directly on the synchronous critical path of every generated token.

```text
Multi-Node Inference Scaling Reference Numbers (ASP Ch. 1, 15; Volume 12 Ch. 9; DAI Ch. 6, 11):
- Llama-3-70B (80 layers, 140 GB FP16 weights + 20+ GB KV cache):
  Exceeds 1x 80 GB H100; requires 2 to 8 GPUs via intra-node Tensor Parallelism (TP = 2, 4, or 8)
- DeepSeek-V3 / DeepSeek-R1 (671B total parameters, ~680B nominal, 37B active per token):
  Uses 1 shared expert + 8 routed experts out of 256 per token (9 active experts = 5.51% active parameters)
  Exceeds an 8x 80 GB H100 node (640 GB) in BF16/FP8 once KV cache and workspace are added
- The 160-AllReduce Per-Token Trap (80-layer Transformer under Tensor Parallelism):
  2 synchronous AllReduce calls per layer * 80 layers = 160 AllReduces per generated token
  At 50 tokens/s = 8,000 AllReduce collectives per second
  Ring AllReduce step count per collective = 2 * (N - 1) steps (14 steps at TP = 8; 30 steps at TP = 16)
  Over intra-node NVLink 4 (900 GB/s, < 1.0 us): ~0.13 ms comm/token (ITL ~14.13 ms)
  Over PCIe Gen5 (64 GB/s) or 100GbE TCP (12.5 GB/s, 50-150 us): adds 50 ms to 200 ms per token (> 90% stall)
- Disaggregated Prefill/Decode and Speculative Decoding Gains:
  DistServe PD disaggregation: up to 7.4x higher goodput and 12.6x tighter latency SLOs
  Speculative decoding (EAGLE-3 / Medusa / MTP): 1.96x to 3.6x decode speedup without accuracy loss
```

Three architectural mistakes routinely break multi-node inference clusters in production.
- **Spanning Tensor Parallelism across slow inter-node links:** Stretching Tensor Parallelism across two eight-GPU servers forces 160 AllReduce operations per token over PCIe or Ethernet. That single mistake adds up to 200 milliseconds per token. It can also trigger a 30-second NCCL watchdog timeout during startup.
- **Unbalanced Mixture-of-Experts and Pipeline stages:** In Mixture-of-Experts serving, a popular expert can drive one GPU to 99 percent utilization while peer GPUs sit at 60 percent. In Pipeline Parallel serving, long prompts can fill nearly all of the KV cache on the first stage while downstream stages sit mostly empty.
- **Cache-blind request routing:** Using round-robin load balancing across Data Parallel replicas destroys prefix cache locality and leaves half the cluster idle. Conversely, naive prefix hashing without load bounds sends over three times more traffic to a single hot node.

**Align your parallelism dimensions with hardware link boundaries first, then accelerate sequential decode with speculative execution and cache-aware routing.**

## Prerequisites and outcomes

### Prerequisites
- Kubernetes gang scheduling, Kueue, Volcano, and topology-aware pod placement from Chapter 11.7.
- NVLink, NVSwitch, InfiniBand NDR, RoCEv2, GPUDirect RDMA, and NCCL collective algorithms from Part 12.
- PagedAttention, continuous batching, chunked prefill, and RadixAttention from Chapters 15.3 and 15.4.

### Outcomes
After completing this chapter, you will be able to achieve five engineering goals.
- **Parallelism mapping:** Map Tensor, Pipeline, Expert, Data, and Context or Helix Parallelism onto intra-node NVLink and inter-node InfiniBand fabrics. You will also prove why cross-node Tensor Parallelism breaks Inter-Token Latency.
- **Wide Expert Parallelism:** Architect wide Expert Parallelism for massive Mixture-of-Experts models like DeepSeek-R1 across multi-node clusters and GB200 NVL72 racks. You will also contrast Tensor Parallel plus Expert Parallel execution against Data Parallel Attention.
- **Dynamic MoE routing:** Optimize dynamic Mixture-of-Experts token routing using hierarchical AllToAll collectives, wave scheduling, capacity factors, expert collocation, and the DeepSeek Expert Parallelism Load Balancer.
- **Speculative and constrained decoding:** Calculate expected tokens per pass and net wall-clock speedup for speculative decoding. You will also configure two-model draft-verify, Medusa, EAGLE, Multi-Token Prediction, Lookahead decoding, and XGrammar constrained decoding.
- **Multi-node Kubernetes serving:** Deploy multi-node inference workloads on Kubernetes using Ray and LeaderWorkerSet with GPUDirect RDMA. You will also tune bounded-load prefix-aware routing and resolve cross-node NCCL and KV cache starvation incidents.

---

## 1. The 5D Parallelism Taxonomy for Multi-Node Inference

### 1.1 Why Inference Parallelism Differs from Training Parallelism

Distributed training and distributed inference solve different equations. Training processes massive batches of tokens where forward and backward computation dominates communication time. Inference serves interactive requests where batch sizes are small. Every generated token must stream back to the user immediately.

Every LLM request executes two distinct stages. During prefill, the engine processes all input prompt tokens in parallel. That parallel work makes prefill compute-bound on GPU Tensor Cores. During decode, the engine generates one token per step for each active sequence. It reads all model weights and cached Key-Value tensors from High-Bandwidth Memory for just a handful of operations per byte. Decode is therefore strictly memory-bandwidth bound.

```text
Hardware Roofline and Memory Bandwidth Reference (HLS Ch. 5; Volume 12 Ch. 9):
- Matmul arithmetic intensity: FLOPs / Bytes = (2 * M * N * K) / (2 * (M * K + K * N + M * N))
- NVIDIA L40S (48 GB GDDR6, 864 GB/s HBM, 362.05 TFLOPS FP16/BF16, 733 TFLOPS FP8):
  FP16 Roofline Knee = 362 TFLOPS / 864 GB/s = 419 FLOPS/Byte
  Square matmul M=N=K=64 -> 21 FLOPS/B (memory-bound); M=512 -> 170 FLOPS/B (memory-bound); M=4096 -> 1,365 FLOPS/B (compute-bound)
  LLM hidden_dim h = 4096:
  Prefill (s = 64 -> 62.06 FLOPS/B; s = 512 -> 409.60 FLOPS/B; s = 4096 -> 1,365.33 FLOPS/B compute-bound)
  Decode (s_decode = 1): ~1.0 FLOPS/B regardless of prompt length (strictly memory-bandwidth bound)
- GPU HBM vs Interconnect Bandwidth Gap (H100 SXM vs H200 SXM vs H100 NVL):
  H200 SXM: 141 GB HBM3e, 4.8 TB/s HBM bandwidth, 1,979 TFLOPS BF16, 900 GB/s NVLink 4 (~$6.30/hr)
  H100 SXM: 80 GB HBM3, 3.35 TB/s HBM bandwidth, 1,979 TFLOPS BF16, 900 GB/s NVLink 4 (~$6.20/hr)
  H100 NVL: 94 GB HBM3, 3.9 TB/s HBM bandwidth, 600 GB/s 2-GPU NVLink bridge
  A100 SXM: 80 GB HBM2e, 1.935 TB/s HBM bandwidth, 312 TFLOPS BF16, 600 GB/s NVLink 3 (~$2.70/hr)
  A10:      24 GB GDDR6, 0.6 TB/s HBM bandwidth, 125 TFLOPS BF16, PCIe only (< $1.25/hr)
```

Even inside a single H100 SXM server, local HBM bandwidth at 3.35 TB/s is nearly four times faster than NVLink at 900 GB/s. Therefore, if a model fits on a single GPU after quantization and meets your latency target, keep it on one GPU. That avoids all inter-GPU communication overhead. When a model exceeds single-GPU memory or requires pooled memory bandwidth, you combine up to five parallelism strategies.

| Parallelism Strategy | Partition Basis | Communication Collective | Primary Interconnect | Impact on TTFT & ITL | KV Cache Layout |
|---|---|---|---|---|---|
| Tensor Parallelism (TP) | Splits weight matrices within each layer (column & row parallel) | 2 synchronous AllReduce calls per layer per token | Intra-node NVLink / NVSwitch (900 to 1,800 GB/s) | Cuts both TTFT and ITL by pooling compute and HBM bandwidth | KV heads sharded across TP ranks or replicated if `H_kv < TP` |
| Pipeline Parallelism (PP) | Splits contiguous blocks of layers across sequential stages | Point-to-point `NCCL_Send` / `Recv` at stage boundaries | Inter-node InfiniBand NDR / RoCEv2 (400 to 800 Gbps GDR) | Increases single-request ITL slightly; scales deep models across nodes | Each stage stores KV blocks only for its assigned layers |
| Expert Parallelism (EP) | Distributes complete MoE experts across GPUs | 2 AllToAll shuffles (dispatch & combine) per MoE layer | NVSwitch intra-rack (NVL72) or Dual-Rail RDMA (`DeepEP`) | Scales MoE capacity to trillions of parameters at constant active FLOPs | Combined with TP or DP Attention (`--enable-dp-attention`) |
| Data Parallelism (DP) | Replicates complete model or TP/PP group across independent instances | Zero inter-replica collectives during forward pass | Standard Ethernet or any cluster fabric behind a router | Scales QPS throughput linearly; zero speedup for single-query latency | Isolated full KV cache pool per replica or per DP Attention rank |
| Context / Helix Parallelism (CP) | Splits input sequence tokens and KV cache across GPUs | Ring or all-gather KV exchange at sequence chunk boundaries | Intra-node NVLink or high-speed RDMA | Cuts TTFT near-linearly on 100k+ to 1M token prompts | Each GPU stores KV cache only for its assigned sequence segment |

### 1.2 Tensor Parallelism Mechanics and Why TP Across PCIe or Ethernet Breaks ITL

Tensor Parallelism, pioneered by Megatron-LM, splits the weight matrices of each Transformer block across *N* GPUs. All *N* GPUs compute every token in lockstep. Each Transformer block contains two self-attention projections and two feed-forward projections paired as Column-Parallel and Row-Parallel layers.
- **Column-Parallel Linear Layers:** Used for the Query, Key, and Value projections and the MLP gate and up projections. The input activation tensor is replicated across all Tensor Parallel ranks. The weight matrix is sliced column-wise across the ranks. Each GPU computes its partial column output locally without any inter-GPU communication.
- **Row-Parallel Linear Layers:** Used for the attention output projection and the MLP down projection. The weight matrix is sliced row-wise across the ranks. Each GPU multiplies its local activation shard by its local weight rows. Because each rank holds only a partial sum of the full output vector, all ranks must execute a synchronous **AllReduce sum** before the layer normalization.

```mermaid
flowchart LR
    subgraph Layer["Single Transformer Layer (TP = N GPUs)"]
        direction LR
        In["Input X"] --> Col1["Attention QKV<br/>(Column-Parallel)"]
        Col1 --> Row1["Attention Out W_o<br/>(Row-Parallel)"]
        Row1 --> AR1["AllReduce #1<br/>2*(N-1) Ring Steps"]
        AR1 --> Col2["MLP Gate / Up<br/>(Column-Parallel)"]
        Col2 --> Row2["MLP Down<br/>(Row-Parallel)"]
        Row2 --> AR2["AllReduce #2<br/>2*(N-1) Ring Steps"]
    end
```

Because every Transformer layer contains two Row-Parallel projections, Tensor Parallelism executes **two synchronous AllReduce operations per layer**. For an eighty-layer model like Llama-3-70B, generating a single token requires **160 synchronous AllReduce operations**. At a streaming rate of fifty tokens per second, the cluster executes **8,000 AllReduce collectives every second**.

In a ring AllReduce across *N* GPUs, a ReduceScatter phase is followed by an AllGather phase. Each phase takes *N* minus one steps, requiring **twice *N* minus one sequential transfer hops** per collective.

```text
Tensor Parallel AllReduce Volume and Latency Equations (Volume 12 Ch. 5 & 9; ASP Ch. 15):
- AllReduce calls per token:         C_token = 2 * L  (for L = 80 layers -> 160 AllReduces/token)
- Ring steps per AllReduce:          S_ring  = 2 * (N - 1)
  * TP = 8  (single 8-GPU node):     2 * (8 - 1)  = 14 steps/AllReduce -> 160 * 14 = 2,240 ring steps/token
  * TP = 16 (two 8-GPU nodes):       2 * (16 - 1) = 30 steps/AllReduce -> 160 * 30 = 4,800 ring steps/token
- Data volume moved per rank per AllReduce:
  Data_Volume = 2 * ((N - 1) / N) * B * S * H * BytesPerElement
  For B = 1, S = 1, H = 8192, BF16 (2 bytes) -> Tensor size = 16,384 bytes (16 KiB)
  At TP = 8:  2 * (7 / 8) * 16,384 bytes = 28,672 bytes (28 KiB) per AllReduce -> 4.59 MB/token across 160 calls
- Per-token communication time:
  T_comm_token = 2 * L * (Data_Volume / BW_link + Latency_collective)
  * NVLink 4 (900 GB/s, ~0.8 us/collective): 160 * (0.03 us + 0.8 us) = 0.13 ms/token (< 1% of 14.13 ms ITL)
  * PCIe Gen5 / 100GbE TCP (12.5 to 64 GB/s, 300 to 1,250 us/collective):
    160 * (0.3125 ms to 1.25 ms) = 50.0 ms to 200.0 ms/token (> 85% to 93% of execution time spent waiting)
```

That math establishes a hard law for inference infrastructure: **never span Tensor Parallelism across PCIe-only slots or standard inter-node networks**. Within an eight-GPU server connected by NVSwitch at 900 GB/s on H100 or 1.8 TB/s on Blackwell B200, those AllReduces add just 0.13 milliseconds per token. Once Tensor Parallelism crosses a server chassis boundary over PCIe or Ethernet, those 160 barriers add 50 to 200 milliseconds of latency to every single token.

| Interconnect Layer | Physical Interface | Bidirectional Bandwidth | Per-Hop Latency | Viable Parallelism Strategy |
|---|---|---|---|---|
| NVLink 5 (Blackwell B200 / GB200 NVL72) | 18x 100 GB/s links + NVSwitch 4 (130 TB/s rack) | 1,800 GB/s (1.8 TB/s) per GPU | `< 1.0 us` | Intra-node TP (TP = 2..8) & Wide EP / TP up to 72 GPUs (NVL72) |
| NVLink 4 (Hopper H100 / H200 SXM) | 4x NVSwitch 3 full mesh (vs 128 GB/s P2P without NVSwitch) | 900 GB/s per GPU | `< 1.0 us` | Intra-node Tensor Parallelism (TP = 2, 4, 8) & Intra-node EP |
| NVLink 3 (A100 SXM) / H100 NVL Bridge | NVSwitch mesh (A100) or 2-GPU Bridge (H100 NVL) | 600 GB/s per GPU | `< 1.5 us` | Intra-node TP (TP = 2..8 on A100; TP = 2 only on H100 NVL) |
| ConnectX-8 SuperNIC / XDR InfiniBand | PCIe Gen6 + GPUDirect RDMA (1:1 NIC:GPU) | 800 Gbps (100 GB/s) per port | `1.0 - 2.0 us` | Inter-node Pipeline Parallelism (PP), Wide EP, NIXL KV transfer |
| InfiniBand NDR / RoCEv2 (ConnectX-7) | PCIe Gen5 + GPUDirect RDMA (`NCCL_NET_GDR_LEVEL=5`) | 400 Gbps (50 GB/s) per port | `1.5 - 3.0 us` | Inter-node Pipeline Parallelism (PP), EP, Data Parallelism (DP) |
| PCIe Gen5 x16 (Host Bus Switch) | Local PCIe root / switch without NVLink | 64 GB/s per dir (128 GB/s bidir) | `5 - 10 us` | Pipeline Parallelism (PP) or Data Parallel Replicas (DP) |
| Standard 100GbE Ethernet | Host kernel TCP/IP socket stack | 100 Gbps (12.5 GB/s) | `50 - 150 us` | Data Parallel Replicas (DP) ONLY |

### 1.3 Pipeline Parallelism, Context Parallelism, and Helix Parallelism

When a model is too large to fit inside a single eight-GPU node even after quantization, combine intra-node Tensor Parallelism with inter-node **Pipeline Parallelism**. Pipeline Parallelism slices the model vertically into contiguous layer stages across *P* nodes. For an eighty-layer model with two pipeline stages, the first node runs the first forty layers with eight-way Tensor Parallelism. The second node runs the remaining forty layers with eight-way Tensor Parallelism.

Instead of communicating twice per layer, Pipeline Parallelism sends an activation tensor across the network **only at stage boundaries**. That requires just one point-to-point `NCCL_Send` and `NCCL_Recv` transfer per stage boundary on each forward pass. Better yet, combining Tensor Parallelism within each node with Pipeline Parallelism across nodes shrinks the cross-node transfer size by the Tensor Parallel factor. Each GPU on the upstream stage sends only its local activation shard directly to its same-rail peer on the downstream node. For a hidden dimension of 8,192 and four-way Tensor Parallelism, each rank transfers only 2,048 elements per token.

Pipeline Parallelism has one major drawback during single-request decoding: **pipeline bubbles**. While the first stage computes a token step, downstream stages sit idle waiting for the activation baton. In production serving, engines eliminate that bubble by interleaving micro-batches from multiple concurrent user requests alongside `--enable-chunked-prefill` and `--max-num-batched-tokens 2048`. That keeps every pipeline stage busy on every millisecond.

For workloads with extreme prompt lengths of one hundred thousand to one million tokens, **Context Parallelism** partitions the input sequence itself across multiple GPUs. This strategy is also called Sequence Parallelism or Helix Parallelism when pipelined across attention and Key-Value dimensions. Using Ring Attention or blocked attention, each GPU stores the Key-Value cache only for its local sequence chunk. The GPUs exchange compact boundary statistics around a logical ring. Context Parallelism cuts prefill Time to First Token roughly in half every time you double the GPU count. On million-token contexts with DeepSeek-V3.1, SGLang's long-context pipeline and sequence parallelism achieves a 3.31x increase in prefill throughput. It also delivers an 81 percent reduction in Time to First Token at 82.8 percent scaling efficiency.

Always keep Tensor Parallelism inside a single NVLink domain and use Pipeline or Context Parallelism only when model weights or million-token contexts exceed single-node memory.

---

## 2. Wide Expert Parallelism, DeepSeek-R1 671B, and GB200 NVL72

### 2.1 Sparse Mixture-of-Experts Mechanics and DeepSeek-R1 671B

Dense models activate every parameter for every token, causing compute cost and memory bandwidth to grow linearly with model size. Sparse **Mixture-of-Experts** models decouple total parameter capacity from per-token compute. They replace each dense feed-forward network with dozens or hundreds of specialist expert MLPs controlled by a lightweight gating router.

DeepSeek-V3 and DeepSeek-R1 exemplify this hardware-software co-design. The full model contains **671 billion parameters**, yet activates only **37 billion parameters per token**, or just 5.51 percent of the network. In each Mixture-of-Experts layer, every token passes through one shared expert plus eight routed experts chosen out of 256 routed experts. That gives nine active experts per token. This sparsity allowed DeepSeek to train DeepSeek-V3 on 2,048 export-restricted H800 GPUs for 5.5 million dollars.

```text
DeepSeek-R1 671B Architecture and Distilled Model Comparison (ASP Ch. 1, 15; DAI Ch. 6, 11; HLS Ch. 5, 6):
- DeepSeek-V3 / DeepSeek-R1 Full MoE Model:
  Total parameters = 671B (~680B with MTP/auxiliary heads); Active parameters/token = 37B (5.51%)
  Expert layout per MoE layer = 1 shared expert + 256 routed experts (top-8 selected -> 9 active experts/token)
  Routed expert activation density = 8 / 256 = 3.125% (> 3.0% threshold where Expert Parallelism beats pure TP)
- Benchmark Comparison (DeepSeek-R1-671B vs DeepSeek-R1-Distill-Llama-70B, HLS Table 6-6):
  * MATH-500 pass@1:       97.3% (671B) vs 94.5% (70B Distill)
  * GPQA Diamond pass@1:   71.5% (671B) vs 65.2% (70B Distill)
  * LiveCodeBench pass@1:  65.9% (671B) vs 57.5% (70B Distill)
- Multi-Node Serving Footprints for DeepSeek-R1 671B:
  * 8x H200 SXM (8 * 141 GB = 1,128 GB HBM3e): Fits full 671B model in FP8 (~671 GB) on a single 8-GPU node
  * 32x H100 80 GB (4 nodes, TP = 4 intra-node x PP = 8 inter-node): ~83.875B (~84B) parameters per PP stage
  * 64-GPU Hybrid MoE Cluster (ASP Ch. 15, 60 layers, 64 experts, 16 groups of 4 GPUs):
    PP = 4 (15 layers/stage) * TP = 2 * EP = 16 (top-2 gating), scaled to 128 GPUs with DP = 2
```

### 2.2 TP+EP vs DP+EP (Data-Parallel Attention) in vLLM and SGLang

Without Expert Parallelism, an inference engine shards every expert's weights across all Tensor Parallel ranks. Every GPU holds a slice of all 256 experts. Enabling **Expert Parallelism** via `--enable-expert-parallel` in vLLM or `--ep` in SGLang changes the weight layout. Each GPU now holds *complete* experts for a subset of the expert pool.

In vLLM, the Expert Parallel group size equals the Tensor Parallel size multiplied by the Data Parallel size. The flag only takes effect when that product exceeds one; if both are set to one, the flag is silently ignored. For DeepSeek-R1 with 256 routed experts on eight GPUs, each GPU hosts 32 complete experts. However, how you form that group of eight GPUs fundamentally changes both network collectives and Key-Value cache memory.

```mermaid
flowchart TB
    subgraph TPEP["Mode A: TP = 8, DP = 1 + EP (Low-Latency / Low-Concurrency)"]
        direction LR
        T1["All 8 GPUs process same request batch<br/>MLA Compressed KV Cache duplicated 8x"] --> T2["32 Complete Experts / GPU<br/>Synced via AllReduce over NVLink"]
    end

    subgraph DPEP["Mode B: DP = 8, TP = 1 + EP (DP Attention / High-Throughput)"]
        direction LR
        D1["Each GPU processes independent requests<br/>Partitioned KV Cache (1x, zero duplication)"] --> D2["AllToAll Token Dispatch (DeepEP)<br/>32 Experts / GPU + AllToAll Combine"]
    end
```

- **Tensor Parallelism plus Expert Parallelism:** Every GPU participates in every request and synchronizes layer outputs using **AllReduce**. While simple, this mode creates a severe Key-Value cache penalty for models like DeepSeek-R1 that use **Multi-Head Latent Attention** or Multi-Query Attention. Because Multi-Head Latent Attention compresses Keys and Values into a single shared latent vector, standard Tensor Parallelism cannot split the cache by head. Instead, it **replicates the entire KV cache across all eight GPUs**.
- **Data Parallelism plus Expert Parallelism with DP Attention:** Passing `--data-parallel-size 8 --enable-expert-parallel` in vLLM or `--enable-dp-attention --dp-size 8` in SGLang runs the attention layers using Data Parallelism. Each GPU stores the KV cache *only* for its own assigned requests. That eliminates the eightfold KV cache duplication and increases decode throughput by up to **1.9x**. Before the Mixture-of-Experts layer, the GPUs execute an **AllToAll** collective via `DeepEP` and `DeepGEMM` to route each token to the GPU hosting its selected experts. A second AllToAll returns the expert outputs.

Expert Parallelism is beneficial whenever expert activation density exceeds **3 percent**, such as DeepSeek-R1's 3.12 percent density. At that density, the memory bandwidth saved by loading fewer expert weights outweighs the AllToAll network cost. For ultra-sparse models with under **1 percent** activation density at tiny batch sizes, AllToAll latency can exceed the compute savings.

### 2.3 Wide Expert Parallelism on GB200 NVL72

On traditional eight-GPU servers, scaling Expert Parallelism past eight GPUs forces the twice-per-layer Mixture-of-Experts AllToAll shuffle across the slower inter-node InfiniBand fabric. NVIDIA's **GB200 NVL72** rack eliminates that node boundary across **72 Blackwell GPUs**.

Each GB200 NVL72 rack houses 36 Grace CPUs and 72 Blackwell GPUs connected through an on-rack NVLink Switch fabric. Every GPU enjoys **1.8 TB/s** of bidirectional NVLink 5 bandwidth, providing **130 TB/s** of non-blocking aggregate GPU-to-GPU bandwidth. The rack pools **13,824 GB** of HBM3e memory across the 72 GPUs, or 30 TB total memory including Grace CPU RAM inside the same NVLink domain. Furthermore, NVLink Switch Systems can unify up to eight racks into a 576-GPU all-to-all fabric. In MLPerf Inference v5.0, the GB200 NVL72 delivered **3.4x higher inference throughput per GPU** than Hopper clusters.

Inside a 72-GPU NVLink domain, engineers deploy **Wide Expert Parallelism** across 64 or 72 GPUs combined with Data-Parallel Attention. Across 64 GPUs, each GPU hosts just four routed experts of DeepSeek-R1. Because every GPU-to-GPU hop traverses the 130 TB/s NVSwitch backplane in sub-microsecond latency, wide AllToAll expert shuffles execute at intra-node speeds. That leaves over twelve terabytes of HBM3e free for massive concurrent KV caches.

### 2.4 Dynamic MoE Routing, Wave Scheduling, Capacity Factor, and EPLB

Even on fast interconnects, naive Mixture-of-Experts routing creates two production bottlenecks: AllToAll network microbursts and hot-expert stragglers.

First, optimize **expert communication**. If all 72 GPUs in an NVL72 rack execute a monolithic AllToAll simultaneously, every GPU sends a message to 71 peers at the exact same instant. That floods the NVSwitch fabric with 5,112 concurrent messages. **Wave scheduling** breaks that collective into four staggered waves of 18 GPUs each. Each wave sends only 306 intra-wave messages, a **16.71x reduction** in instantaneous switch queue pressure. The engine overlaps communication of the current wave with expert computation of the previous wave using `--enable-two-batch-overlap`. On multi-node InfiniBand clusters, use a **two-stage hierarchical AllToAll** that shuffles tokens inside the node over NVLink first and crosses InfiniBand only for remote experts. Combine that with butterfly schedules, FP8 or NVFP4 activation casting, and **expert collocation**, which places frequently co-activated experts on the same GPU.

Second, eliminate **hot-expert stragglers**. Because AllToAll is a synchronous collective barrier across all participating GPUs, a single overloaded GPU running at **99 percent utilization** stalls peer GPUs sitting at **60 percent utilization**. Production engines use three defenses to balance expert load.
- **Capacity Factor:** Caps the maximum tokens an expert processes per pass. With a base average load of 32 tokens per expert, setting a capacity factor of 1.2 gives a twenty percent overflow allowance and caps each expert at **38 tokens**. Any excess tokens beyond that cap overflow to the token's second-choice expert or a fallback pass.
- **Expert Replication and DeepSeek EPLB:** DeepSeek's open-source **Expert Parallelism Load Balancer** tracks per-expert token routing counters in real time. When a specific expert receives 50 tokens while peers receive 20 to 30, EPLB clones that hot expert's weights onto a redundant GPU slot. Splitting incoming traffic across both copies cuts the peak load from 50 tokens down to 30 tokens.
- **Biased Gating Score Adaptive Routing:** At runtime, the inference engine wraps the gating softmax and subtracts a dynamic load penalty bias from overloaded experts. Configure Prometheus alerts whenever an expert exceeds **80 percent utilization** so the router nudges borderline tokens toward underutilized replicas without retraining.

Always combine Data-Parallel Attention with hierarchical double-buffered AllToAll and EPLB expert replication when serving large Mixture-of-Experts models at scale.

---

## 3. Speculative Decoding, Parallel Token Generation, and Constrained Decoding

### 3.1 The Sequential Decode Bottleneck and Draft-Verify Rejection Math

Even with optimal parallelism, standard autoregressive decoding generates only one token per forward pass. Because a single token vector has an arithmetic intensity of roughly 1.0 FLOP per byte, the GPU spends over ninety percent of each decode step waiting on High-Bandwidth Memory reads. Meanwhile, its Tensor Cores sit idle.

**Speculative decoding** turns that spare Tensor Core capacity into lower latency. A fast draft mechanism proposes *K* candidate tokens ahead. The large target model then verifies all *K* tokens in a **single parallel forward pass**. Because verifying *K* tokens processes a matrix of *K* rows instead of one row, the target model reads its weights from HBM once while performing *K* times more useful computation.

To guarantee that speculative decoding produces the **exact same output distribution** as standard autoregressive sampling without any quality loss, the engine applies **modified rejection sampling** sequentially across the *K* drafted tokens.
- **Token probability comparison:** For each drafted token position, the engine compares the target model probability against the draft model probability.
- **Guaranteed acceptance case:** When the target probability is greater than or equal to the draft probability, the engine accepts the drafted token with **100 percent probability**. Suppose the prompt ends with `The soccer team of the United` and the draft model proposes `States` with probability 0.6. When the target model assigns 0.8, the token is immediately accepted.
- **Probabilistic acceptance case:** When the target probability is lower than the draft probability, the engine accepts the token at the ratio of target-to-draft probability. When the target model assigns 0.4 and the draft model assigned 0.6, the engine accepts the token with probability 66.67 percent.
- **Residual resampling and bonus token:** At the first rejected position, the engine discards all subsequent draft tokens and samples one corrected replacement token directly from the target model's residual distribution. When all *K* drafted tokens are accepted, the engine samples one bonus token from the target model's final logit position, yielding *K* plus one tokens in a single target pass.

```text
Speculative Decoding Expected Tokens and Net Speedup Equations (ASP Ch. 15; HLS Ch. 7):
- Rejection sampling acceptance probability at step i:
  beta_i = min(1.0, p_target(x_i) / q_draft(x_i))
  * Case 1: p_target = 0.8, q_draft = 0.6 -> min(1.0, 0.8 / 0.6) = 1.0000 (100% accepted)
  * Case 2: p_target = 0.4, q_draft = 0.6 -> min(1.0, 0.4 / 0.6) = 0.6667 (66.67% accepted)
- Expected tokens generated per target verification pass (uniform acceptance rate alpha):
  E[tokens] = 1 + alpha + alpha^2 + ... + alpha^K = (1 - alpha^(K + 1)) / (1 - alpha)
  * For K = 4, alpha = 0.8: E[tokens] = (1 - 0.8^5) / (1 - 0.8) = (1 - 0.32768) / 0.2 = 3.3616 tokens/pass
  * For K = 4, alpha = 0.6: E[tokens] = (1 - 0.6^5) / (1 - 0.6) = (1 - 0.07776) / 0.4 = 2.3056 tokens/pass
- Wall-clock net speedup (where c_draft = t_draft / t_target is the single-step draft-to-target cost ratio):
  Speedup = E[tokens] / (1 + K * c_draft)
  * Fast draft model (10x faster, c_draft = 0.10, K = 4, alpha = 0.8):
    Cycle cost = 1 + 4 * 0.10 = 1.40 target-pass units -> Speedup = 3.3616 / 1.40 = 2.40x
  * Slow draft model (< 4x faster, c_draft = 0.35, K = 4, alpha = 0.6):
    Cycle cost = 1 + 4 * 0.35 = 2.40 target-pass units -> Speedup = 2.3056 / 2.40 = 0.96x (net slowdown)
- Positional Acceptance Decay Example (HLS Ch. 7, K = 6):
  Observed position acceptance rates = [0.8, 0.7, 0.6, 0.5, 0.10, 0.02]
  Cumulative prefix survival probs   = [0.8000, 0.5600, 0.3360, 0.1680, 0.0168, 0.0003]
  E[tokens] at K = 4 = 1 + 0.8 + 0.56 + 0.336 + 0.168 = 2.8640 tokens
  E[tokens] at K = 6 = 2.8640 + 0.0168 + 0.0003       = 2.8811 tokens (steps 5 & 6 add only 0.0171 tokens)
```

Three operational rules govern two-model speculative decoding in production. First, the draft model must be **at least 4x faster** than the target model or draft overhead will erase verification gains. Second, both models **must share the exact same tokenizer and vocabulary**. Third, monitor per-position acceptance rates and trim *K* whenever tail positions drop below ten percent acceptance.

### 3.2 Medusa, EAGLE-1/2/3, Multi-Token Prediction (MTP), and Lookahead Decoding

Deploying a separate draft model complicates cluster operations because you must allocate HBM for two models and coordinate two schedulers. Modern inference engines therefore favor **single-model self-drafting** and **model-free speculation**.

| Speculative Architecture | Drafting Mechanism | Extra Weights / Training Required | Typical Speedup vs Baseline | Production Sweet Spot |
|---|---|---|---|---|
| Two-Model Draft-Verify | Separate small draft LLM (1.5B or 7B for 70B target) | Separate pretrained / distilled model (same tokenizer) | 1.5–2.5x (3–4x on code/JSON) | General decoding when a matching small family model exists |
| Medusa (Medusa-1 / Medusa-2) | Attaches multiple lightweight decoding heads to top hidden state + tree attention | Fine-tunes heads only (Medusa-1) or joint model + heads (Medusa-2) | 2.2–3.6x (4 tokens/pass cuts 100 tokens to 25 passes) | Single-model serving with parallel tree candidate verification |
| EAGLE (EAGLE-1 / EAGLE-2 / EAGLE-3) | Autoregressive feature-level head or multi-layer direct token fusion | Lightweight auxiliary EAGLE head (~1 Transformer layer) | 3.5x (EAGLE-1), +20%–40% (EAGLE-2), up to 6.5x (EAGLE-3; 1.96x on Qwen3-32B) | Highest single-model acceptance rate in vLLM, SGLang, and TensorRT-LLM |
| Multi-Token Prediction (MTP) | Sequential causal MTP modules trained natively inside DeepSeek-V3 / DeepSeek-R1 | Built into base pretraining (zero external draft setup) | 1.8–2.5x (80%–90% first-token acceptance) | Native speculative decoding on DeepSeek-V3 and DeepSeek-R1 |
| Lookahead / N-gram Prompt Lookup | Matches n-gram subsequences from prompt/context cache or Jacobi n-gram pools | Zero extra parameters, zero training (`method="ngram"`) | +16% to 2x on RAG, templates, and JSON | Zero-memory-overhead acceleration for grounded RAG and code editing |
| Self-Speculative Layer Skipping & Consistent Decoding | Skips every Nth layer / uses FP4 in draft pass (~2x), or trains consistency objective (~3x) | Zero extra weights (layer skip) or consistency fine-tuning | 2x to 3x | Memory-constrained deployments that cannot load draft heads |

Let us examine how each single-model method improves upon two-model drafting.
- **Medusa:** Instead of running a sequential draft loop, Medusa attaches *M* parallel linear heads to the target model's final hidden state. Each head predicts a specific future token position simultaneously in the same forward pass. Medusa arranges the top candidates from each head into a **tree-based attention mask**. A binary tree of depth two proposes four tokens per pass, which cuts a 100-token reply from 100 iterations to 25 ideal iterations. Medusa verifies all branches in one pass and achieves **2.2x to 3.6x speedups**.
- **EAGLE, EAGLE-2, and EAGLE-3:** Predicting multiple tokens independently from the same hidden state suffers when a later token depends strongly on the immediately preceding choice. **EAGLE** solves this by running a tiny autoregressive module at the *feature level*. It feeds both the previous hidden state and the sampled token embedding into a single-layer head. EAGLE achieved up to **3.5x speedup** on four-token drafts. **EAGLE-2** added a context-aware dynamic draft tree that expands or prunes branches based on draft confidence, running **20 to 40 percent faster** than EAGLE. **EAGLE-3** removed the feature-prediction constraint and fused representations from lower, middle, and upper target layers to predict draft tokens directly. That design achieves up to **1.4x speedup over EAGLE-2** and up to **6.5x over unoptimized baselines**.
- **Multi-Token Prediction:** Introduced in DeepSeek-V3 and DeepSeek-R1, Multi-Token Prediction bakes sequential prediction modules directly into the foundation model during pretraining. Unlike Medusa's independent heads, each module uses a complete causal Transformer block. It takes the previous depth's hidden representation and token embedding to predict the next token. At inference time, those built-in heads act as a native, zero-configuration speculative drafter with high acceptance rates.
- **Lookahead and N-gram Prompt Lookup:** When users summarize documents, edit code, or fill structured templates, the generated output frequently copies multi-word phrases directly from the prompt. N-gram prompt lookup maintains a fast hash table of prompt n-grams and proposes matching continuations with zero neural network overhead. Lookahead decoding extends this idea by maintaining a two-dimensional window of Jacobi iteration trajectories and cached n-grams in parallel.

### 3.3 Concurrency Trade-Offs and vLLM Speculative Decoding Configuration

Speculative decoding is not a free lunch at high batch concurrency. When concurrency is one, decode is severely memory-bandwidth bound, so verifying four draft tokens takes nearly the exact same wall-clock time as generating one token. When concurrency climbs to 16 or 64 concurrent requests, multiplying the active token batch pushes the GPU across its 419 FLOPS per byte Roofline knee into the **compute-bound regime**.

```text
vLLM Speculative Decoding Benchmark on Qwen/Qwen3-32B (HLS Ch. 7 Fig. 7-4 & 7-5):
- Setup 1 (Vanilla vLLM baseline):                28.9 tokens/s at C = 1
- Setup 2 (N-gram K = 6, min = 4, max = 6):       Slight gain at C = 1; slower than vanilla at C = 16
- Setup 3 (Improved N-gram K = 4, min = 2, max = 128): +16% throughput (~33.5 tokens/s) at C = 1; slower at C = 16
- Setup 4 (EAGLE-3 K = 3, RedHatAI/Qwen3-32B-speculator.eagle3):
  56.5 tokens/s vs 28.9 tokens/s at C = 1 (1.96x speedup, nearly 2x)
  At C = 16: EAGLE-3 still beats vanilla ITL and throughput, but by a smaller margin and with higher TTFT
```

Below are the production vLLM commands to launch N-gram prompt lookup and EAGLE-3 speculative decoding.

```bash
# 1. Zero-weight N-gram speculative decoding (ideal for RAG, code edits, and JSON templates)
vllm serve Qwen/Qwen3-32B \
  --speculative-config '{"method": "ngram", "num_speculative_tokens": 4, "prompt_lookup_min": 2, "prompt_lookup_max": 128}' \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.95

# 2. EAGLE-3 speculative decoding (ideal for general low-ITL reasoning and chat)
vllm serve Qwen/Qwen3-32B \
  --speculative-config '{"method": "eagle3", "model": "RedHatAI/Qwen3-32B-speculator.eagle3", "num_speculative_tokens": 3}' \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.95
```

### 3.4 Constrained Decoding Performance Implications

Production applications frequently require **constrained decoding**—also called structured outputs—to guarantee that generated tokens match a strict JSON schema or context-free grammar for function calling. Naive constrained decoders evaluate valid next tokens on the CPU at every decode step across a 128,000-token vocabulary. That check adds several milliseconds per token and thrashes CPU caches.

To eliminate that bottleneck, TensorRT-LLM, vLLM, and SGLang integrate **XGrammar** and **Outlines**. These engines precompile the JSON schema into a compact finite-state machine or pushdown automaton ahead of time. They precompute valid token bitmasks for each state and inject the bitmask directly into the GPU softmax kernel while overlapping mask preparation on the CPU. For moderate JSON schemas at scale, compiled grammar masking keeps latency overhead in the **low single-digit percent range**. Overly restrictive or deeply nested schemas can still trigger first-request compilation stalls or double-digit backtracking overhead.

Enable EAGLE-3 or Multi-Token Prediction for low-concurrency interactive workloads, and precompile compact JSON schemas with XGrammar so structured outputs never stall the GPU decode loop.

---

## 4. Multi-Node Orchestration on Kubernetes: Ray and LeaderWorkerSet (LWS)

### 4.1 Why Standard Kubernetes Deployments Fail for Multi-Node Sharded LLMs

When a model fits inside a single server, such as Llama-3-70B on one eight-GPU node, a standard Kubernetes `Deployment` works cleanly. Each pod requests `nvidia.com/gpu: 8`, mounts one complete model replica, and scales horizontally behind a Service. Within a single node, four GPUs typically deliver roughly **3.5x the throughput** of one GPU.

Once a model like Llama-3-405B or DeepSeek-R1 spans multiple nodes, standard Kubernetes `Deployment` and `StatefulSet` primitives break down for three reasons.
- **Asymmetric Leader-Worker Roles:** A multi-node inference instance is not a collection of identical stateless pods. Exactly one leader pod must host the OpenAI HTTP server, global request scheduler, and Ray head or `torch.distributed` master. The remaining worker pods act as headless GPU shard workers.
- **All-or-Nothing Gang Scheduling:** Suppose a two-node model instance has only one pod scheduled while the second pod sits `Pending`. The first pod's eight GPUs sit completely idle burning money. Worse, two partially scheduled jobs can deadlock the cluster.
- **Atomic Failure Domain Recovery:** If a worker pod crashes due to an uncorrectable ECC error or node drain, the leader pod cannot serve requests with half a neural network. The orchestrator must tear down and recreate the entire multi-node pod group atomically.

### 4.2 Kubernetes LeaderWorkerSet (`LWS`) + GPUDirect RDMA Manifest

The Kubernetes **LeaderWorkerSet** (`leaderworkerset.x-k8s.io/v1`) API solves all three problems natively. A LeaderWorkerSet resource manages a set of *R* model replicas, where each replica is a tightly coupled **pod group** of one leader pod and *S* minus one worker pods. LeaderWorkerSet provides built-in headless DNS discovery per group and atomic recreate-on-failure semantics via `RecreateGroupOnPodRestart`. It also integrates directly with gang and topology-aware schedulers such as **Kueue**, **NVIDIA KAI Scheduler**, and **Volcano**.

```mermaid
flowchart TB
    Router["Prefix-Aware Gateway / llm-d Router<br/>(Routes HTTP to Leader Pods only)"] --> L0["LWS Replica 0: Leader Pod (Rank 0)<br/>Node 0: 8x H100 (TP=8, PP Stage 0)"]
    Router --> L1["LWS Replica 1: Leader Pod (Rank 0)<br/>Node 2: 8x H100 (TP=8, PP Stage 0)"]

    subgraph Group0["LWS Group 0 (16 GPUs, Atomic Gang & Restart Unit)"]
        L0 <==>|"InfiniBand NDR 400G<br/>GPUDirect RDMA (GDR Level 5)"| W0["LWS Replica 0: Worker Pod 0 (Rank 1)<br/>Node 1: 8x H100 (TP=8, PP Stage 1)"]
    end

    subgraph Group1["LWS Group 1 (16 GPUs, Atomic Gang & Restart Unit)"]
        L1 <==>|"InfiniBand NDR 400G<br/>GPUDirect RDMA (GDR Level 5)"| W1["LWS Replica 1: Worker Pod 0 (Rank 1)<br/>Node 3: 8x H100 (TP=8, PP Stage 1)"]
    end
```

For cross-node Pipeline or Expert Parallelism to achieve 1.5 to 3.0 microsecond latency over 400 Gbps InfiniBand NDR or RoCEv2, containers must enable **GPUDirect RDMA** via `NCCL_NET_GDR_LEVEL=5` and `NCCL_IB_DISABLE=0`. Without GPUDirect RDMA, every activation tensor copies from GPU VRAM to host CPU RAM, traverses the NIC, copies into remote CPU RAM, and finally copies into remote GPU VRAM. That host-mediated detour increases point-to-point latency by **4x to 6x**.

Below is a complete production LeaderWorkerSet manifest deploying two replicas of `Meta-Llama-3-405B-Instruct-FP8` across 32 GPUs total. It uses eight-way Tensor Parallelism intra-node over NVLink and two-way Pipeline Parallelism inter-node over InfiniBand NDR with GPUDirect RDMA.

```yaml
apiVersion: leaderworkerset.x-k8s.io/v1
kind: LeaderWorkerSet
metadata:
  name: vllm-llama-405b-lws
  namespace: ai-serving
  labels:
    kueue.x-k8s.io/queue-name: gpu-nvlink-infiniband-queue
spec:
  replicas: 2                         # 2 independent DP model replicas (32 GPUs total)
  startupPolicy: LeaderCreated
  rolloutStrategy:
    type: RollingUpdate
  leaderWorkerTemplate:
    size: 2                           # 1 Leader Pod (Stage 0) + 1 Worker Pod (Stage 1) = 16 GPUs/replica
    restartPolicy: RecreateGroupOnPodRestart
    leaderTemplate:
      metadata:
        labels:
          role: leader
      spec:
        containers:
          - name: vllm-leader
            image: vllm/vllm-openai:v0.5.4
            env:
              - name: NCCL_DEBUG
                value: "INFO"
              - name: NCCL_IB_DISABLE
                value: "0"            # Enforce InfiniBand / RoCEv2 RDMA transport
              - name: NCCL_NET_GDR_LEVEL
                value: "5"            # Enable GPUDirect RDMA (PCIe switch P2P bypass)
              - name: NCCL_CROSS_NIC
                value: "1"
            command: ["sh", "-c"]
            args:
              - >-
                ray start --head --port=6379 &&
                vllm serve meta-llama/Meta-Llama-3-405B-Instruct-FP8
                --tensor-parallel-size 8
                --pipeline-parallel-size 2
                --enable-chunked-prefill
                --max-num-batched-tokens 2048
                --gpu-memory-utilization 0.90
                --port 8000
            ports:
              - containerPort: 8000
            resources:
              limits:
                nvidia.com/gpu: "8"
                rdma/rdma_shared_device_a: "1"
            volumeMounts:
              - name: dshm
                mountPath: /dev/shm
        volumes:
          - name: dshm
            emptyDir:
              medium: Memory
              sizeLimit: 32Gi
    workerTemplate:
      spec:
        containers:
          - name: vllm-worker
            image: vllm/vllm-openai:v0.5.4
            env:
              - name: NCCL_DEBUG
                value: "INFO"
              - name: NCCL_IB_DISABLE
                value: "0"
              - name: NCCL_NET_GDR_LEVEL
                value: "5"
              - name: NCCL_CROSS_NIC
                value: "1"
            command: ["sh", "-c"]
            args:
              - "ray start --address=$(LWS_LEADER_ADDRESS):6379 --block"
            resources:
              limits:
                nvidia.com/gpu: "8"
                rdma/rdma_shared_device_a: "1"
            volumeMounts:
              - name: dshm
                mountPath: /dev/shm
        volumes:
          - name: dshm
            emptyDir:
              medium: Memory
              sizeLimit: 32Gi
```

Always deploy multi-node sharded inference engines with `LeaderWorkerSet` and `RecreateGroupOnPodRestart` so Kubernetes schedules and heals multi-node shards as a single atomic unit.

---

## 5. Multi-Node Request Routing and Prefix-Aware Load Balancing

### 5.1 Why Round-Robin Fails and Unbounded Prefix Hashing Creates Hotspots

Once you deploy multiple Data Parallel replicas across a cluster, an ingress router must distribute incoming user requests across those replicas. Standard web load balancing algorithms fail badly on LLM traffic.
- **Round-Robin Failure:** Round-robin sends every fourth request to the first node regardless of prompt length. It also ignores which node already holds the user's cached prefix blocks. Consider a four-node production benchmark where each node supports 60 tokens/s, giving 240 tokens/s of ideal cluster capacity. Round-robin routing caused severe load skew across the four nodes, throttling total cluster throughput to **110 tokens/s**, or just 45.83 percent scaling efficiency.
- **Prefix-Aware Routing Advantage:** Routing requests that share a common system prompt, RAG document context, or multi-turn conversation history (`session_id`) to the same replica raises prefix cache hit rates above **85 percent**. Cached prefixes turn prefill from an expensive matrix multiplication into a fast block pointer lookup. As a result, prefix-aware routing cuts Time to First Token by **up to 90 percent**.
- **The Unbounded Prefix Hotspot Trap:** Suppose a large share of your traffic comes from a single popular enterprise tenant or shared agent template. Pure prefix-hash routing sends all of those requests to a single replica. In a four-node production incident, pure prefix routing raised the cache hit rate to **70 percent**. However, the first node received 3,600 requests while the second node received only 1,100 requests. That **3.27x load imbalance** left cluster throughput flat at **110 tokens/s** instead of the expected 140 tokens/s.

```text
Multi-Signal Cache- and Load-Aware Routing Formula (HLS Ch. 6 & 7; Volume 12 Ch. 9; ASP Ch. 17):
- Round-Robin 4-Node Skew Telemetry (Volume 12 Ch. 9):
  Per-node GPU utilization = [95%, 45%, 88%, 22%] (73% spread); KV cache usage = [91%, 32%, 85%, 18%] (73% spread)
  Unbounded Prefix Skew    = Node 0: 3,600 requests (280K tokens) vs Node 1: 1,100 requests (95K tokens) -> 3.27x ratio
- Signals tracked continuously per replica i by NVIDIA Dynamo KV Router / llm-d / SGLang Gateway:
  1. Prefix cache hit ratio:      hit_ratio_i = matched_cached_tokens / prompt_tokens
  2. KV cache memory utilization: kv_usage_i  = vllm:gpu_cache_usage_perc (target < 0.85)
  3. Waiting request queue depth: queue_i     = vllm:num_requests_waiting (target < 5)
  4. Active in-flight tokens:     running_i   = active prefill + decode token load
  5. Request SLO latency budget:  TTFT_slo, ITL_slo
- Bounded-Load Prefix Routing Rule:
  Select replica i maximizing prefix hit_ratio_i SUBJECT TO:
  (kv_usage_i < 0.85) AND (queue_i <= min_j(queue_j) * 1.5)
  If the prefix-owner replica exceeds the load bound, spill to the secondary warm replica or replicate the hot prefix.
```

### 5.2 Disaggregated Prefill-Decode Routing and NIXL / LMCache Handoff

At cluster scale, even bounded-load prefix routing cannot prevent a long prefill burst from stalling decode streams co-located on the same GPU. As introduced in *AI Systems Performance Engineering* and covered in depth in the companion disaggregation chapters, **Disaggregated Prefill and Decode** separates prefill workers and decode workers into independent GPU pools.
- **Independent Phase Optimization:** Prefill workers run compute-optimized parallelism at high batch sizes to minimize Time to First Token. Decode workers run memory-bandwidth-optimized parallelism with Wide Expert Parallelism and Data-Parallel Attention to guarantee low Inter-Token Latency. In the DistServe benchmark, disaggregating prefill and decode achieved up to **7.4x more goodput requests** within latency targets. It also satisfied **12.6x tighter latency SLOs**.
- **Zero-Copy KV Cache Transfer via NIXL and LMCache:** After a prefill worker computes the prompt's KV cache and first token, **NVIDIA NIXL** and **LMCache** transfer the KV blocks directly to the selected decode worker. They use device-to-device NVLink when co-located on the same node, or **GPUDirect RDMA** over InfiniBand NDR and ConnectX-8 SuperNICs across nodes. Overlapping layer-by-layer transfer with prefill compute keeps transfer latency overhead below one percent.
- **Kubernetes `llm-d` Variant Autoscaler:** On Kubernetes, the open-source `llm-d` architecture pairs a KV-aware gateway with a **Workload Variant Autoscaler**. That autoscaler dynamically shifts GPU replica counts between the prefill pool and the decode pool as prompt-to-output token ratios change.

Always pair prefix-aware routing with a hard queue and KV-cache load ceiling so a popular system prompt replicates across workers instead of saturating a single node.

---

## 6. How It Fails: Multi-Node Production Incidents and Runbooks

### 6.1 Failure Mode 1: Cross-Node `TP=16` NCCL Watchdog Timeout (`Meta-Llama-3-405B`)

- **Symptom:** An infrastructure team deploys `Meta-Llama-3-405B-Instruct-FP8` across two eight-GPU H100 nodes using `--tensor-parallel-size 16`. Pods stick in `Running` with zero HTTP responsiveness and saturated CPU usage on the Ray head node. Memory is allocated only on the first GPU while the remaining seven GPUs sit empty. After 30 seconds, the worker crashes.
- **Diagnosis & Evidence:** Inspecting `kubectl logs pod/vllm-node-2-worker-0 -c vllm-worker` with `NCCL_DEBUG=INFO` and running `nvidia-smi topo -m` reveals the root cause.

```text
2026-08-06T15:02:11.412Z [INFO] ncclCommInitRank: Initializing NCCL rank 8 of 16 across hosts node-1, node-2
2026-08-06T15:02:41.890Z [WARN] [NCCL WARN] Transport dev pcie3-0 is not NVLink capable. Falling back to Host TCP sockets.
2026-08-06T15:03:11.902Z [ERROR] [NCCL ERROR] Call to connect returned Connection refused (Socket: node-1:41235)
2026-08-06T15:03:11.905Z [CRITICAL] Watchdog caught timeout in NCCL collective operation AllReduce. Process terminating.
```

Setting sixteen-way Tensor Parallelism forced 160 synchronous AllReduces per token across two separate chassis lacking cross-node NVLink. NCCL fell back to host TCP sockets and tripped the 30-second watchdog timeout. Similarly, a 130B model with eight-way Tensor Parallelism across two four-GPU nodes deadlocks after 300 seconds.
- **Fix:** Restrict Tensor Parallelism strictly to the intra-node NVLink domain via `--tensor-parallel-size 8`. Use Pipeline Parallelism across nodes via `--pipeline-parallel-size 2`, and enable GPUDirect RDMA with `NCCL_IB_DISABLE=0` and `NCCL_NET_GDR_LEVEL=5`. Engine startup drops under **45 seconds**, and the 130B cluster starts in under 14 seconds with 88 percent less InfiniBand traffic.

### 6.2 Failure Mode 2: Pipeline Parallel Stage 0 KV Cache Starvation (`99.2%` vs `38.5%`)

- **Symptom:** A two-node cluster running four-way Tensor Parallelism and two-way Pipeline Parallelism suffers end-to-end request queue delays exceeding **4,500 ms** during peak hours. Meanwhile, the second node has over sixty percent of its VRAM free.
- **Diagnosis & Evidence:** Querying `vllm:gpu_cache_usage_perc{job="vllm-pp-cluster"}` in Prometheus shows the first stage pinned at **99.2%** while the second stage sits at **38.5%**, a `0.607` differential that exceeds the `0.40` imbalance threshold. When clients send massive 8,192-token prompts with short 64-token outputs, the first stage absorbs and holds un-chunked prefill PagedAttention blocks while the second stage processes short decode steps.
- **Fix:** Enable `--enable-chunked-prefill` and `--max-num-batched-tokens 2048` so the first stage streams prefill in bounded chunks. Alternatively, if the model fits inside an eight-GPU node like Llama-3-70B, switch from Pipeline Parallelism to two independent **Data Parallel replicas** with eight-way Tensor Parallelism. Switching to Data Parallel replicas balanced KV cache usage at **72 percent and 74 percent**, dropping queue delay to zero.

### 6.3 Failure Mode 3: Inter-Node GPUDirect RDMA Disabled (`45 ms` AllReduce Latency)

- **Symptom:** A four-node cluster exhibits tenfold higher collective latency than expected. The `nccl_all_reduce_latency_us` metric spikes to `45000` (45 ms) instead of staying under 5 ms. Interface counters on `eth0` also report `TX_DROPPED: 428, RX_ERRORS: 156`.
- **Diagnosis:** InfiniBand was disabled or GPUDirect RDMA was unconfigured. As a result, NCCL routed inter-node traffic over lossy host Ethernet sockets.
- **Fix:** Set `NCCL_IB_DISABLE=0` and `NCCL_NET_GDR_LEVEL=5`, and verify fabric health with `ibdiagnet -o /tmp/fabric.log`. Benchmark raw collective throughput across all four nodes using `./build/all_reduce_perf -b 1M -e 64M -f 2 -t 2 -G 4`.

### 6.4 Failure Mode 4: MoE AllToAll Hot-Expert Straggler (`99%` vs `60%` Utilization)

- **Symptom:** A multi-node Mixture-of-Experts deployment delivers forty percent lower token throughput than expected. Inspecting Nsight Systems traces shows `ncclAllToAll` barriers stretching across most of each layer step. One GPU runs at **99 percent utilization** while peer GPUs average **60 percent utilization**.
- **Diagnosis:** Domain-skewed user prompts are routing a disproportionate share of tokens to a single hot expert. Every other GPU stalls at the synchronous AllToAll combine barrier.
- **Fix:** Configure a capacity factor of 1.2 for a twenty percent overflow allowance. Enable DeepSeek **EPLB** hot-expert cloning onto redundant GPU slots alongside `--enable-two-batch-overlap`, and alert whenever per-expert utilization exceeds **80 percent**.

```yaml
groups:
  - name: vllm_multinode_distributed_alerts
    rules:
      - alert: NCCLCommunicationDegraded
        expr: rate(nccl_comm_latency_seconds_sum[2m]) / rate(nccl_comm_latency_seconds_count[2m]) > 0.005
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "NCCL Collective Communication Latency Spike (>5ms)"
      - alert: PipelineStageKVCacheImbalance
        expr: (max(vllm:gpu_cache_usage_perc) - min(vllm:gpu_cache_usage_perc)) > 0.40
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Severe KV Cache Imbalance Across Pipeline Stages (>40%)"
```

Always inspect `NCCL_DEBUG=INFO` transport selection and per-stage `vllm:gpu_cache_usage_perc` differentials first whenever multi-node serving throughput degrades.

---

## 7. Hands-On Verification Lab

### Lab Venue and Execution Scope
- **Local deterministic verification:** Run `python3 code/part15/multinode_inference_parallelism_lab.py` to execute the deterministic self-checks. The lab verifies Tensor versus Pipeline Parallelism collective math, DeepSeek-R1 Wide Expert Parallelism and GB200 NVL72 sizing, wave scheduling and EPLB load balancing, speculative decoding rejection sampling, and Kubernetes LeaderWorkerSet routing models.
- **Live GKE / multi-node H100 cluster (`untested here`):** The Kubernetes LeaderWorkerSet YAML, `ibdiagnet`, and multi-node `vllm serve` commands are production reference patterns. They have not been executed on live multi-node InfiniBand hardware in this local build environment.

```bash
python3 code/part15/multinode_inference_parallelism_lab.py
```

```text
=== Chapter 15.9 Lab: Multinode Inference Parallelism, Speculative Decoding & Routing ===
  [PASS] 1. 80-layer model (Llama-3-70B) with TP requires 2 AllReduces/layer = 160 AllReduces/token and 8,000 AllReduces/sec at 50 tok/s
  [PASS] 2. Ring AllReduce at TP=8 executes 2*(N-1) = 14 steps per collective (2,240 steps/token) and moves 2*(7/8)*16,384 = 28,672 B per AllReduce
  [PASS] 3. Intra-node TP=8 over NVLink 4 (900 GB/s, 0.8 us/collective) adds only ~0.13 ms comm per token (total ITL ~14.13 ms < 25 ms SLA)
  [PASS] 4. Cross-node TP=16 executes 2*(16-1)=30 ring steps/AllReduce (4,800 steps/token) and adds 80+ ms network stall per token (>85% comm overhead)
  [PASS] 5. Combining TP=4 with PP=8 shards inter-stage activation transfers by 1/TP (8,192 / 4 = 2,048 elements = 4,096 B per hop across 7 stage boundaries)
  [PASS] 6. NVLink 4 (900 GB/s) is 18x faster than 400G NDR IB (50 GB/s) and 72x faster than 100GbE (12.5 GB/s); L40S FP16 roofline knee is 419 FLOPS/B
  [PASS] 7. DeepSeek-V3/R1 (671B total, 37B active = 5.51% active) activates 1 shared + 8 of 256 routed experts (9 total, 3.12% routed density > 3% EP threshold)
  [PASS] 8. EP_SIZE = TP_SIZE * DP_SIZE: 8 GPUs hold 256/8 = 32 complete experts/GPU; 64 GPUs hold 4 experts/GPU; TP=1, DP=1 disables EP (EP_SIZE=1)
  [PASS] 9. TP=8, DP=1 uses AllReduce and duplicates MLA KV cache 8x across ranks, whereas DP=8, TP=1 (--enable-dp-attention) uses AllToAll and 1x KV cache
  [PASS] 10. Serving DeepSeek-R1 671B across 32 GPUs (TP=4, PP=8) places 83.875B (~84B) params/stage; ASP 64-GPU hybrid (PP=4, TP=2, EP=16) puts 15 layers/stage and 128 GPUs at DP=2
  [PASS] 11. GB200 NVL72 unifies 72 GPUs at 1.8 TB/s per GPU (130 TB/s rack aggregate, 13,824 GB HBM3e) and scales to 576 GPUs across 8 racks
  [PASS] 12. On 72-GPU NVL72, monolithic AllToAll launches 72*71 = 5,112 messages; 4 waves of 18 GPUs cut per-wave messages to 18*17 = 306 (16.71x reduction)
  [PASS] 13. MoE base capacity of 32 tokens scales to 32 (CF=1.0), 38 (CF=1.2, 20% overflow), and 48 (CF=1.5); load [50, 28, 30, 20] spills 12 overflow tokens at CF=1.2
  [PASS] 14. Hot expert GPU at 99% vs 60% peers (39% straggler gap) triggers the 80% utilization alert; EPLB cloning cuts peak expert load from 50 to 30 tokens
  [PASS] 15. Rejection sampling accepts with prob min(1, p/q): p=0.8, q=0.6 -> 1.0 (100%); p=0.4, q=0.6 -> 0.6667 (66.67%) while preserving target distribution
  [PASS] 16. For K=4 draft tokens and alpha=0.8, E[tokens] = (1 - 0.8^5)/(1 - 0.8) = 3.3616 tokens/pass; at c_draft=0.10, net speedup is 3.3616 / 1.4 = 2.40x
  [PASS] 17. When draft model is < 4x faster (c_draft=0.35) and alpha=0.6, cycle cost is 2.40 units vs 2.3056 expected tokens, degrading speedup to 0.96x (< 1.0x)
  [PASS] 18. Positional acceptance [0.8, 0.7, 0.6, 0.5, 0.10, 0.02] yields 2.864 tokens at K=4 vs 2.8811 tokens at K=6 (last 2 steps add only 0.0171 tokens)
  [PASS] 19. Medusa depth-2 binary tree (4 tokens/pass) cuts 100-token reply from 100 to 25 ideal passes; EAGLE-3 on Qwen3-32B reaches 56.5 vs 28.9 tok/s (1.96x)
  [PASS] 20. LeaderWorkerSet (replicas=2, size=2, 8 GPUs/pod) schedules 1 leader + 1 worker pod (16 GPUs) per replica and 32 GPUs total with gang semantics
  [PASS] 21. Naive round-robin across 4 DP nodes achieves 110 tok/s vs 240 tok/s ideal (45.83% efficiency) with 73% GPU util spread (95% vs 22%) and 73% KV spread (91% vs 18%)
  [PASS] 22. Unbounded prefix-hash routing creates a 3.27x load imbalance (Node 0: 3,600 requests vs Node 1: 1,100 requests)
  [PASS] 23. PP stage KV cache imbalance (Stage 0 = 99.2% vs Stage 1 = 38.5%, diff = 0.607 > 0.40) triggers PipelineStageKVCacheImbalance alert
  [PASS] 24. GPUDirect RDMA (NCCL_NET_GDR_LEVEL=5) cuts inter-node P2P latency by 4x to 6x; DistServe PD disaggregation delivers up to 7.4x goodput and 12.6x tighter SLOs
  [PASS] 25. Long-context sequence/pipeline parallelism on 1M-token prompts achieves 3.31x prefill throughput and up to 81% TTFT reduction

Summary: 25 passed, 0 failed
```

---

## Key takeaways

- **Keep Tensor Parallelism strictly inside the NVLink domain:** Tensor Parallelism executes two synchronous AllReduce operations per layer, or 160 AllReduces per token on an eighty-layer model. Crossing PCIe or Ethernet adds 50 to 200 milliseconds per token. Scale across nodes using Pipeline Parallelism, Expert Parallelism, or Data Parallel replicas over GPUDirect RDMA (`NCCL_NET_GDR_LEVEL=5`).
- **Use Data-Parallel Attention with Wide Expert Parallelism for MoE models:** On models like DeepSeek-R1 with 37B active parameters across 256 routed experts, pairing `--enable-dp-attention` with AllToAll routing avoids the eightfold Multi-Head Latent Attention KV cache duplication of Tensor Parallelism. That increases decode throughput by up to 1.9x.
- **Eliminate MoE network microbursts and hot-expert stragglers:** Split large NVL72 AllToAll collectives into staggered waves to cut instantaneous messages by 16.71x. Set a capacity factor of 1.2 and use DeepSeek EPLB to clone hot experts when utilization exceeds eighty percent.
- **Accelerate sequential decode with lossless speculative decoding:** Draft-verify rejection sampling preserves the exact target distribution while generating multiple tokens per target pass. Single-model methods like EAGLE-3, Medusa, and DeepSeek Multi-Token Prediction deliver 1.96x to 6.5x speedups without managing an external draft model.
- **Orchestrate multi-node shards with LeaderWorkerSet and bounded-load prefix routing:** Use Kubernetes `LeaderWorkerSet` for gang-scheduled, atomic multi-node pod groups. Combine prefix-cache affinity with a queue and KV-cache ceiling so popular prefixes achieve over 85 percent cache hits without creating a single-node hotspot.

---

## Exercises

1. **Tensor Parallelism vs Pipeline Parallelism Communication Math:**
   - **(a)** Consider an eighty-layer model with hidden dimension 8,192 running in BF16 at single-request batch size and single-token decode length. Calculate the number of AllReduce calls per token, the ring transfer steps per token at eight-way versus sixteen-way Tensor Parallelism, and the per-AllReduce byte volume per rank at eight-way Tensor Parallelism.
   - **(b)** Compare the per-token communication overhead of eight-way Tensor Parallelism over NVLink 4 at 900 GB/s against sixteen-way Tensor Parallelism across two nodes over 100GbE TCP at 12.5 GB/s. Then compute the per-hop byte volume when switching to four-way Tensor Parallelism and eight-way Pipeline Parallelism across 32 GPUs.
2. **DeepSeek-R1 Wide Expert Parallelism, NVL72, and EPLB:**
   - **(a)** DeepSeek-R1 has 671B total parameters, 37B active parameters per token, one shared expert, and 256 routed experts with top-eight gating. Calculate the active parameter percentage, routed expert activation density, and number of complete routed experts per GPU at eight-way versus 64-way Expert Parallelism on a GB200 NVL72 rack.
   - **(b)** On a 72-GPU NVL72 domain, compare the instantaneous message count of a monolithic AllToAll against four waves of 18 GPUs. Using the base capacity and four expert loads in the Section 2.4 table, calculate the per-expert cap at a 1.2 capacity factor, the overflow token count, and the peak expert load after EPLB clones the hottest expert.
3. **Speculative Decoding Rejection Sampling and Speedup Budgeting:**
   - **(a)** Using the Section 3.1 equation block, compute the exact acceptance probability when the draft model assigns 0.6 and the target model assigns 0.8 versus 0.4. Then compute expected tokens per pass and net wall-clock speedup for the fast draft model versus the slow draft model in Section 3.1.
   - **(b)** Using the six positional acceptance rates in the Section 3.1 equation block, compute expected tokens at depth four versus depth six. Explain why trimming the draft depth from six to four improves net throughput.
4. **Kubernetes LeaderWorkerSet, Prefix-Aware Routing, and PP Stage Triage:**
   - **(a)** Examine the `LeaderWorkerSet` manifest in Section 4.2 and determine how many leader pods, worker pods, and total GPUs are scheduled across the cluster. Then use the Section 5.1 routing block to compute the scaling efficiency under naive round-robin and the load skew ratio under unbounded prefix routing.
   - **(b)** In the Section 6.2 Pipeline Parallel incident where the first stage hits 99.2 percent KV cache usage and the second stage sits at 38.5 percent, compute the stage differential relative to the alert threshold and state the two architectural fixes.

---

## Checkpoint questions (20)

<details>
<summary>**Why does Tensor Parallelism require two synchronous AllReduce operations per Transformer layer, and how many AllReduces per second does an eighty-layer model execute?**</summary>

Each Transformer block contains two Row-Parallel linear layers: the attention output projection and the MLP down projection. Each Row-Parallel layer produces partial sums across ranks that must be summed via an AllReduce before the residual connection and layer norm. Across eighty layers, generating one token requires 160 AllReduces. At fifty tokens per second, that equals 8,000 AllReduce collectives every second.
</details>

<details>
<summary>**How many sequential ring transfer steps does a single AllReduce execute across N GPUs, and what happens to Inter-Token Latency if Tensor Parallelism crosses nodes over Ethernet?**</summary>

A ring AllReduce executes twice *N* minus one sequential steps, split evenly between ReduceScatter and AllGather. That equals 14 steps per collective across eight GPUs, or 2,240 steps per token, and 30 steps per collective across sixteen GPUs, or 4,800 steps per token. Over PCIe or Ethernet, 160 synchronous AllReduces add 50 to 200 milliseconds of communication stall per token or trigger a 30-second NCCL watchdog timeout.
</details>

<details>
<summary>**How does combining intra-node Tensor Parallelism with inter-node Pipeline Parallelism reduce the activation byte volume transferred across the inter-node network?**</summary>

Pipeline Parallelism communicates only once at each stage boundary across *P* minus one point-to-point hops per pass. When each node runs Tensor Parallelism internally, each GPU sends only its local activation shard of size `batch_size * seq_len * (hidden_size / TP)` to its same-rail peer on the next stage. For a hidden dimension of 8,192 and four-way Tensor Parallelism, each GPU sends 2,048 elements, or 4,096 bytes in BF16, per token.
</details>

<details>
<summary>**What is the difference between H100 PCIe, H100 NVL, H100 SXM, and H200 SXM for multi-GPU inference?**</summary>

- **H100 PCIe:** Provides 128 GB/s PCIe bandwidth without NVSwitch; suitable only for single-GPU Data Parallelism or Pipeline Parallelism.
- **H100 NVL:** Provides 94 GB HBM3 at 3.9 TB/s with a 600 GB/s two-GPU NVLink bridge; supports two-way Tensor Parallelism within a pair, while four GPUs still cross PCIe between pairs.
- **H100 SXM:** Provides 80 GB HBM3 at 3.35 TB/s with four NVSwitches delivering 900 GB/s all-to-all across all eight GPUs.
- **H200 SXM:** Keeps the 1,979 TFLOPS compute and 900 GB/s NVLink 4 of H100 SXM, but upgrades memory to 141 GB HBM3e at 4.8 TB/s so eight GPUs can hold DeepSeek-R1 in FP8.
</details>

<details>
<summary>**When should you enable Context Parallelism (Sequence / Helix Parallelism) during inference, and which latency metric does it improve?**</summary>

Enable Context Parallelism for ultra-long prompts of one hundred thousand to one million tokens that exceed single-GPU KV cache capacity or prefill latency budgets. It partitions the input sequence and KV cache across GPUs using ring or blocked attention. That cuts **Time to First Token** roughly in half per GPU doubling, achieving up to an 81 percent reduction in Time to First Token and 3.31x prefill throughput on million-token contexts.
</details>

<details>
<summary>**How many total and active parameters does DeepSeek-R1 have, and how does vLLM compute the Expert Parallel size and experts per GPU when `--enable-expert-parallel` is set?**</summary>

DeepSeek-V3 and DeepSeek-R1 have 671B total parameters and activate 37B parameters per token, or 5.51 percent of the model. Each token uses one shared expert and eight of 256 routed experts, giving nine active experts per token and a 3.125 percent routed activation density. In vLLM, `EP_SIZE = TP_SIZE * DP_SIZE`, and each GPU holds 32 complete routed experts when deployed across eight GPUs.
</details>

<details>
<summary>**Why is Data-Parallel Attention (`--enable-dp-attention`) preferred over Tensor Parallelism with Expert Parallelism for serving DeepSeek-R1 at high concurrency?**</summary>

DeepSeek-R1 uses Multi-Head Latent Attention, which compresses Key-Value heads into a single shared latent vector. Standard Tensor Parallelism cannot shard a single KV head and therefore duplicates the entire KV cache eightfold across an eight-GPU node. Data-Parallel Attention partitions requests across GPUs with zero KV cache duplication and uses AllToAll (`DeepEP`) to route tokens to experts, increasing decode throughput by up to 1.9x.
</details>

<details>
<summary>**What are the interconnect and memory specifications of an NVIDIA GB200 NVL72 rack, and why does it transform Wide Expert Parallelism?**</summary>

A GB200 NVL72 rack integrates 36 Grace CPUs and 72 Blackwell GPUs connected via NVSwitch 4 at 1.8 TB/s bidirectional NVLink 5 bandwidth per GPU. That provides 130 TB/s aggregate bandwidth across the rack and 13,824 GB of HBM3e memory, or 30 TB including Grace CPU RAM. Because all 72 GPUs share a single sub-microsecond NVLink domain, wide Expert Parallel AllToAll shuffles execute at intra-node speeds without touching slower inter-node NICs.
</details>

<details>
<summary>**How does wave scheduling reduce NVSwitch congestion during a rack-scale Mixture-of-Experts `AllToAll` exchange?**</summary>

A monolithic AllToAll across 72 GPUs launches 5,112 simultaneous point-to-point messages, causing switch buffer microbursts. Splitting the exchange into four staggered waves of 18 GPUs reduces the simultaneous intra-wave message count to 306, a 16.71x reduction in instantaneous burst traffic. It also allows communication of the current wave to overlap with expert computation of the previous wave.
</details>

<details>
<summary>**How do Mixture-of-Experts capacity factor, expert collocation, and DeepSeek EPLB prevent a single hot expert from stalling the cluster?**</summary>

If one GPU hits 99 percent utilization while peers sit at 60 percent, every GPU stalls at the synchronous AllToAll barrier. Setting a capacity factor of 1.2 caps each expert at twenty percent above mean load—38 tokens for a 32-token average—and spills excess tokens to fallback experts. Expert collocation places frequently co-activated experts on the same GPU, while DeepSeek EPLB clones persistently hot experts onto redundant GPU slots.
</details>

<details>
<summary>**How does speculative decoding verify draft tokens without changing the target model's output probability distribution?**</summary>

The target model evaluates all *K* drafted tokens in a single parallel forward pass and accepts each token with probability `min(1, p_target(x_i) / q_draft(x_i))`. At the first rejected token, all remaining draft tokens are discarded and a replacement token is sampled from the adjusted residual distribution. That rejection sampling rule mathematically recovers the exact target distribution with zero accuracy loss.
</details>

<details>
<summary>**What is the formula for expected tokens per verification pass and net speedup in speculative decoding, and why must the draft model be at least four times faster?**</summary>

For uniform acceptance rate *alpha* and draft depth *K*, expected tokens per pass equals `(1 - alpha^(K+1)) / (1 - alpha)`, and net speedup equals `E[tokens] / (1 + K * c_draft)`. For four draft tokens at 0.8 acceptance rate and 0.10 draft cost ratio, expected output is 3.3616 tokens and net speedup is 2.40x. When the draft model is too slow at a 0.35 cost ratio and 0.6 acceptance rate, cycle cost reaches 2.40 units against 2.3056 expected tokens, causing a 0.96x slowdown.
</details>

<details>
<summary>**How do Medusa, EAGLE, DeepSeek Multi-Token Prediction, and N-gram Lookahead differ architecturally?**</summary>

- **Medusa:** Attaches independent parallel heads to the top hidden state and verifies candidates with a tree attention mask for a 2.2x to 3.6x speedup.
- **EAGLE family:** Uses an autoregressive feature-level head in EAGLE for a 3.5x speedup, a dynamic draft tree in EAGLE-2 for 20 to 40 percent higher speed, or multi-layer feature fusion in EAGLE-3 for up to a 6.5x peak speedup and 1.96x on Qwen3-32B.
- **Multi-Token Prediction:** Trains sequential causal Transformer prediction heads natively inside DeepSeek-V3 and DeepSeek-R1.
- **N-gram / Lookahead:** Matches n-grams from the prompt cache (`method="ngram"`) or Jacobi windows with zero extra model weights, gaining 16 percent throughput at single-stream concurrency.
</details>

<details>
<summary>**Why does speculative decoding lose effectiveness or reduce throughput at high request concurrency?**</summary>

Speculative decoding trades extra compute FLOPs by verifying *K* plus one tokens per sequence to save HBM weight reads during memory-bound low-batch decoding. At high concurrency of 16 or more requests, standard continuous batching already saturates GPU Tensor Cores past the Roofline knee. Multiplying active tokens by *K* plus one therefore creates a compute bottleneck and increases Time to First Token.
</details>

<details>
<summary>**How does XGrammar accelerate constrained JSON decoding compared to naive token-level grammar filtering?**</summary>

Naive constrained decoding evaluates valid next tokens across a 128,000-token vocabulary in Python on the CPU at every decode step, adding milliseconds of latency. XGrammar precompiles JSON schemas and context-free grammars into compressed finite-state machines and precomputes valid token bitmasks. It overlaps mask generation on the CPU and applies the mask directly inside the GPU softmax kernel, keeping overhead in the low single-digit percent range.
</details>

<details>
<summary>**Why is Kubernetes `LeaderWorkerSet` used instead of a standard `Deployment` or `StatefulSet` for multi-node LLM inference?**</summary>

A multi-node sharded LLM requires one leader pod and *N* minus one worker pods scheduled together as an atomic unit. `LeaderWorkerSet` provides dual leader and worker pod templates, per-group headless DNS discovery via `LWS_LEADER_ADDRESS`, gang-scheduling integration with Kueue, KAI, and Volcano, and `RecreateGroupOnPodRestart` so the entire shard group restarts atomically if any node fails.
</details>

<details>
<summary>**What does `NCCL_NET_GDR_LEVEL=5` do during multi-node Pipeline or Expert Parallelism, and how much latency does it save?**</summary>

Setting `NCCL_NET_GDR_LEVEL=5` enables full GPUDirect RDMA across PCIe bridges so the InfiniBand NDR or RoCEv2 NIC transfers tensors directly between GPU HBM and the network wire. That path bypasses host CPU RAM copies and kernel context switches, cutting inter-node point-to-point latency by **4x to 6x** down to 1.5 to 3.0 microseconds.
</details>

<details>
<summary>**How does bounded-load prefix-aware routing avoid both the round-robin efficiency drop and the prefix-hotspot skew?**</summary>

Round-robin ignores prompt length and KV cache locality, causing a 73 percent utilization spread across nodes and delivering only 110 tokens/s out of 240 tokens/s across four nodes. Pure prefix hashing achieves over 85 percent cache hits and cuts Time to First Token by up to 90 percent, but sent 3,600 requests to the first node versus 1,100 to the second node. Bounded-load prefix routing sends requests to the prefix-owner replica only while its KV cache usage stays below 85 percent and its queue stays within 1.5x of the cluster minimum, spilling excess load to a secondary replica.
</details>

<details>
<summary>**What causes first-stage KV cache starvation in a Pipeline Parallel cluster, and how do you resolve it?**</summary>

When long 8,192-token prompts with short 64-token outputs arrive without chunked prefill, the first stage allocates and holds massive prefill KV blocks while the second stage processes lightweight decode steps. That causes queue delays above 4,500 ms. Resolve it by enabling `--enable-chunked-prefill` or switching to independent Data Parallel replicas, which balances KV cache usage at 72 percent and 74 percent.
</details>

<details>
<summary>**How do NIXL, LMCache, and Kubernetes `llm-d` work together in a disaggregated prefill-decode cluster?**</summary>

In a disaggregated cluster, DistServe achieves up to 7.4x higher goodput and 12.6x tighter SLOs. On Kubernetes, `llm-d` routes incoming prompts to prefill pods and uses a Variant Autoscaler to adjust prefill versus decode replica counts dynamically. Once prefill completes, LMCache and NIXL transfer the KV cache zero-copy over NVLink or GPUDirect RDMA to the decode pod with under one percent latency overhead.
</details>

---

## Sources and review notes

### Primary Sources (Read in Full and Cited)

| Source | What was read and used |
|---|---|
| *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chapters 1, 2, 15, 19) | Chapter 15 *Multinode Inference, Parallelism, Decoding, and Routing Optimizations*: Disaggregated prefill and decode (`DistServe` `7.4x` goodput and `12.6x` tighter SLOs, `ConnectX-8` `800 Gb/s` `1:1` NIC:GPU, `NIXL` + `LMCache`, Kubernetes `llm-d` variant autoscaler); Table 15-1 5D parallelism (`TP`, `PP`, `EP`, `DP`, `CP`), `GB200/GB300 NVL72` (`1.8 TB/s`/GPU, `130 TB/s` rack, `13,824 GB` HBM3e, `30 TB` total, `120–132 kW`, `576` GPUs across `8` racks, `3.4x` MLPerf Inference v5.0 and `2.6x` MLPerf Training v5.0 per-GPU throughput), `64`-GPU (`16 x 4`, `PP=4, TP=2, EP=16, DP=2`) hybrid MoE; speculative decoding (`>= 4x` draft speed, `1.5x–2.5x` two-model, `EAGLE-1` `3.5x`, `EAGLE-2` `+20%–40%`, `EAGLE-3` `1.4x` over EAGLE-2 and `6.5x` over baseline, `Medusa-1/2` `2.2x–3.6x` depth-2 binary tree `4` tokens cutting `100` tokens to `25` passes, self-speculative `~2x`, consistent decoding `~3x`); constrained decoding (`XGrammar` low single-digit percent overhead); and dynamic MoE routing (hierarchical `ncclAllToAll`, double-buffering, butterfly schedules, `72`-GPU -> `4 x 18` wave scheduling `5,112 -> 306` messages, expert collocation `5` & `7`, `FP8`/`NVFP4` activation compression, capacity factor `1.0` vs `1.2` [`20%` overflow] vs `1.5` on `32` tokens, `99%` vs `60%` hot-expert straggler, `EPLB`, and `80%` utilization alerting). |
| `nvidia-zero-to-hero/volume-12/chapter-09-scaling-multi-gpu-and-multi-node-inference.md` (plus `chapter-05-tensorrt-llm-and-llm-execution.md`, `chapter-08-kv-cache-memory-and-concurrency.md`, `chapter-12-volume-12-summary.md`) | Megatron-LM Column/Row-Parallel `TP` mechanics (`2` AllReduces/layer, `160` AllReduces/token for `80`-layer Llama-3-70B, `8,000` AllReduces/s at `50 tok/s`, `2 * (N-1)` ring steps, `2 * ((N-1)/N) * B * S * H * Bytes`); interconnect table (`NVLink 4` `900 GB/s` `< 1.0 us`, `NVLink 3` `600 GB/s` `< 1.5 us`, `PCIe Gen5` `64 GB/s` `5–10 us`, `InfiniBand NDR` `400 Gbps` / `50 GB/s` `1.5–3.0 us` with `NCCL_NET_GDR_LEVEL=5` `4x–6x` P2P latency reduction, `100GbE` `12.5 GB/s` `50–150 us` adding `50–200 ms`/token); prefix-aware routing (`> 85%` hit rate, up to `90%` TTFT reduction); Failure Scenario 1 (`405B` `TP=16` `30 s` timeout fixed to `TP=8, PP=2` `< 45 s`, and `130B` `TP=8` `300 s` deadlock fixed to `TP=4, PP=2` `< 14 s`, `-88%` IB traffic); Failure Scenario 2 (`TP=4, PP=2` Stage 0 `99.2%` vs Stage 1 `38.5%` KV cache starvation and `4,500 ms` queue delay fixed by `--enable-chunked-prefill` or `DP=2, TP=8` at `72%`/`74%`); and troubleshooting tables (`45,000 us` / `45 ms` AllReduce with `TX_DROPPED: 428, RX_ERRORS: 156`, `110` vs `240 tok/s` round-robin skew `95%, 45%, 88%, 22%` GPU / `91%, 32%, 85%, 18%` KV, and `3.27x` prefix skew `3,600` vs `1,100` requests). |
| *Hands-On LLM Serving and Optimization* (`hands-on-llm-serving-and-optimization`, Chapters 5, 6, 7) | Table 5-2/5-3/5-4 GPU interconnect & roofline specs (`H100 PCIe` `128 GB/s`, `H100 NVL` `94 GB` `3.9 TB/s` `600 GB/s` bridge, `H100 SXM` `80 GB` `3.35 TB/s` `900 GB/s` `$6.20/hr`, `H200 SXM` `141 GB` `4.8 TB/s` `1,979 TFLOPS` `$6.30/hr`, `A100 SXM` `80 GB` `1.935 TB/s` `312 TFLOPS` `$2.70/hr`, `L40S` `48 GB` `864 GB/s` `362 TFLOPS` `419 FLOPS/B` knee `$2.25/hr`, `A10` `24 GB` `0.6 TB/s` `125 TFLOPS`); Table 6-6 `DeepSeek-R1-671B` vs `DeepSeek-R1-Distill-Llama-70B` (`97.3%` vs `94.5%` MATH-500, `71.5%` vs `65.2%` GPQA, `65.9%` vs `57.5%` LiveCodeBench); Chapter 7 speculative decoding acceptance math (`0.8 / 0.6 -> 1.0`, `0.4 / 0.6 -> 66.7%`), positional decay `[0.8, 0.7, 0.6, 0.5, 0.10, 0.02]`, and `Qwen/Qwen3-32B` benchmarks (`28.9 tok/s` vanilla vs `+16%` `ngram` vs `56.5 tok/s` `eagle3` at `C=1` and `C=16` trade-offs). |
| *Generative AI on Kubernetes* (`generative-ai-on-kubernetes`, Chapters 3, 7) | Single-node vs multi-node Kubernetes inference (`4` GPUs `~3.5x` throughput intra-node), KubeRay vs Kubernetes `LeaderWorkerSet` (`LWS`) for multi-host sharded LLM inference, gang scheduling and topology-aware placement with Kueue `ResourceFlavor`, NVIDIA KAI Scheduler, and Volcano. |
| *Distributed AI Systems* (`distributed-ai-systems`, Chapters 6, 7, 11) | DeepSeek-V3/R1 `671B` (`37B` active, `256` routed experts, `$5.5M` on `2,048` H800s), vLLM `--enable-expert-parallel` (`EP_SIZE = TP_SIZE * DP_SIZE`, `32` experts/GPU on `8` GPUs, `> 3%` vs `< 1%` activation density, `TP=4, PP=8` across `32` GPUs with `84B`/stage and `8,192 / 4 = 2,048` activation shard), SGLang `--enable-dp-attention` (`1.9x` decode throughput, `DeepEP` + `DeepGEMM` + Two-Batch Overlap), and long-context pipeline parallelism (`3.31x` prefill throughput, `81%` TTFT reduction on `1M` tokens, `82.8%` scaling efficiency). |

### Inferences and Unverified Claims Note

| Note Type | Details |
|---|---|
| Live hardware execution note | Multi-node Kubernetes `LeaderWorkerSet`, InfiniBand `ibdiagnet` / `all_reduce_perf`, and multi-node `vllm serve` commands are production configurations from the cited sources and have not been executed on live multi-node GPU hardware in this local build environment (`untested here`). |
| Deterministic model verification | All collective step counts, bandwidth ratios, Wide EP / NVL72 sizing, wave-scheduled `AllToAll` counts (`5,112 -> 306`), capacity factor / EPLB calculations, speculative decoding expected-token and speedup curves (`3.3616` tokens, `2.40x` speedup, `56.5` vs `28.9 tok/s`), and `LWS` / routing skew metrics (`45.83%` efficiency, `3.27x` skew, `0.607` PP KV diff) are verified deterministically by `code/part15/multinode_inference_parallelism.py` and `code/part15/multinode_inference_parallelism_lab.py` (`25 passed, 0 failed`). |

