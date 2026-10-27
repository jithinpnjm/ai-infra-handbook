---
id: "c15-12"
title: "15.12 Dynamic and adaptive inference engine optimisations"
sidebar_label: "15.12 Dynamic and adaptive inference engine optimisations"
sidebar_position: 12
description: "Dynamic and adaptive inference engine optimizations: CUDA Graphs for decode batch padding buckets and time-series prewarming, TorchCompile and custom OpenAI Triton fused kernels for RMSNorm, RoPE, SwiGLU, and AllReduce, dynamic speculative decoding draft-length adaptation, early exit and layer skipping, adaptive parallelism and semantic model cascades, and test-time compute scaling budgets."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 15.12 Dynamic and adaptive inference engine optimisations

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE + Local Python Verification Lab |
| Part | Part 15: LLM inference and serving |
| Primary sources | *AI Systems Performance Engineering* Chapters 9, 12, 13, 14, 15, 16, 19; *Hands-On LLM Serving and Optimization* Chapters 4, 10; *AI Engineering* Chapter 9 |
| Cross-references | Chapter 10.18 (CUDA Graphs and device-initiated orchestration); Chapter 10.19 (OpenAI Triton and `torch.compile`); Chapter 10.20 (PyTorch profiling and CUDA Graph pools); Chapters 15.3–15.5 (vLLM, SGLang, TensorRT-LLM) |
| Code | `code/part15/dynamic_adaptive_inference.py`, `code/part15/dynamic_adaptive_inference_lab.py` |
| Coverage file | `planning/coverage/chapters/15-12.md` |
| Claim & number ledger | `planning/ledgers/15-12.md` |

## Why this matters for AI infrastructure

A static serving configuration works only when every user sends the exact same prompt length at a steady arrival rate. Real production traffic is never that predictable. One second your cluster faces a morning rush of short chat queries. A moment later, an autonomous coding agent submits a million-token repository prompt or spawns sixteen parallel reasoning branches.

When an inference engine relies on static settings across those shifting workloads, four expensive failures occur.
- **CPU dispatch stalls during decode.** Autoregressive decoding executes hundreds of tiny memory-bandwidth-bound kernels per token. Without static graph capture and fused operators, the GPU sits idle waiting for Python and the CUDA driver to launch each kernel.
- **Speculative decoding regressions.** A fixed draft length accelerates structured code generation where draft acceptance is high. That same fixed draft length slows the cluster down when creative prompts or large batch sizes cause draft rejections and compute bottlenecks.
- **Wasted depth and precision on trivial tokens.** Running all eighty layers of a frontier model in sixteen-bit precision just to emit a closing bracket or boilerplate phrase wastes memory bandwidth and Tensor Core cycles.
- **Misrouted queries and interconnect hotspots.** Sending a simple factual question to a seven-hundred-billion-parameter model wastes ten times the compute. Inside the rack, firing an uncoordinated all-to-all collective across seventy-two GPUs saturates switch buffers and spikes tail latency.

```text
Dynamic and Adaptive Optimization Reference Gains (ASP Chapters 9, 12, 13, 15, 16, 19; HLS Chapter 10; AIE Chapter 9):
- CUDA Graph capture: collapses 300 kernel launches into 100 and cuts microbenchmark latency from 1.00 ms to 0.75 ms (1.33x speedup).
- FireworksAI decreasing-batch graph pool ([8, 4, 2, 1] at 32 MB/batch unit): reuses a 256.0 MB high-water pool vs 480.0 MB isolated (46.67% saved).
- torch.compile on a 64-expert MoE model: reduces step time from 248.0 ms to 173.0 ms (75.0 ms or 30.24% saved, 1.43x speedup).
- Custom kernel fusion: fusedL2Norm cuts HBM traffic 3.0x (36 B -> 12 B); fused Add+RMSNorm, RoPE, and SwiGLU cut 80-layer launch overhead 3.0x (4.32 ms -> 1.44 ms).
- Speculative decoding: Chinchilla-70B (14.1 ms/tok) + 4B draft (1.8 ms/tok, c = 0.1277) at K = 5, alpha = 0.80 yields 3.6893 tokens in 23.1 ms (6.2614 ms/tok, 2.25x speedup); EAGLE-1/2/3 reaches 3.5x to 6.5x; Medusa reaches 1.9x on HGX H200 and 2.2x to 3.6x overall.
- Early exit, layer skipping, and token pruning: Early exit delivers 30% to 50% speedup; DASH skips 20% to 40% of layers; LazyLLM cuts long-context latency by 20% to 30%.
- Model cascading: routing 60% of queries to a 70B model (50 ms, 1x cost) before a 700B model (500 ms, 10x cost) cuts mean latency from 500 ms to 230.0 ms (260.0 ms with 10% fallback) and reduces compute cost by up to 5.0x.
- Test-time compute prefix sharing: PagedAttention/RadixAttention copy-on-write forks on Best-of-16 (4,096 prompt + 512 generated tokens) cut KV token slots from 73,728 to 12,288 (83.33% saved).
```

**An inference engine must continuously observe its own telemetry and adapt in real time.** It should dynamically adjust its graphs, kernels, draft depth, layer execution, routing, and test-time compute budgets. Before you tune any single knob in isolation, design a feedback loop that matches each runtime adaptation to live batch size, sequence length, model confidence, and fabric load.

## Prerequisites and outcomes

### Prerequisites
- Review CUDA Graph capture, stream-ordered memory pools, and device-initiated launches from Chapter 10.18.
- Review PyTorch compiler internals, OpenAI Triton kernels, and profiler workflows from Chapters 10.19 and 10.20.
- Review continuous batching, PagedAttention, RadixAttention, and TensorRT-LLM runtime architecture from Chapters 15.2 through 15.5.

### Outcomes
- Architect decode CUDA Graph pools across padded batch-size buckets using decreasing-batch shared memory handles, stream-ordered allocators, and time-series prewarming.
- Combine TorchCompile and TorchInductor with runtime kernel autotuning, occupancy-aware dynamic shared memory, and custom OpenAI Triton fused kernels for RMSNorm, RoPE, SwiGLU, and one-shot AllReduce.
- Model speculative decoding verification math across Draft-Target, EAGLE, Medusa, and self-speculative pipelines, and build an adaptive controller that adjusts draft length from live acceptance rates and batch sizes.
- Implement dynamic early-exit classifiers, input-aware layer skipping, Mixture of Depths token routing, LazyLLM token pruning, hysteretic FP8 and FP4 precision switching, and real-time quantized KV cache policies.
- Design traffic-driven parallelism pools, congestion-aware NVL72 collective wave schedules, endpoint-level semantic routers, tiered model cascades, test-time compute scaling budgets, and RL-based runtime tuners.

---

## 1. CUDA Graphs for Decode Batch Sizes, Padding Buckets, and Memory Pools

### 1.1 Eliminating Host Dispatch Overhead with Decode CUDA Graphs

During the prefill phase, a single matrix multiplication over thousands of prompt tokens keeps GPU Streaming Multiprocessors busy for tens of milliseconds. During the decode phase, each active request generates only a single token per step. Even with continuous batching across sixteen or thirty-two requests, individual decode kernels finish in just five to twenty microseconds.

In standard eager execution, Python and the CUDA driver require five to fifteen microseconds to validate tensor metadata and enqueue each kernel onto a hardware stream. When an eighty-layer Transformer executes over three hundred small kernels per decode step, the host CPU takes longer to launch the kernels than the GPU takes to execute them. The GPU timeline fragments into tiny bursts of work separated by wide idle gaps.

CUDA Graphs eliminate this host dispatch bottleneck by recording an entire decode forward pass into a static execution graph during engine startup. At serving time, vLLM, SGLang, and TensorRT-LLM replay the entire sequence of hundreds of GPU operations with a single `cudaGraphLaunch` call from the CPU. Capturing a repetitive workload reduces kernel launch transactions from three hundred down to one hundred and cuts step time from 1.00 ms to 0.75 ms.

```mermaid
flowchart LR
    subgraph Ingress["1. Continuous Batching Decode Step"]
        Active["Active Decode Batch<br/>B_actual = 19 requests"]
        Pad["Bucket Selector & Pad<br/>Pad +5 dummy tokens -> B_bucket = 24"]
        Active --> Pad
    end

    subgraph Pool["2. Prewarmed CUDA Graph Pool (Shared Handle)"]
        G256["Graph Bucket B = 256<br/>(Captured 1st: Sets 256 MB High-Water Pool)"]
        G64["Graph Bucket B = 64<br/>(Reuses Shared HBM Pool)"]
        G24["Graph Bucket B = 24<br/>(Selected: Single cudaGraphLaunch)"]
        G1["Graph Bucket B = 1<br/>(Reuses Shared HBM Pool)"]
    end

    subgraph Eager["3. Large-Batch Fallback"]
        Fallback["Eager / TorchInductor Path<br/>(When B_actual > 256)"]
    end

    Pad -->|"Lookup B = 24"| G24
    Active -.->|"If B_actual > 256"| Fallback
```

### 1.2 Decode Batch Padding Buckets and Decreasing-Batch Shared Memory Pools

A captured CUDA Graph hardcodes every kernel's grid dimensions, tensor shapes, and physical GPU memory pointers. If the number of active decode requests changes from sixteen on one step to nineteen on the next step, a single static graph cannot execute the new shape directly.

To support dynamic continuous batching without recapturing graphs on the fly, production serving engines pre-capture a discrete ladder of batch-size buckets. A typical vLLM or SGLang bucket ladder spans power-of-two and stepped sizes from 1 up to 256 or 512. Before launching a decode step, the engine copies the active input tokens into a persistent static input buffer. It then pads any unused slots up to the next bucket boundary with dummy tokens.

| Active Decode Batch (`B_actual`) | Selected Bucket (`B_bucket`) | Dummy Tokens Added | Padding Overhead (`%`) | Execution Path | Why Padding Still Wins |
|---|---|---|---|---|---|
| 1 | 1 | 0 | 0.00% | `CUDAGraph(B=1)` | Eliminates over 2 ms of Python dispatch overhead at minimum latency. |
| 6 | 8 | 2 | 25.00% | `CUDAGraph(B=8)` | Memory-bound GEMV reads the exact same weight bytes for 6 and 8 rows. |
| 19 | 24 | 5 | 20.83% | `CUDAGraph(B=24)` | Stepped bucket 24 vs 32 keeps dummy work under 21% while replaying one graph. |
| 52 | 64 | 12 | 18.75% | `CUDAGraph(B=64)` | Single `cudaGraphLaunch` hides host scheduling across all 80 layers. |
| 300 | 300 | 0 | 0.00% | Eager or Compiled | Above 256 requests, GEMMs are compute-bound and hide CPU launch overhead naturally. |

Padding a batch of nineteen requests up to twenty-four adds five dummy tokens, which is a 20.83% padding overhead. During memory-bandwidth-bound decoding, the GPU spends almost all of its time streaming model weights from HBM into registers rather than doing arithmetic. Computing twenty-four rows instead of nineteen against those already-loaded weights adds almost zero GPU execution time. Meanwhile, replaying the pre-captured graph saves milliseconds of CPU launch delay.

