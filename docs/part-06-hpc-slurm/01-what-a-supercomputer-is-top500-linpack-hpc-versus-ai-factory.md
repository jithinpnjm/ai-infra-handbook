---
id: "c06-01"
title: "6.1 What a supercomputer is: TOP500, Linpack, HPC versus AI factory."
sidebar_label: "6.1 What a supercomputer is: TOP500, Linpack, HPC versus AI factory"
sidebar_position: 1
description: "What makes a computer super: parallelism, FLOPS and precision, Rpeak versus Rmax, the TOP500, HPL, HPCG and Green500 lists, how traditional HPC differs from an AI factory, cluster types, and what the word means to the administrator."
status: "drafted"
tier: "2"
level: "B"
lab_venue: "GCP / GKE."
---

# 6.1 What a supercomputer is: TOP500, Linpack, HPC versus AI factory

| Field | Value |
|---|---|
| Level | Beginner |
| Priority tier | 1 |
| Lab venue | Any machine with Python 3; `flops_lab.py` runs 3 checks locally and cluster CLI commands are **untested** here |
| Part | Part 6: HPC and Slurm |
| Status | Drafted |

## Why this matters for AI infrastructure

Walk onto the data center floor where a large language model is training, and you are standing inside a supercomputer. Thousands of GPUs hum inside liquid-cooled racks, linked by a dedicated InfiniBand or RoCE fabric. Those accelerators read training shards from a parallel file system, and they take orders from a central batch scheduler. Almost every tool and habit that keeps such a cluster productive comes straight from high-performance computing. Slurm queues, collective communications, environment modules, pre-job health checks, node draining, and fair-share accounting were forged over decades by HPC engineers. Understanding what traditional HPC measures, and why a supercomputer is a single synchronized complex, lets you diagnose cluster-wide slowdowns. It also lets you speak with authority in production war rooms.

## Prerequisites and outcomes

You need Part 1 for Linux administration and Part 2 for networking basics. When you finish this chapter, you will be able to define a supercomputer from the operator's point of view. It is a single synchronized complex, not a price tag or a list rank. You will explain hardware parallelism, vector pipelining, the cycle formula `K*(N-1)+S`, and the nine hardware and software parallelism levels across a cluster. You will compute theoretical peak performance from hardware clocks and instruction width, and you will explain why achieved benchmark performance is always lower.

You will also explain what the TOP500, HPL, HPCG, HPL-MxP, Green500, Graph500, IO500, and MLPerf benchmarks measure, and what each one misses. You will compare a traditional HPC center with an AI factory across workloads, numerical precision, network topologies, storage bursts, scheduling, and power density. You will tell high-availability, high-productivity, and high-performance clusters apart. You will also tell custom vendor supercomputers apart from commodity clusters and Beowulf farms. Finally, you will describe the physical and operational realities of running a supercomputer at 80 to 100 percent continuous utilization, including power-on surges and command-line fleet management.

## 1. What "super" means: from marketing ranks to a single synchronized complex

Suppose you have just inherited a hundred Linux servers racked in a cold room. In an ordinary corporate office, nobody panics if one server loses half its memory or a network switch fails. You can swap in a cheap spare switch, or let employees print their reports on the second floor for a few days while you wait for parts. The same casual swap on a compute cluster causes real damage. Replace a broken InfiniBand switch with Gigabit Ethernet, or replace an 8 GB compute node with a 4 GB node, and every multi-node job that spans that rack slows to a crawl. Users flood your ticket queue, because a tightly coupled parallel job runs at the speed of its slowest participant.

There is no formal standards-body definition of a supercomputer. Engineers rely on three working definitions, and the one they use depends on their role:

1. By rank or cost: a machine near the top of a published list, or one that costs tens or hundreds of millions of dollars. That headline number interests executives, but it tells you nothing about how to operate the machine.
2. By capability: a system whose total performance is far beyond what any single server can deliver. It gets there by running one parallel program across many processors that exchange data rapidly.
3. By operational shape: a shared, expensive, tightly integrated complex, where overall synchronization, fabric health, storage throughput, and software consistency decide whether useful work comes out.

In *Supercomputers for Linux SysAdmins*, Sergey Zhumatiy captures this third view directly. A supercomputer is not just a huge pile of expensive hardware, servers, switches, and disks. It is a single complex construction, in idea and in essence. All of its components are closely connected. Your most important task as an administrator is to understand those connections and keep them working together. Because the complex often works together on one huge task, even a slight imbalance in one component can significantly drop the performance of the whole system.

Three technical properties appear in every real supercomputer:

- Scale-out parallelism: performance comes from many cores, many nodes, and many accelerators working together on one problem, rather than from a single fast core.
- Fast, low-latency interconnect: processors must exchange messages with microsecond latency and high bandwidth. That separates a supercomputer from a loose farm of independent servers.
- Shared infrastructure: a parallel file system, a central batch scheduler, a uniform software stack, and a centralized management plane coordinate the entire fleet.

### Parallelism, pipelining, and the nine levels of cluster parallelism

Every modern supercomputer achieves speed through parallel data processing. Since the beginning of the computer era, parallel processing has remained the primary way to reach high performance. Your desktop uses the same idea. Simultaneous multithreading, such as Intel HyperThreading or AMD SMT, lets two or more program threads run at the same time. Cell phones and cameras are parallel and multicore, too. The rule underneath is simple. When operations are independent, so that neither result changes the other's input data, hardware can execute them at the same time.

Inside a processor, this principle takes two classic forms. The first is parallelism proper. Separate hardware devices execute different machine instructions at the same time. If the variables `a`, `b`, and `c` sit in internal processor memory, the commands `x=a+b` and `y=b*c` can run independently. That requires separate addition and multiplication devices. GPUs apply the same principle across hundreds or thousands of small cores that execute the same code in parallel.

The second form is pipelining. A single command is divided into sequential stages, and each stage is handled quickly by its own hardware element, like stations on an assembly line. Several commands sit at different stages of the line at once. Vectorization relies on this idea most often. It runs a single operation across regularly arranged data arrays called vectors, as in AVX vector processor operations.

Consider adding two vectors whose elements sit one after another in memory. Every element gets the same operation, so the hardware can split floating-point addition into stages: loading elements from memory, normalization of mantissas, addition, correction, and writing back to memory. Once the first stage finishes on the first element, it can start on the second element right away. It does not wait for the whole operation to finish on the first element.

Suppose the slowest stage of that conveyor takes `K` clock cycles, and all stages together take `S` clock cycles. Processing a vector of `N` elements requires this many clock cycles:

```text
Total cycles = K * (N - 1) + S
```

The first element finishes after the full `S` cycles. That initial wait is called the pipeline acceleration time. After that fill, the device produces one result every `K` clock cycles, and in modern processors `K` is most often `1`. Take the five-stage example, where `S = 5` and `K = 1`. Processing 100 elements takes 104 cycles instead of 500. The arithmetic is `1 × (100 - 1) + 5`, which gives `104`. Pipelining and vectorization are not the same thing. Vectorization does not need pipelining, and pipelining does not need vectors. A pipelined scalar addition unit can serve a run of ordinary additions just as well.

Hardware parallelism also reaches past the cores, into memory and I/O. Memory banks on a motherboard are independent channels, not just physical slots, so they can work at the same time. Suppose your board has four memory banks. Filling four slots with 8 GB each, one module per bank, works better than a single 32 GB module in one slot. While the first bank takes in data, the memory controller can already start writing the next block into the second bank. Devices use the same idea through direct memory access and offloading. The processor builds a block in memory in advance, then tells the disk or network controller to write or send it. The processor is then free to do other work while the controller moves the data.

Does a parallel program run faster just because it is parallel? Not necessarily. It can run even slower. Parts of the code that should run in parallel may conflict with each other. Two threads might touch different memory sections and stop the processor cache from working efficiently. Or parallel processes might spend most of their time waiting for data from the slowest process. Finding the real cause of poor scaling is hard. It takes performance debuggers, such as parallel profilers, tracers, and compute node monitoring. An administrator should know all nine levels of hardware and software parallelism in a cluster. They form your checklist when a job runs slowly:

