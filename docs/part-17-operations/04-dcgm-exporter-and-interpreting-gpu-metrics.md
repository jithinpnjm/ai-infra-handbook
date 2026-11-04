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

Every other chapter in this part depends on this one. The metrics from Chapter 17.2 are general; the metrics in this chapter are GPU-specific. The team that does not have the DCGM exporter deployed cannot tell whether a GPU is healthy, whether its HBM is saturated, whether its ECC is correcting errors, or whether its clocks are throttling. The team is flying blind on the most expensive resource in the cluster.

A GPU cluster without the DCGM exporter is a cluster where the first sign of a GPU failure is a stuck training job or a crashed inference request. The on-call engineer cannot diagnose the failure because the metrics do not exist. The DCGM exporter is what turns "the GPU is broken" into "GPU 4 on node gpu-node-7 has 17 ECC errors in the last hour and is thermal-throttling at 92 degrees".

```text
Why the DCGM exporter is on the critical path (V16 ch3, 4; V7 ch2; GAK Ch 5):
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

Three operational realities make this chapter a platform-team concern rather than a data-science-only concern:

1. **The DCGM exporter is the only window into the GPU's health.** The exporter is the difference between catching the GPU failure at hour 1 and catching it at hour 24. The platform team owns the deployment.
2. **The GPU metrics are GPU-specific.** A generic exporter (cAdvisor, node exporter) does not expose GPU utilisation, ECC errors, Xid events, or thermal throttling. The platform team must deploy the DCGM exporter separately.
3. **The GPU alert thresholds are different from the CPU alert thresholds.** A 90% CPU utilisation is healthy; a 90% GPU memory utilisation is a CUDA OOM waiting to happen. The platform team must know the GPU-specific thresholds.

**Before a team can run an AI workload on a GPU cluster, the cluster must have the DCGM exporter deployed and the GPU metrics flowing into Prometheus. A GPU cluster without the DCGM exporter is a GPU cluster that the on-call cannot debug.**

## Prerequisites and outcomes

### Prerequisites

- Chapter 10.21 (GPU health: DCGM, ECC, Xid) for the GPU health concepts.
- Chapter 16.10 (Monitoring and drift) for the monitoring patterns.
- Chapter 17.2 (Prometheus and Grafana) for the metrics stack.
- Chapter 11 (GPU Kubernetes) for the GPU device plugin.

### Outcomes

After completing this chapter you will be able to:

1. Deploy the DCGM exporter as a DaemonSet on every GPU node; verify the metrics are flowing into Prometheus.
2. Read the DCGM metric families: utilisation, memory, ECC, Xid, temperature, power, clocks.
3. Write PromQL queries for the GPU-specific operational concerns: per-GPU utilisation, memory pressure, ECC errors, thermal throttling.
4. Configure alert thresholds that catch GPU failures before they cascade.
5. Interpret the DCGM metrics during an incident: what does each metric mean when it spikes?
6. Operate the DCGM exporter on GKE with SLOs, observability, and a runbook.

---

## 1. The DCGM exporter

### 1.1 What DCGM is

The Data Center GPU Manager (DCGM) is NVIDIA's library for managing and monitoring GPUs in a cluster. DCGM runs on every GPU node; DCGM exposes the GPU's health, utilisation, and performance metrics; the metrics are queryable by other tools (DCGM exporter, nvidia-smi, the DCGM CLI).

The DCGM exporter is the bridge from DCGM to Prometheus. The DCGM exporter runs as a DaemonSet on every GPU node; the exporter reads the DCGM metrics; the exporter exposes the metrics in the Prometheus exposition format; Prometheus scrapes the exporter; the metrics flow into Grafana.

```mermaid
flowchart LR
    GPU[NVIDIA GPU<br/>utilisation, memory, ECC, Xid]
    DCGM[DCGM<br/>system library]
    E[DCGM exporter<br/>:9400/metrics]
    P[Prometheus]
    G[Grafana]

    GPU --> DCGM --> E --> P --> G
