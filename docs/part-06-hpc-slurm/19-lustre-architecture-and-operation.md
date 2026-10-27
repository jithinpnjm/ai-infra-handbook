---
id: "c06-19"
title: "6.19 Lustre architecture and operation"
sidebar_label: "6.19 Lustre architecture and operation"
sidebar_position: 19
description: "Lustre in depth: MGS/MDS/MDT/OSS/OST/clients and LNet, creating a file system, striping (raid0, PFL composite layouts, DoM), directory striping (DNE), quotas and project quotas, pools, migration, failover, monitoring and tuning, and diagnosing metadata and data bottlenecks for AI workloads, with a striping model and corrections to common misconceptions"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.19 Lustre architecture and operation

| | |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | Lustre test cluster (VMs); the striping model runs anywhere |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Command syntax and defaults were read from the Lustre manual pages in a sparse checkout of lustre/lustre-release (commit `6325870`, 2026-10-21, development tree) for `lfs setstripe`, `getstripe`, `migrate`, `setquota`, `mkfs.lustre`, and `lctl`. Architecture follows the SCL book and the NVIDIA-DevOps volume-15 chapter (with corrections noted). `code/part06/lustre_stripe.py` was run (output shown). No Lustre file system was built; labs **untested** |

## Why this matters for AI infrastructure

Lustre is the most widely deployed parallel file system in HPC and in many large AI training sites (it underlies several vendor and cloud services). Its strengths, enormous aggregate bandwidth and a POSIX interface, come with sharp edges: striping defaults that cap the bandwidth of a big checkpoint at one disk, a metadata service that a data loader can overwhelm, and failure modes that look like hung nodes. Operators who understand striping, metadata and the management tools can both prevent and diagnose most "storage is slow" tickets.

## Prerequisites and outcomes

Needs 6.18 (parallel storage concepts), Part 2 (LNet runs over IB and Ethernet), Part 1 (block devices, ldiskfs/ZFS). After this chapter you can:

- Draw the Lustre architecture and explain each role (MGS, MDS/MDT, OSS/OST, clients, LNet) and the data and metadata paths.
- Create a file system with `mkfs.lustre` (single node and with failover), mount servers and clients.
- Choose and set striping: stripe count and size, composite (PFL) layouts, Data-on-MDT, pools, directory striping across MDTs.
- Manage quotas (user, group, project), balance OSTs, migrate data, and evacuate hardware.
- Describe the failure and recovery model; know which components need HA.
- Monitor and troubleshoot with `lfs`, `lctl`, client stats and server logs; apply AI-specific advice (shards, checkpoint layouts).

## 1. Architecture

```mermaid
flowchart TB
  subgraph Clients
    C1[Client with lustre.ko + LNet]
    C2[Client]
  end
  subgraph Metadata
    MGS[MGS: configuration]
    MDS1[MDS 1] --- MDT0[(MDT0)]
    MDS2[MDS 2] --- MDT1[(MDT1)]
  end
  subgraph Data
    OSS1[OSS 1] --- OST0[(OST0)] & OST1[(OST1)]
    OSS2[OSS 2] --- OST2[(OST2)] & OST3[(OST3)]
  end
  C1 -- 1 open/lookup/layout --> MDS1
  C1 == 2 read/write stripes in parallel ==> OSS1 & OSS2
  C2 --> MDS2
  C2 ==> OSS2
  Clients -. mount: find config .-> MGS
```

Components (names as in the SCL book and `mkfs.lustre(8)`):

| Role | What it does |
|---|---|
| **MGS** (Management Server) | Holds configuration for one or more Lustre file systems (locations of all targets); clients and servers contact it at mount. Often combined with MDT0 but may have its own small device |
| **MDS / MDT** | Metadata server and metadata target (the storage device): file and directory names, permissions, timestamps, and the **layout** (which OST objects hold the data). An MDS can serve several MDTs; with **DNE** (Distributed Namespace) a file system has several MDTs, each owning part of the namespace |
| **OSS / OST** | Object storage server and target: stores file data as objects. An OSS typically serves several OSTs; scaling bandwidth means adding OSS/OST pairs, which can be done to a running file system |
| **Clients** | Compute and login nodes with the Lustre client module; present a POSIX mount; talk to MDS for metadata and directly to OSSs for data |
| **LNet** | Lustre's network layer: addresses by NID (`10.0.0.5@tcp`, `10.1.0.5@o2ib`), supports TCP, InfiniBand (o2ib), and routers between networks. Over RDMA it provides the high throughput |

