# Let's test Lane 1 vertical clearances:
box_y = 264
box_h = 192 # y=264..456
circle_cx = 76
circle_cy = 292
circle_r = 24
circle_top = circle_cy - circle_r # 268 (pad top = 268 - 264 = 4px? wait!)
# If circle top pad is 16px: cy must be 264 + 16 + 24 = 304.
# Then circle bottom is 328.
# If text below circle starts at baseline 350:
# Text top cap = 350 - 18 = 332 > 328 (4px clear below circle!).
# But how many lines can fit between 350 and box_bot?
# Let's check:
# Line 1: base = 350
# Line 2: base = 373
# Line 3: base = 396
# Line 4: base = 419
# Line 5: base = 442
# Desc = 442 + 4.8 = 446.8.
# Box bot with 16px pad = 446.8 + 16 = 462.8!
# That would require box_h = 463 - 264 = 199px!

# BUT WHAT IF all lines in Lane 1 start at x=116 or x=60?
# Wait! Why not indent line 1, or start all body text below the circle?
# Wait! What if circle is r=24, but wait! Does the rule say:
# "Number circles (r=24, green, white number) only where the source has a time order."
# YES! "Number circles (r=24, green, white number)"
print("Checking dimensions...")
