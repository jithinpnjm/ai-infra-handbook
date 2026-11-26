import re

font_size_body = 24
font_size_title = 30
char_w_body = 24 * 0.6 # 14.4
char_w_title = 30 * 0.6 # 18.0

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

scenario = "every health check green, average latency fine, one replica buried under long generations while the others sit idle"
print("Scenario (max 42 chars):")
for l in wrap_text(scenario, 42):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

c1 = "a request may stream tokens for minutes; cost varies by orders of magnitude with prompt and output length; the real load is queue depth, running sequences and KV-cache occupancy, not connection count"
print("\nC1 (max 46 chars):")
for l in wrap_text(c1, 46):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

c2 = "HTTP/2 and gRPC streams and SSE hold resources; reloads, scale-in and deploys must drain gracefully; an idle timeout at any hop can cut a slow generation"
print("\nC2 (max 46 chars):")
for l in wrap_text(c2, 46):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

c3 = "prefix caching for system prompts, RAG context and multi-turn chat makes a request cheaper on the replica that already holds its prefix KV blocks; same session or prefix to the same replica raises hit rates, pure affinity creates hot spots"
print("\nC3 (max 46 chars):")
for l in wrap_text(c3, 46):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

c4 = "GPU types, tensor-parallel group sizes, disaggregated prefill and decode pools, LoRA adapters per replica, quantised variants"
print("\nC4 (max 46 chars):")
for l in wrap_text(c4, 46):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

c5 = "GPU nodes and model loads take minutes, so the router must absorb bursts by queueing or shedding"
print("\nC5 (max 46 chars):")
for l in wrap_text(c5, 46):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

r1 = "Balance per request, not per connection (Envoy, HAProxy, nginx grpc_pass, Gateway API inference extensions, or client-side)"
print("\nR1 (max 42 chars):")
for l in wrap_text(r1, 42):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

r2 = "load signal: least-outstanding-requests baseline, better backend-reported running and waiting requests, KV-cache usage and estimated tokens (Prometheus, headers, ORCA-style load reports), P2C over load"
print("\nR2 (max 42 chars):")
for l in wrap_text(r2, 42):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

r3 = "cache-aware: consistent hashing on session ID or prefix hash with bounded loads, or a router tracking which replica holds which prefix blocks"
print("\nR3 (max 42 chars):")
for l in wrap_text(r3, 42):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

r4 = "disaggregated: route prefill and decode to separate pools, handle the KV transfer, couple the autoscaling and admission"
print("\nR4 (max 42 chars):")
for l in wrap_text(r4, 42):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")

r5 = "overload: per-tenant concurrency and token-rate limits, priority queues separating interactive from batch, 429 or 503 early, KV-cache headroom in admission control"
print("\nR5 (max 42 chars):")
for l in wrap_text(r5, 42):
    print(f"  '{l}' (chars: {len(l)}, width: {len(l)*char_w_body:.1f})")
