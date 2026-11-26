"""Verify no arrow passes through any node box."""

from test_layout_coords import nodes
from test_all_arrows_clean import arrows

# For each box, interior is (x, x+w) and (y, y+h)
def segment_intersects_box(p1, p2, box):
    bx1 = box["x"]
    bx2 = box["x"] + box["w"]
    by1 = box["y"]
    by2 = box["y"] + box["h"]
    
    x1, y1 = p1
    x2, y2 = p2
    
    # If horizontal
    if y1 == y2:
        y = y1
        if by1 < y < by2:
            seg_min_x, seg_max_x = min(x1, x2), max(x1, x2)
            # Check overlap between (seg_min_x, seg_max_x) and (bx1, bx2)
            if max(seg_min_x, bx1) < min(seg_max_x, bx2):
                return True
    # If vertical
    if x1 == x2:
        x = x1
        if bx1 < x < bx2:
            seg_min_y, seg_max_y = min(y1, y2), max(y1, y2)
            if max(seg_min_y, by1) < min(seg_max_y, by2):
                return True
    return False

box_collision = False
for aname, pts in arrows.items():
    for i in range(len(pts) - 1):
        p1, p2 = pts[i], pts[i+1]
        for bname, box in nodes.items():
            if segment_intersects_box(p1, p2, box):
                print(f"COLLISION: Arrow {aname} segment {p1}->{p2} intersects box {bname}!")
                box_collision = True

if not box_collision:
    print("SUCCESS: NO ARROW INTERSECTS ANY NODE BOX INTERIOR!")
