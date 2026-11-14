---
id: "c13-02"
title: "13.2 Local NVMe and data staging"
sidebar_label: "13.2 Local NVMe and data staging"
sidebar_position: 2
description: "Local NVMe and data staging on AI compute nodes: 2-tier DGX H100/H200 and GB200/GB300 NVL72 scratch architectures, mdadm RAID 0 chunk and XFS stripe alignment, multi-epoch staging break-even math, asynchronous checkpoint staging, Linux blk-mq and read-ahead tuning, SMART endurance telemetry, and Slurm prolog/epilog lifecycle management, verified by a 28-check Python lab."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 13.2 Local NVMe and data staging

| | |
|---|---|
| **Status** | Drafted (`local_nvme_staging_lab.py`: 28 checks pass; bare-metal `mdadm`, `mkfs.xfs`, `nvme`, and `fio` commands **untested** here) |
| **Level** | Intermediate |
| **Priority tier** | 2 |
| **Lab venue** | GCP / GKE + self-checking Python model (`code/part13/local_nvme_staging_lab.py`) |
| **Part** | Part 13: AI storage |
| **Sources used** | `nvidia-devops` V15 Ch. 3 (`chapter-03-local-nvme-and-data-staging.md`) and V15 Lab 02 (`lab-02-benchmark-local-nvme-and-shared-storage.md`); *AI Systems Performance Engineering* (`ai-systems-performance-engineering`); *AI Data Center Network Design and Technologies* (`ai-data-center-network-design-and-technologies`) |
| **Coverage file** | `planning/coverage/chapters/13-02.md` |

## Why this matters for AI infrastructure

Picture a GPU node that a team has just built as a stateless box, with every byte of data living on the network. Within a week, the storage network is the busiest thing in the room. In enterprise web infrastructure, the golden rule is the stateless compute node. Local disks are treated as a liability, and all application state lives on remote storage. That rule works well for web servers. In large-scale AI training, following it too closely turns the storage network into a choke point, and the expensive GPUs end up waiting for their next batch of data.

An AI training job rarely reads a dataset just once. A vision or multimodal model may iterate over the same thousands to millions of files for hundreds of epochs. Every one of those passes has to keep thousands of GPUs fed at the same time. A single slow pass stalls the whole cluster, because the GPUs move forward together.

Feeding Tensor Cores takes real bandwidth. Tensor Cores are the matrix units inside the GPU that do the heavy arithmetic, and they can only work as fast as data arrives. Take an eight-GPU node first. It needs about 1.6 GB per second of continuous ingestion. A 72-GPU DGX GB200 or GB300 NVL72 rack needs 14 to 20 GB per second. Both figures work out to roughly 200 MB per second per GPU, or 14.4 GB per second for the rack.

Now scale that up. Picture 256 GPUs spread across eight nodes, or as many as a thousand GPUs across a full pod, all training again and again on the same 500 GB dataset. That dataset holds two million files averaging 260 KB each. Each GPU needs 120 MB per second to stay fed. Across the job, that adds up to about 30.7 GB per second in aggregate. Think of it as a steady stream of groceries that must reach every kitchen in the building at once.

The shared storage link cannot deliver that cleanly. Opening and checking two million small files adds about 30 percent metadata overhead. Metadata overhead is the extra work spent on names, permissions, and open calls before any data moves. So each GPU receives about 110 MB per second, a little less than the 120 MB per second it needs. That shortfall stalls a cold epoch for 245 seconds, and for almost all of that time the GPUs wait on data instead of computing.

Checkpointing causes a second and different kind of stall. A checkpoint is a saved snapshot of the training state, so a crashed job can resume from it. Writing a 500 GB checkpoint synchronously to shared Lustre at 1.2 GB per second freezes every GPU in the job for about 417 seconds. Nothing computes during that wait, and the cost is paid again each time a checkpoint is written.

Local NVMe solves both problems. It moves the repeated reads and the checkpoint writes off the shared network entirely. NVMe is a flash drive interface that talks directly over PCIe. Every modern AI server ships with a dedicated bank of PCIe NVMe drives wired directly into the node's own PCIe switches. A DGX H100 or H200 carries 30.72 TB of U.2 scratch space across eight striped drives. A DGX GB200 or GB300 NVL72 compute tray carries 15.36 TB of E1.S scratch, and that scales to 276.48 TB across a full rack.

Used well, that local storage pays for itself quickly. If you cache the dataset after the first epoch, epoch time drops from 245 seconds to 200 seconds. That is an 18 percent speedup, and it lifts GPU utilization to 94 percent. Staging checkpoints locally shrinks the 417-second stall to a one-second handoff. The local copy costs a little time up front, and the payback arrives in every epoch that follows.

Local NVMe can also go wrong, and then it adds risk with no payoff. Streaming a dataset that is read only once gains nothing from a local copy. The same is true when scratch space fills past 85 percent, when the RAID 0 stripe is misaligned, and when nothing cleans up between Slurm jobs. Slurm is the scheduler that starts and stops jobs on the cluster. Each mistake turns a performance feature into an operational headache while the GPUs gain no speed. **Before you stage anything, ask whether the job will read the same data enough times to repay the copy.**

## Prerequisites and outcomes

Before you start, read the earlier chapters listed below. The chapter assumes you know how the DGX layouts are wired, and it assumes you can read the output of a few basic Linux storage commands without help.

**Prerequisites:**
- Chapter 9.2 on the DGX H100 and H200 two-tier NVMe layout and four-switch PCIe Gen5 topology, and Chapter 9.5 on the GB200 and GB300 NVL72 compute tray E1.S layout.
- Chapter 13.1 on the AI storage data path from disk to GPU memory.
- Basic Linux block-storage familiarity with `lsblk`, `df`, `mdadm`, `mount`, and `fio`.

This chapter follows the local drives from the node's boot disks to the scratch volume that holds the data. It separates the two local NVMe tiers on AI compute nodes: a RAID 1 M.2 boot mirror for the OS, and an ephemeral RAID 0 `/raid` scratch volume. RAID 1 means two drives hold identical copies, and RAID 0 means one dataset is spread across several drives for speed with no spare copy. The chapter then works through the `mdadm` chunk sizes and XFS stripe alignment for each volume. Next it calculates the multi-epoch staging break-even point and the speedup from asynchronous checkpoint staging, so you can tell when local NVMe pays back its copy cost and when to skip it. After that it tunes the Linux NVMe block and filesystem stack, including the scheduler, queue depth, read-ahead, `noatime`, and NUMA binding, and it validates throughput across four `fio` AI workload profiles. The last part covers NVMe endurance and SMART health, and per-job `/raid` isolation with Slurm Prolog and Epilog hooks.

---

## Concepts: basics → intermediate → advanced

## 1. Why AI compute nodes still need local NVMe: the staging decision path

Picture a platform team that has spent years making GPU nodes stateless, and now a training job keeps stalling on the network. Why would anyone put local disks back into a GPU node after years of stateless design? In a cloud-native microservice cluster, local NVMe is rarely needed. Requests are small, stateless, and not repeated. An AI factory is different, because two kinds of physics push the design the other way.

The first is read amplification. Read amplification means the same bytes are fetched again and again. During multi-epoch training, every worker node reads its assigned shards over and over, across dozens or hundreds of epochs. If you fetch the same bytes across the shared storage fabric on the second, third, and five-hundredth epoch, you waste bandwidth and metadata-server capacity each time. The first epoch already paid that cost once, so the later fetches are pure waste.

The second is the bursty write barrier. A barrier is a point where every rank must wait for the others before going on. Distributed checkpoints dump hundreds of gigabytes to terabytes of state at the same moment, from every rank. Pushing that burst straight over a shared network path stalls GPU compute for minutes at a time, as shown above. The writes are short, but the whole cluster pays for them together.

Before you read the table below, keep one simple rule in mind. Use local NVMe when the shared path is the bottleneck and the same data is read again. Skip it when either part of that rule is missing.

### 1.1 When to use local NVMe, and when to skip it

Local NVMe is an accelerator tier, not a default. Before you add staging logic to a pipeline, check two things. Does the job actually suffer from a storage bottleneck? And does the data get reused enough to repay the cost of copying it? If you can answer yes to the first and no to the second, streaming is the better choice. The table below lists the signs on each side.

| Use local NVMe (`/raid`) when... | Skip local NVMe when... |
|---|---|
| Shared storage or its metadata server is the bottleneck: for example a storage link over 80 percent utilized, or millions of small files adding heavy `open`/`stat` latency. | Shared storage has headroom: link under 50 to 60 percent utilized, GPU utilization already at or above 95 percent. |
| The dataset or per-node shard fits within 85 percent of local NVMe capacity and gets read across multiple epochs. | The dataset is a single-epoch pre-training stream over 100 TB that exceeds local scratch and is read only once. |
| Synchronous checkpoint writes pause training, from a few seconds up to hundreds of seconds on large dumps, and those writes can be staged asynchronously instead. | Checkpoints are small, infrequent, or already overlapped in host RAM. |
| Expensive preprocessing or decompression output gets reused across epochs. | Nodes fail often and lack automated cache rehydration and Epilog cleanup. |

Staging moves the second and later epochs onto local PCIe Gen5 NVMe. That storage reads at roughly 3.5 GB per second per filesystem thread, and up to 25 to 50 GB per second across a full RAID 0 array. It takes slow shared-fabric reads and writes off the GPU's critical path. The critical path is the chain of steps that the GPUs must wait for. Staging a dataset that is read only once, or one that overflows an 85 percent-full NVMe cache, adds copy latency, eviction churn, and SSD wear. You get nothing back for those costs.

```mermaid
flowchart TD
    Start["Training job starts on GPU node<br/>Query: Should we stage on local /raid?"]
    Q1{"1. First access on node<br/>OR dataset > 85% of /raid?"}
    Remote["Stream from Shared PFS / Object Store<br/>Check: Link util, OST queue, MDS ops/s"]
    Local["Read from Local NVMe Cache (/raid)<br/>Check: NVMe GB/s, hit rate, CPU decode"]
    GoodShared["Link < 50% used & GPU util >= 95%<br/>Keep streaming directly (simpler)"]
    NeedStage["Link >= 80% used OR multi-epoch reuse<br/>Stage to /raid (target > 95% hit Ep 2)"]
    GoodLocal["Cache hit > 95% & NVMe > 2.0 GB/s<br/>Epoch runs at local PCIe speed"]
    BadLocal["NVMe < 500 MB/s despite cache hits<br/>Debug NUMA affinity or CPU transforms"]

    Start --> Q1
    Q1 -->|"Yes (Cold / Too Large)"| Remote
    Q1 -->|"No (Warm & Fits)"| Local
    Remote -->|"Healthy"| GoodShared
    Remote -->|"Bottlenecked"| NeedStage
    Local -->|"Fast"| GoodLocal
    Local -->|"Slow"| BadLocal
```

The table turns the flowchart into thresholds you can check on a live node. Each row pairs a metric with the action it triggers. Read the first two rows together, because the streaming path has two outcomes, depending on whether the shared link has headroom. Headroom is the spare capacity left on the link before it becomes the limit.