1. `[HW]` multiple memory banks operating independently across channels.
2. `[HW]` multiline CPU cache hierarchies.
3. `[HW]` multiple CPUs on a motherboard.
4. `[HW]` multiple CPU cores inside one processor chip.
5. `[HW]` multiple functional execution devices inside one CPU core.
6. `[HW]` accelerators, such as GPUs and FPGAs.
7. `[HW]` network devices with DMA and protocol offloading features.
8. `[SW]` multiple UNIX processes and threads on one server, such as OpenMP threads in one process.
9. `[SW]` multiple servers running one parallel program across nodes using MPI for message passing, plus CUDA or OpenACC on accelerators.

When a parallel program runs slowly, even though the installed MPI environment works without errors, work through this hierarchy from top to bottom. A classic root cause is a configuration error that sends MPI messages over the slow Ethernet management network instead of the fast InfiniBand fabric.

**Treat a supercomputer as one synchronized machine where every memory bank, core, accelerator, and network link is balanced.** Always verify which network fabric a slow parallel job is actually using.

> **In one minute:**
> - For an administrator, "super" means overall synchronization across a tightly coupled complex of servers, storage, and fabric, not a price tag.
> - Hardware accelerates independent work through parallel functional units and assembly-line pipelines (`K*(N-1)+S` clock cycles), backed by multi-bank RAM and DMA offload.
> - Parallel programs can run slower than sequential ones if threads thrash CPU caches, wait on stragglers, or accidentally route MPI messages over slow management Ethernet across the nine levels of cluster parallelism.

## 2. Measuring speed: FLOPS, precision, peak and achieved

Picture an executive briefing for a new GPU cluster. Someone announces that the system delivers "an exaflop of compute." If you accept that number without a follow-up question, you can miscalculate job runtimes and capacity plans by more than an order of magnitude. An exaflop in 64-bit scientific simulation and an "AI exaflop" in 8-bit or 16-bit tensor arithmetic measure completely different hardware units.

FLOPS stands for floating-point operations per second. Metric prefixes scale that count. Giga means 10^9, tera means 10^12, peta means 10^15, and exa means 10^18. Modern processors and GPUs pack far more low-precision arithmetic units onto the silicon than double-precision units. So every FLOPS rating must come with its numerical precision. The table pairs each precision with the work it usually serves.

| Precision | Typical workload | Hardware execution notes |
|---|---|---|
| `FP64` (double) | Traditional physics simulation and the TOP500 Linpack benchmark | Highest silicon cost per operation; many AI-focused GPUs execute `FP64` at a small fraction of their tensor rate |
| `FP32` (single) | Graphics, CAD, legacy simulation, and older ML models | Standard single-precision baseline |
| `TF32`, `BF16`, `FP16` | Mixed-precision deep-learning training and fine-tuning | Matrix Tensor Core paths deliver an order of magnitude more throughput than scalar `FP64` |
| `FP8`, `FP4` | Frontier LLM training and high-throughput inference | Highest floating-point rates; accuracy is maintained via per-block scaling factors in Parts 10 and 15 |
| `INT8`, `INT4` | Quantized model inference | Integer matrix pipelines |

Notice the trade-off in the table. FP64 has the highest silicon cost per operation, while FP8 and FP4 have the highest floating-point rates.

Whenever someone quotes a cluster FLOPS figure, ask three questions right away. At what precision is it? Is it dense or sparse? Is it a theoretical peak, Rpeak, or a benchmark result that was actually achieved, Rmax?

Rpeak is the theoretical ceiling. It is the rate a cluster would reach if every arithmetic unit on every chip completed a full instruction on every clock cycle, with zero stalls. For a CPU cluster, you get Rpeak by multiplying the hardware counts together:

```text
Rpeak (GFLOP/s) = nodes * sockets * cores * GHz * FP64 FLOPs per cycle per core
```

For an accelerator cluster, multiply the total number of GPUs by the vendor's per-GPU peak for the precision you chose. Rmax is different. It is the highest sustained performance measured while running the High-Performance Linpack benchmark. The ratio Rmax / Rpeak is the cluster's HPL efficiency. Achieved performance always falls below theoretical peak, because real programs spend time waiting on memory bandwidth, network communication latency, load imbalance across nodes, clock throttling under power or thermal caps, and system software overhead. Well-tuned HPL runs on GPU clusters often reach well over half of Rpeak. A misconfigured fabric, or a single thermally throttled node, pulls Rmax down sharply.

### A calculator you can run

Running `code/part06/flops.py` shows how precision and efficiency change cluster numbers. The core is two small functions and one example:

```python
def rpeak_cpu(nodes, sockets, cores, ghz, flops_per_cycle):
    """GFLOP/s peak = nodes * sockets * cores * GHz * FLOPs/cycle/core."""
    return nodes * sockets * cores * ghz * flops_per_cycle

def gpu_cluster_peak_pflops(nodes, gpus_per_node, tflops_per_gpu):
    return nodes * gpus_per_node * tflops_per_gpu / 1000.0

g = rpeak_cpu(nodes=100, sockets=2, cores=64, ghz=2.4, flops_per_cycle=32)
print(f"CPU cluster Rpeak: {g/1000:.1f} TFLOP/s")
```

Run `python3 code/part06/flops.py`, and the script evaluates a 100-node dual-socket CPU example. That example uses 32 FLOPs per cycle, which comes from dual AVX-512 FMA units. It also models an illustrative 800-GPU cluster, with round placeholder rates of 60 TFLOP/s in FP64 and 1000 TFLOP/s in dense BF16. The output looks like this:

```text
CPU cluster Rpeak: 983.0 TFLOP/s (or 491.5 TFLOP/s at 16 FLOPs/cycle)
GPU cluster Rpeak: 48.0 PFLOP/s
HPL efficiency if Rmax=38 PF: 79%
AI peak (BF16 dense, illustrative): 800 PFLOP/s; at 40% MFU: 320 PFLOP/s
Vector pipeline N=1000: 1004 cycles vs 5000 unpipelined (4.98x)
```

Read the output as a spread, not a single answer. The same 800-GPU cluster has a theoretical peak of 48.0 PFLOP/s in FP64, but 800 PFLOP/s in illustrative dense BF16. Its sustained output changes again once you apply achieved efficiency. For the AI case, 800 PFLOP/s at 40% MFU gives 320 PFLOP/s, because 800 × 0.40 = 320.

In AI work, the practical counterpart to HPL efficiency is MFU, which stands for model FLOPs utilization. MFU measures the fraction of peak accelerator FLOPs that goes into useful forward and backward model math. Time spent waiting on NCCL collectives, kernel launch gaps, or dataloader stalls does not count toward it. Large distributed training jobs routinely land around 35% to 50% MFU. A gain of five points matters, because lifting MFU by even five percentage points saves millions of dollars in GPU time.

**Never accept a FLOPS figure without its precision, its sparsity mode, and its efficiency ratio.**

> **In one minute:**
> - Always qualify FLOPS with precision, sparsity, and whether the figure is theoretical peak or sustained achieved performance.
> - CPU Rpeak equals `nodes * sockets * cores * GHz * FLOPs/cycle/core`. Halving the vector width from 32 to 16 FLOPs per cycle cuts a 100-node cluster from 983.0 to 491.5 TFLOP/s.
> - HPL efficiency and AI MFU show how much hardware capability survives memory, network, and thermal bottlenecks.

## 3. The lists and benchmarks

Picture a newly built cluster being handed over from the hardware integrator to your operations team. How do you prove that all thousand nodes, cables, power supplies, and cooling loops actually work together under full load? Running `nvidia-smi` on each node only proves that the GPUs powered on. So the community relies on standardized benchmark suites. They rank the world's largest machines and burn in new clusters before users arrive.

Each benchmark measures one thing well and leaves other things out. The table lists both sides for each one.

