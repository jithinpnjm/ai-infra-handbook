import itertools
import time

# Graph edges (excluding Start and End for now, or including them)
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

nodes = [
    "Provisioned", "Configured", "Validating", "Ready",
    "Cordoned", "Draining", "Maintenance", "Quarantined", "Decommissioned"
]

# We want to place these 9 nodes onto a 3x3 or 4x3 grid such that:
# Orthogonal/straight connections do not cross, and no edge passes through an intermediate node.
# Let's test a 3x3 grid: positions (r, c) for r in [0, 1, 2], c in [0, 1, 2]

def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(A,B,C,D):
    # Strict segment intersection
    if A == C or A == D or B == C or B == D:
        return False
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

def point_on_segment(P, A, B):
    # P strictly between A and B
    if P == A or P == B:
        return False
    # Cross product 0 and within bounding box
    cross = (P[1]-A[1])*(B[0]-A[0]) - (P[0]-A[0])*(B[1]-A[1])
    if cross != 0:
        return False
    return min(A[0], B[0]) <= P[0] <= max(A[0], B[0]) and min(A[1], B[1]) <= P[1] <= max(A[1], B[1])

# If edges are drawn as straight lines between grid centers:
grid_positions = [(r, c) for r in range(3) for c in range(3)]

valid_layouts = []
t0 = time.time()
count = 0
for p in itertools.permutations(grid_positions):
    count += 1
    pos = {node: p[i] for i, node in enumerate(nodes)}
    
    # Check if any edge passes through any node
    blocked = False
    for u, v in edges:
        A, B = pos[u], pos[v]
        for w in nodes:
            if w != u and w != v and point_on_segment(pos[w], A, B):
                blocked = True
                break
        if blocked:
            break
    if blocked:
        continue
    
    # Check if any two edges intersect
    crosses = False
    for i in range(len(edges)):
        u1, v1 = edges[i]
        A, B = pos[u1], pos[v1]
        for j in range(i+1, len(edges)):
            u2, v2 = edges[j]
            C, D = pos[u2], pos[v2]
            if intersect(A, B, C, D):
                crosses = True
                break
        if crosses:
            break
    if not crosses:
        valid_layouts.append(pos)
        if len(valid_layouts) >= 5:
            break

print(f"Checked in {time.time()-t0:.2f}s, found {len(valid_layouts)} valid layouts with straight lines in 3x3!")
for idx, layout in enumerate(valid_layouts):
    print(f"\nLayout {idx+1}:")
    grid = [["" for _ in range(3)] for _ in range(3)]
    for node, (r, c) in layout.items():
        grid[r][c] = node[:6]
    for r in range(3):
        print("  " + " | ".join(f"{grid[r][c]:10}" for c in range(3)))
