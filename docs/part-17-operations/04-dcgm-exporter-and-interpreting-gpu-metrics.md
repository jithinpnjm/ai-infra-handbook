---
id: "c17-04"
title: "17.4 DCGM exporter and interpreting GPU metrics"
sidebar_label: "17.4 DCGM exporter and GPU metrics"
sidebar_position: 4
description: "DCGM exporter for GPU telemetry: the metric families (utilisation, memory, ECC, Xid, temperature, power, clocks), the GPU-specific PromQL queries, the alert thresholds, and the operational patterns that catch GPU failures before they cascade."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 17.4 DCGM exporter and interpreting GPU metrics

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Primary sources | NVIDIA Zero-to-Hero Volume 16 (`chapter-03-dcgm-exporter.md`, `chapter-04-interpreting-gpu-metrics.md`); NVIDIA Zero-to-Hero Volume 7 (`chapter-02-dcgm-and-gpu-metrics.md`); *Generative AI on Kubernetes* (`generative-ai-on-kubernetes`, Chapter 5); DCGM and DCGM exporter official documentation |
| Cross-references | Chapter 10.21 (GPU health: DCGM, ECC, Xid); Chapter 16.10 (Monitoring and drift); Chapter 17.2 (Prometheus and Grafana); Chapter 11 (GPU Kubernetes) |
| Coverage file | `planning/coverage/chapters/17-04.md` |
| Claim & number ledger | `planning/ledgers/17-04.md` |

## Why this matters for AI infrastructure

Picture a training job that stops making progress at three in the morning. Nothing has crashed, the logs are quiet, and the on-call engineer has no idea which GPU is failing. Without GPU metrics, the first sign of trouble is usually a stuck job or a failed inference request.

The DCGM exporter changes that. It turns "the job is stuck" into a specific finding, such as one GPU on one node logging memory errors. A stuck job also wastes GPU time you already paid for, and it can cost you a deadline. The exporter gives you a chance to act before that time is gone.

The metrics in chapter 17.2 are general. The metrics in this chapter are specific to the GPU, and the later chapters in this part assume they exist.

```text
Why the DCGM exporter is on the critical path (background reading: NVIDIA Zero-to-Hero volume 16; NVIDIA Zero-to-Hero volume 7; Generative AI on Kubernetes; the figures below are examples, not quotations):
- A single H100 GPU costs $3-5 per hour. A 100-GPU cluster costs $300-500 per hour.
  The cost of a stuck training job is the GPU-hours wasted plus the deadline
  missed. The DCGM exporter is what catches the failure before it costs the
  cluster an hour of GPU time.
- ECC errors are the GPU's leading indicator of hardware failure. A GPU
  that is correcting errors today is a GPU that will fail tomorrow. The DCGM
  exporter exposes the ECC error count; the alert catches the failure before
  the customer sees it.
- GPU memory pressure is the leading cause of CUDA OOM crashes. A model
  that fits in HBM today may not fit tomorrow if the memory pressure
  changes. The DCGM exporter exposes the memory utilisation; the alert
  catches the pressure before the crash.
```

Three things make this a platform-team concern rather than a data-science concern.

1. The exporter is your only window into GPU health. The platform team owns the deployment, so it also owns the blind spot if the exporter is missing.
2. GPU metrics are GPU-specific. A generic exporter such as cAdvisor or the node exporter does not expose GPU utilisation, ECC errors, Xid events or thermal throttling, so you must deploy the DCGM exporter separately.
3. GPU alert thresholds differ from CPU thresholds. A CPU at 90 percent can be perfectly healthy, while GPU memory at the same level can mean the next job runs out of memory.

**A GPU cluster without the DCGM exporter is a cluster the on-call engineer cannot debug, so deploy it before the first AI workload arrives.**

## Prerequisites and outcomes

### Prerequisites

- Chapter 10.21 (GPU health: DCGM, ECC, Xid) for the GPU health concepts.
- Chapter 16.10 (Monitoring and drift) for the monitoring patterns.
- Chapter 17.2 (Prometheus and Grafana) for the metrics stack.
- Chapter 11 (GPU Kubernetes) for the GPU device plugin.

### Outcomes

By the end of this chapter, you should be able to:

1. Deploy the DCGM exporter as a DaemonSet on every GPU node, and confirm that Prometheus receives its metrics.
2. Name the DCGM metric families and say what each one tells you.
3. Write PromQL queries for per-GPU utilisation, memory pressure, ECC errors and thermal throttling.
4. Set alert thresholds that catch GPU failures before they spread.
5. Read the DCGM metrics during an incident and explain what a spike means.
6. Run the DCGM exporter on GKE with clear SLOs, observability and a runbook.

---

## 1. The DCGM exporter

### 1.1 What DCGM is

Suppose you want the temperature, memory use and error count of every GPU in a cluster. Running `nvidia-smi` by hand works on one machine, but nobody can do it all day on every node. The Data Center GPU Manager (DCGM) is NVIDIA's library for doing this continuously. It runs on every GPU node and reports each GPU's health, utilisation and performance, so other tools can read those numbers.

*AI Systems Performance Engineering*, chapter 2, makes the same point. It describes DCGM tracking per-GPU utilisation, memory usage, temperature and NVLink throughput.

The DCGM exporter is the bridge from DCGM to Prometheus. It runs as a DaemonSet, reads the DCGM metrics, and publishes them in the Prometheus exposition format. Prometheus scrapes that endpoint, and Grafana draws its dashboards from what Prometheus stores.

```mermaid
flowchart LR
    GPU[NVIDIA GPU<br/>utilisation, memory, ECC, Xid]
    DCGM[DCGM<br/>system library]
    E[DCGM exporter<br/>:9400/metrics]
    P[Prometheus]
    G[Grafana]

    GPU --> DCGM --> E --> P --> G
```

### 1.2 Deploying the DCGM exporter

You install the exporter with Helm, on the GPU nodes.

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm install dcgm-exporter nvidia/dcgm-exporter \
  --namespace monitoring --create-namespace \
  --set serviceMonitor.enabled=true \
  --set tolerations[0].key=nvidia.com/gpu \
  --set tolerations[0].operator=Exists \
  --set tolerations[0].effect=NoSchedule
# expected: the DCGM exporter pods are running on every GPU node; the metrics are scraped by Prometheus
```

The chart creates a DaemonSet, so each GPU node runs one exporter pod. The toleration lets that pod land on nodes tainted for GPU use. The exporter serves metrics on port 9400, and the ServiceMonitor tells Prometheus to scrape it.

*AI Systems Performance Engineering*, chapter 3, notes that the NVIDIA Kubernetes GPU Operator also sets up GPU monitoring with DCGM. If your cluster already runs that operator, check it before you install a second copy.

### 1.3 The DCGM metric families

The NVIDIA Zero-to-Hero Volume 16, chapter 3, and the DCGM exporter documentation go through these families in more detail.

| Family | Examples | What it measures |
|---|---|---|
| **Utilization** | `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_PROF_SM_ACTIVE`, `DCGM_FI_DEV_MEM_COPY_UTIL` | GPU SM utilisation, memory utilisation |
| **Memory** | `DCGM_FI_DEV_FB_USED`, `DCGM_FI_DEV_FB_TOTAL`, `DCGM_FI_DEV_FB_FREE` | HBM used, total, free |
| **Temperature** | `DCGM_FI_DEV_GPU_TEMP`, `DCGM_FI_DEV_MEMORY_TEMP` | GPU temperature |
| **Power** | `DCGM_FI_DEV_POWER_USAGE`, `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` | Power draw, energy |
| **Clocks** | `DCGM_FI_DEV_SM_CLOCK`, `DCGM_FI_DEV_MEM_CLOCK` | SM clock, memory clock |
| **ECC** | `DCGM_FI_DEV_ECC_DBE_AGG_TOTAL`, `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL`, `DCGM_FI_DEV_ECC_SBE_AGG_TOTAL` | Double-bit errors (DBE), single-bit errors (SBE) |
| **Xid** | `DCGM_FI_DEV_XID_ERRORS` | NVIDIA Xid errors |
| **Retired pages** | `DCGM_FI_DEV_RETIRED_PENDING`, `DCGM_FI_DEV_RETIRED_DBE`, `DCGM_FI_DEV_RETIRED_SBE` | Pages retired due to errors |
| **NVLink** | `DCGM_FI_DEV_NVLINK_CRC_DATA_ERROR_TOTAL`, `DCGM_FI_DEV_NVLINK_CRC_DATA_ERROR_TOTAL` | NVLink CRC errors |
| **PCIe** | `DCGM_FI_DEV_PCIE_REPLAY_COUNTER` | PCIe replay count |

Each family answers its own question. Utilisation and memory show how much capacity is in use. ECC and Xid show hardware and driver health. Temperature and power show heat, clocks show throttling, and NVLink and PCIe show whether the links are healthy.

The field names were checked against the dcgm-exporter source, and that check turned up three points. `DCGM_FI_PROF_SM_ACTIVE` reports a ratio from 0 to 1, not a percentage, and not every exporter enables it by default. The retired-page family is `DCGM_FI_DEV_RETIRED_PENDING`, `DCGM_FI_DEV_RETIRED_DBE` and `DCGM_FI_DEV_RETIRED_SBE`. ECC counters end in `_TOTAL`, because an earlier draft used `_DEDUP` names that the exporter does not define.

---

## 2. Reading the GPU metrics

### 2.1 GPU utilisation

A GPU you pay for by the hour should be busy, and utilisation tells you whether it is. The GPU utilisation is the fraction of the GPU's SMs (streaming multiprocessors) that are in use.

```promql
# The current GPU utilisation per GPU
DCGM_FI_DEV_GPU_UTIL

