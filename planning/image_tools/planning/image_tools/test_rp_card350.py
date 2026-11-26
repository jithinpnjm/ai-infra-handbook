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

card_w = 350
fs = 24

all_ok = True
for i, p in enumerate(principles, 1):
    lines = get_best_wrap(p, card_w)
    print(f"\nPrinciple {i} ({len(lines)} lines):")
    for l in lines:
        w = len(l) * 0.6 * fs
        pad = (card_w - w) / 2
        ok = pad >= 16.0
        print(f"  w={w:5.1f}, pad={pad:4.1f} [{'OK' if ok else 'FAIL'}] '{l}'")
        if not ok:
            all_ok = False

print("\nRight Panel Status:", "ALL PASS!" if all_ok else "FAIL!")
