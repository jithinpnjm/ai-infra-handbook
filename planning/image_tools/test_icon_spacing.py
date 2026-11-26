# Check vertical positions in Row 1:
# If Row 1 height = 175 px (y: 235 to 410)
# Icon at top: y = 248 to 280 (32 px high)
# Gap = 16 px
# Text start: y = 310
# Line 1: y = 310
# Line 2: y = 336
# Line 3: y = 362
# Line 4: y = 388
# 388 + 8 = 396 <= 410. Padding bottom = 14-16 px.
# But wait! If Row 1 is 175 px, can we give Row 1, 2, 3, 4, 5 good heights?
# Let's check total height budget with bottom bar at 1090.
# Available for grid = 1060 - 235 = 825 px.
# Row 1: 165 px
# Row 2: 155 px
# Row 3: 175 px
# Row 4: 155 px
# Row 5: 145 px
# Gaps: 4 * 12 = 48 px.
# Total = 165 + 155 + 175 + 155 + 145 + 48 = 843 px.
# 235 + 843 = 1078 <= 1080! Fits within canvas height 1200!
print("Height allocation fits!")
