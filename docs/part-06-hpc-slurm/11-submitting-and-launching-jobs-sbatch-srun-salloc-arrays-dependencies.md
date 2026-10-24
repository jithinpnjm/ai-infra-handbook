---
id: "c06-11"
title: "6.11 Submitting and launching jobs: sbatch, srun, salloc, arrays, dependencies"
sidebar_label: "6.11 Submitting and launching jobs: sbatch, srun, salloc, arrays, dependencies"
sidebar_position: 11
description: "How users run work on Slurm: batch scripts and directives, allocations versus steps, srun inside and outside allocations, interactive jobs, job arrays, dependencies, signals and requeue, output files, environment variables, monitoring and cancelling, and the patterns for AI training jobs, with a linter for batch scripts"
status: "drafted"
tier: "1"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.11 Submitting and launching jobs: sbatch, srun, salloc, arrays, dependencies

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Slurm cluster; the linter script needs only Python 3 |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Option names, defaults, patterns and environment variables were checked against the `sbatch`, `srun`, `salloc`, `scontrol` and `slurm.conf` man pages (SchedMD/slurm commit `521370b`, 2026-10-23, development version 26.11.0rc1; older releases lack some options). `code/part06/sbatch_lint.py` was run on two test scripts (output shown). No Slurm daemon was run; cluster examples are **untested** |

## Why this matters for AI infrastructure

The user-facing interface to a GPU cluster is a handful of commands. Researchers lose hours to avoidable mistakes: a multi-node script that runs everything on one node, an array of 1,000 jobs with no throttle that floods the file system, a requeued job that overwrites its own log, a training run killed at the time limit without a checkpoint, `mpirun` launched inside a batch script without binding. Operators write the documentation, templates, `job_submit` plugins and wrapper scripts that prevent these, and answer the tickets when they happen. This chapter is the working vocabulary for both sides.

## Prerequisites and outcomes

Needs 6.2, 6.7 to 6.10. After this chapter you can:

- Explain the difference between an allocation, a batch script, and job steps, and which command creates which.
- Write correct batch scripts for single-GPU, multi-GPU, multi-node and array workloads, including directives, environment handling, signals and requeue.
- Use `srun` inside allocations (steps, `--exact`, `--overlap`), `salloc` for interactive work, and understand `--pty` and interactive steps.
- Build array, dependency and pipeline workflows; know the failure behaviour of dependencies.
- Read and use the SLURM environment variables for rank/world-size/rendezvous set-up.
- Monitor, inspect, modify and cancel jobs with `squeue`, `scontrol`, `sacct`, `scancel`.
- Lint scripts for common mistakes and write submission templates for a site.

## 1. Allocations, batch jobs and steps

Three concepts:

- An **allocation** is a set of resources (nodes, CPUs, GPUs, memory) held for a time limit under a job ID.
- A **batch job** (`sbatch script`) queues a request; when resources are available, Slurm runs the script on the **first allocated node** as the "batch step". Commands in the script run only there unless launched across the allocation.
- A **job step** (`srun ...`) launches tasks across (part of) the allocation. A batch script typically contains one or more `srun` steps; each gets an ID `JOBID.0`, `JOBID.1`, etc. Accounting records each step.

Commands:

| Command | Does |
|---|---|
| `sbatch script.sh` | Submit a batch script; returns the job ID immediately |
| `salloc ...` | Obtain an allocation and start a shell (or command) with the allocation environment; you then run `srun` steps interactively |
| `srun ...` | Inside an allocation: launch a step. Outside one: create an allocation **and** run the command (blocking) |
| `scancel`, `squeue`, `sinfo`, `scontrol`, `sacct`, `sstat`, `sprio`, `sshare`, `sreport` | Control and query |

Rule: in a **multi-node** batch script, commands without `srun` execute once, on the first node. The linter (section 9) warns about multi-node scripts that contain neither `srun` nor `mpirun`.

## 2. A batch script

```bash
#!/bin/bash
#SBATCH --job-name=bert-pretrain
#SBATCH --partition=gpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8          # one task per GPU
#SBATCH --gpus-per-node=8
#SBATCH --cpus-per-gpu=12
#SBATCH --mem=0                      # all memory on the (exclusive) node
#SBATCH --exclusive
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --signal=B:USR1@300          # warn the batch shell 5 minutes before the limit
#SBATCH --output=logs/%x-%j.out
#SBATCH --open-mode=append

set -euo pipefail
module purge
module load cuda/12.4 nccl/2.21
export OMP_NUM_THREADS=$SLURM_CPUS_PER_GPU   # see section 7; set per your site
srun --mpi=pmix python train.py --resume-if-exists
```

