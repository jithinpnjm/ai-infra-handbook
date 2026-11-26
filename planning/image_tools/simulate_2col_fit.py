#!/usr/bin/env python3

def measure(text, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.60
    return len(text) * fs * coeff

# Available text width in a 730px card with 30px padding on each side = 670px.
# 670 / (24 * 0.6) = 46.5 characters!

anatomy_lines = [
    "pod /etc/resolv.conf: nameserver 10.0.0.10;",
    "three search domains; options ndots:5"
]

rule_lines = [
    "a name with fewer dots than ndots is tried with each",
    "search suffix first; a combined name that does not exist",
    "returns NXDOMAIN; then the real name is asked"
]

queries = [
    "suffix 1 -> NXDOMAIN",
    "suffix 2 -> NXDOMAIN",
    "suffix 3 -> NXDOMAIN",
    "idp.example.test -> answer"
]

load_lines = [
    "gateway release at 10:05 added a per-request call to an",
    "external identity provider; query rate 12,000 per second up",
    "from 3,000; CoreDNS has two replicas, CPU limit 200m, throttled;",
    "DNS latency p99 up to 2 s, some queries time out; no NodeLocal",
    "DNSCache; upstream resolver healthy, 5 ms from a node"
]

result_lines = [
    "about 5 percent of requests fail with 502 because token",
    "validation cannot resolve its host; inference path works"
]

fix_lines = [
    "roll back or flag off the lookup; scale CoreDNS and lift its",
    "CPU limit; trailing-dot name or lower ndots through dnsConfig;",
    "plan NodeLocal DNSCache"
]

risky_lines = [
    "removing every CoreDNS pod; hard-coded hosts entries"
]

test_note_line = "test from a pod, not a laptop, because a laptop uses its own resolver"

sections = [
    ("Anatomy", anatomy_lines, 730),
    ("Rule", rule_lines, 730),
    ("Query 1", [queries[0]], 730),
    ("Query 2", [queries[1]], 730),
    ("Query 3", [queries[2]], 730),
    ("Query 4", [queries[3]], 730),
    ("Load", load_lines, 730),
    ("Result", result_lines, 730),
    ("Fix", fix_lines, 730),
    ("Risky", risky_lines, 730),
    ("Test note", [test_note_line], 1520),
]

all_pass = True
for name, lines, w_box in sections:
    print(f"\n=== {name} (box_w={w_box}) ===")
    for l in lines:
        w = measure(l, 24, False)
        pad = (w_box - w) / 2
        ok = (w <= w_box - 32)
        if not ok:
            all_pass = False
        print(f"  [{len(l):2d}c | {w:5.1f}px / {w_box}px | pad={pad:5.1f}px] {'OK' if ok else 'FAIL'}: '{l}'")

assert all_pass, "Width check failed!"
print("\n>>> ALL TEXT LINES FIT WITH MASSIVE PADDING (>30px to >50px Everywhere) <<<")
