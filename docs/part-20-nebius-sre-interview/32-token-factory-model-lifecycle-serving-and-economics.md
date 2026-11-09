---
id: "c20-32"
title: "20.32 Token Factory: model lifecycle, serving, gateways, caching and economics"
sidebar_label: "20.32 Token Factory architecture"
sidebar_position: 32
description: "A detailed guide to Token Factory's public product architecture: control and data planes, access, model deployment, post-training, serving, caching, billing, observability, privacy and production trade-offs."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "Laptop / browser"
---

# 20.32 Token Factory: model lifecycle, serving, gateways, caching and economics

A product team has a working model and wants to serve real traffic. The team now needs to answer questions that a model benchmark cannot answer: which model version is running, where prompts are processed, how the gateway identifies an endpoint, how costs are counted, what a cache hit means, and what the service will do during an outage.

Token Factory publishes a useful amount of customer-facing architecture. It does not publish the complete implementation of its internal gateway, router, scheduler, or inference fleet. This chapter follows the public contract from account and model selection through endpoint configuration, request serving, cached-token accounting, observability, data handling, and support. The goal is to explain what a solutions architect can promise—and what must be confirmed in the live docs or contract.

## What the interviewer is testing

This chapter serves the system-design, project-deep-dive, and incident rounds. A strong answer traces control-plane actions separately from inference traffic, chooses a deployment mode from workload needs, states the cache and billing model, and distinguishes product behavior from a published experiment. It also shows that you will not promise regional failover, an SLA, or a privacy property that the governing terms do not support.

Likely prompt: “Design the production path for a customer who fine-tunes an open model, deploys it to Token Factory, and serves an agent. Walk me through the endpoint, gateway, cache, bill, observability, and recovery boundaries.”

## The core ideas

### 1. Start with the product contract, not an imagined gateway

Token Factory gives customers a browser UI, model catalog, OpenAI-compatible API, organizations and projects, API keys, inference products, post-training capabilities, and billing/observability surfaces. The public service line includes Public Serverless inference and Dedicated Endpoints. The product is not the same thing as Nebius AI Cloud Serverless AI, which runs customer-provided containers, or a customer-managed Kubernetes inference fleet.

Before drawing an architecture, decide what type of serving the customer needs. Public Serverless is the shortest path to try models and absorb variable use, but its region is Global and it has dynamic service limits. Dedicated Endpoints expose a deployment template, a chosen region, GPU shape, replica bounds, and a routing key. A self-managed AI Cloud platform gives still more control but transfers model runtime, gateway, scaling, and on-call responsibility to the customer.

The first set of architectural promises is public and concrete: what a customer configures, which API endpoint is called, what fields are returned, which metrics are visible, and how the product says it bills. The second set is not public: which proxy technology receives requests, how workers are selected internally, what autoscaling signal fires first, how caches are physically distributed, or how an internal fleet recovers a worker.

Keep those sets separate. The control/data-plane guide is authoritative for public endpoint interfaces. The Nebius engineering blogs provide selected architecture examples, but not the complete service implementation. The Token Factory Supplemental Terms and DPA govern legal commitments; product marketing pages do not replace those documents.

**Answer from the customer-visible contract first; label every description of internal behavior as inference unless sourced.**

### 2. Choose the endpoint product from the workload and data contract

A prototype team may value fast access to many models more than location stability. A regulated production team may make the opposite choice. “Serverless versus dedicated” is therefore a product, residency, and operating decision—not simply a compute-price choice.

| Choice | Capacity and region behavior | Customer control and charge model | Architect's caution |
|---|---|---|---|
| Public Serverless | Shared; Region displays Global and processing location can change | OpenAI-compatible model APIs; token-based input/output pricing, with cached-input price for supported models | Not for a requirement that depends on a fixed processing region; observe model deprecation notices and dynamic rate limits |
| Dedicated Endpoint | Isolated deployment; region selected at creation and fixed for the endpoint | Model template, flavor, GPU type/count, minimum/maximum replicas; GPU-time pricing | Capacity is available while active but can be released on stop or interruption; scale-out above minimum is not guaranteed |
| AI Cloud Serverless AI | Customer container endpoint/job/Devlab; region and resource details follow that service | Managed container lifecycle with usage-based per-second billing | Customer still owns container, model server, input contract, and application semantics |
| Customer-managed Kubernetes/VM fleet | Customer chooses network, cluster layout, pool strategy, and endpoint routing | Customer controls runtime and deployment; pays underlying resources and operates them | Requires a platform team, security review, upgrades, and a complete incident/recovery plan |