| Benchmark / list | What it measures | What it leaves out |
|---|---|---|
| **TOP500** (published twice a year in June at ISC and November at SC) | Ranks the 500 fastest known systems by achieved `Rmax` on HPL in `FP64` | Everything except dense linear algebra; low-precision AI speeds, storage I/O, and real multi-job application mixes |
| **HPL** (High-Performance Linpack) | Solves a large dense linear system `Ax = b` using LU factorization in `FP64`; stresses compute units, power, cooling, and regular collective communication | Memory-bandwidth-bound sparse kernels, irregular graph communication, and file system I/O |
| **HPCG** (High Performance Conjugate Gradients) | Solves a sparse linear system dominated by irregular memory access, pointer chasing, and global reductions; typically achieves only a few percent of `Rpeak` | Still a single synthetic mathematical kernel, though much closer to real PDE simulation codes than HPL |
| **HPL-MxP** | Solves the Linpack problem using mixed-precision tensor arithmetic with `FP64` iterative refinement | Pure low-precision inference or transformer attention patterns |
| **Green500** | Re-ranks the TOP500 systems by energy efficiency in GFLOP/s per watt | Facility overhead outside the compute racks and idle power draw |
| **Graph500** | Measures data-intensive graph traversal in traversed edges per second | Dense matrix compute |
| **IO500** | Ranks parallel storage systems using standardized `IOR` bandwidth and `mdtest` metadata benchmarks in Chapter 6.28 | Compute and accelerator performance |
| **MLPerf Training & Inference** (MLCommons) | Measures wall-clock time to train reference AI models to a target accuracy, or inference throughput and latency under strict quality constraints | Customer-specific data pipelines; vendor submissions use heavily tuned software stacks |

Read the last column as carefully as the first. A high score on one benchmark says nothing about the areas it leaves out.

For an infrastructure engineer, these benchmarks are acceptance tests and diagnostic hammers, not crystal balls. HPL pushes every GPU and CPU to maximum power draw while the fabric carries data between them. If a cluster falls short of its expected HPL efficiency, the cause is almost always a degraded optical transceiver, a misconfigured routing table, a throttling cooling loop, or a sick node. Chapter 6.28 walks through running HPL, HPCG, IOR, OSU, and NCCL tests during cluster acceptance.

Keep three caveats in mind when you quote public rankings in an interview:

1. Many massive AI clusters never submit. Hyperscalers and AI labs often skip TOP500 submissions, for competitive reasons, or because stopping a large GPU training cluster for days of FP64 Linpack tuning costs too much money.
2. TOP500 rewards FP64 double-precision arithmetic. Modern AI factory architectures deliberately devote silicon area to low-precision Tensor Cores instead of maximizing FP64.
3. Exascale has a strict meaning: 10^18 sustained FP64 operations per second on HPL. Publicly ranked systems first passed that milestone in the early 2020s. Always check the current June or November lists at `top500.org` and `mlcommons.org` before you quote a specific rank.

**Use HPL, HPCG, IO500, and MLPerf as burn-in acceptance tests, so that fabric, thermal, and storage flaws show up before you hand a cluster to users.**

> **In one minute:**
> - TOP500 ranks systems twice a year, in June and November, by FP64 Rmax on dense HPL. HPCG tests memory-bandwidth-bound sparse math and typically reaches only a few percent of Rpeak.
> - HPL-MxP and MLPerf evaluate mixed-precision and end-to-end AI workloads. Green500 measures GFLOP/s per watt, and IO500 measures parallel storage.
> - Treat standard benchmarks as acceptance and burn-in tests for your hardware, not as direct predictors of every user workload.

## 4. Traditional HPC versus the AI factory

Suppose an experienced HPC systems administrator moves onto an LLM training platform team. On day one, the cluster looks familiar: liquid-cooled racks, InfiniBand switches, a Lustre or WEKA parallel file system, and Slurm scheduling batch jobs. By Friday, the differences are unmistakable. Instead of two hundred scientists running two hundred different Fortran and C++ codes across a few dozen nodes each, one foundation-model pre-training job occupies four thousand GPUs continuously for six weeks. That job hammers the fabric with giant collective operations, and it dumps multi-terabyte checkpoints every few hours.

Both traditional HPC centers and modern AI factories are tightly coupled parallel machines. Their workloads and priorities still differ in specific ways. The table shows where those differences matter most to an operator.

| Dimension | Traditional HPC center | AI factory / training & serving cluster |
|---|---|---|
| **Primary workloads** | Physical simulation in C, C++, and Fortran using MPI and OpenMP | Neural-network pre-training, fine-tuning, data curation, and inference serving in Python with PyTorch/JAX and NCCL |
| **Numerical precision** | Heavy `FP64` double precision | Heavy `BF16`, `FP16`, `FP8`, and `FP4`; `FP64` is rarely used |
| **Parallelism & traffic** | 3D domain decomposition; MPI point-to-point halo exchanges and small-message global reductions | Data, Tensor, Pipeline, Expert, and Context parallelism; massive AllReduce, AllGather, ReduceScatter, and AllToAll elephant flows |
| **Job distribution** | Wide mix: hundreds of small to medium jobs from many researchers, plus occasional hero runs | Bimodal: a few monolithic training jobs spanning thousands of GPUs for weeks, alongside interactive fine-tuning and 24/7 inference services |
| **Interconnect** | InfiniBand, Slingshot, or custom torus/dragonfly/fat-tree fabrics | Rail-optimized InfiniBand or RoCEv2 Ethernet fat-trees with GPUDirect RDMA, plus intra-rack NVLink and NVSwitch domains in Part 12 |
| **Storage pattern** | Parallel file systems such as Lustre and GPFS for scratch, home, and simulation dumps; heavy POSIX metadata | High-throughput streaming reads for dataloaders plus periodic, synchronous multi-terabyte checkpoint write bursts in Part 13 |
| **Orchestration** | Slurm, PBS, or LSF with deep fair-share trees and project allocation accounting | Slurm with Pyxis and Enroot for large training pools, or Kubernetes with Kueue, KAI, or Volcano for unified training and inference |
| **Software packaging** | Environment modules, Spack, EasyBuild, and bare-metal compiler toolchains | OCI containers built from NGC base images |
| **Failure recovery** | Periodic checkpoint/restart; moderate node count per job keeps per-job MTBF manageable | At thousands of GPUs per job, hardware faults happen every few hours or days; automated health checks and sub-minute checkpointing are mandatory |
| **Primary north-star metric** | High overall node utilization and fair queue turnaround across a broad user community | High MFU, minimum time-to-train, and lowest **cost per token** or **tokens per watt** |
| **Facility envelope** | `15` to `40 kW` per rack with air or rear-door heat exchangers, plus liquid cooling on flagship systems | `40` to `130` kW or more per rack; direct-to-chip liquid cooling and megawatt power feeds are the primary deployment constraint in Chapter 6.30 |

As you read the table, start with the failure-recovery and north-star rows. At thousands of GPUs per job, hardware faults happen every few hours or days. That is why the table calls automated health checks and sub-minute checkpointing mandatory.

The term AI factory reflects an industrial shift in how data centers are planned. A traditional cluster works like a general-purpose computing library, where diverse users check out nodes. An AI factory is engineered like a manufacturing plant. Its raw inputs are megawatts of electricity and petabytes of training data. Its outputs are trained model weights and served intelligence tokens.

Yet HPC and AI have more in common than the contrast suggests. If you can keep an HPC cluster's fabric clean, its parallel storage fast, and its Slurm scheduler healthy, you already have the core skills to run an AI factory.

**Bring HPC's discipline in gang scheduling, fabric hygiene, and pre-job health checks into your AI clusters.** Then add fast container delivery and automated fault recovery for multi-thousand-GPU jobs.

> **In one minute:**
> - Traditional HPC centers run diverse FP64 MPI simulations across many users, whereas AI factories run massive BF16 and FP8 NCCL training jobs and 24/7 inference services.
> - A single AI training run can lock up thousands of GPUs for weeks. The mean time between hardware failures inside that job drops from weeks to hours, which makes fast checkpointing and automated node draining critical.
> - An AI factory measures success as an industrial production line: useful model FLOPs and tokens produced per megawatt and per dollar.

## 5. Kinds of clusters, custom supercomputers, and distributed models

When people say "cluster," they simply mean many computers combined into a single system. In *Supercomputers for Linux SysAdmins* Chapter 2 and *AI Factory* Chapter 9, the authors show that clusters fall into distinct categories, depending on their purpose and coupling.

### The three classic cluster types: HA, high-productivity, and HPC

Clusters come in three classic types, and the type decides what a node failure costs you.

