# Let's optimize card heights and gaps for P1 and P2
# Panel top = 125, Panel height = 955, Panel bottom = 1080.
# Header: 125 to 179 (height 54).
# Content starts at y = 195. Content area ends at y = 1065 (height 870).

# In P1:
# Let's give:
# Flow (2 lines): h = 86
# Gap 1 (connecting line): gap = 16
# Arithmetic (5 lines): h = 172
# Gap 2 (arrow down): gap = 24
# Failure (4 lines): h = 144
# Gap 3: gap = 20
# Metaphor (3 lines): h = 116
# Gap 4: gap = 20
# Fix (4 lines): h = 144
# Gap 5: gap = 20
# Lesson (2 lines): h = 86

p1_h = [86, 172, 144, 116, 144, 86]
p1_gaps = [16, 24, 20, 20, 20]
print("P1 total:", sum(p1_h) + sum(p1_gaps)) # 848 px! Starts at y=200, ends at y=1048. Perfect!

# In P2:
# 5 cards:
# Symptom (3 lines): h = 125
# Evidence (4 lines): h = 155
# Causes (3 lines): h = 125
# Note (2 lines): h = 95
# Fix (3 lines): h = 125
# Sum of heights = 625 px.
# We have 848 - 625 = 223 px for 4 gaps.
# 223 / 4 = ~55 px gap between cards in P2!

p2_h = [125, 155, 125, 95, 125]
p2_gaps = [55, 56, 56, 56]
print("P2 total:", sum(p2_h) + sum(p2_gaps)) # 847 px! Starts at y=200, ends at y=1047. Perfectly balanced!
