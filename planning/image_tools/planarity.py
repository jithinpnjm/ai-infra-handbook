import networkx as nx

G = nx.Graph()
# Undirected graph check for planarity:
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
print(f"Is planar? {is_planar}")

# If planar, let's find a planar embedding!
if is_planar:
    # Print clockwise order of neighbors for each node in embedding
    for node in G.nodes():
        print(f"Node {node} neighbors CW:", P.neighbors_cw_order(node))
