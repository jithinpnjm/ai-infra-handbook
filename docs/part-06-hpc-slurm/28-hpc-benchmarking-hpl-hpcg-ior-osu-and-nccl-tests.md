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
| Status | Drafted. **Run**: `code/part06/bench_stats.py` (HPL-style LU solve and a triad, with repetitions and confidence intervals) on an Apple M3 with OpenBLAS in NumPy (results below, including a surprising 4x slowdown at 8 threads). **Read from source**: NVIDIA/nccl-tests `doc/PERFORMANCE.md` and README (commit `afd59ab`, 2026-10-05), IOR/mdtest repository README (hpc/ior commit `e4e4578`, 2026-10-23), HPCG repository (commit `114602d`, 2023-09-23). HPL, OSU micro-benchmarks, STREAM proper, MLPerf and all multi-node/GPU numbers were **not run**. No lab step was run on a cluster. |

## Why this matters for AI infrastructure

A vendor hands you a new cluster with a slide that says it is fast. Before you accept it, you need your own numbers. Benchmarks are how you accept hardware, find the one sick node out of 1,000, compare fabrics and file systems, and check whether a driver upgrade changed anything. They also answer the question every training team eventually asks: is this run as fast as it should be?

The same tools can fool you too. One run on one node, with warm caches, against an untuned baseline, with no measure of variance, on a workload that does not look like yours, gives a clean number that means very little. The skills in this chapter are designing a measurement, running it repeatably, checking it against physics, and interpreting the result. They apply from a CPU micro-test up to a 4,096-GPU all-reduce.

## Prerequisites and outcomes

Before you start, you should know scaling from 6.3, MPI from 6.4, the I/O arithmetic from 6.18 and NCCL from 6.12. Once you finish this chapter, you should be able to do the following.

- Apply an active-benchmarking method. Define the question, control the factors, measure, analyse the bottleneck while the test runs, and sanity-check the result against hardware limits.
- Recognise and avoid the standard benchmarking failures.
- Run and interpret the standard suite, STREAM, HPL, HPCG, IOR and mdtest, OSU micro-benchmarks and `nccl-tests`, and know what each one tells you.
- Compute NCCL bus bandwidth from the time and size of each collective, and compare it with link speed.
- Design acceptance tests and burn-in for a new cluster, plus a periodic regression suite.
- Report results with statistics, configuration and caveats.

## 1. Methodology (Systems Performance, chapter 12)

```mermaid
flowchart LR
  Char["1. Characterize & Design<br/>Question, Working Set, Bounds"] --> Run["2. Execute & Ramp Load<br/>STREAM, HPL/HPCG, IOR/gdsio, nccl-tests"]
  Run --> Active["3. Active Benchmarking<br/>USE, bpftrace, Flame Graphs, Nsight"]
  Active --> Sanity["4. Sanity Check & Stats<br/>Physics Limits, Mean/CV/95% CI"]
  Sanity --> Gate["5. Acceptance & Regression<br/>Why not double? Did it error?"]
```

A benchmark can only tell you how fast the system ran the benchmark. Imagine a purchase report that calls a cluster fast, and then a training team that finds its real jobs run slower than the report suggests. Gregg's chapter in *Systems Performance* opens with the warning "there are lies, damn lies and then there are performance measures" `[Anon 85]`. Its central point is that benchmarks tell you only how fast the system can run the benchmark. It is up to you to understand the result and decide how it applies to your environment.

The chapter's structure, adapted to clusters, is the five-step flow above. Each step feeds the next. The sanity check in step 4 sits between running a test and accepting its result.

Gregg lists the reasons to benchmark. They include system design and purchase decisions, proofs of concept, tuning tunable parameters, development, capacity planning, troubleshooting, and marketing, which he calls benchmarketing. For a purchase, the price/performance ratio is measured over the five-year capital cost of the equipment `[Anon 85]`. The ratio can also be flipped to performance/price, so that bigger is better. On-premises proofs of concept can take weeks or months, because hardware has to ship, be racked, cabled and installed. Cloud instances can be started in minutes, benchmarked, or tested directly with fault-tolerant production traffic. Netflix, for example, runs automated micro-benchmarking and CPU profiling on new cloud instance types.

The chapter leans on two sources in particular. Joy's 1981 study of BSD networking `[Joy 81]` shows how a benchmark exposes a bottleneck. Traeger's survey of storage benchmarks `[Traeger 08]` shows how often benchmarks mislead. The full list from section 12.6 of the book is in the Sources section at the end of this chapter.

A nine-year study of file system and storage benchmarking `[Traeger 08]` surveyed 415 file system and storage benchmarks across 106 research papers. Most popular benchmarks, it found, are flawed and fail to explain true system behavior. Good benchmarks are repeatable, observable, portable, easily presented, realistic and runnable `[Smaalders 06]`. Above all, engage performance engineers while the benchmark is running, rather than handing them numbers afterward.

Bill Joy's classic 1981 analysis of BSD TCP/IP `[Joy 81]` shows why. Joy moved 4 Megabytes from a DEC VAX-11/750, a machine built in 1980, to a VAX-11/780, in 1024-byte records wrapped in 1068-byte Ethernet packets. The transfer took 28 seconds, a user-to-user throughput of 1.2 Megabaud. During it, the 11/750 was CPU-saturated, while the 11/780 had 30% idle time. Kernel CPU time on the sending side was split across Ethernet handling (20%), IP packet processing (10%), TCP processing (30%), checksumming (25%) and user system call handling (15%).

Gregg lists 16 ways a benchmark goes wrong.

1. Casual benchmarking. You benchmark A, but measure B, and conclude you have measured C. For example, you test the file system RAM cache and conclude you measured disk I/O. Beginners often lack the instinct to notice a number that cannot be right, like a 1,000-degree room thermometer.
2. Blind faith, or argumentum ad populum. You assume a popular or vendor-promoted open-source benchmark is valid, without checking what it actually executes.
3. Numbers without analysis. If you have spent less than a week studying a benchmark result, it is probably wrong. When time is short, list the assumptions you have not verified. For example, the tool is not buggy, the disk test measures disk I/O, it drove the disk I/O to its limit, and that I/O pattern matches your application.
4. Complex benchmark tools. The benchmark itself becomes the bottleneck, such as a single-threaded load generator that saturates before the target does. Prefer short C micro-benchmarks, or client simulations written in the same language as the real client.
5. Testing the wrong thing. You test disk IOPS when the production working set runs 100% in RAM cache, or you put engineering effort into an outdated benchmark.
6. Ignoring the environment. You test a database or file system with default OS and storage tunables, while production runs heavily tuned parameters.
7. Ignoring errors. A tool reports fast or slow completion while every request actually failed. Gregg cites a web server benchmark that reported an average latency above 1 second, because a firewall blocked 100% of requests and the tool measured client connection timeout errors.
8. Ignoring variance. You apply a steady average rate, such as 500 reads/s and 50 writes/s at a fixed 10:1 ratio. Real production writes arrive in synchronous or asynchronous bursts every 10 seconds, and they queue behind reads. Model that stateful clustering with a Markov model `[Jain 91]`.
9. Ignoring perturbations. Cron backups, per-minute monitoring agents, cloud noisy neighbours, device interrupts, kernel CPU affinity migration delays and cold caches all add noise. Run benchmarks for minutes, never less than one second. Repeat them, and inspect the full latency distributions.
10. Changing multiple factors. You compare two hosts that differ in switch hop count or cloud placement. Test several cloud instances, and take the median or the distribution.
11. The benchmark paradox `[Gregg 14c]`. If your product has a 50/50 chance of winning each benchmark, you will usually lose. A buyer who runs three independent benchmarks, and requires your system to win all three, gives you a win probability of 0.5 × 0.5 × 0.5 = 0.125, or 12.5%.
12. Benchmarking the competition. You post untuned results for a competitor's product, which customers have spent months tuning. That destroys your credibility.
13. Friendly fire. You undersell your own product. You may misconfigure an undocumented new feature, fail to drive a physical resource to 100% utilisation, or test an older unpatched software release.
14. Misleading benchmarks. You lie by omission, for example by testing a prohibitively expensive custom configuration without disclosing its price. Or you hire several inexperienced third parties and cherry-pick the highest outlier.
15. Benchmark specials `[Shanley 98]`. You engineer a feature only to inflate a benchmark score, without helping real workloads. The term dates to 1993 and the TPC-A benchmark, when the Standish Group accused Oracle of adding a `discrete transactions` option solely for TPC-A. TPC answered with an anti-benchmark-special clause and a pricing rule `[TPC 19a]`. The pricing rule requires the total disclosed price to be within 2% of what a real customer would pay.
16. Cheating. You fabricate numbers outright. This is rare compared with failures 1 to 15.

