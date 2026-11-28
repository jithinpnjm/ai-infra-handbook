---
id: "c17-01"
title: "17.1 Observability foundations: metrics, logs and traces"
sidebar_label: "17.1 Observability foundations"
sidebar_position: 1
description: "Observability foundations for AI infrastructure: the three pillars (metrics, logs, traces), the RED and USE methods, the cardinality budget, the data shape that makes a system debuggable, and the operational pattern that ties observability to the AI workload's lifecycle."
status: "drafted"
tier: "2"
level: "B"
lab_venue: "GCP / GKE"
---

# 17.1 Observability foundations: metrics, logs and traces

| Field | Value |
|---|---|
| Level | Basics |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Cross-references | Chapter 1.23 (Performance methodology); Chapter 16.10 (Monitoring and drift); Chapter 16.14 (Platform design); Chapter 17.2 (Prometheus and Grafana) |
| Coverage file | `planning/coverage/chapters/17-01.md` |
| Claim & number ledger | `planning/ledgers/17-01.md` |

## Observability at a glance

Picture an on-call night when a page arrives and you open the first tool that comes to hand. Some of the time that tool shows the answer, and some of the time it shows nothing useful. The diagram below shows where each kind of evidence comes from, so you know which tool to open first.

```mermaid
flowchart LR
    subgraph Sources["Workloads"]
        W1[HTTP handler]
        W2[Inference engine]
        W3[Training job]
    end

    subgraph Pillars["Three pillars"]
        M[Prometheus<br/>metrics]
        L[Loki<br/>logs]
        T[Tempo<br/>traces]
    end

    subgraph Consumers["Consumers"]
        G[Grafana<br/>dashboards]
        A[Alertmanager<br/>alerts]
        R[Runbooks<br/>recovery]
    end

    W1 --> M --> G
    W1 --> L --> R
    W1 --> T --> A
    W2 --> M
    W2 --> T
    W3 --> M
    W3 --> L
```

Read the diagram from left to right, and notice where you would look first during an incident. Every workload feeds one or more of the three pillars, and each pillar feeds a different consumer. Dashboards show trends, alerts fire when something crosses a line, and runbooks tell the on-call what to do next.

The diagram also shows something easy to miss. A single HTTP handler sends its data to all three pillars, so one slow request leaves a trail in metrics, in logs, and in traces. The three trails only help you when you can line them up by time, and that is why this part of the handbook keeps coming back to the same question: can you move from one pillar to the next without guessing?

## Why this matters for AI infrastructure

Imagine an on-call engineer paged at night because a training job has slowed down. The dashboard is blank, the logs are spread across dozens of pods, and nobody knows which component changed. Without an observability foundation, the first hour of that incident goes to guessing.

![Three stacked boxes: alerting without metrics is guessing, SLOs without traces cannot be checked, and capacity planning without logs rests on assumptions, with arrows pointing down.](./img/g-306.jpg)
*Figure 17.1.V. Metrics, traces, and logs must exist before alerts, SLOs, and capacity plans can be trusted.*


Every chapter in this part depends on this one. Alerting without metrics is guessing. SLOs without traces cannot be checked against real requests. Capacity planning without logs rests on assumptions you cannot test. An SLO here means a service level objective, which is the target a service promises to meet, such as a share of requests that must succeed.

An AI platform emits the same kinds of signals as a web service: requests, errors, and durations. It also emits GPU utilisation, KV cache occupancy (the memory that holds attention state for each active request), collective communication timing, data-loading throughput, and model quality. The three pillars stay the same. The label budget is tighter, and the shape of the data is different.

```text
Why observability is on the critical path (background reading: NVIDIA Zero-to-Hero volume 16; Engineering AI Systems; NVIDIA Zero-to-Hero volume 7; the figures below are examples, not quotations):
- A typical mature AI platform emits 50k-200k unique time series from a single
  cluster. The cardinality budget is the difference between a dashboard that
  loads in 2 seconds and a dashboard that never loads.
- An AI workload failure has more possible causes than a web service failure:
  GPU OOM, NCCL timeout, data drift, model regression, scheduler starvation,
  container image pull rate limit, feature store staleness. Without traces, the
  on-call engineer has to guess which of these caused the page.
- The operational SLOs from Chapter 16.14 (cluster availability, GPU
  availability, registry availability) are measured by the observability stack.
  Without metrics, the SLOs are unmeasurable; the FinOps dashboard is wrong.
```

The numbers in that block come from the chapter's source notes. They are example values, not measurements from this handbook, so check them against your own cluster before you plan around them.

Three realities make this a platform-team job, not only a data-science job.

1. **The observability stack sits under every other chapter.** Alerts, SLOs, capacity models, and runbooks all read from it. A misconfigured stack either pages at the wrong moment or stays silent while the cluster is down.
2. The platform team decides the cardinality budget. Each label you add multiplies the number of series. That choice decides whether Prometheus can store the data and whether the dashboards can draw.
3. The data shape is an architecture decision. The metric format, the log format, and the trace propagation method decide whether your team can debug the next incident.

A cluster without observability is a cluster nobody can debug. Before a team runs an AI workload, the cluster needs a stack that the on-call can query in seconds. The rest of this chapter works through the three pillars, the label budget, the data shapes, and the way the stack itself is run.

## Prerequisites and outcomes

### Prerequisites

Picture a colleague who opens this chapter cold and hits the term USE in the first paragraph. Work through these three chapters first. Each one gives you a method or pattern that this chapter builds on.

- Chapter 1.23 (Performance methodology) for the USE method.
- Chapter 16.10 (Monitoring and drift) for the AI-specific monitoring pattern.
- Chapter 16.14 (Platform design) for the SLO-based platform design.

### Outcomes

Picture a new engineer on your team who gets paged for the first time and cannot find where the logs live. This chapter walks through the three pillars of observability, metrics, logs and traces, and the contracts that link them. It then explains how to choose between the RED and USE methods, how to keep the label budget under control, and how to shape data so that an on-call engineer can debug it. The last part shows how to run the stack on GKE with Prometheus, Grafana, Loki, and OpenTelemetry, and how the metrics match the workload's stage, from training to serving to on-call.

