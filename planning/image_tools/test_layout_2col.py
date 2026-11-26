import textwrap

scenario_text = "every health check green, average latency fine, one replica buried under long generations while the others sit idle"

diffs = [
    ("1 Requests are long, variable and somewhat stateful",
     "a request may stream tokens for minutes; cost varies by orders of magnitude with prompt and output length; the real load is queue depth, running sequences and KV-cache occupancy, not connection count"),
    ("2 Connections are long-lived",
     "HTTP/2 and gRPC streams and SSE hold resources; reloads, scale-in and deploys must drain gracefully; an idle timeout at any hop can cut a slow generation"),
    ("3 Cache locality matters",
     "prefix caching for system prompts, RAG context and multi-turn chat makes a request cheaper on the replica that already holds its prefix KV blocks; same session or prefix to the same replica raises hit rates, pure affinity creates hot spots"),
    ("4 Backends are expensive and heterogeneous",
     "GPU types, tensor-parallel group sizes, disaggregated prefill and decode pools, LoRA adapters per replica, quantised variants"),
    ("5 Autoscaling is slow",
     "GPU nodes and model loads take minutes, so the router must absorb bursts by queueing or shedding")
]

responses = [
    "Balance per request, not per connection (Envoy, HAProxy, nginx grpc_pass, Gateway API inference extensions, or client-side)",
    "load signal: least-outstanding-requests baseline, better backend-reported running and waiting requests, KV-cache usage and estimated tokens (Prometheus, headers, ORCA-style load reports), P2C over load",
    "cache-aware: consistent hashing on session ID or prefix hash with bounded loads, or a router tracking which replica holds which prefix blocks",
    "disaggregated: route prefill and decode to separate pools, handle the KV transfer, couple the autoscaling and admission",
    "overload: per-tenant concurrency and token-rate limits, priority queues separating interactive from batch, 429 or 503 early, KV-cache headroom in admission control"
]

# Widths:
# Left box: x=40, width=730. Usable text width = 730 - 36 = 694px.
# In Left box, Title has icon offset: icon=48, gap=14 -> usable width for title = 694 - 62 = 632px.
# Title chars at 30px: 632 / 18.0 = 35 chars.
# Conseq chars at 24px: 694 / 14.4 = 48 chars.
# Right box: x=830, width=730. Usable text width = 694px.
# Resp chars at 24px: 694 / 14.4 = 48 chars.

print("=== CHECKING ALL LINE WRAPPINGS ===")
for i in range(5):
    t_lines = textwrap.wrap(diffs[i][0], width=35)
    c_lines = textwrap.wrap(diffs[i][1], width=48)
    r_lines = textwrap.wrap(responses[i], width=48)
    
    print(f"\nRow {i+1}:")
    print(f"  Title ({len(t_lines)} lines, max={max(len(l) for l in t_lines)} chars):", t_lines)
    print(f"  Conseq ({len(c_lines)} lines, max={max(len(l) for l in c_lines)} chars):", c_lines)
    print(f"  Resp ({len(r_lines)} lines, max={max(len(l) for l in r_lines)} chars):", r_lines)
    
    # Check max widths:
    for l in t_lines:
        assert len(l) * 18.0 <= 632, f"Title line too long: {l}"
    for l in c_lines:
        assert len(l) * 14.4 <= 694, f"Conseq line too long: {l}"
    for l in r_lines:
        assert len(l) * 14.4 <= 694, f"Resp line too long: {l}"

print("\nALL LINES FIT WITHIN BOXES WITH >= 18px PADDING ON BOTH SIDES!")
