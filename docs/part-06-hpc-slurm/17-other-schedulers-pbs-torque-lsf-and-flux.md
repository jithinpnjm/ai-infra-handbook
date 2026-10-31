---
id: "c06-17"
title: "6.17 Other schedulers: PBS, Torque, LSF and Flux"
sidebar_label: "6.17 Other schedulers: PBS, Torque, LSF and Flux"
sidebar_position: 17
description: "The other batch schedulers you will meet: OpenPBS/PBS Professional and the legacy Torque, IBM Spectrum LSF, and Flux (El Capitan's workload manager): architecture, request syntax, a command map against Slurm, a tested PBS-to-Slurm directive converter, and guidance for migrations and mixed environments"
status: "reviewed"
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
| Status | Drafted. PBS facts from the OpenPBS man pages (openpbs/openpbs commit `cd7ab5e`, 2026-04-10), Flux facts from the flux-core documentation (commit `40ecc8d`, 2026-10-23). LSF and Torque are described from general knowledge and the Torque chapter of *Supercomputers for Linux SysAdmins*: **unverified**. `code/part06/pbs2slurm.py` was run on one test script. No scheduler other than the converter was executed; labs **untested** |

## Why this matters for AI infrastructure

Slurm runs most GPU training clusters, but you will not always work on one. A university or national lab may run PBS Professional or OpenPBS. A financial or EDA shop may run IBM Spectrum LSF, and LLNL-lineage systems run Flux. Some legacy clusters still run Torque. Customers often send you scripts written for another syntax. The concepts these schedulers share are the same, so learning them once makes it possible to translate between them. That skill matters when a site moves to Slurm or to a Kubernetes-based stack, which is a common migration project, and it comes up in interviews.

## Prerequisites and outcomes

Before you start, work through chapters 6.7 to 6.11. By the end of this chapter, you should be able to:

- Describe the architecture of PBS, Torque, LSF and Flux. Include the server, scheduler, MOM and comm parts of PBS, and explain how each system differs from Slurm.
- Translate job scripts and commands between PBS, Slurm, LSF and Flux. Cover common requests such as nodes, GPUs, time, arrays and dependencies.
- Explain PBS's `select` and `place` model and Flux's nested-instance model. These are the two ideas furthest from Slurm's.
- Plan a migration. Cover inventory, translation, policy mapping, accounting continuity, user retraining and a parallel run.

## 1. What all batch schedulers share

When a job sits in a queue, the first question is which scheduler is holding it. Learn the shared parts once, and you can place any new scheduler quickly. Every batch scheduler has the same basic parts. Jobs wait in a queue, or a partition in Slurm terms. A server or controller holds the state. Each compute node runs a per-node daemon: MOM in PBS, `sbatchd` in LSF, a broker in Flux and `slurmd` in Slurm. A policy engine decides the order, using priority, fair-share, backfill, limits and preemption.

```mermaid
flowchart TB
  subgraph PBS["OpenPBS / Torque"]
    P1["pbs_server + pbs_sched (or Maui maui.cfg)"] --> P2["pbs_mom (+ trqauthd) on compute nodes"]
  end
  subgraph LSF["IBM Spectrum LSF"]
    L1["mbatchd + mbschd + master LIM"] --> L2["sbatchd + res + host LIM"]
  end
  subgraph Flux["LLNL Flux (Hierarchical)"]
    F1["System flux-broker tree + Fluxion"] --> F2["Job Subinstance flux-broker (flux batch)"]
  end
```

Jobs carry a script with directives in comments. The schedulers also support arrays, dependencies, interactive jobs and accounting. The differences lie in vocabulary, the resource-request model, defaults and extensibility. *Supercomputers for Linux SysAdmins* devotes a chapter to OpenPBS and Torque because its target readers meet them. The same skills transfer.

## 2. PBS: OpenPBS and PBS Professional

Suppose a job you submitted to a PBS cluster sits in the queue and never starts. To find the cause, you need to know which daemon does what.

OpenPBS is the open-source release of PBS Professional, which Altair has since open-sourced. The system has several daemons. `pbs_server` keeps the job and queue database and accepts jobs. `pbs_sched` is the scheduler. It decides what runs where, using a policy set in `sched_config` and the resource definitions. `pbs_mom`, the "Machine Oriented Mini-server", runs on each node. `pbs_comm` relays communication for large clusters. A data service, Postgres, sits underneath. The descriptions come from the `pbs(8B)` family of man pages.

You administer the system with `qmgr`, `pbsnodes`, `qstat`, `qenable`, `qdisable`, `qstart`, `qstop` and `tracejob`. You can also write hooks in Python, using `pbs_python`, to control admission and execution.

### Request model: select and place

PBS asks for resources as chunks. The `qsub(1B)` man page gives the syntax:

```text
-l select=[<N>:]<chunk>[+[<N>:]<chunk> ...]        chunk = <resource>=<value>[:<resource>=<value>...]
-l place=[<arrangement>][:<sharing>][:<grouping>]  arrangement: free | pack | scatter | vscatter
                                                   sharing: excl | shared | exclhost
                                                   grouping: group=<resource>
```

Take the example `#PBS -l select=2:ncpus=64:mpiprocs=8:ngpus=8:mem=500gb`. It asks for two identical chunks, and each chunk needs at least 64 CPUs, 8 MPI processes, 8 GPUs and 500 GB. The line `#PBS -l place=scatter:excl` then puts those two chunks on different hosts, used exclusively.

The `+` sign joins different chunks. That makes it a natural fit for heterogeneous jobs, such as one big-memory chunk plus several GPU chunks. Slurm needs its own special "heterogeneous job" syntax for that case. Do not mix the old-style `-l nodes=...:ppn=` form with `select`. The man page warns that this is an error.

Chunks map to vnodes. A vnode is a virtual node, and one host can be split into several of them, for example one per NUMA domain or one per GPU. That is why "node" means something looser in PBS than in Slurm.

