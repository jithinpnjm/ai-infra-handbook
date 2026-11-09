---
id: "c20-30"
title: "20.30 From AI factory to Token Factory: a public architecture map"
sidebar_label: "20.30 AI factory architecture map"
sidebar_position: 30
description: "Trace Nebius's public AI Cloud and Token Factory surfaces from cloud resources to the inference API, billing, caching and recovery limits, and learn where the public evidence stops."
status: "drafted"
tier: "1"
level: "I"
lab_venue: "Laptop / browser"
---

# 20.30 From AI factory to Token Factory: a public architecture map

The interviewer says, "Walk me from GPU capacity to a Token Factory response." You know serving basics, but you now have to reason inward from the cloud boundary. If you draw a gateway, a router and a Kubernetes cluster and call it Nebius's architecture, you have claimed more than Nebius has published.

This chapter maps what a customer can see. It separates three kinds of evidence. Product documentation is tagged [official]. Nebius blog posts and case studies are tagged [vendor]. Your own design reasoning is tagged [inference]. Where Nebius has not published something, the chapter says so and stops.

The chapter is the entry point to the architecture chapters that follow it. Chapter 20.31 covers the AI Cloud substrate, 20.32 the Token Factory lifecycle and economics, and 20.33 customer patterns and recovery. Depth on gateways, estimation and failure modes lives in 20.12, 20.13 and 20.18. This chapter links to them instead of repeating them.

## What the interviewer is testing

This chapter serves the system-design round and the incident round. The plan records the official wording for system design as meeting load and availability targets, estimating performance and compute, and weighing data storage and processing trade-offs. The job posting adds routing, GPU autoscaling, observability and SLOs. The plan also marks autoscaling signals, the router algorithm and probe settings as not public. So the interviewer is checking your reasoning, not your recall of Nebius internals.

A realistic prompt: "Walk me from GPU capacity to a Token Factory response. What is managed, how is it billed, and what happens when capacity disappears?" A strong answer names the product boundary first, follows the public API, states the capacity caveats, and says plainly where the documentation ends.

## The core ideas

### 1. Draw the product boundary before the boxes [official]

Picture a platform team choosing between running its own GPU service and calling a managed model API. The hardware may look the same. The operating boundary is very different.

Nebius AI Cloud is the broad cloud. Its service list covers compute, storage, virtual networks, identity, Kubernetes, monitoring, logging and more. Token Factory is a managed inference service with its own organization and project model, endpoints, API keys, metrics and billing pages. The two have separate documentation sites and separate credentials.

The word serverless appears in both. Serverless AI in AI Cloud runs your own containers as Devlabs, endpoints or jobs on Compute virtual machines, billed per second. Token Factory Public Serverless is a shared catalogue of Nebius-hosted models behind one API. In the first you deploy your application. In the second you only call a model.

With your own Managed Kubernetes you choose node groups, deploy the engine, run the gateway and own the cluster operations. With a Token Factory Dedicated Endpoint you pick a template, region, GPU type, GPUs per replica and a replica range. Nebius runs the service infrastructure and you get no Kubernetes control surface.

```mermaid
flowchart LR
  Client["Client app"] -->|"API key and request"| DataPlane["Regional data-plane URL"]
  Client -->|"manage endpoint"| Control["Control plane API"]
  Control -->|"returns endpoint_id and routing_key"| Client
  DataPlane --> Shared["Public Serverless pool"]
  DataPlane --> Dedicated["Dedicated Endpoint"]
  Shared --> Runtime["Model runtime: internals not public"]
  Dedicated --> Runtime
  Runtime --> Stream["Token stream"]
  Dedicated --> Metrics["Dedicated-only metrics"]
  DataPlane -.-> Billing["Usage and billing views: meter design not public"]
  subgraph Cloud["AI Cloud resources a customer can build"]
    Tenant["Tenant and IAM"] --> Proj["Project"]
    Proj --> Net["VPC and subnet"]
    Proj --> GPU["GPU VMs and clusters"]
    Proj --> K8s["Managed Kubernetes"]
    Proj --> Store["Disks, filesystems, objects"]
  end
```

The diagram shows the customer-visible surfaces only. Nebius's product blog says Dedicated Endpoints run on Nebius AI Cloud, on dedicated NVIDIA GPU clusters in data centers Nebius owns and operates across Europe and the US [vendor]. It does not say how an endpoint maps to cloud resources, so the diagram draws no such link.

**Start every architecture answer by saying which side of the managed-service boundary you are describing.**

### 2. Know the AI Cloud building blocks [official]

A data scientist asks for an endpoint, and you must decide whether to build or buy. The table gives the short version. Each service has its own limits, regions and prices.

