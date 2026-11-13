---
id: "c10-13"
title: "10.13 Memory access patterns and profiling"
sidebar_label: "10.13 Memory access patterns and profiling"
sidebar_position: 13
description: "Memory access patterns and profiling"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "Nebius GPU"
---

# 10.13 Memory access patterns and profiling

| | |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | Nebius GPU |
| Part | Part 10: The GPU and CUDA |
| Sources used | *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chris Fregly), Chapter 7 (pp. 215–252) |
| Coverage file | `planning/coverage/chapters/10-13.md` |
| Claim ledger | `planning/ledgers/10-13.md` |

## Why this matters for AI infrastructure

Picture a training run on a freshly built cluster. The GPUs are the newest models, the memory is the fastest on the market, and the monitoring dashboard shows the cards busy. Yet each step takes much longer than the spec sheet suggests. When an engineer opens the profiler, the Tensor Cores sit idle for long stretches. A warp, which is a group of 32 threads that run the same instruction together, is waiting on data that has to come from off-chip memory. Each wait lasts hundreds of clock cycles. The hardware has the bandwidth. The kernels are the part that wastes it.

To see why, it helps to think of memory as a bus route. A bus costs the same to drive whether it is full or nearly empty. Memory works the same way. Each trip out to off-chip memory costs the same whether the GPU uses every byte it fetches or throws most of them away. A kernel that makes many half-empty trips is slow even when its math is simple.

A single NVIDIA Blackwell B200 GPU has about 8 TB/s of HBM3e bandwidth. HBM stands for high-bandwidth memory, the stacks of memory chips that sit beside the GPU die. HBM3e is one generation of that memory. TB/s means terabytes per second, so 8 TB/s is the peak rate at which the bus can move data. A kernel that reads with a small element stride reaches only a quarter of that. Stride here means the gap between the addresses that neighboring threads read. The hardware cannot fetch single bytes. It fetches whole cache sectors, and each thread uses only a few bytes of every sector it fetches.

Stride is one of six ways a kernel can starve the Streaming Multiprocessors, and each has its own fix. The Streaming Multiprocessors, or SMs, are the units inside the chip that run the threads. Starving an SM means leaving its cores with nothing to do. The six problems are easier to hold in mind as a group. The first is the layout of the reads. The next four are the number of load instructions, the reuse of data already on chip, the layout of shared memory, and the exchange of values inside a warp. The last is the waiting on long loads. The sections below take them in that order.

The first family of problems is narrow loads. Each thread asks for one float at a time, so the same bytes need many load instructions. Narrow scalar loads multiply the instruction count by four or eight. Every instruction takes time to issue and occupies the load units. Packing contiguous values into wider vector loads cuts that pressure and raises global load efficiency.

The second family is reuse. A naive matrix or attention kernel reads the same inputs over and over. Each thread fetches its own copy from HBM, even though a neighbor fetched the same values a moment earlier. Picture a classroom where every student walks to the library for the same book, instead of sharing one copy on a desk. A tile is a small square block of a matrix, and shared memory is a small pool of fast on-chip memory that every thread in one block can read. Staging reusable tiles in shared memory cuts off-chip sector traffic by more than eightfold, and compute throughput rises by more than an order of magnitude.

The third family is bank conflicts. Shared memory is split into banks, which are independent columns of storage that can each serve one address per cycle. Threads that read down a column of a shared-memory tile can collide on one bank. When the lanes of a warp hit different addresses in the same bank, the hardware replays the access one after another. A lane is one thread's position inside its warp. Think of a store with many shoppers and a single checkout lane. If everyone queues at the same lane, the line is slow even though the other lanes are empty. One padding column, or a swizzled index, removes the conflicts and triples kernel speed in the example from *AI Systems Performance Engineering*.

The fourth family is the exchange inside a warp. Suppose the 32 threads of a warp each hold a partial sum, and you want the total. The usual approach writes every partial sum into shared memory, waits at a barrier, and reads them back. A barrier is a point where every thread must arrive before any of them may continue. That approach costs shared-memory space and forces every thread to stop and wait. Summing values inside a warp through shared memory costs capacity and needs barriers. Warp shuffle instructions let lanes read each other's registers directly, in a few butterfly steps, with no shared memory and no bank conflicts. A register is the private storage each thread keeps for its own values. A butterfly step pairs each lane with a partner, and the distance between partners shrinks as the steps go on.

The last family is waiting. Suppose a kernel asks for a value from HBM and then sits still until the value arrives. The SM has nothing else to do during that round trip. Marking immutable lookup tables read-only routes them through the L1 read-only cache, which is a small cache close to each SM. Double-buffering tiles with the Tensor Memory Accelerator overlaps off-chip transfers with computation. Double-buffering means keeping two buffers, so one can fill while the other is in use. The Tensor Memory Accelerator is a hardware helper on newer GPUs that copies tiles in the background.

```text
Memory Access Optimization Summary (AI Systems Performance Engineering Ch 7, pp. 215-252):
  - B200 HBM3e Peak Bandwidth:     8 TB/s (8,000 GB/s) per GPU; 16 TB/s on GB200 / GB300 Superchip (Ch 10.3, Ch 10.7)
  - 1. Coalescing (Table 7-1):     stride 2 -> stride 1 lifts DRAM 25% -> 90% (3.6x), Load Eff 23% -> 99%, Sectors/Req 8.0 -> 4.0, 4.8 ms -> 1.3 ms (3.7x)
  - 2. Vectorizing (Table 7-2):    scalar 4B -> float4 16B (or Blackwell float8 32B) lifts Load Eff 28% -> 97%, Sectors/Req 31.8 -> 4.0, 4.2 ms -> 1.2 ms (3.5x)
  - 3. SMEM Tiling (Table 7-4):    naive 1,024x1,024 GEMM -> 32x32 tile cuts sectors 9,800 -> 1,200 (~8.17x), lifts 1.5 -> 8.0 FLOPs/B, 42% -> 89% occ, 15 -> 170 GFLOPS (~11.3x)
  - 4. Bank Padding (Table 7-5):   tile[32][32] -> tile[32][33] (+1 col, ~3% / 1 KB) drops conflicts 4.8M -> 0, SMEM util 52% -> 100%, stalls 38% -> 0.5%, 4.0 ms -> 1.3 ms (3x)
  - 5. Warp Shuffle (p. 239):      __shfl_down_sync reduces 32 lanes in 5 register steps (offsets 16, 8, 4, 2, 1) with 0 shared memory and 0 bank conflicts
  - 6. Read-Only Cache (Table 7-6): const __restrict__ on T = 1,024 table cuts DRAM 600 -> 200 GB/s, lifts Load Eff 52% -> 97%, L2 1,500 -> 1,800 GB/s, 2.5 ms -> 1.0 ms (2.5x)
  - 7. TMA Prefetch (Table 7-7):   cuda::memcpy_async + cuda::pipeline hides ~800-cycle DRAM latency, lifting Load Eff 23% -> 99%, SM Active 62% -> 100%, 18 ms -> 7 ms (~2.6x)
```

Read the Nsight Compute tables in this chapter with care. Nsight Compute is NVIDIA's profiler for single kernels, and its counters show how a kernel used the memory system. The numbers in these tables come from the example in *AI Systems Performance Engineering*, Chapter 7, and none of them was rerun on live hardware for this handbook. The same DRAM throughput shift appears in three different tables, so the tables do not form one clean experiment. The scalar baseline in the vectorization table also shows scattered sectors, which a contiguous scalar load would not produce. Use the tables for direction and rough size. Do not read them as hardware benchmarks.

This chapter walks through all seven memory-access techniques in turn. Each section gives CUDA C++ and PyTorch patterns, the Nsight Compute counters that show the problem, and a check in the deterministic lab. CUDA C++ is the language for writing GPU kernels directly. PyTorch is the Python framework that most AI code uses, and the PyTorch examples show how the same ideas appear in everyday tensor code. The counters are the evidence for each claim, so keep them open while you read.

:::tip In one minute
- **Global memory coalescing:** A modern NVIDIA GPU services global memory in 128-byte cache lines divided into four 32-byte sectors. When all threads in a warp read contiguous floats from an aligned address, hardware merges all reads into one cache line. Strided access touches many more sectors per request and wastes most of the fetched bytes.
- **Vectorized global loads:** Device pointers from `cudaMalloc` are aligned to at least 256 bytes. Packing four floats into `float4` on Hopper or eight floats into `float8` on Blackwell issues a single wide vector load per thread. This cuts load instructions by fourfold or eightfold.
- **Shared-memory tiling and bank padding:** Staging square tiles in shared memory reuses each global load dozens of times and boosts matrix multiply throughput more than elevenfold. Adding one padding column to a shared array shifts column reads across all banks and eliminates bank conflicts.
- **Warp shuffles, read-only caches, and TMA:** Intra-warp reductions use `__shfl_down_sync` to sum lanes directly in registers in five steps. Adding `const __restrict__` routes immutable tables through the L1 read-only cache. Double-buffering tiles with the Tensor Memory Accelerator hides long DRAM latency behind computation.
:::

---

## Prerequisites and outcomes

**Prerequisites:** Before you start, it helps to have read the earlier Part 10 chapters on SIMT warps, the GPU memory hierarchy, Tensor Cores, and Roofline arithmetic intensity. Those chapters explain the vocabulary used here. You should also be comfortable with CUDA kernel indexing, which is how each thread works out which element it owns, and with asynchronous streams, which let copies and kernels overlap in time.

**What the chapter covers:** The chapter starts with how a warp's loads turn into cache lines and sectors, and how to read the load efficiency counters in Nsight Compute. It then covers vectorized loads with `float4` and `float8`, and why pointer alignment has to survive element offsets. Next comes shared-memory tiling, the register budget against the SM limits, and the two ways to remove bank conflicts. Last, it covers `__shfl_down_sync` reductions, read-only lookup tables, and double buffering with the Tensor Memory Accelerator.

---

## 1. Coalesced vs. Uncoalesced Global Memory Access

A developer writes a kernel where each thread processes every second or fourth element of an array. Another kernel reads one field from an array of C++ structures. Both kernels do very little math, yet they run nearly four times slower than a simple contiguous copy. Nsight Compute reports that three-quarters of the bytes transferred across the HBM bus are thrown away before they reach the registers. The developer's first guess is that the math is the problem. The counters say the memory layout is the problem. This section explains how the GPU turns a warp's loads into bus traffic, so the layout problem becomes visible.

### 1.1 How the GPU memory controller services a 32-thread warp load

Start with what happens when a warp runs one load instruction. The 32 threads do not each send a request for one float. Instead, the memory coalescer, which is the hardware unit in the load and store path, looks at all 32 addresses together and groups them into the fewest memory requests it can. Global memory is the large off-chip memory that every thread can see, and it is backed by HBM. Think of a bus route. If all the passengers live on one street, the bus makes one stop. If they live on different streets, the bus has to visit each street. Modern NVIDIA GPUs service global memory through 128-byte cache lines, and each cache line is divided into four 32-byte sectors. A cache line is the chunk the cache fetches at once, and a sector is the smallest piece the memory system returns.

```mermaid
flowchart TB
  subgraph Coalesced["1. Aligned Coalesced Warp Load (in[idx], stride = 1)"]
    direction LR
    W1["32 Threads in Warp (Lanes 0..31)<br/>Request 32 x 4B = 128 contiguous bytes"] --> L1["1 x 128B Cache Line (4 x 32B Sectors)<br/>Sectors/Req = 4.0, Load Eff = 99% (1.3 ms)"]
  end

  subgraph Misaligned["2. Misaligned Contiguous Warp Load (offset +4B)"]
    direction LR
    W2["32 Threads in Warp (Lanes 0..31)<br/>Span crosses 128B cache-line boundary"] --> L2["Straddles 2 x 128B Cache Lines<br/>Fetches 5 to 8 x 32B Sectors (80% eff)"]
  end

  subgraph Strided["3. Uncoalesced Strided / Gather Load (in[idx * 2] / AoS)"]
    direction LR
    W3["32 Threads in Warp (stride = 2 -> 8B apart)<br/>or Scattered (stride >= 8 -> >= 32B apart)"] --> L3["Stride 2: 8.0 Sectors/Req (Scattered: 32.0)<br/>Load Eff = 23%, DRAM = 25% (4.8 ms = 3.7x slower)"]
  end
```

Before the four patterns, picture the warp as 32 riders waiting at a bus stop, one rider per thread. Each rider wants one address. The memory controller is the driver. Its job is to pick up everyone who wants bytes from the same stretch of road in one trip. If the riders all stand in one spot, one bus covers them. If they stand spread across the city, the bus makes many stops, and most seats on each stop are empty. Keep that picture in mind for the next four patterns, because the only thing that changes between them is where the riders stand.

Four access patterns decide how many sectors the memory controller must fetch for a single warp load. The memory controller is the unit that turns requests into real reads from HBM. Each pattern below uses the same 32 threads, and the difference is only where each thread's address lands. Keep the bus picture in mind. A pattern that spreads the riders across many streets needs many more stops.

In the first pattern, all lanes read contiguous 4-byte floats starting at a 128-byte-aligned address. Aligned means the start address is a multiple of 128 bytes, so the block begins exactly at the start of a cache line. The lanes request 128 contiguous bytes that map to one cache line and four sectors. Every byte fetched from memory is used by a thread. This layout gives an optimal four sectors per request and full theoretical load efficiency. This is the bus making a single stop on one street, and it is the layout to aim for.

