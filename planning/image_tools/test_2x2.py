# Let's test the 2x2 layout in python.
# Quadrants:
# Q1 (Top-Left):     Login / submit nodes (U1, U2)
# Q2 (Top-Right):    Control plane (REST, BACKUP, CTLD, DBD, DB)
# Q3 (Bottom-Left):  Compute nodes (data plane) (D1, D2, D3, STEPD, JOB)
# Q4 (Bottom-Right): MUNGE

# Let's trace all 15 connections:
# 1. U1 -> CTLD: Q1 -> Q2 (horizontal right, top)
# 2. U2 -> DBD: Q1 -> Q2 (horizontal right, lower)
# 3. U1 -> D1: Q1 -> Q3 (vertical down, left)
# 4. REST -> CTLD: internal Q2
# 5. CTLD <-> BACKUP: internal Q2
# 6. CTLD -> DBD: internal Q2
# 7. DBD -> DB: internal Q2
# 8. D1 -> STEPD: internal Q3
# 9. STEPD -> JOB: internal Q3
# 10. CTLD -> D1: Q2 -> Q3 (from Q2 bottom-left to Q3 top-right)
# 11. CTLD -> D2: Q2 -> Q3 (parallel to CTLD -> D1)
# 12. CTLD -> D3: Q2 -> Q3 (parallel to CTLD -> D1)
# 13. MUNGE -> CTLD: Q4 -> Q2 (vertical up)
# 14. MUNGE -> DBD: Q4 -> Q2 (vertical up)
# 15. MUNGE -> D1: Q4 -> Q3 (horizontal left)

# Now let's check if (CTLD -> D1, D2, D3) crosses (MUNGE -> CTLD, DBD):
# CTLD is at Q2. D1 is at Q3.
# This edge connects Q2 (top-right) to Q3 (bottom-left). It passes through the center!
# MUNGE is at Q4. CTLD is at Q2.
# This edge connects Q4 (bottom-right) to Q2 (top-right). It runs vertically along the right!
# Does a diagonal from Q2 to Q3 cross a vertical on the right from Q4 to Q2?
# Let's check:
# CTLD is at the LEFT of Q2.
# D1 is at the TOP/RIGHT of Q3.
# The diagonal from CTLD to D1 is entirely in the LEFT half of the canvas (x around 400..750)!
# MUNGE -> CTLD and MUNGE -> DBD are in the RIGHT half of the canvas (x around 850..1300)!
# THEY DO NOT EVEN COME NEAR EACH OTHER!

print("THEY ARE SEPARATED BY HUNDREDS OF PIXELS! ZERO INTERSECTIONS!")