Storing dozens of pre-captured CUDA Graphs creates a second infrastructure hazard: HBM workspace exhaustion. By default, each captured graph reserves its own private memory pool for intermediate activations. If you capture four buckets of sizes 1, 2, 4, and 8 where each batch unit requires 32 MB of workspace, isolated pools consume 480 MB of HBM.

As detailed in *AI Systems Performance Engineering* Chapter 13, the FireworksAI engineering team solved this memory bloat by sharing a single `torch.cuda.graph_pool_handle()` across all buckets. They captured the graphs in **strictly decreasing batch-size order** from 8 down to 1. Because only one decode batch size ever executes at a given instant, the largest batch size of 8 allocates the 256 MB high-water mark first. Every smaller bucket reuses the exact same 256 MB memory addresses inside the shared pool, saving 46.67% of graph workspace memory.

### 1.3 Time-Series CUDA Graph Prewarming and Dynamic Allocator Switching

Even with a shared graph pool, cold-start initialization can violate tail-latency SLAs when a new replica scales up or traffic surges. *AI Systems Performance Engineering* Chapter 19 pairs cluster autoscaling with **Continuous Prewarming of CUDA Graphs and Caches** driven by time-series forecasting models such as ARIMA or Prophet.

```text
CUDA Graph Pool Sizing and Dynamic Allocator Mechanics (ASP Chapters 12, 13, 19):
1. Shared Pool Memory Savings:
   Isolated_Pool_MB = sum(B_i) * Unit_Workspace_MB = (8 + 4 + 2 + 1) * 32.0 MB = 480.0 MB
   Shared_Decreasing_Pool_MB = max(B_i) * Unit_Workspace_MB = 8 * 32.0 MB = 256.0 MB (Saves 224.0 MB = 46.67%)
2. Time-Series Prewarming Workflow:
   Forecast(RPS, Prompt_Length) via ARIMA/Prophet -> Trigger warm-up before 9:00 AM daily spike
   Execute dummy forward passes on low-priority CUDA streams -> Populate JIT SASS cache, KV pools, and CUDA Graph buckets
3. Dynamic Memory-Allocator Switching:
   - Slab Allocator: Pre-partitions fixed-size blocks (e.g., 64 KB per-token [layers, hidden_dim] activation buffers) for zero fragmentation.
   - PyTorch BFC Caching Allocator: Best-Fit with Coalescing; tuned via PYTORCH_ALLOC_CONF=max_split_size_mb:<val>.
   - Stream-Ordered Allocator (cudaMallocAsync): Driver-managed stream-ordered pools; activated on OOM retry in a clean child process via PYTORCH_ALLOC_CONF="backend:cudaMallocAsync".
```

When the time-series predictor forecasts a 9:00 AM traffic spike, a background scheduler runs synthetic warm-up requests across every expected batch bucket using low-priority CUDA streams. Low-priority streams yield hardware resources immediately if live user traffic arrives. On Grace Blackwell superchips, prewarming also stages unified CPU-GPU memory pages via `cudaMemPrefetchAsync` before the first request lands.

Long-running inference servers also suffer from HBM fragmentation when variable-length prompts alternate with small decode steps. PyTorch's default Best-Fit with Coalescing caching allocator reserves large chunks of HBM. Wide gaps between `torch.cuda.memory_reserved()` and `torch.cuda.memory_allocated()` indicate severe fragmentation. An adaptive engine separates long-lived model weights from short-lived 64 KB per-token activation slabs and tunes `max_split_size_mb`. Whenever fragmentation triggers an out-of-memory exception, the engine switches to CUDA's stream-ordered allocator via `PYTORCH_ALLOC_CONF=backend:cudaMallocAsync` in a fresh worker process.

Before you enable CUDA Graphs in production, capture your decode buckets in decreasing batch-size order inside a shared memory pool and warm every bucket on low-priority streams before opening the replica to live ingress traffic.

---

## 2. TorchCompile, TorchInductor, Kernel Autotuning, and Custom Triton Fused Kernels

### 2.1 The PyTorch Compilation Pipeline and Inference Modes

While CUDA Graphs remove CPU launch overhead, they do not change the efficiency of the GPU kernels inside the graph. If a model executes five separate elementwise PyTorch operations in a row, each operation still reads its inputs from HBM and writes its outputs back to HBM.

PyTorch's compiler stack via `torch.compile` eliminates those redundant memory round-trips through four lowering stages.
1. **TorchDynamo.** Intercepts Python frame evaluation via PEP 523, extracts FX graphs, and attaches SymPy symbolic shape guards to detect when dynamic sequence lengths require recompilation.
2. **AOTAutograd.** Captures joint forward-and-backward graphs and functionalizes in-place mutations into pure out-of-place operations.
3. **PrimTorch IR.** Decomposes more than two thousand ATen operators down into roughly two hundred fifty canonical primitive operations.
4. **TorchInductor.** Fuses sequences of pointwise and reduction primitives into single OpenAI Triton or C++ kernels, and coordinates cuBLASLt, CUTLASS, and CUDA Graph wrappers.

```text
PyTorch Compiler Modes and MoE Benchmark (ASP Chapters 13, 14, 19):
- default: Balances fast compile time with pointwise/reduction kernel fusion; no automatic CUDA Graphs.
- reduce-overhead: Wraps compiled subgraphs in CUDA Graphs to eliminate Python/driver launch overhead; ideal for small-batch decode.
- max-autotune: Profiles multiple Triton tile configs, cuBLASLt heuristics, and CUTLASS templates plus CUDA Graphs; longest warmup, highest steady-state speed.
- max-autotune-no-cudagraphs: Full kernel autotuning without CUDA Graph capture for workloads with highly dynamic tensor shapes.
- 64-Expert MoE Step Benchmark (ASP Ch. 13 Table 13-5): Eager mode = 248.0 ms -> torch.compile = 173.0 ms (75.0 ms / 30.24% saved, 1.43x speedup).
- Artifact Mega-Cache: Persist compiled binaries across fleet restarts via TORCHINDUCTOR_CACHE_DIR and torch.compiler.save_cache_artifacts().
```

On a sixty-four-expert Mixture-of-Experts model where routing and small operators create heavy launch and memory overhead, enabling `torch.compile` cuts step time from 248.0 ms to 173.0 ms, a 1.43x speedup. To prevent cold-start compilation storms when Kubernetes scales out new pods, mount a shared directory across nodes using `TORCHINDUCTOR_CACHE_DIR`. You can then serialize compiled artifacts with `torch.compiler.save_cache_artifacts()`.

### 2.2 Custom OpenAI Triton Fused Kernels for RMSNorm, RoPE, SwiGLU, and AllReduce

Compilers automatically fuse simple pointwise chains, but critical LLM blocks often require custom OpenAI Triton or CUDA kernels to keep intermediate values entirely inside on-chip SRAM and registers. As shown in *AI Systems Performance Engineering* Chapter 9, fusing an L2 normalization kernel (`fusedL2Norm`) reduces global memory traffic by 3.0x, from 36 bytes per element down to 12 bytes per element.

Modern inference engines apply that exact fusion principle to four core Transformer bottlenecks.
- **Fused Add and RMSNorm.** At the entry of every attention and MLP block, the model adds the residual stream and normalizes the activation vector. In unfused eager execution, PyTorch launches four separate kernels and performs five HBM passes over the hidden dimension. A single Triton kernel loads the input and residual once into SRAM, computes the updated residual, reduces the sum of squares in registers, and writes out the results in two or three HBM passes.
- **Fused Rotary Position Embedding.** Unfused RoPE slices query and key tensors, materializes temporary sine and cosine tables in HBM, and concatenates rotated halves. A fused Triton RoPE kernel loads query and key tiles alongside position indices and applies the pairwise rotation directly in registers before writing the rotated tensors in place.
- **Fused SwiGLU Activation.** In Llama and Qwen MLP layers, the gated projection multiplies the SiLU activation of the gate tensor by the up-projection tensor. Unfused execution requires five HBM passes over the 14,336-element intermediate dimension. A fused Triton SwiGLU kernel reads the gate and up tensors once, computes the product in registers, and writes the output once, cutting HBM traffic by 1.67x down to three passes.
- **Custom One-Shot and Two-Shot Fused AllReduce.** During Tensor Parallel decoding across eight GPUs, each layer performs an AllReduce on small activation buffers between 64 KB and 512 KB. Standard ring `ncclAllReduce` requires fourteen sequential link steps and cannot easily fuse with the following RMSNorm. Using PyTorch SymmetricMemory or NVSHMEM via `triton.nvshmem.get()`, a custom one-shot Triton kernel reads peer GPU buffers directly across NVSwitch in a single hop. It fuses the cross-GPU sum with the residual addition and RMSNorm inside one CUDA Graph-capturable kernel.

| LLM Decode Operator Block (80 Layers, B=32, H=4096, I=14336) | Unfused Eager Kernels / Layer | Fused Triton Kernels / Layer | HBM Tensor Passes (Unfused vs Fused) | 80-Layer Launch Overhead (6 us/launch) | Key Hardware Mechanism |
|---|---|---|---|---|---|
| Residual Add + RMSNorm | 4 | 1 | 5 passes vs 2–3 passes | 1.92 ms vs 0.48 ms | On-chip SRAM warp reduction (`tl.sum`) |
| Rotary Position Embedding (RoPE) | 3 | 1 | 4 passes vs 2 passes | 1.44 ms vs 0.48 ms | In-register pairwise sinusoidal rotation |
| Gated MLP Activation (SwiGLU) | 2 | 1 | 5 passes vs 3 passes (1.67x less BW) | 0.96 ms vs 0.48 ms | Single-pass gate sigmoid multiplication |
| TP Decode Synchronization (AllReduce) | 1 (Ring 14 steps) | 1 (Fused w/ Norm) | Separate collective + norm | Host sync gap vs Graph-captured | SymmetricMemory or NVSHMEM 1-shot P2P |
| **Total per Decode Step (80 Layers)** | **720 elemental launches** | **240 fused launches** | **Up to 2.0x–3.0x lower HBM traffic** | **4.32 ms vs 1.44 ms (3.0x faster)** | **Fused SRAM + CUDA Graph capture** |

### 2.3 Runtime Kernel Autotuning, Occupancy-Aware Shared Memory, and Hot-Swapping

Even a fused kernel cannot use a single static tile size across every request length. In self-attention, a large shared-memory tile of 256 by 128 maximizes data reuse for long prompts by loading Key and Value blocks once from HBM. However, its 128 KB shared-memory footprint restricts the Streaming Multiprocessor to 60% occupancy. For short sequences under 256 tokens, a smaller tile of 64 by 64 or a standard global-memory attention kernel avoids tiling setup overhead and reaches 85% SM occupancy.

