---
id: "c06-03"
title: "6.3 Parallel computing concepts: Amdahl, scaling, shared memory versus message passing"
sidebar_label: "6.3 Parallel computing concepts: Amdahl, scaling, shared memory versus message passing"
sidebar_position: 3
description: "The ideas behind parallel programs: speedup and efficiency, Amdahl and Gustafson, strong and weak scaling, Karp-Flatt, shared memory versus message passing versus PGAS versus accelerators, communication cost models, load balance, and the software landscape (compilers, MPI implementations, UCX and NCCL, libraries, debuggers and profilers)"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.3 Parallel computing concepts: Amdahl, scaling, shared memory versus message passing

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Any multi-core machine with Python 3 |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. The script and its measured output below were actually run (Apple M3, 4 performance + 4 efficiency cores). Other labs untested |

## Why this matters for AI infrastructure

Whether a training job scales from 8 GPUs to 8,000 is a parallel-computing question. The same ideas appear under different names: Amdahl's law is why adding GPUs gives diminishing returns; strong versus weak scaling is the difference between making a fixed job faster and training a bigger model; message passing is what NCCL does; shared memory is what threads on one node or GPUs on NVLink do. Operators who understand these ideas can read a scaling plot, predict where a job will stop speeding up, explain why a network upgrade does or does not help, and set realistic expectations with researchers.

## Prerequisites and outcomes

Needs 6.1, 6.2, basic Python (Part 3). After this chapter you can:

- Compute speedup and efficiency, apply Amdahl's and Gustafson's laws, and infer a serial fraction from measurements (Karp-Flatt).
- Distinguish strong and weak scaling and say which a given benchmark measures.
- Compare shared-memory, message-passing, PGAS and accelerator programming models, and map each to technologies (OpenMP, MPI, OpenSHMEM, CUDA, NCCL).
- Use a simple latency-bandwidth cost model to reason about communication.
- Name the main support libraries, debuggers and profilers a cluster provides, and the build/environment tooling around them.
- Explain why real scaling stops: serial sections, communication, load imbalance, I/O, jitter.

## 1. Speedup, efficiency, scalability

Let `T(1)` be the run time on one processing element (core, node or GPU) and `T(n)` the time on `n`.

- **Speedup** `S(n) = T(1) / T(n)`. Ideal (linear) speedup is `n`.
- **Efficiency** `E(n) = S(n) / n`, between 0 and 1. Superlinear (`E > 1`) happens occasionally, usually because more aggregate cache holds the working set.
- **Throughput** for many independent tasks scales almost linearly (HTC); the interesting case is one tightly coupled job.

State always what `T(1)` means: the same parallel code on one core, or the best serial code? The honest baseline is the best known serial algorithm; the convenient one is the parallel code with one process, which flatters the result.

## 2. Amdahl's law (strong scaling)

If a fraction `p` of the work can be parallelised perfectly and `1 - p` is serial, the speedup on `n` processors for a **fixed problem size** is

```text
S(n) = 1 / ((1 - p) + p / n)       limit as n grows: 1 / (1 - p)
```

The serial fraction sets a hard ceiling: with `p = 0.99`, no number of processors gives more than 100x. The script below tabulates this and shows how unforgiving small serial parts are.

## 3. Gustafson's law (weak scaling)

Amdahl fixes the problem and adds processors. Gustafson observed that people usually *grow the problem* with the machine. If the parallel part grows with `n` while the serial part stays constant, the **scaled speedup** is

```text
S_scaled(n) = (1 - p) + p * n
```

which is nearly linear. Both laws are correct; they answer different questions.

| | Strong scaling | Weak scaling |
|---|---|---|
| Problem size | Fixed | Grows with processor count (constant work per processor) |
| Goal | Finish the same job faster | Solve a bigger job in the same time |
| Limiting factor | Serial fraction and communication/computation ratio rising as work per processor shrinks | Communication growth that is not proportional to work, memory per node, I/O |
| Typical in AI | Fine-tuning a fixed model on more GPUs; inference latency | Pre-training larger models and datasets on larger clusters; global batch size grows with GPUs |
| Metric | Speedup, efficiency | Time held constant; efficiency = `T(1)/T(n)` |

In strong scaling the work per processor shrinks while the communication per processor often does not, so the communication-to-computation ratio worsens as `n` increases. That is the usual reason a strong-scaling curve bends over.

## 4. Karp-Flatt: measuring the serial fraction

