def wrap(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return lines

d = "c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame to c2's veth and eth0"
lines = wrap(d, 80)
print("Wrapped Lane 1 desc into", len(lines), "lines:")
for l in lines:
    w = len(l) * 24 * 0.6
    print(f"  len={len(l)}, width={w:.1f}px: {l}")
assert " ".join(lines) == d
