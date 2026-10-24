---
id: "c06-28"
title: "6.28 HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests"
sidebar_label: "6.28 HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests"
sidebar_position: 28
description: "Benchmarking a cluster properly: methodology (active benchmarking, USE, sanity checks, statistics, failure modes), the standard benchmarks (STREAM, HPL, HPCG, IOR/mdtest, OSU micro-benchmarks, NCCL tests with bus-bandwidth formulas, MLPerf), acceptance testing and burn-in, with a tested statistics harness that exposes a 4x thread-count surprise on a heterogeneous-core CPU"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.28 HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Laptop (harness); GPU cluster for the real suite |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. **Run**: `code/part06/bench_stats.py` (HPL-style LU solve and a triad, with repetitions and confidence intervals) on an Apple M3 with OpenBLAS in NumPy (results below, including a surprising 4x slowdown at 8 threads). **Read from source**: NVIDIA/nccl-tests `doc/PERFORMANCE.md` and README (commit `afd59ab`, 2026-10-05), IOR/mdtest repository README (hpc/ior commit `e4e4578`, 2026-10-23), HPCG repository (commit `114602d`, 2023-09-23). HPL, OSU micro-benchmarks, STREAM proper, MLPerf and all multi-node/GPU numbers were **not run**. Labs on a cluster are **untested** |

## Why this matters for AI infrastructure

Benchmarks are how you accept hardware from a vendor, find the one sick node out of 1,000, compare fabrics and file systems, validate a driver upgrade, and answer "is this training run as fast as it should be?". They are also how people fool themselves and others: one run on one node, caches warm, an untuned baseline, no variance, an unrepresentative workload. The skills here, designing a measurement, running it repeatably, checking it against physics, and interpreting it, apply from a CPU micro-test to a 4,096-GPU all-reduce.

## Prerequisites and outcomes

Needs 6.3 (scaling), 6.4 (MPI), 6.18 (I/O arithmetic), 6.12 (NCCL). After this chapter you can:

- Apply an active-benchmarking methodology: define the question, control factors, measure, analyse the bottleneck while the test runs, sanity-check against hardware limits.
- Recognise and avoid the standard benchmarking failures.
- Run and interpret the standard suite: STREAM, HPL, HPCG, IOR/mdtest, OSU micro-benchmarks, `nccl-tests`, and know what each says.
- Compute NCCL "bus bandwidth" from time and size for each collective, and compare it with link speed.
- Design acceptance tests and burn-in for a new cluster, and a periodic regression suite.
- Report results with statistics, configuration, and caveats.

## 1. Methodology (Systems Performance, chapter 12)

Gregg's chapter opens with the warning "there are lies, damn lies and then there are performance measures" and the point that "benchmarks tell you only how fast the system can run the benchmark; it's up to you to understand the result and determine how it applies to your environment". Its structure, adapted to clusters:

**Reasons to benchmark**: system design and capacity planning, proof of concept, tuning, development regression testing, capacity planning, troubleshooting, marketing. **Effective benchmarks** are repeatable, observable, portable, easily presented, realistic, runnable, backwards compatible, and scalable.

**Types**: *micro-benchmarks* (one component: memory bandwidth, one collective, one file operation), *simulation/macro* (synthetic client workload), *replay* (real traces), *industry standards* (TOP500/HPL, SPEC, MLPerf, IO500).

**Common failures** (the book has a long list; those most relevant here):

