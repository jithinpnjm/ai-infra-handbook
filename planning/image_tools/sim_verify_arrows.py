# Let's test the 5-node planar layout:
#
# Nodes:
# IDLE:      (x=460,  y=500)  [w=280, h=90] -> bounds: x in [320, 600], y in [455, 545]
# ALLOCATED: (x=1140, y=500)  [w=280, h=90] -> bounds: x in [1000, 1280], y in [455, 545]
# DRAINED:   (x=460,  y=220)  [w=280, h=90] -> bounds: x in [320, 600], y in [175, 265]
# DRAINING:  (x=1140, y=220)  [w=280, h=90] -> bounds: x in [1000, 1280], y in [175, 265]
# DOWN:      (x=800,  y=820)  [w=280, h=90] -> bounds: x in [660, 940], y in [775, 865]

# Let's check the arrows:
# 1. [*] -> IDLE:
#    Start: (140, 500) -> End: (320, 500) [left edge of IDLE]
#
# 2. IDLE -> ALLOCATED (job starts):
#    Start: (600, 480) -> End: (1000, 480) [horizontal, y=480]
#    Length = 400px. Text = "job starts" (144px). Plenty of room!
#
# 3. ALLOCATED -> IDLE (job ends):
#    Start: (1000, 520) -> End: (600, 520) [horizontal, y=520]
#    Length = 400px. Text = "job ends" (115px). Plenty of room!
#
# 4. IDLE -> DRAINED (scontrol drain / health check):
#    Start: (410, 455) -> End: (410, 265) [vertical, x=410, going UP]
#    Length = 190px.
#
# 5. DRAINED -> IDLE (scontrol resume):
#    Start: (510, 265) -> End: (510, 455) [vertical, x=510, going DOWN]
#    Length = 190px. Parallel to #4! Distance between them = 100px.
#    Text = "scontrol resume" (223px). Can be placed right next to arrow #5!
#
# 6. ALLOCATED -> DRAINING (scontrol drain / health check):
#    Start: (1140, 455) -> End: (1140, 265) [vertical, x=1140, going UP]
#    Length = 190px.
#
# 7. DRAINING -> DRAINED (running jobs finish):
#    Start: (1000, 220) -> End: (600, 220) [horizontal, y=220, going LEFT]
#    Length = 400px. Text = "running jobs finish" (274px). Plenty of room!
#
# 8. IDLE -> DOWN (slurmd not responding (SlurmdTimeout) / admin):
#    Leaves IDLE at (380, 545), goes down to y=800, right to DOWN (660, 800)
#    Or exits left edge of IDLE (320, 520) -> goes left to x=220 -> down to y=800 -> right to DOWN (660, 800).
#    Horizontal stretch along the bottom: x=220 to 660 = 440px.
#    Wait! If it exits (320, 520) -> left to x=180 -> down to y=800 -> right to DOWN (660, 800):
#    Distance = 660 - 180 = 480px.
#    What if it goes from IDLE bottom (x=400, 545) -> down-right to DOWN (660, 800)?
#    Let's check the length of "slurmd not responding (SlurmdTimeout) / admin" (648px).
#    Where does this 648px label go?
#
# Let's inspect all label positions!
print("Arrow check running...")
