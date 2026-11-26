# Let's test the width of a diamond at different y offsets from center:
# Diamond vertices: (cx, cy - H/2), (cx + W/2, cy), (cx, cy + H/2), (cx - W/2, cy)
# Equation of top edge: (x - cx) / (W/2) + (cy - y) / (H/2) = 1
# At a given dy = |y - cy|, available width is W * (1 - 2*dy / H).

# If text has 4 lines:
# Line 1: dy = -45
# Line 2: dy = -15
# Line 3: dy = +15
# Line 4: dy = +45
# Line spacing = 30px. Total text height = 90px.
# For line 1 and line 4, dy = 45.
# If available width must be >= text_width + 32:
# W * (1 - 90/H) >= max_w + 32.
# If H = 220, 1 - 90/220 = 0.59.
# If max_w = 245, W >= (245 + 32) / 0.59 = 469 px!
# A diamond of width 469 px is very wide!

# But what if text is 3 lines or wrapped differently?
# Can line 1 be split?
# Line 1: validation
# Line 2: fails: play stops
# Line 3: before the
# Line 4: 10% batch
# Or:
# Line 1: validation fails:
# Line 2: the play stops
# Line 3: before the 10% batch (22 chars * 14.4 = 316px)

print("Let's analyze diamond geometry...")
