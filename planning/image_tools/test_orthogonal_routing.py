# Let's test orthogonal routing for Layout 1:
# Nodes and centers:
# Col 0: X = 240
# Col 1: X = 800
# Col 2: X = 1360
# Row 0: Y = 200
# Row 1: Y = 560
# Row 2: Y = 920

# Let's check orthogonal paths:
# 1. Start -> Provisioned: (240, 60) -> (240, 140) [Vertical down]
# 2. Provisioned -> Configured: (380, 200) -> (660, 200) [Horizontal right]
# 3. Configured -> Validating: (940, 200) -> (1220, 200) [Horizontal right]
# 4. Validating -> Ready: (1360, 260) -> (1360, 500) [Vertical down]
# 5. Ready -> Decommissioned: (1360, 620) -> (1360, 860) [Vertical down]
# 6. Decommissioned -> End: (1360, 980) -> (1360, 1080) [Vertical down]
# 7. Ready -> Cordoned:
#    Ready is at (1360, 560). Cordoned is at (800, 920).
#    Path: leaves Ready left at (1220, 590), goes left to X = 1080, down to Y = 890, left to Cordoned right at (940, 890).
#    OR leaves Ready bottom-left, down to Y = 740, left to X = 800, down into Cordoned top (800, 860).
# 8. Cordoned -> Draining:
#    Cordoned is at (800, 920). Draining is at (240, 920).
#    Horizontal left from (660, 920) to (380, 920)!
# 9. Draining -> Quarantined:
#    Draining (240, 920) to Quarantined (240, 560).
#    Vertical up from (240, 860) to (240, 620)!
# 10. Quarantined -> Provisioned:
#    Quarantined (240, 560) to Provisioned (240, 200).
#    Vertical up from (240, 500) to (240, 260)!
# 11. Draining -> Maintenance:
#    Draining is at (240, 920). Maintenance is at (800, 560).
#    Path: leaves Draining top at (280, 860), goes up to Y = 740, right to X = 740, up into Maintenance bottom at (740, 620).
# 12. Maintenance -> Validating:
#    Maintenance is at (800, 560). Validating is at (1360, 200).
#    Path: leaves Maintenance top at (800, 500), goes up to Y = 380, right to X = 1300, up into Validating bottom at (1300, 260).

print("Let's check if Ready -> Cordoned and Maintenance -> Validating cross:")
# Ready -> Cordoned: from Ready (1360, 560) to Cordoned (800, 920).
# Maintenance -> Validating: from Maintenance (800, 560) to Validating (1360, 200).
# Notice:
# Ready is at (1360, 560). Validating is at (1360, 200).
# Maintenance is at (800, 560). Cordoned is at (800, 920).
# Maintenance -> Validating goes UP and RIGHT!
# Ready -> Cordoned goes DOWN and LEFT!
# They both connect Col 1 (X=800) and Col 2 (X=1360)!
# Maintenance is at Y=560, goes UP to Y=200.
# Ready is at Y=560, goes DOWN to Y=920.
# Maintenance -> Validating is entirely in the UPPER half (Y <= 560)!
# Ready -> Cordoned is entirely in the LOWER half (Y >= 560)!
# THEY ARE IN COMPLETELY DIFFERENT VERTICAL HALVES!
# THEY CANNOT CROSS!
print("Maintenance -> Validating is strictly in UPPER half (Y <= 560).")
print("Ready -> Cordoned is strictly in LOWER half (Y >= 560).")
print("THEY DO NOT CROSS AT ALL! ZERO CROSSINGS!")
