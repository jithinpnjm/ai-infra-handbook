#!/usr/bin/env python3

rows = [
    # Row 1
    (
        ["Short stateless", "equal requests"],
        ["round robin or", "weighted round robin"],
        ["ignores request cost", "and backend load"]
    ),
    # Row 2
    (
        ["Long-lived connections", "or variable-length", "requests"],
        ["least connections"],
        ["counts connections, not", "work; needs shared state", "across LB instances"]
    ),
    # Row 3
    (
        ["HTTP or gRPC", "requests"],
        ["least outstanding", "requests"],
        ["same, request-granular"]
    ),
    # Row 4
    (
        ["Heterogeneous", "backends"],
        ["least response time,", "EWMA, peak-EWMA"],
        ["needs measurement;", "can oscillate (herding)"]
    ),
    # Row 5 (orange on pitfall)
    (
        ["Large pools with", "imperfect load info"],
        ["power of two", "random choices"],
        ["needs load info", "per backend"]
    ),
    # Row 6
    (
        ["Session affinity", "or cache locality"],
        ["source, URL or", "header hash"],
        ["remaps most keys", "when N changes"]
    ),
    # Row 7
    (
        ["Caches, sticky", "sessions, sharded stores"],
        ["consistent hashing", "(ring, rendezvous,", "jump hash)"],
        ["load imbalance; virtual", "nodes help; hot keys"]
    ),
    # Row 8
    (
        ["L4 LBs behind", "ECMP"],
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
        ["priority or", "failover groups"],
        ["cold backups"]
    ),
    # Row 11
    (
        ["LLM inference"],
        ["load-aware custom:", "GPU, queue, KV-cache"],
        ["needs telemetry; careful", "staleness handling"]
    )
]

w1 = 300
w2 = 320
w3 = 360

fs = 24

def check_lines(col_name, lines, box_w):
    max_avail = box_w - 32 # 16px padding on each side
    for line in lines:
        w = len(line) * 0.6 * fs
        ok = w <= max_avail
        pad_side = (box_w - w) / 2
        print(f"  {col_name}: w={w:5.1f} / {max_avail} (len={len(line):2d}, pad={pad_side:4.1f}) [{'OK' if ok else 'FAIL'}] '{line}'")
        if not ok:
            return False
    return True

all_ok = True
for i, (c1, c2, c3) in enumerate(rows, 1):
    print(f"\n--- Row {i} ---")
    if not check_lines("Col1", c1, w1): all_ok = False
    if not check_lines("Col2", c2, w2): all_ok = False
    if not check_lines("Col3", c3, w3): all_ok = False

print("\nOverall Status:", "ALL PASS!" if all_ok else "SOME OVERFLOW!")
