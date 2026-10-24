---
id: "c06-17"
title: "6.17 Other schedulers: PBS, Torque, LSF and Flux"
sidebar_label: "6.17 Other schedulers: PBS, Torque, LSF and Flux"
sidebar_position: 17
description: "The other batch schedulers you will meet: OpenPBS/PBS Professional and the legacy Torque, IBM Spectrum LSF, and Flux (El Capitan's workload manager): architecture, request syntax, a command map against Slurm, a tested PBS-to-Slurm directive converter, and guidance for migrations and mixed environments"
status: "drafted"
tier: "3"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.17 Other schedulers: PBS, Torque, LSF and Flux

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | Laptop (converter); optional single-node installs of OpenPBS or Flux |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. PBS facts from the OpenPBS man pages (openpbs/openpbs commit `cd7ab5e`, 2026-04-10), Flux facts from the flux-core documentation (commit `40ecc8d`, 2026-10-23). LSF and Torque are described from general knowledge and the SCL book's Torque chapter: **unverified**. `code/part06/pbs2slurm.py` was run on one test script. No scheduler other than the converter was executed; labs **untested** |

## Why this matters for AI infrastructure

Slurm dominates GPU training clusters, but you will inherit or integrate with others: universities and national labs on PBS Professional or OpenPBS, financial and EDA shops on IBM Spectrum LSF, LLNL-lineage systems on Flux, legacy clusters on Torque, plus customers whose scripts are written for another syntax. Knowing the concepts that all of them share, and being able to translate between them, makes you useful in migrations (a common project when a site moves to Slurm or to a Kubernetes-based stack) and in interviews.

## Prerequisites and outcomes

Needs 6.7 to 6.11. After this chapter you can:

- Describe the architecture of PBS (server, scheduler, MOM, comm), Torque, LSF and Flux, and how each differs from Slurm.
- Translate job scripts and commands between PBS, Slurm, LSF and Flux for common requests (nodes, GPUs, time, arrays, dependencies).
- Explain PBS's `select`/`place` model and Flux's nested-instance model, the two ideas furthest from Slurm's.
- Plan a migration: inventory, translation, policy mapping, accounting continuity, user retraining, parallel run.

## 1. What all batch schedulers share

A **queue/partition** concept; a **server/controller** holding state; a **per-node daemon** (MOM in PBS, `sbatchd` in LSF, broker in Flux, `slurmd`); a **policy engine** (priority, fair-share, backfill, limits, preemption); a **job script with directives** in comments; **arrays**, **dependencies**, **interactive** jobs; **accounting**. Differences are in vocabulary, resource-request model, defaults and extensibility. The SCL book devotes a chapter to OpenPBS/Torque because its target readers meet them; the same skills transfer.

## 2. PBS: OpenPBS and PBS Professional

OpenPBS is the open-source release of PBS Professional (Altair, since open-sourced). Components (from the `pbs(8B)` family of man pages): **`pbs_server`** (job and queue database, accepts jobs), **`pbs_sched`** (the scheduler: decides what runs where, with a policy configured in `sched_config` and resource definitions), **`pbs_mom`** (the execution daemon on each node, "Machine Oriented Mini-server"), **`pbs_comm`** (communication/relay for large clusters), and a data service (Postgres). Administration with `qmgr`, `pbsnodes`, `qstat`, `qenable`/`qdisable`/`qstart`/`qstop`, `tracejob`, hooks written in Python (`pbs_python`) for admission/execution control.

### Request model: select and place

PBS asks for resources as **chunks**. From `qsub(1B)`:

```text
-l select=[<N>:]<chunk>[+[<N>:]<chunk> ...]        chunk = <resource>=<value>[:<resource>=<value>...]
-l place=[<arrangement>][:<sharing>][:<grouping>]  arrangement: free | pack | scatter | vscatter
                                                   sharing: excl | shared | exclhost
                                                   grouping: group=<resource>
```

Example: `#PBS -l select=2:ncpus=64:mpiprocs=8:ngpus=8:mem=500gb` asks for two identical chunks (each at least 64 CPUs, 8 MPI processes, 8 GPUs, 500 GB), `#PBS -l place=scatter:excl` puts them on different hosts, exclusively. `+` joins different chunks (a heterogeneous request such as one big-memory chunk plus several GPU chunks), a natural fit for heterogeneous jobs where Slurm needs special "heterogeneous job" syntax. Do not mix old-style (`-l nodes=...:ppn=`) with `select` (the man page warns of an error). Chunks map to **vnodes** (virtual nodes: a host can be split into several vnodes, for example per NUMA domain or per GPU), so "node" has a looser meaning than in Slurm.

