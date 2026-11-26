import math

# Let's test a clean, elegant layout:
# Canvas: 1600 x 1000
#
# Nodes: (box width = 260, height = 80)
# Top Row (y = 220):
# DRAINED:   cx = 400,  cy = 220  -> [270..530, 180..260]
# DRAINING:  cx = 1200, cy = 220  -> [1070..1330, 180..260]
#
# Middle Row (y = 520):
# IDLE:      cx = 400,  cy = 520  -> [270..530, 480..560]
# ALLOCATED: cx = 1200, cy = 520  -> [1070..1330, 480..560]
#
# Bottom Row (y = 900):
# DOWN:      cx = 800,  cy = 900  -> [670..930, 860..940]

# Now let's examine the 3 transitions connected to DOWN:
# 1. ALLOCATED -> DOWN: "node failure (jobs requeued or failed)" (len=38, width=547.2px)
# Arrow leaves ALLOCATED at (1200, 560) [bottom-center of ALLOCATED]
# Goes down to y = 720.
# Then turns left to x = 800.
# Then goes down into DOWN top (800, 860).
# Look at that horizontal segment:
# y = 720, from x = 1200 to x = 800.
# Length = 1200 - 800 = 400px.
# But what if the arrow leaves ALLOCATED right edge at (1330, 520)?
# Goes right to x = 1500, down to y = 900, left into DOWN right edge (930, 900)!
# Horizontal segment: y = 900, from x = 1500 to x = 930.
# Length = 1500 - 930 = 570px!
# 547.2px fits on 570px with 11.4px padding on each end.
# If it goes to x = 1540: length = 1540 - 930 = 610px!
# 610px > 547.2px with 31.4px padding on each end! (>= 16px!)
#
# 2. What about IDLE -> DOWN and DOWN -> IDLE?
# Text lengths:
# IDLE -> DOWN: "slurmd not responding (SlurmdTimeout) / admin" (len=45, width=648px)
# DOWN -> IDLE: "resume or ReturnToService on valid registration" (len=47, width=676.8px)
#
# Can IDLE -> DOWN go around the left?
# Leaves IDLE left edge at (270, 520) -> goes left to x = 60 -> down to y = 900 -> right into DOWN left edge (670, 900)!
# Horizontal segment: y = 900, from x = 60 to x = 670.
# Length = 670 - 60 = 610px.
# Wait! 610px is less than 648px!
#
# How can we make it > 700px?
# What if DOWN is shifted slightly to the right, e.g. cx = 950?
# Then from x = 60 to x = (950 - 130 = 820):
# Length = 820 - 60 = 760px!
# 760px > 648px! Clearance = (760 - 648)/2 = 56px!
#
# And what about DOWN -> IDLE (676.8px)?
# If DOWN is at cx = 950:
# Arrow leaves DOWN top (900, 860) -> goes up to y = 680 -> left to x = 150 -> up into IDLE bottom (x=350, y=560)?
# Length from x = 900 to x = 150 is 750px!
# 750px > 676.8px! Clearance = (750 - 676.8)/2 = 36.6px!
#
# WAIT! LOOK AT THAT!
# If DOWN is at cx = 950 (or 920):
# Both IDLE -> DOWN and DOWN -> IDLE have horizontal segments > 750px!
# AND ALLOCATED -> DOWN:
# Leaves ALLOCATED bottom (1200, 560) -> goes down to y = 800 -> left to DOWN (x=1050, y=860)?
# Wait, ALLOCATED -> DOWN needs 547.2px!
# If it goes to x = 1540 -> down to y = 920 -> left into DOWN right edge:
# DOWN right edge is at 950 + 130 = 1080.
# From 1540 to 1080 = 460px (too short).

print("Testing further...")