```

The pattern is: DCGM runs on every GPU node; the DCGM exporter runs alongside DCGM; the exporter exposes the metrics; Prometheus scrapes the exporter; Grafana renders the dashboards.

### 1.2 Deploying the DCGM exporter

The DCGM exporter is deployed as a Helm chart on the GPU nodes.

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

The pattern is: a DaemonSet on every GPU node; the DaemonSet tolerates the GPU taint; the exporter exposes the metrics on port 9400; the ServiceMonitor registers the exporter as a Prometheus target.

### 1.3 The DCGM metric families

NVIDIA Zero-to-Hero Volume 16 chapter 3 and the DCGM exporter documentation walk through the metric families.

| Family | Examples | What it measures |
|---|---|---|
| **Utilization** | `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_SM_UTIL`, `DCGM_FI_DEV_MEM_UTIL` | GPU SM utilisation, memory utilisation |
| **Memory** | `DCGM_FI_DEV_FB_USED`, `DCGM_FI_DEV_FB_TOTAL`, `DCGM_FI_DEV_FB_FREE` | HBM used, total, free |
| **Temperature** | `DCGM_FI_DEV_GPU_TEMP`, `DCGM_FI_DEV_MEMORY_TEMP` | GPU temperature |
| **Power** | `DCGM_FI_DEV_POWER_USAGE`, `DCGM_FI_DEV_ENERGY_CONSUMPTION` | Power draw, energy |
| **Clocks** | `DCGM_FI_DEV_SM_CLOCK`, `DCGM_FI_DEV_MEM_CLOCK` | SM clock, memory clock |
| **ECC** | `DCGM_FI_DEV_ECC_DBE_AGG_DEDUP`, `DCGM_FI_DEV_ECC_DBE_VOL_DEDUP`, `DCGM_FI_DEV_ECC_SBE_AGG_DEDUP` | Double-bit errors (DBE), single-bit errors (SBE) |
| **Xid** | `DCGM_FI_DEV_XID_ERRORS` | NVIDIA Xid errors |
| **Retired pages** | `DCGM_FI_DEV_RETIRED_PAGES`, `DCGM_FI_DEV_RETIRED_PAGES_DBE`, `DCGM_FI_DEV_RETIRED_PAGES_SBE` | Pages retired due to errors |
| **NVLink** | `DCGM_FI_DEV_NVLINK_CRC_DATA_ERROR_COUNT_TX`, `DCGM_FI_DEV_NVLINK_CRC_DATA_ERROR_COUNT_RX` | NVLink CRC errors |
| **PCIe** | `DCGM_FI_DEV_PCIE_REPLAY_COUNTER` | PCIe replay count |

The pattern is: every metric family has a specific operational concern. Utilisation and memory are about capacity; ECC and Xid are about health; temperature and power are about thermals; clocks are about throttling; NVLink and PCIe are about interconnect health.

---

## 2. Reading the GPU metrics

### 2.1 GPU utilisation

The GPU utilisation is the fraction of the GPU's SMs (streaming multiprocessors) that are in use. The utilisation tells the platform team whether the GPU is doing useful work.

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

The pattern is: utilisation below 30% is under-utilised (the GPU is paying for time it is not using); utilisation above 90% is over-utilised (the GPU is the bottleneck). The platform team's pattern is to alert when utilisation exceeds 95% for more than 10 minutes (the GPU is saturated).

### 2.2 GPU memory

The GPU memory is the HBM. The HBM is the most expensive resource on the GPU; the HBM is the leading cause of CUDA OOM crashes.

```promql
# The GPU memory utilisation per GPU
DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL

# The GPU memory pressure (utilisation > 90%)
DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL > 0.9

# The largest model in HBM
max by (gpu) (DCGM_FI_DEV_FB_USED)
```

The pattern is: memory utilisation above 90% is a CUDA OOM waiting to happen; memory utilisation above 95% is the model growing beyond the GPU's capacity. The platform team's pattern is to alert when memory utilisation exceeds 90% for more than 5 minutes.

### 2.3 ECC errors

The ECC errors are the GPU's leading indicator of hardware failure. A GPU that is correcting errors today is a GPU that will fail tomorrow.

```promql
# The ECC double-bit errors (DBE) per GPU over the last hour
sum by (gpu) (increase(DCGM_FI_DEV_ECC_DBE_VOL_DEDUP[1h]))

# The ECC single-bit errors (SBE) per GPU over the last hour
sum by (gpu) (increase(DCGM_FI_DEV_ECC_SBE_VOL_DEDUP[1h]))

# The retired pages (DBE) per GPU
DCGM_FI_DEV_RETIRED_PAGES_DBE

