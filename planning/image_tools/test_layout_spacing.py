# Layout generator and intersection checker
import math

# Let's define grid coordinates for nodes
# We have 1600 x 1100 canvas (H=1100)
# Margin top: Title at y=60
# Let's consider a clean 3-row or 4-row layout

# Let's inspect the nodes:
# Start [*]
# Provisioned
# Configured
# Validating
# Ready
# Decommissioned
# End [*]
# Cordoned
# Draining
# Maintenance
# Quarantined

# What if:
# Row 1 (y=200):
# Start -> Provisioned -> Configured -> Validating -> Ready -> Decommissioned -> End
# Can 5 or 6 nodes fit on Row 1?
# Wait! Let's check widths:
# If Row 1 has Provisioned, Configured, Validating, Ready:
# That's 4 nodes.
# 1600 width:
# Node boxes: width = 280. 4 nodes * 280 = 1120.
# 3 gaps between them: (1600 - 1120 - 2*60) / 3 = 120 px gap.
# In a 120 px horizontal gap, can a 50-character label fit?
# NO! 50-char label needs at least 250-350 px!
# A horizontal gap of 120 px cannot hold a 350 px transition card!

print("Testing card widths vs gaps...")
