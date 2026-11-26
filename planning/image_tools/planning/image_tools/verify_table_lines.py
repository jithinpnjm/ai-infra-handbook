#!/usr/bin/env python3

# Layout widths:
w1 = 340 # Col 1 (Unit of work)
a1 = 20  # Arrow 1
w2 = 320 # Col 2 (Algorithm)
a2 = 20  # Arrow 2
w3 = 410 # Col 3 (Pitfall)
gap = 30 # Gap to Right Panel
rp_w = 380 # Right Panel

# Total = 340 + 20 + 320 + 20 + 410 + 30 + 380 = 1520 px!
# Margins = 40 left, 40 right -> 1520 + 80 = 1600 px! EXACT!

# Text specifications:
rows_plan = [
    # Row 1
    (
        ["Short stateless", "equal requests"],
        ["round robin or", "weighted round robin"],
        ["ignores request cost", "and backend load"]
    ),
    # Row 2 (3 lines)
    (
        ["Long-lived", "connections or", "variable-length requests"], # wait, check len of line 3
        ["least connections"],
        ["counts connections, not", "work; needs shared state", "across LB instances"]
    ),
    # Row 3
    (
        ["HTTP or gRPC requests"],
        ["least outstanding", "requests"],
        ["same, request-granular"]
    ),
    # Row 4
    (
        ["Heterogeneous", "backends"],
        ["least response time,", "EWMA, peak-EWMA"],
        ["needs measurement; can", "oscillate (herding)"]
    ),
    # Row 5 (orange on pitfall)
    (
        ["Large pools with", "imperfect load info"],
        ["power of two", "random choices"],
        ["needs load info", "per backend"]
    ),
    # Row 6
    (
        ["Session affinity or", "cache locality"],
        ["source, URL or", "header hash"],
        ["remaps most keys", "when N changes"]
    ),
    # Row 7 (3 lines)
    (
        ["Caches, sticky", "sessions, sharded", "stores"],
        ["consistent hashing", "(ring, rendezvous,", "jump hash)"],
        ["load imbalance; virtual", "nodes help; hot keys"]
    ),
    # Row 8
    (
        ["L4 LBs behind ECMP"],
        ["Maglev hashing"],
        ["table rebuild cost;", "small disruption on change"]
    ),
    # Row 9
    (
        ["Cost and latency"],
        ["locality or", "zone-aware"],
        ["capacity imbalance", "across zones"]
    ),
    # Row 10
    (
        ["DR and spillover"],
        ["priority or failover", "groups"],
        ["cold backups"]
    ),
    # Row 11
    (
        ["LLM inference"],
        ["load-aware custom:", "GPU, queue, KV-cache"],
        ["needs telemetry; careful", "staleness handling"]
    )
]

# Let's check padding of each line in each column:
fs = 24
cols = [("Col1", w1), ("Col2", w2), ("Col3", w3)]

all_ok = True
for r_idx, row in enumerate(rows_plan, 1):
    print(f"\n--- Row {r_idx} ---")
    for c_idx, lines in enumerate(row):
        c_name, box_w = cols[c_idx]
        for l in lines:
            w = len(l) * 0.6 * fs
            pad = (box_w - w) / 2
            ok = pad >= 16.0
            print(f"  {c_name} (w={box_w}): len={len(l):2d}, w={w:5.1f}, pad={pad:4.1f} [{'OK' if ok else 'FAIL'}] '{l}'")
            if not ok:
                all_ok = False

print("\nTable lines verification:", "ALL PASS!" if all_ok else "FAILURES FOUND!")
