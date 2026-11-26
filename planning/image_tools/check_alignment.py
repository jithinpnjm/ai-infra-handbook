# Lane 2: 4 cards
# Available Y space: y=220 to y=990 (total height = 770px)
# We have 4 cards and 3 gaps.
# Let heights be:
# C1 (Trigger, 5 lines): 180px
# C2 (Actor, 2 lines): 110px
# C3 (Ranking, 3 lines): 125px
# C4 (Result, 3 lines): 125px
# Sum of card heights = 180 + 110 + 125 + 125 = 540px.
# Remaining space for 3 gaps = 770 - 540 = 230px.
# 230 / 3 = 76.6px per gap!
# Let's say gap = 60px:
# 3 * 60 = 180px.
# Then we have 540 + 180 = 720px.
# Start at y = 235:
# C1: y = 235, h = 180 -> ends at 415
# Arrow 1: y = 415 to 465 (len 50)
# C2: y = 465, h = 110 -> ends at 575
# Arrow 2: y = 575 to 625 (len 50)
# C3: y = 625, h = 130 -> ends at 755
# Arrow 3: y = 755 to 805 (len 50)
# C4: y = 805, h = 145 -> ends at 950!
# Bottom margin inside lane: 1015 - 950 = 65px! Perfectly balanced!

# Now Lane 1: 3 cards
# C1 (Trigger, 3 lines):
# Can match C1: y = 235, h = 180 -> ends at 415!
# Arrow 1: y = 415 to 465 (len 50)
# C2 (Actor, 2 lines):
# Can match C2: y = 465, h = 110 -> ends at 575!
# Arrow 2: y = 575 to 645 (len 70, orange!)
# C3 (Result, 5 lines, orange border):
# y = 645, h = 305 -> ends at 950!
# Bottom ends at EXACTLY 950, aligning with Lane 2 C4 bottom!
# And C3 has h = 305px, which is plenty of room for 5 lines of text and a prominent icon!

print("Lane 1 and Lane 2 vertical alignment matches at y=950!")
