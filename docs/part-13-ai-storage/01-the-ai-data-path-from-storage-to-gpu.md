---
id: "c13-01"
title: "13.1 The AI data path: from storage to GPU"
sidebar_label: "13.1 The AI data path: from storage to GPU"
sidebar_position: 1
description: "Why AI storage fails under capacity-only sizing, the 5 AI storage workload phases, the 8-layer data path from media to GPU HBM, bounce-buffer vs GPUDirect Storage DMA, and per-rack bandwidth math."
status: "drafted"
tier: "2"
level: "B"
lab_venue: "GCP / GKE"
---

# 13.1 The AI data path: from storage to GPU

| Field | Value |
|---|---|
| Level | Basics to Intermediate |
| Priority tier | 2 |
| Lab venue | GCP / GKE (and local Python verification in `code/part13/ai_data_path_lab.py`) |
| Part | Part 13: AI storage |
| Sources used | `nvidia-devops` Volume 15 (`index.md`, `chapter-01-why-ai-storage-is-different.md`, `chapter-02-the-ai-data-path-from-storage-to-gpu.md`, `chapter-12-volume-15-summary.md`, `labs/lab-01-baseline-an-ai-storage-path.md`) and Legacy Volume 06 (`03-ai-storage-data-pipelines-masterclass.md`); *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, `ASP`); *AI Data Center Network Design and Technologies* (`ai-data-center-network-design-and-technologies`, `ADCN`) |
| Coverage file | `planning/coverage/chapters/13-01.md` |
| Claim ledger | `planning/ledgers/13-01.md` |

## Why this matters for AI infrastructure

A GPU that sits idle waiting on a data loader or a stalled checkpoint costs the exact same hourly rate as a GPU waiting on a broken collective. Yet storage is routinely sized by two marketing numbers on a vendor datasheet: total usable terabytes and peak sequential bandwidth.

When 128 or 1,024 GPU workers start a distributed training run, a storage array that passed a synthetic sequential benchmark can still collapse to 24 percent GPU utilization. During an epoch shuffle across eighteen million small files, metadata lookup latency starves the data loaders long before the network links saturate. An hour later, when a thousand GPUs pause simultaneously to flush a checkpoint up to 2 TB, the synchronized write burst overwhelms storage controller queues. Forward progress stops across the entire cluster.

**Understanding AI storage requires replacing the single-number mental model with an end-to-end data path model.** A training sample or model shard must cross eight distinct hardware and software boundaries on its way to the accelerator. It starts on storage media and storage server controllers, then crosses the storage network fabric and the client filesystem driver. From there it enters the Linux kernel page cache, moves through host CPU DRAM across NUMA domains, crosses the PCIe switch fabric, and finally lands in GPU memory.

Every one of those eight boundaries has both a per-operation latency and an aggregate bandwidth ceiling. This chapter maps all five AI storage workload phases across the four-tier storage hierarchy. It contrasts the traditional POSIX CPU bounce-buffer path against GPUDirect Storage direct DMA. You will also derive the bandwidth scaling math from one GPU to a full rack, and learn which commands isolate a storage bottleneck.

## Prerequisites and outcomes

**Prerequisites:**
- Familiarity with Linux storage and memory inspection tools (`iostat`, `vmstat`, `lsblk`, `numactl`, and `strace`) from Part 3.
- Understanding of PCIe generations, NUMA socket topology, and `nvidia-smi topo -m` distance codes from Part 2 and Part 6.
- Basic knowledge of RoCEv2 and InfiniBand lossless fabrics from Part 7.

**Outcomes:** After completing this chapter, you will be able to:
1. Classify the five AI storage lifecycle phases by block size, read and write ratio, and metadata rate.
2. Calculate why a 38.4 GB per second Lustre filesystem delivers only 4.3 GB per second on 220 KB files. Explain how repackaging into 10 MB shards restores 91 percent GPU utilization.
3. Map the four-tier AI factory storage hierarchy and the eight-layer storage-to-GPU data path.
4. Contrast the traditional POSIX CPU bounce-buffer read path against GPUDirect Storage peer-to-peer DMA. Interpret `gdscheck` and `gdsio` benchmarks.
5. Size storage read bandwidth from one GPU up to a thousand-GPU cluster. Calculate the Lustre stripe count needed for a 60-second checkpoint write SLA.

---

## 1. Why AI storage is different: the five workload phases and the capacity illusion

Traditional enterprise storage arrays are built for two predictable workloads. They either serve transactional databases doing small 4 KB random I/O, or media servers streaming large contiguous files to a few clients. An AI factory breaks both assumptions at the same time. Within a single training and serving lifecycle, the storage system gets hit by five conflicting access patterns back to back.

### 1.1 The three failure modes of standard IT storage in AI

When a standard enterprise NAS or untuned storage array is attached to a GPU cluster, it fails in three repeatable ways:

1. **The Metadata Problem:** Computer vision, audio, and multimodal datasets often start as ten million to eighteen million individual files averaging 20 KB to 220 KB each. Before a single byte of payload flows over the network, the client filesystem must resolve the path and check permissions with `stat`. Next, it opens the file descriptor via an RPC to the Metadata Server, reads the tiny file, and closes it. The storage controller spends 85 to 95 percent of its wall-clock time answering metadata lookups rather than streaming bytes. GPUs starve while the storage network links sit 80 percent idle.
2. **The Epoch Shuffle:** To keep a neural network from memorizing sample order across epochs, `DistributedSampler` and data loaders shuffle indices randomly every epoch. Hard disk drives cannot seek fast enough for random access. Even on NVMe arrays, random reads across unsharded files defeat OS kernel read-ahead buffers. They also thrash the Linux page cache whenever the dataset exceeds host RAM.
3. **The Checkpoint Bomb:** Every few hours, hundreds or thousands of GPUs pause computation at the exact same moment. They all flush model weights, gradients, and optimizer states to persistent storage together. That synchronized all-rank fan-in creates a severe network and controller traffic jam known as incast. Every second spent waiting for checkpoint write acknowledgments comes directly out of cluster goodput.

### 1.2 The five AI storage workload phases

Designing an AI storage pipeline starts with separating the data lifecycle into five operational phases. Each phase has its own block size, read-to-write mix, metadata pressure, and failure blast radius.

```mermaid
flowchart LR
    P1["1. Ingest & ETL<br/>S3/GCS bulk write, 4 MB"] --> P2["2. Prep & Sharding<br/>Tokenize/pack, 2 MB"]
    P2 --> P3["3. Training Reads<br/>Shuffled shards, 2 MB, 98% R"]
    P3 --> P4["4. Checkpoint Burst<br/>All-rank sync write, 8 MB"]
    P4 --> P3
    P4 --> P5["5. Inference, RAG & KV<br/>Weights + 64 KB KV/vector"]
```

| Phase | Dominant I/O Pattern | Typical Block Size | Read / Write Split | Metadata Rate at Scale | Primary Storage Tier | Impact When Bottlenecked |
|---|---|---|---|---|---|---|
| **1. Ingest & Raw Collection** | Bulk object writes, dataset scraping, manifest listing | `4,096 KB` (`4 MB`) | `20%` R / `80%` W | `1,000–50,000` ops/s | `Tier 3` Object Store (`S3`/`GCS`) | Delays offline ETL pipeline; does not stall active training GPUs |
| **2. Preprocessing & Sharding** | Read raw objects, deduplicate, tokenize (`NeMo Curator`), pack `.bin`/`.idx` or `WebDataset` `.tar` | `2,048 KB` (`2 MB`) | `55%` R / `45%` W | `5,000–100,000` ops/s | `Tier 2` Parallel FS + `Tier 1` NVMe | Saturates prep CPU/GPU nodes; leaves unsharded small files if skipped |
| **3. Training Dataloader Reads** | Parallel shuffled sequential reads across workers, epoch boundary rescans | `2,048 KB` (`2 MB`) | `98%` R / `2%` W | `50,000–500,000` ops/s (unsharded) or `< 10,000` ops/s (sharded) | `Tier 1` Local NVMe / `Tier 2` PFS | **Stalls GPU SMs on every step; SM utilization drops to `24%–30%`** |
| **4. Synchronous Checkpoint Writes** | Coordinated all-rank burst write of weights + optimizer state, periodic `fsync` | `8,192 KB` (`8 MB`) | `1%` R / `99%` W | `1,000–50,000` ops/s | `Tier 1` NVMe Stage -> `Tier 2` PFS -> `Tier 3` Object | **Freezes all training ranks simultaneously until write completes** |
| **5. Inference, RAG & KV Offload** | Serial/broadcast model startup read, `64 KB` random vector/KV-cache reads & writes | `64 KB` (KV/RAG) to `4,096 KB` (weights) | `85%` R / `15%` W | `100–1,000` ops/s (weights), `1,000–100,000` ops/s (RAG/KV) | `Tier 0` HBM + `Tier 1` Local NVMe + Object/Vector Store | Inflates cold-start time, Time-to-First-Token (`TTFT`), and `p99` latency |

### 1.3 Capacity is not throughput: worked metadata bottleneck calculation

To see why raw capacity and aggregate bandwidth ratings fail to predict training speed, consider a real production deployment on a 7.2 PB Lustre filesystem. The array has 48 Object Storage Targets rated at 800 MB per second each, giving 38.4 GB per second of aggregate read bandwidth. Its Metadata Server is tuned for 50,000 metadata operations per second.

A training job starts across 128 GPU workers, each needing 150 MB per second of training data. The expected aggregate read demand is 19.2 GB per second, which is only half of the array's 38.4 GB per second rating. Yet in production, delivered throughput collapses to 4.3 GB per second, and GPU utilization drops from 94 percent down to 24 percent.

The storage array is not out of bandwidth. Instead, the dataset sits in eighteen million individual files averaging 220 KB each. For every single file, a worker has to resolve the path on the Metadata Server, issue a serialized `open()` RPC, read the 220 KB payload, and close the file.

