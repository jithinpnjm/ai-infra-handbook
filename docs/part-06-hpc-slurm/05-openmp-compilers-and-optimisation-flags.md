---
id: "c06-05"
title: "6.5 OpenMP, compilers and optimisation flags"
sidebar_label: "6.5 OpenMP, compilers and optimisation flags"
sidebar_position: 5
description: "Node-level parallelism and compilation for HPC: the OpenMP model, directives, data scoping, schedules, affinity and first-touch, common bugs, compiler families, optimisation and floating-point flags, vectorisation reports, portability across heterogeneous nodes, and accelerator directives, with measured examples"
status: "drafted"
tier: "3"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.5 OpenMP, compilers and optimisation flags

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop or cluster login/compute node with a C compiler supporting OpenMP |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. All C and Fortran programs and flag comparisons shown were compiled and run (clang 23.1.4 and gfortran 16.2.0 from conda-forge on an Apple M3, 4 performance + 4 efficiency cores). x86/Arm server numbers will differ |

## Why this matters for AI infrastructure

Operators are often asked "why is my CPU code slow on the cluster", "why does the same binary crash on some nodes", or "why do results change when I use `-O3`". The answers sit in the compiler and threading layer: whether the code was vectorised, whether threads are bound where the memory is, whether an aggressive flag changed the arithmetic, whether the binary uses instructions a node does not have. The same ideas appear in AI infrastructure: data-loader and preprocessing threads, CPU-side tokenisation, host-side optimiser steps, PyTorch/NumPy/BLAS thread settings (`OMP_NUM_THREADS`), and building extensions or containers for heterogeneous fleets. Learning them on OpenMP, where the mechanisms are visible, transfers directly.

## Prerequisites and outcomes

Needs 6.3 and 6.4 and basic C or Fortran reading skill. After this chapter you can:

- Parallelise loops with OpenMP and reason about data scoping, reductions and scheduling.
- Control threads, placement and binding with `OMP_*` variables and Slurm options, and avoid oversubscription in hybrid MPI+OpenMP jobs.
- Recognise and reproduce data races and false sharing; explain why a race may pass tests.
- Choose a compiler and flags deliberately: optimisation level, target architecture, floating-point semantics, link-time optimisation, profile-guided optimisation, debug info.
- Read vectorisation reports and explain why strict floating-point rules block vectorisation of reductions.
- Build portable binaries for a mixed fleet and detect illegal-instruction failures.

## 1. OpenMP in one page

OpenMP is a directive-based API (C, C++, Fortran) for **shared-memory** parallelism using threads. The program starts with one thread; at a `parallel` region it forks a *team* of threads; at the end they join (fork-join). Directives look like comments to a compiler without OpenMP, so a serial build still works.

```c
#pragma omp parallel for schedule(static)
for (long i = 0; i < n; i++) a[i] = b[i] + 3.0 * c[i];
```

Build with `-fopenmp` (GCC, clang), `-qopenmp` (Intel classic), `-fiopenmp` (oneAPI), `-mp` (NVIDIA HPC compilers), and link the runtime (`libgomp` for GCC, `libomp` for LLVM). The compiler transforms the region into an outlined function executed by each thread.

### Key concepts

| Concept | Meaning |
|---|---|
| **Team, thread number** | `omp_get_num_threads()`, `omp_get_thread_num()` |
| **Data-sharing clauses** | `shared` (one copy), `private` (uninitialised copy per thread), `firstprivate` (copy initialised from original), `lastprivate`, `reduction(op: var)` (private partials combined at the end) |
| **Work sharing** | `for`/`do` (split loop iterations), `sections`, `single`, `workshare` (Fortran) |
| **Schedule** | `static` (equal chunks, lowest overhead), `dynamic,chunk` (threads grab chunks; balances irregular work, adds overhead), `guided`, `auto`, `runtime` (read `OMP_SCHEDULE`) |
| **Synchronisation** | `barrier`, `critical`, `atomic`, `ordered`, locks, `nowait` to drop the implicit barrier at the end of a work-sharing construct |
| **Tasks** | `task`, `taskwait`, `taskloop`, dependencies (`depend`) for irregular parallelism |
| **SIMD** | `#pragma omp simd` asks for vectorisation of a loop |
| **Offload** | `#pragma omp target teams distribute parallel for` runs on a GPU (section 8) |

