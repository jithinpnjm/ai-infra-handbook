import re

# Conservative widths
def line_w(txt, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    return len(txt) * fs * factor

# Card 1: expander
# (660, 140, 900, 130)
# 'expander chooses which node group to grow: random, most-pods, least-waste, price, priority (rank GPU types)'
card1_lines = [
    "expander chooses which node group to grow:",
    "random, most-pods, least-waste, price,",
    "priority (rank GPU types)"
]

# Card 2: provision time
# (660, 310, 900, 130)
# '--max-node-provision-time default 15 minutes: if a node has not registered by then the autoscaler stops counting it, which is why you keep warm capacity'
card2_lines = [
    "--max-node-provision-time default 15 minutes:",
    "if a node has not registered by then the autoscaler",
    "stops counting it, which is why you keep warm capacity"
]

# Card 3: scale-down
# (660, 480, 900, 240)
# 'scale-down: node considered when pod CPU and memory requests sum below 50 percent of allocatable; must stay unneeded 10 minutes; held 10 minutes after a scale-up; evicts through the eviction API for up to 2 minutes; accelerator flag scale-down-gpu-utilization-threshold default 0.5'
card3_lines = [
    "scale-down: node considered when pod CPU and",
    "memory requests sum below 50 percent of allocatable;",
    "must stay unneeded 10 minutes; held 10 minutes after a",
    "scale-up; evicts through the eviction API for up to",
    "2 minutes; accelerator flag",
    "scale-down-gpu-utilization-threshold default 0.5"
]

# Card 4: Nebius
# (660, 760, 900, 240)
# 'autoscaling min and max node count flags; page gives no defaults or timings; keep a CPU node group of at least two nodes (or autoscaling) so CoreDNS and networking add-ons run there; known issue with GPU Operator and Network Operator creating extra nodes, not reproduced'
card4_lines = [
    "autoscaling min and max node count flags; page gives",
    "no defaults or timings; keep a CPU node group of at",
    "least two nodes (or autoscaling) so CoreDNS and",
    "networking add-ons run there; known issue with",
    "GPU Operator and Network Operator creating",
    "extra nodes, not reproduced"
]

cards = [
    ("Card 1", card1_lines, 660, 140, 900, 130, 736),
    ("Card 2", card2_lines, 660, 310, 900, 130, 736),
    ("Card 3", card3_lines, 660, 480, 900, 240, 736),
    ("Card 4", card4_lines, 660, 760, 900, 240, 736),
]

for name, lines, bx, by, bw, bh, tx in cards:
    print(f"\n--- {name} ---")
    for l in lines:
        w = line_w(l)
        pad_l = tx - bx
        pad_r = (bx + bw) - (tx + w)
        print(f"  len={len(l):2d} w={w:5.1f} pad_l={pad_l:4.1f} pad_r={pad_r:4.1f} : '{l}'")
        assert pad_l >= 16, f"pad_l {pad_l} < 16"
        assert pad_r >= 16, f"pad_r {pad_r} < 16"
print("\nAll horizontal paddings on Right Column PASS!")
