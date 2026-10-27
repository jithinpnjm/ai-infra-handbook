---
id: "c05-07"
title: "5.7 Pods and workloads: Deployments, StatefulSets, DaemonSets and Jobs"
sidebar_label: "5.7 Pods and workloads: Deployments, StatefulSets, DaemonSets and Jobs"
sidebar_position: 7
description: "The pod as the unit of deployment: spec anatomy, containers, init and sidecar containers, resources and QoS, volumes, environment, security context, lifecycle and termination, restart policies, probes overview, and the workload controllers with practical patterns for GPU training, inference and batch"
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP / GKE"
---

# 5.7 Pods and workloads: Deployments, StatefulSets, DaemonSets and Jobs

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | kubectl on any cluster; GPU node with the device plugin for GPU manifests |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Every AI workload ends up as pods: a training worker with eight GPUs and a large shared-memory volume, an inference server with probes tuned for slow model loads, a data-preparation Job, a node agent DaemonSet. The pod spec contains the decisions that determine whether the job runs fast, fails mysteriously, gets evicted under memory pressure, or leaves GPUs idle: resource requests and limits, QoS class, security context, volumes, lifecycle hooks, termination grace, and scheduling constraints. The workload controllers (Deployment, StatefulSet, DaemonSet, Job, CronJob) add replica management, identity, per-node placement and run-to-completion semantics. This chapter is the practical reference for writing those objects correctly.

## Prerequisites and outcomes

Needs 5.3, 5.6. After this chapter you can:

- Read and write complete pod specs, including init containers, native sidecars, volumes, projected volumes, environment variables, and security contexts.
- Set resources correctly (requests, limits, extended resources like `nvidia.com/gpu`, hugepages), predict QoS class, and know how limits translate to cgroups and OOM behaviour.
- Use lifecycle hooks, termination grace, signals, preStop, and restart policies to achieve graceful shutdown and checkpointing.
- Choose between Deployment, StatefulSet, DaemonSet, Job/CronJob (and know when operators/JobSet/Kueue are better) for AI workloads.
- Write production manifests for inference servers, distributed training pods, and node agents; use PodDisruptionBudgets, topology spread, and anti-affinity.
- Debug pods with `describe`, events, logs, ephemeral containers, and `kubectl debug`.

## 1. The pod

A **pod** is the smallest schedulable unit: one or more containers sharing a network namespace (one IP, shared ports), optionally IPC and PID namespaces, a set of volumes, and a cgroup parent. Containers in a pod are co-scheduled on one node and communicate over `localhost` and shared volumes. Pods are **ephemeral**: they are not rescheduled to other nodes if the node dies (controllers create replacements); their IPs change; they should be treated as cattle.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: trainer-0
  namespace: team-a
  labels: { app: llm-train, job: run-142 }
  annotations: { example.com/run-id: "142" }
spec:
  restartPolicy: Never                      # Always | OnFailure | Never
  terminationGracePeriodSeconds: 600        # time for SIGTERM handling (checkpoint) before SIGKILL
  serviceAccountName: trainer
  automountServiceAccountToken: false
  priorityClassName: training-normal
  nodeSelector: { nvidia.com/gpu.product: NVIDIA-H100-80GB-HBM3 }
  tolerations:
    - { key: nvidia.com/gpu, operator: Exists, effect: NoSchedule }
  securityContext:                            # pod-level
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    seccompProfile: { type: RuntimeDefault }
  initContainers:
    - name: fetch-config
      image: registry.example.com/tools/fetch:1.2
      args: ["--out", "/work/config.yaml"]
      volumeMounts: [ { name: work, mountPath: /work } ]
  containers:
    - name: trainer
      image: registry.example.com/ml/trainer@sha256:abc123...
      command: ["torchrun"]
      args: ["--nproc_per_node=8", "train.py", "--config", "/work/config.yaml"]
      env:
        - { name: NCCL_DEBUG, value: WARN }
        - name: RANK_NODE
          valueFrom: { fieldRef: { fieldPath: metadata.annotations['example.com/node-rank'] } }
        - name: HF_TOKEN
          valueFrom: { secretKeyRef: { name: hf, key: token } }
      envFrom:
        - configMapRef: { name: train-env }
      resources:
        requests: { cpu: "64", memory: 800Gi, nvidia.com/gpu: 8, ephemeral-storage: 50Gi }
        limits:   { memory: 800Gi, nvidia.com/gpu: 8, ephemeral-storage: 100Gi }
      securityContext:
        allowPrivilegeEscalation: false
        capabilities: { drop: [ALL] }
        readOnlyRootFilesystem: true
      volumeMounts:
        - { name: work,    mountPath: /work }
        - { name: shm,     mountPath: /dev/shm }
        - { name: data,    mountPath: /data, readOnly: true }
        - { name: ckpt,    mountPath: /ckpt }
        - { name: tmp,     mountPath: /tmp }
      startupProbe:   { exec: { command: ["sh","-c","test -f /tmp/ready"] }, failureThreshold: 120, periodSeconds: 5 }
      lifecycle:
        preStop: { exec: { command: ["sh","-c","kill -USR1 1; sleep 20"] } }    # ask the trainer to checkpoint
  volumes:
    - { name: work, emptyDir: {} }
    - { name: shm,  emptyDir: { medium: Memory, sizeLimit: 64Gi } }
    - { name: tmp,  emptyDir: {} }
    - { name: data, persistentVolumeClaim: { claimName: datasets, readOnly: true } }
    - { name: ckpt, persistentVolumeClaim: { claimName: checkpoints-team-a } }
