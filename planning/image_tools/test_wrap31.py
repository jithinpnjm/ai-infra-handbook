#!/usr/bin/env python3
def wrap_text(text, max_len=31):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_len:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

ipv4_texts = [
    ("Version 4", wrap_text("Version 4", 31)),
    ("DSCP", wrap_text("DSCP (6 bits) and ECN (2 bits)", 31)),
    ("IHL", wrap_text("IHL: header length in 32-bit words, 5 means 20 bytes", 31)),
    ("Total Length", wrap_text("Total Length up to 65,535", 31)),
    ("Identification", wrap_text("Identification, Flags (DF, MF), Fragment Offset: fragmentation lives in the base header; routers may fragment unless DF is set", 31)),
    ("TTL", wrap_text("TTL: drops by one per router, at 0 the router drops the packet and sends ICMP Time Exceeded", 31)),
    ("Protocol", wrap_text("Protocol: 6 TCP, 17 UDP, 1 ICMP, 47 GRE, 50 ESP, 89 OSPF", 31)),
    ("Header checksum", wrap_text("Header checksum: recomputed at every hop because the TTL changes", 31)),
    ("Addresses 32-bit", wrap_text("source and destination 32-bit addresses", 31)),
    ("options", wrap_text("options (rare)", 31)),
]

ipv6_texts = [
    ("Version 4 bits", wrap_text("Version 4 bits", 31)),
    ("Traffic Class", wrap_text("Traffic Class 8 bits = DSCP 6 + ECN 2", 31)),
    ("Flow Label", wrap_text("Flow Label 20 bits: helps routers keep a flow on one path when ECMP spreads traffic", 31)),
    ("Payload Length 16", wrap_text("Payload Length 16", 31)),
    ("no fragmentation fields", wrap_text("no fragmentation fields in the base header: only the source host may fragment, through an extension header; routers never do", 31)),
    ("Hop Limit 8", wrap_text("Hop Limit 8: plays the role of the TTL", 31)),
    ("Next Header 8", wrap_text("Next Header 8: extension headers chained (hop-by-hop, routing, fragment, destination options, AH, ESP)", 31)),
    ("no header checksum", wrap_text("no header checksum (link and transport layers cover errors)", 31)),
    ("Addresses 128-bit", wrap_text("source and destination 128-bit addresses", 31)),
]

print("=== IPv4 Wrapped (max 31) ===")
for name, lines in ipv4_texts:
    max_c = max(len(l) for l in lines)
    print(f"[{len(lines)} lines, {max_c} chars] {name}: {lines}")

print("\n=== IPv6 Wrapped (max 31) ===")
for name, lines in ipv6_texts:
    max_c = max(len(l) for l in lines)
    print(f"[{len(lines)} lines, {max_c} chars] {name}: {lines}")
