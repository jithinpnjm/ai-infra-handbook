# Volume 20 plan: Nebius Senior SRE, Token Factory (Inference Platform)

Research date: 2026-11-09. Evidence tags: [official] Nebius page, [report] anonymous candidate report, [vendor] Nebius marketing, [gap] not public.

## 1. What the research found

### The role (job posting, Remote Europe / London / Amsterdam / Berlin / Prague)
Owner of reliability, performance and observability for the whole inference stack (text, vision, audio, multimodal).
- Telemetry pipelines (metrics, logs, traces) at very large volume.
- Kubernetes autoscaling tuned for GPU efficiency.
- Terraform modules that build resilience into new clusters.
- Request routing and retry logic so transient failures do not reach users.
- Incident detect/isolate/remediate with automation and runbooks; lead post-mortems.
- Required: Kubernetes, Prometheus, Grafana, Terraform/IaC, Python or Bash, alert design and SLOs for high-throughput APIs, how distributed back-ends fail, debugging "from kernel to application layer", self-healing systems.
- Nice: vLLM, Triton, Ray, MLOps / model-hosting.
- Note: the posting is about four months old. Confirm it is still open.

### The process [official: nebius.com/careers/interviews/sre]
1. CV review (reply in 3 business days). 2. Recruiter call (career, skills, interest). 3. Three technical interviews, 60-90 min each, run by interviewers from different teams. 4. Final hour with a team leader (team, projects, possibly extra technical questions, told in advance).
Technical content stated by Nebius:
- Experience with languages, operating systems, databases; service management, Linux/Unix, networks.
- At least one practical coding / algorithms / data-structures task. Practical tasks in the Linux console.
- Coding, troubleshooting, debugging.
- System design: a whole or partial distributed system, meet load/availability targets, estimate performance and compute, data storage and processing trade-offs.
- Any language, any technology allowed. Say your reasoning aloud, ask for hints, offer alternatives, review code before submitting.
- Official reading list: Systems Performance (Gregg); The Linux Programming Interface (Kerrisk); UNIX and Linux System Administration Handbook; Practical Monitoring (Julian); Performance Analysis and Tuning on Modern CPUs (Dendibil); Google SRE books.

### Candidate reports [report, thin, mixed]
- Amsterdam SRE: four stages. (1) Linux server troubleshooting via CLI, 1 h. (2) Algorithms, two LeetCode easy/medium, 1 h. (3) System design, 1 h. (4) "Stress interview": solve a production incident, 30 min. Topics seen: file descriptors, syscalls, a file the service cannot access where chmod does not help.
- Dublin SRE/DevOps: recruiter screen then up to 6-7 rounds. London Senior SRE: five rounds, mostly junior-level questions, no proper system design, and some rescheduling and poor communication.
- Czech Senior SRE (June 2025): about a week, no offer, interviewer without technical background.
- Duration: officially short, reports say one to three months.
- Read: the loop is uneven. Prepare for the hardest version (all of the above) and expect some rounds to be easy.

### What Token Factory is [vendor + docs]
- Serverless and dedicated endpoints, OpenAI-compatible API, full vLLM parameter set. Control plane (lifecycle: create/update/enable/disable/delete) separate from region-specific data plane. Dedicated endpoints: pick GPU type (L40, H100, H200, B200), GPUs per replica, min/max replicas, region (EU/US, data residency).
- Flavors: base and fast (smaller batches and speculative decoding). Optimisations listed: KV cache, paged attention, flash attention, quantisation (about 99% quality claim), continuous batching, context caching, speculative decoding.
- Observability exposed to customers: end-to-end latency p50/p90/p99, TTFT, token throughput, active replicas and scaling, errors by status code, traffic by prompt size and region, KV-cache reuse versus tail latency.
- From the chat-app case study [vendor]: separate prefill and decode pools; cache-aware routing (hit rate about 5% to 30% to 50-60%); backpressure to stop decode queues overrunning; retry logic changed to stop amplification in partial outages; aggressive liveness probes were restarting healthy workers; restarted workers sometimes did not rejoin the pool and capacity shrank silently; X+1 redundancy; alerts on tail TTFT, cache drops, finish_reason drift, decode error bursts; 99.9% SLA on dedicated endpoints; "latency must be stable, not just fast".
- Hardware: B200 today; Vera Rubin NVL72 and Groq 3 LPX announced.
- Not public [gap]: autoscaling signals and thresholds, router algorithm, TPOT targets, probe settings. So the interview will probe your own reasoning here, not recall of Nebius internals.
- Related Nebius open source: Soperator (Slurm on Kubernetes), nebius-solutions-library. Sister SRE postings: DevTools, Compute Node, NetSRE.