| Decision Node | Observed Metric Threshold | Action Taken |
|---|---|---|
| **Shared Storage Stream (`Remote`)** | Shared link `< 50%` utilized (`< 60%` ceiling), no I/O stalls | Bypass local staging; stream directly from Lustre / BeeGFS / WekaFS to keep job startup stateless. |
| **Shared Storage Bottleneck (`NeedStage`)** | Shared link `>= 80%` utilized, `MDS` `stat` storm, or `>= 2` epochs with `NVMe / Shared > 2.0x` | Stage dataset shards into `/raid/job_$SLURM_JOB_ID` during Epoch 1 (or via `s5cmd` pre-stage) and verify `> 95%` cache hit rate by Epoch 2. |
| **Warm Local NVMe (`GoodLocal`)** | Cache hit rate `> 95%` (`97.8%–98.3%`), local throughput `> 1.0–3.5 GB/s` | Retain local NVMe cache; monitor `/raid` fill level (`<= 85%`) and `nvme smart-log` health. |
| **Local Path Bottleneck (`BadLocal`)** | `fio` shows 3.5 GB/s, but training sees `< 500 MB/s` (150 MB/s) | Bottleneck is outside the SSD: bind `DataLoader` workers to the NVMe NUMA socket (`numactl`) or offload CPU JPEG/tokenization transforms (DALI). |

Before you build staging logic into a pipeline, measure the shared-link utilization and the epoch count. If both are low, streaming directly is simpler and just as fast. Simpler code also has fewer ways to fail in the middle of the night, which is a good reason to choose it when the numbers allow.

---

## 2. Two-tier node NVMe architecture and RAID 0 stripe geometry

Imagine a node that reboots after a kernel update, and the training job vanishes with it. Which disks survive that reboot? Every modern NVIDIA system keeps two local NVMe tiers strictly apart, because the answer must be different for each. The first tier holds the operating system, and it must survive a reboot. The second tier holds ephemeral training scratch, which does not have to. Chapter 9.2 covers the DGX H100 and H200 layout, and Chapter 9.5 covers the DGX GB200 and GB300 NVL72 compute tray. This section explains why the split exists and how to size and align it.

Two tiers means two jobs. The first tier must survive a reboot, and the second may be erased without lasting harm. The subsection below shows the drives for each tier and the RAID choice behind them.

### 2.1 The two-tier physical layout: OS RAID 1 vs `/raid` RAID 0 scratch

Picture a DGX node that has been training for a month when one of its two boot drives starts throwing errors. The first tier holds the operating system and container root, and it must not be ephemeral. On a DGX H100 or H200, two 1.92 TB M.2 NVMe drives mirror each other in RAID 1. That gives 1.92 TB of usable space, mounted at `/`. Suppose one M.2 drive fails during a month-long training run. The node keeps running and never drops its GPUs from the job. A mirror tolerates the loss of one drive, and the replacement can be rebuilt later. A DGX GB200 or GB300 NVL72 compute tray uses a single 1.92 TB M.2 drive for the same purpose, so it has no mirror to fall back on.

The second tier is ephemeral scratch for staging data. It is built for speed rather than durability. A DGX H100 or H200 stripes eight 3.84 TB U.2 drives together in software RAID 0, mounted at `/raid`, for 30.72 TB of usable space. Two drives sit behind each of the node's four PCIe Gen5 switches, next to two GPUs and two network cards. That layout delivers about 50.0 GB per second of sequential read bandwidth and 28.0 GB per second of write bandwidth. Sequential means the reads run one after another through the file. A GB200 or GB300 compute tray stripes four 3.84 TB E1.S drives the same way. That gives 15.36 TB per tray, which scales to 276.48 TB across an eighteen-tray rack.

RAID 0 makes sense here because `/raid` never holds the only copy of anything. Every dataset cached there has a golden copy on shared storage. Every checkpoint staged there gets flushed to durable storage right away. Parity RAID would waste 12.5 to 25 percent of capacity. Parity is extra information that lets an array rebuild a lost drive, and it has to be written with every change. It would also add read-modify-write latency during checkpoint bursts, and complicate direct GPU-to-storage DMA. Read-modify-write means the array must read old data and parity before it can write new parity, which slows small writes.

```mermaid
flowchart LR
    subgraph Node["AI Compute Node Two-Tier Local NVMe Architecture"]
        direction TB
        subgraph Tier1["Tier 1: OS & System Mirror (Non-Ephemeral)"]
            M2["DGX H100/H200: 2x 1.92 TB M.2 (RAID 1 = 1.92 TB)<br/>GB200/GB300 Tray: 1x 1.92 TB M.2 OS Boot"]
            RootFS["Mounted at / (Root FS, Logs, System Daemons)<br/>Protected from user job I/O & wear"]
            M2 --> RootFS
        end
        subgraph Tier2["Tier 2: High-Bandwidth Ephemeral Scratch (/raid)"]
            U2["DGX H100/H200: 8x 3.84 TB U.2 (30.72 TB, ~50 GB/s)<br/>GB200/GB300 Tray: 4x 3.84 TB E1.S (15.36 TB/tray)"]
            MD0["Linux mdadm RAID 0 (/dev/md0)<br/>Chunk = 256 KB or 512 KB, XFS noatime"]
            Scratch["Mounted at /raid/job_$SLURM_JOB_ID<br/>Dataset Shards, Container Rootfs, Async Checkpoints"]
            U2 --> MD0 --> Scratch
        end
    end
    PFS["Shared PFS / Object Store<br/>(Lustre / BeeGFS / WekaFS / S3)"]
    GPU["Node GPUs (HBM3 / HBM3e)<br/>via Page Cache / Pinned RAM or GDS"]

    PFS -->|"1. Pre-Stage (s5cmd) or Epoch 1 Cache Fill"| Scratch
    Scratch -->|"2. Epochs 2..N Local Read (3.5-50 GB/s)"| GPU
    GPU -->|"3. Fast Async Checkpoint Dump (<1s ack)"| Scratch
    Scratch -->|"4. Background Flush Thread (1.2 GB/s)"| PFS
```

The table puts the two tiers side by side for each platform. Read down the Tier 1 rows and you will see the OS drives trade speed for redundancy. The Tier 2 rows show the reverse trade. Keep that pattern in mind, because it explains almost every choice in the layout.

| Platform & NVMe Tier | Physical Drives & Form Factor | RAID Configuration | Raw / Usable Capacity | Peak Sequential Read / Write | Primary Operational Role |
|---|---|---|---|---|---|
| **DGX H100 / H200 — Tier 1 (OS)** | `2 × 1.92 TB` M.2 NVMe | Hardware RAID 1 | 3.84 TB raw / 1.92 TB usable | ~3.2 GB/s R / ~2.6 GB/s W | DGX OS boot, kernel, system logs; isolated from job wear |
| **DGX H100 / H200 — Tier 2 (`/raid`)** | `8 × 3.84 TB` U.2 NVMe (2 per PCIe Gen5 switch) | Software RAID 0 (`/dev/md0`) | 30.72 TB raw / 30.72 TB usable | ~50.0 GB/s R / ~28.0 GB/s W | Ephemeral dataset cache, shards, async checkpoints |
| **GB200 / GB300 Tray — Tier 1 (OS)** | `1 × 1.92 TB` M.2 NVMe | Single boot drive | 1.92 TB raw / 1.92 TB usable | ~3.2 GB/s R / ~2.6 GB/s W | 1U compute tray Linux OS boot (144 Grace Arm cores + 4 GPUs) |
| **GB200 / GB300 Tray — Tier 2 (`/raid`)** | `4 × 3.84 TB` E1.S (EDSFF) NVMe (72 drives/rack) | Software RAID 0 (`/dev/md0`) | 15.36 TB/tray (276.48 TB/rack) | ~25.0 GB/s R / ~14.0 GB/s W | Rack-distributed shard caching & checkpoint staging |

The table above tells you which flag to use. It does not tell you why the flag matters, so the next part works through the arithmetic that sits behind it. Once you see how one read maps onto the drives, the flag values stop looking like magic numbers.

### 2.2 `mdadm` RAID 0 chunk size and XFS stripe alignment math

Picture a new eight-drive scratch array that benchmarks well on one large file and then slows to a crawl under a real data loader. Striping several NVMe drives into one `mdadm` RAID 0 array raises a practical question. When your program reads or writes, does the request hit all the drives in parallel, or just one? Two geometry values answer that question. `mdadm` is the Linux tool that builds software RAID arrays, and the geometry is how the array divides data across its drives.

The chunk size is the amount of data written to one drive before the array moves to the next drive in the stripe. Think of a deck of cards dealt around a table, where each player receives one chunk before the next player gets a turn. AI training reads and writes mostly in 1 MB to 4 MB blocks. That is why a chunk size of 256 KB or 512 KB works well, because a block then spans several drives.

The full stripe width is the amount of data needed to touch every drive exactly once. You get it by multiplying the drive count by the chunk size. The formula is short, and the example below applies it to the DGX H100 array:

```text
W_stripe = N x C
On 8-drive DGX H100 with 512 KB chunk: W_stripe = 8 x 512 KB = 4096 KB = 4.0 MB
```

Work through the eight-drive DGX H100 array with a 512 KB chunk. Its full stripe is 4.0 MB. An aligned 4.0 MB read splits into eight parallel 512 KB requests, one per drive, so it uses 100 percent of the array. An unaligned 64 KB read fits inside one chunk, so it touches only one drive. That uses just 12.5 percent of the array. To reach full speed with small reads, you need enough concurrent requests in flight across your workers to keep every drive busy at once. A single small read cannot do that alone.

To keep the filesystem from splitting files across chunk boundaries, pass the RAID geometry to `mkfs.xfs` in units of the 4 KiB filesystem block. XFS is the filesystem used on `/raid`, and `mkfs.xfs` is the command that formats it. The two values below describe the stripe unit and the stripe width in those block units:

```text
sunit (or stride) = C / B_fs
swidth (or stripe-width) = N x sunit = (N x C) / B_fs
```

The table below gives the resulting alignment flags for each node type covered in this chapter. Each row pairs an array profile with the exact flag to format it. The drive count and the chunk size decide the flag, so a row that does not match your hardware should not be copied.

| RAID 0 Array Profile | Drives ($N$) | Chunk Size ($C$) | Full Stripe (`W_stripe`) | XFS `sunit` (`4 KiB` blocks) | XFS `swidth` (`4 KiB` blocks) | Exact `mkfs.xfs` Alignment Flag |
|---|---|---|---|---|---|---|
| **DGX H100 / H200 U.2 `/raid`** | 8 | 512 KB | 4096 KB (4.0 MB) | 128 | 1024 | `mkfs.xfs -f -d su=512k,sw=8 /dev/md0` |
| **DGX H100 / H200 U.2 `/raid` (alt)** | 8 | 256 KB | 2048 KB (2.0 MB) | 64 | 512 | `mkfs.xfs -f -d su=256k,sw=8 /dev/md0` |
| **GB200 / GB300 Tray E1.S `/raid`** | 4 | 256 KB | 1024 KB (1.0 MB) | 64 | 256 | `mkfs.xfs -f -d su=256k,sw=4 /dev/md0` |

