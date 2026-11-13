---
id: "c10-03"
title: "10.3 The GPU memory hierarchy"
sidebar_label: "10.3 The GPU memory hierarchy"
sidebar_position: 3
description: "How data moves through Registers, Shared Memory/L1, Blackwell Tensor Memory (TMEM), Constant Cache, L2 Cache, Local Memory, and HBM3/HBM3e, and how coalescing, 32-bank conflict padding, warp shuffles, TMA async prefetching, ReBAR, and memory pools eliminate memory bottlenecks, verified by a 25-check Python lab."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Nebius GPU"
---

# 10.3 The GPU memory hierarchy

| | |
|---|---|
| **Status** | Drafted (`gpu_memory_hierarchy_lab.py`: 25 checks pass; `ncu`/`nvidia-smi` commands **untested** on live Nebius GPU VM) |
| **Level** | Intermediate |
| **Priority tier** | 2 |
| **Lab venue** | Nebius GPU + self-checking Python model (`code/part10/gpu_memory_hierarchy_lab.py`) |
| **Part** | Part 10: The GPU and CUDA |
| **Sources used** | *AI Systems Performance Engineering* Ch. 6 & Ch. 7; `nvidia-devops` V2 (Ch. 5, 7, 8, 9; Lab 3); `nvidia-devops` VL4 (Ch. 1 §3 & App. B) |

## Why this matters for AI infrastructure

A GPU can have over a thousand TeraFLOPS of arithmetic horsepower and still crawl at a tiny fraction of its capability. Execution pipelines frequently spend 80% of their cycles waiting for bytes to arrive from memory. Picture a fleet of expensive accelerators that all look busy on the dashboard, while the math units sit idle for most of each step. The fix is rarely a faster chip. It is usually a better trip for the bytes.

No single storage technology can be simultaneously tiny, fast, and huge. A register file is fast but holds very little, while a pool of DRAM holds a great deal but answers slowly. Every modern GPU solves this physical trade-off with a seven-tier memory hierarchy, stretching from single-cycle per-thread registers out to off-chip HBM3e and host CPU RAM.

As an AI infrastructure or platform engineer, you will diagnose memory-hierarchy bottlenecks constantly. The four cases below are the kind of problem that shows up in a ticket.
- Why does a model that fits easily still feel slow? A thirteen-billion-parameter FP16 model fits effortlessly inside an 80 GB H100 with plenty of room to spare. Yet it hits a hard latency floor during unbatched LLM decode.
- Why did an optimization make a kernel slower? A compiler optimization that unrolls a loop and reduces instruction count can make a kernel slower. It does this by spilling just two float variables per thread into local memory.
- Why does a shared-memory kernel stall? A naive matrix transpose in fast on-chip shared memory stalls heavily on bank conflicts. Adding a single unused padding column makes that kernel three times faster.
- Why is the CPU-to-GPU path so narrow? A misconfigured server BIOS that leaves Resizable BAR disabled caps the host aperture at a tiny window. That setting cripples CPU-to-GPU transfers on an 80 GB GPU.

This chapter maps every tier of the GPU memory hierarchy, including Blackwell Tensor Memory and the Tensor Memory Accelerator. It derives the exact arithmetic for cache-line coalescing, shared-memory bank conflicts, and register spilling. Finally, it connects kernel-level access patterns to host-level Resizable BAR, pinned memory, stream-ordered memory pools, and Unified Memory, so you can see how a setting on the server affects a kernel on the GPU.

```text
Key memory hierarchy diagnostic benchmarks:
- 13B FP16 weights (26 GB on 80 GB H100, 54 GB spare): ~7.8 ms/token unbatched decode floor.
- Spilling 2 floats (8 bytes) per thread across 65,536 threads: 1.05 MB extra HBM traffic per launch.
- Naive shared-memory transpose: 38% warp stalls on 4.8 million bank conflicts; [32][33] padding is 3x faster.
- Disabled Resizable BAR (ReBAR / Large BAR): BAR1 Total stuck at 256 MiB instead of 81,920 MiB.
```

## Prerequisites and outcomes

**Prerequisites:**
- CPU versus GPU throughput design and peak HBM and PCIe bandwidth formulas from the first chapter of this part.
- The execution hierarchy from thread to warp, block, cluster, and grid, along with sub-partitions and occupancy rules from the second chapter of this part.

The chapter starts with the seven memory tiers and the Points of Coherency, which say where one thread's write becomes visible to another. It then moves on-chip, covering registers and their spills to local memory, shared-memory tiling, bank conflicts with `[32][33]` padding or XOR swizzling, and warp shuffles (`__shfl_down_sync`) that skip shared memory altogether. Next comes global memory, where coalescing, Array of Structures against Structure of Arrays, vectorized loads, the read-only data cache, and the Tensor Memory Accelerator (TMA) with `cuda::memcpy_async` double-buffering decide how fast bytes arrive. The last part separates VRAM capacity from effective HBM bandwidth, shows how to check Resizable BAR in `nvidia-smi -q -d MEMORY`, and tunes stream-ordered memory pools and Unified Memory.

---

## 1. The seven-tier GPU memory hierarchy and Points of Coherency

Picture a workload that runs at a fraction of the GPU's rated speed. The team has three guesses. Maybe the batch is too small, maybe a kernel needs a rewrite, or maybe the hardware is simply too slow. Each guess sends the team down an expensive path. Without a clear map of where bytes sit and how many cycles each hop costs, you cannot tell whether the threads are starving on off-chip DRAM or fighting over the small on-chip scratchpad. The map answers that question before anyone spends a week on the wrong fix.

The rule behind the map is simple. Every step further away from the SM's arithmetic units gives you roughly an order of magnitude more storage capacity, and it costs you higher latency and lower per-SM bandwidth. A register is the closest storage and the smallest. HBM is the farthest on the device and the largest. Keep that trade-off in mind, because each tier in the rest of this chapter is one point on that line.

### 1.1 Architectural map from Registers and TMEM to L2, HBM3e, and Host RAM

The hardware organizes storage into fast on-chip tiers inside each SM, a shared GPU-wide L2 cache, off-chip HBM stacks, and the external host interconnect. On-chip levels respond in a few cycles, and they move terabytes to tens of terabytes per second per SM. Off-chip HBM needs hundreds of cycles for each round trip. The diagram shows which threads can reach which tier, and the dotted line marks the path that register spills take to slow memory.

```mermaid
flowchart TD
  Th["CUDA thread"] --> Reg["1. Registers"]
  Th --> Const["4. Constant cache"]
  CTA["Thread block<br/>or cluster (DSMEM)"] --> SMEM["2. Shared memory + L1"]
  TC["Tensor Cores<br/>(Blackwell)"] <--> TMEM["3. Tensor Memory (TMEM)"]
  SMEM <--> TMEM
  Th -.->|"spill, dynamic arrays<br/>(6. local memory)"| L2
  SMEM <-->|"TMA bulk copy<br/>or LD/ST units"| L2["5. L2 cache"]
  L2 <-->|"memory controllers"| HBM["7. HBM global memory"]
  HBM <-->|"PCIe Gen5 or NVLink-C2C"| Host["Host RAM and NVMe"]
```

Read the diagram from the thread outward. A thread touches its registers directly, and it reaches the constant cache for read-only values. A thread block shares the on-SM shared memory, and it can reach its neighbors through the cluster's distributed shared memory. Tensor Cores on Blackwell have their own tier, TMEM. Everything that does not fit on the SM goes through the L2 cache, and only then to HBM, and from HBM to the host.

The table below lists each level with its size, its latency, and a short note. Read the size column for capacity, and read the latency column for the cost of a miss.

| Level | Size | Latency | Notes |
|---|---|---|---|
| 1. Register file | 64K x 32-bit registers per SM (256 KB), max 255 per thread | about 1 cycle | On-chip, per SM |
| 2. Unified shared memory and L1 | 256 KB SRAM per SM (up to 228 KB shared: 227 KB dynamic per block plus 1 KB reserved) | about 20 to 30 cycles | Shared by the thread block, or the cluster through DSMEM |
| 3. Tensor Memory (TMEM) | 256 KB dedicated SRAM per SM on Blackwell | about 10 cycles | Managed through TMA and descriptors; used by 5th-gen Tensor Cores (`tcgen05` / UMMA) |
| 4. Constant cache | about 8 KB per SM in front of 64 KB of `__constant__` | about 1 cycle on a warp-uniform broadcast | Per SM read-only broadcast cache |
| 5. L2 cache | 50 MB (H100) / 126 MB (B200), GPU-wide | about 200 cycles | Fed by TMA bulk async DMA or 16x LD/ST units |
| 6. Local memory | Logical, per thread | Goes through L1, L2 and HBM | Register spills and dynamic arrays |
| 7. HBM global memory | 80 to 141 GB (H100/H200), 180 to 288 GB (B200/B300) | about 800 cycles typical round trip | 3.35 TB/s (H100) / 8.0 TB/s (B200) through the memory controllers |
| Host link | Host CPU RAM (DDR5 / LPDDR5X) and NVMe (GPUDirect Storage) | n/a | PCIe Gen5 (63 GB/s, BAR1/ReBAR) or NVLink-C2C (900 GB/s coherent) |

The latency column tells the story of a single load. A value in a register is ready almost at once. A value in shared memory takes a few dozen cycles, and a value in L2 takes about two hundred. A value that has to come all the way from HBM can take about eight hundred cycles, and the warp that asked for it simply waits. The GPU hides that wait by running other warps, which is the trick from the execution model in the previous chapter.

The following table compares the full Blackwell memory hierarchy, as described in *AI Systems Performance Engineering* Chapter 6, with Hopper H100. It adds the visibility scope and the rules for each tier, so you can see who controls each level.

| Memory tier | Visibility scope | Capacity (Blackwell B200 / Hopper H100) | Typical latency | Approx. bandwidth | Who manages it & key rules |
|---|---|---|---|---|---|
| **1. Registers** | **Per thread** (private) | **64K 32-bit registers (256 KB) per SM**; max **255 registers/thread** | **~1 cycle** | Tens of TB/s per SM | Compiler (`nvcc -Xptxas=-v`). Fastest storage; excess demand spills to Local Memory. |
| **2. Shared Memory & L1 Data Cache** | **Per Thread Block (CTA)** (or **Cluster** via DSMEM) | **256 KB combined SRAM per SM**; up to **228 KB shared/SM** (**227 KB** max dynamic/block + **1 KB** CUDA reserved), rest is L1 | **~20–30 cycles** | TB/s per SM (when bank-conflict-free) | Programmer (`__shared__`, `cudaFuncAttributePreferredSharedMemoryCarveout`) for SMEM; hardware for L1. |
| **3. Tensor Memory (TMEM, Blackwell)** | **Per SM (Tensor Cores)** | **256 KB dedicated SRAM per SM** (Blackwell B200/B300) | **~10 cycles** | Tens of TB/s to Tensor Cores | **Not pointer-addressable in C++**; holds Tensor Core accumulators/operands, fed via **TMA** and `tcgen05.mma` / UMMA descriptors. |
| **4. Constant Memory Cache** | **Per SM (Read-only)** | **~8 KB cache per SM** fronting **64 KB** device-wide `__constant__` space | **~1 cycle** (on warp broadcast) | TB/s-scale broadcast | Programmer (`__constant__`). Broadcasts in 1 cycle when all 32 warp lanes read the **exact same address** (RoPE tables, ALiBi slopes, LayerNorm gamma/beta, quant scales). |
| **5. L2 Cache** | **GPU-wide** (all SMs, NVLink, PCIe) | **126 MB on Blackwell B200** (50 MB on Hopper H100) | **~200 cycles** | Multi-TB/s aggregate | Hardware. Central coherence hub across all SMs, HBM partitions, NVLink, and PCIe DMA. |
| **6. Local Memory (Spill Space)** | **Per thread** (logical scope, **physically off-chip.**) | Backed by Global HBM DRAM | **100s → 1,000+ cycles** (on L1/L2 miss) | Up to HBM BW (~8 TB/s B200) | Compiler automatic fallback when registers spill (>255 or launch-bounds cap) or for per-thread arrays indexed dynamically. |
| **7. Global Memory (HBM3 / HBM3e)** | **Device-wide / System** | **80 GB H100**, **141 GB H200**, **180–192 GB B200**, **~288 GB B300** | **100s → 1,000+ cycles** (~800 cycles typical) | **3.35 TB/s H100**, **4.8 TB/s H200**, **~8.0 TB/s B200** (16 TB/s per 2-GPU GB200/GB300) | Application (`cudaMalloc`, `cudaMallocAsync`). On B200, 8 HBM3e stacks (4 per reticle die across the 10 TB/s chip-to-chip link) appear as one uniform address space. |

