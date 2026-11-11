---
id: "c11-32"
title: "11.32 NVKE in depth, part 1: what NVIDIA Kubernetes Engine is, how it is built, its API and its cluster spec"
sidebar_label: "11.32 NVKE part 1: architecture, API, cluster spec"
sidebar_position: 32
description: "NVIDIA Kubernetes Engine (NVKE) in November 2026: the problem it solves, the management plane architecture, how a cluster request becomes work, the REST API catalog with real responses from a locally run controller, and the cluster and node pool specification field by field."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "Local controller with Postgres, Temporal and kind, no GPU"
---

# 11.32 NVKE in depth, part 1: what NVIDIA Kubernetes Engine is, how it is built, its API and its cluster spec

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Local Go controller, Postgres, Temporal and a kind cluster on macOS arm64 or Linux. No GPU, no NICo, no bare metal. |
| Part | Part 11: GPUs on Kubernetes, scheduling and virtualization |
| Sources used | NVKE repository at commit 487f511 (2026-11-10), NVIDIA developer blog of 2026-11-10, NVKE documentation (built from the repository `docs/` folder), NVKR and CAPNICo repositories, NVIDIA Infra Controller README. All fetched 2026-11-11. |
| Series | This is part 1 of 3. Part 2 is [11.33](33-nvke-in-depth-part-2-installation-nvkr-and-cluster-lifecycle.md). Part 3 is [11.34](34-nvke-in-depth-part-3-operations-security-failure-modes-and-comparison.md). |

Tag legend. Every claim carries one tag. **[official]** is NVIDIA's blog, documentation or release text. **[source-code]** is a file I read in a clone at the stated commit. **[ran]** is output I produced on this Mac. **[vendor]** is a partner's statement of intent. **[third-party]** is press or community. **[inference]** is my own reasoning.

## Why this matters for AI infrastructure

A neocloud has 2,000 GPU servers and a sales team that keeps promising customers their own Kubernetes cluster. The platform team builds that service with scripts around kubeadm, a spreadsheet of IP addresses and a runbook for replacing a dead node. It works for four customers. At forty customers the upgrade calendar alone fills the team's year.

On 10 November 2026 NVIDIA released NVKE, NVIDIA Kubernetes Engine, as a public preview under Apache 2.0 **[official]**. NVKE is the management system for exactly that job. You install it once in your AI factory. Your tenants then get workload clusters through an API, each with its own control plane, and NVKE carries out scaling, node replacement and certificate renewal.

This chapter is the first of three. It explains the problem NVKE solves, the architecture, the REST API and the cluster specification, and it shows a real controller answering real requests on a laptop. [11.33](33-nvke-in-depth-part-2-installation-nvkr-and-cluster-lifecycle.md) covers installation, the NVKR build system, NICo and the lifecycle runbooks. [11.34](34-nvke-in-depth-part-3-operations-security-failure-modes-and-comparison.md) covers security, failure modes, monitoring, comparisons and how to answer the interview question out loud. For where NVKE sits among NVIDIA's other open-source projects, read [11.31](31-nvidias-open-source-ai-factory-kubernetes-stack.md) first.

## Prerequisites and outcomes

### Prerequisites

- Kubernetes basics: control plane, etcd, kubeadm, node pools. See Part 5.
- Cluster API vocabulary: management cluster, infrastructure provider, Machine. The upstream Cluster API book is enough.
- 11.4 and 11.5 for the GPU Operator, which NVKE does not install. 11.31 for the neighbouring projects.

### Outcomes

After this chapter you can:

1. Explain who NVKE is for and what it deliberately leaves out.
2. Draw the management plane and name each component and where its state lives.
3. Follow a `POST /api/clusters` request from the HTTP handler to a running kubeadm cluster.
4. List the 21 API operations, the error model and the authentication status of the preview.
5. Write a valid cluster spec and node pool spec and lint them for the mistakes the controller rejects.

## 1. The problem: a Kubernetes service you do not have to invent

A customer opens a ticket on Monday. They want a Kubernetes cluster on eight H100 servers, an API endpoint of their own and no neighbour able to see their control plane. By Wednesday your engineers are arguing about who owns etcd backups. By Friday they have a cluster, and nobody remembers the exact steps.

That is the problem NVKE addresses. NVKE is an open-source Kubernetes management system that an AI factory operator installs to create and run Kubernetes clusters for its customers on its own NVIDIA GPU infrastructure **[official]**. The operator asks for each cluster through the NVKE API. NVKE then provisions the bare-metal nodes, forms the cluster and runs scaling, upgrades, node replacement and certificate renewal **[official]**.

The documentation names four audiences **[official]**. AI factory operators, including NVIDIA Cloud Partners, are the main audience. Kubernetes ISVs and platform providers can reuse parts such as CAPNICo or the telemetry pipeline. Customers receive a workload cluster. Evaluators and contributors can run it on one Linux machine without a GPU.

Three jobs sit outside NVKE **[official]**. NVKE does not manage bare metal, because NICo discovers machines, updates firmware and provisions hosts. NVKE does not ship OS images or Kubernetes binaries, because you build and host them. NVKE does not run the customer's workloads. This boundary matters for every later decision, so keep it in mind.

| Question | Answer | Tag |
|---|---|---|
| Who installs it? | The AI factory operator | official |
| Who calls its API? | The operator or the operator's own service. Customers do not, at preview. | official |
| What does the customer receive? | A workload cluster and one admin kubeconfig | official |
| What does it need underneath? | NICo for bare metal. LaunchLayer is also supported once enabled. | official |
| What licence? | Apache 2.0 for NVKE and NVKR | official |
| What maturity? | Public preview. NVIDIA does not recommend it for production. | official |

**Decision rule:** Consider NVKE when you are an operator who offers Kubernetes to several customers on NICo-managed GPU hardware, and treat it as a system you will pilot, not run in production, today.

**In one minute:** NVKE turns a Kubernetes service for GPU customers into an API plus controllers. It starts where NICo ends and stops at a conformant cluster. Preview status means you pilot it with eyes open.

## 2. What ships: the repository family and its versions

A new engineer asks which repository to clone. The honest answer is four, and they have different release rhythms. Knowing which one owns which job prevents hours of searching.

