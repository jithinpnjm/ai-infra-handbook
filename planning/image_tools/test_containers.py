# Let's test the 3 container options.

# In Option A (Stacked Vertically: Users on top, Control in middle, Compute on bottom):
# Height of canvas: 1200
# Users: y = 80 .. 280 (h=200)
# Control: y = 330 .. 680 (h=350)
# Compute: y = 730 .. 1120 (h=390)
# MUNGE: could be a bar between Control and Compute, or on the right side!
#
# Let's check connections between containers in Option A:
# Users -> Control:
#   U1 -> CTLD
#   U2 -> DBD
# Control -> Compute:
#   CTLD -> D1
#   CTLD -> D2
#   CTLD -> D3
# Compute internal:
#   D1 -> STEPD -> JOB
# Users -> Compute:
#   U1 -> D1
# MUNGE:
#   MUNGE -> CTLD
#   MUNGE -> DBD
#   MUNGE -> D1

# Now look at:
# U1 -> D1: from Users (top) to Compute (bottom).
# If it goes down the LEFT outer edge (x=30):
# It completely bypasses Control plane without touching it or crossing anything!
#
# Now what about MUNGE?
# MUNGE connects to CTLD, DBD, and D1.
# What if MUNGE is placed on the RIGHT side, or between Control and Compute?
# Let's check!
print("Testing Option A routing...")
