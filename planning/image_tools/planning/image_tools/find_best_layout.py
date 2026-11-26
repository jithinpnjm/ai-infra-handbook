#!/usr/bin/env python3

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
    # max chars that fit with 16px pad each side:
    max_char_w = max_w - 32
    words = text.split()
    
    # We want to partition words into minimum number of lines such that each line * 0.6 * fs <= max_char_w
    # If not possible, return None
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        w_len = len(w) * 0.6 * fs
        if w_len > max_char_w:
            return None # single word exceeds box!
        cand = (" ".join(cur + [w])) if cur else w
        if len(cand) * 0.6 * fs <= max_char_w:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

# Let's test combinations of (w1, w2, w3, rp_w)
# Total width = 1600. Margins: left 40, right 40 -> 1520 available.
# 1520 = w1 + 20 + w2 + 20 + w3 + 30 + rp_w = w1 + w2 + w3 + rp_w + 70
# So w1 + w2 + w3 + rp_w = 1450.

results = []

for w1 in range(260, 360, 10):
    for w2 in range(280, 360, 10):
        for w3 in range(350, 450, 10):
            rp_w = 1450 - (w1 + w2 + w3)
            if rp_w < 380 or rp_w > 480:
                continue
            
            # Check if all row items wrap nicely
            possible = True
            row_lines_count = []
            for u, a, p in rows_raw:
                u_lines = get_best_wrap(u, w1)
                a_lines = get_best_wrap(a, w2)
                p_lines = get_best_wrap(p, w3)
                if not u_lines or not a_lines or not p_lines:
                    possible = False
                    break
                row_lines_count.append(max(len(u_lines), len(a_lines), len(p_lines)))
            
            if possible:
                max_lines_overall = max(row_lines_count)
                sum_lines = sum(row_lines_count)
                results.append((max_lines_overall, sum_lines, w1, w2, w3, rp_w, row_lines_count))

results.sort()
print(f"Found {len(results)} valid configurations!")
for r in results[:10]:
    print(f"max_lines={r[0]}, sum_lines={r[1]} | w1={r[2]}, w2={r[3]}, w3={r[4]}, rp_w={r[5]} | line counts={r[6]}")