Copy the flag that matches your drive count and chunk size. Do not guess at alignment values, because a wrong value does not fail loudly. It just makes every read and write slower.

Before formatting any local scratch array, match the XFS stripe unit and stripe width to your `mdadm` chunk size and drive count. Formatting is the one step you cannot easily undo, so check the numbers before you run the command.

---

Section 2 answered where the drives sit and how the array is built. The next question is whether a local copy is worth making in the first place. The answer depends on how many times the same bytes get read, and on how long the copy takes compared with the time it saves.

## 3. Data staging economics: multi-epoch break-even and checkpoint staging math

Picture a team that wants to copy a dataset onto local disks before a long run, and a manager who asks whether that copy is worth the wait. Local NVMe staging is a trade. You pay an upfront copy cost, and in return each epoch or checkpoint runs faster. The question is whether the return beats the cost. The sections below answer it with arithmetic, and each case starts from a concrete situation.

The arithmetic in this subsection uses the same 500 GB dataset and the same node from the earlier sections. Follow the steps in order, because each result feeds the next one.

### 3.1 Multi-epoch dataset staging: worked cluster calculation and break-even formula

Picture the eight-node, 256-GPU cluster from earlier. It trains on a 500 GB dataset split into two million small files, and each node has 2 TB of free local NVMe. This is the kind of setup a team faces on a Monday morning, when the first run has to finish before the weekend.

Streaming straight from shared Lustre every epoch is slow for the reasons already covered. Each epoch pays the metadata overhead again, because the shared filesystem has to look up millions of small files every time. That drops delivered throughput to about 110 MB per second per GPU. A cold epoch therefore takes 245 seconds, and the GPUs spend most of that time waiting.

Caching the dataset on local NVMe changes every epoch after the first. Think of the first epoch as the cost of filling the cache, and every later epoch as the return. Once the data lives on `/raid`, the data loader reads it back at 3.5 GB per second sustained. That is about 1.75 GB per second for each GPU, comfortably above the 120 MB per second each GPU needs. Epoch time drops from 245 seconds to 200 seconds. That saves 45 seconds per epoch, an 18 percent speedup. Over a ten-epoch run, inline caching saves 405 seconds in total, which cuts run time by about 16.5 percent.

There are two ways to get the data onto `/raid`, and the choice changes when the savings arrive:

- Pattern A, inline cache fill: The data loader reads from Lustre as usual during the first epoch, and it also writes a copy to `/raid` as it goes. That first epoch still takes the full 245 seconds, so you pay the whole cost up front. Every epoch after it runs at the cached 200-second pace, so the savings start on the second epoch.
- Pattern B, explicit pre-stage: A tool like `s5cmd`, parallel `rsync`, or `mpifileutils` copies the dataset to `/raid` before training starts. The copy runs as a separate step, so the job does not start reading until it finishes. A Slurm Prolog step, which is a script that runs before the job starts, typically runs that copy.

Suppose the explicit copy runs at 2.0 GB per second. The arithmetic below gives two numbers: the time the copy takes, and the epoch count at which the copy finally pays for itself. Break-even means the point where the time saved equals the time spent copying.

```text
T_copy = D_GB / B_stage = 500 GB / 2.0 GB/s = 250 seconds
N_be   = T_copy / (T_remote - T_local) = 250 s / 45 s ~= 5.56 epochs (rounds up to 6 epochs)
Pattern A (10 epochs): 2,450 s uncached vs 2,045 s cached = 405 s saved (16.53% speedup)
Pattern B (3 epochs):  850 s pre-staged vs 735 s uncached = 115 s lost
Pattern B (6 epochs):  1,450 s pre-staged vs 1,470 s uncached = 20 s saved (44,750 s / 12.4 h saved over 1,000 epochs)
```

Pre-staging a run shorter than six epochs makes the job slower, not faster. That is the break-even point. Take the three-epoch fine-tuning run first. Fine-tuning means training a pretrained model further on a smaller dataset. Pre-staging it costs 115 seconds. A six-epoch run, by contrast, comes out 20 seconds ahead. The gap is small for any one run, but over long training runs that per-epoch saving adds up to hours of recovered GPU time.

Before you pre-stage a dataset, count how many epochs the job will actually run. Read that number from the job's config, not from the plan in your head, because a restart can change it. Then compare that number to the break-even point.

Break-even math assumes the cache stays healthy for the whole run. The next subsection covers the two things that break that assumption. One is a cache that fills up and starts evicting. The other is a cache that quietly holds old data.

### 3.2 Cache hit rate progression, the 85% fill-level cliff, and SHA-256 manifest validation

Picture a cache that looked healthy in the first epoch and then quietly served the wrong data later in the run. Two bugs can quietly ruin a cached dataset, even when the break-even math looks good.

The first is eviction thrashing past 85 percent fill. Eviction means the cache throws out a shard to make room for another one. Look at a cache that hits 98.3 percent on the second epoch, then slips to 96.1 percent by the fourth. That slow decline is not random noise. It means `/raid` has crossed 85 percent full and started evicting and garbage-collecting shards in the middle of the run. Keep the cached working set under 85 percent of usable `/raid` capacity. On a 30.72 TB DGX H100 array, that ceiling is 26.11 TB. If a dataset is bigger than that, shard it across nodes instead. For example, split a 100 TB dataset across ten nodes so that each one caches 10 TB. Each node then holds only its own slice, and that slice fits comfortably.

```text
Cache Hit Progression & Safe Capacity Ceiling:
  - Epoch 1 (cold fill): 0.2% hit rate -> Epoch 2: 98.3% -> Epoch 3: 97.8% -> Epoch 4 (thrashing >85% fill): 96.1%
  - DGX H100 85% safe ceiling: 0.85 x 30.72 TB = 26.11 TB (26,112 GB out of 30,720 GB)
```

The second bug is silent staleness. Think of a cache as a shelf of labeled boxes. If someone swaps the contents of a box and leaves the old label on it, nobody notices until a result looks wrong. Suppose an upstream pipeline updates a shard on shared storage. A node's `/raid` cache still holds last week's copy under the same filename. Training then quietly mixes old and new data across nodes, and no error is raised. A SHA-256 hash is a fingerprint of the file contents, so two files with the same name but different contents get different fingerprints. The fix is to store a SHA-256 hash and byte size for every cached file in a `manifest.json`. Then check that hash before you trust a cache hit.

The two bugs above are about trusting a cache. The checkpoint path has a different problem, which is that every GPU waits while a write finishes. The next subsection shows how large that wait is and how a background thread removes it.

### 3.3 Asynchronous two-phase checkpoint staging

Picture a single-epoch job that reads its data once and then spends its time saving checkpoints. A single-epoch job never benefits from dataset caching, because nothing is read twice. It still needs `/raid` for one thing, though. Checkpoint writes can move off the GPU's critical path.

A synchronous write means the training loop waits until the bytes are safely on disk. A synchronous write of a 500 GB checkpoint to shared Lustre at 1.2 GB per second stalls the job. The arithmetic below shows how long, and it also shows what the local path would cost:

```text
T_sync  = 500 GB / 1.2 GB/s = 416.67 seconds (~417 seconds, ~7 minutes at 0% GPU compute)
T_local = 500 GB / 3.5 GB/s = 142.86 seconds (~143 seconds background local write)
T_async = 1.0 second handoff -> 416.67x (~417x) critical-path speedup
```

During a synchronous write, every GPU in the job sits idle, waiting on disk. Two-phase local staging removes most of that wait. It splits the write into two steps, and only the first step blocks the GPUs:

1. Phase 1, host memory to `/raid`: A background thread copies the checkpoint from pinned host memory to `/raid` at 3.5 GB per second. Pinned host memory is page-locked RAM that the GPU copy engine can read directly. The training loop waits only about one second for the memory handoff to start, then it resumes. That is a 417x speedup on the critical path.
2. Phase 2, `/raid` to shared Lustre: Once the local file closes, a separate background thread copies it to shared Lustre at 1.2 GB per second. Nothing in training waits for this copy. The thread deletes the local copy with `os.remove` as soon as that flush finishes. That keeps `/raid` from filling up across checkpoints.

Before you add a synchronous checkpoint write to a training loop, ask whether a background flush thread could do the same work without stalling the GPUs. If the answer is yes, the flush thread is the safer design, because the GPUs never wait on the slow disk.

---

Staging decides which data sits on the local drives. Tuning decides whether those drives deliver what the hardware promises. A fast drive behind a poor queue setting can still look slow to the training job, so the next section covers the Linux settings that matter most.

## 4. Tuning the Linux NVMe and filesystem stack for GPU pipelines

Picture a `/raid` array that wins every benchmark and still leaves the GPUs waiting. A `/raid` array can be fast on paper and still feed the GPUs too slowly. The usual reason is the stock Linux install. Its block devices are tuned for general-purpose virtual machines and databases, not for multi-gigabyte-per-second GPU pipelines. A block device is the kernel's view of a drive, and the block layer is the code that queues requests for it. Getting full bandwidth out of `/raid` means adjusting four layers of the host stack.

This section has two parts. The first covers the block layer and its three queue settings. The second covers the filesystem and the data loader above it, where the last bit of throughput is either won or lost.

### 4.1 `blk-mq` scheduler (`none` vs `mq-deadline`), queue depth (`nr_requests`), and `read_ahead_kb`

Picture a shard reader that is fast in a single-threaded test and slow once many workers run at the same time. Modern Linux sends NVMe I/O through a multi-queue block layer. It maps one submission queue per CPU core directly onto the NVMe hardware queues. A submission queue is the list of requests a CPU core hands to the drive. The older design funneled every request through one lock-contended queue, which is how legacy SATA drives worked. A lock-contended queue makes every core wait at the same lock, so the cores fight over one door. SATA is the older disk interface that NVMe replaced.

Three settings matter most, and each one controls a different part of that queue:

- I/O scheduler (`/sys/block/nvmeXn1/queue/scheduler`): Set it to `none`, which sends requests straight to the hardware with minimal overhead. A scheduler decides the order in which queued requests go out. Choose `mq-deadline` instead if mixed read and write checkpoint traffic needs bounded write latency, meaning a write has a firm limit on how long it can wait. Fairness schedulers like `bfq` add CPU spinlock overhead that NVMe does not need. A spinlock is a lock that a CPU core spins on while it waits, so the extra bookkeeping burns CPU time for no gain on fast drives.
- Queue depth (`nr_requests`): Raise it to at least 512, ideally 1023. Queue depth is how many requests can wait at the drive at once. Parallel data loader workers with deep prefetch queues can then keep the array saturated, because each worker keeps requests lined up.
- Read-ahead (`read_ahead_kb` and `blockdev --setra`): The Linux default is just 128 KB. Read-ahead is how far the kernel fetches past the bytes you asked for. At 128 KB, it triggers far too many small I/O cycles when you stream large shard files. Raising it to 4096 KB matches a full eight-drive RAID 0 stripe, and it lets prefetch run across every drive in the array.

