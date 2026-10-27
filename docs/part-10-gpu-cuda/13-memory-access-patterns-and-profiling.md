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

An engineering team buys modern GPUs with massive high-bandwidth memory. Yet their custom CUDA and PyTorch kernels run at a small fraction of peak speed. Tensor Cores sit idle while warps wait hundreds of clock cycles for data from off-chip memory. The hardware has plenty of raw bandwidth, but the software wastes most of every memory transaction.

A single NVIDIA Blackwell B200 GPU delivers massive HBM3e bandwidth, and a dual-GPU Grace Blackwell Superchip doubles that capacity. Yet a kernel that reads memory with a small element stride wastes three-quarters of that bandwidth. It achieves only a quarter of peak DRAM throughput because the hardware must fetch whole cache sectors. Threads only use a few bytes from each fetched sector and discard the rest.

Even when global memory reads are contiguous, five other memory-access flaws routinely starve Streaming Multiprocessors and stall AI workloads.

First, threads often issue narrow scalar loads instead of wide vector loads. Narrow loads multiply instruction counts by four or eight times and leave memory request queues congested. Packing contiguous values into wider vector loads cuts instruction pressure and raises global load efficiency.

Second, naive matrix and attention kernels repeatedly read the same inputs directly from off-chip HBM. Staging reusable tiles in fast on-chip shared memory cuts off-chip sector traffic by more than eightfold. Arithmetic intensity rises and compute throughput jumps by more than an order of magnitude.

Third, threads reading down a column of a shared-memory tile can collide on the exact same memory bank. When all threads in a warp hit different addresses in the same bank, the hardware replays the access in series. Adding a single padding column or swizzling indices eliminates those bank conflicts and triples kernel speed.

Fourth, using shared memory to sum values inside a single warp wastes on-chip capacity and requires explicit synchronization barriers. Warp shuffle instructions let lanes read each other's registers directly in a few butterfly steps. This register exchange uses zero shared memory and causes zero bank conflicts.

Fifth, omitting read-only pointer qualifiers and waiting synchronously on long HBM loads leave Streaming Multiprocessors stalled. Qualifying immutable lookup tables routes reads through the L1 read-only cache. Double-buffering tiles with the Tensor Memory Accelerator overlaps off-chip transfers with on-chip computation.

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

A caution about the source book's metric tables is needed before we dive in. The book states that the numeric values in its Nsight Compute tables are illustrative examples designed to explain the concepts. None of these tables were rerun on live hardware for this handbook. The same DRAM throughput shift appears in three different tables, and the scalar baseline in the vectorization table shows scattered sectors. Treat these tables as representative examples that show direction and rough magnitude rather than exact hardware benchmarks.

In this chapter, we examine all seven memory-access optimization and Nsight Compute profiling techniques. Each section includes CUDA C++ and PyTorch patterns, hardware counter tables, and a deterministic verification lab.

:::tip In one minute
- **Global memory coalescing:** A modern NVIDIA GPU services global memory in 128-byte cache lines divided into four 32-byte sectors. When all threads in a warp read contiguous floats from an aligned address, hardware merges all reads into one cache line. Strided access touches many more sectors per request and wastes most of the fetched bytes.
- **Vectorized global loads:** Device pointers from `cudaMalloc` are aligned to at least 256 bytes. Packing four floats into `float4` on Hopper or eight floats into `float8` on Blackwell issues a single wide vector load per thread. This cuts load instructions by fourfold or eightfold.
- **Shared-memory tiling and bank padding:** Staging square tiles in shared memory reuses each global load dozens of times and boosts matrix multiply throughput more than elevenfold. Adding one padding column to a shared array shifts column reads across all banks and eliminates bank conflicts.
- **Warp shuffles, read-only caches, and TMA:** Intra-warp reductions use `__shfl_down_sync` to sum lanes directly in registers in five steps. Adding `const __restrict__` routes immutable tables through the L1 read-only cache. Double-buffering tiles with the Tensor Memory Accelerator hides long DRAM latency behind computation.
:::

---

## Prerequisites and outcomes

**Prerequisites:** Review SIMT warps, the GPU memory hierarchy, Tensor Cores, and Roofline arithmetic intensity in earlier Part 10 chapters. You should also be comfortable with CUDA kernel indexing and asynchronous streams.

**Outcomes:** After completing this chapter, you will be able to perform four core optimization tasks.
1. Calculate the exact cache lines and sectors touched by aligned, misaligned, strided, and scattered warp loads. You will also convert Array of Structures layouts into Structure of Arrays layouts and interpret Nsight Compute load efficiency counters.
2. Implement 16-byte `float4` and Blackwell 32-byte `float8` vectorized loads while preserving pointer alignment across element offsets.
3. Design shared-memory tiled kernels and budget per-block registers against Streaming Multiprocessor hardware limits. You will also eliminate bank conflicts using column padding or XOR index swizzling.
4. Replace shared-memory intra-warp reductions with `__shfl_down_sync` register butterfly reductions and route immutable lookup tables through the read-only data cache. Finally, you will hide DRAM latency with Tensor Memory Accelerator double buffering.

---

## 1. Coalesced vs. Uncoalesced Global Memory Access

A developer writes a kernel where each thread processes every second or fourth element of an array. Another kernel reads one field from an array of C++ structures. Both kernels perform very little math, yet they run nearly four times slower than a simple contiguous copy. Nsight Compute reports that three-quarters of the bytes transferred across the HBM bus are thrown away before reaching the registers.

### 1.1 How the GPU memory controller services a 32-thread warp load

When the threads in a warp execute a global-memory load instruction, the load/store units do not fetch individual floats in isolation. Instead, the hardware memory coalescer groups the addresses across the warp. Modern NVIDIA GPUs service global memory through 128-byte cache lines, and each cache line is divided into four 32-byte sectors.

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

Four access patterns determine how many sectors the memory controller must fetch for a single warp load.

In the first pattern, all lanes read contiguous 4-byte floats starting at a 128-byte-aligned address. The lanes request 128 contiguous bytes that map to one cache line and four sectors. Every byte fetched from memory is used by a thread. This layout gives an optimal four sectors per request and full theoretical load efficiency.

