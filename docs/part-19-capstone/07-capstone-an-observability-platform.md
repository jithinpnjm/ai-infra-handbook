---
id: "c19-07"
title: "19.7 Capstone: an observability platform"
sidebar_label: "19.7 Capstone: observability platform"
sidebar_position: 7
description: "Build and prove an end-to-end observability stack for a GPU platform: kube-prometheus-stack, DCGM exporter, vLLM and gateway metrics, Loki, an OpenTelemetry Collector, Grafana dashboards as code, Alertmanager routing and SLO burn-rate alerts. Every layer has an acceptance test: rule unit tests, synthetic fault injection, a Docker end-to-end run, a dashboard check and a cardinality budget."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 19.7 Capstone: an observability platform

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE for the install, a laptop with Docker for the acceptance tests |
| Part | Part 19: Capstones, design and interview readiness |
| Primary sources | Production Kubernetes (Chapter 9); Systems Performance, 2nd edition (Chapters 2 and 4); LLMs in Production (Chapter 3); Scalable Kubernetes Infrastructure for AI Platforms (Chapter 4); AI Factory (Chapter 9, read, not cited); upstream chart, release and documentation pages fetched 2026-11-10 |
| Cross-references | Chapters 17.1 to 17.6; Chapter 11.3 (GPU Feature Discovery); Chapter 19.6 (node health); Chapters 20.15, 20.19 and 20.25 |
| Coverage file | `planning/coverage/chapters/19-07.md` |
| Claim & number ledger | `planning/ledgers/19-07.md` |

## Why this matters for AI infrastructure

It is 3 a.m. and a customer reports slow answers. The on-call engineer opens the dashboard and finds every GPU panel empty. The exporter pods are running, so the usual first check passes. Yet no series arrive, because an upgrade changed the metric names and every query still asks for the old ones. Nothing crashed, and no log line says so. The dashboard just shows nothing, which looks a lot like a quiet, healthy system until someone checks the names.

Each piece of that story has a home chapter. You can read about Prometheus in Chapter 17.2 and about alerting in Chapter 17.6. Chapters 20.15, 20.19 and 20.25 cover pipelines, burn rates and the PromQL traps that catch people. A team can read every one of them and still ship a stack that fails silently. The trouble usually sits between the pieces, where no single chapter's advice applies.

This capstone is about those gaps. It builds one stack, and then it proves the stack works. Here, proof means tests that fail when something breaks. A rule gets a unit test. A fault is injected and must arrive at the right receiver. A dashboard is parsed and then queried. A series budget is computed and checked. Production Kubernetes makes the same point about the weakest link in an alerting system. If the metrics and alerting systems go down, you need an alert that tells you so, and the stack has to be built to give it to you.

## Prerequisites and outcomes

### Prerequisites

Stuck on a term while you read? Each item below names the earlier chapter that teaches it, so you can go back instead of guessing.

- Chapters 17.1 to 17.6 cover the three pillars of observability, Prometheus and Grafana, Loki and OpenTelemetry, the DCGM exporter, profiling, and alerting with SLOs.
- Chapter 20.19 covers the burn-rate arithmetic, and Chapter 20.15 covers the cardinality estimator that this chapter reuses.
- You need a laptop with `promtool`, `amtool`, `helm`, Python 3 with pytest and PyYAML, and Docker.

### Outcomes

Picture a new GPU pool going live on a Monday, with a dashboard nobody has checked and an on-call rota that depends on it. This chapter walks the path from an empty stack to one you can trust. You draw the stack, name the version of each part and find the file that configures it. You learn why dcgm-exporter 4.9.0 breaks queries written for older versions. You write platform alert rules with unit tests, and you wrap them for the Prometheus Operator. You route alerts so that only burn-rate alerts page, and you prove the route and the inhibit rule. You keep a Grafana dashboard in Git and check that every expression parses and returns data. Last, you set and test a cardinality budget, then run the Docker end-to-end test and read what it says.

---
## 1. The platform on one page

You inherit an observability stack from a colleague who has moved to another team. A GPU alert that should have fired last night never arrived, and nobody knows which part to check first. Without a map, the answer is a guess. With a map, it becomes a short walk along one path.

The path starts at the exporters and ends at a person. The NVIDIA Data Center GPU Manager (DCGM) exporter publishes GPU metrics from every GPU node. The vLLM engines, which serve the models, and the gateway publish their own metrics. Prometheus is the metrics database and rule engine. It scrapes all of those sources, which means it reads their numbers from each address on a timer, and then it evaluates the rules. Alertmanager decides who hears about a problem. Grafana shows the same data to humans as dashboards. The OpenTelemetry Collector is a small agent that runs on each node. It takes logs and traces off the node and sends them on to Loki, the log store, and to a trace store.

```mermaid
flowchart LR
  DCGM["DCGM exporter 4.9.0, one pod per GPU node"] --> PROM
  VLLM["vLLM engines and the gateway, /metrics"] --> PROM
  OTEL["OpenTelemetry Collector agent, one per node"] --> LOKI["Loki, single binary"]
  OTEL --> TRACE["Trace store, not installed here"]
  OTEL -- "own metrics, port 8888" --> PROM
  PROM["Prometheus via the Operator: rules and burn-rate alerts"] --> AM["Alertmanager: route, inhibit, Watchdog"]
  AM --> PAGE["On-call page"]
  AM --> TICKET["Ticket queue"]
  AM --> DEAD["Dead man's switch"]
  PROM --> GRAF["Grafana: dashboards from files"]
  LOKI --> GRAF
```

Each box in the diagram carries three things: a pinned version, a file that configures it, and a test that proves it works. The table is the lookup you will come back to most. Its versions are the ones pinned in the files and fetched on 2026-11-10.

| Part | Version pinned | File in code/part19 | Proved by |
|---|---|---|---|
| Prometheus Operator stack | chart 93.1.1, Prometheus v3.16.0, Alertmanager v0.34.2, Grafana 13.3.0 | `c07_values_kps.yaml` | helm template, kubeconform, selector and secret tests |
| DCGM exporter | chart 4.9.0 | `c07_values_dcgm.yaml` | helm template, field-name test against the chart's counter list |
| Loki | chart 7.5.0, Loki 3.6.16 | `c07_values_loki.yaml` | helm template with the chart schema |
| OpenTelemetry Collector | chart 0.178.2, image 0.164.0 | `c07_values_otel.yaml` | rendered config checked with the collector's own validate command |
| Platform alert rules | not applicable | `c07_stack_rules.yaml`, `c07_rules_test.yaml` | promtool check and promtool test |
| SLO burn-rate rules | Chapter 20.19 files | `code/part20/slo_*.yaml` by reference | promtool scenarios and the Docker run |
| Alertmanager config | amtool 0.31.1, test server 0.35.0 | `c07_alertmanager.yaml` | amtool check and route tests, Docker run |
| Dashboard | Grafana schemaVersion 41 | `c07_dashboard_gpu_platform.json` | structure check, promtool parse, queries through Grafana |
| Series budget | Prometheus budget 2,000,000 | `c07_metric_spec.json` | estimator and linter from Chapter 20.15 |

The Alertmanager row needs a closer look, because its versions do not agree. The chart deploys v0.34.2. The `amtool` command on the host is 0.31.1. The Docker test runs 0.35.0. The configuration parses in all three places, which is reassuring. A production team should still pin one version and use it everywhere, so that the tests check the same program that runs in the cluster.

**Decision rule:** Before you build anything, write down one version and one test for each box on the diagram.

**In one minute:** The stack has three layers. Exporters produce the signals, Prometheus and Loki store them, and Alertmanager and Grafana tell people. Every layer here has a pinned version and a test. A box without a test is unproven, however well it seems to work.

---
## 2. The foundation: kube-prometheus-stack

A team installs the stack with the default values and feels good about it. A month later someone adds a ServiceMonitor for the GPU exporter, and nothing gets scraped. The cause is a selector. A selector is the label filter that tells the Operator which objects to pick up. By default the Operator only picks up objects that carry the Helm release label, which is the tag Helm stamps on what it installs. Nobody on the team knew that, and the stack gave no warning.

