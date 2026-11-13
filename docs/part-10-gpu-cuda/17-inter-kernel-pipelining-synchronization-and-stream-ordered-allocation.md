---
id: "c10-17"
title: "10.17 Inter-kernel pipelining, synchronization and stream-ordered allocation"
sidebar_label: "10.17 Inter-kernel pipelining, synchronization and stream-ordered allocation"
sidebar_position: 17
description: "Overlapping kernels, DMA transfers, and allocations across CUDA streams, stream-ordered memory pools (cudaMallocAsync, cudaMemPoolAttrReleaseThreshold, PYTORCH_ALLOC_CONF), legacy vs Per-Thread Default Streams (PTDS), fine-grained events and host callbacks (cudaLaunchHostFunc), two-layer warp-specialized and Thread Block Cluster stream pipelines, multi-GPU P2P/NCCL/NIXL overlap, and Programmatic Dependent Launch (PDL)."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "Nebius GPU"
---

# 10.17 Inter-kernel pipelining, synchronization and stream-ordered allocation

| | |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | Nebius GPU |
| Part | Part 10: The GPU and CUDA |
| Sources used | *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chris Fregly), Chapter 11 (*Inter-Kernel Pipelining, Synchronization, and CUDA Stream-Ordered Memory Allocations*) |
| Code | `code/part10/inter_kernel_pipelining.py`, `code/part10/inter_kernel_pipelining_lab.py` |
| Coverage file | `planning/coverage/chapters/10-17.md` |

## Why this matters for AI infrastructure

Picture a training job whose kernels are beautifully tuned. Each one runs close to full efficiency inside its own loop. Yet the timeline in Nsight Systems shows wide empty gaps between the kernels. The GPU sits idle while the host copies the next micro-batch, while an allocation waits its turn, or while a copy from one GPU to another crawls across the network. The kernels are fine. The space between them is the problem, and that space is what this chapter is about.

Between kernels, the GPU often stalls while it waits for host-to-device micro-batch transfers, blocking memory allocations, legacy default-stream barriers, or cross-GPU network copies. A micro-batch is a small slice of the training data sent to the GPU in one step. Training engineers and inference operators see these stalls as wide empty gaps on the Nsight Systems timeline, and the result is lower token throughput. Token throughput is how many output tokens the service produces per second.

*AI Systems Performance Engineering* Chapter 11 extends intra-kernel pipelining into a full two-layer execution architecture. The first layer runs inside each kernel, and the second runs across kernels. The chapter combines both layers so that work overlaps everywhere it can.

The first idea is three-way overlap. A modern NVIDIA GPU has compute pipelines for the Streaming Multiprocessors, plus at least two copy engines. A copy engine is a separate hardware unit that moves data, so it can work while the compute pipelines are busy. Keeping the compute pipelines and both copy engines busy at once is the goal. Enqueuing micro-batches across explicit non-blocking streams, with pinned host memory and stream-ordered allocation, overlaps the current compute, the staging of the next input, and the retrieval of the prior output. The source describes up to 128 resident kernel grids as well. A grid is one launch of a kernel, so the number reflects how many launches the hardware can hold at once.

The second idea is stream-ordered memory pools. Legacy allocation and deallocation calls can stop the whole GPU while they run. Stream-ordered pools remove that global barrier. Using `cudaMallocAsync` and `cudaFreeAsync` with a tuned pool release threshold lets a job allocate temporary attention scratch buffers and grow variable-length sequence workspaces without stalling other streams. The same approach feeds layerwise large language model pipelines spread across several streams on one GPU.

The third idea is the two-layer pipeline. It combines intra-kernel warp specialization or Thread Block Clusters with inter-kernel CUDA Streams. A three-role dual-pipeline kernel, or a four-block clustered kernel, can run across several streams. Host staging and stream-ordered allocation then hide behind kernels that are already running. The source notes that this overlap still works even when cooperative cluster kernels take turns on the Streaming Multiprocessors.

The fourth idea is wider reach. Multi-GPU peer-to-peer transfers, NCCL ring AllReduce, NIXL, and Programmatic Dependent Launch extend stream overlap across devices and across back-to-back kernels. Peer-to-peer means one GPU reading or writing another GPU's memory directly. NCCL is NVIDIA's library for collective communication between GPUs. NIXL is the NVIDIA Inference Xfer Library, which moves data for inference. Dedicated high-priority streams can overlap peer copies on the copy engine. Low-occupancy NCCL collectives and NIXL transfers can both be captured into a CUDA Graph, which is a recorded sequence of GPU work that can be replayed. Programmatic Dependent Launch lets a primary kernel trigger a dependent kernel as soon as its global memory writes are flushed, so the prologue of the second kernel and the epilogue of the first run in the same stream.

| Architectural Layer | Key Mechanism | Primary Parameters and Figures | Model or Hardware Result |
|---|---|---|---|
| Three-way stream overlap | `cudaStreamNonBlocking`, `cudaMallocHost`, `pin_memory=True`, `asyncEngineCount >= 2` | Figure 11-1, Figure 11-2, 8 batches, max 128 resident grids | 36.0 ms serial to 18.16 ms overlapped, 1.98x speedup in `simulate_inter_kernel_stream_pipeline()` |
| Stream-ordered memory pool | `cudaMallocAsync`, `cudaFreeAsync`, `cudaMemPoolAttrReleaseThreshold`, `PYTORCH_ALLOC_CONF=backend:cudaMallocAsync` | Figure 11-3, threshold `prop.totalGlobalMem / 2` = 96 GiB on 192 GiB GPU, 16 MB = 16,777,216 B scratch | Sequence growth 512 to 1,024 tokens = 2.0x; layerwise split layers 0-5 on stream 0 and layers 6-11 on stream 1 |
| Two-layer warp and cluster streams | `warp_specialized_two_pipelines` and `launch_warp_specialized_cluster_pipeline_multistream` | `blockDim = 96`, `pipe_lc` + `pipe_cs`, `TILE_SIZE = 1,024` at 24,576 B or `TILE_SIZE = 128` at 196,608 B, 528 blocks | Overlaps H2D, D2H, and `cudaMallocAsync` across `NUM_STREAMS = 2` |
| Multi-GPU and PDL | `cudaMemcpyPeerAsync`, NCCL, `nixlCommStream`, `cudaTriggerProgrammaticLaunchCompletion`, `cudaGridDependencySynchronize` | Figure 11-8 with 4 GPUs and 4 chunks 1-4; Figure 11-9, Figure 11-10, Figure 11-11 | 0 SM cycles for peer DMA; PDL cuts 4.0 ms to 3.6 ms in `model_programmatic_dependent_launch()` |

:::note About the timings in this chapter
The stage timings and the Programmatic Dependent Launch figures in the table above come from small timeline models in `code/part10/inter_kernel_pipelining.py`. Those models use assumed stage durations such as 1.0 ms H2D, 2.0 ms compute, and 1.0 ms D2H. They illustrate the diagrams in *AI Systems Performance Engineering* and are not GPU measurements. The source notes that its own metric tables are illustrative as well. The CUDA listings reproduced from that source were not compiled here.
:::

## Prerequisites and outcomes

**Prerequisites:** Work through Chapter 10.12 first. It covers the basics of CUDA Streams, CUDA Events, and pinned memory. Then review Chapter 10.16, which covers `<cuda/pipeline>`, three-role warp specialization, Cooperative Groups, and Thread Block Clusters. The ideas in this chapter stack on top of those two.

The chapter moves through the material in order. It starts with concurrent kernels and the three-way overlap of host-to-device copies, compute, and device-to-host copies across non-blocking streams. It explains why the hardware limit of 128 concurrent grids matters. Next it covers the stream-ordered memory allocator, including the calls `cudaMallocAsync`, `cudaFreeAsync`, `cudaMemPoolSetAttribute`, and `cudaMemPoolAttrReleaseThreshold`, and how they serve scratch buffers, growing token sequences, and layerwise pipelines. Then it compares the legacy default stream with the Per-Thread Default Stream and explicit non-blocking streams. It shows how events and `cudaLaunchHostFunc` coordinate work without deadlocks. After that it layers warp specialization and Thread Block Clusters on top of multiple streams through `cudaLaunchKernelExC`. Multi-GPU overlap comes next, with peer copies, NCCL ring AllReduce streams, NIXL communication streams, and multi-stream graph capture. The last part covers Programmatic Dependent Launch and how it combines with clusters, warp specialization, and Blackwell Tensor Memory Accelerator reductions.

---

## 1. Overlapping Kernel Execution and 3-Way Data Transfers with CUDA Streams

Suppose a training script launches every kernel into one queue. Small kernels that use only part of the GPU leave the rest of the Streaming Multiprocessors idle. Your question is how to let those kernels run side by side. The answer starts with the stream, a queue of GPU work that the hardware can run alongside other queues.

### 1.1 Concurrent kernel dispatch and host interleaving

When a training script launches every kernel into a single queue, small kernels that use only part of the GPU leave the remaining Streaming Multiprocessors idle. Worse, if the host waits for each launch before running CPU bookkeeping, host and device execution serialize completely. A CUDA Stream solves this problem by acting as an independent first-in, first-out queue of device operations. First-in, first-out means work leaves the queue in the same order it entered.

Think of a stream as one checkout lane in a supermarket. Operations inside one lane are served strictly in order. Two lanes can be served at the same time, so the shoppers in lane two do not wait for lane one. Operations enqueued into different non-blocking streams can overlap on the GPU whenever hardware resources are free. Non-blocking means the stream does not wait for the legacy default stream. Figure 11-1 of *AI Systems Performance Engineering* Chapter 11 shows this layout. Because kernel launches are asynchronous, control returns to the CPU immediately. That lets host functions run in parallel with device work. If you have written asynchronous code in Python, the idea will feel familiar. The call returns quickly, and the result shows up later.

The table summarizes the example program below. Read it as a map of which kernel goes on which stream, and where the CPU work fits in between.

| Parameter | Configuration | Detail |
|---|---|---|
| Total kernels launched | 5 kernels | `ker_1`, `ker_2`, `ker_3` on `stream1` and `ker_A`, `ker_B` on `stream2` |
| Launch geometry per kernel | `grid(128)` by `block(256)` | 32,768 threads per kernel launch |
| Interleaved host functions | `cpu_code_1()` and `cpu_code_2()` | Execute on the CPU while device streams run |