There is one exception. Pure random `O_DIRECT` workloads bypass the page cache entirely. GPUDirect Storage reads and DeepSeek's 3FS filesystem are examples. Read the exception carefully, because the rule is about the access pattern, not the drive. If the reads are random and skip the page cache, extra read-ahead only fetches data that will never be used. For these, keep read-ahead at 128 KB or lower, so the kernel does not fetch pages nobody will use. DeepSeek's 3FS applies the same design at cluster scale. It sustains 6.6 TB per second and peaks at 7.3 TB per second across a 68-node NVMe cluster.

The block layer decides how requests reach the drive. The filesystem and the data loader decide whether those requests come back fast enough to matter. The next subsection walks through the mount flags, the small-file problem, and the loader settings in that order.

### 4.2 Filesystem selection (XFS with `noatime`), `io_uring`, and `DataLoader` / GDS integration

Picture a loader whose disks are tuned well, while its CPU cores sit at full load and the GPUs still wait. Three more settings sit above the block layer. They decide whether that raw throughput actually reaches the GPU.

To start, you should mount `/raid` with `noatime`. Every file has an access time, and by default a read updates it, which means a write to disk. Without `noatime`, every read during training writes metadata back to disk, just to update the file's last-access timestamp. That turns a pure read workload into a mixed read-write one, and it gains you nothing.

Pack the small files before training starts. Each small file costs a trip through the filesystem, so a million small files read one at a time cost an order of magnitude more than the same data read as contiguous 1 MB chunks. An order of magnitude means roughly ten times. Tools like NVIDIA NeMo Curator or WebDataset should combine them into shards offline instead, which is the same packing idea from the previous chapter. When random reads are unavoidable, use `io_uring` with pre-registered buffers, rather than one `pread()` call per file. `io_uring` is a Linux interface that lets a program submit many reads in one batch, and pre-registered buffers skip some per-call setup.

Tune the PyTorch `DataLoader` itself, because it sits between the disk and the GPU. Set `num_workers=8`, `pin_memory=True`, and `persistent_workers=True`, so workers do not respawn at every epoch boundary. Set `prefetch_factor=4`, so the next batch transfers while the GPU computes. Profile with `num_workers=0` first, which isolates pure Python and storage latency. Then check the copy lane in Nsight Systems to see transfer time separately. Cutting GPU I/O wait from 30 percent of each step down to 5 percent improves step time accordingly. Change one setting at a time, so you know which one helped.

If CPU cores are pegged decoding JPEGs across eight cores, offload the decode to the GPU with NVIDIA DALI. JPEG decoding is the CPU-heavy work that turns compressed photos into pixels, and DALI is NVIDIA's data-loading library that can run that work on the GPU. That typically drops CPU usage to two cores. Or store compressed batches, and let Blackwell's hardware Decompression Engine unpack them in the pipeline over its 900 GB per second NVLink-C2C link.

The fastest option skips the CPU entirely. GPUDirect Storage pulls data straight from `/raid` into GPU memory over the local PCIe switch. Benchmarks with `gdsio` show this path reaching 9.6 GB per second at 1.00 ms latency. The host-memory path reaches 8.0 GB per second at 1.25 ms. That is a 20 percent improvement in both throughput and latency. This path only helps if the filesystem and the driver support it, which is why the compatibility check from the previous chapter matters here too. Check the `gdsio` result against your own node before you count on it.

Before you blame the SSDs for a slow training loop, check three things in order: the filesystem mount flags, the read-ahead setting, and the CPU decode threads. Those checks are quick to run, and each change can be undone.

---

Section 4 tuned the stack. Section 5 checks the result. It asks whether the drives meet their numbers under the access patterns that training really produces, whether wear will shorten their life, and whether cleanup happens without a human remembering to do it.

## 5. Benchmarking local NVMe vs shared storage, SMART endurance, and Slurm lifecycle

Picture a job that will run for weeks on a node that was set up in an afternoon. A `/raid` volume deserves a few checks before you trust it with a multi-week job. Benchmark it under the access patterns that training really produces. Confirm that checkpoint traffic will not wear the drives out early. And make sure cleanup between jobs happens automatically.

### 5.1 The four AI storage benchmark profiles (`fio` and `dd` baseline vs shared PFS)

Picture a datasheet that promises one fast number and a training team that sees a slow first epoch. A single sequential-read number on a datasheet never tells the whole story. Production benchmarks cover four access patterns, and each one mirrors a real training phase: loading a model once, streaming batches continuously, reading randomly or hammering metadata, and bursting checkpoint writes. The table lists each profile with its expected baseline on local NVMe and on a shared PFS. A PFS is a parallel filesystem, which spreads one dataset across many storage servers.

| Workload Profile | Access Pattern | Representative File / I/O Size | Block Size (`bs`) | Concurrency | Expected Local NVMe Baseline | Expected Shared PFS Baseline |
|---|---|---|---|---|---|---|
| **1. Model Load** | Large sequential read once per job/epoch | 10 GB–100 GB | 1 MB | 1 job, `O_DIRECT` | **3.5 GB/s** | **`1.5–3.0 GB/s`** |
| **2. Batch Stream** | Parallel medium-block streaming reads | 1 GB (`1,000 × 1 MB`) | 64 KB | 8 jobs, `iodepth=16` | **2.8 GB/s** | **`3.0–5.0 GB/s`** aggregate |
| **3. Random Read / Metadata Storm** | 4 MB random reads OR small-file `stat`/`open` storm | 10 GB or `10K–1M` 100 KB files | 4 MB or 4 KB | 1 job (`iodepth=32`) or 16 metadata workers | **1.2 GB/s**; **`50K+` ops/s** local metadata | **`1K–5K` ops/sec** on shared `MDS` |
| **4. Checkpoint Burst** | Concurrent sequential write burst across ranks | 500 MB per rank | 4 MB | 1–8 ranks, `iodepth=16` | **`2.1–3.5 GB/s`** per writer | **1.2 GB/s** shared write rate |

Three rules of thumb come out of these numbers. The first compares speeds: divide the local throughput by the shared throughput on the model-load test. If local NVMe beats shared storage by more than 2x, local caching and async checkpoint staging are worth doing. Suppose you measure 3.5 GB per second on NVMe and 1.5 GB per second on shared storage. A tenfold gap means staging saves 90 percent of the synchronous wait.

The second rule is about small files. If shared metadata throughput falls under 10,000 operations per second when you open thousands or millions of small files, repackage those files into roughly 10,000 contiguous shards before staging them. Repackaging first means the copy moves a few large files instead of millions of tiny ones.

The third rule is a warning about blame. If `fio` reports 3.5 GB per second on `/raid` but training only sees 150 MB per second, the SSDs are not the problem. The bottleneck lies elsewhere, usually in NUMA placement or in single-threaded Python decoding. NUMA placement means which CPU socket the loader runs on, relative to the drive it reads from.

The benchmark numbers tell you how fast the drives can go. They do not tell you how long the drives will last under your writes. The next subsection turns checkpoint traffic into a wear budget that you can check against the drive's rating.

### 5.2 NVMe endurance math (DWPD, TBW, WAF) and SMART health monitoring

Picture a node whose drives look healthy on the day it is installed, and then a year later one of them starts reporting wear. Dataset caching is mostly reads. Aggressive checkpoint staging, though, can write tens of terabytes a day to `/raid`. NAND flash, the storage cell that SSDs use, wears out after a finite number of program and erase cycles, which are the write and clear cycles each cell goes through. Enterprise NVMe drives are therefore rated in Drive Writes Per Day, or DWPD, which is how many full drive writes the drive can take each day, over a five-year warranty. A rating of 1.0 DWPD suits dataset caching and moderate checkpointing. A rating of 3.0 DWPD suits heavier, continuous checkpoint traffic.

Two more terms make the budget concrete. TBW is the total terabytes written budget over the life of the drive. WAF, the Write Amplification Factor, is the ratio of data the drive actually writes to the data the host sent, because the controller rewrites some blocks to manage the flash. The formulas are computed as follows:

```text
TBW = S_TB x DWPD_rated x 365 x Y
Single 3.84 TB drive (1.0 DWPD, 5 yr / 1,825 days): 3.84 x 1.0 x 365 x 5 = 7,008.0 TB (~7 PB; 8-drive array = 56,064 TB / 56.06 PB)
W_NAND,daily = W_host,daily x WAF
Effective DWPD = W_NAND,daily / S_TB
L_years = TBW / (W_NAND,daily x 365)
Healthy case (2.5 TB/day host, WAF 1.2):   3.0 TB/day NAND -> 0.7812 DWPD -> 6.40 years lifespan
Unhealthy case (12.0 TB/day host, WAF 1.5, 92% full): 18.0 TB/day NAND -> 4.6875 DWPD -> 1.07 years lifespan
```

Take the healthy case first, since it is the one you hope to see. A host writes 2.5 TB per day with aligned 4 MB checkpoint writes, and the WAF is 1.2. The NAND then sees 3.0 TB per day, or about 0.78 effective DWPD. That gives an estimated 6.4-year lifespan, which outlasts the five-year warranty.

Now take the unhealthy case. A job hammers a 92 percent-full drive with unaligned small writes. Unaligned writes do not line up with the stripe, so the drive does extra work on each one. The host writes 12.0 TB per day, with a WAF of 1.5. NAND writes jump to 18.0 TB per day. That uses up the drive's lifetime budget in just 1.07 years.

Watch four counters on every drive. SMART is the self-monitoring data that drives report about their own health. Read them with `nvme smart-log` and `smartctl`:
- `percentage_used` is the share of the drive's rated life already used. Alert at 90 percent or higher, and schedule replacement.
- `available_spare` is the reserve of spare capacity the drive keeps for swapping out bad blocks. Drain the node immediately at 10 percent or below.
- `temperature` should stay in its normal range. The normal range is 35 to 55 degrees Celsius. At 70 degrees Celsius or higher, or 343 Kelvin, the controller throttles throughput by 30 to 70 percent.
- `media_errors` counts unreadable blocks. It must stay at zero, since RAID 0 has no parity to recover a bad sector.

Wear is slow, but a full disk is fast. A single leftover directory can take a node out of service in one afternoon, so the next subsection covers the cleanup rules that prevent that. Those rules live in the scheduler, not in anyone's memory.

### 5.3 Multi-tenant Slurm Prolog and Epilog lifecycle for `/raid`

Picture a Monday morning when every new job on one node fails at startup with a full disk. Hardcoded paths such as `/raid/my_dataset` cause trouble. A hardcoded path is a directory name typed into the script, and it stays the same no matter which job runs. A crashed or killed job eventually leaves orphaned files behind. An orphan is a leftover file or folder that no running job owns. Those orphans silently fill `/raid` to 100 percent, and then they break every job scheduled on that node afterward.

The fix is to put scratch lifecycle management in root-owned Slurm hooks, not in the user's own script. Root-owned means only system administrators can change the hook, so a user cannot skip it by accident:

1. Prolog runs before the job starts. It sweeps any orphaned job directories left by previous jobs. Next, it checks that the new job's request fits within an 85 percent safe capacity ceiling, or 26,112 GB on a 30,720 GB array. Then it creates a fresh `/raid/job_$SLURM_JOB_ID` directory owned by the job's user. The Prolog runs as root, so the sweep can remove leftovers that the user's account could not.
2. Epilog runs after the job ends, whether it finished normally or was killed. It waits for any background checkpoint flush to finish, so the flush is not cut off halfway. Then it deletes the job's scratch directory and runs `fstrim`, so the NVMe controller can reclaim free blocks. TRIM, which `fstrim` triggers, tells the drive that deleted blocks are free to erase.
2. Epilog runs after the job ends, whether it finished normally or was killed. It waits for any background checkpoint flush to finish. Then it deletes the job's scratch directory and runs `fstrim`, so the NVMe controller can reclaim free blocks.

Put cleanup in Prolog and Epilog, not in the training script itself. A `SIGKILL` from an out-of-memory event or a wall-clock timeout skips Python's cleanup handlers entirely. A kill signal is not a request the program can refuse, so any cleanup written inside the program never runs. The hooks run outside the job, so they still run when the job does not.

---

Picture a scratch node that has just been racked, with blank drives and a clean install. The commands below walk through the setup in order, from inspecting the drives to tuning the block layer. None of them has been run on live hardware in this repository, so treat them as a checklist for a node you can rebuild.

## Commands and configurations that matter

Run these in order on a scratch node you can rebuild. The first block only inspects the drives, so it is safe to run anywhere. The later blocks create the array, so they erase whatever is on those drives.

### 1. Provisioning an Aligned `mdadm` RAID 0 `/raid` Volume and Tuning `blk-mq`

```bash
# 1. Inspect the two NVMe tiers (2x 1.92 TB M.2 OS RAID 1 vs 8x 3.84 TB U.2 scratch) (untested here)
lsblk -o NAME,MODEL,SIZE,TYPE,FSTYPE,MOUNTPOINT | grep -E "nvme|md"
nvme list

# 2. Create an 8-drive RAID 0 array with a 512 KB chunk size (4.0 MB full stripe) (untested here)
mdadm --create /dev/md0 --level=0 --raid-devices=8 --chunk=512 \
  /dev/nvme{0,1,2,3,4,5,6,7}n1

# 3. Format XFS aligned to chunk=512k and 8 drives (sunit=128, swidth=1024 4KiB blocks) (untested here)
mkfs.xfs -f -d su=512k,sw=8 -l su=256k,version=2 /dev/md0

# 4. Mount /raid with noatime,nodiratime to eliminate per-read inode atime writes (untested here)
mkdir -p /raid
mount -o defaults,noatime,nodiratime,logbufs=8,logbsize=256k /dev/md0 /raid
df -h /raid

# 5. Tune Linux blk-mq scheduler (none), queue depth (1023), and read-ahead (4096 KB = 8192 sectors) (untested here)
for dev in /sys/block/nvme*n1; do
  echo none > "${dev}/queue/scheduler"
  echo 1023 > "${dev}/queue/nr_requests"
  echo 4096 > "${dev}/queue/read_ahead_kb"
done
blockdev --setra 8192 /dev/md0
```

The four workload blocks match the four profiles in the benchmark table. Run each one on its own, and record the result beside the expected baseline. The `gdsio` pair at the end repeats the comparison from the previous chapter.

### 2. Benchmarking Local NVMe vs Shared Storage (`fio` and `gdsio`)

```bash
# Workload 1: Model Load (10 GB sequential read, 1 MB blocks, O_DIRECT) (untested here)
dd if=/dev/zero bs=1M count=10000 of=/raid/model-test.bin oflag=direct
time dd if=/raid/model-test.bin bs=1M count=10000 of=/dev/null iflag=direct

# Workload 2: Batch Streaming (64 KB blocks, 8 parallel jobs, iodepth=16) (untested here)
fio --name=batch-stream --ioengine=libaio --rw=read --bs=64k --size=1G \
    --direct=1 --iodepth=16 --numjobs=8 --filename=/raid/batch-test.bin

# Workload 3: Random Read (4 MB blocks, iodepth=32) (untested here)
fio --name=random-read --ioengine=libaio --rw=randread --bs=4M --size=10G \
    --direct=1 --iodepth=32 --numjobs=1 --filename=/raid/random-test.bin

# Workload 4: Checkpoint Burst Write (4 MB blocks, 500 MB per rank) (untested here)
fio --name=checkpoint-write --ioengine=libaio --rw=write --bs=4M --size=500M \
    --direct=1 --iodepth=16 --numjobs=1 --filename=/raid/checkpoint-test.bin

# Compare CPU-mediated (-x 2: 8.0 GB/s, 1.25 ms) vs GPUDirect Storage (-x 0: 9.6 GB/s, 1.00 ms) (untested here)
/usr/local/cuda/gds/tools/gdsio -f /raid/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 2
/usr/local/cuda/gds/tools/gdsio -f /raid/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 0
```

These checks cover wear, integrity, and cleanup. Run the SMART loop on a schedule, not only when something breaks. The Python block is the cache logic from section 3, and the Slurm hooks are the cleanup from section 5.

### 3. Checking NVMe SMART Health, Checksum Manifests, Async Checkpointing, and Slurm Hooks

```bash
# Inspect SMART wear-leveling (percentage_used, available_spare), temperature, and media_errors (untested here)
for i in {0..7}; do
  echo "=== /dev/nvme${i}n1 ==="
  nvme smart-log "/dev/nvme${i}n1" | egrep "temperature|available_spare|percentage_used|media_errors"
  smartctl -a "/dev/nvme${i}n1" | egrep -i "Temperature|Spare|Percentage|Media|Firmware"
done
iostat -xz 1 5
```

```python
# Asynchronous two-phase checkpoint staging + SHA-256 cache validation (from V15 Ch 3)
import hashlib
import json
import os
import shutil
import threading


def compute_file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def cache_fetch_with_validation(shared_path: str, cache_path: str, manifest_path: str) -> str:
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
    source_hash = compute_file_hash(shared_path)
    key = os.path.basename(shared_path)
    if key in manifest and manifest[key]["hash"] == source_hash and os.path.exists(cache_path):
        return cache_path  # Verified cache hit
    shutil.copy2(shared_path, cache_path)
    manifest[key] = {"hash": source_hash, "size": os.path.getsize(cache_path)}
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)
    return cache_path


def stage_checkpoint_async(save_fn, state_dict, epoch: int, job_scratch: str, durable_dir: str):
    nvme_path = os.path.join(job_scratch, f"ckpt-{epoch}.pt")
    durable_path = os.path.join(durable_dir, f"ckpt-{epoch}.pt")
    save_fn(state_dict, nvme_path)  # Fast local NVMe write (3.5+ GB/s)

    def _flush():
        shutil.copy2(nvme_path, durable_path)
        os.remove(nvme_path)  # Reclaim /raid space immediately after durable flush

    t = threading.Thread(target=_flush, daemon=False)
    t.start()
    return t
```

```bash
# Slurm Prolog (/etc/slurm/prolog.d/50-local-nvme.sh) & Epilog (/etc/slurm/epilog.d/50-local-nvme.sh) (untested here)
# Prolog: create isolated per-job scratch directory on /raid
JOB_SCRATCH="/raid/job_${SLURM_JOB_ID}"
mkdir -p "${JOB_SCRATCH}"
chown "${SLURM_JOB_USER}:${SLURM_JOB_USER}" "${JOB_SCRATCH}"
chmod 0700 "${JOB_SCRATCH}"
echo "export LOCAL_SCRATCH=${JOB_SCRATCH}"

# Epilog: unconditionally remove per-job scratch directory on job exit/cancel/timeout
rm -rf "/raid/job_${SLURM_JOB_ID}"
```

---

## How it fails

Picture an on-call engineer who gets a page about a slow node. Each row below starts from a symptom you can see on that node and ends with the fix. Start from the discriminating evidence column, since it tells you which failure you are looking at before you touch anything.

| Failure Mode | Observed Symptom | Discriminating Evidence | Root Cause | Remediation |
|---|---|---|---|---|
| **1. Cache Eviction Thrashing / `/raid` Full (`> 85%` Fill)** | Epoch 2 starts fast (98.3% hit rate), but Epoch 4 slows down (96.1% or lower) or crashes with `ENOSPC` | `df -h /raid` shows **`> 85%–100%`** used; orphaned `job_*` folders or a dataset `> 85%` of `/raid` | Dataset + uncleaned checkpoints exceed safe 85% NVMe capacity, triggering eviction churn and high WAF | Enforce Slurm Epilog cleanup, delete staged checkpoints after flush, and shard datasets across nodes |
| **2. `fio` Shows 3.5 GB/s, but Training Sees 150 MB/s** | Raw NVMe benchmark is fast, yet `DataLoader` starves GPUs | `numactl --hardware` shows workers on `NUMA 1` while NVMe is on `NUMA 0`; `perf record -g` shows 800% CPU in Python JPEG decode | Cross-socket NUMA traversal penalty or single-threaded Python CPU decode bottleneck | Pin workers to the NVMe NUMA node, set `pin_memory=True`, `persistent_workers=True`, and offload decode to DALI |
| **3. Identical Nodes, but Node B's NVMe Is 30% Slower** | Node B lags every epoch and becomes the `AllReduce` straggler | `smartctl -a` shows `Temperature >= 70°C` (74°C, thermal throttle active), mismatched firmware, or busy `iostat` during idle | Thermal throttling from blocked airflow, stale firmware, or background `fstrim`/GC mid-job | Restore cooling (`< 55°C`), align firmware across nodes, restrict `fstrim` to Epilog or maintenance windows |
| **4. Silent Stale-Cache Data Corruption Across Runs** | Model loss diverges or differs between nodes after a dataset update | Local `/raid` files have old `mtime` and mismatched SHA-256 hashes versus shared storage | Local cache keyed only by filename, with no hash or size check | Validate a `manifest.json` (SHA-256 hash + size) on job startup before accepting any cached file |
| **5. Misaligned RAID 0 Stripe or Missing `noatime`** | Sequential write reaches `< 40%` of the array's rating; high metadata IOPS during pure-read training | `xfs_info` shows `sunit=0 swidth=0`; mount shows `relatime`; `read_ahead_kb` is 128 | `mkfs.xfs` omitted `su/sw`, atime writes on every read, and 128 KB read-ahead under-pipelines stripes | Format with `su=512k,sw=8`, mount `noatime,nodiratime`, set `scheduler=none`, `read_ahead_kb=4096` |
| **6. Single-Drive Media Error Destroys `/raid` (RAID 0)** | Job fails with `Input/output error (EIO)`; `/dev/md0` goes offline | `nvme smart-log` shows `media_errors > 0` or `available_spare` below threshold on one drive | RAID 0 has zero redundancy; one failed drive invalidates the entire stripe | Alert on `percentage_used >= 90%`, `available_spare <= 15%`, and `media_errors > 0`; drain node and rebuild |

