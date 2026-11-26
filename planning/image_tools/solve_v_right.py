# Vertical layout solver for Right Panel
# Available: y=130 (after header) to y=770 (panel bottom)
# Total height = 640 px!
# Nodes to place:
# 1. start: h=70
# 2. diamond 1: h=160 (ry=80)
# 3. box b: h=75
# 4. diamond 2: h=170 (ry=85)
# 5. end: h=70
# Sum of node heights = 70 + 160 + 75 + 170 + 70 = 545 px!
# That leaves 640 - 545 = 95 px for 4 gaps/arrows!
# That is ~24 px per arrow.
# BUT what if diamond ry is 70 and 75?
# Sum = 70 + 140 + 70 + 150 + 70 = 500 px!
# Gaps = (640 - 500) / 4 = 35 px per arrow!
print("Calculated vertical budget.")
