#!/usr/bin/env python3

encaps = {
    "VXLAN": [
        "VXLAN: 50 added (outer Ethernet 14, often not",
        "counted, + IP 20 + UDP 8 + VXLAN 8): 1450 and 8950"
    ],
    "Geneve": [
        "Geneve no options: 50, variable with options:",
        "about 1450 and 8950"
    ],
    "GRE": [
        "GRE: 24 (IP 20 + GRE 4): 1476 and 8976"
    ],
    "IPIP": [
        "IPIP: 20: 1480 and 8980"
    ],
    "WireGuard": [
        "WireGuard: 60 on IPv4, 80 on IPv6:",
        "1420 or 1400, and 8940 or 8920"
    ],
    "IPsec": [
        "IPsec ESP tunnel: about 50 to 73, NAT-T adds 8:",
        "about 1400 to 1430, about 8930"
    ],
    "MPLS": [
        "MPLS: 4 per label: 1496 per label"
    ]
}

targets = {
    "VXLAN": "VXLAN: 50 added (outer Ethernet 14, often not counted, + IP 20 + UDP 8 + VXLAN 8): 1450 and 8950",
    "Geneve": "Geneve no options: 50, variable with options: about 1450 and 8950",
    "GRE": "GRE: 24 (IP 20 + GRE 4): 1476 and 8976",
    "IPIP": "IPIP: 20: 1480 and 8980",
    "WireGuard": "WireGuard: 60 on IPv4, 80 on IPv6: 1420 or 1400, and 8940 or 8920",
    "IPsec": "IPsec ESP tunnel: about 50 to 73, NAT-T adds 8: about 1400 to 1430, about 8930",
    "MPLS": "MPLS: 4 per label: 1496 per label"
}

for k, lines in encaps.items():
    joined = " ".join(lines)
    assert joined == targets[k], f"Mismatch in {k}!"
    max_w = max(len(l) * 0.6 * 24 for l in lines)
    print(f"{k:10s}: {len(lines)} line(s), max_w = {max_w:5.1f}px (chars={max(len(l) for l in lines)})")

print("\nALL PERFECT!")
