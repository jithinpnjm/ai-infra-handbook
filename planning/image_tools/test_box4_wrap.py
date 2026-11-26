#!/usr/bin/env python3

text = "Inode C: type, permissions, owner, size, times, link count, pointers to data blocks"
words = text.split()

def wrap_words(words, max_w):
    lines = []
    cur = []
    for w in words:
        trial = " ".join(cur + [w])
        if len(trial) * 24 * 0.6 <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

for target in [220, 240, 260, 280, 300, 320]:
    lines = wrap_words(words, target)
    max_line_len = max(len(l) for l in lines)
    max_line_w = max_line_len * 24 * 0.6
    print(f"Target {target}px: {len(lines)} lines, max_w={max_line_w:.1f}px (len={max_line_len})")
    for l in lines:
        print(f"   '{l}' ({len(l)} chars, {len(l)*24*0.6:.1f}px)")
