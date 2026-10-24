---
id: "c06-16"
title: "6.16 Slurm on Kubernetes: Slinky and Soperator"
sidebar_label: "6.16 Slurm on Kubernetes: Slinky and Soperator"
sidebar_position: 16
description: "Running Slurm clusters on Kubernetes: why, the two open-source approaches (Slinky slurm-operator and Nebius Soperator) with their CRDs and design, drain/cordon coordination, shared root (jail), active health checks, ephemeral nodes, and how to choose between bare-metal Slurm, Slurm on Kubernetes, and native Kubernetes batch (Kueue)"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.16 Slurm on Kubernetes: Slinky and Soperator

| | |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | kind or a GPU Kubernetes cluster |
| Part | Part 6: HPC and Slurm |
| Status | Drafted from the projects' own repositories and docs, read in shallow clones on 2026-10-24: SlinkyProject/slurm-operator (commit `7e01fc1`, 2026-10-21) and nebius/soperator (commit `b2a58e1`, 2026-10-23). Nothing was deployed. CoreWeave's SUNK is proprietary and described from general knowledge only. Labs **untested** |

## Why this matters for AI infrastructure

Two worlds meet in AI clusters. Researchers and HPC veterans want Slurm: gang-scheduled multi-node jobs, fair-share, accounting, `sbatch`. Platform teams want Kubernetes: declarative infrastructure, GitOps, self-healing, multi-tenant services, a single control plane for training, inference and data services. Neoclouds (CoreWeave, Nebius) and large AI labs run Kubernetes everywhere and therefore need Slurm on top of it. Knowing how that is built (and what it costs) is directly relevant to roles at those companies; the NVIDIA, CoreWeave and Nebius job families all touch it.

## Prerequisites and outcomes

Needs 6.7 to 6.15, 5.29 and 5.31 to 5.33 (CRDs, operators, reading operators), and 5.35 (multicluster). After this chapter you can:

- Explain why and when to run Slurm on Kubernetes versus bare-metal Slurm or native Kubernetes batch schedulers.
- Describe Slinky's `slurm-operator` architecture (CRDs, NodeSet controller, dynamic nodes, drain coordination) and Soperator's design (`SlurmCluster`, jail, health checks, ephemeral nodes).
- Identify the hard problems: node identity, shared state, upgrades, GPU drivers, InfiniBand, cgroups and containers in containers.
- Choose and evaluate an approach for a given platform, and list the questions to ask.

## 1. The motivation and the tension

