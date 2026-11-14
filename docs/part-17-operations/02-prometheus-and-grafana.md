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
| Cross-references | Chapter 17.1 (Observability foundations); Chapter 17.4 (DCGM exporter); Chapter 17.6 (Alerting and SLOs); Chapter 16.10 (Monitoring and drift) |
| Coverage file | `planning/coverage/chapters/17-02.md` |
| Claim & number ledger | `planning/ledgers/17-02.md` |

## Why this matters for AI infrastructure

Imagine you are the on-call engineer at two in the morning. The inference service has slowed down, and you have a few minutes to find out why. You open the metrics first, because metrics show how much of something is happening over time. Chapter 17.1 named the three pillars of observability. This chapter covers the first one, metrics, which answer the question of how much and how fast.

Prometheus is the de facto standard for collecting AI infrastructure metrics. "De facto standard" means that most of the industry uses it, even though no official body chose it. Grafana is the de facto standard for the dashboards that read them. Together, they support every other operational chapter in this part. You can think of Prometheus as the collector and storage, and Grafana as the window you look through.

The Prometheus and Grafana stack sits on the critical path of every alert, every SLO, and every capacity model. A misconfigured stack either pages the on-call at the wrong moment or stays silent while the cluster is down. That is why the platform team runs the stack as a production service, with SLOs, observability, and a runbook.

```text
Why Prometheus + Grafana is on the critical path (background reading: NVIDIA Zero-to-Hero volume 16; Production Kubernetes; the figures below are examples, not quotations):
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

Three operational realities make this chapter a platform-team concern, not only a data-science concern:

1. Prometheus is on the hot path of every alert. Chapter 16.14 measures every SLO with Prometheus, and Chapter 17.6 fires every alert from it. Prometheus's reliability is the platform's reliability.
2. Grafana is the on-call engineer's home page. Your situational awareness during an incident is only as good as the dashboards. A poor dashboard means a slower response.
3. Prometheus enforces the cardinality budget from Chapter 17.1. A label with too many values can run Prometheus out of memory. Cardinality discipline is what keeps Prometheus alive.

**Before a team runs an AI workload on a cluster, the cluster needs a working Prometheus and Grafana stack.** Check for reliable scrapes, useful dashboards, and enforced cardinality budgets before the first workload arrives. A cluster without them is a cluster nobody can debug. If you skip this check, the first real incident becomes the first time anyone learns that a scrape has been failing for a week.

## Prerequisites and outcomes

### Prerequisites

Picture a teammate who reads this chapter without having read Chapter 17.1, and then cannot tell what a cardinality budget is. Reading in order saves that confusion. The two chapters share a vocabulary, and a term that is defined once in Chapter 17.1 is used without redefinition here. Read Chapter 17.1 first. It explains the three pillars and the cardinality budget, and this chapter depends on both.

### Outcomes

Picture a new platform engineer who must keep this stack alive through a release. This chapter covers how to set up Prometheus scrape jobs for your exporters, including DCGM, cAdvisor, kube-state-metrics, and your application exporters. It shows how to write recording rules and alerting rules in PromQL for GPU utilization, KV cache occupancy, and NCCL collective latency. It then turns to Grafana dashboards that answer the on-call engineer's questions quickly, and to the storage and retention side, which covers TSDB compaction, the retention period, and the disk budget. The last part runs the whole stack on GKE with SLOs, observability, and a runbook.

---

## 1. Prometheus

### 1.1 The Prometheus architecture

Suppose a GPU node runs hot, and you want its temperature on a dashboard within a minute. Something has to collect that number, store it, and answer questions about it. *Production Kubernetes*, chapter 9, walks through how Prometheus does this. Prometheus is pull-based. The server scrapes metrics from a set of targets, stores them in its time-series database, the TSDB, and answers queries written in PromQL.

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

Every workload exposes a `/metrics` endpoint in the Prometheus exposition format. Prometheus scrapes that endpoint every N seconds and stores the samples in its TSDB. Grafana queries the TSDB, and Alertmanager evaluates the alert rules.

Notice that the arrows point one way. Applications never push metrics anywhere. They only expose them, so each application needs to know the format and nothing about the metrics system behind it. A sample is one measured value with its timestamp, and a series is the full run of samples for one metric with one set of labels. When you read the diagram, follow the arrows from each exporter into the server, and then out to the two consumers.

Picture a scrape that fails at night. Prometheus does not stop the world when one target stops answering. It keeps scraping the others, and it records the failure as a value of the up series for that target. A down value means the last scrape failed. That is why an up alert is one of the first alerts a new stack should have, and why the scrape job is worth reading before you read anything else in the stack.

### 1.2 Scrape configuration

Picture a new GPU node that joins the cluster on a Tuesday afternoon. Nobody edits a config file by hand, and the node's GPUs still show up on the dashboard by the next scrape. The scrape configuration is a YAML file that tells Prometheus which targets to scrape and how to label them. This file relies on Kubernetes service discovery, so new pods join the scrape without a manual edit. Relabel rules then add the labels your team needs, such as the GPU product and the node name.

```yaml
# code/part17/prometheus_scrape.yaml
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

Use service discovery to find the targets, and use relabel rules to add labels.

Think of service discovery as a phone book that updates itself. Each time a pod starts or stops, the list of endpoints changes, and Prometheus reads the new list on its next refresh. You never write the pod's address into the file. The relabel rules then decide which labels the series will carry, so a dashboard can filter by GPU product or by node name without any extra work from the application team. The fields `__metrics_path__` and `__address__` point Prometheus at the exporter's endpoint. Each job name groups one kind of target, so you can see at a glance which group is failing. Read the file one job at a time, and ask what each job is meant to find.

### 1.3 The exporters for AI infrastructure

Prometheus cannot read a GPU by itself. An exporter reads the hardware or software and publishes the numbers in the Prometheus format. Each exporter answers a different question. The DCGM exporter shows what the GPUs are doing, and cAdvisor shows what each container uses. Picture an incident where a GPU is idle but the container next to it is busy. You need both exporters to see that the container is starved of data and not of compute.

*Production Kubernetes*, chapter 9, and NVIDIA Zero-to-Hero Volume 16, chapter 5, walk through these exporters.

| Exporter | What it exposes | Where it runs |
|---|---|---|
| **DCGM exporter** | GPU utilisation, memory, temperature, ECC, Xid | One per GPU node (DaemonSet) |
| **cAdvisor** | Container CPU, memory, network, filesystem I/O | One per node (built into kubelet) |
| **kube-state-metrics** | Kubernetes object state (pods, nodes, deployments) | One Deployment |
| **Node exporter** | Host CPU, memory, disk, network | One per node (DaemonSet) |
| **Application exporter** | Application-specific metrics | Sidecar per application |
| **Inference engine exporter** | Triton / vLLM / NIM metrics | Built into the engine |