Gregg groups benchmarks into four types, and each answers a different question. The first is micro-benchmarking, which tests one isolated operation. SysBench covers the CPU, lmbench covers memory I/O, fio covers the file system, hdparm, dd and fio cover direct disk I/O, and iperf covers the network.

Table 12.1 in the book lists five core file system tests. Sequential 512-byte reads give the maximum realistic IOPS, since disks round 1-byte I/O up to 512-byte or 4-Kbyte sectors. Sequential 1-Mbyte reads give the maximum read throughput, and the sweet spot is OS-specific. Solaris, for example, has a 128 Kbyte largest slab cache size. Sequential 1-Mbyte writes give the maximum write throughput. Random 512-byte reads show the random seek and IOPS effect, and random 512-byte writes show the rewrite effect.

Multiply each of those tests by two factors. The first is working set size. A working set much smaller than main memory tests the file system cache, and a much larger one tests physical disk I/O. The second is thread count. A single thread tests clock-speed limits, and multiple threads saturate every CPU. Pair sunny day testing, which measures top speeds under ideal conditions, with cloudy day or rainy day testing. The second kind covers contention, perturbations, variance and degraded components.

The second type is simulation, or macro-benchmarking. It simulates a composite client workload. An NFS mix might be reads at 40%, writes at 7%, getattr at 19% and readdir at 1%. Classic CPU simulations are Whetstone from 1972 and Dhrystone from 1984. HTTP load generators include wrk `[Glozer 19]`, siege `[Fulmer 12]` and hey `[Dogan 20]`. They use stateless random probabilities, or stateful Markov models.

The third type is replay, which replays a captured production trace. Be careful about the layer you replay at. Gregg describes a storage upgrade where the old system had 10 K rpm disks, and the new one had 7,200 rpm disks but 16x more file system RAM cache and faster CPUs. Replaying the old system's block-level disk trace on the new system looked worse, and the sale was lost. The block-level replay bypassed the 16x larger file system page cache, which would have served the real workload from RAM.

The fourth type is industry standards. Jim Gray's 1985 paper "A Measure of Transaction Processing Power" `[Anon 85]` defined the Sort, Scan and DebitCredit tests, and transactions per second (TPS), alongside MIPS and FLOPS. Major standards include TPC (TPC-C, TPC-DS, TPC-E, TPC-H, TPC-VMS, TPCx-HS and TPCx-V) and SPEC (SPEC Cloud IaaS 2018, SPEC CPU 2017, SPECjEnterprise 2018 Web Profile, SPECsfs2014 and SPECvirt_sc2013). The HPC and AI standards are TOP500 HPL, HPCG, IO500 and MLPerf.

Section 12.3 and Table 12.2 describe the methodology, starting with the approach to avoid. Passive benchmarking is fire-and-forget. You pick a tool, run it with some options, make a slide deck, and hand it to management. The method is prone to software bugs, single-thread bottlenecks and testing the wrong layer.

Active benchmarking means analysing the system with observability tools while the benchmark runs `[Gregg 14d]`. Gregg's case study used bonnie++ version 1.97 `[Coker 01]`. Its "Sequential Output — Per Chr" test reported 739 Kbytes/sec at 99% CPU. If that were truly 1-byte disk I/O, it would need an impossible 739,000 disk IOPS.

Running `iostat -sxz 1` during the test showed 0 disk IOPS. A `bpftrace -e 'tracepoint:block:* { @[probe] = count(); }'` probe showed `block_dirty_buffer: 808225` and `block_touch_buffer: 1025678`, with no `block_rq_issue` events at all. `cachestat 1` confirmed 100.00% page-cache hits and dirties. A second probe, `bpftrace -e 'kprobe:vfs_* /comm == "bonnie++"/ { @[probe] = count(); }'`, together with `k:vfs_write { @bytes = hist(arg2); }`, proved bonnie++ was issuing 1,176,936 one-byte `vfs_write()` calls into the OS page cache. Finally, `strace bonnie++ -b` showed `write(3, "6", 1) = 1` and no `fsync(2)` after each byte. Older versions also buffered inside the C library's `putc(3)` and `setbuffer(3)` `[Bourbonnais 08]`.

CPU profiling is easy to overlook in disk benchmarks. Profile both the user and kernel stacks while the benchmark runs. A new storage server unexpectedly underperformed an older one on a disk benchmark, while its disks were mostly idle. A kernel CPU flame graph showed 62.17% of CPU samples inside `zfs_zone_io_throttle()`. That was an overlooked default ZFS I/O throttle, limiting the benchmark.

Next, check Utilization, Saturation and Errors on every hardware and software resource, until you find the one that reaches 100% utilisation. That is the USE method. Pair it with workload characterisation.

Write minimal C or Perl load generators, and check that the compiler does not optimise away dead loops. Then ramp the load. Add client threads one at a time, and plot throughput and latency to find the knee. Gregg's `randread.pl` script used unbuffered `sysread()` with `$IOSIZE = 8192`, run across a farm of NFS clients `[Gregg 09b]`. It drove a Sun ZFS Storage Appliance to nearly 500,000 reads/s, above 3.5 Gbytes/s.

Always pair throughput with a latency limit. Suppose a storage array delivers 990,000 IOPS at 5 ms average latency. Adding more clients pushes it past 1,000,000 IOPS, but only by queueing requests to more than 50 ms average latency. The valid engineering result is 990,000 IOPS.

Check whether a reported number breaks a physical limit. Suppose an NFS server on a single 1 Gbit/s Ethernet port reports 50,000 IOPS of 8 Kbyte reads. That is 50,000 × 8 KB = 400,000 KB/s, or about 3.2 Gbits/s before headers. It is more than three times the line rate. A single-direction TCP ceiling on 1 Gbit/s Ethernet is 119–120 Mbytes/s in practice. Claims of 200, 350, 800 or 1,150 Mbytes/s in one direction therefore expose client-cache illusions `[Gregg 09c]`.

Statistical analysis is needed when time on a shared max-config cluster is scarce. Sales, Marketing, Support, Engineering and Quality all want that cluster. Capture full distributions, standard deviations, error margins, and before-and-after `/proc` counter snapshots. Use a custom read script rather than `tar(1)`. The `tar` tool sees zero-sized `/proc` files through `stat(2)`, so it skips their contents.

