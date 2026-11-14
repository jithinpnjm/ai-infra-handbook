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

Busy time alone can mislead you. AI Systems Performance Engineering, chapter 20, points out that a GPU can look fully busy while it moves redundant data, and that this work is not productive. The same source advises measuring goodput, the useful work actually delivered, and not only how busy the device is.

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

This chapter walks through four tools for slow or expensive workloads: the USE method, the roofline model, the performance decision tree and the cost-versus-latency trade-off. It then shows how to forecast capacity, and it ends with the GKE lab, where you run the whole stack as a routine you can repeat.

---

## 1. The USE method

### 1.1 The USE method in detail

Picture the page itself. It has one line in it: the workload is slow. You do not yet know whether the GPU, the disk, the network or the code is at fault, and the team is waiting for an answer. The USE method gives you a fixed set of questions, so you check every resource in the same order each time, instead of starting with whatever you happen to suspect. The handbook's source for the method is *Systems Performance*.

For each resource, the method asks three questions. How busy is it? Is work waiting in a queue? Is it producing errors? Busy means the resource is doing work. Waiting means requests are lining up behind it, and that is the sign of saturation. Errors are the faults the resource reports, such as a bad memory bit or a failed I/O. The table is a checklist that names the metric to pull for each resource, so do not skip a row just because you do not suspect it. The rows you skip are often the ones that hide the problem.

A practical habit helps here. Write the three answers for each resource in a shared note before anyone names a cause. Teams that skip this step tend to argue from memory, and memory favours the resource that was broken last week.

| Resource | Utilisation | Saturation | Errors |
|---|---|---|---|
| **GPU** | SM utilisation, memory utilisation | Queue depth, pending collectives | ECC errors, Xid errors |
| **CPU** | Utilisation per core | Run queue length, load average | Context switch rate, page faults |
| **Memory** | Used vs total | Page-in rate, swap activity | OOM kills, allocation failures |
| **Disk I/O** | IOPS utilisation, bandwidth | Queue depth, await time | I/O errors, SMART warnings |
| **Network** | Bandwidth utilisation | Queue depth, dropped packets | CRC errors, link flaps |
| **Storage** | Object store request rate | 5xx rate, latency p99 | Object lock failures, 4xx rate |

The bottleneck is the resource that stands out on one or more of the three questions. Fix that resource, then measure again, because a fix often exposes the next limit. A team that stops after the first fix may find the same symptom again, one layer further down the stack.

Expect the bottleneck to move. A system that is limited by storage today may be limited by the network after the storage fix, and that is normal.

### 1.2 The USE method in action

Picture the same page, now with the metrics open on the screen. The workload is slow, and each resource shows its three readings. Here is the check applied to a slow workload. Each resource gets a short line with its three readings and a verdict. The lines are example data, so read them for the pattern, not the exact values.

Notice that the check goes resource by resource, and the reading for each one stays on the page while you decide. That habit makes the verdict easy to defend when someone asks why a resource was ruled out.

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

The disk stands out. Its queue depth is 50, which means 50 requests are waiting at the same time, and that queue is the clue. The utilisation alone looked moderate, so a glance at a single panel would have missed it. The remedy is either faster storage or fewer, larger reads. The whole check took one pass over the metrics, before anyone opened a profiler, and that order of work is the point of the method.

The lesson is about order more than about disks. A team that starts with the GPU panel would have spent its time on the wrong resource, while the table pointed straight at the queue.

### 1.3 The USE method as a Grafana dashboard

Picture an on-call engineer who opens six different tools at midnight to collect the same readings they collected last week. Checking these metrics by hand every time is slow, so put them on one screen. A Grafana dashboard with one panel per metric becomes the on-call engineer's first page. Give each resource its three panels, for utilisation, saturation and errors. Grafana is the open-source dashboard tool, and it can read its data from Prometheus.

The dashboard does not replace the table. It is the same table, drawn as panels, so the same checks happen in the same order.

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

Build this dashboard on a quiet day, not in the middle of an incident. Test each panel against a known workload, so you know the query returns a real number before anyone relies on it. Once it exists, the next on-call engineer can start the USE method from the same page you used.

A dashboard built during an incident tends to have wrong queries, missing labels and panels nobody needed. Build it when nothing is on fire, then keep it ready for the next page.

## 2. The roofline model

### 2.1 The roofline model in detail

