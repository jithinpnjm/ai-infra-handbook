---
id: "c06-04"
title: "6.4 MPI in practice: Open MPI, ranks, collectives and tuning"
sidebar_label: "6.4 MPI in practice: Open MPI, ranks, collectives and tuning"
sidebar_position: 4
description: "Using MPI on a cluster: ranks and communicators, point-to-point and collective operations, thread levels, Open MPI architecture (MCA, PML/BTL, UCX), launching with mpirun and srun, mapping and binding, tuning, CUDA-aware MPI, benchmarking, and diagnosing hangs and slow collectives"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.4 MPI in practice: Open MPI, ranks, collectives and tuning

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop with an MPI implementation; ideally two or more nodes |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Honest test record: I installed Open MPI 5.0.11 and MPICH (conda-forge, isolated environments) on an Apple Silicon Mac. Single-process (singleton) MPI initialisation and `mpirun` of non-MPI programs worked, and the lab scripts compile and ran with one rank. **Multi-rank MPI runs hung inside `MPI_Init` in my sandboxed shell with both implementations**, so I could not produce multi-rank output. The multi-rank labs are therefore **untested**; section 11 turns that failure into a troubleshooting lesson |

## Why this matters for AI infrastructure

MPI is the substrate of HPC and still the launch and bootstrap layer for much of distributed AI. Even when training uses NCCL for GPU collectives, jobs are often started by `mpirun` or by Slurm with PMIx, bootstrapped through MPI-style rank and size information, and benchmarked with MPI tools (OSU micro-benchmarks, `nccl-tests` built against MPI). An operator needs to understand ranks, communicators, the transport stack (UCX over InfiniBand or RoCE), process placement and binding, and how to tell a hang from a slow collective. Most "the job does not start / hangs at initialisation / is slower than last week" tickets come down to the topics in this chapter.

## Prerequisites and outcomes

Needs 6.3 and Part 2 (networking). After this chapter you can:

- Write and read small MPI programs (C or `mpi4py`): initialise, find rank and size, send/receive, reduce, broadcast, barrier.
- Explain eager versus rendezvous protocols, blocking versus non-blocking calls, and the common deadlock patterns.
- Choose thread support levels correctly for hybrid MPI+threads.
- Describe Open MPI's component architecture (MCA) and select transports; use `ompi_info`.
- Launch jobs with `mpirun` and with `srun`; control mapping, ranking and binding and verify them.
- Measure latency and bandwidth with ping-pong and OSU-style tests and interpret results with the `alpha + m/beta` model.
- Diagnose the usual failure modes: init hangs, wrong interface, mismatched libraries, slow collectives.

## 1. The MPI model

An MPI program is **SPMD**: the same executable runs as many *processes* (ranks), each with its own address space. They cooperate by passing messages.

- **Communicator**: a group of ranks plus a communication context. `MPI_COMM_WORLD` contains all ranks of the job. You can split it (`MPI_Comm_split`) to make sub-communicators, for example one per node (`MPI_Comm_split_type` with shared-memory type) or per row of a process grid.
- **Rank**: integer identity within a communicator, `0..size-1`. **Size**: the number of ranks.
- **Local rank** is not an MPI concept but is derived (rank within the node), used to pick a GPU (`cudaSetDevice(local_rank)`), typically obtained from a node-local communicator or from Slurm's `SLURM_LOCALID`.
- **Tags** match sends to receives; **datatypes** describe memory layout (`MPI_DOUBLE`, derived types for strided or structured data).

The standard is defined by the MPI Forum; implementations (Open MPI, MPICH and its derivatives MVAPICH2, Intel MPI, Cray MPICH, HPE and NVIDIA HPC-X builds of Open MPI) conform to it. The ABI differs between implementations: **a binary built against one is not generally usable with another** (an MPI ABI effort is under way for MPI 5; check current status).

### A minimal program

In Python with `mpi4py` (`code/part06/mpi_hello.py`):

```python
from mpi4py import MPI
comm = MPI.COMM_WORLD
print(f"rank {comm.Get_rank()} of {comm.Get_size()} on {MPI.Get_processor_name()}")
```

