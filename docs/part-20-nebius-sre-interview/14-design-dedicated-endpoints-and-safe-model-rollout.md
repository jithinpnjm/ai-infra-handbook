---
id: "c20-14"
title: "20.14 Design: dedicated endpoints and safe model rollout"
sidebar_label: "20.14 Dedicated endpoints and rollout"
sidebar_position: 14
description: "A system design walk-through for dedicated inference endpoints and a custom-weights flow: control plane versus data plane, GPU sizing, weights distribution and cold start, probes, rolling versus blue/green versus canary when GPUs are scarce, quality gates, rollback signals, version skew and scale-to-zero, with a tested rollout simulator."
status: "drafted"
tier: "1"
level: "I"
lab_venue: "Laptop / Docker"
---

# 20.14 Design: dedicated endpoints and safe model rollout

## What the interviewer is testing

The interviewer says: "A customer wants their own endpoint for a fine-tuned model, and next week they want to ship a new checkpoint to it without any downtime. Design it." This chapter serves the system design round. The official wording asks you to design "a whole or partial distributed system" that meets load and availability targets, and to estimate performance and compute. The job posting adds request routing, self-healing systems and Kubernetes autoscaling tuned for GPU efficiency.

Two skills are checked at once. First, can you split an endpoint into a control plane that owns lifecycle and a data plane that serves traffic. Second, can you ship a new model version when you cannot simply double your GPUs. Nebius has not published its rollout design, so the interviewer wants your reasoning and your trade-offs, not recall.

### What is public, and what is my reasoning

Public facts, from the plan's research section, tagged vendor and docs. Token Factory offers serverless and dedicated endpoints with an OpenAI-compatible API and the full vLLM parameter set. The control plane, which handles create, update, enable, disable and delete, is separate from the region-specific data plane. On a dedicated endpoint you pick the GPU type from L40, H100, H200 or B200, the GPUs per replica, the minimum and maximum replicas, and the region in the EU or US. The chat-app case study reports a 99.9 percent SLA on dedicated endpoints and a need for X+1 redundancy.

Nothing else here is public. The plan records no detail on a weights hub, on how a checkpoint reaches an endpoint, on rollout strategy, on probe settings or on scale-to-zero. Wherever this chapter describes those, the text says "a reasonable design is" and it is my reasoning. Say the same in the room.

## The core ideas

### 1. The endpoint as a spec, owned by a control plane

An engineer opens a ticket: "disable the endpoint, the customer is over budget". If that action had to touch the machines serving traffic directly, a bug in billing could stop an API. So the endpoint is stored as a small desired-state record, and something else makes reality match it.

The record carries the model reference, the GPU type, GPUs per replica, minimum and maximum replicas, and the region. The control plane validates it, stores it with an audit trail and exposes the five lifecycle actions. Chapter 20.13 already argued that the data plane must keep serving when the control plane is down, using a cached signed snapshot of desired state. Here we add the lifecycle rules.

```mermaid
flowchart LR
  U["Customer / CLI"] --> CP["Control plane<br/>spec + lifecycle"]
  CP -->|"desired state"| R1["Region EU data plane"]
  CP -->|"desired state"| R2["Region US data plane"]
  R1 --> W1["Replicas<br/>GPU pods"]
  R1 --> RT["Router"]
  T["Client traffic"] --> RT --> W1
  H["Weights hub<br/>(object store)"] -->|"pull"| W1
```

The file `c14_endpoint_lifecycle.py` encodes the rules as a tiny state machine. Create makes the endpoint disabled. Enable and disable flip it. Update is allowed in either state. Delete is allowed only from disabled. That last rule is my design choice, and the reason is that deleting a live endpoint is a one-click outage.

| Action | Allowed from | Result | Why |
|---|---|---|---|
| create | nothing | disabled | validate the spec before any GPU is reserved |
| enable | disabled | enabled | data plane starts replicas |
| disable | enabled | disabled | traffic stops, replicas scale to zero, spec kept |
| update | either | same | spec change, may start a rollout |
| delete | disabled | deleted | forces a deliberate two-step removal |

The validator rejects a GPU type outside the four public choices, a region outside EU and US, fewer than one GPU per replica, and a maximum below the minimum. **Keep desired state in the control plane and let the data plane reconcile toward it, so that a control outage never becomes a traffic outage.**

### 2. Sizing the endpoint: GPU type, GPUs per replica, min and max

A customer asks for a 70 billion parameter model. You need the numbers before you pick hardware. Chapter 20.12 gives the full toolkit, so here is only the shape.

