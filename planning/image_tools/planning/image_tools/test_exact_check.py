#!/usr/bin/env python3

w1 = 360
w2 = 324
w3 = 382

cols = [("Col1", w1), ("Col2", w2), ("Col3", w3)]

rows_plan = [
    # Row 1
    (
        ["Short stateless", "equal requests"],
        ["round robin or", "weighted round robin"],
        ["ignores request cost", "and backend load"]
    ),
    # Row 2 (3 lines)
    (
        ["Long-lived connections", "or variable-length", "requests"],
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
        ["table rebuild cost;", "small disruption", "on change"]
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

fs = 24
all_ok = True
for r_idx, row in enumerate(rows_plan, 1):
    for c_idx, lines in enumerate(row):
        c_name, box_w = cols[c_idx]
        for l in lines:
            w = len(l) * 0.6 * fs
            pad = (box_w - w) / 2
            ok = pad >= 16.0
            if not ok:
                print(f"Row {r_idx} FAIL: {c_name} '{l}' w={w:.1f}, pad={pad:.1f} in {box_w}")
                all_ok = False

if all_ok:
    print("ALL TABLE LINES PASS HORIZONTAL PADDING (>= 16 PX)!")
else:
    print("SOME LINES FAILED!")