In the second pattern, the warp reads contiguous floats, but the starting address is shifted by four bytes. The request span now crosses a cache-line boundary and straddles two cache lines. The memory controller must fetch four sectors from the first line plus one sector from the second line. Depending on the caching policy, hardware fetches five to eight sectors per request.

In the third pattern, threads read with a stride of two floats so adjacent lanes sit eight bytes apart. The warp spans two cache lines and touches eight sectors, throwing away half of every sector fetched. In PyTorch, calling `torch.index_select` with a strided index launches a gather kernel with this exact uncoalesced pattern. Using `inp.clone()` or `torch.compile` performs a contiguous copy instead.

In the fourth pattern, threads read with a stride of eight or more floats so adjacent lanes sit at least 32 bytes apart. Every thread in the warp lands in a different sector at the L2 cache. The memory controller must fetch 32 sectors just to deliver 128 useful bytes, which drops load efficiency to an eighth of peak.

```text
Warp Global Memory Sector Math (32 threads x 4-byte FP32 = 128 useful bytes; analyze_warp_global_memory_access):
  - Aligned stride = 1 (offset 0 B, bytes 0..127):     1 cache line (128 B)  |  4.0 sectors (128 B fetched)   | 128 / 128   = 100.0% efficiency (99% in Table 7-1)
  - Misaligned stride = 1 (offset +4 B, bytes 4..131): 2 cache lines         |  5.0 sectors (160 B fetched)   | 128 / 160   =  80.0% efficiency (up to 8 sectors)
  - Strided stride = 2 (in[idx * 2], N = 1,048,576):   2 cache lines (256 B) |  8.0 sectors (256 B fetched)   | 128 / 256   =  50.0% theoretical (23% in Table 7-1)
  - Scattered stride >= 8 (>= 32 B between threads):   8+ cache lines        | 32.0 sectors (1,024 B fetched) | 128 / 1,024 =  12.5% theoretical efficiency
```

### 1.2 Array of Structures vs. Structure of Arrays and Nsight Compute Table 7-1

In C++ code, uncoalesced strided access most commonly comes from storing records as an Array of Structures instead of a Structure of Arrays. When a structure holds four floats in an array, adjacent structures sit 16 bytes apart. If all threads in a warp read only the first field, they access memory with a stride of four floats. That pattern wastes three-quarters of every fetched sector.

Converting the layout to a Structure of Arrays stores all first coordinates in one contiguous array. Separate contiguous arrays hold the remaining coordinates. When all threads in a warp read the first coordinate array, all lanes read contiguous floats in a single cache line.

| Nsight Compute Metric | Before (`uncoalescedCopy`, `stride = 2`) | After (`coalescedCopy`, `stride = 1`) | Improvement Factor (*ASP* Ch 7 Table 7-1, p. 220) |
|---|---:|---:|---|
| **DRAM Throughput (`% of peak`)** | `25%` | **`90%`** | **`3.6x` higher** |
| **Global Memory Load Efficiency** | `23%` | **`99%`** | **`4.3x` higher** (`100%` theoretical useful bytes) |
| **Average Sectors per Request** | `8.0` | **`4.0` (optimal)** | **`2.0x` fewer sectors** per warp request |
| **SM Active `%`** | `62%` | **`99%`** | SMs stay active instead of stalling on DRAM |
| **Kernel Execution Time (`ms`)** | `4.8 ms` | **`1.3 ms`** | **`3.7x` faster** (`N = 1 << 20 = 1,048,576`) |

**Always organize multi-field GPU buffers as a Structure of Arrays so that adjacent threads in a warp read contiguous addresses with a stride of one.** Before optimizing any arithmetic inside a kernel, inspect Nsight Compute's `Average Sectors per Request` counter. Verify that scalar float loads achieve four sectors per request.

---

## 2. Vectorized Global Memory Access

Even when a scalar float kernel is fully coalesced at four sectors per request, each thread still issues a narrow 4-byte load instruction. Issuing four or eight times as many memory instructions as necessary congests the instruction pipeline. It can also leave load efficiency low when accesses are unaligned or scattered.

### 2.1 Coalescing vs. vectorizing and `cudaMalloc` 256-byte alignment

Coalescing is an inter-thread property across the lanes of a warp. Vectorizing is an intra-thread property within each individual thread. Vectorized memory access packs four or eight contiguous floats into a single wider load or store instruction per thread.

| Vector Type & Architecture | Bytes per Thread | PTX Instruction Emitted by `nvcc` | Required Pointer Alignment | Bytes Moved per Warp (`32` lanes) | `128 B` Cache Lines per Warp | `32 B` Sectors per Warp | Sectors per `128 B` Line |
|---|---:|---|---:|---:|---:|---:|---:|
| **Scalar `float`** (All GPUs) | `4 B` (`1` float) | `ld.global.f32` / `st.global.f32` | `4 B` | `128 B` | `1` line | `4` sectors | `4.0` (if `128 B` aligned) |
| **`float4` (`128-bit`)** (Hopper `sm_90` & earlier) | **`16 B` (`4` floats)** | **`ld.global.v4.f32` / `st.global.v4.f32`** | **`16 B`** (`alignof(float4) == 16`) | **`512 B`** | **`4` lines** | **`16` sectors** | **`4.0` per line** (`4x` fewer load instructions) |
| **`alignas(32) float8` (`256-bit`)** (Blackwell `sm_100`, CUDA 13+) | **`32 B` (`8` floats)** | **`ld.global.v8.f32` / `st.global.v8.f32`** | **`32 B`** (`alignas(32)`) | **`1,024 B`** | **`8` lines** | **`32` sectors** | **`4.0` per line** (`8x` fewer load instructions) |

Two hardware alignment rules govern vectorized global loads. First, every device pointer returned by `cudaMalloc` is guaranteed to be aligned to at least 256 bytes. That base alignment automatically satisfies both 16-byte `float4` alignment and 32-byte `float8` alignment at offset zero.

