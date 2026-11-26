import itertools

# We have 8 nodes: U, B, P, D, L, S, C, ST
# We can place them on a small grid, say 4 columns x 3 rows.
# Col 0: U
# Col 1: B, P, D
# Col 2: L, S, ST
# Col 3: C, etc.

# Or more generally, on a 5x3 or 4x3 grid:
# Edges:
# directed:
# U -> B, U -> P, U -> D
# B -> L
# P -> L
# L -> S
# S -> C
# P -> C
# undirected:
# D - ST
# L - ST
# C - ST

# Let's inspect the graph structure:
# Notice that U has degree 3 (B, P, D).
# ST has degree 3 (D, L, C).
# Notice the symmetry!
# U is connected to B, P, D.
# ST is connected to L, C, D.
# B is connected to U, L.
# S is connected to L, C.
# P is connected to U, L, C.
# D is connected to U, ST.

print("Symmetry analysis:")
print("U connects to: B, P, D")
print("ST connects to: L, C, D")
print("B is intermediate between U and L")
print("D is intermediate between U and ST")
print("S is intermediate between L and C")
print("P connects to U, L, C")

