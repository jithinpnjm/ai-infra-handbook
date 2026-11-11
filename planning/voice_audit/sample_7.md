# Voice sample 7: parts part-06-hpc-slurm, part-15-inference

## FILE docs/part-06-hpc-slurm/01-what-a-supercomputer-is-top500-linpack-hpc-versus-ai-factory.md

Historically, a supercomputer was a product made of unique, proprietary components from a single vendor. Take IBM's Blue Gene series. Its architecture resembles a cluster and uses similar software tools. But you could buy a Blue Gene only from IBM or its distributors. You could not build one yourself, because its key components were never sold separately. Custom systems like this are rare today, although examples such as the NEC Tsubasa still exist. At the opposite extreme sit computing farms, which are groups of computers working on a task without transmitting data to each other, and Beowulf systems, assembled practically from improvised commodity PCs. The line between a cluster and a non-cluster is clear. Practically all modern supercomputers, however, are built as clusters, enhanced with fast networks and synchronization hardware.

---

Where do Slurm and Kubernetes fit across these models? Slurm was built for the HPC cluster model. It runs a fixed pool of nodes that execute queued, finite batch jobs, with exclusive resource allocation, gang scheduling, and strict fair-share accounting. Kubernetes was built for the HA and cloud service model. It maintains continuously running desired state across pods and load-balanced services. To adapt it for tightly coupled GPU training, you add a specialized batch operator such as Kueue, Volcano, KAI Scheduler, or JobSet.

---

Picture a plant that sends every sensor reading to a distant cloud and then waits for the answer. Each round trip takes time, and the plant cannot act while it waits. Fog computing solves this by placing processing closer to the devices that produce the data.

---

1. Start with pipelining and memory banks, drawing on *Supercomputers for Linux SysAdmins* Chapter 2. Using `vector_pipeline_cycles()` in `code/part06/flops.py`, compute the clock cycles a five-stage vector adder (`S = 5`, `K = 1`) needs for `N = 100` elements, versus `500` unpipelined cycles. Then explain why populating four `8 GB` RAM modules across four independent motherboard memory banks outperforms a single `32 GB` module in one slot.
2. Work through the nine levels of cluster parallelism from *Supercomputers for Linux SysAdmins* Chapter 2. List all seven hardware levels and both software levels. Then explain why a parallel MPI program can run slower than a sequential program. Threads may contend for CPU cache. Or MPI may route traffic over the Ethernet management network instead of InfiniBand.
3. Use the functions in `code/part06/flops.py` to work out Rpeak, Rmax, HPL efficiency, and MFU. Call `rpeak_cpu()`, `gpu_cluster_peak_pflops()`, and `hpl_efficiency()`. First, compute the FP64 Rpeak of a hundred-node CPU cluster with two sockets, 64 cores per socket, and 2.4 GHz. Do this with 32 FLOPs per cycle, then with 16. Next, compute the HPL efficiency with Rmax at 38 and at 48.0 PFLOP/s. Finally, compute the 40% MFU sustained BF16 rate of an 800-GPU cluster.
4. Contrast HA, HTC (SETI@home and Folding@home), and HPC clusters, drawing on *Supercomputers for Linux SysAdmins* Chapter 2 and *AI Factory* Chapter 9. Look at inter-node coupling and at the blast radius of a single node failure. Then distinguish a commodity COTS or Beowulf cluster from a single-vendor custom supercomputer, such as IBM Blue Gene or NEC Tsubasa. Finally, state how the Cloud, Fog, and Edge tiers divide training and low-latency inference.
5. Drawing on *Supercomputers for Linux SysAdmins* Chapter 2, explain why compute racks often occupy less than a quarter of a supercomputer's total floor area, and why they run at 80–100% continuous utilization. Then describe the three physical startup hazards when you power on a cluster after an outage. They are electrical and network request surges, multi-rack disk shelf spin-up torque and controller ordering, and hot-corridor overheating.
6. Write the `pdsh` or `clush` command that uses `grep MemTotal /proc/meminfo | awk '{print $2}'` to audit physical memory across one hundred nodes after boot. Then trace how `filter_nodes_missing_ram()` in `code/part06/flops.py` finds nodes with missing DIMMs within a two percent tolerance. Finally, explain why enterprise GUI suites such as `HP OpenView` and `Zenoss` are not a universal panacea for supercomputer administration. Use *Supercomputers for Linux SysAdmins* Chapters 1 and 2 as your sources.

---

## FILE docs/part-06-hpc-slurm/02-cluster-anatomy-head-login-compute-storage-and-management-nodes.md

Imagine you have been handed the budget to build a new supercomputer cluster from scratch. What do you buy first, how do the pieces connect, and which teams need to be in the room? Following Sergey Zhumatiy's framing in *Supercomputers for Linux SysAdmins*, published by Apress in 2025, a supercomputer is easiest to reason about in four big parts:

---

Login nodes are the front door for users. People connect with `ssh` or a web portal, covered in Chapter 6.25, to edit files, compile code, submit batch jobs with `sbatch`, check queues with `squeue`, and transfer files. Shared software trees on login and compute nodes are often served from read-mostly NFS or CVMFS, and they are exposed through environment modules, as covered in Chapter 6.6. Never share login nodes with control or core service nodes. Enforce strict per-user CPU, memory, and process limits with cgroups and `pam_limits`.

---

As Zhumatiy notes from 2025 cluster operations, many users now run IDE plugins such as VSCode remote. These plugins look like an easy way to work with the cluster. In practice, many of them, VSCode in particular, consume large amounts of CPU and RAM, and they can paralyze a shared login node. Enforce strict per-user resource slices. When your cluster runs several OS versions or heavy software builds, give compilation to separate compilation nodes.

---

If the cluster sits in a remote location, such as a data center colocation facility, start with physical access. Find out how easily your team can get inside and how remote engineers can help. Then decide which tasks they can do for you and which ones your own team must do.

---

## FILE docs/part-06-hpc-slurm/03-parallel-computing-concepts-amdahl-scaling-shared-memory-versus-messag.md

On Monday morning a research team asks why doubling their Slurm allocation from 64 GPUs to 128 GPUs cut their training epoch time by only 25 percent. The same mathematical laws that High-Performance Computing engineers have used for fifty years explain it. Those laws hold whether a parallel job scales from 8 GPUs to 8,000 GPUs.

---

In Chapter 21 of *Supercomputers for Linux SysAdmins*, Zhumatiy explains why administrators need to understand how parallel programming models work. You may never write a fluid-dynamics solver. You will still install the compilers and MPI stacks, and you will read the error logs when a user's job fails to launch.

---

So why not stretch OpenMP across several nodes? Zhumatiy explains that remote memory access over a network is much slower than local RAM access. Separate nodes also lack hardware cache-coherent shared memory. Intel Cluster OpenMP and ScaleMP vSMP both tried to run OpenMP across distributed memory, and both attempts were unsuccessful. Unlike OpenMP, where you only slice the computation, and unlike implicit PGAS languages such as UPC, SHMEM makes you distribute both data and computation explicitly. Nonlocal accesses go through explicit functions, so transfers can be grouped and optimized in hardware. Operational details for OpenSHMEM follow (**untested** here).

---

1. **The bandwidth term barely depends on rank count.** As n grows, `2(n-1)/n` approaches 2M. For a 1 GB tensor on 8 GPUs, each GPU sends 1.75 GB. That makes ring AllReduce bandwidth-optimal for large tensors.
2. **The latency term grows linearly with rank count.** At hundreds or thousands of GPUs, the `2(n - 1)` hops of latency add up. That is why NCCL switches from ring algorithms to double-binary **tree** algorithms, which need only logarithmic latency steps. Part 12 covers the SHARP in-network reductions that tree algorithms use at scale.

---

## FILE docs/part-06-hpc-slurm/04-mpi-in-practice-open-mpi-ranks-collectives-and-tuning.md

When you understand communicators, eager versus rendezvous deadlocks, Open MPI's Modular Component Architecture, HCOLL and UCX transports, NUMA binding, and NCCL interface selection, you can turn a mysterious multi-node hang into a five-minute fix. Keep that list in mind as you read the rest of this chapter.

---

A collective operation involves every rank in a communicator. Each rank must call it in the same order, with compatible counts and datatypes. The table below maps each MPI collective to the distributed AI operation that plays the same role.

---

Here, `-mca pml ucx` selects the **Unified Communication X (UCX)** point-to-point engine. Passing `-x UCX_NET_DEVICES=mlx5_0:1` and `-x HCOLL_MAIN_IB=mlx5_0:1` pins traffic to port 1 of InfiniBand adapter `mlx5_0`. The other three variables switch on hardware features. `HCOLL_ENABLE_MCAST_ALL=1` enables hardware multicast, `HCOLL_ENABLE_NBC=1` enables non-blocking collectives, and `HCOLL_ENABLE_SHARP=1` enables in-network switch reductions. If you suspect a UCX bug, use `-x OMPI_MCA_pml=^ucx` to disable UCX. Run `ucx_info -d` to inspect the RDMA devices UCX detects. Run **`ucx_info -c -f`** to print documented descriptions of every UCX variable, such as `UCX_TLS=rc,sm,cuda_copy,cuda_ipc,gdr_copy`, `UCX_IB_SL=1`, and `UCX_LOG_LEVEL=info`.

---

1. **The native Slurm HPC standard (`srun --mpi=pmix`):** A head node cannot open thousands of sequential SSH connections and still scale. With `srun --mpi=pmix`, `slurmd` on each allocated node spawns `slurmstepd`. That process starts the local tasks and hosts a local **PMIx server** over a Unix domain socket. The ranks publish and exchange endpoint addresses through the Slurm PMIx tree in milliseconds, without SSH. Always pass **`--kill-on-bad-exit=1`**. If one rank crashes with an OOM (exit 137) or a segfault (exit 139), Slurm immediately terminates all the other ranks. Without that flag, 500 GPUs would hang at the next AllReduce barrier (**untested** here).
    
   Check which Slurm PMI plugins are supported with `srun --mpi=list`. After package upgrades, verify that the `slurm-libpmi` and `pmix-libpmi` RPMs have not conflicted.
2. **The standalone Open MPI / HPC-X launcher (`mpirun`):** Use this on bare-metal SSH clusters or inside multi-node Kubernetes MPIJob pods (**untested** here).
    
   Three `mpirun` flags are critical. First, **`-x VAR`** forwards environment variables to remote nodes. Without `-x`, remote ranks never see your `NCCL_DEBUG=INFO` export. Second, **`--bind-to none`** stops Open MPI from pinning a rank, and all of its PyTorch DataLoader worker threads, onto a single CPU core. Third, **`-mca plm_rsh_no_tree_spawn 1`** can resolve intermittent SSH tree-spawn timeouts on slow management networks. Tuning `routed_radix` goes along with it.
3. **The PyTorch elastic launcher (`torchrun`):** It uses PyTorch's built-in `c10d` TCP store, set with `--rdzv_backend=c10d --rdzv_endpoint=10.100.1.10:29500`, and it does not use MPI. The launcher is convenient for elastic cloud jobs. At very large scale, though, funneling thousands of ranks through that single TCP rendezvous endpoint can become a startup bottleneck, compared with Slurm's hierarchical tree.

---

## FILE docs/part-06-hpc-slurm/05-openmp-compilers-and-optimisation-flags.md

Suppose you want to know why more threads help one loop and barely help another. The file `code/part06/omp_scaling.c` answers that with a measurement. Its program allocates three 50-million-element double-precision arrays, 400 MB each and 1.2 GB in total. It initializes them in parallel for NUMA first-touch placement, then runs an untimed warm-up pass. After that it times three kernels across 1 to 8 threads:

---

On a multi-socket server, which Chapter 6.2 covers, physical RAM is split across NUMA domains. NUMA stands for Non-Uniform Memory Access, and the background comes from *Parallel and High Performance Computing* Chapter 14. A Linux kernel rule surprises many engineers. `malloc()` does not allocate physical RAM pages.

---

Consider a program that allocates a 64 GB array in `main()`. It then fills the array with zeros in a single serial loop on Thread 0, which runs on Socket 0. After that, it starts an OpenMP parallel compute loop across Socket 0 and Socket 1.

---

1. Use `triad_bandwidth_gbps(50_000_000, 8, elapsed_ms)` in `code/part06/omp_compilers.py` to compute the achieved bandwidth in GB/s. Do it at 18.1 ms, where one thread gives 66.3 GB/s, and at 14.1 ms, where 8 threads give 85.1 GB/s. Then explain why the triad curve flattens above 2 to 4 threads while `sin * cos` keeps scaling. Finally, explain why leaving out the untimed warm-up pass falsely reported 20 GB/s.
2. Explain why a serial loop on Thread 0 that initializes a shared array causes cross-socket UPI or Infinity Fabric bottlenecks on a dual-socket server. Then explain how parallel initialization with `schedule(static)` fixes it. Next, use `check_hybrid_oversubscription(8, 64, 64)` to show why an 8-GPU node with 64 cores suffers 8.0x thread oversubscription, or 512 threads, when `OMP_NUM_THREADS` is unset.
3. Trace why the unsynchronized `racy++` loop in `omp_race.c` lost 70–80% of its 20,000,000 increments at `-O0`, with results of 6215980 and 3487814. Explain why it passed twice at `-O2` before failing at 17,500,000. Compare `#pragma omp atomic` with `reduction(+ : reduced)`. Then explain how false sharing occurs across 64-byte (x86/Arm) or 128-byte (Apple M-series) cache lines.
4. Using `fp_relative_error_pct()` in `code/part06/omp_compilers.py`, compare the strict `-O3` dot product with the `-O3 -ffast-math` one. The strict result is 2293365.0 at 2.71 GFLOP/s, with 6.25% error against the FP64 reference 2446257.2. The fast-math result is 2445485.5 at 16.29 GFLOP/s, with 0.03% error. Explain why Clang reported `"vectorized loop"` for both builds, even though only `-ffast-math` broke the serial addition dependency chain. Then explain why `y[rep] = dot * 1e-12f` was needed to prevent dead-loop hoisting.
5. Explain why `gcc -lm *.o` can fail while `gcc *.o -lm` succeeds on the GNU single-pass linker. Then explain how `-fleading-underscore`, or `-fno-underscoring` with `iso_c_binding`, and `extern "C"` resolve C, Fortran, and C++ symbol mismatches. Finally, explain how to prevent `Illegal instruction` crashes when login and compute nodes have different CPU generations.
6. Using `flexlm_quorum_and_seat_availability()` in `code/part06/omp_compilers.py`, explain the 15-minute floating seat lease hold, the 50% server quorum rule for 3-server license triads, and MAC address binding. Then distinguish `libcuda` from `libcudart`, and compare package-manager and `.run` CUDA installations. Finally, write the command sequence to reinitialize a hung `nvidia` kernel module, which is `rmmod nvidia; modprobe nvidia; deviceQuery`.