Backing file systems: **ldiskfs** (a modified ext4, the traditional choice) or **ZFS** (software RAID-Z, checksums, snapshots; `--backfstype=zfs`). The book notes the central property: easy scalability, "at any time a new server can be added to a running file system, increasing both speed and storage capacity", and that only Linux clients/servers are supported natively (others need an NFS/SMB re-export that gives up the benefits). Failure tolerance: targets are on shared storage reachable from two servers (active/passive or active/active pairs) with failover managed by Pacemaker/Corosync or similar; Lustre itself provides **recovery** (clients replay requests after a server restart or failover within a recovery window), not the cluster resource manager.

## 2. Creating a file system

From the `mkfs.lustre(8)` examples (shortened):

```bash
# combined MGS + MDT0 for file system "testfs"
mkfs.lustre --fsname=testfs --index=0 --mdt --mgs /dev/sda1
# an OST using that MGS
mkfs.lustre --fsname=testfs --index=0 --ost --mgsnode=cfs21@tcp0 /dev/sdb
# failover pair for MGS+MDT: both server NIDs listed with --servicenode
mkfs.lustre --fsname=testfs --index=0 --mdt --mgs --servicenode=cfs21@tcp0,cfs21ib@o2ib0 --servicenode=cfs22@tcp0,cfs22ib@o2ib0 /dev/sda1
# ZFS backing: pool + dataset
mkfs.lustre --fsname=testfs --index=0 --mdt --mgs --backfstype=zfs zfspool/mdt1 mirror /dev/sdb /dev/sdc mirror /dev/sdd /dev/sde
```

Then mount each target on its server (`mount -t lustre /dev/sda1 /mnt/mdt`, order: MGS/MDT, then OSTs) and mount clients: `mount -t lustre mgsnode@tcp:/testfs /mnt/testfs` (a list of MGS NIDs separated by `:` or `,` for failover). Key options: `--ost|--mdt|--mgs`, `--fsname`, `--index` (unique per target type), `--mgsnode`, `--servicenode`/`--failnode` (failover partners; do not mix), `--backfstype`, `--mkfsoptions`, `--reformat`. `tunefs.lustre` changes parameters later (e.g. changing NIDs) and must only be run on an OSS or MDS while the server is stopped.

### Step-by-step Lustre creation, LNET port `988`, and OSS RAM sizing (from the book)

In the book's Chapter 9 and Chapter 28 walkthroughs, Lustre runs entirely as kernel modules on both servers and clients, communicating over **LNET** (Lustre Networking) via Lustre Network Drivers (LNDs). On the client side, the software comprises the Metadata Client (MDC), Object Storage Client (OSC, where the group of OSCs forms one Logical Object Volume, or LOV), and Management Client (MGC). Each LNET interface has a unique NID (`<address>@<LND protocol><lnd#>`, such as `10.20.30.40@o2ib1` or `192.168.2.3@tcp2`). Each `<protocol><index>` forms an isolated LNET network (so `1.2.3.4@tcp0` cannot talk directly to `2.3.4.5@tcp1`). **On IP networks, the LNET kernel module uses TCP port `988`—ensure port `988` is not blocked by any firewall.**

1. **Configure LNET (`/etc/modprobe.d/lustre.conf`)**: define networks using `<lnd><#>(<dev>)[,…]`, for example `options lnet networks="tcp0(eth0)"` or `options lnet networks="o2ib0(ib0),tcp0(eth2)"`. Load the module and verify the NIDs (`(untested here)`):

   ```bash
   # (untested here) — Chapter 9 LNET verification example (using networks="tcp0(eth1)")
   modprobe lnet
   lnetctl net show
   lctl list_nids
   ```

