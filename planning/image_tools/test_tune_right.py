#!/usr/bin/env python3

def sans_w(text, size=24):
    return len(text) * 0.60 * size

def mono_w(text, size=24):
    return len(text) * 0.62 * size

# Right Card 1 (5 lines):
r1 = [
    "kubelet Topology Manager",
    "with the single-numa-node",
    "or best-effort policy,",
    "together with the CPU Manager",
    "and the device plugins"
]
print("Right Card 1 (card w=490, max allowed w = 490 - 40 = 450):")
for l in r1:
    w = sans_w(l, 24)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits <= 450: {w <= 450})")

# Right Card 3 (3 lines):
r3 = [
    "same on the host:",
    "pin test CPUs to the",
    "NUMA node of the NIC"
]
print("\nRight Card 3 (card w=490, max allowed w = 450):")
for l in r3:
    w = sans_w(l, 24)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits <= 450: {w <= 450})")
