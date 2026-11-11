# NVIDIA open-source AI factory Kubernetes stack: raw research notes

Fetched 2026-11-11. Tags: official (NVIDIA blog/docs), source-code (repo files read from shallow clones in /private/tmp/claude-501/v20/nvstack), vendor, third-party, inference (my reasoning).
Stars are a signal only (gh api, 2026-11-11).

## Projects, repos, licence, maturity (gh api + clones, 2026-11-11)

| Project | Repo | Licence | Latest release (date) | Stars | Tag |
|---|---|---|---|---|---|
| NVIDIA Run:ai (full platform) | github.com/dsx-ai-factory/run-ai | Apache-2.0 (LICENSE + README, source-code) | 3.0.22 (2026-11-02); supported branch release-3.0 (SUPPORT.md) | 742 | source-code |
| KAI Scheduler | github.com/kai-scheduler/KAI-scheduler (NVIDIA/KAI-Scheduler redirects) | Apache-2.0 | v0.20.1 line; backports v0.16.17, v0.14.13 on 2026-11-10; CHANGELOG v0.18.0 2026-09-23 | 1638 | source-code |
| KAI GPU fractioning | github.com/kai-scheduler/gpu-fractioning | Apache-2.0 | v0.1.8 (2026-10-19) | 59 | source-code |
| Workload Map (karta) | github.com/dsx-ai-factory/workload-map | Apache-2.0 | v0.3.0 (2026-10-21) | 97 | source-code |
| Grove | github.com/ai-dynamo/grove (NVIDIA/grove redirects) | Apache-2.0 | v0.2.0-beta1 (2026-10-30); v0.1.0-alpha.17 (2026-10-26) | 292 | source-code |
| NVIDIA Dynamo | github.com/ai-dynamo/dynamo | Apache-2.0 text in LICENSE (GitHub reports NOASSERTION because of a NOTICE) | v1.6.2 (2026-11-05) | 8467 | source-code |
| AICR | github.com/NVIDIA/aicr | Apache-2.0 | v1.2.0 (2026-11-02) | 472 | source-code |
| NVCRE | github.com/NVIDIA/cluster-readiness-engine | Apache-2.0 | v0.11.0 (2026-11-09) | 84 | source-code |
| NVSentinel | github.com/NVIDIA/NVSentinel | Apache-2.0 | v1.31.0 (2026-11-07) | 434 | source-code |

## Official announcements

- Run:ai open source. https://developer.nvidia.com/blog/nvidia-runai-is-now-open-source-as-part-of-nvidia-dsx-ai-factory-platform/ (official, dated 2026-10-13, Ekin Karabulut and Sam Heywood). "NVIDIA is making the full NVIDIA Run:ai platform available as open source software." Repos named: dsx-ai-factory/run-ai, kai-scheduler/KAI-scheduler, kai-scheduler/kai-gpu-fractioning, kai-scheduler/kai-resource-management, dsx-ai-factory/karta (Workload Map), runai-model-streamer, ai-dynamo/grove. KAI Apache-2.0 and CNCF Sandbox. Platform licence text in the blog: "governed by its applicable open source licenses" (no name); the run-ai repo LICENSE is Apache-2.0 (source-code, resolves the vagueness). NGC Community Product with Helm chart requires accepting NVIDIA Software License Agreement and Product-Specific Terms (official). "No paid NVIDIA Run:ai subscription or NVIDIA support entitlement is required for the Community Product." "NVIDIA enterprise support is not included." Proprietary GPU fractioning retired in favour of CUDA 13.4 native fractioning (blog; I did not verify CUDA 13.4 elsewhere). Commercial: standalone product, Mission Control, NVIDIA AI Enterprise, cloud marketplaces.
- Secondary: AIwire (hpcwire) 2026-10-13, MarkTechPost 2026-10-18, Saturn Cloud 2026-10-12 (third-party; AIwire fetch returned 403). Search snippets agree with NVIDIA blog.
- DSX OS announcement. https://developer.nvidia.com/blog/nvidia-dsx-os-delivers-open-modular-software-for-operating-ai-factories-at-scale/ (official, 2026-05-31, Warren Barkley). DSX = platform for AI factories announced at GTC Taipei. DSX OS = open modular operating layer: DSX Exchange, MaxLPS, Flex, NICo (Infra Controller), DOCA Platform Framework, AICR, NVSentinel, Fleet Intelligence, NVCF, MCP servers. The blog states no per-component licence. Partners named: CoreWeave, Crusoe, Firmus, IREN, Lambda, Nebius, Nscale, Yotta etc.
- DSX OS Kubernetes workflow. https://developer.nvidia.com/blog/configure-certify-and-operate-kubernetes-gpu-clusters-with-nvidia-dsx-os/ (official, 2026-11-05, Sowmyan Soman and Kai Wombacher). AICR configure, NVCRE certify, NVSentinel operate, all Apache-2.0. Flow: aicr recipe, aicr bundle, aicr validate, aicr diff --fail-on-drift; nvcrectl certification run; NVSentinel automatic actions off by default; NVCRE has no thresholds by default; NVCRE attributes only, NVSentinel owns quarantine; double-cordon warning. Blog cites recipe apiVersion aicr.run/v1alpha2; the repo at 2026-11-11 uses aicr.run/v1beta1 (overlays) and v1beta2 (RecipeResult): version drift, trust the repo (source-code).

