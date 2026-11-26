#!/usr/bin/env python3
# Test 10 full-width cards in Column 1 and 9 cards in Column 2

col_w = 600
# Text width available inside full-width card:
# card_w = 560
# icon: x = 16, w = 56, gap = 16 -> text_x = 88
# text_w = 560 - 88 - 16 = 456 px!
# At 24px font: chars_per_line = 456 / (24 * 0.6) = 31.6 chars per line!

ipv4_texts = [
    "Version 4",
    "IHL: header length in 32-bit words, 5 means 20 bytes",
    "DSCP (6 bits) and ECN (2 bits)",
    "Total Length up to 65,535",
    "Identification, Flags (DF, MF), Fragment Offset: fragmentation lives in the base header; routers may fragment unless DF is set",
    "TTL: drops by one per router, at 0 the router drops the packet and sends ICMP Time Exceeded",
    "Protocol: 6 TCP, 17 UDP, 1 ICMP, 47 GRE, 50 ESP, 89 OSPF",
    "Header checksum: recomputed at every hop because the TTL changes",
    "source and destination 32-bit addresses",
    "options (rare)"
]

ipv6_texts = [
    "Version 4 bits",
    "Traffic Class 8 bits = DSCP 6 + ECN 2",
    "Flow Label 20 bits: helps routers keep a flow on one path when ECMP spreads traffic",
    "Payload Length 16",
    "Hop Limit 8: plays the role of the TTL",
    "Next Header 8: extension headers chained (hop-by-hop, routing, fragment, destination options, AH, ESP)",
    "no header checksum (link and transport layers cover errors)",
    "no fragmentation fields in the base header: only the source host may fragment, through an extension header; routers never do",
    "source and destination 128-bit addresses"
]

print("IPv4 lines needed:")
for t in ipv4_texts:
    # simple estimate
    lines = (len(t) + 30) // 31
    print(f"  {lines} lines ({len(t)} chars): {t[:30]}...")

print("\nIPv6 lines needed:")
for t in ipv6_texts:
    lines = (len(t) + 30) // 31
    print(f"  {lines} lines ({len(t)} chars): {t[:30]}...")
