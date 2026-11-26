import xml.etree.ElementTree as ET

# Let's test two different arrow routing strategies:
# Strategy 1: Central corridor
# Root is at top: x=300..1300, y=100..200.
# Left column boxes: x = 60..580 (width 520)
# Right column boxes: x = 1020..1540 (width 520)
# Center corridor: x = 580..1020 (width 440 px)
#
# But wait! Where do the arrows start?
# Bottom of Root box (y=200).
# For Left Column:
# Box 1: y = 260..380
# Box 2: y = 440..560
# Box 3: y = 620..740
# Box 4: y = 800..920
#
# If Arrow 1 starts at (660, 200), goes down to y=320, turns left to Box 1 at (580, 320).
# Arrow 2 starts at (710, 200), goes down to y=500, turns left to Box 2 at (580, 500).
# Arrow 3 starts at (760, 200), goes down to y=680, turns left to Box 3 at (580, 680).
# Arrow 4 starts at (810, 200), goes down to y=860, turns left to Box 4 at (580, 860).
#
# Wait! Does Arrow 2 cross Arrow 1?
# Arrow 1: (660, 200) -> (660, 320) -> (580, 320).
# Arrow 2: (710, 200) -> (710, 500) -> (580, 500).
# At y=320, Arrow 1 is turning left towards x=580.
# Arrow 2 is at x=710 (to the right of 660!). It passes y=320 at x=710.
# Arrow 1 ended at x=580 (which is to the left of 660).
# When Arrow 2 turns left at y=500, it goes from x=710 to x=580.
# But Arrow 1 is up at y=320!
# They DO NOT intersect!
print("Strategy 1 is completely non-intersecting!")