The other directives you will use most are `-N` for the job name, `-q` for the queue and `-J X-Y[:Z][%max]` for arrays. In an array, `%max` caps the number of running sub-jobs. The man page also says that job arrays are always rerunnable. Dependencies use `-W depend=afterok:ID[:ID]`. The types are `after`, `afterok`, `afternotok`, `afterany`, `before...` and `on:N`. The remaining options are `-o/-e/-j` for output, `-v` and `-V` for environment, `-l walltime=HH:MM:SS` for time, `-m/-M` for mail, `-r` for rerunnable jobs, `-I` for interactive jobs and `-A` for the account.

Jobs read their context from environment variables. `PBS_NODEFILE` is a file that lists the allocated hosts, with one line per slot. The others are `PBS_JOBID`, `PBS_O_WORKDIR`, `PBS_ARRAY_INDEX` and `PBS_ARRAYID`.

### Torque

Torque came out of the old Maui/Torque stack. Its origins are Cluster Resources and Adaptive Computing. Torque has the same lineage as PBS, and it forked OpenPBS 2.3.12. It uses `qsub -l nodes=2:ppn=16`, `pbs_server` and `pbs_mom`. For policy, it uses the Maui or Moab scheduler, because Torque's built-in scheduler is basic.

*Supercomputers for Linux SysAdmins* walks through installing Torque, configuring the MOM on compute nodes, customising the scheduler and job-control commands. Torque is legacy. New clusters choose Slurm or PBS Pro/OpenPBS, and the open-source Torque line is no longer a good greenfield choice. That last point comes from general knowledge, so verify the project's current status before you rely on it.

### Strengths and weaknesses

PBS is strong where you need flexible resource chunks, placement and hooks. It has been mature in some industries and has a good Windows/Linux history. It is weaker for GPU AI practice. Its ecosystem of AI tooling is smaller, covering pyxis, NGC reference recipes and Kubernetes bridges. It has fewer GPU-specific features out of the box than Slurm's GRES and `--gpus*` options. AI-lab hiring pools also have less community knowledge of it.

### Setting up Torque and customising its scheduler

Names cause confusion here. The original OpenPBS came from MRJ in 1998, and it has been unsupported since about 2004. Torque is Adaptive Computing's fork of it. PBS Professional is Altair's commercial product, which Altair later released as the new OpenPBS in 2020. These are three different code lines, so "OpenPBS" in a document may mean either the old or the new one.

The steps below follow the concrete Torque setup in chapter 14 of *Supercomputers for Linux SysAdmins* (`(untested here)`):

1. Check the daemons and their fixed TCP ports in `/etc/services`. Torque has client and admin CLI tools, `pbs_server` as the central server, `pbs_mom` as the compute-node agent, and `pbs_sched` or an external scheduler such as Maui. From Torque 4.0 onward, `pbs_mom` pairs with the `trqauthd` authentication daemon. Make sure the four fixed TCP ports in `/etc/services` are open across the cluster:

   ```text
   # (untested here) — /etc/services entries for Torque
   pbs         15001/tcp   # pbs server
   pbs_mom     15002/tcp   # mom to/from server
   pbs_resmom  15003/tcp   # request mom to manage resources
   pbs_sched   15004/tcp   # scheduler
   ```

2. Initialise the server database on first startup with `{sbindir}/pbs_server -t create` (`(untested here)`). Then define the compute nodes in `$PBS_HOME/server_priv/nodes`. Each line uses `node_name[:ts] [property...] [np=NUMBER]`, where `:ts` marks a timeshared node and `np` is the processor count. You can also add nodes with `qmgr`, for example `create node ib01 np=1,ntype=cluster,properties="MYCLUSTER"`, followed by `set node ...`. A node's `state` can be `free`, `offline`, `down` or `excl`, and `excl` applies while the node runs a job.

3. Create the queues and set the server parameters with `qmgr`. In the book's example, the queue is MYCLUSTER or batch. The queue can carry walltime caps such as `24:00:00` or `48:00:00`, and core or slot caps such as 20, 21, 22, 24 or 25. You can enter these settings interactively, load them from a file with `qmgr < MYCLUSTER.txt`, or dump the current settings with `qmgr -c "print server" > /tmp/server.conf`:

   ```text
   # (untested here) — Queue setup (in the book's example, queue MYCLUSTER or batch)
   create queue batch
   set queue batch queue_type = Execution
   set queue batch resources_max.walltime = 48:00:00
   create queue MYCLUSTER
   set queue MYCLUSTER queue_type = Execution
   set queue MYCLUSTER resources_max.ncpus = 20
   set queue MYCLUSTER resources_min.ncpus = 1
   set queue MYCLUSTER resources_max.nodect = 20
   set queue MYCLUSTER resources_max.walltime = 336:00:00
   set queue MYCLUSTER resources_default.ncpus = 1
   set queue MYCLUSTER resources_default.nodect = 1
   set queue MYCLUSTER resources_default.walltime = 01:00:00
   set queue MYCLUSTER max_user_run = 12
   set queue MYCLUSTER enabled = True
   set queue MYCLUSTER started = True

   # (untested here) — Server parameters via qmgr
   set server scheduling = True
   set server acl_host_enable = True
   set server acl_hosts = *.mycluster.com
   set server acl_hosts += server.mycluster.com
   set server managers = root@server.mycluster.com
   set server default_queue = MYCLUSTER
   set server log_events = 511
   set server mail_from = root
   set server query_other_tasks = True
   set server scheduler_iteration = 600
   set server node_ping_rate = 300
   set server node_check_rate = 600
   set server tcp_timeout = 6          # (6 seconds in Ch 14; often raised e.g. tcp_timeout = 20)
   set server task_stat_rate = 30
   set server mail_to = mail.mycluster.com
   ```

