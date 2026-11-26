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
            # Check if it's straight 2 cells (passing through intermediate)
            if r1 == r2: # horizontal jump of 2
                mid_c = (c1 + c2) // 2
                if grid[r1][mid_c] is not None:
                    valid = False
                    break
            elif c1 == c2: # vertical jump of 2
                mid_r = (r1 + r2) // 2
                if grid[mid_r][c1] is not None:
                    valid = False
                    break
            else: # diagonal (1, 1), can route orthogonally via corner!
                pass
        else:
            valid = False
            break
            
    if valid:
        clean_grids.append((dist, mapping))

clean_grids.sort(key=lambda x: x[0])
print(f"Found {len(clean_grids)} completely clean grids with NO node piercing!")
for i, (d, g) in enumerate(clean_grids[:5]):
    print(f"\nClean Grid {i+1} (dist={d}):")
    grid = [["." for _ in range(3)] for _ in range(3)]
    for s, (r, c) in g.items():
        grid[r][c] = s[:4]
    for row in grid:
        print("  " + "  ".join(f"{x:6s}" for x in row))