```

### Labels and annotations: syntax rules and selector queries

Every Pod and workload controller relies on **labels** (identifying key/value pairs used for grouping and selector queries by ReplicaSets, Services, NetworkPolicies, and node selectors) and **annotations** (non-identifying key/value metadata used by tools and controllers, such as `deployment.kubernetes.io/revision`, `kubernetes.io/change-cause`, or `kubectl.kubernetes.io/last-applied-configuration`). As *Kubernetes: Up and Running* (3rd edition, Chapter 6) specifies, Kubernetes enforces strict syntax rules on label keys and values:

- **Label key syntax**: a key has two parts separated by a slash (`/`): an optional prefix and a required name.
  - **Optional prefix**: must be a valid DNS subdomain up to `253` characters (for example, `acme.com/app-version` or `kubernetes.io/cluster-service`).
  - **Required key name**: up to `63` characters consisting of alphanumeric characters (`[a-zA-Z0-9]`), dashes (`-`), underscores (`_`), and dots (`.`), and must start and end with an alphanumeric character.
- **Label value syntax**: a string up to `63` characters following the same character rules as label key names (starts and ends with `[a-zA-Z0-9]`, with `-`, `_`, and `.` allowed in between).
- **Querying and displaying labels with `kubectl`** (untested here): use `--show-labels` to print all labels on each object, `-L <label_key>` to display a specific label's value as a dedicated table column, and `-l` / `--selector` with equality (`=`, `!=`) or set-based (`in`, `notin`, `key`, `!key`) operators:

```bash
kubectl get pods --show-labels
kubectl get deployments -L canary
kubectl get pods -l 'ver=2,!canary'
kubectl get pods -l 'ver in (1, 2)'
kubectl label deployments alpaca-test "canary=true"    # add or update (--overwrite) a label
kubectl label deployments alpaca-test "canary-"        # remove the 'canary' label with a trailing dash
```

In API objects such as `Deployment` and `Job`, a selector like `app=alpaca,ver in (1, 2)` is written using `matchLabels` and `matchExpressions` (evaluated as a logical AND):

```yaml
selector:
  matchLabels:
    app: alpaca
  matchExpressions:
    - { key: ver, operator: In, values: [1, 2] }