1. High-availability and load-balanced service clusters. Their task is to give access to a resource, such as a website, database, or inference API, with maximum speed and minimum latency. They are typically paired with load balancing, A/B or canary testing, and continuous deployment. If one node fails, the resource stays available, because clients reconnect and reach the service on another node. Cloud computing applies a very similar principle. You do not know which physical node will run your application or operating system image, because the cloud platform selects free resources automatically.
2. High-productivity clusters, which include high-throughput computing and Grid clusters. In this model, all nodes work on a single large task that has been broken into independent parts. If a node fails, its unfinished part is simply sent to another node. New nodes that join receive parts that have not been calculated yet, so the overall computation finishes faster. Classic examples include Grid computing and projects like SETI@home and Folding@home. Only a narrow class of loosely coupled tasks can be solved this way. A dedicated data center cluster is often unnecessary, because home computers or ordinary servers connected over a LAN or the internet work well.
3. HPC clusters, including tightly coupled AI training. Unlike the previous two types, the failure of a single node in an HPC cluster usually leads to the emergency termination of the entire parallel program. Only in rare cases does execution continue automatically from a previously saved control point. Because of this tight coupling, HPC clusters are much more sensitive to component faults. They cannot run without strict control and monitoring. All nodes connect through high-speed, low-latency networks and high-performance parallel file systems. Parallel processes exchange messages constantly, so message initialization overhead, which is latency, matters as much as network throughput. On a high-latency network, a parallel program can run many times slower than it would on a low-latency fabric.

The table compares the three types on the points that matter when a node fails. The last column gives typical examples for each type.

| Cluster type | Primary goal | Inter-node coupling | Effect of a single node failure | Typical examples |
|---|---|---|---|---|
| **HA / load-balanced cluster** | Continuous service uptime and low request latency | Loose or replicated state | Traffic fails over transparently to surviving nodes | Web tiers, HA database pairs, stateless LLM inference replicas |
| **High-productivity (HTC / Grid)** | Complete a massive batch of independent tasks | None between worker tasks | Only the failed node's task slice is retried elsewhere | `SETI@home`, `Folding@home`, genomics sweeps, data preprocessing |
| **HPC / AI training cluster** | Run one tightly coupled parallel program as fast as possible | Tight microsecond message passing | Entire multi-node job aborts and must restart from a checkpoint | Weather forecasting, CFD, multi-node LLM pre-training |

### Clusters versus custom vendor supercomputers, farms, and Beowulf systems

Does a supercomputer always mean a cluster? No. An important feature of a cluster is that you can build it from commercially available components. You can buy every part in a store and, with enough experience, assemble the cluster yourself.

Historically, a supercomputer was a product made of unique, proprietary components from a single vendor. Take IBM's Blue Gene series. Its architecture resembles a cluster and uses similar software tools. But you could buy a Blue Gene only from IBM or its distributors. You could not build one yourself, because its key components were never sold separately. Custom systems like this are rare today, although examples such as the NEC Tsubasa still exist. At the opposite extreme sit computing farms, which are groups of computers working on a task without transmitting data to each other, and Beowulf systems, assembled practically from improvised commodity PCs. The line between a cluster and a non-cluster is clear. Practically all modern supercomputers, however, are built as clusters, enhanced with fast networks and synchronization hardware.

### Cloud, fog, and edge distributed tiers

Once an AI platform reaches beyond a single data center, distributed computing spans three geographic tiers and three cloud service models. As *AI Factory* Chapter 9 frames it, cloud providers offer IaaS for raw VMs and GPUs. They offer PaaS for managed application platforms, and SaaS for turnkey software. These services run across public, private, or hybrid clouds.

The cloud or core data center is the centralized tier. It holds hyperscale or on-premises AI factories with thousands of GPUs, plus parallel or object storage (File, Block, and Object stores; see Chapter 1.27). This tier handles heavy model training and high-throughput batch serving.

Fog computing sits in the middle tier, close to the local network edge, such as a factory plant or a regional telecom site. Fog nodes aggregate and filter sensor streams. That reduces bandwidth backhaul and latency before data reaches the central cloud.

Edge computing and cloudlets place compute directly on or beside physical devices and IoT sensors, such as autonomous vehicles or local cloudlet hotspots. Edge serves workloads where millisecond inference latency, or offline operation, rules out a round trip to the cloud.

Where do Slurm and Kubernetes fit across these models? Slurm was built for the HPC cluster model. It runs a fixed pool of nodes that execute queued, finite batch jobs, with exclusive resource allocation, gang scheduling, and strict fair-share accounting. Kubernetes was built for the HA and cloud service model. It maintains continuously running desired state across pods and load-balanced services. To adapt it for tightly coupled GPU training, you add a specialized batch operator such as Kueue, Volcano, KAI Scheduler, or JobSet.

### Fog computing: moving intelligence onto the local network

Picture a plant that sends every sensor reading to a distant cloud and then waits for the answer. Each round trip takes time, and the plant cannot act while it waits. Fog computing solves this by placing processing closer to the devices that produce the data.

Fog computing, also called fog networking or fogging, is a decentralized structure. It sits between data-producing devices, such as Internet of Things (IoT) devices, and the cloud. It extends the cloud architecture to the edge of the network, so the cloud is involved less. Moving processing units nearer the end devices makes better use of computing power, and it shortens task execution and processing time. Fog pushes intelligence down to the local network. Edge devices and gateways do the work. Data flows from the endpoints to a gateway for processing, and then flows back again.

Fog computing brings several benefits:

- Enhanced security and increased business agility.
- Improved reliability and minimized latency.
- Flexible mobility and better overall network performance, because the distance across the network is shorter.
- Time-sensitive analysis at the network edge, instead of sending all IoT data to the cloud.
- Fast response, measured in milliseconds.

Fog has limits too. You should know that its architecture depends on many links in a chain that carries data from physical assets into the digital world, and each link can fail. Its latency and bandwidth are still limited, and it still depends on the cloud.

The fog model has three layers. The cloud layer holds data centers and servers with large storage and computing power. They manage and process data that arrives from the fog layer. The fog layer holds fog nodes, which are network devices with enough processing and temporary storage. A fog node receives requests from devices, then decides whether to process each one locally or send it to the cloud. The terminal layer holds the IoT and end-user devices. They sense the physical world and send their data up to the fog layer.

### Edge computing: processing at the device

Edge computing places computing resources and storage at the edge of the network, close to the end user. It works together with the cloud, so you can think of it as a more localized version of fog and cloud computing. It grew out of peer-to-peer networking, distributed data, self-healing networks, and remote cloud services. It runs on small form-factor hardware with flash storage arrays. Its processors offer better hardware security and use little power.

Edge computing is built on the idea of cloudlets. A cloudlet is like a Wi-Fi hotspot that offers cloud services without Wi-Fi internet connectivity. Its only rule about placement is that it sits at the edge of the network or near the user.

Edge computing brings clear advantages. It reduces latency between end devices and the cloud. It uses the resources of both the cloud and the local devices, because each device both produces and consumes data. It reduces network cost and transmission delay, and it gives better control over sensitive data movements. It helps augmented and virtual reality applications, which benefit from low response times. It can keep data local, so that data stays safe if the data center is compromised. It can also hold data locally and send it to the cloud later, when enough bandwidth is free. In short, it reduces network traffic and the risk of a data bottleneck.

Edge computing processes sensor data where it is produced, rather than carrying it to a central node. Devices at the edge triage their data locally, which cuts the traffic sent to the central repository. That also removes parts of the fog communication chain, and it reduces the number of possible failure points. An edge device can be any device with enough computing capacity, including switches, routers, and sensors.

For IoT, edge devices collect and process the data that sensors send. Without edge computing, that data would travel back and forth to the cloud. Those round trips slow responses and waste efficiency. Because processing happens nearer the source, the data is handled faster, with lower latency, and less bandwidth is used.

### Fusing data from many sensors

Edge devices often collect readings from several sensors at once. When you combine those readings into one picture, the result is called data fusion. It sounds simple, but the readings rarely agree perfectly, so fusion has to handle several problems. The table lists each problem and what it means.