*AI Systems Performance Engineering*, chapter 16, adds two limits. The DCGM exporter does not expose per-link bandwidth on every platform by default. Low-level counters, such as L1 and L2 activity and occupancy, come from Nsight Compute or CUPTI instead. A limit like that is easy to miss, so check the exporter's documentation before you promise a panel to a team.

Choose each exporter by the question you need answered, not by habit. If a number you need is missing, check the exporter's limits first.

Consider a simple case. A team wants to know why one inference pod is slow. The application exporter shows the request latency, and the DCGM exporter shows whether the GPU behind that pod was busy at the same moment. cAdvisor shows whether the container was short of CPU or memory. Each exporter answers one part of the question, and none of them answers all of it. Read the question first, then pick the exporters that cover it.

### 1.4 What Prometheus does for the platform

Picture a platform team that learns about an outage from a customer's email. Metrics and alerting services are vital to the usability of a platform. Metrics plot measured data on a timeline, and divergences on that timeline point to undesirable or unexpected behavior. They show whether applications are behaving as you expect, and they suggest how to remedy a problem. Most critically, they give you measurements to alert on. Warnings of impending failures, ideally before users notice, give you a chance to avert downtime or minimize it.

Prometheus is an open source metrics tool, and it has become the prevalent open source solution for Kubernetes-based platforms. Control plane components expose Prometheus metrics, and virtually every production cluster uses exporters to collect metrics from things like the underlying nodes. For this reason, enterprise systems such as Datadog, New Relic, and VMware Tanzu Observability can consume Prometheus metrics. Because so many tools read the same format, the choice of Prometheus does not lock you into one vendor.

Prometheus provides five core functions:

- It collects metrics from targets with its scraping model.
- It stores the metrics in a time-series database.
- It sends alerts, usually to Alertmanager, based on alerting rules.
- It exposes an HTTP API that other components use to read the stored metrics.
- It provides a dashboard for ad hoc queries and status information.

Many teams start with Prometheus for collection and Grafana for visualization. Keeping that setup organized becomes hard for a small team as the system grows. Long-term storage, scaling, and federation all need ongoing work. If the stack becomes too much to maintain, you can move to a commercial system without changing the metrics your workloads already expose.

### 1.5 Pushing metrics with the Pushgateway

Picture a nightly evaluation job that runs for a short while and exits before the Prometheus server ever visits it. Some workloads do not live long enough to be scraped. A batch job that finishes its work and shuts down may disappear before the Prometheus server collects its metrics. For this case, the job pushes its metrics to the Prometheus Pushgateway. The gateway holds those metrics, and the Prometheus server scrapes the gateway like any other target.

Not every workload fits the scraping model, so treat the Pushgateway as the exception. If your platform supports these workloads, deploy the Pushgateway as part of the metrics stack. Then publish where it runs and how tenants use its REST-like HTTP API. Tenants need both facts before their batch jobs can push anything. A pushed value also stays on the gateway until someone deletes it, so a job that died halfway can leave a stale number that looks current.

### 1.6 Custom metrics and exporters

Picture an internal inference wrapper that your team wrote last month. Nobody has told Prometheus about it yet. Some applications expose Prometheus metrics natively. Many applications built for Kubernetes do this. Official and community client libraries make it simple to publish custom metrics for scraping.

When an application cannot expose metrics itself, an exporter does the work. An exporter collects data from an application or system and publishes it as Prometheus metrics. The Node Exporter is the common example, and community exporters cover many other popular tools.

Once an application exposes metrics, add it to the scrape configuration. The usual way is a ServiceMonitor resource, covered in section 1.9. The rule of thumb is simple. Instrument the software you build in-house. Build or find an exporter where native instrumentation is not possible. Then collect the exposed metrics with auto-discovery.

**Warning:** Labels make the Prometheus data model powerful, but they can also cause harm. Overusing labels can make the resource use of your Prometheus servers unmanageable. Learn how high cardinality affects metrics, and read the instrumentation guide in the Prometheus documentation before you add labels.

### 1.7 The Prometheus Operator

Picture a platform engineer who must create the same Prometheus setup in several clusters by hand. The Prometheus Operator is a Kubernetes operator. It deploys and manages the parts of a metrics system, both for the platform and for tenant workloads. It uses custom resources to describe Prometheus servers, Alertmanager deployments, scrape configurations, and rules for recording and alerting. Platform engineers spend much less time on repetitive configuration this way.

The same custom resources also work as an interface for tenants. A team that needs a dedicated Prometheus server can submit a Prometheus resource to its namespace. A team that wants more alerting rules on an existing server can add a PrometheusRule resource. The Operator does the rest, so the tenant does not need to edit the server's configuration file.

The kube-prometheus project is a good place to start. It provides manifests for a complete metrics stack, along with Grafana dashboards. Treat it as a starting point, though. Learn what each component does, then change the configuration to fit your needs. Only then can you be confident that your metrics and alerting cover your systems.

### 1.8 Prometheus servers as platform resources

Picture a tenant who asks for a metrics server of their own, and the platform team who would rather not hand-build one for each request. With the Operator running, a Prometheus custom resource tells the Operator to create a new StatefulSet for a Prometheus server. The manifest below shows the main fields.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: platform
  namespace: platform-monitoring
  labels:
    monitor: platform
    owner: platform-engineering
spec:
  alerting:
    alertmanagers:
    - name: alertmanager-main
      namespace: platform-monitoring
      port: web
  image: quay.io/prometheus/prometheus:v2.20.0
  nodeSelector:
    kubernetes.io/os: linux
  replicas: 2
  resources:
    requests:
      memory: 400Mi
  ruleSelector:
    matchLabels:
      monitor: platform
      role: alert-rules
  securityContext:
    fsGroup: 2000
    runAsNonRoot: true
    runAsUser: 1000
  serviceAccountName: platform-prometheus
  version: v2.20.0
  serviceMonitorSelector:
    matchLabels:
      monitor: platform
```

The `alerting` block tells Prometheus where to send alerts. The `image` field sets the container image for Prometheus. The `ruleSelector` picks the PrometheusRule resources that apply to this server, so any rule with those labels is loaded. The `serviceMonitorSelector` does the same job for ServiceMonitors, which feed the scrape configuration.

The Prometheus custom resource lets platform operators deploy Prometheus servers readily. A large cluster can divide metrics collection and processing load among several Prometheus deployments, as section 1.13 explains. The same resource can also serve tenants. A team's applications may emit so many metrics that they overwhelm the shared servers. In that case, a dedicated server in the team's namespace makes sense, and its cost can count toward the team's resource budget. Not every team has the appetite to run its own Prometheus resources, so offer a simpler abstraction if you can. Do not discount the added complexity for dashboards, alerting, federation, and long-term storage. Those costs come with a dedicated server, and they are easy to underestimate.

### 1.9 ServiceMonitor and PrometheusRule resources

Picture a new API server add-on that ships without any scrape config. Deploying servers is one task. Keeping their configuration current is another. The most common resource for this is the ServiceMonitor. When you create one, the Operator updates the scrape configuration of the matching Prometheus server. The manifest below scrapes the Kubernetes API server.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    k8s-app: apiserver
    monitor: platform
  name: kube-apiserver
  namespace: platform-monitoring
spec:
  endpoints:
  - bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
    interval: 30s
    port: https
    scheme: https
    tlsConfig:
      caFile: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      serverName: kubernetes
  jobLabel: component
  namespaceSelector:
    matchNames:
    - default
  selector:
    matchLabels:
      component: apiserver
      provider: kubernetes
```