However, if a kernel adds an element offset to a base pointer and casts the sum to a vector pointer, the byte offset must remain aligned. For 16-byte `float4` loads, the element offset must be a multiple of four floats. For 32-byte `float8` loads on Blackwell, the element offset must be a multiple of eight floats. A misaligned cast forfeits vectorization and triggers an address fault.

Second, maximum vector width doubled on Blackwell with CUDA 13. On Hopper and earlier architectures, global vector loads top out at 16 bytes per thread using `ld.global.v4.f32`. An eight-float structure on Hopper compiles into two 16-byte loads. On Blackwell with CUDA 13 and a 32-byte-aligned structure, the compiler emits a single 32-byte `ld.global.v8.f32` instruction. That single instruction moves 1,024 bytes per warp across eight cache lines.

### 2.2 Nsight Compute Table 7-2: Scalar vs. Vectorized Copy

Comparing a scalar copy kernel against a 16-byte `float4` vectorized copy kernel shows how wide loads reduce instruction overhead and improve bus utilization.

| Nsight Compute Metric | Before (`copyScalar`) | After (`copyVector16B` / `float4`) | Improvement Factor (*ASP* Ch 7 Table 7-2, p. 225) |
|---|---:|---:|---|
| **Global Memory Load Efficiency** | `28%` | **`97%`** | **`~3.5x` higher** |
| **Average Sectors per Request** | `31.8` | **`4.0` (per `128 B` line)** | Eliminates scattered sector waste |
| **DRAM Throughput (`% of peak`)** | `25%` | **`90%`** | **`3.6x` higher** |
| **Kernel Execution Time (`ms`)** | `4.2 ms` | **`1.2 ms`** | **`3.5x` faster** (`4.2 / 1.2 = 3.5x`, `N4 = N / 4`) |

**When writing bandwidth-bound elementwise or copy kernels, cast aligned pointers to `float4` on Hopper or `alignas(32) float8` on Blackwell.** This allows each thread to load 16 or 32 bytes per instruction. Always verify that any interior element offset is divisible by four or eight floats before casting.

---

## 3. Shared-Memory Tiling and Eliminating Bank Conflicts

Coalescing and vectorizing make every trip to off-chip HBM efficient, but they do not reduce how many times the kernel goes out to HBM. In a naive matrix multiplication, every thread loops across an entire row and column and reads inputs directly from global memory. Each matrix element is fetched from off-chip HBM a thousand times, saturating the DRAM bus with redundant reads.

### 3.1 Tiling matrix multiplication in shared memory

Shared-memory tiling partitions the input matrices into square tiles stored in fast on-chip SRAM arrays. First, all threads in the thread block cooperatively load one float of each input tile from HBM using coalesced warp reads. Second, the block executes `__syncthreads()` to ensure the entire tile is resident in shared memory before any thread reads it.

Third, every thread loops across the elements of the cached tile and accumulates products from fast on-chip shared memory instead of slow off-chip HBM. Each global memory load is reused 32 times on chip. Fourth, the block calls `__syncthreads()` a second time before advancing to load the next tile. This second barrier prevents faster threads from overwriting the shared buffer while slower threads are still reading it.

| Nsight Compute Metric | Before (`naiveMatMul`) | After (`tiledMatMul` `32 × 32`) | Architectural Interpretation (*ASP* Ch 7 Table 7-4, pp. 230–231) |
|---|---:|---:|---|
| **Global Memory Load Sectors** | `9,800` | **`1,200`** | **`8.17x` (`~8x`) reduction** in 32-byte HBM sector reads from `32x` reuse |
| **DRAM Throughput (`% of peak`)** | `90%` (wasteful) | **`25%` (`3.6x` less)** | Desirable drop because redundant HBM traffic was removed (`10 GB/s -> 21 GB/s`) |
| **Arithmetic Intensity (`FLOPs/byte`)** | `1.5 FLOPs/byte` | **`8.0 FLOPs/byte`** | Shifts the kernel right along the Roofline toward compute-bound |
| **Achieved Occupancy (`%`)** | `42%` | **`89%`** | Fewer HBM stalls allow resident warps to make continuous progress |
| **Shared Memory Throughput (`% of peak`)** | `52%` | **`99%`** | Traffic shifted from off-chip HBM onto conflict-free on-chip SRAM |
| **Sustained FP32 Throughput (`GFLOPS`)** | `15 GFLOPS` | **`170 GFLOPS`** | **`~11.3x` (`~11x`) higher** compute throughput on `N = 1,024` |

### 3.2 Why you cannot blindly grow tiles forever: The `64 × 64` register budget

If a 32 by 32 tile speeds up matrix multiplication elevenfold, it is tempting to double the tile size again. However, growing the tile size increases per-thread register pressure and shared-memory consumption. That extra resource usage can cut the number of blocks that fit on each Streaming Multiprocessor.

Consider a 1,024-thread block computing a 64 by 64 output tile so that each thread computes a 2 by 2 subtile of four outputs. Each input tile consumes 16 KB of shared memory, or 32 KB for both input tiles. That footprint easily fits inside a Blackwell SM's usable shared memory. The binding constraint is the register file and the thread hardware limit per SM.

In the minimal register case, the register file could hold five blocks by registers alone, but the SM thread ceiling caps residency at two blocks per SM. In a double-buffered case using more registers per thread, each block consumes more registers, which still fits two blocks per SM. If register usage climbs above 32 registers per thread on a 1,024-thread block, residency drops to a single block per SM. Even worse, excessive register demand spills registers to slow local memory in HBM.