| Repository | Job | Licence | Version seen on 2026-11-11 | Tag |
|---|---|---|---|---|
| `dsx-ai-factory/nvke` | Controller, node agent, CLI `nvkectl`, node OS image build, telemetry chart, docs | Apache 2.0 | v0.23.1 released 2026-11-03, commit 487f511 on 2026-11-10 | source-code |
| `dsx-ai-factory/nvkr` | Build and release system for NVKE and AICR artifacts | Apache 2.0 | v0.1.0 released 2026-10-22 | source-code |
| `dsx-ai-factory/cluster-api-provider-nico` | Cluster API infrastructure provider for NICo, called CAPNICo | Apache 2.0 | NVKE pins v0.1.0. README lists the 0.0.x series as Experimental. | source-code |
| `dsx-ai-factory/infra-controller` | NICo, the bare-metal lifecycle system | Apache 2.0 | v2.3.4 released 2026-11-10 | third-party, from `gh api` |

The NVKE repository is a Go workspace of thirteen modules. Three run in production: the controller, the node agent and the Cluster API provider for hosts NVKE already provisioned **[source-code]**. The rest are the CLI, the generated API module, the authentication library, CRD types and test tooling.

Pinned versions come from the supported-platforms page **[official]**. Kubernetes 1.36.3 is the only supported version. Cluster API core, kubeadm bootstrap and control plane are v1.13.6. The CNI is OVN-Kubernetes 2.4.2. Nodes run Ubuntu 24.04 or 26.04 on amd64 or arm64. Helm must be v4.2.4, because Helm 3 cannot install the charts. The release qualification policy targets Kubernetes 1.36.

CNCF merged two related changes in October. The Kubernetes conformance results for v1.36 from NVKE merged on 22 October. The landscape entry that lists NVKE as a Certified Kubernetes AI Platform merged on 29 October **[third-party, from `gh api` on the two pull requests]**. The NVIDIA blog adds that NVKE is also a Certified Kubernetes Installer, which I did not check separately **[official]**.

**Decision rule:** Pin a commit or release tag for everything you evaluate, and record NVKE, NVKR, CAPNICo and NICo versions together, because the four move independently.

**In one minute:** Four repositories, four rhythms. NVKE owns the management plane. NVKR owns builds. CAPNICo connects Cluster API to NICo. NICo owns the hardware.

## 3. Architecture: one process, three engines

An on-call engineer sees a cluster stuck in `Provisioning`. Where do they look first? The answer depends on a fact that surprises many readers. One controller process holds a REST API, a Temporal worker and a set of Kubernetes reconcilers **[source-code]**. Reading only the workflows, or only the reconcilers, gives an incomplete picture of what reacts to a change.

```mermaid
flowchart TB
  client["Operator, automation or nvkectl"]
  subgraph mgmt["Management cluster, 3 nodes, formed by nvkectl"]
    api["NVKE controller: REST API on port 8080, NodePort 30080"]
    pg[("PostgreSQL: clusters, node pools, nodes, workflow_outbox")]
    outbox["Outbox processor"]
    temporal["Temporal: durable workflows"]
    recon["Reconcilers (controller-runtime)"]
    capi["Cluster API and CAPNICo"]
    spire["SPIRE server"]
  end
  nico["NICo REST API"]
  nodes["Workload cluster nodes with nvke-agent on port 15005"]
  client --> api
  api --> pg
  pg --> outbox
  outbox --> temporal
  temporal --> capi
  recon --> capi
  capi --> nico
  nico --> nodes
  api -. "gRPC, dialed by the controller" .-> nodes
  spire -. "TPM attestation" .-> nodes
```

The diagram shows the request path. The table below explains each box.

| Component | What it does | Where its state lives | Tag |
|---|---|---|---|
| REST API | Serves `/api/...`, health, readiness and the OpenAPI file. Handlers validate against the OpenAPI schema. | PostgreSQL | source-code |
| PostgreSQL | Rows for clusters, control plane configurations, node pools, node sets, nodes, credential audit events and the workflow outbox. Temporal shares the same server. | A 40 GiB volume claim on the management cluster | source-code, official |
| Outbox processor | Polls the `workflow_outbox` table every 5 seconds in batches of 10 and starts Temporal workflows | PostgreSQL | ran |
| Temporal worker | Runs cluster provisioning, teardown, reboot and certificate workflows. Retries steps without losing progress. | Temporal history in PostgreSQL | official |
| Reconcilers | Node pools, control plane and node scheduling, certificate renewal, tenant access, TPM and SPIFFE identity for Cluster API machines | Kubernetes objects | source-code |
| Cluster API v1.13.6 | Owns `Cluster`, `Machine` and bootstrap objects for each workload cluster | etcd of the management cluster | official |
| CAPNICo | Turns each requested Machine into a NICo instance through the NICo REST API | etcd of the management cluster | source-code |
| SPIRE server | Attests nodes by TPM before they receive a join credential | Management cluster | official |
| `nvke-agent` | gRPC server on every node. Runs kubeadm, installs the CNI, handles drain, reboot and teardown. The controller dials it. | The node | source-code |
| `nvkectl` | CLI. Bootstraps the management cluster, calls the REST API, reads some objects from the management cluster directly. | Local config file | source-code |

### 3.1 The outbox: why the API never calls Temporal

The handler for `POST /api/clusters` opens one database transaction. It writes the cluster record and a row in `workflow_outbox` in that transaction. Either both land or neither does **[source-code]**. A separate processor polls the table, starts the matching Temporal workflow and marks the row done.

The design means a committed cluster always has work queued, even if Temporal is down at that moment. It also means a stuck cluster has two places to check. Look for an unprocessed outbox row first. Then look at the workflow in the Temporal UI.

On my local run, 21 outbox rows existed after a short session and some had no `processed_at` value **[ran]**. I did not investigate why, and the local stack had no CAPI controllers or NICo, so I treat that as unexplained.

### 3.2 Where the control plane runs

Each workload cluster has its own control plane, etcd and node pools **[official]**. The control plane nodes are separate machines allocated from NICo through the `controlPlaneConfig` block of the spec. They join the workload cluster as control plane nodes. The blog's walkthrough lists six CPU servers: three for the management cluster and three for a workload control plane **[official]**.

The roadmap lists two related items as work in progress. One is running control planes on virtual machines instead of dedicated bare-metal nodes. The other is separating the control plane network from the worker network **[official, roadmap]**. Neither exists today.

### 3.3 Identity and trust