Details (from `sbatch(1)`):

- `#SBATCH` lines must precede the first executable command; they are comments to the shell. Command-line options override them. The script must start with `#!`.
- Time: `--time=D-HH:MM:SS` or `HH:MM:SS`. Provide it (6.9 on backfill). `--time-min` lets a flexible job start with less.
- **Output**: by default stdout and stderr go to `slurm-%j.out` (`slurm-%A_%a.out` for arrays) in the submission directory. Filename patterns include `%j` job ID, `%A`/`%a` array job/index, `%x` job name, `%N` short hostname (one file per node), `%u` user, `%t` task id (srun), `%%`. **The directory in `--output` must exist before the job starts**, or the job fails silently with no log; create it in a wrapper or submit from a directory that has it.
- `--open-mode=append|truncate`: default from the cluster's `JobFileAppend`. A **requeued** job reuses the job ID; with truncate mode the second run erases the first run's log, so use `append` or include something unique.
- `--export`: default `ALL` propagates the submitter's environment into the job. That includes loaded modules and conda environments, which makes jobs depend on whatever the user's shell had. For reproducibility use `--export=NONE` plus an explicit `module purge`/`module load` or `source` in the script (note `NONE` also means you must use absolute paths or set `PATH` yourself; `--export=NONE` with `sbatch` also needs `--get-user-env` or login-shell tricks on some sites, check local docs).
- **Containers**: `--container` is available in recent releases (OCI), and sites using pyxis add `--container-image` etc. (6.13).
- **Constraints**: `--constraint="h100&ib"` selects nodes by feature (6.8).
- `--wrap="command"` submits a one-liner without a script file.
- `--test-only` validates and reports when and where the job would start, without submitting. `--parsable` prints only the job ID for scripting.
- Mail: `--mail-type=END,FAIL --mail-user=...` (only if the site runs mail).
- `--begin=now+1hour`, `--deadline=...`, `--hold`, `--nice`, `--reservation`, `--qos`, `--account`: scheduling controls (6.9).

### Environment variables

Slurm sets many; those you will use constantly (all present in the man pages):

| Variable | Meaning |
|---|---|
| `SLURM_JOB_ID`, `SLURM_JOB_NAME`, `SLURM_JOB_PARTITION`, `SLURM_SUBMIT_DIR` | Job identity and where you submitted from |
| `SLURM_JOB_NODELIST` (`SLURM_NODELIST`), `SLURM_JOB_NUM_NODES` (`SLURM_NNODES`) | Nodes of the allocation; the nodelist is compressed (`gpu[01-04]`): expand with `scontrol show hostnames "$SLURM_JOB_NODELIST"` |
| `SLURM_NTASKS`, `SLURM_NTASKS_PER_NODE`, `SLURM_TASKS_PER_NODE`, `SLURM_CPUS_PER_TASK`, `SLURM_CPUS_ON_NODE`, `SLURM_MEM_PER_NODE` | Shape of the allocation |
| `SLURM_PROCID`, `SLURM_LOCALID`, `SLURM_NODEID` | Set **per task by srun**: global rank, node-local rank, node index |
| `SLURM_ARRAY_JOB_ID`, `SLURM_ARRAY_TASK_ID`, `SLURM_ARRAY_TASK_COUNT` | Array identity |
| `SLURM_RESTART_COUNT` | How many times the job was requeued (0 on the first run) |
| `SLURM_JOB_GPUS`, `SLURM_GPUS_ON_NODE`, ... | GPU information (6.10) |

`SLURM_PROCID` and friends exist only inside tasks launched by `srun`, not in the batch shell (the batch script itself has `SLURM_NODEID=0`). This is the usual "variable is empty" confusion.

### Distributed-training rendezvous from Slurm variables

PyTorch needs a master address, port, world size and rank. With one task per GPU launched by `srun`:

```bash
MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
MASTER_PORT=$((10000 + SLURM_JOB_ID % 20000))   # avoid collisions between jobs on shared nodes
export MASTER_ADDR MASTER_PORT
srun bash -c 'export RANK=$SLURM_PROCID LOCAL_RANK=$SLURM_LOCALID WORLD_SIZE=$SLURM_NTASKS; exec python train.py'
```

