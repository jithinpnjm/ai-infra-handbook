---
id: "c05-09"
title: "5.9 The kubelet and the node: CRI, cgroups, QoS classes, probes and eviction"
sidebar_label: "5.9 The kubelet and the node: CRI, cgroups, QoS classes, probes and eviction"
sidebar_position: 9
description: "The node agent in depth: KubeletConfiguration, resource managers (CPU, memory, topology, device), reservations, cgroup hierarchy and QoS, probes, node pressure eviction, image and log GC, graceful node shutdown, node status and leases, static pods, kubelet security and tuning for GPU nodes"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.9 The kubelet and the node: CRI, cgroups, QoS classes, probes and eviction

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | Root on a Kubernetes worker (VM or bare metal); `kubectl`, `crictl`, `systemd-cgls`, `lscpu`, `numactl`; GPU server with multiple NUMA nodes for topology exercises |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

The kubelet is where cluster policy meets hardware. It decides how many pods a node accepts, whether a training pod gets exclusive CPU cores aligned with its GPUs' NUMA node, how much memory the system and Kubernetes daemons keep for themselves, what gets evicted when memory or disk runs low, how long a node can lose connectivity before its pods are rescheduled, and how containers are killed on shutdown. On a GPU server with 8 GPUs, dual-socket CPUs, multiple NICs and NVMe, default kubelet settings leave a lot of performance and reliability on the table: cross-NUMA traffic, CPU throttling, noisy neighbours, nodes that die from OOM because nothing was reserved for the OS, long recovery times after failures. This chapter explains the kubelet's responsibilities and tuning for AI nodes.

## Prerequisites and outcomes

Needs 5.2, 5.7, 5.8. After this chapter you can:

- Describe the kubelet's responsibilities, configuration sources and APIs; write a production `KubeletConfiguration`.
- Explain the cgroup hierarchy the kubelet builds, QoS classes, reservations (`kubeReserved`, `systemReserved`, eviction thresholds) and compute **node allocatable**.
- Configure and reason about the CPU Manager, Memory Manager, Topology Manager, Device Manager and Pod Resources API for GPU/NUMA alignment.
- Configure probes correctly and understand how the kubelet runs them.
- Explain node-pressure eviction (signals, soft/hard thresholds, ordering), PID and disk limits, image GC and log rotation, and how they differ from API-initiated eviction and OOM kills.
- Understand node status/lease heartbeats, NotReady behaviour, graceful node shutdown, static pods, kubelet certificates and security hardening.
- Diagnose node-level problems with kubelet logs, metrics and cgroup data.

## 1. What the kubelet does

```mermaid
flowchart TB
  subgraph Sources["Pod sources"]
    API["API server (watch pods with spec.nodeName=this node)"]
    FILE["Static pod manifests dir"]
    HTTP["HTTP manifest URL (rare)"]
  end
  Sources --> PM["Pod manager / config merge"]
  PM --> PW["Per-pod workers (syncPod)"]
  PW --> VM["Volume manager\n(CSI, emptyDir, configmap...)"]
  PW --> DM["Resource managers\nCPU / memory / topology / device"]
  PW --> CRI["CRI client → containerd/CRI-O"]
  PW --> PR["Prober (startup/readiness/liveness)"]
  CRI --> PLEG["PLEG: relist container states → events"]
  PLEG --> PW
  PW --> SM["Status manager → API server"]
  EV["Eviction manager (node pressure)"] --> PW
  IMG["Image GC / container GC"] --> CRI
  CAD["cAdvisor/cgroup stats → /metrics, /stats/summary"] --> EV
  LEASE["Node lease + node status heartbeats"] --> API
  KAPI["Kubelet HTTPS server :10250\n(logs, exec, attach, port-forward, metrics, pods)"]
```

Responsibilities: register the Node (labels, capacity, allocatable, conditions, addresses, daemon endpoints); run assigned pods via CRI; manage pod/container cgroups and QoS; mount volumes; run probes; report status; garbage-collect containers, images and logs; enforce eviction under pressure; expose metrics and APIs; gracefully handle node shutdown; rotate its client/serving certificates.

Configuration: prefer the `KubeletConfiguration` file (`--config`, typically `/var/lib/kubelet/config.yaml` written by kubeadm) over flags; kubeadm stores a cluster-wide copy in ConfigMap `kube-system/kubelet-config` and per-node overrides via `--config`/drop-ins (`/etc/kubernetes/kubelet.conf.d/*.conf` in newer releases) and `KUBELET_EXTRA_ARGS`. Dynamic kubelet config was removed; roll changes with restarts (drain first for disruptive ones). Inspect live config: `kubectl get --raw "/api/v1/nodes/<node>/proxy/configz" | jq .kubeletconfig`.

## 2. A production KubeletConfiguration for GPU nodes

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous: { enabled: false }
  webhook: { enabled: true, cacheTTL: 2m }
  x509: { clientCAFile: /etc/kubernetes/pki/ca.crt }
authorization:
  mode: Webhook
cgroupDriver: systemd
cgroupsPerQOS: true
clusterDNS: ["169.254.20.10"]            # NodeLocal DNSCache (5.11) or the CoreDNS service IP
clusterDomain: cluster.local
containerLogMaxSize: 50Mi
containerLogMaxFiles: 5
serverTLSBootstrap: true
rotateCertificates: true
protectKernelDefaults: true              # fail if kernel sysctls differ from kubelet expectations (hardening)
seccompDefault: true                     # RuntimeDefault seccomp for all pods
maxPods: 110                             # lower (e.g., 30-60) on GPU nodes if you want to reserve headroom
podPidsLimit: 8192
serializeImagePulls: false
maxParallelImagePulls: 3
registryPullQPS: 20
registryBurst: 40
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 70
imageMinimumGCAge: 30m
nodeStatusUpdateFrequency: 10s
nodeStatusReportFrequency: 5m
shutdownGracePeriod: 120s                # graceful node shutdown (systemd inhibitor)
shutdownGracePeriodCriticalPods: 30s
# --- Resource management for GPU/AI nodes ---
cpuManagerPolicy: static
cpuManagerPolicyOptions: { full-pcpus-only: "true" }
cpuManagerReconcilePeriod: 10s
memoryManagerPolicy: Static              # requires reservedMemory to match the reserved totals
topologyManagerPolicy: single-numa-node  # best-effort | restricted | single-numa-node | none
topologyManagerScope: pod                # container | pod
reservedSystemCPUs: "0-3"                # dedicate cores to OS/kubelet/runtime (instead of per-resource reserved)
kubeReserved: { memory: 4Gi, ephemeral-storage: 5Gi }
systemReserved: { memory: 8Gi, ephemeral-storage: 5Gi }
enforceNodeAllocatable: ["pods"]          # add "system-reserved","kube-reserved" only with dedicated cgroups
evictionHard:
  memory.available: "2Gi"
  nodefs.available: "10%"
  nodefs.inodesFree: "5%"
  imagefs.available: "15%"
  pid.available: "10%"
evictionSoft:
  memory.available: "4Gi"
  nodefs.available: "15%"
evictionSoftGracePeriod:
  memory.available: "2m"
  nodefs.available: "2m"
evictionMinimumReclaim:
  memory.available: "1Gi"
  imagefs.available: "5Gi"
