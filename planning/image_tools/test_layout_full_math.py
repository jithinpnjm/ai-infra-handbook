import re

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

# Verify line splits and text widths
titles = {
    "d1": wrap_text("1 Requests are long, variable and somewhat stateful", 32),
    "d2": ["2 Connections are long-lived"],
    "d3": ["3 Cache locality matters"],
    "d4": wrap_text("4 Backends are expensive and heterogeneous", 28),
    "d5": ["5 Autoscaling is slow"]
}

conseqs = {
    "c1": wrap_text("a request may stream tokens for minutes; cost varies by orders of magnitude with prompt and output length; the real load is queue depth, running sequences and KV-cache occupancy, not connection count", 46),
    "c2": wrap_text("HTTP/2 and gRPC streams and SSE hold resources; reloads, scale-in and deploys must drain gracefully; an idle timeout at any hop can cut a slow generation", 46),
    "c3": wrap_text("prefix caching for system prompts, RAG context and multi-turn chat makes a request cheaper on the replica that already holds its prefix KV blocks; same session or prefix to the same replica raises hit rates, pure affinity creates hot spots", 46),
    "c4": wrap_text("GPU types, tensor-parallel group sizes, disaggregated prefill and decode pools, LoRA adapters per replica, quantised variants", 46),
    "c5": wrap_text("GPU nodes and model loads take minutes, so the router must absorb bursts by queueing or shedding", 46)
}

resps = {
    "r1": wrap_text("Balance per request, not per connection (Envoy, HAProxy, nginx grpc_pass, Gateway API inference extensions, or client-side)", 42),
    "r2": wrap_text("load signal: least-outstanding-requests baseline, better backend-reported running and waiting requests, KV-cache usage and estimated tokens (Prometheus, headers, ORCA-style load reports), P2C over load", 42),
    "r3": wrap_text("cache-aware: consistent hashing on session ID or prefix hash with bounded loads, or a router tracking which replica holds which prefix blocks", 42),
    "r4": wrap_text("disaggregated: route prefill and decode to separate pools, handle the KV transfer, couple the autoscaling and admission", 42),
    "r5": wrap_text("overload: per-tenant concurrency and token-rate limits, priority queues separating interactive from batch, 429 or 503 early, KV-cache headroom in admission control", 42)
}

print("Line counts:")
for k in ["1", "2", "3", "4", "5"]:
    print(f"Row {k}: Title {len(titles['d'+k])} lines, Conseq {len(conseqs['c'+k])} lines, Resp {len(resps['r'+k])} lines")

