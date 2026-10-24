---
id: "c05-24"
title: "5.24 Observability for Kubernetes"
sidebar_label: "5.24 Observability for Kubernetes"
sidebar_position: 24
description: "Metrics, logs, traces and events for Kubernetes and GPU platforms: Prometheus architecture and operator, kube-state-metrics, cAdvisor, node-exporter, DCGM, alerting design (SLOs, burn rates), Alertmanager, log pipelines (Fluent Bit, Loki), OpenTelemetry tracing, dashboards, multi-tenant and long-term storage, cardinality and cost control"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 5.24 Observability for Kubernetes

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | kind/kubeadm; `helm`; kube-prometheus-stack; Loki; OpenTelemetry Collector; Grafana; optional DCGM exporter |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

A GPU platform is only as reliable as your ability to see inside it: a training job that silently runs at 40% of expected throughput because one node's NIC negotiated a lower speed, an inference service whose p99 latency doubles when KV-cache fills, a node whose GPU throws Xid errors for days before the job fails, a control plane slowed by a runaway controller. Observability turns these from mysteries into dashboards and alerts. The Kubernetes ecosystem has converged on Prometheus-compatible metrics, structured logs shipped to a central store, OpenTelemetry for traces, and Grafana for visualisation. This chapter explains the architecture, the exporters that matter, how to design alerts that are actionable, and how to scale and secure the stack, with GPU-specific signals (deeper treatment in Part 17).

## Prerequisites and outcomes

Needs 5.3, 5.9, 5.19. After this chapter you can:

- Describe the Prometheus data model and scrape architecture; install and operate kube-prometheus-stack (Prometheus Operator CRDs: ServiceMonitor, PodMonitor, PrometheusRule, Probe, AlertmanagerConfig).
- Identify the key metric sources (kube-state-metrics, cAdvisor/kubelet, node-exporter, API server/etcd/scheduler/controller metrics, CoreDNS, ingress, DCGM exporter, application metrics) and the most useful PromQL for each.
- Design alerts and SLOs: symptom-based paging, multiwindow burn-rate alerts, severity routing, inhibition, runbooks; avoid alert fatigue.
- Build log pipelines (node agents, structured logging, Loki/Elastic) and trace pipelines (OpenTelemetry Collector, Tempo/Jaeger), and correlate across signals (exemplars, trace IDs).
- Use Kubernetes events and audit logs effectively.
- Scale and secure observability: federation/remote write (Thanos/Mimir/VictoriaMetrics), multi-tenancy, retention, cardinality control, cost.
- Build dashboards for cluster, node, GPU, job and service health.

## 1. The observability signals

| Signal | Question answered | Kubernetes sources |
|---|---|---|
| **Metrics** | How is the system behaving over time? (rates, errors, durations, saturation) | Prometheus scraping `/metrics` endpoints |
| **Logs** | What happened (discrete events with context)? | Container stdout/stderr, node logs (journald), audit logs |
| **Traces** | Where did time go across services for a request? | OpenTelemetry/Jaeger/Tempo |
| **Events** | What did the control plane do? (Scheduled, Pulled, Killing, FailedMount) | `kubectl get events`, Event objects (1 h TTL), event exporters |
| **Profiles** | Where is CPU/memory spent in code? | Pyroscope/Parca, `py-spy`, Nsight (Part 10) |
| **Health checks/synthetics** | Does it work from the outside? | Blackbox exporter, probes, synthetic requests |

Methodologies: **RED** (Rate, Errors, Duration) for request-driven services; **USE** (Utilisation, Saturation, Errors) for resources (CPU, memory, disk, network, GPU); **Four Golden Signals** (latency, traffic, errors, saturation); for ML: **throughput (tokens/s, samples/s), step time, loss/gradient health, MFU, checkpoint age, data-loader wait**.

## 2. Prometheus and the Operator

### Prometheus model