Gregg's six-question benchmarking checklist `[Gregg 18d]` asks the following.

- Why not double? What is the actual bottleneck preventing 2× the rate?
- Did it break limits? Sanity-check against physical bandwidth or IOPS limits.
- Did it error? Are timeouts or failed requests skewing the rate?
- Does it reproduce? What is the variance or CV across repetitions?
- Does it matter? Does the operation match the production workload?
- Did it even happen? Confirm with `iostat`, `bpftrace` or counters that traffic reached the target.

When you audit a vendor's claim without direct access to the system, demand disclosures in four areas, as section 12.4 lists them. For general results, ask about production relevance, single node or cluster, total system cost, client configuration, test duration and sample count, average versus peak, the full distribution or percentiles, the limiting factor, the success-to-failure ratio, active analysis screenshots and error margins. For CPU and memory, ask for the exact SKU, any overclocking or water cooling, the DIMM count and socket population, disabled cores, the system-wide CPU utilisation and turbo boost state, physical cores versus hyperthreads, and the BIOS settings. For storage, ask for the drive count, type and protocol, the RAID level, write-back cache, file system journaling and tuning, the working set size against the RAM cache hit ratio, and the file count. For network, ask for the NIC count and type, the topology, the protocols, the socket options and the TCP or UDP sysctl tunables.

Use this ten-point checklist for cluster benchmarks.

1. Write down the question and the success criterion.
2. Record the hardware, firmware, BIOS, driver, library and kernel versions.
3. Verify the system is idle, with `top`, `squeue`, and no other jobs running.
4. Note the clocks and power state, including the governor, GPU persistence and application clocks.
5. Exclude the warm-up.
6. Run at least 5 to 10 repetitions, and report the statistics.
7. Compare the result against a theoretical bound.
8. Check for errors with `dmesg` and the fabric counters, before and after.
9. Change one factor at a time.
10. Archive the raw data and command lines.

Run the sanity check before you believe any number, and reject a figure that breaks a physical limit.

## 2. A statistics harness (tested)

Before you trust any single number, you want a harness that tells you how stable it is. `code/part06/bench_stats.py` runs two tests. The first is an HPL-style dense solve, using NumPy `solve` and LAPACK LU. It counts flops as `2/3 n^3 + 2 n^2`, as HPL does, and it checks the scaled residual against HPL's threshold of 16. The second is a triad-like bandwidth loop. Each test gets a warm-up run and N repetitions. The report gives the mean, the standard deviation, the coefficient of variation (CV), the minimum, median and maximum, and a 95 percent confidence interval (Student t).

The table comes from an Apple M3 with four performance cores and four efficiency cores, running NumPy with OpenBLAS. Each row uses `n = 3000` and 10 repetitions.

| `OPENBLAS_NUM_THREADS` | mean GFLOP/s | CV | min / median / max |
|---|---|---|---|
| 1 | 44.7 | 0.8% | 44.2 / 44.6 / 45.4 |
| 2 | 81.3 | 1.7% | 79.7 / 80.6 / 83.4 |
| 4 | 90.8 | 4.8% | 82.2 / 91.3 / 97.3 |
| 8 (the library default here) | 22.9 | 13.0% | 17.9 / 22.9 / 27.1 |

The residual check printed `scaled residual = 0.003 (PASS)`. The triad loop gave about 75 GB/s, with a CV of 15 percent, in the default configuration. The table teaches five lessons, in order of importance.

1. The default configuration ran four times slower than the best one. Using all 8 threads gave 23 GFLOP/s, less than a single thread managed (44.7). The machine has heterogeneous cores. A statically partitioned parallel LU waits at each synchronisation point for its slowest thread, which here is an efficiency core, and OS scheduling noise adds jitter. This is the "slowest participant sets the pace" effect from 6.3 and 6.14, now showing up on a laptop. A benchmark that simply ran with defaults would report a number off by 4x, with a CV of 13 percent that signals something is wrong.

2. Variance is information. A CV of 0.8 percent with one thread, against 13 percent with eight threads, means the noisy configuration is unstable, not just slow. On a cluster, a node whose repeated runs differ by 10 percent is suspect.

3. Scaling is not monotonic. Going from one to two threads gave 1.8x, two to four gave only 1.1x, and four to eight collapsed. Sweep the parameter instead of assuming more is better.

4. Check the result against a bound. 91 GFLOP/s on four performance cores is plausible for double-precision dense LU with vectorised BLAS on this class of CPU. A number above the hardware peak would point to a bug in the flop count, the timing or the caching.

5. Report the configuration with the number. "91 GFLOP/s" means little without `n`, the thread count, the library, the precision and the machine. Run the same sweep on your own hardware before you trust its shape.

Single-machine, shared with other processes; numbers will not reproduce exactly on your machine.

## 3. The standard suite

### STREAM (memory bandwidth)

STREAM runs four kernels, copy, scale, add and triad, over arrays much larger than the caches, and reports GB/s. Run it with one thread per core, or per NUMA domain, pinned in place. Section 6.5 covers first-touch placement and `OMP_PROC_BIND`. Compare the result with the theoretical DRAM or HBM bandwidth, which is channels times transfer rate times 8 bytes. On CPUs, a good result is 80 to 90 percent of theoretical. The triad loop in the harness is a toy. For real numbers, use the real STREAM with `-O3 -fopenmp`, and an array at least 4x the size of the last-level cache. On GPUs, use the GPU STREAM variants or `nvbandwidth`.

### HPL (High-Performance Linpack)

HPL solves `Ax = b` with LU factorisation (6.1). Its inputs live in `HPL.dat`. The problem size N should be as large as memory allows, typically 80 to 90 percent of total RAM, because the matrix takes 8N^2 bytes. The block size NB is tuned, for example 192 to 512 on CPUs and larger on GPUs. The process grid P x Q should be near-square, with P at most Q and a product equal to the number of ranks. Broadcast and panel algorithms and the lookahead depth are also set here. The result is Rmax in GFLOP/s, plus a pass or fail residual.

Efficiency is Rmax divided by Rpeak. Well-tuned GPU systems land in a broad range of 60 to 90 percent, depending on the architecture, so check published results for your hardware generation. A node that scores well below its peers has a hardware problem, such as throttling, a failing DIMM or a slow link. NVIDIA provides optimised HPL containers, covering HPL for GPUs and HPL-AI or HPL-MxP for mixed precision, with their own run scripts. Build and tune instructions are in the NGC catalogue. HPL stresses compute and, to a moderate degree, the network, so it doubles as a burn-in workload for power and thermals. A full HPL run on a large cluster takes hours. Use it as an acceptance test, and for power and thermal validation (6.30).

### HPCG (High-Performance Conjugate Gradient)

HPCG is a sparse-matrix conjugate gradient with a multigrid preconditioner. It is limited by memory bandwidth, uses global communication and has irregular access, so it typically reaches only a few percent of Rpeak (6.1). The repository, hpcg-benchmark/hpcg at version 3.1, ships reference code, a `bin/hpcg.dat` input file for the local problem dimensions and run time, and a `QUICKSTART`. The official rules require a minimum run time, commonly 30 minutes for submissions. The benchmark reports GFLOP/s with a validity check. Use it to compare memory systems and interconnects under a load that looks more like an application than HPL does.

### IOR and mdtest

