---
id: "c17-02"
title: "17.2 Prometheus and Grafana"
sidebar_label: "17.2 Prometheus and Grafana"
sidebar_position: 2
description: "Prometheus and Grafana for AI infrastructure: scrape configuration, recording rules, alerting rules, PromQL queries for GPU workloads, dashboard composition, and the operational patterns that make the metrics stack a production service."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 17.2 Prometheus and Grafana

| Field | Value |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Primary sources | *Production Kubernetes* (`production-kubernetes`, Chapter 9); NVIDIA Zero-to-Hero Volume 16 (`chapter-05-prometheus-grafana.md`); NVIDIA Zero-to-Hero Volume 7 (`chapter-01-observability-stack-overview.md`); Prometheus and Grafana official documentation |
| Cross-references | Chapter 17.1 (Observability foundations); Chapter 17.4 (DCGM exporter); Chapter 17.6 (Alerting and SLOs); Chapter 16.10 (Monitoring and drift) |
| Coverage file | `planning/coverage/chapters/17-02.md` |
| Claim & number ledger | `planning/ledgers/17-02.md` |

## Why this matters for AI infrastructure

Chapter 17.1 named the three pillars. This chapter walks through the first one in detail: metrics. Prometheus is the de facto standard for AI infrastructure metrics; Grafana is the de facto standard for the dashboards that consume those metrics. The combination is what every other operational chapter in this part depends on.

The Prometheus + Grafana stack is on the critical path of every alert, every SLO, every capacity-planning model. A misconfigured stack is a stack that pages the on-call at the wrong moment or stays silent when the cluster is down. The platform team's job is to make the stack a production service — with SLOs, observability, and a runbook.

```text
Why Prometheus + Grafana is on the critical path (V16 ch5; PK Ch 9):
- Prometheus is the de facto standard for Kubernetes metrics. Every exporter
  (DCGM, cAdvisor, kube-state-metrics, the application exporter) exposes
  metrics in the Prometheus exposition format. The format is human-readable;
  the format is scrape-based; the format is queryable.
- Grafana is the de facto standard for the dashboards that consume those
  metrics. Grafana renders panels from Prometheus, Loki, and Tempo. Grafana
  is the on-call engineer's home page.
- The combination is what catches the "cluster is on fire but the dashboards
  are stale" failure mode. The combination is what catches the "model is
  making bad predictions but the operational metrics are green" failure mode.
```

Three operational realities make this chapter a platform-team concern rather than a data-science-only concern:

1. **Prometheus is on the hot path of every alert.** Every SLO from Chapter 16.14 is measured by Prometheus. Every alert from Chapter 17.6 is fired by Prometheus. Prometheus's reliability is the platform's reliability.
2. **Grafana is the on-call engineer's home page.** The on-call engineer's situational awareness is Grafana's dashboard quality. A bad dashboard is a slow on-call response.
3. **The cardinality budget from Chapter 17.1 is enforced by Prometheus.** A label that exceeds the budget can OOM Prometheus. The platform team's cardinality discipline is what keeps Prometheus alive.

**Before a team can run an AI workload on a cluster, the cluster must have a working Prometheus + Grafana stack with reliable scrapes, well-designed dashboards, and enforced cardinality budgets. A cluster without the stack is a cluster that nobody can debug.**

## Prerequisites and outcomes

### Prerequisites

- Chapter 17.1 (Observability foundations) for the three pillars and the cardinality budget.

### Outcomes

After completing this chapter you will be able to:

1. Configure Prometheus scrape jobs for the AI infrastructure's exporters (DCGM, cAdvisor, kube-state-metrics, application exporters).
2. Write recording rules and alerting rules for AI workloads (the PromQL for GPU utilisation, KV cache occupancy, NCCL collective latency).
3. Compose Grafana dashboards that answer the on-call's questions in five seconds.
4. Manage Prometheus's storage and retention: the TSDB compaction, the retention period, the disk budget.
5. Operate the Prometheus + Grafana stack on GKE with SLOs, observability, and a runbook.

---

## 1. Prometheus

### 1.1 The Prometheus architecture

