import itertools

# Nodes:
nodes = [
    "Provisioned",
    "Configured",
    "Validating",
    "Ready",
    "Cordoned",
    "Draining",
    "Maintenance",
    "Quarantined",
    "Decommissioned"
]

# Directed edges:
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

# A 3x3 grid has 9 cells: (r, c) for r in 0..2, c in 0..2
# Also Start [*] connects to Provisioned, Decommissioned connects to End [*].

# Let's test what assignments make sense logically:
# Flow:
# Provisioned -> Configured -> Validating -> Ready
# Ready -> Cordoned -> Draining
# Draining -> Maintenance -> Validating
# Draining -> Quarantined -> Provisioned
# Ready -> Decommissioned -> End

# Consider:
# If Provisioned is at (0, 0)
# Configured at (0, 1)
# Validating at (0, 2)
# Ready at (1, 2)
# Cordoned at (2, 2)
# Draining at (2, 1)
# Maintenance at (1, 1)
# Quarantined at (1, 0)
# Decommissioned at (2, 0) or (1, 3)?

print("Testing clockwise ring / spiral layout...")
grid_map = {
    "Provisioned": (0, 0),
    "Configured": (0, 1),
    "Validating": (0, 2),
    "Ready": (1, 2),
    "Cordoned": (2, 2),
    "Draining": (2, 1),
    "Maintenance": (1, 1),
    "Quarantined": (1, 0),
    "Decommissioned": (2, 0)
}

for src, dst in edges:
    r1, c1 = grid_map[src]
    r2, c2 = grid_map[dst]
    print(f"{src:14s} ({r1},{c1}) -> {dst:14s} ({r2},{c2}) | d_row={r2-r1:2d}, d_col={c2-c1:2d}")
