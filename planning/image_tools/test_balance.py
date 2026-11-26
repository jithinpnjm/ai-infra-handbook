# Total canvas: W=1600, H=1200
# Title:
# Y = 40 (margin)
# Title text:
# Line 1: Two state-table limits that look like
# Line 2: random timeouts: SNAT ports and conntrack
# Font size: 48px bold.
# Line 1 y = 55, Line 2 y = 110.
# Title area bottom = 125.
# Panel top = 145.
# Bottom bar:
# Y = 1125 to 1175 (height 50 px).
# Bottom margin = 25 px.
# Panel bottom = 1105.
# Total panel height = 1105 - 145 = 960 px!

# Wait! Earlier we got total panel height 1014 px.
# If panel height is 960 px, can we fit P1 in 960 px?
# Let's check:
# 1014 - 960 = 54 px over 960!
# Wait! What if H = 1200, bottom bar is at 1135 to 1180, panel bottom is 1120.
# What if Title is:
# y = 48 (line 1), y = 98 (line 2). Title ends at 110!
# Panel top = 125!
# Then panel height can be 1120 - 125 = 995 px.
# Can we optimize card padding/heights in P1?
# Let's check!
