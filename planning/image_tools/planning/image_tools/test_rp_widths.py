#!/usr/bin/env python3

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

principles = [
    "choose the metric that represents work: connections, requests, tokens and GPU-seconds differ",
    "many LB instances each doing local least connections herd onto the same backend, like drivers following one satnav to one empty car park; a randomised pick breaks it up",
    "hash affinity serves cache locality and state but accepts uneven load: plan for reshuffling with consistent or resilient hashing",
    "slow start ramps up the weight of a new or recovered backend while its JIT, caches and GPU warm up"
]

for rp_w in [420, 440, 460, 480, 500]:
    inner_w = rp_w - 40 # 20px padding each side
    max_c = int(inner_w / 14.4)
    total_lines = sum(len(wrap_text(p, max_c)) for p in principles)
    print(f"Right panel w={rp_w}, inner_w={inner_w}, max_c={max_c} -> total lines={total_lines}")
    for p in principles:
        print(f"   {len(wrap_text(p, max_c))} lines: {wrap_text(p, max_c)[0]}...")