The Prometheus Operator is a program that runs inside Kubernetes and manages the monitoring pieces for you. Production Kubernetes explains why it exists. It turns Prometheus servers, Alertmanager, scrape targets and rules into Kubernetes objects, so you describe what you want in a file and the Operator makes it happen. Production Kubernetes says the ServiceMonitor is the most common of those objects. The kube-prometheus-stack chart packages the Operator together with Grafana, node-exporter and kube-state-metrics. The values file below changes the chart defaults that matter for a GPU platform.

The file is `code/part19/c07_values_kps.yaml`.

```yaml
# kube-prometheus-stack 93.1.1 (app v0.95.1). Namespace: monitoring. Release: kps.
# Chart facts checked against the chart's own values.yaml and CRDs, 2026-11-10.
# Install:
#   helm install kps prometheus-community/kube-prometheus-stack --version 93.1.1 \
#     -n monitoring --create-namespace -f c07_values_kps.yaml
fullnameOverride: kps

defaultRules:
  create: true

prometheus:
  prometheusSpec:
    # Pick up ServiceMonitor, PodMonitor and PrometheusRule objects from any
    # namespace and without the Helm release label.
    serviceMonitorSelectorNilUsesHelmValues: false
    podMonitorSelectorNilUsesHelmValues: false
    ruleSelectorNilUsesHelmValues: false
    scrapeInterval: 30s
    evaluationInterval: 30s
    retention: 15d
    retentionSize: 80GB
    # Cardinality guard 1: a scrape that returns more samples than this fails.
    enforcedSampleLimit: 100000
    # Cardinality guard 2: a scrape with more labels on one series than this fails.
    enforcedLabelLimit: 30
    resources:
      requests:
        cpu: "1"
        memory: 8Gi
      limits:
        memory: 8Gi
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi

alertmanager:
  alertmanagerSpec:
    replicas: 2
    # Secret in the monitoring namespace with the key alertmanager.yaml.
    # Create it from c07_alertmanager.yaml (see the lab). Other keys in the
    # Secret are copied into /etc/alertmanager/config.
    configSecret: alertmanager-gpu-platform
    # Secrets listed here are mounted under /etc/alertmanager/secrets/<name>/.
    secrets:
      - alertmanager-receivers

grafana:
  admin:
    # Secret with keys admin-user and admin-password. Create it yourself.
    existingSecret: grafana-admin
  sidecar:
    dashboards:
      enabled: true
      label: grafana_dashboard
      labelValue: "1"
      searchNamespace: ALL
  additionalDataSources:
    - name: Loki
      uid: loki
      type: loki
      access: proxy
      url: http://loki.monitoring.svc.cluster.local:3100
```

Read the file from the top, one setting at a time. The `fullnameOverride` of `kps` keeps service names short, so you can type them without fuss. The three `NilUsesHelmValues` settings matter most. Setting them to false tells the Operator to stop filtering by the release label. In the chart's rendering, that turns the service monitor and rule selectors into empty selectors, and a test checks both. An empty selector matches everything in the cluster. That is what you want here, and it is also why you must know it is there.

The two enforced limits are the first guard against cardinality. Cardinality means the count of distinct time series, and every new label value multiplies that count. A scrape over 100,000 samples fails. A series with more than 30 labels also fails. The chart comments say the sample limit overrides any per-target limit. These numbers are starting points that this chapter chose as a reasonable default, not as a rule. Measure `scrape_samples_scraped` on your largest target before you keep them. Note that kube-state-metrics on a large cluster may already be above 100,000 samples, and then the whole scrape would fail.

The size cap of 80 GB matters too, because it limits how much history Prometheus keeps on disk. It interacts with the series budget, and Section 8 shows the effect.

The Alertmanager block uses `configSecret`. A Secret is a Kubernetes object that holds sensitive settings. This one must sit in the same namespace and carry the key `alertmanager.yaml`, and the Operator's custom resource definition, which is the schema for its objects, says so. If the Secret or that key is missing, the Operator quietly installs a minimal config with one empty receiver. A receiver is the place an alert is sent to. In practice, that means alerts are silently dropped. Section 5 adds a test that the Watchdog alert reaches a receiver, so this failure gets caught.

The `secrets` list mounts each named Secret as files inside the Alertmanager container, under `/etc/alertmanager/secrets/<name>`. The receiver tokens live in those files, outside Git, so the repository never holds a password. The Grafana block reads the admin login from a Secret that you create yourself. It also turns on the dashboard sidecar, which is a small helper container that watches for dashboards. The sidecar loads any ConfigMap that carries the label `grafana_dashboard` with the value `1`. A dashboard is installed by adding a labelled file, not by clicking through the user interface.

**Decision rule:** Before you add a scrape target, check that a Prometheus object selects it. Before you rely on any alert, check that the Alertmanager Secret exists.

**In one minute:** The chart defaults hide your own objects behind a release label, so turn that filter off. Cap the scrape size, and mount receiver secrets from outside Git. A missing Alertmanager Secret drops alerts without any error, so test that a canary alert, a test alert that must arrive, really arrives.

---
## 3. GPU and engine signals

An engineer upgrades the DCGM exporter chart from a 4.8 release to 4.9.0 on a Friday afternoon. The pods start cleanly, and the scrape targets stay green on the status page. On Monday the GPU dashboard shows nothing, and the temperature alert has not fired all weekend. Nothing is broken inside Prometheus. The names changed, and every query still asks for the old ones.

Start with the release notes for dcgm-exporter 4.9.0. They say the release renames default metrics and labels, changes some units, and changes the configuration and Helm values formats. A unit is what a number measures, such as megahertz or bytes. A changed unit makes an old query return a wrong answer, or none at all. The notes list 23 renamed fields, and eleven of them change unit. Clocks move from megahertz to hertz. Utilization moves from a percentage to a ratio between 0 and 1. GPU memory moves from mebibytes to bytes.

The table below lists the names this platform uses. Every one of them appears in the chart's default counter file, which is the list of fields the exporter publishes. A test checks that for you.

| Signal | Name in 4.9.0 | Unit or meaning |
|---|---|---|
| GPU utilization | `DCGM_FI_DEV_GPU_UTIL_RATIO` | ratio from 0 to 1 |
| Memory used and total | `DCGM_FI_DEV_FB_USED_BYTES`, `DCGM_FI_DEV_FB_CAPACITY_BYTES` | bytes |
| Temperature | `DCGM_FI_DEV_GPU_TEMP_CELSIUS` | degrees Celsius |
| Last Xid | `DCGM_FI_DEV_XID_ERROR` | value of the last Xid seen |
| Row remap failure | `DCGM_FI_DEV_ROW_REMAP_FAILED` | whether row remapping failed |

Chapter 17.4 and the file `code/part17/gpu_alerts.yaml` still use the older names, such as `DCGM_FI_DEV_GPU_UTIL` and `DCGM_FI_DEV_GPU_TEMP`. Those names match exporter releases before 4.9.0. On a 4.9.0 chart, the same queries return nothing. This is a good example of a failure that a unit test of the rule alone would miss. The rule's test passes, because the test feeds the rule the names it expects. The test that catches the problem reads the chart's counter file and checks every name the platform uses.

The DCGM values file is `code/part19/c07_values_dcgm.yaml`, and it is short. A DaemonSet is a Kubernetes object that runs one copy of a pod on each matching node. This file limits that DaemonSet to nodes that GPU Feature Discovery has labelled, as Chapter 11.3 explains. GPU Feature Discovery is the component that reads what a GPU node has and writes it onto the node as labels. The file also replaces the default toleration list with one for the GPU taint. A toleration lets a pod run on a node that has a matching taint, which is a marker that keeps ordinary pods away. That taint key is a common cloud default, but it is an assumption, so check it on your nodes. Last, the file adds a relabeling that copies the pod's node name into a label called `node`. Every platform rule groups by that label, so it has to be there.