2. **Format and mount the combined MGS + MDT volume on the MDS** (the file system name `--fsname` is limited to 8 characters; mount MGS and MDTs first before OSTs; the book recommend RAID-10 for MDTs due to small I/O size and RAID-6 for OSTs due to 1 MB+ I/O size):

   ```bash
   # (untested here) — Chapter 9 HA-capable example with two --servicenode NIDs
   mkfs.lustre --mdt --mgs --index=0 \
     --servicenode 192.168.2.3@tcp0 \
     --servicenode 192.168.2.4@tcp0 \
     --fsname=large-fs /dev/sdX
   mount -t lustre /dev/sdX /mnt/mdt

   # (untested here) — Chapter 28 simple non-HA recipe
   mkfs.lustre --mdt --mgs --fsname=large-fs /dev/sdX
   mount -t lustre /dev/sdX /mnt/mdt
   ```

3. **Format and mount each OST volume on the OSS nodes**:

   ```bash
   # (untested here) — Chapter 9 OSS initialization
   mkfs.lustre --ost --index=0 --fsname=large-fs \
     --mgsnode=192.168.2.3@tcp0 --mgsnode=192.168.2.4@tcp0 \
     /dev/sdZ
   mount -t lustre /dev/sdZ /mnt/ost1

   # (untested here) — Chapter 28 simple non-HA OSS recipe
   mkfs.lustre --ost --fsname=large-fs --index=0 \
     --mgsnode=mds.your.org@tcp0 /dev/sdZ
   mount -t lustre /dev/sdZ /mnt/ost0
   ```

4. **Mount the Lustre file system on the clients**:

   ```bash
   # (untested here) — Chapter 9 client mount with comma-separated MGS NIDs
   mount -t lustre 192.168.2.3@tcp0,192.168.2.4@tcp0:/large-fs /mnt/lustre
   ```

**OSS RAM sizing formulas from the book**: Lustre OSS nodes require substantial memory. By default, each OST uses `400 MB` of RAM for logging and about `600 MB` for metadata caching, plus `1.5 MB` for each service thread (where the number of threads `N_threads` can be roughly estimated as the number of clients divided by the number of connected OSTs):

```text
Per-OST baseline RAM = 400 MB + 600 MB + 1.5 MB * N_threads
Recommended OSS total RAM = 2 GB + 1 GB per OST (plus extra RAM for OS/network buffers and caching)
```

Sizing rules of thumb (common practice, verify with vendor guides): MDT on fast flash (NVMe, mirrored) because metadata is small random I/O; inode count chosen at format time (ldiskfs `bytes-per-inode`) for the expected file count; OSTs sized for rebuild time (RAID/ZFS groups of 8+2 on 8-12 TB disks are typical for HDD; for NVMe systems erasure-coded or ZFS vdevs); several OSTs per OSS to use all CPUs and NICs; OSS network bandwidth at least the sum of its OST bandwidth; client network matched to OSS network (400 Gb/s IB on GPU nodes is common).

## 3. Striping

### The raid0 layout

Every file has a **layout**: a list of OST objects and the stripe size. With the default `raid0` pattern the file is cut into `stripe_size` chunks assigned **round-robin** to `stripe_count` OST objects. It is **not** "split into N contiguous parts": consecutive chunks alternate between OSTs. `code/part06/lustre_stripe.py` models this:

```text
1 GiB file, stripe_size 1 MiB, stripe_count 4: bytes per OST object (MiB)
[256, 256, 256, 256]
First 8 chunks -> OST slot: [0, 1, 2, 3, 0, 1, 2, 3]
A 3 MiB read at offset 2.5 MiB touches slots: [0, 1, 2, 3]
A 512 KiB read at offset 0 touches slots: [0] (one OST: small I/O does not parallelise)
```

Consequences: a large sequential read or write is spread over all `stripe_count` OSTs and gets their aggregate bandwidth; a small I/O touches one OST, so striping does not speed it up; a file with stripe_count 1 is limited to a single OST regardless of the size of the file system. (The NVIDIA-DevOps volume-15 chapter describes a 2-stripe 1 GB file as "two chunks of 500 MB each", which is a common simplification but wrong for how Lustre places data: chunks alternate in `stripe_size` units.)

### Defaults and setting

