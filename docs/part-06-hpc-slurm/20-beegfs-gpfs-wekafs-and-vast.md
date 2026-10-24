---
id: "c06-20"
title: "6.20 BeeGFS, GPFS, WekaFS and VAST"
sidebar_label: "6.20 BeeGFS, GPFS, WekaFS and VAST"
sidebar_position: 20
description: "The other parallel and scale-out file systems used on GPU clusters: BeeGFS (services, config, RDMA, BeeOND), IBM Storage Scale/GPFS, PanFS, WEKA and VAST, with architecture, strengths, limits, selection criteria, and a comparison with Lustre; claims checked against BeeGFS sources where possible"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.20 BeeGFS, GPFS, WekaFS and VAST

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | BeeGFS on 3 VMs (open source); the others are commercial |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. BeeGFS configuration parameters and the component layout were read from the ThinkParQ/beegfs repository (commit `f329583`, 2026-08-19: default `beegfs-client.conf`, `beegfs-meta.conf`, `beegfs-storage.conf`, README). GPFS/Storage Scale, PanFS, WEKA and VAST are described from the SCL book and general knowledge: **unverified**, vendor documentation must be consulted. Nothing was deployed. Labs **untested** |

## Why this matters for AI infrastructure

You will rarely get to choose the file system from scratch, but you will be asked to operate, size or compare them: a neocloud offering WEKA or VAST, a national lab on Lustre or GPFS, a university on BeeGFS, an appliance vendor shipping PanFS (VDURA). Each makes different trade-offs between metadata scaling, small-file performance, operational complexity, POSIX semantics, cost and ecosystem. The 6.19 chapter covered Lustre in depth; this one gives you the architecture, strengths and pitfalls of the alternatives, and the questions to ask. Part 13 (AI storage) revisits them for AI pipelines, checkpointing and GPUDirect Storage.

## Prerequisites and outcomes

Needs 6.18 and 6.19. After this chapter you can:

- Describe the architecture of BeeGFS, GPFS/Storage Scale, PanFS, WEKA and VAST in a few sentences each and map their components to Lustre's.
- Name the main configuration objects and commands of BeeGFS and read its configuration files.
- Compare the systems on metadata handling, data protection, client access, RDMA/GPUDirect, tiering, multi-tenancy and cost model.
- Pick a candidate for a scenario (checkpoint scratch, dataset store, home directories, mixed HPC) and list the validation tests.

## 1. A common frame

Every system answers the same design questions:

| Question | Why it matters |
|---|---|
| Where does metadata live and how does it scale (single, sharded, distributed everywhere)? | Small-file and create/stat rates, epoch-start storms |
| How is data distributed and protected (RAID on servers, replication, erasure coding, shared disk)? | Bandwidth, rebuild time, capacity efficiency, failure domains |
| How do clients access it (kernel client, FUSE, user-space client, NFS/SMB/S3 gateways)? | POSIX semantics, performance, OS/kernel support, operational friction |
| How is it deployed (software on commodity servers, appliance, managed service)? | Cost, lock-in, support |
| What media tiers (NVMe, HDD, object) and how are they managed? | Cost per TB versus per GB/s |
| Network (RDMA, TCP; GPUDirect Storage support)? | GPU data path (Part 13) |
| Multi-tenancy, quotas, snapshots, encryption, audit? | Shared AI platforms |
| Failure model and recovery | Availability during hardware failure and upgrades |

## 2. BeeGFS

BeeGFS (formerly FhGFS, developed at Fraunhofer, now ThinkParQ) is a parallel cluster file system "designed for very easy installation and management" (its README). It runs on ordinary Linux servers with a kernel client module, and its services are separable:

| Service | Role | Notes (from the repository layout and defaults) |
|---|---|---|
| **Management (mgmtd)** | Registry of nodes and targets, state, configuration; clients and servers find it via `sysMgmtdHost` | In BeeGFS 8 rewritten in Rust (`beegfs-rust`) |
| **Metadata (meta)** | Directory tree, file attributes, stripe pattern; `storeMetaDirectory` points to a fast local file system with extended attributes (`storeUseExtendedAttribs = true`) | Several metadata services can run; each directory is assigned to one, spreading the namespace across servers |
| **Storage** | File chunks on storage targets (`storeStorageDirectory`) | Targets are local file systems (XFS, ext4, ZFS) on RAID or NVMe; `tuneFileReadSize`, read-ahead parameters |
| **Client** | Kernel module `beegfs.ko` mounting at a path configured in `beegfs-mounts.conf` | `connUseRDMA = true` by default with `connTCPFallbackEnabled = true`; `connRDMABufNum`, `connRDMABufSize`; `tuneFileCacheType = buffered` (or native) |
| **CLI** | `beegfs-ctl` (classic), the new Go-based `beegfs` tool in BeeGFS 8 | Node and target listing, stripe settings, quotas, `--serverstats` |
| **Mon / helperd / fsck** | Monitoring (InfluxDB export), client helper, file system checker | |
| **BeeOND** | BeeGFS On Demand: spin up a temporary BeeGFS across the local SSDs of a job's nodes, giving a fast scratch private to the job | Good for staging datasets and checkpoints in training jobs |

Concepts: **striping** with a pattern per directory (chunk size and number of targets; `beegfs-ctl --setpattern --chunksize=1m --numtargets=4 /mnt/beegfs/dir`); **storage pools** (groups of targets, e.g. NVMe and HDD); **buddy mirroring** (replicated metadata/storage groups for high availability); quotas; ACLs; and security options added in recent versions (connection authentication via `connAuthFile = /etc/beegfs/conn.auth`, and TLS in newer releases).

Strengths: quick to install and operate, flexible hardware, good streaming performance, RDMA support, BeeOND, a small team can run it. Trade-offs reported by practitioners: metadata scaling and small-file performance generally trail Lustre-with-DNE and flash-native systems; failure handling and resyncs need care; support depends on the commercial agreement (ThinkParQ). Treat the NVIDIA-DevOps volume-15 chapter's numbers ("50K to 100K ops/s per metadata server", "500 MB/s to 2 GB/s per storage node") as illustrative; its sample `beegfs-client.conf` contains parameters (`tuneUseGDTLSConnPool` and similar) that do not appear in the default configuration file in the repository; use the shipped config files as the source of truth.

## 3. IBM Storage Scale (GPFS)

IBM Storage Scale, formerly Spectrum Scale and **GPFS** (General Parallel File System, originating in the 1990s), is a commercial parallel file system common in large HPC sites and enterprises. The SCL book covers it alongside Lustre. Key ideas (general knowledge; check IBM documentation):

- **Shared-disk heritage**: all nodes in a cluster can access all disks (**NSDs**, Network Shared Disks) directly or via NSD servers; no strict split into "metadata server" and "data server" roles: metadata is distributed across the cluster, and any node can act as a file system manager for certain functions.
- **Wide striping**: files are striped across all disks in a storage pool with large block sizes (multi-MiB) and subblocks to handle small files efficiently.
- **Storage pools and policies**: ILM-style policy engine moving files between pools (flash, HDD, tape) by rules on age, size, name, user.
- **Filesets** and quotas; snapshots; AFM (Active File Management) for caching/replication across sites; protocol nodes for NFS/SMB/S3 exports; erasure coding via **ESS (Elastic Storage System)** with declustered RAID; ECE (Erasure Code Edition) on commodity servers.
- **Strong POSIX semantics** through distributed locking (token management), which also makes some patterns (shared-file small writes) contention-prone.
- **Licensing**: per-client or per-capacity depending on edition (the book notes GPFS client drivers are licensed per client, in contrast to PanFS).
- Typical use in AI: very large HPC/AI centres with IBM relationships; used under NVIDIA SuperPOD-class reference designs as one of the validated options (verify current support matrices).

Operations vocabulary: `mmlscluster`, `mmlsconfig`, `mmgetstate -a`, `mmlsdisk`, `mmlsfs`, `mmcrfs`, `mmmount`, `mmlsmount`, `mmdf`, `mmlsquota`, `mmedquota`, `mmapplypolicy`, `mmhealth`. Dependencies: a quorum of cluster manager nodes, a cluster-wide configuration repository, tiebreaker disks, and kernel-module compatibility (portability layer builds per kernel).

## 4. PanFS (Panasas, now VDURA)

From the SCL book: a **hardware-software complex** (ActiveStor appliances plus client drivers, Linux only), another parallel file system with per-object RAID and the DirectFlow client protocol; NFS/CIFS access via re-export is possible but turns the re-exporting nodes into a bottleneck; client drivers are not licensed per client (unlike GPFS) and the driver does not use DKMS, so the set of compatible distributions/kernels is constrained. Appliance model: simple operation and a single support path; flexibility and price are the trade-offs. Company name: Panasas is now VDURA (per the book).