| Attention Tile Size (TILE_Q x TILE_K) | Shared Memory per Block (KB) | Achieved SM Occupancy (%) | Achieved Throughput (GOPS) | Optimal Workload Regime (ASP Table 19-3) |
|---|---|---|---|---|
| 64 x 64 | 48 KB | 85% | 8.2 GOPS | Short sequences (L ≤ 512), latency-critical small batches |
| 128 x 64 | 64 KB | 78% | 10.5 GOPS | Medium sequences (512 < L ≤ 2,048), balanced reuse and occupancy |
| 128 x 128 | 96 KB | 72% | 9.8 GOPS | High register and SMEM footprint transition zone |
| 256 x 128 | 128 KB | 60% | 11.3 GOPS | Long context prefill (L ≥ 2,048), maximum HBM bandwidth reuse |

As shown in *AI Systems Performance Engineering* Chapter 19, an adaptive engine automates this selection through a six-step runtime loop. The engine measures batch size and sequence length, selects candidate kernels, microbenchmarks them on a background stream, picks the fastest variant, caches the winner by shape signature, and executes. Before launching a tiled attention kernel with tile width T, the runtime computes dynamic shared memory to hold the Query, Key, and Value tiles, and queries `cudaOccupancyMaxActiveBlocksPerMultiprocessor`.

```python
# Occupancy-aware dynamic shared-memory allocation and hot-swapping (ASP Ch. 19)
import torch

def compute_adaptive_attention_launch(seq_len: int, achieved_occ: float, gpu_util: float) -> dict:
    # 1. Dispatch kernel path based on sequence length breakeven (L = 256)
    kernel_name = "standard_attention_kernel" if seq_len < 256 else "tiled_attention_kernel"
    tile_t = 64 if seq_len <= 512 else (128 if seq_len <= 2048 else 256)

    # 2. Halve tile width T if SM occupancy drops below 50% threshold
    if achieved_occ < 0.50:
        tile_t = max(32, tile_t // 2)

    # 3. 3 tiles of T x T float32 elements for Q, K, and V in extern __shared__ float smem[]
    shared_mem_bytes = 3 * tile_t * tile_t * 4
    return {
        "kernel": kernel_name,
        "tile_t": tile_t,
        "shared_mem_bytes": shared_mem_bytes,
        "carveout_hint_smem_pct": 75,  # cudaFuncAttributePreferredSharedMemoryCarveout (75% SMEM / 25% L1)
        "run_prefill_chunk": gpu_util < 0.85,
    }

def hot_swap_compiled_attention(model: torch.nn.Module) -> None:
    # Zero-downtime JIT kernel hot-patching without reloading model weights
    compiled_fn = torch.compile(model.transformer.self_attn.forward, backend="inductor")
    model.transformer.self_attn.forward = compiled_fn
```

When a kernel requires large tiles of 128 or 256, the engine calls `cudaFuncSetAttribute` with `cudaFuncAttributePreferredSharedMemoryCarveout`. That hint shifts the unified L1 and shared-memory pool from a 50% split to 75% shared memory and 25% L1 cache. If a faster kernel implementation such as FlashAttention-3 or a newly compiled TorchInductor graph becomes available, the server drains in-flight requests at an iteration barrier. It then hot-swaps the module's forward function pointer in place without reloading multi-hundred-gigabyte model weights.

Before you write custom CUDA C++ from scratch, compile your model with `torch.compile`, fuse residual RMSNorm, RoPE, and SwiGLU in OpenAI Triton, and drive tile sizes from live SM occupancy telemetry.

---

## 3. Dynamic Speculative Decoding and Draft-Length Adaptation

### 3.1 The Mathematics of Speculative Verification

Autoregressive decoding is bottlenecked by memory bandwidth because reading 140 GB of FP16 weights for a 70B model to produce a single token leaves the GPU's Tensor Cores mostly idle. Speculative decoding exploits those idle FLOPs by turning sequential token generation into parallel token verification.

In a two-model speculative pipeline, a small draft model sequentially proposes K candidate tokens. Next, the large target model executes a single forward pass over all K draft tokens in parallel. Verifying K + 1 tokens in one pass reads the target model's weights from HBM only once. Therefore, the target verification step takes nearly the same wall-clock time as generating a single token, provided the total batch tokens remain below the GPU's Roofline ridge point.

```text
Speculative Decoding Verification Equations and Benchmarks (ASP Ch. 15; AIE Ch. 9):
1. Expected Tokens Generated per Verification Cycle (under token acceptance probability alpha in [0, 1)):
   E[N_tokens] = (1 - alpha^(K + 1)) / (1 - alpha)     (and E[N_tokens] = K + 1 when alpha = 1.0)
2. Verification Cycle Latency and Net Speedup (with draft-to-target cost ratio c = t_draft / t_target):
   T_cycle = K * t_draft + t_verify
   Effective_ITL = T_cycle / E[N_tokens]
   Speedup S(K, alpha, c) = (t_target * E[N_tokens]) / (K * t_draft + t_verify) = E[N_tokens] / (1 + K * c)
3. Concrete Benchmark — Chinchilla-70B Target + 4B Draft (AIE Ch. 9):
   t_target = 14.1 ms/token, t_draft = 1.8 ms/token -> Draft is 7.83x (~8x) faster (c = 1.8 / 14.1 = 0.1277)
   At K = 5 and alpha = 0.80:
   E[N_tokens] = (1 - 0.80^6) / (1 - 0.80) = (1 - 0.262144) / 0.20 = 3.6893 tokens/cycle
   T_cycle = 5 * 1.8 ms + 14.1 ms = 23.1 ms -> Effective_ITL = 23.1 / 3.6893 = 6.2614 ms/token (2.25x speedup)
```

Under standard speculative rejection sampling, the target model compares its exact probability distribution against the draft model's probabilities from left to right. It accepts the longest valid prefix of j draft tokens and always samples one additional bonus token or corrected token from the target distribution at position j + 1. Consequently, every verification cycle guarantees at least 1 valid token and produces up to K + 1 tokens while preserving the exact output distribution of the target model.

### 3.2 Speculative Architecture Variants: Draft-Target, EAGLE, Medusa, and Self-Speculative

Running two separate models in HBM introduces deployment complexity. Both models must share the exact same tokenizer and vocabulary, and the engine must allocate separate KV cache pools for both the draft and target models. Four architectural families address this trade-off across modern serving engines.

| Speculative Paradigm | Architectural Mechanism | Extra VRAM Overhead | Target Distribution Preserved? | Reported Speedup (ASP Ch. 15 & AIE Ch. 9) |
|---|---|---|---|---|
| **Two-Model Draft-Target** | Distilled or smaller draft LLM (4x–10x faster, e.g., 4B for 70B) proposes K tokens; target verifies in one pass | Draft weights + draft KV cache | Yes, exact lossless sampling | 1.5x–2.5x (2.25x on Chinchilla-70B) |
| **EAGLE-1 / EAGLE-2 / EAGLE-3** | Lightweight autoregressive head extrapolates target hidden features; EAGLE-2 adds dynamic draft trees; EAGLE-3 fuses multi-layer features | Under 2%–5% (1 transformer layer head) | Yes, exact lossless sampling | 3.5x (EAGLE-1), +20%–40% (EAGLE-2), up to 6.5x (EAGLE-3) |
| **Medusa (Medusa-1 / Medusa-2)** | Attaches multiple parallel decoding heads to frozen target model; verifies candidates in a depth-2 binary tree (4 tokens/pass) | Small head parameters only | Yes, with tree-attention verification | 1.9x on HGX H200 (Llama 3.1), 2.2x–3.6x overall |
| **Self-Speculative & Prompt Lookup** | Target model drafts by skipping 50% of its own layers or copying input spans via Inference with Reference | 0 GB extra model weights | Yes, verified by full target pass | ~2.0x (~3.0x consistent decoding) |

As covered in *AI Systems Performance Engineering* Chapter 15, **EAGLE** eliminates the separate draft model by attaching a tiny draft module that predicts future tokens directly from the target model's internal feature representations. EAGLE-1 achieves up to 3.5x speedup on a 4-token draft. EAGLE-2 replaces the single chain with a context-aware dynamic draft tree and runs 20% to 40% faster than EAGLE-1. EAGLE-3 fuses lower, middle, and upper layer features to predict draft tokens directly, achieving 1.4x over EAGLE-2 and up to 6.5x over unoptimized baselines.

**Medusa** attaches multiple independent decoding heads to the top of the LLM, where the k-th head predicts k + 1 positions ahead. Using a tree-based attention mask, a depth-2 binary tree evaluates four token candidates in a single forward pass. That tree verification compresses a 100-token reply into 25 passes and boosts Llama 3.1 throughput by up to 1.9x on HGX H200 GPUs. Finally, **SpeCache** in *AI Systems Performance Engineering* Chapter 19 combines speculative decoding with asynchronous KV prefetching. While decoding the current token and a speculative lookahead token in parallel, a background CUDA stream prefetches the most relevant sixteen-bit KV cache pages from CPU memory into HBM. Using `OffloadedCache` chunks ahead of the next verification step incurs only a five to ten percent throughput penalty.

### 3.3 Dynamic Draft-Length Adaptation Under Varying Acceptance and Batch Load

A static draft length K is a dangerous production anti-pattern. Suppose an engineer configures a fixed draft length of 8 on the Chinchilla-70B setup where the draft takes 1.8 ms and the target takes 14.1 ms. When a user asks the model to refactor Python code or emit JSON, the draft model easily predicts boilerplate syntax with an acceptance rate of 0.85, generating 4.86 tokens per cycle for a 2.41x speedup.

Moments later, another user submits an open-ended creative writing prompt with high temperature, causing the draft acceptance rate to plummet to 0.30. At a draft length of 8 and an acceptance rate of 0.30, the expected output drops to 1.4285 tokens per cycle while the cycle latency balloons to 28.5 ms. The effective inter-token latency degrades to **19.96 ms per token, a 0.71x slowdown** that makes speculative decoding 41.5% slower than running the 70B model alone.

```mermaid
flowchart TB
    Step["Decode Step Telemetry<br/>Accepted Tokens j, Active Batch B"] --> EMA["Update Acceptance EMA<br/>alpha_ema = 0.8 * alpha_ema + 0.2 * (j / K)"]
    EMA --> CheckB{"Active Batch B >= B_cutoff<br/>(e.g., B >= 32)?"}
    CheckB -->|"Yes: Compute-Bound"| Disable["Disable Speculation (K = 0)<br/>Run Standard Continuous Batching"]
    CheckB -->|"No: Memory-Bound"| Sweep["Evaluate S(K, alpha_ema, B)<br/>for K in {0, 1, 2, 4, 6, 8}"]
    Sweep --> HighA{"Optimal K* Result"}
    HighA -->|"alpha_ema >= 0.80"| Expand["Expand Draft Depth (K = 5..8)<br/>Code / JSON / RAG Spans"]
    HighA -->|"0.45 <= alpha_ema < 0.80"| Mod["Moderate Draft Depth (K = 2..4)<br/>Standard Conversational Text"]
    HighA -->|"alpha_ema < 0.45"| Shrink["Shrink or Bypass (K = 0..1)<br/>High-Entropy Creative Generation"]
```

