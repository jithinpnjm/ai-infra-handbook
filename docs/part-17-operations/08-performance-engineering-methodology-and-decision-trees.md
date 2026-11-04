---
id: "c17-08"
title: "17.8 Performance engineering methodology and decision trees"
sidebar_label: "17.8 Performance engineering methodology"
sidebar_position: 8
description: "Performance engineering methodology for AI infrastructure: the USE method, the roofline model, the performance decision tree, the capacity planning model, the cost-vs-latency trade-off, and the operational patterns that turn ad-hoc optimisation into a repeatable discipline."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 17.8 Performance engineering methodology and decision trees

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Primary sources | *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chapters 1, 8); *Engineering AI Systems* (`engineering-ai-systems-architecture-and-devops-essentials`, Chapter 8); *Systems Performance* (`systems-performance-2nd-edition`, Chapters 1, 2) |
| Cross-references | Chapter 1.23 (Performance methodology); Chapter 1.25 (Benchmarking correctly); Chapter 10.5 (The roofline model); Chapter 17.5 (Distributed observability and profiling); Chapter 17.7 (Failure modes) |
| Coverage file | `planning/coverage/chapters/17-08.md` |
| Claim & number ledger | `planning/ledgers/17-08.md` |

## Why this matters for AI infrastructure

Every chapter in this part has been about observing failures and acting on them. This chapter is about preventing the failures in the first place. Performance engineering is the discipline that turns an AI workload from "fast enough" to "fast as it can be". Without the discipline, the team optimises ad-hoc; with the discipline, the team optimises systematically.

An AI factory without performance engineering is an AI factory that pays for more GPUs than it needs. An AI factory with performance engineering is an AI factory that runs the same workload on fewer GPUs, with lower latency, and at lower cost. The difference is millions of dollars per year.

```text
Why performance engineering is on the critical path (ASP Ch 1, 8; EAS Ch 8):
- A typical mature AI platform spends 60-80% of its time in GPU kernels. A 10%
  kernel optimisation is the difference between 100 GPUs and 90 GPUs for the
  same workload. The savings are millions of dollars per year.
- The performance engineering methodology is what turns ad-hoc optimisation
  into a repeatable discipline. The methodology is the USE method; the
  methodology is the roofline model; the methodology is the performance
  decision tree.
- The cost-vs-latency trade-off is the most important performance decision.
  The trade-off is: how much latency can the team afford to save by adding
  GPUs? The trade-off is: how much GPU spend can the team afford to save by
  adding latency? The methodology is what makes the trade-off explicit.
```

Three operational realities make this chapter a platform-team concern rather than a data-science-only concern:

1. **The performance methodology is a platform-team discipline.** The team that follows the methodology saves GPUs; the team that does not wastes GPUs. The platform team's job is to make the methodology repeatable.
2. **The decision tree is a platform-team deliverable.** The decision tree tells the on-call where to look when the workload is slow. The decision tree is the difference between ad-hoc debugging and systematic debugging.
3. **The cost-vs-latency trade-off is a platform-team decision.** The platform team owns the GPU pool; the platform team owns the SLOs; the platform team owns the trade-off. The data scientist consumes the trade-off; the platform team makes the trade-off.

**Before a team can optimise an AI workload, the team must follow a methodology. Optimisation without a methodology is ad-hoc; optimisation with a methodology is systematic. The methodology is the USE method; the methodology is the roofline model; the methodology is the decision tree.**

## Prerequisites and outcomes

### Prerequisites

- Chapter 1.23 (Performance methodology) for the USE method and the roofline model.
- Chapter 1.25 (Benchmarking correctly) for the benchmarking methodology.
- Chapter 10.5 (The roofline model) for the roofline model details.
- Chapter 17.5 (Distributed observability and profiling) for the profiling tools.

### Outcomes

After completing this chapter you will be able to:

1. Apply the USE method to identify the bottleneck: utilisation, saturation, or errors.
2. Use the roofline model to predict the achievable performance for a given workload.
3. Follow the performance decision tree to find the bottleneck in seconds.
4. Build the cost-vs-latency trade-off model: the team's explicit choice between GPUs and seconds.
5. Operate the capacity planning model: how many GPUs the team needs for the next quarter.
6. Operate the performance engineering stack on GKE with repeatable methodology, decision trees, and capacity planning.

---

## 1. The USE method

### 1.1 The USE method in detail

*Systems Performance* Chapter 1 introduces the USE method. The USE method is the simplest methodology for performance engineering. The method says: for every resource, check utilisation, saturation, and errors.