```text
64 x 64 FP32 Tile Shared-Memory and Register Residency Budget (ASP Ch 7 pp. 231-232; calc_tile_residency_and_register_budget):
  - Shared Memory Footprint:      64 x 64 x 4 B = 16,384 bytes (16 KB) per matrix tile; sA + sB = 32 KB/block (fits <= 7 blocks in 227 KB usable SMEM on 228 KB Blackwell SM)
  - Per-Thread Register Split:    Book range is ~12 to 22 regs/thread (handbook illustration for 12 regs: 4 accumulators + 2 A-tile + 2 B-tile + 4 index/loop = 12 regs/thread)
  - Minimal Case (12 regs/thread): 12 x 1,024 threads = 12,288 regs/block -> 65,536 // 12,288 = 5 blocks (61,440 regs), capped by 2,048 max threads/SM (64 warps) at 2 blocks/SM
  - Larger Case (22 regs/thread):  22 x 1,024 threads = 22,528 regs/block -> 65,536 // 22,528 = 2 blocks/SM (45,056 regs, 2,048 resident threads)
  - Register Ceiling Drop (>32):   > 32 regs/thread on 1,024 threads exceeds 32,768 regs/block -> drops residency to 1 block/SM (1,024 threads = 50% occupancy) or spills to HBM (max 255 regs/thread)
```

### 3.3 Shared-memory bank conflicts and `+1` column padding

Storing data in on-chip shared memory is only fast when all threads in a warp access distinct memory banks. Shared memory is divided into 32 independent banks of 4-byte width. Successive 4-byte words map to successive banks and wrap back to the first bank every 128 bytes.

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

Three hardware rules govern how bank conflicts arise and how to eliminate them.

First, reading down a column of an unpadded 32 by 32 shared array during a matrix transpose causes a worst-case 32-way bank conflict. Because each row has 32 floats, adjacent lanes reading down a column step by 32 words per thread. Modulo 32, every single thread in the warp maps to the exact same bank. That collision forces hardware to replay the memory instruction 32 times in series.

Second, reading the exact same shared-memory address across multiple threads never causes a bank conflict. When all threads in a warp read the same element with identical indices, the shared-memory crossbar performs a single-cycle hardware broadcast. Bank conflicts only happen when multiple threads in a warp access different addresses within the same bank.

Third, adding one padding column or applying XOR index swizzling eliminates column bank conflicts completely. Declaring `__shared__ float tile[32][33]` adds one unused float per row and changes the row stride from 32 words to 33 words. Because 33 is coprime to 32, lanes reading down a column map across 32 distinct banks with only about three percent memory overhead. Libraries such as CUTLASS achieve the same conflict-free spread with zero extra memory by XOR-swizzling the column index with the row index.

```text
Shared-Memory Bank Modulo Math (32 banks x 4-byte width = 128-byte wrap; analyze_shared_memory_bank_conflicts):
  - Row-Major Access (tile[row][lane], stride = 1 word):      Bank = (row * 32 + lane) mod 32 = lane mod 32 -> 32 distinct banks (1-way, 0 bank conflicts)
  - Unpadded Column Read (tile[lane][col] on tile[32][32]):   Bank = (lane * 32 + col) mod 32 = col mod 32  -> all 32 lanes hit Bank col (32-way conflict!)
  - Padded Column Read (tile[lane][col] on tile[32][33]):     Bank = (lane * 33 + col) mod 32 = (lane + col) mod 32 -> 32 distinct banks (0 conflicts; 1/32 = 3.125% ~ 3% / 128 B overhead on 4 KB tile)
  - Uniform Broadcast (tile[const_r][const_c] across 32 lanes): Same address across all lanes -> hardware single-cycle broadcast (0 bank conflicts)
```

| Nsight Compute Metric | Before (`tile[32][32]`, no padding) | After (`tile[32][33]`, `+1` padding) | Improvement (*ASP* Ch 7 Table 7-5, p. 237) |
|---|---:|---:|---|
| **Shared-Memory Load Bank Conflicts** | `4.8 million` | **`0`** | **100% eliminated** |
| **Shared-Memory Utilization (`% of peak`)** | `52%` | **`100%`** | Full 32-bank parallel throughput |
| **Warp Stall Fraction (`memory`)** | `38%` | **`0.5%`** | Eliminates shared-memory replay stalls |
| **Kernel Execution Time (`ms`)** | `4.0 ms` (`4 ms`) | **`1.3 ms`** | **`~3x` faster** (`N = 1,024` transpose) |

**Whenever a kernel reads columns of a 32-wide shared-memory tile, pad the inner dimension to 33 elements or XOR-swizzle the column index.** This ensures every lane in the warp hits a distinct bank. Check `l1tex__data_bank_conflicts_pipe_lsu_mem_shared_op_ld.sum` in Nsight Compute to confirm that shared-memory bank conflicts drop to zero.

---

## 4. Warp Shuffle Intrinsics, Read-Only Caches, and TMA Prefetching

Even after coalescing global accesses and padding shared-memory tiles, kernels still lose performance in three common situations. Warps waste shared memory and barrier cycles on intra-warp reductions. Lookup tables thrash the L1 data cache because the compiler cannot prove they are read-only. Finally, Streaming Multiprocessors stall for hundreds of cycles waiting on synchronous DRAM loads.

### 4.1 Intra-warp register reductions with `__shfl_down_sync`

When threads within the same warp need to exchange values or compute a sum or maximum for softmax, using shared memory is unnecessary. Writing partial values to shared memory consumes scarce on-chip SRAM. It also forces warps to wait at `__syncthreads()` barriers.

CUDA warp shuffle intrinsics such as `__shfl_sync`, `__shfl_down_sync`, and `__shfl_xor_sync` let threads read each other's registers directly across the warp. A butterfly reduction using `__shfl_down_sync` steps through five halving offsets. After five register-to-register steps, the first lane holds the sum of all 32 lanes with zero shared memory and zero bank conflicts.

```cpp
// Warp-level butterfly reduction in registers (0 bytes of Shared Memory, 0 bank conflicts)
unsigned mask = __activemask();
float val = threadVal; // Each of the 32 lanes starts with its private partial sum
for (int offset = 16; offset > 0; offset >>= 1) {
    val += __shfl_down_sync(mask, val, offset);
}
// After 5 register steps (offsets 16 -> 8 -> 4 -> 2 -> 1), Lane 0 holds the sum of all 32 lanes (1..32 -> 528.0)
```

