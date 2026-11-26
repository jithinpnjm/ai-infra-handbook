from test_all_intersections import ccw, intersect

arrows = {
    "LEASE -> API": [(390, 190), (435, 190)],
    "Sources -> PM": [(800, 255), (800, 285)],
    "CAD -> EV": [(260, 420), (260, 450)],
    "PM -> PW": [(800, 420), (800, 450)],
    "IMG -> CRI": [(1340, 420), (1340, 450)],
    "EV -> PW": [(480, 517), (560, 517)],
    "PW -> CRI": [(1040, 495), (1120, 495)],
    "CRI -> PLEG": [(1340, 585), (1340, 620)],
    "PLEG -> PW": [(1120, 687), (1075, 687), (1075, 545), (1040, 545)],
    "PW -> VM": [(590, 585), (590, 687), (480, 687)],
    "PW -> DM": [(670, 585), (670, 850), (480, 850)],
    "PW -> PR": [(800, 585), (800, 785)],
    "PW -> SM": [(930, 585), (930, 850), (1120, 850)],
}

all_segments = []
for name, pts in arrows.items():
    for i in range(len(pts)-1):
        all_segments.append((name, pts[i], pts[i+1]))

has_intersection = False
for i in range(len(all_segments)):
    name1, A, B = all_segments[i]
    for j in range(i+1, len(all_segments)):
        name2, C, D = all_segments[j]
        if name1 == name2:
            continue
        if intersect(A, B, C, D):
            print(f"INTERSECTION between {name1} {A}->{B} and {name2} {C}->{D}!")
            has_intersection = True

if not has_intersection:
    print("SUCCESS: 0 CROSSINGS!")