Weights take parameters times bytes per parameter. At FP16 that is 70 x 2 = 140 GB. Hands-On LLM Serving and Optimization, chapter 5, gives this rule. One H100 SXM has 80 GB, according to the NVIDIA H100 page fetched on 2026-11-09, so 140 GB cannot fit on one GPU, and you need at least two for the weights alone. Add KV cache and activation headroom and the honest answer is four, or fewer if you quantise. The GPU memory figure is from the NVIDIA datasheet for the H100, which this chapter did not re-fetch, so check it before you quote it.

GPUs per replica is therefore a memory question first and a latency question second. More GPUs per replica via tensor parallelism cuts latency but costs interconnect traffic and makes each replica a bigger unit to lose and to reload. Replicas count is the capacity and availability question. The minimum is your floor for the SLA. The maximum is your cost ceiling and, as section 6 shows, also your rollout budget.

One more figure matters for rollout. The GPUs the data plane must be able to reserve is not maximum replicas times GPUs per replica. It is that figure plus one extra replica worth of GPUs, because a rolling update needs a surge slot. The function `max_gpus` computes it. With 3 maximum replicas at 4 GPUs each, the ceiling is 16 GPUs, not 12.

**Choose GPUs per replica from memory first, and always budget one extra replica for rollout.**

### 3. Cold start has three costs

A pod is scheduled at 10:00. When can it take traffic? Many people answer "when the process starts", and that is wrong for an LLM engine, because most of the time goes to three stages that run one after another.

The first stage is download, which means moving the weights from the weights hub or object store to the node. The second is load, which means reading them from local disk into GPU memory. The third is compile and warm-up, in which the engine profiles memory, builds optimised kernels or graphs and runs a few real requests so the first user does not pay for them. Chapter 20.18 section 7 covers the load arithmetic and the vLLM settings that cut repeat boots, which are the compile cache under `VLLM_CACHE_ROOT` and reuse of a stored KV-cache memory value.

The script computes the sum. For 140 GB, a 2 GB per second download, a 14 GB per second load, 60 seconds of compile and 30 seconds of warm-up, I ran it and got 70, 10, 60 and 30 seconds, a total of 170. The bandwidth range of 0.5 to 14 GB per second for SSD is from the book's table in chapter 5. The download rate, the compile time and the warm-up time are my illustrative inputs. Measure your own from the startup log.

```python
def cold_start(weights_gb: float, download_gb_s: float, load_gb_s: float,
               compile_s: float, warmup_s: float) -> dict:
    """Seconds from pod scheduled to ready. Stages run one after another."""
    if download_gb_s <= 0 or load_gb_s <= 0:
        raise ValueError("bandwidths must be positive")
    parts = {"download_s": weights_gb / download_gb_s, "load_s": weights_gb / load_gb_s,
             "compile_s": compile_s, "warmup_s": warmup_s}
    parts["total_s"] = sum(parts.values())
    return parts
```

The lesson is which stage to attack. In this example the download dominates, so a node-local weights cache removes 70 of 170 seconds. If the load dominated you would look at disk. If compile dominated you would persist the compile cache. LLMs in Production, chapter 6, describes a design where weights are downloaded once and kept on a mounted volume so new instances skip the download.

**Before you promise a rollout time, split cold start into download, load and compile, and say which one you will remove first.**

### 4. Weights distribution and the custom-weights flow

The customer has trained a checkpoint. They upload it. How does it get to an endpoint safely? Nebius has not published its flow, so here is a reasonable design that follows the usual model-registry pattern. Machine Learning Platform Engineering, chapter 10, lists model versioning with rollback as a basic requirement.

Stage one is the upload into a weights hub, which I treat as a versioned object store with a registry record per model. The record holds an immutable version id, a content hash, the file list, the model architecture, the tokenizer files and the quantisation format. Immutable matters because "the same version" must always mean the same bytes.

Stage two is validation before any GPU is used. Check the hash. Check that the architecture is one the engine supports. Check the config values that bite at runtime, such as maximum sequence length. Load it once on a small canary node and run a fixed prompt set. A checkpoint that fails here never reaches an endpoint.

Stage three is the deploy to an existing endpoint, which is an update action in the control plane. The endpoint spec gains a new model version. The data plane does not edit running pods. It starts a rollout, which sections 6 to 8 describe. The old version stays addressable, so that rollback is the same update with the old id.

```mermaid
flowchart TD
  A["Upload checkpoint"] --> B["Weights hub<br/>immutable version + hash"]
  B --> C{"Validate:<br/>hash, arch, tokenizer"}
  C -->|"fail"| X["Reject, no GPU used"]
  C -->|"pass"| D["Eval on fixed prompts<br/>on a scratch replica"]
  D -->|"fail"| X
  D -->|"pass"| E["Update endpoint spec<br/>to new version"]
  E --> F["Rollout: surge, canary, gates"]
  F -->|"promote"| G["New version serves all"]
  F -->|"rollback"| H["Old version kept"]
```

