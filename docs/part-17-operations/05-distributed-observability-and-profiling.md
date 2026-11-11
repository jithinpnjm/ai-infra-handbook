---
id: "c17-05"
title: "17.5 Distributed observability and profiling"
sidebar_label: "17.5 Distributed observability and profiling"
sidebar_position: 5
description: "Distributed observability and profiling for AI workloads: PyTorch Profiler, Nsight Systems, Nsight Compute, NVIDIA Nsys, distributed trace correlation, kernel-level profiling, NCCL collective profiling, and the integration with the on-call dashboard."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 17.5 Distributed observability and profiling

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Primary sources | NVIDIA Zero-to-Hero Volume 16 (`chapter-06-distributed-observability.md`, `chapter-07-profiling.md`); NVIDIA Zero-to-Hero Volume 7 (`chapter-02-distributed-tracing-and-profiling.md`); *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chapters 13, 14, 15) |
| Cross-references | Chapter 10.20 (Profiling tools); Chapter 17.1 (Observability foundations); Chapter 17.3 (Logging with Loki and tracing with OpenTelemetry); Chapter 17.4 (DCGM exporter) |
| Coverage file | `planning/coverage/chapters/17-05.md` |
| Claim & number ledger | `planning/ledgers/17-05.md` |

## Why this matters for AI infrastructure

Suppose your traces show that an inference request spent most of its time in the model call. The trace stops there. It cannot tell you which GPU kernel caused the delay. Chapter 17.3 introduced the three pillars and the tools that collect traces. This chapter covers the profiling tools that turn a trace into a specific cause.

The same gap exists for training. Without NCCL profiling, you know a multi-node job is slow, but you cannot see which collective holds it back. A team that has traces and no profiles knows that something is slow, not why.

Profiling answers the question of why. In a performance incident, you look at metrics first, from Chapter 17.2. Next you look at traces, from Chapter 17.3. The profile comes last, and it names the GPU kernel or NCCL collective that is the bottleneck.

```text
Why profiling is on the critical path (background reading: NVIDIA Zero-to-Hero volume 16; AI Systems Performance Engineering; the figures below are examples, not quotations):
- An AI workload spends 60-80% of its time in GPU kernels. The on-call cannot
  optimise a kernel without a profile. The PyTorch Profiler, Nsight Systems,
  and Nsight Compute are what turn the trace into a kernel-level view.
- A multi-node training job spends 20-40% of its time in NCCL collectives.
  The on-call cannot optimise the collectives without NCCL profiling. The
  NCCL profiler is what turns the trace into a collective-level view.
- A profile without context is just numbers. A profile correlated with the
  trace is a story. The on-call follows the story from the trace to the
  profile to the root cause.
```

Profiling is not only a data-science task. Three realities make it a platform-team responsibility.

1. The tools are GPU-specific. PyTorch Profiler, Nsight Systems, Nsight Compute, and the NCCL Profiler are NVIDIA-specific tools. The platform team owns their deployment and integration.
2. The profile is large. In the example values for this chapter, one training step produces 10 GB of profile data. The platform team therefore stores profiles in object storage and owns the retention policy.
3. The profile must match the trace. The on-call needs the trace to find the slow operation and the profile to find the slow kernel. The platform team owns the link between the two.

**A workload without a profile is one the on-call cannot optimize.** Before an incident, confirm that each profiled workload stores its profiles in object storage and links them to traces.

## Prerequisites and outcomes

### Prerequisites

- Chapter 10.20 (Profiling tools) for the GPU profiling concepts.
- Chapter 17.1 (Observability foundations) for the three pillars.
- Chapter 17.3 (Logging with Loki and tracing with OpenTelemetry) for the trace integration.
- Chapter 17.4 (DCGM exporter) for the GPU metrics.

### Outcomes

After completing this chapter you will be able to:

1. Deploy PyTorch Profiler, Nsight Systems, and Nsight Compute on the cluster, then check that their profiles reach object storage.
2. Turn on NCCL profiling for a multi-node training job, then confirm that the collective timings appear in the traces.
3. Link each profile to its trace, so that a click on the trace opens the matching profile.
4. Read a profile and name the slow kernel, the slow collective, or the slow data loader.
5. Build a Grafana dashboard that surfaces the slowest kernels and collectives.
6. Run the profiling stack on GKE with SLOs, monitoring, and a runbook.

---

## 1. The profiling stack

### 1.1 The four profilers

You have four profilers to choose from when a job is slow. NVIDIA Zero-to-Hero Volume 16 chapter 7 and Volume 7 chapter 2 walk through all four.