LLMs in Production warns that models can fail silently. They keep running and return poor answers, and no error appears. The list it gives for what to monitor has three kinds of metric: resource metrics, performance metrics such as latency and queries per second, and operational metrics such as status codes and error rates. The vLLM and gateway metrics in this chapter come from Chapter 20.19, which checked every name against vLLM v0.32.0. Generative AI on Kubernetes names the vLLM time-to-first-token histogram `vllm:time_to_first_token_seconds`, which matches Chapter 20.19. Scalable Kubernetes Infrastructure for AI Platforms lists the cache usage and the waiting and running request gauges as the vLLM signals to watch. Those names differ from the ones Chapter 20.19 verified for vLLM v0.32.0. The likely explanation is that the engine renamed them in a later release. That is an inference, not something that source states. Use the names in Chapter 20.19, and check them against your own vLLM version.

The platform rules are the second file, and they follow one severity policy. Only burn-rate alerts page a person. Everything in this file opens a ticket instead, which follows the symptom-first advice of Chapter 20.19. A symptom is what a user feels, such as slow answers. A cause is something behind it, such as one bad GPU. The file also carries guards for the pipeline itself, so a broken collector or a dead scrape target gets reported too.

```yaml
# Platform alert rules for the observability capstone (Chapter 19.7).
# GPU metric names are the dcgm-exporter 4.9.0 names (suffixes _CELSIUS, _RATIO, _BYTES).
# SLO burn-rate rules are not repeated here: they live in code/part20 and the
# acceptance tests load them from there (slo_recording_rules.yaml and
# slo_burn_alerts_availability.yaml).
# Severity policy: only burn-rate alerts page. Everything here is a ticket.
groups:
  - name: c07_gpu_health
    interval: 30s
    rules:
      - alert: GPUXidError
        expr: max by (node, gpu) (DCGM_FI_DEV_XID_ERROR) > 0
        labels: {severity: ticket, area: gpu}
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} reported Xid {{ $value }}"
          runbook: "runbooks/gpu-xid.md"
      - alert: GPUTemperatureHigh
        expr: max by (node, gpu) (DCGM_FI_DEV_GPU_TEMP_CELSIUS) > 85
        for: 10m
        labels: {severity: ticket, area: gpu}
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} is above 85 C for 10 minutes"
          runbook: "runbooks/gpu-thermal.md"
      - alert: GPURowRemapFailed
        expr: max by (node, gpu) (DCGM_FI_DEV_ROW_REMAP_FAILED) > 0
        labels: {severity: ticket, area: gpu}
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} failed a memory row remap"
          runbook: "runbooks/gpu-rma.md"
      - alert: DCGMMetricsMissing
        expr: absent(DCGM_FI_DEV_GPU_UTIL_RATIO)
        for: 10m
        labels: {severity: ticket, area: pipeline}
        annotations:
          summary: "No DCGM GPU utilisation series for 10 minutes"
          runbook: "runbooks/dcgm-missing.md"

  - name: c07_observability_pipeline
    interval: 30s
    rules:
      - alert: ObservabilityTargetDown
        expr: up{namespace="monitoring"} == 0
        for: 5m
        labels: {severity: ticket, area: pipeline}
        annotations:
          summary: "Scrape target {{ $labels.job }} {{ $labels.instance }} is down"
          runbook: "runbooks/target-down.md"
      # Budget: 2,000,000 head series per Prometheus shard. Alert at 80 percent.
      - alert: TSDBHeadSeriesNearBudget
        expr: prometheus_tsdb_head_series > 1600000
        for: 15m
        labels: {severity: ticket, area: cardinality}
        annotations:
          summary: "Prometheus head series passed 80 percent of the 2,000,000 budget"
          runbook: "runbooks/cardinality.md"
      - alert: ScrapeSampleLimitHit
        expr: increase(prometheus_target_scrapes_exceeded_sample_limit_total[10m]) > 0
        labels: {severity: ticket, area: cardinality}
        annotations:
          summary: "A scrape was rejected for exceeding the sample limit"
          runbook: "runbooks/cardinality.md"
      - alert: OtelCollectorRefusingData
        expr: sum(rate({__name__=~"otelcol_receiver_refused_(log_records|spans)"}[5m])) > 0
        for: 5m
        labels: {severity: ticket, area: pipeline}
        annotations:
          summary: "An OpenTelemetry Collector is refusing logs or spans"
          runbook: "runbooks/otel-refusing.md"
      - alert: OtelCollectorExportFailing
        expr: sum by (exporter) (rate({__name__=~"otelcol_exporter_send_failed_(log_records|spans)"}[5m])) > 0
        for: 5m
        labels: {severity: ticket, area: pipeline}
        annotations:
          summary: "OpenTelemetry exporter {{ $labels.exporter }} is failing to send"
          runbook: "runbooks/otel-export.md"
```

When you read the table, notice that the new names keep the same metric family prefix, DCGM_FI_DEV_, and change only the part after it. That is a small detail with a large effect. A search for the old prefix still finds the old queries, so a quick text search across the repository is a useful first pass after an upgrade. It will not catch everything, though. A rule can be written against a name that is also a valid name in the new release, but with a different unit, and then the query runs and returns the wrong number. The unit change is the sneakier problem, which is why the table lists units beside the names.

Two rules deserve a comment. An Xid is an error code that the NVIDIA driver writes when a GPU misbehaves. The Xid alert has no `for` clause. A for clause makes an alert wait until its condition has held for some time. An Xid is a single event, though, and waiting would only add delay. The gauge keeps the last value it saw, and whether that value clears after a recovery has not been verified here. Chapter 19.6 treats the Xid codes in detail. The collector rules match the metric name with a regular expression, which is a pattern that can match more than one name. That way a missing span counter does not blank the alert for logs.

The unit tests live in `code/part19/c07_rules_test.yaml`. A unit test feeds the rule made-up numbers and checks what it does. There are 11 test cases. Each alert gets a firing case, where the alert must fire, and a quiet case, where it must stay silent. A pytest check then asserts that every alert in the rule file appears in at least one test, so a new alert without a test fails the suite. Another test changes a threshold in a temporary copy and confirms that the unit tests then fail. That second test proves the first one can catch a real change.

**Decision rule:** After every exporter upgrade, compare the names your rules and dashboards use with the exporter's own default counter list. Do this before you trust any graph.

**In one minute:** dcgm-exporter 4.9.0 renamed fields and changed units, so older queries return nothing and raise no error. Pin the chart, write the rules with the new names, and test those names against the chart itself. Page on burn rate, and send causes to a ticket.

---
## 4. SLOs and burn-rate alerts

A team writes an alert that fires when the error ratio passes one percent. Then a ten-second blip pages the on-call engineer at 2 a.m. A week later, a slow leak of errors runs for three days, and nobody gets paged at all. Both outcomes come from the same alert behaving exactly as it was written. The alert is the problem, not the night shift.

Chapter 20.19 explains the fix and gives the numbers. An SLO, or service level objective, is a target such as 99.9 percent of requests going well. The error budget is what the target leaves over, so for a 99.9 percent SLO it is 0.1 percent of requests. A helpful way to think about it is a bank account. The budget is the money you may spend in a month, and the burn rate is how fast you are spending it. Spending at exactly the allowed pace uses the whole budget by the end of the window. Spending twice as fast empties it in half the time. Alerts must react to both kinds of spending, and they must not react to a single expensive purchase that does not change the pace. A burn rate of 1 spends the whole budget across the window. The page alerts use two burn rates, 14.4 and 6, and each one uses a long window and a short window together. This chapter does not repeat that work. It reuses the rule files in `code/part20` and proves that they page the way the theory says.

The proof uses synthetic signal injection. That means you create a fake fault on purpose and watch what the alerts do. The file `code/part19/c07_signals.py` describes a fault with two inputs: the number of requests per minute and the share of them that fail. It then uses those same inputs in two ways. First, it writes a promtool test that feeds the counters to the real rule files. Second, it evaluates the multiwindow policy in plain Python, using the calculator from Chapter 20.19. The runner compares the two answers. If the rule file and the model disagree, one of them is wrong, and the scenario that differs tells you where to look.

Four scenarios run in the suite. Each one sends 6,000 requests per minute for 70 minutes. The table lists what the model predicts and what promtool confirmed. Read the rows as a story about one service over about an hour.