Keep the hardware scope boundary in mind when using warp shuffles. A warp shuffle can only exchange registers among the 32 lanes of a single warp. Reducing across multiple warps in a thread block still requires a small shared-memory scratchpad or Cooperative Groups barriers such as `thread_group.shuffle()` and `__reduce_sync()`.

### 4.2 Routing immutable lookup tables through the read-only data cache

Inference kernels frequently perform random gather lookups into immutable tables such as token embeddings or quantization scale factors. CUDA provides a 64 KB `__constant__` memory space backed by a small per-SM constant cache. However, that space is too small for large model tables and only runs at full speed when all threads in a warp read the exact same address.

For larger lookup tables, the GPU's L1 read-only data cache can serve scattered reads without polluting the regular read/write cache lines. However, the compiler will only emit read-only `__ldg()` loads automatically if it can prove that the table pointer is never written and never aliases another pointer. Adding `const __restrict__` to the input pointer gives the compiler that guarantee and cuts off-chip DRAM traffic by three times.

| Nsight Compute Metric | Before (`const float* table`, no `__restrict__`) | After (`const float* __restrict__ table`) | Improvement (*ASP* Ch 7 Table 7-6, p. 243) |
|---|---:|---:|---|
| **Global Memory Load Efficiency** | `52%` | **`97%`** | Most fetched cache lines carry useful data |
| **DRAM Throughput (`GB/s`)** | `600 GB/s` | **`200 GB/s`** | **`3.0x` less off-chip DRAM traffic** |
| **L2 Read Throughput (`GB/s`)** | `1,500 GB/s` | **`1,800 GB/s`** | Lookups served from on-chip cache hierarchy |
| **SM Active `%`** | `45%` | **`93%`** | Nearly every cycle has active work |
| **Kernel Execution Time (`ms`)** | `2.5 ms` | **`1.0 ms`** | **`2.5x` faster** (`T = 1,024`, `N = 1 << 20`) |

For spatial interpolation workloads, CUDA also provides `cudaTextureObject_t` with `tex1Dfetch` and `tex2D` alongside surface objects. Legacy texture references are deprecated. For standard one-dimensional AI tensors and embedding tables, qualifying pointers with `const __restrict__` is the clean and portable solution.

### 4.3 Hiding 800-cycle DRAM latency with TMA double buffering

Even a coalesced, vectorized load still faces an approximately 800-cycle HBM round-trip latency on Hopper and Blackwell GPUs. When warps issue synchronous global-to-shared loads using their own load/store units and block until the data arrives, Streaming Multiprocessors sit idle during the memory transit time.

On Hopper and Blackwell, the Tensor Memory Accelerator (`cp.async.bulk.*`) offloads bulk tile transfers between global HBM and shared memory onto a dedicated hardware DMA engine. Pairing the Tensor Memory Accelerator with the `libcu++` `<cuda/pipeline>` API and two ping-pong shared buffers lets the block prime the first tile. Warps then overlap asynchronous prefetching of the next tile while computing on the current tile.

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

| Nsight Compute Metric | Before (No Prefetch) | After (`TMA` + `cuda::memcpy_async` Double Buffering) | Improvement (*ASP* Ch 7 Table 7-7, pp. 248–249) |
|---|---:|---:|---|
| **Global Memory Load Efficiency** | `23%` | **`99%`** | **`4.3x` higher** |
| **Average Sectors per Request** | `6.4` | **`4.0` (optimal)** | Coalesced 128-byte TMA bulk transfers |
| **DRAM Throughput (`% of peak`)** | `25%` | **`90%`** | **`3.6x` higher** sustained HBM utilization |
| **SM Active `%`** | `62%` | **`100%`** | Warps compute continuously while TMA fetches next tile |
| **Kernel Execution Time (`ms`)** | `18 ms` | **`7 ms`** | **`~2.6x` faster** (hides `~800-cycle` DRAM latency) |

**Use `__shfl_down_sync` for intra-warp reductions and mark read-only lookup pointers `const __restrict__`.** In multi-tile loops, double-buffer tile loads with `cuda::memcpy_async` so warps never stall waiting on synchronous DRAM loads.

---

## 5. Commands and Profiling Workflows That Matter

Without hardware performance counters, developers guess at whether a slow kernel is suffering from uncoalesced global reads, shared-memory bank conflicts, or synchronous DRAM stalls. Compiling with line-table information and querying key Nsight Compute metrics isolates the exact memory bottleneck in seconds.

All Nsight Compute and compilation commands below follow *AI Systems Performance Engineering* Chapter 7. Because this handbook builds without an attached GPU, `nvcc` and `ncu` commands are marked **(untested here)**.

### 5.1 Profile global coalescing, sector counts, and shared-memory bank conflicts with `ncu` (untested here)

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

**Always compile profiling builds with `-lineinfo` so Nsight Compute attributes sector waste and bank conflicts directly to the offending C++ source line.**

---

## 6. How It Fails: Six Production Memory-Access and Profiling Failure Modes

When a production kernel misses its latency or throughput target, Nsight Compute counters immediately reveal which of the six memory-access failure modes is responsible.

