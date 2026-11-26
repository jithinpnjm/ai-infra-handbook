#!/usr/bin/env python3
import re

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if cur_len > 0 else 0)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

label1 = "request is slow because one replica is slow; after a short delay (only on a per-try timeout) send a second copy to another replica without cancelling the first; use whichever answers first; cancel the loser at once"
lines1 = wrap_text(label1, 28)
print("Label 1 lines (max 28 chars):", len(lines1))
for l in lines1:
    print(f"  ({len(l):2d}) '{l}' -> {len(l)*0.6*24:.1f}px")

print("\n---")
label2 = "hedge at the 95th percentile: duplicates 5 percent of requests, p99 from 4.02 to 3.57, about 11 percent better"
lines2 = wrap_text(label2, 28)
print("Label 2 lines:", len(lines2))
for l in lines2:
    print(f"  ({len(l):2d}) '{l}' -> {len(l)*0.6*24:.1f}px")

print("\n---")
label3 = "hedge at the 90th: duplicates 10 percent, p99 from 4.01 to 3.30, about 18 percent better"
lines3 = wrap_text(label3, 28)
print("Label 3 lines:", len(lines3))
for l in lines3:
    print(f"  ({len(l):2d}) '{l}' -> {len(l)*0.6*24:.1f}px")

print("\n---")
label4 = "gain per duplicate is modest and shrinks as the delay grows"
lines4 = wrap_text(label4, 28)
print("Label 4 lines:", len(lines4))
for l in lines4:
    print(f"  ({len(l):2d}) '{l}' -> {len(l)*0.6*24:.1f}px")

print("\n---")
label5 = "a hedge repeats the whole prefill on a second GPU and holds KV cache until the loser is cancelled; 5 percent duplicates is roughly 5 percent more prefill work; a fleet at 80 percent utilisation moves to about 84 percent and queueing delay rises steeply near the top; independence fails exactly when you need hedging most"
lines5 = wrap_text(label5, 28)
print("Label 5 lines:", len(lines5))
for l in lines5:
    print(f"  ({len(l):2d}) '{l}' -> {len(l)*0.6*24:.1f}px")

print("\n---")
label6 = "hedge only before the first token, only for tail time to first token, only below a fleet utilisation threshold, only inside the retry budget"
lines6 = wrap_text(label6, 90)
print("Label 6 lines (rule box, width ~1400):", len(lines6))
for l in lines6:
    print(f"  ({len(l):2d}) '{l}' -> {len(l)*0.6*24:.1f}px")