---

The failure table is the bridge between the numbers above and what you will see on a live node. Keep it open when a job misbehaves, and work its rows from top to bottom. Stop at the first row whose evidence matches what you see.

## Hands-on lab

### Venue and Scope

Start with the local model. Run this lab on any workstation with the deterministic Python model in `code/part13/local_nvme_staging_lab.py`, since it needs no special hardware. The GCP or GKE path uses Local SSD NVMe scratch disks attached with `--local-ssd-interface=NVME`, and it is the right place to see real drives. The destructive bare-metal commands above, including `mdadm`, `mkfs.xfs`, `blockdev`, `nvme`, `fio`, and `gdsio`, were not run on live hardware. Run those only on scratch hardware you can rebuild.

The lab runs 28 self-checks. The table groups them by theme, so a failing check points you back to the matching part of this chapter. Read the table as a map from each check to the section that teaches its math.

| Check range | What it verifies |
|---|---|
| 1–3 | Two-tier hardware profiles: DGX H100/H200 (1.92 TB RAID 1 OS, 30.72 TB RAID 0 scratch at 50.0 GB/s read) and GB200/GB300 tray (15.36 TB/tray, 276.48 TB/rack). |
| 4–6 | `mdadm` chunk size and XFS stripe alignment: `8 × 512 KB = 4.0 MB` full stripe (`sunit=128`, `swidth=1024`), `4 × 256 KB = 1.0 MB` full stripe (`sunit=64`, `swidth=256`), and stripe utilization from 12.5% on a 64 KB read to 100% on a 4 MB read. |
| 7–11 | Dataset staging break-even and async checkpoint math: inline cache fill (`245 s` to `200 s`, saving `405 s` over 10 epochs), explicit pre-staging break-even at 6 epochs, the 85% capacity rejection rule (`1,800 GB` rejected on `2,048 GB`), and checkpoint staging (`417 s` sync vs `143 s` local vs `1 s` async handoff). |
| 12–14 | Linux `blk-mq`, read-ahead, `noatime`, and NUMA audit: healthy versus degraded configurations, plus the `mq-deadline` and 128 KB read-ahead exception for pure random `O_DIRECT` workloads. |
| 15–18 | NVMe DWPD/TBW endurance and SMART health: `7,008 TBW` lifetime budget, thermal throttle alert at 74°C, wear warning at 92% used, and critical alerts on low spare or nonzero media errors. |
| 19–28 | Slurm Prolog/Epilog lifecycle and cluster math: 85% safe fill ceiling (`26,112 GB`), orphan leak (`39.06%` to `91.15%` rejected) and recovery (`52.08%` admitted, `0.0%` post-Epilog), 256-GPU Lustre sizing, and 72-GPU NVL72 ingestion sizing. |

Run the lab from the repository root, so the relative path to the script resolves. The script uses only the Python standard library, so it does not need an install step.

### Running the Lab

```bash
python3 -B code/part13/local_nvme_staging_lab.py
```

Here is what a clean run looks like. If your run prints a different summary line, look at the check range that failed first, and then reread that section of this chapter.

Expected output (verified here):

```text
=== Chapter 13.2 Lab: Local NVMe and Data Staging ===
  [PASS] 1. DGX H100/H200 OS tier uses 2x 1.92 TB M.2 NVMe in RAID 1 (3.84 TB raw, 1.92 TB usable, non-ephemeral)
  [PASS] 2. DGX H100/H200 scratch tier uses 8x 3.84 TB U.2 NVMe in RAID 0 at /raid (30.72 TB usable, 50.0 GB/s seq read)
  [PASS] 3. GB200/GB300 1U compute tray uses 1x 1.92 TB M.2 OS drive + 4x 3.84 TB E1.S RAID 0 scratch (15.36 TB/tray, 276.48 TB/rack)
  ...
  [PASS] 27. ASP Ch 5 NVL72 rack ingestion: 72 GPUs * 200 MB/s = 14.4 GB/s (within the 14–20 GB/s rack streaming range)
  [PASS] 28. Striping 15 TB/day of checkpoints across 8x 3.84 TB drives (1.875 TB/drive/day, WAF 1.2) yields 2.25 TB/day NAND writes (0.5859 DWPD, 8.53 years lifespan)

Summary: 28 passed, 0 failed
```

---

The mistakes below are the ones that show up most often once a team starts staging data. Each one is easy to avoid once you know the rule behind it, and each rule is tied to a number you have already calculated in this chapter.

## Common first mistakes

These five mistakes look harmless when you make them. Each one looks harmless until a job fails or a node goes down, and each one has a short check you can run before the next launch.

1. Pre-staging a dataset for a short fine-tuning run costs you more than it saves. Think of the copy as a fee paid before the first step. Copying 500 GB at 2.0 GB per second takes 250 seconds up front, and caching saves only 45 seconds per epoch. Any run shorter than six epochs therefore finishes slower than it would by streaming directly. Count the epochs before you copy anything.
2. Writing checkpoints or container layers onto the OS root partition, instead of `/raid`, is an easy slip. The root partition is the small boot volume the node needs to keep running. Filling or wearing out the 1.92 TB M.2 boot drives crashes system daemons such as `kubelet`, `slurmd`, and `containerd`, and that takes the whole node down. A daemon is a background service, and `kubelet` is the Kubernetes agent on each node. Point `TMPDIR`, `TORCH_HOME`, `HF_HOME`, and the container runtime graph root at `/raid` instead.
3. Relying on a Python `try/finally` block to clean up `/raid` does not work. A `try/finally` block runs cleanup code when the program exits normally or raises an error, but not when the process is killed. A GPU fault, an out-of-memory kill, or a Slurm wall-time limit sends `SIGKILL`, which bypasses Python cleanup entirely. That leaves multi-terabyte orphan directories behind. Cleanup belongs in the root-level Slurm Epilog, backed by a Prolog orphan sweep.
4. Staging millions of tiny files onto `/raid` without packing them first. Local NVMe copes with a metadata storm far better than a shared Lustre metadata server does. Even so, opening millions of individual files burns CPU on syscall overhead, and it prevents full-stripe 4 MB RAID 0 reads. A syscall is a request from a program to the kernel, and each open is one of them. Pack the files into WebDataset, Parquet, or `.bin` and `.idx` shards before you stage them.
5. Forgetting to delete staged checkpoints after the background flush completes. If you leave local copies behind, at 500 GB per checkpoint, those copies on a 2 TB scratch volume fill `/raid` after just four checkpoints. The job then crashes mid-run. Check the free space after every flush, and let the flush thread remove the local copy.

---

The exercises repeat the chapter's calculations with new inputs, so you practice the method instead of memorizing the answers. If a result looks surprising, go back to the matching section and check the formula before you change the inputs.

## Exercises

Work the six exercises with a calculator. Every number you need sits in the reference block at the end of this section, so use it to check each answer after you finish.

1. Two node layouts: Compare the DGX H100 and H200 drive layout with a DGX GB200 or GB300 NVL72 compute tray. What is the usable scratch capacity per node? What is it per tray? What is it for an eighteen-tray rack? Why does `/raid` use RAID 0 while the OS tier uses RAID 1? What is the full stripe width for the eight-drive array? What are `sunit` and `swidth` for the eight-drive array? Repeat the stripe and alignment steps for the four-drive array. What share of the drives does a 64 KB read activate? What share does a 4 MB read activate?
2. When does staging a dataset pay off: A 500 GB dataset of two million files trains on a node with 2 TB of local NVMe. Cold Lustre epochs take 245 seconds, and warm NVMe epochs take 200. Start with the inline cache fill during epoch one. How long do ten epochs take with local NVMe, and how long do they take without it? What is the percentage speedup? Next, pre-stage the data at 2.0 GB per second instead. How long does the copy take? What is the break-even epoch count? What is the net time gained or lost on a three-epoch run? What is it on a six-epoch run?
3. How long does a checkpoint stall the job? A distributed job writes a 500 GB checkpoint. Shared Lustre sustains 1.2 GB per second, and local NVMe sustains 3.5 GB per second. The asynchronous handoff acknowledges in one second. What is the synchronous stall to Lustre? How long does the local NVMe write take? What is the critical-path speedup? What is the shortest safe interval between checkpoints, so the background flush finishes before the next one starts?
4. Why is the data loader slow? Suppose `fio` on `/dev/md0` reads 3.5 GB per second, but the PyTorch loop gets only 150 MB per second, and the GPUs sit at 65 percent. Inspection shows five problems. The scheduler is `bfq`. The queue depth is 128. The read-ahead is 128 KB. The `/raid` mount uses `relatime`. The workers sit on the wrong NUMA node. Write the Linux command that fixes each problem for sequential shard streaming. How should `read_ahead_kb` differ for random `O_DIRECT` reads? What is the `gdsio` gain from switching to GPUDirect Storage?
5. How long will the drives last: Each of the eight U.2 drives in a DGX H100 `/raid` array holds 3.84 TB and is rated at 1.0 DWPD over five years. What is the lifetime TBW for one drive? What is it for the whole array? For 2.5 TB per day of host writes at a WAF of 1.2, what are the daily NAND writes, the effective DWPD, and the lifespan? Repeat the calculation for 15.0 TB per day of checkpoint traffic striped across all eight drives. What alert thresholds apply to `percentage_used`, `available_spare`, `temperature`, and `media_errors`?
6. Why does the second job fail admission? A DGX H100 `/raid` array has 30,720 GB usable and an 85 percent safe fill ceiling. What is the safe allocatable capacity? A killed 12,000 GB job leaves an orphan behind, and a new 16,000 GB job is then refused. Why is it refused? How does an orphan sweep in Prolog, paired with a cleanup in Epilog, let the job in? What is the fill percentage during the second job? What is it after the second job?