Two rows deserve a second look. Local memory is listed as a per-thread tier, but it lives in the same off-chip HBM as the global memory. The name describes who can see the data, not where it is stored. The constant cache is fast only when every lane of a warp reads the same address, because the hardware then sends one broadcast to all of them.

### 1.2 Points of Coherency and tracing a memory request

When threads exchange data, a race condition can occur if the reader looks at a cache level that has not yet received the writer's update. Imagine two people sharing a whiteboard, where one writes a number and the other reads it from a photo taken earlier. The Point of Coherency is the specific hardware level where one thread's write becomes visible to another. That level depends directly on how far apart the two threads sit in the execution hierarchy.

1. Thread level: the register file is private to a single thread, so no other thread can see the write.
2. Thread block level: the L1 and shared memory SRAM on a single SM serve one thread block, and they are synchronized with `__syncthreads()`.
3. Thread block cluster level: the multi-SM distributed shared memory within a Graphics Processing Cluster serves a cluster, and it is synchronized with `cluster.sync()`.
4. Device level: the unified L2 cache and global HBM serve all SMs on one GPU.
5. System level: coherent memory spans multiple GPUs and the host CPU over NVLink, NVSwitch, NVLink-C2C, or PCIe.

The levels run from narrow to wide. The closer two threads are in the hierarchy, the cheaper it is to share data between them. When you design a kernel, ask which level your threads actually need, and keep the sharing at the lowest level that works.

You can tell in five seconds whether a slow workload is bottlenecked on the memory hierarchy rather than on compute or kernel launches. Run `nvidia-smi dmon -s ucm -c 3` to sample SM and memory interface activity. The output below shows what three samples look like, with one row per sample.

```text
$ nvidia-smi dmon -s ucm -c 3
# gpu   sm   mem
# Idx     %     %
    0    18    89
    0    17    91
    0    19    88
```

When SM utilization sits around 18 percent while memory utilization sits around 90 percent, the SMs are starving while the memory interface is saturated. That pattern points at the memory hierarchy. Next, run one Nsight Compute pass on the L1 and L2 sector hit rates, using `l1tex__t_sector_hit_rate.pct` and `lts__t_sector_hit_rate.pct`. The two rates separate two distinct failure modes, and each one has a different fix.

| Cache hit pattern in `ncu` | Typical metrics | Root cause | Fix |
|---|---|---|---|
| **Low L1 and low L2 hit rates + high HBM traffic** | L1 `12.4%`, L2 `18.9%` | Streaming or uncoalesced access pattern bypasses both caches and slams HBM on almost every load | Fix data layout (SoA), coalescing, or shared-memory tiling |
| **High L2 hit rate + high HBM traffic** | Working set slightly exceeds L2 (50 MB H100 / 126 MB B200) | Cache thrashing as tiles are evicted right before reuse | Reduce precision (FP8/FP4), fuse kernels, or adjust tile/batch size |

The first row is a layout problem. Data is read in a pattern the caches cannot reuse, so almost every load goes to HBM. The second row is a capacity problem. The working set is just a little bigger than L2, so tiles get evicted right before the kernel needs them again.

:::info In one minute: Section 1 takeaways
- Which tiers matter most? The seven device memory tiers trade capacity for speed, moving from registers and Blackwell TMEM out to shared memory, constant cache, L2 cache, and global HBM.
- What is new on Blackwell? TMEM provides 256 KB per SM for fifth-generation Tensor Core accumulators and operands. It is managed via TMA and `tcgen05` descriptors rather than C++ pointers.
- How do you find the leaking tier? Pair `nvidia-smi dmon -s ucm` with the `ncu` L1 and L2 sector hit rates (`l1tex__t_sector_hit_rate.pct` and `lts__t_sector_hit_rate.pct`) to pinpoint which tier is leaking performance.
:::

---
## 2. On-chip storage: Registers, Local Memory spills, Shared Memory tiling, Bank Conflicts, and Warp Shuffles

Picture a kernel review. A developer unrolls a loop to cut the instruction count, expecting a faster kernel. The benchmark comes back at half the old throughput. Nothing in the source code looks wrong, and the arithmetic has not changed. The cause sits one level down, in the registers. Even when data fits on chip, a single compiler decision or indexing stride can quietly route on-chip accesses into off-chip DRAM, or serialize a 32-thread warp into 32 sequential steps. Kernel authors and performance engineers feel this most when an apparent optimization, such as unrolling a loop or staging a matrix tile in shared memory, cuts throughput in half instead of raising it.

This section takes the on-chip tiers one at a time. It starts with registers and the local memory that they spill into. Then it covers shared memory as a tile you control, the bank conflicts that can slow it down, and the warp shuffles that let threads trade values without using shared memory at all.

### 2.1 Registers versus Local Memory: why "Local" memory is physically off-chip

One of the most dangerous misnomers in CUDA is local memory. The word "local" describes the logical visibility scope. The variable is private to a single thread, the same way a local variable in C is private to its function. It does not describe where the bytes physically live. Physically, local memory is allocated in off-chip global HBM DRAM and routed through the L1 and L2 caches. A developer who assumes "local" means "fast" will be surprised by the profile.

The `nvcc` compiler places a thread's variables into slow local memory in two situations.
- Register spilling: the kernel needs more live variables than fit in the per-thread register allocation. This happens when demand exceeds the hardware ceiling, or when it exceeds the register cap forced by `__launch_bounds__`.
- Dynamic array indexing: a thread declares a local array, such as `float buf[32]`, and indexes it with a runtime variable, `buf[i]`. The compiler cannot map a runtime index to a fixed register number at compile time, so the array goes to memory.

You can catch register spilling at compile time, before ever running on a GPU, by passing `nvcc -O3 -Xptxas=-v`. The compiler prints the register count and the spill bytes, and those two numbers tell you most of what you need to know. The first block below is a healthy kernel. The second block is the same kernel after aggressive unrolling.

```text
# Healthy kernel: zero spills
ptxas info : Used 44 registers, 0 bytes spill stores, 0 bytes spill loads

# Regressed kernel after aggressive loop unrolling: 88 registers + spills!
ptxas info : Function properties for _Z6kernelPKfPfm
    64 bytes stack frame, 96 bytes spill stores, 128 bytes spill loads
ptxas info : Used 96 registers, 0 bytes cmem[0]
```

The regressed build reports spill stores and spill loads, which means some values no longer fit in registers. Each of those values now travels to HBM and back. The register count also rose, which is the first sign that the unrolled code is asking for more on-chip state than the SM can hold.

To see why even a tiny spill hurts bandwidth-bound workloads, work through the calculation from the source notes. Suppose a kernel spills just two float values per thread, and it launches a modest grid of thread blocks. Every spilled variable is written out as a spill store and read back as a spill load, so each spilled value costs two trips.

```text
Worked register spill traffic calculation:
- Spilled per thread: 2 floats = 8 bytes
- Grid launch size: 256 blocks x 256 threads/block = 65,536 threads total
- Extra Spill Traffic = 65,536 threads x 8 bytes x 2 (store + load) = 1,048,576 bytes (1.0 MiB ≈ 1.05 MB)
```

Read the calculation one factor at a time. The per-thread cost is 8 bytes for the spill and 8 more for the reload. Multiply that by the number of threads, and the total comes out to about one megabyte per launch. That single kernel launch silently injects over a megabyte of extra cache and HBM traffic that does not appear anywhere in your C++ or PyTorch source code. A kernel that runs thousands of times per step pays that cost thousands of times.

### 2.2 Shared Memory tiling and data reuse

Unlike hardware-managed L1 and L2 caches, where hardware heuristics decide what to evict, shared memory is an explicit scratchpad that you manage. Memory declared with `__shared__` lives in on-SM SRAM, and you decide what goes in it and when it is reused. On Hopper and Blackwell, the SM provides combined L1 and shared SRAM, so the split between them is a setting. The dynamic shared memory carveout per block is configured via `cudaFuncAttributePreferredSharedMemoryCarveout`.

Consider the naive matrix multiplication $C = A \times B$ of size $N \times N$. Each thread computing one output element reads an entire row of $A$ and a column of $B$ directly from global HBM. That pattern fetches the same input element again and again, once for every thread that needs it. Shared-memory tiling fixes this redundant traffic in four cooperative steps.

- First, the threads in a square thread block load one tile of $A$ into `__shared__ float sA[32][32]` and one tile of $B$ into `sB[32][32]`, working together so each element is fetched once.
- Second, the block calls `__syncthreads()`, so every load finishes before any thread reads the staged tile.
- Third, each thread runs its multiply-accumulates straight from fast shared memory, reusing each HBM value across the whole width of the tile.
- Fourth, the block calls `__syncthreads()` again before it loads the next tile along the reduction dimension.

The four steps are a rhythm of load, wait, compute, and wait again. The barriers are what keep the rhythm honest. Without them, a thread could read a tile that a neighbor has not finished writing yet.

The table below shows the measured impact of shared-memory tiling from *AI Systems Performance Engineering* Chapter 7. Each row compares the naive kernel with the tiled one on the same matrix size, and the last column explains the change.

| Metric (`N = 1,024` FP32 matrix multiply, *AI Systems Performance Engineering* Ch. 7 Table 7-4) | Before (`naiveMatMul` from HBM) | After (`tiledMatMul` in Shared Memory) | Why it changed |
|---|---|---|---|
| **Global memory load sectors (32 B each)** | 9,800 sectors | **1,200 sectors** | **8.2x fewer DRAM reads** (each tile element fetched once per block instead of 32x). |
| **DRAM throughput (% of peak)** | 90% (wasteful redundant traffic) | **25%** (3.6x lower pressure) | Redundant off-chip HBM fetches eliminated. |
| **Shared-memory throughput (% of peak)** | 52% | **99%** | On-chip SRAM services the inner loop at ~100% efficiency. |
| **Achieved SM occupancy (%)** | 42% | **89%** | Fewer HBM stalls allow resident warps to make continuous progress. |
| **Arithmetic intensity (FLOPs / byte)** | 1.5 FLOPs/byte (15 GFLOPS @ 10 GB/s) | **8.0 FLOPs/byte** (170 GFLOPS @ 21 GB/s) | **5.3x higher arithmetic intensity**, shifting the kernel toward compute-bound. |
| **Sustained FP32 throughput** | 15 GFLOPS | **170 GFLOPS** | **11.3x speedup** from shared-memory reuse alone. |

The table tells one story from several angles. The tiled kernel fetches far fewer sectors from DRAM, so the DRAM channel is less busy. The arithmetic intensity, which is operations per byte moved, rises, and that moves the kernel from waiting on memory toward doing math. The final row is the result that matters to the business, because it is the throughput the user sees.