Time series identified by metric name + labels (`http_requests_total{job="api",code="200"}`); types: **counter** (monotonic; use `rate()`/`increase()`), **gauge**, **histogram** (cumulative buckets; `histogram_quantile`), **summary**. Pull model: Prometheus scrapes targets at an interval (15–30 s typical), stores in a local TSDB (2 h blocks, compaction, retention by time/size), evaluates **recording and alerting rules**, and sends alerts to **Alertmanager**. Service discovery uses the Kubernetes API (`kubernetes_sd_configs`: pods, endpoints, services, nodes, ingresses) plus relabelling to choose targets and attach labels.

### kube-prometheus-stack

Helm chart bundling Prometheus Operator, Prometheus, Alertmanager, Grafana, kube-state-metrics, node-exporter, default dashboards and rules for Kubernetes components.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kps prometheus-community/kube-prometheus-stack -n monitoring --create-namespace \
  --set prometheus.prometheusSpec.retention=15d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=200Gi \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.ruleSelectorNilUsesHelmValues=false
```

Operator CRDs:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata: { name: vllm, namespace: serving, labels: { release: kps } }
spec:
  selector: { matchLabels: { app: vllm } }              # Services with these labels
  namespaceSelector: { matchNames: [serving] }
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
      relabelings:
        - { sourceLabels: [__meta_kubernetes_pod_node_name], targetLabel: node }
      metricRelabelings:
        - { sourceLabels: [__name__], regex: "vllm:(num_requests_.*|gpu_cache_usage_perc|time_to_first_token_seconds.*)", action: keep }   # keep only needed series
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata: { name: gpu-alerts, namespace: monitoring, labels: { release: kps } }
spec:
  groups:
    - name: gpu.rules
      interval: 30s
      rules:
        - record: node:gpu_util:avg
          expr: avg by (node) (DCGM_FI_DEV_GPU_UTIL)
        - alert: GPUXidError
          expr: increase(DCGM_FI_DEV_XID_ERRORS[10m]) > 0
          for: 0m
          labels: { severity: critical, team: platform }
          annotations:
            summary: "Xid {{ $value }} on {{ $labels.Hostname }} GPU {{ $labels.gpu }}"
            runbook_url: https://runbooks.example.com/gpu-xid
```

`PodMonitor` for pod-level endpoints without Services; `Probe` for blackbox targets; `AlertmanagerConfig` for namespaced routing; `ScrapeConfig` for static/external targets. Selectors on Prometheus (`serviceMonitorSelector`) determine which monitors it picks up (the `release: kps` label trap).

### Key exporters and sources