```text
7.2 PB Lustre Metadata Bottleneck Calculation (48 OSTs x 800 MB/s = 38,400 MB/s = 38.4 GB/s; MDS ceiling = 50,000 ops/s):
  - Per-file RPC steps: MDS path resolution (~10 us) -> open() RPC (~40 us) -> 220 KB read (~100 us) -> close()
  - Demand per worker:  150 MB/s (150,000 KB/s) across 128 workers = 19,200 MB/s (19.2 GB/s, 50% of 38.4 GB/s array)
  - Unsharded (18,000,000 files @ 220 KB): 150,000 / 220 ~= 680 files/s/worker -> 128 x 680 = 87,040 opens/s (75% over 50,000 MDS ceiling)
    Result: 4.3 GB/s delivered throughput, 24% GPU utilization.
  - Repackaged (750,000 WebDataset/TFRecord shards @ 10 MB / 10,000 KB): 150,000 / 10,000 = 15 files/s/worker -> 128 x 15 = 1,920 opens/s (3.8% of MDS)
    Result: 18.6 GB/s delivered throughput, 91% GPU utilization.
  - Second incident (10 nodes / 80 A100 GPUs, 1.5 GB/s target, 8 Gbps/client = 80 Gbps iperf3, OSTs 62% balanced):
    15,000,000 small files in 40 GB -> 95,000 opens/s, 280 MB/s delivered, 40% GPU idle.
    Repackaged into 50 shards of 800 MB -> 8,000 ops/s, 1.42 GB/s delivered, 88% GPU utilization.
```

Because 128 workers opening 680 files per second generate 87,040 opens per second, the Metadata Server is overloaded by 75 percent before counting `stat` calls. Meanwhile, the 48 storage targets sit nearly idle. When the team repackages those eighteen million files into 750,000 contiguous 10 MB shards using WebDataset or TFRecord, total opens drop to 1,920 per second. Metadata load falls to 3.8 percent of server capacity. Delivered bandwidth jumps from 4.3 GB per second to 18.6 GB per second, and GPU utilization climbs back to 91 percent.

A second incident on a ten-node cluster with eighty A100 GPUs shows the exact same trap at smaller scale. The job needed 1.5 GB per second in total, and network checks confirmed plenty of headroom. Yet week-one throughput hit only 280 MB per second because fifteen million small files triggered 95,000 opens per second. Packing that 40 GB dataset into fifty shards of 800 MB each cut metadata operations to 8,000 per second. Throughput recovered to 1.42 GB per second.

Before blaming storage bandwidth for a slow training job, check the average file size and the metadata open rate.

---

## 2. The AI storage hierarchy and the 8-layer data path

No single storage medium can meet the cost, capacity, and latency demands of all five AI workload phases at once. Production AI factories therefore split storage into four tiers. Every read or write crosses up to eight hardware and software layers between the physical drives and the GPU cores.

### 2.1 The four-tier AI factory storage hierarchy

| Tier | Name & Location | Representative Hardware / Software | Typical Capacity | Bandwidth Scale | Typical Access Latency | Primary Role in AI Pipeline |
|---|---|---|---|---|---|---|
| **Tier 0** | **GPU HBM** (on-package with compute die) | `A100` (`40/80 GB`), `H100` (`80 GB`), `H200` (`141 GB`), `B200` (`192 GB`) | `40–192 GB` per GPU | `1.5–2.0 TB/s` (`A100`), `3.35 TB/s` (`H100`), `4.8 TB/s` (`H200`), `8.0 TB/s` (`B200`) | `1–10 ns` | Active weights, activations, gradients, and hot inference KV cache |
| **Tier 1** | **Host Local NVMe Scratch** (`PCIe` Gen4/Gen5 in compute node) | `DGX H100`: `8 x 3.84 TB` NVMe in `RAID 0` (`30.72 TB` raw) | `15–60 TB` per node | `25–60 GB/s` per node | `10–20 us` (`~100 ns` PCIe Gen5 bus hop) | Hot dataset shard cache (`AIStore`, `Alluxio`, `hostPath`), async checkpoint staging |
| **Tier 2** | **Parallel File System (`PFS`)** (dedicated `RoCEv2` or `IB` storage fabric) | `Lustre` (`DDN EXAScaler`, `FSx`), `WEKA`, `BeeGFS`, `VAST`, `IBM Storage Scale`, `DeepSeek 3FS` | `1–50+ PB` cluster-wide | `100 GB/s` to `7.3 TB/s` aggregate | `300 ns` (`IB` switch) / `800 ns` (`Eth` switch) to `0.5–5 ms` | Shared active datasets, distributed checkpoint bursts, multi-node scratch |
| **Tier 3** | **Object Store / Data Lake** (capacity tier on-prem or cloud) | `AWS S3`, `GCS`, `MinIO`, `Ceph`, `Pure FlashBlade`, `Scality` | `10–500+ PB` | `10–100+ GB/s` over HTTP/TLS (`s5cmd`) | `5–50 ms` | Durable raw data lake, cold checkpoint archive, model registry |

Modern AI filesystems increasingly blur the line between the first and second tiers by pooling node-local NVMe drives over RDMA. DeepSeek's open-source Fire-Flyer File System, or 3FS, combines a cluster manager, a sharded metadata service, a storage service, and an RDMA client. Together, they bypass the OS page cache completely. The system serves random training and KV-cache reads straight from NVMe drives over InfiniBand or RoCEv2. Across a 68-node cluster with ten 16 TB NVMe drives and dual 100 Gb/s NICs per node, 3FS sustained 6.6 TB per second of read throughput. It also served 1.4 TB per second of background traffic, and reached 7.3 TB per second on larger clusters.

### 2.2 The 8-layer data path from storage media to GPU HBM

When a training job reads a batch from shared storage without GPUDirect Storage, the payload has to cross eight separate layers. Each layer has its own latency floor and its own queue or bandwidth limit.

```mermaid
flowchart TD
    L1["1. Storage Media (NVMe/SSD)<br/>10 us - 10 ms | iostat -x"] --> L2["2. Storage Server Controller<br/>100 us - 2.3 ms | brw_stats"]
    L2 --> L3["3. Storage Network (RoCE/IB/TCP)<br/>0.3 - 100 us/hop | ethtool/iperf3"]
    L3 --> L4["4. Client Filesystem Driver<br/>50 us - 5 ms | llite stats/strace"]
    L4 --> L5["5. Kernel OS Page Cache<br/>1 - 10 us hit | vmstat/pressure"]
    L5 --> L6["6. Host CPU DRAM & NUMA<br/>50 - 110 ns | numactl/perf"]
    L6 --> L7["7. PCIe Gen4/Gen5 Bus<br/>1 - 10 us, 32-64 GB/s | topo -m"]
    L7 --> L8["8. GPU HBM3/HBM3e<br/>1 - 10 ns, 3.35-8 TB/s | dmon"]
```

| Layer | Component | Typical Latency | Capacity / Bottleneck Limit | Primary Linux / GPU Measurement Tool | Healthy vs Saturated Signal |
|---|---|---|---|---|---|
| **1** | **Storage Media** (`NVMe`, `SSD`, `HDD`) | `10 us–10 ms` | Drive IOPS & media channels (`~5–7 GB/s` per Gen4 NVMe) | `iostat -x 1 /dev/nvme0n1`, `smartctl -a` | Healthy: `r_await < 2 ms`, `Media_Errors = 0`. Saturated: `%util = 100.0`, `r_await > 5 ms` |
| **2** | **Storage Server CPU & I/O Controller** | `100 us–2.3 ms` | Controller RPC slots (`256` max), server RAM cache | `lctl get_param obdfilter.*.brw_stats`, `iotop -P -o` | Healthy: `87.2%` server cache hit, `2.3 ms` service time. Saturated: `< 20%` cache hit, `8–10 ms` latency |
| **3** | **Storage Network Fabric** (`RoCEv2`, `IB`, `TCP`) | `300 ns` (`IB`) / `800 ns` (`Eth`) to `100 us` | Link speed (`100/200/400 Gbps`), switch buffers, `1:3` oversubscription | `ethtool -S eth0`, `iperf3 -c server -t 10 -R`, `ibstat` | Healthy: `> 80%` rated link (`106 Gbps` on `200G`), `0` drops. Saturated: `rx_dropped > 0`, `1,000+` TCP `Retr` |
| **4** | **Client Filesystem Driver** (`Lustre`, `WEKA`, `BeeGFS`, `NFS`) | `50–500 us` (local), `0.5–5 ms` (remote) | `max_rpcs_in_flight`, MDS open/stat RPC serialization | `lctl get_param llite.*.stats`, `strace -c -p <pid>` | Healthy: `open` avg `< 2,000 us` (`2 ms`). Saturated: `open` avg `7,234 us` (`7.2 ms`), `85%` time in `stat` |
| **5** | **Kernel OS Page Cache** | `1–10 us` (hit), `1–10 ms` (refill) | Free host RAM (`vmstat cache`), `kswapd` reclaim rate | `vmstat 1`, `cat /proc/pressure/memory` | Healthy: warm cache (`18,342M`), `wa < 5%`. Saturated: constant eviction thrash, `wa >= 15%` |
| **6** | **Host CPU DRAM & NUMA** (`DDR5` / `LPDDR5X`) | `50–55 ns` (local), `100–110 ns` (remote) | Per-socket memory controller BW & `CPU` `memcpy` cores | `numactl --hardware`, `ps -eLo pid,lwp,psr,comm`, `perf record` | Healthy: loader pinned to local NUMA node. Saturated: cross-socket `SYS` access (`20–30%` throughput loss) |
| **7** | **PCIe Bus / Switch Fabric** (`Gen4` / `Gen5 x16`) | `1–10 us` (`~100 ns` local switch) | `PCIe Gen4 x16` = `32 GB/s`; `Gen5 x16` (`32 GT/s`) = `64 GB/s` (`~63 GB/s` net) | `lspci -vvv`, `nvidia-smi topo -m`, `nvidia-smi dmon -s t` | Healthy: `PIX`/`PXB`/`PHB` affinity, pinned `DMA` at `90%` copy util. Saturated: unpinned `60%` copy util or `SYS` hop |
| **8** | **GPU HBM** (`HBM3` / `HBM3e`) | `1–10 ns` | `40–192 GB` capacity, `3.35–8.0 TB/s` bandwidth | `nvidia-smi dmon`, `nvidia-smi -q`, `Nsight Systems` | Healthy: `sm = 94–95%`, `mem = 40%`, `> 10%` free HBM. Starved: `sm` oscillating `24%–94%` on data wait |

When a job stalls on I/O, walk this eight-layer table from bottom to top instead of guessing which component is slow.

---

## 3. Traditional bounce-buffer I/O vs GPUDirect Storage (`GDS`)

Even when the external storage array delivers 10 GB per second to the compute node's network card or local NVMe drive, the path inside the node often chokes on redundant memory copies and unpinned buffers.

### 3.1 Anatomy of the POSIX CPU bounce-buffer path (3 to 4 copies)

In standard POSIX file I/O, where a `read()` syscall is followed by PyTorch tensor creation and `.to('cuda')`, data cannot move straight from the storage controller into GPU memory. Instead, it bounces through host CPU memory up to four times:

1. **Copy 1, Hardware DMA to Kernel Page Cache:** The storage NIC or NVMe controller transfers the file blocks over the PCIe bus into the Linux kernel's page cache in pageable host DRAM.
2. **Copy 2, Kernel-to-User CPU Copy:** The host CPU takes an interrupt, switches context, and runs a CPU-driven `memcpy` from the kernel page cache into the application's user-space buffer in pageable DRAM.
3. **Copy 3, Pageable-to-Pinned Host Staging Copy:** The GPU's DMA engine cannot safely read pageable virtual memory because the kernel could swap or move those pages mid-transfer. Calling `.to('cuda')` on an unpinned tensor therefore forces the CUDA driver to allocate a temporary page-locked staging buffer and run a second CPU copy in host DRAM. Setting `pin_memory=True` on the data loader skips this extra step by landing user buffers in pinned memory up front.
4. **Copy 4, Pinned Host DRAM to GPU HBM DMA:** Finally, the CUDA driver programs the GPU's copy engine to transfer the batch from pinned host DRAM back across the PCIe bus into GPU memory.

```text
Host DRAM Traffic & Copy Accounting per 10 GB Read:
  - Unpinned POSIX path: 4 total copies (2 PCIe DMA crossings + 2 CPU __memcpy_avx2 ops) -> 60.0 GB host DRAM read/write traffic
  - Pinned path (pin_memory=True): 3 total copies (2 PCIe DMA crossings + 1 CPU copy) -> 40.0 GB host DRAM traffic
  - Production unpinned stall case: 45 GB/s delivered vs 60 GB/s expected (78% GPU util, 22% wait); loader took 120 ms/batch (3.6 s over 30 batches), PCIe copy engine at 60%, batch[0].is_pinned() == False.
  - Fix (pin_collate with .pin_memory()): loader dropped from 120 ms to 30 ms (4x faster), GPU util rose to 94%, throughput reached 58 GB/s.
```

In a production training run where throughput stalled at 45 GB per second instead of 60 GB per second, GPUs sat idle for 22 percent of every step. Timing the data loader showed 120 ms per batch. Meanwhile, `nvidia-smi dmon` showed the PCIe copy engine capped at 60 percent utilization. Checking `batch[0].is_pinned()` returned `False`, proving that every `.to('cuda')` call was copying from pageable memory. Adding a custom collation function that pinned batches cut loader time from 120 ms down to 30 ms. GPU utilization climbed to 94 percent, and throughput reached 58 GB per second.

### 3.2 GPUDirect Storage (`GDS`) architecture: 1 direct P2P DMA copy

**GPUDirect Storage**, part of the NVIDIA Magnum IO stack, removes the host DRAM bounce buffer completely. It pairs the `nvidia-fs.ko` kernel driver with the user-space `libcufile.so` library. The application registers GPU memory buffers directly with `cuFileBufRegister` and reads or writes via `cuFileRead` and `cuFileWrite`.

```mermaid
flowchart LR
    subgraph Trad["Traditional POSIX Bounce Path (3-4 Copies)"]
        T_SRC["Storage NIC / NVMe"] -->|"1. PCIe DMA"| T_PC["Host Page Cache"]
        T_PC -->|"2. CPU memcpy"| T_USR["User Buffer (DRAM)"]
        T_USR -->|"3. Pin memcpy"| T_PIN["Pinned DMA Buffer"]
        T_PIN -->|"4. PCIe DMA"| T_GPU["GPU HBM"]
    end
    subgraph GDS["GPUDirect Storage Path (1 P2P DMA Copy)"]
        G_SRC["Storage NIC / NVMe"] -->|"1. Direct P2P DMA"| G_SW["PCIe Switch (PIX/PHB)"]
        G_SW -->|"Zero Host Copy"| G_GPU["GPU HBM"]
        G_CPU["Host CPU (cuFile)"] -.->|"Control Plane Only"| G_SRC
    end
```

| Metric / Path Attribute | Traditional Unpinned POSIX (`read` + `.to('cuda')`) | Traditional Pinned (`pin_memory=True`) | GPUDirect Storage (`cuFileRead` + `nvidia-fs`) |
|---|---|---|---|
| **Total data copies** | `4` copies | `3` copies | **`1` direct P2P DMA copy** |
| **PCIe bus traversals per byte** | `2` (`Device -> RAM`, `RAM -> GPU`) | `2` (`Device -> RAM`, `RAM -> GPU`) | **`1` (`Device -> PCIe Switch -> GPU`)** |
| **CPU `memcpy` operations (`__memcpy_avx2`)** | `2` | `1` | **`0` (CPU is control-plane only)** |
| **Host DRAM traffic per `10 GB` read** | `60.0 GB` | `40.0 GB` | **`0.0 GB` payload (`BAR1` P2P DMA)** |
| **`gdsio` measured throughput (`4` workers, `1M` IO, `10G` file)** | `~5.2 GB/s` (pageable baseline) | `8.0 GB/s` (`gdsio -x 2`) | **`9.6 GB/s` (`gdsio -x 0`, `+20%` uplift)** |
| **`gdsio` average I/O latency** | `~1.90 ms` | `1.25 ms` (`gdsio -x 2`) | **`1.00 ms` (`gdsio -x 0`, `-20%` latency)** |
| **VAST / Hopper H100 RDMA read uplift** | Baseline | Baseline | **`+20%` on `A100`, `+30%+` on `H100`** |

Two practical rules govern GPUDirect Storage in production:
1. **Kernel filesystem and `O_DIRECT` requirement:** GPUDirect Storage requires a kernel-level filesystem client integrated with `nvidia-fs`. Supported options include EXT4 or XFS over local NVMe, Lustre, WEKA, BeeGFS, VAST NFS-over-RDMA, and IBM Storage Scale. User-space FUSE filesystems cannot use it because they bounce buffers through user space and lack kernel DMA hooks.
2. **Compatibility mode trap:** In `/etc/cufile.json`, setting `allow_compat_mode: true` tells `libcufile` to silently fall back to POSIX host-memory reads whenever `nvidia-fs` or the mount lacks direct DMA support. During cluster qualification, set `"allow_compat_mode": false`. Confirm that `/proc/driver/nvidia-fs/stats` counters increment while `__memcpy_avx2` disappears from `perf record`. Note also that `cuda-checkpoint`, used with CRIU for process migration, is separate from GPUDirect Storage. It copies device memory into host driver memory during suspend rather than using direct storage DMA.

Before assuming GPUDirect Storage is accelerating your job, disable compatibility mode in `/etc/cufile.json` and check `/proc/driver/nvidia-fs/stats`.

---

## 4. Bandwidth math, NUMA/PCIe locality, and page cache pollution

Even when your storage array is properly sharded and GPUDirect Storage is enabled, three cluster-level sizing and placement questions remain. First, you must size steady-state read bandwidth and checkpoint write bandwidth. Second, you must keep CPU workers on the right NUMA socket. Third, you must prevent large shuffled datasets from thrashing the Linux page cache.

### 4.1 Per-GPU, per-node, and per-rack bandwidth scaling

How much sustained storage read bandwidth does a cluster actually need? A standard baseline for multimodal and LLM training is **200 MB per second per GPU**. That figure comes from multiplying bytes per sample by samples per second per GPU. Lighter text-only workloads may need 50 to 150 MB per second per GPU. Heavy video or uncompressed multimodal workloads can require 400 to 1,000 MB per second per GPU.

```text
Cluster Storage Read & Synchronous Checkpoint Write Scaling Formulas:
  - Per-GPU read baseline:               200 MB/s (0.2 GB/s)
  - Single 8-GPU node (DGX H100 / B200): 8 x 200 MB/s = 1,600 MB/s = 1.6 GB/s (12.8 Gbps)
  - Single 72-GPU GB200/GB300 NVL72 rack: 72 x 200 MB/s = 14,400 MB/s = 14.4 GB/s (14-20 GB/s planning band)
  - 1,024-GPU cluster (128 x 8-GPU nodes): 1,024 x 200 MB/s = 204,800 MB/s = 204.8 GB/s
  - 500B model checkpoint (2 TB / 2,000 GB across 256 nodes every 2 h, <= 60 s SLA):
      B_ckpt = 2,000 GB / 60 s = 33.33 GB/s -> ceil(33.33 / 0.8 GB/s per OST) = 42 Lustre OSTs minimum
  - 500 GB checkpoint on 40 GB/s Lustre (48 OSTs @ 800 MB/s; 12.5 s theoretical vs 45 s observed, 32 s extra stall):
      Default 4-OST stripe cap = 4 x 800 MB/s = 3.2 GB/s (156 s raw, 45 s partially cached).
      Wide striping (lfs setstripe -c 32): 25 OSTs = 20.0 GB/s (25 s), 32 OSTs = 25.6 GB/s (20-25 s; < 2-5 s with Tier 1 NVMe stage).
```

Now compare steady-state read bandwidth against the **synchronous checkpoint write burst**. Suppose a 500B-parameter model writes a 2 TB checkpoint across 256 nodes every two hours. Our SLA requires the pause to finish in under 60 seconds. Dividing 2,000 GB by 60 seconds requires 33.33 GB per second of sustained write throughput. Meeting that target takes at least 42 Lustre Object Storage Targets rated at 800 MB per second each.

Consider what happens when a smaller 500 GB checkpoint writes to a 40 GB per second Lustre cluster. In theory, that write should finish in 12.5 seconds, yet in production it frequently stalls training for 45 seconds. By default, a checkpoint directory may stripe files across only four storage targets, capping write speed at 3.2 GB per second. Widening the Lustre stripe count to 25 or 32 targets with `lfs setstripe -c 32` lifts write bandwidth above 20 GB per second and cuts the pause in half. Staging the checkpoint to local NVMe first shrinks the stall even further, down to a few seconds.

### 4.2 NUMA and PCIe topology alignment (`PIX`/`PHB` vs `SYS`)

Inside a dual-socket GPU server, every GPU, storage NIC, and NVMe drive connects to a specific CPU socket and PCIe root complex. When a data loader thread runs on the wrong socket, every memory access and PCIe transfer has to cross the inter-socket link.