Why not keep doubling the tile size forever? Doubling a 2D tile's width and height doubles the reuse factor, but it quadruples the shared memory the tile needs and adds per-thread register pressure. At some point the bigger tile costs more occupancy than it saves in traffic. Libraries such as NVIDIA CUTLASS, `cuBLAS`, `cuDNN`, OpenAI Triton, and NVIDIA Python `cuTile` with `TileIR` tune these hierarchical thread, warp, and block tile dimensions automatically, so most teams never pick a tile size by hand.

The next block works through the resource budget for one tile size, so you can see the limits add up.

```text
64 x 64 tile resource budget (ASP Ch. 7 pp. 233-234):
- Shared memory per block: 16 KB for sA + 16 KB for sB = 32 KB
- Block size: 32 x 32 = 1,024 threads (each thread computes a 2 x 2 subtile)
- Register demand: ~12 to 22 registers/thread -> 22 x 1,024 = 22,528 registers/block
- SM residency limit: 2 blocks use 45,056 registers (fits in 65,536), but 2 x 1,024 = 2,048 threads hits the hard 2,048-thread SM ceiling (max 2 blocks/SM).
```

Work through the block limits in order. The shared memory fits, and the registers fit, so the question is the thread ceiling. Two blocks of 1,024 threads reach the 2,048-thread limit exactly, which means the SM can hold no more than two of these blocks. That is the same admission arithmetic from the execution model chapter, now applied to a tiled kernel.

### 2.3 Shared-Memory 32-Bank Conflicts, `[32][33]` Padding, Swizzling, and Warp Shuffles

Shared memory is fast only when the threads in a warp access different hardware banks in parallel. Think of shared memory as 32 parallel drawers, each one word wide. When all 32 threads reach into different drawers at once, every drawer is used in one trip. When several threads reach into the same drawer, they have to take turns. On Hopper, Blackwell, and Ampere, shared memory is divided into hardware banks that are one float wide. Successive words map to successive banks according to `bank = (byte_addr // 4) % 32`.

The rule has three cases, and the first two are good news. Conflict-free stride-1 access happens when all threads in a warp read row-major elements such as `tile[threadIdx.y][threadIdx.x]`. Adjacent threads step by one word, so they hit distinct banks in a single transaction. The broadcast exception happens when all threads in a warp read the exact same address, such as `tile[0][0]`. The hardware sends that one word to every lane in one cycle, with no conflict at all.

The third case is the trap. During a naive matrix transpose, the kernel `transposeNaive` has threads in a warp read down a column of `__shared__ float tile[32][32]`, using `tile[threadIdx.x][threadIdx.y]` or `arr[threadIdx.x * 32]`. Every thread lands on the same bank at different addresses. The hardware cannot serve them in one go, so it serializes the instruction into a series of replays.

```mermaid
flowchart LR
    subgraph Unpadded["Unpadded: __shared__ float tile[32][32] (Row Stride = 32 floats = 128 B)"]
        U0["Thread 0: tile[0][0] -> Word 0 -> Bank 0"]
        U1["Thread 1: tile[1][0] -> Word 32 -> Bank 0"]
        U31["Thread 31: tile[31][0] -> Word 992 -> Bank 0"]
        U0 & U1 & U31 ==>|"ALL 32 threads hit Bank 0!"| Bad["32-Way Bank Conflict<br/>(32 Serialized Replays, 4.0 ms)"]
    end

    subgraph Padded["Padded (+1 col): __shared__ float tile[32][33] (Row Stride = 33 floats = 132 B)"]
        P0["Thread 0: tile[0][0] -> Word 0 -> Bank 0"]
        P1["Thread 1: tile[1][0] -> Word 33 -> Bank 1"]
        P31["Thread 31: tile[31][0] -> Word 1023 -> Bank 31"]
        P0 & P1 & P31 ==>|"Each thread hits a unique Bank 0..31!"| Good["Zero Bank Conflicts<br/>(1 Parallel Access, 1.3 ms = 3.1x faster)"]
    end
```

The two panels show the same access with one change. In the unpadded tile, the row stride is 32 words, so every row starts on Bank 0 and the whole column collides. In the padded tile, the row stride is 33 words, so each row starts one bank further along. The same column read now touches all 32 banks once each.

Three practical techniques remove shared-memory bank conflicts. Each one changes the address math, so the data stays the same.
- Array padding with `__shared__ float tile[32][33]` adds one unused padding column. That changes the row stride so that the column width and the bank count are coprime, which means they share no common factor. Column reads then map each thread in the warp to a unique bank, and all conflicts disappear.
- XOR index swizzling is the second technique. Libraries such as CUTLASS transform the column index with a bitwise XOR, `col_swizzled = col ^ row`. That permutes which bank each row lands on, with zero extra memory.
- Warp shuffle intrinsics (`__shfl_sync` and `__shfl_down_sync`) are the third. When threads only need to exchange or reduce data inside one warp, they do not need shared memory at all. A shuffle reads another lane's register directly, in logarithmic butterfly steps, so the cost is a handful of steps and no barriers. This matches the speed of Cooperative Groups `__reduce_sync` for the same job, with zero shared memory and zero barriers.

The arithmetic for the padded tile is short enough to check by hand. With 33 floats per row, thread `t` reads word `t * 33 + col`, and that lands in bank `(t + col) % 32`. Because 33 and 32 share no common factor, the 32 threads cover all 32 banks. The padding costs one float per row, which is about 3.1 percent of the tile.

```text
Bank conflict math & ASP Ch. 7 Table 7-5 transpose results:
- Shared memory layout: 32 banks x 4 bytes wide (bank assignment repeats every 32 floats = 128 bytes)
- Unpadded tile[32][32] column read: word = t * 32 + col -> bank = (t * 32 + col) % 32 == col (32-way conflict)
- Padded tile[32][33] column read: word = t * 33 + col -> bank = (t * 33 + col) % 32 == (t + col) % 32 (32 unique banks, since 33 and 32 are coprime)
- Padding overhead: +1 float/row = ~3.1% (~3.125%, 1 KB on a 32 x 32 tile)
- Nsight Compute (l1tex__data_bank_conflicts_pipe_lsu.sum): 4.8 million conflicts -> 0 conflicts
- Shared-memory utilization: 52% -> 100%; memory warp stalls: 38% -> 0.5%; kernel latency: 4.0 ms -> 1.3 ms (3.1x speedup)
- Warp shuffle reduction: 5 butterfly steps (offset = 16, 8, 4, 2, 1) across 32 threads
```

The padded result matches the diagram. Zero conflicts, a shared-memory utilization of 100 percent, and a kernel that drops from 4.0 ms to 1.3 ms. The warp shuffle line at the bottom explains the five steps that the next code block uses.

```cpp
unsigned mask = __activemask();
for (int offset = 16; offset > 0; offset >>= 1) {
    val += __shfl_down_sync(mask, val, offset);
}
// Lane 0 now holds the sum of all 32 threads: 0 shared memory bytes, 0 barriers, 0 bank conflicts!
```

The loop runs five times, halving the offset each time, so the values add up in a tree across the 32 lanes. Only lane 0 ends with the full sum. Nothing is written to shared memory, and no barrier is needed, because every step happens inside one warp.

:::info In one minute: Section 2 takeaways
- What is local memory? It is a thread-scoped spill space backed by off-chip HBM DRAM. Always check `nvcc -O3 -Xptxas=-v` to confirm zero spill stores and loads.
- What makes a bank conflict? Shared memory has 32 banks of 4 bytes each, so striding by 32 floats causes a 32-way bank conflict. Padding to `tile[32][33]` or XOR swizzling removes the conflict.
- What should reduce within a warp? Use `__shfl_down_sync` for intra-warp reductions directly in registers, without touching shared memory.
:::

---

## 3. Global memory access: Coalescing, Vectorization, Read-Only Cache, and TMA Async Prefetch

A kernel can have plenty of HBM bandwidth on paper and still stall constantly, if its threads request scattered addresses or wait idle while data travels across the chip. Picture a delivery driver who must visit one house on every block in a city, instead of visiting the houses on one street in order. The same number of packages goes out, but the route is many times longer. When global memory loads are unaligned or strided, the memory controllers fetch many more cache sectors than the kernel actually uses. That saturates the HBM bus while delivering only a fraction of peak throughput to the SMs.

---

### 3.1 128-byte cache-line coalescing and AoS versus SoA

Global memory is reached through the L2 and L1 caches, which move data in aligned cache lines. Each line is split into sectors, and a sector is the smallest unit the memory system moves. When the threads in a warp issue a load, the hardware coalescer (the part that merges the warp's requests) groups their target addresses into as few sector transactions as it can. The closer the addresses sit together, the fewer transactions it needs.

Think of a warp as a group of people fetching books from a shelf. If they all reach for neighboring books, one shelf trip covers everyone. If each person is sent to a different aisle, the same number of books takes many more trips. Coalescing is the difference between those two trips.

- Optimal coalesced load: when threads in a warp read contiguous float values starting at an aligned address such as `in[idx]`, the entire warp request maps to one cache line and achieves full load efficiency.
- Misaligned contiguous load: if the warp's starting address is shifted off a cache-line boundary, the contiguous request straddles two cache lines and fetches an extra sector. The data is still contiguous, but the boundary costs a second trip.
- Strided or AoS load: when threads read strided addresses such as `in[idx * 2]`, or read one field out of an Array of Structures (AoS, where each record keeps all its fields together), a single warp spans multiple cache lines. Most of the bytes transferred across the HBM bus are then thrown away. Converting an Array of Structures to a Structure of Arrays (SoA, where each field gets its own contiguous array) fixes this. Adjacent threads then always read adjacent addresses for the same field.

The table lists four access patterns for the same 128 useful bytes. Read the sector column first, because it shows how many trips the warp made.

| Access pattern (32 threads reading 4-byte floats = 128 useful bytes) | Sectors fetched (32 B each) | Total bytes transferred | Global Memory Load Efficiency | Notes |
|---|---|---|---|---|
| **Aligned contiguous (`stride = 1`, `coalescedCopy`)** | **4.0 sectors** (1 cache line) | 128 B | **100%** (99% measured) | Optimal coalescing. |
| **Misaligned contiguous (`+4 B` offset)** | **5 to 8 sectors** (2 cache lines) | 160 B (at 5 sectors) | **80%** | Straddles cache-line boundary. |
| **Stride-2 (`in[idx * 2]`, `uncoalescedCopy`) or narrow AoS** | **8.0 sectors** (2 cache lines) | 256 B | **50%** (23% measured) | Wastes half of transferred bytes. |
| **Stride ≥ 8 or random scatter** | **32.0 sectors** (up to 32 lines) | 1,024 B | **12.5%** | 8x bandwidth waste. |

The first row is the goal. Every other row shows a way the same 128 useful bytes get wrapped in extra traffic. The measured figures in the stride-2 row sit a little below the ideal ones, which is the usual gap between counting sectors on paper and timing a real run.

### 3.2 Vectorized loads on Hopper and Blackwell

Even when a scalar load is fully coalesced, each thread still issues its own separate read, and the hardware coalescer has to stitch those reads together. Vectorized memory access changes that. It packs several elements into one wide load instruction per thread, which means fewer instructions for the same bytes. The trick depends on the alignment guarantee of `cudaMalloc`, which returns base pointers aligned for this purpose. Still, verify the pointer alignment before you cast an offset pointer to a vector type, because an offset from a misaligned base breaks the guarantee.

The table compares two vector widths. Each row lists the instruction, the bytes per thread, the cache lines per warp, and the alignment check you must pass.

| Vector load width | Target architecture | Per-thread instruction & bytes | Per-warp bytes & cache lines | Instruction reduction | Alignment requirement |
|---|---|---|---|---|---|
| **128-bit (`float4`)** | Ampere & Hopper | `LD.E.128` (4 floats = **16 bytes/thread**) | **512 bytes/warp** across 4 lines (**16 sectors**, 4.0 sectors/tx) | **4x fewer** memory instructions | `uintptr_t(ptr) % 16 == 0` |
| **256-bit (`alignas(32)` struct or `double4`)** | Blackwell B200 (CUDA 13+) | Native 32-byte global load (8 floats = **32 bytes/thread**) | **1,024 bytes/warp** across 8 lines (**32 sectors**) | **8x fewer** memory instructions (compiles to two 16 B loads on Hopper) | `uintptr_t(ptr) % 32 == 0` |

Read the two rows as a single idea repeated at a wider size. The 128-bit form reads 16 bytes per thread on Ampere and Hopper. The 256-bit form reads 32 bytes per thread on Blackwell. Both need the pointer to sit on a boundary of their own width, and a failed check is the signal to fix the layout before you tune anything else.

### 3.3 Read-Only Data Cache and Tensor Memory Accelerator

Two more hardware features on modern SMs remove the global-memory stalls that are left after coalescing and vectorization. Each one solves a different part of the problem.

The first is the read-only data cache, which you reach by declaring the pointer `const __restrict__`. When many threads repeatedly look up values in an immutable table, such as an embedding table that is larger than the constant cache, the compiler needs a promise. Without `const __restrict__`, the compiler must assume that the pointer might be aliased, which means another pointer could modify the same memory. That default path uses normal coherent global loads, which fill up L1 and L2 with data that is never reused. Marking the pointer `const float* __restrict__`, or calling `__ldg()`, makes the promise. It proves that the table is read-only and not aliased, so the compiler can route the loads through the low-latency read-only data cache.

The second is asynchronous bulk prefetching with the Tensor Memory Accelerator (TMA) and `cuda::memcpy_async`. Even a coalesced, vectorized load stalls a warp when the SM's load and store units must issue each address and then wait hundreds of cycles for HBM. On Hopper and Blackwell, the TMA is a dedicated hardware DMA engine (direct memory access, a copier that works without the SM's help) inside the SM. It copies multidimensional tiles between global HBM and shared memory asynchronously, using `cp.async.bulk`. That copy does not use SM registers or load and store slots. The trick is to allocate two ping-pong buffers in shared memory and coordinate them with the C++ `cuda::pipeline` API. While the warps compute on one tile, TMA streams the next tile in from HBM in the background.