# The alert: any DBE in the last hour
sum by (gpu) (increase(DCGM_FI_DEV_ECC_DBE_VOL_DEDUP[1h])) > 0
```

The pattern is: a single DBE is a critical alert (the GPU is corrupting data; the GPU must be replaced); a sustained SBE rate is a warning (the GPU is degrading; the GPU must be scheduled for replacement). The platform team's pattern is to alert on any DBE immediately; alert on SBE rate above 100/hour.

### 2.4 Xid errors

The Xid errors are NVIDIA's driver-level error codes. The Xid errors tell the platform team what went wrong at the driver level.

```promql
# The Xid errors per GPU
DCGM_FI_DEV_XID_ERRORS

# The distinct Xid codes per GPU
count by (gpu) (DCGM_FI_DEV_XID_ERRORS)
```

The pattern is: every Xid error is an alert. Common Xid codes include 31 (GPU memory page fault), 43 (GPU stopped responding), 48 (double-bit ECC error), 63 (ECC page retirement). The platform team's pattern is to alert on any Xid error immediately; the runbook names the common Xid codes and the recovery steps.

### 2.5 Temperature and power

The temperature and power are the GPU's thermals. The thermals are the leading indicator of thermal throttling.

```promql
# The current GPU temperature
DCGM_FI_DEV_GPU_TEMP

# The power usage
DCGM_FI_DEV_POWER_USAGE

# The thermal throttle indicator
DCGM_FI_DEV_GPU_TEMP > 85
```

The pattern is: temperature above 85 degrees Celsius is a warning; temperature above 90 degrees is thermal throttling; temperature above 95 degrees is a critical alert. Power above the GPU's rated TDP (300 W for H100) is a sign of power supply issues.

### 2.6 Clocks

The clocks are the SM clock and the memory clock. The clocks are the leading indicator of thermal or power throttling.

```promql
# The current SM clock
DCGM_FI_DEV_SM_CLOCK

# The memory clock
DCGM_FI_DEV_MEM_CLOCK

# The clock reduction (throttling indicator)
DCGM_FI_DEV_SM_CLOCK < 1400  # H100 base clock is 1.4 GHz
```

The pattern is: clock below the GPU's base clock is thermal or power throttling. The platform team's pattern is to alert when the clock is below the base clock for more than 10 minutes.

---

## 3. GPU-specific alerting

### 3.1 The alert rules

The GPU-specific alerting rules are the alerts that catch GPU failures.

```yaml
# code/part17/gpu_alerts.yaml (shape only)
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
        expr: sum by (gpu, node) (increase(DCGM_FI_DEV_ECC_DBE_VOL_DEDUP[1h])) > 0
        labels:
          severity: critical
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} has DBE errors"

      - alert: GPUSingleBitECCErrors
        expr: sum by (gpu, node) (rate(DCGM_FI_DEV_ECC_SBE_VOL_DEDUP[1h])) > 100
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

The pattern is: every metric family has a specific alert threshold; the alerts page the on-call before the failure cascades; the runbook names the recovery steps for each alert.

### 3.2 The recovery steps

| Alert | Recovery step |
|---|---|
| GPUHighUtilization | Scale the workload; add a GPU; reduce the batch size |
| GPUMemoryPressure | Reduce the model size; enable gradient checkpointing; move to a larger GPU |
| GPUDoubleBitECCError | Drain the node; replace the GPU; investigate the workload |
| GPUSingleBitECCErrors | Schedule the GPU for replacement; monitor for DBE escalation |
| GPUXidError | Check the runbook for the specific Xid code; restart the workload if safe |
| GPUThermalThrottle | Check the cooling system; reduce the workload's power draw |
| GPUClockThrottle | Check the power supply; reduce the workload's clock |

The recovery steps are the platform team's runbook. The runbook is the difference between an incident that is resolved in minutes and an incident that is resolved in hours.

---

## 4. Operating the DCGM exporter on GKE

### 4.1 The components

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| DCGM | System library on every GPU node | (no backing store) | (no SLO; system library) |
| DCGM exporter | DaemonSet on every GPU node | (exposes metrics) | Scrape latency p99 < 5 s |
| Prometheus | Kubernetes Deployment | TSDB | Scrape latency p99 < 5 s |
| Grafana | Kubernetes Deployment | (uses Prometheus) | Dashboard load p99 < 5 s |

### 4.2 IAM and the cardinality budget

The DCGM exporter adds new metrics to Prometheus. The cardinality budget applies.

