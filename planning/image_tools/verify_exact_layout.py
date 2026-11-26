#!/usr/bin/env python3
# Let's verify the exact positions and padding for IPv4 and IPv6

def test_layout():
    # Column 1
    # Card width = 610, x = 55 to 665
    # Text start x = 143
    # Text width = 506
    
    # Card heights:
    card_specs_4 = [
        ("Version 4", ["Version 4"], 72),
        ("IHL", ["IHL: header length in 32-bit words,", "5 means 20 bytes"], 80),
        ("DSCP", ["DSCP (6 bits) and ECN (2 bits)"], 72),
        ("Total Length", ["Total Length up to 65,535"], 72),
        ("Identification", [
            "Identification, Flags (DF, MF),",
            "Fragment Offset: fragmentation",
            "lives in the base header; routers",
            "may fragment unless DF is set"
        ], 136),
        ("TTL", [
            "TTL: drops by one per router, at 0",
            "the router drops the packet and",
            "sends ICMP Time Exceeded"
        ], 108),
        ("Protocol", [
            "Protocol: 6 TCP, 17 UDP, 1 ICMP, 47",
            "GRE, 50 ESP, 89 OSPF"
        ], 80),
        ("Header checksum", [
            "Header checksum: recomputed at",
            "every hop because the TTL changes"
        ], 80),
        ("Addresses 32-bit", [
            "source and destination 32-bit",
            "addresses"
        ], 80),
        ("options", ["options (rare)"], 72),
    ]

    total_h4 = sum(c[2] for c in card_specs_4) + 9 * 12
    print(f"Total IPv4 height: {total_h4}px (must be <= 990)")
    assert total_h4 <= 990, f"IPv4 too tall: {total_h4}"
    
    # Now let's check IPv6 cards
    # How many cards in IPv6? 9 cards!
    card_specs_6 = [
        ("Version 4 bits", ["Version 4 bits"], 72),
        ("Traffic Class", ["Traffic Class 8 bits = DSCP 6 + ECN", "2"], 80),
        ("Flow Label", [
            "Flow Label 20 bits: helps routers",
            "keep a flow on one path when ECMP",
            "spreads traffic"
        ], 108),
        ("Payload Length 16", ["Payload Length 16"], 72),
        ("Hop Limit 8", ["Hop Limit 8: plays the role of the", "TTL"], 80),
        ("Next Header 8", [
            "Next Header 8: extension headers",
            "chained (hop-by-hop, routing,",
            "fragment, destination options, AH,",
            "ESP)"
        ], 136),
        ("no header checksum", [
            "no header checksum (link and",
            "transport layers cover errors)"
        ], 80),
        ("no fragmentation fields", [
            "no fragmentation fields in the base",
            "header: only the source host may",
            "fragment, through an extension",
            "header; routers never do"
        ], 136),
        ("Addresses 128-bit", [
            "source and destination 128-bit",
            "addresses"
        ], 80)
    ]
    
    total_h6 = sum(c[2] for c in card_specs_6) + 8 * 14
    print(f"Total IPv6 height: {total_h6}px (must be <= 990)")
    assert total_h6 <= 990, f"IPv6 too tall: {total_h6}"

test_layout()
