---
id: "c01-17"
title: "1.17 Memory management: virtual memory, NUMA, huge pages, OOM"
sidebar_label: "1.17 Memory management: virtual memory, NUMA, huge pages, OOM"
sidebar_position: 17
description: "Memory management: virtual memory, NUMA, huge pages, OOM"
status: "drafted"
tier: "0"
level: "A"
lab_venue: "GCP / GKE"
---

# 1.17 Memory management: virtual memory, NUMA, huge pages, OOM

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | GCP / GKE (an Ubuntu VM; a multi-socket or multi-GPU machine for the NUMA commands) |
| Part | Part 1: Linux, from the command line to the kernel and performance |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Host memory is the hidden resource on a GPU server. The GPUs hold the model, but the host's RAM holds the dataset cache, the data-loader workers, pinned staging buffers, the framework's own heap, the page cache of everything read, the container images, and the CUDA driver's mappings. Most "mysterious" problems on GPU nodes turn out to be memory problems:

- A training job is **OOM-killed** (exit code 137) although `nvidia-smi` shows free GPU memory, because the *host* or the job's cgroup ran out of RAM.
- A data loader is slow because its memory lives on the **wrong NUMA node**, so every batch crosses the inter-socket link on the way to the GPU.
- Throughput wobbles every few minutes because **direct reclaim** or **transparent huge page compaction** stalls threads.
- A process cannot register RDMA or pinned memory because of the **`memlock`** limit, or the node swaps and the job slows by orders of magnitude.
- A long-running service's resident memory grows for days and nobody knows whether it is a leak, a cache, or allocator fragmentation.
- `free` shows 2 GB "free" and an alarm fires, although 400 GB is cache that the kernel would give back instantly.

This chapter builds the whole picture: virtual memory, paging, demand paging and overcommit; the page cache and reclaim; the memory hardware (DRAM, caches, MMU, TLB, NUMA); huge pages and THP; allocators; the OOM killer (system-wide and per cgroup); NUMA policy and placement; memory limits in cgroups and containers; the observability tools (`free`, `vmstat`, PSI, `/proc/meminfo`, `smaps`, `numastat`, `pmap`, `slabtop`, `perf`, BPF tools); and the method for diagnosing leaks, growth, saturation and locality. It ends with the GPU-specific points: pinned memory, `memlock`, NUMA binding for loaders, THP policy for training versus inference, and swap policy. Chapter 1.8 introduced page faults and `vmstat`; chapter 1.18 covers CPU scheduling and cgroups; chapter 1.28 assembles the tuning.

## Prerequisites and outcomes

You should know processes and the address space (1.8, 1.11), filesystem caching (1.12), sysctl (1.10) and systemd resource control (1.15).

After this chapter you can:

- Explain virtual memory, pages, page tables, the MMU and TLB, demand paging, minor and major faults, and RSS versus virtual size versus PSS.
- Describe how Linux frees memory (free lists, page cache, swapping, reaping, kswapd and direct reclaim, the OOM killer) and what swappiness, watermarks and overcommit do.
- Read `/proc/meminfo`, `free`, `vmstat`, `smem`/`smaps`, and distinguish "available" from "free", anonymous from file-backed memory, and kernel from user memory.
- Predict and tune the OOM killer: `oom_score`, `oom_score_adj`, cgroup memory limits, `memory.events`, `systemd-oomd`, and read an OOM log.
- Explain NUMA, inspect topology (`numactl -H`, `lscpu`, `nvidia-smi topo -m`), bind CPUs and memory, interpret `numastat` and automatic NUMA balancing, and avoid the cross-socket trap for GPU feeding.
- Configure huge pages (explicit and transparent), pick THP policy, and understand TLB reach.
- Choose and apply allocators (glibc, jemalloc, tcmalloc) and diagnose heap growth and leaks.
- Use cgroup memory controls and read their statistics for containers and Slurm jobs.
- Apply swap, memlock and pinned-memory settings correctly for GPU/RDMA workloads.

## 1. Memory at a glance

```mermaid
flowchart TB
  subgraph Proc["Each process"]
    VA["Virtual address space (private, huge, mostly unmapped)"]
  end
  VA -->|"MMU + page tables + TLB\n(per-page translation)"| PM["Physical memory (RAM, DRAM, NUMA nodes)"]
  VA -.->|"anonymous pages paged out (swapping)"| SW["Swap (disk/zram)"]
  VA -.->|"file-backed pages (mmap, page cache) paged from"| FS["Filesystem / disk"]
  PM --> K["Kernel memory: slab, page tables, stacks, driver buffers"]
  PM --> PC["Page cache (file data), reclaimable"]
  PM --> AN["Anonymous memory: heap, stacks, tensors on the host"]
  PM --> HP["Hugepages / pinned (locked) memory"]
```

Four ideas carry the chapter:

1. **Virtual memory** gives each process the illusion of a large private address space; the kernel and hardware map pieces of it to physical RAM *on demand*.
2. **RAM is a cache** for disk and swap: the kernel fills spare memory with file data and reclaims it under pressure. "Free" memory is wasted memory.
3. **Locality matters twice**: temporal and spatial locality at the CPU-cache level, and **NUMA locality** at the socket level. Where a page lives decides how fast every access is.
4. **Limits are enforced per cgroup**, not only per machine. A container can be OOM-killed while the host has lots of RAM free.

## 2. Virtual memory and paging

**Terminology.** *Main memory* is the physical RAM (DRAM). *Virtual memory* is an abstraction: each process and the kernel have their own linear address space, mostly unpopulated, not "real" memory. *Resident* memory is what is currently in RAM. *Anonymous memory* has no file behind it (heap, stacks, `mmap` with `MAP_ANONYMOUS`); *file-backed memory* maps a file (program text, libraries, `mmap`ed data, the page cache). A *page* is the unit of mapping (4 KiB normally; 2 MiB and 1 GiB *huge pages* too). A *page fault* is an access to a virtual page that is not currently mapped to a physical page: it is normal and often cheap. *Paging* is moving pages between RAM and storage; *swapping* in Linux means paging **anonymous** memory to a swap device or file (Linux does not swap whole processes). An *address space* belongs to one process (plus a kernel space); *segments* are areas with a purpose (text, data, heap, stacks, mappings).

### Why virtual memory

It gives each process private memory regardless of others (**isolation**), lets programs be larger than RAM or only partially resident (**oversubscription**), lets the system share one physical copy of library code among many processes (**sharing**), allows files to be accessed as memory (`mmap`), and simplifies programming (contiguous addresses). The cost is address translation, handled by hardware.

### Translation: page tables, MMU and TLB

The CPU's **MMU** translates virtual addresses to physical addresses using **page tables** in RAM maintained by the kernel: a multi-level tree (four or five levels on x86-64: PGD, P4D, PUD, PMD, PTE). A 64-bit virtual address is split into index fields for each level plus a **page offset**; the walk reads one entry per level from RAM, so a naive translation would cost four or five extra memory accesses per access. The **TLB** (translation lookaside buffer) is a small, very fast cache of recent translations inside the CPU; a **TLB hit** costs almost nothing, a **TLB miss** triggers a hardware page-table walk (tens to hundreds of cycles, or a hundred nanoseconds if the table entries themselves miss the CPU caches). The TLB has limited entries (for example 64 for 4 KiB data pages), so its **reach** (entries x page size) is small with 4 KiB pages: a program with a multi-gigabyte working set misses constantly. **Huge pages** (2 MiB, 1 GiB) multiply the reach and also shorten the walk: that is why they matter for AI workloads with tens or hundreds of gigabytes of host memory (section 8).

```mermaid
flowchart LR
  VA["64-bit virtual address"] --> SPLIT["split into: PGD idx | P4D idx | PUD idx | PMD idx | PTE idx | 12-bit offset"]
  SPLIT --> TLB{"TLB hit?"}
  TLB -- yes --> PA["physical address -> RAM / CPU cache"]
  TLB -- no --> WALK["page walk: CR3 -> PGD -> P4D -> PUD -> PMD -> PTE (up to 5 memory reads)"]
  WALK --> FILL["fill TLB"]
  FILL --> PA
  WALK -- "entry not present" --> PF["page fault -> kernel"]
```

### Demand paging, page faults, memory states

