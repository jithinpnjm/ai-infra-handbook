# If Title line 1 baseline is at y = 88, line 2 at y = 142:
# Top of text ~ 88 - 44 = 44 >= 40!
# Bottom of text ~ 142 + 12 = 154.

# Panels start at y = 175, h = 635 (ends at 810).
# In Right Panel:
# Header: 175..245
# Card 1: 255..355 (h=100)
# Card 2: 370..505 (h=135)
# Card 3: 520..620 (h=100)
# Card 4: 635..770 (h=135)
# Card 4 ends at 770. Panels end at 805 (or 810).

# Footer: y = 825..945 (h=120)
# Result: y = 963..1051 (h=88) -> let's make y = 960..1054 (h=94)
# Bottom bar: y = 1066..1160 (h=94)
# Bottom margin: 1200 - 1160 = 40 px!

print("Panels:", 175, "to", 805)
print("Right cards total: 255 to 770")
print("Footer:", 825, "to", 945)
print("Result:", 960, "to", 1054)
print("Bottom bar:", 1066, "to", 1160)
print("Canvas margins: Top >= 40, Bottom = 40, Left >= 40, Right >= 40!")