| Metric family | Cardinality per cluster | Budget impact |
|---|---|---|
| Utilisation, memory, temperature, power | ~12 metrics × 8 metrics per GPU × 1000 GPUs = 96,000 series | Low |
| ECC, Xid | ~6 metrics × 1000 GPUs = 6,000 series | Low |
| NVLink, PCIe | ~10 metrics × 1000 GPUs = 10,000 series | Low |
| Retired pages | ~3 metrics × 1000 GPUs = 3,000 series | Low |

The total cardinality from the DCGM exporter on a 1000-GPU cluster is approximately 115,000 series. The cardinality is within the budget defined in Chapter 17.1.

### 4.3 Observability

| Metric | Why it matters | Alert |
|---|---|---|
| DCGM exporter scrape latency p99 | Hot path for every GPU metric | > 10 s |
| DCGM exporter pod restarts | DCGM exporter is unhealthy | > 0 for 1 hour |
| GPU node CPU usage | DCGM exporter overhead | > 50% for 1 hour |
| GPU node memory usage | DCGM exporter overhead | > 80% for 1 hour |

The DCGM exporter pod restart alert is the most important. A DCGM exporter that is restarting is a DCGM exporter that is not exporting metrics; the GPU metrics are missing; the team cannot detect GPU failures.

---

## 5. How it fails

Six failure modes recur.

### 5.1 "The DCGM exporter is not running on a GPU node"

**Symptom:** The Prometheus target for the GPU node is missing; the GPU metrics for the node are missing.

**Diagnosis:** The DCGM exporter DaemonSet has a taint toleration that does not match the GPU node's taint; the pod is not scheduled on the node.

**Fix:** Verify the taint toleration; verify the pod is scheduled on the node; verify the metrics are exposed on port 9400; add an alert when the DCGM exporter is missing from a GPU node.

### 5.2 "The DCGM exporter is consuming too much CPU"

**Symptom:** The DCGM exporter pod is throttled; the metrics are delayed; the on-call cannot detect GPU failures in real time.

**Diagnosis:** The DCGM exporter is running too frequently; the metrics are being scraped at a high rate; the pod's CPU limit is too low.

**Fix:** Increase the CPU limit; reduce the scrape interval; verify the metrics are still flowing within the SLO.

### 5.3 "The GPU is in ECC error storm"

**Symptom:** The DCGM_FI_DEV_ECC_DBE_VOL_DEDUP metric is increasing rapidly; the GPU is corrupting data.

**Diagnosis:** The GPU has a hardware failure; the GPU must be replaced.

**Fix:** Drain the node; replace the GPU; investigate the workload for data corruption; add the GPU to the retired-GPUs list.

### 5.4 "The GPU is thermal-throttling"

**Symptom:** The DCGM_FI_DEV_GPU_TEMP metric is above 85 degrees; the DCGM_FI_DEV_SM_CLOCK metric is below the base clock.

**Diagnosis:** The cooling system is failing; the workload is consuming too much power; the data centre's HVAC is overloaded.

**Fix:** Check the cooling system; reduce the workload's power draw; move the workload to a cooler node.

### 5.5 "The DCGM exporter metrics are stale"

**Symptom:** The Prometheus target for the DCGM exporter is up; the metrics are flowing; the metrics are stale (the values have not changed in hours).

**Diagnosis:** The DCGM exporter is running but not reading from DCGM; the DCGM system library is failing; the kernel driver is failing.

**Fix:** Restart the DCGM exporter pod; restart the DCGM system library; check the kernel driver logs.

### 5.6 "The DCGM exporter is missing the high-cardinality labels"

**Symptom:** The on-call cannot query the metrics by team or by model; the labels the team needs are missing.

**Diagnosis:** The DCGM exporter does not have access to the Kubernetes labels; the pod is missing the service account; the pod is missing the role binding.

**Fix:** Verify the pod's service account; verify the role binding; restart the pod; verify the labels are present.

---

## 6. Hands-on lab

This lab stands up the DCGM exporter on GKE, verifies the metrics are flowing into Prometheus, and builds the GPU-specific dashboards. The lab is **untested** in this repository.

### 6.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+) with at least 1 H100 or A100 GPU node.
- Helm 3 for installing the DCGM exporter.
- Prometheus installed (Chapter 17.2).

### 6.2 Step 1: install the DCGM exporter

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

```bash
# Port-forward to Prometheus
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Query the GPU utilisation
curl -s 'http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL' | jq .
# expected: the GPU utilisation per GPU
```

### 6.4 Step 3: build the GPU dashboard

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

```bash
# Apply the alert rules
kubectl -n monitoring create configmap gpu-alerts \
  --from-file=configs/gpu_alerts.yaml

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
# expected: the alert rules are active
```

