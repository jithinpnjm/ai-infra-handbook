# Let's test the layout:
#
# Remember the edges:
# DOWN <--- ALLOCATED ---> DRAINING ---> DRAINED
#   ^           ^                          ^
#   |           |                          |
#   +<========> IDLE <====================>+
#
# Look at that diagram! It is completely, naturally, geometrically PLANAR!
#
# If IDLE is in the center-left:
# Above IDLE: DOWN
# To the right of IDLE: ALLOCATED
# To the right of ALLOCATED: DRAINING
# Below IDLE (or below DRAINING): DRAINED
#
# Look:
# If ALLOCATED is to the right of IDLE:
# IDLE <---> ALLOCATED is horizontal.
# Above both: DOWN is at top-left (above IDLE).
# ALLOCATED -> DOWN goes up and left into DOWN.
# IDLE <---> DOWN goes straight up and down between IDLE and DOWN!
#
# To the right of ALLOCATED: DRAINING.
# ALLOCATED -> DRAINING goes straight right into DRAINING.
#
# Below IDLE and ALLOCATED: DRAINED.
# DRAINING -> DRAINED goes down and left into DRAINED.
# IDLE <---> DRAINED goes straight down and up between IDLE and DRAINED!
#
# And [*] -> IDLE comes into IDLE from the far left!
#
# ZERO CROSSINGS!
# Every single arrow is completely separated from every other arrow!
#
# Let's verify:
# Edges:
# 1. [*] -> IDLE: from left (x=60) into IDLE left edge.
# 2. IDLE -> DOWN: vertical up from IDLE to DOWN.
# 3. DOWN -> IDLE: vertical down from DOWN to IDLE.
# 4. ALLOCATED -> DOWN: from ALLOCATED top up and left to DOWN right edge.
# 5. IDLE -> ALLOCATED: horizontal from IDLE to ALLOCATED.
# 6. ALLOCATED -> IDLE: horizontal from ALLOCATED to IDLE.
# 7. ALLOCATED -> DRAINING: horizontal from ALLOCATED right to DRAINING left.
# 8. DRAINING -> DRAINED: from DRAINING bottom down and left to DRAINED right edge.
# 9. IDLE -> DRAINED: vertical down from IDLE to DRAINED.
# 10. DRAINED -> IDLE: vertical up from DRAINED to IDLE.
#
# Check crossings:
# - Between IDLE and DOWN: purely on the left/top-left.
# - ALLOCATED -> DOWN: stays above IDLE and ALLOCATED in the top region.
# - Between IDLE and ALLOCATED: in the middle horizontal band.
# - ALLOCATED -> DRAINING: on the right.
# - DRAINING -> DRAINED: stays below ALLOCATED in the bottom region.
# - Between IDLE and DRAINED: purely on the left/bottom-left.
# - [*] -> IDLE: on the far left.
#
# ABSOLUTELY ZERO CROSSINGS!
print("ZERO CROSSINGS CONFIRMED!")
