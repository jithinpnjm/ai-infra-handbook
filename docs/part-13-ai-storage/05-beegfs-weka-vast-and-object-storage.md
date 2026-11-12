---
id: "c13-05"
title: "13.5 BeeGFS, Weka, VAST and object storage"
sidebar_label: "13.5 BeeGFS, Weka, VAST and object storage"
sidebar_position: 5
description: "Architecture, stripe math, and operational tuning for BeeGFS, WekaFS, VAST Data DASE, DeepSeek 3FS, and S3 object storage dataset pipelines in GPU clusters."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 13.5 BeeGFS, Weka, VAST and object storage

| Field | Value |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | GCP / GKE + Local Python Verification Lab (`code/part13/beegfs_weka_vast_object_lab.py`) |
| Part | Part 13: AI storage |
| Coverage file | `planning/coverage/chapters/13-05.md` |
| Claim & number ledger | `planning/ledgers/13-05.md` |

## Why this matters for AI infrastructure

Picture a training run that should take a week and takes two. The GPU dashboard shows the cards busy, yet progress is slow. Often the cause is not the compute. The storage layer is not delivering batches or saving checkpoints fast enough, so the GPUs spend their time waiting.

Every minute spent waiting on storage is a minute of wasted cluster power and lost training progress. When the storage fabric falls behind, expensive GPU nodes sit idle waiting for batches. They also block on synchronous weight dumps, which means the training loop stops until each dump finishes.

Feeding modern accelerators takes massive sustained bandwidth, which is the amount of data that can move every second. Do the arithmetic for one GPU. If it needs 200 MB/s of training data to keep its Tensor Cores busy, an eight-GPU server needs 1.6 GB/s of continuous read throughput. Multiply again for a rack. An NVIDIA Grace Blackwell GB200 or GB300 NVL72 rack, which forms a single NVLink domain, needs 14.4 GB/s of continuous ingestion.

Stalls matter just as much as raw speed. If storage stalls consume a third of iteration time, cutting that wait down to 5 percent lowers the stall fraction sixfold. The GPUs recover 25 percentage points of active compute time from that single change.

The envelope below puts these figures side by side. Notice how the rack-level number grows with the number of GPUs in the rack, and how the same storage fix changes the stall numbers.

```text
Cluster Storage Bandwidth & Stall Reduction Envelope:
  - Single 8-GPU training server (8 x 200 MB/s):               1.6 GB/s sustained read
  - Single GB200 / GB300 NVL72 rack (72 x 200 MB/s):          14.4 GB/s (14-20 GB/s envelope)
  - Cutting GPU I/O wait from 30% down to 5%:                  6.0x stall reduction (+25 pct pts active compute)
```

Lustre dominates classic national-laboratory supercomputers. Commercial and enterprise GPU clusters, however, often pick from four complementary storage architectures. Each one sits at a different point between operational simplicity, metadata scalability and cost per gigabyte.

The first option is BeeGFS, an open-ecosystem parallel filesystem. It splits its work into management, metadata, storage targets and kernel clients, and each piece runs as a standard Linux service. That makes it far simpler to install and run than Lustre. The trade-off is that you still have to configure directory stripe patterns yourself. Repackaging small files keeps the metadata servers from saturating above 100 GPUs.

The second option is WekaFS, a software-defined, NVMe-first parallel filesystem. It spreads both data and metadata in 4 KB chunks across every storage node. Because no single node owns the metadata, there is no dedicated metadata server that can become a bottleneck. Weka pins dedicated polling CPU cores on GPU hosts, which gives low-latency POSIX access over RoCEv2 or InfiniBand with GPUDirect Storage. It also moves cold extents, the data that is rarely read, to S3 object storage on its own, while keeping one namespace.

The third option is VAST Data DASE, along with AI-native RDMA filesystems such as DeepSeek 3FS. Both designs rethink how compute nodes talk to flash. VAST separates stateless protocol containers from NVMe-oF storage enclosures. Those enclosures pair Storage Class Memory write buffers with wide-striped QLC flash. DeepSeek 3FS goes further for random-read AI workloads. It bypasses the Linux page cache completely, using `O_DIRECT`, `io_uring` and RDMA. In DeepSeek's published peak benchmark, 3FS reached about 6.6 TiB/s of aggregate read throughput across 180 storage nodes.

The fourth option is object storage, such as S3, GCS, Azure Blob and MinIO. It gives you durable, exabyte-scale data lakes that act as the source of truth, reached over HTTP and TLS. The catch is latency. At 150 ms per request, two million small files add up to more than 83 hours of serial API wait. Feeding GPUs from object storage therefore needs more machinery: versioned JSON manifests, prefix sharding, parallel download worker pools and local NVMe staging caches.

Start by working out how much bandwidth your GPUs actually need, because that number narrows the four options quickly.

## Prerequisites and outcomes

### Prerequisites
- You should already know the AI storage workload taxonomy and the local NVMe block queues from the earlier chapters in Part 13.
- Parallel filesystem ideas from the previous chapter, such as separated metadata and data paths and target striping, should feel familiar.
- You need working knowledge of NVMe-oF over TCP on port `8009`, or over RDMA on UDP ports `4420` and `4791`, plus GPUDirect Storage (`cuFile` and `nvidia-fs`).

### Outcomes
After completing this chapter, you will be able to:
1. Lay out and troubleshoot a BeeGFS cluster across its four services. You will work out how round-robin stripe chunks are placed, spot target fill skew, and stop 256-GPU metadata saturation with MDS scale-out and WebDataset sharding.
2. Compare BeeGFS and Lustre with WekaFS and VAST Data DASE. The comparison covers metadata layout, erasure coding, client core pinning and hybrid S3 namespace tiering.
3. Explain how DeepSeek 3FS uses `O_DIRECT`, `io_uring` and RDMA to reach about 6.6 TiB/s across 180 storage nodes.
4. Build and instrument a production S3 dataset staging pipeline. It removes bucket listings by using JSON manifests, scales request rates through prefix sharding, and tracks the per-epoch local NVMe cache hit rate.

---

## 1. The AI Storage Taxonomy: Block, File, Parallel File, and Object

Picture one storage system asked to do every job. It ingests raw data, curates it with NeMo Curator, serves multi-node training reads, absorbs synchronous checkpoint dumps and answers RAG vector lookups. Each of those jobs asks for something different in latency, concurrency and cost. A system built for one of them usually struggles with the rest.

A single standard NFS server cannot feed a 100-GPU cluster. Even when you tune it with 1 MiB transfer sizes, every metadata lookup and data stream still funnels through one server's network interfaces and CPU queues. Parallel filesystems break that single-node ceiling. They stripe data and metadata across dozens or hundreds of independent storage servers at the same time.

The table compares the three families side by side, so you can see which one fits each job. Object storage is the cheapest per gigabyte. Block volumes are the most expensive per gigabyte, but they deliver high per-volume IOPS and latency.

| Feature | Object Storage (`S3` / `GCS` / MinIO) | Block Storage (`NVMe-oF` / SAN) | Shared / Parallel File Storage (`BeeGFS` / `WekaFS` / `VAST` / `Lustre` / `GPFS`) |
|---|---|---|---|
| **Data organization** | Immutable objects (`key -> blob + metadata`) in flat buckets | Fixed-size logical blocks (`4 KB` LBAs) inside `NSID` volumes | Hierarchical POSIX files and directories with inode attributes |
| **Access method** | REST `HTTP/TLS` API (`GET`, `PUT`, byte-range `GET`) | Block-level NVMe queues (`SQE`/`CQE` capsules over PCIe or fabric) | POSIX syscalls (`open`, `read`, `write`, `stat`, `mmap`, `unlink`) |
| **Network transport** | `TCP/HTTPS` over standard Ethernet/IP | `NVMe-o-TCP` (port `8009`), `NVMe-o-RDMA` (`RoCEv2` UDP `4791` / `IB`), `FC` | `RDMA` (`RoCEv2` / InfiniBand) or `TCP` over Ethernet/IP |
| **OS page cache & `GDS`** | No kernel page cache; staged to local NVMe or memory | Raw block volumes have no shared multi-node page cache; `GDS` via local/remote `O_DIRECT` | Supports shared namespace; `GDS` (`cuFile` + `nvidia-fs`) bypasses host bounce buffers over `RDMA` |
| **Scalability & cost** | Highest capacity scalability (multi-exabyte); lowest `$/GB` | High per-volume IOPS/latency (`~100 ns` PCIe Gen5, `~300 ns` IB, `~800 ns` Eth); highest `$/GB` | Scales to hundreds of `GB/s` or multi-`TB/s` across thousands of GPU clients; moderate-to-high `$/GB` |
| **Primary AI domain** | Data lake source of truth, offline curation, cross-site/cloud checkpoint archival, RAG corpus | Local scratch volumes, database backing stores, hyperconverged or disaggregated `DNode` backing | Active multi-node training datasets, synchronous multi-rank checkpoint writes, shared home/code directories |

Put each workload on the tier that suits it, and you protect both GPU utilization and your storage budget. Object stores hold the durable, multi-petabyte data lake. Parallel filesystems serve active multi-node training and checkpoints over RDMA. Local NVMe block volumes absorb node-local scratch and cache traffic.

Sort each workload into one of these tiers before you choose a product.

---

## 2. BeeGFS for GPU Clusters: Architecture, Striping, and Metadata Tuning

Suppose your team runs between 100 and 500 GPUs and needs multi-node parallel storage bandwidth. You probably do not have an HPC storage team to look after Lustre's patched kernels and complex failover pairs. When a parallel filesystem is hard to operate, small configuration mistakes pile up. A checkpoint directory is left unstriped, or a metadata server quietly overloads.