From `lfs-setstripe(1)` in the development tree: `-c/--stripe-count` (0 = file-system default, **default 1**, -1 = all OSTs), `-C/--overstripe-count` (more than one stripe per OST), `-S/--stripe-size` (**default 4 MiB** in this tree; must be a multiple of 64 KiB; older releases defaulted to 1 MiB, so check yours), `-i/--stripe-index` (starting OST; -1 lets the MDS balance, "strongly recommended"), `-o/--ost` (explicit OST list), `-p/--pool` (OST pool), `-L/--layout` (`raid0` or `mdt`). On a directory the settings become the default for files created within; `lfs setstripe -d dir` removes the directory default. `lfs getstripe [-d] path` shows the layout.

```bash
lfs setstripe -c 1  -S 1M  /lustre/small-files        # tiny files: one stripe
lfs setstripe -c 16 -S 4M  /lustre/datasets           # big shared read-mostly files
lfs setstripe -c -1 -S 4M  /lustre/checkpoints        # stripe over all OSTs (use with N-1 checkpoint files)
lfs getstripe -d /lustre/checkpoints
```

Guidance: default stripe count 1 is right for the file-per-process pattern with many files (each file lands on its own OST, load balanced by the MDS); use larger stripe counts for big files shared by many clients or written by one fast client; match `stripe_size` to application I/O size (1 to 4 MiB typical; multiples of the I/O request size to avoid lock contention at boundaries). Too many stripes on small files wastes metadata and RPCs; too few on large files caps bandwidth.

### Progressive File Layouts (PFL) and other layouts

A **composite layout** divides a file into components by offset, each with its own stripe parameters, so a file can start narrow and become wider as it grows (`-E`/`--component-end`):

```bash
lfs setstripe -E 4M -c 1 -E 64M -c 4 -E -1 -c -1 /lustre/dir    # from the man page examples
```

This gives small files one stripe (cheap) and large files all OSTs (fast) without the user choosing: set it as the **directory default** for general-purpose areas. Related features in the man page: **Data-on-MDT** (`-L mdt` for a first component placed on the MDT for fast small-file access, limited by `lod.*.dom_stripesize`), **self-extending layouts** (`-z/--extension-size` grows the first component in steps and avoids full OSTs), **mirrored layouts** (`-N/--mirror-count`, with components in different pools such as `flash` and `disk` and the `prefer` flag so clients favour the flash replica), and newer **erasure-coded** layouts (`--ec`). The tool model prints a PFL example: for a 1 GiB file with components `4 MiB x1`, `to 64 MiB x4`, and `rest x16 (4 MiB stripes)`:

```text
  [    0 MiB,     4 MiB)  stripe_count=1   stripe_size=1 MiB
  [    4 MiB,    64 MiB)  stripe_count=4   stripe_size=1 MiB
  [   64 MiB,  1024 MiB)  stripe_count=16  stripe_size=4 MiB
```

### Pools

An **OST pool** names a subset of OSTs (e.g. `flash`, `disk`); `lfs setstripe -p flash ...` allocates from it; combine with directory defaults and mirrors for tiering. Pools are defined with `lctl pool_new` / `pool_add` on the MGS (general knowledge; see `lfs pool_list`).

### Directory striping and DNE

With multiple MDTs, `lfs mkdir -i N dir` creates a directory on MDT N and `lfs setdirstripe -c K dir` stripes a directory over K MDTs (large directories); `lfs mkdir -c -1 -D` style default directory layouts spread subdirectories across MDTs. `lfs migrate -m START_MDT dir` moves a directory tree to other MDTs (recursively by default). Use DNE to spread per-user or per-project trees across metadata servers. Hash-striped single huge directories help create-heavy workloads but make `ls` slower.

## 4. Quotas and capacity

Enabled at format/`tunefs` time (`--quota` / `lctl conf_param ... quota.ost=ugp` depending on version) and managed with `lfs`: `lfs quota -u alice /lustre`, `lfs setquota -u alice -b 9T -B 10T -i 1M -I 1100K /lustre` (soft/hard block and inode limits; `-g` groups, `-p` projects; default quotas `-U/-G/-P`; `--pool` quotas; grace time `-t`; `--delete`, `--reset`). **Project quotas** (`lfs project -p ID -s dir`, then `lfs setquota -p ID ...`) enforce limits per directory tree irrespective of file owner, the natural unit for AI teams and datasets. Capacity: `lfs df -h` (per-MDT/OST usage; look for imbalance), `lfs df -i` (inodes).