In the second pattern, the warp still reads contiguous floats, but the starting address is shifted by four bytes. The data is still contiguous and still fills the warp's 128 bytes. The shift moves the block across a cache-line boundary, so the bus now needs two stops. The request span now crosses a cache-line boundary and straddles two cache lines. The memory controller must fetch four sectors from the first line plus one sector from the second line. Depending on the caching policy, hardware fetches five to eight sectors per request. The lesson is that a small misalignment costs bandwidth even when the access order is perfect.

In the third pattern, threads read with a stride of two floats, so adjacent lanes sit eight bytes apart. Each thread still asks for one float, but the floats it wants are interleaved with the floats that belong to its neighbors. The bus visits both streets and carries back half of every sector it touches. The warp spans two cache lines and touches eight sectors, throwing away half of every sector fetched. This is the pattern that shows up in everyday PyTorch code. Calling `torch.index_select` with a strided index launches a gather kernel with this exact uncoalesced pattern. Using `inp.clone()` or `torch.compile` performs a contiguous copy instead.

In the fourth pattern, threads read with a stride of eight or more floats, so adjacent lanes sit at least 32 bytes apart. Now every thread lands in a different sector. This is the scattered layout that a gather from random indices produces. A gather reads values from the positions named in an index list. Think of a bus that must visit a different street for every rider. Every thread in the warp lands in a different sector at the L2 cache. L2 is the cache shared by the whole chip, sitting between the SMs and HBM. The memory controller must fetch 32 sectors just to deliver 128 useful bytes, which drops load efficiency to an eighth of peak.

```text
Warp Global Memory Sector Math (32 threads x 4-byte FP32 = 128 useful bytes; analyze_warp_global_memory_access):
  - Aligned stride = 1 (offset 0 B, bytes 0..127):     1 cache line (128 B)  |  4.0 sectors (128 B fetched)   | 128 / 128   = 100.0% efficiency (99% in Table 7-1)
  - Misaligned stride = 1 (offset +4 B, bytes 4..131): 2 cache lines         |  5.0 sectors (160 B fetched)   | 128 / 160   =  80.0% efficiency (up to 8 sectors)
  - Strided stride = 2 (in[idx * 2], N = 1,048,576):   2 cache lines (256 B) |  8.0 sectors (256 B fetched)   | 128 / 256   =  50.0% theoretical (23% in Table 7-1)
  - Scattered stride >= 8 (>= 32 B between threads):   8+ cache lines        | 32.0 sectors (1,024 B fetched) | 128 / 1,024 =  12.5% theoretical efficiency
```

### 1.2 Array of Structures vs. Structure of Arrays and Nsight Compute Table 7-1

Now the C++ side. Uncoalesced strided access most often comes from how the data is stored, not from the kernel code itself. In C++ this usually appears as an Array of Structures, abbreviated AoS, which means each record is a struct and the records sit side by side in one array. Suppose a struct holds four floats for a point in space. Adjacent structs then sit 16 bytes apart. If every thread in a warp reads only the first field, the reads have a stride of four floats. That pattern wastes three-quarters of every fetched sector.

The fix is a Structure of Arrays, abbreviated SoA. Instead of one array of records, you keep one array per field. Converting the layout to a Structure of Arrays stores all first coordinates in one contiguous array. Separate contiguous arrays hold the remaining coordinates. When all threads in a warp read the first coordinate array, all lanes read contiguous floats in a single cache line. The bus now takes everyone from one street.

| Nsight Compute Metric | Before (`uncoalescedCopy`, `stride = 2`) | After (`coalescedCopy`, `stride = 1`) | Improvement Factor |
|---|---:|---:|---|
| **DRAM Throughput (`% of peak`)** | `25%` | **`90%`** | **`3.6x` higher** |
| **Global Memory Load Efficiency** | `23%` | **`99%`** | **`4.3x` higher** (`100%` theoretical useful bytes) |
| **Average Sectors per Request** | `8.0` | **`4.0` (optimal)** | **`2.0x` fewer sectors** per warp request |
| **SM Active `%`** | `62%` | **`99%`** | SMs stay active instead of stalling on DRAM |
| **Kernel Execution Time (`ms`)** | `4.8 ms` | **`1.3 ms`** | **`3.7x` faster** (`N = 1 << 20 = 1,048,576`) |

**Always organize multi-field GPU buffers as a Structure of Arrays so that adjacent threads in a warp read contiguous addresses with a stride of one.** Before you optimize any arithmetic inside a kernel, open Nsight Compute and look at the `Average Sectors per Request` counter. Verify that scalar float loads achieve four sectors per request. If the counter is far above that, the layout is the first thing to fix, long before you touch the math.

### 1.3 A strided copy in C++ and PyTorch, and the contiguous fix

Picture a copy kernel that reads only every second float and writes it to an output. The math is trivial, yet the kernel runs far below peak. The problem is the memory pattern. Neighboring threads sit 8 bytes apart, so one warp's reads spread across more cache lines than they need. A useful habit is to ask how many streets one warp's riders are standing on before you look at anything else.

The C++ version below uses `in[idx * stride]` with `stride = 2`. Each thread copies one element, but its read skips over the values in between. Because `idx` is the thread's global index, the first thread reads the first element and the next thread reads the element two positions along. The example sizes the array at `N = 1 << 20`, which is a shift expression for a power of two.

Read the C++ code from the top. The kernel finds its global index by combining the block number, the block size, and the thread number. That index is the thread's own element. The bounds check, which tests whether the index is below N, stops the extra threads in the last block from reading past the end of the array. The read in the copy line is the line that matters, because it decides how far apart the lanes of a warp look. The host code allocates pinned host buffers, fills them, copies them to the device, launches the kernel, and then times the run. Pinned memory is host memory that the GPU can read directly, so the copies are not slowed by an extra staging step.

```cpp
#include <cuda_runtime.h>
#include <iostream>

__global__ void uncoalescedCopy(const float* __restrict__ in,
                                float* __restrict__ out,
                                int N, int stride) {
    // n = 1048576, stride = 2
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        // Loads from in[] with a stride, causing
        // multiple memory segments to be fetched
        out[idx] = in[idx * stride];
    }
}

int main() {
    const int N = 1 << 20;
    const int stride = 2;

    float* h_in = nullptr;
    float* h_out = nullptr;
    cudaMallocHost(&h_in, N * stride * sizeof(float));
    cudaMallocHost(&h_out, N * sizeof(float));
    for (int i = 0; i < N * stride; ++i) {
        h_in[i] = static_cast<float>(i);
    }

    float *d_in, *d_out;
    cudaMalloc(&d_in, N * stride * sizeof(float));
    cudaMalloc(&d_out, N * sizeof(float));
    cudaMemcpy(d_in, h_in, N * stride * sizeof(float),
               cudaMemcpyHostToDevice);

    const int threadsPerBlock = 256;
    const int blocksPerGrid = (N + threadsPerBlock - 1) / threadsPerBlock;
    uncoalescedCopy<<<blocksPerGrid, threadsPerBlock>>>(d_in, d_out, N, stride);
    cudaDeviceSynchronize();

    cudaFree(d_in);
    cudaFree(d_out);
    cudaFreeHost(h_in);
    cudaFreeHost(h_out);
    return 0;
}
```

The stride means each warp makes several small transactions instead of one wide one. On the measured run, each warp's request breaks into eight separate 32-byte sectors on average. A 128-byte cache line holds four sectors, so the warp spans two lines to collect those eight. Nsight Compute reports only about 25% of sustained peak DRAM throughput. In plain words, the kernel asks for a lot of data, but the DRAM bus is far from full.

The PyTorch version creates the same pattern with a gather. A gather reads values from positions named by an index list, and that is what `torch.index_select` does. Calling `torch.index_select` with a strided index launches a gather kernel. Each thread in a warp loads a value that sits `stride * 4` bytes away from its neighbor's value.

```python
import torch

def uncoalesced_copy(input_tensor, stride):
    # Flatten to 1D so we know exactly
    # which dimension we're indexing
    flat_tensor = input_tensor.contiguous().view(-1)
    # Generate indices with a fixed stride to gather
    assert flat_tensor.numel() % stride == 0, "stride must divide tensor length"
    idx = torch.arange(0, flat_tensor.numel(), stride,
                       device=flat_tensor.device, dtype=torch.long)
    # index_select uses a gather kernel that issues uncoalesced loads
    return torch.index_select(flat_tensor, 0, idx)

# Usage
n, stride = 1 << 20, 2
inp = torch.arange(n * stride, device='cuda', dtype=torch.float32)
out = uncoalesced_copy(inp, stride)
```

The fix is to remove the stride, so each thread copies a neighboring element. Now the warp's loads merge into full 128-byte transactions. A warp usually needs one transaction when its first address is 128-byte aligned, and two when the access straddles a boundary. The kernel below makes that change and keeps everything else the same.

```cpp
#include <cuda_runtime.h>
#include <iostream>

__global__ void coalescedCopy(const float* __restrict__ in,
                              float* __restrict__ out,
                              int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        // Contiguous load
        // Threads copy neighboring elements
        out[idx] = in[idx];
    }
}

int main() {
    const int n = 1 << 20;
    const size_t bytes = n * sizeof(float);

    // 1) Allocate pinned host memory
    float *h_in = nullptr, *h_out = nullptr;
    cudaMallocHost(&h_in, bytes);   // page-locked host alloc
    cudaMallocHost(&h_out, bytes);

    // 2) Initialize input
    for (int i = 0; i < n; ++i) {
        h_in[i] = static_cast<float>(i);
    }

    // 3) Allocate device memory
    float *d_in = nullptr, *d_out = nullptr;
    cudaMalloc(&d_in, bytes);
    cudaMalloc(&d_out, bytes);

    // 4) Copy to device
    cudaMemcpy(d_in, h_in, bytes, cudaMemcpyHostToDevice);

    // 5) Launch kernel
    dim3 block(256);
    dim3 grid((n + block.x - 1) / block.x);
    coalescedCopy<<<grid, block>>>(d_in, d_out, n);
    cudaDeviceSynchronize();

    // 6) Copy back to host
    cudaMemcpy(h_out, d_out, bytes, cudaMemcpyDeviceToHost);

    // 7) Clean up
    cudaFree(d_in);
    cudaFree(d_out);
    cudaFreeHost(h_in);
    cudaFreeHost(h_out);
    return 0;
}
```

Read the coalesced version the same way. The index is the same, and the read now uses the plain index, so neighboring threads read neighboring floats. The host code is longer only because it does the bookkeeping that a timing run needs. It allocates pinned host memory, fills the input, allocates device buffers, copies the input across, launches the kernel, waits for it to finish, and copies the result back. Compare the two kernels line by line and you will find that the only real change is the index in the read. That single change is the whole difference in the table above.

You do not need to write this kernel in PyTorch. A coalesced copy is simply `out = inp.clone()`. A tensor is contiguous when its elements sit back to back in memory. On a contiguous tensor, `clone()` is a device-to-device copy, which means it moves data from one GPU buffer to another GPU buffer without passing through the host. That copy runs on an optimized, vectorized path. It is usually not fused into a custom kernel.

You can also use `torch.compile` with the default TorchInductor backend. TorchInductor is the code generator behind `torch.compile`. It can remove redundant copies and fuse neighboring operations when that is safe. Set `mode="max-autotune"` to let TorchInductor pick coalesced and vectorized schedules, as long as shapes stay stable. Stable shapes matter because a change in tensor size can trigger a new compile.

---

## 2. Vectorized Global Memory Access

Even when a scalar float kernel is fully coalesced at four sectors per request, each thread still issues a narrow 4-byte load instruction. Think of a delivery crew that makes one trip per box instead of carrying a full pallet at a time. Issuing four or eight times as many memory instructions as necessary congests the instruction pipeline. It can also leave load efficiency low when accesses are unaligned or scattered. Vectorizing fixes the instruction count, and coalescing fixes the spread of the addresses. You often need both.

### 2.1 Coalescing vs. vectorizing and `cudaMalloc` 256-byte alignment

Coalescing is an inter-thread property across the lanes of a warp. Vectorizing is an intra-thread property inside each individual thread. Coalescing asks how the riders on one bus line up with each other. Vectorizing asks how much each rider carries in one trip. Vectorized memory access packs four or eight contiguous floats into a single wider load or store instruction per thread.

| Vector Type & Architecture | Bytes per Thread | PTX Instruction Emitted by `nvcc` | Required Pointer Alignment | Bytes Moved per Warp (`32` lanes) | `128 B` Cache Lines per Warp | `32 B` Sectors per Warp | Sectors per `128 B` Line |
|---|---:|---|---:|---:|---:|---:|---:|
| **Scalar `float`** (All GPUs) | `4 B` (`1` float) | `ld.global.f32` / `st.global.f32` | `4 B` | `128 B` | `1` line | `4` sectors | `4.0` (if `128 B` aligned) |
| **`float4` (`128-bit`)** (Hopper `sm_90` & earlier) | **`16 B` (`4` floats)** | **`ld.global.v4.f32` / `st.global.v4.f32`** | **`16 B`** (`alignof(float4) == 16`) | **`512 B`** | **`4` lines** | **`16` sectors** | **`4.0` per line** (`4x` fewer load instructions) |
| **`alignas(32) float8` (`256-bit`)** (Blackwell `sm_100`, CUDA 13+) | **`32 B` (`8` floats)** | **`ld.global.v8.f32` / `st.global.v8.f32`** | **`32 B`** (`alignas(32)`) | **`1,024 B`** | **`8` lines** | **`32` sectors** | **`4.0` per line** (`8x` fewer load instructions) |

