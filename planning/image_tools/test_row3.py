#!/usr/bin/env python3

def test_box(name, text, w, pad=24):
    max_w = w - 2 * pad
    max_chars = int(max_w / 14.4)
    print(f"--- {name} (w={w}, max_w={max_w}, max_chars={max_chars}) ---")
    words = text.split()
    lines = []
    cur = []
    for word in words:
        cand = " ".join(cur + [word])
        if len(cand) <= max_chars:
            cur.append(word)
        else:
            if cur:
                lines.append(" ".join(cur))
                cur = [word]
            else:
                lines.append(word)
                cur = []
    if cur:
        lines.append(" ".join(cur))
    for i, line in enumerate(lines, 1):
        lw = len(line) * 14.4
        print(f"  Line {i}: ({len(line):2d} ch, {lw:5.1f}px <= {max_w}px) '{line}'")
    return lines

side_text = "a Service with no ready endpoints: iptables REJECT sends ICMP port unreachable, client sees connection refused immediately; empty kubectl get endpointslices means selector mismatch or unready pods"
fix_text = "preStop sleep plus graceful shutdown (5.7)"

s = test_box("Side Box", side_text, 1030)
f = test_box("Fix Box", fix_text, 450)