# The average GPU utilisation across the cluster
avg(DCGM_FI_DEV_GPU_UTIL)

# The per-GPU utilisation over the last 5 minutes
avg_over_time(DCGM_FI_DEV_GPU_UTIL[5m])

# The utilisation per team (via Kubernetes labels)
sum by (team) (DCGM_FI_DEV_GPU_UTIL) by (gpu, team)
```

Read utilisation as a pattern over time, not as a single reading. *AI Systems Performance Engineering*, chapter 2, says training GPUs should sit near full utilisation most of the time. If they sit at 50 percent, something keeps them idle half the time, often a slow data loader or a synchronization point.

The draft's example values are 30 percent for under-use, 90 percent for over-use, and an alert when utilisation stays above 95 percent for 10 minutes. These are examples. Choose your own numbers for your workload.

### 2.2 GPU memory

High-bandwidth memory (HBM) is the GPU's own memory. When it runs out, a CUDA job fails with an out-of-memory error, which makes HBM a common cause of those crashes. Memory pressure is the early warning. A model that fits today can stop fitting when batch sizes or sequence lengths grow.

```promql
# The GPU memory utilisation per GPU
DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL

# The GPU memory pressure (utilisation > 90%)
DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL > 0.9

# The largest model in HBM
max by (gpu) (DCGM_FI_DEV_FB_USED)
```

Watch the ratio rather than the raw number. The 90 percent line in the example is a starting point. Pick the level that leaves your team enough time to act before a job fails.

### 2.3 ECC errors

Error-correcting code (ECC) is the memory's built-in repair. *AI Systems Performance Engineering*, chapter 3, explains that ECC fixes single-bit errors as they happen and detects double-bit errors, raising them to the calling code. ECC is on by default on data center GPUs, and the book advises keeping it on for serious AI work.

Many teams treat a rising error count as an early warning. The rate that matters for your fleet is one you have to set and check yourself.

```promql
# The ECC double-bit errors (DBE) per GPU over the last hour
sum by (gpu) (increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[1h]))

# The ECC single-bit errors (SBE) per GPU over the last hour
sum by (gpu) (increase(DCGM_FI_DEV_ECC_SBE_VOL_TOTAL[1h]))

# The retired pages (DBE) per GPU
DCGM_FI_DEV_RETIRED_DBE

# The alert: any DBE in the last hour
sum by (gpu) (increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[1h])) > 0
```

The draft treats a single double-bit error as critical and calls for replacing the GPU. It warns on single-bit errors and says the GPU should be scheduled for replacement once that rate stays high. The example rate in the draft is 100 per hour, so treat it as a starting value.

### 2.4 Xid errors

Xid errors are NVIDIA's driver-level error codes. Each code points to a class of problem, so the code tells you which runbook section to open.

```promql
# The Xid errors per GPU
DCGM_FI_DEV_XID_ERRORS

# The distinct Xid codes per GPU
count by (gpu) (DCGM_FI_DEV_XID_ERRORS)
```

The draft alerts on every Xid error. Its common codes are 31 for a GPU memory page fault, 43 for a GPU that stopped responding, 48 for a double-bit ECC error and 63 for ECC page retirement. Whatever you alert on, the runbook should say what to do for each code.

### 2.5 Temperature and power

Heat is a quiet cause of slow jobs. A GPU that runs hot lowers its clock to protect itself, and the job slows down without raising an error. Temperature and power metrics let you see that before a deadline slips.

```promql
# The current GPU temperature
DCGM_FI_DEV_GPU_TEMP

