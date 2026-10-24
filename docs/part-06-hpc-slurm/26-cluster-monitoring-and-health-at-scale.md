---
id: "c06-26"
title: "6.26 Cluster monitoring and health at scale"
sidebar_label: "6.26 Cluster monitoring and health at scale"
sidebar_position: 26
description: "Monitoring a GPU cluster: from SNMP, Ganglia, Nagios and Zabbix to Prometheus/Grafana, what to measure (node, GPU via DCGM, fabric, storage, Slurm, facility), exporters, alert design and runbooks, health checks and security scans, XDMoD-style usage analytics; with a tested Slurm exporter and an alert-rule checker validated against dcgm-exporter's metric list"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.26 Cluster monitoring and health at scale

| | |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | A cluster or VM stack with Prometheus; GPU node for DCGM |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. **Run**: `code/part06/slurm_exporter.py --selftest` (parser and metric rendering against canned `sinfo`/`squeue` output, `prometheus-client` library; output shown) and `check_alert_rules.py` on `alerts_gpu_cluster.yml` (9 rules, DCGM metric names cross-checked against `etc/default-counters.csv` from NVIDIA/dcgm-exporter commit `fafd151`, 2026-09-18; a deliberately broken copy was caught). **Not run**: Prometheus itself (`promtool` unavailable), Slurm, DCGM, Grafana, any real cluster. The `sinfo -O` fixed-width field format and `squeue -o` specifiers were checked against the Slurm man pages; the real command output was not captured. Labs **untested** |

## Why this matters for AI infrastructure

Monitoring is how a 2,000-GPU cluster stays a cluster instead of a heap of expensive, silently failing parts. It answers four different questions: *Is it up?* (health), *Is it healthy?* (errors, thermals, fabric), *Is it used well?* (utilisation, queue, goodput) and *Is it going to fail?* (trends, predictive signals). It also feeds chargeback, capacity planning and incident analysis. The signals are different from web services: GPU errors (Xid, ECC, remapped rows), NVLink and InfiniBand counters, thermal throttling, power, storage latency, scheduler state.

## Prerequisites and outcomes

Needs 6.2, 6.8 to 6.14, Part 2. After this chapter you can:

- Place the classic tools (SNMP, Ganglia, Nagios, Zabbix, XDMoD) and the modern Prometheus stack, and say what each is good at.
- Define a monitoring plan by layer: facility, node, GPU, network fabric, storage, scheduler, application.
- Collect GPU metrics with DCGM and `dcgm-exporter`; know the key fields and how to interpret them.
- Write, test and route alerts that page for the right things; link alerts to runbooks and automatic remediation.
- Combine monitoring with health checks (6.14) and security scans; build usage reports.
- Scale the stack: cardinality, retention, federation, long-term storage.

## 1. The tool landscape

The SCL book (chapter 19, "Cluster Status Monitoring Systems") surveys the generations:

| Tool | Idea | Today |
|---|---|---|
| **SNMP** (Simple Network Management Protocol, 1988; v1, v2c, v3) | Poll devices' management information bases (MIBs) for counters and settings; the de facto standard for switches, PDUs, UPSes. v1 has short counters, poor security, no encryption; v2c (community strings) is the most common; v3 adds authentication and encryption | Still the way to read many network and power devices; exported to Prometheus via `snmp_exporter` |
| **Ganglia** | Lightweight multicast/unicast daemons (`gmond`), aggregators (`gmetad`), RRD storage, web UI; designed for clusters | Largely historic, simple and scalable for its time |
| **Nagios** (and forks Icinga, Naemon) | Check-based monitoring: plugins return OK/WARN/CRIT/UNKNOWN, with notifications and dependencies | Common for host/service up-down checks and legacy estates |
| **Zabbix** | Agent plus server with templates, auto-discovery, triggers, graphs, SQL backend | Popular all-rounder, strong in enterprises |
| **XDMoD** | Open XDMoD (XSEDE/ACCESS) analyses accounting data (scheduler logs, performance data) into usage and efficiency reports | Used by HPC centres for utilisation reporting, chargeback, job performance |
| **Prometheus + Grafana** (the "modern approach") | Pull-based metrics scraped from exporters, labels instead of hierarchies, PromQL, alert manager, dashboards | De facto standard for AI/cloud-native clusters |
| **DCGM / dcgm-exporter** | NVIDIA's data-centre GPU manager and its Prometheus exporter | GPU-specific telemetry and diagnostics |
| **Commercial/vendor** | BCM monitoring, Datadog, Splunk, NVIDIA UFM (fabric), Mission Control | Integrated stacks |

