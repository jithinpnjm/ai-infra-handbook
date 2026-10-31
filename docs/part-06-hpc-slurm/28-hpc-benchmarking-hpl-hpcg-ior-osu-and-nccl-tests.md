---
id: "c06-28"
title: "6.28 HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests"
sidebar_label: "6.28 HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests"
sidebar_position: 28
description: "Benchmarking a cluster properly: methodology (active benchmarking, USE, sanity checks, statistics, failure modes), the standard benchmarks (STREAM, HPL, HPCG, IOR/mdtest, OSU micro-benchmarks, NCCL tests with bus-bandwidth formulas, MLPerf), acceptance testing and burn-in, with a tested statistics harness that exposes a 4x thread-count surprise on a heterogeneous-core CPU"
status: "reviewed"
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

```mermaid
flowchart LR
  Char["1. Characterize & Design<br/>Question, Working Set, Bounds"] --> Run["2. Execute & Ramp Load<br/>STREAM, HPL/HPCG, IOR/gdsio, nccl-tests"]
  Run --> Active["3. Active Benchmarking<br/>USE, bpftrace, Flame Graphs, Nsight"]
  Active --> Sanity["4. Sanity Check & Stats<br/>Physics Limits, Mean/CV/95% CI"]
  Sanity --> Gate["5. Acceptance & Regression<br/>Why not double? Did it error?"]
```

Gregg's chapter opens with the warning "there are lies, damn lies and then there are performance measures" (`[Anon 85]`) and the point that "benchmarks tell you only how fast the system can run the benchmark; it's up to you to understand the result and determine how it applies to your environment". Its structure, adapted to clusters:

**Background and reasons to benchmark (`SP` 12.1 & 12.1.1)**: system design and purchase decisions (specifically the `price/performance` ratio—or `performance/price` ratio so "bigger is better"—quantified over the five-year capital cost of the equipment `[Anon 85]`), proofs of concept, tuning tunable parameters, development (both automated non-regression testing and limit investigations), capacity planning, troubleshooting (verifying components still hit maximum throughput), and marketing ("benchmarketing"). While on-premises hardware proofs of concept can take weeks or months to ship, rack, cable, and install, cloud computing instances can be spun up in minutes, benchmarked, or tested directly with fault-tolerant production traffic (for example, Netflix's automated micro-benchmarking and CPU profiling of new cloud instance types). Key references from `SP` 12.6 (`References`) appear throughout this section (`[Joy 81]`, `[Anon 85]`, `[Jain 91]`, `[Gunther 97]`, `[Shanley 98]`, `[Coker 01]`, `[Smaalders 06]`, `[Gunther 07]`, `[Bourbonnais 08]`, `[DeWitt 08]`, `[Traeger 08]`, `[Gregg 09b/09c/14c/14d/18d]`).

**Effective benchmarking (`SP` 12.1.2)**: As shown in "A Nine Year Study of File System and Storage Benchmarking" (`[Traeger 08]`, which surveyed `415` file system and storage benchmarks across `106` research papers), most popular benchmarks are flawed and fail to explain true system behavior. Good benchmarks are **repeatable**, **observable**, **portable**, **easily presented**, **realistic**, and **runnable** (`[Smaalders 06]`). Above all, engage performance engineers *while* the benchmark is running rather than handing them numbers afterward. Gregg cites Bill Joy's classic `1981` BSD TCP/IP analysis (`[Joy 81]`): transmitting `4 Megabytes` in `1024`-byte records encapsulated in `1068`-byte Ethernet packets from a DEC `VAX-11/750` (`1980`) to a `VAX-11/780` took `28 seconds` (`1.2 Megabaud` user-to-user throughput), during which the `11/750` was CPU-saturated while the `11/780` had `30%` idle time, with kernel CPU time split across Ethernet handling (`20%`), IP packet processing (`10%`), TCP processing (`30%`), checksumming (`25%`), and user system call handling (`15%`).

**16 Benchmarking Failures (`SP` 12.1.3)**:
1. **Casual benchmarking**: "you benchmark A, but actually measure B, and conclude you've measured C" (for example, testing file system RAM cache while concluding you measured disk I/O; beginners lack the instinct to recognize a "1,000-degree room thermometer" number).
2. **Blind faith (`argumentum ad populum`)**: assuming a popular or vendor-promoted open-source benchmark is valid without verifying what it actually executes.
3. **Numbers without analysis**: "If you've spent less than a week studying a benchmark result, it's probably wrong." When time is short, explicitly list unverified assumptions (e.g., assuming the tool isn't buggy, assuming the disk test measures disk I/O, assuming it drove disk I/O to its limit, and assuming that I/O pattern matches your application).
4. **Complex benchmark tools**: benchmarking the benchmark itself (e.g., a single-threaded load generator bottlenecking before the target). Prefer short C micro-benchmarks, or client simulations written in the same language as the real client.
5. **Testing the wrong thing**: testing disk IOPS when the production working set runs 100% in RAM cache, or optimizing engineering effort around an outdated benchmark.
6. **Ignoring the environment**: testing a database or filesystem with default OS/storage tunables when production runs heavily tuned parameters.
7. **Ignoring errors**: a benchmark tool reporting fast or slow completion when every request actually failed (Gregg cites a web server benchmark reporting `> 1 second` average latency because a firewall blocked 100% of requests and the tool measured client connection timeout errors).
8. **Ignoring variance**: applying a steady average rate (e.g., `500 reads/s` and `50 writes/s` at a fixed `10:1` ratio) when real production writes arrive in synchronous/asynchronous bursts every `10 seconds` that queue behind reads; model stateful request clustering with a **Markov model** (`[Jain 91]`).
9. **Ignoring perturbations**: cron backups, per-minute monitoring agents, cloud noisy neighbors, device interrupts, kernel CPU affinity migration delays, and cold caches. Run benchmarks for minutes (never `< 1 second`), repeat multiple times, and inspect full latency distributions.
10. **Changing multiple factors**: comparing two hosts separated by different switch hop counts or cloud instance placements (test multiple cloud instances and take the median/distribution).
11. **The benchmark paradox (`[Gregg 14c]`)**: "If your product's chances of winning a benchmark are 50/50, you'll usually lose"—because a buyer running three independent benchmarks and requiring your system to win all three gives a win probability of $0.5 \times 0.5 \times 0.5 = 0.125 = \mathbf{12.5\%}$.
12. **Benchmarking the competition**: posting untuned results for a competitor's product (which customers have spent months tuning) destroys your credibility.
13. **Friendly fire**: underselling your own product by misconfiguring an undocumented new feature, failing to drive a physical resource to `100%` utilization, or testing an older unpatched software release.
14. **Misleading benchmarks**: lying by omission (testing a prohibitively expensive custom configuration without disclosing price, or hiring multiple inexperienced third parties and cherry-picking the highest outlier).
15. **Benchmark specials (`[Shanley 98]`)**: engineering a product feature solely to inflate a benchmark score without helping real workloads—a term coined in `1993` during the **TPC-A** benchmark when the Standish Group accused Oracle of adding a `discrete transactions` option solely for TPC-A. TPC responded with an anti-benchmark-special clause and a pricing rule (`[TPC 19a]`) requiring total disclosed price to be within **`2%`** of what a real customer would pay.
16. **Cheating**: fabricating fake numbers outright (rare compared to failures 1–15).

**Benchmarking Types (`SP` 12.2)**:
- **Micro-benchmarking (`SP` 12.2.1)**: tests one isolated operation type (`SysBench` for CPU, `lmbench` for memory I/O, `fio` for file system, `hdparm`/`dd`/`fio` direct I/O for disk, `iperf` for network). In Gregg's `Table 12.1` file system micro-benchmark design, five core tests—(1) `sequential 512-byte reads` (maximum realistic IOPS, since disks round 1-byte I/O up to `512`-byte or `4-Kbyte` sectors), (2) `sequential 1-Mbyte reads` (maximum read throughput, noting OS-specific sweet spots such as Solaris's `128 Kbyte` largest slab cache size), (3) `sequential 1-Mbyte writes` (maximum write throughput), (4) `random 512-byte reads` (random seek/IOPS effect), and (5) `random 512-byte writes` (rewrite effect)—are multiplied by **working set size** (much smaller than main memory to test file system software cache vs much larger than main memory to test physical disk I/O) and **thread count** (single-threaded for clock-speed bound vs multithreaded to saturate all CPUs). Complement **sunny day performance testing** (top speeds under ideal conditions) with **cloudy day / rainy day performance testing** (contention, perturbations, variance, and degraded components).
- **Simulation / macro-benchmarking (`SP` 12.2.2)**: simulates a composite client workload (for example, an NFS mix of `reads 40%`, `writes 7%`, `getattr 19%`, `readdir 1%`; classic CPU simulations `Whetstone` from `1972` and `Dhrystone` from `1984`; HTTP load generators `wrk` `[Glozer 19]`, `siege` `[Fulmer 12]`, and `hey` `[Dogan 20]`), using stateless random probabilities or stateful **Markov models**.
- **Replay (`SP` 12.2.3)**: replays a captured production trace log. Beware of replaying at the wrong layer: Gregg describes a storage upgrade where replaying a block-level disk trace from an old system (`10 K rpm` disks) onto a new system (`7,200 rpm` disks, but with **`16x` more file system RAM cache** and faster CPUs) showed worse performance and lost the sale because the block-level replay bypassed the `16x` larger file system page cache that would have served the real workload from RAM.
- **Industry standards (`SP` 12.2.4)**: Originating from Jim Gray's `1985` paper "A Measure of Transaction Processing Power" (`[Anon 85]`, defining `Sort`, `Scan`, and `DebitCredit` and transactions per second `TPS` alongside `MIPS` and `FLOPS`), major standards include **TPC** (`TPC-C`, `TPC-DS`, `TPC-E`, `TPC-H`, `TPC-VMS`, `TPCx-HS`, `TPCx-V`) and **SPEC** (`SPEC Cloud IaaS 2018`, `SPEC CPU 2017`, `SPECjEnterprise 2018 Web Profile`, `SPECsfs2014`, `SPECvirt_sc2013`), plus HPC/AI standards (**TOP500 HPL**, **HPCG**, **IO500**, **MLPerf**).

**Methodology (`SP` 12.3, `Table 12.2`)**:
1. **Passive benchmarking (`12.3.1`)**: fire-and-forget execution ("pick tool $\to$ run options $\to$ make slide deck $\to$ hand to management")—an anti-methodology prone to software bugs, single-thread bottlenecks, and testing the wrong layer.
2. **Active benchmarking (`12.3.2`, `bonnie++` Case Study)**: analyze the system with observability tools *while* the benchmark runs (`[Gregg 14d]`). In Gregg's case study of `bonnie++` (`Version 1.97` `[Coker 01]`), the "Sequential Output — Per Chr" test reported `739 Kbytes/sec` at `99%` CPU (which, if truly 1-byte disk I/O, would require an impossible `739,000` disk IOPS). Running `iostat -sxz 1` during the test showed **`0` disk IOPS**; `bpftrace -e 'tracepoint:block:* { @[probe] = count(); }'` showed `block_dirty_buffer: 808225` and `block_touch_buffer: 1025678` with zero `block_rq_issue`; `cachestat 1` confirmed `100.00%` page-cache hits/dirties; `bpftrace -e 'kprobe:vfs_* /comm == "bonnie++"/ { @[probe] = count(); }'` and `k:vfs_write { @bytes = hist(arg2); }` proved `bonnie++` was issuing `1,176,936` 1-byte `vfs_write()` calls into the OS page cache; and `strace bonnie++ -b` showed `write(3, "6", 1) = 1` without calling `fsync(2)` after each byte (older versions also buffered inside `libc` `putc(3)` / `setbuffer(3)` `[Bourbonnais 08]`).
3. **CPU profiling (`12.3.3`, Flame Graph Case Study)**: profile both user and kernel stacks during the benchmark. When a new storage server unexpectedly underperformed an older server on a disk benchmark while disks were mostly idle, a kernel CPU flame graph immediately revealed **`62.17%`** of CPU samples inside **`zfs_zone_io_throttle()`**—an overlooked default ZFS I/O resource control throttling the benchmark.
4. **USE Method (`12.3.4`) and Workload Characterization (`12.3.5`)**: check **U**tilization, **S**aturation, and **E**rrors on every hardware and software resource until you confirm which resource hit `100%` utilization.
5. **Custom benchmarks (`12.3.6`) and Ramping load (`12.3.7`, `randread.pl` Case Study)**: write minimal C or Perl load generators (verifying that compiler optimizations do not elide dead loops) and increment client threads one by one to plot the throughput and latency knee. Gregg's `randread.pl` script (`$IOSIZE = 8192`, using unbuffered `sysread()` across a farm of NFS clients) drove a Sun ZFS Storage Appliance (`[Gregg 09b]`) to nearly `500,000` reads/s (`> 3.5 Gbytes/s`). Always pair throughput with latency limits: if a storage array delivers **`990,000 IOPS` at `5 ms` average latency**, and adding more clients scrapes past `1,000,000 IOPS` only by queueing operations to **`> 50 ms` average latency**, the valid engineering result is **`990,000 IOPS`**.
6. **Sanity check (`12.3.8`)**: check whether reported numbers violate physical wire or bus limits. For example, an NFS server connected via a single **`1 Gbit/s` Ethernet port** reported to deliver `50,000 IOPS` of `8 Kbyte` reads would require $50,000 \times 8\text{ KB} = 400,000\text{ KB/s} \approx \mathbf{3.2\text{ Gbits/s}}$ (plus headers)—more than $3\times$ the `1 Gbit/s` line rate (whose practical single-direction TCP throughput ceiling is **`119–120 Mbytes/s`**, exposing single-direction claims of `200`, `350`, `800`, or `1,150 Mbytes/s` `[Gregg 09c]` as client-cache illusions).
7. **Statistical analysis (`12.3.9`)**: when time on a shared "max config" cluster is scarce (contended by Sales, Marketing, Support, Engineering, and Quality), capture full distributions, standard deviations, error margins, and before/after `/proc` counter snapshots (using a custom read script rather than `tar(1)`, because `tar` sees zero-sized `/proc` files from `stat(2)` and skips their contents).
8. **Gregg's 6-Question Benchmarking Checklist (`12.3.10`, `[Gregg 18d]`)**:
   - *Why not double?* (What is the actual bottleneck preventing $2\times$ the rate?)
   - *Did it break limits?* (Physical bandwidth/IOPS sanity check.)
   - *Did it error?* (Are timeouts or failed requests skewing the rate?)
   - *Does it reproduce?* (What is the variance/CV across repetitions?)
   - *Does it matter?* (Does this operation match the production workload?)
   - *Did it even happen?* (Confirm with `iostat`/`bpftrace`/counters that traffic reached the target.)
9. **Vendor Benchmark Questions (`SP` 12.4)**: When auditing a vendor's benchmark claim without direct system access, demand disclosures across four domains: **General** (production relevance, single node vs cluster, total system cost, client configuration, test duration and sample count, average vs peak, full distribution/percentiles, limiting factor, success/fail ratio, active analysis screenshots, error margins), **CPU/Memory** (exact SKU, overclocking/water cooling, DIMM count and socket population, disabled cores, system-wide CPU utilization and turbo boost state, physical cores vs hyperthreads, BIOS settings), **Storage** (drive count/type/protocol, RAID level, write-back cache, filesystem journaling/tuning, working set size vs RAM cache hit ratio, file count), and **Network** (NIC count/type, topology, protocols, socket options, TCP/UDP sysctl tunables).

A practical 10-point checklist for cluster benchmarks: (1) question and success criterion written down; (2) hardware, firmware, BIOS, driver, library and kernel versions recorded; (3) idle system verified (`top`, `squeue`, no other jobs); (4) clocks and power state noted (governor, GPU persistence, application clocks); (5) warm-up excluded; (6) at least 5 to 10 repetitions with statistics; (7) compared against a theoretical bound; (8) errors checked (`dmesg`, fabric counters before/after); (9) one factor changed at a time; (10) raw data and command lines archived.

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

Solves `Ax = b` with LU factorisation (6.1). Inputs in `HPL.dat`: problem size **N** (as large as memory allows, typically 80 to 90 percent of total RAM: matrix is 8N^2 bytes), block size **NB** (tuned, e.g. 192 to 512 on CPUs; larger on GPUs), process grid **P x Q** (P at most Q, product = number of ranks, near-square), broadcast/panel algorithms, lookahead depth. The result is Rmax in GFLOP/s and a pass/fail residual. Interpretation: efficiency = Rmax/Rpeak; typical well-tuned values for GPU systems are in the broad range of 60 to 90 percent depending on architecture (verify against published results for your hardware generation); a node that scores well below its peers has a hardware problem (throttling, a failing DIMM, slow link). NVIDIA provides optimised HPL containers (HPL for GPUs, HPL-AI/HPL-MxP for mixed precision) with their own run scripts; build and tune instructions are in the NGC catalogue. HPL stresses compute and moderately the network, so it is also a **burn-in** workload (power and thermals). A full HPL run on a large cluster takes hours: use it as an acceptance test and for power/thermal validation (6.30).

### HPCG (High-Performance Conjugate Gradient)

A sparse-matrix conjugate gradient with a multigrid preconditioner, memory-bandwidth-bound with global communication and irregular access; typically reaches only a few percent of Rpeak (6.1). The repository (hpcg-benchmark/hpcg, version 3.1) ships reference code, a `bin/hpcg.dat` input file (local problem dimensions and run time) and a `QUICKSTART`. The benchmark's official rules require a minimum run time (commonly 30 minutes for submissions) and reports GFLOP/s with a validity check. Use it to compare memory systems and interconnects on a more application-like load than HPL.

### IOR and mdtest

The `hpc/ior` repository contains both. **IOR** (Interleaved or Random I/O) measures parallel I/O bandwidth: each MPI rank writes/reads blocks to a shared file or one file per process, with transfer size, block size, API (POSIX, MPI-IO, HDF5, S3...), collective or independent, `fsync`, reorder tasks to defeat client caching. **mdtest** measures metadata rates: create/stat/read/remove of many files and directories, with directory depth and per-rank trees. The README tells you to build with `./bootstrap && ./configure && make`. Method for storage tests (6.18, 6.19): defeat client caches (rank reordering `-C`, large sizes, drop caches), run enough ranks to saturate (scale tasks and nodes), separate write from read phases, run at your real transfer size (1 to 4 MiB), repeat, record the file system striping. The **IO500** list standardises IOR+mdtest runs and publishes results.

### Benchmarking GPUDirect Storage with `gdsio`

To benchmark storage-to-GPU DMA paths (GPUDirect Storage, `GDS`, Part 13), NVIDIA ships `/usr/local/cuda/gds/tools/gdsio`. You compare the CPU-staged path (`-x 2`, pinned host memory with async copies) against the direct `GDS` path (`-x 0`, storage directly into GPU HBM via `cuFile` and `nvidia-fs`) in read mode (`-I 0`) with 4 workers (`-w 4`), a 10 GiB file size (`-s 10G`), and 1 MiB I/O size (`-i 1M`) on GPU 0 (`-d 0`) (untested here):

```bash
# Before: Storage -> CPU Memory -> GPU (CPU-staged path, -x 2) (untested here)
/usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 2

# After: Storage -> GPU Memory via GPUDirect Storage (GDS path, -x 0) (untested here)
/usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 0
```

In the book's example (Table 5-1), the CPU-staged path (`-x 2`) achieves `8.0 GB/s` total throughput at `1.25 ms` average latency (with `85%` CPU utilization), whereas the `GDS` path (`-x 0`) achieves `9.6 GB/s` total throughput at `1.00 ms` average latency (with `25%` CPU utilization)—a `+20%` throughput improvement and `20%` lower latency while freeing host CPU cores. (Similarly, VAST Data's GDS benchmarks in the book report a `+20%` sequential read throughput boost on an A100 GPU and `+30%+` on an H100 GPU.) To trace `cuFile` calls alongside CUDA and OS runtime activity on a timeline, run Nsight Systems with `nsys profile --trace=cuda,gds,nvtx,osrt` (untested here) and enable `cuFile` static tracepoints in `/etc/cufile.json`.

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