# The power usage
DCGM_FI_DEV_POWER_USAGE

# The thermal throttle indicator
DCGM_FI_DEV_GPU_TEMP > 85
```

The draft's example lines are 85 degrees for a warning, 90 for throttling and 95 for critical. They are example values, not manufacturer limits, so check your GPU's documented thresholds first. The draft also says power draw above the rated TDP for your GPU model points to power supply problems.

### 2.6 Clocks

The clocks are the SM clock and the memory clock, and they show whether a GPU is running at the speed you expect. *AI Systems Performance Engineering*, chapter 3, explains that GPU Boost moves the core clock up and down to stay within power and thermal limits. A clock below base usually means the GPU is being held back by heat or power.

```promql
# The current SM clock
DCGM_FI_DEV_SM_CLOCK

# The memory clock
DCGM_FI_DEV_MEM_CLOCK

# The clock reduction (throttling indicator)
DCGM_FI_DEV_SM_CLOCK < 1400  # H100 base clock is 1.4 GHz
```

The 1400 threshold in the example is a base-clock value for one model. Confirm your model's base clock before you use it. The draft alerts when the clock stays below base for 10 minutes, and that duration is an example too.

---

## 3. GPU-specific alerting

Dashboards help only when someone is looking at them. Alerts make the platform tell you when a GPU needs attention. The rules below turn the metrics from section 2 into alerts.

### 3.1 The alert rules

Each rule has an expression, a `for` time that the condition must hold before the alert fires, and a severity label. The `for` times and thresholds in this file are example values, so adjust them to your fleet before you rely on them.

```yaml
# code/part17/gpu_alerts.yaml
groups:
  - name: gpu_health
    interval: 30s
    rules:
      - alert: GPUHighUtilization
        expr: avg by (gpu, node) (DCGM_FI_DEV_GPU_UTIL) > 95
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} is over-utilised"

      - alert: GPUMemoryPressure
        expr: DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} is under memory pressure"

      - alert: GPUDoubleBitECCError
        expr: sum by (gpu, node) (increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[1h])) > 0
        labels:
          severity: critical
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} has DBE errors"

      - alert: GPUSingleBitECCErrors
        expr: sum by (gpu, node) (increase(DCGM_FI_DEV_ECC_SBE_VOL_TOTAL[1h])) > 100
        labels:
          severity: warning
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} has SBE errors"

      - alert: GPUXidError
        expr: DCGM_FI_DEV_XID_ERRORS > 0
        labels:
          severity: critical
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} has Xid errors"

      - alert: GPUThermalThrottle
        expr: DCGM_FI_DEV_GPU_TEMP > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} is thermal-throttling"

      - alert: GPUClockThrottle
        expr: DCGM_FI_DEV_SM_CLOCK < 1400
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} is clock-throttling"
```

*Production Kubernetes*, chapter 9, warns against over-alerting. Too many critical alerts burn out on-call engineers, and the noise can bury the real incident. Keep the critical list short, and send the rest to a warning channel. The same chapter also suggests a heartbeat alert, one that fires all the time under normal conditions and pages you when it stops.

### 3.2 The recovery steps

Each alert needs a first action, so the on-call engineer is not guessing in the middle of an incident. The table gives the first step for each rule. The runbook holds the details, and a runbook that lists these steps usually shortens the incident.

| Alert | Recovery step |
|---|---|
| GPUHighUtilization | Scale the workload; add a GPU; reduce the batch size |
| GPUMemoryPressure | Reduce the model size; enable gradient checkpointing; move to a larger GPU |
| GPUDoubleBitECCError | Drain the node; replace the GPU; investigate the workload |
| GPUSingleBitECCErrors | Schedule the GPU for replacement; monitor for DBE escalation |
| GPUXidError | Check the runbook for the specific Xid code; restart the workload if safe |
| GPUThermalThrottle | Check the cooling system; reduce the workload's power draw |
| GPUClockThrottle | Check the power supply; reduce the workload's clock |

---

## 4. Operating the DCGM exporter on GKE

### 4.1 The components

Four pieces make up this stack, and each one can fail on its own. The table shows where each piece runs and the service target the draft uses for it.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| DCGM | System library on every GPU node | (no backing store) | (no SLO; system library) |
| DCGM exporter | DaemonSet on every GPU node | (exposes metrics) | Scrape latency p99 < 5 s |
| Prometheus | Kubernetes Deployment | TSDB | Scrape latency p99 < 5 s |
| Grafana | Kubernetes Deployment | (uses Prometheus) | Dashboard load p99 < 5 s |

The SLO column holds example targets, not values from a source. Your team should choose its own targets and measure against them.

### 4.2 IAM and the cardinality budget

Every new time series costs Prometheus memory and storage, so count them before you deploy. The exporter adds many series, because each GPU reports many metrics. *Production Kubernetes*, chapter 9, warns that every label you add increases the load on Prometheus. Learn the effect of high cardinality before you add labels to these metrics.

| Metric family | Cardinality per cluster | Budget impact |
|---|---|---|
| Utilisation, memory, temperature, power | ~12 metrics × 8 metrics per GPU × 1000 GPUs = 96,000 series | Low |
| ECC, Xid | ~6 metrics × 1000 GPUs = 6,000 series | Low |
| NVLink, PCIe | ~10 metrics × 1000 GPUs = 10,000 series | Low |
| Retired pages | ~3 metrics × 1000 GPUs = 3,000 series | Low |

The counts in this table are rough estimates, not measurements. They add up to about 115,000 series for a 1000-GPU cluster. Compare that total with the budget in chapter 17.1 before you roll the exporter out.

### 4.3 Observability

The exporter is a service too, so it needs its own monitoring. The table lists what to watch and the example alert values. The restart alert matters most. An exporter in a restart loop stops publishing, and the GPU graphs stop updating without showing an error. A frozen graph can look like a healthy GPU unless you alert on the silence.

| Metric | Why it matters | Alert |
|---|---|---|
| DCGM exporter scrape latency p99 | Hot path for every GPU metric | > 10 s |
| DCGM exporter pod restarts | DCGM exporter is unhealthy | > 0 for 1 hour |
| GPU node CPU usage | DCGM exporter overhead | > 50% for 1 hour |
| GPU node memory usage | DCGM exporter overhead | > 80% for 1 hour |

The alert values in this table are examples. Set your own after you have watched normal numbers on your cluster for a while.

---

## 5. How it fails

Six failures come up again and again. For each one, the symptom is what you notice first, the diagnosis is the likely cause, and the fix is what to do next.

### 5.1 "The DCGM exporter is not running on a GPU node"

**Symptom:** The Prometheus target for the GPU node is missing, so that node's GPU metrics are missing too.

**Diagnosis:** The exporter's DaemonSet toleration probably does not match the node's taint, so the pod never lands on the node.

**Fix:** Compare the toleration with the node's taint, confirm the pod runs on the node, and check that port 9400 serves metrics. Then add an alert for any GPU node that has no exporter.

### 5.2 "The DCGM exporter is consuming too much CPU"

**Symptom:** The exporter pod is throttled, so its metrics arrive late and you cannot see GPU problems in time.

**Diagnosis:** The metrics are scraped often, and the pod's CPU limit is probably too low for that load.

**Fix:** Raise the CPU limit or lengthen the scrape interval. Then confirm the metrics still arrive within your latency target.

### 5.3 "The GPU is in ECC error storm"

**Symptom:** The double-bit error counter climbs quickly, which means something on the GPU is failing badly.

**Diagnosis:** The GPU probably has a hardware fault and must be replaced.

**Fix:** Drain the node and replace the GPU. Check the workload's output for damage, and add the GPU to your list of retired GPUs.

### 5.4 "The GPU is thermal-throttling"

**Symptom:** The temperature stays above your alert line, and the SM clock falls below base.

**Diagnosis:** The likely causes are a cooling fault, a workload that draws more power than the node can cool, or a data-centre cooling shortfall.

**Fix:** Check the cooling system, reduce the workload's power draw, or move the job to a cooler node.

### 5.5 "The DCGM exporter metrics are stale"

**Symptom:** The Prometheus target is up, but the values have not changed for hours.

**Diagnosis:** The exporter may be running without reading fresh values from DCGM. The cause then sits lower in the stack, in DCGM or the kernel driver.

**Fix:** Restart the exporter pod first. If the values stay frozen, restart the DCGM system library and check the kernel driver logs.

### 5.6 "The DCGM exporter is missing the high-cardinality labels"

**Symptom:** You cannot query the metrics by team or model, because the labels are missing.

**Diagnosis:** The exporter may lack the access it needs to read Kubernetes labels. A missing service account or role binding is the first thing to check.

**Fix:** Verify the service account and the role binding, restart the pod, and confirm the labels now appear.

---

## 6. Hands-on lab

This lab installs the DCGM exporter on GKE, checks that its metrics reach Prometheus, and builds the GPU dashboard and alerts. The lab is **untested** in this repository.

### 6.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+) with at least 1 H100 or A100 GPU node. Check the version against the GKE release you actually run.
- Helm 3 for installing the DCGM exporter.
- Prometheus installed (Chapter 17.2).

### 6.2 Step 1: install the DCGM exporter

Install the chart with the same settings as section 1.2. The expected result is one exporter pod on each GPU node.

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm install dcgm-exporter nvidia/dcgm-exporter \
  --namespace monitoring --create-namespace \
  --set serviceMonitor.enabled=true \
  --set tolerations[0].key=nvidia.com/gpu \
  --set tolerations[0].operator=Exists \
  --set tolerations[0].effect=NoSchedule
# expected: the DCGM exporter pods are running on every GPU node
```