The Token Factory Public Serverless guide calls the Global location variable and says it is unsuitable when production requires a stable region. A region-specific API URL may cease to match the model's processing region. Dedicated Endpoints are different: the Legal Quick Guide describes the selected region as a contractual data-processing boundary and says Token Factory does not route, overflow, or fail over that endpoint to another region.

Model availability also changes. The November 9, 2026 notice lists specific Public Serverless models removed on that date and says Dedicated Endpoints are unaffected. It does not say all Public Serverless models are removed. Read the live catalog, the current notice, and the model card before designing a migration; Nebius does not silently remap requests from a deprecated model ID.

**Use Public Serverless when global shared service behavior fits; use Dedicated when region and deployment controls matter; use Cloud primitives when you must own the runtime.**

### 3. Separate organizations, projects, users, keys, and cloud identities

An SRE is asked to revoke a contractor's access without disabling a production endpoint. Token Factory and AI Cloud each have organizations and projects, but their identities and credentials are not interchangeable.

Token Factory's organization contains users, groups, projects, billing, and Zero Data Retention settings. Projects contain API keys, endpoints, files, datasets, and fine-tuning jobs. Organization Admin can manage all projects. Organization Billing Manager can view usage and change billing settings but has no project-resource access. Project Admin manages membership; Project Member can operate project resources and create/delete its own keys. These roles let an architect separate financial viewing from API access.

The API key is a bearer credential for inference and project operations. The control-plane API uses a bearer token to list templates and manage Dedicated Endpoints. A cloud service-account token or access key instead manages AI Cloud resources through the Nebius API/CLI/SDK. A customer gateway can add its own user authentication and policy before calling Token Factory, but the gateway's credentials should remain server-side and be scoped to the project's workload.

The request bill and model permissions are not identical to these identities. A user can hold project access while a runtime service uses a dedicated API key. Rotate keys when workloads change owners; keep a separate path for support and billing viewers. Never place a long-lived key in browser code, a public notebook, or a container image.

**Map each human, service, endpoint, and cloud resource to its own permission scope before issuing credentials.**

### 4. Trace provisioning and inference through separate planes

The control plane changes desired endpoint state. The data plane processes prompts. The public docs expose separate base URLs and identifiers for those jobs.

Dedicated Endpoint management uses the common control-plane host `https://api.tokenfactory.nebius.com`. A customer lists model templates, then creates an endpoint using a supported `model_name`, `flavor_name`, `gpu_type`, `gpu_count`, `region`, and scaling policy. `gpu_count` means GPUs per replica. The API response returns an `endpoint_id` for update/delete and a `routing_key` to use as the model value in inference requests.

Inference calls go to a regional `/v1` data-plane host. The current guide shows the common hostname for `eu-north1`, and region-specific hosts for examples such as `eu-west1` and `us-central1`. Use the current URL for the endpoint region rather than assuming the control-plane hostname works everywhere. Public Serverless has a Global location and can change processing region, so do not pin its URL based on a transient observed location.

The call path a customer can observe is: application → bearer key → regional OpenAI-compatible API → routing key → endpoint/model → streamed or complete response. A dedicated endpoint is selected by its routing key; this does not reveal how Token Factory maps that key to replica pods internally. The docs do not publish internal DNS, a particular proxy implementation, control-plane storage, control-state propagation, or worker selection.

| Identifier or surface | Documented role | Unknown behind the service boundary |
|---|---|---|
| API key | Authenticates an organization/project caller | Internal token validation path |
| `endpoint_id` | Identifies a deployment for lifecycle operations | Provider resource IDs and reconciliation implementation |
| `routing_key` | Model identifier used to address the endpoint | Worker/replica selection algorithm |
| Regional `/v1` URL | Receives inference requests in the chosen region | Gateway fleet, load balancer topology, and internal network path |
| Template | Valid combinations of model, flavor, GPU and region | Scheduler mechanics used after endpoint creation |

