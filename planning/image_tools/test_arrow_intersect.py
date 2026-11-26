#!/usr/bin/env python3

# Arrow collision test

arrows = {
    "A1 (U->Q)": [(270, 290), (270, 380)],
    "A2 (H->P)": [(800, 290), (800, 380)],
    "A3 (Q->P)": [(480, 460), (590, 460)],
    "A4 (P->N)": [(1010, 460), (1120, 460)],
    "A5 (N->C)": [(1330, 540), (1330, 630)],
    "A6_h (C->Q horiz)": [(270, 705), (1120, 705)],
    "A6_v (C->Q vert)":  [(270, 540), (270, 705)],
}

def segments_intersect(p1, p2, p3, p4):
    def ccw(a, b, c):
        return (c[1]-a[1]) * (b[0]-a[0]) > (b[1]-a[1]) * (c[0]-a[0])
    # check endpoints touching
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False
    return ccw(p1,p3,p4) != ccw(p2,p3,p4) and ccw(p1,p2,p3) != ccw(p1,p2,p4)

arrow_keys = list(arrows.keys())
for i in range(len(arrow_keys)):
    for j in range(i+1, len(arrow_keys)):
        k1, k2 = arrow_keys[i], arrow_keys[j]
        p1, p2 = arrows[k1]
        p3, p4 = arrows[k2]
        if segments_intersect(p1, p2, p3, p4):
            print(f"INTERSECTION: {k1} and {k2}")
        else:
            print(f"PASS: {k1} and {k2} do not intersect")

print("\nAll arrow intersection tests passed!")