The book's "Healthchecks" and "Security Scans" sections complete the picture (below), and "lm_sensors/hwmon", "IPMI" and "APCUPS/NUT" cover the in-band and out-of-band hardware sensors and UPS monitoring.

## 2. What to monitor, by layer

| Layer | Signals | Source |
|---|---|---|
| **Facility** | Rack inlet/outlet temperature, humidity, PDU power per outlet, UPS state, CDU coolant temperature/flow/pressure, leak sensors | SNMP/Modbus/BACnet to PDUs, CDUs; UPS monitoring with APCUPS (`apcupsd`, which can also trigger orderly shutdown scripts) or NUT (Network UPS Tools); BMC sensors |
| **Node** | CPU load, memory, swap, disk space/IO, temperatures, fan speeds, power, kernel errors (`dmesg`, EDAC ECC), clock sync, services | `node_exporter` (+ textfile collector), `lm_sensors`/hwmon, IPMI/Redfish (`ipmi_exporter`, Part 7), journald |
| **GPU** | Utilisation, memory used, SM/memory clocks, power, temperature, **Xid errors**, ECC and **row remapping**, throttle reasons, NVLink bandwidth and errors, PCIe replay, tensor-pipe activity (profiling) | DCGM, `dcgm-exporter`, `nvidia-smi` |
| **Fabric** | Port state, link speed/width, symbol errors, link-down events, congestion (PFC/ECN counters), adaptive-routing, bandwidth per port | UFM, `ibstat`/`perfquery`, `node_exporter` InfiniBand collector, switch telemetry (Part 12) |
| **Storage** | Server health, OST/MDT utilisation, client latency/throughput, metadata ops, quotas, rebuilds | Lustre/GPFS/WEKA exporters, `lfs df`, `nfsiostat` (6.18 to 6.20) |
| **Scheduler** | Node states, drain reasons, queue length and wait time by partition, utilisation, failed jobs, controller RPC rate and backfill cycle | Slurm exporter, `sdiag`, `sacct` (6.14) |
| **Jobs/application** | Per-job GPU utilisation and efficiency, step time, tokens/s, loss, checkpoint duration, data-loader stalls | DCGM job mapping, framework metrics, MLflow/W&B, Slurm accounting |
| **Security** | Auth failures, new keys, privilege changes, image/package vulnerabilities, open ports | Audit logs, scanners (below) |

The Golden Rule: **alert on symptoms that need human action; graph everything else.** A GPU at 99 C might be fine for a minute; a rack at 40 percent of GPUs with Xid 79 is an incident.

## 3. GPU metrics with DCGM

`dcgm-exporter` exposes DCGM fields on `:9400/metrics`, configured by a CSV of counters. The default CSV in NVIDIA/dcgm-exporter (`etc/default-counters.csv`) includes, as read from the repository: `DCGM_FI_DEV_SM_CLOCK`, `DCGM_FI_DEV_MEM_CLOCK`, `DCGM_FI_DEV_GPU_TEMP`, `DCGM_FI_DEV_MEMORY_TEMP`, `DCGM_FI_DEV_POWER_USAGE`, `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` (counter, mJ), `DCGM_FI_DEV_PCIE_REPLAY_COUNTER`, `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_MEM_COPY_UTIL`, `DCGM_FI_DEV_ENC_UTIL`/`DEC_UTIL`, `DCGM_FI_DEV_XID_ERRORS` ("value of the last XID error encountered"), `DCGM_FI_DEV_FB_FREE`/`FB_USED`/`FB_RESERVED` (MiB), `DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL`, `DCGM_FI_DEV_UNCORRECTABLE_REMAPPED_ROWS`, `DCGM_FI_DEV_CORRECTABLE_REMAPPED_ROWS`, `DCGM_FI_DEV_ROW_REMAP_FAILURE`, `DCGM_FI_DRIVER_VERSION` (label), and profiling fields `DCGM_FI_PROF_GR_ENGINE_ACTIVE`, `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`, `DCGM_FI_PROF_DRAM_ACTIVE`, `DCGM_FI_PROF_PCIE_TX_BYTES`/`RX_BYTES`. A larger set is in `dcp-metrics-included.csv`.

