#!/usr/bin/env python3
import re

# Font metrics conservative rules:
# sans: 0.6 * fs
# mono: 0.62 * fs

def measure_line(text, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.60
    return len(text) * fs * coeff

# Column widths: 480 px.
# Inside card width: 440 px (x_pad = 20 on each side of the card inside the 480 container)
# Inside card text x_pad: at least 16 px inside the 440 card -> text width <= 408 px.
# At fs=24 sans: 408 / (24 * 0.6) = 28.3 chars max per line!

# Let's test lines for all cards with max 28 chars:

card_texts = {
    "anatomy": [
        "pod /etc/resolv.conf:",
        "nameserver 10.0.0.10;",
        "three search domains;",
        "options ndots:5"
    ],
    "rule": [
        "a name with fewer dots",
        "than ndots is tried with",
        "each search suffix first;",
        "a combined name that does",
        "not exist returns NXDOMAIN;",
        "then the real name is asked"
    ],
    "risky": [
        "removing every CoreDNS pod;",
        "hard-coded hosts entries"
    ],
    "load": [
        "gateway release at 10:05",
        "added a per-request call to",
        "an external identity provider;",
        "query rate 12,000 per second",
        "up from 3,000; CoreDNS has",
        "two replicas, CPU limit 200m,",
        "throttled; DNS latency p99",
        "up to 2 s, some queries time",
        "out; no NodeLocal DNSCache;",
        "upstream resolver healthy,",
        "5 ms from a node"
    ],
    "result": [
        "about 5 percent of requests",
        "fail with 502 because token",
        "validation cannot resolve",
        "its host; inference path works"
    ],
    "fix": [
        "roll back or flag off the",
        "lookup; scale CoreDNS and",
        "lift its CPU limit; trailing-",
        "dot name or lower ndots",
        "through dnsConfig; plan",
        "NodeLocal DNSCache"
    ],
    "test_note": [
        "test from a pod, not a laptop, because a laptop uses its own resolver"
    ]
}

print("=== Text Line Measurements ===")
all_pass = True
for card_name, lines in card_texts.items():
    print(f"\n--- {card_name} ---")
    box_w = 1440 if card_name == "test_note" else 420
    for l in lines:
        w = measure_line(l, 24, False)
        pad = (box_w - w) / 2
        ok = (w <= box_w - 32)
        if not ok:
            all_pass = False
        print(f"  [{len(l):2d}c | {w:5.1f}px / {box_w}px | pad={pad:4.1f}px] {'OK' if ok else 'FAIL'}: {l}")

assert all_pass, "Some lines exceed width budget!"
print("\nALL LINES PASS WIDTH BUDGET WITH >16px PADDING!")