BeeGFS avoids much of that burden. It runs as ordinary Linux user-space daemons on top of an existing XFS or EXT4 filesystem. It was originally developed at the Fraunhofer Center for High Performance Computing. Its servers pair with a lightweight client kernel module, which supports InfiniBand and RoCEv2 RDMA as well as GPUDirect Storage.

### 2.1 The Four Decoupled BeeGFS Services

The cluster splits into four independent services. One handles cluster management, one holds directory metadata, one stores the bulk chunks, and one mounts the POSIX client on each GPU node.

```mermaid
flowchart TD
    Client["GPU Node: beegfs-client<br/>POSIX + RDMA (connUseRDMA=true)"]
    Mgmt["Control Plane: beegfs-mgmtd<br/>Cluster Node & Target Registry"]
    MDS1["Metadata 1: beegfs-meta<br/>50K-100K ops/s, <5ms latency"]
    MDS2["Metadata 2: beegfs-meta<br/>Directory-level scale-out"]
    OSS1["Storage 1: beegfs-storage<br/>Targets 1001, 1002 (500M-2GB/s)"]
    OSS2["Storage 2: beegfs-storage<br/>Targets 2001, 2002 (±5% fill)"]

    Client -.->|"1. Query node/target map"| Mgmt
    Client -->|"2. stat/open/mkdir + get stripe layout"| MDS1
    MDS1 -.->|"Directory tree distribution"| MDS2
    Client ===|"3. Parallel RDMA read/write chunks"| OSS1
    Client ===|"3. Parallel RDMA read/write chunks"| OSS2
```

Each row of the table below names one service, its job, the envelope that counts as healthy and the command that checks it. Keep the envelope in mind when a checkpoint slows down, because it tells you what normal looks like.

| Service | Daemon / Module | Core Responsibility | Healthy Operational Envelope | Primary CLI check |
|---|---|---|---|---|
| **Management Service** | `beegfs-mgmtd` | Maintains the authoritative registry of all metadata nodes, storage nodes, targets, and client sessions; never sits on the data path | `< 1%` CPU/network load; queried upon mount and topology changes | `beegfs-ctl --listnodes --nodetype=mgmt` |
| **Metadata Service (`MDS`)** | `beegfs-meta` | Stores POSIX inodes, directory hierarchies, permissions, and the per-file stripe pattern (`target IDs` + `chunksize`) | **`50,000–100,000` ops/sec** per MDS; average latency **`< 5 ms`** (e.g., `2.0–2.1 ms` at `5.2K–5.4K` ops/sec) | `beegfs-ctl --serverstats --nodetype=meta` |
| **Storage Service (`OSS`)** | `beegfs-storage` | Manages one or more underlying NVMe RAID/XFS storage targets (`TargetID`) and serves striped file chunks over `RDMA` or `TCP` | **`500 MB/s–2 GB/s`** per storage node; all targets balanced within **`±5%` fill** (`> 10%` spread triggers investigation) | `beegfs-ctl --listtargets --nodetype=storage --spaceinfo` |
| **Client Service** | `beegfs-client` | Kernel module mounted at `/beegfs`; fetches file stripe layout from `MDS` on `open()` and performs direct parallel `RDMA` I/O to storage targets | Sustained `4–5 GB/s` single-client read across `8–12` targets with `connUseRDMA = true` | `beegfs-ctl --clientinfo` and `mount \| grep beegfs` |

Picture a GPU worker opening a file under `/beegfs`. The client module first asks the Metadata Service for that file's stripe recipe. Once it holds the target list, it skips the metadata server entirely. It then streams the chunks in parallel to every assigned storage target over RDMA.

Before you trust a new mount, run the client check and confirm the read rate sits inside the envelope above.

### 2.2 Round-Robin Striping Math and Checkpoint Stall Time

Suppose a checkpoint directory is left on the default stripe width of one or two targets. A multi-hundred-gigabyte checkpoint then has to squeeze through just two targets while the rest of the storage cluster sits idle. Every GPU in the job freezes until that slow write finishes.

BeeGFS cuts each file into fixed-size, contiguous chunks. It then deals those chunks out in round-robin order across the directory's storage targets. You control this with `--chunksize`, which can be 1 MiB through 4 MiB, and `--numtargets`, set to 8 or 12. Set both with `beegfs-ctl --setpattern`, and one large file can draw on the write bandwidth of the whole pool.

```text
BeeGFS Round-Robin Stripe Mapping & 500 GB Checkpoint Stall Math (800 MB/s per target):
  - Formulas for byte offset B, chunksize C, numtargets N across ordered TargetIDs T[0..N-1]:
      chunk_index        = floor(B / C)
      stripe_row         = floor(chunk_index / N)
      target_slot        = chunk_index mod N
      intra_chunk_offset = B mod C
      TargetID           = T[target_slot]
  - Worked example: C = 1 MiB (1,048,576 B), N = 8 targets [1001, 1002, 2001, 2002, 3001, 3002, 4001, 4002]:
      Offset B = 10,486,272 B (10 MiB + 512 B) -> chunk_index = 10, stripe_row = 1, target_slot = 2 (TargetID 2001), intra_chunk_offset = 512 B
  - 500 GB Checkpoint Write Duration by Stripe Width:
      numtargets = 2:   2 x 800 MB/s = 1.6 GB/s theoretical -> 500 GB / 1.6 GB/s = 312.5 s (~312 s / 5.2 min stall)
      numtargets = 8:   8 x 800 MB/s = 6.4 GB/s theoretical -> 500 GB / 6.4 GB/s = 78.125 s (~78 s, 4.0x faster; 100.0 s at 5.0 GB/s / 78.125% efficiency)
      numtargets = 12: 12 x 800 MB/s = 9.6 GB/s theoretical -> 500 GB / 9.6 GB/s = 52.0833 s (52.08 s)
```

Here is the arithmetic for that 500 GB checkpoint. On two targets, the write runs at 2 x 800 MB/s, which is 1.6 GB/s. The checkpoint therefore takes 312.5 seconds, about 5.2 minutes of stall. Move to eight targets and the theoretical rate becomes 6.4 GB/s, so the write drops to 78.125 seconds. That is fourfold faster. At a sustained 5.0 GB/s across eight targets, the same write finishes in 100 seconds. Twelve targets cut the theoretical time further, to 52.08 seconds.

There is a catch. Running `beegfs-ctl --setpattern` on a directory affects only the files created after that point. Existing files keep the stripe width recorded in their inode when they were created. To restripe an existing dataset or checkpoint, you have to rewrite the files or migrate them with `beegfs-ctl --migrate`. Set the stripe pattern on a checkpoint directory before the first checkpoint lands in it.

### 2.3 The 256-GPU Metadata Wall and Target Fill Skew

BeeGFS is much simpler to run than Lustre, but scaling its metadata takes more hands-on work than Lustre's Distributed Namespace. Picture 256 GPUs starting an epoch over ten million raw JPEG files. Each GPU makes 800 metadata calls per second, so demand climbs past 200,000 ops/sec. A single BeeGFS metadata server is rated for 50,000 to 100,000 ops/sec, so it is overwhelmed. Average latency climbs past 30 ms and stalls every GPU.

Scaling out helps. With four or five `beegfs-meta` servers you reach 250,000 ops/sec of raw capacity, because BeeGFS assigns different directories to different metadata nodes. The catch is that all ten million JPEGs in one flat directory still land on the one metadata server that owns that directory's inode. Every lookup hits that server. The lasting fix is repackaging small files into large WebDataset `.tar`, TFRecord or Parquet shards. That step cuts metadata operations a hundredfold, down to 2,048 ops/sec.

A second hazard appears once the cluster is running. Storage targets drift apart in how full they are, and that is target fill skew. Unstriped files or uneven client placement can fill one storage node to 72 percent while another sits at 44 percent. That 28 percent spread breaks the healthy 5 percent balance band. If one target reaches 100 percent full, wide-striped writes fail, even when the rest of the cluster has terabytes free.

The summary below gathers the storm, the scale-out ceiling and the skew example in one place.

```text
BeeGFS 256-GPU Metadata Storm & Storage Target Fill Skew Summary:
  - 256-GPU raw small-file storm (10,000,000 JPEGs, 800 ops/s/GPU): 204,800 ops/sec (200K+ ops/sec; saturates 1 MDS at 50,000 ops/sec, > 30 ms latency)
  - MDS scale-out capacity (5 x 50,000 ops/sec safe ceiling):       250,000 ops/sec (requires multi-directory tree distribution vs Lustre DNE 500,000+ ops/sec)
  - 100x WebDataset / TFRecord sharding reduction:                    2,048 ops/sec (< 5,000 ops/sec; < 5 ms latency on a single MDS)
  - Target fill skew example (Node 101 storage1 vs Node 102 storage2):
      storage1: TargetID 1001 = 4.5 / 10.0 TB (45%), TargetID 1002 = 4.4 / 10.0 TB (44%)
      storage2: TargetID 2001 = 7.2 / 10.0 TB (72%), TargetID 2002 = 7.1 / 10.0 TB (71%)
      Cluster mean = 58.0%, inter-node spread = 28.0% (exceeds +/-5% healthy band and > 10% investigation threshold; migrate 2001, 2002)
```

Notice that sharding cuts the metadata load a hundredfold, while the skew example calls for migrating targets 2001 and 2002. Package the small files first, then check that every target stays inside the 5 percent band.

---

## 3. WekaFS: Distributed Virtual Metadata, Core Pinning, and S3 Tiering

Picture a platform team that supports dozens of research groups. Some run small-file workloads, and others write large checkpoints. If someone has to hand-balance directory metadata trees, or repackage datasets before each experiment, the platform team becomes the bottleneck. What those groups need is one shared POSIX filesystem. It should absorb millions of small-file lookups and multi-gigabyte streaming reads, with no manual stripe tuning.

