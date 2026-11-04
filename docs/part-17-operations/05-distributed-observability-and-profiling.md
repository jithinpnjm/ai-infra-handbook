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

Chapter 17.3 named the three pillars and walked through Loki and OpenTelemetry. This chapter walks through the AI-specific profiling tools that turn traces into actionable insights. A team that has traces but cannot profile the GPU kernels is a team that knows the inference is slow but cannot find the slow kernel. A team that has metrics but cannot profile the NCCL collectives is a team that knows the training is slow but cannot find the slow collective.

Profiling is the difference between knowing that the workload is slow and knowing why. The on-call engineer's first action during a performance incident is to look at the metrics (Chapter 17.2); the second action is to look at the traces (Chapter 17.3); the third action is to look at the profile. The profile is what tells the on-call which GPU kernel or which NCCL collective is the bottleneck.

```text
Why profiling is on the critical path (V16 ch6, 7; ASP Ch 13-15):
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

Three operational realities make this chapter a platform-team concern rather than a data-science-only concern:

1. **The profiling tools are GPU-specific.** PyTorch Profiler, Nsight Systems, Nsight Compute, NCCL Profiler — these are not generic tools; these are NVIDIA-specific tools. The platform team owns the deployment and the integration.
2. **The profile is large.** A single training step can produce 10 GB of profile data. The platform team's pattern is to store the profiles in object storage; the platform team owns the retention policy.
3. **The profile is correlated with the trace.** The on-call needs the trace to find the slow operation; the on-call needs the profile to find the slow kernel. The platform team owns the integration that links the two.

**Before a team can debug a performance incident, the workload must be profiled end-to-end; the profile must be stored in object storage; the profile must be correlated with the trace. A workload without a profile is a workload that the on-call cannot optimise.**

## Prerequisites and outcomes

### Prerequisites

- Chapter 10.20 (Profiling tools) for the GPU profiling concepts.
- Chapter 17.1 (Observability foundations) for the three pillars.
- Chapter 17.3 (Logging with Loki and tracing with OpenTelemetry) for the trace integration.
- Chapter 17.4 (DCGM exporter) for the GPU metrics.

### Outcomes

After completing this chapter you will be able to:

1. Deploy PyTorch Profiler, Nsight Systems, and Nsight Compute on the cluster; verify the profiles are stored in object storage.
2. Configure NCCL profiling for multi-node training; verify the collective timings are visible in the traces.
3. Correlate the profile with the trace; the on-call clicks on a trace and sees the profile for that trace.
4. Interpret the profile: identify the slow kernel, the slow collective, the slow data loader.
5. Build a profile dashboard in Grafana that surfaces the slow kernels and the slow collectives.
6. Operate the profiling stack on GKE with SLOs, observability, and a runbook.

---

## 1. The profiling stack

### 1.1 The four profilers

NVIDIA Zero-to-Hero Volume 16 chapter 7 and Volume 7 chapter 2 walk through the four profilers.

| Profiler | What it profiles | When to use |
|---|---|---|
| **PyTorch Profiler** | PyTorch operations (forward, backward, optimiser) | PyTorch workloads; high-level view |
| **Nsight Systems** | CUDA kernels, memory transfers, GPU utilisation | Detailed kernel-level view |
| **Nsight Compute** | Single kernel performance (occupancy, register pressure) | Deep dive on a single kernel |
| **NCCL Profiler** | NCCL collectives (all-reduce, all-gather, reduce-scatter) | Multi-node training |

The pattern is: PyTorch Profiler first (the high-level view); Nsight Systems next (the kernel-level view); Nsight Compute last (the single-kernel deep dive); NCCL Profiler in parallel (the collective view for multi-node training).

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

The pattern is: the profilers run on the workload; the profiles are exported to object storage; the profiles are correlated with the trace; the profiles and the traces are queryable in Grafana.

### 1.3 The profile format

The profile is a structured trace in the Chrome Trace Event Format. The profile is queryable in the Chrome browser's `chrome://tracing`; the profile is also queryable in PyTorch Profiler Viewer, Nsight Systems GUI, and Grafana's trace UI.

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

The format is JSON; the format is parseable; the format is queryable. The on-call can find the slow operation by querying the JSON; the on-call can find the slow kernel by looking at the kernel timings; the on-call can find the slow collective by looking at the collective timings.

---

## 2. PyTorch Profiler

### 2.1 The PyTorch Profiler basics