Linux allocates virtual memory immediately and **physical memory only when touched** (demand paging). A `malloc(1<<30)` or an `mmap` of a gigabyte consumes almost no RAM until the pages are written. Each virtual page is in one of four states: *unallocated*; *allocated but not mapped* (not yet touched); *mapped to RAM*; *mapped to swap* (paged out). Moving from "allocated, unmapped" to "mapped" is a page fault:

- **Minor fault**: satisfied without I/O (a new zero page for the heap, mapping an already-cached file page or a shared library page). Cheap and frequent.
- **Major fault**: requires reading from storage (first touch of an uncached file-backed page, or swapping in an anonymous page). Slow: milliseconds on spinning disks, tens to hundreds of microseconds on flash, and the thread blocks.

Two sizes follow: **virtual size (VSZ/VIRT)** is everything allocated (all states except unallocated); **resident set size (RSS)** is the part in RAM. **Shared memory** (shared libraries, `shmget`/`mmap` shared, tmpfs) is counted in the RSS of every process mapping it, so summing RSS over processes overstates use. **PSS** (proportional set size) divides shared pages among their users and sums correctly (`/proc/PID/smaps_rollup`, `smem`, `pmap -X`). **USS** (unique set size) is private memory only. The **working set size (WSS)** is the memory a process actively uses; performance collapses when the WSS exceeds available RAM (and improves greatly when it fits in the CPU caches). There is no standard WSS metric in tools (they report RSS), but estimates exist (`wss` tool using idle-page tracking; the "memory shrinking" negative experiment: reduce available memory step by step until swapping starts, only in test).

### Overcommit

Linux can grant more virtual memory than RAM plus swap, because programs rarely use everything they allocate. `vm.overcommit_memory`:

| Value | Policy |
|---|---|
| `0` (default) | Heuristic: refuse only obviously excessive single requests; everything else succeeds |
| `1` | Always allow (never fail `malloc`; used by some HPC/scientific and Redis-style setups) |
| `2` | Strict: total committed virtual memory limited to swap + `vm.overcommit_ratio`% of RAM (or `vm.overcommit_kbytes`); allocations fail with `ENOMEM` when exceeded |

The price of overcommit is that a failure is deferred: instead of `malloc` returning `NULL`, memory runs out later, at first touch, and the **OOM killer** (section 5) chooses a victim. With `2`, allocation errors surface early and predictably but many programs (including those that reserve large address spaces, such as JVMs and some CUDA/GPU runtimes and `fork` of big processes) misbehave. Strict mode is rare in practice; know the knob, and `grep -E 'Commit' /proc/meminfo` (`CommitLimit`, `Committed_AS`).

### Utilisation and saturation

Memory utilisation is "used versus total" **where file cache counts as available** (it is reclaimable). **Saturation** is demand exceeding available RAM, shown by page scanning, paging/swapping, direct reclaim, and OOM kills; PSI (section 6) measures it directly. **Errors** are allocation failures, OOM kills, and hardware errors (ECC; `edac-util`, `ipmitool sel`, `dmesg | grep -i -E 'mce|edac'`).

### Swap