The `hpc/ior` repository contains both tools. IOR, short for Interleaved or Random I/O, measures parallel I/O bandwidth. Each MPI rank writes or reads blocks to a shared file, or to one file per process. You set the transfer size, block size, API (POSIX, MPI-IO, HDF5 or S3), whether I/O is collective or independent, whether to use `fsync`, and whether to reorder tasks to defeat client caching. mdtest measures metadata rates, with create, stat, read and remove operations on many files and directories, using a set directory depth and per-rank trees. The README says to build with `./bootstrap && ./configure && make`.

For storage tests (6.18, 6.19), follow a method. Defeat the client caches with rank reordering (`-C`), large sizes and dropped caches. Run enough ranks to saturate the system, by scaling tasks and nodes. Keep write and read phases separate. Use your real transfer size, from 1 to 4 MiB. Repeat each run, and record the file system striping. The IO500 list standardises IOR and mdtest runs, and publishes the results.

### Benchmarking GPUDirect Storage with `gdsio`

To benchmark the storage-to-GPU DMA paths, GPUDirect Storage (GDS, Part 13), NVIDIA ships `/usr/local/cuda/gds/tools/gdsio`. Compare the CPU-staged path, `-x 2`, which uses pinned host memory with async copies, against the direct GDS path, `-x 0`, which moves data from storage straight into GPU HBM through `cuFile` and `nvidia-fs`. Both run in read mode (`-I 0`), with 4 workers (`-w 4`), a 10 GiB file (`-s 10G`), a 1 MiB I/O size (`-i 1M`) and GPU 0 (`-d 0`). They have not been run on a live system.

```bash
# Before: Storage -> CPU Memory -> GPU (CPU-staged path, -x 2) (untested here)
/usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 2

# After: Storage -> GPU Memory via GPUDirect Storage (GDS path, -x 0) (untested here)
/usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 0
```

The book's example, Table 5-1, shows what this comparison looks like. The CPU-staged path reaches 8.0 GB/s of total throughput at 1.25 ms average latency, with 85% CPU utilisation. The GDS path reaches 9.6 GB/s at 1.00 ms, with 25% CPU utilisation. That is a 20% throughput gain and 20% lower latency, and it also frees host CPU cores. VAST Data's GDS benchmarks in the book report a 20% sequential read throughput boost on an A100 GPU, and 30% or more on an H100. To trace `cuFile` calls alongside CUDA and OS runtime activity on a timeline, run Nsight Systems with `nsys profile --trace=cuda,gds,nvtx,osrt` (untested here), and enable the `cuFile` static tracepoints in `/etc/cufile.json`.

### OSU Micro-Benchmarks (MPI)

The OSU micro-benchmarks come from Ohio State University, from the MVAPICH team. They include `osu_latency` for ping-pong, `osu_bw` and `osu_bibw` for bandwidth, `osu_allreduce`, `osu_alltoall`, `osu_bcast` and `osu_barrier`. CUDA variants, selected with `-d cuda`, use GPU buffers. Run them between two nodes first, to get the best-case point-to-point number. Then run them across racks, which adds switch hops and exposes the topology.

Compare the result with line rate. NDR InfiniBand at 400 Gb/s is about 50 GB/s per direction before protocol overhead. A point-to-point bandwidth far below that suggests a TCP fallback, a downtrained link, a PCIe problem or a wrong NIC mapping (6.4, section 10). The ping-pong model from 6.4 applies to the latency and bandwidth curve.

### NCCL tests

The NVIDIA/nccl-tests repository builds `all_reduce_perf`, `all_gather_perf`, `reduce_scatter_perf`, `broadcast_perf`, `reduce_perf`, `alltoall_perf`, `sendrecv_perf` and others. For multi-node runs, build with `make MPI=1 MPI_HOME=... CUDA_HOME=... NCCL_HOME=...`. The README gives these usage examples.

```bash
./build/all_reduce_perf -b 8 -e 128M -f 2 -g 8                  # one process, 8 GPUs, sizes 8 B .. 128 MiB, doubling
mpirun -np 64 -N 8 ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1  # 64 ranks over 8 nodes, one GPU per rank
srun -N 8 --ntasks-per-node=8 --gpus-per-task=1 ./build/all_reduce_perf_mpi -b 8 -e 8G -f 2   # Slurm (binary built with MPI=1 and a suffix)
```

The flags control the sweep. `-b/-e` set the minimum and maximum bytes, `-f` sets the multiplicative step, and `-i` sets an additive one. `-g` sets GPUs per thread, and `-n` sets the iterations, which default to 20. `-w` sets the warm-up iterations, which default to 1. `-c` turns on correctness checking. In MPI mode, `-a` controls how results are averaged across ranks: 0 for rank 0, 1 for the average, 2 for the minimum, and 3 for the maximum. `-t` sets threads per process. `NCCL_TESTS_SPLIT` runs several concurrent sub-communicators. For example, `MOD 8` runs eight parallel operations, one GPU per node each, which tests rail-wise network paths.

Each size prints the time in microseconds, then `algbw` (algorithm bandwidth, size divided by time) and `busbw` (bus bandwidth). Each size appears twice, once for out-of-place and once for in-place. The `doc/PERFORMANCE.md` file in the repository explains the rest. When you read the output, you will see both columns side by side. At small sizes, time is dominated by latency. At large sizes, it becomes overhead plus size divided by bandwidth. `algbw` is what an application experiences. `busbw` is `algbw` times a correction factor, which reflects how much data each rank link must carry for that collective. That lets you compare the result with the hardware peak, whatever the rank count. The factors are below.

| Collective | busbw = algbw x |
|---|---|
| AllReduce | 2(n-1)/n |
| ReduceScatter | (n-1)/n |
| AllGather | (n-1)/n |
| AlltoAll | (n-1)/n |
| Broadcast, Reduce | 1 |
| Send/Recv | 1 |

The first six rows come from the `nccl-tests` summary list. The Send/Recv factor of 1 is not in that list. It follows from the fact that a point-to-point transfer moves exactly its size over one link. The AllReduce factor comes from the best-case time, t = (S/B) x 2(n-1)/n. Each of the n links carries 2(n-1)/n times the data.

Here is a worked example. Take 64 ranks, an 8 GiB message and a measured time of 0.60 s. The algbw is 8.59 GB divided by 0.60 s, which gives 14.3 GB/s. The busbw is 14.3 x 2 x 63/64, which gives 28.2 GB/s. If each GPU has a 400 Gb/s (50 GB/s) NIC, then 28.2 GB/s is 56 percent of the NIC rate. That is worth investigating for NIC mapping, routing and congestion. A healthy 8-GPU NVSwitch node runs far higher within the node, in the hundreds of GB/s, so compare intra-node and inter-node results separately.

To use this in practice, run the tests in a fixed order. Start with a single-node all-reduce on every node, which finds a bad GPU, NVLink or PCIe link. Next, test pairs of nodes, which finds bad NICs or cables, by rotating the pairs. Then run the full allocation at several sizes. Compare each result with the baseline from a golden run, per switch tier. Run the whole sequence after maintenance, and before you release nodes. Add `NCCL_DEBUG=INFO` to confirm the transport (6.12).

Batch-size halving and doubling tells you whether a distributed training job is communication-bound or compute-bound. When you profile a real DDP backward pass, the gradient `all_reduce` payload depends on the number of model parameters, not the batch size. Backward compute, however, scales with the batch size. In the book's example, suppose the gradient `all_reduce` reaches 60 GB/s across a 100 GB/s NIC. Halve the batch size, which halves compute and keeps the gradient bytes fixed. If NIC throughput stays at 60 GB/s, the network is the bottleneck, so the job is communication-bound. If it drops from 60 GB/s to 40 GB/s, the GPUs were not finishing compute fast enough to keep the NIC busy, so the job is compute-bound.