A design detail that interviewers like is the distribution path. If 8 replicas all download from one bucket at once, they share its bandwidth. Chapter 20.18 section 7 showed the herd arithmetic. A reasonable fix is to stage the new version onto node-local disk before the rollout begins, then start pods that read locally. That moves the long step out of the critical window.

**Treat a checkpoint as an immutable, hashed, validated artifact, and make deploy an ordinary spec update that can be reversed.**

### 5. Readiness versus liveness for an engine

A rollout is only as safe as the signal that says a new pod can take traffic. If readiness lies, the controller removes a good old pod in favour of a broken new one. So you must be exact about the probe roles.

Production Kubernetes, chapter 14, says liveness failures cause restarts, so a liveness probe should be local and should not check external dependencies. Readiness decides whether a pod gets traffic, and it is the place for conditions such as a cold cache or overload. The Kubernetes documentation adds the startup probe, which protects slow-starting containers. It holds off the other probes until it succeeds, with a window of the failure threshold times the period. If the startup probe never succeeds the container is killed.

For an LLM engine that gives a clean split. The startup probe covers the load and compile window, and its length must be at least your measured cold start. Liveness is a cheap local check with generous failure tolerance, because a busy engine answers slowly and a restart throws away both the in-flight requests and a long weight load. Readiness should mean "has loaded, has warmed up and can complete a real one-token request", not "the port is open".

Chapter 20.18 section 6 notes that in vLLM v0.32.0 the health route reports a crash and not a stall, which is my reading of the source. So a green health route is weak evidence for readiness. A reasonable design is a readiness check that runs a real one-token request after warm-up and then keeps passing as long as token rate is sane. The file `c14_engine_deploy.yaml` shows the shape with a startup window of 600 seconds, which comes from a failure threshold of 60 times a period of 10. The probe path `/ready` is a hypothetical one that a sidecar or wrapper would have to provide.

```yaml
# Sketch of a GPU engine Deployment. Probe numbers are starting values, not Nebius settings.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-engine
spec:
  replicas: 8
  minReadySeconds: 30
  progressDeadlineSeconds: 900
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels: {app: demo-engine}
  template:
    metadata:
      labels: {app: demo-engine}
    spec:
      terminationGracePeriodSeconds: 120
      containers:
        - name: engine
          image: example.invalid/engine:v2
          resources:
            limits: {nvidia.com/gpu: 1}
          startupProbe:
            httpGet: {path: /health, port: 8000}
            periodSeconds: 10
            failureThreshold: 60
          readinessProbe:
            httpGet: {path: /ready, port: 8000}
            periodSeconds: 5
            failureThreshold: 2
          livenessProbe:
            httpGet: {path: /health, port: 8000}
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 6
```

The grace period matters for the old pods. On shutdown Kubernetes sends SIGTERM and waits for the grace period, 30 seconds by default, before SIGKILL, as Production Kubernetes chapter 14 explains. A long generation needs time to finish, so raise it and have the engine stop accepting new requests while it drains.

**Make readiness mean "can complete a real request", keep liveness local and tolerant, and size the startup probe to your measured cold start.**

### 6. Rolling, blue/green and canary when you cannot double your GPUs

You have 8 replicas on H100s and the cluster has one spare GPU. The classic advice is blue/green: stand up a full copy, switch traffic, delete the old. For this workload that needs 16 GPUs. The function `blue_green_gpus` returns exactly twice the replicas. If the endpoint is large or the region is short of GPUs, that is simply not available.

Practical MLOps, chapter 4, describes the two patterns. Blue/green gets the new version running in an environment identical to production and routes traffic separately. A canary routes traffic progressively to the new model while the old one still serves, in different ratios, so that checks can catch problems in real time. The book warns that blue/green is hard when the environment is expensive to replicate, and that a canary at 100 percent can still miss a subtle break, which it shows with a boolean that became a string.

| Strategy | Extra GPUs while rolling | Rollback speed | Weak point |
|---|---|---|---|
| Rolling update | the surge amount, for example 1 replica | slow, a reverse rollout | old and new mix on every route |
| Blue/green | a full second fleet, 2x | instant, flip the router | needs double the GPUs |
| Canary | the canary replicas, at least 1 | fast, drop its weight | needs a router with weights and enough traffic |

For scarce GPUs the answer is a hybrid. Use a rolling update with a small surge for the mechanics of replacing pods. Put a canary gate in front by starting with one replica of the new version and a small router weight. Promote only after the gates pass. Chapter 20.13 section 15 described the same order, with an earlier shadow stage.