**Diagnosing communication-bound versus compute-bound training with the batch-size halving/doubling test:** When profiling a real DDP backward pass, gradient `all_reduce` payload size depends on the number of model parameters rather than the batch size, whereas backward compute scales with the batch size. In the book's example, suppose your gradient `all_reduce` achieves `60 GB/s` across a `100 GB/s` NIC:
- **Halve the batch size** (halving compute while keeping gradient communication bytes fixed): if achieved NIC throughput stays at `60 GB/s`, the network is the bottleneck (communication-bound). If NIC throughput drops from `60 GB/s` to `40 GB/s`, the GPUs were not finishing compute fast enough to keep the NIC saturated (compute-bound).
- **Double the batch size** (reverse check): if the workload is communication-bound, the NIC remains pinned at `60 GB/s`; if it is compute-bound, the fraction of total iteration time spent in `all_reduce` shrinks relative to the growing compute time. Combine this test with `nsys` timelines (checking for NCCL wait gaps between compute kernels) and `ncu` kernel profiles (checking whether a slow NCCL kernel is at `60%` SM busy over PCIe vs `90%` SM busy over NVLink).

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

### Remeasure after every change

Change only one or two things at a time, and then measure. Otherwise you will not know which change helped. When scaling is good on the current configuration, write down the good metric values. Then aim to keep those values as you scale.