| Problem | What it means |
|---|---|
| Imprecision and uncertainty | No measurement is perfect, so each reading carries some level of uncertainty. |
| Spurious data and outliers | Data can be noisy or hard to read, and faulty or imprecise measurements can produce extreme values. |
| Modality | The data may mix visual, auditory, and physical measurements. |
| Conflict | Different sensors can report values that contradict each other, and these are hard to fuse. |
| Operational timing | Different parts of the data can take different routes to the fusion point, so they arrive out of sequence. |
| Dynamic versus static | Some values come from a phenomenon that does not change over time, while others change constantly. |
| Dimensionality | Measurements can come in different dimensions, so they must be reduced to the needed dimensions, either at the sensor node or at the fusion center. |
| Correlation | Nearby sensors can share the same external noise. If those shared dependencies are ignored, the result can be inconsistent. |
| Alignment and registration | Each sensor uses its own local frame, so the data must be placed in one standard frame before fusion. |

Two more terms matter here. Data association means finding meaningful relations between variables, often quite different ones, inside large databases. The processing framework decides whether fusion is centralized or decentralized. Decentralized fusion is usually preferred in wireless sensor networks, because it lowers the communication load and lets each sensor process its own data. Consider data quality from collection all the way through to fusion.

### Cloud, fog and edge compared

These three architectures look alike, but they meet different needs. The table below shows the main differences.

| Points of difference | Cloud computing | Fog computing | Edge computing |
|---|---|---|---|
| Location of data processing | Central cloud server | Within an IoT gateway or fog nodes located in the LAN network | Device itself |
| Purpose | Long-term in-depth analysis | Quick analysis and real-time response | Quick analysis and real-time response |
| Latency | High | Low | Very low |
| Security | Less secure | High security | High security |
| Geographical distribution | Centralised | Distributed | Distributed |

The three are not interchangeable. Time-sensitive data is processed at the edge, while data that is not time-driven goes to the cloud. Fog uses a centralized system that works with industrial gateways and embedded computers on a LAN. Edge computing does much of its processing on embedded platforms that connect directly to sensors and controllers.

Organizations that rely heavily on data increasingly use cloud, fog, and edge infrastructure together. Most enterprises are moving toward fog or edge designs to make better use of their end-user and industrial IoT devices. Pairing a cloud platform with on-site fog networks or edge devices often gives the best results.

**Match your orchestrator and fault-tolerance design to how tightly coupled the workload is.** Use gang scheduling and fast checkpoints for tightly coupled HPC and NCCL jobs. Use stateless failover or task retries for HA and HTC pools.

> **In one minute:**
> - HA clusters survive node failures transparently, and HTC or Grid clusters, such as Folding@home, simply retry the dead node's task. In a tightly coupled HPC or AI training job, a single node failure halts the entire job.
> - True clusters are built from commercially available components, unlike proprietary single-vendor supercomputers such as IBM Blue Gene or NEC Tsubasa. Loose compute farms are separated from them by their low-latency fabric.
> - Slurm naturally fits queued, tightly coupled batch jobs on a fixed node pool. Kubernetes naturally fits long-running services and adds batch queueing through operators.

## 6. What "super" means to the administrator

A user who submits a job script sees one giant virtual computer, with a huge memory and tens of thousands of computing cores. You, the administrator on call, know that the illusion holds together only because eight strict invariants apply to every node in the fleet. The table lists them. Each one maps to a chapter, so you can read the detail when you need it.

| # | Invariant | What it means |
|---|---|---|
| 1 | Identical software state | Every compute node runs the exact same OS image, kernel patch level, GPU driver, and NIC firmware. |
| 2 | Synchronized time and identity | Clocks are synchronized via `chrony` or NTP, and every username maps to the exact same numeric UID and GID everywhere in Chapter 6.24. |
| 3 | Predictable naming and networking | DNS, `/etc/hosts`, DHCP and PXE boot, the out-of-band management network, and the high-speed compute fabric all resolve and route cleanly. |
| 4 | Uniform shared storage | Parallel and home file systems are mounted at identical paths with enforced user and project quotas in Chapters 6.18 to 6.21. |
| 5 | Centralized scheduling and accounting | Users never log into compute nodes directly to start work; the batch scheduler places every job, isolates it in cgroups, and logs usage in Chapters 6.7 to 6.15. |
| 6 | Comprehensive observability | Automated monitoring tracks node health, temperatures, power supplies, air conditioning, UPS units, fabric symbol errors, and GPU faults in Chapter 6.26. |
| 7 | Repeatable provisioning | Automated image deployment and configuration management ensure a replacement server boots into an identical state within minutes in Chapter 6.22. |
| 8 | Spares and SLA discipline | Unless hardware has built-in redundancy, you maintain an on-site emergency stock of key spares and vendor service agreements with clearly defined replacement SLAs. |

### Why office IT habits fail in a supercomputer data center

At first glance, a large cluster looks no different from many office computers connected by a local area network and a few storage servers. In reality, four physical and operational differences separate a supercomputer from office IT.

The first difference is density. Office PCs spread across a building, but a cluster is packed into several square meters or a few dozen square meters. You cannot cool it with an open window or a household air conditioner. You cannot plug it into wall sockets or protect it with a household UPS. In modern clusters, **the computing part can occupy less than a quarter of the total installation area**. The rest goes to climate and energy equipment, covered in Chapter 6.30.

The second difference is utilization. In an office, a computer needs only a few minutes a day to display a document or play a video clip. Ninety-nine percent of the time, office PCs sit idle, waiting for a mouse click or keystroke. In a supercomputer, the normal mode of operation is 80–100% utilization of each node at all times.

The third difference is the I/O storm. When an office network suddenly sees load jump hundreds of times and network storage slows to a crawl, every administrator suspects a virus. In a cluster, all nodes busy on one task, exchanging data or writing intermediate results to network disk at the same time, is completely normal. Peak loads are routine here, so key services must be duplicated or load-shared from the start.

The fourth difference is how you learn about failures. In an office, when a node, an air conditioner, or a UPS fails, an employee runs in shouting that their report is on fire. The worst case in a cluster is learning about a hardware failure from users whose parallel program has stopped working properly, or that starts only two times out of three. You prevent that by monitoring everything across the facility and the cluster.

### Power-on surge hazards and startup sequencing

Powering on is itself a peak load. In an office, employees arrive at different times and switch on their computers gradually. Powering on a supercomputer all at once creates three severe hazards:

1. Electrical inrush and boot-storm service overload: Switching on a supercomputer sharply increases power consumption, by dozens or even thousands of kilowatts. Immediately afterward, all compute nodes request storage and service nodes at almost the same time. If you turn on everything at once, the electrical installation can trip or burn down. Even switching nodes on smoothly at intervals of a few seconds can cause network conflicts or overload a central service with requests.
2. Multi-rack disk array spin-up torque and controller sequencing: In large disk arrays that span several racks, shelves and disks start in a specific sequence. That limits high starting currents and keeps the spinning disks from swaying the rack. You must also power on the array components in the exact sequence the storage controllers expect. Otherwise, the controllers may decide the array is broken, start rebuilding it, or even mark it as dead.
3. Hot-corridor thermal baking: Server racks often sit opposite each other in a corridor and blow hot air into a shared hot aisle. Turn them on at staggered intervals, so you do not overheat opposing servers that are not yet on.

### Command-line fleet management and the "panacea" console trap

Many complicated cluster jobs come down to a few standard commands chained together. Most of the time, you need no special tool. The real effort goes into mastering each command at first, and that takes time. After that, the command line works like a toolbox you can combine in many ways.

Even a small compute cluster is far bigger than a dozen servers, so graphical tools stop being realistic. Suppose you need to know which servers failed to detect their full RAM the last time they powered on. Opening a graphical system monitor on a hundred nodes and clicking the system tab on each would take all day. Instead, you run one command across all nodes, using a parallel shell tool such as `pdsh` or `clush`:

```bash
# (untested here)
grep MemTotal /proc/meminfo | awk '{print $2}'
```

In a couple of seconds, you get the detected memory from every server. A couple more shell commands, modeled in `filter_nodes_missing_ram()` in `code/part06/flops.py`, do the rest. They compare each node's value against your expected benchmark of `528,482,304` kB, within a 2% tolerance. Then they print only the nodes that failed. Studying the *Advanced Bash Scripting Guide* helps, and so does combining `bash` or `zsh` with `grep`, `sed`, `awk`, `find`, `ps`, and Python or Perl. Together, these multiply your speed many times over. Supercomputer users also need very different support from users in neighboring office rooms, a topic covered in Chapter 6.25.