---

## FILE docs/part-06-hpc-slurm/06-environment-modules-spack-and-easybuild.md

Picture a shared GPU cluster that serves fifty researchers. Group A needs GCC 10.4, Open MPI 4.1, and CUDA 11.8 for a legacy molecular dynamics code. Group B needs GCC 15.1, Open MPI 5.0.7, and CUDA 12.6 to compile custom FlashAttention kernels for a foundation model.

---

Compilers and tools read their own variables too. Compilers consult `CPATH`, `C_INCLUDE_PATH`, `LIBRARY_PATH`, and `PKG_CONFIG_PATH`. Python consults `PYTHONPATH`, and CUDA tools consult `CUDA_HOME` and `CUDA_PATH`. A complete software stack therefore means setting several of these variables consistently. It also means reversing every change cleanly when you switch to another version.

---

Zhumatiy explains that the original Environment Modules project, also called Tcl modules or Tcl/C modules, paused after the 3.2.10 release in 2012. Development resumed at the end of 2017, aimed at different technical features. Version 3.2.10 caused two problems in practice. Loading a package failed if another version was already loaded. Tracking dependencies between modules was also hard, for example MPI builds made with different compilers.

---

1. **Automatic replacement of conflicting versions:** Suppose a package already has one version loaded, and you load another. Lmod unloads the old version automatically and prints a version-change message. That stops two compiler versions from being active at once, which would make their runtime libraries conflict.
2. **On-the-fly `MODULEPATH` hierarchies and `inactive` modules:** Lmod changes `MODULEPATH` as modules load. Loading a compiler such as `gcc` adds the directory of packages built with that compiler to `MODULEPATH`. Imagine a cluster with OpenMPI built by two compilers, `gcc` and the Intel Compiler. You load `gcc`, then `openmpi`. When you later unload `gcc`, Lmod sees that `openmpi` is no longer visible, and marks it **inactive**. Its paths leave `PATH` and `LD_LIBRARY_PATH`, but Lmod still remembers `openmpi` in your loaded list. If you then load the Intel compiler module, which has its own `openmpi` in its `MODULEPATH`, **Lmod reloads the Intel build of `openmpi` automatically** and updates your variables.
3. **`module spider` across the whole module tree:** Lmod provides `module spider`, which searches every module in the hierarchy. You can narrow it to one module family, or ask for the prerequisites of an exact version. The output below is **untested** here.
    
4. **Numeric version sorting versus Tcl string sorting (`mkl/11.0` vs. `mkl/4.0`):** If you load a module by name with no version, and no default is set, the highest version is chosen. This is where Lmod and classic Tcl modules differ. Lmod sorts versions as numbers. Classic Tcl modules sort them as strings, so `mkl/4.0` ranks higher than `mkl/11.0`. Lmod also saves and restores module collections with `module save` and `module restore`. It can hide modules for testing, and it supports flexible dependency declarations.

---

## FILE docs/part-06-hpc-slurm/07-slurm-architecture-and-installation.md

Modern supercomputers rarely describe a job that way. Usually a job asks for one type of resource, such as processors or GPUs, and a count of them. Sometimes it also names attributes, such as memory size or the licenses it needs. Because the way jobs launch and get tracked has changed a lot, older control systems often struggle with today's workloads.

---

Every request in Slurm carries an identity. When a user submits a job, when `slurmctld` tells `slurmd` to launch something, or when an admin updates a node, the request arrives with proof of who sent it. By default, that proof is a **munge credential**. Munge is a tiny service that runs on every node, and it does one thing. Any process can ask the local `munged` for a credential. Any other node's `munged` can decode it and report back the *numeric UID and GID of the process that asked for it*. This works provided both nodes share the same secret key and their clocks are within a few minutes of each other. This is how Slurm can trust "user 1042 sent this" without passwords.

---

A recovery after two controllers believed they were primary follows a set order. Stop all but one controller first. Restore `StateSaveLocation` from backup, and start with the default or `-R`. Validate with `squeue` and `sinfo` before you reopen the queue. Have users resubmit what was lost. Then find out why the split happened.

---

Run `sdiag`. Look at "Remote Procedure Call statistics by message type" and by user, and check the scheduler cycle times. Then throttle and cache the polling. Use `sacct` instead of `squeue` for history, use `squeue --noheader` sparingly, and use exporters that poll once. Set `RPC rate limiting` where available, and raise limits only after you have found the source. This is the first failure to expect at scale, so treat the controller as a shared service with an API budget.

---

## FILE docs/part-06-hpc-slurm/08-slurm-configuration-nodes-partitions-and-cgroups.md

Do not guess CPU counts or RAM from a server datasheet. The Linux kernel reserves several gigabytes of RAM for page tables and kernel structures, so `MemTotal` always comes in slightly below the nominal DIMM capacity. Run `slurmd -C` on each node class to print the exact hardware topology that `slurmd` detects (**untested** here).

---

In `slurm.conf`, nodes are declared on `NodeName=...` lines. Do not write one line per node. Group identical nodes with bracket notation, such as `NodeName=gpu[01-32] ...`. Use **`NodeName=DEFAULT`** to set shared attributes for every later `NodeName` line, until the next `DEFAULT` line appears. You can also define a **`NodeSet`** alias to shorten node lists inside partition definitions. *Supercomputers for Linux SysAdmins* shows this form in Chapter 15:

---

Consider a 16-node job on an InfiniBand or RoCE fat-tree fabric. If Slurm places all 16 nodes under one leaf switch, their collective traffic stays on that switch, one hop away. It never congests the spine uplinks. In Chapter 15, Zhumatiy shows how to make Slurm aware of this. You set `TopologyPlugin=topology/<type>`, where the type is `default`, `block`, `3d-torus`, or `tree`. The layout goes in `topology.conf`, or in the newer `topology.yaml`.

---

The table splits the work in two, so you can see which setting solves which problem. If your controller slows down during a submit storm, you know which rows to read first. If you need every node ready before a job starts, the `PrologFlags` rows are where you look. `PrologFlags` controls when prologs run and how jobs are contained. `SchedulerParameters` controls how often the scheduler runs and how much work each pass does.

---

## FILE docs/part-06-hpc-slurm/09-slurm-accounting-and-scheduling-policy-qos-fairshare-backfill-preempti.md

A GPU cluster is shared and expensive, so somebody has to decide who gets it next. That decision is the scheduler's policy, and it is where organisational choices become code. The policy decides who gets priority before a deadline. It decides how a team that bought 64 GPUs is guaranteed them, and whether idle capacity can be borrowed. It also decides how one user is stopped from queueing 10,000 jobs, and how much each group is charged.

---

Every job runs under an association, and `AccountingStorageEnforce` decides how strictly Slurm checks that. If it includes `associations`, a user with no association cannot run. `limits` implies associations and enforces the limits on associations and QOS. `qos` requires a valid QOS. `safe` launches a job only if it can finish within a TRES-minutes limit. `nojobs` and `nosteps` turn accounting off for jobs and steps, according to the `slurm.conf` man page. The 6.7 starter config uses `associations,limits,qos`.

---

A **QOS** is a named policy object that a job requests, for example with `--qos=high`. A QOS bundles several things. It has a **priority**, an integer that feeds the QOS factor. It has **limits**, which use the same Grp and Max families at QOS scope. It defines **preemption** relationships and mode, a **usage factor** that scales billing, and a **grace time** for preemption. It also carries **flags**. The usage factor works like this: 0.5 suits a cheap scavenger QOS, and 2 suits an expensive urgent one.

---

1. Create one account per team, with `fairshare` set in proportion to what it bought. Use Fair Tree, the default, with a decay half-life of 14 days.
2. Define three partitions. `gpu` covers all nodes, is the default, and has `MaxTime=2-00:00:00`, `DefMemPerGPU` and `DefCpuPerGPU`. `debug` covers a few nodes, has a 30 minute limit, and sits in a high tier. `long` is limited to approved accounts, has `MaxTime=14-00:00:00`, and carries a lower weight.
3. Define three QOS. `normal` has priority 100, `MaxTRESPerUser=gres/gpu=64` and `MaxSubmitJobsPerUser=500`. `urgent` has priority 1000 and usage factor 2. It is approved through `AllowQos`, and it preempts `scavenger`. `scavenger` has priority 0, a usage factor of 0 or 0.1, requeue, a grace time of 120 s, and `NoReserve`, so it never blocks planning.
4. Impose hard budgets only where a contract requires them, using `GrpTRESMins` with `safe`. Otherwise, rely on fair-share.
5. Set the weights: `PriorityWeightFairshare=100000`, `PriorityWeightQOS=50000`, `PriorityWeightAge=1000` (with `PriorityMaxAge=7-0`), `PriorityWeightPartition=10000`, `PriorityWeightJobSize=0` so that job size does not distort the order, and `PriorityWeightTRES=gres/gpu=100`. Use `sprio` to check that an urgent job from a heavy user outranks a normal job from a light user, if that is the intent.
6. Use `sched/backfill`, set `bf_window` to the longest limit, set `bf_max_job_user=100`, and enable `bf_continue`.
7. Bill with `TRESBillingWeights=GRES/gpu=10,CPU=1,Mem=0.1G` and `PriorityFlags=MAX_TRES_GRES`, so that GPUs dominate the cost.
8. Report with `sreport cluster AccountUtilizationByUser`, `sreport cluster utilization` and `sacct -X --format=...` for the monthly chargeback. Review the wait time for each QOS.
9. Run a monthly policy review that compares waiting times and utilisation. Do not tune weights ad hoc during a crunch.

---

## FILE docs/part-06-hpc-slurm/10-slurm-gpu-scheduling-gres-nvml-autodetect-mig-and-device-constraints.md

Typing out every device by hand is slow and easy to get wrong. `AutoDetect` in `gres.conf` asks slurmd to discover the hardware for you. The man page lists these values for the current development version. `nvml` covers NVIDIA GPUs through the NVIDIA Management Library, and it needs Slurm built with NVML support and the library present. `nvidia` covers NVIDIA GPUs without a library. It "doesn't detect MIGs or NVlinks", and it was added in 24.11. `rsmi` and `amd` cover AMD GPUs. `oneapi` covers Intel. `nrt` covers AWS Trainium and Inferentia. `full` tries all of these in order, and `off` turns detection off.

---

Set `Type` to the product name, such as `h100`, `a100` or `l40s`. Users can then ask for a specific model with `--gres=gpu:h100:4`, and mixed clusters stay schedulable. Keep type strings short and stable. Once they appear in accounting and user scripts, they are hard to rename. The MIG profile docs say a type may be requested as a substring-compatible token.

---

MIG gives you strong isolation and predictable performance. The costs are that it is static, and that it fragments. A 3g.20gb instance, for example, cannot be merged with another instance. MIG instances also have no NVLink or multi-GPU use, and some CUDA features are limited.

---

3. You can profile GPU compute against `ncclAllReduce` communication. When GPU utilisation looks high but step throughput is slow, the cause may be NCCL polling loops, which spin CUDA kernels at 100% utilization. Wrap 5 training steps in `torch.profiler.profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA], record_shapes=True, profile_memory=True, with_stack=True)`. Put `record_function("forward")`, `record_function("backward")` and `record_function("optimizer")` around the matching parts. Export the Chrome trace only on rank 0, with `if dist.get_rank() == 0: prof.export_chrome_trace("trace.json")`. Then print `prof.key_averages().table(sort_by="cuda_time_total", row_limit=10)`. If `ncclAllReduce` dominates `cuda_time_total`, you have an inter-node communication bottleneck. The remedies are a larger micro-batch size, gradient accumulation, or overlapping communication with computation. For lower-level transport diagnostics, enable `export NCCL_DEBUG=INFO`, `export NCCL_DEBUG_SUBSYS=ALL` and `export TORCH_DISTRIBUTED_DEBUG=DETAIL` selectively. Run this profile before you change the model code, because it shows whether the time goes to compute or to communication.

---

## FILE docs/part-06-hpc-slurm/11-submitting-and-launching-jobs-sbatch-srun-salloc-arrays-dependencies.md

A batch job is a request you queue with `sbatch script`. When resources are free, Slurm runs your script on the first allocated node, as the batch step. Commands in the script run only on that node, unless you launch them across the allocation.

---

A job step is started by `srun ...`. It launches tasks across all or part of the allocation. A batch script usually contains one or more `srun` steps. Each step gets an ID such as `JOBID.0` or `JOBID.1`, and accounting records every step.

---

`srun` launches a step, which is one parallel run inside an allocation. It connects to the allocation, or creates one if none exists. It starts the requested number of tasks on the nodes, forwards stdin, stdout and stderr, and returns the exit status. The key options come from the `srun(1)` man page. They include `-n/--ntasks`, `-N/--nodes`, `--ntasks-per-node`, `-c/--cpus-per-task`, `--cpu-bind`, `--mem-bind`, `--gpu-bind` and `--gpus-per-task`. Others include `--mpi=<type>`, where `list` shows plugins and `pmix` and `pmi2` are common, plus `--export`, `-K/--kill-on-bad-exit`, `--label` (which prefixes output with the task id), `--output/--error` per-step patterns, `--time`, `--wait` and `--pty`.

---

By default, `salloc` runs its own shell on the submission host, which is the login node. Many sites prefer a shell on the compute node instead. The current way to get one is `LaunchParameters=use_interactive_step` in `slurm.conf`. With it, `salloc` starts `srun` with `InteractiveStepOptions`, so you land on a node of the allocation. The default for `InteractiveStepOptions` is `--interactive --preserve-env --pty $SHELL`, according to the man page. The interactive step consumes no resources, so other steps can run in parallel with it. The old `SallocDefaultCommand` parameter no longer appears in the `slurm.conf` man page.

---

## FILE docs/part-06-hpc-slurm/12-multi-node-training-on-slurm-pmix-torchrun-nccl-environment-binding-to.md