| Resource | Utilisation | Saturation | Errors |
|---|---|---|---|
| **GPU** | SM utilisation, memory utilisation | Queue depth, pending collectives | ECC errors, Xid errors |
| **CPU** | Utilisation per core | Run queue length, load average | Context switch rate, page faults |
| **Memory** | Used vs total | Page-in rate, swap activity | OOM kills, allocation failures |
| **Disk I/O** | IOPS utilisation, bandwidth | Queue depth, await time | I/O errors, SMART warnings |
| **Network** | Bandwidth utilisation | Queue depth, dropped packets | CRC errors, link flaps |
| **Storage** | Object store request rate | 5xx rate, latency p99 | Object lock failures, 4xx rate |

The pattern is: for every resource, the on-call checks the three metrics. The bottleneck is the resource that is most utilised, most saturated, or most error-prone. The on-call fixes the bottleneck; the workload improves.

### 1.2 The USE method in action

Suppose the on-call is paged for "the workload is slow". The on-call applies the USE method.

```text
USE method application:
- GPU: SM utilisation 95%, memory utilisation 60%, queue depth 0, ECC errors 0
  - Utilisation is high; saturation is low; errors are zero
  - The GPU is doing useful work; the GPU is not the bottleneck
- CPU: utilisation 30%, run queue 0, context switches 100/s
  - Utilisation is low; saturation is low; errors are zero
  - The CPU is not the bottleneck
- Memory: used 60%, page-in rate 0, OOM kills 0
  - Utilisation is moderate; saturation is low; errors are zero
  - The memory is not the bottleneck
- Disk I/O: IOPS utilisation 80%, bandwidth 60%, queue depth 50, I/O errors 0
  - Utilisation is moderate; saturation is high; errors are zero
  - The disk is saturated; the disk is the bottleneck
- Network: bandwidth 30%, queue depth 0, errors 0
  - The network is not the bottleneck
- Storage: object store 5xx 0, latency p99 200ms
  - The storage is not the bottleneck
```

The bottleneck is the disk; the disk queue depth is 50 (the disk is processing 50 requests at the same time); the fix is to use a faster disk or to batch the reads. The USE method gave the answer in seconds.

### 1.3 The USE method as a Grafana dashboard

The USE method as a Grafana dashboard is the on-call engineer's home page.

```yaml
# code/part17/use_method_dashboard.json (shape only)
{
  "dashboard": {
    "title": "AI Factory - USE Method",
    "panels": [
      {"title": "GPU utilisation", "type": "timeseries", "targets": [{"expr": "DCGM_FI_DEV_GPU_UTIL"}]},
      {"title": "GPU saturation (queue depth)", "type": "stat", "targets": [{"expr": "kube_pod_status_phase{phase=\"Pending\"}"}]},
      {"title": "GPU errors (ECC)", "type": "stat", "targets": [{"expr": "DCGM_FI_DEV_ECC_DBE_VOL_DEDUP"}]},
      {"title": "CPU utilisation", "type": "timeseries", "targets": [{"expr": "100 - rate(node_cpu_seconds_total{mode=\"idle\"}[5m]) * 100"}]},
      {"title": "Memory utilisation", "type": "timeseries", "targets": [{"expr": "node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes"}]},
      {"title": "Disk I/O utilisation", "type": "timeseries", "targets": [{"expr": "rate(node_disk_io_time_seconds_total[5m])"}]},
      {"title": "Network utilisation", "type": "timeseries", "targets": [{"expr": "rate(node_network_transmit_bytes_total[5m])"}]},
      {"title": "Storage latency p99", "type": "stat", "targets": [{"expr": "s3_request_duration_seconds{quantile=\"0.99\"}"}]}
    ]
  }
}
```

The pattern is: every resource has three panels (utilisation, saturation, errors); the dashboard is the on-call's situational awareness; the dashboard is the USE method as a service.

---

## 2. The roofline model

### 2.1 The roofline model in detail

*AI Systems Performance Engineering* Chapter 8 introduces the roofline model. The roofline model says: the achievable performance is bounded by the hardware peak (compute or bandwidth) and the workload's arithmetic intensity (operations per byte).

```text
Roofline model:
- For a kernel with arithmetic intensity I (FLOP/byte):
  - If I < I_ridge (memory-bound): performance = bandwidth * I
  - If I > I_ridge (compute-bound): performance = compute peak
- I_ridge = compute peak / bandwidth

H100 roofline (FP16):
- Compute peak: 989 TFLOPS
- Bandwidth: 3,350 GB/s
- I_ridge: 295 FLOP/byte
```