```text
TMA double-buffering pipeline sequence (cuda::pipeline):
1. pipe.producer_acquire() -> 2. cuda::memcpy_async(...) -> 3. pipe.producer_commit()
4. pipe.consumer_wait()    -> 5. compute on staged tile  -> 6. pipe.consumer_release()
```

Read the sequence as two roles taking turns. The producer side acquires a buffer, starts the copy, and commits it. The consumer side waits for the copy to finish, computes on the tile, and then releases the buffer for reuse. With two buffers, the producer is always one tile ahead, so the consumer rarely waits.

The table below compares the five hardware and software memory optimizations from *AI Systems Performance Engineering* Chapter 7. Each row names the technique, the before and after numbers, and the speedup that the profiler showed.

| Optimization technique (*AI Systems Performance Engineering* Ch. 7) | Before (Unoptimized) | After (Optimized) | Speedup & key profiler evidence (`ncu`) |
|---|---|---|---|
| **1. Global Memory Coalescing** (`stride=2` → `stride=1`, Table 7-1) | 4.8 ms, 25% DRAM peak, 23% Load Eff, 8.0 sectors/req | **1.3 ms**, **90% DRAM peak**, **99% Load Eff**, **4.0 sectors/req** | **3.7x faster** (3.6x higher effective DRAM throughput). |
| **2. Shared-Memory Tiling** (`32 x 32` GEMM tile, Table 7-4) | 15 GFLOPS (1.5 FLOPs/B), 90% DRAM, 9,800 sectors | **170 GFLOPS** (**8.0 FLOPs/B**), **25% DRAM**, **1,200 sectors** | **11.3x higher GFLOPS** (8.2x fewer DRAM sector reads). |
| **3. Shared-Memory Padding** (`tile[32][32]` → `tile[32][33]`, Table 7-5) | 4.0 ms, 4.8M bank conflicts, 52% SMEM util, 38% stall | **1.3 ms**, **0 bank conflicts**, **100% SMEM util**, **0.5% stall** | **3.1x faster** (~3.1% / 1 KB memory overhead). |
| **4. Read-Only Cache** (adding `const __restrict__`, Table 7-6) | 2.5 ms, 52% Load Eff, 600 GB/s DRAM, 1,500 GB/s L2, 45% SM Active | **1.0 ms**, **97% Load Eff**, **200 GB/s DRAM**, **1,800 GB/s L2**, **93% SM Active** | **2.5x faster** (3x less DRAM traffic, served from L1/L2 cache). |
| **5. TMA + `cuda::memcpy_async` Double-Buffering** (Table 7-7) | 18.0 ms, 23% Load Eff, 6.4 sectors/req, 62% SM Active | **7.0 ms**, **99% Load Eff**, **4.0 sectors/req**, **100% SM Active** | **2.6x faster** (~800-cycle HBM latency hidden behind compute). |

The five rows form a progression. Rows 1 and 2 fix how bytes are laid out and reused. Row 3 fixes the bank conflicts, and rows 4 and 5 fix how the data is fetched. Each row removes a source of wasted traffic, and the speedup follows from that.

:::info In one minute: Section 3 takeaways
- What should the profiler show? Aim for 4.0 sectors per request and above 95% Global Memory Load Efficiency in `ncu`.
- Which vector width fits your GPU? Use `float4` vector loads on Ampere and Hopper, and 32-byte `alignas(32)` vector loads on Blackwell.
- How do you hide HBM latency? Mark read-only lookup tables `const __restrict__`, and use TMA with `cuda::memcpy_async` and `cuda::pipeline` to double-buffer global-to-shared tile transfers.
:::

---

## 4. Device and Host-Device memory: Capacity vs Bandwidth, ReBAR, Memory Pools, and Unified Memory

Picture a model that fits comfortably in GPU memory, with plenty of free space, and still misses its production latency target. The GPU is not short of room. The bottleneck is the speed of the path that feeds it. Platform engineers also hit mysterious multi-millisecond stalls between kernels. When that happens, the cause is often a host BIOS setting that caps the PCIe aperture, or a training loop that calls a synchronous OS memory allocator on every step.

### 4.1 Capacity versus Bandwidth

In cluster sizing and incident triage, never confuse HBM capacity in gigabytes with HBM bandwidth in terabytes per second. They answer different questions. Capacity decides whether the model weights, the KV cache, and the activations fit without an out-of-memory error. Bandwidth sets the physical speed limit on how fast those bytes can stream into the SMs. A system can have plenty of one and too little of the other.

- Worked serving latency floor on a 13B FP16 model: a thirteen-billion-parameter model in half precision fits inside an H100 with plenty of free VRAM to spare. During unbatched autoregressive decode, though, the GPU must read all the model weights from HBM for every token it generates. No amount of extra free VRAM lowers that per-token floor. You must increase HBM bandwidth, quantize the weights to lower precision, or use continuous batching so that each weight read serves several requests at once.
- Worked bandwidth-utilization check: when an elementwise kernel processes data near the physical peak on an H100, the memory controllers are already saturated. The only way to speed up that step is kernel fusion or reduced precision. If the kernel reaches only a small fraction of the peak, the bus is not the limit, and uncoalesced addressing or partition stride contention is wasting bandwidth.

The derivations below work both examples with numbers. Follow the first one line by line, since it explains the per-token floor.

```text
Worked capacity vs. bandwidth derivations (V2 Ch. 5 & Ch. 8):
1. 13B FP16 decode floor on H100 SXM (80 GB VRAM, 3,350 GB/s = 3.35 TB/s peak):
   - Weight footprint = 13e9 params x 2 bytes = 26.0 GB (leaves 54.0 GB free VRAM)
   - Minimum Token Latency Floor = 26.0 GB / 3,350 GB/s = 0.007761 s ≈ 7.76 ms/token (~7.8 ms/token)
   - FP8 quantization (1 byte/param = 13.0 GB): 13.0 GB / 3,350 GB/s = 3.88 ms/token
   - Higher HBM bandwidth options: H200 at 4.8 TB/s (4,800 GB/s) or B200 at 8.0 TB/s (8,000 GB/s)

2. Elementwise bandwidth utilization check on H100 (8 GB read + 8 GB write = 16.0 GB in 6.0 ms):
   - Effective Bandwidth = 16.0 GB / 0.006 s = 2,666.7 GB/s (79.6% ≈ 80% of 3,350 GB/s peak -> saturated)
   - Pathological case = 500 GB/s (14.9% ≈ 15% of 3,350 GB/s peak -> uncoalesced or partition-strided)
```

The first derivation reads like a simple division. The model's weights are 26 GB, and every token streams them through the memory bus once. Dividing 26 GB by the 3.35 TB/s bus gives about 7.8 milliseconds per token, which is the floor no matter how much memory is free. Halving the bytes per weight with FP8 halves that floor. The second derivation runs the same logic in reverse. A kernel that moves 16 GB in 6 ms is already using about 80 percent of the bus, so there is little left to gain from better addressing, and only fusion or lower precision can help.

### 4.2 PCIe BAR1 and Resizable BAR, Stream-Ordered Memory Pools, and Unified Memory

Beyond the GPU package itself, three host and runtime memory settings directly govern production stability. Each one is easy to overlook, and each one shows up as a symptom far from its cause.

- PCIe BAR1 and Resizable BAR: Base Address Register 1 is the PCIe aperture, a window in the host CPU's physical address space. The CPU and peer RDMA NICs use this window to map GPU HBM for GPUDirect RDMA. Legacy BIOS defaults cap BAR1 at a tiny window, which forces transfers to be broken into many small pieces. On every production GPU server, Resizable BAR and Above 4G Decoding must be enabled in the BIOS, so that BAR1 Total matches the full GPU VRAM.
- Stream-ordered memory pools (`cudaMallocAsync` and `PYTORCH_ALLOC_CONF`): traditional `cudaMalloc()` and `cudaFree()` are synchronous across the entire GPU device, and they call into the operating system (`mmap` and `ioctl`). Those calls cause context switches and pipeline stalls whenever a loop allocates temporary buffers. In CUDA C++, use `cudaMallocAsync(&ptr, bytes, stream)` and `cudaFreeAsync(ptr, stream)` on a non-blocking stream (`cudaStreamCreateWithFlags(&s, cudaStreamNonBlocking)`). A pool keeps freed memory around for reuse, so the next allocation does not go back to the OS. You can tune how much the pool keeps with `cudaMemPoolSetAttribute(..., cudaMemPoolAttrReleaseThreshold, ...)` and `cudaMemPoolTrimTo`. In PyTorch, the caching memory allocator implements this pool strategy automatically, and you control it through `PYTORCH_ALLOC_CONF`, formerly `PYTORCH_CUDA_ALLOC_CONF`. Set `expandable_segments:True` to prevent fragmentation OOMs, where memory is free in total but too scattered to hand out.
- Unified Memory (`cudaMallocManaged`) and proactive prefetching: calling `cudaMallocManaged()` creates a single pointer that the CPU and the GPU can both use, with the hardware page faulting pages across as needed. On PCIe systems, touching a page that has not moved yet inside a GPU kernel triggers an expensive on-demand page fault across the bus. On Grace Hopper GH200 and Grace Blackwell GB200 and GB300 systems, pages migrate over the high-bandwidth coherent NVLink-C2C instead. Even on those Superchips, you should avoid surprise page-fault stalls. Advise the driver and prefetch the buffers before the kernel launches.

