---
id: "c17-07"
title: "17.7 Failure modes and detection"
sidebar_label: "17.7 Failure modes and detection"
sidebar_position: 7
description: "AI infrastructure failure modes: GPU hardware failures, network failures, storage failures, scheduler failures, container image failures, model serving failures, and the detection patterns that catch them before they cascade."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 17.7 Failure modes and detection

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Cross-references | Chapter 17.4 (DCGM exporter); Chapter 17.6 (Alerting and SLOs); Chapter 11 (GPU Kubernetes); Chapter 16.10 (Monitoring and drift) |
| Coverage file | `planning/coverage/chapters/17-07.md` |
| Claim & number ledger | `planning/ledgers/17-07.md` |

## The six failure families

Picture a GPU node that starts logging memory errors late at night while a training job is still running on it. Nobody has written down what those errors mean, so the on-call engineer has to start from nothing. A failure mode is a specific way the cluster stops meeting its objectives. The goal of this chapter is to name each one before it happens, so the response is already written down when the page arrives.

Each one below is a short entry. It gives the symptom you see first, the signal that detects the failure, and the first action to take. The diagram shows where each family is caught.

```mermaid
flowchart LR
    subgraph Categories["Six failure categories"]
        HW[GPU hardware<br/>ECC, Xid, thermal]
        NET[Network<br/>NCCL, RDMA, partition]
        STO[Storage<br/>object store, disk]
        SCH[Scheduler<br/>OOMKilled, image pull]
        IMG[Container image<br/>signature, CVE]
        SVC[Model serving<br/>OOM, quality]
    end

    subgraph Detection["Detection layer"]
        DCGM[DCGM exporter<br/>GPU metrics]
        PROM[Prometheus<br/>SLI metrics]
        LOGS[Loki<br/>log patterns]
        ALERT[Alertmanager<br/>inhibit rules]
    end

    subgraph Response["Response layer"]
        RB[Runbook]
        IC[Incident Commander]
        DR[Disaster recovery]
    end

    HW --> DCGM
    NET --> DCGM
    STO --> PROM
    SCH --> PROM
    IMG --> LOGS
    SVC --> DCGM

    DCGM --> ALERT
    PROM --> ALERT
    LOGS --> ALERT
    ALERT --> RB
    RB --> IC
    IC --> DR
```

## Why this matters for AI infrastructure

It is the middle of the night, and a page arrives. A training job stopped making progress some time ago, and the GPU dashboard shows nothing obvious. An on-call engineer who knows the failure modes can name the likely cause from the symptom and start the right fix. An engineer who does not know them spends the first minutes searching the wiki, while the cluster stays stuck and the job keeps losing time.

![Three stacked boxes: name the likely cause from the symptom, know the failure catalogue, and start the right fix, with arrows pointing down.](./img/g-332.jpg)
*Figure 17.7.V. Learn the failure catalogue so that a page points you to a likely cause and a fix quickly.*


The earlier chapters in this part show how to detect failures, one tool at a time. This chapter is the catalogue of the failures themselves. An AI infrastructure failure mode is a specific way the cluster can stop meeting its service-level objectives, which are the targets the team has promised for speed and availability. The range is wide. At one end, a single GPU reports a memory error that the DCGM exporter picks up. DCGM is the NVIDIA tool that reads GPU health counters, and the DCGM exporter publishes those counters so Prometheus can store them. At the other end, a network partition splits the cluster, and the Prometheus blackbox exporter is the detector.

Every failure mode needs three things. It needs a detection signal, an alert built on that signal, and a runbook the alert links to. A runbook is a written set of steps for one kind of problem. Without all three, the failure is either invisible or unhandled. Think of a smoke alarm that rings with nobody assigned to answer it. The tables in this chapter use the symptom, detect and first action columns for that reason, so you can check each row for all three parts.

Picture a data scientist who sees a model give strange results on a Monday morning, while a platform engineer sees the cluster misbehaving at the same moment. Before the entries, one point about ownership. This chapter belongs to the platform team as much as to the data scientists. Three things make it a platform concern.

1. The failure modes are platform-level. A data scientist sees a model that gives bad results. The platform team sees a cluster that stops working, and this chapter catalogues those cluster failures.

Put together, the three points give one team the whole path from signal to fix. That is why the platform team should plan the catalogue, not leave it to whoever is on call that week.

2. The detection signals are platform-level. The DCGM exporter catches GPU failures, Prometheus catches metric failures, Loki catches log failures, and Tempo catches trace failures. The platform team owns that detection.

3. The runbooks are platform-level. Each alert should carry a runbook link, so the on-call engineer finds the next step from the alert itself. Put a description and a runbook link in each alert's annotations, so the responder has context right away. The platform team owns those runbooks.

**Build the failure mode catalogue before the first AI workload runs on the cluster.** Without it, every incident starts from scratch. With it, the on-call engineer recognises the symptom and moves straight to the fix.

## Prerequisites and outcomes

### Prerequisites

- Chapter 17.4 (DCGM exporter) for the GPU-specific failures.
- Chapter 17.6 (Alerting and SLOs) for the alert routing.
- Chapter 11 (GPU Kubernetes) for the GPU node operations.

Read these chapters before you start, because the rest of this chapter assumes you already know what they cover. The DCGM exporter and the alert routing are the two tools you will use most, and the GPU node operations come from the GPU Kubernetes chapter. Skipping them means the entries below will read as a list of unexplained names.

### Outcomes

This chapter walks through the six groups of failure that matter most for AI infrastructure: GPU hardware, network, storage, scheduler, container image, and model serving. For each group it shows the detection signal, the alert with its threshold and routing, and the runbook link the on-call engineer opens. It then shows how to build the catalogue, which is a structured document the on-call engineer can search quickly during an incident. Last, it covers how to keep the catalogue current by updating it after every incident, reviewing it each quarter, and checking that its entries are fresh. The chapter ends with the GKE lab, where you run the stack and confirm that the runbooks work.

---

## 1. GPU hardware failures

![GPU hardware failures with the signal to watch and the first action for each](./img/pre-gpu-failures.jpg)

*Figure 17.7.1. Each GPU failure has a signal that detects it and a first action. Most start with cordon and drain.*

### 1.1 The GPU failure catalogue

GPU hardware causes a large share of training interruptions, and one published record makes that concrete. Meta recorded 419 unexpected interruptions in 54 days of Llama 3 405B pretraining. Faulty GPUs caused 148 of them, which is 35.3 percent. GPU HBM3 memory caused 72 more, which is 17.2 percent. HBM3 is the high-bandwidth memory that sits on the GPU package, next to the compute cores. Together those two causes are more than half of the unexpected stops, so GPU faults deserve the first place in the catalogue. Chapter 17.13 uses the full table for fleet reliability numbers.