Doing bulk operations day after day, every administrator eventually dreams of one convenient console. It would do everything without scripts or text copied from terminal screens. That dream often strikes when you look at enterprise management suites such as `HP OpenView` or `Zenoss`. You want to exclaim, "Here it is, the panacea." These products inventory equipment, track users and software, and automate standard tasks. You can adapt them for parts of your work.

Sadly, they solve only parts of the problem. Commercial and free enterprise consoles aim at tasks that overlap with supercomputing without being the same. Forcing them into specialized HPC work takes a huge investment of human effort, money, and time. Each time your supercomputer's configuration changes, you must redo that customization. Experience across many supercomputer centers shows that no universal all-in-one solution exists. The market for supercomputer administrators is narrow, and custom tools are expensive to maintain. Instead, rely on flexible, extensible CLI tools, and keep all organizational and accounting processes well documented. That documentation does more than remind you of steps. It shows the big picture, so you can adapt established processes quickly when conditions change.

**Automate fleet checks from the command line and enforce a staggered storage-first power-on sequence.** Monitor every facility and hardware metric proactively, so users never discover failures for you.

> **In one minute:**
> - A supercomputer runs at 80–100% utilization 24/7, packs compute into less than a quarter of the total facility floor space, and treats synchronized network and storage bursts as normal everyday load.
> - Never power on a cluster all at once. Sequence disk shelves before storage controllers to prevent starting-current spikes, rack sway, and false array rebuilds. Stagger hot-corridor racks, and pace compute node boots.
> - Use parallel CLI tools (`pdsh` or `clush` with `grep MemTotal /proc/meminfo | awk '{print $2}'`) and flexible scripts, rather than chasing rigid all-in-one enterprise GUI consoles.

## 7. The stack at a glance

The diagram shows how the pieces of a supercomputer connect, from users and login nodes down to the facility. You can use it to see where each piece sits. The table after it maps each layer to the chapters that cover it.

```mermaid
flowchart TB
  U[Users and workflows]
  U --> L[Login nodes: SSH, Open OnDemand]
  L --> S[Scheduler: Slurm or K8s queues]
  S --> C[Compute nodes with GPUs]
  C --> A[Apps: MPI, NCCL, PyTorch]
  C --- F[Compute fabric: IB or RoCE]
  C --- P[Parallel storage: Lustre, WEKA]
  M[Management: PXE, BCM, BMC] --> C
  M --> S
  M --> P
  FAC[Facility: power, liquid cooling] --> C
```

| Layer in diagram | Role in the supercomputer complex | Covered in |
|---|---|---|
| **Login nodes (`L`)** | User entry point for editing code, compiling, and submitting batch jobs (`ssh`, Open OnDemand) | Chapters 6.2, 6.25 |
| **Scheduler (`S`)** | Allocates nodes and GPUs exclusively, enforces fair-share and QoS, and launches parallel steps (Slurm, Kueue) | Chapters 6.7–6.17 |
| **Compute nodes & Apps (`C`, `A`)** | Execute parallel kernels across CPUs and GPUs (MPI, OpenMP, NCCL, PyTorch, Enroot) | Chapters 6.3–6.6, 6.12–6.13, 6.29 |
| **Compute fabric (`F`)** | Low-latency, high-bandwidth RDMA interconnect (InfiniBand, RoCEv2) | Chapter 6.12, Part 12 |
| **Parallel storage (`P`)** | High-throughput shared namespaces for datasets and checkpoints (Lustre, GPFS, BeeGFS, WEKA, VAST) | Chapters 6.18–6.21, Part 13 |
| **Management plane (`M`)** | Out-of-band BMCs (Redfish), PXE image provisioning (xCAT, Warewulf, BCM), LDAP, and monitoring | Chapters 6.22–6.27, Parts 7 & 8 |
| **Facility (`FAC`)** | High-density power distribution, UPS, chillers, and direct-to-chip liquid cooling | Chapter 6.30, Part 9 |

If you are tracing a failure, start by finding its layer. Then use the table to find the chapters for that layer.

## 8. Common misconceptions

Watch for these five common beliefs about supercomputers.

- "A supercomputer is one giant computer." Physically, it is hundreds or thousands of separate Linux servers. The high-speed fabric, parallel file system, and batch scheduler make them behave as one coherent system.
- "More FLOPS means my job will run faster." That holds only if your code uses the numerical precision the headline number assumes. Your job also has to avoid being bottlenecked by memory bandwidth, network latency, or storage I/O.
- "A TOP500 rank proves AI capability." TOP500 measures FP64 dense LU factorization on HPL. Evaluate AI clusters with MLPerf, NCCL tests, and your actual training or inference workload.
- "Cloud VMs are identical to a supercomputer." Cloud providers can host true supercomputer clusters. You need bare-metal or passthrough GPU instances, placed inside a compact placement group with RDMA fabrics. Ordinary unplaced VMs on a shared TCP network suffer severe latency penalties, as Chapter 1.27 explains.
- "Replacing a failed component with a slightly slower spare is fine temporarily." In a tightly coupled cluster, one node with less RAM or a slower network link drags down every multi-node job that lands on it.

## 9. Lab (no cluster required)

Start with the self-checking Python lab, which runs on your own machine. Run `code/part06/flops_lab.py` locally. It verifies the vector pipeline cycle equation `K*(N-1)+S` from *Supercomputers for Linux SysAdmins* Chapter 2. It also checks the CPU and GPU Rpeak, HPL efficiency, and BF16 MFU calculations. Finally, it tests the fleet-wide `/proc/meminfo` `MemTotal` anomaly filter from *Supercomputers for Linux SysAdmins* Chapter 1:

```bash
python3 code/part06/flops_lab.py
```

Then work through these hands-on steps.

1. Open `code/part06/flops.py` and run `python3 code/part06/flops.py`. Then change `flops_per_cycle` from `32` to `16`. That simulates a CPU without dual AVX-512 FMA units. You should see Rpeak drop from `983.0` to `491.5` TFLOP/s.
2. Call `vector_pipeline_cycles(1000, 1, 5)` and compare the pipelined count of `1004` cycles with the `5000` unpipelined cycles. Then check that the `4.98x` speedup printed by `code/part06/flops.py` matches.
3. Test `filter_nodes_missing_ram()` with a 10-node dictionary. In it, one node lost one of its eight `64 GB` DIMMs on boot. That node reports `448 GB` instead of `512 GB`, so a 2% tolerance threshold flags it immediately.
4. Look up the current June or November TOP500 and Green500 lists online (**untested** here). Record the number-one system's Rmax, Rpeak, HPL efficiency, and power in megawatts.

## 10. Interview angles

Use these questions to test yourself. Answer each one in your own words before you check the sections above.

- Define a supercomputer in two sentences from a system administrator's perspective. What separates it from a 1,000-node web farm?
- Walk through the nine levels of hardware and software parallelism in a cluster. If an MPI job launches cleanly on 64 nodes but runs ten times slower than expected, what is the first configuration mistake you check?
- Explain the difference between Rpeak, Rmax, and MFU. Why is HPCG efficiency only a few percent of Rpeak when HPL reaches 60% to 80% or more?
- Why do powering on a multi-rack storage array and a hot-corridor compute cluster require a strict startup sequence?
- How do you verify in three seconds that all 500 compute nodes detected their full physical RAM after a power outage?

## Exercises

Work through these on paper first, then check your answers. You should answer before you look.

