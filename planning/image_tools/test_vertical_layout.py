H = 1000
# Title:
# <text x="800" y="65" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
#   <tspan x="800" dy="0">Exit codes tell you what happened,</tspan>
#   <tspan x="800" dy="56">from 0 for success to 128 plus N for a signal</tspan>
# </text>

# Number line:
# y = 180, height = 70, rx = 12
# Markers inside the number line at y = 224:
# Marker 0: (107.5, 224)
# Marker 1: (330, 224)
# Marker 2: (581, 224)
# Marker 126: (807, 224)
# Marker 127: (1019.5, 224)
# Segment 128 + N: (1241, 224)
# Marker 255: (1470, 224)

# Leader lines:
# From y1 = 250 to y2 = 320 (vertical line of length 70 px)
# x = marker center

# Boxes:
# y = 320, height = 520, rx = 16
# Bottom of boxes = 320 + 520 = 840

# Caption bar:
# y = 890, height = 66, rx = 12
# Bottom of caption = 890 + 66 = 956
# Bottom margin = 1000 - 956 = 44 px >= 40 px!

print("Vertical layout fits cleanly within H = 1000!")
