import re

# Geometry check
boxes = {
    "top_box": (60, 140, 1480, 185),
    "shard1": (60, 375, 460, 170),
    "shard2": (570, 375, 460, 170),
    "shard3": (1080, 375, 460, 170),
    "aggregates_pill": (300, 580, 350, 95),
    "never_federate_card": (720, 620, 330, 95),
    "side_card": (1110, 575, 430, 140),
    "global_box": (60, 735, 1480, 195),
    "takeaway_bar": (60, 965, 1480, 80)
}

# Check box collisions
names = list(boxes.keys())
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        n1, n2 = names[i], names[j]
        x1, y1, w1, h1 = boxes[n1]
        x2, y2, w2, h2 = boxes[n2]
        overlap_x = not (x1 + w1 <= x2 or x2 + w2 <= x1)
        overlap_y = not (y1 + h1 <= y2 or y2 + h2 <= y1)
        if overlap_x and overlap_y:
            print(f"COLLISION: {n1} overlaps {n2}!")
            assert False

print("NO BOX COLLISIONS!")

# Vertical lines for arrows:
# Arrow 1: x=240, from y=545 to y=723
# Arrow 2: x=685, from y=545 to y=723
# Arrow 3: x=1075, from y=545 to y=723
# Red arrow: x=885, from y=545 to y=615 (stops at red card)
arrows = [
    ("Arrow 1", 240, 545, 723),
    ("Arrow 2", 685, 545, 723),
    ("Arrow 3", 1075, 545, 723),
    ("Red Arrow", 885, 545, 615)
]

for aname, ax, ay1, ay2 in arrows:
    for bname, (bx, by, bw, bh) in boxes.items():
        # check if line intersects box interior
        if bx < ax < (bx + bw) and not (ay2 <= by or ay1 >= by + bh):
            print(f"ARROW COLLISION: {aname} intersects {bname}!")
            assert False

print("NO ARROW COLLISIONS!")

# Now check text padding inside each box
def check_pad(label, lines, fs, box_w, box_h):
    max_w = max(len(l) * 0.6 * fs for l in lines)
    total_h = len(lines) * fs * 1.3
    pad_h = (box_w - max_w) / 2
    pad_v = (box_h - total_h) / 2
    print(f"[{label}] pad_h={pad_h:.1f}px (need >=16), pad_v={pad_v:.1f}px (need >=16)")
    assert pad_h >= 16
    assert pad_v >= 16

check_pad("aggregates_pill", ["Only aggregates and", "SLI series upward"], 26, 350, 95)
check_pad("never_federate_card", ["Never federate", "raw per-pod series"], 26, 330, 95)
# side_card: 4 lines
check_pad("side_card", ["Cost: fragmented data,", "a question across", "shards needs two", "queries and a join"], 24, 430, 140)

print("\nALL CLEARANCES AND PADDINGS VERIFIED PERFECTLY!")
