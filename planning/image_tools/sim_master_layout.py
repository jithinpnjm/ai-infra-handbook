# Let's test the Master Layout:
# Canvas: 1600 x 950 (or 1000)
#
# Nodes: (box width = 250, height = 80)
# NW, NH = 250, 80
#
# IDLE:      cx = 320,  cy = 280 -> [195..445, 240..320]
# ALLOCATED: cx = 780,  cy = 280 -> [655..905, 240..320]
# DRAINED:   cx = 320,  cy = 580 -> [195..445, 540..620]
# DRAINING:  cx = 780,  cy = 580 -> [655..905, 540..620]
# DOWN:      cx = 1420, cy = 430 -> [1295..1545, 390..470]

# Let's check ALL 10 arrows in this Master Layout:
# 1. [*] -> IDLE:
#    Start: (80, 280) -> End: (195, 280) [left edge of IDLE]
#
# 2. IDLE -> ALLOCATED (job starts, 144px):
#    Horizontal arrow at y = 260 from (445, 260) to (655, 260).
#    Length = 655 - 445 = 210px.
#    Wait! 210px vs 144px: padding = (210 - 144)/2 = 33px >= 16px!
#    What if cx of ALLOCATED is 820? (x: 695..945)
#    Then length = 695 - 445 = 250px! Padding = (250 - 144)/2 = 53px!
#
# 3. ALLOCATED -> IDLE (job ends, 115.2px):
#    Horizontal arrow at y = 300 from (695, 300) to (445, 300).
#    Length = 250px! Padding = (250 - 115.2)/2 = 67.4px!
#
# 4. IDLE -> DRAINED (scontrol drain / health check):
#    Vertical arrow going down from IDLE bottom (270, 320) to DRAINED top (270, 540).
#
# 5. DRAINED -> IDLE (scontrol resume, 223.2px):
#    Vertical arrow going up from DRAINED top (370, 540) to IDLE bottom (370, 320).
#    Length = 220px. Text can sit to the left of the arrow at x = 180!
#
# 6. ALLOCATED -> DRAINING (scontrol drain / health check):
#    Vertical arrow going down from ALLOCATED bottom (820, 320) to DRAINING top (820, 540).
#
# Between the two drain arrows (x=270 and x=820):
# Label: "scontrol drain / health check" (431.5px)
# Centered at x = 545, y = 430.
# Width = 431.5px (from x=329 to 761). Fits comfortably between x=270 and 820!
#
# 7. DRAINING -> DRAINED (running jobs finish, 273.6px):
#    Horizontal arrow at y = 580 from DRAINING left (695, 580) to DRAINED right (445, 580).
#    Length = 250px.
#    Wait! 250px is slightly less than 273.6px!
#    If cx of ALLOCATED and DRAINING is 860:
#    Then distance = 860 - 125 - 445 = 735 - 445 = 290px.
#    If cx = 880: distance = 755 - 445 = 310px!
#    310px > 273.6px! Clearance = (310 - 273.6)/2 = 18.2px >= 16px!
#
# Now let's check DOWN connections (DOWN at cx = 1440, x in [1315..1565]):
# Distance from x=880 (ALLOCATED right = 1005) to DOWN left (1315) is:
# 1315 - 1005 = 310px.
# Wait! ALLOCATED -> DOWN: "node failure (jobs requeued or failed)" is 547.2px!
# 310px is too short for a straight horizontal line!
#
# How does ALLOCATED -> DOWN go?
# What if it goes from ALLOCATED top (880, 240) -> up to y = 140 -> right to x = 1440 -> down to DOWN top (1440, 390)?
# Horizontal segment: y = 140, from x = 880 to x = 1440!
# Length = 1440 - 880 = 560px!
# 560px > 547.2px!
# But what about IDLE -> DOWN and DOWN -> IDLE?
# Where do they go?

print("Checking routing...")