featureGates: {}                          # avoid alpha gates in production
```

Notes on key items:

- **`cgroupDriver: systemd`** must match the runtime (5.2); mismatch destabilises nodes.
- **`protectKernelDefaults`** makes the kubelet error on start if required sysctls (`vm.overcommit_memory=1`, `kernel.panic=10`, `kernel.panic_on_oops=1`) are not set; set them in node bootstrap (4.17) to guarantee consistent behaviour.
- **`seccompDefault`** applies the runtime's default seccomp profile (needs workloads compatible; some GPU/RDMA tools need exceptions).
- **`serverTLSBootstrap`** and **`rotateCertificates`**: kubelet gets/rotates its certificates via CSRs (5.21); approve serving CSRs with an approver.
- **`maxPods`** (default 110) is limited also by pod CIDR size per node (a `/24` gives ~254 IPs) and CNI. GPU nodes rarely need 110.
- **Image pulls**: `serializeImagePulls: false` + `maxParallelImagePulls` speeds starts for multiple large images on one node; registry QPS prevents hammering a registry.

## 3. cgroups, QoS and node allocatable

### The hierarchy (cgroup v2, systemd driver)

```text
/sys/fs/cgroup/
├── system.slice/                        # OS services incl. kubelet.service, containerd.service
├── kubepods.slice/                      # all pods; memory.max = node allocatable for pods
│   ├── kubepods-pod<uid>.slice/         # Guaranteed pods (directly under kubepods)
│   │   └── cri-containerd-<id>.scope    # container
│   ├── kubepods-burstable.slice/
│   │   └── kubepods-burstable-pod<uid>.slice/...
│   └── kubepods-besteffort.slice/
│       └── kubepods-besteffort-pod<uid>.slice/...
└── user.slice/
```

The kubelet creates `kubepods` and the QoS sub-slices (`cgroupsPerQOS`), sets CPU weights proportional to requests (`cpu.weight`), and enforces the **node allocatable** limit on the `kubepods` cgroup. Pod-level cgroup limits (sum of container limits) exist for non-Guaranteed pods; with cgroup v2 and the MemoryQoS feature `memory.min/memory.high` provide soft protection and throttling before hitting hard limits (check your release's status).

### Node capacity and allocatable

```text
Capacity (reported by kubelet: cpu, memory, ephemeral-storage, pods, hugepages-*, extended resources)
  − kube-reserved (kubelet, container runtime, node problem detector)
  − system-reserved (sshd, udev, systemd, other OS daemons)
  − eviction-threshold (hard)
  = Allocatable   ← what the scheduler uses for pod requests
```

`kubectl describe node` shows Capacity, Allocatable and Allocated resources (sum of requests/limits). Reserve generously on GPU nodes: DCGM, the device plugin, CNI agents, log shippers, storage clients and the GPU driver stack all need CPU and memory, and unreserved nodes die in surprising ways (kernel OOM killing kubelet/containerd, SSH unresponsive). `enforceNodeAllocatable: ["pods"]` (default) enforces only the pods limit; enforcing `system-reserved`/`kube-reserved` requires dedicated cgroups and carefully sized values (misconfigured enforcement kills system daemons).

### QoS recap (details in 5.7)

Guaranteed/Burstable/BestEffort determine cgroup placement, OOM score and eviction order. The kernel OOM killer picks victims by `oom_score` (which includes `oom_score_adj`: kubelet sets -997 for Guaranteed, 1000 for BestEffort, between for Burstable proportional to request/capacity; critical kubelet and runtime processes have -999). System daemons without protection can be killed if the node runs out of memory outside the pods cgroup.

## 4. Resource managers: CPU, memory, topology, devices

### CPU Manager

- **`none`** (default): pods share all CPUs via CFS; limits cause throttling.
- **`static`**: Guaranteed pods requesting **integer** CPUs get **exclusive** cores (removed from the shared pool and pinned via `cpuset`). Benefits for AI: no CFS throttling, no cache/scheduler noise for data-loading threads, NUMA-local placement, deterministic latency for inference. Requires: Guaranteed QoS, integer CPU requests, reserved CPUs configured (`reservedSystemCPUs` or `kubeReserved/systemReserved` CPU); policy options (`full-pcpus-only` avoids sharing hyperthread siblings; `distribute-cpus-across-numa`, `align-by-socket`). Changing the policy requires draining the node and deleting `/var/lib/kubelet/cpu_manager_state`.
- Containers in Burstable/BestEffort pods and non-integer requests use the shared pool.

### Memory Manager

`Static` policy with `reservedMemory` lets Guaranteed pods get NUMA-pinned memory (and hugepages) allocations coordinated with the Topology Manager; the sum of `reservedMemory` across NUMA nodes must equal `kubeReserved + systemReserved + hard eviction threshold` for memory. Useful for latency-critical or hugepage-based workloads (DPDK, some HPC); complex to operate, so enable only when needed.

### Topology Manager

A broker that collects NUMA **hints** from the CPU Manager, Memory Manager and Device Manager (device plugins report topology: GPU NUMA node, NIC NUMA node) and enforces a policy:

| Policy | Behaviour |
|---|---|
| `none` | No alignment (default) |
| `best-effort` | Prefer aligned allocations; admit even if not aligned |
| `restricted` | Admit only if the preferred (minimal number of NUMA nodes) alignment is achieved; else reject with `TopologyAffinityError` |
| `single-numa-node` | Admit only if all resources fit on a single NUMA node |

Scope `container` aligns per container; `pod` aligns all containers of a pod together. For AI nodes the question is how many GPUs a pod needs: 8-GPU training pods span both sockets by design (hints would be non-preferred; use `best-effort`/`none` or per-pod relaxations), while 1 to 4 GPU inference pods benefit from `single-numa-node`/`restricted` so the pod's CPUs, memory, GPU and NIC share a NUMA node and PCIe root. Misalignment shows up as lower DataLoader throughput or GPUDirect RDMA falling back through the CPU interconnect. When alignment cannot be satisfied the pod fails at admission after scheduling (the scheduler is not topology-aware by default; use NFD/topology-aware scheduling (NodeResourceTopology plugin) or DRA to avoid it; 5.18).

### Device Manager and Pod Resources API

Device plugins register with the kubelet over gRPC at `/var/lib/kubelet/device-plugins/kubelet.sock` and expose a socket; `ListAndWatch` streams devices and health; `Allocate` returns injection details (5.8); `GetPreferredAllocation` lets plugins hint better device sets (e.g., NVLink-connected GPUs). The kubelet checkpoints allocations (`/var/lib/kubelet/device-plugins/kubelet_internal_checkpoint`), so restarts keep allocations. The **Pod Resources API** (`/var/lib/kubelet/pod-resources/kubelet.sock`: `List`, `GetAllocatableResources`, `Get`) exposes which pods use which devices/CPUs/memory: used by DCGM exporter and monitoring. **Dynamic Resource Allocation (DRA)** (stable in recent releases) replaces the counting-based device plugin model with `ResourceClaim`s and driver-published `ResourceSlice`s, enabling structured device selection (GPU model, MIG profile, shared claims) and scheduler awareness (Part 11).

## 5. Probes

The kubelet runs probes on a timer per container:

| Probe | Question | On failure |
|---|---|---|
| **startupProbe** | Has the app finished starting? (disables the others until it succeeds) | Container killed and restarted per restartPolicy after `failureThreshold` |
| **readinessProbe** | Can it serve traffic now? | Pod marked NotReady; removed from Service endpoints; not restarted |
| **livenessProbe** | Is it stuck? | Container killed and restarted |

Handlers: `exec` (command inside the container, exit 0 = success), `httpGet` (2xx/3xx), `tcpSocket`, `grpc` (gRPC health protocol). Parameters: `initialDelaySeconds`, `periodSeconds` (10), `timeoutSeconds` (1), `successThreshold`, `failureThreshold` (3), `terminationGracePeriodSeconds` (probe-level override for liveness kills).

Operational rules:

- HTTP/TCP/gRPC probes originate from the **kubelet on the node** to the pod IP (so NetworkPolicy and host firewalls must allow node → pod traffic); `exec` probes run via CRI inside the container (fork cost: expensive at high frequency and in minimal images; avoid shell-heavy probes).
- **Startup probe for slow starts** (LLM weights load, CUDA graph capture, large dataset indexing): `failureThreshold × periodSeconds` is the allowed startup time; this avoids liveness kill loops.
- **Liveness probes must be local and cheap**: check the process is not deadlocked, not external dependencies (a database outage must not restart every app pod); consider omitting liveness for stateful or long-running training workers where restarts are destructive.
- **Readiness for serving**: only ready when the model is loaded and a tiny inference works; flip not-ready during graceful shutdown/drain; make endpoints cheap.
- **Timeouts**: default 1 s often too short on busy nodes; CFS throttling can fail probes of otherwise healthy pods (CPU-limited containers); set realistic `timeoutSeconds`.
- Probe results appear in events (`Unhealthy: Readiness probe failed: ...`) and metrics (`prober_probe_total`).
- **Readiness gates** (`readinessGates`) let external controllers add conditions that must be true (e.g., load balancer registration for cloud LBs).

### Liveness probes, step by step

A process check has a gap. A deadlocked application still has a running process, so a process check calls it healthy. A liveness probe closes that gap by running application logic, such as loading a web page, to confirm the app works. Liveness probes are defined per container, so each container in a Pod is checked separately. Example 5-2 adds a liveness probe to the `kuard` container. It sends an HTTP request to `/healthy` on port 8080:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kuard
spec:
  containers:
    - image: gcr.io/kuar-demo/kuard-amd64:blue
      name: kuard
      livenessProbe:
        httpGet:
          path: /healthy
          port: 8080
        initialDelaySeconds: 5
        timeoutSeconds: 1
        periodSeconds: 10
        failureThreshold: 3
      ports:
        - containerPort: 8080
          name: http
          protocol: TCP
```