Nodes need an attested identity before they receive join credentials **[official]**. On bare metal each node attests with its TPM through SPIFFE and SPIRE. Node agent connections use one of five transport modes: `plaintext`, `spiffe`, `spiffe-jwt`, `external-mtls` or `external-mtls-jwt` **[source-code, docs/architecture.md]**. The mode is published on each Machine as an annotation.

### 3.4 What state exists and where

This question decides your backup plan, and the preview has no official procedure for it. State lives in four places **[inference, from the sources above]**. PostgreSQL holds the API's records and Temporal history. The management cluster's etcd holds Cluster API objects, release objects and secrets, including each workload cluster's admin kubeconfig. The etcd encryption key file produced at bootstrap is the only copy not on a node **[official]**. Each workload cluster's own etcd holds the customer's data. Chapter 11.34 turns this into a recovery plan.

### 3.5 The proposed next architecture

An architecture decision record dated 2026-11-05 has status proposed **[source-code]**. It splits NVKE into three layers: NVKE Core built on standard Cluster API contracts, a Service Layer of CRDs for operator catalogs, and an NVKE API above them. It says the current PostgreSQL-backed REST API will be replaced and retired. Treat the REST API in this chapter as the preview's API, not a stable contract. The OpenAPI file itself says version `0.1.0-alpha` **[source-code]**.

**Decision rule:** When a cluster is stuck, check in this order: the cluster's conditions through the API, the outbox row, the Temporal workflow, the Cluster API objects, then the node agent on the machine.

**In one minute:** One controller process combines an API backed by PostgreSQL, a Temporal worker and Kubernetes reconcilers. The outbox makes request and work atomic. Each workload cluster gets control plane machines from NICo. State is split across PostgreSQL and etcd, and the preview offers no backup procedure.

## 4. How a cluster request becomes a running cluster

A product manager asks how long cluster creation takes. The answer depends on which steps run where. Here is the sequence from the source and docs **[source-code, official]**.

1. A client calls `POST /api/clusters` with a spec. The API validates it against the OpenAPI schema, then against extra rules such as pod CIDR capacity and VIP overlap.
2. The handler stores the cluster and an outbox row in one transaction and returns `201` with the cluster.
3. The outbox processor starts the provisioning workflow in Temporal.
4. The workflow creates Cluster API objects in the management cluster namespace `nvke-system`. I saw a `Cluster` and a `NicoCluster` appear there within seconds **[ran]**.
5. CAPNICo requests instances from NICo. NICo boots each machine from the iPXE script in the release's machine image and hands it cloud-init data.
6. The node agent on the first control plane machine runs `kubeadm init` and the CNI installs. The cluster's status becomes `Provisioned`.
7. Other control plane nodes and workers join. A node needs its SPIRE attestation first.
8. The admin kubeconfig appears as the Secret `<cluster>-admin-kubeconfig` in `nvke-system` on the management cluster.

Steps 1 to 4 ran on my laptop. Steps 5 to 8 need NICo and bare metal, so they did not run **[ran]**. In the local run the provisioning condition read "Waiting for a control plane node to be ready to join" and stayed there, which is the honest state of a stack with no machines.

**Decision rule:** Judge provisioning speed by NICo capacity first. NVKE keeps waiting for a control plane machine that never becomes ready.

**In one minute:** Validation and storage take milliseconds. Everything after the outbox depends on NICo, the boot files and the node agent.

## 5. The REST API

An automation engineer wants to build a customer portal on top of NVKE. The first question is what the API offers and how it fails. The OpenAPI document is the contract **[source-code]**.

### 5.1 Conventions

- Everything lives under `/api`. Bodies are JSON.
- Create returns `201` with the stored object while provisioning continues. Delete returns `202` and sets the `deleting` condition. There is no operation resource. You poll the object and read its conditions.
- PATCH uses field-level merge, not RFC 7386. Omitted means unchanged. `null` is rejected. An empty array clears a list. The `nico` sub-object merges field by field.
- Lists return everything in one response. There is no pagination or ordering. Filters are exact match, and unknown query parameters are ignored.
- IDs are server-assigned UUIDs. Cluster names are unique per management plane. Node pool names are unique inside a cluster.
- Four paths need no token and sit outside `/api`: `/openapi.yaml`, `/api/docs/`, `/healthz` and `/readyz`.

### 5.2 Error model

Every error has one shape, `{"message": "..."}`. The status codes are 400 for validation, 401 and 403 for authentication and admission, 404 with no body, 409 for conflicts with a running operation, and 500 for unexpected errors **[source-code]**. I produced each of the 400 and 404 cases below on a local controller **[ran]**.

```text
$ curl -s -w ' [%{http_code}]' -X POST /api/clusters   (same name twice)
{"message":"A cluster already exists with the name \"demo-a\""} [400]

$ ... "controlPlaneKubernetesVersion": "v1.36.3"
{"message":"request body has an error: doesn't match schema #/components/schemas/CreateClusterRequest: Error at \"/controlPlaneKubernetesVersion\": string doesn't match the regular expression \"^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)$\""} [400]

$ ... etcdEncrypted omitted
{"message":"request body has an error: doesn't match schema #/components/schemas/CreateClusterRequest: Error at \"/etcdEncrypted\": property \"etcdEncrypted\" is missing"} [400]

$ GET /api/clusters/00000000-0000-4000-8000-0000000000ff
 [404]

$ GET /api/clusters/abc
{"message":"Invalid format for parameter clusterID: error unmarshaling 'abc' text as *uuid.UUID: invalid UUID length: 3"} [400]

$ PATCH /api/clusters/{id}  {"enableOidc": null}
{"message":"request body has an error: doesn't match schema #/components/schemas/UpdateClusterRequest: Error at \"/enableOidc\": Value is not nullable"} [400]

$ PATCH ... {"bogus": 1}
{"message":"request body has an error: doesn't match schema #/components/schemas/UpdateClusterRequest: property \"bogus\" is unsupported"} [400]
```

Business rules produce their own messages. These came from the same run **[ran]**:

```text
3 control plane nodes, no controlPlaneVIP:
  controlPlaneVIP is required to increase desired control-plane capacity above one; recreate the cluster with controlPlaneVIP configured
VIP 192.168.5.5 with default pod CIDR:
  controlPlaneVIP "192.168.5.5" overlaps network.podCIDR "192.168.0.0/16"
pod CIDR 192.168.0.0/23 with 3 nodes:
  network.podCIDR "192.168.0.0/23" provides 2 /24 node blocks, but 4 are required for 3 desired nodes plus 1 surge/headroom; choose a larger pod CIDR
label kubernetes.io/foo on a node pool:
  invalid node pool "gpu-workers": nodeLabels: key "kubernetes.io/foo" is under reserved domain "kubernetes.io"; labels in this domain cannot be set
controlPlaneConfig.maxSurge 2:
  maxSurge should be max 1 for cluster-level control plane config
taint effect Bogus:
  ... value is not one of the allowed values ["NoSchedule","PreferNoSchedule","NoExecute"]
upgrade on a cluster with no VIP:
  controlPlaneVIP is required to upgrade the control plane; recreate the cluster with controlPlaneVIP configured
```

### 5.3 Authentication status

The OpenAPI description says every operation requires a bearer token. The install says otherwise **[source-code, official]**. After a default install the API serves plain HTTP on NodePort 30080 with authentication off. A running controller reports this in its own metrics and log, which I saw **[ran]**.

```text
{"level":"INFO","msg":"API authorization is disabled"}
nvke_auth_enabled{mode="off"} 1
nvke_authz_enabled{mode="off"} 1
```

Authentication has three modes: off, permissive and enforcing. Permissive checks and counts every request but rejects nothing. Enforcing returns 401 without a valid token and 403 when no admission rule matches. NVKE does no authorization at all. Every admitted caller can call every endpoint **[official]**. Chapter 11.34 covers the mitigations.

### 5.4 Endpoint catalog

The OpenAPI document defines 21 operations on 12 paths and 76 schemas **[source-code, counted from the file]**.

| Method and path | Purpose | Success | Other statuses |
|---|---|---|---|
| `GET /clusters` | List clusters. `?name=` filters. | 200 | 401, 403 |
| `POST /clusters` | Create a cluster | 201 | 400, 401, 403 |
| `GET /clusters/{clusterID}` | One cluster with conditions | 200 | 404 |
| `PATCH /clusters/{clusterID}` | Upgrade control plane, enable etcd encryption or OIDC, toggle control plane recycling, change control plane config | 200 | 400, 404, 409 |
| `DELETE /clusters/{clusterID}` | Start deletion, allowed in any state | 202 | 404 |
| `GET /clusters/{clusterID}/control-plane` | Control plane configuration and rollout status | 200 | 404 |
| `GET /clusters/{clusterID}/control-plane/configHistory` | Control plane config changes, oldest first | 200 | 404 |
| `GET /clusters/{clusterID}/spire-server` | SPIRE server the nodes point at, with per-node reachability | 200 | 404 |
| `PATCH /clusters/{clusterID}/spire-server` | Point the nodes at another SPIRE server | 202 | 400, 404, 409 |
| `GET /nodePools` | List pools. Filters `clusterID`, `clusterName`, `name`. | 200 | |
| `POST /nodePools` | Create a worker pool | 201 | 400, 409 |
| `GET /nodePools/{nodePoolID}` | One pool | 200 | 404 |
| `PATCH /nodePools/{nodePoolID}` | Scale, recycle budget, auto-mode switches, Kubernetes version, release | 200 | 400, 404 |
| `DELETE /nodePools/{nodePoolID}` | Delete a pool and its nodes | 202 | 400, 404, 409 |
| `GET /nodeSets` | Versioned groups of nodes inside a pool. `?nodePoolID=` filters. | 200 | |
| `GET /nodeSets/{nodeSetID}` | One node set | 200 | 404 |
| `GET /nodes` | List nodes. Filters `clusterID`, `nodePoolID`, `clusterName`, `name`, `controlPlane`. | 200 | |
| `GET /nodes/{nodeID}` | One node with its conditions | 200 | 404 |
| `DELETE /nodes/{nodeID}` | Delete one node, optionally flag the machine for repair | 202 | 400, 404, 409 |
| `GET /releases` | Release names the management plane can use | 200 | |
| `GET /configProfiles` | Config profile names | 200 | |

Two things are missing. There is no endpoint for the management cluster itself. There is no kubeconfig endpoint. The OpenAPI text says cluster kubeconfigs come from `nvkectl`, which reads a Secret from the management cluster **[source-code]**.

Node sets are worth understanding. When I changed a pool's `kubernetesVersion`, the API created a new node set for the pool and left the old one with `desiredCount` 0 **[ran]**. The documentation calls the old ones deprecated node sets, and auto mode marks their nodes for recycling **[official]**.

### 5.5 A real exchange: create, list, get

This exchange used the local controller from the lab at the end of this chapter, with `c32_cluster_minimal.yaml` converted to JSON and the release name replaced by one installed locally. The response is trimmed to the fields that matter **[ran]**.

```text
$ curl -s -i -X POST localhost:8080/api/clusters -H 'Content-Type: application/json' --data @cluster.json
HTTP/1.1 201 Created
...
{"id":"8ef5e56a-9b0d-4265-b39c-dcda0547fe97","name":"demo-a",
 "controlPlaneKubernetesVersion":"1.36.3","cniPlugin":"ovn-kubernetes","cniVersion":"2.4.2",
 "etcdEncrypted":true,"enableCPNodeRecycling":false,
 "conditions":{"provisioning":{"status":"True","message":"Starting provisioning"},
               "provisioned":{"status":"False","message":"Not yet provisioned"}, ...},
 "controlPlaneConfig":{"desiredCount":1,"maxSurge":0,"systemReservedMemory":"16Gi",
   "nico":{"diskSelectionStrategy":"smallest","release":"test-fixture-amd64", ...}},
 "network":{"podCIDR":"192.168.0.0/16","serviceCIDR":"10.96.0.0/12"}}
```

Notice what the server filled in. `cniVersion` became `2.4.2`. The network defaults appeared. `diskSelectionStrategy` defaulted to `smallest`. A few seconds later the same cluster showed the message "Waiting for a control plane node to be ready to join". A node pool listing showed each pool with its taints and budget, and `GET /api/nodes?nodePoolID=...` showed pending nodes with fifteen conditions each, such as `pending: True` and `kubernetesReady: False` **[ran]**.

**Decision rule:** Build clients against the OpenAPI file at your pinned commit, treat every `400` message as human text rather than a code, and poll conditions instead of waiting for callbacks.