*Production Kubernetes* Chapter 9 walks through the Prometheus architecture. Prometheus is a pull-based monitoring system; the Prometheus server scrapes metrics from a set of targets; the metrics are stored in a time-series database (TSDB); the metrics are queried via PromQL.

```mermaid
flowchart LR
    subgraph Targets["Scrape targets"]
        T1[DCGM exporter]
        T2[cAdvisor]
        T3[kube-state-metrics]
        T4[Node exporter]
        T5[App exporter]
    end

    P[Prometheus server<br/>scrape + TSDB]
    A[Alertmanager]
    G[Grafana]

    T1 --> P
    T2 --> P
    T3 --> P
    T4 --> P
    T5 --> P
    P --> A
    P --> G
```

The pattern is: every workload exposes a `/metrics` endpoint in the Prometheus exposition format; Prometheus scrapes the endpoint every N seconds; Prometheus stores the metrics in a TSDB; Grafana queries the TSDB; Alertmanager evaluates the alert rules.

### 1.2 Scrape configuration

The scrape configuration is a YAML file that lists every target the Prometheus server scrapes.

```yaml
# code/part17/prometheus_scrape.yaml (shape only)
scrape_configs:
  - job_name: 'dcgm-exporter'
    scrape_interval: 15s
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_nvidia_com_gpu_product]
        target_label: gpu_product
      - source_labels: [__meta_kubernetes_pod_node_name]
        target_label: node
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        regex: ([^:]+)(?::\d+)?
        target_label: __address__
        replacement: ${1}:9400

  - job_name: 'cadvisor'
    scrape_interval: 15s
    kubernetes_sd_configs:
      - role: node

  - job_name: 'kubelet'
    scrape_interval: 15s
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics

  - job_name: 'app-exporter'
    scrape_interval: 10s
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        action: drop
        regex: false
      - source_labels: [__meta_kubernetes_service_label_app]
        target_label: job
```

The pattern is: use Kubernetes service discovery to find the targets; use relabel rules to add the labels the platform team needs; use the `__metrics_path__` and `__address__` to point Prometheus at the exporter's metrics endpoint.

### 1.3 The exporters for AI infrastructure

*Production Kubernetes* Chapter 9 and NVIDIA Zero-to-Hero Volume 16 chapter 5 walk through the exporters.

| Exporter | What it exposes | Where it runs |
|---|---|---|
| **DCGM exporter** | GPU utilisation, memory, temperature, ECC, Xid | One per GPU node (DaemonSet) |
| **cAdvisor** | Container CPU, memory, network, filesystem I/O | One per node (built into kubelet) |
| **kube-state-metrics** | Kubernetes object state (pods, nodes, deployments) | One Deployment |
| **Node exporter** | Host CPU, memory, disk, network | One per node (DaemonSet) |
| **Application exporter** | Application-specific metrics | Sidecar per application |
| **Inference engine exporter** | Triton / vLLM / NIM metrics | Built into the engine |

The pattern is: one exporter per concern. The platform team owns the cluster-wide exporters (DCGM, cAdvisor, kube-state-metrics, node exporter); the application team owns the application exporter; the inference engine ships its own exporter.

---

## 2. PromQL for AI workloads

### 2.1 The basic PromQL

PromQL is the query language for Prometheus. The basic shape is `metric_name{labels} operator value`. The queries can aggregate, transform, and join.

```promql
# The current GPU utilisation per node
gpu_utilization_ratio{node="gpu-node-1"}

# The average GPU utilisation across the cluster
avg(gpu_utilization_ratio)

# The p99 inference latency over the last 5 minutes
histogram_quantile(0.99, rate(inference_request_duration_seconds_bucket[5m]))

# The inference request rate per model
sum by (model) (rate(inference_request_total[5m]))

# The 5xx error rate per model
sum by (model) (rate(inference_request_total{status=~"5.."}[5m]))

# The GPU memory utilisation per GPU
gpu_memory_used_bytes / gpu_memory_total_bytes
```

The pattern is: pick a metric; apply labels; aggregate with `sum`, `avg`, `max`, `min`; aggregate across time with `rate`, `increase`, `irate`; compute percentiles with `histogram_quantile`.

