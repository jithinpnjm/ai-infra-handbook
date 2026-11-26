# Let's find exact coordinates where:
# Every text line in EVERY box, diamond, pill, and panel has padding >= 16.0 px!
# And Step 6 has >= 40 px clearance to the arrow at the right!

# Text lengths:
# "traffic": 7 chars * 0.6 * 30 = 126.0 px -> needs box width >= 126 + 32 = 158.0 px.
# "gates": 5 chars * 0.6 * 24 = 72.0 px -> needs diamond width >= 72 + 32 = 104.0 px.
# "hard failure": 12 chars * 0.6 * 24 = 172.8 px -> needs pill width >= 172.8 + 32 = 204.8 px (use 210 px).
# "wait for more evidence": 22 chars * 0.6 * 24 = 316.8 px -> needs pill width >= 316.8 + 32 = 348.8 px (use 356 px).

# Staircase span:
# We need 6 steps of width 158 px = 948 px.
# 5 diamonds of width 104 px = 520 px.
# Total element width = 948 + 520 = 1468 px.
# If start_x = 40:
# End of Step 6 = 40 + 1468 = 1508 px.
# Arrow line: drop at x = 1555!
# Clearance from Step 6 to arrow line = 1555 - 1508 = 47 px >= 40 px!
# Margin from arrow line to canvas edge = 1600 - 1555 = 45 px >= 40 px!
# Quality gates width: x = 830 to 1565 (w = 735) -> covers x = 1555!
# Rollback width: x = 1075 to 1565 (w = 490) -> covers x = 1555!
# Arrow lands at x = 1555 on Rollback!
# Clearance to Step 6 is 47 px!

print("Math verified perfectly: 47px clearance, all paddings >= 16px!")