```cpp
// Launching 5 kernels across 2 non-blocking streams while interleaving CPU work (Figure 11-1)
// Source: AI Systems Performance Engineering, Chapter 11
#include <cstdio>
#include <cuda_runtime.h>

__global__ void ker_A() { /* ... device work ... */ }
__global__ void ker_B() { /* ... device work ... */ }
__global__ void ker_1() { /* ... device work ... */ }
__global__ void ker_2() { /* ... device work ... */ }
__global__ void ker_3() { /* ... device work ... */ }

void cpu_code_1() {}
void cpu_code_2() {}

int main() {
    // 1. Create two explicit non-blocking streams (do NOT sync with legacy stream 0)
    cudaStream_t stream1, stream2;
    cudaStreamCreateWithFlags(&stream1, cudaStreamNonBlocking);
    cudaStreamCreateWithFlags(&stream2, cudaStreamNonBlocking);

    dim3 grid(128), block(256); // 32,768 threads per launch

    // 2. Enqueue ker_1 on stream1; control returns immediately to CPU
    ker_1<<<grid, block, 0, stream1>>>();
    printf("CPU code 1 executing\n");
    cpu_code_1();

    // 3. Interleave launches across stream2 and stream1 + CPU code 2
    ker_A<<<grid, block, 0, stream2>>>();
    ker_B<<<grid, block, 0, stream1>>>();
    ker_2<<<grid, block, 0, stream2>>>();
    printf("CPU code 2 executing\n");
    cpu_code_2();
    ker_3<<<grid, block, 0, stream1>>>();

    // 4. Synchronize both streams and clean up
    cudaStreamSynchronize(stream1);
    cudaStreamSynchronize(stream2);
    cudaStreamDestroy(stream1);
    cudaStreamDestroy(stream2);
    return 0;
}
```

### 1.2 Three-way `H2D` / `Compute` / `D2H` overlap, hardware limits (`128` grids), and saturation contention

Start with a plain inference loop. Each micro-batch copies its inputs from host to device, runs the kernel, and then copies the outputs from device back to host. The steps happen one after another. While the PCIe or NVLink bus carries data, the Streaming Multiprocessors sit idle. While the Streaming Multiprocessors compute, both directions of the bus sit idle. Over eight batches, this stop-and-go execution nearly doubles wall-clock latency.

The fix is a three-lane assembly line. Batch b is computing, batch b+1 is arriving, and batch b-1 is leaving. Every hardware engine works on a different batch in the same moment. Modern NVIDIA data-center GPUs provide at least two independent Direct Memory Access copy engines, the units that move data without using the compute cores. The check is `deviceProp.asyncEngineCount >= 2`, and it sits alongside the Streaming Multiprocessor compute pipeline. One copy engine handles host-to-device transfers, while the second handles device-to-host transfers. Figure 11-2 of *AI Systems Performance Engineering* Chapter 11 illustrates this split. Pipelining micro-batches across three or more non-blocking streams keeps all three hardware engines busy during steady state. The lanes only truly run side by side when the host memory is pinned. Pinning lets a copy engine read the host buffer directly while the CPU does other work. Without pinning, the lane has to wait for a staging copy first, and that wait stops the whole lane.

Each stream in that three-lane layout has one job:

- Stream 0 drives the Streaming Multiprocessor compute pipeline for the current micro-batch.
- Stream 1 drives copy engine 0 to run a host-to-device asynchronous copy for the next micro-batch, from pinned host RAM into HBM.
- Stream 2 drives copy engine 1 to run a device-to-host asynchronous copy for the completed output of the previous micro-batch, back to pinned host RAM.

The diagram shows the same three lanes at one moment in steady state. A helpful way to follow it is to pick one batch and track it across time. In the first slice, batch b is still arriving on the input lane. In the next slice, it is the batch on the compute lane. In the slice after that, its results are leaving on the output lane. Each batch passes through all three lanes, and the lanes always hold three different batches at the same moment. That is the whole secret of steady state. Nothing waits for the previous batch to finish completely before the next one starts moving.

```mermaid
flowchart LR
    subgraph StepT["Steady-State Time Slice t (3-Way Hardware Overlap, Figure 11-2)"]
      E1["DMA Engine 0 (H2D) on Stream 1\ncudaMemcpyAsync(Batch b+1, H2D)"]
      E2["SM Compute Pipeline on Stream 0\ncomputeKernel(Batch b)"]
      E3["DMA Engine 1 (D2H) on Stream 2\ncudaMemcpyAsync(Batch b-1, D2H)"]
    end
    subgraph Reqs["Four Mandatory Overlap Preconditions"]
      R1["1. Explicit cudaStreamNonBlocking streams"]
      R2["2. Pinned host memory (cudaMallocHost / pin_memory=True)"]
      R3["3. Stream-ordered allocation (cudaMallocAsync / cudaFreeAsync)"]
      R4["4. Per-kernel SM & BW usage below 100% saturation (<= 128 active grids)"]
    end
    Reqs --> StepT
```

Four physical and runtime rules decide whether multi-stream work really overlaps on the hardware. Missing any one of them quietly turns the pipeline back into a line of waiting.

1. Pinned host memory is required for asynchronous `cudaMemcpyAsync` transfers. Pinned memory is host RAM that the operating system will not move around, so the GPU can read it directly. If you pass a pageable pointer, the CUDA driver makes a synchronous CPU staging copy into an internal pinned buffer first. That copy blocks the calling CPU thread and serializes the stream. Allocate host staging buffers with `cudaMallocHost` in C++, or set `pin_memory=True` in PyTorch.
2. Stream-ordered allocation is required when buffers are allocated inside a multi-stream loop. Calling the legacy `cudaMalloc` or `cudaFree` forces a device-wide synchronization across all streams on the GPU. Every lane has to stop so the allocator can finish its work.
3. Resource saturation splits throughput between contending streams. Suppose a single kernel already uses 100% of compute throughput or HBM bandwidth. If you launch a second kernel in another stream, the two kernels contend, and each one runs at 50% speed. The second stream adds no net speedup in that case.
4. Modern GPUs enforce a hard limit of 128 concurrently executing kernel grids per device. Launches beyond 128 active grids wait in hardware queues. When an active grid finishes, a waiting grid can start. Kernels that do run together must still fit within each Streaming Multiprocessor's register, shared memory, and block limits.

The table compares three versions of the same eight-batch workload. Each row changes one thing, so you can see what each fix buys you. The timings are the assumed stage times from the timeline model, not measurements.

| Pipeline Scenario (`simulate_inter_kernel_stream_pipeline`, 8 Batches) | Stage Timings Assumed | Total Time | Speedup vs Serial |
|---|---|---|---|
| Serial baseline or blocking `cudaMalloc` | 1.0 ms H2D, 2.0 ms compute, 1.0 ms D2H, 0.5 ms sync `cudaMalloc` = 4.5 ms/batch | 36.0 ms | 1.00x |
| Overlapped with pageable host memory | 0.02 ms `cudaMallocAsync`, synchronous CPU staging on H2D/D2H | 32.16 ms | 1.12x |
| Overlapped with pinned host memory and `cudaMallocAsync` | Full 3-way overlap across `asyncEngineCount >= 2` | 18.16 ms | 1.98x |

---

## 2. The Stream-Ordered Memory Allocator (`cudaMallocAsync`) and LLM Scratch Pools

Picture a serving engine that has been running steadily for hours. A request arrives with a longer prompt than usual, and the scratch buffer has to grow. Your question is why that one allocation makes other requests stall. The answer lies in how the allocator talks to the rest of the GPU.

### 2.1 Tuning the device memory pool (`cudaMemPoolSetAttribute` & `PYTORCH_ALLOC_CONF`)

Dynamic deep learning workloads frequently allocate and free temporary tensors inside the training or inference loop. A tensor is a block of numbers on the GPU, and a temporary tensor lives only for part of a step. When a runtime falls back to OS-level blocking allocations, the driver halts every stream on the GPU to update page tables. Page tables are the bookkeeping that maps memory addresses to physical pages. Even PyTorch's default caching allocator, which is stream-aware on cache hits, synchronizes the entire device whenever a cache miss triggers a fresh allocation from the driver. A cache miss means the allocator has no free block of the right size and has to ask the driver for new memory.

Exporting `PYTORCH_ALLOC_CONF=backend:cudaMallocAsync` switches PyTorch to CUDA's native stream-ordered memory allocator. This allocator treats allocation and deallocation calls as items in a stream queue, inside a per-device memory pool of type `cudaMemPool_t`. Because the work is queued in order, it reduces cross-stream fragmentation. Fragmentation is the situation where free memory exists but is split into pieces too small to use. Consider a tensor freed asynchronously on stream A. Stream B can reuse that physical memory right after an event dependency, without waiting for the rest of the GPU. An event dependency is a marker that tells stream B to wait only for that one point in stream A.

```bash
export PYTORCH_ALLOC_CONF=backend:cudaMallocAsync
```

Think of the pool as a shelf where unused boxes wait for the next order. The release threshold decides how much stays on that shelf before the extra boxes go back to the warehouse. A higher threshold means fewer trips to the warehouse, but it also keeps more memory tied up in the process. In CUDA C++, you control how much memory the default device pool keeps before it returns physical pages to the operating system. You do this by calling `cudaMemPoolSetAttribute` with `cudaMemPoolAttrReleaseThreshold`. The chapter's example sets the threshold to half of total global memory. That keeps up to 50% of total VRAM in the pool across asynchronous free calls. On a 192 GiB Blackwell B200 GPU, the threshold keeps 96 GiB cached in the pool, so later mini-batches do not pay the cost of mapping memory from the operating system again. Mapping is the work of connecting physical pages to the process's address space, and it is slow compared with reusing pages the pool already holds.

```bash
export PYTORCH_ALLOC_CONF=backend:cudaMallocAsync
```

```cpp
// Stream-ordered memory pool configuration and 2-stream overlapped pipeline
// Source: AI Systems Performance Engineering, Chapter 11
#include <cuda_runtime.h>
#include <cstdint>

void runStreamOrderedPipeline(const float* h_data1, float* h_result1,
                              const float* h_data2, float* h_result2,
                              size_t N, dim3 gridDim, dim3 blockDim) {
    cudaMemPool_t pool;
    int device = 0;
    cudaGetDevice(&device);
    cudaDeviceGetDefaultMemPool(&pool, device);

    cudaDeviceProp prop{};
    cudaGetDeviceProperties(&prop, device);
    // Keep up to 50% of total VRAM (e.g., 96 GiB on a 192 GiB GPU) in the pool before releasing to OS
    uint64_t threshold = prop.totalGlobalMem / 2;
    cudaMemPoolSetAttribute(pool, cudaMemPoolAttrReleaseThreshold, &threshold);

    cudaStream_t stream1, stream2;
    cudaStreamCreateWithFlags(&stream1, cudaStreamNonBlocking);
    cudaStreamCreateWithFlags(&stream2, cudaStreamNonBlocking);

    void *d_data1 = nullptr, *d_result1 = nullptr;
    void *d_data2 = nullptr, *d_result2 = nullptr;
    size_t dataSizeBytes = N * sizeof(float);

    // 1. Stream-ordered allocations: zero cross-stream synchronization
    cudaMallocAsync(&d_data1, dataSizeBytes, stream1);
    cudaMallocAsync(&d_result1, dataSizeBytes, stream1);
    cudaMallocAsync(&d_data2, dataSizeBytes, stream2);
    cudaMallocAsync(&d_result2, dataSizeBytes, stream2);

    // 2. Stream 1: H2D -> Kernel -> D2H
    cudaMemcpyAsync(d_data1, h_data1, dataSizeBytes, cudaMemcpyHostToDevice, stream1);
    // computeKernel<<<gridDim, blockDim, 0, stream1>>>((float*)d_data1, (float*)d_result1);
    cudaMemcpyAsync(h_result1, d_result1, dataSizeBytes, cudaMemcpyDeviceToHost, stream1);

    // 3. Stream 2 overlaps concurrently: H2D -> Kernel -> D2H
    cudaMemcpyAsync(d_data2, h_data2, dataSizeBytes, cudaMemcpyHostToDevice, stream2);
    // computeKernel<<<gridDim, blockDim, 0, stream2>>>((float*)d_data2, (float*)d_result2);
    cudaMemcpyAsync(h_result2, d_result2, dataSizeBytes, cudaMemcpyDeviceToHost, stream2);

    // 4. Stream-ordered frees enqueued before host synchronization
    cudaFreeAsync(d_data1, stream1);
    cudaFreeAsync(d_result1, stream1);
    cudaFreeAsync(d_data2, stream2);
    cudaFreeAsync(d_result2, stream2);

    cudaStreamSynchronize(stream1);
    cudaStreamSynchronize(stream2);
    cudaStreamDestroy(stream1);
    cudaStreamDestroy(stream2);
}
```