The table names each failure, then gives its symptom, the signal that detects it, and the first action. The metric names are the dcgm-exporter 4.9.0 names. Chapter 17.4 maps them to the 4.8.x names and holds the alert rules that go with them.

Read each row from left to right. The symptom tells you what someone will notice first, the detection signal tells you where to look, and the first action tells you what to do with the node or the job. A row that has a signal but no action is a gap to close before the next incident, and a row with an action but no signal is a fix nobody will know to apply.

| Failure mode | Symptom | Detect | First action |
|---|---|---|---|
| Uncorrectable ECC error | Job crash or corrupted output | `increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[1h]) > 0`, Xid 48 in the kernel log | Cordon and drain, flag checkpoints from the fault window |
| Failed row remap | Spare rows exhausted | `DCGM_FI_DEV_ROW_REMAP_FAILED == 1`, Xid 64 | Cordon, drain, RMA |
| Single-bit error growth | None yet | Weekly `increase` of `DCGM_FI_DEV_ECC_SBE_AGG_TOTAL` more than triples | Ticket, drain at the next window |
| GPU fell off the bus | Job dies, GPU missing | Xid 79, node reports fewer GPUs than it advertises | Cordon, drain, PCIe rescan, `dcgmi diag -r 3` |
| Thermal throttling | Jobs run slower, no error | `rate(DCGM_FI_DEV_GPU_THERMAL_THROTTLE_SECONDS_TOTAL[10m])` above 0.1 | Check fans and inlet temperature, then the rack |
| Power throttling | Jobs run slower | Rate of `DCGM_FI_DEV_GPU_POWER_THROTTLE_SECONDS_TOTAL` | Compare with the site power cap |
| CUDA out of memory | Step crashes with a CUDA error | `CUDA out of memory` in the application log | Shrink batch or model, see section 4.2 |
| GPU hang | No progress, no error | Step counter flat while the GPU reports work, NCCL watchdog timeout in the log | Restart the job, drain the node if it repeats |
| NVLink errors | Slow collectives | `increase(DCGM_FI_DEV_NVLINK_CRC_DATA_ERROR_TOTAL[1h])` | Compare both link ends, reseat or replace |
| PCIe replays | Slow host transfers | `increase(DCGM_FI_DEV_PCIE_REPLAY_TOTAL[1h])` | Check link width and generation, reseat |

Thermal and power throttle counters, ECC counters and NVLink counters are optional fields in the default counters file. Enable them before you rely on these rows. Without them, a throttling GPU can look normal on the dashboard, and that blind spot is exactly what this table is meant to prevent. A quick check is to query one of these metric names after the exporter restarts and confirm that a value comes back.

### 1.2 The ECC error storm

Picture a GPU that logs a few corrected memory errors each hour while its job keeps running with no visible problem. Memory errors often come before a GPU fails, and the early ones are easy to miss. ECC, the error-correcting code built into GPU memory, fixes a single-bit error on the fly, so the job keeps running. A double-bit error cannot be corrected, but the hardware detects it and raises it to the program that caused it. ECC is on by default on NVIDIA data center GPUs. A corrected error is still a warning, because the rate of those warnings tells you whether the memory is getting worse.

Read the timeline as the story of one GPU getting worse. It is an illustration, not a measured log, so use it for the order of events and not for the times or rates.

```text
The ECC error storm:
- T+0: SBE rate increases from 0 to 10/hour
- T+1h: SBE rate increases to 50/hour
- T+2h: First DBE appears
- T+2h+1m: DBE rate increases to 5/hour
- T+3h: GPU is corrupting data; workload must be moved
- T+4h: GPU is replaced
```

Alerting on a fixed single-bit rate would miss this storm. The rate never reaches a round number like 100 per hour before the first double-bit error, so a rule that waits for that number stays silent through the early climb. The policy in chapter 17.4 watches the week-over-week growth of single-bit errors instead, and it pages on any double-bit error, then drains the node at once. Measure the normal error rate on your own fleet before you set thresholds, since a rate that is healthy on one fleet can be a warning sign on another.

### 1.3 The GPU hang

Picture a training job whose log stops moving late at night, while the GPU monitor still shows the card as busy. A GPU hang is the quietest failure in this chapter. The workload still runs, kernels sit in the queue, and the GPU makes no progress. A kernel is a small program that runs on the GPU, and kernels waiting in the queue behave like cars waiting at a toll gate. Nothing crashes, so nothing forces anyone to look until the job stalls.

The SM clock does not show a hang, because a powered GPU has a non-zero clock whether it is working or stuck. SM stands for streaming multiprocessor, the block of compute units inside the GPU. The signal that does show a hang is a mismatch. The GPU reports high utilisation, but the job's own progress counter, such as steps or tokens per second, stays flat for several step times. Set the wait from your own step time, because a legitimate step can take seconds or minutes.

```bash
# Detect a GPU hang
nvidia-smi --query-gpu=utilization.gpu,clocks.sm --format=csv -l 5
# expected: utilisation stays high while the job's step counter does not advance, which means hung
```

Fail fast. A hung call that raises an error is far more useful than one that holds GPU time quietly for a long time. Put timeouts around inference calls, so a hung call raises an error instead of holding GPU time, and apply the same idea to training jobs wherever you can. A timeout turns a silent hang into a loud event that the alerts can catch.

A reasonable response, in order, is to alert, restart the workload, drain the node, and replace the GPU if the hang returns. Each step costs more than the one before it. A restart is quick, and it may clear a stuck process. Draining moves the work off the node so that other jobs can keep running. Replacing the GPU takes the most effort, and it is the step that fixes bad hardware.

Write the three steps into the runbook, along with the signs that tell the on-call engineer when to move from one step to the next. Without those signs, the engineer ends up guessing in the middle of the night, and guessing is how a small hang becomes a long outage.

---

## 2. Network failures

![Network failures in a training cluster with the first action for each](./img/pre-network-failures.jpg)

*Figure 17.7.2. Read the first error, not the last, because healthy ranks often print the timeout.*

### 2.1 The network failure catalogue

Picture a training run across many nodes where one switch uplink fails and half the ranks stop hearing from the other half. Network problems hit distributed training because every GPU depends on its neighbours. A rank is one process in a distributed job, usually one per GPU. When one link slows or drops, every rank that waits on it slows as well. In the same Meta record, network switches and cables caused 35 of the 419 interruptions, which is 8.4 percent. The table lists the network failures this chapter covers. Start from the symptom column.