The PyTorch Profiler is built into PyTorch; the profiler is invoked with `torch.profiler.profile`; the profiler emits a trace in the Chrome Trace Event Format.

```python
# code/part17/pytorch_profiler.py (shape only)
import torch
from torch.profiler import profile, ProfilerActivity, record_function

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    schedule=torch.profiler.schedule(wait=1, warmup=1, active=3, repeat=1),
    on_trace_ready=torch.profiler.tensorboard_trace_handler("./profiles"),
    record_shapes=True,
    profile_memory=True,
    with_stack=True,
) as prof:
    for step in range(5):
        with record_function(f"step_{step}"):
            # ... training step ...
        prof.step()
```

The pattern is: wrap the training step in `torch.profiler.profile`; the profiler records the CPU and CUDA activities; the profiler emits the trace to a TensorBoard-compatible handler; the trace is uploaded to object storage.

### 2.2 The PyTorch Profiler integration with the trace

The PyTorch Profiler can be correlated with the OpenTelemetry trace by including the trace id in the profile's annotations.

```python
# code/part17/pytorch_profiler_otel.py (shape only)
import torch
from torch.profiler import profile, ProfilerActivity, record_function
from opentelemetry import trace

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    on_trace_ready=lambda prof: prof.export_chrome_trace(f"./profiles/trace-{trace.get_current_span().get_span_context().trace_id}.json"),
) as prof:
    for step in range(5):
        with record_function(f"step_{step}"):
            # ... training step ...
        prof.step()
```

The pattern is: the trace id is part of the profile filename; the profile is queryable by trace id in Grafana; the on-call clicks on a trace and sees the profile for that trace.

### 2.3 The PyTorch Profiler dashboard

The PyTorch Profiler dashboard in Grafana shows the kernel timings, the memory usage, and the GPU utilisation per step. The dashboard is the on-call engineer's view of the profile.

```promql
# The total CUDA time per kernel
sum by (kernel) (rate(pytorch_profiler_cuda_time_seconds[5m]))

# The total memory usage per operation
sum by (operation) (pytorch_profiler_memory_bytes)

# The GPU utilisation per step
avg by (step) (DCGM_FI_DEV_GPU_UTIL)
```

The pattern is: the dashboard shows the slow kernels; the on-call clicks on a slow kernel; the dashboard shows the kernel's profile; the on-call finds the root cause.

---

## 3. Nsight Systems

### 3.1 The Nsight Systems basics

Nsight Systems is NVIDIA's system-wide profiler. Nsight Systems profiles the CUDA kernels, the memory transfers, the GPU utilisation, and the API calls. Nsight Systems is invoked with `nsys`; the profile is stored in a `.nsys-rep` file; the profile is opened in the Nsight Systems GUI.

```bash
# Run Nsight Systems on a workload
nsys profile \
  --output=/profiles/workload.nsys-rep \
  --force-overwrite=true \
  --trace=cuda,nvtx,osrt \
  python train.py
```

The pattern is: wrap the workload's invocation in `nsys profile`; the profiler records the CUDA kernels and the NVTX ranges; the profile is stored in a `.nsys-rep` file; the profile is uploaded to object storage.

### 3.2 The Nsight Systems integration with the trace

The Nsight Systems profile can be correlated with the OpenTelemetry trace by including the trace id in the NVTX ranges.