| `nvidia-smi topo -m` Code | Meaning | P2P / GDS Path Quality | Typical Bandwidth Impact |
|---|---|---|---|
| **`PIX`** | Connection traversing at most a single `PCIe` switch | **Optimal for GDS P2P DMA** | `100%` of rated `PCIe` / `NIC` speed |
| **`PXB`** | Connection traversing multiple `PCIe` switches without crossing the PCIe Host Bridge | **Very good for GDS** | `95–100%` of rated speed |
| **`PHB`** | Connection traversing a PCIe Host Bridge within the same CPU `NUMA` socket | **Supported for GDS** (root complex hair-pinning) | `85–95%` of rated speed |
| **`NODE`** | Connection traversing `PCIe` and interconnect between NUMA nodes within a socket | Suboptimal | `~88%` retention (`~12%` penalty) |
| **`SYS`** | Connection crossing the inter-socket interconnect (`Intel UPI` / `AMD Infinity Fabric`) | **Poor / GDS P2P often disabled or severely throttled** | `~55–72%` retention (`20–30%+` throughput loss; DRAM latency doubles from `50–55 ns` to `100–110 ns`) |

Suppose `GPU0` and `NIC0` sit on the first NUMA node, while the Linux scheduler places the PyTorch data loader workers on the second NUMA node. Every memory access then crosses the socket interconnect and doubles DRAM latency. Pinning the process and its memory to the local socket with `numactl -N 0 -m 0` eliminates cross-socket traffic and recovers 20 to 30 percent of lost throughput. On NVIDIA Grace Blackwell systems, the 72-core Grace CPU connects to the Blackwell GPU over NVLink-C2C at up to 900 GB per second bidirectional bandwidth. Those GPUs also include a hardware **Decompression Engine** for LZ4, Snappy, Deflate, and `nvJPEG`. Compressed batches can travel across the bus and unpack directly on the GPU without saturating CPU cores.

### 4.3 Linux Page Cache pollution vs `O_DIRECT`

The Linux kernel automatically caches recently read file blocks in free host DRAM, reported as `cache` in `vmstat` and `Cached` in `/proc/meminfo`. Whether that page cache helps or hurts depends on the ratio of your dataset working set to available host RAM:

1. **Regime A, Working set fits in RAM:** When a 120 GB dataset runs on a node with 256 GB of free RAM, the working set stays inside the 85 percent safe memory ceiling. The first epoch populates the page cache from storage. Every subsequent epoch reads straight from host DRAM at microsecond latency with a 95 percent hit rate. Keep buffered I/O enabled and raise `read_ahead_kb` from its 128 KB default up to 2,048 or 4,096 KB with `blockdev --setra`.
2. **Regime B, Working set exceeds RAM:** When a shuffled 4 TB dataset runs on a node with 512 GB of RAM, every cached page gets evicted long before the next epoch needs it again. The cache hit rate drops below 4 to 15 percent. Yet the kernel still burns CPU cycles allocating page frames and running `kswapd` memory reclaim while I/O wait climbs to 15 percent. In this regime, bypass the OS page cache completely using **`O_DIRECT`**, GPUDirect Storage `cuFileRead`, or direct-I/O filesystems like 3FS.

Before launching a multi-epoch job, compare the dataset shard size per node against free host RAM to decide between buffered read-ahead and `O_DIRECT`.

---

## 5. Storage network fabrics and Kubernetes CSI integration

Once storage moves outside the compute node, two infrastructure layers determine whether remote drives can still feed the GPUs at line rate. First, the backend network fabric must transport NVMe commands without packet loss or excessive latency. Second, the Kubernetes container runtime must expose shared filesystems and shared memory cleanly to every worker pod.

### 5.1 NVMe-oF (`TCP` vs `RDMA` over `RoCEv2` vs `InfiniBand`) and Fabric A/B design

A local PCIe Gen5 bus crosses its switch in about 100 nanoseconds and delivers 64 GB per second across 16 lanes. That bandwidth is enough to drive a 400 Gbps storage NIC at line rate. Across a data center, AI clusters attach those NICs to dedicated backend storage networks. Unlike the non-blocking rail-optimized compute fabric used for collectives, the storage fabric commonly uses a **1:3 oversubscribed** leaf-spine topology with **Fabric A and Fabric B path diversity**. Over distances beyond 40 kilometers, maintaining lossless RoCEv2 becomes impractical. Operators instead switch to deep-buffer Ethernet switches running NVMe-oF/TCP or S3 over HTTPS and IPsec.

Under the hood, **NVMe over Fabrics** preserves the native NVMe queue model. It wraps 64-byte Submission Queue Entries and Completion Queue Entries inside fabric capsules:

| Storage Network Option | Transport Encapsulation & Ports | Typical Switch / Fabric Latency | Lossless Fabric Required? | Parallel Shared File Access | Primary AI Factory Use Case |
|---|---|---|---|---|---|
| **`NVMe-oF/TCP`** | `TCP` (`port 8009` discovery; `IC Req PDU`, `CapsuleCmd` `0x01`, `C2HData` `0x04`, `H2CData` `0x03`, `H2CTermReq`; `NVMe` read `0x02` / write `0x01`, `NSID`, `64`-bit `PRP1`/`PRP2`, `SGL`) | `~800 ns` per Ethernet switch hop + host TCP stack | **No** (runs over standard lossy BGP/IP fabric with `MTU 9000` jumbo frames) | No (block-level `1:1` host-to-target session per CPU core) | Cost-effective scale-out block storage, cold/warm tier, `> 40 km` WAN replication |
| **`NVMe-oF/RDMA` (`RoCEv2`)** | `UDP` (`TCP 8009` discovery, `UDP 4420` `RDMA_CM` `RDMA_PRTYPE 04` vs `05` iWARP, `UDP 4791` `BTH` + `RETH` + NVMe capsule; `1:1` SQ/CQ to `QPair`) | `700–900 ns` port-to-port Ethernet switch latency (`~66%` lower write latency vs TCP) | **Yes** (`PFC`, `ECN`, `DCQCN` tuned separately from training fabric) | No (unless layered under a parallel FS like `WEKA`, `VAST`, or `3FS`) | High-IOPS block targets, `GPUDirect Storage` over Ethernet (`100/200/400 Gbps` storage NICs) |
| **`InfiniBand` Storage (`NVMe-oF/IB` / `LNet`)** | Native `IB` (`LRH` with `16`-bit `S-LID`/`D-LID` up to `48,000` nodes, `GRH`, `BTH` `RDMA_PRTYPE 02`, `ICRC`/`VCRC`) | `~300 ns` port-to-port IB switch latency | **Yes** (hardware `CBFC` credit-based flow control across `16` Virtual Lanes `VLs`, `64 B`/credit) | Via `Lustre` (`LNet`), `BeeGFS`, `GPFS`, or `WEKA` | Ultra-low-latency HPC/AI training storage and direct `GDS` over `NDR`/`HDR` |
| **Parallel FS / `pNFS` over `RDMA`** | `POSIX` client (`open`, `read`, `write`, `stat`, `mmap`) over `RoCEv2` or `IB` (`WEKA`, `Lustre`, `BeeGFS`, `VAST`, `3FS`) | `300–900 ns` switch hop + `50–500 us` client driver | Recommended for `RDMA` transport | **Yes** (`ReadWriteMany` across `1,000+` GPU nodes with distributed metadata) | Primary `Tier 2` AI training datasets and synchronized checkpoint bursts |

### 5.2 Kubernetes CSI (`ReadWriteMany`), `hostPath` NVMe, and PyTorch `DataLoader` pipelining

In Kubernetes clusters, standard cloud block CSI drivers provide `ReadWriteOnce` volumes built for single-pod databases. Distributed training across dozens or thousands of pods requires **`ReadWriteMany` parallel filesystem CSI provisioners**. Common choices include WEKA CSI, Lustre CSI, and Google Cloud Managed Lustre, paired with three essential pod settings:

1. **Memory-backed `/dev/shm` `emptyDir` (`sizeLimit: 400Gi`):** Multi-worker PyTorch data loaders pass collated tensor batches to the main training process through POSIX shared memory at `/dev/shm`. NCCL uses it as well. Docker and Kubernetes default `/dev/shm` to just 64 MiB, which immediately crashes multi-worker loaders with `Bus error (core dumped)`.
2. **GPUDirect Storage config injection (`CUFILE_ENV_PATH_JSON`):** Mount the validated `/etc/cufile.json` ConfigMap into the container. Run the pod under `runtimeClassName: nvidia` so `/dev/nvidia-fs*` device nodes are exposed.
3. **Local NVMe scratch via `hostPath` (`/mnt/nvme_raid_0/ai_scratch`):** Mount the node's local RAID 0 directory directly to avoid CSI overhead when caching shards or staging checkpoints.

On the software side, the PyTorch `DataLoader` has to overlap CPU batch preparation with GPU kernel execution so the next batch transfers while the current batch computes:
- Set `num_workers=8` or scale to CPU core count, and enable `pin_memory=True` with host `ulimit -l unlimited`. Also set `persistent_workers=True` so workers do not respawn every epoch, and `prefetch_factor=4` to queue 32 batches ahead.
- Call `batch.to(device, non_blocking=True)` on a dedicated CUDA copy stream and synchronize with `compute_stream.wait_stream(copy_stream)`.
- Offload heavy image or video decoding to GPU hardware decoders with **NVIDIA DALI** or `nvJPEG`. Pre-tokenize text offline with **NVIDIA NeMo Curator** into memory-mappable `.bin` and `.idx` shards.

Before deploying a multi-worker training pod on Kubernetes, verify that `/dev/shm` is backed by a large memory `emptyDir` and that `persistent_workers=True` is enabled.

---

## Commands and configurations that matter

All commands below are marked `(untested here)` because they target live Linux GPU nodes with Lustre, WEKA, NVMe hardware, and NVIDIA GDS drivers. See the Hands-on lab for the runnable Python verification suite executed in this repository.

### 1. Layer-by-layer data path inspection (`Layers 1–8`) `(untested here)`

