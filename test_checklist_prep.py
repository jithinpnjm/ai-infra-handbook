import xml.etree.ElementTree as ET
import re, subprocess, os

# Source labels required:
required_labels = [
    "Top-down and bottom-up checklist",
    "Top-down (application symptom to wire)",
    "process listening",
    "ss -tulpn",
    "connect test",
    "nc -zv host port",
    "refusal versus timeout",
    "DNS",
    "getent hosts",
    "dig",
    "route and source",
    "ip route get <dst>",
    "ip rule",
    "rp_filter",
    "firewall",
    "nft list ruleset",
    "conntrack",
    "neighbours",
    "ip neigh",
    "arping",
    "interface",
    "ip -s link",
    "ethtool -S",
    "capture packets at both ends",
    "Bottom-up goes the other way",
    "link up",
    "speed and FEC",
    "errors",
    "ring buffers",
    "IRQ and CPU",
    "Application reports the failure: go top-down. Counters already rising: go bottom-up"
]

print("Total required labels:", len(required_labels))
