---
id: "c05-20"
title: "5.20 Upgrades, etcd backup and restore, and disaster recovery"
sidebar_label: "5.20 Upgrades, etcd backup and restore, and disaster recovery"
sidebar_position: 20
description: "Planning and executing Kubernetes upgrades (version skew, kubeadm, node pools, add-ons, API deprecations), etcd backup/restore procedures, control-plane and cluster disaster recovery, application/PV backup with Velero and snapshots, DR strategies (active/passive, active/active, rebuild-from-Git), RPO/RTO and game days for GPU platforms"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 5.20 Upgrades, etcd backup and restore, and disaster recovery

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | kubeadm cluster (3 CP + 2 workers), etcdctl/etcdutl, Velero + MinIO, a second empty cluster/VMs for restore |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Kubernetes releases a minor version about three times a year and supports each for roughly a year, so a GPU platform is always one or two upgrades away from running an unsupported version; every upgrade touches the control plane, the container runtime, CNI/CSI, the GPU Operator and driver stack, kernels, and sometimes API versions that your operators still use. At the same time training clusters hold irreplaceable state: etcd (all object state), PersistentVolumes (datasets, checkpoints, registries, metadata DBs), secrets and keys, and the knowledge in GitOps repos. A botched upgrade or lost etcd can strand thousand-GPU jobs; a regional outage can idle the whole fleet. Mature teams practise upgrades routinely, test restores, and know their recovery objectives.

## Prerequisites and outcomes

Needs 5.4, 5.5, 5.19. After this chapter you can:

- Explain Kubernetes versioning, support windows, and skew policy among control-plane components, kubelet, kubectl and clients; plan an upgrade path.
- Execute a kubeadm upgrade (control plane then nodes) and the equivalent for managed services, with pre-flight checks (API deprecations, add-on compatibility, backups), canaries, drains and rollback strategy.
- Upgrade the GPU stack (drivers, toolkit, operators) safely in step with Kubernetes.
- Back up and restore etcd (snapshots, certificates, multi-member restore), and rebuild failed control planes.
- Design backup/DR for workloads and data: GitOps as source of truth, Velero/CSI snapshots, volume replication, object-storage durability; define RPO/RTO per tier.
- Run DR drills and handle realistic failure scenarios (lost etcd quorum, corrupted data, expired certificates, accidental namespace deletion, regional loss).

## 1. Versioning and skew

- Versions are `v1.<minor>.<patch>`. Minor releases roughly every 4 months; patch releases roughly monthly. The project supports **the three most recent minor releases** (about 14 months of patches).
- **Skew policy** (verify the current doc): `kube-apiserver` instances in an HA control plane may differ by one minor during rolling upgrade (newest `n`, oldest `n-1`); `kube-controller-manager`, `kube-scheduler`, `cloud-controller-manager` must not be newer than the API server and may be up to one minor older; **`kubelet` may be up to three minors older** than the API server (never newer) in recent releases (two before 1.28); `kube-proxy` same as kubelet; `kubectl` ±1 minor of the API server. Therefore the standard order is **upgrade control plane first, then nodes**, one minor at a time (no skipping minors for the control plane), and clients/operators last or in step.
- **Feature gates and API lifecycle**: alpha (off by default), beta (on by default for many APIs, but beta APIs are off by default since 1.24), GA; deprecated APIs are removed after at least 9 months or 3 releases (GA APIs are not removed within v1). Removed APIs break manifests, Helm charts and operators that still use them (e.g., `policy/v1beta1` PodSecurityPolicy removal in 1.25, `batch/v1beta1` CronJob in 1.25, `flowcontrol.apiserver.k8s.io/v1beta2` etc.). Always read the changelog "Urgent upgrade notes" and "Deprecation" sections.
- **Component compatibility** beyond Kubernetes itself: container runtime (containerd versions per Kubernetes), CNI (Calico/Cilium support matrix), CSI drivers and sidecars, ingress controllers, cert-manager, Prometheus operator, GPU Operator/driver/toolkit/device plugin/DCGM, Kueue and training operators, service meshes, Argo CD/Flux, CoreDNS/etcd versions shipped by kubeadm. Build a compatibility matrix per target version (5.19).