### 2.2 PromQL for the AI infrastructure

The platform team's PromQL queries are the queries the on-call engineer runs during an incident. The queries are the queries that drive the dashboards.

```promql
# GPU pool utilisation (cluster-wide)
avg(gpu_utilization_ratio) by (gpu_product)

# Per-team GPU utilisation
sum by (team) (gpu_utilization_ratio)

# GPU memory pressure (per GPU)
gpu_memory_used_bytes / gpu_memory_total_bytes > 0.9

# NCCL collective latency (per collective)
histogram_quantile(0.99, rate(nccl_collective_duration_seconds_bucket[5m]))

# Data loading throughput (per training job)
rate(data_loading_throughput_total[5m])

# Training loss (per run)
training_loss{run_id="abc-123"}

# Inference throughput (per model, per replica)
sum by (model, replica) (rate(inference_token_throughput_total[5m]))

# Inference p99 latency vs SLO
histogram_quantile(0.99, rate(inference_request_duration_seconds_bucket[5m])) > 0.3

# Live accuracy (per model)
model_quality_score{model="churn-model"}

# Drift score (per feature)
evidently_drift_score{feature="user_tenure_days"}

# Cost per team per month
sum by (team) (kubecost_team_cost)
```

The platform team's pattern is to publish a library of these queries; the queries are versioned; the queries are tested; the queries are the queries the on-call runs during an incident.

### 2.3 Recording rules

Recording rules pre-compute expensive queries. The platform team's pattern is to record the queries that drive the dashboards.

```yaml
# code/part17/recording_rules.yaml (shape only)
groups:
  - name: gpu_pool
    interval: 30s
    rules:
      - record: gpu_pool:utilization:avg5m
        expr: avg by (gpu_product) (gpu_utilization_ratio)
      - record: gpu_pool:memory_pressure:avg5m
        expr: avg by (gpu_product) (gpu_memory_used_bytes / gpu_memory_total_bytes)
      - record: gpu_pool:count:by_product
        expr: count by (gpu_product) (gpu_utilization_ratio)

  - name: inference
    interval: 30s
    rules:
      - record: inference:latency:p99:5m
        expr: histogram_quantile(0.99, rate(inference_request_duration_seconds_bucket[5m]))
      - record: inference:error_rate:5m
        expr: sum by (model) (rate(inference_request_total{status=~"5.."}[5m])) / sum by (model) (rate(inference_request_total[5m]))
      - record: inference:throughput:5m
        expr: sum by (model) (rate(inference_request_total[5m]))

  - name: cost
    interval: 5m
    rules:
      - record: cost:team:monthly
        expr: sum by (team) (kubecost_team_cost)
```

The recording rules fire every 30 seconds (or every 5 minutes for the cost rule); the rules write the result to a new time series; the dashboards read the pre-computed series; the on-call engineer sees the dashboard in seconds.

---

## 3. Grafana

### 3.1 The Grafana architecture

Grafana is the dashboard renderer. Grafana queries the data sources (Prometheus, Loki, Tempo) and renders the panels. The panels are organised into dashboards; the dashboards are organised into folders; the folders are organised into teams.

```mermaid
flowchart LR
    subgraph Sources["Data sources"]
        P[Prometheus]
        L[Loki]
        T[Tempo]
    end

    G[Grafana<br/>dashboards + alerts]
    U[Users<br/>on-call + teams]

    P --> G
    L --> G
    T --> G
    G --> U
```

The pattern is: Grafana reads from the data sources; the dashboards are JSON files; the dashboards are versioned in Git; the dashboards are deployed via the platform team's GitOps loop.

### 3.2 The on-call dashboard

The on-call dashboard is the single most important dashboard in the platform. The dashboard is the on-call engineer's home page; the dashboard answers the questions the on-call asks during an incident.