The three settings share one theme. Each one decides whether the GPU waits for a slow path that the kernel code never sees. The BIOS decides how big the window is, the allocator decides how often the OS gets involved, and the prefetch decides whether a page is already in place when the kernel asks for it.

The command below checks the BAR1 window on a host. It filters the memory report down to the BAR1 block, so you can compare the total against the VRAM.

```text
$ nvidia-smi -q -d MEMORY | grep -A 5 "BAR1"
    BAR1 Memory Usage
        Total                             : 81920 MiB
        Used                              : 2 MiB
        Free                              : 81918 MiB
```

Read the `Total` line first. It should match the VRAM of the card. A total of 256 MiB is the value the diagnostic warns about, and it means the BIOS setting is still wrong. The `Used` and `Free` lines are only the current state.

The next block lists the advice and prefetch calls for managed memory. Each line tells the driver one thing about the buffer, and the last line starts the move.

```cpp
cudaMemAdvise(ptr, size, cudaMemAdviseSetPreferredLocation, gpuId);
cudaMemAdvise(ptr, size, cudaMemAdviseSetReadMostly, gpuId);
cudaMemAdvise(ptr, size, cudaMemAdviseSetAccessedBy, otherGpuId);
cudaStreamAttachMemAsync(stream, ptr, 0, cudaMemAttachSingle);
cudaMemPrefetchAsync(ptr, size, gpuId, stream);
```

The advice lines describe where the data should live and who will read it. The prefetch line moves it there ahead of time, on the stream, so the kernel finds it already in place.

Combining the BAR1 Resizable BAR check, the pinned memory check, the `cudaMallocAsync` pool check, and the `cudaMemPrefetchAsync` Unified Memory check into `audit_host_device_memory_config` in `code/part10/gpu_memory_hierarchy.py` is a suggestion of this chapter rather than a published recipe. The function is meant to run the four checks in one pass, which makes the review repeatable.

:::info In one minute: Section 4 takeaways
- What does gigabytes decide? Capacity in gigabytes decides whether weights, KV cache, and activations fit. Bandwidth in terabytes per second sets the per-token decode floor.
- What should the BAR1 check show? Always verify that BAR1 Total is at least equal to VRAM Total via `nvidia-smi -q -d MEMORY`.
- What replaces the slow allocator? Replace synchronous `cudaMalloc` and `cudaFree` inside loops with stream-ordered `cudaMallocAsync` and `cudaFreeAsync`, or set `PYTORCH_ALLOC_CONF=expandable_segments:True`. Pair `cudaMallocManaged` with `cudaMemPrefetchAsync` and `cudaMemAdvise`.
:::

---

## 5. Field notes from the Volume 02 memory chapters

When a team triages a slow training or inference job in production, the profiler metrics are often misread. Terms like global memory, local memory, and peak bandwidth sound interchangeable in casual conversation, but each one names a different thing. Treating a timing gap as proof of uncoalesced loads, without checking occupancy or L2 hit rates, leads engineers to rewrite kernels that were actually stalled on host copies or partition contention. These field notes are meant to slow that reflex down.

These field notes come from the source notes' memory chapters and labs. All command outputs below are marked illustrative in those notes rather than captured on live hardware, so treat the numbers as diagnostic examples rather than hardware specifications.

### 5.1 Words that are easy to confuse

The notes highlight four pairs of memory terms that engineers regularly mix up during design reviews and incident calls. Every memory tier is characterized by five measurable properties: capacity, peak bandwidth, effective bandwidth, latency, and reuse. Reuse measures how many useful operations are performed on a piece of data before it must be fetched again.

The table defines each term by what it means and by what it does not mean. Read the second column as the definition and the third column as the trap.

| Term | What it means | What it does not mean |
|---|---|---|
| Global memory | An address space: visible to every thread and block | A separate chip. A global load can be served by L1 or L2 and never reach HBM |
| HBM | The physical stacked DRAM on a wide interface that backs global memory on data-center GPUs | A software visibility rule |
| Local memory | Private to one thread (logical scope) | On-chip. It is backed by the device memory path |
| Peak bandwidth | The theoretical maximum transfer rate | What a kernel achieves. Effective bandwidth is the useful bytes delivered per second |

The most common mix-up is the first row. People picture global memory as a chip of its own, but it is only an address space. A load to global memory might be satisfied by L1 or L2 and never touch HBM at all. The same confusion hits local memory, which sounds on-chip but lives in the device memory path.

### 5.2 Locality, memory partitions and what to size

Understanding why a kernel misses peak bandwidth, or why it runs out of memory under load, requires looking at locality, hardware partitions, and runtime state growth. Locality is the idea that recently and nearby used data is likely to be used again. Partitions are the physical split of memory into controllers that work in parallel. Runtime state is everything that grows while a job runs.

- Temporal locality: the same data is reused soon, so an on-chip cache can avoid a repeat HBM read.
- Spatial locality: nearby addresses are used together, so a single cache transaction serves several thread values.
- Working set: if reuse happens only after the data has already been evicted from cache, the cache gives little benefit.
- Memory partitions: HBM bandwidth is delivered in parallel across multiple memory controllers and partitions, and hardware address mapping spreads requests across them. A bad stride or memory layout can concentrate traffic on a few partitions while others sit idle. This makes a kernel deliver far less than peak bandwidth, even when its accesses are coalesced.
- Capacity plan must include runtime state: training requires parameters, gradients, optimizer state, activations, communication buffers, and checkpoints. Inference requires weights, KV cache, temporary workspaces, batching buffers, and allocator reserves or fragmentation headroom. Always size for peak concurrency and sequence length, rather than the quiet moment right after the model loads.
- KV cache estimate: the KV cache byte footprint follows the formula below. It grows dynamically with sequence length and traffic, unlike the static model weights.

```text
KV cache byte footprint formula (Volume 02 interview note):
KV_cache_bytes = 2 x layers x heads x head_dim x sequence_length x batch_size x bytes_per_element
(where the factor of 2 accounts for Key plus Value tensors)
```

Read the formula from the left. Each factor is a dial you can turn. More layers, more heads, longer sequences, bigger batches, and wider numbers all push the total up. The leading 2 is there because every token keeps both a key and a value. Plug in your own model's values before a capacity review, and you will see why the cache can outgrow the weights under load.

### 5.3 Evidence patterns

The table below summarizes four recurring profiler signatures from the source notes, along with how to read each one.

| Symptom | Evidence in the note | How to read it |
|---|---|---|
| Host-to-device copies dominate | `nsys stats` GPU trace: HtoD memcpy 61.2% (18.4 ms), compute kernel 4.1% (1.2 ms), DtoH memcpy 33.9% (10.2 ms) | The GPU is not the limit. Use pinned memory, fewer larger transfers, or overlap copy and compute |
| Scattered or strided loads | sectors per request 18.6 (ideal is about 4, worst case 32) | The warp fetches roughly 4 to 5 times more sectors than it uses |
| Shared-memory bank conflicts | `l1tex__data_bank_conflicts_pipe_lsu.sum` = 412,800 on a kernel expected to be conflict-free | A stride maps several lanes to one bank. Fix with a small padding or layout change, not a rewrite |
| A "faster" kernel got slower | `-Xptxas=-v` diff: 44 registers and 0 spills became 88 registers with 40 bytes spill stores and 48 bytes spill loads | Two costs at once: lower occupancy and new memory traffic |

The first row shows that the GPU can be idle while the copies run. The second row explains a number that looks odd until you divide it. 18.6 sectors per request, against an ideal of about four, means each warp pulls several times the bytes it uses. The last two rows point at fixes that are a padding change and a register review, which are small and specific.

Two operational rules follow from these patterns. First, forcing a lower register count with a launch bound can make a kernel slower, because live values spill to local memory instead of disappearing. Second, a compiler upgrade can change register allocation for unchanged source code, so always diff the `-Xptxas=-v` output, built with `nvcc -O3 -Xptxas=-v`, between compiler versions. Shared memory and L1 also share the same on-chip SRAM on many architectures, so a kernel that carves out more shared memory leaves less room for L1.

### 5.4 Lab 03 worked comparison: contiguous versus strided copy

In the third lab of the source notes, two kernels copy `1 << 24` floats for one hundred iterations on an illustrative H100 run. The contiguous kernel maps thread `i` to element `i`. The strided kernel maps logical thread `i` to element `(i * 32) % count`. The two kernels do the same work on the same data, but they visit the memory in different orders.

| Metric | Contiguous | Strided |
|---|---:|---:|
| Elapsed time | 42.18 ms | 156.42 ms (about 3.7x) |
| Registers per thread | 16 | 20 |
| Spills | 0 bytes | 0 bytes |
| Memory throughput | 91.2% | 68.4% |
| L2 hit rate | 34.1% | 9.8% |
| Achieved occupancy | 87.4% | 85.9% |
| Sectors per request | 4.0 | 23.5 |

The notes reason through the evidence in a useful order. Achieved occupancy is nearly identical between the two runs, so warp residency is ruled out as the cause. Sectors per request jump upward while the L2 hit rate drops, and those two changes together explain the gap in elapsed time. The notes also warn that the modulo arithmetic in the strided kernel adds some instruction cost of its own. A rigorous diagnosis states both what the evidence supports and what is still uncertain. A timing difference alone is never proof of a coalescing problem. If the strided kernel is not slower on your GPU, change the stride and the array size, and profile again instead of forcing the result you expected.

### 5.5 Customer scenarios from the notes

Two customer situations from the notes show how the same numbers lead to different advice.

- Recommendation model with large embedding lookups: when a workload has irregular access patterns and very little data reuse, focus on memory capacity, HBM bandwidth, cache behavior, data placement, and batching. Peak Tensor Core throughput is not the bottleneck.
- Comparing GPUs for small-batch weight streaming: when a team compares GPUs by memory capacity and peak compute alone, add HBM bandwidth, L2 behavior, reuse, and latency targets to the comparison. A less compute-dense GPU can be the better fit if it meets the capacity and bandwidth need at lower cost.

The lesson is the same in both cases. Pick the GPU and the tuning by the resource the workload actually waits on, not by the headline number on the spec sheet.

---

## Commands and configurations that matter

The three command groups below cover a host check, a kernel check, and an allocator setting. Run them in that order, because each one narrows the search for the next.

### 1. Pre-flight check for BAR1, HBM usage, and streaming SM vs memory utilization

The first command confirms that the BAR1 window maps the full VRAM. The second samples SM and memory activity once per second for five samples, which tells you whether the SMs are waiting on memory.

```bash
# 1. Confirm Resizable BAR (Large BAR1) maps full GPU VRAM (expect ~81920 MiB on H100 80GB, NOT 256 MiB!)
nvidia-smi -q -d MEMORY | grep -A 5 "BAR1"

# 2. Sample SM compute utilization (%) vs HBM memory interface busy (%) every 1 second
nvidia-smi dmon -s ucm -c 5
```

### 2. Inspecting register spills and Nsight Compute memory counters

The first command builds the kernel and prints its register and spill counts. The second asks Nsight Compute for the cache hit rates, the DRAM throughput, the sectors per request, and the bank conflicts, all in one pass.

