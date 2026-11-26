import itertools

# Graph edges:
edges = [
    ("Start", "Provisioned"),
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
    ("Decommissioned", "End")
]

# Let us analyze the cycles and faces of this graph.
# Cycles:
# C1: V -> R -> Cd -> Dr -> M -> V (length 5)
# C2: P -> C -> V -> R -> Cd -> Dr -> Q -> P (length 7)
# Note that Dr -> M -> V and Dr -> Q -> P -> C -> V form two paths between Dr and V!
# This means:
# Inside face: V, R, Cd, Dr, M
# Outside face: P, C, V, M, Dr, Q (with Dr -> M -> V sharing the M-V edge? No, sharing Dr and V endpoints!)

print("Topology analysis:")
print("Path from Dr to V: (1) Dr -> M -> V; (2) Dr -> Q -> P -> C -> V.")
print("Path from V to Dr: V -> R -> Cd -> Dr.")
print("Branch from R: R -> Decommissioned -> End.")
print("Branch into P: Start -> Provisioned.")
