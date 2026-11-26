#!/usr/bin/env python3

label1 = "lines 1-2: finding the link address because the client needs the server's MAC before it can send a frame"
label2 = "lines 3-5: three-way handshake"
label3 = "lines 6-9: data"

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

for max_c in range(25, 45):
    l = wrap_text(label1, max_c)
    max_w = max(len(line) * 0.6 * 24 for line in l)
    print(f"max_chars={max_c}: {len(l)} lines, max_w={max_w:.1f}px")
    for line in l:
        print(f"   '{line}' ({len(line)} chars, {len(line)*0.6*24:.1f}px)")
    print()
    if len(l) <= 4:
        break
