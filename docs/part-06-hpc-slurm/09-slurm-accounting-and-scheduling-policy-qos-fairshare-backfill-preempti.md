---
id: "c06-09"
title: "6.9 Slurm accounting and scheduling policy: QOS, fair-share, backfill, preemption"
sidebar_label: "6.9 Slurm accounting and scheduling policy: QOS, fair-share, backfill, preemption"
sidebar_position: 9
description: "How Slurm decides who runs next and how much anyone may use: accounting associations and TRES, limits and QOS, the multifactor priority formula, Fair Tree fair-share with a worked simulator, usage decay, backfill and why time limits matter, preemption modes, and policy designs for AI clusters"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.9 Slurm accounting and scheduling policy: QOS, fair-share, backfill, preemption

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Slurm cluster with accounting (6.7); the simulator needs only Python 3 |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Formulas, flags and defaults were read from the Slurm documentation and man pages in a shallow clone (SchedMD/slurm commit `521370b`, 2026-10-23, development version 26.11.0rc1); the Fair Tree and priority model in `code/part06/fairtree_sim.py` was run (output shown) and is a teaching re-implementation, not Slurm itself. No Slurm daemon was run; cluster labs are **untested** |

## Why this matters for AI infrastructure

A GPU cluster is a shared, expensive asset, and the scheduler's policy is where organisational decisions become code: who gets priority before a deadline, how a team that bought 64 GPUs is guaranteed them, whether idle capacity can be borrowed, how one user is stopped from queueing 10,000 jobs, and how much each group is charged. Poor policy produces the two classic failures: starvation (large or low-priority jobs never run) and low utilisation (GPUs idle while jobs wait because limits or reservations are mis-set). This chapter explains the mechanisms well enough to design policy and explain to a user why their job is pending.

## Prerequisites and outcomes

Needs 6.7 (accounting database, associations) and 6.8 (partitions, memory/GPU defaults). After this chapter you can:

- Build and inspect an accounting hierarchy with `sacctmgr`, and explain associations, TRES and billing.
- Set and reason about limits (Grp\*, Max\*), `AccountingStorageEnforce`, and QOS flags.
- Compute a job's priority from the multifactor formula and use `sprio` and `sshare` to explain an ordering.
- Explain Fair Tree fair-share, usage decay and what the numbers mean; predict who goes next in a small example.
- Explain backfill, why accurate time limits matter, and the main tuning knobs.
- Choose a preemption design (partition tiers or QOS; cancel, requeue, suspend) and its consequences for AI jobs.
- Design a policy for a multi-team GPU cluster including guaranteed shares, burst, and urgent work.

## 1. The accounting model

With `slurmdbd` and a database (6.7), Slurm records every job and keeps a tree of **associations**. An association is a tuple (cluster, account, user, optionally partition) to which limits, shares and a default QOS attach.

```text
root
 └─ physics (account, shares 60)
     ├─ alice (user association)
     └─ bob
 └─ biology (account, shares 40)
     ├─ carol
     └─ dave
```

Creating and inspecting it (syntax per `sacctmgr(1)`; the man page also documents `modify`, `delete`, `show` and the `where`/`set` form):

```bash
sacctmgr add cluster mycluster
sacctmgr add account physics Description="Physics dept" Organization=sci fairshare=60
sacctmgr add account biology fairshare=40
sacctmgr add user alice account=physics
sacctmgr add user bob   account=physics
sacctmgr show assoc format=cluster,account,user,fairshare,qos,grptres%30 tree
sacctmgr modify user where name=alice set maxjobs=20 defaultaccount=physics
```

Every job runs under an association. If `AccountingStorageEnforce` includes `associations`, a user with no association cannot run; `limits` (implies associations) enforces the limits on associations and QOS; `qos` requires a valid QOS; `safe` only launches jobs that can finish within a TRES-minutes limit; `nojobs`/`nosteps` turn accounting off for jobs/steps. (From the `slurm.conf` man page.) The 6.7 starter config uses `associations,limits,qos`.

### TRES