| Profiler | What it profiles | When to use |
|---|---|---|
| **PyTorch Profiler** | PyTorch operations (forward, backward, optimiser) | PyTorch workloads; high-level view |
| **Nsight Systems** | CUDA kernels, memory transfers, GPU utilisation | Detailed kernel-level view |
| **Nsight Compute** | Single kernel performance (occupancy, register pressure) | Deep dive on a single kernel |
| **NCCL Profiler** | NCCL collectives (all-reduce, all-gather, reduce-scatter) | Multi-node training |

Each profiler answers a different question, so start broad and go deeper only when the broad view points at a cause. PyTorch Profiler shows which operations are slow. Nsight Systems shows the timeline, including the gaps where the GPU sits idle. Nsight Compute explains why one kernel is slow. The NCCL Profiler shows which collective holds up a multi-node job.

### 1.2 The profiling pipeline

```mermaid
flowchart LR
    W[Workload<br/>PyTorch + CUDA + NCCL]
    PT[PyTorch Profiler<br/>on each rank]
    NS[Nsight Systems<br/>on GPU node]
    NC[NCCL Profiler<br/>on each rank]
    S[Object storage<br/>profile repository]
    T[Tempo<br/>trace backend]
    G[Grafana]

    W --> PT
    W --> NS
    W --> NC
    PT --> S
    NS --> S
    NC --> S
    NC --> T
    PT --> T
    S --> G
    T --> G
```

Each profiler runs next to the workload and writes its output to object storage. PyTorch Profiler and the NCCL Profiler also send trace data to Tempo, so Grafana can show profiles and traces side by side. When an incident starts, begin with the trace and follow it to the matching profile.

### 1.3 The profile format

The profile is a structured trace in the Chrome Trace Event Format. You can open it in `chrome://tracing`, the PyTorch Profiler viewer, the Nsight Systems GUI, or the Grafana trace UI.

```text
{
  "traceEvents": [
    {"name": "aten::add", "cat": "kernel", "ph": "B", "ts": 1000, "pid": 0, "tid": 0},
    {"name": "aten::add", "cat": "kernel", "ph": "E", "ts": 1100, "pid": 0, "tid": 0},
    {"name": "nccl::all_reduce", "cat": "collective", "ph": "B", "ts": 2000, "pid": 0, "tid": 0},
    {"name": "nccl::all_reduce", "cat": "collective", "ph": "E", "ts": 2200, "pid": 0, "tid": 0}
  ]
}
```

The format is plain JSON, so a script can search it. An on-call engineer can list the slowest kernel events or the slowest collective events, then jump to the operation that takes the most time. Before you write a custom parser, open one profile in a viewer and learn its layout.

---

## 2. PyTorch Profiler

### 2.1 The PyTorch Profiler basics

When a training step slows down, PyTorch Profiler is the first tool to reach for. It ships inside PyTorch, so you add it to the training code without a separate install. You wrap the training steps in `torch.profiler.profile`. The profiler records CPU activity and, when a GPU is present, CUDA activity.

```python
# code/part17/snippets/pytorch_profiler.py
"""PyTorch profiler with a schedule. Runs on CPU too (CUDA activity is skipped when no GPU is present)."""
import torch
from torch.profiler import profile, ProfilerActivity, record_function

acts = [ProfilerActivity.CPU] + ([ProfilerActivity.CUDA] if torch.cuda.is_available() else [])
model = torch.nn.Linear(64, 64)

with profile(
    activities=acts,
    schedule=torch.profiler.schedule(wait=1, warmup=1, active=3, repeat=1),
    on_trace_ready=torch.profiler.tensorboard_trace_handler("./profiles"),
    record_shapes=True,
    profile_memory=True,
    with_stack=True,
) as prof:
    for step in range(5):
        with record_function(f"step_{step}"):
            model(torch.randn(32, 64)).sum().backward()
        prof.step()
```

The schedule skips the first step, warms up for one step, and then records three active steps. That keeps the profile small, which matters because profiles grow quickly. The handler writes the trace into `./profiles`. A separate job copies that trace to object storage, as Section 6 describes.

### 2.2 The PyTorch Profiler integration with the trace

A slow request shows up in a trace, but the trace does not show which GPU kernels ran. Linking the profile to the trace closes that gap. The export function reads the trace ID from the active span and uses it in the file name.

```python
# code/part17/snippets/pytorch_profiler_otel.py
"""Name the exported profile after the current trace id, so the profile can be found from a trace (see correlate_profile.py)."""
import os
import torch
from torch.profiler import profile, ProfilerActivity, record_function
from opentelemetry import trace

def export(prof):
    tid = format(trace.get_current_span().get_span_context().trace_id, "032x")
    os.makedirs("./profiles", exist_ok=True)
    prof.export_chrome_trace(f"./profiles/trace-{tid}.json")

model = torch.nn.Linear(64, 64)
with profile(activities=[ProfilerActivity.CPU], on_trace_ready=export) as prof:
    for step in range(5):
        with record_function(f"step_{step}"):
            model(torch.randn(32, 64)).sum().backward()
        prof.step()
```