```bash
# 1. Check compile-time register count and verify 0 bytes spill stores / 0 bytes spill loads
nvcc -O3 -arch=sm_90 -Xptxas=-v memory_patterns.cu -o memory_patterns

# 2. Profile L1/L2 hit rates, DRAM throughput, global load sectors/request, and shared-memory bank conflicts
ncu --metrics \
  dram__throughput.avg.pct_of_peak_sustained_elapsed,\
  l1tex__t_sector_hit_rate.pct,\
  lts__t_sector_hit_rate.pct,\
  l1tex__average_t_sectors_per_request_pipe_lsu_mem_global_op_ld.ratio,\
  l1tex__data_bank_conflicts_pipe_lsu.sum \
  ./memory_patterns
```

### 3. Configuring PyTorch's caching allocator pool to reduce VRAM fragmentation

PyTorch's caching allocator can be told to use expandable segments. That setting reduces fragmentation, so the pool can grow in place instead of splitting into pieces. Set the variable before the process starts.

```bash
# Use expandable virtual memory segments in PyTorch's caching allocator pool
export PYTORCH_ALLOC_CONF="expandable_segments:True"
```

---

## How it fails

The table lists five failure modes that you will meet in production. Each row gives the symptom you see first, the root cause behind it, and the fix to try. Match the symptom first, and then trace it to the cause.