```python
# code/part17/nsight_nvtx_otel.py (shape only)
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

The pattern is: the NVTX range includes the trace id; the Nsight Systems profile shows the NVTX range; the on-call correlates the NVTX range with the trace id; the on-call clicks on the trace id in Grafana and sees the profile for that trace.

### 3.3 The Nsight Systems dashboard

The Nsight Systems dashboard in Grafana shows the kernel timelines, the memory transfers, and the GPU utilisation per kernel. The dashboard is the on-call engineer's view of the kernel-level profile.

```text
Nsight Systems dashboard panels:
- Kernel timeline: the CUDA kernels per stream
- Memory transfer timeline: the HBM-DRAM transfers
- GPU utilisation: the DCGM_FI_DEV_GPU_UTIL metric
- API call timeline: the CUDA API calls
- NVTX range timeline: the application's logical ranges
```

The pattern is: the dashboard shows the kernel timelines; the on-call clicks on a slow kernel; the dashboard shows the kernel's CUDA source; the on-call finds the root cause.

---

## 4. Nsight Compute

### 4.1 The Nsight Compute basics

Nsight Compute is NVIDIA's kernel-level profiler. Nsight Compute profiles a single CUDA kernel; the profile includes the kernel's occupancy, register pressure, memory access patterns, and instruction-level metrics. Nsight Compute is invoked with `ncu`; the profile is stored in a `.ncu-rep` file; the profile is opened in the Nsight Compute GUI.

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

The pattern is: wrap the workload's invocation in `ncu`; the profiler records the kernel's metrics; the profile is stored in a `.ncu-rep` file; the profile is uploaded to object storage.

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

The pattern is: the metrics tell the on-call why the kernel is slow (low SM utilisation, high register pressure, low occupancy). The on-call applies the fix (rewrite the kernel, reduce register pressure, increase shared memory).

### 4.3 The Nsight Compute integration with Nsight Systems

The Nsight Compute profile can be linked from the Nsight Systems profile. The pattern is: the Nsight Systems profile shows the slow kernel; the on-call clicks on the slow kernel; the dashboard opens the Nsight Compute profile for that kernel.

```text
Nsight Systems → Nsight Compute integration:
- Nsight Systems shows the kernel timelines
- The on-call clicks on a slow kernel
- The dashboard opens the Nsight Compute profile for that kernel
- The Nsight Compute profile shows the kernel's metrics
```

The pattern is the integration that turns the high-level profile into the kernel-level profile. The on-call follows the chain from the trace to the high-level profile to the kernel-level profile to the root cause.

---

## 5. NCCL Profiler

### 5.1 The NCCL Profiler basics

The NCCL Profiler is NVIDIA's collective communication profiler. The NCCL Profiler profiles the NCCL collectives (all-reduce, all-gather, reduce-scatter, broadcast); the profile includes the collective size, the algorithm, the protocol, and the duration. The NCCL Profiler is invoked with `NCCL_DEBUG=INFO` and `NCCL_DEBUG_SUBSYS=ALL`; the profile is emitted to stderr.

```bash
# Run NCCL Profiler
NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=ALL python train.py 2> nccl_profile.log
```

The pattern is: wrap the workload's invocation in the NCCL debug environment variables; the profiler records the collectives; the log is uploaded to object storage.

### 5.2 The NCCL profile format

The NCCL profile is a log of collective events. The log is parseable; the log is queryable.

```text
[NCCL DEBUG] Channel 0: 0[0] -> 1[0] [send] via P2P/IPC
[NCCL DEBUG] Channel 0: 0[0] -> 1[0] [receive] via P2P/IPC
[NCCL DEBUG] Channel 0: all-reduce algorithm: Ring
[NCCL DEBUG] Channel 0: all-reduce protocol: Simple
[NCCL DEBUG] Channel 0: all-reduce size: 1073741824 bytes
[NCCL DEBUG] Channel 0: all-reduce time: 12.345 ms
```

The pattern is: every collective event is logged with the size, the algorithm, the protocol, and the time. The on-call can find the slow collective by parsing the log; the on-call can find the slow algorithm by looking at the algorithm field.

### 5.3 The NCCL profile integration with the trace

The NCCL profile can be correlated with the OpenTelemetry trace by including the trace id in the NCCL events.

```python
# code/part17/nccl_profile_otel.py (shape only)
import os
os.environ["NCCL_DEBUG"] = "INFO"
os.environ["NCCL_DEBUG_SUBSYS"] = "ALL"

import torch
import torch.distributed as dist
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("all-reduce"):
    dist.all_reduce(tensor)
```

The pattern is: the NCCL events are correlated with the OpenTelemetry trace; the on-call clicks on a trace and sees the NCCL events for that trace.

### 5.4 The NCCL profile dashboard

The NCCL profile dashboard in Grafana shows the collective timings per operation, per size, and per algorithm. The dashboard is the on-call engineer's view of the collective profile.

```promql
# The average all-reduce time per size
sum by (size_bucket) (rate(nccl_all_reduce_duration_seconds_sum[5m])) / sum by (size_bucket) (rate(nccl_all_reduce_duration_seconds_count[5m]))

# The p99 all-reduce time per algorithm
histogram_quantile(0.99, sum by (algorithm, le) (rate(nccl_all_reduce_duration_seconds_bucket[5m])))