4. Configure `pbs_mom` on the compute nodes and add an epilogue cleanup script. On every compute node, write the server hostname into `$PBS_HOME/server_name`. Then create `/var/spool/PBS/mom_priv/config`:

   ```text
   # (untested here) — /var/spool/PBS/mom_priv/config in the book's example
   $logevent 255
   $pbsserver rsufs
   $cputmult 1.0
   $ideal_load 1.0
   $max_load 2.0
   ```

   When a parallel job's head process exits, stray worker processes and `/tmp` files can remain on the allocated nodes. Torque may already show those nodes as `free`. If a node is dedicated to one user job at a time, you can clean up automatically. Place an executable `/var/spool/PBS/mom_priv/epilogue` script on those nodes:

   ```bash
   #!/usr/bin/env bash
   # (untested here) — Chapter 14 Torque epilogue cleanup script example
   JOBID=$1
   USER=$2
   ######### Get the list of task nodes ###########
   if test -r "/var/spool/PBS/aux/$1"; then
   PBS_NODEFILE="/var/spool/PBS/aux/$1"
   # Perform cleanup on each node of the task
   for node in $PBS_NODEFILE; do
   ssh -o ConnectTimeout=5 $node \
   'pkill -KILL -u $USER; \
   find /tmp -user $USER -exec rm -r \{\} \; >& /dev/null'
   done
   fi
   ```

5. Customise the scheduler in `/var/spool/PBS/sched_priv/sched_config`, or in `maui.cfg`. In Torque, a separate process, the scheduler, selects the next task to launch. Keeping it separate lets you choose a policy that weighs time of day, system load, task size and queuing time. When the server's `scheduling` attribute is set to `True`, `pbs_server` reacts to two events, a task being added to the queue or an assignment finishing. Each event makes it call the scheduler to pick the next task to run.

   Torque ships with several schedulers, which you choose at installation with `./configure --set-sched=cc --set-sched-code=sgi_origin`. By default, the installation includes the FIFO scheduler. Production sites often pair Torque with the external Maui or Moab scheduler, which handles fair-share, backfill, reservations and priority weights in `maui.cfg`. For the built-in scheduler, entries in `/var/spool/PBS/sched_priv/sched_config` take the form `name:value [prime | non_prime | all]`. The options include `round_robin`, `by_queue`, `strict_fifo`, `fair_share` (with `half_life` and `sync_time`), `load_balancing`, `help_starving_jobs` (after `max_starve`), `log_filter` and `sort_by`.

   The built-in scheduler sorts tasks with the keys in Table 14-2 of the book, plus `multi_sort`, which takes several `key:` lines:

   | Sorting key (`sort_by`) | Meaning |
   |---|---|
   | `no_sort` | Don't sort tasks |
   | `shortest_task_first` | In ascending order by `cput` attribute |
   | `longest_task_first` | Descending by `cput` attribute |
   | `smallest_memory_first` | Ascending by `mem` attribute |
   | `largest_memory_first` | Descending by `mem` attribute |
   | `high_priority_first` | In descending order by `task_priority` attribute |
   | `low_priority_first` | In ascending order by `task_priority` attribute |
   | `large_walltime_first` | Descending by `task_walltime` attribute |
   | `short_walltime_first` | In ascending order by `task_walltime` attribute |

6. Submit work with `qsub -q QUEUE -l ncpus=CORES script_name`, or place `#PBS` directives inside the batch script and run `qsub myprog.batch`. The book's examples (`(untested here)`) cover four cases. For one node with several processes, `#PBS -l nodes=1:ppn=4` and `#PBS -q MYCLUSTER` set the request. Then `cd $PBS_O_WORKDIR` moves into the working directory, which holds the executable `progname`, and `./progname` runs it.

   An OpenMP program starts as many threads as the node has cores by default. To cap it at 2 cores, add `#PBS -l nodes=1`, `#PBS -q MYCLUSTER` and `#PBS -v OMP_NUM_THREADS=2`. For a long job, add `#PBS -l walltime=300:20:00`, which is 300 hours and 20 minutes.

   For MPI across several nodes, set `#PBS -l walltime=30:00:00` and `#PBS -l nodes=4:MYCLUSTER`. Then add `cd $PBS_O_WORKDIR` and `mpirun -np 4 ./progname`.

   Torque buffers everything the job writes to stdout and stderr on the compute node. At the end of the run, it copies those files back to the submission directory, named `<script_name>.o<task_number>` and `<script_name>.e<task_number>`. To watch output live with `cat`, `less` or `tail -f`, redirect it inside the script, for example `mpirun -np 4 progname > $PBS_JOBID`. With input as well, use `mpirun -np 4 progname < input_file > $PBS_JOBID`. If Torque cannot reach the destination path when the job ends, the files stay in `/var/spool/PBS/undelivered/` on the compute node, and the user is notified by mail.

7. Users and admins both use these commands to manage Torque jobs: `qsub`, `qdel`, `qhold`, `qrls`, `qmove`, `qmsg`, `qselect`, `qsig` and `qstat`. The examples include `qstat -a` and `qstat -q`. The list also includes `pestat`, and the X11 GUIs `xpbs` and `xpbsmon`.

Decide early whether your site will stay on PBS or move, because that choice decides how much of this setup you need to learn.

## 3. IBM Spectrum LSF (general knowledge, unverified)

Suppose your team's jobs run on an EDA or finance cluster. The scheduler there may well be IBM Spectrum LSF. LSF stands for Load Sharing Facility. It is a commercial scheduler, common in EDA, finance and some HPC centres.

The master host runs `mbatchd`, the master batch daemon, and `mbschd`, the scheduler. It may also have failover candidates. Each execution host runs `sbatchd` and `res`. `LIM`, the Load Information Manager, collects host load and resource information. The main concepts are queues, each with its own policies, hosts and host groups, and resource requirement strings such as `select[...] rusage[...] span[...] order[...]`. You also meet fair-share, preemption and "job slots".

