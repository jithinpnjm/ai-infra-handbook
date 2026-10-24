---
id: "c06-08"
title: "6.8 Slurm configuration: nodes, partitions and cgroups"
sidebar_label: "6.8 Slurm configuration: nodes, partitions and cgroups"
sidebar_position: 8
description: "Configuring Slurm for a GPU cluster: node definitions and states, features, weights and reserved resources, partitions and their limits, resource selection (cons_tres), cgroup containment, reconfigure versus restart, validation, and common misconfigurations, checked against the slurm.conf, cgroup.conf and topology.yaml man pages"
status: "drafted"
tier: "1"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.8 Slurm configuration: nodes, partitions and cgroups

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Small Slurm cluster; the linter runs anywhere with Python 3 |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Parameter names, defaults and semantics were checked against the Slurm man pages (`slurm.conf`, `cgroup.conf`, `topology.yaml`, `slurmd`) from a shallow clone of SchedMD/slurm (commit `521370b`, 2026-10-23, source version 26.11.0rc1, a development version). Production sites run older releases: confirm with `man` on your version. The lint script was run on two test files. No Slurm daemon was run; cluster labs are **untested** |

## Why this matters for AI infrastructure

Almost every "my GPU job is wrong" ticket (sees all 8 GPUs instead of 2, runs on the wrong cores, is killed for memory unexpectedly, queues forever though nodes are idle, node marked invalid) is a configuration problem in the three places this chapter covers: how nodes are described, how partitions group them, and how cgroups enforce what the scheduler decided. Getting them right once makes the cluster boring, which is the goal. 6.7 introduced the daemons and a first `slurm.conf`; this chapter goes through each part with the reasoning and the failure modes.

## Prerequisites and outcomes

Needs 6.2, 6.7 and Linux cgroups basics (Part 1). After this chapter you can:

- Write correct node definitions from `slurmd -C`, including reserved cores and memory, features, weights and GPU resources.
- Explain node states and flags, and the commands and settings that move a node between them (`ReturnToService`, `scontrol update`).
- Design partitions: overlapping vs separate, priority tiers, limits, defaults, access control, exclusivity.
- Choose `SelectType` and `SelectTypeParameters` and explain how they make cores and memory consumable.
- Configure cgroup containment (`ProctrackType`, `TaskPlugin`, `cgroup.conf`) and verify that it works.
- Apply configuration changes safely (`scontrol reconfigure` vs restart), validate a config, and recognise typical mistakes.

## 1. How configuration is organised

Slurm reads `slurm.conf` (and optional companion files) from a common directory (`/etc/slurm` by default). Companion files include `cgroup.conf`, `gres.conf`, `topology.yaml` (or the older `topology.conf`), `slurmdbd.conf` (only on the database host), `oci.conf`, and others. Facts from the man pages:

- Parameter names are case-insensitive; `#` starts a comment; `Include filename` pulls in another file (useful to split node and partition definitions).
- `slurm.conf` must be **readable by all Slurm users**, since client commands read it. Keep secrets (database passwords) out of it; those belong in `slurmdbd.conf` (mode 600).
- **Configuration must be identical on all nodes** that read a file, or you use **configless mode** (`slurmctld` serves the config to `slurmd`; 6.7 section 7). Mismatched configs cause nodes to register as invalid and to be set to DOWN or DRAIN with a configuration mismatch reason.
- Changes take effect on daemon restart, on SIGHUP, or on `scontrol reconfigure`, "unless otherwise noted"; changes to TCP listening settings require a daemon restart.

## 2. Nodes

### Describing the hardware: trust `slurmd -C`

`slurmd -C` prints the hardware configuration **as detected on that node** (not from `slurm.conf`) in a form you can paste. Always start from it:

```bash
slurmd -C
# NodeName=gpu01 CPUs=64 Boards=1 SocketsPerBoard=2 CoresPerSocket=16 ThreadsPerCore=2 RealMemory=515000 ...
```

Key node parameters (all from `slurm.conf(5)`):

