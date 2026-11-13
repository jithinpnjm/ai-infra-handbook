---
id: "c09-04"
title: "9.4 Grace CPU, GH200 and GB200 superchips"
sidebar_label: "9.4 Grace CPU, GH200 and GB200 superchips"
sidebar_position: 4
description: "Inside the NVIDIA Grace Arm Neoverse V2 CPU, the 900 GB/s coherent NVLink-C2C interconnect, the GH200, GB200, and GB300 Superchip modules, unified virtual memory tiering, and SuperOffload/GraceAdam runtime tuning, verified by a 30-check Python lab."
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "none (design / reading)"
---

# 9.4 Grace CPU, GH200 and GB200 superchips

| Field | Value |
|---|---|
| **Status** | Drafted (`grace_superchips_lab.py`: 30 checks pass; hardware commands **untested** on live Grace Superchip nodes) |
| **Level** | Intermediate |
| **Priority tier** | 1b |
| **Lab venue** | none (design / reading) + self-checking Python model (`code/part09/grace_superchips_lab.py`) |
| **Part** | Part 9: NVIDIA systems and reference architectures |
| **Sources used** | `nvidia-devops` V4 Ch. 7; `nvidia-devops` V5 Ch. 7; *AI Systems Performance Engineering* Ch. 2, Ch. 3, Ch. 13; *Distributed AI Systems* Ch. 2; *NVIDIA DGX SuperPOD Reference Architecture Featuring NVIDIA DGX GB300 Systems* (`superpod-gb300-ra`) |

## Why this matters for AI infrastructure

Picture a recommendation model whose embedding tables are too large for the GPU, so they sit in host RAM. Each training step asks the GPU to fetch a few rows from those tables. The GPU finishes its math in a moment and then waits for the rows to arrive. Your utilization graph shows busy GPUs only part of the time, and nothing in the logs explains why.

For fifteen years, accelerated computing lived with that kind of compromise. GPU High Bandwidth Memory (HBM, the fast memory package mounted next to the GPU die) climbed into the multi-terabyte-per-second range. The host CPU, however, stayed behind a narrow PCIe bus. PCIe, short for Peripheral Component Interconnect Express, is the general-purpose bus that connects cards to a server board. Long-context language models that offload key-value caches to host memory paid the same toll, and so did graph networks that sample huge datasets. In each case the accelerator sat idle while bytes crawled across an I/O bus that was designed for network cards and storage drives.

To remove this wall between the CPU and GPU, NVIDIA designed its own data center processor. The Grace CPU pairs 72 Arm Neoverse V2 cores with fast on-package LPDDR5X memory. Arm Neoverse V2 is a CPU core design from Arm, and LPDDR5X is a low-power memory standard used in servers. The CPU bonds directly to Hopper and Blackwell GPUs over NVLink-C2C, a chip-to-chip link, at 900 GB/s bidirectional. The link carries full hardware cache coherence, so the CPU and the GPU always see the same current copy of a value, and a single virtual address space, so both use the same pointers. Understanding how Grace, GH200, GB200, and GB300 Superchips work is essential for running modern rack-scale clusters. You must also learn what they do not solve automatically. GPU-to-GPU caches remain non-coherent across NVSwitch, and hot tensors must stay in HBM.

:::info Corpus scope note
The standalone *NVIDIA Grace CPU Superchip Architecture Whitepaper* and *NVIDIA GH200 Grace Hopper Superchip Datasheet* are not among the sources this chapter used. The architecture figures, the NVLink-C2C coherence model, the memory placement rules, and the SuperOffload and GraceAdam methods come from the books cited in the Sources section.
:::

## Prerequisites and outcomes

**Prerequisites:**
- Chapters 9.1 to 9.3 covering DGX and HGX system families, PCIe Gen5 switch complexes, and NUMA domains.

This chapter starts with the cost of the PCIe bus and works up to the Grace CPU itself. It then covers the coherence rules that tie the CPU to the GPU, the lineup of Superchip modules and the roadmap after Blackwell, and the operating system settings that make Grace run well. Those settings are NUMA pinning (non-uniform memory access, which means binding work to the memory closest to it), hugepages, and SuperOffload.

---

## Concepts: basics → intermediate → advanced

## 1. The bottleneck: the PCIe tax on x86 GPU servers

Imagine a training job whose data fits in the server's ordinary RAM but not in the GPU's memory. The job starts, and it runs far slower than expected. Platform engineers and ML researchers meet this slowdown often, and it usually traces back to one narrow link. When a model or dataset outgrows GPU memory on a traditional x86 server, training and inference speeds collapse. The culprit is the narrow PCIe bus separating the Intel Xeon or AMD EPYC processor from the GPU. x86 is the instruction set family that Intel and AMD server processors share, and DDR5 is the current generation of server memory.

In a standard x86 server, the CPU and GPU live on separate boards with separate physical memory pools. Think of the GPU HBM3e memory as a factory floor moving materials on wide conveyor belts at 8,000 GB/s. The host CPU DDR5 RAM is a giant warehouse across the street. Connecting them with a 16-lane PCIe Gen5 slot is like linking that warehouse to the factory with a single garden hose. As long as all materials fit inside the factory floor, production flies. The moment the factory fetches parts from across the street, the machines grind to a halt.

The analogy has a limit, but it points at the right question. The question is not how fast the factory is. The question is how often the factory has to reach across the street. If the working set stays on the factory floor, the slow link barely matters. If the working set keeps moving back and forth, the link decides the speed of the whole plant.

### 1.1 Quantifying the PCIe Gen5 bandwidth gap

Suppose a GPU needs a tensor that sits in host memory. How long does the trip take, compared with reading from the GPU's own memory? The table below compares the three memory and interconnect tiers inside a traditional x86 Hopper or Blackwell server. Read each row as a question about speed. How fast can the GPU reach its own memory, how fast can GPUs talk to each other, and how fast can the GPU reach the host? The last column turns each answer into a multiple of the PCIe baseline, which makes the gap easier to see.

| Memory or Interconnect Tier | Hardware Example | Unidirectional Bandwidth | Bidirectional or Total Bandwidth | Relative Speed vs PCIe Gen5 x16 |
|---|---|---|---|---|
| **GPU HBM3 / HBM3e** | H100, H200, B200 | N/A | 3,350 GB/s (H100), 4,800 GB/s (H200), 8,000 GB/s (B200) | 50× to 125× faster |
| **GPU-to-GPU NVLink** | Hopper NVLink 4, Blackwell NVLink 5 | 450 GB/s or 900 GB/s | 900 GB/s (Hopper) or 1,800 GB/s (Blackwell) | 7× to 14× faster |
| **CPU-to-GPU PCIe Gen5 x16** | x86 Host to GPU | 64 GB/s | 128 GB/s | 1× baseline |

Whenever a workload exceeds local HBM capacity and spills into host CPU memory, it pays the PCIe tax. Three common AI workloads pay it most often.

1. Giant recommendation models store multi-terabyte embedding tables in host RAM and query them on every mini-batch.
2. Long-context KV-cache offloading and MoE streaming push inactive key-value cache blocks or unscheduled Mixture-of-Experts weights to host DDR5, and the decode loop stalls when transfers are capped at 64 GB/s.
3. Massive graph neural networks run into the same wall. A fraud-detection graph of 1.2 TB cannot fit inside 80 GB of GPU HBM, and streaming those node features across PCIe Gen5 leaves the GPU compute cores idle for days.

The three workloads share one pattern. Each one keeps reaching for data that does not fit where the GPU can use it at full speed. A mixture-of-experts model, for example, activates only a few experts for each token, so the rest of its weights wait in host memory. Every time one of those waiting experts is needed, the transfer crosses the slow bus.

```text
Portfolio GNN host-to-GPU transfer time on PCIe Gen5 x16 (my inference):
Dataset size: 1.2 TB = 1,200 GB (from Volume 04 Chapter 7 customer scenario)
PCIe Gen5 x16 unidirectional limit: 64 GB/s
Pure bus transfer time per pass = 1,200 GB / 64 GB/s = 18.75 seconds
```

The arithmetic in the block is simple division. The dataset size divided by the bus rate gives the minimum time to move the dataset once. That number is a floor, not an estimate of the whole training step, because the bus has to carry the data even when nothing else is slow.

:::tip In one minute
- A 16-lane PCIe Gen5 bus delivers only 64 GB/s in one direction and 128 GB/s bidirectional, which is over 50× slower than Hopper HBM3 and 125× slower than Blackwell HBM3e.
- Workloads that spill embeddings, graph features, optimizer states, or long-context KV caches to host RAM pay the PCIe tax and starve the GPU SMs.
:::

---

## 2. Inside the NVIDIA Grace CPU: 72 Arm Neoverse V2 cores and on-package LPDDR5X

