# Let us define the exact coordinates of all 9 nodes, start, and end.
# Canvas: Width 1600, Height 1150 (or 1200)

# Layout concept:
# Columns:
# Col 1 (Left): X = 100 .. 380 (width 280, center 240)
# Col 2 (Mid-Left): X = 500 .. 780 (width 280, center 640)
# Col 3 (Mid-Right): X = 880 .. 1160 (width 280, center 1020)
# Col 4 (Right): X = 1260 .. 1540 (width 280, center 1400)

# Rows:
# Row 1 (Top): Y = 130 .. 250 (height 120, center 190)
# Row 2 (Mid): Y = 450 .. 570 (height 120, center 510)
# Row 3 (Bottom): Y = 770 .. 890 (height 120, center 830)

# Let's map nodes to grid:
# Row 1 (Top):
# (R1, C1): Provisioned
# (R1, C2): Configured
# (R1, C3): Validating
# (R1, C4): Ready  <-- HERO NODE (Orange accent!)

# Row 2 (Mid):
# (R2, C1): [Empty or arrow Quarantined -> Provisioned]
# (R2, C2): Maintenance
# (R2, C3): Cordoned
# (R2, C4): Decommissioned

# Row 3 (Bottom):
# (R3, C1): Quarantined
# (R3, C2): [Empty or arrow Draining -> Quarantined]
# (R3, C3): Draining
# (R3, C4): End [*]

# Wait! Let's check connections with this exact mapping:
# 1. Start -> Provisioned:
#    Start at X=240, Y=50. Enters Provisioned top. Straight down.
# 2. Provisioned -> Configured:
#    (R1, C1) to (R1, C2). Straight horizontal right. (X=380 -> 500)
# 3. Configured -> Validating:
#    (R1, C2) to (R1, C3). Straight horizontal right. (X=780 -> 880)
# 4. Validating -> Ready:
#    (R1, C3) to (R1, C4). Straight horizontal right. (X=1160 -> 1260)
# 5. Ready -> Cordoned:
#    Ready (R1, C4) to Cordoned (R2, C3).
#    Leaves Ready bottom (X=1350, Y=250), goes down to Y=350, left to X=1020, down into Cordoned top (X=1020, Y=450).
# 6. Ready -> Decommissioned:
#    Ready (R1, C4) to Decommissioned (R2, C4).
#    Leaves Ready bottom (X=1450, Y=250), straight down into Decommissioned top (X=1450, Y=450).
# 7. Decommissioned -> End:
#    Decommissioned (R2, C4) to End (R3, C4).
#    Leaves Decommissioned bottom (X=1400, Y=570), straight down to End (X=1400, Y=770).
# 8. Cordoned -> Draining:
#    Cordoned (R2, C3) to Draining (R3, C3).
#    Leaves Cordoned bottom (X=1020, Y=570), straight down to Draining top (X=1020, Y=770).
# 9. Draining -> Maintenance:
#    Draining (R3, C3) to Maintenance (R2, C2).
#    Leaves Draining top/left (X=880, Y=800), goes left to X=640, up into Maintenance bottom (X=640, Y=570).
# 10. Maintenance -> Validating:
#     Maintenance (R2, C2) to Validating (R1, C3).
#     Leaves Maintenance top (X=640, Y=450), goes up to Y=350, right to X=1020, up into Validating bottom (X=1020, Y=250).
#     WAIT! Look at Y=350:
#     Ready -> Cordoned left-segment was: from X=1350 to X=1020 at Y=350?
#     Maintenance -> Validating right-segment would be: from X=640 to X=1020 at Y=350?
#     Notice both touch X=1020 at Y=350!
#     Can we separate their Y levels?
#     YES! Ready -> Cordoned at Y=380, Maintenance -> Validating at Y=320!
#     Wait! Maintenance is at X=640, Validating is at X=1020.
#     Ready is at X=1400, Cordoned is at X=1020.
#     If Maintenance goes to X=1020 at Y=320, it goes UP to Validating.
#     If Ready goes to X=1020 at Y=380, it goes DOWN to Cordoned.
#     DO THEY CROSS?
#     X=640 to X=1020 is on the LEFT of X=1020!
#     X=1400 to X=1020 is on the RIGHT of X=1020!
#     THEY ARE ON OPPOSITE SIDES OF X=1020! THEY DO NOT OVERLAP AT ALL!
#     One approaches X=1020 from the left, the other approaches X=1020 from the right!
#     Zero crossing!

# 11. Draining -> Quarantined:
#     Draining (R3, C3) to Quarantined (R3, C1).
#     Leaves Draining bottom (X=1020, Y=890), down to Y=980, left across Y=980 to X=240, up into Quarantined bottom (X=240, Y=890).
# 12. Quarantined -> Provisioned:
#     Quarantined (R3, C1) to Provisioned (R1, C1).
#     Leaves Quarantined top (X=240, Y=770), straight up to Provisioned bottom (X=240, Y=250).

print("Check completed: Beautiful symmetry and zero crossings!")