### 6.3 Step 2: verify the metrics are flowing

Open a port-forward to Prometheus and ask it for one metric. A value in the answer means the pipeline works from the GPU all the way to the database.

```bash
# Port-forward to Prometheus
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Query the GPU utilisation
curl -s 'http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL' | jq .
# expected: the GPU utilisation per GPU
```

### 6.4 Step 3: build the GPU dashboard

Load the dashboard JSON into a ConfigMap, then import it into Grafana. Use the Grafana credentials for your own instance, not the example ones in the command. The dashboard should then open at the path the last command names.

```bash
# Apply the dashboard JSON
kubectl -n monitoring create configmap gpu-dashboard \
  --from-file=dashboards/gpu.json

# Reload Grafana
curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/gpu-import.json
# expected: the dashboard is available at /d/gpu/ai-factory-gpu
```

### 6.5 Step 4: add the GPU alert rules

Store the rules in a ConfigMap, then tell Prometheus to reload them. The file in this command is `configs/gpu_alerts.yaml`, while the rules in section 3.1 live under `code/part17/`, so check which copy you are using.

```bash
# Apply the alert rules
kubectl -n monitoring create configmap gpu-alerts \
  --from-file=configs/gpu_alerts.yaml

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
# expected: the alert rules are active
```

### 6.6 Step 5: simulate a GPU failure