Two hardware alignment rules govern vectorized global loads. Alignment means the address is a multiple of a fixed size, and a wide load works cleanly only when its address follows that rule. First, every device pointer returned by `cudaMalloc` is guaranteed to be aligned to at least 256 bytes. That base alignment automatically satisfies both 16-byte `float4` alignment and 32-byte `float8` alignment at offset zero.

However, if a kernel adds an element offset to a base pointer and casts the sum to a vector pointer, the byte offset must remain aligned. Adding an offset is common when a kernel handles a slice of a larger tensor. For 16-byte `float4` loads, the element offset must be a multiple of four floats. For 32-byte `float8` loads on Blackwell, the element offset must be a multiple of eight floats. A misaligned cast forfeits vectorization and triggers an address fault, which is an error the GPU raises when a load asks for an address that the rule forbids.

Second, maximum vector width doubled on Blackwell with CUDA 13. Hopper is the GPU generation before Blackwell. On Hopper and earlier architectures, global vector loads top out at 16 bytes per thread using `ld.global.v4.f32`. An eight-float structure on Hopper compiles into two 16-byte loads. On Blackwell with CUDA 13 and a 32-byte-aligned structure, the compiler emits a single 32-byte `ld.global.v8.f32` instruction. That single instruction moves 1,024 bytes per warp across eight cache lines. Think of it as a larger bucket on the same bus route. The route still makes its stops at 128-byte cache lines.

### 2.2 Nsight Compute Table 7-2: Scalar vs. Vectorized Copy

Comparing a scalar copy kernel against a 16-byte `float4` vectorized copy kernel shows how wide loads reduce instruction overhead and improve bus utilization. Read the table with two questions in mind. The sector and load efficiency rows measure how well each request uses the bus. The runtime row measures the total effect on the kernel.

| Nsight Compute Metric | Before (`copyScalar`) | After (`copyVector16B` / `float4`) | Improvement Factor |
|---|---:|---:|---|
| **Global Memory Load Efficiency** | `28%` | **`97%`** | **`~3.5x` higher** |
| **Average Sectors per Request** | `31.8` | **`4.0` (per `128 B` line)** | Eliminates scattered sector waste |
| **DRAM Throughput (`% of peak`)** | `25%` | **`90%`** | **`3.6x` higher** |
| **Kernel Execution Time (`ms`)** | `4.2 ms` | **`1.2 ms`** | **`3.5x` faster** (`4.2 / 1.2 = 3.5x`, `N4 = N / 4`) |

**When writing bandwidth-bound elementwise or copy kernels, cast aligned pointers to `float4` on Hopper or `alignas(32) float8` on Blackwell.** A bandwidth-bound kernel is one whose speed is set by how fast memory can deliver data. An elementwise kernel computes each output from the matching input, such as adding a bias to every value, so there is little reuse that could hide the memory cost. This allows each thread to load 16 or 32 bytes per instruction. Always verify that any interior element offset is divisible by four or eight floats before casting.

### 2.3 Scalar and vector copy kernels side by side

A scalar copy moves one 4-byte float per thread. Each warp then issues 32 narrow loads. Picture the same job done one item at a time, with a separate trip through the warehouse for each item. The C++ kernel below is the baseline that the vectorized version beats.

```cpp
#include <cuda_runtime.h>

__global__ void copyScalar(
    const float* __restrict__ in,
    float* __restrict__ out, int N) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        // Scalar load: 4-byte copy per thread
        out[idx] = in[idx];
    }
}

int main() {
    const int N = 1 << 20;
    float* h_in = nullptr;
    float* h_out = nullptr;
    cudaMallocHost(&h_in, N * sizeof(float));
    cudaMallocHost(&h_out, N * sizeof(float));
    for (int i = 0; i < N; ++i) h_in[i] = float(i);

    float *d_in, *d_out;
    cudaMalloc(&d_in, N * sizeof(float));
    cudaMalloc(&d_out, N * sizeof(float));
    cudaMemcpy(d_in, h_in, N * sizeof(float), cudaMemcpyHostToDevice);

    dim3 block(256), grid((N + 255) / 256);
    copyScalar<<<grid, block>>>(d_in, d_out, N);
    cudaDeviceSynchronize();

    cudaFree(d_in); cudaFree(d_out);
    cudaFreeHost(h_in);
    cudaFreeHost(h_out);
    return 0;
}
```

The PyTorch scalar version uses a Python loop. It is shown only as a warning. Each loop iteration reaches into the GPU tensor from Python and copies one element, so the overhead of each separate launch dominates the run time. Do not copy this pattern. Use tensor operations instead.

```python
import torch

def copy_scalar(inp: torch.Tensor) -> torch.Tensor:
    out = torch.empty_like(inp)
    flat_in = inp.view(-1)
    flat_out = out.view(-1)
    for i in range(flat_in.numel()):
        # Each iteration issues a 4-byte load on the GPU
        # This is extremely slow. DO NOT DO THIS!
        # Use vectorized operations to avoid Python loops
        # on GPU tensors as shown in optimized version
        flat_out[i] = flat_in[i]
    return out

# Usage
N = 1 << 20
inp = torch.arange(N, device='cuda', dtype=torch.float32)
out = copy_scalar(inp)
```

With scalar 4-byte loads, a warp often issues one 128-byte transaction when aligned. It uses two when the access straddles a 128-byte boundary. A `float4` load gives each thread 16 bytes. One warp then moves 512 bytes, split into four 128-byte transactions. The kernel below does exactly that.

```cpp
#include <cuda_runtime.h>

// 16-byte (128-bit) vector copy: one float4 per thread
static_assert(alignof(float4) == 16, "float4 alignment must be 16 bytes");

__global__ void copyVector16B(const float4* __restrict__ in,
                              float4* __restrict__ out,
                              int N4)  // number of float4 elements
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N4) {
        // Per-thread 16B load+store.
        // On sm_90, NVCC emits ld.global.v4.f32 / st.global.v4.f32
        // for 16-byte vector loads and stores.
        // On sm_100 (Blackwell), 32-byte aligned data can use
        // ld.global.v8.f32 and st.global.v8.f32 instead.
        out[idx] = in[idx];
    }
}

int main() {
    const int N = 1 << 20;     // total number of floats
    const int N4 = N / 4;      // total number of float4s (16B chunks)

    float4 *d_in = nullptr, *d_out = nullptr;
    cudaMalloc(&d_in, N4 * sizeof(float4));   // >=256B aligned
    cudaMalloc(&d_out, N4 * sizeof(float4));

    dim3 block(256);
    dim3 grid((N4 + block.x - 1) / block.x);
    copyVector16B<<<grid, block>>>(d_in, d_out, N4);
    cudaDeviceSynchronize();

    cudaFree(d_in);
    cudaFree(d_out);
    return 0;
}
```

This kernel launches N/4 threads, so each thread copies one `float4` of 16 bytes. Each warp then handles 128 floats in four transactions. `cudaMalloc` returns pointers aligned to at least 256 bytes, which satisfies `float4` alignment. A misaligned cast can give up the vectorized load. In the worst case it crashes with `cudaErrorMisalignedAddress`, so keep casts aligned. Check the alignment before the cast, not after the crash.

Blackwell doubles the bytes per thread. With CUDA 13, Blackwell can do 32-byte loads and stores instead of 16-byte ones. The example defines an aligned 8-float type for this case. Declaring the alignment in the type lets the compiler pick the wider instruction without you writing any PTX by hand.

```cpp
#include <cuda_runtime.h>

// Blackwell-only variant: 32-byte per-thread vector copy
// (PTX: ld.global.v8.f32). Requires 32B alignment.
struct alignas(32) float8 { float v[8]; };

// Proof of 32-byte alignment
static_assert(alignof(float8) == 32, "float8 alignment must be 32 bytes");

__global__ void copyVector32B(const float8* __restrict__ in,
                              float8* __restrict__ out, int N8) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N8) {
        // Per-thread 32B load+store
        // NVCC emits ld.global.v8.f32/st.global.v8.f32 on sm_100
        out[idx] = in[idx];
    }
}

int main() {
    const int N = 1 << 20;
    const int N8 = N / 8;

    float8 *d_in, *d_out;
    // cudaMalloc returns pointers aligned to >=256 bytes
    cudaMalloc(&d_in, N8 * sizeof(float8));
    cudaMalloc(&d_out, N8 * sizeof(float8));

    dim3 block(256), grid((N8 + block.x - 1) / block.x);
    copyVector32B<<<grid, block>>>(d_in, d_out, N8);
    cudaDeviceSynchronize();

    cudaFree(d_in); cudaFree(d_out);
    return 0;
}
```

The 32-byte load only pays off when the compiler can prove 32-byte alignment. Otherwise it may split each access into two 16-byte instructions. That doubles the instruction count for the same bytes. A custom 8-float struct with no alignment proof still compiles into two 16-byte loads. The compiler behaves like a shipping clerk who uses the large box only when the item is known to fit.

The PyTorch version views the tensor as groups of four floats and clones it. A view changes only how the tensor is labeled, not where its bytes sit, so the reshape itself costs almost nothing. The clone is a contiguous copy, not an element-by-element one.

```python
import torch

def copy_vectorized(inp: torch.Tensor) -> torch.Tensor:
    # Reshape into groups of 4 floats for bulk copy
    vec = inp.view(-1, 4)
    # clone() on a contiguous CUDA tensor performs a device-to-device copy
    # using optimized runtime paths such as cudaMemcpyAsync().
    out_vec = vec.clone()
    return out_vec.view(-1)

# Usage
N = 1 << 20
inp = torch.arange(N, device='cuda', dtype=torch.float32)
out = copy_vectorized(inp)
```

Coalescing and vectorizing solve different problems, so they are easy to mix up. The table below puts them side by side.

| Aspect | Coalesced warp load (inter-thread) | Vectorizing (intra-thread) |
|---|---|---|
| Granularity | Threads ↔ contiguous memory addresses | Per thread ↔ vector loads |
| Typical fix | Contiguous indexing (stride = 1) | Use `float4`, a custom 32-byte struct with explicit 32-byte alignment, or a 32-byte-aligned vector type (e.g., Blackwell and CUDA 13+) |
| Transactions/warp | 32 threads × 4 bytes → 128 bytes, equal to 4 32-byte sectors if aligned (4 sectors) | 32 threads × 16 bytes → 512 bytes, equal to 4 128-byte transactions, which correspond to 16 32-byte sectors (16 sectors) |
| Instruction count change | Same number of loads | 1 vector load instead of 4 scalars |
| Benefit | Fewer scattered sectors | Perfectly sized, fewer sectors |

Use both together. Coalescing makes the warp hit one contiguous block, and vectorizing makes each thread fetch a wide chunk that fits that block. A simple way to remember it is that coalescing decides where the riders stand, and vectorizing decides how much each rider carries. Before Blackwell and CUDA 13, global vector loads topped out at 16 bytes per thread. Prefer the 32-byte types when your hardware and alignment allow.

Even a Blackwell thread that loads 32 bytes still gets serviced in 128-byte chunks. A 32-thread warp moving 32 bytes per thread moves 1,024 bytes, or 8 lines. Hopper's 16-byte version moves 512 bytes, or 4 lines. Both are fully efficient when aligned, so the choice between them is about how many instructions you want to issue, not about correctness.

---

## 3. Shared-Memory Tiling and Eliminating Bank Conflicts

Coalescing and vectorizing make every trip to off-chip HBM efficient, but they do not reduce how many times the kernel goes out to HBM. Imagine a cook who makes every trip to the warehouse full, yet still walks to the warehouse for the same flour again and again. In a naive matrix multiplication, every thread loops across an entire row and column and reads inputs directly from global memory. Each matrix element is fetched from off-chip HBM a thousand times, saturating the DRAM bus with redundant reads.

### 3.1 Tiling matrix multiplication in shared memory

Shared-memory tiling partitions the input matrices into square tiles stored in fast on-chip SRAM arrays. SRAM is the fast on-chip memory built from static RAM cells, and shared memory is one such array. The idea is to copy one small tile of each input into shared memory once, then let many threads use it. A thread block is a group of threads that can all see the same shared memory.

First, all threads in the thread block cooperatively load one float of each input tile from HBM using coalesced warp reads. Second, the block executes `__syncthreads()` to ensure the entire tile is resident in shared memory before any thread reads it. `__syncthreads()` is a barrier, so every thread in the block waits there until all of them have arrived.

Third, every thread loops across the elements of the cached tile and accumulates products from fast on-chip shared memory instead of slow off-chip HBM. Each global memory load is reused 32 times on chip. Fourth, the block calls `__syncthreads()` a second time before advancing to load the next tile. This second barrier prevents faster threads from overwriting the shared buffer while slower threads are still reading it. Think of a group of cooks sharing one cutting board. The first barrier means everyone waits until the ingredients are on the board. The second means nobody swaps in the next batch until everyone has finished chopping.