A **TRES** (trackable resource) is anything Slurm counts: `cpu`, `mem`, `node`, `energy`, `billing`, and GRES such as `gres/gpu` (add `AccountingStorageTRES=gres/gpu` so GPUs are tracked; per-type like `gres/gpu:h100` also possible). Limits and usage are expressed in TRES. **`billing`** is a synthetic TRES computed from per-partition `TRESBillingWeights`. The documentation's example with `TRESBillingWeights=CPU=1.0,Mem=0.25G` on 16-CPU/64-GiB nodes shows why: a 1-CPU job that requests 60 GiB occupies the memory of a whole node but, billed for CPU only, looks cheap. With the default sum, Job1 (1 CPU, 60 GiB) is billed 1 + 15 = 16; Job2 (16 CPU, 1 GiB) 16.25; Job3 (16 CPU, 60 GiB) 31. With the `MAX_TRES` flag the bill is the max of the per-node TRES (15, 15, 16), which tracks "how much of the node did you deny to others". For GPU clusters bill GPUs heavily (for example `GRES/gpu=10`) and use `MAX_TRES_GRES` (added in Slurm 25.05 per the man page) so that GPU hours dominate. Billing drives fair-share usage, reports, chargeback and the TRES priority factor.

### User levels and coordinators

Accounting also defines who may change policy. A user's `AdminLevel` (set with `sacctmgr modify user ... set adminlevel=...`) is `None`, `Operator` or `Admin` (values from the `sacctmgr` man page); operators can perform most accounting operations, admins everything. A **coordinator** is a regular user designated for an account (`sacctmgr add coordinator account=physics names=alice`) who can add users to, and set limits within, that account but not exceed what the parent allows. Delegating to coordinators keeps routine account management with the teams; Fair Tree (section 4) is designed so that a coordinator reshuffling their own users cannot hurt their account's standing relative to others.

## 2. Limits and QOS

### Association limits

Set on accounts or users with `sacctmgr modify ... set`. The families (names from `sacctmgr(1)`):