The Kubernetes documentation defines the rolling update controls. By default both `maxSurge` and `maxUnavailable` are 25 percent. Surge rounds up and unavailable rounds down. The two cannot both be zero. With 8 replicas and 25 percent surge you may run 10 pods, which is two GPUs you may not have. So set the numbers in absolute terms and tie them to your spare GPUs.

The simulator makes the trade-off visible. It models one replica as one GPU slot, a new pod that holds its slot while loading, and the controller loop of scaling down old pods while availability stays above the floor and scaling up new ones within the pod cap. I ran four settings for 8 replicas and a load time of 4 ticks.

| Setting | Spare GPUs | Result |
|---|---|---|
| surge 1, unavailable 0 | 1 | done in 33 ticks, never below 8 available, peak 9 GPUs |
| surge 1, unavailable 0 | 0 | stalls, never finishes, no capacity to start the new pod |
| surge 0, unavailable 1 | 0 | done in 33 ticks, but capacity drops to 7 of 8 |
| surge 2, unavailable 0 | 2 | done in 17 ticks, never below 8, peak 10 GPUs |

The second row is the trap. The Kubernetes documentation says the Deployment controller reports `ProgressDeadlineExceeded` when a rollout makes no progress for the deadline. The pods that cannot be scheduled stay pending and the rollout hangs while the old fleet keeps serving. That is safe for availability and bad for velocity, so alert on it. The third row is the other honest option: accept one replica less during the update, which is fine only if your headroom covers it.

**When GPUs are scarce, trade time against capacity: more surge is faster and needs spare GPUs, and zero surge needs you to accept lower capacity.**

### 7. Surge budgets when GPUs are scarce

An engineer proposes surge of 25 percent, and the capacity planner says "we have one spare GPU in that region". Who wins? The planner, and you should explain why using one formula.

The pod cap in the simulator is the smaller of replicas plus surge and replicas plus spare GPU slots. Surge above the spare count buys nothing, because the extra pods stay pending. Production Kubernetes, chapter 13, describes the same pressure from the cluster side. The Cluster Autoscaler reacts to pending pods, so the cluster is already full when it acts, and node provisioning takes time. Overprovisioning with low-priority placeholder pods keeps standby capacity that real pods can evict. For GPU nodes that standby is costly, so decide on purpose how many spare GPUs you hold for rollouts.

There are three practical levers. First, schedule rollouts to a quiet hour so that headroom is larger. Second, roll in small batches so the surge is one replica at a time, which is the first table row and needs one spare GPU. Third, if no spare exists, run the rollout as surge zero and unavailable one, and only when the traffic forecast shows capacity of N minus 1 is enough. Chapter 20.12 explains how to compute that headroom.

There is also the multi-GPU twist. A replica that uses 4 GPUs needs 4 free GPUs on a node, possibly on the same NVLink domain. A surge slot of one replica therefore means four contiguous GPUs, not one. If the free GPUs are spread across nodes the pod will not schedule even though the count looks fine. That is a placement problem, and it is why a spare pool should hold whole nodes.

**State the surge you can afford in GPUs, not in percent, and remember that a multi-GPU replica needs its GPUs together.**

### 8. Traffic shifting with a router, and the gates

The new version is up on one replica and ready. Now what decides how much traffic it gets? A router with weights, not the replica count. If the router balanced evenly across 8 pods, one new pod would take about 12.5 percent. The function `canary_replicas` shows the point: 5 percent of 8 replicas still needs one whole replica, since a replica cannot be split. So use router weights to send 1 or 5 percent to that one pod, and let its capacity be a ceiling, not a target.

Chapter 20.13 section 6 designed the router and its cache-aware routing. Here note one interaction. A fresh replica has an empty prefix cache, so its early latency looks worse for reasons unrelated to the model. Warm it with a few real requests before giving it weight, and compare it against the baseline over the same prompt mix, not against the whole fleet.

The ladder is a sequence of steps, each held until the gates pass. A reasonable ladder is shadow traffic, then 1 percent, then 5, then 25, then 50, then 100. At every step the question is the same: promote, hold or roll back. The function `decide` returns one of these three from baseline and canary metrics.

The gates fall in two groups. Latency gates compare canary TTFT p99 and inter-token latency p99 against the baseline, with a ratio limit. Quality gates compare an eval score on a fixed prompt set, the share of finish_reason equal to length, and error rate. Chapter 20.18 section 11 explains why finish_reason drift is the early signal for silent quality loss, and Practical MLOps chapter 4 warns that a canary can reach 100 percent without errors and still be broken. That is why the gate must include output quality and not only health.

