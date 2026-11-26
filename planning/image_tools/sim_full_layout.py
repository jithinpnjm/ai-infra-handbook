import re

# Canvas: width 1600, height H (e.g. 1000)
# Margins: 40 px left and right -> x from 40 to 1560 (width = 1520)

# Title:
# "Exit codes tell you what happened,"
# "from 0 for success to 128 plus N for a signal"
# y = 60, 115

# Number line:
# y = 200 to 280
# The number line runs horizontally from x=60 to x=1540 (width 1480 px).

# Let's see: How are segments distributed along the number line?
# On the number line:
# Markers:
# 0, 1, 2, 126, 127, 128+N (130 Ctrl-C, 137 SIGKILL, 143 SIGTERM), 255.

# Let's inspect the spatial distribution:
# If the line represents 0 to 255:
# To make it readable, the segments can be visually apportioned:
# Segment 0: x = 60 to 180 (Marker '0')
# Segment 1-2: x = 180 to 480 (Markers '1', '2')
# Gap / transition 3..125: x = 480 to 560
# Segment 126-127: x = 560 to 860 (Markers '126', '127')
# Gap / transition: x = 860 to 920
# Segment 128+N: x = 920 to 1340 (wide segment with orange outline, containing '128 + N' and '130 Ctrl-C', '137 SIGKILL', '143 SIGTERM')
# Gap / transition: x = 1340 to 1400
# Segment 255: x = 1400 to 1540 (Marker '255')

print("Testing layout idea...")