---

## 1. The three pillars

![Metrics, logs and traces and the question each one answers](./img/pre-three-pillars.jpg)

*Figure 17.1.1. Metrics say that something is wrong. Logs say what. Traces say where.*

### 1.1 Metrics, logs, traces: what each is for

Imagine a model endpoint that suddenly takes twice as long to answer. One kind of evidence will not explain it. Chapter 11 of *Engineering AI Systems* walks through the three pillars, and each one answers a different question.

| Pillar | What it is | What question it answers | Cardinality |
|---|---|---|---|
| **Metrics** | Numeric time series with labels | How much, how fast, how often? | Low to medium (10k-200k series) |
| **Logs** | Discrete events with structured fields | What happened at this point in time? | High (millions of events/day) |
| **Traces** | Directed acyclic graph of spans | Where did the time go? | Medium (1k-100k traces/day) |

The ranges in the Cardinality column are example values, not measurements. Your team should size its own limits from what its cluster can store and query.

The three pillars complement each other. Metrics show that something is wrong. Logs show what the system was doing at that moment. Traces show where the time went inside one request. Start with metrics to find the symptom, then open the logs and traces for the same time window. That order keeps you from reading a long pile of log lines before you know which minute matters.

Here is how the three pillars work together on one slow endpoint. The metric panel shows that latency climbed at a particular minute. You then open the logs for that minute and look for errors, retries, or a timeout message from the same service. Finally you open a trace for one of the slow requests and see which span took the time. Each step narrows the question, and each one reuses the time window from the step before.

### 1.2 The RED method for services

Think about a web API that returns errors for ten minutes. You need a few numbers on every service to see that failure quickly. The RED method gives you three: how many requests arrive, how many fail, and how long they take. The name is a memory aid for the three letters, Rate, Errors and Duration. *Production Kubernetes* Chapter 9 introduces the RED method, and every request-driven service should emit these three metrics.

The three measures answer the questions a customer would ask. Is the service taking requests at all? Are those requests succeeding? Are they fast enough to feel acceptable? If any answer is no, you have a reason to look closer. Because the same three questions apply to every service, a team can build one dashboard template and reuse it everywhere.

| Metric | What it measures |
|---|---|
| **Rate** | The number of requests per second |
| **Errors** | The fraction of requests that failed (5xx, 4xx for client errors) |
| **Duration** | The latency of each request (typically p50, p95, p99) |

RED fits serving systems well. An LLM InferenceService emits Rate, Errors, and Duration for each model and each replica. A replica is one running copy of the service. Alerts usually fire on p99 latency and on the error rate. The p99 value is the time that almost all requests finish within, leaving out only the slowest few, so it shows how the slowest requests feel to a customer.

### 1.3 The USE method for resources

A training job can look busy while most of its GPUs sit idle. The USE method asks three questions about every resource, such as a GPU, a memory pool, or a network link. Brendan Gregg's USE method gives you utilisation, saturation, and errors for each one. Utilisation tells you how busy the resource is, saturation tells you how much work is waiting for it, and errors tell you whether it is failing.

Think of a checkout line. Utilisation is how many cashiers are busy, saturation is the length of the queue, and errors are the transactions that fail at the register. A line can have every cashier busy and no queue, which is healthy, or a long queue with busy cashiers, which means you need more registers. The three measures together tell you which case you are in, and one measure alone does not.

| Metric | What it measures |
|---|---|
| **Utilisation** | The fraction of the resource that is in use (e.g. GPU utilisation, memory utilisation) |
| **Saturation** | The degree to which the resource has more work queued than it can process (e.g. queue depth, NCCL pending collectives) |
| **Errors** | The rate of error events on the resource (e.g. ECC errors, GPU Xid events) |

USE fits AI workloads well. A training job emits GPU utilisation, GPU memory utilisation, the NCCL pending collective count, and the ECC error count. NCCL is the library that moves data between GPUs, and a pending collective is a step that is waiting for the other GPUs to join. Alerts sit on utilisation (too high means wasted; too low means under-provisioned) and on the errors.

When you read a GPU panel with USE in mind, you first ask whether the GPU is busy. Then you ask whether work is queuing behind it, such as pending collectives that wait for a slow peer. Last you check the error counters. A GPU that is busy with no queue and no errors is doing its job, even if the number looks lower than you hoped.

### 1.4 The golden signals

Picture a new service on its first day in production, with time to build only four charts. When you can only chart four things, the golden signals are a good place to start. They combine RED and USE into one short list, and they are the four that most teams pick.

The golden signals are not a replacement for RED and USE. They are a short starting set that keeps a new dashboard from growing into dozens of panels nobody reads. Once the first four charts are in place, add the detailed panels that your incidents show you are missing.

| Signal | Method | What it measures |
|---|---|---|
| Latency | RED | The duration of a successful request |
| Traffic | RED | The rate of requests |
| Errors | RED | The rate of failed requests |
| Saturation | USE | The degree to which the service is approaching its capacity |

An AI factory adds two AI-specific signals.

| Signal | Method | What it measures |
|---|---|---|
| GPU utilisation | USE | The fraction of GPU SMs in use |
| Model quality | (new) | The live accuracy of the model's predictions |

A model can be unhealthy while every operational metric stays green. The model quality signal catches a model that gives bad predictions even though the serving system works. Add it to the stack before you need it, not after the first bad release.

---

## 2. The cardinality budget

![Stacked boxes: method has 10 values, status has 10 values, and path has 100 values, which multiply to 10,000 series, with arrows pointing down.](./img/g-307.jpg)
*Figure 17.1.V. Every label multiplies the number of time series, so one unbounded label such as user_id can explode your metric count.*


### 2.1 What cardinality is

Imagine adding a `user_id` label to a request counter. The change is one line of code. In storage, it creates one time series for every user, and that count grows with your traffic.