| Parameter | Meaning and notes |
|---|---|
| `NodeName` | The name Slurm uses; usually `hostname -s`. Hostlist expressions (`gpu[01-32]`) work when the number is at the end. `NodeName=DEFAULT` sets defaults for the lines that follow (and replaces/adds, it does not reset) |
| `NodeHostname`, `NodeAddr` | Real hostname and the address used to reach it, if different from the node name (for example a management or fabric IP) |
| `Sockets`/`SocketsPerBoard`, `CoresPerSocket`, `ThreadsPerCore`, `Boards` | The topology. `CPUs` defaults from these; if you give `CPUs`, make it consistent: `CPUs = Boards x SocketsPerBoard x CoresPerSocket x ThreadsPerCore` |
| `RealMemory` | Memory in MiB available to Slurm. **Default is 1.** Lowering it to leave room for the OS only works if memory is a consumable resource (`SelectTypeParameters` with a `*_Memory` option) |
| `MemSpecLimit` | MiB of RealMemory reserved for system use and not available to jobs; with `task/cgroup` and `ConstrainRAMSpace=yes` the slurmd is given that memory limit. Slurm's daemons are not OOM-killed if they exceed it. Needs a consumable-memory `SelectTypeParameters` |
| `CoreSpecCount` / `CpuSpecList` | Cores reserved for the system (and the slurmd); mutually exclusive. Isolating `slurmd` from jobs can improve application performance (jitter, 6.3) |
| `Gres` | Generic resources, for example `gpu:8` or `gpu:h100:8` (6.10). **Drain the node of jobs before changing a GRES count** |
| `Features` | Arbitrary labels users request with `--constraint` (for example `h100,nvlink,ib_ndr,rack3`). `feature{name}` is a hostlist function expanding to all nodes with that feature (partition `Nodes=feature{myfeature}`) |
| `Weight` | Scheduling preference: jobs go to the lowest-weight nodes that satisfy them; larger weights for bigger/better nodes keep scarce hardware free for jobs that need it |
| `TmpDisk` | MiB of the temp file system (`TmpFS`); informational for `--tmp` requests, not free space |
| `State` | Initial state (below) |
| `Reason` | Text for DOWN/DRAIN/FAIL states |
| `Port` | Per-node slurmd port; rarely needed |
| `CpuBind` | Default task binding for the node |
| `RestrictedCoresPerGPU` | Reserve cores per GPU for GPU-bound work (newer versions) |

### Hyperthreads and the allocation unit

Slurm allocates down to a **core**. With `ThreadsPerCore=2`, a job gets both hardware threads of its cores unless it asks otherwise (`--threads-per-core`, `--hint=nomultithread`). Running a different job on each thread of a core is unsupported unless you configure `SelectTypeParameters=CR_CPU` and give only `CPUs` (no socket/core/thread fields). With `cons_tres` and more than one thread per core, use a setting other than `CR_CPU`, as the man page warns. In practice GPU clusters use `CR_Core_Memory` and leave SMT on or off at the BIOS level based on workload tests (Part 9).

### Node states

From the node-state documentation in the man page and `sinfo`:

| State | Meaning |
|---|---|
| `IDLE` | Up and nothing running |
| `MIXED` | Some resources allocated, some free |
| `ALLOCATED` | Fully allocated |
| `DRAIN`/`DRAINING`/`DRAINED` | No new work will start. `DRAINING` means jobs are still running; `DRAINED` (shown as `drain`) means it is empty. Set by an admin or a health check |
| `DOWN` | Failed; unavailable. Slurm sets this when `slurmd` does not respond within `SlurmdTimeout` (default 300 s; 0 disables the check) or on registration problems |
| `FAIL` / `FAILING` | Expected to fail soon; `FAIL` has no jobs, `FAILING` has jobs but accepts no new ones |
| `FUTURE` | Defined for later; invisible until made available with `scontrol` (no restart needed) |
| `CLOUD` | Powered-down/cloud nodes |
| `UNKNOWN` | Initial; Slurm resolves it to IDLE/BUSY/etc. when the slurmd registers |
| `PLANNED`, `RESERVED`, `COMPLETING`, `MAINT`, `POWER_*` | Flags/states shown in `sinfo` for backfill planning, reservations, epilog running, maintenance, power saving |

In the *configuration file* do not set `IDLE` or `BUSY`; set `UNKNOWN` (the default) and let Slurm recover the state from its saved state and the registering daemon.

Commands (6.14 covers the operational side):

```bash
sinfo -N -l                              # per node
sinfo -R                                 # reasons for down/drained nodes
scontrol show node gpu01
scontrol update nodename=gpu01 state=drain reason="ECC errors, ticket 1234"
scontrol update nodename=gpu01 state=resume
```