## 5. WEKA (WekaFS)

WEKA is a commercial, software-defined, NVMe-first distributed file system popular in AI and EDA (general knowledge, vendor-dependent details):

- Runs on commodity servers with NVMe; uses **user-space** drivers (SPDK/DPDK-style) to bypass the kernel, with a kernel/POSIX client (and also NFS, SMB, S3, and GPU-direct paths). Dedicated cores on each client and backend host run the WEKA data-plane threads, so CPU planning matters.
- **Metadata and data both distributed** across all backend servers (no dedicated metadata servers); aims at high small-file and metadata performance, flash-optimised data layout and distributed erasure coding (N+2/N+4 stripes).
- **Tiering to object storage** (S3-compatible) behind the flash tier for capacity; snapshots, snap-to-object; filesystem groups and quotas for multi-tenancy; encryption.
- Deployed on-prem and in clouds (often marketed as consistent across both); GPUDirect Storage supported on appropriate hardware.
- Cost model: software licence by capacity/cores plus NVMe server hardware; strong at "performance per rack", costly per TB at pure flash.

## 6. VAST Data

VAST Data's **Universal Storage** (DASE: Disaggregated, Shared-Everything architecture) is a commercial all-flash scale-out system (general knowledge, verify):

- **Disaggregation**: stateless compute nodes ("CNodes", containers) and NVMe storage enclosures ("DBoxes", with storage-class memory and QLC flash) connected through an NVMe-over-Fabrics network; all CNodes can access all media ("shared-everything"), so capacity and compute scale independently and there is no data partitioning between servers.
- **Protocols**: NFS (including NFS over RDMA and multi-path "nconnect"-style), SMB, S3, plus a database/analytics interface; the primary HPC/AI access is NFS, with a VAST client for multipathing; a POSIX-like kernel client is not required. Therefore it presents as "enterprise NAS speed with parallel-file-system bandwidth".
- **Data reduction**: global similarity-based reduction and wide erasure coding aimed at making QLC flash cost-efficient.
- Used in AI factories (reference architectures with NVIDIA), notably for dataset hosting; checkpoint absorption characteristics depend on configuration.

## 7. Comparison

(Qualitative, general; verify for the versions you evaluate.)

| | Lustre | GPFS / Storage Scale | BeeGFS | PanFS | WEKA | VAST |
|---|---|---|---|---|---|---|
| Licence / model | Open source; DIY or vendor-supported | Commercial software, appliances (ESS) | Open core, commercial support | Appliance (VDURA) | Commercial software on commodity | Commercial software + enclosures |
| Metadata | Dedicated MDS/MDT; DNE to scale out | Distributed | Dedicated meta services, spread by directory | Director blades | Distributed across all backends | Distributed, shared-everything |
| Data protection | Underlying RAID/ZFS, failover pairs | Declustered RAID (ESS), replication | Underlying RAID; optional buddy mirroring | Per-object RAID | Distributed EC | Wide EC |
| Client | Kernel (Linux only) | Kernel (multi-OS) | Kernel module | Kernel driver (Linux) | User-space/kernel POSIX, NFS/SMB/S3 | NFS/SMB/S3 (+RDMA) |
| Small files | Weak on HDD MDT, strong with flash MDT/DoM | Good, subblocks | Moderate | Good (flash) | Strong | Strong |
| RDMA / GDS | o2ib; GDS support in newer releases | RDMA; GDS support | RDMA (default on) | Limited | Yes | Yes (NFS RDMA) |
| Tiering | Pools, HSM | Pools, policy engine, AFM | Storage pools | Hybrid media | Flash + object | All-flash with data reduction |
| Operational skill | High | High | Low to medium | Low (appliance) | Medium | Low to medium |
| Typical fit | Large scratch for HPC and AI, national labs | Mixed HPC/enterprise, long-term data | Smaller clusters, university, BeeOND scratch | Legacy HPC appliance | AI/EDA performance tier | AI datasets, enterprise consolidation |

## 8. Selecting and validating