```bash
# (untested here) Layer 1: Local NVMe media health and saturation (%util, r_await)
smartctl -a /dev/nvme0n1 | grep -E "Media_Errors|Unsafe_Shutdowns|Temperature"
iostat -x 1 /dev/nvme0n1 | head -10

# (untested here) Layer 1b: Verify NVMe multiqueue scheduler (none/mq-deadline) and tune read-ahead (128 KB -> 4096 KB)
cat /sys/block/nvme0n1/queue/scheduler
cat /sys/block/nvme0n1/queue/read_ahead_kb
blockdev --setra 8192 /dev/nvme0n1

# (untested here) Layer 2 & 4: Lustre OST balance, server RPC stats, and client metadata open/getattr latency
lfs df -h
lfs df -i
lctl get_param obdfilter.*.brw_stats
lctl get_param llite.*.stats 2>/dev/null | grep -E "close|open|getattr|readdir"
lctl get_param -n mdc.*.max_rpcs_in_flight

# (untested here) Layer 3: Storage NIC link speed, ring buffers, drops, and reverse iperf3 bandwidth
ethtool eth0
ethtool -g eth0
ethtool -S eth0 | grep -E "rx_packets|rx_bytes|rx_errors|rx_dropped|collisions"
iperf3 -c storage-server -t 10 -R

# (untested here) Layer 4b: Tuned NFS mount (when NFS is used on small clusters)
mount -t nfs -o rsize=1048576,wsize=1048576,noatime,async,actimeo=60,lookupcache=pos \
  nfs-server:/export/datasets /mnt/datasets

# (untested here) Layer 5: OS Page Cache activity, memory pressure, and I/O wait (wa)
vmstat 1 10
cat /proc/pressure/memory

# (untested here) Layer 6, 7 & 8: NUMA layout, PCIe link width, GPU-to-NIC topology, and H2D copy utilization
numactl --hardware
nvidia-smi topo -m
lspci -vvv | grep -A 5 "NVIDIA"
nvidia-smi dmon -s t -c 10
nvidia-smi -i 0 --query-gpu=memory.used,memory.total,memory.free --format=csv,nounits
```

### 2. GPUDirect Storage (`GDS`) verification and `gdsio` benchmarking `(untested here)`

```bash
# (untested here) 1. Verify nvidia-fs kernel module and platform GDS support
lsmod | grep nvidia_fs
/usr/local/cuda/gds/tools/gdscheck -p
cat /proc/driver/nvidia-fs/stats

# (untested here) 2. Benchmark CPU bounce-buffer path (-x 2) vs direct GDS DMA path (-x 0)
# Baseline CPU path: 8.0 GB/s, 1.25 ms average latency
/usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 2

# Direct GDS path: 9.6 GB/s (+20%), 1.00 ms average latency (-20%)
/usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 0
```

Configuration `/etc/cufile.json` with compatibility fallback disabled during qualification `(untested here)`:

```json
{
  "logging": {
    "level": "ERROR"
  },
  "properties": {
    "max_device_pinned_mem_size_kb": 33554432,
    "use_poll_mode": false,
    "poll_mode_max_size_kb": 4,
    "allow_compat_mode": false
  }
}
```

### 3. Benchmarking sequential reads (`fio`), checkpoint bursts (`fio`), and MDS (`mdtest`) `(untested here)`

```bash
# (untested here) 1. Simulate 32-worker sequential dataset reads (2 MB blocks, 500 GB > host RAM, O_DIRECT)
fio --name=ai_dataset_read_sim \
    --directory=/mnt/weka/ai_datasets/benchmarks \
    --rw=read --bs=2M --size=500G --numjobs=32 --iodepth=128 \
    --ioengine=libaio --direct=1 --group_reporting

# (untested here) 2. Simulate synchronous checkpoint write burst (8 MB blocks, periodic fsync=1000)
fio --name=checkpoint_write_burst \
    --directory=/mnt/lustre/checkpoints/benchmarks \
    --rw=write --bs=8M --size=100G --numjobs=8 --iodepth=64 \
    --ioengine=libaio --direct=1 --fsync=1000 --group_reporting

# (untested here) 3. Stress-test Metadata Server (MDS) across 128 MPI ranks
mpirun -np 128 mdtest -d /mnt/lustre/metadata_stress_test -i 5 -b 10 -z 3 -L -I 100000 -y -u -t
```

### 4. Kubernetes `RWX` CSI StorageClass and GDS-enabled training Pod `(untested here)`

```yaml
# (untested here) RWX parallel filesystem StorageClass + training Pod with 400Gi /dev/shm and cufile.json
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: weka-rwx-ai-optimized
provisioner: csi.weka.io
parameters:
  volumeType: dir/v1
  filesystemName: "ai-factory-primary-fs"
reclaimPolicy: Retain
allowVolumeExpansion: true
---
apiVersion: v1
kind: Pod
metadata:
  name: llm-training-worker-rank-0
spec:
  runtimeClassName: nvidia
  containers:
  - name: pytorch-training-container
    image: nvcr.io/nvidia/pytorch:24.07-py3
    env:
    - name: CUFILE_ENV_PATH_JSON
      value: "/etc/cufile.json"
    volumeMounts:
    - name: dataset-vol
      mountPath: /workspace/datasets
    - name: local-nvme-cache
      mountPath: /mnt/nvme_scratch
    - name: dev-shm
      mountPath: /dev/shm
    - name: gds-config
      mountPath: /etc/cufile.json
      subPath: cufile.json
    resources:
      limits:
        nvidia.com/gpu: 8
  volumes:
  - name: dataset-vol
    persistentVolumeClaim:
      claimName: weka-dataset-pvc-1tb
  - name: local-nvme-cache
    hostPath:
      path: /mnt/nvme_raid_0/ai_scratch
      type: Directory
  - name: dev-shm
    emptyDir:
      medium: Memory
      sizeLimit: 400Gi
  - name: gds-config
    configMap:
      name: gds-configmap
```

---

## How it fails

| Failure Mode | Symptom | Root Cause | Diagnosis Commands | Architectural Fix |
|---|---|---|---|---|
| **1. Metadata Server (`MDS`) Saturation ("Small File Problem")** | GPU `SM` utilization drops from `94%` to `24%–30%`; storage array delivers `4.3 GB/s` out of `38.4 GB/s` capacity while storage network links sit idle. | DataLoader iterates over `10M–18M` small files (`20–220 KB`). Workers issue `87,040–95,000` `open`/`stat` RPCs/s against a `50,000` ops/s `MDS` limit (`85%` of syscall time spent in `stat`). | `strace -c -p <loader_pid>`, `lctl get_param llite.*.stats \| grep -E "open\|getattr"` (`avg > 7,234 us`). | Repackage small files into `10 MB–800 MB` shards (`WebDataset` `.tar`, `TFRecord`, `Parquet`, or `.bin`/`.idx`), reducing `MDS` ops by `50x–50,000x`, or stage dataset to `Tier 1` local `NVMe`. |
| **2. Cascading `D`-State Hang (Uninterruptible Sleep)** | `4`+ nodes drop out of a `64`-node `DDP` job; SSH takes `30 s`; `top` shows load average `500+` with `0%` CPU; `htop` shows hundreds of `python3` processes stuck in state `D` (`kill -9` has no effect). | Broken storage `AOC` cable (`symbol_error_counter > 1000`) or dead storage router causes hard-mounted network FS client (`NFS`/`Lustre`) to block indefinitely inside kernel `rpc_wait_bit_killable`. | `dmesg -T \| grep "blocked for more than 120 seconds"`, `ibstat`, `ibv_devinfo -d mlx5_0`. | Hard-reset wedged nodes via `ipmitool chassis power reset`, replace bad optics, and use bounded timeouts / soft mounts on read-only dataset volumes so I/O errors fail fast instead of locking the kernel. |
| **3. Unpinned Host Bounce-Buffer Stall** | Training achieves `45 GB/s` instead of `60 GB/s`; GPUs sit idle `22%` of each step (`120 ms` loader wait per batch); `nvidia-smi dmon -s t` shows `PCIe` memory copy utilization capped at `60%`. | `DataLoader` returns pageable CPU tensors (`is_pinned() == False`), forcing synchronous on-the-fly host pinning and an extra CPU `memcpy` on every `.to('cuda')` call. | Check `batch[0].is_pinned()`, run `nsys profile --trace=cuda,nvtx,osrt`, inspect `perf record` for `__memcpy_avx2`. | Enable `pin_memory=True` (with `ulimit -l unlimited`), use `non_blocking=True` on a dedicated copy `Stream`, or enable `GPUDirect Storage` (`cuFileRead`). |
| **4. Under-Striped Synchronous Checkpoint Incast** | A `500 GB` checkpoint stalls training for `45 s` (or `500 s` at `1 GB/s`) even though cluster storage is rated for `40 GB/s` (`12.5 s` theoretical). | Checkpoint directory defaults to `4` Lustre `OST` stripes (`4 * 800 MB/s = 3.2 GB/s` ceiling), or `1` `OST` sits at `98%` full while others sit at `49%`. | `lfs getstripe /mnt/lustre/checkpoints`, `lfs df -h`, `iotop -P -o` during checkpoint flush. | Set wide striping on checkpoint directories at creation time (`lfs setstripe -c 32 -S 8M`), shard checkpoints per rank (`PyTorch DCP`), and stage writes asynchronously to `Tier 1` local `NVMe` first. |
| **5. Cross-Socket `NUMA` / `PCIe` Misalignment (`SYS` Hop)** | One node or rank runs `20%–30%` slower than identical peers; `GDS` falls back to host bounce mode or runs at `5.76 GB/s` instead of `10 GB/s`. | DataLoader CPU threads run on `NUMA 1` (`CPUs 8–15`) while `GPU0` and `NIC0` sit on `NUMA 0` (`CPUs 0–7`), forcing every `DRAM` and `PCIe` transfer across the inter-socket `SYS` link (`110 ns` vs `55 ns`). | `nvidia-smi topo -m`, `numactl --hardware`, `ps -eLo pid,lwp,psr,comm \| grep loader`. | Bind each rank's process and memory to the `NUMA` node affine to its GPU and storage NIC (`numactl -N 0 -m 0` or `torchrun` CPU affinity). |
| **6. OS Page Cache Thrashing on Multi-TB Shuffled Datasets** | Throughput degrades sharply on Epoch 2+; `vmstat` shows `wa >= 15%` and high `bi`, `kswapd` burns CPU, and `/proc/pressure/memory` shows high stall percentages. | Shuffled `4 TB` dataset exceeds `512 GB` host RAM; buffered POSIX reads pollute the page cache with single-use pages (`~4%` hit rate) and trigger continuous page reclaim. | `vmstat 1`, `cat /proc/pressure/memory`, `free -h`. | Enable `O_DIRECT` (`direct=1` or `cuFileRead` via `GDS`) to bypass the OS page cache when dataset working set exceeds `85%` of free host RAM. |

---

## Hands-on lab

### Venue and scope

- **Primary runnable lab:** `code/part13/ai_data_path.py` and `code/part13/ai_data_path_lab.py`, using only the Python standard library across 26 automated self-checks.
- **Cluster venue:** GCP or GKE node pools with local NVMe SSDs and Managed Lustre or Filestore RWX volumes, with live hardware commands marked `(untested here)`.

### Part A: Run the self-checking AI data path lab locally

Run the verification script to validate all five workload phases, the metadata saturation math, and bounce-buffer copies versus GPUDirect Storage. The script also checks cluster bandwidth scaling, NUMA and PCIe locality penalties, and page cache thrashing versus `O_DIRECT`:

```bash
python3 -B code/part13/ai_data_path_lab.py
```

Expected output (verified):

```text
[PASS] five_workload_phases_defined
[PASS] ingest_phase_write_dominant
[PASS] preprocessing_phase_balanced_io
[PASS] training_reads_phase_high_read_and_metadata
[PASS] checkpoint_writes_phase_burst_write
[PASS] inference_rag_kv_phase_low_latency_64kb
[PASS] four_storage_tiers_ordered
[PASS] eight_data_path_layers_complete
[PASS] lustre_raw_ost_bandwidth_38_4_gbs
[PASS] small_files_220kb_saturate_mds
[PASS] sharded_10mb_files_relieve_mds
[PASS] ten_node_sharded_bandwidth_restored
[PASS] traditional_pinned_path_has_3_copies_and_2_pcie_crossings
[PASS] gds_path_has_1_dma_copy_and_0_host_dram_payload
[PASS] gdsio_benchmark_8_0_vs_9_6_gbs_uplift_20_pct
[PASS] unpinned_pageable_path_has_4_copies_and_lower_bw
[PASS] node_8gpu_bandwidth_is_1_6_gbs
[PASS] nvl72_rack_bandwidth_is_14_4_gbs_within_14_to_20_gbs_band
[PASS] cluster_1024gpu_bandwidth_is_204_8_gbs
[PASS] checkpoint_2tb_in_60s_requires_33_33_gbs_and_42_osts
[PASS] checkpoint_500gb_in_25s_requires_20_gbs_and_25_osts
[PASS] aligned_numa0_pix_retains_100_pct_bandwidth_and_gds
[PASS] cross_socket_sys_and_wrong_numa_degrades_bw_and_disables_optimal_gds
[PASS] working_set_fitting_in_ram_warms_page_cache
[PASS] multi_tb_shuffled_dataset_thrashes_page_cache_without_odirect
[PASS] o_direct_eliminates_page_cache_thrashing_on_large_datasets
Summary: 26 passed, 0 failed (total 26)
```

### Part B: Baseline a GPU node storage path on Linux / GKE `(untested here)`

When onboarding a new GPU node pool, capture a reproducible five-stage storage path baseline before launching distributed jobs:

```bash
#!/bin/bash
# (untested here) Capture 5-stage AI storage path baseline on a GPU node
OUT="baseline-$(hostname)-$(date +%Y%m%d).txt"
echo "=== 1. NETWORK & RING BUFFERS ===" | tee "$OUT"
ip -s link >> "$OUT"
ethtool eth0 >> "$OUT" 2>/dev/null || true
ethtool -g eth0 >> "$OUT" 2>/dev/null || true

echo "=== 2. CPU, NUMA & GPU-TO-NIC TOPOLOGY ===" | tee -a "$OUT"
lscpu >> "$OUT"
numactl --hardware >> "$OUT" 2>/dev/null || true
nvidia-smi topo -m >> "$OUT" 2>/dev/null || true

echo "=== 3. MOUNTS, LUSTRE/BEEGFS & LOCAL NVME ===" | tee -a "$OUT"
findmnt -D >> "$OUT"
lsblk -o NAME,MODEL,SIZE,ROTA,TYPE >> "$OUT"
lfs df -h >> "$OUT" 2>/dev/null || true

echo "=== 4. SEQUENTIAL READ BENCHMARK (FIO 1M DIRECT) ===" | tee -a "$OUT"
fio --name=seq-read --ioengine=libaio --rw=read --bs=1M --size=10G \
    --direct=1 --iodepth=32 --numjobs=4 --filename=/mnt/scratch/test.file \
    --group_reporting >> "$OUT" 2>/dev/null || true

echo "=== 5. MEMORY & PAGE CACHE STATE ===" | tee -a "$OUT"
free -h >> "$OUT"
cat /proc/meminfo | grep -E "Cached|Buffers|MemAvailable|MemFree" >> "$OUT"
```

---

## Common first mistakes

1. **Benchmarking AI storage with 4 KB random OLTP profiles or cached files smaller than host RAM.** Running `fio` with a 10 GB test file on a node with 256 to 2,000 GB of RAM without `--direct=1` measures DDR5 page cache bandwidth above 50 GB per second. It does not measure storage throughput. Always set `--size` larger than host RAM or pass `--direct=1` with 1 MB to 8 MB block sizes that match dataset reads and checkpoint writes.
2. **Leaving `/dev/shm` at the 64 MiB container default.** Multi-worker PyTorch data loader pipelines with `num_workers=8` and `prefetch_factor=4` allocate tens of gigabytes of shared memory segments in `/dev/shm`. Always mount a memory-backed `emptyDir` with `sizeLimit: 400Gi` at `/dev/shm` on eight-GPU nodes.
3. **Assuming GPUDirect Storage is active without checking `/proc/driver/nvidia-fs/stats`.** Because `/etc/cufile.json` defaults to `"allow_compat_mode": true`, a misconfigured mount or unsupported FUSE filesystem silently falls back to CPU bounce-buffer copies. Your job continues to run at degraded speed without raising an error.
4. **Treating local RAID 0 NVMe scratch as durable storage.** Node-local NVMe has no cross-node replication. If a compute node fails, any checkpoint staged only on local NVMe is lost until flushed asynchronously to shared parallel storage or object storage.
5. **Using `num_workers=0` in production or forgetting `persistent_workers=True`.** While `num_workers=0` is useful as a temporary diagnostic to isolate pure Python transform time, leaving it in production serializes file reads with GPU execution. Forgetting `persistent_workers=True` causes worker processes to respawn and re-initialize file handles at the start of every epoch.

---

## Exercises

All numerical constants and target verification outputs for the six exercises below appear in the reference block that follows.

1. **Metadata Server Saturation and Repackaging Math:** Evaluate a 7.2 PB Lustre cluster with 48 Object Storage Targets rated at 800 MB per second each. Its single Metadata Server is rated at 50,000 open operations per second, and a 128-worker job needs 150 MB per second per worker. Calculate the aggregate open rate when reading 220 KB files and the percentage by which the Metadata Server is overloaded. Then calculate the open rate after repackaging the dataset into 10 MB WebDataset shards. Verify whether the 48 storage targets can sustain the 19.2 GB per second demand.
2. **Bounce-Buffer vs GPUDirect Storage Copy and DRAM Accounting:** A node reads a 10 GB shard from a storage NIC into `GPU0` memory. List the memory copies, PCIe bus traversals, and total host DRAM traffic for an unpinned POSIX read, a pinned `pin_memory=True` read, and a GPUDirect Storage `cuFileRead` transfer. Next, use the `gdsio` baselines for CPU mode versus GPUDirect Storage mode to compute the percentage throughput uplift and latency reduction.
3. **Node, NVL72 Rack, and 1,024-GPU Cluster Bandwidth Sizing:** Assume each GPU requires 200 MB per second of sustained training read throughput. Compute the required aggregate read bandwidth for an eight-GPU node, a 72-GPU GB200 NVL72 rack, and a 1,024-GPU cluster. Next, assume the cluster saves a 2 TB synchronous checkpoint every two hours and must finish the write pause in under 60 seconds. Calculate the minimum write bandwidth required and how many 800 MB per second Lustre targets the checkpoint must be striped across.
4. **Diagnosing the 45-Second Checkpoint Stall:** A 500 GB checkpoint on a 40 GB per second storage array should theoretically finish in 12.5 seconds, but takes 45 seconds in production. Calculate the effective bandwidth cap when the checkpoint directory defaults to four Lustre stripes. Then compute the new theoretical write bandwidth when striped across 25 versus 32 targets.
5. **NUMA and PCIe Topology Penalty Calculation:** On a dual-socket server, `GPU0` and `NIC0` sit on the first NUMA node with a 10.0 GB per second baseline rate. Compare the DRAM access latency, GPUDirect Storage P2P eligibility, and delivered throughput when the data loader runs locally versus on the second socket across the inter-socket `SYS` link.
6. **Page Cache vs `O_DIRECT` Regime Selection:** Using `evaluate_page_cache_vs_odirect` from `code/part13/ai_data_path.py`, determine whether buffered page cache or `O_DIRECT` should be used for two workloads. First evaluate a 120 GB dataset on a node with 256 GB of free RAM. Second, evaluate a 4,000 GB randomly shuffled dataset on a node with 512 GB of free RAM.

```text
Exercise Input Parameters & Expected Verification Targets (code/part13/ai_data_path_lab.py):
  - Ex 1 (MDS Math):     7.2 PB Lustre, 48 OSTs x 800 MB/s = 38.4 GB/s, MDS = 50,000 ops/s; 128 workers x 150 MB/s (150,000 KB/s) = 19.2 GB/s. At 220 KB/file: ~680 files/s/worker -> 128 x 680 = 87,040 opens/s (~75% overload -> 4.3 GB/s, 24% GPU util). At 10 MB (10,000 KB) shards (750,000 shards): 15 files/s/worker -> 1,920 opens/s (3.8% MDS load -> 18.6 GB/s delivered, 91% GPU util).
  - Ex 2 (GDS vs POSIX): Per 10 GB read: (i) Unpinned POSIX = 4 copies, 2 PCIe traversals, 2 CPU memcpy, 60.0 GB host DRAM traffic; (ii) Pinned (pin_memory=True) = 3 copies, 2 PCIe traversals, 1 CPU copy, 40.0 GB DRAM traffic; (iii) GDS (cuFileRead) = 1 P2P DMA copy, 1 PCIe traversal, 0 CPU copies, 0.0 GB host DRAM payload traffic. gdsio: -x 2 (CPU) = 8.0 GB/s @ 1.25 ms vs -x 0 (GDS) = 9.6 GB/s @ 1.00 ms (+20% throughput uplift, -20% latency reduction).
  - Ex 3 (BW Sizing):    At 200 MB/s (0.2 GB/s) per GPU: 8-GPU node = 1.6 GB/s; 72-GPU NVL72 rack = 14.4 GB/s (14-20 GB/s band); 1,024-GPU cluster = 204.8 GB/s. Checkpoint: 2 TB (2,000 GB) in 60 s = 33.33 GB/s -> ceil(33.33 / 0.8 GB/s) = 42 OSTs.
  - Ex 4 (Stripe Cap):   500 GB on 40 GB/s array (48 OSTs @ 800 MB/s) = 12.5 s theoretical vs 45 s observed. Default 4 OST stripes = 4 x 800 MB/s = 3.2 GB/s cap. Striping across 25 OSTs = 20.0 GB/s (25 s); 32 OSTs = 25.6 GB/s.
  - Ex 5 (NUMA/PCIe):    NUMA 0 local (CPUs 0-7, PIX): 50-55 ns DRAM latency, GDS P2P enabled, 10.0 GB/s (100% retained). Cross-socket NUMA 1 (CPUs 8-15, SYS): 100-110 ns DRAM latency, GDS P2P disabled/throttled, 10.0 x 0.72 (SYS factor) x 0.80 (remote DRAM factor) = 5.76 GB/s (57.6% retained).
  - Ex 6 (Page Cache):   (a) 120 GB dataset on 256 GB free RAM (W <= 0.85 x M = 217.6 GB): use buffered page cache (~95% hit rate in Epoch 2+, read_ahead_kb = 2048-4096 KB). (b) 4,000 GB (4 TB) shuffled dataset on 512 GB RAM (W >> M): use O_DIRECT (bypasses ~4% hit-rate thrashing and 15% iowait).
```

