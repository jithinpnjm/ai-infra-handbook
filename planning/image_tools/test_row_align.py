#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Let's test the alignment and calculate heights for each row
rows = [
    # row 0: Version
    {
        "id": "version",
        "h4": 68,
        "h6": 68,
        "txt4": ["Version 4"],
        "txt6": ["Version 4 bits"],
    },
    # row 1: DSCP / Traffic Class (Arrow: DSCP+ECN to Traffic Class)
    {
        "id": "traffic_class",
        "h4": 74,
        "h6": 74,
        "txt4": ["DSCP (6 bits) and ECN (2 bits)"],
        "txt6": ["Traffic Class 8 bits = DSCP 6 + ECN", "2"],
        "arrow": "DSCP+ECN to Traffic Class"
    },
    # row 2: IHL / Flow Label
    {
        "id": "ihl_flow",
        "h4": 76,
        "h6": 96, # Flow label has 3 lines
        "txt4": ["IHL: header length in 32-bit words,", "5 means 20 bytes"],
        "txt6": ["Flow Label 20 bits: helps routers", "keep a flow on one path when ECMP", "spreads traffic"]
    },
    # row 3: Total Length / Payload Length
    {
        "id": "length",
        "h4": 68,
        "h6": 68,
        "txt4": ["Total Length up to 65,535"],
        "txt6": ["Payload Length 16"]
    },
    # row 4: Fragmentation (Crossed out on IPv6 side)
    {
        "id": "fragmentation",
        "h4": 128,
        "h6": 128,
        "txt4": [
            "Identification, Flags (DF, MF),",
            "Fragment Offset: fragmentation",
            "lives in the base header; routers",
            "may fragment unless DF is set"
        ],
        "txt6": [
            "no fragmentation fields in the base",
            "header: only the source host may",
            "fragment, through an extension",
            "header; routers never do"
        ],
        "crossed6": True
    },
    # row 5: TTL / Hop Limit (Arrow: TTL to Hop Limit)
    {
        "id": "ttl_hop",
        "h4": 96,
        "h6": 96,
        "txt4": [
            "TTL: drops by one per router, at 0",
            "the router drops the packet and",
            "sends ICMP Time Exceeded"
        ],
        "txt6": [
            "Hop Limit 8: plays the role of the",
            "TTL"
        ],
        "arrow": "TTL to Hop Limit"
    },
    # row 6: Protocol / Next Header (Arrow: Protocol to Next Header)
    {
        "id": "protocol_next",
        "h4": 120,
        "h6": 120,
        "txt4": [
            "Protocol: 6 TCP, 17 UDP, 1 ICMP, 47",
            "GRE, 50 ESP, 89 OSPF"
        ],
        "txt6": [
            "Next Header 8: extension headers",
            "chained (hop-by-hop, routing,",
            "fragment, destination options, AH,",
            "ESP)"
        ],
        "arrow": "Protocol to Next Header"
    },
    # row 7: Checksum (Crossed out on IPv6 side)
    {
        "id": "checksum",
        "h4": 74,
        "h6": 74,
        "txt4": [
            "Header checksum: recomputed at",
            "every hop because the TTL changes"
        ],
        "txt6": [
            "no header checksum (link and",
            "transport layers cover errors)"
        ],
        "crossed6": True
    },
    # row 8: Addresses
    {
        "id": "addresses",
        "h4": 74,
        "h6": 74,
        "txt4": [
            "source and destination 32-bit",
            "addresses"
        ],
        "txt6": [
            "source and destination 128-bit",
            "addresses"
        ]
    },
    # row 9: options (rare) (IPv4 only)
    {
        "id": "options",
        "h4": 68,
        "h6": 0,
        "txt4": ["options (rare)"],
        "txt6": []
    }
]

# Let's check the vertical positions
y_start = 145
gap = 10
cur_y = y_start
for i, r in enumerate(rows):
    row_h = max(r["h4"], r["h6"])
    print(f"Row {i:d} ({r['id']:15s}): y={cur_y:4d}, h={row_h:3d}, bottom={cur_y+row_h:4d}")
    cur_y += row_h + gap

total_height_needed = cur_y - gap
print(f"\nTotal content height: {total_height_needed}px")
print(f"Bottom bar at y={total_height_needed + 15}, height=55px -> ends at {total_height_needed + 15 + 55}")