### Honest limits of this research
Only about four Nebius-specific candidate reports found, none for this exact role. Glassdoor and Blind pages could not be fetched in full (403). Ask the recruiter which rounds apply, and whether a project deep dive or a take-home is included.

## 2. Volume 20 design

Principle: every chapter maps to a stated interview stage or a line of the job posting. Reuse the handbook (Parts 1-6, 10-12, 15-18) by linking, not copying. New material only where the handbook has a gap. Same standards as the other volumes: LANGUAGE_RULE, tested code, gem-book depth, fact-check pass.

### Part A: the loop
- 20.1 The Nebius loop and how to use this volume (process, scoring signals, 8-week schedule, the "think aloud" protocol, questions to ask them).
- 20.2 The role in one page: JD line by line, with the handbook chapter that covers each.

### Part B: Linux console and troubleshooting round
- 20.3 Triage method for a sick Linux box (USE method, first 60 seconds, what to run in what order).
- 20.4 Files, descriptors and syscalls (strace, lsof, /proc/PID/fd, ulimit, inodes, deleted-but-open files, permission puzzles: ACLs, SELinux, mount options, immutable bit, chmod that "does nothing").
- 20.5 CPU, memory, disk and scheduler (load vs utilisation, PSI, OOM killer, cgroup limits, page cache, iostat, perf, flame graphs).
- 20.6 Network debugging (ss, tcpdump, conntrack, DNS, MTU, retransmits, TLS failures, TIME_WAIT, SYN backlog).
- 20.7 Lab set: 20 broken-box scenarios with scripts you run locally in a container/VM, each with an answer key.

### Part C: coding and algorithms round
- 20.8 What to expect (one to three problems, easy to hard, any language) and a Python/Go toolkit.
- 20.9 Patterns for SRE-flavoured problems: log parsing, sliding windows, heaps and top-k, interval merging, rate limiters (token bucket, sliding log), LRU, consistent hashing, retry with jitter, graph/topological ordering of dependencies, string compression.
- 20.10 Complexity, latency numbers every engineer should know, testing your own code aloud.
- 20.11 Practice set: about 40 problems with tested reference solutions in `code/part20/`.

### Part D: system design for an inference platform
- 20.12 Estimation toolkit: tokens/s, KV-cache memory per request, GPUs per QPS, cost per million tokens, capacity with headroom.
- 20.13 Design: multi-tenant LLM API (gateway, auth, quotas, router, prefill/decode pools, autoscaling, regions, control plane vs data plane).
- 20.14 Design: dedicated endpoints and model rollout (weights hub, canary, rollback, warm-up, cold start, scale-to-zero).
- 20.15 Design: observability pipeline at very high volume (metrics cardinality, sampling traces, log cost, SLO burn alerts).
- 20.16 Design: GPU fleet health and capacity (node failure, DCGM, drain/cordon, spare pool, X+1).
- 20.17 Design drill sheet: 12 prompts, each with a time-boxed outline and the trade-offs graders look for.

