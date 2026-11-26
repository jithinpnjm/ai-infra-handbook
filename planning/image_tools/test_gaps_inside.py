# If gap between all boxes (including lanes) is 40px:
# Let's see:
# y = 40..115 (Title)
# Title to Box 1 gap: 40px -> y = 155
# If Box 1 is Host bar or Lane 1:
# What if the 4 shared nodes are in a header bar:
# Header bar: y = 155..215 (h=60)
# Gap: 40px -> Lane 1 starts at y = 255
# Lane 1: h = 175 -> y = 255..430
# Gap: 40px -> Lane 2 starts at y = 470
# Lane 2: h = 250 -> y = 470..720
# Gap: 40px -> Lane 3 starts at y = 760
# Lane 3: h = 115 -> y = 760..875
# Gap: 40px -> Footer box starts at y = 915
# Footer box: h = 145 -> y = 915..1060
# Gap: 40px -> Takeaway bar starts at y = 1100
# Takeaway bar: h = 50 -> y = 1100..1150
# Bottom margin: 1200 - 1150 = 50px (> 40px!)

print("EVERY gap is >= 40px! Total fits in 1200!")
print("Lane 1:", 430 - 255)
print("Lane 2:", 720 - 470)
print("Lane 3:", 875 - 760)
print("Footer:", 1060 - 915)