This command only reads the ECC counters. It shows the current error counts, and it cannot create errors. Run it on a test GPU only, never in production, and do not expect it to trigger the alert.

```bash
# Read the ECC counters (this cannot inject errors)
nvidia-smi -q -d ECC
# expected: the current ECC error counts are printed; on a healthy GPU they are zero
```

### 6.7 Step 6: verify the alert fires

Ask Alertmanager which alerts are active. On a healthy GPU, the double-bit alert should not appear, so this check mainly confirms that Alertmanager responds.

```bash
# Query Alertmanager
kubectl -n monitoring port-forward svc/alertmanager-operated 9093:9093 &
curl -s http://localhost:9093/api/v2/alerts | jq .
# expected: the GPUDoubleBitECCError alert is active
```

### 6.8 What to record

After the lab, you should be able to answer five questions in about five seconds each. The five seconds is an example target, not a standard.

1. What is the current GPU utilisation per GPU?
2. What is the current GPU memory pressure per GPU?
3. What is the current ECC error count per GPU?
4. What is the current GPU temperature per GPU?
5. What is the current GPU clock per GPU?

If any answer takes more than 30 seconds, the GPU exporter is not yet a production service. The 30-second figure is also an example, and the lab is still untested against a live GKE cluster.

---

## Exercises

Try these after the lab. Each one asks you to build something you could use on your own cluster.