A second failure occurs when request concurrency spikes. Speculative verification is only free when the target model is memory-bandwidth-bound. If active batch size reaches 32 and each request verifies 6 tokens, the target forward pass processes 192 tokens per step. That token volume crosses the GPU's Roofline ridge point of roughly 295 FLOPs per byte on H100, making verification compute-bound and multiplying target step latency.

| Workload Scenario | Live Acceptance Rate (`alpha_ema`) | Active Batch Size (B) | Static K = 8 Speedup | Adaptive K* Selected | Adaptive Speedup (S) | Runtime Action Taken |
|---|---|---|---|---|---|---|
| Structured Code or JSON | 0.85 | 2 | 2.34x (6.03 ms/tok) | K* = 6 | 2.36x (5.98 ms/tok) | Expands K to harvest high draft accuracy |
| Standard Q&A Chat | 0.70 | 4 | 1.49x (9.44 ms/tok) | K* = 4 | 1.69x (8.35 ms/tok) | Caps K at 4 to avoid diminishing tail probabilities |
| High-Entropy Creative | 0.30 | 2 | **0.71x (19.96 ms/tok SLOWDOWN)** | K* = 1 or 0 | **1.01x (13.96 ms/tok)** | Shrinks K immediately to prevent draft waste |
| High-Concurrency Surge | 0.80 | 32 | 0.58x (Compute-bound stall) | K* = 0 | 1.00x (Full batch throughput) | Disables speculation when B reaches 32 |

To prevent both failure modes, adaptive inference engines track an exponential moving average of the acceptance rate and evaluate expected speedup at every iteration. Whenever the active batch size exceeds the compute-bound cutoff of 32 or the acceptance rate drops below the breakeven threshold, the scheduler automatically throttles the draft length down to 1 or 0.

Never deploy speculative decoding with a hard-coded draft length in multi-tenant production; always couple draft depth to an online acceptance-rate EMA and a maximum batch-size cutoff.

---

## 4. Early Exit, Layer Skipping, Mixture of Depths, and Dynamic Precision Scaling

### 4.1 Dynamic Early-Exit Networks, DASH Layer Skipping, Mixture of Depths, and LazyLLM

Standard Transformer inference executes every layer for every token, spending the exact same compute on a predictable punctuation mark as on a complex mathematical deduction. Adaptive depth and token-pruning architectures break that rigid allocation along four axes.
- **Dynamic Early-Exit Networks.** Attach lightweight auxiliary classifier heads at intermediate layers. At each exit point, the engine computes the Shannon entropy or top-2 logit margin of the intermediate vocabulary distribution. When confidence exceeds a calibrated threshold, such as exiting at layer 48 of an 80-layer model to save 40.0% of layer executions for a 1.67x layer-count reduction, the token emits immediately. As noted in *AI Systems Performance Engineering* Chapter 19, dynamic early-exit networks deliver **30% to 50% inference speedup** on reasoning tasks without accuracy loss. To keep subsequent tokens valid, the runtime either copies the last computed hidden state into the upper-layer KV cache slots or restricts attention of later tokens to the exited layer depth.
- **Input-Aware Layer Skipping.** Frameworks such as DASH formulate per-token layer execution as a Markov Decision Process. A tiny learned scoring network inspects the incoming activation vector at each layer and decides dynamically whether to execute the Transformer block or bypass it via the residual connection. DASH skips **20% to 40% of layers** across typical NLP benchmarks while preserving task accuracy.
- **Mixture of Depths.** While per-token early exit and MDP skipping vary the number of tokens executing at each layer, Mixture of Depths enforces a fixed per-layer token capacity factor such as 0.25 or 0.50. A lightweight router scores all tokens in the sequence and routes only the top 25.0% fraction through self-attention and the MLP, while the remaining 75.0% of tokens bypass the block along the residual stream. Because the routed token count is known statically for every batch size, Mixture of Depths achieves massive FLOP reductions while preserving static tensor shapes for CUDA Graph capture.
- **Dynamic Token Pruning with LazyLLM.** Long-context prompts contain thousands of stopwords and filler tokens that contribute almost nothing to the final answer. LazyLLM in *AI Systems Performance Engineering* Chapter 19 uses a lightweight attention-importance scoring function to selectively compute and retain KV cache entries only for high-impact tokens. Pruning low-impact tokens out of both prefill and decode achieves a **20% to 30% end-to-end latency reduction** on long-context workloads.

| Adaptive Computation Technique | Granularity of Adaptation | CUDA Graph Compatibility | Reported Speedup or Reduction (ASP Ch. 19) | Key Operational Consideration |
|---|---|---|---|---|
| **Dynamic Early-Exit Networks** | Per-token truncation at intermediate layer | Requires state-copy or batch grouping | 30%–50% inference speedup | Must populate or mask upper-layer KV cache slots for future tokens |
| **Input-Aware Layer Skipping (DASH)** | Per-token, per-layer MDP gating | Dynamic shape per layer unless bucketed | Skips 20%–40% of layers | Requires trained gating network per layer |
| **Mixture of Depths (MoD)** | Top-k token routing per layer (capacity 0.25–0.50) | **100% static shapes** (k fixed per batch) | Bypasses 50%–75% of layer tokens | Router top-k gather and scatter overhead must be fused |
| **Dynamic Token Pruning (LazyLLM)** | Selective KV computation and token pruning | Compatible with paged block tables | 20%–30% long-context latency reduction | Must calibrate pruning threshold to preserve needle-in-a-haystack recall |

### 4.2 Hysteretic Token-Level Precision Scaling and Real-Time KV Cache Compression

Modern Hopper and Blackwell GPUs provide hardware Tensor Cores for 16-bit, 8-bit, and 4-bit arithmetic. Because PyTorch's native `torch.autocast` only manages FP16 and BF16, production engines use NVIDIA Transformer Engine via `fp8_autocast` and `DelayedScaling` with `Format.HYBRID`, `amax_history_len=1024`, and `amax_compute_algo="max"` to switch layer and token precision at runtime.

| Precision Configuration (ASP Table 19-2) | Relative Memory Usage | Relative Compute Throughput | Typical Quality Impact (Accuracy Delta) | Recommended Runtime Role |
|---|---|---|---|---|
| FP16 or BF16 (Baseline) | 1.00x (100%) | 1.0x (Baseline) | 0.0% (Full fidelity) | High-entropy reasoning tokens and sensitive early input layers |
| FP16 Weights + FP8 Activations | ~0.50x (50%) | ~1.5x (Up to 2.0x compute-bound) | Negligible (< 0.1%) | Default steady-state precision (MXFP8 on Blackwell) |
| INT4 Weights + FP8 Activations (W4A8) | ~0.25x (25%) | ~1.8x (Mixed compute and memory) | ~0.5% drop | Memory-bandwidth-bound decode at moderate concurrency |
| INT4 Weights + FP4 Activations (W4A4) | ~0.20x (20%) | ~3.5x (Peak 4.0x theoretical) | ~1.0% drop | High-confidence continuations and extreme memory pressure |

In *AI Systems Performance Engineering* Chapter 19, `decode_with_dynamic_precision` adjusts numerical precision at the token level without stalling the GPU on per-step host synchronizations.
1. **On-device confidence EMA.** At every decode step, the GPU computes the top-2 logit margin and updates an on-device exponential moving average with smoothing factor 0.2.
2. **Interval host re-evaluation.** Synchronizing a float scalar to the host on every token would stall the GPU pipeline on every step. Instead, the host inspects the smoothed confidence only once every 8 steps.
3. **Hysteresis band.** To prevent rapid precision flapping, the loop uses separate entry and exit thresholds of 6.0 and 3.0. The engine upgrades from BF16 to FP8 only when confidence exceeds 6.0, and stays in FP8 until confidence drops below 3.0.

Similarly, when long reasoning chains push GPU memory utilization toward exhaustion, `generate_with_dynamic_quantized_cache` switches the Hugging Face `QuantizedCache` using the HQQ backend (`q_group_size=64` and `residual_length=128`) from 8-bit down to 4-bit across 32-token generation chunks. That transition triggers whenever the smoothed `torch.cuda.mem_get_info()` used ratio reaches 0.90, following an initial 80% high-watermark alert for 8-bit compression.

Always guard dynamic precision and KV cache compression switches with EMA smoothing, interval re-evaluation, and hysteresis bands so the engine never thrashes between modes on adjacent tokens.

---

## 5. Adaptive Parallelism, Congestion-Aware Scheduling, and Semantic Model Cascades

### 5.1 Traffic-Driven Adaptive Parallelism Switching and NVL72 Congestion Scheduling

Fixing a single sharding strategy at container boot forces a painful compromise between short-prompt latency and long-context memory capacity. As summarized in *AI Systems Performance Engineering* Table 19-1, an adaptive serving platform pre-provisions logical worker pools with distinct parallelism layouts. The router then dispatches each request to the pool that matches its sequence length and concurrency profile.

| Inference Traffic Pattern (ASP Table 19-1) | Recommended Parallelism Strategy | Architectural Rationale |
|---|---|---|
| Many short requests (< 256 tokens, high RPS) | Data Parallel (DP) / Replica Scaling | Zero inter-GPU collective overhead; each replica serves independent requests |
| Few long requests (≥ 8K tokens, low concurrency) | Pipeline Parallelism (PP with microbatches) | Splits layers across GPUs and pipelines microbatches to hold large KV states |
| Mixed load (short interactive + long context) | Hybrid Dynamic (TP pool + TP + PP pool) | Routes short chats to TP-only replicas and long contexts (> 4,096 tokens) to TP + PP |
| Extremely large dense model (> 1 GPU HBM) | Tensor + Pipeline Hybrid (TP + PP) | Balances intra-layer matrix splits (TP) with inter-node stage splits (PP) |
| Sparse MoE inference (DeepSeek-R1 680B / 37B active) | Expert Parallelism (EP + TP / DP) | Distributes 256 total experts across GPUs while activating only 9 (1 shared + 8 routed) per token |

Consider serving DeepSeek-R1 on an eight-GPU Blackwell B200 server with 1,440 GB of total HBM. DeepSeek-R1 has 680B total parameters and activates 37B parameters per token across 256 total experts and 9 active experts. Under normal chat traffic with sequence lengths up to 4,096 tokens and memory utilization up to 0.80, the router dispatches requests to a four-way Tensor Parallel pool to avoid pipeline bubbles. When a request arrives with an ultra-long context over 4,096 tokens or over 1,000,000 tokens, or when GPU memory utilization exceeds 0.80, `choose_worker_pool` routes the job to a two-stage hybrid pool. In that hybrid pool, each four-GPU pipeline stage provides 720 GB of HBM, preventing out-of-memory crashes without resharding weights in place.

