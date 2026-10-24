---
id: "c08-11"
title: "8.11 Monitoring, health checks and alerts in BCM"
sidebar_label: "8.11 Monitoring, health checks and alerts in BCM"
sidebar_position: 11
description: "How BCM watches a cluster: measurables and data producers, metrics, enummetrics and health checks, triggers with enter, leave, during and flapping actions, severities and AlertLevel, built-in actions, GPU and DCGM health checks, consolidation and scale, and a safe design for automatic remediation, with the manual's trigger rules reproduced in a tested model"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "Nebius GPU"
---

# 8.11 Monitoring, health checks and alerts in BCM

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 8: NVIDIA Base Command Manager |
| Status | Drafted (`monitoring_lab.py`: 46 checks pass; cluster commands **untested** on live BCM) |

## Why this matters for AI infrastructure

A training run that loses one GPU can stall hundreds of others. The sooner a bad node is found and drained, the less compute is wasted. BCM's monitoring collects thousands of numbers per node, turns some of them into pass or fail checks, and can run actions when something changes. The skill is deciding what to watch, what is only information and what should act on its own.

## Prerequisites and outcomes

You need chapters 8.1 to 8.7 (objects, nodes, power) and 8.8 (drain). After this chapter you can:

- name the parts of the monitoring pipeline and what each does
- tell metrics, enummetrics and health checks apart, and read `PASS`, `FAIL`, `UNKNOWN` and `no data`
- predict exactly when a trigger fires, using enter, leave, during and flapping
- build a custom trigger and action, and validate it before committing
- list the GPU, DCGM and Redfish checks BCM provides
- understand consolidation and when monitoring needs to scale out
- design automatic remediation that cannot loop or hide a hardware fault

## 1. The pipeline

```mermaid
flowchart LR
  P[data producer: a sampler or a script] -->|every N seconds| M[measurable: metric, enummetric or health check]
  M --> S[(stored on the node, picked up by the head node)]
  M --> T{trigger: expression on a measurable}
  T -->|enter, leave, during, flapping| A[action: built-in or script]
  M -->|severity| L[AlertLevel metrics]
  A --> E[event + mail + drain + power ...]
```

The manual's words, simplified:

- A **data producer** is the thing that takes a measurement. It may produce many measurables (ProcStat gives CPU user, system, idle, forks...), or one (a health check script such as `ssh2node`).
- A **measurable** is one measured value for an **entity**. An entity is usually a device, but can be a category, partition, software image, network, job queue, user and more.
- **Metrics** are numbers (or `no data`). **Enummetrics** have a small set of states (for example `DeviceStatus`). **Health checks** have the states `PASS`, `FAIL`, `UNKNOWN` and `no data`.
- A **trigger** is a condition on a measurable. When it is met, it launches **actions**. An action is a built-in or a script that exits 0 on success.
- **Severity** and **AlertLevel** summarise how bad things are.

## 2. Health checks, severities and AlertLevel (10.2.4 to 10.2.8)

`PASS` means fine. `FAIL` means failed. **`UNKNOWN`** means it neither passed nor failed (for example a timeout); the manual says to investigate it. **`no data`** means the check did not run (for example it is disabled), and CMDaemon writes it explicitly so a gap is visible. Keep `UNKNOWN` as its own signal; do not fold it into `FAIL`.

**Default severities** come from the three pre-defined trigger templates: **FAIL 15, UNKNOWN 10, PASS 0**. A standalone health check script can override them with its own value (`FAIL 40`, as the `hpraid` script does).

**AlertLevel** is a special metric with three forms, recalculated whenever an event with a severity happens:

| Form | Meaning | Use it to |
|---|---|---|
| count | number of events at "notice" level or higher | see how many problems |
| max | the highest latest severity | see the worst problem |
| sum | the sum of the latest severities | see overall load of problems |

`healthoverview` (device mode) shows sum, maximum and count per node. Example from the manual: a node with "hot" (15) and "fan high" (15) has sum 30, max 15, count 2.

## 3. Common health checks you will see

