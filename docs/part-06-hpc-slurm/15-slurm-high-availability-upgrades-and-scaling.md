---
id: "c06-15"
title: "6.15 Slurm high availability, upgrades and scaling"
sidebar_label: "6.15 Slurm high availability, upgrades and scaling"
sidebar_position: 15
description: "Keeping Slurm running and current: controller and database failover, state storage, backups, the documented upgrade order and compatibility window (with a path planner), reverting, scaling to thousands of nodes and high job rates (sysctls, timers, select plugin, tree fan-out, munge), configless and sackd, REST and authentication, federation and elastic nodes"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.15 Slurm high availability, upgrades and scaling

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Three or more VMs (controller pair, database, nodes) |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Read from the `slurm.conf(5)`/`slurmdbd.conf(5)` man pages and the Upgrade, Large Cluster, High Throughput and Configless guides (SchedMD/slurm commit `521370b`, 2026-10-23, development 26.11.0rc1). `code/part06/slurm_upgrade_path.py` was run on four cases (output below) and checked against the guide's compatibility table for 23.11 to 25.05. No failover or upgrade was performed; labs **untested** |

## Why this matters for AI infrastructure

The scheduler is a single point of failure for a very expensive asset: if `slurmctld` is down, nothing new starts and queued work sits idle behind a multi-million-dollar fleet. Upgrades are mandatory (security fixes, GPU features such as new GRES autodetect values or `MAX_TRES_GRES` billing), but carry real risk because Slurm state and the accounting database are migrated in place and cannot be rolled back. And clusters grow: tens of thousands of GPUs, millions of short jobs for inference and evaluation. This chapter covers redundancy, the safe upgrade procedure, and scaling knobs.

## Prerequisites and outcomes

Needs 6.7 to 6.14. After this chapter you can:

- Configure controller failover and database redundancy; explain what is and is not preserved when the primary dies.
- Back up and restore Slurm state and accounting data.
- Plan and execute upgrades in the documented order within the compatibility window, and know why downgrades are unsafe.
- Apply the large-cluster and high-throughput tuning guidance and verify results with `sdiag`.
- Use configless mode, `sackd`, `slurmrestd`, JWT/authentication choices, federation, and cloud/elastic nodes at a conceptual level.

## 1. What fails and what survives

Components: `slurmctld` (scheduler, state), `slurmdbd` (accounting) + database, `slurmd` (per node), `munge`, shared storage for `StateSaveLocation`, name services.

