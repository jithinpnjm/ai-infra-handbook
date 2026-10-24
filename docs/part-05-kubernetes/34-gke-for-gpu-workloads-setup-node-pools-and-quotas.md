---
id: "c05-34"
title: "5.34 GKE for GPU workloads: setup, node pools and quotas"
sidebar_label: "5.34 GKE for GPU workloads: setup, node pools and quotas"
sidebar_position: 34
description: "Running GPU workloads on Google Kubernetes Engine: Standard vs Autopilot, GPU machine families, node pool creation with driver installation, taints and scheduling, quotas and reservations, Spot and flex-start, compact placement, GPU sharing and MIG, high-performance networking, monitoring with managed DCGM, cost controls and a verified-flags command reference"
status: "drafted"
tier: "1"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.34 GKE for GPU workloads: setup, node pools and quotas

| | |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP project with GPU quota or a reservation; `gcloud` and `kubectl`. GPU nodes are expensive: set budgets and delete pools after each lab |
| Part | Part 5: Kubernetes |
| Status | Drafted. `gcloud` flag names and values below were checked against the local `gcloud` 584.0.0 `--help` output (offline). Machine-type and accelerator-type names, quotas, and every behaviour claim are from documentation knowledge and are **unverified** against your project. Labs are **untested** |

## Why this matters for AI infrastructure

Google Cloud is one of the three clouds this role touches (alongside CoreWeave and Nebius), and GKE is the managed Kubernetes most teams meet first. Its GPU story combines managed control plane, managed drivers, several consumption models (on-demand, reservations, Spot, flex-start), and specialised networking for large training. The Kubernetes concepts are the same as on bare metal (5.8 device plugins, 5.9 scheduling, Part 11 GPU on Kubernetes), but the operational levers are different: quota is the usual first blocker, node pools are the unit of hardware, and the managed driver and networking stack replace parts of what the GPU Operator and Network Operator do elsewhere (5.33). Interviewers ask how you would stand up GPU capacity on GKE and what can go wrong.

## Prerequisites and outcomes

Needs 5.8 to 5.10, 5.14 (CNI), Part 2 (cloud networking basics) and 4.x (Terraform) for the IaC section. After this chapter you can:

- Choose between GKE Standard and Autopilot for GPU work, and between consumption models.
- Create a GPU node pool with the right machine type, accelerator, driver version, location, taints and labels.
- Request and verify GPU quota, understand reservations and why quota errors differ from stockout errors.
- Schedule Pods onto GPUs correctly, and share GPUs with time-sharing, MPS or MIG when appropriate.
- Set up compact placement and high-performance networking for multi-node training.
- Enable GPU monitoring and set cost guardrails; express it in Terraform.

## 1. Standard vs Autopilot

| | Standard | Autopilot |
|---|---|---|
| Node management | You create and size node pools | Google provisions nodes from Pod requests |
| GPU choice | Any supported machine/accelerator you can get | Limited set; requested through Pod nodeSelectors |
| Customisation (host settings, DaemonSets, privileged Pods, custom drivers, special networking) | Wide | Restricted |
| Billing | Per node (VM plus GPU) | Per Pod resource request |
| Best for | Large training, special networking, reservations, control | Simpler inference and bursty workloads |

Serious multi-node training with RDMA-class networking, reservations and compact placement uses **Standard**. Use Autopilot for smaller or intermittent GPU inference where you do not want to manage nodes. Check the current docs for which GPUs Autopilot offers.

## 2. GPU machine families and accelerators

GPUs on GCE come in two forms:

1. **Accelerator-optimized machine types** where the GPUs are part of the shape. Families include A2 (A100), A3 (H100), A3 Ultra (H200), A4 (B200) and G2 (L4) (names as I recall; verify the current list, new generations appear often). The accelerator count is fixed by the machine type (for example an 8-GPU shape).
2. **General-purpose machine types with attached GPUs** for some older GPU models (T4, V100, P100), where you pick `--accelerator type=...,count=...`.

In `gcloud`, both forms use the same `--accelerator` flag on node pools. Useful discovery commands (these call the API, so they need credentials):