| Failure mode | Symptom | Detect | First action |
|---|---|---|---|
| NCCL timeout | Training step hangs | PyTorch watchdog line "Watchdog caught collective operation timeout" in the rank logs | Find the first rank that logged an error, see section 2.2 |
| NCCL error | Training step fails | `NCCL WARN` lines in the rank logs, with `NCCL_DEBUG=WARN` | Read the first error, not the last |
| InfiniBand or RoCE port errors | Slow collectives | Port error counters from the fabric manager or the node exporter InfiniBand collector | Compare both ends of the link, replace the cable or transceiver |
| Network partition | Multi-node training fails | Probe failures between node groups, for example `probe_success == 0` from the blackbox exporter | Locate the failed switch or uplink |
| DNS failure | Service discovery fails | CoreDNS `SERVFAIL` or `NXDOMAIN` response rates | Check the CoreDNS pods and upstream resolver |
| Load balancer or ingress failure | External traffic not routed | 5xx rate spike at the gateway | Check the controller and backend health |
| Mesh mTLS failure | Handshake errors between services | Proxy logs and the mesh's handshake failure counters | Check certificate expiry first |

### 2.2 The NCCL timeout

Picture a job of many GPUs that goes quiet in the middle of a step, with a single watchdog line in the logs. NCCL, the NVIDIA Collective Communications Library, is the library that moves data between GPUs. An NCCL timeout happens when one collective operation, such as an all-reduce, runs past its time limit. A collective operation is a step where every GPU in the job exchanges data with the others. An all-reduce adds up values from every GPU and gives each GPU the total. Every GPU in the job waits on that operation, so the whole training step stalls. The timeout is the symptom you see first. The cause can be the network, or it can be a single rank that crashed, so check your peer ranks before you blame the fabric.

That second case matters, and it is easy to miss. When one GPU rank hits an error, the other ranks can hang waiting for it, so the ranks that print the timeout are often the healthy ones. The GPU that actually failed may print nothing at all. Meta's record lists 7 NCCL watchdog timeouts, 1.7 percent of the unexpected interruptions, a small share, but each one stalls the whole job. The watchdog is a timer inside PyTorch that gives up on a stuck collective and reports it.

```python
# code/part17/snippets/nccl_timeout.py
"""Collective timeouts in PyTorch are set on the process group, not through an NCCL_TIMEOUT environment variable
(PyTorch ignores that name). Requires GPUs and torchrun, so this file is syntax-checked only."""
import os
from datetime import timedelta

import torch
import torch.distributed as dist
from opentelemetry import trace

os.environ.setdefault("TORCH_NCCL_ASYNC_ERROR_HANDLING", "1")   # PyTorch 2.15 default is 3 (tear down only); 1 also aborts the communicator
dist.init_process_group(backend="nccl", timeout=timedelta(minutes=10))
tracer = trace.get_tracer(__name__)

tensor = torch.ones(1024, device="cuda")
with tracer.start_as_current_span("all-reduce"):
    dist.all_reduce(tensor)       # raises (and the watchdog aborts the job) if the collective does not finish in 10 minutes
```

The snippet sets the timeout to 10 minutes, which is the 600 seconds used in the policy below. Read it in two parts. The first part is the process group timeout, which tells the watchdog how long a collective may run. The second part is the error-handling setting, which makes the job abort instead of hanging, as the comments explain. Together they turn a silent stall into a crash that the alerts can see.

A simple policy sets the NCCL timeout to 600 seconds, alerts on any NCCL timeout in the logs, and investigates the network first. Restart the workload only if the timeout keeps coming back. The order matters. An alert tells the team that something stopped. The investigation tells them whether the network is the cause, and a restart before that can wipe out the evidence the investigation needs.

### 2.3 The network partition

Picture a multi-node training job where the ranks in one rack suddenly stop hearing from the ranks in another rack. A network partition splits the cluster into two halves that cannot reach each other. Multi-node training stops, because the ranks on one side wait for peers they can no longer reach. The detection signal is a failed ping between nodes, and the alert is critical. A partition looks the same as a dead host from one side, so you need a second viewpoint before you decide which one you have.

One quick check is an Ansible ping across all hosts. Ansible is a tool that connects to many machines and runs a simple command on each one. A host that does not answer is either on the other side of the split or simply down, so you need to tell those cases apart. Run the check from a host on each side of the suspected split. If the set of unreachable hosts changes with the viewpoint, you have a partition. If the same host is unreachable from everywhere, that host is probably down. Run it from a host you trust.

```bash
# Check which hosts this machine can reach. Run it from a host on each side of the suspected split.
ansible all -m ping
# expected: the set of unreachable hosts differs depending on where you run it
```

A GPU that shows much lower utilisation than its peers may have dropped out of the NCCL group. Look in the logs for the line `WARN NCCL_COMM_FAILURE`. That line is easy to overlook, so set `NCCL_DEBUG=WARN` to make silent errors visible. The setting is cheap to leave on, and it is the first place to look after an unexplained slowdown.

When the ping fails, alert, investigate the fabric, restart the affected workloads, and drain the affected nodes. Work in that order, and write down what you found at each step. The record helps the next on-call engineer who meets the same symptom.

---

## 3. Storage failures

![Two side-by-side panels: a failing read stops the job at once, while a slow read lets the job limp along with idle GPUs.](./img/g-333.jpg)
*Figure 17.7.V. A failed read and a slow read need different responses, so find out which one you have first.*


### 3.1 The storage failure catalogue

Picture a training job that reads its data from object storage and suddenly starts waiting at every batch. Storage failures either stop a job from starting or slow it down while it runs. Training reads its data from object storage or a shared filesystem, so an outage there starves the GPUs. A read error and a slow read need different alerts, which is why the table separates them. The object storage metric names in this section are illustrative, because every client library names its counters differently. Object storage is a service that keeps files as objects in buckets, and a client library is the code your job uses to talk to it.

Read the table with the running job in mind. A read that fails stops the job at once, while a read that is slow lets the job limp along with idle GPUs. The two need different responses, so ask first whether the job is failing or only slowing down.

| Failure mode | Symptom | Detect | First action |
|---|---|---|---|
| Object storage 5xx | Training cannot read data | Your object store client's error counter by status class (the metric name depends on the client) | Switch to a replica region if you have one |
| Object storage 4xx | Reads fail for one job | Same counter, 4xx class, plus the 403 in the job log | Check the job's credentials and bucket policy |
| Object storage latency | Training is slow, GPUs wait | p99 of the client's request duration | Check regional status, then the egress path |
| Shared filesystem failure | Mounts hang, reads fail | Mount errors in the kernel log, stalled processes in D state | Check the filesystem servers, then remount |
| Local disk full | Pods evicted or fail to start | `node_filesystem_avail_bytes` below 10 percent of size | Find the writer, clean up, resize |
| Disk I/O error | Slow or failing writes | `I/O error` lines in the kernel log, SMART status | Drain the node and replace the disk |
| PVC not bound | Pod stays Pending | `kube_persistentvolumeclaim_status_phase{phase="Pending"} == 1` | Check the storage class and provisioner events |

