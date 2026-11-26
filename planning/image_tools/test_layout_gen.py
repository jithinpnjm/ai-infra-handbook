import re
import xml.etree.ElementTree as ET

# Canvas dimensions
WIDTH = 1600
HEIGHT = 1050

# Colors
BG_COLOR = "#f5f8f5"
TEXT_COLOR = "#303a36"
MAIN_GREEN = "#207448"
LIGHT_GREEN = "#e8f1ea"
ORANGE = "#db8129"

# Let's consider 3 rows of nodes:
# Top Row (y ~ 220):
# DRAINED (left), DRAINING (right)
#
# Middle Row (y ~ 500):
# IDLE (left), ALLOCATED (right)
#
# Bottom Row (y ~ 820):
# DOWN (center)

# Wait! Let's check the arrows between ALLOCATED and DOWN, IDLE and DOWN:
# ALLOCATED is at (x=1150, y=500)
# DOWN is at (x=800, y=820)
# Arrow ALLOCATED -> DOWN: "node failure (jobs requeued or failed)"
# Can it go from ALLOCATED right side (x=1300, y=500) -> down to y=880 -> left to DOWN (x=950, y=880)?
# Along that horizontal stretch (x=1300 down to 950):
# Wait, 1300 - 950 = 350px.
# But "node failure (jobs requeued or failed)" is 547px!
# 350px is shorter than 547px!
# If the arrow goes:
# From ALLOCATED right side: x=1350, y=500 -> right to x=1500 -> down to y=880 -> left to DOWN right side (x=950, y=880)!
# That horizontal stretch from 1500 to 950 is 550px.
# What if it's placed along a vertical stretch or what if ALLOCATED -> DOWN is placed differently?
# Let's test different positions!

