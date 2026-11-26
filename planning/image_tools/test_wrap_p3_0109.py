#!/usr/bin/env python3
import xml.etree.ElementTree as ET
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

# Let's test wrapping the descriptions
d1 = "removes the longest matching prefix up to the last slash: result 'model.final.ckpt' (same as basename)"
d2 = "removes the shortest matching suffix starting at the last slash: result '/data/run42' (same as dirname)"
d3 = "removes the shortest suffix starting at the last dot: result '/data/run42/model.final'"
d4 = "removes the longest prefix up to the last dot: result 'ckpt'"

print("Wrap at 50 chars:")
for d in [d1, d2, d3, d4]:
    lines = wrap_text(d, 50)
    print("Lines:", len(lines))
    for l in lines:
        w = len(l) * 24 * 0.6
        print(f"  {w:5.1f}px: {l}")