| Nsight Compute Metric | Before (`naiveMatMul`) | After (`tiledMatMul` `32 × 32`) | Architectural Interpretation |
|---|---:|---:|---|
| **Global Memory Load Sectors** | `9,800` | **`1,200`** | **`8.17x` (`~8x`) reduction** in 32-byte HBM sector reads from `32x` reuse |
| **DRAM Throughput (`% of peak`)** | `90%` (wasteful) | **`25%` (`3.6x` less)** | Desirable drop because redundant HBM traffic was removed (`10 GB/s -> 21 GB/s`) |
| **Arithmetic Intensity (`FLOPs/byte`)** | `1.5 FLOPs/byte` | **`8.0 FLOPs/byte`** | Shifts the kernel right along the Roofline toward compute-bound |
| **Achieved Occupancy (`%`)** | `42%` | **`89%`** | Fewer HBM stalls allow resident warps to make continuous progress |
| **Shared Memory Throughput (`% of peak`)** | `52%` | **`99%`** | Traffic shifted from off-chip HBM onto conflict-free on-chip SRAM |
| **Sustained FP32 Throughput (`GFLOPS`)** | `15 GFLOPS` | **`170 GFLOPS`** | **`~11.3x` (`~11x`) higher** compute throughput on `N = 1,024` |

Read the table as a chain of cause and effect. Fewer trips to HBM lower the DRAM throughput number, which looks like a bad sign but is actually the goal. The work moves into shared memory. Arithmetic intensity, the number of floating-point operations per byte moved, climbs as a result, and that moves the kernel toward the compute side of the Roofline.

### 3.2 Why you cannot blindly grow tiles forever: The `64 × 64` register budget

If a 32 by 32 tile speeds up matrix multiplication elevenfold, it is tempting to double the tile size again. Doubling is a natural instinct. However, growing the tile size increases per-thread register pressure and shared-memory consumption. Register pressure means each thread needs more of its private registers, and when registers run short, fewer blocks can live on the SM at once. That extra resource usage can cut the number of blocks that fit on each Streaming Multiprocessor.

Consider a 1,024-thread block computing a 64 by 64 output tile so that each thread computes a 2 by 2 subtile of four outputs. Each input tile consumes 16 KB of shared memory, or 32 KB for both input tiles. That footprint easily fits inside a Blackwell SM's usable shared memory. The binding constraint is the register file and the thread hardware limit per SM. The register file is the pool of registers the SM splits among its resident threads. The thread limit is the most threads one SM can hold at once.

In the minimal register case, the register file could hold five blocks by registers alone, but the SM thread ceiling caps residency at two blocks per SM. Residency means how many blocks are living on the SM at the same time. In a double-buffered case using more registers per thread, each block consumes more registers, which still fits two blocks per SM. If register usage climbs above 32 registers per thread on a 1,024-thread block, residency drops to a single block per SM. Even worse, excessive register demand spills registers to slow local memory in HBM. Spilling happens when the compiler runs out of registers and parks values in local memory, which is far slower.

Read the residency math as a budget. Each block asks for registers, the SM has a fixed pile of them, and the smallest pile sets the limit. The text block below shows the arithmetic for each case.

```text
64 x 64 FP32 Tile Shared-Memory and Register Residency Budget (ASP Ch 7 pp. 231-232; calc_tile_residency_and_register_budget):
  - Shared Memory Footprint:      64 x 64 x 4 B = 16,384 bytes (16 KB) per matrix tile; sA + sB = 32 KB/block (fits <= 7 blocks in 227 KB usable SMEM on 228 KB Blackwell SM)
  - Per-Thread Register Split:    Book range is ~12 to 22 regs/thread (handbook illustration for 12 regs: 4 accumulators + 2 A-tile + 2 B-tile + 4 index/loop = 12 regs/thread)
  - Minimal Case (12 regs/thread): 12 x 1,024 threads = 12,288 regs/block -> 65,536 // 12,288 = 5 blocks (61,440 regs), capped by 2,048 max threads/SM (64 warps) at 2 blocks/SM
  - Larger Case (22 regs/thread):  22 x 1,024 threads = 22,528 regs/block -> 65,536 // 22,528 = 2 blocks/SM (45,056 regs, 2,048 resident threads)
  - Register Ceiling Drop (>32):   > 32 regs/thread on 1,024 threads exceeds 32,768 regs/block -> drops residency to 1 block/SM (1,024 threads = 50% occupancy) or spills to HBM (max 255 regs/thread)
```

### 3.3 Shared-memory bank conflicts and `+1` column padding

Storing data in on-chip shared memory is only fast when all threads in a warp access distinct memory banks. Shared memory is divided into 32 independent banks of 4-byte width. Successive 4-byte words map to successive banks and wrap back to the first bank every 128 bytes. Think of 32 checkout lanes in a store. Traffic is fast when every shopper picks a different lane. If many shoppers pile into the same lane, the line backs up, and the hardware replays the access one step at a time.

```mermaid
flowchart TB
  subgraph Conflict["1. Unpadded __shared__ float tile[32][32] (Row Stride = 32 floats = 128 B)"]
    direction TB
    C1["Transpose Read: Lane i (0..31) reads tile[i][col]<br/>Linear word index = i * 32 + col"] --> C2["Bank = (i * 32 + col) mod 32 = col mod 32<br/>All 32 threads hit SAME bank -> 32-Way Conflict (4.8M, 4.0 ms)"]
  end

  subgraph Padded["2. Padded __shared__ float tile[32][33] (Row Stride = 33 floats, +3% / ~1 KB)"]
    direction TB
    P1["Transpose Read: Lane i (0..31) reads tile[i][col]<br/>Linear word index = i * 33 + col"] --> P2["Bank = (i * 33 + col) mod 32 = (i + col) mod 32<br/>All 32 threads hit 32 DISTINCT banks -> 0 Conflicts (1.3 ms = 3x)"]
  end
```

Three hardware rules govern how bank conflicts arise and how to eliminate them. Keep them in mind when you read the layout of any tile.

First, reading down a column of an unpadded 32 by 32 shared array during a matrix transpose causes a worst-case 32-way bank conflict. Reading down a column means each lane reads the next row below the one before it. Because each row has 32 floats, adjacent lanes reading down a column step by 32 words per thread. Modulo 32, every single thread in the warp maps to the exact same bank. That collision forces the hardware to replay the memory instruction 32 times in series.

Second, reading the exact same shared-memory address across multiple threads never causes a bank conflict. When all threads in a warp read the same element with identical indices, the shared-memory crossbar performs a single-cycle hardware broadcast. A broadcast sends one value to many readers at once, like a speaker announcing a message to a whole room. Bank conflicts only happen when multiple threads in a warp access different addresses within the same bank.

Third, adding one padding column or applying XOR index swizzling eliminates column bank conflicts completely. Declaring `__shared__ float tile[32][33]` adds one unused float per row and changes the row stride from 32 words to 33 words. Because 33 is coprime to 32, which means the two numbers share no common factor, lanes reading down a column map across 32 distinct banks with only about three percent memory overhead. XOR swizzling means mixing the column index with the row index using the exclusive-or bit operation, so the same data lands in different banks without wasting any space. Libraries such as CUTLASS achieve the same conflict-free spread with zero extra memory by XOR-swizzling the column index with the row index.

```text
Shared-Memory Bank Modulo Math (32 banks x 4-byte width = 128-byte wrap; analyze_shared_memory_bank_conflicts):
  - Row-Major Access (tile[row][lane], stride = 1 word):      Bank = (row * 32 + lane) mod 32 = lane mod 32 -> 32 distinct banks (1-way, 0 bank conflicts)
  - Unpadded Column Read (tile[lane][col] on tile[32][32]):   Bank = (lane * 32 + col) mod 32 = col mod 32  -> all 32 lanes hit Bank col (32-way conflict!)
  - Padded Column Read (tile[lane][col] on tile[32][33]):     Bank = (lane * 33 + col) mod 32 = (lane + col) mod 32 -> 32 distinct banks (0 conflicts; 1/32 = 3.125% ~ 3% / 128 B overhead on 4 KB tile)
  - Uniform Broadcast (tile[const_r][const_c] across 32 lanes): Same address across all lanes -> hardware single-cycle broadcast (0 bank conflicts)
```

| Nsight Compute Metric | Before (`tile[32][32]`, no padding) | After (`tile[32][33]`, `+1` padding) | Improvement |
|---|---:|---:|---|
| **Shared-Memory Load Bank Conflicts** | `4.8 million` | **`0`** | **100% eliminated** |
| **Shared-Memory Utilization (`% of peak`)** | `52%` | **`100%`** | Full 32-bank parallel throughput |
| **Warp Stall Fraction (`memory`)** | `38%` | **`0.5%`** | Eliminates shared-memory replay stalls |
| **Kernel Execution Time (`ms`)** | `4.0 ms` (`4 ms`) | **`1.3 ms`** | **`~3x` faster** (`N = 1,024` transpose) |

Read the Nsight Compute rows as a set of questions. The first asks how many shared-memory conflicts the kernel suffers. The second asks how much of the shared-memory throughput the kernel uses. The third asks how often warps stall waiting for the memory system. The fourth asks how long the whole kernel runs. A fix is working when the first three move the right way and the fourth follows. A conflict count that falls to zero while the runtime stays flat means the conflicts were not the bottleneck, and you should go back to the stall breakdown to find the real one.

**Whenever a kernel reads columns of a 32-wide shared-memory tile, pad the inner dimension to 33 elements or XOR-swizzle the column index.** This ensures every lane in the warp hits a distinct bank. Check `l1tex__data_bank_conflicts_pipe_lsu_mem_shared_op_ld.sum` in Nsight Compute to confirm that shared-memory bank conflicts drop to zero. If the counter does not move, the padding did not reach the array you think it did.

### 3.4 Naive and tiled matrix multiply code

In a naive kernel, each thread computes one element of C. For every step of the loop, it reads a value of A and a value of B straight from global memory. The host is the CPU side, and the device is the GPU. The kernel below shows that pattern. The host code allocates N by N matrices, copies them to the device, and launches 32 by 32 thread blocks. Here `row` and `col` are the coordinates of the element in the output matrix C.

```cpp
#include <cuda_runtime.h>

__global__ void naiveMatMul(const float* A, const float* B, float* C, int N) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < N && col < N) {
        float sum = 0.0f;
        for (int k = 0; k < N; ++k) {
            // Each thread loads A[row, k] and B[k, col]
            // from global memory for every k.
            // This is very memory heavy.
            sum += A[row * N + k] * B[k * N + col];
        }
        C[row * N + col] = sum;
    }
}

// Launch for N = 1024:
// dim3 block(32, 32);
// dim3 grid((N + 31) / 32, (N + 31) / 32);
// naiveMatMul<<<grid, block>>>(d_A, d_B, d_C, N);
```

The PyTorch naive version uses nested Python loops. It is slow on purpose, so the redundant loads are easy to see. Each dot product reloads its row and column from global memory. A dot product is the sum of products of matching entries from a row and a column. The inner work runs on the GPU, but the GPU spends most of its time waiting on memory. The Python loops also launch one small operation after another, so the timing mostly measures launch overhead and memory waiting, not the matrix math itself.

```python
import torch

def naive_matmul(A, B):
    N = A.size(0)
    C = torch.zeros((N, N), device='cuda')
    for i in range(N):
        for j in range(N):
            # Each dot product loads A[i,:] B[:,j] from global memory repeatedly
            C[i, j] = (A[i, :] * B[:, j]).sum()
    return C

# Usage
N = 1024
A = torch.ones((N, N), device='cuda', dtype=torch.float32)
B = torch.ones((N, N), device='cuda', dtype=torch.float32)
C = naive_matmul(A, B)
```

The tiled kernel loads one 32 by 32 tile of A and one of B into shared memory. Then every thread in the block reuses those tiles. A 32 by 32 tile matches the warp size of 32, so each warp loads one row of the tile at a time. The match is convenient rather than required. It keeps each warp's loads lined up with one row of the tile, which keeps the reads coalesced.

```cpp
#include <cuda_runtime.h>

#define TILE_SIZE 32

__global__ void tiledMatMul(const float* A, const float* B, float* C, int N) {
    __shared__ float sA[TILE_SIZE][TILE_SIZE];
    __shared__ float sB[TILE_SIZE][TILE_SIZE];

    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;
    float sum = 0.0f;

    // compute partial results using the tile
    // in shared memory
    for (int t = 0; t < N; t += TILE_SIZE) {
        // Cooperative load of a tile of A and B into shared memory
        // Load tile A with boundary check
        if (row < N && (t + threadIdx.x) < N) {
            sA[threadIdx.y][threadIdx.x] = A[row * N + t + threadIdx.x];
        } else {
            sA[threadIdx.y][threadIdx.x] = 0.0f;
        }

        // Load tile B with boundary check
        if ((t + threadIdx.y) < N && col < N) {
            sB[threadIdx.y][threadIdx.x] = B[(t + threadIdx.y) * N + col];
        } else {
            sB[threadIdx.y][threadIdx.x] = 0.0f;
        }

        // Wait until the whole tile is in shared memory
        __syncthreads();

        // Compute using the tile loaded in shared memory
        for (int k = 0; k < TILE_SIZE; ++k) {
            sum += sA[threadIdx.y][k] * sB[k][threadIdx.x];
        }

        // Wait until every thread has finished using the tile
        __syncthreads();
    }

    if (row < N && col < N) {
        C[row * N + col] = sum;
    }
}
```