### 3.2 The object storage 5xx

Picture a data loader that asks the object store for the next batch and gets an error back instead of the bytes it wanted. A 5xx error means the object storage service failed to answer. The training job asks for the next batch of data and gets an error back instead. The detection signal is the `s3_errors_total` metric, and the query below counts the 5xx rate over five minutes. In HTTP, a 5xx status code means the server failed, while a 4xx code means the request itself was wrong.

```promql
# The S3 5xx rate
sum(rate(s3_errors_total{status=~"5.."}[5m]))

# Alert: 5xx rate > 0
sum(rate(s3_errors_total{status=~"5.."}[5m])) > 0
```

The alert in that example fires on any 5xx at all. That is a deliberately sensitive starting point, so tune the threshold to the normal error rate of your traffic. A small background rate of errors is normal for a busy service, and an alert that fires on it every hour teaches people to ignore it. When the outage lasts, switch to a backup region if you have one. If you do not, wait for the service to recover while the job holds its state.

### 3.3 The local disk full

Picture a node whose disk fills overnight, because a container writes logs without any limit. A full disk stops a workload in an ordinary way. Logs, caches, and checkpoints all grow on the node's disk, and once the disk fills, new work cannot start. A checkpoint is a saved copy of the model's state, written so that a job can resume after a failure. The detection signal is the `node_filesystem_avail_bytes` metric, which tells you how much space is left.

```promql
# The available disk space per node
node_filesystem_avail_bytes{mountpoint="/"}

# Alert: disk space < 10%
node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1
```

The example alert fires below 10 percent free space, which is a starting point. A node that writes large checkpoints may need more margin, because one big write can use up the rest of the disk in a single step. When the alert fires, find the workload that is filling the disk. Check the largest directories first, so you clean up the right thing. Then clean up its logs, resize the disk, and drain the node only if you cannot free enough space safely.

---

## 4. Scheduler failures

### 4.1 The scheduler failure catalogue

Picture a pod that sits in Pending for a long time while the team cannot tell whether the cluster is full or the pod itself is broken. Scheduler failures leave a pod waiting or kill it before it does useful work. Your first question is whether the pod is waiting for capacity, or whether it started and then died. The table below groups the failures by symptom, so you can start from what the pod shows.

Two questions split this table in half. Is the pod waiting for something, such as a free GPU or a slot in a queue? Or did it start and then die? Answering the first question tells you whether to look at the scheduler or at the workload itself.

| Failure mode | Symptom | Detect | First action |
|---|---|---|---|
| Container OOMKilled | Pod restarts, exit code 137 | `kube_pod_container_status_last_terminated_reason{reason="OOMKilled"} == 1` | Raise the memory limit or reduce host memory use |
| GPUs all allocated | Pod Pending | `kube_pod_status_phase{phase="Pending"}` for more than 5 minutes, scheduler event "Insufficient nvidia.com/gpu" | Check queue position and quota |
| Image pull failure | Pod stuck before start | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` | Check name, tag, rate limit, pull secret |
| Node not ready | Pods Pending or evicted | `kube_node_status_condition{condition="Ready",status="false"} == 1` | Check the kubelet and the node, drain if needed |
| Preemption loop | Job restarts repeatedly | Preemption events in the job's namespace | Check priority classes and queue quota |
| Quota exhausted | Job waits in the queue | Kueue pending workloads per ClusterQueue | Check team quota and borrowing |

### 4.2 OOMKilled is host memory, not GPU memory

Two different out-of-memory failures look alike in a ticket. A ticket that says the job ran out of memory could mean either one, and the fix for each is different. When the container uses more host memory than its limit, the kernel's cgroup memory controller kills it. A cgroup is the Linux mechanism that limits what a container may use. Kubernetes records the reason `OOMKilled` with exit code 137. When the application asks the GPU for more memory than it has, the CUDA runtime raises an error such as `CUDA out of memory` inside the application, and the pod usually exits with an ordinary error. CUDA is NVIDIA's programming platform for GPUs. The first kind shows up in pod status. The second kind shows up only in the application log, so read the log before you change the limit.

```promql
# Containers whose last termination was an OOM kill
kube_pod_container_status_last_terminated_reason{reason="OOMKilled"} == 1
```

For an OOMKilled pod, check the memory limit against what the workload really uses. Dataloader workers and pinned host buffers both count against host memory, so look at them too. Then raise the limit or reduce the use. For a CUDA error, shrink the batch or the model, or use a larger GPU. Do not raise the container memory limit to fix a CUDA out-of-memory error, because that limit lives in host memory and GPU memory is a different pool.

### 4.3 The image pull failure

Picture a rollout that starts on a busy afternoon, and the new pods never leave the pending state because they cannot fetch their image. An image pull failure leaves a pod stuck before its container starts. Three causes are common. The image name may be wrong, with a typo or a missing tag. The registry may be rate limiting you, as Docker Hub does for anonymous pulls. Or the pull may time out on the network. The detection signal is the `ImagePullBackOff` reason in the pod status. Kubernetes shows that reason while it waits and retries the pull.

```promql
# The pods that are ImagePullBackOff
kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}

