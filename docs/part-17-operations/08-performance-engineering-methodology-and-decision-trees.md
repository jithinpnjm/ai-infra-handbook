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

Picture a training job that used to finish overnight and now runs past the morning shift. The GPU graphs look busy, so nobody can say what changed. Without a method, the team guesses. It adds a node, raises the batch size or rewrites a kernel, and hopes for the best. Performance engineering replaces that guessing with a repeatable way to find the real bottleneck.

The payoff is both speed and money. A team that finds the real bottleneck can often run the same work on fewer GPUs, with lower latency. A team that skips that step tends to pay for capacity its workload never uses.

Busy time alone can mislead you. AI Systems Performance Engineering, chapter 20, points out that a GPU can look fully busy while it moves redundant data, and that this work is not productive. The book's advice is to measure goodput, the useful work actually delivered, and not only how busy the device is.

The block below states the argument in short form. Its percentages and dollar amounts are illustrative, not measured, so check them against your own platform before you quote them.

```text
Why performance engineering is on the critical path (background reading: AI Systems Performance Engineering; Engineering AI Systems; the figures below are examples, not quotations):
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

Three operational realities make this a platform-team concern, not only a data-science concern. The method has to be repeatable, and the platform team is the group that can make it so. The decision tree is what an on-call engineer follows at night, so the platform team has to publish it and keep it current. The cost-versus-latency trade-off is also a platform decision, because the platform team owns the GPU pool and the service levels. The data scientists consume that trade-off, and the platform team has to make it visible to them.

**Optimising without a method is guessing.** Before you change any code, decide which method you will use to find the bottleneck.

## Prerequisites and outcomes

Before you use the methods in this chapter, check that you know the material they build on. The chapters below cover the basic checks, the benchmarking habits and the profiling tools that the rest of the chapter assumes.

### Prerequisites

- Chapter 1.23 (Performance methodology) for the USE method and the roofline model.
- Chapter 1.25 (Benchmarking correctly) for the benchmarking methodology.
- Chapter 10.5 (The roofline model) for the roofline model details.
- Chapter 17.5 (Distributed observability and profiling) for the profiling tools.

### Outcomes

By the end of this chapter, you should be able to:

1. Use the USE method to find the bottleneck, by checking utilisation, saturation and errors.
2. Use the roofline model to estimate how fast a kernel can run.
3. Follow the performance decision tree to the likely bottleneck.
4. Compare the cost of more GPUs with the cost of more latency, in one explicit model.
5. Run a capacity forecast and the performance stack on GKE as a repeatable routine.

---

## 1. The USE method

### 1.1 The USE method in detail

Imagine you are paged with one line: the workload is slow. You do not yet know whether the GPU, the disk, the network or the code is at fault. The USE method gives you a fixed set of questions, so you check every resource in the same order each time. The handbook's source for the method is *Systems Performance*.

For each resource, the method asks three questions. How busy is it? Is work waiting in a queue? Is it producing errors? The table is a checklist that names the metric to pull for each resource, so do not skip a row just because you do not suspect it.

| Resource | Utilisation | Saturation | Errors |
|---|---|---|---|
| **GPU** | SM utilisation, memory utilisation | Queue depth, pending collectives | ECC errors, Xid errors |
| **CPU** | Utilisation per core | Run queue length, load average | Context switch rate, page faults |
| **Memory** | Used vs total | Page-in rate, swap activity | OOM kills, allocation failures |
| **Disk I/O** | IOPS utilisation, bandwidth | Queue depth, await time | I/O errors, SMART warnings |
| **Network** | Bandwidth utilisation | Queue depth, dropped packets | CRC errors, link flaps |
| **Storage** | Object store request rate | 5xx rate, latency p99 | Object lock failures, 4xx rate |

The bottleneck is the resource that stands out on one or more of the three questions. Fix that resource, then measure again, because a fix often exposes the next limit.

### 1.2 The USE method in action

Here is the check applied to a slow workload. Each resource gets a short line with its three readings and a verdict. The lines are example data, so read them for the pattern, not the exact values.

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

The disk stands out. Its queue depth is 50, which means 50 requests are waiting at the same time, and that queue is the clue. The remedy is either faster storage or fewer, larger reads. The whole check took one pass over the metrics, before anyone opened a profiler.

### 1.3 The USE method as a Grafana dashboard

Checking these metrics by hand every time is slow, so put them on one screen. A Grafana dashboard with one panel per metric becomes the on-call engineer's first page. Give each resource its three panels, for utilisation, saturation and errors.

```yaml
# code/part17/use_method_dashboard.json
{
  "dashboard": {
    "title": "AI Factory - USE Method",
    "panels": [
      {"title": "GPU utilisation", "type": "timeseries", "targets": [{"expr": "DCGM_FI_DEV_GPU_UTIL_RATIO"}]},
      {"title": "GPU saturation (queue depth)", "type": "stat", "targets": [{"expr": "kube_pod_status_phase{phase=\"Pending\"}"}]},
      {"title": "GPU errors (ECC)", "type": "stat", "targets": [{"expr": "DCGM_FI_DEV_ECC_DBE_VOL_TOTAL"}]},
      {"title": "CPU utilisation", "type": "timeseries", "targets": [{"expr": "100 - avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100"}]},
      {"title": "Memory utilisation", "type": "timeseries", "targets": [{"expr": "node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes"}]},
      {"title": "Disk I/O utilisation", "type": "timeseries", "targets": [{"expr": "rate(node_disk_io_time_seconds_total[5m])"}]},
      {"title": "Network utilisation", "type": "timeseries", "targets": [{"expr": "rate(node_network_transmit_bytes_total[5m])"}]},
      {"title": "Storage latency p99", "type": "stat", "targets": [{"expr": "s3_request_duration_seconds{quantile=\"0.99\"}"}]}
    ]
  }
}
```

Build this dashboard on a quiet day, not in the middle of an incident. Once it exists, the next on-call can start the USE method from the same page you used.

## 2. The roofline model

### 2.1 The roofline model in detail

Suppose a kernel runs well below what the GPU can deliver. You need to know whether the limit is the arithmetic units or the memory system, because the fixes are different. The roofline model answers that question with one number, the arithmetic intensity, which is how much math a kernel does for each byte it moves.

The model caps performance with two lines. One is the compute peak. The other rises with intensity and is set by memory bandwidth. Where they meet is the ridge point. A kernel left of the ridge waits on memory, and a kernel right of it waits on arithmetic.

AI Systems Performance Engineering, chapter 8, shows how to get this picture from a tool. Nsight Compute has a roofline section that plots each kernel's achieved performance against both roofs. It also reports the kernel's arithmetic intensity directly, so you do not have to count it by hand.

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

The ridge point is simply the compute peak divided by the bandwidth. For these H100 figures, that gives about 295 FLOP per byte. For each kernel, compute its intensity, compare it with the ridge, and decide which side it falls on. The fix depends on the answer.

### 2.2 The roofline model in action

Take a transformer attention kernel as the example. Before you decide on a fix, you need its arithmetic intensity. The block below works through the counts for one set of sizes.

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

On these counts, the kernel looks compute-bound, so the chapter suggests lower precision or fuller use of Tensor Cores. Check the counts before you act on them. A wrong byte count changes the answer, and the roofline is only as good as the numbers you feed it.

### 2.3 The roofline model as a profiling tool

Once you have a roofline, use it as a yardstick for every kernel you profile. Measure what the kernel actually achieves and compare it with the roof. The distance between the two is the room you have to improve.

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

Be careful where the numbers come from. AI Systems Performance Engineering, chapter 8, notes that the PyTorch profiler's FLOP counts are formula-based estimates for a limited set of operators. They do not come from hardware counters. For measured numbers, run Nsight Compute on the kernel you care about.

Pick the one kernel that matters most to your service, and compute its roofline before you change anything.

## 3. The performance decision tree

### 3.1 The decision tree structure

The USE table asks you to check every resource. When you are under pressure, you want a shorter route to the same answer. The decision tree is that route. Each question has a yes or no answer, and each answer moves you one step closer to a likely cause.

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

The percentages in the diamonds, such as 90 percent, are example thresholds. Your team should choose its own values from its own workloads. One more point comes from AI Systems Performance Engineering, chapter 16. If GPU utilisation is lower than you expect, check GPU memory first. When memory is nearly full, the inference engine may be moving cache data to host memory or disk, and the GPUs sit idle while they wait. A rise in copy-engine activity while SM utilisation falls is a sign of that swapping.

### 3.2 The decision tree in action

Suppose the training job is slow and the on-call starts at the top of the tree. The walk below follows the steps the way the tree asks them. Each step records a reading and a decision.

```text
Decision tree application:
- Step 1: GPU utilisation > 90%? Yes -> continue to step 2; No -> go to step 5
- Step 2: Memory utilisation > 90%? No -> kernel optimisation (Tensor Cores, FP8)
- Step 5: CPU utilisation > 90%? No -> continue to step 8
- Step 8: Network bound? Yes -> check for congestion
- Step 9: Network congestion? Yes -> apply QoS
- Step 10: Network QoS applied -> training is faster
```

The walk ends at the network. The fix was QoS, and the workload improved. The example ends in a network fix rather than a GPU change, which is the kind of result the tree is meant to reach.

### 3.3 The decision tree as a Grafana dashboard

The same questions can live on a Grafana dashboard, with one stat panel per question. Each panel shows the current answer, so the on-call does not have to type the queries again. The last panel is a text placeholder for the recommended fix, and someone has to write that logic for it.

```yaml
# code/part17/decision_tree_dashboard.json
{
  "dashboard": {
    "title": "AI Factory - Performance Decision Tree",
    "panels": [
      {"title": "Step 1: GPU utilisation > 90%?", "type": "stat", "targets": [{"expr": "DCGM_FI_DEV_GPU_UTIL_RATIO > 0.9"}]},
      {"title": "Step 2: Memory utilisation > 90%?", "type": "stat", "targets": [{"expr": "DCGM_FI_DEV_FB_USED_BYTES / DCGM_FI_DEV_FB_CAPACITY_BYTES > 0.9"}]},
      {"title": "Step 5: CPU utilisation > 90%?", "type": "stat", "targets": [{"expr": "100 - avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100 > 90"}]},
      {"title": "Step 8: Network bound?", "type": "stat", "targets": [{"expr": "rate(node_network_transmit_bytes_total[5m]) > 1e9"}]},
      {"title": "Recommended fix", "type": "text", "options": {"content": "Based on the panels above, the recommended fix is..."}}
    ]
  }
}
```

Before you trust the tree, walk it once against last month's slow job. If it would have led you to the wrong resource, fix the branch before the next incident.

## 4. The cost-vs-latency trade-off

### 4.1 The trade-off model

Suppose users complain that responses are slow. More GPUs would help, but they cost money, and a faster kernel might help for free. The question is which change buys the most speed for the least spend.

The trade-off has two sides. You can ask how much latency a GPU purchase saves. You can also ask how much GPU spend a latency fix saves, if users accept slower responses. Write both sides down before anyone signs an order.

The block below is a worked example with invented options. Copy its structure, not its numbers.

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

Compare the options on latency saved and extra cost, then pick the best return. AI Systems Performance Engineering, chapter 16, adds two cautions. A higher batching wait raises throughput, but setting it too high hurts tail latency, so tune it against your service level. The same chapter notes that newer GPUs can beat a larger fleet of older ones on cost.

### 4.2 The trade-off as a Grafana dashboard

Put the trade-off on a dashboard, so every team looks at the same numbers. The last panel depends on FinOps data that your team has to export, so the dashboard is only as good as that feed.

```yaml
# code/part17/cost_latency_dashboard.json
{
  "dashboard": {
    "title": "AI Factory - Cost vs Latency",
    "panels": [
      {"title": "Current p99 latency", "type": "stat", "targets": [{"expr": "histogram_quantile(0.99, rate(inference_request_duration_seconds_bucket[5m]))"}]},
      {"title": "Current GPU cost per hour", "type": "stat", "targets": [{"expr": "sum(rate(kubecost_gpu_cost[1h]))"}]},
      {"title": "Latency saved per GPU added (week over week)", "type": "table", "targets": [{"expr": "(inference:latency:p99:5m offset 7d - inference:latency:p99:5m) / (count(DCGM_FI_DEV_GPU_UTIL_RATIO) - count(DCGM_FI_DEV_GPU_UTIL_RATIO offset 7d))"}]},
      {"title": "ROI per optimisation (metrics are illustrative: your FinOps tooling must export them)", "type": "table", "targets": [{"expr": "sum by (optimisation) (optimisation_saving_per_month) / sum by (optimisation) (optimisation_cost)"}]}
    ]
  }
}
```

Before you approve a GPU purchase, write the latency saved and the cost added in the same table as the cheaper fixes.

## 5. Capacity planning

### 5.1 The capacity planning model

Every quarter, someone asks how many GPUs to order. A guess based on today's count leaves you with idle hardware or a missed service level. The model turns current usage into a forecast, adds a margin for spikes, and produces an order size.

The numbers in the block below are example values. Take the growth rate and the spike buffer from your own history.

```text
Capacity planning model:
- Current usage: 100 H100 GPUs at 80% utilisation
- Forecast growth: 20% per quarter
- Buffer: 30% for spikes
- Q+1 forecast: 100 * 1.20 * 1.30 = 156 GPUs
- Q+1 order: 156 GPUs (rounded up)
```

The model counts GPUs, not busy GPU hours, so the 80 percent utilisation in the first line does not change the result. If utilisation is low, the count alone will overstate the order. AI Systems Performance Engineering, chapter 16, suggests watching how latency rises as load rises. The load where tail latency climbs sharply shows the practical limit, which is a better basis for the order than the raw count.

### 5.2 The capacity planning dashboard

Put the same arithmetic on a dashboard, so the forecast updates as the metrics change.

```yaml
# code/part17/capacity_dashboard.json
{
  "dashboard": {
    "title": "AI Factory - Capacity Planning",
    "panels": [
      {"title": "Current GPU pool utilisation", "type": "stat", "targets": [{"expr": "avg(DCGM_FI_DEV_GPU_UTIL_RATIO) * 100"}]},
      {"title": "Current GPU count", "type": "stat", "targets": [{"expr": "count(DCGM_FI_DEV_GPU_UTIL_RATIO)"}]},
      {"title": "Forecast growth rate", "type": "stat", "targets": [{"expr": "(count(DCGM_FI_DEV_GPU_UTIL_RATIO) - count(DCGM_FI_DEV_GPU_UTIL_RATIO offset 30d)) / count(DCGM_FI_DEV_GPU_UTIL_RATIO offset 30d) * 100"}]},
      {"title": "Q+1 forecast GPU count", "type": "stat", "targets": [{"expr": "count(DCGM_FI_DEV_GPU_UTIL_RATIO) * 1.20 * 1.30"}]},
      {"title": "Q+1 forecast cost per hour", "type": "stat", "targets": [{"expr": "count(DCGM_FI_DEV_GPU_UTIL_RATIO) * 1.20 * 1.30 * 3.20"}]}
    ]
  }
}
```

The last panel uses an example rate of 3.20 per GPU hour. Replace it with the rate in your own contract before the number reaches finance.

Before the next procurement cycle, compare last quarter's forecast with the actual GPU count and write down the error.

## 6. Operating the performance engineering stack

### 6.1 The components

Each piece of the stack runs somewhere, stores its data somewhere, and has a target for how fast it should answer. The targets in the table are example values, not measured service levels. Choose your own before you publish them to users.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| USE method dashboard | Grafana | Prometheus | Dashboard load p99 < 5 s |
| Roofline analysis | Python script (or notebook) | (no backing store) | (no SLO; offline analysis) |
| Performance decision tree | Grafana | Prometheus | Dashboard load p99 < 5 s |
| Cost-vs-latency trade-off dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| Capacity planning dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |

The roofline analysis is the only component with no backing store, because it runs offline against a profile file.

### 6.2 IAM and the performance methodology

Not everyone who reads a dashboard should be able to change one. The pattern below gives three roles, so readers, exporters and the platform team each get only the rights they need.

| Role | Who | What they can do |
|---|---|---|
| `performance.reader` | The on-call; data scientists | Read the dashboards; query the metrics |
| `performance.writer` | The exporters | Write metrics to Prometheus |
| `performance.admin` | The platform team | Manage the dashboards; manage the methodology |

Documentation and training are part of the discipline. Update the method after every incident, so the next on-call inherits what the last one learned.

### 6.3 Observability

The stack needs its own alerts, because a broken dashboard during an incident is worse than no dashboard. The table lists four alerts. The thresholds are example values, so set them against what your on-call can tolerate.

| Metric | Why it matters | Alert |
|---|---|---|
| USE method panel load latency p99 | Dashboard performance | > 5 s |
| Decision tree panel load latency p99 | Dashboard performance | > 5 s |
| Roofline analysis run duration | Offline analysis performance | > 1 hour |
| Capacity planning dashboard accuracy | Procurement accuracy | Error > 20% |

Of the four, the forecast accuracy alert matters most. A forecast that is too high wastes GPUs, and a forecast that is too low puts service levels at risk.

## 7. How it fails

Six failure modes come back again and again in performance reviews. Each one below gives the symptom you will recognise, the likely cause and the first fix to try. The numbers are illustrative, so they show the shape of each failure rather than a real measurement.

### 7.1 "The team cannot find the bottleneck"

Symptom: the workload is slow, the team runs the USE method, and no resource stands out.

Diagnosis: the bottleneck may be a mix of resources, such as CPU and GPU together. It may sit below the alert threshold, as a CPU at 70 percent can hide an inefficient kernel. Or the limit may be the code itself, such as slow Python.

Fix: add a check for combinations of resources to the method. Lower the thresholds for the resources you suspect, then profile the kernel and the Python code.

### 7.2 "The roofline model is too theoretical"

Symptom: the roofline predicts 989 TFLOPS for a kernel, but the measured run reaches 600 TFLOPS. That is a gap of 39 percent.

Diagnosis: the roofline describes the kernel alone. The measured time also includes launch overhead, memory allocation and data transfer, and that extra time can account for the gap.

Fix: include launch overhead when you compare, time the data transfers separately, and account for the rest in your prediction.

### 7.3 "The decision tree is too shallow"

Symptom: the tree says GPU utilisation is high, so the on-call tunes the GPU, and the job is still slow.

Diagnosis: the tree may be missing a branch for network or storage. Its thresholds may be wrong for your workload. It may also miss a bottleneck that spans more than one resource.

Fix: add the missing branches and tune the thresholds on your own data. Then replay the tree against past incidents to see whether it would have found the cause.

### 7.4 "The cost-vs-latency trade-off is not explicit"

Symptom: the team buys GPUs without a trade-off analysis, and it tunes kernels without measuring what they cost.

Diagnosis: the trade-off is not part of the buying or tuning workflow, so the decision rests on instinct.

Fix: put the trade-off dashboard into the procurement review. Ask for the latency and cost comparison before any order is placed.

### 7.5 "The capacity planning forecast is wrong"

Symptom: the forecast says 156 GPUs, but actual usage is 100 GPUs, so the team over-provisioned by 56.

Diagnosis: the growth rate, the buffer or the history behind the forecast may be wrong.

Fix: check the history first. Add a confidence range to the forecast, and review it every quarter.

### 7.6 "The performance methodology is not followed"

Symptom: the team tunes ad hoc, and nobody uses the USE method, the roofline or the decision tree.

Diagnosis: the method is not part of the workflow, nobody has been trained on it, and nobody enforces it.

Fix: train the team, add the method to the workflow, check it in code review, and automate the dashboards that support it.

Pick the failure your team hit most recently. Check whether one of these fixes would have shortened that incident.

## 8. Hands-on lab

This lab ties the chapter together. You build the USE dashboard, compute a roofline, walk the decision tree and produce a capacity forecast on GKE. The lab is untested in this repository, so treat each expected result as a hypothesis you still need to confirm.

### 8.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+) with at least 1 H100 GPU node.
- Helm 3 for installing the observability stack.
- A PyTorch workload for the roofline analysis.

### 8.2 Step 1: deploy the USE method dashboard

Load the dashboard first, so the rest of the lab has something to read.

```bash
kubectl -n monitoring create configmap use-method-dashboard \
  --from-file=dashboards/use_method.json

curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/use_method_import.json
# expected: the dashboard is available at /d/use/ai-factory-use-method
```

### 8.3 Step 2: run the USE method on a workload

Next, put load on the service and see which panel moves. The load generator below sends 100 concurrent requests for 60 seconds.

```bash
# Apply a synthetic load to the cluster
hey -z 60s -c 100 -m POST -T "application/json" \
  -d '{"inputs":[{"name":"tier_gold","shape":[1],"datatype":"FP32","data":[1.0]}]}' \
  $INFERENCE_URL/v2/models/churn-model/infer

# Open Grafana and look at the USE method dashboard
# expected: the GPU utilisation panel is above 90%; the bottleneck is the GPU
```

If the GPU panel stays low, the bottleneck is somewhere else, so go back to the USE table and work through the other rows.

### 8.4 Step 3: compute the roofline for a sample kernel

Next, compute the roofline for a small transformer. The script profiles ten forward passes, then estimates intensity from hand-counted FLOPs and bytes. Treat those counts as an estimate, not a measurement, for the reasons given in section 2.3.

```python
# code/part17/snippets/roofline_analysis.py
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

Compare the printed intensity with the ridge point. If the counts are right, the script shows which side of the ridge the model sits on.

### 8.5 Step 4: follow the performance decision tree

