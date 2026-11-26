# Let's test uncrossing U2->DBD and CTLD->D1.
# What are the edges between Q1, Q2, Q3?
# From Q1:
#   U1 -> CTLD
#   U1 -> D1
#   U2 -> DBD
# From Q2:
#   CTLD -> D1, D2, D3
#   CTLD -> DBD
#   DBD -> DB
#   REST -> CTLD
#   BACKUP <-> CTLD
# From Q4 (MUNGE):
#   MUNGE -> CTLD
#   MUNGE -> DBD
#   MUNGE -> D1

# Look at the three tiers:
# What if:
# Tier 1 (Top): Login / submit nodes (U1, U2)
# Tier 2 (Middle): Control plane (CTLD, DBD, DB, REST, BACKUP)
# Tier 3 (Bottom): Compute nodes (D1, D2, D3, STEPD, JOB) + MUNGE
#
# In Tier 1:
# U1 is on the left.
# U2 is on the right.
#
# In Tier 2:
# CTLD is on the left (directly under U1).
# DBD is on the right (directly under U2).
#
# In Tier 3:
# Compute nodes (D1, D2, D3, STEPD, JOB) is on the left (directly under CTLD).
# MUNGE is on the right (directly under DBD).

print("Let's analyze Tier 1 -> Tier 2 -> Tier 3:")
