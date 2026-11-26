#!/usr/bin/env python3

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr and curr_len + 1 + len(w) > max_chars:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
        else:
            curr.append(w)
            curr_len = curr_len + 1 + len(w) if curr_len else len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

texts = {
    "col1_hdr": ("Error the client sees", 15), # 2 lines
    "col2_hdr": ("What actually happened on the wire", 20),
    "col3_hdr": ("Where to look", 15),
    "r1_c1": ("Connection refused (ECONNREFUSED)", 18),
    "r1_c2": ("a RST came back: host reachable, nobody listening on that port, or a firewall using reject --tcp-reset", 26),
    "r1_c3": ("the listener: somebody was home and said no", 22),
    "r2_c1": ("Connection timed out (ETIMEDOUT)", 18),
    "r2_c2": ("no reply to the SYNs, retried with exponential backoff 1, 2, 4 seconds and so on; tcp_syn_retries=6 gives about 127 seconds", 26),
    "r2_c3": ("route and firewall or security group, host down: nobody answered the door at all", 22),
    "r3_c1": ("No route to host or Network is unreachable", 16),
    "r3_c2": ("ICMP unreachable from a router, or no local route", 25),
    "r3_c3": ("the routing table (chapter 2.5)", 18),
    "r4_c1": ("Connection reset by peer", 17),
    "r4_c2": ("a RST during an established connection", 22),
    "r4_c3": ("peer crashed, app closed with unread data, firewall or NAT state expired, load balancer idle timeout", 22),
}

for k, (t, mc) in texts.items():
    lines = wrap_text(t, mc)
    max_w = max(len(ln) * 14.4 for ln in lines)
    print(f"{k:10s} (lines={len(lines)}, max_chars={max(len(ln) for ln in lines):2d}, max_w={max_w:5.1f}px):")
    for ln in lines:
        print(f"    '{ln}'")
