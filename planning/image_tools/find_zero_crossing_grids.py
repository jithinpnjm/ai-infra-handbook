# Find planar grid layouts with ZERO crossings
import itertools

states = [
    "Provisioned", "Configured", "Validating",
    "Ready", "Cordoned", "Draining",
    "Maintenance", "Quarantined", "Decommissioned"
]

edges = [
    ("Provisioned", "Configured"),
    ("Configured", "Validating"),
    ("Validating", "Ready"),
    ("Ready", "Cordoned"),
    ("Cordoned", "Draining"),
    ("Draining", "Maintenance"),
    ("Maintenance", "Validating"),
    ("Draining", "Quarantined"),
    ("Quarantined", "Provisioned"),
    ("Ready", "Decommissioned"),
]

# A grid layout has positions (r, c) for each node.
# Let's route edges orthogonally:
# If adjacent (dr=0 or dc=0): straight line segment between nodes.
# If diagonal (dr=1, dc=1): routes via corner (r1, c2) or (r2, c1).
# We can check which corner is free!

def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def segments_intersect(A, B, C, D):
    # Proper intersection between open segments AB and CD
    if A == C or A == D or B == C or B == D:
        return False
    # Check if collinear overlapping
    # For orthogonal segments, easy:
    # Segment 1 horizontal, Segment 2 vertical:
    if A[1] == B[1] and C[0] == D[0]:
        x1, x2 = min(A[0], B[0]), max(A[0], B[0])
        y1, y2 = min(C[1], D[1]), max(C[1], D[1])
        return (x1 < C[0] < x2) and (y1 < A[1] < y2)
    if A[0] == B[0] and C[1] == D[1]:
        y1, y2 = min(A[1], B[1]), max(A[1], B[1])
        x1, x2 = min(C[0], D[0]), max(C[0], D[0])
        return (y1 < C[1] < y2) and (x1 < A[0] < x2)
    return False

print("Searching for zero-crossing layouts...")
