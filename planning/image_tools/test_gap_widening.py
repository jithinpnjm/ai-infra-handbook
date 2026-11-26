# If box width = 290
# Margins = 50
# Col 0: X = 50 .. 340 (center 195)
# Gap 0-1: X = 340 .. 655 (width 315)
# Col 1: X = 655 .. 945 (center 800)
# Gap 1-2: X = 945 .. 1260 (width 315)
# Col 2: X = 1260 .. 1550 (center 1405)

# Check box title padding inside width 290:
# Longest title: Decommissioned (14 chars * 18px = 252px)
pad = (290 - 252) / 2
print(f"Decommissioned in w=290: pad = {pad}px >= 16px: {pad >= 16}")

# Check badge in 315px gap:
# Badge width = 280:
# Badge centered at 497.5 (left: 357.5, right: 637.5)
# From Col 0 right (340) to badge left (357.5): 17.5px segment!
# From badge right (637.5) to Col 1 left (655): 17.5px segment with arrow!
print("Arrow segments visible on both sides of badge!")
