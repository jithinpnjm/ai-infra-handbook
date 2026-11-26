def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

c2_texts = {
    "r1_c2": "a RST came back: host reachable, nobody listening on that port, or a firewall using reject --tcp-reset",
    "r2_c2": "no reply to the SYNs, retried with exponential backoff 1, 2, 4 seconds and so on; tcp_syn_retries=6 gives about 127 seconds",
    "r3_c2": "ICMP unreachable from a router, or no local route",
    "r4_c2": "a RST during an established connection"
}

c3_texts = {
    "r1_c3": "the listener: somebody was home and said no",
    "r2_c3": "route and firewall or security group, host down: nobody answered the door at all",
    "r3_c3": "the routing table (chapter 2.5)",
    "r4_c3": "peer crashed, app closed with unread data, firewall or NAT state expired, load balancer idle timeout"
}

print("Col 2 wrapped at 29 chars:")
for k, t in c2_texts.items():
    lines = wrap_text(t, 29)
    print(f"{k} ({len(lines)} lines):")
    for l in lines:
        w = len(l) * 0.6 * 24
        print(f"   '{l}' (len={len(l)}, w={w:.1f}, pad_r={480 - 24 - w:.1f})")

print("\nCol 3 wrapped at 21 chars:")
for k, t in c3_texts.items():
    lines = wrap_text(t, 21)
    print(f"{k} ({len(lines)} lines):")
    for l in lines:
        w = len(l) * 0.6 * 24
        print(f"   '{l}' (len={len(l)}, w={w:.1f}, pad_r={360 - 24 - w:.1f})")
