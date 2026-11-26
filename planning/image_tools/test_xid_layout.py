import re
import xml.etree.ElementTree as ET

# Let's design the layout coordinates:
# Total width 1600, total height 1100 (fits in 900..1200)

# Title: y=55, font-size 48

# Row 1: Start box:
# Label: "Xid reported on a node" (22 chars)
# Width: 480, Height: 80.
# Centered around x=950? Or x=960?
# Let's see: Step 1 and Step 2 should align with Start box.
# If Start box is at x=720, w=480: left=720, right=1200, center=960.
# Step 1: x=720, y=210, w=480, h=80.
# Circle 1: cx=660, cy=250, r=24.
# Gap circle to box: 720 - (660+24) = 36px? Let's make cx=650 -> gap = 720 - 674 = 46px >= 40px!
# Step 2: x=720, y=340, w=480, h=80.
# Circle 2: cx=650, cy=380, r=24.

# Let's check:
# Start box: y=80, h=80 -> bottom=160.
# Gap to Step 1: 210 - 160 = 50px (>= 40px!).
# Arrow 1: line from (960, 160) to (960, 208) [length 48px].
# Step 1: y=210, h=80 -> bottom=290.
# Gap to Step 2: 340 - 290 = 50px (>= 40px!).
# Arrow 3 (Step 1 to Step 2): line from (960, 290) to (960, 338) [length 48px].

# Step 1 exits:
# [Yes] goes down to Step 2 (Arrow 3).
# [No] goes left to Suspect box!
# Suspect box: in Column 1 (left side).
# Where is Column 1?
# Left margin = 40.
# Suspect box: x=40, width=320 -> right=360.
# Suspect box y: y=530, h=220 -> bottom=750.
# Arrow 2 (Step 1 [No] to Suspect):
# Exits Step 1 at left edge (x=720, y=250).
# Path: M 720 250 L 200 250 L 200 528 (with marker-end).
# Top of Suspect is y=530, arrow ends at y=528!
# Does Arrow 2 cross anything?
# y=250 between x=200 and x=720: completely empty! Circle 1 is at cx=650, cy=250, r=24 (from 626 to 674).
# WAIT! If Arrow 2 is at y=250, it would PASS THROUGH Circle 1 if Circle 1 is at cy=250!
# AHA! Circle 1 is at cx=650, cy=250! Arrow from x=720 to x=200 would cross Circle 1!
# That is a crucial catch!
# How to avoid crossing Circle 1?
# Option A: Arrow 2 exits the TOP or BOTTOM of Step 1, OR turns around Circle 1!
# E.g., Arrow 2 exits Step 1 at x=720, y=230 or y=270, or exits at x=760 y=210?
# OR: Circle 1 is placed on the RIGHT of Step 1! Or ABOVE Step 1!
# If Circle 1 is placed at cx=650, cy=180? Or cx=720, cy=180?
# Wait! In test_xid_candidate.svg:
# Look at test_xid_candidate.svg:
# Circle 1 is at cx=660, cy=260.
# Arrow 2 is: M 715 260 L 200 260 L 200 518!
# In test_xid_candidate.svg, Arrow 2 starts at 715, 260, goes left to 200, 260!
# It literally crossed through Circle 1 (cx=660, cy=260)!
# That was an arrow crossing in test_xid_candidate.svg!
print("Detected collision in old candidate!")