```

## 2. Pod spec anatomy

### Containers and init containers

- `containers[]`: image (pin by digest in production), `command`/`args` (override ENTRYPOINT/CMD; use exec form lists), `workingDir`, `env`/`envFrom`, `ports` (informational), `resources`, `volumeMounts`, probes, `lifecycle`, `securityContext`, `imagePullPolicy` (`IfNotPresent` default for tagged images, `Always` for `:latest`), `terminationMessagePath/Policy`, `stdin/tty`.
- **Init containers** run sequentially to completion before app containers start; use for waiting on dependencies, fetching config or model files, permissions fixes, schema migrations. They share volumes with the pod; their resource requests count as `max(init max, sum(app))` for scheduling. A failing init container restarts per `restartPolicy` and blocks the pod in `Init:Error`/`Init:CrashLoopBackOff`.
- **Sidecar containers** (native sidecars, `initContainers` with `restartPolicy: Always`, stable in recent releases): start before and stay for the lifetime of app containers, are ordered with probes honoured, and terminate after the main containers: ideal for log shippers, proxies, credential refreshers and metrics exporters, avoiding the old problem that a sidecar kept Jobs from completing.
- **Ephemeral containers** (`kubectl debug`) are added to a running pod for debugging (shell in distroless images) and share namespaces; they cannot be removed or have resources.

### Resources and QoS

- `requests` are used for **scheduling** and as the minimum guaranteed share; `limits` are enforced at run time by cgroups: **CPU limit** throttles (CFS quota `cpu.max`), **memory limit** is a hard cap and exceeding it causes an **OOM kill** of the container. Requests map to `cpu.weight` (shares); memory requests inform eviction and (with MemoryQoS) `memory.min/high`.
- **Extended resources** (`nvidia.com/gpu`, `rdma/hca_shared_devices_a`, `hugepages-2Mi`, `ephemeral-storage`) are integers and, for devices, requests must equal limits (no overcommit); GPUs are not shared or fractional unless using MIG, time-slicing or MPS via the device plugin/operator configuration (Part 11).
- **QoS classes** (derived, not set): **Guaranteed** (every container has CPU and memory requests equal to limits), **Burstable** (some requests/limits, not Guaranteed), **BestEffort** (none). QoS determines cgroup placement (`kubepods.slice/guaranteed|burstable|besteffort`), OOM score adjustment (`oom_score_adj`: -997 for Guaranteed, 1000 for BestEffort, scaled for Burstable) and eviction order under node pressure (5.9). Training and inference pods that must not be evicted should be Guaranteed; also required for the **CPU Manager static policy** (exclusive cores for integer CPU requests) and Topology Manager alignment (5.18).
- **CPU limits and ML**: CFS throttling hurts latency-sensitive servers and data loaders with bursts; many teams set CPU requests but no limits for GPU pods (while still avoiding noisy neighbours via node dedication), or use the static CPU manager for exclusive cores. Memory limits equal to requests are recommended to avoid surprising node-level OOM.
- **Memory for ML**: the container limit includes page cache attributable to the cgroup, pinned memory, and shared memory (`/dev/shm`) because tmpfs pages are charged to the cgroup; a large DataLoader or NCCL buffers plus `/dev/shm` can trigger OOM kills even when "the process" seems small. Size `emptyDir.medium: Memory` volumes and include them in limits.
- **Ephemeral storage** requests/limits cover container writable layers, logs and `emptyDir` (disk-backed); exceeding the limit evicts the pod.
- **LimitRange** sets per-namespace defaults/min/max; **ResourceQuota** caps totals per namespace (including `requests.nvidia.com/gpu`) (5.22).
- **Pod overhead** (RuntimeClass) and **in-place pod resize** (stable in recent releases for CPU/memory without restart) are additional features; check your version.

### Volumes

Types you will meet: `emptyDir` (per-pod scratch; `medium: Memory` for tmpfs; `sizeLimit`), `configMap`/`secret`/`downwardAPI`/`projected` (config and identity injection; projected ServiceAccount tokens with audience and expiry), `persistentVolumeClaim` (durable storage, 5.17), `hostPath` (node paths: avoid except for system agents; large security risk), `nfs`, CSI ephemeral volumes, `image` volumes (mount OCI artefacts, e.g., model weights, in newer releases), `ephemeral` (generic ephemeral PVC per pod). Mount options: `readOnly`, `subPath` (note: subPath mounts don't receive ConfigMap updates), `mountPropagation`, `subPathExpr`. `fsGroup` in the security context changes ownership of volumes (can be slow on huge volumes; use `fsGroupChangePolicy: OnRootMismatch`).

### Environment and configuration

`env` with literal values, `valueFrom` (field refs like `status.podIP`, `spec.nodeName`, resource field refs, ConfigMap/Secret keys), `envFrom` (whole ConfigMap/Secret). Env vars are fixed at container start; volume-mounted ConfigMaps/Secrets update eventually (kubelet sync ~1 minute) unless mounted via subPath. Prefer mounted files for secrets over env (env leaks into `ps`, crash dumps and child processes). Service discovery env vars (`MYSVC_SERVICE_HOST`) are legacy; use DNS (5.11); set `enableServiceLinks: false` in namespaces with many Services.

### Security context

Container- and pod-level: `runAsUser/Group`, `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]` (+ minimal adds like `IPC_LOCK` for RDMA pinned memory, `NET_BIND_SERVICE`), `seccompProfile: RuntimeDefault`, `seLinuxOptions`, `appArmorProfile`, `privileged` (avoid), `procMount`, `supplementalGroups`, `sysctls` (safe vs unsafe; unsafe require kubelet `--allowed-unsafe-sysctls`), `hostUsers: false` (user namespaces). Enforce with Pod Security Admission (5.21): `baseline` and `restricted` profiles; GPU/RDMA workloads often need a few exceptions, which should be granted per namespace rather than cluster-wide. Host namespaces (`hostNetwork`, `hostPID`, `hostIPC`) are for system DaemonSets; some HPC jobs use `hostIPC` or `hostNetwork` for performance but weaken isolation.

### Lifecycle, termination and restart policy

Pod termination: API sets `deletionTimestamp`; endpoints controller removes the pod from Service endpoints (in parallel); kubelet runs `preStop` hooks, sends `SIGTERM` to PID 1 of each container, waits up to `terminationGracePeriodSeconds`, then `SIGKILL`. Because endpoint removal and SIGTERM race, servers should keep serving while draining for a few seconds (preStop `sleep 5-10`) and then shut down gracefully. For training: handle SIGTERM by writing a checkpoint, flush logs, and exit 0 or a distinctive code; set the grace period to cover the checkpoint time; pods preempted by higher priority workloads or evicted get the same treatment. `restartPolicy`: `Always` (Deployments etc.), `OnFailure`/`Never` (Jobs). Container restarts use exponential backoff (10 s to 5 min) shown as `CrashLoopBackOff`. `terminationMessagePath` (`/dev/termination-log`) lets a container leave a short failure reason visible in `kubectl describe`.

**Probes** (detailed in 5.9): `startupProbe` (protect slow starts such as multi-GB model loads), `readinessProbe` (traffic gating), `livenessProbe` (restart on deadlock; use sparingly, never tie to dependencies), with `exec`, `httpGet`, `tcpSocket`, `grpc` handlers.

### Scheduling-related fields

`nodeName` (bypass scheduler; avoid), `nodeSelector`, `affinity` (node, pod, anti-affinity: required vs preferred, topology keys), `tolerations`, `topologySpreadConstraints`, `priorityClassName`/`preemptionPolicy`, `schedulerName`, `runtimeClassName`, `resourceClaims` (DRA). See 5.18.

## 3. Workload controllers: choosing

| Controller | Identity | Storage | Typical use | Notes |
|---|---|---|---|---|
| **Deployment** | Interchangeable replicas | Shared or none | Stateless services, inference servers, gateways, dashboards | Rolling updates, rollbacks, HPA targets |
| **StatefulSet** | Stable names `x-0..n`, stable DNS, ordered | Per-pod PVC via templates | Databases, queues, vector DBs, etcd, some parameter servers, coordination for distributed jobs needing stable hostnames | Careful with update/scale semantics; headless Service |
| **DaemonSet** | One per node | Host paths/CSI | Node agents: device plugin, DCGM, CNI, log shipper, node problem detector, GPU driver containers | Tolerations to reach tainted GPU nodes |
| **Job** | Run to completion, optional indexing | Any | Data prep, evaluations, single-node training, batch inference, benchmarks | `backoffLimit`, `podFailurePolicy`, TTL, `suspend` |
| **CronJob** | Scheduled Jobs | Any | Periodic retraining, backups, report generation, cleanup | `concurrencyPolicy: Forbid` for jobs that must not overlap |
| **JobSet / MPIJob / PyTorchJob / RayJob** (operators) | Gang of heterogeneous pods with startup ordering and failure policies | Any | Multi-node training/inference | Prefer these (plus Kueue) over hand-rolled Jobs for distributed workloads (Part 14) |
| **Bare Pod** | None | | Debugging only | Not rescheduled if the node dies |

### Deployment patterns for inference

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: vllm-llama, namespace: serving }
spec:
  replicas: 3
  revisionHistoryLimit: 5
  progressDeadlineSeconds: 1800         # model downloads and CUDA graph capture are slow
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }    # GPUs are scarce: surge needs a spare GPU; use maxUnavailable: 1 / maxSurge: 0 if none
  selector: { matchLabels: { app: vllm-llama } }
  template:
    metadata: { labels: { app: vllm-llama } }
    spec:
      terminationGracePeriodSeconds: 120
      tolerations: [ { key: nvidia.com/gpu, operator: Exists, effect: NoSchedule } ]
      topologySpreadConstraints:
        - { maxSkew: 1, topologyKey: kubernetes.io/hostname, whenUnsatisfiable: ScheduleAnyway, labelSelector: { matchLabels: { app: vllm-llama } } }
      containers:
        - name: vllm
          image: vllm/vllm-openai@sha256:...
          args: ["--model", "/models/llama-70b", "--tensor-parallel-size", "4", "--max-model-len", "8192"]
          ports: [ { containerPort: 8000 } ]
          resources: { requests: { cpu: "16", memory: 200Gi, nvidia.com/gpu: 4 }, limits: { memory: 200Gi, nvidia.com/gpu: 4 } }
          startupProbe:   { httpGet: { path: /health, port: 8000 }, periodSeconds: 10, failureThreshold: 180 }    # up to 30 min
          readinessProbe: { httpGet: { path: /health, port: 8000 }, periodSeconds: 5 }
          livenessProbe:  { httpGet: { path: /health, port: 8000 }, periodSeconds: 20, failureThreshold: 6 }
          lifecycle: { preStop: { exec: { command: ["sleep", "15"] } } }
          volumeMounts: [ { name: models, mountPath: /models, readOnly: true }, { name: shm, mountPath: /dev/shm } ]
      volumes:
        - { name: models, persistentVolumeClaim: { claimName: model-weights-ro } }
        - { name: shm, emptyDir: { medium: Memory, sizeLimit: 16Gi } }
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: vllm-llama, namespace: serving }
spec:
  minAvailable: 2
  selector: { matchLabels: { app: vllm-llama } }
```