# Alert expression; set `for: 5m` on the rule
count by (pod, namespace) (kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}) > 0
```

Start by checking the image name and tag, because that is the cheapest fix. Then check the pull rate limit, and configure an image pull secret if the registry requires authentication. A pull secret is a stored credential that lets the cluster log in to a private registry. The five-minute window is an example, so choose the wait that suits your deploys. A short window catches problems fast but may fire during normal slow pulls.

---

## 5. Container image failures

### 5.1 The container image failure catalogue

Picture a deploy that stops halfway, because the admission check rejects a pod that carries an unsigned image. A container image can fail at the registry, at the admission check, or during a security scan. Each failure leaves a different trace, so read the event or log that names the stage first. The admission check is the gate the cluster runs before it accepts a new pod. The table lists the failures this chapter covers, along with the signal for each.

| Failure mode | Symptom | Detect | First action |
|---|---|---|---|
| Image not signed | Pod rejected | Admission controller deny event | Fix the signing step in CI |
| Signature mismatch | Pod rejected | Admission controller deny event | Investigate the pipeline, see section 5.2 |
| Pull rate limit | ImagePullBackOff | Pull error text in the pod events | Use a mirror or authenticated pulls |
| Digest mismatch | Pod fails to start | Pull error naming the digest | Re-push from CI, never edit the registry by hand |
| Known CVE | Runs with a vulnerability | Scanner report, for example Trivy | Rebuild on an updated base image |
| Registry storage full | Pushes fail | Registry metrics and push errors | Prune old tags |

### 5.2 The image signature mismatch

Picture a pod that will not start, and the event says the image signature could not be verified. A signature mismatch is the failure you should treat with the most care. The image was signed, but the signature no longer matches the image. The admission controller then refuses to start the pod, which is the behaviour you want. Admission webhooks can check for signed images before a pod runs, so this check fits into the cluster itself. A signature is a cryptographic proof that the image came from a known pipeline and has not changed since it was signed.

```bash
# Detect an image signature mismatch
kubectl get events -n mlops --field-selector reason=Failed
# expected: "Failed to verify signature" event
```

The exact event text depends on your admission controller, so confirm the wording in your own cluster before you write an alert on it. Alert on any mismatch, investigate the signing pipeline, and rotate the signing key if you think it was exposed. Rotating a key means issuing a new one and retiring the old one. Never bypass the admission controller to get a pod running, because the refusal is the protection working as designed.

### 5.3 The image CVE

Picture a scanner that flags a library in an image that has been running in production for months. An image CVE means the image carries a known vulnerability. CVE is the standard identifier for a published security flaw. The workload keeps running with that weakness until the image is rebuilt. Scanning is the way you find these, and the Trivy command below scans one image. Trivy is an open-source scanner that reads the packages inside an image and matches them against known flaws.

```bash
# Run Trivy on the image
trivy image my-image:v1
# expected: list of CVEs with severity
```

Keep one point in mind. An image that passed its scan at pull time can gain new CVEs later, so scans must repeat on a schedule. New flaws are published after an image is built, and a scan that ran once tells you little about the months that follow. A reasonable policy is to run Trivy on every image in CI, the automated build pipeline, alert on any CVE at HIGH severity or above, and rebuild on an updated base image. The severity cut-off is an example you can adjust.

---

## 6. Model serving failures

### 6.1 The model serving failure catalogue

Picture a chat assistant that suddenly gives strange answers while every health check stays green. Model serving failures reach users in two ways. Some crash the request, so the user gets an error. Others return a wrong answer with no error at all, and you will not see those in your error logs. The table separates the two kinds, and the second kind is the one that needs the most attention.

| Failure mode | Symptom | Detect | First action |
|---|---|---|---|
| CUDA out of memory in serving | Requests fail, engine restarts | `CUDA out of memory` in the engine log, restart count | Lower concurrency or the KV cache budget, see section 6.2 |
| Slow requests | Users see long waits | p99 time to first token and inter-token latency against the SLO, see chapter 20.19 | Check queue depth and cache usage first |
| Wrong model version | Output differs from the approved model | Loaded model hash differs from the registry entry | Redeploy the approved version |
| Tokenizer failure | Requests fail on some inputs | Error rate by error type at the gateway | Compare tokenizer files with the model |
| Feature or vector store down | Requests fail or answers degrade | Dependency error rate and its own health check | Fail open or closed by design, then fix the dependency |
| Quality regression | Requests succeed, answers are worse | Quality score from chapter 16.10 below its baseline | Roll back, then retrain |
| Prompt injection | Harmful or leaked output | Guardrail trigger counts | Block, log and review the prompt |

The signal names in this table are generic on purpose, because every engine and gateway names its counters differently. Name the counters after your own stack. See chapters 15.3 and 20.18 for vLLM metrics. vLLM is an open-source engine for serving large language models.

### 6.2 The model OOM

Picture a model server that works well at lunch and crashes during the afternoon peak, when more requests arrive at once. An OOM in serving happens when the model and its working memory no longer fit on the GPU. The model is too large for the GPU's memory, the inference engine's KV cache fills up, and a CUDA out-of-memory crash follows. The KV cache, short for key-value cache, holds the attention data for each request, so it grows with every token the model produces. The detection signal is a counter your engine or gateway exposes for these crashes. The counter name below is illustrative, and the query counts it over five minutes.

```promql
# The inference OOM rate
sum(rate(inference_oom_total[5m]))

# Alert: any inference OOM in the last 5 minutes
sum(rate(inference_oom_total[5m])) > 0
```

Apply backpressure when errors spike. Backpressure means the server pushes back on new work, either by rejecting new requests or by reducing the batch size for a while. That gives the system room to recover, and the users who are turned away get a clear signal to retry instead of a crash. An alert on any inference OOM is a good first step. The lasting fixes are to shrink the KV cache budget, move to a larger GPU, or lower the number of concurrent requests.

### 6.3 The model quality regression

Picture a churn model that returns answers all day, with no errors in the logs at all. A quality regression is the hardest serving failure to see. The request succeeds, the model returns an answer, and the answer is wrong. Nothing in the error logs points to the problem, so the detection signal has to measure quality itself. In this chapter that signal is the `model_quality_score` metric from Chapter 16.10.

```promql
# The model quality score
model_quality_score{model="churn-model"}

# Alert: model quality score < threshold
model_quality_score{model="churn-model"} < 0.85
```

The 0.85 in that alert is an example threshold, so choose the value your own model needs. Set yours from the score your model reached when it was approved, because that score is the baseline the model has already shown it can reach. When the score drops below it, retrain with recent data, check the drift detector, and roll back to the previous model version if the retrain does not recover the score. Drift is the slow change between the data the model learned from and the data it sees now.

---

## 7. Operating the failure mode catalogue

### 7.1 The catalogue structure

Picture an on-call engineer who opens the catalogue in the middle of an incident and has only a few minutes to find a match. The catalogue only helps if the engineer can search it quickly during an incident. Give every failure mode the same fields, so each entry reads the same way. The list below shows the fields this chapter uses. Consistent fields also make the catalogue easy to search with a plain text tool.

```text
Failure mode catalogue fields:
- ID (FM-001, FM-002, ...)
- Name
- Symptom
- Root cause
- Detection signal (metric, log, trace, probe)
- Alert (rule, severity, routing)
- Runbook URL
- Last updated
- Last incident
```

### 7.2 The catalogue update

The incident is closed, and the post-mortem says the runbook pointed the on-call engineer the wrong way. Update the catalogue at the end of every incident. Add a new failure mode if the incident did not match one. Change the runbook if the fix changed, and record the date of the last incident. The script below does this from the command line.

```bash
# Update the failure mode catalogue after an incident
python code/part17/update_catalogue.py \
  --incident-id INC-2024-03-15-001 \
  --failure-mode FM-001 \
  --runbook-url https://wiki.example.com/runbooks/gpu-memory-pressure \
  --last-incident 2024-03-15