The probe waits `initialDelaySeconds` (5 seconds) after all containers in the Pod are created before it first runs. It must answer within the 1-second `timeoutSeconds`. A status code from 200 up to, but not including, 400 counts as success. Kubernetes calls the probe every 10 seconds. When more than three consecutive probes fail, the container fails and restarts.

To see this in action, apply the manifest and port-forward to the Pod:

```
$ kubectl apply -f kuard-pod-health.yaml
$ kubectl port-forward kuard 8080:8080
```

Open http://localhost:8080 in a browser and click the "Liveness Probe" tab. It lists every probe this `kuard` instance has received. Click the "Fail" link, and `kuard` starts failing its health checks. Wait long enough and Kubernetes restarts the container, and the display starts over. Run `kubectl describe pods kuard` to see the restart in the "Events" section, which reads like this:

```
Killing container with id docker://2ac946...:pod "kuard_default(9ee84...)"
container "kuard" is unhealthy, it will be killed and re-created.
```

A failed liveness check restarts the Pod by default. The real behavior depends on the Pod's `restartPolicy`. `Always` is the default. `OnFailure` restarts only on a liveness failure or a nonzero exit code. `Never` does not restart.

### Readiness and startup probes

Liveness asks whether an application is running properly. Readiness asks whether a container can serve user requests now. A container that fails liveness is restarted. A container that fails readiness is removed from service load balancers. Readiness probes are set up much like liveness probes. Using both keeps only healthy containers in service. The book covers Kubernetes Services in its Chapter 7.

A startup probe is the book's answer to slow-starting containers, and the book calls it a recent addition. It runs before any other probe on the Pod. It keeps trying until it either times out, which restarts the Pod, or succeeds. After it succeeds, the liveness probe takes over. The startup probe lets you poll slowly while the container starts, then respond quickly once it is up.

### Advanced probe settings and other handlers

Probes have more options. You can set how long to wait after startup before probing, how many failures count as a real failure, and how many successes reset the failure count. Each option has a default when you leave it out. Set them yourself for applications that are flaky or take a long time to start.

Besides HTTP checks, Kubernetes supports `tcpSocket` probes. A `tcpSocket` probe opens a TCP socket, and it succeeds if the connection works. That suits databases and other non-HTTP APIs. An `exec` probe runs a script or program inside the container. A zero exit code means success, and any other code means failure. `exec` probes suit custom checks that do not fit neatly into an HTTP call.

## 6. Node-pressure eviction

The eviction manager monitors node signals from cAdvisor/cgroup stats at `evictionPressureTransitionPeriod` intervals and compares them with thresholds:

| Signal | Meaning |
|---|---|
| `memory.available` | `capacity − working set` on the node (excluding reclaimable page cache accounted into inactive file) |
| `nodefs.available`, `nodefs.inodesFree` | Root filesystem (kubelet dir, logs, emptyDir) free space/inodes |
| `imagefs.available`, `imagefs.inodesFree` | Container image/writable layer filesystem (if separate) |
| `containerfs.*` | Newer split for container writable layers |
| `pid.available` | PIDs left |

**Hard** thresholds evict immediately (grace 0, `SIGKILL`-like short grace); **soft** thresholds require the condition to persist for `evictionSoftGracePeriod` and use the pod's grace period up to `evictionMaxPodGracePeriod`. Reclaim attempts happen first (garbage collect dead containers and unused images when disk is low). Node conditions `MemoryPressure`, `DiskPressure`, `PIDPressure` are set (and taints `node.kubernetes.io/memory-pressure:NoSchedule` etc. prevent new BestEffort/otherwise pods from scheduling).

**Selection order** when evicting for memory: pods whose usage exceeds requests first (BestEffort counts as request 0), ordered by priority (lower first), then by how far over request they are; for disk pressure, by ephemeral storage usage over request and priority. Guaranteed pods are evicted last (only if system daemons are the problem and nothing else is left). Evicted pods end `Failed` with reason `Evicted`; controllers recreate them elsewhere. Critical pods (priority `system-node-critical`/`system-cluster-critical`, static pods) are protected.

Distinguish **three kill mechanisms**: (1) *kernel OOM killer* in a cgroup (container exceeded its memory limit, or node ran out of memory faster than kubelet could react): process killed, container restarted per policy, `OOMKilled`; (2) *kubelet eviction* (graceful, pod-level, node pressure; ignores PDBs); (3) *API-initiated eviction/preemption/drain* (respects PDBs and priority). For AI nodes: set `evictionHard memory.available` large enough (several GiB) to act before the kernel OOM kills random processes, because workloads with huge page cache and pinned memory can consume memory faster than kubelet's housekeeping (10 s) sampling; prefer Guaranteed pods for important jobs; keep `ephemeral-storage` requests for pods that write scratch to avoid disk-pressure surprises.

## 7. Garbage collection and logs