```text
Rack-Scale Interconnect and Congestion-Aware Scheduling Numbers (ASP Chapter 19):
- GB200 NVL72 (72 x B200 @ 180 GB = 12,960 GB HBM) & GB300 NVL72 (72 x B300 @ 288 GB = 20,736 GB HBM):
  18 NVLink 5 ports/GPU * 100 GB/s bidirectional/port = 1.8 TB/s per GPU (3.6 TB/s per superchip; > 130 TB/s NVSwitch rack bisection).
- Hop Latency: < 1 us inside NVSwitch domain vs 5–10 us per hop across inter-rack NDR InfiniBand.
- NVTAGS (NVIDIA Topology-Aware GPU Selection): Remaps high-traffic pipeline/expert pairs onto local switches, converting a 50 GB/s cross-node bottleneck into two 25 GB/s intra-node transfers (50% network latency reduction).
- NCCL Ring vs Tree on 72 GPUs: Ring AllReduce requires 71 (= 72 - 1) sequential hops; forcing NCCL_ALGO=Tree reduces latency to 6 (~log2(72)) steps.
- Collective Wave Scheduling: A monolithic 72-GPU all-to-all fires 72 * 71 = 5,112 simultaneous messages (71 senders flooding GPU 0's 18 NVLink ports). Splitting into 4 waves of 18 GPUs (GPUs 1–18, 19–36, 37–54, 55–71) matches the 18-port ingress capacity and caps concurrent heavy transfers at 2–4 (instead of 12).
```

Inside a Grace Blackwell NVL72 rack, adaptive engines pair `choose_worker_pool` with topology-aware communication scheduling. Using `nvmlDeviceGetNvLinkUtilizationCounter` and NVTAGS, the scheduler places heavily communicating layers on adjacent NVSwitch ports. It also sets `NCCL_ALGO=Tree` to cut all-reduce steps from seventy-one down to six and staggers all-to-all exchanges into four waves of eighteen GPUs. Across racks, it enables `NCCL_CROSS_NIC` over multi-rail InfiniBand links and speculatively prefetches MoE expert assignments to cut cross-node bandwidth by up to thirty percent.

### 5.2 Endpoint-Level Semantic Caching, Routers, and Tiered Model Cascades

Before a request ever reaches a GPU worker pool, an intelligent serving stack evaluates whether the query needs a frontier LLM at all. As detailed in *Hands-On LLM Serving and Optimization* Chapter 10, **Endpoint-Level Semantic Routing** operates above replica-level load balancers by combining four fast stages.
1. **PII Masking via Lightweight NER.** A compact token-classification encoder scans raw user text and replaces sensitive entities such as names and email addresses with placeholders. That masking ensures private data never leaks into vector caches or external model logs.
2. **Embedding Vector Generation and Semantic Cache Lookup.** An embedding model maps the sanitized prompt into a vector and searches a vector database for semantically equivalent prior queries. On a semantic cache hit taking only a few milliseconds, the cached answer returns immediately with zero LLM GPU compute.
3. **MCP Tool Filtering.** For agentic workloads using the Model Context Protocol, the router runs vector similarity over registered tool schemas and injects only the relevant subset of tools into the prompt. That filtering shrinks prefill token count and prevents unintended tool calls.
4. **Complexity Classification and Tiered Model Cascading.** A lightweight encoder classifier such as ModernBERT inspects the prompt embedding. It routes the query across a hierarchy of fine-tuned Small Language Models, a medium workhorse model, or a frontier reasoning model.

```mermaid
flowchart LR
    Req["Raw User Prompt"] --> PII["1. NER PII Masking<br/>PERSON (0.97) -> &lt;NAME_1&gt;<br/>EMAIL (0.95) -> &lt;Email_1&gt;"]
    PII --> Emb["2. Embedding Encoder<br/>768-Dim Vector + MCP Tool Filter"]
    Emb --> Cache{"3. Vector Semantic<br/>Cache Hit?"}
    Cache -->|"Hit (~3 ms)"| FastRet["Return Cached Response<br/>(0 LLM GPU FLOPs)"]
    Cache -->|"Miss"| ModBERT["4. ModernBERT Router<br/>Complexity &amp; Confidence Cascade"]
    ModBERT -->|"Simple (60% share)"| Small["Tier 1: 8B–32B SLM / 70B Model<br/>(50 ms latency, 1.0x cost)"]
    ModBERT -->|"Complex (40% share)"| Large["Tier 2: 700B / Reasoning Model<br/>(500 ms latency, 10.0x cost)"]
    Small -.->|"Low Logit Confidence (10% fallback)"| Large
```

In the tiered model cascade analyzed in *AI Systems Performance Engineering* Chapter 16, a seventy-billion-parameter model answers straightforward factual queries in 50 ms. A seven-hundred-billion-parameter frontier model requires 500 ms at ten times the compute cost. When the router sends sixty percent of queries to the smaller model and forty percent directly to the larger model, two operating regimes emerge.
- **Without fallback.** Expected latency drops from 500.0 ms to 230.0 ms, which is more than twice as fast. Relative compute cost drops from 10.0 to 4.6, and higher offload shares achieve up to the **fivefold cost reduction** reported in *AI Systems Performance Engineering*.
- **With a low-confidence sequential fallback.** Suppose ten percent of the small model's answers exhibit high logit entropy and escalate sequentially to the large model. Expected latency becomes 260.0 ms and relative cost is 5.2. Adding a twenty percent semantic cache hit rate further reduces expected latency to 208.6 ms and relative cost to 4.16.

```text
Model Cascade Latency and Relative Cost Equations (ASP Chapter 16; HLS Chapter 10):
- Baseline (100% 700B model): Latency = 500.0 ms, Cost = 10.0
- Cascade without fallback (60% 70B @ 50 ms / 1.0x, 40% 700B @ 500 ms / 10.0x):
  E[Latency] = 0.60 * 50 + 0.40 * 500 = 230.0 ms;  E[Cost] = 0.60 * 1.0 + 0.40 * 10.0 = 4.6
- Cascade with 10% sequential fallback on 70B (0.54 * 50 ms + 0.06 * 550 ms + 0.40 * 500 ms):
  E[Latency] = 260.0 ms;  E[Cost] = 0.60 * 1.0 + 0.46 * 10.0 = 5.2
- With 20% Semantic Cache Hit Rate (3.0 ms lookup, 0 LLM cost):
  E[Latency] = 0.20 * 3.0 + 0.80 * 260.0 = 208.6 ms;  E[Cost] = 0.80 * 5.2 = 4.16
```

Place an endpoint-level semantic cache and ModernBERT classifier in front of your GPU pools so trivial and repeated queries never consume frontier model capacity.

---

## 6. Test-Time Compute Scaling, Multi-LoRA, Multimodal V1, and RL Runtime Tuning

### 6.1 Test-Time Compute Scaling Budgets: Best-of-N and MCTS with Prefix Sharing

Scaling pretraining compute is no longer the only way to improve model accuracy. Test-time compute scaling dynamically trades additional inference FLOPs for higher reasoning accuracy on hard math, coding, and planning prompts. An adaptive engine maps the router's prompt difficulty score between 0 and 1 to three test-time compute tiers.
1. **Tier 1: System-1 Greedy Decoding.** For difficulty scores under 0.30, the engine emits a single trajectory (`N = 1`) where single-sample accuracy is already near 100%.
2. **Tier 2: Parallel Best-of-N Sampling with Reward Verification.** For difficulty scores from 0.30 to 0.70, the engine generates 4 to 16 independent candidate completions in parallel and scores them with a Process Reward Model. If a hard coding problem has a single-sample pass probability of 0.25, scaling from 1 sample to 8 samples raises multi-sample pass accuracy from **25.00% to 89.99%**, and scaling to 16 samples reaches **99.00%**.
3. **Tier 3: Tree Search and Monte Carlo Tree Search.** For difficulty scores of 0.70 and above, the engine expands 16 trajectories across a tree depth of 4. It interleaves multi-step generation with reward scoring, pruning low-value reasoning branches early under a strict wall-clock SLO and token budget.

```text
Test-Time Compute KV Cache Sharing and Pass@N Math (ASP Ch. 15, 16; HLS Ch. 10):
1. Pass@N Success Probability (under independent single-sample success probability p = 0.25):
   Pass@1  = 1 - (1 - 0.25)^1  = 25.00%
   Pass@4  = 1 - (1 - 0.25)^4  = 68.36%
   Pass@8  = 1 - (1 - 0.25)^8  = 89.99%
   Pass@16 = 1 - (1 - 0.25)^16 = 99.00%
2. PagedAttention / RadixAttention Prefix KV Sharing for Best-of-N (S_prompt = 4,096, S_gen = 512, N = 16):
   Unshared_KV_Tokens = N * (S_prompt + S_gen) = 16 * (4,096 + 512) = 73,728 token slots
   Shared_Prefix_KV_Tokens = S_prompt + N * S_gen = 4,096 + 16 * 512 = 12,288 token slots
   KV_Memory_Saved = 73,728 - 12,288 = 61,440 token slots (83.33% KV memory reduction; 6.0x smaller footprint)
```

Naively running Best-of-16 on a 4,096-token prompt with 512 generated tokens per branch would allocate 73,728 KV cache token slots and recompute the 4,096-token prefill sixteen times. In vLLM PagedAttention and SGLang RadixAttention, the engine computes the 4,096-token prompt prefill **once**. It then bumps the physical page reference count to 16 via zero-copy copy-on-write forking and allocates unique KV blocks only for the 8,192 diverging decode tokens. Total KV cache consumption drops from 73,728 slots to 12,288 slots, an **83.33% memory reduction** that makes parallel test-time compute practical in production.

### 6.2 Multimodal V1 Process Decoupling, Multi-LoRA Punica Kernels, and RL Runtime Tuning

*Hands-On LLM Serving and Optimization* Chapter 10 and *AI Systems Performance Engineering* Chapter 19 highlight three additional runtime architectures that keep GPUs saturated across diverse workloads.
- **Multimodal VLM Process Separation in vLLM V1.** In Vision-Language Models, a single image expands into hundreds of vision tokens, such as 644 image pad tokens. In vLLM V0, synchronous CPU image decoding, cropping, and tensor normalization blocked the main Python thread and starved the GPU. **vLLM V1** splits the engine into two asynchronous OS processes. Process 0 handles the HTTP API, CPU-intensive vision preprocessing, and detokenization. Process 1 exclusively runs the GPU scheduler and launches CUDA kernels without ever stalling on host preprocessing.
- **Multi-LoRA Serving with Punica Kernels.** Many enterprise deployments serve dozens of tenant-specific fine-tuned LoRA adapters whose individual traffic is too low to saturate dedicated GPU replicas. Multi-LoRA co-locates multiple active adapters in HBM alongside the frozen base model. Specialized **Punica** segmented gather-scatter GEMM kernels batch base-model matrix multiplications across all requests and apply each request's distinct low-rank adapter matrices in a single fused pass.
- **RLHF Generation Loops and Online RL System Tuners.** In reinforcement learning pipelines such as OpenRLHF, actor-model sample generation in vLLM or SGLang consumes **eighty percent of total RLHF training time**. That loop requires **batch-invariant deterministic kernels**, as demonstrated by Thinking Machines' work on defeating LLM inference nondeterminism, so batch-shape variations do not corrupt policy-gradient rewards. At the engine control plane, *AI Systems Performance Engineering* Chapter 19 introduces an online Proximal Policy Optimization agent that observes GPU utilization, memory utilization, latency, and queue depth to maximize a continuous SLA-penalized reward.

