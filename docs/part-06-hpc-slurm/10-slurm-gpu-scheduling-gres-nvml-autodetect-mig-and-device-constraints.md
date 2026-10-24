---
id: "c06-10"
title: "6.10 Slurm GPU scheduling: GRES, NVML autodetect, MIG and device constraints"
sidebar_label: "6.10 Slurm GPU scheduling: GRES, NVML autodetect, MIG and device constraints"
sidebar_position: 10
description: "Making Slurm schedule GPUs correctly: GRES configuration (slurm.conf, gres.conf, AutoDetect), types, topology (Cores and Links), the request options (--gres, --gpus*, --cpus-per-gpu, --mem-per-gpu, --gpu-bind, --gres-flags), device isolation, MIG, MPS and sharding, accounting for GPUs, and debugging"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.10 Slurm GPU scheduling: GRES, NVML autodetect, MIG and device constraints

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Slurm with one or more GPU nodes; CPU-only VMs can practise with fake device files |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Options, defaults and semantics were checked against the man pages and the `gres` documentation from SchedMD/slurm commit `521370b` (2026-10-23, development version 26.11.0rc1; AutoDetect values `nvidia` and `amd` are version-specific). The helper script was run on a machine without GPUs (output only shows the unset case). No Slurm daemon was run; cluster labs are **untested** |

## Why this matters for AI infrastructure