The `labels` on the ServiceMonitor match the `serviceMonitorSelector` in the Prometheus manifest above. The `endpoints` block sets the port and the connection details. This example connects over HTTPS, and it supplies a Certificate Authority file and a server name to verify the endpoint. A Certificate Authority file is the trusted list of certificates that the client uses to check the server's identity.

In Prometheus terms, a job is a group of instances of one service. A single API server is an instance, and all the API servers together form a job. The `jobLabel` field names the label that supplies the job name, which is `apiserver` in this example. The `namespaceSelector` tells Prometheus which namespaces to search for Services. The `selector` finds Services by their labels. Any Service in the default namespace with those labels becomes a scrape target.

ServiceMonitors cover Services. PodMonitor resources scrape groups of Pods directly, and Probe resources monitor Ingresses or static targets.

The PrometheusRule resource tells the Operator to generate a rule file for Prometheus. The rules go into a ConfigMap, which is mounted into the Prometheus Pods. The manifest below holds one recording rule and one alerting rule.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  labels:
    monitor: platform
    role: alert-rules
  name: sample-rules
  namespace: platform-monitoring
spec:
  groups:
  - name: kube-apiserver.rules
    rules:
    - expr: |
        sum by (code,resource) (rate(
          apiserver_request_total{job="apiserver",verb=~"LIST|GET"}[5m]
        ))
      labels:
        verb: read
      record: code_resource:apiserver_request_total:rate5m
  - name: kubernetes-apps
    rules:
    - alert: KubePodNotReady
      annotations:
        description: Pod {{ $labels.namespace }}/{{ $labels.pod }} has been in a non-ready state for longer than 15 minutes.
        summary: Pod has been in a non-ready state for more than 15 minutes.
      expr: |
        sum by (namespace, pod) (
          max by(namespace, pod) (
            kube_pod_status_phase{job="kube-state-metrics", phase=~"Pending|Unknown"}
          ) * on(namespace, pod) group_left(owner_kind) topk by(namespace, pod) (
            1, max by(namespace, pod, owner_kind) (kube_pod_owner{owner_kind!="Job"})
          )
        ) > 0
      for: 15m
      labels:
        severity: warning
```

The `labels` on this resource match the `ruleSelector` in the Prometheus manifest. The recording rule computes the total LIST and GET requests to all API server instances over a five-minute window. It stores the result in a new metric called `code_resource:apiserver_request_total:rate5m`. The alerting rule sends a warning if a Pod stays in a not ready state for more than 15 minutes. Read the two rules side by side, and notice that one produces a new series and the other produces an alert.

Managing Prometheus servers with the Operator and these custom resources has proven useful in the field. If Prometheus is your main metrics tool, this pattern is worth adopting.

### 1.10 Alertmanager

Picture a single outage that makes many replicas fail at once, each one trying to page someone. Alertmanager is a separate workload. It processes alerts and routes them to receivers, which reach the on-call engineers. Prometheus fires alerts when a measurable condition occurs, and it sends them to Alertmanager. Alertmanager groups and deduplicates them, so engineers do not get a flood of pages when one outage affects many replicas or components.

Receivers are the supported notification channels, such as email, Slack, or PagerDuty. For a custom or unsupported system, the webhook receiver sends a POST request with a JSON payload to a URL you provide. A webhook is simply a request that one system sends to another when something happens.

With the Operator, you deploy Alertmanager with a manifest like this one.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: Alertmanager
metadata:
  labels:
    alertmanager: main
  name: main
  namespace: platform-monitoring
spec:
  image: quay.io/prometheus/alertmanager:v0.21.0
  nodeSelector:
    kubernetes.io/os: linux
  replicas: 2
  securityContext:
    fsGroup: 2000
    runAsNonRoot: true
    runAsUser: 1000
  serviceAccountName: alertmanager-main
  version: v0.21.0
```

Setting `replicas` above one gives you a highly available Alertmanager. Most clusters need only one Alertmanager, and one per cluster is the wise choice. Each cluster's own Alertmanager reduces its external dependencies. A centralized Alertmanager for several clusters is possible, but one per cluster is the safer default. If the shared Alertmanager is down, every cluster that depends on it goes quiet at once.

A shared Alertmanager also helps tenants. Each Prometheus server sends its alerts to the cluster's Alertmanager, so a tenant can add alerting rules through a single PrometheusRule resource.

Be careful not to over-alert. Excess critical alerts burn out on-call engineers, and false positives can drown out real critical events. Tune your alerts until each one is useful. Add clear descriptions to the annotations, so the engineer has context right away. Link to runbooks or other docs that help resolve the incident. A good alert tells the reader what is broken, how bad it is, and what to do first.

Offer tenants a way to add their own alerting rules, and set up notifications through Alertmanager so each team gets alerted according to the rules it sets.

Silences and maintenance windows are the other side of alerting. During a planned upgrade, an engineer can silence the alerts for one service for a short time, so the pager does not ring for a known change. A silence should always carry a comment and an expiry time. A silence without an expiry is an alert that has been turned off by accident, and nobody remembers to turn it back on.

### 1.11 The dead man's switch

Picture the morning after a storm, when the alerting system itself was down all night and nobody was paged. One alert deserves special attention because every platform needs it. What happens when the metrics or alerting system goes down? You will not get an alert from a system that is itself down.

The answer is a dead man's switch. Set up an alert that fires on a regular schedule under normal operation. If that alert stops arriving, a critical alert reaches on-call and tells them the metrics or alerting system is down. PagerDuty offers an integration called Dead Man's Snitch that provides this. You can also build a custom solution with webhook alerts to a system you install. Either way, make sure you are notified urgently when your alerting system goes offline. The switch works because silence becomes the signal.

### 1.12 Node exporter, kube-state-metrics and the Prometheus adapter

Picture a pod stuck in a crash loop late at night, and you want to see the restart count without typing a long kubectl command. The node exporter usually runs as a DaemonSet and collects machine and operating system metrics. It reports host-level CPU, memory, disk I/O, disk space, network statistics, and file descriptor information. Linux does not export Prometheus metrics natively, so the node exporter reads the values from the kernel and exposes them for scraping. Use it whenever you want to monitor the hardware and system of Unix-like machines.