- **Container GC** removes exited containers beyond `maxPerPodContainer`/`maxContainers` and older than `minimumContainerTTL`-like behaviour (flags `--maximum-dead-containers*` were deprecated in favour of eviction-based cleaning); dead containers consume writable layer space.
- **Image GC**: when image filesystem usage exceeds `imageGCHighThresholdPercent`, remove least-recently-used unused images until `imageGCLowThresholdPercent`; skip images younger than `imageMinimumGCAge`. With 20 to 50 GB ML images, 85% thresholds on a 1 TB disk mean hundreds of GB of headroom is consumed before GC; but then GC may delete the image you need next and trigger a long re-pull; use bigger disks, `imageMaximumGCAge` (newer), and pre-pull policies.
- **Log rotation**: the kubelet rotates CRI logs at `containerLogMaxSize` keeping `containerLogMaxFiles`; training jobs printing per-step logs at high rate can fill disks and add CPU overhead; log to stdout moderately, ship metrics separately, or write detailed logs to a PVC/object storage.
- **Ephemeral storage accounting**: container logs, writable layer and `emptyDir` count toward the pod's ephemeral-storage usage; exceeding `limits.ephemeral-storage` evicts the pod.

## 8. Node status, leases and failure behaviour

- **Heartbeats**: the kubelet renews a **Lease** (`kube-node-lease/<node>`) every `nodeLeaseDurationSeconds/4` (10 s) – cheap; and updates `Node.status` when something changes or every `nodeStatusReportFrequency` (5 min). Node controller's `--node-monitor-grace-period` (40 s) after the last lease/status marks `Ready=Unknown`.
- **Conditions**: `Ready`, `MemoryPressure`, `DiskPressure`, `PIDPressure`, `NetworkUnavailable`; extra conditions from node-problem-detector (e.g., `KernelDeadlock`, `GPUXidError`) used by remediation controllers (5.32, Part 17).
- **Taints**: automatically added by the node lifecycle controller: `node.kubernetes.io/not-ready`, `unreachable` (NoExecute with default 300 s toleration), plus `memory-pressure`, `disk-pressure`, `pid-pressure`, `network-unavailable`, `unschedulable` (cordon). For GPU jobs requiring fast recovery, shorten `tolerationSeconds` for those taints in pod specs; for stateful workloads consider longer values or manual fencing.
- **Graceful node shutdown** (`shutdownGracePeriod`): on systemd hosts the kubelet takes a shutdown inhibitor lock; when the node shuts down, it terminates pods in priority order (regular first, critical last) within the budget, updates node status, then allows poweroff. Combined with draining before maintenance (5.19), this prevents abrupt SIGKILLs of training pods during reboots. **Non-graceful node shutdown** handling lets you apply `node.kubernetes.io/out-of-service` taint after confirming a node is down so StatefulSet pods and their volumes move.
- **Kubelet restart** does not restart containers: it reconciles from the runtime state; checkpointed manager states (`cpu_manager_state`, device checkpoint, memory manager state) persist. Kubelet down ≠ pods down; but NotReady node triggers evictions after the toleration period, and no probes/log rotation/volume operations happen while it's down.

## 9. Static pods, kubelet API and security

- **Static pods**: manifests in `staticPodPath` (`/etc/kubernetes/manifests`) are run directly by the kubelet and mirrored into the API as read-only "mirror pods" (suffix `-<nodename>`). Used for control-plane components in kubeadm, node-critical agents. Editing a file reconfigures immediately; deleting it removes the pod. They cannot use ConfigMaps/Secrets from the API (file-based only) and are not controlled by controllers.
- **Kubelet API (10250)**: authenticated by x509 or bearer tokens (webhook), authorised by webhook (`nodes/proxy`, `nodes/stats`, `nodes/log`, `nodes/metrics` subresources): granting `nodes/proxy` is effectively `exec` rights on every pod on the node, so audit RBAC that includes it (many monitoring roles do). Endpoints: `/pods`, `/runningpods`, `/stats/summary`, `/metrics`, `/metrics/cadvisor`, `/metrics/resource`, `/metrics/probes`, `/logs/`, `/exec`, `/attach`, `/portForward`, `/configz`, `/healthz`. Disable the read-only port 10255 and anonymous auth; keep `authorization.mode: Webhook`.
- **Node authorizer + NodeRestriction admission** limit what a kubelet can read/modify (only its node and pods bound to it; cannot set certain labels like `node-role.*` or `node-restriction.kubernetes.io/*`).
- **Certificates**: kubelet client cert (CN `system:node:<name>`, group `system:nodes`) via TLS bootstrapping, auto-rotation (`rotateCertificates`); serving cert via CSR (`serverTLSBootstrap`) needs approval; expiry causes NotReady nodes (5.21).
- **Hardening checklist**: `protectKernelDefaults`, `seccompDefault`, read-only port off, `--anonymous-auth=false`, `readOnlyPort: 0`, TLS minimum version and cipher suites, `eventRecordQPS`, restrict `hostPath`/privileged via Pod Security, user namespaces for pods (`hostUsers: false`), AppArmor/SELinux, node OS hardening (Part 18).

## 10. Observability

Kubelet metrics (scrape `:10250/metrics`, `/metrics/cadvisor`, `/metrics/probes`): `kubelet_running_pods`, `kubelet_running_containers`, `kubelet_pod_start_duration_seconds`, `kubelet_runtime_operations_duration_seconds`, `kubelet_pleg_relist_duration_seconds`, `kubelet_pleg_relist_interval_seconds`, `kubelet_evictions`, `kubelet_node_name`, `kubelet_certificate_manager_client_ttl_seconds`, `kubelet_volume_stats_*` (PVC usage), `container_cpu_cfs_throttled_periods_total`, `container_memory_working_set_bytes`, `container_oom_events_total`, `prober_probe_total`, `rest_client_requests_total`. Alerts worth having: node NotReady, PLEG relist slow, kubelet certificate expiring, container CPU throttling ratio high on latency-critical pods, disk/inode/PID pressure approaching thresholds, image pull errors, kubelet restarts, runtime operation latency.

Logs: `journalctl -u kubelet -f` (verbosity `--v=2` default; `4` for sync details), runtime logs `journalctl -u containerd`, kernel `dmesg -T` (OOM kills: "Killed process", "oom-kill:constraint=CONSTRAINT_MEMCG"), `/var/log/pods`.

## 11. Troubleshooting guide

| Symptom | Likely cause | Where to look |
|---|---|---|
| Node `NotReady` | Kubelet down/cert expired/runtime down/network | `systemctl status kubelet`, `journalctl -u kubelet`, `kubectl describe node` conditions, `crictl info` |
| `PLEG is not healthy` | Runtime slow/overloaded (many containers, disk IO) or kernel issue | PLEG metrics, containerd CPU/IO, `crictl ps` latency |
| Kubelet crash loop on start | Swap on, cgroup driver mismatch, invalid config, `protectKernelDefaults` sysctl mismatch, cpu manager state mismatch | kubelet journal first lines |
| `TopologyAffinityError` | Topology manager policy cannot align | pod events, policy and device NUMA info, `numactl -H`, `nvidia-smi topo -m` |
| CPU manager state error after changing policy | Stale state file | drain node, remove `cpu_manager_state`, restart |
| Pods evicted with `The node was low on resource: memory` | Memory pressure beyond thresholds, over-request pods | `kubectl describe pod`, node events, kubelet eviction logs, node `memory.available` |
| Pods OOMKilled while node has free memory | Container limit reached (cgroup) | `kubectl describe`, `memory.events`, shm/page cache |
| Node unresponsive/SSH hangs under load | No system reserved, kernel OOM, CPU starvation | reservations, `dmesg`, `systemd-cgtop` |
| Disk pressure, image GC thrash | Small image disk, large images, logs | `df -h`, `crictl imagefsinfo`, log sizes, thresholds |
| Probes failing intermittently | CPU throttling, short timeouts, NetworkPolicy blocking node→pod | `cpu.stat`, probe events, policy |
| `kubectl logs/exec` fails TLS | Serving CSR unapproved | `kubectl get csr`, approve |
| Pods Pending on node with free GPUs | Device plugin not registered/unhealthy, allocatable 0 | `kubectl describe node`, plugin logs, kubelet device-plugin dir |
| Containers can't see GPUs after kubelet/plugin restart | Plugin restart without kubelet resync; runtime hook mis-config | restart order, `ListAndWatch` logs, checkpoint file |
| Time to start high | Serial image pulls, slow CSI, CNI | see 5.8 |