```text
Exercise Input Parameters & Expected Verification Targets (code/part13/local_nvme_staging_lab.py):
  - Ex 1 (Topology/RAID): DGX H100/H200 = 2x 1.92 TB M.2 RAID 1 (3.84 TB raw, 1.92 TB usable) + 8x 3.84 TB U.2 RAID 0 (30.72 TB usable, 6.25 GB/s/drive, 50.0 GB/s R, 28.0 GB/s W). GB200/GB300 tray = 1x 1.92 TB M.2 + 4x 3.84 TB E1.S RAID 0 (15.36 TB/tray, 18 x 15.36 = 276.48 TB/rack, 25.0 GB/s R, 14.0 GB/s W). 8x 512 KB chunk (4 KiB block): W_stripe = 4096 KB (4.0 MB), sunit = 128, swidth = 1024; 64 KB read = 0.125 chunk = 1/8 drives (12.5%) vs 4 MB = 8/8 drives (100%). 4x 256 KB chunk: W_stripe = 1024 KB (1.0 MB), sunit = 64, swidth = 256.
  - Ex 2 (Break-Even):    500 GB (2,000,000 files, 260 KB avg), 2 TB local NVMe; cold Lustre = 245 s (156.25 MB/s raw at 1.25 Gbps/GPU or 12.5 Gbps/2-GPU slice, 30% metadata overhead -> 110 MB/s vs 120 MB/s demand, 30.72 GB/s across 256 GPUs on 8 nodes / 32 GPUs per unit or 1,000 GPUs/pod); warm NVMe = 200 s (45 s saved/epoch, 18% speedup). Pattern A (10 epochs): 2,450 s vs 245 + 9 x 200 = 2,045 s (405 s saved, 16.53%). Pattern B (2.0 GB/s): T_copy = 250 s, N_be = 250 / 45 = 5.5556 (~5.56 -> 6 epochs); 3 epochs = 850 s vs 735 s (-115 s loss); 6 epochs = 1,450 s vs 1,470 s (+20 s gain).
  - Ex 3 (Checkpoints):   500 GB checkpoint: Lustre sync (1.2 GB/s) = 416.67 s (~417 s); local NVMe write (3.5 GB/s) = 142.86 s (~143 s); async handoff = 1.0 s (416.67x / ~417x critical-path speedup). Minimum safe interval without double-buffering = 416.67 s (~417 s) so NVMe -> Lustre flush + os.remove() completes.
  - Ex 4 (Linux/GDS):     3.5 GB/s fio vs 1.5 GB/s shared = 2.33x (> 2.0x rule; 10x saves 90%); training stuck at 150 MB/s (65% GPU util). Remediate: scheduler bfq -> none/mq-deadline, nr_requests 128 -> 1023, read_ahead_kb 128 -> 4096 (blockdev --setra 8192), mount relatime -> noatime,nodiratime, pin workers to NUMA 0. Random O_DIRECT (GDS / DeepSeek 3FS): keep read_ahead_kb <= 128 KB. gdsio: -x 2 (CPU) = 8.0 GB/s at 1.25 ms vs -x 0 (GDS) = 9.6 GB/s at 1.00 ms (+20% throughput, -20% latency).
  - Ex 5 (Endurance):     3.84 TB at 1.0 DWPD over 5 yr (1,825 days) = 7,008.0 TBW/drive (56,064 TB / 56.06 PB for 8 drives). At 2.5 TB/day host (WAF 1.2): 2.5 x 1.2 = 3.0 TB/day NAND, 0.7812 DWPD, 6.40 yr lifespan. At 15.0 TB/day across 8 drives (1.875 TB/drive/day, WAF 1.2): 2.25 TB/day NAND, 0.5859 DWPD, 8.53 yr lifespan. SMART thresholds: percentage_used >= 90%, available_spare <= 10% (warn <= 15%), temperature >= 70°C (343 K, normal 35–55°C, throttles 30%–70%), media_errors > 0.
  - Ex 6 (Slurm Hooks):   30,720 GB x 0.85 (15% headroom) = 26,112 GB safe ceiling. Orphaned job_1001 = 12,000 GB (39.06% fill) + job_1002 = 16,000 GB -> 28,000 GB (91.15% fill > 85%, rejected). With Prolog sweep + Epilog rm -rf: job_1001 swept, job_1002 admitted at 16,000 / 30,720 = 52.08% fill, returning to 0.0% after Epilog.
```

---

The interview questions below test whether you can explain a trade-off, not just recite a number. The answers show how to reason from the layer that matters, and how to state the break-even math in plain words.

## Interview angles

1. **"We added 30 TB of local NVMe to every GPU node, but the first epoch is still slow, and our one-epoch pre-training job saw zero speedup on data loading. Was the local NVMe a waste?"**
   A strong answer separates the two jobs that local NVMe does: dataset caching and checkpoint staging. Start there, because the two jobs pay back in different ways. The first epoch is always a cold cache miss, unless the data was pre-staged. A single-epoch petabyte pre-training stream that exceeds `/raid` capacity can never be fully cached. That same run still benefits from asynchronous checkpoint staging, which turns a 417-second synchronous Lustre write into a one-second local handoff. State the break-even formula directly. Divide the upfront copy time by the per-epoch savings. A 250-second copy that saves 45 seconds per epoch needs at least six epochs to pay off.

2. **"Why does a DGX H100 use RAID 1 for its two M.2 drives but RAID 0 for its eight U.2 `/raid` drives? Doesn't RAID 0 risk losing data if one SSD dies?"**
   The two tiers have different durability needs, and that difference is the whole answer. The M.2 drives hold the OS and system services, so RAID 1 keeps the node alive if one boot drive fails. The U.2 `/raid` volume holds only ephemeral data. That means cached copies of shards that live permanently on shared storage, and checkpoints that get flushed to durable storage right away. RAID 0 gives that volume its full 30.72 TB of capacity and full bandwidth, about 50 GB per second read and 28 GB per second write. Parity schemes like RAID 5 or 6 would bring the parity overhead and GPUDirect Storage alignment problems that RAID 0 avoids. Losing scratch is an inconvenience, because the golden copy still exists upstream.

3. **"Your `fio` benchmark on `/raid` hits 3.5 GB per second per job, but PyTorch's `DataLoader` only feeds the GPUs at 150 MB per second. How do you find the bottleneck?"**
   Walk up the stack one layer at a time, and do not guess at the cause. First, check `numactl --hardware` and `nvidia-smi topo -m`. They show whether the data loader workers run on the wrong NUMA socket, relative to the NVMe drives. Second, profile with `num_workers=0` or `perf record -g`. That reveals whether CPU cores are pegged decoding JPEGs or tokenizing text in Python. DALI or offline NeMo Curator shards would fix that. Third, check whether the dataset is millions of small files, because small reads may be too small to span more than one of the eight RAID 0 drives. Fourth, confirm that `pin_memory`, `persistent_workers`, `prefetch_factor`, `noatime`, and `read_ahead_kb` are all set correctly. Only then decide the fix.

---

The checkpoint questions below check the main ideas in order. Each answer points back to the numbers you worked through earlier in the chapter, so use them as a final review before you move on.

## Checkpoint questions (20)

<details>
<summary>**1. Why does the enterprise "stateless compute node, no local disks" rule break down for multi-epoch AI training and large-model checkpointing?**</summary>

Multi-epoch training reads the same shards dozens to hundreds of times. Distributed checkpointing writes hundreds of gigabytes at once, across every rank. For example, streaming over hundreds of epochs, or writing a 500 GB checkpoint synchronously, saturates the shared switch uplinks and the metadata server. Caching shards on local PCIe NVMe drops the second and later epochs to near-zero network use. Local checkpoint staging cuts the stall from 417 seconds to about one second.
</details>

<details>
<summary>**2. Under what four conditions should you bypass local NVMe dataset staging and stream directly from shared storage?**</summary>

You should skip local staging under any of four conditions. First, shared storage has headroom: link utilization is under 50 to 60 percent, and GPU utilization is at 95 percent or higher. Second, the dataset is too large to fit within 85 percent of local NVMe, even after sharding. Third, the job runs fewer epochs than the staging break-even point, as a single-epoch pre-training run does. Fourth, nodes fail often and lack automated cache rehydration and Slurm Epilog cleanup.
</details>

<details>
<summary>**3. How are local NVMe drives partitioned across the two storage tiers on a DGX H100/H200 versus a DGX GB200/GB300 NVL72 compute tray?**</summary>

On a DGX H100 or H200, the first tier is two 1.92 TB M.2 drives in RAID 1, giving 1.92 TB usable for the OS. The second tier is eight 3.84 TB U.2 drives in RAID 0, giving 30.72 TB usable at about 50 GB per second read. It is mounted at `/raid`.

On a DGX GB200 or GB300 NVL72 tray, the first tier is a single 1.92 TB M.2 drive. The second tier is four 3.84 TB E1.S drives in RAID 0. That gives 15.36 TB per tray, or 276.48 TB across an eighteen-tray rack.
</details>

<details>
<summary>**4. Why is `/raid` configured as RAID 0 rather than RAID 5 or RAID 6 on AI compute nodes?**</summary>

The `/raid` volume only ever holds ephemeral copies. Some are cached shards whose golden source lives on shared storage. Others are checkpoints that get flushed to durable storage right away. RAID 0 gives it 100 percent usable capacity, or 30.72 TB on a DGX H100, along with full bandwidth across every drive. RAID 5 and 6 would bring parity overhead, read-modify-write latency, and GPUDirect Storage alignment problems. None of those costs buys this volume anything.
</details>

<details>
<summary>**5. On an 8-drive `mdadm` RAID 0 array with a 512 KB chunk size and 4 KiB filesystem blocks, what are the full stripe width, XFS `sunit`, and XFS `swidth`?**</summary>

The arithmetic is short. Eight drives at 512 KB each make a full stripe of 4096 KB, or 4.0 MB. Divide the chunk by the 4 KB block size to get the stripe unit, then multiply by the drive count to get the width:

```text
Full stripe width = 8 x 512 KB = 4096 KB (4.0 MB)
XFS sunit         = 512 KB / 4 KB = 128 blocks
XFS swidth        = 8 x 128 = 1024 blocks (formatted via: mkfs.xfs -f -d su=512k,sw=8 /dev/md0)
```

Those values are the ones the `mkfs.xfs` command below carries.
</details>

<details>
<summary>**6. Why does a single 64 KB read achieve only 12.5% drive parallelism on an 8-drive, 512 KB-chunk RAID 0 array, and how do you reach 100% stripe utilization?**</summary>

Each drive's chunk is 512 KB. A 64 KB request fits entirely inside one drive's chunk, so it uses only one of the eight drives, or 12.5 percent of the array. Reaching 100 percent utilization takes an aligned read of at least 4.0 MB, which spans all eight drives. Concurrency helps smaller reads too. Enough requests in flight across eight or more data loader workers, with a queue depth of 16 or higher, spread even small reads across every drive at once.
</details>

<details>
<summary>**7. How do you calculate the break-even epoch count for explicit dataset pre-staging?**</summary>

Divide the upfront copy time by the time saved per epoch.

```text
N_be = T_copy / (T_remote - T_local) = 250 s / (245 s - 200 s) = 250 / 45 ~= 5.56 epochs (minimum 6 epochs)
```

For a 500 GB dataset copied at 2.0 GB per second, the copy takes 250 seconds. Each cached epoch saves 45 seconds, so the job needs to run at least six epochs to come out ahead.
</details>

<details>
<summary>**8. What causes a local NVMe cache hit rate to drop from 98.3% in Epoch 2 to 96.1% in Epoch 4, and how do you fix that degradation?**</summary>

A 0.2 percent hit rate on the first epoch is a normal cold start. Hit rates above 97 percent on the second and third epochs show healthy warm caching. The drop to 96.1 percent on the fourth epoch is the warning sign. It means `/raid` has crossed 85 percent full and started evicting and garbage-collecting active shards mid-run. The fix is to keep `/raid` usage at or below 85 percent. You can also shard the dataset across nodes with `DistributedSampler`, or switch from plain LFU eviction to deterministic shard pinning.
</details>

<details>
<summary>**9. Why does synchronous writing of a 500 GB checkpoint to shared Lustre stall training for 417 seconds, and how does two-phase local NVMe staging achieve a 417x critical-path speedup?**</summary>