```bash
gcloud compute accelerator-types list --filter="zone:us-central1-a"
gcloud compute machine-types list --filter="name~^a3 AND zone:us-central1-a"
```

Details to verify per generation: GPU memory, NVLink/NVSwitch topology, NIC count and bandwidth, local SSD, supported OS images (Container-Optimized OS vs Ubuntu), minimum GKE version, and which zones carry it.

## 3. Creating a cluster for GPUs

Start with a regional or zonal **Standard** cluster that has a small CPU-only default pool for system components, and add GPU pools separately. A cluster-per-concern approach (CPU system, GPU training) keeps failure domains and costs clear.

```bash
export PROJECT=my-project REGION=us-central1 ZONE=us-central1-a CLUSTER=gpu-lab

gcloud container clusters create "$CLUSTER" \
  --project "$PROJECT" --zone "$ZONE" \
  --release-channel regular \
  --num-nodes 1 --machine-type e2-standard-4 \
  --workload-pool "${PROJECT}.svc.id.goog" \
  --enable-dataplane-v2 \
  --enable-ip-alias \
  --enable-managed-prometheus \
  --monitoring SYSTEM,DCGM
```

Flags verified present in `gcloud container clusters create --help` (584.0.0): `--release-channel`, `--workload-pool` (Workload Identity), `--enable-dataplane-v2` (Cilium-based dataplane, 5.14/5.15), `--enable-ip-alias`, `--enable-managed-prometheus`, and `--monitoring` whose component list includes `DCGM` and `JOBSET` (the help states DCGM requires Google Managed Prometheus). Add `--enable-multi-networking` if you will attach additional NICs to Pods (section 8), `--enable-private-nodes` for private clusters, and review `--enable-shielded-nodes` defaults.

Use Workload Identity rather than node service account keys for any Pod that talks to GCS, Artifact Registry or other Google APIs (5.21 on security).

## 4. Creating a GPU node pool

```bash
gcloud container node-pools create h100-pool \
  --cluster "$CLUSTER" --zone "$ZONE" \
  --machine-type a3-highgpu-8g \
  --accelerator type=nvidia-h100-80gb,count=8,gpu-driver-version=latest \
  --num-nodes 2 \
  --node-locations "$ZONE" \
  --node-labels workload=training \
  --enable-gvnic \
  --placement-type COMPACT \
  --reservation-affinity specific --reservation my-h100-reservation
```

Verified in help: `--accelerator` takes `type`, `count`, `gpu-driver-version` (`default`, `latest`, `disabled`; `latest` only on Container-Optimized OS), `gpu-partition-size`, `gpu-sharing-strategy`, `max-shared-clients-per-gpu`. Also verified: `--placement-type` (`UNSPECIFIED` or `COMPACT`), `--placement-policy` (a named resource policy), `--reservation-affinity` (`any`, `none`, `specific`, `any-reservation-then-fail`) with `--reservation`, `--spot`, `--flex-start`, `--max-run-duration`, `--additional-node-network` (repeatable up to 7 times), `--accelerator-network-profile=auto`, `--enable-gvnic`, `--enable-image-streaming`, `--node-taints`, `--node-labels`, `--node-locations`, `--local-nvme-ssd-block`. The machine and accelerator type strings in the example (`a3-highgpu-8g`, `nvidia-h100-80gb`) are from memory: confirm them with the listing commands.

What happens after creation (documented behaviour, unverified here):

- GKE installs a **GPU driver DaemonSet** automatically when `gpu-driver-version` is not `disabled`; the node then advertises `nvidia.com/gpu` through the GKE device plugin. The help text says that for GKE 1.30.1 and later the default is to install the default driver version, and for earlier versions the default was `disabled`.
- Nodes get labels such as `cloud.google.com/gke-accelerator=<type>`; check `kubectl get node -L cloud.google.com/gke-accelerator`.
- GKE normally **taints GPU nodes** so only Pods that request GPUs land there (`nvidia.com/gpu=present:NoSchedule`) and a built-in admission step adds the matching toleration to Pods that request `nvidia.com/gpu`. Confirm on your cluster with `kubectl describe node`. If you add your own taints (for example to isolate a team) you must add tolerations explicitly.
- GPU nodes cannot live-migrate; host maintenance terminates them. Plan for it (checkpointing, Part 14).

