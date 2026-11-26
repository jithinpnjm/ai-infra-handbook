#!/usr/bin/env python3

rows = [
    (
        "Short stateless equal requests",
        "round robin or weighted round robin",
        "ignores request cost and backend load"
    ),
    (
        "Long-lived connections or variable-length requests",
        "least connections",
        "counts connections, not work; needs shared state across LB instances"
    ),
    (
        "HTTP or gRPC requests",
        "least outstanding requests",
        "same, request-granular"
    ),
    (
        "Heterogeneous backends",
        "least response time, EWMA, peak-EWMA",
        "needs measurement; can oscillate (herding)"
    ),
    (
        "Large pools with imperfect load info",
        "power of two random choices",
        "needs load info per backend"
    ),
    (
        "Session affinity or cache locality",
        "source, URL or header hash",
        "remaps most keys when N changes"
    ),
    (
        "Caches, sticky sessions, sharded stores",
        "consistent hashing (ring, rendezvous, jump hash)",
        "load imbalance; virtual nodes help; hot keys"
    ),
    (
        "L4 LBs behind ECMP",
        "Maglev hashing",
        "table rebuild cost; small disruption on change"
    ),
    (
        "Cost and latency",
        "locality or zone-aware",
        "capacity imbalance across zones"
    ),
    (
        "DR and spillover",
        "priority or failover groups",
        "cold backups"
    ),
    (
        "LLM inference",
        "load-aware custom: GPU, queue, KV-cache",
        "needs telemetry; careful staleness handling"
    )
]

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if not cur:
            cur.append(w)
            cur_len = len(w)
        elif cur_len + 1 + len(w) <= max_chars:
            cur.append(w)
            cur_len += 1 + len(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

col1_w = 280
col2_w = 310
col3_w = 390

# Padding at least 16px each side -> text_w = w - 32
max_c1 = int((col1_w - 32) / 14.4) # 17
max_c2 = int((col2_w - 32) / 14.4) # 19
max_c3 = int((col3_w - 32) / 14.4) # 24

print(f"Max chars: Col1={max_c1}, Col2={max_c2}, Col3={max_c3}")
for i, (u, a, p) in enumerate(rows, 1):
    u_lines = wrap_text(u, max_c1)
    a_lines = wrap_text(a, max_c2)
    p_lines = wrap_text(p, max_c3)
    print(f"Row {i:2d}: c1={len(u_lines)} c2={len(a_lines)} c3={len(p_lines)} -> max={max(len(u_lines), len(a_lines), len(p_lines))}")
    if max(len(u_lines), len(a_lines), len(p_lines)) >= 3:
        print(f"   Col1: {u_lines}")
        print(f"   Col2: {a_lines}")
        print(f"   Col3: {p_lines}")
