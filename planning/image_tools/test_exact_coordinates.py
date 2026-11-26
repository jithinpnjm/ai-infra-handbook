#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Let's define the exact layout and verify all constraints

# Height = 1200, Width = 1600
# Background: #f5f8f5
# Margins: outside left=40, right=40, top=15, bottom=20

# Column 1 (IPv4): x = 40 to 660 (width = 620)
# Middle Corridor (arrows): x = 660 to 940 (width = 280)
# Column 2 (IPv6): x = 940 to 1560 (width = 620)

# Inside Column 1: card x = 58, width = 584 (left pad inside col = 18, right pad = 18)
# Inside Column 2: card x = 958, width = 584

# Usable text width inside card (width 584):
# icon at x = 74, width = 44, right = 118
# text starts at x = 134
# right edge of card = 58 + 584 = 642
# right pad = 16 -> max text right = 626
# usable text width = 626 - 134 = 492 px
# at 24px font: 492 / 14.4 = 34.1 chars per line!

print("Testing exact wrapping with max_len = 34:")

def wrap_text(text, max_len=34):
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

# Let's inspect the exact lines
ipv4_labels = [
    "Version 4",
    "DSCP (6 bits) and ECN (2 bits)",
    "IHL: header length in 32-bit words, 5 means 20 bytes",
    "Total Length up to 65,535",
    "Identification, Flags (DF, MF), Fragment Offset: fragmentation lives in the base header; routers may fragment unless DF is set",
    "TTL: drops by one per router, at 0 the router drops the packet and sends ICMP Time Exceeded",
    "Protocol: 6 TCP, 17 UDP, 1 ICMP, 47 GRE, 50 ESP, 89 OSPF",
    "Header checksum: recomputed at every hop because the TTL changes",
    "source and destination 32-bit addresses",
    "options (rare)"
]

ipv6_labels = [
    "Version 4 bits",
    "Traffic Class 8 bits = DSCP 6 + ECN 2",
    "Flow Label 20 bits: helps routers keep a flow on one path when ECMP spreads traffic",
    "Payload Length 16",
    "no fragmentation fields in the base header: only the source host may fragment, through an extension header; routers never do",
    "Hop Limit 8: plays the role of the TTL",
    "Next Header 8: extension headers chained (hop-by-hop, routing, fragment, destination options, AH, ESP)",
    "no header checksum (link and transport layers cover errors)",
    "source and destination 128-bit addresses"
]

for t in ipv4_labels:
    w = wrap_text(t, 34)
    print(f"IPv4 [{len(w)} lines, max={max(len(l) for l in w)}]: {w}")

print()
for t in ipv6_labels:
    w = wrap_text(t, 34)
    print(f"IPv6 [{len(w)} lines, max={max(len(l) for l in w)}]: {w}")