If you prefer the GPU Operator (5.33) on GKE, set `gpu-driver-version=disabled` and let the operator install the driver, or let GKE manage drivers and run the operator without its driver component. Do not let both install a driver on the same node.

### Verify

```bash
gcloud container clusters get-credentials "$CLUSTER" --zone "$ZONE"
kubectl get nodes -L cloud.google.com/gke-accelerator
kubectl describe node NODE | grep -A8 -i "taints\|nvidia.com/gpu"
kubectl apply -f - <<'YAML'
apiVersion: v1
kind: Pod
metadata:
  name: nvidia-smi
spec:
  restartPolicy: Never
  containers:
  - name: c
    image: nvidia/cuda:12.4.1-base-ubuntu22.04
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 1
YAML
kubectl logs nvidia-smi
```

The image tag is an example; use a CUDA base image compatible with the node driver (Part 10 on driver/CUDA compatibility).

## 5. Quotas, reservations and consumption models

Capacity problems come in three flavours. Learn to tell them apart because the fixes differ:

| Symptom | Meaning | Fix |
|---|---|---|
| `QUOTA_EXCEEDED` / "Quota 'NVIDIA_H100_GPUS' exceeded" (name varies) | Your project's quota is too low | Request a quota increase for that GPU model in that region; also the global GPU quotas and CPU/RAM/SSD quotas used by the machine type |
| `ZONE_RESOURCE_POOL_EXHAUSTED` (stockout) | Quota is fine; Google has no free hardware in that zone | Try other zones, another machine type, a reservation, flex-start, or wait |
| Node pool stuck creating / Pods Pending with scale-up not triggered | Autoscaler constraints (max nodes, location policy, resource limits) or a placement constraint | Read the cluster autoscaler events and node pool status |

Quota check commands (API calls):

```bash
gcloud compute regions describe us-central1 --format="yaml(quotas)" | grep -B1 -A1 -i gpu
gcloud quotas info list --project "$PROJECT" --service compute.googleapis.com | grep -i gpu   # if the quotas CLI is installed
```

Consumption models, in rough order of cost and certainty:

1. **Reservation** (specific or any, shared across projects if configured): guaranteed capacity at a committed price. Use `--reservation-affinity specific --reservation NAME`. Large training clusters normally use reservations. Reserved capacity of a very large shape usually comes with a compact placement policy created for it.
2. **Committed use discounts**: price commitments, not capacity guarantees on their own.
3. **On-demand**: pay as you go, subject to stockouts.
4. **Spot**: deeply discounted, preemptible at any time with short notice. For fault-tolerant jobs with checkpoints and for batch inference. Use `--spot` and tolerate the Spot taint behaviour; expect 25 to 30 second preemption notice (verify) which is shorter than most checkpoints take.
5. **Flex-start (Dynamic Workload Scheduler)**: you ask for capacity for a bounded run and GKE provisions it when available, then removes it. Use `--flex-start` with `--max-run-duration`; it integrates with queued provisioning (ProvisioningRequest) and Kueue. Good for short finetunes and evaluation when you lack a reservation. Verified flags exist (`--flex-start`, `--max-run-duration`); verify supported machine types and node pool sizing rules in current docs.

Reservations and quota interact: a reservation does not increase quota, and consuming reservation capacity still needs quota in some configurations. Check the current documentation for your reservation type.

## 6. Scheduling Pods onto GPUs

The basic Pod requests `nvidia.com/gpu`. Typical additions:

```yaml
spec:
  nodeSelector:
    cloud.google.com/gke-accelerator: nvidia-h100-80gb
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
  containers:
  - name: train
    resources:
      limits:
        nvidia.com/gpu: 8
```

Practical rules:

- Request the **whole node's** GPUs for multi-GPU jobs so NVLink-connected GPUs are used together; a Pod asking for 4 of 8 GPUs can leave an awkward remainder.
- Use **Kueue** (queueing, quotas, fair share, preemption) for shared GPU capacity, and JobSet / Kubeflow Trainer or similar for multi-node jobs (Part 14). The help for `--monitoring` lists a `JOBSET` metrics component, which hints at first-party JobSet observability.
- Set `priorityClassName` so critical inference can preempt batch work (5.9).
- Use `topologySpreadConstraints` or node affinity for zone spread of inference replicas; training jobs usually want the opposite (one tight placement group).
- Pull large images quickly: Artifact Registry in the same region, image streaming (`--enable-image-streaming`), and/or pre-pulled images via a DaemonSet or a secondary boot disk with a pre-loaded image.

## 7. Sharing a GPU: time-sharing, MPS, MIG

The `--accelerator` flag includes `gpu-sharing-strategy` and `max-shared-clients-per-gpu`, and `gpu-partition-size` for MIG.

| Technique | How it works | Isolation | When to use |
|---|---|---|---|
| Time-sharing | GPU context-switched between containers; each sees one GPU | Weak (shared memory space is not isolated; no fault isolation) | Many small, bursty inference/dev workloads |
| MPS | Concurrent kernels from multiple processes share SMs | Weak to medium | Throughput for several small processes on one GPU |
| MIG | Hardware partitions with dedicated memory and SMs (A100/H100 class) | Strong | Multi-tenant inference with predictable latency |

Example (MIG, partition name from documentation, verify for your GPU):

```bash
gcloud container node-pools create mig-pool --cluster "$CLUSTER" --zone "$ZONE" \
  --machine-type a2-highgpu-1g \
  --accelerator type=nvidia-tesla-a100,count=1,gpu-partition-size=1g.5gb,gpu-driver-version=default
```

With time-sharing, a Pod's `nvidia.com/gpu: 1` limit consumes one *slice*; nothing stops a slice holder from using all GPU memory. Never use it for tenants you do not trust. Compare with NVIDIA-side options (time-slicing and MPS in the device plugin, MIG manager) in Part 11.

## 8. Networking for multi-node training

For a single-node job, the default VPC networking is enough. For multi-node training, inter-node bandwidth and latency dominate (Part 12). On GKE this involves several pieces; the details depend on the machine family and change between generations, so treat the following as a map and read the current guide for your shape:

- **gVNIC** (`--enable-gvnic`) is required or recommended on high-end accelerator machine types.
- **Multiple VPC networks / NICs**: accelerator-optimized shapes have several NICs dedicated to GPU traffic. GKE exposes them to Pods through **multi-networking** (cluster flag `--enable-multi-networking`, node pool flag `--additional-node-network network=NAME,subnetwork=SUBNET`, repeatable up to 7 times, plus Network and GKENetworkParamSet resources in the cluster). The help also lists `--accelerator-network-profile=auto`, which creates a profile for compatible accelerator machine types; check which machine types it covers.
- **NCCL network plugins**: older A3 shapes use a GPUDirect-TCPX/TCPXO approach with a sidecar and a NCCL plugin; newer shapes use RDMA over RoCE with NCCL's native IB verbs path. Pod specs need the right annotations, the right NCCL environment variables, and sometimes an installer DaemonSet. (From documentation; version-specific.)
- **Compact placement** (`--placement-type COMPACT` or a named `--placement-policy`) keeps nodes in a tight physical cluster to cut hops; it limits maximum pool size and can cause stockouts.
- Validate with **NCCL tests** (`all_reduce_perf`) and compare against expected bus bandwidth for the shape before running real jobs (Part 12/14).

## 9. Autoscaling and upgrades