- **slurmctld down**: running jobs **continue** (the `slurmstepd` processes on nodes keep going); no new jobs start; commands like `squeue` fail; job completion messages queue up on nodes and are delivered when the controller returns. Node health checks continue locally. If the outage exceeds `SlurmdTimeout`, nodes are only marked down after the controller is back and notices unresponsiveness, so a controller restart does not itself kill jobs.
- **slurmdbd down**: scheduling continues; accounting records are buffered by `slurmctld` and written later (the controller holds them in memory/state files; long outages risk loss or memory growth, and with `AccountingStorageEnforce=associations,limits` jobs from users lacking cached associations may be rejected, check your version's behaviour). Fair-share priority calculations stall.
- **Database down**: slurmdbd cannot persist; same as above.
- **Node loss**: jobs on that node fail or are requeued.
- **munge or time skew**: authentication failures everywhere.

## 2. Controller high availability

From `slurm.conf(5)`:

```ini
SlurmctldHost=ctl1
SlurmctldHost=ctl2
SlurmctldHost=ctl3        # optional additional standbys
SlurmctldTimeout=120      # seconds before a backup assumes control (default 120)
StateSaveLocation=/shared/slurm/state   # must be readable and writable by all controller hosts
```

"If specified more than once, the first entry will run as the primary and all other entries as standby backups. If the primary host fails, the first backup will change from standby to primary until the first host comes back online. This same process will repeat if the new primary fails." The standby watches the primary (every `SlurmctldTimeout`/2 roughly) and takes control when it stops responding for `SlurmctldTimeout`. All controllers read the same `StateSaveLocation`, which the man page says holds "all running and pending job information" and recommends placing on a reliable file system (for example RAID); it also receives core files of crashing daemons.

Design implications:

1. **The state directory is the real HA component.** It must be shared (NFS with strong locking semantics, a parallel file system, a clustered/replicated block device) and itself highly available. Latency matters: `slurmctld` writes state frequently; a slow or flaky state file system degrades scheduling (watch `sdiag` and `iostat`).
2. Avoid split-brain: two controllers both believing they are primary can corrupt state. Use the built-in standby mechanism, fence properly (STONITH or lease) if you add external automation, and keep clocks synced.
3. Failover time is about `SlurmctldTimeout` plus state load time (minutes for large queues). Plan for 2 to 5 minutes of no scheduling, and tune the timeout against false failovers during short network glitches.
4. Test failover regularly (stop slurmctld on the primary; confirm the standby takes over; restore). Test restart of both.
5. Clients find the active controller through the same `slurm.conf` (or configless `--conf-server` list); keep it identical on all controllers.

**slurmdbd HA**: `slurmdbd.conf` supports `DbdBackupHost` ("must have access to the same underlying database"). The real redundancy is in the **database**: MariaDB/MySQL replication (Galera cluster, primary/replica with automatic failover) or a managed database service. Keep the database on fast storage, backed up, and sized for the job history; configure `Purge*` options to archive or delete old records.

**munge**: same key on all nodes, synchronised clocks; run with more threads on busy controllers (documentation suggests starting with ten for high throughput).

## 3. Backups

Back up:

| Item | How | Frequency |
|---|---|---|
| `StateSaveLocation` | Snapshot or rsync while the controller is stopped or via file-system snapshots; at least before upgrades | Before every upgrade; periodic snapshots |
| Accounting database | `mysqldump --single-transaction` or physical backup/replica snapshot | Daily plus pre-upgrade |
| `/etc/slurm/*` (slurm.conf, cgroup.conf, gres.conf, topology, slurmdbd.conf, plugstack) | Git | On every change |
| `munge.key` | Secure secret store | Once; rotate by procedure |
| Custom scripts and plugins (prolog, epilog, health, job_submit.lua) | Git | On change |

A backup you have not restored is a hope. Practise restoring the accounting database to a test host and starting a test `slurmdbd` against it.

## 4. Upgrades

### Rules from the Upgrade Guide

- Version numbers `YY.MM.patch`: the first two numbers are the **major** release; patch releases are maintenance. Since 24.05 there are two major releases a year (previously nine-monthly).
- **Compatibility window**: in-place upgrades are supported from the previous two major releases; with the 6-month cycle, since 24.11 from the previous **three**. The guide's table: 23.11 accepts 23.02, 22.05; 24.05 accepts 23.11, 23.02; 24.11 accepts 24.05, 23.11, 23.02; 25.05 accepts 24.11, 24.05, 23.11; 25.11 accepts 25.05, 24.11, 24.05; support lasts about 18 months per release. "Upgrades from incompatible versions will fail immediately upon startup", and upgrading outside the window kills running jobs and loses job accounting. Out-of-window upgrades must go **in steps**, each verified.
- **No downgrade**: "Reverting an upgrade (or downgrading) is not supported once any of the Slurm daemons have been started", because daemons rewrite state files and database schemas. Reverting needs restoring `StateSaveLocation` and the database from before the upgrade and loses everything after the backup. (Patch/minor upgrades are more tolerant of mixed versions and in-place downgrades, but keep backups.)
- **Order**: prepare; create backups; upgrade **slurmdbd**; then **slurmctld**; then **slurmd** (preferably together with slurmctld); then login nodes and client commands; recompile or upgrade customised plugins (SPANK such as pyxis, `job_submit`, `auth`), including **pyxis, which must be built against the Slurm version in use**; test key functions; archive backups.
- Finish by letting jobs that started before the slurmd upgrade end: they run with the old `slurmstepd`, and starting another upgrade or using new features before then "may cause problems".
- Package managers: upgrade all Slurm packages on a host together; avoid low-level `rpm`/`dpkg` that bypass dependency checks; **exclude `slurm*` from EPEL** so an unsupported distribution package does not replace yours.
- Read `RELEASE_NOTES` for every major between your version and the target; note removed options and OpenAPI/`data_parser` changes if you use `slurmrestd` or `--json`.
- Plan downtime: database schema migration in `slurmdbd` can take a long time with a large job table (minutes to hours); notify users.
- Optional "seamless" practice from the guide: install each version in its own directory and switch a symlink, so you can pre-stage and switch back (only for pre-start rollback of the binaries; it does not undo state conversion).
- Pre-release versions (rc, master) are not for production.

### A path planner

`code/part06/slurm_upgrade_path.py CURRENT TARGET` encodes the window rule (two prior majors before 24.11, three from 24.11) and returns the minimal sequence of steps. The windows for 23.11 to 25.05 reproduce the guide's table exactly; windows for releases older than 22.05 follow the stated "previous two major releases" rule and are not from the table, so confirm them against the guide of the target release. Outputs:

```text
22.05 -> 23.11 -> 25.05 -> 26.05   (3 upgrade steps)
25.05 -> 26.11   (1 upgrade step)
20.11 -> 22.05 -> 23.11 -> 24.11   (3 upgrade steps)
24.05 -> 25.05   (1 upgrade step)
```

(The planner always takes the furthest compatible step, which minimises the number of upgrades; you may prefer to stop at an intermediate release for a soak period, and the guide recommends testing every step.)

### Procedure (rolling, with downtime windows)

1. Test the whole upgrade in a staging cluster with a copy of the production database and config. Time the `slurmdbd` migration.
2. Announce; drain or reserve; ensure no `slurmd` auto-restart surprises (`SlurmctldParameters=reconfig_on_restart` can cause earlier upgrades of slurmd/sackd, so consider disabling temporarily).
3. Back up state and database.
4. Stop `slurmdbd`; upgrade; start it (it migrates the schema; keep an eye on the log); wait until finished.
5. Stop `slurmctld`; upgrade; start (it converts state). If using HA, upgrade standbys too.
6. Upgrade `slurmd` nodes in waves (drain-free: `slurmd` can be restarted while jobs run, because `slurmstepd` owns the job), or all at once with the controller; upgrade login nodes and clients.
7. Smoke tests: submit jobs on each partition, GPU job, array, `srun --mpi=pmix`, container job, accounting query (`sacct`), `sreport`, REST if used.
8. Keep rollback materials until jobs from before the upgrade finish and the tests pass; then archive.

## 5. Scaling

### Large clusters (1,024 or more nodes) — Large Cluster Administration Guide

- System limits: `/proc/sys/fs/file-max` (recommended start 388067 or the OS default if greater), `net.ipv4.tcp_max_syn_backlog`, `net.core.somaxconn` (raise to absorb bursts, for example 1024 or higher), txqueuelen, `ip_local_port_range`; systemd `TasksMax` for the daemons (newer systemd imposes thread limits per service); high `ulimit` for `slurmctld` (memory, open files, stack).
- **`SelectType`**: for best scalability, allocate whole nodes with `select/linear` and avoid `select/cons_tres` (the guide's advice for huge CPU clusters). GPU clusters generally need `cons_tres` for per-GPU allocation, so scale by tuning other parameters instead.
- **Accounting gather**: `jobacct_gather` sampling costs cycles on every node ("system noise"); for noise-sensitive large jobs choose `jobacct_gather/none` or a large interval (`JobAcctGatherFrequency=task=300`); `JobCompType` records are much cheaper.
- **Node definitions**: state the expected configuration (`RealMemory`, `CPUs`, `TmpDisk`) rather than letting Slurm discover; use the minimal number of `NodeName` lines.
- **Timers**: `SlurmdTimeout` (communication at half of it) of 120 s or more on very large clusters; `MinJobAge` as small as practical for high job rates; `EioTimeout` larger for big `srun`; `EpilogMsgTime` to spread completion messages when large jobs end.
- **`TreeWidth`**: fan-out of the hierarchical slurmd communication, default 16 (about 4,368 nodes reachable in three hops); the default is fine for most.
- Verify everything with `sdiag` (RPC rates, cycle times) and `slurmctld` CPU use.

### High throughput (many short jobs) — High Throughput Guide

Recommendations (for example inference or evaluation fans with thousands of jobs per minute): the same OS limits (`file-max` at least 32,832, `somaxconn` 4096 or 8192 or more than nodes plus clients, wider ephemeral port range, `tcp_syncookies`), **more munge threads**, a fast `StateSaveLocation` (local NVMe for single controller, replicated for HA), `MinJobAge` small, `SchedulerParameters` such as `max_rpc_cnt`, `defer`, `sched_min_interval`, `default_queue_depth`, `bf_*` tuned (6.9), `MaxJobCount` large, job arrays instead of individual submissions, fewer short `srun` steps (`--multi-prog`, one allocation with many tasks), database on SSD with enough RAM for InnoDB, and discouraging polling. For AI platforms, prefer to run **many small inference tasks as long-lived services** rather than as many Slurm jobs; Slurm is a batch scheduler.

### Other scale and architecture features

- **Configless** (`slurmctld` serves configuration to `slurmd`; clients use `sackd` to fetch config and maintain a local cache and the controller address): eliminates config drift and shared `/etc/slurm`; changes propagate on `scontrol reconfigure`. Use DNS SRV (`_slurmctld._tcp`) or `--conf-server`. Highly recommended for large clusters.
- **`slurmrestd`** (REST API) with **JWT** authentication (`AuthAltTypes=auth/jwt`) for portals, Open OnDemand, workflow engines (6.25); watch `data_parser` versions on upgrade; expose only behind authentication and TLS.
- **Authentication**: `munge` (classic) or the newer `auth/slurm` plugin (Slurm's own, documented in the Authentication page); JWT for REST. Rotate keys with a procedure.
- **Federation** (`sacctmgr add federation`): multiple clusters share a job queue view and can accept jobs submitted to any member; used by large sites to balance across clusters or sites. Compare with MultiKueue in Kubernetes (5.35).
- **Elastic/cloud nodes and power saving** (`CLOUD` state, `ResumeProgram`, `SuspendProgram`, `SuspendTime`, dynamic nodes with `slurmd -Z`): scale GPU capacity in and out in clouds; cost-saving at on-prem sites (`PowerDownOnIdle`). Needs robust provisioning (6.22) and accurate `ResumeTimeout`.
- **Multiple Slurm clusters** per site (separate controllers for separate fabrics/hardware generations) behind a shared `slurmdbd`: simplifies upgrades and failure domains, at the cost of fragmented capacity. Slurm on Kubernetes (Slinky, SUNK/Soperator, 6.16) is another way to run several isolated Slurm clusters.

## 6. Operating HA and upgrades safely

| Practice | Why |
|---|---|
| Quarterly failover drill and restore drill | Procedures rot; surprises happen at 3 a.m. |
| One change at a time, outside peak, with a rollback plan (for config) | Slurm config rollback is easy, upgrade rollback is not |
| Staging cluster mirrors production topology and config | Catches plugin/ABI and config removals |
| Pin and track versions of Slurm, pyxis, enroot, munge, PMIx, NVML/Slurm build options | Plugins link against Slurm |
| Watch `sdiag`, controller CPU, state dir latency, DB lag, munge errors | Early warning before outages |
| Document dependencies (DNS, NTP/chrony, LDAP, NFS) with the same HA level | Slurm HA is only as good as these |
| Keep an out-of-band path to controllers | You need them when the network is the problem |

## 7. Lab (planner tested; rest untested)

1. Run `slurm_upgrade_path.py` for your current and target versions; compare with the release notes.
2. Build a 3-VM test: `ctl1`, `ctl2` sharing an NFS state dir, and `db1`; configure `SlurmctldHost` twice; submit jobs; stop `slurmctld` on `ctl1`; time the takeover; verify running jobs survived and `squeue` works through `ctl2`.
3. Take a database dump and state snapshot; restore to a scratch VM and start a test `slurmdbd`/`slurmctld` against them.
4. Upgrade a test cluster one major version in the documented order; record durations (`slurmdbd` migration, controller start) and issues.
5. Switch the test cluster to configless with `sackd` on a login node.
6. Generate a synthetic burst of 5,000 trivial jobs (array) and watch `sdiag`; tune `somaxconn`, `max_rpc_cnt`, `MinJobAge`, munge threads, and compare.
7. Enable `slurmrestd` with JWT; submit a job via REST; note the `data_parser` version.

## 8. Interview angles

- What happens to running jobs when `slurmctld` dies? When `slurmdbd` dies?
- How does controller failover work? What is the critical shared component?
- In what order do you upgrade Slurm components and why?
- Can you roll back a Slurm upgrade? What do you need beforehand?
- You are on 22.05 and want the latest release. What do you do?
- Name five tuning steps for a 5,000-node cluster with many short jobs.
- How do you avoid configuration drift across thousands of nodes?
- What is a SPANK plugin and why does it complicate upgrades?
- When would you run multiple Slurm clusters instead of one?

## 9. Checkpoint questions (30)

1. Which components can fail and what is the impact of each?
2. Do running jobs survive a controller restart?
3. How do you configure a backup controller?
4. What is `SlurmctldTimeout`?
5. Why must `StateSaveLocation` be shared and reliable?
6. How do you avoid split-brain?
7. What redundancy exists for slurmdbd and the database?
8. What do you back up before an upgrade?
9. How do you verify a backup?
10. What does a Slurm version number mean?
11. State the compatibility window rules.
12. What happens when you upgrade outside the window?
13. Why is downgrade unsupported?
14. Give the component upgrade order.
15. Why wait for old jobs to finish after upgrading slurmd?
16. What is special about pyxis and Slurm upgrades?
17. Why exclude Slurm from EPEL?
18. What is the "seamless upgrade" idea?
19. What can slow the slurmdbd migration?
20. List the OS limits tuned for large clusters.
21. Why avoid `cons_tres` on CPU-only giant clusters and why can't GPU clusters?
22. How does job accounting create system noise?
23. What do `MinJobAge`, `EpilogMsgTime` and `TreeWidth` control?
24. What changes for high job throughput?
25. How many munge threads does the guide suggest?
26. What is configless mode and what does `sackd` do?
27. What is `slurmrestd` and how is it authenticated?
28. What is federation?
29. What are elastic/cloud nodes and which parameters drive them?
30. Why run Slurm clusters per failure domain?

## 10. Sources and review notes

- HA, upgrade, large-cluster, high-throughput, configless and authentication behaviour: `slurm.conf(5)`, `slurmdbd.conf(5)` and the HTML guides (Upgrade Guide, Large Cluster Administration, High Throughput, Configless, Authentication, Federation, Power Save, Dynamic Nodes) in SchedMD/slurm commit `521370b`. Operational context: *Supercomputers for Linux SysAdmins* chapter 15 (installation, troubleshooting, advanced slurm.conf parameters).
- Original: `slurm_upgrade_path.py` and its outputs, the failure-impact table, drills.
- Unverified: exact behaviour of accounting buffering and association enforcement while slurmdbd is down on your version, windows for releases older than the guide's table, tuning values beyond those the guides state.
