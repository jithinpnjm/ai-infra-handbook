"""Test swapped exit x coordinates."""

arrows = {
    "RQR -> RQ (error)": [
        (860, 1005), (860, 1060),
        (1535, 1060),
        (1535, 118),
        (800, 118),
        (800, 145)
    ],
    "RQR -> RQ (requeue)": [
        (720, 1005), (720, 1120),
        (1570, 1120),
        (1570, 92),
        (700, 92),
        (700, 145)
    ]
}

# Run intersection test on this
def seg_intersect(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    is_h1 = (y1 == y2)
    is_v1 = (x1 == x2)
    is_h2 = (y3 == y4)
    is_v2 = (x3 == x4)
    
    if is_h1 and is_h2:
        if y1 != y3: return False
        return max(min(x1, x2), min(x3, x4)) < min(max(x1, x2), max(x3, x4))
    if is_v1 and is_v2:
        if x1 != x3: return False
        return max(min(y1, y2), min(y3, y4)) < min(max(y1, y2), max(y3, y4))
    
    if is_h1 and is_v2:
        hx_min, hx_max = min(x1, x2), max(x1, x2)
        vy_min, vy_max = min(y3, y4), max(y3, y4)
        vx = x3
        hy = y1
        return (hx_min < vx < hx_max) and (vy_min < hy < vy_max)
    if is_v1 and is_h2:
        vy_min, vy_max = min(y1, y2), max(y1, y2)
        hx_min, hx_max = min(x3, x4), max(x3, x4)
        vx = x1
        hy = y3
        return (hx_min < vx < hx_max) and (vy_min < hy < vy_max)
    return False

all_segments = []
for name, pts in arrows.items():
    for i in range(len(pts) - 1):
        all_segments.append((name, i, pts[i], pts[i+1]))

has_intersection = False
for i in range(len(all_segments)):
    name1, idx1, p1, p2 = all_segments[i]
    for j in range(i + 1, len(all_segments)):
        name2, idx2, p3, p4 = all_segments[j]
        if name1 == name2 and abs(idx1 - idx2) <= 1:
            continue
        if seg_intersect(p1, p2, p3, p4):
            print(f"INTERSECTION: {name1}[{idx1}] and {name2}[{idx2}]")
            has_intersection = True

if not has_intersection:
    print("SUCCESS: 0 INTERSECTIONS BETWEEN THE TWO LOOPBACK ARROWS!")