- **Cluster autoscaler** per node pool: `--enable-autoscaling --min-nodes --max-nodes` (or `--total-min-nodes/--total-max-nodes` with `--location-policy`, both listed in the help). `--location-policy=ANY` favours zones with capacity; `BALANCED` spreads. Scale GPU pools to zero when idle (`min-nodes 0`) if start latency is acceptable.
- **Node auto-provisioning** can create GPU pools on demand within resource limits you configure. Useful for variety, less so for tightly controlled training clusters.
- **Upgrades**: GPU node pools should use surge settings carefully. With no spare GPUs available, `max-surge-upgrade` above 0 may fail for lack of capacity; use `max-unavailable-upgrade` instead and drain with checkpointing. Control windows and exclusions (`--add-maintenance-exclusion-until-end-of-support` exists in node pool help). Use a release channel and test GPU driver changes on a canary pool first, because a driver bump changes the CUDA compatibility story (Part 10).
- Auto-repair of GPU nodes can restart long jobs. Decide deliberately whether to enable it for training pools, and pair with your own health logic (5.32).

## 10. Observability and cost

- `--monitoring SYSTEM,DCGM` with Google Managed Prometheus exports DCGM GPU metrics (utilisation, memory, power, temperature, Xid and ECC where available) into Cloud Monitoring. Or deploy `dcgm-exporter` yourself and scrape with your own Prometheus (5.19, Part 11).
- Alert on: GPU utilisation low for long periods on expensive nodes, Xid errors, ECC errors, Pending Pods that request GPUs, node pool at max, preemptions, autoscaler failures.
- **Cost controls**: budgets and alerts on the project; labels on node pools and Pods for attribution; scale idle pools to zero; use Spot or flex-start for interruptible work; use right-sized shapes; delete lab clusters. Idle reserved GPUs are the biggest silent cost: track reservation utilisation.
- Cloud Logging for nodes and GPU driver install DaemonSet logs; check them first when `nvidia.com/gpu` is missing.

## 11. Terraform sketch (untested)

```hcl
resource "google_container_cluster" "gpu" {
  name     = "gpu-lab"
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 1

  release_channel { channel = "REGULAR" }
  workload_identity_config { workload_pool = "${var.project}.svc.id.goog" }
  datapath_provider = "ADVANCED_DATAPATH"
}

resource "google_container_node_pool" "h100" {
  name       = "h100-pool"
  cluster    = google_container_cluster.gpu.id
  location   = var.zone
  node_count = 2

  node_config {
    machine_type = "a3-highgpu-8g"
    guest_accelerator {
      type  = "nvidia-h100-80gb"
      count = 8
      gpu_driver_installation_config { gpu_driver_version = "LATEST" }
    }
    labels = { workload = "training" }
  }

  placement_policy { type = "COMPACT" }
}
```

Argument names are from the Google provider as I remember it and **must be validated** with `terraform validate` against your provider version. Prefer a module pinned to a version, manage the cluster and the GPU pools in separate states or at least separate modules, and set `lifecycle.prevent_destroy` on anything holding state. See Part 4 on Terraform structure.

## 12. Failure modes and troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| Node pool creation fails with quota error | GPU/CPU/SSD/IP quota | Quota page; error text names the metric |
| Creation fails with resource exhausted | Zone stockout | Another zone, shape or consumption model |
| Nodes up but `nvidia.com/gpu` is 0 | Driver install failed or disabled | Driver installer DaemonSet logs in `kube-system`; `gpu-driver-version`; OS image |
| Pod Pending "Insufficient nvidia.com/gpu" | No node with free GPU, taint/toleration mismatch, wrong selector | `kubectl describe pod`; node taints; autoscaler events |
| Pod runs but cannot see GPU | Missing resource limit; wrong runtime or image | `nvidia-smi` in a minimal Pod |
| Slow multi-node training | No compact placement, wrong NICs or NCCL env, cross-zone nodes | NCCL test, topology, placement policy |
| Job dies randomly | Spot preemption, host maintenance, auto-repair, Xid | Node events, Cloud Logging, DCGM |
| Upgrade stuck | No surge capacity, PDB blocking drain | Upgrade settings, PDBs |
| Unexpected bill | Idle pools, unused reservations, egress | Billing export, labels, utilisation |

## 13. Lab (untested; costs money)

