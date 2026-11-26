# Let's explore all topological permutations of:
# Nodes:
# U1, U2
# REST, BACKUP, CTLD, DBD, DB
# D1, D2, D3, STEPD, JOB
# MUNGE

# Let's see: can we arrange them so that EVERY arrow is direct (no detour)?
# Let's check:
# Edges:
# U1 -> CTLD
# U1 -> D1
# U2 -> DBD
# REST -> CTLD
# BACKUP <-> CTLD
# CTLD -> DBD
# DBD -> DB
# CTLD -> D1
# CTLD -> D2
# CTLD -> D3
# D1 -> STEPD
# STEPD -> JOB
# MUNGE -.-> CTLD
# MUNGE -.-> D1
# MUNGE -.-> DBD

# Notice:
# 1. DBD connects to: U2, CTLD, DB, MUNGE.
# 2. D1 connects to: U1, CTLD, STEPD, MUNGE.
# 3. CTLD connects to: U1, REST, BACKUP, DBD, D1, D2, D3, MUNGE.
# 4. MUNGE connects to: CTLD, DBD, D1.

# Notice how SYMMETRIC this is!
# U1 connects to CTLD and D1.
# U2 connects to DBD.
# DB connects to DBD.
# D1 connects to STEPD -> JOB.
# CTLD connects to REST, BACKUP, D2, D3, and DBD, D1.

print("Checking layout options...")