```python
def decide(base: Metrics, canary: Metrics, g: Gates = Gates()) -> Decision:
    hard, soft = [], []
    if canary.tokens_per_s <= 0 and canary.requests > 0:
        hard.append("canary produced zero tokens while receiving traffic")
    if canary.error_rate > g.error_abs_max:
        hard.append(f"error rate {canary.error_rate:.3f} above hard limit {g.error_abs_max}")
    elif canary.error_rate - base.error_rate > g.error_delta_max:
        soft.append(f"error rate up {canary.error_rate - base.error_rate:.3f} over baseline")
    if base.quality - canary.quality > g.quality_drop_max:
        hard.append(f"quality down {base.quality - canary.quality:.3f} on eval set")
    shift = abs(canary.length_share - base.length_share)
    if shift > g.length_shift_max:
        hard.append(f"finish_reason=length share moved {shift:.2f}")
    for name, c, b, lim in (("ttft_p99", canary.ttft_p99_s, base.ttft_p99_s, g.ttft_ratio_max),
                            ("itl_p99", canary.itl_p99_s, base.itl_p99_s, g.itl_ratio_max)):
        ratio = c / b if b > 0 else float("inf")
        if ratio > lim * (1 + g.hold_band):
            hard.append(f"{name} {ratio:.2f}x baseline, far above {lim}x")
        elif ratio > lim:
            soft.append(f"{name} {ratio:.2f}x baseline, above {lim}x")
    if hard:
        return Decision("rollback", hard + soft)
    if canary.requests < g.min_requests:
        return Decision("hold", [f"only {canary.requests} requests, need {g.min_requests}"] + soft)
    if soft:
        return Decision("hold", soft)
    return Decision("promote", ["all gates passed"])
```

The rule order is the design. Hard failures roll back even with too little traffic, because a quality drop of 6 points on a fixed eval does not need 200 requests to be real. Insufficient traffic holds, it does not promote. Marginal results hold, they do not roll back. Only a clean pass promotes. The thresholds, such as 1.25 times baseline latency, a 2 point quality drop and a 10 point finish_reason shift, are my starting values and not Nebius values.

**Promote only on a clean pass with enough traffic, hold on marginal or thin data, and roll back at once on a hard signal such as quality or zero tokens.**

### 9. Automatic rollback signals

At 03:00 nobody is watching the canary. Which signals should flip it back by themselves? Pick the ones that are cheap, fast and unambiguous, and keep a human in the loop for the rest.

Strong automatic signals are the canary producing zero tokens, the error rate above a hard ceiling, a pod restarting or failing readiness repeatedly, and a quality score below the floor on the live eval probe. Weaker signals are latency ratios and finish_reason shifts, which need a baseline and enough traffic, so they should hold first and page a person if they persist. Chapter 20.19 covers SLO burn alerts that can serve as a fleet-wide backstop.

Rollback itself must be boring. It is the same update action pointing at the previous version id, which still exists in the weights hub and is still cached on nodes if you keep it. Time to rollback is the sum of a router weight change, which is seconds, and a pod replacement, which is a cold start. So keep the old replicas alive until the new version has carried peak traffic, as chapter 20.13 recommends. That makes rollback a weight change and not a reload.

Be careful about the automation itself. A rollback loop that fights an autoscaler or a second rollout can flap. A reasonable rule is that a rollout holds a lock on the endpoint, scaling decisions respect it, and a rollback releases it only after the old version is serving.

**Let machines roll back on cheap, unambiguous signals, and keep the previous version warm so rollback is a weight change.**

### 10. Version skew

During a rollout two versions run at once. Where can that hurt? Anywhere two components assume the same thing. A client sends a request the old version accepts and the new version rejects. A router parses a metric that was renamed. A prefix cache holds blocks computed by the old model, and the new model must never reuse them, because the keys and values differ.

The cache point is worth saying out loud. A reasonable design keys the prefix cache and cache-aware routing by model version, so no hit crosses a version boundary. That is my reasoning, and it follows from the fact that different weights produce different KV values.

Other skews are the engine version against the router and the tokenizer against the weights. A checkpoint paired with the wrong tokenizer fails quietly, with garbage output and green infrastructure. So the registry record from section 4 binds weights, tokenizer and config into one version. Chapter 20.18 section 12 covers metric-name skew and the rule that missing series should be treated as a fault.

Finally, a client-facing skew: if the same user sees both versions in one conversation, answers may change style midway. Sticky routing by tenant or session during the canary solves it, and it is the difference between a canary and an A/B test that Distributed AI Systems, chapter 9, draws.

**Pin tokenizer, weights and config as one version, key caches by version, and keep a session on one version during a canary.**

### 11. Scale-to-zero and the minimum replica decision