**Balancing, OST retirement/deactivation, and evacuation**: `lfs migrate` moves OST objects between OSTs to rebalance, change stripe count (`lfs migrate -c 16 file`), move between pools, or evacuate an OST for maintenance; it takes the same `setstripe`-style options and can run with `lfs find ... --print0 | lfs migrate -0 ...`; the layout swap is performed so that, per the man page, files are migrated while preserving data (verify behaviour for open/active files on your version; plan migrations during low load). The NVIDIA-DevOps chapter calls migration "offline"; in practice it is an online but I/O-heavy operation.

When an OST shows hardware trouble and needs to be retired, the book gives a four-step deactivation and evacuation sequence (`(untested here)`):

1. Run `lctl dl` to list all Lustre devices visible on the client and find the numeric device index `N` of the target OST.
2. Disable new object allocations on that OST by running `lctl --device N deactivate` (where `N` is the device number from `lctl dl`).
3. Locate files residing on the retiring OST (for example with `lfs find --ost ...`) and migrate their data onto healthy OSTs using `lfs_migrate` (or `lfs migrate`).
4. If an OST fails after the file system already holds data and must be repaired offline, unmount all clients first, then unmount all OSTs, then unmount the MDTs and MGS, mount the affected OST locally as `ldiskfs` (if ext4-based), and run the Lustre-patched `e2fsck` per your exact Lustre version documentation.

## 5. Failure and recovery model

- **Failover pairs**: each MDT/OST device is reachable from two servers via shared storage (dual-ported disks/NVMe-oF/JBOD); if one server fails the partner mounts the target and recovery begins.
- **Recovery**: after a restart clients reconnect and replay uncommitted requests during a **recovery window** (default several minutes; configurable). Applications see a pause rather than errors if recovery succeeds; clients that miss the window are evicted (stale file handles, I/O errors).
- **Client eviction**: unresponsive clients (network flap, hang) are evicted by servers after timeouts, freeing locks; the node must remount. Time synchronisation matters (6.18).
- **LFSCK**: online consistency checker (`lctl lfsck_start`), used after crashes or suspected inconsistency.
- **HSM and changelogs**: hierarchical storage management and change logs support tiering to object stores and external tools.
- **Hardware**: RAID/ZFS redundancy per target; dual power and network paths; spare OSS capacity; monitoring of disk and SSD health.

## 6. Monitoring and tuning

| Tool | Use |
|---|---|
| `lfs df -h`, `lfs df -i` | Space and inode distribution per target |
| `lfs getstripe`, `lfs find`, `lfs quota` | Layout, searches by size/stripe/age, usage |
| `lctl get_param` / `lctl set_param` / `lctl list_param` | Read and set tunables and statistics (`llite.*` client side, `osc.*`, `mdc.*`, `obdfilter.*` on OSS, `mdt.*` on MDS); `lctl conf_param`/`set_param -P` for persistent settings |
| `lctl dk` | Kernel debug log dump |
| Client `/proc/fs/lustre` / `lctl get_param llite.*.stats` | Operation counts and latencies (open, close, getattr, read, write) |
| `lnetctl` | LNet configuration and statistics (`lnetctl net show`, `stats show`) |
| `lctl ping NID` | LNet reachability |
| Server logs (`dmesg`, `/var/log/messages`) | Evictions, recovery, ldiskfs/ZFS errors, LNet errors |
| Monitoring stacks | Lustre exporters for Prometheus, Grafana dashboards, vendor tools (e.g. IML, LTOP-like tools) |

Common tunables (names illustrative, validate against your version): client `osc.*.max_rpcs_in_flight`, `osc.*.max_dirty_mb`, `llite.*.max_read_ahead_mb`, `llite.*.statahead_max` (speeds `ls -l`); server `ost.OSS.ost_io.threads_max`; LNet `peer_credits`/`credits`. Defaults are tuned for typical HPC; change one parameter at a time against a benchmark (IOR, mdtest, `fio`; 6.28).