The pattern is: for each kernel, the on-call computes the arithmetic intensity; the on-call compares the intensity to the ridge point; the kernel is either memory-bound or compute-bound. The optimisation depends on the bound.

### 2.2 The roofline model in action

Suppose the on-call is profiling a transformer attention kernel. The on-call computes the arithmetic intensity.

```text
Attention kernel arithmetic intensity:
- FLOPs: 4 * batch * seq_len * seq_len * hidden_size
  - Example: 4 * 1 * 2048 * 2048 * 4096 = 6.87e10 FLOPs
- Bytes: batch * seq_len * hidden_size * 4 (FP16 weights + activations)
  - Example: 1 * 2048 * 4096 * 4 = 3.36e7 bytes
- Arithmetic intensity: 6.87e10 / 3.36e7 = 2045 FLOP/byte

Comparison to H100 ridge point (295 FLOP/byte):
- Attention intensity (2045) > ridge point (295)
- The kernel is compute-bound
- The optimisation is to increase the compute peak (use FP8; use Tensor Cores)
```

The roofline model gave the answer in seconds. The attention kernel is compute-bound; the optimisation is to use FP8 (which doubles the compute peak) or to use Tensor Cores more aggressively.

### 2.3 The roofline model as a profiling tool

The roofline model is the on-call's tool for predicting kernel performance. The on-call computes the roofline for every kernel; the on-call compares the kernel's actual performance to the roofline; the gap between the actual performance and the roofline is the optimisation opportunity.

```text
Roofline analysis:
- Kernel: matmul
- Actual performance: 800 TFLOPS
- Roofline (compute peak): 989 TFLOPS
- Gap: 989 - 800 = 189 TFLOPS (19% of peak)
- Optimisation opportunity: close the 19% gap; use Tensor Cores more aggressively

Roofline analysis:
- Kernel: embedding lookup
- Actual performance: 1500 GB/s
- Roofline (bandwidth): 3,350 GB/s
- Gap: 3,350 - 1,500 = 1,850 GB/s (55% of peak)
- Optimisation opportunity: close the 55% gap; use vector loads; reduce memory accesses
```

The pattern is: the roofline model tells the on-call where the optimisation opportunity is; the on-call closes the gap; the workload improves.

---

## 3. The performance decision tree

### 3.1 The decision tree structure

The performance decision tree is the on-call's guide for finding the bottleneck. The decision tree has branches that lead to the bottleneck.

```mermaid
flowchart TD
    A[Workload is slow] --> B{GPU utilisation > 90%?}
    B -- yes --> C{Memory utilisation > 90%?}
    B -- no --> D{CPU utilisation > 90%?}
    C -- yes --> E{Memory bound or compute bound?}
    C -- no --> F[Kernel optimisation<br/>Tensor Cores, FP8]
    E -- memory bound --> G[Memory access pattern<br/>coalescing, vectorisation]
    E -- compute bound --> H[Use Tensor Cores<br/>reduce precision]
    D -- yes --> I{CPU bound?}
    D -- no --> J{Network bound?}
    I -- yes --> K[CPU optimisation<br/>vectorisation, batching]
    I -- no --> L[Profile CPU<br/>find hot function]
    J -- yes --> M{Network congestion or failure?}
    J -- no --> N[Storage bound?]
    M -- congestion --> O[QoS, traffic shaping]
    M -- failure --> P[Investigate network]
    N -- yes --> Q[Storage optimisation<br/>batching, caching]
    N -- no --> R[Profile kernel<br/>find bottleneck]
```

The pattern is: the decision tree has branches that lead to the bottleneck. The on-call follows the tree; the on-call finds the bottleneck in seconds; the on-call fixes the bottleneck.

### 3.2 The decision tree in action

Suppose the on-call is paged for "the training is slow". The on-call follows the decision tree.

```text
Decision tree application:
- Step 1: GPU utilisation > 90%? Yes -> continue to step 2; No -> go to step 5
- Step 2: Memory utilisation > 90%? No -> kernel optimisation (Tensor Cores, FP8)
- Step 5: CPU utilisation > 90%? No -> continue to step 8
- Step 8: Network bound? Yes -> check for congestion
- Step 9: Network congestion? Yes -> apply QoS
- Step 10: Network QoS applied -> training is faster
```

The decision tree gave the answer in seconds. The bottleneck was the network; the fix was QoS; the workload improved.

### 3.3 The decision tree as a Grafana dashboard

The decision tree as a Grafana dashboard is the on-call's guide for finding the bottleneck.