---

## Interview angles

1. **"Your GPUs are at 30 percent utilization, but the storage network links are 80 percent idle. How do you isolate whether the bottleneck is storage media, metadata, network, or CPU preprocessing?"**
   Walk the data path layer by layer rather than guessing from aggregate bandwidth. First check metadata open and `stat` rates with `lctl get_param llite.*.stats` or `strace -c -p <loader_pid>`. If opens exceed 50,000 per second or `stat` consumes 85 percent of syscall time, it is the small-file problem. The fix is sharding into WebDataset or TFRecord. Second, verify client-to-storage network throughput with `iperf3 -c storage-server -R` and check `lfs df -h` for storage target fill imbalance. Third, isolate the Python data loader by comparing `num_workers=0` against `num_workers=8`. Check CPU core saturation and NUMA affinity with `numactl --hardware` and `nvidia-smi topo -m`, and verify `batch.is_pinned()` so transfers use DMA rather than pageable CPU copies.
2. **"When does GPUDirect Storage materially improve performance, and how do you prove it is actually active?"**
   GPUDirect Storage removes the host DRAM bounce buffer, cutting three or four copies down to a single direct P2P DMA transfer across PCIe. That pays off on bandwidth-heavy sequential reads and checkpoint writes when the PCIe topology is `PIX`, `PXB`, or `PHB`. It will not fix a metadata-bound workload opening millions of tiny files, and it cannot run over user-space FUSE mounts. Prove it is active by setting `"allow_compat_mode": false` in `/etc/cufile.json` and running `gdscheck -p`. Then benchmark `gdsio -x 2` against `gdsio -x 0`, confirm `/proc/driver/nvidia-fs/stats` increments during training, and verify that `__memcpy_avx2` disappears from `perf record`.
3. **"A 64-node training job hangs and four nodes have hundreds of `python3` processes stuck in Linux state `D` that ignore `kill -9`. What happened and how do you prevent it?"**
   State `D` is uninterruptible kernel sleep waiting on hardware or network filesystem I/O, often shown as `rpc_wait_bit_killable` in `dmesg`. A failed optical transceiver with rising symbol errors or a dead storage router left a hard-mounted filesystem client waiting forever for an RPC reply. Immediate recovery requires an out-of-band `ipmitool chassis power reset` and cable replacement. Long-term prevention uses redundant Fabric A and Fabric B storage paths. Also configure bounded timeouts on read-only dataset mounts so broken links raise an exception instead of wedging the kernel.

---

## Checkpoint questions (20)

<details>
<summary>`&lt;strong>`1. Why can a 38.4 GB/s Lustre array deliver only 4.3 GB/s and 24% GPU utilization to a 128-worker job requesting 19.2 GB/s?`&lt;/strong>`</summary>

The dataset sits in eighteen million small 220 KB files. At 150 MB per second per worker, each worker opens about 680 files per second, or 87,040 opens per second across all 128 workers. That overloads the Metadata Server's 50,000 operations per second ceiling by 75 percent before the 48 storage targets can stream data.
</details>

<details>
<summary>`&lt;strong>`2. What are the five AI storage lifecycle workload phases and their primary I/O profiles?`&lt;/strong>`</summary>

```text
1. Ingest & ETL:                  4 MB (4,096 KB) bulk writes to Tier 3 object store (20% R / 80% W, 1K-50K ops/s)
2. Preprocessing & Sharding:      2 MB (2,048 KB) mixed read/write tokenizing and packing shards (55% R / 45% W, 5K-100K ops/s)
3. Training Dataloader Reads:     2 MB parallel shuffled sequential reads (98% R / 2% W, 50K-500K ops/s unsharded vs <10K sharded)
4. Synchronous Checkpoint Writes: 8 MB (8,192 KB) all-rank write burst (1% R / 99% W, 1K-50K ops/s)
5. Inference, RAG & KV Offload:   64 KB low-latency random KV/vector I/O + 4 MB model weight reads (85% R / 15% W)
```
</details>

<details>
<summary>`&lt;strong>`3. What are the four storage tiers (Tier 0 to Tier 3) in an AI factory and their typical capacities on a DGX H100 cluster?`&lt;/strong>`</summary>

Tier 0 is GPU HBM, holding 80 GB on an H100 at 3.35 TB per second, 141 GB on an H200, and 192 GB on a B200. Tier 1 is host local NVMe scratch, such as eight 3.84 TB drives in RAID 0 for 30.72 TB on a DGX H100. Tier 2 is the shared Parallel File System like Lustre, WEKA, BeeGFS, VAST, or 3FS. Tier 3 is the durable Object Store such as S3, GCS, MinIO, or Ceph.
</details>

<details>
<summary>`&lt;strong>`4. List the 8 layers of the AI storage-to-GPU data path in order from media to accelerator.`&lt;/strong>`</summary>

The eight layers in order are Storage Media, Storage Server CPU and Controller, Storage Network Fabric, and Client Filesystem Driver. Inside the compute node, the payload then crosses the Kernel OS Page Cache, Host CPU DRAM and NUMA, the PCIe Bus or Switch Fabric, and finally GPU HBM.
</details>

<details>
<summary>`&lt;strong>`5. How many memory copies and PCIe traversals occur in a traditional POSIX unpinned read versus a pinned read versus GPUDirect Storage (GDS)?`&lt;/strong>`</summary>

```text
Per 10 GB Payload Read:
  - Unpinned POSIX (read + .to('cuda')): 4 copies (2 PCIe traversals + 2 CPU memcpy calls, 60.0 GB host DRAM traffic)
  - Pinned (pin_memory=True):            3 copies (2 PCIe traversals + 1 CPU copy, 40.0 GB host DRAM traffic)
  - GPUDirect Storage (cuFileRead):      1 direct P2P DMA copy across PCIe (1 PCIe traversal, 0 CPU copies, 0.0 GB host DRAM payload traffic)
```
</details>

<details>
<summary>`&lt;strong>`6. In NVIDIA's `gdsio` benchmark tool, what is the difference between `-x 2` and `-x 0`, and what typical uplift does GDS show?`&lt;/strong>`</summary>

Selector `-x 2` benchmarks the CPU-mediated bounce path through pinned host memory, reaching 8.0 GB per second at 1.25 ms average latency on a four-worker 10 GB test. Selector `-x 0` benchmarks the direct GPUDirect Storage path, reaching 9.6 GB per second at 1.00 ms average latency. That is a 20 percent throughput gain and a 20 percent latency reduction, with 30 percent or higher gains observed on H100 over fast RDMA links.
</details>

<details>
<summary>`&lt;strong>`7. Why can a FUSE-based user-space filesystem never use GPUDirect Storage?`&lt;/strong>`</summary>

GPUDirect Storage requires kernel-level filesystem integration with `O_DIRECT` DMA semantics so `nvidia-fs.ko` and `libcufile` can map GPU BAR1 memory pages directly to the NVMe or RDMA NIC driver. A FUSE filesystem instead bounces every I/O buffer through a user-space daemon in host DRAM.
</details>

<details>
<summary>`&lt;strong>`8. What does `"allow_compat_mode": true` do in `/etc/cufile.json`, and why is it dangerous during cluster qualification?`&lt;/strong>`</summary>

It allows `libcufile` to silently fall back to standard POSIX host-memory reads whenever `nvidia-fs`, the filesystem mount, or the PCIe topology does not support GPUDirect Storage. During qualification, set `"allow_compat_mode": false` so any misconfiguration fails immediately instead of hiding a CPU bounce bottleneck.
</details>

<details>
<summary>`&lt;strong>`9. At a baseline of 200 MB/s per GPU, how much aggregate read bandwidth is required for an 8-GPU node, a 72-GPU GB200 NVL72 rack, and a 1,024-GPU cluster?`&lt;/strong>`</summary>

```text
- 8-GPU node:        8 x 200 MB/s = 1.6 GB/s
- 72-GPU NVL72 rack: 72 x 200 MB/s = 14.4 GB/s (14-20 GB/s planning band)
- 1,024-GPU cluster: 1,024 x 200 MB/s = 204.8 GB/s
```
</details>

<details>
<summary>`&lt;strong>`10. How much sustained write bandwidth and how many 800 MB/s Lustre OSTs are required to flush a 2 TB checkpoint in under 60 seconds?`&lt;/strong>`</summary>

```text
Required Write Bandwidth = 2,000 GB / 60 s = 33.33 GB/s
Minimum Lustre OSTs      = ceil(33.33 GB/s / 0.8 GB/s per OST) = 42 OSTs
```
</details>

<details>
<summary>`&lt;strong>`11. How does DeepSeek's Fire-Flyer File System (3FS) handle the OS page cache, and what throughput did it achieve on a 68-node cluster?`&lt;/strong>`</summary>

Random training and KV-cache reads make traditional read caching ineffective. Therefore, 3FS eliminates OS page caching completely and uses `O_DIRECT` plus RDMA over InfiniBand or RoCEv2 straight to NVMe SSDs. Across a 68-node cluster with ten 16 TB NVMe drives and dual 100 Gb/s NICs per node, 3FS achieved 6.6 TB per second of read throughput. It also served 1.4 TB per second of background traffic, scaling to 7.3 TB per second on larger clusters.
</details>

<details>
<summary>`&lt;strong>`12. What do `PIX`, `PXB`, `PHB`, `NODE`, and `SYS` mean in `nvidia-smi topo -m`, and which are acceptable for GDS?`&lt;/strong>`</summary>

Codes `PIX`, `PXB`, and `PHB` mean the GPU and NIC share a single PCIe switch, multiple PCIe switches, or the same CPU socket PCIe Host Bridge. All three stay inside the same NUMA domain and support fast GPUDirect Storage DMA. Code `NODE` crosses host bridges within a socket for roughly a 12 percent penalty. Code `SYS` crosses the inter-socket link, doubling DRAM latency and cutting bandwidth by 20 to 30 percent or more.
</details>