| Scenario | Errors | Minute checked | Fast alert | Slow alert |
|---|---|---|---|---|
| Healthy | 0.05 percent | 30 and 65 | quiet | quiet |
| Fast burn | 3 percent for 70 minutes | 10 and 65 | fires | fires |
| Slow leak | 0.8 percent | 30 and 65 | quiet | fires |
| Blip | total failure for 3 minutes, then clean | 2 | fires | fires |
| Blip | same | 10 | quiet | fires |
| Blip | same | 65 | quiet | quiet |

The blip rows are the lesson, so read them slowly. At minute 2 both alerts fire, because both windows are full of failures. At minute 10 the fast alert is quiet again, since its 5-minute window is clean. The slow alert still fires, because its 30-minute window still holds the blip. A three-minute outage therefore keeps the slow page open for about half an hour. That sounds odd at first, but it is how the policy is built. It also explains why the slow rule is a page and not a log line. The row at minute 65 shows both alerts closing once the windows are clean.

**Decision rule:** Test every burn-rate rule with at least one fault that must fire it and one fault that must not.

**In one minute:** Reuse the Chapter 20.19 rules, and prove them with injected faults. The Python model and promtool must agree on every scenario. A short blip pages the fast rule while it lasts, and it keeps the slow rule open for about thirty minutes.

---
## 5. Alertmanager: routing that is tested

Two weeks after a migration, nobody has been paged. The dashboards show alerts firing, yet the phone stays silent. The cause is a route that matched on a label no rule ever sets. A route is a rule that decides where an alert goes, so this one never matched anything. The alerts fell through to a default receiver, which sends them to a mailbox nobody reads. The configuration was valid, and the tool accepted it. It was never tested.

The Alertmanager file has three routes and one inhibit rule. An inhibit rule hides some alerts while a bigger one is active, so you are not flooded with symptoms of one fault. The Watchdog is an alert that always fires. It goes to a dead man's switch, which is an outside service that expects the Watchdog to keep arriving. Production Kubernetes calls this out as one of the most important alerts. If the alerting system goes down, the switch stops hearing the Watchdog and raises the alarm. Alerts with `severity="page"` go to the on-call service. Alerts with `severity="ticket"` go to a ticket queue, and so does anything without a severity label.

```yaml
# Alertmanager configuration for the GPU platform. Loaded from the Secret
# alertmanager-gpu-platform (key alertmanager.yaml), see c07_values_kps.yaml.
# Secret files are mounted by the operator at /etc/alertmanager/secrets/<secret>/
# and are created outside Git, mode 0400 inside the Secret volume.
route:
  receiver: ticket-queue
  group_by: [alertname, model, node]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    # The always-firing Watchdog goes to a dead man's switch, never to humans.
    - matchers: [alertname="Watchdog"]
      receiver: deadman
      group_wait: 0s
      group_interval: 1m
      repeat_interval: 1m
    - matchers: [severity="page"]
      receiver: oncall-page
      group_wait: 10s
      repeat_interval: 1h
    - matchers: [severity="ticket"]
      receiver: ticket-queue
      repeat_interval: 12h

inhibit_rules:
  # A node that is not ready explains every GPU alert on it.
  - source_matchers: [alertname="KubeNodeNotReady"]
    target_matchers: [area="gpu"]
    equal: [node]

receivers:
  - name: oncall-page
    pagerduty_configs:
      - routing_key_file: /etc/alertmanager/secrets/alertmanager-receivers/pagerduty-routing-key
  - name: ticket-queue
    webhook_configs:
      - url_file: /etc/alertmanager/secrets/alertmanager-receivers/ticket-webhook-url
  - name: deadman
    webhook_configs:
      - url_file: /etc/alertmanager/secrets/alertmanager-receivers/deadman-url
        send_resolved: false
```

Why not simply read the rendered file by eye? Because a route tree is a small program. Each alert label is matched against each route in order, and the first match wins. A reviewer can read the file and believe it is correct while a single misspelled label quietly sends every page to the wrong place. A test walks the tree the same way Alertmanager does, so the answer comes from the program and not from a reader's memory of the program.

The secrets rule is simple. No token or URL appears in the file itself. The pager key and the two webhook URLs are read from files that the Operator mounts from the `alertmanager-receivers` Secret. The Alertmanager documentation lists `routing_key_file` for the PagerDuty receiver and `url_file` for the webhook receivers. A test checks that no inline secret field exists. Create each file with mode 0400, which means only the owner can read it, and keep the files out of Git. The host `amtool` 0.31.1 accepts this file. The Docker run swaps the real receivers for plain webhooks, so reading the real secret files is not exercised there.

The inhibit rule uses the matcher syntax with `source_matchers`, `target_matchers` and `equal`. A matcher is a small test on a label, such as severity equals page. The Alertmanager docs mark the older `source_match` forms as deprecated, so new files should avoid them. This rule says that a node that is not ready explains every GPU alert on that same node, so those GPU alerts are held back. The alert name `KubeNodeNotReady` comes from the chart's default rules. A test renders the chart to confirm that it and the Watchdog both exist, because an inhibit rule that names a missing alert does nothing at all.

Two kinds of test prove the file. The first is offline. `amtool config routes test` prints the receiver an alert would reach, and the test asserts four routes, including the fall-through route that catches everything else. The second is live. The Docker run starts a real Alertmanager with the same route tree and inhibit rule. It posts a not-ready alert for node n2, then a GPU alert for n2 and another for n3. The n3 alert reaches the ticket receiver. The n2 alert does not. The API reports that alert as suppressed, with a non-empty `inhibitedBy` field that names the rule that held it back.

**Decision rule:** Never ship a route tree that you have not walked with `amtool config routes test`, and sent at least one real alert through to each receiver.

**In one minute:** Route on severity, send the Watchdog to a dead man's switch, and keep secrets in mounted files. Prove the tree with amtool and with a real Alertmanager. An inhibit rule needs a positive case, where it must hide an alert, and a negative case, where it must let one through.

---
## 6. Logs and traces: Loki and the OpenTelemetry Collector

Follow one log line through the pipeline to see why each step matters. A container writes a line to a file on the node. The collector's file reader picks it up and attaches the pod and namespace from the metadata processor. The memory limiter checks that the agent has room to hold it, and the batch step groups it with its neighbours. Finally the line leaves the node for Loki over OTLP. Each step can fail on its own, and the collector counters are how you find out which step lost the line.

An incident review needs the error logs from the minute the alert fired. The logs exist, but each node shipped them with a different label scheme, so the same service has a different name on every node. The engineer spends an hour joining them by hand. A single collector configuration, which adds the same metadata at the edge of every node, removes that hour of work. The edge here means the node itself, before the logs leave it.

Production Kubernetes lists three ways to get container logs off a node. The application can forward them itself. A sidecar, which is a helper container that runs beside the application, can forward them. Or a node agent can read the log files directly. Production Kubernetes recommends the node agent, because it gives one place to filter logs, add metadata and change the backend later. This capstone follows that advice and uses the OpenTelemetry Collector as the node agent. The same book also warns about the cost of that choice. The agent becomes a single point of failure for its node, so it needs its own alerts. Section 3 has them.

The collector values file turns on two presets. A preset is a ready-made bundle of settings. The log preset adds the file-reading receiver, which is the part that reads log files, plus the volume mounts it needs. The metadata preset adds the processor that tags every record with its pod and namespace. The pipeline then limits memory first, so a burst cannot crash the agent. After that it adds metadata, removes one sensitive header, and groups records into batches. The logs go to Loki over its OTLP endpoint, which is the address that accepts OpenTelemetry data. The traces go to a trace store, and this chapter does not install one.