`bsub` submits a job, for example `bsub -n 16 -R "span[ptile=8]" -gpu "num=4" -q gpu -W 12:00 < script`. `bjobs` shows queue status, `bkill` cancels a job and `bqueues` lists queues. `bhosts` and `lsload` show nodes, and `bhist` and `bacct` cover history and accounting. The other commands are `bmod`, `bswitch` and `bpeek`. Inside a script, you pass options as directives: `#BSUB -n`, `-q`, `-W`, `-o` and `-J name[1-100]%10`. The environment variables are `LSB_JOBID`, `LSB_HOSTS`, `LSB_DJOB_HOSTFILE` and `LSB_JOBINDEX`.

LSF's strengths are enterprise support, license-aware scheduling, a mature policy model and LSF multicluster. Many current AI sites that use LSF are migrating to Slurm or Kubernetes. Verify all of this against IBM documentation before you use it.

## 4. Flux

Flux has a very different shape from the other schedulers in this chapter. Suppose you hold an allocation and need to run millions of small tasks inside it. Flux is built for that case. It comes from Lawrence Livermore National Laboratory and its collaborators, and its core project is `flux-core`. The Flux documentation describes it as a framework for resource management.

A Flux instance is a set of `flux-broker` processes that form a tree-based overlay network. The docs say it "can be started by most launchers that can start MPI jobs." You can start one without administrator privilege, for example inside a Slurm allocation or a Kubernetes pod.

The key idea is that every job can itself be a Flux instance, called a subinstance. `flux batch SCRIPT` "submits SCRIPT to run as the initial program of a Flux subinstance". When the script exits, the subinstance ends and its resources return to the enclosing instance. Commands inside the script, such as `flux run` and `flux submit`, refer to the subinstance. `flux proxy JOBID` connects a shell to a running subinstance, and `flux uptime` shows `depth` and `size`. Hierarchical scheduling lets users run their own scheduler policy and millions of tasks inside an allocation, without loading the system scheduler. That makes it a strength for ensemble and AI-workflow workloads.

The main commands are `flux run` to run a job interactively, `flux submit` to queue one, `flux batch` to run a script as a subinstance, and `flux alloc` for an interactive subinstance. `flux batch` reads `#flux:` directive lines in the script. `flux bulksubmit` submits many jobs, `flux jobs` lists them and `flux cancel` cancels one. The rest are `flux resource list`, `flux queue`, `flux top`, `flux pstree`, `flux dmesg`, `flux uptime` and `flux config`.

Requests use options on `flux-run` and `flux submit`. `-n` sets tasks, `-c` cores per task and `-g` GPUs per task. `-N` sets nodes, while `--tasks-per-node` and `--gpus-per-node` set counts per node. `-x` requests exclusive use, `-t` sets the time limit, `-q` picks the queue and `-B` sets the bank for accounting. Dependencies use `--dependency=URI`, and the RFC 26 URIs have schemes such as `afterok`. The docs say "dependency chains behave like shell command separators", and `afterok` works like `&&`.

The scheduler is a separate project, `flux-sched`, which provides the graph-based resource model Fluxion. `flux-core` alone provides services such as the job manager, the KVS, which is a key-value store, and the message bus.

Flux's docs, in a page titled "Flux Maturity" from late 2025, say that Flux is the sole system workload manager on El Capitan. El Capitan was then number one on the TOP500. Flux also runs the unclassified sister systems at LLNL. The migration guide, titled "Migrating from Slurm", tells large centres not to leave Slurm yet. It says to "check back with us at the end of 2026". The guide lists missing features, including rolling upgrades, where nodes must run exactly the same flux-core version until 1.0. It also lists restarting Flux without killing running jobs, and immovable future reservations. Flux also works alongside Slurm, as an enhanced step manager and portability layer.

For AI work, nested scheduling suits hyperparameter sweeps and agent or RL workloads. Flux can run MPI-style jobs under Kubernetes through the Flux Operator, and it has strong tooling for ensembles. Flux is not common on commercial GPU clouds. Decide whether your ensemble work needs nested scheduling badly enough to accept Flux's missing features.

## 5. Command and concept map

When you move a team from one scheduler to another, the commands are what people notice first. The table lines up the same task across Slurm, PBS, LSF and Flux, so you can compare them side by side.

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

Look at the launch row and the node list row first. They show where you will see the most difference in how a job finds its hosts and starts its processes.

## 6. A tested translator

Suppose a team hands you a folder of PBS scripts and asks you to run them on Slurm. Translating each file by hand is slow and easy to get wrong. The repository includes a converter for that job.

The converter `code/part06/pbs2slurm.py` turns common `#PBS` directives into `#SBATCH` lines. It handles the job name, the queue (which becomes the partition), the account, output and error, arrays with their `%` throttle, mail, `depend=`, `walltime`, `place=...excl` (which becomes `--exclusive`), and `select` with `ncpus`, `mpiprocs`, `ngpus` and `mem`. It also rewrites `$PBS_JOBID`, `$PBS_O_WORKDIR` and `$PBS_ARRAY_INDEX`, and it flags `$PBS_NODEFILE`. Here is its output on a test script:

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

Look at the `select` line first, because it shows the arithmetic. The chunk asks for `ncpus=64` and `mpiprocs=8`. Dividing 64 CPUs across 8 processes leaves 8 CPUs per task, so the converter writes `--cpus-per-task=8`. This is a semantic translation, not a mechanical one. PBS `ncpus` counts CPUs per chunk, while Slurm `--cpus-per-task` counts CPUs per task.