kube-state-metrics is an exporter for Kubernetes resources. It reads information from the Kubernetes API and exposes it as metrics. It reports Pod start times, status, labels, priority class, resource requests, and limits. These are the same facts you would normally gather with `kubectl get` or `kubectl describe`. The metrics help you spot critical conditions, such as Pods stuck in crash loops or Namespaces close to their resource quotas. The difference matters. kube-state-metrics tells you the state of an object, and a node exporter tells you the state of the machine under it.

The Prometheus adapter ships in the kube-prometheus stack, but it is not an exporter. It also plays no part in Prometheus core functions. Instead, it is a client of Prometheus. It reads metrics from the Prometheus API and serves them through the Kubernetes metrics APIs. That lets workloads autoscale on those metrics. In other words, the adapter lets the autoscaler ask Prometheus a question.

### 1.13 Organizing and federating Prometheus servers

Picture a single Prometheus server that starts to lag every time someone opens the platform dashboards. Processing metrics can be compute-intensive. Splitting that load across servers keeps resource use manageable. One server can collect platform metrics, while others collect application metrics or node metrics. This matters most in large clusters with many scrape targets and large volumes of data.

Splitting the work also scatters the data. Federation brings it back together. Prometheus federation collects important metrics from several Prometheus servers into one central server. It uses the same scraping model that collects metrics from workloads, so one scrape target can be another Prometheus server. Federation can work within one cluster, across several clusters, or both. You can also layer it in tiers. For example, a global server can scrape servers in different datacenters, and each of those can scrape the targets in its own cluster.

Federation is powerful, but it is complex to manage. Thanos is an open source project that builds federation-like capabilities on top of Prometheus. The Prometheus Operator supports it, and you can add it to existing installations.

The Prometheus Operator supports it, and you can add it to existing installations. Adding it to an existing install is usually a matter of deploying the extra components beside the server and pointing them at the same storage. Cortex is another promising project. Both Thanos and Cortex are incubating projects in the CNCF. Pick the tool that matches the problem you have, and do not add a layer just because it exists.

Remember that every layer adds a place where data can get stuck. A federated setup has two scrape hops instead of one, and a remote storage setup adds a network path that can fail. Each extra layer is worth it only when the problem it solves is real and you can name it.

Plan the layout of your Prometheus servers before adoption grows.

Plan the layout of your Prometheus servers before adoption grows. A layout that works for a few teams can fail badly as the list grows, and changing it later means moving dashboards, alerts, and habits all at once. Think about how tenants will consume the metrics. Avoid making them switch between many dashboards to see their own workloads.

---

## 2. PromQL for AI workloads

### 2.1 The basic PromQL

Picture the question you ask during an incident: how busy is one GPU node right now? PromQL is the query language for Prometheus, and it answers questions like this one. A query has a metric name, labels in braces, and then an operator and a value.

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

Start with a metric, then filter it with labels. Aggregate with sum, avg, max, or min. Use rate, increase, or irate to turn counters into values over time, and use `histogram_quantile` to get a percentile from a histogram.

Here is a short walk through a typical query. You start with the metric name, such as a request counter. You filter it with a label, such as the model. You apply rate to turn the growing counter into a per-second value. Then you sum the result by model, so the panel shows one line for each model. Each step is small, and the final query reads almost like the sentence you would say to a colleague. A counter only goes up, so the rate function turns its growth into a per-second value you can graph. A histogram groups observations into buckets, and the percentile function reads the buckets to estimate the value at a chosen percentile.

### 2.2 PromQL for the AI infrastructure

Picture a dashboard that answers a handful of questions about the GPU pool at once. During an incident, the on-call engineer runs a small set of queries again and again. Those same queries later drive the dashboards. Keep the list short, so the on-call can type each one from memory under pressure.

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

Publish these queries as a library, version them, and test them. The on-call engineer relies on them under pressure, so a broken query is an operational risk. A query that returns the wrong unit can look fine on a graph and still send the team in the wrong direction. Keep the query file in Git next to the dashboards, so a change to one shows up in review.

### 2.3 Recording rules

Imagine a dashboard where every panel runs a heavy query on every page load. The page is slowest exactly when the on-call needs it most. Recording rules fix this by computing expensive queries ahead of time.

Prometheus evaluates each recording rule on a schedule and writes the result to a new time series. Dashboards then read that precomputed series, which costs far less than running the raw query again. The naming convention in the example, with colons between the level, the metric, and the window, makes it clear which series is a precomputed one.

```yaml
# code/part17/recording_rules.yaml
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

The rules in this example run every 30 seconds, and the cost rule runs every 5 minutes. Before you add a dashboard panel, ask whether its query is heavy. If it is, record that query first. Recording rules trade a little storage for a lot of speed, so they pay off most on panels that many people open at once.

Name each rule so the name tells the reader where it came from. The convention in the example puts the level first, then the metric, then the window. A reader who sees gpu_pool:utilization:avg5m knows it is a pool-level average over a five-minute window without opening the file. Keep the evaluation interval close to the rate of change you care about. A rule that runs every 30 seconds is fine for pool utilization, and a rule that runs every 5 minutes is fine for cost.

### 2.4 Showback and chargeback

Picture a finance review where a team asks why its cluster bill doubled in one quarter. Showback describes how much of the cluster an organizational unit or its workloads use. Chargeback attaches a cost to that use. Both turn raw metrics into numbers a team can act on. Without them, Kubernetes capacity is easy to over-request, and clusters sprawl with poor utilization.

Kubernetes makes compute capacity readily available to application teams. Streamlining how infrastructure gets deployed is advantageous to the business, but it can also encourage waste. Many organizations therefore hold each team and business line answerable for the resources it uses. Showback and chargeback turn that usage into actionable numbers.

To measure showback, each workload needs a label that names its owning team, such as `team` or `owner`. Choose one standard label for the whole organization. Then use admission control to require that label on every Pod that tenants deploy. Admission control is the check the cluster runs before it accepts an object, so a Pod without the label is rejected at the door. Namespaces can also identify workloads, but labels are the most flexible option.

There are two ways to calculate showback. The requests method uses the resource requests each container defines. The consumption method uses what a workload actually uses, or its requests, whichever is higher.

With the requests method, a Deployment with 10 replicas that requests 1 CPU core each counts as 10 cores for every unit of time it runs. If a replica bursts to 1.5 cores on average, the extra half core is not attributed to the workload. That adds up to 5 cores across the Deployment. The scheduler treats requests as reserved capacity on a node, so a burst into unused capacity was effectively free. This method matches what the scheduler can assign.

With the consumption method, a workload that often uses more than its requests is charged for what it really uses. This removes the incentive to set requests low to game the system. The downside is that it can cause resource contention on overcommitted nodes. Overcommitted means the node has promised more capacity than it physically has, which works until several workloads peak together.

If you run kube-state-metrics, these metrics provide the request values:

- CPU requests: `kube_pod_container_resource_requests`
- Memory requests: `kube_pod_container_resource_requests_memory_bytes`

These metrics provide the actual usage:

- CPU usage: `container_cpu_usage_seconds_total`
- Memory usage: `container_memory_usage_bytes`

Decide whether CPU or memory drives the showback for each workload. Calculate the share of total cluster CPU and the share of total cluster memory that the workload uses. Apply the higher of the two. A cluster that runs out of CPU or memory cannot host more workloads. A workload using 1% of cluster CPU and 3% of cluster memory effectively uses 3% of the cluster. The same comparison shows whether different node profiles would suit different workloads.

Chargeback becomes possible once showback exists, because you then have a value to price. Cloud machine costs are usually straightforward. Your own hardware takes more work, but you still need two values. The first is the cost per unit of time for CPU, and the second is the cost per unit of time for memory. Apply those costs to the showback value, and you have a model for charging your platform tenants. Start with a simple model and refine it after the first billing cycle, because a perfect model that arrives late helps nobody.

Some workloads also consume large amounts of network bandwidth or disk storage, and those costs can be significant. The model stays the same. Collect the relevant metrics, then decide whether to charge for resources reserved, resources consumed, or a mix of both. How you collect those metrics depends on the systems that provide that infrastructure.

---

## 3. Grafana

### 3.1 The Grafana architecture

Picture a single incident that needs the metric spike, the error log, and the slow trace on the same screen. A single incident often needs metrics, logs, and traces on one screen. Grafana puts them there. It queries its data sources, which in this chapter are Prometheus, Loki, and Tempo, and it renders the results as panels. Panels are grouped into dashboards, and dashboards are grouped into folders for each team.

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

Dashboards are JSON files, so you can version them in Git. The platform team deploys them through its GitOps loop, which makes every change reviewable. GitOps means that the desired state of the cluster lives in Git, and a tool applies whatever Git says.

### 3.2 The on-call dashboard

Picture the on-call engineer who opens a page late at night and needs to know within a minute whether the problem is the cluster, the model, or the cost. The on-call engineer needs one page that answers the first questions of an incident. The on-call dashboard is that page, and it is the most important dashboard in the platform. Its job is to show the state of the system as soon as it opens.

```yaml
# code/part17/on_call_dashboard.json
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

