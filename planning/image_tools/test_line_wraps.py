#!/usr/bin/env python3
import sys

# Conservative width estimators
def sans_width(text, size=24):
    return len(text) * 0.60 * size

def mono_width(text, size=24):
    return len(text) * 0.62 * size

print("--- Testing Text Line Wraps and Widths ---")

# 1. Title: "Keeping the GPU, its NIC and its CPUs on one NUMA node" (size 48 bold)
title_text = "Keeping the GPU, its NIC and its CPUs on one NUMA node"
w = len(title_text) * 0.60 * 48
print(f"Title: '{title_text}' -> {w:.1f} px (Canvas width 1600 px, fits on 1 line: {w < 1520})")

# Sockets: "NUMA node 0", "NUMA node 1" (size 30 bold)
for s in ["NUMA node 0", "NUMA node 1"]:
    w = len(s) * 0.60 * 30
    print(f"Socket: '{s}' -> {w:.1f} px")

# Panel titles: "Aligned", "Misaligned" (size 30 bold)
for p in ["Aligned", "Misaligned"]:
    w = len(p) * 0.60 * 30
    print(f"Panel: '{p}' -> {w:.1f} px")

# Right title: "how to keep them together" (size 30 bold)
rt = "how to keep them together"
w = len(rt) * 0.60 * 30
print(f"Right title: '{rt}' -> {w:.1f} px (Right col width 520, fits: {w < 440})")

# Let's check wrapping for each multi-line card:

# Card A1: "GPU, NIC VF or RDMA device, and the pod's CPUs all on NUMA node 0"
# Width available in card: ~410 px. At size 24, max chars per line is 410 / (0.6*24) = 28.4 chars.
# Let's wrap Card A1:
lines_a1 = [
    "GPU, NIC VF or RDMA device, and",
    "the pod's CPUs all on NUMA node 0"
]
print("\nCard A1 lines:")
for l in lines_a1:
    wl = sans_width(l, 24)
    print(f"  '{l}': {len(l)} chars -> {wl:.1f} px")

# Card A2: "transfers stay inside the node; fast"
lines_a2 = [
    "transfers stay inside the node; fast"
]
print("\nCard A2 lines:")
for l in lines_a2:
    wl = sans_width(l, 24)
    print(f"  '{l}': {len(l)} chars -> {wl:.1f} px")

# Card M1: "pod CPUs on node 0 but the NIC on node 1"
lines_m1 = [
    "pod CPUs on node 0 but",
    "the NIC on node 1"
]
print("\nCard M1 lines:")
for l in lines_m1:
    wl = sans_width(l, 24)
    print(f"  '{l}': {len(l)} chars -> {wl:.1f} px")

# Card M2: "every transfer crosses the link between sockets and takes the slower road"
lines_m2 = [
    "every transfer crosses the link between",
    "sockets and takes the slower road"
]
print("\nCard M2 lines:")
for l in lines_m2:
    wl = sans_width(l, 24)
    print(f"  '{l}': {len(l)} chars -> {wl:.1f} px")

# Right Card 1: "kubelet Topology Manager with the single-numa-node or best-effort policy, together with the CPU Manager and the device plugins"
# Right col card width: ~470 px. Max chars per line = 470 / (0.6*24) = 32.6 chars.
lines_r1 = [
    "kubelet Topology Manager with the",
    "single-numa-node or best-effort policy,",
    "together with the CPU Manager and the",
    "device plugins"
]
print("\nRight Card 1 lines:")
for l in lines_r1:
    wl = sans_width(l, 24)
    print(f"  '{l}': {len(l)} chars -> {wl:.1f} px")

# Right Card 2: "Verify after the pod starts: nvidia-smi topo -m, ibdev2netdev"
# Note: command part can be monospace or sans, let's check monospace width:
lines_r2 = [
    "Verify after the pod starts:",
    "nvidia-smi topo -m, ibdev2netdev"
]
print("\nRight Card 2 lines:")
for l in lines_r2:
    wl = mono_width(l, 24) if "nvidia" in l else sans_width(l, 24)
    print(f"  '{l}': {len(l)} chars -> {wl:.1f} px")

# Right Card 3: "same on the host: pin test CPUs to the NUMA node of the NIC"
lines_r3 = [
    "same on the host: pin test CPUs",
    "to the NUMA node of the NIC"
]
print("\nRight Card 3 lines:")
for l in lines_r3:
    wl = sans_width(l, 24)
    print(f"  '{l}': {len(l)} chars -> {wl:.1f} px")

# Bottom Bar: "A scheduler can place CPUs on one node and the network card on the other, so check the placement after the pod starts"
# Available width: 1520 px.
# At size 26, 117 chars * 0.6 * 26 = 1825 px -> Needs 2 lines!
# Max chars per line = 1440 / (0.6*26) = 92 chars.
lines_bb = [
    "A scheduler can place CPUs on one node and the network card on the other,",
    "so check the placement after the pod starts"
]
print("\nBottom bar lines:")
for l in lines_bb:
    wl = sans_width(l, 26)
    print(f"  '{l}': {len(l)} chars -> {wl:.1f} px")