The tool does not translate some things on purpose, so you must handle them by hand. Heterogeneous `select` requests with `+` chunks are flagged as TODO. So is vnode-specific placement, and custom resources map to Slurm features, licenses or GRES. Hooks need rewriting as `job_submit` plugins. Queue policy, such as fair-share and limits, must be rebuilt as described in 6.9. Job IDs in dependencies, the interactive behaviour of `qsub -I` and the MPI launch line also need manual work. Replace `mpirun -machinefile` with `srun`. Finish by running the result through `sbatch_lint.py`, covered in 6.11.

## 7. Migration plan (any scheduler to Slurm)

A migration touches more than user scripts. Queues, fair-share, hooks and accounting all have to move too.

1. Start with an inventory. List your queues, node classes, resource types, limits, fair-share trees, reservations, hooks or plugins, license servers and user scripts. Scan the scripts with `grep -r '#PBS'` or `'#BSUB'`. Then list the accounting integrations, web portals and workflow tools that call `qsub` or `bsub`.
2. Map the policies next. Queues become partitions or QOS, and limits become association or QOS limits. Fair-share shares become accounts. Preemption rules move to `PreemptType` (6.9), and custom resources become GRES, features or licenses. Hooks become `job_submit` and prolog or epilog scripts (6.14).
3. Translate the scripts, first with the automated pass and then with review. Build a compatibility shim only if you cannot avoid one. Slurm ships `qsub`-like wrappers in contribs, and PBS-compatible wrappers exist. Check which ones are available for your version.
4. Keep accounting continuous. Export the historical usage, seed fair-share if you want to, and keep the old reports for audits.
5. Run a parallel pilot. Split the nodes, dual-submit tests and compare the job outcomes. Train users and publish a command-map cheat sheet.
6. Cut over in node groups. Keep a rollback window, and decommission the old scheduler only after one full allocation cycle.
7. Revisit the workflow layer, such as Airflow, Nextflow or Snakemake DAGs. These usually have a Slurm executor already.

Decide who owns each step before you start.

## 8. Mixed environments and bridges

Many sites run more than one scheduler. You will likely meet three patterns.

The first is running Flux, Ray or Dask inside a Slurm allocation. That gives you fine-grained, nested scheduling without touching the system scheduler. The second is moving from Slurm to Kubernetes, covered in 6.16. Kubernetes-to-Slurm bridges also exist. They are niche queue-based virtual kubelets. The third is workflow tools. Nextflow, Snakemake, Airflow providers, Parsl and Dask-Jobqueue support Slurm, PBS and LSF through executors.

Cloud bursting works differently on each system. PBS and LSF have cloud connectors, while Slurm has power-save and cloud nodes, covered in 6.15. Decide whether you need a bridge, or whether a workflow tool can hide the difference.

## 9. Lab (self-checking converter lab tested; live scheduler installs untested)

Start with the self-checking Python lab. It runs locally, so you can check the converter before you touch a live scheduler. The lab, `code/part06/pbs2slurm_lab.py`, verifies `convert_line()` and `mem_to_slurm()` in `code/part06/pbs2slurm.py`. It runs them on a 9-directive PBS GPU script. The check confirms that `select=2:ncpus=64:mpiprocs=8:ngpus=8:mem=500gb` translates to `--nodes=2`, `--ntasks-per-node=8`, `--cpus-per-task=8`, `--gpus-per-node=8` and `--mem=500G`. It also checks the Torque port mapping in `/etc/services`, `15001` to `15004`. Finally, it validates the 9 `sort_by` keys from chapter 14 of *Supercomputers for Linux SysAdmins*, in `Table 14-2`:

```bash
python3 code/part06/pbs2slurm_lab.py
```

Next, work through these steps:

1. Run `pbs2slurm.py` on two of your own PBS scripts. Fix every TODO by hand, then lint the results with `sbatch_lint.py`.
2. Install OpenPBS in a single-node container or VM. Submit a `select` job, then inspect `pbsnodes -a` and `qstat -f`.
3. Install Flux with `flux start --test-size=4` in a container. Run `flux batch` with nested `flux run`, then use `flux proxy` and `flux uptime` to observe the depth.
4. Write the command-map cheat sheet for your site.
5. Draft a migration inventory template that lists every item in section 7, step 1.
6. Extend the converter to handle Torque-style `-l nodes=2:ppn=16` requests and heterogeneous select.

Work through step 1 before you install anything. The converter is the quickest way to see the translation rules at work.

## 10. Interview angles

If you move into an HPC or AI infrastructure role, interviewers may ask questions like these.

- What does PBS's `select` / `place` express that Slurm's `-N/-n` does not?
- Compare PBS MOM, LSF sbatchd and Slurm slurmd.
- What is a Flux subinstance and why is hierarchical scheduling useful?
- You inherit a PBS cluster and must move it to Slurm. Plan the migration.
- How would you translate a PBS script requesting `select=4:ncpus=32:ngpus=4:mem=128gb`?
- Which schedulers run the top supercomputers?
- Why do most GPU clouds standardise on Slurm or Kubernetes?

## Exercises

Work through these exercises in order. Each one asks you to explain or write something specific.