| Choice | Nebius manages | Your team owns | Fits when |
|---|---|---|---|
| GPU VMs and GPU clusters | Physical capacity, VM provisioning, InfiniBand fabric | OS, drivers, runtime, serving, repair policy | You need host control |
| Managed Kubernetes | Control plane and cluster operations | Workloads, node groups, operators, app reliability | You need custom serving on containers |
| Managed Soperator | Slurm-based clusters for distributed training | Jobs, images, data, job-level recovery | You need Slurm workflows |
| Serverless AI | Runs your container, per-second billing | The container, model server and request contract | You want a custom container without a cluster |
| Token Factory Public Serverless | Shared model catalogue and API | Client, prompts, application policy | Testing or tolerant workloads |
| Token Factory Dedicated Endpoint | Endpoint deployment and replicas | Template, region, GPU and replica settings, keys, SLOs | Stable model endpoint with explicit hardware |

Compute offers GPU VMs and InfiniBand-connected GPU clusters. The topology guide describes three layers: the InfiniBand fabric, the point of delivery, and the scalable unit. It reports NCCL AllReduce gains of up to 20 percent from topology-aware placement, depending on cluster size, in NCCL Tests runs. That is test evidence, not a guarantee for your job.

Storage choices follow recovery needs. Network SSD tolerates up to two concurrent hardware failures. Non-replicated disks have no redundancy. Local SSD is erased when the VM stops or is deleted. A shared filesystem can attach to many VMs at once.

Virtual Networks supports only IPv4 today. Each project gets a default network, subnet, pools, route table and DNS zone. Security groups act as a stateful or stateless firewall for VMs, and unmatched traffic is denied. You cannot change network resources while active workloads are attached, so plan address ranges before you start.

In the service list, Monitoring and Logging are marked Preview, described as intended for testing and feedback. Check their status before you depend on them.

**Use the cloud catalogue to explain the build-your-own path, never to guess Token Factory internals.**

### 3. Follow identity, project and billing boundaries [official]

A customer says "my key does not work" or "the bill is wrong." Before you debug anything, ask which product they mean, because identity and billing are separate in the two products.

In AI Cloud, a tenant is the top container. It holds projects, users, groups, quotas and billing settings. Being a tenant member grants no resource access. Access comes from group membership, and the default groups run from auditors and viewers to editors and admins. Service accounts authenticate with access keys or authorized keys.

Token Factory has its own organization and project hierarchy. A project holds API keys, dedicated endpoints, fine-tuning jobs, files and datasets. Its group page defines four roles. The Organization Admin has full access to settings, billing and all projects. The Organization Billing Manager manages billing and sees usage but has no access to project resources. The Project Admin controls project resources and creates and deletes API keys. The Project Member has full access to the Files, Fine-tuning, Batch, Dedicated Endpoints and Public Endpoints APIs and can create and delete only their own keys.

So you can give finance cost visibility without handing over inference keys. Do not assume a Token Factory API key is an AI Cloud IAM token, or that a cloud service account can authorize inference. The documents show them as separate systems [inference: no page says they never interact].

Billing is separate too. Token Factory billing has a balance, top-ups, card thresholds, monthly invoices for bank-transfer customers and a Usage tab you can filter by region, project, service and product. A failed card charge suspends the account, so payment setup is part of production readiness. AI Cloud billing is pay-as-you-go by default, with commitment discounts for eligible company accounts. The two models can be combined.

AI Cloud budgets only send alerts. The budget page says a budget does not stop or cap usage and that usage data updates every few hours. To actually limit usage, the page points to a quota decrease. Separately, capacity block groups reserve a number of GPUs on one platform in one region, on one InfiniBand fabric, for VMs or Kubernetes node groups. They are not project quotas and not the Token Factory `max_replicas` setting.

**Identify the product, project, credential and usage surface before you diagnose an access or billing complaint.**

### 4. Trace one request through the documented API [official]

A developer has just created a dedicated endpoint. Which identifier goes in the inference call? The control plane returns two values, and knowing which is which removes most of the mystery.

The deploy guide describes three steps. List the model templates, create the dedicated endpoint, then send inference requests. The template response is the source of truth for valid combinations of model, flavor, GPU type, GPU count and region. The create response carries an `endpoint_id` and a `routing_key`. The `endpoint_id` manages the endpoint through the control plane. The `routing_key` goes in the `model` field of OpenAI-compatible inference requests.