```yaml
# opentelemetry-collector chart 0.178.2. One agent per node (DaemonSet).
# The chart default image is 0.163.2. This file pins 0.164.0, the version the
# rendered config is validated against in test_c07_stack.py.
# Install:
#   helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
#   helm install otel-agent open-telemetry/opentelemetry-collector --version 0.178.2 \
#     -n monitoring -f c07_values_otel.yaml
mode: daemonset
fullnameOverride: otel-agent

image:
  repository: otel/opentelemetry-collector-contrib
  tag: "0.164.0"

presets:
  logsCollection:
    enabled: true
  kubernetesAttributes:
    enabled: true

config:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: ${env:MY_POD_IP}:4317
        http:
          endpoint: ${env:MY_POD_IP}:4318
    # Replace the chart defaults so only the receivers named in the pipelines exist.
    jaeger: null
    zipkin: null
    prometheus: null
  processors:
    memory_limiter:
      check_interval: 1s
      limit_percentage: 80
      spike_limit_percentage: 25
    batch:
      timeout: 1s
      send_batch_size: 1024
    # Never ship an Authorization header into the trace store.
    attributes/redact:
      actions:
        - key: http.request.header.authorization
          action: delete
  exporters:
    otlphttp/loki:
      endpoint: http://loki.monitoring.svc.cluster.local:3100/otlp
    otlp/tempo:
      endpoint: tempo.monitoring.svc.cluster.local:4317
      tls:
        insecure: true
    debug: null
  service:
    telemetry:
      metrics:
        readers:
          - pull:
              exporter:
                prometheus:
                  host: 0.0.0.0
                  port: 8888
    pipelines:
      logs:
        receivers: [otlp, filelog]
        processors: [memory_limiter, k8sattributes, batch]
        exporters: [otlphttp/loki]
      traces:
        receivers: [otlp]
        processors: [memory_limiter, k8sattributes, attributes/redact, batch]
        exporters: [otlp/tempo]
      metrics: null

# Expose the collector's own metrics so Prometheus can scrape them.
ports:
  metrics:
    enabled: true
podMonitor:
  enabled: true
  metricsEndpoints:
    - port: metrics
```

Three things were surprising, and each one is a reason to test the rendered output and not the values file.

First, the chart rewrites component names. The values file says `otlphttp/loki`, but the chart's output says `otlp_http/loki`. It also renames `filelog` to `file_log` and `k8sattributes` to `k8s_attributes`. The collector image 0.164.0 accepts the rendered names. A reader who greps the live config for the names in the values file will find nothing, and that looks like a bug when it is only a rename.

Second, the metadata processor reads the node name from an environment variable called `K8S_NODE_NAME`. An environment variable is a named setting that a process reads when it starts. The first validation attempt failed with a message that the variable was not set. Inside the cluster, the DaemonSet sets it. On a laptop nothing sets it, so the validation command needs it passed in. The test passes it with `-e`.

Third, the chart's default image is 0.163.2, while the values file pins 0.164.0. The pin is checked with `validate` only. The full chart output was not run, because the metadata processor needs a live Kubernetes API to do its work. A check that only validates the config cannot tell you whether that processor will behave correctly in the cluster.

The test extracts the rendered ConfigMap and runs the pinned image's `validate` command on it. It mounts only that one file, so the image sees nothing else. To prove the check can fail, the test also makes a broken copy, in which the first processor is replaced by one that does not exist. That copy must fail. Both outcomes are asserted, so a check that always passed would be caught too.

Loki follows the same idea in a smaller file. Loki is the log store. It runs here as a single binary, which means one process, with filesystem storage. That layout suits a lab and a small platform. Chapter 20.15 covers what changes at high volume. The Loki documentation says that OTLP ingestion needs structured metadata, which is on by default from Loki 3.0. The values file sets it explicitly anyway, so the intent is visible. The default index labels include the Kubernetes namespace, pod and container names. Loki stores the namespace as a label whose dots become underscores, so the dashboard query uses `k8s_namespace_name`. That mapping is an inference from the documentation and the label list. The documentation does not state it, and Loki was not run here.

The file is `code/part19/c07_values_loki.yaml`. It sets the deployment mode to single binary. It uses schema version 13, with the TSDB store on the filesystem, and it turns structured metadata on. It keeps 168 hours of retention and sets zero replicas for every other mode. It also turns off MinIO, the caches and the canary, and enables the chart's service monitor. MinIO is an object store that the chart can bring along, and the canary is a test writer that checks the store. Helm rendered the file against the chart schema without error. A deployment mode that was not a string did fail to render. Several other bad values did not fail, though, so treat the schema as a weak guard.

The collector's own metrics matter as much as the logs. If the agent refuses data or fails to send it, the logs are gone and no one notices. Collector 0.164.0, with the Prometheus reader on port 8888, exposed these names after one log record was sent: `otelcol_receiver_accepted_log_records`, `otelcol_receiver_refused_log_records` and `otelcol_receiver_failed_log_records`. There was no `_total` suffix on any of them. A second run pointed an exporter at a dead address and produced `otelcol_exporter_send_failed_log_records`, with exporter and server labels. The platform alert rules use exactly these names. The collector docs also list some names with `_total`, so check your own version before you trust a rule written for another one.

**Decision rule:** Validate the rendered collector config with the collector's own command. Alert on the collector's own refusal and send-failure counters, because those counters are the first sign that logs are being lost.

**In one minute:** Use a node agent, as Production Kubernetes recommends, and let the chart add the metadata. The chart rewrites component names, so test its output and not your input. Watch the agent itself too, because it can fail silently and take a whole node's logs with it.

---
## 7. Dashboards as code

During an incident, someone edits a dashboard by hand to add one useful panel. The change is never saved anywhere. Three months later a redeploy restores the old version, and the panel everyone relied on is gone. Keeping the dashboard JSON in Git and loading it from a file fixes that. JSON is the plain-text format Grafana uses to store a dashboard. The fix works only if something checks the file before it goes live.

The dashboard has 11 panels. Ten query Prometheus, and one queries Loki. Each panel names its datasource by a fixed uid, which is a unique identifier, and the uids are `prometheus` or `loki`. The uid `prometheus` matches the one that the stack chart provisions by default, so the panels connect without any manual step. A variable called `model` is filled from the vLLM waiting-request gauge and feeds four panels. A variable is a drop-down at the top of a dashboard that changes what every panel shows.

| Panel | Expression summary | Why it is there |
|---|---|---|
| GPU utilization by node | average of the utilization ratio per node | USE method, utilization |
| GPU memory used share | memory used divided by capacity per node | USE method, saturation of memory |
| GPU temperature | maximum per node and GPU | thermal trouble |
| Last Xid per GPU | maximum of the Xid gauge | USE method, errors |
| vLLM requests waiting | sum of the waiting gauge per model | saturation of the engine |
| vLLM KV cache usage | maximum of cache usage per model | saturation of memory in the engine |
| Availability burn rate | one-hour error ratio divided by 0.001 | how fast the budget burns |
| Gateway TTFT p99 | recorded 99th percentile of time to first token | user-visible latency |
| Prometheus head series | head series gauge | budget watch |
| Collector refusals | rate of refused log records and spans | pipeline health |
| Error logs | Loki query on the llm-serving namespace | context for a page |

The table follows two methods from Systems Performance. The USE method asks for utilization, saturation and errors for every resource. Saturation means work waiting in line for a resource that is already full. The RED method asks for rate, errors and duration for every service, where duration means how long each request takes. Systems Performance says the first suits machine health and the second suits user health. The dashboard shows both on purpose. The same book warns that a five-minute average can hide short bursts of saturation, which is why the burn-rate alerts pair a long window with a short one.

The check script runs in two stages. The first stage tests the structure of the dashboard, the datasource uids and the dollar variables, which are the variables that start with a dollar sign. The second stage parses every PromQL expression. PromQL is the query language that Prometheus uses.

Think of the check as two gates. The first gate asks whether the dashboard is shaped correctly, with panels that point at real datasources and variables that are defined. The second gate asks whether each query is valid PromQL. Neither gate asks whether the query returns anything useful, and that gap is why the Docker run exists.

Parsing uses promtool and not a home-made grammar. A home-made grammar would drift away from the real one, and then the check would approve queries that Prometheus rejects. The script swaps the rate-interval macro for a plain duration. It swaps the model variable for a regular expression that matches anything. Then it writes each expression into a temporary rule file as a recording rule and runs `promtool check rules` on that file. A bad expression is reported against the panel it came from. The tests break each of these on purpose and require that a report appears.