**In one minute:** Twenty-one operations, one error shape, asynchronous create and delete, and no pagination. The OpenAPI description says authentication is required, but a default install has it off and offers no authorization.

## 6. The cluster specification

A tenant asks for a cluster with three control plane nodes and one GPU pool. You need the exact fields, which of them are fixed forever, and what the API will reject. The cluster spec is the `CreateClusterRequest` schema, and `nvkectl` rejects any field the schema does not define **[official]**. I confirmed that with a spec carrying an unknown nested field, where `nvkectl` answered `unmarshal request: json: unknown field "bogus"` **[ran]**.

### 6.1 Top-level fields

| Field | Required | Default | Rule | Fixed at creation |
|---|---|---|---|---|
| `name` | yes | none | Lowercase DNS label, at most 55 characters, unique on the management plane | yes |
| `controlPlaneKubernetesVersion` | yes | none | `X.Y.Z`, no leading `v`. The API accepts any such string, but nodes run only versions their image carries. | no, upgrade through PATCH |
| `etcdEncrypted` | yes | none | Can be turned on later, never off | on-only |
| `cniPlugin` | no | `ovn-kubernetes` | Schema allows `calico` too, but docs support only ovn-kubernetes and the controller refuses legacy Calico unless configured | yes |
| `cniVersion` | no | `2.4.2` | The version the node image carries | yes |
| `controlPlaneVIP` | for more than one control plane node | none | IPv4, outside pod and service CIDRs. Without it you cannot scale above one, upgrade or replace control plane nodes. | yes, recreate to add |
| `network.podCIDR` | no | `192.168.0.0/16` | Private IPv4, `/12` to `/23`, comma-separated list allowed. Needs one `/24` per node plus headroom. | yes |
| `network.serviceCIDR` | no | `10.96.0.0/12` | Private IPv4, `/12` to `/24` | yes |
| `nico.orgID`, `siteID`, `vpcID` | yes for NICo | none | The organization ID is a string. The others are UUIDs. | yes |
| `controlPlaneConfig` | yes | none | See 6.2 | partly |
| `nodePools` | no | none | See 6.3. You can add pools later. | pool by pool |

Pod CIDR capacity is worth a worked example. The controller needs one `/24` block for every control plane and worker node in the request, plus `max(1, surge)` blocks of headroom **[source-code]**. A `/16` offers 256 blocks. A `/23` offers 2. Three nodes need 4, which is why my small-CIDR request failed in the run above.

### 6.2 Control plane configuration

| Field | Default | Rule |
|---|---|---|
| `desiredCount` | required | Use an odd number. Exactly two is excluded from automatic certificate renewal. More than one needs a VIP. |
| `maxSurge` | 0 | 0 or 1. Extra nodes allowed during a rollout. |
| `systemReservedMemory` | `16Gi` | If it is close to node memory, the node never reaches `Ready`. |
| `nodeLabels` | none | Fixed at creation. Control plane nodes accept no custom taints. |
| `nico.instanceTypePreference` | required | Ordered list of NICo instance type IDs. The first with capacity wins. |
| `nico.vpcPrefixIDs` or `subnetIDs` | one of the two | Exactly one |
| `nico.release` | required | Name of a ClusterRelease. The API does not check it at creation. A wrong name fails when the first node provisions. |
| `nico.sshKeyGroupIDs` | none | Optional |

### 6.3 Node pool fields

| Field | Default | Rule |
|---|---|---|
| `name` | required | Unique in the cluster, fixed once created |
| `nodeNamePrefix` | required | Node names are `<cluster>-<prefix>-<NNNN>` and must fit in 63 characters |
| `desiredNodeCount` | required | Not workload-driven autoscaling. NVKE changes it only when you do. |
| `nico.instanceTypeID` | required | Fixed at creation. To change machine type, add a pool. |
| `nico.release` | required | Name of a NodePoolRelease |
| `nico.vpcPrefixIDs` or `subnetIDs` | one of the two | Exactly one |
| `nico.infinibandPartitionID`, `nvLinkLogicalPartitionID` | none | Optional NICo partitions. The NVLink one can be replaced later but not cleared. |
| `nico.diskSelectionStrategy` | `smallest` | Disk for the OS: `smallest` or `largest` |
| `nodeLabels` | none | Fixed at creation and applied once after the node joins |
| `nodeTaints` | none | Key, optional value and effect. Fixed at creation. |
| `recycleBudget` | 0 | How many outdated nodes auto mode may mark at once. 0 marks none. |
| `autoModeDisabled`, `autoProvisionDisabled`, `provisioningMonitorDisabled` | false | Operator switches. The last one stops replacement of nodes that provision for more than the timeout, 2 hours by default. |
| `systemReservedMemory`, `kubeReservedMemory` | `16Gi`, `2Gi` | Kubelet reservations |
| `machineLabels`, `machineAnnotations` | none | Applied to new Cluster API Machines only |

Reserved domains are `kubernetes.io`, `k8s.io`, `nvke.nvidia.com`, `nke.nvidia.com` and `nke.io`. An operator can allow specific label keys under the first two through the controller chart value `nodeMetadata.allowlistedLabelKeys`. No taint under them can be allowed. The label `node-role.kubernetes.io/control-plane` can never be set **[official]**.

### 6.4 Annotated example: minimal cluster

This spec creates one control plane node with no VIP and no pools. It is the smallest valid request, and its limits are real. A single node without a VIP cannot be scaled, upgraded or replaced.

```yaml
name: demo-a
controlPlaneKubernetesVersion: 1.36.3
cniPlugin: ovn-kubernetes
etcdEncrypted: true
nico:
  orgID: example-org
  siteID: 00000000-0000-4000-8000-000000000001
  vpcID: 00000000-0000-4000-8000-000000000002
controlPlaneConfig:
  desiredCount: 1
  nico:
    instanceTypePreference:
      - 00000000-0000-4000-8000-000000000003
    vpcPrefixIDs:
      - 00000000-0000-4000-8000-000000000004
    release: example-ubuntu-24.04-amd64
```

The file is validated against the vendored OpenAPI schema by `c32_validate.py`, and the controller accepted the same body with a locally installed release name **[ran]**.

### 6.5 Annotated example: HA cluster with a GPU pool