A customer has a quiet endpoint used twice a day. Their finance contact asks why they pay for an idle GPU. Scale-to-zero saves that cost and adds one risk, the cold request.

The first request after zero waits for a full cold start. With the section 3 example that is 170 seconds before the first token, which breaks any interactive timeout. So scale-to-zero needs three honest conditions. The client tolerates a long first request or a retry. The weights are cached locally so the download stage is gone. And the owner accepts that the first request may fail on a timeout.

Kubernetes for Generative AI Solutions, chapter 6, notes that KEDA can scale to zero when there are no events, which fits event-driven work. Handbook chapter 15.15 covers autoscaling and scale-to-zero mechanics, so do not repeat them here. The dedicated endpoint has a public 99.9 percent SLA in the case study. A minimum of zero replicas and a 99.9 percent availability target pull in opposite directions, since a cold request counts as slow or failed. My reasoning is that dedicated endpoints serving production traffic should use a minimum of at least one, and scale-to-zero suits development or batch endpoints. Nebius has not said how it handles this.

The cost side is easy to state. One replica kept warm costs its GPUs for every hour. The saving from zero is the idle hours times those GPUs. The price per GPU hour is not given here because it is a commercial figure, so ask for it. Then compare the saving against the cost of failing a customer's first request.

**Set the minimum replicas to one for anything with an SLA, and allow zero only where a long first request is acceptable.**

## How to answer out loud

**Question 1. "Design a dedicated endpoint."** Say the order. State the spec: model, GPU type, GPUs per replica, minimum and maximum replicas, region. Separate the control plane, which stores desired state and lifecycle, from the regional data plane, which serves and keeps serving if the control plane is down. Size from memory first: weights are parameters times bytes. Name the SLA and the redundancy, one extra replica. Mention that Nebius publishes the split and the spec fields, and that the rest is your design.

**Question 2. "How does a customer's checkpoint get onto an endpoint?"** Say upload to a versioned store, hash, validate architecture and tokenizer, eval on a scratch replica, then an update to the endpoint spec that starts a rollout. Say immutable version ids and that rollback is the same action pointing back. Say Nebius has not published this flow and you are describing a reasonable design.

**Question 3. "We have one spare GPU. How do you roll out?"** Say blue/green needs double, so no. Use a rolling update with a surge of one and an unavailable value of zero, with a canary gate in front. Give the cost: it is slow, one replica at a time, so 8 replicas at a 4-tick load take 33 ticks in the simulator against 17 with a surge of two. Name the stall when there is no spare slot and the progress deadline alert.

**Question 4. "What decides promote or rollback?"** Say fixed gates compared against a baseline over the same traffic. Latency ratios, error rate, finish_reason shares and an eval score. Hard failures roll back immediately, thin data holds, marginal results hold. Give your thresholds as starting values you would tune against the SLO. Expect "what if the canary has no traffic" and answer: hold, and use synthetic eval prompts.

**Question 5. "Why not scale to zero for every endpoint?"** Say a cold request waits for download, load and compile, which was 170 seconds in my example, so the first request fails or times out. For a 99.9 percent SLA I would keep at least one replica. Offer zero for dev and batch endpoints with local weights caching.

## Worked scenarios

### Scenario A. Eight replicas, one spare GPU

An endpoint runs 8 replicas, one GPU each, in a region that has exactly one spare GPU. A new engine image must roll out. Engineering proposes the Kubernetes defaults.

Reasoning. The defaults are 25 percent surge and 25 percent unavailable. For 8 replicas that allows 2 extra pods and 2 down. Capacity could fall to 6 of 8 and the second surge pod stays pending. Instead set surge 1 and unavailable 0, so the pod cap is 9 and availability never dips. I ran the simulator and it finished in 33 ticks with a minimum of 8 available and a peak of 9 GPUs. With no spare GPU the same settings stalled for 60 ticks and never finished.

Answer. Use surge 1 and unavailable 0, a `minReadySeconds` so a new pod proves itself before the next, and a progress deadline that alerts. If the spare GPU is later taken by another team, the rollout stalls without hurting users, so alert on the deadline.

```bash
python3 code/part20/c14_rollout_sim.py rolling
```

### Scenario B. Latency is green, quality is not

A canary of a fine-tuned checkpoint reaches 5 percent. TTFT and inter-token latency match the baseline. Error rate is the same. The next day support reports cut-off answers.

Reasoning. The sample file holds baseline and canary metrics. Latency, errors and token rate match. Quality on the fixed eval falls from 0.90 to 0.84 and the share of finish_reason length rises from 0.05 to 0.22. I ran the decision and it returned rollback with two reasons, quality down 0.060 and a length-share shift of 0.17. A latency-only gate would have promoted.