| Source | Metrics | Notes |
|---|---|---|
| **kubelet / cAdvisor** (`/metrics/cadvisor`) | `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`, `container_cpu_cfs_throttled_periods_total`, `container_network_*`, `container_fs_*`, `container_oom_events_total` | Per container; the basis of `kubectl top` and capacity |
| **kubelet** (`/metrics`, `/metrics/probes`, `/metrics/resource`) | Pod start durations, PLEG, runtime ops, volume stats, evictions, cert TTL | 5.9 |
| **kube-state-metrics (KSM)** | State of API objects: `kube_pod_status_phase`, `kube_pod_container_status_restarts_total`, `kube_pod_container_resource_requests/limits`, `kube_node_status_condition`, `kube_deployment_status_replicas_available`, `kube_job_status_failed`, `kube_persistentvolumeclaim_status_phase`, `kube_horizontalpodautoscaler_*` | Joins with cAdvisor for efficiency; supports custom resource state metrics for CRDs (Kueue, jobs) |
| **node-exporter** | CPU, memory, disk, filesystem, network, load, `node_pressure_*` (PSI), softnet, conntrack, hwmon temperatures, `node_infiniband_*` | DaemonSet; mount host paths; collectors configurable |
| **API server** | `apiserver_request_total`, `apiserver_request_duration_seconds`, `apiserver_flowcontrol_*`, `etcd_request_duration_seconds`, `apiserver_admission_*` | 5.5 |
| **etcd** | `etcd_server_*`, `etcd_disk_wal_fsync_duration_seconds`, `etcd_mvcc_db_total_size_in_bytes` | Scrape with client certs |
| **scheduler / controller-manager** | `scheduler_pending_pods`, `scheduler_schedule_attempts_total`, `workqueue_*`, `rest_client_requests_total` | |
| **CoreDNS** | `coredns_dns_requests_total`, `coredns_dns_responses_total{rcode}`, duration | 5.11 |
| **kube-proxy / CNI** | `kubeproxy_sync_proxy_rules_duration_seconds`, Cilium/Calico metrics, Hubble | 5.10, 5.14 |
| **Ingress/Gateway** | request rates, latencies, status codes, upstream health | 5.12 |
| **DCGM exporter** | `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_FB_USED`, `DCGM_FI_DEV_POWER_USAGE`, `DCGM_FI_DEV_GPU_TEMP`, `DCGM_FI_DEV_SM_CLOCK`, `DCGM_FI_DEV_XID_ERRORS`, `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL`, `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`, `DCGM_FI_PROF_DRAM_ACTIVE`, NVLink bandwidth/error counters | Profile metrics need DCGM profiling enabled; labels `gpu`, `UUID`, `modelName`, `Hostname`, `pod`, `namespace` (via pod-resources mapping) |
| **Network/RDMA** | `node_infiniband_*`, `ibstat` exporters, UFM exporter, switch telemetry (gNMI/SNMP) | Part 12, Part 17 |
| **Storage** | CSI driver metrics, `kubelet_volume_stats_*`, filesystem exporters (Lustre/WEKA/Ceph), S3 gateway metrics | |
| **Applications** | Framework metrics: PyTorch/Lightning custom (`train_step_seconds`, `tokens_per_second`), vLLM/Triton/TGI endpoints, Ray metrics | Instrument with `prometheus_client`/OpenTelemetry metrics |
| **Blackbox probes** | HTTP/TCP/ICMP/DNS from inside/outside | Synthetic checks for endpoints and DNS |
| **Node problem detector** | Conditions/events for kernel/runtime/hardware problems | Exposes as node conditions → KSM metric |

### Essential PromQL

```promql
# Node and pod health
sum(kube_node_status_condition{condition="Ready",status="true"} == 0)                                # NotReady nodes
sum by (namespace, pod) (rate(kube_pod_container_status_restarts_total[15m])) > 0.01                  # restarting pods
sum by (reason) (kube_pod_container_status_last_terminated_reason{reason="OOMKilled"})                # OOMs
count by (phase) (kube_pod_status_phase == 1)

# Pending pods and reasons (scheduler)
sum(scheduler_pending_pods{queue="unschedulable"})
sum by (namespace) (kube_pod_status_phase{phase="Pending"} == 1)

# CPU throttling and saturation
sum by (namespace,pod,container) (rate(container_cpu_cfs_throttled_periods_total[5m]) / rate(container_cpu_cfs_periods_total[5m])) > 0.25
sum by (node) (rate(node_cpu_seconds_total{mode!="idle"}[5m])) / count by (node) (node_cpu_seconds_total{mode="idle"})

# Memory
container_memory_working_set_bytes{container!=""} / on(namespace,pod,container) kube_pod_container_resource_limits{resource="memory"} > 0.9
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.1

# API server
histogram_quantile(0.99, sum by (le,verb) (rate(apiserver_request_duration_seconds_bucket{verb!~"WATCH|CONNECT"}[5m])))
sum(rate(apiserver_request_total{code=~"5.."}[5m])) / sum(rate(apiserver_request_total[5m]))
histogram_quantile(0.99, rate(etcd_disk_wal_fsync_duration_seconds_bucket[5m])) > 0.01

# GPU
avg by (Hostname, gpu) (DCGM_FI_DEV_GPU_UTIL)
sum by (namespace) (kube_pod_container_resource_requests{resource="nvidia_com_gpu"}) / ignoring(namespace) group_left sum(kube_node_status_allocatable{resource="nvidia_com_gpu"})   # allocation fraction
avg_over_time(DCGM_FI_PROF_PIPE_TENSOR_ACTIVE[5m]) < 0.2 and on(pod) kube_pod_container_resource_requests{resource="nvidia_com_gpu"} > 0     # allocated but tensor cores idle
increase(DCGM_FI_DEV_XID_ERRORS[1h]) > 0
DCGM_FI_DEV_GPU_TEMP > 85
```

