# Test 4 nodes on Row 1:
# Canvas width = 1600.
# Left margin = 50, Right margin = 50. Total usable = 1500.

# 4 nodes:
# Col 0: Provisioned
# Col 1: Configured
# Col 2: Validating
# Col 3: Ready

# What if:
# Start [*] is ABOVE Provisioned!
# (X = Provisioned.cx, Y = 120)
# Arrow goes straight DOWN from [*] to Provisioned!
# Badge: "bare metal/VM created (image, BMC/PXE or cloud API)"
# Sits right beside or on the vertical arrow from [*] to Provisioned!

# And Decommissioned & End [*] are BELOW or to the RIGHT of Ready!
# Ready is at Col 3.
# Ready -> Decommissioned: goes DOWN or RIGHT-DOWN to Decommissioned!
# Decommissioned -> End [*]: goes straight to End [*]!

print("Let's analyze this!")