Other directives: `-N` name, `-q` queue, `-J X-Y[:Z][%max]` arrays (indices; `%max` caps running sub-jobs; "job arrays are always rerunnable"), `-W depend=afterok:ID[:ID]` (types `after`, `afterok`, `afternotok`, `afterany`, `before...`, `on:N`), `-o/-e/-j`, `-v`/`-V` environment, `-l walltime=HH:MM:SS`, `-m/-M` mail, `-r` rerunnable, `-I` interactive, `-A` account.

Environment variables: `PBS_JOBID`, `PBS_O_WORKDIR`, `PBS_NODEFILE` (a file listing allocated hosts, one line per slot), `PBS_ARRAY_INDEX`, `PBS_ARRAYID`.

### Torque

Torque (from the old Maui/Torque stack, originally Cluster Resources/Adaptive Computing) has the same lineage as PBS (it forked OpenPBS 2.3.12), with `qsub -l nodes=2:ppn=16`, `pbs_server`, `pbs_mom`, and the Maui or Moab scheduler for policy (Torque's built-in scheduler is basic). The SCL book walks through installing Torque, configuring the MOM on compute nodes, customising the scheduler, and job-control commands. It is **legacy**: new clusters choose Slurm or PBS Pro/OpenPBS; the open-source Torque line is no longer a good greenfield choice (from general knowledge: verify the project's current status before relying on it).

### Strengths and weaknesses

Strong: flexible resource chunks and placement, hooks, mature in some industries, good Windows/Linux history. Weaker for GPU AI practice: smaller ecosystem of AI tooling (pyxis, NGC reference recipes, Kubernetes bridges), fewer GPU-specific features out of the box than Slurm's GRES/`--gpus*`, and less community knowledge in AI-lab hiring pools.

### Setting up Torque and customising its scheduler

Naming caution from the SCL book: the *original* OpenPBS (MRJ, 1998, unsupported since about 2004), **Torque** (Adaptive Computing's fork of it) and **PBS Professional** (Altair's commercial product, later released as the *new* OpenPBS in 2020) are three different code lines; "OpenPBS" in a document may mean either the old or the new one. The sketch below is the classic Torque flow (from the book and general memory; paths vary by build and version, **unverified**):

1. Install the Torque packages on the head node (`pbs_server`, client commands, `trqauthd`) and `pbs_mom` plus the client on each compute node.
2. Initialise the server database once (`torque.setup <user>` or `pbs_server -t create`), then list compute nodes in `server_priv/nodes` with their CPU counts (`node01 np=16 gpus=4`).
3. On each compute node point the MOM at the server (`mom_priv/config` with `$pbsserver head`, and `$logevent`), start `pbs_mom`.
4. Create queues and limits with `qmgr` (`create queue batch`, `set queue batch queue_type = Execution`, `set queue batch resources_max.walltime = 48:00:00`, `set queue batch enabled = True`, `started = True`, `set server default_queue = batch`, `set server scheduling = True`).
5. Scheduling policy: Torque ships a simple FIFO `pbs_sched`; real sites use the **Maui** or **Moab** schedulers (fair-share, backfill, reservations, priority weights in `maui.cfg`), connecting to `pbs_server` as an external scheduler.
6. Users then use `qsub`, `qstat`, `qdel`, `qhold`/`qrls`, `qalter`; admins use `qmgr`, `pbsnodes`, `qrun`, `tracejob`.

## 3. IBM Spectrum LSF (general knowledge, unverified)

LSF (Load Sharing Facility) is a commercial scheduler (IBM Spectrum LSF) common in EDA, finance and some HPC centres. Architecture: **mbatchd** (master batch daemon) and **mbschd** (scheduler) on the master host (with failover candidates), **sbatchd** and **res** on each execution host, **LIM** (Load Information Manager) collecting host load and resource information. Concepts: **queues** with their own policies, **hosts and host groups**, **resource requirement strings** (`select[...] rusage[...] span[...] order[...]`), fair-share and preemption, "job slots". Commands: `bsub` (submit; `bsub -n 16 -R "span[ptile=8]" -gpu "num=4" -q gpu -W 12:00 < script`), `bjobs`, `bkill`, `bqueues`, `bhosts`, `lsload`, `bhist`, `bacct`, `bmod`, `bswitch`, `bpeek`. Script directives: `#BSUB -n`, `-q`, `-W`, `-o`, `-J name[1-100]%10`. Environment: `LSB_JOBID`, `LSB_HOSTS`, `LSB_DJOB_HOSTFILE`, `LSB_JOBINDEX`. Strengths: enterprise support, license-aware scheduling, mature policy model, LSF multicluster. Many current AI sites using LSF are migrating to Slurm or Kubernetes. Verify all of this against IBM documentation before use.