Given a measured speedup `S` on `n` processors, the **experimentally determined serial fraction** is

```text
e = (1/S - 1/n) / (1 - 1/n)
```

Interpretation: if `e` stays roughly constant as `n` grows, the loss is a fixed serial portion (Amdahl). If `e` *increases* with `n`, parallel overhead (communication, synchronisation, imbalance) is growing, which is the more common and more fixable situation.

## 5. A script you can run

```python
import math, os, time
from multiprocessing import Pool

def amdahl(p, n):  return 1.0 / ((1 - p) + p / n)
def gustafson(p, n): return (1 - p) + p * n
def karp_flatt(speedup, n): return (1.0 / speedup - 1.0 / n) / (1.0 - 1.0 / n)

def work(args):
    lo, hi = args
    s = 0.0
    for i in range(lo, hi):
        s += math.sqrt(i) * math.sin(i)
    return s

def run(n_workers, total):
    chunks = [(k * total // n_workers, (k + 1) * total // n_workers) for k in range(n_workers)]
    t = time.perf_counter()
    if n_workers == 1:
        work(chunks[0])
    else:
        with Pool(n_workers) as pool:
            pool.map(work, chunks)
    return time.perf_counter() - t
```

(The complete script, with the table printing and the loop over worker counts, is `code/part06/scaling.py` in the handbook repository.) Output of the Amdahl table:

```text
p     n=8   n=64  n=1024  limit
0.5     1.8   2.0     2.0      2
0.9     4.7   8.8     9.9     10
0.99    7.5  39.3    91.2    100
0.999   7.9  60.2   506.2   1000
```

Read it: with 99 percent parallel code, 1,024 processors give a 91x speedup (9 percent efficiency). With 99.9 percent, about 506x. Parallel efficiency at scale requires the serial and overhead parts to be tiny.

Measured strong scaling on a laptop, fixed problem of 40 million iterations, on an Apple M3 (8 logical cores: 4 performance and 4 efficiency):

```text
workers  time_s  speedup  efficiency  karp_flatt
      1    2.55     1.00        1.00  -
      2    1.38     1.85        0.92  0.083
      4    0.90     2.84        0.71  0.135
      8    0.76     3.37        0.42  0.196
```

What to notice: (1) efficiency falls as workers increase; (2) the Karp-Flatt value rises with `n`, which says overhead is growing, not a fixed serial part: process start-up and result collection (`Pool` creation, pickling), memory-bandwidth contention, and, on this chip, the efficiency cores being slower than the performance cores, so equal-sized chunks finish at different times (load imbalance). A first run with a smaller problem (6 million iterations) was dominated by start-up cost and showed almost no speedup with two workers, which is itself a lesson: **a problem too small for the machine measures overhead, not scaling**. Your numbers will differ.

## 6. Why scaling stops

| Cause | Description | Typical remedy |
|---|---|---|
| Serial section | Setup, I/O by one process, a single-threaded reduction | Parallelise it, overlap it with compute |
| Communication cost | Latency and bandwidth of the network; collectives grow with `n` | Better algorithm, overlap communication and computation, topology-aware placement, larger messages |
| Load imbalance | Some ranks have more work, or slower hardware | Dynamic balancing, domain re-decomposition, remove sick nodes |
| Synchronisation | Barriers, locks, waiting for the slowest rank | Reduce synchronisation, asynchronous methods |
| Memory bandwidth | Cores share the memory system; adding cores does not add bandwidth | NUMA-aware placement, fewer ranks per node, more nodes |
| I/O | Reading input or writing checkpoints through a shared file system | Parallel I/O, staged or asynchronous checkpoints (6.21) |
| OS and system jitter | Daemons, interrupts, page-cache writeback steal cycles at random moments; in a tightly coupled job the delay hits every rank at the next barrier | Reserve cores for the OS, quiet the nodes, pin processes |
| Fabric congestion | Other jobs' traffic, oversubscribed uplinks | Placement, QoS, adaptive routing (Part 12) |

At scale, **variability** matters as much as average speed: a job is only as fast as its slowest rank at each synchronisation point. That is the technical reason for node health checks (6.14), for removing nodes with thermally throttled GPUs, and for the obsession with identical software and firmware (6.2).

## 7. Programming models

### Shared memory (threads)

Multiple threads in one process share an address space. Easy to share data, hard to get right (races, false sharing). Limited to one node (or one coherent domain).