Picture a kernel that runs far slower than the GPU's spec sheet promises. You need to know whether the limit is the arithmetic units or the memory system, because the fixes are different. Suppose a kernel runs well below what the GPU can deliver. The roofline model answers that question with one number, the arithmetic intensity, which is how much math a kernel does for each byte it moves. A kernel is a small program that runs on the GPU, and each one has its own intensity.

The model caps performance with two lines, which is why it is called a roofline. One line is the compute peak, the most math per second the chips can do. The other line rises with intensity and is set by memory bandwidth, the most bytes per second the memory can move. Where the two lines meet is the ridge point. A kernel left of the ridge waits on memory, and a kernel right of it waits on arithmetic. Picture a roof with a slope on one side and a flat top on the other, and the kernel sits somewhere under it.

A quick way to place a kernel is to ask whether it moves a lot of data for very little math. Simple element-wise operations, such as adding two tensors, usually do that, and they tend to sit left of the ridge. Large matrix multiplies do the opposite, and they tend to sit right of it.

AI Systems Performance Engineering, chapter 8, shows how to get this picture from a tool. Nsight Compute has a roofline section that plots each kernel's achieved performance against both roofs. It also reports the kernel's arithmetic intensity directly, so you do not have to count it by hand. Nsight Compute is NVIDIA's kernel profiler, and it is the source of the measured numbers that the rest of this section relies on.

Use the roofline as a guide for where to look, not as a promise about speed. The real run includes effects that a roofline leaves out.

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

The ridge point is simply the compute peak divided by the bandwidth. For these H100 figures, that gives about 295 FLOP per byte. For each kernel, compute its intensity, compare it with the ridge, and decide which side it falls on. The fix depends on the answer. A memory-bound kernel needs better access patterns, while a compute-bound kernel needs more arithmetic throughput, so a wrong guess sends the team to the wrong part of the code.

The ridge point is a property of the hardware, not of your code. Every kernel on the same GPU is judged against the same ridge, so you compute it once for each GPU type and keep it in the team notes.

### 2.2 The roofline model in action

Picture a team that wants to speed up the attention step of a transformer, the part of the model that lets each token look at the others. Before they decide on a fix, they need its arithmetic intensity. Take a transformer attention kernel as the example. The block below works through the counts for one set of sizes, so you can see each step.

```text
Attention kernel arithmetic intensity:
- FLOPs: 4 * batch * seq_len * seq_len * hidden_size
  - Example: 4 * 1 * 2048 * 2048 * 4096 = 6.87e10 FLOPs
- Bytes: batch * seq_len * hidden_size * 4 (FP16 weights + activations)
  - Example: 1 * 2048 * 4096 * 4 = 3.36e7 bytes
- Arithmetic intensity: 6.87e10 / 3.36e7 = 2048 FLOP/byte

Comparison to H100 ridge point (295 FLOP/byte):
- Attention intensity (2048) > ridge point (295)
- The kernel is compute-bound
- The optimisation is to increase the compute peak (use FP8; use Tensor Cores)
```

On these counts, the kernel looks compute-bound, so the chapter suggests lower precision or fuller use of Tensor Cores. Tensor Cores are the units inside the GPU that do matrix math very quickly. Check the counts before you act on them. A wrong byte count changes the answer, and the roofline is only as good as the numbers you feed it.

Work through the same steps for each kernel on your shortlist. Keep the numbers in a short table with the bytes, the FLOPs, the intensity and the side of the ridge. A table like that turns a debate about one kernel into a comparison the whole team can check.

### 2.3 The roofline model as a profiling tool

Picture a profile full of kernels, and only one of them is slow. Once you have a roofline, use it as a yardstick for every kernel you profile. Measure what the kernel actually achieves and compare it with the roof. The distance between the two is the room you have to improve. A kernel that is already close to its roof has little left to gain, however much you rewrite it.

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

Be careful where the numbers come from. AI Systems Performance Engineering, chapter 8, notes that the PyTorch profiler's FLOP counts are formula-based estimates for a limited set of operators. They do not come from hardware counters. A formula can miss an operator entirely, and nothing in the printed output tells you that the intensity is off. For measured numbers, run Nsight Compute on the kernel you care about.

When in doubt, measure the kernel once and compare the measured number with the formula. A large gap tells you which numbers to distrust.

Pick the one kernel that matters most to your service, and compute its roofline before you change anything. One careful measurement on the hot kernel is worth more than many guesses about the cold ones.

Keep the roofline plot with the ticket for the change, so the next engineer can see the gap that justified the work.