## 12. Tuning checklist for GPU nodes

1. systemd cgroup driver, cgroup v2, kernel and runtime up to date and consistent across nodes (4.17).
2. Reserve CPU (dedicated cores via `reservedSystemCPUs`) and memory/ephemeral-storage for kube/system daemons; set meaningful hard eviction thresholds.
3. CPU Manager `static` with `full-pcpus-only`; Topology Manager policy chosen per node pool (relaxed for 8-GPU training pools, strict for small-GPU inference pools); Memory Manager only if hugepage/NUMA pinning is required.
4. Guaranteed QoS for GPU pods; explicit shm and ephemeral storage; PID limit adequate for multi-process training (`podPidsLimit` ≥ thousands).
5. Image management: large dedicated NVMe image filesystem, parallel pulls, careful GC thresholds, pre-pull DaemonSet.
6. Fast failure handling: node problem detector + remediation, shorter taint tolerations for elastic jobs, `shutdownGracePeriod` for planned reboots.
7. Security: webhook authn/z, rotate certs, approve serving CSRs, seccomp default, no read-only port.
8. Observability: scrape kubelet/cAdvisor, DCGM, NPD; alert on pressure and throttling.
9. Roll changes through drains and canary nodes; keep config in Git (4.26) and verify with `configz`.

## 13. Lab

First, run the self-checking Python lab (`code/part05/kubelet_node_managers_lab.py`) locally. It verifies the Kubelet CPU Manager (`evaluate_cpu_manager_static` with `full-pcpus-only: "true"`), the Topology Manager NUMA hint intersection evaluator (`evaluate_topology_manager`: comparing `single-numa-node`, `restricted`, and `best-effort` policies), and the Node-Pressure Memory Eviction victim selector (`rank_memory_eviction_victims`).

```bash
python3 code/part05/kubelet_node_managers_lab.py
```

Next, on a Linux Kubernetes worker node (all interactive shell steps below are `untested here`), work through these exercises:

1. **Config and allocatable**: print live kubelet config via `configz`; compute allocatable from capacity and reservations by hand; change `kubeReserved`/`systemReserved` and observe `kubectl describe node` changes after restart.
2. **cgroup tree**: with `systemd-cgls`/`systemd-cgtop`, find `kubepods.slice`, QoS slices, pod and container scopes; read `memory.max`/`cpu.weight` for Guaranteed, Burstable, BestEffort pods; match to requests/limits.
3. **QoS and OOM**: create the three QoS pods; read each container's `oom_score_adj`; use a stress image to trigger a container OOM, then node-level memory pressure (lab VM) and observe eviction order and events.
4. **Eviction tuning**: set `evictionHard memory.available` low and high on two nodes; run a memory consumer; compare kubelet-managed eviction vs kernel OOM kills; set soft thresholds and grace.
5. **CPU Manager**: enable `static` on a node (drain, delete state file), run a Guaranteed pod with 4 CPUs, inspect `cpuset.cpus` (`cat /sys/fs/cgroup/.../cpuset.cpus.effective`), `taskset -pc`, and a shared-pool pod's cpuset; compare latency/throttling with and without exclusivity; try `full-pcpus-only` with odd CPU counts.
6. **Topology Manager**: on a multi-NUMA GPU node set `single-numa-node`; request 1 GPU + CPUs and observe aligned allocation (`nvidia-smi topo -m`, `numactl`); request 8 GPUs and observe `TopologyAffinityError`; adjust to `best-effort` for that pool.
7. **Pod Resources API**: query the socket with `grpcurl` or a small client to list devices per pod; compare with DCGM exporter labels.
8. **Probes**: build a server with controllable startup time and failure toggles; test startup/readiness/liveness interplay; demonstrate CPU-throttle-induced probe failures by limiting CPU hard.
9. **Image and log GC**: fill the image filesystem with test images and observe GC; set low `containerLogMaxSize` and a chatty pod; watch rotation and disk usage; compute log retention per pod.
10. **Node failure timeline**: block kubelet → API connectivity with iptables on a worker; record timestamps for lease expiry, `Unknown` condition, taint, pod eviction; repeat with shorter tolerations; then with graceful shutdown (`systemctl reboot`) and `shutdownGracePeriod`.
11. **Static pod**: add a static pod manifest; see the mirror pod; modify and delete; compare with a DaemonSet.
12. **Kubelet API security**: query `:10250` with and without credentials; check `nodes/proxy` RBAC in existing ClusterRoles; verify read-only port closed.
13. **Dashboards/alerts**: build panels for pressure signals, throttling, PLEG latency, eviction counts; write alerts.
14. **Clean up**.

## 14. Common mistakes

- Running GPU nodes with no reserved resources and tiny eviction thresholds; surprise kernel OOM on the node.
- Enabling `static` CPU manager without Guaranteed integer-CPU pods (no effect) or without draining/removing state when switching.
- Using `single-numa-node` for pods that need all 8 GPUs (guaranteed admission failures).
- Liveness probes that call external dependencies; no startup probe for slow model loads; 1 s timeouts on throttled pods.
- Assuming evictions respect PDBs; treating node-pressure eviction as an API eviction.
- Letting image GC delete large ML images repeatedly; tiny image disks.
- Chatty training logs filling disks; no log rotation tuning.
- Granting `nodes/proxy` RBAC broadly; leaving anonymous/read-only kubelet ports on.
- Forgetting to approve kubelet serving CSRs; expired kubelet certificates.
- Changing kubelet config on all nodes at once without canaries.

## 15. Interview angles

- "What does the kubelet do? Walk through its main loops and managers."
- "How is node allocatable computed? Why reserve resources?"
- "Explain QoS classes, OOM scores and eviction."
- "What is the difference between kernel OOM kill, node-pressure eviction and API eviction?"
- "What do the CPU, Memory and Topology Managers do? When would you use `static` and `single-numa-node` for AI?"
- "How do probes work and what are common mistakes?"
- "What happens when a node loses network connectivity to the control plane?"
- "How would you tune kubelet for an 8-GPU training node versus a 1-GPU inference node?"

## Exercises

