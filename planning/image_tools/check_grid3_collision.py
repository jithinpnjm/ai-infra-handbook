# Check all edge paths in Clean Grid 3
# Nodes:
# Col 0: Configured(0,0), Provisioned(1,0), Quarantined(2,0)
# Col 1: Validating(0,1), Maintenance(1,1), Draining(2,1)
# Col 2: Decommissioned(0,2), Ready(1,2), Cordoned(2,2)

# Edges:
# 1. Start -> Provisioned: enters (1,0) from left.
# 2. Provisioned(1,0) -> Configured(0,0): straight UP in Col 0 (from y=mid to y=top).
# 3. Configured(0,0) -> Validating(0,1): straight RIGHT on Row 0 (from Col 0 to Col 1).
# 4. Validating(0,1) -> Ready(1,2):
#    From right of Validating(0,1), goes right to between Col 1 and Col 2, then down to Ready(1,2)?
#    Wait! Between (0,1) and (1,2) is (0,2) Decommissioned!
#    If it goes from right of Validating(0,1) at y=top across to Col 2, it would hit Decommissioned!
#    UNLESS it goes down out of Validating(0,1) into the horizontal channel between Row 0 and Row 1,
#    then goes right to Col 2, and into the top of Ready(1,2)!
#    WAIT! What is going into Decommissioned(0,2)?
#    Ready(1,2) -> Decommissioned(0,2)! That goes UP from Ready(1,2) to Decommissioned(0,2)!
#    If Ready -> Decommissioned goes UP from Ready, and Validating -> Ready comes DOWN into Ready:
#    THEY WOULD COLLIDE at the top of Ready(1,2)!

print("Validating->Ready and Ready->Decommissioned meet at top of Ready!")