### Remove hidden synchronization and tune the environment

Unnecessary synchronization can quietly serialize your work. Remove `torch.cuda.synchronize()` calls and barriers that force everything to wait, because they can line up execution in the wrong order. The book covers this in its PyTorch chapter. If the environment needs tuning, set `NCCL_IGNORE_CPU_AFFINITY=1` when it helps. You can also pin CPU threads to a different topology.

Small changes like these sometimes turn poor resource use into high use. It is not always easy, but it is worth trying. Measure after each change, as described above, so you can tell which one mattered.

### Use the right tools for the job

NCCL is built for scalable collective operations, such as all-reduce, which training uses heavily. NIXL targets high-throughput point-to-point and streaming transfers, which inference often needs. Use NIXL where token streaming dominates the workload. Prefer NCCL or NVSHMEM for bulk collective and symmetric-memory patterns.

GPUDirect RDMA and GDS remove the host memory bounce buffer for network and storage I/O. The CPU still schedules and controls those transfers. Always use `DistributedDataParallel` over `DataParallel` for multi-GPU training. These libraries are heavily tuned, so use them instead of reinventing the wheel.

### Document and educate

Tuning often depends on tacit team knowledge, such as which environment variables are overridden or which library versions have bugs. Write these findings in the code or configuration file, where the next reader will see them. A note can be as simple as: in this cluster, setting `NCCL_SOCKET_NTHREADS=2` improved multinode throughput by 10%. Make this a standard practice, so the lesson survives staff changes.

## 6. Lab