```yaml
# code/part17/on_call_dashboard.json (shape only)
{
  "dashboard": {
    "title": "AI Factory - On-Call",
    "panels": [
      {"title": "Cluster p99 inference latency", "type": "timeseries", "targets": [{"expr": "inference:latency:p99:5m"}]},
      {"title": "Inference error rate per model", "type": "timeseries", "targets": [{"expr": "inference:error_rate:5m"}]},
      {"title": "GPU pool utilisation", "type": "stat", "targets": [{"expr": "gpu_pool:utilization:avg5m"}]},
      {"title": "GPU memory pressure", "type": "timeseries", "targets": [{"expr": "gpu_pool:memory_pressure:avg5m"}]},
      {"title": "Recent error logs", "type": "logs", "targets": [{"expr": "{severity=\"ERROR\"}"}]},
      {"title": "Open incidents", "type": "stat", "targets": [{"expr": "alertmanager_alerts_state{state=\"active\"}"}]},
      {"title": "Cost per team this month", "type": "bargauge", "targets": [{"expr": "cost:team:monthly"}]},
      {"title": "Model quality signals", "type": "stat", "targets": [{"expr": "model_quality_score"}]}
    ]
  }
}
```

The dashboard has eight panels; the panels answer the eight questions the on-call asks during an incident. The dashboard loads in seconds; the dashboard is the on-call engineer's situational awareness.

### 3.3 The per-team dashboard

Each team has its own dashboard. The team's dashboard shows the team's specific models, the team's specific pipelines, the team's specific cost. The platform team owns the template; the team fills in the specifics.

### 3.4 Dashboard as code

Dashboards are JSON files. The platform team's pattern is to version the dashboards in Git; deploy the dashboards via Argo CD or a similar GitOps tool; the dashboards are reviewable in pull requests.

```bash
# code/part17/dashboard_deploy.sh (shape only)
#!/bin/bash
# Deploy a Grafana dashboard via the Grafana API
DASHBOARD_JSON=$(cat dashboards/on-call.json | jq -c '.dashboard')
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d "{\"dashboard\": $DASHBOARD_JSON, \"overwrite\": true}" \
  $GRAFANA_URL/api/dashboards/db
```

The pattern is: the dashboard is a file; the file is in Git; the deployment is automated; the deployment is auditable.

---

## 4. Storage and retention

### 4.1 The TSDB

Prometheus stores metrics in a time-series database (TSDB) on local disk. The TSDB has three components: the head block (recent data), the write-ahead log (WAL), and the compacted blocks (older data).

```mermaid
flowchart LR
    H[Head block<br/>recent data in memory]
    W[Write-ahead log<br/>disk]
    B[Compacted blocks<br/>older data on disk]

    S[Scrape] --> H
    H -->|flush| W
    H -->|compact| B
    W -->|replay| H
```

The pattern is: Prometheus writes to the head block; the head block flushes to the WAL on shutdown; the head block compacts to immutable blocks over time; the compacted blocks are queryable alongside the head block.

### 4.2 Retention

The retention period is the trade-off between storage cost and historical visibility.

| Retention | Storage per series per year | Use case |
|---|---|---|
| 1 day | 1 MB | Debugging only |
| 7 days | 7 MB | Recent debugging |
| 30 days | 30 MB | Default |
| 90 days | 90 MB | Capacity planning |
| 1 year | 365 MB | Regulatory audit |
| 5 years | 1.8 GB | Long-term retention (rare) |

The platform team's pattern is to set the retention based on the use case: 30 days for operational dashboards; 90 days for capacity planning; 1 year for the audit log. The retention is enforced by the Prometheus `--storage.tsdb.retention.time` flag.

### 4.3 Remote storage

For long-term retention, Prometheus can write to remote storage (Thanos, Cortex, Mimir). The pattern is: Prometheus retains recent data locally; the remote storage backend retains historical data; the query layer (Querier) merges the two.

```mermaid
flowchart LR
    P[Prometheus<br/>recent data]
    R[Thanos Receive<br/>remote write]
    S[Object storage<br/>historical blocks]
    Q[Querier<br/>merged query]
    G[Grafana]

    P -->|remote_write| R
    R --> S
    P --> Q
    S --> Q
    Q --> G
```

The pattern is the same as Chapter 13's storage pattern: recent data is local; historical data is in object storage; the query layer merges the two. The pattern is what makes 90-day retention affordable.