| # | Failure Mode | Nsight Compute Symptom | Root Cause | Fix |
|---|---|---|---|---|
| **1** | **Strided / `AoS` / `index_select` uncoalesced global loads** | `DRAM Throughput = 25%`, `Global Memory Load Efficiency = 23%`, `Average Sectors per Request = 8.0` (up to `32.0`), runtime `4.8 ms` (Table 7-1) | Adjacent threads in a warp index memory with `stride > 1` (`in[idx * 2]`, `AoS` structs, or `torch.index_select` gather), touching multiple 128-byte cache lines per warp | Restructure layout to Structure of Arrays (`SoA`) and contiguous `stride = 1` (`in[idx]`), reducing sectors/request to `4.0` (`1.3 ms`, `3.7x` faster) |
| **2** | **Scalar loads or misaligned `float4` / `float8` casts** | `Global Memory Load Efficiency = 28%`, `Average Sectors per Request = 31.8`, or `cudaErrorMisalignedAddress` crash (Table 7-2 & p. 223) | Kernel issues 4-byte scalar loads instead of wide vector loads, or casts `d_ptr + offset` to `float4*` / `float8*` when `offset` is not a multiple of `16 B` (`4` floats) or `32 B` (`8` floats) | Use `float4` (`16 B`, `ld.global.v4.f32`) on Hopper or `alignas(32) float8` (`32 B`, `ld.global.v8.f32`) on Blackwell (CUDA 13+), ensuring `offset % 4 == 0` or `offset % 8 == 0` (`1.2 ms`, `3.5x` faster) |
| **3** | **Redundant HBM loads in untiled GEMM / attention kernels** | `DRAM Throughput = 90%`, `Global Load Sectors = 9,800`, `Achieved Occupancy = 42%`, compute stuck at `15 GFLOPS` (`1.5 FLOPs/byte`, Table 7-4) | Inner loop reads `A[row, k]` and `B[k, col]` directly from global HBM on every step (`N` redundant loads per element) | Stage `32 × 32` tiles in `__shared__` memory with `__syncthreads()`, cutting global load sectors to `1,200` and raising throughput to `170 GFLOPS` (`~11x`) |
| **4** | **Oversized tile (`64 × 64`+) exhausting registers per SM** | Increasing tile size reduces achieved occupancy below `50%` or triggers local-memory register spills (`100s–1,000` cycles) | A `1,024`-thread block using `> 32` registers/thread exceeds half of the SM's `65,536`-register file, dropping residency from `2` blocks (`2,048` threads) to `1` block (pp. 231–232) | Balance tile size (`32 × 32` vs `64 × 64`) against `65,536` regs/SM and `227 KB` usable SMEM using `ncu` occupancy reports or `CUTLASS` / `cuTile` autotuners |
| **5** | **32-way Shared-Memory Bank Conflicts on column reads (`tile[32][32]`)** | `Shared-Memory Load Bank Conflicts = 4.8 million`, `Shared-Memory Utilization = 52%`, `Warp Stall Fraction (memory) = 38%`, runtime `4.0 ms` (Table 7-5) | Reading down a column of `__shared__ float tile[32][32]` strides by `32 floats = 128 B`, mapping all 32 lanes to `Bank 0` (`32`-way serialization) | Pad shared array to `__shared__ float tile[32][33]` (`+1` column = `~3%` / `1 KB` overhead) or apply XOR index swizzling, dropping conflicts to `0` (`1.3 ms`, `3x` faster) |
| **6** | **Missing `const __restrict__` on read-only tables or unpipelined `800-cycle` DRAM loads** | High DRAM traffic (`600 GB/s`) and low `SM Active = 45%` on lookup tables (Table 7-6), or warps stalled waiting on synchronous global-to-shared loads (`18 ms`, Table 7-7) | Compiler cannot prove table immutability/non-aliasing without `const __restrict__`, and SM `LD/ST` units stall on 800-cycle HBM round trips | Mark immutable tables `const __restrict__` (`2.5 ms -> 1.0 ms`), use `__shfl_down_sync` for intra-warp reductions, and double-buffer tile loads with `TMA` (`cuda::memcpy_async` + `cuda::pipeline`, `18 ms -> 7 ms`) |

**Treat every Nsight Compute counter as a pointer to a specific hardware unit.** Sector counts diagnose global coalescing, bank conflict counters diagnose shared memory layout, and DRAM versus L2 throughput diagnoses read-only caching.

---

## 7. Hands-On Lab: Verify Coalescing Sector Math, Vectorized Loads, Shared-Memory Tiling, Bank Padding, and Warp Shuffles

**Venue:** Any Linux machine or Nebius GPU VM with Python 3.10+. This lab runs deterministically using standard library Python. All `nvcc` and `ncu` commands are provided in Section 5 and marked `(untested here)`.

Run `code/part10/memory_access_patterns_lab.py` to execute all checks.

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

1. **Warp sector and cache-line math across strides:** Using `analyze_warp_global_memory_access()`, calculate how many cache lines and sectors a warp touches when reading floats under four patterns. Evaluate an aligned contiguous read, a contiguous read offset by four bytes, a stride of two, and a stride of eight. Report the theoretical Global Memory Load Efficiency for each case.
2. **Vectorized `float4` vs. Blackwell `float8` warp transactions:** For a single warp, calculate the total bytes moved per instruction, the number of cache lines, the number of sectors, and the PTX instruction emitted when using `float4` on Hopper versus `alignas(32) float8` on Blackwell. Then explain why casting an unaligned interior pointer offset fails even though `cudaMalloc` returned a 256-byte-aligned base pointer.
3. **Shared-memory tiling and register residency:** Using the numbers from *AI Systems Performance Engineering* Chapter 7, state the global load sector reduction, arithmetic intensity shift, and GFLOPS speedup achieved by 32 by 32 shared-memory tiling. Next, calculate the shared-memory footprint and total registers per block for a 64 by 64 tile using minimal registers versus double-buffered registers on a Blackwell SM.
4. **Shared-memory bank conflict math:** Prove mathematically using modulo arithmetic why reading down column zero across all lanes causes every thread to hit the first bank when the row stride is 32 floats. Then prove why adding one padding column maps all lanes to distinct banks with about three percent memory overhead.
5. **Warp shuffle vs. shared-memory reduction:** Trace the five butterfly iterations of `__shfl_down_sync` for a warp where each lane starts with its one-based lane number and verify the final sum in the first lane. Explain why this pattern cannot reduce across two different warps without shared memory or cluster barriers.
6. **Read-only cache and TMA double-buffering:** Compare the Nsight Compute metrics from the read-only cache and TMA tables in *AI Systems Performance Engineering* Chapter 7. Then write the four-method `cuda::pipeline` stage sequence (`producer_acquire`, `producer_commit`, `consumer_wait`, `consumer_release`) that overlaps TMA tile prefetching with tile computation.

---

## Checkpoint questions (20)