WekaFS tackles this in the filesystem design itself. It does not send directory lookups to dedicated metadata servers. Instead, it pools every NVMe drive in the storage cluster into one virtual pool, and it spreads both data and metadata across every node.

### 3.1 Fully Distributed Metadata and N+K Erasure Coding

Unlike Lustre and BeeGFS, WekaFS has no dedicated metadata servers at all. It cuts both file data and virtual metadata into 4 KB chunks. A deterministic cryptographic hash then decides which node holds each chunk. Because every node handles metadata operations in parallel, small-file `open`, `stat` and `unlink` IOPS grow linearly as you add storage nodes.

For durability, WekaFS skips hardware RAID cards and 3x replication. Triple replication wastes two-thirds of raw NVMe capacity. Instead, WekaFS stripes data across failure domains with cluster-wide N plus K erasure coding. Here N counts the data chunks and K counts the parity chunks, and together they never exceed the number of storage nodes.

The numbers below work through an 8-node cluster first, then an 18-node cluster. Compare the 3x replication line with the 6+2 line. The erasure code keeps 75 percent of raw capacity usable, and it still gives 2.25 times the usable capacity of 3x replication.

```text
WekaFS Distributed N+K Erasure Coding, Core Pinning & Hybrid S3 Namespace Math:
  - 8-node cluster (8 x 8 x 15.36 TB NVMe SSDs = 983.04 TB raw):
      3x replication:   33.33% efficiency (66.67% overhead) -> 327.68 TB usable
      6+2 erasure code: 6 / (6+2) = 75.0% efficiency        -> 737.28 TB usable Tier 1 NVMe (2.25x usable capacity gain over 3x replication; survives 2 node/drive failures)
      Tier 2 S3 bucket: 2,000 TB cold extent capacity       -> 737.28 + 2,000 = 2,737.28 TB single unified POSIX namespace
  - 18-node cluster with 16+2 erasure stripe:
      16 / (16+2) = 88.89% net NVMe efficiency
  - GPU host client core pinning (ll_core polling mode):
      4 pinned cores on a 128-core GPU server = 3.125% host CPU tax
```

Erasure coding is the trade you make for durability. Before you count terabytes, count how many node or drive failures the layout must survive.

### 3.2 POSIX Client Core Pinning and Unified S3 Tiering

Line-rate RDMA and GPUDirect Storage need steady CPU time, and kernel interrupt jitter would get in the way. So WekaFS runs a dedicated client on each GPU server, and that client pins one to four CPU cores in polling mode.

```mermaid
flowchart LR
    App["PyTorch / TensorFlow App<br/>POSIX open/read/write (.pt, .ckpt)"]
    Client["GPU Host: WekaFS Client<br/>Pinned Polling Cores + GDS"]
    Fabric["Storage Fabric<br/>RoCEv2 (100/200/400G) or IB"]
    Tier1["Tier 1: WekaFS NVMe Nodes 1..8<br/>Distributed 4KB Data + Metadata"]
    Tier2["Tier 2: On-Prem / Cloud S3<br/>HTTPS/TLS Cold Extent Tier"]

    App -->|"POSIX Syscall / cuFileRead"| Client
    Client ===|"WekaFS-o-RDMA + GDS"| Fabric
    Fabric ===|"Hot Chunks (NVMe-o-PCIe)"| Tier1
    Tier1 -.->|"Transparent S3 Tiering (HTTPS)"| Tier2
```

The table maps each architectural layer to what it does for a GPU cluster.

| Architectural Layer | WekaFS Mechanism | Operational Impact for GPU Clusters |
|---|---|---|
| **GPU Host Access (`WekaFS Client`)** | Dedicated user-space/kernel POSIX client running on the GPU server (`100/200/400/800 Gbps` NICs); pins `1` to `4` dedicated CPU cores (`ll_core`) in polling mode | Eliminates OS interrupt latency and sequential NFS state-machine overhead; on a `128`-core host, pinning `4` cores consumes **`3.125%`** CPU to drive line-rate `RDMA` and `GPUDirect Storage` (`GDS`) |
| **Protocol Fallback (`NFS`)** | Optional standard `NFSv3` / `NFSv4.1` gateway access for non-GPU hosts without the native client | Functional for management nodes, but delivers substantially lower IOPS and does not provide the full native `WekaFS-o-RDMA` client pipeline |
| **Unified Hybrid Namespace (`Tier 1 + Tier 2`)** | Hot working sets reside on Tier 1 NVMe flash (`737.28 TB`), while cold datasets and older `.pt`, `.ckpt`, `.npy`, `.h5`, and `.bin` files transparently tier to Tier 2 `S3` object storage (`2,000 TB`+) over `HTTPS/TLS` | Applications see a single `2,737.28 TB` POSIX directory tree; policy engines evict cold data extents from NVMe to `S3` while keeping metadata headers in flash for instant `ls`/`stat` lookups |

Metadata headers stay on Tier 1 flash, even after the data behind them has moved to S3. That is why a directory listing or a `stat` call stays fast across a multi-petabyte namespace. Now suppose a training script opens a cold checkpoint. WekaFS streams those extents back to Tier 1 NVMe without the script doing anything special.

Decide which working sets must stay on Tier 1 flash, since that choice sets how fast the hot data feels.

---

## 4. VAST Data DASE, GPUDirect Storage, and DeepSeek 3FS

Consider what happens on a shared-nothing storage cluster when many clients write at once. Each server owns specific drives and metadata shards, so a write that spans nodes forces those servers to exchange lock and cache-coherency messages across the network. At multi-terabyte-per-second scale, that east-west coordination and the host OS page caches become the main bottlenecks.

Two modern architectures remove those bottlenecks in different ways. VAST Data uses a Disaggregated Shared-Everything architecture, which removes east-west lock traffic between protocol servers. DeepSeek's Fire-Flyer File System bypasses the Linux page cache completely. It uses `O_DIRECT`, `io_uring` and RDMA to saturate NVMe drives on random-read AI workloads.

### 4.1 VAST Data Disaggregated Shared-Everything Architecture

VAST Data separates stateless protocol containers from high-availability NVMe-oF drive enclosures. The two sides talk over an internal RoCEv2 or InfiniBand fabric. Because the protocol servers hold no persistent state, any container can read or write any drive enclosure directly. It never has to coordinate locks with its peers.

```mermaid
flowchart TD
    GPU["GPU Compute Nodes (A100 / H100 / B200)<br/>Multipath NFS-over-RDMA + GDS (cuFile)"]
    CNode1["Stateless CNode 1<br/>NFS / S3 / SMB Protocol Container"]
    CNode2["Stateless CNode N<br/>Zero East-West Lock Traffic"]
    NVMeFabric["Internal NVMe-oF Fabric<br/>RoCEv2 / InfiniBand (Sub-ms)"]
    SCM["DNode Tier A: SCM / Optane / 3D XPoint<br/>Global Metadata + Coalesced Write Buffer"]
    QLC["DNode Tier B: Hyperscale QLC NAND Flash<br/>Wide Erasure Stripe (146+4 = 97.33% Net)"]

    GPU ===|"Multipath NFSv3/v4.1 over RDMA + GDS"| CNode1
    GPU ===|"Multipath NFSv3/v4.1 over RDMA + GDS"| CNode2
    CNode1 ===|"Direct NVMe-oF Read/Write"| NVMeFabric
    CNode2 ===|"Direct NVMe-oF Read/Write"| NVMeFabric
    NVMeFabric ===|"1. All writes + metadata lookups"| SCM
    SCM -.->|"2. Large sequential erase-block stripes"| QLC
```

The table lists the four DASE components. Read each row as a job the component does, and the advantage it gives you.

| DASE Component | Architectural Function | Quantitative Advantage |
|---|---|---|
| **Stateless `CNodes` (Compute Nodes)** | Containerized protocol servers exposing multipath `NFS-over-RDMA` (`nconnect` / multipath), `S3`, and `SMB`; hold **zero persistent state** | Any `CNode` can read or write any `DNode` drive directly over `NVMe-oF`; if a `CNode` fails, active `RDMA` connections fail over to peer `CNodes` without data rebuilds |
| **Internal `NVMe-oF` Fabric** | High-speed `RoCEv2` or InfiniBand switch fabric connecting every `CNode` to every high-availability `DNode` enclosure | Allows independent scaling of protocol CPU (`CNodes`) and flash capacity (`DNodes`) |
| **`DNode` `SCM` (`Optane` / `3D XPoint`) Tier** | Ultra-low-latency, high-endurance non-volatile memory that stores global metadata data structures and absorbs `100%` of incoming random writes | Protects lower-endurance `QLC` flash from random write amplification; `CNodes` coalesce data in `SCM` (`24 TB`+) and destage only full, sequential erase-block stripes |
| **`DNode` `QLC` Flash + Wide Stripes (`146+4`)** | Low-cost, high-density `QLC` NAND flash protected by locally decodable wide erasure codes (e.g., `146` data strips + `4` parity strips across enclosures) | Cuts erasure-coding parity overhead to **`2.67%`** (**`97.33%` net efficiency**; `1,460 TB` usable out of `1,500 TB` raw, or `2,920 TB` at `2.0x` similarity reduction) while surviving `4` concurrent failures |

Think of the SCM tier as a landing zone. Every random write lands there first, so the lower-endurance QLC flash only receives full, sequential stripes.

### 4.2 GPUDirect Storage on these filesystems

Streaming over RDMA at line rate still wastes time if every byte passes through host memory on its way to the GPU. GPUDirect Storage removes that copy by letting the storage or network card write straight into GPU memory. Chapter 13.3 explains the mechanism and shows the `gdsio` measurement that compares the bounce-buffer path with the direct path, so this chapter does not repeat it.