1. Start with pipelining and memory banks, drawing on *Supercomputers for Linux SysAdmins* Chapter 2. Using `vector_pipeline_cycles()` in `code/part06/flops.py`, compute the clock cycles a five-stage vector adder (`S = 5`, `K = 1`) needs for `N = 100` elements, versus `500` unpipelined cycles. Then explain why populating four `8 GB` RAM modules across four independent motherboard memory banks outperforms a single `32 GB` module in one slot.
2. Work through the nine levels of cluster parallelism from *Supercomputers for Linux SysAdmins* Chapter 2. List all seven hardware levels and both software levels. Then explain why a parallel MPI program can run slower than a sequential program. Threads may contend for CPU cache. Or MPI may route traffic over the Ethernet management network instead of InfiniBand.
3. Use the functions in `code/part06/flops.py` to work out Rpeak, Rmax, HPL efficiency, and MFU. Call `rpeak_cpu()`, `gpu_cluster_peak_pflops()`, and `hpl_efficiency()`. First, compute the FP64 Rpeak of a hundred-node CPU cluster with two sockets, 64 cores per socket, and 2.4 GHz. Do this with 32 FLOPs per cycle, then with 16. Next, compute the HPL efficiency with Rmax at 38 and at 48.0 PFLOP/s. Finally, compute the 40% MFU sustained BF16 rate of an 800-GPU cluster.
4. Contrast HA, HTC (SETI@home and Folding@home), and HPC clusters, drawing on *Supercomputers for Linux SysAdmins* Chapter 2 and *AI Factory* Chapter 9. Look at inter-node coupling and at the blast radius of a single node failure. Then distinguish a commodity COTS or Beowulf cluster from a single-vendor custom supercomputer, such as IBM Blue Gene or NEC Tsubasa. Finally, state how the Cloud, Fog, and Edge tiers divide training and low-latency inference.
5. Drawing on *Supercomputers for Linux SysAdmins* Chapter 2, explain why compute racks often occupy less than a quarter of a supercomputer's total floor area, and why they run at 80–100% continuous utilization. Then describe the three physical startup hazards when you power on a cluster after an outage. They are electrical and network request surges, multi-rack disk shelf spin-up torque and controller ordering, and hot-corridor overheating.
6. Write the `pdsh` or `clush` command that uses `grep MemTotal /proc/meminfo | awk '{print $2}'` to audit physical memory across one hundred nodes after boot. Then trace how `filter_nodes_missing_ram()` in `code/part06/flops.py` finds nodes with missing DIMMs within a two percent tolerance. Finally, explain why enterprise GUI suites such as `HP OpenView` and `Zenoss` are not a universal panacea for supercomputer administration. Use *Supercomputers for Linux SysAdmins* Chapters 1 and 2 as your sources.

## Checkpoint questions (20)

<details>
<summary>1. What are the three working definitions of a supercomputer, and what does "super" mean to the Linux administrator who operates one (*Supercomputers for Linux SysAdmins*, Chapters 1 and 2)?</summary>

There are three working definitions: by rank or cost, by capability, and by operational shape. By capability means solving one large problem through parallel execution across many processors. To the administrator, "super" means overall synchronization across one tightly integrated complex. Every server, switch, storage array, and software layer must line up and be tuned together. Even a slight imbalance on one node degrades the whole complex.
</details>

<details>
<summary>2. What is the difference between hardware **parallelism** and **pipelining** inside a processor (*Supercomputers for Linux SysAdmins*, Chapter 2)?</summary>

Parallelism means separate hardware units run different independent instructions at the same time. For example, an adder can compute `x=a+b` while a multiplier computes `y=b*c`. Hundreds of GPU cores can run the same kernel together. Pipelining is different. It splits one operation into sequential stages, such as load, normalize mantissas, add, correct, and write. The stages work like a conveyor belt, so several elements are in flight at different stages at once. AVX vector instructions work this way.
</details>

<details>
<summary>3. Write the cycle formula for processing a vector of `N` elements through a pipeline whose slowest stage takes `K` clock cycles and whose full pipeline length is `S` cycles (*Supercomputers for Linux SysAdmins*, Chapter 2).</summary>

$$\text{Total cycles} = K \times (N - 1) + S$$
The first element finishes after `S` cycles. That wait is the pipeline acceleration time. Each later element finishes one every `K` cycles. In modern processors `K` is typically `1`. For example, with `S = 5`, `K = 1`, and `N = 100`, the total is `104` cycles.
</details>

<details>
<summary>4. Why does populating four `8 GB` RAM modules across four motherboard memory banks perform better than installing one `32 GB` module in a single slot (*Supercomputers for Linux SysAdmins*, Chapter 2)?</summary>

Independent memory banks work in parallel. While one word is being written or read on the first bank, the memory controller can start the next access on a second bank at the same time. If you put all `32 GB` into a single slot, every access goes through one bank, which serializes them.
</details>

<details>
<summary>5. List the nine levels of hardware (`[HW]`) and software (`[SW]`) parallelism in a compute cluster (*Supercomputers for Linux SysAdmins*, Chapter 2).</summary>

1. `[HW]` Multiple independent memory banks.
2. `[HW]` Multiline CPU caches.
3. `[HW]` Multiple CPUs (sockets).
4. `[HW]` Multiple CPU cores on a die.
5. `[HW]` Multiple functional devices inside one CPU core.
6. `[HW]` Accelerators such as GPUs and FPGAs.
7. `[HW]` Network devices with DMA and offloading.
8. `[SW]` Multiple UNIX processes and threads on a node (OpenMP).
9. `[SW]` Multiple servers running one parallel program across nodes (MPI, plus CUDA and OpenACC).
</details>

<details>
<summary>6. Why can a parallel program run **slower** than a sequential program, and what classic network misconfiguration slows down working MPI jobs (*Supercomputers for Linux SysAdmins*, Chapter 2)?</summary>

Parallel code can run slower if you have threads on a node contending for different memory sections and thrashing the CPU cache. It can also run slower when processes spend most of their time waiting for data from the slowest process. A classic misconfiguration is MPI launching cleanly but routing inter-node messages over the slow Ethernet management network instead of the high-speed InfiniBand fabric.
</details>

<details>
<summary>7. Why must every FLOPS rating be accompanied by a numerical precision, and how do FP64, BF16, and FP8 compare on modern AI GPUs?</summary>

FLOPS counts floating-point operations per second. Modern GPUs put far more throughput into low-precision Matrix Tensor Cores (BF16, FP16, FP8, FP4) than into FP64 double-precision units. So if you compare a cluster's dense BF16 or FP8 peak with its FP64 TOP500 peak, you will often find the first is more than an order of magnitude higher.
</details>

<details>
<summary>8. Write the formula for a CPU cluster's theoretical peak (Rpeak), and compute Rpeak for `100` nodes with `2` sockets, `64` cores per socket, `2.4 GHz`, and `32` FP64 FLOPs per cycle per core.</summary>

Multiply the hardware counts together. For example, the 100-node cluster works out like this.

$$\text{Rpeak (GFLOP/s)} = \text{nodes} \times \text{sockets} \times \text{cores} \times \text{GHz} \times \text{FLOPs/cycle/core}$$
For the 100-node cluster: $100 \times 2 \times 64 \times 2.4 \times 32 = 983{,}040\text{ GFLOP/s} \approx \mathbf{983.0\text{ TFLOP/s}}$.
</details>

<details>
<summary>9. What is the difference between Rpeak, Rmax, and MFU?</summary>

- Rpeak is the theoretical maximum FLOP/s, reached only if every arithmetic unit runs on every clock cycle with zero stalls.
- Rmax is the highest sustained FP64 FLOP/s achieved on the HPL benchmark. If you divide Rmax by Rpeak, you get the HPL efficiency.
- MFU, model FLOPs utilization, is the AI counterpart to HPL efficiency. It compares useful model forward and backward FLOP/s with the accelerator's theoretical peak at the training precision.
</details>

<details>
<summary>10. What does HPL measure on the TOP500 list, when is the list published, and how does HPL-MxP differ?</summary>

- TOP500 / HPL: The list is published twice a year, in June at ISC and in November at SC. It ranks systems by Rmax on a dense linear system $Ax = b$, solved by LU factorization in FP64 double precision.
- HPL-MxP: It solves the Linpack problem with mixed-precision, low-precision tensor factorization (FP16 or BF16), then applies FP64 iterative refinement. That reflects AI hardware capabilities.
</details>

<details>
<summary>11. Why does HPCG typically achieve only a few percent of Rpeak on machines that score 60% to 80% efficiency on HPL?</summary>

HPL performs dense matrix-matrix multiplication with high arithmetic intensity. In plain terms, you can think of it as doing many FLOPs for every byte it reads from memory, which keeps the compute cores saturated. HPCG, the High Performance Conjugate Gradients benchmark, performs sparse linear algebra instead. It uses irregular pointer chasing, low arithmetic intensity, and frequent global reductions. So its speed depends on memory bandwidth and network latency more than on raw FLOPs.
</details>

<details>
<summary>12. What do Green500, Graph500, IO500, and MLPerf each measure?</summary>