## 2. Upgrade planning

**Checklist before touching anything:**

1. **Objective and window**: target version (usually latest patch of next minor), who is affected, freeze period for critical training runs, rollback criteria.
2. **Read release notes** (urgent notes, deprecations, changed defaults, kubelet/containerd changes, CNI/CSI notes). Review KEPs affecting your features (DRA, sidecars, cgroup v1 deprecation, etc.).
3. **Detect deprecated/removed API usage**: `kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis`, audit logs, tools `pluto detect-helm`/`detect-files`, `kubent`, `kubectl-convert`, Helm chart `helm template | kubeconform -kubernetes-version 1.xx`. Upgrade charts/operators/CRDs to versions that support both old and new Kubernetes where possible *before* the cluster upgrade.
4. **Compatibility matrix check** for add-ons and the GPU stack; stage upgrades of add-ons that support both versions first.
5. **Backups**: etcd snapshot (and copies off the node), PV snapshots/Velero backups of critical namespaces, export of cluster-scoped config (CRDs, RBAC, webhooks), GitOps repo is the source for the rest. Verify the backup is restorable (do a restore drill at least before the first production upgrade).
6. **Health baseline**: all nodes Ready, no crashlooping system pods, API/etcd metrics normal, PDB audit (`kubectl get pdb -A`: any with 0 allowed disruptions?), capacity headroom for rolling node drains.
7. **Staging rehearsal**: upgrade a representative non-production cluster (same CNI/CSI/GPU stack, ideally a few GPU nodes) and run conformance + workload smoke tests (5.25).
8. **Communication and runbook**: published schedule; escalation path; abort and rollback steps; success checks.

**Strategies:**

| Strategy | How | Pros | Cons |
|---|---|---|---|
| **In-place rolling** | Upgrade control plane nodes sequentially, then drain/upgrade workers pool by pool | No extra capacity (beyond headroom); standard | Risk of partial failure; rollback means restoring from backup or downgrading components (not supported for etcd/API) |
| **Surge node pools** (managed) | Add new nodes on the new version, drain old | Continuous capacity | Needs spare GPU quota/capacity (rare for GPUs); use `maxUnavailable` instead |
| **Blue/green cluster** | Build new cluster on new version, shift workloads gradually (GitOps, MultiKueue, DNS) | Easy rollback; test fully before cutover; clean state | Double capacity (hard for GPUs), data migration, identity/networking duplication |
| **Cluster API rolling** | Declarative upgrade of `KubeadmControlPlane` and `MachineDeployment` | Automates replace-not-patch | Needs CAPI maturity |

For GPU clusters, in-place rolling with canary pools and strict drain choreography is typical; blue/green is attractive for major platform shifts (CNI change, major GPU stack change) if you can borrow capacity.

## 3. kubeadm upgrade procedure

On a single minor-version upgrade (example 1.30 → 1.31); commands and flags must be verified against the docs for your versions.

```bash
# 0. Pre-flight (on a control-plane node)
kubeadm version; kubectl version; kubectl get nodes -o wide
sudo kubeadm upgrade plan                         # shows available versions, component versions, needed manual actions
sudo ETCDCTL_API=3 etcdctl snapshot save /backup/pre-upgrade-$(date +%F-%H%M).db \
  --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key

# 1. First control-plane node
sudo apt-mark unhold kubeadm && sudo apt-get update && sudo apt-get install -y kubeadm=1.31.x-* && sudo apt-mark hold kubeadm
sudo kubeadm upgrade plan
sudo kubeadm upgrade apply v1.31.x                # upgrades static pod manifests (apiserver, controller-manager, scheduler, etcd), certs renewed, kube-proxy/CoreDNS addons, then waits for health
# 2. Drain, upgrade kubelet/kubectl on that node, uncordon
kubectl drain cp1 --ignore-daemonsets
sudo apt-mark unhold kubelet kubectl && sudo apt-get install -y kubelet=1.31.x-* kubectl=1.31.x-* && sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload && sudo systemctl restart kubelet
kubectl uncordon cp1

# 3. Other control-plane nodes (one at a time)
sudo apt-get install -y kubeadm=1.31.x-*    # then:
sudo kubeadm upgrade node                         # NOT `apply`: upgrades local static pods using the stored config
# drain, upgrade kubelet/kubectl, restart kubelet, uncordon

# 4. Workers (batches; canary first)
kubectl drain w1 --ignore-daemonsets --delete-emptydir-data --grace-period=600 --timeout=30m
# on w1:
sudo apt-get install -y kubeadm=1.31.x-* && sudo kubeadm upgrade node
sudo apt-get install -y kubelet=1.31.x-* && sudo systemctl daemon-reload && sudo systemctl restart kubelet
kubectl uncordon w1
kubectl get nodes   # VERSION column updates
```

