#!/usr/bin/env python3

# Layout A: 3-row layout
# Row 1 (y=160-280): Teams (Col 1), Node health feed (Col 2)
# Row 2 (y=380-520): Queue and fair share (Col 1), Topology-aware placer (Col 2), Nodes in fabric blocks (Col 3)
# Row 3 (y=620-740): Checkpoint store (Col 3)

# Let's check text fits for all boxes:
# Rule: "Title 48 px bold. Node and step titles at least 30 px bold. Secondary text and monospace at least 24 px. NO text smaller than 24 px anywhere."
# "Estimate widths conservatively: sans 0.6 x font-size per character"
# "Every text line must fit inside its box with at least 16 px padding."

def check_box(name, text, w, h, fs=30, multiline=False):
    lines = text.split('\n') if multiline else [text]
    max_len = max(len(l) for l in lines)
    est_w = max_len * 0.6 * fs
    pad_h = (w - est_w) / 2
    print(f"{name:25s} | lines={lines} | max_w={est_w:.1f} | box_w={w} | pad={pad_h:.1f} (>=16: {pad_h>=16})")

print("Checking box text fits at 30px font size:")
check_box("Teams", "Teams", 380, 130)
check_box("Node health feed", "Node health feed", 460, 130)
check_box("Queue (1-line)", "Queue and fair share", 440, 140)
check_box("Queue (2-line)", "Queue and\nfair share", 380, 140, multiline=True)
check_box("Placer (1-line)", "Topology-aware placer", 460, 140)
check_box("Placer (2-line)", "Topology-aware\nplacer", 460, 140, multiline=True)
check_box("Nodes (1-line)", "Nodes in fabric blocks", 460, 140)
check_box("Nodes (2-line)", "Nodes in\nfabric blocks", 380, 140, multiline=True)
check_box("Checkpoint (1-line)", "Checkpoint store", 380, 130)