### 2.2 Three LLM workloads that depend on `cudaMallocAsync`

Large language model serving and training engines allocate scratch memory whose size changes from batch to batch and step to step. Scratch memory is temporary working space that a computation needs while it runs. When a serving engine uses blocking allocations for these buffers, a single jump in sequence length stalls every concurrent stream on the GPU. Figure 11-3 of *AI Systems Performance Engineering* Chapter 11 and `plan_stream_ordered_pool()` in `code/part10/inter_kernel_pipelining.py` show three places where `cudaMallocAsync` keeps full overlap. The table below takes each pattern in turn and compares the legacy call with the stream-ordered call. A quick way to see the difference is to ask what the other streams are doing while the allocation runs. With the legacy call, the answer is nothing, because every stream is frozen. With the stream-ordered call, the other streams keep working. The allocation is only one more item in the queue of the stream that asked for it, so the rest of the GPU does not wait for it.

Each row is a pattern you are likely to meet. The first is a fixed-size scratch buffer that gets allocated again and again. The second is a buffer that has to grow as the sequence gets longer. The third is a model split across streams, where one half hands its buffers to the other half.

| LLM Runtime Pattern | Why Dynamic Allocation Occurs | What Happens with Legacy `cudaMalloc` | What Happens with `cudaMallocAsync` |
|---|---|---|---|
| 1. Per-batch attention scratch buffers (`16 MB` workspace) | Each Transformer mini-batch requires temporary scratch memory of 16 MB = 16,777,216 bytes for pre-softmax attention scores, layer norm, or intermediate activations. | Calling `cudaMalloc` on `stream1` forces a global barrier across the GPU, stalling `stream0`'s in-flight attention kernel. | `cudaMallocAsync(&scratchPtr, 16 * 1024 * 1024, stream1)` appends a queue item to `stream1`; `stream0` continues executing uninterrupted. |
| 2. Variable-length sequence batches (`512` to `1,024` tokens) and growing decode KV caches | When Batch N has 512 tokens per sequence and Batch N + 1 has 1,024 tokens per sequence for a 2.0x growth, or as autoregressive decode appends K/V vectors, the previous buffer is too small. | Reallocating the larger buffer via `cudaMalloc` halts all concurrent H2D prompt staging and D2H token streaming. | `cudaMallocAsync` reserves the 2.0x larger buffer inside the active stream while upstream H2D and downstream D2H streams run in parallel. |
| 3. Layerwise pipeline parallelism across streams (`layers 0-5` vs `layers 6-11`) | A 12-layer Transformer block is split on one GPU so `stream 0` runs layers 0-5 and `stream 1` runs layers 6-11, handing off intermediate activation buffers between halves. | Allocating the next batch's activation buffer after `stream 0` finishes layers 0-5 pauses `stream 1`'s execution of layers 6-11. | `stream 0` calls `cudaMallocAsync` for the next micro-batch's activations while `stream 1` simultaneously computes layers 6-11 on the prior batch. |

---

## 3. Default vs. Explicit Streams, Per-Thread Default Streams (`PTDS`), Events, and Host Callbacks

Think about a shared kitchen where one cook refuses to let anyone else use the stove until their own dish is finished. Your question is why a single CUDA call without a stream argument can freeze work that has nothing to do with it. The answer is the legacy default stream, and the stream choices in this section decide whether the kitchen runs in parallel.

### 3.1 Comparing Legacy Default Stream (`stream 0`), `PTDS`, and Explicit Non-Blocking Streams

A single stray CUDA call that omits its stream argument can silently destroy multi-stream concurrency across an entire application. By default, omitting the stream argument sends work to the legacy default stream. That stream acts as a global bidirectional barrier against every blocking stream on the GPU. A barrier here means work on the default stream cannot start until earlier work everywhere finishes, and later work cannot start until it finishes. Engineers debugging Nsight Systems traces recognize this bug immediately. All active streams stop at a vertical wall before and after a tiny helper kernel, and the helper is the one call that did not name a stream.

CUDA provides three distinct stream behaviors, depending on how streams are created. Whether Per-Thread Default Streams are enabled changes which one you get. Figure 11-4 of *AI Systems Performance Engineering* Chapter 11 shows the difference. The table lists the three behaviors and the recommendation for each. Per-Thread Default Streams change the rule so that each host thread gets its own default lane. The lanes stay in order inside each thread, but a lane in one thread no longer blocks a lane in another thread. That helps when third-party libraries omit stream arguments inside a multi-threaded application. An explicit non-blocking stream goes one step further. It never waits for the legacy stream, unless you tell it to wait on an event.

| Stream Type | Creation or Activation Flag | Self-Ordering | Cross-Stream Synchronization Behavior | Production Recommendation |
|---|---|---|---|---|
| Legacy Default Stream (`stream 0` / `cudaStreamLegacy`) | Default when PTDS is not enabled and stream is omitted or `0`. | Strictly FIFO within `stream 0`. | Global bidirectional barrier: any command issued to `stream 0` waits for all prior work in every blocking stream across the GPU to finish, and blocks all subsequent work in those streams until `stream 0` finishes. | Never launch performance-critical kernels or copies on `stream 0`; keep `stream 0` completely idle during training and inference loops. |
| Per-Thread Default Stream (PTDS / `cudaStreamPerThread`) | Compile with `nvcc --default-stream per-thread` or `#define CUDA_API_PER_THREAD_DEFAULT_STREAM 1` before CUDA headers. | Strictly FIFO within each CPU thread's private default stream. | Private per host thread: Thread A's default stream never waits on or blocks Thread B's default stream or explicit streams, though it still synchronizes with `cudaStreamLegacy` if mixed. | Enable in multi-threaded C++ runtimes so third-party libraries omitting stream arguments do not serialize across CPU threads. |
| Explicit Non-Blocking Stream (`cudaStreamNonBlocking`) | `cudaStreamCreateWithFlags(&s, cudaStreamNonBlocking)` | Strictly FIFO within stream `s`. | Completely independent: never implicitly synchronizes with `stream 0` (`cudaStreamLegacy`) or any other stream; synchronizes only when explicitly instructed via `cudaStreamWaitEvent`. | Create named non-blocking streams for all compute, H2D, D2H, P2P, and NCCL or NIXL queues. |

### 3.2 Fine-grained cross-stream events (`Figures 11-5 to 11-7`) and the `cudaLaunchHostFunc` deadlock rule

Consider a producer stream that writes a tensor and a consumer stream that reads it. The consumer must wait for the producer, but nothing else should wait. A host-blocking call is the blunt tool here. Calls such as `cudaDeviceSynchronize()` or `cudaStreamSynchronize()` stall the CPU and drain unrelated GPU queues along with the one you care about. Producer-consumer pipelines need a way to enforce ordering inside the GPU scheduler, without stopping the host thread or unrelated streams. Figures 11-5 through 11-7 in *AI Systems Performance Engineering* Chapter 11 contrast coarse host synchronization with fine-grained CUDA Events. An event is a marker placed in a stream that other streams can wait on.

The four options below run from the bluntest to the most precise.

- Device-wide synchronization with `cudaDeviceSynchronize()` blocks the calling CPU thread until every stream across the entire GPU drains to completion. Never call it inside a hot training or inference loop.
- Single-stream host synchronization, shown in Figure 11-5, blocks the calling CPU thread until all operations in that one stream complete. Reserve it for epoch boundaries or final cleanup.
- Event-based stream synchronization, shown in Figures 11-6 and 11-7, pairs `cudaEventRecord` on the producer stream with `cudaStreamWaitEvent` on the consumer stream. The CPU returns immediately. Only the consumer stream waits, and only until the producer reaches the recorded event. All other GPU streams keep running at full speed.
- Disabling timestamps with `cudaEventDisableTiming` removes the cost of recording times. Use it when an event only orders work and you never measure elapsed time with it.

Use the list above as a decision guide. Start with the event option whenever two streams depend on each other. Reach for a host synchronization only at a natural boundary, such as the end of an epoch. The device-wide option is the one to avoid in any loop that runs many times.

Sometimes the CPU needs to recycle a host memory buffer as soon as a GPU stream finishes a kernel. Blocking on a stream synchronization would be wasteful, and spinning on an event query burns CPU time. The better tool is a callback. You enqueue a host function on the stream by calling `cudaLaunchHostFunc(stream, myHostCallback, userData)`. The rule is strict. Never invoke a device-side CUDA API inside that host callback. That includes a memory copy, an allocation, or a kernel launch. The callback runs on an internal CUDA runtime thread, and the stream waits for the callback to return. A CUDA call inside the callback waits on work that is itself waiting for the callback, so the application deadlocks.

---

## 4. Two-Layer Pipelining: Intra-Kernel Warp Specialization + Inter-Kernel CUDA Streams + Thread Block Clusters

Picture a dual-stage kitchen. One station chops while another cooks, and a third plates. Each station keeps its own queue of orders, and the pass between stations stays busy. Your question is how to build that kitchen when the pipeline lives inside one kernel and the orders come from several streams. This section answers it in two layers.

### 4.1 Layering dual-pipeline 3-role warp specialization with CUDA streams (`warp_specialized_two_pipelines`)

A single pipeline object inside a thread block overlaps global-to-shared loads with compute. But the compute warp and the storer warp still contend if they share a single stage barrier. A barrier here is the point where a group of threads waits for each other. In addition, a single kernel launch still pays host-to-device and device-to-host transfer latency between batches. Combining a dual-pipeline three-role warp-specialized kernel with multiple CUDA Streams solves both bottlenecks at once. Each layer covers the weakness of the other. The inner pipeline keeps the warps of one block busy. The outer streams keep the copies and allocations running beside the kernel.

The roles and buffers are easier to follow as a plan before you read the code. The loader warp is warp 0. It copies the A and B tiles from global memory into Shared Memory with 16-byte vector copies. The compute warp is warp 1. It adds the two input tiles into C and hands the result forward. The storer warp is warp 2. It copies the finished C tile back to global memory. Two pipeline objects connect the three roles. The first one, `pipe_lc`, links the loader to the compute warp. The second one, `pipe_cs`, links the compute warp to the storer warp. Each pipeline has two stages, so the next tile can load while the current one computes.

The configuration numbers in the next block explain how the buffers fit. Each line gives one fact about the layout.