## 3. The performance decision tree

### 3.1 The decision tree structure

Picture the on-call engineer at a slow hour, with one question to answer before the next page arrives. The USE table asks you to check every resource. When you are under pressure, you want a shorter route to the same answer. The decision tree is that route. Each question has a yes or no answer, and each answer moves you one step closer to a likely cause.

Use the tree for speed and the table for completeness. The tree answers the question you are asked now, and the table makes sure you did not skip a resource that could be the real cause.

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

The percentages in the diamonds, such as 90 percent, are example thresholds. Your team should choose its own values from its own workloads. One more point comes from AI Systems Performance Engineering, chapter 16. If GPU utilisation is lower than you expect, check GPU memory first. When memory is nearly full, the inference engine may be moving cache data to host memory or disk, and the GPUs sit idle while they wait. A rise in copy-engine activity while SM utilisation falls is a sign of that swapping. The copy engine is the part of the GPU that moves data, and it runs alongside the compute units.

Thresholds drift as the workload changes, so write the date next to each one. A threshold set during a quiet quarter can be wrong after a new model ships, and the date tells the next reviewer when to look again.

### 3.2 The decision tree in action

Suppose the training job is slow and the on-call starts at the top of the tree. The walk below follows the steps the way the tree asks them. Each step records a reading and a decision, so anyone who reads the log later can see why the team went where it did.

Keep the walk short when you can. Each extra step is another reading to collect while the job is still slow, and that adds up under pressure.

```text
Decision tree application:
- Step 1: GPU utilisation > 90%? Yes -> continue to step 2; No -> go to step 5
- Step 2: Memory utilisation > 90%? No -> kernel optimisation (Tensor Cores, FP8)
- Step 5: CPU utilisation > 90%? No -> continue to step 8
- Step 8: Network bound? Yes -> check for congestion
- Step 9: Network congestion? Yes -> apply QoS
- Step 10: Network QoS applied -> training is faster
```

The walk ends at the network. The fix was QoS, which is a way of giving important traffic priority over the rest, and the workload improved. The example ends in a network fix rather than a GPU change, which is the kind of result the tree is meant to reach. Without the tree, the first instinct would have been to buy more GPUs.

Notice what the example did not do. It did not add GPUs, and it did not change the model. The tree pointed at the cheapest branch that the readings supported, and that discipline is what keeps the cost down.

### 3.3 The decision tree as a Grafana dashboard

Picture a shift change, where the next on-call engineer has never seen the tree before. The same questions can live on a Grafana dashboard, with one stat panel per question. Each panel shows the current answer, so the on-call engineer does not have to type the queries again. The last panel is a text placeholder for the recommended fix, and someone has to write that logic for it.

Name each panel with its question, not with its metric, so the on-call engineer reads the decision first.

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

Before you trust the tree, walk it once against last month's slow job. If it would have led you to the wrong resource, fix the branch before the next incident. A tree that has never been checked against a real incident is still a guess.

When the tree and the team disagree, write down the reading that caused the disagreement. That reading is usually the thing that needs fixing, either a threshold or a missing branch.

## 4. The cost-vs-latency trade-off

### 4.1 The trade-off model

Picture a support queue full of complaints that responses are slow. More GPUs would help, but they cost money, and a faster kernel might help for free. Suppose users complain that responses are slow. The question is which change buys the most speed for the least spend, and that question needs numbers on both sides before anyone decides.

Users rarely ask for a faster GPU. They ask for a faster answer, and the team has to translate that request into a choice among the fixes.

The trade-off has two sides. You can ask how much latency a GPU purchase saves. You can also ask how much GPU spend a latency fix saves, if users accept slower responses. Write both sides down before anyone signs an order. Latency here means the time a user waits for an answer, and the p99 value is the wait that almost all requests beat.

A useful way to frame the choice is to ask what the users would notice. A faster response is visible to them, while a lower GPU bill is visible only to finance. Both matter, but different people see them, so the write-up should say who gains from each option.

The block below is a worked example with invented options. Copy its structure, not its numbers. The point is the habit of listing each option with its latency change and its cost change, so the comparison is explicit before anyone argues for a favourite.

Read the numbers slowly the first time. Each option changes one thing, so you can see the effect of that one change on latency and cost.

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

Compare the options on latency saved and extra cost, then pick the best return. AI Systems Performance Engineering, chapter 16, adds two cautions. A higher batching wait raises throughput, but setting it too high hurts tail latency, so tune it against your service level. The same chapter notes that newer GPUs can beat a larger fleet of older ones on cost. Return here means the most speed gained for each unit of extra spend.