```text
RL-Based Runtime Autotuner Reward and Safety Kill Switch (ASP Chapter 19):
- Soft Continuous Reward:
  reward = tokens_per_second - lambda * max(0.0, latency_ms - SLA_ms)
  Calibration rule: If 10 ms overshoot is acceptable for +100 tok/s gain, set 10 ms * lambda = 100 -> lambda = 10.0.
  Worked example (850 tok/s, latency = 110 ms, SLA = 100 ms, lambda = 10.0):
  reward_soft = 850.0 - 10.0 * (110.0 - 100.0) = 750.0   (vs hard binary penalty: 850.0 - 1000.0 = -150.0).
- Stability Guardrails:
  1. Action damping: Hold each chosen policy for a minimum cooldown window to prevent oscillation.
  2. Automatic Kill Switch: If p95 latency regresses by > 50% over baseline (e.g., 90 ms -> 140 ms = +55.56%), immediately disable the RL agent, revert to static heuristic defaults, and page the on-call engineer.
```

Start with deterministic heuristics for batching, precision, and routing, and wrap any online RL tuner in action-damping cooldowns and an automatic 50% tail-latency kill switch.

---

## 7. Commands, Configurations, and Production Failure Modes

### 7.1 Production Engine Launch Commands That Matter

The commands below configure vLLM with decode CUDA Graph buckets, TorchInductor compilation, EAGLE speculative decoding, prefix caching for Best-of-N test-time scaling, and Prometheus observability on a multi-GPU node.

```bash
# 1. Persist TorchInductor and Triton compiled kernel mega-cache across pod restarts
export TORCHINDUCTOR_CACHE_DIR="/mnt/shared-nvme/torchinductor_cache"
export TRITON_CACHE_DIR="/mnt/shared-nvme/triton_cache"
export PYTORCH_ALLOC_CONF="expandable_segments:True,max_split_size_mb:256"

# 2. Launch vLLM V1 with CUDA Graph capture buckets, TorchCompile, Prefix Caching, and EAGLE Speculative Decoding
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --tensor-parallel-size 4 \
  --dtype bfloat16 \
  --kv-cache-dtype fp8 \
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --max-num-batched-tokens 2048 \
  --max-num-seqs 256 \
  --cuda-graph-sizes 1 2 4 8 16 24 32 48 64 96 128 192 256 \
  --compilation-config '{"level": 3, "use_cudagraph": true}' \
  --speculative-config '{"method": "eagle", "model": "yuhuili/EAGLE-LLaMA3.1-Instruct-70B", "num_speculative_tokens": 5, "speculative_disable_by_batch_size": 32}' \
  --port 8000
```

Notice that `--speculative-config` sets `speculative_disable_by_batch_size` to 32. That parameter automatically disables speculative drafting whenever the active continuous batch size reaches 32 requests so compute-bound verification never stalls the cluster.

### 7.2 Five Production Failure Modes: Symptom, Diagnosis, and Fix

| Failure Mode | Production Symptom | Root Cause and Telemetry Evidence | Exact Remediation and Configuration Fix |
|---|---|---|---|
| **1. CUDA Graph Pool OOM During Startup Capture** | Engine crashes during warmup with `torch.cuda.OutOfMemoryError` before serving a single request, even though model weights and KV cache fit in HBM. | Too many fine-grained `--cuda-graph-sizes` captured without a shared decreasing-batch pool, or `--gpu-memory-utilization` of 0.95 leaves insufficient workspace for graph buffers. | Lower `--gpu-memory-utilization` to 0.85–0.88, restrict `--cuda-graph-sizes` to stepped buckets up to 256, and ensure decreasing-batch shared pool capture. |
| **2. Dynamic Shape Recompilation Storms** | Tail TTFT spikes from 150 ms to over 12 s sporadically when new prompt lengths arrive; CPU cores peg at 100% running `ptxas`. | `torch.compile` guards triggered on unbucketed variable sequence lengths without `mark_dynamic()` or bucket padding of 10%–20%. | Pad prefill inputs to 512-token buckets, set `torch._dynamo.mark_dynamic()`, mount `TORCHINDUCTOR_CACHE_DIR`, and prewarm extremes before live traffic. |
| **3. Speculative Decoding Throughput Collapse** | Enabling speculative decoding with K=6 speeds up single-user chat by 2.2x but degrades cluster throughput by 30%–45% during peak traffic or creative prompts. | Static K=6 runs during low acceptance (0.30 -> 0.71x slowdown) or when batch size B ≥ 32 pushes verification tokens into the compute-bound regime. | Configure `speculative_disable_by_batch_size` at 32 or 16 and enable dynamic draft-length adaptation driven by live acceptance EMA. |
| **4. Precision or KV Cache Thrashing Oscillation** | Inter-token latency exhibits rhythmic 40 ms jitter every few tokens; logs show hundreds of FP8 to BF16 or INT8 to INT4 switches per second. | Single-threshold controller without EMA smoothing or hysteresis bands reacts to per-token logit noise and synchronizes the host CPU on every step. | Use on-device EMA (0.2), inspect on host only every 8 steps, and enforce hysteresis (`enter_fp8_threshold=6.0`, `exit_fp8_threshold=3.0`). |
| **5. Model Cascade Sequential Tail-Latency Blowup** | Average cost drops, but p99 end-to-end latency jumps from 500 ms to 1,050 ms during complex traffic bursts. | Router misclassifies hard prompts to the small model (> 35% fallback rate), forcing sequential execution of both models on tail requests. | Retrain the ModernBERT router classifier, lower small-model routing threshold for reasoning keywords, or race small and large models in parallel for strict SLAs. |

Every dynamic optimization introduces a control loop; always pair each adaptive policy with a hard cutoff and a fallback guardrail so a shifting workload cannot push the controller into an unstable regime.

---

## 8. Hands-On Verification Lab

### Venue and Scope

This deterministic verification lab runs locally in Python via `code/part15/dynamic_adaptive_inference.py` and `code/part15/dynamic_adaptive_inference_lab.py` with zero external hardware dependencies. The live GKE and multi-GPU `vLLM` commands in Section 7.1 are marked **untested on live hardware** in this environment. All twenty-eight mathematical and algorithmic models in the Python lab are **tested and verified**.

### Running the Self-Checking Lab

Execute the verification suite from the repository root.

```bash
python3 code/part15/dynamic_adaptive_inference_lab.py
```

Expected output.

```text
=== Chapter 15.12 Lab: Dynamic and Adaptive Inference Engine Optimisations ===
  [PASS] 1. Active decode batch 19 maps to CUDA Graph bucket 24 with 5 dummy tokens (20.83% padding overhead)
  [PASS] 2. Active decode batch 300 (> max_graph_batch_size=256) bypasses CUDA Graph and falls back to eager execution
  [PASS] 3. FireworksAI decreasing-batch capture [8, 4, 2, 1] reuses 256.0 MB shared pool vs 480.0 MB isolated (46.67% saved)
  [PASS] 4. CUDA Graph capture reduces kernel launches from 300 to 100 and cuts latency from 1.00 ms to 0.75 ms (1.33x speedup)
  [PASS] 5. torch.compile on 64-expert MoE cuts step time from 248.0 ms to 173.0 ms (75.0 ms / 30.24% saved, 1.43x speedup)
  [PASS] 6. Fused L2Norm cuts traffic 3.0x (36 B -> 12 B), Fused SwiGLU cuts HBM passes 5 -> 3 (1.67x), and 80-layer launch drops 4.32 ms -> 1.44 ms (3.0x)
  [PASS] 7. ASP Table 19-3 tile sweep identifies 256x128 (128 KB SMEM, 60% occ, 11.3 GOPS) as highest throughput and 64x64 (48 KB, 85% occ, 8.2 GOPS) as highest occupancy
  [PASS] 8. Occupancy-aware scheduler halves tile T from 256 to 128 when occupancy 0.30 < 0.50, allocating 3 * 128^2 * 4 = 196,608 bytes (192.0 KB) dynamic SMEM and scheduling prefill when util 0.70 < 0.85
  [PASS] 9. Chinchilla-70B (14.1 ms) + 4B draft (1.8 ms, c=0.1277) at K=5, alpha=0.80 yields E[N]=3.6893 tokens in 23.1 ms (6.2614 ms/tok, 2.25x speedup)
  [PASS] 10. Static K=8 under low acceptance alpha=0.30 degrades performance to 0.71x (19.9615 ms/tok > 14.1 ms/tok baseline)
  [PASS] 11. Dynamic draft-length controller selects K=6..8 at alpha=0.85 (B=2), shrinks to K=1..2 at alpha=0.25, and disables speculation (K=0) when batch B=32 >= cutoff
  [PASS] 12. Exiting at layer 48 of 80 saves 40.0% of layers (1.67x speedup; ASP Early Exit range 30%–50%)
  [PASS] 13. DASH skips 30% of layers (56 executed; range 20%–40%), MoD (C=0.25) bypasses 75.0% of tokens, and LazyLLM cuts long-context latency by 20%–30%
  [PASS] 14. ASP Table 19-2 precision modes: FP16+FP8 (0.5x mem, 1.5x speed, <0.1% drop), INT4+FP8 (0.25x mem, 1.8x speed), INT4+FP4 (0.20x mem, 3.5x speed)
  [PASS] 15. Hysteretic precision loop (enter=6.0, exit=3.0, reeval=8) upgrades BF16 -> FP8 at step 8 and reverts FP8 -> BF16 at step 16 without per-step host sync
  [PASS] 16. Real-time QuantizedCache (HQQ q_group_size=64, residual_length=128) drops from 8-bit to 4-bit when smoothed GPU memory ratio crosses 0.90
  [PASS] 17. choose_worker_pool routes seq_len=16384 (>4096) or mem=0.85 (>0.80) to 'tp_pp_hybrid' and short concurrent chats to 'tensor_parallel'
  [PASS] 18. 8x B200 node provides 1,440 GB HBM (720 GB per 4-GPU PP stage) for DeepSeek-R1 (680B total / 37B active, 256 total / 9 active experts); GB200 NVL72 = 12,960 GB, GB300 NVL72 = 20,736 GB
  [PASS] 19. GB200/GB300 NVL72 provides 18 NVLink 5 ports/GPU = 1.8 TB/s/GPU (3.6 TB/s/superchip, >130 TB/s rack bisection) and tree all-reduce cuts 72-GPU steps from 71 ring hops to 6
  [PASS] 20. Wave scheduling splits 72*71 = 5,112 all-to-all messages into 4 waves of 18 GPUs (matching 18 NVLink ports), and NVTAGS cuts 50 GB/s cross-node traffic into two 25 GB/s local links (-50% latency)
  [PASS] 21. Semantic router (768-dim embedding, NER PII 0.97/0.95, 8B–32B SLMs) + 70B (50 ms) / 700B (500 ms) cascade at 60% small share cuts latency from 500 ms to 230.0 ms (260.0 ms with 10% fallback, 208.6 ms with 20% cache hits)
  [PASS] 22. 70B/700B cascade reduces relative compute cost from 10.0 to 4.6 without fallback (5.2 with 10% fallback, 4.16 with 20% semantic cache hits; up to 5.0x reported in ASP Ch. 16)
  [PASS] 23. Test-time compute router selects N=1 greedy for easy (d=0.15), Best-of-8 PRM for medium (d=0.50), and MCTS (N=16, depth=4) for hard (d=0.85)
  [PASS] 24. Scaling from N=1 to N=8 and N=16 at single-sample pass p=0.25 raises Pass@N accuracy from 25.0% to 89.99% and 99.0%
  [PASS] 25. PagedAttention/RadixAttention prefix sharing on N=16 (4096 prompt + 512 gen) cuts KV slots from 73,728 to 12,288 (83.33% KV memory saved); OpenRLHF generation is 80.0% of RLHF time
  [PASS] 26. RL soft reward at 850 tok/s, latency=110 ms (10 ms > 100 ms SLA, lambda=10.0) equals 850 - 10*10 = 750.0 vs hard binary reward -150.0
  [PASS] 27. RL p95 latency regression of 22.22% (90 ms -> 110 ms) keeps agent active, whereas 55.56% regression (90 ms -> 140 ms, > 50% threshold) triggers the static fallback kill switch
  [PASS] 28. All 6 adaptive engine subsystems (CUDA Graphs, Fused Kernels/Autotuning, Speculative Decoding, Early Exit/Precision, Adaptive Parallelism/Routing, Test-Time Compute/RL) verified

Summary: 28 passed, 0 failed
```