```yaml
# code/part17/decision_tree_dashboard.json (shape only)
{
  "dashboard": {
    "title": "AI Factory - Performance Decision Tree",
    "panels": [
      {"title": "Step 1: GPU utilisation > 90%?", "type": "stat", "targets": [{"expr": "DCGM_FI_DEV_GPU_UTIL > 90"}]},
      {"title": "Step 2: Memory utilisation > 90%?", "type": "stat", "targets": [{"expr": "DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL > 0.9"}]},
      {"title": "Step 5: CPU utilisation > 90%?", "type": "stat", "targets": [{"expr": "100 - rate(node_cpu_seconds_total{mode=\"idle\"}[5m]) * 100 > 90"}]},
      {"title": "Step 8: Network bound?", "type": "stat", "targets": [{"expr": "rate(node_network_transmit_bytes_total[5m]) > 1e9"}]},
      {"title": "Recommended fix", "type": "text", "options": {"content": "Based on the panels above, the recommended fix is..."}}
    ]
  }
}
```

The pattern is: the dashboard shows the decision tree's panels; the on-call reads the panels; the dashboard recommends the fix. The decision tree is the on-call's guide.

---

## 4. The cost-vs-latency trade-off

### 4.1 The trade-off model

The cost-vs-latency trade-off is the most important performance decision. The trade-off is: how much latency can the team afford to save by adding GPUs? The trade-off is: how much GPU spend can the team afford to save by adding latency?

```text
Cost-vs-latency trade-off:
- Current: 8 H100 GPUs, p99 latency 500 ms, cost $32/hour
- Option A: 16 H100 GPUs (2x), p99 latency 250 ms (2x faster), cost $64/hour
  - Saves 250 ms; costs $32/hour extra
- Option B: Optimise the kernel, p99 latency 350 ms, cost $32/hour
  - Saves 150 ms; costs $0 extra
- Option C: Reduce the model size, p99 latency 400 ms, cost $32/hour
  - Saves 100 ms; costs $0 extra
- Recommendation: Option B (best ROI)
```

The pattern is: the trade-off makes the choice explicit. The team sees the options; the team sees the costs; the team sees the savings; the team picks the best option.

### 4.2 The trade-off as a Grafana dashboard

The trade-off as a Grafana dashboard is the team's view of the cost-vs-latency trade-off.

```yaml
# code/part17/cost_latency_dashboard.json (shape only)
{
  "dashboard": {
    "title": "AI Factory - Cost vs Latency",
    "panels": [
      {"title": "Current p99 latency", "type": "stat", "targets": [{"expr": "histogram_quantile(0.99, rate(inference_request_duration_seconds_bucket[5m]))"}]},
      {"title": "Current GPU cost per hour", "type": "stat", "targets": [{"expr": "sum(rate(kubecost_gpu_cost[1h]))"}]},
      {"title": "Latency saved per GPU added", "type": "table", "targets": [{"expr": "..."}]},
      {"title": "ROI per optimisation", "type": "table", "targets": [{"expr": "..."}]}
    ]
  }
}
```

The pattern is: the dashboard shows the current state; the dashboard shows the trade-off; the team picks the best option.

---

## 5. Capacity planning

### 5.1 The capacity planning model

Capacity planning is the discipline that turns the current usage into the future GPU order. The model is: forecast the next quarter's usage; add a buffer for spikes; order the GPUs.

```text
Capacity planning model:
- Current usage: 100 H100 GPUs at 80% utilisation
- Forecast growth: 20% per quarter
- Buffer: 30% for spikes
- Q+1 forecast: 100 * 1.20 * 1.30 = 156 GPUs
- Q+1 order: 156 GPUs (rounded up)
```

The pattern is: forecast the growth; add the buffer; order the GPUs. The capacity planning model is what turns the cost dashboard into the procurement order.

### 5.2 The capacity planning dashboard

The capacity planning dashboard is the platform team's view of the future GPU order.