The control plane has one base URL, `https://api.tokenfactory.nebius.com`. The data plane URL depends on the endpoint region. The control and data plane page maps `eu-north1` to the same hostname as the control plane, `eu-west1` to `api.tokenfactory.eu-west1.nebius.com`, and `us-central1` to `api.tokenfactory.us-central1.nebius.com`. The deploy guide's own example creates an `eu-north1` endpoint but shows a `us-central1` inference URL, so match the URL to the region you actually chose.

During provisioning, inference may fail, often with 404, until the endpoint is routable. The FAQ gives the status code meanings in the table below.

| Code | FAQ cause | First action |
|---|---|---|
| 401 | Missing or invalid token | Set the `Authorization: Bearer` header, check the token is active |
| 403 | Token lacks permission | Use a token with dedicated endpoint permissions |
| 404 | Not ready, wrong inference domain, or wrong `routing_key` | Wait for readiness, use the region URL, pass the key exactly |
| 409 | Capacity or config conflict | Pick a supported GPU and region, or reduce max replicas |
| 422 | Invalid payload values | Check fields against the templates |

Classify the code before you blame the model server. The docs do not describe the gateway, the credential path, how control state reaches the data plane, or how a replica is chosen behind the routing key. Say that out loud when asked. A design guess about those parts is [inference] and must be labelled that way.

**Explain the path from API key to regional data plane, then stop where the docs stop.**

### 5. Compare shared and dedicated inference as capacity products [official]

A team starts with experiments and then gets a production commitment with a latency target. The product that suited the first stage may not suit the second.

Public Serverless is shared multi-tenant capacity with dynamic rate limits and per-token prices. The legal guide says the Region field for public model endpoints shows Global, that the processing location can change without notice, and that these endpoints are intended for testing and non-critical workloads. It also says they are not meant for use cases that need a stable, predictable region.

The public rate limits are dynamic. The rate-limits page says a limit rises by 20 percent per 15-minute window when average usage stays at or above 80 percent of it. It falls by a third when usage stays at or below 50 percent. Responses carry `x-ratelimit-*` headers and a `Retry-After` header in seconds.

Dedicated Endpoints bind a deployment to a region you choose, with GPU type, GPUs per replica and a replica range. Pricing is per GPU-hour, billed per minute. The overview says there are no standard rate limits and that throughput depends on deployed capacity. The legal guide says the region is fixed and that Nebius does not use automatic overflow or failover to other regions. An EU endpoint therefore cannot spill into the US when EU capacity is short.

Shared does not mean every model stays available. The November 9, 2026 notice lists eleven model IDs removed from Token Factory Serverless on that date and says Dedicated Endpoints for those models are unaffected. Check the live catalogue before you recommend a model.

A dedicated endpoint is not pay-per-token. Cost follows GPUs and time. More GPUs per replica can fit a larger model or speed one replica but raise the baseline. More replicas add traffic capacity but also add billed capacity. Minimum replicas set the baseline. Maximum replicas cap scale-out and are not a promise that GPUs exist. The total ceiling is `gpu_count × max_replicas`.

**Choose shared inference only after checking model availability and limits, and choose dedicated capacity when its controls justify the baseline cost.**

### 6. Read lifecycle and readiness as two separate states [official]

A customer sees an endpoint marked running and sends production traffic, and some requests fail. The lifecycle label and the ability to serve are different facts.

The lifecycle guide lists six lifecycle states: Starting, Updating, Running, Warning, Stopping and Stopped. It lists three readiness states: Not ready, Partially ready and Ready. The page's table writes the Warning state as Error, which is an inconsistency in the source. Send traffic based on readiness, not on the lifecycle label or on a successful control-plane response.

| Lifecycle | Readiness | Meaning per the guide |
|---|---|---|
| Starting | Not ready | Provisioning in progress |
| Starting | Partially ready | Serving traffic while scaling up |
| Updating | Ready | Serving normally during an update |
| Running | Ready | Fully operational |
| Running | Partially ready | Reduced capacity |
| Running | Not ready | Unexpected outage |
| Warning | Ready | Serving, but a deployment issue exists |
| Warning | Not ready | Deployment failure |
| Stopping | Partially ready | Shutting down |
| Stopped | Not ready | Fully stopped |

The guide says to contact support if a warning or partially ready state is unresolved for more than 3 hours. That is a support threshold, not a recovery objective for your application.

The operating guide says `gpu_count` is per replica and that `region` cannot be updated after creation. Moving region means creating a new endpoint and cutting over traffic and data yourself. Setting `enabled` to false stops the endpoint and frees its replicas. Custom model weights are described as beta and available on request, through support.

