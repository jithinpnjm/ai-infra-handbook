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

# Let's write an optimizer that directly computes the coordinates for each box:
# Target: pad_top >= 18, pad_bottom >= 18, pad_left >= 18, pad_right >= 18.

def compute_diff_box(by, title_lines, conseq_lines, title_fs=30, conseq_fs=24, title_lh=32, conseq_lh=25):
    # Title top must have pad >= 18:
    # t_y0 - 0.75 * title_fs - by >= 18 -> t_y0 >= by + 18 + 0.75 * title_fs
    t_y0 = by + 18 + int(0.75 * title_fs + 0.99) # by + 41
    t_last_y = t_y0 + (len(title_lines) - 1) * title_lh
    t_bottom_g = t_last_y + 0.25 * title_fs
    
    # Conseq top must be below title bottom:
    # c_y0 - 0.75 * conseq_fs >= t_bottom_g + 8
    c_y0 = int(t_bottom_g + 8 + 0.75 * conseq_fs + 0.99)
    c_last_y = c_y0 + (len(conseq_lines) - 1) * conseq_lh
    c_bottom_g = c_last_y + 0.25 * conseq_fs
    
    # Box bottom must be >= c_bottom_g + 18:
    min_bh = int(c_bottom_g + 18 - by + 0.99)
    return t_y0, c_y0, min_bh

def compute_resp_box(by, resp_lines, resp_fs=24, resp_lh=25):
    r_y0 = by + 18 + int(0.75 * resp_fs + 0.99) # by + 36
    r_last_y = r_y0 + (len(resp_lines) - 1) * resp_lh
    r_bottom_g = r_last_y + 0.25 * resp_fs
    min_bh = int(r_bottom_g + 18 - by + 0.99)
    return r_y0, min_bh

print("Computing exact minimum heights:")
# Row 1:
t1 = wrap_text("1 Requests are long, variable and somewhat stateful", 32)
c1 = wrap_text("a request may stream tokens for minutes; cost varies by orders of magnitude with prompt and output length; the real load is queue depth, running sequences and KV-cache occupancy, not connection count", 46)
r1 = wrap_text("Balance per request, not per connection (Envoy, HAProxy, nginx grpc_pass, Gateway API inference extensions, or client-side)", 42)
ty1, cy1, h1_d = compute_diff_box(0, t1, c1, title_lh=32, conseq_lh=25)
ry1, h1_r = compute_resp_box(0, r1, resp_lh=26)
h1 = max(h1_d, h1_r)
print(f"Row 1: diff_h={h1_d}, resp_h={h1_r} -> h1={h1}")

# Row 2:
t2 = ["2 Connections are long-lived"]
c2 = wrap_text("HTTP/2 and gRPC streams and SSE hold resources; reloads, scale-in and deploys must drain gracefully; an idle timeout at any hop can cut a slow generation", 46)
r2 = wrap_text("load signal: least-outstanding-requests baseline, better backend-reported running and waiting requests, KV-cache usage and estimated tokens (Prometheus, headers, ORCA-style load reports), P2C over load", 42)
ty2, cy2, h2_d = compute_diff_box(0, t2, c2, title_lh=32, conseq_lh=25)
ry2, h2_r = compute_resp_box(0, r2, resp_lh=25)
h2 = max(h2_d, h2_r)
print(f"Row 2: diff_h={h2_d}, resp_h={h2_r} -> h2={h2}")

# Row 3:
t3 = ["3 Cache locality matters"]
c3 = wrap_text("prefix caching for system prompts, RAG context and multi-turn chat makes a request cheaper on the replica that already holds its prefix KV blocks; same session or prefix to the same replica raises hit rates, pure affinity creates hot spots", 46)
r3 = wrap_text("cache-aware: consistent hashing on session ID or prefix hash with bounded loads, or a router tracking which replica holds which prefix blocks", 42)
ty3, cy3, h3_d = compute_diff_box(0, t3, c3, title_lh=32, conseq_lh=25)
ry3, h3_r = compute_resp_box(0, r3, resp_lh=26)
h3 = max(h3_d, h3_r)
print(f"Row 3: diff_h={h3_d}, resp_h={h3_r} -> h3={h3}")

# Row 4:
t4 = wrap_text("4 Backends are expensive and heterogeneous", 28)
c4 = wrap_text("GPU types, tensor-parallel group sizes, disaggregated prefill and decode pools, LoRA adapters per replica, quantised variants", 46)
r4 = wrap_text("disaggregated: route prefill and decode to separate pools, handle the KV transfer, couple the autoscaling and admission", 42)
ty4, cy4, h4_d = compute_diff_box(0, t4, c4, title_lh=30, conseq_lh=25)
ry4, h4_r = compute_resp_box(0, r4, resp_lh=26)
h4 = max(h4_d, h4_r)
print(f"Row 4: diff_h={h4_d}, resp_h={h4_r} -> h4={h4}")

# Row 5:
t5 = ["5 Autoscaling is slow"]
c5 = wrap_text("GPU nodes and model loads take minutes, so the router must absorb bursts by queueing or shedding", 46)
r5 = wrap_text("overload: per-tenant concurrency and token-rate limits, priority queues separating interactive from batch, 429 or 503 early, KV-cache headroom in admission control", 42)
ty5, cy5, h5_d = compute_diff_box(0, t5, c5, title_lh=32, conseq_lh=25)
ry5, h5_r = compute_resp_box(0, r5, resp_lh=25)
h5 = max(h5_d, h5_r)
print(f"Row 5: diff_h={h5_d}, resp_h={h5_r} -> h5={h5}")

# Scenario:
sc_lines = wrap_text("every health check green, average latency fine, one replica buried under long generations while the others sit idle", 42)
sc_y0, sc_h = compute_resp_box(0, sc_lines, resp_lh=26)
print(f"Scenario: h={sc_h}")

# Bottom bar:
bb_lines = ["Measure first, and choose the load signal before you choose the algorithm"]
bb_y0, bb_h = compute_resp_box(0, bb_lines, resp_lh=24)
print(f"Bottom bar: h={bb_h}")

total = sc_h + h1 + h2 + h3 + h4 + h5 + bb_h
print(f"Total box heights: {total}")