```yaml
# code/part17/capacity_dashboard.json (shape only)
{
  "dashboard": {
    "title": "AI Factory - Capacity Planning",
    "panels": [
      {"title": "Current GPU pool utilisation", "type": "stat", "targets": [{"expr": "avg(DCGM_FI_DEV_GPU_UTIL)"}]},
      {"title": "Current GPU count", "type": "stat", "targets": [{"expr": "count(DCGM_FI_DEV_GPU_UTIL)"}]},
      {"title": "Forecast growth rate", "type": "stat", "targets": [{"expr": "(count(DCGM_FI_DEV_GPU_UTIL) - count(DCGM_FI_DEV_GPU_UTIL offset 30d)) / count(DCGM_FI_DEV_GPU_UTIL offset 30d) * 100"}]},
      {"title": "Q+1 forecast GPU count", "type": "stat", "targets": [{"expr": "count(DCGM_FI_DEV_GPU_UTIL) * 1.20 * 1.30"}]},
      {"title": "Q+1 forecast cost per hour", "type": "stat", "targets": [{"expr": "count(DCGM_FI_DEV_GPU_UTIL) * 1.20 * 1.30 * 3.20"}]}
    ]
  }
}
```

The pattern is: the dashboard shows the current state; the dashboard forecasts the future; the dashboard recommends the GPU order. The capacity planning dashboard is what the CFO sees before the procurement order is signed.

---

## 6. Operating the performance engineering stack

### 6.1 The components

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| USE method dashboard | Grafana | Prometheus | Dashboard load p99 < 5 s |
| Roofline analysis | Python script (or notebook) | (no backing store) | (no SLO; offline analysis) |
| Performance decision tree | Grafana | Prometheus | Dashboard load p99 < 5 s |
| Cost-vs-latency trade-off dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| Capacity planning dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |

### 6.2 IAM and the performance methodology

The performance engineering stack has its own IAM. The pattern is:

| Role | Who | What they can do |
|---|---|---|
| `performance.reader` | The on-call; data scientists | Read the dashboards; query the metrics |
| `performance.writer` | The exporters | Write metrics to Prometheus |
| `performance.admin` | The platform team | Manage the dashboards; manage the methodology |

The performance methodology is the platform team's discipline. The methodology is documented; the methodology is trained; the methodology is updated after every incident.

### 6.3 Observability

| Metric | Why it matters | Alert |
|---|---|---|
| USE method panel load latency p99 | Dashboard performance | > 5 s |
| Decision tree panel load latency p99 | Dashboard performance | > 5 s |
| Roofline analysis run duration | Offline analysis performance | > 1 hour |
| Capacity planning dashboard accuracy | Procurement accuracy | Error > 20% |

The capacity planning dashboard accuracy alert is the most important. An inaccurate forecast is a forecast that orders the wrong number of GPUs; the team is either over-provisioned (wasting GPUs) or under-provisioned (missing SLOs).

---

## 7. How it fails

Six failure modes recur.

### 7.1 "The team cannot find the bottleneck"

**Symptom:** The workload is slow; the team runs the USE method; the team finds no bottleneck.

**Diagnosis:** The bottleneck is the combination of resources (e.g. CPU + GPU); the bottleneck is below the threshold (e.g. CPU at 70% but the kernel is inefficient); the bottleneck is the workload (e.g. inefficient Python code).

**Fix:** Add multi-resource analysis to the USE method; lower the bottleneck thresholds; profile the kernel; profile the Python code.

### 7.2 "The roofline model is too theoretical"

**Symptom:** The on-call computes the roofline; the roofline predicts 989 TFLOPS; the actual is 600 TFLOPS; the gap is 39%.

**Diagnosis:** The roofline is for the kernel only; the actual includes kernel launch overhead, memory allocation, and data transfer; the gap is the non-kernel overhead.

**Fix:** Include the kernel launch overhead in the roofline; measure the data transfer separately; account for the non-kernel overhead in the prediction.

### 7.3 "The decision tree is too shallow"

**Symptom:** The on-call follows the decision tree; the decision tree says "GPU utilisation is high"; the on-call optimises the GPU; the workload is still slow.

**Diagnosis:** The decision tree is missing branches (e.g. network, storage); the decision tree's thresholds are wrong; the decision tree does not account for multi-resource bottlenecks.

**Fix:** Add the missing branches; tune the thresholds; add multi-resource analysis; test the decision tree against historical incidents.

### 7.4 "The cost-vs-latency trade-off is not explicit"

**Symptom:** The team orders GPUs without a trade-off analysis; the team optimises kernels without measuring the cost; the team's procurement is wrong.

**Diagnosis:** The trade-off model is not in the team's workflow; the trade-off is implicit; the team's decisions are not data-driven.

**Fix:** Add the trade-off dashboard to the team's procurement workflow; add the trade-off analysis to the team's optimisation workflow; train the team on the trade-off model.

### 7.5 "The capacity planning forecast is wrong"

**Symptom:** The forecast says 156 GPUs; the actual usage is 100 GPUs; the team over-provisioned by 56 GPUs.

