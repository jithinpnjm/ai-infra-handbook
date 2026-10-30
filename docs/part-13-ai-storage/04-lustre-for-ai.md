---
id: "c13-04"
title: "13.4 Lustre for AI"
sidebar_label: "13.4 Lustre for AI"
sidebar_position: 4
description: "Production Lustre engineering for AI training and inference clusters: SuperPOD High-Performance Storage tiers, Progressive File Layout (PFL) and Data-on-MDT (DoM), Distributed Namespace (DNE Phase 1 and Phase 2) metadata scaling, LNet multi-rail RDMA binding, client RPC bandwidth-delay-product tuning, GPUDirect Storage integration, and N-to-1 vs N-to-N checkpoint striping."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 13.4 Lustre for AI

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE + Local Python Verification Lab (`code/part13/lustre_for_ai_lab.py`) |
| Part | Part 13: AI storage |
| Primary sources | NVIDIA Zero-to-Hero Volume 15 (`chapter-05-lustre-for-ai-and-hpc.md`); *AI Systems Performance Engineering* (`ai-systems-performance-engineering`); *Supercomputers for Linux SysAdmins* (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`); NVIDIA DGX SuperPOD Reference Architectures (`superpod-gb300-ra`, `superpod-b200-dc`) |
| Coverage file | `planning/coverage/chapters/13-04.md` |
| Claim & number ledger | `planning/ledgers/13-04.md` |

## Why this matters for AI infrastructure

When thousands of GPUs run synchronous distributed training, the parallel file system sits on the critical path of every epoch start and recovery barrier. Chapter 6.19 established basic Lustre component anatomy including the MGS, MDS, MDT, OSS, OST, quotas, and basic formatting. Operating Lustre for AI factories introduces three severe failure modes that classic single-job HPC simulations rarely trigger together.

First, AI clusters suffer from bimodal file sizes and epoch-start metadata storms. A single workspace holds millions of tiny raw files alongside multi-gigabyte packed shards and multi-terabyte checkpoints. At the start of an epoch, hundreds of GPU clients flood a single MDS with file open and attribute requests. Open latency then spikes from a few milliseconds to tens of milliseconds. Every GPU sits idle waiting for file handles while the OST data drives remain ninety percent idle.

Second, default single-OST striping stalls synchronized checkpoint bursts. Lustre defaults to a stripe count of one for new directories. Writing a multi-hundred-gigabyte checkpoint into an untuned directory serializes the entire dump onto a single OST. That bottleneck freezes training for over ten minutes instead of finishing in seconds across all targets. Conversely, when dozens of ranks write unaligned byte ranges into one shared file, the Lustre Distributed Lock Manager thrashes extent locks and cuts throughput by fourfold.

Third, untuned client RPC queues and cross-socket hardware paths starve high-speed RDMA links. Even when files are striped across two dozen OSTs over 400 Gbps InfiniBand or RoCEv2, default Object Storage Client queue depths cap throughput below the network bandwidth-delay product. If LNet binds to a NIC on one NUMA socket while the dataloader or GPUDirect Storage buffer runs on the other socket, single-client throughput drops by fivefold. Missing mount flags also break distributed locks and cause cluster health probes to hang whenever one storage target slows down.

```text
AI Factory Lustre Failure Regime Summary:
1. Bimodal datasets & metadata storms:
   - Raw datasets: multi-million files at 260 KB (images, audio, JSON manifests)
   - Packed shards: 512 MiB to 26 GB (WebDataset, TFRecord, Parquet)
   - Distributed checkpoints: 140 GB to 5.6 TB across 1,000 to 9,216 GPUs
   - 128 to 1,000 GPU clients issuing 200,000 open()/getattr() ops/s against 1 MDS (rated 50,000 to 100,000 ops/s)
   - open() latency spikes from 2.1 ms avg (5.4 ms max) to 45.2 ms avg (65.4 ms max) or 120 ms burst; OSTs sit 90% idle
2. Default single-OST striping & LDLM lock ping-pong:
   - Default stripe_count = 1 serializes a 500 GB checkpoint onto 1 OST (800 MB/s disk or 5 GB/s NVMe)
   - Stalls training for 625 seconds (10+ minutes) vs 41.67 seconds across 24 OSTs at 12 GB/s (24 * 500 MB/s) or 10.0 seconds across 112 NVMe OSTs at 560 GB/s
   - 64 ranks writing unaligned N-to-1 shared ranges trigger LDLM extent lock ping-pong, cutting throughput 4x (3.0 GB/s vs 12.0 GB/s)
3. Client RPC BDP starvation, NUMA hairpins, and mount flags:
   - Default OSC max_rpcs_in_flight = 8 and max_pages_per_rpc = 256 (1 MiB) starve 16 to 24 OSTs over 400 Gbps o2ib / RoCEv2
   - Cross-socket LNet binding (NIC on NUMA 1, GPU/loader on NUMA 0) or MTU 1500 vs 9000 drops client throughput 5x
   - Omitting -o flock,lazystatfs causes PyTorch FileStore to fail with ENOSYS and df to hang on degraded OSTs
```

## Prerequisites and outcomes

### Prerequisites

Review the foundational Lustre concepts from Chapter 6.19. Those include the MGS, MDS, MDT, OSS, OST, backing filesystems, project quotas, and target deactivation with `lctl`. You should also know InfiniBand and RoCEv2 fabrics, jumbo frames, and NUMA locality inspection with `nvidia-smi` from Part 12. Finally, review the AI data path, direct I/O bypass, and GPUDirect Storage tools from Chapters 13.1 through 13.3.

### Outcomes

After completing this chapter, you will map Lustre into the NVIDIA DGX SuperPOD dual-tier storage architecture. That layout separates the High-Performance Storage fabric from the in-band User Storage tier. You will design Progressive File Layout and Data-on-MDT directory policies with `lfs setstripe` and calculate round-robin RAID 0 chunk placement. You will also diagnose and eliminate metadata bottlenecks using `lctl get_param`, Distributed Namespace directory striping, client statahead tuning, and dataset repackaging. Finally, you will configure LNet multi-rail RDMA networking, client RPC bandwidth-delay product settings, GPUDirect Storage, and sharded checkpoint architectures.

---

## 1. Lustre in the AI Factory and DGX SuperPOD Storage Architecture

When one storage network carries both user home directories and multi-terabyte training streams, interactive logins freeze during every checkpoint burst. Engineers editing code or compiling software in shared home directories hit multi-second terminal stalls whenever thousands of GPUs flush state. Worse, congestion on a shared network delays Slurm heartbeats and Base Command Manager health probes. Those delays can cause the cluster manager to fence healthy compute nodes mid-epoch.

Modern AI factories such as the NVIDIA DGX SuperPOD prevent this interference through physical network isolation. Storage traffic stays completely separate from both the east-west GPU compute fabric and the in-band management network. Whether a cluster deploys air-cooled DGX B200 nodes or liquid-cooled DGX GB300 NVL72 racks, reference architectures divide external storage into two tiers over dedicated switch ports.

```text
NVIDIA DGX SuperPOD Scale & Power Parameters:
- DGX B200 air-cooled Scalable Unit (SU): up to 32 nodes / 458 kW per SU; 127 servers + 1 UFM appliance across 4 SUs
- DGX GB300 NVL72 liquid-cooled SU: 8 racks / 18 compute trays per rack / 72 GPUs per rack = 576 GPUs and 1.2 MW per SU
- Maximum GB300 SuperPOD scale: 16 SUs / 128 racks / 9,216 GPUs
- Compute tray local storage & interconnect: 4x 3.84 TB E1.S NVMe RAID0 + 1x 1.92 TB M.2 OS drive; 900 GB/s NVLink-C2C
- Storage fabric switch radix: SN5600D 800GbE switches providing 72 non-blocking 400 Gbps storage leaf links per SU (64x to 1024x 400GbE across 2 to 16 SUs) and 24x 400 Gbps management leaf uplinks
```

### 1.1 High-Performance Storage (HPS) vs User Storage Tiering

Rather than forcing one file system to serve both latency-sensitive home directories and bulk training streams, reference AI architectures split storage across dedicated ports on the BlueField-3 DPU.

```mermaid
flowchart TB
    subgraph ComputeTray["DGX Compute Node / Tray"]
        GPU["GPUs + Local NVMe<br/>4x 3.84TB E1.S RAID0"]
        DPU["BlueField-3 DPU / NIC<br/>Port 0: 400G | Port 1: 200G+"]
        GPU ===|"PCIe / NVLink-C2C<br/>900 GB/s"| DPU
    end

    subgraph StorageNet["Storage Ethernet / IB Fabric"]
        SLeaf["Storage Leaf Switches<br/>SN5600D 400GbE RoCEv2 / o2ib"]
        MLeaf["In-Band Mgmt Switches<br/>200GbE Bonded"]
    end

    subgraph LustreHPS["High-Performance Storage (Lustre HPS)"]
        MDS["MDS Cluster (DNE + DoM)<br/>NVMe RAID-10 MDTs"]
        OSS["Scale-Out OSS Cluster<br/>NVMe OST Pools (c=1..All)"]
    end

    subgraph UserNFS["User & Admin Storage (NFSv3)"]
        NFS["Enterprise NFS Array<br/>100GbE+ Home, Logs, BCM HA"]
    end

    DPU -->|"Dedicated 400 Gbps<br/>RoCEv2 / o2ib RDMA"| SLeaf
    DPU -->|"Dedicated 200 Gbps<br/>In-Band TCP/IP"| MLeaf
    SLeaf -->|"1 open / stat / layout"| MDS
    SLeaf ===|"2 Parallel RDMA stripes"| OSS
    MLeaf -->|"Home dirs / Slurm / Logs"| NFS
```

| Architectural Tier | Network Fabric & Protocol | Target AI Workloads | SuperPOD Bandwidth Targets (`1 SU` / `4 SU`) | Lustre / Filesystem Design Choice |
|---|---|---|---|---|
| **High-Performance Storage (`HPS`)** | Dedicated `400 Gbps` per compute tray over `SN5600D` (`800GbE` radix) `RoCEv2` or `o2ib` InfiniBand (`72` non-blocking `400 Gbps` storage leaf links; `64x` to `1024x 400GbE` across `2` to `16` SUs) | Training dataset shards (`WebDataset`, `Parquet`, `TFRecord`), multi-modal streaming, distributed checkpoints (`140 GB`–`5.6 TB`), inference weight loading & KV-cache offload | **Standard:** `90 GB/s` read, `45 GB/s` write (`1 SU`); `360 GB/s` read, `180 GB/s` write (`4 SU`).<br/>**Enhanced:** `280 GB/s` read, `140 GB/s` write (`1 SU`); `1,120 GB/s` read, `560 GB/s` write (`4 SU`) | **Lustre** (or certified parallel FS) with NVMe `OST`s, `DNE` multi-`MDT`, `PFL`+`DoM`, `LNet` RDMA, `GDS` (`O_DIRECT`), and `flock,lazystatfs` |
| **User & Admin Storage** | In-band management network (`200 Gbps` bonded on compute trays; `>= 100GbE DR1` to storage; `24x 400 Gbps` mgmt leaf uplinks) | User `/home` directories, Slurm batch scripts, `conda`/source trees, Mission Control / Base Command Manager (`BCM`) HA state, cluster log collection | High IOPS and metadata consistency (not bulk parallel streaming) | **NFSv3** (`rsize=1048576,wsize=1048576,noatime`; often mounted `ro` on compute nodes to prevent `/home` log storms) |
| **Node-Local Scratch NVMe** | Internal PCIe Gen5 (`4x 3.84 TB` E1.S NVMe `RAID0` + `1x 1.92 TB` M.2 OS drive per GB300 tray) | Ephemeral container rootfs (`Enroot`/`Pyxis` squashfs), local dataset caching, and asynchronous two-stage checkpoint staging before draining to Lustre | Tens of `GB/s` per node with zero fabric traversal | Local `XFS`/`ext4` `RAID0` (`none` block scheduler) feeding background movers into `/lustre/checkpoints` |

Separating the 400 Gbps storage RDMA port from the 200 Gbps management port on the BlueField-3 BF3240 card isolates bulk data from control traffic. High-bandwidth Lustre RoCEv2 reads and checkpoint bursts never share a bonded interface with cluster management packets, Slurm heartbeats, or Kubernetes probes.

### 1.2 Why Metadata and Data Decoupling Can Still Starve GPUs

Operators often assume that adding more OST data arrays will speed up any slow AI job. Yet when a vision job opens millions of small images, adding fifty new OSTs produces zero speedup while GPUs sit idle. The data disks remain unused because every file access is bottlenecked on the metadata servers before a single byte of payload moves.

As established in Chapter 6.19, the Lustre client module `lustre.ko` splits every file operation across three internal client subsystems over LNet. The Management Client reads cluster target maps from the MGS at mount time. The Metadata Client sends namespace operations such as `open`, `close`, `stat`, `getattr`, `mkdir`, `unlink`, and `getxattr` to MDS nodes backed by NVMe RAID 10 MDTs. The MDS returns a layout extended attribute describing which OST objects store the file stripes. The Object Storage Client and Logical Object Volume then perform parallel RDMA transfers directly against the OSS and OST nodes.

```text
Lustre Client Module & Target Performance Summary:
- MGC (Management Client) -> MGS (Management Server): mount-time cluster target maps
- MDC (Metadata Client) -> MDS / MDT (NVMe RAID-10): 50,000 to 100,000 metadata ops/sec per MDS; returns LOV EA layout
- OSC / LOV (Object Storage Client / Logical Object Volume) -> OSS / OST:
  * Spinning or hybrid RAID-6 OST: 100 to 800 MB/s per OST
  * All-NVMe ZFS or ldiskfs OST: 5,000+ MB/s per OST
- Core Invariant: Striping distributes data I/O across C OSTs, but every open(), stat(), and close() still hits the MDS.
```

Wide striping actually increases metadata and lock overhead for small files. Creating, statting to find file size across stripes, or unlinking a file with $C$ stripes requires managing $C$ child OST objects plus the MDT inode. Therefore, AI Lustre engineering requires co-designing progressive stripe layouts and distributed metadata simultaneously.

---

## 2. Progressive File Layouts (PFL), Data-on-MDT (DoM), and Striping Math

In a shared AI workspace such as `/lustre/ai-workspace`, data scientists and training jobs write files spanning seven orders of magnitude. These artifacts range from tiny YAML configuration files and JPEG images to multi-gigabyte WebDataset tar shards and huge checkpoints. Applying a single static stripe count to that shared directory guarantees a performance failure at one end of the spectrum.

If the directory keeps the Lustre default stripe count of one, a large checkpoint or dataset shard is pinned to a single OST. Sequential throughput hits a wall at the speed of that one target while twenty-three other OSTs sit idle. Conversely, if the directory stripes every file across all twenty-four OSTs, a tiny image smaller than the stripe size still lands inside the first chunk on one OST. That small file gains zero read parallelism while forcing the client and MDS to allocate, stat, and clean up two dozen object references.

```text
Static Striping Failure Extremes on a 24-OST Cluster:
- File size range in /lustre/ai-workspace: 4 KiB YAML configs, 260 KB JPEGs, 26 GB WebDataset shards, 500 GB checkpoints
- Case A (stripe_count = 1 default):
  * 500 GB checkpoint or 26 GB shard is pinned to 1 OST (500 to 800 MB/s on HDD/hybrid or 5 GB/s on NVMe)
  * Remaining 23 OSTs sit 100% idle
- Case B (stripe_count = 16 or -c -1 across all 24 OSTs):
  * 260 KB file with 1 MiB (1,048,576-byte) stripe_size fits entirely in chunk 0 on OST slot 0
  * Gains 0 read parallelism while allocating and statting 16 to 24 OST object references
```

### 2.1 Round-Robin RAID0 Striping Math vs the "Contiguous Halves" Fallacy

A common misconception is that striping a one-gigabyte file across two OSTs splits the file into two contiguous five-hundred-megabyte halves. When engineers write custom dataloaders or checkpoint readers under this assumption, their byte-range reads fail to parallelize across drives. Understanding the exact chunk-mapping math prevents sub-stripe read stalls.

When a file has a stripe size $S$ and a stripe count $C$, Lustre slices the logical byte stream into fixed chunks of size $S$. The stripe size defaults to four megabytes in modern Lustre releases or one megabyte in older releases. It must always be a multiple of sixty-four kilobytes. Lustre then assigns each chunk round-robin across the $C$ OST slots starting at the initial stripe offset $O_0$.

```text
Lustre RAID0 Round-Robin Chunk Mapping Formulas:
  chunk_index(b) = floor(b / S)
  ost_slot(b)    = chunk_index(b) mod C
  ost_id(b)      = (O_0 + ost_slot(b)) mod N_OST

Concrete Example (lfs getstripe /lustre/test-file.bin, untested here):
- File size: 1 GiB (1,024 MiB) | stripe_size S = 1048576 (1 MiB) | stripe_count C = 2 | stripe_offset O_0 = 0
- OST 0 holds even chunks: 0, 2, 4, ..., 1022 (512 chunks = 512 MiB total)
- OST 1 holds odd chunks:  1, 3, 5, ..., 1023 (512 chunks = 512 MiB total)
- Sub-stripe read (512 KiB at offset 0 with S = 1 MiB, C = 8):
  * Touches only chunk 0 (ost_slot = 0) -> uses exactly 1 OST (zero stripe parallelism)
- Multi-stripe sequential read (16 MiB batch read with S = 2 MiB, C = 8):
  * Spans 8 consecutive 2 MiB chunks (chunks 0..7) -> hits all 8 OSTs in parallel (2 MiB per OST)
  * At 800 MB/s per OST, read bandwidth scales from 1.6 GB/s (2 * 800 MB/s at C = 2) to 6.4 GB/s (8 * 800 MB/s at C = 8)
```

### 2.2 Composite Layouts: Progressive File Layout (PFL) + Data-on-MDT (DoM)

Progressive File Layout solves the bimodal file-size dilemma by dividing a file's logical offset space into sequential components defined with `-E`. Each component has its own layout type, stripe count `-c`, stripe size `-S`, and optional OST pool `-p`. Components beyond the current end of the file remain uninstantiated until a write extends the file past the previous boundary.

Data-on-MDT, enabled with `-L mdt`, places the first PFL component directly on the NVMe MDT alongside the file inode. When a training worker opens and reads a tiny manifest or image under one megabyte, the client receives both layout and payload from the MDT in one round-trip. This optimization allocates zero OST objects and eliminates Object Storage Client lock and RPC traffic completely.

```mermaid
flowchart LR
    File["Logical File Byte Offset<br/>(0 bytes to Multi-Hundred GiB)"] --> C0["Component 0: [0, 1 MiB)<br/>-E 1M -L mdt (Data-on-MDT)<br/>0 OSTs | Single-hop NVMe MDT I/O"]
    C0 -->|"File grows > 1 MiB"| C1["Component 1: [1 MiB, 64 MiB)<br/>-E 64M -c 1 -S 1M<br/>1 OST | Low RPC & lock overhead"]
    C1 -->|"File grows > 64 MiB"| C2["Component 2: [64 MiB, 4 GiB)<br/>-E 4G -c 4 -S 4M<br/>4 OSTs | Shards (WebDataset/Parquet)"]
    C2 -->|"File grows > 4 GiB"| C3["Component 3: [4 GiB, EOF)<br/>-E -1 -c -1 -S 4M<br/>All 24 OSTs | Full checkpoint BW"]
```

| PFL Component Range | `lfs setstripe` Clause | Target AI Artifacts | Instantiated Objects (`24`-OST Cluster) | Primary Performance Benefit |
|---|---|---|---|---|
| **`[0, 1 MiB)`** | `-E 1M -L mdt` | Configs (`YAML`/`JSON`), tokenizer vocabs, small `< 1 MiB` images (`260 KB`) | `1` `MDT` inode + data block (`0` `OST` objects) | Eliminates `OST` object creation, `OSC` `getattr` RPCs, and spinning-disk seek latency |
| **`[1 MiB, 64 MiB)`** | `-E 64M -c 1 -S 1M` | Medium images, audio clips, per-step TensorBoard logs (`32 MiB`) | `1` `MDT` (`1 MiB`) + `1` `OST` (`31 MiB` for a `32 MiB` file) | Avoids over-striping medium files; MDS balances single-stripe files across `OST`s via `-i -1` |
| **`[64 MiB, 4 GiB)`** | `-E 4G -c 4 -S 4M` | `WebDataset` `.tar` shards, `Parquet` / `TFRecord` files (`512 MiB`–`2 GiB`) | `1` `MDT` (`1 MiB`) + `1` `OST` (`63 MiB`) + `4` `OST`s (`448 MiB` for a `512 MiB` shard) | `4x` parallel `OST` bandwidth per shard (`2–3.2 GB/s`) with `4 MiB` chunks aligned to large RDMA RPCs |
| **`[4 GiB, EOF)`** | `-E -1 -c -1 -S 4M` | Large dataset shards (`26 GB`) and monolithic/consolidated checkpoints (`10 GiB`–`500 GB`) | All `24` `OST`s active for bytes above `4 GiB` (`10 GiB` file puts `6 GiB` across `24` `OST`s) | Automatically unlocks full cluster write/read bandwidth (`12+ GB/s` to `560+ GB/s`) without manual per-file flags |

Administrators can also combine PFL with self-extending layouts using `-z` or `--extension-size` so that Lustre dynamically skips OSTs approaching capacity limits in `lfs df -h`. Pairing PFL with OST pools via `-p flash` and `-p disk` ensures that hot training datasets reside on NVMe OSTs while cold archival checkpoints migrate to high-capacity disk pools.

---

## 3. Metadata Scaling at Scale: DNE Phase 1/2, `statahead`, and Dataset Sharding

AI training pipelines punish Lustre metadata subsystems at three distinct points in the job lifecycle. At job startup, a thousand ranks importing Python libraries simultaneously generate millions of `stat` and `open` calls across shared package search paths. At the start of every epoch, dataloader workers open and stat millions of unsharded training files. Finally, every thirty minutes, checkpoint routines create over a thousand shard files and run recursive deletions on expired checkpoint directories.

### 3.1 Diagnosing Metadata Saturation with `lctl get_param llite.*.stats`

When a training loop stalls, operators often waste hours investigating network switches or OST disk arrays when the real bottleneck is the MDS. To prove whether a slow job is bound on metadata rather than data bandwidth, inspect the client-side `llite` statistics using `lctl get_param llite.*.stats`. Comparing a healthy cluster against a saturated production cluster immediately reveals metadata queueing.

| Metric (`1`-Minute Window) | Healthy Metadata Headroom (`lustre-1a5c`) | Saturated Metadata Bottleneck (`lustre-1a5c`) | Operational Interpretation |
|---|---|---|---|
| **`open` samples & rate** | `150,000` samples (`2,500` opens/sec) | `950,000` samples (`15,833` opens/sec) | Aggregate rate across `open` + `close` + `getattr` (`3,800,000` total ops/min = `63,333` ops/sec) exceeds single-`MDS` `50K` threshold |
| **`open` latency (`min / avg / max`)** | `800 us` / **`2,100 us` (`2.1 ms`)** / `5,400 us` (`5.4 ms`) | `1,200 us` / **`45,200 us` (`45.2 ms`)** / `65,400 us` (`65.4 ms`) | Healthy `open()` is `< 5 ms`. At `45.2 ms` avg (or `120 ms` during `150K`-open epoch bursts), GPUs stall waiting for file descriptors |
| **`close` latency (`min / avg / max`)** | `600 us` / **`1,800 us` (`1.8 ms`)** / `4,200 us` (`4.2 ms`) | `800 us` / **`42,100 us`** / `58,900 us` | High `close()` latency confirms `MDS` worker threads (`mdt_thread`) and `MDT` journal commits are queued |
| **`getattr` samples & latency** | `300,000` samples (`400 / 2,200 / 8,900 us` = `2.2 ms` avg) | `1,900,000` samples (`400 / 78,900 / 102,000 us` = `102 ms` max) | `2x` as many `getattr` (`stat`) calls as `open` calls; `102 ms` max `getattr` stalls directory listings and dataset indexing |

### 3.2 Distributed Namespace (DNE Phase 1 vs Phase 2) Across Multiple MDTs

A single MDS typically sustains fifty thousand to one hundred thousand metadata operations per second depending on MDT NVMe media and RPC complexity. When a hundred-node training job demands two hundred thousand operations per second, one MDS cannot keep up. Lustre's Distributed Namespace scales metadata horizontally across multiple MDTs under a single mount point `/lustre`. However, DNE Phase 1 and DNE Phase 2 behave very differently when confronted with flat AI dataset directories.

DNE Phase 1 creates remote directories using `lfs mkdir -i`, which pins an entire subdirectory tree to a specific MDT index. If a vision dataset stores millions of images inside a single flat directory such as `/lustre/imagenet/train`, DNE Phase 1 routes every single lookup to whichever MDT owns that directory. Having four MDTs provides zero speedup for that flat directory unless the dataset is manually split across separate subdirectories on each MDT.

DNE Phase 2 solves the flat-directory problem by creating striped directories with `lfs setdirstripe -c` or `lfs mkdir -c`. It splits a single large directory across multiple MDTs by hashing each filename to one of the MDT shards. Opening two hundred thousand files inside `/lustre/imagenet/train` now fans out evenly across all four MDTs, cutting epoch-start open time by fourfold. Because cross-MDT directory operations require distributed coordination, administrators pair DNE Phase 2 with client-side statahead and Asynchronous Glimpse Locking for sequential directory scans.

```text
DNE Phase 1 vs Phase 2 Metadata Scaling (4 MDTs @ 50,000 ops/sec each = 200,000 ops/sec max):
- Workload: 128 GPU clients opening 200,000 or 5,000,000 files in /lustre/imagenet/train
- DNE Phase 1 (Remote Directories):
  * Commands: lfs mkdir -i 0 /lustre/dataset-mdt0 ; lfs mkdir -i 1 /lustre/dataset-mdt1 ; lfs mkdir -i 2 /lustre/dataset-mdt2
  * Single flat directory behavior: active_mdts = 1 (MDT0 only), MDT1..MDT3 sit idle (0% speedup)
  * Throughput & time for 200,000 files in 1 dir: 50,000 ops/sec -> 4.0 seconds
- DNE Phase 2 (Striped Directories):
  * Commands: lfs mkdir -c 4 /lustre/imagenet/train ; lfs setdirstripe -D -c -1 /lustre/checkpoints
  * Hash mechanism: crush / fnv filename hash distributes 50,000 files per MDT across MDT0..MDT3
  * Throughput & time for 200,000 files in 1 dir: active_mdts = 4, 200,000 ops/sec -> 1.0 second (4x faster)
  * Client readdir / stat prefetch tuning: llite.*.statahead_max = 64 or 128, statahead_agl = 1
```

### 3.3 The 1,000x Multiplier: Dataset Repackaging and Containerized Environments

Even with four MDTs running DNE Phase 2 at two hundred thousand operations per second, opening ten million individual raw files per epoch requires thirty million total open, stat, and close RPCs. Whenever adding MDS hardware is out of scope, the highest-leverage engineering fix is repackaging small files into contiguous shards. Packing a multi-million-file dataset into WebDataset tar archives, TFRecord files, or Parquet shards converts a metadata-bound random-I/O workload into a sequential bulk-streaming workload where Lustre excels.

At the same time, operators must stop running Python or Conda virtual environments directly from `/lustre` at scale. When a thousand ranks run import statements simultaneously, Python walks every directory on the module search path and floods the MDS with millions of stat calls. Packaging training environments into read-only SquashFS container images staged onto node-local NVMe eliminates import storms completely.

```text
Dataset Repackaging & Containerization Impact on Metadata RPCs:
1. Moderate Sharding (5,000,000 files -> 50,000 shards at 100 files/shard):
   - Reduces open() calls per epoch by 100x (5,000,000 -> 50,000)
   - Cuts a 3-minute (180 s) epoch-start stall down to under 2 seconds
2. Full AI Factory Sharding (10,000,000 files at 260 KB avg = 2.6 TB total -> 100 shards of 26 GB each at 100,000 files/shard):
   - Format: WebDataset (.tar), TFRecord, or Parquet striped across 8 to 16 OSTs (lfs setstripe -c 16 -S 2M)
   - Reduces open() pressure from 150,000+ opens/min to 100 opens per epoch (1,500x to 100,000x reduction; 0.0005 s across 4 MDTs)
3. Python Import Storm Mitigation:
   - Never run Conda / venv from /lustre across 1,000 GPUs (import torch, transformers triggers millions of stat() calls)
   - Stage read-only SquashFS images (Enroot / Pyxis or Singularity / Apptainer) onto node-local NVMe RAID0
```

---
## 4. LNet Multi-Rail Networking, Client RPC BDP Tuning, and GPUDirect Storage

Even after an engineer eliminates metadata bottlenecks and stripes dataset shards across two dozen OSTs, a single misconfigured GPU node can still read five times slower than its peers. Because distributed training runs at the speed of the slowest worker at every all-reduce barrier, one throttled client drags down the entire multi-node job. Once layout striping is correct, data-plane throughput depends on three client-to-OSS layers: LNet multi-rail RDMA networking, Object Storage Client RPC queue depth, and GPUDirect Storage.

### 4.1 LNet Multi-Rail (`o2ib` / `RoCEv2`), Port `988`, and NUMA/PCIe Affinity

Lustre Networking abstracts underlying network fabrics through pluggable Lustre Network Drivers. The kernel TCP driver `ksocklnd` uses TCP port 988. Host and datacenter firewalls must allow that port for management fallback, though TCP becomes CPU-bound at 400 Gbps line rates. Production AI data planes use the native RDMA Verbs driver `ko2iblnd` over both InfiniBand and RoCEv2 Ethernet. Each protocol name and number forms an isolated LNet subnet. Clients on `@o2ib0` can only communicate directly with servers on `@o2ib0` unless LNet routers bridge the subnets.

On multi-NIC GPU nodes and DGX compute trays, LNet Multi-Rail aggregates multiple local NICs. It uses User-Defined Selection Policies alongside LNet Health scoring to steer RDMA traffic. First, LNet Multi-Rail selects the local storage rail on the same NUMA socket and PCIe switch as the CPU or GPU initiating the transfer. If a dataloader thread or GPUDirect Storage buffer on one NUMA socket must cross the inter-socket link to a NIC on the opposite socket, that client runs five times slower than peers. Dropping from jumbo frames to standard frames causes the same fivefold penalty. Second, when `lnetctl` detects transmit errors or timeouts on one network identifier, LNet decrements that rail's health score and fails over to the surviving rail without evicting the client.

```text
LNet Transport, Multi-Rail Affinity, and Health Parameters:
- LND Drivers:
  * ksocklnd (@tcp0, @tcp1): Kernel TCP/IP transport on TCP port 988 (MGS / management fallback)
  * ko2iblnd (@o2ib0, @o2ib1): RDMA Verbs over InfiniBand (ib0, ib1) or RoCEv2 (ens1f0, enp1s0f0np0)
- Namespace isolation: 10.20.4.15@o2ib0 communicates directly only with @o2ib0 targets
- NUMA & MTU locality:
  * Dual storage NICs: ib0 on NUMA 0, ib1 on NUMA 1 (PCIe PIX / PXB switch locality)
  * Cross-socket hairpin (NUMA 0 buffer -> UPI/QPI/NVLink-C2C -> NUMA 1 NIC) or MTU 1500 vs MTU 9000 causes a 5x single-client slowdown
- LNet Health & Failover (lnet_health_sensitivity, lnet_recovery_limit):
  * On send timeout or drop on 10.20.4.16@o2ib0, health score decrements (1000 -> 0) and RPCs steer to 10.20.4.15@o2ib0
```

### 4.2 Client RPC Bandwidth-Delay Product (`BDP`) Math and OSC Tunables

Even over a healthy 400 Gbps RDMA rail, a Lustre client cannot saturate an all-NVMe OST unless its Object Storage Client keeps enough bytes in flight to cover the network and storage round-trip time. Under heavy cluster load, NVMe queue depths rise and round-trip latency increases from half a millisecond to several milliseconds. With conservative default queue settings, the client runs out of credits and sits idle waiting for acknowledgments while the network link remains two-thirds empty.

For each OST connection, Little's Law defines the maximum single-OST throughput as the ratio of in-flight bytes to round-trip time. Raising the maximum pages per RPC to match a four-megabyte stripe size and increasing maximum RPCs in flight to sixty-four expands the per-OST window thirty-two-fold. That larger window easily saturates eight NVMe OSTs in parallel and fills a 400 Gbps client NIC even under congested four-millisecond storage latencies.

```text
Lustre Client OSC Bandwidth-Delay Product (BDP) Equations & Derivations:
  RPC_Size            = max_pages_per_rpc * Page_Size   (where Page_Size = 4 KiB = 4,096 bytes on x86_64)
  In_Flight_Bytes_OST = max_rpcs_in_flight * RPC_Size
  B_OST_BDP           = In_Flight_Bytes_OST / RTT

1. Legacy / Conservative Client Defaults (max_rpcs_in_flight = 8, max_pages_per_rpc = 256):
   - RPC_Size = 256 * 4 KiB = 1 MiB (1,048,576 bytes)
   - In_Flight_Bytes_OST = 8 * 1 MiB = 8 MiB (8,388,608 bytes)
   - At uncongested RTT = 500 us (0.0005 s): B_OST_BDP = 8,388,608 / 0.0005 = 16,777.22 MB/s (sufficient for 800 or 5,000 MB/s OST)
   - At congested RTT = 4,000 us (4.0 ms): B_OST_BDP = 2,097.15 MB/s (~2.1 GB/s) -> starves a 6,000 MB/s (6 GB/s) NVMe OST by ~3x (8 OSTs cap at 16,777.22 MB/s)

2. AI-Tuned Client (max_rpcs_in_flight = 64, max_pages_per_rpc = 1024 [4 MiB] or 4096 [16 MiB]):
   - RPC_Size = 1024 * 4 KiB = 4 MiB (matches stripe_size = 4M)
   - In_Flight_Bytes_OST = 64 * 4 MiB = 256 MiB per OST
   - At congested RTT = 4,000 us (4.0 ms): B_OST_BDP = 67,108.86 MB/s per OST
   - Across 8 NVMe OSTs at 6,000 MB/s each: 8 * 6,000 = 48,000 MB/s (48.0 GB/s), saturating a 400 Gbps (50 GB/s) client NIC

3. Server-Side OSS RAM Sizing Formulas (Supercomputers for Linux SysAdmins):
   - Per-OST baseline RAM: 400 MB (logging) + 600 MB (metadata caching) + 1.5 MB * N_threads
     (For 6 OSTs serving 120 clients, N_threads = 120 / 6 = 20 -> 1,000 + 1.5 * 20 = 1,030 MB per OST)
   - Recommended total OSS RAM: 2 GB + 1 GB per OST (For 6 OSTs -> 2 + 6 = 8.0 GB minimum)
```

| Client / Server Tunable (`lctl set_param`) | Typical Default | AI Training / Checkpoint Value | Why It Matters for GPU Workloads |
|---|---|---|---|
| `osc.*.max_pages_per_rpc` | `256` (`1 MiB`) or `1024` (`4 MiB`) | `1024` (`4 MiB`) or `4096` (`16 MiB`) | Amortizes RDMA memory registration and RPC framing overhead across `4 MiB`–`16 MiB` bulk transfers; match to `stripe_size` |
| `osc.*.max_rpcs_in_flight` | `8` | `32` to `64` | Multiplies per-`OST` in-flight window (`BDP`) by `4x–8x` so high-latency bursts do not stall NVMe `OST` pipelines |
| `osc.*.max_dirty_mb` | `32`–`2000` MiB | `512` to `2048` MiB | Controls buffered writeback cache per `OSC` before throttling dirty pages (Ensure total `N_OST * max_dirty_mb` fits safely in client RAM) |
| `mdc.*.max_rpcs_in_flight` | `8` | `32` to `64` | Allows parallel dataloader workers on a multi-GPU node to keep `32–64` concurrent `open`/`getattr` RPCs in flight to each `MDT` |
| `llite.*.max_read_ahead_mb` | `64`–`1024` MiB | `2048` to `4096` MiB | Critical for sequential buffered reads of `WebDataset` / `TFRecord` / `Parquet` shards |
| `llite.*.max_read_ahead_per_file_mb` | `64` MiB | `256` to `1024` MiB | Allows a single large shard reader to prefetch hundreds of MiB across all striped `OST`s |
| `llite.*.statahead_max` | `32` | `64` to `128` | Prefetches directory entry attributes asynchronously during `readdir` / `ls -l` or dataset directory scans |
| `ost.OSS.ost_io.threads_max` | `64`–`512` (auto) | `512` to `1024` | Prevents `OSS` service thread exhaustion when thousands of GPU ranks flush checkpoints simultaneously (each thread uses `~1.5 MB` RAM) |

### 4.3 GPUDirect Storage (`GDS`) with Lustre and Mount Options (`flock,lazystatfs`)

When reading training shards or loading hundred-gigabyte model weights into GPU memory, standard POSIX buffered reads copy data twice on the host. Data travels from the OSS to the LNet NIC and lands in the Linux page cache in host DRAM. It then copies into a pinned user buffer and finally crosses PCIe or NVLink-C2C into GPU memory. Those redundant host copies burn CPU cycles needed for tokenization and add latency to every batch load.

With NVIDIA GPUDirect Storage and a GDS-enabled Lustre client combining `nvidia-fs.ko` and `lustre.ko` over `ko2iblnd`, files open with `O_DIRECT` to bypass the page cache. Because FUSE userspace filesystems bounce buffers through userspace and lack kernel DMA hooks, they cannot support GDS. Under GDS, `cuFileRead` and `cuFileWrite` instruct the RDMA NIC to transfer OST stripes directly into or out of GPU memory. That direct path boosts throughput by twenty percent and cuts latency by twenty percent in standard `gdsio` benchmarks.

Finally, every production AI Lustre client mount in `/etc/fstab` or systemd must include `-o flock,lazystatfs,noatime`. Enabling `flock` provides coherent cluster-wide POSIX file locking. Using `localflock` corrupts shared caches across nodes, while omitting `flock` returns `ENOSYS` and crashes PyTorch `FileStore` rendezvous, Hugging Face locks, and SQLite stores. Adding `lazystatfs` lets `df` and Kubernetes kubelet probes return immediately from cached MDS data instead of hanging when one OST degrades. Lastly, `noatime` stops redundant access-time writes on the MDT.

```text
GPUDirect Storage (gdsio) Benchmark & Mount Option Reference:
- Command (untested here): /usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0
  * CPU bounce-buffer path (-x 2): 8.0 GB/s throughput, 1.25 ms average latency
  * Direct GDS path Storage -> GPU BAR1 / C2C (-x 0): 9.6 GB/s throughput (+20.0%), 1.00 ms average latency (-20.0%)
- Mandatory Client Mount Command (untested here):
  mount -t lustre -o flock,lazystatfs,noatime mgs1@o2ib0,mgs2@o2ib0:/ai_fs /lustre
```

---

## 5. Checkpoint Architecture on Lustre: N-to-1 Lock Contention vs N-to-N Sharded Writes

During large-scale language or multimodal model training, checkpointing produces the most violent write burst a storage system ever sees. Every thirty to sixty minutes, hundreds or thousands of GPU ranks pause to flush hundreds of gigabytes to several terabytes of model weights and Adam optimizer states. If the storage layout or locking pattern is misconfigured, checkpoint stalls can consume thirty percent of total cluster GPU hours.

### 5.1 Why Unaligned N-to-1 Shared-File Checkpoints Collapse Under LDLM Locking

Lustre enforces strict POSIX byte-range cache coherency across all clients using the Lustre Distributed Lock Manager. Each OST manages Protected Write extent locks rounded to page and stripe boundaries. Understanding how four common checkpoint write patterns interact with LDLM extent locks explains why some jobs stall for ten minutes while others finish in ten seconds.

In the first pattern, a job writes a shared checkpoint into a directory left at the default stripe count of one. The entire five-hundred-gigabyte dump serializes onto a single OST, stalling the cluster for over ten minutes while twenty-three other OSTs sit idle. In the second pattern, sixty-four ranks open one shared file striped across twelve OSTs and write variable-length tensor slices without aligning offsets to the four-megabyte stripe size. Whenever two ranks write inside the same four-megabyte stripe extent on an OST, that OST must revoke the first rank's lock and flush its dirty pages. It then grants the lock to the second rank, and this lock ping-pong slashes effective bandwidth by fourfold.

In the third pattern, an application uses collective buffering such as MPI-IO or stripe-aligned `cuFileWrite` offsets. Every rank writes exact multiples of the four-megabyte stripe size across all OSTs, keeping lock contention low and reaching over ninety percent of hardware peak. In the fourth and preferred pattern, modern frameworks such as PyTorch Distributed Checkpointing write N-to-N sharded files. Each rank writes its own independent shard file into a DNE-striped directory, achieving zero cross-node lock contention and full hardware bandwidth.

```text
Checkpoint Write Patterns & LDLM Lock Math (500 GB Checkpoint on 64 Ranks; 12 to 16 Bytes/Param FP32 + Adam):
1. Pattern A — Single-OST N-to-1 / Rank-0 Write (stripe_count = 1):
   - 500 GB lands on 1 OST -> 625.0 seconds (10.4 minutes) at 800 MB/s, or 500 seconds (8.3 minutes; 15-30 min with serialization) at 1,000 MB/s
2. Pattern B — Unaligned N-to-1 Shared File (stripe_count = 12 OSTs @ 1,000 MB/s = 12.0 GB/s peak):
   - Unaligned tensor writes inside 4 MiB stripe extents trigger PW extent lock ping-pong (~25% efficiency)
   - Effective throughput drops 4x to 3.0 GB/s -> 166.67 seconds (vs 41.67 seconds ideal)
3. Pattern C — Stripe-Aligned N-to-1 Shared File (lfs setstripe -c -1 -S 4M across 24 OSTs):
   - Allocates 500 GB / 24 = 20.83 GB (~21 GB) per OST; 4 MiB / 16 MiB aligned writes reach 90%+ peak (~10.8 GB/s, ~46.3 s)
4. Pattern D — Sharded N-to-N Write (PyTorch DCP / Megatron-LM / DeepSpeed per-rank shards: rank_0000.distcp ..):
   - 1 writer per file -> zero cross-node LDLM extent lock contention
   - 500 GB / 64 ranks = 7.81 GB per rank shard with narrow stripe (lfs setstripe -c 1 to -c 4 -i -1) across 24 OSTs @ 500 MB/s
   - Reaches full 12.0 GB/s (24 * 500 MB/s) in 41.67 seconds (15x faster than 625 s single-OST)
   - On 4-SU SuperPOD Enhanced tier (560 GB/s across 112 NVMe OSTs @ 5 GB/s each): 5.6 TB (5,600 GB) checkpoint completes in 10.0 seconds
```

| Checkpoint Pattern | Directory `lfs setstripe` Policy | `LDLM` Lock Contention | `500 GB` Write Time (`24` OSTs @ `500–800 MB/s`) | Recommended AI Use Case |
|---|---|---|---|---|
| **1. Single-OST `N-to-1` / Rank-0** | `-c 1` (untuned default) | None (serialized on `1` `OST`) | **`625.0 s`** (`@ 800 MB/s`) | **Anti-pattern** — never use for multi-GB checkpoints |
| **2. Unaligned Shared `N-to-1`** | `-c 12` or `-c -1`, unaligned offsets | **Severe** (`PW` lock ping-pong, `~25%` eff.) | **`166.67 s`** (`@ 3.0 GB/s` on `12`x`1 GB/s` OSTs) | **Anti-pattern** — avoid unaligned multi-rank writes to one file |
| **3. Aligned Shared `N-to-1`** | `-c -1 -S 4M` (all `OST`s, `4 MiB` aligned) | Low (one rank per `4 MiB` stripe extent) | **`~46.3 s`** (`@ 10.8 GB/s`) | Legacy monolithic `.pt` / `.safetensors` exports or `MPI-IO` |
| **4. Sharded `N-to-N` (`PyTorch DCP`)** | `-c 1` to `-c 4 -S 4M -i -1` + DNE dir stripe | **Zero** (1 writer per file; `O_LOV_DELAY_CREATE`) | **`41.67 s`** (`@ 12.0 GB/s` across `24` OSTs) | **Production standard** for LLM/multimodal FSDP/TP/PP training |

Production pipelines combine N-to-N sharded Lustre layouts with two-stage asynchronous checkpointing. Each node copies GPU tensors over PCIe Gen5 or NVLink-C2C into pinned host DRAM or local RAID 0 NVMe drives in under two seconds. GPU training resumes immediately while background worker threads drain the shards to `/lustre/checkpoints`.

---

## Commands and configurations that matter

All commands below reflect standard Lustre administration and tuning workflows using `lfs`, `lctl`, `lnetctl`, `mkfs.lustre`, `mount.lustre`, `gdsio`, and `fio` from the cited sources. They are marked `untested here` where live multi-node Lustre kernel modules and RDMA hardware are absent in this local verification environment.

### 6.1 LNet Multi-Rail Configuration (`/etc/modprobe.d/lustre.conf` and `lnetctl`)

```bash
# (untested here) — 1. Configure LNet multi-rail in /etc/modprobe.d/lustre.conf
# Binds o2ib0 to dual 400G RoCEv2/IB interfaces (ib0 on NUMA 0, ib1 on NUMA 1)
# plus tcp0 fallback on eth2 (uses TCP port 988; ensure firewall allows TCP 988)
cat <<'EOF' > /etc/modprobe.d/lustre.conf
options lnet networks="o2ib0(ib0,ib1),tcp0(eth2)"
options ko2iblnd peer_credits=128 peer_credits_hiw=64 credits=2048 concurrent_sends=128 ntx=2048 map_on_demand=32
EOF

# (untested here) — 2. Load LNet and inspect multi-rail NIDs, NUMA cpt, and health
modprobe lnet
lnetctl lnet configure
lnetctl net show -v
lctl list_nids
# Expected output on a dual-rail GPU node:
# 10.20.4.15@o2ib
# 10.20.4.16@o2ib
# 192.168.2.15@tcp

# (untested here) — 3. Verify LNet reachability and peer NID health statistics
lctl ping 10.20.1.10@o2ib
lnetctl peer show -v --nid 10.20.1.10@o2ib
lnetctl stats show
```

### 6.2 Client Mount with `flock,lazystatfs,noatime` and OSC/MDC/LLITE Tuning

```bash
# (untested here) — 1. Mount Lustre with HA MGS NIDs, global flock, lazystatfs, and noatime
mkdir -p /lustre
mount -t lustre -o flock,lazystatfs,noatime \
  10.20.1.10@o2ib0,10.20.1.11@o2ib0:/ai_fs /lustre

# (untested here) — 2. Apply AI client RPC BDP and read-ahead tunables
lctl set_param osc.*.max_pages_per_rpc=1024          # 4 MiB RPCs (or 4096 for 16 MiB)
lctl set_param osc.*.max_rpcs_in_flight=64           # 64 * 4 MiB = 256 MiB in flight per OST
lctl set_param osc.*.max_dirty_mb=1024               # 1 GiB writeback cache per OSC
lctl set_param mdc.*.max_rpcs_in_flight=64           # Parallel metadata RPCs for dataloader workers
lctl set_param llite.*.max_read_ahead_mb=4096        # 4 GiB aggregate client read-ahead
lctl set_param llite.*.max_read_ahead_per_file_mb=512
lctl set_param llite.*.statahead_max=128             # Async directory stat prefetching
```

### 6.3 Configuring DNE Directories, PFL + DoM Layouts, and Checkpoint Striping

```bash
# (untested here) — 1. DNE Phase 1 (pin directory to MDT index) vs Phase 2 (hash across 4 MDTs)
lfs mkdir -i 0 /lustre/datasets-mdt0
lfs mkdir -i 1 /lustre/datasets-mdt1
lfs mkdir -c 4 /lustre/imagenet-sharded              # DNE Phase 2: stripe single dir across 4 MDTs
lfs setdirstripe -D -c -1 /lustre/checkpoints        # Default: stripe new checkpoint subdirs across all MDTs
lfs getdirstripe /lustre/imagenet-sharded

# (untested here) — 2. Set a 4-tier PFL + Data-on-MDT (DoM) default layout on /lustre/ai-workspace
# [0, 1M): DoM on MDT | [1M, 64M): 1 OST, 1M stripe | [64M, 4G): 4 OSTs, 4M | [4G, EOF): all OSTs, 4M
lfs setstripe \
  -E 1M -L mdt \
  -E 64M -c 1 -S 1M \
  -E 4G -c 4 -S 4M \
  -E -1 -c -1 -S 4M \
  /lustre/ai-workspace
lfs getstripe -d /lustre/ai-workspace

# (untested here) — 3. Explicit striping for packed training shards vs N-to-1 / N-to-N checkpoints
lfs setstripe -c 16 -S 2M /lustre/training-data/     # 16 OSTs, 2 MiB stripe for WebDataset/Parquet shards
lfs setstripe -c -1 -S 4M /lustre/checkpoints-n1/    # All OSTs for aligned N-to-1 monolithic checkpoints
lfs setstripe -c 2  -S 4M -i -1 /lustre/checkpoints-dcp/ # 2 OSTs per rank shard for N-to-N PyTorch DCP
```

### 6.4 Live Metadata, OST Balance, Migration, and GPUDirect Storage (`gdsio`) Verification

```bash
# (untested here) — 1. Measure real-time client metadata pressure (open, close, getattr, readdir)
lctl get_param llite.*.stats | grep -E "^  open|^  close|^  getattr|^  readdir"
watch -n 1 'lctl get_param llite.*.stats | grep "^  open" | tail -3'

# (untested here) — 2. Inspect MDT/OST capacity and inode balance (healthy: all OSTs within +-5%)
lfs df -h
lfs df -i

# (untested here) — 3. Rebalance files off a 98%-full OST (e.g., OST0) onto balanced OSTs
lfs find /lustre/training-data --ost ai_fs-OST0000 -type f -print0 | lfs migrate -0 -c 16 -S 2M

# (untested here) — 4. Verify GPUDirect Storage (GDS) read bandwidth & latency vs CPU path
# CPU bounce-buffer baseline (-x 2): 8.0 GB/s, 1.25 ms avg latency
/usr/local/cuda/gds/tools/gdsio -f /lustre/training-data/shard-000.tar -d 0 -w 4 -s 10G -i 1M -I 0 -x 2
# Direct GDS path Storage -> GPU BAR1 (-x 0): 9.6 GB/s (+20%), 1.00 ms (-20%) avg latency
/usr/local/cuda/gds/tools/gdsio -f /lustre/training-data/shard-000.tar -d 0 -w 4 -s 10G -i 1M -I 0 -x 0
```

---

## How it fails

When a Lustre issue strikes a running training job, symptoms almost always look identical from the user side: GPU compute utilization drops to zero percent or a checkpoint step times out. Using a structured diagnostic decision tree separates metadata overload, layout mistakes, lock contention, capacity skew, and client network misconfigurations in under two minutes.

```mermaid
flowchart TD
    Incident["Symptom: Training Stall, Slow Epoch, or Failed Checkpoint"] --> Q1{"Check llite.*.stats<br/>open/getattr avg > 5 ms<br/>or rate > 50K/s?"}
    Q1 -->|"Yes (45-120 ms)"| M1["FM 1: MDS Metadata Saturation<br/>Fix: Repackage to WebDataset/Parquet,<br/>enable DNE (-c 4) & DoM (-L mdt)"]
    Q1 -->|"No (< 5 ms)"| Q2{"Check lfs getstripe<br/>on slow dataset or<br/>checkpoint directory"}
    Q2 -->|"stripe_count = 1"| M2["FM 2: Single-OST Serialization<br/>Fix: lfs setstripe -c 16 (shards)<br/>or -c -1 / N-to-N DCP (checkpoints)"]
    Q2 -->|"Wide stripe, N-to-1 write"| M3["FM 3: LDLM Extent Lock Ping-Pong<br/>Fix: Switch to N-to-N per-rank shards<br/>or align writes to 4 MiB stripe_size"]
    Q2 -->|"Layout healthy"| Q3{"Check lfs df -h<br/>Any OST >= 95% full or<br/>one OST offline?"}
    Q3 -->|"OST0 at 98% / offline"| M4["FM 4: OST Fill Skew / Hanging df<br/>Fix: Mount -o lazystatfs; deactivate<br/>& lfs migrate off hot OST"]
    Q3 -->|"OSTs balanced (49%)"| Q4{"Is 1 client 5x slower<br/>or PyTorch FileStore<br/>failing with ENOSYS?"}
    Q4 -->|"1 client 5x slower"| M5["FM 5: Client NUMA/MTU/RPC Mismatch<br/>Fix: MTU 9000, pin loader to NIC NUMA,<br/>raise max_rpcs_in_flight=64"]
    Q4 -->|"ENOSYS / lock error"| M6["FM 6: Missing -o flock Mount Option<br/>Fix: Remount all clients with<br/>-o flock,lazystatfs,noatime"]
```

| Failure Mode | Production Symptom | Exact Diagnostic Evidence | Root Cause | Remediation |
|---|---|---|---|---|
| **1. Epoch-Start Metadata Storm (`MDS` Saturation)** | Epoch 0 takes `3+` minutes to start; GPU SM utilization sits at `0–5%` while `OST` bandwidth is near zero | `lctl get_param llite.*.stats \| grep open`: `950,000` samples/min (`15.8K` opens/s), avg open latency **`45.2 ms`** (`65.4 ms` max) or **`120 ms`** during `150K`-file bursts (healthy is `< 5 ms`, `< 50K` ops/s) | Dataloader opens `5M–10M` individual `260 KB` files per epoch on `1` `MDS`, or imports Python environments directly from `/lustre` | Repackage `5M` files into `50K` shards (`100` files/shard) or `10M` files (`2.6 TB`) into `100` `WebDataset` shards (`26 GB` each, cutting opens `1,500x–100,000x`); enable DNE Phase 2 (`lfs setdirstripe -c 4`) and `DoM` (`-E 1M -L mdt`); move Conda into `SquashFS` containers |
| **2. Single-OST Serialization (`stripe_count = 1`)** | Aggregate read throughput is `100–800 MB/s` (expected `5+ GB/s` across `6` clients), or a `500 GB` checkpoint takes `10–30 minutes` (`625 s` at `800 MB/s`) | `lfs getstripe /lustre/checkpoints/ckpt.pt` or `lfs getstripe -d /lustre/dataset` shows **`stripe_count: 1`** | Directory kept Lustre's default `stripe_count = 1`, funneling all I/O for a multi-GB file onto a single `OST` | Set `lfs setstripe -c 16 -S 2M /lustre/dataset` for large shards and `-c 24` (`-c -1`) or `PFL` (`-E -1 -c -1 -S 4M`) for `/lustre/checkpoints`; run `lfs migrate -c 16` on existing large files |
| **3. Shared-File `LDLM` Lock Contention (`N-to-1` Write Stall)** | `lfs getstripe` shows `stripe_count = 12` or `24`, yet `64` ranks writing one shared `500 GB` checkpoint achieve only `3.0 GB/s` (`166.7 s`) instead of `12.0 GB/s` (`41.7 s`) | High `ldlm_cancel` and extent lock wait times in `lctl get_param osc.*.stats` and `ldlm.services.ldlm_cbd.stats` | Multiple ranks write unaligned byte ranges inside the same `4 MiB` stripe chunks, forcing `OST`s to revoke and re-grant `PW` extent locks on every write | Switch checkpointing to **`N-to-N` per-rank sharded files** (`PyTorch DCP`) with `stripe_count = 1..4` and `-i -1`, or enforce `4 MiB` stripe-aligned collective writes |
| **4. `OST` Capacity Skew (`98%` vs `60%`) & Hanging `df`** | Writes fail with `ENOSPC` even though `lfs df -h` shows `35%` free cluster space, or `df -h` / kubelet hangs when `1` `OST` is degraded | `lfs df -h` shows `OST0` at **`98%`** full while `OST1–OST5` are at **`60%`** (healthy skew is `<= ±5%`); `mount` lacks `lazystatfs` | Large `-c 1` files or pinned `stripe_offset` (`-i 0`) filled `OST0` preferentially; synchronous `statfs()` blocks on any slow/offline `OST` | Never hardcode `-i 0` (use `-i -1`); rebalance with `lfs find --ost <OST0> -print0 \| lfs migrate -0 -c 6`; mount clients with `-o lazystatfs` |
| **5. Single-Client `5x` Slowdown (NUMA / MTU / RPC BDP)** | `1` GPU worker node reads at `1 GB/s` while `7` peer nodes reading the exact same striped dataset achieve `5 GB/s` | `lfs getstripe` is identical; `ip link` shows `mtu 1500` (instead of `9000`), `lnetctl net show -v` or `numactl` shows cross-socket NIC/CPU binding, or `max_rpcs_in_flight = 8` on high-RTT paths | Dataloader threads on `NUMA 0` pull through a storage NIC on `NUMA 1`, jumbo frames (`MTU 9000`) dropped to `1500`, or `OSC` RPC window is starved | Enforce `MTU 9000` end-to-end, pin dataloader workers to the storage NIC/GPU `NUMA` node, verify `lnetctl` multi-rail health, and set `osc.*.max_rpcs_in_flight=64` |
| **6. Missing `-o flock` Breaks Distributed Coordination** | PyTorch `FileStore`, Hugging Face `datasets` cache, or SQLite crashes at job startup with `OSError: [Errno 38] Function not implemented (ENOSYS)` or corrupts shared state | `grep lustre /proc/mounts` shows default `noflock` or `localflock` instead of `flock` | By default, Lustre disables distributed POSIX `flock()` to avoid lock overhead unless explicitly requested at mount time | Remount all AI compute clients with **`-o flock,lazystatfs,noatime`** |

---

## Hands-on lab

### Venue and Scope

The local verification lab runs `code/part13/lustre_for_ai.py` and `code/part13/lustre_for_ai_lab.py` using standard-library Python with zero external dependencies. It models and verifies twenty-five production checks covering PFL and DoM object instantiation, RAID 0 round-robin chunk placement, and `lctl` metadata saturation thresholds. It also verifies DNE Phase 1 and Phase 2 scaling, WebDataset shard repackaging, OSC RPC bandwidth-delay product math, and `gdsio` throughput gains. Finally, it checks N-to-1 versus N-to-N checkpoint timing, LNet multi-rail health, OST skew, and OSS RAM sizing. For a cluster venue on GCP, GKE, or a four-VM Lustre testbed, run the commands in the previous section on live Lustre nodes.

### Run the Local Verification Lab

Run the self-checking verification suite:

```bash
python3 -B code/part13/lustre_for_ai_lab.py
```

Expected output verified in this workspace:

```text
=== Chapter 13.4 Lab: Lustre for AI Workloads ===
  [PASS] 1. 260 KiB file with DoM (-E 1M -L mdt) stays 100% on the MDT with 0 OST objects
  [PASS] 2. 32 MiB file puts first 1 MiB on DoM MDT and remaining 31 MiB on exactly 1 OST
  [PASS] 3. 512 MiB shard activates 3 PFL components (DoM 1 MiB, 1-OST 63 MiB, 4-OST 448 MiB)
  [PASS] 4. 10 GiB checkpoint file expands into the final PFL component (-E -1 -c -1) across all 24 OSTs
  [PASS] 5. RAID0 2-stripe 1 GiB file alternates 1 MiB chunks round-robin [0,1,0,1,0,1] (512 MiB per OST)
  [PASS] 6. Sub-stripe 512 KiB read on an 8-stripe file touches only 1 OST (no stripe parallelism)
  [PASS] 7. 16 MiB sequential batch read with 2 MiB stripe_size fans out evenly across all 8 OSTs
  [PASS] 8. Healthy lctl llite stats (2.1 ms avg open, 5.4 ms max, 7.5K ops/sec) reports HEALTHY_HEADROOM
  [PASS] 9. Saturated lctl llite stats (45.2 ms avg open, 65.4 ms max, 15.83K opens/s, 3800000 total samples = 63333.33/s) flags METADATA_SATURATED
  [PASS] 10. DNE Phase 1 with all 200K files in 1 directory only uses 1 active MDT (50K ops/s, 4.0 s)
  [PASS] 11. DNE Phase 2 (lfs setdirstripe -c 4) hashes 1 directory across all 4 MDTs (200K ops/s, 1.0 s)
  [PASS] 12. Repackaging 5M files into 50K shards (100 files/shard) cuts open calls 100x (100 s -> 1.0 s)
  [PASS] 13. Repackaging 10M files (2.6 TB at 260 KB) into 100 shards of 26 GB cuts opens to 100 (0.0005 s across 4 MDTs)
  [PASS] 14. Default OSC RPC (8 in-flight, 256 pages = 1 MiB) at 500 us RTT caps single-OST BDP at 16777.22 MB/s
  [PASS] 15. Tuning max_rpcs_in_flight=64 & max_pages_per_rpc=1024 (4 MiB) across 8 OSTs raises BDP from 2097.15 MB/s to 67108.86 MB/s and saturates 48 GB/s on 400G
  [PASS] 16. gdsio direct GDS path (-x 0: 9.6 GB/s, 1.00 ms) vs CPU path (-x 2: 8.0 GB/s, 1.25 ms) gives +20% BW & -20% latency
  [PASS] 17. 500 GB checkpoint to single OST at 800 MB/s takes 625.0 seconds
  [PASS] 18. 500 GB sharded checkpoint across 24 OSTs (20.83 GB/OST, 7.81 GB/rank) at 500 MB/s/OST reaches 12.0 GB/s (41.67 s / 41.7 s)
  [PASS] 19. Unaligned N-to-1 shared write suffers 4x LDLM extent lock slowdown (3.0 GB/s, 166.67 s / 166.7 s vs 12.0 GB/s, 41.67 s N-to-N)
  [PASS] 20. Dual 400G o2ib0 rails NUMA-aligned + 6 OSTs at 49% report BALANCED and 800.0 Gbps
  [PASS] 21. OSS RAM sizing formula (400+600+1.5*N_threads MB/OST; 2+1*N_OSTs GB/OSS) matches 1030 MB and 8.0 GB
  [PASS] 22. Down LNet rail + OST0 at 98% vs OST1-5 at 60% (38% skew) flags IMBALANCED_MIGRATE_REQUIRED on OST 0
  [PASS] 23. SuperPOD HPS 4-SU read/write targets scale linearly (4x single-SU: 360/180 GB/s Std, 1120/560 GB/s Enh)
  [PASS] 24. 4-SU Enhanced HPS (560 GB/s across 112 NVMe OSTs at 5 GB/s) writes a 5.6 TB checkpoint in 10.0 s
  [PASS] 25. Increasing dataset stripe_count from 2 to 8 at 800 MB/s per OST scales file read bandwidth from 1.6 to 6.4 GB/s

Summary: 25 passed, 0 failed
```

---

## Common first mistakes

Setting `lfs setstripe -c -1` on a directory containing millions of small files is a frequent mistake. Wide-striping files under one megabyte does not parallelize sub-stripe reads. Instead, it multiplies OST object allocations, lock traffic, and size-calculation RPCs across every OST in the cluster. Always use Progressive File Layout with Data-on-MDT on mixed directories, or repackage small files into WebDataset shards.

Expecting `lfs setstripe` on a directory to re-stripe existing files is another common trap. Changing a directory's default layout only affects newly created files. Existing single-stripe files keep their original layout until an operator explicitly copies or migrates them with `lfs migrate -c 16`.

Administrators also frequently confuse DNE Phase 1 using `lfs mkdir -i` with DNE Phase 2 using `lfs setdirstripe -c`. Adding four MDS servers and enabling DNE Phase 1 does nothing if a job dumps five million training images into one flat directory. Phase 1 assigns that entire directory to one MDT. Use DNE Phase 2 for huge flat directories and shard the dataset into tar archives.

Hardcoding the starting stripe offset with `-i 0` in training or checkpoint scripts causes severe capacity skew. Passing `-i 0` forces every single-stripe file to start on OST 0. That drives OST 0 to ninety-eight percent full while other OSTs sit at sixty percent, triggering premature out-of-space stalls. Always let the MDS select the starting target automatically with the default `-i -1`. Finally, never mount compute clients with `-o localflock` or default `noflock`. Always mount with `-o flock,lazystatfs,noatime` so multi-node file locks stay coherent and `ENOSYS` errors never crash PyTorch coordination.

---

## Exercises

1. **PFL + DoM Object & Byte Distribution (`evaluate_pfl_dom_file`):**
   A directory on a 24-OST Lustre cluster uses the composite layout `lfs setstripe -E 1M -L mdt -E 64M -c 1 -S 1M -E 4G -c 4 -S 4M -E -1 -c -1 -S 4M`. Evaluate three files: a 260 KiB JSON manifest, a 512 MiB WebDataset shard, and a 10 GiB checkpoint. Calculate how many bytes reside on the MDT via DoM, how many bytes reside on OSTs, and how many distinct OSTs hold data for each file.
2. **Metadata Bottleneck Diagnosis and Dataset Sharding (`evaluate_lctl_metadata_stats` & `model_dne_metadata_scaling`):**
   During epoch start across 128 GPU nodes, `lctl get_param llite.lustre-1a5c.stats` over a 60-second window records the saturated metrics shown below. First, compute the per-second open rate, `getattr` rate, and average open latency in milliseconds, and compare them against healthy thresholds. Second, if the dataset is repackaged as shown below, calculate the reduction factor in `open` calls per epoch and the total open time across 4 MDTs.
3. **DNE Phase 1 vs Phase 2 Single-Directory Trap (`model_dne_metadata_scaling`):**
   A Lustre cluster has 4 MDTs, each rated for 50,000 metadata operations per second. A vision job opens 200,000 files stored inside a single directory `/lustre/imagenet/train`. Calculate the active MDT count, aggregate metadata IOPS capacity, and total open time under DNE Phase 1 with `lfs mkdir -i 0` versus DNE Phase 2 with `lfs setdirstripe -c 4`.
4. **Client RPC Bandwidth-Delay Product (`calculate_client_rpc_bdp`):**
   A GPU client with a 400 Gbps RDMA NIC reads a file striped across 8 NVMe OSTs over a congested path where storage RTT is 4,000 microseconds. First, calculate the per-OST RPC size, in-flight bytes, per-OST BDP limit, and aggregate 8-OST client bandwidth with untuned defaults. Second, recalculate after applying the tuned `max_rpcs_in_flight` and `max_pages_per_rpc` values from the parameter block below.
5. **Checkpoint Striping & LDLM Lock Contention (`model_checkpoint_write_strategy`):**
   A 64-rank training job writes a 500 GB checkpoint. Compare the effective write bandwidth and total checkpoint stall time across three configurations: a single-OST write, an unaligned N-to-1 shared-file write across 12 NVMe OSTs, and a sharded N-to-N write across 24 OSTs. Also compute the write time for a 5.6 TB checkpoint on a 4-SU SuperPOD Enhanced tier.
6. **OST Skew Remediation, OSS RAM Sizing, and `gdsio` Verification (`audit_lnet_multirail_and_osts` & `compare_gdsio_paths`):**
   An OSS serves 6 OSTs connected to 120 Lustre clients. Using the book's sizing formulas, calculate the baseline per-OST RAM and recommended OSS total RAM. Next, calculate the fill skew when OST 0 is at 98% and OST 1 through OST 5 are at 60%, and write the `lfs find` and `lfs migrate` pipeline to rebalance OST 0. Finally, compute the percentage throughput gain and latency reduction between `gdsio` modes `-x 2` and `-x 0`.

```text
Exercise Input Parameters Reference:
- Exercise 2 inputs:
  * 60-second window on 128 GPU nodes: 950,000 open samples (1,200 us min, 65,400 us max, 45,200 us avg); 1,900,000 getattr samples (78,900 us avg)
  * Healthy thresholds: < 50,000 ops/sec aggregate, < 5.0 ms average open latency
  * Dataset repackaging: 10,000,000 files at 260 KB each (2.6 TB total) -> 100 shards of 26 GB each (100,000 files/shard) across 4 MDTs (50,000 ops/sec per MDT = 200,000 ops/sec)
- Exercise 4 inputs:
  * Client NIC: 400 Gbps (50,000 MB/s) | 8 NVMe OSTs at 6,000 MB/s (6.0 GB/s) each | Storage RTT = 4,000 us (4.0 ms) | Page_Size = 4 KiB
  * Untuned defaults: max_rpcs_in_flight = 8, max_pages_per_rpc = 256
  * Tuned settings:   max_rpcs_in_flight = 64, max_pages_per_rpc = 1024 (4 MiB RPCs)
- Exercise 5 inputs:
  * 64 ranks writing 500 GB (500,000 MB):
    (a) stripe_count = 1 at 800 MB/s per OST
    (b) Unaligned N-to-1 across 12 OSTs at 1,000 MB/s per OST with 25% LDLM lock efficiency
    (c) Sharded N-to-N (PyTorch DCP) across 24 OSTs at 500 MB/s per OST (100% efficiency), plus 5,600 GB (5.6 TB) across 112 NVMe OSTs at 5,000 MB/s (560 GB/s)
- Exercise 6 inputs:
  * OSS with 6 OSTs and 120 clients (N_threads = 120 / 6 = 20): per-OST RAM = 400 MB + 600 MB + 1.5 MB * N_threads; total OSS RAM = 2 GB + 1 GB * N_OSTs
  * OST fill skew: OST0 at 98% vs OST1-OST5 at 60%
  * gdsio benchmark: -x 2 achieves 8.0 GB/s at 1.25 ms latency; -x 0 achieves 9.6 GB/s at 1.00 ms latency
```

---

## Interview angles

1. **Fixing a 10-million-file metadata storm without new MDS hardware:**
   Suppose you manage a twenty-four-OST Lustre cluster where a training job opens ten million small files per epoch. Metadata is saturated at forty-five milliseconds average open latency. Do not try to micro-tune a single MDS to handle ten million random opens. Instead, attack the operation count by repackaging the dataset into one hundred contiguous WebDataset tar, TFRecord, or Parquet shards striped across sixteen OSTs with `lfs setstripe -c 16 -S 2M`. Dataloader workers now issue one hundred `open` calls per epoch instead of ten million. That shift converts random metadata IOPS into parallel sequential OST streaming. Also package the Python and Conda environment into a node-local SquashFS image using Enroot and Pyxis.
2. **Diagnosing a 15-minute stall on a 500 GB checkpoint write:**
   When a five-hundred-gigabyte checkpoint write takes fifteen minutes on a twelve-OST or twenty-four-OST cluster at seventy percent mean capacity, inspect three layers in order. First, check `lfs getstripe` on the checkpoint file. If the stripe count is one, all five hundred gigabytes serialize onto one OST, so set `lfs setstripe -c -1 -S 4M` on the checkpoint directory. Second, check `lfs df -h` for OST fill skew. If OST 0 sits at ninety-eight percent while peers sit at sixty percent, rebalance with `lfs migrate` and ensure `-i -1` is used. Third, eliminate application serialization or unaligned N-to-1 LDLM extent lock ping-pong by switching to N-to-N sharded checkpointing with PyTorch DCP after staging tensors to pinned host RAM or local NVMe.
3. **Why global `lfs setstripe -c -1` is dangerous and how PFL + DoM solve it:**
   Setting `-c -1` globally across twenty-four OSTs forces every tiny config or small image file to allocate twenty-four OST object references. Yet payloads under one megabyte still land entirely on the first OST slot. That mismatch explodes MDS and OST inode consumption and multiplies `getattr` and `unlink` RPC fanout. A Progressive File Layout with Data-on-MDT keeps files under one megabyte entirely on the NVMe MDT with zero OST objects. It gives medium files one OST, stripes half-gigabyte shards across four OSTs, and automatically fans multi-gigabyte checkpoints across all twenty-four OSTs.

---

## Checkpoint questions (20)

<details>
<summary>**1. In an NVIDIA DGX SuperPOD, how are High-Performance Storage and User Storage separated, and what are the 1-SU and 4-SU HPS bandwidth targets?**</summary>

High-Performance Storage such as Lustre runs over a dedicated 400 Gbps RoCEv2 or InfiniBand storage fabric port per compute tray. This port is physically and logically separated from the 200 Gbps bonded in-band management network. That management network carries User Storage over NFSv3 for `/home`, logs, and Base Command Manager high-availability state.

```text
SuperPOD GB300 High-Performance Storage (HPS) Bandwidth Targets:
- Standard HPS: 90 GB/s read / 45 GB/s write (1 SU); 360 GB/s read / 180 GB/s write (4 SUs)
- Enhanced HPS: 280 GB/s read / 140 GB/s write (1 SU); 1,120 GB/s read / 560 GB/s write (4 SUs)
```
</details>

<details>
<summary>**2. Why does increasing `stripe_count` from 1 to 24 fail to speed up metadata-bound workloads?**</summary>

Striping only distributes file data chunks across OSTs. Every namespace operation such as `open`, `close`, `stat`, `getattr`, `readdir`, and `unlink` still traverses the MDS and MDT. Worse, wide striping on small files forces the MDS and client to manage up to 24 child OST object references per file. That extra state increases `getattr` and `unlink` overhead.
</details>

<details>
<summary>**3. How does Lustre's `raid0` layout map byte offset `b` to an OST slot, and why is "a 2-stripe 1 GiB file is split into two contiguous 500 MB halves" wrong?**</summary>

Lustre slices a file into fixed `stripe_size` chunks of size $S$ and assigns chunk `floor(b / S)` round-robin to slot `floor(b / S) mod C`. For a 1 GiB file with a 1 MiB stripe size and a stripe count of 2, even-numbered 1 MiB chunks go to OST slot 0 and odd-numbered 1 MiB chunks go to OST slot 1. Each OST holds 512 MiB interleaved every 1 MiB.
</details>

<details>
<summary>**4. If a file is striped across 8 OSTs with a 1 MiB stripe size, how many OSTs are used by a 512 KiB read at offset 0 versus a 16 MiB sequential read with a 2 MiB stripe size?**</summary>

The 512 KiB read at offset 0 lies entirely within chunk 0. It touches only 1 OST on slot 0 and gains zero stripe parallelism. The 16 MiB sequential read with a 2 MiB stripe size spans 8 consecutive 2 MiB chunks, hitting all 8 OSTs in parallel at 2 MiB per OST.
</details>

<details>
<summary>**5. What is a Progressive File Layout, and how does it handle files of different sizes in the same directory?**</summary>

Progressive File Layout divides a file into sequential offset ranges defined with `-E`, each with its own `stripe_count` and `stripe_size`. Components beyond a file's current end-of-file are not instantiated until the file grows past the boundary. Small files allocate a single stripe while multi-gigabyte shards or checkpoints automatically expand across 4, 16, or all OSTs with `-c -1`.
</details>

<details>
<summary>**6. What is Data-on-MDT, and what happens when a 260 KiB file is written to a directory with `lfs setstripe -E 1M -L mdt -E 64M -c 1 -S 1M ...`?**</summary>

Data-on-MDT, configured with `-L mdt`, stores the first component of a file up to 1 MiB directly on the NVMe MDT alongside the inode. A 260 KiB file fits completely inside the first 1 MiB range. As a result, 100% of its payload stays on the MDT and 0 OST objects are allocated. This allows `open` and `read` calls to avoid OST RPCs completely.
</details>

<details>
<summary>**7. How do you distinguish healthy vs saturated metadata in `lctl get_param llite.*.stats`?**</summary>

Inspect the `open`, `close`, and `getattr` sample counts and latencies in microseconds. Healthy metadata stays under 50,000 aggregate operations per second across the MDS with average `open` latency below 5 ms. Saturated metadata exhibits high sample rates and average `open` latency spiking to 45.2 ms or 120 ms during epoch-start storms.

```text
llite.*.stats Comparison (1-Minute Window):
- Healthy: 150,000 opens/min (2,500/s), 2,100 us (2.1 ms) avg, 5,400 us (5.4 ms) max
- Saturated: 950,000 opens/min (15,833/s) + 1,900,000 getattr/min, 45,200 us (45.2 ms) avg, 65,400 us (65.4 ms) max (120 ms burst)
```
</details>

<details>
<summary>**8. What is the difference between DNE Phase 1 (`lfs mkdir -i`) and DNE Phase 2 (`lfs setdirstripe -c`) when a dataset has 200,000 files in a single directory across 4 MDTs?**</summary>

DNE Phase 1 pins a whole directory subtree to a single MDT index with `-i`. If all 200,000 files live in 1 directory, only 1 MDT serves them at 50,000 ops/sec in 4.0 seconds while the other 3 MDTs sit idle. DNE Phase 2 uses `lfs setdirstripe -c 4` or `lfs mkdir -c 4` to hash filenames within that single directory across all 4 MDTs, achieving 200,000 ops/sec in 1.0 second.
</details>

<details>
<summary>**9. Why is repackaging 10 million 260 KB files into 100 WebDataset shards superior to tuning MDS threads alone?**</summary>

Tuning MDS threads or adding MDTs improves metadata IOPS by a factor of 2 to 4. Repackaging 10,000,000 files totaling 2.6 TB into 100 shards of 26 GB each reduces `open` calls per epoch from 10,000,000 to 100. That 100,000x reduction eliminates the metadata bottleneck completely and turns small random reads into sequential OST streaming.
</details>

<details>
<summary>**10. Why should Python virtual environments never be executed directly from `/lustre` on a 1,000-GPU job launch?**</summary>

When 1,000 Python processes run `import torch, transformers`, Python searches every directory on `sys.path`. That walk issues thousands of `stat` and `open` calls per rank, hitting the MDS with millions of simultaneous metadata RPCs. Package environments inside read-only SquashFS container images with Enroot, Pyxis, or Apptainer staged on node-local NVMe.
</details>

<details>
<summary>**11. What LNet Lustre Network Drivers and TCP port are used for IP vs RDMA fabrics, and why does `<protocol><index>` numbering matter?**</summary>

The `ksocklnd` driver (`@tcp0`) runs over TCP/IP using TCP port 988, while `ko2iblnd` (`@o2ib0`) runs native RDMA Verbs over InfiniBand or RoCEv2. Each protocol and index combination such as `@o2ib0` versus `@o2ib1` is an isolated LNet subnet. Nodes on `@o2ib0` cannot communicate directly with `@o2ib1` without an LNet router.
</details>

<details>
<summary>**12. How does LNet Multi-Rail (`lnetctl`) prevent a single GPU training node from running 5x slower than its peers?**</summary>

LNet Multi-Rail binds multiple local 400 Gbps RDMA NICs across NUMA sockets and steers I/O to the rail on the same NUMA node and PCIe switch as the requesting CPU or GPU. This local steering avoids cross-socket interconnect hairpins. It also tracks per-NID health scores from 1000 down to 0 to fail over automatically if one rail drops packets.
</details>

<details>
<summary>**13. State the Lustre client OSC Bandwidth-Delay Product formula and compute the single-OST BDP limit for default vs tuned settings at 500 us vs 4,000 us RTT.**</summary>

```text
BDP_OST = (max_rpcs_in_flight * max_pages_per_rpc * 4096 bytes) / RTT
- Untuned (8 RPCs, 256 pages = 1 MiB/RPC = 8 MiB in flight):
  * At 500 us RTT: 8 MiB / 500 us = 16,777.22 MB/s
  * At 4,000 us RTT: 8 MiB / 4,000 us = 2,097.15 MB/s (starves a 6,000 MB/s NVMe OST)
- Tuned (64 RPCs, 1024 pages = 4 MiB/RPC = 256 MiB in flight):
  * At 4,000 us RTT: 256 MiB / 4,000 us = 67,108.86 MB/s
```
</details>

<details>
<summary>**14. How does GPUDirect Storage interact with Lustre, why can't FUSE filesystems use GDS, and what do `gdsio` flags `-x 2` vs `-x 0` measure?**</summary>

GPUDirect Storage requires a kernel-level filesystem client (`lustre.ko` with `nvidia-fs.ko`) using `O_DIRECT` page-cache bypass. That allows the RDMA NIC to DMA OST data directly into GPU BAR1 or NVLink-C2C memory. FUSE filesystems bounce buffers through userspace and lack kernel `O_DIRECT` DMA hooks. In `gdsio`, `-x 2` benchmarks the CPU-mediated pinned host memory path at 8.0 GB/s and 1.25 ms latency. Flag `-x 0` benchmarks the direct GDS path at 9.6 GB/s and 1.00 ms latency, delivering +20% throughput and -20% latency.
</details>

<details>
<summary>**15. Why must production AI Lustre clients be mounted with `-o flock,lazystatfs,noatime`?**</summary>

The `flock` option enables cluster-wide coherent POSIX `flock()` locking. Without it, `flock()` returns `ENOSYS` and crashes PyTorch `FileStore` and Hugging Face dataset locks, whereas `localflock` only locks locally on one node. The `lazystatfs` option prevents `df`, `statfs()`, and Kubernetes kubelet probes from hanging when a single OST is slow or offline. Finally, `noatime` eliminates redundant MDT access-time writes on training reads.
</details>

<details>
<summary>**16. Why do unaligned N-to-1 concurrent writes to a wide-striped Lustre checkpoint file perform poorly, and how does N-to-N sharded checkpointing solve it?**</summary>

When multiple ranks write unaligned byte ranges inside the same 4 MiB stripe extent of a single shared file, the OST's Lustre Distributed Lock Manager must repeatedly revoke and re-grant Protected Write extent locks between clients. This lock ping-pong cuts throughput by 4x from 12.0 GB/s down to 3.0 GB/s. With N-to-N sharded checkpoints in PyTorch DCP, each rank writes its own separate shard file with a stripe count of 1 to 4 and `-i -1`. That design guarantees zero cross-rank lock contention while spreading files across all OSTs.
</details>

<details>
<summary>**17. What are the two OSS RAM sizing formulas from *Supercomputers for Linux SysAdmins*, and what do they yield for an OSS with 6 OSTs serving 120 clients?**</summary>

```text
OSS RAM Sizing Formulas (6 OSTs, 120 clients -> N_threads = 120 / 6 = 20 threads/OST):
1. Per-OST baseline RAM: 400 MB (logging) + 600 MB (metadata caching) + 1.5 MB * N_threads = 1,000 + 1.5 * 20 = 1,030 MB per OST
2. Recommended total OSS RAM: 2 GB + 1 GB per OST = 2 + 6 = 8.0 GB minimum
```
</details>

<details>
<summary>**18. What does `lfs df -h` show when a cluster has OST fill skew, why is a single 98%-full OST dangerous, and how do you fix it online?**</summary>

Running `lfs df -h` shows per-MDT and per-OST byte usage, where healthy clusters keep all OSTs within 5% of each other around the 49% mean. If OST 0 reaches 98% while OST 1 through OST 5 sit at 60%, any file striped across OST 0 blocks or fails with `ENOSPC`. Fix it online by finding files on OST 0 and migrating them across balanced OSTs with `lfs find /lustre/dataset --ost <OST0_UUID> -type f -print0 | lfs migrate -0 -c 6`.
</details>

<details>
<summary>**19. What is the exact four-step sequence to deactivate and retire a failing OST without losing data?**</summary>

First, run `lctl dl` on the client or MGS to identify the numeric device index `N` of the failing OST. Second, run `lctl --device N deactivate` so the MDS stops allocating new objects on that OST. Third, locate existing files on the retiring OST with `lfs find --ost` and evacuate their extents to healthy OSTs using `lfs_migrate` or `lfs migrate`. Fourth, if offline repair is required, unmount clients first, then OSTs, then MDTs and the MGS. Then mount the target locally as `ldiskfs` and run Lustre-patched `e2fsck`.
</details>

<details>
<summary>**20. You run `lfs setstripe -c 16 /lustre/checkpoints` after noticing slow `stripe_count = 1` checkpoints, but re-reading yesterday's 500 GB checkpoint is still capped at 800 MB/s. Why, and how do you fix it?**</summary>

Running `lfs setstripe` on a directory only sets the default layout template for newly created files. Existing files retain the LOV layout (`stripe_count = 1`) assigned when they were created. To re-stripe yesterday's checkpoint across 16 OSTs, run `lfs migrate -c 16 -S 4M /lustre/checkpoints/ckpt-yesterday.pt`.
</details>

---

## Sources and review notes

The primary sources migrated and cited in this chapter are cataloged in the reference block below.

```text
Primary Sources (Read in Full and Migrated):
1. Migrated from nvidia-devops:
   - nvidia-zero-to-hero/volume-15/chapter-05-lustre-for-ai-and-hpc.md (Lustre for AI and HPC: metadata vs data path split, ~50K-100K ops/sec per MDS, 100-800 MB/s per OST, 140 GB and 500 GB checkpoint striping across 20 and 24 OSTs [625 s at 800 MB/s vs 12 GB/s at 24 * 500 MB/s], lctl get_param llite.lustre-1a5c.stats healthy [150,000 opens, 2,100 us avg, 5,400 us max] vs saturated [950,000 opens, 45,200 us avg, 65,400 us max; 1,900,000 getattr, 78,900 us avg, 102,000 us max], lfs df -h 49% balanced vs 98%/60% skewed, lfs getstripe/setstripe -c 2/8/16/-1 and -S 2M, DNE 4-MDS 200K ops/sec scaling, 5M files -> 50K shards [100x] and 10M files [260 KB, 2.6 TB] -> 100 shards of 26 GB [1,500x-100,000x], and the 5-row troubleshooting table).
2. Book & Reference Architecture Corpus Sources:
   - AI Systems Performance Engineering (ai-systems-performance-engineering, Chapter 5: GPU-Based Storage I/O Optimizations — cuFile / GPUDirect Storage with parallel filesystems, O_DIRECT requirement and why FUSE filesystems cannot use GDS, gdsio benchmark -x 2 CPU path [8.0 GB/s, 1.25 ms latency] vs -x 0 direct GDS path [9.6 GB/s, 1.00 ms latency, +20% throughput and -20% latency in Table 5-1], lfs setstripe across 4 or 8 OSTs at 500 MB/s = 2 GB/s, lmt monitoring, and nsys --trace=gds).
   - Supercomputers for Linux SysAdmins (supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to, Chapter 9: Network File Systems and Chapter 28: One-Two-Three Instructions — MGS/MDS/MDT/OSS/OST, client MDC/OSC/LOV/MGC, LNet o2ib/tcp NIDs and TCP port 988, /etc/modprobe.d/lustre.conf, lnetctl net show, OSS RAM sizing formulas 400 MB + 600 MB + 1.5 MB * N_threads and 2 GB + 1 GB per OST, RAID-10 for MDTs vs RAID-6 for OSTs, PFL composite layouts, lctl dl + lctl --device N deactivate + lfs_migrate OST retirement, and NFSv3 /home vs Lustre scratch separation).
   - NVIDIA DGX SuperPOD Reference Architectures (superpod-gb300-ra and superpod-b200-dc — DGX GB300 NVL72 8 racks / 576 GPUs / 1.2 MW per SU up to 16 SUs / 9,216 GPUs, DGX B200 32 nodes / 458 kW per SU and 127 nodes per 4 SUs, dedicated 400 Gbps RoCEv2 High-Performance Storage [HPS] port vs 200 Gbps in-band management network on BlueField-3 BF3240 + SN5600D switches, 4x 3.84 TB E1.S local NVMe RAID0, 900 GB/s NVLink-C2C, and Table 5 HPS throughput targets: Standard 90 / 45 GB/s [1 SU] and 360 / 180 GB/s [4 SU]; Enhanced 280 / 140 GB/s [1 SU] and 1,120 / 560 GB/s [4 SU]).
   - Cross-referenced with Chapter 6.19 (Lustre architecture and operation) and Lustre manual pages (lfs-setstripe(1), lfs-getstripe(1), lfs-migrate(1), lctl(8), mount.lustre(8) from lustre-release commit 6325870).
```

### Inferences and Unverified Claims Note

All Lustre, LNet, and GDS CLI commands including `lfs`, `lctl`, `lnetctl` (`UDSP` rules, `tx_queued` on `ConnectX-7` and `ConnectX-8` NICs), `mkfs.lustre`, `mount -t lustre` (avoiding `site-packages` storms, writing `rank_0001.distcp` / `0001` shards from GPU `HBM`, `0.5` ms / `70` / `75` / `2304` GPU examples), `gdsio`, and `fio` are illustrative production patterns from the cited sources. They have not been executed on a live multi-node Lustre kernel cluster in this build environment, so they are marked `untested here`. The Python models in `code/part13/lustre_for_ai.py` and `code/part13/lustre_for_ai_lab.py` deterministically encode the PFL, DoM, RAID 0, DNE, OSC BDP, `gdsio`, checkpoint, and LNet or OSS sizing formulas. Those scripts were verified locally with all twenty-five checks passing.