Slurm excels at "quickly scheduling workloads that run for a finite amount of time, with well-defined resource requirements and topology, on multiple nodes, with strict policy, but its resource pool is known"; Kubernetes at "workloads that typically run for an indefinite amount of time, with potentially vague resource requirements, on a single node, with loose policy, but can scale its resource pool infinitely" (the Slinky README's framing, in my condensation). The reason to combine them:

- **One infrastructure layer**: the same Kubernetes cluster, node lifecycle, observability, CI/CD and security tooling for Slurm and non-Slurm workloads; capacity can move between training (Slurm) and inference (Kubernetes services).
- **Declarative operations**: cluster = YAML in Git; the operator handles bootstrap, upgrades, healing.
- **Elasticity**: Slurm workers as pods scale with demand (and to zero).
- **Isolation**: many small Slurm clusters per team or tenant instead of one huge shared one.

Costs and risks:

- **Two schedulers** can disagree: Kubernetes places Slurm worker pods; Slurm places jobs on those pods. Capacity fragmentation, double accounting, confusing failure semantics (a Kubernetes eviction kills a Slurm node mid-job).
- **Pods are not hosts**: `slurmd` expects a machine; cgroups, device access, systemd, SSH access, shared home directories, user identity, MPI/NCCL host networking and IB devices all need deliberate design.
- **Extra moving parts** (operator, CRDs, storage classes, CNI) and a new failure domain.
- **Performance sensitivity**: AI training wants bare-metal-like networking (host network, RDMA devices, SR-IOV or device plugins) and NUMA/CPU pinning; container layers must not interfere.

## 2. Slinky: `slurm-operator`

Slinky is SchedMD's project (the Slurm maintainers). The operator manages the lifecycle (creation, upgrade, graceful shutdown) of Slurm components as Kubernetes resources, with a Helm chart as a reference deployment.

### CRDs (from `config/crd/bases` and the README)

| CRD | Represents |
|---|---|
| `Controller` | The Slurm control plane (`slurmctld`); HA by enabling `controller.ha.enabled` and a ReadWriteMany PVC for state (`controller.persistence.existingClaim`), matching the shared `StateSaveLocation` requirement of 6.15; configuration changes recreate controller pods by default, or reconfigure in place with `controller.inplaceReconfigure=true` |
| `NodeSet` | A set of homogeneous Slurm workers (`slurmd` pods). `scalingMode` selects **StatefulSet** behaviour (fixed `replicas`, stable ordinal names such as `gpu-2-1`, scale-to-zero, HPA compatible) or **DaemonSet** behaviour (one pod per matching Kubernetes node, `replicas` ignored, 1:1 mapping between Kubernetes nodes and Slurm nodes) |
| `LoginSet` | Login (submit) nodes using SSSD for identity; scale to zero supported |
| `Accounting` | `slurmdbd` and its database connection |
| `RestApi` | `slurmrestd` |
| `Token` | JWT/authentication tokens for the REST API and operator-to-Slurm calls |

### How the operator talks to Slurm

The key idea: the operator must make Kubernetes decisions (scale in, upgrade, replace a pod) **with knowledge of Slurm state**. It therefore keeps a map of Slurm clients (via `slurmrestd` with JWT) and consults them. From the architecture docs it relies on required Slurm features: **configless** (workers fetch config from the controller), **`auth/slurm`** and **`auth/jwt`**, and **dynamic nodes** (pods register themselves with the controller at startup rather than being listed in `slurm.conf`; this is how elastic pods can exist; see 6.15), plus dynamic topology and node features.

Design points from `docs/concepts/nodeset-controller.md`:

- **Node state visibility**: each NodeSet pod carries pod conditions mirroring its Slurm node state (Idle, Allocated, Mixed, Down, Drain, Not Responding...), so `kubectl` shows scheduler state.
- **Scale-in lifecycle**: before deleting a pod the controller **drains** its Slurm node and waits until it is drained (no running jobs), then deletes the pod; if the node is still busy it checks again later. Upgrades follow the same pattern.
- **Drain and cordon coordination** (the flowchart in the doc): cordoning a Kubernetes node triggers a Slurm drain of the pods on it; annotating a pod with a pod-cordon annotation drains the Slurm node; uncordoning reverses it. The controller also sets the annotation itself when it selects a pod for scale-in. **All drain reasons the operator sets are prefixed `slurm-operator:`; reasons without that prefix are treated as externally owned (set by admins or health-check tools via `scontrol`) and are never modified or cleared.**

That last rule is the same discipline built into the GPU health operator in 5.32: mark what you changed, touch only what you marked, never undo a human's drain. It is the central safety property of any controller that shares a resource with people and other automation.

- **Hybrid support**: some Slurm components in Kubernetes and others outside (for example controllers on bare metal and elastic worker pods in Kubernetes), supported by design.
- **Compatibility**: the README's matrix ties operator releases (1.0.x to 1.3.x) to supported Kubernetes minors (1.35 and later at the time of reading); the project follows upstream Kubernetes support.

### What it does not do for you

Slinky manages Slurm daemons; it does not install GPU drivers or the NVIDIA stack (use the GPU Operator, 5.33), does not provide the fabric (network operator, SR-IOV), and does not itself solve user home directories or shared software (you provide storage classes). The reference chart is configurable but you own the integration.

## 3. Soperator (Nebius)

Soperator turns one `SlurmCluster` custom resource into a complete AI-oriented Slurm cluster, from the Nebius repository (`nebius/soperator`) described as "an open-source Kubernetes operator for running Slurm clusters for AI training and high-performance computing". Its README lists three goals: simple cluster management, high reliability, efficient GPU use.

### Architecture (from `docs/architecture.md`)

- Three node types, each a Kubernetes Pod group (StatefulSets): **Login**, **Controller**, **Worker/Compute**. The operator is built with Kubebuilder; the top-level reconcile code is `internal/controller/clustercontroller/reconcile.go`.
- Slurm and system config files are rendered into ConfigMaps; Munge and SSH server keys live in Secrets. Container file systems are ephemeral; persistence uses Persistent Volumes.
- **The jail**: the "real magic". A shared Persistent Volume (the *jail*) is mounted on all worker and login nodes and contains **another root directory**, possibly a different Linux distribution. When a user logs in or runs a job, the jail is their `/`. So a package installed, a user created or a checkpoint written on one node appears on all nodes. This removes per-node drift, the classic "software differs between nodes" problem of 6.6 and 6.22, and makes Slurm behave like a bare-metal cluster with a golden shared image. The cost: the jail is shared storage on the critical path (performance of `/usr` and Python imports; locking; blast radius of a corrupted root), so the storage backend choice matters.
- **Images** contain much of the product logic (drivers, CUDA, NCCL, `nccl-tests`, Slurm builds, SSSD, SSH): the README stresses a preinstalled training stack with an explicit CUDA-to-NCCL version mapping, and the docs advise deriving from the provided images rather than writing your own.
- **Health and replacement**: passive health checks (control-plane signals, node conditions such as NVMe health) and **`ActiveCheck`** custom resources that run scheduled probes either as Kubernetes Jobs or as Slurm jobs on some or all nodes (GPU performance, system, storage, network/InfiniBand, hardware acceptance); failed nodes are drained and replaced automatically. Checks are deployed through GitOps (Flux) as a Helm chart and can be customised by cluster owners.
- **Ephemeral nodes and autoscaling**: workers created on demand and scaled down when unused; **InfiniBand topology awareness** (placement constraints, excluding CPU-only nodes from the IB tree).
- **Integrations**: SSSD (LDAP/AD/FreeIPA), Tailscale for SSH, Prometheus/Grafana/Loki, Helm and Argo/Flux, cert-manager, Cilium, and the NVIDIA GPU Operator; Pyxis/Enroot and OCI runtimes for container jobs (6.13).
- **Versions at the time of reading** (README): Ubuntu 24.04 node images, a Nebius-patched Slurm 26.05 build, CUDA 13.x, NCCL 2.28 or newer, Kubernetes 1.35 or newer. The `docs/limitations.md` file (single partition, GPUs required, scaling-down leftovers in `sinfo`) appears to lag the README (which mentions CPU-only exclusion handling and fuller scheduling features); trust neither blindly: check the current releases and test your requirements.

### Deployment options

Self-deploy on any Kubernetes, or Nebius-managed services (managed Soperator, "Pro" with engineering support), per the README. Terraform recipes in the repository target Nebius.

## 4. SUNK and other approaches (general knowledge, unverified)

CoreWeave offers **SUNK** (Slurm on Kubernetes), a proprietary integration that exposes Slurm to customers on CoreWeave's Kubernetes-native cloud, with Kubernetes-aware scheduling so that Slurm jobs and Kubernetes workloads share nodes. Details beyond that are not public in the sources I have; use CoreWeave documentation. Other patterns: Run:ai or Kueue as the primary scheduler with a "Slurm-like" front end; Volcano; custom Slurm-in-container projects; and vendor stacks (NVIDIA Base Command Manager can manage both, Part 8).

## 5. Choosing

| Question | Lean toward |
|---|---|
| Many existing Slurm users/scripts, multi-node training dominant | Slurm (bare metal or Slurm on Kubernetes) |
| Mixed training and inference on shared GPUs, GitOps everywhere | Slurm on Kubernetes (Slinky/Soperator/SUNK) or Kubernetes-native (Kueue + JobSet/Kubeflow Trainer) |
| Small team, few clusters | Whatever you can operate: bare-metal Slurm is simplest to reason about |
| Strong multi-tenant isolation with different images and policies | Several small Slurm clusters on Kubernetes |
| Maximum, predictable network performance with minimal layers | Bare-metal Slurm or Slurm on Kubernetes with host networking and device passthrough, validated by `nccl-tests` (6.28) |
| Need Kubernetes-native tooling for researchers (notebooks, services, pipelines) | Kubernetes-native batch (Part 11, 14) |
| Platform vendor provides it (Nebius managed, CoreWeave SUNK) | Use the managed option unless you need control |

Evaluation questions: How are GPU drivers and the host stack provided to worker pods? How do pods get RDMA devices and pin CPUs? How is user identity and `$HOME` handled? What is the state-storage and HA story? What happens on node failure mid-job (requeue, drain, replace)? How are upgrades sequenced (Slurm version, operator, Kubernetes, drivers) and can they be rolled back? What is the scaling model (static vs ephemeral)? How do Kubernetes quota/priority and Slurm fair-share interact? Who owns observability and on-call? Is there a path to run it multi-cluster?

## 6. Operating considerations

- **Two control planes, two upgrade tracks**: pin Kubernetes, operator, Slurm and driver versions together; read compatibility matrices; stage upgrades (6.15 rules apply to Slurm inside).
- **Failure semantics**: a Kubernetes node drain or eviction must translate into a Slurm drain first (the operators implement this); a hard node failure still kills the job: checkpointing remains essential.
- **State**: controller state on RWX storage (Slinky HA) or a PVC with backups; accounting database as a managed service or operator-managed with backups.
- **Resource requests**: worker pods should request whole nodes' GPUs, CPUs and memory (Guaranteed QoS, static CPU manager policy, topology manager) so Kubernetes does not oversubscribe or throttle them (5.9, 5.11).
- **Observability**: DCGM, node and Slurm metrics (Slurm exporter), logs from `slurmctld`/`slurmd` pods, ActiveCheck results (Part 17).
- **Security**: privileged or capability-rich pods are needed for `slurmd`, cgroup management, device access; isolate namespaces, restrict who can edit the CRs, protect Munge/JWT secrets (5.21).

## 7. Reading the code (follows 5.33)

Method from 5.33: start at the API types, then `SetupWithManager`, `Reconcile`, state/rendering, readiness. For Slinky read `api/`, `internal/controller/nodeset`, `docs/concepts/*`; for Soperator read `api/`, `internal/controller/clustercontroller/reconcile.go`, `images/`, `docs/architecture.md` and `docs/active-checks.md`. Compare with the GPU Operator: Slinky resembles it in modelling components as CRs with drain-aware lifecycle; Soperator additionally owns the image and root filesystem.

## 8. Lab (untested)

1. On kind, install cert-manager and the Slinky chart; create a Controller and a NodeSet with CPU workers; submit a Slurm job from a LoginSet pod; scale the NodeSet and watch `sinfo` drain nodes before pod deletion.
2. Cordon a Kubernetes node and observe the Slurm node going to DRAIN with a `slurm-operator:` reason; set your own reason with `scontrol` and confirm the operator preserves it.
3. Read the Soperator docs; write a one-page comparison with Slinky: node model, shared filesystem, health checks, image strategy.
4. Design (on paper) a GPU deployment: GPU Operator, network operator, Soperator or Slinky, storage for jail or state, IB topology; list the failure drills.
5. Run `nccl-tests` as a Slurm job inside the Kubernetes-hosted Slurm and compare bus bandwidth with the bare-metal figure for the same nodes (needs hardware).

## 9. Interview angles

- Why run Slurm on Kubernetes? What problems does it introduce?
- Describe how an operator should scale in a Slurm worker pod safely.
- How does the operator distinguish its own drains from an administrator's?
- What is the Soperator jail and what are its trade-offs?
- Slinky NodeSet StatefulSet vs DaemonSet scaling modes?
- How would you give Slurm pods RDMA and pinned CPUs?
- How do you upgrade Slurm, the operator and Kubernetes in a Slurm-on-Kubernetes cluster?
- When would you choose Kueue and JobSet instead?

## 10. Checkpoint questions (25)

1. State the Slurm versus Kubernetes workload contrast.
2. List three benefits and three costs of Slurm on Kubernetes.
3. Who maintains Slinky? Who maintains Soperator?
4. Name Slinky's CRDs.
5. What does `scalingMode` choose?
6. What Slurm features does the Slinky operator require and why?
7. How does Slinky enable controller HA?
8. What is the scale-in lifecycle of a NodeSet pod?
9. What does the `slurm-operator:` drain-reason prefix guarantee?
10. How does a Kubernetes cordon propagate to Slurm?
11. What is hybrid support?
12. What does Soperator's `SlurmCluster` resource describe?
13. What is the jail?
14. What problem does the jail solve and what risks does it add?
15. What are ActiveChecks and their two execution modes?
16. How are checks deployed?
17. What is ephemeral node scaling?
18. Which integrations does Soperator list?
19. Why might docs disagree with the README?
20. What is SUNK, and how reliable is what you know about it?
21. List five evaluation questions.
22. Why must worker pods use Guaranteed QoS and CPU pinning?
23. How do upgrade tracks interact?
24. What does a node failure mean for a running job?
25. How does 5.32's safety design relate to Slinky's drain prefix?

## 11. Sources and review notes

- Slinky: `README.md`, `docs/concepts/architecture.md`, `docs/concepts/nodeset-controller.md`, CRD names in `config/crd/bases` (commit `7e01fc1`). Soperator: `README.md`, `docs/architecture.md`, `docs/active-checks.md`, `docs/limitations.md` (commit `b2a58e1`). All restated in my own words; short phrases quoted from the READMEs for the Slurm/Kubernetes contrast and the Soperator tagline.
- Context: 5.29 to 5.35 (operators and fleets), 6.13 and 6.15 in this part.
- Unverified: SUNK details, current feature completeness of either project, performance overhead, behaviour of any component at scale. Nothing was deployed or executed.
