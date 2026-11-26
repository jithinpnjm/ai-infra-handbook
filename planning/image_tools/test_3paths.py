# Let's test intersections of Path 1, Path 2, Path 3:

# Path 1: DOWN -> IDLE
# (800, 910) -> (800, 680) -> (160, 680) -> (160, 520) -> (270, 520)
# Segments:
# S1_1: vertical x=800, y in [680, 910]
# S1_2: horizontal y=680, x in [160, 800]
# S1_3: vertical x=160, y in [520, 680]
# S1_4: horizontal y=520, x in [160, 270]

# Path 2: IDLE -> DOWN
# (340, 560) -> (340, 1040) -> (800, 1040) -> (800, 990)
# Segments:
# S2_1: vertical x=340, y in [560, 1040]
# S2_2: horizontal y=1040, x in [340, 800]
# S2_3: vertical x=800, y in [990, 1040]

# Path 3: ALLOCATED -> DOWN
# (1330, 520) -> (1450, 520) -> (1450, 840) -> (850, 840) -> (850, 910)
# Segments:
# S3_1: horizontal y=520, x in [1330, 1450]
# S3_2: vertical x=1450, y in [520, 840]
# S3_3: horizontal y=840, x in [850, 1450]
# S3_4: vertical x=850, y in [840, 910]

# Now let's check:
# Does Path 2 cross Path 1?
# S2_1 (vertical x=340, y in [560, 1040]):
# Does it cross S1_2 (horizontal y=680, x in [160, 800])?
# x=340 IS in [160, 800]! And y=680 IS in [560, 1040]!
# THEY CROSS at (340, 680)!

print("Path 1 and Path 2 cross at (340, 680)!")