Run with `mpirun -np 4 python mpi_hello.py`; each of four processes prints its own rank. In C the equivalent uses `MPI_Init`, `MPI_Comm_rank`, `MPI_Comm_size`, `MPI_Finalize`, compiled with the wrapper `mpicc` and run with `mpirun` or `srun`.

## 2. Point-to-point communication

- **Blocking**: `MPI_Send` / `MPI_Recv`. `MPI_Send` may return once the buffer is reusable, which can mean "copied into a system buffer" (small messages, **eager protocol**) or "receiver has posted a matching receive" (large messages, **rendezvous protocol**). Code that relies on `Send` buffering works for small messages and deadlocks for large ones: two ranks that both `Send` first to each other is the classic example. Fix with ordered send/recv, `MPI_Sendrecv`, or non-blocking calls.
- **Non-blocking**: `MPI_Isend` / `MPI_Irecv` return a request; later `MPI_Wait` / `MPI_Test`. They let you overlap communication with computation (only if the library progresses the transfer in the background, which depends on the implementation and hardware).
- **Synchronous and buffered modes**: `MPI_Ssend` completes only after the receiver has started; `MPI_Bsend` uses a user buffer.
- **Matching rules**: by communicator, source, tag, in order per pair. `MPI_ANY_SOURCE` makes results timing-dependent.
- **Persistent requests** reuse setup for repeated patterns (halo exchanges).

The **eager limit** (message size below which eager is used) is tunable per transport; it trades memory for latency.

Ping-pong measures latency and bandwidth: two ranks bounce a message; half the round trip is the one-way time. The handbook script `code/part06/mpi_pingpong.py` sweeps message sizes and prints one-way time and MB/s. Fit `T(m) = alpha + m / beta` (6.3): `alpha` from the smallest message, `beta` from the largest. On shared memory expect around a microsecond or less and many GB/s; on InfiniBand HDR/NDR a few microseconds between nodes and tens of GB/s per link; on TCP Ethernet tens of microseconds. (Ranges from experience, not measured here: see the test record above.)

## 3. Collective communication

All ranks of a communicator call the collective with consistent arguments. Main operations:

| Operation | Effect | AI analogue |
|---|---|---|
| `MPI_Barrier` | Synchronise | |
| `MPI_Bcast` | Root sends data to all | Broadcast initial weights |
| `MPI_Reduce` / `MPI_Allreduce` | Combine (sum, max, ...) to root / to all | Gradient all-reduce |
| `MPI_Gather` / `MPI_Allgather` | Collect pieces to root / to all | Parameter all-gather (sharded training) |
| `MPI_Scatter` | Distribute pieces | |
| `MPI_Reduce_scatter` | Reduce then scatter | ZeRO/FSDP gradient reduce-scatter |
| `MPI_Alltoall(v)` | Everyone sends distinct data to everyone | Expert-parallel token routing, FFT transpose |

Why they matter operationally: collectives are **where scaling happens or fails**, are implemented with algorithms selected by message size and rank count (binomial tree, ring, recursive doubling, Rabenseifner, hierarchical node-aware variants), and are the part of MPI most sensitive to fabric topology and tuning. Non-blocking collectives (`MPI_Iallreduce`) allow overlap. Hardware-assisted collectives exist (NVIDIA SHARP in-network reduction on InfiniBand through the HCOLL library; Part 12).

Correctness rules: **every rank in the communicator must call the collective, in the same order, with matching counts and types**. Mismatches produce hangs or corrupted data. Floating-point reductions are not bit-reproducible across different rank counts or algorithms (addition is not associative); if you need reproducibility, choose a deterministic algorithm and fixed layout.

The script `code/part06/mpi_allreduce.py` checks an all-reduce sum (`size*(size+1)/2` for ranks contributing `rank+1`) and times all-reduce of 1 to 8 million floats. With a single rank it printed:

```text
ranks=1 sum check ok: 1
    floats        ms
         1     0.001
      1000     0.001
   1000000     0.228
   8000000     1.363
```