Cardinality is the number of unique time series a metric produces. Take `http_requests_total` with three labels: `method` with 10 values, `status` with 10 values, and `path` with 100 values. The metric then produces 10 × 10 × 100 = 10,000 series. A label built from user IDs, request IDs, or timestamps can push the count into the millions. When you see a count like that, the label is the first suspect.

Every label multiplies the count by its own number of values.

A simple way to check a change is to multiply the number of values for each label in your head before you merge it. If the product is small, the change is probably safe. If the product runs into the millions, stop and ask whether the label belongs in a metric at all. That is why a metric can grow from a modest number of series to millions after one careless change, even though the code change looked tiny.

```text
Cardinality math (background reading: Production Kubernetes; the figures below are examples, not quotations):
- 1 metric x 3 labels x 10 values each = 10 * 10 * 10 = 1,000 series
- 1 metric x 5 labels x 100 values each = 100 * 100 * 100 * 100 * 100 = 10^10 series (impossible)
```

The platform team owns the cardinality budget. It decides which labels are safe to add. One label with 1,000 possible values turns one metric into up to 1,000 series. A label with 1000000 possible values turns it into up to 1000000 series, and you will feel that in memory.

### 2.2 Safe and unsafe labels

Picture a developer who asks to add the pod name as a label to every request metric so they can debug one replica. The request sounds reasonable, and that is exactly why you need a table to check it against. Use this table when a developer proposes a new label.

Keep the table next to the code review checklist, so the question gets asked in the same review every time. Ask how many values the label could take as the system grows, not how many you see today.

The value you see today is a poor guide, because labels tend to grow with the business. A label that holds one value per team looks harmless until the company hires many more teams. Ask what the label could look like in a year, and write that answer down with the change.

| Label | Cardinality | Safe? |
|---|---|---|
| `method` (GET, POST, PUT, DELETE) | 4 | Yes |
| `status` (200, 404, 500) | 3 | Yes |
| `region` (us-central1, europe-west1) | 10 | Yes |
| `team` (5 teams) | 5 | Yes |
| `model_name` (10 models) | 10 | Yes |
| `user_id` (millions of users) | millions | No |
| `request_id` (every request) | millions | No |
| `gpu_uuid` (8 GPUs per node × 1000 nodes) | 8000 | Yes (with care) |
| `pod_name` (every pod is unique) | 1000s | No |

A common rule of thumb says a label is safe if it has fewer than 1,000 possible values. The source notes describe that figure as an inference from common practice, so treat it as a starting point. A label above the line should be dropped at the source, moved into a log or trace, or aggregated before it reaches the metric.

Dropping the label at the source is the cleanest option, because the metric never sees it. Moving the value into a log or trace keeps the detail for debugging without paying for it in every series. Aggregating before it reaches the metric keeps the totals and removes the per-item detail, which is often what the dashboard needed anyway.

### 2.3 The consequences of getting cardinality wrong

Picture a Prometheus that uses more memory every week without anyone changing its settings. A bad cardinality budget shows up in three ways. The table below matches each symptom with its root cause and with what the on-call sees.

| Symptom | Root cause | Operational consequence |
|---|---|---|
| Prometheus uses too much memory | Too many time series | Prometheus OOM; metric ingestion stops |
| Grafana dashboards load slowly | Too many series per query | Dashboards take minutes to render; on-call loses situational awareness |
| The TSDB grows too fast | Too many series | Storage costs balloon, and the cluster's storage becomes the bottleneck |

The usual response is a hard limit on the series each metric may produce. Prometheus has a `--storage.tsdb.max-label-values-per-label-name` flag and a similar flag for series limits. Set the limit to fit the cluster's memory budget, and alert when you see a metric go over it.

Pick the limit by working backward from memory. Start with the memory your Prometheus server can use, estimate how much each series needs, and set the limit below that ceiling with room to spare. The alert should fire before the limit is hit, so the team has time to act. A limit that fires only after the server has crashed is not a limit at all.

---

## 3. The data shape

### 3.1 Metrics: Prometheus exposition format

Picture a GPU exporter writing its numbers in one shape while Prometheus expects another. Every exporter and every scraper has to agree on one format. The Prometheus exposition format is widely used for AI infrastructure metrics, and it is plain text. Each sample is one line that holds the metric name, its labels, and its value. An exporter is a small program that reads a system and publishes its numbers in that format.

```text
# HELP gpu_utilization_ratio The fraction of GPU SMs in use
# TYPE gpu_utilization_ratio gauge
gpu_utilization_ratio{gpu="0",node="gpu-node-1",model="churn-model"} 0.87
gpu_utilization_ratio{gpu="1",node="gpu-node-1",model="churn-model"} 0.92
gpu_utilization_ratio{gpu="2",node="gpu-node-2",model="churn-v3"} 0.65
```

Because the format is plain text, you can read an endpoint with curl and see the numbers directly.

This matters during an incident. When a dashboard looks wrong, you can open the raw endpoint, check the value yourself, and decide whether the exporter or the dashboard is at fault. That quick check often saves a long argument about which tool is lying. Prometheus pulls from each endpoint on a schedule, so the application never has to push data anywhere. Exporters such as DCGM, cAdvisor, and kube-state-metrics expose the numbers. Prometheus scrapes them, and Grafana draws the results. Scraping is the name for that pull, and it happens on a fixed interval.

### 3.2 Logs: structured JSON

Picture an engineer searching a month of text logs for every slow step of one model, and finding a line for each step with a different wording. A log line that says a step finished is easy to write and hard to query. A structured log carries the same event as named fields. That lets you filter by model, by run, or by severity without parsing free text.

```json
{
  "timestamp": "2024-03-15T10:30:00.000Z",
  "severity": "INFO",
  "message": "Training step 1000 completed",
  "run_id": "abc-123",
  "model": "churn-model",
  "step": 1000,
  "loss": 0.234,
  "throughput_tokens_per_sec": 45000,
  "gpu_utilization": 0.92
}
```

Loki (Chapter 17.3) indexes these logs by label, so you can ask questions across many records at once. For example, `sum by (model) (rate({model="churn-model", severity="ERROR"}[5m]))` shows the error rate per model. Agree on one schema across services first. Otherwise every team ends up writing its own parser, and the dashboards break every time a team renames a field.