### Diagnosing bottlenecks

1. **Is it metadata or data?** Compare `lctl get_param llite.*.stats` (open/getattr rates and latencies) with bandwidth per OST (server `obdfilter` stats, `lfs df`). Slow `ls -l`, slow Python imports, slow epoch starts, and thousands of `open` calls per second point to metadata. Low MB/s on a few large files points to striping or OST/network limits.
2. **Metadata-bound** remedies: reduce file counts (shard datasets into large files; WebDataset/TFRecord/Parquet shards, 6.18 section 5), avoid giant directories, spread trees across MDTs (DNE), add client caching (statahead), move metadata-heavy trees (Python environments, build trees) to containers or local disks, use Data-on-MDT for small files, increase MDS threads and use faster MDT media.
3. **Data-bound** remedies: raise stripe count for large files, align I/O size with stripe size, check client network (MTU, RDMA), OSS CPU/network, OST imbalance (`lfs df`), failing disks, rebuilds in progress, competing jobs.
4. **One slow client**: network (NIC link speed, errors, MTU), CPU/NUMA, client eviction history, `lctl ping`, `lnetctl stats`.
5. **Stalls and hangs**: check server logs for recovery/eviction, LNet errors, and OSS/MDS load; test from another client.

The NVIDIA-DevOps chapter's per-MDS and per-OST throughput figures ("about 50K to 100K metadata ops/s per MDS", "100 to 800 MB/s per OST") are illustrative orders of magnitude, not guarantees; real figures depend on hardware (flash MDTs achieve far more than spinning disks, NVMe OSTs far more than 800 MB/s). Measure your system.

## 7. AI-specific guidance

| Concern | Practice |
|---|---|
| Datasets | Few large shards (hundreds of MB to GB) per dataset; stripe count 4 to 16 (or PFL) on the dataset directory; read-ahead tuned; a pool on flash for hot datasets |
| Epoch start storms | Pre-shard; stagger; open files lazily; cache dataset index locally |
| Checkpoints | Distributed (per-rank or per-node shard) files with stripe count 1 to 4 each, **or** a few large shared files with wide striping (-c -1) and aligned writes; test both; use async checkpointing to local NVMe and drain to Lustre |
| Restart read | Same layout as writes; ensure enough OST bandwidth for a simultaneous read by all ranks |
| Python/conda environments | Do not run from Lustre at scale: containers (squashfs) or node-local copies; if unavoidable, `statahead` and metadata on flash |
| Logs | Per-rank files in per-job directories; avoid shared append files |
| Quotas | Project quotas per team/dataset; monitor inodes as well as bytes |
| Multi-tenant fairness | Network request scheduler (NRS) policies and QoS (TBF) exist in Lustre; use with care |
| Cloud | Managed Lustre services (e.g. on major clouds) expose the same client semantics; capacity and throughput are provisioned per TiB |

## 8. Lab

Tested: run `lustre_stripe.py`; change the stripe parameters and predict per-OST bytes; model a 4 GiB file with PFL `-E 1M -c 1 -E 1G -c 4 -E -1 -c 8`.

Untested (needs Lustre VMs): 1) Build a single-node Lustre (MGS+MDT, 2 OSTs on loop devices or small disks) following the `mkfs.lustre` examples; mount a client. 2) `lfs setstripe -c 2 -S 1M f`, write 1 GiB, `lfs getstripe f`, `lfs df`; compare with `-c 1`. 3) Set a directory PFL default; create small and large files; inspect layouts. 4) Create 100,000 files with `iomix.py` or `mdtest`; compare to NFS. 5) Add a second MDT and use `lfs mkdir -i 1`; observe `lfs getdirstripe`. 6) Set a project quota, exceed it, observe the error. 7) Run `lfs migrate -c 2 bigfile` while reading it. 8) Stop the OSS holding an OST and watch client behaviour and recovery; restart. 9) Write a runbook for evicted clients.

## 9. Interview angles

