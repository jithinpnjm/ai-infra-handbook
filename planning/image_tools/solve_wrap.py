#!/usr/bin/env python3
def wrap_to_max_chars(text, max_chars):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        cand_len = cur_len + len(w) + (1 if cur else 0)
        if cand_len <= max_chars:
            cur.append(w)
            cur_len = cand_len
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

label1 = "request is slow because one replica is slow; after a short delay (only on a per-try timeout) send a second copy to another replica without cancelling the first; use whichever answers first; cancel the loser at once"
lines1 = wrap_to_max_chars(label1, 26)
print("=== Label 1 (max 26) ===")
for l in lines1:
    print(f"({len(l):2d}) {len(l)*14.4:5.1f}px : '{l}'")

label5 = "a hedge repeats the whole prefill on a second GPU and holds KV cache until the loser is cancelled; 5 percent duplicates is roughly 5 percent more prefill work; a fleet at 80 percent utilisation moves to about 84 percent and queueing delay rises steeply near the top; independence fails exactly when you need hedging most"
lines5 = wrap_to_max_chars(label5, 26)
print("\n=== Label 5 (max 26) ===")
for l in lines5:
    print(f"({len(l):2d}) {len(l)*14.4:5.1f}px : '{l}'")