This spec is what a real tenant cluster looks like. Three control plane nodes with a VIP and surge of one. A GPU pool with a label, a taint and a recycle budget. A small CPU pool for system pods.

```yaml
name: tenant-a
controlPlaneKubernetesVersion: 1.36.3
cniPlugin: ovn-kubernetes
etcdEncrypted: true
controlPlaneVIP: 10.20.0.50
network:
  podCIDR: 192.168.0.0/16
  serviceCIDR: 10.96.0.0/12
nico:
  orgID: example-org
  siteID: 00000000-0000-4000-8000-000000000001
  vpcID: 00000000-0000-4000-8000-000000000002
controlPlaneConfig:
  desiredCount: 3
  maxSurge: 1
  systemReservedMemory: 16Gi
  nico:
    instanceTypePreference:
      - 00000000-0000-4000-8000-000000000003
    vpcPrefixIDs:
      - 00000000-0000-4000-8000-000000000004
    sshKeyGroupIDs:
      - 00000000-0000-4000-8000-000000000005
    release: example-ubuntu-24.04-amd64
nodePools:
  - name: gpu-h100
    nodeNamePrefix: h
    desiredNodeCount: 4
    recycleBudget: 1
    nodeLabels:
      example.com/accelerator: h100
    nodeTaints:
      - key: example.com/gpu
        value: "true"
        effect: NoSchedule
    nico:
      instanceTypeID: 00000000-0000-4000-8000-000000000006
      vpcPrefixIDs:
        - 00000000-0000-4000-8000-000000000004
      sshKeyGroupIDs:
        - 00000000-0000-4000-8000-000000000005
      release: example-ubuntu-24.04-amd64
  - name: cpu-system
    nodeNamePrefix: c
    desiredNodeCount: 2
    nico:
      instanceTypeID: 00000000-0000-4000-8000-000000000007
      vpcPrefixIDs:
        - 00000000-0000-4000-8000-000000000004
      release: example-ubuntu-24.04-amd64
```

Read it in four parts. The VIP `10.20.0.50` sits outside both CIDRs. The control plane has three nodes so etcd survives one failure. The GPU pool taints its nodes with `NoSchedule`, so only pods that tolerate `example.com/gpu` land there. The `recycleBudget` of 1 lets auto mode mark one outdated node at a time. The controller accepted this spec with a local release name and returned `201` **[ran]**.

The taint choice deserves care. A `NoExecute` taint also evicts pods that already run on the node and lack a toleration, including DaemonSet pods that started before NVKE applied the taint **[official]**. Prefer `NoSchedule`.

### 6.6 Adding a pool, and the patch bodies

A node pool added later carries the cluster ID in the body.

```yaml
clusterID: 8ef5e56a-9b0d-4265-b39c-dcda0547fe97
name: gpu-workers-b
nodeNamePrefix: gb
desiredNodeCount: 4
recycleBudget: 1
nico:
  instanceTypeID: 00000000-0000-4000-8000-000000000006
  release: example-ubuntu-24.04-amd64
  vpcPrefixIDs:
    - 00000000-0000-4000-8000-000000000004
```

Two PATCH bodies cover the day-two changes. The first upgrades the control plane by one minor version.

```yaml
controlPlaneKubernetesVersion: 1.37.2
```

The second sets a pool's Kubernetes version and recycle budget through the REST API, because `nvkectl patch nodepool` accepts only `desiredNodeCount`.

```yaml
kubernetesVersion: 1.37.2
recycleBudget: 2
```

Deleting a node takes an optional body that flags the machine for repair in NICo.

```yaml
machineHealthIssue:
  category: Hardware
  summary: Node reports 7 of 8 GPUs
forceUnreachable: false
```

All four files pass `c32_validate.py`. Run it yourself. Replace the name `nodepool` with `cluster`, `patch-cluster`, `patch-nodepool` or `delete-node` to match the file.

```bash
python3 -I code/part11/c32_validate.py nodepool code/part11/c32_nodepool_add.yaml
```

The node pool update has one trap that the API does not guard. I sent `kubernetesVersion: 1.37.2` for a pool in a `1.36.3` cluster, and the API returned `200` and created a new node set **[ran]**. The source sets the field without a skew check **[source-code]**. Upstream Kubernetes does not allow a kubelet newer than the API server, so this is a guard you must add yourself. Chapter 11.33 gives a planner that does.

### 6.7 A linter for the mistakes

`c32_spec_lint.py` checks a spec for the rejections above before you send it. It flags errors the API refuses and warnings the docs say will hurt later, for example a single control plane node without a VIP, an even control plane count, `NoExecute` taints and `etcdEncrypted: false`. Every rule maps to a message I saw from the controller or to a documented limit.

```bash
python3 -I code/part11/c32_spec_lint.py code/part11/c32_cluster_minimal.yaml
```

```text
WARN  vip: no VIP: a single control-plane node cannot be scaled, upgraded or replaced; recreate the cluster to add a VIP
```

**Decision rule:** Decide VIP, CIDRs, etcd encryption and instance types before the first request, because the controller treats them as fixed, and lint every spec in CI.

**In one minute:** A cluster spec is one JSON document. The fields you cannot change later are the name, the networks, the NICo identifiers, the VIP and the instance types. Labels and taints are applied once and are not updated by NVKE.

## 7. Hands-on lab: run the real controller on your laptop

You cannot rent a bare-metal site for a chapter. You can still run the real controller and exercise the API, which is where most of the contract lives. This lab ran on macOS arm64 with Docker (Rancher Desktop) and Go 1.27.3. It needs no GPU, no NICo and no privileged containers.

**What ran here:** the controller built from commit 487f511, Postgres 18.6, the Temporal development server, a kind cluster with only the Cluster API and CAPNICo CRDs installed, the three release CRDs and one fixture release, and every `curl` call in this chapter. **What did not run:** bare-metal provisioning, NICo, SPIRE, `nvke-agent`, the bootstrap, enforcing authentication, the CAPI controllers and any GPU. A cluster therefore never leaves `Provisioning`, and deleting one stays in `Deleting` because no CAPI controller finishes the finalizers.

### Step 1. Start the dependencies