```

Keep the catalogue in Git. The script writes its change as a commit, and a reviewer approves that commit in a pull request. That gives you a history of how the catalogue changed over time. The history answers a question that comes up often after an incident, which is when a runbook was last changed and by whom.

### 7.3 The catalogue review

Picture an on-call engineer who follows a runbook link and finds steps written for a cluster that was retired last year. A stale catalogue sends people to runbooks that no longer work. Review it on a schedule, and this chapter suggests quarterly. The review flags failure modes that have not appeared in the last 90 days, failure modes that keep coming back, and new failure modes from the latest vendor releases. The 90-day window is an example, so set it to match how often your incidents happen.

```bash
# Review the failure mode catalogue
python code/part17/review_catalogue.py \
  --catalogue planning/failure_modes/catalogue.yaml \
  --staleness-threshold-days 90
# expected: a list of stale failure modes; a list of repeated failure modes; a list of new failure modes
```

---

## 8. How it fails

Picture an on-call engineer who opens the catalogue during a page and finds that the failure is not listed. Six patterns come back again and again when the catalogue or its alerts stop helping. Each pattern below describes what you see, what usually causes it, and what to do about it.

### 8.1 "The on-call cannot find the failure mode in the catalogue"

The on-call engineer is paged and searches the catalogue. The failure mode is not there, so the engineer starts debugging from scratch, and the minutes add up while the users wait.

The cause is an incomplete catalogue. Either the team never wrote this failure mode down, or the discovery step missed it. Both are common when a team moves quickly.

After the post-mortem, add the failure mode. Give it a detection signal, an alert, and a runbook, so the next on-call engineer finds it. When you write the entry, use the words an on-call engineer would search for, not the words the vendor uses.

### 8.2 "The detection signal is wrong"

The alert fires on every small variation in the metric. The on-call engineer starts ignoring it, and then the real failure slips past without a response.

The signal is too sensitive, the threshold is too low, or the alert is misconfigured. Any of the three produces the same flood of noise.

Tune the signal, raise the threshold, add hysteresis, and measure the alert's precision and recall. Hysteresis means the condition has to hold for a while before the alert fires, and has to clear for a while before it resolves, so brief wobbles do not page anyone. Precision is the share of alerts that were real, and recall is the share of real failures the alert caught. Too many critical alerts burn out on-call engineers and let false positives hide real events. Tune each alert until it is worth a page.

### 8.3 "The runbook is missing the recovery step"

The on-call engineer follows the runbook step by step. The recovery step fails, and the incident escalates while the engineer is still at the keyboard.

The runbook was not updated after the last incident, so the recovery step has since changed. A runbook is only as good as its last review.

Update the runbook after every incident, review it quarterly, and automate a freshness check. Before you trust a runbook during an incident, check when someone last changed it. An old date is a reason to ask the team, not a reason to skip the check.

### 8.4 "The failure mode cascades"

A GPU fails, the failure spreads to its node, the node failure spreads to the cluster, and the cluster SLO is breached.

Failure isolation is missing, so the failure travels along the dependency chain. Each link passes the problem to the next one, much like a row of dominoes.

Drain the node when its GPU fails. Add circuit breakers, so a workload stops calling a failing service. A circuit breaker is a switch that cuts calls to a service that keeps failing, and it closes again once the service recovers. Add bulkheads, so one team's failure does not reach another team. A bulkhead is a wall between groups of resources, so trouble stays in one compartment. Anti-affinity rules spread pods across failure domains and limit the damage from one disturbance, though they cannot remove the disturbance itself.

### 8.5 "The alert is inhibited at the wrong moment"

A less important alert hides a critical one. The on-call engineer never sees the critical alert, and the first sign of trouble is a customer complaint.

The inhibit rule is too broad, or it matches the wrong alerts. An inhibit rule tells Alertmanager to mute one alert while another is firing. That is useful, and it becomes dangerous when the match is loose.

Review the inhibit rules and check that each one matches only the alerts it should. If you cannot explain why an alert was hidden, read the inhibit rules first. Add an integration test that fires both alerts and checks which one reaches the on-call engineer. Also keep an alert that always fires under normal conditions and pages when it goes quiet. That alert tells you when the alerting path itself has failed.

### 8.6 "The catalogue is stale"

The catalogue links to runbooks that are gone, metrics that no longer exist, and vendors that have changed. The on-call engineer trusts the page and loses time to each dead link.

Nobody updated the catalogue after the last incident, and nobody reviewed it on schedule. The gap between the catalogue and the cluster grows quietly.

Update the catalogue after every incident, review it quarterly, and automate the freshness check. A freshness check is a small script or CI step that flags entries whose last update is too old.

---

## 9. Hands-on lab

Picture the first day the cluster runs a real AI workload. Nobody has a catalogue yet, and the on-call engineer has no runbook to open. Work through this lab in order. It builds the failure mode catalogue, configures the detection signals, and checks the on-call integration. The commands were not run on hardware for this book, so treat each expected output as something to confirm on your own cluster.

### 9.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+).
- Helm 3 for installing the alert routing.
- Prometheus installed (Chapter 17.2).

### 9.2 Step 1: create the failure mode catalogue

Start with one entry and add the rest as your failures teach you what matters. Picture the first page about a double-bit error, where the on-call engineer needs a symptom, a signal and a runbook in one place. The first entry below covers an uncorrectable GPU memory error, which is a double-bit error that the GPU cannot repair.

```bash
# Create the catalogue
mkdir -p planning/failure_modes
cat > planning/failure_modes/catalogue.yaml <<EOF
- id: FM-001
  name: GPU ECC Double-Bit Error
  symptom: Data corruption
  root_cause: GPU memory failure
  detection_signal: DCGM_FI_DEV_ECC_DBE_VOL_TOTAL
  alert: GPUDoubleBitECCError
  severity: critical
  runbook_url: https://wiki.example.com/runbooks/gpu-ecc-dbe