Then double the batch size as a reverse check. A communication-bound job keeps the NIC pinned at 60 GB/s. A compute-bound job spends a shrinking share of each iteration in `all_reduce`, as compute time grows. Combine this test with `nsys` timelines, looking for NCCL wait gaps between compute kernels. Add `ncu` kernel profiles too. They show whether a slow NCCL kernel is 60% SM busy over PCIe, or 90% SM busy over NVLink.

### MLPerf

MLCommons runs MLPerf Training and Inference. The benchmarks cover end-to-end model training and inference scenarios, with defined rules and quality targets. They show how a complete stack performs on standard models, but vendors tune them heavily. Use the published rules and reference implementations to benchmark your own cluster, and remember that your workload may differ. Framework-level numbers, such as tokens/s, MFU, and time to train a fixed number of steps, are the final arbiter (Parts 14 and 15).

## 4. Acceptance testing and burn-in

Picture the day a new cluster is handed over. The vendor says it is ready, and your team has to decide whether it is. A new cluster should not enter production on the vendor's word, so you need evidence of your own. The plan below runs from hardware checks up to full-cluster tests.

1. Audit the inventory and firmware. Confirm that the BIOS, BMC, NIC and GPU firmware on every node matches the baseline from Parts 7 and 9.
2. Burn in the hardware. Stress the CPU and memory with `stress-ng` and `memtester`, the GPUs with `dcgmi diag -r 3`, `gpu-burn` or HPL, and the disks with `fio`. Test the network with iperf3 and RDMA perftest. Run for 24 to 72 hours, and watch for errors and thermal throttling. Infant mortality shows up here.
3. Check per-node performance. Run STREAM, single-node HPL or DGEMM, and single-node NCCL. Compare each node with the median of its peers, and flag outliers, such as any node below 95 percent of the median.
4. Validate the fabric. Run `ib_write_bw` and `ib_send_lat` between all node pairs in a shifted pattern, or use the vendor's all-to-all validation. Then run `nccl-tests` at scale. Check the fabric error counters before and after.
5. Validate storage. Run IOR and mdtest at scale, and fio from each client, against the targets in the purchase specification.
6. Run the system end to end. Run a full-cluster HPL to test power, cooling and stability. Follow it with a multi-day training-like job. Inject failures, such as pulling a cable or killing a node, to test recovery.
7. Smoke-test the scheduler and software. Check the Slurm features, containers, identity and monitoring covered in 6.7 to 6.26.
8. Document the results. Record the expected values per node type, the tolerances, and a pass or fail report. Get it signed off before each payment milestone.

Keep the suite as a regression test. Run a short version nightly or weekly, and after every change to the driver, firmware, kernel, NCCL or Slurm. Trend the results, and alert on drops (6.26).

## 5. Reporting

Start with what a reader needs from a report. A good benchmark report states the question and the system: hardware, firmware, software versions, topology and node count. It gives the command lines, the configuration files and the environment variables. It also says how many runs were made, with the statistics (mean or median, spread and confidence interval), and it names the baseline or theoretical bound. It notes which resources limited the run, using USE. It records anomalies and excluded runs, says where the raw data lives, and gives the conclusions with their caveats. Present distributions as box plots and scaling curves, not single numbers.

### Remeasure after every change

As with any debugging effort, change only one or two things at a time, and then measure. Without that discipline, you cannot tell which change helped. When you reach good scaling on the current configuration, note the good metric values. Then aim to keep those values as you scale. Each change should move you toward the goal, and you should be able to reach the same good numbers again.

### Remove hidden synchronization and tune the environment

Unnecessary synchronization can quietly serialize your work. Remove `torch.cuda.synchronize()` calls and barriers that force everything to wait, because they can line up execution in the wrong order. The book covers this in its PyTorch chapter. If the environment needs tuning, set `NCCL_IGNORE_CPU_AFFINITY=1` when it helps. You can also pin CPU threads to a different topology.

Small changes like these sometimes turn poor resource use into high use. That is not always easy, but it is worth trying. Measure after each change, as described above, so you know which one mattered.

### Use the right tools for the job

NCCL is built for scalable collective operations, such as all-reduce, which training uses heavily. NIXL targets high-throughput point-to-point and streaming transfers, which inference often needs. Use NIXL where token streaming dominates the workload, and prefer NCCL or NVSHMEM for bulk collective and symmetric-memory patterns.

GPUDirect RDMA and GDS both skip the host memory bounce buffer, on the network path and the storage path. The CPU still schedules those transfers. Always use `DistributedDataParallel` over `DataParallel` for multi-GPU training. These libraries are heavily tuned, so use them rather than reinventing the wheel.

### Document and educate

Tuning often depends on tacit team knowledge, such as which environment variables are overridden or which library versions have bugs. Write these findings into the code or configuration file, where the next reader will see them. A note can be as simple as this: in this cluster, setting `NCCL_SOCKET_NTHREADS=2` improved multinode throughput by 10%. Make this standard practice, so the lesson survives staff changes.

## 6. Lab

Start on your laptop with the self-checking Python lab. Run `code/part06/bench_stats_lab.py`. It calls `hpl_like()` and `triad()` from `code/part06/bench_stats.py`, and it verifies that the dense LU solve passes HPL's scaled residual check, $< 16.0$. It also checks the `nccl-tests` `algbw` and `busbw` formulas. For example, 8 GiB across 64 ranks in 0.60 s gives `algbw = 14.3 GB/s` and `busbw = 28.2 GB/s` for `AllReduce`, and `14.1 GB/s` for `AllGather`. Last, it runs two sanity checks from Chapter 12 of Systems Performance: `50,000 IOPS * 8 KB = 400,000 KB/s = 3.2 Gbps > 1 Gbps` limit, and the Benchmark Paradox, `0.5^3 = 12.5%`.

```bash
python3 code/part06/bench_stats_lab.py
```

The tested tasks run on your laptop. Work through these four.

1. Run `bench_stats.py` with `OPENBLAS_NUM_THREADS` set to 1, 2, 4, 8 and the number of your physical cores, with 10 repetitions each. Record the mean and CV, and explain the shape.
2. Change `n` to 1000 and then to 6000. How does GFLOP/s scale, and why?
3. Compare the triad with a compiled STREAM, built with the 6.5 toolchain.
4. Compute busbw for 8 sample measurements by hand, using the formulas above.

The next seven tasks need a cluster, and none of them was run for this handbook.

5. Run STREAM on every node, and list the outliers.
6. Run single-node and 2-node HPL, or the NVIDIA HPL container, and compute the efficiency.
7. Run OSU latency and bandwidth between node pairs across racks.
8. Run `nccl-tests` `all_reduce` at 1, 2, 4 and 8 nodes, and plot busbw against size.
9. Run IOR and mdtest on `/home` and on scratch, with 1 to 64 ranks.
10. Write a burn-in plan for 16 nodes.
11. Inject a fault, such as throttling a GPU with a lower power cap or unplugging a cable, and see what each test shows.

Start with the tested tasks. They show whether your harness behaves before you spend cluster time.

## 7. Interview angles