Environment variables (runtime control without recompiling):

| Variable | Use |
|---|---|
| `OMP_NUM_THREADS` | Team size (list form for nested levels) |
| `OMP_PROC_BIND` | `false`, `true`, `close`, `spread`, `master/primary` |
| `OMP_PLACES` | `threads`, `cores`, `sockets`, `numa_domains`, or an explicit list |
| `OMP_SCHEDULE` | Used by `schedule(runtime)` |
| `OMP_DISPLAY_ENV=verbose` | Print the settings actually in effect (useful when debugging) |
| `OMP_STACKSIZE` | Per-thread stack (deep recursion or large private arrays) |

## 2. A scaling experiment

The program `code/part06/omp_scaling.c` times a memory-bound triad (`a = b + 3c`), a compute-heavy loop (sine and cosine) and a sum reduction at several thread counts. It uses first-touch initialisation and an untimed warm-up pass. Build and run:

```bash
clang -O2 -fopenmp omp_scaling.c -o omp_scaling -lm      # or: gcc -O2 -fopenmp ...
./omp_scaling
```

Output on the Apple M3 (8 cores):

```text
threads  triad_ms  GB/s   sin_ms   sum_ms
      1      18.1   66.3     86.3     37.7  (checksum 4.498e+08)
      2      15.3   78.4     13.3     18.9
      4      14.2   84.4     11.3     12.9
      6      14.1   85.0      7.8      8.9
      8      14.1   85.4      7.3      9.4
```

(The checksum was identical in every row, as expected.) Interpretation:

- **Memory-bound triad**: one thread already reaches 66 GB/s and the curve is flat above two threads at about 85 GB/s: the memory system, not the cores, is the limit. Adding threads cannot help. This is why memory-bound HPC codes use fewer ranks/threads per node than cores, and why bandwidth (HBM) matters more than FLOPs for many AI inference steps (Part 10, 15).
- **Compute-heavy sine loop**: scales much better (13 ms to 7 ms), but not 8x: the first row (86 ms) is an outlier from running on an efficiency core or a slow ramp (a repeat earlier gave 26 ms for the same single-thread case). Heterogeneous cores and frequency scaling make single-thread timings noisy; on servers pin and repeat.
- **Reduction**: scales moderately; the final combination and memory traffic dominate.
- An earlier run without a warm-up pass reported 20 GB/s for one thread, entirely an artefact of page-fault and start-up costs charged to the first measurement. **Always warm up, repeat, and report the spread.**

## 3. Affinity, NUMA and first touch

A dual-socket server is two NUMA domains, each with local memory and PCIe devices. Linux places a page on the node of the thread that first writes it (**first touch**). If one thread initialises an entire array, all its pages land near that thread's socket, and threads on the other socket then read across the inter-socket link. The remedies:

1. **Initialise in parallel with the same schedule as the compute loop** (as in the scaling program), so each thread touches the data it will use.
2. **Bind threads**: `OMP_PROC_BIND=close` or `spread` with `OMP_PLACES=cores` (or `numa_domains`) so threads do not migrate away from their data. Verify with `OMP_DISPLAY_AFFINITY=true` or `numactl --hardware` plus `ps -L`/`taskset -pc`.
3. For a hybrid job, give each MPI rank its own NUMA domain and set threads per rank to the domain's core count (6.4 section 8).
4. Watch **hyperthreads**: two threads on the sibling hardware threads of a core share its units and cache; for floating-point-heavy work, binding to physical cores usually beats using all logical CPUs.