```text
1D tile size:          TILE_SIZE = 1,024 floats per buffer
Alignment guard:       static_assert((TILE_SIZE % (32 * 4)) == 0)
Warp copy step:        32 lanes * 4 floats (sizeof(float4) = 16 B/lane) = 128 floats = 512 B (four 128-byte cache lines)
Shared memory layout:  2 stages * 3 buffers [A0 | B0 | C0 | A1 | B1 | C1] * 1,024 floats * 4 B
                       = 6 * 1,024 * 4 = 24,576 bytes (24.0 KiB << 227,328 bytes Blackwell dynamic SMEM limit)
Host stream driver:    NUM_STREAMS = 2, BATCHES = 8, prefetching next = tile + gridDim.x
```

Here is the complete device kernel and multi-stream host driver from *AI Systems Performance Engineering* Chapter 11. Read the kernel in the order the work flows. The loader warp issues vector copies, two per chunk, using `float4` values, so each lane moves a full 16-byte piece at a time. The loader then commits the stage and waits for it. The compute warp adds the two tiles into C. The storer warp waits on the second pipeline and writes C back out. Each `cta.sync()` is a checkpoint that makes the roles wait for each other before the next role starts. The host driver then spreads the eight batches across two streams, so the copies for one batch can sit beside the kernel for another. If the pipeline stalls, check the stage count first. A depth of 2 lets one tile load while the other tile computes. Each extra stage needs its own buffers in Shared Memory, so more depth costs more of the budget.

```cpp
// Two-level pipeline: Intra-kernel 3-role dual-pipeline (pipe_lc + pipe_cs)
// driven across Inter-kernel non-blocking CUDA streams + cudaMallocAsync
// Source: AI Systems Performance Engineering, Chapter 11
#include <cstdio>
#include <cuda_runtime.h>
#include <cooperative_groups.h>
#include <cuda/pipeline>

namespace cg = cooperative_groups;

// shmem_bytes = 2 (stages) * 3 (buffers) * 1,024 * 4 B = 24,576 B (24 KiB << 227 KB SMEM)
#define TILE_SIZE 1024
#define NUM_STREAMS 2
#define BATCHES 8

static_assert((TILE_SIZE % (32 * 4)) == 0,
              "TILE_SIZE must be a multiple of 128 (32 lanes * 4 floats) for float4 vectorization");

__global__ void warp_specialized_two_pipelines(const float* __restrict__ A_global,
                                               const float* __restrict__ B_global,
                                               float* __restrict__ C_global,
                                               int numTiles) {
    cg::thread_block cta = cg::this_thread_block();
    // Stage s in {0, 1}: [A_s | B_s | C_s], each of length TILE_SIZE (total 6 * TILE_SIZE floats)
    extern __shared__ float shared_mem[];

    using pipe_state = cuda::pipeline_shared_state<cuda::thread_scope_block, 2>;
    __shared__ alignas(pipe_state) unsigned char state_lc_storage[sizeof(pipe_state)];
    __shared__ alignas(pipe_state) unsigned char state_cs_storage[sizeof(pipe_state)];
    auto* state_lc = reinterpret_cast<pipe_state*>(state_lc_storage);
    auto* state_cs = reinterpret_cast<pipe_state*>(state_cs_storage);
    if (threadIdx.x == 0) {
        new (state_lc) pipe_state();
        new (state_cs) pipe_state();
    }
    cta.sync();

    auto pipe_lc = cuda::make_pipeline(cta, state_lc); // loader -> compute (depth 2)
    auto pipe_cs = cuda::make_pipeline(cta, state_cs); // compute -> storer (depth 2)

    const int warp_id = threadIdx.x >> 5; // 0 = loader, 1 = compute, 2 = storer
    const int lane_id = threadIdx.x & 31;
    auto warp = cg::tiled_partition<32>(cta);

    for (int tile = blockIdx.x; tile < numTiles; tile += gridDim.x) {
        const int stage = tile & 1;
        const size_t offset = static_cast<size_t>(tile) * TILE_SIZE;
        float* A_buf = shared_mem + stage * 3 * TILE_SIZE;
        float* B_buf = A_buf + TILE_SIZE;
        float* C_buf = B_buf + TILE_SIZE;

        // 1. Loader warp (warp 0) stages A_buf and B_buf using 16B float4 vectorized memcpy_async
        pipe_lc.producer_acquire();
        if (warp_id == 0) {
            #pragma unroll
            for (int chunk = 0; chunk < TILE_SIZE; chunk += 32 * 4) {
                cuda::memcpy_async(warp,
                    reinterpret_cast<float4*>(A_buf + chunk) + lane_id,
                    reinterpret_cast<const float4*>(A_global + offset + chunk) + lane_id,
                    sizeof(float4), pipe_lc);
                cuda::memcpy_async(warp,
                    reinterpret_cast<float4*>(B_buf + chunk) + lane_id,
                    reinterpret_cast<const float4*>(B_global + offset + chunk) + lane_id,
                    sizeof(float4), pipe_lc);
            }
        }
        pipe_lc.producer_commit();

        // 2. Wait for loader stage and compute C_buf = A_buf + B_buf in warp 1
        pipe_lc.consumer_wait();
        cta.sync();
        if (warp_id == 1) {
            #pragma unroll
            for (int chunk = 0; chunk < TILE_SIZE; chunk += 32) {
                C_buf[chunk + lane_id] = A_buf[chunk + lane_id] + B_buf[chunk + lane_id];
            }
        }
        cta.sync();
        pipe_lc.consumer_release();

        // 3. Handoff computed C_buf from compute (warp 1) to storer (warp 2) via pipe_cs
        pipe_cs.producer_acquire();
        pipe_cs.producer_commit();
        pipe_cs.consumer_wait();
        cta.sync();
        if (warp_id == 2) {
            #pragma unroll
            for (int chunk = 0; chunk < TILE_SIZE; chunk += 32) {
                C_global[offset + chunk + lane_id] = C_buf[chunk + lane_id];
            }
        }
        cta.sync();
        pipe_cs.consumer_release();
    }
}

void runTwoPipelineMultistreamHost() {
    cudaStream_t s[NUM_STREAMS];
    for (int i = 0; i < NUM_STREAMS; ++i)
        cudaStreamCreateWithFlags(&s[i], cudaStreamNonBlocking);

    const size_t bytesPerBatch = TILE_SIZE * sizeof(float);
    float *hA = nullptr, *hB = nullptr, *hC = nullptr;
    cudaMallocHost(&hA, BATCHES * bytesPerBatch); // pinned host memory
    cudaMallocHost(&hB, BATCHES * bytesPerBatch);
    cudaMallocHost(&hC, BATCHES * bytesPerBatch);

    for (int b = 0; b < BATCHES; ++b) {
        cudaStream_t st = s[b % NUM_STREAMS];
        float *dA = nullptr, *dB = nullptr, *dC = nullptr;
        cudaMallocAsync(&dA, bytesPerBatch, st);
        cudaMallocAsync(&dB, bytesPerBatch, st);
        cudaMallocAsync(&dC, bytesPerBatch, st);

        cudaMemcpyAsync(dA, hA + size_t(b) * TILE_SIZE, bytesPerBatch, cudaMemcpyHostToDevice, st);
        cudaMemcpyAsync(dB, hB + size_t(b) * TILE_SIZE, bytesPerBatch, cudaMemcpyHostToDevice, st);

        const dim3 block(96), grid(1); // 3 warps per block
        const size_t shmem = 6 * TILE_SIZE * sizeof(float); // 24,576 bytes
        warp_specialized_two_pipelines<<<grid, block, shmem, st>>>(dA, dB, dC, /*numTiles=*/1);

        cudaMemcpyAsync(hC + size_t(b) * TILE_SIZE, dC, bytesPerBatch, cudaMemcpyDeviceToHost, st);
        cudaFreeAsync(dA, st);
        cudaFreeAsync(dB, st);
        cudaFreeAsync(dC, st);
    }

    for (int i = 0; i < NUM_STREAMS; ++i) {
        cudaStreamSynchronize(s[i]);
        cudaStreamDestroy(s[i]);
    }
    cudaFreeHost(hA); cudaFreeHost(hB); cudaFreeHost(hC);
}
```

### 4.2 Combining Thread Block Clusters, Warp Specialization, and CUDA Streams (`launch_warp_specialized_cluster_pipeline_multistream`)

Full-device cooperative and clustered kernels often reserve every Streaming Multiprocessor on the GPU at once. Because no free Streaming Multiprocessors remain, a second cooperative cluster kernel launched on another stream cannot run on the compute engines at the same moment. Engineers often conclude that multi-stream execution is useless for full-grid cluster kernels. The result is host transfers and memory allocations left exposed between runs.

The source argues that this conclusion is too quick. Even when cooperative cluster kernels take turns on the Streaming Multiprocessors, driving them across two streams through `launch_warp_specialized_cluster_pipeline_multistream` still overlaps every non-compute stage. Think of two chefs who share one oven. The oven is busy with one dish at a time, but the prep and cleanup for both dishes happen off the oven, at the same time. While Stream 0 runs its cluster kernel on the Streaming Multiprocessors, Stream 1 runs stream-ordered allocations and stages the next micro-batch into HBM through a host-to-device asynchronous copy. At the same time, Stream 0 streams the completed output of the previous micro-batch back to the host and frees its buffers asynchronously.

The configuration block below lists the geometry for that launch. Read the cluster size first, then the block size, then the stream count.

```text
Cluster kernel:       warp_specialized_cluster_pipeline
Tile geometry:        TILE_SIZE = 128, TILE_ELEMS = 16,384 floats, 32 rows per CTA
Shared memory / CTA:  shmemBytes = 3 * 16,384 * 4 = 196,608 bytes (192 KiB < 227,328 B dynamic SMEM limit)
Cluster launch grid:  CLUSTER_BLOCKS = 4, blocksPerGrid = prop.multiProcessorCount * 4 = 132 * 4 = 528 blocks
Block and stream cfg: blockDim = 96 (3 warps), NUM_STREAMS = 2
Host launch API:      cudaLaunchKernelExC with cudaLaunchConfig_t (cfg.stream = st, cfg.dynamicSmemBytes = 196608)
Launch attributes:    2 attributes: cudaLaunchAttributeClusterDimension = dim3(4, 1, 1)
                      and cudaLaunchAttributeNonPortableClusterSizeAllowed = 1
Kernel handle lookup: cudaGetKernel(&k, warp_specialized_cluster_pipeline)
```

Once a simpler double-buffered kernel and a multi-stream pipeline already saturate HBM bandwidth, the picture changes. Hiding host-to-device latency is the job that is still left, and adding three-role warp specialization and Thread Block Clusters yields only a few extra percentage points of utilization. Reserve the full three-layer combination for ultra-latency-sensitive inference kernels, where every microsecond of tile handoff matters.

---

## 5. Multi-GPU Compute, P2P (`cudaMemcpyPeerAsync`), `NCCL` Ring All-Reduce, `NIXL`, and `CUDA Graph` Stream Capture

### 5.1 Multi-GPU pipeline parallelism (`cudaMemcpyPeerAsync`) and data parallelism (`NCCL` & `NIXL`)

