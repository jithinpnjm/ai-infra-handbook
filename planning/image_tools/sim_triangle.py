# Let's test the triangle layout in Python:
# U1: (x=100..450, y=100..200)
# CTLD: (x=550..950, y=100..250)
# D1: (x=100..450, y=350..450)
#
# Edges:
# 1. U1 -> CTLD: from (450, 150) to (550, 150) -> horizontal, clear!
# 2. U1 -> D1: from (275, 200) to (275, 350) -> vertical down, clear!
# 3. CTLD -> D1: from (550, 220) to (450, 370) -> diagonal down-left, clear!
#
# What about D2, D3?
# D2, D3 are inside Compute nodes. Where?
# D1 is at x=100..450, y=350..450.
# D2 could be at x=100..260, y=500..570?
# But wait! D1 -> STEPD -> JOB:
# STEPD at x=300..450, y=500..570?
# JOB at x=300..450, y=620..690?
# And CTLD -> D2, CTLD -> D3:
# If D2 and D3 are below CTLD?
# But wait! Subgraph grouping!
# Remember the source has 3 subgraphs:
# subgraph users["Login / submit nodes"] (U1, U2)
# subgraph control["Control plane"] (CTLD, BACKUP, DBD, DB, REST)
# subgraph compute["Compute nodes (data plane)"] (D1, D2, D3, STEPD)
# MUNGE is standalone.

# If U1 and U2 must be in subgraph "Login / submit nodes",
# then U1 and U2 must be inside one container box!
# If CTLD, BACKUP, DBD, DB, REST must be in subgraph "Control plane",
# they must be inside one container box!
# If D1, D2, D3, STEPD are in subgraph "Compute nodes (data plane)",
# they must be inside one container box!

print("Subgraphs must be distinct bounding boxes!")