Open the decision tree dashboard and check that each panel shows a current value. The recommended-fix panel only shows placeholder text until someone writes its logic, so read the other panels to find the bottleneck.

```bash
# Open Grafana and look at the performance decision tree dashboard
# expected: the dashboard shows the current state of every panel
# expected: the recommended fix panel shows the bottleneck
```

### 8.6 Step 5: build the cost-vs-latency trade-off

Query the current cost and the p99 latency from Prometheus. Record both numbers before you compare any options.

```bash
# Compute the current cost and latency
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=sum(rate(kubecost_gpu_cost[1h]))' | jq .
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=histogram_quantile(0.99,%20rate(inference_request_duration_seconds_bucket[5m]))' | jq .
# expected: the current cost per hour; the current p99 latency
```

### 8.7 Step 6: produce the capacity planning forecast

Last, query the GPU count and the forecast. The forecast command uses the example growth and buffer from section 5, so change those values to match your own history.

```bash
# Query the current GPU pool utilisation
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=count(DCGM_FI_DEV_GPU_UTIL)' | jq .
# expected: the current GPU count

# Query the forecast (assuming 20% growth and 30% buffer)
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=count(DCGM_FI_DEV_GPU_UTIL)%20*%201.20%20*%201.30' | jq .
# expected: the Q+1 forecast GPU count
```