What matters here is which filesystems qualify. GPUDirect Storage needs a kernel client that works with the `nvidia-fs` driver. BeeGFS, WekaFS, VAST over NFS with RDMA, Lustre and GPFS provide one. A user-space FUSE mount does not, and I/O through it falls back to the host-memory path. Run `gdscheck -p` on a client before you assume the direct path is active.

### 4.3 DeepSeek Fire-Flyer File System

Picture a large pretraining job, a multi-modal shuffle or a fleet of workers doing distributed KV cache lookups. Thousands of workers issue random reads that rarely repeat across petabytes of data. On a conventional filesystem backed by the Linux page cache, those reads get almost no cache hits. They also burn CPU cycles on page-table locks and memory allocations.

DeepSeek's open-source Fire-Flyer File System, 3FS, is built for this pattern. It reads with `O_DIRECT`, submits I/O through `io_uring` and moves data over RDMA, so the page cache is out of the path. Four services make up the design: Cluster Manager, Metadata Service, Storage Service and Client. It also offers a FUSE mount for compatibility, but the fast path is the native client.

```text
DeepSeek 3FS peak read benchmark, as published in the project README:
  Storage cluster:   180 nodes, each with two 200 Gbps InfiniBand NICs (50 GB/s) and sixteen 14 TiB NVMe SSDs
  Clients:           more than 500 nodes, each with one 200 Gbps InfiniBand NIC
  Aggregate read:    about 6.6 TiB/s (7.26 TB/s) with background traffic from training jobs
  Network line rate: 180 x 50 GB/s = 9.0 TB/s, so the cluster served about 80 percent of it
  Per storage node:  6.6 x 1024 / 180 = 37.6 GiB/s of the 50 GB/s its NICs can carry
```

The result shows what random-read AI storage can reach when the software stays out of the kernel's way. It is also a custom RDMA and `io_uring` stack, so it suits very large AI factories with a team to run it, not a 100-GPU cluster.

---

## 5. Object Storage and Dataset Staging Pipelines

Many AI teams keep their source-of-truth data in object storage. Systems such as AWS S3, Google Cloud Storage, Azure Blob Storage, and on-premises MinIO or VAST S3 offer nearly unlimited capacity and strong durability. They also cost a fraction of what an all-flash parallel filesystem costs. Object storage is not a POSIX filesystem, though. Pointing a PyTorch DataLoader straight at millions of individual S3 keys is one of the costliest mistakes you can make in AI infrastructure.

### 5.1 The S3 Small-Object Latency Trap

Every S3 `GET` request goes through an HTTP and TLS stack. It authenticates IAM signatures, looks up the object key in a distributed index, and streams the payload over TCP. For a single 100 MB model weight file, 150 ms of control-plane latency plus 100 ms of data transfer finishes in a harmless 250 ms.

Now picture a 500 GB vision dataset stored as two million individual objects of 260 KB each. Every request still pays the 150 ms HTTP and API latency, and that delay is far larger than the transfer time for a 260 KB payload. Issued one after another, the two million requests waste 300,000 seconds, or 83.33 hours. Your GPUs would sit 99 percent idle for more than three days, waiting on HTTP headers.

```text
S3 Object Latency Trap & Parallel Staging Math:
  - Loading 1 x 100 MB model file:             50 ms TCP/TLS + 100 ms S3 API + 100 ms transfer (at 1 GB/s) = 250 ms total
  - Fetching 2,000,000 x 260 KB objects:       2,000,000 x 0.150 s = 300,000 seconds = 83.33 hours (~83 hours serial API wait)
  - Single 1 GB object download:               50 ms TLS + 80 ms API + 6,000 ms transfer = 6.2 s (161.29 MB/s / ~161 MB/s)
  - Parallel 8 x 1 GB object download:         7.5 s elapsed vs 8 x 6.2 = 49.6 s serial (6.61x speedup; 1,066.67 MB/s / ~1,067 MB/s aggregate; 133.33 MB/s / ~133 MB/s per worker)
  - Time-to-First-Batch (500 GB = 50 x 10 GB shards, prefetch 2 shards = 20 GB):
      8 workers at 150 MB/s (1.2 GB/s agg):    20 GB / 1.2 GB/s = 16.67 s (~17 s) + 2 x 5.0 s API (10.0 s) + 2 x 0.1 s TLS (0.2 s) = 26.87 s (~27 s)
      16 workers at 150 MB/s (2.4 GB/s agg):   20 GB / 2.4 GB/s = 8.33 s + 10.2 s API/TLS = 18.53 s
```

The single-object line shows the cost clearly. Fetching one 1 GB object takes 6.2 seconds, which works out to about 161 MB/s. Fetching eight of them in parallel finishes in 7.5 seconds, a 6.61x speedup. That is why the next section uses a worker pool.

### 5.2 Prefix Sharding, Parallel Worker Pools, and Local NVMe Caching

Turning an object store into a high-bandwidth training feeder takes five coordinated pieces. You need versioned JSON manifests, prefix sharding, parallel worker pools, asynchronous prefetching, and local NVMe staging caches. Each piece removes one source of waiting.

```mermaid
flowchart LR
    S3["Object Store (S3 / GCS / MinIO)<br/>100-300ms Latency, 1-10 GB/s Shared"]
    Manifest["Versioned JSON Manifest<br/>Shard URLs + SHA-256 (No LIST Calls)"]
    Workers["Download Worker Pool (8-16 Threads)<br/>8 x 150 MB/s = 1.2 GB/s Aggregate"]
    Cache["Local NVMe Staging Cache<br/>100 GB - 2 TB (Warm Hit Rate >98%)"]
    Loader["PyTorch DataLoader + GPU<br/>pin_memory=True, prefetch_factor=4"]

    S3 -->|"Pinned Version"| Manifest
    Manifest -->|"Deterministic Shard List"| Workers
    S3 ===|"Parallel Range GETs / s5cmd"| Workers
    Workers ===|"Validate SHA-256 & Stage"| Cache
    Cache ===|"Fast Local NVMe Read"| Loader
```

The table walks through the five stages in order. For each stage, it names the bottleneck and the sizing rule that keeps it under control.

| Pipeline Stage | Operational Bottleneck Addressed | Target Metric / Sizing Rule |
|---|---|---|
| **1. Versioned JSON Manifest** | Eliminates repeated `ListObjectsV2` bucket listings, which are slow, paginated at `1,000` keys, and exposed to eventual-consistency and data-drift bugs | Pre-compute `imagenet-manifest.json` (`1,099,511,627,776` bytes = `1 TiB` across `1,073,741,824`-byte `1 GiB` `.tar` shards, `1,281,167` samples) with pinned `sha256` checksums |
| **2. S3 Prefix Sharding** | Standard S3 partitions enforce **`3,500` `PUT/COPY/POST/DELETE`** and **`5,500` `GET/HEAD` requests/sec per prefix**; dumping all shards under one prefix triggers `503 Slow Down` throttling at cluster scale | Shard object keys across 16 hex or hash prefixes (`s3://bucket/00/..` to `s3://bucket/0f/..`) to scale aggregate request ceilings to **`88,000` `GET`/s** and **`56,000` `PUT`/s** |
| **3. Parallel Worker Pool (`8–16` Workers / `s5cmd`)** | Single-stream TCP/TLS downloads cannot saturate `10–100 Gb/s` host NICs (`1 GB` single object takes `6.2 s` = **`161.29 MB/s`**: `50 ms` TLS + `80 ms` API + `6,000 ms` transfer) | Fetching `8 x 1 GB` objects in parallel completes in **`7.5 s`** instead of `8 x 6.2 = 49.6 s` (**`6.61x` speedup**), delivering **`1,066.67 MB/s`** (`~1,067 MB/s`) aggregate (**`133.33 MB/s`** per worker) |
| **4. Time-to-First-Batch Startup** | Prevents GPU starvation at job launch when staging a `500 GB` dataset (`50 x 10 GB` shards) | With `8` workers at `150 MB/s` (`1.2 GB/s` aggregate), prefetching the first `2` shards (`20 GB`) takes `20 / 1.2 = 16.67 s` (`~17 s`) + `2 x 5.0 s` API + `2 x 0.1 s` TLS = **`26.87 s` (`~27 s`)** (`18.53 s` with `16` workers) |
| **5. Local NVMe Cache & LRU Eviction** | Absorbs S3 latency jitter and serves Epochs `2..N` at local NVMe speed (`100 GB–2 TB` scratch) | **Epoch 1 (cold):** `0.1%` hit rate (`45.3 min` wait); **Epoch 2 (warm):** `98.2%` hit rate (`2.1 min` wait, **`21.57x` wait reduction**); **Epoch 3 (`> 85%` fill):** `97.5%` hit rate (`3.5 min` wait as LRU eviction begins) |

Tracking the cache hit rate across epochs exposes sizing bugs early. Suppose the hit rate jumps from 0.1 percent in epoch 1 to 98.2 percent in epoch 2. That confirms the local NVMe cache is warming properly, and it cuts the wait by more than twentyfold. If the hit rate slips to 97.5 percent in the third epoch, cache occupancy has crossed 85 percent. At that point your dataset is larger than the local scratch budget, and LRU eviction has started.

Watch the cache hit rate in every epoch, and resize the scratch budget before the third epoch slows down.

---

## 6. Choosing between them: metadata rate, small files and failure modes

The four options differ most in three places: how fast they answer metadata calls, how they treat small files, and how they fail. Capacity and price matter too, but these three decide whether your GPUs wait. The rates below are the figures quoted earlier in this chapter. Treat them as starting points, because your own result depends on hardware and layout. Measure your metadata rate with `mdtest` before you size anything.

