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

boxes = {}

# Scenario box:
boxes['scenario'] = {
    'box': (40, 96, 740, 102),
    'text': wrap_text("every health check green, average latency fine, one replica buried under long generations while the others sit idle", 42),
    'fs': 24,
    'x': 114,
    'y0': 130,
    'lh': 25
}

# Row 1:
boxes['row1_diff'] = {
    'box': (40, 206, 740, 218),
    'title': wrap_text("1 Requests are long, variable and somewhat stateful", 32),
    'title_fs': 30,
    'title_x': 112,
    'title_y0': 244,
    'title_lh': 32,
    'conseq': wrap_text("a request may stream tokens for minutes; cost varies by orders of magnitude with prompt and output length; the real load is queue depth, running sequences and KV-cache occupancy, not connection count", 46),
    'conseq_fs': 24,
    'conseq_x': 58,
    'conseq_y0': 304,
    'conseq_lh': 24
}
boxes['row1_resp'] = {
    'box': (820, 206, 740, 218),
    'text': wrap_text("Balance per request, not per connection (Envoy, HAProxy, nginx grpc_pass, Gateway API inference extensions, or client-side)", 42),
    'fs': 24,
    'x': 894,
    'y0': 252,
    'lh': 30
}

# Row 2:
boxes['row2_diff'] = {
    'box': (40, 432, 740, 156),
    'title': ["2 Connections are long-lived"],
    'title_fs': 30,
    'title_x': 112,
    'title_y0': 468,
    'title_lh': 32,
    'conseq': wrap_text("HTTP/2 and gRPC streams and SSE hold resources; reloads, scale-in and deploys must drain gracefully; an idle timeout at any hop can cut a slow generation", 46),
    'conseq_fs': 24,
    'conseq_x': 58,
    'conseq_y0': 502,
    'conseq_lh': 24
}
boxes['row2_resp'] = {
    'box': (820, 432, 740, 156),
    'text': wrap_text("load signal: least-outstanding-requests baseline, better backend-reported running and waiting requests, KV-cache usage and estimated tokens (Prometheus, headers, ORCA-style load reports), P2C over load", 42),
    'fs': 24,
    'x': 894,
    'y0': 464,
    'lh': 24
}

# Row 3:
boxes['row3_diff'] = {
    'box': (40, 596, 740, 222),
    'title': ["3 Cache locality matters"],
    'title_fs': 30,
    'title_x': 112,
    'title_y0': 632,
    'title_lh': 32,
    'conseq': wrap_text("prefix caching for system prompts, RAG context and multi-turn chat makes a request cheaper on the replica that already holds its prefix KV blocks; same session or prefix to the same replica raises hit rates, pure affinity creates hot spots", 46),
    'conseq_fs': 24,
    'conseq_x': 58,
    'conseq_y0': 668,
    'conseq_lh': 25
}
boxes['row3_resp'] = {
    'box': (820, 596, 740, 222),
    'text': wrap_text("cache-aware: consistent hashing on session ID or prefix hash with bounded loads, or a router tracking which replica holds which prefix blocks", 42),
    'fs': 24,
    'x': 894,
    'y0': 646,
    'lh': 28
}

# Row 4:
boxes['row4_diff'] = {
    'box': (40, 826, 740, 160),
    'title': wrap_text("4 Backends are expensive and heterogeneous", 28),
    'title_fs': 30,
    'title_x': 112,
    'title_y0': 860,
    'title_lh': 30,
    'conseq': wrap_text("GPU types, tensor-parallel group sizes, disaggregated prefill and decode pools, LoRA adapters per replica, quantised variants", 46),
    'conseq_fs': 24,
    'conseq_x': 58,
    'conseq_y0': 920,
    'conseq_lh': 24
}
boxes['row4_resp'] = {
    'box': (820, 826, 740, 160),
    'text': wrap_text("disaggregated: route prefill and decode to separate pools, handle the KV transfer, couple the autoscaling and admission", 42),
    'fs': 24,
    'x': 894,
    'y0': 868,
    'lh': 28
}

# Row 5:
boxes['row5_diff'] = {
    'box': (40, 994, 740, 134),
    'title': ["5 Autoscaling is slow"],
    'title_fs': 30,
    'title_x': 112,
    'title_y0': 1030,
    'title_lh': 32,
    'conseq': wrap_text("GPU nodes and model loads take minutes, so the router must absorb bursts by queueing or shedding", 46),
    'conseq_fs': 24,
    'conseq_x': 58,
    'conseq_y0': 1064,
    'conseq_lh': 24
}
boxes['row5_resp'] = {
    'box': (820, 994, 740, 134),
    'text': wrap_text("overload: per-tenant concurrency and token-rate limits, priority queues separating interactive from batch, 429 or 503 early, KV-cache headroom in admission control", 42),
    'fs': 24,
    'x': 894,
    'y0': 1024,
    'lh': 24
}

# Bottom bar:
boxes['bottom_bar'] = {
    'box': (40, 1136, 1520, 48),
    'text': ["Measure first, and choose the load signal before you choose the algorithm"],
    'fs': 24,
    'x': 800, # centered
    'y0': 1168,
    'lh': 24,
    'align': 'middle'
}

all_passed = True
for name, data in boxes.items():
    bx, by, bw, bh = data['box']
    box_right = bx + bw
    box_bottom = by + bh
    
    if 'title' in data:
        # Check title
        t_fs = data['title_fs']
        t_x = data['title_x']
        t_y0 = data['title_y0']
        t_lh = data['title_lh']
        t_lines = data['title']
        
        top_g = t_y0 - 0.75 * t_fs
        pad_top = top_g - by
        
        min_l = t_x - bx
        min_r = 999
        for line in t_lines:
            w = len(line) * t_fs * 0.6
            min_r = min(min_r, box_right - (t_x + w))
            
        # Consequence
        c_fs = data['conseq_fs']
        c_x = data['conseq_x']
        c_y0 = data['conseq_y0']
        c_lh = data['conseq_lh']
        c_lines = data['conseq']
        
        min_l = min(min_l, c_x - bx)
        for i, line in enumerate(c_lines):
            w = len(line) * c_fs * 0.6
            min_r = min(min_r, box_right - (c_x + w))
            bottom_g = c_y0 + i * c_lh + 0.25 * c_fs
            
        pad_bottom = box_bottom - bottom_g
        
    else:
        fs = data['fs']
        x = data['x']
        y0 = data['y0']
        lh = data['lh']
        lines = data['text']
        align = data.get('align', 'start')
        
        top_g = y0 - 0.75 * fs
        pad_top = top_g - by
        
        min_l = 999
        min_r = 999
        for i, line in enumerate(lines):
            w = len(line) * fs * 0.6
            if align == 'start':
                min_l = min(min_l, x - bx)
                min_r = min(min_r, box_right - (x + w))
            elif align == 'middle':
                min_l = min(min_l, (x - w/2) - bx)
                min_r = min(min_r, box_right - (x + w/2))
            bottom_g = y0 + i * lh + 0.25 * fs
            
        pad_bottom = box_bottom - bottom_g
        
    print(f"{name:12s}: L={min_l:5.1f}, R={min_r:5.1f}, T={pad_top:5.1f}, B={pad_bottom:5.1f}")
    if min_l < 16 or min_r < 16 or pad_top < 16 or pad_bottom < 16:
        print(f"  ❌ FAILED PADDING in {name}")
        all_passed = False

if all_passed:
    print("\n🎉 ALL BOXES PASSED STRICT >= 16px PADDING ON ALL SIDES!")