Picture a dense, liquid-cooled AI rack where the power budget is already committed to the GPUs. Every watt that the host CPU and its memory slots burn is a watt that cannot go to a GPU. General-purpose x86 server processors burn hundreds of watts and take up huge board area on legacy instruction decoders and bulky DDR5 DIMM slots. A DIMM, or dual inline memory module, is the removable memory stick that plugs into a server board. NVIDIA needed a compact, high-bandwidth host processor built specifically to feed accelerators.

To remove the CPU-to-GPU bottleneck, NVIDIA engineered the Grace CPU from a clean sheet of paper. A general-purpose x86 CPU acts like a Swiss Army knife carrying decades of legacy attachments for older desktop and enterprise software. By contrast, the Grace CPU is a purpose-built fuel pump. Its sole job is to pre-process tensors, orchestrate CUDA graphs, and stream memory into attached GPUs at maximum bandwidth per watt. A CUDA graph is a recorded sequence of GPU work that the CPU can launch in one step, which cuts the back-and-forth of launching each piece separately.

```mermaid
flowchart LR
    subgraph GracePkg["NVIDIA Grace CPU Package (60W–200W Memory+CPU Envelope)"]
        CORES["72x Arm Neoverse V2 Cores (aarch64)<br/>Armv9 Scalable Vector Extension (SVE)<br/>32 Vector + 16 Predicate Registers"]
        SCF["Scalable Coherency Fabric (SCF)<br/>Mesh Interconnect & Distributed Cache"]
        LPDDR["On-Package Soldered ECC LPDDR5X<br/>Up to 480–512 GB @ ~500 GB/s"]
        C2C["NVLink-C2C Interface<br/>900 GB/s Bidirectional (<5 pJ/bit)"]
        CORES <--> SCF
        LPDDR <--> SCF
        SCF <--> C2C
    end
```

The diagram shows the package as a small set of blocks. The cores on the left do the computing. The memory on the right holds the data. The fabric in the middle connects them and also connects the cores to the link that leads to the GPU. Data can move from memory to a core, and from a core out to the GPU, without leaving the package.

### 2.1 72 Arm Neoverse V2 cores and Armv9 Scalable Vector Extension

Suppose a team moves a data preprocessing job from an x86 server to a Grace node. The job starts, and then one library fails to load. The library was built for x86 and cannot run on the Arm processor without a rebuild. Problems like this are the first thing a team meets when it changes architectures.

Instead of licensing x86, NVIDIA built Grace around the Armv9 architecture. Each socket integrates 72 high-performance Arm Neoverse V2 cores linked by a high-bandwidth on-die mesh called the Scalable Coherency Fabric. All 72 cores feed data loaders, tokenizers, and network rings without legacy x86 decode overhead. A tokenizer turns raw text into the integer token IDs that a language model reads, and a data loader is the code that prepares batches for the GPU.

For CPU-side math such as offloaded Adam optimizer steps or data augmentations, Grace implements the Arm Scalable Vector Extension. SVE provides 32 vector registers and 16 predicate registers per core. A vector register holds several numbers that one instruction can process together, and a predicate register marks which of those numbers should take part. Operators migrating containers from x86 servers must keep one compatibility rule in mind. Any C++ or Cython Python wheel that hard-codes x86 AVX2 or AVX-512 intrinsics will fail on Grace and must be compiled for `aarch64` and Arm SVE. A wheel is a prebuilt Python package, and an intrinsic is a low-level instruction written directly into the code.

### 2.2 Soldered on-package ECC LPDDR5X memory

Look at a Grace Superchip board and you will notice that there are no DIMM slots. The memory is part of the module itself, which changes what you can upgrade and what you can replace in the field. Instead of using socketed DDR5 RDIMMs, NVIDIA solders low-power server-grade ECC LPDDR5X memory directly onto the module substrate millimeters from the Grace CPU die. ECC, or error-correcting code, lets the memory detect and fix single-bit errors on its own. That physical proximity delivers high sustained bandwidth inside a fraction of the power and board area required by 8-channel or 12-channel x86 DDR5 subsystems. The saved power and board area go directly to the GPUs and liquid cold plates.

| Grace CPU Subsystem Feature | Specification | Operational Impact |
|---|---|---|
| **CPU Core Architecture** | 72 Arm Neoverse V2 cores (`aarch64`) per Grace socket | Drives data loaders, tokenization, and control loops without x86 bloat |
| **Vector Execution Units** | Armv9 SVE with 32 vector registers and 16 predicate registers | Accelerates vectorized GraceAdam CPU optimizer updates |
| **On-Package Memory Capacity** | Up to 480 GB (500 GB to 512 GB on high-capacity GH200 and GB300 SKUs) | Holds giant embedding tables, graph features, and offloaded KV caches |
| **Sustained Memory Bandwidth** | ~500 GB/s per Grace CPU | Matches or beats bulky multi-channel x86 DDR5 DIMM banks |
| **Combined CPU + Memory Power** | 60W to 200W total envelope | Frees rack power and PCB area for high-TDP GPUs and cold plates |

Read the table as a set of trade-offs. The left column names the part, the middle column gives its specification, and the right column says what that specification changes in daily work. The memory row is the one most people miss. A large capacity sitting next to the CPU is useful only if the CPU and GPU can reach it fast enough, and the bandwidth row answers that question.

:::tip In one minute
- The NVIDIA Grace CPU integrates 72 Arm Neoverse V2 cores with Arm SVE vector units for fast data preprocessing and CPU-offloaded optimizer math.
- Instead of bulky DDR5 DIMM slots, Grace solders up to 480–512 GB of ECC LPDDR5X directly onto the package, delivering ~500 GB/s within a 60W–200W power envelope.
:::

---

### The Grace CPU as a data feeder

A training loop that stalls between steps often has its GPUs waiting for the next batch. The GPU is ready to work, but the data has not arrived. A GPU is only as fast as the data it receives. The design goal for Grace is that the CPU should never be the bottleneck when it shovels data to the GPUs. Grace can stream data from storage. It can also run on-the-fly transforms such as tokenization or data augmentation, then feed the results to the GPUs over NVLink-C2C. If part of the workload suits a CPU better, the Grace cores can handle it and leave the results where the GPUs can read them at once.

The two chips complement each other. The CPU covers the work GPUs do poorly, such as random memory access and control-heavy code. The GPUs handle the number crunching that a CPU cannot keep up with. The low-latency link also lets them trade tasks cheaply. Launching a GPU kernel from the CPU is much faster here, because the command does not cross a slow PCIe bus. A kernel is a function that runs on the GPU. The launch is like calling a fast local function instead of a slow remote one.

## 3. NVLink-C2C and the hardware-coherent unified memory model

Picture a fine-tuning job that outgrows GPU memory. On a traditional server, the engineer writes explicit copy commands to move each block of data to and from the GPU, and manages a special staging buffer for each copy. Weeks of such code are common. Having a fast Arm CPU with half a terabyte of LPDDR5X only helps if the attached GPU can read and write that memory without squeezing through a 64 GB/s PCIe straw. On traditional systems, developers also waste weeks writing explicit host-to-device memory copies and managing pinned staging buffers whenever data spills out of GPU HBM. A pinned buffer is host memory that the operating system is not allowed to move, so the GPU can copy from it directly.

The bridge that removes both bottlenecks is NVLink-C2C. NVLink-C2C is a custom, ultra-short-reach die-to-die and package-to-package coherent interconnect etched directly onto the Superchip substrate between the Grace CPU and its paired Hopper or Blackwell GPUs. Die-to-die means the link joins two chips in the same package, and coherent means both sides agree on the latest value stored in memory.

### 3.1 Physical specs of NVLink-C2C vs PCIe Gen5 x16

Consider two quotes for the same rack, one built on PCIe and one built on NVLink-C2C. The spec sheet is the first place the difference shows up. The table compares the two links row by row. Start with the bandwidth rows, since they answer how much data moves per second. Then look at the energy row, which matters in a rack that already draws a lot of power. The last two rows explain what a programmer sees, which is the part that changes the code.

| Metric | Traditional x86 PCIe Gen5 x16 | NVIDIA NVLink-C2C (Superchip) | Advantage (NVLink-C2C vs PCIe Gen5) |
|---|---|---|---|
| **Unidirectional Bandwidth** | 64 GB/s | 450 GB/s | 7.03× higher one-way throughput |
| **Bidirectional Bandwidth** | 128 GB/s | 900 GB/s | 7.03× higher aggregate throughput |
| **Energy Efficiency** | ~25+ picojoules/bit across PCB traces | `< 5 picojoules/bit` | `> 5×` more energy-efficient per bit moved |
| **Memory Address Space** | Separate host RAM and GPU BAR spaces | Single Unified Virtual Address Space with hardware ATS | CPU and GPU threads share standard pointers without explicit `cudaMemcpy()` |
| **Hardware Cache Coherence** | Non-coherent by default | Full hardware cache coherence between Grace CPU caches and GPU memory | Zero software staging buffer overhead for CPU–GPU access |

