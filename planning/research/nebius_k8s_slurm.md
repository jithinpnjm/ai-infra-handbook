# Research notes for 20.36: Managed Kubernetes and Soperator

Fetched 2026-11-11. Tags: [official] Nebius docs, [vendor] Nebius blog, [source-code] public repo, [third-party], [inference] my reasoning.
Work dir: /private/tmp/claude-501/v20/w36 (clones and docs saved there).

## Repositories read

- [source-code] github.com/nebius/soperator, shallow clone, commit f10392e1264a (2026-11-10, merge of PR 3250). VERSION file says 5.0.0.
  - README.md: Soperator turns a SlurmCluster resource into a Slurm cluster. Requirements table: Ubuntu 24.04, Slurm 26.05.4-nebius-1 (Nebius fork), CUDA above 13.0, NCCL 2.28 or newer, Kubernetes 1.35 or newer, Cilium recommended. Three deployment paths (self-deploy, Managed Service for Soperator, Soperator Pro).
  - docs/architecture.md: three node types (login, controller, worker) are pods in StatefulSets. Jail is a shared PV mounted as root. SPANK "chroot" plugin does pivot_root after slurmd forks. PAM module does the same for SSH. populate-jail runs once as a Job. Namespace plugin gives per-job tmpfs for /tmp, /dev/shm, /mnt/memory (needs cgroup v2).
  - docs/passive-checks.md: prolog, epilog and HealthCheckProgram (every 120 s) run check_runner.py. Exit 1 only. Reason prefixes decide automation. BatchStartTimeout 10 s shared with prolog. hc_program killed after 60 s. Reason strings become metric labels. Simulated failure marker file for GPU check.
  - docs/active-checks.md: ActiveCheck CR maps 1:1 to a CronJob. k8sJob or slurmJob. Reactions drainSlurmNode and commentSlurmNode. backoffLimit 0. gpu_checks license caps 200 nodes at once.
  - docs/worker-node-rollout.md: slurmAwareRollingUpdate, handoff via `scontrol reboot` with power action soperator-worker-handoff, PDB maxUnavailable 0 excluding pods labelled phase ready, OpenKruise ContainerRecreateRequest, metrics soperator_rollout_*.
  - docs/ephemeral-nodes.md: State=CLOUD nodes, NodeSetPowerState, power-manager, ResumeTimeout 1800 s default (Slurm default 60 s), SuspendTime 600, SuspendTimeout 90.
  - docs/topology.md: topology.yaml from node labels topology.nebius.com/tier-N, tree, block and flat types, fabric per NodeSet.
  - docs/slurm-configuration.md: scontrol edits are not persistent, ConfigMap limit 1 MiB, JailedConfig plus sconfigcontroller, Reconfigure.
  - docs/limitations.md: GPU-required, single partition (note: the docs also describe partitionConfiguration, so this file may be stale), scale-down leaves nodes in slurmctld memory.
  - docs/login-pod-updates.md: delayedRollout, minNotice 720h default.
  - docs/slurm-exporter.md: slurm_node_info, slurm_node_fails_total labels.
  - api/v1/slurmcluster_types.go, api/v1alpha1/nodeset_types.go, nodesetpowerstate_types.go, activecheck_types.go; config/crd/bases/*.yaml (six CRDs).
  - Go: internal/controller/soperatorchecks/slurm_nodes_controller.go (processDegradedNode, processSetUnhealthy, hardwareIssuesMessage), k8s_nodes_controller.go (drain conditions, NotReady delete), internal/consts/slurm.go (reason list order) and conditions.go, cmd/soperatorchecks/main.go (flags), internal/controller/clustercontroller/reconcile.go (order: populate jail, common, accounting, sconfigcontroller, controllers, login, REST, exporter), internal/render/controller/statefulset.go (controller replicas is a constant single replica).
  - helm: slurm-cluster, nodesets, soperator-activechecks, soperatorchecks (values default enableNodeReplacement false while the binary flag default is true), soperator-fluxcd (umbrella: cert-manager, kruise, mariadb-operator, victoria-metrics, otel collectors, dcgm exporter, nfs).
  - config/samples/*.yaml are empty scaffolds ("TODO(user)"), so the validated examples come from `helm template` output, not from the samples directory.
- [source-code] github.com/nebius/nebius-solutions-library, commit 3db4054d463d (2026-11-10). soperator/VERSION 4.1.18.
  - soperator/README.md (Terraform install flow, slurm_nodeset_workers fields rolling_update_strategy, drain_timeout, max_unavailable_percent).
  - soperator/modules/k8s/k8s_cluster.tf (nebius_mk8s_v1_cluster, public endpoint, audit logs), k8s_ng_workers_v2.tf (node group: auto_repair conditions, strategy max_unavailable 50 percent, max_surge 0, drain_timeout, taint nvidia.com/gpu NO_SCHEDULE, gpu_cluster, gpu_settings drivers_preset, filesystems attach jail), gpu_fabric_validation.tf, installations/example/driver_presets.tf (cuda13.0 for Kubernetes 1.35 and 1.36).
  - modules/slurm/templates/helm_values/flux_release_nodesets.yaml.tftpl: worker spool is `emptyDir: {}`.
  - Also listed: k8s-training, k8s-inference, modules (gpu-operator, network-operator, kuberay...). Not read in depth.

## Nebius docs fetched (all [official], as markdown via docs.nebius.com/<path>.md)

- /llms.txt (index; searched for SLA and release channel pages: none)
- /kubernetes (overview), /kubernetes/components, /kubernetes/versions, /kubernetes/manage-versions, /kubernetes/version-deprecation
- /kubernetes/maintenance/index, /kubernetes/maintenance/manage, /kubernetes/maintenance/health-checks
- /kubernetes/node-groups/manage (deployment strategy and parameters, GPU settings), /kubernetes/node-groups/autoscaling, /kubernetes/node-groups/reservations (skimmed)
- /kubernetes/gpu/set-up (driver presets cuda12.8 570.x, cuda13.0 580.x), /kubernetes/gpu/clusters (InfiniBand node groups)
- /kubernetes/networking/add-ons (CoreDNS and Cilium managed, not configurable via API), /kubernetes/resources/quotas-limits, /kubernetes/storage/filesystem-over-csi (skimmed), /kubernetes/monitoring
- /slurm-soperator/overview/architecture, /overview/why-slurm-soperator, /worker-nodes-health, /managed-soperator/service-nodes, /monitoring/statuses, /monitoring/metrics, /capacity/ephemeral-nodes, /managed-soperator/manage, /deploy/overview
- [vendor] nebius.com/blog/posts/soperator-in-open-source-explained, dated 24 Sep 2024, by the Managed Schedulers team leader. Used only for date and authorship.
- [third-party] WebSearch result pages (not relied on): Yandex Cloud release channel pages. They describe another product. Not used.

## Key facts recorded

1. mk8s control plane: API server, scheduler, cluster autoscaler, controller manager, etcd. Default three etcd members, HA at no extra cost [official]. Nodes are Compute VMs; "do not modify" them in Compute [official]. Node group max 100 nodes. Cilium and CoreDNS are service-managed add-ons.
2. Node group rolling update default: max unavailable 1, max surge 0, cordon, drain, delete, create. Default drain timeout 10 minutes then force drain [official]. Surge needs extra quota.
3. Health checks via Node Problem Detector. NebiusBootDiskIOError after 30 s of I/O errors. Ready False over 5 min or Unknown over 15 min: delete and recreate. GPU checks every 5 min using nvidia-smi, dcgmi, dmesg (Xid, ECC): NebiusGPUError true leads to cordon, wait for GPU workloads, drain up to 1 h, stop and start VM [official]. Enabled by default for clusters created 1 Dec 2025 or later (search result snippet of the health-check enable page; the health-checks page itself I read does not state the date).
4. Maintenance: NebiusMaintenanceScheduled condition with SLA deadline in the message. Batch size 1 or maxUnavailable. Waits for GPU pods until one hour before the SLA deadline. Labels nebius.com/perform-maintenance and nebius.com/defer-maintenance-node-drain [official].
5. Versions: 1.36 recommended, no more than four minor versions offered, deprecated version stays two months, automatic upgrade at end of life, node groups only upgraded when skew requires [official, 2026-11-11]. Manual upgrade: control plane first then node groups. No automatic upgrade otherwise.
6. Soperator on Nebius disables most mk8s auto-repair conditions on worker node groups to avoid races, keeping only HardwareIssuesSuspected with a 1 s timeout [source-code, k8s_ng_workers_v2.tf].
7. Platform side of replacement: soperator sets node condition HardwareIssuesSuspected; "the platform" calls Compute SetUnhealthy with unlimited retries then replaces the node; a per-tenant limit of unhealthy reports exists [source-code, docs/passive-checks.md]. The numeric limit is not published.
8. Managed Soperator service nodes: 2 controller, 1 accounting, 3 to 5 system nodes, 8vcpu-32gb each [official]. The source's controller StatefulSet is a single replica, so what the second controller node does is not documented here.
9. Chart discrepancy: nodesets chart default `spool.volumeClaimTemplateSpec` is not in the NodeSet CRD schema (spool is a corev1.VolumeSource). Reproduced with tools/check_crd_yaml.py (see below). The Terraform recipe uses emptyDir.

## What I looked for and did NOT find

- Managed Kubernetes SLA terms: not in the docs index and I did not fetch the legal page. Chapter 20.33 cites a 99.90% control plane target from a page I did not re-check.
- Release channels for Managed Kubernetes: none documented; versions are chosen explicitly.
- Soperator internals of Nebius's platform component that calls SetUnhealthy (closed source), the unhealthy-report limit, how Managed Soperator runs its second controller node.
- Conference talks or transcripts about Soperator: not searched in depth (no fetch). Only the 2024 blog post was read, and only for date.
- Slurm 26.05.4 "Nebius fork" patch list: the repo github.com/nebius/slurm was not read.
- Autoscaler scale-down timing and GPU-specific autoscaler behaviour: the autoscaling page gave only the principles.
- Managed Soperator SLA, pricing: out of scope.

## Validation log

- `python3 -I tools/check_crd_yaml.py soperator/config/crd/bases/slurm.nebius.ai_*.yaml -- code/part20/c36_crd_examples/*.yaml`: 7 resources, 0 problems.
- Before the fix the same tool reported 4 problems on the raw `helm template` output (NodeSet spool.volumeClaimTemplateSpec, three times, and a nodeSetRef written as an object).
- `helm template` run with Helm v4.2.3 locally, charts slurm-cluster, nodesets, soperator-activechecks at default values.
