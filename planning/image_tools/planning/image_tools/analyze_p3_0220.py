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

principles = [
    "choose the metric that represents work: connections, requests, tokens and GPU-seconds differ",
    "many LB instances each doing local least connections herd onto the same backend, like drivers following one satnav to one empty car park; a randomised pick breaks it up",
    "hash affinity serves cache locality and state but accepts uneven load: plan for reshuffling with consistent or resilient hashing",
    "slow start ramps up the weight of a new or recovered backend while its JIT, caches and GPU warm up"
]

print("=== ROW TEXT LENGTHS ===")
for i, (u, a, p) in enumerate(rows, 1):
    print(f"Row {i:2d}:")
    print(f"  Unit:      len={len(u):2d} | '{u}'")
    print(f"  Algorithm: len={len(a):2d} | '{a}'")
    print(f"  Pitfall:   len={len(p):2d} | '{p}'")

print("\n=== PRINCIPLES TEXT LENGTHS ===")
for i, pr in enumerate(principles, 1):
    print(f"Principle {i}: len={len(pr):3d} | '{pr}'")