Each block loads its tiles once and then reuses them. A multiply-accumulate is one multiply followed by one add into a running sum. Each value in a tile feeds 32 of these in a row, which cuts global reads for those values by 32 times. *AI Systems Performance Engineering*, Chapter 7, counts an 8 times drop in global memory accesses per thread. The measured run in that chapter cut 9,800 global load sectors to 1,200.

The PyTorch version tiles by hand and calls `torch.mm` on each block. The tile loop is in Python, but `torch.mm` runs an optimized kernel that tiles internally. The code below shows the structure.

```python
import torch

def tiled_matmul(A, B, tile_size=32):
    N = A.size(0)
    C = torch.zeros((N, N), device='cuda')
    for i in range(0, N, tile_size):
        for j in range(0, N, tile_size):
            C_block = torch.zeros((tile_size, tile_size), device='cuda')
            for k in range(0, N, tile_size):
                A_block = A[i:i+tile_size, k:k+tile_size]
                B_block = B[k:k+tile_size, j:j+tile_size]
                # torch.mm uses an optimized kernel (likely tiling internally)
                C_block += torch.mm(A_block, B_block)
            C[i:i+tile_size, j:j+tile_size] = C_block
    return C

# Usage
N = 1024
A = torch.ones((N, N), device='cuda', dtype=torch.float32)
B = torch.ones((N, N), device='cuda', dtype=torch.float32)
C = tiled_matmul(A, B)
```

Tiling cuts DRAM traffic and raises arithmetic intensity, because each byte pulled from memory feeds more math. The measured run in that chapter moved the kernel from 15 to 170 GFLOPS. GFLOPS is billions of floating-point operations per second. Its DRAM throughput fell from 90% to 25% of peak, which is the wanted result. Lower DRAM throughput here is good news, because the DRAM bus is no longer the bottleneck. Those GFLOPS numbers are low because the matrix is small. Bigger problems move closer to peak.

Tiling is the same idea that high-performance libraries use. NVIDIA's CUTLASS exposes templated tile iterators and profilers in C++ and Python. TorchInductor, built on OpenAI Triton, generates tiled kernels when shapes and alignment allow. cuBLAS is NVIDIA's linear algebra library, and cuDNN is its library of deep learning primitives. Both use similar blocking at the thread, warp, and block levels. NVIDIA also announced a Python-first API called cuTile in early 2025, built on an intermediate representation called TileIR.

Use a library when it fits. Calling `torch.mm`, `torch.matmul`, or `cublasSgemm` already does this tiling and coalescing. Write your own tiles when you need a case the libraries do not cover, or when you must explain a slow kernel. A practical rule is to measure the library first and write your own tile only after you have found it lacking. Also keep in mind that a 32 by 32 tile makes warp threads share banks on column reads. Section 3.5 shows the fix.

### 3.5 Transpose with and without padding, and the stride-32 trap

A matrix transpose is the clearest bank-conflict example. Transposes show up whenever you flip a layout, such as turning row-major data into column-major data for a library call. The kernel below writes its tile row by row, which is coalesced. It then reads the tile transposed. The read is where the conflict happens.

```cpp
#include <cuda_runtime.h>

#define TILE_DIM 32

__global__ void transposeNaive(const float *idata, float *odata, int width) {
    __shared__ float tile[TILE_DIM][TILE_DIM];

    int x = blockIdx.x * TILE_DIM + threadIdx.x;
    int y = blockIdx.y * TILE_DIM + threadIdx.y;

    // threads in a warp write a row
    tile[threadIdx.y][threadIdx.x] = idata[y * width + x];
    __syncthreads();

    // Read from shared memory with transposed indices
    // This is a classic case of all threads in a warp
    // hitting the same bank causing a bank conflict
    odata[x * width + y] = tile[threadIdx.x][threadIdx.y];
}
```

Each row of a 32 by 32 float tile is 32 floats, or 128 bytes. Lanes that step down a column jump 128 bytes each time. Every one of those jumps lands back on bank 0. All 32 lanes collide on one bank, and the hardware replays the access 32 times in series. It is the checkout-lane picture again, with every shopper choosing the same lane.

The same trap appears with any stride of 32 floats. Here the index is `threadIdx.x * 32`, so the byte address is `threadIdx.x * 128`. Every thread then hits bank 0. The stride is the thing to check. A pattern like this often hides in code that looks innocent.

```cpp
// Allocate a shared buffer big enough for several warps (warpCount)
__shared__ float arr[32 * warpCount];
// Each thread reads from arr[threadIdx.x * 32]
float x = arr[threadIdx.x * 32];
```

Nsight Compute shows this cost in the Shared Memory section. You see more bank conflicts and lower shared-memory efficiency. Nsight Systems is the timeline profiler that shows the whole application, while Nsight Compute zooms into one kernel. Use the first to find the slow kernel and the second to see why it is slow. If a kernel does not speed up the way its buffering should, check for conflicts first.

Padding fixes it. Adding one unused column makes each row 33 floats. Lane k then reads from a bank that shifts from row to row, so no two lanes collide. The unused column is wasted on purpose. It costs very little memory and changes which bank each row begins on. The padded transpose looks like this.

```cpp
#include <cuda_runtime.h>

#define TILE_DIM 32
#define PAD 1  // padding columns to avoid bank conflicts

__global__ void transposePadded(const float *idata, float *odata, int width) {
    // Each row is TILE_DIM+1 elements to shift bank mapping
    __shared__ float tile[TILE_DIM][TILE_DIM + PAD];

    int x = blockIdx.x * TILE_DIM + threadIdx.x;
    int y = blockIdx.y * TILE_DIM + threadIdx.y;

    tile[threadIdx.y][threadIdx.x] = idata[y * width + x];
    __syncthreads();

    odata[x * width + y] = tile[threadIdx.x][threadIdx.y];
}
```

The cost is small. The padding adds about 3% memory for a 32-wide tile, which is about 1 KB. The measured run in that chapter dropped bank conflicts from 4.8 million to zero and took the kernel from 4 ms to 1.3 ms.

PyTorch has no high-level padding API. You would write the padded tile in a CUDA kernel and load it with `torch.utils.cpp_extension`, which is the route for compiling your own CUDA code and calling it from Python. In practice, cuDNN and cuBLAS already avoid these conflicts inside their kernels.

Swizzling is the other fix. It changes the linear index with a compile-time transform, such as an XOR with a bit mask, so that sequential threads land on different banks. A compile-time transform is worked out when the code is built, so it costs nothing at run time. It removes the padding overhead entirely. CUTLASS uses this kind of index swizzling in its tile iterators.

The tiling, padding, and transpose sections all came back to one habit: look at the layout before you look at the math. Tiling cut the number of trips to HBM. Padding and swizzling removed the collisions inside shared memory. Each fix changed where the data sat, not what the kernel computed, which is why the results stayed the same while the timing moved. Keep that rule in mind when you read a profile. If a change alters the answer, it is not a memory-layout fix, and it needs a different kind of review.

---

## 4. Warp Shuffle Intrinsics, Read-Only Caches, and TMA Prefetching

Even after coalescing global accesses and padding shared-memory tiles, kernels still lose performance in three common situations. Think of a kitchen where the cooks are fast but spend their time waiting. The three situations are three kinds of waiting. Warps waste shared memory and barrier cycles on intra-warp reductions. Lookup tables thrash the L1 data cache because the compiler cannot prove they are read-only. Finally, Streaming Multiprocessors stall for hundreds of cycles waiting on synchronous DRAM loads.

### 4.1 Intra-warp register reductions with `__shfl_down_sync`

When threads within the same warp need to exchange values, or compute a sum or maximum for softmax, using shared memory is unnecessary. Softmax is a function that turns a row of scores into probabilities, and it needs a maximum and a sum across that row. Writing partial values to shared memory consumes scarce on-chip SRAM. It also forces warps to wait at `__syncthreads()` barriers.

CUDA warp shuffle intrinsics such as `__shfl_sync`, `__shfl_down_sync`, and `__shfl_xor_sync` let threads read each other's registers directly across the warp. Intrinsics are built-in functions the compiler turns into a single instruction. A butterfly reduction using `__shfl_down_sync` steps through five halving offsets. Each step pairs lanes at a distance, adds the partner's value, and then halves the distance, so the partial sums fold in on themselves like a zipper. After five register-to-register steps, the first lane holds the sum of all 32 lanes with zero shared memory and zero bank conflicts.

```cpp
// Warp-level butterfly reduction in registers (0 bytes of Shared Memory, 0 bank conflicts)
unsigned mask = __activemask();
float val = threadVal; // Each of the 32 lanes starts with its private partial sum
for (int offset = 16; offset > 0; offset >>= 1) {
    val += __shfl_down_sync(mask, val, offset);
}
// After 5 register steps (offsets 16 -> 8 -> 4 -> 2 -> 1), Lane 0 holds the sum of all 32 lanes (1..32 -> 528.0)
```

Keep the hardware scope boundary in mind when using warp shuffles. A warp shuffle can only exchange registers among the 32 lanes of a single warp. Reducing across multiple warps in a thread block still requires a small shared-memory scratchpad or Cooperative Groups barriers such as `thread_group.shuffle()` and `__reduce_sync()`. A useful way to remember this is that a shuffle is a conversation inside one group of 32, and a block-wide reduction needs a message that crosses groups.

### 4.2 Routing immutable lookup tables through the read-only data cache

Inference kernels frequently perform random gather lookups into immutable tables such as token embeddings or quantization scale factors. An embedding table maps each token to a vector of numbers. A quantization scale factor is a number used to convert low-precision values back to real ones. CUDA provides a 64 KB `__constant__` memory space backed by a small per-SM constant cache. However, that space is too small for large model tables, and it only runs at full speed when all threads in a warp read the exact same address.

For larger lookup tables, the GPU's L1 read-only data cache can serve scattered reads without polluting the regular read/write cache lines. Polluting a cache means filling it with data that will not be reused, so the lines that matter get pushed out. However, the compiler will only emit read-only `__ldg()` loads automatically if it can prove that the table pointer is never written and never aliases another pointer. Aliasing means two pointers may point at the same memory, so a write through one could change what the other reads. Adding `const __restrict__` to the input pointer gives the compiler that guarantee and cuts off-chip DRAM traffic by three times.

| Nsight Compute Metric | Before (`const float* table`, no `__restrict__`) | After (`const float* __restrict__ table`) | Improvement |
|---|---:|---:|---|
| **Global Memory Load Efficiency** | `52%` | **`97%`** | Most fetched cache lines carry useful data |
| **DRAM Throughput (`GB/s`)** | `600 GB/s` | **`200 GB/s`** | **`3.0x` less off-chip DRAM traffic** |
| **L2 Read Throughput (`GB/s`)** | `1,500 GB/s` | **`1,800 GB/s`** | Lookups served from on-chip cache hierarchy |
| **SM Active `%`** | `45%` | **`93%`** | Nearly every cycle has active work |
| **Kernel Execution Time (`ms`)** | `2.5 ms` | **`1.0 ms`** | **`2.5x` faster** (`T = 1,024`, `N = 1 << 20`) |

For spatial interpolation workloads, CUDA also provides `cudaTextureObject_t` with `tex1Dfetch` and `tex2D` alongside surface objects. Interpolation means estimating values between samples, as in resizing an image. Texture hardware can blend nearby values in hardware. Legacy texture references are deprecated, which means CUDA still accepts them but recommends newer APIs. For standard one-dimensional AI tensors and embedding tables, qualifying pointers with `const __restrict__` is the clean and portable solution.

### 4.3 Hiding 800-cycle DRAM latency with TMA double buffering

Picture a cook who sends a runner to the pantry and then stands still until the runner returns. That wait is the round trip. Even a coalesced, vectorized load faces an approximately 800-cycle HBM round-trip latency on Hopper and Blackwell GPUs. When warps issue synchronous global-to-shared loads using their own load/store units and block until the data arrives, Streaming Multiprocessors sit idle during the memory transit time.

On Hopper and Blackwell, the Tensor Memory Accelerator (`cp.async.bulk.*`) offloads bulk tile transfers between global HBM and shared memory onto a dedicated hardware DMA engine. DMA stands for direct memory access, a helper that moves data without the cores doing the copy. Pairing the Tensor Memory Accelerator with the `libcu++` `<cuda/pipeline>` API and two ping-pong shared buffers lets the block prime the first tile. Ping-pong means the two buffers swap roles on each step, like two trays in a kitchen where one is filled while the other is served. Warps then overlap asynchronous prefetching of the next tile while computing on the current tile.