(With one rank this is only a local copy; it demonstrates the script runs and the arithmetic check, not communication.)

## 4. One-sided communication, MPI-IO, and other features

- **One-sided (RMA)**: `MPI_Put`, `MPI_Get`, windows and synchronisation; maps well to RDMA hardware; used by PGAS-style codes.
- **MPI-IO**: collective parallel file access (`MPI_File_write_at_all`) used by HDF5 and checkpoint libraries on Lustre/GPFS (6.21).
- **Process management**: `MPI_Comm_spawn`; rarely used on schedulers.
- **Persistent collectives, partitioned communication** in newer standards.
- **Profiling interface (PMPI)**: lets tools intercept every call; used by tracers.

## 5. Threads and hybrid programs

`MPI_Init_thread` requests a level:

| Level | Meaning |
|---|---|
| `MPI_THREAD_SINGLE` | One thread only |
| `MPI_THREAD_FUNNELED` | Multithreaded, but only the main thread calls MPI |
| `MPI_THREAD_SERIALIZED` | Any thread may call MPI, but never concurrently |
| `MPI_THREAD_MULTIPLE` | Any thread, any time |

Use the lowest level you need: higher levels add locking overhead inside the library. The common pattern, communication in the main loop and OpenMP threads for compute loops, needs only FUNNELED. Check the level actually granted (it can be lower than requested). With hybrid codes, set threads (`OMP_NUM_THREADS`) and binding so that threads of one rank stay within a socket or NUMA domain.

### MPI implementations compared

| Implementation | Origin and character | Typical use |
|---|---|---|
| **Open MPI** | Community project; modular (MCA); strong UCX/OFI support; the base of NVIDIA HPC-X | Default on many clusters; most AI-cluster tooling assumes it |
| **MPICH** | Reference implementation from Argonne; many vendor derivatives | Portable baseline; base of MVAPICH2, Intel MPI and Cray MPICH |
| **MVAPICH / MVAPICH2** | Ohio State University; MPICH-derived; very tuned for InfiniBand and GPUs | Research and HPC sites with InfiniBand |
| **Intel MPI** | Proprietary, MPICH-based, part of oneAPI | Intel-centric clusters |
| **Cray MPICH / HPE** | MPICH-derived, tuned for Slingshot and Cray systems | HPE Cray systems |
| **IBM Spectrum MPI** | Proprietary, Open MPI-based; tied to IBM systems | Legacy IBM POWER machines (largely historic) |
| **NVIDIA HPC-X** | Open MPI + UCX + HCOLL + SHARP bundle | NVIDIA InfiniBand clusters |

Choose one implementation per software stack, build every dependency against it, and record it in the module or container name (6.6); mixing implementations is the most common cause of mysterious start-up failures. The wrappers `mpicc`, `mpicxx`, `mpifort` supply the right compiler flags and libraries; `mpicc --showme` (Open MPI) or `mpicc -show` (MPICH) prints the underlying command.

## 6. Open MPI architecture and tuning

Open MPI is built from the **Modular Component Architecture (MCA)**: frameworks (functional areas) with interchangeable components chosen at run time. The ones you meet most:

| Framework | Role | Notes |
|---|---|---|
| `pml` | Point-to-point messaging layer | `ob1` (generic, uses BTLs), `ucx` (UCX transport), `cm` (uses MTLs, for libfabric/OFI) |
| `btl` | Byte transfer layer used by `ob1` | `self`, shared-memory (`vader` in 4.x, named `sm` in 5.x, from memory), `tcp`, and others; legacy `openib` removed in Open MPI 5 |
| `mtl` | Matching transport layer | OFI/libfabric |
| `coll` | Collective algorithms | `tuned`, `hcoll` (NVIDIA), `han` (hierarchical), `libnbc` (non-blocking) |
| `osc` | One-sided | |
| `io` | MPI-IO | `romio`, `ompio` |
| `rte`/PRRTE/PMIx | Runtime and process management | In Open MPI 5 `mpirun` is `prterun`; I observed this directly (`ps` showed `prterun`) |

