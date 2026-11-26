"""Test all 15 arrows with the fixed coordinates."""

from test_fix_loopback import seg_intersect

arrows = {
    "EV -> RQ": [(500, 215), (570, 215)],
    "RQ -> R": [(1010, 215), (1080, 215)],
    "R -> G": [(1290, 285), (1290, 325)],
    "G -> D": [(1080, 395), (1010, 395)],
    "D -> F (yes)": [(570, 395), (500, 395)],
    "D -> FIN (no)": [(790, 465), (790, 505)],
    "FIN -> V": [(1010, 575), (1080, 575)],
    "V -> C": [(1290, 645), (1290, 685)],
    "C -> A": [(1080, 755), (1010, 755)],
    "A -> S": [(570, 755), (500, 755)],
    "S -> U": [(280, 825), (280, 865)],
    "U -> RQR": [(500, 935), (570, 935)],
    "RQR -> END (done)": [(1010, 935), (1080, 935)],
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
    print("ALL 15 ARROWS HAVE ZERO INTERSECTIONS!")