1. **Casual benchmarking**: a quick tool run with default settings, no understanding of what it does.
2. **Blind faith**: believing a number without checking whether the benchmark measured what you think. Example: a "disk" benchmark that reads from page cache (6.18's `iomix.py`).
3. **Numbers without analysis**: no explanation of the result; no check against theoretical limits.
4. **Complex benchmark tools**: unexplained behaviour hidden behind many options.
5. **Testing the wrong thing**: measuring a different layer (loopback instead of the fabric) or the benchmark's own bottleneck.
6. **Ignoring errors**, **ignoring variance** (a single run), **ignoring perturbations** (background jobs, thermal throttling, other tenants in a cloud).
7. **Changing multiple factors** at once.
8. **Friendly fire**: the benchmark disturbs the production system or the monitoring.
9. **The benchmark paradox**: "If your product's chances of winning a benchmark are 50/50, you'll usually lose" because customers want to win several in a row (three 50 percent benchmarks: 12.5 percent). Corollary for buyers: define the benchmarks and pass criteria before looking at results.
10. **Cloud variance**: instances may land on faster or slower hosts or noisy neighbours; test several instances, record the distribution, use the median rather than a single run.

**Micro-benchmarking** exercises one component with a simple artificial workload (a single collective, a memory stream, one file operation); **simulation** drives the system with a synthetic client workload (a generator mimicking users or a training job's I/O pattern); **replay** re-issues a captured trace. **CPU profiling** during a benchmark (`perf record -g`, flame graphs, Nsight for GPUs) shows what the benchmark is really executing, a core part of active benchmarking. **Workload characterisation** (who, what, how much, over time) tells you which benchmark resembles your workload before you run anything; *custom benchmarks* written for your workload are the final arbiter. The book ends the chapter with exercises and references, which I do not reproduce.

**Methodology elements**: *passive benchmarking* (run a tool, record the number: weak), **active benchmarking** (analyse the system *while* the benchmark runs, with observability tools, to confirm what limits it), the **USE method** (Utilisation, Saturation, Errors for every resource), workload characterisation, custom benchmarks written for your workload, **ramping load** (increase until saturation to find the knee), **sanity checks** (does the result exceed hardware limits? does it scale as predicted?), **statistical analysis** (repetitions, mean/median/standard deviation, coefficient of variation, confidence intervals), and a **benchmarking checklist**.

A practical checklist for cluster benchmarks: (1) question and success criterion written down; (2) hardware, firmware, BIOS, driver, library and kernel versions recorded; (3) idle system verified (`top`, `squeue`, no other jobs); (4) clocks and power state noted (governor, GPU persistence, application clocks); (5) warm-up excluded; (6) at least 5 to 10 repetitions with statistics; (7) compared against a theoretical bound; (8) errors checked (`dmesg`, fabric counters before/after); (9) one factor changed at a time; (10) raw data and command lines archived.

## 2. A statistics harness (tested)

`code/part06/bench_stats.py` runs an HPL-style dense solve (NumPy `solve`, LAPACK LU; flop count `2/3 n^3 + 2 n^2` as in HPL; scaled residual check against HPL's threshold of 16) and a triad-like bandwidth loop, with a warm-up, N repetitions, and reports mean, standard deviation, coefficient of variation (CV), min/median/max and a 95 percent confidence interval (Student t). On the Apple M3 (4 performance + 4 efficiency cores, NumPy with OpenBLAS), `n = 3000`, 10 repetitions each:

| `OPENBLAS_NUM_THREADS` | mean GFLOP/s | CV | min / median / max |
|---|---|---|---|
| 1 | 44.7 | 0.8% | 44.2 / 44.6 / 45.4 |
| 2 | 81.3 | 1.7% | 79.7 / 80.6 / 83.4 |
| 4 | 90.8 | 4.8% | 82.2 / 91.3 / 97.3 |
| 8 (the library default here) | 22.9 | 13.0% | 17.9 / 22.9 / 27.1 |

and the residual check printed `scaled residual = 0.003 (PASS)`. The triad loop gave about 75 GB/s with a CV of 15 percent in the default configuration.

What this teaches, in order of importance:

1. **The default configuration was four times slower than the best.** Using all 8 threads gave 23 GFLOP/s, less than one thread (44.7), because the machine has heterogeneous cores: statically partitioned parallel LU waits at each synchronisation point for the slowest thread (an efficiency core), and OS scheduling noise adds jitter. This is the "slowest participant sets the pace" effect from 6.3 and 6.14, appearing on a laptop. A benchmark that simply ran "with defaults" would have reported a number off by 4x and a CV of 13 percent that screams "something is wrong".
2. **Variance is information.** CV of 0.8 percent (1 thread) versus 13 percent (8 threads): the noisy configuration is unstable, not just slow. On a cluster, a node whose repeated runs differ by 10 percent is suspect.
3. **Scaling is not monotonic**: 1 to 2 threads gave 1.8x, 2 to 4 only 1.1x, 4 to 8 collapsed. Sweep parameters; do not assume more is better.
4. **Sanity check against a bound**: 91 GFLOP/s on 4 performance cores is plausible for double-precision dense LU with vectorised BLAS on this class of CPU; a number above the hardware peak would signal a bug (flop count, timing, caching).
5. **Report the configuration with the number.** "91 GFLOP/s" is meaningless without `n`, threads, library, precision and machine.

(Single-machine, shared with other processes; numbers will not reproduce exactly on your machine.)

## 3. The standard suite

### STREAM (memory bandwidth)

Four kernels (copy, scale, add, triad) over arrays much larger than caches; reports GB/s. Run with one thread per core (or per NUMA domain) pinned (6.5 first-touch and `OMP_PROC_BIND`). Compare with the theoretical DRAM/HBM bandwidth (channels x transfer rate x 8 bytes): a good result is 80 to 90 percent of theoretical on CPUs. The triad loop in the harness is a toy; use real STREAM with `-O3 -fopenmp` and array size at least 4x the last-level cache. On GPUs use the GPU STREAM variants or `nvbandwidth`.

### HPL (High-Performance Linpack)

Solves `Ax = b` with LU factorisation (6.1). Inputs in `HPL.dat`: problem size **N** (as large as memory allows, typically 80 to 90 percent of total RAM: matrix is 8N^2 bytes), block size **NB** (tuned, e.g. 192 to 512 on CPUs; larger on GPUs), process grid **P x Q** (P at most Q, product = number of ranks, near-square), broadcast/panel algorithms, lookahead depth. The result is Rmax in GFLOP/s and a pass/fail residual. Interpretation: efficiency = Rmax/Rpeak; typical well-tuned values for GPU systems are in the broad range of 60 to 90 percent depending on architecture (verify against published results for your hardware generation); a node that scores well below its peers has a hardware problem (throttling, a failing DIMM, slow link). NVIDIA provides optimised HPL containers (HPL for GPUs, HPL-AI/HPL-MxP for mixed precision) with their own run scripts; build and tune instructions are in the NGC catalogue. HPL stresses compute and moderately the network, so it is also a **burn-in** workload (power and thermals!). A full HPL run on a large cluster takes hours: use it as an acceptance test and for power/thermal validation (6.30).

### HPCG (High-Performance Conjugate Gradient)

A sparse-matrix conjugate gradient with a multigrid preconditioner, memory-bandwidth-bound with global communication and irregular access; typically reaches only a few percent of Rpeak (6.1). The repository (hpcg-benchmark/hpcg, version 3.1) ships reference code, a `bin/hpcg.dat` input file (local problem dimensions and run time) and a `QUICKSTART`. The benchmark's official rules require a minimum run time (commonly 30 minutes for submissions) and reports GFLOP/s with a validity check. Use it to compare memory systems and interconnects on a more application-like load than HPL.

### IOR and mdtest

The `hpc/ior` repository contains both. **IOR** (Interleaved or Random I/O) measures parallel I/O bandwidth: each MPI rank writes/reads blocks to a shared file or one file per process, with transfer size, block size, API (POSIX, MPI-IO, HDF5, S3...), collective or independent, `fsync`, reorder tasks to defeat client caching. **mdtest** measures metadata rates: create/stat/read/remove of many files and directories, with directory depth and per-rank trees. The README tells you to build with `./bootstrap && ./configure && make`. Method for storage tests (6.18, 6.19): defeat client caches (rank reordering `-C`, large sizes, drop caches), run enough ranks to saturate (scale tasks and nodes), separate write from read phases, run at your real transfer size (1 to 4 MiB), repeat, record the file system striping. The **IO500** list standardises IOR+mdtest runs and publishes results.

### OSU Micro-Benchmarks (MPI)

From Ohio State University (MVAPICH team): `osu_latency` (ping-pong), `osu_bw`/`osu_bibw` (bandwidth), `osu_allreduce`, `osu_alltoall`, `osu_bcast`, `osu_barrier`, with CUDA variants (`-d cuda`) for GPU buffers. Use between two nodes (best case point-to-point), then across racks (switch hops) to expose topology. Compare to line rate: NDR InfiniBand at 400 Gb/s is about 50 GB/s per direction before protocol overhead, so a point-to-point bandwidth far below it indicates TCP fallback, a downtrained link, a PCIe issue, or wrong NIC mapping (6.4 section 10). The ping-pong model from 6.4 applies to the latency/bandwidth curve.

### NCCL tests

`NVIDIA/nccl-tests` builds `all_reduce_perf`, `all_gather_perf`, `reduce_scatter_perf`, `broadcast_perf`, `reduce_perf`, `alltoall_perf`, `sendrecv_perf` and others; build with `make MPI=1 MPI_HOME=... CUDA_HOME=... NCCL_HOME=...` for multi-node runs. Usage from the README:

```bash
./build/all_reduce_perf -b 8 -e 128M -f 2 -g 8                  # one process, 8 GPUs, sizes 8 B .. 128 MiB, doubling
mpirun -np 64 -N 8 ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1  # 64 ranks over 8 nodes, one GPU per rank
srun -N 8 --ntasks-per-node=8 --gpus-per-task=1 ./build/all_reduce_perf_mpi -b 8 -e 8G -f 2   # Slurm (binary built with MPI=1 and a suffix)
```

Flags: `-b/-e` min/max bytes, `-f` multiplicative step (`-i` additive), `-g` GPUs per thread, `-n` iterations (default 20), `-w` warm-up iterations (default 1), `-c` correctness checking, `-a` how to average across ranks (0 rank 0, 1 average, 2 minimum, 3 maximum) in MPI mode, `-t` threads per process. `NCCL_TESTS_SPLIT` runs several concurrent sub-communicators (e.g. `MOD 8` runs eight parallel operations, one GPU per node each, which tests rail-wise network paths).

**Reading the output**: each size prints time (µs), **algbw** (algorithm bandwidth = size / time) and **busbw** (bus bandwidth), once for out-of-place and once for in-place. From `doc/PERFORMANCE.md`: time is dominated by latency at small sizes and becomes `overhead + size/bandwidth` at large sizes; *algbw* is what an application experiences; *busbw* = algbw times a correction factor that reflects how much data each rank link must actually carry for that collective, so it can be compared with the hardware peak independent of rank count:

| Collective | busbw = algbw x |
|---|---|
| AllReduce | 2(n-1)/n |
| ReduceScatter | (n-1)/n |
| AllGather | (n-1)/n |
| AlltoAll | (n-1)/n |
| Broadcast, Reduce | 1 |
| Send/Recv | 1 |

(The first six rows are the document's own summary list; the Send/Recv factor of 1 is my inference, since a point-to-point transfer moves exactly its size over one link.) The AllReduce factor derives from the best-case time `t = (S/B) x 2(n-1)/n`: each of `n` links carries `2(n-1)/n` times the data. Worked example: 64 ranks, 8 GiB message, measured time 0.60 s. algbw = 8.59 GB / 0.60 s = 14.3 GB/s; busbw = 14.3 x 2 x 63/64 = 28.2 GB/s. If each GPU has a 400 Gb/s (50 GB/s) NIC, that is 56 percent of the NIC rate: worth investigating (NIC mapping, routing, congestion). A healthy 8-GPU NVSwitch node runs far higher intra-node (hundreds of GB/s), so intra-node and inter-node results should be compared separately.

How to use it in practice: (1) single-node all-reduce on every node (finds a bad GPU, NVLink or PCIe link); (2) pairs of nodes (finds bad NICs or cables: rotate pairs); (3) full allocation at several sizes; (4) compare with the baseline of a golden run, per switch tier; (5) run after maintenance and before releasing nodes. Combine with `NCCL_DEBUG=INFO` to confirm the transport (6.12).

### MLPerf

MLCommons' MLPerf Training and Inference benchmark end-to-end model training/inference scenarios with defined rules and quality targets. They tell you how a complete stack performs on standard models; vendors tune them heavily. Use the published rules and reference implementations to benchmark your own cluster, but remember that your workload may differ. Also relevant: framework-level benchmarks (tokens/s, MFU, time to train a fixed number of steps), which are the final arbiter (Part 14, 15).

## 4. Acceptance testing and burn-in

A new cluster should not enter production on the vendor's word. A plan:

1. **Inventory and firmware audit**: every node's BIOS/BMC/NIC/GPU firmware matches the baseline (Part 7, 9).
2. **Burn-in**: CPU and memory stress (`stress-ng`, `memtester`), GPU stress (`dcgmi diag -r 3`, `gpu-burn` or HPL), disk (`fio`), network (iperf3 and RDMA perftest), for 24 to 72 hours, watching for errors and thermal throttling. Infant mortality shows up here.
3. **Per-node performance**: STREAM, single-node HPL or DGEMM, single-node NCCL: compare to the median of peers and flag outliers (e.g. below 95 percent of median).
4. **Fabric**: `ib_write_bw`/`ib_send_lat` between all node pairs in a shifted pattern (or the vendor's all-to-all validation), then `nccl-tests` at scale. Check fabric error counters before and after.
5. **Storage**: IOR/mdtest at scale and fio per client against targets in the purchase specification.
6. **System**: full-cluster HPL run (power, cooling, stability), multi-day training-like job, failure injection (pull a cable, kill a node) to test recovery.
7. **Scheduler/software**: smoke tests of Slurm features, containers, identity, monitoring (6.7 to 6.26).
8. **Document**: expected values per node type, tolerances, and the pass/fail report, signed off before payment milestones.

Keep the suite as a **regression test**: run a short version nightly or weekly and after every change (driver, firmware, kernel, NCCL, Slurm); trend results; alert on drops (6.26).

## 5. Reporting

A good benchmark report states: the question; the system (hardware, firmware, software versions, topology, number of nodes); the command lines and configuration files; the environment variables; the number of runs and statistics (mean/median, spread, CI); the baseline or theoretical bound; observations of limiting resources (USE); anomalies and exclusions; raw data location; and conclusions with caveats. Present distributions (box plots) and scaling curves, not single numbers.

## 6. Lab

Tested: 1) run `bench_stats.py` with `OPENBLAS_NUM_THREADS` set to 1, 2, 4, 8 (and the number of your physical cores), 10 repetitions each; record mean/CV; explain the shape. 2) Change `n` to 1000 and 6000; how does GFLOP/s scale and why? 3) Compare the triad to a compiled STREAM (6.5 toolchain). 4) Compute busbw for 8 sample measurements by hand with the formulas above.

Untested (cluster): 5) STREAM on every node; list outliers. 6) Single-node and 2-node HPL (or the NVIDIA HPL container) and compute efficiency. 7) OSU latency/bandwidth between node pairs across racks. 8) `nccl-tests` all_reduce at 1, 2, 4, 8 nodes; plot busbw vs size. 9) IOR/mdtest on `/home` and scratch with 1 to 64 ranks. 10) Burn-in plan for 16 nodes. 11) Inject a fault (throttle a GPU with a lower power cap or unplug a cable) and see what each test shows.