Inspect and set parameters:

```bash
ompi_info                       # version, frameworks, components
ompi_info --param pml ucx --level 9      # parameters of a component
mpirun --mca pml ucx --mca btl ^openib,smcuda ...     # command line
export OMPI_MCA_pml=ucx                                # environment
# or ~/.openmpi/mca-params.conf, or the system-wide openmpi-mca-params.conf
```

The `^` prefix excludes components. As listed in Chapter 21 of the SCL book, Open MPI evaluates MCA parameters in five levels of increasing priority:

1. Global configuration file (`/etc/openmpi-mca-params.conf`, with `key=value` lines; PMIx and PRRTE parameters can use `openpmix-mca-params.conf` or `prte-mca-params.conf`).
2. User configuration file (`$HOME/.openmpi/mca-params.conf`).
3. Tuned option files passed via `mpiexec --tune file1,file2...` `(untested here)`.
4. Environment variables (`export OMPI_MCA_xxx=value`, or `PMIX_MCA_` and `PRRTE_MCA_` for PMIx/PRRTE).
5. Command-line flags (`mpiexec -mca xxx value`).

**HCOLL (Host Collectives)** is NVIDIA's collective library used by Open MPI to offload or accelerate MPI collectives over InfiniBand (including hardware multicast and SHARP in-network reductions). You can enable, disable, or steer HCOLL via MCA flags and environment variables `(untested here)`:

```bash
# Enable or disable HCOLL on the command line or via environment (for srun --mpi=pmix) (untested here)
mpiexec -mca coll_hcoll_enable 1 ... myprog
mpiexec -mca coll_hcoll_enable 0 ... myprog
export OMPI_MCA_coll_hcoll_enable=0
srun --mpi=pmix ... myprog

# HCOLL and UCX environment controls passed with -x (untested here)
-x HCOLL_MAIN_IB=mlx5_0:1        # force HCOLL to use a specific InfiniBand HCA:port
-x HCOLL_ENABLE_MCAST_ALL=1      # enable hardware multicast for HCOLL collectives
-x HCOLL_ENABLE_NBC=1            # enable non-blocking collectives in HCOLL
-x HCOLL_ENABLE_SHARP=1          # enable in-network SHARP collective offload
-x OMPI_MCA_pml=^ucx             # disable UCX PML if troubleshooting a UCX issue
```

**UCX** (Unified Communication X) is the preferred path on InfiniBand and RoCE with Open MPI (for example `mpirun -np 2 -mca pml ucx -x UCX_NET_DEVICES=mlx5_0:1 ./myapp` `(untested here)`). Its own environment variables select transports and devices: `UCX_TLS` (for example `rc,ud,sm,self,cuda_copy,cuda_ipc,gdr_copy`), `UCX_NET_DEVICES` (for example `mlx5_0:1`), `UCX_IB_GID_INDEX` (RoCE), `UCX_LOG_LEVEL`. Use `ucx_info -d` to list devices and transports, and `ucx_info -c` (or `ucx_info -c -f` for full descriptions) `(untested here)` to list all UCX configuration variables. NVIDIA's HPC-X is a tuned Open MPI + UCX + HCOLL bundle.

Typical tuning questions and where to look:

- **Wrong network used** (TCP over management Ethernet instead of InfiniBand): force `pml ucx`, restrict interfaces (`btl_tcp_if_include`, `UCX_NET_DEVICES`), verify with `UCX_LOG_LEVEL=info` and measured bandwidth.
- **Collectives slow at scale**: try `coll_hcoll_enable`, hierarchical collectives, different algorithm selection (`coll_tuned_*` parameters), proper process placement.
- **Memory use at large rank counts**: connection setup per peer; use dynamically connected transports (UCX DC) and adjust.
- **Launch time**: `plm_rsh_no_tree_spawn`, `routed_radix`, PMIx wire-up settings. Large jobs are faster to start under Slurm with PMIx than via `ssh`.

From the NVIDIA-DevOps volume-10 notes merged into this chapter, a typical bare-metal AI launch looks like:

```bash
mpirun -np 16 -hostfile hosts.txt \
  --bind-to none --map-by slot \
  -x NCCL_DEBUG=INFO -x LD_LIBRARY_PATH -x PATH \
  --mca pml ucx --mca btl ^openib \
  --mca btl_tcp_if_include enp1s0f0 \
  python3 train.py
```

Points worth keeping: `-x VAR` exports an environment variable to remote ranks (without it remote processes do not see it); `--bind-to none` stops Open MPI's default binding from confining a rank's helper threads (data loaders) to a single core, which suits PyTorch jobs but is wrong for tightly tuned MPI codes; `--mca btl ^openib` is only relevant to old Open MPI versions; `coll_hcoll_enable` applies to MPI collectives, not to NCCL collectives. Treat command lines copied from blog posts as starting points and re-derive them against your Open MPI version's documentation.

## 7. Launching: mpirun, srun, and PMIx

Two launch models:

1. **`mpirun`** (the MPI implementation's own launcher): starts daemons on the allocated nodes (via the scheduler's launch support or `ssh`), then the ranks. Within a Slurm allocation, Open MPI detects Slurm and uses it to launch daemons.
2. **`srun`** (Slurm launches the ranks directly): `srun --mpi=pmix -n 64 ./a.out`. Slurm's PMIx plugin provides the wire-up information (ranks, sizes, locations) to the MPI library, avoiding an extra daemon layer and giving Slurm full control of binding and accounting. This is the usual choice on Slurm clusters (6.12). `srun --mpi=list` shows supported plugin types. The MPI library must be built with PMIx support compatible with Slurm's.

Both ways, ranks need: consistent MPI library versions on all nodes (same path, usually on shared storage or in a container), the same environment, working name resolution and network interfaces, and a PMIx/runtime wire-up that can reach every node.

## 8. Mapping, ranking and binding

Three separate decisions:

- **Mapping**: which node/socket/core each rank is placed on (`--map-by slot|node|socket|numa|ppr:N:node`).
- **Ranking**: which rank number each placement gets (`--rank-by`).
- **Binding**: restrict each process to a set of cores (`--bind-to core|socket|numa|none`), so the OS scheduler cannot migrate it away from its cache and local memory.

Always verify instead of assuming: `mpirun --report-bindings ...` prints each rank's binding. The affinity chapter of *Parallel and High Performance Computing* shows the classic traps: placing two ranks on the two hardware threads of one core (they then share the core's cache and units), leaving the default binding in place for threaded code, or binding all threads of a rank to one core. For GPU jobs map ranks to the NUMA domain closest to their GPU (`nvidia-smi topo -m`; Part 10). Under Slurm use `--cpu-bind`, `--gpu-bind`, `--ntasks-per-node`, `--cpus-per-task`, `--distribution` (6.11, 6.12).

Rules of thumb: one rank per GPU for GPU codes; one rank per NUMA domain with threads inside for memory-bound CPU codes; do not oversubscribe cores unless intentionally (`--oversubscribe` is needed for more ranks than slots on a laptop, and performance is then meaningless).

## 9. CUDA-aware MPI and GPUDirect

A **CUDA-aware** MPI accepts GPU device pointers in `MPI_Send/Recv` and collectives. With **GPUDirect RDMA**, the NIC reads and writes GPU memory directly, skipping a host copy. Requirements: CUDA-aware build of the MPI/UCX, the `nvidia-peermem` (or DMA-BUF) kernel path, supported topology (GPU and NIC under the same PCIe switch for best performance). Check support with `ompi_info --parsable --all | grep mpi_built_with_cuda_support`. Most AI jobs bypass this and use NCCL, but CUDA-aware MPI remains important for simulation codes and some AI libraries (Part 10, 12).

## 10. Benchmarking