```cpp
// Block-scoped 2-stage TMA double-buffering pattern (ASP Ch 7 pp. 246-248)
__shared__ cuda::pipeline_shared_state<cuda::thread_scope_block, 2> state;
auto pipe = cuda::make_pipeline(cuda::this_thread_block(), &state);

// 1. Prime Stage 0: TMA asynchronously copies tile 0 from HBM -> tiles[0] (16 B Hopper / 32 B Blackwell alignment)
pipe.producer_acquire();
cuda::memcpy_async(tiles[0], global_ptr + 0 * TILE_SIZE,
                   cuda::aligned_size_t<32>{bytes}, pipe);
pipe.producer_commit();

// 2. Main loop: wait for tile t-1, compute on it, and overlap TMA prefetch of tile t
for (int t = 1; t < nTiles; ++t) {
    pipe.consumer_wait();
    processTile(tiles[(t - 1) & 1]);
    pipe.consumer_release();

    pipe.producer_acquire();
    cuda::memcpy_async(tiles[t & 1], global_ptr + t * TILE_SIZE,
                       cuda::aligned_size_t<32>{bytes}, pipe);
    pipe.producer_commit();
}
pipe.consumer_wait();
processTile(tiles[(nTiles - 1) & 1]);
pipe.consumer_release();
```

The table below compares the same tile loop without prefetch and with the TMA double buffer.

| Nsight Compute Metric | Before (No Prefetch) | After (`TMA` + `cuda::memcpy_async` Double Buffering) | Improvement |
|---|---:|---:|---|
| **Global Memory Load Efficiency** | `23%` | **`99%`** | **`4.3x` higher** |
| **Average Sectors per Request** | `6.4` | **`4.0` (optimal)** | Coalesced 128-byte TMA bulk transfers |
| **DRAM Throughput (`% of peak`)** | `25%` | **`90%`** | **`3.6x` higher** sustained HBM utilization |
| **SM Active `%`** | `62%` | **`100%`** | Warps compute continuously while TMA fetches next tile |
| **Kernel Execution Time (`ms`)** | `18 ms` | **`7 ms`** | **`~2.6x` faster** (hides `~800-cycle` DRAM latency) |

**Use `__shfl_down_sync` for intra-warp reductions and mark read-only lookup pointers `const __restrict__`.** In multi-tile loops, double-buffer tile loads with `cuda::memcpy_async` so warps never stall waiting on synchronous DRAM loads. In plain words, the warps should have the next tile ready before they finish the current one.

### 4.4 Lookup tables: a naive kernel versus a `const __restrict__` kernel

Take an embedding lookup. A large table is read-only during inference, and many threads read from it at once. A naive kernel sends every read to global memory, even though the table never changes. An embedding lookup is the step where a model turns token IDs into vectors, so it runs on every request.

The `__constant__` memory space is 64 KB and has a small per-SM cache. It is too small for large tables. It also runs at full speed only when all threads in a warp read the same address. A large read-only table belongs in the L1 read-only cache instead. The naive kernel below does not use that path.

```cpp
#include <cuda_runtime.h>
#define T 1024

__global__ void naiveLookup(const float* table, float* out, int N) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        // __ldg not used here, each access goes to
        // global memory without using read-only cache
        int t = idx % T;
        out[idx] = table[t];
    }
}
```

The optimized kernel marks the table pointer as `const __restrict__`. That tells the compiler the data is immutable and not aliased. The compiler can then route the loads through the read-only path.

```cpp
#include <cuda_runtime.h>
#define T 1024

__global__ void lookup(const float* __restrict__ table,
                       float* out, int N) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        int t = idx % T;
        // Compiler can turn this into a load from the
        // read-only cache for faster loads
        out[idx] = table[t];
    }
}
```

On modern GPUs, global loads are cached in L2 and often in L1 too. The read-only path has lower latency, especially for broadcast reads, where many threads want the same value. It also does not evict other cached data. You rarely need the older `__ldg()` intrinsic now, because the compiler uses the path for `const __restrict__` pointers when it is safe.

The common mistake is leaving off the qualifier. The compiler then cannot use the read-only path, and every access becomes a plain global load. You can spot this in a profile. The same addresses are fetched from DRAM again and again, the instruction stream has no `__ldg()` loads, the L2 hit rate for that array is low, and DRAM throughput looks like an uncached workload.

A warp that reads one constant address gets a broadcast. The hardware serves all 32 lanes in one transaction, instead of 32 separate loads. This is the same broadcast idea from the bank section, now applied to a read-only table.

In PyTorch, you could apply the same trick by writing a small CUDA extension with `torch.utils.cpp_extension` that declares the table pointer as `const __restrict__`. You could also use the PyTorch compiler to optimize this kind of code. The vectorized PyTorch version below does the lookup with a single gather.

```python
import torch

def vectorized_lookup(table, N):
    flat = table.view(-1)
    T = flat.size(0)
    # build indices [0,1,2,...,N-1] % T all on GPU
    idx = torch.arange(N, device=flat.device) % T
    # one gather kernel does all N loads in parallel
    return flat.index_select(0, idx)

# Usage
T = 1024
N = 1 << 20
table = torch.arange(T, dtype=torch.float32, device='cuda')
out = vectorized_lookup(table, N)
```

Texture and surface objects are the other read-only option. A `cudaTextureObject_t` read with `tex1Dfetch` or `tex2D` suits data with strong two- or three-dimensional locality. The legacy texture reference APIs are deprecated. For one-dimensional tensors and embedding tables, `const __restrict__` is the simpler choice.

### 4.5 A full TMA double-buffer kernel

Section 4.3 showed the pattern in pieces. This kernel puts the whole thing together. It uses two shared tiles and a block-scoped pipeline. The function `processTile` is the compute step that you supply. Think of it as the place where your real math goes, while the rest of the kernel keeps the next tile moving in.

The vector width is chosen at the top. CUDA 13 and later on Blackwell prefer 32-byte vectors, and `-DUSE_256B_VEC` forces that choice. A macro is a compile-time switch, so the choice is made when the file is built, not while the kernel runs.

The kernel below is long, so read it in parts. The first part picks the vector width at compile time. The second part declares two shared tiles and a block-scoped pipeline. The third part primes the pipeline with the first copy. The loop then overlaps the compute on one tile with the copy of the next. The last part waits for the final tile and computes on it. Each part maps to one of the five steps described below, so you can match the code to the explanation.

```cpp
#include <cuda/pipeline>
#include <cuda_runtime.h>
#include <cstdint>
#include <cassert>

#define TILE_SIZE 1024  // example tile size

// User-provided compute function operating on a shared-memory tile
__device__ void processTile(const float* tile);

// --- choose vector width ---------------------------------------------
// Prefer 32B vectors on CUDA 13+/Blackwell.
// Define -DUSE_256B_VEC to force.
#ifndef VEC_BYTES
#if defined(USE_256B_VEC) || (defined(CUDA_VERSION) && CUDA_VERSION >= 13000)
#define VEC_BYTES 32  // 256-bit: v8.f32, double4
#else
#define VEC_BYTES 16  // 128-bit: v4.f32, float4
#endif
#endif

__global__ void kernelWithTMA(const float* __restrict__ global_ptr,
                              int nTiles) {
    // Two ping-pong buffers in shared memory
    __shared__ __align__(VEC_BYTES) float tile0[TILE_SIZE];
    __shared__ __align__(VEC_BYTES) float tile1[TILE_SIZE];
    float* tiles[2] = { tile0, tile1 };

    constexpr int VEC_ELEMS = VEC_BYTES / sizeof(float);  // 4 (128b) or 8 (256b)
    constexpr int WARP = 32;

    // Alignment / size guards for vectorized copies
    static_assert((TILE_SIZE % (WARP * VEC_ELEMS)) == 0,
                  "TILE_SIZE must be a multiple of WARP_SIZE * VEC_ELEMS");
    static_assert(((TILE_SIZE * sizeof(float)) % VEC_BYTES) == 0,
                  "Tile byte size must be a multiple of VEC_BYTES");
    assert((reinterpret_cast<std::uintptr_t>(global_ptr) % VEC_BYTES) == 0);

    size_t bytes = TILE_SIZE * sizeof(float);

    // Block-scoped pipeline for TMA
    __shared__ cuda::pipeline_shared_state<cuda::thread_scope_block, 2> state;
    auto pipe = cuda::make_pipeline(cuda::this_thread_block(), &state);

    // Prime the pipeline with the first async copy into tile0
    pipe.producer_acquire();
    cuda::memcpy_async(tiles[0],
                       global_ptr + 0 * TILE_SIZE,
                       cuda::aligned_size_t<32>{bytes},
                       pipe);
    pipe.producer_commit();

    // Loop over the remaining tiles
    for (int t = 1; t < nTiles; ++t) {
        // Wait for the previous copy to finish, then compute on it
        pipe.consumer_wait();
        processTile(tiles[(t - 1) & 1]);
        pipe.consumer_release();

        // Enqueue the next async copy into the alternate buffer
        pipe.producer_acquire();
        cuda::memcpy_async(tiles[t & 1],
                           global_ptr + t * TILE_SIZE,
                           cuda::aligned_size_t<32>{bytes},
                           pipe);
        pipe.producer_commit();
    }

    // Final wait and compute on the last tile
    pipe.consumer_wait();
    processTile(tiles[(nTiles - 1) & 1]);
    pipe.consumer_release();
}
```

The pattern has five steps. First, prime the pipeline by starting the copy of tile 0. Second, wait for that tile and compute on it. Third, start the copy of the next tile into the other buffer. Fourth, repeat until the last tile. Fifth, wait for the last tile and compute on it. Read the loop as a rhythm. The copy for the next tile runs while the current tile is being processed, and the two never touch the same buffer at the same time.

While the TMA streams the next tile, the warps compute on the current one. The load and store units stay free for other work. That overlap is what hides the roughly 800-cycle DRAM latency. The TMA also handles 1D to 5D bulk copies with arbitrary strides, without blocking the SM instruction pipeline. Bulk copies move a whole block of data in one request instead of one element at a time.

Two habits follow from this. Use the highest-level pipeline API you have, because it picks the TMA path when alignment and direction allow. Also check that host buffers are pinned. Pinned memory is host memory the operating system is not allowed to move, so the GPU can read it directly. Pageable memory is the normal kind, which the operating system can move around. Pageable memory turns off the DMA overlap that `cudaMemcpyAsync` on multiple streams needs.

---

## 5. Commands and Profiling Workflows That Matter

Imagine a kernel that runs slowly on a Monday, and the team spends the day arguing about whether the cause is the memory layout, the banks, or the waiting. Guessing wastes days. Without hardware performance counters, developers guess at whether a slow kernel is suffering from uncoalesced global reads, shared-memory bank conflicts, or synchronous DRAM stalls. Compiling with line-table information and querying key Nsight Compute metrics isolates the exact memory bottleneck in seconds.

All Nsight Compute and compilation commands below follow *AI Systems Performance Engineering*, Chapter 7. This handbook builds without an attached GPU, so the `nvcc` and `ncu` commands in this section were not run on a live cluster. Treat them as a guide to the workflow, then check them on your own hardware.

### 5.1 Profile global coalescing, sector counts, and shared-memory bank conflicts with `ncu`

```bash
# 1. Compile kernels with lineinfo so Nsight Compute maps metrics to exact C++ source lines (untested here)
nvcc -O3 -lineinfo -arch=sm_90 memory_kernels.cu -o memory_kernels

# 2. Profile DRAM throughput %, Global Load Efficiency, and Average Sectors per Request (ASP Ch 7 p. 250) (untested here)
ncu --metrics \
  gpu__dram_throughput.avg.pct_of_peak_sustained_elapsed,\
  smsp__sass_average_data_bytes_per_sector_mem_global_op_ld.pct,\
  l1tex__average_t_sectors_per_request_pipe_lsu_mem_global_op_ld.ratio,\
  l1tex__data_bank_conflicts_pipe_lsu_mem_shared_op_ld.sum,\
  sm__warps_active.avg.pct_of_peak_sustained_active \
  ./memory_kernels
```

**Always compile profiling builds with `-lineinfo` so Nsight Compute attributes sector waste and bank conflicts directly to the offending C++ source line.** The flag keeps a map from machine code back to your source lines, so the counters point at a line you can edit. Without it, you see a kernel name and a percentage, but not the line that caused the problem.

---

## 6. How It Fails: Six Production Memory-Access and Profiling Failure Modes

When a production kernel misses its latency or throughput target, the Nsight Compute counters usually point to one of six memory-access failure modes. Each row below pairs a symptom you can see with a root cause and a fix. Match the symptom first, then read the root cause to confirm the match.

The table is organized by failure, so each row starts from a symptom you may already see in a profile. Read the symptom column first and check the numbers against your own counters. Then read the root cause to see why the counter moved. The fix column is the last step, and it is only safe after the symptom and the cause agree. A table row is a hypothesis to test, not a diagnosis by itself.