## 3. Alerting design

### Principles

1. **Page on symptoms, ticket on causes.** Page when users or SLOs are affected (API errors, inference latency/availability, jobs failing to start, many nodes lost). Notify (ticket/chat) for causes and capacity warnings (disk 80% full, certificate in 14 days).
2. **Every alert is actionable**: clear summary (what/where), severity, owner/team, runbook link, dashboard link, `for:` duration to avoid flapping; delete alerts nobody acts on.
3. **SLO-based alerting** with **multiwindow, multi-burn-rate** rules (Google SRE workbook): e.g., page when 2% of a 30-day error budget burns in 1 hour (burn rate 14.4) and in 5 minutes; ticket on 5% in 6 hours (burn 6) and 30 minutes. Use recording rules for SLI ratios.
4. **Routing and noise control** in Alertmanager: group by `alertname, cluster, namespace`; `group_wait`, `group_interval`, `repeat_interval`; **inhibition** (suppress downstream alerts when a node or the control plane is down); **silences** for maintenance; time-based routing (office hours for low severity); route by labels to teams (PagerDuty/Opsgenie/Slack/email/webhooks).
5. **Watchdog / dead man's switch**: an always-firing alert to an external service proves the pipeline works.
6. **Alert on the absence** of data (`absent()`, `up == 0`) for critical exporters; alert on observability stack health (Prometheus WAL, scrape failures, rule evaluation failures, disk).
7. **Test alerts** (`promtool test rules`, synthetic failures) and review them after incidents.

```yaml
# SLO example: inference availability (non-5xx ratio) 99.5% over 30d
- record: slo:inference_error_ratio:rate5m
  expr: sum(rate(gateway_requests_total{route="chat",code=~"5.."}[5m])) / sum(rate(gateway_requests_total{route="chat"}[5m]))
- alert: InferenceErrorBudgetBurnFast
  expr: slo:inference_error_ratio:rate1h > (14.4 * 0.005) and slo:inference_error_ratio:rate5m > (14.4 * 0.005)
  labels: { severity: page }
  annotations: { summary: "Burning 2% of monthly error budget per hour", runbook_url: https://runbooks.example.com/inference-errors }
```

### GPU-fleet specific alerts

Node-level hardware (page/ticket by severity): Xid errors (esp. 79 fallen off bus, 48 DBE, 74 NVLink), uncorrectable ECC, retired pages pending, GPU temperature/power throttling (`DCGM_FI_DEV_CLOCK_THROTTLE_REASONS`), NVLink errors/down links, PCIe replay counters, lost GPU count vs expected, `nvidia-smi` hang; network (IB/RoCE link down, symbol errors, PFC storms, ECN marks, port speed lower than expected); storage (mount errors, throughput drop); job-level (training throughput below baseline, loss NaN, step-time skew across ranks (stragglers), checkpoint failing or stale); platform (queue wait time p95, pending reasons, GPU allocation efficiency). Details in Part 17.

## 4. Logs

### Architecture

Containers write stdout/stderr → runtime files `/var/log/pods/...` (5.9) → **node agent** DaemonSet (Fluent Bit, Vector, Promtail/Grafana Alloy, Fluentd, Filebeat) tails files, parses (JSON/CRI), enriches with Kubernetes metadata (namespace, pod, labels, node), filters/redacts, and ships to a backend: **Loki** (label-indexed, cheap, object-storage backed), **Elasticsearch/OpenSearch** (full-text), **ClickHouse**, cloud logging (Cloud Logging, CloudWatch), or Splunk. Node-level logs: journald (`kubelet`, `containerd`, kernel `dmesg` with Xid messages), audit logs from API server, and application files in volumes.