The create-endpoint OpenAPI schema also has an optional `reservation_policy` object. Its `policy` field takes AUTO, FORBID or STRICT, and `reservation_ids` is an optional list. The capacity guide does not explain which reservations qualify or what guarantee follows. Confirm that with Nebius before you assume anything. Canarying and draining an endpoint rollout are your own design choices [inference], unless a current page documents them.

**Judge an update by serving capacity, not by a successful control-plane response.**

### 7. Separate serving concepts from serving implementation [official, vendor]

An architect must decide whether to serve a catalogue model, adapt one, or run a custom runtime. Token Factory lists text-to-text, embedding and vision model families behind an OpenAI-compatible API. Its Data Lab holds automatically collected chat completions unless Zero Data Retention is on, plus reusable datasets and batch and fine-tuning outputs. Post-training covers long-context supervised fine-tuning on full weights or LoRA adapters, and custom speculator training.

The legal guide is architecture input. By default, inputs and outputs are kept to speed up inference through speculative decoding and are stored in Finland. They are not used to train models. Zero Data Retention applies to the whole organization, stops that retention and may reduce service performance, for example inference speed. Fine-tuning datasets, artifacts and outputs are stored in EU data centers even when a US customer's job runs in the US. Draw inference data, training data and telemetry as three flows and check each against the current terms.

The inference overview lists KV cache, paged attention, flash attention, quantization, continuous batching, context caching and speculative decoding. The base and fast flavors give identical outputs. They differ in price, latency and applied optimizations, and fast uses smaller batches, more compute and techniques such as speculative decoding. These are documented capabilities. They do not name the engine or the scheduling policy.

Prefill, decode, batching and KV memory are covered in chapters 20.13 and 20.18. A Nebius chat-app case study describes a proof of concept with prefill-specialized and decode-specialized workers and backpressure controls [vendor]. It is one design exercise, not Token Factory's topology.

**Learn the serving physics and name an engine or topology only when a source does.**

### 8. Treat cache-aware routing as a published example [official, vendor]

An agent sends a chain of requests that reuse a long context. If they land on different replicas, each may repeat the prefill work. That turns a runtime detail into a routing and cost question.

The Cached Tokens guide says prefix caching is automatic and best-effort, with no SLA on hits. The caller does not set a cache key. Chat responses report the count in `prompt_tokens_details.cached_tokens`. Streaming clients must set `stream_options.include_usage` to receive usage. On Serverless, cached input is billed at a per-model cached input price. Dedicated Endpoints bill per GPU hour, so hits change speed and latency but not the bill.

Scope matters for security. On Serverless the cache is shared within a model, regardless of organization, project or API key. On Dedicated Endpoints each customer has an isolated cache. The guide says caching is not an access-control boundary, so never put secrets at the start of a prompt expecting isolation. The `prompt_cache_key` only helps routing to the cache holder and is not a credential. A hit can fail through eviction, routing to another replica or a model or service update.

Nebius's routing experiment ran 300 concurrent agent trajectories on one or three vLLM replicas [vendor]. Default Kubernetes ClusterIP routing ignored request content. The cache-aware router picked the replica with the best KV match and fell back when it was overloaded. Average step time fell from 9.0 s to 4.8 s, and p95 fell from 70.8 s to 17 s. The post states that no standalone least-request baseline was evaluated, and that memory pressure and eviction signals were not tested. It is one experiment, not a product guarantee.

A cache-only router can overload one replica. A sensible customer-side design weighs prefix locality against queue depth and avoids unhealthy workers [inference]. Chapter 20.21 covers routing and retries in depth.

**Treat cache locality as a performance signal, not permission to send everything to one replica.**

### 9. Read telemetry and the bill as separate views [official]

A dashboard shows low GPU utilization while the customer says the endpoint is slow. Another shows high token throughput and says nothing about the target. You must know which view answers which question.

Token Factory inference observability says its metrics are only accessible for Dedicated Endpoints. The page lists requests per minute, input and output tokens per minute, input and output tokens per request, KV-cache hit rate, end-to-end latency, time to first token for streaming requests, output speed, active replicas and GPUs, average and busiest GPU utilization, and error rate by status code. Latency charts show p50, p90 and p99. Filters cover time range, endpoint, project, API key, region, error code, prompt length and latency range. Some capacity metrics may be hidden depending on the pricing model.

Metrics are collected where inference runs and ultimately stored in `eu-north`. The Prometheus and Grafana integration page uses a static API key issued in the Token Factory UI. Its path includes your project ID, and it recommends a scrape interval of no less than 15 seconds. A residency review should treat metrics location separately from endpoint region. The page also says the dashboards are for debugging and performance analysis, not billing reconciliation.

For public serverless, do not assume this dashboard exists. AI Cloud has its own Monitoring and Logging services, which are separate products and still marked Preview.

