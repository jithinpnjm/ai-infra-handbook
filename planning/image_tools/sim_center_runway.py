# If left column is at x=340, and right column is at x=1260:
# Distance between left box right edge (x=480) and right box left edge (x=1120) is:
# 1120 - 480 = 640px.
# What if left box is at x=250 (width=260, from 120 to 380),
# and right box is at x=1350 (width=260, from 1220 to 1480)?
# Then distance between them is 1220 - 380 = 840px!
# 840px is HUGE!
# 677px text has (840 - 677)/2 = 81.5px padding on BOTH sides!
#
# Let's see what happens if:
# Left column has: IDLE, DRAINED
# Right column has: ALLOCATED, DRAINING
# And DOWN: where does DOWN go?
# What if DOWN is in the CENTER, or what if DOWN is at the bottom, or at the top?
# Let's test!
print("Testing center runway...")
