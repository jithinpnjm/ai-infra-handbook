# Let's test routing where both Path 1 and Path 2 have >= 700px horizontal runways:
#
# Nodes:
# IDLE: cx = 400, cy = 450
# DOWN: cx = 800, cy = 950
# ALLOCATED: cx = 1200, cy = 450
#
# What if:
# Look at where ALLOCATED -> DOWN goes:
# ALLOCATED (1200, 450) -> DOWN (800, 950):
# Text: "node failure (jobs requeued or failed)" (len=38, width=547.2px)
# If it goes from ALLOCATED (1200, 490) -> down to y = 780 -> left to x = 600?
# Wait!
# What if DOWN is at the bottom right, or bottom left, or what if DOWN is at (x=1200, y=950)?
# Wait! Look at that:
# What if DOWN is at (x=1200, y=950)?
# Then ALLOCATED (1200, 450) -> DOWN (1200, 950) is DIRECTLY VERTICAL!
# Then:
# IDLE (400, 450) <---> DOWN (1200, 950):
# They are on OPPOSITE SIDES of the canvas!
# From x = 400 to x = 1200 is 800px!
# 800px!
# Both IDLE -> DOWN and DOWN -> IDLE go ACROSS THE ENTIRE CANVAS!
# Distance = 800px!
# And 800px > 677px!
# Both 648px and 677px fit with HUGE PADDING across the 800px span!
#
# BUT WAIT!
# If DOWN is at (1200, 950):
# Where are DRAINED and DRAINING?
# If DRAINED is at (400, 200) and DRAINING is at (1200, 200):
# Then ALLOCATED is at (1200, 450).
# BUT ALLOCATED connects to DRAINING (at 1200, 200) and DOWN (at 1200, 950)!
# And DRAINING connects to DRAINED (at 400, 200)!
# And DRAINED connects to IDLE (at 400, 450)!
# And IDLE connects to ALLOCATED (at 1200, 450)!
#
# LOOK AT THIS GEOMETRY!
# Let's trace EVERY connection:
# 1. DRAINED is at (400, 200).
# 2. DRAINING is at (1200, 200).
# 3. IDLE is at (400, 550).
# 4. ALLOCATED is at (1200, 550).
# 5. DOWN is at (1200, 920).
#
# Look at the 2 columns:
# Left column (x = 400):
#   - DRAINED (y = 200)
#   - IDLE (y = 550)
# Right column (x = 1200):
#   - DRAINING (y = 200)
#   - ALLOCATED (y = 550)
#   - DOWN (y = 920)
#
# Now let's trace EVERY connection in this 2-column layout:
# 1. [*] -> IDLE: from left (x=140, y=550) into IDLE.
# 2. IDLE <-> ALLOCATED: horizontal between (400, 550) and (1200, 550).
#    Distance = 800px!
#    - IDLE -> ALLOCATED: "job starts" (144px)
#    - ALLOCATED -> IDLE: "job ends" (115px)
# 3. DRAINING -> DRAINED: horizontal between (1200, 200) and (400, 200).
#    Distance = 800px!
#    - DRAINING -> DRAINED: "running jobs finish" (274px)
# 4. Vertical connections on the left:
#    - IDLE -> DRAINED: straight UP from (400, 550) to (400, 200).
#    - DRAINED -> IDLE: straight DOWN from (400, 200) to (400, 550).
#    Both are in Col 1!
# 5. Vertical connection on the right (top):
#    - ALLOCATED -> DRAINING: straight UP from (1200, 550) to (1200, 200).
#    In Col 2!
# 6. Vertical connection on the right (bottom):
#    - ALLOCATED -> DOWN: straight DOWN from (1200, 550) to (1200, 920).
#    In Col 2!
#    Wait! What is the label on ALLOCATED -> DOWN?
#    "node failure (jobs requeued or failed)" (547.2px)!
#    Wait! If it is vertical, how does a 547.2px text fit?
#    Distance from y=550 to y=920 is 370px.
#    A horizontal text of 547px would stick out horizontally!
#    Can it go across horizontally?
#    What if DOWN is on the LEFT instead of the right?

print("Evaluating...")
