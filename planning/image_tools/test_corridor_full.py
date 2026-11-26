import xml.etree.ElementTree as ET

# Let's verify all coordinates, text elements, and boxes.
W = 1600
H = 1200

# Canvas margins: 40px everywhere
# Title: 48px bold
# "Read the vmstat columns to classify the bottleneck"
# y = 52

# Root Box:
# "Run vmstat 2 and start at line 2" (30px bold)
# "Line 1 is the average since boot" (24px)
# Root box: x = 60, y = 80, width = 1480, height = 95
# Icon at (85, 95, 65, 65)

# Takeaway bar at bottom:
# "Read the trend across several lines, not one number."
# x = 60, y = 1115, width = 1480, height = 55

# That leaves y = 175 to 1115 (940 px of height) for the tree!
# Let's inspect the vertical distribution for Column 1 (4 rows):
# Total space: 940 px.
# Available per row: ~235 px.
# For each row in Column 1:
# Row 1 (Branch 1):
#   Condition label & arrow: y = 175 .. 265 (90 px)
#   Box 1 ("Healthy"): y = 265 .. 370 (105 px)
# Row 2 (Branch 2):
#   Condition label & arrow: y = 390 .. 480 (90 px)
#   Box 2 ("CPU-bound compute"): y = 480 .. 585 (105 px)
# Row 3 (Branch 3):
#   Condition label & arrow: y = 605 .. 695 (90 px)
#   Box 3 ("I/O-bound work: look at iostat"): y = 695 .. 825 (130 px)
# Row 4 (Branch 4):
#   Condition label & arrow: y = 845 .. 935 (90 px)
#   Box 4 ("Memory exhausted: kernel is paging out"): y = 935 .. 1075 (140 px)

# Total height used by Column 1: up to 1075.
# Margin to takeaway bar (1115): 1115 - 1075 = 40 px!
# Exactly >= 40 px margin!

print("Column 1 vertical fit is PERFECT!")

# Now for Column 2 (3 rows):
# Total space: 940 px.
# Row 1 (Branch 5):
#   Condition label & arrow: y = 175 .. 285 (110 px)
#   Box 5 ("CPU contention"): y = 285 .. 410 (125 px)
# Row 2 (Branch 6):
#   Condition label & arrow: y = 460 .. 570 (110 px)
#   Box 6 ("Many system calls or lock contention"): y = 570 .. 720 (150 px)
# Row 3 (Branch 7):
#   Condition label & arrow: y = 770 .. 880 (110 px)
#   Box 7 ("Noisy neighbours on a shared VM"): y = 880 .. 1030 (150 px)

print("Column 2 vertical fit is PERFECT!")