- You run `all_reduce_perf` and get 30 GB/s busbw on 64 GPUs with 50 GB/s NICs. What do you check next?
- Explain `algbw` versus `busbw`, and why the all-reduce factor is 2(n-1)/n.
- What makes a benchmark result trustworthy? List the checks.
- Why did eight threads run slower than one in the harness?
- How would you acceptance-test a new GPU cluster?
- HPL, HPCG and MLPerf: what does each one tell a buyer?
- How do you benchmark a parallel file system without measuring RAM?
- A benchmark shows one node 8 percent slower than its peers. How do you decide whether that is a problem?
- What is active benchmarking?

## Exercises

Try each one on paper before you run any code.

1. Run `python3 code/part06/bench_stats_lab.py`. Why does `hpl_like()` run a throwaway solve before its timed repetitions?
2. The check in `hpl_like()` is a scaled residual that must stay below 16. What does it prove about the answer?
3. On a 4P+4E Apple M3, setting `OPENBLAS_NUM_THREADS=8` dropped throughput from 90.8 to 22.9 GFLOP/s. The coefficient of variation rose from 4.8 to 13.0 percent. Why?
4. Use `nccl_busbw()` for an 8 GiB collective across 64 ranks that finishes in 0.60 s. What are `algbw` and the AllReduce `busbw`? The answers are 14.3 and 28.2 GB/s.
5. What `busbw` do AllGather, ReduceScatter, and AlltoAll give for the same run? You should get 14.1 GB/s.
6. The NIC is a 400 Gb/s NDR InfiniBand rail, which is 50 GB/s. The AllReduce reaches 28.2 GB/s, which is 56 percent. Name four checks you would run to explain the gap.
7. Brendan Gregg found that a `bonnie++` result of 739 KB/s was really 1-byte `vfs_write()` calls into the page cache. Which tools showed this: `iostat -sxz 1`, `bpftrace`, `cachestat 1`, and `strace`? What did each one show?
8. A vendor claims 50,000 IOPS of 8 KB reads over a 1 Gbit/s Ethernet link. Show why that cannot be true. The arithmetic is 400,000 KB/s, which is 3.2 Gbps.
9. An 8-GPU node has 640 GiB of HBM, or 2,048 GiB of host RAM. HPL stores an N by N matrix of 8-byte numbers. What N fills 85 percent of the HBM?
10. For 64 ranks, choose a near-square process grid. A grid of P = 8 by Q = 8 is the usual answer.
11. What do HPL, HPCG, and STREAM Triad each measure? HPL usually reaches 60 to 90 percent of peak. HPCG reaches a few percent.
12. Write the `IOR` and `mdtest` flags that defeat client page caching. Cover `-C` for rank reordering, a file size over twice the aggregate client RAM, and separate write and read phases. Chapter 5 of *AI Systems Performance Engineering* is the guide.
13. Compare two `gdsio` runs. With `-x 2`, the CPU-staged path reaches 8.0 GB/s at 1.25 ms and 85 percent CPU. With `-x 0`, GPUDirect Storage reaches 9.6 GB/s at 1.00 ms and 25 percent CPU. What does the difference tell you?
14. A multi-node DDP run reaches 60 GB/s during the gradient AllReduce over 100 GB/s NICs. You halve and double the micro-batch size. A network-bound job stays at 60 GB/s, and a compute-bound job drops to 40 GB/s. How do `nsys` timeline gaps and `ncu` SM occupancy support the diagnosis?

---

## Checkpoint

<details>
<summary>1. What is the difference between **passive benchmarking** and **active benchmarking** (Systems Performance, chapter 12)?</summary>

- **Passive benchmarking:** You run a tool, record only its final number, and move on. This often measures the wrong layer, such as the page cache or firewall timeouts, or it bottlenecks on the benchmark client itself.
- **Active benchmarking (`[Gregg 14d]`):** You analyse the system while the benchmark runs. Tools such as `iostat`, `bpftrace`, `perf` flame graphs, `cachestat`, `nvidia-smi dmon`, `nsys` and `ibstat` confirm what is really being tested. The USE method then finds the resource at 100% utilisation.
</details>

<details>
<summary>2. State Brendan Gregg's **6-Question Benchmarking Checklist** (Systems Performance, chapter 12.3.10).</summary>

1. **Why not double?** What specific resource stopped the benchmark from running twice as fast?
2. **Did it break limits?** Check the result against physical wire, bus or disk ceilings.
3. **Did it error?** Check whether failed requests or timeouts skewed the result.
4. **Does it reproduce?** Check the CV and confidence intervals across repetitions.
5. **Does it matter?** Check that the workload matches production.
6. **Did it even happen?** Confirm with kernel or hardware counters that I/O or network packets reached the target.
</details>

<details>
<summary>3. Explain the **Benchmark Paradox** (Systems Performance, chapter 12.1.3) and its mathematical implication for multi-test evaluations.</summary>

Suppose your product has a 50% (0.5) chance of winning any single noisy or untuned benchmark. A buyer requires it to win three benchmarks in a row. The chance of winning all three is:
$$0.5 \times 0.5 \times 0.5 = 0.125 = \mathbf{12.5\%}$$
In Gregg's words, if your product's chances of winning a benchmark are 50/50, you will usually lose.
</details>

<details>
<summary>4. What is a **Benchmark Special** (Systems Performance, chapter 12.1.3), when did the term originate, and what two rules did the TPC introduce to stop it?</summary>

A **benchmark special** is a feature or pricing discount built only to inflate a benchmark score, with no benefit to real customer workloads. The term dates to **`1993`**. The Standish Group challenged Oracle's `discrete transactions` option in the **TPC-A** benchmark (`[Shanley 98]`). The TPC responded with two rules. The first bans any implementation that raises scores without improving real-world performance. The second requires disclosed pricing to be within **`2%`** of actual customer pricing (`[TPC 19a]`).
</details>

<details>
<summary>5. How did active benchmarking with `iostat`, `bpftrace`, `cachestat`, and `strace` expose what `bonnie++`'s "Per Chr" disk test was actually measuring (Systems Performance, chapter 12.3.2)?</summary>

`bonnie++` reported `739 Kbytes/sec` on "Sequential Output — Per Chr". That would imply an impossible `739,000` disk IOPS. The active analysis showed otherwise. `iostat -sxz 1` showed `0` disk IOPS. `bpftrace` on `tracepoint:block:*` found zero `block_rq_issue` events. `cachestat 1` showed `100%` page-cache dirties. `bpftrace` on `k:vfs_write` showed `1`-byte writes into the VFS page cache. Finally, `strace bonnie++ -b` showed that `fsync(2)` was never called per byte.
</details>

<details>
<summary>6. How did CPU kernel flame-graph profiling solve the mystery of a new storage server underperforming an older server while disks were idle (Systems Performance, chapter 12.3.3)?</summary>

CPU profiling is easy to overlook in disk benchmarks. A kernel CPU flame graph showed that **`62.17%`** of kernel CPU samples were spent inside **`zfs_zone_io_throttle()`**. That is a ZFS I/O throttle, enabled by default on the new OS, and it was capping throughput artificially.
</details>

<details>
<summary>7. Why can a block-level **trace replay** benchmark make a faster new storage server look slower than an old server (Systems Performance, chapter 12.2.3)?</summary>

In Gregg's example, the old server had `10 K rpm` disks and a small RAM cache. The new server had `7,200 rpm` disks, but **`16x` more file system RAM cache**. Replaying the old server's block-device trace directly onto the new disks skipped that larger cache, which would have served the real workload from RAM.
</details>