| # | Failure Mode | Nsight Compute Symptom | Root Cause | Fix |
|---|---|---|---|---|
| **1** | **Strided / `AoS` / `index_select` uncoalesced global loads** | `DRAM Throughput = 25%`, `Global Memory Load Efficiency = 23%`, `Average Sectors per Request = 8.0` (up to `32.0`), runtime `4.8 ms` | Adjacent threads in a warp index memory with `stride > 1` (`in[idx * 2]`, `AoS` structs, or `torch.index_select` gather), touching multiple 128-byte cache lines per warp | Restructure layout to Structure of Arrays (`SoA`) and contiguous `stride = 1` (`in[idx]`), reducing sectors/request to `4.0` (`1.3 ms`, `3.7x` faster) |
| **2** | **Scalar loads or misaligned `float4` / `float8` casts** | `Global Memory Load Efficiency = 28%`, `Average Sectors per Request = 31.8`, or `cudaErrorMisalignedAddress` crash | Kernel issues 4-byte scalar loads instead of wide vector loads, or casts `d_ptr + offset` to `float4*` / `float8*` when `offset` is not a multiple of `16 B` (`4` floats) or `32 B` (`8` floats) | Use `float4` (`16 B`, `ld.global.v4.f32`) on Hopper or `alignas(32) float8` (`32 B`, `ld.global.v8.f32`) on Blackwell (CUDA 13+), ensuring `offset % 4 == 0` or `offset % 8 == 0` (`1.2 ms`, `3.5x` faster) |
| **3** | **Redundant HBM loads in untiled GEMM / attention kernels** | `DRAM Throughput = 90%`, `Global Load Sectors = 9,800`, `Achieved Occupancy = 42%`, compute stuck at `15 GFLOPS` (`1.5 FLOPs/byte`) | Inner loop reads `A[row, k]` and `B[k, col]` directly from global HBM on every step (`N` redundant loads per element) | Stage `32 × 32` tiles in `__shared__` memory with `__syncthreads()`, cutting global load sectors to `1,200` and raising throughput to `170 GFLOPS` (`~11x`) |
| **4** | **Oversized tile (`64 × 64`+) exhausting registers per SM** | Increasing tile size reduces achieved occupancy below `50%` or triggers local-memory register spills (`100s–1,000` cycles) | A `1,024`-thread block using `> 32` registers/thread exceeds half of the SM's `65,536`-register file, dropping residency from `2` blocks (`2,048` threads) to `1` block (pp. 231–232) | Balance tile size (`32 × 32` vs `64 × 64`) against `65,536` regs/SM and `227 KB` usable SMEM using `ncu` occupancy reports or `CUTLASS` / `cuTile` autotuners |
| **5** | **32-way Shared-Memory Bank Conflicts on column reads (`tile[32][32]`)** | `Shared-Memory Load Bank Conflicts = 4.8 million`, `Shared-Memory Utilization = 52%`, `Warp Stall Fraction (memory) = 38%`, runtime `4.0 ms` | Reading down a column of `__shared__ float tile[32][32]` strides by `32 floats = 128 B`, mapping all 32 lanes to `Bank 0` (`32`-way serialization) | Pad shared array to `__shared__ float tile[32][33]` (`+1` column = `~3%` / `1 KB` overhead) or apply XOR index swizzling, dropping conflicts to `0` (`1.3 ms`, `3x` faster) |
| **6** | **Missing `const __restrict__` on read-only tables or unpipelined `800-cycle` DRAM loads** | High DRAM traffic (`600 GB/s`) and low `SM Active = 45%` on lookup tables, or warps stalled waiting on synchronous global-to-shared loads (`18 ms`) | Compiler cannot prove table immutability/non-aliasing without `const __restrict__`, and SM `LD/ST` units stall on 800-cycle HBM round trips | Mark immutable tables `const __restrict__` (`2.5 ms -> 1.0 ms`), use `__shfl_down_sync` for intra-warp reductions, and double-buffer tile loads with `TMA` (`cuda::memcpy_async` + `cuda::pipeline`, `18 ms -> 7 ms`) |

**Treat every Nsight Compute counter as a pointer to a specific hardware unit.** Sector counts diagnose global coalescing, bank conflict counters diagnose shared memory layout, and DRAM versus L2 throughput diagnoses read-only caching. A counter is a clue, not a verdict. Confirm the clue by changing one thing and measuring again.

---

## 7. Hands-On Lab: Verify Coalescing Sector Math, Vectorized Loads, Shared-Memory Tiling, Bank Padding, and Warp Shuffles

**Venue:** Any Linux machine or Nebius GPU VM with Python 3.10+. This lab runs deterministically using standard library Python, so it does not need a GPU to pass. All `nvcc` and `ncu` commands sit in Section 5 and carry the `(untested here)` marker, which means they were not run on a live cluster.

Run `code/part10/memory_access_patterns_lab.py` to execute all checks. Each check prints a line starting with PASS or FAIL, so one run tells you which claim in the chapter holds on your machine.

```bash
python3 code/part10/memory_access_patterns_lab.py
```

Expected output (`25 passed, 0 failed`):

```text
=== Chapter 10.13 Lab: Memory Access Patterns and Profiling (ASP Chapter 7) ===
  [PASS] ASP Ch7 p.216: Aligned stride-1 FP32 warp load touches 1 x 128B cache line = 4.0 x 32B sectors (100% load efficiency)
  [PASS] ASP Ch7 p.216: Misaligned stride-1 FP32 warp load (offset +4B) straddles 2 cache lines and fetches 5 sectors
  [PASS] ASP Ch7 p.219 & Table 7-1: Stride-2 FP32 warp load touches 8.0 sectors across 2 cache lines; stride>=8 touches 32.0 sectors
  [PASS] ASP Ch7 Table 7-1: Coalescing raises DRAM throughput 25% -> 90% (3.6x), Load Efficiency 23% -> 99%, and cuts runtime 4.8 -> 1.3 ms (3.7x)
  [PASS] ASP Ch7 p.222 & Table 7-3: float4 (16B/thread, ld.global.v4.f32) moves 512 B/warp = 4 x 128B lines = 16 sectors (4.0 sectors/tx, 4x fewer instructions)
  [PASS] ASP Ch7 pp.223-226: Blackwell CUDA 13+ alignas(32) float8 (32B/thread, ld.global.v8.f32) moves 1,024 B/warp = 8 x 128B lines = 32 sectors
  [PASS] ASP Ch7 p.223: Misaligned element offset (260 % 16 != 0) forfeits vectorized load
  [PASS] ASP Ch7 Table 7-2: Vectorized loads raise Load Efficiency 28% -> 97%, cut sectors/req 31.8 -> 4.0, and cut runtime 4.2 -> 1.2 ms (3.5x)
  [PASS] ASP Ch7 Table 7-4: 32x32 shared-memory tiling cuts global load sectors 9,800 -> 1,200 (~8.17x), lifts occupancy 42% -> 89%, and raises GFLOPS 15 -> 170 (~11.3x)
  [PASS] ASP Ch7 p.231: 64x64 FP32 tile uses 16,384 B (16 KB) per matrix; 12 regs/thread * 1,024 = 12,288 regs/block (5 blocks by regs, capped at 2 blocks = 2,048 threads by SM thread limit)
  [PASS] ASP Ch7 p.232: 22 regs/thread * 1,024 = 22,528 regs/block fits 2 blocks (45,056 <= 65,536 regs) = 2,048 resident threads/SM
  [PASS] ASP Ch7 p.234: Row-major shared access hits 32 distinct banks (1-way, 0 bank conflicts)
  [PASS] ASP Ch7 pp.234-236: Unpadded tile[32][32] column transpose (128B stride) hits bank 0 across all 32 lanes -> 32-way bank conflict
  [PASS] ASP Ch7 pp.235-237: Padded tile[32][33] (+1 float = 3.12% ~ 3% overhead) shifts row modulo across 32 distinct banks -> 0 bank conflicts
  [PASS] ASP Ch7 p.234: All 32 threads reading the exact same shared-memory address triggers hardware broadcast (0 bank conflicts)
  [PASS] ASP Ch7 Table 7-5: Padding tile[32][33] drops bank conflicts 4.8M -> 0, lifts shared util 52% -> 100%, cuts warp stalls 38% -> 0.5%, and cuts runtime 4.0 -> 1.3 ms (~3x)
  [PASS] ASP Ch7 p.239: __shfl_down_sync butterfly reduction sums 32 lanes (1..32 == 528.0) in 5 steps (offsets 16,8,4,2,1) with 0 shared memory and 0 bank conflicts
  [PASS] ASP Ch7 Table 7-6: const __restrict__ raises Load Efficiency 52% -> 97%, L2 read 1,500 -> 1,800 GB/s, cuts DRAM 600 -> 200 GB/s, and cuts runtime 2.5 -> 1.0 ms (2.5x)
  [PASS] ASP Ch7 Table 7-7: TMA double-buffering (cuda::memcpy_async) lifts Load Efficiency 23% -> 99%, cuts sectors/req 6.4 -> 4.0, lifts SM Active 62% -> 100%, and cuts runtime 18 -> 7 ms (~2.6x)
  [PASS] Rejects non-positive stride_elements
  [PASS] Rejects invalid vector_bytes_per_thread (12)
  [PASS] Rejects non-positive tile_cols
  [PASS] Rejects unknown shared-memory access_mode
  [PASS] Rejects regs_per_thread > 255 hardware ceiling
  [PASS] Rejects warp shuffle list with length != 32

Summary: 25 passed, 0 failed (total 25)
```

---

## Exercises

1. A warp reads floats from an aligned address. Use `analyze_warp_global_memory_access()` to count the cache lines and sectors it touches. What load efficiency does it reach?
2. Repeat the count for a read shifted by four bytes. Then repeat it for a stride of two. Then repeat it for a stride of eight.
3. One warp loads with `float4` on Hopper. Another loads with `alignas(32) float8` on Blackwell. How many bytes does each warp move per instruction? How many cache lines and sectors does each warp touch?
4. `cudaMalloc` returned a 256-byte-aligned base pointer, yet casting an interior offset to `float4` fails. Explain why.
5. Chapter 7 of *AI Systems Performance Engineering* reports a 32 by 32 shared-memory tile. What is the drop in global load sectors? What is the change in arithmetic intensity? What is the GFLOPS speedup?
6. For a 64 by 64 tile on a Blackwell SM, what is the shared-memory footprint? How many registers per block does the minimal case need? How many does the double-buffered case need?
7. The row stride of a shared tile is 32 floats. Use modulo arithmetic to show why a column read puts every lane on the first bank. Then show why one padding column spreads the lanes across distinct banks.
8. Trace the five butterfly steps of `__shfl_down_sync` for a warp where each lane starts with its one-based lane number. What is the sum in lane zero? Why can this pattern not reduce across two warps without shared memory or cluster barriers?
9. Compare the Nsight Compute metrics in the read-only cache table and the TMA table of Chapter 7. Then write the four-method `cuda::pipeline` sequence that overlaps TMA prefetch with computation: `producer_acquire`, `producer_commit`, `consumer_wait`, `consumer_release`.

---

## Checkpoint questions (20)

<details>
<summary>**1. How many bytes are in a modern NVIDIA GPU global-memory cache line, how many sectors does it contain, and what is the optimal `Average Sectors per Request` in Nsight Compute for a coalesced scalar warp load?**</summary>

A global-memory cache line is 128 bytes and is divided into four 32-byte sectors. When all threads in a warp read contiguous, aligned 4-byte floats, the entire warp request maps to one cache line and four sectors per request.
</details>

<details>
<summary>**2. What happens to sector and cache-line counts when a warp reads contiguous floats starting at an address that is not aligned to a cache line?**</summary>

The warp span crosses a cache-line boundary and straddles two cache lines. Hardware fetches five sectors totaling 160 bytes instead of four sectors totaling 128 bytes, or up to eight sectors depending on the start offset. This boundary crossing wastes memory bandwidth on unused bytes.
</details>

<details>
<summary>**3. In *AI Systems Performance Engineering* Chapter 7 Table 7-1, how did `uncoalescedCopy` compare to `coalescedCopy` across Nsight Compute metrics?**</summary>

Coalescing reduced Average Sectors per Request from eight to four and raised Global Memory Load Efficiency to nearly one hundred percent. It also increased DRAM throughput from a quarter of peak to ninety percent, lifted SM Active percentage, and cut kernel execution time by nearly fourfold. See Table 7-1 in Section 1.2 for the exact figures.
</details>

<details>
<summary>**4. Why does an Array of Structures cause uncoalesced global memory access on a GPU, and how does a Structure of Arrays fix it?**</summary>

In an Array of Structures, adjacent threads reading the first field access memory addresses separated by the size of the entire structure. That stride pulls unused fields into the cache sectors. In a Structure of Arrays, adjacent threads reading the first coordinate array access contiguous 4-byte addresses with a stride of one, achieving full warp coalescing.
</details>

<details>
<summary>**5. Why does `torch.index_select` with a strided index perform poorly in PyTorch, and what PyTorch operation or compiler mode achieves coalesced and vectorized copies?**</summary>

Calling `torch.index_select` with a strided index launches a gather kernel where threads in a warp load addresses separated by multiple words. That strided pattern touches twice as many sectors per request at stride two. Operating on contiguous tensors via `inp.clone()` or compiling with `torch.compile` in `max-autotune` mode allows TorchInductor to emit coalesced, vectorized memory operations.
</details>

<details>
<summary>**6. Contrast global memory coalescing with vectorized memory access as summarized in *AI Systems Performance Engineering* Chapter 7.**</summary>

Coalescing is an inter-thread property that ensures the threads in a warp access contiguous addresses so hardware merges scalar reads into one cache-line transaction. It does not change the instruction count per thread. Vectorizing is an intra-thread technique that packs four floats (`float4`) or eight floats (`float8`) into a single wide load instruction per thread, cutting load instructions by fourfold or eightfold.
</details>

<details>
<summary>**7. How many bytes per warp, cache lines, and sectors are moved by a single warp-wide `float4` load on Hopper versus a `float8` load on Blackwell, and what PTX instructions does `nvcc` emit?**</summary>