1. **Designing a Production `KubeletConfiguration` for Dual-Socket 8-GPU Nodes:** Walk through the `KubeletConfiguration` in Section 2, explaining why `cgroupDriver: systemd`, `protectKernelDefaults: true`, `seccompDefault: true`, `serializeImagePulls: false` (`maxParallelImagePulls: 3`), `reservedSystemCPUs: "0-3"`, `kubeReserved` / `systemReserved`, and `evictionHard` / `evictionSoft` are set as shown.
2. **The Cgroup v2 Hierarchy (`kubepods.slice`), QoS Placement, and `Node Allocatable`:** Trace the `/sys/fs/cgroup` tree under `systemd` (`system.slice`, `kubepods.slice`, `kubepods-burstable.slice`, `kubepods-besteffort.slice`), explain why `Guaranteed` pods sit directly under `kubepods.slice`, and calculate `Allocatable` from `Capacity`, `kubeReserved`, `systemReserved`, and `evictionHard`.
3. **CPU Manager (`static` + `full-pcpus-only`), Memory Manager (`Static`), and Topology Manager (`single-numa-node` vs. `best-effort`):** Using `evaluate_cpu_manager_static()` and `evaluate_topology_manager()` in `code/part05/kubelet_node_managers.py`, explain: (a) what happens when a `Guaranteed` Pod requests 3 CPUs on an SMT-enabled host with `full-pcpus-only: "true"`; (b) why `/var/lib/kubelet/cpu_manager_state` must be removed when changing CPU Manager policy; and (c) why 1–4 GPU inference pools use `topologyManagerPolicy: single-numa-node` whereas 8-GPU training pools use `best-effort` (or `restricted` with `pod` scope).
4. **Device Manager (`ListAndWatch`, `Allocate`, `GetPreferredAllocation`), Pod Resources API, and Dynamic Resource Allocation (`DRA`):** Explain how the NVIDIA device plugin registers at `/var/lib/kubelet/device-plugins/kubelet.sock`, how `kubelet_internal_checkpoint` preserves GPU assignments across `kubelet` restarts, how `dcgm-exporter` uses `/var/lib/kubelet/pod-resources/kubelet.sock`, and what `DRA` (`ResourceClaim`, `ResourceSlice`) improves over integer device counting.
5. **Node-Pressure Eviction Signals (`memory.available`, `nodefs`, `imagefs`, `pid.available`), Victim Ranking, and the Three Kill Mechanisms:** Using `rank_memory_eviction_victims()` in `code/part05/kubelet_node_managers.py`, trace the exact order in which `kubelet` selects Pods for eviction under `MemoryPressure`, and contrast (1) Kernel Cgroup OOM Kill (`OOMKilled`), (2) Kubelet Node-Pressure Eviction (`Reason: Evicted`), and (3) API-Initiated Eviction (`kubectl drain`).
6. **Graceful Node Shutdown (`shutdownGracePeriod`), Static Pods, and Kubelet API Security (`:10250`, `nodes/proxy`, `NodeRestriction`):** Explain how `shutdownGracePeriod` (`120s`) and `shutdownGracePeriodCriticalPods` (`30s`) use systemd inhibitor locks to drain Pods cleanly during OS reboots, how Static Pods and mirror Pods work, and why granting `nodes/proxy` RBAC permissions is a major security risk.

## Checkpoint questions (20)

<details>
<summary>1. How do you inspect the live `KubeletConfiguration` running on a specific worker node from `kubectl`?</summary>

Query the node's `/configz` endpoint through the API server proxy:
```bash
kubectl get --raw "/api/v1/nodes/<node-name>/proxy/configz" | jq .kubeletconfig
```
This returns the exact merged `KubeletConfiguration` currently active in memory on that `kubelet`.
</details>

<details>
<summary>2. What does `protectKernelDefaults: true` in `KubeletConfiguration` do?</summary>

When `protectKernelDefaults: true` is set, `kubelet` **refuses to start** if any kernel `sysctl` parameter (`vm.overcommit_memory = 1`, `vm.panic_on_oom = 0`, `kernel.panic = 10`, `kernel.panic_on_oops = 1`, `kernel.keys.root_maxkeys = 1000000`, `kernel.keys.root_maxbytes = 25000000`) differs from the values `kubelet` expects—instead of attempting to mutate host kernel tunables at runtime. This enforces CIS Kubernetes Benchmark compliance and ensures kernel parameters are managed declaratively in node bootstrap (Ansible/Packer).
</details>

<details>
<summary>3. Where are `Guaranteed`, `Burstable`, and `BestEffort` Pods placed inside `/sys/fs/cgroup/kubepods.slice` when `cgroupsPerQOS: true` and `cgroupDriver: systemd` are used?</summary>

- **`Guaranteed` Pods:** Placed **directly under `kubepods.slice/`** as `/sys/fs/cgroup/kubepods.slice/kubepods-pod<uid>.slice/cri-containerd-<id>.scope`.
- **`Burstable` Pods:** Placed under **`kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod<uid>.slice/...`**.
- **`BestEffort` Pods:** Placed under **`kubepods.slice/kubepods-besteffort.slice/kubepods-besteffort-pod<uid>.slice/...`**.
`kubepods.slice` itself has its `memory.max` set to the node's **Allocatable** memory (`enforceNodeAllocatable: ["pods"]`) so user Pods combined can never encroach on `kubeReserved` + `systemReserved` + `evictionHard`.
</details>

<details>
<summary>4. Why is `reservedSystemCPUs: "0-3"` preferred over `kubeReserved.cpu` + `systemReserved.cpu` when using `cpuManagerPolicy: static` on a GPU node?</summary>

When `cpuManagerPolicy: static` is active, `kubelet` must know **which specific physical CPU cores** to keep in the shared/system pool so it never pins a user `Guaranteed` Pod onto the cores running `kubelet`, `containerd`, `sshd`, kernel softirqs, or NVMe/NIC interrupts. Specifying **`reservedSystemCPUs: "0-3"`** explicitly reserves hardware threads `0..3` (on NUMA node 0) for OS and Kubernetes daemons, leaving all remaining cores cleanly available for exclusive `cpuset` assignment.
</details>

<details>
<summary>5. What three requirements must a Pod meet to receive exclusive pinned CPU cores from `cpuManagerPolicy: static`, and what does `full-pcpus-only: "true"` add?</summary>

1. The Pod's QoS class must be **`Guaranteed`** (every container sets CPU and memory `requests == limits`).
2. The container must request a **whole integer number of CPUs** (`cpu: "8"`, `cpu: "16"`—not `cpu: "7500m"`).
3. With **`cpuManagerPolicyOptions: { full-pcpus-only: "true" }`** on an SMT (Hyper-Threading) server with 2 threads per physical core, the container must request a **multiple of 2 vCPUs** (`2, 4, 8, 16...`) so `kubelet` allocates complete physical cores (both hyperthread siblings) and prevents two different containers from sharing the L1/L2 cache and execution units of the same physical core. If a Guaranteed container requests an odd number of vCPUs (e.g., `3`) under `full-pcpus-only: "true"`, `kubelet` rejects the Pod at node admission (`SMTAlignmentError`).
</details>

<details>
<summary>6. Why does `kubelet` fail to start with `policy ... is not allowed to be changed` after you edit `cpuManagerPolicy` or `reservedSystemCPUs` in `/var/lib/kubelet/config.yaml`, and how do you fix it?</summary>

`kubelet` persists its current CPU assignments and policy name in **`/var/lib/kubelet/cpu_manager_state`** (and `/var/lib/kubelet/memory_manager_state`). If you change `cpuManagerPolicy` (`none` -> `static`) or `reservedSystemCPUs` without clearing that checkpoint file, `kubelet` refuses to start to avoid corrupting live container `cpuset`s. Always **drain the node first**, stop `kubelet`, **`sudo rm -f /var/lib/kubelet/cpu_manager_state`**, and start `kubelet`.
</details>

<details>
<summary>7. Compare the four `topologyManagerPolicy` modes (`none`, `best-effort`, `restricted`, `single-numa-node`) and explain which to use for 1–4 GPU inference nodes vs. 8-GPU HGX training nodes.</summary>

