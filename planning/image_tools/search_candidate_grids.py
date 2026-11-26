import itertools

# We have 9 nodes in 3x3 grid
# Let's see:
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

# Let's find layouts where:
# 1. Connected nodes are adjacent in grid (Chebyshev distance <= 1 or Manhattan distance <= 2)
# 2. Cycles don't cross
# Let's score each valid placement:

best_score = 999999
best_grids = []

cells = [(r, c) for r in range(3) for c in range(3)]

# Provisioned -> Configured -> Validating -> Ready -> Cordoned -> Draining
# Draining -> Maintenance -> Validating
# Draining -> Quarantined -> Provisioned
# Ready -> Decommissioned

for p in itertools.permutations(cells):
    mapping = {s: p[i] for i, s in enumerate(states)}
    
    # Calculate total edge Manhattan distance
    dist = 0
    valid = True
    for u, v in edges:
        r1, c1 = mapping[u]
        r2, c2 = mapping[v]
        d = abs(r1 - r2) + abs(c1 - c2)
        dist += d
        # Penalize long jumps
        if d > 2:
            valid = False
            break
            
    if valid and dist < best_score:
        best_score = dist
        best_grids = [mapping]
    elif valid and dist == best_score:
        if len(best_grids) < 10:
            best_grids.append(mapping)

print(f"Best total edge Manhattan distance: {best_score}")
print(f"Found {len(best_grids)} top candidate grids.")
for i, g in enumerate(best_grids[:3]):
    print(f"\nCandidate {i+1}:")
    grid = [["." for _ in range(3)] for _ in range(3)]
    for s, (r, c) in g.items():
        grid[r][c] = s[:4]
    for row in grid:
        print("  " + "  ".join(f"{x:6s}" for x in row))
