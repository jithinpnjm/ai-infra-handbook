#!/usr/bin/env python3

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

principles = [
    "choose the metric that represents work: connections, requests, tokens and GPU-seconds differ",
    "many LB instances each doing local least connections herd onto the same backend, like drivers following one satnav to one empty car park; a randomised pick breaks it up",
    "hash affinity serves cache locality and state but accepts uneven load: plan for reshuffling with consistent or resilient hashing",
    "slow start ramps up the weight of a new or recovered backend while its JIT, caches and GPU warm up"
]

for rp_w in [380, 390, 400]:
    inner_card_w = rp_w - 36 # 18px padding inside right panel
    print(f"\n=== RP_W = {rp_w}, card_w = {inner_card_w} ===")
    total_lines = 0
    for p in principles:
        lines = get_best_wrap(p, inner_card_w)
        total_lines += len(lines)
        print(f"  {len(lines)} lines: {lines}")
    print(f"Total lines: {total_lines}")