From `/cm/local/apps/cmd/scripts/healthchecks/` and the measurables list: `ssh2node`, `diskspace`, `mounts`, `mysql`, `ldap`, `ntp`, `dmesg`, `oomkiller`, `defaultgateway`, `exports`, `interfaces`, `chrootprocess` (a daemon running inside an image), `cmsh`, `cuda-dcgm`, `lustre`, `hpraid`, `ManagedServicesOk` (CMDaemon), and the Redfish checks `chassis_health`, `cpu_health`, `memory_health`, `storage_health`, `drive_health`, `volume_health`, `psu_health` and more. The `cm-docker-setup`, `cm-kubernetes-setup` and `cm-wlm-setup` tools add their own health checks when they install a component (chapters 8.8 to 8.10).

In cmsh: `measurables node001` lists everything for an entity, `healthchecks`, `metrics`, `enummetrics` the subsets, `usage <measurable>` shows which entities use one, `monitoringproducers` lists the producers on an entity.

## 4. Triggers: exactly when does it fire? (10.4.5)

A trigger watches one measurable. The "zone" is where the condition is true (for example `CPUUser > 50`). The manual defines four launch options:

| Option | Fires when |
|---|---|
| **Enter actions** | this sample is in the zone **and the previous sample was not** |
| **Leave actions** | this sample is out of the zone and the previous sample was in it |
| **During actions** | this sample and the previous sample are both in the zone |
| **State flapping actions** | the threshold is crossed repeatedly: 5 times (default) within 5 minutes (default) |

Consequences the lab proves:

- **The first sample can never "enter"**: there is no previous sample. The manual says it directly for the example: after an enter, the very next sample never enters again.
- A value that stays in the zone fires **During** every sample, not Enter again.
- Pre-defined triggers: only **three** exist, all with Enter actions: failing, passing and unknown health checks, each running the Event action at severities 15, 0 and 10.
- **The default sampling period is 120 s** (the manual's basic example samples `CPUUser` every 120 s, changeable in the data producer).

**A derived caveat (my arithmetic).** With 120 s sampling and flapping defined as 5 crossings in 300 s, flapping can never be detected on that measurable: crossings are only seen between consecutive samples, so at most two fit in five minutes. To use flapping actions, sample faster or loosen the flap settings. The manual does not say this; I computed it from its defaults, and the lab labels it so.

**The basic example (10.1).** The manual simulates a user running eight `yes` processes on a head node. The administrator clones the `killprocess` action as `killallyesaction` pointing at a script in `/cm/local/apps/cmd/scripts/actions/`, then clones the *Failing health checks* trigger as `killallyestrigger` with Enter action `killallyesaction` and the expression *entity = head node, measurable `CPUUser`, operator `>`, value 50*. `CPUUser` is in jiffies per second; do not confuse it with `CPUUsage`, a percentage. It is deliberately contrived: any CPU-heavy process would fire it.

**Always validate.** In cmsh, `validate` on a new trigger warns "No actions were set" and "No known measurable matches the specified regexes". The manual's own example is a misspelled `devicestate` (the data producer) instead of `devicestatus` (the measurable).

```text
[basecm11]% monitoring trigger add nodedown
[...]% expression
[...->expression]% set measurables devicestatus ; set operator eq ; set value down
[...]% validate
```

(The manual's example, shortened; untested here.)

## 5. Actions (10.2.6, G.4)

Built-in actions, with where they run:

| Action | Runs on | What it does |
|---|---|---|
| Drain / Undrain | head ("Active") | stop / allow the workload manager placing jobs on the node. Plan for undrain from another node if the drain happened on a node that went down |
| Send e-mail to administrators | head | uses the mail setup from 8.3; recipients are an action parameter |
| Event | head | an event for connected clients |
| ImageUpdate | head | update the node's image (chapter 8.4) |
| PowerOff, PowerOn, PowerReset | head | **hard**, through the BMC or PDU |
| Reboot, Shutdown | node | clean, through the operating system |
| `killprocess`, `remount`, `testaction` | node | standalone scripts in `/cm/local/apps/cmd/scripts/actions/` (head) or the image path (nodes) |

Drain has a hidden setting, `post-drain-actions`, that runs more actions after the node is fully drained: `set -e -v post-drain-actions send\ e-mail\ to\ administrators poweroff`. Also relevant: `monitoringactionhistory` shows which triggers fired and what ran.

## 6. GPU and DCGM health (G.1.6, G.2.2)

The `GPUSampler` producer reads GPUs. Metrics are written `name:gpuN` (for example `gpu_ecc_dbe_agg:gpu1`): ECC single and double bit counts (aggregate and volatile), memory, power, clocks, temperature, NVLink bandwidth, power violation time, and `gpu_xid_error`. Profiling metrics (SM activity, NVLink read and transmit) exist too (see MIG caveats in 8.3).

**Fourteen GPU health checks** (the V100 and A100 table; newer GPUs are in the Mission Control Manual): `gpu_health_driver`, `_hostengine`, `_inforom`, `_mcu`, `_mem`, `_nvlink`, `_nvswitch_fatal`, `_nvswitch_non_fatal`, `_overall`, `_pcie`, `_pmu`, `_power`, `_sm`, `_thermal`. Written with `:gpuN` for one GPU, without it for all; `_hostengine` is always for the whole node.

**DCGM WARN.** These checks report only PASS, UNKNOWN or FAIL. A DCGM **WARN is reported as PASS by default**, with the reason in the Info field. If you want warnings to count as failures, set the `GPUSampler` extra parameter **`Warn as fail`** to true (`monitoring setup use gpusampler; set -e "Warn as fail" true; commit`); it then applies to all `gpu_health_*` checks. This is an easy way to have a "healthy" cluster that is hiding DCGM warnings: decide on purpose.

The `cuda-dcgm` package must be present for GPU metrics (chapter 8.3).

## 7. Keeping data: consolidation, storage and scale

- Raw samples are stored on the head node. **Consolidators** summarise old data; the default `hour` consolidator keeps hourly averages for **7 years 26 weeks** at most **65,536 samples** (65,536 hours is about 7.5 years; the lab checks this). Reducing the sample limit discards consolidated data, so change it with care.
- `monitoringinfo --storage` shows disk use; the raw store grows in **1 GB increments**. `cm-monitoring-disk-usage.py` estimates the final size (the manual's 10-entity, 286-measurable example gives a maximum of about 1.4 GB). `dumpmonitoringdata` exports a period, `monitoringdrop` removes data, `samplenow`, `latestmetricdata` and `latesthealthdata` read live and last values.
- Nodes **cache** their samples; the head node picks them up at a **pickup interval** (`monitoringpickup`).
- **Scale:** the traditional design handles about **10,000 nodes** with default metrics and hit a limit around **20,000** on 2020 hardware. **Offloaded monitoring** assigns the `monitoring` role to nodes, removes the single point of failure and scales with the cluster (10.7). Add data producers and metrics with the monitoring storage in mind.

## 8. Automatic remediation: a design that cannot make things worse

BCM gives the pieces (health check, trigger, action). It does **not** ship a policy. This is the design recommendation from the user's notes (marked as the author's recommendation there; the mechanisms are documented, the mapping is judgment):

| Tier | Fault | Suggested chain | Why |
|---|---|---|---|
| 1 | suspected **hardware** (GPU falls off the bus, uncorrectable ECC, PSU) | Drain, notify, evidence (`NVSMHealthDump`). **No automatic reboot or image update.** | A reboot does not repair silicon; it returns suspect hardware to the scheduler |
| 2 | reproducible **software state** (missing mount, wrong package, bad module) | Drain, `ImageUpdate` (or reboot), re-run the check, Undrain on PASS | The image defines the state, so restoring the image restores the node |
| 3 | **transient** (a brief fabric blip, one timeout) | alert; use flapping and `UNKNOWN`; drain only if it persists | Reimaging healthy nodes wastes the time you meant to save |

**The loop trap.** In tier 2 a node that fails after every reimage will be reimaged forever. Count attempts per node (the counter is yours to build in the action script) and move the node to tier 1 after the second failure. The lab implements this cap.

Also: treat `UNKNOWN` as its own signal; remember an action that drains must be paired with an undrain plan; and test every trigger on one node with `samplenow` and `validate` before applying it to a category.

## 8.1 Base View monitoring screens, data producer tuning, consolidator math, and PromQL

- **Top-right Base View icons:** eight icons sit in the top-right bar, from left to right: (1) **Cluster Overview**, (2) **Job Accounting**, (3) **Monitoring** (visual graphs), (4) **Chargeback**, (5) **Events**, (6) **Background Tasks**, (7) **Package Updates** (the GUI equivalent of `packages --outdated` in `cmsh`), and (8) the **Menu (`≡`)** icon (dark mode toggle and logout).
- **Monitoring visualization window:** opens the **Critical Services** dashboard by default, with two plot panels plotting the `ManagedServicesOK` health check—panel 1 for the head node, panel 2 for all regular nodes in the `default` category. The left navigation filter is case-insensitive, supports regexes (`node001.*cpuuser`, `(node001|node002).*cpuuser`), and uses `/` for tree depth (`node001/cpu/cpuuser`). Dragging a measurable into a panel draws two graphs: a smaller bottom bar chart of polled values and a larger upper interpolated line graph.
- **Data producer settings and RLE:** samples are compressed with **run length encoding (RLE)**.
  - **`Maximal samples` and `Maximal Age`:** whichever limit is reached first drops older RLE samples (`0` means ignore that limit; setting both to `0` keeps samples forever and is discouraged because of disk exhaustion). Reducing `Maximal samples` discards previously consolidated values after about **30 minutes**.
  - **`Offset` and `Fuzzy offset`:** `Offset` delays sampling for producers that depend on others (for example `AggregateNode`, which computes `TotalCPUIdle` and `TotalMemoryFree`, depends on `ProcStat` for `CPUIdle` and `ProcMemInfo` for `MemoryFree`). `Fuzzy offset` is a multiplier in `[0, 1]` that spreads node sampling evenly across `[0, fuzzy_offset * interval]` to avoid a sampling storm—in the manual's example, a `120 s` interval with a `0.25` fuzzy offset spreads node samples across a **`30 s`** window (`0.25 * 120 = 30`).
  - **`When` and `Only when idle`:** `When` is `Timed` (default), `On demand`, `Out of band`, or `On start`. Enabling `Only when idle` runs the producer only when the node is idle, defined by the metric condition `LoadOne > 1`.
- **Cumulative metrics:** a metric marked `Cumulative` is monotonic from boot (such as interface bytes received, resetting at boot); administrators usually plot its differential per sample interval (bytes/second).
- **Consolidators and the consolidation time equations:**
  - Pre-existing groups are `default` (in BCM 11 it contains only `hour`, interval `3600 s`; clusters upgraded from BCM 10 also keep legacy `day` and `week`) and `none` (no consolidation). Each consolidator item has `Kind` (`average` by default, `maximum`, or `minimum`; **changing `Kind` discards all previous consolidated data for that consolidator**).
  - When a measurable with interval `Interval_measurable` and maximal raw samples `Maximal_samples_measurable` drops its oldest raw point, that point enters consolidation at age:
    ```text
    t_raw_gone = Maximal_samples_measurable * Interval_measurable
    ```
    With `Offset` on the consolidator item, consolidated data is presented starting at `t_consolidation = t_raw_gone + Offset` into the past, and extends back to `t_consolidation_gone = Maximal_samples_consolidation * Interval_consolidation`.
- **Action `Allowed time` syntax and `Run on`:** an action runs on `Active head node`, `Node` (the triggering node), or `Monitoring node`. `Allowed time` restricts when an action may start (months and days in **lowercase**), such as `november-march{monday-saturday{13:00-17:00}}`, `may-september{monday-friday{09:00-18:00};saturday-sunday{13:00-17:00}}`, or `may,september{1-15{monday-friday}}`. In `Send e-mail to administrators`, the `Info` field replaces `{infomessage}` in `/cm/local/apps/cmd/scripts/actions/sendemail.py`.
- **Standalone monitored entities and PromQL queries:** `Monitoring > Standalone Monitored Entities` monitors unmanaged devices (no CMDaemon on the target, such as an admin workstation pinged by a custom script on the head node). `Monitoring > Queries` manages PromQL job-related queries and drilldown queries (`Monitoring > Queries > <query> > Manage the drilldown queries`).

## 8.2 The User Portal, Cloud Job Tagging, Events, the Event Bucket, and InfoMessages

- **The User Portal:** a restricted, read-only version of Base View for non-root users, installed via the **`cm-webportal`** package (`yum install cm-webportal`; when missing, the head-node landing page shows a grey block with `⊕`; when installed, a colored block with a chain-link icon).
  - **URL and server:** `https://<head>:8081/userportal`, served directly by **CMDaemon** (unlike the landing page, which Apache serves), using BCM's self-signed X509v3 certificate (`NVIDIA Bright CA`) unless replaced with a public CA certificate.
  - **Authentication and profile:** users log in with their own credentials and get the `readonly` profile by default. To enable a shared login for all users, create a user in `cmsh` and set `"username"` and `"password"` in `/cm/local/apps/cmd/etc/htdocs/userportal/assets/config/common-credentials.json` (blank by default, which disables common access).
  - **Home page:** shows the Message Of The Day (`/cm/local/apps/cmd/etc/htdocs/userportal/assets/config/message-of-the-day.html`), cluster documentation links, a cluster state overview **refreshed every 10 s by default**, and a Job Accounting chart icon. **Security rule:** the user portal serves static files only and **will not execute PHP or CGI scripts**.
- **Cloud Job Tagging (AWS only):** enabled with `cmsh -c 'cloud; use amazon; set cloudjobtagging yes; commit'`. When a job starts on an AWS cloud node, CMDaemon applies four cost-allocation tags (out of AWS's 50-tag limit)—**`BCM_JOB_ID`**, **`BCM_JOB_ACCOUNT`**, **`BCM_JOB_USER`**, and **`BCM_JOB_NAME`**—and removes them when the job stops, so AWS Cost Explorer can attribute cloud spend per job.
- **Viewing events in Base View and `cmsh`:** enabled by the `EventLogger` directive in `cmd.conf`. In `cmsh`, the global `events` command supports `on [broadcast|private]`, `off [broadcast|private]`, `show-acknowledged <yes/no>`, `show-detailed <yes/no>`, `level <info|notice|warning|error|alert>`, `clear`, `details <id>`, `acknowledge <id>`, `unacknowledge <id>`, `events <number> [level]`, and `events follow` (like `tail -f`). By default (`events` with no arguments): `Private events: off`, `Broadcast events: on`, `Acknowledged events: off`, `Details: off`, `Level: notice`. For example, `updateprovisioners` emits **private** events, which appear live in your `cmsh` session only if `events on private` (or `events on`) is set.
- **The Event Bucket and InfoMessages:**
  - **InfoMessages from health/metric scripts:** inside a measurable script, writing to **file descriptor 3** sets the status reason (InfoMessage):
    ```bash
    echo "Drive speed unknown: Reverse polarity" >&3
    ```
  - **Head/node Event Bucket (`/var/spool/cmd/eventbucket`):** piping a line into `/var/spool/cmd/eventbucket` creates a BCM event (default severity `info`). Prefix with `EVENT_SEVERITY_DEBUG:`, `EVENT_SEVERITY_INFO:`, `EVENT_SEVERITY_NOTICE:`, `EVENT_SEVERITY_WARNING:`, `EVENT_SEVERITY_ERROR:`, or `EVENT_SEVERITY_ALERT:` to choose the severity; regex filters live in `/cm/local/apps/cmd/etc/eventbucket.filter` (`EventBucket` and `EventBucketFilter` directives in `cmd.conf`).
  - **Tagging device status lines and reloading logging via the Event Bucket:**
    - `echo "STATE.USERMESSAGE.node001:just right" > /var/spool/cmd/eventbucket` makes `device status node001` display `node001 ... (just right) [ UP ]` (omitting `.node001` targets the local host; echoing an empty message `STATE.USERMESSAGE.node001:` clears it).
    - `echo LOGGING.RELOAD.CONFIG > /var/spool/cmd/eventbucket` reloads CMDaemon's logging configuration **without restarting `cmd`**.
  - **Node-installer Event Bucket (`/tmp/eventbucket`):** during node provisioning (before `systemd` and node `CMDaemon` are up), initialize and finalize scripts can write to `/tmp/eventbucket` in two modes: `echo "info-message: text" > /tmp/eventbucket` (updates the device status line) or `echo "Some text" > /tmp/eventbucket` (raises a warning event).

## 9. Common first mistakes

1. Folding `UNKNOWN` into `FAIL`, or ignoring it.
2. Expecting Enter to fire again while the value stays high (that is During).
3. Relying on flapping with 120 s sampling and default settings.
4. A trigger on a misspelled measurable (always `validate`).
5. A power or reboot action wired to an automatic hardware fault.
6. A drain action with no undrain plan.
7. Leaving DCGM warnings hidden as PASS without choosing it.
8. Adding many measurables and never checking monitoring disk growth.
9. Reducing a consolidator's sample count and losing history.
10. Using `CPUUser` (jiffies per second) as if it were a percentage.

## 10. Exercises

1. Run `python3 monitoring_lab.py`. Pick four checks and explain each rule in your own words.
2. Using `evaluate_trigger`, find a series where Enter fires twice but During fires only once.
3. Choose a sampling interval and flap settings for a link-flap alert on a GPU fabric port. Show it can be detected.
4. Write the cmsh steps (from the manual, untested) for a trigger that mails the administrators when `gpu_health_overall` fails, and a second that drains on `gpu_health_nvlink` failing.
5. Decide whether you want `Warn as fail` on a training cluster, and say what you would watch if not.
6. Sketch a remediation counter that survives a reboot of the node (it must live somewhere other than the node's local disk).

## 11. Interview angles

- "How does BCM decide a node is unhealthy?" Health checks produce PASS/FAIL/UNKNOWN/no data on a schedule; triggers watch them; severities feed AlertLevel and `healthoverview`.
- "Explain Enter versus During." Enter is a threshold crossing; During is staying in the zone.
- "What would you not automate?" Reboot or reimage for suspected hardware faults.
- "How do you avoid alert storms?" Flapping detection, severities, `mute` during maintenance (chapter 8.4), consolidation of notifications.
- "When does head-node monitoring stop scaling?" Around 10,000 to 20,000 nodes; offloaded monitoring.

## 12. Checkpoint questions (20)

1. Name the three kinds of measurable.
2. What are the four health check states?
3. What are the default severities for FAIL, UNKNOWN and PASS?
4. How can a health check script override its severity?
5. What do AlertLevel count, max and sum show?
6. State the four trigger launch options.
7. Why can the first sample never fire Enter?
8. How many pre-defined triggers exist and what do they do?
9. What is the default sampling period in the basic example?
10. What is the difference between `CPUUser` and `CPUUsage`?
11. What does `validate` warn about?
12. Which built-in actions run on the head node and which on the node?
13. Which actions are hard power actions?
14. What is `post-drain-actions` for?
15. How are GPU metric names written for one GPU?
16. How does a DCGM WARN appear by default and how do you change it?
17. What does the default `hour` consolidator keep?
18. In what increment does the raw monitoring store grow?
19. When should offloaded monitoring be considered?
20. Why does the recommended remediation design cap reimages?

## 13. Sources and review notes

- **BCM 11 Administrator Manual:** chapter 10 (10.1 basic example; 10.2 concepts and 10.2.11 Base View top-right icons; 10.3 Base View monitoring window and regex/path filters; 10.4 Base View configuration of data producers, RLE, `Fuzzy offset`, `Only when idle`, cumulative metrics, consolidator equations, action `Allowed time` syntax, triggers, `post-drain-actions`, standalone entities, and 10.4.9 PromQL queries; 10.5.2 consolidators; 10.6 on-demand sampling, health overview, action history, pickup intervals; 10.7 offloaded monitoring; 10.8 User Portal `cm-webportal` and `common-credentials.json`; 10.9 AWS Cloud Job Tagging; 10.10 Events, `/var/spool/cmd/eventbucket`, `/tmp/eventbucket`, and fd 3 InfoMessages), appendix G (GPU metrics, health checks, Redfish checks, actions), 14.8 (monitoring data storage).
- **NVIDIA-DevOps notes**, volume 10 chapter 13: the health check, trigger and action pipeline and the remediation tiers; the notes say the tiers are a design recommendation, not a BCM feature. The Xid mapping there is a catalog matter I did not re-check.
- **Not read in depth:** GNSS location monitoring (10.11, skimmed), monitoring report queries and NVSM/Syslog sections (10.12 to 10.14), job monitoring, accounting and chargeback chapters (chapters 11 to 13 of the Administrator Manual), the full metrics tables (InfiniBand, NFS, IPMI, Redfish, Kubernetes, NetQ), Mission Control's extra GB200 metrics.
- **Run here:** `monitoring_lab.py` (46 checks): severities and AlertLevel, trigger firing rules and flapping, the flapping arithmetic, validate, consolidation retention, scale advice, GPU check names, DCGM WARN handling, the remediation chain and its loop cap, plus (`added in the gap pass`) `Fuzzy offset` spread window, consolidator `t_raw_gone` / `t_consolidation` / `t_consolidation_gone` equations and `Kind`-change discard, User Portal URL/package/CGI rules, AWS cloud job tags, `events` default flags, and `/var/spool/cmd/eventbucket` / `/tmp/eventbucket` / fd 3 InfoMessage parsing.
- **My own choices, not the manual's:** the numeric value of "notice" (10); the flapping arithmetic; the remediation chain (the notes' recommendation, implemented as written).
- **Not verified:** everything about a real BCM system.
