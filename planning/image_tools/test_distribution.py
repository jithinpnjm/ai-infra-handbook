# Calculate distribution of vertical space

# candidate_cfg_order.svg had:
# Ladders: y = 145..650 (h = 505)
# Commands: y = 690..786 (h = 96) -> gap = 40
# Surprise: y = 826..902 (h = 76) -> gap = 40
# Rules: y = 942..1038 (h = 96) -> gap = 40
# Bottom bar: y = 1078..1130 (h = 52) -> gap = 40
# Bottom margin = 1200 - 1130 = 70px!

# What if:
# Bottom bar ends at y = 1158 (outside margin = 42 >= 40)
# Bottom bar: h = 60 (y: 1098..1158)
# Gap = 40 -> y = 1058
# Rules strip: h = 118 (y: 940..1058)
# Gap = 40 -> y = 900
# Surprise story: h = 90 (y: 810..900)
# Gap = 40 -> y = 770
# Commands strip: h = 118 (y: 652..770)
# Gap = 40 -> y = 612
# Ladders bottom = 612!

# Now top:
# Title:
# Line 1 baseline y = 84 (top = 40 >= 40)
# Line 2 baseline y = 132 (bottom = 146)
# Gap = 40 -> Ladders top = 186!

# Available height for Ladders:
ladders_h = 612 - 186
print(f"Ladders height: {ladders_h}px (from y=186 to y=612)")
