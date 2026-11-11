# NVKE deep research notes (fetched 2026-11-11)

Tags: official (NVIDIA blog and docs, which the repo builds), source-code (read in clones under /private/tmp/claude-501/v20/nvstack), ran (executed in /private/tmp/claude-501/v11/w32), vendor, third-party, inference.

## Pinned versions
- nvke commit 487f511 (2026-11-10 23:54 UTC), latest release v0.23.1 (2026-11-03), tags up to v0.24.0-rc.x. Apache-2.0. 1141 stars, 205 open issues (gh api).
- nvkr commit 616c308 (2026-11-11), v0.1.0 (2026-10-22), Go 1.27.4 pinned. cluster-api-provider-nico commit 41351eb (2026-11-10), CAPNICo 0.0.x series, contract v1beta2, built on cluster-api v1.13.4, support level Experimental (README); NVKE pins CAPNICo v0.1.0 and Cluster API v1.13.6 (supported-platforms.md).
- NICo: dsx-ai-factory/infra-controller, Rust, Apache-2.0, release v2.3.4 (2026-11-10). README: discovers BMCs with Redfish; boots any iPXE-installable OS. No Redfish code exists in the nvke, nvkr or CAPNICo clones (grep).
- CNCF: cncf/k8s-conformance PR 4492 "Conformance results for v1.36/nvke" merged 2026-10-22; cncf/landscape PR 5236 "Add NVIDIA Kubernetes Engine to Certified Kubernetes - AI Platform" merged 2026-10-29 (gh api).

## Sources fetched
- NVIDIA blog 2026-11-10 (Taber, Chapman, Boyd): components, release sets, partners, walkthrough prerequisites (six CPU servers: three management, three workload control plane; a bootstrap host; GPU servers; existing NICo; Linux build host with Docker and KVM), certified Kubernetes AI Platform and Certified Kubernetes Installer claim, conformance on 1.36.
- Partners per blog: Firmus and SK Telecom integrate NVKE and NVKR in their AI factories; Mirantis, Rafay, Spectro Cloud, OpenNebula Systems, vCluster incorporate components of NVKE and NVKR in managed Kubernetes offerings; Netris enables NVKE in its network automation. All vendor statements of intent; not verified by product docs here.
- Search 2026-11-11: no heise or Cloud Native Now NVKE article found (aiweekly, borncity, explainx, zeli exist; third-party). Mirantis/Netris/vCluster press items exist but do not mention NVKE in the snippets.
- docs.nvidia.com/nvke: the site is built from docs/ in the nvke repo (fern/docs.yml, docs/index.yml), so repo files at 487f511 are the docs source.

## Ran locally (macOS arm64, no GPU)
Real controller binary built with go 1.27.3, run with Postgres 18.6 and Temporal dev server in docker, kind cluster with only the Cluster API and CAPNICo CRDs. See chapter 11.32 lab. Not run: bare-metal provisioning, NICo, SPIRE, nvke-agent, bootstrap, API authentication enforcing, GPUs, nvkectl get providers (downloads kubectl).

## Findings that differ between sources
- docs/architecture.md draws "Forge" as the bare-metal lifecycle system; every other page says NICo. Inference: Forge is the earlier name of the NICo API (stack config apiName "forge").
- sitespec infra.provider nico is refused by nvkectl 487f511 unless NVKECTL_ENABLE_NICO=1 (ran), while docs/site-bootstrap pages describe it without the flag.
- OpenAPI allows cniPlugin calico; docs say ovn-kubernetes only; controller config allowLegacyCalicoClusterCreation defaults false.
- API accepts a node pool kubernetesVersion newer than the control plane (ran: pool 1.37.2 on a 1.36.3 cluster, 200).
- docs/lifecycle.md example patch uses 1.34.0 while supported version is 1.36.3 (stale example).
- site-bootstrap docs mention ArgoCD deploy repository; operate docs use deploy/nvke-deploy.sh.
- ADR 20261105 (status proposed) says the PostgreSQL-backed REST API will be replaced by a new NVKE API over a CRD service layer; legacy API retired.