For billing, Public Serverless is metered per token, with a cached input price where one exists. Dedicated Endpoints are billed per GPU time. The billing policy says zero running replicas means inaccessible and not billed, and one or more running replicas means available and billed. Its state table says provisioning, not ready, partially ready, replica restarts and graceful shutdown are not billed, and capacity in a ready status is billed. Those two readings can differ for a partially ready endpoint that has a running replica, so confirm that case with support or your contract rather than infer an invoice from status.

Chapters 20.13 and 20.19 cover gateway SLIs and burn-rate alerts. **Use inference metrics to operate the endpoint and the billing surface to reconcile charges.**

### 10. Treat high availability as a capacity and ownership question [official, vendor]

A minimum replica count can look like a recovery guarantee until the endpoint is interrupted and its GPUs return to the shared pool.

The capacity guide says minimum replicas are reserved and non-preemptible while the endpoint is running. When it stops, because you stopped it, an incident interrupted it or maintenance stopped it, the GPUs are released back to the shared pool. On restart it requests capacity again. It may stay in Starting and Not ready, or reach only Partially ready, until enough capacity is available. Self-service endpoints have no formal SLA unless covered by contract. For guarantees across restarts and maintenance, the docs tell you to contact Sales.

The chat-app case study says critical endpoints run with X+1 redundancy and that dedicated endpoints run with a 99.9 percent SLA [vendor]. That conflicts with the capacity guide for self-service endpoints. Treat the blog as marketing for a contract tier and the documentation as the self-service rule.

Managed Kubernetes has its own documented repair path, which is not Token Factory's hidden machinery. The control plane defaults to three etcd stores. The cluster autoscaler adds nodes for unschedulable Pods and removes underused ones. A CPU node group lets CoreDNS and Cilium keep running while the GPU group scales down. For a faulty GPU node, health checks cordon it, wait for GPU workloads to finish, drain it for up to one hour, then stop and start the VM so the node moves to a healthy VM.

Alert on readiness and active capacity. Set baseline replicas from measured demand and settle contractual capacity before you promise recovery [inference].

**A configured replica count is not an availability contract, so name the capacity promise and its failure boundary.**

### 11. Plan recovery without inventing automatic failover [official, inference]

Public Serverless has a Global location that can change. Dedicated Endpoints stay in their chosen region, with no multi-region routing and no automatic overflow, and the region cannot be changed later.

For application-level failover, build and test a second endpoint, confirm the data may legally move there, and check model version, weights, keys, capacity and rollback. Without that, define a degraded mode and an escalation path [inference]. Use bounded retries with jitter and do not replay a partial stream unless the protocol can resume. Chapters 20.21 and 20.26 cover the method.

| Failure | Documented behaviour | Safe first response | Do not assume |
|---|---|---|---|
| 429 on public endpoints | Rate limit exceeded, headers and `Retry-After` available | Read headers, smooth demand | Every 429 has the same delay |
| Endpoint still provisioning | Readiness state, early 404 possible | Wait on readiness, avoid retry storms | Created means routable |
| Partial readiness | Reduced capacity | Check active replicas and latency | Running means full capacity |
| Stopped by incident or maintenance | GPUs released to shared pool | Check state, contact support, run your plan | Old GPUs return automatically |
| Region unavailable | Dedicated stays in region | Follow the approved residency policy | Provider overflows elsewhere |
| Budget alert crossed | Alert only, data lags hours | Find the project and resource, apply a quota | The alert stopped charges |

**Fail over only to a tested destination that may receive the data and has usable capacity.**

### 12. Keep a reference design ready [inference]

The interviewer asks, "What would you propose for a company launching an AI product on Nebius?" Start with discovery, not a diagram. Ask whether the work is training or serving, the model size, request and token rates, context lengths, streaming needs, latency targets, peak-to-average ratio, retention rules, regions, recovery target and budget.

Then pick the operating boundary. For variable experiments with a standard model, Public Serverless is quickest if the global location and dynamic limits are acceptable. For a production model that needs a fixed region and hardware, propose a Dedicated Endpoint and design around its region, billing states and lack of provider failover. For a custom container, compare Serverless AI with Managed Kubernetes. For distributed training, consider Soperator or GPU VMs on an InfiniBand cluster.

Build the foundation around the choice: tenant and project separation, group roles, quotas, key handling, network design, storage, a registry and cost allocation. Put your own gateway in front only when you need product-specific auth, quotas or routing, and never present it as a Nebius component. Finish with operations: user-facing SLOs, readiness, cache and token metrics, budgets, rollback and a residency-approved recovery plan.