- **OpenMP**: compiler directives (`#pragma omp parallel for`) that create and manage threads; the dominant HPC choice for node-level parallelism (6.5).
- **POSIX threads, C++ std::thread, TBB** (Intel/oneAPI Threading Building Blocks): lower-level or task-based libraries.
- **Python**: the GIL limits thread parallelism for CPU-bound Python; use processes, native extensions, or vectorised libraries (Part 3).

### Message passing (distributed memory)

Separate processes with separate memories exchange explicit messages. Scales across many nodes. **MPI** (Message Passing Interface) is the standard: point-to-point (`MPI_Send/Recv`), collectives (`MPI_Allreduce`, `MPI_Bcast`), one-sided operations, and parallel I/O (6.4). Implementations: Open MPI, MPICH and derivatives (MVAPICH2, Intel MPI, Cray MPICH), vendor builds (NVIDIA HPC-X includes Open MPI tuned for InfiniBand). Programs are portable across implementations at source level; performance and launch details differ.

### Hybrid

One MPI rank per node (or per socket, or per GPU) with threads inside, to cut the number of messages and the memory footprint. Standard on large clusters. The scheduler must be told how to place ranks and threads (`--ntasks-per-node`, `--cpus-per-task`; 6.11, 6.12).

### PGAS and one-sided

**Partitioned Global Address Space** models (OpenSHMEM, UPC, Chapel, Coarray Fortran) give each process a local partition of a logically global memory and offer one-sided put/get. OpenSHMEM is the standardised library form (the SCL book covers SHMEM, standardised from 2009 onward after earlier Cray, SGI, and Quadrics implementations; C and Fortran programs compile with `oshc` and `oshfort`, launch via `oshrun` or `mpirun`, size the symmetric heap with `SHMEM_SYMMETRIC_HEAP_SIZE`, and inspect collective algorithm options with `oshconfig` `(untested here)`). NVSHMEM is NVIDIA's GPU-resident variant used in some AI kernels (Part 10, 12). Niche in application codes, growing in GPU libraries.

### Accelerators

Offload computation to GPUs: **CUDA** (NVIDIA), **OpenACC** and OpenMP target directives (directive-based), OpenCL and SYCL/HIP (portable or other vendors). Combined with MPI (one rank per GPU, CUDA-aware MPI or GPUDirect RDMA moving device memory directly over the fabric) or with **NCCL** for GPU collectives. NCCL (NVIDIA Collective Communications Library) implements all-reduce, all-gather, reduce-scatter, broadcast and all-to-all optimised for NVLink and InfiniBand/RoCE topologies; it is the communication layer under PyTorch distributed training (Part 10, 12, 14). **UCX** is a communication framework used by Open MPI and others to drive InfiniBand, shared memory and GPU transports.

### Data parallelism in AI, in these terms

Data-parallel training is SPMD (single program, multiple data) with an all-reduce of gradients each step: the same pattern as an MPI domain-decomposition code with a global reduction. Tensor, pipeline and expert parallelism are decompositions of the model with different communication patterns (point-to-point and all-to-all). The scaling laws above apply directly.

## 8. A communication cost model

The simplest useful model for a message of `m` bytes between two processes: 

```text
T(m) = alpha + m / beta
```

where `alpha` is the latency (microseconds on InfiniBand, tens of microseconds on typical TCP Ethernet, far lower inside a node) and `beta` the bandwidth. Small messages are latency-dominated, large messages bandwidth-dominated; the crossover is `m = alpha * beta`. Consequences:

- Aggregate many small messages into fewer large ones.
- Overlap communication with computation (non-blocking operations, CUDA streams).
- Collectives use algorithms (ring, tree, recursive halving/doubling) chosen by message size and topology; a ring all-reduce moves about `2(n-1)/n` times the data per participant, nearly independent of `n` for bandwidth, while its latency term grows with `n`. NCCL chooses among ring and tree algorithms automatically (Part 12).
- Distinguish intra-node (NVLink, shared memory) from inter-node bandwidth, which is typically much lower; parallelism strategies place the most communication-hungry dimension inside the node (Part 14).

## 9. Load balance and domain decomposition