On Hopper, `float4` loads 16 bytes per thread via `ld.global.v4.f32`, moving 512 bytes per warp across four cache lines and 16 sectors. On Blackwell with CUDA 13, `alignas(32) float8` loads 32 bytes per thread via `ld.global.v8.f32`, moving 1,024 bytes per warp across eight cache lines and 32 sectors.
</details>

<details>
<summary>**8. What minimum byte alignment does `cudaMalloc` guarantee on returned device pointers, and how can an element offset break `float4` or `float8` vectorization?**</summary>

The `cudaMalloc` runtime call returns pointers aligned to at least 256 bytes, which satisfies both 16-byte `float4` and 32-byte `float8` alignment at offset zero. Adding an element offset that is not a multiple of four floats for `float4` or eight floats for `float8` breaks natural alignment and forfeits vectorized loads.
</details>

<details>
<summary>**9. In Table 7-2 of *AI Systems Performance Engineering* Chapter 7, how did `copyVector16B` using `float4` improve Nsight Compute metrics compared to `copyScalar`?**</summary>

Vectorized `float4` loads raised Global Memory Load Efficiency from 28 percent to 97 percent and dropped Average Sectors per Request to four. DRAM throughput rose to ninety percent of peak, and kernel runtime fell by three and a half times. See Table 7-2 in Section 2.2 for all numbers.
</details>

<details>
<summary>**10. Why does `tiledMatMul` with a square shared-memory tile require two `__syncthreads()` barriers inside its tile loop?**</summary>

The first `__syncthreads()` barrier after loading the shared tiles ensures all threads in the block have finished writing their element into shared memory before any thread reads the tile. The second `__syncthreads()` barrier after the compute loop ensures all threads have finished reading the current tile before faster threads advance to the next iteration and overwrite the shared arrays.
</details>

<details>
<summary>**11. In Table 7-4 of *AI Systems Performance Engineering* Chapter 7, why did DRAM throughput drop when shared-memory tiling was applied, and why was that drop desirable?**</summary>

In `naiveMatMul`, high DRAM throughput reflected wasteful redundant HBM reads at low arithmetic intensity and low compute throughput. Tiling reused each element 32 times in shared memory, cutting global load sectors by more than eightfold and dropping DRAM saturation while lifting arithmetic intensity, occupancy, and GFLOPS by more than elevenfold.
</details>

<details>
<summary>**12. Walk through the register and shared-memory residency math for a 64 by 64 FP32 GEMM tile computed by a 1,024-thread block on a Blackwell SM when each thread uses 12 registers versus 22 registers.**</summary>

Each 64 by 64 FP32 tile takes 16 KB of shared memory, so both input tiles use 32 KB per block and fit easily inside usable shared memory. In both the 12-register and 22-register cases, per-block register consumption and the SM thread limit allow two resident blocks totaling 2,048 threads per SM. See the residency budget breakdown in Section 3.2 for the exact numbers.
</details>

<details>
<summary>**13. How is on-chip shared memory organized into banks on modern NVIDIA GPUs, and when does a shared-memory bank conflict occur, including the single-address exception?**</summary>

Shared memory has 32 banks that are each four bytes wide, so successive words map to successive banks and wrap every 128 bytes. A bank conflict occurs when two or more threads in the same warp access different addresses in the same bank during the same cycle. Multiple threads reading the exact same address trigger a conflict-free hardware broadcast instead.
</details>

<details>
<summary>**14. Why does reading down a column in `transposeNaive` on `tile[32][32]` cause a 32-way bank conflict, and how does `tile[32][33]` padding or XOR swizzling fix it?**</summary>

In `tile[32][32]`, each row is 32 floats wide, so adjacent lanes reading down a column step by 32 words and all threads hit the exact same bank. Padding the array to `tile[32][33]` changes the row stride to 33 floats so adjacent lanes map to 32 distinct banks with zero conflicts. XOR swizzling achieves the same spread by XOR-transforming the column index.
</details>

<details>
<summary>**15. In Table 7-5 of *AI Systems Performance Engineering* Chapter 7, what was the reported impact of padding `tile[32][32]` to `tile[32][33]` in Nsight Compute?**</summary>

Padding `tile[32][33]` reduced Shared-Memory Load Bank Conflicts from 4.8 million to zero and raised Shared-Memory Utilization to one hundred percent. It also dropped the memory warp stall fraction and cut kernel runtime by roughly threefold. See Table 7-5 in Section 3.3 for the full metric comparison.
</details>

<details>
<summary>**16. How does a warp shuffle reduction (`__shfl_down_sync`) work, why does it avoid bank conflicts completely, and what is its scope limitation?**</summary>

Calling `__shfl_down_sync` with halving offsets lets each lane read the register value of a higher lane directly across the warp register file in five butterfly steps. Because all values stay in registers and never touch shared memory, no bank conflicts or `__syncthreads()` barriers occur. Its scope is strictly limited to the 32 lanes of a single warp.
</details>

<details>
<summary>**17. How does the L1 Read-Only Data Cache (`const __restrict__`) differ from the `__constant__` memory cache, and what speedup did `const __restrict__` achieve in Table 7-6?**</summary>

The 64 KB `__constant__` space has a small per-SM cache optimized for uniform single-address warp broadcasts. The L1 read-only cache serves scattered reads across larger immutable lookup tables when pointers are marked `const __restrict__`. In Table 7-6, adding `const __restrict__` cut off-chip DRAM throughput by threefold, raised L2 read throughput and load efficiency, and cut runtime from 2.5 ms to 1.0 ms.
</details>

<details>
<summary>**18. What is the Tensor Memory Accelerator on Hopper and Blackwell GPUs, and how does `cuda::memcpy_async` with `cuda::pipeline` hide the 800-cycle DRAM latency?**</summary>

The Tensor Memory Accelerator (`cp.async.bulk.*`) is a dedicated hardware DMA unit that copies multi-dimensional tiles between global HBM and shared memory asynchronously without using SM registers. Using a two-stage `cuda::pipeline` with ping-pong shared buffers, the block prefetches the next tile asynchronously while warps compute on the current tile. This overlap hides the 800-cycle DRAM latency behind computation.
</details>

<details>
<summary>**19. In Table 7-7 of *AI Systems Performance Engineering* Chapter 7, how did TMA-accelerated double buffering change Nsight Compute metrics compared to a naive kernel without prefetching?**</summary>

TMA double buffering raised Global Memory Load Efficiency to 99 percent and dropped Average Sectors per Request to four. DRAM throughput rose to ninety percent, SM Active percentage climbed to one hundred percent, and kernel execution time dropped from 18 ms to 7 ms. See Table 7-7 in Section 4.3 for the complete table.
</details>

<details>
<summary>**20. Which Nsight Compute metrics should you inspect first to distinguish uncoalesced global loads, shared-memory bank conflicts, and uncached read-only DRAM thrashing?**</summary>

For uncoalesced global loads, check for low Global Memory Load Efficiency paired with Average Sectors per Request above four. For shared-memory bank conflicts, check `l1tex__data_bank_conflicts_pipe_lsu_mem_shared_op_ld.sum`, low shared-memory utilization, and high memory stall fractions. For uncached read-only DRAM thrashing, look for high off-chip DRAM read bandwidth paired with low L2 and read-only hit rates on immutable buffers lacking `const __restrict__`.
</details>

---

## Sources and review notes

### Primary sources read in full for this chapter

The primary textbook source for this chapter is *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chris Fregly), Chapter 7.

```text
Source Breakdown — AI Systems Performance Engineering Ch 7 (pp. 215-252):
  - Coalesced vs Uncoalesced Global Memory Access (pp. 216-221):
    128-byte cache lines (4 x 32-byte sectors), aligned 4.0 sectors/req vs misaligned 5 or 8 sectors vs scattered 32 sectors,
    AoS vs SoA (Figure 7-2), uncoalescedCopy (stride = 2, N = 1 << 20) and PyTorch torch.index_select vs coalescedCopy
    and inp.clone() / torch.compile(mode="max-autotune"), and Table 7-1 (DRAM throughput 25% -> 90%, Load Efficiency 23% -> 99%,
    Sectors/req 8.0 -> 4.0, SM Active 62% -> 99%, Runtime 4.8 ms -> 1.3 ms).
  - Vectorized Memory Access (pp. 221-226):
    float4 (16 B/thread, 512 B/warp = 4 x 128 B lines = 16 sectors, ld.global.v4.f32) on Hopper vs struct alignas(32) float8
    (32 B/thread, 1,024 B/warp = 8 x 128 B lines = 32 sectors, ld.global.v8.f32) on Blackwell (sm_100, CUDA 13+),
    cudaMalloc >= 256-byte alignment, Table 7-2 (Load Efficiency 28% -> 97%, Sectors/req 31.8 -> 4.0, DRAM 25% -> 90%,
    Runtime 4.2 ms -> 1.2 ms), and Table 7-3 (coalescing vs vectorizing).
  - Tiling and Data Reuse Using Shared Memory (pp. 226-233):
    naiveMatMul vs tiledMatMul (32 x 32 tile on N = 1,024), Table 7-4 (DRAM 90% -> 25%, Occupancy 42% -> 89%,
    GFLOPS 15 -> 170, Global load sectors 9,800 -> 1,200, Shared memory throughput 52% -> 99%, 1.5 FLOPs/B @ 10 GB/s ->
    8.0 FLOPs/B @ 21 GB/s), 64 x 64 tile register/SMEM math (16 KB/tile, 12 regs/thread = 12,288 regs/block vs 22 regs/thread =
    22,528 regs/block against 65,536 regs/SM and 2,048 threads/SM = 2 blocks/SM), CUTLASS, cuTile, and TileIR.
  - Avoid Shared-Memory Bank Conflicts (pp. 233-238):
    32 banks x 4 B width (128 B wrap), arr[threadIdx.x * 32] 32-way conflict, single-address broadcast exception,
    transposeNaive (tile[32][32]) vs transposePadded (tile[32][33], +1 column = ~3% / 1 KB overhead) and XOR swizzling,
    and Table 7-5 (Bank conflicts 4.8M -> 0, Shared util 52% -> 100%, Warp stall 38% -> 0.5%, Runtime 4.0 ms -> 1.3 ms).
  - Warp Shuffle Intrinsics (pp. 238-240):
    __shfl_sync, __shfl_down_sync 5-step butterfly reduction (offset = 16, 8, 4, 2, 1, __activemask()),
    Cooperative Groups thread_group.shuffle(), and __reduce_sync().
  - Read-Only Data Caches (pp. 240-244):
    const __restrict__ and __ldg() vs 64 KB __constant__ cache, T = 1,024 lookup table (N = 1 << 20),
    Table 7-6 (Load Efficiency 52% -> 97%, DRAM 600 -> 200 GB/s, L2 read 1,500 -> 1,800 GB/s, SM Active 45% -> 93%,
    Runtime 2.5 ms -> 1.0 ms), and cudaTextureObject_t (tex1Dfetch, tex2D).
  - Asynchronous Memory Prefetching and Tensor Memory Accelerator (pp. 244-251):
    TMA (cp.async.bulk.*), cuda::memcpy_async + cuda::pipeline_shared_state<cuda::thread_scope_block, 2>
    (producer_acquire, producer_commit, consumer_wait, consumer_release) hiding 800-cycle DRAM latency, and
    Table 7-7 (Load Efficiency 23% -> 99%, Sectors/req 6.4 -> 4.0, DRAM 25% -> 90%, SM Active 62% -> 100%, Runtime 18 ms -> 7 ms).
```

### Related source files mapped in `MIGRATION_MAP.md`
- None mapped because all `nvidia-devops` memory-coalescing notes were already migrated into earlier Part 10 chapters.

### Run here
- `code/part10/memory_access_patterns_lab.py` passes all 25 verification checks with zero failures.

### The handbook's own synthesis
- The warp sector simulator `analyze_warp_global_memory_access()`, the vectorized load validator `calc_vectorized_warp_load()`, the bank-conflict analyzer `analyze_shared_memory_bank_conflicts()`, and the residency calculator `calc_tile_residency_and_register_budget()` in `code/part10/memory_access_patterns.py` are this handbook's own code. They encode the hardware formulas and benchmark tables of *AI Systems Performance Engineering* Chapter 7.

### Not verified on live hardware
- No physical Blackwell or Hopper GPU was available for this chapter, so `nvcc` and `ncu` commands in Section 5 (`64K` constant memory, `tile0` and `tile1` ping-pong staging, `30` / `217` cycle latencies, Volume `02` notes, cross-referenced with Chapters `10.2`, `10.5`, `10.11`, `10.12`, and `10.16` in `2026`) are marked `(untested here)`.

### Not in the corpus
- Low-level CUTLASS CuTe layout swizzling algebra beyond the conceptual XOR swizzling overview in *AI Systems Performance Engineering* Chapter 7.

### Corrections to the author's notes
- Validation pass confirmed the vectorization and tiling tables directly against the book text, while the remaining tables are encoded in the chapter lab from the same source. The chapter explicitly notes that these are the author's illustrative results, that the DRAM throughput figures repeat across three tables, and that the vectorization baseline sector count is inconsistent with a contiguous scalar load.
- The register breakdown in Section 3.2 is an illustration added by this handbook rather than a figure from the book, and is labelled accordingly in the text block.
