#!/usr/bin/env python3

text = "restart fleetapp only when something changed"
words = text.split()

# Possible line splits:
splits = [
    ["restart fleetapp", "only when", "something changed"],
    ["restart fleetapp", "only when something", "changed"],
    ["restart", "fleetapp only", "when something", "changed"],
    ["restart fleetapp", "only when", "something", "changed"],
]

for s in splits:
    print("Split:", s)
    for line in s:
        w_sans = len(line) * 0.60 * 24
        w_mono = len(line) * 0.62 * 24
        print(f"   '{line}': sans={w_sans:.1f}px, mono={w_mono:.1f}px")