Suppose you run a model split across two GPUs. GPU 0 finishes its layers and then has to hand activations to GPU 1. If that handoff runs on the same stream as the compute, GPU 0 sits idle during the transfer. The same problem appears in data-parallel training. The backward pass waits for a ring AllReduce, which is a collective where every GPU combines its gradients with its neighbors in a ring, before the next layer can start. In multi-GPU training and inference, running peer-to-peer activation transfers, or gradient reductions, on the same stream as forward and backward compute stalls every GPU at every layer boundary. A pipeline-parallel stage on GPU 0 sits idle while its activations cross NVLink to GPU 1. Data-parallel backward passes wait for ring AllReduce collectives to finish before starting the next layer. Separating compute and communication onto dedicated streams across GPUs lets the compute engines and the network engines run at the same time.

The diagram shows the handoff as two streams on each GPU. The compute stream keeps working on the next batch while the copy stream carries the activations across.

```mermaid
flowchart LR
    subgraph GPU0["GPU 0 (Layers 0-3)"]
      S0A["stream0_A (SM Compute)\nBatch N: Layers 0-3 -> record(eventA)\nImmediately start Batch N+1 Layers 0-3"]
      S1A["stream1_A (DMA Copy Engine, 0 SM cycles)\nwait(eventA) -> cudaMemcpyPeerAsync(GPU 1, GPU 0)\nrecord(eventFromA)"]
      S0A -->|"eventA (DisableTiming)"| S1A
    end
    subgraph GPU1["GPU 1 (Layers 4-7)"]
      S0B["stream0_B (SM / Prefetch)\nPrefetch weights / Batch N-1 work"]
      S1B["stream1_B (SM Compute)\nwait(eventFromA) -> Batch N: Layers 4-7"]
    end
    S1A -->|"NVLink / PCIe P2P + eventFromA"| S1B
```

*AI Systems Performance Engineering* Chapter 11 details three multi-GPU overlap patterns across NVLink, PCIe, and RDMA interconnects. NVLink and PCIe are the links between GPUs and the host. RDMA is remote direct memory access, which moves data between machines without involving the remote CPU. The first pattern is two-GPU pipeline parallelism. Layers 0-3 run on GPU 0, and layers 4-7 run on GPU 1. On GPU 0, the compute stream runs `myTransformerLayers0to3`, records an event with timing disabled, and immediately starts the next micro-batch. Meanwhile, a communication stream waits on that event, calls `cudaMemcpyPeerAsync` to push activations to GPU 1, and records a completion event. GPU 1's compute stream waits on that completion event before it runs `myTransformerLayers4to7`. Because the peer copy runs on GPU 0's copy engine, using 0 SM cycles, GPU 0 computes the next batch at 100% speed during the transfer.

The second pattern is data parallelism. Backward compute overlaps with NCCL ring AllReduce collectives, as shown in Figure 11-8 across 4 GPUs and 4 contiguous tensor chunks labeled Chunks 1-4. Unlike peer Direct Memory Access copies, NCCL collectives run as device kernels on Streaming Multiprocessors. They are tuned as low-occupancy kernels, which means they saturate link bandwidth using only a few thread blocks. Some collectives instead offload reductions to NVIDIA SHARP switch hardware, which performs the reduction inside the network switch. Frameworks launch `ncclAllReduce` on a dedicated high-priority communication stream, and CUDA Events coordinate it so that backward compute overlaps gradient communication.

The third pattern is disaggregated serving. Prefill and decode run on different GPUs in that setup, so the KV-cache has to travel between them. The KV-cache holds the attention keys and values of earlier tokens. The NVIDIA Inference Xfer Library, NIXL, moves that cache on a dedicated high-priority `nixlCommStream`. NIXL replaces manual peer copies with chunked, pipelined transfers across NVLink, GPUDirect RDMA, and NVMe storage. High-priority copy commands can then preempt lower-priority queues, without consuming upfront Streaming Multiprocessor resources. The three patterns share one idea. Each one moves the slow transfer off the compute stream, so the compute stream does not wait for the network or for the second GPU.

### 5.2 Capturing a multi-stream iteration into a `CUDA Graph` (`cudaStreamCaptureModeGlobal`)

Even when compute and NCCL streams overlap on the GPU, the host still has to launch them. Launching dozens of small kernels, events, and collective calls from Python every step can bottleneck on host CPU driver overhead. Picture a cook who must call out every ticket one by one, when a single printed order sheet would do. Capturing the entire multi-stream dependency graph into a single CUDA Graph removes that CPU launch overhead. It keeps every cross-stream overlap edge, because the edges are part of the recorded graph.

To capture across multiple streams, begin capture on the primary stream using `cudaStreamCaptureModeGlobal`. Fork work onto secondary streams with CUDA Events, and join all secondary streams back into the primary stream before calling `cudaStreamEndCapture`. Fork means the secondary stream waits on an event from the primary stream, and join means the primary stream waits on an event from the secondary stream. Once the graph is instantiated, one `cudaGraphLaunch` call replays the entire multi-stream compute and communication step. Capture works by recording instead of running. During capture, the calls are written into a graph and are not executed right away. That is why the graph can be replayed later without the host issuing every call again. The trade-off is that a recorded graph has a fixed shape. A step whose structure changes from one iteration to the next has to be captured again, or it has to run outside the graph.

```cpp
// Capturing a multi-stream compute + NCCL communication DAG into a single CUDA Graph
// Source: AI Systems Performance Engineering, Chapter 11
cudaGraph_t graph;
// CRITICAL: Use cudaStreamCaptureModeGlobal when capturing across multiple streams (streamA + streamB)
cudaStreamBeginCapture(streamA, cudaStreamCaptureModeGlobal);

computeGradientsLayer1<<<grid, block, 0, streamA>>>(/* ... */);
cudaEventRecord(ev1, streamA);
cudaStreamWaitEvent(streamB, ev1, 0);
ncclAllReduce(grad1, grad1, count1, ncclFloat, ncclSum, comm, streamB);

computeGradientsLayer2<<<grid, block, 0, streamA>>>(/* ... */);
cudaEventRecord(ev2, streamA);
cudaStreamWaitEvent(streamB, ev2, 0);
ncclAllReduce(grad2, grad2, count2, ncclFloat, ncclSum, comm, streamB);

cudaStreamWaitEvent(streamA, evAllDone, 0); // rejoin streamB into streamA before ending capture
cudaStreamEndCapture(streamA, &graph);
```

---

## 6. Programmatic Dependent Launch (`PDL`) and Combining `PDL` + Thread Block Clusters + Warp Specialization

### 6.1 Overlapping Kernel B's prologue with Kernel A's epilogue in the same stream

Normally, two kernels enqueued into the same CUDA Stream execute strictly back to back. Think of two cars in a single-lane tunnel. The second car waits for the first to exit completely. The hardware scheduler will not start the secondary kernel on any Streaming Multiprocessor until every thread block of the primary kernel has finished its epilogue and exited. The epilogue is the final cleanup work at the end of a kernel. During the tail wave of the primary kernel, most Streaming Multiprocessors sit idle while the secondary kernel waits behind the stream boundary.

Programmatic Dependent Launch, supported on Hopper and Blackwell GPUs, breaks that strict boundary inside a single stream without CPU intervention. Figure 11-9 of *AI Systems Performance Engineering* Chapter 11 shows the timing. As soon as the primary kernel finishes writing the global memory data that the secondary kernel needs, the primary kernel signals the hardware command processor. The GPU then starts the secondary kernel's non-dependent prologue on the free Streaming Multiprocessors. The prologue is the setup that does not need the primary kernel's data. The primary kernel keeps running its remaining epilogue in the meantime.

The diagram shows both kernels on one stream. The trigger in kernel A and the synchronization in kernel B are the handshake that makes the overlap safe.

```mermaid
flowchart LR
    subgraph KA["Primary Kernel A (stream)"]
      A1["1. Main Compute & Global Memory Writes\n(e.g., 1.6 ms)"]
      A2["2. cudaTriggerProgrammaticLaunchCompletion()\nSignals memory flush complete"]
      A3["3. Kernel A Epilogue / Housekeeping\n(e.g., 0.4 ms — runs in parallel with B)"]
      A1 --> A2 --> A3
    end
    subgraph KB["Secondary Kernel B (same stream, launched via cudaLaunchKernelExC)"]
      B1["1. Kernel B Prologue / Preamble\nStarts early while A is in epilogue"]
      B2["2. cudaGridDependencySynchronize()\nWaits for A's trigger + memory flush"]
      B3["3. Dependent Compute on d_ptr\n(total 2.0 ms -> stream finishes in 3.6 ms vs 4.0 ms)"]
      B1 --> B2 --> B3
    end
    A2 ==>|"Device-side PDL handoff (0 CPU overhead)"| B2
```

Implementing Programmatic Dependent Launch requires a three-part contract across the primary kernel, the secondary kernel, and the host launch. Each part has one job, and all three must be present.

1. In the primary kernel, call `cudaTriggerProgrammaticLaunchCompletion()` once all global memory writes needed by the secondary kernel are complete. This call flushes global writes and tells the hardware scheduler that the secondary kernel may launch while the primary kernel is still in its epilogue.
2. In the secondary kernel, run any independent preamble or constant setup first. Then call `cudaGridDependencySynchronize()` before reading any global memory that the primary kernel wrote.
3. On the host, set `cudaLaunchAttributeProgrammaticStreamSerialization` to 1 in the secondary kernel's launch configuration, and enqueue the launch with `cudaLaunchKernelExC`.

The table compares the two modes with the same kernels. The only change is whether the epilogue overlaps the start of the secondary kernel. Read the second row closely. The secondary kernel now starts at the 1.6 ms mark, while the primary kernel's 0.4 ms epilogue is still running. The secondary kernel's own work is unchanged. Only its start moves earlier, and that is where the saving comes from.

| Execution Mode (`model_programmatic_dependent_launch`) | Primary Main + Epilogue | Secondary Duration | Total Stream Time | Time Saved |
|---|---|---|---|---|
| Standard back-to-back stream serialization | 1.6 ms main + 0.4 ms epilogue | 2.0 ms after epilogue finishes | 4.0 ms | 0.0 ms |
| Programmatic Dependent Launch enabled | 1.6 ms main + 0.4 ms overlapped epilogue | 2.0 ms starting at 1.6 ms mark | 3.6 ms | 0.4 ms |

### 6.2 Combining `PDL` + Thread Block Clusters (`__cluster_dims__(2,1,1)`) + Warp Specialization (`primary_gemm` → `secondary_gemm`, `Figures 11-10 & 11-11`)

Consider a Transformer MLP block, which chains two matrix multiplications back to back. These are the up-projection and the down-projection. Running those two GEMM kernels without overlap leaves memory buses idle during compute, and it leaves Streaming Multiprocessors idle during kernel handoffs. GEMM is general matrix multiplication, the operation that dominates Transformer compute. Figures 11-10 and 11-11 in *AI Systems Performance Engineering* Chapter 11 combine Programmatic Dependent Launch, Thread Block Clusters, and warp specialization in a `primary_gemm` to `secondary_gemm` pipeline.

