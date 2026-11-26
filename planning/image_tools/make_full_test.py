import xml.etree.ElementTree as ET

# Canvas: 1600 x 1050
# Let's define the precise positions of the 8 boxes:

# Row heights:
# Top row (P): y = 140, h = 150 (y_bottom = 290)
# Middle row (U, B, L, S, C): y = 430, h = 170 (y_bottom = 600)
# Bottom row (D, ST): y = 800, h = 175 (y_bottom = 975)

# Middle row X positions:
# 5 nodes: U, B, L, S, C
# U: x = 50, w = 220  [50..270]
# B: x = 360, w = 240 [360..600]
# L: x = 690, w = 230 [690..920]
# S: x = 1010, w = 240 [1010..1250]
# C: x = 1330, w = 230 [1330..1560]

# Gaps in middle row:
# U to B: 360 - 270 = 90 px
# B to L: 690 - 600 = 90 px
# L to S: 1010 - 920 = 90 px
# S to C: 1330 - 1250 = 80 px
# Margins: left = 50, right = 1600 - 1560 = 40 px! Exactly matches >= 40px rule!

# Top row (P):
# P: x = 450, w = 420 [450..870], y = 130, h = 150 [130..280]
# Center of P = 660, y_center = 205.

# Bottom row:
# D: x = 160, w = 440 [160..600], y = 800, h = 175 [800..975]
# ST: x = 720, w = 540 [720..1260], y = 800, h = 175 [800..975]

print("Grid calculations:")
print(f"U: [50..270, 430..600]")
print(f"B: [360..600, 430..600]")
print(f"L: [690..920, 430..600]")
print(f"S: [1010..1250, 430..600]")
print(f"C: [1330..1560, 430..600]")
print(f"P: [450..870, 130..280]")
print(f"D: [160..600, 800..975]")
print(f"ST: [720..1260, 800..975]")