## Source-code findings

### Run:ai (dsx-ai-factory/run-ai)
- README: "NVIDIA Run:ai is an open-source AI workload and GPU orchestration platform". Monorepo: control-plane/ (about 30 services incl. frontend, identity-manager, workloads-manager, policy-service, metrics-service), runai-cluster/ (controllers, admission webhooks, ships KAI scheduler), runai-installer/ (guided installer CLI), runai-mcp-server/, clients, docs/. Two parts: control plane and cluster. Control plane connects one or more clusters. UI, CLI, REST API.
- Install: guided (runai-installer with config YAML, preflight) or manual Helm. Images nvcr.io/nvidia/runai-oss, charts https://helm.ngc.nvidia.com/nvidia/runai-oss.
- Licence: Apache-2.0 root; nested MIT/Apache vendor files; trademarks not licensed (TRADEMARKS.md).
- docs/README.md: "NVIDIA Run:ai is available as open source. The NVIDIA Run:ai Support-Entitled Release is available for organizations that require NVIDIA enterprise support and an SLA."
- docs/getting-started/product-support-policy.md: support tiers for the Support-entitled self-hosted offering: 9 months full + 3 months extended = 12 months; policy as of 2026-10-13; SaaS control plane under NVIDIA Cloud Agreement; self-hosted under Software License Agreement + Product Specific Terms. Components control plane, cluster, CLI released together; control plane version >= cluster version; CLI = cluster version.
- SUPPORT.md (repo): only release-3.0 supported. Help via GitHub Discussions/Issues, PSIRT for security.
- README "Known limitations": root Makefile targets are placeholders; no long-range roadmap published.
- Unclear: the exact feature delta between Community Product and Support-Entitled Release (no feature table found); whether SaaS control plane is open source (it is described separately as a cloud service). I did not run the installer.

### KAI Scheduler
- README: CNCF sandbox project; built on kube-batch; features: batch (gang), bin-pack/spread, hierarchical queues, DRF fairness, time-based fairshare, min-guaranteed runtime, consolidation, elastic workloads, background pods, DRA, topology-aware scheduling, hierarchical PodGroups, GPU sharing, explainability via Events. Integrated with Grove (2025/11 news item) and KubeRay.
- Chart crds: kai.scheduler_configs, schedulingshards, topologies; scheduling.run.ai_bindrequests, podgroups, queues. Chart.yaml deps include gpu-fractioning (OCI subchart per CHANGELOG v0.18.0).
- Dynamo platform chart pins kai-scheduler v0.17.0 and Grove v0.2.0-beta1 (source-code, deploy/helm/charts/platform/Chart.yaml).