## 4. Flux

Flux (Lawrence Livermore National Laboratory and collaborators; `flux-core`) is a framework for resource management with a very different shape. From its docs:

- A **Flux instance** is a set of `flux-broker` processes (a tree-based overlay network) that "can be started by most launchers that can start MPI jobs" and by a user without administrator privilege, e.g. inside a Slurm allocation or a Kubernetes pod.
- The key idea: **every job can itself be a Flux instance** ("subinstance"). `flux batch SCRIPT` "submits SCRIPT to run as the initial program of a Flux subinstance"; once it exits the subinstance ends and resources return to the enclosing instance. Commands run inside the script (`flux run`, `flux submit`) refer to the subinstance; `flux proxy JOBID` connects a shell to a running subinstance (`flux uptime` shows `depth`, `size`). **Hierarchical scheduling** lets users run their own scheduler policy and millions of tasks inside an allocation without loading the system scheduler, the strength for ensemble and AI-workflow workloads.
- Commands: `flux run` (run a job, interactive), `flux submit` (queue), `flux batch` (script as subinstance, `#flux:` directive lines), `flux alloc` (interactive subinstance), `flux bulksubmit` (many jobs), `flux jobs` (list), `flux cancel`, `flux resource list`, `flux queue`, `flux top`, `flux pstree`, `flux dmesg`, `flux uptime`, `flux config`.
- Request options (`flux-run`/`submit`): `-n` tasks, `-c` cores per task, `-g` GPUs per task, `-N` nodes, `--tasks-per-node`, `--gpus-per-node`, `-x` exclusive, `-t` time limit, `-q` queue, `-B` bank (accounting), `--dependency=URI` (RFC 26 dependency URIs with schemes such as `afterok`: "dependency chains behave like shell command separators", `afterok` like `&&`).
- Scheduler: the separate `flux-sched` project provides the graph-based resource model **Fluxion**; flux-core alone provides services (job manager, KVS, message bus).
- **Maturity** (docs, "Flux Maturity", late 2025): Flux is the sole system workload manager on **El Capitan** (then number one on the TOP500) and its unclassified sister systems at LLNL. The docs' migration guide ("Migrating from Slurm") tells large centres not to leave Slurm yet ("check back with us at the end of 2026") and lists missing features: rolling upgrades (nodes must run exactly the same flux-core version until 1.0), restarting Flux without killing running jobs, immovable future reservations, among others. Flux also coexists with Slurm as an enhanced step manager and portability layer.
- Relevance for AI: nested scheduling for hyperparameter sweeps and agent/RL workloads; Kubernetes integration (the Flux Operator) to run MPI-style jobs; strong tooling for ensembles. Not common on commercial GPU clouds.

## 5. Command and concept map

| Task | Slurm | PBS (OpenPBS/Pro) | LSF | Flux |
|---|---|---|---|---|
| Submit script | `sbatch s.sh` | `qsub s.sh` | `bsub < s.sh` | `flux batch s.sh` |
| Run interactive | `srun --pty bash` / `salloc` | `qsub -I` | `bsub -Is bash` | `flux alloc` / `flux run` |
| List jobs | `squeue` | `qstat` | `bjobs` | `flux jobs` |
| Cancel | `scancel` | `qdel` | `bkill` | `flux cancel` |
| Node status | `sinfo`, `scontrol show node` | `pbsnodes -a` | `bhosts`, `lsload` | `flux resource list` |
| Queue/partition | partition | queue | queue | queue |
| Nodes + CPUs | `-N 2 -n 16` | `-l select=2:ncpus=8` | `-n 16 -R "span[ptile=8]"` | `-N 2 -n 16` |
| GPUs | `--gpus-per-node=8` | `ngpus=8` in chunk | `-gpu "num=8"` | `--gpus-per-node=8` / `-g` |
| Memory | `--mem=64G` | `mem=64gb` in chunk | `-R "rusage[mem=65536]"` | via resources/constraints |
| Time | `--time=HH:MM:SS` | `-l walltime=HH:MM:SS` | `-W HH:MM` | `-t MINUTES` or FSD |
| Array | `--array=0-9%3` | `-J 0-9%3` | `-J "name[0-9]%3"` | `flux bulksubmit` |
| Dependency | `--dependency=afterok:ID` | `-W depend=afterok:ID` | `-w "done(ID)"` | `--dependency=afterok:ID` |
| Exclusive node | `--exclusive` | `-l place=excl` | `-x` | `-x` |
| Job ID variable | `SLURM_JOB_ID` | `PBS_JOBID` | `LSB_JOBID` | `FLUX_JOB_ID` |
| Node list | `SLURM_JOB_NODELIST` | `PBS_NODEFILE` | `LSB_DJOB_HOSTFILE` | `flux hostlist` |
| Launch MPI | `srun` | `mpiexec` / `pbsdsh` | `mpirun` / `blaunch` | `flux run` |

