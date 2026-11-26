# Let's test the entire canvas width of 1600 px.
# Left margin: 40 px.
# Right margin: 40 px.
# Total usable width: 1520 px (from x = 40 to x = 1560).

# If the staircase uses the full middle width:
# Can we place 6 steps and 5 diamonds?
# Let's see:
# If Step 6 is at the top right of the staircase, say x = 1200..1360.
# Where can the arrow to Rollback go?
# Gate row: y = 140..250.
# Rollback box: at bottom row: x = 1080..1540, y = 840..1010.
# If Quality gates is x = 820..1540:
# The arrow can start from the bottom-right corner of Quality gates at x = 1500, y = 250.
# And drop straight down to Rollback at x = 1500, y = 840!
# At x = 1500, y = 250..840:
# What is to the right of x = 1500? Margin to 1600 (100 px).
# What is to the left of x = 1500?
# Step 6 can end at x = 1420!
# Between Step 6 (x=1420) and arrow (x=1500) there is 80 px gap!
# The label "hard failure" can be placed:
# At x = 1500, y = 540, with a small background box, or at x = 1430..1490!
# If label is:
# "hard"
# "failure"
# (7 chars * 0.6 * 24 = 100 px).
# Or on one line: "hard failure" (12 chars * 0.6 * 24 = 172.8 px).
# Placed on the arrow with a clean pill background!
print("Arrow at x=1500 fits with 80px clearance from Step 6!")