Parsing proves syntax only. A well-formed query for a metric that no longer exists still passes the parser, and its panel then sits empty. The Docker run closes that gap. Grafana 13.3.0 loads the dashboard from a provisioned file, which means the file is read at startup and nobody clicks it into place. The run then sends each Prometheus panel expression through the Grafana query API and requires data back. All ten panels returned data in the run recorded below.

**Decision rule:** Keep dashboards in Git, parse every expression in continuous integration (CI), and query every panel against test data before you merge.

**In one minute:** A dashboard in Git survives a redeploy. A structural check plus the promtool parser catches broken queries. A query run through Grafana against synthetic data catches the queries that are valid but empty, which the parser alone would miss.

---
## 8. The cardinality budget

A developer adds a user identifier as a label on the gateway request counter. The change looks harmless in review, because it is only one more field. Within a day, Prometheus memory use triples and the dashboards start to time out. One label multiplied every other label, and the cost arrived before anyone noticed.

Cardinality is the count of distinct series, and a series is one unique combination of a metric name and its labels. Chapter 17.1 gives the cardinality rules, and Chapter 20.15 gives an estimator and a label linter. A linter is a checker that reads a file and flags problems in it. This chapter reuses both without copying them. The script `c07_cardinality_budget.py` adds one platform rule. The series the platform declares, plus the series reserved for Kubernetes components, must fit inside the Prometheus budget of 2,000,000 head series. A head series is one series currently held in Prometheus memory.

Think of the budget as a shared pool of space in a warehouse. Some of the space belongs to the platform's own metrics, and some is reserved for the Kubernetes components that run underneath everything. Each new metric family takes a share of what is left. A label that multiplies a family takes far more than its share, and it does so quietly, because no single metric looks large on its own.

The reserved share is an assumption, and this chapter treats it as a placeholder. It is set to 1,000,000 to stand in for kube-state-metrics, cAdvisor and node-exporter. cAdvisor is the component that reports the resource use of containers. Replace the placeholder with the value you measure from your own Prometheus. The declared families are in `code/part19/c07_metric_spec.json`. The example fleet has 50 GPU nodes with 8 GPUs each, 40 vLLM pods and 4 gateway pods.

The estimator works in three steps. It multiplies the label values of each family together, since every combination is a separate series. It applies a fill factor, which assumes that only some of the possible combinations actually appear. Then it counts histogram buckets, because a histogram stores one series per bucket. The results are below. The DCGM line is 26 fields times 8 GPUs times 50 nodes. The 26 is the count of non-label rows in the chart's default counter file, and a test checks that count against the file.

| Family | Series |
|---|---|
| DCGM default fields | 10,400 |
| Gateway TTFT histogram | 1,700 |
| Tenant token counter | 1,600 |
| vLLM TTFT and inter-token histograms | 1,000 each |
| Gateway request counter | 800 |
| vLLM success counter and waiting gauge | 160 and 40 |
| Declared total | 16,700 |

The declared total plus the reserved 1,000,000 gives 1,016,700 series. That leaves 983,300 of headroom under the budget. Next comes disk. The disk estimate for the full 1,016,700 series, at 30-second scrapes over 15 days, is 43.9 GB at one byte per sample and 87.8 GB at two. A sample is one stored value, and the bytes per sample depend on how well the data compresses. The size cap in the values file is 80 GB. At the high end, the cap would delete old blocks before the 15 days are over, so you would keep less history than the retention setting promises. Raise the volume or lower the retention, and decide which one on purpose.

The second file, `c07_metric_spec_bad.json`, is a deliberately bad example. It adds a label called `user_id`, with 50,000 possible values, to the gateway counter. The check rejects it in three ways. The linter flags the forbidden label. The family budget is exceeded, because 40,000,000 series is far above the family limit. The total budget is blown as well. The test asserts all three results. A further test raises the reserved share to 1,990,000 and confirms that the check then fails. That proves the total check is real and not decoration.

The budget is enforced in three places, and each one catches a different kind of mistake. The spec check runs in CI, before a change merges. The scrape limits in Section 2 stop one bad target from flooding Prometheus. The alert from Section 3 warns at 80 percent of the budget, so you have time to act. The Docker run also lints the exporter's real exposition text, which is the raw text that the exporter serves. A bad sample with a request identifier label must fail that lint.

**Decision rule:** Compute the series count of every new metric family before it ships. Fail the build when the total passes the budget.

**In one minute:** A label is a multiplier. Declare the metric families, estimate their series, reserve room for Kubernetes, and fail CI when the sum passes the budget. Back that up with scrape limits and an alert at 80 percent.

---
## 9. The acceptance tests: what each one proves

A platform team announces that the stack is done. A skeptical engineer leans back and asks what would fail if one part broke. A good answer is a map from each part to the test that would catch it. The table below is that map for this chapter, so you can answer the question without guessing.

| Test | Fault or input | Expected result | Where |
|---|---|---|---|
| promtool check and test rules | thresholds, missing series, flat counters | each alert fires or stays quiet as specified | `c07_rules_test.yaml` |
| Changed threshold | threshold raised in a copy | unit tests fail | `test_c07_observability.py` |
| Synthetic SLO scenarios | healthy, fast burn, slow leak, blip | promtool equals the Python model | `c07_signals.py` |
| Route tests | four label sets | each reaches its receiver | `c07_acceptance.py` |
| Dashboard check | five kinds of broken dashboard | each reported | `c07_dashboard_check.py` |
| Cardinality | good spec, bad spec, big reserve | pass, fail, fail | `c07_cardinality_budget.py` |
| Chart tests | helm template, schemas, kubeconform | rendered objects are valid | `test_c07_stack.py` |
| Collector validate | rendered config, broken config | pass, fail | `test_c07_stack.py` |
| Docker end to end | injected faults | each alert reaches its receiver | `c07_e2e.py` |

The Docker run ties the layers together. It starts Prometheus 3.16.0 with the platform rules and the Part 20 SLO rules. It starts Alertmanager 0.35.0 with the real route tree and webhook receivers, and Grafana 13.3.0 with the dashboard. A synthetic exporter and a webhook sink run in small Python containers. Synthetic here means the data is made up for the test. The containers drop all Linux capabilities, which are the special privileges a process could otherwise use. They mount only generated config files, and they mount them read-only. They publish ports on the loopback address alone, so nothing outside the machine can reach them.

An early version ran the exporter and the sink as processes on the host machine. The containers could not scrape them, and the reason was never traced. The final version runs both inside the Docker network instead, which avoids the problem.

The run follows a fixed order. It first checks the Watchdog, to prove the pipeline is alive. Then it waits a minute for healthy traffic to build up. Next it injects four faults at once and polls for up to 150 seconds. Polling means asking again on a timer until the answer arrives. The faults are a GPU Xid, a probe signal, a 100 percent gateway error ratio, and a not-ready alert, with GPU alerts posted straight to Alertmanager.

The recorded result of the run was 16 checks passed and none failed. The full list of checks is in the lab. The check that matters most is "injected 100 percent errors fire the fast burn alert". It shows the whole chain at work. The synthetic counter moves. Prometheus scrapes it. The Part 20 recording rule computes the error ratio. The burn alert fires, Alertmanager routes it by severity, and the page receiver gets it. The run starts with a fresh Prometheus, so its one-hour window holds only a few minutes of data. That is why a few minutes of failure is enough to fire the alert in the test. A production alert would need the full window to fill first, and the promtool scenarios in Section 4 cover that case.

Read the table as a list of questions to ask about your own stack. For each row, ask which fault you would be most afraid of, then find the test that would notice it. If you cannot find one, you have found a gap in the stack, and that is more useful to know before an incident than after.

The probe alert in the end-to-end rules file exists only for the test. It proves the path from a rule to the page receiver without waiting for a real burn. Do not carry it into production, because it fires on a signal that no real service sends.

**Decision rule:** Map every box in the architecture to a test that fails when that box breaks. Run the full chain at least once before each stack upgrade.