(LSF entries are from memory: verify.)

## 6. A tested translator

`code/part06/pbs2slurm.py` converts the common `#PBS` directives to `#SBATCH`: name, queue (to partition), account, output/error, array (with `%` throttle), mail, `depend=`, `walltime`, `place=...excl` (to `--exclusive`), and `select` with `ncpus`, `mpiprocs`, `ngpus`, `mem`. It also rewrites `$PBS_JOBID`, `$PBS_O_WORKDIR`, `$PBS_ARRAY_INDEX`, and flags `$PBS_NODEFILE`. On a test script:

```text
#PBS -N bert                              ->  #SBATCH --job-name=bert
#PBS -q gpuq                              ->  #SBATCH --partition=gpuq
#PBS -l select=2:ncpus=64:mpiprocs=8:ngpus=8:mem=500gb
                                          ->  #SBATCH --nodes=2 / --ntasks-per-node=8 / --cpus-per-task=8
                                              / --gpus-per-node=8 / --mem=500G
#PBS -l walltime=12:00:00                 ->  #SBATCH --time=12:00:00
#PBS -l place=scatter:excl                ->  #SBATCH --exclusive
#PBS -J 0-9%3                             ->  #SBATCH --array=0-9%3
#PBS -m abe                               ->  #SBATCH --mail-type=FAIL,BEGIN,END
#PBS -W depend=afterok:1234.server        ->  #SBATCH --dependency=afterok:1234.server   (job id must be edited)
#PBS -l software=matlab                   ->  # TODO unmapped resource: software=matlab    (a PBS custom resource -> Slurm licenses/features)
cd $PBS_O_WORKDIR                         ->  cd $SLURM_SUBMIT_DIR
mpirun -np 16 -machinefile $PBS_NODEFILE python train.py
                                          ->  ... <use: scontrol show hostnames $SLURM_JOB_NODELIST> (and prefer srun)
```

The `ncpus=64` per chunk with `mpiprocs=8` became `--cpus-per-task=8` (64/8). That is a **semantic translation**, not a mechanical one: PBS `ncpus` counts CPUs per chunk, Slurm `--cpus-per-task` per task. Things the tool deliberately does not translate: heterogeneous `select` with `+` chunks (flagged as TODO), vnode-specific placement, custom resources (map to Slurm features, licenses or GRES), hooks (rewrite as `job_submit` plugins), queue policy (fair-share, limits: rebuild per 6.9), job IDs in dependencies, `qsub -I` interactive semantics, and the MPI launch line (replace `mpirun -machinefile` by `srun`). Run the result through `sbatch_lint.py` (6.11).

## 7. Migration plan (any scheduler to Slurm)

1. **Inventory**: queues, node classes, resource types, limits, fair-share trees, reservations, hooks/plugins, license servers, user scripts (scan with `grep -r '#PBS'` / `'#BSUB'`), accounting integrations, web portals, workflow tools that call `qsub`/`bsub`.
2. **Policy mapping**: queues to partitions/QOS, limits to association/QOS limits, fair-share shares to accounts, preemption rules to `PreemptType` (6.9), custom resources to GRES/features/licenses, hooks to `job_submit` and prolog/epilog (6.14).
3. **Translate** scripts (automated first pass plus review), build a compatibility shim only if unavoidable (Slurm ships `qsub`-like wrappers in contribs; PBS-compatible wrappers exist: check availability for your version).
4. **Accounting continuity**: export historical usage; seed fair-share if desired; keep old reports for audits.
5. **Parallel run**: split nodes; dual-submit tests; compare job outcomes; train users; publish a command-map cheat sheet.
6. **Cutover** by node groups; keep rollback window; decommission after one full allocation cycle.
7. Revisit the **workflow layer** (Airflow, Nextflow, Snakemake, DAGs) which usually has a Slurm executor already.