Two terms in the table need a plain definition. A picojoule is one trillionth of a joule, and energy per bit tells you how much power the link spends for each bit it moves. ATS, or Address Translation Services, is the hardware that lets the GPU translate a CPU address into the physical location of the data without help from the driver.

### 3.2 What hardware cache coherence means and the crucial GPU-to-GPU boundary

A developer who reads that the GPU can see CPU memory may assume that every GPU in a rack can also see every other GPU's memory with the same guarantees. That assumption is wrong, and this section explains why.

On a Grace Hopper or Grace Blackwell Superchip, NVLink-C2C implements hardware Address Translation Services and full cache coherence across the Grace CPU and its paired GPUs. A CUDA kernel running on the GPU can dereference a pointer residing in the Grace CPU LPDDR5X memory at 450 GB/s per direction without a single `cudaMemcpy()` call. A kernel that dereferences a pointer reads the data at that address directly. The programmer does not need to allocate a page-locked staging buffer for that transfer.

On a DGX GB300 compute tray, which houses two GB300 Superchips, a coherent NVLink-C2C link also bridges the two Superchips together. That bridge allows both Grace CPUs and all four B300 GPUs on the tray to act as a single logical unit under one Linux OS instance. The operating system sees one machine, even though the hardware is made of two modules.

:::caution Critical distinction: CPU–GPU coherence vs GPU–GPU non-coherence
Do not confuse CPU-to-GPU coherence over NVLink-C2C with GPU-to-GPU memory sharing over NVSwitch. As detailed in *AI Systems Performance Engineering*, only the CPU-to-GPU path over NVLink-C2C is hardware cache-coherent. Across multiple GPUs connected by NVLink and NVSwitch, there is a shared global physical address space for peer-to-peer loads and stores. However, GPU L1 and L2 caches are not globally hardware cache-coherent across GPUs. Multi-GPU communication still requires explicit software synchronization and memory ordering via NCCL collectives or NVSHMEM symmetric memory barriers.
:::

The caution box is the most important idea in this section. Shared addressing and shared caching are different properties. A GPU can read another GPU's memory through the switch and still see a stale copy in its own cache, unless the software forces an update. NCCL, the NVIDIA collective communication library, and NVSHMEM, a library for symmetric memory across GPUs, are the tools that provide that ordering.

### 3.3 Real-world impact: solving the 1.2 TB Graph Neural Network bottleneck

Return to the financial-services team from Section 1. Their fraud-detection Graph Neural Network took 4 days per training epoch on an x86 and H100 PCIe server. An epoch is one full pass over the training data. Streaming 1,200 GB of graph node features across a 64 GB/s PCIe Gen5 slot took 18.75 seconds of pure bus transfer time per pass.

When the team moves that workload onto two GH200 Grace Hopper Superchips, the entire dataset fits inside the hardware-coherent memory pool. When the Hopper GPUs sample graph neighbors stored in Grace LPDDR5X, they read the features directly over the NVLink-C2C highway. That direct memory access collapses epoch times from days to hours. The change comes from where the data lives. The features no longer sit behind a narrow bus that the GPU has to cross every time it needs a neighbor.

```text
Two-Superchip GH200 GNN memory and transfer math (my inference from code/part09/grace_superchips.py):
Per-Superchip coherent memory (144 GB SKU): 480 GB LPDDR5X + 144 GB HBM3e = 624 GB
Two-Superchip total coherent pool: 2 × 624 GB = 1,248 GB
Dataset placement (1,200 GB total): 240 GB hot GNN weights/activations in HBM3e + 960 GB feature tables in LPDDR5X
NVLink-C2C unidirectional pass time: 1,200 GB / 450 GB/s = 2.67 seconds (7.03× faster than 18.75 seconds on PCIe Gen5)
```

Read the block as a placement plan. The first lines add up the memory the two Superchips provide. The next line splits the dataset between fast HBM and the larger LPDDR5X pool. The last line gives the time for one pass over the features on the faster link. The split matters because the hot part of the work, the weights and activations that the GPU touches constantly, stays in HBM, and the large feature tables sit in the slower but roomier memory.

:::tip In one minute
- NVLink-C2C links the Grace CPU to its paired GPUs at 900 GB/s bidirectional, which is 7.03× faster than PCIe Gen5 x16 while consuming less than 5 picojoules per bit.
- Only the CPU-to-GPU NVLink-C2C path is hardware cache-coherent with ATS unified virtual addressing. GPU-to-GPU caches across NVSwitch are not globally coherent and require NCCL or NVSHMEM synchronization.
:::

---

### Fitting a 500 GB model on one superchip

A researcher has a 500 GB model and a GPU whose HBM is much smaller. Before this design, the choices were to split the model across several GPUs or to spill part of it to slower storage. Both options add complexity to the code and the schedule. Memory size used to be the hard limit. A model too big for one GPU's HBM had to be split across several GPUs or spilled to slower storage. On a GB200 superchip, the GPU can use the CPU's LPDDR5X as overflow. A model of about 500 GB is too large for one GPU's HBM, but it fits in one superchip. The superchip has 192 GB of HBM (180 GB usable) and about 500 GB of CPU memory, so the model runs without partitioning across GPUs.

The GPU pulls the extra data from CPU memory when it needs it, and the overflow does not have to go out to NVMe storage or across a network. NVMe is solid-state storage that connects over PCIe, and it is far slower than memory. The trade-off is speed. Reading LPDDR5X over NVLink-C2C has higher latency and about one-tenth the bandwidth of local HBM. A smart runtime keeps hot data in HBM and uses CPU memory for the rest. Prefetch the data you can see coming. Prefetching means copying data into HBM before the kernel that needs it starts. Memory size stops being a hard wall, but placement still decides how fast the model runs.

## 4. The Superchip lineup: Grace CPU Superchip, GH200, GB200, GB300, and the Vera Rubin roadmap

Imagine you are sizing the racks for a new AI factory. You must pick between CPU-only Grace nodes, single-GPU Grace Hopper nodes, and dual-GPU Grace Blackwell compute trays. Each choice sets how much HBM and how much CPU memory the rack will hold. Cluster architects make this choice before the hardware arrives. Picking the wrong module or misreading memory SKU tables leads to under-provisioned HBM capacity or wasted rack power. A SKU, or stock-keeping unit, is the specific model variant that the vendor sells, and two SKUs of the same module can carry different memory.

NVIDIA packages the Grace CPU and NVLink-C2C into four production Superchip modules today, with the next-generation Vera Rubin and Feynman architectures on the roadmap. The diagram below shows how each module pairs its CPU and GPUs.

```mermaid
flowchart TD
    subgraph GCPU["1. Grace CPU Superchip (CPU-Only HPC)"]
        GC1["Grace CPU 0<br/>(72 Neoverse V2 Cores + 480 GB LPDDR5X)"] <-->|"NVLink-C2C<br/>900 GB/s"| GC2["Grace CPU 1<br/>(72 Neoverse V2 Cores + 480 GB LPDDR5X)"]
    end
    subgraph GH["2. GH200 Grace Hopper Superchip (1:1 CPU:GPU)"]
        GH_C["1x Grace CPU<br/>(72 Cores + 480–512 GB LPDDR5X)"] <-->|"NVLink-C2C<br/>900 GB/s"| GH_G["1x Hopper H100 (96 GB HBM3)<br/>or H200 (144 GB HBM3e)"]
    end
    subgraph GB["3. GB200 / GB300 Grace Blackwell Superchip (1:2 CPU:GPU)"]
        GB_C["1x Grace CPU<br/>(72 Cores + 480–500 GB LPDDR5X)"] <-->|"NVLink-C2C<br/>900 GB/s"| GB_G["2x Blackwell B200 (384 GB HBM3e)<br/>or 2x B300 (576 GB HBM3e)"]
    end
```

Read the diagram as three boxes with the same link in each. The box changes with the module. The GPU count changes from zero to one to two, and the memory on each side changes with it. Keep that picture in mind for the rest of the section, since the comparison table below depends on it.

### 4.1 Complete comparison of Grace-based Superchip modules

Imagine a buyer choosing among Superchip modules for a rack, where each module changes how much memory every node carries. Read this table one row at a time. Each row is one module, and each column answers a sizing question. The CPU column tells you how many cores you get. The memory column tells you the size and speed of the CPU-attached memory. The GPU columns tell you what sits on the other side of the link, and the last two columns give the total memory pool and the power envelope. Power matters because it decides the cooling you need.