Write the recommendation in one sentence that names the option and its cost. A reader in a hurry needs only that sentence to act.

### 4.2 The trade-off as a Grafana dashboard

Picture two teams arguing about the same service, each with its own numbers. Put the trade-off on a dashboard, so every team looks at the same numbers. The last panel depends on FinOps data that your team has to export. FinOps is the practice of tracking cloud and hardware spend against the work it buys, so the dashboard is only as good as that feed.

A dashboard only helps when the numbers are trusted. Check the latency panel against a load test before the team uses it to argue for money.

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

Before you approve a GPU purchase, write the latency saved and the cost added in the same table as the cheaper fixes. A purchase that looks large on its own can lose to a kernel change once both sit side by side.

Ask the team to show the numbers for each option, not only for the one it prefers.

## 5. Capacity planning

### 5.1 The capacity planning model

Every quarter, someone asks how many GPUs to order. A guess based on today's count leaves you with idle hardware or a missed service level. The model turns current usage into a forecast, adds a margin for spikes, and produces an order size. The forecast is only a plan, so the model is most useful when you check it against what really happened.

The question also has a human side. Ordering hardware is a commitment that lasts for years, so explain the model in plain terms to the people who sign the order.

The numbers in the block below are example values. Take the growth rate and the spike buffer from your own history, and read each line as a step you can check on its own.

```text
Capacity planning model:
- Current usage: 100 H100 GPUs at 80% utilisation
- Forecast growth: 20% per quarter
- Buffer: 30% for spikes
- Q+1 forecast: 100 * 1.20 * 1.30 = 156 GPUs
- Q+1 order: 156 GPUs (rounded up)
```

The model counts GPUs, not busy GPU hours, so the 80 percent utilisation in the current-usage line of the block does not change the result. If utilisation is low, the count alone will overstate the order. AI Systems Performance Engineering, chapter 16, suggests watching how latency rises as load rises. The load where tail latency climbs sharply shows the practical limit, which is a better basis for the order than the raw count.

A common mistake is to add a buffer on top of a forecast that already includes one. Write down where each margin came from, so the final number has one clear buffer and not two stacked on each other.

### 5.2 The capacity planning dashboard

Put the same arithmetic on a dashboard, so the forecast updates as the metrics change. A forecast that updates by itself is easier to check than one that lives in a spreadsheet nobody opens.

