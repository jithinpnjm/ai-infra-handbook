import networkx as nx

# We know the graph is planar.
# Let's find an embedding using networkx planar embedding
G = nx.DiGraph()
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

# Find planar embedding
is_planar, P = nx.check_planarity(G)
print("Planar?", is_planar)

# Print neighbors in cyclic order for each node
for node in P.nodes():
    print(f"Node {node}: cyclic neighbors = {list(P.neighbors_cw_order(node))}")