| Superchip Module | CPU Configuration | On-Package LPDDR5X & Bandwidth | Paired GPU(s) | Total GPU HBM & Bandwidth | Total Coherent Memory Pool | Module TDP Envelope |
|---|---|---|---|---|---|---|
| **Grace CPU Superchip** | 2x Grace CPUs (144 Arm Neoverse V2 cores) linked via NVLink-C2C | Up to 960 GB ECC LPDDR5X @ ~1.0 TB/s | None (CPU-only HPC / cloud server) | 0 GB | 960 GB | ~500W (including memory) |
| **GH200 Grace Hopper (96 GB SKU)** | 1x Grace CPU (72 Arm cores) | 480 GB (or 512 GB SKU) LPDDR5X @ ~500 GB/s | 1x Hopper GPU (H100-class) | 96 GB HBM3 @ 4.0 TB/s | 576 GB (480+96) or 608 GB (512+96) | ~1,000W |
| **GH200 Grace Hopper (144 GB SKU)** | 1x Grace CPU (72 Arm cores) | 480 GB LPDDR5X @ ~500 GB/s | 1x Hopper H200-class GPU | 144 GB HBM3e @ 4.9 TB/s | 624 GB (480 + 144 GB) | ~1,000W |
| **GB200 Grace Blackwell Superchip** | 1x Grace CPU (72 Arm cores) | Up to 480 GB LPDDR5X @ ~500 GB/s | 2x Blackwell B200 GPUs (dual-reticle dies each) | 384 GB HBM3e (2 × 192 GB, or 360 GB usable on 180 GB SKU) @ 16.0 TB/s | Up to 864 GB (480 + 384 GB) per Superchip | ~2,700W (liquid-cooled) |
| **GB300 Grace Blackwell Ultra Superchip** | 1x Grace CPU (72 Arm cores) | ~500 GB LPDDR5X @ ~500 GB/s (18 TB across 36 modules) | 2x Blackwell Ultra B300 GPUs (1.5× FP4 compute vs B200) | 576 GB HBM3e (2 × 288 GB, 1.5× B200) @ 16.0 TB/s | ~1,076 GB (~1.08 TB) per Superchip (~2.15 TB per 2-superchip compute tray) | ~2,800W+ (liquid-cooled) |

The rows show that the Superchip family is not one product. The first row has no GPU at all, which makes it a CPU server. The GH200 rows share a CPU but come with two different GPU memory sizes, so two GH200 nodes can have different pools. The GB200 and GB300 rows double the GPU count and therefore the HBM. Read a row before you trust a memory figure, and check the SKU name first.

:::note Reconciling GH200 and GB200 memory SKU numbers across sources
Different books and reference guides quote either raw or usable memory capacities depending on the SKU. The table below reconciles all figures from the sources used in this handbook.
:::

The next table lists each source and the figure that source gives. When two sources disagree, the difference usually comes from the SKU or from whether a figure counts raw or usable memory. The table shows where each number comes from, so you can check it against the vendor sheet for your own hardware.

| Platform | Source Citation | LPDDR5X Capacity | GPU HBM Capacity | Combined Memory Pool |
|---|---|---|---|---|
| **GH200 (96 GB / 144 GB)** | `nvidia-devops` V4 Ch 7 | 480 GB | 96 GB HBM3 or 144 GB HBM3e | 576 GB or 624 GB per Superchip |
| **GH200 (512 GB variant)** | *Distributed AI Systems* Ch 2 | 512 GB | 96 GB HBM3 | 608 GB per Superchip |
| **GB200 Superchip** | `nvidia-devops` V4 Ch 6/7 & *AI Systems Performance Engineering* Ch 2 | 480 GB | 384 GB HBM3e (2 × 192 GB) | 864 GB per Superchip |
| **GB200 NVL72 (36 Superchips)** | *AI Systems Performance Engineering* Ch 2 NVL72 table | ~17 TB | 13.4 TB HBM3e (180 GB per B200 GPU) | ~30 TB across 36 Superchips |
| **GB300 NVL72 (36 Superchips)** | *AI Systems Performance Engineering* Ch 2 | ~18 TB (~500 GB per Superchip) | ~20.7 TB HBM3e (288 GB per B300 GPU, 576 GB per Superchip) | ~38 TB across 36 Superchips |

### 4.2 Why GB200 and GB300 move from a 1:1 to a 1:2 CPU-to-GPU ratio

Picture two rack designs side by side. One has a Grace CPU for every Hopper GPU. The other has a Grace CPU for every two Blackwell GPUs. The second design has fewer CPUs per GPU, and that difference is the reason the GB200 and GB300 modules look the way they do. The shift from GH200 to GB200 is the most visible change in the lineup.

Notice the architectural shift from GH200, which pairs one Grace CPU with one Hopper GPU, to GB200 and GB300, which pair one Grace CPU with two Blackwell GPUs. A single 72-core Grace CPU with 500 GB/s of LPDDR5X and 900 GB/s of NVLink-C2C has more than enough CPU cores and memory capacity to drive two GPUs simultaneously. Providing 36 Arm cores per GPU while pairing one Grace CPU with two Blackwell GPUs doubles GPU compute density inside every 1U tray. A 1U tray is a server that is one unit tall in the rack, and a rack unit is the standard height measure for rack equipment.

In a GB200 or GB300 NVL72 compute tray, two Superchips sit side-by-side and are bridged by a coherent NVLink-C2C link. A single Linux OS kernel manages both Grace CPUs and all four GPUs as one node. The kernel is the core of the operating system, and it schedules every process across the tray's hardware.

```text
NVL72 compute tray and full-rack scaling math:
1 compute tray (1U) = 2 Superchips = 2 Grace CPUs (144 Arm cores) + 4 Blackwell GPUs
18 compute trays per NVL72 rack = 36 Superchips = 36 Grace CPUs (2,592 Arm Neoverse V2 cores) + 72 Blackwell GPUs
```

The math is a straight multiplication. Each tray carries two Superchips, and each Superchip carries one CPU and two GPUs. The rack repeats that tray 18 times. The result is the rack total that you see in later tables, and the same multiplication is the first thing to check when a quoted rack figure looks wrong.

### 4.3 The multi-year Superchip roadmap: Vera Rubin and Feynman

A capacity plan that covers three or four years has to say what hardware will arrive next. The roadmap answers that question, but it describes plans rather than shipping products, so treat each row as a target to verify when it becomes available. As documented in *AI Systems Performance Engineering* Chapter 2, NVIDIA continues the one-CPU-to-two-GPU Superchip design across three upcoming generations.

| Generation & Target Year | CPU Architecture & Memory | GPU Architecture & HBM | Interconnect & Rack Scale |
|---|---|---|---|
| **Vera Rubin (`VR200`, 2026)** | 1x Vera Arm CPU (TSMC 3nm, more cores, LPDDR6 at ~1 TB/s) | 2x Rubin GPUs (~200 SMs per die, 288 GB HBM4 at ~13–14 TB/s) | 6th-generation NVLink 6 doubling CPU–GPU and GPU–GPU bandwidth |
| **Vera Rubin Ultra (`VR300` / `R300`, 2027)** | Vera Arm CPU complex | Quad-die Rubin Ultra GPU module (4 GPU dies, 16 HBM stacks, 1 TB HBM per GPU module) | NVL144 and NVL576 rack configurations (~3–4 ExaFLOPS per rack) |
| **Feynman (2028)** | Next-generation Arm host CPU | 2nm process node with HBM5 and multi-tier on-package memory | On-package optical NVLink interconnects for reasoning-era scaling |

Each row answers the same questions as the earlier tables. What CPU comes with the module, how much memory the GPUs get, and how the racks connect. The Vera Rubin row names the chip process and memory type, and the Ultra row names the rack configurations, which tell you how many GPUs fit together. The Feynman row is the furthest out, and its details are the least settled.

:::tip In one minute
- Moving from GH200 (1 Grace to 1 Hopper) to GB200 and GB300 (1 Grace to 2 Blackwell GPUs) doubles GPU compute density per 1U tray while still providing 36 Arm Neoverse V2 cores per GPU.
- Always check the specific SKU sheet (180 GB vs 192 GB B200, or 288 GB B300) when sizing tight memory footprints across a 36-Superchip NVL72 rack.
:::

---

### Why each generation doubles something

NVIDIA's roadmap follows a pattern. Each generation doubles something important, and some years it doubles more than one thing. Picture a planner who wants to know whether a model that does not fit today will fit in two generations. The pattern gives a quick answer. Blackwell introduced two GPU dies per module instead of one. NVLink bidirectional bandwidth per link doubled from about 900 GB/s to about 1.8 TB/s. Per-GPU memory grew from 180 GB in Blackwell to about 288 GB in Blackwell Ultra. Over a few years, that compound growth is large. Vera Rubin and Feynman push compute, memory, and bandwidth further.

For a performance engineer, the message is steady. Hardware will keep unlocking larger scale, so models that are out of reach today may become routine. You will also have to keep adapting software to new precision formats, larger memory pools, and faster interconnects. A precision format is the number representation, such as FP8 or FP4, that the model uses to store its values. The Grace Blackwell design is the base for that path, and the same codesign ideas carry forward to Vera Rubin and beyond.

## 5. Software co-design on Grace Superchips: data placement, NUMA, hugepages, and SuperOffload