| | BeeGFS | WekaFS | VAST Data | Object storage |
|---|---|---|---|---|
| Metadata rate | About 50,000 to 100,000 operations per second per metadata server; more servers spread directories | Metadata is spread over all nodes in 4 KB pieces, so it grows with node count | Global metadata held in the storage-class-memory tier, reached by stateless protocol servers | Each request is an HTTP call of about 150 ms; per-prefix limits of 5,500 GET and 3,500 PUT per second |
| Small-file behaviour | Needs repackaging into shards above about 100 GPUs; one directory stays on one metadata server | Handles many small files well because no single server owns the namespace | Handles many small files well | Poor: 2,000,000 objects of 260 KB take 83 hours to fetch one by one |
| Typical failure mode | Metadata server saturation at epoch start; a narrow stripe on a checkpoint directory; targets filling unevenly | The client pins dedicated CPU cores, so a host short of cores slows down; the erasure stripe must fit the node count | Depends on the protocol servers and the internal fabric; write-buffer capacity sets burst behaviour | 503 Slow Down above the prefix limit; a cold local cache in epoch 1; a bucket listing run on every rank |
| Fix | Shard files, add metadata servers, set stripe before writing, rebalance targets | Reserve client cores, keep hot data on flash and tier the rest | Size the write buffer to your checkpoint burst | Manifests, prefix sharding, parallel workers and a local NVMe cache |
| Operational load | Low to moderate | Low to moderate | Low | Lowest, but the data pipeline is yours |

How do you pick? If you run 100 to 500 GPUs, can repackage datasets and want a simple open stack, BeeGFS fits. If many teams share the cluster and small-file work is mixed with large checkpoints, WekaFS or VAST remove the metadata tuning. If the source of truth is a data lake, keep it in object storage and stage it, as section 5 shows. Choose one parallel filesystem for the hot tier and one object store for the lake, and do not try to make one system do both jobs.

---

## Commands and configurations that matter

The commands below need a live BeeGFS cluster, GPU hosts or an S3 bucket, and none of them was run for this edit. Treat the sample outputs as illustrations.

### 1. BeeGFS Health, Metadata Rate, and Target Fill Inspection

```bash
# 1. Inspect Metadata Service (MDS) nodes, active sessions, ops/sec, and latency
beegfs-ctl --listnodes --nodetype=meta --details
beegfs-ctl --serverstats --nodetype=meta

# Illustrative healthy output:
# Metadata Service ID 1 (meta1.example.com):
#   Used capacity: 45 GB / 500 GB (9%)
#   Sessions: 24 active
#   Operations: 5,230 ops/sec (healthy, < 50,000 ops/sec ceiling)
#   Latency (avg): 2.1 ms (healthy, < 5.0 ms threshold)
# Metadata Service ID 2 (meta2.example.com):
#   Used capacity: 44 GB / 500 GB (8%)
#   Sessions: 25 active
#   Operations: 5,410 ops/sec (healthy)
#   Latency (avg): 2.0 ms

# 2. Inspect Storage Targets and detect fill-level skew across storage nodes
beegfs-ctl --listtargets --nodetype=storage --spaceinfo
beegfs-ctl --serverstats --nodetype=storage

# Illustrative skewed output requiring rebalancing:
# NodeID: 101 (storage1) Paths:
#  TargetID: 1001 Capacity: 10.0 TB Used: 4.5 TB (45%) Path: /data/target1
#  TargetID: 1002 Capacity: 10.0 TB Used: 4.4 TB (44%) Path: /data/target2
# NodeID: 102 (storage2) Paths:
#  TargetID: 2001 Capacity: 10.0 TB Used: 7.2 TB (72%) Path: /data/target1
#  TargetID: 2002 Capacity: 10.0 TB Used: 7.1 TB (71%) Path: /data/target2
```

### 2. BeeGFS Client RDMA Config and Stripe Tuning

```ini
# /etc/beegfs/beegfs-client.conf — AI training & checkpoint optimization
sysMgmtdHost = mgmt.example.com
connUseRDMA = true               # Use InfiniBand / RoCEv2 RDMA instead of TCP
tuneUseGDTLSConnPool = true      # Connection pooling reduces per-I/O setup latency
tuneUseGDTLSDisableSSL = false
tunePrefetchType = buffered      # Client read-ahead caching for sequential dataset scans
connMaxInactiveTime = 900000     # Keep connections alive across long GPU compute steps
```

```bash
# Verify client mount, RDMA connectivity, and file stripe layout
mount | grep beegfs
grep -E "sysMgmtdHost|connUseRDMA|tuneUseGDTLSConnPool|tunePrefetchType" /etc/beegfs/beegfs-client.conf
beegfs-ctl --clientinfo

# Set directory stripe pattern BEFORE writing training shards or checkpoints
# Training data: 4 MiB chunks across 12 targets for large sequential batch reads
beegfs-ctl --setpattern --chunksize=4M --numtargets=12 /beegfs/training-data/

# Checkpoints: 2 MiB chunks across 12 targets for maximum parallel write fan-out
beegfs-ctl --setpattern --chunksize=2M --numtargets=12 /beegfs/checkpoints/

# Verify stripe pattern on a specific 500 GB shard
beegfs-ctl --getentryinfo /beegfs/dataset/train.tar.gz

# Benchmark single-client direct read throughput (expect 4-5 GB/s across 8-12 targets)
time dd if=/beegfs/training-data/large-file bs=4M count=25000 of=/dev/null iflag=direct
```

### 3. Linux read-ahead and a high-throughput NFS mount

For the `gdsio` benchmark and the GPUDirect Storage setup, see chapter 13.3.

```bash
# Check the NVMe scheduler and raise read-ahead to 4 MiB
cat /sys/block/nvme0n1/queue/scheduler
cat /sys/block/nvme0n1/queue/read_ahead_kb
blockdev --setra 8192 /dev/nvme0n1   # 8192 x 512 B sectors = 4 MiB

# NFS client mount options for VAST NFS over RDMA or an enterprise NAS
mount -t nfs -o rdma,port=20049,nconnect=16,rsize=1048576,wsize=1048576,noatime,async,actimeo=60,lookupcache=pos \
  10.30.0.10:/ai-datasets /mnt/data

# Check that the client can use GPUDirect Storage at all
/usr/local/cuda/gds/tools/gdscheck -p
```

### 4. Production S3 Manifest Validation and Exponential Backoff Prefetch

```python
# Production S3 manifest verification + asynchronous 8-worker prefetch with exponential backoff
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import time
import boto3
from botocore.exceptions import ClientError

def verify_and_stage_manifest(manifest_path: str, cache_dir: str = "/local-cache", max_workers: int = 8) -> None:
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    s3 = boto3.client("s3")
    os.makedirs(cache_dir, exist_ok=True)

    def download_and_verify(shard: dict, max_retries: int = 3) -> str:
        local_path = os.path.join(cache_dir, shard["name"])
        if os.path.exists(local_path) and os.path.getsize(local_path) == shard["size"]:
            return local_path
        bucket, key = shard["s3_path"].replace("s3://", "").split("/", 1)
        for attempt in range(max_retries):
            try:
                s3.download_file(bucket, key, local_path)
                digest = hashlib.sha256()
                with open(local_path, "rb") as lf:
                    for chunk in iter(lambda: lf.read(16 * 1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != shard["sha256"]:
                    raise ValueError(f"SHA-256 mismatch on {shard['name']}")
                return local_path
            except ClientError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
        return local_path

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(download_and_verify, s) for s in manifest["shards"]]
        for fut in futures:
            fut.result()
```

---

## How it fails

Suppose a parallel filesystem or S3 staging pipeline is misconfigured. The failure rarely shows up as a clear storage error. You are more likely to see idle GPUs, epoch-boundary hangs or sudden checkpoint timeouts. Use the symptoms and verification checks below to find the broken layer quickly.

| Failure Mode | Observable Symptom | Root Cause Diagnosis | Verification Check | Remediation |
|---|---|---|---|---|
| **1. BeeGFS `MDS` Saturation at Epoch Start** | Training hangs or crawls at the start of every epoch; metadata latency spikes to **`30 ms+`** (vs `< 5 ms` healthy) | `100–256+` GPUs concurrently `open()`/`stat()` millions of small individual files (`200K+` ops/sec), overwhelming `beegfs-meta` (`50K–100K` ops/sec per server) | `beegfs-ctl --serverstats --nodetype=meta` and `time ls -la /beegfs/dataset/ \| wc -l` | Repackage small files into `100 MB–10 GB` `WebDataset` `.tar` or `TFRecord` shards (`100x` fewer metadata ops, `< 5K` ops/s); scale out `beegfs-meta` servers |
| **2. Narrow Directory Stripe Width (`numtargets = 1` or `2`)** | A `500 GB` checkpoint stalls the cluster for `312.5 s` (`1.6 GB/s`), or a client reads at `800 MB/s` instead of `4–5 GB/s` | Directory was created with default `numtargets=1` or `2`; existing files keep their narrow stripe layout even after `--setpattern` is run later | `beegfs-ctl --getentryinfo /beegfs/checkpoints/ckpt.pt` (inspect `NumTargets` and `ChunkSize`) | Set `beegfs-ctl --setpattern --chunksize=2M --numtargets=12` on the directory *before* creating files; restripe/copy existing files |
| **3. BeeGFS Storage Target Fill Skew (`> 10%` Spread)** | `storage2` targets hit `71–72%` (or `95%`) full while `storage1` targets sit at `44–45%`; wide writes fail when one target fills | Large unstriped files (`numtargets=1`) or uneven client placement concentrated writes on `storage2` | `beegfs-ctl --listtargets --nodetype=storage --spaceinfo` | Enforce wide directory striping (`numtargets=8` or `12`) and run `beegfs-ctl --migrate` to rebalance overloaded target IDs |
| **4. BeeGFS / WekaFS / VAST Client Fallback from `RDMA` to `TCP` or `SYS` NUMA Path** | Single-client read throughput drops from `4–5 GB/s` to `800 MB/s`, or clients show `2x` throughput variance across nodes | `connUseRDMA = false`, storage subnet routed over a slow management NIC, or DataLoader workers scheduled on the wrong CPU/NUMA socket (`SYS` traversal) | `beegfs-ctl --clientinfo`, `lsof \| grep beegfs`, `iperf3`, and `numactl --hardware` | Enable `connUseRDMA = true`, verify lossless `RoCEv2`/`IB` path, and pin DataLoader workers (`numactl`) to the storage NIC's local NUMA node |
| **5. Attempting Kernel `GDS` (`cuFile`) over a User-Space `FUSE` Mount** | `cuFileRead` falls back to host compatibility mode (`-x 2` speed, high CPU `memcpy` load) or fails `O_DIRECT` registration | Standard `FUSE` filesystems route I/O through user-space daemons and lack kernel `nvidia-fs` `O_DIRECT` DMA integration | `/usr/local/cuda/gds/tools/gdscheck -p` and `gdsio -x 0` vs `-x 2` | Use a `GDS`-supported kernel client (`BeeGFS`, `WekaFS`, `VAST NFS-over-RDMA`, `Lustre`, `GPFS`, local `XFS` `NVMe`) or native user-space `RDMA` + `io_uring` (`3FS`) |
| **6. S3 Cold-Cache Stall, Early LRU Eviction, or `503 Slow Down`** | Epoch 1 is `10x` slower than Epoch 2 (`45.3 min` vs `2.1 min` wait), training stalls `30 s` every `5 min`, or S3 returns `503` / `403` | Cold NVMe cache in Epoch 1; download pool (`8` workers) slower than GPU consumption; cache fill `> 85%` triggering LRU eviction in Epoch 3 (`97.5%` hit); or unsharded S3 prefix exceeding `5,500` `GET`/s | Log per-epoch `cache_hits / (cache_hits + cache_misses)`, `df -h /local-cache`, and `aws sts get-caller-identity` | Pre-warm local NVMe cache before `1`-epoch jobs, scale download workers `8 -> 16`, enlarge NVMe cache above dataset working set, use STS credentials with sufficient TTL, and shard S3 keys across `16+` prefixes |