## 8. Mixed environments and bridges

- Run **Flux or Ray or Dask inside a Slurm allocation** for fine-grained task scheduling (nested/hierarchical scheduling) without touching the system scheduler.
- Slurm to Kubernetes: 6.16; Kubernetes to Slurm bridges (queue-based "virtual kubelets") exist but are niche.
- Workflow tools abstract the scheduler: Nextflow, Snakemake, Airflow providers, Parsl, Dask-Jobqueue support Slurm, PBS and LSF through executors.
- Cloud bursting: PBS and LSF have cloud connectors; Slurm has power-save/cloud nodes (6.15).

## 9. Lab (converter tested; rest untested)

1. Run `pbs2slurm.py` on two of your own PBS scripts; fix every TODO by hand; lint with `sbatch_lint.py`.
2. Install OpenPBS in a single-node container or VM; submit a `select` job; inspect `pbsnodes -a` and `qstat -f`.
3. Install Flux (`flux start --test-size=4` in a container); run `flux batch` with nested `flux run`; use `flux proxy` and `flux uptime` to observe depth.
4. Write the command-map cheat sheet for your site.
5. Draft a migration inventory template listing all items in section 7 step 1.
6. Extend the converter to handle `-l nodes=2:ppn=16` (Torque-style) and heterogeneous select.

## 10. Interview angles

- What does PBS's `select` / `place` express that Slurm's `-N/-n` does not?
- Compare PBS MOM, LSF sbatchd and Slurm slurmd.
- What is a Flux subinstance and why is hierarchical scheduling useful?
- You inherit a PBS cluster and must move it to Slurm. Plan the migration.
- How would you translate a PBS script requesting `select=4:ncpus=32:ngpus=4:mem=128gb`?
- Which schedulers run the top supercomputers?
- Why do most GPU clouds standardise on Slurm or Kubernetes?

## 11. Checkpoint questions (25)

1. Name the PBS daemons and roles.
2. What is a PBS chunk? A vnode?
3. Explain `place=scatter:excl`.
4. How are PBS arrays and dependencies written?
5. What are `PBS_NODEFILE` and `PBS_O_WORKDIR`?
6. What is Torque's relationship to PBS and Maui/Moab?
7. List LSF's main daemons.
8. Give a `bsub` GPU example (unverified).
9. What is a Flux instance and how is it started?
10. What does `flux batch` do?
11. What does `flux proxy` do?
12. What is hierarchical scheduling?
13. What is `flux-sched`/Fluxion?
14. Which production system runs Flux as its only workload manager?
15. Name two limitations in Flux's own migration guide.
16. Map `sbatch`, `squeue`, `scancel`, `sinfo` to PBS and LSF.
17. How do you express "8 GPUs per node, exclusive" in each of the four?
18. Why is ncpus-per-chunk not the same as `--cpus-per-task`?
19. What can't an automatic PBS-to-Slurm translator do?
20. How do PBS hooks map to Slurm?
21. What are the first steps of a scheduler migration?
22. How do you preserve fair-share history?
23. Which workflow tools abstract the scheduler?
24. How can you run a nested scheduler inside a Slurm job?
25. Why is Torque a poor greenfield choice?

## 12. Sources and review notes

- OpenPBS: man pages `qsub(1B)`, `pbs(8B)` family, `pbs_resources(7B)` (openpbs/openpbs commit `cd7ab5e`). Torque and its place in Linux cluster practice: *Supercomputers for Linux SysAdmins* chapter 14 (installing and configuring Torque, MOM, scheduler, job control), restated in my words.
- Flux: flux-core documentation (`flux-batch(1)`, job parameter and dependency pages, "Migrating from Slurm" in the admin guide), commit `40ecc8d`.
- LSF: general knowledge only; verify with IBM documentation. SUNK/other Kubernetes bridges: see 6.16.
- Original: `code/part06/pbs2slurm.py` and its run on `/tmp` test input, the command map, the migration plan.
- Unverified: all LSF command syntax, the current status of Torque, the PBS wrappers shipped with Slurm, Flux roadmap dates.