GPU scheduling is the main reason Slurm configuration for AI differs from classic HPC. Users must get exactly the GPUs they asked for, close to the right CPU cores and memory, isolated from other jobs, and counted in accounting. Mistakes look like: a job that sees all 8 GPUs, two jobs that collide on one GPU, training that is 30 percent slower because its CPU threads are on the wrong NUMA node, or a 4-GPU job that waits forever because the request cannot be satisfied by any node. This chapter covers configuration (6.8's `Gres`/`ConstrainDevices` in depth), request syntax, binding and sharing, and diagnosis.

## Prerequisites and outcomes

Needs 6.8, 6.9, Part 9/10 for GPU topology basics (NVLink, PCIe, NUMA). After this chapter you can:

- Configure GPUs as GRES manually and with AutoDetect, with types, device files, `Cores` and `Links`.
- Verify what Slurm thinks the node has (`slurmd -G`, `scontrol show node`) and what a job actually sees.
- Request GPUs correctly using the right option for the situation, including per-GPU CPU and memory.
- Explain and use GPU-to-task binding and CPU-GPU affinity (`--gpu-bind`, `--gres-flags`).
- Isolate devices with cgroups and explain what `CUDA_VISIBLE_DEVICES` does and does not guarantee.
- Choose between whole GPUs, MIG, MPS and sharding for sharing, and configure each.
- Account for GPU usage in TRES, billing and limits.

## 1. Generic resources (GRES)

A **GRES** is a consumable resource other than CPU and memory: GPUs, but also licences, network devices, burst buffers, bandwidth tokens. Each has a **name** (`gpu`), an optional **type** (`h100`, `a100_3g.20gb`), a **count** per node, and optionally device files and topology. Configuration lives in two places:

1. **`slurm.conf`**: declare the GRES *types of resource* cluster-wide and the node counts.

```ini
GresTypes=gpu,shard
AccountingStorageTRES=gres/gpu,gres/gpu:h100
NodeName=gpu[01-16] ... Gres=gpu:h100:8
```

2. **`gres.conf`**: describe the devices on the node: device files, types, CPU affinity, links. Per the man page, if the `Gres` information in `slurm.conf` fully describes the resources (names and counts only), `gres.conf` may be minimal; for GPUs with device files and topology you need it, or `AutoDetect`.

### AutoDetect

`AutoDetect` in `gres.conf` asks slurmd to discover hardware. Values listed in the man page (current development version): `nvml` (NVIDIA GPUs through the NVIDIA Management Library; needs Slurm built with NVML support and the library present), `nvidia` (NVIDIA GPUs without a library, "doesn't detect MIGs or NVlinks"; added in 24.11), `rsmi`/`amd` (AMD), `oneapi` (Intel), `nrt` (AWS Trainium/Inferentia), `full` (try all in order), `off`. For NVIDIA data-centre nodes **use `AutoDetect=nvml`**: it fills in `Type`, `File`, `Cores` (CPU affinity), `Links` (NVLink connectivity) and `UUID` for each GPU, and is the only mode that handles MIG devices. Verify with `slurmd -G`, which "prints GRES configuration (based upon `slurm.conf` GRES merged with `gres.conf` contents for this node) and exit":

```bash
slurmd -G        # run on the GPU node; check type, file, cores, links for each device
```

Different node groups can use different settings (per the man page examples): `NodeName=tux[0-7] AutoDetect=nvml`, `NodeName=tux[8-11] AutoDetect=rsmi`, `NodeName=tux[12-15] Name=gpu File=/dev/nvidia[0-3]`, and a per-node `AutoDetect=off` override for a node with a manual definition.

### Manual definition

When you cannot autodetect, or to override:

```ini
# gres.conf
NodeName=gpu[01-16] Name=gpu Type=h100 File=/dev/nvidia[0-3] Cores=0-31  Links=-1,18,18,18,0,0,0,0
NodeName=gpu[01-16] Name=gpu Type=h100 File=/dev/nvidia[4-7] Cores=32-63
```

(Illustrative; real `Links` lists need one entry per device of that name, one device per record when `Links` is given.) Parameters from the man page:

| Parameter | Meaning |
|---|---|
| `Name`, `Type`, `Count` | Resource name, optional model/type label, number (default 1 per File) |
| `File` | Device files (`/dev/nvidia[0-7]`). Required for cgroup device constraint and for `CUDA_VISIBLE_DEVICES` |
| `Cores` | **Logical core indices** (as in `lstopo -l` "Core L#", not physical OS numbering) that are close to the device; whole sockets (or NUMA nodes with `SlurmdParameters=numa_node_as_socket`) must be specified together because Slurm co-allocates GRES and CPUs at socket granularity. A restart of `slurmctld` is needed after changing `Cores` |
| `Links` | Connection counts to other devices of the same name (`-1` self, `0` none), used to prefer well-connected GPUs; usually autodetected. Note the `/dev/nvidiaN` minor number may differ from the GPU index, which is sorted by PCI bus ID |
| `MultipleFiles` | Several device files per card |
| `UUID` | Device UUID; with `Flags=env_uuid`, `CUDA_VISIBLE_DEVICES` carries UUIDs instead of indices |
| `Flags` | `CountOnly` (count-only resource with no device plugin), `explicit` (not allocated to whole-node jobs unless explicitly requested), `env_uuid`, `one_sharing`/`all_sharing` for MPS |
| `ChunkSizes`/`ChunkOrder` | Restrict how GPU counts are granted (advanced topologies) |

**Types**: set `Type` to the product (`h100`, `a100`, `l40s`) so users can ask for a specific model (`--gres=gpu:h100:4`) and so mixed clusters stay schedulable. Keep type strings short and stable; once they appear in accounting and user scripts they are hard to rename. A type may be requested as a substring-compatible token according to the docs for MIG profiles.

## 2. Requesting GPUs

Options from the `sbatch`/`srun`/`salloc` man pages:

| Option | Meaning |
|---|---|
| `--gres=gpu:N` or `gpu:type:N` | **Per node** count (`name[[:type]:count]`). In a multi-node job this is per node |
| `--gpus=N` (`-G`) | **Total** GPUs for the job (Slurm decides the per-node split) |
| `--gpus-per-node=N` | Per node |
| `--gpus-per-socket=N` | Per socket (requires a socket-count request) |
| `--gpus-per-task=N` | Per task; requires an explicit task count; **implicitly sets** `--tres-bind=gres/gpu:per_task:N` |
| `--cpus-per-gpu=N` | CPUs per allocated GPU (not compatible with `--cpus-per-task`) |
| `--mem-per-gpu=SIZE` | Memory per GPU; mutually exclusive with `--mem` and `--mem-per-cpu`; default is the partition's `DefMemPerGPU` |
| `--gpu-bind=[verbose,]TYPE` | Same as `--tres-bind=gres/gpu:TYPE` |
| `--gpu-freq=...` | Request GPU (and memory) clocks `low`, `medium`, `high`, `highm1` or MHz; applied per regular step, not in the batch script itself |
| `--gres-flags=...` | `enforce-binding`, `disable-binding`, `enforce-links`, `ignore-links`, `one-task-per-sharing`, `multiple-tasks-per-sharing` and others |

Which to use:

- **Single-node training**, all GPUs of a node: `--gres=gpu:8` (or `--gpus-per-node=8`) with `--exclusive` if the whole node should be dedicated (note `Flags=explicit` and partition `Exclusive` interplay).
- **Multi-node, one process per GPU** (the standard PyTorch layout): `--nodes=N --ntasks-per-node=8 --gpus-per-node=8` (or `--gres=gpu:8`), and `--cpus-per-gpu` or `--cpus-per-task` for data-loader threads. This yields N x 8 ranks, one GPU each. Prefer `--gpus-per-node` over `--gpus` when the job needs a regular shape.
- **Flexible total**: `--gpus=16` lets Slurm pack 16 GPUs across fewer or more nodes, which can fragment placement and hurt NCCL performance; use only for tolerant jobs.
- **Several independent tasks in one allocation**: `--gpus-per-task=1` (explicit `-n`), so each task gets its own GPU.
- **Interactive**: `salloc --gres=gpu:1 --cpus-per-gpu=8 --mem-per-gpu=64G --time=1:00:00` then `srun --pty bash` (6.11).

Defaults make life easier: partition `DefCpuPerGPU` and `DefMemPerGPU` (6.8) give a sane share when users type only `--gres=gpu:1`. A job asking for GPUs without CPUs on a node where CPUs are scarce can otherwise block, or get a starved allocation.

### What the job sees

Slurm sets (per the `sbatch` man page environment list): `SLURM_JOB_GPUS` (GPU indices allocated to the job on the node), `SLURM_GPUS_ON_NODE`, `SLURM_GPUS_PER_NODE`, `SLURM_GPUS_PER_SOCKET`, `SLURM_GPUS` (total requested), `SLURM_GPU_BIND`, and for each task `CUDA_VISIBLE_DEVICES` (and `ROCR_VISIBLE_DEVICES`/`ZE_AFFINITY_MASK`/`GPU_DEVICE_ORDINAL` for other vendors) with indices **relative to the job's allocation** (the first allocated GPU is `0`, even if its physical index is 3), when device constraints are on. The helper `code/part06/gpu_env_check.py` prints all of these plus `nvidia-smi -L`; run it as the job step to compare request variants:

```bash
srun --gpus-per-node=2 --ntasks-per-node=2 python gpu_env_check.py
srun --gpus-per-node=2 --ntasks-per-node=2 --gpus-per-task=1 python gpu_env_check.py     # one GPU each
srun --gpus-per-node=2 --ntasks-per-node=2 --gpu-bind=none python gpu_env_check.py       # no per-task binding
```

Run on a machine with no Slurm and no GPUs it prints each key as `<unset>` and `nvidia-smi not found`, confirming the script runs; the interesting output appears on the cluster.

## 3. Binding GPUs to tasks and CPUs

Two separate binding questions:

1. **Which GPU does each task get?** `--gpu-bind` / `--tres-bind=gres/gpu:...`. From the `srun` man page: `closest` binds each task to the closest GRES (in a NUMA environment possibly several), `map:<list>` assigns GPU ids to tasks (`map:0,1,2,3` or `map:0*4,1*4`), `mask:<list>` uses hexadecimal masks per task, `none` turns off binding (including the implicit binding of `--gpus-per-task`), plus `per_task:N`, `single:N`, and a `verbose` prefix. With `task/cgroup` and `ConstrainDevices=yes` the ids are zero-based indexes relative to the job's allocation; without it they are global ids and predictable results need whole-node allocation.
2. **Which CPUs may a task use relative to its GPU?** Governed by `Cores=` in `gres.conf` and `--gres-flags`. By default the cores near a GPU are *preferred*. `--gres-flags=enforce-binding` restricts the job to the cores bound to its GRES (better performance, possibly longer waits: the man page's example is a 2-GPU/1-CPU job delayed until both GPUs on one socket are free). `disable-binding` allows any core (needed when a job needs more CPUs than are bound to its GPUs). Remember the socket granularity: you cannot prefer different cores of the same socket for different GPUs.

For a typical 8-GPU, 2-socket HGX node: GPUs 0 to 3 on socket 0 (NUMA 0), GPUs 4 to 7 on socket 1. Eight tasks with `--gpus-per-task=1 --cpus-per-gpu=N --gpu-bind=closest` put each rank on a GPU with CPUs from the same NUMA node, which matters for host-to-device bandwidth and for NIC proximity (the NIC also hangs off a socket; Part 9, 12). Verify with `nvidia-smi topo -m` (affinity columns) and per-rank `taskset -pc $$` (6.12 goes through launch details).

## 4. Isolation: what actually stops a job from using other GPUs

Environment variables are advisory. A process can ignore `CUDA_VISIBLE_DEVICES` and open `/dev/nvidia3`. Real isolation comes from **cgroup device control**: with `TaskPlugin=task/cgroup` and `ConstrainDevices=yes` (default `no`!) in `cgroup.conf` (6.8) the job's cgroup is only allowed the device files of its allocated GRES; opening another fails with a permission error and `nvidia-smi` lists only the allocated GPUs. This requires that GRES have `File=` entries (or autodetect supplied them). Also:

- The control files `/dev/nvidiactl`, `/dev/nvidia-uvm` and `/dev/nvidia-caps/*` (for MIG) are shared and allowed.
- Containers (6.13) need the device nodes and driver libraries injected (enroot/pyxis, `nvidia-container-toolkit`); the cgroup limits still apply to the container's processes.
- Test it every time you change drivers, kernel, systemd, container runtime: a systemd update (`systemctl daemon-reload`) or a cgroup v2 mismatch has historically reset device permissions and broken isolation on running nodes (an operations lesson; verify against your versions).

Verification script:

```bash
srun --gres=gpu:1 bash -c 'nvidia-smi -L; ls /dev/nvidia*'          # one GPU listed
srun --gres=gpu:1 bash -c 'CUDA_VISIBLE_DEVICES=1 nvidia-smi -L'    # should not reveal GPUs outside the allocation
```

## 5. Sharing a GPU: MIG, MPS and sharding

Whole-GPU allocation is the default and the right default for training. For small workloads (inference, notebooks, debugging) one job per 80 GB GPU wastes capacity. Slurm supports three mechanisms (from the `gres` documentation):

### MIG (Multi-Instance GPU)

NVIDIA A100/H100-class GPUs can be hardware-partitioned into up to seven isolated instances, each with its own SMs, memory and bandwidth. Slurm treats each MIG instance as a GPU, "complete with cgroup isolation and task binding". Configuration: `AutoDetect=nvml` in `gres.conf` and the instances declared in `slurm.conf`, optionally with types that must be a substring of the profile string reported at `debug2` log level:

```ini
AccountingStorageTRES=gres/gpu,gres/gpu:a100,gres/gpu:a100_3g.20gb
GresTypes=gpu
NodeName=tux[1-16] Gres=gpu:a100:1,gpu:a100_3g.20gb:2
```

Key points: **Slurm does not partition the GPU; MIG instances must already exist** (created by `nvidia-smi mig` or the GPU Operator's MIG manager before slurmd starts; "does not support dynamic MIG partitioning"). The sanity-check AutoDetect mode is not supported for MIG. Changing the layout means draining the node, reconfiguring MIG, restarting slurmd. Pros: strong isolation and predictable performance. Cons: static, fragmentation (a 3g.20gb instance cannot be merged), no NVLink/multi-GPU for MIG, some CUDA features limited.

### MPS (Multi-Process Service)

Lets several processes share a GPU concurrently, each allocated a **percentage** of its resources, via the `gres/mps` count. Declare in `slurm.conf` (`Gres=gpu:2,mps:200`, i.e. 100 per GPU) and optionally in `gres.conf`; the count is translated to a percentage, so use multiples of 100 per GPU. The `Cores` parameter for mps is ignored (copied from the GPU). By default only one sharing job is allowed per GPU (`one_sharing`), and the documentation says MPS requires `select/cons_tres`. No memory isolation: one client can exhaust GPU memory.

### Sharding

`gres/shard` is a generic mechanism for **time-shared** use of a GPU by several jobs ("by default it does not fence the processes running on the GPU nor constrain its device memory"). Declare `Gres=gpu:2,shard:64` (32 shards per GPU). It suits homogeneous small jobs; the documentation recommends limiting shards per node to the maximum number of simultaneous jobs. Newer versions add opt-in shard device-memory enforcement (see the page).

### Choosing

| Need | Use |
|---|---|
| Training, multi-GPU, performance-sensitive | Whole GPUs, never share |
| Many small inference/dev jobs, isolation required | MIG |
| Many cooperating small processes, throughput | MPS (trusted users) |
| Maximum density, trusted workloads, simple | Sharding |
| Fractional GPUs for notebooks/serving across a platform | Consider Kubernetes (time-slicing, MIG, DRA; Part 11) |

Mixing MIG and whole-GPU nodes in one cluster is common: a `mig` partition for interactive work, a whole-GPU partition for training. Keep them separate to avoid surprising users.

## 6. Accounting and limits for GPUs

- Add `AccountingStorageTRES=gres/gpu` (and typed variants) so usage appears in `sacct`/`sreport`: `sacct -X --format=JobID,AllocTRES%60`.
- Limit with `GrpTRES=gres/gpu=64` on accounts, `MaxTRESPerUser=gres/gpu=32` on QOS (6.9).
- Weight GPUs in billing: `TRESBillingWeights=GRES/gpu=10,...` on the partition, and `PriorityFlags=MAX_TRES_GRES` (Slurm 25.05 and later per the man page) so GPU hours dominate cost and fair-share.
- Typed TRES (`gres/gpu:h100`) allow per-model limits and reports.
- GPU hours consumed by idle jobs are the real cost problem; combine accounting with utilisation monitoring (DCGM; Part 17) and `sstat`/`sacct` GPU usage fields where `AccountingStorageTRES` includes `gres/gpuutil`/`gres/gpumem` (enabled by `JobAcctGatherParams` and the `acct_gather_energy`/`gpu` plugin; exact spelling version-specific).

## 7. Operational notes

- **Health and drain**: a GPU falling off the bus, Xid errors, ECC failures, or NVLink faults should drain the node (6.14). Slurm does not know GPU health by itself; use a node health check, prolog or `NHC`, DCGM diagnostics (`dcgmi diag`).
- **GPU reset between jobs**: an epilog can reset GPU state, kill leftover processes (`fuser -k /dev/nvidia*` carefully), and clear persistent mode issues (6.14).
- **Persistence mode and MIG state** must be consistent across reboots (systemd units set before slurmd starts).
- **Driver updates**: rolling upgrades need the node empty; consider `Reason` strings and reservations (6.15).
- **Heterogeneous types**: avoid a request like `--gres=gpu:1` landing on an old GPU when the user needs an H100: use types, partitions, features, or a job submit plugin default.
- **Changing GRES counts**: drain first (man page note), then restart `slurmctld`/`slurmd` as required.
- **Containers**: pyxis/enroot exposes GPUs according to the Slurm allocation (6.13).

## 8. Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| `Invalid generic resource (gres) specification` | Type or name not in `GresTypes`/node `Gres` | `scontrol show node`, `slurmd -G`, typo in type |
| Job pending `Resources` / `ReqNodeNotAvail` for GPUs | Request not satisfiable (type, count, memory per GPU, sockets with `enforce-binding`), nodes drained | `scontrol show job`, `sinfo -o "%N %G %t"` |
| Node DRAIN `gres/gpu count too low (0 < 8)` | NVML/driver failed to load, GPU missing; slurmd saw fewer devices than configured | `nvidia-smi`, slurmd log, `slurmd -G`, dmesg Xid |
| `CUDA_VISIBLE_DEVICES` empty or unset in job | No `File=` / device constraint config, `--gres` not requested, `--gpu-bind=none` interplay | `gres.conf`, `scontrol show job` `TresPerNode` |
| Job sees all GPUs | `ConstrainDevices=no` | `cgroup.conf` (6.8) |
| Two ranks use one GPU | No per-task binding; `--gpus-per-task` missing; sharing configured | `gpu_env_check.py` output per rank |
| Slow host-device copies / data loading | CPUs on wrong NUMA node | `--gres-flags=enforce-binding`, `Cores=`, `taskset`, `nvidia-smi topo -m` |
| NVLink-poor GPU pairs allocated | `Links` missing | `slurmd -G`, `--gres-flags=enforce-links` |
| MIG count wrong after reboot | MIG layout not recreated before slurmd | systemd ordering, `nvidia-smi -L` |
| `slurmd` fails: "unable to load NVML" | Slurm built without NVML, or library missing | build config, `ldconfig -p \| grep nvidia-ml` |

## 9. Lab (untested; needs GPU nodes or fake GRES)

1. On a GPU node run `slurmd -C` and `slurmd -G` with `AutoDetect=nvml`; record types, files, cores, links for each GPU; compare with `nvidia-smi topo -m`.
2. Write `slurm.conf`/`gres.conf` for the node; restart; `scontrol show node` should show `Gres=gpu:h100:8` (or your type).
3. Run `code/part06/gpu_env_check.py` under the three `srun` variants in section 2. Record environment and `nvidia-smi -L` per rank.
4. Toggle `ConstrainDevices` and prove the difference with the isolation script.
5. Compare `--gpu-bind=closest`, `map:0,1,2,3`, `none` with 4 tasks: print `taskset -pc` and GPU per rank.
6. Request more CPUs than bound to a GPU with and without `--gres-flags=disable-binding`; observe the pending reason.
7. Create two MIG instances (`nvidia-smi mig`), configure Slurm for them, and run two simultaneous jobs.
8. Practise without GPUs: `Name=gpu File=/dev/null Count=4`-style fake devices (document limits) and check that requests, binding variables and accounting TRES behave.
9. Add `gres/gpu` to `AccountingStorageTRES`; run a job; check `sacct -X --format=JobID,AllocTRES`.

## 10. Interview angles

- How does Slurm know how many GPUs a node has, and how do you verify it?
- What is the difference between `--gres=gpu:4`, `--gpus=4`, `--gpus-per-node=4` and `--gpus-per-task=1`?
- How do you guarantee a job cannot touch GPUs it did not request?
- What are `Cores` and `Links` in `gres.conf` for? What does `enforce-binding` trade off?
- MIG vs MPS vs sharding: isolation, flexibility, use cases. Can Slurm create MIG slices?
- A multi-node PyTorch job is 25 percent slower than last week. What scheduler-side causes would you check?
- How do you bill GPU hours fairly in fair-share?
- Describe what happens when a GPU falls off the bus mid-job.

## 11. Checkpoint questions (30)

1. What is a GRES, and what are its name, type and count?
2. Which two files describe GPUs and what goes in each?
3. List the AutoDetect values and what NVML detects.
4. Which tool prints the merged GRES configuration of a node?
5. What does `Cores` use as numbering, and why in sockets?
6. What does `Links` express?
7. What does `Flags=explicit` change?
8. What does `env_uuid` do?
9. Which options give per-node vs total GPU counts?
10. Which option implicitly sets task binding?
11. Why use `--cpus-per-gpu` and `--mem-per-gpu`?
12. What defaults protect users who omit them?
13. What environment variables does Slurm set for GPU jobs?
14. What does `CUDA_VISIBLE_DEVICES=0` mean when the job holds physical GPU 3?
15. What does `--gpu-bind=closest` do?
16. What do `enforce-binding` and `disable-binding` do?
17. What isolates devices in practice, and what is its default?
18. Why are environment variables insufficient isolation?
19. Which device files must stay accessible to all jobs?
20. How does Slurm treat MIG instances?
21. Can Slurm create MIG partitions? What must happen before slurmd starts?
22. How is MPS capacity expressed, and what are its limits?
23. What does sharding provide and not provide?
24. When do you prefer whole GPUs?
25. How do you enable GPU accounting?
26. What is `MAX_TRES_GRES`?
27. How do you restrict a user to 32 GPUs total?
28. What do you do before changing a node's GRES count?
29. List three causes of "job sees wrong GPUs".
30. What node health actions should GPU faults trigger?

## 12. Sources and review notes

- GRES and GPU scheduling concepts, partitions and operations: *Supercomputers for Linux SysAdmins* chapter 15 (generic and trackable resources), restated in my words; distributed-training launch patterns from *Distributed AI Systems* chapter 8 (SLURM for AI training), used in 6.11 and 6.12 more fully.
- Parameters and semantics: Slurm man pages `gres.conf(5)`, `slurm.conf(5)`, `cgroup.conf(5)`, `sbatch(1)`, `srun(1)`, `slurmd(8)` and the `gres` documentation page (MIG, MPS, sharding), SchedMD/slurm commit `521370b`. Several AutoDetect values and shard memory enforcement belong to very recent releases.
- Original: `code/part06/gpu_env_check.py` (run once without GPUs), the request-choice guidance and troubleshooting table.
- Unverified: NVSwitch/HGX socket-to-GPU layout statement (typical, check `nvidia-smi topo -m`); the systemd/cgroup device-reset incident remark; accounting field names for GPU utilisation; all cluster behaviour.