The configuration block lists the sizes and the handoff points for that pipeline.

```text
Cluster dimension:     __cluster_dims__(2, 1, 1) (2 CTAs per cluster)
Tile dimensions:       TILE_M = 128, TILE_K = 128, TILE_N = 128 (16,384 floats per tile)
Static shared memory:  tileA[128 * 128] (65,536 B) + tileB[128 * 128] (65,536 B)
                       = 2 * 16,384 * 4 B = 131,072 bytes (128 KiB) per CTA
Inter-kernel handoff:  primary_gemm calls cudaTriggerProgrammaticLaunchCompletion() after cluster.sync()
                       secondary_gemm calls cudaGridDependencySynchronize() before consuming C
```

Each kernel uses the compile-time attribute `__cluster_dims__(2, 1, 1)` to co-schedule pairs of thread blocks within a Graphics Processing Cluster, and it synchronizes them through cluster barrier instructions. Inside each block, producer warps stage tiles into shared memory while consumer warps compute matrix-multiply-accumulate instructions. On Blackwell GPUs, producer warps can pair descriptor-based Tensor Memory Accelerator multicast, written as `cp.async.bulk.tensor`, with descriptor-based Tensor Memory Accelerator reductions, written as `cp.reduce.async.bulk.tensor`. That fuses small reductions into the copy engine and lowers register pressure. Put simply, the cluster pair cooperates inside each kernel, and Programmatic Dependent Launch cooperates between the two kernels. Each layer removes a different kind of waiting. Clusters remove waiting between blocks. Programmatic Dependent Launch removes waiting between kernels. Warp specialization removes waiting inside a block. When all three appear in one pipeline, the GPU spends less of its time in the gaps between those steps.

The code below shows the handoff between the two kernels. Read `primary_gemm` first, then the trigger, and then the wait at the top of `secondary_gemm`.

```cpp
// Combining Programmatic Dependent Launch (PDL), Thread Block Clusters (__cluster_dims__(2,1,1)),
// and Warp Specialization in primary_gemm -> secondary_gemm
// Source: AI Systems Performance Engineering, Chapter 11
#include <cstdio>
#include <cuda_runtime.h>
#include <cuda_runtime_api.h>
#include <cooperative_groups.h>
#include <cuda/barrier>
#include <cuda/pipeline>

namespace cg = cooperative_groups;

constexpr int TILE_M = 128;
constexpr int TILE_K = 128;
constexpr int TILE_N = 128; // tileA + tileB = 2 * 16,384 * 4 B = 131,072 B (128 KiB) SMEM

__device__ void do_compute(const float* tileA, const float* tileB, float* C) {}

__global__ __cluster_dims__(2, 1, 1) // Compile-time cluster of 2 CTAs
void primary_gemm(const float* __restrict__ A,
                  const float* __restrict__ B,
                  float* __restrict__ C,
                  int M, int N, int K) {
    cg::cluster_group cluster = cg::this_cluster();
    cg::thread_block cta = cg::this_thread_block();

    int tid = threadIdx.x + threadIdx.y * blockDim.x;
    int warpId = tid / warpSize;
    const int numProducerWarps = 1;

    __shared__ float tileA[TILE_M * TILE_K];
    __shared__ float tileB[TILE_K * TILE_N];
    __shared__ cuda::pipeline_shared_state<cuda::thread_scope_block, 1> pipe_state;
    auto pipe = cuda::make_pipeline(cta, &pipe_state);
    auto warp = cg::tiled_partition<32>(cta);

    // 1. CTA-uniform pipeline acquire; producer warp issues async copies
    pipe.producer_acquire();
    if (warpId < numProducerWarps) {
        cuda::memcpy_async(warp, tileA, A, TILE_M * TILE_K * sizeof(float), pipe);
        cuda::memcpy_async(warp, tileB, B, TILE_K * TILE_N * sizeof(float), pipe);
    }
    pipe.producer_commit();
    cta.sync();
    pipe.consumer_wait();

    // 2. Compute on the staged tile and synchronize across the 2-CTA cluster
    do_compute(tileA, tileB, C);
    cluster.sync();

    // 3. Signal dependent secondary_gemm via PDL that main writes/flushes are complete
    cudaTriggerProgrammaticLaunchCompletion();

    // 4. Remaining epilogue work runs concurrently with secondary_gemm's startup
}

__global__ __cluster_dims__(2, 1, 1)
void secondary_gemm(const float* __restrict__ A,
                    const float* __restrict__ B,
                    float* __restrict__ C,
                    int M, int N, int K) {
    // Wait for primary_gemm's PDL signal and global memory flush before reading shared data
    cudaGridDependencySynchronize();
    // Proceed with warp-specialized cluster GEMM on the dependent layer/tile...
}
```

---

## 7. Commands and Configurations That Matter

Multi-threaded applications can silently serialize on the legacy default stream when no one passes the right compiler flags or profiler options. The overlap bug then stays invisible until a trace shows the wall. The commands in this section are the ones to run when you suspect that. Start with the environment settings, then the compile line, then the trace. Each step gives you a clearer picture than the one before it. All commands below follow *AI Systems Performance Engineering* Chapter 11. Shell commands that need an attached Hopper or Blackwell GPU were not run on live hardware for this handbook.

### 7.1 Enable Per-Thread Default Streams (`PTDS`), compile `PDL` + Cluster kernels, and trace multi-stream overlap in `nsys` (untested here)

Use `--default-stream per-thread` during compilation to isolate default streams per host thread. Each thread then gets its own private default stream, so one thread's stray call does not stop the others. Export the stream-ordered allocator configuration for PyTorch workloads. Then run Nsight Systems to inspect multi-stream overlap on the timeline. Nsight Systems is NVIDIA's timeline profiler, and it is the tool that shows the walls and gaps in the first place.

```bash
# 1. Compile with Per-Thread Default Stream (PTDS) enabled and Hopper/Blackwell arch (untested here)
nvcc -O3 -std=c++20 -arch=sm_100a --default-stream per-thread -lineinfo \
     pdl_cluster_gemm.cu -o pdl_cluster_gemm

# 2. Enable CUDA's stream-ordered memory allocator in PyTorch (untested here)
export PYTORCH_ALLOC_CONF=backend:cudaMallocAsync

# 3. Trace multi-stream H2D/Compute/D2H overlap, cudaMallocAsync, NCCL, and PDL in Nsight Systems (untested here)
nsys profile --trace=cuda,nvtx,osrt --sample=none -o multistream_pdl_report ./pdl_cluster_gemm
nsys stats multistream_pdl_report.nsys-rep
```

---

## 8. How It Fails: Six Multi-Stream, Allocator, Callback, and `PDL` Failure Modes

When a multi-stream pipeline runs slower than expected or hangs in production, the root cause almost always traces back to one of six synchronization or memory-staging mistakes. Most of them are small. Each one takes away the overlap that the rest of the chapter depends on. The table below pairs each failure mode with its profiler symptom, root cause, and fix.

Read the symptom column first. A wall on the timeline points to the legacy stream. A slow copy that blocks the host points to pageable memory. A hang inside the runtime points to a callback that calls back into CUDA. Two of the six rows come up most often in practice. Legacy allocation and pageable host memory are easy to add by accident and hard to notice without a timeline. If you find one, check the other one too.

| # | Failure Mode | Production or Profiler Symptom | Root Cause | Fix |
|---|---|---|---|---|
| 1 | Stray operations on the legacy default stream (`stream 0`) | Nsight Systems timeline shows all `stream1` and `stream2` kernels and `cudaMemcpyAsync` transfers stopping at a wall before and after a single helper kernel. | A kernel or copy was launched without an explicit stream into `cudaStreamLegacy` / `stream 0`, or custom streams were created with blocking `cudaStreamCreate` instead of `cudaStreamNonBlocking`. | Create all streams with `cudaStreamCreateWithFlags(&s, cudaStreamNonBlocking)`, pass explicit streams to every CUDA, cuBLAS, and NCCL call, and compile multi-threaded apps with `--default-stream per-thread`. |
| 2 | Passing pageable host memory to `cudaMemcpyAsync` | `cudaMemcpyAsync` blocks the host CPU thread and fails to overlap with kernel execution on that stream, degrading our 8-batch model from 18.16 ms to 32.16 ms. | DMA engines require physical page-locked host addresses; pageable memory forces a synchronous CPU staging copy into a temporary pinned buffer. | Allocate host staging buffers with `cudaMallocHost` or `cudaHostAlloc` in C++ or set `pin_memory=True` on PyTorch `DataLoader`. |
| 3 | Calling blocking `cudaMalloc` or `cudaFree` inside a multi-stream or multi-GPU loop | Variable-length LLM batches growing from 512 to 1,024 tokens or 16 MB scratch allocations cause periodic multi-millisecond bubbles across all streams. | Legacy `cudaMalloc` and `cudaFree` synchronize the entire GPU device before returning, as shown in Figure 11-3. | Replace with `cudaMallocAsync` and `cudaFreeAsync`, set `cudaMemPoolAttrReleaseThreshold` to `prop.totalGlobalMem / 2`, and export `PYTORCH_ALLOC_CONF=backend:cudaMallocAsync`. |
| 4 | Calling device CUDA APIs inside a `cudaLaunchHostFunc` callback | Application deadlocks permanently inside the CUDA runtime when a stream reaches a registered host callback. | The callback runs on an internal CUDA runtime thread while the stream waits for the callback to finish; invoking `cudaMemcpy` or a kernel launch inside the callback creates a circular wait. | Restrict `cudaLaunchHostFunc` callbacks strictly to pure CPU operations such as recycling host memory or notifying a CPU worker thread. |
| 5 | Using default capture mode instead of `cudaStreamCaptureModeGlobal` across multi-stream NCCL and compute | `cudaStreamEndCapture` fails or omits cross-stream `ncclAllReduce` operations enqueued on `streamB` when capturing from `streamA`. | Without `cudaStreamCaptureModeGlobal` and event fork-join edges via `cudaEventRecord` and `cudaStreamWaitEvent`, multi-stream operations are not captured into the unified graph. | Begin capture with `cudaStreamBeginCapture(streamA, cudaStreamCaptureModeGlobal)` and fork and join `streamB` into `streamA` using CUDA Events before `cudaStreamEndCapture`. |
| 6 | Firing `cudaTriggerProgrammaticLaunchCompletion()` before global memory writes are produced | Secondary `kernel_B` reads corrupted or incomplete values from `d_ptr` after returning from `cudaGridDependencySynchronize()`. | Primary `kernel_A` called `cudaTriggerProgrammaticLaunchCompletion()` before finishing the global-memory stores that `kernel_B` depends on. | Call `cudaTriggerProgrammaticLaunchCompletion()` in `kernel_A` only after all data required by `kernel_B` has been written and synchronized across participating blocks or clusters. |

---

## 9. Hands-On Lab: Verify 3-Way Stream Overlap, Stream-Ordered Pools, Dual-Pipeline Warp Specialization, Cluster Streams, and `PDL`