**Keep provisioning separate from request serving in every diagram and incident explanation.**

### 5. Deploy, update, stop, and replace an endpoint deliberately

An endpoint creation returns before GPUs and model replicas necessarily become ready. The lifecycle guide separates deployment lifecycle (`starting`, `updating`, `running`, `stopping`, `stopped`, `error`) from readiness (`not_ready`, `partially_ready`, `ready`). A running endpoint can still be only partially ready. A control-plane success response does not prove that the data plane can serve the expected load.

The deployment template defines the model, flavor, GPU type, GPUs per replica, region, `min_replicas`, and `max_replicas`. Nebius's best-practice guide says GPU type/count determine per-replica performance while replica counts shape concurrency and availability. More replicas do not fix insufficient GPU memory or per-request latency on an underpowered replica; first compare vertical scaling with horizontal scaling.

`region` cannot be changed after creation. Moving the endpoint means create a new deployment, validate it, transfer or configure its model/weights, shift traffic, then retire the old one. The `enabled` field stops or starts an endpoint and frees capacity while stopped. A stop is therefore both a cost control and a capacity-risk decision.

Custom model weights remain a controlled feature. The public guide marks them beta and available on request. The Create Dedicated Endpoint OpenAPI schema includes `custom_weights_id` and an optional `reservation_policy`, but the exact account eligibility and reservation behavior must be checked against the active API schema, capacity agreement, and account manager. Do not assume any arbitrary Hugging Face checkpoint can be attached to any template.

For a production rollout, write down a traffic cutover, readiness test, rollback condition, and old/new model identity before changing the endpoint. Canary and shadow patterns are good customer-side designs, not published promises about Token Factory's deployment controller.

**Treat region changes as migration projects and wait for readiness before directing production traffic.**

### 6. Connect post-training and data workflows to inference

Token Factory documents a model-development loop, not just an inference API. Data Lab brings inference logs, uploaded data, filtered datasets, batch outputs, and fine-tuning outputs into a common workspace. Post-training includes supervised fine-tuning of full weights or LoRA adapters, custom speculator training, datasets, and resulting checkpoints. Custom weights can then be attached to Dedicated Endpoints where the supported workflow is enabled.

This loop is useful when a team can express a testable quality or latency problem. For example, a coding assistant can use accepted/rejected completions to prepare a training set, fine-tune a base model, measure quality against a fixed eval, then compare the checkpoint on an endpoint. A workload-specific draft model can improve speculative decoding acceptance when the application's traffic has repeated patterns. Training itself may run in separate Nebius infrastructure; do not assume all fine-tuning uses the same dedicated endpoint GPUs.

The Token Factory Data Lab and legal documents are architectural boundaries. The Data Lab says chat-completion logs are collected unless ZDR is enabled. The Token Factory Supplemental Terms and the plain-language Legal Quick Guide should both be read before submitting sensitive data. The quick guide says ZDR is organization-wide, stops retention of prompts/responses and opts out of speculative-decoding data use, possibly reducing performance. The supplemental terms permit Nebius to process input/output for service operation and to train smaller speculative-decoding models. These statements are not phrased identically; the quick guide says it is a summary and the DPA/terms prevail. A regulated customer should obtain account-specific written confirmation instead of relying on a marketing page.

Fine-tuning has its own geography and retention policy. The legal guide says fine-tuning datasets and artifacts are stored in the EU even when a US job is processed in the US. That is distinct from Dedicated Endpoint inference, whose selected region is contractually pinned. Map prompts, logs, datasets, weights, metrics, and billing metadata separately.

**Ask where each data class is processed, stored, logged, and deleted before approving a model lifecycle.**

### 7. Understand the serving options without guessing the runtime

Token Factory's inference documentation lists text, embeddings, and vision models, OpenAI-compatible APIs, vLLM request parameters, and performance templates. Base and Fast flavors provide different latency/throughput/cost profiles. Documented optimization techniques include continuous batching, paged attention, prefix/context caching, quantization, flash attention, and speculative decoding.

