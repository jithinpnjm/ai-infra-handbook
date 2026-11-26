# Let's test header card dimensions:
# bx, by, bw = 220, bh = 94
# Icon: center at cx, size 34x26, at by + 6..32
# Text:
# 1 line: baseline at by + 70 (font-size 30) -> top at 70 - 24 = 46. Gap to icon = 46 - 32 = 14px. Bottom pad = 94 - 70 = 24px.
# 2 lines:
# Line 1: baseline at by + 58 -> top at 58 - 24 = 34. Gap to icon = 2px.
# Line 2: baseline at by + 84 -> bottom pad = 94 - 84 = 10px.

# Total height = 94 px.
# Row 1: y = 46 to 140 (h = 94)
# Row 2: y = 146 to 240 (h = 94)
# Step 1 starts at y = 252!

# If Step 1 starts at y = 252:
# Span of steps = 1099 - 216 = 883 px.
# End of steps = 252 + 883 = 1135 px!
# Bottom margin = 1200 - 1135 = 65 px (>= 40px)!
print(f"End of steps: {252 + 883}px, Bottom margin: {1200 - (252 + 883)}px")
