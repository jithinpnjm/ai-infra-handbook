#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

# Define the exact 15 labels
LABELS = [
    "Overlay MTU on a 1500 and a 9000 underlay: how many bytes each tunnel takes",
    "VXLAN: 50 added (outer Ethernet 14, often not counted, + IP 20 + UDP 8 + VXLAN 8): 1450 and 8950",
    "Geneve no options: 50, variable with options: about 1450 and 8950",
    "GRE: 24 (IP 20 + GRE 4): 1476 and 8976",
    "IPIP: 20: 1480 and 8980",
    "WireGuard: 60 on IPv4, 80 on IPv6: 1420 or 1400, and 8940 or 8920",
    "IPsec ESP tunnel: about 50 to 73, NAT-T adds 8: about 1400 to 1430, about 8930",
    "MPLS: 4 per label: 1496 per label",
    "Where mismatches bite",
    "Kubernetes CNIs such as Calico (VXLAN or IPIP), Flannel and Cilium set the pod MTU from the underlay MTU and the overlay; a mismatch is a top cause of services work for tiny requests only",
    "GCP VPC defaults to MTU 1460, configurable up to 8896",
    "AWS supports 9001 inside a VPC but only 1500 across the Internet and on many inter-region and VPN paths: validate jumbo designs path by path",
    "ip -d link show shows the mtu and the encapsulation device; then ping -M do",
    "largest ping -M do -s payloads: 1472 IPv4, 1452 IPv6, 8972 jumbo",
    "Compute, don't guess: overlay MTU is the underlay MTU minus the added bytes"
]

print(f"Total labels: {len(LABELS)}")
for i, l in enumerate(LABELS, 1):
    print(f"{i:2d}. {l}")