This dashboard has eight panels, and each one answers a question the on-call asks during an incident. The aim is a page that loads fast enough to be useful in the first minute of a page. Each panel reads a recording rule, so the page stays quick even when many engineers open it at once.

The order of the panels matters too. Put the question that the on-call asks first at the top left, where the eye lands first. Put the slow, detailed panels further down, where the on-call only reaches them when the top panels point somewhere. A page built this way answers the first question quickly, even if the rest of the dashboard takes a moment to finish.

### 3.3 The per-team dashboard

Picture a data science lead who asks where the team's own models show up in the dashboards. Each team needs a view of its own models, pipelines, and costs. The platform team owns one template, and each team fills in its own specifics. A template keeps the layout the same from team to team, so an on-call engineer who is new to one team can still find things quickly.

### 3.4 Dashboard as code

Picture a dashboard that someone edited by hand last week, with no record of the change. When it breaks, nobody knows what changed or why. Keep dashboards as JSON files in Git instead. Reviewers can read each change in a pull request, and a GitOps tool such as Argo CD can deploy the file.

```bash
# code/part17/dashboard_deploy.sh
#!/bin/bash
# Deploy a Grafana dashboard via the Grafana API
DASHBOARD_JSON=$(cat dashboards/on-call.json | jq -c '.dashboard')
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d "{\"dashboard\": $DASHBOARD_JSON, \"overwrite\": true}" \
  $GRAFANA_URL/api/dashboards/db
```

Once the dashboard is a file in Git, every change has a reviewer, an automated deploy, and a record. The script above is a simple way to push a dashboard file to Grafana through its API. In a mature setup, a GitOps tool does this step for you.

### 3.5 One dashboard or many

Picture a platform operator who must reason about a whole fleet from one screen. Platform operators must reason about a complex platform, so they need charts built from the data in Prometheus. Grafana is the default visualization layer for Prometheus metrics. The kube-prometheus project ships dashboards you can use as a starting point, and the community offers many more. You can also build your own charts for any system in the platform.

Tenants need these views too, so the way you deploy Prometheus shapes what they see. If each Prometheus server has its own dashboard, the separation is clean. But tenants who must log in to many dashboards every day will find that tiring. You then have two options. The first is federation, which collects metrics from several servers into one server with one dashboard. Projects such as Thanos use this approach. The second is to add several Prometheus data sources to a single Grafana dashboard.

The choice comes down to where you want the complexity. Federation moves it into the Prometheus layer, and multiple data sources move it into Grafana configuration. Federation uses more resources, but if that cost is acceptable, the choice is mostly a matter of preference.

If one Prometheus server serves both platform operators and tenants from one place, plan permissions for viewing and editing dashboards. Set up organizations, teams, and users to match your use case. Think about the on-call engineer who is not a member of the owning team during a shared incident. That person needs read access to the right folder, but not the power to edit a panel that another team depends on. Folders and permissions are the simplest way to give that access without handing out more than the person needs.

---

## 4. Storage and retention

### 4.1 The TSDB

Suppose Prometheus restarts in the middle of an incident. It must not lose the last few minutes of data, and it must keep answering queries. Prometheus keeps its metrics in a time-series database, or TSDB, on local disk. The TSDB has three parts: the head block for recent data, the write-ahead log, or WAL, and compacted blocks for older data.

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

Each sample goes to the write-ahead log on disk and into the head block in memory. After a restart, Prometheus replays the log to rebuild the head block. Roughly every two hours, the head block is compacted into an immutable block on disk. Queries read the head block and the compacted blocks together. Compaction is the housekeeping step that merges small blocks into larger ones, so queries over long ranges stay fast.

Queries read the head block and the compacted blocks together. Compaction is the housekeeping step that merges small blocks into larger ones, so queries over long ranges stay fast. If the disk fills up, Prometheus stops writing new samples, and the dashboards show gaps that look like a healthy system. That is why the disk budget and the disk alert belong in the same review as the retention period.

### 4.2 Retention

Picture a capacity review where someone asks how far back the disk history goes. Keeping metrics longer costs disk space. Keeping them shorter means you cannot look back at last month's incident. The retention period is the balance between those two needs.

| Retention | Disk for one series | Use case |
|---|---|---|
| 1 day | 12 KB | Debugging only |
| 7 days | 81 KB | Recent debugging |
| 30 days | 346 KB | Default |
| 90 days | 1.0 MB | Capacity planning |
| 1 year | 4.2 MB | Regulatory audit |
| 5 years | 21 MB | Long-term retention (rare) |

The table assumes one sample every 15 seconds, which is 5,760 samples a day, and 2 bytes per compressed sample. The Prometheus documentation gives 1 to 2 bytes per sample as a planning figure. Disk use grows in step with the retention period, so 90 days needs three times the disk of 30 days. Multiply by the number of series you keep. Real storage depends on your scrape interval and your data, so measure your own before you set a budget.