First, run the self-checking Python lab (`code/part06/bench_stats_lab.py`) locally. It runs `hpl_like()` and `triad()` from `code/part06/bench_stats.py` (verifying that the dense LU solve passes HPL's scaled residual check $< 16.0$), verifies the `nccl-tests` `algbw` and `busbw` formulas (`8 GiB` across `64` ranks in `0.60 s` $\to$ `algbw = 14.3 GB/s`, `busbw = 28.2 GB/s` for `AllReduce` and `14.1 GB/s` for `AllGather`), and checks `SP` Chapter 12's sanity-check math (`50,000 IOPS * 8 KB = 400,000 KB/s = 3.2 Gbps > 1 Gbps` limit) and Benchmark Paradox (`0.5^3 = 12.5%`):

```bash
python3 code/part06/bench_stats_lab.py
```

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

## Exercises

1. **Statistical Benchmarking and Heterogeneous-Core Stragglers (`code/part06/bench_stats.py` & `bench_stats_lab.py`):** Run `python3 code/part06/bench_stats_lab.py`. Explain why `hpl_like()` performs a throwaway warm-up solve before timing repetitions, how the scaled residual $\frac{\|Ax - b\|_\infty}{\epsilon (\|A\|_\infty \|x\|_\infty + \|b\|_\infty) n} < 16$ validates numerical correctness, and why running `OPENBLAS_NUM_THREADS=8` on a 4P+4E Apple M3 collapsed throughput from `90.8 GFLOP/s` (`CV = 4.8%`) down to `22.9 GFLOP/s` (`CV = 13.0%`).
2. **Calculating `nccl-tests` Algorithm Bandwidth (`algbw`) and Bus Bandwidth (`busbw`) (`code/part06/bench_stats_lab.py`):** Using `nccl_busbw()` in `code/part06/bench_stats_lab.py`, calculate `algbw` (`14.3 GB/s`) and `busbw` (`28.2 GB/s` for `AllReduce`, `14.1 GB/s` for `AllGather`/`ReduceScatter`/`AlltoAll`) when an `8 GiB` (`8,589,934,592` B) collective across `64` ranks completes in `0.60 s`. Compare `28.2 GB/s` against a `400 Gb/s` (`50 GB/s`) NDR InfiniBand rail and list the four checks to diagnose the `56%` efficiency gap.
3. **Active Benchmarking and Debunking Cached Benchmarks (`SP` Chapter 12 `bonnie++` & Sanity Checks):** Trace how Brendan Gregg used `iostat -sxz 1`, `bpftrace` (`tracepoint:block:*` and `kprobe:vfs_*`), `cachestat 1`, and `strace` to prove that `bonnie++`'s `739 KB/s` `Per Chr` disk test actually issued `1`-byte `vfs_write()` calls into the page cache with zero block I/O. Perform the `SP` Chapter 12 sanity check on a vendor claim of `50,000 IOPS` of `8 KB` reads over a `1 Gbit/s` Ethernet link (`400,000 KB/s = 3.2 Gbps > 1 Gbps`).
4. **Sizing HPL (`HPL.dat`) and Contrasting HPL, HPCG, and STREAM:** For an 8-GPU node with `640 GiB` total HBM (or `2,048 GiB` host RAM), calculate the problem size $N$ (`8 * N^2` bytes) that fills `85%` of memory, choose a near-square process grid $P \times Q$ across 64 ranks ($P=8, Q=8$), and contrast what HPL (`Rmax/Rpeak` $\approx 60\text{–}90\%$), HPCG (sparse multigrid, a few percent of `Rpeak`), and STREAM Triad measure.
5. **Benchmarking Parallel Storage (`IOR`, `mdtest`, and `gdsio`, `ASP` Chapter 5):** Write the `IOR` and `mdtest` flags needed to defeat client page caching on a parallel filesystem (`-C` rank reordering, file size $> 2\times$ aggregate client RAM, separate write/read phases), and compare the two `gdsio` commands (`-x 2` CPU-staged `8.0 GB/s` at `1.25 ms` / `85%` CPU vs `-x 0` GPUDirect Storage `9.6 GB/s` at `1.00 ms` / `25%` CPU).
6. **Distinguishing Communication-Bound vs Compute-Bound Training (`ASP` Chapter 5 Batch-Size Test):** Given a multi-node DDP training run achieving `60 GB/s` during gradient `all_reduce` over `100 GB/s` NICs, explain how halving and doubling the micro-batch size (combined with `nsys` timeline gaps and `ncu` SM occupancy) isolates whether the job is network-bound (`60 GB/s` unchanged) or compute-bound (`60 GB/s` drops to `40 GB/s`).

## Checkpoint

<details>
<summary>1. What is the difference between **passive benchmarking** and **active benchmarking** (`SP` Chapter 12)?</summary>

- **Passive benchmarking:** "Fire-and-forget" execution where a tool is run and only its final summary number is recorded—frequently measuring the wrong layer (such as page cache or firewall timeouts) or bottlenecking on the benchmark client itself.
- **Active benchmarking (`[Gregg 14d]`):** Analyzing the system *while* the benchmark is running using observability tools (`iostat`, `bpftrace`, `perf` flame graphs, `cachestat`, `nvidia-smi dmon`, `nsys`, `ibstat`) to confirm what is actually being tested and identify the exact 100%-utilized limiting resource (**USE method**).
</details>

<details>
<summary>2. State Brendan Gregg's **6-Question Benchmarking Checklist** (`SP` Chapter 12.3.10).</summary>

1. **Why not double?** (What specific physical or software resource prevented the benchmark from running $2\times$ faster?)
2. **Did it break limits?** (Sanity-check against physical wire/bus/disk ceilings.)
3. **Did it error?** (Check whether failed requests or timeouts skewed the result.)
4. **Does it reproduce?** (Check CV and confidence intervals across repetitions.)
5. **Does it matter?** (Does the benchmark's workload match production?)
6. **Did it even happen?** (Confirm via kernel/hardware counters that I/O or network packets actually reached the target.)
</details>

<details>
<summary>3. Explain the **Benchmark Paradox** (`SP` Chapter 12.1.3) and its mathematical implication for multi-test evaluations.</summary>

If a product has a $50\%$ ($0.5$) chance of winning any single noisy/untuned benchmark and a buyer requires the product to win **three benchmarks in a row**, the probability of winning all three is:
$$0.5 \times 0.5 \times 0.5 = 0.125 = \mathbf{12.5\%}$$
("If your product's chances of winning a benchmark are 50/50, you'll usually lose.")
</details>

<details>
<summary>4. What is a **Benchmark Special** (`SP` Chapter 12.1.3), when did the term originate, and what two rules did the TPC introduce to stop it?</summary>

A **benchmark special** is a hardware/software feature or pricing discount engineered solely to inflate a benchmark score without benefiting real-world customer workloads. The term originated in **`1993`** when the Standish Group challenged Oracle's `discrete transactions` option in the **TPC-A** benchmark (`[Shanley 98]`). The TPC responded by (1) prohibiting any implementation that improves benchmark scores without improving real-world performance, and (2) requiring disclosed pricing to be within **`2%`** of actual customer pricing (`[TPC 19a]`).
</details>

<details>
<summary>5. How did active benchmarking with `iostat`, `bpftrace`, `cachestat`, and `strace` expose what `bonnie++`'s "Per Chr" disk test was actually measuring (`SP` Chapter 12.3.2)?</summary>

`bonnie++` reported `739 Kbytes/sec` on "Sequential Output — Per Chr" (which would imply an impossible `739,000` disk IOPS). Active analysis showed `iostat -sxz 1` had `0` disk IOPS, `bpftrace` on `tracepoint:block:*` had zero `block_rq_issue` events, `cachestat 1` showed `100%` page-cache dirties, `bpftrace` on `k:vfs_write` showed `1`-byte writes into the VFS page cache, and `strace bonnie++ -b` proved `fsync(2)` was never called per byte.
</details>

<details>
<summary>6. How did CPU kernel flame-graph profiling solve the mystery of a new storage server underperforming an older server while disks were idle (`SP` Chapter 12.3.3)?</summary>

Although CPU profiling is often overlooked during disk benchmarks, capturing a kernel CPU flame graph revealed that **`62.17%`** of kernel CPU samples were spent inside **`zfs_zone_io_throttle()`**—an enabled-by-default ZFS I/O throttling resource control on the new OS that was artificially capping throughput.
</details>

<details>
<summary>7. Why can a block-level **trace replay** benchmark make a faster new storage server look slower than an old server (`SP` Chapter 12.2.3)?</summary>

In Gregg's example, the old server had `10 K rpm` disks and a small RAM cache, while the new server had `7,200 rpm` disks but **`16x` more file system RAM cache**. Replaying the old server's post-cache block-device trace directly against the new disks bypassed the `16x` larger file system cache that would have served the real production workload out of RAM.
</details>

<details>
<summary>8. When ramping load (`SP` Chapter 12.3.7), why must you report `990,000 IOPS` at `5 ms` latency instead of `1,000,000 IOPS` at `50 ms` latency?</summary>

Pushing client concurrency past the saturation knee (`990,000 IOPS` at `5 ms`) forces all requests into deep queues (`> 50 ms` average latency), violating acceptable service-level latency for a negligible `1%` throughput gain. Always report throughput at an acceptable target latency ceiling.
</details>

<details>
<summary>9. Perform a **sanity check** (`SP` Chapter 12.3.8) on a benchmark claiming `50,000 IOPS` of `8 Kbyte` reads from an NFS server over a single `1 Gbit/s` Ethernet port.</summary>

$$50,000\text{ IOPS} \times 8\text{ KB} = 400,000\text{ KB/s} \approx \mathbf{3.2\text{ Gbits/s}}$$
Because a single `1 Gbit/s` Ethernet link has a physical wire ceiling of `1.0 Gbit/s` (`~119–120 Mbytes/s` practical TCP payload in one direction), `3.2 Gbits/s` is physically impossible over the wire—proving the benchmark measured local **client RAM caching** rather than the NFS server.
</details>

<details>
<summary>10. Why must you never use `tar(1)` to archive `/proc` counter files before and after a benchmark run (`SP` Chapter 12.3.9)?</summary>

Because virtual files in `/proc` report a file size of **`0` bytes** to the `stat(2)` system call; `tar(1)` trusts `stat(2)`'s zero size and archives empty 0-byte files without reading their text contents. Use a script that reads (`cat`/`cp`) `/proc` files explicitly.
</details>

<details>
<summary>11. Why did running `code/part06/bench_stats.py` with `OPENBLAS_NUM_THREADS=8` on an Apple M3 run $4\times$ slower (`22.9 GFLOP/s`, `CV = 13.0%`) than 4 threads (`90.8 GFLOP/s`, `CV = 4.8%`)?</summary>

The Apple M3 has a heterogeneous core architecture (**4 Performance cores + 4 Efficiency cores**). OpenBLAS partitions panel/update blocks evenly across all 8 threads; at every LU synchronization barrier, the 4 fast P-cores sit idle waiting for the 4 slower E-cores (and OS thread migration jitter inflates the coefficient of variation from `0.8–4.8%` to `13.0%`).
</details>

<details>
<summary>12. What is the floating-point operation count of a dense $n \times n$ LU solve (`HPL`), and what is HPL's scaled residual acceptance formula?</summary>

- **Operation count:** $\frac{2}{3} n^3 + 2 n^2$ floating-point operations.
- **Scaled residual check:**
  $$R = \frac{\|Ax - b\|_\infty}{\epsilon \left(\|A\|_\infty \|x\|_\infty + \|b\|_\infty\right) n} < \mathbf{16}$$
  where $\epsilon$ is machine epsilon (`np.finfo(float).eps` $\approx 2.22 \times 10^{-16}$ for FP64). Any run with $R \ge 16$ is invalid due to memory bit flips, unstable overclocking, or numerical corruption.
</details>

<details>
<summary>13. How do you choose the problem size $N$, block size $NB$, and process grid $P \times Q$ in `HPL.dat`?</summary>

- **Problem size $N$:** Sized so the FP64 matrix ($8 N^2$ bytes) occupies **`80–90%` of total aggregate memory** (maximizing compute-to-communication ratio without triggering swap/OOM).
- **Block size $NB$:** Tuned to the CPU cache or GPU tensor-core tile size (typically `192–512` on CPUs, `1024–4096` on GPUs).
- **Process grid $P \times Q$:** $P \times Q = N_{\text{ranks}}$ with $P \le Q$ and **as close to square as possible** (e.g., $8 \times 8$ for 64 ranks) to balance row and column collective broadcasts.
</details>

<details>
<summary>14. Contrast what **HPL**, **HPCG**, and **STREAM** measure on a supercomputer.</summary>

- **HPL (High-Performance Linpack):** Dense FP64 LU factorization ($O(n^3)$ flops over $O(n^2)$ bytes); measures peak compute (`Rmax`) and sustained power/thermal stability (`60–90%` of `Rpeak`).
- **HPCG (High-Performance Conjugate Gradient):** Sparse multigrid solver with irregular memory access and halo exchanges; measures memory-subsystem and interconnect latency/bandwidth under realistic PDE workloads (typically `< 5%` of `Rpeak`).
- **STREAM (`Copy`, `Scale`, `Add`, `Triad`):** Sequential vector streaming over arrays $\ge 4\times$ last-level cache size; measures sustainable DRAM/HBM memory bandwidth (`80–90%` of theoretical memory bus bandwidth).
</details>

<details>
<summary>15. What do **IOR** and **mdtest** measure, and what three rules prevent client page caches from invalidating an IOR run?</summary>

- **IOR:** Parallel `N-to-1` (shared file) and `N-to-N` (file-per-process) read/write streaming bandwidth and IOPS.
- **mdtest:** Parallel directory and small-file metadata `create`, `stat`, `read`, and `remove` rates (standardized together in **IO500**).
- **Three anti-cache rules:** (1) Pass **`-C` (`reorderTasks`)** so rank $i$ reads back the data written by rank $(i+1) \bmod N$ on a different node, (2) write a total dataset size exceeding $2\times$ aggregate client RAM, and (3) use `O_DIRECT` or drop caches between write and read phases.
</details>

<details>
<summary>16. How do you benchmark GPUDirect Storage (`GDS`) against CPU bounce-buffer I/O using `gdsio`, and what did `ASP` Chapter 5 Table 5-1 show?</summary>

Run `/usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0` comparing:
- **`-x 2` (CPU-staged through pinned host RAM):** `8.0 GB/s` throughput, `1.25 ms` latency, `85%` CPU utilization.
- **`-x 0` (GPUDirect Storage via `cuFile` / `nvidia-fs`):** **`9.6 GB/s` throughput (`+20%`)**, **`1.00 ms` latency (`-20%`)**, and **`25%` CPU utilization**.
</details>

<details>
<summary>17. In `nccl-tests`, define **algorithm bandwidth (`algbw`)** and **bus bandwidth (`busbw`)**, and state the `busbw` multiplier for `AllReduce`, `AllGather`, `ReduceScatter`, `AlltoAll`, and `Broadcast`.</summary>

- **Algorithm bandwidth (`algbw`):** $\text{algbw} = \frac{S}{t}$ (tensor size $S$ divided by elapsed time $t$).
- **Bus bandwidth (`busbw`):** $\text{busbw} = \text{algbw} \times \text{factor}$, normalizing for the actual bytes moved across each rank's bottleneck link so the result can be compared directly against hardware NVLink/NIC wire speed regardless of rank count $n$:
  - **`AllReduce`:** $\text{busbw} = \text{algbw} \times \mathbf{\frac{2(n-1)}{n}}$
  - **`ReduceScatter` / `AllGather` / `AlltoAll`:** $\text{busbw} = \text{algbw} \times \mathbf{\frac{n-1}{n}}$
  - **`Broadcast` / `Reduce` / `SendRecv`:** $\text{busbw} = \text{algbw} \times \mathbf{1}$
</details>

<details>
<summary>18. Calculate `algbw` and `busbw` for an `8 GiB` (`8.59 GB`) `all_reduce_perf` run across `64` GPUs that takes `0.60 s`, and interpret the result on a `400 Gb/s` (`50 GB/s`) NDR InfiniBand cluster.</summary>

$$\text{algbw} = \frac{8.5899\text{ GB}}{0.60\text{ s}} = \mathbf{14.3\text{ GB/s}}$$
$$\text{busbw} = 14.3 \times \frac{2 \times 63}{64} = 14.3 \times 1.96875 = \mathbf{28.2\text{ GB/s}}$$
Against a `50 GB/s` (`400 Gb/s`) NIC per GPU, `28.2 GB/s` is only `56%` of line rate—indicating a topology, rail-alignment (`NCCL_CROSS_NIC`), PCIe/GDR, or congestion issue that should be bisected with pairwise `osu_bw` / `nccl-tests`.
</details>

<details>
<summary>19. How does the **batch-size halving/doubling test** (`ASP` Chapter 5) determine whether a distributed training job is communication-bound or compute-bound?</summary>

In DDP, gradient `all_reduce` volume depends only on parameter count (fixed), whereas forward/backward compute time scales linearly with micro-batch size. If your run achieves `60 GB/s` on a `100 GB/s` NIC and **halving the batch size** leaves NIC throughput pinned at `60 GB/s`, the fabric is the bottleneck (**communication-bound**). If halving the batch size causes average NIC throughput to drop (e.g., to `40 GB/s`, and doubling the batch size shrinks the `all_reduce` fraction of step time), the GPUs are **compute-bound**.
</details>

<details>
<summary>20. List the eight stages of a production **cluster acceptance and burn-in test plan** before signing off on vendor hardware.</summary>

1. **Inventory & firmware baseline audit** (BIOS, BMC, GPU VBIOS, NIC/switch firmware).
2. **24–72 hour thermal/power burn-in** (`stress-ng`, `memtester`, `dcgmi diag -r 3`, `gpu-burn`/HPL, `fio`, `ib_write_bw`) to catch infant-mortality hardware faults.
3. **Single-node sweeps across every node** (`STREAM`, single-node `HPL`/`DGEMM`, 8-GPU `all_reduce_perf`) to flag outlier nodes $> 5\%$ below peer median.
4. **All-pairs / shifted-pair fabric validation** (`osu_latency`, `osu_bw`, `ib_write_bw`, and `NCCL_TESTS_SPLIT` rail tests) checking port error counters before and after.
5. **Parallel storage validation at scale** (`IOR`, `mdtest`, `fio`, `gdsio`).
6. **Full-cluster scale runs** (multi-hour full-fleet `HPL`, `nccl-tests`, and a reference multi-node training job).
7. **Fault-injection & HA drills** (kill a node/link during a checkpointed job, test `slurmctld` failover and `HealthCheckProgram` auto-drain).
8. **Baseline archival & automated regression suite** (converting the acceptance scripts into nightly/post-maintenance canary checks).
</details>

## Sources and review notes

- Methodology, reasons to benchmark, `[Traeger 08]` (415 benchmarks in 106 papers), `[Smaalders 06]`, Bill Joy's 1981 VAX-11/750 to 11/780 4 MB TCP/IP analysis `[Joy 81]`, the 16 benchmarking failures (including the Benchmark Paradox `0.5^3 = 12.5%` `[Gregg 14c]` and 1993 TPC-A Standish Group vs Oracle `discrete transactions` Benchmark Specials `[Shanley 98]` / TPC `2%` pricing rule `[TPC 19a]`), micro-benchmarking (`Table 12.1` 5 file system tests, Solaris `128 Kbyte` slab cache, sunny/cloudy/rainy day testing), simulation (`Whetstone` 1972, `Dhrystone` 1984, `wrk`, `siege`, `hey`, Markov models), trace replay (`10 K rpm` vs `7,200 rpm` + `16x` cache), industry standards (Jim Gray 1985 `Sort, Scan, DebitCredit` / `TPS` `[Anon 85]`, `TPC-C..TPCx-V`, `SPEC`), active benchmarking (`bonnie++` 739 KB/s `Per Chr` analyzed with `iostat`, `bpftrace`, `cachestat`, `strace`, and `putc(3)`/`setbuffer(3)` `[Bourbonnais 08]`), CPU profiling (`zfs_zone_io_throttle()` `62.17%`), ramping load (`randread.pl` `$IOSIZE = 8192` `sysread()` on Sun ZFS Storage Appliance `[Gregg 09b]` and `990,000 IOPS` at `5 ms` vs `1,000,000 IOPS` at `50 ms`), sanity checks (`50,000 IOPS * 8 KB = 400,000 KB/s = 3.2 Gbps` over `1 Gbps` Ethernet `[Gregg 09c]`), statistical analysis, the 6-question Benchmarking Checklist `[Gregg 18d]`, and Section 12.4 Benchmark Questions: read in full from Brendan Gregg, *Systems Performance*, 2nd ed. (`systems-performance-2nd-edition`, `SP`), Chapter 12 ("Chapter 12. Benchmarking").
- MPI/HPC performance context: *Parallel and High Performance Computing* (`parallel-and-high-performance-computing`, `PHPC`).
- `ai-systems-performance-engineering` — Chris Fregly, *AI Systems Performance Engineering* (`ASP`), "Chapter 5. GPU-Based Storage I/O Optimizations" (read in full): benchmarking GPUDirect Storage with `gdsio` (`-I 0 -w 4 -s 10G -i 1M -x 0` for GDS vs `-x 2` for CPU-staged; Table 5-1 example: `8.0 GB/s` at `1.25 ms` average latency and `85%` CPU util vs `9.6 GB/s` at `1.00 ms` average latency and `25%` CPU util, a `+20%` throughput gain; VAST Data GDS showing `+20%` on A100 and `+30%+` on H100), Nsight Systems GDS tracing (`nsys profile --trace=cuda,gds,nvtx,osrt` and `/etc/cufile.json`), and the batch-size halving/doubling test to distinguish communication-bound (`60 GB/s` on a `100 GB/s` NIC stays at `60 GB/s` when batch size is halved) from compute-bound (`60 GB/s` drops to `40 GB/s`).
- `nccl-tests` usage and bus-bandwidth formulas: `NVIDIA/nccl-tests` `README.md` and `doc/PERFORMANCE.md` (commit `afd59ab`). `IOR`/`mdtest`: `hpc/ior` README (commit `e4e4578`). `HPCG`: `hpcg-benchmark/hpcg` README (commit `114602d`).
- Run here: `code/part06/bench_stats.py` and `python3 code/part06/bench_stats_lab.py` (3 passed, 0 failed).
- Explicitly labelled inferences: The Send/Recv `busbw` factor of `1.0` in `nccl_busbw()` is a direct point-to-point identity; the `8 GiB`, `64`-rank, `0.60 s` calculation (`algbw = 14.3 GB/s`, `busbw = 28.2 GB/s`) is a worked application of `doc/PERFORMANCE.md`.
- Not verified on live hardware: multi-node HPL, HPCG, OSU, `nccl-tests`, `IOR`/`mdtest`, and `gdsio` runs on a live GPU cluster (`untested here`).