| Failure mode | Symptom | Root cause | Diagnosis & fix |
|---|---|---|---|
| **1. Register spilling into off-chip Local Memory** | After unrolling a loop or adding local arrays, kernel latency jumps 2x–4x and `nvidia-smi dmon` shows elevated `mem%` for identical input tensors. | Thread register demand exceeded 255 (or exceeded the block's register budget), causing `ptxas` to spill variables to **Local Memory** (65,536 threads spilling 8 B = 1.05 MB of hidden HBM traffic per launch). | Run `nvcc -O3 -Xptxas=-v` and check for non-zero **spill stores / spill loads**; reduce live variable scope, replace dynamically indexed per-thread arrays with Shared Memory, or adjust `__launch_bounds__`. |
| **2. 32-way Shared-Memory Bank Conflict on 32 x 32 tiles** | A kernel that stages a 32 x 32 float tile in `__shared__` memory achieves only ~50% of expected shared-memory bandwidth and stalls 38% of cycles on memory. | Threads in a warp read or write down a **column** of `__shared__ float tile[32][32]` (stride = 32 floats = 128 bytes), mapping all 32 lanes to the **exact same bank (bank 0)**. | Confirm with `ncu --metrics l1tex__data_bank_conflicts_pipe_lsu.sum`; pad the array to **`__shared__ float tile[32][33]`** (stride = 33, 0 conflicts, 3.1x speedup) or apply XOR index swizzling. |
| **3. Uncoalesced / AoS global loads (15–25% achieved HBM bandwidth)** | `nvidia-smi dmon` shows `mem = 90%+` and `sm = 18%`, yet achieved bytes/sec (`useful_bytes / time`) is only 500 GB/s (~15% of H100 peak). | Threads read strided or scattered addresses (AoS), forcing the memory system to fetch **8 to 32 sectors (256–1,024 B)** per warp instead of **4 sectors (128 B)**. | Check `l1tex__average_t_sectors_per_request_pipe_lsu_mem_global_op_ld.ratio` in `ncu`; convert AoS to **SoA**, align pointers to 16/32 bytes, and use vectorized **`float4` (16 B)** or **Blackwell 32 B** loads. |
| **4. Legacy 256 MiB BAR1 aperture bottleneck (ReBAR disabled)** | Host-to-device DMA transfers, GPUDirect RDMA, or peer-to-peer mappings crawl or fail with BAR1 exhaustion errors on an 80 GB GPU node. | **Resizable BAR (ReBAR / Above 4G Decoding)** was left disabled in the server BIOS after a motherboard replacement or BIOS reset. | Run `nvidia-smi -q -d MEMORY \| grep -A 5 "BAR1"`. If `Total` is 256 MiB, reboot into BIOS, enable **Above 4G Decoding** and **Resizable BAR**, and verify `Total` matches full VRAM (81,920 MiB). |
| **5. Synchronous `cudaMalloc` or unprefetched `cudaMallocManaged` stalls** | `nsys` timeline shows millisecond-scale gaps between kernel launches with frequent OS `ioctl`/`mmap` calls or GPU page-fault migrations. | The application calls synchronous `cudaMalloc`/`cudaFree` inside the training/serving loop, or touches `cudaMallocManaged` buffers on the GPU without prefetching. | Switch to stream-ordered **`cudaMallocAsync` / `cudaFreeAsync`** (or PyTorch's caching allocator pool), and call **`cudaMemPrefetchAsync`** + **`cudaMemAdvise`** before launching kernels on Unified Memory. |

---

## Hands-on lab

### Self-checking Python model (`code/part10/gpu_memory_hierarchy_lab.py` — verified here)

The module `code/part10/gpu_memory_hierarchy.py` implements the seven-tier Blackwell and Hopper memory specifications. It also includes the capacity-versus-bandwidth evaluators, the register-spill calculators, the cache-line coalescing models, the shared-memory bank conflict solvers, and the host-device BAR1 and pool auditors. Its companion script, `code/part10/gpu_memory_hierarchy_lab.py`, runs twenty-five self-checks across six core areas. The areas are listed below, so you can see which part of the chapter each check protects.

- Blackwell memory hierarchy and Points of Coherency: validates registers, shared/L1, TMEM, constant cache, L2 cache, local memory, and global HBM3e.
- Capacity versus bandwidth decode floor: evaluates the half-precision weight footprint inside an H100 and its weight-read latency floor.
- Register spilling and effective bandwidth utilization: computes hidden HBM spill traffic and compares saturated versus uncoalesced HBM throughput.
- Cache-line coalescing and vectorized loads: models sector counts and load efficiency across aligned, misaligned, strided, `float4`, and Blackwell vector accesses.
- Shared-memory bank conflict math: verifies row accesses, unpadded column conflicts, padded `tile[32][33]` column accesses, even strides, and hardware broadcasts.
- Benchmark tables and host-device config audits: checks all five optimization tables, plus the BAR1 Resizable BAR, pinned memory, `cudaMallocAsync`, and `cudaMemPrefetchAsync` rules.

The parameter block below lists the values the checks use, so you can compare each expected result with the arithmetic in the earlier sections.

```text
Lab verification parameters (25 self-checks):
- Blackwell tiers: TMEM = 256 KB/SM (~10 cycles, non-pointer-addressable); L2 = 126 MB (B200) vs 50 MB (H100).
- Decode floor: 13B FP16 = 26.0 GB on 80 GB H100 (54.0 GB free) -> 7.76 ms/token at 3,350 GB/s.
- Register spills: 8 B/thread across 65,536 threads -> 1,048,576 B = 1.05 MB decimal (1.0 MiB) traffic.
- Effective bandwidth: 16 GB / 6 ms = 2,666.7 GB/s (79.6% of H100 peak) vs 500 GB/s (14.9%).
- Coalescing: aligned 4B = 4 sectors (100% eff); +4B offset = 5 sectors across 2 lines (80% eff); stride 2 = 8 sectors (50% eff); stride 8 = 32 sectors (12.5% eff); float4 16B = 512 B across 4 lines (16 sectors); Blackwell 32B = 1,024 B across 8 lines (32 sectors).
- Bank conflicts: stride 1 = 32 banks (1-way); stride 32 = 1 bank (32-way conflict); stride 33 = 32 banks (0 conflicts); stride 2 = 2-way; stride 16 = 16-way; stride 0 = 1-cycle broadcast.
```

Run the lab from the repository root. The `-B` flag keeps Python from writing bytecode into the repository.

```bash
python3 -B code/part10/gpu_memory_hierarchy_lab.py
```

The output below came from a run in this repository. Each `PASS` line names the source table it checks, so you can trace the result back to the text.

```text
=== Chapter 10.3 Lab: The GPU Memory Hierarchy ===
  [PASS] ASP Ch6 Table 6-5: Tracks all 7 Blackwell memory tiers (Registers, Shared/L1, TMEM, Constant, L2 126MB, Local, Global HBM3e)
  [PASS] ASP Ch6 p.194: TMEM is 256 KB per SM dedicated to Tensor Cores (~10 cycles) and is not directly pointer-addressable in C++
  [PASS] ASP Ch6 p.196 & V2 Ch7: Local memory is thread-scoped logical spill space backed by off-chip HBM DRAM
  [PASS] ASP Ch6 Fig 6-15: 5 Points of Coherency (thread, thread_block_cta, thread_block_cluster, device, system)
  [PASS] V2 Ch5 worked example: 13B FP16 model == 26.0 GB (fits in 80 GB H100 with 54 GB free), weight-read floor == 7.76 ms/token (~7.8 ms)
  ...
  [PASS] VL4 Ch1 §3.4: 80 GB GPU with BAR1 == 81,920 MiB passes ReBAR check; BAR1 == 256 MiB flags legacy PCIe aperture bottleneck
  [PASS] ASP Ch6 & VL4 Ch1: Flags pageable host memory, synchronous cudaMalloc in loop, and unprefetched Unified Memory
  [PASS] Rejects invalid per-thread vector byte width
  [PASS] Rejects non-positive VRAM / BAR1 capacity

Summary: 25 passed, 0 failed (total 25)
```

The lab output is the check, and the next step is the real card. The commands in the earlier section, such as `nvcc`, `ncu`, and `nvidia-smi`, were not run on a live cluster, so run them on a GPU host before you trust the numbers.

---

## Common first mistakes

Each of these mistakes is common, and each one has a short check that catches it.

- Assuming local memory is fast on-SM memory is the first. Local memory is a per-thread logical address space backed by off-chip HBM DRAM, and a cache miss on it costs hundreds to over a thousand cycles. Always check `nvcc -O3 -Xptxas=-v` for `spill stores` and `spill loads`.
- Declaring `__shared__ float tile[32][32]` when warps read columns is the second. Shared memory has thirty-two banks, so reading down a column of an unpadded float array hits the same bank across all threads in the warp and triggers a bank conflict. Pad the array to `tile[32][33]` by adding one column.
- Forgetting `const __restrict__` on read-only lookup or embedding tables is the third. Without `const __restrict__`, the compiler cannot prove non-aliasing, and it skips the low-latency read-only data cache path.
- Casting unaligned offset pointers to `float4*` or wide vector types is the fourth. `cudaMalloc` guarantees base alignment, but adding an unaligned element offset, such as `ptr + 1`, before `reinterpret_cast<const float4*>` causes a misaligned address fault (`cudaErrorMisalignedAddress`).
- Calling synchronous `cudaMalloc` or `cudaFree` inside a request or training loop is the fifth. Synchronous allocations stall the streams on the GPU and trigger OS `ioctl` and `mmap` context switches. Use `cudaMallocAsync` and `cudaFreeAsync`, or framework memory pools, instead.
- Ignoring `BAR1 Total: 256 MiB` in `nvidia-smi -q -d MEMORY` is the sixth. Leaving Resizable BAR disabled in the BIOS forces CPU and RDMA mappings through a tiny aperture.

---

## Exercises

Each exercise gives one task. The input values for all six are listed in the block after the list, so you do not have to look them up.

- First exercise: run `python3 -B code/part10/gpu_memory_hierarchy_lab.py` and inspect `code/part10/gpu_memory_hierarchy.py`. Use `evaluate_capacity_vs_decode_floor` to compare the weight-read latency floor of a large language model across FP16, FP8, and FP4. Run it on H100, H200, and B200, using the parameters in the block below.
- Second exercise: using `calc_register_spill_traffic`, calculate how many megabytes of extra HBM traffic a grid generates per launch when it spills four floats per thread.
- Third exercise: call `calc_warp_coalescing_and_vector_loads(4, stride_elements=s, base_offset_bytes=0)` for the stride values listed below. Determine how many sectors are fetched at each stride. Then work out the Global Memory Load Efficiency percentage for each one.
- Fourth exercise: call `calc_shared_mem_bank_conflict(stride)` for the stride values listed below. Explain why even strides cause bank conflicts. Then explain why odd strides are conflict-free.
- Fifth exercise: using `calc_effective_bandwidth_utilization`, evaluate a kernel on a Blackwell B200 that reads and writes the buffer sizes listed below. What percentage of peak HBM3e bandwidth does it achieve?
- Sixth exercise: using `audit_host_device_memory_config`, test the node configuration listed below, where BAR1 is capped at its legacy default. Which BIOS setting is misconfigured? Which `nvidia-smi` command verifies the fix?

```text
Exercise input parameters for code/part10/gpu_memory_hierarchy.py:
- Exercise 1 (evaluate_capacity_vs_decode_floor): 70B model in FP16 (2 B/param), FP8 (1 B/param), FP4 (0.5 B/param) across H100 (3,350 GB/s), H200 (4,800 GB/s), B200 (8,000 GB/s).
- Exercise 2 (calc_register_spill_traffic): 1,024 blocks x 256 threads, spilling 4 floats (16 bytes) per thread.
- Exercise 3 (calc_warp_coalescing_and_vector_loads): stride_elements s = 1, 2, 4, 8, 16 with base_offset_bytes = 0 (32-byte sectors).
- Exercise 4 (calc_shared_mem_bank_conflict): stride values 0, 1, 2, 4, 8, 16, 32, 33.
- Exercise 5 (calc_effective_bandwidth_utilization): Blackwell B200 (8,000 GB/s peak), 32 GB read + 32 GB write in 9.5 ms.
- Exercise 6 (audit_host_device_memory_config): vram_total_mib = 143360 (H200 141 GB), bar1_total_mib = 256.
```

---

## Interview angles

- "What is the difference between Global Memory, Local Memory, Shared Memory, Registers, and Blackwell's TMEM?"
  *Answer:* Registers are private per-thread on-SM SRAM with single-cycle latency. Shared memory is per-block on-SM SRAM explicitly staged by the programmer. Blackwell TMEM is dedicated on-SM SRAM for fifth-generation Tensor Core accumulators and operands, managed via TMA and `tcgen05` descriptors rather than C++ pointers. Global memory is device-wide off-chip stacked HBM DRAM. Local memory is a per-thread logical spill space physically backed by off-chip HBM DRAM when registers spill.
- "Why does a naive Shared-Memory matrix transpose suffer a bank conflict, and why does declaring `tile[32][33]` fix it?"
  *Answer:* Shared memory has thirty-two banks that repeat every thirty-two floats. In `tile[32][32]`, reading down a column steps by the exact bank period, so all threads in a warp land on the same bank and serialize the read. Padding to `tile[32][33]` makes the row stride coprime to the bank count. Each thread in the warp then lands in a distinct bank with zero conflicts.
- "A 13B FP16 model only uses 26 GB of an 80 GB H100, yet single-user token generation cannot get below ~8 ms/token. Why?"
  *Answer:* Capacity only answers whether the model fits in VRAM, whereas autoregressive decode must stream all model weights from HBM for every output token. Dividing the weight footprint by the H100 peak bandwidth sets the physical weight-read latency floor. You lower that floor by quantizing to FP8 or FP4, upgrading to higher-bandwidth HBM on H200 or B200, or using continuous batching.
- "How does the Tensor Memory Accelerator on Hopper and Blackwell improve memory-bound kernels?"
  *Answer:* Instead of using the SM's load/store units and thread registers to issue addresses and wait hundreds of cycles for HBM, the TMA hardware DMA engine executes bulk multidimensional global-to-shared copies in the background. It uses `cuda::memcpy_async` and `cuda::pipeline` while the SM's warps compute on the previous tile in a ping-pong buffer.
- "What is BAR1 in `nvidia-smi -q -d MEMORY`, and why is 256 MiB a red flag on an AI node?"
  *Answer:* BAR1 is the PCIe Base Address Register aperture mapping GPU HBM into the host CPU physical address space. Seeing a small legacy aperture means Resizable BAR is disabled in the server BIOS. That bottlenecks host DMA and GPUDirect RDMA transfers that expect the full VRAM aperture to be mapped.

---

## Checkpoint questions (20)

<details>
<summary>**1. List the seven tiers of the Blackwell B200 memory hierarchy from fastest to slowest, with their scope, capacity, and approximate latency.**</summary>

Registers are per-thread on-SM storage at about 1 cycle. Shared memory and L1 are per-block or per-cluster SRAM on the SM at about 20 to 30 cycles. Tensor Memory (TMEM) is per-SM dedicated SRAM on Blackwell at about 10 cycles. Constant cache is per-SM read-only cache at about 1 cycle on a broadcast. L2 cache is GPU-wide cache at about 200 cycles. Local memory is per-thread spill space backed by HBM, and HBM global memory is off-chip DRAM at about 800 cycles typical.

</details>

<details>
<summary>**2. What is Tensor Memory (TMEM) on Blackwell (256 KB/SM), what is its approximate latency (~10 cycles), and how is data moved into and out of it if it is not pointer-addressable in C++?**</summary>

TMEM is dedicated SRAM per SM on Blackwell used by the fifth-generation Tensor Cores for accumulators and operands. It is not pointer-addressable in C++. Data moves in and out through TMA and `tcgen05.mma` or UMMA descriptors.

</details>

<details>
<summary>**3. What are the five Points of Coherency (PoC) for GPU threads, from narrowest to widest scope?**</summary>

Thread level is the register file. Thread block level is L1 and shared memory on one SM synchronized with `__syncthreads()`. Cluster level is Distributed Shared Memory across SMs in a GPC synchronized with `cluster.sync()`. Device level is L2 and global HBM across all SMs. System level is coherent memory across GPUs and the host over NVLink, NVSwitch, NVLink-C2C, or PCIe.

</details>

<details>
<summary>**4. When `nvidia-smi dmon -s ucm` shows `sm = 18%` and `mem = 90%`, how do you use L1 and L2 hit rates in `ncu` (`l1tex__t_sector_hit_rate.pct` and `lts__t_sector_hit_rate.pct`) to distinguish a streaming/uncoalesced pattern from an L2-thrashing working set?**</summary>

Low SM utilization with high memory utilization means the SMs are starving while the memory interface is saturated. Low L1 and low L2 hit rates with high HBM traffic point to a streaming or uncoalesced pattern bypassing both caches, which you fix with SoA layout, coalescing, or tiling. A high L2 hit rate with high HBM traffic means the working set slightly exceeds L2 capacity and is thrashing, which you fix by reducing precision, fusing kernels, or adjusting tile and batch sizes.

</details>

<details>
<summary>**5. Why is Local Memory slow despite its name, and what two code patterns cause `nvcc` to place data in Local Memory?**</summary>

The word local describes logical scope private to a thread, not physical location. Local memory lives in off-chip HBM and is reached through L1 and L2. The `nvcc` compiler uses it for register spills when live variables exceed the per-thread register cap or `__launch_bounds__`, and for local arrays indexed with a runtime variable such as `buf[i]`.

</details>

<details>
<summary>**6. If a kernel launches 256 blocks of 256 threads (65,536 threads) and spills 2 floats (8 bytes) per thread, how many bytes (1,048,576 B ≈ 1.05 MB) of extra memory traffic are generated per launch?**</summary>

Multiplying total threads by spilled bytes per thread and doubling for one spill store plus one spill load equals 1,048,576 bytes, or about 1.05 MB of extra cache and HBM traffic per launch. That traffic appears nowhere in the C++ source code.

</details>

<details>
<summary>**7. How does 32 x 32 Shared-Memory Tiling change global memory sector reads (9,800 → 1,200), DRAM throughput (90% → 25%), arithmetic intensity (1.5 → 8.0 FLOPs/B), and GFLOPS (15 → 170) in Table 7-4 of *AI Systems Performance Engineering*?**</summary>

Each tile element is fetched from HBM once per block instead of thirty-two times. As a result, global load sectors drop from 9,800 to 1,200, DRAM throughput drops from 90% to 25%, arithmetic intensity rises from 1.5 to 8.0 FLOPs/byte, and sustained throughput jumps from 15 to 170 GFLOPS. Shared-memory throughput and SM occupancy also rise substantially.

</details>

<details>
<summary>**8. Why does scaling a 2D Shared-Memory tile from 32 x 32 to 64 x 64 (with 1,024 threads and 22 registers/thread) cap SM residency at 2 blocks (2,048 threads)?**</summary>

A 1,024-thread block using 22 registers per thread consumes 22,528 registers per block. Two blocks fit inside the 65,536-register file, but two blocks of 1,024 threads already hit the SM's hard 2,048-thread ceiling, so only two blocks can reside on the SM.

</details>

<details>
<summary>**9. How many banks and what bank width (32 banks x 4 bytes) does Shared Memory use on Hopper and Blackwell, and why does reading down a column of `__shared__ float tile[32][32]` cause a 32-way bank conflict?**</summary>

Shared memory has 32 banks that are each 4 bytes wide, so bank assignments repeat every 128 bytes. Reading down a column of `tile[32][32]`, thread `t` reads word `t * 32 + col`, which maps to bank `col` for every thread in the warp. All 32 threads hit the same bank at different addresses and serialize into 32 replays.

</details>

<details>
<summary>**10. Under what condition can all 32 threads in a warp access the same Shared-Memory (or Constant-Cache) bank in 1 cycle with zero conflict?**</summary>

When all threads in the warp read the exact same address with stride zero, such as `tile[0][0]`, the hardware broadcasts that word to all lanes in a single cycle with no conflict. The constant cache also broadcasts in about one cycle when all lanes read the same address.

</details>

<details>
<summary>**11. How does padding `__shared__ float tile[32][32]` to `tile[32][33]` eliminate bank conflicts, how much memory overhead does it add (~3.1% / 1 KB), and what zero-overhead alternative does CUTLASS use (XOR swizzling)?**</summary>

Padding changes the row stride from 32 to 33 words. Since 33 and 32 are coprime, thread `t` reading `tile[t][col]` hits bank `(t + col) % 32`, placing all 32 threads in distinct banks. The overhead is one extra float per row, and CUTLASS instead uses XOR swizzling (`col ^ row`) to permute banks with zero memory overhead.

</details>

<details>
<summary>**12. How does `__shfl_down_sync` perform a 32-thread warp reduction in 5 steps without using Shared Memory or `__syncthreads()`?**</summary>

Each butterfly step adds the value from the lane `offset` away using `__shfl_down_sync` across five halving offsets. Lanes read each other's registers directly, so lane zero ends up holding the sum of all threads in the warp with zero shared-memory bytes, zero barriers, and zero bank conflicts.

</details>

<details>
<summary>**13. How many bytes are in a modern GPU cache line (128 B) and in each sector (32 B), and how many sectors does a 32-thread warp touch for: (a) an aligned contiguous 4B load (4), (b) a +4B misaligned contiguous load (5), (c) a stride = 2 load (8), and (d) a scattered load (32)?**</summary>

A cache line is 128 bytes subdivided into four 32-byte sectors. A warp reading four-byte floats touches 4 sectors when aligned and contiguous, 5 sectors when shifted by four bytes, 8 sectors at stride two, and up to 32 sectors when scattered.

</details>

<details>
<summary>**14. Why does Structure of Arrays (SoA) achieve much higher Global Memory Load Efficiency than Array of Structures (AoS) when threads read a single field across records?**</summary>

With SoA each field has its own contiguous array, so adjacent threads read adjacent addresses and the warp fills whole cache lines. With AoS a single field is strided through memory, so the warp spans extra cache lines and fetches unneeded sectors.

</details>

<details>
<summary>**15. What minimum pointer alignment does `cudaMalloc()` guarantee (256 bytes), and how many bytes per thread and per warp are moved by `float4` (16 B/thread = 512 B/warp) on Hopper versus 256-bit (32 B/thread = 1,024 B/warp) vector loads on Blackwell (CUDA 13+)?**</summary>

The `cudaMalloc` allocator guarantees at least 256-byte base pointer alignment. A `float4` load moves 16 bytes per thread and 512 bytes per warp across four cache lines, cutting memory instructions fourfold. On Blackwell with CUDA 13+, a 256-bit load moves 32 bytes per thread and 1,024 bytes per warp across eight cache lines, cutting instructions eightfold.

</details>

<details>
<summary>**16. What does qualifying a read-only input pointer with `const __restrict__` allow the CUDA compiler and hardware to do, and how did it affect DRAM vs L2 throughput in Table 7-6?**</summary>

Adding `const __restrict__` or calling `__ldg()` proves the pointer is read-only and not aliased, routing loads through the read-only data cache path instead of coherent loads that pollute L1 and L2. In Table 7-6 this cut DRAM traffic from 600 to 200 GB/s, served 1,800 GB/s from L2, and sped up the kernel from 2.5 ms to 1.0 ms.

</details>

<details>
<summary>**17. How do the Tensor Memory Accelerator (TMA) and `cuda::memcpy_async` (`cuda::pipeline`) hide ~800-cycle HBM latency, and why does offloading copies to TMA help the SM's 16 LD/ST units?**</summary>

TMA is a dedicated DMA engine in the SM that copies multidimensional tiles between HBM and shared memory without using registers or load/store instruction slots. With two ping-pong shared buffers and `cuda::pipeline`, TMA streams the next tile in the background while warps compute on the current tile, hiding HBM latency and freeing the load/store units.

</details>

<details>
<summary>**18. Calculate the weight memory footprint (26 GB) and the unbatched decode weight-read latency floor (7.76 ms/token) for a 13B FP16 model on an 80 GB H100 (3,350 GB/s).**</summary>

Multiplying 13B parameters by two bytes equals 26.0 GB of weights, leaving 54.0 GB free on an 80 GB H100. Decode at batch one reads all weights per token, so dividing 26.0 GB by 3,350 GB/s gives about 7.76 ms per token. Extra free VRAM does not lower that floor; only higher bandwidth, lower-precision weights, or continuous batching does.

</details>

<details>
<summary>**19. Why are `cudaMallocAsync` and `cudaFreeAsync` (and PyTorch's `PYTORCH_ALLOC_CONF` caching allocator pool) strongly preferred over synchronous `cudaMalloc` and `cudaFree` inside loops?**</summary>

Standard `cudaMalloc` and `cudaFree` are synchronous across the whole device and invoke OS `mmap` and `ioctl` calls, stalling execution when called in a loop. The `cudaMallocAsync` and `cudaFreeAsync` calls are stream-ordered and draw from a configurable memory pool. PyTorch's caching allocator pools memory the same way, and `PYTORCH_ALLOC_CONF=expandable_segments:True` reduces fragmentation OOMs.

</details>

<details>
<summary>**20. What are the five `cudaMemAdvise` / `cudaMemPrefetchAsync` / `cudaStreamAttachMemAsync` calls used to prevent on-demand page-fault stalls with Unified Memory (`cudaMallocManaged`), and how do you verify Resizable BAR (BAR1) on a Linux GPU host?**</summary>

The five calls issued before kernel launch are `cudaMemAdvise` with `cudaMemAdviseSetPreferredLocation`, `cudaMemAdviseSetReadMostly`, and `cudaMemAdviseSetAccessedBy`, plus `cudaStreamAttachMemAsync` and `cudaMemPrefetchAsync`. To verify Resizable BAR, run `nvidia-smi -q -d MEMORY | grep -A 5 "BAR1"` and confirm BAR1 Total matches full VRAM rather than 256 MiB.

</details>

---

## Sources and review notes

### Sources read in full for this chapter

| Source | Chapters / files and key topics used |
|---|---|
| **Chris Fregly, *AI Systems Performance Engineering* (`ai-systems-performance-engineering`)** | **Ch. 6 (pp. 193–201):** Async memory allocation and pools (`cudaMallocAsync`, `cudaFreeAsync`, `cudaStreamNonBlocking`, `cudaMemPoolAttrReleaseThreshold`, `cudaMemPoolTrimTo`, `PYTORCH_ALLOC_CONF`, pp. 193–194); Blackwell 7-tier memory hierarchy (Table 6-5: Registers, Shared/L1 256 KB with 228 KB shared / 227 KB dynamic + 1 KB reserved and `cudaFuncAttributePreferredSharedMemoryCarveout`, Tensor Memory TMEM 256 KB/SM ~10 cycles for `tcgen05` / UMMA, Constant Cache ~8 KB fronting 64 KB, L2 Cache 126 MB on B200, Local Memory spill space in HBM, Global HBM3e 180–288 GB @ ~8 TB/s across 8 stacks on 2 dies linked at 10 TB/s, and 5 Points of Coherency, pp. 194–198); Unified Memory (`cudaMallocManaged`, NVLink-C2C 900 GB/s vs PCIe page faults, `cudaMemPrefetchAsync`, `cudaMemAdvise`, `cudaStreamAttachMemAsync`, pp. 198–201). |
| **Chris Fregly, *AI Systems Performance Engineering* (`ai-systems-performance-engineering`)** | **Ch. 7 (pp. 216–253):** Coalesced vs uncoalesced global memory access (128-byte cache lines = 4 x 32-byte sectors, misaligned 5–8 sectors, `stride=2` 8 sectors, AoS vs SoA, Table 7-1 4.8 ms → 1.3 ms = 3.7x, pp. 216–223); Vectorized memory access (`cudaMalloc` 256 B alignment, `float4` 16 B/thread = 512 B/warp on Hopper vs 32 B/thread = 1,024 B/warp `alignas(32)` on Blackwell CUDA 13+, pp. 223–226); Shared-memory tiling (32 x 32 tile 32x reuse, Table 7-4 15 → 170 GFLOPS = 11.3x, 64 x 64 tile register/thread budget, CUTLASS, `cuBLAS`, `cuDNN`, `cuTile` / `TileIR`, pp. 231–235); Shared-memory bank conflicts (32 banks x 4 B = 128 B, 1-cycle broadcast exception, `tile[32][32]` 32-way conflict vs `tile[32][33]` padding and XOR swizzling, Table 7-5 4.0 ms → 1.3 ms = 3.1x, pp. 235–241); Warp shuffle intrinsics (`__shfl_sync`, `__shfl_down_sync` butterfly reduction in registers, Cooperative Groups `__reduce_sync`, pp. 241–243); Read-only data caches (`const __restrict__`, `__ldg()`, texture/surface objects, Table 7-6 2.5 ms → 1.0 ms = 2.5x, pp. 243–246); Asynchronous memory prefetching with TMA (`cuda::memcpy_async`, `cuda::pipeline` ping-pong double buffering, `cp.async.bulk`, Table 7-7 18 ms → 7 ms = 2.6x, pp. 246–253). |
| **Migrated from `nvidia-devops`** | `nvidia-zero-to-hero/volume-02/chapter-05-gpu-memory-hierarchy.md`; `nvidia-zero-to-hero/volume-02/chapter-07-registers-shared-memory-and-local-memory.md` (`chapter-07-registers-shared-memory-and-local-memory.md`); `nvidia-zero-to-hero/volume-02/chapter-08-global-memory-l1-l2-and-hbm.md` (`chapter-08-global-memory-l1-l2-and-hbm.md`, including `16-byte` `float4` loads and `tile0`/`tile1` ping-pong staging); `nvidia-zero-to-hero/volume-02/chapter-09-divergence-coalescing-and-bottleneck-reasoning.md` (completed migration together with 10.2); `nvidia-zero-to-hero/volume-02/labs/lab-03-profile-memory-and-warp-efficiency.md` (completed migration together with 10.2); `volume-04/01-gpu-architecture-topology-masterclass.md` (Section 3 GPU Memory Mental Model, HBM vs GDDR, Pinned vs Pageable, BAR1 / Resizable BAR, and Appendix B Unified Memory & KV cache offload). |

### Mapped notes checked in the 2026-10-25 deep-read pass

These files are assigned to this chapter in `planning/MIGRATION_MAP.md`. The status of each file after the deep-read pass is listed in the table below.

| Mapped file | Disposition |
|---|---|
| `nvidia-zero-to-hero/volume-02/chapter-01-why-gpu-architecture-evolved.md` | Checked for numbers only; background already in 10.1 section 3. |
| `nvidia-zero-to-hero/volume-02/chapter-02-inside-a-modern-nvidia-gpu.md` | Not re-read in this pass; read earlier for 10.2, topic covered there. |
| `nvidia-zero-to-hero/volume-02/chapter-04-cuda-cores-tensor-cores-and-rt-cores.md` | Not re-read in this pass; read earlier for 10.4, topic covered there. |
| `nvidia-zero-to-hero/volume-02/chapter-06-scheduling-occupancy-and-instruction-dispatch.md` | Not re-read in this pass; read earlier for 10.2, topic covered there. |
| `nvidia-zero-to-hero/volume-02/chapter-10-gpu-topology-peer-access-and-data-paths.md` | Read in full; nothing new for this chapter, its NVLink-versus-SYS arithmetic and degraded-link example are already in 10.6. |
| `nvidia-zero-to-hero/volume-02/chapter-11-building-a-gpu-performance-model.md` | Read in full; nothing new for this chapter, roofline and bottleneck content is already in 10.5. |
| `nvidia-zero-to-hero/volume-02/chapter-12-volume-02-architecture-summary.md` | Read in full; nothing new for this chapter, symptom map and anti-patterns are already in 10.5. |
| `nvidia-zero-to-hero/volume-02/labs/lab-01-inspect-gpu-architecture-and-topology.md` | Read in part (the `lspci` versus `nvidia-smi` driver-init example only); not added, candidate for 10.8. |
| `nvidia-zero-to-hero/volume-02/labs/lab-02-inspect-gpu-engine-and-memory-behavior.md` | Read in full; nothing new for this chapter, the container and Container Toolkit parts belong to 10.9 and 10.8. |
| `nvidia-zero-to-hero/volume-02/labs/lab-04-build-a-topology-aware-gpu-placement-plan.md` | Read in part (the degraded NVLink example only); already in 10.6. |

### Run here
- Running `python3 -B code/part10/gpu_memory_hierarchy_lab.py` passes all 25 checks with 0 failures.

### My own choices and inferences, labelled in the text
- **Unified bank-conflict, sector-coalescing, and host-device memory auditor:** Combining the cache-line, sector, and bank modulo rules from *AI Systems Performance Engineering* with the BAR1 Resizable BAR check and `cudaMallocAsync` and `cudaMemPrefetchAsync` checks into deterministic Python validators is my inference. Those validators are `calc_shared_mem_bank_conflict`, `calc_warp_coalescing_and_vector_loads`, and `audit_host_device_memory_config` in `code/part10/gpu_memory_hierarchy.py`.

### Not verified on live hardware
- The commands `nvidia-smi -q -d MEMORY`, `nvidia-smi dmon -s ucm`, `nvcc -O3 -Xptxas=-v`, and `ncu` counter queries were not executed on a live GPU VM in this authoring environment.

