# Let's test routing of the 3 DOWN transitions:
#
# Nodes:
# DRAINED:   [240..520, 515..605]
# DRAINING:  [1080..1360, 515..605]
# DOWN:      [660..940, 900..980] (cx=800, cy=940)
# IDLE:      [240..520, 215..305]
# ALLOCATED: [1080..1360, 215..305]
#
# Let's route 8: ALLOCATED -> DOWN: "node failure (jobs requeued or failed)" (len=38, width=547.2px)
# Leaves ALLOCATED right at (1360, 260) -> goes right to x=1480 -> down to y=730 -> left to x=860 -> down to DOWN top (860, 900)!
# Look at that horizontal segment:
# y = 730, from x = 1480 to x = 860!
# Length = 1480 - 860 = 620px!
# 620px > 547.2px!
# Clearance = (620 - 547.2)/2 = 36.4px >= 16px!
#
# Let's route 9: IDLE -> DOWN: "slurmd not responding (SlurmdTimeout) / admin" (len=45, width=648px)
# Leaves IDLE left at (240, 260) -> goes left to x=80 -> down to y=1020 -> right to x=800 -> up to DOWN bottom (800, 980)!
# Look at that horizontal segment:
# y = 1020, from x = 80 to x = 800!
# Length = 800 - 80 = 720px!
# 720px > 648px!
# Clearance = (720 - 648)/2 = 36px >= 16px!
#
# Let's route 10: DOWN -> IDLE: "resume or ReturnToService on valid registration" (len=47, width=676.8px)
# Leaves DOWN top at (740, 900) -> goes up to y=810 -> left to x=150 -> up to y=260 -> right to IDLE left (240, 260)!
# Look at that horizontal segment:
# y = 810, from x = 740 to x = 150!
# Wait! Length = 740 - 150 = 590px.
# 590px is less than 676.8px!
#
# How can we make it > 700px?
# What if it exits DOWN right edge at (940, 940) -> down to y=810?
# No, DOWN right edge is at x=940!
# If it leaves DOWN top at x=900:
# Length from 900 to 150 is 750px!
# 750px > 676.8px!
# Clearance = (750 - 676.8)/2 = 36.6px >= 16px!
#
# WAIT! Does Route 10 cross Route 8?
# Let's check:
# Route 8 enters DOWN top at x=860, from y=730.
# If Route 10 leaves DOWN top at x=900, going up to y=810:
# Route 10 goes up to y=810 at x=900, turns left across x=860 to x=150!
# BUT Route 8 is coming down at x=860 to y=900!
# So Route 10's horizontal line at y=810 WOULD CROSS Route 8's vertical line at x=860!
#
# BUT WAIT! What if Route 8 is at x=900, and Route 10 is at x=740?
# Then Route 10 (at x=740) goes up to y=810, turns left towards x=150!
# It goes to the LEFT!
# It NEVER touches x=900 (which is to the RIGHT)!
# Then Route 10's horizontal segment is from x=740 to x=150!
# But from 740 to 150 is only 590px!
#
# How can the segment be >= 700px?
# What if DOWN is shifted slightly to the right, e.g. cx = 900?
# Let's test cx = 900!
print("Testing cx = 900...")
