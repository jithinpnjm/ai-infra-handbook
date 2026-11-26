# Python layout solver and validator
import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def ccw(A, B, C):
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)

def intersect(A, B, C, D):
    # Returns True if line segments AB and CD intersect (strictly, not at endpoints)
    if (A.x == C.x and A.y == C.y) or (A.x == D.x and A.y == D.y) or \
       (B.x == C.x and B.y == C.y) or (B.x == D.x and B.y == D.y):
        return False
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

print("Intersection test ready.")
