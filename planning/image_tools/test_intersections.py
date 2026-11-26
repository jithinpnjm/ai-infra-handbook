import re

# Let's test segment intersections for all arrow lines
# Arrow 1: (290, 126) -> (290, 200)
# Arrow 2: (520, 220) -> (1080, 220)
# Arrow 3: (1080, 270) -> (520, 270)
# Arrow 4: (320, 290) -> (320, 570)
# Arrow 5: (440, 570) -> (440, 290)
# Arrow 6: (1240, 290) -> (1240, 570)
# Arrow 7: (1080, 636) -> (520, 636)
# Arrow 8: (1400, 245) -> (1550, 245) -> (1550, 966) -> (960, 966)
# Arrow 9: (200, 260) -> (130, 260) -> (130, 938) -> (640, 938)
# Arrow 10: (780, 1010) -> (780, 1068) -> (60, 1068) -> (60, 220) -> (200, 220)

arrows = {
    1: [((290, 126), (290, 200))],
    2: [((520, 220), (1080, 220))],
    3: [((1080, 270), (520, 270))],
    4: [((320, 290), (320, 570))],
    5: [((440, 570), (440, 290))],
    6: [((1240, 290), (1240, 570))],
    7: [((1080, 636), (520, 636))],
    8: [((1400, 245), (1550, 245)), ((1550, 245), (1550, 966)), ((1550, 966), (960, 966))],
    9: [((200, 260), (130, 260)), ((130, 260), (130, 938)), ((130, 938), (640, 938))],
    10: [((780, 1010), (780, 1068)), ((780, 1068), (60, 1068)), ((60, 1068), (60, 220)), ((60, 220), (200, 220))]
}

def ccw(A, B, C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(A, B, C, D):
    # Strict intersection (ignoring shared endpoints)
    if A == C or A == D or B == C or B == D:
        return False
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

intersections = []
for id1, segs1 in arrows.items():
    for id2, segs2 in arrows.items():
        if id1 >= id2: continue
        for s1 in segs1:
            for s2 in segs2:
                if intersect(s1[0], s1[1], s2[0], s2[1]):
                    intersections.append((id1, id2, s1, s2))

print(f"Total arrow-to-arrow intersections: {len(intersections)}")
assert len(intersections) == 0, f"Found intersections: {intersections}"
print("ZERO ARROW CROSSINGS CONFIRMED!")