---

## 5. Operating Prometheus and Grafana on GKE

### 5.1 The components

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Prometheus server | Kubernetes Deployment, 2 replicas (HA) | Persistent disk | Scrape latency p99 < 5 s |
| Alertmanager | Kubernetes Deployment, 2 replicas | (sends to PagerDuty) | Alert latency p99 < 10 s |
| Grafana | Kubernetes Deployment | (uses Prometheus) | Dashboard load p99 < 5 s |
| Thanos Receive | Kubernetes Deployment | Object storage | Remote write p99 < 10 s |
| Thanos Querier | Kubernetes Deployment | Object storage | Query latency p99 < 5 s |

### 5.2 IAM and the cardinality budget

The Prometheus + Grafana stack has its own IAM. The pattern is:

| Role | Who | What they can do |
|---|---|---|
| `prometheus.reader` | Every team's data scientists | Query PromQL; view dashboards |
| `prometheus.writer` | The exporters | Write metrics to the remote write endpoint |
| `prometheus.admin` | The platform team | Manage the Prometheus server; set the cardinality budget |

The cardinality budget is enforced by the platform team's discipline. Every metric that the team adds must declare its label cardinality; the team rejects metrics whose cardinality exceeds the budget.

### 5.3 Observability

| Metric | Why it matters | Alert |
|---|---|---|
| Scrape latency p99 | Hot path for every metric | > 10 s |
| TSDB head series count | Cardinality budget | > budget for 1 hour |
| TSDB disk usage | Storage budget | > 80% for 1 hour |
| Prometheus process CPU | Resource budget | > 80% for 1 hour |
| Prometheus process memory | Resource budget | > 80% for 1 hour |
| Dashboard load latency p99 | On-call response time | > 10 s |

The TSDB head series count alert is the most important. A spike in series count is a signal that a new high-cardinality label was added; the platform team investigates before Prometheus OOMs.

---

## 6. How it fails

Six failure modes recur.

### 6.1 "Prometheus is using too much memory"

**Symptom:** Prometheus is OOM-killed; the dashboards go stale; the alerts stop firing.

**Diagnosis:** The cardinality exceeded the memory budget. A new metric with a high-cardinality label was added.

**Fix:** Identify the high-cardinality metric with `prometheus_tsdb_head_series`; drop the high-cardinality label at the source; aggregate the metric before it reaches Prometheus. Add a cardinality alert.

### 6.2 "The dashboards are loading slowly"

**Symptom:** The on-call opens the dashboard; the dashboard takes 30 seconds to load; the on-call cannot answer the question in seconds.

**Diagnosis:** The dashboard has too many panels; the panels query too many series; the queries are not recording rules.

**Fix:** Reduce the number of panels per dashboard; pre-compute expensive queries as recording rules; use Prometheus federation to query the right Prometheus for the right dashboard.

### 6.3 "The alert fires but the page is empty"

**Symptom:** Alertmanager fires the alert; the page goes out; the on-call opens the dashboard; the dashboard shows the metric is green.

**Diagnosis:** The alert rule has a typo in the PromQL; the alert fires on a label combination that is not the one the on-call cares about.

**Fix:** Test the alert rule before deploying it; use the `during` keyword in the alert rule to filter the cases; add an alert rule that catches the false positive.

### 6.4 "The retention period is too short"

**Symptom:** The on-call needs historical data from 60 days ago; the data is not in Prometheus; the on-call cannot debug the incident.

**Diagnosis:** The retention period is too short for the incident's age.

**Fix:** Increase the retention period; use Thanos remote storage for long-term retention; document the retention period on the platform's status page.

### 6.5 "The Thanos remote write is failing"

**Symptom:** The Prometheus server is healthy; the historical data is not in object storage; the long-term queries fail.

**Diagnosis:** The remote write endpoint is unhealthy; the network is failing; the credentials are wrong.

**Fix:** Verify the remote write endpoint; verify the credentials; verify the network; add a remote write latency alert.

### 6.6 "The cardinality budget is silently exceeded"

**Symptom:** Prometheus is using more memory than expected; the cardinality alert has not fired.