---

## Hands-on lab

### Venue and scope

The lab runs the Python script `code/part13/beegfs_weka_vast_object_lab.py` against the models in `code/part13/beegfs_weka_vast_object.py`. It needs no cluster. It checks BeeGFS chunk placement and checkpoint stall times, metadata saturation, target fill skew, WekaFS and VAST erasure coding, the 3FS benchmark arithmetic and the S3 staging cache progression.

### Step 1: Run the Self-Contained Verification Lab

Run the script with the command below. Each line of the expected output maps to one quantitative model.

```bash
python3 -B code/part13/beegfs_weka_vast_object_lab.py
```

**Expected output:**
```text
=== Chapter 13.5 Lab: BeeGFS, Weka, VAST and Object Storage ===
=== Chapter 13.5 Lab: BeeGFS, Weka, VAST and Object Storage ===
  [PASS] 1. BeeGFS defines four decoupled services: beegfs-mgmtd, beegfs-meta, beegfs-storage, and beegfs-client
  [PASS] 2. BeeGFS storage node capacity ranges from 500 MB/s to 2000 MB/s (2 GB/s) with a +/-5% healthy target fill band
  [PASS] 3. BeeGFS 1 MiB chunksize across 8 targets maps offset 0 to slot 0 (Target 1001) and offset 10 MiB to chunk 10, row 1, slot 2 (Target 2001)
  [PASS] 4. BeeGFS 500 GB checkpoint striped across 2 targets at 800 MB/s gets 1.6 GB/s (312.5 s) vs 8 targets getting 6.4 GB/s (78.125 s, 4.0x faster)
  [PASS] 5. BeeGFS 12-target training/checkpoint pattern at 800 MB/s/target yields 9.6 GB/s theoretical throughput (52.0833 s for 500 GB)
  [PASS] 6. 256 GPUs generating 204,800 metadata ops/sec saturate 1 MDS (50K ops/sec, needing >= 5 MDSs), while 100x WebDataset sharding drops load to 2,048 ops/sec
  [PASS] 7. BeeGFS target fill check flags storage1 (45%, 44%) vs storage2 (72%, 71%) as a 28% spread (> 10% investigation threshold, outside +/-5% band)
  [PASS] 8. WekaFS 8-node cluster with 6+2 erasure coding achieves 75.0% usable NVMe capacity (2.25x more usable capacity than 3x replication)
  [PASS] 9. WekaFS 18-node cluster with 16+2 erasure coding achieves 88.89% usable NVMe efficiency and pins dedicated client cores (4/128 = 3.125% core tax)
  [PASS] 10. WekaFS unifies Tier 1 hot NVMe-o-RDMA storage (737.28 TB usable on 8 nodes) with Tier 2 S3 object storage (2000 TB) into a 2737.28 TB POSIX namespace
  [PASS] 11. WekaFS rejects N+K stripe widths that exceed the number of failure-domain storage nodes
  [PASS] 12. VAST DASE decouples stateless CNodes from NVMe-oF DNodes (SCM/Optane write buffer + QLC flash) with zero east-west CNode lock traffic
  [PASS] 13. VAST DASE wide 146+4 erasure stripe achieves 97.33% net capacity efficiency (only 2.67% parity overhead across DNodes)
  [PASS] 14. DeepSeek 3FS comprises 4 RDMA-connected components (Cluster Manager, Metadata Service, Storage Service, Client) and bypasses the OS page cache via O_DIRECT + io_uring
  [PASS] 15. DeepSeek 3FS peak benchmark: 180 storage nodes (2,880 x 14 TiB NVMe = 40,320 TiB, dual 200 Gb/s NICs = 9.0 TB/s line rate) reach about 6.6 TiB/s (7.26 TB/s) aggregate read
  [PASS] 16. Each 3FS storage node serves 37.55 GiB/s (40.32 GB/s) of its 50 GB/s network line rate, about 80.6 percent
  [PASS] 17. Fetching 2,000,000 small 260 KB objects serially from S3 at 150 ms/request wastes 300,000 seconds (83.33 hours) on HTTP/TLS API latency alone
  [PASS] 18. Prefetching 2 x 10 GB shards (20 GB) with 8 workers at 150 MB/s each (1.2 GB/s aggregate) takes 16.67 s transfer + 10.2 s API/TLS = 26.87 s (~27 s) to first batch
  [PASS] 19. Doubling S3 download workers from 8 to 16 (2.4 GB/s aggregate) cuts 20 GB transfer time to 8.33 s (18.53 s total with API/TLS)
  [PASS] 20. S3 prefix sharding across 16 prefixes scales request ceilings from 5,500 GET/s and 3,500 PUT/s to 88,000 GET/s and 56,000 PUT/s
  [PASS] 21. Parallel 8 x 1 GB S3 download finishes in 7.5 s (1066.67 MB/s aggregate, 133.33 MB/s per worker) vs 6.2 s single-object (161.29 MB/s) and 49.6 s serial (6.61x speedup)
  [PASS] 22. Local NVMe staging cache warms from 0.1% hit rate (45.3 min wait) in Epoch 1 to 98.2% (2.1 min wait, 21.57x wait reduction) in Epoch 2
  [PASS] 23. Local NVMe staging cache detects LRU eviction onset in Epoch 3 when cache fill (88.0%) exceeds the 85.0% threshold and hit rate dips to 97.5% (3.5 min wait)
  [PASS] 24. GB200/GB300 NVL72 rack (72 GPUs x 200 MB/s per GPU) requires 14.4 GB/s (14-20 GB/s envelope) of sustained storage ingestion bandwidth
  [PASS] 25. Reducing GPU I/O wait time from 30% to 5% lowers the I/O stall fraction by 6.0x and recovers 25 percentage points of active GPU compute time

Summary: 25 passed, 0 failed
```

---

## Common first mistakes

1. Suppose you upload the dataset or write checkpoints first, and only then run `beegfs-ctl --setpattern`. The new stripe pattern does nothing for files that already exist. Directory stripe patterns are inherited only when a new inode is created. Changing `--numtargets=12` on `/beegfs/checkpoints/` does nothing to a 500 GB file that was already created with two targets. You must rewrite or migrate existing files.
2. Do not put `beegfs-meta` and `beegfs-storage` on the same physical disks in production. Sharing spindles or NVMe queues between 50,000 random inode transactions per second and 2 GB/s bulk checkpoint writes causes severe metadata tail-latency spikes above 30 ms. Give `beegfs-meta` its own low-latency NVMe mirrors.
3. Consider how one cold-cache epoch plays out in two different jobs. In a 100-epoch pretraining run, a first epoch of 180 minutes against 30-minute epochs after it adds an extra 2.5 hours. That is under 5 percent of a 50-hour run. In a one-epoch fine-tuning job, the same cold wait is 100 percent overhead. Pre-warm the local NVMe cache before you start GPU workers.
4. Avoid calling `s3.list_objects_v2()` inside every rank's dataset initialization. Suppose a thousand GPU workers start at once and paginate through two million keys. They quickly use up the per-prefix rate limit, which triggers 503 Slow Down errors. If new files are uploaded mid-run, the listing can also cause silent training drift. Read a static, version-pinned `manifest.json` file instead.
5. Do not forget `ulimit -l` when you turn on `pin_memory=True` or GPUDirect Storage. Both PyTorch's `DataLoader` with pinned memory and `cuFile` buffer registration lock pages in physical RAM. If the container's `memlock` limit stays at the default 64 KB, you get mid-epoch allocation crashes or a silent fallback to unpinned transfers. Check each item before the first run, not after the first crash.

---

## Exercises

Work through the six exercises below using the parameters in the block. The block also lists the values the verification lab should produce, so you can check your answers.

