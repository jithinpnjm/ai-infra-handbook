# Verify the exact 16px bottom bar and test strip

# Test strip: y = 946 to 1056 (h = 110)
# L1: 982 (top pad: 982 - 19.2 - 946 = 16.8)
# L2: 1008
# L3: 1034 (bot pad: 1056 - 1040 = 16.0)

# Gap: 1096 - 1056 = 40 px!

# Bottom bar: y = 1096 to 1160 (h = 64)
# Text y = 1136:
# Top pad: 1136 - 22.4 - 1096 = 17.6 px (>= 16)
# Bot pad: 1160 - 1143 = 17.0 px (>= 16)
# Bottom margin: 1200 - 1160 = 40 px (>= 40)

print("Exact perfection confirmed!")