<details>
<summary>8. When ramping load (Systems Performance, chapter 12.3.7), why must you report `990,000 IOPS` at `5 ms` latency instead of `1,000,000 IOPS` at `50 ms` latency?</summary>

Pushing client concurrency past the saturation knee, `990,000 IOPS` at `5 ms`, forces requests into deep queues. The average latency rises above `50 ms`. That buys a negligible `1%` throughput gain at a far worse latency. Always report throughput at an acceptable latency ceiling.
</details>

<details>
<summary>9. Perform a **sanity check** (Systems Performance, chapter 12.3.8) on a benchmark claiming `50,000 IOPS` of `8 Kbyte` reads from an NFS server over a single `1 Gbit/s` Ethernet port.</summary>

$$50,000\text{ IOPS} \times 8\text{ KB} = 400,000\text{ KB/s} \approx \mathbf{3.2\text{ Gbits/s}}$$
A single `1 Gbit/s` Ethernet link carries about `119–120 Mbytes/s` of TCP payload in one direction. The claim is therefore physically impossible over the wire. The benchmark measured local **client RAM caching**, not the NFS server.
</details>

<details>
<summary>10. Why must you never use `tar(1)` to archive `/proc` counter files before and after a benchmark run (Systems Performance, chapter 12.3.9)?</summary>

Virtual files in `/proc` report a size of **`0` bytes** to `stat(2)`. `tar(1)` trusts that size, so it archives empty files without reading their contents. Use a script that reads the files with `cat` or `cp` instead.
</details>

<details>
<summary>11. Why did running `code/part06/bench_stats.py` with `OPENBLAS_NUM_THREADS=8` on an Apple M3 run $4\times$ slower (`22.9 GFLOP/s`, `CV = 13.0%`) than 4 threads (`90.8 GFLOP/s`, `CV = 4.8%`)?</summary>

The Apple M3 has heterogeneous cores, with **4 performance cores and 4 efficiency cores**. OpenBLAS splits the panel and update blocks evenly across all 8 threads. At every LU synchronisation barrier, the 4 fast cores sit idle, waiting for the slower efficiency cores. OS thread migration adds jitter as well, which pushes the CV from `0.8–4.8%` up to `13.0%`.
</details>

<details>
<summary>12. What is the floating-point operation count of a dense $n \times n$ LU solve (`HPL`), and what is HPL's scaled residual acceptance formula?</summary>

- **Operation count:** $\frac{2}{3} n^3 + 2 n^2$ floating-point operations.
- **Scaled residual check:**
  $$R = \frac{\|Ax - b\|_\infty}{\epsilon \left(\|A\|_\infty \|x\|_\infty + \|b\|_\infty\right) n} < \mathbf{16}$$
  Here $\epsilon$ is machine epsilon, `np.finfo(float).eps` $\approx 2.22 \times 10^{-16}$ for FP64. Any run with $R \ge 16$ is invalid. The usual causes are memory bit flips, unstable overclocking or numerical corruption.
</details>

<details>
<summary>13. How do you choose the problem size $N$, block size $NB$, and process grid $P \times Q$ in `HPL.dat`?</summary>

- **Problem size $N$:** Pick N so the FP64 matrix, which takes $8 N^2$ bytes, uses **`80–90%` of total aggregate memory**. That maximises the ratio of compute to communication without triggering swap or OOM.
- **Block size $NB$:** Tune it to the CPU cache or the GPU tensor-core tile size. The typical range is `192–512` on CPUs and `1024–4096` on GPUs.
- **Process grid $P \times Q$:** Make $P \times Q$ equal the number of ranks, with $P \le Q$, and as close to square as possible, such as $8 \times 8$ for 64 ranks. That balances the row and column collective broadcasts.
</details>

<details>
<summary>14. Contrast what **HPL**, **HPCG**, and **STREAM** measure on a supercomputer.</summary>

- **HPL (High-Performance Linpack):** Dense FP64 LU factorisation, with $O(n^3)$ flops over $O(n^2)$ bytes. It measures peak compute (`Rmax`), and sustained power and thermal stability, at `60–90%` of `Rpeak`.
- **HPCG (High-Performance Conjugate Gradient):** A sparse multigrid solver with irregular memory access and halo exchanges. It measures memory-subsystem and interconnect latency and bandwidth under PDE-style workloads, and typically reaches `< 5%` of `Rpeak`.
- **STREAM (`Copy`, `Scale`, `Add`, `Triad`):** Sequential vector streaming over arrays at least $4\times$ the last-level cache size. It measures sustainable DRAM or HBM bandwidth, which is `80–90%` of the theoretical memory bus bandwidth.
</details>

<details>
<summary>15. What do **IOR** and **mdtest** measure, and what three rules prevent client page caches from invalidating an IOR run?</summary>

- **IOR:** Parallel `N-to-1` (shared file) and `N-to-N` (file-per-process) read and write streaming bandwidth and IOPS.
- **mdtest:** Parallel directory and small-file metadata rates for `create`, `stat`, `read` and `remove`. The two tools are standardised together in **IO500**.
- **Three anti-cache rules:** First, pass **`-C` (`reorderTasks`)**, so rank $i$ reads back the data written by rank $(i+1) \bmod N$ on a different node. Second, write a total dataset larger than $2\times$ the aggregate client RAM. Third, use `O_DIRECT` or drop caches between the write and read phases.
</details>

<details>
<summary>16. How do you benchmark GPUDirect Storage (`GDS`) against CPU bounce-buffer I/O using `gdsio`, and what did AI Systems Performance Engineering chapter 5, Table 5-1, show?</summary>

Run `/usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0`, and compare two modes.

- **`-x 2` (CPU-staged through pinned host RAM):** `8.0 GB/s` of throughput, `1.25 ms` of latency and `85%` CPU utilisation.
- **`-x 0` (GPUDirect Storage through `cuFile` and `nvidia-fs`):** **`9.6 GB/s` of throughput (`+20%`)**, **`1.00 ms` of latency (`-20%`)**, and `25%` CPU utilisation.
</details>

<details>
<summary>17. In `nccl-tests`, define **algorithm bandwidth (`algbw`)** and **bus bandwidth (`busbw`)**, and state the `busbw` multiplier for `AllReduce`, `AllGather`, `ReduceScatter`, `AlltoAll`, and `Broadcast`.</summary>

- **Algorithm bandwidth (`algbw`):** $\text{algbw} = \frac{S}{t}$, the tensor size $S$ divided by the elapsed time $t$.
- **Bus bandwidth (`busbw`):** $\text{busbw} = \text{algbw} \times \text{factor}$. The factor accounts for the bytes each rank's bottleneck link actually moves, so the result can be compared with NVLink or NIC wire speed whatever the rank count $n$.
  - **`AllReduce`:** $\text{busbw} = \text{algbw} \times \mathbf{\frac{2(n-1)}{n}}$
  - **`ReduceScatter` / `AllGather` / `AlltoAll`:** $\text{busbw} = \text{algbw} \times \mathbf{\frac{n-1}{n}}$
  - **`Broadcast` / `Reduce` / `SendRecv`:** $\text{busbw} = \text{algbw} \times \mathbf{1}$
</details>

<details>
<summary>18. Calculate `algbw` and `busbw` for an `8 GiB` (`8.59 GB`) `all_reduce_perf` run across `64` GPUs that takes `0.60 s`, and interpret the result on a `400 Gb/s` (`50 GB/s`) NDR InfiniBand cluster.</summary>

