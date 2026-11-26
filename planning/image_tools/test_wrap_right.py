def wrap_text(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return lines

labels_right = [
    ("capture on the server interface", False),
    ("capture on the client interface; the offload caveat still applies", False),
    ("nsenter -t PID -n tcpdump", True),
    ("bridge or veth host-side; compare both ends of a veth", False),
    ("switch port mirror (SPAN, ERSPAN) or TAP; mirrored traffic can be dropped under congestion", False),
    ("NIC or DPU capture: tcpdump -i mlx5_0 with rdma-core, ibdump, or a switch mirror", False),
    ("tracepoints, kfree_skb, pwru; complement, do not replace, pcap", False)
]

# Right box width: 830 px.
# Left margin to icon = 20, icon = 50, gap = 20 -> text starts at 90 from box left.
# Available text width = 830 - 90 - 20 = 720 px.
# At 25px:
# sans: 0.6 * 25 = 15 px/char -> 720 / 15 = 48 chars.
# mono: 0.62 * 25 = 15.5 px/char -> 720 / 15.5 = 46.4 chars.
# At 24px:
# sans: 0.6 * 24 = 14.4 px/char -> 720 / 14.4 = 50 chars.
# mono: 0.62 * 24 = 14.88 px/char -> 720 / 14.88 = 48.3 chars.

print("=== RIGHT COLUMN at 25px ===")
for lr, is_m in labels_right:
    max_c = 44 if is_m else 45
    lines = wrap_text(lr, max_c)
    print(f"Original ({len(lr)}): '{lr}'")
    for line in lines:
        factor = 0.62 if is_m else 0.6
        w = len(line) * 25 * factor
        print(f"   [{len(line)} chars, {w:.1f}px] : '{line}'")