- **Ping-pong** (section 2) for latency and bandwidth.
- **OSU Micro-Benchmarks** (`osu_latency`, `osu_bw`, `osu_allreduce`, `osu_alltoall`, with CUDA variants): the standard way to compare fabrics and MPI builds. Run intra-node and inter-node, and at several node counts.
- **Intel/IMB**, **`nccl-tests`** for GPU collectives (Part 12, 6.28).
- Method: warm up, repeat, report median and spread; pin the placement; test both a pair of nodes and the full allocation; record versions and environment variables. Compare against the theoretical line rate (for example 400 Gb/s NDR is about 50 GB/s per direction before overheads); a result far below indicates misconfiguration (wrong NIC, TCP fallback, PCIe link downtrained, bad cable).

## 11. When it does not work: a troubleshooting guide

I hit the first of these myself, so it comes with a record.

**Symptom: multi-rank job hangs in `MPI_Init`.** What I observed: on macOS in a sandboxed shell, both Open MPI 5.0.11 and MPICH launched processes (`mpirun -np 2 hostname` printed twice, a single-rank `mpi4py` initialisation succeeded) but any 2+-rank `MPI_Init` never returned. I tried: shorter `TMPDIR` (`/tmp`, to keep Unix socket paths short), restricting transports to `self,sm` or `self,vader`, restricting the out-of-band interface to `lo0` (which failed with "No network interfaces were found for out-of-band communications"), PMIx `gds=hash`, MPICH without shared-memory locality and with the TCP libfabric provider. None worked, which suggests an environment restriction (the sandbox likely blocks some inter-process mechanism the wire-up needs) rather than an MPI configuration error; I did not confirm the root cause. The lesson for clusters is the diagnostic *method*:

1. Does the launcher itself work for a non-MPI program (`mpirun -np 2 hostname`)? If yes, the launch path (ssh, Slurm) is fine.
2. Does a singleton (1 rank) initialise? If yes, the library loads.
3. Does a 2-rank job on one node initialise? That tests shared-memory and local wire-up.
4. Does a 2-rank job across two nodes initialise? That tests the network, name resolution and firewalls.
5. Raise verbosity (`--mca pmix_base_verbose`, `--mca btl_base_verbose`, `UCX_LOG_LEVEL=debug`, `srun --mpi=pmix` with `SLURM_DEBUG`), and look at which step the last message belongs to.

**Other frequent causes** (from experience and the references): wrong or multiple network interfaces (the library picks a Docker bridge or a management NIC; restrict with `*_if_include`); firewalls blocking the dynamic ports MPI uses between nodes (open the range or use the fabric); hostname not resolving consistently; mismatched MPI versions between nodes or between `mpirun` and the linked `libmpi` (check `ldd`, `which mpirun`, `ompi_info --version` on each node); stale daemons or temp files from a previous failed run; a node with a dead fabric port (the hang is "waiting for the missing rank"); `OMPI_*` or `PMIX_*` environment variables leaking from a container or a different module; running under a scheduler without the right `--mpi` plugin.

**Symptom: job runs but slowly.** Check which transport is in use, binding (`--report-bindings`), CPU frequency and thermal state, a single slow node (compare per-rank timings, or run a node-by-node benchmark), fabric errors (`ibstat`, `perfquery`, switch counters; Part 12), and storage if the job does I/O.

**Symptom: wrong results or crash at scale only.** Uninitialised data, rank-count-dependent algorithms, floating-point reduction order, memory growth with peers, buffer sizes. Use sanitizers, MPI correctness tools (MUST, Marmot) and a small-scale reproducer.

## 12. MPI and NCCL

NCCL covers GPU collectives (all-reduce, all-gather, reduce-scatter, broadcast, all-to-all, send/recv) with topology-aware ring/tree algorithms over NVLink, PCIe and InfiniBand/RoCE; it has no point-to-point matching semantics like MPI and runs inside CUDA streams. PyTorch and most training stacks use NCCL for tensor traffic and use MPI (or a TCP/c10d store, or Slurm environment variables) only to exchange rank and address information at start-up. Many HPC codes mix them: MPI for the application, NCCL for GPU-resident reductions.

When multi-NIC nodes need explicit interface selection in NCCL (`NCCL_SOCKET_IFNAME` for IP bootstrap/socket interfaces or `NCCL_IB_HCA` for RDMA HCAs), Chapter 21 of the SCL book summarizes the four prefix-matching operators (multiple entries can be comma-separated) `(untested here)`:

- **Plain string (prefix match)**: `eth` matches every interface whose name starts with `eth` (`eth0`, `eth1`, `eth11`).
- **`=` prefix (exact match)**: `=eth1` matches only `eth1` and does not match `eth11`.
- **`^` prefix (exclude prefix)**: `^docker` matches all interfaces except those starting with `docker`.
- **`^=` prefix (exclude exact)**: `^=eth0` matches all interfaces except `eth0` specifically.

Key NCCL environment variables highlighted in the book for debugging and fabric tuning `(untested here)`:

- `NCCL_DEBUG` — diagnostic verbosity (`INFO` is recommended when debugging).
- `NCCL_SOCKET_IFNAME` — list of IP network interfaces used for bootstrap and socket communication.
- `NCCL_IB_HCA` — list of RDMA (InfiniBand/RoCE) HCAs to use.
- `NCCL_IB_TIMEOUT` — timeout for InfiniBand/RDMA operations.
- `NCCL_IB_RETRY_CNT` — number of RDMA retries before reporting failure.
- `NCCL_IB_SL` / `NCCL_IB_TC` — InfiniBand Service Level and Traffic Class (important on QoS-configured IB and RoCE fabrics).
- `NCCL_TOPO_FILE` — path to an explicit XML PCI/network topology file when automatic topology detection is wrong.

Chapters 6.12 and Part 12 and 14 go deeper; verify any variable against the NCCL version you run.

## 13. Lab

Parts marked (tested) were run as described in the status box; the rest are untested.

1. (tested, single rank) Install Open MPI or MPICH and `mpi4py` in a Conda environment. Run `mpi_hello.py` with one process; run `mpirun -np 2 hostname`; run `ompi_info | head`.
2. (untested multi-rank) `mpirun -np 4 python code/part06/mpi_hello.py`, then `--report-bindings`, then `--bind-to none`. Compare bindings.
3. (untested) `mpirun -np 2 python code/part06/mpi_pingpong.py` on one node and across two nodes. Fit alpha and beta.
4. (untested) `mpi_allreduce.py` with 2, 4, 8 ranks; plot time vs size. Which sizes are latency-bound?
5. (untested) Under Slurm: `srun --mpi=list`; then `srun --mpi=pmix -N2 -n8 python mpi_hello.py`; compare with `mpirun` inside `salloc`.
6. (untested) Write a deliberately deadlocking program (both ranks `Send` large messages first), observe, then fix it with `Sendrecv`.
7. Build OSU micro-benchmarks and run `osu_latency` / `osu_bw` intra- and inter-node; record versions and flags.
8. Write a one-page checklist titled "MPI job will not start" using the diagnostic ladder of section 11.

## 14. Interview angles

- What are ranks and communicators? How do you get a per-node rank?
- Eager versus rendezvous: why can code that works for small messages deadlock for large ones?
- `mpirun` versus `srun --mpi=pmix`: what does PMIx do?
- What is the MCA? How do you force Open MPI to use UCX and exclude TCP?
- How do you check process binding, and what goes wrong with the default binding in a hybrid job?
- A job hangs at start on 64 nodes but works on 8. What do you check?
- Name three common reasons a collective is slow.
- What is CUDA-aware MPI? What does GPUDirect RDMA change?
- How do MPI and NCCL relate in a PyTorch training job?

## 15. Checkpoint questions (30)

