#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Expected labels
expected_labels = [
    "Fixing a PMTU black hole: four options and the ping arithmetic that finds it",
    "Four ways to fix a black hole",
    "1 allow the required ICMP messages (IPv4 type 3 code 4 Fragmentation Needed, IPv6 type 2 Packet Too Big)",
    "2 clamp the TCP MSS on tunnels: iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu",
    "3 use a consistent MTU across the path",
    "4 enable PLPMTUD with net.ipv4.tcp_mtu_probing",
    "Ping sizes add up to 1500",
    "payload 1472 + ICMP 8 + IPv4 20 = 1500 (ping -M do -s 1472)",
    "payload 1452 + ICMP 8 + IPv6 40 = 1500 (ping -6 -M do -s 1452)",
    "MSS at MTU 1500: IPv4 1500 - 20 - 20 = 1460; IPv6 1500 - 40 - 20 = 1440",
    "Fragmentation costs: each fragment carries an ID, an offset in 8-byte units and the MF flag; lose one fragment and you lose the whole packet; firewalls often drop fragments; some hardware paths send them to the CPU",
    "tracepath target, ip route get target, ss -ti dst target | grep mss pmtu: find the narrow door",
    "If the largest working size is smaller than you expected, you have found a narrow door"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. {l}")