### Part E: inference-specific SRE knowledge
- 20.18 How LLM serving fails (queues, KV-cache exhaustion, preemption, long-context head-of-line blocking, OOM, NCCL hangs, thundering herd on restart, silent pool shrink).
- 20.19 SLIs and SLOs for token APIs (TTFT, TPOT/ITL, e2e, error rate, goodput, availability by tenant), burn-rate alerts, and why "fast" is not "stable".
- 20.20 Autoscaling GPU inference (HPA/KEDA on queue depth and KV usage versus GPU utilisation, cold-start cost, warm pools, flap control).
- 20.21 Routing and retries (cache-aware routing, backpressure, load shedding, retry budgets, hedging, idempotency, circuit breakers).
- 20.22 vLLM / Triton / Ray / TensorRT-LLM / SGLang operations: knobs, metrics, failure signatures (links to Part 15).

### Part F: Kubernetes, Terraform, observability
- 20.23 Kubernetes failure drills (scheduler, GPU device plugin, node pressure, PDB, upgrades, CoreDNS, etcd) with a stress-interview format.
- 20.24 Terraform for resilient clusters (module design, state, drift, blast radius, multi-region, Nebius provider basics).
- 20.25 Prometheus/Grafana/OpenTelemetry deep dive (PromQL traps, recording rules, cardinality, long-term storage options, trace sampling).

### Part G: the stress interview and the final round
- 20.26 Production incident role-play: 10 scripted incidents (inference-specific and general) played as a 30-minute drill, with a scoring rubric (communication, hypothesis order, mitigation before root cause).
- 20.27 Post-mortem and on-call: blameless writing, incident command, how to answer "tell me about an incident you led".
- 20.28 Project deep dive and behavioural round (STAR stories mapped to Nebius values, a 90-minute single-project defence template).
- 20.29 The 8-week plan, final-week checklist, one-page cheat sheet.

Size target: about 4-6k words per chapter for design/knowledge chapters, shorter for drill sheets. About 29 chapters, one new code folder `code/part20/` with tests.

## 3. Sources to mine beyond the handbook
- Nebius: careers/interviews/sre, Token Factory docs (docs.tokenfactory.nebius.com, llms.txt), blog (invisible architecture, dedicated endpoints, vLLM guide), nebius/soperator, nebius-solutions-library.
- Gem books already in the library: Systems Performance if present, The Linux Programming Interface, Linux sysadmin handbook, K8s books, production-k8s, ai-factory, supercomputers. Build a per-book ledger like earlier volumes.
- Google SRE books (SLOs, alerting, handling overload, cascading failures), Practical Monitoring.
- Papers/docs for inference: vLLM paged attention, continuous batching (Orca), DistServe / Splitwise (prefill-decode disaggregation), LMCache, llm-d, AIBrix, KServe, Dynamo.
- Candidate reports: Glassdoor, Blind, Jointaro, Reddit (re-check manually in a browser since fetch is blocked).

## 4. Method and order of work
1. You confirm this plan (and the open questions below).
2. Build `planning/volume-20-ledger` (chapter to source mapping), then agents draft chapters in batches, gates as in Parts 16-18 (voice, chain density, code tests, fact-check).
3. Priority order if time is short (interview date matters): Part B, Part D, Part E, Part G, then C and F. The Linux console and system design rounds appear in every report.

## 5. Open questions for you
- Interview date and which stages the recruiter has already confirmed?
- Preferred coding language: Python or Go?
- Do you want a separate fast track (a 2-week cram document) built first from existing chapters, while the full volume is written?

## 6. Status (2026-11-09 evening)
All chapters 20.1 to 20.29 are drafted (gates: 648 tests, 289 code files clean, site build passes). 20.30 to 20.33 (Nebius public architecture series) were added by another session and are kept. Not yet done: human read of every chapter, fact-check pass over claims marked unverified or "my reasoning", running Linux scenarios on a real Linux host, and a trim of 20.26 (about 9,900 words, mostly drill tables). Part 19 rebuild has not started.
