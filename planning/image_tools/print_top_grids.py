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

clean_grids = []

for p in itertools.permutations(cells):
    mapping = {s: p[i] for i, s in enumerate(states)}
    grid = [[None for _ in range(3)] for _ in range(3)]
    for s, (r, c) in mapping.items():
        grid[r][c] = s
        
    valid = True
    dist = 0
    for u, v in edges:
        r1, c1 = mapping[u]
        r2, c2 = mapping[v]
        d = abs(r1 - r2) + abs(c1 - c2)
        dist += d
        if d == 1:
            continue
        elif d == 2:
            if r1 == r2:
                mid_c = (c1 + c2) // 2
                if grid[r1][mid_c] is not None:
                    valid = False
                    break
            elif c1 == c2:
                mid_r = (r1 + r2) // 2
                if grid[mid_r][c1] is not None:
                    valid = False
                    break
            else: # diagonal jump
                # diagonal can be routed through an empty cell if available
                pass
        else:
            valid = False
            break
            
    if valid:
        clean_grids.append((dist, mapping))

clean_grids.sort(key=lambda x: x[0])

# Let's inspect the first 12 clean grids:
for i in range(min(12, len(clean_grids))):
    d, g = clean_grids[i]
    print(f"\n--- Grid {i+1} (total dist={d}) ---")
    grid = [["." for _ in range(3)] for _ in range(3)]
    for s, (r, c) in g.items():
        grid[r][c] = s[:4]
    for row in grid:
        print("  " + "  ".join(f"{x:6s}" for x in row))
    # print edges and their directions
    print("  Edges:")
    for u, v in edges:
        r1, c1 = g[u]
        r2, c2 = g[v]
        print(f"    {u[:4]} ({r1},{c1}) -> {v[:4]} ({r2},{c2})")