EOF
```

### 9.3 Step 2: configure the detection signals

Picture a set of alert rules sitting in a file that Prometheus has never read. Load the GPU fault-signal rules from chapter 17.4 as a PrometheusRule, as that chapter's lab shows. A PrometheusRule is the Kubernetes object that tells Prometheus which alert rules to load. Check the file first with promtool, which reads the rules and reports any syntax errors before they reach the cluster. After Prometheus reloads, the rules should be active.

```bash
promtool check rules code/part17/gpu_alerts.yaml
# expected: SUCCESS: 13 rules found
```

### 9.4 Step 3: verify the runbook integration

An alert without a runbook link leaves the on-call engineer with nothing to do. Check that every alert carries a runbook URL. The command below forwards the Alertmanager port, which is how your laptop reaches the Alertmanager running in the cluster, and then lists each alert with its runbook link.

```bash
# Query Alertmanager
kubectl -n monitoring port-forward svc/alertmanager-operated 9093:9093 &
curl -s http://localhost:9093/api/v2/alerts | jq '.[] | {alertname, runbookURL}'
# expected: every alert has a runbook URL
```

### 9.5 Step 4: simulate a failure mode

Picture a quiet test node that is safe to break. Inject a fault on it with DCGM, as chapter 17.4 does, and watch the matching row of the catalogue come alive. The row is only useful if its alert fires, so this step checks the whole path from the GPU to the page. Never inject faults on a production GPU.

```bash
dcgmi test --inject --gpuid 0 -f 202 -v 99999
# expected: Successfully injected field info. The PCIe replay alert fires once the exporter reads the same host engine.
```

### 9.6 Step 5: verify the on-call runbook

A runbook that loads but gives no next step is as bad as a missing one. Open the runbook from the first alert, and check that it loads and gives a clear next step. A runbook that opens to an empty page fails this check.

```bash
# Click the runbook URL in the alert
open "$(curl -s http://localhost:9093/api/v2/alerts | jq -r '.[0].annotations.runbookURL')"
# expected: the runbook opens in the browser
```

### 9.7 Step 6: review the catalogue

The review is the last check, and it tells you whether the catalogue is still alive. Run it with the 90-day window from Section 7.3. Treat that window as an example, and change it to match your own review cycle.

```bash
python code/part17/review_catalogue.py \
  --catalogue planning/failure_modes/catalogue.yaml \
  --staleness-threshold-days 90