Picture a team that tests a model on an 864 GB GB200 Superchip and treats the whole pool as one flat block of memory. Training steps and inference token times then jump by an order of magnitude. Having a 900 GB/s coherent NVLink-C2C link between the CPU and GPU prevents out-of-memory crashes, but it does not change memory physics or eliminate Linux page-table overhead. A page table is the data structure the operating system uses to translate addresses, and walking it costs time. The hardware makes the memory reachable, but the team still has to decide what lives where.

### 5.1 Two-tier memory placement: keeping hot tensors in HBM and cold overflow in LPDDR5X

Consider a single training step. The GPU reads the weights of the current layer many times, while the Adam momentum buffers are touched only once per step. Those two kinds of data should not share the same tier. Even though Grace LPDDR5X and NVLink-C2C are over seven times faster than PCIe Gen5, Blackwell HBM3e is still roughly 16× to 32× faster than LPDDR5X. Therefore, you must treat a Grace Superchip as an explicit two-tier coherent memory complex. A tier is a level of memory with its own speed and size, and placing data in the right tier is the job of the runtime and the programmer.

| Memory Tier | Bandwidth | What to Place Here | Prefetching Strategy |
|---|---|---|---|
| **Tier 1: GPU HBM3 / HBM3e** | 4.0–8.0 TB/s per GPU (8,000 GB/s per B200, 16,000 GB/s per Superchip) | Hot working-set tensors, active layer weights, forward/backward activations, and active KV-cache blocks | Resident in HBM during active kernel execution |
| **Tier 2: Grace CPU LPDDR5X** | ~500 GB/s (accessed at 450 GB/s per direction via NVLink-C2C) | Cold or overflow structures, unscheduled MoE expert weights, master FP32 weights, Adam momentum/variance buffers, DLRM/GNN feature tables, and evicted KV-cache blocks | Use `cudaMallocAsync` and prefetch upcoming slices into HBM via `cudaMemPrefetchAsync()` on a secondary CUDA stream |

Read the table as a rule for each kind of data. The first tier takes whatever the GPU touches on every step. The second tier takes whatever the GPU touches rarely or in a predictable order. The last column is the mechanism. A CUDA stream is an ordered queue of GPU work, and a second stream lets a copy run while the first stream computes. Prefetching on that second stream hides the cost of the copy from the kernels that need the data.

### 5.2 Linux NUMA pinning, `pin_memory`, and Transparent Hugepages on Grace

A training job on a dual-Superchip compute tray runs at a steady speed for a while. Then the throughput drops, and the GPUs show short gaps between steps. Often the cause is not the GPU at all. It is where the operating system placed the work. Even though NVLink-C2C is hardware cache-coherent, the Linux kernel still models each Grace CPU LPDDR5X pool as a CPU NUMA node and each GPU HBM pool as a distinct memory domain. On a dual-Superchip compute tray with two Grace CPUs and four Blackwell GPUs, crossing from Grace CPU 0 to a GPU attached to Grace CPU 1 adds hop latency. Always pin each training rank and its PyTorch `DataLoader` workers via `worker_init_fn` to the local Grace CPU NUMA node. A training rank is one process that drives one GPU, and a DataLoader worker is a helper process that prepares batches.

On standard x86 PCIe servers, setting `pin_memory=True` for page-locked memory is mandatory to achieve two to three times faster DMA copies. A DMA copy moves data without the CPU doing the work of each byte. On Grace Superchips, CPU-to-GPU transfers already use the coherent NVLink-C2C path without explicit page-locking. You must still enable Linux hugepages of 2 MB or 1 GB so the CPU and GPU Translation Lookaside Buffers do not thrash on millions of 4 KB page translations. A TLB, or translation lookaside buffer, is a small cache of recent address translations, and missing it forces a slower lookup. When the `DataLoader` thread is CPU-bound during heavy LLM tokenization, combine `pin_memory=True` or hugepages with `ulimit -l unlimited`, `non_blocking=True`, and `persistent_workers=True`. Always verify transfer overlap with Nsight Systems, NVIDIA's profiler, which shows when copies and kernels run at the same time.

| Linux Tuning Parameter | Setting for Throughput Training | Setting for Low-Latency Inference | Reason and Measured Impact |
|---|---|---|---|
| **NUMA Node Binding** | `numactl --cpunodebind=$NODE --membind=$NODE` | `numactl --cpunodebind=$NODE --membind=$NODE` | Local NUMA memory latency is ~80 ns versus ~139 ns cross-node (~75% remote latency penalty) |
| **Transparent Hugepages (THP)** | `always` (2 MB pages) | `madvise` or `never` (`transparent_hugepage=never` + explicit `hugetlbfs` / `vm.nr_hugepages`) | `always` yields a ~3%–5% training throughput gain by cutting TLB misses, while `madvise` or `never` avoids background THP compaction pauses that hurt P99 ITL |

The table gives two settings for two goals. Training cares about total throughput, so it can accept a small background cost in return for fewer TLB misses. Inference cares about the slowest responses, so it avoids background work that might pause a request. P99 ITL is a tail-latency measure. It describes the wait between tokens that the slowest one percent of requests experience. Compaction is the kernel's work to merge memory into larger pages, and it can pause a process for a moment.

### 5.3 SuperOffload and GraceAdam: superchip-native training optimization

Picture the end of a training step. The backward pass has just produced gradients. On an offload setup built for slow buses, the system then waits for the gradients to be combined, checks them for bad numbers, runs the optimizer on the CPU, and copies the updated weights back. Each wait leaves the GPU idle. Traditional CPU offload engines such as standard ZeRO-Offload were built for slow 64 GB/s PCIe buses. ZeRO-Offload is a method that moves optimizer work from the GPU to host memory to save GPU memory. They wait for global gradient reductions and NaN or Inf norm checks to finish on the GPU before copying gradients to the CPU. A gradient reduction combines gradients from every GPU, and NaN or Inf checks look for values that are not valid numbers. Next, they run the CPU Adam step sequentially and copy updated weights back. On a Grace Superchip, that sequential barrier wastes both the 72 Arm cores and the 900 GB/s NVLink-C2C link.

SuperOffload, which is detailed in *AI Systems Performance Engineering* Chapter 13, re-architects CPU-to-GPU offloading around four Grace-native mechanisms. The diagram shows how work moves between the two chips during one step.

```mermaid
flowchart LR
    subgraph GPU["Blackwell / Hopper GPU (HBM3e)"]
        BP["1. Backward Pass<br/>Gradient Computation"]
        HOPT["3a. Heavy Tensor Updates<br/>& Type Conversions on GPU"]
    end
    subgraph Grace["72-Core Grace CPU (LPDDR5X + Arm SVE)"]
        STV["2. Speculation-Then-Validation (STV)<br/>Speculative Optimizer Step Overlapped<br/>with GPU Backprop, Validated After"]
        GADAM["3b. GraceAdam Optimizer<br/>Arm A64 SVE (32 Vector + 16 Predicate Regs)<br/>Updates Momentum & Variance States"]
    end
    BP -->|"900 GB/s Coherent NVLink-C2C<br/>(Streamed Gradients)"| STV
    STV --> GADAM
    GADAM <-->|"Coherent Parameter Sync"| HOPT
```

The diagram follows one step from left to right. The backward pass on the GPU streams gradients to the Grace CPU. The CPU starts its optimizer work early, before the global check is done. The heavy tensor work returns to the GPU, and the two chips keep their copies of the parameters in sync. The numbered boxes match the list below.

1. Speculation-Then-Validation: Instead of waiting for the backward pass and global gradient norm check to finish, STV speculatively runs the optimizer updates on the Grace CPU in parallel with GPU backpropagation. It then validates to commit or roll back the updates once the global check completes, eliminating the end-of-step synchronization bubble. To speculate means to do the work before you know it is allowed, and to roll back means to undo it if the check fails.
2. Heterogeneous Optimizer Computation: Rather than running 100% of the optimizer on the CPU or 100% on the GPU, SuperOffload partitions optimizer work across both chips simultaneously. Compute-heavy tensor updates run on the GPU Tensor and SIMT cores. Lighter state updates for Adam first-moment and second-moment buffers in LPDDR5X run on the 72 Grace CPU cores. The first moment and second moment are the running averages that Adam keeps for each parameter.
3. Superchip-Aware Type Casts and Copies: Because NVLink-C2C provides 900 GB/s of coherent bandwidth, SuperOffload shifts FP32 to BF16 or FP8 precision conversions onto the GPU. That avoids burning CPU memory bandwidth on type casting before transfer. A type cast converts a number from one precision format to another.
4. GraceAdam Vectorized Optimizer: Standard x86 PyTorch CPU Adam kernels rely on x86 AVX intrinsics. SuperOffload replaces them with GraceAdam, an Adam implementation hand-tuned for the Grace CPU Arm A64 Scalable Vector Extension. GraceAdam exploits all 32 SVE vector registers and 16 predicate registers across all 72 Neoverse V2 cores. A kernel tuned this way processes many values per instruction instead of one at a time.