A schema is a short written list of field names, types, and meanings that every service follows. When a new field appears, the schema changes first and the code follows. Without that discipline, a query that worked last week returns nothing because one team spelled the model field differently.

### 3.3 Traces: OpenTelemetry

Picture a chat reply that is slow, and nobody can say which service it passed through caused the delay. A trace follows one request through every service it touches. Each step in the trace is a span, with a name, a start time, an end time, a parent span, and attributes. The OpenTelemetry trace format is widely used for this, and the tree below shows what one request looks like.

```text
Trace abc-123
├─ Span inference-svc[churn-model]
│  ├─ Span http-handler
│  ├─ Span tokenize-prompt
│  ├─ Span feature-fetch[user_features]
│  ├─ Span vector-search[churn-v3]
│  └─ Span llm-inference[vllm]
│     ├─ Span prefill
│     └─ Span decode
└─ (response sent)
```

The tree shows where the time went. In the worked example, an 800 ms request splits into 200 ms of prefill, 500 ms of decode, and 100 ms of feature fetch. Prefill is the step that reads the whole prompt, and decode is the step that writes the answer one token at a time. Those three parts add up to the full 800 ms, so the on-call engineer knows which step to inspect first. The numbers are an illustration, not measurements.

### 3.4 Trace context propagation

Picture a request that leaves the handler, reaches the inference service, and then stops appearing in the trace. The usual cause is a hop that forgot to forward the ID. A trace stays whole only when every hop passes the trace ID along. The W3C Trace Context standard does this with the `traceparent` header. The header carries the trace ID and the parent span ID from the client to the server, then on to the database and the inference engine.

```python
# code/part17/snippets/trace_propagation.py
import requests
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("http-handler")
def handle_request(request):
    # Propagate the trace context to downstream services
    headers = {}
    TraceContextTextMapPropagator().inject(headers)
    response = requests.post(
        "http://llm-inference/v1/chat/completions",
        headers=headers,
        json=request.json(),
    )
    return response.json()
```

The snippet writes the header into the outgoing request, so the inference service can join the same trace. The inference service creates child spans, and the handler sends the finished trace to the collector. Your application still needs instrumentation. A service mesh does not remove that work, because the request headers must still pass from one service to the next. With the trace in place, the on-call engineer can follow one request from the HTTP handler to the LLM inference and to the GPU kernel.

Think of the trace ID as a ticket number that every hop writes on its paperwork. If one hop loses the ticket, the paperwork for the rest of the journey cannot be found. That is why the header must be copied on every outgoing call, even when the code path looks trivial.

---

## 4. Observability for AI workloads

### 4.1 What to observe at training time

Picture a training run that has been going for days, with the loss curve flat and nobody sure whether the job is still learning. A training run can last that long. Its health shows up in loss, throughput, and GPU use, not in request latency. The table lists the signals most teams watch during a run.

| Metric | What it measures | Why it matters |
|---|---|---|
| `training_loss` | The loss function value | The model is learning |
| `training_throughput_samples_per_sec` | The training throughput | The cluster is fully utilised |
| `gpu_utilization_ratio` | The GPU SM utilisation | The cluster is doing useful work |
| `gpu_memory_used_bytes` | The GPU memory used | The model fits in HBM |
| `data_loading_throughput` | The data loader throughput | The GPUs are not waiting on data |
| `gradient_norm` | The gradient norm | The model is not exploding |
| `checkpoint_save_duration_seconds` | The checkpoint save time | The job can resume from a checkpoint |
| `distributed_collective_latency_seconds` | The NCCL collective latency | The network is not the bottleneck |

Watch the data loader as closely as you watch the GPUs. A slow loader leaves the GPUs waiting, and you pay for hardware that does nothing.

A useful habit is to compare the loader panel and the GPU panel on the same time axis. When the GPU line dips at the same moment the loader line falls, the loader is the bottleneck. When the GPU line dips while the loader looks fine, look somewhere else, such as the collective operations between GPUs. *AI Systems Performance Engineering*, Chapter 16, names the DCGM field behind the SM utilisation row: `DCGM_FI_DEV_GPU_UTIL`. Use that field when you build the panel on the exporter side.