The profile file name now carries the trace ID. Any tool that can search the profile folder can find the profile for a given trace. Test the link once in a staging run before you rely on it during an incident.

### 2.3 The PyTorch Profiler dashboard

The dashboard turns a raw profile into three views: kernel time, memory use, and GPU utilization per step. The queries below assume that an exporter publishes these series. This chapter does not set up that exporter, so check that the series exist before you build the panels.

```promql
# The total CUDA time per kernel
sum by (kernel) (rate(pytorch_profiler_cuda_time_seconds[5m]))

# The total memory usage per operation
sum by (operation) (pytorch_profiler_memory_bytes)

# The GPU utilisation per step
avg by (step) (DCGM_FI_DEV_GPU_UTIL)
```

> **dcgm-exporter 4.9.0 version note.** dcgm-exporter 4.9.0 (2026-11-06) renamed many default metrics and changed some units. For example `DCGM_FI_DEV_GPU_UTIL` (percent) became `DCGM_FI_DEV_GPU_UTIL_RATIO` (0 to 1), and `DCGM_FI_DEV_FB_USED` (MiB) became `DCGM_FI_DEV_FB_USED_BYTES`. The metric names in this chapter are the 4.8.x names. On a 4.9.0 exporter use the [full mapping in 17.4](04-dcgm-exporter-and-interpreting-gpu-metrics.md#14-what-dcgm-exporter-490-renamed), and change thresholds together with the unit.

Start with the kernel-time query when a step is slow, because it names the first kernel to investigate. If a panel is empty, confirm that the exporter runs before you blame the workload.

---

## 3. Nsight Systems

### 3.1 The Nsight Systems basics

Your GPUs look busy on one dashboard, yet the job runs slower than it should. Nsight Systems puts CPU threads, GPU kernels, memory transfers, and API calls on one timeline. You run it with `nsys`, and it writes a `.nsys-rep` file that you open in the GUI.

```bash
# Run Nsight Systems on a workload
nsys profile \
  --output=/profiles/workload.nsys-rep \
  --force-overwrite=true \
  --trace=cuda,nvtx,osrt \
  python train.py
```

The `--trace` flag picks the event types to record: CUDA calls, NVTX ranges, and OS runtime events.

### 3.2 The Nsight Systems integration with the trace

Nsight Systems shows named NVTX ranges on its timeline. If a range name carries the trace ID, you can match that part of the timeline to one request.

```python
# code/part17/snippets/nsight_nvtx_otel.py
import torch
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("training-step"):
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, "032x")
    torch.cuda.nvtx.range_push(f"step-{trace_id}")
    # ... training step ...
    torch.cuda.nvtx.range_pop()
```

Nothing adds the trace ID to the range name for you. You choose that convention. AI Systems Performance Engineering, chapter 13, notes that NVTX markers have very low overhead when no profiler is attached, so you can leave them in production code.

### 3.3 The Nsight Systems dashboard

When you open a slow step, the panels answer the first questions. Are the kernels back to back? Are transfers blocking the GPU?

```text
Nsight Systems dashboard panels:
- Kernel timeline: the CUDA kernels per stream
- Memory transfer timeline: the HBM-DRAM transfers
- GPU utilisation: the DCGM_FI_DEV_GPU_UTIL metric
- API call timeline: the CUDA API calls
- NVTX range timeline: the application's logical ranges
```

AI Systems Performance Engineering, chapter 13, treats large gaps in the timeline, which it calls bubbles, as a problem. Small synchronization gaps are expected. Check that host-side data loading overlaps with GPU compute, as the book recommends.

Before you tune a kernel, confirm that the timeline shows the GPU is busy in the first place.

---

## 4. Nsight Compute

### 4.1 The Nsight Compute basics

Nsight Systems has shown you that one matrix multiply kernel takes most of the step. Now you need to know why. Nsight Compute profiles one kernel in much more detail. It reports occupancy, register pressure, memory access patterns, and instruction-level metrics. You run it with `ncu` and open the `.ncu-rep` file in its GUI.

```bash
# Run Nsight Compute on a single kernel
ncu \
  --target-processes all \
  --kernel-name regex:gemm_kernel \
  --launch-skip 5 \
  --launch-count 1 \
  --metrics sm__cycles_active.avg.pct_of_peak_sustained_elapsed \
  python train.py
```

The flags select the kernel by name, skip the first five launches so the warm-up is excluded, and collect metrics for one launch. Wrap the workload's command in `ncu`, then upload the report to object storage with the other profiles.

Live services need a gentler approach. AI Systems Performance Engineering, chapter 16, points to Nsight Compute's program counter sampling for live inference servers. Sampling finds the hot instructions without full instrumentation, so its overhead stays low. Start with sampling, and switch to full tracing only when a sample points to one kernel or phase.

### 4.2 The Nsight Compute metrics

| Metric | What it measures | Why it matters |
|---|---|---|
| `sm__cycles_active.avg.pct_of_peak_sustained_elapsed` | SM utilisation | The kernel is using the SMs |
| `sm__warps_active.avg.pct_of_peak_sustained_active` | Warp utilisation | The kernel is using the warps |
| `gpc__cycles_elapsed.avg` | Cycles elapsed | The kernel is taking time |
| `smsp__inst_executed.sum` | Instructions executed | The kernel is doing work |
| `l1tex__t_bytes.sum` | L1 texture bytes | The kernel is reading memory |
| `dram__bytes.sum` | DRAM bytes | The kernel is reading DRAM |
| `launch__registers_per_thread` | Registers per thread | The kernel is using registers |
| `launch__shared_mem_per_block_static` | Shared memory per block | The kernel is using shared memory |
| `launch__waves_per_multiprocessor` | Waves per SM | The kernel's occupancy |

Metric names change between Nsight Compute releases. AI Systems Performance Engineering, chapter 13, advises that when a metric is not found, you should look up its current name in the UI. The metrics above tell you why a kernel is slow, such as low SM utilization, high register pressure, or low occupancy. Each finding points to a different fix, such as rewriting the kernel, reducing register use, or changing how it uses shared memory.

### 4.3 The Nsight Compute integration with Nsight Systems

Nsight Systems finds the slow kernel, and Nsight Compute explains it. The chain runs from the trace to the high-level profile, then to the kernel profile, and finally to the root cause.

```text
Nsight Systems → Nsight Compute integration:
- Nsight Systems shows the kernel timelines
- The on-call clicks on a slow kernel
- The dashboard opens the Nsight Compute profile for that kernel
- The Nsight Compute profile shows the kernel's metrics
```

This pattern moves you from a broad profile to a specific fix. The chapter assumes your dashboard can link a slow kernel to its Nsight Compute report. If your dashboard cannot do that, find the report by hand in the profile folder.

Keep each kernel's name and launch settings with its report, so you can repeat the same capture later.

---

## 5. NCCL Profiler

### 5.1 The NCCL Profiler basics

Picture a multi-node job that runs at half speed while every GPU waits for the others. NCCL carries out the collectives that move data between GPUs, such as all-reduce, all-gather, reduce-scatter, and broadcast. The NCCL Profiler is invoked with `NCCL_DEBUG=INFO` and `NCCL_DEBUG_SUBSYS=ALL`. The profile is emitted to stderr.

```bash
# Run NCCL Profiler
NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=ALL python train.py 2> nccl_profile.log
```

Run the job with those variables set, and send stderr to a file. Then copy that file to object storage with the other profiles.

### 5.2 The NCCL profile format

The output is a plain-text log of collective events. Each event carries its size, algorithm, protocol, and time. An on-call engineer can parse the log to find the slow collective, and the algorithm field shows which algorithm each one used.

```text
[NCCL DEBUG] Channel 0: 0[0] -> 1[0] [send] via P2P/IPC
[NCCL DEBUG] Channel 0: 0[0] -> 1[0] [receive] via P2P/IPC
[NCCL DEBUG] Channel 0: all-reduce algorithm: Ring
[NCCL DEBUG] Channel 0: all-reduce protocol: Simple
[NCCL DEBUG] Channel 0: all-reduce size: 1073741824 bytes
[NCCL DEBUG] Channel 0: all-reduce time: 12.345 ms
```

### 5.3 The NCCL profile integration with the trace

A slow collective is hard to place on a trace unless it has its own span. The example below wraps one all-reduce in a span and turns on NCCL logging for initialization and collectives. It needs GPUs and `torchrun`, so run it on a GPU node rather than a laptop.

```python
# code/part17/snippets/nccl_profile_otel.py
"""Wrap a collective in a span, with NCCL debug logging on. Requires GPUs and torchrun: syntax-checked only."""
import os
os.environ["NCCL_DEBUG"] = "INFO"
os.environ["NCCL_DEBUG_SUBSYS"] = "INIT,COLL"      # ALL is extremely verbose; INIT and COLL are enough for most hangs

import torch
import torch.distributed as dist
from opentelemetry import trace

dist.init_process_group(backend="nccl")
tracer = trace.get_tracer(__name__)
tensor = torch.ones(1024, device="cuda")
with tracer.start_as_current_span("all-reduce"):
    dist.all_reduce(tensor)
```

The code comment explains why the example uses INIT and COLL instead of ALL. You correlate the NCCL profile with the trace by putting the trace ID into the NCCL events.

### 5.4 The NCCL profile dashboard

A single average all-reduce time hides the difference between small and large messages. The dashboard therefore splits the timings by size, operation, and algorithm. The queries below compute the average time per size, the p99 time per algorithm, and the collective bandwidth.

```promql
# The average all-reduce time per size
sum by (size_bucket) (rate(nccl_all_reduce_duration_seconds_sum[5m])) / sum by (size_bucket) (rate(nccl_all_reduce_duration_seconds_count[5m]))

# The p99 all-reduce time per algorithm
histogram_quantile(0.99, sum by (algorithm, le) (rate(nccl_all_reduce_duration_seconds_bucket[5m])))

# The collective bandwidth
sum by (size_bucket) (rate(nccl_all_reduce_bytes[5m])) / sum by (size_bucket) (rate(nccl_all_reduce_duration_seconds_sum[5m]))
```

The queries assume that an exporter publishes the NCCL series, and this chapter does not set one up. Confirm that the series exist first. Then start with the p99 query per algorithm, because a slow tail shows up there before it shows in the average.

---

## 6. Operating the profiling stack on GKE

### 6.1 The components

Suppose the profiling stack goes live on Monday and every workload starts writing profiles. Without a clear owner for each component, nobody knows which one to check first. The table lists each component, where it runs, what stores its data, and the target the chapter proposes for it.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| PyTorch Profiler | In the workload's process | Object storage for profile | Profile write latency p99 < 30 s |
| Nsight Systems | In the workload's process (sidecar or shared) | Object storage for `.nsys-rep` | Profile write latency p99 < 30 s |
| Nsight Compute | In the workload's process | Object storage for `.ncu-rep` | Profile write latency p99 < 30 s |
| NCCL Profiler | In the workload's process | Object storage for log | Log write latency p99 < 30 s |
| Profile repository | Object storage | (the profiles themselves) | Profile load latency p99 < 5 s |
| Trace backend (Tempo) | Kubernetes Deployment | Object storage for traces | Trace query latency p99 < 5 s |

The latency targets in the table are example values, not figures from a source. Your team should choose its own targets, based on what it can support, and write them down.

### 6.2 IAM and the profile cardinality

Profiles reveal how your code runs, so access to them needs limits. Readers can view profiles, writers can only upload them, and the platform team alone manages retention and dashboards.

| Role | Who | What they can do |
|---|---|---|
| `profiler.reader` | The on-call; data scientists | Read profiles from object storage; view profiles in Grafana |
| `profiler.writer` | The workload's process | Write profiles to object storage |
| `profiler.admin` | The platform team | Manage the profile retention; manage the profile dashboard |

The profile cardinality is the profile's storage cost. Production Kubernetes, chapter 9, uses cardinality for metric labels, and it warns that overusing labels can make the resource use of your Prometheus servers untenable. Keep the storage question separate from that label question when you plan the budget.

In the example values of this chapter, one training step produces 10 GB of profile data. A 100-step run therefore produces 1 TB. The example retention policy keeps profiles for 7 days before archiving them to cold storage. Its deletion rule is unclear, so set the periods that fit your storage budget.

### 6.3 Observability

| Metric | Why it matters | Alert |
|---|---|---|
| Profile write latency p99 | Hot path for profile upload | > 30 s |
| Profile repository size | Storage budget | > 80% for 1 day |
| Trace-to-profile correlation rate | Catches broken correlation | < 100% for 1 hour |
| NVTX range coverage | Catches missing correlation | < 100% for 1 hour |

Treat the thresholds in this table as starting points, not standards. AI Systems Performance Engineering, chapter 16, notes that production teams cannot run heavy profilers all the time. They watch lightweight metrics such as SM utilization and tail latency instead.

The trace-to-profile correlation rate matters most. A broken correlation means the on-call cannot find the profile for a trace, so they must debug without it.

Before you wire these alerts to a pager, agree with the team on which thresholds you will act on.

---

## 7. How it fails

When the profiling stack breaks, the on-call usually meets one of six failures. Each one below gives the symptom, the likely cause, and the fix.

### 7.1 "The profile is too large"

Symptom: The profile write fails. The bucket fills up, and the team runs out of storage.

Diagnosis: The profile is too verbose. It captures every CUDA kernel, so each step can produce a very large file.

Fix: Reduce the verbosity and capture only the slow operations. Use `torch.profiler.schedule` to skip warm-up steps.

### 7.2 "The profile is not correlated with the trace"

Symptom: The on-call clicks a trace in Grafana, but the dashboard shows no profile for it.

Diagnosis: The NVTX ranges or the profile file name do not carry the trace ID, so the link breaks.

Fix: Check that the NVTX ranges and file names include the trace ID. Then add an integration test that fails when the correlation breaks.

### 7.3 "The Nsight Systems profiler adds too much overhead"

Symptom: The workload slows down sharply when the profiler is on.

Diagnosis: The profiler captures every kernel, so its overhead grows with the number of kernels.

Fix: Use `nsys profile --trace=cuda` to capture only CUDA kernels, and use the `--sample` flag to reduce the sampling rate.

### 7.4 "The NCCL Profiler log is too large"

Symptom: The NCCL log grows large, is hard to query, and can fill the disk.

Diagnosis: The level is set to INFO, so every collective is logged in full.

Fix: Use `NCCL_DEBUG=WARN` to reduce the noise, and set `NCCL_DEBUG_SUBSYS=COLL` to log only collective events. AI Systems Performance Engineering, chapter 16, makes the same suggestion. WARN also surfaces errors that would otherwise stay silent. The same chapter warns that NCCL logs are very verbose, so keep the detailed levels for short runs.

### 7.5 "The Nsight Compute profile is missing the kernel"

Symptom: You run `ncu` on the workload, but the report does not include the kernel you care about.

Diagnosis: The `--kernel-name` value does not match the kernel's name, or the kernel is inlined or optimised away.

Fix: Check the kernel name. Use `--launch-skip` to skip warm-up launches, and use `--launch-count` to limit how many launches get profiled.

### 7.6 "The profile is stale"

Symptom: You open a profile from yesterday, but the workload has changed since then.

Diagnosis: Nobody regenerated the profile after the last update, so it describes an older version.

Fix: Regenerate the profile on every workload update. Make that a CI step, and tag each profile with the workload's commit hash.

When a profile misleads you, check its age and its trace link before you trust the numbers.

---

## 8. Hands-on lab

Suppose you have just built the profiling stack and want proof that it works. This lab sets up the stack on GKE, runs PyTorch Profiler on a training job, and checks that the profile links to its trace. The lab is untested in this repository.

### 8.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+) with at least 1 H100 GPU node.
- Helm 3 for installing the profiling stack.
- A PyTorch training workload (a small model like ResNet-50).

### 8.2 Step 1: install the profile repository

```bash
# Create the profile bucket
gsutil mb -l us-central1 gs://${PROJECT_ID}-profiles
# expected: the bucket is created
```

### 8.3 Step 2: deploy a training workload with PyTorch Profiler

```yaml
# code/part17/profiling_workload.yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata:
  name: profiling-demo
spec:
  tasks:
    - replicas: 1
      template:
        spec:
          containers:
            - name: train
              image: my-train:v1
              command: [python, train_with_profiler.py]
              args: ["--profile-dir", "/profiles"]
              volumeMounts:
                - name: profiles
                  mountPath: /profiles
          volumes:
            - name: profiles
              persistentVolumeClaim:
                claimName: profiles-pvc
```

### 8.4 Step 3: run the workload and capture the profile

```bash
kubectl apply -f code/part17/profiling_workload.yaml
# expected: the workload runs; the profile is captured to /profiles
```

### 8.5 Step 4: upload the profile to object storage

```bash
gsutil cp /profiles/*.json gs://${PROJECT_ID}-profiles/
# expected: the profile is uploaded to the bucket
```

### 8.6 Step 5: query the profile in Grafana

```bash
# Add the profile as a Grafana data source
curl -X POST http://admin:admin@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Profiles",
    "type": "grafana-pyroscope-datasource",
    "url": "http://pyroscope.monitoring:4040"
  }'
# expected: the data source is added; the dashboard can query the profiles
```

### 8.7 Step 6: correlate the profile with the trace

```bash
# Add the trace id to the profile
python code/part17/correlate_profile.py \
  --profile /profiles/trace-abc123.json \
  --trace-id abc123
# expected: the profile is queryable by trace id in Grafana
```

### 8.8 What to record

After the lab, you should answer these five questions in about five seconds each. That five-second goal is an example value, so set the target your team needs.

1. What is the current PyTorch Profiler write latency p99?
2. What is the current profile repository size?
3. What is the current trace-to-profile correlation rate?
4. What is the current slowest CUDA kernel?
5. What is the current slowest NCCL collective?

The 30-second cut-off is also an example value. If any answer takes longer than your cut-off, the stack is not yet a production service. The lab has not been run against a live GKE cluster.

---

## Exercises

Work through these after the lab. Each exercise extends the stack, and a solution sketch follows it.

1. Add an Nsight Systems profile to the trace. Configure Nsight Systems to capture the workload, and verify that its profile links to the OpenTelemetry trace. *Solution sketch:* the NVTX range includes the trace ID, the profile file name includes the trace ID, and an integration test checks the link.
2. Add an Nsight Compute dashboard. Build a Grafana dashboard that shows kernel-level metrics for each kernel. *Solution sketch:* build a Prometheus exporter for Nsight Compute, then add a Grafana dashboard with one panel per metric.
3. Add an NCCL Profiler dashboard. Build a Grafana dashboard that shows collective timings for each operation, size, and algorithm. *Solution sketch:* build a Prometheus exporter for the NCCL Profiler, then add a Grafana dashboard with those panels.
4. Add a profile retention policy. Configure the profile repository with retention periods that fit your storage budget. *Solution sketch:* an object storage lifecycle policy, reviewed each quarter.
5. Add a profile-to-trace correlation alert. Alert when the correlation rate falls below the target you choose. *Solution sketch:* a Prometheus alert on the correlation rate that pages the platform team.
6. Add a profile viewer to the on-call dashboard. Add a panel that links to the profile for each trace. *Solution sketch:* a Grafana data link that points to the profile, shown on the on-call dashboard.

Do exercise 5 first. A broken correlation is the failure that costs the most time during an incident.

## Checkpoint questions

<details><summary>1. A trace shows an inference request spent most of its time in the model call, and the trace stops there. What do you do next, and why?</summary>
The trace cannot say which GPU kernel caused the delay, so you move to a profile. Start broad with PyTorch Profiler to see which operations are slow, then use Nsight Systems for the timeline. Go to Nsight Compute only if one kernel dominates. The order in an incident is metrics, then traces, then the profile.
</details>

<details><summary>2. A multi-node training job runs at half speed and every GPU seems to be waiting on the others. Which profiler fits, and how do you turn it on?</summary>
Use the NCCL Profiler, because it shows which collective holds the job back. Run the job with `NCCL_DEBUG=INFO` set, send stderr to a file, and copy that file to object storage. Then look for the collective with the slow tail, for example in the p99 time per algorithm.
</details>

<details><summary>3. The on-call clicks a trace in Grafana and no profile appears. What is the likely cause, and what do you add afterwards?</summary>
The NVTX range or the profile file name probably does not carry the trace ID, so the link breaks. Check that both include it. Afterwards add an integration test that fails when the correlation breaks, and alert on the trace-to-profile correlation rate.
</details>

<details><summary>4. A profile write fails and the bucket is full. What went wrong and what is the fix?</summary>
The profile is too verbose and captures every CUDA kernel, so each step can produce a very large file. Capture only the slow operations. Use `torch.profiler.schedule` to skip warm-up steps so the profile stays small.
</details>

<details><summary>5. You run `ncu` with `--kernel-name regex:gemm_kernel` and the report does not contain the kernel you care about. What do you check?</summary>
Either the `--kernel-name` value does not match the kernel's real name, or the kernel was inlined or optimised away. Check the name first. Then use `--launch-skip` to skip warm-up launches and `--launch-count` to limit how many launches are profiled.
</details>

<details><summary>6. The NCCL log from a job is huge, hard to query, and close to filling the disk. What do you change?</summary>
The level is set to INFO, so every collective is logged in full. Use `NCCL_DEBUG=WARN` to cut the noise and set `NCCL_DEBUG_SUBSYS=COLL` to log only collective events. WARN also surfaces errors that would otherwise stay silent. Keep the detailed levels for short runs.
</details>

<details><summary>7. Why does naming the exported profile after the trace ID let the on-call find it?</summary>
The export function reads the trace ID from the active span and puts it in the file name. Any tool that can search the profile folder can then find the profile for a given trace. Test the link once in a staging run before you rely on it during an incident.
</details>

<details><summary>8. Why does the profiler schedule use wait, warmup and active steps instead of recording every step?</summary>
The example skips the first step, warms up for one step, and then records three active steps. Warm-up steps would distort the picture, and every recorded step adds to the profile. Profiles grow quickly, so recording only a few steps keeps storage and upload time under control.
</details>

<details><summary>9. Why does Nsight Systems slow a workload more when the workload has many kernels?</summary>
The profiler captures every kernel, so its overhead grows with the number of kernels. The chapter's fix is to capture only CUDA kernels with `nsys profile --trace=cuda` and to use the `--sample` flag to reduce the sampling rate.
</details>

<details><summary>10. Why does the NCCL dashboard split all-reduce timings by size bucket and show p99 per algorithm instead of one average?</summary>
A single average all-reduce time hides the difference between small and large messages. Splitting by size shows which messages are slow. A slow tail shows up in the p99 per algorithm before it shows in the average, so the p99 panel is the one to start with.
</details>

<details><summary>11. Why is a profile from yesterday dangerous to trust?</summary>
If the workload changed after the profile was taken, the profile describes an older version of the code. Regenerate the profile on every workload update, make that a CI step, and tag each profile with the workload's commit hash so you can see which code it came from.
</details>

<details><summary>12. When do you pick PyTorch Profiler, Nsight Systems or Nsight Compute, and what do you give up by starting broad?</summary>
Start with PyTorch Profiler for the high-level view of operations. Use Nsight Systems when you need the timeline and the idle gaps. Use Nsight Compute only for one kernel in depth. You give up detail at first, but you avoid the cost and size of a deep capture until the broad view points at a cause.
</details>

<details><summary>13. For a live inference server, when would you choose Nsight Compute sampling over full tracing, and what do you give up?</summary>
Choose sampling first, because it finds the hot instructions without full instrumentation and its overhead stays low. You give up completeness. Switch to full tracing only when a sample points to one kernel or phase.
</details>

<details><summary>14. When would you set `NCCL_DEBUG_SUBSYS` to `INIT,COLL` instead of `ALL`, and what do you give up?</summary>
The code comment says ALL is extremely verbose, while INIT and COLL are enough for most hangs. Choose INIT,COLL for normal debugging. You give up the log lines from the other subsystems, so use ALL only for a short run when those lines are needed.
</details>

<details><summary>15. Should heavy profilers run all the time in production, or should you watch lightweight metrics?</summary>
Production teams cannot run heavy profilers all the time. They watch lightweight metrics such as SM utilization and tail latency, and start a profile when those metrics look wrong. You give up kernel detail until you capture a profile. NVTX markers have very low overhead when no profiler is attached, so they can stay in production code.
</details>

<details><summary>16. One training step produces 10 GB of profile data in the chapter's example. How much do a 100-step run and a run that records only three active steps produce?</summary>
A 100-step run is 100 times 10 GB, which is 1,000 GB or 1 TB. Three active steps are 3 times 10 GB, which is 30 GB. The 10 GB figure is an example value, so measure your own.
</details>

<details><summary>17. An all-reduce of 1073741824 bytes takes 12.345 ms. What bandwidth is that?</summary>
Bandwidth is bytes divided by time, which is 1,073,741,824 bytes divided by 0.012345 seconds. That is about 87 billion bytes per second, or about 87 GB per second. This matches the chapter's bandwidth query, which divides bytes by duration.
</details>

<details><summary>18. In the chapter's example a multi-node job spends 20 to 40 percent of its time in NCCL collectives. For a 10 second step, how long is that?</summary>
Twenty percent of 10 seconds is 2 seconds, and 40 percent is 4 seconds. So between 2 and 4 seconds of each step are in collectives. The percentages are example figures, not measurements, and the 10 second step is an assumption.
</details>

<details><summary>19. A training step slowed down. In what order do you look, and why?</summary>
First look at metrics from Chapter 17.2 to see that something is slow. Second look at traces from Chapter 17.3 to find the slow operation. Third open the profile, which names the GPU kernel or NCCL collective. Each step narrows the search so the expensive profile is read last.
</details>

<details><summary>20. The kernel-time panel in Grafana is empty. What do you check first, second and third?</summary>
First confirm the exporter that publishes the profiler series is running, because this chapter does not set one up. Second confirm the series names in the query actually exist. Only then suspect the workload, since an empty panel usually means missing data, not a healthy job.
</details>

## Sources and review notes

- NVIDIA Zero-to-Hero Volume 16 (`chapter-06-distributed-observability.md`, `chapter-07-profiling.md`). Source for the profiling stack, the PyTorch Profiler integration, the Nsight Systems and Nsight Compute usage, and the NCCL Profiler. The wording has been rewritten in the handbook's voice.
- NVIDIA Zero-to-Hero Volume 7 (`chapter-02-distributed-tracing-and-profiling.md`). Source for the distributed tracing and profiling patterns.
- *AI Systems Performance Engineering* (`ai-systems-performance-engineering`, Chapters 13, 14, 15). Source for the PyTorch Profiler, Nsight Systems, Nsight Compute, and the kernel-level profiling patterns. The wording has been rewritten in the handbook's voice.

### Cross-references to other handbook chapters

- Chapter 10.20 for the GPU profiling tools.
- Chapter 17.1 for the three pillars.
- Chapter 17.3 for the OpenTelemetry integration.
- Chapter 17.4 for the GPU metrics.

### Migrated from `nvidia-devops`

The profiling operational patterns draw on Volume 16 chapters 6-7 and Volume 7 chapter 2. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The profiler overhead in Section 7.3 is approximate; specific overhead depends on the workload.
- The profile retention in Section 6.2 is a starting point; specific retention depends on the storage budget.
- The NVTX range coverage in Section 6.3 is a starting point; specific coverage depends on the workload.

### Not verified on live hardware

- The lab in Section 8 is **untested** against a live GKE cluster in this repository.
- The PyTorch Profiler, Nsight Systems, and Nsight Compute versions assumed in the lab should be pinned against the current releases before production use.
- The profile-to-trace correlation rate in the lab is illustrative; production rates depend on the workload.
