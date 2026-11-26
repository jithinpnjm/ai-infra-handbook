import networkx as nx

G = nx.Graph()
edges = [
    ('U', 'B'),
    ('U', 'P'),
    ('U', 'D'),
    ('B', 'L'),
    ('P', 'L'),
    ('L', 'S'),
    ('S', 'C'),
    ('P', 'C'),
    ('D', 'ST'),
    ('L', 'ST'),
    ('C', 'ST')
]
G.add_edges_from(edges)
is_planar, P = nx.check_planarity(G)

for node in G.nodes():
    print(f"Node {node} neighbors CW:", list(P.neighbors_cw_order(node)))

# Let's compute a combinatorial embedding / planar coordinates
pos = nx.combinatorial_embedding_to_pos(P)
print("\nPositions:")
for k, v in pos.items():
    print(k, v)