<details>
<summary>`&lt;strong>`1. How many bytes are in a modern NVIDIA GPU global-memory cache line, how many sectors does it contain, and what is the optimal `Average Sectors per Request` in Nsight Compute for a coalesced scalar warp load?`&lt;/strong>`</summary>

A global-memory cache line is 128 bytes and is divided into four 32-byte sectors. When all threads in a warp read contiguous, aligned 4-byte floats, the entire warp request maps to one cache line and four sectors per request.
</details>

<details>
<summary>`&lt;strong>`2. What happens to sector and cache-line counts when a warp reads contiguous floats starting at an address that is not aligned to a cache line?`&lt;/strong>`</summary>

The warp span crosses a cache-line boundary and straddles two cache lines. Hardware fetches five sectors totaling 160 bytes instead of four sectors totaling 128 bytes, or up to eight sectors depending on the start offset. This boundary crossing wastes memory bandwidth on unused bytes.
</details>

<details>
<summary>`&lt;strong>`3. In *AI Systems Performance Engineering* Chapter 7 Table 7-1, how did `uncoalescedCopy` compare to `coalescedCopy` across Nsight Compute metrics?`&lt;/strong>`</summary>

Coalescing reduced Average Sectors per Request from eight to four and raised Global Memory Load Efficiency to nearly one hundred percent. It also increased DRAM throughput from a quarter of peak to ninety percent, lifted SM Active percentage, and cut kernel execution time by nearly fourfold. See Table 7-1 in Section 1.2 for the exact figures.
</details>

<details>
<summary>`&lt;strong>`4. Why does an Array of Structures cause uncoalesced global memory access on a GPU, and how does a Structure of Arrays fix it?`&lt;/strong>`</summary>

In an Array of Structures, adjacent threads reading the first field access memory addresses separated by the size of the entire structure. That stride pulls unused fields into the cache sectors. In a Structure of Arrays, adjacent threads reading the first coordinate array access contiguous 4-byte addresses with a stride of one, achieving full warp coalescing.
</details>

<details>
<summary>`&lt;strong>`5. Why does `torch.index_select` with a strided index perform poorly in PyTorch, and what PyTorch operation or compiler mode achieves coalesced and vectorized copies?`&lt;/strong>`</summary>

Calling `torch.index_select` with a strided index launches a gather kernel where threads in a warp load addresses separated by multiple words. That strided pattern touches twice as many sectors per request at stride two. Operating on contiguous tensors via `inp.clone()` or compiling with `torch.compile` in `max-autotune` mode allows TorchInductor to emit coalesced, vectorized memory operations.
</details>

<details>
<summary>`&lt;strong>`6. Contrast global memory coalescing with vectorized memory access as summarized in *AI Systems Performance Engineering* Chapter 7.`&lt;/strong>`</summary>

Coalescing is an inter-thread property that ensures the threads in a warp access contiguous addresses so hardware merges scalar reads into one cache-line transaction. It does not change the instruction count per thread. Vectorizing is an intra-thread technique that packs four floats (`float4`) or eight floats (`float8`) into a single wide load instruction per thread, cutting load instructions by fourfold or eightfold.
</details>

<details>
<summary>`&lt;strong>`7. How many bytes per warp, cache lines, and sectors are moved by a single warp-wide `float4` load on Hopper versus a `float8` load on Blackwell, and what PTX instructions does `nvcc` emit?`&lt;/strong>`</summary>

On Hopper, `float4` loads 16 bytes per thread via `ld.global.v4.f32`, moving 512 bytes per warp across four cache lines and 16 sectors. On Blackwell with CUDA 13, `alignas(32) float8` loads 32 bytes per thread via `ld.global.v8.f32`, moving 1,024 bytes per warp across eight cache lines and 32 sectors.
</details>

<details>
<summary>`&lt;strong>`8. What minimum byte alignment does `cudaMalloc` guarantee on returned device pointers, and how can an element offset break `float4` or `float8` vectorization?`&lt;/strong>`</summary>

The `cudaMalloc` runtime call returns pointers aligned to at least 256 bytes, which satisfies both 16-byte `float4` and 32-byte `float8` alignment at offset zero. Adding an element offset that is not a multiple of four floats for `float4` or eight floats for `float8` breaks natural alignment and forfeits vectorized loads.
</details>

<details>
<summary>`&lt;strong>`9. In Table 7-2 of *AI Systems Performance Engineering* Chapter 7, how did `copyVector16B` using `float4` improve Nsight Compute metrics compared to `copyScalar`?`&lt;/strong>`</summary>

Vectorized `float4` loads raised Global Memory Load Efficiency from 28 percent to 97 percent and dropped Average Sectors per Request to four. DRAM throughput rose to ninety percent of peak, and kernel runtime fell by three and a half times. See Table 7-2 in Section 2.2 for all numbers.
</details>

<details>
<summary>`&lt;strong>`10. Why does `tiledMatMul` with a square shared-memory tile require two `__syncthreads()` barriers inside its tile loop?`&lt;/strong>`</summary>

The first `__syncthreads()` barrier after loading the shared tiles ensures all threads in the block have finished writing their element into shared memory before any thread reads the tile. The second `__syncthreads()` barrier after the compute loop ensures all threads have finished reading the current tile before faster threads advance to the next iteration and overwrite the shared arrays.
</details>

<details>
<summary>`&lt;strong>`11. In Table 7-4 of *AI Systems Performance Engineering* Chapter 7, why did DRAM throughput drop when shared-memory tiling was applied, and why was that drop desirable?`&lt;/strong>`</summary>

In `naiveMatMul`, high DRAM throughput reflected wasteful redundant HBM reads at low arithmetic intensity and low compute throughput. Tiling reused each element 32 times in shared memory, cutting global load sectors by more than eightfold and dropping DRAM saturation while lifting arithmetic intensity, occupancy, and GFLOPS by more than elevenfold.
</details>

<details>
<summary>`&lt;strong>`12. Walk through the register and shared-memory residency math for a 64 by 64 FP32 GEMM tile computed by a 1,024-thread block on a Blackwell SM when each thread uses 12 registers versus 22 registers.`&lt;/strong>`</summary>