### 6.6 Step 5: simulate a GPU failure

```bash
# Inject a synthetic ECC error (for testing only - DO NOT run on production)
nvidia-smi -q -d ECC
# expected: the ECC error count is non-zero; the alert fires
```

### 6.7 Step 6: verify the alert fires

```bash
# Query Alertmanager
kubectl -n monitoring port-forward svc/alertmanager-operated 9093:9093 &
curl -s http://localhost:9093/api/v2/alerts | jq .
# expected: the GPUDoubleBitECCError alert is active
```

### 6.8 What to record

After the lab, you should be able to answer five questions in five seconds each:

1. What is the current GPU utilisation per GPU?
2. What is the current GPU memory pressure per GPU?
3. What is the current ECC error count per GPU?
4. What is the current GPU temperature per GPU?
5. What is the current GPU clock per GPU?

If any takes more than 30 seconds, the GPU exporter is not yet a production service. The lab is **untested** against a live GKE cluster.

---

## Exercises

1. **Add a GPU temperature dashboard.** Build a Grafana dashboard that shows the temperature per GPU; alert when the temperature exceeds 85 degrees. *Solution sketch:* the DCGM_FI_DEV_GPU_TEMP metric; a Grafana panel; an alert rule.
2. **Add a retired-GPUs list.** Maintain a list of GPUs that have been retired due to ECC errors; add an alert when a GPU is added to the list. *Solution sketch:* a ConfigMap that lists the retired GPUs; a Prometheus alert that compares the running GPUs to the list.
3. **Add a per-team GPU cost.** Compute the GPU cost per team from the DCGM metrics; the cost feeds the FinOps dashboard from Chapter 16.14. *Solution sketch:* the DCGM_FI_DEV_GPU_UTIL * DCGM_FI_DEV_POWER_USAGE; the per-team labels; the cost dashboard.
4. **Add a GPU health check.** Add a Kubernetes health check that fails when the DCGM exporter is not running on a GPU node. *Solution sketch:* a Kubernetes Probe that checks the DCGM exporter's `/health` endpoint.
5. **Add a GPU utilisation histogram.** Emit the GPU utilisation as a histogram; the histogram feeds the percentile-based dashboards. *Solution sketch:* a custom exporter that emits the utilisation as a histogram; the histogram feeds the dashboards.
6. **Add a GPU NVLink error alert.** Alert when the NVLink CRC error count exceeds 100 in an hour. *Solution sketch:* a Prometheus alert on the DCGM_FI_DEV_NVLINK_CRC_DATA_ERROR_COUNT_TX metric.

---

## Checkpoint questions

<details><summary>1. What is the DCGM exporter?</summary>
The bridge from DCGM to Prometheus. The DCGM exporter runs as a DaemonSet on every GPU node; the exporter reads the DCGM metrics; the exporter exposes the metrics in the Prometheus exposition format; Prometheus scrapes the exporter; the metrics flow into Grafana.
</details>

<details><summary>2. What is DCGM?</summary>
NVIDIA's Data Center GPU Manager. DCGM is a system library that runs on every GPU node; DCGM exposes the GPU's health, utilisation, and performance metrics. DCGM is what the DCGM exporter reads from.
</details>

<details><summary>3. What are the DCGM metric families?</summary>
Utilization (GPU SM utilisation, memory utilisation), Memory (HBM used, total, free), Temperature (GPU temperature), Power (power draw, energy), Clocks (SM clock, memory clock), ECC (double-bit errors, single-bit errors), Xid (NVIDIA driver-level error codes), Retired pages (pages retired due to errors), NVLink (NVLink CRC errors), PCIe (PCIe replay count). Every metric family has a specific operational concern.
</details>

<details><summary>4. What does the GPU utilisation tell the platform team?</summary>
Whether the GPU is doing useful work. Utilisation below 30% is under-utilised (the GPU is paying for time it is not using); utilisation above 90% is over-utilised (the GPU is the bottleneck). The platform team's pattern is to alert when utilisation exceeds 95% for more than 10 minutes.
</details>

<details><summary>5. What does GPU memory pressure tell the platform team?</summary>
Whether the GPU is at risk of CUDA OOM. Memory utilisation above 90% is a CUDA OOM waiting to happen; memory utilisation above 95% is the model growing beyond the GPU's capacity. The platform team's pattern is to alert when memory utilisation exceeds 90% for more than 5 minutes.
</details>