**In one minute:** Unit tests prove the rules, scenario tests prove the SLO policy, route tests prove Alertmanager, and chart tests prove the install. The Docker run proves the whole chain. It injected four faults, and each one reached the right receiver.

---
## 10. Hands-on lab

Picture a laptop on a train, with no cluster and no GPU, and a stack you still need to prove works. Most of the lab can run in that situation. The lab has two halves. The first half runs on a laptop. The second half installs the stack on a cluster, which needs GPU nodes. Any step that needs hardware says so.

The first half ran on a laptop for this chapter, and the second half was not run because it needs a cluster with GPUs.

**Tools used here:** the host promtool built from Go module v0.316.0 and the promtool 3.16.0 inside the Prometheus image, amtool 0.31.1, helm v4.2.3, kubeconform, Docker through Rancher Desktop, and Python 3.12 with pytest 8.3.5. The charts were pulled on 2026-11-10 at the versions above.

**Checks left for a cluster:** the cluster install, the DCGM exporter on real GPUs, Loki, the collector with the Kubernetes metadata processor, a trace store, and the real PagerDuty and ticket receivers.

### Step 1. Run the offline acceptance checks

Start here, because these checks need nothing but your laptop, and they fail fast when a tool is missing. You can run them on a plane or in a cafe, and they give the same answer every time, which is what a good first check should do. Run the script below from `code/part19`. It takes a few seconds, and it needs promtool and amtool on the path.

```bash
#!/usr/bin/env bash
# Runs on a laptop with promtool, amtool, helm and Docker. No cluster, no GPU.
set -euo pipefail
cd "$(dirname "$0")"

python3 c07_acceptance.py                                     # offline checks, seconds
python3 -m pytest test_c07_observability.py test_c07_stack.py -q
C07_E2E_TMP="${C07_E2E_TMP:-$PWD}" python3 c07_e2e.py         # Docker, a few minutes
```

The first command prints one line for each check. You should see two lines for promtool, four for the scenarios, one for amtool, four for the routes, one for the dashboard and two for the cardinality spec. The run for this chapter printed 14 passed and 0 failed.

What to record: the pass count and the promtool version. Expected result: 14 passed.

### Step 2. Run the pytest suites

Next come the pytest suites, which check the Python side and the chart renders. The second command in the script runs 42 tests in two files. One more test runs only when the environment variable `C07_E2E` is set. The suites need network access for the chart pulls and the CRD schemas, which are the object definitions the charts are checked against. A test skips with a reason when a tool or the network is missing, so a skip is not a failure.

What to record: passed and skipped counts. Expected result: 42 passed in the run recorded here, and one skipped by default.

### Step 3. Run the Docker end-to-end test

The third command is the long one. It starts the containers, injects the faults and prints one line per check. Those lines are what the run recorded:

```text
PASS amtool accepts the test Alertmanager config
PASS Prometheus scrapes the synthetic exporter and itself
PASS Prometheus loaded the platform rules without error
PASS Watchdog reaches the deadman receiver (no page, no ticket)
PASS synthetic probe reaches the page receiver
PASS injected 100 percent errors fire the fast burn alert at the page receiver
PASS injected Xid 79 reaches the ticket receiver, not the page receiver
PASS a GPU alert on a healthy node (n3) passes the inhibit rule
PASS a GPU alert on the NotReady node (n2) is inhibited
PASS Alertmanager reports the n2 alert as inhibited by KubeNodeNotReady
PASS Prometheus shows the injected alerts as firing
PASS Grafana is healthy
PASS Grafana provisioned the dashboard from the file
PASS every Prometheus panel expression returns data through Grafana
PASS live exposition passes the label policy
PASS Prometheus head series is far below the 1,600,000 alert line
16 passed, 0 failed
```

What to record: the pass count and the time from injection to the page. Expected result: 16 passed. If a check fails, the line names the receiver or panel that failed. The first run of this test failed 8 of 16 checks, because the containers could not scrape an exporter that ran on the host. Moving the exporter into the network fixed that.

### Step 4. Break something on purpose

This step proves that the checks can fail. Change the temperature limit in `c07_stack_rules.yaml` from 85 to 95. Then rerun step 1. The rule unit test must fail. Revert that change. Next, rename one DCGM metric in the dashboard JSON and rerun the Docker test. It must report an empty panel.

What to record: the failing check names. Expected result: the temperature test and one empty panel.

### Step 5. Install the stack on a cluster (not run)

The script `code/part19/c07_lab_cluster.sh` installs all four charts, creates the secrets, wraps the rule files and loads the dashboard. Create the three receiver files first, and keep each at mode 0400. The script needs a GKE or other Kubernetes cluster with GPU nodes that GPU Feature Discovery has labelled.

Expected shape of the output, as a guide and not a record: Helm reports each release as deployed. The Operator creates a Prometheus and an Alertmanager StatefulSet in the `monitoring` namespace. The DCGM exporter DaemonSet has one pod per GPU node. Grafana lists the dashboard under its title after the sidecar syncs.

### Step 6. Fire a real alert on the cluster (not run)

Port-forward to Alertmanager, which means opening a local tunnel to the service, and check that the Watchdog is present. Then scale a test gateway down, or send failing requests, and wait for the burn alert. The page must arrive at the real receiver. The dead man's switch must keep getting the Watchdog the whole time.

**Decision rule:** Do not call the platform ready until step 3 passes on your laptop and step 6 has fired a real page on the cluster.

**In one minute:** Steps 1 to 4 prove the rules, the routes, the dashboard and the chain. Steps 5 and 6 need a cluster. Break a rule on purpose at least once, so you see the tests fail with your own eyes.

---
## Exercises

Imagine your first week on a new platform team. A teammate hands you the stack from this chapter and asks you to change it. Each exercise below is a small request of that kind, and each one starts from the files you have just read.

1. **Add a rule with its test.** Your team wants a warning when GPU memory stays above 95 percent for 10 minutes. Write that alert with the 4.9.0 names. Then add a firing case and a quiet case.

   Solution sketch: start by dividing `DCGM_FI_DEV_FB_USED_BYTES` by `DCGM_FI_DEV_FB_CAPACITY_BYTES`, per node and GPU. Keep the ratio and not a raw byte count, so the threshold reads as a percent. In the test, set used to 77 GB and capacity to 80 GB for the firing case. The pytest that checks every alert for a test will fail until you add yours, and that failure is the reminder you want.

2. **Find the renamed metric.** A dashboard from Chapter 17.4 goes empty after the cluster moves to 4.9.0. Name the three queries you would change first.

   Solution sketch: open the chart's default counter file and compare the names with the queries. Utilization becomes the `_RATIO` name, and the panel unit changes to percent of one. Memory used becomes the `_BYTES` name, and the old megabyte conversion must go. Temperature gets the `_CELSIUS` suffix.

3. **Design a new scenario.** Picture a service that fails 0.1 percent of its requests for 70 minutes. Write that scenario, and predict the result before you run it.

   Solution sketch: here 0.1 percent is the whole budget, so the burn rate is 1. Neither page threshold, 0.006 or 0.0144, is passed, so both alerts should stay quiet. Add the scenario to the list. The Python model and promtool must then agree.

4. **Break the route.** Someone edits the page matcher to `severity="critical"`. Which tests fail?

   Solution sketch: the route test for a page alert falls through to the ticket queue and fails. The Docker run fails the burn alert check at the page receiver. The amtool syntax check still passes, which is why route tests exist.

5. **Size the disk.** Your fleet doubles to 100 GPU nodes. Recompute the series and the disk, and say whether the volume still fits.

   Solution sketch: multiply the 26 fields by 8 GPUs. Then multiply by 100 nodes, which gives 20,800. Change the target count in the spec first. Run the spec check for the new total and the disk formula. Compare the result with the volume and the size cap.

6. **Dead man's switch.** Suppose you stop the deadman receiver in the Docker test. What should happen, and what does the test show?

   Solution sketch: the Watchdog never arrives, so the first end-to-end check fails. In production, the external service would notice the silence and page someone. The lesson is that silence is only a signal if something outside the stack listens for it.

---

## Checkpoint questions