| Family | Meaning |
|---|---|
| `GrpTRES`, `GrpJobs`, `GrpSubmit`, `GrpWall` | Aggregate limit for the association **and all its children** at one time (for example `GrpTRES=gres/gpu=64` caps an account's running GPUs) |
| `GrpTRESMins`, `GrpTRESRunMins` | Cumulative TRES-minutes (usage budget) / TRES-minutes currently committed by running jobs |
| `MaxTRES`/`MaxTRESPerJob`, `MaxTRESPerNode`, `MaxTRESPerUser`, `MaxTRESPerAccount` | Per job / node / user / account caps |
| `MaxJobs`, `MaxSubmitJobs`, `MaxWall`, `MaxTRESMins` | Counts and wall-time per job |
| `MaxJobsAccrue*` | Limit how many pending jobs accrue age priority |
| `Fairshare` | Share value used in fair-share |
| `DefaultQOS`, `QOS` | Allowed and default QOS |

Limits are checked when a job is being considered to run. A job above a limit stays pending with a reason such as `AssocGrpGRES`, `AssocMaxJobsLimit`, `QOSMaxCpuPerUserLimit` (shown by `squeue -o "%R"`), unless the QOS has `DenyOnLimit`, in which case it is rejected at submission.

### QOS (Quality of Service)

A **QOS** is a named policy object that jobs request (`--qos=high`). It bundles: a **priority** (integer feeding the QOS factor), **limits** (the same Grp/Max families but at QOS scope), **preemption** relationships and mode, a **usage factor** (scale billing: 0.5 for a cheap scavenger QOS, 2 for an expensive urgent one), a **grace time** for preemption, and **flags**:

| Flag | Effect |
|---|---|
| `DenyOnLimit` | Reject at submit rather than queue when limits are violated |
| `NoReserve` | With backfill, jobs in this QOS do not reserve resources in the future (man page warns this can starve larger jobs) |
| `OverPartQOS` | The job's QOS limits override the partition QOS |
| `NoDecay` | QOS usage (`GrpTRESMins`, `GrpWall`, raw usage) is not decayed |
| `EnforceUsageThreshold` | Jobs rejected if the QOS usage is below a threshold |
| `RelativeTRES`-style options | Interpret limits relative to the partition (see the page) |

Example policy set (sketch):

```bash
sacctmgr add qos normal   priority=10   maxtresperuser=gres/gpu=64
sacctmgr add qos urgent   priority=1000 usagefactor=2   maxwall=12:00:00 preempt=scavenger flags=DenyOnLimit
sacctmgr add qos scavenger priority=0   usagefactor=0   preemptmode=requeue gracetime=120
sacctmgr modify user alice set qos=normal,urgent defaultqos=normal
```

(Option spellings are from the `sacctmgr(1)` QOS section as I read it; verify with `sacctmgr show qos format=...` and the man page on your version.)

Partition-level QOS (`QOS=` on a partition) extends limits for jobs in that partition; where a limit exists in both the partition QOS and the job QOS, the partition QOS wins unless the job QOS has `OverPartQOS` (man page).

### The 6-level QoS and association limit precedence order

Because a single job can inherit limits from a partition, a job QoS, a user association, parent accounts, and the cluster root, Slurm evaluates conflicting limit definitions in a strict **6-level precedence order** (as given in Chapter 15 of *Supercomputers for Linux SysAdmins*):

1. **Partition QOS limit** (if `Flags=OverPartQOS` is set on the Job QoS, this moves after Job QoS)
2. **Job QOS limit**
3. **User association**
4. **Account association(s)**, ascending the hierarchy
5. **Root/cluster association**
6. **Partition limit**

Also note that when Slurm compares whether one job has higher overall scheduling priority (or preemption authority) than another, it checks four levels in order: (1) **Reservation** (jobs with a reservation come first), (2) **Partition priority tier** (`PriorityTier`), (3) **Job priority** (the calculated multifactor integer), and (4) **Job ID** (earlier submissions with a lower job ID win ties).

## 3. Priority: the multifactor formula

With `PriorityType=priority/multifactor` each pending job gets an integer priority (0 to 4,294,967,295; higher runs sooner). From the multifactor documentation:

```text
Job_priority = site_factor
             + PriorityWeightAge       * age_factor
             + PriorityWeightAssoc     * assoc_factor
             + PriorityWeightFairshare * fair-share_factor
             + PriorityWeightJobSize   * job_size_factor
             + PriorityWeightPartition * priority_job_factor
             + PriorityWeightQOS       * QOS_factor
             + SUM(TRES_weight_<type> * TRES_factor_<type>)
             - nice_factor
```

All factors range 0.0 to 1.0 and weights are unsigned 32-bit integers. By default values are **normalised** to the highest in the cluster (a partition factor of 10 against a maximum of 20 with weight 5000 gives 2,500; the `NO_NORMAL_*` flags turn normalisation off per factor). Weights should be large enough to preserve significant digits: with a fair-share weight of 10, factors 0.59534 and 0.50002 both become about 5 and tie, so use weights from about 1000 upward for the factors that should dominate.

| Factor | Meaning |
|---|---|
| **Age** | Time pending while eligible, rising to 1.0 at `PriorityMaxAge` (default 7 days). Dependent or held jobs do not accrue unless `PriorityFlags=ACCRUE_ALWAYS` |
| **Association** | Per-association integer priority, normalised |
| **Fair-share** | Under-service of the user and account (section 4) |
| **Job size** | Larger or smaller job favoured (`PriorityFavorSmall`); `SMALL_RELATIVE_TO_TIME` divides by time limit |
| **Partition** | `PriorityJobFactor` of the partition, normalised |
| **QOS** | QOS priority, normalised |
| **TRES** | Weighted amount of each TRES requested (set `PriorityWeightTRES=gres/gpu=...`) |
| **Site** | Set by `scontrol`, a `job_submit` plugin or a site-factor plugin |
| **Nice** | User-supplied reduction (negative values need privilege) |

Other relevant parameters: `PriorityCalcPeriod`, `PriorityDecayHalfLife` (default 7 days), `PriorityUsageResetPeriod`, `PriorityFlags` (`CALCULATE_RUNNING`, `INCR_ONLY`, `NO_FAIR_TREE`, `DEPTH_OBLIVIOUS`, `MAX_TRES`, ...).

Inspect:

```bash
sprio -l                     # factors of each pending job
sprio -w                     # the configured weights
sshare -al                   # shares, raw usage, effective usage, level FS, fairshare
squeue --start               # expected start times (after backfill planning)
scontrol show job JOBID | grep -i -E "priority|reason|starttime"
```

**Reading `sprio` is the answer to "why is job A ahead of job B".** Compare the columns.

## 4. Priorities and fair-share

Fair-share steers queue order toward under-served groups. It is **not** a hard quota: over-served groups can still run when the machine would otherwise idle (documentation). The inputs: each association's **shares** (assigned fraction) and its **usage** (decayed history of billed TRES). Usage decays exponentially with half-life `PriorityDecayHalfLife` (default 7 days, "half of the original value cleared at age" of the half-life; 0 disables decay and requires `PriorityUsageResetPeriod`).

### Fair Tree (default since 19.05)

Per the documentation, for each association compute **Level Fairshare**

```text
LF = S / U
S = shares / (sum of shares of itself and its siblings)
U = usage  / (sum of usage  of itself and its siblings)
```

LF above 1 means under-served, below 1 over-served. Then sort siblings by LF (descending) at every level, walk the tree depth-first, and rank the **users** in the order met; the final FairShare factor is `rank / number_of_user_associations`, so the best user gets 1.0. Consequence (documented): if account A has a higher LF than sibling account B, **every user under A outranks every user under B**, regardless of individual usage. This prevents a heavy user in a light account from beating a light user in a heavy account, and prevents account coordinators gaming their team's order. (The older **Classic** algorithm computes `F = 2^(-U/S)` per association from effective usage; select it with `PriorityFlags=NO_FAIR_TREE`.)

### The simulator

`code/part06/fairtree_sim.py` implements Level FS, the tree walk, decay and the priority sum. Run on the tree above (physics shares 60, usage alice 5000, bob 500; biology shares 40, usage carol 100, dave 100):

```text
Level fairshare among accounts:
  physics  S=0.60 U=0.965 LF=0.622
  biology  S=0.40 U=0.035 LF=11.400
FairShare (Fair Tree):
  carol  1.00
  dave   0.75
  bob    0.50
  alice  0.25
```

Note bob (usage 500) ranks below dave (usage 100) because **biology as an account outranks physics**; within physics, bob (less usage) ranks above alice. Decay with a 7-day half-life of 8,000 core-hours: 8,000 now, 4,000 at 7 days, 2,000 at 14, 500 at 28. And two jobs under the example weights (age 1000, fair-share 100000, QOS 10000, partition 1000): alice's one-hour-old job with the highest QOS scores 36,005, while carol's three-day-old normal-QOS job scores 102,428 because the fair-share term dominates. The lesson: **with a large fair-share weight a QOS bump does not rescue a heavy user**; if urgent work must jump the queue, give QOS priority a weight comparable to fair-share, or use preemption (section 6).

### Practical fair-share guidance

- Shares express entitlement (what you bought), usage expresses consumption; pick a decay half-life that matches the planning horizon (days for interactive research, weeks for allocations). Very long half-lives let a past burst punish a group for months.
- `sshare` shows `NormShares`, `RawUsage`, `EffectvUsage`, `LevelFS`, `FairShare`.
- New users with no usage get high LF (infinity if no usage), which is intentionally welcoming but can be exploited by creating accounts; control account creation.
- Fair-share needs `slurmdbd` and honest accounting of GPUs (billing weights).
- Hard budgets use `GrpTRESMins` with `AccountingStorageEnforce=limits` (and `safe` if you want jobs to finish within the budget).

## 5. Backfill

The main scheduling pass walks the pending queue in priority order and starts what fits. **Backfill** (`SchedulerType=sched/backfill`) adds look-ahead: it plans a start time for high-priority jobs that cannot start now, then lets lower-priority jobs start immediately **only if they will finish before they delay any planned job** (or fit in resources not needed by the plan). This raises utilisation without starving big jobs.

Backfill relies on **time limits**. A job's `--time` is its promised maximum; the scheduler plans with it. Consequences:

- **Accurate (tight) limits let more jobs backfill.** A user who requests the 2-day maximum for a 2-hour job blocks backfill windows for others and delays their own job's planning.
- Jobs finishing early create gaps that the next scheduling pass refills.
- Without limits, or with a default equal to the partition maximum, backfill is crippled. Set `DefaultTime` low and `MaxTime` where needed (6.8), and consider `--time-min` for flexible jobs.
- Backfill cannot help when all jobs are huge multi-node and uniform; it shines on mixed sizes.

Selected `SchedulerParameters` (defaults from the man page):

| Parameter | Default | Meaning |
|---|---|---|
| `bf_interval` | 30 s | Seconds between backfill iterations (-1 disables) |
| `bf_window` | 1440 min (1 day) | How far ahead to plan; should be at least the longest time limit to avoid starvation |
| `bf_resolution` | 60 s | Time granularity of planning; raise it with a large `bf_window` |
| `bf_max_job_test` | 500 | Maximum jobs considered per cycle (queue depth) |
| `bf_max_job_user` | 0 (none) | Per-user cap on backfill candidates; prevents one user's flood from hiding others |
| `bf_continue` | off | Continue the cycle after releasing locks even if state changed |
| `default_queue_depth` | 100 | Jobs tried in the main scheduling pass |
| `defer`, `sched_interval`, `sched_min_interval`, `partition_job_depth`, `max_rpc_cnt` | | Limit scheduler overhead under heavy load (see page) |

Typical GPU-cluster tuning: raise `bf_window` to cover the longest time limit (for example 7 days), raise `bf_resolution` accordingly (for example 300 s), keep `bf_max_job_test` in the low thousands for large queues, set `bf_max_job_user` to something like 50 to 200, enable `bf_continue`. Monitor with `sdiag` (cycle times, depth reached, queue lengths). **Too deep and too frequent backfill makes the controller unresponsive**; look at `sdiag` before raising numbers. Values quoted as typical are experience-based, not measured here.

Diagnostics: `squeue --start`, `scontrol show job` (`StartTime`, `Reason`), `sprio`. A job pending with reason `Priority` is waiting behind others; `Resources` is next in line but resources are not yet free; `Dependency`, `JobHeldUser`, `BeginTime` are not scheduling problems; limit reasons begin with `Assoc`/`QOS`.

## 6. Preemption

Preemption stops lower-priority jobs to let a higher-priority one run (documentation). Configuration:

- **`PreemptType`**: `preempt/none` (default), `preempt/partition_prio` (decided by partition `PriorityTier`), `preempt/qos` (decided by the QOS `Preempt` list).
- **`PreemptMode`** (cluster default; per partition with partition_prio or per QOS with qos): `OFF` (default), `CANCEL`, `REQUEUE`, `SUSPEND` (requires `GANG`), and the modifier `GANG` (gang scheduling/time-slicing, per partition). `PRIORITY` limits preemption to cases where the preemptor's job priority is higher; `WITHIN` lets jobs of the same QOS preempt each other.
- **`GraceTime`** (partition or QOS): seconds the preempted job has to finish after being selected; it gets SIGCONT and SIGTERM immediately and SIGKILL at the end. Default 0 (no delay). A job that exits within the grace time is handled according to the preempt mode regardless of why it exited.
- Memory: suspended jobs keep their memory, so with `SUSPEND,GANG` make memory a consumable resource (6.8) or nodes will swap.
- `REQUEUE` works only for jobs submitted with `--requeue` or when cluster-wide `JobRequeue=1`; otherwise the job is cancelled.

### What preemption means for AI work

- **Suspend** is unsuitable for GPU training: suspended jobs hold GPU memory, and NCCL jobs across nodes time out. Use `REQUEUE` or `CANCEL`.
- **Requeue** only helps if the job **checkpoints and resumes** (Part 14); otherwise the work is lost. Train with periodic checkpoints and an automatic resume path (`--requeue`, `--signal=B:USR1@120` to get a warning, handle SIGTERM during `GraceTime`).
- A scavenger QOS (usage factor 0, lowest priority, requeue) turns idle GPUs into free throughput for groups with resumable work, while guaranteeing owners instant access.
- Preemption interacts with fair-share: preempted GPU time is charged, so use a low `UsageFactor` for scavenger usage.

## 7. A policy design for a multi-team GPU cluster

Requirements: three teams with purchased shares (50/30/20), research bursts allowed, a monthly deadline crunch, protection against floods, easy auditability.

1. **Accounts** per team with `fairshare` proportional to purchase; Fair Tree (default); decay half-life 14 days.
2. **Partitions**: `gpu` (all nodes, default, `MaxTime=2-00:00:00`, `DefMemPerGPU`, `DefCpuPerGPU`), `debug` (few nodes, 30 minutes, high tier), `long` (restricted to approved accounts, `MaxTime=14-00:00:00`, lower weight).
3. **QOS**: `normal` (priority 100, `MaxTRESPerUser=gres/gpu=64`, `MaxSubmitJobsPerUser=500`), `urgent` (priority 1000, usage factor 2, approval by `AllowQos`, preempts `scavenger`), `scavenger` (priority 0, usage factor 0 or 0.1, requeue, grace 120 s, `NoReserve` so it never blocks planning).
4. **Hard budgets** only where contractually required (`GrpTRESMins` plus `safe`); otherwise rely on fair-share.
5. **Weights**: `PriorityWeightFairshare=100000`, `PriorityWeightQOS=50000`, `PriorityWeightAge=1000` (`PriorityMaxAge=7-0`), `PriorityWeightPartition=10000`, `PriorityWeightJobSize=0` (do not distort), `PriorityWeightTRES=gres/gpu=100`. Check with `sprio` that an urgent QOS job of a heavy user outranks a normal job of a light user if that is the intent.
6. **Scheduler**: `sched/backfill`, `bf_window` at the longest limit, `bf_max_job_user=100`, `bf_continue`.
7. **Billing**: `TRESBillingWeights=GRES/gpu=10,CPU=1,Mem=0.1G` and `PriorityFlags=MAX_TRES_GRES` so GPUs dominate cost.
8. **Reporting**: `sreport cluster AccountUtilizationByUser`, `sreport cluster utilization`, `sacct -X --format=...` for monthly chargeback; review wait time per QOS.
9. **Review loop**: monthly policy review comparing waiting times and utilisation; avoid tuning weights ad hoc during a crunch.

### Concrete `sacct` and `sreport` reporting commands (from the book)

Once accounting is active, `sacct` queries per-job records (and `sstat` queries live running-job CPU, memory, and disk utilization when `jobacct_gather` is enabled), while `sreport` aggregates utilization across three top-level report classes: `cluster` (total utilization), `job` (task size classes by CPU count, grouped by account), and `user` (top users by resource consumption). The book's Chapter 15 provides four ready-to-use reporting invocations (`(untested here)`):

```bash
# (untested here) — 1. One-day job summary: JobID, Partition, User, core-seconds (CPUTimeRAW), State
sacct -S 2024-01-01 -E 2024-01-02 \
  -o JobID,Partition,User%16,CPUTimeRAW,State%20 -X

# (untested here) — 2. Weekly job size breakdown by account (0–16 cores, 17–1024 cores, and >1024 cores, in minutes)
sreport job SizesByAccount grouping=0-16,17-1024 \
  start=2024-01-01 end=2024-01-07

# (untested here) — 3. Monthly cluster utilization percentages (Allocated, Down, PLND Down, Idle, Planned, Reported)
sreport cluster utilization Start=2024-11-01 End=2024-12-01 -t percent

# (untested here) — 4. Top 5 users by resource utilization over a month (reported in TRES Minutes and Energy)
sreport user topusage topcount=5 start=2024-01-10 \
  end=2024-02-10
```

Alternatives: reservations (`scontrol create reservation`) for guaranteed windows (training runs, exams, demos); hard partitions per team (simple, wasteful); dedicated nodes via `AllowAccounts`; a Kubernetes layer with Kueue where quota/borrowing semantics are expressed as ClusterQueue and cohort (Part 11, 14).

## 8. Why is my job pending: a decision list

1. `squeue -j JOB -o "%i %T %r %S"` for reason and estimated start.
2. Reason starts with `Assoc` or `QOS`: a limit; `sacctmgr show assoc where user=...` and `sacctmgr show qos`.
3. `Priority`: compare `sprio -j JOB` with the jobs ahead; `sshare -u USER`.
4. `Resources`: wait for free nodes; check the request (GPU type? memory default? constraint?) for something no node can satisfy; `scontrol show job` `Features`, `Gres`, `MinMemoryNode`.
5. `ReqNodeNotAvail`: nodes down/drained/reserved (`sinfo -R`, `scontrol show reservation`).
6. `PartitionConfig`, `PartitionTimeLimit`, `PartitionNodeLimit`: request exceeds partition limits.
7. `BeginTime`, `Dependency`, `JobHeldUser/Admin`: not a scheduling issue.
8. `BadConstraints`/`InvalidQOS`/`InvalidAccount`: fix the request.

## 9. Lab (simulator tested; cluster parts untested)

1. Run `fairtree_sim.py`; change usage so that physics has less usage than biology; predict, then verify the ranking.
2. Add a third account with no usage and observe LF (infinity) and its users' rank. Discuss the incentive problem.
3. Change the decay half-life; compute how long until a one-off burst stops mattering.
4. Modify the priority weights and find the QOS weight at which an urgent job of a heavy user beats a normal job of a light user.
5. Cluster: create the accounts, users, QOS from section 7; set weights; submit jobs under different users with `--test-only`/`--hold` and examine `sprio -l`.
6. Cluster: run a backfill experiment: queue a large job requiring all nodes behind running small jobs; then submit short jobs with accurate `--time` and long jobs with a loose `--time`; observe which backfill (`squeue --start`).
7. Cluster: configure `scavenger` with requeue; run a checkpointing toy job, preempt it with an `urgent` job, confirm requeue and resume.
8. Read `sdiag` output before and after changing `bf_window`/`bf_max_job_test`.

## 10. Interview angles

- Explain associations, accounts, QOS, and TRES. What is `billing`?
- How is a job's priority computed? How would you explain the order of two jobs?
- What does Fair Tree guarantee about users in sibling accounts?
- What does usage decay do? How do you choose the half-life?
- Why do accurate time limits matter for backfill?
- Describe a preemption setup for GPU training with checkpoints. Why not suspend?
- How would you give a team a guaranteed share but let others borrow idle GPUs?
- A user says their job is stuck "Priority". What do you do?
- What breaks if `PriorityWeightFairshare` is 10?
- Difference between Grp and Max limits.

## 11. Checkpoint questions (30)

1. What is an association?
2. What does `AccountingStorageEnforce=limits` require and imply?
3. What is a TRES? Give four.
4. Why use billing weights?
5. Compare the default sum and `MAX_TRES` billing on the documentation's example.
6. Difference between `GrpTRES` and `MaxTRESPerUser`.
7. What does `GrpTRESMins` limit?
8. What does a QOS contain, what is Slurm's 6-level precedence order for enforcing limits, and which three `sreport` commands report job size groupings by account, cluster utilization percentage, and top users? **A:** A QOS bundles a priority factor, Grp\*/Max\* limits, preemption settings and grace time, a usage factor, and flags (such as `DenyOnLimit`, `NoReserve`, `OverPartQOS`). When limits conflict, Slurm enforces them in this 6-level order: (1) Partition QOS limit (moves after Job QOS if `OverPartQOS` is set), (2) Job QOS limit, (3) User association, (4) Account association(s) ascending the hierarchy, (5) Root/cluster association, and (6) Partition limit. The three `sreport` commands are `sreport job SizesByAccount grouping=0-16,17-1024 start=... end=...`, `sreport cluster utilization Start=... End=... -t percent`, and `sreport user topusage topcount=5 start=... end=...`.
9. What do `DenyOnLimit` and `NoReserve` do?
10. What is `UsageFactor` for?
11. Write the multifactor priority formula.
12. What range do factors and weights have?
13. What does normalisation do, and how do you disable it for the partition factor?
14. Why should weights be at least ~1000 for dominant factors?
15. When does the age factor accrue?
16. What does `sprio -l` show?
17. What do shares and usage mean in fair-share?
18. Define Level Fairshare.
19. How is the final Fair Tree factor derived?
20. In the simulator, why does bob rank below dave?
21. What does `PriorityDecayHalfLife` do?
22. How does backfill decide whether a job may start?
23. Why must `bf_window` cover the longest time limit?
24. Name four backfill parameters and defaults.
25. Which tool shows scheduler cycle statistics?
26. Compare `preempt/partition_prio` and `preempt/qos`.
27. List the preempt modes and which need `GANG`.
28. What is `GraceTime` and which signals are sent?
29. Why is suspend a poor choice for NCCL jobs?
30. Describe a scavenger QOS design.

## 12. Sources and review notes

- Accounting concepts, the 6-level QoS/association limit precedence order, `sacct` and `sreport` commands (`sreport job SizesByAccount`, `sreport cluster utilization`, `sreport user topusage`), partitions, GRES, backfill and preemption (read in full: `supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`, "15. Slurm").
- Priority formula, factor descriptions, normalisation, TRES billing examples, Fair Tree and Level FS, decay: Slurm documentation pages `priority_multifactor`, `fair_tree`, `classic_fair_share`, `preempt`, `qos`, and man pages `slurm.conf(5)`, `sacctmgr(1)`, from SchedMD/slurm commit `521370b` (development version).
- Run here: `code/part06/fairtree_sim.py` (output shown above). The simulator ignores ties, per-partition associations, TRES billing details and many edge cases and must not be used to predict a production queue.
- Not verified on live hardware: `sacctmgr`, `sacct`, `sreport`, `sprio`, `sshare`, `squeue` commands, sacctmgr option spellings in the examples (checked against the man page headings only), typical backfill tuning values, and behaviour on releases older than the documentation read.