At 1.2 GB per second, writing 500 GB synchronously to Lustre blocks every GPU for about 417 seconds. Two-phase staging writes the checkpoint to local NVMe at 3.5 GB per second instead, which takes about 143 seconds in the background. The training loop waits only about one second for the memory handoff before it resumes. A background thread then flushes the file from `/raid` to Lustre and deletes the local copy once that finishes. For example, the stall moves off the GPUs, and that is where the 417x speedup comes from.
</details>

<details>
<summary>**10. Why is filename-only cache lookup dangerous on `/raid`, and how does `manifest.json` prevent silent training corruption?**</summary>

If an upstream pipeline updates a file on shared storage, a node's `/raid` cache may still hold last week's copy under the same filename. Training then quietly mixes old and new data, and no error appears. A `manifest.json` stores each file's SHA-256 hash and byte size. Checking that hash before you trust a cache hit catches the staleness and forces a re-fetch.
</details>

<details>
<summary>**11. Which Linux `blk-mq` scheduler should be configured for AI NVMe workloads, and why should `bfq` or `cfq` be avoided?**</summary>

Use `none`, which sends requests straight to the hardware queues with no scheduling overhead. Choose `mq-deadline` when mixed read and write checkpoint traffic needs bounded write latency. Avoid `bfq` and the legacy `cfq` scheduler. Both were built around fairness heuristics and spinlocks for rotational hard drives, and on NVMe they only add overhead.
</details>

<details>
<summary>**12. How does `blockdev --setra 8192 /dev/md0` affect `read_ahead_kb`, and when should you raise versus lower read-ahead?**</summary>

The `blockdev --setra` command counts in 512-byte sectors. Setting 8192 sectors therefore sets `read_ahead_kb` to 4096 KB, which matches a full 4 MB RAID 0 stripe. The Linux default is 128 KB. Raise read-ahead to 4096 or 8192 KB for large sequential shard streaming. Keep it at 128 KB or lower for pure random `O_DIRECT` workloads, such as GPUDirect Storage or 3FS, because those bypass the page cache anyway.
</details>

<details>
<summary>**13. Why must `/raid` always be mounted with the `noatime` option on AI training nodes?**</summary>

Without `noatime`, the filesystem updates each file's last-access timestamp on disk every time the file is read. POSIX requires that by default. Across millions of training reads, that turns a read-only workload into a mixed read-write one. It wastes IOPS and adds SSD wear you do not need.
</details>

<details>
<summary>**14. In the local NVMe benchmark lab, what are the four benchmark workload profiles, and what NVMe-to-shared ratio justifies local caching?**</summary>

The first profile, Model Load, is a large sequential read. NVMe reaches about 3.5 GB per second, versus 1.5 to 3.0 GB per second on shared storage. Batch Stream runs parallel medium-block reads, and it reaches about 2.8 GB per second on NVMe. Random Read / Metadata Storm reaches about 1.2 GB per second for 4 MB random reads. It reaches over 50,000 operations per second for local metadata, against 1,000 to 5,000 on a shared metadata server. Checkpoint Write reaches 2.1 to 3.5 GB per second per writer on NVMe. A Model Load ratio above 2x justifies local caching and checkpoint staging.
</details>

<details>
<summary>**15. What do `gdsio` transfer selectors `-x 2` and `-x 0` measure, and what improvement is typical when switching to GPUDirect Storage?**</summary>

Selector `-x 2` measures the traditional path through pinned host memory. It reaches about 8.0 GB per second at 1.25 ms average latency. Selector `-x 0` measures the GPUDirect Storage direct DMA path from NVMe into GPU memory. It reaches about 9.6 GB per second at 1.00 ms average latency. That switch delivers a 20 percent gain in both throughput and latency, and it frees the host CPU as well.
</details>

<details>
<summary>**16. Why did DeepSeek's 3FS eliminate read page caching in favor of `O_DIRECT` RDMA reads across cluster NVMe drives?**</summary>

DeepSeek found that large-scale training and inference perform huge numbers of random reads across terabytes of data. Those reads thrash the OS page cache and waste CPU cycles on host memory copies. So 3FS bypasses the page cache, using `O_DIRECT` and RDMA reads straight from each node's NVMe drives. The result was 6.6 TB per second across a 68-node cluster, with a peak of 7.3 TB per second. The nodes had ten 16 TB drives and dual 100 Gb/s links. The cluster also served 1.4 TB per second of background traffic, compared with about 1.1 TB per second on Ceph.
</details>

<details>
<summary>**17. How do you compute the TBW rating and expected lifespan of a 3.84 TB, 1.0 DWPD drive under a 2.5 TB/day workload with a WAF of 1.2?**</summary>

Start with the drive's lifetime budget, then apply the write amplification, then divide:

```text
TBW      = 3.84 TB x 1.0 DWPD x 365 x 5 = 7,008.0 TB
W_NAND   = 2.5 TB/day x 1.2 WAF = 3.0 TB/day (0.7812 effective DWPD)
Lifespan = 7,008.0 / (3.0 x 365) = 6.40 years
```

The NAND sees 3.0 TB each day, so the lifespan works out to 6.40 years.
</details>

<details>
<summary>**18. Which four `nvme smart-log` metrics must be monitored on `/raid` drives, and what are their alert thresholds?**</summary>

Monitor `percentage_used`, and alert at 90 percent or higher. Watch `available_spare`. Warn at 15 percent, and drain the node immediately at 10 percent or below. Check `temperature`. Normal operation runs at 35 to 55 degrees Celsius. At 70 degrees Celsius or higher, the drive throttles by 30 to 70 percent. Track `media_errors`, and alert on any value above zero, since RAID 0 has no parity to fall back on.
</details>

<details>
<summary>**19. Why must per-job `/raid/job_$SLURM_JOB_ID` creation and teardown be enforced in Slurm Prolog and Epilog scripts rather than inside the user's training script?**</summary>

A `SIGKILL` from an out-of-memory event, a GPU hardware fault, node preemption, or a wall-clock timeout cannot be caught by user-space Python or bash cleanup code. So the cleanup has to live in root-owned Slurm hooks. The Epilog runs after every job exit and deletes the job's `/raid` directory. The Prolog sweeps stale orphans and enforces the 85 percent safe fill ceiling before it admits the next job.
</details>

<details>
<summary>**20. How do you isolate whether GPU data starvation comes from slow Python `DataLoader` transforms versus slow Host-to-Device transfers?**</summary>

Start by benchmarking the data loader alone with `num_workers=0`. That measures pure Python read and decode time per batch. Then measure the Host-to-Device transfer time separately. You can read the copy lane in Nsight Systems, or wrap CUDA event timers around `.to(device, non_blocking=True)`. If Python transforms dominate, add workers, vectorize the code, offload to DALI, or pre-shard with NeMo Curator. If the transfer itself dominates, enable `pin_memory`, check NUMA locality, or switch to GPUDirect Storage.
</details>

---

## Sources and review notes

### Primary Sources (Read in Full and Migrated)

```text
Source Map & Key Migrated Facts:
  1. nvidia-devops Volume 15 (AI Storage, Checkpointing, and Data Pipelines):
     - nvidia-zero-to-hero/volume-15/chapter-03-local-nvme-and-data-staging.md (when to use vs skip local NVMe, decision flowchart, 8-node 256-GPU Lustre scenario on 500 GB / 2,000,000 files at 260 KB avg, 25-100 Gbps links, 245 s cold vs 200 s warm, cache hit progression 0.2% -> 98.3% -> 97.8% -> 96.1%, 500 GB checkpoint staging 417 s vs 1 s, SHA-256 manifest.json validation, troubleshooting table).
     - nvidia-zero-to-hero/volume-15/labs/lab-02-benchmark-local-nvme-and-shared-storage.md (4 AI storage benchmark profiles and NVMe / Shared > 2.0x caching rule).
  2. Book Corpus Sources:
     - AI Systems Performance Engineering (Ch. 5: GPU-Based Storage I/O Optimizations — 200 MB/s per GPU, 1.6 GB/s per 8-GPU node, 14-20 GB/s / 14.4 GB/s per 72-GPU NVL72 rack, blk-mq none/mq-deadline, read_ahead_kb 128 KB vs 4096-8192 KB, XFS noatime, DataLoader / DALI 800% -> 200% CPU / NeMo Curator / Blackwell Decompression Engine 900 GB/s NVLink-C2C, gdsio -x 2 8.0 GB/s @ 1.25 ms vs -x 0 9.6 GB/s @ 1.00 ms, DeepSeek 3FS 6.6-7.3 TB/s on 68 nodes with 10x 16 TB NVMe and dual 100 Gb/s vs Ceph 1.1 TB/s).
     - AI Data Center Network Design and Technologies (Ch. 9: Storage Network Design and Technologies — PCIe Gen5 local SSD latency vs InfiniBand/Ethernet, NVMe queue architecture, storage tier lifecycle).
  3. Cross-Referenced Handbook Chapters:
     - Chapter 9.2 (DGX H100/H200 2-tier NVMe layout) and Chapter 9.5 (DGX GB200/GB300 NVL72 1U compute tray E1.S layout).
```

### Inferences and Verification Notes
- Bare-metal CLI commands (`mdadm`, `mkfs.xfs` or `ext4` checked via `/proc/mounts` and `fstrim.timer`, `mount` on `/raid/tmp`, `/raid/cache/train-0042.tar` (`0042`), `/raid/ckpt-epoch-N.pt`, `/raid/.../manifest.json` vs `/shared-storage/dataset/train-0042.tar` and `/shared-storage/checkpoints/ckpt-epoch-N.pt` on `/lustre`, `/beegfs`, or `/shared-storage` `.tar` / `TFRecord` shards, `blockdev` tuning `/sys/block/nvme0n1/queue/scheduler`, `/sys/block/nvme0n1/queue/read_ahead_kb`, `/sys/block/md0/queue/read_ahead_kb`, `/sys/block/nvmeXn1/queue/read_ahead_kb`, and `/sys/block/nvmeXn1/queue/nr_requests` with `nr_requests=128` vs `nr_requests=1023` and `pure_random_o_direct`, `nvme` / `smartctl` checking `P/E` cycles and `available_spare_threshold` -> `CRITICAL_REPLACE_DRIVE`, `SQE`/`CQE` and `PRP`/`SGL` descriptors, `PIX` vs `UPI` on `A100` / `400G` nodes, `cuFileRead` via `nvidia-fs` vs `H2D` copies timed with `torch.cuda.Event`, `nvidia.dali.pipeline.Pipeline`, `LZ4`, `9/10` checkpoint savings, and `15.3` / `99.8` / `156` / `225` / `255` / `400` / `1750` / `2000` / `1000000` metrics, `fio`, `gdsio`) are operational patterns from the cited sources and are marked *(untested here)*.
- All RAID 0 geometry calculations, multi-epoch staging break-even formulas, checkpoint staging speedups, `blk-mq` tuning audits, DWPD and TBW endurance models, and Slurm Prolog and Epilog simulations are verified in `code/part13/local_nvme_staging_lab.py` (`28 passed, 0 failed`).