These names explain what the platform exposes; they do not identify the exact production runtime. A model template is a deployable performance blueprint defining supported flavors, GPU types, and regions. The Customer sees the configuration and metrics, not necessarily the engine image, process model, scheduler, cache-store topology, tensor-parallel layout, or rollout internals.

Nebius's blog case studies add implementation evidence at the workload level. The chat-app case describes prefill/decode specialization, cache-locality routing, backpressure, retry adjustments, and probe lessons. A separate vLLM experiment measured better tail latency when cache locality was considered. Another validated AI Factory stack uses NVIDIA NIM deployments on Nebius GPUs alongside a DataRobot agent layer, while Token Factory provides model access for experimentation. These examples show architectural options, not a uniform Token Factory blueprint.

For a design interview, explain prefill versus decode, KV-cache growth, continuous batching, and model quantization briefly, then refer to 20.13 and Part 15 for generic internals. Keep 20.32 focused on the mapping between those mechanisms and public Token Factory controls.

**Describe the serving features documented for customers; do not assert a specific engine topology without a source.**

### 8. Treat caching as performance, billing, and privacy architecture

Token Factory automatically reuses matching prompt prefixes. Stable system instructions, tool definitions, few-shot examples, and earlier conversation turns can create reusable prefixes. The API returns cached-token counts in usage details; streaming requests may need `stream_options.include_usage` for the final usage object.

The serving and billing behavior differs by product. Public Serverless may charge cached input at a model-specific cached-token rate. Dedicated Endpoints are billed by GPU time, so cache hits can raise throughput or reduce latency without changing the endpoint's GPU-hour bill. The `prompt_cache_key` is a routing hint to the process holding cache, not a credential or isolation control.

Cache scope also differs. Public Serverless caches prefixes within a model across organizations, projects, and API keys. The documentation says the cache stores derived state, not readable prompt or response text, and a hit does not reveal who sent the earlier request. Dedicated Endpoint cache is isolated per customer. Cache reuse is best-effort, can be evicted, and has no SLA or minimum hit rate. It works with ZDR according to the cache guide, but the legal contract controls data commitments.

This is a subtle systems trade-off. A shared cache can reduce duplicate prefill, yet the model catalog, tenant access, and cache-scope statements must be understood before an architect puts sensitive or tenant-specific material at the start of prompts. Do not design authorization around cache behavior. Use per-tenant application policy and model access controls for security; use cached-token metrics and response usage for performance/cost analysis.

**A cache hit is a best-effort optimization, never an authorization boundary or a guaranteed discount.**

### 9. Distinguish documented routing from published routing experiments

The Token Factory public interface gives the caller a `routing_key` and a regional inference URL. It does not disclose the complete internal gateway or router. Ask what is documented before assuming request retries, queue policies, cache-aware placement, or admission control are provider features.

Nebius has published specific routing experiments. In a vLLM agent-style test with 300 concurrent trajectories, a cache-aware router preferred a replica with a matching KV cache and fell back when that replica was overloaded. The post reports nearly half the average step time and p95 latency below twenty seconds, compared with default Kubernetes ClusterIP routing. It did not compare a standalone least-request-only baseline; eviction and memory-aware routing were left for future work.