Best practices:

- **Structured JSON logs** with consistent fields (`timestamp`, `level`, `msg`, `trace_id`, `request_id`, `job`, `rank`), not free text; avoid multi-line stack traces (or use multiline parsing).
- **Control volume**: training frameworks can log per step per rank: sample/aggregate, send metrics instead of logs for numeric series, set log levels, rotate (kubelet `containerLogMaxSize`), drop noisy lines at the agent.
- **Labels in Loki** must be low-cardinality (namespace, app, container, cluster); put high-cardinality data in the log line and use LogQL filters/parsers.
- **Retention & tiering**: hot (days) in the log store, cold in object storage; compliance retention for audit logs.
- **Security**: logs can contain secrets/PII; redact at the agent; RBAC and tenant separation (Loki multi-tenancy `X-Scope-OrgID`); protect access to node logs.
- **Correlation**: include trace IDs; use Grafana Explore to jump between metrics, logs and traces; Loki `derived fields`.
- **Kubernetes events** are not logs: export with `kubernetes-event-exporter` or Grafana Alloy `loki.source.kubernetes_events` to retain beyond 1 hour; alert on repeated `FailedScheduling`, `FailedMount`, `BackOff`, `Unhealthy`, `NodeNotReady`.

```yaml
# Fluent Bit essentials (ConfigMap excerpt)
[INPUT]
    Name tail
    Path /var/log/containers/*.log
    multiline.parser cri
    Tag kube.*
    Mem_Buf_Limit 50MB
    Skip_Long_Lines On
[FILTER]
    Name kubernetes
    Match kube.*
    Merge_Log On
    Keep_Log Off
    K8S-Logging.Parser On
[FILTER]
    Name grep
    Match kube.*
    Exclude log health(z)?
[OUTPUT]
    Name loki
    Match kube.*
    Host loki-gateway.monitoring
    Labels job=fluentbit, namespace=$kubernetes['namespace_name'], pod=$kubernetes['pod_name'], container=$kubernetes['container_name']
```

LogQL examples: `{namespace="training"} |= "NCCL WARN"`; `sum by (pod) (rate({namespace="serving"} |= "ERROR" [5m]))`; `{app="vllm"} | json | latency_ms > 2000`.

## 5. Traces and OpenTelemetry

**OpenTelemetry (OTel)** standardises telemetry: SDKs/auto-instrumentation produce traces/metrics/logs; the **OpenTelemetry Collector** (agent DaemonSet and/or gateway Deployment) receives (OTLP), processes (batch, memory limiter, attributes, tail sampling, k8sattributes enrichment), and exports to backends (Tempo, Jaeger, Prometheus remote write, Loki, cloud APIs). The **OpenTelemetry Operator** manages Collector instances and auto-instruments workloads via annotations (`instrumentation.opentelemetry.io/inject-python: "true"`).

For AI services, traces show: gateway → auth → router → model server → tokenizer/KV-cache/GPU kernel spans, retrieval (vector DB) latency in RAG pipelines, tool calls in agent workflows; LLM-specific observability (OpenLLMetry, Langfuse, Arize Phoenix, LangSmith) adds prompt/response/token/cost spans. Propagate W3C `traceparent` through gateways and meshes; sample intelligently (head sampling for volume, tail sampling to keep errors and slow traces); avoid storing prompts/PII in spans without policy.

## 6. Dashboards

Grafana (provisioned from Git; dashboards-as-code with Jsonnet/Grafonnet/Terraform). Recommended set:

1. **Cluster overview**: node readiness, pod phases, pending/unschedulable, API latency/errors, etcd health, scheduler queue, certificate expiry, GitOps sync status.
2. **Capacity & allocation**: allocatable vs requested vs used for CPU/memory/GPU per pool/namespace; fragmentation (largest free GPU block); quota usage; queue depth/wait (Kueue metrics).
3. **Node/GPU health**: per-node GPU utilisation/memory/power/temp/clocks, throttle reasons, ECC/Xid timeline, NVLink/PCIe errors, NIC throughput/errors, disk/inode; heatmaps across the fleet to spot outliers (one hot or one slow GPU stands out).
4. **Training job view**: per-job GPU utilisation and tensor activity, step time, tokens/s, loss, data-loader wait, checkpoint duration/age, per-rank skew, network bandwidth per node; links to logs and pods.
5. **Inference service view (RED + saturation)**: RPS, error rate, TTFT/ITL/latency percentiles, queue depth, batch size, KV-cache usage, GPU util/SM activity, replicas vs desired, cold starts, per-model/tenant breakdown.
6. **Platform/tenant view**: GPU-hours by team, utilisation vs allocation, idle waste, budget burn.
7. **Network & storage**: CoreDNS, ingress, CNI drops, conntrack; PVC usage, CSI latency, storage throughput.
8. **Observability stack health**: Prometheus ingestion/series count/cardinality, scrape failures, rule eval time, Alertmanager notifications, Loki ingestion/query errors, storage growth.

Design rules: top-level SLO panels first; drill-down links; consistent time ranges and variables (cluster, namespace, node, job); units and thresholds; avoid walls of graphs; annotate deployments and maintenance events.

## 7. Scaling, retention and cost

- **Cardinality** is the main scaling issue: every unique label set is a series (memory ~ a few KB each). Avoid unbounded labels (user IDs, request IDs, full URLs, pod UIDs in app metrics); `metricRelabelings` drop heavy series; check `topk(10, count by (__name__)({__name__=~".+"}))`; per-pod histograms with many buckets multiply; DCGM exports many fields per GPU: restrict the counters CSV to what you use.
- **Prometheus sizing**: roughly 1–2 bytes/sample on disk, memory dominated by head series (e.g., 1M series ≈ several GB); shard by scrape target (Prometheus Operator `shards`) or by function (separate Prometheus for infrastructure, GPU and applications); use `agent` mode + remote write for edge clusters.
- **Long-term storage and global view**: Thanos (sidecar/receive, object storage, global querier, compaction/downsampling), Grafana Mimir, Cortex, VictoriaMetrics (single/cluster), or managed Prometheus (GMP, AMP). Multi-cluster: each cluster runs Prometheus (agent) → remote write to a central TSDB with `cluster` external label; central Alertmanager/ruler for global rules.
- **High availability**: two Prometheus replicas scraping identically with different external labels (replica), deduplicated by Thanos/Mimir queriers; HA Alertmanager cluster (gossip); persistent volumes on fast disks; WAL protection.
- **Retention**: local 7–15 days, remote 6–13 months with downsampling (5 m / 1 h); logs 7–30 days hot; traces 3–7 days with tail sampling; audit logs per compliance. Estimate costs: series × samples/s × retention; logs GB/day × retention.
- **Multi-tenancy**: tenant IDs in Mimir/Loki/Tempo; Grafana orgs/teams/folders with RBAC; label-based enforcement (prom-label-proxy) so teams only see their namespaces; separate datasources per tenant for strict isolation.
- **Security**: TLS and auth on metrics endpoints where exposed (kube-rbac-proxy, ServiceMonitor `tlsConfig`/`bearerTokenFile`), NetworkPolicy to allow scraping (monitoring namespace → pods, node ports 9100/9400/10250), secure Grafana (SSO, no anonymous), restrict Alertmanager/Prometheus UIs, protect against metric/label injection by tenants, and keep the monitoring stack's own credentials minimal.
- **Reliability of the monitoring stack**: run it with priority, resource requests, anti-affinity, outside the failure domain it watches where possible (a separate management cluster or external SaaS for the critical alerting path), with a Watchdog.

## 8. Practical diagnosis flows

