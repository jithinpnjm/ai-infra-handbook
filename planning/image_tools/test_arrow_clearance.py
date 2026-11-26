boxes = {
    "top_box": (60, 135, 1480, 175),
    "shard1": (60, 350, 460, 160),
    "shard2": (570, 350, 460, 160),
    "shard3": (1080, 350, 460, 160),
    "aggregates_pill": (250, 570, 340, 105),
    "never_federate_card": (640, 570, 310, 105),
    "global_box": (60, 725, 960, 175),
    "side_card": (1070, 725, 470, 175),
    "takeaway_bar": (60, 945, 1480, 80)
}

# Arrows:
# Arrow 1: x = 200, from y = 510 to y = 713
# Arrow 2: x = 610 (or x = 600), from y = 510 to y = 713
# Arrow 3: (1140, 510) -> (1140, 540) -> (990, 540) -> (990, 713)
# Red Arrow: (790, 510) -> (790, 560) (stops before never_federate_card at 570)

# Check all gaps between boxes >= 40:
print("Checking pairwise box gaps:")
for n1, b1 in boxes.items():
    for n2, b2 in boxes.items():
        if n1 >= n2: continue
        x1, y1, w1, h1 = b1
        x2, y2, w2, h2 = b2
        # if horizontally aligned:
        if not (y1 + h1 <= y2 or y2 + h2 <= y1):
            # overlapping in y, so they are side-by-side
            dist_x = max(x1 - (x2 + w2), x2 - (x1 + w1))
            assert dist_x >= 40, f"Horizontal gap between {n1} and {n2} is {dist_x} < 40"
        # if vertically aligned:
        if not (x1 + w1 <= x2 or x2 + w2 <= x1):
            # overlapping in x, so stacked
            dist_y = max(y1 - (y2 + h2), y2 - (y1 + h1))
            assert dist_y >= 40, f"Vertical gap between {n1} and {n2} is {dist_y} < 40"

print("ALL PAIRWISE BOX GAPS >= 40px: PASS!")

# Check arrow segments do not intersect box interiors
segments = [
    ("Arrow 1", (200, 510), (200, 713)),
    ("Arrow 2", (610, 510), (610, 713)),
    ("Arrow 3 seg 1", (1140, 510), (1140, 540)),
    ("Arrow 3 seg 2", (1140, 540), (990, 540)),
    ("Arrow 3 seg 3", (990, 540), (990, 713)),
    ("Red Arrow", (790, 510), (790, 560))
]

for sname, (p1x, p1y), (p2x, p2y) in segments:
    sx1, sx2 = min(p1x, p2x), max(p1x, p2x)
    sy1, sy2 = min(p1y, p2y), max(p1y, p2y)
    for bname, (bx, by, bw, bh) in boxes.items():
        # check overlap with box interior (excluding boundaries)
        overlap_x = not (sx2 <= bx or sx1 >= bx + bw)
        overlap_y = not (sy2 <= by or sy1 >= by + bh)
        if overlap_x and overlap_y:
            print(f"COLLISION: {sname} intersects {bname}!")
            assert False

print("ALL ARROWS COMPLETELY CLEAR OF ALL BOXES: PASS!")