> **dcgm-exporter 4.9.0 version note.** dcgm-exporter 4.9.0 (2026-11-06) renamed many default metrics and changed some units. For example `DCGM_FI_DEV_GPU_UTIL` (percent) became `DCGM_FI_DEV_GPU_UTIL_RATIO` (0 to 1), and `DCGM_FI_DEV_FB_USED` (MiB) became `DCGM_FI_DEV_FB_USED_BYTES`. The metric names in this chapter are the 4.8.x names. On a 4.9.0 exporter use the [full mapping in 17.4](04-dcgm-exporter-and-interpreting-gpu-metrics.md#14-what-dcgm-exporter-490-renamed), and change thresholds together with the unit. If you copy a dashboard from this chapter onto a new exporter without checking the names, the panels will show no data and look broken.

The training script emits these metrics, either to a metrics endpoint or to a TensorBoard log that the platform scrapes. Many teams standardise on the OpenTelemetry Python SDK and send the metrics to a collector, which forwards them to Prometheus. Short jobs, such as an evaluation run, can finish before Prometheus scrapes them. For those, Prometheus offers a Pushgateway, which accepts metrics the job pushes before it exits.

### 4.2 What to observe at serving time

Picture a chat product where answers slow down, and customers notice within seconds. That is why you watch latency and errors first. The table lists the signals for the serving dashboard.

| Metric | What it measures | Why it matters |
|---|---|---|
| `inference_request_duration_seconds` (p50, p95, p99) | The inference latency | The SLO the customer sees |
| `inference_request_rate` | The inference throughput | The autoscaler reads this |
| `inference_request_errors_total` | The 5xx rate | The customer-facing error budget |
| `inference_kv_cache_utilization_ratio` | The KV cache utilisation | The model is not OOM |
| `inference_batch_size` | The continuous batch size | The inference engine is batching correctly |
| `inference_token_throughput` | The token throughput | The GPU is producing tokens |
| `model_quality_score` | The live model quality | The model is not regressing |

Track p95 and p99 latency, not only the median.

The reason is simple. A median describes the typical request, and the on-call needs to know about the unusual ones too. Tail latency is often where a timeout, a retry, or a cold cache shows up first, so it is the earliest warning you have. If you watch only the median, you will miss the slow requests. Even a 0.1 percent outlier shows up often in a large cluster, so the tail matters more than the average. Picture a chat product where a small group of requests takes far longer than the rest. The median looks fine, and that small group of customers sees the product as broken. *AI Systems Performance Engineering*, Chapter 16, makes this point with the same reasoning.

The serving metrics come from the inference engine, such as Triton, vLLM, or NIM. The platform team usually scrapes the engine's Prometheus endpoint. It then adds the model quality signal from Chapter 16.10.

### 4.3 What to observe at on-call time

At 3 a.m., an on-call engineer needs a few answers, not a chart of everything. The engineer is half awake, and every extra panel costs time. The table lists the signals that matter when a page arrives.

| Signal | Source | Why it matters |
|---|---|---|
| Cluster-wide p99 latency | Prometheus | The customer-facing SLO |
| GPU pool utilisation | DCGM | The capacity planning model |
| Failed training runs | MLflow | The team's ability to iterate |
| Failed promotions | MLflow Registry | The registry's reliability |
| Open incidents | PagerDuty | The team's operational state |
| Audit log writes | object storage | The regulator's question |

These signals belong on one dashboard, covered in Chapter 17.2. Make that dashboard the first page you open after a page. Keep it short enough to read in one screen.

---

## 5. Operating the observability stack on GKE

Picture Prometheus falling over at the start of a shift, and the team realising it cannot see anything. The observability stack is a production service too. If Prometheus or Loki fails, the team loses its view of everything else. Each component therefore needs its own latency target.

### 5.1 The components

Picture the first Monday after go-live, when the on-call opens a dashboard and it takes a minute to draw. That slow screen is an incident of its own. The table below lists each component, where it runs, what it stores, and the latency target the team agreed on.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Prometheus | Kubernetes Deployment | TSDB on persistent disk | Scrape latency p99 < 5 s |
| Grafana | Kubernetes Deployment | (uses Prometheus) | Dashboard load p99 < 5 s |
| Loki | Kubernetes Deployment | Object storage for log chunks | Query latency p99 < 5 s |
| OpenTelemetry Collector | Kubernetes Deployment | (forwards to backend) | Export latency p99 < 5 s |
| Alertmanager | Kubernetes Deployment | (sends to PagerDuty) | Alert latency p99 < 10 s |

The SLO values in this table are example targets. Pick your own from what the team can tolerate, and write them down before go-live.

*Production Kubernetes*, Chapter 9, makes the point that Prometheus is not designed for long-term storage of metrics. It can write to remote endpoints instead. Projects such as Thanos and Cortex offer stacks for that job. Decide how long production keeps data and how long nonproduction keeps it, then tell your tenants what to expect.

### 5.2 IAM and the cardinality budget

Imagine a data scientist who can change the settings of the metrics server. One mistake could blind the on-call team. Not everyone should get to change the metrics stack. Readers need read access. Exporters need write access. Admin rights stay with the platform team.

| Role | Who | What they can do |
|---|---|---|
| `observability.reader` | Every team's data scientists | Read Grafana dashboards; query Loki; query traces |
| `observability.writer` | The exporters (DCGM, kube-state-metrics) | Write metrics to Prometheus |
| `observability.admin` | The platform team | Manage the Prometheus server; set the cardinality budget; manage Grafana |

The cardinality budget is the platform team's discipline. Every new metric must declare its label cardinality. The team rejects metrics that exceed the budget and publishes the budget on the platform's status page.

In practice, the review looks like a short form attached to each merge request. The author lists each label and its expected number of values. The reviewer checks the product of those values against the budget. The form takes a few minutes to fill in, and it prevents the kind of surprise that otherwise shows up as a Prometheus restart in the middle of the night.

### 5.3 Observability

Picture a Prometheus that has stopped ingesting data while every other panel still looks normal. Nothing alarms, and the team learns about it from a customer. The stack needs its own alerts. Otherwise it can fail quietly while the rest of the cluster looks fine.

| Metric | Why it matters | Alert |
|---|---|---|
| Prometheus scrape latency p99 | Hot path for every metric | > 10 s |
| Grafana dashboard load latency p99 | On-call response time | > 10 s |
| Loki query latency p99 | Hot path for log queries | > 10 s |
| TSDB disk usage | Storage budget | > 80% for 1 hour |
| Cardinality per metric | Cardinality budget | > budget for 1 hour |

The thresholds in the Alert column are example values. Tune them to your team's tolerance and your hardware. The cardinality alert matters most. One metric over budget can exhaust Prometheus memory. Keep in mind that the stack's own alerts are the last line of defence, so review them after every incident, not only after the ones that involve the stack. A Prometheus out-of-memory failure is silent, because Prometheus stops ingesting metrics, the dashboards go stale, and nobody is told that they are stale.

---

## 6. How it fails

Picture a page that arrives with no obvious cause on the dashboard. Six failure modes recur. Each one below starts with the symptom you see first, then the likely cause, then the fix. Read them in that order, because the symptom is the only thing you can see at the start of a page.

### 6.1 "Prometheus OOM'd because of a high-cardinality label"

Prometheus crashes. The dashboards stop refreshing and the alerts stop firing. From the outside, the cluster can look healthy while it is on fire. That is the symptom to notice first.

The likely cause is that someone added a metric with a high-cardinality label, such as a request ID, a user ID, or a timestamp. The series count grew past what Prometheus can hold in memory.

The fix is to find the metric with `prometheus_tsdb_head_series`. Drop the label at the source, or aggregate the metric before it reaches Prometheus. Then set a hard limit on the series each metric may produce.

### 6.2 "The dashboards are stale"

The dashboard shows a healthy cluster. The on-call gets paged anyway, because the dashboard is out of date. The stale picture is what makes this failure hard to catch.

The likely cause is that Prometheus cannot scrape one or more targets, and the failure is silent. The dashboard keeps drawing old data while the cluster degrades.

The fix is to add an `up` metric alert for every Prometheus target. Choose how long a target may stay down before it pages, and alert when scrape latency grows too high. The source's example values are 5 minutes of downtime and 10 seconds of scrape latency.

A fixed threshold is the simplest alert, and it is easy to get wrong. *AI Factory*, Chapter 11, describes threshold alerts as either too nervous, firing more often than needed, or too relaxed, firing too rarely. Start with a few alerts, and improve each one as you learn how the system behaves.

### 6.3 "The logs are searchable but not queryable"

The on-call can find a specific log line but cannot answer "what was the error rate per model in the last 5 minutes". The search works, and the question still cannot be answered. That gap is the symptom.

The likely cause is that the logs are plain text. The fields the team wants to query sit inside the message, so Loki cannot index them as labels.

The fix is to move to structured JSON logs with a declared schema. Use the OpenTelemetry log SDK and emit the labels as separate fields.

### 6.4 "The traces are incomplete"

The on-call sees a trace that stops at the LLM inference. The inference service's child spans are missing, so the trace looks finished when it is not.

The likely cause is that the trace context does not reach the inference service. The service starts a new trace instead of adding child spans to the existing one.

The fix is to confirm that the W3C Trace Context header leaves every outgoing request from the handler. Confirm that the inference service reads the header and creates child spans. Add an integration test that checks the trace from end to end.

### 6.5 "The model quality signal is missing"

The model gives bad predictions, but the operational metrics are green. Nobody knows. This failure hides well, because every dashboard that the team checks looks healthy.

The likely cause is that the live accuracy signal from Chapter 16.10 is not connected to the observability stack. The model can degrade without anyone seeing it.

The fix is to send the live accuracy signal to Prometheus. Alert when it drops below a threshold your team chooses. Also alert when the signal goes missing for a period your team sets, because silence is also a failure.

### 6.6 "The observability stack is the bottleneck"

Dashboards take 30 seconds to load. Alert evaluation takes minutes, and queries take a minute. The stack is still running, but every question you ask it takes too long to answer during an incident.

The likely cause is that the stack is under-resourced. Prometheus needs more memory, Loki needs more storage, and a slow stack slows down every debugging session.

The fix is to right-size the stack. Give it a dedicated node pool. For high-cardinality workloads, consider Prometheus sharding, which splits the series across several Prometheus servers.

---

## 7. Hands-on lab

Suppose you have a GKE cluster and no observability yet. This lab installs Prometheus, Grafana, Loki, and the OpenTelemetry Collector on GKE. Then it checks the three pillars from end to end. The lab is untested in this repository, so treat the commands as a starting point. These steps were not run on a live cluster, so expect to fix a few details.

### 7.1 Prerequisites

Picture a fresh GKE project where nothing has been installed yet. Before you start, check these three items.

- A GKE Autopilot or Standard cluster. Check the minimum version that each chart requires.
- Helm 3 for installing the observability stack.
- A workload that emits metrics, logs, and traces, such as an InferenceService from Chapter 16.7.

### 7.2 Step 1: install Prometheus and Grafana

Picture a new cluster where the first question is whether any metrics tool is running at all. Start with the kube-prometheus-stack chart. It brings Prometheus and Grafana, and the retention flag keeps metrics for 30 days.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set grafana.adminPassword=admin
# expected: Prometheus and Grafana pods are running; Grafana is exposed via Ingress
```

### 7.3 Step 2: install Loki

Picture a pod that crashed an hour ago, where you need its logs without logging into the node. Install Loki with the loki-stack chart. The retention flag sets how long log data is kept. Logs go in first, because the next steps need somewhere to send them.

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set loki.limits_config.retention_period=30d
# expected: Loki pods are running; Loki is exposed via Grafana
```

### 7.4 Step 3: install the OpenTelemetry Collector

Picture a busy node with many workloads on it, each one needing a route to the backend. Run the collector as a DaemonSet, so one collector sits on each node. It forwards data to the backend address you set.

```bash
helm install otel-collector open-telemetry/opentelemetry-collector \
  --namespace monitoring \
  --set mode=daemonset \
  --set configmap.config.exporters.otlp.endpoint=backend.example.com:4317
# expected: the OpenTelemetry Collector pods are running as a DaemonSet
```

### 7.5 Step 4: configure a workload to emit the three pillars

Picture a new workload that has no idea where its telemetry should go. Point the workload at the collector and give it a service name. The environment variables tell the application where to send its data. If the endpoint is wrong, the workload still runs, but its data goes nowhere.

```yaml
# code/part17/observability_workload.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: observability-demo
spec:
  selector:
    matchLabels:
      app: observability-demo
  template:
    metadata:
      labels:
        app: observability-demo
    spec:
      containers:
        - name: app
          image: my-app:v1
          env:
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: http://otel-collector.monitoring:4317
            - name: OTEL_SERVICE_NAME
              value: observability-demo
            - name: METRICS_PORT
              value: "9090"
          ports:
            - containerPort: 8080
            - containerPort: 9090
```

### 7.6 Step 5: query the three pillars

Picture a fresh install that looks ready on the surface. Query each pillar once from the command line. Together, the three commands confirm that metrics, logs, and traces all arrive. If one command returns nothing, you know which pillar to check first.

```bash
# Metrics
curl http://prometheus.monitoring:9090/api/v1/query?query=up | jq .

# Logs
curl -G http://loki.monitoring:3100/loki/api/v1/query \
  --data-urlencode 'query={job="observability-demo"}' | jq .

# Traces
curl http://otel-collector.monitoring:4318/v1/traces | jq .
```

### 7.7 Step 6: build a unified dashboard

Picture the moment you see a spike and need the matching log line and trace. The dashboard puts request rate, p99 latency, error logs, and traces on one page. That lets you move from a spike in a graph to the matching log line and trace. Build it last, because it only works when the three pillars already carry data.

```yaml
# code/part17/grafana_dashboard.json
{
  "dashboard": {
    "title": "Grafana dashboard",
    "panels": [
      {"title": "Inference request rate", "type": "timeseries", "targets": [{"expr": "rate(inference_request_total[5m])"}]},
      {"title": "Inference latency p99", "type": "timeseries", "targets": [{"expr": "histogram_quantile(0.99, rate(inference_request_duration_seconds_bucket[5m]))"}]},
      {"title": "Error logs", "type": "logs", "targets": [{"expr": "{severity=\"ERROR\"}"}]},
      {"title": "Trace latency", "type": "traces", "targets": [{"query": "inference-svc"}]}
    ]
  }
}
```

### 7.8 What to record

Picture the lab finished and the stack running. After the lab, answer five questions. Each answer should take seconds to find. The 5-second and 30-second figures below are example targets that your team should set for itself.

1. What is the current Prometheus scrape latency p99?
2. What is the current cardinality per metric?
3. What is the current Loki query latency p99?
4. What is the most recent error log?
5. What is the current p99 trace latency?

If an answer takes more than 30 seconds to find, the stack is not yet ready to run as a production service. Write down the slow answers, because they tell you which part of the stack to tune first.

## Exercises

Picture the stack you just built, still running, as the place where each exercise happens. Work through these in order. Each one checks a single idea from the chapter.

1. Add a metric with a label that has 10000 unique values. Watch how Prometheus behaves, then remove the label. Watch how Prometheus behaves, then remove the label.

Keep the notes from that run, because they show the memory cost you avoided. *Solution sketch:* an exporter that emits `http_requests_total{user_id=...}`; watch the `prometheus_tsdb_head_series` metric.
2. Define a JSON schema for your logs. Emit it from the application, then query Loki by the schema fields. *Solution sketch:* a Pydantic model in Python that emits structured JSON; Loki's label extraction from JSON.
3. Verify that the trace context moves from the HTTP handler into the LLM inference. *Solution sketch:* a Python test that asserts the trace ID in the HTTP handler matches the trace ID in the LLM inference.
4. Send the live accuracy signal from Chapter 16.10 to Prometheus. Then alert when the signal drops. *Solution sketch:* a sidecar that emits the live accuracy metric, and a Prometheus alert on that metric.
5. Configure an alert that fires when a metric's cardinality passes a limit you choose. The chapter's 1,000-value rule of thumb from Section 2.2 is a reasonable starting point. *Solution sketch:* a recording rule that computes `count by (__name__) (up{job=~".+"})`, with an alert on the recording rule.
6. Build a dashboard that shows the metrics, logs, and traces for a single request. *Solution sketch:* a Grafana dashboard with the panels from Section 7.7, where the data source links metrics to logs and traces.

## Checkpoint questions

<details><summary>1. Prometheus crashes, the dashboards stop refreshing and the alerts stop firing, yet the cluster looks healthy from outside. What is the likely cause and how do you find it?</summary>
Someone added a metric with a high-cardinality label, such as a request ID, a user ID or a timestamp. The series count grew past what Prometheus can hold in memory. Find the metric with `prometheus_tsdb_head_series`, drop the label at the source or aggregate before Prometheus, and set a hard limit on series per metric.
</details>

<details><summary>2. The dashboard shows a healthy cluster but the on-call gets paged anyway. What went wrong and what alert would have caught it?</summary>
Prometheus cannot scrape one or more targets, and the failure is silent, so the dashboard keeps drawing old data. Add an `up` metric alert for every Prometheus target, and alert when scrape latency grows too high. The source's example values are 5 minutes of downtime and 10 seconds of scrape latency.
</details>

<details><summary>3. On-call can find one log line but cannot answer "what was the error rate per model in the last 5 minutes". What is wrong with the logs?</summary>
The logs are plain text, so the fields the team wants to query sit inside the message and Loki cannot index them as labels. Move to structured JSON logs with a declared schema, and emit the labels as separate fields. Then a query such as `sum by (model) (rate(...[5m]))` works.
</details>

<details><summary>4. A trace stops at the LLM inference span and the inference service's child spans are missing. What do you conclude and what do you check?</summary>
The trace context does not reach the inference service, so it starts a new trace instead of adding child spans to the existing one. Confirm that the W3C Trace Context header leaves every outgoing request from the handler. Confirm that the inference service reads the header, and add an end-to-end integration test.
</details>

<details><summary>5. Customers complain about bad predictions while every operational metric is green. Which signal is missing?</summary>
The model quality signal is not connected to the observability stack, so the model can degrade unseen. Send the live accuracy signal to Prometheus. Alert when it drops below a threshold your team chooses, and also when the signal goes missing for a period your team sets.
</details>

<details><summary>6. Dashboards take 30 seconds to load, alert evaluation takes minutes and queries take a minute. What is the diagnosis and the fix?</summary>
The observability stack is under-resourced, so it slows every debugging session. Right-size it and give it a dedicated node pool. For high-cardinality workloads, consider Prometheus sharding.
</details>

<details><summary>7. Why does adding one label to a counter multiply storage instead of adding to it?</summary>
Cardinality is the number of unique time series a metric produces. Each label multiplies the possible combinations with the values of the other labels. So a label with a million possible values can turn one metric into up to a million series, and you feel that in memory.
</details>

<details><summary>8. Why do metrics, logs and traces need to be used together during an incident, and in what order?</summary>
Each answers a different question. Metrics show that something is wrong, logs show what the system was doing at that moment, and traces show where the time went inside one request. Start with metrics to find the symptom, then open the logs and traces for the same time window.
</details>

<details><summary>9. Why does the chapter say to watch p95 and p99 latency and not only the median?</summary>
A median hides the slow requests. Even a 0.1 percent outlier shows up often in a large cluster, so the tail matters more than the average. The chapter cites AI Systems Performance Engineering Chapter 16 for the same reasoning.
</details>

<details><summary>10. Why does a slow data loader show up as a GPU problem in the dashboards, and which metric tells you the loader is the cause?</summary>
A slow loader leaves the GPUs waiting, so GPU utilisation drops while you still pay for the hardware. The `data_loading_throughput` metric shows whether the loader is feeding the GPUs. That is why the chapter says to watch the loader as closely as the GPUs.
</details>

<details><summary>11. When would you choose RED metrics over USE metrics, and what does each give up?</summary>
RED fits request-driven services such as an InferenceService, where you track rate, errors and duration. USE fits resources such as a GPU, a memory pool or a network link, where you track utilisation, saturation and errors. RED says nothing about whether a GPU is saturated, and USE says nothing about request latency, so an AI platform needs both.
</details>

<details><summary>12. A developer wants a `gpu_uuid` label across 1000 nodes with 8 GPUs each. How do you decide whether to allow it?</summary>
Ask how many values the label could take as the system grows. The table marks `gpu_uuid` as safe only with care, and the 1,000-value rule of thumb is an inference from common practice. Compare the count with your series budget, and alert when a metric goes over it.
</details>

<details><summary>13. Short evaluation jobs finish before Prometheus scrapes them. What do you use, and what is the trade-off of Prometheus pulling by default?</summary>
Use the Pushgateway, which accepts metrics a job pushes before it exits. By default Prometheus pulls from each endpoint on a schedule, so the application never has to push data anywhere. That pull model is simple, but a job shorter than the scrape interval can vanish unseen.
</details>

<details><summary>14. A team adds a service mesh, and the trace still breaks at the first hop between the HTTP handler and the inference service. Can the team stop adding instrumentation to the application now, and what must each hop pass along?</summary>
No. The chapter says a service mesh does not remove the instrumentation work, because the request headers must still pass from one service to the next. The application has to inject and read the `traceparent` header on every hop. Without that header, the trace breaks at the first hop that drops it.
</details>

<details><summary>15. `http_requests_total` has three labels: `method` with 10 values, `status` with 10 values and `path` with 100 values. How many series can it produce?</summary>
Multiply the values of the three labels. That is 10 times 10 times 100, which is 10,000 series. A label built from user IDs or request IDs could push it into the millions.
</details>

<details><summary>16. An 800 ms request has 200 ms of prefill and 500 ms of decode. How much time is left for the other step in the worked example, and where do you look first?</summary>
The rest is 800 minus 200 minus 500, which is 100 ms for feature fetch. Decode is the largest part at 500 ms, so that is where to look first. The numbers are an illustration, not measurements.
</details>

<details><summary>17. A metric already has 10,000 series. A developer adds a `model_name` label with 10 values. What is the worst-case series count, and does it fit a budget of 200,000?</summary>
The count multiplies, so 10,000 times 10 is 100,000 series. That is under 200,000, which is the top of the example range for a mature cluster. But all other metrics share that budget, so check the total before approving.
</details>

<details><summary>18. The TSDB disk usage alert is set at more than 80 percent for 1 hour. How much of a 1 TB disk is left when the alert fires, and what else do you check?</summary>
At 80 percent used, 20 percent is left, which is 200 GB of 1 TB. Then check cardinality per metric, because too many series makes the TSDB grow fast. The thresholds in the chapter are example values.
</details>

<details><summary>19. You get paged for a slow endpoint. In what order do you look at the three pillars, and why?</summary>
First metrics, to find the symptom such as p99 latency or error rate. Second logs for the same time window, to see what the system was doing. Third traces, to see where the time went inside one slow request.
</details>

<details><summary>20. Dashboards are stale and you suspect Prometheus OOM. What do you check first, second and third?</summary>
First check whether Prometheus is running and ingesting, because an out-of-memory failure is silent and the dashboards simply go stale. Second query `prometheus_tsdb_head_series` to find the metric with too many series. Third find the label responsible and drop it at the source or aggregate it.
</details>

---

## Sources and review notes

- *Production Kubernetes* (`production-kubernetes`, Chapter 9). Source for the RED method, the observability stack patterns, the cardinality budget, and the operational discipline. Chapter 9 is approximately 9,200 words.
- *Engineering AI Systems: Architecture and DevOps Essentials* (`engineering-ai-systems-architecture-and-devops-essentials`, Chapter 11). Source for the three pillars of observability (metrics, logs, traces), the AI-specific signals, and the integration with the MLOps lifecycle. Chapter 11 is approximately 2,800 words.
- NVIDIA Zero-to-Hero Volume 16 (`chapter-01-observability-foundations.md`, `chapter-02-metrics-logs-and-traces.md`). Source for the operational observability patterns, the cardinality discipline, and the data shape decisions. The wording has been rewritten in the handbook's voice.
- NVIDIA Zero-to-Hero Volume 7 (`chapter-01-observability-stack-overview.md`). Source for the observability stack patterns (Prometheus + Grafana + Loki + OpenTelemetry), the deployment on Kubernetes, and the operational metrics.

### Cross-references to other handbook chapters

- Chapter 1.23 (Performance methodology) for the USE method.
- Chapter 16.10 (Monitoring and drift) for the AI-specific monitoring pattern.
- Chapter 16.14 (Platform design) for the SLO-based platform design.
- Chapter 17.2 (Prometheus and Grafana) for the metrics stack in detail.

### Migrated from `nvidia-devops`

The three pillars framework, the cardinality discipline, and the operational observability patterns draw on Volume 16 chapters 1-2 and Volume 7 chapter 1. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The cardinality budget's rule of thumb (1000 unique values per label) is a starting point drawn from common practice; specific budgets depend on the metric and the cluster's memory.
- The model quality signal as an AI-specific golden signal is an inference from the operational patterns of mature AI factories; specific signals depend on the use case.
- The structured JSON log format as the standard is an inference from the OpenTelemetry and Loki conventions; specific teams may use other structured formats.

### Not verified on live hardware

- The lab in Section 7 is **untested** against a live GKE cluster in this repository.
- The Prometheus, Grafana, Loki, and OpenTelemetry Collector versions assumed in the lab should be pinned against the current releases before production use.
- The cardinality numbers in the lab are illustrative; production cardinality depends on the workload.