Each 64 by 64 FP32 tile takes 16 KB of shared memory, so both input tiles use 32 KB per block and fit easily inside usable shared memory. In both the 12-register and 22-register cases, per-block register consumption and the SM thread limit allow two resident blocks totaling 2,048 threads per SM. See the residency budget breakdown in Section 3.2 for the exact numbers.
</details>

<details>
<summary>`&lt;strong>`13. How is on-chip shared memory organized into banks on modern NVIDIA GPUs, and when does a shared-memory bank conflict occur, including the single-address exception?`&lt;/strong>`</summary>

Shared memory has 32 banks that are each four bytes wide, so successive words map to successive banks and wrap every 128 bytes. A bank conflict occurs when two or more threads in the same warp access different addresses in the same bank during the same cycle. Multiple threads reading the exact same address trigger a conflict-free hardware broadcast instead.
</details>

<details>
<summary>`&lt;strong>`14. Why does reading down a column in `transposeNaive` on `tile[32][32]` cause a 32-way bank conflict, and how does `tile[32][33]` padding or XOR swizzling fix it?`&lt;/strong>`</summary>

In `tile[32][32]`, each row is 32 floats wide, so adjacent lanes reading down a column step by 32 words and all threads hit the exact same bank. Padding the array to `tile[32][33]` changes the row stride to 33 floats so adjacent lanes map to 32 distinct banks with zero conflicts. XOR swizzling achieves the same spread by XOR-transforming the column index.
</details>

<details>
<summary>`&lt;strong>`15. In Table 7-5 of *AI Systems Performance Engineering* Chapter 7, what was the reported impact of padding `tile[32][32]` to `tile[32][33]` in Nsight Compute?`&lt;/strong>`</summary>

Padding `tile[32][33]` reduced Shared-Memory Load Bank Conflicts from 4.8 million to zero and raised Shared-Memory Utilization to one hundred percent. It also dropped the memory warp stall fraction and cut kernel runtime by roughly threefold. See Table 7-5 in Section 3.3 for the full metric comparison.
</details>

<details>
<summary>`&lt;strong>`16. How does a warp shuffle reduction (`__shfl_down_sync`) work, why does it avoid bank conflicts completely, and what is its scope limitation?`&lt;/strong>`</summary>

Calling `__shfl_down_sync` with halving offsets lets each lane read the register value of a higher lane directly across the warp register file in five butterfly steps. Because all values stay in registers and never touch shared memory, no bank conflicts or `__syncthreads()` barriers occur. Its scope is strictly limited to the 32 lanes of a single warp.
</details>

<details>
<summary>`&lt;strong>`17. How does the L1 Read-Only Data Cache (`const __restrict__`) differ from the `__constant__` memory cache, and what speedup did `const __restrict__` achieve in Table 7-6?`&lt;/strong>`</summary>

The 64 KB `__constant__` space has a small per-SM cache optimized for uniform single-address warp broadcasts. The L1 read-only cache serves scattered reads across larger immutable lookup tables when pointers are marked `const __restrict__`. In Table 7-6, adding `const __restrict__` cut off-chip DRAM throughput by threefold, raised L2 read throughput and load efficiency, and cut runtime from 2.5 ms to 1.0 ms.
</details>

<details>
<summary>`&lt;strong>`18. What is the Tensor Memory Accelerator on Hopper and Blackwell GPUs, and how does `cuda::memcpy_async` with `cuda::pipeline` hide the 800-cycle DRAM latency?`&lt;/strong>`</summary>

The Tensor Memory Accelerator (`cp.async.bulk.*`) is a dedicated hardware DMA unit that copies multi-dimensional tiles between global HBM and shared memory asynchronously without using SM registers. Using a two-stage `cuda::pipeline` with ping-pong shared buffers, the block prefetches the next tile asynchronously while warps compute on the current tile. This overlap hides the 800-cycle DRAM latency behind computation.
</details>

<details>
<summary>`&lt;strong>`19. In Table 7-7 of *AI Systems Performance Engineering* Chapter 7, how did TMA-accelerated double buffering change Nsight Compute metrics compared to a naive kernel without prefetching?`&lt;/strong>`</summary>

TMA double buffering raised Global Memory Load Efficiency to 99 percent and dropped Average Sectors per Request to four. DRAM throughput rose to ninety percent, SM Active percentage climbed to one hundred percent, and kernel execution time dropped from 18 ms to 7 ms. See Table 7-7 in Section 4.3 for the complete table.
</details>

<details>
<summary>`&lt;strong>`20. Which Nsight Compute metrics should you inspect first to distinguish uncoalesced global loads, shared-memory bank conflicts, and uncached read-only DRAM thrashing?`&lt;/strong>`</summary>

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

### Explicitly labelled inferences
- The warp sector simulator `analyze_warp_global_memory_access()`, the vectorized load validator `calc_vectorized_warp_load()`, the bank-conflict analyzer `analyze_shared_memory_bank_conflicts()`, and the residency calculator `calc_tile_residency_and_register_budget()` in `code/part10/memory_access_patterns.py` are **my inference** encoding the hardware formulas and benchmark tables of *AI Systems Performance Engineering* Chapter 7.

### Not verified on live hardware
- A physical Blackwell or Hopper GPU was not attached during this build, so `nvcc` and `ncu` commands in Section 5 are marked `(untested here)`.

### Not in the corpus
- Low-level CUTLASS CuTe layout swizzling algebra beyond the conceptual XOR swizzling overview in *AI Systems Performance Engineering* Chapter 7.

### Corrections to the author's notes
- Validation pass confirmed the vectorization and tiling tables directly against the book text, while the remaining tables are encoded in the chapter lab from the same source. The chapter explicitly notes that these are the author's illustrative results, that the DRAM throughput figures repeat across three tables, and that the vectorization baseline sector count is inconsistent with a contiguous scalar load.
- The register breakdown in Section 3.2 is an illustration added by this handbook rather than a figure from the book, and is labelled accordingly in the text block.