1. Start with the converter `code/part06/pbs2slurm.py` and its self-checking lab, `code/part06/pbs2slurm_lab.py`. Run the lab with `python3 code/part06/pbs2slurm_lab.py`. Then explain why `pbs2slurm.py` divides ncpus (64) by mpiprocs (8) to produce `#SBATCH --cpus-per-task=8`. Next, explain how it translates `-l place=scatter:excl`, `-J 0-9%3` and `-m abe`. Finally, explain why custom resources (`-l software=matlab`) and heterogeneous `+` chunks are emitted as `# TODO` comments for manual review.
2. Configure Torque queues, server parameters and the `pbs_mom` epilogue, using chapter 14 of *Supercomputers for Linux SysAdmins*. Write the `/etc/services` port lines (`15001`–`15004`). Write the `qmgr` commands that create queue MYCLUSTER (`resources_max.ncpus = 20`, `resources_max.walltime = 336:00:00`, `max_user_run = 12`), then dump `/tmp/server.conf`. Explain how `/var/spool/PBS/mom_priv/epilogue` uses `/var/spool/PBS/aux/$1` to clean up orphan user processes and `/tmp` files across nodes.
3. Work through Torque's scheduler, comparing `sched_config` with `maui.cfg`. Explain the difference between `round_robin`, `by_queue`, `strict_fifo`, `fair_share` and `help_starving_jobs` (`max_starve`) in `/var/spool/PBS/sched_priv/sched_config`. Write a `multi_sort` block that combines three keys from Table 14-2. Then state why production Torque sites often replace `pbs_sched` with Maui or Moab (`maui.cfg`).
4. Write the equivalent submission commands and directives for a 2-node job across Slurm (`sbatch`), OpenPBS (`qsub`), IBM Spectrum LSF (`bsub`) and LLNL Flux (`flux batch`). Each node needs 8 GPUs, 64 CPU cores and 500 GiB RAM. Your job also needs exclusive node access and a 12-hour walltime.
5. Explain how `flux batch` creates a nested flux-broker subinstance inside an enclosing Slurm allocation. Explain why hierarchical scheduling keeps a 50,000-task hyperparameter or RL ensemble from overwhelming slurmctld. Then name the missing features that Flux's own "Migrating from Slurm" guide highlights for large centers, so that you know what to watch for.
6. Design a 7-step migration plan from PBS or LSF to Slurm. Cover the script and hook inventory, queue-to-partition and QoS policy mapping, and automated conversion with `pbs2slurm.py` and `sbatch_lint.py`. Include historical fair-share seeding in `slurmdbd`, dual-partition parallel validation, and workflow engine cutover (Nextflow, Airflow or Snakemake).

## Checkpoint

<details>
<summary>1. Distinguish between the three historical code lines associated with the name **PBS** (*Supercomputers for Linux SysAdmins*, chapter 14).</summary>

1. Original OpenPBS came from MRJ Technology Solutions for NASA in 1998, and it was discontinued around 2004.
2. Torque, which stands for Terascale Open-Source Resource and QUEue Manager, is Adaptive Computing's open-source fork of OpenPBS 2.3.12. It is often paired with the Maui or Moab scheduler.
3. PBS Professional and modern OpenPBS come from Altair Engineering. Altair open-sourced its commercial PBS in 2020 as the `openpbs/openpbs` project.
</details>

<details>
<summary>2. Name the four core daemons of **OpenPBS / PBS Professional** and their Slurm equivalents.</summary>

- `pbs_server` is the central job and queue server and state manager, backed by PostgreSQL. Its Slurm equivalent is `slurmctld` plus `slurmdbd`. $\leftrightarrow$
- `pbs_sched` is the policy scheduler daemon that decides which job runs next. Its Slurm equivalent is the `sched/backfill` scheduling plugin in `slurmctld`.
- `pbs_mom`, the "Machine Oriented Mini-server", is the compute-node execution agent. Its Slurm equivalent is `slurmd` plus `slurmstepd`.
- `pbs_comm` is the inter-node communication relay. Its Slurm equivalent is hierarchical `TreeWidth` communication.
</details>

<details>
<summary>3. How do PBS `select` chunks and `place` directives work, and what is a **vnode**?</summary>

- `-l select=<N>:<chunk>[+<M>:<chunk>]` requests $N$ resource chunks. Each chunk sets its own `ncpus`, `mpiprocs`, `ngpus` and `mem`, and `+` joins heterogeneous chunks in one job.
- `-l place=<arrangement>:<sharing>:<grouping>` controls how chunks map onto hosts. The arrangements are `free`, `pack`, `scatter` and `vscatter`, combined with `excl`, `shared` or `exclhost`.
- A vnode, or virtual node, is an abstract, schedulable subdivision of a physical host. For example, one vnode might cover one NUMA socket or one GPU.
</details>

<details>
<summary>4. How are job arrays, job dependencies, and node hostlists expressed in PBS compared to Slurm?</summary>

- Arrays: `#PBS -J 0-9%3` sets the array, and `$PBS_ARRAY_INDEX` holds the index. Slurm uses `#SBATCH --array=0-9%3` and `$SLURM_ARRAY_TASK_ID`.
- Dependencies: PBS uses `#PBS -W depend=afterok:1234`, and Slurm uses `#SBATCH --dependency=afterok:1234`.
- Allocated hostlist: `$PBS_NODEFILE` is a file with one hostname line per allocated slot. `$SLURM_JOB_NODELIST` is a compressed range string that `scontrol show hostnames` expands.
</details>

<details>
<summary>5. Which four TCP ports in `/etc/services` are used by **Torque**, and what daemon was added alongside `pbs_mom` in Torque 4.0 (*Supercomputers for Linux SysAdmins*, chapter 14)?</summary>

- `15001/tcp` for `pbs` is used by `pbs_server`.
- `15002/tcp` for `pbs_mom` carries traffic between `pbs_mom` and the server.
- `15003/tcp` for `pbs_resmom` carries resource management requests to `pbs_mom`.
- `15004/tcp` for `pbs_sched` is the scheduler daemon.

Starting in Torque 4.0, the `trqauthd` client authentication daemon must also run alongside `pbs_mom`.
</details>

<details>
<summary>6. How are compute nodes defined in Torque's `$PBS_HOME/server_priv/nodes` file and via `qmgr`, and what does `:ts` mean (*Supercomputers for Linux SysAdmins*, chapter 14, `Table 14-1`)?</summary>

Each line in `$PBS_HOME/server_priv/nodes` uses the format `node_name[:ts] [property...] [np=NUMBER]`. You can also add a node dynamically with `qmgr: create node ib01 np=1,ntype=cluster,properties="MYCLUSTER"`. Appending `:ts` marks the node as time-shared, which means it is polled for status and used interactively, not for batch cluster allocation. The node states in `Table 14-1` are `free`, `offline` and `down`, plus `excl` while a task runs.
</details>