**Diagnosis:** The forecast model is wrong; the growth rate is wrong; the buffer is wrong; the historical data is wrong.

**Fix:** Tune the forecast model; review the historical data; add a confidence interval to the forecast; review the forecast quarterly.

### 7.6 "The performance methodology is not followed"

**Symptom:** The team optimises ad-hoc; the team does not use the USE method; the team does not use the roofline model; the team does not use the decision tree.

**Diagnosis:** The methodology is not in the team's workflow; the methodology is not trained; the methodology is not enforced.

**Fix:** Train the team on the methodology; add the methodology to the team's workflow; enforce the methodology in code review; automate the methodology in the dashboards.

---

## 8. Hands-on lab

This lab builds the USE method dashboard, computes the roofline for a sample kernel, follows the performance decision tree, and produces the capacity planning forecast. The lab is **untested** in this repository.

### 8.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+) with at least 1 H100 GPU node.
- Helm 3 for installing the observability stack.
- A PyTorch workload for the roofline analysis.

### 8.2 Step 1: deploy the USE method dashboard

```bash
kubectl -n monitoring create configmap use-method-dashboard \
  --from-file=dashboards/use_method.json

curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/use_method_import.json
# expected: the dashboard is available at /d/use/ai-factory-use-method
```

### 8.3 Step 2: run the USE method on a workload

```bash
# Apply a synthetic load to the cluster
hey -z 60s -c 100 -m POST -T "application/json" \
  -d '{"inputs":[{"name":"tier_gold","shape":[1],"datatype":"FP32","data":[1.0]}]}' \
  $INFERENCE_URL/v2/models/churn-model/infer

# Open Grafana and look at the USE method dashboard
# expected: the GPU utilisation panel is above 90%; the bottleneck is the GPU
```

### 8.4 Step 3: compute the roofline for a sample kernel

```python
# code/part17/roofline_analysis.py (shape only)
import torch
import torch.profiler

model = torch.nn.Transformer(d_model=512, nhead=8, num_layers=6).cuda()

with torch.profiler.profile(
    activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
    record_shapes=True,
) as prof:
    for _ in range(10):
        x = torch.randn(32, 128, 512).cuda()
        model(x)

# Export the profile
prof.export_chrome_trace("/profiles/transformer.json")

# Compute the roofline
flops = 4 * 32 * 128 * 128 * 512 * 6 * 12  # FLOPs for the forward pass
bytes = 32 * 128 * 512 * 4 * 6  # Bytes for activations and weights
intensity = flops / bytes
ridge = 989e12 / 3350e9  # H100 ridge point
print(f"Arithmetic intensity: {intensity:.0f} FLOP/byte")
print(f"H100 ridge point: {ridge:.0f} FLOP/byte")
print(f"Bottleneck: {'compute' if intensity > ridge else 'memory'}")
```

### 8.5 Step 4: follow the performance decision tree

```bash
# Open Grafana and look at the performance decision tree dashboard
# expected: the dashboard shows the current state of every panel
# expected: the recommended fix panel shows the bottleneck
```

### 8.6 Step 5: build the cost-vs-latency trade-off

```bash
# Compute the current cost and latency
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=sum(rate(kubecost_gpu_cost[1h]))' | jq .
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=histogram_quantile(0.99,%20rate(inference_request_duration_seconds_bucket[5m]))' | jq .
# expected: the current cost per hour; the current p99 latency
```

### 8.7 Step 6: produce the capacity planning forecast

```bash
# Query the current GPU pool utilisation
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=count(DCGM_FI_DEV_GPU_UTIL)' | jq .
# expected: the current GPU count

# Query the forecast (assuming 20% growth and 30% buffer)
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=count(DCGM_FI_DEV_GPU_UTIL)%20*%201.20%20*%201.30' | jq .
# expected: the Q+1 forecast GPU count
```

### 8.8 What to record

After the lab, you should be able to answer five questions in five seconds each:

1. What is the current GPU utilisation per the USE method?
2. What is the current roofline gap per the kernel profile?
3. What is the current bottleneck per the decision tree?
4. What is the current cost-vs-latency trade-off per the dashboard?
5. What is the current Q+1 GPU forecast per the capacity planning model?

If any takes more than 30 seconds, the performance engineering stack is not yet a production service. The lab is **untested** against a live GKE cluster.

---

## Exercises

