import networkx as nx

# Let's inspect the faces of the planar embedding:
# Edges:
# U -> B, U -> P, U -> D
# B -> L, P -> L
# L -> S, S -> C
# P -> C
# D - ST, L - ST, C - ST

# What if:
# Look at the three user access methods:
# 1. SSH: U -> B -> L
# 2. Web / Portal: U -> P -> L and P -> C
# 3. Data: U -> D -> ST

# Can we arrange rows as:
# Row 1 (top): P (Open OnDemand portal)
# Row 2 (middle-upper): B (Bastion) and L (Login nodes) and S (Slurm controller) and C (Compute nodes)
# Row 3 (bottom): D (Data transfer nodes) and ST (Parallel file system)
# Wait! In this arrangement, how does P connect to C, and how does L connect to ST?
# If P is in Row 1:
# P connects to C. Since C is in Row 2, P -> C goes down-right to C!
# But L is in Row 2, and ST is in Row 3.
# L connects to ST: can L connect to ST?
# Where is P? P is in Row 1!
# If P is in Row 1, P is ABOVE Row 2!
# So P -> C goes OVER Row 2 (or along Row 1 and down into C).
# ST is in Row 3 (BELOW Row 2).
# L is in Row 2. So L connects DOWN into ST in Row 3.
# Does L -> ST cross P -> C?
# NO! Because P -> C is at the TOP (Row 1), while L -> ST is at the BOTTOM (going from Row 2 to Row 3)!
# They are on OPPOSITE SIDES of Row 2!

print("Testing top/bottom split:")