<details><summary>6. What do ECC errors tell the platform team?</summary>
The GPU's leading indicator of hardware failure. A GPU that is correcting errors today is a GPU that will fail tomorrow. The platform team's pattern is to alert on any double-bit error immediately; alert on single-bit error rate above 100/hour.
</details>

<details><summary>7. What do Xid errors tell the platform team?</summary>
The NVIDIA driver-level error codes. Every Xid error is an alert. Common Xid codes include 31 (GPU memory page fault), 43 (GPU stopped responding), 48 (double-bit ECC error), 63 (ECC page retirement). The runbook names the common Xid codes and the recovery steps.
</details>

<details><summary>8. What does thermal throttling tell the platform team?</summary>
The GPU is overheating. The cooling system may be failing; the workload may be consuming too much power; the data centre's HVAC may be overloaded. The platform team's pattern is to alert when the temperature exceeds 85 degrees Celsius for more than 10 minutes.
</details>

<details><summary>9. What does clock throttling tell the platform team?</summary>
The GPU is reducing its clock to manage temperature or power. The platform team's pattern is to alert when the SM clock is below the GPU's base clock for more than 10 minutes.
</details>

<details><summary>10. What is the cardinality impact of the DCGM exporter?</summary>
Approximately 115,000 series per 1000-GPU cluster. The cardinality is within the budget defined in Chapter 17.1. The platform team's pattern is to verify the cardinality after every DCGM exporter upgrade.
</details>

<details><summary>11. What is the most common DCGM exporter failure mode?</summary>
The DCGM exporter is not running on a GPU node. The pod's taint toleration does not match the GPU node's taint; the pod is not scheduled on the node. The fix is to verify the taint toleration; verify the pod is scheduled; verify the metrics are exposed.
</details>

<details><summary>12. What is the most critical GPU alert?</summary>
The double-bit ECC error alert. A single DBE is a critical alert; the GPU is corrupting data; the GPU must be replaced immediately. The platform team's pattern is to drain the node; replace the GPU; investigate the workload for data corruption.
</details>

<details><summary>13. What is the difference between DBE and SBE?</summary>
DBE (double-bit errors) are uncorrectable errors; the data is corrupted. SBE (single-bit errors) are correctable errors; the data is recovered. A single DBE is a critical alert; sustained SBE rate is a warning.
</details>

<details><summary>14. What is the Xid code 31?</summary>
GPU memory page fault. The GPU tried to access a memory page that was not mapped. Common causes include driver bugs, workload bugs, or hardware failures. The runbook names the recovery steps.
</details>

<details><summary>15. What is the Xid code 48?</summary>
Double-bit ECC error. The GPU detected an uncorrectable memory error. The GPU must be replaced immediately. The platform team's pattern is to drain the node and replace the GPU.
</details>

<details><summary>16. What is the Xid code 63?</summary>
ECC page retirement. The GPU retired a memory page due to errors. The retirement is automatic; the GPU continues to operate; the retirement count increases. The platform team's pattern is to monitor the retirement count; alert when the rate increases.
</details>

<details><summary>17. Why is the DCGM exporter a DaemonSet?</summary>
Because the DCGM exporter must run on every GPU node; the DCGM exporter reads the GPU's metrics via the kernel driver; the DCGM exporter cannot run on a non-GPU node. The DaemonSet pattern ensures one exporter pod per GPU node.
</details>

<details><summary>18. What is the relationship between DCGM and nvidia-smi?</summary>
Both DCGM and nvidia-smi read the GPU's metrics via the kernel driver. nvidia-smi is a CLI; DCGM is a system library that the DCGM exporter uses. nvidia-smi is for ad-hoc inspection; DCGM is for continuous monitoring.
</details>

<details><summary>19. What is the most expensive GPU failure mode?</summary>
The GPU is corrupting data (DBE errors). The workload's outputs are wrong; the workload's training is corrupted; the customer sees bad predictions. The fix is immediate GPU replacement; the data corruption must be investigated; the workload must be re-run on a healthy GPU.
</details>

<details><summary>20. What five questions should the DCGM exporter lab let you answer in five seconds each?</summary>
What is the current GPU utilisation per GPU. What is the current GPU memory pressure per GPU. What is the current ECC error count per GPU. What is the current GPU temperature per GPU. What is the current GPU clock per GPU. If any takes more than 30 seconds, the GPU exporter is not yet a production service.
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