Slurm sees one task per node in this style, and torchrun starts the eight local ranks. The benefit is that torchrun adds elastic features, such as restart on failure and rendezvous. It also sets all the variables, so the script does not depend on the launcher. The costs are coarser per-rank binding and GPU isolation, because Slurm sees one task per node. Process monitoring belongs to torchrun, and `--cpus-per-task` must cover all 8 ranks.

---

Set only the minimum. Default detection is usually right on a well-built node. Put site-wide settings in one file, either `NCCL_CONF_FILE` or `/etc/nccl.conf`, or in the module, so users do not paste folklore into their scripts. Re-verify every variable against the NCCL version you run. The guide gives a "since" note for each variable, and some variables have been renamed.

---

PyTorch adds variables of its own: `TORCH_NCCL_ASYNC_ERROR_HANDLING`, `TORCH_NCCL_BLOCKING_WAIT`, process-group timeouts (`init_process_group(timeout=...)`), and flight-recorder settings. Their names vary by version, so check them. A short timeout turns a silent hang into a crash with a stack trace, which is what you want in production.

---

Work from small to large. If you can reproduce the problem on 1 node, try 2 nodes next. Run `nccl-tests` with `srun` on the same allocation, using `all_reduce_perf -b 8 -e 8G -f 2 -g 1` (untested here). That separates fabric problems from application problems, covered in 6.28. Compare the result with the baseline bus bandwidth for your node type, and bisect by node subsets.

---

## FILE docs/part-06-hpc-slurm/13-containers-on-slurm-enroot-and-pyxis.md

pyxis is the complementary Slurm plugin. It adds useful flags to `srun`, and it runs the container through enroot for you, so you never call enroot yourself. Both projects come from NVIDIA, so only NVIDIA GPUs are well managed when you use them. The book calls this technology really easy to use. It adds minimum overhead compared with the other options.

---

Use `srun --mpi=pmix` with a container whose MPI is PMIx-aware and compatible with the host's PMIx and Slurm. The pyxis README notes that support for PMI2 and PMIx "requires Slurm support". The `50-slurm-pmi.sh` hook forwards the PMIx variables and socket into the container. NGC images ship HPC-X with PMIx support. A mismatch between the container's PMIx and the host's causes launch failures at `MPI_Init`. Section 11 of chapter 6.4 covers that failure. NCCL inside the container uses the injected host IB libraries and devices.

---

A local registry mirror or pull-through cache is the next option. Harbor, Artifactory, a registry:2 mirror, or the docker-registry-proxy project can fill this role. The docker-registry-proxy project is the one recommended in chapter 16 of *Supercomputers for Linux SysAdmins*, under Caching. Here is why a mirror matters. When processes start a container directly from a registry, every node downloads, unpacks and converts the layers at the same time. Take 64 nodes pulling a 15 GB image. Over a 10 GB/s uplink, that takes 96.0 s. A single central import takes 1.5 s. A generic HTTP proxy is a poor fit, because Docker registries require token authorization, and you must not cache mutable image manifests for long periods. The docker-registry-proxy project handles registry authentication. It caches immutable layer blobs and keeps manifest checks fresh. Pair this with encouraging users to pre-import `.sqsh` images onto the shared filesystem, and turn on the Enroot/Charliecloud layer caches.

---

Start with the self-checking Python lab, `code/part06/enroot_pyxis_lab.py`. It covers these checks. It verifies the enroot `docker://REGISTRY#REPO:TAG` URI format. It checks the `#` escaping in `#SBATCH --container-image`, written as `nvcr.io\#nvidia/pytorch:24.07-py3`, and the `.sqsh` naming, which gives `nvidia+pytorch+24.07-py3.sqsh`. It also tests the pyxis `--container-mounts=SRC:DST[:FLAGS]` parser, comparing `ro+rprivate` with the default `rw`. Last, it calculates the registry thundering-herd pull penalty: `96.0 s` for 64 nodes pulling 15 GB over 10 GB/s, against `1.5 s` for a single central squashfs import.

---

## FILE docs/part-06-hpc-slurm/14-slurm-operations-prolog-epilog-health-checks-drain-reason-codes-troubl.md

A health check is a script that Slurm runs on a schedule, as root, on compute nodes. Slurm runs the script but does not judge its output. The program decides what counts as a failure and what to do about it. `HealthCheckProgram` names the script, and `HealthCheckInterval` sets how often it runs. The default interval is 0, which leaves the check disabled. `HealthCheckNodeState` chooses which node states get checked, and its default is `ANY`. Other values include `ALLOC`, `IDLE`, `MIXED` and `CYCLE`. With `CYCLE`, the runs are spread across the interval instead of hitting every node at once. That avoids a thundering herd against shared storage.

---

Stuck jobs show up in other states too. A job that sits in `COMPLETING` for a long time has an epilog that is running or hung, an unkillable step, or an unreachable node. Check `scontrol show job` and `sinfo` for the nodes involved. A job that stays `PENDING` forever is covered in 6.9, section 8. A job that is `RUNNING` but makes no progress usually means a hang on the user's side. Check GPU utilisation with `srun --overlap --jobid=ID nvidia-smi`, read the NCCL logs, or dump the Python stacks with `py-spy dump`.

---

The `Remote Procedure Call statistics by user` section shows who is sending those requests. In the sample, `root (0) count:728986 ave_time:10228 total_time:456422703` appears next to `user1 (25002) count:29784 ave_time:13439 total_time:269036`. A single user running `squeue` in a tight loop is the classic cause of a sluggish controller under a request storm. Check the backfill cycle mean and maximum times and depth as well, as covered in 6.9. Then use `max_rpc_cnt`, and the `defer` options `salloc_wait_nodes` and `sbatch_wait_nodes`, in `SchedulerParameters` to protect the controller. Teach your users not to run `watch -n1 squeue`. Offer `squeue` caching or a read-only web dashboard instead.

---

Tell users what is happening. A status page, a message of the day with maintenance notices, clear reason strings and documentation for common errors all help. For each alert, write a runbook with commands and an escalation path. Practise failure drills, such as killing slurmd, filling a disk or unplugging a node.

---

## FILE docs/part-06-hpc-slurm/15-slurm-high-availability-upgrades-and-scaling.md

When `slurmctld` is down, running jobs keep going, because the `slurmstepd` processes on the nodes carry on without it. No new jobs start, and commands like `squeue` fail. Job completion messages wait on the nodes and are delivered when the controller returns, and node health checks keep running locally. If the outage exceeds `SlurmdTimeout`, nodes are marked down only after the controller is back and notices they stopped responding. A controller restart does not kill jobs by itself.

---

Each release is supported for about 18 months. The guide warns that "Upgrades from incompatible versions will fail immediately upon startup." Upgrading outside the window also kills running jobs and loses job accounting. Out-of-window upgrades must therefore go in steps, and you verify each step.

---

Set `SlurmdTimeout` to 120 s or more on very large clusters. Communication happens at half of it. Keep `MinJobAge` as small as practical for high job rates. Make `EioTimeout` larger for a big `srun`, and use `EpilogMsgTime` to spread completion messages when large jobs end.

---

1. Freeze new submissions, or set a maintenance reservation with `flags=maint,ignore_jobs`. Existing multi-day training jobs keep running on compute nodes. `slurmd` keeps running active job steps unattended while `slurmctld` restarts, provided the outage stays shorter than `SlurmdTimeout`.
2. Back up `slurmdbd` first with `mysqldump --single-transaction --Quick slurm_acct_db > pre_upgrade.sql`. Then upgrade the `slurmdbd` package and start `slurmdbd`. Watch `/var/log/slurm/slurmdbd.log` until the database table conversion completes. On tables with millions of historical jobs, that can take several minutes. Confirm that `sacctmgr show cluster` responds cleanly.
3. Stop both the backup and the primary `slurmctld` daemons. Then tar the whole `StateSaveLocation` directory with `tar -czf /var/backups/slurm_state_pre_upgrade.tar.gz -C /var/spool/slurmctld .`. If a catastrophic bug forces a rollback, you have what you need. You can stop the new daemons, restore the SQL dump and state directory from the exact pre-upgrade second, and start the old binaries cleanly.
4. Upgrade and start `slurmctld`, primary first and then the backup. Verify with `scontrol ping` and `squeue` that all running jobs survived intact. Then roll out the new `slurmd` and client packages across compute and login nodes, and recompile SPANK plugins such as Pyxis against the new Slurm headers.

---

## FILE docs/part-06-hpc-slurm/16-slurm-on-kubernetes-slinky-and-soperator.md

Health checks come in two forms. Passive checks watch control-plane signals and node conditions, such as NVMe health. Active checks come from `ActiveCheck` custom resources, which run scheduled probes as either Kubernetes Jobs or Slurm jobs, on some or all nodes. The probes cover GPU performance, the system, storage, network and InfiniBand, and hardware acceptance. A failed node is drained and replaced automatically. Checks are deployed through GitOps with Flux as a Helm chart, and cluster owners can customise them.

---

The script checks Slinky's `NodeSet` drain and cordon logic. It exercises the scale-in state machine in `reconcile_slinky_node_drain` and proves that pod deletion waits for `DRAINED`. It also shows that the function never overwrites or clears an external admin or health-check drain reason, one without the `slurm-operator:` prefix. Next, it validates Slinky's 6 CRDs (`Controller`, `NodeSet`, `LoginSet`, `Accounting`, `RestApi`, `Token`) and the RWX PVC HA requirement. Last, it checks Soperator's `SlurmCluster` model, with its `Login`, `Controller` and `Worker` groups, the shared `jail`, and `ActiveCheck` in both `k8sJob` and `slurmJob` form.

---

Suppose your team moves a GPU training job from bare-metal Slurm into Slurm on Kubernetes. The first worry is simple: will `slurmd` inside a pod slow down multi-node training? The answer depends on how the `slurmd` worker PodSpec is configured on the Kubernetes nodes underneath. An untuned default pod uses virtualized bridge networking (`veth` pairs with a CNI overlay), time-sliced CFS CPU scheduling and default `memlock` ulimits. Those defaults cripple GPUDirect RDMA and add millisecond-level jitter to AllReduce collectives. To reach bare-metal parity inside a `slurmd` worker pod, verify these five pod and kubelet invariants.

---

1. **Guaranteed Pod QoS Class and Kubelet `static` CPU / Topology Manager.** Every `slurmd` worker pod on a GPU node should request and limit the same integer CPU, memory and `nvidia.com/gpu` resources, or a privileged device, so Kubernetes assigns the Guaranteed QoS class. Pair that with kubelet `cpuManagerPolicy: static` and `topologyManagerPolicy: single-numa-node`, or `best-effort` at `pod` scope. The pod's CPUs, host memory, GPUs and RDMA NICs then stay pinned, free from interference by background node agents.
2. **Unlimited locked memory (`ulimit -l unlimited` / `RLIMIT_MEMLOCK`).** InfiniBand and RoCEv2 GPUDirect RDMA require pinning large memory regions in RAM and GPU BAR space (`ibv_reg_mr`). If the container runtime (`containerd`) applies a default `64 KB` or `64 MB` `memlock` limit to the `slurmd` container, multi-node NCCL jobs launched via `srun` inside that pod fail immediately during communicator initialization. Configure `containerd`, or the pod's security context or privileged container entrypoint, so that `ulimit -l` inside `srun` job steps reports `unlimited`.
3. **Direct RDMA / InfiniBand device passthrough (`hostNetwork` or SR-IOV / RDMA CNI).** For GPU-to-GPU traffic across nodes to bypass the kernel TCP/IP stack, the `slurmd` worker pod needs direct access to `/dev/infiniband/uverbs*` and `/dev/infiniband/rdma_cm`. You can grant it through the NVIDIA Network Operator, an RDMA shared device plugin or SR-IOV VF passthrough, with the `IPC_LOCK` capability. The pod must then either run with `hostNetwork: true` on the compute fabric, or attach secondary high-speed RDMA interfaces through Multus CNI.
4. **Shared `/dev/shm` sizing (`emptyDir: {medium: Memory}`).** PyTorch `DataLoader` multi-processing workers and NCCL intra-node shared-memory channels allocate gigabytes of POSIX shared memory in `/dev/shm`. By default, Kubernetes mounts `/dev/shm` with a tiny `64 MiB` cap. That makes multi-GPU PyTorch jobs crash on step 1 with `Bus error (core dumped) — Insufficient shared memory`. Mount a memory-backed `emptyDir` (`medium: Memory`, `sizeLimit: 64Gi` or `128Gi`) at `/dev/shm` on every `slurmd` worker pod.
5. **Coordinated drain state machine (`slinky_soperator_lab.py`).** Two control planes now watch the same physical node. Kubernetes must never let `kubectl drain` or a cluster autoscaler scale-in abruptly `SIGKILL` a `slurmd` pod in the middle of a 64-node training job. As verified in `code/part06/slinky_soperator_lab.py`, the operator intercepts node cordoning and pod deletion through PodDisruptionBudgets and finalizers. It sets the Slurm node state to `DRAIN` with `Reason="slurm-operator: node-cordoned"`. It waits until all active Slurm jobs on that pod complete and reach `DRAINED`, and only then permits pod eviction. It also keeps a manual administrator hardware drain, such as `Reason="Xid79 GPU3 ticket INC123"`, intact across Kubernetes uncordons.

---

## FILE docs/part-06-hpc-slurm/17-other-schedulers-pbs-torque-lsf-and-flux.md

Torque came out of the old Maui/Torque stack. Its origins are Cluster Resources and Adaptive Computing. Torque has the same lineage as PBS, and it forked OpenPBS 2.3.12. It uses `qsub -l nodes=2:ppn=16`, `pbs_server` and `pbs_mom`. For policy, it uses the Maui or Moab scheduler, because Torque's built-in scheduler is basic.

---

The tool does not translate some things on purpose, so you must handle them by hand. Heterogeneous `select` requests with `+` chunks are flagged as TODO. So is vnode-specific placement, and custom resources map to Slurm features, licenses or GRES. Hooks need rewriting as `job_submit` plugins. Queue policy, such as fair-share and limits, must be rebuilt as described in 6.9. Job IDs in dependencies, the interactive behaviour of `qsub -I` and the MPI launch line also need manual work. Replace `mpirun -machinefile` with `srun`. Finish by running the result through `sbatch_lint.py`, covered in 6.11.

---