1. **Characterise the workload first**: checkpoint size and cadence, dataset format (shards vs small files), number of clients, read/write mix, metadata rate (creates and stats per second), latency sensitivity, POSIX needs. Use the arithmetic from 6.18.
2. **Short-list by constraints**: budget model (capex appliance vs software + hardware vs managed service), existing skills, support, ecosystem (reference architectures from the GPU vendor), network (RDMA fabric), data protection requirements, multi-tenancy.
3. **Prove it** with your own pipeline: `fio` (bandwidth, IOPS, latency, mixed), `IOR` (shared file and file-per-process), `mdtest` (metadata), an AI-realistic read job (your data loader on your dataset format) and a checkpoint job (synchronised all-rank writes at your target size), at the intended client count; test failure modes (kill a server, pull a drive, upgrade) while running load.
4. **Total cost**: capacity, performance (per GB/s), power and rack space, licences per client or core, support, growth steps, data egress.
5. **Plan tiers**: even the fastest system is rarely the only tier; combine with local NVMe, object storage, and NFS for home directories (6.18 section 8).

## 9. Lab

Untested (BeeGFS is open source and installable on three VMs):

1. Install BeeGFS management, one metadata and two storage services and a client on small VMs; read `beegfs-meta.conf` and `beegfs-storage.conf`; mount the client.
2. Create a directory, set a stripe pattern (4 targets, 512k chunks), write a large file, inspect with `beegfs-ctl --getentryinfo`.
3. Run `fio`/`iomix.py` (6.18) against BeeGFS and an NFS export on the same VMs; compare data and metadata rates.
4. Disable `connUseRDMA` / `connTCPFallbackEnabled` on a lab with Soft-RoCE to see transport selection logs.
5. Try BeeOND on two nodes using local disks as a job-private scratch.
6. Write a comparison worksheet for two candidate file systems for a hypothetical 1,024-GPU cluster using the questions in section 1, and list the validation tests you would run.

## 10. Interview angles

- Compare Lustre, GPFS, BeeGFS, WEKA and VAST for a new 2,000-GPU training cluster.
- What is BeeOND and when is it useful?
- Why is metadata the usual differentiator for AI data loading?
- What does "disaggregated, shared-everything" mean in VAST's architecture?
- What does user-space IO give WEKA and what does it cost?
- How would you validate a vendor's performance claims before purchase?
- What happens to throughput during a drive failure or rebuild in each system?
- Which file system fits a university cluster of 200 nodes with a two-person admin team?

## 11. Checkpoint questions (25)

1. Name BeeGFS's services and their roles.
2. What does `sysMgmtdHost` configure?
3. What do `connUseRDMA` and `connTCPFallbackEnabled` do?
4. What is BeeOND?
5. How does BeeGFS stripe and what are buddy groups?
6. What changed in BeeGFS 8 regarding management and CLI?
7. What is an NSD in GPFS?
8. How does GPFS differ from Lustre structurally?
9. What is the policy engine for?
10. What is AFM?
11. What is ESS?
12. What are PanFS's notable licensing and kernel constraints?
13. What does WEKA's architecture require of client and server CPUs?
14. How does WEKA tier to object storage?
15. Define DASE and its CNode/DBox parts.
16. Which protocols does VAST primarily expose?
17. Which of the five systems are open source?
18. Which require dedicated metadata servers?
19. How would you test small-file performance?
20. Which test emulates synchronised checkpoint writes?
21. What are the cost drivers beyond capacity?
22. Why combine several tiers?
23. Which questions belong in a selection checklist?
24. Why distrust vendor numbers measured on different client counts?
25. What did this chapter correct in the source notes?

## 12. Sources and review notes

- BeeGFS: ThinkParQ/beegfs repository (README, default configuration files, component layout) at commit `f329583`; NVIDIA-DevOps volume-15 chapter 6 for the framing, with its configuration parameters and numeric claims not carried over (they do not match the shipped configuration files, and the throughput numbers are illustrative).
- GPFS/IBM Storage Scale, PanFS, Lustre comparison and "other file systems": *Supercomputers for Linux SysAdmins* chapter 9, restated; additional GPFS, WEKA and VAST statements from general knowledge, flagged unverified.
- Further volume-15 chapters (AI data path, local NVMe staging, GPUDirect Storage, object storage and dataset pipelines) are covered in Part 13, which is their natural home.
- Original: the comparison frame, the selection and validation method, the correction notes.
- Unverified: all commercial product details (licensing, ports, versions, feature lists), BeeGFS 8 specifics beyond the README, GPFS command list.