Notes and gotchas:

- **etcd** is upgraded by `kubeadm upgrade` to the version bundled for the target (may change minor versions); stacked etcd members upgrade as their control-plane node does; do one node at a time and confirm `etcdctl endpoint health --cluster` between nodes.
- **Certificates** are renewed during `kubeadm upgrade` (unless `--certificate-renewal=false`), a useful annual side effect (5.21).
- **Config**: kubeadm stores `ClusterConfiguration` in `kube-system/kubeadm-config`; edit with `kubeadm upgrade apply --config` if you change flags. Custom manifest edits made by hand under `/etc/kubernetes/manifests` are lost on upgrade unless expressed in the kubeadm config (use `extraArgs`, `extraVolumes`, or patches directory `--patches`).
- **kubelet config** (`/var/lib/kubelet/config.yaml`) is regenerated from the cluster-wide `kubelet-config` ConfigMap on `upgrade node`; per-node overrides need patches.
- **Addons**: `kubeadm upgrade` updates CoreDNS and kube-proxy only; CNI, CSI, ingress, GPU Operator, monitoring and everything else are your responsibility.
- **API server rolling**: while control plane nodes are at mixed versions, controllers use the older API behaviours; keep the window short; don't run create/update of new fields until all are upgraded.
- **Time**: control plane ~5 to 10 min per node; workers dominated by drains.
- **Rollback**: Kubernetes does not support downgrading the control plane in place (etcd data and API storage versions may have advanced). Rollback = restore the pre-upgrade etcd snapshot and old binaries/manifests on all control-plane nodes (a disruptive procedure) or fall back to a blue/green cluster. Therefore rehearsal and canaries are critical, and workers can be rolled back individually (re-image/reinstall previous kubelet) since older kubelets within skew are fine.

### Managed services

GKE/EKS/AKS: upgrade control plane via API/console/Terraform (the provider handles HA rollout), then node pools by surge or blue/green node-pool replacement with maintenance windows/exclusions and release channels (rapid/regular/stable). GPU node pools: set `maxUnavailable`/surge according to spare capacity, disable auto-upgrade for pools with reservations and pin node image versions until the driver stack is validated, and test GPU driver version bundled with node images (GKE installs drivers per node image/version; EKS-optimised GPU AMIs bundle a driver version). Provider auto-upgrades can break custom stacks; use maintenance exclusions during critical runs (4.24).

## 4. Upgrading the GPU and platform stack

Order of operations (typical, verify per vendor docs):

1. Review the NVIDIA GPU Operator/driver/toolkit/device plugin/DCGM/MIG manager compatibility with the target Kubernetes and OS/kernel.
2. Upgrade **operators and CRDs** compatible with both old and new Kubernetes first (Helm chart upgrades via GitOps, CRD handling per 4.25).
3. Upgrade the control plane, then node pools.
4. For **driver upgrades**: with operator-managed drivers, use the operator's upgrade controller (`ClusterPolicy.spec.driver.upgradePolicy`: `autoUpgrade`, `maxParallelUpgrades`, `drain` options, `waitForCompletion`, pod deletion/ eviction policy) to cordon, drain GPU pods, reload the driver, validate, uncordon node by node; with host-installed drivers, use Ansible `serial` flows (4.17). Coordinate with training: checkpoint-and-drain windows, quotas for in-flight jobs, and fail-safe if validation fails (keep node cordoned).
5. **Kernel/OS** upgrades require reboot and DKMS/precompiled driver rebuild; pin and test combos; roll by rack.
6. Validate after each batch: node Ready, `nvidia.com/gpu` allocatable correct, DCGM exporter up, `nvidia-smi` pod test, NCCL smoke test across the upgraded batch (4.17), network operator secondary networks present.
7. Upgrade **kubectl, CI/CD tools, client libraries, controllers built with older client-go** thereafter; operators compiled against removed APIs need new versions.