Interpretation tips: **`GPU_UTIL`** is the fraction of time any kernel was running, not how efficiently the SMs are used; a job can show 100 percent util while tensor cores idle. `PIPE_TENSOR_ACTIVE` and `DRAM_ACTIVE` indicate real efficiency (low tensor activity with high DRAM activity means memory-bound). `XID_ERRORS` shows the *last* Xid number (a gauge); alert on non-zero and keep the history in logs. Remapped rows and a failed remap are RMA signals. Temperature plus power plus clocks reveal throttling. Always include the job-to-GPU mapping labels (DCGM can map GPUs to Kubernetes pods; for Slurm map via `SLURM_JOB_GPUS`/cgroup or a prolog-written file consumed by the textfile collector) to attribute usage to users and projects.

Beyond metrics, **DCGM diagnostics** (`dcgmi diag -r 1|2|3`, from knowledge) run active tests (level 1 quick, higher levels stress memory, PCIe and compute): use them in health checks before jobs, not as continuous monitors (6.14).

## 4. A Slurm exporter (tested)

Maintained exporters exist (the community `prometheus-slurm-exporter` family and others); the point of `code/part06/slurm_exporter.py` is to show what such an exporter does and how to test its parser without a cluster. It runs

```text
sinfo -h -N -O "NodeList:32,StateLong:20,Gres:40,GresUsed:60,Reason:80,Partition:24"
squeue -h -o "%T|%P|%u|%D"
```

(`-O` fields `NodeList`, `StateLong`, `Gres`, `GresUsed`, `Reason`, `Partition` and the `-o` specifiers `%T %P %u %D` were verified in the `sinfo(1)` and `squeue(1)` man pages), parses fixed-width columns, de-duplicates nodes that appear in several partitions, extracts GPU counts from GRES strings such as `gpu:h100:8(S:0-1)`, classifies drain reasons (`gpu`, `network`, `storage`, `prolog`, `unresponsive`, `unkillable`...), and renders metrics with `prometheus_client`. The self-test uses six canned node rows (one node listed in two partitions; one with a GPU Xid reason; one down and not responding) and four jobs, asserts the aggregation, and printed:

```text
slurm_nodes{state="allocated"} 1.0
slurm_nodes{state="mixed"} 1.0
slurm_nodes{state="drained"} 1.0
slurm_nodes{state="down"} 1.0
slurm_nodes{state="idle"} 1.0
slurm_node_drain_reason{reason_class="gpu"} 1.0
slurm_node_drain_reason{reason_class="unresponsive"} 1.0
slurm_gpus{status="total"} 40.0
slurm_gpus{status="allocated"} 11.0
slurm_jobs{partition="gpu",state="running"} 1.0
slurm_jobs{partition="gpu",state="pending"} 2.0
slurm_jobs{partition="debug",state="running"} 1.0
slurm_exporter_scrape_ok 1.0
selftest passed
```

Design lessons embedded in it: expose *state counts*, not per-job series (cardinality); put the controller-load cost in perspective (every scrape runs `sinfo` and `squeue` against `slurmctld`: scrape every 30 to 60 seconds, never every second; this is the same RPC load issue as users running `watch squeue`, 6.14); emit a `scrape_ok` gauge so a dead exporter pages; treat unknown output formats as scrape failures rather than silently reporting zeros. Limits of this demo: it was not run against real `sinfo` output (the fixed-width format and node-state suffixes vary by version), it does not report per-user usage, and it parses CLI text rather than using the REST API (`slurmrestd`, 6.15), which is more robust for production.

## 5. Alerting

Principles:

1. **Page on user-visible or capacity-threatening symptoms**; ticket on degradations; graph the rest. A paged alert must be actionable at 3 a.m. and have a runbook.
2. **Use `for:` durations** to avoid flapping; group related alerts; inhibit lower-level alerts when a higher-level cause is firing (rack power loss should not page 32 nodes).
3. **Cardinality and labels**: hostname, GPU index, rack, partition; never user-supplied free text as a label.
4. **Alert on absence**: `absent()` for exporters; heartbeat ("dead man's switch") alerts to verify the alert path itself.
5. **Link to remediation**: annotations with runbook URL; automatic drain via webhook for known hardware faults (Alertmanager to a service that calls `scontrol update ... state=drain reason=...`; test for loops and false positives; 6.14 and 5.32 discuss the safety properties such automation needs: budgets, dry-run, provenance of what you changed).
6. **Review weekly**: delete alerts nobody acts on; measure alert precision.