1. Start with an inventory. List your queues, node classes, resource types, limits, fair-share trees, reservations, hooks or plugins, license servers and user scripts. Scan the scripts with `grep -r '#PBS'` or `'#BSUB'`. Then list the accounting integrations, web portals and workflow tools that call `qsub` or `bsub`.
2. Map the policies next. Queues become partitions or QOS, and limits become association or QOS limits. Fair-share shares become accounts. Preemption rules move to `PreemptType` (6.9), and custom resources become GRES, features or licenses. Hooks become `job_submit` and prolog or epilog scripts (6.14).
3. Translate the scripts, first with the automated pass and then with review. Build a compatibility shim only if you cannot avoid one. Slurm ships `qsub`-like wrappers in contribs, and PBS-compatible wrappers exist. Check which ones are available for your version.
4. Keep accounting continuous. Export the historical usage, seed fair-share if you want to, and keep the old reports for audits.
5. Run a parallel pilot. Split the nodes, dual-submit tests and compare the job outcomes. Train users and publish a command-map cheat sheet.
6. Cut over in node groups. Keep a rollback window, and decommission the old scheduler only after one full allocation cycle.
7. Revisit the workflow layer, such as Airflow, Nextflow or Snakemake DAGs. These usually have a Slurm executor already.

---

1. Run `pbs2slurm.py` on two of your own PBS scripts. Fix every TODO by hand, then lint the results with `sbatch_lint.py`.
2. Install OpenPBS in a single-node container or VM. Submit a `select` job, then inspect `pbsnodes -a` and `qstat -f`.
3. Install Flux with `flux start --test-size=4` in a container. Run `flux batch` with nested `flux run`, then use `flux proxy` and `flux uptime` to observe the depth.
4. Write the command-map cheat sheet for your site.
5. Draft a migration inventory template that lists every item in section 7, step 1.
6. Extend the converter to handle Torque-style `-l nodes=2:ppn=16` requests and heterogeneous select.

---

## FILE docs/part-06-hpc-slurm/18-parallel-storage-concepts-and-the-limits-of-nfs.md

Training reads datasets, writes checkpoints and logs, and loads Python environments, all from shared storage. A different failure looks just as bad. A data loader starves for files, or a thousand ranks import Python packages at the same moment and bring the metadata server to its knees. Storage design is one of the highest-leverage and most misunderstood parts of an AI cluster.

---

The consistency model is the part that surprises people. NFS provides *close-to-open* consistency, not strict POSIX coherence. A client caches attributes (`actimeo`, `acregmin/max`) and data. A write becomes visible to another client only after the writer closes the file and the reader opens it. Suppose two nodes append to the same log file, or one node polls a status file that another keeps writing. The reader can see stale data. Parallel I/O libraries, some build systems and `tail -f` across nodes all depend on immediate visibility, so they misbehave. Using `noac` or `lookupcache=none` fixes the correctness problem, but at a large cost.

---

1. Install the `nfs-server` package, or a similar one, and `portmap` if your system needs it.
2. Start the `portmap` and `nfsd` services, and include them in the services that start at boot.
3. Export `/home` to the clients on the `10.0.0.0/8` network by adding `/home 10.0.0.0/8(rw,no_subtree_check)` to `/etc/exports`.
4. Run `exportfs -ra` to apply the change.

---