## 7. Interview angles

- You run `all_reduce_perf` and get busbw 30 GB/s on 64 GPUs with 50 GB/s NICs. What next?
- Explain algbw vs busbw and why the all-reduce factor is 2(n-1)/n.
- What makes a benchmark result trustworthy? List the checks.
- Why did eight threads run slower than one in the harness?
- How do you acceptance-test a new GPU cluster?
- HPL vs HPCG vs MLPerf: what does each tell a buyer?
- How do you benchmark a parallel file system without measuring RAM?
- A benchmark shows a node 8 percent slower than peers. How do you decide if it is a problem?
- What is active benchmarking?

## 8. Checkpoint questions (30)

1. State three reasons to benchmark.
2. List five benchmarking failures.
3. What is the benchmark paradox?
4. What is active benchmarking?
5. What does the USE method check?
6. What belongs in a benchmarking checklist?
7. Why are warm-up and repetitions required?
8. Define CV and why it matters.
9. What did the thread sweep show on the M3?
10. Why is `solve` flop count `2/3 n^3 + 2 n^2`?
11. What does HPL's residual check do?
12. Which HPL parameters matter most?
13. Why choose N from memory size?
14. What does HPCG measure and why is its efficiency low?
15. What is STREAM and its bound?
16. What do IOR and mdtest measure?
17. How do you stop IOR measuring cache?
18. List OSU benchmarks.
19. What do `-b -e -f -g` mean in nccl-tests?
20. Define algbw and busbw.
21. Give the busbw factor for all-reduce, all-gather, reduce-scatter, broadcast.
22. Compute busbw for 8 GiB, 64 ranks, 0.60 s.
23. How do you compare busbw to hardware?
24. Why test pairs of nodes?
25. What does `NCCL_TESTS_SPLIT` do?
26. What is MLPerf?
27. List burn-in steps.
28. How do you detect an outlier node?
29. What should a report contain?
30. How does a benchmark suite become a regression test?

## 9. Sources and review notes

- Methodology, failures, benchmark types, active benchmarking, statistics, checklist: *Systems Performance*, 2nd ed. (Gregg), chapter 12 (SP 12), restated in my words; AI-specific storage and input-pipeline benchmarking: *AI Systems Performance Engineering* (ASP); MPI/HPC performance context: *Parallel and High Performance Computing* (PHPC).
- NCCL tests usage and bus-bandwidth formulas: `nccl-tests/README.md` and `doc/PERFORMANCE.md` (commit `afd59ab`). IOR/mdtest: `hpc/ior` README (commit `e4e4578`). HPCG: repository layout and README (commit `114602d`, version from 2023).
- Original and run: `bench_stats.py` and its measured table; worked busbw example; acceptance plan.
- Unverified: typical HPL efficiency ranges for specific hardware, STREAM efficiency percentages, OSU option names beyond the common ones, HPCG submission rules, MLPerf details, burn-in durations. No benchmark other than the harness was executed.