```bash
docker run -d --name nvke-pg -p 55432:5432 -e POSTGRES_PASSWORD=postgres postgres:18.6
docker run -d --name nvke-temporal -p 7233:7233 temporalio/temporal:latest server start-dev --ip 0.0.0.0 --namespace cloud-workflow-engine
docker exec nvke-pg psql -U postgres -c 'create database "nvke-controller"'
kind create cluster --name nvke --kubeconfig ./kind.kubeconfig
```

Expected result: both containers run, the database exists and `kind` prints the cluster-info line. The Postgres password here is a throwaway value for a local container. Never reuse it.

### Step 2. Install only the CRDs the controller needs

The controller exits when the Cluster API `Machine` CRD is missing **[source-code]**. Download the Cluster API v1.13.6 components file, keep only the CustomResourceDefinition documents and apply them. Then apply the CAPNICo CRDs and the three NVKE release CRDs from `controller/test/fixtures` and `controller/deploy/charts/nvke-crds/bases` in the repository, create the namespace `nvke-system`, and apply the fixture release.

Expected result: `kubectl get clusterreleases` lists `test-fixture-amd64`. I applied 17 Cluster API CRDs **[ran]**.

### Step 3. Build and run the controller

```bash
cd nvke/controller
go build -o /tmp/nvke-controller ./cmd/worker
export KUBECONFIG=./kind.kubeconfig CONTROLLER_CONFIG_PATH=$PWD/hack/local-controller-config.yaml
export DB_CONNECTION_STRING='postgres://postgres:postgres@localhost:55432/nvke-controller?sslmode=disable'
export SERVER_LISTEN_ADDRESS=127.0.0.1:8080
/tmp/nvke-controller
```

Expected result: log lines "Starting HTTP server", "Starting Temporal worker" and "API authorization is disabled". A repeating error says `namespaces "cloud-workflow-engine" not found` from the leader election. Create that namespace and the errors stop. The controller used it for its lease lock, and the local config file names it **[ran]**.

### Step 4. Check health, then create, list and delete

```bash
curl -s localhost:8080/healthz
curl -s localhost:8080/readyz
```

```text
{"status":"ok"}
{"status":"ok","checks":{"database":"ok","temporal":"ok"}}
```

Then post a cluster, list clusters, list node pools and nodes, patch a pool and delete a node. Use the files and the error cases from section 5 as your script. The API created Cluster API `Cluster` and `NicoCluster` objects in `nvke-system` for every cluster **[ran]**:

```text
NAMESPACE     NAME                              ...  AGE
nvke-system   cluster.cluster.x-k8s.io/demo-a        13s
nvke-system   nicocluster.infrastructure.cluster.x-k8s.io/demo-a   00000000-0000-4000-8000-000000000001
```

The nine PostgreSQL tables were `bun_migration_locks`, `bun_migrations`, `clusters`, `control_plane_configurations`, `credential_audit_events`, `node_pools`, `node_sets`, `nodes` and `workflow_outbox` **[ran]**. The metrics endpoint on port 9090 exposed 233 `nvke_` series, including per-node lifecycle timers and pool desired, actual and pending counts **[ran]**.

**What to record:** the HTTP status for each call, the `conditions` of a new cluster, the outbox row count and the pool metrics.

### Step 6. Run the self-checking lab

The lab file `c32_nvke_lab.py` validates every example in this series and checks the planner arithmetic. Run `python3 -B code/part11/c32_nvke_lab.py`. Expected last line: `16 passed, 0 failed`.

### Step 5. Clean up

Stop the controller, remove both containers and delete the kind cluster.

```bash
docker rm -f nvke-pg nvke-temporal
kind delete cluster --name nvke
```

**Decision rule:** Run this lab before you read any more documentation, because ten minutes of real error messages teach more than a page of field tables.

**In one minute:** A real controller runs on a laptop with three containers. You can exercise the whole API contract. You cannot provision anything, which is the point where NICo and hardware begin.

## Exercises

1. **Spec lint.** Write a spec with three control plane nodes and no VIP. Predict the lint result, then run `c32_spec_lint.py`. Worked solution: the linter reports ERROR `vip`. The controller returned `controlPlaneVIP is required to increase desired control-plane capacity above one`.
2. **CIDR sizing.** How many `/24` blocks does a cluster with 3 control plane nodes, 40 workers and `maxSurge` 1 need, and what is the smallest allowed pod CIDR? Worked solution: 3 + 40 + max(1, 1) = 44 blocks. A `/18` offers 64 and a `/19` offers 32, so `/18`. The allowed prefix range is `/12` to `/23`, so `/18` is valid.
3. **Error model.** Which status does the API return for a non-UUID ID, an unknown UUID and a duplicate name? Worked solution: 400 with a message, 404 with no body, and 400 with a message.
4. **Outbox.** A cluster exists in the API but no workflow ran. Name two places to look. Worked solution: the `workflow_outbox` row's `processed_at` and the Temporal UI for the workflow ID.
5. **Schema strictness.** Add `bogus: 1` inside a node pool's `nico` object. Which tools reject it? Worked solution: `c32_validate.py` through its strict walk, and `nvkectl create cluster`. The REST API itself validates against the schema as well. Run the three and compare.
6. **Preview risk.** List three API facts that would block a customer portal from calling NVKE directly. Worked solution: no per-customer authorization, plain HTTP, and an API that the architecture decision says will be replaced.

## Checkpoint questions

<details>
<summary>1. What is NVKE in one sentence?</summary>

An open-source Kubernetes management system that an AI factory operator installs to create and operate Kubernetes clusters for customers on its own NVIDIA GPU infrastructure.

</details>

<details>
<summary>2. Which three jobs does NVKE leave to others?</summary>

Bare-metal lifecycle, which NICo owns. Building and hosting OS images and Kubernetes binaries, which the operator does with NVKR. Running the customer's workloads.

</details>

<details>
<summary>3. What are the four repositories and their jobs?</summary>

`nvke` for the management plane, `nvkr` for builds, `cluster-api-provider-nico` for the NICo provider and `infra-controller` for NICo itself.

</details>

<details>
<summary>4. Which Kubernetes version is supported at preview?</summary>

Only 1.36.3, pinned. The node image stages other versions, but they are not supported.

</details>

<details>
<summary>5. What three engines live in the controller process?</summary>

A REST API backed by PostgreSQL, a Temporal worker and controller-runtime reconcilers.

</details>

<details>
<summary>6. Why does the API write to an outbox table instead of calling Temporal?</summary>