# The collective bandwidth
sum by (size_bucket) (rate(nccl_all_reduce_bytes[5m])) / sum by (size_bucket) (rate(nccl_all_reduce_duration_seconds_sum[5m]))
```

The pattern is: the dashboard shows the collective timings; the on-call clicks on a slow collective; the dashboard shows the collective's algorithm and size; the on-call finds the root cause.

---

## 6. Operating the profiling stack on GKE

### 6.1 The components

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| PyTorch Profiler | In the workload's process | Object storage for profile | Profile write latency p99 < 30 s |
| Nsight Systems | In the workload's process (sidecar or shared) | Object storage for `.nsys-rep` | Profile write latency p99 < 30 s |
| Nsight Compute | In the workload's process | Object storage for `.ncu-rep` | Profile write latency p99 < 30 s |
| NCCL Profiler | In the workload's process | Object storage for log | Log write latency p99 < 30 s |
| Profile repository | Object storage | (the profiles themselves) | Profile load latency p99 < 5 s |
| Trace backend (Tempo) | Kubernetes Deployment | Object storage for traces | Trace query latency p99 < 5 s |

### 6.2 IAM and the profile cardinality

The profiling stack has its own IAM. The pattern is:

| Role | Who | What they can do |
|---|---|---|
| `profiler.reader` | The on-call; data scientists | Read profiles from object storage; view profiles in Grafana |
| `profiler.writer` | The workload's process | Write profiles to object storage |
| `profiler.admin` | The platform team | Manage the profile retention; manage the profile dashboard |

The profile cardinality is the profile's storage cost. A single training step can produce 10 GB of profile data; a 100-step training run produces 1 TB of profile data. The platform team's pattern is to retain profiles for 7 days; archive to cold storage for 30 days; delete after 30 days.

### 6.3 Observability

| Metric | Why it matters | Alert |
|---|---|---|
| Profile write latency p99 | Hot path for profile upload | > 30 s |
| Profile repository size | Storage budget | > 80% for 1 day |
| Trace-to-profile correlation rate | Catches broken correlation | < 100% for 1 hour |
| NVTX range coverage | Catches missing correlation | < 100% for 1 hour |

The trace-to-profile correlation rate is the most important. A broken correlation means the on-call cannot find the profile for a trace; the on-call must debug without the profile.

---

## 7. How it fails

Six failure modes recur.

### 7.1 "The profile is too large"

**Symptom:** The profile write fails; the object storage bucket fills up; the team runs out of storage.

**Diagnosis:** The profile is too verbose; the profile captures every CUDA kernel; the profile is hundreds of GB per step.

**Fix:** Reduce the profile's verbosity; capture only the slow operations; use the `torch.profiler.schedule` to skip warm-up steps.

### 7.2 "The profile is not correlated with the trace"

**Symptom:** The on-call clicks on a trace in Grafana; the dashboard does not show the profile for that trace.

**Diagnosis:** The NVTX ranges do not include the trace id; the profile filename does not include the trace id; the correlation is broken.

**Fix:** Verify the NVTX ranges include the trace id; verify the profile filename includes the trace id; add an integration test that asserts the correlation.

### 7.3 "The Nsight Systems profiler adds too much overhead"

**Symptom:** The workload runs 10x slower with the profiler enabled; the profiler overhead is too high.

**Diagnosis:** The profiler is capturing every kernel; the profiler's overhead is proportional to the kernel count.

**Fix:** Use the `nsys profile --trace=cuda` flag to capture only the CUDA kernels; use the `--sample` flag to reduce the sampling rate.

### 7.4 "The NCCL Profiler log is too large"

**Symptom:** The NCCL log is hundreds of MB; the log is hard to query; the log fills up the disk.

**Diagnosis:** The NCCL Profiler is set to `INFO`; every collective is logged with full details; the log is too verbose.

**Fix:** Use `NCCL_DEBUG=WARN` to reduce the verbosity; use `NCCL_DEBUG_SUBSYS=COLL` to log only the collective events.

### 7.5 "The Nsight Compute profile is missing the kernel"

**Symptom:** The on-call runs `ncu` on the workload; the profile does not include the kernel of interest.

**Diagnosis:** The `--kernel-name` flag does not match the kernel's name; the kernel is inlined or optimised away.

**Fix:** Verify the kernel name; use `--launch-skip` to skip warm-up steps; use `--launch-count` to limit the number of profiled launches.

### 7.6 "The profile is stale"

**Symptom:** The on-call opens the profile; the profile is from yesterday; the workload has changed since then.

**Diagnosis:** The workload has been updated; the profile is not regenerated; the profile is from a previous version of the workload.

**Fix:** Regenerate the profile on every workload update; the CI includes the profile regeneration as a step; the profile is tagged with the workload's commit hash.

---

## 8. Hands-on lab

This lab stands up the profiling stack on GKE, runs PyTorch Profiler on a training workload, and verifies the profile is correlated with the trace. The lab is **untested** in this repository.

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
# code/part17/profiling_workload.yaml (shape only)
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

After the lab, you should be able to answer five questions in five seconds each:

1. What is the current PyTorch Profiler write latency p99?
2. What is the current profile repository size?
3. What is the current trace-to-profile correlation rate?
4. What is the current slowest CUDA kernel?
5. What is the current slowest NCCL collective?

If any takes more than 30 seconds, the profiling stack is not yet a production service. The lab is **untested** against a live GKE cluster.

---

## Exercises

1. **Add a Nsight Systems profile to the trace.** Configure Nsight Systems to capture the trace; verify the profile is correlated with the OpenTelemetry trace. *Solution sketch:* the NVTX range includes the trace id; the profile filename includes the trace id; the integration test asserts the correlation.
2. **Add an Nsight Compute dashboard.** Build a Grafana dashboard that shows the kernel-level metrics per kernel. *Solution sketch:* a Prometheus exporter for Nsight Compute; a Grafana dashboard; the panels.
3. **Add an NCCL Profiler dashboard.** Build a Grafana dashboard that shows the collective timings per operation, per size, and per algorithm. *Solution sketch:* a Prometheus exporter for NCCL Profiler; a Grafana dashboard; the panels.
4. **Add a profile retention policy.** Configure the profile repository to retain profiles for 7 days; archive to cold storage for 30 days; delete after 30 days. *Solution sketch:* an object storage lifecycle policy; the policy is reviewed quarterly.
5. **Add a profile-to-trace correlation alert.** Alert when the trace-to-profile correlation rate drops below 100%. *Solution sketch:* a Prometheus alert on the correlation rate; the alert pages the platform team.
6. **Add a profile viewer to the on-call dashboard.** Add a panel to the on-call dashboard that links to the profile for the trace. *Solution sketch:* a Grafana data link that points to the profile; the panel is visible on the on-call dashboard.

---

## Checkpoint questions

<details><summary>1. What four profilers does the chapter walk through?</summary>
PyTorch Profiler (PyTorch operations; high-level view), Nsight Systems (CUDA kernels, memory transfers, GPU utilisation; kernel-level view), Nsight Compute (single kernel performance; deep dive on a single kernel), NCCL Profiler (NCCL collectives; multi-node training). The pattern is: PyTorch Profiler first, Nsight Systems next, Nsight Compute last, NCCL Profiler in parallel.
</details>

<details><summary>2. What is the profile format?</summary>
The Chrome Trace Event Format. The profile is JSON; the profile is parseable; the profile is queryable in the Chrome browser's chrome://tracing, PyTorch Profiler Viewer, Nsight Systems GUI, and Grafana's trace UI.
</details>

<details><summary>3. What does the PyTorch Profiler profile?</summary>
PyTorch operations (forward, backward, optimiser). The PyTorch Profiler is built into PyTorch; the profiler is invoked with torch.profiler.profile; the profiler emits a trace in the Chrome Trace Event Format. The pattern is: wrap the training step in torch.profiler.profile; the profiler records the CPU and CUDA activities.
</details>

<details><summary>4. What does Nsight Systems profile?</summary>
CUDA kernels, memory transfers, GPU utilisation, and API calls. Nsight Systems is invoked with nsys; the profile is stored in a .nsys-rep file. The pattern is: wrap the workload's invocation in nsys profile; the profiler records the CUDA kernels and the NVTX ranges.
</details>

<details><summary>5. What does Nsight Compute profile?</summary>
A single CUDA kernel. The profile includes the kernel's occupancy, register pressure, memory access patterns, and instruction-level metrics. Nsight Compute is invoked with ncu; the profile is stored in a .ncu-rep file. The pattern is: wrap the workload's invocation in ncu; the profiler records the kernel's metrics.
</details>

<details><summary>6. What does the NCCL Profiler profile?</summary>
NCCL collectives (all-reduce, all-gather, reduce-scatter, broadcast). The profile includes the collective size, the algorithm, the protocol, and the duration. The NCCL Profiler is invoked with NCCL_DEBUG=INFO; the profile is emitted to stderr.
</details>

<details><summary>7. How is the profile correlated with the trace?</summary>
The NVTX range includes the trace id; the profile filename includes the trace id; the profile is queryable by trace id in Grafana. The on-call clicks on a trace in Grafana; the dashboard shows the profile for that trace.
</details>

<details><summary>8. What is the most expensive profiling tool?</summary>
Nsight Compute. Nsight Compute profiles a single kernel in detail; the profile can be hundreds of MB per kernel. The platform team's pattern is to use Nsight Compute only when the high-level profile (PyTorch Profiler, Nsight Systems) has identified a single slow kernel.
</details>

<details><summary>9. What is the cardinality impact of the profiling stack?</summary>
A single training step can produce 10 GB of profile data; a 100-step training run produces 1 TB of profile data. The platform team's pattern is to retain profiles for 7 days; archive to cold storage for 30 days; delete after 30 days.
</details>

<details><summary>10. What is the most common profiling failure mode?</summary>
The profile is too large. The profile write fails; the object storage bucket fills up; the team runs out of storage. The fix is to reduce the profile's verbosity; capture only the slow operations; use the torch.profiler.schedule to skip warm-up steps.
</details>

<details><summary>11. What is the most common correlation failure mode?</summary>
The profile is not correlated with the trace. The NVTX ranges do not include the trace id; the profile filename does not include the trace id; the correlation is broken. The fix is to verify the NVTX ranges include the trace id; verify the profile filename includes the trace id; add an integration test.
</details>

<details><summary>12. What is the difference between Nsight Systems and Nsight Compute?</summary>
Nsight Systems profiles the entire workload (CUDA kernels, memory transfers, GPU utilisation, API calls); Nsight Compute profiles a single CUDA kernel in detail (occupancy, register pressure, memory access patterns, instruction-level metrics). The pattern is: Nsight Systems first (find the slow kernel); Nsight Compute next (profile the slow kernel).
</details>

<details><summary>13. What is the difference between PyTorch Profiler and Nsight Systems?</summary>
PyTorch Profiler profiles PyTorch operations (forward, backward, optimiser); Nsight Systems profiles CUDA kernels and API calls. PyTorch Profiler is built into PyTorch; Nsight Systems is a separate tool. The pattern is: PyTorch Profiler for high-level view; Nsight Systems for kernel-level view.
</details>

<details><summary>14. What is the NCCL collective algorithm?</summary>
The algorithm that NCCL uses for the collective. Common algorithms include Ring, Tree, and NVLS. The algorithm affects the collective's latency and bandwidth; the algorithm is chosen based on the collective size, the number of ranks, and the topology.
</details>

<details><summary>15. What is the NCCL collective protocol?</summary>
The protocol that NCCL uses for the collective. Common protocols include Simple, LL (Low Latency), and LL128. The protocol affects the collective's latency and bandwidth; the protocol is chosen based on the collective size and the network bandwidth.
</details>

<details><summary>16. What is the NCCL_DEBUG_SUBSYS environment variable?</summary>
The environment variable that controls which NCCL subsystems are logged. Common subsystems include INIT, COLL, P2P, NET, ALL. The platform team's pattern is to use NCCL_DEBUG_SUBSYS=COLL for collective-only profiling.
</details>

<details><summary>17. What is the NVTX range?</summary>
NVIDIA Tools Extension (NVTX) is a C-based API for annotating the application's source code with ranges and markers. The NVTX range is a named region of code; the NVTX range is captured by Nsight Systems; the NVTX range is correlated with the OpenTelemetry trace via the trace id.
</details>

<details><summary>18. What is the chrome://tracing UI?</summary>
The Chrome browser's built-in trace viewer. The viewer renders the Chrome Trace Event Format; the viewer shows the timeline of events; the viewer is the on-call engineer's tool for inspecting profiles. The viewer is at chrome://tracing in the Chrome browser.
</details>

<details><summary>19. What is the difference between PyTorch Profiler and TensorBoard?</summary>
PyTorch Profiler is built into PyTorch; PyTorch Profiler emits the Chrome Trace Event Format. TensorBoard is a visualisation tool that reads the PyTorch Profiler output; TensorBoard renders the profile in the TensorBoard UI. The pattern is: PyTorch Profiler produces the profile; TensorBoard visualises the profile.
</details>

<details><summary>20. What five questions should the profiling lab let you answer in five seconds each?</summary>
What is the current PyTorch Profiler write latency p99. What is the current profile repository size. What is the current trace-to-profile correlation rate. What is the current slowest CUDA kernel. What is the current slowest NCCL collective. If any takes more than 30 seconds, the profiling stack is not yet a production service.
</details>

---

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
