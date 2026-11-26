import networkx as nx

# Define the graph
G = nx.DiGraph()

# Nodes:
# S (Start [*]), Provisioned (P), Configured (C), Validating (V), Ready (R)
# Cordoned (Cd), Draining (Dr), Maintenance (M), Quarantined (Q)
# Decommissioned (Dc), E (End [*])

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
    ("Decommissioned", "End"),
]

G.add_edges_from(edges)

# Check if planar
is_planar, embedding = nx.check_planarity(G)
print(f"Is graph planar? {is_planar}")

if is_planar:
    print("Embedding faces / planar structure exists!")