Name the panels with the same labels as the model, so a reviewer can match each panel to its line in the block.

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
      {"title": "Q+1 forecast cost per hour", "type": "stat", "targets": [{"expr": "count(DCGM_FI_DEV_GPU_UTIL_RATIO) * 1.20 * 1.30 * 4.00"}]}
    ]
  }
}
```

The last panel uses an example rate of $4.00 per GPU hour, which matches the $32 per hour for 8 GPUs in Section 4.1. Replace it with the rate in your own contract before the number reaches finance. A rate that is out of date makes a correct forecast look wrong.

Before the next procurement cycle, compare last quarter's forecast with the actual GPU count and write down the error. The written error is the most useful input for the next forecast, because it shows which part of the model drifted.

Share the comparison with finance before the next cycle starts, so the forecast and the budget use the same assumptions.

## 6. Operating the performance engineering stack

### 6.1 The components

Each piece of the stack runs somewhere, stores its data somewhere, and has a target for how fast it should answer. The targets in the table are example values, not measured service levels. Choose your own before you publish them to users. A target nobody has measured is a promise the team cannot keep.

Give each target an owner. A number without an owner tends to drift, while a number with a named owner gets reviewed.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| USE method dashboard | Grafana | Prometheus | Dashboard load p99 < 5 s |
| Roofline analysis | Python script (or notebook) | (no backing store) | (no SLO; offline analysis) |
| Performance decision tree | Grafana | Prometheus | Dashboard load p99 < 5 s |
| Cost-vs-latency trade-off dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| Capacity planning dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |

The roofline analysis is the only component with no backing store, because it runs offline against a profile file. Its speed matters less than the others, so it is the only row with no service level.

Offline analysis is slow to run but cheap to keep. A missing backing store is a design choice here, not a gap in the stack.

### 6.2 IAM and the performance methodology

Picture a data scientist who accidentally edits the platform team's shared dashboard during a busy week. Read access to a shared dashboard is the default, and write access is granted on purpose. The pattern below gives three roles, so readers, exporters and the platform team each get only the rights they need.

| Role | Who | What they can do |
|---|---|---|
| `performance.reader` | The on-call; data scientists | Read the dashboards; query the metrics |
| `performance.writer` | The exporters | Write metrics to Prometheus |
| `performance.admin` | The platform team | Manage the dashboards; manage the methodology |

Documentation and training are part of the discipline. Update the method after every incident, so the next on-call engineer inherits what the last one learned. A method that lives only in one person's head disappears when that person changes teams.

A short written method, kept next to the dashboards, does more good than a long document that nobody opens.

### 6.3 Observability

The stack needs its own alerts, because a broken dashboard during an incident is worse than no dashboard. A dashboard that silently shows stale numbers can send the team in the wrong direction with full confidence. The table lists four alerts. The thresholds are example values, so set them against what your on-call can tolerate.

A broken alert is easy to miss because it fails quietly. Test each of the four alerts once by making its input go bad on purpose, then confirm that the page arrives.

| Metric | Why it matters | Alert |
|---|---|---|
| USE method panel load latency p99 | Dashboard performance | > 5 s |
| Decision tree panel load latency p99 | Dashboard performance | > 5 s |
| Roofline analysis run duration | Offline analysis performance | > 1 hour |
| Capacity planning dashboard accuracy | Procurement accuracy | Error > 20% |

Of the four, the forecast accuracy alert matters most. A forecast that is too high wastes GPUs, and a forecast that is too low puts service levels at risk. Both mistakes cost money, and only the accuracy alert tells you that the model has drifted.

Set this alert to a loose value at first, and tighten it once the forecasts have a few quarters of history behind them.

## 7. How it fails

Picture a performance review where the team asks why the last slow job took so long to fix. Six failure modes come back again and again in performance reviews. Each one below gives the symptom you will recognise, the likely cause and the first fix to try. The numbers are illustrative, so they show the shape of each failure rather than a real measurement.

### 7.1 "The team cannot find the bottleneck"

The workload is slow, and the team runs the USE method with care. No resource stands out, so the team has no clear next step.

The bottleneck may be a mix of resources, such as CPU and GPU together. It may sit below the alert threshold, as a CPU at 70 percent can hide an inefficient kernel. Or the limit may be the code itself, such as slow Python.

Add a check for combinations of resources to the method. Lower the thresholds for the resources you suspect, then profile the kernel and the Python code.

### 7.2 "The roofline model is too theoretical"

The roofline predicts 989 TFLOPS for a kernel, but the measured run reaches 600 TFLOPS. The team reads that as a gap of 39 percent and wonders whether the roofline is wrong.

The roofline describes the kernel alone. The measured time also includes launch overhead, memory allocation and data transfer, and that extra time can account for the gap. Nothing is wrong with the roofline, because it was never meant to include those costs.

Include launch overhead when you compare, time the data transfers separately, and account for the rest in your prediction. A fair comparison measures the same work on both sides.

### 7.3 "The decision tree is too shallow"

The tree says GPU utilisation is high, so the on-call tunes the GPU, and the job is still slow. The team spends a day on the wrong resource.

The tree may be missing a branch for network or storage. Its thresholds may be wrong for your workload. It may also miss a bottleneck that spans more than one resource.

Add the missing branches and tune the thresholds on your own data. Then replay the tree against past incidents to see whether it would have found the cause.

### 7.4 "The cost-vs-latency trade-off is not explicit"

The team buys GPUs without a trade-off analysis, and it tunes kernels without measuring what they cost. The budget is spent before anyone knows what it bought.

The trade-off is not part of the buying or tuning workflow, so the decision rests on instinct. Instinct is not wrong every time, but nobody can check it later.

Put the trade-off dashboard into the procurement review. Ask for the latency and cost comparison before any order is placed.

### 7.5 "The capacity planning forecast is wrong"

The forecast says 156 GPUs, but actual usage is 100 GPUs, so the team over-provisioned by 56. The purchase order is already signed.

The growth rate, the buffer or the history behind the forecast may be wrong. Any one of them is enough to push the result far from the real count.

Check the history first. Add a confidence range to the forecast, and review it every quarter.

### 7.6 "The performance methodology is not followed"

The team tunes ad hoc, and nobody uses the USE method, the roofline or the decision tree. Each engineer has a different favourite fix.

The method is not part of the workflow, nobody has been trained on it, and nobody enforces it. A method that is optional tends to be skipped under pressure.

Train the team, add the method to the workflow, check it in code review, and automate the dashboards that support it.

Pick the failure your team hit most recently. Check whether one of these fixes would have shortened that incident. The answer tells you which of the six patterns to watch for first.

Write the answer into the post-mortem, so the lesson stays with the team after the people who lived through the incident move on.

## 8. Hands-on lab

Picture a new cluster with no performance dashboards yet and a team that wants to learn the method by doing it. This lab ties the chapter together. You build the USE dashboard, compute a roofline, walk the decision tree and produce a capacity forecast on GKE. The lab is untested in this repository, so treat each expected result as a hypothesis you still need to confirm.

### 8.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+) with at least 1 H100 GPU node.
- Helm 3 for installing the observability stack.
- A PyTorch workload for the roofline analysis.

### 8.2 Step 1: deploy the USE method dashboard

Load the dashboard first, so the rest of the lab has something to read. The steps below create the dashboard in the monitoring namespace and import it into Grafana.

```bash
kubectl -n monitoring create configmap use-method-dashboard \
  --from-file=dashboards/use_method.json

curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/use_method_import.json
# expected: the dashboard is available at /d/use/ai-factory-use-method
```

### 8.3 Step 2: run the USE method on a workload

Next, put load on the service and see which panel moves. The load generator below sends 100 concurrent requests for 60 seconds. Watch the GPU panel while the load runs, because that is the panel you expect to move.

```bash
# Apply a synthetic load to the cluster
hey -z 60s -c 100 -m POST -T "application/json" \
  -d '{"inputs":[{"name":"tier_gold","shape":[1],"datatype":"FP32","data":[1.0]}]}' \
  $INFERENCE_URL/v2/models/churn-model/infer

# Open Grafana and look at the USE method dashboard
# expected: the GPU utilisation panel is above 90%; the bottleneck is the GPU
```

If the GPU panel stays low, the bottleneck is somewhere else, so go back to the USE table and work through the other rows. A flat GPU panel under load is a finding in its own right, not a failed step.

### 8.4 Step 3: compute the roofline for a sample kernel

Next, compute the roofline for a small transformer. The script profiles ten forward passes, then estimates intensity from hand-counted FLOPs and bytes. Treat those counts as an estimate, not a measurement, for the reasons given in section 2.3. The script also prints the ridge point, so both numbers appear side by side.

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

Compare the printed intensity with the ridge point. If the counts are right, the script shows which side of the ridge the model sits on. If the two numbers are close, check the counts before you choose a fix.

### 8.5 Step 4: follow the performance decision tree

Open the decision tree dashboard and check that each panel shows a current value. The recommended-fix panel only shows placeholder text until someone writes its logic, so read the other panels to find the bottleneck. Walk the tree by hand from the top, using the same panels, so you see each decision for yourself.

```bash
# Open Grafana and look at the performance decision tree dashboard
# expected: the dashboard shows the current state of every panel
# expected: the recommended fix panel shows the bottleneck
```

### 8.6 Step 5: build the cost-vs-latency trade-off

Query the current cost and the p99 latency from Prometheus. Record both numbers before you compare any options, so the comparison starts from the same baseline for everyone on the team.

```bash
# Compute the current cost and latency
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=sum(rate(kubecost_gpu_cost[1h]))' | jq .
curl -s 'http://prometheus.monitoring:9090/api/v1/query?query=histogram_quantile(0.99,%20rate(inference_request_duration_seconds_bucket[5m]))' | jq .
# expected: the current cost per hour; the current p99 latency
```

### 8.7 Step 6: produce the capacity planning forecast

Last, query the GPU count and the forecast. The forecast command uses the example growth and buffer from section 5, so change those values to match your own history. Write down the answer before you compare it with the real count later.

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

Five questions show whether the stack is ready for the page. Answer them from the dashboards you just built. The chapter treats five seconds per answer as its target, which is an example value and not a standard. Answers that take longer suggest the stack is not yet ready for on-call use.

1. What is the current GPU utilisation per the USE method?
2. What is the current roofline gap per the kernel profile?
3. What is the current bottleneck per the decision tree?
4. What is the current cost-vs-latency trade-off per the dashboard?
5. What is the current Q+1 GPU forecast per the capacity planning model?

Run it on a quiet day first, and record the answers so you can compare them later. A record from a quiet day is the baseline that makes a slow day easy to read.

## Exercises

1. Add a per-team USE dashboard. Build one USE dashboard per team, with the metrics filtered by a team label. *Solution sketch:* a Grafana dashboard template with a team filter, so each team sees its own USE view.
2. Add a roofline analysis script. Build a Python script that reads a PyTorch profile and computes the roofline for each kernel. *Solution sketch:* the script reads the profile, computes the intensity, compares it with the ridge point and prints the bottleneck.
3. Add a decision tree integration test. Replay past incidents through the tree and check that it reaches the recorded root cause. *Solution sketch:* a Python test that takes an incident, runs the tree and asserts that the bottleneck matches the root cause.
4. Add a cost-vs-latency trade-off dashboard. Build a Grafana dashboard that shows the trade-off for each team. *Solution sketch:* one page with the current cost, the current latency, the options and the recommended fix.
5. Add a capacity planning script. Build a Python script that reads the current pool utilisation and prints the next-quarter forecast. *Solution sketch:* the script reads the metrics, applies the forecast model and prints the GPU count and cost.
6. Add a performance engineering playbook. Write a short playbook that covers the USE method, the roofline, the decision tree, the trade-off and capacity planning. *Solution sketch:* a Markdown document the team can follow during an incident.

Start with exercise 3 if you have past incidents on hand. A decision tree that has never been tested against real incidents is still a guess, and you will not know its gaps until you try it. Pick one exercise you can finish this month, and write down what it taught you.

## Checkpoint questions

<details><summary>1. You are paged for a slow workload. Disk I/O shows 80 percent IOPS use, 60 percent bandwidth and a queue depth of 50, and every other resource looks fine. What is the bottleneck and the remedy?</summary>
The disk is the bottleneck. Its saturation is high, because 50 requests are waiting at the same time, and that queue is the clue. The remedy is either faster storage or fewer, larger reads. The whole check took one pass over the metrics, before anyone opened a profiler.
</details>

<details><summary>2. A training job that used to finish overnight now runs past the morning, the GPU graphs look busy, and a manager suggests adding nodes. What do you say?</summary>
Busy time can mislead, because a GPU can look fully busy while it moves redundant data. Measure goodput, the useful work actually delivered, and run the USE method before buying capacity. Adding nodes without finding the bottleneck is guessing and may pay for capacity the workload never uses.
</details>

<details><summary>3. The decision tree says GPU utilisation is high, so the on-call tunes the GPU, and the job is still slow. What went wrong?</summary>
The tree may be missing a branch for network or storage, its thresholds may be wrong for your workload, or the bottleneck may span more than one resource. Add the missing branches and tune the thresholds on your own data. Then replay the tree against past incidents to see whether it would have found the cause.
</details>

<details><summary>4. Inference GPU utilisation is lower than expected, GPU memory is nearly full, and copy-engine activity rises while SM utilisation falls. What is likely happening?</summary>
The inference engine may be moving cache data to host memory or disk, and the GPUs sit idle while they wait. That is why you check GPU memory first when utilisation is low. The fix is to relieve memory pressure so the cache stays on the GPU.
</details>

<details><summary>5. The roofline predicts 989 TFLOPS for a kernel, but the measured run reaches 600 TFLOPS. How big is the gap and what explains it?</summary>
The gap is 989 minus 600, which is 389 TFLOPS, about 39 percent. The roofline describes the kernel alone. The measured time also includes launch overhead, memory allocation and data transfer. Include launch overhead in the comparison and time the data transfers separately.
</details>

<details><summary>6. The team runs the USE method and no resource stands out. Where can the bottleneck still hide?</summary>
It may be a mix of resources, such as CPU and GPU together. It may sit below the alert threshold, as a CPU at 70 percent can hide an inefficient kernel. Or the limit may be the code itself, such as slow Python. Add a check for combinations, lower thresholds for suspects, and profile the kernel and the Python code.
</details>

<details><summary>7. Why does the ridge point decide whether a kernel is memory-bound or compute-bound?</summary>
The ridge point is the compute peak divided by the memory bandwidth, measured in FLOP per byte. A kernel with lower arithmetic intensity is left of it and waits on memory. A kernel with higher intensity is right of it and waits on arithmetic. The fix differs on each side, so compute the intensity first.
</details>

<details><summary>8. Why should you not trust the PyTorch profiler's FLOP counts for a roofline?</summary>
They are formula-based estimates for a limited set of operators, not hardware counters. A roofline is only as good as the numbers fed into it. For measured values, run Nsight Compute on the kernel you care about.
</details>

<details><summary>9. Why does the USE method tell you to measure again after fixing a resource?</summary>
A fix often exposes the next limit. Once the worst resource is no longer the bottleneck, another resource becomes the one that stands out. Measuring again shows what limits the workload now, so you do not keep tuning something that no longer matters.
</details>

<details><summary>10. Why does the 80 percent utilisation in the capacity model not change the forecast?</summary>
The model counts GPUs, not busy GPU hours, so the order is 100 times the growth times the buffer regardless of utilisation. If utilisation is low, the count alone will overstate the order. A better basis is the load where tail latency climbs sharply, which shows the practical limit.
</details>

<details><summary>11. Why does raising the batching wait help throughput and yet risk your service level?</summary>
A longer wait lets more requests join a batch, which raises throughput. If the wait is too high, every request sits longer before it runs, which hurts tail latency. Tune the wait against your service level, not against throughput alone.
</details>

<details><summary>12. In the chapter's example, Option A doubles the GPUs, Option B optimises the kernel. When would you still pick A, and what do you give up?</summary>
Option A cuts p99 from 500 to 250 ms but adds $32 per hour. Option B cuts it to 350 ms at no extra cost, so B has the best return. Pick A only if the service level needs the full 250 ms and B cannot reach it. You give up the extra $32 per hour. The figures are invented for illustration.
</details>

<details><summary>13. Should you order 156 GPUs with the 30 percent buffer, or fewer, and what is the risk each way?</summary>
The buffer covers spikes. A forecast that is too high wastes GPUs, and one that is too low puts service levels at risk. Rather than trust the count, watch where tail latency climbs as load rises and use that practical limit as the basis. The growth and buffer values are examples.
</details>

<details><summary>14. When would you use the decision tree and when the full USE table, and what do you give up with each?</summary>
Under pressure, the tree is the shorter route, with yes or no questions that move you toward a likely cause. You give up completeness, because it can miss a branch. The USE table checks every resource and misses nothing it lists, but it takes longer. Walk the tree against last month's slow job to test it.
</details>

<details><summary>15. Should you count a kernel's arithmetic intensity by hand or take it from Nsight Compute, and what do you give up?</summary>
Nsight Compute reports the arithmetic intensity directly and plots each kernel against both roofs, so you do not count by hand. A wrong byte count changes the answer. You give up the quick estimate and need a profiling run on the kernel.
</details>

<details><summary>16. With the H100 figures of 989 TFLOPS and 3,350 GB/s, what is the ridge point, and what performance does a kernel at 100 FLOP per byte reach?</summary>
The ridge is 989 TFLOPS divided by 3,350 GB/s, about 295 FLOP per byte. At 100 FLOP per byte the kernel is left of the ridge, so it is memory-bound. Performance is bandwidth times intensity, 3,350 GB/s times 100, which is 335 TFLOPS.
</details>

<details><summary>17. Use the capacity model with 100 GPUs, 20 percent growth and a 30 percent buffer. What is the Q+1 order and hourly cost at $4.00 per GPU hour?</summary>
The forecast is 100 times 1.20 times 1.30, which is 156 GPUs. At $4.00 per GPU hour the cost is 156 times 4.00, which is $624 per hour. The $4.00 is an example rate, so replace it with the rate in your contract.
</details>

<details><summary>18. The attention example has 6.87e10 FLOPs and 3.36e7 bytes. What is the intensity and which side of the 295 ridge is it?</summary>
Divide 6.87e10 by 3.36e7, which gives about 2,048 FLOP per byte. That is far above 295, so the kernel is compute-bound. The suggested fixes are lower precision such as FP8 and fuller use of Tensor Cores. Check the counts first, because a wrong byte count changes the answer.
</details>

<details><summary>19. Following the decision tree, what do you check first, second and third when GPU utilisation is not above 90 percent?</summary>
The first question is whether GPU utilisation is above 90 percent, and the answer is no. Second ask whether CPU utilisation is above 90 percent. Third, if it is not, ask whether the workload is network bound, then storage. Each answer moves you one step closer to a likely cause.
</details>

<details><summary>20. The forecast says 156 GPUs but actual usage is 100, so the team over-provisioned by 56. What do you check, in order?</summary>
Check the history behind the forecast first. Then check the growth rate and the buffer. Add a confidence range to the forecast and review it every quarter, writing down the error against the real GPU count.
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