Before you rely on the timeline numbers in this chapter, you want to confirm the arithmetic behind them. This lab does that check. It verifies the three-way stream overlap timeline model, stream-ordered pool sizing, dual-pipeline warp specialization geometry, multi-stream Thread Block Cluster launches, and Programmatic Dependent Launch calculations. It runs deterministically on any Linux machine or Nebius GPU VM with Python 3.10 or newer, using standard library Python only. The compiler and profiler commands in Section 7 were not run on a live cluster for this handbook, so this lab is the part you can run first.

Run `code/part10/inter_kernel_pipelining_lab.py` from the repository root. If a line prints FAIL, do not edit the chapter's numbers to match it. Find the rule that disagrees, and check that rule against the source first.

```bash
python3 code/part10/inter_kernel_pipelining_lab.py
```

Expected output with 25 passed and 0 failed tests is shown below. Each line names the check it covers, so a failure points to the rule that broke.

```text
=== Chapter 10.17 Lab: Inter-Kernel Pipelining, Sync & Stream-Ordered Allocation (ASP Ch 11) ===
  [PASS] ASP Ch11 3-way stream overlap: 8 batches serialize at 36.0 ms (4.5 ms/batch) vs 18.16 ms overlapped (1.98x speedup) with pinned memory + cudaMallocAsync
  [PASS] ASP Ch11 Pageable host memory penalty: Calling cudaMemcpyAsync on pageable memory forces staging copy and degrades 8-batch time to 32.16 ms
  [PASS] ASP Ch11 Blocking cudaMalloc penalty: Legacy cudaMalloc forces global device sync across all streams (36.0 ms vs 18.16 ms)
  [PASS] ASP Ch11 Saturation & residency limits: 2 concurrent streams on a saturated engine get 50.0% each; max concurrent resident grids == 128
  [PASS] ASP Ch11 Figure 11-3: Per-stream attention scratch allocation reserves 16 MB (16,777,216 B) via cudaMallocAsync without stalling other streams
  [PASS] ASP Ch11 Variable-length LLM sequences: Batch N (512 tokens) -> Batch N+1 (1,024 tokens) doubles scratch requirement (2.0x) in stream order
  [PASS] ASP Ch11 cudaMemPoolAttrReleaseThreshold: Setting release threshold to totalGlobalMem / 2 retains 96 GiB in pool on a 192 GiB GPU
  [PASS] ASP Ch11 PyTorch & layerwise LLM pipelining: PYTORCH_ALLOC_CONF=backend:cudaMallocAsync and stream 0 (layers 0-5) + stream 1 (layers 6-11)
  [PASS] ASP Ch11 warp_specialized_two_pipelines: 2 stages * 3 buffers ([A0|B0|C0|A1|B1|C1]) * 1,024 floats * 4 B == 24,576 B (24 KiB << 227,328 B SMEM)
  [PASS] ASP Ch11 warp_specialized_two_pipelines: blockDim=96 (3 warps: loader 0, compute 1, storer 2) with 2 pipelines (pipe_lc, pipe_cs) across NUM_STREAMS=2, BATCHES=8
  [PASS] ASP Ch11 float4 alignment guard: TILE_SIZE=1,024 is a multiple of 128 (32 lanes * 4 floats = 128 B coalesced warp copy)
  [PASS] ASP Ch11 launch_warp_specialized_cluster_pipeline_multistream: TILE_SIZE=128 (TILE_ELEMS=16,384) uses 3 * 16,384 * 4 B == 196,608 B (192 KiB < 227,328 B)
  [PASS] ASP Ch11 Cluster multistream geometry: 132 SMs * CLUSTER_BLOCKS=4 == 528 blocksPerGrid, blockDim=96 (3 warps), 32 rows/block
  [PASS] ASP Ch11 Cooperative cluster stream nuance: Cooperative kernels serialize on SMs across streams while still overlapping H2D, D2H, and cudaMallocAsync/cudaFreeAsync
  [PASS] ASP Ch11 Programmatic Dependent Launch (PDL): Overlapping secondary_gemm (2.0 ms) with primary_gemm epilogue (0.4 ms after 1.6 ms main) cuts stream time 4.0 -> 3.6 ms (saves 0.4 ms)
  [PASS] ASP Ch11 PDL API contract: cudaTriggerProgrammaticLaunchCompletion -> cudaGridDependencySynchronize + cudaLaunchAttributeProgrammaticStreamSerialization
  [PASS] ASP Ch11 primary_gemm + __cluster_dims__(2,1,1): tileA[128*128] + tileB[128*128] uses 131,072 B (128 KiB) static SMEM across a 2-CTA cluster
  [PASS] Rejects TILE_SIZE not divisible by 128 (32 * 4) in warp_specialized_two_pipelines
  [PASS] Rejects batchLength not divisible by TILE_ELEMS (16,384) in cluster multistream launch
  [PASS] Rejects cluster TILE_SIZE whose 3 tiles exceed 227,328 B dynamic SMEM limit
  [PASS] Rejects non-positive num_batches in stream pipeline simulator
  [PASS] Rejects invalid release threshold fraction > 1.0 in stream-ordered pool planner
  [PASS] Rejects negative primary_epilogue_ms in PDL model
  [PASS] ASP Ch11 Multi-GPU pipeline & NCCL ring: 2-GPU Transformer split (layers 0-3 on GPU 0, layers 4-7 on GPU 1) and 4-GPU NCCL ring with 4 chunks (1-4)
  [PASS] ASP Ch11 Figure 11-1: 5 kernels (ker_1..3 on stream1, ker_A..B on stream2) launched with grid(128), block(256) == 32,768 threads/kernel

Summary: 25 passed, 0 failed (total 25)
```

---

## Exercises

Each exercise below uses one situation from this chapter. Work through them in order, since the later ones reuse the timing and sizing math from the earlier ones. Write each answer in one line before you check the chapter. The arithmetic is short, but the units change between bytes, KiB, and GiB, so note the unit each time.

1. Start with the 8-batch timeline model in Section 1.2. Calculate the total execution time for fully overlapped streams with pinned host memory and stream-ordered allocation. Then calculate the total for pageable host memory. Finally, calculate the total for blocking allocation. Compare each speedup with the serial baseline.
2. Two streams share a saturated engine. What per-stream throughput share does each one get? Then state the hardware limit on concurrent resident grids. On a 192 GiB GPU, what is half of total global memory in bytes? What is the exact byte size of a 16 MB per-stream attention scratch buffer? When sequence length grows from 512 to 1,024 tokens, what is the scratch growth factor?
3. Explain how the legacy default stream interacts with other streams. Name both ways to enable Per-Thread Default Streams, one through a compiler flag and one through a preprocessor macro. Then explain why a device copy inside a `cudaLaunchHostFunc` callback deadlocks.
4. Take a 1,024-float tile across 2 stages and 3 buffers per stage. What is the dynamic shared memory footprint in bytes? What is it in KiB? Why must the tile size be a multiple of 128? How do the two pipelines coordinate the 3 warps when the block has 96 threads?
5. Take a 128-by-128 tile of 16,384 floats, a 4-block cluster, and 132 Streaming Multiprocessors across 2 streams. How many shared memory bytes does each block need? How many blocks are in each grid? How many rows does each block handle? Why does launching across 2 streams still improve throughput when the cooperative cluster kernels take turns on the Streaming Multiprocessors?
6. A primary GEMM has 1.6 ms of main work and 0.4 ms of epilogue. The secondary GEMM has 2.0 ms of total work and uses 128-by-128 tiles. What is the total stream time with Programmatic Dependent Launch? What is it without? What is the static shared memory footprint per block for those tiles? Name the API calls or attributes needed on the primary kernel, the secondary kernel, and the host launch.

---

## Checkpoint questions (20)

<details>
<summary>**1. How many dedicated DMA copy engines do modern NVIDIA GPUs provide alongside the SM compute pipeline, and how does 3-way stream overlap use them?**</summary>

```text
Modern GPUs provide at least two independent Direct Memory Access copy engines where `deviceProp.asyncEngineCount >= 2`, with one engine for host-to-device copies and one for device-to-host copies. In a three-way pipeline, Stream 0 runs the compute kernel for the current batch on the Streaming Multiprocessors while Stream 1 copies the next batch host-to-device on copy engine 0 and Stream 2 copies the previous batch device-to-host on copy engine 1.
```
</details>

<details>
<summary>**2. What happens to `cudaMemcpyAsync` when you pass a pageable (non-pinned) host pointer?**</summary>

The CUDA runtime must first perform a synchronous host-side staging copy into an internal page-locked buffer. That staging copy blocks the calling CPU thread and serializes the transfer on the enqueuing stream, preventing overlap with kernel execution on that stream. Always use `cudaMallocHost` in C++ or `pin_memory=True` in PyTorch.
</details>

<details>
<summary>**3. What happens when two concurrent streams launch kernels that each demand 100% of a saturated GPU resource, and what is the hard hardware limit on concurrent resident grids?**</summary>

When compute throughput or memory bandwidth is already 100% saturated. Two concurrent operations contend for the same bottleneck and each runs at roughly 50% throughput, yielding no net speedup. Across the entire device, modern GPUs enforce a hard hardware limit of 128 concurrently executing kernel grids.
</details>

<details>
<summary>**4. Why does legacy `cudaMalloc` / `cudaFree` break multi-stream pipelines, and how does `cudaMallocAsync` / `cudaFreeAsync` solve it?**</summary>

Legacy blocking allocation and deallocation calls are device-wide operations that force a global synchronization across every stream on the GPU. Calling `cudaMallocAsync` and `cudaFreeAsync` enqueues allocation. Deallocation requests as stream-ordered items inside a device memory pool, synchronizing only within the requesting stream while all other streams continue executing.
</details>

<details>
<summary>**5. How do you enable CUDA's stream-ordered allocator in PyTorch, and how does it differ from PyTorch's default caching allocator?**</summary>

Set `PYTORCH_ALLOC_CONF=backend:cudaMallocAsync`. PyTorch's default caching allocator is stream-aware on cache hits. Synchronizes the device only when a cache miss triggers an OS allocation. Whereas the stream-ordered backend delegates directly to CUDA's memory pool to reduce cross-stream fragmentation and improve buffer reuse.
</details>

<details>
<summary>**6. What does `cudaMemPoolSetAttribute(pool, cudaMemPoolAttrReleaseThreshold, &threshold)` control?**</summary>

It sets the byte threshold of reserved physical memory that the device memory pool retains. Asynchronous free calls before releasing unused pages back to the operating system. Setting half of total global memory retains 96 GiB on a 192 GiB GPU, avoiding repeated expensive OS mapping round-trips during high-churn mini-batch loops.
</details>

<details>
<summary>**7. Describe three LLM training/inference scenarios where `cudaMallocAsync` prevents global device stalls.**</summary>

1. Per-batch attention scratch workspaces that allocate a 16 MB temporary buffer per stream for softmax and attention intermediates, as shown in Figure 11-3.
2. Variable-length sequence batches growing from 512 to 1,024 tokens and growing autoregressive decode KV caches that dynamically resize buffers in stream order.
```text
3. Layerwise LLM pipelining across streams where stream 0 computes layers 0-5 and allocates the next batch's activations asynchronously while stream 1 computes layers 6-11 on the prior batch.
```
</details>

