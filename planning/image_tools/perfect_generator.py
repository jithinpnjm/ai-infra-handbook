import xml.etree.ElementTree as ET
import re

# Exact labels from prompt:
LABELS = {
    "title": "Why web load balancing assumptions fail for LLM serving: five differences",
    "scenario": "every health check green, average latency fine, one replica buried under long generations while the others sit idle",
    "d1": "1 Requests are long, variable and somewhat stateful",
    "c1": "a request may stream tokens for minutes; cost varies by orders of magnitude with prompt and output length; the real load is queue depth, running sequences and KV-cache occupancy, not connection count",
    "r1": "Balance per request, not per connection (Envoy, HAProxy, nginx grpc_pass, Gateway API inference extensions, or client-side)",
    "d2": "2 Connections are long-lived",
    "c2": "HTTP/2 and gRPC streams and SSE hold resources; reloads, scale-in and deploys must drain gracefully; an idle timeout at any hop can cut a slow generation",
    "r2": "load signal: least-outstanding-requests baseline, better backend-reported running and waiting requests, KV-cache usage and estimated tokens (Prometheus, headers, ORCA-style load reports), P2C over load",
    "d3": "3 Cache locality matters",
    "c3": "prefix caching for system prompts, RAG context and multi-turn chat makes a request cheaper on the replica that already holds its prefix KV blocks; same session or prefix to the same replica raises hit rates, pure affinity creates hot spots",
    "r3": "cache-aware: consistent hashing on session ID or prefix hash with bounded loads, or a router tracking which replica holds which prefix blocks",
    "d4": "4 Backends are expensive and heterogeneous",
    "c4": "GPU types, tensor-parallel group sizes, disaggregated prefill and decode pools, LoRA adapters per replica, quantised variants",
    "r4": "disaggregated: route prefill and decode to separate pools, handle the KV transfer, couple the autoscaling and admission",
    "d5": "5 Autoscaling is slow",
    "c5": "GPU nodes and model loads take minutes, so the router must absorb bursts by queueing or shedding",
    "r5": "overload: per-tenant concurrency and token-rate limits, priority queues separating interactive from batch, 429 or 503 early, KV-cache headroom in admission control",
    "bottom": "Measure first, and choose the load signal before you choose the algorithm"
}

print(f"Total labels defined: {len(LABELS)}")