<details>
<summary>7. How do you initialize `pbs_server` for the first time, back up all server/queue settings with `qmgr`, and restore them (*Supercomputers for Linux SysAdmins*, chapter 14)?</summary>

Initialize the database the first time with `{sbindir}/pbs_server -t create`. Dump the server and queue configuration with `qmgr -c "print server" > /tmp/server.conf`. To restore it, you run `qmgr < /tmp/server.conf`.
</details>

<details>
<summary>8. What parameters go into `/var/spool/PBS/mom_priv/config`, and how does `/var/spool/PBS/mom_priv/epilogue` clean up stray processes after a Torque job ends (*Supercomputers for Linux SysAdmins*, chapter 14)?</summary>

The config file sets `$logevent 255`, `$pbsserver <head_host>`, `$cputmult 1.0`, `$ideal_load 1.0` and `$max_load 2.0`. When a job finishes on the head compute node, `pbs_mom` runs `/var/spool/PBS/mom_priv/epilogue` with `JOBID=$1` and `USER=$2`. The script reads `/var/spool/PBS/aux/$1`, which holds the `PBS_NODEFILE` list. It then SSHes to every allocated node, runs `pkill -KILL -u $USER`, and deletes the user's files in `/tmp`.
</details>

<details>
<summary>9. In Torque's `/var/spool/PBS/sched_priv/sched_config`, what do `round_robin`, `strict_fifo`, `help_starving_jobs`, and `sort_by` (`Table 14-2`) control (*Supercomputers for Linux SysAdmins*, chapter 14)?</summary>

- `round_robin` cycles one task at a time across queues, instead of draining one queue until a limit is hit.
- `strict_fifo` blocks younger tasks whenever the oldest queued task cannot start yet. That prevents starvation of large jobs, but it can leave idle gaps.
- `help_starving_jobs` stops other tasks from starting once a job has waited longer than `max_starve`.
- `sort_by`, in `Table 14-2`, orders queued tasks. The keys are `no_sort`; the pair `shortest_task_first` and `longest_task_first` by `cput`; the pair `smallest_memory_first` and `largest_memory_first` by `mem`; the pair `high_priority_first` and `low_priority_first` by `task_priority`; the pair `large_walltime_first` and `short_walltime_first` by `task_walltime`; and `multi_sort`.
</details>

<details>
<summary>10. How does Torque name standard output and error files by default, how can a user watch output in real time, and where do undeliverable output files land (*Supercomputers for Linux SysAdmins*, chapter 14)?</summary>

By default, Torque buffers stdout and stderr on the execution node. It copies them back to the submission directory at job completion, as `<script_name>.o<task_number>` and `<script_name>.e<task_number>`. To watch output live, redirect stdout inside the batch script, as in `mpirun -np 4 progname > $PBS_JOBID`, and run `tail -f`. If Torque cannot write to the submission path when the job ends, the files are saved in `/var/spool/PBS/undelivered/`, and the user receives mail.
</details>

<details>
<summary>11. Name the core daemons of **IBM Spectrum LSF** and its primary CLI commands.</summary>

The master host runs `mbatchd`, the master batch daemon, `mbschd`, the scheduler daemon, and the master `LIM`, the Load Information Manager. Each execution host runs `sbatchd`, the slave batch daemon, `res`, the Remote Execution Server, and a host `LIM`. The main CLI commands are `bsub` to submit, `bjobs` for queue status, `bkill` to cancel, `bqueues` for queues, `bhosts` and `lsload` for nodes, and `bhist` and `bacct` for history and accounting.
</details>

<details>
<summary>12. How do you request 16 tasks packed 8 per node with 4 GPUs and a 12-hour walltime in LSF (`bsub`)?</summary>

Use `bsub -n 16 -R "span[ptile=8]" -gpu "num=4" -q gpu -W 12:00 < script.sh`. You can also put `#BSUB` directives inside the script, and read `$LSB_JOBID` and `$LSB_DJOB_HOSTFILE` from inside it.
</details>

<details>
<summary>13. What is **LLNL Flux**, and how does its **hierarchical subinstance** model (`flux batch`) differ from Slurm?</summary>

Flux combines `flux-core` with the Fluxion graph scheduler from `flux-sched`. Each scheduler instance is a tree overlay of `flux-broker` processes. When you run `flux batch script.sh`, Flux starts a new child instance, called a subinstance, inside the allocated resources. The subinstance has its own job manager, KVS and scheduling policy. You can launch millions of fine-grained `flux submit` or `flux run` tasks inside it, and none of them adds RPC load to the top-level system scheduler.
</details>

<details>
<summary>14. What does `flux proxy JOBID` do, and how are job dependencies expressed in Flux?</summary>

`flux proxy JOBID` attaches a shell or command to the message bus of a running Flux subinstance. `flux uptime` then shows the nesting `depth` and `size`. Dependencies use RFC 26 URIs, such as `--dependency=afterok:ID`. The `afterok` form behaves like a shell `&&` chain.
</details>

<details>
<summary>15. Which TOP500 #1 supercomputer runs Flux as its sole system workload manager, and what limitations does Flux's Slurm migration guide note for general centers?</summary>

El Capitan at Lawrence Livermore National Laboratory (LLNL) runs Flux as its system workload manager. If you run a general HPC center, Flux's migration guide warns that pre-1.0 Flux still has gaps. It lacks rolling daemon upgrades, because nodes must run exactly the same `flux-core` version. It also lacks controller restarts that preserve running jobs, and it has immovable future maintenance reservations.
</details>

<details>
<summary>16. Why does `code/part06/pbs2slurm.py` translate `#PBS -l select=2:ncpus=64:mpiprocs=8:ngpus=8:mem=500gb` into `--cpus-per-task=8` instead of `--cpus-per-task=64`?</summary>