Most simulation codes split a grid or mesh into subdomains, one per rank, exchanging **halo (ghost) cells** with neighbours each step. Computation scales with the subdomain volume, communication with its surface: shrinking subdomains (strong scaling) raise the surface-to-volume ratio and hence the communication share. Static decomposition assumes equal work per cell; if work varies (adaptive meshes, particles clustering) use dynamic load balancing or work stealing. Graph partitioners (METIS and similar) divide irregular meshes. For AI, the analogue is balanced micro-batches and pipeline stages; an unbalanced pipeline leaves "bubbles".

## 10. The software landscape around parallel programs

From the SCL book's chapters on compilers, environments and libraries (summarised here, detailed in 6.4 to 6.6):

- **Compilers**: GNU (`gcc`, `gfortran`), Intel oneAPI and NVIDIA HPC SDK compilers, LLVM; optimisation flags and vectorisation matter (6.5).
- **MPI and launch**: Open MPI, MPICH family, MVAPICH, Intel MPI; **PMIx** is the process-management interface that lets schedulers such as Slurm launch MPI jobs directly (`srun --mpi=pmix`; 6.12).
- **Communication substrates**: UCX, libfabric, NCCL, NVSHMEM.
- **Environment management**: Environment Modules and Lmod, Spack and EasyBuild for building software stacks (6.6); containers via Apptainer or enroot (6.13, 6.29).
- **Build systems**: Make, CMake, Autotools, Meson; reproducible builds need pinned compilers and libraries.
- **Numerical libraries**: BLAS/LAPACK (OpenBLAS, MKL, ACML, cuBLAS), **ScaLAPACK** (distributed dense linear algebra), **PETSc** (parallel sparse solvers and PDEs), **FFTW** and cuFFT (Fourier transforms), **Intel TBB** (task-based C++ threading), HDF5/NetCDF (I/O), cuDNN and CUTLASS for deep learning (Part 10).
- **Debuggers**: `gdb`, `valgrind`, Arm **DDT**, **TotalView**, `cuda-gdb`, `compute-sanitizer` for CUDA.
- **Profilers and tracers**: `perf`, `gprof`, **MPE** and **JumpShot**, **Intel Trace Collector and Analyzer (ITAC)**, **Intel VTune** / Advisor / Inspector, **Vampir** / VampirTrace, **TAU** (Tuning and Analysis Utilities), Arm MAP, Score-P/Scalasca, `cuda-nsight` / NVIDIA Nsight Systems and Nsight Compute (Part 10).

As an operator you rarely write these codes, but you install, tune, and support them, and most user tickets (a job that is slow, hangs, crashes at scale, or fails to link) involve this layer. Chapter 22 of the SCL book walks through the core numerical libraries and debugging tools you will meet in user build logs and job errors:

### ScaLAPACK (`BLAS`, `PBLAS`, `BLACS`, `SLmake.inc`, and `PTXXYYYY` naming)

**ScaLAPACK** (Scalable LAPACK) ports dense linear algebra (`LAPACK` and `LINPACK`) to distributed-memory clusters using two architectural layers:

1. **PBLAS** (Parallel Basic Linear Algebra Subprograms, including `PTOOLS`): distributed-memory versions of Level 2 and Level 3 `BLAS` vector/matrix operations, built on top of fast single-node `BLAS` and `LAPACK` libraries (such as Intel MKL, AMD ACML, GotoBLAS, or OpenBLAS).
2. **BLACS** (Basic Linear Algebra Communication Subprograms): the communication portability layer over MPI (`-lblacs`, `-lblacsC`, `-lblacsF`).

When building ScaLAPACK from source (`http://www.netlib.org/scalapack/`), you edit `SLmake.inc` before running `make`. In the book's example `(untested here)`:

```makefile
# SLmake.inc excerpt (untested here)
SHELL = /bin/sh
home = /share/download/SCALAPACK
PLAT = LINUX
BLACSDBGLVL = 0
BLACSdir = /usr/local/lib
USEMPI = -DUsingMpiBlacs
SMPLIB =
BLACSFINIT = -lblacsF
BLACSCINIT = -lblacsC
BLACSLIB = -lblacs
F77 = mpif77
CC = mpicc
BLASLIB = -lgoto -lpthread
LAPACKLIB = -llapack
```

ScaLAPACK provides `530` subroutines across three categories—**driver** subroutines (14 per data type, solving complete linear systems or eigenvalue problems), **computational** subroutines (such as LU factorisation or tridiagonal reduction), and **service** subroutines. Routine names follow the LAPACK scheme prefixed with `P` in the pattern `PTXXYYYY` (or `PTXXYYY`):