The chapter's pattern is 30 days for operational dashboards, 90 days for capacity planning, and one year for the audit log. Set the period with the Prometheus flag `--storage.tsdb.retention.time`. Write the chosen period next to the reason for it, so the next person who asks why the data stops at a certain date can find the answer.

### 4.3 Remote storage

Picture an audit request that asks for metrics from more than a year ago. Local disk handles recent data well, but it is not built for long-term history. *Production Kubernetes*, chapter 9, makes the same point. Prometheus supports writing to remote endpoints, and the book names Thanos and Cortex as projects for that job.

The pattern splits the work. Prometheus keeps recent data locally, a remote backend keeps historical blocks in object storage, and the query layer merges both.

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

This follows the storage pattern from Chapter 13: recent data stays local, and history moves to object storage. That split is what keeps 90-day retention affordable. Before you promise a retention period, test a query against the oldest data you plan to keep. A promise that the query layer cannot answer is worse than a shorter period you can actually deliver.

---

## 5. Operating Prometheus and Grafana on GKE

### 5.1 The components

Picture a Grafana page that loads slowly on the first morning of a release, and the team realising that nobody had set a latency target for it. Running the stack is a service in its own right. Each component has a job, a place where it runs, and a latency target that tells you whether it is healthy.

Each component has a job, a place where it runs, and a latency target that tells you whether it is healthy. Someone must own each target and the pager that goes with it. When nobody owns the stack, the first person to notice a slow Grafana is often the on-call engineer at the worst possible hour.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Prometheus server | Kubernetes Deployment, 2 replicas (HA) | Persistent disk | Scrape latency p99 < 5 s |
| Alertmanager | Kubernetes Deployment, 2 replicas | (sends to PagerDuty) | Alert latency p99 < 10 s |
| Grafana | Kubernetes Deployment | (uses Prometheus) | Dashboard load p99 < 5 s |
| Thanos Receive | Kubernetes Deployment | Object storage | Remote write p99 < 10 s |
| Thanos Querier | Kubernetes Deployment | Object storage | Query latency p99 < 5 s |

The latency targets in this table are example values. Choose your own, based on what your on-call engineers and users actually need. Write each target down next to the component it protects, so a change to the component reminds you to check the target too.

### 5.2 IAM and the cardinality budget

Imagine a data scientist who can change the settings of the metrics server. One mistake could blind the on-call team. Separate roles keep reading, writing, and administration apart.

The stack has its own IAM with three roles, shown below. IAM is the identity and access system that decides who may do what. Each role maps to a group of people or systems.

| Role | Who | What they can do |
|---|---|---|
| `prometheus.reader` | Every team's data scientists | Query PromQL; view dashboards |
| `prometheus.writer` | The exporters | Write metrics to the remote write endpoint |
| `prometheus.admin` | The platform team | Manage the Prometheus server; set the cardinality budget |

The role names in the table are examples. Use the naming scheme your own IAM system already follows.

The cardinality budget depends on discipline. Every new metric must declare its label cardinality before it ships. The platform team rejects any metric that exceeds the budget. A declaration can be as simple as a line in the metric's documentation that lists each label and its expected number of values. A declaration can be as simple as a line in the metric's documentation that lists each label and its expected number of values. A better version lives in the code review template, so the reviewer sees the declaration beside the change. Either way, the point is that the number is written down before the metric ships, not discovered after the server has crashed.

### 5.3 Observability

Picture the Prometheus server that stops answering while every other system looks fine. Prometheus must watch itself, too. If its series count or memory climbs, the platform team needs to know before the server runs out of memory. The stack's own alerts are the early warning for that case. Treat them as a product in their own right. Each one needs an owner, a description, and a link to a runbook, just like an alert for a customer-facing service.

| Metric | Why it matters | Alert |
|---|---|---|
| Scrape latency p99 | Hot path for every metric | > 10 s |
| TSDB head series count | Cardinality budget | > budget for 1 hour |
| TSDB disk usage | Storage budget | > 80% for 1 hour |
| Prometheus process CPU | Resource budget | > 80% for 1 hour |
| Prometheus process memory | Resource budget | > 80% for 1 hour |
| Dashboard load latency p99 | On-call response time | > 10 s |

The thresholds in this table are example values. Set your own from a baseline you measure on your cluster. *AI Systems Performance Engineering*, chapter 16, gives its own examples for GPU alerts. One fires when utilization stays below 10 percent for 60 seconds. A memory warning fires above 80 percent. Those examples show the shape of a good alert, which names a threshold and a duration together.

The TSDB head series count is the most important alert. A spike in series count is a signal that a new high-cardinality label was added. The platform team investigates before Prometheus runs out of memory.

---

## 6. How it fails

Picture a dashboard that goes quiet at the worst moment of an incident. Six failure modes come up again and again. Each one starts with a symptom you can see, and each has a diagnosis and a fix. Picture the first symptom as the only clue on a dark night, and the diagnosis as the step that turns the clue into a cause.

### 6.1 "Prometheus is using too much memory"

Prometheus is OOM-killed. The dashboards go stale, and the alerts stop firing. That is the symptom. The out-of-memory kill is silent from the outside, so the first sign is usually an empty graph.

The diagnosis is that cardinality has outgrown the memory budget. Someone added a metric with a high-cardinality label.

The fix is to find the metric with `prometheus_tsdb_head_series`. Drop the high-cardinality label at its source, or aggregate the metric before it reaches Prometheus. Then add a cardinality alert, so the next creep is caught before the crash.

### 6.2 "The dashboards are loading slowly"

The on-call opens the dashboard and waits. For example, the page takes 30 seconds to load, and the on-call cannot answer the question in time. The delay is the symptom, and it is easy to blame the network first.

The diagnosis is that the dashboard has too many panels. Each panel queries many series, and none of those queries is a recording rule.

The fix is to cut the number of panels per dashboard. Record the expensive queries as recording rules. Use Prometheus federation so each dashboard queries the right Prometheus server.

### 6.3 "The alert fires but the page is empty"

Alertmanager fires, and the page goes out. The on-call opens the dashboard and sees that the metric is green. The alert and the picture disagree, and that disagreement is the symptom.

The diagnosis is that the alert rule has a typo in its PromQL. It fires on a label combination the on-call does not care about.

The fix is to test the alert rule before you deploy it. Add a `for:` clause to the alert rule so that it fires only when the condition holds for a set time, and tighten the expression to filter out the cases you do not need. Then add an alert rule that catches the false positive.

### 6.4 "The retention period is too short"

The on-call needs historical data from 60 days ago, and Prometheus no longer has it. The incident cannot be debugged without that data. The symptom only appears when you go looking for old data.

The diagnosis is that the retention period is shorter than the age of the incident.

