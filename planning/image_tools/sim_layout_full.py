import math

# Let's test exact coordinates for the layout:
# Canvas: 1600 x 1050
#
# Nodes: (box_w = 280, box_h = 90)
# DOWN:      cx = 800,  cy = 210 -> x1 = 660,  y1 = 165, x2 = 940,  y2 = 255
# IDLE:      cx = 440,  cy = 550 -> x1 = 300,  y1 = 505, x2 = 580,  y2 = 595
# ALLOCATED: cx = 1160, cy = 550 -> x1 = 1020, y1 = 505, x2 = 1300, y2 = 595
# DRAINED:   cx = 440,  cy = 880 -> x1 = 300,  y1 = 835, x2 = 580,  y2 = 925
# DRAINING:  cx = 1160, cy = 880 -> x1 = 1020, y1 = 835, x2 = 1300, y2 = 925

# Let's check text labels and their bounding boxes:
# Label 1: Title "Node lifecycle" (48px bold, sans)
# cx = 800, cy = 70. Bounding box: y in [30, 90]

# Label 2: [*] circle at cx = 140, cy = 550, r = 16.
# Arrow [*] -> IDLE: from (156, 550) to (300, 550). Length = 144px.

# Label 3: IDLE -> ALLOCATED "job starts" (24px sans, len=10, width=144px)
# Arrow from (580, 525) to (1020, 525). Length = 440px.
# Label at cx = 800, cy = 512 (above arrow at y=525).

# Label 4: ALLOCATED -> IDLE "job ends" (24px sans, len=8, width=115.2px)
# Arrow from (1020, 575) to (580, 575). Length = 440px.
# Label at cx = 800, cy = 595 (below arrow at y=575).

# Label 5: DRAINING -> DRAINED "running jobs finish" (24px sans, len=19, width=273.6px)
# Arrow from (1020, 880) to (580, 880). Length = 440px.
# Label at cx = 800, cy = 865 (above arrow at y=880).

# Label 6: Between IDLE and DRAINED, ALLOCATED and DRAINING:
# IDLE -> DRAINED (down) and ALLOCATED -> DRAINING (down)
# Label: "scontrol drain / health check" (24px mono, len=29, width=431.5px)
# Look: IDLE right edge = 580, ALLOCATED left edge = 1020. Distance = 440px!
# In the vertical gap between y=595 (bottom of IDLE/ALLOCATED) and y=835 (top of DRAINED/DRAINING):
# Height gap = 240px!
# Center is y = 715.
# If "scontrol drain / health check" is centered at cx = 800, cy = 715:
# Width is 431.5px (from x=584 to 1016).
# It sits perfectly between the two columns!

# Label 7: DRAINED -> IDLE "scontrol resume" (24px mono, len=15, width=223.2px)
# Arrow DRAINED -> IDLE: goes from DRAINED top (y=835) up to IDLE bottom (y=595).
# Where are the two vertical arrows between IDLE and DRAINED?
# IDLE -> DRAINED is at x = 390 (going down from y=595 to y=835)
# DRAINED -> IDLE is at x = 490 (going up from y=835 to y=595)
# "scontrol resume" can be placed vertically or beside x=490?
# Wait! "scontrol resume" is 223px wide.
# If placed horizontally at x=490, it would be 223px wide, but distance between columns is available on the right of x=490!
# From x=490 to x=580 is 90px. To the right of x=580 (between columns) is open space!

print("Testing geometry...")