> **dcgm-exporter 4.9.0 version note.** dcgm-exporter 4.9.0 (2026-11-06) renamed many default metrics and changed some units. For example `DCGM_FI_DEV_GPU_UTIL` (percent) became `DCGM_FI_DEV_GPU_UTIL_RATIO` (0 to 1), and `DCGM_FI_DEV_FB_USED` (MiB) became `DCGM_FI_DEV_FB_USED_BYTES`. The metric names in this chapter are the 4.8.x names. On a 4.9.0 exporter use the [full mapping in 17.4](04-dcgm-exporter-and-interpreting-gpu-metrics.md#14-what-dcgm-exporter-490-renamed), and change thresholds together with the unit.

### 8.8 What to record

After the lab, you should be able to answer five questions quickly. The chapter uses five seconds per answer as its target, and that is an example value, not a standard. Answers that take longer suggest the stack is not yet ready for on-call use.

1. What is the current GPU utilisation per the USE method?
2. What is the current roofline gap per the kernel profile?
3. What is the current bottleneck per the decision tree?
4. What is the current cost-vs-latency trade-off per the dashboard?
5. What is the current Q+1 GPU forecast per the capacity planning model?

The lab has not yet been run against a live GKE cluster. Run it on a quiet day first, and record the answers so you can compare them later.

## Exercises

1. Add a per-team USE dashboard. Build one USE dashboard per team, with the metrics filtered by a team label. *Solution sketch:* a Grafana dashboard template with a team filter, so each team sees its own USE view.
2. Add a roofline analysis script. Build a Python script that reads a PyTorch profile and computes the roofline for each kernel. *Solution sketch:* the script reads the profile, computes the intensity, compares it with the ridge point and prints the bottleneck.
3. Add a decision tree integration test. Replay past incidents through the tree and check that it reaches the recorded root cause. *Solution sketch:* a Python test that takes an incident, runs the tree and asserts that the bottleneck matches the root cause.
4. Add a cost-vs-latency trade-off dashboard. Build a Grafana dashboard that shows the trade-off for each team. *Solution sketch:* one page with the current cost, the current latency, the options and the recommended fix.
5. Add a capacity planning script. Build a Python script that reads the current pool utilisation and prints the next-quarter forecast. *Solution sketch:* the script reads the metrics, applies the forecast model and prints the GPU count and cost.
6. Add a performance engineering playbook. Write a short playbook that covers the USE method, the roofline, the decision tree, the trade-off and capacity planning. *Solution sketch:* a Markdown document the team can follow during an incident.

Start with exercise 3 if you have past incidents on hand. A decision tree that has never been tested against real incidents is still a guess, and you will not know its gaps until you try it. Pick one exercise you can finish this month.

## Checkpoint questions

<details><summary>1. What is the USE method?</summary>
It is a method that asks you to check utilisation, saturation and errors for every resource. The bottleneck is whichever resource is most utilised, most saturated or most error-prone. The method was introduced by Brendan Gregg in *Systems Performance* Chapter 1.
</details>

<details><summary>2. What does the USE method measure for a GPU?</summary>
For a GPU, utilisation means SM and memory use, saturation means queue depth and pending collectives, and errors means ECC and Xid errors. You apply the method, find the bottleneck, and then fix it.
</details>

<details><summary>3. What is the roofline model?</summary>
The roofline model says a kernel's performance is capped by the hardware peak and by its arithmetic intensity, meaning the operations per byte it moves. It predicts whether the kernel is memory-bound or compute-bound, which tells you where to look for a speedup.
</details>

<details><summary>4. What is the arithmetic intensity?</summary>
It is the ratio of floating-point operations to the bytes transferred. Written as a formula, I = FLOPs / Bytes. The kernel is memory-bound when I is below the ridge point, which is the compute peak divided by bandwidth, and compute-bound when I is above it.
</details>

<details><summary>5. What is the performance decision tree?</summary>
It is a structured guide for finding the bottleneck. Each branch asks a yes or no question and moves you closer to the cause. You follow the tree from the top until it names the bottleneck. The tree is built as a Grafana dashboard, and the team updates it after every incident.
</details>

<details><summary>6. What is the cost-vs-latency trade-off?</summary>
It is the performance decision that matters most. It asks how much latency you can save by adding GPUs. It also asks how much GPU spend you can save by accepting more latency. The trade-off dashboard makes both sides visible, so the team can pick the best option.
</details>

<details><summary>7. What is the capacity planning model?</summary>
It turns current usage into the GPU order for the next period. You forecast the next quarter's usage, add a margin for spikes, and then order the GPUs. A Grafana dashboard shows the same arithmetic, and finance reviews it before the purchase is signed.
</details>

<details><summary>8. What is the ridge point?</summary>
It is the arithmetic intensity where a kernel changes from memory-bound to compute-bound. You get it by dividing the compute peak by the bandwidth. For an H100 at FP16, that works out to 295 FLOP per byte.
</details>

<details><summary>9. What is the most common performance failure mode?</summary>
The most common failure is that the team cannot find the bottleneck. The workload is slow, the team runs the USE method, and nothing stands out. The bottleneck may be a mix of resources, may sit below the threshold, or may be in the code itself. The fix is to add multi-resource analysis to the USE method.
</details>

<details><summary>10. What is the most common roofline model failure?</summary>
The roofline is too theoretical. The on-call computes the roofline, and the measured result comes in below the prediction. The roofline covers the kernel alone, while the measured time also includes kernel launch overhead and data transfer. The fix is to include the non-kernel overhead in the roofline.
</details>

<details><summary>11. What is the most common decision tree failure?</summary>
The decision tree is too shallow. The on-call follows the tree, which says "GPU utilisation is high", so the on-call optimises the GPU, and the workload is still slow. The tree is probably missing branches for network or storage. The fix is to add the missing branches and tune the thresholds.
</details>

<details><summary>12. What is the most common cost-vs-latency failure?</summary>
The trade-off is not explicit. The team orders GPUs without a trade-off analysis, and it optimises kernels without measuring the cost. The trade-off model is not part of the team's workflow. The fix is to add the trade-off dashboard to the team's procurement workflow.
</details>

<details><summary>13. What is the most common capacity planning failure?</summary>
The forecast is wrong. It says 156 GPUs, but actual usage is 100 GPUs, so the team over-provisioned. The forecast model, the growth rate or the buffer may be wrong. The fix is to tune the forecast model, review the historical data and add a confidence interval.
</details>

<details><summary>14. What is the difference between utilisation and saturation?</summary>
Utilisation is the fraction of the resource that is in use, such as GPU SM utilisation of 80 percent. Saturation is how much work is queued beyond what the resource can process, such as a GPU queue depth of 50. Utilisation describes the current state, and saturation describes the queue.
</details>

<details><summary>15. What is the difference between the USE method and the RED method?</summary>
USE looks at a resource from the operator's side, through utilisation, saturation and errors. RED looks at a service from the customer's side, through rate, errors and duration. The two complement each other, since a healthy service shows good RED metrics and a healthy resource shows good USE metrics.
</details>

<details><summary>16. Why is the roofline model a platform-team discipline?</summary>
The roofline model predicts kernel performance, and it shows the on-call where the optimisation opportunity sits. The platform team owns the methodology, the dashboards and the training. A team that does not use the roofline model tends to optimise ad hoc.
</details>

<details><summary>17. What is the difference between the roofline model and the benchmarking methodology?</summary>
The roofline model predicts kernel performance from first principles, using compute peak, bandwidth and arithmetic intensity. The benchmarking methodology measures actual performance against a baseline. The two complement each other, because the roofline predicts and the benchmark checks the prediction.
</details>

<details><summary>18. What is the relationship between the decision tree and the failure mode catalogue?</summary>
The decision tree is the on-call's guide for finding the bottleneck. The failure mode catalogue is the on-call's guide for naming the failure. The two complement each other: the tree shows where to look, and the catalogue gives the failure its name.
</details>

<details><summary>19. What is the relationship between capacity planning and the cost dashboard?</summary>
The capacity planning model looks forward, while the cost dashboard looks back. The model uses historical cost data, and the dashboard is the source of that data. The cost dashboard shows what the GPUs cost, and the capacity planning model shows how many GPUs to buy.
</details>

<details><summary>20. What five questions should the performance engineering lab let you answer in five seconds each?</summary>
The five questions are: what is the current GPU utilisation per the USE method; what is the current roofline gap per the kernel profile; what is the current bottleneck per the decision tree; what is the current cost-vs-latency trade-off per the dashboard; and what is the current Q+1 GPU forecast per the capacity planning model. The five-second target is an example value, and an answer that takes over 30 seconds, another example limit, shows the stack is not yet a production service.
</details>

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
