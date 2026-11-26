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

# Let's search across all 9! = 362,880 grid permutations
# We want a layout where:
# Every edge can be routed orthogonally along grid tracks without crossing any node or other edge.

cells = [(r, c) for r in range(3) for c in range(3)]

# Let's test a very natural, logical layout:
# What if:
# Row 0: Provisioned, Configured, Validating
# Row 1: Quarantined, Maintenance, Ready
# Row 2: (empty), Draining, Cordoned
# Wait! We had 9 cells, but what if canvas has 4 columns or 3x3?
# Let's test 3x3 grids where ALL 10 edges are adjacent (distance = 1)!
# Can distance of all edges be 1?
# Graph has 10 edges. In 3x3 grid, can all edges have Manhattan distance 1?
# Let's check!

dist_1_grids = []
for p in itertools.permutations(cells):
    mapping = {s: p[i] for i, s in enumerate(states)}
    all_adj = True
    for u, v in edges:
        r1, c1 = mapping[u]
        r2, c2 = mapping[v]
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            all_adj = False
            break
    if all_adj:
        dist_1_grids.append(mapping)

print(f"Number of grids where ALL 10 edges have distance 1: {len(dist_1_grids)}")
