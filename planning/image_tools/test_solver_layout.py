#!/usr/bin/env python3
# Check exact layout with H=1120

def check_box(name, x, y, w, h):
    print(f"Box {name:20s}: x=[{x}, {x+w}], y=[{y}, {y+h}]")

def check_clearance(b1, b2, min_gap=16):
    # b = (x1, y1, x2, y2)
    # Check if disjoint
    x_overlap = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
    y_overlap = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
    if x_overlap > 0 and y_overlap > 0:
        print(f"COLLISION between {b1} and {b2}!")
        return False
    return True

print("Layout solver testing...")