**Name one owner for each layer and one signal that tells that owner to act.**

## How to answer out loud

**Question 1. "How does Token Factory work?"** Open with the boundary, then the public API, then the limit of the evidence. A model answer:

> "I'd separate AI Cloud from Token Factory. AI Cloud gives customers GPU compute, networks, storage, Kubernetes and IAM. Token Factory is a managed inference service with its own organizations and projects. For a dedicated endpoint, you pick a template, region, GPU shape and replica range, and call a regional OpenAI-compatible URL with the routing key. The docs show lifecycle, readiness, metrics and billing. They do not show the gateway or router internals, so beyond that I'd be proposing a design, not describing Nebius."

**Question 2. "How does a request find its deployment?"** The control plane returns an endpoint ID and a routing key. The client sends the key as the model name to the regional `/v1` URL. Then say the gateway and router are not documented. Expect a follow-up on 404 versus 409.

**Question 3. "What does high availability mean here?"** Minimum replicas are reserved while the endpoint is running, not after it stops. Self-service has no SLA. Offer reserved capacity through Sales, plus a tested, residency-approved fallback as your own design.

**Question 4. "How is it billed?"** Public Serverless per token. Dedicated per GPU-hour billed per minute, and cache hits do not change that bill. Utilization charts and budgets are not a ledger. Expect a follow-up on partially ready billing, and say you would confirm it with support.

**Question 5. "Why can more replicas make things worse?"** Related requests may lose cache locality. Nebius's experiment showed cache-aware routing helping on one workload, but it did not test a least-request baseline. Propose weighing locality against load as your own design.

## Worked scenarios

### Scenario 1: A request fails just after endpoint creation

A developer lists templates, creates an endpoint and receives an `endpoint_id` and `routing_key`. The first chat call returns 404 and the instinct is to raise client retries.

Check lifecycle and readiness first. The deploy guide says early failures, often 404, are expected until the endpoint is routable. If it is ready, check the bearer token, the exact `routing_key` and the region URL, as the FAQ lists. Do not diagnose an internal router fault from an early request.

### Scenario 2: Three replicas do worse than one

An agent reuses context across sequential requests. After scaling vLLM from one to three replicas, p95 gets worse. Nebius's experiment found that default ClusterIP routing scattered related requests and that cache-aware routing recovered the loss.

Measure prompt length, per-replica queue depth, cache hit rate, TTFT and tail latency. Propose a bounded cache-aware policy with a load fallback as your design. Say clearly that this is not Nebius's published router.

### Scenario 3: Recovery after capacity is released

A dedicated endpoint is interrupted by maintenance. It shows Starting and Partially ready, and the old replica count is not back. Product asks to send traffic to another region.

The capacity guide says GPUs were released to the shared pool and a restart requests capacity again. Do not promise the same GPUs or a recovery time. Before failover, verify that the data may move, that the model and config match, and that the other region has warm capacity. If no tested alternative exists, use the degraded mode, bound the work, communicate impact and ask Sales about reserved capacity.

## Hands-on lab

This lab needs no Nebius account and spends no money. It checks that you can separate product facts from your own proposal. I did not run any of it against a live endpoint.

1. Open the dedicated-endpoint deploy guide. Write the sequence: list templates, create endpoint, receive `endpoint_id` and `routing_key`, call the regional `/v1` API. Expected result: you can say which value manages the endpoint and which selects it for inference.
2. Draw the AI Cloud resource plane separately from Token Factory. Label tenant, project, identity, compute, storage, control plane, data plane, metrics and billing. Expected result: nothing implies that customer-managed Kubernetes is Token Factory's implementation.
3. Build a three-column evidence sheet: documented, case-study only, unpublished. Expected result: lifecycle and readiness land in the first column, the cache-routing measurements in the second, and the router algorithm in the third.
4. Add a recovery row for a stopped endpoint with released capacity, restart behaviour and the questions for Sales. Expected result: the plan never promises the old GPUs return.
5. Say the opening answer aloud in 90 seconds and ask a partner to interrupt with "How does the internal router work?" Expected result: you separate evidence from inference without losing the thread.

## Drill questions

<details><summary>1. What is the difference between Nebius AI Cloud and Token Factory?</summary>
AI Cloud is the broad cloud of VMs, networks, storage, Kubernetes and IAM. Token Factory is a managed inference service with its own organizations, projects, endpoints, metrics and billing. Do not assume Token Factory exposes its internal cloud resources.
</details>

<details><summary>2. What are the endpoint ID and the routing key for?</summary>
The endpoint ID manages the deployment through the control plane. The routing key goes in the model field of requests to the regional data plane.
</details>

