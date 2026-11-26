# Let's test widths:
# Total width available: x = 50 to 1420 (w = 1370 px).
# Why 1420? Because the arrow from Quality gates down to Rollback drops at x = 1485.
# With label "hard failure" at x = 1470 (anchor="end"), label left edge is at 1470 - 173 = 1297 px.
# Wait! Does the label "hard failure" have to be between y = 310 and 800?
# What if the label "hard failure" is at y = 550?
# And what if Step 6 is at y = 310..420?
# At y = 550, Step 6 has ALREADY ENDED (Step 6 is at y = 310..420)!
# So at y = 550, the staircase is NOT THERE!
# Step 6 is at y = 310..420!
# At y = 310..420, the arrow is just a vertical line at x = 1485!
# So Step 6 can extend up to x = 1440, leaving 45 px clearance to the line at x = 1485!
# And at y = 550, where "hard failure" label sits, the staircase is at Step 3 or 4 (x <= 950)!
# The space from x = 950 to 1485 is COMPLETELY EMPTY at y = 550!
# So "hard failure" has over 300 px of empty space!
print("Arrow and label have massive clearance!")
