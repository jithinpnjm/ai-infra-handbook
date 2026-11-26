#!/usr/bin/env python3

# Layout verification script

W = 1600
H = 900

# Boxes:
# Col 1: center_x = 270, w = 420 -> [60, 480]
# Col 2: center_x = 800, w = 420 -> [590, 1010]
# Col 3: center_x = 1330, w = 420 -> [1120, 1540]

# Row 1: y = [140, 290], h = 150
# Row 2: y = [380, 540], h = 160
# Row 3: y = [630, 780], h = 150

boxes = {
    "U": {"name": "Teams", "x": 60, "y": 140, "w": 420, "h": 150},
    "H": {"name": "Node health feed", "x": 590, "y": 140, "w": 420, "h": 150},
    "Q": {"name": "Queue and fair share", "x": 60, "y": 380, "w": 420, "h": 160},
    "P": {"name": "Topology-aware placer", "x": 590, "y": 380, "w": 420, "h": 160},
    "N": {"name": "Nodes in fabric blocks", "x": 1120, "y": 380, "w": 420, "h": 160},
    "C": {"name": "Checkpoint store", "x": 1120, "y": 630, "w": 420, "h": 150},
}

# Check box overlaps
box_list = list(boxes.items())
for i in range(len(box_list)):
    for j in range(i + 1, len(box_list)):
        k1, b1 = box_list[i]
        k2, b2 = box_list[j]
        # check overlap
        overlap_x = not (b1["x"] + b1["w"] <= b2["x"] or b2["x"] + b2["w"] <= b1["x"])
        overlap_y = not (b1["y"] + b1["h"] <= b2["y"] or b2["y"] + b2["h"] <= b1["y"])
        if overlap_x and overlap_y:
            print(f"ERROR: Box {k1} overlaps Box {k2}")

# Check distances between boxes
print("Checking distances between boxes:")
for i in range(len(box_list)):
    for j in range(i + 1, len(box_list)):
        k1, b1 = box_list[i]
        k2, b2 = box_list[j]
        dx = max(0, b1["x"] - (b2["x"] + b2["w"]), b2["x"] - (b1["x"] + b1["w"]))
        dy = max(0, b1["y"] - (b2["y"] + b2["h"]), b2["y"] - (b1["y"] + b1["h"]))
        dist = max(dx, dy)
        print(f"Dist {k1}-{k2}: dx={dx}, dy={dy} -> dist={dist} (min 40: {dist >= 40})")
        assert dist >= 40, f"Distance between {k1} and {k2} is {dist} < 40!"

print("All box clearances >= 40 px!")