### Grove
- README: "One API. Any inference architecture." Four concepts: PodClique, PodCliqueScalingGroup, PodCliqueSet, PodGang (scheduler API). Needs: multi-node scaling units, hierarchical gang scheduling, startup ordering, topology-aware placement. Min Kubernetes 1.34 tested (K3s 1.34, 1.35 in CI). Roadmap 2026: resource-optimised rolling updates, topology spread, automatic topology detection.
- v0.2.0-beta1 release notes: APIs to beta (grove.io/v1beta1 served and stored), v1alpha1 deprecated but served; packDomain removed, use topologyConstraint.pack.required; PodGang stays scheduler.grove.io/v1alpha1; upgrade with crdInstaller.upgradeCRDs=true; downgrade path exists.
- Install: helm upgrade -i grove oci://ghcr.io/ai-dynamo/grove/grove-charts --version <version>. Chart version 0.2.0-beta1 (appVersion string "v0.1.0-dev": cosmetic oddity).
- CRDs: PodCliqueSet, PodClique, PodCliqueScalingGroup, ClusterTopologyBinding, PodGangMap (grove.io), PodGang (scheduler.grove.io).
- Dynamo docs: Grove-backed multinode deployments model worker groups as PodCliqueSet/PodClique; prefill/decode elasticity via PodCliqueScalingGroup (dynamo docs/fern/pages/developer-guide/knowledge-base/overview.md). Dynamo enterprise install doc: KAI, Grove bundled as subcharts, disabled by default.
- Run:ai blog lists Grove under related projects, github.com/ai-dynamo/grove.

### AICR
- README: recipes = version-locked configs; CLI commands snapshot, recipe, bundle, validate, verify, diff, query; deployers helm, argocd, argocd-helm, flux, helmfile, terraform, fleet; validation phases deployment, performance, conformance; supply-chain (SLSA L3, cosign); "Not a Kubernetes distribution / provisioner / managed control plane". Components include GPU Operator, DRA GPU driver, Network Operator, NFD, NVSentinel, KAI Scheduler, Kueue, Dynamo, Grove, NIM Operator. Platforms include Dynamo, Kubeflow, Kueue, NIM, Run:ai, Slurm (Slinky). Services EKS, GKE, AKS, OKE, etc. Accelerators incl. H100, H200, B200, GB200, GB300; VR200 preview.
- Overlay example recipes/overlays/h100-eks-ubuntu-inference-dynamo.yaml: kind RecipeMetadata, apiVersion aicr.run/v1beta1, spec.base, criteria, constraints (K8s.server.version >= 1.34), componentRefs with dependencyRefs (grove -> prometheus-operator-crds; dynamo-platform -> grove, cert-manager, prometheus-operator-crds, gpu-operator, kai-scheduler), validation phases. 166 overlay files.
- cli-reference: aicr diff --baseline --target --fail-on-drift (exit non-zero), cm:// ConfigMap URIs.
- No JSON schema for hand-written recipes found as a CRD; REST openapi schemas exist under api/aicr/v1/schemas. I could not run aicr here.
- Release v1.2.0 (2026-11-02); CLI deprecation policy in docs/user/deprecations.md.

### NVCRE
- README: controller that certifies GPU clusters; CRDs nvcre.nvidia.com/v1alpha1: Certification, Workflow, WorkloadRun, Job, LogProfile, GoodputMeasurement, BandwidthMeasurement. nvcrectl / kubectl nvcre. Requires GPU Operator, Prometheus Operator CRDs, standalone DCGM for dcgm-level4; GB200/GB300 need DRA driver ComputeDomain. Catalog: NCCL, nemotron5-8b training. Pre-1.0 (v0.11.0).
- Certification spec.thresholds: map of metric name to CEL expression over `value` (description in CRD, example "value >= 900"). docs/designs/000-adr.md: NVCRE does not dictate pass/fail criteria; docs 104: "pass/fail thresholds exist only if the user sets them".
- examples/certification.yaml in repo (read).

### NVSentinel
- README: detect, protect (cordon and drain), remediate (GPU reset or reboot). Beta/Stable since v1.0.0, "recommended for production testing and use" (ROADMAP.md). Needs Kubernetes 1.34+, Helm 3, GPU Operator with dcgm.enabled=true, cert-manager v1.21+, persistent storage for a datastore (MongoDB by default; PostgreSQL provider doc exists). Default install is monitoring only. Flags: global.faultQuarantine.enabled, nodeDrainer, faultRemediation, janitor, janitorProvider, preflight.
- Fault quarantine: CEL rulesets over HealthEvent and Node (metadata, spec only); circuit breaker defaults percentage 50, duration 5m; a tripped breaker pauses all event processing including uncordon; dryRun option. Node drainer: Eviction API respects PDBs; modes such as AllowCompletion; partial drain.
- NVCRE Certification Monitor (docs/nvcre-certification-monitor.md): reads Certification CRs, turns failed nodes into health events, NVCRECertFailed condition, taint nvsentinel.dgxc.nvidia.com/nvcre-cert-failed=true:NoSchedule (no cordon). Sweep every 15 minutes.
- CRDs in chart: ValidationRequest (nvsentinel.nvidia.com), RebootNode/GPUReset/TerminateNode (janitor.dgxc.nvidia.com), PreflightConfig, DrainRequest. Fault-quarantine rulesets are Helm values, not a CRD.