```text
Exercise Input Parameters & Expected Verification Targets (code/part13/beegfs_weka_vast_object_lab.py):
  - Ex 1 (BeeGFS Stripe & Checkpoint):
      (a) --chunksize=1M (1,048,576 B), --numtargets=8 [1001, 1002, 2001, 2002, 3001, 3002, 4001, 4002], offset 10,486,272 B (10 MiB + 512 B)
          -> chunk_index = 10, stripe_row = 1, target_slot = 2, TargetID = 2001, intra_chunk_offset = 512 B.
      (b) 500 GB checkpoint at 800 MB/s per target:
          numtargets=2  -> 1.6 GB/s (312.5 s);
          numtargets=8  -> 6.4 GB/s theoretical (78.125 s, saving 234.375 s) or 5.0 GB/s at 78.125% efficiency (100.0 s, saving 212.5 s);
          numtargets=12 -> 9.6 GB/s (52.0833 s / 52.08 s).
  - Ex 2 (BeeGFS 256-GPU Metadata & Skew):
      (a) 256 GPUs x 800 ops/sec = 204,800 ops/sec peak; requires >= 5 MDS nodes at 50,000 ops/sec/MDS (250,000 ops/sec); 100x WebDataset sharding -> 2,048 ops/sec (1 MDS at < 5 ms).
      (b) storage1: 1001 (4.5/10.0 TB = 45%), 1002 (4.4/10.0 TB = 44%); storage2: 2001 (7.2/10.0 TB = 72%), 2002 (7.1/10.0 TB = 71%)
          -> mean fill = 58.0%, max spread = 28.0% (> 10% threshold, outside +/-5% band); migrate TargetIDs [2001, 2002].
  - Ex 3 (WekaFS Erasure Coding & Tiering):
      (a) 8 nodes x 8 x 15.36 TB = 983.04 TB raw; 6+2 stripe = 737.28 TB usable (75.0%) vs 3x replication = 327.68 TB (33.33%), a 2.25x gain; + 2,000 TB Tier 2 S3 = 2,737.28 TB namespace.
      (b) 18 nodes with 16+2 stripe = 88.89% efficiency; 4 pinned ll_core threads on 128-core host = 3.125% CPU tax.
  - Ex 4 (VAST DASE):
      146+4 wide stripe on 1,500 TB raw QLC (24 TB SCM buffer): parity overhead = 2.67% (4/150), net efficiency = 97.33% (146/150), physical usable = 1,460.0 TB, logical at 2.0x reduction = 2,920.0 TB.
  - Ex 5 (DeepSeek 3FS):
      180 nodes x 16 x 14 TiB NVMe = 2,880 SSDs (40,320 TiB raw), dual 200 Gb/s NICs = 50 GB/s per node, 9.0 TB/s line rate; 6.6 TiB/s = 7.26 TB/s = 40.32 GB/s per node = 80.6% of line rate.
  - Ex 6 (S3 Staging Pipeline):
      (a) 2,000,000 x 260 KB at 150 ms = 300,000 s (83.33 hours); 20 GB (2 x 10 GB shards) across 8 workers (1.2 GB/s) = 16.67 s + 10.0 s API + 0.2 s TLS = 26.87 s (~27 s); 16 workers (2.4 GB/s) = 8.33 s + 10.2 s = 18.53 s.
      (b) 16 prefixes x (5,500 GET/s, 3,500 PUT/s) = 88,000 GET/s and 56,000 PUT/s; 8 x 1 GB in 7.5 s (1,066.67 MB/s agg, 133.33 MB/s/worker) vs 6.2 s single (161.29 MB/s) and 49.6 s serial = 6.61x speedup; Epoch 1 (0.1%, 45.3 min) -> Epoch 2 (98.2%, 2.1 min) = 21.57x wait reduction; Epoch 3 rises to 3.5 min (97.5% hit) because 88.0% fill exceeds 85.0% LRU eviction threshold.
```

1. Start with the byte offset in Ex 1. Work out the chunk index, stripe row, target slot, TargetID and intra-chunk offset for it. Then compute the theoretical write bandwidth, the checkpoint stall, and the seconds saved when you stripe the checkpoint across two, eight and twelve targets.
2. Using Ex 2, find the peak metadata ops/sec for the cluster and the minimum number of `beegfs-meta` nodes you need. Then work out the rate after WebDataset sharding. Finally, measure the fill spread between `storage1` and `storage2`, and say which targets need migration.
3. For the cluster in Ex 3, compute the raw NVMe capacity, the usable Tier 1 capacity, the replication baseline, the usable capacity gain and the total unified POSIX namespace. Then find the net erasure efficiency on the larger cluster, along with the CPU core tax of pinning polling client cores.
4. For the wide stripe in Ex 4, calculate the parity overhead percentage, the net efficiency, the usable physical QLC capacity and the effective logical capacity at 2.0 times data reduction.
5. Using Ex 5, calculate the total SSD count, the raw flash capacity, the network line rate of the cluster, the per-node read rate and the share of line rate that the benchmark reached. Then explain why 3FS bypasses the page cache.
6. For Ex 6, compare the serial API wait for two million small S3 requests with prefetching two large shards across eight or sixteen workers. Then compute the prefix sharding ceilings, the parallel download speedup and the wait reduction from epoch 1 to epoch 2. Last, explain why wait time rises in epoch 3.

---

## Interview angles

Interviewers use these questions to see whether you can reason about trade-offs. Answer with the mechanism, not just the product name.

1. **"You are deploying BeeGFS for a 256-GPU cluster. What is your single biggest architectural risk, and how do you mitigate it?"**
   Metadata saturation on `beegfs-meta` is the top risk. Picture 256 GPUs starting an epoch over millions of small files. Metadata demand spikes past 200,000 ops/sec, which is four times a single server's 50,000 ops/sec safe ceiling, and latency climbs past 30 ms. Start by scaling out to four or five metadata servers and spreading directory subtrees across them. Then repackage the small files into large WebDataset `.tar`, TFRecord, or `.bin` and `.idx` shards. That repackaging cuts metadata operations a hundredfold, down to 2,048 ops/sec, and keeps latency around 2.1 ms even on a single server.
2. **"How do WekaFS and VAST Data solve the metadata and small-file problem differently than Lustre and BeeGFS?"**
   Lustre and BeeGFS rely on dedicated metadata servers that partition the directory namespace. WekaFS removes dedicated metadata servers altogether. It slices both file data and virtual metadata into 4 KB chunks across every NVMe node in the cluster, and it drives RDMA from pinned polling client cores. VAST Data DASE separates stateless protocol containers from NVMe-oF drive enclosures. It keeps all global metadata and coalesces random writes inside Storage Class Memory. Then it destages wide 146+4 erasure stripes to QLC flash, with zero east-west lock traffic.
3. **"Why does a filesystem like 3FS bypass the OS page cache?"**
   LLM pretraining and KV cache workloads read randomly across petabytes of data. On a conventional page cache those reads almost never hit, and they waste CPU on page-table work. 3FS combines `O_DIRECT`, `io_uring` for batched submission and RDMA. The project reports about 6.6 TiB/s of aggregate read on 180 storage nodes. It is a custom stack that needs a team to run it.
4. **"Epoch 1 on an S3-backed dataset takes 3 hours, while Epoch 2 takes 30 minutes. Explain the exact mechanics and whether you should fix it."**
   The first epoch starts with a cold cache at a 0.1 percent hit rate. Workers pull shards over HTTP and TLS into the local NVMe staging cache, which leaves 45.3 minutes or more of download wait. The second epoch is warm, at a 98.2 percent hit rate and 2.1 minutes of wait, because it reads straight from local NVMe. Over a 100-epoch run, the extra 2.5 hours on the first epoch is under 5 percent of total runtime, so it amortizes. Over a one-epoch fine-tuning run, the same wait is 100 percent wasted GPU time. So fix it by pre-warming the local NVMe cache from the version-pinned JSON manifest before you launch GPU workers.

---

## Checkpoint questions (20)

<details>
<summary>**1. How much aggregate storage read bandwidth is required to keep an 8-GPU node and a 72-GPU Grace Blackwell NVL72 rack saturated at 200 MB/s per GPU?**</summary>

At 200 MB/s per GPU, an eight-GPU server needs 1.6 GB/s of sustained read throughput. A 72-GPU GB200 or GB300 NVL72 rack needs 14.4 GB/s, which sits inside the 14 to 20 GB/s operational envelope.
</details>

<details>
<summary>**2. What are the four core services in a BeeGFS cluster, and which ones sit on the active I/O data path?**</summary>

The four services are `beegfs-mgmtd` for cluster registry management, `beegfs-meta` for directory inodes and stripe layouts, `beegfs-storage` for NVMe and XFS storage targets, and `beegfs-client` for the kernel mount on GPU nodes. Once a file is open, only `beegfs-client` and `beegfs-storage` carry the bulk data.
</details>

<details>
<summary>**3. What are the healthy operational thresholds for a BeeGFS Metadata Service and Storage Target?**</summary>

A `beegfs-meta` server should stay below 50,000 ops/sec and keep average latency under 5 ms. A `beegfs-storage` node delivers 500 MB/s to 2 GB/s. Every storage target should stay within a plus or minus 5 percent fill band. If you see a spread above 10 percent, investigate it.
</details>

<details>
<summary>**4. In BeeGFS, how is a logical file byte offset mapped to a storage target given chunk size C and target count N?**</summary>

BeeGFS uses round-robin striping. The chunk index is `floor(B / C)`, the stripe row is `floor(chunk_index / N)`, the target slot is `chunk_index mod N`, and the intra-chunk offset is `B mod C`. With a 1 MiB chunk size across eight targets, byte offset 10 MiB plus 512 B lands in chunk 10, row 1, target slot 2, at byte offset 512 inside that chunk.
</details>