<details><summary>1. Why does the stack set the three NilUsesHelmValues options to false?</summary>
By default the Operator only selects service monitors, pod monitors and rules that carry the Helm release label. Setting them to false makes the selectors empty, so objects without that label are picked up.
</details>

<details><summary>2. What happens if the Alertmanager config Secret is missing?</summary>
The Operator installs a minimal config with one empty receiver, so alerts are dropped without an error. A canary alert that must arrive is the test.
</details>

<details><summary>3. Why do older DCGM queries return nothing on a 4.9.0 exporter?</summary>
The release renamed default fields and changed units. For example the utilization name now ends in a ratio suffix. The scrape still succeeds, so nothing errors.
</details>

<details><summary>4. Which unit changes did 4.9.0 make?</summary>
Clocks moved from megahertz to hertz and utilization moved from a percentage to a ratio. GPU memory moved to bytes and NVLink throughput to bytes per second. Energy moved from millijoules to joules.
</details>

<details><summary>5. Why is the Xid alert a ticket and not a page?</summary>
Chapter 20.19 says to page on user-visible symptoms and keep cause signals for tickets. An Xid is a cause signal.
</details>

<details><summary>6. Why does the Xid rule have no for clause?</summary>
An Xid is a discrete event and the gauge holds the last value, so waiting adds delay and no confidence. Whether the gauge clears after recovery is not verified here.
</details>

<details><summary>7. How does the signals module prove a burn-rate rule?</summary>
It feeds the same per-minute counters to promtool with the real rule files and to a Python model of the policy. The two answers must match for each scenario.
</details>

<details><summary>8. Why does the slow burn alert stay open after a three-minute outage?</summary>
Its 30-minute short window still contains the failed minutes, so both of its windows stay above the threshold until the blip leaves the short window.
</details>

<details><summary>9. What does the inhibit rule say?</summary>
When KubeNodeNotReady fires for a node, alerts with area gpu and the same node are suppressed. The node explains them.
</details>

<details><summary>10. How does the test prove the inhibit rule works and not just parses?</summary>
It posts a not-ready alert and a GPU alert for node n2 and a GPU alert for n3 to a real Alertmanager. The n3 alert is delivered. The n2 alert is not, and the API reports it suppressed.
</details>

<details><summary>11. Why keep receiver secrets in files?</summary>
The config references files such as the routing key file. The Operator mounts the Secret under a known path. The tokens stay out of Git and out of the config.
</details>

<details><summary>12. What did the chart do to the collector component names?</summary>
It rendered otlphttp as otlp_http, filelog as file_log and k8sattributes as k8s_attributes. The pinned collector accepted them.
</details>

<details><summary>13. Why did collector validation fail the first time?</summary>
The metadata processor reads the node name from an environment variable that the DaemonSet sets. Outside the pod the variable was not set, so the test passes it in.
</details>

<details><summary>14. Which collector metric names did the run observe?</summary>
Refused, accepted and failed receiver counters for log records, and a send-failed exporter counter. None had a total suffix on collector 0.164.0 with this telemetry config.
</details>

<details><summary>15. What does parsing dashboard expressions with promtool prove, and what does it not?</summary>
It proves syntax. A well-formed query for a metric that no longer exists passes. Only a query against data catches that.
</details>

<details><summary>16. How does the dashboard check handle Grafana macros and variables?</summary>
It replaces the rate-interval macro with a duration and the model variable with a regular expression that matches anything. Then it parses each expression as a recording rule.
</details>

<details><summary>17. What is the reserved share in the cardinality check and where does its value come from?</summary>
It is the series set aside for Kubernetes components. The value of 1,000,000 is the author's assumption and should be replaced by a measured number.
</details>

<details><summary>18. Why is the disk estimate a concern for the size cap?</summary>
At two bytes per sample the full budget needs about 88 GB, which is above the 80 GB cap. Old blocks would be deleted before 15 days pass.
</details>

<details><summary>19. Why was the exporter moved into a container for the end-to-end test?</summary>
The containers could not scrape a host process, and binding a host process to all interfaces exposes a local service. Running it inside the test network avoids both problems.
</details>

<details><summary>20. What is the probe alert for and why is it not in production?</summary>
It proves the path from a rule to the page receiver without waiting for a real burn. It fires on a synthetic signal that only the test exporter produces.
</details>

---

## Sources and review notes

### Books

- *Production Kubernetes*, Chapter 9 "Observability": node-agent log forwarding, audit logs, alerting on logs, the Prometheus Operator objects, the dead man's switch, showback and chargeback, and tracing. Used for Sections 2, 5 and 6.
- *Systems Performance, 2nd edition*, Chapter 2 "Methodologies" (USE and RED methods, utilization over long intervals, baselines) and Chapter 4 "Observability Tools" (monitoring and exporters). Used for Section 7.
- *LLMs in Production*, Chapter 3 "Large language model operations": the monitoring system section, including silent model failure and what to record. Used in Section 3 and Section 7.
- *Scalable Kubernetes Infrastructure for AI Platforms*, Chapter 4 "Model Deployment and Monitoring": metrics for LLM serving and the vLLM signals. Used in Section 3.
- *Generative AI on Kubernetes*, Chapter 5 "Model Observability": the vLLM time-to-first-token histogram name. Used in Section 3.
- *AI Factory*, Chapter 9: read. It covers distributed computing for industrial AI and supplies no claim here.

### Upstream documents fetched 2026-11-10

- Helm chart indexes and the charts themselves: kube-prometheus-stack 93.1.1, dcgm-exporter 4.9.0, loki 7.5.0 and opentelemetry-collector 0.178.2. Values, CRD descriptions and default counter files read from the pulled archives.
- dcgm-exporter 4.9.0 release notes on GitHub, published 2026-11-06.
- Prometheus documentation for unit testing rules. Alertmanager configuration documentation (main branch).
- Loki documentation for ingesting logs with OpenTelemetry (main branch). OpenTelemetry Collector internal telemetry page.

### Cross-references to other handbook chapters

- Chapters 17.1 to 17.6 for the foundations. Chapter 11.3 for GPU Feature Discovery. Chapter 19.6 for Xid handling and node health.
- Chapters 20.15, 20.19 and 20.25 for the pipeline, the burn-rate rules and the PromQL traps. The code reused from them is `code/part20/slo_recording_rules.yaml`, `slo_burn_alerts_availability.yaml`, `slo_burn_rate.py` and `c15_cardinality.py`.

### Migrated from `nvidia-devops`

None. This chapter was built from the books, the upstream documents and the code, and no passage from `nvidia-devops` Volume 24 or Volume 8 is used. The corpus name `nvidia-devops` appears here for the lab checker only.

### Explicitly labelled inferences

- The enforced sample limit of 100,000, the label limit of 30, the 15-day retention and the 80 GB size cap are my starting values.
- The reserved Kubernetes share of 1,000,000 series, the fleet size and the label counts in the metric spec are assumptions.
- The temperature threshold of 85 and the 10-minute hold are examples. Use your vendor limit.
- The GPU taint key in the DCGM values is an assumption.
- That Loki stores the namespace as a label with underscores is my reasoning from the docs.
- That the vLLM metric names in the Kubernetes book were renamed is my reasoning from comparing it with Chapter 20.19.

### Not verified or not run

- Not run: the cluster install, real GPUs, Loki, the collector with the Kubernetes processor, a trace store and the real receivers. The Helm values were rendered and checked only.
- Not verified: whether the Xid gauge clears after a recovery, and whether the Docker run's Alertmanager 0.35.0 reads secret files, because the test swaps in webhooks. The behaviour of Alertmanager 0.34.2, the chart's version, was not run.
- Part 17.4 and `code/part17/gpu_alerts.yaml` still use pre-4.9.0 DCGM names. This chapter did not edit them.

### Verification log

- Claims checked: 52. Confirmed against a source or by running code: 37. Corrected during writing: 3 (the chart renames component names, the collector names have no total suffix, and the Loki chart schema does not reject most bad values). Removed: 3 (a pod-level DCGM naming claim, an Operator object count and a run-time figure). Still unverified: 9, listed above and in the ledger.
- Gate results are in the ledger `planning/ledgers/19-07.md`.
