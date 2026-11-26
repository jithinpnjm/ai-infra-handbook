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

# Let's check how long each string is and how wide a column must be to hold it in 2 lines:
for i, (u, a, p) in enumerate(rows, 1):
    print(f"Row {i:2d}:")
    print(f"  u: len={len(u):2d}, w_est={len(u)*14.4:.1f}px | '{u}'")
    print(f"  a: len={len(a):2d}, w_est={len(a)*14.4:.1f}px | '{a}'")
    print(f"  p: len={len(p):2d}, w_est={len(p)*14.4:.1f}px | '{p}'")
