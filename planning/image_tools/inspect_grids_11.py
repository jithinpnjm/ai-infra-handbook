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

cells = [(r, c) for r in range(3) for c in range(3)]

# Find grids with total distance 11:
grids_11 = []
for p in itertools.permutations(cells):
    mapping = {s: p[i] for i, s in enumerate(states)}
    dist = 0
    valid = True
    for u, v in edges:
        r1, c1 = mapping[u]
        r2, c2 = mapping[v]
        d = abs(r1 - r2) + abs(c1 - c2)
        dist += d
        if d > 2:
            valid = False
            break
    if valid and dist == 11:
        grids_11.append(mapping)

print(f"Total grids with total distance 11: {len(grids_11)}")

# For each grid, see which edge is the distance-2 edge:
for i, g in enumerate(grids_11[:8]):
    print(f"\n--- Grid {i+1} ---")
    grid = [["." for _ in range(3)] for _ in range(3)]
    for s, (r, c) in g.items():
        grid[r][c] = s[:4]
    for row in grid:
        print("  " + "  ".join(f"{x:6s}" for x in row))
    for u, v in edges:
        r1, c1 = g[u]
        r2, c2 = g[v]
        d = abs(r1 - r2) + abs(c1 - c2)
        if d == 2:
            print(f"  Distance-2 edge: {u} ({r1},{c1}) -> {v} ({r2},{c2})")