The cluster row and the outbox row commit in one transaction, so a committed cluster always has work queued even when Temporal is briefly unavailable.

</details>

<details>
<summary>7. Where does each workload cluster's control plane run?</summary>

On separate machines allocated from NICo, joined to the workload cluster as control plane nodes. Virtual machine control planes are on the roadmap, not available.

</details>

<details>
<summary>8. What does `nvke-agent` do, and who starts the connection?</summary>

It runs kubeadm, installs the CNI and handles drain, reboot and teardown. The controller dials the agent over gRPC on port 15005. The agent does not call home.

</details>

<details>
<summary>9. What status codes does a create and a delete return?</summary>

Create returns 201 with the stored object. Delete returns 202. Progress is read from conditions.

</details>

<details>
<summary>10. How does PATCH treat null and unknown fields?</summary>

Both are rejected with 400. Omitted fields stay unchanged and an empty array clears a list.

</details>

<details>
<summary>11. Which endpoints need no token?</summary>

`/openapi.yaml`, `/api/docs/`, `/healthz` and `/readyz`.

</details>

<details>
<summary>12. What is the authentication state after a default install?</summary>

Off. The API serves plain HTTP on NodePort 30080 and does no authorization.

</details>

<details>
<summary>13. How many operations does the OpenAPI file define, and what is missing?</summary>

Twenty-one operations on 12 paths. There is no management cluster endpoint and no kubeconfig endpoint.

</details>

<details>
<summary>14. Which spec fields can you never change after creation?</summary>

The name, the networks, the NICo organization, site and VPC, the VIP, the CNI and each pool's instance type. Node labels and taints are also fixed.

</details>

<details>
<summary>15. How many pod CIDR blocks does a cluster need?</summary>

One `/24` per control plane and worker node plus `max(1, surge)` blocks of headroom.

</details>

<details>
<summary>16. Why is a two-node control plane a bad choice?</summary>

Two voters tolerate no failure, and the certificate renewal controller excludes exactly two control plane nodes.

</details>

<details>
<summary>17. What does a `NoExecute` taint do that `NoSchedule` does not?</summary>

It evicts running pods that lack a toleration, including DaemonSet pods that started before the taint was applied.

</details>

<details>
<summary>18. What happened when the pool version was set above the control plane?</summary>

The API accepted it with 200 and created a new node set. The source applies the field without a skew check, so you must guard it yourself.

</details>

<details>
<summary>19. What did the local lab prove, and what could it not prove?</summary>

It proved the API contract, validation messages, Cluster API object creation and metrics. It could not prove provisioning, NICo, SPIRE, the node agent or enforcing authentication.

</details>

<details>
<summary>20. What does the architecture decision record of 2026-11-05 imply for API clients?</summary>

It has status proposed and says the PostgreSQL-backed REST API will be replaced and retired. Isolate your client code behind an interface.

</details>

## Sources and review notes

### Sources

- NVKE repository `dsx-ai-factory/nvke` at commit 487f511 (2026-11-10): `README.md`, `ROADMAP.md`, `docs/architecture.md`, `docs/concepts.md`, `docs/lifecycle.md`, `docs/overview/*.md`, `docs/workload-clusters/create.md`, `docs/workload-clusters/node-pools.md`, `controller/api/openapi.yaml`, `controller/internal/server/clusters.go`, `cluster_network.go`, `node_metadata_validation.go`, `node_pools.go`, `controller/hack/local-controller-config.yaml`, `docs/adrs/20261105-capi-architecture.md`. Fetched 2026-11-11.
- NVIDIA developer blog, "Manage Kubernetes Clusters for GPU Infrastructure with NVIDIA Kubernetes Engine", 2026-11-10, fetched 2026-11-11.
- NVIDIA documentation site `docs.nvidia.com/nvke`, which is built from the repository `docs/` folder (`fern/docs.yml`).
- NICo README, `dsx-ai-factory/infra-controller`, fetched through `gh api` on 2026-11-11.
- CNCF pull requests `cncf/k8s-conformance#4492` and `cncf/landscape#5236`, read through `gh api` on 2026-11-11.

### Cross-references

- [11.31](31-nvidias-open-source-ai-factory-kubernetes-stack.md) for the wider stack. [11.30](30-lab-multi-node-gpu-kubernetes-on-gke-and-nebius.md) for managed Kubernetes on Nebius and GKE. [11.4](04-gpu-operator-architecture-and-operands.md) and [11.5](05-gpu-operator-installation-configuration-and-upgrades.md) for the GPU Operator. [11.33](33-nvke-in-depth-part-2-installation-nvkr-and-cluster-lifecycle.md) and [11.34](34-nvke-in-depth-part-3-operations-security-failure-modes-and-comparison.md) for the rest of this series.
- Code: `code/part11/c32_validate.py`, `c32_spec_lint.py`, `c32_upgrade_planner.py` and their tests, plus the example files named in the text and the vendored `c32_nvke_openapi_487f511.yaml`.

### Migrated from `nvidia-devops`

None. This chapter draws on upstream sources only. The `nvidia-devops` corpus has no NVKE material.

### Explicitly labelled inferences

- The state inventory in section 3.4 is my synthesis from the sources, not an NVKE document.
- The advice to add a pool-version guard in section 6.6 is mine. Upstream Kubernetes policy is the reason.
- That "Forge" in the architecture diagram of `docs/architecture.md` is the former name of the NICo API is my reading of the stack config default `apiName: forge`.

### Not verified or not run

- Bare-metal provisioning, NICo, SPIRE attestation, `nvke-agent`, the bootstrap, enforcing authentication and any GPU step did not run, because they need hardware or an identity provider.
- The CNCF Certified Kubernetes Installer claim from the blog was not checked in the CNCF repositories.
- The 21 unprocessed or partly processed outbox rows were observed but not explained.
- I found no heise or Cloud Native Now article on NVKE through search, so none is cited.
- `nvkectl get providers` was not run because it downloads a kubectl binary on first use.

### Verification log

| Measure | Count |
|---|---|
| Claims checked against a source | 74 |
| Confirmed | 68 |
| Corrected | 3 |
| Removed | 1 |
| Still unverified | 5 |

Corrected: the OpenAPI description claims every operation needs a token, while a default install runs with authentication off. The documentation example of a `1.34.0` upgrade is stale against the supported `1.36.3`. The `calico` schema value does not mean Calico is supported.