1. **Add a per-team USE method dashboard.** Build a USE method dashboard per team; the dashboard filters the metrics by team label. *Solution sketch:* a Grafana dashboard template with team-specific filters; the dashboard is the team's view of the USE method.
2. **Add a roofline analysis script.** Build a Python script that takes a PyTorch profile and computes the roofline for each kernel. *Solution sketch:* a Python script that reads the profile; computes the arithmetic intensity; compares to the ridge point; outputs the bottleneck.
3. **Add a decision tree integration test.** Build an integration test that runs the decision tree against historical incidents; verify the tree produces the correct bottleneck. *Solution sketch:* a Python test that takes an incident; runs the decision tree; asserts the bottleneck matches the incident's root cause.
4. **Add a cost-vs-latency trade-off dashboard.** Build a Grafana dashboard that shows the trade-off per team; the dashboard is the team's view of the trade-off. *Solution sketch:* a Grafana dashboard with the current cost, the current latency, the options, and the recommended fix.
5. **Add a capacity planning script.** Build a Python script that takes the current GPU pool utilisation and produces the Q+1 forecast. *Solution sketch:* a Python script that reads the metrics; applies the forecast model; outputs the GPU count and the cost.
6. **Add a performance engineering playbook.** Build a document that walks the team through the methodology: USE method, roofline model, decision tree, trade-off model, capacity planning. *Solution sketch:* a Markdown document with the methodology; the document is the team's playbook.

---

## Checkpoint questions

<details><summary>1. What is the USE method?</summary>
A performance engineering methodology that says: for every resource, check utilisation, saturation, and errors. The bottleneck is the resource that is most utilised, most saturated, or most error-prone. The method was introduced by Brendan Gregg in *Systems Performance* Chapter 1.
</details>

<details><summary>2. What does the USE method measure for a GPU?</summary>
Utilisation (SM utilisation, memory utilisation), saturation (queue depth, pending collectives), errors (ECC errors, Xid errors). The on-call applies the USE method; the on-call finds the bottleneck; the on-call fixes the bottleneck.
</details>

<details><summary>3. What is the roofline model?</summary>
A model that says: the achievable performance is bounded by the hardware peak (compute or bandwidth) and the workload's arithmetic intensity (operations per byte). The model predicts whether a kernel is memory-bound or compute-bound; the model tells the on-call where the optimisation opportunity is.
</details>

<details><summary>4. What is the arithmetic intensity?</summary>
The ratio of floating-point operations to bytes transferred. I = FLOPs / Bytes. The roofline model compares I to the ridge point (compute peak / bandwidth); the kernel is memory-bound if I < ridge, compute-bound if I > ridge.
</details>

<details><summary>5. What is the performance decision tree?</summary>
A structured guide for finding the bottleneck. The tree has branches that lead to the bottleneck. The on-call follows the tree; the on-call finds the bottleneck in seconds; the on-call fixes the bottleneck. The tree is implemented as a Grafana dashboard; the tree is updated after every incident.
</details>

<details><summary>6. What is the cost-vs-latency trade-off?</summary>
The most important performance decision. The trade-off is: how much latency can the team afford to save by adding GPUs? The trade-off is: how much GPU spend can the team afford to save by adding latency? The trade-off is made explicit by the trade-off dashboard; the team picks the best option.
</details>

<details><summary>7. What is the capacity planning model?</summary>
A model that turns the current usage into the future GPU order. The model is: forecast the next quarter's usage; add a buffer for spikes; order the GPUs. The model is implemented as a Grafana dashboard; the dashboard is what the CFO sees before the procurement order is signed.
</details>

<details><summary>8. What is the ridge point?</summary>
The arithmetic intensity at which a kernel transitions from memory-bound to compute-bound. I_ridge = compute peak / bandwidth. For the H100 (FP16), I_ridge = 295 FLOP/byte.
</details>

<details><summary>9. What is the most common performance failure mode?</summary>
The team cannot find the bottleneck. The workload is slow; the team runs the USE method; the team finds no bottleneck. The bottleneck is the combination of resources (e.g. CPU + GPU); the bottleneck is below the threshold; the bottleneck is the workload. The fix is to add multi-resource analysis to the USE method.
</details>

<details><summary>10. What is the most common roofline model failure?</summary>
The roofline is too theoretical. The on-call computes the roofline; the actual is below the predicted. The roofline is for the kernel only; the actual includes kernel launch overhead and data transfer. The fix is to include the non-kernel overhead in the roofline.
</details>

<details><summary>11. What is the most common decision tree failure?</summary>
The decision tree is too shallow. The on-call follows the tree; the decision tree says "GPU utilisation is high"; the on-call optimises the GPU; the workload is still slow. The decision tree is missing branches (e.g. network, storage). The fix is to add the missing branches; tune the thresholds.
</details>