On Slurm: `--cpus-per-task=N` plus `export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK` and `--cpu-bind=cores`. The classic failure is **oversubscription**: 8 MPI ranks per node each starting a default team of `ncores` threads gives 8 x ncores threads fighting for ncores cores, often a 5 to 50x slowdown. Always set `OMP_NUM_THREADS` explicitly in job scripts, including for Python jobs using NumPy, PyTorch (`torch.set_num_threads`), MKL and OpenBLAS (`MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`).

## 4. Bugs OpenMP makes easy

**Data race**: two threads access the same location, at least one writes, without synchronisation. Results are undefined. The program `code/part06/omp_race.c` increments a shared counter 20 million times in parallel three ways. Measured with 8 threads at `-O0`:

```text
expected 20000000 | racy 6215980  | atomic 20000000 | reduction 20000000
expected 20000000 | racy 3487814  | atomic 20000000 | reduction 20000000
```

Two runs, two different wrong answers, with roughly 70 to 80 percent of the updates lost. At `-O2` the same source (with the counter declared `volatile`) printed the correct total in two of three runs and 17,500,000 in the third. **A race can pass repeated testing and fail later**, on another node count, optimisation level or under load; "it worked when I ran it" proves nothing. Fixes: `reduction` (fast), `atomic` (correct, serialises the updates; the atomic loop is far slower), per-thread partials, or restructure.

**False sharing**: independent per-thread variables that sit in the same cache line make the line bounce between cores, slowing everything though no data is logically shared. Pad per-thread data to the cache-line size (64 bytes on most x86 and Arm servers, 128 bytes on Apple M-series; `getconf LEVEL1_DCACHE_LINESIZE` or `sysctl hw.cachelinesize`). The second half of `omp_race.c` tries to expose this with packed versus padded per-thread counters. **On the M3 I could not reproduce a slowdown** (about 0.09 s either way), possibly because the volatile update loop is limited by something else; the effect is well documented on x86 servers and you should measure it on your hardware rather than assume it either way.

Other classics: `private` variables used before initialisation, missing `reduction`, a `critical` section that makes the loop serial, `schedule(dynamic,1)` on a trivial loop (overhead dominates), nested parallel regions creating more threads than cores, thread-unsafe library calls, and calling MPI from threads without the right thread level (6.4 section 5). Tools: ThreadSanitizer (`-fsanitize=thread`), Intel Inspector, Archer, Valgrind's Helgrind, compiler warnings.

## 5. Compilers

| Family | Compilers | Notes |
|---|---|---|
| **GNU** | `gcc`, `g++`, `gfortran` | Ubiquitous; the default on most Linux distributions; GOMP runtime; `-fopt-info-vec` for vectorisation reports |
| **LLVM** | `clang`, `clang++`, `flang` | Basis of many vendor compilers; `-Rpass=loop-vectorize` reports; libomp runtime |
| **Intel oneAPI** | `icx`, `icpx`, `ifx` (LLVM-based), classic `icc`/`ifort` (retired) | Strong on Intel CPUs; oneMKL, MPI, VTune |
| **NVIDIA HPC SDK** | `nvc`, `nvc++`, `nvfortran`, plus `nvcc` for CUDA | OpenACC, OpenMP offload, CUDA Fortran; bundles MPI, math libraries, profilers |
| **AMD** | AOCC (LLVM-based), ROCm compilers | AMD CPUs and GPUs |
| **Arm / Cray / HPE** | Arm Compiler for Linux, Cray compiler environment | Vendor-tuned for their systems |

Operational points: use the compiler that matches the MPI and library stack (a Fortran module built by one compiler cannot be read by another; C++ ABI differences between libstdc++ and libc++; interprocedural optimisation such as IPO breaks object-file compatibility across compilers); keep several versions available through modules (6.6); record `compiler --version` in the build metadata; mixing OpenMP runtimes (GOMP and libomp) in one process causes subtle failures, so make sure all libraries in a process share the runtime or are loaded carefully.