The fix is to increase the retention period. Use Thanos remote storage for long-term history. Document the retention period on the platform's status page, so the next person knows how far back the data goes.

### 6.5 "The Thanos remote write is failing"

Prometheus is healthy, but historical data never reaches object storage. Long-term queries fail. The local dashboards look fine, so the failure hides in the background.

The diagnosis is that the remote write endpoint is unhealthy, the network is failing, or the credentials are wrong.

The fix is to check the remote write endpoint, the credentials, and the network. Then add an alert on remote write latency.

### 6.6 "The cardinality budget is silently exceeded"

Prometheus uses more memory than expected, and the cardinality alert has never fired. The memory graph climbs slowly, week after week, and nobody has noticed the trend.

The diagnosis is that the alert threshold is set too high to catch a slow creep. A threshold that suits a sudden jump can miss a slow rise.

The fix is to lower the cardinality alert threshold. Add an alert on the cardinality growth rate, and review the budget every quarter.

Pick the failure you are most likely to meet, and write its alert before you need it.

## 7. Hands-on lab

Suppose you have a GKE cluster and no metrics yet. In this lab, you stand up Prometheus and Grafana, configure scrape jobs for the AI infrastructure's exporters, and build the on-call dashboard. The lab is untested in this repository, so treat each command as a starting point. These steps were not run on a live cluster.

### 7.1 Prerequisites

Picture a cluster that has never had a metrics tool. Before you begin, check these three items.

- A GKE Autopilot or Standard cluster, version 1.27 or later.
- Helm 3, to install the observability stack.
- A workload that emits Prometheus metrics, such as the DCGM exporter from Chapter 17.4.

### 7.2 Step 1: install Prometheus

Picture a fresh cluster where the first goal is to see any numbers at all. This command installs the kube-prometheus-stack chart, which brings in Prometheus and Grafana. It sets retention to 30 days.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set grafana.adminPassword=admin
# expected: Prometheus and Grafana pods are running
```

### 7.3 Step 2: install the DCGM exporter

Picture the GPU nodes sitting idle in the cluster while Prometheus has nothing to say about them. Install the DCGM exporter on the GPU nodes, and let Prometheus scrape it through a ServiceMonitor.

```bash
helm install dcgm-exporter nvidia/dcgm-exporter \
  --namespace monitoring \
  --set serviceMonitor.enabled=true
