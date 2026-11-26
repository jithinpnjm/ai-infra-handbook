# Let's test a layout with label boxes:
# Canvas: 1600 x 1100
#
# Nodes:
# IDLE:      cx = 400,  cy = 450, w = 260, h = 80 -> [270..530, 410..490]
# ALLOCATED: cx = 1200, cy = 450, w = 260, h = 80 -> [1070..1330, 410..490]
# DRAINED:   cx = 400,  cy = 200, w = 260, h = 80 -> [270..530, 160..240]
# DRAINING:  cx = 1200, cy = 200, w = 260, h = 80 -> [1070..1330, 160..240]
# DOWN:      cx = 800,  cy = 950, w = 260, h = 80 -> [670..930, 910..990]

# Let's check the transitions and their label boxes:
# 1. [*] -> IDLE
# 2. IDLE -> ALLOCATED: "job starts" (144px) -> box_w = 180px
# 3. ALLOCATED -> IDLE: "job ends" (115px) -> box_w = 150px
# 4. DRAINING -> DRAINED: "running jobs finish" (274px) -> box_w = 320px
# 5. scontrol drain / health check: (432px) -> box_w = 480px
# 6. scontrol resume: (223px) -> box_w = 260px
# 7. ALLOCATED -> DOWN: "node failure (jobs requeued or failed)" (547px) -> box_w = 600px
# 8. IDLE -> DOWN: "slurmd not responding (SlurmdTimeout) / admin" (648px) -> box_w = 700px
# 9. DOWN -> IDLE: "resume or ReturnToService on valid registration" (677px) -> box_w = 720px

# Look at the bottom half of the canvas (y from 500 to 1100):
# Height = 600px! Width = 1600px!
# In this bottom half:
# There is only ONE node: DOWN (at cx=800, cy=950)!
# And we have three transitions:
# - ALLOCATED -> DOWN (label box 600px)
# - IDLE -> DOWN (label box 700px)
# - DOWN -> IDLE (label box 720px)
#
# Can we arrange these three transitions cleanly in this 1600 x 600 space?
# YES!
# For example:
# Right side: ALLOCATED -> DOWN
# Center/Left: IDLE -> DOWN and DOWN -> IDLE
#
print("Testing layout feasibility...")