### Commercial compiler licences and FlexLM operational pitfalls

While GCC, LLVM, Intel oneAPI, and NVIDIA HPC SDK compilers are now freely downloadable (with optional paid support), legacy commercial compilers (such as PathScale or PGI) and many commercial engineering and EDA packages rely on floating licence servers (such as FlexLM). Chapter 21 of the SCL book highlights three licensing models and their operational traps:

1. **Single-user, single-computer** or **fixed-computer, unlimited-users**: a fixed-host licence on the login/build node is the simplest for a cluster (and Intel compilers can read a local licence file directly from a directory without a licence daemon), but is not always sold by vendors.
2. **Concurrent-use (floating) licences and the `15-minute` checkout hold**: floating licences cap how many users can invoke the compiler simultaneously (for example `3` concurrent seats). In the PathScale implementation described in the book, "simultaneity" is metered in `15-minute` blocks: a single compiler call leases a seat for that user for `15 minutes` (whether they compile once, compile 20 files, or their build job crashes immediately), blocking other users from checking out that seat until the 15-minute lease expires.
3. **High-availability quorum and MAC address binding**: fault-tolerant licence server clusters typically run as a 3-server triad that requires at least `50%` of the licence servers to be online to maintain quorum. Licences are bound to the network interface **MAC address** (and sometimes hostname) of the licence server at activation time; if you run a licence server inside a virtual machine, you must pin the VM's virtual NIC MAC address so a reboot or host migration does not invalidate the licence.

## 6. Optimisation and floating-point flags

### Optimisation levels

| Flag | Effect (GCC/clang, approximately) |
|---|---|
| `-O0` | No optimisation; best for debugging; slow |
| `-O1` | Basic optimisations |
| `-O2` | Standard production level; inlining, scheduling, many loop optimisations |
| `-O3` | More aggressive: vectorisation, unrolling, interchange |
| `-Ofast` | `-O3` plus `-ffast-math` and other non-standard-compliant shortcuts |
| `-Os`, `-Oz` | Size-oriented |
| `-g` | Debug info (does not slow the code; keep it in production builds for profiling) |
| `-fno-omit-frame-pointer` | Helps profilers produce stacks |
| `-flto` | Link-time optimisation across files |
| `-fprofile-generate` / `-fprofile-use` | Profile-guided optimisation |

### Target architecture

`-march=native` (x86, GCC/clang) or `-mcpu=native` (Arm and Apple) tunes and enables every instruction set of the **build machine**. This is fast and dangerous: a binary built on a node with AVX-512 crashes with `Illegal instruction` on a node without it. For a heterogeneous fleet, build for the **lowest common architecture** (`-march=x86-64-v3` for AVX2, or a named micro-architecture such as `-march=znver3`), use **function multi-versioning / runtime dispatch** (`-ftree-vectorize` with `target_clones`, or libraries like MKL and OpenBLAS that dispatch at run time), or build per-architecture variants selected by modules (the Spack/EasyBuild approach, 6.6). Check a node's features with `lscpu` or `/proc/cpuinfo` flags.

### Floating-point semantics

The central experiment of this chapter, `code/part06/flags_kernel.c`, sums a 20-million-element float array 20 times (a reduction), compiled with different flags:

```text
-O0                                dot=2293365.000000  2.02 GFLOP/s
-O1                                dot=2293365.000000  2.01 GFLOP/s
-O2                                dot=2293365.000000  2.69 GFLOP/s
-O3                                dot=2293365.000000  2.71 GFLOP/s
-O3 -mcpu=native                   dot=2293365.000000  2.68 GFLOP/s
-O3 -ffast-math                    dot=2445485.500000  16.05 GFLOP/s
-O3 -ffast-math -mcpu=native       dot=2445485.500000  16.29 GFLOP/s
```

A double-precision reference of the same sum is 2446257.2. What this shows:

1. **`-O3` alone did not help.** Compilers must preserve the exact order of floating-point operations unless told otherwise, because addition is not associative. A sequential `dot += x[i]*y[i]` is a chain of dependent adds; the compiler may vectorise the multiplications but must still add the products one after another in source order, so throughput is bound by the add chain's latency.
2. **`-ffast-math` (which permits reassociation) gave about 6x**, because the compiler may keep several partial sums in vector lanes and combine them at the end.
3. **The answers differ**, by 6.2 percent for the strict version and 0.03 percent for the fast one *relative to the double-precision reference*. The strict serial float sum is the *less* accurate here, since accumulating 20 million small terms into a large float running total loses low-order bits. Reassociated partial sums are often more accurate, not less. Speed and accuracy are not a simple trade; but **reproducibility** is: the fast-math result depends on vector width, thread count and compiler version.
4. The first version of this benchmark reported a 20x speedup at `-O3` that was wrong: the compiler recognised that the 20 repetitions were identical and executed the loop once (loop-invariant hoisting). The fix was to make each repetition depend on the previous one. **Compilers delete work that has no observable effect; make benchmarks consume their results.**

Checking with `-Rpass=loop-vectorize` is a useful reminder that a vectorisation remark is not the whole story: on this machine clang reported "vectorized loop (vectorization width: 4, interleaved count: 4)" for the dot-product loop in **both** the strict and the fast-math builds. In the strict build only the multiplies and loads are vectorised and the additions remain an in-order chain (an "in-order reduction"); with `-ffast-math` the compiler may split the sum into independent partial sums, and that is where the 6x comes from. (My first reading, that the strict build did not vectorise at all, was wrong; the timings and the remarks together give the right picture.)

What `-ffast-math` actually allows (GCC/clang): reassociation, assuming no NaNs or infinities, treating signed zero as unimportant, reciprocal approximations, contracting multiply-add (FMA). Related flags offer finer control (`-fassociative-math`, `-fno-math-errno`, `-ffp-contract=fast`, `-fno-signed-zeros`). Consequences: results can differ from other machines and from the strict build; code relying on NaN checks (`isnan`) may break; and some libraries get linked with different semantics. In scientific and ML practice: use strict flags to produce reference results, validate that fast flags stay within a tolerance, and document the choice. Also consider **denormal handling** (flush-to-zero, `-ffast-math` sets it) which speeds up some codes and changes tiny values, and FMA fusing differences between CPUs and GPUs.

### Vectorisation reports

```bash
gcc   -O3 -fopt-info-vec-optimized -fopt-info-vec-missed file.c    # GCC
clang -O3 -Rpass=loop-vectorize -Rpass-missed=loop-vectorize -Rpass-analysis=loop-vectorize file.c
```

Reasons loops are not vectorised include aliasing (use `restrict`/`__restrict__` when valid), non-unit stride, function calls, dependent iterations, and strict FP reductions. Check the report before inserting intrinsics.

## 7. Fortran, Python and libraries

Fortran remains common in legacy and domain codes: `gfortran -O2 -fopenmp prog.f90` (where `gfortran` has replaced the older GNU `g77` front end). A tested example, a parallel harmonic-sum reduction with `!$omp parallel do reduction(+:s)`, compiled with gfortran 16.2.0 and run on 8 threads, printed `harmonic(1e6) = 14.392726722865611  threads= 8`. Module files (`.mod`) are compiler- and version-specific.

When a project mixes C and Fortran object files (compiled separately with `-c` and linked together), symbol-naming conventions differ between the two languages: Fortran compilers historically append or prepend underscores to external subroutine names in `.o` files. As noted in Chapter 21 of the SCL book, you can align C and Fortran symbol names either by compiling the C sources with `-fleading-underscore` `(untested here)` or by controlling Fortran underscore generation with `-fno-underscoring` (or using standard `iso_c_binding` in modern Fortran). When linking C++ functions into C or Fortran programs, declare those C++ functions with `extern "C"` so their names are not mangled. Also watch argument order on the GNU linker command line (`gcc -o myexe *.o -lm`): the single-pass linker resolves unresolved symbols from left to right, so `-lzzz` flags must appear *after* the `.o` object files that call them.