## 5. Backing up and restoring etcd

### Backup

```bash
export ETCDCTL_API=3
EP="--endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key"
etcdctl $EP snapshot save /backup/etcd-$(hostname)-$(date -u +%FT%H%M%SZ).db
etcdutl snapshot status /backup/etcd-....db -w table       # hash, revision, total keys, size (integrity check)
sha256sum /backup/etcd-....db > /backup/etcd-....db.sha256
# Ship off-cluster, encrypted, versioned, immutable (object lock); retain per policy
aws s3 cp /backup/etcd-....db s3://dr-bucket/etcd/ --sse aws:kms
# Also back up: /etc/kubernetes/pki (CA keys!), /etc/kubernetes/*.conf, /etc/kubernetes/manifests, kubeadm config, encryption config + KMS keys
```

Automation: a CronJob on a control-plane node (hostNetwork, hostPath mounts of PKI and backup dir) or systemd timer running every 15 to 60 minutes; managed tools (Velero doesn't back up etcd directly; etcd-operator-style backup via `etcd-backup-restore` from Gardener, Kubernetes-native CronJobs, cloud snapshots of etcd volumes with consistency caveats). **Secrets in snapshots**: contain all Secrets (encrypted only if encryption at rest was enabled; with KMS you also need the KMS key) — treat backups as top-secret. Store the **cluster CA private keys** securely; without them, restoring/rebuilding the PKI is far harder. Monitor backup age and size; alert when a backup fails or is older than the RPO.

Hot backups are consistent point-in-time snapshots (MVCC); taking them from one healthy member is sufficient. Snapshot size ≈ DB size (hundreds of MB to a few GB).

### Restore scenarios

**A. One etcd member failed (quorum intact)** — replace, don't restore:

```bash
etcdctl $EP member list -w table
etcdctl $EP member remove <failed-member-id>          # remove the dead one FIRST
# rebuild the node; for kubeadm stacked etcd: on a new control-plane node run `kubeadm join --control-plane ...` (adds a learner, promotes)
etcdctl $EP member list -w table; etcdctl $EP endpoint health --cluster
```

**B. Quorum lost (majority of members gone) or data corrupted** — restore from snapshot. The restore creates a **new cluster** from the snapshot (new cluster ID); all members must be restored from the same snapshot.

```bash
# 1. Stop API servers and etcd on ALL control-plane nodes (kubeadm: move static pod manifests away)
sudo mkdir -p /etc/kubernetes/manifests.disabled && sudo mv /etc/kubernetes/manifests/{kube-apiserver,etcd}.yaml /etc/kubernetes/manifests.disabled/
sudo crictl ps | grep -E 'etcd|apiserver'   # wait until gone
# 2. On each control-plane node restore the snapshot into a fresh data dir with its own name/peer URL
sudo mv /var/lib/etcd /var/lib/etcd.bak-$(date +%s)
sudo etcdutl snapshot restore /backup/etcd-snap.db \
  --name cp1 --data-dir /var/lib/etcd \
  --initial-cluster cp1=https://10.0.0.11:2380,cp2=https://10.0.0.12:2380,cp3=https://10.0.0.13:2380 \
  --initial-advertise-peer-urls https://10.0.0.11:2380 --initial-cluster-token etcd-restore-$(date +%s)
# (repeat on cp2, cp3 with their names/URLs; ensure the manifest's --initial-cluster flags match, kubeadm manifests use these defaults)
# 3. Restore manifests (etcd first, wait healthy; then kube-apiserver)
sudo mv /etc/kubernetes/manifests.disabled/etcd.yaml /etc/kubernetes/manifests/
etcdctl $EP endpoint health --cluster
sudo mv /etc/kubernetes/manifests.disabled/kube-apiserver.yaml /etc/kubernetes/manifests/
kubectl get nodes; kubectl get pods -A
```

Single-member shortcut for a lab: restore one member with `--initial-cluster cp1=...` only (a one-node cluster), then `member add` the others (they must have empty data dirs). For disaster scenarios with total loss: rebuild nodes with the same hostnames/IPs/certs from backups, restore the snapshot, then re-join.

**Expected effects of restore**: the cluster state rewinds to the snapshot time. Objects created after are gone (their pods remain running on nodes until kubelets reconcile, and then orphaned containers are removed or restarted); objects deleted after are resurrected; PV/PVC bindings may reference volumes that no longer match (cloud disks created after the snapshot exist but aren't known); node leases/status refresh quickly; controllers re-reconcile everything to the restored desired state (including scaling replicas back), e.g., a Deployment scaled up after the snapshot returns to the older replica count; Jobs may rerun; operator status can be stale; certificates/tokens issued after the snapshot are invalid (service account tokens are bound to objects that may not exist). Plan to restart controllers/operators and reconcile external state (cloud resources, DNS, load balancers). Resource versions reset relative to clients; informers relist.

**C. Lost control plane but etcd data intact on disk**: rebuild nodes, copy the etcd data dir/PKI, or restore from the latest snapshot.

**D. Expired certificates** (a common outage after one year): `kubeadm certs check-expiration`; renew with `kubeadm certs renew all` on each control-plane node and restart static pods (move manifests out and back, or restart kubelet); also renew kubelet client/serving certs if rotation failed; update `admin.conf` copies (5.21).

**E. Accidental deletion of a namespace/critical object**: restore from GitOps (re-sync), Velero backup, or etcd snapshot restored to a *scratch* cluster to extract the objects (`kubectl get -o yaml`) and re-apply into production (safer than rewinding production).

### Test restores

A backup you never restored is a hope. Schedule quarterly restore drills into an isolated VM cluster; measure RTO; verify the restored cluster boots, objects exist, and a sample workload runs (disable external side effects: scale controllers down, block egress, remove cloud credentials to avoid the restored cluster acting on real resources — a restored cluster thinks it owns your load balancers and disks!).

## 6. Application and data backup

Layers of protection:

| Layer | What | Tools |
|---|---|---|
| **Declarative config** | Manifests, Helm values, policies, CRDs | Git + GitOps (4.26); the primary way to recreate cluster state |
| **Cluster objects** | Namespaces, CRs created at runtime (not in Git), Secrets | Velero, Kasten K10, Trilio; periodic `kubectl get` exports for cluster-scoped objects |
| **Persistent data** | PV contents | CSI snapshots (`VolumeSnapshot`), Velero with CSI/restic/Kopia file-system backup, storage-native replication (Ceph RBD mirroring, cloud disk snapshots, FSx backups, Lustre HSM/archive), application-level backups (database dumps, WAL archiving) |
| **Object storage data** | Datasets, checkpoints, model artefacts | Bucket versioning + object lock, cross-region replication, lifecycle rules (4.24), checksum manifests |
| **Registries and artefacts** | Images, charts, models | Replicated registries, immutable tags, mirrors; keep golden base images offline |
| **Identity and secrets** | CA keys, KMS keys, Vault, OIDC provider config | Escrowed offline backups; HSM/KMS multi-region keys |
| **Observability data** | Metrics/logs | Often best-effort; keep dashboards/rules in Git |

**Velero** (CNCF project): server-side controller + CLI; backs up Kubernetes resources to object storage and volumes via CSI snapshots or file-system backup (Kopia); supports schedules, TTLs, hooks (pre/post backup commands for DB quiescing), restore to the same or a different cluster, namespace mapping, and resource filters.

```bash
velero install --provider aws --plugins velero/velero-plugin-for-aws:v1.10.0 --bucket dr-velero --backup-location-config region=us-east-1 \
  --snapshot-location-config region=us-east-1 --use-node-agent --features=EnableCSI
velero backup create ml-platform --include-namespaces mlflow,vector-db --snapshot-volumes --ttl 720h
velero schedule create nightly --schedule="0 2 * * *" --include-namespaces '*' --exclude-namespaces kube-system,kube-public --ttl 168h
velero backup describe ml-platform --details; velero restore create --from-backup ml-platform --namespace-mappings mlflow:mlflow-restore
```

Considerations for AI data: multi-terabyte checkpoints are better protected by storage-layer replication and tiering than by Velero file-system backup; datasets are re-creatable from source (store recipes and hashes); prioritise irreplaceable artefacts (trained models, fine-tuning data, evaluation sets, experiment metadata, feature stores). Define retention per class (e.g., keep last N checkpoints plus milestones).

## 7. Disaster recovery strategies

**Define objectives per tier**: RPO (maximum tolerable data loss) and RTO (maximum tolerable downtime). Example: inference gateway RTO 15 min/RPO 0 (stateless, redeploy from Git); metadata DB RTO 1 h/RPO 5 min (replicated Postgres); training in progress RTO hours/RPO last checkpoint (checkpoint cadence = RPO in GPU-time); datasets RTO days/RPO 0 (replicated objects).

| Strategy | Description | RTO | Cost | Notes |
|---|---|---|---|---|
| **Backup and restore** | Restore etcd/Velero into rebuilt cluster | Hours | Low | Rebuild infrastructure from Terraform/Ansible (4.17, 4.24) |
| **Rebuild from Git** | Recreate cluster via IaC + GitOps; restore data stores only | Hours | Low | Cleanest for stateless platforms; requires immutable infrastructure discipline |
| **Pilot light / warm standby** | Small standby cluster in another region/zone with replicated data and GitOps in sync | Minutes to an hour | Medium | GPU capacity at the standby is the expensive part; keep minimal inference footprint, scale up on failover |
| **Active-active multi-cluster** | Multiple clusters serving traffic (global LB/DNS, MultiKueue for batch) | Seconds to minutes | High | Needs data replication and conflict handling (5.35) |

AI-specific DR notes:

- **Training jobs** recover from **checkpoints** (frequency vs cost; async multi-tier checkpointing, redundant shards, validation of checkpoint integrity) not from cluster snapshots; make checkpoint storage durable and in another failure domain; test restart from the latest checkpoint on a different cluster/region (bandwidth!).
- **Inference** is mostly stateless: weights from a registry/object store; DR = stand up replicas elsewhere and shift traffic; pre-stage model artefacts in the standby region.
- **GPU capacity is the DR bottleneck**: a standby region with no GPUs cannot take over; negotiate reservations/priority access or accept degraded service (smaller models, queueing).
- **Control-plane SPOFs**: management cluster, GitOps hub, CI, registry, DNS, identity provider (OIDC), secret manager, KMS: each needs its own DR plan.
- **Split-brain avoidance**: a restored/standby cluster must not manage the same external resources as the live one.
- **Runbook the order**: networking/DNS → identity/secrets → storage → control plane → platform add-ons → workloads → traffic cutover.

## 8. Failure scenarios and responses

| Scenario | Impact | Response |
|---|---|---|
| One control-plane node dies | HA continues; etcd 2/3 | Replace member (remove then add), rejoin control plane |
| Two of three etcd members die | API read-only/unavailable; workloads keep running | Restore quorum: bring back a member or restore from snapshot; avoid adding members before removing dead ones |
| etcd DB full (NOSPACE) | Writes fail | Compact, defrag, disarm alarm; find churn source (5.5) |
| All control-plane nodes lost | No API; workloads run until nodes churn | Rebuild from snapshot + PKI backup, rejoin nodes |
| Certificates expired | API/kubelets reject TLS; nodes NotReady | Renew certs, restart components; set up expiry alerts and annual renewal/upgrade cadence |
| Failed minor upgrade (control plane) | Component crashloop, API errors | Check static pod logs; fix config; if irrecoverable restore pre-upgrade snapshot and old manifests |
| Bad CNI/CSI/operator upgrade | Network/storage broken for new pods | Roll back via GitOps; node-by-node revert; keep old DaemonSet versions available |
| Accidental `kubectl delete ns` | Namespace content destroyed (PVs may survive with `Retain`) | Re-sync from Git, Velero restore, PV `Retain` rebinding; RBAC to prevent |
| Corrupted/poisoned admission webhook blocks everything | Writes rejected | Delete/patch the webhook configuration (emergency), fix failurePolicy, scope exclusions |
| Region/zone outage | Cluster or capacity gone | Failover per DR tier: traffic shift, standby cluster, restore data in other region |
| Ransomware / credential compromise | Data and cluster at risk | Immutable backups, break-glass rebuild, rotate CA and secrets, forensic isolation (Part 18) |

## 9. Lab (untested)

1. **Upgrade rehearsal**: build a 1.N cluster with kubeadm (3 CP, 2 workers); run workloads including a StatefulSet, a PDB-protected Deployment, a GPU-like fake extended resource DaemonSet; take an etcd snapshot; upgrade to 1.N+1 following section 3; record timings and issues; run `kubectl get nodes` and smoke tests at each stage.
2. **Deprecated API scan**: before upgrading, apply a manifest using an API removed in the target version; detect it with `pluto`/`kubent` and the API server metric; migrate with `kubectl-convert`.
3. **Skew experiment**: run a worker one minor behind the control plane (supported); try one newer than the API server (observe failure); try kubectl two minors apart.
4. **PDB trap**: create a PDB with zero allowed disruptions and attempt drain during upgrade; fix; document the checklist.
5. **etcd backup automation**: create the snapshot CronJob/systemd timer with checksum and offsite copy; alert on staleness; verify `snapshot status`.
6. **Member replacement**: kill an etcd member (stop and delete data); replace using remove-then-add; compare with adding first (lab-only) to see risk.
7. **Full restore drill**: with a 3-CP cluster, snapshot, create and delete objects, wipe etcd on all nodes, restore on all members, bring up the API server; compare restored vs expected state; list side effects (replica counts, missing objects, stale leases).
8. **Certificate expiry**: set certificates to expire soon (or manually move the clock in a throwaway VM), observe failure modes, renew with `kubeadm certs renew all`, restart components, fix kubeconfigs.
9. **Velero**: back up a namespace with a PVC (CSI snapshots or Kopia), delete it, restore into the same and a different cluster; test hooks for database quiescing; verify data integrity with checksums.
10. **GitOps rebuild**: destroy a workload cluster (lab) and rebuild from Terraform/CAPI + GitOps bootstrap (4.25, 4.26); measure time to healthy platform; list manual steps and automate them.
11. **GPU stack upgrade**: upgrade the GPU Operator/driver on a canary pool using the operator's upgrade policy with a checkpointing job running; validate; roll to the rest.
12. **DR game day**: simulate loss of a zone or region (block network between clusters); execute the DR runbook for inference and training (restart from checkpoint in another cluster); record RTO/RPO achieved and gaps.
13. **Webhook outage**: break an admission webhook to block all pod creation; practise emergency recovery.
14. **Clean up**.

Mark tested only after execution.

## 10. Common mistakes

- Skipping minor versions or upgrading nodes before the control plane; ignoring skew policy.
- No pre-upgrade etcd snapshot, or backups that were never restored; backups stored on the same nodes/disks.
- Not scanning for deprecated APIs; upgrading operators after the cluster rather than before when they're incompatible.
- Hand-edited static pod manifests lost during upgrade; kubeadm config not tracked.
- Draining GPU nodes without checkpoint coordination; PDBs that deadlock drains.
- Upgrading kernel/driver/Kubernetes simultaneously with no ability to bisect failures.
- Adding an etcd member before removing the dead one; running two-member etcd clusters.
- Forgetting the CA private key and encryption/KMS keys in DR plans; Secrets in unencrypted snapshots.
- Restoring a cluster that then competes with the live one for cloud resources.
- Treating snapshots as backups; ignoring object storage versioning/immutability.
- DR plans that assume GPUs will be available in the standby region.
- No game days; runbooks untested.

## 11. Interview angles

- "Walk through upgrading a production Kubernetes cluster. What order? What do you check first? How do you roll back?" 
- "What is the version skew policy?" 
- "How do you find deprecated API usage before an upgrade?" 
- "How do you back up and restore etcd? What happens to the cluster when you restore?" 
- "A control-plane node died permanently. How do you replace its etcd member?" 
- "How would you design DR for a GPU training platform? What are RPO and RTO for training vs inference?" 
- "How do you upgrade GPU drivers across hundreds of nodes without killing training jobs?" 
- "What's in a complete Kubernetes backup strategy?" 

## 12. Checkpoint questions (35)

1. Minor release cadence? **A:** ~3 per year.
2. Supported minors? **A:** Latest three.
3. Upgrade order? **A:** Control plane then nodes.
4. Can you skip minors? **A:** No (one at a time for control plane).
5. kubelet skew? **A:** Up to 3 minors older than API server (recent).
6. kubectl skew? **A:** ±1 minor.
7. kubeadm command for first CP? **A:** `kubeadm upgrade apply`.
8. For other nodes? **A:** `kubeadm upgrade node`.
9. What does `upgrade plan` show? **A:** Available versions and requirements.
10. Does kubeadm upgrade CNI? **A:** No.
11. Does kubeadm upgrade CoreDNS/kube-proxy? **A:** Yes.
12. Can control plane be downgraded? **A:** Not supported; restore backup.
13. Tool for deprecated APIs? **A:** pluto/kubent.
14. API server deprecated usage metric? **A:** `apiserver_requested_deprecated_apis`.
15. Why PDB check? **A:** Zero-disruption PDBs block drains.
16. Etcd snapshot command? **A:** `etcdctl snapshot save`.
17. Snapshot validation? **A:** `etcdutl snapshot status`.
18. Restore tool? **A:** `etcdutl snapshot restore`.
19. Must all members restore from same snapshot? **A:** Yes.
20. State after restore? **A:** Rewound to snapshot time.
21. Replace dead member order? **A:** Remove, then add.
22. What else to back up with etcd? **A:** PKI/CA keys, kubeadm config, encryption/KMS keys.
23. Cert default lifetime? **A:** 1 year for leaf certs.
24. Renew command? **A:** `kubeadm certs renew all`.
25. Velero stores to? **A:** Object storage.
26. Velero volume options? **A:** CSI snapshots or Kopia file-system backup.
27. Are snapshots backups? **A:** No (same failure domain).
28. RPO definition? **A:** Max tolerable data loss.
29. RTO definition? **A:** Max tolerable downtime.
30. Training DR basis? **A:** Checkpoints.
31. Inference DR basis? **A:** Redeploy stateless replicas, weights from replicated storage.
32. Warm standby cost driver for AI? **A:** GPU capacity.
33. Operator-managed driver upgrade control? **A:** `upgradePolicy` in ClusterPolicy.
34. Restore drill precaution? **A:** Isolate from real external resources.
35. DR game day purpose? **A:** Validate runbooks and measure RTO/RPO.

## 13. Sources and review notes

**Written in original words.** Principal sources:

- Josh Rosso, Rich Lander, Alex Brand and John Harris, *Production Kubernetes* (chapters on deployment models, cluster lifecycle and platform considerations).
- Brendan Burns et al., *Kubernetes: Up and Running* (3rd edition; cluster deployment and operations).
- The author's `nvidia-devops` repository, volume 03 (etcd backup/restore and operations, control plane masterclass) and volume 10 (change management).
- Kubernetes documentation (version skew policy, kubeadm upgrade, etcd disaster recovery), etcd operations guide, Velero and NVIDIA GPU Operator upgrade documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** exact skew numbers per release, kubeadm flags and config API versions for your versions, package repository naming, `etcdutl`/`etcdctl` command split, GPU Operator `upgradePolicy` fields, Velero plugin/flag versions, and every command listing; all labs are **untested**.
