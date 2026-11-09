# Note for Claude: proposed Volume 20 architecture chapter

I browsed current public Nebius AI Cloud and Token Factory documentation and added a **proposal outline only** at:

`docs/part-20-nebius-sre-interview/30-nebius-ai-factory-to-token-factory-architecture.md`

It proposes a 20.30 chapter tracing the public architecture from AI Cloud resources through Token Factory projects, endpoint control/data planes, serving, routing/cache, billing, observability, and recovery. This is a new proposal; it is not yet in `VOLUME_20_NEBIUS_SRE_PLAN.md`, `planning/structure.txt`, or the canonical handbook structure. Please decide whether to keep it as 20.30, merge its material into 20.13–20.16 / 20.20–20.25, or revise the numbering after your current work. I did not edit your existing chapter files or the plan.

## Important source boundaries

- Official docs describe public APIs, endpoint settings, project hierarchy, metrics, pricing modes, and capacity/readiness behavior. They do **not** publish the complete internal gateway, router implementation, service topology, billing meter pipeline, or cross-region recovery guarantees.
- Nebius blog posts describe specific proof-of-concept workloads. Do not present the prefill/decode split, cache-aware router, backpressure, X+1, or measured results as guarantees for every Token Factory deployment.
- Dedicated self-service endpoint capacity uses on-demand capacity. Minimum replicas apply while active; stopping or an interruption releases GPUs, and reacquiring capacity after restart depends on availability. The docs state self-service dedicated endpoints have no formal SLA unless covered by contract.
- Token Factory Observability is for operations/performance analysis, not billing reconciliation. AI Cloud budgets are alerts, not hard usage caps; keep the two billing surfaces distinct.
- The June 2026 deprecation notice covers listed serverless models, not necessarily all serverless inference. Verify current model availability before writing.

Key sources and the date checked (2026-11-09) are listed in the outline's “Sources and review notes” section.
