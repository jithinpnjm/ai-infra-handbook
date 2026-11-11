# Nebius inference research notes (chapter 20.38)

Fetched 2026-11-11. Scope narrowed by the user to technical architecture only. Tags: [official] [vendor] [source-code] [third-party] [report] [inference]. The machine-readable form is `code/part20/c38_claim_register.json` (55 entries, validated by `c38_claim_register.py`).

## Fetched, in my own words

### docs.tokenfactory.nebius.com [official]
- `llms.txt` index (all pages listed; also sandboxes/ConTree, team access, billing, which I did not read as they are not inference serving).
- `ai-models-inference/overview`: Base and Fast flavors, `-fast` suffix, list of optimisations, "approximately 99%" quality claim [vendor wording inside docs], full vLLM parameter set on the API.
- `dedicated-endpoints/operating`, `best-practice`, `capacity-and-scaling`, `faq`, `custom-weights` (beta, on request), `lifecycle-and-status`, `control-data-plane`, `billing-policy`, `overview`, `quickstart`.
- `ai-models-inference/rate-limits`: 15-minute buckets, x1.2 and /1.5, 20x ceiling, over-limit lower-priority processing, header list.
- `ai-models-inference/observability` and `observability-api-integrations`: metric list, KV-cache hit rate "local and external", TTFT streaming only, dedicated only, stored in eu-north, Prometheus federate scrape.
- `cached-tokens`, `public-serverless`, `legal/legal-quick-guide` (no cross-region failover for dedicated; speculative decoding retention; Finland storage).
- `post-training/models`, `merge-moe-lora-weights`, `custom-speculator`, `how-to-fine-tune`, `data-lab/*`.
- `json`, `function-calling`, deprecation notices for 2026-06, 2026-08, 2026-11.
- `api.tokenfactory.nebius.com/openapi.json` version 20261109: paths, `ServiceTier`, `SupportedGPU`, `SupportedRegion` (16 values), `ModelFlavor.quantization`, `ReservationPolicy`. No `/v1/batches`.

### nebius.com/blog [vendor] (publication dates from page metadata)
routing-is-the-difference-between-scaling-and-stalling (2026-02-17); the-invisible-architecture-behind-great-chat-apps (2025-12-15); nebius-weka-shared-kv-cache-benchmark-hgx-b300 (2026-09-24); in-agentic-rl-faster-tokens-are-not-enough (2026-09-28); lk-losses (2026-04-10); slimspec (2026-07-20); train-the-draft-model-for-your-workload (2026-06-25); training-speculative-decoders (2026-08-06, kernel and memory engineering, not used); moe-spec-decoding (2026-01-14); nvidia-groq-3-lpx-nebius-token-factory (2026-08-24); nebius-and-eigen-ai-partner (2026-03-17); the-ai-cloud-will-be-won-at-the-software-layer (2026-05-13); dedicated-endpoints-and-custom-weights-hub (2026-02-26); elevating-the-craft-introducing-the-inference-frontier-program (2026-03-15); mlperf-inference-v6-0 / v6-1 / v5.1 results; introducing-serverless (2026-03-26, this is AI Cloud serverless Endpoints, a different product from Token Factory Serverless); incident-post-mortem us-central1 2026-08-19 (published 2026-08-27) [official-style post-mortem].
Also read and set aside as not architecture: serving-llms-with-vllm-practical-guide (generic vLLM tutorial), serving-llama-4/qwen3-skypilot-sglang (AI Cloud tutorials), run:ai fractional GPUs, world-models serving, retail/agents/partner posts, business posts.

### Press [vendor]
HPCwire release 2025-11-07: 99.9 percent SLA for dedicated, sub-second latency, up to 70 percent cost cut; conflicting model counts.

### GitHub [source-code]
- `api.github.com/orgs/nebius/repos`: 53 repos, none an inference engine. Relevant: token-factory-cookbook, tokenfactory-rl, kvax, ml-containers, mcp-server.
- Search "nebius" in vllm, sglang, LMCache, llm-d, dynamo, TensorRT-LLM, SpecForge. Almost all hits are third parties running on Nebius. Confirmed Nebius-attributed: SpecForge PR 492 (LK losses, merged, blog says Nebius contributed it); vLLM PR 56414 docs for Nebius Serverless AI by an author whose profile lists @nebius (AI Cloud product, not TF). vLLM issue 65611 is a third-party bug report against a Nebius EAGLE3 drafter on AMD.
- Hugging Face org nebius: EAGLE3, Medusa, MLP-Speculator and MTP drafters; SWE-rebench datasets.

### Third-party
- SemiAnalysis InferenceX: Nebius appears as a compute supporter, no ranked result (web search summary only).
- Artificial Analysis has a Nebius provider page (search result); I did not read figures. Blog claims citing it are tagged vendor.

## Looked for and NOT found
- Any Nebius engineering post naming the router product, the gateway, the scheduler, the autoscaler signal, or the KV-transfer library for disaggregation.
- A published Nebius LMCache, llm-d or Dynamo contribution by a verifiably Nebius-affiliated author (search hits were third parties).
- Any quantisation quality number beyond "approximately 99%", and which flavor uses which precision (the API exposes a `quantization` string per flavor; values not documented on the pages read).
- A multi-region data plane design: docs say dedicated has none. Serverless "Global" has no description.
- A Batch API page or schema. Talks or webinar recordings with architecture detail (one conference abstract only, no content).
- MLPerf results measuring Token Factory itself. They measure AI Cloud hardware.
- Any published latency or availability SLOs for Serverless.
- Not fetched: SEC filings (out of scope), Clarifai post, Artificial Analysis pages, ev.careers listing.

## Conflicts noted
1. Docs say no formal SLA for self-service dedicated; blog and press say 99.9 percent (contract case).
2. Chat post says all inference ran zero-retention; legal guide says retention for speculative decoding is the default.
3. Overview says Fast and Base outputs are identical and also "approximately 99%" quality.
