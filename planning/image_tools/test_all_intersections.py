def ccw(A, B, C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(A, B, C, D):
    # returns True if open line segments AB and CD intersect
    # check bounding boxes first
    if max(A[0], B[0]) < min(C[0], D[0]) or min(A[0], B[0]) > max(C[0], D[0]):
        return False
    if max(A[1], B[1]) < min(C[1], D[1]) or min(A[1], B[1]) > max(C[1], D[1]):
        return False
    return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))

# Define all 13 arrows as lists of points:
arrows = {
    "LEASE -> API": [(390, 197), (440, 197)],
    "Sources -> PM": [(800, 270), (800, 305)],
    "CAD -> EV": [(260, 420), (260, 460)],
    "PM -> PW": [(800, 415), (800, 455)],
    "IMG -> CRI": [(1340, 415), (1340, 460)],
    "EV -> PW": [(480, 517), (560, 517)],
    "PW -> CRI": [(1040, 495), (1120, 495)],
    "CRI -> PLEG": [(1340, 575), (1340, 620)],
    "PLEG -> PW": [(1120, 677), (1075, 677), (1075, 545), (1040, 545)],
    "PW -> VM": [(640, 585), (640, 680), (480, 680)],
    "PW -> DM": [(720, 585), (720, 755), (280, 755), (280, 780)],
    "PW -> PR": [(800, 585), (800, 780)],
    "PW -> SM": [(880, 585), (880, 755), (1320, 755), (1320, 780)],
}

# Decompose arrows into segments:
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
    print("SUCCESS: EXACTLY ZERO ARROW CROSSINGS!")