<details>
<summary>**5. A 500 GB checkpoint is written to a BeeGFS cluster with 800 MB/s per target. How long does the write stall training with 2, 8, or 12 targets?**</summary>

With two targets, the aggregate bandwidth is 1.6 GB/s, and the write stalls for 312.5 seconds. With eight targets, the theoretical bandwidth reaches 6.4 GB/s, which makes a 78.125-second write. At a sustained 5.0 GB/s, it takes 100 seconds. With twelve targets, the theoretical bandwidth reaches 9.6 GB/s and cuts the write to 52.08 seconds.
</details>

<details>
<summary>**6. Why doesn't running `beegfs-ctl --setpattern --numtargets=12 /beegfs/checkpoints/` speed up reads of checkpoints that were already written in that directory?**</summary>

BeeGFS records a file's stripe width and chunk size in its inode at the moment the file is created. Running `--setpattern` on a directory affects only the files created after that. Existing files must be rewritten, or migrated with `beegfs-ctl --migrate`.
</details>

<details>
<summary>**7. Why does a 256-GPU cluster opening raw JPEG files saturate BeeGFS metadata, and why is scaling out MDS nodes alone insufficient?**</summary>

When 256 GPUs each issue 800 metadata calls per second, the 204,800 ops/sec storm is four times one metadata server's 50,000 ops/sec safe limit. Adding four or five metadata servers still is not enough when millions of files sit in one flat directory. Every lookup then lands on the one server that owns that directory's inode. Repackaging the files into WebDataset or TFRecord shards cuts metadata calls a hundredfold, to 2,048 ops/sec.
</details>

<details>
<summary>**8. Which `/etc/beegfs/beegfs-client.conf` parameters are most critical for AI GPU clusters?**</summary>

Set `connUseRDMA = true` to use InfiniBand or RoCEv2 RDMA instead of TCP. Set `tunePrefetchType = buffered` for read-ahead on sequential shards. Turn on `tuneUseGDTLSConnPool = true` to pool connections. Set `connMaxInactiveTime = 900000` so connections stay up through long GPU compute steps.
</details>

<details>
<summary>**9. How does WekaFS eliminate the Metadata Server bottleneck present in both Lustre and BeeGFS?**</summary>

WekaFS has no dedicated metadata servers. It cuts both file data and virtual metadata into 4 KB chunks and spreads them across every NVMe storage node in the cluster. Because every node serves `open`, `stat` and `unlink` in parallel, no single server becomes the choke point.
</details>

<details>
<summary>**10. Why does the native WekaFS client pin dedicated CPU cores on GPU servers, and how does it compare to mounting WekaFS via NFS?**</summary>

The native client pins one to four polling CPU cores, which is 3.125 percent of a 128-core host. That lets it drive a lockless RDMA engine without OS interrupt latency or NFS state-machine overhead. The result is full GPUDirect Storage bandwidth and millions of small-file IOPS. A legacy NFS mount needs no pinned cores, but it gives up GPUDirect Storage and high IOPS.
</details>

<details>
<summary>**11. How does WekaFS unify local NVMe flash and cloud S3 object storage for PyTorch workloads?**</summary>

WekaFS presents one POSIX mount point. Hot working sets sit on Tier 1 NVMe flash over RDMA, and cold data extents tier to Tier 2 S3 object storage over HTTPS without any extra steps. PyTorch scripts open `.pt`, `.ckpt` and `.bin` files as usual. The metadata headers stay on Tier 1 flash, so directory lookups stay instant.
</details>

<details>
<summary>**12. In VAST Data's Disaggregated Shared-Everything architecture, what is the difference between CNodes and DNodes?**</summary>

CNodes are stateless protocol containers that serve NFS-over-RDMA, S3 and SMB. They hold no persistent state and send no east-west lock traffic between nodes. DNodes are high-availability NVMe-oF enclosures. They hold Storage Class Memory for global metadata and write coalescing, plus high-density QLC NAND flash for bulk capacity.
</details>

<details>
<summary>**13. How does VAST Data achieve 97.33% net capacity efficiency on QLC flash without suffering random-write wear-out?**</summary>

Every incoming random write and metadata update lands first in high-endurance Storage Class Memory. There, CNodes coalesce them into large sequential erase-block stripes. The stripes then go to QLC flash under a wide 146+4 locally decodable erasure code. That stripe adds only 2.67 percent parity overhead, which gives 97.33 percent net efficiency.
</details>

<details>
<summary>**14. Which filesystems can use kernel GPUDirect Storage, and how do you check a client?**</summary>

Filesystems with a kernel client that works with `nvidia-fs`, such as BeeGFS, WekaFS, VAST over NFS with RDMA, Lustre and GPFS. A user-space FUSE mount cannot. Run `gdscheck -p` on the client, and see chapter 13.3 for the measurement.
</details>

<details>
<summary>**15. What are the four services of DeepSeek's Fire-Flyer File System, and what did its published benchmark reach?**</summary>

Cluster Manager, Metadata Service, Storage Service and Client. On 180 storage nodes with two 200 Gbps NICs and sixteen 14 TiB NVMe SSDs each, the project reports about 6.6 TiB/s of aggregate read throughput with background training traffic, roughly 80 percent of the 9.0 TB/s network line rate.
</details>

<details>
<summary>**16. Why does 3FS bypass the page cache, and why can a plain FUSE mount not use kernel GPUDirect Storage?**</summary>

Random reads over petabytes rarely hit the page cache and cost CPU in page-table work, so 3FS reads with `O_DIRECT`, `io_uring` and RDMA. Kernel GPUDirect Storage needs a kernel client that works with `nvidia-fs`, which a user-space FUSE daemon does not provide.
</details>

<details>
<summary>**17. Why does training directly on 2,000,000 small 260 KB objects in S3 stall GPUs for 83.33 hours?**</summary>

Each S3 GET request carries roughly 150 ms of TCP, TLS and API lookup latency. That delay dwarfs the transfer time of a 260 KB payload. If you issue two million requests one after another, you waste 300,000 seconds, or 83.33 hours, waiting on HTTP round-trips.
</details>

<details>
<summary>**18. What are the per-prefix request limits in S3, and how does prefix sharding across 16 prefixes prevent 503 Slow Down errors?**</summary>

A single S3 prefix supports 5,500 GET or HEAD requests per second and 3,500 PUT, COPY, POST or DELETE requests per second. Spreading keys evenly across 16 hex prefixes multiplies the aggregate capacity sixteenfold, to 88,000 GET/s and 56,000 PUT/s. That keeps any one prefix below its limit.
</details>

<details>
<summary>**19. With a 500 GB dataset split into 50 x 10 GB shards in S3 and 8 download workers at 150 MB/s each, what is the expected startup time to the first training batch?**</summary>

Eight workers at 150 MB/s deliver 1.2 GB/s of aggregate download bandwidth. Prefetching the first two shards, or 20 GB, takes 16.67 seconds of transfer. Add 10.2 seconds of S3 API and TLS overhead, and the total time to the first batch is 26.87 seconds.
</details>

<details>
<summary>**20. In a multi-epoch S3-to-NVMe staging pipeline, what causes cache hit rate to rise from 0.1% in Epoch 1 to 98.2% in Epoch 2 and then dip to 97.5% in Epoch 3?**</summary>

Think about what your cache does across three epochs. The first epoch starts with a cold local NVMe cache, at a 0.1 percent hit rate and 45.3 minutes of download wait. By the second epoch, the shards are cached on local NVMe, which lifts the hit rate to 98.2 percent and cuts the wait to 2.1 minutes. In the third epoch, cache fill crosses 85 percent and reaches 88 percent. That triggers LRU eviction of earlier shards and pushes the wait up to 3.5 minutes.
</details>

---

## Sources and review notes

### Sources used

| Source | Used for |
|---|---|
| BeeGFS documentation | Services, stripe patterns, `beegfs-ctl` |
| WEKA documentation and *AI Data Center Network Design and Technologies*, chapter 9 | Distributed 4 KB metadata, erasure coding, client core pinning, object tiering, the PCIe, InfiniBand and Ethernet latency comparison |
| VAST Data documentation | Disaggregated shared-everything design, storage-class-memory write buffer, wide erasure stripes |
| DeepSeek 3FS project README (github.com/deepseek-ai/3FS, read 2026-11-12) | Four services, `O_DIRECT`, `io_uring` and RDMA, and the peak benchmark: 180 storage nodes, two 200 Gbps NICs and sixteen 14 TiB SSDs each, about 6.6 TiB/s read |
| Amazon S3 documentation, request rates and prefixes | 5,500 GET and 3,500 PUT per second per prefix |
| *AI Systems Performance Engineering*, chapter 5 | Per-GPU bandwidth arithmetic, NVMe read-ahead, GPUDirect Storage context |
| NVIDIA storage field notes (volume 15 of the `nvidia-devops` repository) | BeeGFS and S3 worked examples. The figures are illustrative. |

### Corrections made in this revision

- The 3FS benchmark was described as 68 nodes with 100 Gb/s NICs and a Ceph comparison. The project README reports 180 storage nodes with two 200 Gbps NICs and about 6.6 TiB/s, and it makes no Ceph comparison. The numbers and the lab were corrected.
- The `gdsio` comparison table duplicated chapter 13.3 and was removed. This chapter now links there.
- A comparison of BeeGFS, WekaFS, VAST and object storage on metadata rate, small-file behaviour and failure modes was added as section 6.

### Not verified here

The cluster commands were not run. The BeeGFS metadata ceiling of 50,000 to 100,000 operations per second, the 4 KB WekaFS chunk size and the VAST 146 plus 4 stripe come from the vendor-oriented notes above and were not measured. Measure your own metadata rate with `mdtest`.