<details>
<summary>`&lt;strong>`13. When does the Linux OS Page Cache help AI training, and when does it cause thrashing?`&lt;/strong>`</summary>

When the dataset working set fits inside 85 percent of free host DRAM, such as a 120 GB dataset on 256 GB of RAM, the second and later epochs achieve a 95 percent page cache hit rate. Reads finish at microsecond latency. When a shuffled working set exceeds RAM, such as 4 TB on 512 GB of RAM, pages get evicted before reuse. Then `kswapd` burns CPU and I/O wait spikes to 15 percent or higher, which enabling `O_DIRECT` stops.
</details>

<details>
<summary>`&lt;strong>`14. How do you distinguish Python DataLoader transform latency from Host-to-Device (`H2D`) PCIe copy stalls in PyTorch?`&lt;/strong>`</summary>

Temporarily profile the data loader in isolation with `num_workers=0` and downstream GPU compute disabled to measure pure single-process Python read and decode time. Then wrap `.to('cuda', non_blocking=True)` with CUDA event timers. You can also inspect the copy stream lanes in Nsight Systems with `nsys profile --trace=cuda,nvtx,gds`.
</details>

<details>
<summary>`&lt;strong>`15. What four parameters should be configured on a high-throughput PyTorch `DataLoader`, and what host OS limit must accompany `pin_memory=True`?`&lt;/strong>`</summary>

Set `num_workers=8` scaled to CPU cores, `pin_memory=True`, and `persistent_workers=True` to avoid worker teardown and respawn across epochs. Also set `prefetch_factor=4` to queue batches ahead. On the host or container, set `ulimit -l unlimited` so page-locked memory allocations do not fail.
</details>

<details>
<summary>`&lt;strong>`16. Why do multi-worker PyTorch training pods in Kubernetes crash with `Bus error (core dumped)` unless `/dev/shm` is explicitly configured?`&lt;/strong>`</summary>

Kubernetes containers default `/dev/shm` to 64 MiB. Meanwhile, PyTorch data loader workers and NCCL allocate tens or hundreds of gigabytes of shared-memory tensors there. Pods must mount an `emptyDir` with `medium: Memory` and `sizeLimit: 400Gi` at `/dev/shm` on eight-GPU nodes.
</details>

<details>
<summary>`&lt;strong>`17. How does `cuda-checkpoint` (used with CRIU) differ from GPUDirect Storage and framework checkpoints (`torch.save`)?`&lt;/strong>`</summary>

The `cuda-checkpoint` utility transparently snapshots and restores an entire running CUDA process for preemption or fault migration. It uses `cuCheckpointProcessLock`, `cuCheckpointProcessCheckpoint`, `cuCheckpointProcessRestore`, and `cuCheckpointProcessUnlock`. Unlike GPUDirect Storage, it does not DMA directly from GPU memory to disk. During suspend, the CUDA driver copies device memory into host DRAM first so CRIU can save the process image.
</details>

<details>
<summary>`&lt;strong>`18. Compare `NVMe-oF/TCP`, `NVMe-oF/RDMA` (`RoCEv2`), and `InfiniBand` storage transports in terms of switch latency, port numbers, and lossless requirements.`&lt;/strong>`</summary>

```text
- NVMe-oF/TCP:          TCP port 8009 (~800 ns Ethernet switch hop, runs on lossy IP fabrics with MTU 9000)
- NVMe-oF/RDMA (RoCEv2): TCP 8009 discovery, UDP 4420 RDMA_CM (RDMA_PRTYPE 04), UDP 4791 data (700-900 ns hop, ~66% lower write latency vs TCP, requires lossless PFC/ECN/DCQCN)
- Native InfiniBand:    RDMA_PRTYPE 02, 16-bit LID up to 48,000 nodes (~300 ns switch hop, hardware CBFC credit-based flow control at 64 B/credit across 16 VLs)
```
</details>

<details>
<summary>`&lt;strong>`19. What is the difference between `PRP` (`PRP1`/`PRP2`), `SGL`, and `NSID` inside an NVMe or NVMe-oF command capsule?`&lt;/strong>`</summary>

The `NSID`, or Namespace ID, identifies the logical storage volume on the target NVMe controller. By contrast, `PRP1` and `PRP2` are 64-bit Physical Region Page pointers, and `SGL` is a Scatter-Gather List descriptor. Both specify the host or GPU BAR1 memory buffer addresses for DMA placement inside the 64-byte NVMe read (`0x02`) or write (`0x01`) command.
</details>

<details>
<summary>`&lt;strong>`20. How do NVIDIA DALI, `nvJPEG`, and the Blackwell Hardware Decompression Engine shift the storage-to-GPU bottleneck?`&lt;/strong>`</summary>

They allow datasets to stay compressed on disk in formats like JPEG, LZ4, Snappy, or Deflate. Smaller payloads then travel across the network and PCIe or NVLink-C2C, which runs at up to 900 GB per second bidirectional on GB200. DALI, `nvJPEG`, and the on-die Blackwell Decompression Engine unpack and augment data directly on the GPU. That avoids burning eight CPU cores or bouncing decoded pixels between host and device memory.
</details>

---

## Sources and review notes

### 1. Primary `nvidia-devops` and Gem Book Sources

```text
Source Map & Consolidated Facts:
  1. Migrated from nvidia-devops:
     - nvidia-zero-to-hero/volume-15/index.md
     - nvidia-zero-to-hero/volume-15/chapter-01-why-ai-storage-is-different.md (7.2 PB Lustre metadata bottleneck: 48 OSTs @ 800 MB/s = 38.4 GB/s, 128 workers @ 150 MB/s = 19.2 GB/s expected vs 4.3 GB/s observed on 18,000,000 220 KB files generating 87,040 opens/s vs 50,000 MDS ceiling, fixed by 750,000 10 MB shards reaching 18.6 GB/s and 91% GPU util; 10-node 80-A100 15,000,000-file incident in 40 GB fixed by 50 x 800 MB shards restoring 1.42 GB/s and 88% GPU util)
     - nvidia-zero-to-hero/volume-15/chapter-02-the-ai-data-path-from-storage-to-gpu.md (8-layer data path: iostat, brw_stats, ethtool/iperf3, vmstat, numactl, nvidia-smi topo -m, nvidia-smi dmon; 120 ms -> 30 ms pin_memory fix lifting 45 GB/s -> 58 GB/s and 78% -> 94% GPU util; 500 GB checkpoint on 40 GB/s array 45 s stall fixed by 25-32 OST striping)
     - nvidia-zero-to-hero/volume-15/chapter-12-volume-15-summary.md
     - nvidia-zero-to-hero/volume-15/labs/lab-01-baseline-an-ai-storage-path.md (5-stage node baseline script)
     - volume-06/03-ai-storage-data-pipelines-masterclass.md (4-tier storage hierarchy Tier 0 HBM through Tier 3 S3, fio/mdtest commands, WEKA CSI + /dev/shm 400Gi + cufile.json manifests, D-state hang rpc_wait_bit_killable diagnosis, 2 TB in 60 s = 33.33 GB/s checkpoint sizing)
  2. Book Corpus Sources:
     - Chris Fregly, AI Systems Performance Engineering (ai-systems-performance-engineering, ASP), Ch. 5 (GPU-Based Storage I/O Optimizations): 200 MB/s per GPU, 1.6 GB/s per 8-GPU node, 14-20 GB/s (14.4 GB/s) per 72-GPU GB200/GB300 NVL72 rack; blk-mq (none / mq-deadline) and read_ahead_kb (128 KB default, blockdev --setra); GPUDirect Storage (cuFileRead, cuFileReadAsync, O_DIRECT, VAST +20% on A100 and +30%+ on H100); gdsio (-x 2 CPU 8.0 GB/s @ 1.25 ms vs -x 0 GDS 9.6 GB/s @ 1.00 ms, +20%); cuda-checkpoint + CRIU; DeepSeek Fire-Flyer File System (3FS, 6.6 TB/s + 1.4 TB/s on 68 nodes with 10x 16 TB NVMe and dual 100 Gb/s vs Ceph ~1.1 TB/s, up to 7.3 TB/s); NFS client tuning (rsize=1048576,wsize=1048576,noatime,async,actimeo=60,lookupcache=pos); Blackwell Decompression Engine (LZ4, Snappy, Deflate, nvJPEG, NVLink-C2C 900 GB/s); PyTorch DataLoader (pin_memory=True, persistent_workers=True, prefetch_factor=4), NVIDIA DALI (800% -> 200% CPU), and NeMo Curator (.bin/.idx).
     - Wissamawad et al., AI Data Center Network Design and Technologies (ai-data-center-network-design-and-technologies, ADCN), Ch. 9 (Storage Network Design and Technologies): AI storage lifecycle stages; PCIe Gen5 (32 GT/s, ~100 ns latency, ~63 Gbps/lane, 64 GB/s x16) vs InfiniBand (~300 ns switch hop, 16-bit LID up to 48,000 nodes, 16 VLs, CBFC 64 B/credit) vs Ethernet (700-900 ns switch hop, MTU 9000); Fabric A/B separation (1:3 oversubscription, > 40 km inter-site replication); NVMe-oF/TCP (port 8009, IC Req PDU, CapsuleCmd 0x01, C2HData 0x04, H2CData 0x03, opcode 0x02 read / 0x01 write, NSID, PRP1/PRP2, SGL) and NVMe-oF/RDMA over RoCEv2 (UDP 4420 RDMA_CM, UDP 4791 BTH/RETH, RDMA_PRTYPE 04 RoCEv2 / 02 IB / 05 iWARP, ~66% lower write latency).
```

### 2. Lab verification and labelled inferences

- **Verified in this environment:** `python3 -B code/part13/ai_data_path_lab.py` passes all 26 checks using Python standard library models in `code/part13/ai_data_path.py`.
- **Not run on live hardware here:** All `iostat`, `lctl`, `lfs`, `fio`, `mdtest`, `gdscheck`, `gdsio`, `ethtool`, `iperf3`, `ibstat`, `numactl`, and `kubectl` commands are marked `(untested here)` and derived from the cited reference outputs.
- **Labelled inferences:** The 40.0 GB versus 60.0 GB host DRAM traffic accounting per 10 GB read and the multiplicative NUMA plus `SYS` penalty model in `code/part13/ai_data_path.py` are deterministic engineering models constructed from the penalty bands reported in the source chapters.