Alternative: one task per node launching `torchrun --nnodes=$SLURM_NNODES --nproc-per-node=8 --rdzv-backend=c10d --rdzv-endpoint=$MASTER_ADDR:29500 train.py` (6.12 compares the two). The `MASTER_PORT` formula is a convenience, not a guarantee; some sites provide port management (`--resv-ports`, MPI/PMIx plugins).

## 3. srun

`srun` launches a **step**: it connects to the allocation (or creates one), starts the requested number of tasks on the nodes, forwards stdin/stdout/stderr, and returns the exit status. Key options (from `srun(1)`): `-n/--ntasks`, `-N/--nodes`, `--ntasks-per-node`, `-c/--cpus-per-task`, `--cpu-bind`, `--mem-bind`, `--gpu-bind`, `--gpus-per-task`, `--mpi=<type>` (`list` shows plugins, `pmix` and `pmi2` common), `--export`, `-K/--kill-on-bad-exit`, `--label` (prefix output with the task id), `--output/--error` per-step patterns, `--time`, `--wait`, `--pty`.

Steps inside an allocation:

- **Steps do not share resources by default** with other parallel steps. A second concurrent `srun` that wants CPUs/GPUs already used by the first step **waits or is rejected** unless `--overlap` is given ("allows steps to share all resources (CPUs, memory, and GRES) with all other steps"). This is why `srun nvidia-smi` in a second terminal of an interactive allocation can hang, and why monitoring a running training job's GPUs is done with `srun --overlap --jobid=JOBID ...` (6.14).
- `--exact` limits a step to exactly the resources it requested; without it a step may use "all non-GRES resources on each node in the step allocation". For several concurrent steps with different shapes use `--exact` (often the default behaviour in current versions through `--cpus-per-task`/`--cpus-per-gpu`; check yours).
- `-K/--kill-on-bad-exit`: terminate the whole step if any task exits non-zero. Default from the cluster's `KillOnBadExit`. For tightly coupled jobs you want this; otherwise one dead rank leaves the others hanging in a collective until the time limit (a classic waste of GPU hours).
- `srun` without an allocation creates one for the command: `srun -N1 --gres=gpu:1 --pty bash` is an interactive session in a single command.
- `srun --jobid=<id>` attaches to a running job's allocation (permission: the user's own job).

### MPI and launching

`srun --mpi=pmix` hands rank wire-up to Slurm's PMIx plugin (6.4, 6.12); `mpirun` inside a script works with Open MPI's Slurm integration but does its own launching and binding. Prefer `srun` so that Slurm sets binding (`--cpu-bind`, `--gpu-bind`), tracks processes in the job cgroup, and accounts usage per step.

## 4. Interactive jobs

```bash
salloc --partition=gpu --gres=gpu:1 --cpus-per-gpu=8 --mem-per-gpu=64G --time=2:00:00
# a shell opens; Slurm variables are set; then:
srun --pty bash                # a shell on the compute node
srun python quick_test.py      # or run a step
exit                           # releases the allocation
```

Or in one step: `srun --partition=gpu --gres=gpu:1 --time=1:00:00 --pty bash`.

Where does `salloc`'s own shell run? By default on the submission host (the login node). Many sites want it on the compute node: the current mechanism is `LaunchParameters=use_interactive_step` in `slurm.conf`, which makes `salloc` start `srun` with `InteractiveStepOptions` (default `--interactive --preserve-env --pty $SHELL`, per the man page) so you land on a node of the allocation. The "interactive step" consumes no resources, so other steps can run in parallel. (The old `SallocDefaultCommand` parameter is no longer in the `slurm.conf` man page.)

Interactive etiquette and policy: short time limits, a dedicated `interactive`/`debug` partition with high priority and small size, MIG or shared GPUs for notebooks (6.10), idle-job reaping, and Open OnDemand for Jupyter and VS Code (6.25). An idle `salloc` holding 8 GPUs for a day is an expensive nap; consider a `job_submit` plugin or epilog that kills idle interactive allocations.

## 5. Job arrays

`sbatch --array=0-99%10 script.sh` creates 100 tasks (indices 0 to 99), at most 10 running at once. Forms: `0-15`, `0,6,16-32`, `0-15:4` (step), `%N` throttle. Indices must be below `MaxArraySize`, and the count is limited by `max_array_tasks` in `SchedulerParameters` (man page). Heterogeneous jobs cannot be arrays.