:::tip In one minute
- Keep hot tensors in GPU HBM and place overflow or cold states in Grace LPDDR5X, using `cudaMemPrefetchAsync()` to hide NVLink-C2C transfer latency.
- Pin worker threads to the local Grace NUMA node. Enable THP `always` for training throughput, and use `madvise` or `never` with explicit hugepages for low-latency LLM inference.
- SuperOffload unlocks Grace Superchip performance via Speculation-Then-Validation, heterogeneous CPU and GPU optimizer partitioning, and GraceAdam compiled for Arm SVE.
:::

---

## Commands and configurations that matter

Suppose you log into a new Grace node and want to confirm it is the right kind of machine before you start a job. The commands in this section do that check, then configure memory and CPU placement. These commands were not run on live Grace Superchip hardware. Their rules are checked in `code/part09/grace_superchips_lab.py`.

### 1. Inspect the 72-core or 144-core Grace Arm Neoverse V2 CPU and SVE capabilities

Start with the CPU itself. The first command reads the architecture and core count, and the second looks for the SVE flag that tells you the vector extension is present.

```bash
# 1. Verify aarch64 architecture, 72 cores per socket (144 cores on dual-Superchip tray), and SVE flags
lscpu | grep -E "Architecture:|Model name:|Socket\(s\):|Core\(s\) per socket:|NUMA node|Flags:"

# 2. Confirm Arm Scalable Vector Extension (sve / sve2) support in /proc/cpuinfo
grep -m 1 -oE "sve[^ ]*" /proc/cpuinfo
```

### 2. Inspect Grace LPDDR5X and GPU HBM NUMA topology and NVLink-C2C links

Next, check how the operating system sees memory. Each memory pool should appear as its own NUMA node, and the GPU-to-GPU links should show up in the topology matrix. If a pool or a link is missing, the placement rules in the earlier sections cannot be applied.

```bash
# 1. View CPU and memory NUMA nodes (LPDDR5X vs GPU memory nodes)
numactl --hardware

# 2. View GPU-to-GPU NVLink and CPU/NUMA affinity matrix
nvidia-smi topo -m

# 3. Query NVLink link speeds and active sub-links
nvidia-smi nvlink --status
```

### 3. Tune Linux virtual memory, locked memory limits, and Transparent Hugepages

These settings decide how the kernel treats the memory that the training job uses. Swapping off keeps the working set in RAM, which matters because a swap to NVMe would add delays that the GPUs cannot hide. The locked-memory limit lets pinned buffers exist, and the hugepage setting trades background work for fewer TLB misses. Choose the THP setting that matches the job, and do not apply both settings to the same node at the same time.

```bash
# 1. Disable swapping on GPU/Superchip compute nodes so LPDDR5X never swaps to NVMe
sudo sysctl -w vm.swappiness=0
sudo swapoff -a

# 2. Ensure unlimited locked (pinned) memory in /etc/security/limits.conf or container ulimits
ulimit -l unlimited

# 3. For throughput training: enable Transparent Hugepages (2 MB pages reduce TLB pressure by ~3-5%)
echo always | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# 4. For latency-sensitive LLM inference: use madvise (or never) to prevent background compaction pauses
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
```

### 4. Launch a training process pinned to each GPU local Grace CPU NUMA node

The last command starts one training process for each GPU and binds each process to the NUMA node of its local Grace CPU. The loop reads the NUMA affinity from the topology matrix, so the binding follows the hardware instead of a hard-coded guess. The wait command at the end keeps the shell running until all the processes finish.

```bash
# Dynamically query each GPU's local NUMA node from nvidia-smi topo -m and bind CPU + memory
for GPU in 0 1 2 3; do
  NODE=$(nvidia-smi topo -m -i "$GPU" | awk '/NUMA Affinity/ {print $NF}')
  numactl --cpunodebind="$NODE" --membind="$NODE" \
    bash -c "CUDA_VISIBLE_DEVICES=$GPU python3 train.py --gpu $GPU" &
done
wait
```

---

## How it fails

The table lists five failures that teams meet on Grace systems. Each row follows the same path. The symptom is what the on-call engineer sees first, the root cause is the design error behind it, and the last column is the fix. Notice that three of the five come from treating Grace like an ordinary x86 server, and the other two come from treating shared memory as if it behaved like local memory.

| Failure mode | Symptom | Root cause | Diagnosis & fix |
|---|---|---|---|
| **1. Assuming GPU-to-GPU caches are hardware cache-coherent across NVSwitch** | Custom multi-GPU CUDA kernels reading/writing peer GPU memory directly across NVLink produce silent stale-cache data corruption or race conditions on a GB200/GB300 node. | Engineers hear *"Grace Blackwell has coherent unified memory"* and assume all 4 or 72 GPUs have globally coherent L1/L2 caches. In reality, **only the CPU–GPU NVLink-C2C link is hardware cache-coherent**; GPU-to-GPU memory across NVSwitch has a shared global address space but **non-coherent GPU caches**. | Use **NCCL** collectives or **NVSHMEM** symmetric memory APIs (`nvshmem_barrier_all()`, `triton.nvshmem.put()/get()`) to enforce explicit memory ordering and cache invalidation across GPUs. |
| **2. Placing "hot" activations or active KV cache in Grace LPDDR5X** | A model fits inside the 864 GB coherent pool of a GB200 Superchip without OOM errors, but step time or decode ITL is **8× to 15× slower** than expected. | Relying blindly on automatic CUDA Unified Memory placed frequently accessed ("hot") weights, activations, or active KV-cache tensors in **Grace LPDDR5X (`~500 GB/s`, accessed at `450 GB/s` over NVLink-C2C)** instead of **GPU HBM3e (`8,000 GB/s`)**. | Explicitly place hot weights, activations, and active KV cache in **GPU HBM3e**, restrict LPDDR5X to cold/overflow tiers (optimizer states, unscheduled MoE experts, historical KV blocks), and stream upcoming layers into HBM ahead of use via **`cudaMemPrefetchAsync()`**. |
| **3. Using Unified Memory on Grace without Hugepages (`4 KB` TLB thrashing)** | Profiling with Nsight Systems shows frequent CPU/GPU page-translation stalls and high kernel overhead during coherent CPU–GPU memory access. | The workload accesses hundreds of gigabytes of unified virtual memory across NVLink-C2C using default **4 KB Linux pages** without `pin_memory=True` or hugepages, flooding the CPU and GPU Address Translation Services (ATS) / TLBs. | Enable **2 MB Transparent Hugepages** (`always` for training; `madvise` + explicit `hugetlbfs` for low-latency inference), set `ulimit -l unlimited`, and verify H2D/D2H overlap in Nsight Systems. |
| **4. `Illegal instruction (core dumped)` or 10× slower CPU preprocessing on Grace** | Moving an x86 Docker container or custom C++ optimizer extension onto a GH200/GB200 node either fails to start (`exec format error` / `SIGILL`) or runs CPU Adam updates painfully slowly. | The Grace CPU is **Armv9 `aarch64` (Neoverse V2)** with **Arm SVE** (`32` vector + `16` predicate registers), not x86_64. Containers built for `amd64` or C++ extensions compiled with x86 `AVX2`/`AVX-512` intrinsics either crash or fall back to scalar C loops. | Build multi-arch (`linux/arm64`) NGC containers, recompile native wheels with `-march=armv9-a+sve2`, and use **`GraceAdam` / SuperOffload** to vectorize offloaded optimizer updates on Arm SVE. |
| **5. Unbound DataLoader workers migrating across dual Grace Superchips** | On a 2-Superchip compute tray (`144` Arm cores, `4` GPUs), training throughput fluctuates by 5%–10% with periodic GPU launch bubbles. | Linux CFS migrated `DataLoader` workers for `GPU 0` (attached to `Grace CPU 0`) onto `Grace CPU 1` cores, incurring a **~75% remote NUMA memory latency penalty** (`~139 ns` vs `~80 ns`). | Bind both the main rank process (`numactl --cpunodebind --membind`) and every forked `DataLoader` worker (`worker_init_fn` with `psutil.Process().cpu_affinity()` + `libnuma`) to the GPU's local Grace CPU NUMA node, and set `persistent_workers=True`. |

Two of the rows deserve a closer read. Row 2 is the one that surprises people, because the model fits and nothing crashes. The job simply runs slowly, and the only clue is the step time. Row 5 is a reminder that the scheduler moves threads around unless you tell it not to. A worker that lands on the wrong CPU keeps paying for remote memory on every batch.

---

## Hands-on lab

This chapter provides a self-checking Python model in `code/part09/grace_superchips.py` and a lab runner in `code/part09/grace_superchips_lab.py` that verify four core areas. Think of the lab as a set of calculators with rules attached. Each check either reproduces a number from this chapter or confirms that the code rejects a bad input. When you change a value in the model, the checks tell you whether the chapter's arithmetic still holds.