Run `python3 code/part15/dynamic_adaptive_inference_lab.py` whenever you modify bucket ladders, speculative acceptance thresholds, or router cascade weights to verify your calculations before deploying to GPU nodes.

---

## Checkpoint questions

<details>
<summary>1. Why do LLM serving engines capture CUDA Graphs primarily for the decode phase rather than the prefill phase?</summary>

During the decode phase, each request processes only 1 token per step. That makes decode kernels memory-bandwidth-bound with execution times of 5 to 20 microseconds, which is often shorter than the 5 to 15 microseconds of Python and CUDA driver launch overhead across 300+ kernels. Prefill processes thousands of prompt tokens in large compute-bound GEMMs that run for tens of milliseconds and have variable sequence lengths that violate static CUDA Graph shape requirements.
</details>

<details>
<summary>2. An active decode batch contains 19 sequences against bucket ladder 1, 2, 4, 8, 16, 24, 32, 48, 64. Which bucket is chosen, what is the padding overhead, and why is padding faster than eager execution?</summary>

The engine selects bucket 24 and pads 5 dummy tokens, which is a 20.83% padding overhead. Because small-batch decoding is memory-bandwidth-bound on weight reads from HBM, computing 24 rows instead of 19 against the same weight matrices adds almost zero GPU time. Replaying the pre-captured CUDA Graph eliminates milliseconds of CPU kernel-launch overhead.
</details>

<details>
<summary>3. Why should decode CUDA Graph buckets 8, 4, 2, 1 be captured in decreasing batch-size order using a shared graph pool handle?</summary>

Capturing the largest batch size first allocates the 256.0 MB high-water workspace inside the shared pool. Because only one decode graph executes at a time, all smaller buckets reuse those exact same HBM addresses. That shared pool avoids allocating independent buffers totaling 480.0 MB and saves 46.67% of graph workspace memory.
</details>

<details>
<summary>4. How does torch.compile lower a PyTorch model, and what speedup does it achieve on the 64-expert MoE benchmark in AI Systems Performance Engineering?</summary>

TorchDynamo captures Python bytecode into an FX graph with SymPy guards, and AOTAutograd traces joint functional graphs. Next, PrimTorch decomposes over two thousand ATen operators into roughly two hundred fifty primitives, and TorchInductor generates fused OpenAI Triton or C++ kernels. On the sixty-four-expert MoE benchmark, compilation reduces step time from 248.0 ms to 173.0 ms, a 1.43x speedup.
</details>

<details>
<summary>5. How many HBM tensor passes does a Fused SwiGLU Triton kernel save compared to unfused PyTorch execution, and why?</summary>

Unfused execution performs five HBM passes over the intermediate dimension: read gate, write SiLU of gate, read SiLU of gate, read up, and write the product. A fused Triton SwiGLU kernel reads gate and up once, computes the gated activation in registers, and writes the output once. Cutting five passes to three reduces memory-bandwidth traffic by 1.67x.
</details>

<details>
<summary>6. How do PyTorch SymmetricMemory and NVSHMEM enable custom one-shot fused AllReduce kernels to outperform standard ring ncclAllReduce during Tensor Parallel decoding?</summary>

For small decode activation buffers of 64 KB to 512 KB, standard ring AllReduce suffers multi-hop latency and host-synchronization graph breaks unless specially captured. SymmetricMemory and NVSHMEM map peer GPU HBM addresses directly across NVSwitch. That allows a single Triton or CUDA kernel to read peer pointers in one hop and fuse AllReduce, residual addition, and RMSNorm inside a single CUDA Graph node.
</details>

<details>
<summary>7. According to AI Systems Performance Engineering Table 19-3, why does a 256 x 128 attention tile achieve higher throughput (11.3 GOPS) than 64 x 64 (8.2 GOPS) despite dropping SM occupancy from 85% to 60%?</summary>

For long sequences, the larger tile uses 128 KB of shared memory per block to load Key and Value blocks from HBM once. It then reuses those blocks across many more queries in on-chip shared memory. That reduction in global memory traffic and memory-stall cycles outweighs the lower number of concurrent thread blocks per SM.
</details>

<details>
<summary>8. How much dynamic shared memory is required for a tiled attention kernel with tile width T = 128 in FP32, and how does the adaptive scheduler react if SM occupancy falls to 30%?</summary>

Holding three tiles for Query, Key, and Value of 128 by 128 floats requires 196,608 bytes or 192.0 KB. When achieved occupancy of 0.30 falls below the 0.50 threshold, the adaptive scheduler halves T to free shared memory per block so more thread blocks can co-reside on each SM.
</details>

<details>
<summary>9. In the Chinchilla-70B (14.1 ms/tok) and 4B draft (1.8 ms/tok) speculative decoding setup with K = 5 and acceptance rate 0.80, what is the expected tokens per cycle, cycle latency, and net speedup?</summary>

Expected tokens per cycle is 3.6893 tokens. Cycle latency is 23.1 ms, yielding an effective inter-token latency of 6.2614 ms per token and a net speedup of 2.25x.
</details>

<details>
<summary>10. What happens if you keep a static draft length of K = 8 on that same Chinchilla-70B setup when a high-entropy creative prompt drops the acceptance rate to 0.30?</summary>

Expected tokens per cycle drops to 1.4285 tokens while cycle latency rises to 28.5 ms. Effective inter-token latency becomes 19.9615 ms per token, which is a 0.71x slowdown or 41.5% slower than standard decoding without a draft model.
</details>

<details>
<summary>11. How do EAGLE, Medusa, and Self-Speculative decoding differ from two-model Draft-Target speculative decoding?</summary>

Instead of hosting a separate multi-billion-parameter draft LLM, EAGLE attaches a lightweight feature-extrapolation head and reaches 3.5x to 6.5x speedup across its three versions. Medusa attaches parallel decoding heads verified via tree attention for 1.9x speedup on H200 and up to 3.6x overall. Self-Speculative decoding drafts by skipping half of the target model's own layers for roughly 2.0x speedup with zero extra model weights.
</details>

<details>
<summary>12. How does Mixture of Depths differ from Dynamic Early-Exit networks and DASH input-aware layer skipping in terms of CUDA Graph compatibility?</summary>

Early Exit and DASH decide dynamically per token whether to halt or skip a layer, causing variable active batch sizes across layers. Mixture of Depths enforces a static top-k capacity factor per layer, such as routing a fixed quarter of tokens through attention and MLP while bypassing the rest via the residual stream. That fixed capacity preserves deterministic static tensor shapes for CUDA Graphs.
</details>

<details>
<summary>13. Why does decode_with_dynamic_precision use an on-device EMA, an 8-step re-evaluation interval, and separate entry (6.0) and exit (3.0) thresholds?</summary>

Updating the top-2 logit margin EMA on the GPU avoids stalling the CPU and GPU with a device-to-host synchronization on every single token. Checking the EMA only every 8 steps with a hysteresis band between 6.0 and 3.0 prevents rapid precision flapping between BF16 and FP8.
</details>

<details>
<summary>14. How does generate_with_dynamic_quantized_cache change KV cache bit-width from INT8 to INT4 at runtime when Hugging Face QuantizedCache does not support in-place bit-width mutation?</summary>

It generates output tokens in 32-token chunks and monitors true GPU memory utilization via `torch.cuda.mem_get_info()`. When the smoothed used ratio reaches the 0.90 threshold, it starts the next chunk with a new HQQ cache configuration set to 4 bits. That configuration uses a group size of 64 and keeps the most recent 128 tokens in full precision.
</details>

<details>
<summary>15. How does an 8-GPU Blackwell B200 node (1,440 GB HBM) dynamically serve DeepSeek-R1 across both short low-latency queries and 1M-token long-context requests?</summary>

The cluster pre-provisions a four-way Tensor Parallel worker pool for short concurrent queries up to 4,096 tokens and 0.80 memory utilization to avoid pipeline bubbles. It routes longer sequences or high-memory requests to a two-stage hybrid pool where each four-GPU stage provides 720 GB of HBM.
</details>

<details>
<summary>16. On a 72-GPU GB200 NVL72 rack (18 NVLink 5 ports/GPU at 100 GB/s bidirectional = 1.8 TB/s/GPU), why are tree AllReduce and 4-wave collective scheduling preferred over a monolithic ring or all-to-all?</summary>

A 72-GPU ring AllReduce requires 71 sequential hops, whereas a binary tree completes in 6 steps. In an all-to-all or parameter gather, having all 71 peers send to GPU 0 simultaneously generates 5,112 messages and oversubscribes the receiver's 18 NVLink ports. Splitting senders into four waves of 18 GPUs matches the hardware ingress without switch queueing.
</details>

<details>
<summary>17. What are the four stages of the endpoint-level Semantic Router in Hands-On LLM Serving and Optimization Chapter 10?</summary>

First, NER PII masking replaces sensitive entities such as names and emails with placeholders. Second, an encoder generates a 768-dimensional embedding for vector similarity lookup in the semantic cache. Third, Model Context Protocol vector filtering selects relevant agent tools. Fourth, a ModernBERT classifier routes requests across small language models and frontier reasoning models.
</details>

<details>
<summary>18. In a model cascade pairing a 70B model (50 ms, 1x cost) with a 700B model (500 ms, 10x cost) where 60% of queries route to the 70B model and 10% of those escalate sequentially to the 700B model, what are the expected latency and relative cost?</summary>

Fifty-four percent of total traffic finishes on the smaller model in 50 ms, six percent escalates sequentially in 550 ms, and forty percent goes directly to the larger model in 500 ms. That yields 260.0 ms expected latency and 5.2 relative cost, compared to 230.0 ms and 4.6 without fallback.
</details>