<details>
<summary>**8. What are the two implicit synchronization rules of the legacy default stream (`stream 0` / `cudaStreamLegacy`)?**</summary>

1. Implicit self-synchronization: operations issued to the legacy default stream execute strictly sequentially in FIFO order.
2. Implicit cross-stream global barrier: any operation issued to the legacy default stream waits for all prior work in every blocking stream. The GPU to finish, and blocks any subsequent work in those streams until it finishes.
</details>

<details>
<summary>**9. How do Per-Thread Default Streams (`PTDS` / `cudaStreamPerThread`) work, and what are the two ways to enable them?**</summary>

With Per-Thread Default Streams enabled, each host CPU thread gets its own private default stream that does not wait on. Block other threads' default streams, as shown in Figure 11-4. Enable it by compiling with `nvcc --default-stream per-thread` or defining `CUDA_API_PER_THREAD_DEFAULT_STREAM=1` before including any CUDA headers.
</details>

<details>
<summary>**10. Why should you always create explicit streams with `cudaStreamCreateWithFlags(&s, cudaStreamNonBlocking)`?**</summary>

Passing `cudaStreamNonBlocking` disables the implicit synchronization barrier between the new stream and the legacy default stream. That guarantees an accidental or third-party call on the legacy default stream will not stall your explicit stream.
</details>

<details>
<summary>**11. Contrast `cudaDeviceSynchronize()`, `cudaStreamSynchronize(s)`, and `cudaEventRecord(ev, s0)` + `cudaStreamWaitEvent(s1, ev, 0)`, and state when to pass `cudaEventDisableTiming`.**</summary>

- Device synchronization blocks the CPU until all streams on the GPU finish.
- Stream synchronization blocks the CPU until that single stream finishes, as shown in Figure 11-5.
- Recording an event on a producer stream and waiting on it with `cudaStreamWaitEvent` on a consumer stream returns control to the CPU immediately. Stalls only the consumer stream on the GPU, as shown in Figure 11-6. Pass `cudaEventDisableTiming` when creating the event if you only need synchronization and not elapsed-time timestamps.
</details>

<details>
<summary>**12. What is `cudaLaunchHostFunc`, and why must you never call `cudaMemcpy` or launch a kernel inside its callback?**</summary>

`cudaLaunchHostFunc` enqueues a CPU callback function to run automatically on a host thread once prior work in a CUDA Stream completes. Because the callback executes on an internal thread managed by the CUDA runtime. The GPU stream waits for the callback to finish, calling any device CUDA API inside the callback creates a circular wait and deadlocks.
</details>

<details>
<summary>**13. How does `warp_specialized_two_pipelines` organize its Shared Memory (`24,576 B`) and its two `<cuda/pipeline>` objects (`pipe_lc` and `pipe_cs`)?**</summary>

```text
It launches 96 threads per block for 3 warps: loader warp 0, compute warp 1, and storer warp 2. Shared memory holds 2 stages by 3 buffers of 1,024 floats, totaling 24,576 bytes or 24 KiB of dynamic shared memory. Pipeline `pipe_lc` with depth 2 coordinates loader-to-compute handoffs, while `pipe_cs` with depth 2 coordinates compute-to-storer handoffs.
```
</details>

<details>
<summary>**14. Why does `warp_specialized_two_pipelines` enforce `static_assert((TILE_SIZE % (32 * 4)) == 0)`?**</summary>

```text
Each warp has 32 lanes and each lane copies a 16-byte `float4` of 4 floats per asynchronous copy instruction, transferring 128 floats or 512 bytes across the 32-lane warp. Requiring the tile size of 1,024 to be a multiple of 128 ensures every unrolled warp copy iteration is 16-byte aligned without scalar tail loops.
```
</details>

<details>
<summary>**15. In `launch_warp_specialized_cluster_pipeline_multistream`, why do cooperative cluster kernels serialize across streams on the SMs, and why does `NUM_STREAMS = 2` still improve throughput?**</summary>

```text
A full-device cluster launch of 528 blocks pins block slots across all Streaming Multiprocessors simultaneously, so Stream 1's kernel must wait until Stream 0's kernel finishes on the Streaming Multiprocessors. Using two streams still overlaps Stream 1's asynchronous allocations and host-to-device copies, plus Stream 0's device-to-host copies and asynchronous frees, behind active kernel execution so the next cluster kernel starts with zero staging delay.
```
</details>

<details>
<summary>**16. In a 2-GPU pipeline-parallel Transformer (`Layers 0–3` on GPU 0, `Layers 4–7` on GPU 1), why doesn't `cudaMemcpyPeerAsync` slow down GPU 0's compute stream for Batch `N + 1`?**</summary>

`cudaMemcpyPeerAsync` executes entirely on GPU 0's dedicated Direct Memory Access copy engine and consumes 0 Streaming Multiprocessor cycles. That allows GPU 0's Streaming Multiprocessors on the compute stream to begin computing the next micro-batch immediately after recording the handoff event.
</details>

<details>
<summary>**17. How do `NCCL` and `NIXL` differ from `cudaMemcpyPeerAsync` in how they use SMs, DMA engines, and stream priorities?**</summary>

```text
Peer asynchronous copies run purely on copy engines using 0 Streaming Multiprocessors. NCCL collectives such as the 4-GPU, 4-chunk ring AllReduce in Figure 11-8 run as low-occupancy device kernels on Streaming Multiprocessors inside a high-priority communication stream or offload reductions to NVIDIA SHARP. NIXL `nixlCommStream` pipelines chunked peer-to-peer and disaggregated transfers across NVLink, RDMA, and storage on high-priority streams so copy commands preempt lower-priority work.
```
</details>

<details>
<summary>**18. Why must you pass `cudaStreamCaptureModeGlobal` to `cudaStreamBeginCapture` when capturing a multi-stream iteration (`streamA` compute + `streamB` `ncclAllReduce`)?**</summary>

Passing `cudaStreamCaptureModeGlobal` instructs CUDA to record operations enqueued on all participating streams joined by event dependencies into the same graph capture session. That way, cudaGraphLaunch replays the complete multi-stream DAG.
</details>

<details>
<summary>**19. Explain the three-part API mechanism of Programmatic Dependent Launch (`PDL`).**</summary>

1. The primary kernel calls `cudaTriggerProgrammaticLaunchCompletion()` as soon as all global memory writes needed by the secondary kernel are flushed. Allowing the secondary kernel to start while the primary kernel runs its epilogue.
2. The secondary kernel calls `cudaGridDependencySynchronize()` to wait for the primary kernel's trigger and memory flush before reading shared data.
3. The host launch sets `cudaLaunchAttributeProgrammaticStreamSerialization` on the secondary kernel's launch configuration.
</details>

<details>
<summary>**20. How does `primary_gemm` → `secondary_gemm` (Figures 11-10 & 11-11) combine intra-kernel, inter-block, and inter-kernel overlap, and what Blackwell TMA feature can fuse small reductions during copies?**</summary>

1. Intra-kernel overlap uses producer warps to stage 128 by 128 tiles in 131,072 B of static shared memory asynchronously while consumer warps compute matrix multiplications.
2. Inter-block overlap uses `__cluster_dims__(2, 1, 1)` to co-schedule two-block clusters on a GPC with hardware barrier synchronization and Tensor Memory Accelerator multicast. On Blackwell, descriptor-based Tensor Memory Accelerator reduce operations `cp.reduce.async.bulk.tensor` perform on-the-fly reductions during tiled copies to lower register pressure.
3. Inter-kernel overlap uses Programmatic Dependent Launch to overlap the secondary GEMM startup with the primary GEMM epilogue inside the same stream.
</details>

---

## Sources and review notes

### Primary sources read in full for this chapter
- *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chris Fregly), Chapter 11 (*Inter-Kernel Pipelining, Synchronization, and CUDA Stream-Ordered Memory Allocations*):
  - Overlapping Kernel Execution with CUDA Streams (`Figure 11-1`: 5 kernels `ker_1..3` on `stream1`, `ker_A..B` on `stream2`, and multi-stream `warp_specialized_pipeline`),
  - Using Streams to Overlap Compute with Data Transfers (`Figure 11-2`: 3-way H2D/Compute/D2H overlap across `asyncEngineCount >= 2` DMA copy engines, 50% contention under saturation, 128 max concurrent resident grids, and pageable vs pinned `cudaMallocHost` / `pin_memory=True`),
  - Stream-Ordered Memory Allocator (`cudaMallocAsync`, `cudaFreeAsync`, `cudaDeviceGetDefaultMemPool`, `cudaMemPoolSetAttribute`, `cudaMemPoolAttrReleaseThreshold`, `PYTORCH_ALLOC_CONF=backend:cudaMallocAsync`),
  - Legacy Default Stream vs Per-Thread Default Stream (`cudaStreamLegacy`, `cudaStreamPerThread` / `PTDS`, `--default-stream per-thread`, `CUDA_API_PER_THREAD_DEFAULT_STREAM=1`, `cudaStreamNonBlocking`),
  - Fine-Grained Synchronization with Events and Callbacks (`cudaEventRecord`, `cudaStreamWaitEvent`, `cudaEventDisableTiming`, `cudaEventQuery`, `cudaEventElapsedTime` across `producerStream`, `consumerStream`, and `computeStream`, and `cudaLaunchHostFunc` deadlock rules),
  - Pipelining with Warp Specialization and Thread Block Clusters (`warp_specialized_two_pipelines` with `blockDim = 96`, `97`% efficiency, `287` metrics, `launch_warp_specialized_cluster_pipeline_multistream` with `DSMEM` and `rows_per_block`),
  - Multi-GPU Compute and Data Transfer Overlap (`cudaMemcpyPeerAsync`, `DistributedDataParallel`, `FSDP`, `NCCL`, `NIXL` `nixlCommStream`, and `cudaStreamBeginCapture` with `cudaStreamCaptureModeGlobal`),
  - Programmatic Dependent Launch (`PDL`, `cudaTriggerProgrammaticLaunchCompletion`, `cudaGridDependencySynchronize`, `cudaLaunchAttributeProgrammaticStreamSerialization`, `primary_gemm` / `secondary_gemm` with `__cluster_dims__(2,1,1)`, and Blackwell TMA reduce `cp.reduce.async.bulk.tensor`).

### Verification and review notes
- **Run here:** `python3 -B code/part10/inter_kernel_pipelining_lab.py` (25 passed, 0 failed; read via `tools/study_rag/bookch.py` and mapped in `MIGRATION_MAP.md`, expanding Chapters `10.3`, `10.11`, and `10.12` in `2026`).
- **Explicitly labelled inferences:** The illustrative stage timings in `simulate_inter_kernel_stream_pipeline()` and `model_programmatic_dependent_launch()` in `code/part10/inter_kernel_pipelining.py` are **my inference** illustrating Figures 11-2 and 11-9 of *AI Systems Performance Engineering* Chapter 11.
- **Not verified on live hardware:** All `nvcc`, `nsys`, `ncclAllReduce`, `nixlCommStream`, and `cudaLaunchKernelExC` commands in Section 7 are marked `(untested here)` because this verification environment does not have an attached Hopper (`sm_90`) or Blackwell (`sm_100`) GPU.


