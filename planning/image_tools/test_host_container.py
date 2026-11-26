# Let's test the numbers:
# Canvas: 1600 x 1200
# Title:
# y = 40 (top margin)
# Line 1: y = 70 (48px bold)
# Line 2: y = 114 (48px bold)
# Title area ends at y = 125.
# Gap: 40px -> Outer Box 1 (Host) starts at y = 165.

# Outer Box 1: Host container (x=40, y=165, w=1520)
# Inside Host:
# - Host title & shared nodes bar:
#   y = 175, h = 55 (y=175..230)
# - Gap: 15px
# - Lane 1 panel:
#   y = 245, h = 195 (y=245..440)
# - Gap: 15px
# - Lane 2 panel:
#   y = 455, h = 270 (y=455..725)
# - Gap: 15px
# - Lane 3 panel:
#   y = 740, h = 120 (y=740..860)
# - Bottom padding of Host: 15px -> Host ends at y = 875.
# Total Host height = 875 - 165 = 710px!

# Gap: 40px -> Outer Box 2 (Footer & Docker note) starts at y = 915.
# Outer Box 2:
# y = 915, h = 140 (y=915..1055)

# Gap: 45px -> Outer Box 3 (Takeaway bar) starts at y = 1100.
# Outer Box 3:
# y = 1100, h = 56 (y=1100..1156)

# Bottom margin = 1200 - 1156 = 44px (>= 40px!)

print("Title: 40..125")
print("Gap to Host: 165 - 125 = 40px")
print("Host container: y = 165..875 (h = 710px)")
print("Gap to Footer: 915 - 875 = 40px")
print("Footer box: y = 915..1055 (h = 140px)")
print("Gap to Takeaway: 1100 - 1055 = 45px")
print("Takeaway bar: y = 1100..1156 (h = 56px)")
print("Bottom margin: 1200 - 1156 = 44px")