<details>
<summary>19. For a Best-of-16 test-time compute query with a 4,096-token prompt and 512 generated tokens per branch, how much KV cache memory does PagedAttention or RadixAttention prefix sharing save, and how does Pass@16 compare to Pass@1 at p = 0.25?</summary>

Sharing the prompt KV blocks across all sixteen branches via copy-on-write reduces allocated KV token slots from 73,728 down to 12,288, saving 83.33%. Meanwhile, multi-sample pass accuracy rises from 25.00% at one sample to 89.99% at eight samples and 99.00% at sixteen samples.
</details>

<details>
<summary>20. How is the RL runtime tuner reward formulated in AI Systems Performance Engineering Chapter 19, how is lambda calibrated, and when does the safety kill switch trip?</summary>

The continuous soft reward subtracts lambda times the SLA latency overshoot from tokens per second. If a 10 ms SLA overshoot is acceptable for a 100 tokens per second throughput gain, lambda equals 10.0. The automatic kill switch disables the RL agent and reverts to static heuristics whenever p95 latency regresses by more than 50% over baseline.
</details>

---

## Key takeaways

1. **Capture decode CUDA Graphs in decreasing batch-size order.** Pre-capturing padded decode buckets from largest to smallest inside a shared pool handle eliminates host launch gaps for a 1.33x speedup. It also saves 46.67% of graph workspace memory across buckets.
2. **Fuse memory-bound decode operators in OpenAI Triton and TorchInductor.** Combining `torch.compile` with custom fused Triton kernels for Add+RMSNorm, RoPE, SwiGLU, and one-shot SymmetricMemory AllReduce cuts eighty-layer kernel launch overhead by 3.0x.
3. **Make speculative draft length adaptive to acceptance rate and batch size.** While a five-token draft at 0.80 acceptance accelerates Chinchilla-70B by 2.25x, a static eight-token draft at 0.30 acceptance causes a 0.71x slowdown. Always drive draft length from an online acceptance EMA and disable speculation at large batch sizes.
4. **Skip redundant layers, tokens, and precision bits with hysteresis.** Dynamic Early Exit, DASH layer skipping, Mixture of Depths, LazyLLM token pruning, hysteretic BF16 to FP8 switching, and HQQ KV cache compression reclaim HBM and FLOPs without quality collapse.
5. **Coordinate topology-aware worker pools, semantic cascades, and shared-prefix test-time compute.** Route traffic across pre-sharded pools, stagger NVL72 collectives into eighteen-GPU waves with tree AllReduce, filter requests through a semantic cache and model cascade, and share prompt KV prefixes across Best-of-N branches to save 83.33% of KV memory.

---

## Exercises

1. **Decode CUDA Graph Bucket Padding and Shared Pool Sizing.**
   - **(a)** Use `select_cuda_graph_bucket()` with the default bucket ladder up to 256. Compute the selected bucket, dummy tokens added, and percentage padding overhead for active decode batches of 19 and 52, and explain what happens at batch size 300.
   - **(b)** Calculate the total HBM workspace allocated for buckets 8, 4, 2, and 1 at 32.0 MB per batch unit under isolated graph pools versus a FireworksAI decreasing-batch shared pool. State the exact megabytes and percentage saved.
2. **Fused Triton Kernels and Occupancy-Aware Attention Autotuning.**
   - **(a)** Consider an eighty-layer LLM decoding 32 tokens with hidden size 4,096 and intermediate size 14,336 in BF16. Compare the HBM passes moved by unfused versus fused SwiGLU and the total launch time at 6 microseconds per launch when replacing nine unfused kernels per layer with three fused Triton kernels.
   - **(b)** From *AI Systems Performance Engineering* Table 19-3, identify which attention tile maximizes throughput and which maximizes SM occupancy. Calculate the dynamic shared memory in bytes and kilobytes after the adaptive scheduler halves T from 256 to 128 when achieved occupancy drops to 0.30.
3. **Speculative Decoding Verification Math and Dynamic Draft Adaptation.**
   - **(a)** Chinchilla-70B takes 14.1 ms per token and its 4B draft model takes 1.8 ms per token. Compute expected tokens per cycle, cycle latency, effective inter-token latency, and net speedup for K=5 at 0.80 acceptance versus K=8 at 0.30 acceptance.
   - **(b)** Explain why an active continuous batch size of 32 causes speculative verification to become compute-bound and why `speculative_disable_by_batch_size` must cut the draft length to zero.
4. **Semantic Model Cascades, Test-Time Compute Scaling, and RL Runtime Rewards.**
   - **(a)** A cascade pairs a 50 ms small model at 1.0 cost with a 500 ms large model at 10.0 cost. Sixty percent of requests route to the small model, ten percent of those escalate sequentially to the large model, and a semantic cache intercepts twenty percent of all requests in 3.0 ms. Calculate the expected latency and relative compute cost with and without the semantic cache.
   - **(b)** Consider a Best-of-16 reasoning query with a 4,096-token prompt, 512 generated tokens per branch, and single-sample pass probability 0.25. Compute Pass@1, Pass@8, Pass@16, and the exact KV token slots saved by PagedAttention prefix sharing. Then compute the soft RL runtime reward at 850 tokens per second, 110 ms latency, 100 ms SLA, and lambda 10.0, and check whether a p95 jump from 90 ms to 140 ms trips the kill switch.

---

## Sources and review notes

### Primary Sources Cited

```text
Book Sources (Local TOON-RAG Corpus):
1. Chris Fregly, "AI Systems Performance Engineering" (O'Reilly, 2025) [corpus: ai-systems-performance-engineering]:
   - Chapter 19: "Dynamic and Adaptive Inference Engine Optimizations" (Table 19-1 traffic-to-parallelism mapping; 8x B200 1,440 GB / 720 GB DeepSeek-R1 680B/37B 256/9 experts choose_worker_pool; Table 19-2 FP16/FP8/INT4+FP8/INT4+FP4 trade-offs; decode_with_dynamic_precision enter=6.0, exit=3.0, reeval=8, alpha=0.2; Transformer Engine DelayedScaling Format.HYBRID amax_history_len=1024; Table 19-3 attention tile autotuning 64x64..256x128; dynamic shared memory 3*T*T*sizeof(float) and 75%/25% L1/SMEM carveout; SpeCache and OffloadedCache 8 MiB two-stream KV prefetching; QuantizedCache HQQ INT8->INT4 at 0.90 mem ratio with q_group_size=64, residual_length=128; RL runtime tuner reward = throughput - lambda * max(0, latency - SLA) and >50% p95 kill switch; 64 KB slab vs BFC vs cudaMallocAsync allocator retry; ARIMA/Prophet CUDA Graph prewarming; SARATHI 1.3x–1.9x chunked prefill 10,000 -> 5x 2,000 tokens; GB200/GB300 NVL72 18 * 100 GB/s = 1.8 TB/s/GPU, NVTAGS 50 GB/s -> 2x 25 GB/s, NCCL_ALGO=Tree 6 vs 71 steps, 4 waves of 18 GPUs for 5,112 messages; Early Exit 30%–50%, DASH 20%–40%, speculative MoE -30% BW, LazyLLM 20%–30%).
   - Chapter 9: "Increasing CUDA Kernel Efficiency and Arithmetic Intensity" (fusedL2Norm 36 B -> 12 B, 3.0x memory traffic reduction).
   - Chapter 12: "Dynamic Scheduling, CUDA Graphs, and Device-Initiated Kernel Orchestration" (Table 12-1 CUDA Graph 300 -> 100 launches, 1.00 -> 0.75 ms, 1.33x speedup).
   - Chapter 13: "Profiling, Tuning, and Scaling PyTorch" (Table 13-5 torch.compile 64-expert MoE 248.0 -> 173.0 ms, 1.43x speedup; FireworksAI decreasing-batch [8, 4, 2, 1] shared CUDA Graph pool; SymmetricMemory & NVSHMEM on-device collectives).
   - Chapter 14: "PyTorch Compiler, OpenAI Triton, and XLA Backends" (TorchDynamo PEP 523, AOTAutograd, PrimTorch ~250 prims, TorchInductor modes, dynamic shape bucket padding ±10%–20%).
   - Chapter 15: "Multinode Inference, Parallelism, Decoding, and Routing Optimizations" (Speculative decoding, EAGLE-1 3.5x, EAGLE-2 +20%–40%, EAGLE-3 1.4x / 6.5x, Medusa 2.2x–3.6x, self-speculative 2.0x, consistent decoding 3.0x, XGrammar guided decoding).
   - Chapter 16: "Profiling, Debugging, and Tuning Inference at Scale" (W4A8 / NVFP4 fused quant-dequant, SGLang RadixAttention LRU tree, and 70B 50 ms vs 700B 500 ms model cascading achieving up to 5.0x cost reduction at 60% small-model routing).
2. Yuan Tang, "Hands-On LLM Serving and Optimization" (O'Reilly, 2025) [corpus: hands-on-llm-serving-and-optimization]:
   - Chapter 10: "Advancements in LLM Serving" (Endpoint-level vs replica-level semantic caching and routing; NER PII masking PERSON 0.97 / EMAIL 0.95; 768-dim embedding vector lookup; ModernBERT classifier routing to 8B–32B SLMs; MCP tool filtering; 3-layer Serving/Framework/Runtime profiling funnel; VLM 644-token <|image_pad|> multimodal serving and vLLM V1 Process 0 / Process 1 separation; edge TOPS/W NPUs and thermal scheduling; Multi-LoRA Punica kernels; OpenRLHF 80% sample-generation time and batch-invariant deterministic inference).
   - Chapter 4: "Model Serving Best Practices" (Enterprise speculative decoding and model orchestration layers).
3. Chip Huyen, "AI Engineering" (O'Reilly, 2025) [corpus: ai-engineering]:
   - Chapter 9: "Inference Optimization" (Speculative decoding acceptance/verification loop; DeepMind Chinchilla-70B 14.1 ms/tok + 4B draft 1.8 ms/tok = 7.83x faster draft; Inference with Reference 2.0x speedup; Lookahead Jacobi decoding; Medusa 1.9x speedup on HGX H200 for Llama 3.1).
```

### Inferences and Verification Notes

- **Verified against source text and self-checking code.** All tables, formulas, and numerical examples in Sections 1 through 8 are verified by the twenty-eight passing checks in `code/part15/dynamic_adaptive_inference_lab.py` and traced in `planning/ledgers/15-12.md`.
- **Labelled engineering synthesis.** The eighty-layer HBM pass and launch breakdown, the decreasing-batch pool instantiation, the Mixture of Depths static-shape comparison, and the Best-of-16 KV slot savings are deterministic first-principles calculations. All four models are implemented in `code/part15/dynamic_adaptive_inference.py` to make the book concepts concrete and testable.
- **Hardware execution status.** The multi-GPU `vLLM` CLI deployment command in Section 7.1 is a production reference template and was **not run on live GPU hardware** during this documentation build. The Python verification lab in `code/part15/dynamic_adaptive_inference_lab.py` was executed and verified locally with 28 passed and 0 failed checks.