Answer. Roll back by pointing the endpoint at the previous version id. Then compare outputs on the fixed prompt set, check the tokenizer and generation config bound to the new version, and add the eval and finish_reason gates to the pipeline so this is automatic next time.

```bash
python3 code/part20/c14_rollout_sim.py decide code/part20/samples/c14_canary_quality_regress.json
```

### Scenario C. Shipping a custom checkpoint to a live endpoint

A customer uploads a 70 billion parameter checkpoint in FP16 and wants it live on their existing endpoint within the hour. The endpoint runs 4 replicas of 4 GPUs.

Reasoning. Weights are 140 GB. The hash and architecture check take minutes. The scratch eval needs one replica, so you borrow one slot. Cold start is 170 seconds under the section 3 inputs, of which 70 is download. Pre-stage the weights onto the nodes first. A rolling update with surge 1 replaces 4 replicas, each taking about 100 seconds once staged. The surge slot is 4 GPUs together, which must exist on one node. If it does not, the rollout stalls, as in Scenario A.

Answer. Validate, stage to local disk, run the canary at 1 percent with the eval gate, step up, keep the old replicas until peak traffic has passed on the new version. Tell the customer the time budget from the numbers, and measure real load time on the first replica before promising the rest.

## Hands-on lab

Everything below runs on a laptop with Python and pytest. I ran steps 1 to 4. Step 5 was not run, because it needs a GPU cluster.

1. Run the tests.

```bash
python3 -m pytest code/part20/test_c14_rollout_sim.py -q
```

Expected result: 19 passed.

2. Run the rolling-update table and compare it with section 6.

```bash
python3 code/part20/c14_rollout_sim.py rolling
```

Expected result: four lines, matching the table in section 6.

3. Validate the Deployment sketch with a client-side dry run.

```bash
kubectl apply --dry-run=client -f code/part20/c14_engine_deploy.yaml
```

Expected result: `deployment.apps/demo-engine created (dry run)`. This checks the shape only. The image is a placeholder and no cluster state changed.

4. Compute a cold start for your own numbers and see which stage dominates.

```bash
python3 -c "import sys; sys.path.insert(0,'code/part20'); from c14_rollout_sim import cold_start; print(cold_start(140, 2, 14, 60, 30))"
```

Expected result: total 170.0 seconds with download 70.0.

5. On a GKE or Nebius cluster, apply the Deployment with a real engine image, change the image tag, and watch `kubectl rollout status` while a script samples ready pods. Expected shape of the output: ready pods never below replicas minus the unavailable value. This step was not run.

## Drill questions

1. Which actions does the control plane own for a dedicated endpoint, and what stays in the data plane?

<details><summary>Answer</summary>

The control plane owns create, update, enable, disable and delete, plus the stored spec. The data plane is regional and serves traffic. It should keep serving from a cached copy of desired state if the control plane is down.

</details>

2. What fields does a dedicated endpoint expose, as public information says?

<details><summary>Answer</summary>

GPU type from L40, H100, H200 or B200, GPUs per replica, minimum and maximum replicas, and region in the EU or US.

</details>

3. Why is the GPU budget for an endpoint maximum replicas plus one, not just maximum replicas?

<details><summary>Answer</summary>

A rolling update needs a surge slot to start a new pod before an old one is removed. Without a spare replica's worth of GPUs, the rollout stalls or you lose capacity.

</details>

4. Name the three stages of cold start and one way to shorten each.

<details><summary>Answer</summary>

Download, load and compile with warm-up. Pre-stage weights on local disk for download, use faster local storage for load, and persist the compile cache for compile.

</details>

5. What should liveness, readiness and startup probes each do for an LLM engine?

<details><summary>Answer</summary>

The startup probe covers the load window and must outlast the measured cold start. Liveness is a local check with generous tolerance, so a busy engine is not killed. Readiness means the engine can complete a real request.

</details>

6. Why is blue/green a poor default for GPU endpoints?

<details><summary>Answer</summary>

It needs a full second fleet, twice the GPUs, which may not exist. Rollback is instant, but the cost in scarce GPUs is the problem.

</details>

7. What are the Kubernetes defaults for maxSurge and maxUnavailable, and how do they round?

<details><summary>Answer</summary>

Both default to 25 percent. Surge rounds up and unavailable rounds down. They cannot both be zero.

</details>

8. A rollout has surge 1, unavailable 0, and no spare GPU. What happens?

<details><summary>Answer</summary>

The new pod cannot be scheduled and stays pending, so the rollout makes no progress. The old fleet keeps serving, and the Deployment reports `ProgressDeadlineExceeded` after the deadline. So alert on it.

</details>

9. Latency gates pass but users complain. Which gates did you miss?