## Differences open-source Run:ai vs commercial

- Same source base (inference): the repo is the product's monorepo; the Support-Entitled Release is a support and SLA wrapper (official docs/README.md). Community Product has no enterprise support, support policy page defines 12-month lifecycle for entitled release only.
- Fractioning moved to CUDA-native (blog, unverified elsewhere).
- Unclear: any feature gating, SaaS control plane source, release cadence of entitled vs community builds, upgrade path between them.

## Maturity read (inference)
Production-grade engines: KAI (CNCF sandbox, 0.x). Run:ai 3.0.x is the long-running product now open. Grove beta (v0.2.0-beta1, API just promoted 2026-10-30). NVSentinel v1.x Beta/Stable. AICR 1.2 but API versions in flux (blog v1alpha2 vs repo v1beta1/v1beta2). NVCRE 0.11 v1alpha1 CRDs, early.

## NVKE, NVKR, CAPNICo (added 2026-11-11)

- Official: NVIDIA developer blog "Manage Kubernetes Clusters for GPU Infrastructure with NVIDIA Kubernetes Engine", 2026-11-10 (Nathan Taber, Eric Chapman, Erin Boyd); docs https://docs.nvidia.com/nvke/documentation/overview/what-is-nvke ; NVIDIA blog on OpenShell, 2026-11-10 (Snapshot, Agent Substrate also named); Cloud Native Now, 2026-11-10 (third-party). heise not fetched.
- Repos (gh api 2026-11-11): dsx-ai-factory/nvke Apache-2.0, 1138 stars, v0.23.1 (2026-11-03), v0.24.0-rc.7 tag, commit 487f511 (2026-11-10); dsx-ai-factory/nvkr Apache-2.0, 25 stars, v0.1.0 (2026-10-22); dsx-ai-factory/cluster-api-provider-nico Apache-2.0, 24 stars, CAPNICo v0.1.0 pinned by NVKE.
- Architecture (source-code): management cluster of 3 nodes formed by nvkectl via a seed cluster; controller = REST API + PostgreSQL + Temporal worker + reconcilers; workflow outbox; Cluster API v1.13.6 pinned; NICo via CAPNICo; nvke-agent over gRPC; SPIFFE/SPIRE TPM node attestation; OVN-Kubernetes 2.4.2; Kubernetes 1.36.3 pinned; Ubuntu 24.04/26.04; IPv4 only; internal CRDs (internal.nvke.nvidia.com), public interface is REST (openapi.yaml 0.1.0-alpha).
- Preview limits (README + docs/overview/preview-status.md): API plain HTTP port 30080, auth off by default (off/permissive/enforcing), no authorization, no management-plane upgrade or backup/restore, management cluster does not self-manage, admin kubeconfig irrevocable, node pool changes do not recycle nodes, labels/taints immutable, nvkectl upgrades control plane only, FDE images evaluation only, NKTP default backend anonymous Grafana admin. Third-party claim (no auth, no upgrade/backup) CONFIRMED.
- dsx-stack.md: NVKE scope ends at a conformant cluster; GPU stack via Nodewright + GPU Operator through AICR; CRE certifies; NVSentinel break-fix with NVKE lifecycle APIs; bring-up order NICo, NVKE, workload cluster, AICR, CRE, NVSentinel.
- Metrics (operate/observe.md): nvke_controller_cluster_info, node_pool_*_count, node_lifecycle_elapsed_seconds, node_provision_total, node_provisioning_giveups_total, nvke_auth_requests_total, nvke_auth_enabled.
- Roadmap (ROADMAP.md): coming soon per-customer authorization, self-managed management cluster, K8s 1.37.
- Unverified: CNCF conformance/certification claims, K8s 1.36 conformance test results, NICo version, KAI/Run:ai relation (not in NVKE docs).
- Code: code/part11/c31_nvke_cluster.yaml validated against controller/api/openapi.yaml CreateClusterRequest (schema is not additionalProperties:false; strict walk added in test).
