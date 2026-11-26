# Let's test routing for the 3 DOWN transitions:
# Canvas: 1600 x 1100
#
# Nodes:
# IDLE: cx=360, cy=480 (box: 230..490, 438..522)
# ALLOCATED: cx=1240, cy=480 (box: 1110..1370, 438..522)
# DOWN: cx=800, cy=960 (box: 670..930, 918..1002)
#
# Transition 1: ALLOCATED -> DOWN: "node failure (jobs requeued or failed)" (len=38, width=547.2px)
# Leaves ALLOCATED right at (1370, 480) -> goes right to x=1480 -> down to y=850 -> left to x=800 -> down to DOWN top (800, 918)!
# Look at that horizontal segment:
# y = 850, from x = 1480 to x = 800!
# Length = 1480 - 800 = 680px!
# 680px > 547.2px!
# Clearance = (680 - 547.2)/2 = 66.4px >= 16px!
#
# Transition 2: IDLE -> DOWN: "slurmd not responding (SlurmdTimeout) / admin" (len=45, width=648px)
# Leaves IDLE bottom at (300, 522) -> goes down to y=1050 -> right to x=800 -> up to DOWN bottom (800, 1002)!
# Look at that horizontal segment:
# y = 1050, from x = 300 to x = 800.
# Length = 800 - 300 = 500px.
# Wait! 500px is less than 648px!
# Can it start further left?
# Leaves IDLE left at (230, 480) -> goes left to x=80 -> down to y=1050 -> right to x=800 -> up to DOWN bottom (800, 1002)!
# Look at that horizontal segment:
# y = 1050, from x = 80 to x = 800!
# Length = 800 - 80 = 720px!
# 720px > 648px!
# Clearance = (720 - 648)/2 = 36px >= 16px!
#
# Transition 3: DOWN -> IDLE: "resume or ReturnToService on valid registration" (len=47, width=676.8px)
# Leaves DOWN top at (740, 918) -> goes up to y=680 -> left to x=80 -> up to y=480 -> right to IDLE left (230, 480)?
# Wait! Does Transition 3 cross Transition 2?
# Let's check:
# Transition 2 leaves IDLE left at y=480, goes left to x=80, down to y=1050.
# Transition 3 comes from DOWN (740, 918) up to y=680, left to x=80, up to y=480...
# They both use x=80 and y=480! They would overlap on that wire!
# Can Transition 3 enter IDLE at the bottom (x=420, y=522)?
# If Transition 3 goes:
# From DOWN (740, 918) -> up to y=680 -> left to x=420 -> up to IDLE bottom (420, 522):
# The horizontal segment is from x=740 to x=420 = 320px. Too short for 676.8px!
#
# BUT WAIT!
# Where does Transition 3 go if DOWN is in a different position?
# What if DOWN is at the bottom-right or bottom-left?
# Let's test!
print("Done check.")