`code/part06/alerts_gpu_cluster.yml` is an illustrative rule file with nine alerts across three groups: `GpuXidError` (any non-zero last-Xid for 1 minute), `GpuRowRemapFailure`, `GpuHot` (> 85 C for 10 minutes), `AllocatedGpuIdle` (30-minute average utilisation under 5 percent while GPUs are allocated), `SlurmNodesDrainedHigh` (> 5 percent drained/down for 15 minutes), `SlurmExporterDown`, `GpuQueueBacklogWhileIdle` (many pending GPU jobs while more than 16 GPUs idle: a policy or fragmentation problem), `TmpFull`, `IbPortDown`. `check_alert_rules.py` loads the YAML and checks structure, duplicate names, bracket balance, severity labels, required `summary` and `runbook` annotations, paging rules needing `for:` (with an exception for the row-remap failure which is a discrete, severe event), and that every `DCGM_FI_*` name appears in the exporter's counters CSV. On the rule file: `9 rules in 3 groups` and no problems. On a copy with `DCGM_FI_DEV_GPU_TEMP` mistyped as `DCGM_FI_DEV_GPU_TEMPERATURE > (85`:

```text
9 rules in 3 groups
PROBLEM GpuHot: unbalanced brackets in expr
PROBLEM GpuHot: DCGM_FI_DEV_GPU_TEMPERATURE is not in the dcgm-exporter counters file
```

This is a lint, not PromQL validation: run `promtool check rules` and unit-test rules with `promtool test rules` in CI. Several thresholds are guesses to be tuned (the 85 C limit depends on the GPU model's slowdown and shutdown temperatures; the idle test depends on workload; join keys such as `Hostname` depend on your relabelling; the `AllocatedGpuIdle` expression joins DCGM series with a Slurm series that does not carry a `Hostname` label in the demo exporter, so it needs per-node labels to work as written).

## 6. Health checks, scans, and active testing

- **Passive monitoring** tells you what already happened; **active health checks** (6.14: `node_health.sh`, NHC, DCGM diagnostics, NCCL pair tests) find latent faults before a job does. Schedule short checks on every node frequently and deep checks on idle nodes; feed results to the same alerting system.
- **Burn-in and acceptance**: stress tests (CPU, memory, GPU, network, storage) on new hardware (6.28).
- **Security scans**: the book lists regular scans as part of monitoring. Vulnerability scanning of images and packages (Trivy, Grype, OpenSCAP), port scans of internal ranges to detect unexpected services (`nmap`), configuration audits (the `sshd_audit.py` idea from 6.25), integrity monitoring (AIDE), log analysis for auth anomalies, container image provenance (5.22, Part 18). Treat scan results as inputs to the same ticketing and SLO process.
- **Out-of-band**: BMC sensors, SEL logs, Redfish events (Part 7) catch problems when the OS is dead.

## 7. Usage and efficiency analytics

Utilisation questions are a different kind of monitoring: *Who used which resources, how well, at what cost?* Sources: Slurm accounting (`sacct`, `sreport`, 6.9), job-level GPU metrics (DCGM job stats or per-job exporters), XDMoD-style tools combining accounting with performance data. Reports: cluster utilisation (allocated vs total GPU-hours), efficiency (average GPU utilisation of allocated GPUs; a classic finding is many allocated GPUs below 20 percent), wait times by queue, failure causes (`NODE_FAIL`, OOM, timeout), top users/projects, storage growth. Use them to right-size allocations, steer users to MIG for small jobs (6.10), plan capacity, and justify spend. Publish dashboards to users: transparency reduces wasteful allocation.

## 8. Scaling the monitoring stack

- **Cardinality**: per-GPU, per-port, per-job series multiply (2,000 GPUs x 30 fields x 15-second scrapes). Drop unused fields (CSV), aggregate with recording rules, keep per-job series out of Prometheus (use accounting).
- **Topology**: one Prometheus per cluster or per failure domain with remote-write or federation to a central long-term store (Thanos, Mimir, VictoriaMetrics); 15 to 30 s scrape intervals for GPU metrics, 60 s for slow signals; retention tiers.
- **Reliability of the monitor**: redundant Prometheus pairs, external dead-man's-switch, monitoring network separate from the data plane (so you can see during a fabric outage), time sync (6.18).
- **Logs and traces**: journald/syslog forwarding (Loki, Elasticsearch), structured logs from prolog/epilog/health scripts, kernel log filtering for Xid/ECC/MCE lines, central retention.
- **Exporter hygiene**: pin versions, run as non-root, bind to the management network, authenticate if remote, avoid scraping `slurmctld` too often.
- **Cost**: storage for long retention of high-cardinality data is real; define retention by use.

## 9. Lab

Tested: 1) install `prometheus-client`, run `slurm_exporter.py --selftest`; add a drain reason class and a test; extend the parser to a second `sinfo` layout. 2) Run `check_alert_rules.py` on the rules file and on copies with deliberate mistakes; add rules for NVLink bandwidth and PCIe replay counters (look up names in `dcp-metrics-included.csv`). 3) Write a recording rule for per-partition GPU utilisation efficiency (sketch).