```text
Job slow →  Grafana job view: GPU util low?  yes → data-loader wait / storage throughput / CPU throttling (cAdvisor) / network
                                          no  → comms bound? NIC throughput vs expected, NCCL logs, step-time skew across ranks → straggler node (GPU throttle, ECC, PCIe)
Pods Pending → pending reasons event metric + scheduler_pending_pods; quota/queue (Kueue), node capacity, taints
Latency up → gateway RED, queue depth, KV-cache %, GPU SM activity, recent deploy annotation, node noisy neighbour (CPU throttle), DNS latency
API slow → apiserver_request_duration by verb/resource, APF queues, etcd fsync, top clients (audit), webhook latency
Node flapping → NotReady condition history, kubelet PLEG, runtime errors, disk pressure, kernel logs (Loki: Xid), temperature
```

## 9. Lab (untested)

1. **Install the stack**: kube-prometheus-stack with persistent storage; explore default dashboards and rules; find a control-plane metric for each component; confirm Watchdog alert is firing.
2. **ServiceMonitor**: instrument a small FastAPI app (3.7) with `prometheus-fastapi-instrumentator`; create Service + ServiceMonitor; verify the target, labels, and queries; fix the `release` label mismatch trap on purpose.
3. **PromQL drills**: write the queries in section 2 for your cluster; build recording rules; test with `promtool test rules` using synthetic series.
4. **GPU metrics**: deploy the DCGM exporter (or the GPU Operator's), enable profiling fields, customise the counters CSV; build a per-pod GPU panel using the pod-resources mapping; simulate Xid events (or use `dcgmi` health injection in lab) and fire the alert.
5. **Alerting**: implement an SLO alert pair (fast/slow burn) for a synthetic service; trigger failures with fault injection; test routing, grouping, inhibition (node down inhibits pod alerts), silences; deliver to a webhook receiver; write the runbook.
6. **Logs**: deploy Loki + Promtail/Alloy or Fluent Bit; ship container logs, journald and (if allowed) audit logs; build LogQL queries for NCCL warnings, OOM kills and Xid kernel messages; create a log-based alert.
7. **Events**: export Kubernetes events to Loki; build an "events timeline" dashboard; alert on repeated `FailedScheduling`/`FailedMount`.
8. **Tracing**: deploy the OTel Collector and Tempo; auto-instrument the FastAPI app and a client; view a trace; add exemplars linking metrics to traces; configure tail sampling for errors.
9. **Cardinality incident**: introduce a high-cardinality label (user id) in app metrics; watch series growth and Prometheus memory; find it with TSDB status page; fix via relabeling and code.
10. **Scale-out**: add remote write to a central Mimir/VictoriaMetrics/Thanos (lab) with external `cluster` labels; query across two clusters; compare costs and retention settings.
11. **Dashboards-as-code**: provision a dashboard via ConfigMap/Grafana provisioning from Git; add deployment annotations; build the training job and inference views.
12. **Failure drills**: kill Prometheus (PVC retained) and check recovery; fill disk; stop an exporter and verify `absent`/`up==0` alerts; make Alertmanager unreachable and confirm the Watchdog/DMS alerts externally.
13. **Clean up**.

Mark tested only after execution.

## 10. Common mistakes

- Dashboards without alerts and alerts without runbooks; paging on CPU % or single-pod restarts.
- High-cardinality labels and per-request IDs in metrics; scraping everything at 5 s.
- Relying on GPU utilisation as the only GPU health metric; no Xid/ECC/throttle alerts; no per-pod mapping.
- Single Prometheus with no HA/remote storage; monitoring in the same failure domain as the system; no Watchdog.
- Logs unstructured and unbounded; training frameworks logging every step from every rank; secrets in logs.
- Trace sampling at 100% in production, or no sampling policy; prompts/PII in spans.
- Ignoring Kubernetes events (expire in an hour) and audit logs.
- Not versioning dashboards/rules; manual edits lost on upgrade.
- ServiceMonitor selectors not matching the Prometheus instance, so nothing is scraped.
- No tenant separation in shared monitoring.

## 11. Interview angles

- "Explain Prometheus's pull model, data model, and how it discovers Kubernetes targets." 
- "What does kube-state-metrics provide vs cAdvisor vs node-exporter?" 
- "How do you alert on an SLO? Explain multi-window burn-rate alerts." 
- "What GPU metrics and alerts would you set up for a training fleet?" 
- "How do you handle high cardinality?" 
- "How do you design logging for a 1,000-GPU job?" 
- "How would you scale Prometheus across many clusters?" 
- "How do you diagnose a slow training job using observability data?" 

## 12. Checkpoint questions (35)

1. Prometheus collection model? **A:** Pull (scrape).
2. Counter function? **A:** `rate()`/`increase()`.
3. Histogram quantile function? **A:** `histogram_quantile`.
4. Operator CRD for scraping Services? **A:** ServiceMonitor.
5. For Pods? **A:** PodMonitor.
6. For rules? **A:** PrometheusRule.
7. kube-state-metrics shows? **A:** Object state from the API.
8. cAdvisor shows? **A:** Container resource usage.
9. node-exporter shows? **A:** Host metrics.
10. DCGM exporter shows? **A:** GPU metrics.
11. Throttle metric? **A:** `container_cpu_cfs_throttled_periods_total`.
12. OOM metric? **A:** `container_oom_events_total`/lastTerminatedReason.
13. USE method? **A:** Utilisation, Saturation, Errors.
14. RED method? **A:** Rate, Errors, Duration.
15. Page on? **A:** Symptoms affecting users/SLOs.
16. Burn-rate alert idea? **A:** Alert on budget consumption speed over windows.
17. Alertmanager features? **A:** Grouping, routing, inhibition, silences.
18. Watchdog purpose? **A:** Prove alert pipeline alive.
19. Log agent examples? **A:** Fluent Bit, Vector, Promtail/Alloy.
20. Loki labels advice? **A:** Low-cardinality.
21. Event TTL? **A:** ~1 hour.
22. OTel Collector roles? **A:** Receive, process, export telemetry.
23. Trace propagation header? **A:** W3C `traceparent`.
24. Tail sampling? **A:** Keep traces based on outcome (errors/slow).
25. Cardinality means? **A:** Number of unique series.
26. Remote storage options? **A:** Thanos, Mimir, VictoriaMetrics.
27. HA Prometheus approach? **A:** Replicas + dedup at query layer.
28. Multi-tenancy tool? **A:** Mimir/Loki tenants, label proxy.
29. Metric for API latency? **A:** `apiserver_request_duration_seconds`.
30. Metric for etcd disk? **A:** WAL fsync duration.
31. Pending pods metric? **A:** `scheduler_pending_pods`.
32. GPU health key signal? **A:** Xid, ECC, throttle reasons.
33. Tensor activity metric? **A:** `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`.
34. Why straggler detection? **A:** One slow rank slows the job.
35. Why separate monitoring failure domain? **A:** Alerts must survive the outage.

## 13. Sources and review notes

**Written in original words.** Principal sources:

- Josh Rosso, Rich Lander, Alex Brand and John Harris, *Production Kubernetes* (chapter 9 on observability: metrics, logs, traces, alerting).
- The author's `nvidia-devops` repository, volume 03 (control plane metrics, API Priority and Fairness metrics) and volume 10 (GPU/cluster operations).
- Prometheus, Prometheus Operator, kube-prometheus, Grafana Loki/Tempo/Mimir, OpenTelemetry, Thanos and NVIDIA DCGM exporter documentation; the Google SRE Workbook for SLO alerting.
- Examples are the author's constructions.

**Flagged for verification before publishing:** metric names across exporter and Kubernetes versions (DCGM field names, vLLM metric names, scheduler/APF metrics), Helm values, Operator CRD fields, Loki/Alloy configuration syntax, burn-rate multipliers for your SLO windows, and every query/manifest; all labs are **untested**.