The DataRobot/Nebius benchmark is another bounded example: 8× HGX B200 systems, NVIDIA Dynamo, and specified trace workloads reported up to 245,000 tokens/s, with hundreds-of-milliseconds TTFT and KV-routing gains ([Nebius summary](https://nebius.com/blog/posts/datarobot-validated-ai-factory-stack)). Those figures are from one validated configuration, not a Token Factory SLA or capacity quote. See the [DataRobot technical analysis](https://www.datarobot.com/blog/datarobot-nebius-enterprise-ai-factory-optimized-for-agents/) for workload and benchmark detail.

In a customer-owned gateway, cache affinity should be balanced with queue pressure, tenant fairness, and overload behavior. A router that pursues cache hits without a load bound can create a hot replica and worsen p99. Use bounded retries, admission control, backpressure, and model/region allow-lists. Label this as your design, not as Nebius's production algorithm.

**Quote a routing measurement only with its workload and comparison baseline attached.**

### 10. Read observability, billing, and commercial terms together

Token Factory Inference Observability is documented as available only for Dedicated Endpoints. It exposes requests and tokens per minute, prompt/output size, p50/p90/p99 latency, streaming TTFT, output speed, active replicas/GPUs, utilization, status-code errors, and cache-hit rate. Some capacity metrics depend on the pricing model. Metrics are aggregated in rolling windows and are for operational analysis, not invoice reconciliation.

Metrics are collected where inference runs but eventually stored in `eu-north`, according to the product docs. Prometheus/Grafana integration uses a project-scoped static API key and the docs recommend at least a 15-second scrape interval. Organization Admin can view across projects; Billing Manager does not have inference-observability access. For strict residency, map inference payloads, metric samples, Data Lab records, and billing metadata as separate data classes.

Product billing currently has several layers:

| Product/account layer | Meter | Architectural consequence |
|---|---|---|
| Public Serverless | Input, cached-input where priced, and output tokens | Cost follows requests and token mix; dynamic rate limits protect shared capacity |
| Dedicated Endpoint | GPU time, per-minute granularity | Baseline replica floor costs while active; actual charge depends on ready/active state and contract |
| Nebius AI Cloud Compute | VM/GPU time, disks/filesystems, storage, network, managed services | The customer fleet pays for idle nodes and platform resources as well as useful tokens |
| Customer-operated inference fleet | Underlying cloud resources plus optional internal token/key ledger | The customer must build metering, cost attribution, budgets, and reconciliation |

There is a current documentation conflict worth raising with an account team. The Token Factory changelog and Supplemental Terms say fees are post-paid unless an Order Form says otherwise; the Billing & Consumption page still describes balance top-ups and automatic card charging. Dedicated Endpoint billing policy says zero replicas are inaccessible and not billed, while its table says provisioning/not-ready/partially-ready are not billed and ready capacity is billed. The page's prose also calls an endpoint active and billable when one or more replicas run. Do not resolve that ambiguity with a dashboard guess—confirm the applicable plan, Order Form, and line-item rules.

The enterprise sales page advertises 99.9% SLA, reserved capacity, and failover; the Supplemental Terms say no SLA applies unless agreed otherwise in writing. That is not necessarily a contradiction: marketing describes an enterprise offer, while legal terms set the default contract. The architect must identify which agreement applies to the actual tenant.

**Take service-level promises from the applicable contract and cost from usage reports, not from marketing or utilization graphs.**

### 11. Model capacity and recover from a provider or application failure

For self-service Dedicated Endpoints, the capacity guide says GPUs come from an on-demand shared pool. Minimum replicas remain allocated only while active. Stopping or interruption releases them; restart requests capacity again. Maximum replicas are a burst ceiling rather than guaranteed long-term supply. The endpoint's region is immutable, and the legal guide says there is no provider-managed multi-region routing or automatic failover.

Endpoint start/update status and readiness must be watched separately. `starting/not_ready` is provisioning, `partially_ready` is degraded capacity, and `running/ready` is the expected serving state. The FAQ maps `401` to authentication, `403` to permission, `404` to readiness/host/routing key, `409` to capacity or configuration conflict, and `422` to invalid payload/template. Check the status page and support escalation thresholds; do not turn transient lifecycle behavior into an unbounded client retry loop.

For a customer-managed GPU fleet, Managed Kubernetes uses Node Problem Detector and GPU health checks. The documented repair can cordon a faulty GPU node, wait for workloads, drain it, stop/start the VM, and uncordon it. The drain can take up to an hour. Training jobs need checkpointing outside ephemeral local NVMe; endpoints need enough warm or reserved capacity to survive node replacement. Soperator provides a separate Slurm recovery model with health checks and checkpoint-aware jobs. Neither cloud node repair path proves Token Factory's internal recovery mechanism.

| Failure domain | Detection signal | First safe response | Recovery owner |
|---|---|---|---|
| Model quality/configuration | Eval regression, finish-reason drift, malformed usage | Freeze rollout and compare against the known-good version | Customer model/app team |
| Endpoint capacity | Readiness partial, active replicas below desired, 429/5xx | Shed load, bound retries, request support/capacity | Token Factory service plus customer edge |
| GPU node | Xid, health condition, node NotReady, link errors | Drain/replace through documented service; preserve checkpoint | Nebius for managed node repair; customer for job restart |
| Region | Status incident, API reachability loss, pinned-region outage | Follow residency-approved degraded/failover plan | Customer routing + Nebius incident/support process |
| Facility/capacity | Provisioning delay, no capacity in template region | Use a contracted alternate capacity plan or communicate degraded service | Nebius capacity team and customer product owner |

If cross-region continuity is required, prepare an alternate endpoint and model version before the incident, test it under load, and confirm its data-processing permissions. If it is not authorized, fail closed or degrade rather than silently violating residency.

**Separate provider repair of infrastructure from customer recovery of application state and service objectives.**

### 12. Interview-ready architecture decision

The interviewer asks, “How would you build this for a customer?” Start with workload and contract discovery: train or serve, model size/modality, request/token rates, context length, streaming, TTFT/TPOT, tenant count, data location/retention, availability/RTO/RPO, and spend ceiling.

Then select the operating boundary. Token Factory Public Serverless is for rapid access when global processing and shared limits are acceptable. Dedicated Endpoint is the managed model option for fixed-region production and GPU/replica controls. AI Cloud Serverless AI is for customer containers without a cluster. Managed Kubernetes or the Solutions Library fleet is for teams that need custom gateways, tenant quotas, placement, batch jobs, or their own telemetry. Soperator is a training scheduler path when Slurm semantics matter.

Draw the customer-owned path explicitly: user/app authentication → customer policy gateway → cloud or Token Factory API → model endpoint/engine → cache and storage → metrics, audit and billing. Mark which components are managed, which are customer-run, and which remain unknown. For a self-managed fleet, add the control cluster, region clusters, Kueue/MultiKueue placement, Envoy authorization, model registry, data path, and recovery flow. For Token Factory, do not draw internals the service does not document.

Close by naming one risk and one validation test per layer. Check model quality and tokenizer, endpoint readiness, capacity availability, cache-hit profile, Cloud region routing, storage durability, auth isolation, billed usage, and failover behavior. A solution is ready for production only when those checks have owners and acceptance criteria.

**End the whiteboard with the unresolved contracts and the next validation step, not another box.**

## How to answer out loud

Use this opening: “I’d split the system into facility/fabric, AI Cloud resources, managed or customer-owned orchestration, and the model/API product. I would not equate Token Factory with a customer Kubernetes cluster. For training I would compare Soperator with Managed Kubernetes or GPU VMs; for serving I would choose Public Serverless, Dedicated Endpoint, AI Cloud Serverless AI, or a custom fleet according to region, control, and operating burden. I’d map identity, data, cost, and recovery separately, then validate actual project capacity and contract guarantees.”

Rehearse three follow-ups: (1) explain why GPU topology changes distributed-training performance; (2) justify shared filesystem, Object Storage, or local NVMe for weights/checkpoints; (3) distinguish cloud capacity reservations from a Token Factory endpoint's active replica floor. State which numbers are source measurements and which are your assumptions.

## Worked scenarios

### Scenario 1: A planned AI factory is not usable quota

A customer hears that Nebius is building a large Finnish AI factory and asks for 64 B300 GPUs next week. First identify the correct service region, platform/preset, and whether B300 capacity is public there. Check the tenant's GPU quota and capacity advisor. The 310 MW Lappeenranta announcement is for first capacity expected in 2027; it does not satisfy a 2026 order. Offer currently available H200/B300 alternatives only after confirming the exact project and region.

### Scenario 2: Training all-reduce stalls across nodes

The GPU nodes are healthy and utilization is high, but all-reduce time rises after scaling out. Confirm that every VM belongs to the same GPU cluster and fabric. Read topology and link counters, validate NCCL selected `NET/IB`, compare same-POD versus cross-POD placement, and run the supported NCCL test. Then separate fabric bottleneck from shared-filesystem read stalls. Do not “fix” an InfiniBand job by moving one rank to a pool without the same fabric.

### Scenario 3: A regional self-managed serving fleet loses a spot worker

The API latency rises after one spot GPU VM stops. The customer uses KServe replicas plus a job queue and checkpointed jobs. Confirm node state, pending pods, pool max, quota, image-cache readiness, and whether the model is pinned to the lost pool. Scale/reschedule within the budget, but verify checkpoint durability and expected cold start. Cloud node replacement is not equivalent to an active inference replica being immediately ready.

## Hands-on lab

Use public documentation only; no cloud resource creation is required.

1. Choose an example: eight-GPU distributed training, an interactive 8B model endpoint, or a multimodal agent. Write the SLO, data location, concurrency, and cost boundary. **Expected:** a workload statement, not a product choice.
2. Choose service and region options from the Compute and service catalogs. Check the GPU platform table and mark capacity/quotas that require a live project query. **Expected:** one preferred and one fallback design with the risk named.
3. Draw the four efficiency layers and map one optimization to each. **Expected:** model/runtime, cluster, fabric, and facility are separate owners and evidence classes.
4. Assign datasets, weights, cache, checkpoints, and outputs to storage types. **Expected:** each item has a durability class, access pattern, and recovery copy.
5. Write a failure runbook for one fabric/node/storage event. **Expected:** signal, safe mitigation, data-loss boundary, recovery owner, and validation test.

I did not provision VMs or GPU clusters. Facility sizes, PUE, topology gains, and MLPerf results in public materials are dated company announcements or benchmark claims, not live customer acceptance tests.

## Drill questions

1. What are the four layers in Nebius's public energy-to-AI framework?

<details><summary>Answer</summary>
Model, cluster, fabric, and data center. The framework is a company synthesis, not a full internal service diagram.
</details>

2. Does the 310 MW Lappeenranta project mean GPU capacity is available now?

<details><summary>Answer</summary>
No. The announcement says the first capacity is expected in 2027. Query the current product-region catalog and project capacity for an actual deployment.
</details>

3. What is the difference between a GPU VM and a GPU cluster?

<details><summary>Answer</summary>
A VM supplies one host's GPUs. A GPU cluster places compatible VMs in one InfiniBand fabric for multi-node communication and topology-aware scheduling.
</details>

4. Why can a healthy GPU utilization chart coexist with poor distributed-training performance?

<details><summary>Answer</summary>
The workload may be waiting on collectives, crossing network tiers, reading data slowly, or retrying. Correlate job timings with topology and link counters.
</details>

5. What data belongs on local SSD?

<details><summary>Answer</summary>
Recreatable scratch, cache, and staging data. Checkpoints and model artifacts need a durable storage path because local SSD disappears with the VM.
</details>

6. What is the purpose of a shared filesystem in an AI factory?

<details><summary>Answer</summary>
It gives multiple VMs shared access to datasets, weights, or checkpoints. Verify consistency and access patterns; it is not automatically the best path for every workload.
</details>

7. When would you choose Soperator?

<details><summary>Answer</summary>
When the training environment needs Slurm job semantics, accounting, and HPC scheduling while Kubernetes manages the service resources.
</details>

8. Does a capacity block guarantee every service tier has capacity?

<details><summary>Answer</summary>
No. A block applies to specified GPU platform/region/fabric and eligible resources. Confirm the product, interval, project limit, and endpoint reservation behavior.
</details>

9. What does an AI Cloud budget do when a threshold is crossed?

<details><summary>Answer</summary>
It sends an alert; it does not stop usage. Use quotas or application-level controls when enforcement is required.
</details>

10. How do you explain the role of the AI Cloud service catalog in a Token Factory design?

<details><summary>Answer</summary>
It lists customer-visible Cloud building blocks. It does not disclose the specific internal compute, network, or orchestration path for a managed Token Factory endpoint.
</details>

## Common mistakes and weak answers

- Treating an announced campus as an orderable GPU pool.
- Choosing a GPU by name without checking model memory, preset, region, quota, and fabric.
- Assuming a healthy node means a healthy collective or model request.
- Putting the only checkpoint on ephemeral local SSD.
- Conflating Serverless AI custom containers with Token Factory model APIs.
- Treating a topology benchmark, PUE, or marketing throughput figure as a service guarantee.

## Connections to the rest of the handbook

- [20.30 Public architecture map](./30-nebius-ai-factory-to-token-factory-architecture.md) — overview and evidence boundary.
- [20.31 Nebius AI Cloud foundation](./31-nebius-ai-cloud-foundation-gpu-fabric-and-platform-choices.md) — the resource and managed-service substrate beneath Token Factory.
- [20.33 Production AI Factory patterns](./33-ai-factory-solution-architecture-ha-and-recovery.md) — reference architectures and failure recovery.
- Parts 6, 11, 12, 13, 15, and 17 — Slurm, GPU Kubernetes, networking, storage, inference, and operations.

## Sources and review notes

Official documentation, public repositories, and company announcements checked 2026-11-09. Recheck current price, region, capacity, and project availability before promising an architecture.

- [Nebius AI Cloud services](https://docs.nebius.com/overview/services), [GPU platform/preset list](https://docs.nebius.com/compute/virtual-machines/types), [GPU cluster networking](https://docs.nebius.com/compute/clusters/gpu/index), [InfiniBand topology](https://docs.nebius.com/compute/clusters/gpu/topology/index).
- [VPC](https://docs.nebius.com/vpc/overview), [Compute storage types](https://docs.nebius.com/compute/storage/types), [Object Storage classes](https://docs.nebius.com/object-storage/storage-classes), [Kubernetes components](https://docs.nebius.com/kubernetes/components), [autoscaling](https://docs.nebius.com/kubernetes/node-groups/autoscaling), and [GPU node repair](https://docs.nebius.com/kubernetes/maintenance/health-checks).
- [AI Cloud pricing model](https://docs.nebius.com/signup-billing/billing-models/overview), [capacity blocks](https://docs.nebius.com/overview/limits/capacity-block-groups), [cost labels](https://docs.nebius.com/signup-billing/usage/cost-allocation-labels), and [GPU VM monitoring](https://docs.nebius.com/compute/monitoring/virtual-machines).
- [Nebius energy-efficiency framework](https://nebius.com/blog/posts/the-energy-behind-ai) and its [whitepaper](https://26806167.fs1.hubspotusercontent-eu1.net/hubfs/26806167/gated/nebius-the-energy-behind-ai.pdf); [Mäntsälä expansion](https://nebius.com/newsroom/nebius-to-triple-capacity-at-finland-data-center-to-75-mw); [GB300 deployment](https://nebius.com/blog/posts/first-live-nvidia-gb300-nvl72-deployment-in-europe); [planned Lappeenranta facility](https://nebius.com/newsroom/nebius-to-construct-310-mw-ai-factory-in-finland); [planned Independence campus](https://nebius.com/newsroom/nebius-secures-approval-for-its-first-gigawatt-scale-ai-factory).
- [Nebius AI Cloud changelog](https://docs.nebius.com/changelog) — prices, capacity, and service features change over time.
- [Nebius Solutions Library inference fleet](https://github.com/nebius/nebius-solutions-library/tree/main/k8s-inference) and [Soperator repository](https://github.com/nebius/soperator) — customer-operated reference implementations, not Token Factory's internal architecture.
- [DataRobot validated AI Factory](https://nebius.com/blog/posts/datarobot-validated-ai-factory-stack) and [partner technical analysis](https://www.datarobot.com/blog/datarobot-nebius-enterprise-ai-factory-optimized-for-agents/) — partner-specific reference architecture and benchmark claims; configuration-specific, not universal service performance.
- Generic sources: *AI Factory: Building Large-Scale Production Systems*, Volume 21, Chapter 1; *GPU Compute Cluster Design*, Volume 21, Chapter 2; *AI Data Center Network Design and Technologies*, Chapters 2, 3, and 5; *Why AI Storage Is Different*, Volume 15, Chapter 1.

**Explicit inferences:** customer product selection, GPU sizing, VPC topology, checkpoint frequency, cost controls, and recovery targets unless specified by a live account or contract.

**Not verified:** current account capacity, live GPU reservation availability, site-level facility telemetry, customer-specific prices, and the complete internal Token Factory fleet topology.