| Field | Code | Meaning |
|---|---|---|
| **`P`** (prefix) | `P` | Parallel (ScaLAPACK) routine |
| **`T`** (data type) | `S`, `D`, `C`, `Z` | Single-precision real (`S`), double-precision real (`D`), single-precision complex (`C`), double-precision complex (`Z`) |
| **`XX`** (matrix type) | `DB`, `DT`, `GB`, `GE`, `GT`, `HE`, `PB`, `PO`, `PT`, `ST`, `SY`, `TR`, `TZ`, `UN` | Diagonally dominant band (`DB`), diagonally dominant tridiagonal (`DT`), general band (`GB`), general (`GE`), general tridiagonal (`GT`), Hermitian (`HE`), symmetric/Hermitian positive-definite band (`PB`), symmetric/Hermitian positive-definite (`PO`), symmetric/Hermitian positive-definite tridiagonal (`PT`), symmetric tridiagonal (`ST`), symmetric (`SY`), triangular (`TR`), trapezoidal (`TZ`), unitary (`UN`) |
| **`YYYY`** (operation) | `TRF`, `TRS`, `CON`, `SV`, `SVX`, `EV` / `EVX`, `GVX`, `SVD`, `RFS`, `LS` | Matrix factorisation (`TRF`), solve linear system using factorisation (`TRS`), estimate condition number (`CON`), solve linear system (`SV`), solve with expert diagnostics (`SVX`), eigenvalues/eigenvectors (`EV`, `EVX`), generalised eigenvalue problem (`GVX`), singular value decomposition (`SVD`), iterative solution refinement (`RFS`), least squares (`LS`) |

### PETSc (`PETSC_ARCH`, `PETSC_DIR`, and runtime diagnostic flags)

**PETSc** (Portable, Extensible Toolkit for Scientific Computation) provides parallel linear/nonlinear solvers and time integrators for partial differential equations (PDEs) in C, C++, Fortran, and Python using MPI, hybrid MPI+threads (`--with-pthreadclasses`), and GPUs (CUDA). A single source tree can hold multiple compiler/library builds side by side using two environment variables: `PETSC_DIR` (the installation root) and `PETSC_ARCH` (the build profile name). Compilers (`--with-cc=mpicc`, `--with-fc=mpifort`, `--with-cxx=mpicxx`), optimisation flags (`COPTFLAGS`, `FOPTFLAGS`, `CXXOPTFLAGS`), and external solver packages (`--with-PACKAGE-include` or `--download-PACKAGE` for `Hypre`, `MUMPS`, `Parmetis`, etc.) are passed to `./configure`. In the book's Intel MPI + MKL build example `(untested here)`:

```bash
# (untested here)
./configure PETSC_ARCH=linux-intel -with-cc=mpicc \
  --with-fc=mpifort --with-blas-lapack-dir=/opt/intel/mkl
make PETSC_ARCH=linux-intel all test
sudo make install
```

When a user's PETSc application crashes or runs slowly, you can pass built-in PETSc runtime flags on the job command line without recompiling `(untested here)`:

- `-log_summary` — print a breakdown of subroutine execution times, FLOP rates, and MPI message counts at program exit.
- `-fp_trap` — trap and halt immediately on floating-point exceptions (divide-by-zero, NaN, overflow).
- `-malloc_debug` / `-trdump` / `-trmalloc` — enable PETSc memory tracing and dump unfreed memory blocks at exit.
- `-start_in_debugger [noxterm, gdb, dbx, xxgdb]` — launch the processes directly inside a debugger.
- `-on_error_attach_debugger [noxterm, gdb, dbx, xxgdb]` — attach a debugger automatically only when a runtime error occurs.

### FFTW and Intel TBB

- **FFTW** (Fastest Fourier Transform in the West) computes 1D and multivariate discrete Fourier transforms for both complex and real arrays of arbitrary size `N` (not restricted to powers of two). Keep two operational facts in mind: (1) **FFTW version 2 and version 3 have incompatible APIs**, so clusters often need both installed (`-lfftw` / `-lfftw_mpi` for v2; `-lfftw3` / `-lfftw3_mpi` for v3 `(untested here)`); and (2) Intel MKL and AMD ACML include built-in optimized FFTW interfaces, avoiding a separate build when those math libraries are used.
- **Intel TBB** (Threading Building Blocks) is a C++ template library that expresses node-level parallelism as a directed graph of **tasks** rather than raw threads, mapping tasks dynamically onto POSIX, Windows, or Boost threads for cache and core efficiency. Because TBB hides thread creation and synchronisation internally, the book cautions that mixing TBB task graphs with asynchronous MPI calls requires care to avoid subtle thread-safety bugs.