- Green500 measures energy efficiency in GFLOP/s per watt.
- Graph500 measures data-intensive graph traversal throughput, in traversed edges per second.
- IO500 measures parallel storage bandwidth (`IOR`) and metadata rate (`mdtest`).
- MLPerf, from MLCommons, measures the time to train reference AI models to a target quality, along with serving throughput or latency under quality constraints.
</details>

<details>
<summary>13. Compare a traditional HPC center with an AI factory across workloads, numerical precision, and failure frequency.</summary>

- Workloads and precision: Traditional HPC runs many distinct C, C++, and Fortran physical simulations in FP64, using MPI and OpenMP. An AI factory runs Python, PyTorch, and NCCL foundation-model training and inference in BF16, FP8, and FP4.
- Failure frequency: A single AI training job can occupy thousands of GPUs at once for weeks. Its mean time between hardware faults drops to hours or days. That calls for fast asynchronous checkpoints and automated node draining.
</details>

<details>
<summary>14. Compare High-Availability (HA), High-Productivity (HTC / Grid), and High-Performance (HPC) clusters when a single compute node fails (*Supercomputers for Linux SysAdmins*, Chapter 2).</summary>

- HA cluster: Clients reconnect transparently to surviving nodes, and the service stays online.
- HTC / Grid cluster (SETI@home, Folding@home): Only the failed node's independent task chunk is lost. That chunk is reassigned to another node while the other nodes keep working.
- HPC / AI training cluster: Because all processes are tightly coupled and exchange messages synchronously, one failed node usually terminates the entire multi-node parallel program. The job then restarts from the last saved checkpoint.
</details>

<details>
<summary>15. How does a commodity cluster differ from a historical single-vendor supercomputer like `IBM Blue Gene` or `NEC Tsubasa`, and what is a `Beowulf` cluster (*Supercomputers for Linux SysAdmins*, Chapter 2)?</summary>

A cluster can be assembled from commercially available off-the-shelf servers and switches sold on the open market. A Beowulf cluster is built from ordinary commodity PCs or improvised parts. A historical non-cluster supercomputer, such as IBM Blue Gene or NEC Tsubasa, uses proprietary processors, boards, and interconnects made by a single vendor. You cannot buy those parts separately to build your own machine.
</details>

<details>
<summary>16. Why do Slurm and Kubernetes fit different cluster models by default, and how are they bridged in AI platforms?</summary>

Slurm models a fixed pool of nodes that runs queued, finite batch jobs. It offers exclusive node and GPU allocation, gang scheduling, and fair-share accounting. Kubernetes models continuously running desired state across pods and load-balanced services. To gang-schedule tightly coupled training jobs, it needs batch add-ons such as Kueue, Volcano, KAI Scheduler, or JobSet. If you want Slurm on Kubernetes instead, Slinky and Soperator provide it, as Chapter 6.16 covers.
</details>

<details>
<summary>17. Contrast an office LAN with a supercomputer facility in terms of floor area allocation, normal node utilization, and synchronized I/O bursts (*Supercomputers for Linux SysAdmins*, Chapter 2).</summary>

- Floor area: In a modern supercomputer facility, the computing racks can occupy less than a quarter of the total floor area. Cooling and power equipment take up the remaining three-quarters.
- Utilization: An office PC sits idle 99% of the time. A supercomputer runs at `80–100%` node utilization continuously.
- Synchronized bursts: Hundreds of nodes blasting data across the network or writing checkpoints to shared storage is normal everyday operation in a cluster, not a sign of a virus outbreak.
</details>

<details>
<summary>18. What are the three physical and operational hazards of powering on a supercomputer after a maintenance window (*Supercomputers for Linux SysAdmins*, Chapter 2)?</summary>

1. Electrical inrush and boot-request storm: Turning everything on at once causes a sudden jump of dozens or thousands of kilowatts in power draw. Immediately afterward, every compute node floods storage and management servers with simultaneous requests.
2. Multi-rack disk array spin-up torque and controller order: Disk shelves and drives must spin up in sequence to limit starting currents and keep the physical torque of spinning disks from swaying the rack. Shelves must also be online before storage controllers boot, so the controllers do not mark the array dead or start a rebuild.
3. Hot-corridor overheating: In face-to-face racks that blow exhaust into a shared hot corridor, you must start the servers at staggered intervals. That keeps active racks from overheating opposing servers whose fans are still off.
</details>

<details>
<summary>19. How does an administrator check in seconds which compute nodes failed to detect their full physical RAM on boot (*Supercomputers for Linux SysAdmins*, Chapter 1)?</summary>

Instead of opening a GUI monitor on each machine, you run a parallel shell command across all nodes, with `pdsh` or `clush`:
`grep MemTotal /proc/meminfo | awk '{print $2}'`.
Then compare each node's reported kilobytes against the expected benchmark, within tolerance, and print only the nodes with missing DIMMs.
</details>

<details>
<summary>20. Why does *Supercomputers for Linux SysAdmins* Chapter 2 warn against treating enterprise management suites like `HP OpenView` or `Zenoss` as a universal "panacea" for supercomputers?</summary>

Enterprise suites such as `HP OpenView` and `Zenoss` inventory standard servers and automate routine office IT tasks. They cover only a fraction of a supercomputer's specialized fabric, scheduler, and boot requirements. Customizing them for HPC takes a massive investment of human effort, money, and time, and you must redo it whenever the cluster's architecture changes. If you build a documented, systematic workflow on flexible, extensible CLI tools and scripts, it adapts far better.
</details>

## Sources and review notes

- **Sources read in full:**
  - `supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to-hardware` — Sergey Zhumatiy, *Supercomputers for Linux SysAdmins*, **Chapter 1: Introduction** and **Chapter 2: What Is "Super"?**. Covered topics include the supercomputer as a single closely connected complex, CLI mastery (`pdsh`/`clush` `grep MemTotal /proc/meminfo | awk '{print $2}'`), and hardware parallelism versus vector pipelining (`K*(N-1)+S` with `S=5` and `K=1`). Also covered are multi-bank RAM (`4 x 8 GB` vs `1 x 32 GB`), DMA offload, the 9 levels of cluster parallelism, slow-Ethernet MPI misconfiguration, cluster types (`HA`, `HTC`/`SETI@home`/`Folding@home`, `HPC`), `IBM Blue Gene` and `NEC Tsubasa` versus commodity/Beowulf clusters, `< 25%` compute floor area, `80–100%` utilization, the 3 power-on hazards, and the `HP OpenView`/`Zenoss` console warning.
  - `ai-factory` — Ramin Karim, Diego Galar & Uday Kumar, *AI Factory*, **Chapter 9: Distributed Computing**. Covered topics include Cloud (`IaaS`, `PaaS`, `SaaS`), public/private/hybrid deployment, `File`/`Block`/`Object` storage, and Cloud/Fog/Edge distributed computing tiers. Remaining general IT sections on cognitive computing, blockchain, and railway cybersecurity are out of scope per `planning/gem_books/ai-factory_triage.md` and `planning/coverage/chapters/06-01.md`.
- **Public benchmark references:** `TOP500`, `HPL`, `HPCG`, `HPL-MxP`, `Green500`, `Graph500`, `IO500`, and `MLCommons` (`MLPerf Training` and `Inference`) benchmark definitions and publication schedules.
- **Run here:** `python3 code/part06/flops.py` and `python3 code/part06/flops_lab.py` (3 passed, 0 failed).
- **Explicitly labelled inferences:** The `vector_pipeline_cycles` (`104` vs `500` cycles for `N=100`, `1004` vs `5000` cycles for `N=1000`, `4.98x`) and `filter_nodes_missing_ram` (`528,482,304` kB, `448 GB` vs `512 GB`) functions in `code/part06/flops.py` are the author's deterministic teaching models. The illustrative `100`-node and `800`-GPU `Rpeak` (`983.0` and `491.5` TFLOP/s, `48.0` and `38` PFLOP/s = `79%`, `800` and `320` PFLOP/s at `40%` MFU, `60` and `1000` TFLOP/s per GPU) examples are likewise illustrative models.
- **Not verified on live hardware:** Live `pdsh` and `clush` execution across a physical cluster (`grep MemTotal /proc/meminfo | awk '{print $2}'`), live `TOP500` and `MLPerf` benchmark runs, and facility power-on sequences are marked (`untested here`).