Untested: 4) deploy `node_exporter` and `dcgm-exporter` on a GPU node, scrape with Prometheus, build a Grafana dashboard (utilisation, tensor activity, power, temperature, Xid). 5) Run `promtool check rules` and `promtool test rules` on the file. 6) Configure Alertmanager routes (page, warn, ticket) and an inhibition rule for rack power loss. 7) Wire a webhook that drains a node on `GpuXidError` in dry-run mode first. 8) Build an efficiency report from `sacct` and DCGM job stats. 9) Run a fabric congestion test and watch counters.

## 10. Interview angles

- What would you monitor on a 1,000-GPU training cluster, by layer, and what would page?
- What does `DCGM_FI_DEV_GPU_UTIL` really measure? Which fields show real efficiency?
- How do you attribute GPU usage to Slurm jobs and projects?
- Design alerting that avoids pages for symptoms with a known upstream cause.
- How do you scale Prometheus for tens of thousands of GPUs?
- SNMP v2c versus v3? Where is SNMP still necessary?
- How would you detect an allocated-but-idle GPU problem and what would you do about it?
- How do monitoring and health checks differ and how do they cooperate?
- A node shows Xid 79 once. What do you do?

## 11. Checkpoint questions (30)

1. List the four questions monitoring answers.
2. Compare SNMP versions 1, 2c and 3.
3. What were Ganglia and Nagios designed for?
4. What does XDMoD report?
5. What is the "modern approach" stack?
6. Name facility, node, GPU, fabric, storage and scheduler signals.
7. What is the golden rule of alerting?
8. Which DCGM field shows the last Xid and what type is it?
9. What does `GPU_UTIL` hide?
10. Which fields indicate tensor-core and memory activity?
11. How do row-remap fields relate to RMA?
12. How do you map GPUs to Slurm jobs?
13. What does `dcgmi diag` do and when should it run?
14. Which `sinfo -O` fields does the exporter use?
15. Why de-duplicate nodes across partitions?
16. Why export state counts rather than per-job series?
17. What scrape interval is reasonable for Slurm state?
18. What is a scrape_ok gauge for?
19. What does `for:` do in an alert?
20. What is an inhibition rule?
21. What is a dead-man's-switch alert?
22. What does `check_alert_rules.py` verify?
23. Why is `promtool` still needed?
24. Why join DCGM and Slurm series carefully?
25. How do active checks complement passive monitoring?
26. Name four kinds of security scans.
27. Which efficiency finding is common on GPU clusters?
28. How do you manage Prometheus cardinality?
29. What is long-term storage for?
30. How do you keep monitoring alive during a fabric outage?

## 12. Sources and review notes

- Monitoring system survey (SNMP, Ganglia, Nagios, Zabbix, "modern approach", XDMoD, lm_sensors/hwmon, IPMI, APCUPS/NUT, healthchecks, security scans): *Supercomputers for Linux SysAdmins* chapter 19, restated in my words (only the SNMP section text was re-read in detail; the rest follows the chapter's headings and general knowledge).
- DCGM exporter metrics: NVIDIA/dcgm-exporter `etc/default-counters.csv` (commit `fafd151`). Slurm CLI formats: `sinfo(1)`, `squeue(1)` man pages (SchedMD/slurm commit `521370b`).
- Original and run: `slurm_exporter.py`, `alerts_gpu_cluster.yml`, `check_alert_rules.py`.
- Unverified: node_exporter metric names used in the sample rules (`node_infiniband_port_state_id`, filesystem metrics), DCGM diag levels, tool versions and features of Ganglia/Nagios/Zabbix/XDMoD, thresholds, real `sinfo` output layout.
