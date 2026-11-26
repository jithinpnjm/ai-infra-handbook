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

label2 = "hedge at the 95th percentile: duplicates 5 percent of requests, p99 from 4.02 to 3.57, about 11 percent better"
lines2 = wrap_to_max_chars(label2, 26)
print("=== Label 2 (max 26) ===")
for l in lines2:
    print(f"({len(l):2d}) {len(l)*14.4:5.1f}px : '{l}'")

label3 = "hedge at the 90th: duplicates 10 percent, p99 from 4.01 to 3.30, about 18 percent better"
lines3 = wrap_to_max_chars(label3, 26)
print("\n=== Label 3 (max 26) ===")
for l in lines3:
    print(f"({len(l):2d}) {len(l)*14.4:5.1f}px : '{l}'")

label4 = "gain per duplicate is modest and shrinks as the delay grows"
lines4 = wrap_to_max_chars(label4, 26)
print("\n=== Label 4 (max 26) ===")
for l in lines4:
    print(f"({len(l):2d}) {len(l)*14.4:5.1f}px : '{l}'")
