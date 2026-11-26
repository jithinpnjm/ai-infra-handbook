#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

expected_labels = [
    "Encapsulation overhead and ECMP entropy",
    "Horizontal bar chart of overhead in bytes (IPv4 underlay)",
    "GRE 24 B",
    "IPIP 20 B",
    "VXLAN 50 B (outer Ethernet 14 + IP 20 + UDP 8 + VXLAN 8)",
    "GENEVE 50+ B",
    "MPLS 4 B per label",
    "WireGuard 60 B",
    "IPsec ESP about 50 to 73 B",
    "UDP-based: ECMP entropy from outer source port",
    "no ports: all traffic between two endpoints hashes to one path",
    "VXLAN is L2 over UDP/4789, GENEVE UDP/6081"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. {l} (len={len(l)})")