**`ReturnToService`** controls automatic recovery from DOWN: `0` (default) stays DOWN until an admin intervenes; `1` returns the node on registration with a valid configuration only if it was set DOWN for being unresponsive; `2` returns it on registration with a valid configuration for any reason. "Valid" means memory, GRES and CPU count at least what `slurm.conf` says. Setting 2 looks convenient and is the setting in the 6.7 starter config, but it can hide a node that rebooted because of a hardware fault and re-enter it into service; pair it with a node health check (6.14) that drains bad nodes.

## 3. Partitions

A partition is a named **set of nodes with a policy**. Jobs are submitted to a partition (users may list several). A node can belong to several partitions, which is how you express "the same GPUs are available to both the `debug` and `batch` queues". Key options (`slurm.conf(5)`, partition section):

| Option | Use |
|---|---|
| `Nodes` | Node list (or `ALL`, or nodesets) |
| `Default=YES` | The partition used if none is specified; exactly one |
| `MaxTime`, `DefaultTime` | Wall-clock limit and default limit; short `DefaultTime` plus longer `MaxTime` encourages accurate requests |
| `MinNodes`, `MaxNodes` | Size limits per job |
| `State` | `UP` (accept and run), `DOWN` (accept, do not run), `DRAIN` (do not accept new, run existing), `INACTIVE` |
| `PriorityTier` | Higher tier partitions are evaluated first and can preempt lower tiers if `PreemptType=preempt/partition_prio` (max 65533) |
| `PriorityJobFactor` | Partition term in the multifactor priority (default 1) |
| `AllowAccounts`, `DenyAccounts`, `AllowGroups`, `AllowQos`, `DenyQos`, `AllocNodes`, `ReqResv` | Access control; `ReqResv=YES` forces jobs to use a reservation |
| `QOS` | Partition QOS whose limits apply (the partition QOS limit wins unless the job's QOS has `OverPartQOS`) |
| `OverSubscribe` | Whether more than one job may share a resource (`NO` default, `YES`, `FORCE`); sharing is usually for gang scheduling and needs memory as a consumable resource |
| `Exclusive` | In current development versions, `NO`, `NODE`, `USER` or `TOPO`: whole-node, single-user-per-node or per-topology-segment allocation; replaces the older `OverSubscribe=EXCLUSIVE`, `ExclusiveUser` |
| `DefMemPerCPU`/`DefMemPerGPU`/`DefMemPerNode`, `MaxMemPerCPU`/`MaxMemPerNode` | Default and maximum memory; the default ones are mutually exclusive. `DefMemPerGPU` is natural for GPU partitions |
| `DefCpuPerGPU` | Default CPUs per allocated GPU (a good default prevents GPU jobs from getting 1 core) |
| `MaxCPUsPerNode`, `MaxCPUsPerSocket` | Cap CPUs a partition's jobs can use per node, so a `cpu` partition cannot starve a `gpu` partition of host cores on shared nodes |
| `LLN` | Place on the least-loaded node |
| `Hidden`, `RootOnly`, `DisableRootJobs` | Visibility and root usage |
| `Alternate` | Fallback partition when this one is drained |
| `GraceTime`, `OverTimeLimit`, `PreemptMode` | Preemption and time-limit behaviour |
| `Topology` | Which topology (from `topology.yaml`) the partition uses |

(Option availability varies by version; for example `Exclusive` appears in the development man page I read. Check your version.)

### Partition design patterns

1. **By hardware**: `h100`, `a100`, `cpu`, `bigmem`. Users know what they get; no cross-contamination.
2. **By policy on the same hardware**: `debug` (MaxTime 30 min, high `PriorityTier`, small MaxNodes), `batch`, `long` (lower priority, larger MaxTime restricted by `AllowGroups`), `preempt` or `scavenger` (lowest tier, preemptible), `interactive`. The same nodes appear in several partitions; priority tiers and QOS make them cooperate (6.9).
3. **Per-tenant** partitions with `AllowAccounts` for purchased hardware, plus a shared scavenger partition spanning all nodes for idle cycles.
4. Keep the partition count small and meaningful; dozens of partitions confuse users and the scheduler's planning.

Always set `Default=YES` on exactly one partition, a `DefaultTime` appropriate for it, and `DefMemPerGPU`/`DefCpuPerGPU` on GPU partitions so that `--gres=gpu:1` yields a sensible CPU and memory share by default.

## 4. Resource selection: how cores, memory and GPUs are counted

`SelectType=select/cons_tres` is the standard: "consumable trackable resources", which tracks cores/CPUs, sockets, memory and GRES per node. `SelectTypeParameters` chooses the allocation granularity: `CR_CPU`, `CR_Core`, `CR_Socket`, each optionally with `_Memory` (`CR_Core_Memory` is the common GPU-cluster choice). Practical consequences:

- Without `_Memory`, memory is **not tracked**; jobs can oversubscribe RAM and `--mem` is just advice, and `ConstrainRAMSpace` does nothing (man page: `CR_*_Memory` must be set for it to take effect).
- `CR_Core` hands out whole cores; `CR_CPU` hands out hardware threads (only recommended when you intend to schedule at thread granularity).
- Options such as `CR_ONE_TASK_PER_CORE` and `CR_CORE_DEFAULT_DIST_BLOCK` change task distribution.
- For GPU nodes, make sure `DefCpuPerGPU` and `DefMemPerGPU` (or per-node defaults) exist, or users get arbitrary slivers.

## 5. Containment with cgroups

The scheduler only *decides*; the kernel must *enforce*. Three pieces:

| Setting | Role |
|---|---|
| `ProctrackType=proctrack/cgroup` | Track all processes of a job so that cleanup at job end kills every descendant, including daemonised children |
| `TaskPlugin=task/affinity,task/cgroup` | `task/affinity` sets CPU masks and enables `--cpu-bind`/`--mem-bind`; `task/cgroup` fences processes into the allocated resources using cgroups. The man page recommends stacking them together with `ConstrainCores=yes` |
| `JobAcctGatherType=jobacct_gather/cgroup` | Accounting from cgroup statistics (accurate memory/CPU use) |

`cgroup.conf` (read by all of the above), with defaults from the man page:

| Parameter | Default | Effect |
|---|---|---|
| `CgroupPlugin` | autodetect behaviour (`cgroup/v1`, `cgroup/v2`, `autodetect`, `disabled`) | Which cgroup version to use; on modern distributions (cgroup v2) use `autodetect` or `cgroup/v2` |
| `ConstrainCores` | **no** | Restrict a job to the cores it was allocated (cpuset) |
| `ConstrainRAMSpace` | **no** | Hard memory limit = allocated memory x `AllowedRAMSpace` percent; OOM-kills the step beyond it. Needs `CR_*_Memory` |
| `AllowedRAMSpace`, `AllowedSwapSpace`, `ConstrainSwapSpace`, `MaxRAMPercent`, `MinRAMSpace` | various | Tune the memory limits; `AllowedRAMSpace` above 100 can cause system-wide OOM |
| `ConstrainDevices` | **no** | Restrict a job's device access to its GRES allocation (GPUs) |
| `ConstrainDeviceMemory` and others | no | Additional device-related constraints (see the page) |

Important: **every Constrain option defaults to `no`.** A config with only `TaskPlugin=task/cgroup` and an empty `cgroup.conf` constrains nothing. For GPU clusters set at least:

```ini
# cgroup.conf
CgroupPlugin=autodetect
ConstrainCores=yes
ConstrainRAMSpace=yes
ConstrainDevices=yes
```

`ConstrainDevices=yes` is what makes `CUDA_VISIBLE_DEVICES`-independent isolation real: the job physically cannot open GPUs it was not allocated. Without it, a job allocated one GPU can run on all eight by ignoring the environment variable.

Kernel notes from the man page: on Debian and derivatives (including Ubuntu) the memory and swap cgroup controllers may be disabled by default; enable them on the kernel command line (`cgroup_enable=memory swapaccount=1` for the cgroup v1 case, via `GRUB_CMDLINE_LINUX` and `update-grub`) if you want memory constraints. On cgroup v2, check that the `cpuset`, `memory` and `devices`-equivalent (eBPF) support are available and that Slurm was built with cgroup v2 support (6.7 section 10).

**Verify containment** instead of assuming:

```bash
srun --gres=gpu:1 --mem=4G -n1 bash -c 'nvidia-smi -L; cat /proc/self/cgroup; grep Cpus_allowed_list /proc/self/status'
```

Expect one GPU listed, a Slurm job/step cgroup path, and only the allocated CPUs. Then test the limits: a process that allocates more than `--mem` should be OOM-killed, with `dmesg` and `sacct` reflecting `OUT_OF_MEMORY`.

## 6. Topology awareness

For multi-node jobs the placement of nodes on the network matters (6.3). Slurm's topology configuration lives in `topology.yaml` (current versions; older `topology.conf`, which is ignored if `topology.yaml` exists). The man page describes multiple named topologies, one marked `cluster_default: true`, each of exactly one type: `tree` (switch hierarchy, the classic InfiniBand/Ethernet fat-tree), `block` (nodes grouped in blocks for rail/block-oriented systems), `ring`, `torus3d`, or `flat` (default, no topology). Partitions pick a topology by name. With tree topology the scheduler prefers to place a job under the fewest switches; `sbatch --switches=N[@maxwait]` asks for that. Generating the file from the fabric (`ibnetdiscover`-based tools such as `slurm-topology` helpers, or from BCM/UFM data) is part of fabric commissioning (Part 12). Keep it in step with cabling changes, or the scheduler optimises for a network that no longer exists.

## 7. Applying changes safely

- **`scontrol reconfigure`** re-reads configuration and applies most changes without stopping jobs. Some parameters require a restart of the daemons (the man pages mark these; changes to listening ports, `StateSaveLocation` and plugin types are typical).
- **Adding nodes**: add them to `slurm.conf`/`Include` file, distribute (or rely on configless), restart `slurmctld` and the `slurmd`s as required (or use `FUTURE`/dynamic nodes to avoid restarts; dynamic nodes register with `slurmd -Z --conf "..."`).
- **Changing a GRES count or node CPU layout**: drain first.
- **Keep configs in Git**; deploy via configuration management (Part 4); show the diff in review.
- **Validate** before applying:
  - `slurmd -C` on a real node to confirm hardware matches the definition.
  - `scontrol show config` after reconfigure to see effective values.
  - A linter. The handbook includes `code/part06/slurmconf_lint.py`, a small checker (not the real parser) for the commonest slips: CPU arithmetic, undefined nodes in partitions, duplicate node definitions, missing `RealMemory`, no `_Memory` in `SelectTypeParameters`, missing cgroup plugins, multiple default partitions, `Gres` without `GresTypes`.
  - A test cluster or a single-node canary partition for risky changes.

### Linter output

On a known-good file the tool printed one advisory (the `ReturnToService=2` caution). On a deliberately broken file it printed:

```text
ERROR: gpu[01-04]: CPUs=64 but Sockets*CoresPerSocket*ThreadsPerCore=32
ERROR: gpu[01-04]: Gres=gpu:8 but GresTypes does not list gpu
ERROR: node gpu04 defined more than once
ERROR: partition gpu: node gpu05 is not defined
ERROR: 2 partitions marked Default=YES (expected exactly 1)
warn:  gpu[01-04]: RealMemory not set (defaults to 1 MB; memory limits will not work)
warn:  SelectTypeParameters has no *_Memory: memory is not a consumable resource, ConstrainRAMSpace has no effect
warn:  TaskPlugin/ProctrackType do not both use cgroup: job cleanup and containment will be weak
```

Each message corresponds to a real incident type described in section 8. The script is deliberately small; treat it as a teaching aid and extend it for your site.

## 8. Common misconfigurations and symptoms

| Symptom | Likely cause |
|---|---|
| Node goes `inval`/DRAIN right after registering, reason "Low RealMemory" or "Low CPUs" | The node definition claims more memory/CPUs than detected; start from `slurmd -C`; remember kernel-reserved memory |
| Every node shows 1 MB of memory; memory requests behave oddly | `RealMemory` omitted (default 1) |
| Jobs see all GPUs | `ConstrainDevices` is `no` (default); or `gres.conf` missing |
| A job uses more cores than allocated | `ConstrainCores` no; `task/affinity` missing |
| Memory-hungry job takes the whole node down, other jobs are OOM-killed | No `_Memory` in `SelectTypeParameters`; `ConstrainRAMSpace` no; no `MemSpecLimit` for the OS and slurmd |
| Processes of a finished job linger and hold GPU memory | `ProctrackType` not cgroup; no epilog cleanup (6.14) |
| Jobs pending with reason `Resources` although nodes idle | Partition `MaxCPUsPerNode`, node `Weight`/feature mismatch, GRES typo, memory default too high (`DefMemPerGPU`), reservations |
| Jobs pending `PartitionConfig` or `ReqNodeNotAvail` | Request violates partition limits; nodes DOWN/DRAIN; reservation |
| Multi-node job placed across the cluster with poor bandwidth | No topology configured, or stale `topology.yaml` |
| Config change ignored | Needed restart not reconfigure; config differs between nodes; configless cache; wrong file path |
| `SlurmdTimeout` marks healthy nodes DOWN under load | Network/slurmd responsiveness; tune the timeout and check name resolution |
| After a reboot nodes stay DOWN | `ReturnToService=0` (default) |

## 9. Lab (untested; needs a Slurm test cluster)

1. On each node run `slurmd -C`; build the node lines from it. Compare with your hardware documentation.
2. Write `slurm.conf`, `cgroup.conf`, `gres.conf` (6.10) for 2 GPU nodes and 2 CPU nodes with partitions `debug` (high tier, 30 min), `gpu`, `cpu`, and a preemptible `scavenger`.
3. Lint with `code/part06/slurmconf_lint.py`; fix findings; start the cluster.
4. Verify containment (section 5): GPU isolation, core isolation, memory OOM. Record `cat /proc/self/cgroup` output.
5. Break each of these on purpose and write down the symptom and the log line: wrong `RealMemory`; `ConstrainDevices=no`; two default partitions; `Gres` without `GresTypes`.
6. Practice states: drain a node with a reason while a job runs, watch `DRAINING` to `DRAINED`, resume it; kill `slurmd` and watch it go DOWN after `SlurmdTimeout`; test the effect of `ReturnToService=0` vs `2`.
7. Change a partition limit and apply with `scontrol reconfigure`; confirm with `scontrol show partition`.
8. Add a `topology.yaml` with a tree of two leaf switches and see `sbatch --switches=1` behaviour.

## 10. Interview angles

- How do you obtain the right node definition? What does the default `RealMemory` imply?
- What is the difference between `DRAIN` and `DOWN`, and what does `ReturnToService` change?
- A user sees all GPUs in the job. What do you check?
- Explain `PriorityTier` versus `PriorityJobFactor`.
- Why use overlapping partitions? What are the pitfalls?
- What does `ConstrainRAMSpace` need to work?
- What is `MemSpecLimit` for? `CoreSpecCount`?
- When is `scontrol reconfigure` not enough?
- How would you let a `cpu` partition share nodes with a `gpu` partition without starving GPU jobs of host cores?
- What does topology awareness add for multi-node training?

## 11. Checkpoint questions (30)

1. Where does Slurm read its configuration, and who must be able to read `slurm.conf`?
2. What does `Include` do?
3. What is configless mode?
4. What does `slurmd -C` print?
5. Write the relationship between `CPUs` and the topology parameters.
6. What is the default `RealMemory`?
7. What does `MemSpecLimit` do and what does it require?
8. What is `CoreSpecCount` for?
9. When must a node be drained before changing configuration?
10. What are features and weights used for?
11. List five node states and their meaning.
12. What sets a node DOWN automatically?
13. Explain `ReturnToService` 0, 1 and 2.
14. Which node states should not be set in the configuration?
15. What does `Default=YES` do and how many may exist?
16. Compare `MaxTime` and `DefaultTime`.
17. What does `PriorityTier` change?
18. What does `OverSubscribe` do, and what must accompany it?
19. What is `MaxCPUsPerNode` useful for?
20. Why set `DefMemPerGPU` and `DefCpuPerGPU`?
21. What does `select/cons_tres` provide?
22. Compare `CR_CPU`, `CR_Core` and `CR_Core_Memory`.
23. What do `proctrack/cgroup`, `task/affinity` and `task/cgroup` each do?
24. What are the defaults of the `Constrain*` options?
25. Which option isolates GPUs, and how do you prove it works?
26. What kernel setting may be needed on Ubuntu for memory cgroups (cgroup v1 case)?
27. What does `topology.yaml` define, and which types exist?
28. When does a config change need a restart?
29. How do you validate a config before rollout?
30. Describe three misconfigurations and their symptoms.

## 12. Sources and review notes

- Parameter semantics, defaults, option lists, node states, `ReturnToService`, `SlurmdTimeout`, `TaskPlugin` recommendation, `cgroup.conf` options and defaults, `topology.yaml` types: Slurm man pages `slurm.conf(5)`, `cgroup.conf(5)`, `topology.yaml(5)`, `slurmd(8)` read from SchedMD/slurm commit `521370b` (development version 26.11.0rc1). Option availability differs by release (for example `Exclusive`).
- Concepts and the standard operational picture: *Supercomputers for Linux SysAdmins* chapter 15 (Slurm: partitions, nodes, GRES, accounting, troubleshooting), restated in my words; the existing 6.7 chapter of this handbook for the surrounding architecture.
- Original: `code/part06/slurmconf_lint.py` (tested on two files) and the failure table.
- Unverified: behaviour on specific older releases, cgroup v2 details on your kernel, the effect of SMT choices on your workloads.