# expected: the DCGM exporter pods are running on each GPU node; the metrics are scraped by Prometheus
```

### 7.4 Step 3: verify the scrape

Picture the first check after an install: is the number really arriving? Think of it as a quick proof that the whole path works, from the GPU driver through the exporter and the scrape into the time-series database. If any link breaks, the query comes back empty, and the empty answer tells you the link to check first. Port-forward to Prometheus, then query one DCGM metric. If the query returns a value for each GPU, the scrape works.

```bash
# Port-forward to Prometheus
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Query the DCGM metrics
curl -s 'http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL' | jq .
# expected: the GPU utilisation per GPU
```

> **dcgm-exporter 4.9.0 version note.** dcgm-exporter 4.9.0 (2026-11-06) renamed many default metrics and changed some units. For example `DCGM_FI_DEV_GPU_UTIL` (percent) became `DCGM_FI_DEV_GPU_UTIL_RATIO` (0 to 1), and `DCGM_FI_DEV_FB_USED` (MiB) became `DCGM_FI_DEV_FB_USED_BYTES`. The metric names in this chapter are the 4.8.x names. On a 4.9.0 exporter use the [full mapping in 17.4](04-dcgm-exporter-and-interpreting-gpu-metrics.md#14-what-dcgm-exporter-490-renamed), and change thresholds together with the unit. If the query above returns nothing on a new exporter, check the version before you check the network.

### 7.5 Step 4: build the on-call dashboard

Picture the moment the on-call dashboard first loads and the team wants to confirm it shows the right panels. Look at each panel with one question in mind. Does it show data, and does the data make sense for the title? A panel that shows a flat line can be correct for an idle pool, and it can also be a broken query, so check the source before you trust the picture. Load the on-call dashboard into Grafana, then open it at the path shown in the expected output.

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

Picture a dashboard that is still slow after the panel cut, because one query is heavy. Load the recording rules into Prometheus, then reload Prometheus so the rules take effect.

```bash
# Apply the recording rules
kubectl -n monitoring create configmap recording-rules \
  --from-file=configs/recording_rules.yaml

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
# expected: the recording rules are active
```

### 7.7 Step 6: query the recording rules

Picture a panel that reads a recording rule and shows nothing. Query one of the recording rules to confirm that the pool utilization series exists.

```bash
curl -s 'http://localhost:9090/api/v1/query?query=gpu_pool:utilization:avg5m' | jq .
# expected: the GPU pool utilisation per GPU product
```

### 7.8 What to record

Picture the lab done and the stack running. After the lab, you should answer five questions quickly. Each answer should come from one query or one panel.

1. What is the current Prometheus scrape latency p99?
2. What is the current TSDB head series count?
3. What is the current inference p99 latency (from the recording rule)?
4. What is the current cost per team this month (from the recording rule)?
5. What is the current cardinality per metric?

The 30-second limit is this lab's own target, not an industry standard. If any answer takes longer, the stack is not yet ready for production. Write down which answer was slow, because that is the first part of the stack to tune.

Write down which answer was slow, because that is the first part of the stack to tune. Keep the notes in the same place as the runbook, so the next on-call engineer finds them without asking.

## Exercises

Picture a stack that already runs, with the lab's dashboard and recording rules in place. Work through these exercises after the lab, while the stack is still running. Each one extends the stack, and each comes with a sketch you can check your own answer against.

1. Precompute the per-feature drift score so that dashboards read it cheaply. *Solution sketch:* a recording rule that aggregates `evidently_drift_score` per feature.
2. Fire an alert when any metric's cardinality exceeds 1000. The 1000 limit is an example value. *Solution sketch:* a Prometheus alert on `count by (__name__) ({__name__=~".+"})`.
3. Configure Prometheus to remote-write to Thanos, then check that the historical data is queryable. *Solution sketch:* the Thanos Receive endpoint, the Thanos Querier, and a Thanos integration in Grafana.
4. Build a template that each team fills in with its own models and pipelines. *Solution sketch:* a Grafana dashboard JSON template, the team's specific labels, and the deployment script.
5. Show recent audit log events, so you can answer the regulator's questions quickly. *Solution sketch:* a Grafana data source that queries the audit log, and the dashboard's panels.
6. Alert when cardinality grows faster than 10 percent in 24 hours. The 10 percent figure is an example value. *Solution sketch:* a recording rule that computes the daily cardinality delta, and an alert on that delta.

## Checkpoint questions

<details><summary>1. Prometheus is OOM-killed, the dashboards go stale and the alerts stop firing. What is the cause and what is the fix order?</summary>
Cardinality has outgrown the memory budget, because someone added a metric with a high-cardinality label. Find the metric with `prometheus_tsdb_head_series`. Drop the label at its source or aggregate the metric before it reaches Prometheus, then add a cardinality alert.
</details>

<details><summary>2. The on-call opens a dashboard and waits 30 seconds for it to load. What is the diagnosis and the fix?</summary>
The dashboard has too many panels, each panel queries many series, and none of the queries is a recording rule. Cut the number of panels and record the expensive queries as recording rules. Use federation so each dashboard queries the right Prometheus server.
</details>

<details><summary>3. Alertmanager pages the on-call, but the metric on the dashboard is green. What is the likely cause and how do you fix it?</summary>
The alert rule has a typo in its PromQL and fires on a label combination the on-call does not care about. Test the rule before deploying it. Add a `for:` clause so it fires only when the condition holds for a set time, and tighten the expression to filter out cases you do not need.
</details>

<details><summary>4. The on-call needs data from 60 days ago, and Prometheus no longer has it. What do you change?</summary>
The retention period is shorter than the age of the incident. Increase the retention period and use Thanos remote storage for long-term history. Document the retention period on the platform's status page.
</details>

<details><summary>5. Prometheus is healthy, but long-term queries fail because history never reaches object storage. What do you check?</summary>
Check the remote write endpoint, because it may be unhealthy. Then check the credentials and the network. Last, add an alert on remote write latency so the failure does not go unseen.
</details>

<details><summary>6. Prometheus uses more memory than expected, yet the cardinality alert never fired. What went wrong?</summary>
The alert threshold is set too high to catch a slow creep. Lower the threshold, add an alert on the cardinality growth rate, and review the budget every quarter.
</details>

<details><summary>7. Why do applications never need to know anything about the metrics system behind Prometheus?</summary>
Prometheus is pull-based, and the arrows point one way. Applications only expose a `/metrics` endpoint in the exposition format, and the server scrapes it. Each application needs to know the format and nothing more.
</details>

<details><summary>8. Why does a dead man's switch alert exist, and how does it work?</summary>
You cannot get an alert from a system that is itself down. The switch is an alert that fires on a regular schedule under normal operation. If it stops arriving, a critical alert reaches the on-call and says the metrics or alerting system is down.
</details>

<details><summary>9. Why do recording rules make an incident dashboard faster?</summary>
Prometheus evaluates the rule on a schedule and writes the result to a new time series. The dashboard then reads that precomputed series instead of running the heavy query on every page load. The cost is paid once per interval and not once per viewer.
</details>

<details><summary>10. Why does Alertmanager group and deduplicate alerts, and what does it protect against?</summary>
When one outage affects many replicas or components, each would fire its own alert. Grouping and deduplicating prevents a flood of pages. The chapter warns that excess critical alerts burn out on-call engineers and bury real events.
</details>

<details><summary>11. A batch job finishes before Prometheus scrapes it. Why does the Pushgateway help, and why is it the exception?</summary>
The job pushes its metrics to the gateway, the gateway holds them, and Prometheus scrapes the gateway like any other target. It is the exception because most workloads fit the scraping model. If you deploy it, publish where it runs and how tenants use its HTTP API.
</details>

<details><summary>12. When would you offer tenants a dedicated Prometheus server, and what do you give up?</summary>
Offer it when a team's applications emit so many metrics that they overwhelm the shared servers. Its cost can count toward the team's resource budget. You give up simplicity, because dashboards, alerting, federation and long-term storage all get more complex.
</details>

<details><summary>13. Should tenants see metrics through federation or through several data sources in one Grafana dashboard?</summary>
Federation moves the complexity into the Prometheus layer, and multiple data sources move it into Grafana configuration. Federation uses more resources. If that cost is acceptable, the choice is mostly a matter of preference. The goal is that tenants do not have to log in to many dashboards every day.
</details>

<details><summary>14. When would you charge by requests and when by consumption, and what does each give up?</summary>
The requests method matches what the scheduler can assign, but a burst into unused capacity is effectively free. The consumption method charges for actual usage or requests, whichever is higher, which removes the incentive to set requests low. Its downside is that it can cause resource contention on overcommitted nodes.
</details>

<details><summary>15. A Deployment has 10 replicas that each request 1 CPU core. Under the requests method, how many cores are charged, and how many are left unattributed if each replica averages 1.5 cores?</summary>
The requests method charges 10 times 1, which is 10 cores. Actual use is 10 times 1.5, which is 15 cores. The extra 5 cores are not attributed to the workload.
</details>

<details><summary>16. A workload uses 1 percent of cluster CPU and 3 percent of cluster memory. What share do you apply for showback, and why?</summary>
Apply the higher of the two, which is 3 percent. A cluster that runs out of either CPU or memory cannot host more workloads. So the workload effectively uses 3 percent of the cluster.
</details>

<details><summary>17. A scrape job uses `scrape_interval: 15s`. How many samples does one series gain per day?</summary>
A day has 24 times 60 times 60, which is 86,400 seconds. Divided by 15, that is 5,760 samples per series per day. A `10s` interval would give 8,640.
</details>

<details><summary>18. Your retention is 30 days and you want 90 days for capacity planning. Using the chapter's table, how does disk use per series change?</summary>
The table gives 346 KB for 30 days and 1.0 MB for 90 days. Disk use grows in step with retention, so the factor is 90 divided by 30, which is 3. The figures assume 15-second scrapes and 2 bytes per sample, so measure your own before you set a budget.
</details>

<details><summary>19. After a restart in the middle of an incident, what do you expect Prometheus to do and why does it not lose the last minutes?</summary>
Each sample goes to the write-ahead log on disk and into the head block in memory. After a restart, Prometheus replays the log to rebuild the head block. Roughly every two hours the head block is compacted into an immutable block on disk.
</details>

<details><summary>20. A `gpu_pool:utilization:avg5m` query returns nothing after the lab. In what order do you check?</summary>
First check that the DCGM exporter scrape works by querying `DCGM_FI_DEV_GPU_UTIL` and looking for a value per GPU. Second check that the recording rules were loaded and that Prometheus was reloaded. Third query the recording rule again. The lab names these steps as the way to confirm the series exists.
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

- The retention period table in Section 4.2 is computed from a 15-second scrape and 2 bytes per sample, the upper end of the Prometheus documentation's 1 to 2 bytes planning figure, and is a starting point; specific retention depends on the regulatory regime and the storage budget.
- The on-call dashboard panels in Section 3.2 are a starting point; specific panels depend on the team's operational discipline.
- The cardinality budget's 1000-value limit is a rule of thumb; specific limits depend on the cluster's memory budget.

### Not verified on live hardware

- The lab in Section 7 is **untested** against a live GKE cluster in this repository.
- The Prometheus, Grafana, and Thanos versions assumed in the lab should be pinned against the current releases before production use.
- The recording rules in the lab are illustrative; production rules depend on the workload.