<details><summary>3. Why are lifecycle and readiness separate?</summary>
Lifecycle says what the deployment is doing. Readiness says whether it can serve now. A running endpoint can be partially ready or not ready.
</details>

<details><summary>4. What does a maximum replica count guarantee?</summary>
Only a ceiling on scale-out. It does not guarantee that GPUs will be available. The total possible footprint is gpu_count times max_replicas.
</details>

<details><summary>5. What do minimum replicas guarantee after an endpoint stops?</summary>
Nothing. Minimum replicas are reserved while the endpoint runs. After a stop, the GPUs go back to the shared pool, and a restart requests capacity again.
</details>

<details><summary>6. How strong is the evidence for cache-aware routing at Nebius?</summary>
It is one vLLM experiment with 300 concurrent agent trajectories, plus a case-study blueprint. Both are vendor evidence for specific workloads. The experiment did not test a least-request baseline, and neither is a product contract.
</details>

<details><summary>7. Why is Token Factory observability not a billing ledger?</summary>
The page says the dashboards are for operational debugging and performance analysis, not billing reconciliation. Use the Usage tab and billing pages for charges.
</details>

<details><summary>8. What happens to a self-service endpoint's GPUs after a stop or incident?</summary>
They are released to the shared pool. On restart the endpoint asks for capacity again. It may stay in Starting or only reach Partially ready until capacity is available.
</details>

<details><summary>9. Does the public documentation promise cross-region failover for dedicated endpoints?</summary>
No. The legal guide says the region is fixed and there is no multi-region routing or automatic overflow. Failover is a customer design that needs a tested second endpoint and a data-residency check.
</details>

<details><summary>10. How do you answer a question about the unpublished internal gateway?</summary>
State what the public API shows, say the internal implementation is not published, then offer your own design clearly labelled as a proposal.
</details>

## Common mistakes and weak answers

- Calling the customer-visible AI Cloud resource map the internal Token Factory topology. Say instead what the docs show and where they stop.
- Mixing up Token Factory API keys with AI Cloud IAM credentials. Name the product first.
- Presenting a cache-routing case study as a feature every endpoint has.
- Treating a maximum replica count as reserved capacity, or a running endpoint as fully ready.
- Reading billing from a GPU utilization chart, or treating a budget as a spending cap.
- Promising cross-region failover, an SLA or the return of old GPUs with no source or contract.

## Connections to the rest of the handbook

- [20.12 Estimation toolkit for inference capacity](./12-estimation-toolkit-for-inference-capacity.md) turns traffic and model shape into GPU and cost estimates.
- [20.13 Design a multi-tenant LLM inference API](./13-design-a-multi-tenant-llm-inference-api.md) covers the gateway, router, quotas and failure policy.
- [20.14 Dedicated endpoints and safe model rollout](./14-design-dedicated-endpoints-and-safe-model-rollout.md) covers rollout design.
- [20.15 Observability pipeline design](./15-design-an-observability-pipeline-for-very-high-volume.md) and [20.16 GPU fleet health and capacity](./16-design-gpu-fleet-health-and-capacity.md) cover telemetry and fleet capacity.
- [20.18 How LLM serving fails](./18-how-llm-serving-fails.md) covers queue, cache and runtime failures.
- [20.19 SLIs, SLOs and alerts for token APIs](./19-slis-slos-and-alerts-for-token-apis.md) covers user-facing signals and paging.
- [20.20 Autoscaling GPU inference](./20-autoscaling-gpu-inference.md) and [20.21 Routing, retries and overload control](./21-request-routing-retries-and-overload-control.md) cover scaling and retries.
- [20.26 The stress interview](./26-the-stress-interview-production-incident-role-play.md) covers incident role-play.
- [20.31](./31-nebius-ai-cloud-foundation-gpu-fabric-and-platform-choices.md), [20.32](./32-token-factory-model-lifecycle-serving-and-economics.md) and [20.33](./33-ai-factory-solution-architecture-ha-and-recovery.md) continue this architecture series.

## Sources and review notes

All Nebius pages below were fetched on 2026-11-09. Prices, templates and status change, so recheck before quoting.