- Walk through what happens when a client opens and reads a striped file.
- Why is default stripe count 1 and when do you change it?
- Explain PFL layouts and a case for Data-on-MDT.
- Your checkpoint of 500 GB takes 15 minutes. How do you find and fix the cause?
- Epoch start takes minutes with 10 million files. What do you do?
- How do MGS, MDS, OSS fail over and what do clients experience?
- What are project quotas and why use them?
- How would you rebalance OSTs or evacuate one?
- Lustre versus GPFS versus WEKA/VAST: strengths and weaknesses?

## 10. Checkpoint questions (30)

1. Name Lustre's components and roles.
2. What is an NID and what does LNet do?
3. What backing file systems are used?
4. What is DNE?
5. What does the MDS store compared to the OSS?
6. Describe the read path of a file.
7. How does striping place chunks?
8. Why does a small read not benefit from striping?
9. Give the default stripe count and size in the development tree.
10. What does `-i -1` do?
11. Write the command for stripe count all OSTs, 4 MiB.
12. What is a composite (PFL) layout?
13. Explain `-E 4M -c 1 -E 64M -c 4 -E -1 -c -1`.
14. What is Data-on-MDT and when is it used?
15. What are OST pools for?
16. How do you stripe a directory across MDTs?
17. How do you set a project quota?
18. What does `lfs df` show and what imbalance signals trouble?
19. What TCP port does LNET use over IP, what are the book's two OSS RAM sizing formulas, and what commands deactivate and evacuate a retiring OST? **A:** On IP networks, LNET uses TCP port `988` (configured in `/etc/modprobe.d/lustre.conf`, e.g., `options lnet networks="tcp0(eth0)"`). For OSS memory sizing, each OST requires `400 MB` (logging) + `600 MB` (metadata caching) + `1.5 MB * N_threads` (where `N_threads` is roughly the number of clients divided by the number of connected OSTs), and total OSS RAM is recommended at `2 GB + 1 GB per OST` (plus extra for OS/network caching). To retire an OST, run `lctl dl` to find its device number `N`, run `lctl --device N deactivate` so Lustre stops allocating new objects on it, and migrate existing files off the OST using `lfs find --ost ...` and `lfs_migrate` (or `lfs migrate`).
20. What is Lustre recovery?
21. What is client eviction and its causes?
22. What is LFSCK?
23. Which commands show client-side operation statistics?
24. How do you distinguish metadata-bound from data-bound?
25. List four metadata-bound remedies.
26. List four data-bound remedies.
27. Why shard datasets?
28. Checkpoint layout options for N ranks?
29. Why are quoted per-MDS rates only illustrative?
30. What is mistaken about "a 2-stripe file is two halves"?

## 11. Sources and review notes

- Architecture, roles, LNET port `988`, OSS RAM sizing formulas (`400 MB + 600 MB + 1.5 MB * N_threads` and `2 GB + 1 GB per OST`), step-by-step Lustre creation (`mkfs.lustre`), OST retirement/deactivation (`lctl dl`, `lctl --device N deactivate`, `lfs_migrate`), fault tolerance, striping and PFL, quotas, and PanFS/GPFS context (read in full: `supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`, "9. Network File Systems" and "28. One-Two-Three Instructions"); the NVIDIA-DevOps volume-15 chapter 5 (metadata/data split, measurement, tuning, AI scenarios), restated in my words with corrections: contiguous-halves description of striping, "Metadata Disk Targets", "offline" migration, and unsupported throughput figures.
- Command semantics and defaults: Lustre manual pages `lfs-setstripe(1)`, `lfs-getstripe(1)`, `lfs-migrate(1)`, `lfs-setquota(1)`, `lfs-df(1)`, `lfs-project(1)`, `mkfs.lustre(8)`, `lctl(8)`, `lustre(7)` from lustre/lustre-release (commit `6325870`, development tree). Releases differ.
- Run here: `code/part06/lustre_stripe.py`.
- Not verified on live hardware: `mkfs.lustre`, `mount -t lustre`, `lnetctl`, `lctl`, `lfs` commands, tunable names, DNE default directory layout syntax, pool commands, recovery window values, sizing rules of thumb, managed-service details. Nothing was run against a live Lustre file system.
