#!/usr/bin/env python3

w1 = 340
w2 = 320
w3 = 400
rp_w = 390 # 340 + 20 + 320 + 20 + 400 + 30 + 390 = 1520! Exact width!

rows_raw = [
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

def get_best_wrap(text, max_w, fs=24):
    max_char_w = max_w - 32
    words = text.split()
    lines = []
    cur = []
    for w in words:
        cand = (" ".join(cur + [w])) if cur else w
        if len(cand) * 0.6 * fs <= max_char_w:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

for i, (u, a, p) in enumerate(rows_raw, 1):
    u_l = get_best_wrap(u, w1)
    a_l = get_best_wrap(a, w2)
    p_l = get_best_wrap(p, w3)
    print(f"Row {i:2d}: ({len(u_l)}, {len(a_l)}, {len(p_l)})")
    print(f"   Col1: {u_l}")
    print(f"   Col2: {a_l}")
    print(f"   Col3: {p_l}")