Each task is an independent job with `SLURM_ARRAY_TASK_ID`, `SLURM_ARRAY_JOB_ID` (the first task's ID, "the array's master") and its own `SLURM_JOB_ID`. Default output is `slurm-%A_%a.out`. Manage collectively (`scancel 12345` cancels all; `scancel 12345_7` one) or individually; `squeue` condenses pending arrays (`-r` expands).

Typical use: hyperparameter sweeps, per-shard preprocessing, evaluation over checkpoints.

```bash
#SBATCH --array=0-31%8
CONFIG=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" configs.txt)
srun python train.py $CONFIG
```

Good practice: always throttle (`%N`) to protect shared storage and fair-share; keep tasks reasonably long (arrays of 5-second tasks overload the controller; batch them); write results per task into separate directories; for very large sweeps use a workflow tool or `srun --multi-prog`/GNU parallel inside one allocation.

## 6. Dependencies and pipelines

`--dependency=<type>:<jobid>[:<jobid>...]` defers a job until conditions on other jobs are met (man page):

| Type | Starts when |
|---|---|
| `after:ID[+minutes]` | Listed jobs have started or been cancelled (plus optional delay) |
| `afterany:ID` | They have terminated for any reason (**default type**) |
| `afterok:ID` | They completed successfully (exit code 0) |
| `afternotok:ID` | They failed (non-zero, cancelled, timeout, node failure): for cleanup or notification jobs |
| `aftercorr:ID` | The matching task of an array completed successfully |
| `afterburstbuffer:ID`, `singleton` | After burst-buffer stage-out; only one job of the same name/user at a time |

Combine with `,` (all must hold) or `?` (any); only one separator type per expression: `afterok:20:21,afterany:23` versus `afterok:20:21?afterany:23`.

**Failure semantics matter**: "once a job dependency fails due to the termination state of a preceding job, the dependent job will never be run, even if the preceding job is requeued and has a different termination state in a subsequent execution". By default such a job stays pending forever with reason `DependencyNeverSatisfied`; `--kill-on-invalid-dep=yes` (or the cluster's `kill_invalid_depend`) cancels it. Pipelines can therefore leave zombie pending jobs; always clean up.

Pattern for a training chain that continues past the time limit:

```bash
J1=$(sbatch --parsable train.sh)
J2=$(sbatch --parsable --dependency=afterany:$J1 train.sh)      # resume run 2
J3=$(sbatch --parsable --dependency=afterok:$J2 evaluate.sh)
```

Use `afterany` between training segments (a timeout is a "failure") and have each segment resume from the latest checkpoint. For a self-resubmitting job, trap the warning signal, checkpoint, and `scontrol requeue $SLURM_JOB_ID`.

## 7. Time limits, signals, checkpoints, requeue

Training must survive the time limit, preemption (6.9) and node failures. Slurm tools:

- `--signal=[R:|B:]<sig>[@seconds]`: send a signal that many seconds before the limit (up to 60 seconds early due to resolution; if no time is given, 60 seconds). **By default only job steps are signalled, not the batch shell; use `B:` to signal the batch shell.** `R:` allows overlap with a reservation that has a start delay.
- On preemption, `GraceTime` (partition or QOS; 6.9) gives the SIGTERM-to-SIGKILL window.
- `--requeue` / `--no-requeue`: whether the job may be restarted from the beginning of the script, with the same job ID, after node failure, admin action or preemption. `SLURM_RESTART_COUNT` tells the script which attempt it is. `scontrol requeue JOBID` requeues explicitly.

A robust pattern:

```bash
#!/bin/bash
#SBATCH --signal=B:USR1@600 --requeue --open-mode=append
checkpoint_and_requeue() { scancel --signal=USR1 --batch-only ${SLURM_JOB_ID} 2>/dev/null || true; kill -TERM "$PID"; wait "$PID"; scontrol requeue "$SLURM_JOB_ID"; }
trap checkpoint_and_requeue USR1
srun python train.py --resume-latest &
PID=$!
wait "$PID"
```

(The pattern is the commonly used one; the exact signalling plumbing varies. The training program should handle SIGTERM/SIGUSR1 by writing a checkpoint, and the launcher must forward the signal to the ranks. Test it end to end before relying on it; Part 14 covers checkpointing strategy, and 6.12 launcher details.) The simplest dependable approach is **periodic checkpoints plus idempotent resume**, with the signal handler as an optimisation.

## 8. Monitoring, modifying, cancelling

```bash
squeue -u $USER -o "%.10i %.9P %.20j %.8T %.10M %.6D %R"      # job id, partition, name, state, runtime, nodes, reason/nodes
squeue -j JOBID --start                                         # estimated start
scontrol show job JOBID                                         # everything (Reason, TresPerNode, StdOut, WorkDir, NodeList...)
scontrol update job JOBID TimeLimit=+2:00:00                    # extend (privileged) or reduce
scontrol update job JOBID Dependency=afterok:123
scontrol hold JOBID ; scontrol release JOBID
sacct -j JOBID --format=JobID,JobName,Partition,State,ExitCode,Elapsed,TotalCPU,MaxRSS,AllocTRES%50
sacct -X -u $USER -S now-7days --format=JobID,State,Elapsed,NodeList
sstat -j JOBID.0 --format=JobID,AveCPU,MaxRSS                  # running steps
scancel JOBID ; scancel -u $USER --state=PENDING ; scancel --signal=USR1 JOBID
```

States to know: `PENDING`, `RUNNING`, `COMPLETING`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMEOUT`, `NODE_FAIL`, `OUT_OF_MEMORY`, `PREEMPTED`, `REQUEUED`, `SUSPENDED`. Reasons for pending are in 6.9 section 8. `scontrol show job` shows `ExitCode=0:15` as exit code and signal. After completion, `sacct` is the source (the controller forgets completed jobs after `MinJobAge`).

Peek into a running job: `srun --overlap --jobid=JOBID --pty bash` (lands on the first node, sharing resources), or `srun --overlap --jobid=JOBID -w NODE nvidia-smi`; check allowed by site policy (`pam_slurm_adopt` also allows SSH to nodes where you have a job).

## 9. A linter for batch scripts

`code/part06/sbatch_lint.py` parses `#SBATCH` lines and checks them against an option list extracted from the `sbatch` man page and against rules stated there or standard practice. Output for a good and a bad script:

```text
== good.sbatch
no findings
== bad.sbatch
ERROR no shebang line; sbatch rejects scripts that do not start with #!
warn  line 8: --tasks-per-node is not in the reference option list (typo, or a different Slurm version?)
warn  no --time: the partition default applies; backfill works best with an accurate limit (6.9)
ERROR --mem, --mem-per-gpu are mutually exclusive
ERROR --cpus-per-gpu is not compatible with --cpus-per-task
ERROR --gpus-per-task needs an explicit task count (-n/--ntasks or --ntasks-per-node with --nodes)
info  job array without a %N throttle can flood the scheduler and the file system
warn  requeued job writes to a fixed output name; use --open-mode=append or include %j
info  --requeue without --signal: the job gets no warning before preemption/time limit; checkpoint on SIGTERM/USR1
warn  module load without module purge: inherited modules can mix toolchains (6.6)
info  no 'set -e'/errexit: a failed setup step will not stop the script
info  mpirun inside a batch script: srun --mpi=pmix lets Slurm launch and bind the ranks (6.12)
```

Sites can run a linter from a `job_submit` plugin (Lua) or a wrapper around `sbatch`, rejecting or warning on bad requests, setting defaults (partition, time, GPU CPU/memory defaults, account) and routing jobs. Keep the policy visible: a clear message beats a silent rewrite.

## 10. Submission patterns for AI workloads

| Workload | Pattern |
|---|---|
| Single-GPU experiment | `--gpus=1 --cpus-per-gpu=8 --mem-per-gpu=...`, short time, `debug` or `interactive` partition |
| Multi-GPU single node | `--gpus-per-node=8 --ntasks-per-node=8 --exclusive`, `torchrun --standalone` or `srun` per GPU |
| Multi-node DDP/FSDP | `--nodes=N --ntasks-per-node=8`, `srun` or `torchrun` with rendezvous from `scontrol show hostnames` (6.12) |
| Hyperparameter sweep | Job array with `%throttle`, one config per index |
| Long run | Checkpoints every K minutes, `--requeue`, `--signal=B:USR1@...`, dependency chain |
| Data preprocessing | CPU array jobs on a cpu partition; write sharded outputs; later GPU job reads them |
| Evaluation after training | `--dependency=afterok:$TRAIN` or triggered from the training script |
| Inference server batch | One job per replica; health endpoint; service discovery via a shared file or the Slurm nodelist (or move serving to Kubernetes) |
| Debugging a hang | `salloc` same shape, `srun --pty`, `py-spy`, `NCCL_DEBUG=INFO` (6.12, 6.14) |

## 11. Common mistakes

- Output directory in `--output` does not exist: job fails without a log.
- Using `mpirun` or `torchrun` once per node incorrectly, or forgetting `srun` so everything runs on node 0.
- Asking `--gres=gpu:8` for a multi-node job and forgetting that it is per node.
- `--mem` or `--cpus-per-task` unset on GPU jobs: starved data loaders.
- `--export=ALL` default carrying a stale conda environment into jobs.
- A second concurrent `srun` that blocks because steps do not share resources.
- Dependencies on a job that times out with `afterok`: the chain dies silently.
- A requeued job overwriting its own log or restarting training from scratch.
- Massive arrays without throttle.
- `scancel` of a pending array element vs the whole array.
- Writing results to `$HOME` on a quota-limited file system.

## 12. Lab (untested except the linter)

1. Run `sbatch_lint.py` on your own scripts. Fix every ERROR and warn.
2. Write a 2-node, 16-rank hello script that prints `hostname`, `SLURM_PROCID`, `SLURM_LOCALID`, `SLURM_NODEID` via `srun`; compare the same commands run without `srun`.
3. Submit `--test-only`, then real; use `squeue --start`, `scontrol show job`, `sacct`.
4. Array with `%2` throttle over 6 indices; inspect output files and `squeue -r`.
5. Dependency chain train, evaluate with `afterok`; make the first fail and observe `DependencyNeverSatisfied`; add `--kill-on-invalid-dep=yes`.
6. Interactive: `salloc` then `srun --pty bash`; run a second `srun nvidia-smi` and observe blocking; retry with `--overlap`.
7. Time-limit rehearsal: `--time=00:03:00 --signal=B:USR1@60` with a script that traps USR1 and writes a "checkpoint" file; verify it fires before TIMEOUT, then add requeue and check `SLURM_RESTART_COUNT`.
8. Write a site template repository with scripts for the patterns in section 10 and a README.

## 13. Interview angles

- Explain allocation, batch step, job step. What runs where in a multi-node batch script?
- What is the difference between `sbatch`, `srun` and `salloc`?
- What does `--overlap` do and when do you need it?
- How do you get rank, world size and master address inside a Slurm job?
- How do you make a job survive its time limit?
- What does `afterok` do if the first job is requeued after failing?
- Why throttle arrays? What limits array size?
- A user's job log is empty. What are three causes?
- How would you design a `job_submit` plugin policy for a GPU cluster?
- How do you attach to a running job to look at GPUs?

## 14. Checkpoint questions (30)

1. What is an allocation? A step?
2. Where does the batch script run?
3. What do `salloc` and `srun --pty` provide?
4. What does `srun` do outside an allocation?
5. Which `#SBATCH` rules does the shell enforce (placement, shebang)?
6. List five filename pattern symbols.
7. Why create the log directory beforehand?
8. What does `--open-mode` default to and why does it matter for requeue?
9. What does `--export=NONE` change?
10. How do you expand `SLURM_JOB_NODELIST`?
11. Which variables are set only by `srun`?
12. How do you derive MASTER_ADDR?
13. What are steps' resource-sharing defaults and what overrides them?
14. What does `-K` do?
15. What does `--mpi=pmix` do?
16. How do you write an interactive session in one command?
17. What replaced `SallocDefaultCommand`?
18. Write array syntax with step and throttle.
19. What variables identify an array task?
20. List dependency types and the default.
21. `,` versus `?` in dependency lists?
22. What happens to a job whose dependency can never be met?
23. What does `--signal=B:USR1@300` do?
24. Why use `afterany` for training segments?
25. What does `--requeue` change and what is `SLURM_RESTART_COUNT`?
26. How do you see estimated start time?
27. How do you look at finished-job statistics?
28. How do you extend or hold a job?
29. Why lint batch scripts and where can linting run?
30. Name five common submission mistakes.

## 15. Sources and review notes

- User-level behaviour and the allocation/step/job life cycle: *Supercomputers for Linux SysAdmins* chapter 15 (user experience, job life cycle, `scontrol`, accounting and statistics) and *Distributed AI Systems* chapter 8 (batch submission, environment variables, DDP/FSDP launch, arrays, interactive jobs, dependencies, checkpointing and resumption, failure handling), restated in my words; multi-node launch details continue in 6.12.
- Options and semantics: man pages `sbatch(1)`, `srun(1)`, `salloc(1)` (via the shared option text), `scontrol(1)`, `slurm.conf(5)` from SchedMD/slurm commit `521370b`.
- Original: `code/part06/sbatch_lint.py` (tested on two scripts above) and the patterns.
- Unverified: exact behaviour of `--export=NONE` with `sbatch` on your site, whether `--exact` is the default for your release, the signal-forwarding plumbing in the requeue example, and all cluster behaviour.