Consider the arithmetic. PBS `ncpus=64` gives the total CPUs per chunk, which means per node. `mpiprocs=8` gives the MPI tasks per chunk. In Slurm, `--cpus-per-task` multiplies with `--ntasks-per-node=8`, so each of the 8 tasks needs its share of the 64 CPUs. That gives $64 / 8 = \mathbf{8}$ CPUs per task, written as `--cpus-per-task=8`.
</details>

<details>
<summary>17. Name five PBS features or constructs that an automated directive translator (`pbs2slurm.py`) cannot mechanically convert without human review.</summary>

1. Heterogeneous multi-chunk requests, such as `select=1:...+4:...`.
2. Custom site resource attributes, such as `-l software=matlab`, which map to Slurm licenses, features or GRES.
3. Python admission and execution hooks, written with `pbs_python`, which map to Slurm `job_submit.lua` and `Prolog`/`Epilog`.
4. Queue-level fair-share, routing queues and preemption policies, which must be rebuilt in `sacctmgr` QoS or Fair Tree.
5. `mpirun -machinefile $PBS_NODEFILE` launch lines, which you should replace with `srun --mpi=pmix`.
</details>

<details>
<summary>18. What are the 7 steps of a safe production migration from PBS or LSF to Slurm?</summary>

1. Inventory queues, limits, custom resources, hooks, user scripts and workflow integrations.
2. Map policies to Slurm partitions, QoS, Fair Tree accounts, GRES or licenses, and `job_submit`, `Prolog` and `Epilog`.
3. Translate user scripts with `pbs2slurm.py` and `sbatch_lint.py`, plus optional `qsub` compatibility wrappers.
4. Preserve accounting continuity by exporting historical usage and seeding initial fair-share.
5. Run a parallel pilot on a subset of nodes, with a user command-map cheat sheet.
6. Cut over in node waves, with a defined rollback window.
7. Switch workflow executors, such as Nextflow, Snakemake, Airflow and Ray or Dask, to their native Slurm backends.
</details>

<details>
<summary>19. When should you run **Flux, Ray, or Dask inside a Slurm allocation** instead of submitting 100,000 individual `sbatch` jobs?</summary>

Use this approach for high-throughput ensembles, reinforcement-learning rollouts or sub-minute task graphs. You launch one multi-node Slurm allocation, then start Flux (`srun flux start ...`), Ray or Dask inside it. That keeps `slurmctld` completely insulated from high-frequency task scheduling.
</details>

<details>
<summary>20. Map the five everyday user commands (submit batch, interactive shell, list queue, cancel job, inspect nodes) across **Slurm**, **PBS**, **LSF**, and **Flux**.</summary>

- Submit a batch job: `sbatch` on Slurm, `qsub` on PBS, `bsub <` on LSF, and `flux batch` on Flux.
- Interactive shell: `salloc` or `srun --pty` on Slurm, `qsub -I` on PBS, `bsub -Is` on LSF, and `flux alloc` on Flux.
- List the queue: `squeue` on Slurm, `qstat` on PBS, `bjobs` on LSF, and `flux jobs` on Flux.
- Cancel a job: `scancel` on Slurm, `qdel` on PBS, `bkill` on LSF, and `flux cancel` on Flux.
- Inspect nodes: `sinfo` on Slurm, `pbsnodes -a` on PBS, `bhosts` or `lsload` on LSF, and `flux resource list` on Flux.
</details>

## Sources and review notes

Use these notes to judge what you can trust in this chapter.

- OpenPBS: man pages `qsub(1B)`, the `pbs(8B)` family and `pbs_resources(7B)`, from commit `cd7ab5e` of `openpbs/openpbs`.
- Torque history: MRJ's 1998 OpenPBS, Adaptive Computing's Torque and Altair's PBS Pro. The daemon ports `15001`–`15004` and `trqauthd` come from the same source.
- Server and node setup come from the same source. They cover `$PBS_HOME/server_priv/nodes` with its `:ts` timeshared flag, the node attributes in `qmgr` Table 14-1, and the server and queue setup commands, including `qmgr -c "print server" > /tmp/server.conf`.
- Scheduler and output setup come from the same source. They cover `mom_priv/config`, the `/var/spool/PBS/mom_priv/epilogue` cleanup script, `configure --set-sched=cc --set-sched-code=sgi_origin`, `maui.cfg`, and the `sched_config` sorting keys in Table 14-2.
- Batch scripts also come from the same source. They include `myprog.batch`, the OpenMP and MPI scripts, the output names `<script_name>.o<task_number>` and `<script_name>.e<task_number>`, and `/var/spool/PBS/undelivered/`. Job control commands `pestat`, `xpbs` and `xpbsmon` do too.
- That source is *Supercomputers for Linux SysAdmins*, chapter 14, "14. OpenPBS and Torque", at `supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to-hardware`.
- Flux: the `flux-core` documentation, including `flux-batch(1)`, the job parameter and dependency pages, and "Migrating from Slurm" in the admin guide, commit `40ecc8d`.
- LSF: general knowledge only. Verify it with the IBM Spectrum LSF documentation. For SUNK and other Kubernetes bridges, see Chapter 6.16.
- Run here: `code/part06/pbs2slurm.py` and `python3 code/part06/pbs2slurm_lab.py`, with 3 passed and 0 failed.
- Explicitly labelled inferences: the semantic `ncpus // mpiprocs` translation in `code/part06/pbs2slurm.py` and `pbs2slurm_lab.py` is a deterministic migration aid. It converts chunk-level PBS CPU requests into per-task Slurm requests.
- Not verified on live hardware: all Torque (`pbs_server`, `qmgr`, `pbs_mom`, `qsub`), OpenPBS, Flux and LSF commands in this chapter, the current upstream status of Torque, the PBS wrappers shipped with Slurm, and the Flux roadmap dates (`untested here`).

Treat those items as untested until you run them yourself.
