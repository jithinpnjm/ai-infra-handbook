# Let's test a 3-column vertical layout:
# Col 1: Provisioning & Staging
# Col 2: Active Lifecycle (Validating, Ready, Maintenance)
# Col 3: Drain & Decommission (Cordoned, Draining, Decommissioned)

# Let's trace nodes:
# Col 1:
# Row 1: Provisioned
# Row 2: Configured
# Row 3: Quarantined

# Col 2:
# Row 1: Validating
# Row 2: Ready  (HERO NODE - Orange!)
# Row 3: Maintenance

# Col 3:
# Row 1: Decommissioned -> End [*]
# Row 2: Cordoned
# Row 3: Draining

# Let's trace the 12 transitions in this layout:
# 1. Start -> Provisioned:
#    Start above Provisioned. Vertical down.
# 2. Provisioned -> Configured:
#    From (R1, C1) to (R2, C1). Vertical down.
# 3. Configured -> Validating:
#    From (R2, C1) to (R1, C2).
#    Leaves Configured top/right, goes up to R1, enters Validating left.
# 4. Validating -> Ready:
#    From (R1, C2) to (R2, C2). Vertical down.
# 5. Ready -> Cordoned:
#    From (R2, C2) to (R2, C3). Horizontal right.
# 6. Cordoned -> Draining:
#    From (R2, C3) to (R3, C3). Vertical down.
# 7. Draining -> Maintenance:
#    From (R3, C3) to (R3, C2). Horizontal left.
# 8. Maintenance -> Validating:
#    Wait! Maintenance is (R3, C2). Validating is (R1, C2).
#    In between is Ready (R2, C2)!
#    How does Maintenance reach Validating?
#    If it goes to the left of Ready (between C1 and C2) or right of Ready (between C2 and C3)?
#    Wait, between C2 and C3 is Ready -> Cordoned! Crosses!
#    Between C1 and C2: Configured -> Validating is there!
#    Could it cross Configured -> Validating?
#    Let's check if Maintenance and Validating can be placed differently.

print("Testing alternative in Col 2:")
