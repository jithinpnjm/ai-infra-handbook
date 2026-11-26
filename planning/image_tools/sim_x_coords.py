# Canvas: 0 to 1600
# Margin left = 40, margin right = 40
# Usable width = 1520 (x = 40 to 1560)

# Right strip width = 300 (x = 1260 to 1560)
# Gap between grid and right strip = 20 px (x = 1240 to 1260)
# Grid total width = 1200 px (x = 40 to 1240)

# Let's divide Grid (1200 px):
# 4 columns:
# col_fabric: x = 40, w = 280 (x: 40 to 320)
# gap = 10 (320 to 330)
# col_l12: x = 330, w = 265 (x: 330 to 595)
# gap = 10 (595 to 605)
# col_l3: x = 605, w = 265 (x: 605 to 870)
# gap = 10 (870 to 880)
# col_l4: x = 880, w = 360 (x: 880 to 1240)
# Total grid = 280 + 10 + 265 + 10 + 265 + 10 + 360 = 1200!
# Gap = 20 (1240 to 1260)
# Right strip: x = 1260, w = 300 (1260 to 1560)
# Total = 1560 + 40 margin = 1600! PERFECT!

print("Grid layout perfectly matches 1600 px!")