1. Create a project budget alert first.
2. Create a small Standard cluster (`e2-standard-4`, 1 node), then a single-GPU pool with a cheap GPU (for example L4 or T4, whichever your quota allows). Record the exact commands and errors.
3. Run the `nvidia-smi` Pod, then a CUDA sample or PyTorch `torch.cuda.is_available()` Pod.
4. Break it deliberately: remove the toleration, request 2 GPUs on a 1-GPU node, request a GPU type with no quota. Capture each failure message and map it to the table in section 12.
5. Add a time-sharing pool and run 4 Pods against one GPU; observe interference with `nvidia-smi`.
6. Enable `DCGM` monitoring and view GPU utilisation in Cloud Monitoring.
7. Try `--spot` and `--flex-start` pools; note how they differ in scale-up behaviour.
8. Express the cluster and pool in Terraform; run `terraform validate` and `plan`.
9. Delete everything. Verify with `gcloud container clusters list` and billing.

## 14. Interview angles

- Walk me through standing up a GPU node pool on GKE. What do you check first when it fails?
- Quota exceeded vs stockout: how do you tell, and what do you do about each?
- Reservation vs Spot vs flex-start: which for a 3-day 64-GPU training run? A nightly evaluation? Production inference?
- How do GPU drivers get onto GKE nodes, and when would you disable that?
- Time-sharing vs MPS vs MIG: isolation and use cases.
- Why compact placement, and what are its downsides?
- How would you upgrade a GPU node pool when there is no spare capacity?
- How do you make multi-node training network performance predictable on GKE?
- How would you attribute GPU cost to teams?

## 15. Checkpoint questions (30)

1. When do you choose Standard over Autopilot for GPUs?
2. What are the two ways GPUs attach to GCE machine shapes?
3. What does `gpu-driver-version` accept and what does `latest` require?
4. What happens by default for driver installation on recent GKE versions?
5. Which taint is normally on GPU nodes, and who adds the toleration?
6. How do you request a whole 8-GPU node?
7. Name the three capacity problem categories and a fix for each.
8. What does a reservation guarantee, and what does it not change?
9. When is Spot appropriate, and what must the job tolerate?
10. What is flex-start, and which flags did we verify?
11. What does `--placement-type COMPACT` do and what does it limit?
12. Time-sharing vs MIG: isolation difference?
13. What flag partitions a GPU with MIG on node pool creation?
14. What flags attach extra NICs to nodes, and what cluster flag enables Pod access?
15. Why does GPU networking differ between generations?
16. How do you validate inter-node bandwidth before a training run?
17. Why can surge upgrades fail on GPU pools?
18. What is the effect of auto-repair on long jobs?
19. What does `--monitoring SYSTEM,DCGM` need?
20. What GPU metrics and events do you alert on?
21. Why use Workload Identity?
22. Why separate system CPU pool from GPU pools?
23. How would you scale a GPU pool to zero, and what is the cost?
24. How does image pull time affect GPU idle cost, and how do you reduce it?
25. When would you run the GPU Operator on GKE, and what must you disable?
26. What is Kueue used for here?
27. How do you attribute cost per team?
28. Where do you look first when `nvidia.com/gpu` is 0?
29. Which facts in this chapter were verified offline, and which are from memory?
30. How would you structure Terraform for cluster and GPU pools?

## 16. Sources and review notes

- Verified locally: `gcloud container clusters create --help` and `gcloud container node-pools create --help` from Google Cloud SDK 584.0.0 (flag names, accepted values, and the quoted behaviour of `gpu-driver-version`, `--placement-type`, `--reservation-affinity`, `--monitoring`, `--additional-node-network`).
- From Google Cloud documentation, remembered rather than re-read: GPU machine family names, accelerator type strings, taint behaviour, quota names, TCPX/TCPXO and RDMA networking details, Spot notice times, Terraform argument names. Treat these as leads to confirm in the current docs.
- Concept sources: the Kubernetes documentation on device plugins and scheduling GPUs; this handbook's 5.8, 5.9, 5.33, Part 11, 12 and 14.
- Not done: no cluster was created, so no output, error text or cost in this chapter comes from a real run.