$$\text{algbw} = \frac{8.5899\text{ GB}}{0.60\text{ s}} = \mathbf{14.3\text{ GB/s}}$$
$$\text{busbw} = 14.3 \times \frac{2 \times 63}{64} = 14.3 \times 1.96875 = \mathbf{28.2\text{ GB/s}}$$
Against a `50 GB/s` (`400 Gb/s`) NIC per GPU, `28.2 GB/s` is only `56%` of line rate. That points to a topology, rail-alignment (`NCCL_CROSS_NIC`), PCIe or GDR, or congestion problem. Bisect it with pairwise `osu_bw` and `nccl-tests` runs.
</details>

<details>
<summary>19. How does the **batch-size halving/doubling test** (AI Systems Performance Engineering chapter 5) determine whether a distributed training job is communication-bound or compute-bound?</summary>

In DDP, the gradient `all_reduce` volume depends only on the parameter count, which is fixed. Forward and backward compute time, however, scales linearly with the micro-batch size. Suppose your run reaches `60 GB/s` on a `100 GB/s` NIC. If halving the batch size leaves NIC throughput pinned at `60 GB/s`, the fabric is the bottleneck, so the job is **communication-bound**. If halving the batch size drops the average NIC throughput, to `40 GB/s` for example, the GPUs are **compute-bound**. Doubling the batch size then shrinks the share of step time spent in `all_reduce`.
</details>

<details>
<summary>20. List the eight stages of a production **cluster acceptance and burn-in test plan** before signing off on vendor hardware.</summary>

1. **Inventory and firmware baseline audit:** BIOS, BMC, GPU VBIOS, and NIC or switch firmware.
2. **24–72 hour thermal and power burn-in:** `stress-ng`, `memtester`, `dcgmi diag -r 3`, `gpu-burn` or HPL, `fio`, and `ib_write_bw`. The goal is to catch infant-mortality hardware faults.
3. **Single-node sweeps across every node:** `STREAM`, single-node `HPL` or `DGEMM`, and 8-GPU `all_reduce_perf`. Flag any outlier node more than $5\%$ below the peer median.
4. **All-pairs or shifted-pair fabric validation:** `osu_latency`, `osu_bw`, `ib_write_bw`, and `NCCL_TESTS_SPLIT` rail tests. Check the port error counters before and after.
5. **Parallel storage validation at scale:** `IOR`, `mdtest`, `fio`, and `gdsio`.
6. **Full-cluster scale runs:** A multi-hour full-fleet `HPL`, `nccl-tests`, and a reference multi-node training job.
7. **Fault-injection and HA drills:** Kill a node or link during a checkpointed job, test `slurmctld` failover, and test the `HealthCheckProgram` auto-drain.
8. **Baseline archival and an automated regression suite:** Turn the acceptance scripts into nightly or post-maintenance canary checks.
</details>

## Sources and review notes

- Methodology, reasons to benchmark, `[Traeger 08]` (415 benchmarks in 106 papers), `[Smaalders 06]`, Bill Joy's 1981 VAX-11/750 to 11/780 4 MB TCP/IP analysis `[Joy 81]`, the 16 benchmarking failures (including the Benchmark Paradox `0.5^3 = 12.5%` `[Gregg 14c]` and 1993 TPC-A Standish Group vs Oracle `discrete transactions` Benchmark Specials `[Shanley 98]` / TPC `2%` pricing rule `[TPC 19a]`), micro-benchmarking (`Table 12.1` 5 file system tests, Solaris `128 Kbyte` slab cache, sunny/cloudy/rainy day testing), simulation (`Whetstone` 1972, `Dhrystone` 1984, `wrk`, `siege`, `hey`, Markov models), trace replay (`10 K rpm` vs `7,200 rpm` + `16x` cache), industry standards (Jim Gray 1985 `Sort, Scan, DebitCredit` / `TPS` `[Anon 85]`, `TPC-C..TPCx-V`, `SPEC`), active benchmarking (`bonnie++` 739 KB/s `Per Chr` analyzed with `iostat`, `bpftrace`, `cachestat`, `strace`, and `putc(3)`/`setbuffer(3)` `[Bourbonnais 08]`), CPU profiling (`zfs_zone_io_throttle()` `62.17%`), ramping load (`randread.pl` `$IOSIZE = 8192` `sysread()` on Sun ZFS Storage Appliance `[Gregg 09b]` and `990,000 IOPS` at `5 ms` vs `1,000,000 IOPS` at `50 ms`), sanity checks (`50,000 IOPS * 8 KB = 400,000 KB/s = 3.2 Gbps` over `1 Gbps` Ethernet `[Gregg 09c]`), statistical analysis, the 6-question Benchmarking Checklist `[Gregg 18d]`, and Section 12.4 Benchmark Questions: read in full from Brendan Gregg, *Systems Performance*, 2nd ed. (`systems-performance-2nd-edition`, `SP`), Chapter 12 ("Chapter 12. Benchmarking").
- MPI/HPC performance context: *Parallel and High Performance Computing* (`parallel-and-high-performance-computing`).
- `ai-systems-performance-engineering` — Chris Fregly, *AI Systems Performance Engineering*, "Chapter 5. GPU-Based Storage I/O Optimizations" (read in full): benchmarking GPUDirect Storage with `gdsio` (`-I 0 -w 4 -s 10G -i 1M -x 0` for GDS vs `-x 2` for CPU-staged; Table 5-1 example: `8.0 GB/s` at `1.25 ms` average latency and `85%` CPU util vs `9.6 GB/s` at `1.00 ms` average latency and `25%` CPU util, a `+20%` throughput gain; VAST Data GDS showing `+20%` on A100 and `+30%+` on H100), Nsight Systems GDS tracing (`nsys profile --trace=cuda,gds,nvtx,osrt` and `/etc/cufile.json`), and the batch-size halving/doubling test to distinguish communication-bound (`60 GB/s` on a `100 GB/s` NIC stays at `60 GB/s` when batch size is halved) from compute-bound (`60 GB/s` drops to `40 GB/s`).
- `nccl-tests` usage and bus-bandwidth formulas: `NVIDIA/nccl-tests` `README.md` and `doc/PERFORMANCE.md` (commit `afd59ab`). `IOR`/`mdtest`: `hpc/ior` README (commit `e4e4578`). `HPCG`: `hpcg-benchmark/hpcg` README (commit `114602d`).
- Run here: `code/part06/bench_stats.py` and `python3 code/part06/bench_stats_lab.py` (3 passed, 0 failed).
- Explicitly labelled inferences: The Send/Recv `busbw` factor of `1.0` in `nccl_busbw()` is a direct point-to-point identity; the `8 GiB`, `64`-rank, `0.60 s` calculation (`algbw = 14.3 GB/s`, `busbw = 28.2 GB/s`) is a worked application of `doc/PERFORMANCE.md`.
- Not verified on live hardware: multi-node HPL, HPCG, OSU, `nccl-tests`, `IOR`/`mdtest`, and `gdsio` runs on a live GPU cluster (not run).
- References listed in section 12.6 of the book and cited in this chapter: `[Joy 81]`, `[Anon 85]`, `[Jain 91]`, `[Gunther 97]`, `[Shanley 98]`, `[Coker 01]`, `[Smaalders 06]`, `[Gunther 07]`, `[Bourbonnais 08]`, `[DeWitt 08]`, `[Traeger 08]`, `[Gregg 09b]`, `[Gregg 09c]`, `[Gregg 14c]`, `[Gregg 14d]`, and `[Gregg 18d]`.