<details><summary>Answer</summary>

Quality gates. Run an eval on a fixed prompt set and watch the share of finish_reason length against a baseline, as well as error rate.

</details>

10. When is scale-to-zero acceptable on a dedicated endpoint, and when not?

<details><summary>Answer</summary>

Acceptable for dev or batch endpoints where a long first request is fine and weights are cached locally. Not acceptable for a production endpoint with a 99.9 percent SLA, because the cold request waits for the whole cold start.

</details>

## Common mistakes and weak answers

Saying "blue/green" without costing it. Say it needs twice the GPUs and name what you do when you do not have them.

Treating the rollout as only a Kubernetes setting. A rollout has weights, caches, a router, gates and rollback. Walk through all of them.

Promoting on latency alone. Add quality, finish_reason and error gates, and say why health is not correctness.

Quoting percentages for surge. Quote GPUs, and remember a multi-GPU replica needs its GPUs together.

Claiming Nebius details. Say "Nebius publishes the split between control plane and data plane and the endpoint fields. The rest is my design."

Ignoring cache and version skew. Mention version-keyed caches and one version per session during a canary.

## Connections to the rest of the handbook

- 20.12 Estimation toolkit for inference capacity (`c20-12`) gives the sizing arithmetic used in section 2.
- 20.13 Design: a multi-tenant LLM inference API (`c20-13`) designs the router, the control plane split and the first rollout sketch.
- 20.18 How LLM serving fails (`c20-18`) covers cold start, probe mistakes, quality drift and version skew from the failure side.
- 20.19 SLIs, SLOs and alerts for token APIs (`c20-19`) covers the burn alerts behind automatic rollback.
- 20.26 The stress interview (`c20-26`) practises a bad rollout as an incident.
- 15.15 Autoscaling inference (`c15-15`) covers scale-to-zero and autoscaler signals. 15.16 Production serving stack and reliability (`c15-16`) covers probes.
- 16.6 Model registry, CI/CD and GitOps for models (`c16-06`) and 16.9 LLM evaluation and guardrails (`c16-09`) cover the registry and the eval gates.

## Sources and review notes

Sources and dates fetched or read (2026-11-09):

- Kubernetes documentation, Deployments page, from the kubernetes/website repository main branch: rolling update, `maxSurge`, `maxUnavailable`, defaults, rounding and progress deadline. Kubernetes documentation, "Configure Liveness, Readiness and Startup Probes": startup probe window. The local `kubectl` client is version 1.35.0.
- Production Kubernetes, chapter 14 "Application Considerations": SIGTERM, grace period, probe types. Chapter 13 "Autoscaling": cluster overprovisioning and pending pods.
- Practical MLOps, chapter 4 "Continuous Delivery for Machine Learning Models": blue/green and canary, the boolean example.
- Machine Learning Platform Engineering, chapter 10 "Model inference and serving": model versioning and rollback.
- Kubernetes for Generative AI Solutions, chapter 6 "Scaling GenAI Applications on Kubernetes": KEDA scale to zero. Chapter 13 "High Availability and Disaster Recovery": blue/green and canary for safer rollouts.
- Hands-On LLM Serving and Optimization, chapter 5: weights size rule and the SSD bandwidth range. LLMs in Production, chapter 6, as summarised in chapter 20.13: weights on a mounted volume.
- Chapters 20.12, 20.13, 20.18 and 20.19 of this volume for the facts they source.
- `planning/VOLUME_20_NEBIUS_SRE_PLAN.md` section 1: public Nebius facts, tagged vendor or docs.

Explicitly labelled inferences:

- The weights-hub flow, the immutable version record, validation steps and staging to node-local disk.
- The lifecycle rule that delete is allowed only from disabled.
- Version-keyed prefix caching, session pinning during a canary and the rollout lock.
- All gate thresholds and the traffic ladder.
- The readiness design that runs a real one-token request, and the hypothetical `/ready` path.
- That dedicated endpoints with an SLA should keep a minimum of one replica.
- Illustrative inputs for download rate, compile time and warm-up time.
- The simulator frees a terminating pod's slot at once, which real pods do not, since they drain first.

Not verified:

- No real cluster or GPU was used. The rolling update is a simulation of the controller's rules and not a real controller trace. The Deployment was checked by client-side dry run only.
- The H100 SXM memory size of 80 GB was checked against the NVIDIA H100 page on 2026-11-09.
- I did not check Nebius Token Factory documentation for custom-weights features, rollout behaviour or scale-to-zero. The plan records none.
- The statement that a health route reports a crash and not a stall is inherited from chapter 20.18, where it is an inference from the source.
- Docker was not running and the host is macOS, so no Linux command was run.