| Lab Component | Verified Calculations and Rules |
|---|---|
| **1. NVLink-C2C vs PCIe Gen5 x16 Calculator** | 450 GB/s vs 64 GB/s unidirectional = 7.03× speedup, 900 GB/s vs 128 GB/s bidirectional, `< 5 pJ/bit`, and 1.2 TB GNN pass taking 18.75 s on PCIe Gen5 vs 2.67 s on NVLink-C2C |
| **2. Superchip Architecture Catalog** | Grace CPU Superchip (144 cores / 960 GB); GH200-96GB (576 GB); GH200-144GB (624 GB); GB200 (384 GB HBM3e + 480 GB LPDDR5X = 864 GB); GB300 (576 GB HBM3e + 500 GB LPDDR5X = 1,076 GB, scaling to 2,592 Arm cores, 20,736 GB HBM3e, and 18,000 GB LPDDR5X across a 36-Superchip NVL72 rack) |
| **3. Two-Tier Coherent Memory Placement Evaluator** | Verifies whether hot working sets fit in HBM3 or HBM3e and how overflow spills into Grace LPDDR5X |
| **4. Runtime & OS Configuration Auditor** | Checks CPU–GPU vs GPU–GPU cache-coherence assumptions, local Grace NUMA pinning, large-page enablement, THP `always` vs `madvise`, hot tensor placement, and Arm A64 SVE vs x86 AVX compatibility |

Run the lab from the repository root. The command runs the Python script with bytecode writing turned off, so no cache files appear in the repository.

```bash
python3 -B code/part09/grace_superchips_lab.py
```

Expected output from a run of this lab in this repository:

```text
=== Chapter 9.4 Lab: Grace CPU, GH200, GB200 & GB300 Superchips ===
  [PASS] PCIe Gen5 x16 is 64 GB/s unidirectional and 128 GB/s bidirectional
  [PASS] NVLink-C2C is 450 GB/s unidirectional and 900 GB/s bidirectional (7.03x PCIe Gen5)
  [PASS] Grace CPU Superchip bonds 2x 72-core Arm Neoverse V2 CPUs (144 cores) + up to 960 GB LPDDR5X at ~1 TB/s
  [PASS] GH200-96GB combines 72-core Grace (480 GB LPDDR5X) + H100 (96 GB HBM3) = 576 GB coherent memory
  [PASS] GH200-144GB HBM3e variant delivers 480 + 144 = 624 GB coherent memory
  [PASS] GB200 combines 1x 72-core Grace + 2x B200 GPUs (384 GB HBM3e @ 16 TB/s + 480 GB LPDDR5X = 864 GB)
  [PASS] GB300 combines 1x Grace + 2x B300 GPUs (2x 288 GB = 576 GB HBM3e + 500 GB LPDDR5X = 1,076 GB)
  ...
  [PASS] 1.2 TB (1,200 GB) host-to-GPU pass takes 18.75 s over PCIe Gen5 x16 vs 2.67 s over NVLink-C2C
  [PASS] Rejects unknown superchip SKU
  [PASS] Rejects negative payload in transfer time estimator
  [PASS] Rejects unsupported link_type in transfer time estimator
  [PASS] Unidirectional NVLink-C2C (450 GB/s) is 7.03x unidirectional PCIe Gen5 x16 (64 GB/s)

Summary: 30 passed, 0 failed (total 30)
```

---

## Exercises

1. Run `python3 -B code/part09/grace_superchips_lab.py`. Find the check that compares PCIe Gen5 and NVLink-C2C transfer time for the 1,200 GB graph. Can you reproduce the 18.75 s figure by hand? Then reproduce the 2.67 s figure.
2. Work out the total coherent memory of one GB300 Superchip. Then work out the total for the whole 36-Superchip NVL72 rack, using the numbers in Section 4.1. Which figure should you compare with the HBM size when you size a model that must stay in HBM?
3. You have a GB200 node and a 600 GB model with a 200 GB KV cache. Which tensors would you place in HBM? Which would you place in LPDDR5X? What would you prefetch, and when?
4. Write the three commands that show whether a node is `aarch64`, has SVE, and how many NUMA nodes it has. What do you expect to see on a GB200 compute tray?
5. A teammate moves an x86 container to a GH200 node and gets `exec format error`. What checklist would you give them? Cover the image build, the wheels, and any native code.
6. Explain to a colleague in five lines why unified memory on a Grace Superchip does not mean the 864 GB behaves like HBM.

## Checkpoint questions (20)

<details>
<summary>**1. Compare the unidirectional and bidirectional bandwidth of NVLink-C2C against PCIe Gen5 x16, and state its energy efficiency per bit.**</summary>

PCIe Gen5 x16 provides 64 GB/s unidirectional and 128 GB/s bidirectional bandwidth. NVLink-C2C provides 450 GB/s unidirectional and 900 GB/s bidirectional, which is a 7.03× bandwidth increase. It consumes less than 5 picojoules per bit, making it more than 5× more energy-efficient than standard PCB PCIe Gen5 traces.
</details>

<details>
<summary>**2. Why does the NVIDIA Grace CPU solder ECC LPDDR5X memory directly onto the package instead of using standard DDR5 DIMM slots?**</summary>

Soldering server-grade ECC LPDDR5X millimeters from the 72 Arm Neoverse V2 cores delivers ~500 GB/s of sustained memory bandwidth for up to 480–512 GB per Grace CPU. The entire CPU and memory package operates inside a compact 60W–200W total power envelope. That uses a fraction of the power and board space consumed by 8-channel to 12-channel x86 DDR5 DIMMs.
</details>

<details>
<summary>**3. Contrast the CPU-to-GPU ratio and coherent memory capacity across the GH200, GB200, and GB300 Superchips.**</summary>

| Superchip | CPU-to-GPU Ratio | Grace LPDDR5X | GPU HBM | Coherent Memory Pool |
|---|---|---|---|---|
| **GH200 Grace Hopper** | 1:1 | 480–512 GB | 96 GB HBM3 or 144 GB HBM3e | 576 GB to 624 GB |
| **GB200 Grace Blackwell** | 1:2 | 480 GB | 384 GB HBM3e (or 360 GB on 180 GB SKUs) at 16 TB/s | Up to 864 GB |
| **GB300 Grace Blackwell Ultra** | 1:2 | ~500 GB | 576 GB HBM3e (2 × 288 GB, 1.5× B200 capacity) | ~1,076 GB (~1.08 TB) |
</details>

<details>
<summary>**4. On a Grace Blackwell NVL72 system, is memory hardware cache-coherent between two GPUs, or only between a Grace CPU and its paired GPUs? Why does this matter for programmers?**</summary>

Only the CPU-to-GPU path over NVLink-C2C is hardware cache-coherent with Address Translation Services. Across GPUs over NVLink and NVSwitch, there is a shared global physical address space for peer-to-peer access, but GPU L1 and L2 caches are not globally hardware cache-coherent across GPUs. Programmers must still use NCCL collectives or NVSHMEM synchronization barriers to maintain consistency across GPUs.
</details>

<details>
<summary>**5. If a GB200 Superchip has an 864 GB unified virtual address space, why must you still carefully separate hot tensors from cold overflow tensors?**</summary>

Blackwell HBM3e delivers 8,000 GB/s per GPU or 16,000 GB/s per Superchip, whereas Grace LPDDR5X delivers ~500 GB/s and is accessed at 450 GB/s per direction over NVLink-C2C. Because of this roughly 18× bandwidth difference, active weights, activations, and active KV caches must reside in HBM3e. LPDDR5X should hold overflow layers, optimizer states, or cold embeddings prefetched into HBM asynchronously via `cudaMemPrefetchAsync()`.
</details>

<details>
<summary>**6. How many GB300 Superchips reside on a single DGX GB300 compute tray, and how are they connected to run under a single OS instance?**</summary>

Each 1U DGX GB300 compute tray houses two GB300 Superchips, providing 2 Grace CPUs with 144 Arm cores and 4 B300 GPUs. A coherent NVLink-C2C interconnect bridges the two Superchips so they operate as a single logical SMP system under one Linux OS instance.
</details>

<details>
<summary>**7. How should Transparent Hugepages be configured on a Grace Superchip node for throughput-focused training versus low-latency LLM inference, and why?**</summary>

For training, set THP to `always` so 2 MB pages reduce page-fault overhead and TLB misses across huge LPDDR5X and unified memory pools, improving throughput by ~3%–5%. For low-latency LLM inference, set THP to `madvise` or `never` via `transparent_hugepage=never` and use explicit `hugetlbfs` hugepages instead. Kernel background THP compaction causes unpredictable latency pauses during token generation.
</details>

<details>
<summary>**8. What are the three core innovations in SuperOffload and GraceAdam for Grace-based Superchips?**</summary>