- Token Factory docs: [deploy API](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/deploy-api), [control and data planes](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/control-data-plane), [FAQ](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/faq), [overview](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/overview), [lifecycle and status](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/lifecycle-and-status), [operating](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/operating), [capacity and scaling](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/capacity-and-scaling), [billing policy](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/billing-policy), [custom weights](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/custom-weights), [create endpoint OpenAPI](https://docs.tokenfactory.nebius.com/api-reference/dedicated-endpoints/create-dedicated-endpoint).
- Token Factory models, data and operations: [inference overview](https://docs.tokenfactory.nebius.com/ai-models-inference/overview), [cached tokens](https://docs.tokenfactory.nebius.com/cached-tokens), [rate limits](https://docs.tokenfactory.nebius.com/ai-models-inference/rate-limits), [observability](https://docs.tokenfactory.nebius.com/ai-models-inference/observability), [Prometheus and Grafana](https://docs.tokenfactory.nebius.com/ai-models-inference/observability-api-integrations), [legal quick guide](https://docs.tokenfactory.nebius.com/legal/legal-quick-guide), [Data Lab](https://docs.tokenfactory.nebius.com/data-lab/overview), [post-training](https://docs.tokenfactory.nebius.com/post-training/overview), [billing](https://docs.tokenfactory.nebius.com/other-capabilities/billing-new), [November 2026 deprecations](https://docs.tokenfactory.nebius.com/november-2026-deprecation-notice), [organizations and projects](https://docs.tokenfactory.nebius.com/team-access/org-projects), [groups and roles](https://docs.tokenfactory.nebius.com/team-access/groups). Index checked: [llms.txt](https://docs.tokenfactory.nebius.com/llms.txt).
- AI Cloud docs: [services](https://docs.nebius.com/overview/services), [IAM](https://docs.nebius.com/iam/overview), [budgets](https://docs.nebius.com/signup-billing/budgets), [billing models](https://docs.nebius.com/signup-billing/billing-models/overview), [capacity block groups](https://docs.nebius.com/overview/limits/capacity-block-groups), [GPU topology](https://docs.nebius.com/compute/clusters/gpu/topology/index), [storage types](https://docs.nebius.com/compute/storage/types), [VPC](https://docs.nebius.com/vpc/overview), [security groups](https://docs.nebius.com/vpc/security-groups), [Kubernetes components](https://docs.nebius.com/kubernetes/components), [node-group autoscaling](https://docs.nebius.com/kubernetes/node-groups/autoscaling), [GPU health checks](https://docs.nebius.com/kubernetes/maintenance/health-checks), [Serverless AI](https://docs.nebius.com/serverless/overview).
- Vendor posts [vendor]: [Dedicated Endpoints and Custom Weights Hub](https://nebius.com/blog/posts/dedicated-endpoints-and-custom-weights-hub), [routing experiment](https://nebius.com/blog/posts/routing-is-the-difference-between-scaling-and-stalling), [chat-app architecture proof of concept](https://nebius.com/blog/posts/the-invisible-architecture-behind-great-chat-apps).
- Planning: `planning/VOLUME_20_NEBIUS_SRE_PLAN.md` section 1 for the official interview wording and the list of non-public items.
- Books: *Scalable Kubernetes Infrastructure for AI Platforms*, Chapter 4 "Model Deployment and Monitoring" was cited by the original draft for generic serving vocabulary. *Hands-On LLM Serving and Optimization* and *AI Systems Performance Engineering* Chapter 18 were also cited by the original draft. I did not re-read them in this pass, and no claim in this chapter depends on them.

**Explicitly labelled inferences:** that the two credential systems do not interact, customer gateways, application-level failover, cache and load balancing policy, retry rules, canary and drain procedures, warm capacity, and recovery targets.

**Not verified:** the gateway, router and Kubernetes topology behind Token Factory, autoscaling signals, the billing-meter pipeline, which reservations satisfy `reservation_policy`, how a partially ready endpoint with a running replica is billed, and any live behaviour. I created no endpoint and called no billable API.

### Verification log

About 64 claims and 40 URLs were checked on 2026-11-09, and none was unreachable. Roughly 47 claims were confirmed. About 11 were corrected, and 6 were removed or relabelled as inference. Notable corrections:

- The lifecycle table now includes Warning and Stopping and shows the Warning versus Error inconsistency in the source.
- The "testing and non-critical" wording comes from the legal guide, not the endpoint overview.
- `reservation_policy` is in the OpenAPI schema, not the operating guide.
- Role definitions come from the groups page. The Project Member row was corrected.
- The Prometheus key being project-scoped was not supported and was removed.
- The scrape-interval advice and the `eu-north` storage claim were each attributed to the correct page.
- GPU health checks stop and start the VM, and the docs do not describe a replace step.
- The claim that Token Factory itself runs on those GPU clusters was narrowed to what the blog says about Dedicated Endpoints.
- The invented "several minutes" provisioning time, the claim that some 429s signal capacity errors, and the claim about derived cache storage were removed.
- The 409 meaning was fixed to match the FAQ.
- The routing experiment now quotes the measured numbers.