1. What is a communicator and what is `MPI_COMM_WORLD`?
2. Define rank, size and local rank.
3. Why is an MPI binary tied to its MPI implementation?
4. Explain eager versus rendezvous.
5. Give the classic send-send deadlock and two fixes.
6. When does non-blocking communication actually overlap computation?
7. List five collectives and their AI analogues.
8. What must all ranks agree on when calling a collective?
9. Why are floating-point reductions not reproducible across layouts?
10. State the four MPI thread levels and which suits an OpenMP main loop.
11. What is the MCA and where do parameters come from, in precedence order?
12. Name the roles of PML, BTL and COLL.
13. What does the `^` prefix do?
14. How do you list the transports UCX sees?
15. Which UCX variable restricts devices? Which selects transports?
16. In Open MPI 5, what is `mpirun`?
17. What does `srun --mpi=pmix` change versus `mpirun`?
18. Define mapping, ranking and binding.
19. How do you verify bindings?
20. Why might `--bind-to none` be right for a PyTorch job and wrong for a stencil code?
21. What does `-x` do?
22. What is HCOLL, what do `-mca coll_hcoll_enable 1`, `HCOLL_MAIN_IB`, and `HCOLL_ENABLE_MCAST_ALL` control, and what do the four `NCCL_SOCKET_IFNAME` prefix operators (`eth`, `=eth1`, `^docker`, `^=eth0`) match? (Answer: HCOLL accelerates MPI collectives on InfiniBand; `-mca coll_hcoll_enable 1` enables it, `HCOLL_MAIN_IB` selects the HCA:port, and `HCOLL_ENABLE_MCAST_ALL` enables hardware multicast; in `NCCL_SOCKET_IFNAME`, a plain string matches a prefix, `=` matches an exact name, `^` excludes a prefix, and `^=` excludes an exact name.)
23. What is CUDA-aware MPI and how do you check for it?
24. Give three benchmark tools and what each measures.
25. Describe the five-step diagnostic ladder for an init hang.
26. List four causes of init hangs on clusters.
27. How do you find which MPI library a binary actually loads?
28. What would you check for a job slower than yesterday?
29. How do MPI and NCCL divide responsibility in training?
30. What did the author's failed multi-rank test suggest, and what does it not prove?

## 16. Sources and review notes

- Book source (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`):
  - Chapter `21. Compilers and Environments, for Parallel Technologies` (read in full): MPI implementations (`mpich`, `OpenMPI`, `Mvapich`/`Mvapich2` `mpirun_rsh`, `Spectrum MPI`, `IntelMPI`), `PMIx` (`srun --mpi=list`), OpenMPI MCA five-level parameter priority (`/etc/openmpi-mca-params.conf`, `$HOME/.openmpi/mca-params.conf`, `--tune`, `OMPI_MCA_`, `-mca`), `HCOLL` controls (`-mca coll_hcoll_enable`, `HCOLL_MAIN_IB`, `HCOLL_ENABLE_MCAST_ALL`, `HCOLL_ENABLE_NBC`, `HCOLL_ENABLE_SHARP`), `UCX` (`UCX_NET_DEVICES`, `ucx_info -c -f`), and `NCCL` interface prefix matching (`=`, `^`, `^=`) and environment variables (`NCCL_DEBUG`, `NCCL_SOCKET_IFNAME`, `NCCL_IB_HCA`, `NCCL_IB_TIMEOUT`, `NCCL_IB_RETRY_CNT`, `NCCL_IB_SL`, `NCCL_IB_TC`, `NCCL_TOPO_FILE`).
- Concepts, affinity, mapping and binding, threading levels: *Parallel and High Performance Computing* (Robey and Zamora, Manning), chapters 8 and 14 (in the corpus; used for thread levels and the placement/binding pitfalls).
- Launch commands, HPC-X/MCA parameters and NCCL notes: the author's NVIDIA-DevOps volume-10 chapter 7 (`mpirun`, `srun --mpi=pmix`, `-x`, `--bind-to none`, MCA parameters, HCOLL), re-checked for obvious version issues (legacy `openib`).
- Open MPI facts: 5.x runs `prterun` (observed); `vader` renamed `sm` and `openib` removed in v5 (from memory, verify with `ompi_info` on your version).
- Original: the three scripts under `code/part06/` (syntax-checked; single-rank runs recorded; multi-rank runs not obtained) and the troubleshooting ladder.
- Unverified: all latency/bandwidth ranges quoted for shared memory, InfiniBand and TCP, the MPI ABI status, HCOLL/UCX/NCCL runtime variables on live InfiniBand hardware, and root cause of the observed init hang.