### Parallel debuggers, profilers, and trace formats

Standard `gdb` inspects only a single process at a time, and running hundreds of independent `gdb` instances across an MPI job produces unreadable output. Cluster debuggers and tracers solve this in two ways:

- **Parallel debuggers**:
  - **TotalView** (RogueWave / Perforce): supports MPI, OpenMP, OpenACC, and CUDA, attaches to running jobs or launches via the batch scheduler (with a remote GUI client), stops and inspects stacks and variables across all ranks simultaneously, includes memory debugging and **ThreadSpotter** (for cache/memory bandwidth and thread-contention analysis), and supports **reverse debugging** (recording execution state and stepping backward in time to the root cause of a crash).
  - **Arm DDT** (Distributed Debugging Tool, originally Allinea): similar multi-rank GUI debugging for MPI/OpenMP/GPU codes, plus an **offline debugging mode** (`ddt --offline ...` `(untested here)`) that runs under the batch scheduler without an interactive GUI session and writes a post-mortem HTML/text report of variable values, call stacks, and suspected memory leaks when the job finishes or crashes.
  - **GPU debuggers**: `cuda-gdb` (drop-in replacement for `gdb` in CLI or GUIs such as DDD and VS Code) and `cuda-nsight` from the CUDA Toolkit.
- **Profilers, tracers, and PMPI**:
  - Most MPI tracers intercept MPI calls without source changes using the standard **PMPI** (Profiling MPI) wrapper interface, writing timestamped communication and subroutine events into open trace formats such as **CLOG**, **SLOG** / **SLOG2**, **OTF**, and **OTF2** (or Intel's **STF**).
  - **MPE and JumpShot**: Argonne's free **MPE** library records MPI traces into `CLOG` / `SLOG2` files, which **JumpShot** visualises as a timeline of rank states and message arrows.
  - **Vampir and VampirTrace**: commercial timeline visualiser (**Vampir**) and open-source instrumentation library (**VampirTrace**) using the open **OTF** / **OTF2** trace format to pinpoint communication bottlenecks across thousands of ranks.
  - **Intel Trace Collector and Analyzer (ITAC)** and **Intel VTune** / Advisor / Inspector (in the Intel oneAPI HPC Toolkit): collect full or sampled **STF** traces (automatically via a startup flag when using Intel MPI) and hardware counter profiles.
  - **TAU** (Tuning and Analysis Utilities, University of Oregon): open-source profiling and tracing suite with its own visualisers and JumpShot integration.

## 11. Examples worth keeping in mind

1. **Embarrassingly parallel**: independent tasks, linear scaling (parameter sweeps, per-sample inference).
2. **Stencil / halo exchange**: neighbour communication, good strong scaling until subdomains are small.
3. **Global reduction / all-reduce each step**: gradient synchronisation; bandwidth-bound for large tensors, latency-bound for small.
4. **All-to-all**: transposes (FFT), mixture-of-experts routing; stresses bisection bandwidth.
5. **Master-worker with irregular tasks**: dynamic balancing, scalability limited by the master.

## 12. Lab (script part tested)

1. Run the scaling script on your machine (save the complete version; modify `total` so the one-worker run takes 2 to 5 seconds). Record the table. Does Karp-Flatt rise with workers? What is your core mix?
2. Change the work function to be memory-bound (sum a large NumPy array in chunks) and compare scaling with the compute-bound version. Explain the difference using memory bandwidth.
3. Plot (matplotlib) measured speedup against ideal and against Amdahl curves for `p` in 0.9, 0.99.
4. Take a published scaling result (from a paper or a vendor blog for an AI training run) and compute efficiency and the Karp-Flatt value from two data points. What does it say about the dominant overhead?
5. Write one paragraph explaining to a researcher why doubling their GPU allocation did not halve the training time.

## 13. Interview angles

- State Amdahl's law. What does it say about 1,000 processors with 1 percent serial code?
- Strong versus weak scaling: which does an LLM pre-training run demonstrate?
- What does Karp-Flatt tell you that speedup alone does not?
- Shared memory versus message passing: when is each appropriate? What is hybrid parallelism?
- Why does a single slow GPU slow a whole training job?
- What is NCCL and how does it relate to MPI?
- Latency versus bandwidth: how do message sizes affect which one matters?
- What is OS jitter, and how do you reduce it on a cluster?

## 14. Checkpoint questions (30)

1. Define speedup and efficiency.
2. What baseline should `T(1)` be?
3. State Amdahl's law. What is the limit?
4. State Gustafson's law and what question it answers.
5. Define strong and weak scaling.
6. Which scaling type shows the communication-to-computation ratio worsening?
7. State the Karp-Flatt metric and its interpretation when it rises with `n`.
8. In the Amdahl table, what is the speedup for p = 0.99 on 1,024 processors?
9. Why did the small-problem run in the lab show almost no speedup?
10. Give four reasons scaling stops.
11. What is load imbalance, and why is it worse with heterogeneous cores?
12. What is OS jitter?
13. Name the shared-memory programming options.
14. What does MPI provide that threads do not?
15. What is a collective operation? Give three examples.
16. What is hybrid MPI+OpenMP and why use it?
17. What is PGAS? Name two implementations or models.
18. What is NCCL and what operations does it implement?
19. What is UCX?
20. What is PMIx used for?
21. Write the latency-bandwidth cost model and the crossover message size.
22. Why aggregate small messages?
23. How does a ring all-reduce's per-participant data volume depend on `n`?
24. What is a halo exchange? How does surface-to-volume affect scaling?
25. In ScaLAPACK (`PTXXYYYY` naming), what do `PBLAS` and `BLACS` do, and which PETSc runtime flags print a performance summary, trap floating-point exceptions, and attach a debugger on error? (Answer: `PBLAS` provides distributed Level 2/3 BLAS operations and `BLACS` provides the MPI communication layer; in PETSc, `-log_summary`, `-fp_trap`, and `-on_error_attach_debugger`.)
26. Name two debuggers and two profilers.
27. Why do operators care about parallel programming models?
28. How is data-parallel training an SPMD program?
29. Why is NVLink bandwidth relevant to choosing parallelism dimensions?
30. Explain to a researcher why doubling GPUs does not halve time.

## 15. Sources and review notes

- Book source (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`):
  - Chapter `21. Compilers and Environments, for Parallel Technologies` (read in full): MPI, OpenMP, CUDA, OpenCL, OpenACC, and OpenSHMEM (`oshc`, `oshfort`, `oshrun`, `SHMEM_SYMMETRIC_HEAP_SIZE`, `oshconfig`), `PMIx`, `UCX`, `NCCL`, Environment Modules / `LMOD`, and `EasyBuild` / `Spack`.
  - Chapter `22. Parallel Computing Support Libraries` (read in full): `ScaLAPACK` (`BLAS`, `PBLAS`, `PTOOLS`, `BLACS`, `SLmake.inc`, `530` subroutines, and the `PTXXYYYY` routine naming table), `PETSc` (`PETSC_ARCH`/`PETSC_DIR` configure workflow and runtime diagnostic flags `-log_summary`, `-fp_trap`, `-trdump`/`-trmalloc`/`-malloc_debug`, `-start_in_debugger`, `-on_error_attach_debugger`), `FFTW` (versions 2 `-lfftw_mpi` and 3 `-lfftw3_mpi`), `Intel TBB`, and parallel debuggers/profilers (`TotalView` reverse debugging and `ThreadSpotter`, Arm `DDT` offline mode, `PMPI`, `MPE`/`JumpShot` `CLOG`/`SLOG2`, `Vampir`/`VampirTrace` `OTF`/`OTF2`, `ITAC`/`VTune`/`Advisor`/`Inspector` `STF`, `TAU`, and `cuda-gdb`/`cuda-nsight`).
- Amdahl (1967), Gustafson (1988) and Karp-Flatt (1990) are standard results; the formulas here are the textbook forms. The cost model is the classic latency-bandwidth (Hockney) model.
- General background on parallel programming concepts also draws on the PHPC and public-reference material listed in the handbook's source map.
- Original: the measured script output (run once on an Apple M3) and the interpretation; numbers will vary by machine.
- Unverified: ring all-reduce volume factor stated as `2(n-1)/n` (standard result, not re-derived here); NCCL algorithm selection details (see Part 12); ScaLAPACK `SLmake.inc`, PETSc configure/runtime flags, FFTW/TBB/OpenSHMEM commands, and debugger/profiler invocations (from the book, not run here).