1. **Add a GPU temperature dashboard.** Build a Grafana dashboard that shows temperature for each GPU. Alert when temperature passes a limit you choose. The draft's example is 85 degrees. *Solution sketch:* start from `DCGM_FI_DEV_GPU_TEMP`, add a Grafana panel, and write the alert rule.
2. **Add a retired-GPUs list.** Keep a list of GPUs retired because of ECC errors, and alert when a GPU joins it. *Solution sketch:* store the list in a ConfigMap, then write a Prometheus alert that compares the running GPUs against it.
3. **Add a per-team GPU cost.** Compute the GPU cost per team from the DCGM metrics, and feed the result into the FinOps dashboard from chapter 16.14. *Solution sketch:* multiply `DCGM_FI_DEV_GPU_UTIL` by `DCGM_FI_DEV_POWER_USAGE`, group the result by the team labels, and build the cost dashboard on top.
4. **Add a GPU health check.** Add a Kubernetes health check that fails when the DCGM exporter is missing from a GPU node. *Solution sketch:* a Kubernetes probe that calls the exporter's `/health` endpoint.
5. **Add a GPU utilisation histogram.** Emit GPU utilisation as a histogram, so the dashboards can show percentiles. *Solution sketch:* write a custom exporter that emits the histogram, then point the dashboards at it.
6. **Add a GPU NVLink error alert.** Alert when NVLink CRC errors pass 100 in an hour, and treat 100 as an example value. *Solution sketch:* a Prometheus alert on the `DCGM_FI_DEV_NVLINK_CRC_DATA_ERROR_TOTAL` metric.

---

## Checkpoint questions

<details><summary>1. What is the DCGM exporter?</summary>
It is the bridge from DCGM to Prometheus. It runs as a DaemonSet on every GPU node, reads the DCGM metrics, and exposes them in the Prometheus format, so Prometheus can scrape them and Grafana can graph them.
</details>

<details><summary>2. What is DCGM?</summary>
It is NVIDIA's Data Center GPU Manager. It is a system library that runs on every GPU node and exposes each GPU's health, utilisation and performance. The DCGM exporter reads its numbers from DCGM.
</details>

<details><summary>3. What are the DCGM metric families?</summary>
The families cover utilisation, memory, temperature, power and clocks, plus ECC errors, Xid driver codes, retired pages, NVLink CRC errors and PCIe replays. Each family answers its own operational question about the GPU, such as whether it is busy or whether its memory is failing.
</details>

<details><summary>4. What does the GPU utilisation tell the platform team?</summary>
It shows whether the GPU is doing useful work. Under 30 percent is a sign of idle capacity, and over 90 percent means the GPU may be the bottleneck. The draft's example alert fires above 95 percent for 10 minutes, and those thresholds are examples to tune.
</details>

<details><summary>5. What does GPU memory pressure tell the platform team?</summary>
It shows whether the GPU is at risk of a CUDA out-of-memory error. The draft treats 90 percent as the point where that error becomes likely, and 95 percent as the model outgrowing the GPU. Its example alert fires above 90 percent for 5 minutes, and that is an example value to set for your own workload.
</details>

<details><summary>6. What do ECC errors tell the platform team?</summary>
They are an early sign of hardware trouble, and many teams treat a rising count as a warning. The draft's pattern is to page on any double-bit error at once. It also alerts when single-bit errors pass 100 per hour, an example rate to tune.
</details>

<details><summary>7. What do Xid errors tell the platform team?</summary>
Xid errors are NVIDIA's driver-level error codes. The draft alerts on every one. Its common codes are 31 for a GPU memory page fault, 43 for a GPU that stopped responding, 48 for a double-bit ECC error and 63 for ECC page retirement. The runbook should say what to do for each code.
</details>

<details><summary>8. What does thermal throttling tell the platform team?</summary>
A hot GPU is usually overheating, which can mean a cooling fault, a workload drawing too much power or an overloaded data-centre cooling system. Each cause points to a different fix. The draft's example alert fires when temperature stays above 85 degrees Celsius for 10 minutes, and you should choose your own limit.
</details>

<details><summary>9. What does clock throttling tell the platform team?</summary>
The GPU lowers its clock to stay within its temperature or power limits. The draft alerts when the SM clock stays below base for 10 minutes, which is an example value.
</details>

<details><summary>10. What is the cardinality impact of the DCGM exporter?</summary>
The draft's estimate is about 115,000 series for a 1000-GPU cluster, and it is a rough figure rather than a measurement. Compare that with the budget in chapter 17.1. Check the series count again after every exporter upgrade.
</details>

<details><summary>11. What is the most common DCGM exporter failure mode?</summary>
The exporter pod is not running on a GPU node. Usually the pod's toleration does not match the node's taint, so the scheduler skips that node. If you see it, check the toleration, confirm the pod is scheduled, and confirm the metrics are exposed.
</details>

