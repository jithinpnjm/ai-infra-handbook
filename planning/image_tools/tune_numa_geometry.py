#!/usr/bin/env python3

def sans_w(text, size=24):
    return len(text) * 0.60 * size

def mono_w(text, size=24):
    return len(text) * 0.62 * size

# Check Card A1
lines_a1 = [
    "GPU, NIC VF or",
    "RDMA device, and the",
    "pod's CPUs all on",
    "NUMA node 0"
]
print("=== Card A1 ===")
for l in lines_a1:
    w = sans_w(l, 24)
    print(f"  '{l}': {len(l)}c, {w:.1f}px")

# Check Card A2
# "transfers stay inside the node; fast"
# 36 chars * 0.6 * 24 = 518.4 px!
# Wait! In Card A2:
# If box width is 410 px: 518.4 px > 410 px!
# So Card A2 MUST BE WRAPPED into 2 lines!
lines_a2 = [
    "transfers stay inside",
    "the node; fast"
]
print("\n=== Card A2 ===")
for l in lines_a2:
    w = sans_w(l, 24)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits in 410: {w < 370})")

# Check Card M1: "pod CPUs on node 0 but the NIC on node 1"
lines_m1 = [
    "pod CPUs on node 0",
    "but the NIC on node 1"
]
print("\n=== Card M1 ===")
for l in lines_m1:
    w = sans_w(l, 24)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits in 410: {w < 370})")

# Check Card M2: "every transfer crosses the link between sockets and takes the slower road"
# Wide card across the panel (w=900)
lines_m2 = [
    "every transfer crosses the link between sockets",
    "and takes the slower road"
]
print("\n=== Card M2 ===")
for l in lines_m2:
    w = sans_w(l, 24)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits in 900: {w < 860})")

# Check Right Card 1:
# "kubelet Topology Manager with the single-numa-node or best-effort policy, together with the CPU Manager and the device plugins"
# Right box width: 490 px. Available width ~440 px.
lines_r1 = [
    "kubelet Topology Manager with the",
    "single-numa-node or best-effort",
    "policy, together with the CPU",
    "Manager and the device plugins"
]
print("\n=== Right Card 1 ===")
for l in lines_r1:
    w = sans_w(l, 24)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits in 490: {w < 440})")

# Check Right Card 2:
# "Verify after the pod starts: nvidia-smi topo -m, ibdev2netdev"
lines_r2 = [
    ("Verify after the pod starts:", 24, False),
    ("nvidia-smi topo -m, ", 24, True),
    ("ibdev2netdev", 24, True)
]
print("\n=== Right Card 2 ===")
for l, s, is_mono in lines_r2:
    w = mono_w(l, s) if is_mono else sans_w(l, s)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits in 490: {w < 440})")

# Check Right Card 3:
# "same on the host: pin test CPUs to the NUMA node of the NIC"
lines_r3 = [
    "same on the host: pin test CPUs",
    "to the NUMA node of the NIC"
]
print("\n=== Right Card 3 ===")
for l in lines_r3:
    w = sans_w(l, 24)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits in 490: {w < 440})")

# Check Bottom Bar:
# "A scheduler can place CPUs on one node and the network card on the other, so check the placement after the pod starts"
lines_bb = [
    "A scheduler can place CPUs on one node and the network card on the other,",
    "so check the placement after the pod starts"
]
print("\n=== Bottom Bar ===")
for l in lines_bb:
    w = sans_w(l, 25)
    print(f"  '{l}': {len(l)}c, {w:.1f}px (fits in 1520: {w < 1440})")