1. **Speculation-Then-Validation:** Overlaps speculative CPU optimizer updates with GPU backpropagation before global gradient checks complete, then validates afterward to eliminate synchronization stalls.
2. **Heterogeneous Optimizer Computation:** Splits optimizer work between the GPU for compute-heavy tensor updates and precision casts, and the 72 Grace CPU cores for lighter momentum and variance buffer updates in LPDDR5X.
3. **GraceAdam on Arm SVE:** Vectorizes CPU Adam updates using the Grace CPU Arm A64 Scalable Vector Extension with 32 vector registers and 16 predicate registers.
</details>

<details>
<summary>**9. What is the Vera Rubin Superchip on NVIDIA post-Blackwell roadmap?**</summary>

The Vera Rubin `VR200` Superchip targeted for 2026 pairs one Vera Arm CPU on TSMC 3nm with LPDDR6 at ~1 TB/s and two Rubin GPUs with ~200 SMs per die, 288 GB HBM at ~13–14 TB/s, and NVLink 6. It is followed by Vera Rubin Ultra `VR300` or `R300` in 2027 with quad-die GPU modules holding 1 TB HBM per GPU module in NVL144 and NVL576 racks.
</details>

<details>
<summary>**10. What is the PCIe tax?**</summary>

It is the slowdown a GPU suffers when it needs data from host RAM over a PCIe Gen5 x16 link at 64 GB/s per direction, which is far slower than the GPU HBM. Workloads like huge embedding tables, long KV caches, or big graphs pay it.
</details>

<details>
<summary>**11. How many cores and how much memory does a Grace CPU have, and why is its memory soldered?**</summary>

A Grace CPU has 72 Arm Neoverse V2 cores and up to about 480–512 GB of LPDDR5X. The memory is soldered close to the CPU to achieve about 500 GB/s of bandwidth inside a small 60–200 W power budget together with the CPU.
</details>

<details>
<summary>**12. What does NVLink-C2C let a CUDA kernel do that PCIe does not?**</summary>

With hardware coherence and a single virtual address space, a GPU kernel can use a pointer to Grace LPDDR5X memory directly. It requires no `cudaMemcpy` call and no page-locked staging buffer.
</details>

<details>
<summary>**13. What is the CPU-to-GPU ratio in a GH200 and in a GB200, and why did it change?**</summary>

GH200 is 1 Grace to 1 Hopper, while GB200 and GB300 are 1 Grace to 2 Blackwell GPUs. One 72-core Grace has enough cores, memory, and link bandwidth to drive two GPUs, so the tray holds more GPUs.
</details>

<details>
<summary>**14. How many Arm cores and GPUs are in one NVL72 compute tray, and in the whole rack?**</summary>

One compute tray has 2 Grace CPUs with 144 cores and 4 GPUs. The rack has 18 trays, which gives 36 Grace CPUs with 2,592 cores and 72 GPUs.
</details>

<details>
<summary>**15. Why are the 864 GB GB200 memory figure and the 8,000 GB/s HBM figure not interchangeable?**</summary>

The 864 GB figure is the size of the combined coherent pool of HBM plus LPDDR5X. HBM is much faster than LPDDR5X at about 8,000 GB/s versus 500 GB/s, so only hot data should live in HBM.
</details>

<details>
<summary>**16. What does `cudaMemPrefetchAsync()` do for you on a Grace node?**</summary>

It moves upcoming weights or expert slices from LPDDR5X into HBM on a second stream while the GPU computes the current layer. That way, kernels do not stall on page faults.
</details>

<details>
<summary>**17. How does Linux see a Grace compute tray, and what should you pin?**</summary>

Each Grace CPU LPDDR5X pool is a NUMA node and the GPUs have their own memory domains. Pin each rank and its `DataLoader` workers to the NUMA node of the Grace CPU attached to its GPU with `numactl --cpunodebind --membind`.
</details>

<details>
<summary>**18. Do you still need `pin_memory=True` on a Grace Superchip?**</summary>

You do not need it for coherent transfers if you use hugepages. When the `DataLoader` is CPU-bound, the chapter still recommends pinned memory with `non_blocking=True` and `persistent_workers=True`, and advises checking overlap in Nsight Systems.
</details>

<details>
<summary>**19. Why must C++ or Python extensions be rebuilt for Grace?**</summary>

Grace is Armv9 `aarch64`, not x86. Code with AVX2 or AVX-512 intrinsics will crash or fall back to slow scalar code, so build `linux/arm64` images and compile native code for Arm SVE.
</details>

<details>
<summary>**20. Give one fact about the Vera Rubin roadmap from this chapter.**</summary>

The `VR200` Superchip in 2026 pairs a Vera Arm CPU using LPDDR6 at about 1 TB/s with two Rubin GPUs offering 288 GB HBM at about 13–14 TB/s and NVLink 6. `VR300` in 2027 moves to quad-die GPU modules with 1 TB of HBM each.
</details>

---

## Sources and review notes

### Sources read in full for this chapter

| Source | Chapters / Pages Read | Topics Extracted |
|---|---|---|
| **`nvidia-devops` Volume 04 & Volume 05** | `nvidia-zero-to-hero/volume-04/chapter-07-grace-cpu-and-superchips.md` (`chapter-07-grace-cpu-and-superchips.md`, 1,007 words) and `nvidia-zero-to-hero/volume-05/chapter-07-dgx-gh200-and-gb200-systems.md` (`chapter-07-dgx-gh200-and-gb200-systems.md`, 982 words) | The PCIe tax (64 GB/s unidirectional / 128 GB/s bidirectional PCIe Gen5 x16 vs 3.35 TB/s / 3,350 GB/s HBM3 and 1,990 TFLOPS FP8), 72-core Arm Neoverse V2 Grace CPU with soldered ECC LPDDR5X (~500 GB/s at 60W–200W), NVLink-C2C (900 GB/s bidirectional, `< 5 pJ/bit`, ATS), Superchip lineup (Grace CPU Superchip 144 cores / 960 GB, GH200 480 GB + 96/144 GB = 576/624 GB, GB200 480 GB + 384 GB = 864 GB), `THP=always` vs `madvise`/`never`, and 1.2 TB GNN customer scenario |
| **Chris Fregly, *AI Systems Performance Engineering* (`ai-systems-performance-engineering`)** | Chapter 2 (pp. 20–55, chunks 1, 6–9), Chapter 3 (lines 49–331), Chapter 13 (chunk 71 & summary) | Grace Blackwell architecture, CPU–GPU NVLink-C2C hardware cache coherence vs GPU–GPU non-coherent caches across NVSwitch (requiring NCCL/NVSHMEM), Blackwell Ultra GB300 (288 GB HBM3e per B300 GPU, 1.5× FP4 compute, ~20.7 TB HBM + ~18 TB LPDDR across 36 modules in NVL72), Vera Rubin (`VR200`/`VR300`) and Feynman roadmap, NUMA latency (~80 ns local vs ~139 ns remote), THP (`always` +3%–5% vs `madvise`/`never`), `cudaMemPrefetchAsync`, SuperOffload, STV, and GraceAdam on Arm SVE (32 vector + 16 predicate registers) |
| ***NVIDIA DGX SuperPOD Reference Architecture Featuring NVIDIA DGX GB300 Systems* (`superpod-gb300-ra`) & *Distributed AI Systems* (`distributed-ai-systems`)** | `superpod-gb300-ra` pp. 8–10; `distributed-ai-systems` Chapter 2, chunk 9 | Dual GB300 Superchips per 1U compute tray bridged by coherent NVLink-C2C acting as a single logical unit under one OS instance, and the 512 GB LPDDR5X + 96 GB HBM3 = 608 GB GH200 variant |

### Not in the corpus
- Standalone *NVIDIA Grace CPU Superchip Architecture Whitepaper* and *NVIDIA GH200 Grace Hopper Superchip Datasheet* PDFs are not in `~/Desktop/books-toon-rag/`.

### Run here
- `python3 -B code/part09/grace_superchips_lab.py` passes all 30 checks with 0 failures.

### My own choices and inferences, labelled in the text
1. **Unidirectional 1.2 TB host-to-GPU pass transfer-time comparison (`estimate_host_to_gpu_transfer_seconds` in `code/part09/grace_superchips.py` and Sections 1.1 and 3.3):** Dividing the 1,200 GB GNN feature payload from Volume 04 Chapter 7 by the 64 GB/s PCIe Gen5 x16 unidirectional limit gives 18.75 seconds, versus 2.67 seconds on the 450 GB/s NVLink-C2C unidirectional limit, which is a 7.03× link speedup and is **my inference** to make the customer scenario bandwidth math concrete and testable.

### Not verified on live hardware
- `lscpu`, `numactl --hardware`, `nvidia-smi topo -m`, and `sysfs` Transparent Hugepage toggles were not executed on a live Grace Superchip node in this authoring environment.

