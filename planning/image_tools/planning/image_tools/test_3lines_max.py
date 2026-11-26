#!/usr/bin/env python3

# Let's test if Col 1 = 350, Col 2 = 300, Col 3 = 390
# 350 + 20 + 300 + 20 + 390 = 1080 px!
# Table width = 1080 px.
# Canvas width = 1600.
# Left margin = 40.
# Table x = 40..1120.
# Gap = 30 px.
# Right Panel x = 1150..1560 (width = 410 px).
# Right margin = 40 px (1560 + 40 = 1600).

rows = [
    # Row 1
    (
        ["Short stateless", "equal requests"],
        ["round robin or", "weighted round robin"],
        ["ignores request cost", "and backend load"]
    ),
    # Row 2 (3 lines each!)
    (
        ["Long-lived connections", "or variable-length", "requests"],
        ["least connections"],
        ["counts connections, not", "work; needs shared state", "across LB instances"]
    ),
    # Row 3
    (
        ["HTTP or gRPC requests"],
        ["least outstanding requests"],
        ["same, request-granular"]
    ),
    # Row 4
    (
        ["Heterogeneous backends"],
        ["least response time,", "EWMA, peak-EWMA"],
        ["needs measurement; can", "oscillate (herding)"]
    ),
    # Row 5 (orange on pitfall)
    (
        ["Large pools with", "imperfect load info"],
        ["power of two", "random choices"],
        ["needs load info per backend"]
    ),
    # Row 6
    (
        ["Session affinity or", "cache locality"],
        ["source, URL or", "header hash"],
        ["remaps most keys", "when N changes"]
    ),
    # Row 7
    (
        ["Caches, sticky sessions,", "sharded stores"],
        ["consistent hashing", "(ring, rendezvous,", "jump hash)"],
        ["load imbalance; virtual", "nodes help; hot keys"]
    ),
    # Row 8
    (
        ["L4 LBs behind ECMP"],
        ["Maglev hashing"],
        ["table rebuild cost; small", "disruption on change"]
    ),
    # Row 9
    (
        ["Cost and latency"],
        ["locality or zone-aware"],
        ["capacity imbalance across", "zones"]
    ),
    # Row 10
    (
        ["DR and spillover"],
        ["priority or failover groups"],
        ["cold backups"]
    ),
    # Row 11
    (
        ["LLM inference"],
        ["load-aware custom: GPU,", "queue, KV-cache"],
        ["needs telemetry; careful", "staleness handling"]
    )
]

w1 = 350
w2 = 300
w3 = 390
fs = 24

def check_col(name, lines, box_w):
    max_avail = box_w - 32
    for l in lines:
        w = len(l) * 0.6 * fs
        pad = (box_w - w) / 2
        if pad < 16:
            print(f"FAIL {name}: '{l}' w={w:.1f}, pad={pad:.1f} < 16 in {box_w}")
            return False
    return True

all_pass = True
for i, (c1, c2, c3) in enumerate(rows, 1):
    m_lines = max(len(c1), len(c2), len(c3))
    print(f"Row {i:2d} (max {m_lines} lines):")
    if not check_col("Col1", c1, w1): all_pass = False
    if not check_col("Col2", c2, w2): all_pass = False
    if not check_col("Col3", c3, w3): all_pass = False

print("\nResult:", "ALL PASS!" if all_pass else "FAIL!")