In Python, the GIL limits thread parallelism for pure-Python CPU work; scalable CPU code calls into compiled libraries (NumPy/BLAS, SciPy, PyTorch, Numba) that use OpenMP or pthreads internally, so the thread-count variables above matter for Python jobs too (6.11, Part 3). Prefer vendor-tuned BLAS/LAPACK (MKL, OpenBLAS, BLIS, cuBLAS) to hand-written loops.

## 8. Accelerator directives (brief)

- **OpenMP target**: `#pragma omp target teams distribute parallel for map(to: ...) map(from: ...)` offloads to a GPU with a compiler that supports it (NVIDIA HPC SDK, LLVM, GCC with offload plugins).
- **OpenACC**: a directive model similar in spirit (`#pragma acc parallel loop`), strong in NVIDIA's compilers and in some legacy GPU ports.
- **OpenCL / SYCL / HIP / Kokkos / RAJA**: portability layers; **CUDA** for native NVIDIA programming (Part 10).

For AI infrastructure the point is knowing that a "GPU-enabled" legacy HPC code may use these models and needs the matching compiler stack and runtime on the nodes.

## 9. Building for a cluster: practical rules

1. Build on a node type **representative of the target** (or deliberately for the lowest common denominator).
2. Use modules or Spack/EasyBuild to pin compiler, MPI and library versions; never `module load` "latest" inside a production script (6.6).
3. Put `-g` in release builds; strip separately if needed.
4. Record flags and versions in the binary or metadata (`gcc -frecord-gcc-switches`, build logs).
5. Run a small regression test comparing against a reference, with tolerance, after any compiler or flag change.
6. Run one test on each node type (login-node builds often differ from compute nodes).
7. Static versus dynamic linking: dynamic linking against a module's libraries is normal; verify with `ldd` which libraries the binary loads and that `RPATH`/`RUNPATH` or `LD_LIBRARY_PATH` point to the intended ones.
8. When a job dies with `Illegal instruction`, compare `lscpu` flags between the build and run nodes first.

## 10. Lab (tested on macOS with clang; adapt for Linux)

1. Compile and run `omp_scaling.c` at `-O2`. Plot GB/s against threads. Where does the triad saturate? Repeat after setting `OMP_PROC_BIND=close OMP_PLACES=cores` on Linux and compare.
2. Compile `omp_race.c` at `-O0` and `-O2` and run each five times. Record the racy count. Then replace the racy loop with a `reduction`, and verify.
3. On a multi-socket Linux node, remove the parallel first-touch in `omp_scaling.c` (initialise serially) and compare the triad bandwidth, then fix it with `numactl --interleave=all` and with proper first touch.
4. Compile `flags_kernel.c` with each flag set in section 6 on two different CPU types. Record GFLOP/s and `dot`. Run `lscpu` on each. Try `-march=native` on one and execute on the other, and capture the failure.
5. Use `-fopt-info-vec-missed` (GCC) or `-Rpass-missed` (clang) on a loop of your own and fix one missed vectorisation.
6. Convert the Fortran harmonic sum to C and compare `-O2` strict versus `-Ofast`.
7. Write a Slurm script for an 8-rank, 4-thread hybrid job (`--ntasks-per-node=8 --cpus-per-task=4`), set `OMP_NUM_THREADS` from Slurm, and print affinity with `OMP_DISPLAY_AFFINITY=true`. (Untested without a cluster.)

## 11. Interview angles