- **`none` (default):** Performs no NUMA alignment between CPUs, memory, GPUs, and NICs.
- **`best-effort`:** Stores the preferred NUMA affinity hint and tries to align resources on the minimal set of NUMA nodes, **but still admits the Pod** if alignment is impossible.
- **`restricted`:** Admits the Pod **only** if all requested resources can be allocated on the **minimum theoretical number of NUMA nodes** required by the request size (for example, 1 NUMA node for a 2-GPU pod, or 2 NUMA nodes for an 8-GPU pod on a dual-socket server); otherwise rejects with `TopologyAffinityError`.
- **`single-numa-node`:** Admits the Pod **only** if **all** requested CPUs, memory, GPUs, and NICs fit on a **single NUMA node** (`1–4` GPUs on one socket).
**Rule of thumb:** Use **`single-numa-node`** (with `topologyManagerScope: pod`) on **1–4 GPU inference pools** so CPUs, RAM, GPU, and NIC never cross the inter-socket UPI/Infinity Fabric link; use **`restricted` or `best-effort`** on **8-GPU training pools** where a single Pod intentionally spans both CPU sockets (all 8 GPUs).
</details>

<details>
<summary>8. What are the three gRPC methods of the Kubernetes Device Plugin API, and what does `GetPreferredAllocation` do on an 8-GPU NVLink/PCIe node?</summary>

Every device plugin (`nvidia-device-plugin`, SR-IOV/RDMA plugin) registers with `/var/lib/kubelet/device-plugins/kubelet.sock` and implements:
1. **`ListAndWatch`:** Streams the list of device IDs (`GPU-uuid-0..7`), their **health status** (`Healthy` vs `Unhealthy` on XID faults), and their **NUMA topology hints** to `kubelet`.
2. **`GetPreferredAllocation`:** When a Pod requests a subset of GPUs (e.g., `2` or `4` GPUs out of `8`), `kubelet` calls `GetPreferredAllocation(available_gpus, required_count)` so the NVIDIA plugin can pick a **topologically optimal subset** (e.g., 2 GPUs sharing the same NVLink bridge or PCIe switch rather than 2 GPUs on opposite sockets).
3. **`Allocate`:** Called during `syncPod` to get the exact `NVIDIA_VISIBLE_DEVICES` env vars, `/dev/nvidia*` device paths, and CDI annotations for the chosen GPUs.
</details>

<details>
<summary>9. How does `kubelet` compute `memory.available` for Node-Pressure Eviction, and why is it different from `free` in `/proc/meminfo`?</summary>

Linux aggressively uses free RAM for filesystem **page cache** (`Buffers`/`Cached` in `/proc/meminfo`), so raw `MemFree` is almost always near zero on a busy node even when plenty of memory is reclaimable. Instead, `kubelet` reads cgroup memory stats (`memory.stat`) and computes:
`memory.available = NodeCapacity - working_set`
where **`working_set = total_usage - total_inactive_file`** (i.e., anonymous/heap memory + pinned memory + `/dev/shm` tmpfs + active file cache, excluding easily reclaimable `inactive_file` page cache).
</details>

<details>
<summary>10. What is the difference between `evictionHard`, `evictionSoft`, and `evictionMinimumReclaim` in `KubeletConfiguration`?</summary>