1. Run `python3 code/part06/iomix_lab.py`. Then use `ckpt_bytes(params, 14)`, `need_gbs(size, 60)` and `overhead(size, 10, 3600)`, which come from `code/part06/ckpt_math.py`, to check two results that you can verify yourself. First, a `70B` mixed-precision Adam checkpoint of `0.98 TB` needs `16 GB/s` to write in 60 seconds. On a `10 GB/s` NFS server it wastes `98 s`, which is `2.7%` of an hour. Second, a `405B` checkpoint of `5.67 TB` needs `94 GB/s`. At `10 GB/s` it wastes `567 s`, or `15.8%` of every hour.
2. Run `python3 code/part06/iomix.py --mb 64 --files 2000`. Explain why sequential read bandwidth (`11,562 MB/s` in the laptop run) exceeds physical SSD write bandwidth (`633 MB/s` `fsync`'d). Explain why `create` (`4,585 files/s`) is roughly $80\times$ slower than cached `stat` (`378,127/s`). Then describe how you would defeat OS page-cache inflation during storage benchmarks.
3. Using chapters 9 and 28 of *Supercomputers for Linux SysAdmins* as your guide, configure an NFS server and its client mounts. Write the `/etc/exports` entries `/export/dir host1,host2,host3(rw,root_squash)` and `/home 10.0.0.0/8(rw,no_subtree_check)`. Write the `exportfs -ra` command and the `showmount -e/-d/-a` commands. Write the client `/etc/fstab` mount line with `rw,noatime,nodiratime,vers=4.2,rsize=1048576,wsize=1048576,nconnect=8,hard`. Then explain the trade-offs of `root_squash` against `no_root_squash`, `sync` against `async`, and `hard` against `soft`.
4. Harden cluster time synchronisation with `ntpd`, `chrony` and `systemd-timesyncd`, following chapter 9 of *Supercomputers for Linux SysAdmins*. Write `/etc/ntpd.conf` for a cluster service node, with `listen on 10.1.2.251` and `restrict default kod nomodify notrap nopeer noquery`. Explain each of the five `restrict` flags. State why `ntpdate` (or `chronyd` with `iburst`) is needed before mounting parallel filesystems after a cold boot with a large clock offset. Finally, write the `timedatectl show-timesync --all` verification command.
5. Compare dataset streaming bandwidth for pre-tokenized LLM text and for raw computer vision data. Using `iomix_lab.py`, calculate the aggregate cluster read bandwidth for two cases. In case (a), 4,096 GPUs train on pre-tokenized text at `3,000 tokens/s/GPU` and `4 bytes/token`, which is `49 MB/s`. In case (b), 500 nodes train a vision model at `2,000 images/s/node` and `150 KB/image`, which is `150 GB/s`. Explain why converting millions of small JPEG files into WebDataset `.tar` shards solves both the metadata and the bandwidth bottlenecks.
6. Design a four-tier storage architecture for a 2,048-GPU AI cluster. Specify the storage technology, the capacity and bandwidth targets, and the data lifecycle policies that you would use for four tiers: (a) `/home` and `/opt` software trees, (b) `/scratch` and active training datasets, (c) a node-local NVMe burst tier for asynchronous checkpointing and Enroot `ENROOT_DATA_PATH`, and (d) a cold S3 object archive.

---

## FILE docs/part-06-hpc-slurm/19-lustre-architecture-and-operation.md

Those strengths come with sharp edges. Striping defaults can cap the bandwidth of a big checkpoint at one disk. A metadata service can be overwhelmed by a data loader. Failures can look like hung nodes. Operators who understand striping, metadata and the management tools can prevent and diagnose most "storage is slow" tickets.

---

This chapter builds on earlier material, so check these first. Chapter 6.18 covers parallel storage concepts. Part 2 covers LNet, which runs over IB and Ethernet. Part 1 covers block devices and the ldiskfs and ZFS back ends. When you finish, you should be able to do the following:

---

Formatting is only half the job. Next, mount each target on its server, starting with the MGS and MDT and then the OSTs. Mount `/dev/sda1` as `/mnt/mdt` with `mount -t lustre /dev/sda1 /mnt/mdt`. Clients mount last, using `mount -t lustre mgsnode@tcp:/testfs /mnt/testfs`. For failover, the list of MGS NIDs can be separated by `:` or `,`.

---

Run the self-checking Python lab locally before you touch a cluster. It needs no Lustre file system, so you can check the math first. The lab, `code/part06/lustre_stripe_lab.py`, verifies `slot()`, `per_ost_bytes()`, `request_osts()` and `pfl_layout()` in `code/part06/lustre_stripe.py`. It also checks the Supercomputers for Linux SysAdmins Chapter 9 OSS RAM sizing equations, the LNET port, and the stripe size. The expected results are:

---

## FILE docs/part-06-hpc-slurm/20-beegfs-gpfs-wekafs-and-vast.md

Be careful with the numbers in the NVIDIA-DevOps volume-15 chapter. Its figures, "50K to 100K ops/s per metadata server" and "500 MB/s to 2 GB/s per storage node", are illustrative. Its sample `beegfs-client.conf` also contains parameters such as `tuneUseGDTLSConnPool` and similar parameters that do not appear in the default configuration file in the repository. Trust the shipped config files over a sample when you set your client configuration.

---

Behind the flash tier, WEKA can tier to S3-compatible object storage for capacity. It also offers snapshots, snap-to-object, filesystem groups and quotas for multi-tenancy, and encryption. Its cost model combines a software licence, priced by capacity or cores, with NVMe server hardware. WEKA is strong on performance per rack, but it is costly per TB at pure flash.

---

Chapter 9 also surveys other distributed file systems that run on Linux. They include Gluster (GlusterFS), Coda, CEPH (CephFS), Hadoop HDFS, MooseFS and zFS. The zFS in this list is the IBM z/OS distributed file system, so do not confuse it with OpenZFS. The chapter warns against adopting general-purpose or non-POSIX file systems blindly for HPC and AI compute scratch. Such file systems may lack strict POSIX compliance, high-concurrency lock scaling or production stability under thousand-node load.

---

Most HPC and AI access goes through NFS, including NFS over RDMA and multipath, `nconnect`-style client mounts. SMB, S3 and a database and analytics interface are also available. A VAST client handles multipathing, and a POSIX-like kernel client is not required. The chapter sums this up as "enterprise NAS speed with parallel-file-system bandwidth".

---

## FILE docs/part-06-hpc-slurm/21-parallel-i-o-and-checkpoint-patterns.md

Suppose many ranks each need to write their piece of one large array into the same file. If every rank works on its own, the file system spends its time sorting out scattered writes. The HPC world avoids that with a layered stack, which *Parallel and High Performance Computing* (chapter 16) describes. Each layer hands its work down to the layer below.

---

OpenMPI has two MPI-IO plugins, and the choice matters. Parallel file operations entered MPI in the MPI-2 standard in the late 1990s, through Argonne National Laboratory's ROMIO library, which Rajeev Thakur led. In OpenMPI, `ompi_info | grep "MCA io:"` lists two MCA `io` plugins. One is `romio321`, the default on older releases. The other is `ompio`, the default on newer OpenMPI releases. You select one with `mpirun --mca io [ompio|romio]`.

---

As an example, consider a tiny batch size of 1 MB and a target of 1,000 batches per second. That is roughly 1,000 MB/s. Copying it with the CPU would consume a few cores. With GDS, the GPU pulls that data straight from disk and frees the CPU. The gap grows at higher rates and with thousands of GPUs.

---

Curator also enforces quality. It deduplicates data and removes problematic content, which matters for both model quality and speed. A clean, preprocessed dataset gives the trainer well-structured, evenly sized data, padded to a fixed length. It never has to tokenize on the fly or handle messy strings. Once Curator does the heavy work offline, the online pipeline only reads prepared data and maybe does a light last-mile shuffle.

---

## FILE docs/part-06-hpc-slurm/22-provisioning-with-pxe-ipxe-dhcp-tftp-and-image-management.md

Hand-editing DHCP files for a thousand nodes is how typos reach production. You can avoid that by generating every file from one inventory. The script `code/part06/gen_provision.py` reads an inventory CSV with the columns `name,mac,ip,bmc_mac,bmc_ip,role,image`. It validates each row for hostname syntax, MAC syntax, subnet membership and duplicates. Then it writes a `dnsmasq.conf`, one iPXE script per node, and a `boot.ipxe` dispatcher.

---

PelicanHPC, also called Parallel Knoppix, is a Debian-based distribution that runs from a LiveCD or LiveUSB. You usually do not install it on the head node or the compute nodes. It suits a quick, temporary cluster in a classroom or workstation room. It is not meant for a cluster that runs permanently.

---

Several causes come up again and again. Two DHCP servers can answer the same node. A PXE client sent to a relay that drops option 60 or option 93 can fail to boot. The boot order can put disk ahead of network after the first install, so the node never reimages. You set that order with IPMI `chassis bootdev pxe options=efiboot` or with Redfish `BootSourceOverrideTarget`.

---

What has been tested: the generator ran on the sample inventory and on the broken one. Two extensions remain. Extend `validate()` so that it checks that BMC IPs sit in a different /16 than node IPs, and that role values come from an allowed list. Add a `--check` mode that only validates.

---

## FILE docs/part-06-hpc-slurm/23-xcat-warewulf-and-cluster-managers-compared-with-bcm.md

Picture a new GPU node arriving at the data center. Someone has to record its MAC address, give it a boot image, power it on and confirm that it comes up healthy. Chapter 6.22 explained the mechanisms behind that work. A cluster manager packages those mechanisms into one tool. It covers the node database, the DHCP, TFTP and HTTP services, image build and distribution, power and console control, discovery, health, user and software management, and integration with Slurm or Kubernetes.

---

Chapters 26 and 28 of the Supercomputers for Linux SysAdmins book install xCAT on a Red Hat or CentOS management server. You point the package manager at the `xCAT-core.repo` and `xCAT-dep.repo` files under `/etc/yum.repos.d/`. Then you run `yum install -y xCAT` and `source /etc/profile.d/xcat.sh`, which puts the `/opt/xcat` binaries in your `PATH`. `(untested here)`

---

4. Populate `litefile` with writable RAM paths using `tabedit litefile`. The NFS root is read-only, so services need a place to write their runtime state. The book recommends adding at least these 15 entries, so services can write to `tmpfs` `(untested here)`:

---

For customization at first boot or after it, put your scripts in `/install/postscripts/`, for example `/install/postscripts/mypost`. Attach a script to a node with `chdef node1 -p postbootscripts=mypost`, which stores it in the `postscripts` table. xCAT then renders `/tftpboot/mypostscripts/mypostscript.<node_name>` from `/opt/xcat/share/xcat/mypostscript/mypostscript.tmpl`.

---

## FILE docs/part-06-hpc-slurm/24-users-ldap-sssd-quotas-and-accounting-at-scale.md

Basic data, such as uid, gid, home directory and shell, must match everywhere. Quotas, access limits and similar information can be stored and synchronised separately, and they may legitimately differ by node type. The book gives a pointed example. CPU time limits should not apply on compute nodes, but they may apply on login nodes. Users generally should not log in to service nodes, such as backup servers. Those service nodes still need to know who the users are, because file ownership depends on it.

---

The table compares the options side by side. In practice, teams mix these approaches. The corporate identity provider (IdP) stays the authority for people. The cluster keeps its own LDAP or IPA tree, or uses SSSD mapping, to supply POSIX attributes and groups. Local system and service accounts stay in local files, with UIDs below a reserved range.

---

On login nodes, the book's example limits ordinary users to `50` to `100` processes. That stops a fork bomb from taking the node down. It also sets a `cpu` time limit, such as `100` seconds of processor time, which stops accidental calculations on the head node.

---

Report usage with `lfs quota`, `repquota`, and nightly usage reports per user and per project. Alert at 80 percent, and document your purge policy for scratch. Decide your soft and hard limits, and your purge policy, before users start writing data.

---

## FILE docs/part-06-hpc-slurm/25-remote-access-bastions-open-ondemand-and-user-environments.md

Bulk transfers should not load the login nodes. Data transfer nodes (DTNs) are dedicated hosts with fast external links, and they run tools such as Globus, `rsync`, `rclone` and `aria2` to move datasets in and out. Their firewall and intrusion detection are tuned for large flows, which is the Science DMZ pattern.

---

Good email etiquette matters here too. Remove unnecessary quotes of the user's question, such as headers, addresses and signatures, and keep only the key lines. Write your answer directly underneath them. If a letter holds several questions, answer each one under its own quotation. The book covers this in Chapter 27.

---

Give every user least privilege, and restrict the portal and bastion networks. Require MFA on all remote access, and use short-lived certificates. Log everything, and review the logs. Patch the bastion, the portal and OOD promptly, because they face the internet. Isolate the management networks (Parts 7 and 18). Protect the tokens, such as JWT tokens for Slurm REST and Jupyter tokens, and disable the Jupyter terminal where policy requires it. Scan user-run web apps. Classify what data may leave through DTNs, and keep an acceptable-use policy with a documented process for suspending an account quickly.

---

4. Compare remote graphical access: `X11`, `Xming`, `TigerVNC`, `x2go` and OOD batch-connect, using Chapter 18 of the book. Explain the role swap in X11, where the X server runs on your workstation and the X client runs on the cluster node. Trace each flag in `"C:\Program Files\Xming\Xming.exe" :0 -clipboard -multiwindow -xkblayout us,ru -xkbvariant winkeys -xkboptions grp:ctrl_shift_toggle`. Explain why `xauth` is strongly preferred over `xhost +` and `X0.hosts`. Then compare `TigerVNC`, `x2go` and Open OnDemand browser desktops over high-latency WAN links.

---

## FILE docs/part-06-hpc-slurm/26-cluster-monitoring-and-health-at-scale.md

The protocol defines six core operations: `GetRequest`, `GetNextRequest`, `SetRequest`, `GetResponse`, `GetBulkRequest`, and `Trap`. Each variable in a device's Management Information Base (MIB) has a numeric sequence of numbers called an Object Identifier (OID), such as `1.3.6.1.2.1.1.1.3`. Its human-readable MIB name is `iso.org.dod.internet.mgmt.mib-2.system.sysUpTime`, which is the time the device has been running since it was last powered on. Most OID branches are standardized by IETF, ISO, and IANA. Enterprise sub-branches belong to manufacturers such as Cisco and APC.

---

Notice that each row names both what to measure and where the number comes from, so you know which exporter to install for you to get it. The Golden Rule is **alert on symptoms that need human action; graph everything else.** A GPU at 99 C might be fine for a minute. A rack where 40 percent of GPUs show Xid 79 is an incident, and that is the kind of symptom that should page someone.

---

Suppose a job runs for two hours, its GPUs look busy, and the results still arrive slower than last week. Before you blame the code, you need the right GPU counters on screen. `dcgm-exporter` exposes DCGM fields on `:9400/metrics`. A CSV of counters decides which fields it publishes. The default CSV, `etc/default-counters.csv` in NVIDIA/dcgm-exporter, includes, as read from the repository: `DCGM_FI_DEV_SM_CLOCK`, `DCGM_FI_DEV_MEM_CLOCK`, `DCGM_FI_DEV_GPU_TEMP`, `DCGM_FI_DEV_MEMORY_TEMP`, `DCGM_FI_DEV_POWER_USAGE`, `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` (counter, mJ), `DCGM_FI_DEV_PCIE_REPLAY_COUNTER`, `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_MEM_COPY_UTIL`, `DCGM_FI_DEV_ENC_UTIL`/`DEC_UTIL`, `DCGM_FI_DEV_XID_ERRORS` ("value of the last XID error encountered"), `DCGM_FI_DEV_FB_FREE`/`FB_USED`/`FB_RESERVED` (MiB), `DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL`, `DCGM_FI_DEV_UNCORRECTABLE_REMAPPED_ROWS`, `DCGM_FI_DEV_CORRECTABLE_REMAPPED_ROWS`, `DCGM_FI_DEV_ROW_REMAP_FAILURE`, `DCGM_FI_DRIVER_VERSION` (label), and profiling fields `DCGM_FI_PROF_GR_ENGINE_ACTIVE`, `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`, `DCGM_FI_PROF_DRAM_ACTIVE`, `DCGM_FI_PROF_PCIE_TX_BYTES`/`RX_BYTES`. A larger set is in `dcp-metrics-included.csv`.

---

This is a lint, not real PromQL validation. Run `promtool check rules`, and unit-test the rules with `promtool test rules` in CI. Several thresholds are guesses that you will need to tune, so treat them as starting points. The 85 C limit depends on the GPU model's slowdown and shutdown temperatures. The idle test depends on your workload. Join keys such as `Hostname` depend on your relabelling. The `AllocatedGpuIdle` expression joins DCGM series with a Slurm series that does not carry a `Hostname` label in the demo exporter, so it needs per-node labels to work as written.

---

## FILE docs/part-06-hpc-slurm/27-backup-and-data-protection.md

`ls -li` shows the same inode number for the unchanged `f1.bin` in both snapshots. An inode is the number that identifies a file on disk. The modified `f7.bin` gets a different inode. Each snapshot directory looks like a full copy, and you can browse and restore it with plain `cp`.

---

The caveats matter. The first run copies everything. A file modified in place costs a full copy each time, because there is no block-level dedup. Permissions and ownership need root on the target. Hard links do not cross file systems, and rotation scripts must prune old snapshots. macOS ships an old `openrsync`, so use a current rsync.

---

A parallel file system can hold petabytes of small and large files, and backing it up is a different problem from backing up a home directory. Walking the namespace and moving the data both slow down at this scale, so the methods change.

---

Datasets and models need versioning. Store them in a versioned object store, such as S3 with versioning and object lock. A data-versioning layer such as DVC or lakeFS also works, because it keeps immutable snapshots. Record dataset versions in experiment metadata, so a training run stays reproducible and a lost model can be retrained. Large checkpoints and weights go to object storage with lifecycle policies. Do not stream TB-scale checkpoints through a backup agent.

---

## FILE docs/part-06-hpc-slurm/28-hpc-benchmarking-hpl-hpcg-ior-osu-and-nccl-tests.md

The key references come from the References in section 12.6 of the book, and several appear throughout this section: `[Joy 81]`, `[Anon 85]`, `[Jain 91]`, `[Gunther 97]`, `[Shanley 98]`, `[Coker 01]`, `[Smaalders 06]`, `[Gunther 07]`, `[Bourbonnais 08]`, `[DeWitt 08]`, `[Traeger 08]`, and `[Gregg 09b]`, `[Gregg 09c]`, `[Gregg 14c]`, `[Gregg 14d]`, `[Gregg 18d]`.

---

Before you trust any single number, you want a harness that tells you how stable it is. `code/part06/bench_stats.py` runs two tests. The first is an HPL-style dense solve, using NumPy `solve` and LAPACK LU. It counts flops as `2/3 n^3 + 2 n^2`, as HPL does, and it checks the scaled residual against HPL's threshold of 16. The second is a triad-like bandwidth loop. Each test gets a warm-up run and N repetitions. The report gives the mean, the standard deviation, the coefficient of variation (CV), the minimum, median and maximum, and a 95 percent confidence interval (Student t).

---

Efficiency is Rmax divided by Rpeak. Well-tuned GPU systems land in a broad range of 60 to 90 percent, depending on the architecture, so check published results for your hardware generation. A node that scores well below its peers has a hardware problem, such as throttling, a failing DIMM or a slow link. NVIDIA provides optimised HPL containers, covering HPL for GPUs and HPL-AI or HPL-MxP for mixed precision, with their own run scripts. Build and tune instructions are in the NGC catalogue. HPL stresses compute and, to a moderate degree, the network, so it doubles as a burn-in workload for power and thermals. A full HPL run on a large cluster takes hours. Use it as an acceptance test, and for power and thermal validation (6.30).

---

Start on your laptop with the self-checking Python lab. Run `code/part06/bench_stats_lab.py`. It calls `hpl_like()` and `triad()` from `code/part06/bench_stats.py`, and it verifies that the dense LU solve passes HPL's scaled residual check, $< 16.0$. It also checks the `nccl-tests` `algbw` and `busbw` formulas. For example, 8 GiB across 64 ranks in 0.60 s gives `algbw = 14.3 GB/s` and `busbw = 28.2 GB/s` for `AllReduce`, and `14.1 GB/s` for `AllGather`. Last, it runs two sanity checks from Chapter 12 of Systems Performance: `50,000 IOPS * 8 KB = 400,000 KB/s = 3.2 Gbps > 1 Gbps` limit, and the Benchmark Paradox, `0.5^3 = 12.5%`.

---

## FILE docs/part-06-hpc-slurm/29-containers-and-reproducibility-in-hpc-apptainer-and-enroot.md

The book *Supercomputers for Linux SysAdmins*, in chapter 16, defines a container as "an isolated set of processes". Those processes have limited access to the other processes, the network, the file system and devices. A container is similar to a virtual machine, but it does no emulation. Every process is real, and you can see each one from the host.

---

Containers help you escape dependency hell, the tangle that appears when you recompile a program or try to run one binary next to other software. Picture a team that wants to test a new database for an afternoon. They cannot install it on the shared system without risking a clash with the software already there. A container avoids this by carrying its own files: the binaries, the libraries and even a private copy of `libc`.

---

Apptainer is a fork of Singularity, developed independently under the Linux Foundation. Most of what is written about Singularity applies to Apptainer too. This book notes that the history is more tangled than that, because Singularity was itself a fork. The Apptainer community announcement explains the details. For day-to-day work, the commands and image workflows are the same.

---

The documentation describes two models for MPI applications. Under the hybrid model, the host provides `mpirun` or `srun`, along with its own MPI. The container also carries an MPI. The launcher starts the container once per rank, and the MPI inside connects back through PMI. For Open MPI, `orted` launches Apptainer, which starts the application, which connects back through PMI.

---

## FILE docs/part-06-hpc-slurm/30-facility-basics-power-cooling-racks-and-liquid-cooling.md

A DGX B200 has six power supplies, and it needs five of them to run. Engineers call this internal N+1. The server keeps working if one supply loses power, but not if two do. That holds no matter how redundant the feeds upstream are.

---

The rest of the file controls logging and the UPS's own memory. `STATTIME` sets how often status records are written, and `0` blocks them. `DATATIME` does the same for log entries. `LOGSTATS on` writes a very large volume, so the book leaves it off. The book's example also shows the settings that `apctest` writes into the UPS EEPROM. These lines are commented out in the example, so they show the available options.

---

The temperature monitor works in two steps. Above 25 °C it warns the administrator by mail and on the terminal. Above 30 °C it starts `haltall`, but this emergency version powers off all equipment at once rather than in stages. The book also notes that the warning can go to several addresses or to all terminals.

---

A DGX SuperPOD "scalable unit" (SU) is the building block. One SU holds up to 32 DGX B200 systems and draws about 458 kW. A full SuperPOD has up to four SUs in the typical build, though the reference design can scale much further. With UFM management appliances, the table reaches up to 127 servers, or 1,016 GPUs.

---

## FILE docs/part-06-hpc-slurm/31-capstone-build-and-operate-a-small-slurm-gpu-cluster.md

Suppose someone replaces a failed node, then updates `dnsmasq.conf` and forgets `slurm.conf` or `gres.conf`. The result is `gpu004` either unbootable or invisible to the scheduler. This is configuration drift, and hand-editing files across a cluster makes it almost certain. The remedy is **single-source-of-truth generation**. You keep declarative inventory files in Git (`hardware.csv`, `nodes.csv`, `users.csv`) and compile every daemon configuration and validation check from those files.

---

Many candidates repeat outdated or inaccurate folklore about NVIDIA Base Command Manager (BCM), NCCL and DGX firmware. You can avoid that trap by checking each claim against the source. The table below pairs each common myth with the documented fact from the BCM 11 Administrator Manual, the NCCL User Guide or the DGX H100 User Guide, so you know what to say instead.

---

Interviewers listen for the difference between a quick answer and a structured one. The table below sets a junior reply next to a senior one for five common questions. Read each pair and notice what the senior answer adds: a source of truth, a measurable check, or a named tool.

---

1. **Senior SA Interview Lab (`volume-10/00c-slurm-bcm-interview-lab.md`):** Primary source for the six-plane AI factory stack, the three whiteboard scenarios (128-node AI factory design, 64-node hang triage with `ncclras`, and Slurm vs Kubernetes coexistence), and the vendor-verified correction tables.
2. **NVIDIA DGX SuperPOD with DGX H100 Reference Architecture:** [docs.nvidia.com/dgx-superpod/reference-architecture-scalable-infrastructure-h100](https://docs.nvidia.com/dgx-superpod/reference-architecture-scalable-infrastructure-h100/latest/index.html) — specifies the four fabrics (`MQM9700-NS2F` storage IB at `> 40 GB/s`/node with `1:1` storage and `4:3` compute oversubscription, `SN4600C` in-band Ethernet, `SN2201` OOB Ethernet), `32`-node Scalable Units (`4` SUs = `128` nominal nodes / `1,024` GPUs; `127` nodes / `1,016` GPUs and `31` nodes / `1` SU when `1` DGX node is removed for UFM connectivity), rail alignment, and `> 40 kW` reference rack density.
3. **NVIDIA DGX H100/H200 User Guide and Firmware Update Guide:** [docs.nvidia.com/dgx/dgxh100-user-guide](https://docs.nvidia.com/dgx/dgxh100-user-guide/redfish-api-supp.html) and [docs.nvidia.com/dgx/dgxh100-fw-update-guide](https://docs.nvidia.com/dgx/dgxh100-fw-update-guide/index.html) — specifies `10.2 kW` max system power, `6 x 3.3 kW` PSUs, Redfish URIs (`/redfish/v1/Systems/DGX/Actions/ComputerSystem.Reset`, `/Chassis/DGX/Sensors`, `/UpdateService/FirmwareInventory`, `/Managers/BMC/LogServices/SEL/Entries` with `75` members/page and `Members@odata.nextLink`), `13–20` character BMC password rules, `nvfwupd` firmware management, and `ipmitool mc reset cold`.
4. **NVIDIA Base Command Manager 11 Administrator Manual:** [docs.nvidia.com/base-command-manager/manuals/11/admin-manual.pdf](https://docs.nvidia.com/base-command-manager/manuals/11/admin-manual.pdf) — §5.1.7 and §5.2 (boot role vs provisioning role), §5.6 (`imageupdate` in-place updates on running nodes), §8.1.1–8.1.2 (BCM Auto Scaler `cm-scale` dynamic node repurposing between Slurm and Kubernetes configuration overlays), and §15 (`cmha-setup` HA head nodes with BMC fencing, quorum, and shared NAS).
5. **NVIDIA NCCL User Guide & Kubernetes Gang Scheduling Documentation:** [docs.nvidia.com/deeplearning/nccl/user-guide](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/index.html) (`ncclras` RAS client `MISMATCH` and `INCOMPLETE` diagnostics, automatic RoCE GID selection) and [kubernetes.io/docs/concepts/scheduling-eviction/gang-scheduling](https://kubernetes.io/docs/concepts/scheduling-eviction/gang-scheduling/) (`PodGroup` API feature-gate and alpha hierarchical group status).
6. **Part 6 Toolchain Verification (`code/part06/capstone_demo.sh` & `code/part06/capstone_demo_lab.py`):** Executed locally (`3/3` checks passed), exercising `gen_provision.py` (6.22), `identity_gen.py` (6.24), `gen_slurm_conf.py` and `slurmconf_lint.py` (6.8, 6.10), `sbatch_lint.py` (6.11), `slurm_exporter.py` and `check_alert_rules.py` (6.26), `node_health_lab.py` (6.14), `ckpt_atomic.py` (6.21), and `facility_calc.py` (6.30).

---

## FILE docs/part-15-inference/01-the-anatomy-of-an-inference-request.md

Serving that trained model in production is a real-time systems problem. In this section, we compare the architectural demands of training and inference. Requests arrive over the public network following bursty Poisson arrival patterns. One user sends an eight-token greeting while the next uploads a thirty-two-thousand-token contract. Users watch tokens stream onto their screens in real time and abandon the application if the response stalls.

---

Pushing batch sizes higher increases total TPS and lowers cost per token, but it also slows down per-user TTFT and TPOT. If you double TPS by letting queue wait times climb to five seconds, users leave. To capture usable capacity, we measure **Goodput**—the number of completed requests per second or per minute that simultaneously satisfy both the TTFT and TPOT Service Level Objectives.

---

Consider multiplying an FP16 input matrix [M, K] by an FP16 weight matrix [K, N] to produce an FP16 output matrix [M, N]. Each of the M * N output elements computes a dot product of length K, requiring K multiplications and K additions for 2 * K FLOPs total. Each FP16 element occupies 2 bytes.

---

In production, these request lifecycle stages map onto the full NVIDIA inference software hierarchy, which we detail across Chapters 15.3 through 15.7.
- **vLLM:** Open-source serving engine pioneering PagedAttention, continuous batching, chunked prefill, and multi-LoRA paging (`Activation = (Base_Weights * Input) + (LoRA_B_X * (LoRA_A_X * Input))`) behind an OpenAI-compatible server.
- **TensorRT-LLM — convert_checkpoint.py and trtllm-build:** Ahead-of-time C++/CUDA compiler that fuses attention and GEMM layers and applies FP8/INT4 quantization. It also captures CUDA Graphs across batch-size buckets to eliminate CPU kernel-launch overhead and enables paged context FMHA via `--use_paged_context_fmha enable`.
- **Triton Inference Server — config.pbtxt:** Enterprise HTTP/gRPC serving orchestrator that wraps the tensorrtllm or vllm backend with `decoupled: True` streaming transaction policies, max_tokens_in_paged_kv_cache, and `kv_cache_free_gpu_mem_fraction: "0.9"`.
- **NVIDIA NIM — Inference Microservices:** Pre-packaged OCI containers combining Triton, pre-compiled TensorRT-LLM engines, and OpenAI REST endpoints for drop-in Kubernetes deployment.

---

## FILE docs/part-15-inference/02-batching-the-kv-cache-and-quantization-fundamentals.md

1. **Static Batching:** The client or server waits until a fixed number of requests accumulates before launching execution. It then holds the entire batch until all sequences finish. If nine requests arrive in one second and the tenth arrives five minutes later, the first nine users sit idle for five minutes.
2. **Request-Level Dynamic Batching:** Traditional deep learning servers such as Triton Inference Server use this mode for vision or embedding models. The scheduler collects requests until either `max_batch_size` is reached or a timer `max_queue_delay_microseconds` expires. While this bounds initial queue delay, the formed batch still executes as a locked rectangular tensor from start to finish.
3. **Iteration-Level Continuous Batching:** Pioneered by the Orca serving system and also called In-Flight Batching, this approach is standard in vLLM, TensorRT-LLM, SGLang, and TGI. The scheduler makes decisions at every single token generation step rather than across the full request lifecycle.

---

Quantization compresses a neural network by representing its weights, activations, or KV Cache tensors in lower-bit numerical formats instead of 32-bit or 16-bit floating point. Lowering precision delivers three compounding advantages for LLM serving.
1. **Smaller VRAM footprint:** Cutting parameter width from 16 bits to 8 bits or 4 bits shrinks a 70B model from 140 GB to 70 GB or 35 GB. That allows the model to fit on a single 80 GB GPU and frees tens of gigabytes for KV Cache blocks.
2. **Higher decode memory bandwidth efficiency:** Because autoregressive decode is bottlenecked by HBM bandwidth, reading 4-bit or 8-bit weights moves two to four times fewer bytes per token. That directly lowers Inter-Token Latency.
3. **Faster Tensor Core compute:** When both weights and activations are quantized to 8-bit or 4-bit formats supported by hardware Tensor Cores, peak compute throughput doubles. On an H100 SXM GPU, throughput jumps from 1,979 TFLOPS in BF16 or FP16 to 3,958 TFLOPS in FP8 or INT8.

---

Finally, platform engineers should not leave the **KV Cache** in 16-bit precision when serving long contexts or high concurrency. Quantizing the KV Cache from FP16 or BF16 down to **FP8** cuts per-token KV memory in half. For Llama-3-70B, a 4,096-token KV Cache shrinks from 1.25 GiB to 0.625 GiB per sequence. In production deployments on four 80 GB GPUs, enabling FP8 KV Cache alongside 32-token PagedAttention blocks expands maximum concurrent sessions from 64 to 210. Effective KV Cache utilization rises from 52 percent to 91 percent when paired with quantized attention kernels.

---

corrected 2026-11-11: `--swap-space` (swap_space) is no longer a vLLM option; vllm/config/cache.py has it at v0.17.0 and not at v0.18.0 or v0.32.0, and the v0.32.0 docs/configuration/optimization.md says V1 preempts by recompute rather than swap. The swap-thrashing figures in this chapter come from the nvidia-devops material and describe vLLM before v0.18. Sources: vllm-project/vllm tags v0.17.0, v0.18.0, v0.32.0.

---

## FILE docs/part-15-inference/03-vllm-in-depth.md

Researchers at UC Berkeley built vLLM around a simple operating system insight. Just as an operating system kernel maps contiguous virtual memory addresses onto non-contiguous physical RAM pages, vLLM partitions the KV cache into fixed-size physical blocks and maps them through a per-request Block Table. That single abstraction—PagedAttention—eliminates external memory fragmentation, bounds internal waste to a few tokens per sequence, and removes padding FLOPs from decode attention.

---

Paging the KV cache into uniform physical blocks unlocks a second operating system optimization: memory sharing across sequences via reference counting. Whenever a single prompt spawns multiple output completions—such as parallel sampling with `n=4` or beam search with `"use_beam_search": true, "n": 4`—every candidate branch shares the exact same prompt tokens.

---

In vLLM V0, the HTTP API server, tokenizer, multimodal image processor, scheduler, and GPU kernel launcher shared a single Python process. When serving fast GPUs at large batch sizes or processing Vision-Language Model requests, that shared process became a bottleneck. High-resolution images expand into hundreds of placeholder tokens on the CPU. Decoding pixels, resizing images, and contending for the Python Global Interpreter Lock stalled the GPU kernel launch loop.

---

corrected 2026-11-11: `--swap-space` (swap_space) is no longer a vLLM option; vllm/config/cache.py has it at v0.17.0 and not at v0.18.0 or v0.32.0, and the v0.32.0 docs/configuration/optimization.md says V1 preempts by recompute rather than swap. The swap-thrashing figures in this chapter come from the nvidia-devops material and describe vLLM before v0.18. Sources: vllm-project/vllm tags v0.17.0, v0.18.0, v0.32.0.

---

## FILE docs/part-15-inference/04-sglang-and-cross-request-optimisation.md

When an agentic workflow explores multiple reasoning paths or runs best-of-N candidate selection, calling `s.fork(N)` clones the conversation state into N parallel branches. In the backend, `s.fork(4)` does not duplicate the prompt's Key-Value cache four times. Instead, all four branches point to the same shared prefix node in the Radix Tree. They allocate new Key-Value slots only for their diverging generated tokens, cutting Key-Value memory consumption by more than half.

---

Tracing the lifecycle of the Radix Tree across nine operational stages reveals how SGLang balances reuse against finite VRAM.
1. **Initial empty state:** Before traffic arrives, the tree contains only the root node and all slots in the Level 2 Key-Value pool are free.
2. **First conversation insertion:** When Session A completes its first turn, SGLang does not free its Key-Value tensors. Instead, it inserts a single node containing the system prompt and the first exchange into the Radix Tree with reference count zero and records its access timestamp.
3. **Node splitting on follow-up turns:** When Session A sends a second message, the scheduler walks the tree and matches the first turn. If another user Session B arrives sharing only the system prompt, SGLang splits the original node into a shared parent node and two child branches.
4. **Multi-session fan-out:** As dozens of users connect, all sessions branch off the single shared system prompt node. The system prompt Key-Value tensors occupy GPU memory once.
5. **Leaf-first Least Recently Used eviction under memory pressure:** When a new request requires Key-Value slots and the static memory pool is full, SGLang runs recursive **Leaf-First LRU Eviction**. Any node with an active request holds a positive reference count (`ref_count > 0`) and cannot be evicted. Internal ancestor nodes also cannot be evicted while their children remain in the tree. The eviction loop collects unreferenced leaf nodes (`ref_count == 0`) and evicts the leaf with the oldest access timestamp first. It then recursively prunes newly exposed parent leaves until enough token slots are freed.

---

How do you scale SGLang across a cluster of GPUs without losing RadixAttention cache locality? SGLang supports standard intra-layer Tensor Parallelism, inter-layer Pipeline Parallelism, and Expert Parallelism just like vLLM. However, when a model fits on a single GPU or a single node's NVLink group, SGLang introduces **request-level routing** via the **SGLang Model Gateway** as a horizontal scaling primitive.

---

The SGLang Model Gateway separates cluster management into a control plane and a data plane.
- **Control plane:** Includes a **Worker Manager** that discovers worker capabilities and a **Health Checker** that probes `/health` endpoints and opens worker-scoped circuit breakers after 5 consecutive failures. It also runs a **Load Monitor** that tracks active queues and **Kubernetes Service Discovery** that syncs the worker pool with pod lifecycles.
- **Data plane:** Exposes an **HTTP Router** for OpenAI endpoints, a **gRPC Router** with native tokenization and reasoning parsers, and a **Prefill/Decode Router** for disaggregated clusters. It also enforces exponential-backoff retries with jitter, token-bucket rate limiting, and Prometheus `/metrics` plus OpenTelemetry tracing.

---

## FILE docs/part-15-inference/05-tensorrt-and-tensorrt-llm.md

Consider two real production bottlenecks from enterprise GPU deployments.
- **High-throughput multimodal and vision pipelines.** A feature-extraction cluster serving 25,000 requests per second on H100 GPUs using standard ONNX Runtime suffered severe tail-latency spikes above 85 ms. Those spikes violated its strict 30 ms service-level objective. Whenever bursty traffic drove dynamic batch sizes from 1 to 64, uncalibrated intermediate activation buffers triggered GPU out-of-memory crashes.
- **Distributed large language model serving.** A platform team served Llama-3-70B across eight H100 SXM5 GPUs using a naive PyTorch and Hugging Face pipeline. At 150 concurrent sessions, Inter-Token Latency averaged 115 ms per token, missing the 25 ms target by more than fourfold. GPU utilization swung wildly between 12 percent during decode and 98 percent during prefill. Meanwhile, static contiguous KV cache allocations crashed on long retrieval-augmented prompts exceeding 8,192 tokens.

---

Even after graph fusion, a fused GEMM or attention node can be executed by dozens of distinct CUDA kernels. Those kernels differ in thread-block tile sizes, warp specializations, shared-memory staging layouts, and Tensor Core instructions. Rather than relying on static heuristics alone, the TensorRT builder compiles candidate kernels and times them empirically on the physical GPU during the build phase.

---

Production inference traffic is rarely static. Batch sizes fluctuate with request arrival rates, image resolutions vary by client device, and prompt sequence lengths span tens to thousands of tokens. Because a compiled TensorRT engine pre-plans its memory layout and selects kernel tactics ahead of time, you must declare explicit three-point shape boundaries for every dynamic input tensor using `IOptimizationProfile`.

---

1. **Minimum shape (`kMIN`).** The smallest tensor dimensions the engine will accept at runtime.
2. **Optimum shape (`kOPT`).** The exact dimensions where the builder empirically benchmarks candidate tactics and selects the fastest CUDA kernels.
3. **Maximum shape (`kMAX`).** The hard upper bound used by TensorRT to allocate internal activation and workspace memory buffers.

---

## FILE docs/part-15-inference/06-triton-inference-server.md

A common anti-pattern in production Triton deployments is cranking the instance group count up to 8 or 16 on a single GPU. Engineers often assume that more instances always yield higher throughput. Volume 12 Chapter 3 documents the exact failure mode on an 80 GB A100 GPU serving an ONNX Transformer encoder where each instance requires 9.5 GB of VRAM.

---

Deserializing and loading a 70B parameter model from object storage or NFS into GPU HBM takes 30 to 90 seconds. Suppose a Kubernetes deployment points its liveness probe at the readiness endpoint with a short timeout. The `kubelet` agent will conclude the container is dead while weights are still loading and kill the pod in an infinite crash loop.

---

Run the self-checking lab script to verify repository version resolution, `config.pbtxt` validation, and DenseNet dynamic batching sweeps. The script also verifies sequence batcher routing, continuous LLM batching, instance group VRAM math, shared memory DMA speedups, Prometheus KPIs, Model Analyzer Pareto selection, and Kubernetes probes.

---

1. **Dynamic Batching Speedup and Queue Delay Budgeting.**
   - **(a)** Using the Lab 02 benchmark data in Section 2.1, compute the throughput speedup factor and p99 latency reduction factor of the conservative profile compared to the unbatched profile at concurrency 64. Also compute the percentage of server processing time spent in GPU compute at concurrency 1.
   - **(b)** Explain why the misconfigured profile with a 500 ms queue delay achieves only 4.0 RPS at concurrency 2. Specify the queue delay range in microseconds you should configure for a production pipeline with a 20 ms end-to-end SLA.
2. **Instance Group VRAM Sizing vs CUDA Stream Contention.**
   - **(a)** An ONNX model requires 9.5 GB of GPU VRAM per instance on an 80.0 GB A100 GPU and needs at least 5.0 GB of runtime execution workspace. Calculate the static VRAM footprint and remaining free VRAM for 8 instances versus 2 instances, and explain why 8 instances trigger allocator failures and 84 ms stream mutex stalls.
   - **(b)** Use the Model Analyzer candidate table in `code/part15/triton_inference_server_lab.py`. Identify which configurations form the Pareto frontier under a 25.0 ms p99 SLO and 40.0 GB VRAM ceiling, and name the optimal winner.
3. **Request-Level Dynamic Batching vs Decoupled Continuous Batching.**
   - **(a)** When a 10-token request is co-batched with a 2,048-token request under request-level dynamic batching, how many padded decode iterations does the short request endure? State what happens to p99 ITL, p99 TTFT, and SM occupancy before and after switching to continuous batching with chunked prefill.
   - **(b)** Compute the per-token and 4,096-token session KV cache footprint of Llama-3-70B in FP16 versus FP8. State how 32-token paged blocks and FP8 KV cache changed maximum concurrent sessions and KV cache utilization on four A100 GPUs.
4. **Transport Protocols, Shared Memory Bandwidth, and Prometheus KPIs.**
   - **(a)** A batch of 64 FP32 images totaling 38,535,168 bytes is transferred from host RAM to GPU HBM over PCIe Gen5. Compare the DMA transfer time using pageable memory at 12.0 GB/s versus pinned shared memory at 58.5 GB/s, and state why a 6.2 MB request fails on a default gRPC channel.
   - **(b)** Use the Prometheus scrape counters for `resnet50` in Section 5.1 across 1,000 requests and 50 batches. Calculate the realized average batch size, mean queue wait in microseconds, GPU execution efficiency percentage, and VRAM usage in decimal GB and binary GiB.

---

## FILE docs/part-15-inference/07-nvidia-nim-and-the-nim-operator.md

NVIDIA NIM, short for NVIDIA Inference Microservices, and the Kubernetes NIM Operator solve both problems. **A NIM packages an OpenAI-compatible API server, Triton Inference Server, pre-optimized TensorRT-LLM and vLLM engines, and a hardware-aware model profile selector into one immutable, SLA-backed container**. On Kubernetes, the NIM Operator automates shared model caching, multi-node deployment, and autoscaling through declarative custom resources.

---

As Volume 14 Chapter 4 highlights, that design introduces the **Cold-Start Problem** if you deploy NIM on an ephemeral container filesystem. Every time a pod restarts, reschedules onto a new node. Scales out from 1 to 10 replicas, the container must download the entire model from NGC over the network.

---

To automate this entire lifecycle using Kubernetes-native controllers, *BCM 11 Containerization* Chapter 6 and *Generative AI on Kubernetes* Chapter 1. NVIDIA provides the **NVIDIA NIM Operator** under the `apps.nvidia.com/v1alpha1` API group. The NIM Operator reconciles three core Custom Resource Definitions alongside three **NeMo Microservices CRDs**.

---

1. **Hardware-Aware Profile Selection and GPU Memory Sizing**.
   - **, a,** Using the profile selection rules in Section 2, state which profile and backend NIM selects from the manifest table. Deployed on, i, 2x H100 80GB GPUs in throughput mode, ii, 1x L40S 48GB GPU. No pre-built L40S TensorRT-LLM engine exists, and, iii, 1x A100 40GB GPU when NIM_MODEL_PROFILE is erroneously pinned to tensorrt_llm-h100-fp8-tp2-throughput.
 
2. **Cold-Start Latency vs Persistent Volume Caching, NIM_CACHE_PATH**.
 
   - **, b,** Calculate the warm startup time and speedup factor. Those 140.0 GB weights are loaded from a pre-populated ReadWriteMany NVMe PVC, `NIM_CACHE_PATH=/model_cache`, at `3.5 GB/s` plus 5.0 s of engine initialization.
3. **Multi-LoRA Memory Consolidation, NIM_PEFT_SOURCE**.
   - **, a,** Calculate the total GPU VRAM and GPU count required to host 10 separate fine-tuned 8B NIM deployments where each pod consumes 16.0 GB for base weights and 2.0 GB for runtime overhead.
   - **, b,** Calculate the total GPU VRAM and percentage VRAM reduction. All 10 adapters, 64.0 MB each, are served by a single Multi-LoRA NIM pod configured with `NIM_MAX_GPU_LORAS=8` and `NIM_MAX_CPU_LORAS=32`.
4. **NeMo Microservices Pipeline, Guardrails Latency Budget, and Canary Rollback Gates**.

---

## FILE docs/part-15-inference/08-nvidia-dynamo-llm-d-and-disaggregated-serving.md

Consider the benchmark evaluation from DistServe and *AI Systems Performance Engineering* Chapter 17. The service enforces a ninetieth-percentile TTFT budget of 0.4 seconds and a ninetieth-percentile TPOT budget of 0.04 seconds. When prefill and decode are colocated on a single GPU, the server can sustain 3.0 RPS within the TTFT ceiling alone. However, prefill interference degrades token generation so severely that the server can sustain only 1.6 RPS within the TPOT ceiling. Because goodput requires meeting both targets at once, the colocated GPU delivers only 1.6 RPS of goodput.

---

A subtle trap in disaggregated serving occurs when PagedAttention meets RDMA. By default, vLLM allocates KV cache in small sixteen-token pages so memory fragmentation stays near zero. However, if a prefill worker finishes a 7,500-token prompt and posts 470 separate RDMA write requests—one for each sixteen-token page—NIC work queue element. WQE, setup and doorbell overhead choke the link.

---

On the hardware side, prefill workers can run on compute-optimized accelerators such as Blackwell B200, Hopper H100, or NVIDIA's specialized Rubin CPX context processor. Decode workers can run on memory-capacity and bandwidth-optimized accelerators such as Blackwell Ultra B300. 70 GB of weights on a 180 GB GPU leaves roughly 122 GB for KV cache. Hopper H200, 141 GB HBM3e at 4.8 TB/s vs H100's 80 GB at 3.35 TB/s. Cost-efficient L40S and A100 GPUs. In the Splitwise study, pairing four H100 GPUs for prefill with four A100 GPUs for decode achieved 2.35x the RPS of an eight-GPU homogeneous cluster at the same cost and power budget, and another configuration delivered 1.4x higher throughput at 20 percent lower cost. Similarly, HexGen-2 demonstrated up to 2.0x higher throughput, 1.3x on average, or 30 percent lower cost by co-optimizing heterogeneous GPU assignment.

---

2. **NVIDIA Dynamo Smart Router Decisions and Composite Latency Cost:**.
   -, a, Using `PREFILL_LENGTH_THRESHOLD = 256`, `PREFILL_QUEUE_MAX = 10`, and `DECODE_LOAD_THRESHOLD = 8`, evaluate should_offload_prefill() and the YAML remote_prefill_score, 0.7 length weight, 0.3 queue weight, 0.5 threshold, for. Request A, `prompt=1024, cached=256, queue=4, active=3`, Request B, `prompt=1024, cached=900, queue=3, active=4`, and Request C, `prompt=2048, cached=0, queue=12, active=2`.
   -, b, Calculate both the simple 2-term cost, 0.7 * occ + 0.3 * reqs. The 5-factor composite latency_cost, 3.0 * occ + 1.0 * reqs - 10.0 * match + 0.5 * bw - 1.0 * recent, for worker-0-cold, `occ=1.0, reqs=2, match=0, bw=2.0, recent=0`. Worker-1-warm, `occ=2.0, reqs=3, match=1, bw=4.0, recent=1`, and explain why their routing choices differ.

---

## FILE docs/part-15-inference/09-multinode-inference-parallelism-decoding-and-routing.md

Overlap hides much of the remaining latency. High-performance MoE servers use double buffers. While one batch of tokens moves across the network, the previous batch runs its expert computation. Measure link utilization on both the internode NIC and the intranode NVLink paths. Near-optimal all-to-all times depend on keeping the internode fabric busy.

---

Production applications frequently require **constrained decoding**—also called structured outputs—to guarantee that generated tokens match a strict JSON schema or context-free grammar for function calling. Naive constrained decoders evaluate valid next tokens on the CPU at every decode step across a 128,000-token vocabulary. That check adds several milliseconds per token and thrashes CPU caches.

---

No second model needs training, maintenance, or memory. The hard part is finding a draft-stage reduction, such as dropping layers or lowering precision, that does not hurt accuracy. Other draft-cost cuts include dynamic depth decoding, which skips layers that matter least for quality. Some teams skip every Nth transformer layer. Others run the draft in FP8 or NVFP4, or use a smaller hidden size during the draft stage.

---

Another way to keep the GPU busy is to interleave decode steps from many concurrent requests. This is mostly an inference-engine feature rather than an algorithm change. It batches work at the token level across users, which fills the gaps that a single sequence leaves behind.

---

## FILE docs/part-15-inference/10-prefill-and-decode-disaggregation.md

Decode worker load works in both directions. A decode GPU already busy with many streams can still offload a new prompt. Otherwise it would juggle heavy prefill compute and decoding at once, and both could slow down. A nearly idle decode GPU can take a longer prefill itself.

---

With pipeline parallelism, the layers are cut into stages that sit on separate GPUs, for example GPU 0 and GPU 1. When GPU 0 completes its work on the first microbatch, it passes the activations along to GPU 1 and picks up the second microbatch. The result is an assembly line where every device works on a different piece. The cost is extra inter-GPU communication, plus pipeline bubbles when the microbatch size or stage split is unbalanced.

---

Notice the architectural leverage of attention compression and KV quantization. Moving from 64-head MHA to 8-head GQA cuts the Llama-3-70B KV transfer payload by 87.5 percent. Adopting DeepSeek Multi-Head Latent Attention shrinks the per-token cache by another 4.66x relative to GQA-8. Quantizing the KV cache from FP16 to FP8 halves the network payload again.

---

To prevent pool starvation when the input-to-output ratio shifts, disaggregated platforms combine three dynamic control loops.
1. **Elastic pool autoscaling.** NVIDIA Dynamo's GPU Planner, Arrow, and the Kubernetes `llm-d` variant autoscaler monitor queue depths, GPU utilization, and KV cache occupancy. In the Dynamo reference configuration, the prefill pool scales between 4 and 12 replicas, while the decode pool scales between 8 and 24 replicas. Arrow's integrated request-and-instance scheduler achieves up to **5.6x higher request serving rate** than static allocations during rapid workload shifts.
2. **Stateless instance flipping.** On fixed on-premises clusters where spinning up new cloud nodes is impossible, TetriInfer drains an underutilized decode worker until its active sequences finish and flips its role to prefill. A minimum cooldown window prevents rapid oscillation.
3. **QoS capacity reservation and prediction-based Early Rejection.** When traffic exceeds max cluster capacity, queueing every request causes all users to miss their latency SLOs. Instead, production schedulers reserve capacity by customer tier and run `QoSController` admission control (`est_ttft = Q_prefill * t_prefill + Q_decode * t_decode`). When `est_ttft` exceeds `ttft_slo_ms`, low-priority requests are immediately rejected with HTTP 429 or 503. Alternatively, they are downgraded to local decode-worker prefill so premium traffic stays within SLA.

---

## FILE docs/part-15-inference/11-advanced-prefill-decode-and-kv-cache-tuning.md

The Grace CPU can also spill KV data that does not fit in HBM into CPU DDR memory. That extends the context length the GPU can support. You can slice the transformer across devices. Run the first N layers on the GPU, where most tokens are handled and the sequence is compressed. Offload the next M layers to the CPU, then bring the remaining layers back to the GPU for the final outputs. This layer partitioning adds data movement and orchestration complexity. Justify it only for ultralong contexts or severe GPU memory limits.

---

CPU offload raises TTFT, so it does not suit normal latency-sensitive requests. Treat it as an extensibility and safety-net feature. If the path runs often, track how often. Frequent CPU offloads may mean you need more GPU capacity or model optimization instead. CPU offload handles edge cases, such as very long inputs or GPU bursts, by falling back to a slower path instead of failing. Still, fail fast if processing is too slow and breaks the SLO.

---

Arrow, which is not the Arrow data format, is an adaptive instance scaling technique. Disaggregated systems respond slowly to workload change. If the input-to-output mix shifts, the fixed number of prefill and decode workers does not adjust right away. That causes a temporary drop in goodput, because one side becomes the bottleneck. Arrow tracks the input token rate against the output token rate, and the backlog in each pool. It then adjusts how many workers each side gets.

---

Dynamic scaling changes the split between prefill and decode in response to load. Arrow does this continuously. In Kubernetes, you can define an autoscale policy for each deployment. For example, you can keep average prefill GPU utilization at 70%. If utilization rises, the system adds a pod or node to the prefill pool. If it falls while decode stays busy, one pod can move from prefill to decode. The rule can be simple, or it can solve for the best X and Y counts at each interval.

---

## FILE docs/part-15-inference/12-dynamic-and-adaptive-inference-engine-optimisations.md

In standard eager execution, Python and the CUDA driver require five to fifteen microseconds to validate tensor metadata and enqueue each kernel onto a hardware stream. When an eighty-layer Transformer executes over three hundred small kernels per decode step, the host CPU takes longer to launch the kernels than the GPU takes to execute them. The GPU timeline fragments into tiny bursts of work separated by wide idle gaps.

---

Compilers automatically fuse simple pointwise chains, but critical LLM blocks often require custom OpenAI Triton or CUDA kernels to keep intermediate values entirely inside on-chip SRAM and registers. As shown in *AI Systems Performance Engineering* Chapter 9, fusing an L2 normalization kernel (`fusedL2Norm`) reduces global memory traffic by 3.0x, from 36 bytes per element down to 12 bytes per element.

---

Quantizing the cache works best with per-head, group-wise scaling rather than per-token scaling. Hugging Face's `QuantizedCache` calibrates the value range per attention head. It implements per-channel, group-wise quantization with a configurable group size. It also keeps a residual window of the newest tokens in their original precision. The method is a form of min-max quantization: scale by the largest absolute value in a tensor.

---

Picture a rack of 72 GPUs that can all talk to each other at once. It sounds like the problem is solved, but the fast network is still a shared road. If everyone drives to the same destination at the same minute, you get a traffic jam, and in serving the jam shows up as slow outlier responses. This section is about scheduling the traffic, not just buying the road.

---

## FILE docs/part-15-inference/13-profiling-debugging-and-tuning-inference-at-scale.md

Traditional stateless web services fail and slow down in predictable ways. Each microservice call performs roughly the same work and returns within a uniform time window. Large language model serving behaves very differently. A single inference endpoint receives short chat prompts alongside massive document digests. Each request transitions from a compute-bound prefill phase into a memory-bandwidth-bound autoregressive decode loop.

---

Once profiling confirms that your kernels are memory-bandwidth-bound on weight reads or compute-bound on Tensor Core GEMMs, **quantization** delivers the largest single-node throughput leap. Reducing precision shrinks weight storage, slashes HBM bandwidth traffic per decode step, frees HBM for larger KV cache batches, and doubles or quadruples Tensor Core math rate.

---

Early LLM inference gained a lot by moving from FP32 to TF32, FP16, or BF16. NVIDIA Tensor Cores deliver 2× the throughput with FP16 compared with FP32. They fuse half-precision multiply-add operations into hardware pipelines, and the math doubles without a noticeable accuracy loss.

---

A query classifier or heuristic must make the routing decision. That is harder than it sounds. The classifier needs constant adaptation, broad heuristics, and regular router tuning. Many organizations keep heuristic, rule-based routers and update the criteria from offline analysis.

---

## FILE docs/part-15-inference/14-benchmarking-genai-perf-latency-percentiles-and-goodput.md

Queueing theory explains why LLM tail latency stays flat at low load and then explodes vertically across a tiny increase in traffic. Because average queue wait time scales inversely with idle headroom, pushing cluster utilization from 60 percent to 90 percent multiplies queueing delay sixfold. Pushing utilization to 98 percent multiplies total residency time twentyfold. Once the arrival rate exceeds the engine's maximum service rate, the system becomes unstable and the admission queue grows without bound until requests time out.

---

For new work, use AIPerf. Its CLI reference accepts the same flag names for the arguments below as aliases, so the open-loop example moves over with a new command name. The `--service-type`, `--measurement-interval` and `--generate-plots` flags are not in the AIPerf CLI reference, so drop them. The AIPerf README shows `aiperf profile` with `--streaming`, `--endpoint-type chat`, `--tokenizer`, `--url` and `--concurrency`. This handbook did not run AIPerf, so check the flags against `aiperf profile --help` for your installed version.

---

Does sharding a model across multiple GPUs with Tensor Parallelism (`--tensor-parallel-size`) always improve performance? Step 8 of *Hands-On LLM Serving and Optimization* Chapter 9 answers this question by benchmarking Qwen3-14B-AWQ across single-GPU and multi-GPU layouts on two AWS instances with different interconnects.
- **AWS g6e.12xlarge (L40S GPUs connected via PCIe only, no NVLink).** The **single-GPU setup outperforms multi-GPU Tensor Parallelism** in both total throughput and TTFT latency. Tensor Parallelism executes two synchronous AllReduce collectives per Transformer layer on every single token. Running those collectives across high-latency PCIe bridges costs more time than splitting the small quantized model saves.
- **AWS p4d.24xlarge (A100 GPUs connected via high-speed NVLink).** Here four-way Tensor Parallelism scales cleanly over NVLink, cutting TTFT in half from **66.0 milliseconds down to 33.0 milliseconds** while achieving **3,926 TPS** total throughput. However, when the model already fits on a single GPU and meets its latency target, running **four independent single-GPU Data Parallel replicas achieves 9,816 TPS**. That horizontal layout delivers **2.50x the total throughput** of the single Tensor Parallel instance with zero inter-GPU communication overhead.

---

Use Tensor Parallelism over NVLink when you must fit a large model or cut per-request latency in half. Use Data Parallel replicas when you want maximum cluster throughput per GPU, and never approve a quantization speedup without passing an automated accuracy gate.

---

## FILE docs/part-15-inference/15-autoscaling-inference-hpa-keda-and-scale-to-zero.md

When vLLM starts on an 80 GB GPU with `--gpu-memory-utilization 0.90`, it profiles the model and reserves 90 percent of physical VRAM before serving a single user request. On an H100 reporting 79.14 GiB of usable device memory, vLLM claims 71.22 GiB at startup. For an 8B parameter model in 16-bit precision, the weights consume 14.99 GiB, peak PyTorch activations take 1.19 GiB, and the remaining 54.93 GiB is locked into the PagedAttention KV cache pool.

---

Queue depth and KV cache utilization measure internal engine pressure. Time to First Token and Inter-Token Latency measure the actual user experience. In OpenMetrics and Prometheus, vLLM exports `vllm:time_to_first_token_seconds_bucket` and `vllm:time_per_output_token_seconds_bucket`, while OpenTelemetry semantic conventions standardize on `gen_ai.server.time_to_first_token` and `gen_ai.server.time_per_output_token`.

---

Relying on default HPA scaling behavior is one of the most destructive mistakes in production LLM operations. The default scale-up stabilization window of 0 seconds reacts quickly to traffic surges. However, the default scale-down policy allows Kubernetes to terminate **100 percent of excess pods every 15 seconds** once the 300-second stabilization window elapses.

---

Quantizing weights from 16-bit to 4-bit AWQ or 8-bit FP8 does not merely accelerate matrix math. It expands the PagedAttention KV cache pool from 72,064 tokens to 191,056 tokens on the exact same 48 GB L40S GPU. Because each pod can hold 2.65x more concurrent tokens before `vllm:gpu_cache_usage_perc` hits the 80 percent scale-up threshold, the cluster requires 2.7x fewer GPU nodes to absorb peak traffic.

---

## FILE docs/part-15-inference/16-production-serving-stack-and-reliability.md

Once the prompt reaches the GPU, the sixth stage runs compute-bound prefill matrix multiplications to emit the first token. Memory-bandwidth-bound autoregressive decode iterations then generate the remaining tokens one step at a time. In the seventh stage, GPU sampling kernels apply temperature scaling, repetition penalties, and nucleus filtering over the vocabulary logits. In the eighth stage, the selected 32-bit integer token ID copies back over PCIe to pinned host memory and detokenizes into UTF-8 text. Finally, the ninth stage wraps each text chunk into a Server-Sent Events frame and flushes the TCP socket.

---

When an organization hosts several models and inference engines behind one unified endpoint, the gateway routes requests by inspecting the OpenAI-compatible JSON body.
- **Multi-model routing.** The gateway reads the requested model name and maps it to its internal Kubernetes service DNS address in the multi-models namespace. Clients send all requests to port 8080 without needing to know which pod hosts which weights.
- **Multi-engine routing.** When benchmarking or migrating between runtimes in a multi-engines namespace, the gateway inspects both the model field and the inference server field. Specifying SGLang routes the request to the SGLang service, while leaving the engine field empty defaults to vLLM. The gateway also aggregates `/v1/models` across all backends.
- **Feature-based, A/B, and dynamic routers.** Beyond static name lookup, a feature-based router inspects prompt keywords or a classifier to send coding tasks to a code model. An A/B router hashes the user ID so a user consistently lands on the same model variant. A dynamic router selects among candidate models in real time based on active load, latency budgets, and per-token cost.
- **Ray Serve model multiplexing.** Dedicating an entire GPU pod to each rarely used domain classifier wastes memory. Ray Serve provides `@serve.multiplexed` paired with the `ray_serve_multiplexed_model_id` HTTP header. Each replica lazily loads and caches up to a configured number of models and evicts the Least Recently Used model when a new model arrives.

---

Operating SSE streaming reliably at scale requires four transport and flow-control safeguards.
1. **Disable Nagle's algorithm and proxy buffering.** Interaction between TCP Nagle batching and delayed acknowledgments can stall small token packets by up to 200 ms. Enable `TCP_NODELAY` on the server socket and pass `X-Accel-Buffering: no` so proxies flush SSE chunks immediately.
2. **Decouple egress I/O from the GPU loop with bounded buffers.** Slow mobile clients must never block the GPU continuous batching loop. A separate async I/O thread buffers outgoing tokens up to a hard cap of 50 to 100 unacknowledged tokens per client. If a stalled client exceeds 100 buffered tokens or clicks a Stop button, the server aborts that sequence and frees its PagedAttention KV blocks immediately.
3. **Optional typewriter token pooling.** Speculative decoding can burst 20 tokens in 0.5 seconds. Inserting a configurable 50 ms smoothing delay creates a steady reading cadence for free-tier users while streaming at full speed for paid tiers.
4. **Hard generation ceilings.** Enforce a maximum output limit of 4,096 tokens and a server-side generation timeout of 30 seconds so runaway loops never monopolize GPU slots.

---

Because a lightweight `/ping` liveness probe only checks the CPU web server, hardware faults must be remediated out-of-band by pairing **NVIDIA DCGM Exporter** with **Kubernetes Node Problem Detector**:
1. DCGM Exporter monitors kernel driver events and increments `dcgm_xid_error` the instant a fatal hardware fault such as XID 62 appears in `dmesg`. It also tracks rising rates of precursor single-bit ECC warnings such as XID 63 and XID 92.
2. Node Problem Detector matches the fatal XID pattern and immediately marks the node condition unhealthy.
3. Automated remediation cordons the node via `kubectl cordon` so no new pods land there. It then drains active pods via `kubectl drain` so the Deployment or LeaderWorkerSet respawns the replica on a healthy server, and sends the faulted node for `nvidia-smi --gpu-reset` or hardware replacement.

---

## FILE docs/part-15-inference/17-lab-serve-and-benchmark-on-gke-and-nebius.md

Deploying an inference service on Kubernetes starts with matching the model footprint and latency target to the right physical GPU node pool. Both GKE and Nebius MK8s offer two distinct classes of GPU servers. Cost-optimized PCIe servers include GKE g2-standard-48 with four NVIDIA L4 GPUs and Nebius gpu-l40s-d with four NVIDIA L40S GPUs. Those servers connect accelerators through standard PCIe switches without NVLink bridges. Scale-up SXM servers include GKE a3-highgpu-8g and Nebius gpu-h100-sxm or gpu-h200-sxm. Those servers connect all eight H100 or H200 GPUs across an all-to-all NVSwitch fabric at 900 GB/s per GPU. They also provide 3.2 Tbps of rail-optimized InfiniBand or RoCEv2 networking across nodes.

---

Every serving engine partitions physical GPU HBM into four regions: static model weights, non-PyTorch CUDA runtime context, peak forward-pass activations, and the pre-allocated KV cache pool. In vLLM, the `--gpu-memory-utilization` flag defaults to 0.90. That setting reserves 90 percent of total VRAM for the engine and leaves 10 percent as an OOM safety buffer.

---

Standard Kubernetes Service load balancing distributes connections using round-robin rules. Round-robin fails for LLM workloads because two requests never consume equal GPU work. One request may send a short greeting while the next submits a multi-thousand-token RAG document. Another request may target a specific LoRA adapter loaded via `--enable-lora` and `--lora-modules`. Furthermore, routing follow-up turns of a conversation to a random replica discards the KV cache blocks already computed on the replica that handled the previous turn.

---

Default Kubernetes HPA monitors only CPU and host memory. Knative KPA counts raw HTTP requests regardless of token length. Because neither signal reflects GPU saturation, *Generative AI on Kubernetes* Chapter 4 recommends KServe Standard deployment mode with KEDA autoscaling. KEDA queries `vllm:num_requests_running` directly from the pod or Prometheus. It then scales replicas between 1 and 5 whenever running requests per pod reach the target threshold of 4.

---

## FILE docs/part-15-inference/18-inference-cost-capacity-and-cost-per-token.md

This chapter builds a first-principles financial and capacity model for LLM inference. You will learn how to price input and output tokens, adjust unit economics for latency Goodput, and size KV cache concurrency across precisions. You will also plan multi-region fleets for diurnal traffic, select the right NVIDIA accelerator tier, and compute the break-even point between self-hosted GPUs and managed APIs.

---

During the autoregressive decode phase, each active sequence generates one token per forward pass. To emit that single token, the GPU must stream every parameter of the model plus the historical KV cache from High Bandwidth Memory into SRAM registers. Because arithmetic intensity drops to roughly one to two FLOPs per byte at small batch sizes, decode throughput is governed by HBM bandwidth rather than Tensor Core TFLOPS. Even under continuous batching, each output token occupies a memory-bandwidth-bound iteration slot across every layer of the network.

---

Choosing the right GPU for LLM inference is an exercise in matching your model's memory footprint and parallelism boundary to the accelerator's memory capacity, HBM bandwidth, precision support, and interconnect fabric. Deploying an eight-billion-parameter model on an H100 SXM wastes High Bandwidth Memory premium. Conversely, deploying a seventy-billion-parameter model across four PCIe cards without NVLink cripples token generation with PCIe collective stalls.

---

Notice that the break-even daily token volume depends only on the replica's daily dollar cost and the managed API price per million tokens. If a two-GPU H100 replica costs 297.60 dollars per day and your managed API charges 4.00 dollars per million blended tokens, you must process at least **74.40 million tokens per day** on that replica to break even on raw compute cost. Above that volume, or when strict data residency, compliance, deterministic model pinning, or low local network latency are mandatory, self-hosting wins decisively.

---