- What does `-O3` do that `-O2` does not? Why did my reduction not speed up?
- What does `-ffast-math` change and why can results differ between machines?
- A binary runs on node A and prints `Illegal instruction` on node B. Why, and how do you build for both?
- Explain first touch and NUMA. How would you detect remote-memory access?
- What is oversubscription in a hybrid job, and how do you prevent it in Slurm?
- Data race versus false sharing: symptoms and fixes.
- Why is a memory-bound loop not faster with more threads?
- How do `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `torch.set_num_threads` interact in a Python job?
- Which compiler families exist and when would you use the NVIDIA HPC SDK?

## 12. Checkpoint questions (30)

1. Describe OpenMP's fork-join model.
2. What does a directive compile to without `-fopenmp`?
3. Define `shared`, `private`, `firstprivate` and `reduction`.
4. Compare static, dynamic and guided schedules.
5. What is the cost of `atomic` versus `reduction`?
6. What does `nowait` do?
7. Name four `OMP_*` environment variables and their purposes.
8. What is first touch and why does it matter?
9. What does `OMP_PROC_BIND=close` do compared with `spread`?
10. Why might using hyperthreads hurt FP-heavy code?
11. How do you set threads correctly under Slurm?
12. Why did the triad stop scaling beyond two threads in the lab?
13. Why can a data race pass tests?
14. What is false sharing and what cache-line sizes exist?
15. Name three tools for finding races.
16. List five compiler families.
17. What are the `-O0` to `-O3` and `-Ofast` differences?
18. What does `-march=native` do and what is its main risk?
19. How do you build one binary for a mixed fleet?
20. Why does strict FP prevent vectorising a reduction?
21. What did `-ffast-math` change in the lab, in speed and in the result?
22. Which of the two results was closer to the double-precision reference?
23. What was wrong with the first version of the benchmark?
24. How do you get a vectorisation report in GCC and clang?
25. What can block vectorisation?
26. What are denormals and flush-to-zero?
27. Why must Fortran `.mod` files match the compiler, what flags align C/Fortran symbol underscores when linking `.o` files, and what are three operational pitfalls of floating compiler licence servers? (Answer: `.mod` files are compiler- and version-specific; `-fleading-underscore` on C or `-fno-underscoring` on Fortran aligns symbol names; floating licences can hold a seat for `15 minutes` after a single call or crash, require at least `50%` server quorum in redundant setups, and bind to the server's NIC MAC address.)
28. Why do mixed OpenMP runtimes cause problems?
29. What do OpenMP target and OpenACC do?
30. List four rules for building software on a cluster.

## 13. Sources and review notes

- Book source (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`):
  - Chapter `21. Compilers and Environments, for Parallel Technologies` (read in full): `gcc`/`gfortran` compilation and linking (`-c`, `-o`, `-l`, `-I`, `-L`, `-On`, `-fleading-underscore` for C/Fortran symbol linking, `extern "C"` for C++, GNU linker argument order), commercial compiler licensing pitfalls (`15-minute` seat lease hold, `50%` quorum rule for redundant licence servers, and MAC address binding), OpenMP, CUDA, OpenCL, OpenACC, and OpenSHMEM overview.
  - Chapter `22. Parallel Computing Support Libraries` (read in full): library and debugging context.
- OpenMP model, affinity, first touch, hybrid MPI+OpenMP and thread-placement pitfalls: *Parallel and High Performance Computing* (Robey and Zamora, Manning), chapters on OpenMP and affinity (in the corpus). All prose is my own restatement.
- Original: the four C programs and the Fortran snippet under `code/part06/` and every measurement and observation reported above, produced on the machine described in the status box. Two of my own benchmark mistakes (no warm-up; hoisted loop) are reported deliberately.
- Not reproduced: false-sharing slowdown on Apple M3. Not tested: Linux-specific binding commands, Slurm scripts, `-march=native` crash on mismatched nodes, GCC-specific flags (`-fleading-underscore`, `-fno-underscoring`), compiler families other than clang and gfortran, licence servers.
- Unverified: flag spellings for the Intel and NVIDIA compilers beyond those listed; cache-line sizes quoted for server CPUs.
