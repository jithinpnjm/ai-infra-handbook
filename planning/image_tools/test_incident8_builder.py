#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

expected_labels = [
    "Incident 8: one external lookup becomes several DNS queries",
    "pod /etc/resolv.conf: nameserver 10.0.0.10; three search domains; options ndots:5",
    "a name with fewer dots than ndots is tried with each search suffix first; a combined name that does not exist returns NXDOMAIN; then the real name is asked",
    "suffix 1 -> NXDOMAIN",
    "suffix 2 -> NXDOMAIN",
    "suffix 3 -> NXDOMAIN",
    "idp.example.test -> answer",
    "gateway release at 10:05 added a per-request call to an external identity provider; query rate 12,000 per second up from 3,000; CoreDNS has two replicas, CPU limit 200m, throttled; DNS latency p99 up to 2 s, some queries time out; no NodeLocal DNSCache; upstream resolver healthy, 5 ms from a node",
    "about 5 percent of requests fail with 502 because token validation cannot resolve its host; inference path works",
    "roll back or flag off the lookup; scale CoreDNS and lift its CPU limit; trailing-dot name or lower ndots through dnsConfig; plan NodeLocal DNSCache",
    "removing every CoreDNS pod; hard-coded hosts entries",
    "test from a pod, not a laptop, because a laptop uses its own resolver"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. len={len(l):3d}: '{l}'")
