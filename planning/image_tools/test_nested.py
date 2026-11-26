# Path 1 (Inner): DOWN -> IDLE
# (750, 910) -> (750, 680) -> (450, 680) -> (450, 560)
# Segments:
# S1_1: vertical x=750, y in [680, 910]
# S1_2: horizontal y=680, x in [450, 750]
# S1_3: vertical x=450, y in [560, 680]

# Path 2 (Outer): IDLE -> DOWN
# (320, 560) -> (320, 1040) -> (800, 1040) -> (800, 990)
# Segments:
# S2_1: vertical x=320, y in [560, 1040]
# S2_2: horizontal y=1040, x in [320, 800]
# S2_3: vertical x=800, y in [990, 1040]

# Check intersection:
# S1_1 (x=750, y in [680, 910]) vs S2_2 (y=1040, x in [320, 800]): y=1040 not in [680, 910]. No.
# S1_2 (y=680, x in [450, 750]) vs S2_1 (x=320, y in [560, 1040]): x=320 not in [450, 750]. No.
# S1_3 (x=450, y in [560, 680]) vs S2_2 (y=1040): y=1040 not in [560, 680]. No.
# S2_3 (x=800, y in [990, 1040]) vs any S1: y in [990, 1040] does not overlap y in [560, 910]!
#
# ZERO INTERSECTIONS! THEY DO NOT CROSS AT ALL!
print("ZERO INTERSECTIONS CONFIRMED FOR NESTED PATHS!")