Swap holds paged-out anonymous pages (and, for tmpfs, tmpfs pages). It lets rarely used memory (an idle daemon's heap) make room for cache, and gives a grace period under pressure: with swap an endlessly growing process first degrades (visible, debuggable), without swap it is OOM-killed immediately. The cost is that touching swapped memory blocks on disk I/O. **On GPU and latency-sensitive nodes the usual policy is little or no swap and low `vm.swappiness`, with the OOM killer and cgroup limits as the safety net**, because a training process that is partially swapped out slows by orders of magnitude and stalls collective communication for the whole job. Large-scale services often prefer to be OOM-killed and rescheduled over limping; just make sure the OOM victim is the job, not `sshd`/`kubelet` (chapter 1.15 section 10). `zram`/`zswap` (compressed swap in RAM) are middle options on small hosts. Commands: `swapon --show`, `free -h`, `cat /proc/swaps`, `swapoff -a`, `vm.swappiness`.

## 3. Memory hardware that affects performance

**DRAM** is volatile, dense memory; **DDR4/DDR5** channels set bandwidth (DDR5-4800 is 38.4 GB/s per channel; servers have 8 to 12 channels per socket, so hundreds of GB/s). Latency to DRAM is on the order of 80 to 100 ns (with CAS latency of tens of ns plus controller and interconnect). **CPU caches** (L1 per core, L2, shared L3; instruction and data) hide this: L1 about 1 ns, L2 a few ns, L3 ten-plus ns. The hardware moves data in **cache lines** (64 bytes). **ECC** memory detects and corrects single-bit errors (correctable errors are logged by EDAC and are a leading failure indicator; uncorrectable errors crash processes or the machine). **HBM** on GPUs is separate, much faster memory attached to the GPU; **Grace CPU LPDDR5X** memory and **NVLink-C2C** on GH200/GB200 give a coherent CPU-GPU address space but Linux still models CPU DRAM and GPU HBM as separate pools (and exposes the Grace memory as NUMA nodes).

### UMA versus NUMA

On a **UMA/SMP** machine every CPU reaches all memory with the same latency over a shared bus. Modern servers are **NUMA** (non-uniform memory access): each socket has its own memory controllers and attached DRAM (a *node*), and sockets are joined by an interconnect (UPI on Intel, Infinity Fabric/xGMI on AMD). A CPU reaches **local** memory directly and **remote** memory through the other CPU, which is slower (commonly 1.3x to 2x the latency, with reduced bandwidth, and it consumes interconnect bandwidth). Many modern CPUs present several NUMA nodes *per socket* (sub-NUMA clustering, NPS modes), so a 2-socket server can show 2, 4 or 8 nodes. PCIe devices (GPUs, NICs, NVMe) hang off a particular socket's root complex, so they too have a **home node**.

```mermaid
flowchart LR
  subgraph N0["NUMA node 0"]
    C0["CPU socket 0"] --- M0[("DRAM 0")]
    C0 --- P0["PCIe root 0"]
    P0 --- G0["GPU 0,1"] 
    P0 --- NIC0["NIC 0"]
  end
  subgraph N1["NUMA node 1"]
    C1["CPU socket 1"] --- M1[("DRAM 1")]
    C1 --- P1["PCIe root 1"]
    P1 --- G1["GPU 2,3"]
    P1 --- NIC1["NIC 1"]
  end
  C0 <-->|"UPI / xGMI interconnect (slower, shared)"| C1
```

The "NUMA trap" for AI hosts: a data-loading process runs on node 0 and allocates its buffers there, but the GPU it feeds is attached to node 1. Every host-to-device copy then crosses the interconnect (memory on node 0, GPU on node 1's PCIe root). Fix by **binding** the loader's CPUs and memory to the GPU's node (section 7).

## 4. How Linux frees memory

Memory is requested from the kernel's **page allocator**, which keeps **free lists** per NUMA node and per memory zone (DMA, DMA32, Normal), organised by the **buddy allocator**: free blocks come in power-of-two sizes (order 0 = one page, order 9 = 2 MiB, ...) and neighbouring free blocks ("buddies") merge. The kernel's own small objects (inodes, dentries, task structs) come from the **slab/SLUB allocator**, which keeps per-type caches of pre-allocated objects (`slabtop`). User-space `malloc` obtains pages from the kernel and subdivides them (section 9).

When free memory falls, Linux uses several methods, in roughly this order as pressure rises:

```mermaid
flowchart TD
  A["Free pages above 'high' watermark: all fine"] --> B["Below 'low' watermark:\nkswapd wakes (background reclaim)"]
  B --> C1["Reclaim page cache (clean pages dropped instantly; dirty ones written first)"]
  B --> C2["Swap out cold anonymous pages (if swap exists; bias set by vm.swappiness)"]
  B --> C3["Reap/shrink kernel caches (slab: dentries, inodes)"]
  B -->|"allocation outpaces kswapd; below 'min'"| D["Direct reclaim:\nthe ALLOCATING thread pauses and reclaims synchronously -> latency stalls"]
  D -->|"nothing left to reclaim"| E["OOM killer selects and kills a process"]
```

- **Watermarks** (`min`, `low`, `high`, per zone) derive from `vm.min_free_kbytes` (the `low` and `high` marks scale from `min`; `vm.watermark_scale_factor` controls the gap, default 10 meaning 0.1% of memory; `vm.watermark_boost_factor` lets kswapd reclaim extra after fragmentation events). `kswapd` is the per-node background page-out daemon, scanning the active/inactive LRU lists. Hysteresis keeps it from flapping. **Direct reclaim** happens when an allocation cannot wait: the application thread itself does the reclaim work, which shows up as unexplained latency spikes and high `sys` time. Raising `vm.min_free_kbytes` moderately (and `watermark_scale_factor`) makes kswapd start earlier and can eliminate direct-reclaim stalls on large memory machines (test on a canary; very large values waste RAM and can cause other trouble).
- **Page cache vs anonymous**: `vm.swappiness` (0 to 100, default 60; up to 200 on cgroup v2/newer kernels) biases reclaim between dropping page cache and swapping anonymous pages. Setting it very low keeps application memory resident at the expense of cache. On GPU nodes the common settings are 0 to 10 (documentation often says 1). With 0 the kernel still swaps when it must.
- **`vm.vfs_cache_pressure`** (default 100) controls how eagerly dentry/inode caches are reclaimed (lower keeps them, 0 never reclaims and can cause OOM).
- **Dirty pages** (modified file data awaiting write-back) are limited by `vm.dirty_ratio`/`dirty_background_ratio` or the `_bytes` forms (chapter 1.12); a flood of dirty data can itself cause stalls.
- **Dropping caches** (`echo 3 > /proc/sys/vm/drop_caches`) is a test tool, not a tuning knob; the kernel refills the cache right away.
- **Compaction** defragments physical memory so that large contiguous blocks (huge pages, high-order allocations) can be found; it costs CPU and can stall (section 8). `cat /proc/buddyinfo`, `/proc/pagetypeinfo`, `/proc/vmstat` (`compact_*`, `thp_*`, `pgscan_*`, `pgsteal_*`, `allocstall_*`, `oom_kill`) show these.

## 5. The OOM killer

When reclaim fails, the kernel invokes the **out-of-memory (OOM) killer**: it selects a process by a "badness" score and kills it with `SIGKILL`, logging to the kernel ring buffer (`dmesg`, `journalctl -k`: `Out of memory: Killed process 1234 (python) total-vm:... anon-rss:...`, also `oom-kill:constraint=...`, and a dump of all candidate processes). The victim cannot clean up (no `SIGTERM`), so partial checkpoints and GPU state may be left behind; the exit status seen by a parent or by Kubernetes is `137` (128 + 9).

**Scoring.** `/proc/PID/oom_score` is a number (0 to 1000) roughly proportional to the share of RAM (and swap) the process (plus its children in some versions) uses, adjusted by **`/proc/PID/oom_score_adj`** (-1000 to +1000, added to the score): `-1000` makes a process immune to the OOM killer, `+1000` makes it the first choice. Older root-user bonuses no longer exist on current kernels. Protect critical daemons (`echo -1000 > /proc/$(pidof sshd)/oom_score_adj`, or `OOMScoreAdjust=-900` in the systemd unit, chapter 1.15) and optionally make batch workers preferred victims (`+500`).

**cgroup OOM.** With memory cgroups, each group has its own limit (`memory.max`). When a group exceeds it and cannot reclaim enough, the kernel runs the OOM killer **inside that cgroup**, killing one of its processes (or the whole group if `memory.oom.group=1`). This is exactly what happens to a container exceeding its limit: the host may have hundreds of gigabytes free. Evidence: `memory.events` (counters `high`, `max`, `oom`, `oom_kill`), `dmesg` messages with `constraint=CONSTRAINT_MEMCG` and the cgroup path, Kubernetes `OOMKilled` reason. Contrast with a **global OOM**, where the whole machine is out of memory. A different case is a **NUMA-constrained OOM**: a process bound (`--membind`, cpuset `cpuset.mems`) to a node that is full can OOM although other nodes have free memory (and low-memory zones such as DMA32 can also exhaust: look at the `Node 0 DMA32 free:...` lines in the OOM report).

**Userspace OOM daemons.** The kernel OOM killer reacts late, after the system has already thrashed. `systemd-oomd` (uses PSI and cgroup memory data to kill whole cgroups under sustained pressure), `earlyoom` and `nohang` act earlier. On clusters, the scheduler enforces memory limits (Slurm cgroup plugin with `--mem`, Kubernetes limits and kubelet eviction thresholds) so the node as a whole seldom reaches a global OOM. **Kubelet eviction** (`evictionHard: memory.available<...`) removes pods before the kernel OOM kills randomly; set node reservations (`systemReserved`, `kubeReserved`).

**Reading an OOM report**: find the `invoked oom-killer` line (who requested memory and the `gfp_mask`/`order`), the memory summary (`Mem-Info`: `active_anon`, `inactive_file`, `slab_reclaimable`, `free`, `shmem`), the per-zone free counts, the task table (pid, uid, `total_vm`, `rss`, `oom_score_adj`, name), and the `Killed process` line. If `shmem` or `tmpfs` is huge, in-memory filesystems (`/dev/shm`, `/tmp` on tmpfs, `emptyDir` Memory medium) are the consumer; if `slab_unreclaimable` is huge, a kernel/driver leak; if `anon_rss` of one process dominates, the application.

## 6. Observing memory

### The summary view: `free` and `/proc/meminfo`

```bash
free -h
#                total   used   free  shared  buff/cache  available
# Mem:           1.9Ti  120Gi   40Gi    1.2Gi      1.7Ti      1.7Ti
# Swap:             0B     0B     0B
free -mw                      # wide: separate 'buffers' and 'cache'
grep -E 'MemTotal|MemFree|MemAvailable|Buffers|^Cached|SwapTotal|SwapFree|Dirty|Writeback|AnonPages|Mapped|Shmem|Slab|SReclaimable|SUnreclaim|PageTables|Mlocked|HugePages|AnonHugePages|Hugepagesize|Committed_AS|CommitLimit' /proc/meminfo
```

**The key number is `available`** (`MemAvailable`): an estimate of how much memory is available to start new applications **without swapping**, counting reclaimable page cache and slab. `free` is idle memory, deliberately small. `buff/cache` is mostly reclaimable (but `shared`/tmpfs and `mlock`ed pages are not). The breakdown to remember: `AnonPages` (process private heap/stack), `Cached` (page cache incl. mapped files and tmpfs/`Shmem`), `Slab` (`SReclaimable` can be freed, `SUnreclaim` cannot), `PageTables`, `KernelStack`, `HugePages_*` (explicitly reserved, not available to ordinary allocation), `Mlocked`/`Unevictable`.

### Pressure and activity: `vmstat`, PSI, `sar`

```bash
vmstat 1 5                    # si/so = swap in/out per second; free/buff/cache; b = blocked; wa = I/O wait
cat /proc/pressure/memory     # some avg10=.. avg60=.. avg300=.. total=..  and  full ...
sar -B 1 5                    # paging: pgpgin/out, fault/s, majflt/s, pgscank/s, pgscand/s (direct scan!), pgsteal/s, %vmeff
sar -r 1 5; sar -S 1 5        # memory utilisation; swap
grep -E 'pgscan|pgsteal|allocstall|oom_kill|thp_|compact_stall|numa_' /proc/vmstat
```

**PSI** (pressure stall information, Linux 4.20+): `some` is the percentage of time at least one task stalled waiting for memory; `full` is the time all non-idle tasks stalled. Averages over 10, 60 and 300 seconds. Any sustained non-zero `some`, and any `full`, is a saturation signal far more direct than free-memory numbers. Per-cgroup PSI exists in `memory.pressure`. `sar -B`: continuous `pgscand/s` (direct scans) means allocating threads are reclaiming themselves: stalls.

### Per process

```bash
ps -eo pid,ppid,user,rss,vsz,pmem,comm --sort=-rss | head       # RSS in KiB, VSZ; %MEM
top -o %MEM                    # M sorts by resident memory; columns VIRT, RES, SHR
cat /proc/PID/status | grep -E 'VmPeak|VmSize|VmRSS|RssAnon|RssFile|RssShmem|VmSwap|VmLck|VmHWM|Threads'   # VmHWM = peak RSS
cat /proc/PID/smaps_rollup     # Rss, Pss, Shared/Private Clean/Dirty, Anonymous, Swap, Locked (summed)
pmap -x PID | tail -20         # per-mapping Rss/Dirty; pmap -X for PSS; shows [heap], [stack], libraries, big anonymous mappings
smem -rk | head                # PSS, USS per process (install smem)
numastat -p PID                # which NUMA nodes hold this process's pages
```

In `top`: `VIRT` (everything allocated and mapped), `RES` (resident), `SHR` (the part of RES that is shared). Large `VIRT` is not a problem by itself (GPU processes show terabytes of VIRT because the CUDA driver reserves large address ranges). Look at `RES` and its anonymous part.

### Kernel memory and caches: `slabtop`, `/proc/slabinfo`

`sudo slabtop -o -s c | head -15` lists the kernel caches sorted by size (`dentry`, `inode_cache`, `ext4_inode_cache`, `kmalloc-*`, `nvidia`-related). A huge `dentry`/`inode` cache after scanning millions of files is normal and reclaimable; a growing `kmalloc-*` or driver cache that never shrinks is a kernel/driver leak (check `SUnreclaim`).

### Tracing: `perf`, BCC, `bpftrace`

Page-fault and allocation events: `perf stat -e page-faults,minor-faults,major-faults -p PID`, `perf record -e page-faults -g -p PID`, `perf trace -F all`. BCC/bpftrace tools (chapter 1.24): `drsnoop` (direct reclaim latency per process), `memleak -p PID` (allocations not freed, with stacks; high overhead), `oomkill` (traces OOM kills), `cachestat`, `slabratetop`, `numamove` (NUMA page migrations), `wss` (working-set estimation). Cheap trick: a CPU profile (flame graph) and search for `malloc`, `page_fault`, `clear_page`, `compact`, `isolate`.

### The method for memory problems

1. **USE**: utilisation (`available`, per-cgroup usage), saturation (PSI, `si/so`, `pgscand`, OOM kills), errors (allocation failures, OOM, ECC/EDAC).
2. **Characterise**: system-wide usage, kernel versus user, cache versus anonymous, biggest processes (RSS and PSS), cgroup limits and usage, NUMA distribution, huge page use, swap.
3. **Growth versus leak**: a *leak* is memory allocated and never freed (a bug); *growth* is normal use at a higher rate or a cache warming up. First ask "is it supposed to do that?" (check configuration, cache sizes, allocator behaviour). Then watch RSS over time per process (`pidstat -r 60`, node_exporter `process` metrics, `smem`), find the allocation path (`memleak`, `jemalloc`/`tcmalloc` heap profiling, language profilers such as Python `tracemalloc`, `memray`, `objgraph`; PyTorch `torch.cuda.memory_summary` is GPU memory, not host).
4. **Static**: total RAM and DIMM population (all channels filled?), memory speed, NUMA mode, BIOS settings, huge pages, overcommit, limits, allocator.
5. **Tune last, one change at a time** (section 10).

Memory capacity planning for training nodes: sum the data-loader worker footprints (each worker process may hold a copy of dataset indexes and decoded batches), pinned staging buffers, framework overhead, the page cache you want to keep for the dataset, and a margin; compare with `MemAvailable` and cgroup limits; test with the real job and watch `RssAnon` and PSI.

## 7. NUMA in practice

### Discover the topology

```bash
lscpu | grep -E 'Model name|Socket|NUMA|Thread|Core|L3'
numactl --hardware                 # nodes, CPUs per node, memory per node, node distance matrix
#   node distances:  node 0 1 / 0: 10 21 / 1: 21 10   (10 = local, 21 = about 2.1x remote cost)
ls /sys/devices/system/node/; cat /sys/devices/system/node/node0/cpulist
lstopo --of ascii                  # hwloc: sockets, caches, memory, PCI devices, GPUs, NICs
nvidia-smi topo -m                 # GPU<->GPU links (NV#, PIX, PHB, SYS) and each GPU's CPU/NUMA affinity
cat /sys/bus/pci/devices/0000:3b:00.0/numa_node        # a device's home node (-1 = unknown)
numastat                           # per-node numa_hit / numa_miss / numa_foreign / local_node / other_node
numastat -m                        # per-node meminfo-style breakdown
```

`numa_hit`: allocations satisfied on the intended node; `numa_miss`: allocated here although another node was intended (that node was full); `numa_foreign`: intended here but allocated elsewhere; `other_node`: allocations made by a process running on a different node than the page. Rising `numa_miss`/`other_node` while a workload runs means remote placement and cross-socket traffic.

### Policies and binding

The default policy is **local allocation with first touch**: a page is placed on the node of the CPU that first writes it. If one thread initialises a huge buffer and others on a different node use it, the buffer is entirely remote for them. Policies: **bind** (only these nodes), **preferred** (try this, fall back), **interleave** (round-robin pages across nodes, good for data accessed by all CPUs), **local** (default).

```bash
numactl --cpunodebind=1 --membind=1 python train.py --gpu 4        # run on node 1's CPUs with node 1's memory
numactl --interleave=all ./big_shared_table                        # spread pages over all nodes
numactl --physcpubind=16-31 --localalloc ./prog                   # particular cores, local memory
taskset -c 16-31 ./prog; taskset -cp 16-31 PID                     # CPU affinity only (memory follows first touch)
numactl --show                                                      # current policy of this shell
```

Per-GPU launch on an 8-GPU, 2-socket machine (illustrative; derive nodes from topology, never hard-code):

```bash
for g in 0 1 2 3 4 5 6 7; do
  node=$(cat /sys/bus/pci/devices/$(nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader -i $g | sed 's/^0000//;s/^00000000/0000/' | tr 'A-Z' 'a-z')/numa_node)
  CUDA_VISIBLE_DEVICES=$g numactl --cpunodebind=$node --membind=$node python train.py --rank $g &
done; wait
```

In frameworks: pin each data-loader worker to the GPU's node (PyTorch `DataLoader(worker_init_fn=...)` calling `os.sched_setaffinity` and `libnuma`), use persistent workers so affinity survives epochs, create **pinned** host buffers from threads on the right node, and re-apply binding inside worker processes (a spawn start method or `exec` does not inherit `numactl` memory policy; `fork` does). Slurm provides `--cpu-bind`, `--mem-bind`, `--gpu-bind=closest`, and Kubernetes the Topology Manager and CPU/Memory Managers (Part 6 and Kubernetes chapters). Containers: `docker run --cpuset-cpus --cpuset-mems`.

**Automatic NUMA balancing** (`kernel.numa_balancing=1`) samples page accesses and migrates pages or threads toward each other; helpful for general workloads, but its scanning and page-migration faults add overhead and jitter, and the kernel's guesses are worse than explicit binding for GPU feeding. Many AI sites disable it (`sysctl kernel.numa_balancing=0`) on nodes where processes are explicitly bound; tune `kernel.numa_balancing_scan_size_mb` instead if keeping it on. `zone_reclaim_mode` (default 0 on modern kernels) makes allocation reclaim the local node before using a remote one; leave 0 except for specific database/NUMA-isolation reasons.

Grace-based systems (GH200/GB200) expose CPU memory and, depending on configuration, GPU memory as NUMA nodes with very different distances; the unified (coherent) address space removes the need to copy but not the need to place data well. Always read `numactl -H` and the platform guide.

## 8. Huge pages and transparent huge pages

With 4 KiB pages, a 256 GiB dataset needs 67 million page-table entries and the TLB can cache only a few dozen: constant misses and page walks. **Huge pages** (2 MiB, and 1 GiB on x86-64) reduce page-table size, shorten walks and increase TLB reach by 512x or more, giving typically a few percent (3% to 10%) to more on memory-heavy workloads, plus fewer page faults during initial population.

### Explicit huge pages (hugetlb)

Reserved at boot or runtime in a dedicated pool, **not swappable, not counted as normal available memory**, used by applications that ask for them:

```bash
grep -i huge /proc/meminfo                                  # HugePages_Total/Free/Rsvd/Surp, Hugepagesize
echo 1024 | sudo tee /proc/sys/vm/nr_hugepages              # 1024 x 2 MiB = 2 GiB (may fail if memory is fragmented)
sudo sysctl vm.nr_hugepages=1024                            # persist in /etc/sysctl.d
# 1 GiB pages need boot parameters (they must be reserved early): default_hugepagesz=1G hugepagesz=1G hugepages=64
cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
mount -t hugetlbfs none /mnt/huge -o pagesize=2M           # filesystem interface
# apps: mmap(... MAP_HUGETLB), shmget(SHM_HUGETLB), libhugetlbfs, DPDK, databases (Oracle, PostgreSQL huge_pages=on), VM hypervisors (QEMU -mem-path), NCCL/RDMA in some configurations
```

Use explicit huge pages for: VM guests and hypervisors, DPDK/RDMA data planes, large in-memory databases, and workloads that need guaranteed, predictable page size. Reserve them at boot when possible (fragmentation makes late reservation unreliable) and size them so the rest of the system still has memory; per-NUMA-node pools: `/sys/devices/system/node/node*/hugepages/`.

### Transparent huge pages (THP)

THP lets the kernel **automatically** back large aligned anonymous regions with 2 MiB pages and split or merge them as needed, with no application changes:

```bash
cat /sys/kernel/mm/transparent_hugepage/enabled      # [always] madvise never
cat /sys/kernel/mm/transparent_hugepage/defrag       # always defer defer+madvise [madvise] never
grep -E 'AnonHugePages|thp_' /proc/meminfo /proc/vmstat
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled        # runtime; or boot param transparent_hugepage=madvise
```

`enabled=always` uses huge pages wherever possible; `madvise` only for regions where the application calls `madvise(MADV_HUGEPAGE)`; `never` disables. `defrag` controls how hard the kernel works (direct compaction) to find a huge page at fault time. Trade-offs: THP can reduce TLB misses and page faults (good for throughput workloads such as training, with big contiguous tensors in host memory) but costs **latency spikes** when the kernel compacts memory or `khugepaged` collapses pages, and can **bloat** memory for sparse allocations (a few touched bytes can pin 2 MiB). Common guidance: **training/throughput nodes: `always` (or `madvise` with frameworks that opt in); latency-critical inference servers, databases and Redis: `madvise` or `never`**, with `defrag=defer` or `madvise` to avoid synchronous compaction stalls; test on your workload and watch `thp_fault_alloc`, `thp_collapse_alloc`, `compact_stall` in `/proc/vmstat` and application tail latency. Set policy at boot (kernel parameter or a `tuned`/systemd-tmpfiles unit), not by editing `/sys` once by hand.

When using large **pinned** host buffers, see section 11 for `memlock`.

## 9. Allocators and heap behaviour

`malloc` is user-space library code, not a system call: it obtains big chunks from the kernel (`brk` for the main heap, `mmap` for large requests and for per-thread arenas) and hands out pieces. `free` usually returns memory to the allocator, **not** to the operating system, so RSS stays high; this is normal ("heap growth"). glibc's `malloc_trim()` and `M_TRIM_THRESHOLD` can release top-of-heap and (since glibc 2.8) free ranges; very large allocations (above `M_MMAP_THRESHOLD`, default 128 KiB, dynamic) get their own `mmap` and are returned immediately on `free`. Multithreaded programs create up to 8x CPU-count arenas, which can multiply fragmentation: `MALLOC_ARENA_MAX=2..4`, `MALLOC_TRIM_THRESHOLD_`, `MALLOC_MMAP_THRESHOLD_` tune glibc; `GLIBC_TUNABLES=glibc.malloc.arena_max=4`.

| Allocator | Notes |
|---|---|
| **glibc malloc** (ptmalloc, from dlmalloc) | Default; bins by size, per-thread arenas; decent, can fragment in long-running multithreaded services |
| **jemalloc** | Multiple arenas, per-thread caches, size classes; scalable and fragmentation-resistant; heap profiling (`MALLOC_CONF=prof:true`); used by Facebook/Meta, Redis, Firefox; often reduces RSS growth in Python/C++ services |
| **tcmalloc** (gperftools / Google tcmalloc) | Per-thread caches, central heap, periodic return of memory; good for many small allocations; heap profiler; `libtcmalloc_minimal.so` |
| **mimalloc** | Compact, fast, good defaults |
| **Kernel: slab/SLUB** | Per-type object caches for kernel structs (`slabtop`); SLUB is the default |

Switch without recompiling with `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2 python train.py` (verify in `/proc/PID/maps`); measure RSS and throughput before and after; the effect can be negative. **Python specifics**: CPython's `pymalloc` allocates 256 KiB arenas from the OS; a single surviving small object keeps an entire arena resident, so deleting a big list and calling `gc.collect()` does not drop RSS to its old value; reference cycles need the cyclic collector; native extension memory (NumPy, PyTorch host tensors) is allocated outside `pymalloc`. Mitigations: recycle worker processes (`maxtasksperchild`), use `jemalloc`, avoid holding giant Python object collections (use NumPy/Arrow/memory-mapped files), `del` plus `torch.cuda.empty_cache()` is for GPU memory only. For data loaders with many workers, `fork` shares pages copy-on-write, but Python reference counting writes to objects and **breaks sharing** (each worker gradually copies the dataset); store datasets in NumPy/Arrow/`mmap`/shared memory instead of Python lists to keep pages shared.

**Leak detection**: confirm monotonic growth of `RssAnon` over long periods under steady load; ask whether it is a cache or pool; use allocator debug/profiling (jemalloc `prof`, tcmalloc heap profiler, `valgrind massif` for small tests), `memleak`/`bpftrace` in production (cost!), Python `tracemalloc`/`memray`, `/proc/PID/smaps` to see which mapping grows (heap vs anonymous mmap vs shared), and `pmap -x` over time. Kernel-side leaks show as growing `Slab`/`SUnreclaim` or `PageTables`.

## 10. Tuning parameters

Defaults are usually sensible; change only against evidence. Representative `vm.*` and `kernel.*` settings (kernel documentation `Documentation/admin-guide/sysctl/vm.rst`):

| Parameter | Default | Meaning and GPU-node practice |
|---|---|---|
| `vm.swappiness` | 60 | Bias to swap anonymous pages over dropping cache. 0 to 10 on GPU/HPC nodes |
| `vm.overcommit_memory` / `vm.overcommit_ratio` | 0 / 50 | Overcommit policy; 2 gives strict accounting (usually not for GPU nodes) |
| `vm.min_free_kbytes` | dynamic | Minimum free pool and base of watermarks. Raise moderately on large-RAM nodes to avoid direct-reclaim stalls (for example hundreds of MB to a few GB; test) |
| `vm.watermark_scale_factor` | 10 | Gap between watermarks (0.1% of RAM per unit); raise to wake kswapd earlier |
| `vm.zone_reclaim_mode` | 0 | Leave 0 |
| `vm.vfs_cache_pressure` | 100 | Dentry/inode reclaim aggressiveness |
| `vm.dirty_ratio`, `vm.dirty_background_ratio` (or `_bytes`) | 20 / 10 | Write-back thresholds; use bytes forms on huge-RAM nodes (chapter 1.12) |
| `vm.max_map_count` | 65530 | Max memory mappings per process; **raise (e.g. 262144 to 1048576)** for frameworks and Elasticsearch/JVM/PyTorch loaders with many mmaps (error: "Cannot allocate memory" in `mmap`) |
| `vm.nr_hugepages` | 0 | Explicit huge pages pool |
| `vm.panic_on_oom` | 0 | 1 reboots on OOM (some HPC sites prefer fast failure) |
| `vm.oom_kill_allocating_task` | 0 | Kill the allocating process instead of scanning for the worst |
| `kernel.numa_balancing` | 1 | Disable when binding explicitly |
| `kernel.pid_max` / `kernel.threads-max` | 32768+ / varies | Raise for dense containers and many threads |
| `vm.compact_unevictable_allowed`, `vm.compaction_proactiveness` | | Compaction behaviour (THP stalls) |

```ini
# /etc/sysctl.d/90-gpu-node-memory.conf   (illustrative; validate on a canary node)
vm.swappiness = 1
vm.max_map_count = 1048576
vm.min_free_kbytes = 4194304        # 4 GiB on a 1+ TiB machine; far too much on small ones
vm.watermark_scale_factor = 100
vm.dirty_background_bytes = 1073741824
vm.dirty_bytes = 4294967296
kernel.numa_balancing = 0
```

Kernel command line (chapter 1.14): `transparent_hugepage=madvise`, `default_hugepagesz=1G hugepagesz=1G hugepages=N`, `numa_balancing=disable`, `crashkernel=`. Limits (chapter 1.8 and section 11): `LimitMEMLOCK=infinity`. `ulimit -v`/`-m`/`-d` exist but are crude; use cgroups.

## 11. Memory in cgroups, containers and GPU workloads

### cgroup v2 memory controller

```bash
cat /sys/fs/cgroup/<path>/memory.max          # hard limit ("max" = none)
cat /sys/fs/cgroup/<path>/memory.high         # throttle/reclaim threshold
cat /sys/fs/cgroup/<path>/memory.low          # protection (best effort); memory.min is a hard protection
cat /sys/fs/cgroup/<path>/memory.current      # current usage (anon + file cache + kernel memory)
cat /sys/fs/cgroup/<path>/memory.stat         # anon, file, kernel, slab, shmem, pgfault, pgmajfault, workingset_*, thp_*
cat /sys/fs/cgroup/<path>/memory.events       # low, high, max, oom, oom_kill (counters)
cat /sys/fs/cgroup/<path>/memory.pressure     # per-cgroup PSI
cat /sys/fs/cgroup/<path>/memory.swap.max / memory.swap.current
echo 1 > /sys/fs/cgroup/<path>/memory.oom.group     # kill the whole group on OOM
```

Key points: **`memory.current` includes page cache** charged to the cgroup; when it nears `memory.max`, the kernel reclaims the cgroup's own cache first, so high usage is not necessarily a problem, but the **working set** (`memory.stat` `anon`, active file) is. A container whose `anon` approaches `memory.max` will be OOM-killed. `memory.high` makes the group slow (throttled and reclaimed) before it is killed: a good soft limit for batch jobs. Kubernetes: `resources.limits.memory` sets `memory.max`; `requests.memory` influences scheduling and `memory.min/low` protection via QoS classes (Guaranteed, Burstable, BestEffort) and OOM score adjustments (BestEffort pods are killed first); `Memory` `emptyDir` (tmpfs) counts toward the pod's memory. Slurm's `--mem`, `--mem-per-cpu`, `--mem-per-gpu` become cgroup limits (`ConstrainRAMSpace`). Under cgroup v1 the equivalents are `memory.limit_in_bytes`, `memory.usage_in_bytes`, `memory.memsw.*`, `memory.oom_control`.

### Pinned (page-locked) memory, `memlock`, and DMA

GPUs and NICs transfer data by **DMA**, which needs physical addresses that do not move. **Pinned (page-locked) memory** is excluded from swapping and migration, so the device can read and write it directly: host-to-device copies from pinned memory are typically 2x to 3x faster than from pageable memory (no staging copy) and allow asynchronous overlap with compute (`cudaMemcpyAsync`; PyTorch `pin_memory=True`, `tensor.pin_memory()`, `non_blocking=True`). GPUDirect RDMA/Storage and InfiniBand verbs also require registered (pinned) memory. Consequences:

- Pinned memory is **limited by `RLIMIT_MEMLOCK`** (`ulimit -l`). Too low a limit makes registrations fail (`ibv_reg_mr` errors, CUDA "out of memory" pinning host memory, NCCL `ibv_reg_mr` failures). Set `memlock` to `unlimited` for HPC/AI users and services (`/etc/security/limits.d/*.conf` for logins, `LimitMEMLOCK=infinity` for systemd units, `--ulimit memlock=-1:-1` for Docker, Slurm `PropagateResourceLimits`, Kubernetes via runtime configuration) (chapters 1.8, 1.15).
- Pinned pages are **unevictable**: they reduce what the kernel can reclaim, count in `Mlocked`/`Unevictable`, and in cgroup accounting; pinning most of RAM invites OOM. Keep staging buffers sized to need and reuse them.
- Pinning cost: allocation is slow (it touches and locks every page); allocate once up front, not per batch.
- Huge pages for pinned buffers reduce the number of mappings and registration cost.
- Unified Virtual Memory (`cudaMallocManaged`) migrates pages between CPU and GPU on demand; oversubscription and thrashing are performance traps (a GPU topic).

### Host memory budget for a training node

Budget per node: operating system and daemons (a few GB) + data-loader workers (per worker: process overhead, decoded batches, prefetch queue x number of workers x GPUs) + pinned staging buffers + framework host allocations (CUDA context host memory, NCCL buffers, NCCL proxy threads) + page cache for the dataset (desired) + headroom for checkpoint staging in tmpfs or page cache + margin. A common mistake is multiplying workers (8 GPUs x 16 workers x 2 GB) and exceeding RAM, or putting checkpoints in `/dev/shm` without a size cap. Monitor `MemAvailable`, PSI, per-cgroup `memory.stat` and OOM counters.

### Swap and memory policy summary

| Node type | Swap | Swappiness | THP | NUMA balancing | Limits |
|---|---|---|---|---|---|
| Training / HPC compute | None or minimal | 0 to 10 | `always` or `madvise` (measure) | off, explicit binding | cgroup `memory.max` per job, `memlock` unlimited |
| Inference / latency-critical | None | 0 to 10 | `madvise` or `never`, `defrag=defer` | off, bind | Per-service limits, `memory.high` as early warning |
| Login / shared nodes | Small swap, maybe zram | 10 to 60 | default | default | **Per-user slice `MemoryMax`** (chapter 1.15) |
| Kubernetes workers | Usually off (kubelet requires special setting for swap) | low | per workload | per policy | `systemReserved`/`kubeReserved`, QoS classes, eviction thresholds |

## How it fails

1. **Exit code 137 / "Killed".** OOM kill. `dmesg -T | grep -i -E 'oom|killed process'`, `memory.events oom_kill`. Decide whether it was a cgroup OOM (limit too low or leak) or a global one.
2. **"Free memory is 0" panic.** Misreading `free`. Look at `available` and PSI.
3. **System slow, high load, `kswapd` busy or `sys` time high.** Memory pressure, direct reclaim, THP compaction. PSI, `sar -B`, `/proc/vmstat`.
4. **Swapping a GPU job.** Swap enabled with default swappiness; lower it or disable swap; find the oversized consumer.
5. **Cross-socket slowdown.** Loader on the wrong NUMA node; `numastat -p`, bind with `numactl`; compare `nvidia-smi topo -m`.
6. **THP stalls** (periodic latency spikes). `compact_stall`/`thp_*` counters; set `madvise`, `defrag=defer`.
7. **Hugepages unavailable** at runtime (`nr_hugepages` lower than requested): fragmentation; reserve at boot.
8. **`ibv_reg_mr` / pinned allocation fails.** `memlock` limit; `ulimit -l`, unit limits, container ulimits.
9. **"Cannot allocate memory" with free RAM.** `vm.max_map_count` exhausted, `overcommit_memory=2` limit, address-space limit (`ulimit -v`), cgroup limit, NUMA bind to a full node, or `fork` of a large process under strict overcommit.
10. **RSS never shrinks after freeing.** Allocator behaviour, Python arenas; not necessarily a leak. Recycle workers, change allocator.
11. **Dataloader workers each hold a full copy** (copy-on-write broken by refcounts). Use shared/mmap formats.
12. **`/dev/shm` or tmpfs fills memory.** Size limits; remember Memory `emptyDir`.
13. **Kernel slab leak** (`SUnreclaim` grows). Driver/kernel bug; reboot window; report with `slabtop` evidence.
14. **ECC errors accumulate then the node crashes.** Watch EDAC counters, replace DIMMs proactively.
15. **Kubernetes pod OOMKilled below node capacity.** Limit set too low or page cache counted; look at `memory.stat` working set; set `requests` = `limits` for Guaranteed QoS on training pods.
16. **OOM killer picks `sshd`/`kubelet`.** Missing `OOMScoreAdjust`; slices without protection.

## Hands-on lab (an Ubuntu VM; untested)

Use a throwaway VM with at least 4 GiB RAM and `sudo`. These commands have **not** been run; run them before relying on them. Do not run the memory-exhaustion steps on a shared or production machine.

**A. Read memory.**

```bash
free -h; grep -E 'MemAvailable|Cached|AnonPages|Slab|SReclaimable|SUnreclaim|PageTables|Mlocked|Huge|Committed_AS|CommitLimit' /proc/meminfo
vmstat 1 3; cat /proc/pressure/memory; sar -B 1 3 2>/dev/null
ps -eo pid,rss,vsz,comm --sort=-rss | head -5
cat /proc/$$/smaps_rollup; pmap -x $$ | tail -5
sudo slabtop -o -s c | head -10
```

**B. Demand paging.**

```bash
python3 - <<'EOF'
import mmap, os, time, resource
n = 1<<30
m = mmap.mmap(-1, n)        # 1 GiB anonymous, untouched
def rss(): return int(open('/proc/self/statm').read().split()[1]) * 4096 // (1<<20)
print("after mmap: RSS MiB", rss(), "minflt", resource.getrusage(resource.RUSAGE_SELF).ru_minflt)
for i in range(0, n, 4096): m[i] = 1
print("after touch: RSS MiB", rss(), "minflt", resource.getrusage(resource.RUSAGE_SELF).ru_minflt)
EOF
```

**C. Page cache and `available`.**

```bash
free -h; dd if=/dev/zero of=/tmp/big bs=1M count=2048 status=none; sync
free -h        # buff/cache grew, available barely changed
echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null; free -h
rm /tmp/big
```

**D. cgroup memory limit and OOM.**

```bash
sudo systemd-run --scope -p MemoryMax=300M -p MemorySwapMax=0 --unit=oomlab python3 -c 'x=[bytearray(10*1024*1024) for _ in range(100)]'; echo "exit $?"
sudo dmesg -T | tail -15 | grep -iE 'oom|killed'
sudo systemd-run --scope -p MemoryHigh=200M -p MemoryMax=600M --unit=highlab python3 -c '
import time
x=[bytearray(10*1024*1024) for _ in range(40)]
time.sleep(5)'
# inspect while running in another shell:  systemctl show highlab.scope -p MemoryCurrent; cat /sys/fs/cgroup/system.slice/highlab.scope/memory.events
```

**E. oom_score_adj.**

```bash
sleep 600 & P=$!; cat /proc/$P/oom_score /proc/$P/oom_score_adj
echo 500 | sudo tee /proc/$P/oom_score_adj; cat /proc/$P/oom_score; sudo kill $P
```

**F. NUMA (on a multi-node machine, or `numactl --hardware` on any).**

```bash
sudo apt install -y numactl hwloc
numactl --hardware; numastat; lscpu | grep -i numa
numactl --cpunodebind=0 --membind=0 python3 -c 'import os; print(open("/proc/self/numa_maps").read()[:400])'
numastat -p $$
```

**G. Huge pages and THP.**

```bash
cat /sys/kernel/mm/transparent_hugepage/{enabled,defrag}; grep -E 'AnonHugePages|HugePages_|Hugepagesize' /proc/meminfo
echo 128 | sudo tee /proc/sys/vm/nr_hugepages; grep HugePages_ /proc/meminfo; echo 0 | sudo tee /proc/sys/vm/nr_hugepages
sudo sh -c 'echo always > /sys/kernel/mm/transparent_hugepage/enabled'
python3 -c 'import mmap,time; m=mmap.mmap(-1,512<<20); [m.__setitem__(i,1) for i in range(0,512<<20,4096)]; print(open("/proc/self/smaps_rollup").read().split("AnonHugePages:")[1].split()[0],"kB in THP"); time.sleep(1)'
sudo sh -c 'echo madvise > /sys/kernel/mm/transparent_hugepage/enabled'
grep -E 'thp_fault_alloc|thp_collapse_alloc|compact_stall' /proc/vmstat
```

**H. Allocator behaviour.**

```bash
cat > /tmp/alloc.py <<'EOF'
import os
def rss(): return int(open('/proc/self/statm').read().split()[1])*4096//(1<<20)
d=[str(i)*1000 for i in range(1000000)]; print("allocated", rss())
del d; print("after del", rss())
import gc; gc.collect(); print("after gc", rss())
EOF
python3 /tmp/alloc.py
sudo apt install -y libjemalloc2; LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2 python3 /tmp/alloc.py
MALLOC_ARENA_MAX=1 python3 /tmp/alloc.py
```

**I. memlock.**

```bash
ulimit -l; ulimit -Sl 64; python3 -c 'import mmap,ctypes; libc=ctypes.CDLL("libc.so.6",use_errno=True); b=ctypes.create_string_buffer(1<<20); print(libc.mlock(b,ctypes.c_size_t(1<<20)), ctypes.get_errno())'
```

**J. (GPU VM, optional) pinned versus pageable.**

```bash
python3 - <<'EOF'
import torch,time
x=torch.empty(1<<28,dtype=torch.uint8); y=torch.empty(1<<28,dtype=torch.uint8).pin_memory()
for name,t in (("pageable",x),("pinned",y)):
    torch.cuda.synchronize(); s=time.time()
    for _ in range(5): t.cuda(non_blocking=True)
    torch.cuda.synchronize(); print(name, 5*(1<<28)/(time.time()-s)/1e9, "GB/s")
EOF
```

## Checkpoint questions

1. What does virtual memory provide and what is the cost? Describe the translation path including the TLB.
2. Define RSS, VSZ, PSS and USS. Why is summing RSS misleading?
3. What is demand paging? What are minor and major page faults, with examples?
4. What is overcommit and what are the three `vm.overcommit_memory` modes?
5. What is the difference between "free", "available" and "buff/cache" in `free`?
6. How does Linux free memory as pressure rises? What do kswapd and direct reclaim do, and why do stalls appear?
7. What do `vm.swappiness`, `vm.min_free_kbytes` and `vm.watermark_scale_factor` change?
8. Why is swap often disabled on GPU nodes? What is the downside of no swap?
9. How does the OOM killer choose a victim? What are `oom_score` and `oom_score_adj` and how do you protect `sshd`?
10. How is a cgroup OOM different from a global OOM? What evidence tells you which occurred?
11. What does exit code 137 mean? What would you check first?
12. What is NUMA? Local versus remote memory? How do you view topology and which GPU belongs to which node?
13. What is first-touch placement and why does it hurt GPU feeding?
14. Write a command that runs a training process on NUMA node 1's CPUs and memory. What happens to the memory policy in spawned workers?
15. What do `numa_hit`, `numa_miss` and `other_node` indicate?
16. Why is automatic NUMA balancing often disabled on AI nodes?
17. What are huge pages and why do they help? Explicit versus transparent: differences?
18. Recommend THP settings for training nodes versus latency-sensitive inference, and name two risks of THP.
19. Why does RSS stay high after freeing memory? Name three ways to reduce it.
20. Compare glibc malloc, jemalloc and tcmalloc. How do you switch without recompiling and verify it?
21. Why do forked DataLoader workers still copy a Python list dataset?
22. How do you tell a memory leak from memory growth? Name three tools.
23. What is PSI and how do you read `some` and `full`?
24. What do `memory.high`, `memory.max`, `memory.low` and `memory.events` mean?
25. Why does a container's `memory.current` include page cache and should that alarm you?
26. What is pinned memory, why is it faster, what limits it, and what happens with a low `memlock`?
27. A node with 1 TiB RAM shows periodic multi-second stalls. List three memory-related causes and a check for each.
28. Which `/proc/meminfo` fields would you check for a suspected kernel memory leak?
29. What does `vm.max_map_count` limit and when must it be raised?
30. Draw up a host-memory budget for an 8-GPU node and say which numbers you would measure.

### Answers

1. Private, large, linear address spaces; isolation, oversubscription, sharing, mmap. Cost: address translation. The MMU translates via page tables (4 to 5 levels) cached in the TLB; a miss triggers a page walk; no mapping triggers a page fault.
2. RSS: pages in RAM; VSZ: all allocated address space; PSS: private plus shared divided by users; USS: private only. Shared pages are counted in every mapping process's RSS, so sums overcount.
3. Physical pages are assigned on first touch. Minor: no I/O (zero page, mapping a cached/shared page); major: requires disk I/O (uncached file page or swapped-out page).
4. Granting more virtual memory than RAM+swap. 0 heuristic, 1 always allow, 2 strict limit by ratio.
5. free: unused; available: estimate of memory obtainable without swapping (includes reclaimable cache); buff/cache: file cache and buffers, mostly reclaimable.
6. Free lists, then kswapd background reclaim (page cache, swap, slab) below the low watermark, direct reclaim in the allocating thread below min, finally the OOM killer. Direct reclaim and compaction stall the thread.
7. Swappiness: bias toward swapping vs dropping cache; min_free_kbytes: size of the reserve and base of watermarks; watermark_scale_factor: gap between watermarks (earlier kswapd wake-up).
8. Swapped pages cause huge slowdowns and stalls of collective ops; fail fast instead. Downside: no grace period, OOM kills happen immediately; need limits and monitoring.
9. By badness score (proportional to memory use) plus `oom_score_adj` (-1000 immune to +1000 first). `echo -1000 > /proc/PID/oom_score_adj` or `OOMScoreAdjust=-900/-1000` in the unit.
10. cgroup OOM: the group exceeded `memory.max`, killing within it; host has free memory. Evidence: `memory.events oom_kill`, `constraint=CONSTRAINT_MEMCG` and cgroup path in dmesg; global shows system-wide exhaustion.
11. Killed by SIGKILL (128+9), typically the OOM killer. Check dmesg, cgroup `memory.events`, container limits.
12. Memory attached per CPU socket/node with remote access slower. `numactl -H`, `lscpu`, `lstopo`, `nvidia-smi topo -m`, `/sys/bus/pci/devices/*/numa_node`.
13. A page is allocated on the node of the CPU that first touches it; if the loader initialises buffers on node 0 but the GPU is on node 1, every copy crosses the interconnect.
14. `numactl --cpunodebind=1 --membind=1 python train.py`. Policy is inherited by `fork`ed children; `exec`/spawn'd processes do not inherit and must be re-bound.
15. Hit: allocated on the intended node; miss: allocated here though another node was intended; other_node: process on one node touching memory of another; rising values mean remote placement.
16. Its scanning and migrations add overhead and jitter, and explicit binding is better than its heuristics for GPU feeding.
17. Larger pages (2 MiB/1 GiB) reduce page-table size and TLB misses. Explicit: reserved pool, not swappable, application opts in; transparent: automatic promotion/demotion, may stall on compaction or bloat memory.
18. Training: `always` or `madvise` (measure); inference: `madvise`/`never` with `defrag=defer`. Risks: compaction latency spikes and memory bloat.
19. Allocators keep freed memory (arenas, fragmentation, Python pymalloc arenas). Recycle workers, use jemalloc/tcmalloc or tuning (`MALLOC_ARENA_MAX`, trim), use mmap-based storage.
20. glibc: default, arenas; jemalloc: scalable, low fragmentation, profiling; tcmalloc: thread caches. `LD_PRELOAD=libjemalloc.so.2 cmd` and check `/proc/PID/maps`.
21. Python refcount updates write to object headers, triggering copy-on-write of pages; use NumPy/Arrow/mmap data.
22. Leak: memory never freed; growth: expected increase (cache, warm-up). Tools: RSS time series (`pidstat -r`, `smem`), `memleak`/`bpftrace`, jemalloc/tcmalloc profiling, `tracemalloc`/`memray`, `smaps`.
23. Pressure stall information: `some` = time at least one task stalled for memory, `full` = all tasks stalled; averages over 10/60/300 s; sustained values mean saturation.
24. `high` soft limit with throttling/reclaim, `max` hard limit with OOM, `low` best-effort protection, `events` counters of high/max/oom/oom_kill occurrences.
25. The cgroup is charged for its page cache; the kernel reclaims it when near the limit, so high `current` is normal; watch anonymous/working-set memory and events.
26. Page-locked memory that cannot be swapped/moved so devices can DMA; avoids a staging copy and permits async overlap; limited by `RLIMIT_MEMLOCK` and physical RAM; low `memlock` makes registrations fail.
27. Direct reclaim (`pgscand`, `allocstall`, PSI), THP compaction (`compact_stall`, `thp_*`), NUMA balancing/writeback stalls (`numa_pages_migrated`, dirty/writeback in `/proc/meminfo`); check `sar -B`, `/proc/vmstat`, PSI, perf.
28. `Slab`, `SUnreclaim`, `PageTables`, `KernelStack`, `VmallocUsed`, `Unevictable`; `slabtop`.
29. The number of memory mappings per process; raise for programs with many mmaps (PyTorch loaders, Elasticsearch, JVM) when `mmap` fails with ENOMEM.
30. OS and daemons, loader workers x GPUs x per-worker memory, pinned buffers, framework host allocations, NCCL buffers, page cache for datasets, tmpfs/checkpoint staging, margin; measure `RssAnon` per process, `MemAvailable`, PSI, cgroup `memory.stat`, NUMA distribution.

## Sources and further reading

- Brendan Gregg, *Systems Performance*, 2nd ed.: ch. 7 (memory: terminology; virtual memory, paging, demand paging, overcommit, process swapping, file-system cache usage, utilisation and saturation, allocators, shared memory, working set size, word size; hardware: main memory, DDR, multichannel, CPU caches, MMU, multiple page sizes, TLB; software: freeing memory, free lists, reaping, page scanning, process address space and heap growth, allocators slab, SLUB, glibc, TCMalloc, jemalloc; methodology: tools method, USE, characterising usage, cycle analysis, monitoring, leak detection, static tuning, resource controls, micro-benchmarking, memory shrinking; observability tools: `vmstat`, PSI, `swapon`, `sar`, `slabtop`, `numastat`, `ps`, `top`, `pmap`, `perf`, `drsnoop`, `wss`, `bpftrace`; tuning: tunable parameters, multiple page sizes, allocators, NUMA binding, resource controls). Sections 2 to 6 and 9 to 10 condense this chapter in original wording; the book's figures, tables of DDR bandwidths and TLB sizes, and tool outputs are not reproduced.
- nvidia-devops (the user's earlier notes): `volume-01/01-linux-compute-memory-masterclass.md` (the NUMA GPU trap, page tables and TLB walk, page cache and reclaim watermarks, swappiness, NUMA policies and `numactl`, OOM score mechanics, the `mmap` and Python allocator examples, `numastat`, sysctl guide). Reused with edits in sections 2, 4, 5, 7 and 10 (partial: CPU scheduling and CFS/EEVDF migrate to chapter 1.18; the `perf` scenarios to 1.24).
- Manual pages and kernel documents: `proc(5)` (`meminfo`, `smaps`, `oom_score_adj`, `vmstat`), `free(1)`, `vmstat(8)`, `numactl(8)`, `numastat(8)`, `numa(7)`, `mbind(2)`, `mmap(2)`, `madvise(2)`, `mlock(2)`, `malloc(3)`, `mallopt(3)`, `sysctl(8)`; kernel `Documentation/admin-guide/sysctl/vm.rst`, `admin-guide/mm/transhuge.rst`, `admin-guide/mm/hugetlbpage.rst`, `admin-guide/cgroup-v2.rst`, `accounting/psi.rst`; `systemd.resource-control(5)`, `systemd-oomd(8)`.
- Related chapters: 1.8 (page faults, `vmstat`, limits, cgroup basics), 1.11 (address space layout, allocators in practice), 1.12 (page cache, write-back), 1.14 (kernel parameters for huge pages and NUMA), 1.15 (slices, `MemoryMax`, `OOMScoreAdjust`), 1.18 (CPU scheduling and cgroups), 1.22 (kernel tuning), 1.24 (BPF memory tools), 1.28 (node tuning), Kubernetes and Slurm chapters (memory limits, Topology Manager, `--mem`, `--gpu-bind`), NCCL and RDMA chapters (memlock, registration).

*Notes for review:* defaults (swappiness range, watermark factors, THP defaults, `oom_score` details, `vm.max_map_count`), the cgroup file names and the behaviour of Kubernetes QoS and OOM scoring depend on kernel and distribution versions; the numerical tuning values and the pinned-memory speed-up factors are illustrative and must be measured. NUMA binding commands must be derived from the actual topology; the Grace-system NUMA description should be checked against NVIDIA's platform documentation. All lab commands are **untested**; run them on a disposable VM before this chapter moves to `reviewed`.