# expected: a list of stale failure modes; a list of repeated failure modes
```

### 9.8 What to record

Five questions show whether the catalogue is ready for on-call use. Answer them from the stack you just built:

1. What is the current number of failure modes in the catalogue?
2. What is the current number of stale failure modes?
3. What is the most recent failure mode added to the catalogue?
4. What is the current ECC error rate per GPU?
5. What is the current alert firing rate per failure mode?

If an answer takes longer than your on-call engineers can afford, the catalogue is not yet a production service. Treat that as a reason to keep improving the entries, not as a sign that the idea has failed.

---

## Exercises

1. **Add a new failure mode to the catalogue.** Think about the last incident your team handled. Did it match an entry in the catalogue? Add it with its detection signal, alert, and runbook. *Solution sketch:* the YAML fields from Section 7.1, the post-mortem, the alert rule, and the runbook.
2. **Add a cascade detection.** Picture one GPU failure that drags down its node and then its service. Write an alert that fires when several failure modes fire together. *Solution sketch:* a Prometheus alert that matches several failure modes at once, with critical severity.
3. **Add a failure isolation pattern.** A GPU fails on a node that is running a job. Configure the platform to drain that node. Then check that the workload reschedules onto a healthy node. *Solution sketch:* a Kubernetes controller that watches GPU health, drains the node when the GPU is unhealthy, and lets the workload reschedule.
4. **Add a runbook freshness check.** A runbook can sit untouched for a long time. Set up a CI step that fails when a runbook has not changed in 30 days. The 30-day window is only an example. *Solution sketch:* the CI step reads the runbook's Git history and fails when the last change is older than the window.
5. **Add a catalogue review report.** Your team needs a quarterly report before each review meeting. Generate a report that lists stale failure modes, repeated ones, and new ones from the latest vendor releases. Use the report to plan your next review. *Solution sketch:* a Python script that reads the catalogue and writes the report, which the platform team reviews.
6. **Add a per-team failure mode view.** Each team wants to know which failures touch its own workloads. Build a dashboard that shows each team its own failure modes. That dashboard becomes the team's view of cluster health. *Solution sketch:* a Grafana dashboard that filters alerts by team, with one panel per view and a data source behind each panel.

---

## Checkpoint questions

<details><summary>1. A training step hangs and the logs show an NCCL timeout. The network team says the fabric looks fine. What do you check before blaming the network?</summary>
Check the peer ranks. When one GPU rank hits an error, the other ranks can hang waiting for it, so a crashed rank looks like a network timeout. Search the logs for `WARN NCCL_COMM_FAILURE` and set `NCCL_DEBUG=WARN` so silent errors show. If every rank is healthy, investigate the network.
</details>

<details><summary>2. A GPU's single-bit ECC error rate climbs, and two hours later the first double-bit error appears. What do you do?</summary>
A double-bit error cannot be corrected, so the GPU may be corrupting data. Cordon and drain the node, flag the outputs of jobs that ran there, and replace the GPU. The rising single-bit rate was the earlier warning, which is why chapter 17.4 alerts on its week-over-week growth.
</details>

<details><summary>3. A multi-node job fails, and a ping between two nodes fails. How do you tell a network partition from a dead host?</summary>
Run `ansible all -m ping` from a host on each side of the suspected split. In a partition, the set of unreachable hosts differs depending on where you run the check. A host that is simply down is unreachable from everywhere. Run it from a host you trust.
</details>

<details><summary>4. A churn model returns answers all day, no errors appear in the logs, and `model_quality_score` has fallen below 0.85. What do you do?</summary>
This is a quality regression, which error logs cannot show. Retrain with recent data and check the drift detector. If the retrain does not recover the score, roll back to the previous model version. The 0.85 is an example, so set your own from the score the model had when it was approved.
</details>

<details><summary>5. A pod is killed with the reason `OOMKilled`. Does that prove the GPU ran out of memory?</summary>
No. `OOMKilled` means the container exceeded its host memory limit and the kernel killed it, usually with exit code 137. A GPU out-of-memory error is raised by the CUDA runtime inside the application and shows in the application log. Check the host memory limit and the dataloader and pinned-buffer use, and do not raise the container limit to fix a CUDA error.
</details>

<details><summary>6. A pod will not start and the events show "Failed to verify signature". What do you do and what must you never do?</summary>
Alert on any mismatch, investigate the signing pipeline, and rotate the signing key if you think it was exposed. Confirm the exact event text in your own cluster first. Never bypass the admission controller to get the pod running, because refusing the pod is the behaviour you want.
</details>

<details><summary>7. Why does one crashed rank stall the whole training job, and what does the timeout setting change?</summary>
Every GPU waits on each collective, so one missing rank blocks them all. The timeout is set on the process group, here 10 minutes, and PyTorch ignores an `NCCL_TIMEOUT` environment variable. With async error handling on, the job aborts after the timeout instead of hanging forever.
</details>

<details><summary>8. Why does a GPU hang go unnoticed until the job stalls?</summary>
Nothing crashes. The workload still runs, kernels sit in the queue, and the GPU makes no progress. The check needs two signals, one from the GPU and one from the job: utilisation stays high while the step counter stays flat for several step times. The SM clock alone cannot show a hang. Timeouts around calls make a hang fail fast.
</details>

<details><summary>9. Why must image scans repeat on a schedule?</summary>
An image that passed its scan at pull time can gain new CVEs later, because new vulnerabilities are found after the image was built. A single scan at pull time cannot catch those. Run Trivy on every image in CI, repeat the scans, alert on HIGH severity or above, and rebuild on an updated base image.
</details>

<details><summary>10. Why does a GPU failure turn into a cluster SLO breach, and what stops it?</summary>
Without failure isolation, the failure travels along the dependency chain from the GPU to the node and then to the cluster. Drain the node when its GPU fails, add circuit breakers so workloads stop calling a failing service, and add bulkheads between teams. Anti-affinity limits the damage but cannot remove the disturbance.
</details>

<details><summary>11. Why is a model quality regression the hardest serving failure to detect?</summary>
The request succeeds and the model returns an answer, so nothing appears in the error logs. The detection signal has to measure quality itself, which is the `model_quality_score` metric from Chapter 16.10. Without that metric the failure is invisible.
</details>

<details><summary>12. An alert fires on every small variation and the on-call ignores it. How far do you loosen it, and what do you give up?</summary>
Tune the signal, raise the threshold, and add hysteresis. Then measure the alert's precision and recall. You give up some sensitivity, so a real failure could fire later. That is acceptable when too many alerts hide real events. Tune each alert until it is worth a page.
</details>

<details><summary>13. A GPU hang returns after a restart. When do you restart, drain or replace, and what does each cost?</summary>
The suggested order is to alert, restart the workload, drain the node, and replace the GPU if the hang returns. A restart is cheap but does not fix hardware. Draining removes capacity until the repair. Replacing the GPU costs the most but is the only fix for a bad part.
</details>

<details><summary>14. A model server hits OOM errors. When do you use backpressure and when do you change the deployment?</summary>
Backpressure rejects new requests or reduces the batch size for a while, which gives the system room to recover during a spike. You give up some requests. The lasting fixes are to shrink the KV cache budget, move to a larger GPU, or lower the number of concurrent requests.
</details>

<details><summary>15. The disk alert fires below 10 percent free space. When would you set a higher margin, and what do you give up?</summary>
A node that writes large checkpoints may need more margin, because the disk can fill before anyone reacts. A higher margin gives earlier warning but fires more often and wastes usable space. The 10 percent is a starting point, so tune it to your workload.
</details>

<details><summary>16. In Meta's 54 days of Llama 3 405B pretraining, 419 interruptions were unexpected. Faulty GPUs caused 148 and HBM3 memory 72. What share is that together?</summary>
Add the counts, 148 plus 72, which is 220. Divide by 419 to get 52.5 percent, with 35.3 percent from faulty GPUs and 17.2 percent from HBM3. More than half of all unexpected interruptions came from those two causes. Network switches and cables added 35, which is 8.4 percent.
</details>

<details><summary>17. The disk alert is `node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1`. At what free space does it fire on a 2 TB disk?</summary>
The ratio is below 0.1 when free space is under 10 percent of 2 TB. Ten percent of 2,000 GB is 200 GB. So the alert fires when less than about 200 GB is free.
</details>

<details><summary>18. In the example storm, why would an alert on 100 single-bit errors per hour miss the warning?</summary>
The single-bit rate reaches only 50 per hour in the first hour, and the first double-bit error appears at two hours. The rate never reaches 100 before the double-bit page, so the fixed threshold adds nothing. Alerting on week-over-week growth of the single-bit count, as chapter 17.4 does, catches the climb earlier.
</details>

<details><summary>19. Pods are stuck in `ImagePullBackOff`. What do you check first, second and third?</summary>
First check the image name and tag, because that is the cheapest fix. Second check whether the registry is applying a pull rate limit, as Docker Hub does for anonymous pulls. Third configure an image pull secret if the registry requires authentication. A network timeout is the other common cause.
</details>

<details><summary>20. A real critical failure happened and the on-call never saw the alert. What do you check, in order?</summary>
First read the inhibit rules, since a less important alert may be hiding the critical one. Second check that each rule matches only the alerts it should. Third add an integration test, and add an always-firing alert that pages when it goes quiet, so a failure of the alerting path becomes visible.
</details>

## Sources and review notes

- NVIDIA Zero-to-Hero Volume 16 (`chapter-08-failure-modes-and-detection.md`). Source for the GPU hardware failures, the network failures, the storage failures, and the detection signals. The wording has been rewritten in the handbook's voice.
- NVIDIA Zero-to-Hero Volume 20. Source for additional failure modes drawn from the broader nvidia-devops corpus.
- *AI Systems Performance Engineering*, Table 4-4 (Meta's Llama 3 405B interruptions). The book prints 30.1 percent for the 148 faulty-GPU interruptions, but 148 of 419 is 35.3 percent, and the other rows use 419 as the base, so this chapter uses 35.3.
- Chapter 10.21 and chapter 17.4 for the Xid tiers, row remapping and the alert rules.
- *Production Kubernetes* (`production-kubernetes`, Chapter 14). Source for the Kubernetes-level failure modes (scheduler, container image) and the operational patterns.

### Cross-references to other handbook chapters

- Chapter 17.4 for the DCGM exporter and the GPU-specific failures.
- Chapter 17.6 for the alerting and SLOs.
- Chapter 11 for the GPU Kubernetes operations.
- Chapter 16.10 for the monitoring and drift.

### Migrated from `nvidia-devops`

The failure mode catalogue operational patterns draw on Volume 16 chapter 8 and Volume 20. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The failure mode catalogue in this chapter is a starting point; specific failure modes depend on the cluster and the workload.
- The detection signals are starting points; specific signals depend on the exporter configuration.
- The alert thresholds are starting points; specific thresholds depend on the production traffic.

### Not verified on live hardware

- The lab in Section 9 is **untested** against a live GKE cluster in this repository.
- The catalogue YAML in the lab is illustrative; production catalogues are larger and more detailed.
- The detection signals in the lab assume the exporters from earlier chapters are installed.

corrected 2026-11-11: TORCH_NCCL_ASYNC_ERROR_HANDLING defaults to 3 in PyTorch 2.15 and 1 is a deliberate non-default choice; source PyTorch 2.15 docs, ProcessGroupNCCL environment variables.

corrected 2026-11-11: Meta Llama 3 paper (arXiv 2407.21783, Table 5) counts sum to 419, so shares are computed as count over 419: faulty GPU 148 is 35.3 percent and faulty GPU plus HBM3 is 220 or 52.5 percent. The paper prints 30.1 percent for the faulty-GPU row and 58.7 percent for all GPU issues, and neither matches its own counts; the 64.0 percent for 268 GPU-category interruptions does match.