**PodDisruptionBudgets** limit *voluntary* disruptions (drains, upgrades, autoscaler scale-down) via the Eviction API: set `minAvailable` or `maxUnavailable`; they do not stop involuntary failures. A PDB that allows zero disruptions blocks node drains (a common upgrade-time stall), so pair with capacity to place replacements.

### Controlling Deployment rollouts: `change-cause`, `pause`, `resume`, `history`, and `undo --to-revision`

During a `Deployment` rollout, the Deployment controller scales up the new `ReplicaSet` (`NewReplicaSet`) and scales down the old `ReplicaSet`s (`OldReplicaSets`) while keeping up to `spec.revisionHistoryLimit` (default `10`) old `ReplicaSet`s scaled to `0` for rollback. As *Kubernetes: Up and Running* (3rd edition, Chapter 10) shows, you can record the reason for an update by setting the `kubernetes.io/change-cause` annotation inside `spec.template.metadata.annotations` (on the Pod template, not on the top-level Deployment metadata, and only when changing the template since modifying `spec.template` triggers a new rollout):

```yaml
spec:
  template:
    metadata:
      annotations:
        kubernetes.io/change-cause: "Update to green kuard"
```

You can then inspect, pause, resume, or roll back the rollout using `kubectl rollout` (in the book's `kuard` example, untested here):

```bash
kubectl rollout status deployments kuard
kubectl rollout pause deployments kuard                    # halt a rollout mid-flight to investigate anomalies
kubectl rollout resume deployments kuard                   # continue a paused rollout
kubectl rollout history deployment kuard                   # list REVISION and CHANGE-CAUSE columns
kubectl rollout history deployment kuard --revision=2      # inspect the Pod template of revision 2
kubectl rollout undo deployments kuard                     # roll back to the previous revision (same as --to-revision=0)
kubectl rollout undo deployments kuard --to-revision=3     # roll back to a specific revision (renumbered as the newest revision)
```

Remember that `kubectl rollout undo` mutates cluster state directly; in a GitOps workflow, prefer reverting the manifest in Git and applying it so version control matches what runs in the cluster.

### StatefulSet example (vector database)

```yaml
apiVersion: v1
kind: Service
metadata: { name: qdrant, namespace: data }
spec: { clusterIP: None, selector: { app: qdrant }, ports: [ { port: 6333, name: http } ] }
---
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: qdrant, namespace: data }
spec:
  serviceName: qdrant
  replicas: 3
  podManagementPolicy: Parallel
  persistentVolumeClaimRetentionPolicy: { whenDeleted: Retain, whenScaled: Retain }
  selector: { matchLabels: { app: qdrant } }
  updateStrategy: { type: RollingUpdate, rollingUpdate: { partition: 0 } }
  template:
    metadata: { labels: { app: qdrant } }
    spec:
      containers:
        - name: qdrant
          image: qdrant/qdrant:v1.9.0
          volumeMounts: [ { name: storage, mountPath: /qdrant/storage } ]
  volumeClaimTemplates:
    - metadata: { name: storage }
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: fast-nvme
        resources: { requests: { storage: 200Gi } }
```

Pods get DNS `qdrant-0.qdrant.data.svc.cluster.local`; PVCs `storage-qdrant-0..2` persist across pod deletion; scaling down leaves PVCs (data safety); pods are re-attached to the same PVC (and thus tied to zone/node topology for local volumes).

### DaemonSet example (GPU telemetry agent)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata: { name: dcgm-exporter, namespace: gpu-monitoring }
spec:
  selector: { matchLabels: { app: dcgm-exporter } }
  updateStrategy: { type: RollingUpdate, rollingUpdate: { maxUnavailable: 10% } }
  template:
    metadata: { labels: { app: dcgm-exporter } }
    spec:
      nodeSelector: { nvidia.com/gpu.present: "true" }
      tolerations: [ { operator: Exists } ]                  # run on every (tainted) GPU node
      priorityClassName: system-node-critical
      containers:
        - name: exporter
          image: nvcr.io/nvidia/k8s/dcgm-exporter:3.3.5-3.4.1-ubuntu22.04
          ports: [ { containerPort: 9400, hostPort: 9400, name: metrics } ]
          securityContext: { capabilities: { add: [SYS_ADMIN] } }
          resources: { requests: { cpu: 100m, memory: 128Mi }, limits: { memory: 512Mi } }
```

### Job patterns for batch and distributed work

```yaml
apiVersion: batch/v1
kind: Job
metadata: { name: embed-corpus-142, namespace: team-a, labels: { kueue.x-k8s.io/queue-name: team-a-gpu } }
spec:
  suspend: true                          # Kueue (or you) unsuspends when quota is available
  completionMode: Indexed
  completions: 16
  parallelism: 16
  backoffLimitPerIndex: 2
  maxFailedIndexes: 1
  ttlSecondsAfterFinished: 86400
  podFailurePolicy:
    rules:
      - action: Ignore
        onPodConditions: [ { type: DisruptionTarget } ]       # node drain/preemption does not consume retries
      - action: FailJob
        onExitCodes: { containerName: worker, operator: In, values: [42] }   # config error: do not retry
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: worker
          image: registry.example.com/ml/embed:1.7
          env: [ { name: SHARD, valueFrom: { fieldRef: { fieldPath: "metadata.annotations['batch.kubernetes.io/job-completion-index']" } } } ]
          resources: { requests: { cpu: "8", memory: 64Gi, nvidia.com/gpu: 1 }, limits: { memory: 64Gi, nvidia.com/gpu: 1 } }
```

For tightly coupled multi-node training use JobSet/MPIJob/PyTorchJob with gang admission by Kueue/Volcano (a plain Job with `parallelism: N` can start some pods while others wait, wasting GPUs and deadlocking collective initialisation) (Part 14).

## 4. Operating pods

### Reading state

```bash
kubectl get pod trainer-0 -o wide
kubectl describe pod trainer-0                    # events: Scheduled, Pulling, Created, Started, FailedScheduling, Unhealthy, OOMKilled
kubectl get pod trainer-0 -o jsonpath='{.status.containerStatuses[0].lastState}' | jq
kubectl get pod trainer-0 -o jsonpath='{.status.qosClass}{"\n"}'
kubectl logs trainer-0 -c trainer --previous --timestamps --tail=200
kubectl logs -f job/embed-corpus-142 --all-containers --max-log-requests=20
kubectl exec -it trainer-0 -c trainer -- bash
kubectl attach -it trainer-0 -c trainer                                       # attach to PID 1 stdin/stdout when no shell exists in the container
kubectl apply -f pod.yaml view-last-applied                                   # inspect (or edit-/set-last-applied) the last-applied-configuration annotation
kubectl config set-context my-context --namespace=team-a && kubectl config use-context my-context
source <(kubectl completion bash)                                             # enable bash tab completion for kubectl
kubectl debug -it trainer-0 --image=nicolaka/netshoot --target=trainer      # ephemeral container sharing the process namespace
kubectl debug node/gpu-node-1 -it --image=ubuntu                              # privileged node debug pod (chroot /host)
kubectl top pod trainer-0 --containers
kubectl get events --field-selector involvedObject.name=trainer-0 --sort-by=.lastTimestamp
```

### Phases and states

Pod `phase`: Pending (accepted, not all containers running: scheduling, image pulls, init), Running, Succeeded, Failed, Unknown. Container states: Waiting (reason: `ContainerCreating`, `ImagePullBackOff`, `CrashLoopBackOff`, `CreateContainerConfigError`), Running, Terminated (reason `Completed`, `Error`, `OOMKilled`, exit code). Conditions: `PodScheduled`, `Initialized`, `ContainersReady`, `Ready`, `DisruptionTarget`.

| Symptom | Likely cause | Fix |
|---|---|---|
| Pending, `0/10 nodes are available: Insufficient nvidia.com/gpu` | No free GPUs / taints / quota | `describe` shows predicate counts; add capacity, tolerations, queue |
| Pending, `node(s) had untolerated taint` | Missing toleration | Add toleration |
| `ImagePullBackOff` | Wrong name/tag, auth, rate limit, registry down | Events, `crictl pull` on node, imagePullSecrets (5.1) |
| `CreateContainerConfigError` | Missing ConfigMap/Secret key | `describe` |
| `CrashLoopBackOff` | App crash, bad args, missing dependency | `logs --previous`, exit code |
| `OOMKilled` (exit 137) | Memory limit hit | Increase memory limit, reduce dataloader workers/shm, find leaks |
| Evicted | Node pressure (memory/disk) or ephemeral storage limit | `describe`, node conditions, QoS |
| Stuck `Terminating` | Finalizers, unresponsive kubelet, process ignoring SIGTERM, volume detach | `describe`, kubelet logs |
| Running but not Ready | Readiness failing | Probe config, app logs |
| `ContainerCannotRun` / `exec format error` | Wrong arch/entrypoint | Image platform (5.1) |

## 5. Sizing and placement guidelines for GPU workloads

1. Request **all** GPUs of a node for multi-GPU training pods (8 on HGX), plus proportional CPU and memory so the pod is Guaranteed and the node isn't fragmented by small CPU pods.
2. Match CPU requests to data-loading needs (e.g., 8 to 16 cores per GPU for heavy augmentation), and leave headroom for system daemons (kube/system reserved).
3. Set `/dev/shm` explicitly (memory-backed emptyDir with sizeLimit); include it in memory accounting.
4. Mount datasets read-only from shared storage; write checkpoints to durable storage with atomic rename; use local NVMe `emptyDir` or local PVs for scratch/caching.
5. Use `priorityClassName` and preemption policies deliberately (interactive vs training vs best-effort), and handle SIGTERM for checkpointing.
6. Add `topologySpreadConstraints`/anti-affinity for inference replicas across nodes/zones; use pod affinity or rack/rail labels for training pods that need locality (5.18, Part 12).
7. Use `terminationGracePeriodSeconds` ≥ checkpoint duration + margin.
8. Pin images by digest; prefer images prepared with matching CUDA/driver (5.1) and pre-pulled on nodes.
9. Set `automountServiceAccountToken: false` where the pod doesn't call the API.
10. Label for cost allocation and ownership (team, project, run id) consistently.

## 6. Lab (untested)

1. **Pod anatomy**: write a pod with init container, sidecar (native), shared `emptyDir`, env from ConfigMap/Secret/Downward API; view with `kubectl get -o yaml`; read `status` fields and conditions.
2. **QoS and OOM**: create pods with Guaranteed, Burstable and BestEffort QoS; inspect `/proc/<pid>/oom_score_adj` via `crictl`/node; run a memory hog beyond limits and observe `OOMKilled`; fill node memory to see eviction ordering (lab only).
3. **/dev/shm**: reproduce a PyTorch DataLoader failure (or a Python `multiprocessing` shared-memory failure) with default 64 MiB shm; fix with memory-backed emptyDir and sized limits; observe the memory accounting in cgroup `memory.current`.
4. **Termination**: write an app that handles SIGTERM and logs timing; test `terminationGracePeriodSeconds`, `preStop`, and the race with endpoint removal behind a Service (use a request loop).
5. **Probes**: configure startup/readiness/liveness for a slow-start server; break each and observe behaviour (restart vs unready).
6. **Deployment rollouts**: perform rolling update with `maxUnavailable: 0`, `maxSurge: 1` on a cluster without spare capacity; observe stuck rollout; adjust; add a PDB and drain a node.
7. **StatefulSet**: create the example; delete a pod; scale down/up; verify PVC retention; test `OrderedReady` vs `Parallel`; partitioned update.
8. **DaemonSet**: deploy the exporter pattern; add a node; cordon a node and see DaemonSet pods persist (tolerations).
9. **Jobs**: Indexed Job with `podFailurePolicy` and `backoffLimitPerIndex`; simulate a disruption (drain) and an application error; watch which count against retries; add `suspend` and unsuspend.
10. **GPU manifests**: on a GPU node run `nvidia-smi` pods (limits 1, 2, 8 GPUs); request more than available and read the scheduler message; add taints/tolerations; try `NVIDIA_VISIBLE_DEVICES` in-pod behaviours.
11. **Debugging**: use `kubectl debug` ephemeral container on a distroless pod; node debug pod to inspect kubelet logs; reproduce `CrashLoopBackOff`, `ImagePullBackOff`, `CreateContainerConfigError`.
12. **PDB and drain**: create a PDB with `minAvailable` equal to replicas and drain a node (blocked); fix capacity or PDB; discuss upgrade implications.
13. **Clean up**.

Mark tested only after execution.

## 7. Common mistakes

- No resource requests (BestEffort) for important pods; limits far above requests for memory; forgetting `/dev/shm` in memory sizing.
- Putting liveness probes on slow-starting model servers without a startup probe (restart loops).
- Using `latest` tags, `hostPath` for convenience, or `privileged` to "make GPUs work".
- SIGTERM ignored (shell-form entrypoint), grace period too short for checkpoints.
- Using Deployments for training jobs that should be Jobs/JobSet; using plain Jobs for gang workloads.
- StatefulSet with a PDB or update strategy that blocks maintenance; deleting PVCs accidentally.
- PDBs that forbid all disruption.
- DaemonSets without tolerations for tainted GPU nodes (agents missing exactly where needed).
- Secrets in env vars printed in logs; service account tokens auto-mounted into pods that don't need them.
- Assuming CPU limits are harmless for latency-sensitive services.

## 8. Interview angles

- "What is a pod and why not just containers? What do containers in a pod share?" 
- "Explain QoS classes and how they affect eviction and OOM." 
- "When do you use a StatefulSet vs Deployment vs Job vs DaemonSet?" 
- "What happens when you delete a pod? Walk through termination and the endpoint race." 
- "Why does my GPU pod stay Pending? How do you debug?" 
- "How do init containers and native sidecars differ? What problems do sidecars cause for Jobs?" 
- "How would you configure an inference deployment that loads a 140 GB model?" (startup probe, PVC/image volume, rolling update strategy, PDB, topology spread.)
- "What's special about `/dev/shm` in ML containers on Kubernetes?" 

## 9. Checkpoint questions (40)

1. What do containers in a pod share? **A:** Network namespace, volumes, optionally IPC/PID.
2. Are pods rescheduled to another node on failure? **A:** No; controllers create replacements.
3. What do init containers do? **A:** Run to completion sequentially before app containers.
4. What is a native sidecar? **A:** Init container with `restartPolicy: Always`.
5. What do requests control? **A:** Scheduling and guaranteed share.
6. What do limits control? **A:** Runtime caps (CPU throttle, memory OOM).
7. QoS Guaranteed condition? **A:** Requests = limits for CPU and memory in all containers.
8. Eviction order by QoS? **A:** BestEffort, then Burstable, then Guaranteed.
9. Must GPU requests equal limits? **A:** Yes for extended resources.
10. How to give a pod large shared memory? **A:** Memory-backed `emptyDir` with sizeLimit.
11. Does `/dev/shm` count toward memory limit? **A:** Yes (tmpfs charged to cgroup).
12. What is `fsGroup`? **A:** Group ownership applied to volumes.
13. What is `readOnlyRootFilesystem`? **A:** Immutable container rootfs; use volumes for writes.
14. Default termination signal? **A:** SIGTERM then SIGKILL after grace.
15. Default grace period? **A:** 30 seconds.
16. Purpose of preStop sleep? **A:** Let endpoint removal propagate before shutdown.
17. restartPolicy for Deployments? **A:** Always.
18. What is CrashLoopBackOff? **A:** Exponential restart backoff after repeated crashes.
19. What is exit code 137? **A:** SIGKILL (often OOM).
20. Pod phases? **A:** Pending, Running, Succeeded, Failed, Unknown.
21. Probe types? **A:** startup, readiness, liveness.
22. Why startup probes? **A:** Protect slow initialisation from liveness kills.
23. Deployment strategy options? **A:** RollingUpdate, Recreate.
24. What does `maxSurge` need for GPU pods? **A:** A spare GPU.
25. StatefulSet identity? **A:** Stable name, DNS and PVC per ordinal.
26. StatefulSet PVC deletion on scale-down? **A:** Retained by default.
27. DaemonSet scheduling? **A:** One pod per matching node.
28. DaemonSet on tainted nodes needs? **A:** Tolerations.
29. Job completionMode Indexed? **A:** Each pod gets an index.
30. What is `podFailurePolicy`? **A:** Rules to count/ignore/fail on exit codes or conditions.
31. What does Job `suspend` enable? **A:** External admission control (Kueue).
32. What is a PDB? **A:** Limits voluntary disruptions.
33. PDB with minAvailable = replicas? **A:** Blocks drains.
34. What is `topologySpreadConstraints`? **A:** Even spread across topology domains.
35. What is an ephemeral container? **A:** Debug container added to a running pod.
36. When avoid hostPath? **A:** Almost always (security, portability).
37. Why `automountServiceAccountToken: false`? **A:** Reduce credential exposure.
38. Why not Deployments for training? **A:** Wrong semantics (restart forever, no completion).
39. Why gang scheduling for distributed training? **A:** All-or-nothing starts avoid deadlock/idle GPUs.
40. What are the character-length limits for Kubernetes label keys and values, and what `kubectl rollout` commands pause, resume, or roll back a Deployment to revision `3`? **A:** Label keys have an optional DNS subdomain prefix up to `253` characters plus `/` and a required name up to `63` characters (`[a-zA-Z0-9]`, `-`, `_`, `.`, starting/ending alphanumeric); values are up to `63` characters with the same rules; use `kubectl rollout pause deployments <name>`, `kubectl rollout resume deployments <name>`, and `kubectl rollout undo deployments <name> --to-revision=3`.

## 10. Sources and review notes

**Written in original words.** Principal sources:

- Brendan Burns, Joe Beda, Kelsey Hightower and Lachlan Evenson, *Kubernetes: Up and Running* (`kubernetes-up-and-running-3rd-edition`, 3rd edition; Chapter 4: `4. Common kubectl Commands`, Chapter 5 on pods, Chapter 6: `6. Labels and Annotations`, Chapters 9 to 12 including Chapter 10: `10. Deployments`, and Chapter 22 on running batch and stateful workloads — Chapters 4, 6, and 10 read in full for `kubectl` context/last-applied/attach/completion commands, label syntax rules and selectors, and Deployment rollout pause/resume/undo/change-cause mechanics).
- Josh Rosso, Rich Lander, Alex Brand and John Harris, *Production Kubernetes* (chapter 14 on application considerations: resource requests, probes, graceful shutdown, config).
- Kubernetes documentation for pods, workloads, QoS, probes, PDBs and Job features.
- Examples are the author's constructions.

**Flagged for verification before publishing:** feature status for native sidecars, in-place resize, image volumes, `backoffLimitPerIndex`, `podFailurePolicy` and `persistentVolumeClaimRetentionPolicy` in your Kubernetes version; default timings and values; image tags in examples; and every manifest; all labs are **untested**.