<details><summary>12. What is the most common cost-vs-latency failure?</summary>
The trade-off is not explicit. The team orders GPUs without a trade-off analysis; the team optimises kernels without measuring the cost. The trade-off model is not in the team's workflow. The fix is to add the trade-off dashboard to the team's procurement workflow.
</details>

<details><summary>13. What is the most common capacity planning failure?</summary>
The forecast is wrong. The forecast says 156 GPUs; the actual usage is 100 GPUs; the team over-provisioned. The forecast model is wrong; the growth rate is wrong; the buffer is wrong. The fix is to tune the forecast model; review the historical data; add a confidence interval.
</details>

<details><summary>14. What is the difference between utilisation and saturation?</summary>
Utilisation is the fraction of the resource that is in use (e.g. GPU SM utilisation 80%). Saturation is the degree to which the resource has more work queued than it can process (e.g. GPU queue depth 50). Utilisation is the current state; saturation is the queue.
</details>

<details><summary>15. What is the difference between the USE method and the RED method?</summary>
USE measures the resource's behaviour from the operator's perspective (utilisation, saturation, errors). RED measures the service's behaviour from the customer's perspective (rate, errors, duration). The two are complementary; a healthy service has good RED metrics; a healthy resource has good USE metrics.
</details>

<details><summary>16. Why is the roofline model a platform-team discipline?</summary>
Because the roofline model is what predicts kernel performance; the roofline model is what tells the on-call where the optimisation opportunity is. The platform team owns the methodology; the platform team owns the dashboards; the platform team owns the training. A team that does not use the roofline model is a team that optimises ad-hoc.
</details>

<details><summary>17. What is the difference between the roofline model and the benchmarking methodology?</summary>
The roofline model predicts kernel performance from first principles (compute peak, bandwidth, arithmetic intensity). The benchmarking methodology measures actual performance against a baseline. The two are complementary; the roofline predicts; the benchmark validates.
</details>

<details><summary>18. What is the relationship between the decision tree and the failure mode catalogue?</summary>
The decision tree is the on-call's guide for finding the bottleneck. The failure mode catalogue is the on-call's guide for naming the failure. The two are complementary; the decision tree tells the on-call where to look; the catalogue tells the on-call what to call it.
</details>

<details><summary>19. What is the relationship between capacity planning and the cost dashboard?</summary>
The capacity planning model is the forward-looking view; the cost dashboard is the backward-looking view. The capacity planning model uses the historical cost data; the cost dashboard is the source of the historical cost data. The two are complementary; the cost dashboard tells the team what the GPUs cost; the capacity planning model tells the team how many GPUs to buy.
</details>

<details><summary>20. What five questions should the performance engineering lab let you answer in five seconds each?</summary>
What is the current GPU utilisation per the USE method. What is the current roofline gap per the kernel profile. What is the current bottleneck per the decision tree. What is the current cost-vs-latency trade-off per the dashboard. What is the current Q+1 GPU forecast per the capacity planning model. If any takes more than 30 seconds, the performance engineering stack is not yet a production service.
</details>

---

## Sources and review notes

- *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chapters 1, 8). Source for the performance engineering methodology, the roofline model, and the operational discipline. The wording has been rewritten in the handbook's voice.
- *Engineering AI Systems* (`engineering-ai-systems-architecture-and-devops-essentials`, Chapter 8). Source for the performance engineering patterns for AI systems.
- *Systems Performance* (`systems-performance-2nd-edition`, Chapters 1, 2). Source for the USE method and the performance engineering methodology.

### Cross-references to other handbook chapters

- Chapter 1.23 for the USE method and the roofline model.
- Chapter 1.25 for the benchmarking methodology.
- Chapter 10.5 for the roofline model details.
- Chapter 17.5 for the profiling tools.

### Migrated from `nvidia-devops`

The performance engineering methodology draws on the *AI Systems Performance Engineering* corpus and the *Engineering AI Systems* corpus. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The USE method thresholds (90% utilisation, 50 queue depth) are starting points; specific thresholds depend on the workload.
- The roofline ridge points are GPU-specific; specific ridge points depend on the GPU model.
- The capacity planning buffer (30%) is a starting point; specific buffers depend on the workload's spike pattern.

### Not verified on live hardware

- The lab in Section 8 is **untested** against a live GKE cluster in this repository.
- The roofline analysis in the lab is illustrative; production analyses depend on the workload.
- The capacity planning forecast in the lab is illustrative; production forecasts depend on the historical data.
