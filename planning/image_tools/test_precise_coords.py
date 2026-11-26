# Verification of precise coordinates

# Canvas: width=1600, height=1200
# Background: #f5f8f5
# Margins: left=40, right=40 (usable width = 1520)

title = "The N-dimensional Vector, one capability at a time (Takes 1 to 5)"
# Title: font-size: 48px, bold, fill: #207448, y = 52, x = 800 (text-anchor="middle")

# Ladder container / rungs:
# Left ladder rail: x=56, width=8, rx=4, fill="#207448", y=75 to 765
# Right ladder rail: x=1536, width=8, rx=4, fill="#207448", y=75 to 765

# Rungs: x=40, width=1520
# Each rung: rx=10, fill="#e8f1ea", stroke="#207448", stroke-width=2

# Step 1: y=75, h=96
# Step 2: y=183, h=198
# Step 3: y=393, h=198
# Step 4: y=603, h=120
# Step 5: y=735, h=120
# Ladder bottom: 735 + 120 = 855

# Gap between ladder and strip: 20px
# Strip: y=875, h=215
# Strip bottom: 875 + 215 = 1090

# Gap between strip and bottom bar: 20px
# Bottom bar: y=1110, h=55
# Bottom bar bottom: 1110 + 55 = 1165
# Bottom margin: 1200 - 1165 = 35px!

print("Total layout fits in H=1200 with 35px bottom margin!")