**Diagnosis:** The cardinality alert threshold is too high; the alert is not catching the slow creep.

**Fix:** Lower the cardinality alert threshold; add a cardinality growth rate alert; review the cardinality budget quarterly.

---

## 7. Hands-on lab

This lab stands up Prometheus and Grafana on GKE, configures the scrape jobs for the AI infrastructure's exporters, and builds the on-call dashboard. The lab is **untested** in this repository.

### 7.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+).
- Helm 3 for installing the observability stack.
- A workload that emits Prometheus metrics (a DCGM exporter from Chapter 17.4).

### 7.2 Step 1: install Prometheus

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set grafana.adminPassword=admin
# expected: Prometheus and Grafana pods are running
```

### 7.3 Step 2: install the DCGM exporter

```bash
helm install dcgm-exporter nvidia/dcgm-exporter \
  --namespace monitoring \
  --set serviceMonitor.enabled=true
# expected: the DCGM exporter pods are running on each GPU node; the metrics are scraped by Prometheus
```

### 7.4 Step 3: verify the scrape

```bash
# Port-forward to Prometheus
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Query the DCGM metrics
curl -s 'http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL' | jq .
# expected: the GPU utilisation per GPU
```

### 7.5 Step 4: build the on-call dashboard

```bash
# Apply the dashboard JSON
kubectl -n monitoring create configmap on-call-dashboard \
  --from-file=dashboards/on-call.json

