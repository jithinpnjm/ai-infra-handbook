# Note for Claude: Volume 20.30–20.33 architecture series handoff

I browsed current public Nebius AI Cloud and Token Factory documentation and drafted this four-chapter series:

- `docs/part-20-nebius-sre-interview/30-nebius-ai-factory-to-token-factory-architecture.md`
- `docs/part-20-nebius-sre-interview/31-nebius-ai-cloud-foundation-gpu-fabric-and-platform-choices.md`
- `docs/part-20-nebius-sre-interview/32-token-factory-model-lifecycle-serving-and-economics.md`
- `docs/part-20-nebius-sre-interview/33-ai-factory-solution-architecture-ha-and-recovery.md`

Together they exceed the requested 20K-word minimum (about 23.7K words). The sequence is: architecture map; AI Cloud facilities and substrate; Token Factory product lifecycle/serving/economics; and customer solution patterns, HA and recovery. They remain proposed additions, not yet integrated into `VOLUME_20_NEBIUS_SRE_PLAN.md`, `planning/structure.txt`, or the canonical handbook structure. Please decide how to integrate or renumber after your current work. I did not edit your existing chapters or the volume plan.

## Important source boundaries

- The official docs index maps a wider set of Cloud and Token Factory pages; relevant compute, fabric, storage, VPC, Kubernetes, billing, IAM, control/data plane, lifecycle, cached-token, legal, Data Lab, and post-training pages are linked in the chapter.
- Keep the products distinct: AI Cloud Serverless AI runs customer containers; Token Factory Public Serverless is a shared model API with Global processing; Dedicated Endpoints have a fixed, contractually selected region and no provider multi-region routing, overflow, or failover.
- Official docs do **not** publish the complete internal gateway, router implementation, serving topology, billing-meter pipeline, or exact autoscaling signals. Blog architecture and cache-routing results are workload-specific evidence, not universal product contracts.
- Nebius blog posts describe specific proof-of-concept workloads. Do not present the prefill/decode split, cache-aware router, backpressure, X+1, or measured results as guarantees for every Token Factory deployment.
- Self-service Dedicated Endpoint GPUs are released when stopped or interrupted; restart capacity is subject to availability, and no formal SLA applies unless covered by contract. The Token Factory billing policy's prose trigger and readiness table need support/contract clarification for partially-ready cases.
- Public Serverless uses shared prefix cache across organizations for a model; Dedicated Endpoint cache is customer-isolated. The cache guide warns that it is not an access-control boundary. ZDR is org-scoped and disables speculative decoding, which may affect performance.
- Token Factory metrics are documented as Dedicated-Endpoint-only and not a billing ledger. AI Cloud budgets are delayed alerts, not spend caps. The November 9, 2026 notice removes listed models from Public Serverless only; check the live catalog.

Sources were checked on 2026-11-09 and are listed in the chapters. Targeted MDX/Mermaid checks and the full Docusaurus build passed with all four files present. The generic validator reports REVIEW because it expects the handbook-wide 20-question/exercise/claim-ledger template, while the Volume 20 prompt specifies 10 drill questions and a hands-on lab. Claim-ledger and plan/structure integration remain follow-up decisions; no shared plan or status tracker was changed.
