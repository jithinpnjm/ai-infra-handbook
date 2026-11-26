# Let's test the 3 failure routes on a 1600 x 1100 canvas:
#
# Nodes:
# Title at y = 60.
#
# Middle Row:
# IDLE: cx = 400, cy = 480 (box: 270..530, 438..522)
# ALLOCATED: cx = 1200, cy = 480 (box: 1070..1330, 438..522)
#
# Bottom Row:
# DRAINED: cx = 400, cy = 800 (box: 270..530, 758..842)
# DRAINING: cx = 1200, cy = 800 (box: 1070..1330, 758..842)
#
# Top Row:
# DOWN: cx = 800, cy = 200 (box: 670..930, 158..242)
#
# Let's look at the region above Middle Row (y in [100, 438]):
# Height = 338px. Width = 1600px.
# In this region, we only have DOWN (670..930, 158..242).
#
# We need to route 3 connections to DOWN:
# 1. ALLOCATED -> DOWN: "node failure (jobs requeued or failed)" (len=38, width=547.2px)
# 2. IDLE -> DOWN: "slurmd not responding (SlurmdTimeout) / admin" (len=45, width=648px)
# 3. DOWN -> IDLE: "resume or ReturnToService on valid registration" (len=47, width=676.8px)
#
# Can we route them in this 1600 x 338 region?
# Let's trace:
#
# Route 1: ALLOCATED -> DOWN
# Leaves ALLOCATED right at (1330, 480) [or top at (1200, 438)]
# What if it leaves ALLOCATED top at (1260, 438)?
# Goes up to y = 200: (1260, 438) -> (1260, 200) -> (930, 200) [hits DOWN right edge]
# Length of horizontal segment: from 1260 to 930 = 330px.
# Too short for 547px!
# BUT what if it goes up to y = 140, right to x = 1500, down to y = 200... wait,
# What if it leaves ALLOCATED top at (1140, 438)?
# Goes up to y = 300 -> left to x = 500? No, that crosses IDLE.
#
# What if Route 1 goes around to the right of ALLOCATED:
# Leaves ALLOCATED right at (1330, 480) -> goes to x = 1520 -> up to y = 200 -> left to DOWN right (930, 200)?
# Length of horizontal segment: from 1520 to 930 = 590px!
# 590px > 547.2px!
# Clearance = (590 - 547.2)/2 = 21.4px >= 16px!
# PASSES ROUTE 1!
#
# Now let's check Route 2 and Route 3 on the left side of DOWN:
# Left edge of DOWN is at x = 670, y in [158, 242].
# Top of DOWN is at y = 158, x in [670, 930].
# Bottom of DOWN is at y = 242, x in [670, 930].
#
# Left side of canvas has x from 40 to 670.
# That is 630px wide!
# Wait! 630px is less than 676.8px!
# To get >= 720px, the arrow must start further right or extend further left!
# Look:
# If DOWN is shifted to cx = 900 (box: 770..1030):
# Then left edge of DOWN is at x = 770!
# From x = 50 to x = 770 is:
# 770 - 50 = 720px!
# 720px > 676.8px!
# Clearance = (720 - 676.8)/2 = 21.6px >= 16px!
# And from x = 900 to x = 1520:
# 1520 - 1030 = 490px... wait!
# If DOWN is at 900, right side is 1030, so 1520 - 1030 = 490px < 547px.

print("Testing...")