<details><summary>12. What is the most critical GPU alert?</summary>
The double-bit ECC error alert is the most critical one. In the draft, a single double-bit error is critical, and it says the GPU is corrupting data and must be replaced at once. The usual response is to drain the node, replace the GPU and check the workload's output.
</details>

<details><summary>13. What is the difference between DBE and SBE?</summary>
DBE means double-bit error, which ECC cannot correct, so the data is treated as corrupted. SBE means single-bit error, which ECC corrects, so the data is recovered. In the draft, one DBE is critical, and a sustained SBE rate is a warning.
</details>

<details><summary>14. What is the Xid code 31?</summary>
It is a GPU memory page fault. The GPU tried to reach a memory page that was not mapped. Driver bugs, workload bugs and hardware failures can all cause it. The runbook names the recovery steps.
</details>

<details><summary>15. What is the Xid code 48?</summary>
It is a double-bit ECC error. The GPU detected a memory error it cannot correct. The draft says the GPU must be replaced immediately. The usual response is to drain the node and replace the GPU.
</details>

<details><summary>16. What is the Xid code 63?</summary>
It is ECC page retirement. The GPU retired a memory page because of errors. The retirement happens automatically, the GPU keeps running, and the retirement count goes up. The draft's pattern is to watch that count and alert when its rate rises.
</details>

<details><summary>17. Why is the DCGM exporter a DaemonSet?</summary>
It must run on every GPU node, and it reads GPU metrics through the kernel driver, so it cannot do its job on a node without a GPU. A DaemonSet runs exactly one exporter pod on each GPU node.
</details>

<details><summary>18. What is the relationship between DCGM and nvidia-smi?</summary>
Both read GPU metrics through the kernel driver. nvidia-smi is a command-line tool you run by hand, while DCGM is a system library the exporter calls. Use nvidia-smi for a quick look, and use DCGM when you need continuous monitoring.
</details>

<details><summary>19. What is the most expensive GPU failure mode?</summary>
The most expensive case is a GPU that corrupts data, which shows up as DBE errors. Outputs and training can go wrong, and customers may see bad predictions before anyone notices. The fix is to replace the GPU at once, investigate the corruption, and re-run the workload on a healthy GPU.
</details>

<details><summary>20. What five questions should the DCGM exporter lab let you answer in five seconds each?</summary>
What is the current GPU utilisation per GPU? What is the current GPU memory pressure per GPU? What is the current ECC error count per GPU? What is the current GPU temperature per GPU? What is the current GPU clock per GPU? If any takes more than 30 seconds, the GPU exporter is not yet a production service.
</details>

---

## Sources and review notes

- NVIDIA Zero-to-Hero Volume 16 (`chapter-03-dcgm-exporter.md`, `chapter-04-interpreting-gpu-metrics.md`). Source for the DCGM exporter deployment, the metric families, the PromQL queries, the alert thresholds, and the operational patterns. The wording has been rewritten in the handbook's voice.
- NVIDIA Zero-to-Hero Volume 7 (`chapter-02-dcgm-and-gpu-metrics.md`). Source for the DCGM integration with the observability stack and the dashboard composition.
- *Generative AI on Kubernetes* (`generative-ai-on-kubernetes`, Chapter 5). Source for the GPU observability patterns on AI infrastructure and the integration with the model serving stack.
- DCGM and DCGM exporter official documentation. Source for the API shapes, the metric names, the exporter configuration, and the alert thresholds.

### Cross-references to other handbook chapters

- Chapter 10.21 for the GPU health concepts (DCGM, ECC, Xid).
- Chapter 16.10 for the AI-specific monitoring pattern.
- Chapter 17.2 for the Prometheus and Grafana integration.
- Chapter 11 for the GPU device plugin.

### Migrated from `nvidia-devops`

The DCGM exporter operational patterns draw on Volume 16 chapters 3-4 and Volume 7 chapter 2. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The alert thresholds in Section 3.1 are starting points drawn from common practice; specific thresholds depend on the GPU model and the workload.
- The GPU utilisation thresholds (30% under-utilised, 90% over-utilised) are rules of thumb; specific thresholds depend on the workload.
- The DCGM exporter cardinality budget in Section 4.2 is approximate; specific cardinality depends on the GPU model and the cluster size.

### Not verified on live hardware

- The lab in Section 6 is **untested** against a live GKE cluster in this repository.
- The DCGM exporter version assumed in the lab should be pinned against the current releases before production use.
- The GPU-specific alert thresholds should be tuned on the production traffic.