# Reload Grafana to pick up the dashboard
curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/on-call-import.json
# expected: the dashboard is available in Grafana at /d/on-call/ai-factory-on-call
```

### 7.6 Step 5: write a recording rule

```bash
# Apply the recording rules
kubectl -n monitoring create configmap recording-rules \
  --from-file=configs/recording_rules.yaml

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
# expected: the recording rules are active
```

### 7.7 Step 6: query the recording rules

```bash
curl -s 'http://localhost:9090/api/v1/query?query=gpu_pool:utilization:avg5m' | jq .
# expected: the GPU pool utilisation per GPU product
```

### 7.8 What to record

After the lab, you should be able to answer five questions in five seconds each:

1. What is the current Prometheus scrape latency p99?
2. What is the current TSDB head series count?
3. What is the current inference p99 latency (from the recording rule)?
4. What is the current cost per team this month (from the recording rule)?
5. What is the current cardinality per metric?

If any takes more than 30 seconds, the metrics stack is not yet a production service. The lab is **untested** against a live GKE cluster.

---

## Exercises

1. **Add a recording rule for the drift detector.** Create a recording rule that pre-computes the per-feature drift score. *Solution sketch:* a recording rule that aggregates `evidently_drift_score` per feature.
2. **Add an alert for high cardinality.** Create an alert that fires when any metric's cardinality exceeds 1000. *Solution sketch:* a Prometheus alert on `count by (__name__) ({__name__=~".+"})`.
3. **Add Thanos remote storage.** Configure Prometheus to remote-write to Thanos; verify the historical data is queryable. *Solution sketch:* the Thanos Receive endpoint; the Thanos Querier; a Thanos integration in Grafana.
4. **Add a per-team dashboard.** Build a dashboard template that the teams fill in with their specific models and pipelines. *Solution sketch:* a Grafana dashboard JSON template; the team's specific labels; the deployment script.
5. **Add a dashboard for the audit log.** Build a Grafana dashboard that shows the recent audit log events; the dashboard is the on-call engineer's view into the regulator's questions. *Solution sketch:* a Grafana data source that queries the audit log; the dashboard's panels.
6. **Add a cardinality growth rate alert.** Alert when the cardinality grows by more than 10% in 24 hours. *Solution sketch:* a recording rule that computes the daily cardinality delta; an alert on the delta.

---

## Checkpoint questions

<details><summary>1. What is Prometheus's architecture?</summary>
Prometheus is a pull-based monitoring system; the Prometheus server scrapes metrics from a set of targets; the metrics are stored in a time-series database (TSDB); the metrics are queried via PromQL; Alertmanager evaluates the alert rules; Grafana renders the dashboards. The pattern is: every workload exposes a `/metrics` endpoint in the Prometheus exposition format.
</details>

<details><summary>2. What are the exporters for AI infrastructure?</summary>
DCGM exporter (GPU utilisation, memory, temperature, ECC, Xid); cAdvisor (container CPU, memory, network, filesystem I/O); kube-state-metrics (Kubernetes object state); node exporter (host CPU, memory, disk, network); application exporter (application-specific metrics); inference engine exporter (Triton / vLLM / NIM metrics). One exporter per concern.
</details>

<details><summary>3. What is PromQL?</summary>
The query language for Prometheus. The basic shape is `metric_name{labels} operator value`. PromQL can aggregate (sum, avg, max, min), transform (rate, increase, irate), and join (on, group_left). The platform team's PromQL queries are the queries the on-call engineer runs during an incident.
</details>

<details><summary>4. What is a recording rule?</summary>
A pre-computed query that Prometheus evaluates on a schedule. The recording rule writes the result to a new time series; the dashboards read the pre-computed series; the on-call engineer sees the dashboard in seconds. Recording rules are how the platform team makes expensive queries affordable.
</details>

<details><summary>5. What is the on-call dashboard?</summary>
The single most important dashboard in the platform. The dashboard has eight panels: cluster p99 inference latency, inference error rate per model, GPU pool utilisation, GPU memory pressure, recent error logs, open incidents, cost per team this month, and model quality signals. The dashboard is the on-call engineer's home page.
</details>

<details><summary>6. What is the retention period trade-off?</summary>
Storage cost vs historical visibility. 30 days is the default for operational dashboards; 90 days for capacity planning; 1 year for the audit log. For long-term retention, use Thanos remote storage; the query layer merges recent and historical data.
</details>

<details><summary>7. What is the cardinality budget's enforcement mechanism?</summary>
The platform team's discipline. Every metric that the team adds must declare its label cardinality; the team rejects metrics whose cardinality exceeds the budget; the team publishes the cardinality budget on the platform's status page. The `prometheus_tsdb_head_series` metric is the signal that the budget is being exceeded.
</details>

<details><summary>8. What is the difference between Prometheus and Thanos?</summary>
Prometheus is the server that scrapes and stores recent metrics. Thanos is the long-term storage layer that Prometheus remote-writes to. The Thanos Querier merges recent data from Prometheus with historical data from object storage. The combination is what makes 90-day retention affordable.
</details>

<details><summary>9. What is the most common Prometheus failure mode?</summary>
OOM because of a high-cardinality label. A single metric with a label that has millions of unique values can OOM Prometheus; Prometheus stops ingesting; the dashboards go stale. The fix is the cardinality budget and the cardinality alert.
</details>

<details><summary>10. What is the TSDB?</summary>
The time-series database that Prometheus uses to store metrics. The TSDB has three components: the head block (recent data), the write-ahead log (WAL), and the compacted blocks (older data). The TSDB stores metrics on local disk; for long-term retention, Prometheus can remote-write to Thanos.
</details>

<details><summary>11. What is the W3C Trace Context's role in Prometheus?</summary>
Prometheus is not a tracing system; the W3C Trace Context is the standard for propagating trace context across services. Prometheus and Tempo (or Jaeger) are complementary; the metric exemplars link a metric to the traces that produced the metric.
</details>

<details><summary>12. What is the difference between a recording rule and an alert rule?</summary>
A recording rule pre-computes a query and writes the result to a new time series; the dashboards read the pre-computed series. An alert rule evaluates a query and fires an alert when the query breaches a threshold; Alertmanager sends the alert to PagerDuty. Recording rules are about making the dashboards fast; alert rules are about paging the on-call.
</details>

<details><summary>13. Why is the cardinality budget a platform-team discipline?</summary>
Because every label the team adds to a metric increases the cardinality. The platform team's choice of labels determines whether Prometheus can store the metrics and whether the dashboards can render the panels. A label with more than 1000 possible values is unsafe; the label should be dropped at the source, stored in a trace or log instead, or aggregated.
</details>

<details><summary>14. What is the most expensive PromQL query?</summary>
A query that scans a high-cardinality metric without a recording rule. The query is evaluated every dashboard load; the query takes seconds; the dashboard loads slowly. The fix is a recording rule that pre-computes the query every 30 seconds; the dashboard reads the pre-computed series; the dashboard loads in seconds.
</details>

<details><summary>15. What is the difference between a dashboard and a recording rule?</summary>
A dashboard is a Grafana JSON file that renders panels. A recording rule is a Prometheus configuration that pre-computes queries. The dashboard reads from the recording rule (fast) or from the raw metric (slow). The dashboard is the on-call's situational awareness; the recording rule is the platform team's performance optimisation.
</details>

<details><summary>16. What is the on-call dashboard's most important panel?</summary>
The cluster p99 inference latency panel. The panel answers the customer's question: "is the cluster meeting the SLO?". The panel is the first thing the on-call checks when paged; the panel is the first thing the customer sees when the cluster is degraded.
</details>

<details><summary>17. What is the difference between scrape_interval and scrape_timeout?</summary>
scrape_interval is how often Prometheus scrapes a target. scrape_timeout is how long Prometheus waits for the target to respond. The default scrape_interval is 1 minute; the default scrape_timeout is 10 seconds. For AI workloads, scrape_interval is 10-15 seconds; scrape_timeout is 10 seconds.
</details>

<details><summary>18. Why is the cardinality alert the most important alert?</summary>
Because a cardinality spike can OOM Prometheus; Prometheus OOM is a silent failure (Prometheus stops ingesting; the dashboards go stale; the on-call does not know). The cardinality alert catches the spike before Prometheus OOMs; the platform team fixes the metric; the cluster stays healthy.
</details>

<details><summary>19. What is the difference between the head block and the compacted blocks?</summary>
The head block is the recent data in memory; the compacted blocks are the older data on disk. The head block flushes to the write-ahead log on shutdown; the head block compacts to immutable blocks over time. The TSDB queries the head block and the compacted blocks as one logical time series.
</details>

<details><summary>20. What five questions should the metrics lab let you answer in five seconds each?</summary>
What is the current Prometheus scrape latency p99. What is the current TSDB head series count. What is the current inference p99 latency from the recording rule. What is the current cost per team this month from the recording rule. What is the current cardinality per metric. If any takes more than 30 seconds, the metrics stack is not yet a production service.
</details>

---

## Sources and review notes

- *Production Kubernetes* (`production-kubernetes`, Chapter 9). Source for the Prometheus architecture, the scrape configuration, the exporters, the RED method, and the operational patterns. Chapter 9 is approximately 9,200 words.
- NVIDIA Zero-to-Hero Volume 16 (`chapter-05-prometheus-grafana.md`). Source for the operational Prometheus + Grafana patterns, the cardinality discipline, and the on-call dashboard composition. The wording has been rewritten in the handbook's voice.
- NVIDIA Zero-to-Hero Volume 7 (`chapter-01-observability-stack-overview.md`). Source for the observability stack patterns and the deployment on Kubernetes.
- Prometheus and Grafana official documentation. Source for the API shapes, the configuration syntax, and the operator patterns.

### Cross-references to other handbook chapters

- Chapter 17.1 for the three pillars and the cardinality budget.
- Chapter 17.4 for the DCGM exporter in detail.
- Chapter 17.6 for the alerting and SLO patterns.
- Chapter 16.10 for the AI-specific monitoring pattern.

### Migrated from `nvidia-devops`

The Prometheus + Grafana operational patterns draw on Volume 16 chapter 5 and Volume 7 chapter 1. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The retention period table in Section 4.2 is a starting point; specific retention depends on the regulatory regime and the storage budget.
- The on-call dashboard panels in Section 3.2 are a starting point; specific panels depend on the team's operational discipline.
- The cardinality budget's 1000-value limit is a rule of thumb; specific limits depend on the cluster's memory budget.

### Not verified on live hardware

- The lab in Section 7 is **untested** against a live GKE cluster in this repository.
- The Prometheus, Grafana, and Thanos versions assumed in the lab should be pinned against the current releases before production use.
- The recording rules in the lab are illustrative; production rules depend on the workload.