- **`evictionHard` (e.g., `memory.available: "2Gi"`, `nodefs.available: "10%"`):** As soon as the signal drops below the hard threshold, `kubelet` **immediately evicts Pods with a 0-second grace period** (`SIGKILL`).
- **`evictionSoft` + `evictionSoftGracePeriod` (e.g., `memory.available: "4Gi"` for `"2m"`):** If `memory.available` stays below `4Gi` continuously for 2 minutes, `kubelet` triggers a **graceful eviction** (honoring the Pod's `terminationGracePeriodSeconds` up to `evictionMaxPodGracePeriod`)—giving training jobs time to write an emergency checkpoint before hitting `evictionHard`.
- **`evictionMinimumReclaim` (e.g., `memory.available: "1Gi"`, `imagefs.available: "5Gi"`):** Once an eviction is triggered, `kubelet` continues evicting/reclaiming until at least `threshold + minimumReclaim` (`2Gi + 1Gi = 3Gi`) is free, preventing rapid oscillation right at the threshold boundary.
</details>

<details>
<summary>11. In what exact order does `kubelet` choose which Pod to evict first during `MemoryPressure`?</summary>

`kubelet` ranks all active Pods on the node into two tiers and evicts from the top of the list:
1. **Tier 1 — Pods whose memory usage (`working_set`) EXCEEDS their memory request** (note: `BestEffort` Pods have `request = 0`, so any `BestEffort` Pod using > 0 bytes is in Tier 1 alongside `Burstable` Pods exceeding their request). Ordered by **lowest `PriorityClass` first**, and then by **largest `(usage - request)` byte excess**.
2. **Tier 2 — Pods whose memory usage is BELOW or EQUAL to their memory request** (`Burstable` Pods within request and `Guaranteed` Pods). Ordered by **lowest `PriorityClass` first**, and then by usage. (`Guaranteed` Pods and `system-node-critical` Pods are never evicted unless system daemons themselves exceed reserved memory.)
</details>

<details>
<summary>12. What is the difference between `nodefs` and `imagefs` in `kubelet` disk-pressure eviction?</summary>

- **`nodefs`:** The node's root filesystem where `/var/lib/kubelet` lives—holding **Pod `emptyDir` volumes (disk-backed), `/var/log/pods` container logs, and kubelet state**. When `nodefs.available < 10%`, `kubelet` deletes dead pods/containers and evicts Pods using the most ephemeral storage (`logs + emptyDir`).
- **`imagefs`:** The filesystem where `/var/lib/containerd` stores **pulled container image layers and container writable layers**. Putting `/var/lib/containerd` on a dedicated NVMe partition separates `imagefs` from `nodefs` so pulling 30 GB container images never fills the OS root disk (`nodefs`).
</details>

<details>
<summary>13. Why can a CPU-limited container (`limits.cpu: "2"`) fail its `httpGet` or `exec` `livenessProbe` even when the application has zero bugs, and how do you fix it?</summary>

When a container has a strict CFS CPU quota (`limits.cpu`) and experiences a burst of request or garbage-collection activity, the Linux kernel throttles all threads in the container for the remainder of the 100ms CFS period (`nr_throttled` in `cpu.stat`). If `livenessProbe.timeoutSeconds` is left at the default **`1` second**, a few consecutive throttled periods delay the HTTP `/healthz` handler past 1,000 ms, causing `kubelet` to kill and restart a healthy container. Fix it by:
1. Raising **`timeoutSeconds` to `5`–`10` seconds** on probes.
2. Removing `limits.cpu` (keeping `requests.cpu`) or using `cpuManagerPolicy: static` so latency-sensitive servers are never CFS-throttled.
</details>

<details>
<summary>14. How do `nodeStatusUpdateFrequency` (`10s`) and `nodeStatusReportFrequency` (`5m`) work together with `kube-node-lease` to reduce API server load on a 5,000-node cluster?</summary>

In early Kubernetes, every `kubelet` PATCHed its entire heavy `Node.status` object (containing dozens of conditions, addresses, capacity, and a list of the 50 largest container images on the node) every 10 seconds—which overwhelmed `etcd` at 5,000 nodes.
Today:
- Every **`10s` (`nodeStatusUpdateFrequency` / `nodeLeaseDurationSeconds/4`)**, `kubelet` updates only its tiny ~200-byte **`Lease` object** in `kube-node-lease`.
- `kubelet` only sends a full **`Node.status` update** when a condition/capacity actually changes OR once every **`5 minutes` (`nodeStatusReportFrequency`)**—cutting `etcd` heartbeat write load by >95%.
</details>

<details>
<summary>15. How does Graceful Node Shutdown (`shutdownGracePeriod: 120s`, `shutdownGracePeriodCriticalPods: 30s`) work on a `systemd` Linux host?</summary>

When `shutdownGracePeriod` is configured, `kubelet` acquires a **systemd delay inhibitor lock** via D-Bus (`systemd-inhibit --list`). When an operator or cloud autoscaler initiates an OS shutdown (`systemctl reboot` / `poweroff` / spot termination ACPI signal), `systemd` delays the actual shutdown for up to `120s` and notifies `kubelet`:
1. **First `90s` (`120s - 30s`):** `kubelet` marks the node not-ready (`Shutdown` condition) and terminates all regular user Pods (running their `preStop` hooks and sending `SIGTERM` so training jobs can flush a final checkpoint).
2. **Final `30s` (`shutdownGracePeriodCriticalPods`):** `kubelet` terminates `system-node-critical` / `system-cluster-critical` Pods (CNI,CSI, storage flushers) and releases the systemd inhibitor lock so the kernel powers off cleanly.
</details>

<details>
<summary>16. What are the differences between a Static Pod (`/etc/kubernetes/manifests`) and a `DaemonSet` Pod?</summary>

- **Static Pod:** Managed directly by the local **`kubelet`** reading a file on disk (`/etc/kubernetes/manifests/*.yaml`), with **zero dependency on `kube-apiserver` or `kube-scheduler`**. Cannot reference `ConfigMap`s or `Secret`s, cannot be deleted via `kubectl delete pod` (deleting the mirror Pod in `kube-apiserver` causes `kubelet` to recreate it immediately), and is used for bootstrapping `etcd`, `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, and `kube-vip`.
- **`DaemonSet` Pod:** Managed by the **`DaemonSet` controller** in `kube-controller-manager` and scheduled by `kube-scheduler` through `kube-apiserver`. Can mount `ConfigMap`s, `Secret`s, and PVCs, supports rolling updates across the fleet, and is used for node agents (`nvidia-device-plugin`, `dcgm-exporter`, `calico-node`/`cilium`, `fluent-bit`).
</details>

<details>
<summary>17. Why is granting RBAC permission on `nodes/proxy` (`verbs: ["*"]` or `["get", "create"]`) equivalent to granting root/exec access to every Pod on every node?</summary>

The `nodes/proxy` subresource authorizes direct proxying to the **Kubelet HTTPS API (`:10250`)**—which includes the `/exec`, `/run`, `/attach`, and `/portForward` endpoints for every container on the node. An attacker or compromised monitoring ServiceAccount with `nodes/proxy` `create`/`get` permission can execute arbitrary commands inside any `kube-system` or tenant Pod on any node, completely bypassing namespace-level `pods/exec` RBAC rules. Monitoring scrapers (Prometheus) should only be granted **`nodes/metrics`** and **`nodes/stats`** (`get`), never `nodes/proxy`.
</details>

<details>
<summary>18. What do the `Node` Authorizer and `NodeRestriction` Admission Plugin prevent a compromised worker node's `kubelet` from doing?</summary>

Every `kubelet` authenticates to `kube-apiserver` as `system:node:<nodename>` (in group `system:nodes`). If a single worker node is compromised:
- **The `Node` Authorizer** restricts `system:node:<nodename>` so it can **only read `Secret`s, `ConfigMap`s, and `PV`s mounted by Pods currently scheduled onto `<nodename>`**—it cannot read Secrets belonging to Pods on other nodes.
- **The `NodeRestriction` Admission Plugin** restricts `system:node:<nodename>` so it can only modify its **own** `Node` and bound `Pod` status objects, and **forbids the kubelet from adding or modifying `node-role.kubernetes.io/*` or `node-restriction.kubernetes.io/*` labels** on itself (so a compromised worker cannot relabel itself as a control-plane or trusted security node).
</details>

<details>
<summary>19. Why should `podPidsLimit` (and `evictionHard["pid.available"]`) be configured explicitly on multi-GPU training nodes?</summary>

A single 8-GPU PyTorch `torchrun` job spawns 8 rank processes, each spawning 8–16 `DataLoader` worker processes, OpenMP/MKL thread pools, and NCCL proxy threads—easily creating **500 to 2,000 Linux tasks (PIDs) per Pod** (in Linux, every thread is a task consuming a PID from `/proc/sys/kernel/pid_max`). Setting `podPidsLimit: 8192` (or `16384`) in `KubeletConfiguration` (which writes `pids.max` in each Pod's cgroup) gives legitimate multi-GPU training jobs enough headroom while still preventing a runaway fork bomb in one container from exhausting the host's global `kernel.pid_max` and crashing `sshd`/`kubelet`.
</details>

<details>
<summary>20. Contrast the `KubeletConfiguration` tuning for an 8-GPU HGX Training Node vs. a 1-GPU / MIG Multi-Tenant Inference Node.</summary>

| Setting | 8-GPU HGX Training Node (1 Pod = Whole Node) | 1-GPU / MIG Multi-Tenant Inference Node (Many Pods) |
|---|---|---|
| `maxPods` | Low (`30`–`40`: system daemons + 1 training pod) | Standard (`60`–`110`) |
| `topologyManagerPolicy` | `restricted` or `best-effort` (pod spans 2 sockets) | `single-numa-node` (`scope: pod`) for strict PCIe/NUMA locality |
| `cpuManagerPolicy` | `static` (`full-pcpus-only: "true"`) | `static` (`full-pcpus-only: "true"`) |
| `podPidsLimit` | High (`8192`–`32768`) for multi-process DataLoaders | Moderate (`2048`–`4096`) |
| `shutdownGracePeriod` | Long (`120s`–`300s`) to allow emergency checkpointing | Moderate (`60s`–`120s`) for connection draining |
</details>

## Sources and review notes

- **Sources read in full:**
  - `production-kubernetes` — Josh Rosso, Rich Lander, Alexander Brand & John Harris, *Production Kubernetes*, **Chapter 3: Container Runtime** (node runtime, CRI, and cgroup considerations).
  - `kubernetes-up-and-running-3rd-edition` — Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, *Kubernetes: Up and Running*, 3rd ed., **Chapter 5: Pods** (probes, resource requests/limits, volumes, and node behavior).
  - `nvidia-devops` (`volume-03/02-k8s-node-storage-masterclass.md`): node operations masterclass (`KubeletConfiguration` for AI nodes, CPU/Memory/Topology/Device managers, eviction and QoS, CRI and sandbox, and `crictl` debugging).
- **Run here:** `python3 code/part05/kubelet_node_managers_lab.py` (3 passed, 0 failed).
- **Explicitly labelled inferences:** The `evaluate_cpu_manager_static`, `evaluate_topology_manager`, and `rank_memory_eviction_victims` models in `code/part05/kubelet_node_managers.py` and the production GPU `KubeletConfiguration` (Section 2) are the author's constructions synthesizing `PK` Chapter 3, `KUR` Chapter 5, and `volume-03/02` (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, and 40).
- **Not verified on live hardware:** Live `kubelet`, `systemd-cgls`, `numactl`, and `grpcurl` executions (`169.254.20.10`, `50Mi`, `110` maxPods, `8192` podPidsLimit, `85%`/`70%`/`80%` image GC, `120s`/`30s` shutdownGracePeriod, `reservedSystemCPUs: "0-3"`, `4Gi`/`8Gi` reserved, `2Gi`/`4Gi` eviction, `-997`/`-999`/`1000` oom_score_adj, `:10250`, `10255`) are marked (`untested here`) where not executed by `kubelet_node_managers_lab.py`.
